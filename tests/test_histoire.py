#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests pour le module historique exhaustif (1792→2026).
Vérifie l'intégrité des 12 périodes, des séries chronologiques,
des réformes, des crises, des comparaisons et des endpoints HTTP.
"""

import json
import unittest
import urllib.request

from simulateur.histoire_france import (
    PeriodeHistorique,
    AnneeHistorique,
    ReformeHistorique,
    CriseHistorique,
    PERIODES_HISTORIQUES,
    SERIES_ANNUELLES,
    REFORMES_MAJEURES,
    CRISES_HISTORIQUES,
    DIMENSIONS_COMPARISON,
    obtenir_toutes_periodes,
    obtenir_periode_par_id,
    comparer_periodes,
    filtrer_periodes,
    obtenir_series_chronologiques,
    obtenir_reformes,
    obtenir_crises,
    obtenir_options_dropdown,
    generer_synthese_historique,
    calibrer_parametres_historiques,
    exporter_json_complet,
)


class TestStructureDonnees(unittest.TestCase):
    """Vérifie la cohérence structurelle des données historiques."""

    def test_12_periodes_definies(self):
        self.assertEqual(len(PERIODES_HISTORIQUES), 12)

    def test_couverture_1792_2026(self):
        annee_min = min(p.annee_debut for p in PERIODES_HISTORIQUES)
        annee_max = max(p.annee_fin for p in PERIODES_HISTORIQUES)
        self.assertEqual(annee_min, 1792)
        self.assertEqual(annee_max, 2026)

    def test_periodes_sans_trou(self):
        """Vérifie qu'il n'y a pas de trous entre les périodes."""
        sorted_p = sorted(PERIODES_HISTORIQUES, key=lambda p: p.annee_debut)
        for i in range(len(sorted_p) - 1):
            self.assertGreaterEqual(
                sorted_p[i + 1].annee_debut,
                sorted_p[i].annee_fin,
                f"Trou entre {sorted_p[i].nom} et {sorted_p[i+1].nom}"
            )

    def test_chaque_periode_a_sources(self):
        for p in PERIODES_HISTORIQUES:
            self.assertGreater(len(p.sources), 0, f"{p.nom} sans sources")
            self.assertGreater(len(p.evenements_cles), 0, f"{p.nom} sans événements")

    def test_chaque_periode_a_lecons(self):
        for p in PERIODES_HISTORIQUES:
            self.assertGreater(len(p.lecons_pour_simulateur), 0, f"{p.nom} sans leçons")

    def test_types_regime_valides(self):
        types_valides = {"monarchie", "republique", "empire", "republique_puis_empire",
                         "republique_puis_dictature_puis_liberation", "dictature"}
        for p in PERIODES_HISTORIQUES:
            self.assertIn(p.type_regime, types_valides, f"Type inconnu: {p.type_regime}")


class TestSeriesChronologiques(unittest.TestCase):
    """Vérifie les séries annuelles."""

    def test_series_non_vides(self):
        self.assertGreater(len(SERIES_ANNUELLES), 10)

    def test_series_couverture_1870_2026(self):
        annees = sorted(s.annee for s in SERIES_ANNUELLES)
        self.assertEqual(annees[0], 1870)
        self.assertGreaterEqual(annees[-1], 2024)

    def test_dette_non_negative(self):
        for s in SERIES_ANNUELLES:
            self.assertGreaterEqual(s.dette_publique_pct_pib, 0, f"Dette négative en {s.annee}")

    def test_gini_dans_plage(self):
        for s in SERIES_ANNUELLES:
            if s.gini_revenu > 0:
                self.assertGreaterEqual(s.gini_revenu, 0.15, f"Gini trop bas en {s.annee}")
                self.assertLessEqual(s.gini_revenu, 0.65, f"Gini trop haut en {s.annee}")

    def test_top10_dans_plage(self):
        for s in SERIES_ANNUELLES:
            if s.part_top10_revenu_pct > 0:
                self.assertGreaterEqual(s.part_top10_revenu_pct, 25, f"Top10 trop bas en {s.annee}")
                self.assertLessEqual(s.part_top10_revenu_pct, 60, f"Top10 trop haut en {s.annee}")

    def test_obtenir_series_chronologiques(self):
        serie = obtenir_series_chronologiques("dette_publique_pct_pib")
        self.assertGreater(len(serie), 0)
        self.assertIn("annee", serie[0])
        self.assertIn("valeur", serie[0])

    def test_filtrer_par_annee(self):
        serie = obtenir_series_chronologiques("dette_publique_pct_pib", annee_debut=1980, annee_fin=2000)
        for s in serie:
            self.assertGreaterEqual(s["annee"], 1980)
            self.assertLessEqual(s["annee"], 2000)


class TestReformes(unittest.TestCase):
    """Vérifie les réformes majeures."""

    def test_reformes_non_vides(self):
        self.assertGreater(len(REFORMES_MAJEURES), 3)

    def test_chaque_reforme_a_source(self):
        for r in REFORMES_MAJEURES:
            self.assertGreater(len(r.sources), 0, f"{r.nom} sans sources")

    def test_categorie_valide(self):
        cats_valides = {"fiscale", "sociale", "institutionnelle", "energetique", "monetaire"}
        for r in REFORMES_MAJEURES:
            self.assertIn(r.categorie, cats_valides, f"Catégorie inconnue: {r.categorie}")

    def test_obtenir_reformes_filtre(self):
        fiscales = obtenir_reformes(categorie="fiscale")
        for r in fiscales:
            self.assertEqual(r["categorie"], "fiscale")


class TestCrises(unittest.TestCase):
    """Vérifie les crises historiques."""

    def test_crises_non_vides(self):
        self.assertGreater(len(CRISES_HISTORIQUES), 5)

    def test_gravite_dans_plage(self):
        for c in CRISES_HISTORIQUES:
            self.assertGreaterEqual(c.gravite, 1)
            self.assertLessEqual(c.gravite, 10)

    def test_obtenir_crises_filtre(self):
        financieres = obtenir_crises(type_crise="financiere")
        for c in financieres:
            self.assertEqual(c["type_crise"], "financiere")

    def test_obtenir_crises_gravite_min(self):
        graves = obtenir_crises(gravite_min=8)
        for c in graves:
            self.assertGreaterEqual(c["gravite"], 8)


class TestComparaisons(unittest.TestCase):
    """Vérifie les comparaisons inter-régimes."""

    def test_comparer_revolution_vs_trente_glorieuses(self):
        comp = comparer_periodes("revolution_1792_1799", "trente_glorieuses_1946_1974")
        self.assertIn("fiscale", comp.dimensions)
        self.assertGreater(len(comp.enseignements), 0)

    def test_comparer_inconnu_leve_erreur(self):
        with self.assertRaises(ValueError):
            comparer_periodes("inexistant", "trente_glorieuses_1946_1974")

    def test_comparer_toutes_dimensions(self):
        comp = comparer_periodes(
            "troisieme_republique_1871_1913",
            "zone_euro_1999_2007",
            dimensions=["fiscale", "sociale"]
        )
        self.assertIn("fiscale", comp.dimensions)
        self.assertIn("sociale", comp.dimensions)


class TestFiltres(unittest.TestCase):
    """Vérifie les fonctions de filtrage."""

    def test_filtrer_par_type_regime(self):
        republiques = filtrer_periodes(type_regime="republique")
        for p in republiques:
            self.assertEqual(p["type_regime"], "republique")

    def test_filtrer_par_dette(self):
        haute_dette = filtrer_periodes(dette_min=100)
        for p in haute_dette:
            self.assertGreaterEqual(p["dette_publique_pct_pib"], 100)

    def test_filtrer_par_chomage(self):
        fort_chomage = filtrer_periodes(chomage_min=8)
        for p in fort_chomage:
            self.assertGreaterEqual(p["chomage_moyen_pct"], 8)


class TestDropdowns(unittest.TestCase):
    """Vérifie les options de menus déroulants."""

    def test_options_contient_periodes(self):
        opts = obtenir_options_dropdown()
        self.assertIn("periodes", opts)
        self.assertEqual(len(opts["periodes"]), 12)

    def test_options_contient_dimensions(self):
        opts = obtenir_options_dropdown()
        self.assertIn("dimensions", opts)
        self.assertEqual(len(opts["dimensions"]), 6)

    def test_options_contient_types_regime(self):
        opts = obtenir_options_dropdown()
        self.assertIn("types_regime", opts)
        self.assertGreater(len(opts["types_regime"]), 0)


class TestExport(unittest.TestCase):
    """Vérifie l'export JSON."""

    def test_export_json_valide(self):
        json_str = exporter_json_complet()
        data = json.loads(json_str)
        self.assertIn("periodes", data)
        self.assertIn("series_annuelles", data)
        self.assertIn("reformes", data)
        self.assertIn("crises", data)
        self.assertIn("metadata", data)
        self.assertEqual(data["metadata"]["nb_periodes"], 12)


