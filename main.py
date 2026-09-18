#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Point d'entrée principal du Simulateur Macro-Politique & Démocratique.
Projet : Démocratie et politique, du peuple, pour le peuple, par le peuple.
"""

import sys
from simulateur.cli import executer_scenario, lancer_menu_interactif

def main():
    if len(sys.argv) > 1:
        scenario = sys.argv[1].lower()
        if scenario in ("mandature", "statut_quo", "austerite"):
            executer_scenario(scenario)
        else:
            print("Usage: python3 main.py [mandature|statut_quo|austerite]")
            sys.exit(1)
    else:
        # Exécution automatique du scénario de mandature avec affichage complet
        print("Lancement de la simulation du Plan de Mandature quinquennal...")
        res = executer_scenario("mandature")
        print("\nSimulation exécutée avec succès !")


if __name__ == "__main__":
    main()
