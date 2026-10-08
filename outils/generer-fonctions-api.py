#!/usr/bin/env python3
"""Vérifie les fonctions Vercel de `api/` au regard des routes du moteur.

Sur Vercel, chaque fichier `.py` de `api/` est une fonction, et l'offre Hobby
plafonne un déploiement à 12 fonctions. Toutes les routes `/api/*` du moteur
sont donc servies par **une seule** fonction attrape-tout, `api/[...path].py`,
qui hérite de `simulateur.pont_api.PontAPI`. Ce script ne génère plus rien : il
vérifie que ce contrat tient.

Usage :
    python3 outils/generer-fonctions-api.py [--verifier]

Échoue (code 1) si la fonction attrape-tout manque, si `api/` contient un
fichier inattendu, ou si le nombre de fonctions dépasse le plafond. Les
fonctions propres au site (voir `FONCTIONS_DU_SITE`) sont tolérées.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

#: Fonctions propres au site (pas des routes du moteur).
FONCTIONS_DU_SITE: tuple[str, ...] = ("verifier-source",)

#: Fonction attrape-tout qui sert toutes les routes du moteur.
FONCTION_ATTRAPE_TOUT = "[...path].py"

#: Plafond de fonctions par déploiement, offre Hobby de Vercel.
PLAFOND_FONCTIONS = 12


def routes_du_moteur() -> set[str]:
    """Routes réellement servies, lues dans le source du moteur."""
    source = (RACINE / "simulateur" / "dashboard.py").read_text(encoding="utf-8")
    # `[a-z_]+` et non `[a-z]+` : sans le souligné, `/api/garde_fous` restait
    # invisible pour cette vérification — donc jamais signalée comme manquante.
    return set(re.findall(r'chemin == "(/api/[a-z_]+)"', source))


def fonction_attrape_tout_valide(dossier: Path) -> bool:
    """La fonction attrape-tout existe et hérite bien du pont du moteur."""
    fichier = dossier / FONCTION_ATTRAPE_TOUT
    if not fichier.is_file():
        return False
    texte = fichier.read_text(encoding="utf-8")
    return "from simulateur.pont_api import PontAPI" in texte and "class handler(PontAPI)" in texte


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analyseur.add_argument(
        "--verifier", action="store_true", help="ne rien écrire (comportement par défaut)"
    )
    analyseur.parse_args()

    dossier = RACINE / "api"
    routes = routes_du_moteur()
    fonctions = sorted(nom.name for nom in dossier.glob("*.py"))
    fichiers_attendus = {FONCTION_ATTRAPE_TOUT, *(f"{nom}.py" for nom in FONCTIONS_DU_SITE)}

    erreurs: list[str] = []
    if len(routes) != 16:
        erreurs.append(f"le moteur sert {len(routes)} routes /api/ (16 attendues) : vérifier dashboard.py")
    if not fonction_attrape_tout_valide(dossier):
        erreurs.append(f"api/{FONCTION_ATTRAPE_TOUT} absent ou ne dérive pas de PontAPI")
    for nom in fonctions:
        if nom not in fichiers_attendus:
            erreurs.append(f"fichier inattendu dans api/ : {nom}")
    if len(fonctions) > PLAFOND_FONCTIONS:
        erreurs.append(f"{len(fonctions)} fonctions dans api/, plafond {PLAFOND_FONCTIONS}")

    if erreurs:
        print("Contrat api/ non respecté :", file=sys.stderr)
        for erreur in erreurs:
            print(f"  {erreur}", file=sys.stderr)
        return 1

    print(
        f"1 fonction attrape-tout sert les {len(routes)} routes du moteur : "
        f"{len(fonctions)} fonction(s) dans api/, plafond {PLAFOND_FONCTIONS}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
