"""
tests/test_extension_eva.py — Tests unitaires de l'extension ÉVA Simulateur Politique (Protocole 4.2.3).
"""

import unittest
import asyncio
from extension_eva.main import ExtensionSimulateurPolitique, EventBus, EVENEMENT_DEMANDE, EVENEMENT_REPONSE


class TestExtensionSimulateurPolitique(unittest.TestCase):

    def setUp(self):
        self.ext = ExtensionSimulateurPolitique("politique.simulateur.test")

    def test_instanciation_id_obligatoire(self):
        """Vérifie que l'ID de l'extension est obligatoire (§4 Protocole)."""
        with self.assertRaises(ValueError):
            ExtensionSimulateurPolitique("")

    def test_cycle_de_vie(self):
        """Vérifie install, start, health_check et stop."""
        async def run_lifecycle():
            installed = await self.ext.install()
            self.assertTrue(installed)

            await self.ext.start()
            self.assertTrue(self.ext._initialized)

            health = await self.ext.health_check()
            self.assertEqual(health["status"], "healthy")
            self.assertIn("Gigogne 4 échelons", health["modele"])

            await self.ext.stop()
            self.assertFalse(self.ext._initialized)

            health_stopped = await self.ext.health_check()
            self.assertEqual(health_stopped["status"], "degraded")

        asyncio.run(run_lifecycle())

    def test_on_event_mandature(self):
        """Vérifie le traitement d'une demande de scénario 'mandature'."""
        donnees = {"scenario": "mandature", "annee_cible": 5}
        reponse = self.ext.on_event(donnees)
        self.assertTrue(reponse["publie"])
        payload = reponse["reponse"]
        self.assertEqual(payload["scenario"], "mandature")
        self.assertEqual(len(payload["resultats_trajectoire"]), 5)

        annee5 = payload["synthese_annee_cible"]
        self.assertEqual(annee5["annee"], 5)
        self.assertLess(annee5["ratio_deficit_pib"], 3.0)
        self.assertTrue(annee5["pde_europe_conforme"])

    def test_on_event_choc_mondial(self):
        """Vérifie le traitement d'une demande de scénario 'choc_mondial'."""
        donnees = {"scenario": "choc_mondial", "annee_cible": 3}
        reponse = self.ext.on_event(donnees)
        self.assertTrue(reponse["publie"])
        payload = reponse["reponse"]
        self.assertEqual(payload["scenario"], "choc_mondial")
        self.assertEqual(len(payload["resultats_trajectoire"]), 3)


if __name__ == "__main__":
    unittest.main()
