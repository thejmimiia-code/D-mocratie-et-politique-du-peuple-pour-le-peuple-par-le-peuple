"""Tests du protocole, sans supposer la supériorité d'une politique."""
import math
import unittest
from dataclasses import asdict

from simulateur.laboratoire import Experience, campagne, comparer, executer
from simulateur.scenarios import get_scenario_mandature_5_ans


class TestLaboratoire(unittest.TestCase):
    def test_reproductibilite(self):
        self.assertEqual(campagne(3, 42), campagne(3, 42))
        self.assertNotEqual(campagne(3, 42), campagne(3, 43))

    def test_isolation_et_choc_date(self):
        decisions = get_scenario_mandature_5_ans()
        avant = [asdict(d) for d in decisions]
        e = Experience(0.5, 30, -0.1, 100, 3)
        a = executer(decisions, e)
        self.assertEqual(a, executer(decisions, e))
        self.assertEqual(avant, [asdict(d) for d in decisions])
        self.assertEqual(a[:2], executer(decisions, e, False, False)[:2])
        self.assertNotEqual(a[2:], executer(decisions, e, False, False)[2:])

    def test_interaction_nulle_sans_choc(self):
        r = comparer(Experience(1, 0, 0, 0, 1))
        self.assertEqual(r['interaction_deficit_points'], 0)

    def test_temoin_exposition_identique(self):
        r = comparer(Experience(0.3, 60, -0.2, 200, 1))
        for a, b in zip(r['trajectoire_reformes'], r['trajectoire_temoin']):
            for cle in ('cours_petrole_usd', 'taux_change_eur_usd'):
                self.assertEqual(a[cle], b[cle])
            for valeur in a.values():
                if isinstance(valeur, float):
                    self.assertTrue(math.isfinite(valeur))

    def test_validation(self):
        for nombre in (0, -1, 10001, True, 1.5):
            with self.assertRaises(ValueError):
                campagne(nombre)
        for e in ((float('nan'), 0, 0, 0, 1), (1, 61, 0, 0, 1), (1, 0, 0, 0, 6)):
            with self.assertRaises(ValueError):
                Experience(*e)
