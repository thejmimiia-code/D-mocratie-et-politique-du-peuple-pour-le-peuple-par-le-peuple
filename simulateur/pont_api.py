"""
simulateur/pont_api.py — Pont HTTP du moteur vers les hébergeurs sans serveur.

Le moteur du simulateur (`simulateur.dashboard.DashboardHandler`) route sur
`self.path` et sert toutes les routes `/api/*` depuis un seul processus. Sur un
hébergeur à fonctions (Vercel), le dépôt n'expose donc qu'**une seule** fonction
d'API, `api/[...path].py`, qui reçoit toutes les URL `/api/...` et les transmet
au moteur telles quelles.

    api/[...path].py  ->  class handler(PontAPI): ...

Une fonction par route (une par fichier de `api/`) dépassait le plafond de
12 fonctions par déploiement de l'offre Hobby de Vercel ; c'est pourquoi les
routes sont réunies ici.

⚠️ Ce fichier est un **ajout du dépôt du site M.R.S.C**, il ne vient pas du
dépôt du simulateur : une mise à jour du moteur ne doit ni l'écraser ni le
supprimer.
"""

from __future__ import annotations

import os

# Sur un hébergeur à fonctions, le dossier du projet est en lecture seule :
# le cache des données publiques part dans /tmp (éphémère, une instance à la
# fois). Le moteur retombe sans cache si l'écriture échoue, mais autant lui
# donner un chemin inscriptible. Ce réglage doit précéder l'import du moteur,
# qui lit la variable à l'initialisation de `simulateur.donnees_live`.
os.environ.setdefault("SIMULATEUR_CACHE", "/tmp/simulateur_cache")

from simulateur.dashboard import DashboardHandler  # noqa: E402


class PontAPI(DashboardHandler):
    """Sert l'ensemble des routes `/api/*` du moteur.

    Aucune réécriture de chemin : le moteur route déjà sur le chemin complet
    (y compris la chaîne de requête). `do_GET`, `do_POST` et `do_HEAD` sont
    hérités tels quels de `DashboardHandler`.
    """
