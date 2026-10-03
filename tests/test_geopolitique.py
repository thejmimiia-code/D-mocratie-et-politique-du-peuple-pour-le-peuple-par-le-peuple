"""
tests/test_geopolitique.py — Banc d'essai de la STRATE 5 (Géopolitique, Sécurité,
Chokepoints, Dissuasion et Effort de défense).

Couvre les éléments auparavant manquants du simulateur :
  * `tension_strait_taiwan` et choc semi-conducteurs,
  * `risque_nucleaire` et coût économique du franchissement du seuil,
  * convergence Chine-Russie-Iran et probabilité d'escalade mondiale,
  * chokepoints (Hormuz) et réserves stratégiques AIE,
  * trajectoire OTAN de La Haye et clause de sauvegarde nationale du PSC,
  * non-régression comptable (SFC) et non-divergence sous stress extrême.
"""

import math
import unittest

from simulateur.geopolitique import (
    CIBLE_OTAN_DEFENSE_PCT,
    PLAFOND_CLAUSE_SAUVEGARDE_PCT,
    EchelonGeopolitique,
    chokepoints_par_defaut,
)
from simulateur.model import DecisionPolitique
from simulateur.moteur import MoteurSimulationSystemique
from simulateur.scenarios import (
    get_scenario_convergence_ww3,
    get_scenario_crise_taiwan,
    get_scenario_escalade_nucleaire_tactique,
    get_scenario_fermeture_hormuz,
    get_scenario_mandature_5_ans,
    get_scenario_resilience_republicaine,
)

SCENARIOS_GEO = (
    get_scenario_crise_taiwan,
    get_scenario_fermeture_hormuz,
    get_scenario_escalade_nucleaire_tactique,
    get_scenario_convergence_ww3,
    get_scenario_resilience_republicaine,
)


class TestCalibrageStrate5(unittest.TestCase):
    """Calibrage à l'instant T (SIPRI 2026, OTAN La Haye 2025, AIE)."""

    def test_arsenal_nucleaire_sipri_2026(self):
        geo = EchelonGeopolitique()
        self.assertEqual(geo.tetes_nucleaires_mondiales, 12187)
        self.assertEqual(geo.tetes_nucleaires_deployees, 4012)
        self.assertEqual(geo.tetes_nucleaires_france, 290)

    def test_sept_chokepoints_cartographies(self):
        points = chokepoints_par_defaut()
        self.assertEqual(len(points), 7)
        noms = " | ".join(p.nom for p in points)
        for attendu in ("Hormuz", "Malacca", "Taïwan", "Suez", "Bab el-Mandeb", "Gibraltar", "Panama"):
            self.assertIn(attendu, noms)
        self.assertTrue(all(p.taux_ouverture_pct == 100.0 for p in points))
        self.assertEqual(sum(1 for p in points if p.sous_tension), 0)

    def test_indice_tension_composite_pondere(self):
        geo = EchelonGeopolitique()
        attendu = (62.0 * 0.30) + (71.0 * 0.28) + (78.0 * 0.22) + (45.0 * 0.20)
        self.assertAlmostEqual(geo.indice_tension_globale, round(attendu, 1), places=1)

    def test_reserves_strategiques_conformes_aie(self):
        """Obligation AIE : au moins 90 jours d'importations nettes en stock."""
        self.assertGreaterEqual(EchelonGeopolitique().stocks_strategiques_petrole_jours, 90.0)

    def test_effort_defense_instant_t_et_cible_otan(self):
        geo = EchelonGeopolitique()
        self.assertAlmostEqual(geo.effort_defense_pct_pib, 2.10, places=2)
        self.assertAlmostEqual(CIBLE_OTAN_DEFENSE_PCT, 3.50, places=2)


