"""
tests/test_donnees_live.py — Tests du socle « données vivantes ».

Le module `simulateur.donnees_live` est la source de vérité des chiffres
affichés par le simulateur : registre d'indicateurs, sources publiques
licenciées, snapshot daté, contexte « instant T » et collecte navigateur.

Ces tests s'exécutent **hors ligne** : ils vérifient le contrat (provenance,
licences, cohérence interne) et non la disponibilité d'Internet.
"""

import json
import tempfile
import unittest
from dataclasses import fields
from pathlib import Path

from simulateur.donnees_live import (
    _CORRESPONDANCE,
    _REPLI,
    ADAPTATEURS_SERVEUR,
    DATE_VERIFICATION,
    INDICATEURS,
    ContexteInstant,
    Lecture,
    browser_payload,
    charger_cache,
    collecter,
    construire_contexte,
    sauver_cache,
)


class TestRegistreIndicateurs(unittest.TestCase):
    """Chaque indicateur doit être sourcé, licencié et exploitable."""

    def test_registre_non_vide_et_cle_coherente(self):
        self.assertGreaterEqual(len(INDICATEURS), 30)
        for cle, indicateur in INDICATEURS.items():
            with self.subTest(indicateur=cle):
                self.assertEqual(cle, indicateur.cle)
                self.assertTrue(indicateur.libelle.strip())
                self.assertTrue(indicateur.unite.strip())
                self.assertIsInstance(indicateur.precision, int)
                self.assertGreaterEqual(indicateur.precision, 0)

    def test_chaque_indicateur_a_une_source_publique_licenciee(self):
        for cle, indicateur in INDICATEURS.items():
            with self.subTest(indicateur=cle):
                self.assertTrue(indicateur.sources, "aucune source déclarée")
                for source in indicateur.sources:
                    self.assertIn(source.adaptateur, ADAPTATEURS_SERVEUR)
                    self.assertTrue(source.fournisseur.strip())
                    self.assertTrue(source.licence.strip(), "licence manquante")
                    self.assertTrue(source.url.startswith("https://"))
                    self.assertTrue(source.url_page.startswith("https://"))

    def test_au_moins_une_source_par_indicateur_pour_le_navigateur(self):
        exposees = browser_payload()
        self.assertTrue(exposees)
        for cle, charge in exposees.items():
            with self.subTest(indicateur=cle):
                self.assertIn(cle, INDICATEURS)
                self.assertIsInstance(charge["sources"], list)
                for source in charge["sources"]:
                    self.assertTrue(source["url"].startswith("https://"))
                    self.assertIn(source["adaptateur"], ADAPTATEURS_SERVEUR)
                    self.assertTrue(source["licence"])

    def test_reference_datee_ou_marquee_a_collecter(self):
        """Un indicateur sans snapshot doit le dire explicitement."""
        for cle, indicateur in INDICATEURS.items():
            with self.subTest(indicateur=cle):
                if indicateur.reference is None:
                    self.assertIn("collecter", indicateur.note.lower())
                else:
                    valeur, periode, fournisseur, verifie = indicateur.reference
                    self.assertIsInstance(valeur, float)
                    self.assertTrue(periode)
                    self.assertTrue(fournisseur)
                    self.assertEqual(verifie, DATE_VERIFICATION)


class TestRepliEtCorrespondance(unittest.TestCase):
    """Le repli documentaire ne doit jamais contredire le snapshot daté."""

    def test_repli_aligne_sur_le_snapshot(self):
        for champ, cle in _CORRESPONDANCE.items():
            indicateur = INDICATEURS[cle]
            if not indicateur.reference or indicateur.reference[0] is None:
                continue
            with self.subTest(champ=champ):
                self.assertAlmostEqual(
                    float(_REPLI[champ]), float(indicateur.reference[0]), places=6
                )

    def test_correspondance_pointe_sur_des_indicateurs_existants(self):
        for champ, cle in _CORRESPONDANCE.items():
            with self.subTest(champ=champ):
                self.assertIn(cle, INDICATEURS)

    def test_contexte_contient_tous_les_champs_calibrables(self):
        champs = {f.name for f in fields(ContexteInstant)}
        for champ in _CORRESPONDANCE:
            self.assertIn(champ, champs)


