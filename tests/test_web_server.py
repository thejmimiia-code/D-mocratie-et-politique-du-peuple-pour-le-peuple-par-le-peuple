"""
tests/test_web_server.py — Tests d'intégration de l'API REST et du serveur Web HTTP.
"""

import unittest
import json
import threading
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from simulateur.web_server import (
    ThreadedHTTPServer,
    SimulateurHTTPHandler,
    serialize_resultat,
    executer_simulation_scenario,
    executer_simulation_personnalisee,
    generer_comparatif_global,
)
from simulateur.moteur import MoteurSimulationSystemique
from simulateur.model import DecisionPolitique


class TestWebServerUnitaires(unittest.TestCase):
    """Tests unitaires des fonctions internes du serveur Web."""

    def test_serialize_resultat(self):
        moteur = MoteurSimulationSystemique()
        res = moteur.appliquer_etape(DecisionPolitique(annee=1))
        d = serialize_resultat(res)
        self.assertIsInstance(d, dict)
        self.assertEqual(d["annee"], 1)
        self.assertIn("deficit_nominal_mde", d)
        self.assertIn("taux_oat_pct", d)
        self.assertIn("spread_bund_bps", d)

    def test_executer_simulation_scenarios_valides(self):
        for nom in ["mandature", "statut_quo", "austerite", "choc_mondial"]:
            traj = executer_simulation_scenario(nom)
            self.assertGreaterEqual(len(traj), 3)
            self.assertEqual(traj[0]["annee"], 1)

    def test_executer_simulation_scenario_invalide(self):
        with self.assertRaises(ValueError):
            executer_simulation_scenario("inconnu")

    def test_simulation_personnalisee(self):
        decisions = [
            {"recettes_fraude_ia_mde": 5.0, "baisse_tva_energie_5_5_mde": 9.0},
            {"recettes_fraude_ia_mde": 10.0, "reforme_ric_souverain": True},
        ]
        traj = executer_simulation_personnalisee(decisions)
        self.assertEqual(len(traj), 2)
        self.assertEqual(traj[0]["annee"], 1)
        self.assertEqual(traj[1]["annee"], 2)

    def test_comparatif_global(self):
        comp = generer_comparatif_global()
        self.assertIn("mandature", comp)
        self.assertIn("statut_quo", comp)
        self.assertIn("austerite", comp)
        self.assertIn("choc_mondial", comp)
        self.assertLess(comp["mandature"]["ratio_deficit_pib"], 3.0)


class TestWebServerHTTP(unittest.TestCase):
    """Tests d'intégration réseau sur une instance éphémère du serveur HTTP."""

    @classmethod
    def setUpClass(cls):
        # Bind sur port éphémère (port 0 = OS attribue un port libre)
        cls.server = ThreadedHTTPServer(("127.0.0.1", 0), SimulateurHTTPHandler)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.daemon = True
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_get_index_html(self):
        with urlopen(f"{self.base_url}/") as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertIn("Simulateur Macro-Politique & Démocratique", body)
            self.assertIn("RÉPUBLIQUE CITOYENNE", body)

    def test_api_status(self):
        with urlopen(f"{self.base_url}/api/status") as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "ok")
            self.assertEqual(data["version"], "1.1.0")

    def test_api_scenarios(self):
        with urlopen(f"{self.base_url}/api/scenarios") as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(len(data["scenarios"]), 4)

    def test_api_comparatif(self):
        with urlopen(f"{self.base_url}/api/comparatif") as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("mandature", data)
            self.assertIn("statut_quo", data)

    def test_api_corpus_sans_filtre(self):
        with urlopen(f"{self.base_url}/api/corpus") as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertGreaterEqual(data["total"], 20)

    def test_api_corpus_avec_recherche(self):
        with urlopen(f"{self.base_url}/api/corpus?q=TVA") as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertGreater(data["total"], 0)
            self.assertTrue(any("tva" in a["identifiant"].lower() or "tva" in a["titre"].lower() for a in data["articles"]))

    def test_api_dossier(self):
        with urlopen(f"{self.base_url}/api/dossier") as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertGreaterEqual(len(data["volumes"]), 8)

    def test_post_simuler_mandature(self):
        req = Request(
            f"{self.base_url}/api/simuler",
            data=json.dumps({"scenario": "mandature"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["scenario"], "mandature")
            self.assertEqual(data["nombre_annees"], 5)
            self.assertLess(data["synthese_annee_cible"]["ratio_deficit_pib"], 3.0)

    def test_post_simuler_custom(self):
        req = Request(
            f"{self.base_url}/api/simuler",
            data=json.dumps({
                "scenario": "custom",
                "parametres": {
                    "recettes_fraude_ia_mde": 12.0,
                    "baisse_tva_energie_5_5_mde": 9.0,
                }
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["scenario"], "custom")
            self.assertEqual(data["nombre_annees"], 5)

    def test_post_export_markdown(self):
        req = Request(
            f"{self.base_url}/api/export",
            data=json.dumps({"scenario": "mandature", "format": "markdown"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["format"], "markdown")
            self.assertIn("# RAPPORT DE SIMULATION MACRO-POLITIQUE", data["contenu"])


if __name__ == "__main__":
    unittest.main()
