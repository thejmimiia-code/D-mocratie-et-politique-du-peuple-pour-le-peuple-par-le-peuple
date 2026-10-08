#!/usr/bin/env python3
"""Génère la fonction Vercel de `api/` et vérifie son contrat.

Sur Vercel, chaque fichier `.py` de `api/` est une fonction, et l'offre Hobby
plafonne un déploiement à 12 fonctions. Toutes les routes `/api/*` du moteur sont
donc servies par **une seule** fonction attrape-tout, `api/[...path].py`, qui
hérite de `simulateur.pont_api.PontAPI`.

Usage :
    python3 outils/generer-fonctions-api.py              écrit la fonction attrape-tout
    python3 outils/generer-fonctions-api.py --verifier   ne modifie rien, échoue si le contrat ne tient pas

Un fichier de `api/` n'est supprimé que s'il porte la marque de génération de ce
script (ancienne fonction par route). Un fichier inconnu fait échouer la
génération, sans rien modifier. Les fonctions propres au site (voir
`FONCTIONS_DU_SITE`, par exemple `verifier-source`) ne sont jamais touchées.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

#: Fonctions propres au site (pas des routes du moteur) : jamais générées ni supprimées.
FONCTIONS_DU_SITE: tuple[str, ...] = ("verifier-source",)

#: Fonction attrape-tout : elle sert toutes les routes du moteur.
FONCTION_ATTRAPE_TOUT = "[...path].py"

#: Marque présente dans tout fichier produit par ce script.
MARQUE_GENERATION = "Fichier généré par `outils/generer-fonctions-api.py`"

#: Plafond de fonctions par déploiement, offre Hobby de Vercel.
PLAFOND_FONCTIONS = 12

GABARIT_ATTRAPE_TOUT = '''"""Fonction Vercel unique — toutes les routes `/api/*` du simulateur.

{marque} : ne pas modifier à la main.

Un seul fichier sert les routes du moteur (`/api/bulle`, `/api/simuler`, …) :
Vercel n'en compte qu'une, ce qui reste sous le plafond de 12 fonctions par
déploiement de l'offre Hobby. Le moteur route lui-même sur le chemin reçu, voir
`simulateur/pont_api.py`. `verifier-source.py` reste une fonction distincte.
"""

import pathlib
import sys

RACINE = pathlib.Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from simulateur.pont_api import PontAPI  # noqa: E402


class handler(PontAPI):  # noqa: N801 - nom attendu par Vercel
    """Point d'entrée Vercel : hérite du moteur, sans rien redéfinir."""
