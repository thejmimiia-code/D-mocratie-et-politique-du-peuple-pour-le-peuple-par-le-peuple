"""
tests/test_simulateur.py — Tests d'intégration et de cohérence des 4 strates.
"""

import unittest

from simulateur.model import (
    DecisionPolitique,
)
from simulateur.moteur import MoteurSimulationSystemique
from simulateur.scenarios import (
    get_scenario_mandature_5_ans,
)


class TestSimulateurQuatreStrates(unittest.TestCase):

    def setUp(self):
        self.moteur = MoteurSimulationSystemique()

    def test_initialisation_strates(self):
        """Vérifie la présence et le calibrage initial des 4 strates."""
        # 1. Local
        self.assertEqual(self.moteur.local.bloc_communal.taxe_fonciere_tfpb_mde, 39.5)
        # 2. National
        self.assertEqual(self.moteur.national.pib_nominal_mde, 3015.0)
        self.assertEqual(self.moteur.national.dette_maastricht_stock_mde, 3568.0)
        # 3. Europe
        self.assertEqual(self.moteur.europe.seuil_deficit_pde_pct, 3.0)
        self.assertTrue(self.moteur.europe.statut_pde_actif)
        # 4. Mondial
        self.assertEqual(self.moteur.mondial.part_dette_detenue_non_residents, 0.558)
        self.assertEqual(self.moteur.mondial.spread_oat_bund_bps, 88.0)

    def test_scenario_mandature_atterrissage_complet(self):
        """Vérifie le redressement complet à travers les 4 strates en An 5."""
        decisions = get_scenario_mandature_5_ans()
        self.assertEqual(len(decisions), 5)

        for dec in decisions:
            self.moteur.appliquer_etape(dec)

        res_final = self.moteur.historique_etapes[-1]

        # Validation Strate Nationale & Européenne : Déficit < 3.0%
        self.assertLess(res_final.ratio_deficit_pib, 3.0)
        self.assertFalse(res_final.statut_pde_europe)
        self.assertTrue(res_final.bouclier_tpi_actif)

        # Validation Strate Mondiale : Spread resserré, taux OAT apaisé
        self.assertLess(res_final.spread_bund_bps, 55.0)
        self.assertLess(res_final.taux_oat_pct, 3.50)
        self.assertEqual(res_final.note_souveraine, "AA")

        # Validation Strate Locale : Tension sociale pacifiée, confiance haute
        self.assertLess(res_final.tension_sociale_locale, 15.0)
        self.assertGreater(res_final.confiance_democratique, 60.0)

    def test_regle_or_cgct_baisse_dgf_report_foncier(self):
        """Vérifie la règle d'or (art. L. 1612-4 CGCT) : couper la DGF force la hausse foncière."""
        moteur = MoteurSimulationSystemique()
        foncier_initial = moteur.local.bloc_communal.taxe_fonciere_tfpb_mde
        tension_initiale = moteur.local.tension_sociale_territoriale

        # Coupe de 6 Md€ de DGF
        dec = DecisionPolitique(annee=1, delta_dotation_dgf_mde=-6.0)
        res = moteur.appliquer_etape(dec)

        self.assertGreater(res.produit_taxe_fonciere_mde, foncier_initial)
        self.assertGreater(res.tension_sociale_locale, tension_initiale)

    def test_restitution_tva_energie_et_baisse_tension(self):
        """Vérifie que la baisse de TVA sur l'énergie désamorce la tension locale et soutient le pouvoir d'achat."""
        moteur = MoteurSimulationSystemique()
        pouvoir_initial = moteur.national.pouvoir_achat_menages_index
        tension_initiale = moteur.local.tension_sociale_territoriale

        dec = DecisionPolitique(annee=1, baisse_tva_energie_5_5_mde=9.0)
        res = moteur.appliquer_etape(dec)

        self.assertGreater(res.pouvoir_achat_index, pouvoir_initial)
        self.assertLess(res.tension_sociale_locale, tension_initiale)

    def test_corpus_juridique_et_reglements(self):
        """Vérifie la présence et l'interrogation du corpus juridique de référence."""
        from simulateur.reglements_lois import get_corpus_lois, rechercher_loi
        corpus = get_corpus_lois()
        self.assertIn("CONST_ART_2", corpus)
        self.assertIn("CGCT_L1612_4", corpus)
        self.assertIn("DIR_TVA_2022_542", corpus)
        self.assertIn("CP_432_10", corpus)

        # Recherche par mot-clé
        resultats_tva = rechercher_loi("TVA")
        self.assertGreater(len(resultats_tva), 0)
        self.assertTrue(any(r.identifiant == "DIR_TVA_2022_542" for r in resultats_tva))

    def test_indexation_pib_recettes_fiscales(self):
        """Issue #4 : les recettes fiscales de base sont indexées sur la croissance du PIB."""
        moteur = MoteurSimulationSystemique()

        # An 1 : aucune croissance → indexation = 1.0 → recettes = 1565.0
        dec1 = DecisionPolitique(annee=1)
        r1 = moteur.appliquer_etape(dec1)
        # Les recettes de base sont 1565.0 * 1.0 (aucune croissance en An 1)
        self.assertAlmostEqual(r1.recettes_publiques_totales_mde, 1565.0, delta=0.1)

        # An 5 : PIB a croi en 1.9%/an → recettes indexées > 1565.0
        # pib_t = 3015 * 1.019^4 = 3249.2 → indexation = 1.0776
        # recettes_base = 1565.0 * 1.0776 = 1686.4
        dec5 = DecisionPolitique(annee=5)
        r5 = moteur.appliquer_etape(dec5)
        self.assertGreater(r5.recettes_publiques_totales_mde, 1565.0)
        self.assertGreater(r5.recettes_publiques_totales_mde, 1650.0)

    def test_transmission_progressive_taux_oat_vers_charge_dette(self):
        """Issue #4 : seulement ~35 % du changement de taux OAT impacte la charge de dette (roll-over 8,5 ans)."""
        moteur = MoteurSimulationSystemique()
        # Décision vide An 1 → effort_structurel_net = 0 (≤ 0) → spread OAT-Bund = 96 bp, OAT = 4.26 %
        dec = DecisionPolitique(annee=1)
        r = moteur.appliquer_etape(dec)

        # Transmission progressive : ecart = 4.26 - 4.18 = +0.08
        # Ajustement sans transmission = 0.08 * 11.5 = 0.92
        # Ajustement avec transmission = 0.92 * 0.35 = 0.32
        # charge = max(48.0, 66.5 + 0.32) = 66.82
        self.assertAlmostEqual(r.charge_dette_mde, 66.82, delta=0.1)
        # Vérifie que le taux OAT et le spread sont bien calculés
        self.assertEqual(r.taux_oat_pct, 4.26)
        self.assertEqual(r.spread_bund_bps, 96.0)

    def test_mandature_an5_superavit_hors_pde(self):
        """Issue #4 : le scénario mandature atteint un superavit à l'An 5 (-0,73 %) grâce à l'indexation PIB."""
        decisions = get_scenario_mandature_5_ans()
        for dec in decisions:
            self.moteur.appliquer_etape(dec)
        res_final = self.moteur.historique_etapes[-1]
        # Après le fix #4, le déficit est sous 3% et atteint un superavit
        self.assertAlmostEqual(res_final.ratio_deficit_pib, -0.73, delta=0.1)
        self.assertLess(res_final.ratio_deficit_pib, 0.0)  # Superavit
        self.assertFalse(res_final.statut_pde_europe)
        self.assertEqual(res_final.note_souveraine, "AA")


if __name__ == "__main__":
    unittest.main()
