"""Tests de fuite temporelle et de scores ; les exemples sont tous fictifs."""

import json
import math
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path

from simulateur.validation_temporelle import (
    CIBLE,
    Observation,
    Registre,
    avertissements_echantillon,
    evaluer,
    importer_jsonl,
    metriques,
    prevoir,
)

FIXTURE = Path(__file__).parent / 'fixtures' / 'observations_synthetiques.jsonl'


def observation(**changements):
    base = {'identifiant': 'A:2020-01', 'unite': 'A', 'mois': '2020-01', 'revision': 1,
                'cible': CIBLE, 'valeur': 1, 'couverture': 'complete', 'nature': 'synthetique',
                'source': 'synthetic://test', 'version_source': '1', 'licence': 'GPL-3.0',
                'preuve_disponibilite': 'synthetic://preuve', 'publication': '2020-02-01',
                'disponibilite': '2020-02-01', 'ingestion': '2020-02-01'}
    return Observation(**{**base, **changements})


class TestValidationTemporelle(unittest.TestCase):
    def setUp(self):
        self.registre = importer_jsonl(FIXTURE)

    def test_import_fixture_et_revisions(self):
        self.assertEqual(len(self.registre.observations), 74)
        avant = self.registre.instantane('2021-01-31')
        apres = self.registre.instantane('2021-02-01')
        self.assertEqual(avant['FICTIF_A', '2020-03'].valeur, 1)
        self.assertEqual(apres['FICTIF_A', '2020-03'].valeur, 0)

    def test_registre_insensible_ordre(self):
        inverse = Registre(tuple(reversed(self.registre.observations)))
        self.assertEqual(inverse.empreinte(), self.registre.empreinte())
        self.assertEqual(inverse.instantane('2021-12-01'), self.registre.instantane('2021-12-01'))

    def test_revision_future_ne_change_pas_prevision_passee(self):
        sans_revision = Registre(tuple(o for o in self.registre.observations if o.revision == 1))
        a = prevoir(self.registre, '2020-12-01', ('FICTIF_A',))
        b = prevoir(sans_revision, '2020-12-01', ('FICTIF_A',))
        self.assertEqual(a, b)
        self.assertNotEqual(prevoir(self.registre, '2021-03-01', ('FICTIF_A',)),
                            prevoir(sans_revision, '2021-03-01', ('FICTIF_A',)))

    def test_mutation_du_futur_sans_effet(self):
        modifies = tuple(replace(o, valeur=1-o.valeur) if o.mois >= '2021-01'
                         and o.valeur is not None else o for o in self.registre.observations)
        self.assertEqual(prevoir(self.registre, '2020-12-01', ('FICTIF_A', 'FICTIF_B')),
                         prevoir(Registre(modifies), '2020-12-01', ('FICTIF_A', 'FICTIF_B')))

    def test_publication_du_jour_exclue(self):
        r = Registre((observation(),))
        self.assertEqual(len(prevoir(r, '2020-02-01', ('A',), minimum=1)['predictions']), 0)
        self.assertEqual(len(prevoir(r, '2020-03-01', ('A',), minimum=1)['predictions']), 2)

    def test_public_et_local_distincts(self):
        r = Registre((observation(ingestion='2020-04-01'),))
        self.assertEqual(r.instantane('2020-03-01'), {})
        self.assertEqual(len(r.instantane('2020-03-01', 'publique')), 1)
        self.assertEqual(prevoir(r, '2020-03-01', ('A',), 1)['predictions'], [])
        self.assertEqual(len(prevoir(r, '2020-03-01', ('A',), 1, 'publique')['predictions']), 2)

    def test_retrait_ne_reutilise_pas_ancienne_etiquette(self):
        snapshot = self.registre.instantane('2022-01-01')
        o = snapshot['FICTIF_B', '2021-04']
        self.assertIsNone(o.valeur)
        revisions = prevoir(self.registre, '2021-09-01', ('FICTIF_B',))['predictions'][0]['revisions_utilisees']
        self.assertFalse(any(i == o.identifiant for i, _ in revisions))

    def test_abstention_pas_zero(self):
        r = prevoir(self.registre, '2020-03-01', ('FICTIF_A', 'INCONNU'))
        self.assertEqual(r['predictions'], [])
        self.assertEqual(len(r['abstentions']), 2)

    def test_scores_connus(self):
        s = metriques([(0.25, 0), (0.75, 1)])
        self.assertAlmostEqual(s['brier'], 0.0625)
        self.assertAlmostEqual(s['log_loss'], -math.log(0.75))
        self.assertEqual(s['vrais_positifs'], 1)
        self.assertEqual(s['vrais_negatifs'], 1)
        self.assertEqual(sum(b['n'] for b in s['calibration_descriptive']), 2)

    def test_extremes_et_echantillon_vide(self):
        s = metriques([(0, 1), (1, 0), (0.5, 1)])
        self.assertTrue(math.isfinite(s['log_loss']))
        self.assertEqual(s['evenements_manques'], 1)
        self.assertEqual(s['fausses_alertes'], 1)
        vide = metriques([])
        self.assertIsNone(vide['brier'])
        self.assertIsNone(vide['log_loss'])

    def test_evaluation_appariee_et_exclusions(self):
        r = evaluer(self.registre, '2020-07-01', '2021-12-01', '2022-02-01',
                    ('FICTIF_A', 'FICTIF_B', 'FICTIF_C'))
        self.assertEqual(r['scores']['frequence_lissee']['n'], 48)
        self.assertEqual(r['scores']['dernier_etat_lisse']['n'], 48)
        self.assertEqual(len(r['abstentions']), 3)
        self.assertEqual(len(r['exclusions']), 6)  # 3 cellules × 2 modèles
        for p in r['predictions']:
            for identifiant, revision in p['revisions_utilisees']:
                o = next(o for o in self.registre.observations
                         if o.identifiant == identifiant and o.revision == revision)
                self.assertLess(o.ingestion, p['origine'])
                self.assertLess(o.mois, p['mois_cible'])
        json.dumps(r, allow_nan=False)

    def test_scores_changent_mais_pas_previsions_avec_verite_revisee(self):
        a = evaluer(self.registre, '2021-04-01', '2021-04-01', '2021-06-01', ('FICTIF_B',))
        b = evaluer(self.registre, '2021-04-01', '2021-04-01', '2021-09-01', ('FICTIF_B',))
        self.assertEqual(a['predictions'][0]['probabilite'], b['predictions'][0]['probabilite'])
        self.assertEqual(a['scores']['frequence_lissee']['n'], 1)
        self.assertEqual(b['scores']['frequence_lissee']['n'], 0)

    def test_champs_invalides(self):
        for changements in ({'valeur': True}, {'valeur': None}, {'couverture': 'incomplete'},
                             {'mois': '2020-13'}, {'publication': '2020-01-31'},
                             {'disponibilite': '2020-01-31'}, {'ingestion': '2020-01-31'},
                             {'source': ''}, {'licence': ' '}, {'preuve_disponibilite': ''},
                             {'revision': True}, {'cible': 'guerre_mondiale'}, {'nature': 'incertaine'}):
            with self.subTest(changements=changements), self.assertRaises(ValueError):
                observation(**changements)

    def test_registre_invalide(self):
        o = observation()
        cas = ((), (o, o), (o, replace(o, identifiant='autre')),
               (o, replace(o, revision=2, unite='B')),
               (o, replace(o, identifiant='B', unite='B', nature='observee')),
               (replace(o, publication='2020-03-01', disponibilite='2020-03-01',
                        ingestion='2020-03-01'), replace(o, revision=2)))
        for observations in cas:
            with self.assertRaises(ValueError):
                Registre(observations)

    def test_import_erreur_contextualisee(self):
        with tempfile.TemporaryDirectory() as dossier:
            p = Path(dossier) / 'erreur.jsonl'
            for texte in ('[]', '{"valeur":0,"valeur":1}', '{}', '{pas du json}'):
                p.write_text(texte)
                with self.assertRaisesRegex(ValueError, 'ligne 1'):
                    importer_jsonl(p)
            donnees = {**asdict(observation()), **{'inconnu': 'non autorisé'}}
            p.write_text(json.dumps(donnees))
            with self.assertRaises(ValueError):
                importer_jsonl(p)

    def test_configuration_invalide(self):
        for origine in ('2020-07-02', '2020-7-01', 'inconnue'):
            with self.assertRaises(ValueError):
                prevoir(self.registre, origine, ('FICTIF_A',))
        for unites in ((), ('A', 'A'), ('',)):
            with self.assertRaises(ValueError):
                prevoir(self.registre, '2020-07-01', unites)
        with self.assertRaises(ValueError):
            prevoir(self.registre, '2020-07-01', ('A',), minimum=True)
        with self.assertRaises(ValueError):
            self.registre.instantane('2020-07-01', 'futur')
        with self.assertRaises(ValueError):
            evaluer(self.registre, '2020-07-01', '2020-08-01', '2020-08-15', ('A',))
        for p, y in ((float('nan'), 1), (1.1, 0), (True, 1), (0.5, True)):
            with self.assertRaises(ValueError):
                metriques([(p, y)])

    def test_la_frequence_de_base_est_publiee(self):
        """Un Brier de 0,2222 ne se lit pas sans elle — et elle est publiée."""
        rapport = metriques([(0.9, 1), (0.8, 1), (0.2, 0), (0.1, 0)])
        self.assertEqual(rapport['n'], 4)
        self.assertEqual(rapport['cas_positifs'], 2)
        self.assertEqual(rapport['cas_negatifs'], 2)
        self.assertEqual(rapport['frequence_de_base'], 0.5)
        self.assertAlmostEqual(rapport['brier'], (0.01 + 0.04 + 0.04 + 0.01) / 4)

    def test_la_reference_sans_competence_est_le_produit(self):
        """Référence = p(1-p) : le Brier de qui annonce partout la fréquence.

        Le jeu est parfait : tous les cas positifs au-dessus du seuil, tous les
        négatifs en dessous. La compétence doit donc être franchement positive —
        et une prévision constante à la fréquence de base, exactement nulle.
        """
        parfait = metriques([(0.9, 1), (0.8, 1), (0.2, 0), (0.1, 0)])
        self.assertAlmostEqual(parfait['brier_reference_sans_competence'], 0.25)
        self.assertGreater(parfait['competence_brier'], 0)
        self.assertIsNone(parfait['competence_non_publiee_pour'])
        nulle = metriques([(0.5, 1), (0.5, 1), (0.5, 0), (0.5, 0)])
        self.assertAlmostEqual(nulle['competence_brier'], 0.0, places=12,
                               msg="annoncer la fréquence de base ne peut pas être "
                                   "une compétence")

    def test_sans_cas_negatif_aucune_competence_n_est_publiee(self):
        """La lacune P0 « pas de cas négatifs », comblée en la publiant.

        Sur un échantillon qui ne porte qu'un côté, un score de compétence
        mesurerait la fréquence du corpus, pas la prévision : le rapport refuse
        de le publier, et dit lequel des deux cas manque.
        """
        for paires, motif in (((0.9, 1), (0.8, 1)), 'aucun_cas_negatif'), \
                             (((0.2, 0), (0.1, 0)), 'aucun_cas_positif'):
            with self.subTest(motif=motif):
                rapport = metriques(list(paires))
                self.assertIsNone(rapport['competence_brier'],
                                  "une compétence est publiée sur un échantillon à un seul côté")
                self.assertEqual(rapport['competence_non_publiee_pour'], motif)
                self.assertIsNotNone(rapport['frequence_de_base'],
                                     "la fréquence de base reste due, même sans compétence")
        vide = metriques([])
        self.assertIsNone(vide['competence_brier'])
        self.assertEqual(vide['competence_non_publiee_pour'], 'echantillon_vide')
        self.assertIsNone(vide['frequence_de_base'])

    def test_l_avertissement_parle_du_score_publie(self):
        """Les mêmes nombres : l'avertissement ne parle pas d'un jumeau."""
        scores = {'un_seul_cote': metriques([(0.9, 1), (0.8, 1), (0.7, 1)])}
        avertissements = avertissements_echantillon(scores)
        self.assertEqual(len(avertissements), 1)
        self.assertIn('un_seul_cote', avertissements[0])
        self.assertIn('sans cas négatif', avertissements[0])
        self.assertIn('3 cas évalués', avertissements[0])
        self.assertIn(str(scores['un_seul_cote']['frequence_de_base']), avertissements[0],
                      "l'avertissement ne donne pas la fréquence du score publié")
        deux_cotes = {'complet': metriques([(0.9, 1), (0.1, 0)])}
        self.assertEqual(avertissements_echantillon(deux_cotes), [],
                         "un échantillon qui porte les deux cas n'a rien à signaler")
        self.assertEqual(len(avertissements_echantillon({'vide': metriques([])})), 1)

    def test_le_corpus_synthetique_porte_les_deux_cas(self):
        """18 positifs, 30 négatifs, fréquence 0,375 — mesuré, pas supposé.

        C'est la condition pour qu'une compétence soit publiée : sans elle, le
        rapport se tairait, et c'est ce silence-là qu'on vérifie.
        """
        resultat = evaluer(self.registre, '2020-07-01', '2021-12-01', '2022-02-01',
                           ('FICTIF_A', 'FICTIF_B', 'FICTIF_C'))
        self.assertEqual(resultat['avertissements_echantillon'], [])
        for nom, rapport in resultat['scores'].items():
            with self.subTest(modele=nom):
                self.assertEqual(rapport['n'], 48)
                self.assertEqual(rapport['cas_positifs'], 18)
                self.assertEqual(rapport['cas_negatifs'], 30)
                self.assertEqual(rapport['frequence_de_base'], 0.375)
                self.assertAlmostEqual(rapport['brier_reference_sans_competence'],
                                       0.375 * 0.625)
                self.assertIsNotNone(rapport['competence_brier'])

    def test_les_deux_references_sont_comparees_a_la_frequence_de_base(self):
        """Le résultat mesuré : l'une coûte plus qu'elle n'apprend, l'autre non.

        Mesuré le 15 octobre 2026 sur le corpus synthétique : `frequence_lissee`
        fait moins bien que d'annoncer partout 0,375 (compétence −0,108) ;
        `dernier_etat_lisse` fait à peine mieux (+0,052). C'est ce que la
        fréquence de base permet enfin de dire — et un chiffre qu'on veut voir
        changer si le protocole change.
        """
        resultat = evaluer(self.registre, '2020-07-01', '2021-12-01', '2022-02-01',
                           ('FICTIF_A', 'FICTIF_B', 'FICTIF_C'))
        lissee = resultat['scores']['frequence_lissee']['competence_brier']
        dernier = resultat['scores']['dernier_etat_lisse']['competence_brier']
        self.assertLess(lissee, 0,
                        "le lissage fait maintenant mieux que la fréquence de base : "
                        "le protocole a changé, le dire")
        self.assertGreater(dernier, 0,
                           "le dernier état ne bat plus la fréquence de base : "
                           "le protocole a changé, le dire")
        self.assertGreater(dernier, lissee)

    def test_le_rapport_ne_publie_toujours_pas_de_probabilite(self):
        """La fréquence de base ne transforme pas un score en probabilité."""
        resultat = evaluer(self.registre, '2020-07-01', '2021-12-01', '2022-02-01',
                           ('FICTIF_A', 'FICTIF_B', 'FICTIF_C'))
        self.assertIn('aucun score de guerre mondiale ou nucléaire', resultat['avertissement'])
        for nom, rapport in resultat['scores'].items():
            with self.subTest(modele=nom):
                self.assertNotIn('probabilite', rapport,
                                 "un score de référence s'affiche comme une probabilité")

    def test_empreinte_change_si_revision(self):
        r = Registre(tuple(o for o in self.registre.observations if o.revision == 1))
        self.assertNotEqual(r.empreinte(), self.registre.empreinte())
