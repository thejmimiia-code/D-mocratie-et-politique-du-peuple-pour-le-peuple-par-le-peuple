"""Invariants physiques et expériences contrefactuelles, pas validation prédictive."""

import json
import unittest
from dataclasses import replace

from simulateur.geopolitique import (
    Acteur,
    Alliance,
    Evenement,
    Parametres,
    Secteur,
    campagne,
    cas_experimental,
    coupler_macro,
    resumer,
    simuler,
)
from simulateur.model import DecisionPolitique
from simulateur.moteur import MoteurSimulationSystemique


class TestGeopolitique(unittest.TestCase):
    def setUp(self):
        self.acteurs = (Acteur('A', True), Acteur('B'), Acteur('C', True))
        self.secteurs = (Secteur('energie'),)

    def test_temoin_sans_choc(self):
        r = cas_experimental(duree=0)
        self.assertEqual(resumer(r)['mois_en_penurie'], 0)
        self.assertEqual(resumer(r)['tension_max'], 0)
        for a in r['macro']['annees']:
            self.assertEqual(a['expose'], a['temoin'])

    def test_conservation_flux(self):
        for stock in (0.0, 1.0, 3.0):
            for substitution in (0, 0.25, 1):
                r = cas_experimental(stock=stock, substitution=substitution)
                for m in r['mois']:
                    for f in m['flux'].values():
                        self.assertAlmostEqual(f['stock_initial'] + f['approvisionnement'],
                                               f['servi'] + f['stock_final'] + f['excedent'])
                        self.assertAlmostEqual(f['demande'], f['servi'] + f['penurie'])
                        self.assertTrue(all(v >= -1e-10 for v in f.values()))

    def test_stock_et_substitution_reduisent_penurie(self):
        def perte(stock, substitution):
            return resumer(cas_experimental(stock=stock, substitution=substitution))['penurie_cumulee_mois_demande']
        self.assertGreater(perte(0, 0.25), perte(1, 0.25))
        self.assertGreater(perte(1, 0.25), perte(3, 0.25))
        self.assertGreater(perte(1, 0), perte(1, 0.75))

    def test_delai_substitution_et_fin_blocus(self):
        r = cas_experimental(duree=6)
        for m in r['mois'][:3]:
            self.assertEqual(m['flux']['energie']['substitution'], 0)
        self.assertGreater(r['mois'][3]['flux']['energie']['substitution'], 0)
        self.assertEqual(r['mois'][6]['flux']['energie']['substitution'], 0)
        self.assertEqual(r['mois'][6]['penurie_ponderee'], 0)

    def test_blocage_total_stock_nul(self):
        s = Secteur('x', part_importee=1, exposition_route=1, stock_mois=0, substitution=0)
        r = simuler(self.acteurs, (), (s,), (Evenement(1, blocus=1),), 1)
        self.assertEqual(r['mois'][0]['penurie_ponderee'], 1)

    def test_alliance_conditionnelle_et_delai(self):
        r = cas_experimental()
        self.assertEqual(r['mois'][0]['interventions_calculees'], [])
        self.assertEqual(r['mois'][1]['interventions_calculees'], [['C', 'A']])
        self.assertFalse(r['mois'][0]['confrontation_nucleaire_directe'])
        self.assertTrue(r['mois'][1]['confrontation_nucleaire_directe'])
        sans = cas_experimental(autorisation=False)
        self.assertTrue(all(not m['interventions_calculees'] for m in sans['mois']))

    def test_alliance_pas_de_contagion_recursive(self):
        acteurs = (*self.acteurs, Acteur('D'))
        e = (Evenement(1, combats=(('A', 'B'),), autorisations=('C', 'D')),)
        r = simuler(acteurs, (Alliance('C', 'B', 0), Alliance('D', 'A', 0)), self.secteurs, e, 1)
        self.assertEqual(r['mois'][0]['interventions_calculees'], [['C', 'A']])

    def test_delai_reinitialise_apres_accalmie(self):
        e = tuple(Evenement(m, combats=(('A', 'B'),), autorisations=('C',)) for m in (1, 3))
        r = simuler(self.acteurs, (Alliance('C', 'B'),), self.secteurs, e, 3)
        self.assertTrue(all(not m['interventions_calculees'] for m in r['mois']))

    def test_mediation_et_desescalade(self):
        crise, mediation = cas_experimental(), cas_experimental(mediation=True)
        self.assertLess(resumer(mediation)['tension_max'], resumer(crise)['tension_max'])
        self.assertLess(crise['mois'][-1]['indice_tension_conventionnel'],
                        crise['mois'][17]['indice_tension_conventionnel'])
        # La médiation n'ouvre pas magiquement la route : le blocus reste imposé.
        self.assertEqual([m['penurie_ponderee'] for m in crise['mois']],
                         [m['penurie_ponderee'] for m in mediation['mois']])

    def test_pas_emploi_automatique_et_arret_explicite(self):
        r = cas_experimental()
        self.assertIsNone(r['arret'])
        self.assertIn('alerte', [m['posture_heuristique'] for m in r['mois']])
        for mois in (1, 8, 13):
            r = cas_experimental(emploi_mois=mois)
            self.assertEqual(len(r['mois']), mois - 1)
            self.assertEqual(len(r['macro']['annees']), (mois - 1) // 12)
            self.assertEqual(r['arret']['mois'], mois)

    def test_sensibilite_macro(self):
        faible = cas_experimental(parametres=Parametres(elasticite_penurie=0.02))
        fort = cas_experimental(parametres=Parametres(elasticite_penurie=0.08))
        nul = cas_experimental(parametres=Parametres(elasticite_penurie=0))
        self.assertLess(resumer(fort)['dernier_ecart_pib_mde'], resumer(faible)['dernier_ecart_pib_mde'])
        for annee in nul['macro']['annees']:
            self.assertEqual(annee['expose'], annee['temoin'])
        self.assertEqual(faible['mois'], fort['mois'])  # couplage unidirectionnel déclaré

    def test_reproductibilite_et_isolation(self):
        r = cas_experimental()
        avant = json.dumps(r, sort_keys=True, allow_nan=False)
        self.assertEqual(r, cas_experimental())
        self.assertEqual(r['macro'], coupler_macro(r))
        self.assertEqual(avant, json.dumps(r, sort_keys=True, allow_nan=False))

    def test_validation(self):
        for valeur in (-1, 1.1, float('nan'), float('inf'), True):
            with self.assertRaises(ValueError):
                Evenement(1, blocus=valeur)
        for valeur in (0, 1.5, True, 121):
            with self.assertRaises(ValueError):
                Evenement(valeur)
        with self.assertRaises(ValueError):
            Parametres(seuil_signal=60, seuil_alerte=60)
        with self.assertRaises(ValueError):
            replace(self.secteurs[0], poids_pib=float('nan'))
        for evenements in ((Evenement(1), Evenement(1)), (Evenement(2),),
                           (Evenement(1, combats=(('X', 'A'),)),),
                           (Evenement(1, autorisations=('X',)),)):
            with self.assertRaises(ValueError):
                simuler(self.acteurs, (), self.secteurs, evenements, 1)
        with self.assertRaises(ValueError):
            simuler(self.acteurs, (Alliance('X', 'B'),), self.secteurs, (), 1)
        with self.assertRaises(ValueError):
            simuler(self.acteurs, (), (replace(self.secteurs[0], poids_pib=0.5),), (), 1)

    def test_pont_macro_validation_et_premiere_annee(self):
        moteur = MoteurSimulationSystemique()
        for valeur in (0, -1, 1.01, float('nan'), float('inf'), True):
            with self.assertRaises(ValueError):
                moteur.appliquer_etape(DecisionPolitique(), facteur_activite=valeur)
        self.assertEqual(moteur.historique_etapes, [])
        expose = moteur.appliquer_etape(DecisionPolitique(), facteur_activite=0.9)
        temoin = MoteurSimulationSystemique().appliquer_etape(DecisionPolitique())
        self.assertLess(expose.pib_nominal_mde, temoin.pib_nominal_mde)
        self.assertLess(expose.recettes_publiques_totales_mde, temoin.recettes_publiques_totales_mde)

    def test_persistence_apres_blocus(self):
        r = cas_experimental()
        dernier = r['macro']['annees'][-1]
        self.assertEqual(dernier['penurie_moyenne'], 0)
        self.assertLess(dernier['facteur_activite_cumule'], 1)
        self.assertLess(dernier['ecart_pib_mde'], 0)

    def test_campagne(self):
        r = campagne()
        self.assertEqual(len(r['sensibilite']), 81)
        self.assertEqual(len(r['cas']), 5)
        self.assertEqual(len(r['sensibilite_escalade']), 27)
        json.dumps(r, allow_nan=False)
