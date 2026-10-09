#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests pour le module d'enrichissement historique.
"""

import unittest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from simulateur.enrichissement_historique import (
    GINI_FRANCE,
    PAUVRETE_FRANCE,
    DETTE_PIB_FRANCE,
    SOLDE_BUDGETAIRE_FRANCE,
    DEMOGRAPHIE_FRANCE,
    FECONDITE_FRANCE,
    ESPERANCE_VIE_FRANCE,
    THINK_TANKS_ENRICHIS,
    obtenir_gini,
    obtenir_pauvrete,
    obtenir_dette_pib,
    obtenir_solde_budgetaire,
    obtenir_demographie,
    obtenir_fecondite,
    obtenir_esperance_vie,
    obtenir_think_tanks_enrichis,
    generer_synthese_enrichissement,
    exporter_json_enrichissement,
)


class TestEnrichissementStructure(unittest.TestCase):
    """Tests de structure des séries historiques."""

    def test_gini_non_vide(self):
        self.assertGreater(len(GINI_FRANCE), 20)

    def test_pauvrete_non_vide(self):
        self.assertGreater(len(PAUVRETE_FRANCE), 20)

    def test_dette_non_vide(self):
        self.assertGreater(len(DETTE_PIB_FRANCE), 30)

    def test_solde_non_vide(self):
        self.assertGreater(len(SOLDE_BUDGETAIRE_FRANCE), 20)

    def test_demographie_non_vide(self):
        self.assertGreater(len(DEMOGRAPHIE_FRANCE), 5)

    def test_fecondite_non_vide(self):
        self.assertGreater(len(FECONDITE_FRANCE), 10)

    def test_esperance_vie_non_vide(self):
        self.assertGreater(len(ESPERANCE_VIE_FRANCE), 5)

    def test_think_tanks_enrichis_non_vide(self):
        self.assertGreater(len(THINK_TANKS_ENRICHIS), 5)


class TestGini(unittest.TestCase):
    """Tests de cohérence de l'indice de Gini."""

    def test_gini_valeurs_entre_0_et_1(self):
        for g in GINI_FRANCE:
            self.assertGreaterEqual(g["gini"], 0.0)
            self.assertLessEqual(g["gini"], 1.0)

    def test_gini_minimum_2006(self):
        gini_2006 = next(g for g in GINI_FRANCE if g["annee"] == 2006)
        self.assertAlmostEqual(gini_2006["gini"], 0.297, places=3)

    def test_gini_maximum_1970(self):
        gini_1970 = next(g for g in GINI_FRANCE if g["annee"] == 1970)
        self.assertAlmostEqual(gini_1970["gini"], 0.371, places=3)

    def test_gini_dernier_2023(self):
        gini_2023 = next(g for g in GINI_FRANCE if g["annee"] == 2023)
        self.assertAlmostEqual(gini_2023["gini"], 0.318, places=3)

    def test_gini_croissant_annees(self):
        annees = [g["annee"] for g in GINI_FRANCE]
        self.assertEqual(annees, sorted(annees))

    def test_gini_chaque_point_a_source(self):
        for g in GINI_FRANCE:
            self.assertIn("source", g)
            self.assertGreater(len(g["source"]), 0)


class TestPauvrete(unittest.TestCase):
    """Tests de cohérence du taux de pauvreté."""

    def test_pauvrete_valeurs_positives(self):
        for p in PAUVRETE_FRANCE:
            self.assertGreater(p["taux_pct"], 0)
            self.assertLess(p["taux_pct"], 30)

    def test_pauvrete_minimum_2004(self):
        p_2004 = next(p for p in PAUVRETE_FRANCE if p["annee"] == 2004)
        self.assertAlmostEqual(p_2004["taux_pct"], 12.4, places=1)

    def test_pauvrete_dernier_2024(self):
        p_2024 = next(p for p in PAUVRETE_FRANCE if p["annee"] == 2024)
        self.assertAlmostEqual(p_2024["taux_pct"], 15.4, places=1)

    def test_pauvrete_croissant_annees(self):
        annees = [p["annee"] for p in PAUVRETE_FRANCE]
        self.assertEqual(annees, sorted(annees))

    def test_pauvrete_2024_plus_haut_mesure(self):
        max_pauvrete = max(p["taux_pct"] for p in PAUVRETE_FRANCE if p["annee"] >= 1996)
        p_2024 = next(p for p in PAUVRETE_FRANCE if p["annee"] == 2024)
        self.assertGreaterEqual(p_2024["taux_pct"], max_pauvrete)


