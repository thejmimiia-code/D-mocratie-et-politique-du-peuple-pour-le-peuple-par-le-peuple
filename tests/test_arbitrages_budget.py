"""
tests/test_arbitrages_budget.py — Tests unitaires et d'intégration de la modélisation
des arbitrages budgétaires et de la gouvernance ministérielle de Bercy.
"""

import json
import unittest
from simulateur.model import (
    ProfilMinistreBudget,
    DirecteurCabinetBercy,
    JaugesSurvieBercy,
    StrateGouvernanceBudgetaireBercy,
    StrateBatailleDuBudget,
    ResultatEtapeSimulation,
)
from simulateur.moteur import MoteurSimulationSystemique
from simulateur.scenarios import (
    get_scenario_mandature_5_ans,
    get_scenario_statut_quo,
    get_scenario_austerite_brutale,
    get_scenario_choc_mondial_stagflation,
)


class TestArbitragesBudgétairesBercy(unittest.TestCase):
    """Vérification des mécaniques d'arbitrages budgétaires et de survie ministérielle à Bercy."""

    def test_structures_gouvernance_budgetaire(self):
        """Vérifie l'instanciation des profils de ministres et des directeurs de cabinet."""
        profil = ProfilMinistreBudget()
        self.assertEqual(profil.archetype, "universitaire")
        self.assertEqual(profil.popularite_initiale_pct, 50.0)
        self.assertEqual(profil.capital_politique_initial, 50.0)

        dircab = DirecteurCabinetBercy()
        self.assertEqual(dircab.archetype, "technocrate")
        self.assertEqual(dircab.efficience_reformes_structurelles_pct, 15.0)

        jauges = JaugesSurvieBercy()
        self.assertEqual(jauges.capital_politique, 50.0)
        self.assertEqual(jauges.popularite_ministre_pct, 50.0)
        self.assertEqual(jauges.seuil_alerte_matignon_pct, 15.0)
        self.assertEqual(jauges.seuil_demission_elysee_pct, 10.0)
        self.assertEqual(jauges.voix_motion_censure_potentielle, 140)

        strate = StrateGouvernanceBudgetaireBercy()
        self.assertEqual(strate.catalogue_mesures_count, 200)
        self.assertEqual(strate.seuil_censure_assemblee_voix, 289)
        self.assertEqual(strate.horizon_cible_deficit_2030, 3.0)

        # Compatibilité alias
        self.assertIs(StrateBatailleDuBudget, StrateGouvernanceBudgetaireBercy)

    def test_moteur_jauges_scenario_mandature(self):
        """Vérifie que le Plan de Mandature réussit l'assainissement sans démission ni censure."""
        moteur = MoteurSimulationSystemique()
        for dec in get_scenario_mandature_5_ans():
            moteur.appliquer_etape(dec)

        res5 = moteur.historique_etapes[-1]

        # 1. Déficit sous 3% avant 2030 (Objectif central des traités européens)
        self.assertLess(res5.ratio_deficit_pib, 3.0)
        self.assertAlmostEqual(res5.ratio_deficit_pib, 2.84, delta=0.2)

        # 2. Capital politique en forte hausse
        self.assertGreater(res5.capital_politique_ministre, 60.0)
        self.assertEqual(res5.capital_politique_ministre, res5.bataille_capital_politique)

        # 3. Popularité ministérielle au zénith (loin du seuil d'alerte de 15% et de démission à 10%)
        self.assertGreater(res5.popularite_ministre_pct, 55.0)
        self.assertFalse(res5.menace_demission_matignon)

        # 4. Motion de censure désarmée (loin des 289 voix)
        self.assertLess(res5.voix_censure_an, 289)
        self.assertFalse(res5.menace_censure_assemblee)

        # 5. Helper property
        gov = res5.gouvernance_budgetaire
        self.assertIsInstance(gov, StrateGouvernanceBudgetaireBercy)
        self.assertFalse(gov.jauges_survie.procedure_deficit_excessif_active)

    def test_moteur_austerite_brutale_chute_popularite(self):
        """Vérifie qu'une politique d'austérité brutale fait plonger la popularité sous le seuil d'alerte."""
        moteur = MoteurSimulationSystemique()
        etapes = []
        for dec in get_scenario_austerite_brutale():
            etapes.append(moteur.appliquer_etape(dec))

        res_aust5 = etapes[-1]

        # La popularité s'effondre face à la rigueur destructrice
        self.assertLess(res_aust5.popularite_ministre_pct, 30.0)

    def test_moteur_choc_mondial_tensions_spread(self):
        """Vérifie l'impact du choc mondial sur le spread obligataire OAT-Bund."""
        moteur = MoteurSimulationSystemique()
        for dec in get_scenario_choc_mondial_stagflation():
            moteur.appliquer_etape(dec)

        res_choc = moteur.historique_etapes[-1]
        self.assertGreater(res_choc.spread_oat_bund_pb, 75.0)


if __name__ == "__main__":
    unittest.main()