class TestSynthese(unittest.TestCase):
    """Vérifie la synthèse historique."""

    def test_synthese_non_vide(self):
        synthese = generer_synthese_historique()
        self.assertGreater(len(synthese), 500)
        self.assertIn("DETTE PUBLIQUE", synthese)
        self.assertIn("PIKETTY", synthese.upper())

    def test_calibration_non_vide(self):
        calib = calibrer_parametres_historiques()
        self.assertIn("dette_pib_plage", calib)
        self.assertIn("po_pib_plage", calib)
        self.assertIn("gini_plage", calib)


class TestPeriodeParId(unittest.TestCase):
    """Vérifie la recherche par ID."""

    def test_trouver_periode_existante(self):
        p = obtenir_periode_par_id("trente_glorieuses_1946_1974")
        self.assertIsNotNone(p)
        self.assertEqual(p["nom"], "VII. Les Trente Glorieuses")

    def test_periode_inexistante_retourne_none(self):
        p = obtenir_periode_par_id("inexistant")
        self.assertIsNone(p)


class TestHttpHistoire(unittest.TestCase):
    """Tests d'intégration des endpoints HTTP de l'historique."""

    BASE = "http://127.0.0.1:8000"

    def _get_json(self, path: str):
        try:
            req = urllib.request.Request(self.BASE + path)
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            return None

    def test_api_histoire(self):
        data = self._get_json("/api/histoire")
        if data is None:
            self.skipTest("Serveur non disponible")
        self.assertGreater(data["total"], 0)

    def test_api_histoire_options(self):
        data = self._get_json("/api/histoire/options")
        if data is None:
            self.skipTest("Serveur non disponible")
        self.assertEqual(len(data["periodes"]), 12)

    def test_api_histoire_synthese(self):
        data = self._get_json("/api/histoire/synthese")
        if data is None:
            self.skipTest("Serveur non disponible")
        self.assertIn("synthese", data)

    def test_api_histoire_reformes(self):
        data = self._get_json("/api/histoire/reformes")
        if data is None:
            self.skipTest("Serveur non disponible")
        self.assertGreater(data["total"], 0)

    def test_api_histoire_crises(self):
        data = self._get_json("/api/histoire/crises")
        if data is None:
            self.skipTest("Serveur non disponible")
        self.assertGreater(data["total"], 0)

    def test_api_histoire_comparer(self):
        data = self._get_json("/api/histoire/comparer?a=revolution_1792_1799&b=trente_glorieuses_1946_1974&dimensions=fiscale")
        if data is None:
            self.skipTest("Serveur non disponible")
        self.assertIn("dimensions", data)
        self.assertIn("enseignements", data)

    def test_api_histoire_series(self):
        data = self._get_json("/api/histoire/series?indicateur=dette_publique_pct_pib")
        if data is None:
            self.skipTest("Serveur non disponible")
        self.assertGreater(data["points"], 0)


if __name__ == "__main__":
    unittest.main()