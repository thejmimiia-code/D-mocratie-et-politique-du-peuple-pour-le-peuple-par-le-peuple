"""
tests/test_dashboard.py — Tests d'intégration du dashboard web interactif.

Vérifie que le serveur HTTP, les endpoints API et le rendu HTML
fonctionnent correctement.
"""

import http.client
import json
import re
import socket
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from simulateur.dashboard import (
    SCENARIOS,
    DashboardHandler,
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


class TestDashboardInterface(unittest.TestCase):
    """Tests de non-régression de l'interface web du dashboard.

    Ces tests protègent le rendu de la grille de scénarios : les cartes doivent
    être réellement insérées dans le DOM, cliquables, et le serveur doit rester
    réactif derrière un proxy qui maintient des connexions persistantes.
    """

    @classmethod
    def setUpClass(cls):
        """Démarre le serveur sur un port libre et récupère la page HTML."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("", 0))
        cls.port = sock.getsockname()[1]
        sock.close()

        cls.server = create_server("127.0.0.1", cls.port)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

        url = f"http://127.0.0.1:{cls.port}/"
        with urllib.request.urlopen(url, timeout=30) as resp:
            cls.page = resp.read().decode("utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    @staticmethod
    def _script(page: str) -> str:
        """Retourne le JS de la page, commentaires exclus."""
        scripts = re.findall(r"<script>(.*?)</script>", page, re.S)
        js = "\n".join(scripts)
        js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
        # Les « // » précédés de « : » (http://) ne sont pas des commentaires.
        js = re.sub(r"(?<!:)//.*$", "", js, flags=re.M)
        return js

    def test_render_scenarios_insere_les_cartes_dans_le_dom(self):
        """Les cartes créées sont bien ajoutées à la grille (appendChild)."""
        js = self._script(self.page)
        # Sans appendChild, les cartes existent mais n'atteignent jamais le DOM :
        # la grille reste vide et aucun scénario n'est cliquable.
        self.assertIn("grid.appendChild(card);", js)
        self.assertIn("document.createElement('div')", js)
        # La grille est vidée puis remplie dans le même rendu.
        render = js.split("function renderScenarios()")[1].split("\nfunction ")[0]
        self.assertIn("grid.innerHTML = '';", render)
        self.assertIn("appendChild(card)", render)

    def test_run_scenario_recoit_evenement_explicite(self):
        """runScenario reçoit l'événement en paramètre, sans globale implicite."""
        js = self._script(self.page)
        self.assertIn("card.onclick = (ev) => runScenario(key, ev);", js)
        self.assertIn("async function runScenario(scenario, ev)", js)
        # La globale implicite `event` (absente de certains environnements)
        # ne doit plus être utilisée comme source de la carte cliquée.
        self.assertIsNone(re.search(r"(?<![\w$])event(?![\w$])", js))
        # Repli sur data-key lorsque l'événement ne porte pas de carte.
        self.assertIn("card.dataset.key = key;", js)
        self.assertIn('.scenario-card[data-key="${scenario}"]', js)

    def test_mandature_auto_lance_et_exports_actives(self):
        """Le scénario mandature est lancé au chargement, exports activés."""
        js = self._script(self.page)
        self.assertIn("renderScenarios();", js)
        self.assertIn("runScenario('mandature');", js)
        # Les boutons d'export partent désactivés...
        self.assertIn('id="btn-export-json"', self.page)
        self.assertIn("disabled", self.page)
        # ...et sont activés dès qu'une simulation a tourné.
        self.assertIn("function activerExports()", js)
        self.assertIn("activerExports();", js)

    def test_neuf_scenarios_exposes(self):
        """Les 9 scénarios sont exposés côté serveur et injectés dans la page."""
        status, body = self._get("/api/scenarios")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(len(data["scenarios"]), 9)
        self.assertEqual(len(SCENARIOS), 9)
        for key in [
            "mandature",
            "statut_quo",
            "austerite",
            "choc_mondial",
            "crise_taiwan",
            "hormuz",
            "escalade_nucleaire",
            "convergence_ww3",
            "resilience",
        ]:
            self.assertIn(key, SCENARIOS)
            self.assertIn(key, self.page)

    def test_balises_div_equilibrees(self):
        """Le HTML servi a autant de <div> ouvrantes que fermantes."""
        ouverts = len(re.findall(r"<div\b", self.page))
        fermes = len(re.findall(r"</div>", self.page))
        self.assertEqual(ouverts, fermes)
        self.assertGreater(ouverts, 0)

    def test_serveur_multi_thread_et_http1_1(self):
        """Le serveur est multi-thread (daemon) et parle HTTP/1.1 keep-alive."""
        self.assertIsInstance(self.server, ThreadingHTTPServer)
        self.assertTrue(self.server.daemon_threads)
        self.assertEqual(DashboardHandler.protocol_version, "HTTP/1.1")

        # Plusieurs requêtes sur une même connexion persistante ne bloquent pas
        # le serveur : c'est la régression corrigée par le passage en threading.
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        try:
            for _ in range(3):
                conn.request("GET", "/api/scenarios")
                resp = conn.getresponse()
                self.assertEqual(resp.status, 200)
                payload = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(len(payload["scenarios"]), 9)
                self.assertFalse(resp.will_close)
            # Une 404 sans corps doit annoncer Content-Length: 0, sinon le
            # client attend indéfiniment la fin d'une réponse keep-alive.
            conn.request("GET", "/route-inexistante")
            resp = conn.getresponse()
            self.assertEqual(resp.status, 404)
            self.assertEqual(resp.getheader("Content-Length"), "0")
            resp.read()
        finally:
            conn.close()

    def _get(self, path: str) -> tuple[int, str]:
        """Effectue une requête GET et retourne (status_code, body)."""
        url = f"http://127.0.0.1:{self.__class__.port}{path}"
        with urllib.request.urlopen(url, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8")


if __name__ == "__main__":
    unittest.main()
