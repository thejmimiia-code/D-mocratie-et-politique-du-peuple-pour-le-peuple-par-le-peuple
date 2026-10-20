"""tests/test_innovation_prospective.py — Tests unitaires et d'intégration de la R&D Innovation & Prospective."""

from __future__ import annotations

import io
import json
import sys
import unittest
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from simulateur import innovation_prospective as inno  # noqa: E402


class TestDiffusionInnovationEtPGF(unittest.TestCase):
    """Vérifie la modélisation mathématique de la diffusion logistique et des gains de PGF."""

    def test_coefficients_diffusion_monotones_et_bornes(self):
        valeurs = [inno.coefficient_diffusion_logistique(an) for an in range(1, 11)]
        # Doit être borné entre 0 et 1
        for v in valeurs:
            self.assertGreaterEqual(v, 0.0)
            self.assertLessEqual(v, 1.0)
        # Croissance monotone
        self.assertEqual(valeurs, sorted(valeurs))
        # À l'an 10, la diffusion est quasi-complète (> 95 %)
        self.assertGreater(valeurs[-1], 0.95)

    def test_delai_de_latence_respecte(self):
        """Avec un délai de latence de 1,5 an, l'année 1 ne produit aucune diffusion."""
        self.assertEqual(inno.coefficient_diffusion_logistique(1), 0.0)
        # Dès l'année 2, la diffusion commence
        self.assertGreater(inno.coefficient_diffusion_logistique(2), 0.0)

    def test_parametres_invalides_levent_erreur(self):
        with self.assertRaises(ValueError):
            inno.ParametresDiffusionRND(delai_latence_annees=-1.0)
        with self.assertRaises(ValueError):
            inno.ParametresDiffusionRND(annee_inflexion=15.0)
        with self.assertRaises(ValueError):
            inno.ParametresDiffusionRND(taux_retour_social_max=1.5)
        with self.assertRaises(ValueError):
            inno.coefficient_diffusion_logistique(0)
        with self.assertRaises(ValueError):
            inno.trajectoire_rendement_rnd(-5.0, horizon=5)
        with self.assertRaises(ValueError):
            inno.trajectoire_rendement_rnd(5.0, horizon=7)

    def test_trajectoire_rendement_rnd_quinquennale_et_decennale(self):
        t5 = inno.trajectoire_rendement_rnd(5.0, horizon=5)
        self.assertEqual(len(t5), 5)
        self.assertEqual(t5[0]["effort_cumule_mde"], 5.0)
        self.assertEqual(t5[-1]["effort_cumule_mde"], 25.0)
        self.assertGreater(t5[-1]["rendement_social_annuel_mde"], 0.0)

        t10 = inno.trajectoire_rendement_rnd(5.0, horizon=10)
        self.assertEqual(len(t10), 10)
        self.assertEqual(t10[-1]["effort_cumule_mde"], 50.0)
        # Vérification de la somme sectorielle
        for etape in t10:
            eco = etape["economies_sectorielles"]
            somme_eco = round(
                eco["energie_climat_mde"] + eco["sante_biotech_mde"] + eco["industrie_numerique_mde"], 2
            )
            self.assertAlmostEqual(somme_eco, etape["rendement_social_annuel_mde"], places=1)

    def test_croissance_pgf_proportionnelle_a_l_effort(self):
        t_faible = inno.trajectoire_rendement_rnd(2.0, horizon=5)
        t_fort = inno.trajectoire_rendement_rnd(10.0, horizon=5)
        self.assertGreater(t_fort[-1]["gain_pgf_points"], t_faible[-1]["gain_pgf_points"])


class TestPiliersProspective(unittest.TestCase):
    """Vérifie la cohérence et l'exhaustivité des 5 piliers de prospective technologique."""

    def test_les_cinq_piliers_sont_presents(self):
        self.assertEqual(len(inno.PILIERS_PROSPECTIVE), 5)
        cles = {p.cle for p in inno.PILIERS_PROSPECTIVE}
        attendu = {
            "ia_calcul_souverain",
            "energie_decarbonee_smr",
            "biotech_sante_souveraine",
            "materiaux_critiques_recyclage",
            "agroecologie_eau_climat",
        }
        self.assertEqual(cles, attendu)

    def test_chaque_pilier_a_des_jalons_chronologiques_valides(self):
        for p in inno.PILIERS_PROSPECTIVE:
            with self.subTest(cle=p.cle):
                annees = sorted(p.jalons_temporels.keys())
                self.assertGreaterEqual(len(annees), 3)
                self.assertGreaterEqual(min(annees), 2026)
                self.assertLessEqual(max(annees), 2040)
                self.assertGreater(len(p.signaux_qui_renforcent), 20)
                self.assertGreater(len(p.signaux_contraires), 20)
                self.assertGreater(len(p.verrous_scientifiques_et_industriels), 20)
                self.assertIn("TRL", p.maturite_initiale_trl)


