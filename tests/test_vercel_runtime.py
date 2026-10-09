"""Tests du contrat Vercel : page interactive à la racine et fonctions API."""

from __future__ import annotations
from typing import Dict, Optional, Tuple

import http.client
import importlib
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

from simulateur.dashboard import DashboardHandler  # noqa: E402
from simulateur.pont_api import FonctionAPI  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
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

        for nom in ROUTES_MOTEUR:
            with self.subTest(route=nom):
                module = importlib.import_module(f"api.{nom}")
                fonction = module.handler
                self.assertTrue(issubclass(fonction, BaseHTTPRequestHandler))
                self.assertEqual(fonction.ROUTE, f"/api/{nom}")

    def test_pont_retablit_la_route_et_preserve_la_requete(self):
        class RouteTest(FonctionAPI):
            ROUTE = "/api/scenarios"

        instance = object.__new__(RouteTest)
        instance.path = "/api/index.py?scenario=mandature"
        with patch.object(DashboardHandler, "do_GET") as deleguer:
            instance._deleguer("GET")
        self.assertEqual(instance.path, "/api/scenarios?scenario=mandature")
        deleguer.assert_called_once_with(instance)


class TestFonctionsVercelHTTP(unittest.TestCase):
    @staticmethod
    def requete(handler: type[BaseHTTPRequestHandler], methode: str, chemin: str,
                corps: Optional[Dict[str, object]] = None) -> Tuple[int, str, str]:
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
        from api.scenarios import handler

        code, type_contenu, contenu = self.requete(handler, "GET", "/api/scenarios")
        donnees = json.loads(contenu)
        self.assertEqual(code, 200)
        self.assertIn("application/json", type_contenu)
        self.assertIn("mandature", donnees["scenarios"])

    def test_api_simuler_retourne_une_simulation_complete(self):
        from api.simuler import handler

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
