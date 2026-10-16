"""Fonction Vercel unique — 23 routes `/api/*` du simulateur.

Fichier généré par `outils/generer-fonctions-api.py` : ne pas modifier à la main. Une
seule fonction sert 23 routes (`/api/catalogue, /api/contexte, /api/donnees, /api/simuler, /api/comparer`, …) : Vercel n'en compte qu'une, ce qui
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
ROUTES = ("catalogue", "contexte", "donnees", "simuler", "comparer", "presets", "bulles", "bulle", "proxy", "run", "scenarios", "export", "conseil", "lexique", "marches", "garde_fous", "constitution", "contrepouvoirs", "instances", "dynamiques", "objections", "nuances", "prospective",)


class handler(PontAPI):  # noqa: N801 - nom attendu par Vercel
    """Point d'entrée Vercel : hérite du moteur, sans rien redéfinir."""
