"""
tests/test_assemblees.py — Tests exhaustifs des assemblées représentatives et décisionnelles :
1. Assemblée nationale (577 députés, voix de censure, seuil 289, 49.3).
2. Sénat (348 sénateurs, veto constitutionnel art. 89, défense des maires, CMP).
3. Congrès de Versailles (925 parlementaires, seuil 3/5èmes, voie art. 11).
4. Conseils Municipaux & AMF (34 935 communes, fronde fiscale, règle d'or).
5. Conseils Départementaux & ADF (101 départements, effet de ciseau social, faillites).
6. Conseils Régionaux & Régions de France (18 régions, CPER, TER/lycées).
7. Assemblées Consulaires (CCI, CMA, Chambres d'Agriculture, commande publique 30% PME).
8. CESE et Conventions Citoyennes tirées au sort (consensus social et délibératif).
9. Parlement Européen & Conseil UE (720 eurodéputés, majorité qualifiée, PDE).
"""

import unittest
from simulateur.model import DecisionPolitique
from simulateur.moteur import MoteurSimulationSystemique
from simulateur.scenarios import (
    get_scenario_mandature_5_ans,
    get_scenario_austerite_brutale,
    get_scenario_statut_quo,
    get_scenario_choc_mondial_stagflation,
)


class TestAssembleesParlementaires(unittest.TestCase):
    """Vérifie le fonctionnement décisionnel de l'Assemblée nationale, du Sénat et du Congrès."""

    def test_assemblee_nationale_stabilite_mandature(self):
        """Sous le Plan de Mandature, la censure recule et la majorité se consolide."""
        moteur = MoteurSimulationSystemique()
        for dec in get_scenario_mandature_5_ans():
            res = moteur.appliquer_etape(dec)

        res_final = moteur.historique_etapes[-1]
        self.assertFalse(res_final.gouvernement_censure)
        self.assertLess(res_final.voix_censure_an, 260)
        self.assertIn("Majorité consolidée", res_final.climat_assemblee_nationale)

    def test_assemblee_nationale_censure_sous_austerite_brutale(self):
        """Une austérité brutale fait flamber la grogne civique et provoque la censure (voix >= 289)."""
        moteur = MoteurSimulationSystemique()
        for dec in get_scenario_austerite_brutale():
            res = moteur.appliquer_etape(dec)

        # En fin d'austérité brutale, la tension dépasse 90/100 -> le gouvernement est censuré
        res_final = moteur.historique_etapes[-1]
        self.assertTrue(res_final.gouvernement_censure)
        self.assertGreaterEqual(res_final.voix_censure_an, 289)
        self.assertIn("GOUVERNEMENT CENSURÉ", res_final.climat_assemblee_nationale)

    def test_senat_veto_article_89_en_cas_attaque_dgf(self):
        """Si l'État coupe massivement la DGF, le Sénat active son veto constitutionnel sur l'article 89."""
        moteur = MoteurSimulationSystemique()
        # Coupe de 10 Md€ de DGF sans concertation
        dec = DecisionPolitique(annee=1, delta_dotation_dgf_mde=-10.0)
        res = moteur.appliquer_etape(dec)

        self.assertGreater(res.hostilite_senat_indice, 55.0)
        self.assertTrue(res.senat_veto_art_89)
        self.assertFalse(res.congres_majorite_3_5)
        # Vérification du message d'alerte constitutionnelle
        self.assertTrue(any("VETO CONSTITUTIONNEL" in c for c in res.commentaires))

    def test_senat_apaisement_sous_mandature(self):
        """Sous le plan de mandature, l'hostilité du Sénat s'effondre et les CMP fonctionnent."""
        moteur = MoteurSimulationSystemique()
        for dec in get_scenario_mandature_5_ans():
            moteur.appliquer_etape(dec)

        res_final = moteur.historique_etapes[-1]
        self.assertFalse(res_final.senat_veto_art_89)
        self.assertLess(res_final.hostilite_senat_indice, 25.0)
        self.assertGreater(moteur.national.senat.taux_accord_cmp_pct, 65.0)

    def test_congres_versailles_seuil_trois_cinquiemes(self):
        """Vérifie la règle mathématique des 3/5èmes (555 voix sur 925) au Congrès de Versailles."""
        moteur = MoteurSimulationSystemique()
        for dec in get_scenario_mandature_5_ans():
            moteur.appliquer_etape(dec)

        res_final = moteur.historique_etapes[-1]
        # En Année 5 avec haute confiance civique et Sénat apaisé, le Congrès dépasse 555 voix
        self.assertTrue(res_final.congres_majorite_3_5)
        self.assertGreaterEqual(moteur.national.congres.voix_favorables_projetees, 555)


