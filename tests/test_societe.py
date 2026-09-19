#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests pour le module sociétal des 18 domaines (1792→2026).
Vérifie la structure, les séries, les comparaisons et les endpoints HTTP.
"""

import json
import unittest
import urllib.request

from simulateur.societe_domaines import (
    DomaineSocietal,
    IndicateurHistorique,
    DOMAINES_SOCIETAUX,
    obtenir_tous_domaines,
    obtenir_domaine_par_id,
    lister_domaines_ids,
    comparer_domaines,
    obtenir_serie_domaine,
    generer_synthese_societale,
    exporter_json_domaines,
)


class TestStructureDomaines(unittest.TestCase):
    """Vérifie la cohérence structurelle des 18 domaines."""

    def test_18_domaines_definis(self):
        self.assertEqual(len(DOMAINES_SOCIETAUX), 18)

    def test_ids_uniques(self):
        ids = [d.id for d in DOMAINES_SOCIETAUX]
        self.assertEqual(len(ids), len(set(ids)), "IDs de domaines non uniques")

    def test_chaque_domaine_a_icon(self):
        for d in DOMAINES_SOCIETAUX:
            self.assertGreater(len(d.icon), 0, f"{d.id} sans icône")

    def test_chaque_domaine_a_indicateurs(self):
        for d in DOMAINES_SOCIETAUX:
            self.assertGreater(len(d.indicateurs_cles), 0, f"{d.id} sans indicateurs")

    def test_chaque_domaine_a_serie(self):
        for d in DOMAINES_SOCIETAUX:
            self.assertGreater(len(d.serie_historique), 0, f"{d.id} sans série historique")

    def test_chaque_domaine_a_sources(self):
        for d in DOMAINES_SOCIETAUX:
            self.assertGreater(len(d.sources_principales), 0, f"{d.id} sans sources")

    def test_chaque_domaine_a_pertinence(self):
        for d in DOMAINES_SOCIETAUX:
            self.assertGreater(len(d.pertinence_pour_simulateur), 0, f"{d.id} sans pertinence")


class TestFonctionsAcces(unittest.TestCase):
    """Vérifie les fonctions d'accès."""

    def test_obtenir_tous_domaines(self):
        tous = obtenir_tous_domaines()
        self.assertEqual(len(tous), 18)

    def test_obtenir_domaine_par_id(self):
        d = obtenir_domaine_par_id("sante")
        self.assertIsNotNone(d)
        self.assertEqual(d["nom"], "Santé & Protection sanitaire")

    def test_domaine_inexistant(self):
        d = obtenir_domaine_par_id("inexistant")
        self.assertIsNone(d)

    def test_lister_ids(self):
        ids = lister_domaines_ids()
        self.assertEqual(len(ids), 18)
        self.assertIn("education", ids)
        self.assertIn("sante", ids)
        self.assertIn("defense", ids)
        self.assertIn("energie", ids)
        self.assertIn("culture", ids)


class TestSeriesHistoriques(unittest.TestCase):
    """Vérifie les séries historiques des domaines."""

    def test_obtenir_serie_sante(self):
        serie = obtenir_serie_domaine("sante")
        self.assertGreater(len(serie), 5)
        self.assertIn("annee", serie[0])
        self.assertIn("valeur", serie[0])

    def test_obtenir_serie_inexistante(self):
        serie = obtenir_serie_domaine("inexistant")
        self.assertEqual(len(serie), 0)

    def test_serie_education_couvre_1792(self):
        serie = obtenir_serie_domaine("education")
        annees = [s["annee"] for s in serie]
        self.assertLessEqual(min(annees), 1800)

    def test_serie_sante_couvre_mortalite_infantile(self):
        serie = obtenir_serie_domaine("sante")
        unites = [s["unite"] for s in serie]
        self.assertIn("‰", unites)


class TestComparaisonsDomaines(unittest.TestCase):
    """Vérifie les comparaisons inter-domaines."""

    def test_comparer_education_et_sante(self):
        comp = comparer_domaines("education", "sante")
        self.assertEqual(comp["domaine_a"], "Éducation & Formation")
        self.assertEqual(comp["domaine_b"], "Santé & Protection sanitaire")
        self.assertGreater(comp["nb_indicateurs_a"], 0)

    def test_comparer_inexistant(self):
        with self.assertRaises(ValueError):
            comparer_domaines("inexistant", "sante")


class TestSyntheseExport(unittest.TestCase):
    """Vérifie la synthèse et l'export."""

    def test_synthese_non_vide(self):
        syn = generer_synthese_societale()
        self.assertGreater(len(syn), 500)
        self.assertIn("ÉDUCATION", syn)
        self.assertIn("SANTÉ", syn)
        self.assertIn("DÉFENSE", syn)
        self.assertIn("CULTURE", syn)

    def test_export_json_valide(self):
        json_str = exporter_json_domaines()
        data = json.loads(json_str)
        self.assertIn("domaines", data)
        self.assertIn("metadata", data)
        self.assertEqual(data["metadata"]["nb_domaines"], 18)


class TestDomainesSpecifiques(unittest.TestCase):
    """Vérifie des domaines spécifiques en détail."""

    def test_education_alphabetisation(self):
        edu = obtenir_domaine_par_id("education")
        serie = [s for s in edu["serie_historique"] if s["annee"] == 1882]
        self.assertGreater(len(serie), 0)

    def test_sante_mortalite_infantile(self):
        san = obtenir_domaine_par_id("sante")
        serie_1830 = [s for s in san["serie_historique"] if s["annee"] == 1830]
        self.assertGreater(len(serie_1830), 0)
        self.assertEqual(serie_1830[0]["valeur"], 182)  # 182‰

    def test_defense_1914_pic(self):
        defense = obtenir_domaine_par_id("defense")
        serie_1914 = [s for s in defense["serie_historique"] if s["annee"] == 1914]
        self.assertGreater(len(serie_1914), 0)
        self.assertEqual(serie_1914[0]["valeur"], 43.0)  # 43% PIB

    def test_travail_smic_2026(self):
        travail = obtenir_domaine_par_id("travail")
        serie_2026 = [s for s in travail["serie_historique"] if s["annee"] == 2026]
        self.assertGreater(len(serie_2026), 0)

    def test_environnement_co2_pic_1973(self):
        env = obtenir_domaine_par_id("environnement")
        serie_1973 = [s for s in env["serie_historique"] if s["annee"] == 1973]
        self.assertGreater(len(serie_1973), 0)
        self.assertEqual(serie_1973[0]["valeur"], 8.4)


class TestHttpSociete(unittest.TestCase):
    """Tests d'intégration des endpoints HTTP."""

    BASE = "http://127.0.0.1:8000"

    def _get_json(self, path: str):
        try:
            req = urllib.request.Request(self.BASE + path)
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            return None

    def test_api_societe(self):
        data = self._get_json("/api/societe")
        if data is None:
            self.skipTest("Serveur non disponible")
        self.assertEqual(data["total"], 18)

    def test_api_societe_detail(self):
        data = self._get_json("/api/societe?id=sante")
        if data is None:
            self.skipTest("Serveur non disponible")
        self.assertEqual(data["nom"], "Santé & Protection sanitaire")

    def test_api_societe_serie(self):
        data = self._get_json("/api/societe/serie/education")
        if data is None:
            self.skipTest("Serveur non disponible")
        self.assertGreater(data["points"], 0)

    def test_api_societe_synthese(self):
        data = self._get_json("/api/societe/synthese")
        if data is None:
            self.skipTest("Serveur non disponible")
        self.assertIn("synthese", data)


if __name__ == "__main__":
    unittest.main()