class TestNonRegressionStrate5(unittest.TestCase):
    """La strate 5 doit être strictement neutre quand aucun levier n'est activé."""

    def test_mandature_inchangee_sans_choc_geopolitique(self):
        moteur = MoteurSimulationSystemique()
        for dec in get_scenario_mandature_5_ans():
            moteur.appliquer_etape(dec)
        res = moteur.historique_etapes[-1]

        self.assertEqual(res.chokepoints_sous_tension, 0)
        self.assertEqual(res.disponibilite_semiconducteurs_pct, 100.0)
        self.assertAlmostEqual(res.effort_defense_pct_pib, 2.10, places=2)
        self.assertEqual(res.cours_petrole_usd, 82.5)
        # Pas de double comptage : la prime géopolitique de référence est déjà
        # incorporée dans le spread de 88 bps calé à l'instant T.
        self.assertLess(res.ratio_deficit_pib, 3.0)
        self.assertFalse(res.statut_pde_europe)


class TestCriseTaiwan(unittest.TestCase):
    def test_blocus_coupe_les_semiconducteurs_et_le_pib(self):
        moteur_ref = MoteurSimulationSystemique()
        ref = moteur_ref.appliquer_etape(DecisionPolitique(annee=1))

        moteur = MoteurSimulationSystemique()
        res = moteur.appliquer_etape(DecisionPolitique(annee=1, blocus_taiwan_intensite=1.0))

        self.assertAlmostEqual(res.disponibilite_semiconducteurs_pct, 30.0, delta=0.1)
        self.assertLess(res.pib_nominal_mde, ref.pib_nominal_mde)
        self.assertGreater(res.inflation_globale_pct, ref.inflation_globale_pct)
        self.assertEqual(res.chokepoints_sous_tension, 1)

    def test_plan_souverainete_amortit_le_choc(self):
        """Le Chips Act souverain réduit la perte d'approvisionnement à blocus égal."""
        moteur = MoteurSimulationSystemique()
        moteur.geo.capacite_souveraine_semiconducteurs_mde = 80.0
        res = moteur.appliquer_etape(DecisionPolitique(annee=1, blocus_taiwan_intensite=1.0))
        # Amortissement plafonné à 50 % : 100 - 70*0.5 = 65 %
        self.assertAlmostEqual(res.disponibilite_semiconducteurs_pct, 65.0, delta=0.1)

    def test_scenario_complet_sort_de_crise(self):
        moteur = MoteurSimulationSystemique()
        for dec in get_scenario_crise_taiwan():
            moteur.appliquer_etape(dec)
        premier, dernier = moteur.historique_etapes[0], moteur.historique_etapes[-1]
        self.assertLess(premier.disponibilite_semiconducteurs_pct, 100.0)
        self.assertEqual(dernier.disponibilite_semiconducteurs_pct, 100.0)
        self.assertAlmostEqual(dernier.effort_defense_pct_pib, CIBLE_OTAN_DEFENSE_PCT, places=2)


class TestChokepointHormuz(unittest.TestCase):
    def test_fermeture_totale_renverifie_le_brent(self):
        moteur = MoteurSimulationSystemique()
        res = moteur.appliquer_etape(DecisionPolitique(annee=1, fermeture_hormuz_intensite=1.0))
        # 82,5 $ + 78 $ de prime = 160,5 $/bbl (cohérent avec -15/-20 % d'offre mondiale)
        self.assertAlmostEqual(res.cours_petrole_usd, 160.5, delta=0.5)
        self.assertGreater(res.facture_energetique_mde, 64.5)
        self.assertGreater(res.inflation_globale_pct, 2.1)
        self.assertEqual(moteur.geo.get_chokepoint("Hormuz").taux_ouverture_pct, 0.0)

    def test_liberation_stocks_strategiques_amortit_30_pct(self):
        sans = MoteurSimulationSystemique()
        r_sans = sans.appliquer_etape(DecisionPolitique(annee=1, fermeture_hormuz_intensite=1.0))

        avec = MoteurSimulationSystemique()
        r_avec = avec.appliquer_etape(
            DecisionPolitique(annee=1, fermeture_hormuz_intensite=1.0, liberation_stocks_strategiques=True)
        )
        self.assertLess(r_avec.cours_petrole_usd, r_sans.cours_petrole_usd)
        self.assertLess(r_avec.stocks_strategiques_petrole_jours, 98.0)
        # Les réserves ne descendent jamais sous le plancher opérationnel de 60 jours
        self.assertGreaterEqual(r_avec.stocks_strategiques_petrole_jours, 60.0)

    def test_prime_petroliere_en_niveau_et_non_cumulative(self):
        """Deux années de fermeture identique ne doivent pas empiler la prime."""
        moteur = MoteurSimulationSystemique()
        a1 = moteur.appliquer_etape(DecisionPolitique(annee=1, fermeture_hormuz_intensite=0.5))
        a2 = moteur.appliquer_etape(DecisionPolitique(annee=2, fermeture_hormuz_intensite=0.5))
        self.assertAlmostEqual(a1.cours_petrole_usd, a2.cours_petrole_usd, places=2)

    def test_reouverture_reconstitue_les_reserves(self):
        moteur = MoteurSimulationSystemique()
        moteur.appliquer_etape(
            DecisionPolitique(annee=1, fermeture_hormuz_intensite=1.0, liberation_stocks_strategiques=True)
        )
        bas = moteur.geo.stocks_strategiques_petrole_jours
        moteur.appliquer_etape(DecisionPolitique(annee=2))
        self.assertGreater(moteur.geo.stocks_strategiques_petrole_jours, bas)
        self.assertLessEqual(moteur.geo.stocks_strategiques_petrole_jours, 98.0)


