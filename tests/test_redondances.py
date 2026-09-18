"""
tests/test_redondances.py — Banc de test exhaustif de toutes les redondances systémiques :
1. Redondances comptables (conservation stricte des flux budgétaires, dette, déficit, règle d'or).
2. Redondances des marchés financiers et de l'échelon mondial (Bund, Spread, OAT, Fed, Brent, Forex).
3. Redondances institutionnelles et réglementaires européennes (PDE, TPI, seuils Maastricht).
4. Redondances politiques et civiques (censure parlementaire, tension territoriale, confiance).
5. Redondances du corpus juridique (ancrage légal de chaque levier).
6. Redondances de stabilité numérique et non-divergence sous stress-tests extrêmes.
"""

import unittest
import math
from simulateur.model import (
    EchelonLocal,
    EchelonNational,
    EchelonEuropeen,
    EchelonMondial,
    DecisionPolitique,
    ResultatEtapeSimulation,
)
from simulateur.moteur import MoteurSimulationSystemique
from simulateur.scenarios import (
    get_scenario_mandature_5_ans,
    get_scenario_statut_quo,
    get_scenario_austerite_brutale,
    get_scenario_choc_mondial_stagflation,
)
from simulateur.reglements_lois import get_corpus_lois, rechercher_loi


class TestRedondancesComptables(unittest.TestCase):
    """Vérifie la conservation stricte des identités comptables et de la dette publique."""

    def test_conservation_flux_et_deficit_tous_scenarios(self):
        """Pour tous les scénarios et toutes les années : Déficit = Dépenses - Recettes."""
        scenarios = [
            ("mandature", get_scenario_mandature_5_ans()),
            ("statut_quo", get_scenario_statut_quo()),
            ("austerite", get_scenario_austerite_brutale()),
            ("choc_mondial", get_scenario_choc_mondial_stagflation()),
        ]

        for nom, decisions in scenarios:
            moteur = MoteurSimulationSystemique()
            dette_precedente = moteur.national.dette_maastricht_stock_mde

            for step_idx, dec in enumerate(decisions, start=1):
                res = moteur.appliquer_etape(dec)

                # 1. Redondance Déficit nominal = Dépenses - Recettes
                deficit_theorique = round(res.depenses_publiques_totales_mde - res.recettes_publiques_totales_mde, 2)
                self.assertAlmostEqual(
                    res.deficit_nominal_mde,
                    deficit_theorique,
                    places=2,
                    msg=f"[{nom} An {step_idx}] Rupture identité comptable dépenses/recettes",
                )

                # 2. Redondance Ratio déficit / PIB
                ratio_theorique = round((res.deficit_nominal_mde / res.pib_nominal_mde) * 100.0, 2)
                self.assertAlmostEqual(
                    res.ratio_deficit_pib,
                    ratio_theorique,
                    places=2,
                    msg=f"[{nom} An {step_idx}] Incohérence ratio déficit/PIB",
                )

                # 3. Redondance Accumulation Dette = Dette_{t-1} + Déficit_{t}
                dette_theorique = round(dette_precedente + res.deficit_nominal_mde, 2)
                self.assertAlmostEqual(
                    res.dette_nominale_mde,
                    dette_theorique,
                    places=2,
                    msg=f"[{nom} An {step_idx}] Dérive d'accumulation de dette",
                )
                dette_precedente = res.dette_nominale_mde

                # 4. Redondance Ratio dette / PIB
                ratio_dette_calc = round((res.dette_nominale_mde / res.pib_nominal_mde) * 100.0, 2)
                self.assertAlmostEqual(
                    res.ratio_dette_pib,
                    ratio_dette_calc,
                    places=2,
                    msg=f"[{nom} An {step_idx}] Incohérence ratio dette/PIB",
                )

    def test_regle_dor_locale_cgct(self):
        """Vérifie la transmission arithmétique de la contrainte budgétaire locale (art. L. 1612-4 CGCT)."""
        moteur = MoteurSimulationSystemique()
        taxe_fonciere_initiale = moteur.local.bloc_communal.taxe_fonciere_tfpb_mde

        # Baisse DGF de 5 Md€ imposée par l'État
        baisse_dgf = 5.0
        dec = DecisionPolitique(annee=1, delta_dotation_dgf_mde=-baisse_dgf)
        res = moteur.appliquer_etape(dec)

        # Les communes doivent compenser à 94% par la taxe foncière
        hausse_attendue = baisse_dgf * 0.94
        taxe_fonciere_observee = res.produit_taxe_fonciere_mde
        self.assertAlmostEqual(
            taxe_fonciere_observee - taxe_fonciere_initiale,
            hausse_attendue,
            places=2,
            msg="La règle d'or d'équilibre budgétaire local n'a pas été respectée",
        )


