"""tests/test_cli.py — Tests de l'interface terminale (CLI), des scénarios, de la prospective et de l'innovation."""

from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from simulateur import cli  # noqa: E402


class TestCLICommands(unittest.TestCase):
    """Vérifie l'exécution des commandes CLI sans crash."""

    def test_catalogue_scenarios_complet(self):
        self.assertEqual(len(cli.CATALOGUE_SCENARIOS), 11)
        self.assertIn("mandature", cli.CATALOGUE_SCENARIOS)
        self.assertIn("double_mandature", cli.CATALOGUE_SCENARIOS)
        self.assertIn("resilience", cli.CATALOGUE_SCENARIOS)

    def test_afficher_prospective_cli(self):
        anc = sys.stdout
        try:
            sys.stdout = io.StringIO()
            cli.afficher_prospective_cli(horizon=5)
            sortie = sys.stdout.getvalue()
            self.assertIn("REGISTRE DE PROSPECTIVE", sortie)
            self.assertIn("Horizon 5 ans", sortie)
            self.assertIn("incident_majeur", sortie)
        finally:
            sys.stdout = anc

    def test_afficher_innovation_cli(self):
        anc = sys.stdout
        try:
            sys.stdout = io.StringIO()
            cli.afficher_innovation_cli(horizon=10)
            sortie = sys.stdout.getvalue()
            self.assertIn("RAPPORT R&D, INNOVATION & PROSPECTIVE", sortie)
            self.assertIn("Piliers de Prospective", sortie)
            self.assertIn("Horizon 10 ans", sortie)
        finally:
            sys.stdout = anc

    def test_afficher_stress_tests_cli(self):
        anc = sys.stdout
        try:
            sys.stdout = io.StringIO()
            cli.afficher_stress_tests_cli()
            sortie = sys.stdout.getvalue()
            self.assertIn("AUDIT CONTRADICTOIRE", sortie)
        finally:
            sys.stdout = anc

    def test_afficher_think_tanks_cli(self):
        anc = sys.stdout
        try:
            sys.stdout = io.StringIO()
            cli.afficher_think_tanks_cli()
            sortie = sys.stdout.getvalue()
            self.assertIn("RÉPERTOIRE MONDIAL DES 23 THINK TANKS", sortie)
        finally:
            sys.stdout = anc

    def test_executer_scenario_mandature(self):
        anc = sys.stdout
        try:
            sys.stdout = io.StringIO()
            res = cli.executer_scenario("mandature")
            self.assertEqual(len(res), 5)
            self.assertLess(res[-1].ratio_deficit_pib, 3.0)
        finally:
            sys.stdout = anc


if __name__ == "__main__":
    unittest.main()
