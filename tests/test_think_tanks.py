"""
tests/test_think_tanks.py — Validation unitaire et intégration de l'audit contradictoire
des Think Tanks (Local à International) et des 5 paradigmes de stress-test.
"""

import unittest
import urllib.request
import json
import socket
import threading
import time

from simulateur.think_tanks import (
    REGISTRE_THINK_TANKS,
    PARADIGMES_STRESS_TEST,
    get_think_tank,
    lister_think_tanks_par_echelon,
    exporter_catalogue_think_tanks,
    executer_stress_tests_mandature,
    ThinkTankAudit,
    ResultatStressTestThinkTank,
)
from simulateur.web_server import ThreadedHTTPServer, SimulateurHTTPHandler


class TestThinkTanksAudit(unittest.TestCase):
    """Tests d'exhaustivité et de cohérence scientifique du registre des think tanks."""

    def test_registre_exhaustivite_et_completude(self):
        """Vérifie que les 23 think tanks sont documentés avec tous les champs requis."""
        self.assertEqual(len(REGISTRE_THINK_TANKS), 23, "Le registre doit comporter exactement 23 think tanks.")

        for tt_id, tt in REGISTRE_THINK_TANKS.items():
            self.assertEqual(tt_id, tt.id)
            self.assertTrue(len(tt.nom) > 3, f"Nom trop court pour {tt_id}")
            self.assertTrue(len(tt.sigle) >= 2, f"Sigle manquant pour {tt_id}")
            self.assertIn(tt.echelon, ["local", "national", "europeen", "international"], f"Échelon invalide pour {tt_id}")
            self.assertTrue(len(tt.pays_siege) > 2, f"Siège manquant pour {tt_id}")
            self.assertTrue(len(tt.epistemologie) > 5, f"Épistémologie manquante pour {tt_id}")
            self.assertTrue(len(tt.directeur_ou_fondateur) > 2, f"Direction manquante pour {tt_id}")

            # Publications clés
            self.assertTrue(len(tt.sources_cles) >= 1, f"Au moins une publication clé requise pour {tt_id}")
            for pub in tt.sources_cles:
                self.assertTrue(len(pub.titre) > 5)
                self.assertTrue(pub.url.startswith("http"), f"URL invalide dans {tt_id}: {pub.url}")
                self.assertTrue(pub.annee >= 2023, f"Année obsolète (<2023) pour {tt_id}: {pub.annee}")
                self.assertTrue(len(pub.auteurs) > 2)
                self.assertTrue(len(pub.resume_methodologique) > 20)

            # Hypothèses et objections
            self.assertTrue(len(tt.hypotheses_et_parametres) >= 2, f"Paramètres insuffisants pour {tt_id}")
            self.assertTrue(len(tt.objections_anticipees) >= 1, f"Objection manquante pour {tt_id}")
            self.assertTrue(len(tt.pourquoi_integration) > 30, f"Raison d'intégration trop courte pour {tt_id}")
            self.assertTrue(len(tt.reponse_du_simulateur) > 30, f"Réponse simulateur trop courte pour {tt_id}")
            self.assertIn(tt.stress_test_associe, PARADIGMES_STRESS_TEST, f"Paradigme associé inconnu pour {tt_id}")

    def test_couverture_equilibrée_des_4_echelons(self):
        """Vérifie que chaque strate (Local, National, UE, Mondial) est rigoureusement couverte."""
        locaux = lister_think_tanks_par_echelon("local")
        nationaux = lister_think_tanks_par_echelon("national")
        europeens = lister_think_tanks_par_echelon("europeen")
        internationaux = lister_think_tanks_par_echelon("international")

        self.assertEqual(len(locaux), 4, "Doit comporter 4 think tanks territoriaux/locaux (OFGL, AMF, CEREMA, I4CE)")
        self.assertEqual(len(nationaux), 10, "Doit comporter 10 think tanks nationaux français")
        self.assertEqual(len(europeens), 4, "Doit comporter 4 think tanks européens (Bruegel, CEPS, Delors, Bertelsmann)")
        self.assertEqual(len(internationaux), 5, "Doit comporter 5 think tanks mondiaux (PIIE, WID, TJN, INET, Brookings)")

    def test_fonctions_recherche_et_export(self):
        """Teste get_think_tank, lister et export catalogue."""
        ofce = get_think_tank("ofce")
        self.assertIsNotNone(ofce)
        self.assertEqual(ofce.sigle, "OFCE")

        inconnu = get_think_tank("non_existant")
        self.assertIsNone(inconnu)

        export = exporter_catalogue_think_tanks()
        self.assertIn("metadonnees", export)
        self.assertEqual(export["metadonnees"]["total_think_tanks"], 23)
        self.assertIn("think_tanks", export)
        self.assertEqual(len(export["think_tanks"]), 23)

    def test_execution_stress_tests_mandature(self):
        """Teste l'évaluation contradictoire des 5 paradigmes de stress-test."""
        resultats = executer_stress_tests_mandature(None, None, None, None, None)

        self.assertEqual(len(resultats), 5, "Les 5 paradigmes doivent être tous évalués.")
        self.assertIn("liberal_competitivite", resultats)
        self.assertIn("post_keynesien_social", resultats)
        self.assertIn("biophysique_climat", resultats)
        self.assertIn("territorial_decentralise", resultats)
        self.assertIn("ordoliberal_international", resultats)

        for p_id, st in resultats.items():
            self.assertIsInstance(st, ResultatStressTestThinkTank)
            self.assertEqual(st.paradigme_id, p_id)
            self.assertEqual(st.statut, "SOLIDE", f"Le paradigme {p_id} devrait être SOLIDE pour le plan mandature")
            self.assertEqual(st.score_robustesse_sur_100, 100.0, f"Le score de {p_id} doit être 100%")
            self.assertTrue(len(st.objections_relevees) >= 1)
            self.assertTrue(len(st.reponses_systemiques) >= 1)
            self.assertTrue(len(st.justification_scientifique) > 20)

            # Vérification des critères individuels
            for crit_nom, crit_info in st.criteres_analyses.items():
                self.assertTrue(crit_info["conforme"], f"Le critère {crit_nom} dans {p_id} doit être conforme")