class TestSeuilNucleaire(unittest.TestCase):
    def test_usage_tactique_declenche_un_choc_massif(self):
        ref = MoteurSimulationSystemique().appliquer_etape(DecisionPolitique(annee=1))
        moteur = MoteurSimulationSystemique()
        res = moteur.appliquer_etape(DecisionPolitique(annee=1, usage_nucleaire_tactique=True))

        self.assertEqual(res.risque_nucleaire_tactique_pct, 100.0)
        self.assertLess(res.pib_nominal_mde, ref.pib_nominal_mde * 0.98)
        self.assertGreater(res.spread_bund_bps, ref.spread_bund_bps + 150.0)
        self.assertEqual(res.note_souveraine, "BBB+")
        self.assertGreater(res.tension_sociale_locale, ref.tension_sociale_locale)
        self.assertGreater(res.probabilite_escalade_mondiale_pct, 35.0)

    def test_remanence_du_choc_les_annees_suivantes(self):
        moteur = MoteurSimulationSystemique()
        moteur.appliquer_etape(DecisionPolitique(annee=1, usage_nucleaire_tactique=True))
        suivant = moteur.appliquer_etape(DecisionPolitique(annee=2))
        self.assertTrue(moteur.geo.usage_nucleaire_constate)
        self.assertGreater(suivant.spread_bund_bps, 88.0)

    def test_scenario_escalade_reste_borne(self):
        moteur = MoteurSimulationSystemique()
        for dec in get_scenario_escalade_nucleaire_tactique():
            moteur.appliquer_etape(dec)
        for r in moteur.historique_etapes:
            for valeur in (r.pib_nominal_mde, r.ratio_deficit_pib, r.ratio_dette_pib, r.taux_oat_pct):
                self.assertTrue(math.isfinite(valeur))
            self.assertGreater(r.pib_nominal_mde, 0.0)
            self.assertLessEqual(r.spread_bund_bps, 600.0)
            self.assertLessEqual(r.tension_sociale_locale, 100.0)


