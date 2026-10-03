"""Régressions de l'audit PR : installation, fichiers, intégrité et arrêt du modèle."""

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

from simulateur.geopolitique import cas_experimental, coupler_macro
from simulateur.import_ucdp import ContratImport, convertir

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests' / 'fixtures'


class TestAuditPR(unittest.TestCase):
    def test_metadata_setuptools(self):
        config = tomllib.loads((ROOT / 'pyproject.toml').read_text())
        self.assertEqual(config['tool']['setuptools']['py-modules'], ['main'])

    def test_arret_interdit_toute_projection_posterieure(self):
        r = cas_experimental()
        r['arret'] = {'mois': 8, 'motif': 'emploi_nucleaire_impose_hors_validite'}
        with self.assertRaisesRegex(ValueError, 'arrêt déclaré'):
            coupler_macro(r)

    def test_rapport_tronque_ou_prolonge_refuse(self):
        original = cas_experimental()
        for mois in (original['mois'][:-1], original['mois'] + [original['mois'][-1]]):
            r = copy.deepcopy(original)
            r['mois'] = mois
            with self.assertRaises(ValueError):
                coupler_macro(r)

    def test_arret_invalide_refuse(self):
        for arret in ({'mois': True, 'motif': 'emploi_nucleaire_impose_hors_validite'},
                      {'mois': 37, 'motif': 'emploi_nucleaire_impose_hors_validite'},
                      {'mois': 8, 'motif': 'inconnu'}):
            r = cas_experimental(emploi_mois=8)
            r['arret'] = arret
            with self.assertRaises(ValueError):
                coupler_macro(r)

    def test_arrets_valides_conservent_annees_completes(self):
        for mois in (1, 8, 13, 25):
            r = cas_experimental(emploi_mois=mois)
            self.assertEqual(len(coupler_macro(r)['annees']), (mois - 1) // 12)

    def test_empreinte_des_octets_exactement_lus(self):
        contrat = ContratImport(**json.loads((FIXTURES / 'contrat_ged_synthetique.json').read_text()))
        contenu = b'\xef\xbb\xbf' + (FIXTURES / 'ged_schema_synthetique.csv').read_bytes().replace(b'\n', b'\r\n')
        with tempfile.TemporaryDirectory() as dossier:
            csv = Path(dossier) / 'source.csv'
            csv.write_bytes(contenu)
            original_open = Path.open
            lectures = []

            def ouvrir(chemin, *args, **kwargs):
                if chemin == csv:
                    lectures.append(args)
                return original_open(chemin, *args, **kwargs)

            with patch.object(Path, 'open', ouvrir):
                r = convertir(csv, contrat)
            self.assertEqual(len(lectures), 1)
            self.assertEqual(r['empreinte_csv_sha256'], hashlib.sha256(contenu).hexdigest())
            self.assertEqual(r['synthese']['positives'], 2)

    def test_validation_cli_preserve_source_et_alias(self):
        with tempfile.TemporaryDirectory() as dossier:
            source = Path(dossier) / 'observations.jsonl'
            contenu = (FIXTURES / 'observations_synthetiques.jsonl').read_bytes()
            source.write_bytes(contenu)
            symbolique = Path(dossier) / 'symbolique.jsonl'
            symbolique.symlink_to(source)
            physique = Path(dossier) / 'physique.jsonl'
            os.link(source, physique)
            for sortie in (source, symbolique, physique):
                r = subprocess.run([
                    sys.executable, '-m', 'simulateur.validation_temporelle',
                    '--observations', str(source), '--sortie', str(sortie),
                    '--debut', '2020-07-01', '--fin', '2021-12-01',
                    '--evaluation-au', '2022-02-01', '--unites', 'FICTIF_A',
                ], cwd=ROOT, capture_output=True, text=True, check=False)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertIn('fichiers distincts', r.stderr)
                self.assertEqual(source.read_bytes(), contenu)

    def test_import_cli_preserve_source_lien_physique(self):
        with tempfile.TemporaryDirectory() as dossier:
            dossier = Path(dossier)
            source, rapport = dossier / 'source.csv', dossier / 'rapport.json'
            contenu = (FIXTURES / 'ged_schema_synthetique.csv').read_bytes()
            source.write_bytes(contenu)
            os.link(source, rapport)
            r = subprocess.run([
                sys.executable, '-m', 'simulateur.import_ucdp', '--csv', str(source),
                '--contrat', str(FIXTURES / 'contrat_ged_synthetique.json'),
                '--sortie', str(dossier / 'resultat.jsonl'), '--rapport', str(rapport),
            ], cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertEqual(source.read_bytes(), contenu)
            self.assertFalse((dossier / 'resultat.jsonl').exists())

    def test_pipeline_cli_import_validation(self):
        with tempfile.TemporaryDirectory() as dossier:
            dossier = Path(dossier)
            observations = dossier / 'observations.jsonl'
            resultat = dossier / 'evaluation.json'
            commandes = [
                ['simulateur.import_ucdp', '--csv', str(FIXTURES / 'ged_schema_synthetique.csv'),
                 '--contrat', str(FIXTURES / 'contrat_ged_synthetique.json'),
                 '--sortie', str(observations), '--rapport', str(dossier / 'import.json')],
                ['simulateur.validation_temporelle', '--observations', str(observations),
                 '--debut', '2024-01-01', '--fin', '2024-06-01', '--evaluation-au', '2026-10-03',
                 '--unites', 'UCDP_COUNTRY_101', '--minimum', '1', '--sortie', str(resultat)],
            ]
            for commande in commandes:
                r = subprocess.run([sys.executable, '-m', *commande], cwd=ROOT,
                                   capture_output=True, text=True, check=False)
                self.assertEqual(r.returncode, 0, r.stderr)
            r = json.loads(resultat.read_text())
            self.assertEqual(len(r['abstentions']), 6)
            self.assertEqual(r['predictions'], [])
            self.assertIsNone(r['scores']['frequence_lissee']['brier'])