class TestRedondancesMarchesEtMonde(unittest.TestCase):
    """Vérifie la transmission des variables mondiales et des marchés de capitaux."""

    def test_coherence_oat_bund_spread(self):
        """Vérifie l'égalité financière : Taux OAT = Taux Bund + Spread (en %)."""
        moteur = MoteurSimulationSystemique()
        dec = DecisionPolitique(annee=1)
        res = moteur.appliquer_etape(dec)

        oat_calcule = round(moteur.mondial.taux_bund_allemagne_10ans + (res.spread_bund_bps / 100.0), 2)
        self.assertAlmostEqual(
            res.taux_oat_pct,
            oat_calcule,
            places=2,
            msg="Incohérence entre taux OAT, Bund allemand et spread souverain",
        )

    def test_credit_pme_et_transmission_reelle(self):
        """Le taux de crédit aux PME doit rigoureusement répercuter le coût souverain OAT (+0.85 pt)."""
        moteur = MoteurSimulationSystemique()
        res = moteur.appliquer_etape(DecisionPolitique(annee=1))
        self.assertAlmostEqual(
            res.taux_credit_pme,
            round(res.taux_oat_pct + 0.85, 2),
            places=2,
            msg="Défaut de transmission du canal de crédit PME",
        )

    def test_choc_petrolier_mondial_et_inflation(self):
        """Une hausse du baril de pétrole mondial de 30 $ doit alourdir la facture et alimenter l'inflation."""
        moteur_neutre = MoteurSimulationSystemique()
        res_neutre = moteur_neutre.appliquer_etape(DecisionPolitique(annee=1))

        moteur_choc = MoteurSimulationSystemique()
        choc_brent = 30.0
        res_choc = moteur_choc.appliquer_etape(DecisionPolitique(annee=1, choc_petrole_brent_usd=choc_brent))

        # Vérification du cours
        self.assertEqual(res_choc.cours_petrole_usd, 82.5 + choc_brent)
        # La facture énergétique doit augmenter d'au moins 10 Md€
        self.assertGreater(res_choc.facture_energetique_mde, res_neutre.facture_energetique_mde + 10.0)
        # L'inflation doit bondir
        self.assertGreater(res_choc.inflation_globale_pct, res_neutre.inflation_globale_pct)
        # Le pouvoir d'achat des ménages doit baisser
        self.assertLess(res_choc.pouvoir_achat_index, res_neutre.pouvoir_achat_index)

    def test_choc_fed_et_hausse_taux_mondiaux(self):
        """Un resserrement des taux directeurs de la Fed doit pousser le taux Bund et l'OAT vers le haut."""
        moteur_neutre = MoteurSimulationSystemique()
        res_neutre = moteur_neutre.appliquer_etape(DecisionPolitique(annee=1))

        moteur_fed = MoteurSimulationSystemique()
        res_fed = moteur_fed.appliquer_etape(DecisionPolitique(annee=1, choc_taux_fed_bps=100.0))

        self.assertGreater(res_fed.taux_oat_pct, res_neutre.taux_oat_pct)

    def test_degradation_notation_sur_spread_eleve(self):
        """Si la dérive budgétaire pousse le spread au-delà de 105 bps, la note bascule en A+."""
        moteur = MoteurSimulationSystemique()
        # Simulation d'immobilisme sur plusieurs années avec dérive
        for annee in range(1, 4):
            res = moteur.appliquer_etape(DecisionPolitique(annee=annee))

        # En année 3 sans réformes, le spread monte à 88 + 24 = 112 bps > 105 bps
        self.assertGreater(res.spread_bund_bps, 105.0)
        self.assertEqual(res.note_souveraine, "A+")


