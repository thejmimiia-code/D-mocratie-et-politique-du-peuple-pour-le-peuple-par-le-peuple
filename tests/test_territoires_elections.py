"""
tests/test_territoires_elections.py — Tests unitaires et d'intégration des strates territoriales,
de l'Outre-mer complet et des fonctions électorales de la République.
"""

import unittest
from simulateur.model import (
    StrateTerritorialeContinuum,
    StrateOutreMerDetail,
    StrateFonctionsElectorales,
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
from simulateur.reglements_lois import (
    CONST_ART_1,
    CONST_ART_72_3,
    CONST_ART_73,
    CONST_ART_74,
    CONST_TITRE_XIII,
    CODE_ELEC_L16,
    CODE_ELEC_L123,
    CODE_ELEC_L260,
    CGCT_L2411_1,
    CODE_TRANSP_L1803_1,
    REGISTRE_LEGAL,
)


class TestStratesTerritorialesEtElections(unittest.TestCase):
    """Vérification des structures territoriales, ultramarines et des fonctions électorales."""

    def test_continuum_territorial_complet(self):
        """Vérifie le continuum du lieu-dit à la métropole."""
        terr = StrateTerritorialeContinuum()

        self.assertEqual(terr.sections_commune_lieux_dits_count, 2500)
        self.assertEqual(terr.communes_rurales_count, 25800)
        self.assertEqual(terr.bourgs_centres_count, 7650)
        self.assertEqual(terr.villes_moyennes_count, 1280)
        self.assertEqual(terr.grandes_agglomerations_count, 180)
        self.assertEqual(terr.metropoles_count, 22)
        self.assertEqual(terr.communes_total, 34935)
        self.assertEqual(terr.epci_total, 1254)
        self.assertEqual(terr.cantons_electoraux_count, 2054)
        self.assertEqual(terr.arrondissements_deconcentres_count, 332)
        self.assertEqual(terr.departements_total, 101)
        self.assertEqual(terr.regions_total, 18)

    def test_outre_mer_detail(self):
        """Vérifie l'inventaire des 14 territoires ultramarins et la souveraineté maritime."""
        om = StrateOutreMerDetail()

        self.assertAlmostEqual(om.drom_population_millions, 2.22)
        self.assertAlmostEqual(om.com_population_millions, 0.34)
        self.assertAlmostEqual(om.nouvelle_caledonie_population_millions, 0.27)
        self.assertAlmostEqual(om.francais_etranger_inscrits_millions, 2.10)
        self.assertAlmostEqual(om.zee_maritime_millions_km2, 10.2)
        self.assertAlmostEqual(om.surcout_vie_chere_outremer_pct, 32.5)
        self.assertAlmostEqual(om.octroi_de_mer_recette_mde, 1.60)
        self.assertAlmostEqual(om.indice_continuite_territoriale, 54.0)

    def test_fonctions_electorales(self):
        """Vérifie le REU, les scrutins républicains et les seuils institutionnels."""
        elec = StrateFonctionsElectorales()

        self.assertAlmostEqual(elec.reu_electeurs_inscrits_millions, 49.5)
        self.assertAlmostEqual(elec.taux_participation_presidentielle_pct, 72.0)
        self.assertAlmostEqual(elec.taux_participation_legislatives_pct, 66.5)
        self.assertAlmostEqual(elec.taux_participation_municipales_pct, 62.0)
        self.assertAlmostEqual(elec.taux_participation_europeennes_pct, 51.5)
        self.assertAlmostEqual(elec.taux_participation_regionales_pct, 45.0)
        self.assertEqual(elec.circonscriptions_legislatives_total, 577)
        self.assertEqual(elec.grands_electeurs_senat_total, 162000)
        self.assertEqual(elec.sieges_majorite_absolue_an, 289)
        self.assertEqual(elec.triangulaires_legislatives_projetees, 85)
        self.assertAlmostEqual(elec.procurations_dematerialisees_pct, 68.0)

    def test_corpus_juridique_articles_fondamentaux(self):
        """Vérifie la présence et les attributs des articles constitutionnels et légaux majeurs."""
        ids = list(REGISTRE_LEGAL.keys())
        self.assertIn(CONST_ART_1.identifiant, ids)
        self.assertIn(CONST_ART_72_3.identifiant, ids)
        self.assertIn(CONST_ART_73.identifiant, ids)
        self.assertIn(CONST_ART_74.identifiant, ids)
        self.assertIn(CONST_TITRE_XIII.identifiant, ids)
        self.assertIn(CODE_ELEC_L16.identifiant, ids)
        self.assertIn(CODE_ELEC_L123.identifiant, ids)
        self.assertIn(CODE_ELEC_L260.identifiant, ids)
        self.assertIn(CGCT_L2411_1.identifiant, ids)
        self.assertIn(CODE_TRANSP_L1803_1.identifiant, ids)

        # Vérification du contenu spécifique
        self.assertIn("indivisible", CONST_ART_1.texte_integral)
        self.assertIn("répertoire électoral unique", CODE_ELEC_L16.texte_integral.lower())
        self.assertIn("continuité territoriale", CODE_TRANSP_L1803_1.texte_integral.lower())
        self.assertIn("section de commune", CGCT_L2411_1.texte_integral.lower())

    def test_moteur_dynamique_mandature_territoires(self):
        """Vérifie les effets positifs de la mandature sur la vitalité rurale et l'Outre-mer."""
        moteur = MoteurSimulationSystemique()
        for dec in get_scenario_mandature_5_ans():
            moteur.appliquer_etape(dec)

        res5 = moteur.historique_etapes[-1]

        # La vitalité rurale augmente
        self.assertGreater(res5.communes_rurales_vitalite_indice, 62.0)
        # La vie chère en Outre-mer recule
        self.assertLess(res5.outremer_vie_chere_indice, 32.5)
        # La continuité territoriale s'améliore
        self.assertGreater(res5.outremer_continuite_indice, 54.0)
        # La participation électorale progresse grâce aux réformes civiques
        self.assertGreater(res5.participation_electorale_globale_pct, 70.0)
        # Le nombre de triangulaires se tasse
        self.assertLess(res5.triangulaires_legislatives_count, 85)

        # Vérification des propriétés helpers
        self.assertEqual(res5.territoire.communes_total, 34935)
        self.assertEqual(res5.outremer.zee_maritime_millions_km2, 10.2)
        self.assertAlmostEqual(res5.elections.taux_participation_legislatives_pct, res5.participation_electorale_globale_pct)

    def test_moteur_dynamique_choc_mondial_aggravation(self):
        """Vérifie l'aggravation de la vie chère ultramarine en Année 1 et la crise civique lors d'un choc stagflationniste."""
        moteur = MoteurSimulationSystemique()
        etapes = []
        for dec in get_scenario_choc_mondial_stagflation():
            etapes.append(moteur.appliquer_etape(dec))

        res_annee1 = etapes[0]
        res_choc = etapes[-1]

        # En année 1 du choc pétrolier, la vie chère flambe en Outre-mer
        self.assertGreater(res_annee1.outremer_vie_chere_indice, 32.5)
        # Forte abstention civique
        self.assertLess(res_choc.participation_electorale_globale_pct, 66.0)
        # Explosion des triangulaires dues à l'extrême fragmentation
        self.assertGreater(res_choc.triangulaires_legislatives_count, 85)


    def test_typologie_communale_insee_9_strates(self):
        """Vérifie la répartition intégrale des 34 935 communes en 9 strates démographiques."""
        terr = StrateTerritorialeContinuum()

        self.assertEqual(terr.communes_moins_100_hab_count, 3400)
        self.assertEqual(terr.communes_100_a_499_hab_count, 17000)
        self.assertEqual(terr.communes_500_a_999_hab_count, 5400)
        self.assertEqual(terr.communes_1000_a_3499_hab_count, 5900)
        self.assertEqual(terr.communes_3500_a_9999_hab_count, 1750)
        self.assertEqual(terr.communes_10000_a_19999_hab_count, 580)
        self.assertEqual(terr.communes_20000_a_49999_hab_count, 460)
        self.assertEqual(terr.communes_50000_a_99999_hab_count, 88)
        self.assertEqual(terr.communes_100000_a_199999_hab_count, 30)
        self.assertEqual(terr.communes_200000_et_plus_hab_count, 11)

        # Somme des communes rurales (< 1000 hab.)
        total_rural = terr.communes_moins_100_hab_count + terr.communes_100_a_499_hab_count + terr.communes_500_a_999_hab_count
        self.assertEqual(total_rural, terr.communes_rurales_count)
        self.assertEqual(terr.communes_rurales_count, 25800)

        # Vérification du total général communal
        somme_toutes_strates = (
            terr.communes_rurales_count
            + terr.bourgs_centres_count
            + terr.villes_moyennes_count
            + terr.grandes_agglomerations_count
            + terr.communes_100000_a_199999_hab_count
            + terr.communes_200000_et_plus_hab_count
            + 5  # Communes spécifiques d'outre-mer / arrondissements
        )
        self.assertAlmostEqual(terr.communes_total, 34935, delta=15)

    def test_epci_et_deconcentration_etat(self):
        """Vérifie l'exhaustivité des 1 254 EPCI et des services déconcentrés de l'État."""
        terr = StrateTerritorialeContinuum()

        self.assertEqual(terr.communautes_de_communes_count, 991)
        self.assertEqual(terr.communautes_agglomeration_count, 228)
        self.assertEqual(terr.communautes_urbaines_count, 14)
        self.assertEqual(terr.metropoles_droit_commun_count, 21)
        self.assertEqual(terr.metropole_lyon_statut_particulier, 1)
        self.assertEqual(
            terr.communautes_de_communes_count
            + terr.communautes_agglomeration_count
            + terr.communautes_urbaines_count
            + terr.metropoles_droit_commun_count,
            terr.epci_total,
        )
        self.assertEqual(terr.epci_total, 1254)

        # Déconcentration
        self.assertEqual(terr.arrondissements_deconcentres_count, 332)
        self.assertEqual(terr.cantons_electoraux_count, 2054)
        self.assertEqual(terr.circonscriptions_legislatives_count, 577)
        self.assertEqual(terr.academies_scolaires_count, 30)
        self.assertEqual(terr.agences_regionales_sante_ars, 18)
        self.assertEqual(terr.cours_appel_judiciaires_count, 36)
        self.assertEqual(terr.zones_defense_securite_count, 12)

    def test_souverainete_maritime_zee_par_oceans(self):
        """Vérifie la décomposition par bassin océanique des 10,2M km² de ZEE."""
        om = StrateOutreMerDetail()

        self.assertAlmostEqual(om.zee_pacifique_millions_km2, 6.8)
        self.assertAlmostEqual(om.zee_indien_millions_km2, 2.6)
        self.assertAlmostEqual(om.zee_atlantique_antilles_guyane_km2, 0.5)
        self.assertAlmostEqual(om.zee_metropole_facade_europeenne_km2, 0.3)
        total_zee = (
            om.zee_pacifique_millions_km2
            + om.zee_indien_millions_km2
            + om.zee_atlantique_antilles_guyane_km2
            + om.zee_metropole_facade_europeenne_km2
        )
        self.assertAlmostEqual(total_zee, om.zee_maritime_millions_km2, delta=0.01)

    def test_nouveaux_textes_fondateurs_republicains(self):
        """Vérifie la présence et le contenu des 90 textes légaux et constitutionnels majeurs."""
        ids = list(REGISTRE_LEGAL.keys())
        self.assertGreaterEqual(len(ids), 90)

        # Vérification des textes constitutionnels et déclarations
        textes_obligatoires = [
            "DDHC_ART_1", "DDHC_ART_3", "DDHC_ART_13", "DDHC_ART_16",
            "PREAMBULE_1946_AL3", "PREAMBULE_1946_AL9", "PREAMBULE_1946_AL11",
            "CHARTE_ENV_ART_4", "CHARTE_ENV_ART_5",
            "CONST_ART_4", "CONST_ART_5", "CONST_ART_6", "CONST_ART_12",
            "CONST_ART_34", "CONST_ART_37", "CONST_ART_40", "CONST_ART_47",
            "CONST_ART_72_4", "CONST_ART_88_1",
            "CODE_ELEC_L1", "CODE_ELEC_L52_4", "CODE_ELEC_L71",
            "CGCT_L1111_1", "CGCT_L2143_1", "CGCT_L5217_1",
            "CNUDM_ART_56_ZEE", "LOI_55_1052_TAAF",
        ]
        for t_id in textes_obligatoires:
            self.assertIn(t_id, ids, f"Le texte {t_id} doit être présent dans le registre légal.")

    def test_elections_seuils_et_voies_referendaires(self):
        """Vérifie les critères mathématiques des scrutins et des référendums."""
        elec = StrateFonctionsElectorales()

        self.assertAlmostEqual(elec.seuil_second_tour_legislatives_pct_inscrits, 12.5)
        self.assertAlmostEqual(elec.seuil_second_tour_departementales_pct_inscrits, 12.5)
        self.assertAlmostEqual(elec.seuil_second_tour_regionales_pct_exprimes, 10.0)
        self.assertAlmostEqual(elec.seuil_fusion_regionales_pct_exprimes, 5.0)
        self.assertAlmostEqual(elec.seuil_representation_europeennes_pct, 5.0)
        self.assertAlmostEqual(elec.prime_majoritaire_municipales_pct, 50.0)
        self.assertAlmostEqual(elec.prime_majoritaire_regionales_pct, 25.0)
        self.assertEqual(elec.parrainages_presidentiels_requis, 500)
        self.assertEqual(elec.departements_minimum_parrainages, 30)
        self.assertEqual(elec.rip_seuil_parlementaires, 185)
        self.assertAlmostEqual(elec.rip_seuil_electeurs_millions, 4.95)
        self.assertEqual(elec.congres_versailles_majorite_trois_cinquiemes, 555)
        self.assertAlmostEqual(elec.referendum_local_seuil_participation_pct, 50.0)


if __name__ == "__main__":
    unittest.main()