'''.replace("{marque}", MARQUE_GENERATION)


def routes_du_moteur() -> set[str]:
    """Routes réellement servies, lues dans le source du moteur."""
    source = (RACINE / "simulateur" / "dashboard.py").read_text(encoding="utf-8")
    # `[a-z_]+` et non `[a-z]+` : sans le souligné, `/api/garde_fous` restait
    # invisible pour cette vérification — donc jamais signalée comme manquante.
    return set(re.findall(r'chemin == "(/api/[a-z_]+)"', source))


def est_genere(fichier: Path) -> bool:
    """Le fichier porte la marque de génération de ce script."""
    try:
        return MARQUE_GENERATION in fichier.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False


def analyser(dossier: Path) -> tuple[list[Path], list[Path], list[str]]:
    """Classe les fichiers de `api/` : (inconnus, générés obsolètes, fonctions du site absentes)."""
    fichiers = sorted(dossier.glob("*.py")) if dossier.is_dir() else []
    inconnus: list[Path] = []
    obsoletes: list[Path] = []
    for fichier in fichiers:
        if fichier.name == FONCTION_ATTRAPE_TOUT or fichier.stem in FONCTIONS_DU_SITE:
            continue
        (obsoletes if est_genere(fichier) else inconnus).append(fichier)
    absentes = [
        nom for nom in FONCTIONS_DU_SITE if not (dossier / f"{nom}.py").is_file()
    ]
    return inconnus, obsoletes, absentes


def verifier(dossier: Path, routes: set[str]) -> int:
    """Contrôle sans rien écrire : code 0 si le contrat tient, 1 sinon."""
    erreurs: list[str] = []
    if not dossier.is_dir():
        erreurs.append("le dossier api/ est absent")
    inconnus, obsoletes, absentes = analyser(dossier)
    if inconnus:
        erreurs.append(f"fichiers inconnus dans api/ : {', '.join(f.name for f in inconnus)}")
    if obsoletes:
        erreurs.append(
            "fonctions générées route par route encore présentes : "
            f"{', '.join(f.name for f in obsoletes)} (lancer sans --verifier)"
        )
    if absentes:
        erreurs.append(f"fonctions du site absentes : {', '.join(absentes)}")
    attrape_tout = dossier / FONCTION_ATTRAPE_TOUT
    if not attrape_tout.is_file():
        erreurs.append(f"api/{FONCTION_ATTRAPE_TOUT} absent (lancer sans --verifier)")
    elif attrape_tout.read_text(encoding="utf-8") != GABARIT_ATTRAPE_TOUT:
        erreurs.append(
            f"api/{FONCTION_ATTRAPE_TOUT} ne correspond pas au gabarit (lancer sans --verifier)"
        )
    nombre = len(list(dossier.glob("*.py"))) if dossier.is_dir() else 0
    if nombre > PLAFOND_FONCTIONS:
        erreurs.append(f"{nombre} fonctions dans api/, plafond {PLAFOND_FONCTIONS}")
    if erreurs:
        print("Contrat api/ non respecté :", file=sys.stderr)
        for erreur in erreurs:
            print(f"  {erreur}", file=sys.stderr)
        return 1
    print(
        f"1 fonction attrape-tout sert les {len(routes)} routes du moteur : "
        f"{nombre} fonction(s) dans api/, plafond {PLAFOND_FONCTIONS}."
    )
    return 0


def generer(dossier: Path, routes: set[str]) -> int:
    """Écrit la fonction attrape-tout et retire les anciennes fonctions générées."""
    inconnus, obsoletes, absentes = analyser(dossier)
    if inconnus or absentes:
        # Refus avant toute écriture : rien n'est créé ni supprimé.
        if inconnus:
            print(
                "Fichiers inconnus dans api/ (ni générés par ce script, ni propres au site) : "
                f"{', '.join(f.name for f in inconnus)}. Rien n'a été modifié.",
                file=sys.stderr,
            )
        if absentes:
            print(
                f"Fonctions du site absentes de api/ : {', '.join(absentes)}. "
                "Rien n'a été modifié.",
                file=sys.stderr,
            )
        return 1
    dossier.mkdir(exist_ok=True)
    for ancienne in obsoletes:
        ancienne.unlink()
    (dossier / FONCTION_ATTRAPE_TOUT).write_text(GABARIT_ATTRAPE_TOUT, encoding="utf-8")
    retirees = ", ".join(f.name for f in obsoletes) or "aucune"
    print(
        f"api/{FONCTION_ATTRAPE_TOUT} écrite : sert les {len(routes)} routes du moteur. "
        f"Anciennes fonctions supprimées : {retirees}. "
        f"Fonctions du site conservées : {', '.join(f'{nom}.py' for nom in FONCTIONS_DU_SITE)}."
    )
    return 0


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analyseur.add_argument(
        "--verifier",
        action="store_true",
        help="ne rien écrire : signaler les écarts et échouer en cas de non-conformité",
    )
    options = analyseur.parse_args()

    routes = routes_du_moteur()
    if not routes:
        print("Aucune route /api/ trouvée dans simulateur/dashboard.py.", file=sys.stderr)
        return 1
    dossier = RACINE / "api"
    if options.verifier:
        return verifier(dossier, routes)
    return generer(dossier, routes)


if __name__ == "__main__":
    raise SystemExit(main())
