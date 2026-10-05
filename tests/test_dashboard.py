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
        """Le préréglage mandature est chargé au démarrage, exports activés."""
        js = self._script(self.page)
        self.assertIn("renderScenarios();", js)
        # Au démarrage, la page charge le préréglage paramétrable (et non le
        # moteur d'origine) : c'est le simulateur qui doit être prêt à l'emploi.
        self.assertIn("chargerPreset('mandature', null);", js)
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


class TestAPIparametrique(unittest.TestCase):
    """API du simulateur paramétrable (leviers, contexte réel, impacts croisés).

    Ces routes remplacent les cartes généralistes du premier tableau de bord :
    elles servent la table des 93 leviers, la grille des 20 domaines, le contexte
    « instant T » et la matrice d'impacts calculée par le modèle.
    """

    @classmethod
    def setUpClass(cls):
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

    def _appel(self, chemin: str, corps: dict | None = None, methode: str | None = None):
        url = f"http://127.0.0.1:{self.__class__.port}{chemin}"
        donnees = None if corps is None else json.dumps(corps).encode("utf-8")
        requete = urllib.request.Request(url, data=donnees, method=methode or ("POST" if corps else "GET"))
        if donnees:
            requete.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(requete, timeout=60) as reponse:
            return reponse.status, json.loads(reponse.read().decode("utf-8"))

    def test_catalogue_complet(self):
        statut, donnees = self._appel("/api/catalogue")
        self.assertEqual(statut, 200)
        self.assertEqual(len(donnees["domaines"]), 20)
        familles = donnees["parametres"]["familles"]
        leviers = [levier for famille in familles for levier in famille["leviers"]]
        self.assertGreaterEqual(len(leviers), 90)
        self.assertEqual(len(donnees["parametres"]["presets"]), 13)

    def test_contexte_avec_sources_navigateur(self):
        statut, donnees = self._appel("/api/contexte")
        self.assertEqual(statut, 200)
        contexte = donnees["contexte"]
        self.assertIn(contexte["mode"], {"live", "reference", "mixte"})
        self.assertGreater(contexte["pib_nominal_mde"], 2000)
        self.assertTrue(contexte["provenance"])
        # Le navigateur doit recevoir de quoi interroger les API publiques.
        self.assertTrue(donnees["browser"])
        un_indicateur = next(iter(donnees["browser"].values()))
        self.assertIn("sources", un_indicateur)
        self.assertIn("proxy_url", un_indicateur)
        for source in un_indicateur["sources"]:
            self.assertTrue(source["url"].startswith("https://"))
            self.assertTrue(source["licence"])
        self.assertIn("diagnostic", donnees)

    def test_presets(self):
        statut, donnees = self._appel("/api/presets")
        self.assertEqual(statut, 200)
        self.assertIn("mandature", donnees["presets"])
        self.assertIn("crise_taiwan", donnees["presets"])

    def test_simuler_get_avec_parametres(self):
        params = json.dumps({"tva_taux_normal": 1.0})
        statut, donnees = self._appel(f"/api/simuler?params={urllib.parse.quote(params)}")
        self.assertEqual(statut, 200)
        self.assertEqual(len(donnees["etapes"]), 5)
        self.assertEqual(len(donnees["domaines"]), 20)
        self.assertIn("synthese", donnees)

    def test_simuler_post_avec_impacts(self):
        statut, donnees = self._appel("/api/simuler", {
            "parametres": {"tva_taux_normal": 1.0, "hopital_public": 6.0,
                           "lutte_fraude_fiscale_ia": 10.0},
            "avec_impacts": True,
            "max_impacts": 5,
        })
        self.assertEqual(statut, 200)
        self.assertTrue(donnees["impacts"])
        self.assertLessEqual(len(donnees["impacts"]), 5)
        for impact in donnees["impacts"]:
            self.assertTrue(impact["effets"])
            self.assertTrue(any(abs(e["effet_score"]) > 0 for e in impact["effets"]))

    def test_le_diagnostic_de_seuils_accompagne_la_simulation(self):
        """POST /api/simuler renvoie les garde-fous par strate."""
        corps = json.dumps({"parametres": {"tva_taux_normal": 1.0}, "avec_impacts": False}).encode()
        requete = urllib.request.Request(
            f"http://127.0.0.1:{self.__class__.port}/api/simuler",
            data=corps, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(requete, timeout=60) as reponse:
            donnees = json.loads(reponse.read().decode("utf-8"))
        diagnostic = donnees["diagnostic"]
        self.assertIn(diagnostic["niveau_global"], diagnostic["barème"])
        self.assertEqual(diagnostic["verdict"]["niveau"], diagnostic["niveau_global"])
        self.assertEqual(len(diagnostic["strates"]), 5)
        self.assertIn(diagnostic["population"]["niveau"], diagnostic["barème"])
        self.assertTrue(diagnostic["alertes"]
                        or diagnostic["niveau_global"] in ("tolerable", "favorable"))
        for alerte in diagnostic["alertes"]:
            self.assertNotIn("{", alerte["message"])
            self.assertIn(alerte["niveau"], diagnostic["barème"])
            self.assertIn(alerte["strate"], (1, 2, 3, 4, 5))
        for marge in diagnostic["marges"]:
            self.assertGreater(marge["marge"], 0)

    def test_simuler_levier_inconnu_refuse(self):
        try:
            statut, donnees = self._appel("/api/simuler", {"parametres": {"levier_bidon": 1.0}})
        except urllib.error.HTTPError as erreur:  # 400 attendu
            statut, donnees = erreur.code, json.loads(erreur.read().decode("utf-8"))
        self.assertEqual(statut, 400)
        self.assertIn("error", donnees)

    def test_comparer_les_presets(self):
        statut, donnees = self._appel("/api/comparer")
        self.assertEqual(statut, 200)
        self.assertEqual(len(donnees["comparaison"]), 13)
        for entree in donnees["comparaison"]:
            self.assertEqual(len(entree["scores"]), 20)

    def test_proxy_refuse_un_indicateur_inconnu(self):
        try:
            statut, _ = self._appel("/api/proxy?indicateur=inexistant")
        except urllib.error.HTTPError as erreur:
            statut = erreur.code
        self.assertEqual(statut, 400)

    def test_proxy_accepte_un_indicateur_du_registre(self):
        statut, donnees = self._appel("/api/proxy?indicateur=taux_oat_france_10ans")
        self.assertEqual(statut, 200)
        self.assertIn("lecture", donnees)
        self.assertIn("valeur", donnees["lecture"])

    def test_donnees_du_navigateur_recalibrent_le_contexte(self):
        """Un relevé posté par le navigateur doit remonter dans le contexte."""
        from unittest import mock

        releve = {
            "lectures": {
                "taux_oat_france_10ans": {
                    "valeur": 4.37, "periode": "2026-10", "fournisseur": "test",
                    "url": "https://example.org/", "statut": "live",
                }
            }
        }
        with mock.patch("simulateur.dashboard.charger_cache", return_value={}), \
             mock.patch("simulateur.dashboard.sauver_cache") as sauvegarde:
            statut, donnees = self._appel("/api/donnees", releve)
        self.assertEqual(statut, 200)
        self.assertTrue(sauvegarde.called)
        self.assertIn("contexte", donnees)
        self.assertAlmostEqual(donnees["contexte"]["taux_oat_10ans"], 4.37, places=2)

    def test_routes_inconnues_et_methodes_invalides(self):
        try:
            self._appel("/api/inexistant")
        except urllib.error.HTTPError as erreur:
            self.assertEqual(erreur.code, 404)
        else:  # pragma: no cover - garde-fou
            self.fail("une route inconnue doit répondre 404")
