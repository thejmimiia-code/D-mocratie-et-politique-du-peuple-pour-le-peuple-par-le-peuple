#!/usr/bin/env python3
"""
outils/details_depot.py — prépare et applique les « Edit repository details ».

Le bloc *About* du dépôt (description, site web, sujets) et l'aperçu social ne
sont pas versionnés : ce script les tient à jour à partir du contenu réel du
projet, et tente de les appliquer via l'API GitHub. Si le jeton disponible n'a
pas les droits d'administration du dépôt (l'API répond alors 403), il affiche
le bloc exact à copier dans *Edit repository details*.

    python3 outils/details_depot.py              # état actuel + bloc à copier
    python3 outils/details_depot.py --appliquer  # tente la mise à jour GitHub
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DEPOT = "thejmimiia-code/D-mocratie-et-politique-du-peuple-pour-le-peuple-par-le-peuple"
DEPOT_COURT = "thejmimiia-code/D-mocratie-et-politique-du-peuple"

#: Description du dépôt (limite GitHub : 350 caractères).
DESCRIPTION = (
    "Simulateur macro-politique systémique à 5 échelons (local → européen → mondial → "
    "géopolitique) : 97 leviers croisables, 20 domaines d'impact notés 0-100, données "
    "publiques en direct (Eurostat, BCE, Banque mondiale) et console de veille des seuils "
    "tolérables et hors-sol."
)

#: Sujets GitHub (limite : 20). Ils décrivent ce que fait le dépôt aujourd'hui.
SUJETS = [
    "france",
    "simulation",
    "politiques-publiques",
    "finances-publiques",
    "budget",
    "dette-publique",
    "democratie",
    "geopolitique",
    "open-data",
    "api-publiques",
    "eurostat",
    "banque-mondiale",
    "dashboard",
    "python",
    "modele-systemique",
    "souverainete",
    "politiques-budgetaires",
    "transparence",
    "constitution",
    "economie",
]

#: Le site web déclaré ne répond plus (404 Vercel) : on recommande de le vider
#: et de renvoyer vers la documentation versionnée.
SITE_WEB = ""  # laisser vide : le lien actuel est mort
SITE_WEB_CONSEIL = (
    "https://github.com/thejmimiia-code/D-mocratie-et-politique-du-peuple/blob/main/"
    "docs/SIMULATEUR_PARAMETRABLE.md"
)

APERCU_SOCIAL = RACINE / "docs" / "apercu_social.png"


def bloc_a_copier() -> str:
    """Le bloc exact à coller dans *Edit repository details*."""
    sujets = ", ".join(SUJETS)
    return f"""\
────────────────────────────────────────────────────────────────────────────
EDIT REPOSITORY DETAILS — à coller tel quel
────────────────────────────────────────────────────────────────────────────

Description ({len(DESCRIPTION)} / 350 caractères)
{DESCRIPTION}

Website
(vide — l'ancienne adresse Vercel renvoie 404)
À défaut d'application hébergée, renvoyer vers la documentation :
{SITE_WEB_CONSEIL}

Topics ({len(SUJETS)} / 20)
{sujets}

Social preview
Téléverser l'image : {APERCU_SOCIAL.relative_to(RACINE)}
(1280 × 640, régénérée par `python3 outils/apercu_social.py`)

Réglages recommandés dans la même page
  ☑ Include in the home page … non (projet de recherche, pas de vitrine)
  ☑ Releases : activées (l'application se lance par `python -m simulateur.dashboard`)
  ☑ Packages : inutile pour ce dépôt
────────────────────────────────────────────────────────────────────────────
"""


def _gh(*arguments: str) -> tuple[int, str]:
    gh = shutil.which("gh")
    if gh is None:
        return 127, "gh CLI absent"
    proc = subprocess.run([gh, *arguments], capture_output=True, text=True, cwd=str(RACINE))
    return proc.returncode, (proc.stdout or proc.stderr).strip()


def etat_actuel() -> dict | None:
    """Lit les réglages actuels du dépôt (None si l'API est indisponible)."""
    code, sortie = _gh("api", f"repos/{DEPOT}",
                       "--jq", "{description,homepage,topics,visibility,license:.license.spdx_id}")
    if code != 0:
        print(f"Lecture impossible ({code}) : {sortie[:200]}", file=sys.stderr)
        return None
    try:
        return json.loads(sortie)
    except json.JSONDecodeError:
        print(f"Réponse inattendue : {sortie[:200]}", file=sys.stderr)
        return None


def appliquer() -> int:
    """Tente la mise à jour ; retourne 0 si elle a abouti."""
    # PATCH /repos : description, site web, puis un champ `topics[]` répété par sujet.
    arguments = ["api", "-X", "PATCH", f"repos/{DEPOT}",
                 "-f", f"description={DESCRIPTION}",
                 "-f", f"homepage={SITE_WEB}"]
    for sujet in SUJETS:
        arguments += ["-f", f"topics[]={sujet}"]
    code, sortie = _gh(*arguments)
    if code == 0:
        print("Réglages appliqués par l'API.")
        return 0
    print(f"L'API a refusé la mise à jour ({code}) : {sortie[:200]}")
    print("Le jeton disponible est un jeton d'intégration sans droit d'administration.\n")
    print(bloc_a_copier())
    return 1


def main() -> int:
    analyseur = argparse.ArgumentParser(description="Réglages du dépôt (About, sujets, aperçu)")
    analyseur.add_argument("--appliquer", action="store_true",
                           help="tente la mise à jour via l'API GitHub")
    arguments = analyseur.parse_args()

    etat = etat_actuel()
    if etat:
        print("État actuel :")
        print(f"  description : {etat.get('description')}")
        print(f"  website     : {etat.get('homepage') or '(vide)'}")
        print(f"  topics      : {etat.get('topics') or '(aucun)'}")
        print()
        if etat.get("description") == DESCRIPTION and set(etat.get("topics") or []) == set(SUJETS):
            print("Déjà à jour, rien à faire.")
            return 0
    if arguments.appliquer:
        return appliquer()
    print(bloc_a_copier())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