class TestThinkTanksAPI(unittest.TestCase):
    """Tests d'intégration des endpoints API HTTP pour les think tanks et stress tests."""

    @classmethod
    def setUpClass(cls):
        """Lance un serveur HTTP de test sur un port éphémère."""
        cls.server = ThreadedHTTPServer(("127.0.0.1", 0), SimulateurHTTPHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.daemon = True
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        """Arrête le serveur HTTP."""
        cls.server.shutdown()

    def test_api_think_tanks_global(self):
        """GET /api/think_tanks retourne les 23 think tanks."""
        url = f"http://127.0.0.1:{self.port}/api/think_tanks"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertEqual(data["total"], 23)
            self.assertEqual(len(data["think_tanks"]), 23)

    def test_api_think_tanks_filtre_echelon(self):
        """GET /api/think_tanks?echelon=local retourne 4 instituts."""
        url = f"http://127.0.0.1:{self.port}/api/think_tanks?echelon=local"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertEqual(data["total"], 4)
            for tt in data["think_tanks"]:
                self.assertEqual(tt["echelon"], "local")

    def test_api_think_tanks_recherche(self):
        """GET /api/think_tanks?q=Montaigne retourne l'Institut Montaigne."""
        url = f"http://127.0.0.1:{self.port}/api/think_tanks?q=Montaigne"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertTrue(data["total"] >= 1)
            ids = [t["id"] for t in data["think_tanks"]]
            self.assertIn("institut_montaigne", ids)

    def test_api_think_tank_detail(self):
        """GET /api/think_tanks/bruegel retourne la fiche complète de Bruegel."""
        url = f"http://127.0.0.1:{self.port}/api/think_tanks/bruegel"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            tt = json.loads(resp.read().decode())
            self.assertEqual(tt["id"], "bruegel")
            self.assertEqual(tt["sigle"], "Bruegel")
            self.assertEqual(tt["echelon"], "europeen")
            self.assertTrue(len(tt["sources_cles"]) >= 2)

    def test_api_think_tank_404(self):
        """GET /api/think_tanks/inconnu retourne 404."""
        url = f"http://127.0.0.1:{self.port}/api/think_tanks/inconnu"
        try:
            with urllib.request.urlopen(url) as resp:
                self.assertEqual(resp.status, 404)
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)

    def test_api_stress_tests(self):
        """GET /api/stress_tests retourne l'évaluation des 5 stress-tests."""
        url = f"http://127.0.0.1:{self.port}/api/stress_tests"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertIn("resultats", data)
            self.assertEqual(len(data["resultats"]), 5)
            self.assertEqual(data["statut_global"], "TOUS CONFORMES ET RÉSISTANTS")


if __name__ == "__main__":
    unittest.main()
