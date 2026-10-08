"""Fonction Vercel unique — toutes les routes `/api/*` du simulateur.

Fichier généré par `outils/generer-fonctions-api.py` : ne pas modifier à la main.

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
