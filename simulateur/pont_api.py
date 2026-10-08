"""
simulateur/pont_api.py — Pont HTTP du moteur vers les hébergeurs sans serveur.

Le moteur du simulateur (`simulateur.dashboard.DashboardHandler`) route sur
`self.path` et sert toutes les routes `/api/*` depuis un seul processus. Sur un
hébergeur à fonctions (Vercel), le dépôt n'expose donc qu'**une seule** fonction
d'API, `api/[...path].py`, qui reçoit les URL `/api/...` et les transmet au moteur.

    api/[...path].py  ->  class handler(PontAPI): ...

Une fonction par route (une par fichier de `api/`) dépassait le plafond de
12 fonctions par déploiement de l'offre Hobby de Vercel ; c'est pourquoi les
routes sont réunies ici.

Chemin reçu : le moteur attend `/api/<route>?…`. La fonction attrape-tout reçoit
ce chemin tel quel ; si Vercel lui transmettait à la place la destination de la
réécriture (`/api/[...path]?...path=<route>&…`), `chemin_demande` rétablit le
chemin demandé à partir des segments capturés. Ce repli n'agit que sur cette
forme précise : toute autre cible de requête passe inchangée.

⚠️ Ce fichier est un **ajout du dépôt du site M.R.S.C**, il ne vient pas du
dépôt du simulateur : une mise à jour du moteur ne doit ni l'écraser ni le
supprimer.
"""

from __future__ import annotations

import os
from urllib.parse import quote, unquote

# Sur un hébergeur à fonctions, le dossier du projet est en lecture seule :
# le cache des données publiques part dans /tmp (éphémère, une instance à la
# fois). Le moteur retombe sans cache si l'écriture échoue, mais autant lui
# donner un chemin inscriptible. Ce réglage doit précéder l'import du moteur,
# qui lit la variable à l'initialisation de `simulateur.donnees_live`.
os.environ.setdefault("SIMULATEUR_CACHE", "/tmp/simulateur_cache")

from simulateur.dashboard import DashboardHandler  # noqa: E402

#: Destination de la réécriture de la fonction attrape-tout, telle que Vercel
#: peut la transmettre à la place de l'URL demandée.
CHEMIN_DESTINATION = "/api/[...path]"
#: Clé de requête où Vercel dépose les segments capturés par `[...path]`.
CLE_SEGMENTS = "...path"


def chemin_demande(chemin_recu: str) -> str:
    """Rend à la cible de requête `chemin_recu` la forme `/api/<route>?…`.

    `chemin_recu` contient le chemin et la chaîne de requête. Elle est renvoyée
    telle quelle, sauf si elle désigne la destination de la réécriture :

        /api/[...path]?...path=catalogue&x=1   ->   /api/catalogue?x=1
    """
    chemin, _, requete = chemin_recu.partition("?")
    if unquote(chemin) != CHEMIN_DESTINATION:
        return chemin_recu
    segments: str | None = None
    restants: list[str] = []
    for morceau in filter(None, requete.split("&")):
        cle, _, valeur = morceau.partition("=")
        if segments is None and unquote(cle) == CLE_SEGMENTS:
            segments = unquote(valeur)
        else:
            restants.append(morceau)
    if segments is None:
        return chemin_recu
    route = "/api/" + quote(segments.strip("/"), safe="/")
    return route + ("?" + "&".join(restants) if restants else "")


class PontAPI(DashboardHandler):
    """Sert l'ensemble des routes `/api/*` du moteur.

    La cible de requête est ramenée à `/api/<route>?…` par `chemin_demande`,
    puis `do_GET`, `do_POST` et `do_HEAD` sont ceux du moteur.
    """

    def do_GET(self) -> None:  # noqa: N802 - API stdlib
        self._deleguer("GET")

    def do_POST(self) -> None:  # noqa: N802 - API stdlib
        self._deleguer("POST")

    def do_HEAD(self) -> None:  # noqa: N802 - API stdlib
        self._deleguer("HEAD")

    def _deleguer(self, methode: str) -> None:
        # Idempotent : do_HEAD rappelle self.do_GET(), qui repasse ici.
        self.path = chemin_demande(self.path)
        if methode == "GET":
            DashboardHandler.do_GET(self)
        elif methode == "POST":
            DashboardHandler.do_POST(self)
        else:
            DashboardHandler.do_HEAD(self)