class TestContexteInstant(unittest.TestCase):
    """Le contexte hors ligne reste complet, daté et traçable."""

    @classmethod
    def setUpClass(cls):
        cls.contexte = construire_contexte(utiliser_cache=False, rafraichir=False)

    def test_mode_reference_hors_ligne(self):
        self.assertEqual(self.contexte.mode, "reference")
        self.assertTrue(self.contexte.horodatage)

    def test_valeurs_plausibles(self):
        contexte = self.contexte
        self.assertGreater(contexte.pib_nominal_mde, 2000.0)
        self.assertLess(contexte.pib_nominal_mde, 4000.0)
        self.assertGreater(contexte.dette_publique_pct_pib, 60.0)
        self.assertLess(contexte.dette_publique_pct_pib, 200.0)
        self.assertGreater(contexte.taux_oat_10ans, 0.0)
        self.assertLess(contexte.taux_oat_10ans, 15.0)
        self.assertGreater(contexte.brent_usd, 10.0)
        self.assertLess(contexte.brent_usd, 400.0)

    def test_spread_et_charge_de_dette_coherents(self):
        contexte = self.contexte
        self.assertAlmostEqual(
            contexte.spread_oat_bund_bps,
            round((contexte.taux_oat_10ans - contexte.taux_bund_10ans) * 100.0, 1),
            places=1,
        )
        self.assertGreater(contexte.charge_dette_estimee_mde, 10.0)
        self.assertLess(contexte.charge_dette_estimee_mde, 200.0)

    def test_provenance_complete_et_licenciee(self):
        provenance = self.contexte.en_dict()["provenance"]
        for champ in _CORRESPONDANCE:
            with self.subTest(champ=champ):
                info = provenance[champ]
                self.assertTrue(info["libelle"])
                self.assertTrue(info["source"])
                self.assertIn(info["statut"], {"live", "reference", "indisponible", "mixte"})
                self.assertIn("licence", info)

    def test_en_dict_json_serialisable(self):
        charge = self.contexte.en_dict()
        self.assertIn("spread_oat_bund_bps", charge)
        self.assertIn("charge_dette_estimee_mde", charge)
        json.dumps(charge)


class TestCollecteEtCache(unittest.TestCase):
    """Collecte réseau et cache navigateur : contrats de robustesse."""

    def test_collecter_ne_leve_jamais_sans_reseau(self):
        lectures = collecter(["taux_oat_france_10ans"], timeout=0.4)
        self.assertIn("taux_oat_france_10ans", lectures)
        lecture = lectures["taux_oat_france_10ans"]
        self.assertIsInstance(lecture, Lecture)
        self.assertIn(lecture.statut, {"live", "indisponible", "reference", "erreur"})

    def test_enregistrer_donnees_navigateur_ecrit_dans_le_cache(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "cache.json"
            lectures = {
                "gini_france": Lecture(
                    cle="gini_france", valeur=30.4, periode="2025",
                    fournisseur="Eurostat", url="https://ec.europa.eu/",
                    statut="live",
                )
            }
            sauver_cache(lectures, chemin=chemin)
            relues = charger_cache(chemin=chemin)
            self.assertEqual(relues["gini_france"].valeur, 30.4)
            self.assertEqual(relues["gini_france"].statut, "live")

    def test_charger_cache_inexistant_retourne_vide(self):
        with tempfile.TemporaryDirectory() as dossier:
            self.assertEqual(charger_cache(chemin=Path(dossier) / "absent.json"), {})

    def test_charger_cache_corrompu_ne_leve_pas(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "corrompu.json"
            chemin.write_text("{ pas du json", encoding="utf-8")
            self.assertEqual(charger_cache(chemin=chemin), {})

    def test_une_lecture_live_recalibre_le_contexte(self):
        """Une valeur fournie par le navigateur doit remonter dans le contexte."""
        lectures = {
            "taux_oat_france_10ans": Lecture(
                cle="taux_oat_france_10ans", valeur=4.42, periode="2026-10",
                fournisseur="test", url="https://example.org/", statut="live",
            )
        }
        contexte = construire_contexte(lectures=lectures)
        self.assertAlmostEqual(contexte.taux_oat_10ans, 4.42, places=2)
        self.assertIn(contexte.mode, {"live", "mixte"})


if __name__ == "__main__":
    unittest.main()
