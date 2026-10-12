#!/usr/bin/env python3
"""Génère les fonctions Vercel de `api/` à partir des routes du simulateur.

Sur Vercel, chaque fichier `.py` de `api/` devient une route (« file-based
Python functions ») et doit exposer une classe `handler` dérivant de
`BaseHTTPRequestHandler` : d'où un fichier par route du moteur, chacun
déclarant sa route à `simulateur.pont_api.FonctionAPI`.

Usage :
    python3 outils/generer-fonctions-api.py [--verifier]

`--verifier` compare les fichiers présents aux routes réellement servies par
`simulateur/dashboard.py` et sort en erreur en cas d'écart (utilisable en CI).
Les fonctions propres au site (voir `FONCTIONS_DU_SITE`, par exemple
`verifier-source`) sont conservées telles quelles.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Set, Tuple

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

#: Fonctions propres au site (pas des routes du moteur) : ni générées, ni signalées.
FONCTIONS_DU_SITE: Tuple[str, ...] = ("verifier-source",)

#: Routes du moteur à exposer (voir `simulateur/dashboard.py`, do_GET/do_POST).
ROUTES: Tuple[str, ...] = (
    "catalogue",
    "contexte",
    "donnees",
    "simuler",
    "comparer",
    "presets",
    "bulles",
    "bulle",
    "proxy",
    "run",
    "scenarios",
    "export",
    "conseil",
    "lexique",
    "marches",
    "garde_fous",
    "constitution",
    "contrepouvoirs",
    "instances",
    "dynamiques",
    "objections",
    "nuances",
)

#: La fonction unique servie par Vercel : un seul fichier `.py` dans `api/`, parce que
#: chaque fichier de ce dossier devient une Serverless Function à lui seul et que l'offre
#: Hobby plafonne à douze fonctions par déploiement. Le pont rétablit le chemin demandé
#: (`/api/<route>?...path=<route>` → `/api/<route>`), voir `simulateur/pont_api.py`.
GABARIT_PONT = '''"""Fonction Vercel unique — {total} routes `/api/*` du simulateur.

Fichier généré par `outils/generer-fonctions-api.py` : ne pas modifier à la main. Une
seule fonction sert {total} routes (`{liste}`, …) : Vercel n'en compte qu'une, ce qui
reste sous le plafond de douze fonctions par déploiement de l'offre Hobby. Le moteur
route lui-même sur le chemin reçu, voir `simulateur/pont_api.py`.
`verifier-source.py` reste une fonction distincte, propre au site.

Vérifié par `outils/generer-fonctions-api.py --verifier`.
"""

import pathlib
import sys

RACINE = pathlib.Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from simulateur.pont_api import PontAPI  # noqa: E402

#: Routes que cette fonction s'engage à servir — relue par les tests.
ROUTES = ({routes},)


class handler(PontAPI):  # noqa: N801 - nom attendu par Vercel
    """Point d'entrée Vercel : hérite du moteur, sans rien redéfinir."""
'''


def routes_du_moteur() -> Set[str]:
    """Routes réellement servies, lues dans le source du moteur."""
    source = (RACINE / "simulateur" / "dashboard.py").read_text(encoding="utf-8")
    return set(re.findall(r'chemin == "(/api/[a-z_]+)"', source))


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analyseur.add_argument("--verifier", action="store_true", help="ne rien écrire, signaler les écarts")
    options = analyseur.parse_args()

    attendues = {f"/api/{route}" for route in ROUTES}
    servies = routes_du_moteur()
    manquantes = sorted(servies - attendues)
    inconnues = sorted(attendues - servies)
    if manquantes or inconnues:
        print("Désaccord entre api/ et le moteur :")
        if manquantes:
            print(f"  routes du moteur non exposées : {', '.join(manquantes)}")
        if inconnues:
            print(f"  routes exposées mais absentes du moteur : {', '.join(inconnues)}")
        return 1

    dossier = RACINE / "api"
    pont = dossier / "[...path].py"
    contenu = GABARIT_PONT.format(
        total=len(ROUTES),
        liste=", ".join(f"/api/{route}" for route in ROUTES[:5]),
        routes=", ".join(f'"{route}"' for route in ROUTES),
    )
    a_retirer = sorted(
        nom for nom in dossier.glob("*.py")
        if nom.stem not in (*ROUTES, *FONCTIONS_DU_SITE, "[...path]")
        or (nom.stem in ROUTES and nom.name != "[...path].py")
    )

    if options.verifier:
        absentes = [nom for nom in FONCTIONS_DU_SITE if not (dossier / f"{nom}.py").is_file()]
        if absentes:
            print(f"Fonctions du site manquantes dans api/ : {', '.join(absentes)}")
            return 1
        if not pont.is_file() or pont.read_text(encoding="utf-8") != contenu:
            print("La fonction Vercel unique est absente ou obsolète : relancer "
                  "`python3 outils/generer-fonctions-api.py`.")
            return 1
        if a_retirer:
            print("Fonctions par route encore présentes (une seule suffit, plafond Vercel) : "
                  + ", ".join(nom.name for nom in a_retirer))
            return 1
        print(f"{len(ROUTES)} routes du moteur servies par la fonction unique api/[...path].py, "
              f"{len(FONCTIONS_DU_SITE)} fonction(s) du site en plus.")
        return 0

    for nom in FONCTIONS_DU_SITE:  # jamais écrasées : elles n'existent pas côté moteur
        if (dossier / f"{nom}.py").is_file():
            print(f"Fonction du site conservée : api/{nom}.py")
    dossier.mkdir(exist_ok=True)
    pont.write_text(contenu, encoding="utf-8")
    for nom in a_retirer:
        nom.unlink()
        print(f"Fonction par route retirée : api/{nom.name}")
    print(f"Fonction Vercel unique écrite : api/[...path].py — {len(ROUTES)} routes du moteur.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