class TestRedondancesInstitutionnellesEtUE(unittest.TestCase):
    """Vérifie le respect des règles du Pacte de Stabilité européen et des institutions."""

    def test_invariant_pde_et_bouclier_tpi(self):
        """Déficit > 3% sans effort structurel suffisant déclenche le signal d'alarme PDE et suspend le TPI."""
        moteur = MoteurSimulationSystemique()
        # Scénario sans effort
        res = moteur.appliquer_etape(DecisionPolitique(annee=1))
        self.assertTrue(res.statut_pde_europe)
        self.assertFalse(res.bouclier_tpi_actif)

    def test_sortie_pde_sous_3_pourcent(self):
        """Déficit <= 3% réactive immédiatement le bouclier TPI et lève la PDE."""
        moteur = MoteurSimulationSystemique()
        # Effort massif ramenant le déficit sous 3%
        dec = DecisionPolitique(
            annee=1,
            recettes_fraude_ia_mde=20.0,
            taxe_superprofits_rachats_mde=15.0,
            extension_ttf_mde=10.0,
            fusion_doublons_territoriaux_mde=15.0,
            commande_publique_massifiee_mde=15.0,
        )
        res = moteur.appliquer_etape(dec)
        self.assertLessEqual(res.ratio_deficit_pib, 3.00)
        self.assertFalse(res.statut_pde_europe)
        self.assertTrue(res.bouclier_tpi_actif)

    def test_invariant_censure_et_tension_sociale(self):
        """Une tension sociale locale supérieure à 65/100 fait basculer le risque de censure au-dessus de 50%."""
        moteur = MoteurSimulationSystemique()
        # Choc d'austérité brutale sur les collectivités qui fait flamber la taxe foncière
        dec = DecisionPolitique(annee=1, delta_dotation_dgf_mde=-25.0)
        res = moteur.appliquer_etape(dec)
        self.assertGreater(res.tension_sociale_locale, 65.0)
        self.assertGreater(res.risque_censure_parlement, 50.0)


class TestRedondancesCorpusJuridique(unittest.TestCase):
    """Vérifie l'ancrage juridique complet et sans orphelin de tous les paramètres du simulateur."""

    def test_couverture_des_quatre_strates_dans_le_registre(self):
        """Le registre légal doit couvrir obligatoirement les 4 strates."""
        corpus = get_corpus_lois()
        strates_presentes = set(art.strate_impactee for art in corpus.values())
        self.assertIn("Local", strates_presentes)
        self.assertIn("National", strates_presentes)
        self.assertIn("Européen", strates_presentes)
        self.assertIn("Mondial", strates_presentes)

    def test_textes_fondateurs_presents(self):
        """Vérifie la présence nominative des articles fondamentaux."""
        corpus = get_corpus_lois()
        cles_requises = [
            "CONST_ART_2",             # Principe républicain
            "CONST_ART_24",            # Parlement et Sénat
            "CONST_ART_47_2",          # Cour des comptes
            "CONST_ART_49_2",          # Motion de censure
            "CONST_ART_61_1",          # Question Prioritaire de Constitutionnalité
            "CONST_ART_71_1",          # Défenseur des droits
            "DDHC_ART_14",             # Consentement à l'impôt
            "CHARTE_ENV_ART_1",        # Droit à un environnement sain
            "CRPA_L123_1",             # Droit à l'erreur (Loi ESSOC)
            "CP_432_10",               # Concussion
            "CP_131_26_2",             # Inéligibilité probité
            "CGCT_L1612_4",            # Règle d'or budgétaire locale
            "TFUE_ART_126",            # Procédure de déficit excessif
            "DIR_TVA_2022_542",        # Taux de TVA réduit sur l'énergie
            "OCDE_PILIER_2_CGI_223_VJ",# Impôt minimum mondial 15%
            "REG_UE_2023_956_MACF",    # Mécanisme carbone aux frontières
            "BALE_III_REG_575_2013",   # Ratio de risque bancaire et dette souveraine
            "CCOM_L710_1",             # Chambres de Commerce et d'Industrie (CCI)
            "CART_L711_1",             # Chambres de Métiers et de l'Artisanat (CMA)
            "CRURAL_L510_1",           # Chambres d'Agriculture (CA)
            "CONST_ART_39",            # Initiative des lois et avis Conseil d'État
            "CONST_ART_45",            # Navette, CMP et dernier mot AN
            "CONST_ART_48",            # Ordre du jour et niches parlementaires
            "CONST_ART_51_2",          # Commissions d'enquête parlementaires
            "CONST_ART_70",            # CESE consultation
            "CONST_ART_71",            # CESE saisine citoyenne
            "CONST_ART_72",            # Libre administration des collectivités
            "CONST_ART_72_1",          # Référendum local décisionnel
            "CONST_ART_72_2",          # Autonomie financière locale
            "CONST_ART_89",            # Congrès de Versailles et révision
            "CGCT_L2121_1",            # Conseil municipal
            "CGCT_L3121_1",            # Conseil départemental
            "CGCT_L4131_1",            # Conseil régional
            "CGCT_L5211_1",            # Conseil communautaire EPCI
            "TUE_ART_14",              # Parlement Européen
            "TUE_ART_16",              # Conseil de l'Union Européenne
        ]
        for cle in cles_requises:
            self.assertIn(cle, corpus, msg=f"Article ou directive manquante : {cle}")

    def test_chambres_consulaires_et_institutions_modele(self):
        """Vérifie la présence et le bon calibrage des chambres consulaires et institutions de la République."""
        moteur = MoteurSimulationSystemique()
        # Échelon Local : Chambres consulaires
        self.assertEqual(moteur.local.chambres_consulaires.ressortissants_entreprises_milliers, 6900.0)
        self.assertGreater(moteur.local.chambres_consulaires.taux_survie_pme_locales_pct, 60.0)
        # Échelon National : Institutions de la République
        self.assertEqual(moteur.national.institutions.conseil_constitutionnel_conformite_pct, 100.0)
        self.assertGreater(moteur.national.institutions.cour_des_comptes_evaluation_efficience, 70.0)


