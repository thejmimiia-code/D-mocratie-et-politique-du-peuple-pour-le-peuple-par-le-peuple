#!/usr/bin/env python3
"""
Point d'entrée principal du Simulateur Macro-Politique & Démocratique.
Projet : Démocratie et politique, du peuple, pour le peuple, par le peuple.
"""

import sys

from simulateur.cli import executer_scenario


def main() -> None:
    if len(sys.argv) > 1:
        scenario = sys.argv[1].lower()
        if scenario in ("mandature", "statut_quo", "austerite", "choc_mondial"):
            export_path = None
            if "--export" in sys.argv:
                idx = sys.argv.index("--export")
                if idx + 1 < len(sys.argv):
                    export_path = sys.argv[idx + 1]
                else:
                    print("Usage: python3 main.py [mandature|statut_quo|austerite|choc_mondial] [--export <path.json|csv>]")
                    sys.exit(1)
            executer_scenario(scenario, export_path=export_path)
        else:
            print("Usage: python3 main.py [mandature|statut_quo|austerite|choc_mondial] [--export <path.json|csv>]")
            sys.exit(1)
    else:
        print("Lancement de la simulation du Plan de Mandature quinquennal...")
        executer_scenario("mandature")
        print("\nSimulation exécutée avec succès !")


if __name__ == "__main__":
    main()
