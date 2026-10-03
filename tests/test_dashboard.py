"""
tests/test_dashboard.py — Tests d'intégration du dashboard web interactif.

Vérifie que le serveur HTTP, les endpoints API et le rendu HTML
fonctionnent correctement.
"""

import json
import socket
import threading
import unittest
import urllib.request

from simulateur.dashboard import (
    SCENARIOS,
    create_server,
    run_simulation_api,
)


class TestDashboardAPI(unittest.TestCase):
    """Tests des endpoints API du dashboard."""

    @classmethod
    def setUpClass(cls):
        """Démarre le serveur sur un port aléatoire."""
        # Trouve un port libre
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("", 0))
        cls.port = sock.getsockname()[1]
        sock.close()

        cls.server = create_server("127.0.0.1", cls.port)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _get(self, path: str) -> tuple[int, str]:
        """Effectue une requête GET et retourne (status_code, body)."""
        url = f"http://127.0.0.1:{self.__class__.port}{path}"
        resp = urllib.request.urlopen(url, timeout=30)
        return resp.status, resp.read().decode("utf-8")

    def test_html_page_served(self):
        """La page HTML du dashboard est servie avec le bon Content-Type."""
        status, body = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn("Simulateur Macro-Politique", body)
        self.assertIn("strates-cascade", body)
        self.assertIn("scenario-grid", body)
        self.assertIn("grid-metrics", body)
        self.assertIn("svg-chart", body)
        self.assertIn("results-table", body)
        self.assertIn("fetch(", body)
        # Le placeholder doit être remplacé
        self.assertNotIn("===SCENARIOS_JSON===", body)

    def test_api_scenarios(self):
        """L'endpoint /api/scenarios retourne les 4 scénarios."""
        status, body = self._get("/api/scenarios")
        data = json.loads(body)
        self.assertEqual(status, 200)
        self.assertIn("scenarios", data)
        for key in ["mandature", "statut_quo", "austerite", "choc_mondial"]:
            self.assertIn(key, data["scenarios"])
            s = data["scenarios"][key]
            self.assertIn("nom", s)
            self.assertIn("description", s)
            self.assertIn("couleur", s)

    def test_api_run_mandature(self):
        """L'endpoint /api/run exécute la simulation mandature (5 étapes)."""
        status, body = self._get("/api/run?scenario=mandature")
        data = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(data["scenario"], "mandature")
        self.assertEqual(len(data["resultats"]), 5)
        # Validation An 5 : déficit < 3%
        last = data["resultats"][-1]
        self.assertLess(last["ratio_deficit_pib"], 3.0)
        self.assertEqual(last["note_souveraine"], "AA")

    def test_api_run_statut_quo(self):
        """L'endpoint /api/run exécute le scénario statut_quo (5 étapes)."""
        status, body = self._get("/api/run?scenario=statut_quo")
        data = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(len(data["resultats"]), 5)

    def test_api_run_scenario_inconnu(self):
        """Un scénario inconnu retourne une erreur."""
        status, body = self._get("/api/run?scenario=invalid")
        data = json.loads(body)
        self.assertIn("error", data)

    def test_api_export_csv(self):
        """L'endpoint /api/export?format=csv retourne un CSV valide."""
        status, body = self._get("/api/export?scenario=mandature&format=csv")
        self.assertEqual(status, 200)
        lines = body.strip().split("\n")
        self.assertGreater(len(lines), 1)  # header + data

    def test_api_export_json(self):
        """L'endpoint /api/export?format=json retourne un JSON valide."""
        status, body = self._get("/api/export?scenario=mandature&format=json")
        data = json.loads(body)
        self.assertEqual(status, 200)
        self.assertIn("resultats", data)

    def test_scenarios_contiennent_fonctions(self):
        """Chaque scénario a une fonction callable."""
        for _key, val in SCENARIOS.items():
            self.assertIn("fn", val)
            self.assertTrue(callable(val["fn"]))


class TestRunSimulationAPI(unittest.TestCase):
    """Tests de la fonction run_simulation_api."""

    def test_run_simulation_mandature(self):
        """La simulation mandature retourne 5 résultats formattés."""
        result = run_simulation_api("mandature")
        self.assertNotIn("error", result)
        self.assertEqual(len(result["resultats"]), 5)
        # Check all numeric fields are properly typed
        for r in result["resultats"]:
            self.assertIsInstance(r["annee"], int)
            self.assertIsInstance(r["ratio_deficit_pib"], (int, float))
            self.assertIsInstance(r["note_souveraine"], str)

    def test_run_simulation_inconnu(self):
        """Un scénario inconnu retourne une erreur."""
        result = run_simulation_api("non_existent")
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