class TestRedondancesStabiliteNumeriqueEtStress(unittest.TestCase):
    """Stress tests numériques : vérifie la stabilité asymptotique, l'absence de NaN et l'idempotence."""

    def test_stress_test_extreme_non_divergence(self):
        """Soumet le simulateur à 10 années consécutives de chocs violents sans explosion numérique."""
        moteur = MoteurSimulationSystemique()
        for i in range(1, 11):
            dec = DecisionPolitique(
                annee=i,
                choc_petrole_brent_usd=40.0,
                choc_change_eur_usd=-0.12,
                choc_taux_fed_bps=150.0,
                delta_dotation_dgf_mde=-5.0,
                recettes_pilier2_ocde_mde=4.0,
                recettes_macf_carbone_mde=2.5,
                baisse_tva_energie_5_5_mde=9.0,
            )
            res = moteur.appliquer_etape(dec)

            # Aucune valeur ne doit être NaN ou infinie
            for attr in [
                "pib_nominal_mde",
                "deficit_nominal_mde",
                "ratio_deficit_pib",
                "dette_nominale_mde",
                "ratio_dette_pib",
                "charge_dette_mde",
                "taux_oat_pct",
                "spread_bund_bps",
                "facture_energetique_mde",
                "inflation_globale_pct",
                "tension_sociale_locale",
            ]:
                val = getattr(res, attr)
                self.assertFalse(math.isnan(val), f"Valeur NaN détectée pour {attr} à l'année {i}")
                self.assertFalse(math.isinf(val), f"Valeur infinie détectée pour {attr} à l'année {i}")

            # Bornes logiques
            self.assertGreater(res.pib_nominal_mde, 2000.0)
            self.assertGreater(res.dette_nominale_mde, 0.0)
            self.assertGreater(res.taux_oat_pct, 0.0)

    def test_idempotence_et_determinisme(self):
        """Deux moteurs initialisés à l'identique et recevant les mêmes décisions doivent donner le même résultat."""
        moteur1 = MoteurSimulationSystemique()
        moteur2 = MoteurSimulationSystemique()

        scen = get_scenario_mandature_5_ans()
        for dec in scen:
            r1 = moteur1.appliquer_etape(dec)
            r2 = moteur2.appliquer_etape(dec)
            self.assertEqual(r1.deficit_nominal_mde, r2.deficit_nominal_mde)
            self.assertEqual(r1.dette_nominale_mde, r2.dette_nominale_mde)
            self.assertEqual(r1.taux_oat_pct, r2.taux_oat_pct)
            self.assertEqual(r1.tension_sociale_locale, r2.tension_sociale_locale)
            self.assertEqual(r1.facture_energetique_mde, r2.facture_energetique_mde)


if __name__ == "__main__":
    unittest.main()