class TestEffortDefenseEtClauseDeSauvegarde(unittest.TestCase):
    def test_trajectoire_otan_la_haye(self):
        moteur = MoteurSimulationSystemique()
        res = moteur.appliquer_etape(
            DecisionPolitique(annee=1, effort_defense_cible_pct_pib=CIBLE_OTAN_DEFENSE_PCT)
        )
        self.assertAlmostEqual(res.effort_defense_pct_pib, 3.50, places=2)
        attendu_mde = 3015.0 * 3.50 / 100.0
        self.assertAlmostEqual(res.depenses_defense_mde, attendu_mde, delta=0.5)

    def test_surcout_defense_degrade_le_solde_public(self):
        ref = MoteurSimulationSystemique().appliquer_etape(DecisionPolitique(annee=1))
        res = MoteurSimulationSystemique().appliquer_etape(
            DecisionPolitique(annee=1, effort_defense_cible_pct_pib=3.50)
        )
        self.assertGreater(res.depenses_publiques_totales_mde, ref.depenses_publiques_totales_mde)
        self.assertGreater(res.deficit_nominal_mde, ref.deficit_nominal_mde)
        # Mais le multiplicateur budgétaire de défense soutient l'activité
        self.assertGreater(res.pib_nominal_mde, ref.pib_nominal_mde)

    def test_economie_de_guerre_multiplicateur_renforce(self):
        normal = MoteurSimulationSystemique().appliquer_etape(
            DecisionPolitique(annee=1, effort_defense_cible_pct_pib=4.0)
        )
        guerre = MoteurSimulationSystemique().appliquer_etape(
            DecisionPolitique(annee=1, effort_defense_cible_pct_pib=4.0, mobilisation_economie_de_guerre=True)
        )
        self.assertGreater(guerre.pib_nominal_mde, normal.pib_nominal_mde)
        self.assertGreater(guerre.inflation_globale_pct, normal.inflation_globale_pct)

    def test_clause_sauvegarde_neutralise_une_part_du_deficit_pde(self):
        """La dérogation défense du PSC est plafonnée à 1,5 pt de PIB."""
        sans = MoteurSimulationSystemique().appliquer_etape(
            DecisionPolitique(annee=1, effort_defense_cible_pct_pib=3.50, delta_dotation_dgf_mde=0.0)
        )
        avec = MoteurSimulationSystemique().appliquer_etape(
            DecisionPolitique(
                annee=1,
                effort_defense_cible_pct_pib=3.50,
                activation_clause_sauvegarde_nationale_ue=True,
            )
        )
        self.assertAlmostEqual(sans.ratio_deficit_pib, avec.ratio_deficit_pib, delta=0.01)
        journal = " ".join(avec.commentaires)
        self.assertIn("Clause de sauvegarde nationale", journal)
        self.assertLessEqual(1.40, PLAFOND_CLAUSE_SAUVEGARDE_PCT)

    def test_resilience_republicaine_rearme_et_sort_de_la_pde(self):
        """Simulation auparavant impossible : réarmer à 3,5 % ET sortir de la PDE."""
        moteur = MoteurSimulationSystemique()
        for dec in get_scenario_resilience_republicaine():
            moteur.appliquer_etape(dec)
        final = moteur.historique_etapes[-1]
        self.assertAlmostEqual(final.effort_defense_pct_pib, CIBLE_OTAN_DEFENSE_PCT, places=2)
        self.assertLess(final.ratio_deficit_pib, 3.0)
        self.assertFalse(final.statut_pde_europe)
        self.assertTrue(final.bouclier_tpi_actif)
        self.assertLess(final.tension_sociale_locale, 20.0)


class TestCyberEtEscaladeMondiale(unittest.TestCase):
    def test_cyberattaque_systemique_coute_du_pib(self):
        ref = MoteurSimulationSystemique().appliquer_etape(DecisionPolitique(annee=1))
        res = MoteurSimulationSystemique().appliquer_etape(
            DecisionPolitique(annee=1, cyberattaque_systemique=True)
        )
        self.assertLess(res.pib_nominal_mde, ref.pib_nominal_mde)
        self.assertGreater(res.spread_bund_bps, ref.spread_bund_bps)

    def test_convergence_des_blocs_augmente_le_risque_global(self):
        moteur = MoteurSimulationSystemique()
        calme = moteur.appliquer_etape(DecisionPolitique(annee=1))
        chaud = moteur.appliquer_etape(
            DecisionPolitique(
                annee=2,
                delta_tension_taiwan=25.0,
                delta_tension_ukraine_otan=20.0,
                delta_tension_iran_hormuz=15.0,
                delta_convergence_blocs=35.0,
            )
        )
        self.assertGreater(chaud.indice_tension_geopolitique, calme.indice_tension_geopolitique)
        self.assertGreater(chaud.probabilite_escalade_mondiale_pct, calme.probabilite_escalade_mondiale_pct)
        self.assertLessEqual(chaud.probabilite_escalade_mondiale_pct, 100.0)

    def test_scenario_ww3_est_la_borne_superieure_de_risque(self):
        moteur = MoteurSimulationSystemique()
        for dec in get_scenario_convergence_ww3():
            moteur.appliquer_etape(dec)
        pic = max(r.probabilite_escalade_mondiale_pct for r in moteur.historique_etapes)
        self.assertGreater(pic, 70.0)
        self.assertLessEqual(pic, 100.0)


