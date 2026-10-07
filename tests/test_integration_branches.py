"""Régressions de l'intégration PR #10 / #11 : les deux modèles doivent coexister."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from simulateur import geopolitique, geopolitique_annuelle
from simulateur.cli import CATALOGUE_SCENARIOS
from simulateur.dashboard import run_simulation_api
from simulateur.model import DecisionPolitique
from simulateur.moteur import MoteurSimulationSystemique

ROOT = Path(__file__).resolve().parents[1]


class TestIntegrationBranches(unittest.TestCase):
    def test_compatibilite_import_annuel_et_mensuel(self):
        self.assertIs(geopolitique.EchelonGeopolitique, geopolitique_annuelle.EchelonGeopolitique)
        self.assertIs(geopolitique.propager_geopolitique, geopolitique_annuelle.propager_geopolitique)
        self.assertEqual(geopolitique.CIBLE_OTAN_DEFENSE_PCT, 3.5)
        with self.assertRaises(AttributeError):
            _ = geopolitique.inexistant
        self.assertEqual(len(geopolitique.cas_experimental()['mois']), 36)

    def test_help_cli_retourne_succes(self):
        r = subprocess.run([sys.executable, 'main.py', '--help'], cwd=ROOT,
                           capture_output=True, text=True, check=False)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('convergence_ww3', r.stdout)

    def test_onze_scenarios_cli_exports(self):
        self.assertEqual(len(CATALOGUE_SCENARIOS), 11)
        with tempfile.TemporaryDirectory() as dossier:
            for scenario, (fabrique, _) in CATALOGUE_SCENARIOS.items():
                with self.subTest(scenario=scenario):
                    sortie = Path(dossier) / f'{scenario}.json'
                    r = subprocess.run([sys.executable, 'main.py', scenario, '--export', str(sortie)],
                                       cwd=ROOT, capture_output=True, text=True, check=False)
                    self.assertEqual(r.returncode, 0, r.stderr)
                    data = json.loads(sortie.read_text())
                    self.assertEqual(data['nombre_etapes'], len(fabrique()))
                    self.assertIn('non calibrés', ' '.join(data['resultats'][0]['commentaires']))

    def test_onze_scenarios_api_dashboard(self):
        for scenario, (fabrique, _) in CATALOGUE_SCENARIOS.items():
            with self.subTest(scenario=scenario):
                data = run_simulation_api(scenario)
                self.assertNotIn('error', data)
                self.assertEqual(len(data['resultats']), len(fabrique()))

    def test_facteur_activite_applique_au_budget_annuel(self):
        moteur = MoteurSimulationSystemique()
        r = moteur.appliquer_etape(DecisionPolitique(effort_defense_cible_pct_pib=3.5),
                                  facteur_activite=0.9)
        self.assertAlmostEqual(r.depenses_defense_mde, round(3015 * 0.9 * 0.035, 2))

    def test_extension_eva_neuf_scenarios_bus_simule(self):
        # Vérifie l'adaptateur, pas une connexion réelle à ÉVA.
        bus = types.ModuleType('eva.extensions.bus')
        bus.EventBus = object
        with patch.dict(sys.modules, {'eva.extensions.bus': bus}):
            spec = importlib.util.spec_from_file_location('eva_integration_test', ROOT / 'extension_eva/main.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            extension = module.ExtensionSimulateurPolitique('test')
            for scenario, (fabrique, _) in CATALOGUE_SCENARIOS.items():
                with self.subTest(scenario=scenario):
                    resultats = extension._executer_simulation(scenario)
                    self.assertEqual(len(resultats), len(fabrique()))

    def test_limite_nucleaire_mensuelle_preservee(self):
        r = geopolitique.cas_experimental(emploi_mois=8)
        self.assertEqual(len(r['mois']), 7)
        self.assertEqual(r['macro']['annees'], [])
        self.assertEqual(r['arret']['mois'], 8)