class TestDette(unittest.TestCase):
    """Tests de cohérence de la dette/PIB."""

    def test_dette_valeurs_positives(self):
        for d in DETTE_PIB_FRANCE:
            self.assertGreater(d["dette_pct_pib"], 0)

    def test_dette_minimum_1980(self):
        d_1980 = next(d for d in DETTE_PIB_FRANCE if d["annee"] == 1980)
        self.assertAlmostEqual(d_1980["dette_pct_pib"], 21.3, places=1)

    def test_dette_covid_2020(self):
        d_2020 = next(d for d in DETTE_PIB_FRANCE if d["annee"] == 2020)
        self.assertGreater(d_2020["dette_pct_pib"], 110)

    def test_dette_dernier_2025(self):
        d_2025 = next(d for d in DETTE_PIB_FRANCE if d["annee"] == 2025)
        self.assertAlmostEqual(d_2025["dette_pct_pib"], 115.6, places=1)

    def test_dette_croissant_annees(self):
        annees = [d["annee"] for d in DETTE_PIB_FRANCE]
        self.assertEqual(annees, sorted(annees))

    def test_dette_depassee_maastricht_1996(self):
        d_1996 = next(d for d in DETTE_PIB_FRANCE if d["annee"] == 1996)
        self.assertGreater(d_1996["dette_pct_pib"], 60.0)


class TestSoldeBudgetaire(unittest.TestCase):
    """Tests de cohérence du solde budgétaire."""

    def test_solde_negatif_la_plupart(self):
        negatifs = sum(1 for s in SOLDE_BUDGETAIRE_FRANCE if s["solde_pct_pib"] < 0)
        self.assertGreater(negatifs, len(SOLDE_BUDGETAIRE_FRANCE) * 0.7)

    def test_solde_covid_2020_record(self):
        s_2020 = next(s for s in SOLDE_BUDGETAIRE_FRANCE if s["annee"] == 2020)
        self.assertLess(s_2020["solde_pct_pib"], -8.0)

    def test_solde_2024(self):
        s_2024 = next(s for s in SOLDE_BUDGETAIRE_FRANCE if s["annee"] == 2024)
        self.assertAlmostEqual(s_2024["solde_pct_pib"], -5.8, places=1)

    def test_solde_croissant_annees(self):
        annees = [s["annee"] for s in SOLDE_BUDGETAIRE_FRANCE]
        self.assertEqual(annees, sorted(annees))


class TestDemographie(unittest.TestCase):
    """Tests de cohérence démographique."""

    def test_population_croissante(self):
        populations = [d["population_milliers"] for d in DEMOGRAPHIE_FRANCE]
        for i in range(1, len(populations)):
            self.assertGreater(populations[i], populations[i-1])

    def test_population_2025(self):
        pop_2025 = next(d for d in DEMOGRAPHIE_FRANCE if d["annee"] == 2025)
        self.assertGreater(pop_2025["population_milliers"], 68000)


class TestFecondite(unittest.TestCase):
    """Tests de cohérence de la fécondité."""

    def test_fecondite_valeurs_raisonnables(self):
        for f in FECONDITE_FRANCE:
            self.assertGreater(f["icf"], 0.5)
            self.assertLess(f["icf"], 5.0)

    def test_fecondite_baby_boom(self):
        f_1946 = next(f for f in FECONDITE_FRANCE if f["annee"] == 1946)
        self.assertGreater(f_1946["icf"], 2.5)

    def test_fecondite_record_bas_2024(self):
        f_2024 = next(f for f in FECONDITE_FRANCE if f["annee"] == 2024)
        self.assertAlmostEqual(f_2024["icf"], 1.62, places=2)

    def test_fecondite_record_haut_2010(self):
        f_2010 = next(f for f in FECONDITE_FRANCE if f["annee"] == 2010)
        self.assertGreaterEqual(f_2010["icf"], 2.0)


class TestEsperanceVie(unittest.TestCase):
    """Tests de cohérence de l'espérance de vie."""

    def test_femmes_plus_longue_que_hommes(self):
        for e in ESPERANCE_VIE_FRANCE:
            self.assertGreater(e["femmes"], e["hommes"])

    def test_esperance_vie_croissante(self):
        ev_1994 = next(e for e in ESPERANCE_VIE_FRANCE if e["annee"] == 1994)
        ev_2024 = next(e for e in ESPERANCE_VIE_FRANCE if e["annee"] == 2024)
        self.assertGreater(ev_2024["femmes"], ev_1994["femmes"])
        self.assertGreater(ev_2024["hommes"], ev_1994["hommes"])

    def test_covid_impact_2020(self):
        ev_2019 = next(e for e in ESPERANCE_VIE_FRANCE if e["annee"] == 2019)
        ev_2020 = next(e for e in ESPERANCE_VIE_FRANCE if e["annee"] == 2020)
        self.assertLess(ev_2020["hommes"], ev_2019["hommes"])


