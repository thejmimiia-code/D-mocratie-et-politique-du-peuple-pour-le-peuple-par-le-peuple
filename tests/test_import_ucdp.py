"""Adaptateur testé sur CSV fictif : aucune certification de données réelles."""

import csv
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from simulateur.import_ucdp import ContratImport, convertir, date_ged
from simulateur.validation_temporelle import (
    CIBLE,
    CIBLE_UCDP,
    Observation,
    Registre,
    evaluer,
    importer_jsonl,
)

FIXTURES = Path(__file__).parent / 'fixtures'
CSV = FIXTURES / 'ged_schema_synthetique.csv'


class TestImportUCDP(unittest.TestCase):
    def setUp(self):
        self.contrat = ContratImport(**json.loads(
            (FIXTURES / 'contrat_ged_synthetique.json').read_text()))

    def test_conversion_et_provenance(self):
        r = convertir(CSV, self.contrat)
        self.assertEqual(r['synthese'], {'cellules': 6, 'positives': 2, 'negatives': 0, 'inconnues': 4})
        self.assertEqual(r['comptes']['doublons_identiques'], 1)
        self.assertEqual(r['comptes']['evenements_uniques'], 5)
        self.assertEqual(r['comptes']['evenements_retenus'], 4)
        self.assertEqual(r['comptes']['hors_perimetre'], 1)
        self.assertTrue(all(o['cible'] == CIBLE_UCDP for o in r['observations']))
        self.assertEqual(len(r['empreinte_csv_sha256']), 64)
        self.assertEqual(r, convertir(CSV, self.contrat))

    def test_positif_prioritaire_sur_intervalle_ambigu(self):
        r = convertir(CSV, self.contrat)
        janvier = r['audit_cellules'][0]
        self.assertEqual(janvier['valeur'], 1)
        self.assertEqual(janvier['ids_certains'], [1001])
        self.assertEqual(janvier['ids_ambigus'], [1002])
        # Le type 3 (violence unilatérale) n'est pas perdu par un filtre "batailles".
        self.assertEqual(r['audit_cellules'][1]['ids_certains'], [1003])

    def test_intervalles_pas_de_repartition_artificielle(self):
        r = convertir(CSV, self.contrat)
        for cellule in r['audit_cellules'][2:4]:
            self.assertIsNone(cellule['valeur'])
            self.assertEqual(cellule['ids_ambigus'], [1004])
        self.assertNotIn('victimes_estimees', r)

    def test_filtrage_ne_rend_pas_date_precise(self):
        r = convertir(CSV, replace(self.contrat, debut='2024-03', fin='2024-03'))
        self.assertIsNone(r['observations'][0]['valeur'])
        self.assertEqual(r['audit_cellules'][0]['ids_ambigus'], [1004])

    def test_zeros_seulement_si_attestation(self):
        c = replace(self.contrat, couverture_exhaustive=True, preuve_exhaustivite='synthetic://attestation')
        r = convertir(CSV, c)
        self.assertEqual(r['synthese'], {'cellules': 6, 'positives': 2, 'negatives': 2, 'inconnues': 2})
        self.assertIsNone(r['observations'][2]['valeur'])  # ambigu malgré exhaustivité
        self.assertEqual(r['observations'][4]['valeur'], 0)

    def test_aucun_pays_non_present_nest_invente_calme(self):
        r = convertir(CSV, replace(self.contrat, pays_ids=[999]))
        self.assertEqual(r['synthese']['inconnues'], 6)
        self.assertEqual(r['synthese']['negatives'], 0)

    def test_snapshot_recent_interdit_hindcast_artificiel(self):
        r = convertir(CSV, self.contrat)
        registre = Registre(tuple(Observation(**o) for o in r['observations']))
        for mode in ('publique', 'locale'):
            resultat = evaluer(registre, '2024-01-01', '2024-06-01', '2026-10-03',
                               ('UCDP_COUNTRY_101',), minimum=1, mode=mode)
            self.assertEqual(resultat['cible'], CIBLE_UCDP)
            self.assertEqual(len(resultat['abstentions']), 6)
            self.assertEqual(resultat['predictions'], [])
            self.assertIsNone(resultat['scores']['frequence_lissee']['brier'])

    def test_roundtrip_jsonl_et_cible_separee(self):
        r = convertir(CSV, self.contrat)
        with tempfile.TemporaryDirectory() as dossier:
            p = Path(dossier) / 'observations.jsonl'
            p.write_text(''.join(json.dumps(o) + '\n' for o in r['observations']))
            registre = importer_jsonl(p)
            self.assertEqual(registre.empreinte(), r['empreinte_registre_sha256'])
        premiere = registre.observations[0]
        with self.assertRaisesRegex(ValueError, 'cibles différentes'):
            Registre((premiere, replace(registre.observations[1], cible=CIBLE)))

    def _muter_csv(self, mutation):
        with CSV.open(newline='', encoding='utf-8') as f:
            lecteur = csv.DictReader(f)
            noms, lignes = lecteur.fieldnames, list(lecteur)
        mutation(lignes)
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / 'test.csv'
            with chemin.open('w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=noms)
                writer.writeheader()
                writer.writerows(lignes)
            return convertir(chemin, self.contrat)

    def test_doublon_contradictoire_refuse(self):
        def modifier(lignes):
            lignes[-1]['best'] = '3'
        with self.assertRaisesRegex(ValueError, 'contradictoires'):
            self._muter_csv(modifier)

    def test_invariants_evenements(self):
        for champ, valeur in (('high', '0'), ('low', '4'), ('best', 'NaN'),
                              ('date_prec', '0'), ('type_of_violence', '4'), ('id', '1.0'),
                              ('date_end', '2024-01-11'), ('date_start', '2024-13-01'),
                              ('country', ''), ('country_id', '-1')):
            def modifier(lignes, champ=champ, valeur=valeur):
                lignes[0][champ] = valeur
            with self.subTest(champ=champ), self.assertRaisesRegex(ValueError, 'Ligne CSV'):
                self._muter_csv(modifier)

    def test_donnees_hors_perimetre_validees(self):
        def modifier(lignes):
            lignes[4]['high'] = 'inconnu'
        with self.assertRaises(ValueError):
            self._muter_csv(modifier)

    def test_entete_invalide(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / 'incorrect.csv'
            for contenu in ('id,country\n1,A\n', 'id,id\n1,1\n', ''):
                chemin.write_text(contenu)
                with self.assertRaisesRegex(ValueError, 'En-tête'):
                    convertir(chemin, self.contrat)

    def test_contrat_refuse_fausse_exhaustivite_et_dates(self):
        for changements in ({'couverture_exhaustive': True}, {'couverture_exhaustive': 'oui'},
                             {'pays_ids': [True]}, {'pays_ids': [101, 101]}, {'pays_ids': []},
                             {'version_source': '25.1'}, {'fin': '2026-01'},
                             {'publication': '2024-01-01'}, {'ingestion': '2025-01-01'},
                             {'nature': 'observee'}, {'preuve_disponibilite': ''}):
            with self.subTest(changements=changements), self.assertRaises(ValueError):
                replace(self.contrat, **changements)

    def test_formats_dates(self):
        self.assertEqual(date_ged('2024-01-10'), date_ged('2024-01-10T00:00:00'))
        for texte in ('2024-01-10 13:00:00', '2024-01-10inconnu', '', '2024-1-10'):
            with self.assertRaises(ValueError):
                date_ged(texte)
