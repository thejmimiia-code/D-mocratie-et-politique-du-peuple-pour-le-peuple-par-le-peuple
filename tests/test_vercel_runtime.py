"""Tests du contrat Vercel : page interactive à la racine et fonction API unique."""

from __future__ import annotations

import contextlib
import http.client
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
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
from simulateur.pont_api import PontAPI, chemin_demande  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FONCTIONS_ATTENDUES = {"[...path].py", "verifier-source.py"}


def charger_fonction_unique():
    """Charge `api/[...path].py`, la fonction Vercel qui sert toutes les routes."""
    chemin = ROOT / "api" / "[...path].py"
    specification = importlib.util.spec_from_file_location("api_attrape_tout", chemin)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module.handler


def charger_generateur():
    """Charge `outils/generer-fonctions-api.py` comme module, sans l'exécuter."""
    chemin = ROOT / "outils" / "generer-fonctions-api.py"
    specification = importlib.util.spec_from_file_location("generer_fonctions_api", chemin)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


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

    def test_generateur_confirme_une_fonction_attrape_tout(self):
        commande = subprocess.run(
            [sys.executable, "outils/generer-fonctions-api.py", "--verifier"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(commande.returncode, 0, commande.stdout + commande.stderr)
        self.assertIn("16 routes du moteur", commande.stdout)
        self.assertIn("2 fonction(s) dans api/, plafond 12", commande.stdout)

    def test_api_ne_contient_que_la_fonction_attrape_tout_et_le_site(self):
        fichiers = {nom.name for nom in (ROOT / "api").glob("*.py")}
        self.assertEqual(fichiers, FONCTIONS_ATTENDUES)

    def test_fonction_attrape_tout_herite_du_pont(self):
        handler = charger_fonction_unique()
        self.assertTrue(issubclass(handler, PontAPI))
        self.assertTrue(issubclass(PontAPI, DashboardHandler))
        self.assertTrue(issubclass(handler, BaseHTTPRequestHandler))

    def test_pont_conserve_la_requete_telle_quelle(self):
        instance = object.__new__(PontAPI)
        instance.path = "/api/scenarios?scenario=mandature"
        with patch.object(DashboardHandler, "do_GET") as deleguer:
            instance.do_GET()
        self.assertEqual(instance.path, "/api/scenarios?scenario=mandature")
        deleguer.assert_called_once_with(instance)

    def test_pont_retablit_la_destination_de_reecriture(self):
        instance = object.__new__(PontAPI)
        instance.path = "/api/[...path]?...path=catalogue&x=1"
        with patch.object(DashboardHandler, "do_GET") as deleguer:
            instance.do_GET()
        self.assertEqual(instance.path, "/api/catalogue?x=1")
        deleguer.assert_called_once_with(instance)


class TestCheminDemande(unittest.TestCase):
    def test_formes_de_cible_de_requete(self):
        cas = {
            # Vercel transmet l'URL demandée : elle est conservée telle quelle.
            "/api/catalogue": "/api/catalogue",
            "/api/scenarios?scenario=mandature": "/api/scenarios?scenario=mandature",
            # Vercel transmet la destination de la réécriture : le chemin est rétabli.
            "/api/[...path]?...path=catalogue&x=1": "/api/catalogue?x=1",
            "/api/[...path]?...path=bulle&levier=abc": "/api/bulle?levier=abc",
            "/api/[...path]?...path=simuler": "/api/simuler",
            "/api/%5B...path%5D?...path=lexique&q=spread": "/api/lexique?q=spread",
            "/api/[...path]?x=1&...path=export&format=csv": "/api/export?x=1&format=csv",
            # Sans segment capturé, ou hors de la destination : rien n'est réécrit.
            "/api/[...path]?autre=1": "/api/[...path]?autre=1",
            "/api/[...path]": "/api/[...path]",
            "/": "/",
        }
        for entree, attendu in cas.items():
            with self.subTest(entree=entree):
                self.assertEqual(chemin_demande(entree), attendu)


class TestFonctionsVercelHTTP(unittest.TestCase):
    @staticmethod
    def requete_complete(handler: type[BaseHTTPRequestHandler], methode: str, chemin: str,
                         corps: dict[str, object] | None = None) -> tuple[int, dict[str, str], str]:
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
            en_tetes = {cle.lower(): valeur for cle, valeur in reponse.getheaders()}
            contenu = reponse.read().decode("utf-8")
            connexion.close()
            return code, en_tetes, contenu
        finally:
            serveur.shutdown()
            serveur.server_close()
            thread.join(timeout=5)

    @classmethod
    def requete(cls, handler: type[BaseHTTPRequestHandler], methode: str, chemin: str,
                corps: dict[str, object] | None = None) -> tuple[int, str, str]:
        code, en_tetes, contenu = cls.requete_complete(handler, methode, chemin, corps)
        return code, en_tetes.get("content-type", ""), contenu

    def test_api_scenarios_est_servie_par_la_fonction(self):
        handler = charger_fonction_unique()

        code, type_contenu, contenu = self.requete(handler, "GET", "/api/scenarios")
        donnees = json.loads(contenu)
        self.assertEqual(code, 200)
        self.assertIn("application/json", type_contenu)
        self.assertIn("mandature", donnees["scenarios"])

    def test_api_lexique_passe_par_la_fonction_unique(self):
        handler = charger_fonction_unique()

        code, type_contenu, contenu = self.requete(handler, "GET", "/api/lexique?q=spread")
        donnees = json.loads(contenu)
        self.assertEqual(code, 200)
        self.assertIn("application/json", type_contenu)
        self.assertGreater(donnees["total"], 0)

    def test_api_simuler_retourne_une_simulation_complete(self):
        handler = charger_fonction_unique()

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

    def test_route_inconnue_renvoie_404(self):
        handler = charger_fonction_unique()

        code, _type, _contenu = self.requete(handler, "GET", "/api/inconnue")
        self.assertEqual(code, 404)

    def test_destination_de_reecriture_est_servie(self):
        handler = charger_fonction_unique()

        code, type_contenu, contenu = self.requete(
            handler, "GET", "/api/[...path]?...path=scenarios"
        )
        self.assertEqual(code, 200, contenu[:500])
        self.assertIn("mandature", json.loads(contenu)["scenarios"])

    def test_head_repond_sans_corps(self):
        handler = charger_fonction_unique()

        code, entetes, contenu = self.requete_complete(handler, "HEAD", "/api/scenarios")
        self.assertEqual(code, 200)
        self.assertIn("application/json", entetes.get("content-type", ""))
        self.assertEqual(contenu, "")

    def test_export_csv_est_servi_sans_ecriture_disque(self):
        handler = charger_fonction_unique()

        with tempfile.TemporaryDirectory() as dossier, contextlib.chdir(dossier):
            code, entetes, contenu = self.requete_complete(
                handler, "GET", "/api/export?scenario=mandature&format=csv"
            )
            fichiers_apres = os.listdir(dossier)
        self.assertEqual(code, 200, contenu[:500])
        self.assertIn("text/csv", entetes.get("content-type", ""))
        self.assertEqual(
            entetes.get("content-disposition"), 'attachment; filename="mandature_simulateur.csv"'
        )
        lignes = contenu.splitlines()
        self.assertEqual(len(lignes), 6)  # en-tête et cinq années
        self.assertEqual(fichiers_apres, [], "l'export ne doit rien écrire dans le dossier courant")

    def test_export_json_est_servi_sans_ecriture_disque(self):
        handler = charger_fonction_unique()

        with tempfile.TemporaryDirectory() as dossier, contextlib.chdir(dossier):
            code, entetes, contenu = self.requete_complete(
                handler, "GET", "/api/export?scenario=mandature&format=json"
            )
            fichiers_apres = os.listdir(dossier)
        self.assertEqual(code, 200, contenu[:500])
        self.assertIn("application/json", entetes.get("content-type", ""))
        self.assertEqual(len(json.loads(contenu)["resultats"]), 5)
        self.assertEqual(fichiers_apres, [], "l'export ne doit rien écrire dans le dossier courant")


class TestGenerateurFonctionsAPI(unittest.TestCase):
    """Le générateur travaille dans un dossier temporaire, jamais dans le dépôt."""

    def setUp(self):
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        self.racine = Path(dossier.name)
        (self.racine / "simulateur").mkdir()
        shutil.copy(ROOT / "simulateur" / "dashboard.py", self.racine / "simulateur" / "dashboard.py")
        (self.racine / "api").mkdir()
        self.generateur = charger_generateur()
        self.generateur.RACINE = self.racine
        self.marque = self.generateur.MARQUE_GENERATION
        self.gabarit = self.generateur.GABARIT_ATTRAPE_TOUT

    def lancer(self, *arguments: str) -> tuple[int, str, str]:
        sortie, erreurs = io.StringIO(), io.StringIO()
        with (
            patch.object(sys, "argv", ["generer-fonctions-api.py", *arguments]),
            contextlib.redirect_stdout(sortie),
            contextlib.redirect_stderr(erreurs),
        ):
            code = self.generateur.main()
        return code, sortie.getvalue(), erreurs.getvalue()

    def ecrire_site(self) -> None:
        (self.racine / "api" / "verifier-source.py").write_text("# fonction du site\n", encoding="utf-8")

    def test_generation_supprime_les_anciennes_fonctions_generees(self):
        self.ecrire_site()
        ancienne = self.racine / "api" / "bulle.py"
        ancienne.write_text(f'"""Ancienne route.\n\n{self.marque} : ne pas modifier.\n"""\n', encoding="utf-8")

        code, _sortie, erreurs = self.lancer()

        self.assertEqual(code, 0, erreurs)
        self.assertFalse(ancienne.exists())
        self.assertEqual((self.racine / "api" / "[...path].py").read_text(encoding="utf-8"), self.gabarit)
        self.assertEqual(
            (self.racine / "api" / "verifier-source.py").read_text(encoding="utf-8"), "# fonction du site\n"
        )

    def test_generation_refuse_un_fichier_inconnu_sans_rien_modifier(self):
        self.ecrire_site()
        generee = self.racine / "api" / "bulle.py"
        generee.write_text(f'"""Ancienne route.\n\n{self.marque}.\n"""\n', encoding="utf-8")
        intrus = self.racine / "api" / "intrus.py"
        intrus.write_text("# fichier écrit à la main\n", encoding="utf-8")

        code, _sortie, erreurs = self.lancer()

        self.assertEqual(code, 1)
        self.assertIn("intrus.py", erreurs)
        self.assertTrue(intrus.exists())
        self.assertTrue(generee.exists(), "rien ne doit être supprimé quand un fichier est inconnu")
        self.assertFalse((self.racine / "api" / "[...path].py").exists())

    def test_generation_refuse_si_la_fonction_du_site_manque(self):
        code, _sortie, erreurs = self.lancer()

        self.assertEqual(code, 1)
        self.assertIn("verifier-source", erreurs)
        self.assertFalse((self.racine / "api" / "[...path].py").exists())

    def test_verifier_reussit_apres_generation(self):
        self.ecrire_site()
        self.lancer()

        code, sortie, erreurs = self.lancer("--verifier")

        self.assertEqual(code, 0, erreurs)
        self.assertIn("1 fonction attrape-tout", sortie)

    def test_verifier_echoue_si_le_gabarit_est_modifie(self):
        self.ecrire_site()
        self.lancer()
        (self.racine / "api" / "[...path].py").write_text(self.gabarit + "# modifié\n", encoding="utf-8")

        code, _sortie, erreurs = self.lancer("--verifier")

        self.assertEqual(code, 1)
        self.assertIn("gabarit", erreurs)


if __name__ == "__main__":
    unittest.main()