class TestAssembleesTerritorialesEtConsulaires(unittest.TestCase):
    """Vérifie le fonctionnement des conseils municipaux, départementaux, régionaux et consulaires."""

    def test_conseil_departemental_effet_ciseau_financier(self):
        """Vérifie l'explosion des départements en faillite technique en cas de crise et de coupe DGF."""
        moteur = MoteurSimulationSystemique()
        # Choc d'austérité avec coupes DGF
        dec = DecisionPolitique(annee=1, delta_dotation_dgf_mde=-12.0)
        res = moteur.appliquer_etape(dec)

        self.assertGreater(res.departements_alerte_ciseau, 25)
        self.assertGreater(moteur.local.conseil_departemental.indice_effet_ciseau_social, 70.0)

    def test_conseil_municipal_fronde_amf(self):
        """La fronde des maires s'enflamme si la DGF baisse et s'éteint si le pouvoir d'achat est restauré."""
        moteur_choc = MoteurSimulationSystemique()
        res_choc = moteur_choc.appliquer_etape(DecisionPolitique(annee=1, delta_dotation_dgf_mde=-8.0))

        moteur_calme = MoteurSimulationSystemique()
        res_calme = moteur_calme.appliquer_etape(DecisionPolitique(annee=1, baisse_tva_energie_5_5_mde=9.0))

        self.assertGreater(res_choc.fronde_maires_indice, res_calme.fronde_maires_indice + 20.0)

    def test_assemblees_consulaires_allotissement_commande_publique(self):
        """L'allotissement réservant 30% aux PME fait bondir la confiance des patrons (CCI) et artisans (CMA)."""
        moteur = MoteurSimulationSystemique()
        conf_initiale = moteur.local.assemblees_consulaires.cci_confiance_patrons_pct

        dec = DecisionPolitique(annee=1, commande_publique_massifiee_mde=6.0)
        res = moteur.appliquer_etape(dec)

        self.assertGreater(res.consulaire_confiance_pme, conf_initiale + 10.0)
        self.assertGreater(moteur.local.assemblees_consulaires.cma_adhesion_artisans_pct, 70.0)


class TestAssembleesEuropeennesEtCitoyennes(unittest.TestCase):
    """Vérifie le Parlement Européen, le Conseil UE, le CESE et les Conventions Citoyennes."""

    def test_parlement_europeen_alignement(self):
        """Le taux d'alignement au Parlement Européen est favorisé par la conformité budgétaire."""
        moteur = MoteurSimulationSystemique()
        for dec in get_scenario_mandature_5_ans():
            moteur.appliquer_etape(dec)

        res_final = moteur.historique_etapes[-1]
        self.assertGreaterEqual(res_final.pe_taux_alignement, 70.0)
        self.assertFalse(moteur.europe.conseil_ue.decision_pde_sanction_active)

    def test_convention_citoyenne_consensus_ric(self):
        """L'instauration du RIC et du Casier B2 fait bondir l'indice délibératif de la convention citoyenne."""
        moteur = MoteurSimulationSystemique()
        dec = DecisionPolitique(annee=1, reforme_ric_souverain=True, reforme_casier_b2=True)
        res = moteur.appliquer_etape(dec)

        self.assertGreaterEqual(res.convention_citoyenne_consensus, 85.0)
        self.assertGreaterEqual(res.cese_consensus_social, 44.0)


if __name__ == "__main__":
    unittest.main()
