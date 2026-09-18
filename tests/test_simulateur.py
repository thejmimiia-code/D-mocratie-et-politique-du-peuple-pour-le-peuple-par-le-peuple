"""
tests/test_simulateur.py — Tests d'intégration et de cohérence des 4 strates.
"""

import unittest
from simulateur.model import (
    EchelonLocal,
    EchelonNational,
    EchelonEuropeen,
    EchelonMondial,
    DecisionPolitique,
)
from simulateur.moteur import MoteurSimulationSystemique
from simulateur.scenarios import (
    get_scenario_mandature_5_ans,
    get_scenario_statut_quo,
    get_scenario_austerite_brutale,
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


if __name__ == "__main__":
    unittest.main()
