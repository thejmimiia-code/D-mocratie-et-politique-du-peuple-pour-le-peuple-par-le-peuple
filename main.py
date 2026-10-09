#!/usr/bin/env python3
"""
Point d'entrée principal du Simulateur Macro-Politique & Démocratique.
Projet : Démocratie et politique, du peuple, pour le peuple, par le peuple.
"""

import sys
from simulateur.cli import (
    executer_scenario,
    lancer_menu_interactif,
    comparer_tous_scenarios,
    afficher_stress_tests_cli,
    afficher_think_tanks_cli,
    afficher_histoire_cli,
    afficher_societe_cli,
)


from simulateur.cli import SCENARIOS_DISPONIBLES, USAGE_SCENARIOS, executer_scenario


def main() -> None:
    usage = f"Usage: python3 main.py [{USAGE_SCENARIOS}] [--export <path.json|csv>]"
    if len(sys.argv) > 1:
        scenario = sys.argv[1].lower()
        if scenario in ("--help", "-h"):
            print(usage)
            return
        if scenario in SCENARIOS_DISPONIBLES:
            export_path = None
            if "--export" in sys.argv:
                idx = sys.argv.index("--export")
                if idx + 1 < len(sys.argv):
                    export_path = sys.argv[idx + 1]
                else:
                    print(usage)
                    sys.exit(1)
            executer_scenario(scenario, export_path=export_path)
        else:
            print(usage)
            sys.exit(1)
    else:
        print("Lancement de la simulation du Plan de Mandature quinquennal...")
        executer_scenario("mandature")
        print("\nSimulation exécutée avec succès !")


if __name__ == "__main__":
    main()
