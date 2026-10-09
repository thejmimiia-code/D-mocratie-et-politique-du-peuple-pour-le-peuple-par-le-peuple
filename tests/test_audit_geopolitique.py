"""Régressions, contrôles physiques et audit des nouvelles hypothèses."""

import copy
import json
import random
import unittest

from simulateur.audit_geopolitique import auditer, crises_repetees
from simulateur.geopolitique import (
    Acteur,
    Evenement,
    Parametres,
    Secteur,
    cas_experimental,
    coupler_macro,
    simuler,
)


class TestAuditGeopolitique(unittest.TestCase):
    def test_regression_cas_historique(self):
        r = cas_experimental()
        self.assertAlmostEqual(sum(m['penurie_ponderee'] for m in r['mois']), 5.5664)
        self.assertEqual(r['macro']['annees'][-1]['ecart_pib_mde'], -57.84)

    def test_capacite_distincte_du_stock_initial(self):
        secteur = Secteur('x', stock_mois=0, capacite_stock_mois=2, reconstitution_mensuelle=0.5)
        r = simuler((Acteur('A'),), (), (secteur,), (), horizon=6)
        self.assertEqual(r['mois'][0]['flux']['x']['stock_initial'], 0)
        self.assertEqual(r['mois'][0]['flux']['x']['stock_final'], 50)
        self.assertEqual(r['mois'][3]['flux']['x']['stock_final'], 200)
        self.assertEqual(r['mois'][4]['flux']['x']['reconstitution'], 0)

    def test_reconstitution_pause_sous_blocus(self):
        r = crises_repetees(0.25, 0)
        for mois in r['mois']:
            if mois['evenement_impose']['blocus'] > 0:
                self.assertEqual(mois['flux']['approvisionnement']['reconstitution'], 0)

    def test_moins_de_penurie_deuxieme_crise(self):
        sans, avec = crises_repetees(0, 0), crises_repetees(0.25, 0)
        self.assertEqual([m['penurie_ponderee'] for m in sans['mois'][:6]],
                         [m['penurie_ponderee'] for m in avec['mois'][:6]])
        self.assertLess(sum(m['penurie_ponderee'] for m in avec['mois'][12:18]),
                        sum(m['penurie_ponderee'] for m in sans['mois'][12:18]))

    def test_calendrier_strict(self):
        args = ((Acteur('A'),), (), (Secteur('x'),))
        with self.assertRaisesRegex(ValueError, 'Calendrier incomplet'):
            simuler(*args, (Evenement(1), Evenement(3)), 3, calendrier_complet=True)
        r = simuler(*args, (Evenement(1), Evenement(3)), 3)
        self.assertEqual(r['mois_supposes_calmes'], [2])
        r = simuler(*args, tuple(Evenement(i) for i in (1, 2, 3)), 3, calendrier_complet=True)
        self.assertEqual(r['mois_supposes_calmes'], [])

    def test_recuperation_bornee_sans_effet_sur_flux(self):
        sans, partiel, total = [crises_repetees(0, r) for r in (0, 0.5, 1)]
        self.assertEqual(sans['mois'], total['mois'])
        facteurs = [r['macro']['annees'][-1]['facteur_activite_cumule']
                    for r in (sans, partiel, total)]
        self.assertLess(facteurs[0], facteurs[1])
        self.assertLess(facteurs[1], facteurs[2])
        self.assertEqual(facteurs[2], 1)
        self.assertEqual(total['macro']['annees'][0]['recuperation_activite_points'], 0)

    def test_recuperation_nefface_pas_dette_passee(self):
        annee = crises_repetees(0, 1)['macro']['annees'][-1]
        self.assertEqual(annee['ecart_pib_mde'], 0)
        self.assertGreater(annee['expose']['dette_nominale_mde'],
                           annee['temoin']['dette_nominale_mde'])

    def test_factoriel_isole_mediation(self):
        a = cas_experimental(mediation=False, rupture_dialogue=True)
        b = cas_experimental(mediation=True, rupture_dialogue=True)
        self.assertGreater(a['mois'][4]['indice_tension_conventionnel'],
                           b['mois'][4]['indice_tension_conventionnel'])
        for x, y in zip(a['mois'], b['mois']):
            self.assertEqual(x['flux'], y['flux'])
            self.assertEqual(x['interventions_calculees'], y['interventions_calculees'])
            self.assertEqual(x['evenement_impose']['rupture_dialogue'],
                             y['evenement_impose']['rupture_dialogue'])

    def test_conservation_100_calendriers_synthetiques(self):
        rng = random.Random(20261003)
        for _ in range(100):
            stock = rng.uniform(0, 3)
            capacite = stock + rng.uniform(0, 3)
            secteur = Secteur('x', demande=rng.uniform(1, 1000),
                              part_importee=rng.random(), exposition_route=rng.random(),
                              stock_mois=stock, capacite_stock_mois=capacite,
                              reconstitution_mensuelle=rng.random(), substitution=rng.random())
            events = tuple(Evenement(m, blocus=rng.choice((0, 0.2, 0.8, 1))) for m in range(1, 25))
            r = simuler((Acteur('A'),), (), (secteur,), events, 24, calendrier_complet=True)
            for mois in r['mois']:
                f = mois['flux']['x']
                self.assertAlmostEqual(f['stock_initial'] + f['approvisionnement'],
                                       f['servi'] + f['stock_final'] + f['excedent'])
                self.assertAlmostEqual(f['servi'] + f['penurie'], f['demande'])
                self.assertLessEqual(f['stock_final'], f['capacite_stock'])
                self.assertTrue(all(v >= -1e-10 for v in f.values()))
                self.assertTrue(0 <= mois['penurie_ponderee'] <= 1)

    def test_validation_nouveaux_parametres(self):
        with self.assertRaises(ValueError):
            Secteur('x', stock_mois=2, capacite_stock_mois=1)
        for valeur in (-1, 1.1, float('nan'), True, 'inconnu'):
            with self.assertRaises(ValueError):
                Secteur('x', reconstitution_mensuelle=valeur)
            with self.assertRaises(ValueError):
                Parametres(recuperation_annuelle=valeur)
        for valeur in ('non', 0, 1):
            with self.assertRaises(ValueError):
                cas_experimental(rupture_dialogue=valeur)

    def test_macro_refuse_trajectoire_corrompue(self):
        r = cas_experimental()
        for champ, valeur in (('mois', 3), ('penurie_ponderee', float('nan')),
                              ('penurie_ponderee', -0.01)):
            invalide = copy.deepcopy(r)
            invalide['mois'][0][champ] = valeur
            with self.assertRaises(ValueError):
                coupler_macro(invalide)

    def test_audit_reproductible(self):
        r = auditer()
        self.assertEqual(r, auditer())
        self.assertEqual(len(r['crises_repetees']), 9)
        self.assertEqual(len(r['factoriel_dialogue_mediation']), 4)
        json.dumps(r, allow_nan=False)
