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


if __name__ == "__main__":
    unittest.main()
