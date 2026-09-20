#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ("mandature", "statut_quo", "austerite", "choc_mondial"):
            executer_scenario(cmd)
        elif cmd in ("comparatif", "compare"):
            comparer_tous_scenarios()
        elif cmd in ("stress", "stress-tests", "--stress-tests"):
            afficher_stress_tests_cli()
        elif cmd in ("thinktanks", "think-tanks", "--think-tanks"):
            afficher_think_tanks_cli()
        elif cmd in ("histoire", "history", "--histoire"):
            afficher_histoire_cli()
        elif cmd in ("societe", "society", "--societe", "--society"):
            afficher_societe_cli()
        elif cmd in ("menu", "interactif", "cli"):
            lancer_menu_interactif()
        elif cmd in ("web", "serveur", "server"):
            from simulateur.web_server import demarrer_serveur_web
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
            demarrer_serveur_web(port=port)
        else:
            print("Usage: python3 main.py [mandature|statut_quo|austerite|choc_mondial|comparatif|--stress-tests|--think-tanks|--histoire|menu|web [port]]")
            sys.exit(1)
    else:
        # Exécution automatique du scénario de mandature avec affichage complet
        print("Lancement de la simulation du Plan de Mandature quinquennal...")
        res = executer_scenario("mandature")
        print("\nSimulation exécutée avec succès !")


if __name__ == "__main__":
    main()