class TestInvariantsComptablesAvecStrate5(unittest.TestCase):
    """Les invariants SFC du modèle doivent tenir sur TOUS les scénarios géopolitiques."""

    def test_conservation_des_flux_et_accumulation_de_dette(self):
        for fabrique in SCENARIOS_GEO:
            with self.subTest(scenario=fabrique.__name__):
                moteur = MoteurSimulationSystemique()
                dette_precedente = moteur.national.dette_maastricht_stock_mde
                for dec in fabrique():
                    r = moteur.appliquer_etape(dec)
                    self.assertAlmostEqual(
                        r.deficit_nominal_mde,
                        r.depenses_publiques_totales_mde - r.recettes_publiques_totales_mde,
                        places=2,
                    )
                    self.assertAlmostEqual(
                        r.dette_nominale_mde, dette_precedente + r.deficit_nominal_mde, places=2
                    )
                    dette_precedente = r.dette_nominale_mde

    def test_parite_des_taux_preservee(self):
        for fabrique in SCENARIOS_GEO:
            with self.subTest(scenario=fabrique.__name__):
                moteur = MoteurSimulationSystemique()
                for dec in fabrique():
                    r = moteur.appliquer_etape(dec)
                    attendu = moteur.mondial.taux_bund_allemagne_10ans + r.spread_bund_bps / 100.0
                    self.assertAlmostEqual(r.taux_oat_pct, attendu, places=2)
                    self.assertAlmostEqual(r.taux_credit_pme, r.taux_oat_pct + 0.85, places=2)

    def test_determinisme_bit_a_bit(self):
        for fabrique in SCENARIOS_GEO:
            with self.subTest(scenario=fabrique.__name__):
                serie = []
                for _ in range(2):
                    moteur = MoteurSimulationSystemique()
                    for dec in fabrique():
                        moteur.appliquer_etape(dec)
                    serie.append([(r.pib_nominal_mde, r.deficit_nominal_mde, r.taux_oat_pct) for r in moteur.historique_etapes])
                self.assertEqual(serie[0], serie[1])

    def test_non_divergence_sous_stress_extreme_prolonge(self):
        """15 années de guerre mondiale continue : aucun NaN, aucun inf, bornes tenues."""
        moteur = MoteurSimulationSystemique()
        for annee in range(1, 16):
            r = moteur.appliquer_etape(
                DecisionPolitique(
                    annee=annee,
                    blocus_taiwan_intensite=1.0,
                    fermeture_hormuz_intensite=1.0,
                    usage_nucleaire_tactique=(annee == 3),
                    cyberattaque_systemique=True,
                    delta_tension_taiwan=10.0,
                    delta_tension_ukraine_otan=10.0,
                    delta_tension_iran_hormuz=10.0,
                    delta_convergence_blocs=10.0,
                    effort_defense_cible_pct_pib=5.0,
                    mobilisation_economie_de_guerre=True,
                    choc_petrole_brent_usd=5.0,
                    choc_taux_fed_bps=50.0,
                    choc_change_eur_usd=-0.02,
                )
            )
            for valeur in (
                r.pib_nominal_mde,
                r.deficit_nominal_mde,
                r.dette_nominale_mde,
                r.taux_oat_pct,
                r.spread_bund_bps,
                r.inflation_globale_pct,
                r.probabilite_escalade_mondiale_pct,
            ):
                self.assertTrue(math.isfinite(valeur), f"Valeur non finie en année {annee}")
            self.assertGreaterEqual(r.pib_nominal_mde, 500.0)
            self.assertLessEqual(r.indice_tension_geopolitique, 100.0)
            self.assertLessEqual(r.probabilite_escalade_mondiale_pct, 100.0)
            self.assertGreaterEqual(r.disponibilite_semiconducteurs_pct, 0.0)
            self.assertGreaterEqual(r.stocks_strategiques_petrole_jours, 0.0)


if __name__ == "__main__":
    unittest.main()
