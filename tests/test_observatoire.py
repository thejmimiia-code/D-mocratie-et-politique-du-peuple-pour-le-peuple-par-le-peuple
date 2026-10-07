"""Repères vérifiables de l'observatoire public et bornes méthodologiques."""

import unittest

from simulateur.observatoire import DATE_COLLECTE, observatoire_public


class TestObservatoirePublic(unittest.TestCase):
    def test_dates_sources_et_frequences_sont_exposees(self):
        observatoire = observatoire_public()
        self.assertEqual(observatoire["collecte_le"], DATE_COLLECTE)
        for bloc in (
            observatoire["finances_locales"],
            observatoire["comptes_nationaux"],
            observatoire["ipch_europe"],
            observatoire["menages"]["consommation_2025"],
            observatoire["menages"]["panier_national_2025"],
            observatoire["menages"]["effort_logement_2024"],
            observatoire["menages"]["transferts"]["minima_sociaux"],
        ):
            with self.subTest(source=bloc["source"]):
                self.assertTrue(bloc["periode"])
                self.assertEqual(bloc["collecte_le"], DATE_COLLECTE)
                self.assertTrue(bloc["frequence"])
                self.assertTrue(bloc["url"].startswith("https://"))

    def test_minima_distinguent_personnes_et_allocations(self):
        minima = observatoire_public()["menages"]["transferts"]["minima_sociaux"]
        self.assertAlmostEqual(minima["beneficiaires_millions"], 4.252)
        self.assertAlmostEqual(minima["allocations_versees_millions"], 4.4168)
        self.assertAlmostEqual(minima["montant_total_mde"], 33.3)
        self.assertIn("doubles comptes", minima["note"])
        self.assertEqual(minima["periode"], "2024 (effectifs au 31 décembre)")

    def test_cheque_energie_est_clairement_historique(self):
        cheque = observatoire_public()["menages"]["transferts"]["cheque_energie"]
        self.assertTrue(cheque["periode"].startswith("2023"))
        self.assertEqual(cheque["beneficiaires_millions"], 5.6)
        self.assertIn("pas une estimation", cheque["note"])
        self.assertIn("2023", cheque["url"])

    def test_repere_de_panier_est_provisoire_et_inclut_la_correction(self):
        panier = observatoire_public()["menages"]["panier_national_2025"]
        self.assertEqual(panier["statut"], "Données provisoires.")
        correction = next(
            ligne for ligne in panier["part_depense_finale_pct"]
            if ligne["cle"] == "correction_tourisme"
        )
        self.assertEqual(correction["part"], -1.3)

    def test_appel_renvoie_une_copie_profonde(self):
        premier = observatoire_public()
        premier["menages"]["transferts"]["minima_sociaux"]["beneficiaires_millions"] = 0
        second = observatoire_public()
        self.assertAlmostEqual(
            second["menages"]["transferts"]["minima_sociaux"]["beneficiaires_millions"],
            4.252,
        )


if __name__ == "__main__":
    unittest.main()