class TestThinkTanksEnrichis(unittest.TestCase):
    """Tests des think tanks enrichis."""

    def test_chaque_tt_a_nom(self):
        for tt in THINK_TANKS_ENRICHIS:
            self.assertIn("nom", tt)
            self.assertGreater(len(tt["nom"]), 0)

    def test_chaque_tt_a_url(self):
        for tt in THINK_TANKS_ENRICHIS:
            self.assertIn("url_rapport", tt)
            self.assertTrue(tt["url_rapport"].startswith("http"))

    def test_chaque_tt_a_donnees_cles(self):
        for tt in THINK_TANKS_ENRICHIS:
            self.assertIn("donnees_cles", tt)
            self.assertGreater(len(tt["donnees_cles"]), 0)

    def test_chaque_tt_a_pourquoi(self):
        for tt in THINK_TANKS_ENRICHIS:
            self.assertIn("pourquoi_integration", tt)
            self.assertGreater(len(tt["pourquoi_integration"]), 0)

    def test_igf_present(self):
        noms = [tt["nom"] for tt in THINK_TANKS_ENRICHIS]
        self.assertTrue(any("IGF" in n for n in noms))

    def test_hcfp_present(self):
        noms = [tt["nom"] for tt in THINK_TANKS_ENRICHIS]
        self.assertTrue(any("HCFP" in n for n in noms))

    def test_ofce_present(self):
        noms = [tt["nom"] for tt in THINK_TANKS_ENRICHIS]
        self.assertTrue(any("OFCE" in n for n in noms))


class TestFonctionsAcces(unittest.TestCase):
    """Tests des fonctions d'accès."""

    def test_obtenir_gini_filtre(self):
        result = obtenir_gini(2000, 2010)
        self.assertGreater(len(result), 0)
        for g in result:
            self.assertGreaterEqual(g["annee"], 2000)
            self.assertLessEqual(g["annee"], 2010)

    def test_obtenir_pauvrete_filtre(self):
        result = obtenir_pauvrete(2010, 2020)
        self.assertGreater(len(result), 0)

    def test_obtenir_dette_filtre(self):
        result = obtenir_dette_pib(2000, 2010)
        self.assertGreater(len(result), 0)

    def test_obtenir_solde_filtre(self):
        result = obtenir_solde_budgetaire(2000, 2010)
        self.assertGreater(len(result), 0)

    def test_obtenir_demographie(self):
        result = obtenir_demographie()
        self.assertEqual(len(result), len(DEMOGRAPHIE_FRANCE))

    def test_obtenir_fecondite(self):
        result = obtenir_fecondite()
        self.assertEqual(len(result), len(FECONDITE_FRANCE))

    def test_obtenir_esperance_vie(self):
        result = obtenir_esperance_vie()
        self.assertEqual(len(result), len(ESPERANCE_VIE_FRANCE))

    def test_obtenir_think_tanks_enrichis(self):
        result = obtenir_think_tanks_enrichis()
        self.assertEqual(len(result), len(THINK_TANKS_ENRICHIS))


class TestSyntheseEtExport(unittest.TestCase):
    """Tests de synthèse et export."""

    def test_synthese_non_vide(self):
        synthese = generer_synthese_enrichissement()
        self.assertGreater(len(synthese), 100)
        self.assertIn("Gini", synthese)
        self.assertIn("pauvreté", synthese)
        self.assertIn("Dette", synthese)

    def test_export_json_valide(self):
        json_str = exporter_json_enrichissement()
        data = json.loads(json_str)
        self.assertIn("gini_france", data)
        self.assertIn("pauvrete_france", data)
        self.assertIn("dette_pib_france", data)
        self.assertIn("metadata", data)

    def test_export_json_metadata(self):
        json_str = exporter_json_enrichissement()
        data = json.loads(json_str)
        self.assertGreater(data["metadata"]["nb_points_total"], 100)
        self.assertGreater(data["metadata"]["nb_think_tanks"], 5)


if __name__ == "__main__":
    unittest.main()