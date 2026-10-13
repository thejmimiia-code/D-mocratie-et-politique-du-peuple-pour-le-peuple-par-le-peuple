"""Tests du contrat Vercel : page interactive à la racine et fonctions API."""

from __future__ import annotations

import http.client
import json
import os
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

# Garder les tests réseau déterministes et garantir le cache inscriptible comme
# sur Vercel. pont_api définit également SIMULATEUR_CACHE avant l'import moteur.
os.environ.setdefault("SIMULATEUR_HORS_LIGNE", "1")
os.environ.setdefault("SIMULATEUR_CACHE", "/tmp/simulateur_cache")

from outils.chargement_module import charger_module  # noqa: E402
from simulateur.dashboard import DashboardHandler  # noqa: E402
from simulateur.pont_api import FonctionAPI, PontAPI, chemin_de_pont  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def _charger_fonction_unique():
    """Charge `api/[...path].py` : le nom n'est pas un nom de module, d'où le chemin.

    Sans cache de bytecode : l'engendré doit être relu à chaque fois, jamais
    servi depuis un `.pyc` — voir `outils/chargement_module.py`.
    """
    return charger_module("api_pont_unique", ROOT / "api" / "[...path].py")
ROUTES_MOTEUR = (
    "catalogue",
    "contexte",
    "donnees",
    "simuler",
    "comparer",
    "presets",
    "bulles",
    "bulle",
    "proxy",
    "run",
    "scenarios",
    "export",
)


class TestContratVercel(unittest.TestCase):
    def test_index_racine_est_la_vraie_page_interactive(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        commande = subprocess.run(
            [sys.executable, "outils/generer-index-simulateur.py", "--verifier"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(commande.returncode, 0, commande.stdout + commande.stderr)
        self.assertIn('id="console-pilotage"', page)
        self.assertIn("fetch('/api/catalogue')", page)
        self.assertNotIn("===SCENARIOS_JSON===", page)
        self.assertNotIn("frame-ancestors", page.lower())
        self.assertNotIn("x-frame-options", page.lower())

    def test_generateur_expose_toutes_les_routes_du_moteur(self):
        commande = subprocess.run(
            [sys.executable, "outils/generer-fonctions-api.py", "--verifier"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(commande.returncode, 0, commande.stdout + commande.stderr)
        self.assertIn("routes du moteur", commande.stdout)  # nb varie selon les extensions actives

        # Une seule fonction Vercel, parce que chaque fichier `.py` de `api/` en devient
        # une et que l'offre Hobby plafonne à douze : `docs/HEBERGEMENT.md` le dit, ce
        # test le vérifie.
        module = _charger_fonction_unique()
        self.assertTrue(issubclass(module.handler, BaseHTTPRequestHandler))
        self.assertTrue(issubclass(module.handler, PontAPI))
        self.assertTrue(set(ROUTES_MOTEUR) <= set(module.ROUTES),
                        f"routes absentes du pont : {sorted(set(ROUTES_MOTEUR) - set(module.ROUTES))}")
        fichiers = sorted(chemin.name for chemin in (ROOT / "api").glob("*.py"))
        self.assertEqual(fichiers, ["[...path].py", "verifier-source.py"])
        for nom in ROUTES_MOTEUR:
            with self.subTest(route=nom):
                self.assertIn(nom, module.ROUTES)
                self.assertIn(nom, (ROOT / "simulateur" / "dashboard.py").read_text(encoding="utf-8"))

    def test_pont_retablit_la_route_et_preserve_la_requete(self):
        class RouteTest(FonctionAPI):
            ROUTE = "/api/scenarios"

        instance = object.__new__(RouteTest)
        instance.path = "/api/index.py?scenario=mandature"
        with patch.object(DashboardHandler, "do_GET") as deleguer:
            instance._deleguer("GET")
        self.assertEqual(instance.path, "/api/scenarios?scenario=mandature")
        deleguer.assert_called_once_with(instance)


class TestCheminDePont(unittest.TestCase):
    """Ce que Vercel envoie dans la chaîne de requête doit redevenir un chemin."""

    def cases(self):
        return [
            ("/api/simuler?horizon=5", "/api/simuler?horizon=5"),
            ("/api/%5B...path%5D.py?...path=simuler&horizon=5", "/api/simuler?horizon=5"),
            ("/api/pont.py?path=/api/nuances&article=49", "/api/nuances?article=49"),
            ("/api/pont.py?...path=constitution&article=49", "/api/constitution?article=49"),
            ("/api/pont.py?...path=", "/"),
            ("/", "/"),
        ]

    def test_le_pont_retablit_le_chemin_servi_par_le_moteur(self):
        for recu, attendu in self.cases():
            with self.subTest(chemin=recu):
                self.assertEqual(chemin_de_pont(recu), attendu)

    def test_le_pont_est_idempotent(self):
        # `do_HEAD` rappelle `do_GET` : repasser sur un chemin déjà rétabli ne doit
        # rien changer, sinon la requête partirait en boucle vers une route fantôme.
        for _, retabli in self.cases():
            with self.subTest(chemin=retabli):
                self.assertEqual(chemin_de_pont(retabli), retabli)


class TestFonctionsVercelHTTP(unittest.TestCase):
    @staticmethod
    def requete(handler: type[BaseHTTPRequestHandler], methode: str, chemin: str,
                corps: dict[str, object] | None = None) -> tuple[int, str, str]:
        serveur = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=serveur.serve_forever, daemon=True)
        thread.start()
        try:
            hote, port = serveur.server_address
            connexion = http.client.HTTPConnection(hote, port, timeout=90)
            donnees = None if corps is None else json.dumps(corps).encode("utf-8")
            entetes = {"Content-Type": "application/json"} if donnees is not None else {}
            connexion.request(methode, chemin, body=donnees, headers=entetes)
            reponse = connexion.getresponse()
            code = reponse.status
            type_contenu = reponse.getheader("Content-Type", "")
            contenu = reponse.read().decode("utf-8")
            connexion.close()
            return code, type_contenu, contenu
        finally:
            serveur.shutdown()
            serveur.server_close()
            thread.join(timeout=5)

    def test_api_scenarios_est_servie_par_la_fonction(self):
        handler = _charger_fonction_unique().handler

        code, type_contenu, contenu = self.requete(handler, "GET", "/api/scenarios")
        donnees = json.loads(contenu)
        self.assertEqual(code, 200)
        self.assertIn("application/json", type_contenu)
        self.assertIn("mandature", donnees["scenarios"])

    def test_api_simuler_retourne_une_simulation_complete(self):
        handler = _charger_fonction_unique().handler

        code, type_contenu, contenu = self.requete(
            handler,
            "POST",
            "/api/simuler",
            {"parametres": {"tva_taux_normal": 1.5}, "horizon": 5},
        )
        donnees = json.loads(contenu)
        self.assertEqual(code, 200, contenu[:1000])
        self.assertIn("application/json", type_contenu)
        self.assertEqual(len(donnees["etapes"]), 5)


if __name__ == "__main__":
    unittest.main()