class TestCompteStocksResilience(unittest.TestCase):
    """Vérifie le compte ressources/emplois et la fin de l'hypothèse de gratuité des stocks."""

    def test_non_gratuite_des_stocks(self):
        compte = inno.compte_ressources_emplois_resilience(horizon_annees=5)
        self.assertGreater(compte["valeur_totale_capital_immobilise_mde"], 20.0)
        self.assertGreater(compte["charge_budgetaire_annuelle_mde"], 1.0)
        self.assertGreater(compte["charge_budgetaire_cumulee_horizon_mde"], 5.0)

    def test_conservation_comptable_ressources_emplois(self):
        compte = inno.compte_ressources_emplois_resilience(horizon_annees=10)
        total_portage = sum(d["cout_portage_annuel_mde"] for d in compte["details_par_stock"])
        total_amort = sum(d["amortissement_annuel_mde"] for d in compte["details_par_stock"])
        self.assertAlmostEqual(compte["cout_portage_annuel_total_mde"], total_portage, places=2)
        self.assertAlmostEqual(compte["amortissement_annuel_infrastructures_mde"], total_amort, places=2)

    def test_stocks_parametres_invalides_levent_erreur(self):
        with self.assertRaises(ValueError):
            inno.StockResilience("Test", "energie", volume_mois=-1.0, cout_acquisition_mde_par_mois=1.0)
        with self.assertRaises(ValueError):
            inno.StockResilience("Test", "energie", volume_mois=3.0, cout_acquisition_mde_par_mois=-1.0)
        with self.assertRaises(ValueError):
            inno.StockResilience("Test", "energie", volume_mois=3.0, cout_acquisition_mde_par_mois=1.0,
                                 duree_amortissement_annees=15)
        with self.assertRaises(ValueError):
            inno.compte_ressources_emplois_resilience(horizon_annees=3)


class TestStressTestInnovationResilience(unittest.TestCase):
    """Vérifie l'exécution des stress-tests croisés."""

    def test_tous_les_scenarios_de_choc_sont_executables(self):
        for cle in inno.SCENARIOS_CHOCS_PROSPECTIFS:
            with self.subTest(choc=cle):
                res = inno.stress_test_innovation_resilience(cle_choc=cle, horizon_annees=5)
                self.assertIn("perte_cumulee_temoin_mde", res)
                self.assertIn("perte_cumulee_combinee_mde", res)
                self.assertIn("gain_net_cumule_mde", res)
                self.assertGreater(res["gain_net_cumule_mde"], 0.0)
                self.assertGreater(res["ratio_cout_benefice_resilience"], 1.0)

    def test_la_combinaison_est_plus_protectrice_que_les_actions_isolees(self):
        res5 = inno.stress_test_innovation_resilience(
            effort_rnd_annuel_mde=5.0,
            avec_stocks_resilience=True,
            cle_choc="stagflation_multi_theatres",
            horizon_annees=5,
        )
        self.assertLess(res5["perte_cumulee_combinee_mde"], res5["perte_cumulee_temoin_mde"])
        self.assertLess(res5["perte_cumulee_combinee_mde"], res5["perte_cumulee_rnd_seule_mde"])

        # À 10 ans (deux mandatures), la R&D arrive à pleine maturité et surpasse les stocks seuls
        res10 = inno.stress_test_innovation_resilience(
            effort_rnd_annuel_mde=5.0,
            avec_stocks_resilience=True,
            cle_choc="stagflation_multi_theatres",
            horizon_annees=10,
        )
        self.assertLess(res10["perte_cumulee_combinee_mde"], res10["perte_cumulee_temoin_mde"])
        self.assertLess(res10["perte_cumulee_combinee_mde"], res10["perte_cumulee_stocks_seuls_mde"])
        self.assertLess(res10["perte_cumulee_combinee_mde"], res10["perte_cumulee_rnd_seule_mde"])

    def test_scenarios_inconnus_levent_erreur(self):
        with self.assertRaises(ValueError):
            inno.stress_test_innovation_resilience(cle_choc="choc_inexistant")


class TestRapportEtCLI(unittest.TestCase):
    """Vérifie la génération du rapport et le fonctionnement de la CLI."""

    def test_rapport_structure(self):
        rapport = inno.rapport_prospective_innovation(date(2026, 10, 20), horizon=5)
        self.assertEqual(rapport["date_evaluation"], "2026-10-20")
        self.assertEqual(rapport["horizon_annees"], 5)
        self.assertEqual(len(rapport["piliers_prospective"]), 5)
        self.assertIn("avertissement", rapport)
        self.assertIn("aucune probabilité", rapport["avertissement"].lower())

    def test_lignes_rapport_non_vides(self):
        lignes = inno.lignes_rapport(date(2026, 10, 20), horizon=5)
        self.assertGreater(len(lignes), 15)
        texte = "\n".join(lignes)
        self.assertIn("RAPPORT R&D, INNOVATION & PROSPECTIVE", texte)
        self.assertIn("Piliers de Prospective", texte)
        self.assertIn("Compte Économique des Stocks", texte)

    def test_main_cli(self):
        anc = sys.stdout
        try:
            sys.stdout = io.StringIO()
            code_0 = inno.main(["--json", "--horizon", "5"])
            self.assertEqual(code_0, 0)
            data = json.loads(sys.stdout.getvalue())
            self.assertEqual(data["horizon_annees"], 5)

            sys.stdout = io.StringIO()
            code_texte = inno.main(["--horizon", "10"])
            self.assertEqual(code_texte, 0)
            self.assertIn("Horizon 10 ans", sys.stdout.getvalue())

            sys.stdout = io.StringIO()
            code_err = inno.main(["--depart", "date_invalide"])
            self.assertEqual(code_err, 2)
        finally:
            sys.stdout = anc


if __name__ == "__main__":
    unittest.main()
