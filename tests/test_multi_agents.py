#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests pour le module de simulation multi-agents."""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from simulateur.modele_multi_agents import (
    TypeAgent,
    StrategieConsommation,
    StrategieInvestissement,
    AgentMenage,
    AgentEntreprise,
    AgentCollectivite,
    EnvironnementMarche,
    ModeleMultiAgents,
    creer_modele_demo,
    executer_simulation,
)


class TestAgentMenage(unittest.TestCase):
    """Tests de l'agent ménage."""

    def test_creation(self):
        m = AgentMenage(id=0, revenu=25000, patrimoine=100000, decile=5, csp=4)
        self.assertEqual(m.id, 0)
        self.assertEqual(m.revenu, 25000)
        self.assertEqual(m.decile, 5)

    def test_consommation_keynesienne(self):
        m = AgentMenage(id=0, revenu=25000, patrimoine=100000, decile=5, csp=4,
                        strategie=StrategieConsommation.KEYNESIENNE)
        conso = m.calculer_consommation(inflation=0.02)
        # PMC = 0.75
        self.assertAlmostEqual(conso, 25000 * 0.75 * 1.02, delta=10)

    def test_consommation_ricardienne(self):
        m = AgentMenage(id=0, revenu=25000, patrimoine=100000, decile=5, csp=4,
                        strategie=StrategieConsommation.RICARDIENNE)
        conso = m.calculer_consommation(inflation=0.02)
        # PMC = 0.60
        self.assertAlmostEqual(conso, 25000 * 0.60 * 1.02, delta=10)

    def test_impot_revenu(self):
        m = AgentMenage(id=0, revenu=30000, patrimoine=100000, decile=6, csp=4)
        impot = m.calculer_impot_revenu()
        # 11294 à 0% + (28797-11294) à 11% + (30000-28797) à 30%
        attendu = 17503 * 0.11 + 1203 * 0.30
        self.assertAlmostEqual(impot, attendu, delta=10)

    def test_impot_revenu_faible(self):
        m = AgentMenage(id=0, revenu=10000, patrimoine=0, decile=1, csp=8)
        impot = m.calculer_impot_revenu()
        self.assertEqual(impot, 0.0)

    def test_mise_a_jour(self):
        m = AgentMenage(id=0, revenu=25000, patrimoine=100000, decile=5, csp=4)
        m.mettre_a_jour(27000)
        self.assertEqual(m.revenu, 27000)
        self.assertEqual(len(m.historique_revenu), 1)
        self.assertEqual(m.historique_revenu[0], 25000)


class TestAgentEntreprise(unittest.TestCase):
    """Tests de l'agent entreprise."""

    def test_creation(self):
        e = AgentEntreprise(id=0, ca_annuel=1500000, effectifs=10, investissement=300000)
        self.assertEqual(e.ca_annuel, 1500000)
        self.assertEqual(e.effectifs, 10)

    def test_impot_societes(self):
        e = AgentEntreprise(id=0, ca_annuel=1000000, effectifs=10, investissement=200000)
        is_impot = e.payer_impot_societes(taux=0.25)
        # Bénéfice = 8% du CA = 80 000
        self.assertAlmostEqual(is_impot, 80000 * 0.25, delta=10)

    def test_investissement_accelerateur(self):
        e = AgentEntreprise(id=0, ca_annuel=1000000, effectifs=10, investissement=200000,
                           strategie=StrategieInvestissement.ACCELERATEUR)
        inv = e.decider_investissement(demande=1.1, taux_interet=0.03)
        # alpha = 0.25, demande * CA = 0.25 * 1.1 * 1000000 = 275000
        self.assertGreater(inv, 0)

    def test_investissement_sensible_taux(self):
        e = AgentEntreprise(id=0, ca_annuel=1000000, effectifs=10, investissement=200000,
                           strategie=StrategieInvestissement.ACCELERATEUR)
        inv_bas = e.decider_investissement(demande=1.1, taux_interet=0.03)
        inv_haut = e.decider_investissement(demande=1.1, taux_interet=0.08)
        # Taux élevé devrait réduire l'investissement
        self.assertLessEqual(inv_haut, inv_bas)


class TestAgentCollectivite(unittest.TestCase):
    """Tests de l'agent collectivité."""

    def test_creation(self):
        c = AgentCollectivite(id=0, type_collectivite="commune",
                             population=5000, dotation_etat=500000,
                             taxe_fonciere=300000, investissement=200000)
        self.assertEqual(c.population, 5000)

    def test_regle_or(self):
        c = AgentCollectivite(id=0, type_collectivite="commune",
                             population=5000, dotation_etat=500000,
                             taxe_fonciere=300000, investissement=200000)
        # Baisse de DGF de 100 000€
        variation_tf = c.appliquer_regle_or(-100000)
        # TF augmente de 94% de la baisse
        self.assertAlmostEqual(variation_tf, 94000, delta=1)
        self.assertAlmostEqual(c.dotation_etat, 400000, delta=1)
        self.assertAlmostEqual(c.taxe_fonciere, 394000, delta=1)

    def test_poids_politique(self):
        c = AgentCollectivite(id=0, type_collectivite="commune",
                             population=50000, dotation_etat=5000000,
                             taxe_fonciere=3000000, investissement=2000000)
        poids = c.calculer_poids_politique()
        self.assertGreater(poids, 0)
        self.assertLessEqual(poids, 1)


class TestEnvironnementMarche(unittest.TestCase):
    """Tests de l'environnement de marché."""

    def test_creation(self):
        env = EnvironnementMarche()
        self.assertAlmostEqual(env.taux_directeur, 0.0375, places=4)
        self.assertAlmostEqual(env.inflation, 0.02, places=2)

    def test_taux_credit(self):
        env = EnvironnementMarche()
        taux = env.calculer_taux_credit(risque=0.01)
        # taux = 0.0375 + 0.0088 + 0.01 = 0.0563
        self.assertAlmostEqual(taux, 0.0563, places=4)

    def test_choc_petrole(self):
        env = EnvironnementMarche()
        impact = env.simuler_choc("petrole", 0.5)
        self.assertIn("inflation_supplementaire", impact)
        self.assertIn("pib_impact", impact)
        self.assertAlmostEqual(env.prix_petrole, 80 * 1.5, delta=1)

    def test_choc_taux(self):
        env = EnvironnementMarche()
        impact = env.simuler_choc("taux", 0.01)
        self.assertIn("credit_impact", impact)
        self.assertAlmostEqual(env.taux_directeur, 0.0475, places=4)


class TestModeleMultiAgents(unittest.TestCase):
    """Tests du modèle multi-agents."""

    def test_creation(self):
        modele = ModeleMultiAgents(nb_menages=50, nb_entreprises=5)
        self.assertEqual(len(modele.menages), 50)
        self.assertEqual(len(modele.entreprises), 5)

    def test_simulation_periode(self):
        modele = ModeleMultiAgents(nb_menages=50, nb_entreprises=5)
        resultats = modele.simuler_periode(2024)
        self.assertIn("consommation_totale", resultats)
        self.assertIn("investissement_total", resultats)
        self.assertIn("annee", resultats)
        self.assertEqual(resultats["annee"], 2024)

    def test_simulation_multiples(self):
        modele = ModeleMultiAgents(nb_menages=50, nb_entreprises=5)
        historique = modele.simuler_multiples_periodes(nb_annees=3, annee_debut=2024)
        self.assertEqual(len(historique), 3)
        self.assertEqual(historique[0]["annee"], 2024)
        self.assertEqual(historique[2]["annee"], 2026)

    def test_gini_valide(self):
        modele = ModeleMultiAgents(nb_menages=50, nb_entreprises=5)
        gini = modele.calculer_gini()
        self.assertGreaterEqual(gini, 0.0)
        self.assertLessEqual(gini, 1.0)

    def test_gini_comparaison_historique(self):
        """Le Gini simulé devrait être proche du Gini INSEE (0.29-0.32)."""
        modele = ModeleMultiAgents(nb_menages=100, nb_entreprises=10)
        gini = modele.calculer_gini()
        # Gini INSEE 2023 : 0.318
        self.assertGreater(gini, 0.2)
        self.assertLess(gini, 0.5)

    def test_export_json(self):
        modele = ModeleMultiAgents(nb_menages=20, nb_entreprises=3)
        modele.simuler_periode(2024)
        json_str = modele.exporter_resultats()
        import json
        data = json.loads(json_str)
        self.assertIn("modele", data)
        self.assertIn("historique", data)


class TestFonctionsAcces(unittest.TestCase):
    """Tests des fonctions d'accès."""

    def test_creer_modele_demo(self):
        modele = creer_modele_demo(nb_menages=50, nb_entreprises=5)
        self.assertIsInstance(modele, ModeleMultiAgents)

    def test_executer_simulation(self):
        resultats = executer_simulation(nb_annees=3, nb_menages=50)
        self.assertIn("historique", resultats)
        self.assertIn("gini_initial", resultats)
        self.assertIn("gini_final", resultats)
        self.assertEqual(len(resultats["historique"]), 3)


if __name__ == "__main__":
    unittest.main()