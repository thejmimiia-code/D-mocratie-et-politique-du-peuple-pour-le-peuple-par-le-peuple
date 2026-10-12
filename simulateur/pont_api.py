"""
simulateur/pont_api.py — Pont HTTP du moteur vers les hébergeurs sans serveur.

Le moteur du simulateur (`simulateur.dashboard.DashboardHandler`) route sur
`self.path` et sert toutes les routes depuis un seul processus. Sur un
hébergeur à fonctions (Vercel), chaque fichier de `api/` devient une route
distincte et reçoit l'URL complète de la requête : il faut donc réécrire le
chemin reçu sur la route déclarée, en conservant la chaîne de requête.

    api/catalogue.py  ->  class handler(FonctionAPI): ROUTE = "/api/catalogue"
    api/[...path].py  ->  class handler(PontAPI): sert toutes les routes à la fois

La seconde forme est celle du dépôt : `PontAPI` laisse le moteur router lui-même et
ne rétablit que le chemin que Vercel a déplacé dans la chaîne de requête. Une seule
fonction, parce que l'offre Hobby plafonne le nombre de fonctions par déploiement.

⚠️ Ce fichier est un **ajout du dépôt du site M.R.S.C**, il ne vient pas du
dépôt du simulateur : `outils/mettre-a-jour-simulateur.py` ne doit ni
l'écraser ni le supprimer lors d'une mise à jour du moteur.
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


class FonctionAPI(DashboardHandler):
    """Sert une route unique du moteur, quel que soit le chemin reçu."""

    #: Route servie, par exemple « /api/catalogue » (défini par la sous-classe).
    ROUTE = ""

    def do_GET(self) -> None:  # noqa: N802 - API stdlib
        self._deleguer("GET")

    def do_POST(self) -> None:  # noqa: N802 - API stdlib
        self._deleguer("POST")

    def do_HEAD(self) -> None:  # noqa: N802 - API stdlib
        self._deleguer("HEAD")

    def _deleguer(self, methode: str) -> None:
        if not self.ROUTE:
            raise RuntimeError("La sous-classe doit définir ROUTE (ex. « /api/catalogue »).")
        requete = self.path.split("?", 1)
        # Idempotent : do_HEAD rappelle self.do_GET(), qui repasse ici.
        self.path = self.ROUTE + (("?" + requete[1]) if len(requete) > 1 else "")
        if methode == "GET":
            DashboardHandler.do_GET(self)
        elif methode == "POST":
            DashboardHandler.do_POST(self)
        else:
            DashboardHandler.do_HEAD(self)


def chemin_de_pont(chemin_recu: str) -> str:
    """
    Rétablit le chemin que le moteur sait servir.

    Vercel envoie `/api/simuler?horizon=5` sur `api/[...path].py` avec le chemin
    d'origine passé dans la chaîne de requête (`?...path=simuler`, parfois
    `?path=simuler` ou déjà préfixé). Le pont remet les deux morceaux ensemble ;
    si le chemin est déjà correct, il est rendu tel quel (fonctionnement local).
    """
    from urllib.parse import parse_qs, urlencode, urlparse

    cles = ("...path", "..path", ".path", "path")
    analyse = urlparse(chemin_recu or "/")
    parametres = parse_qs(analyse.query, keep_blank_values=True)
    if not any(cle in parametres for cle in cles):
        return chemin_recu or "/"          # chemin déjà correct : rien à rétablir
    deplace = (parametres.get("...path") or parametres.get("path") or [""])[0].strip()
    reste = {cle: valeurs for cle, valeurs in parametres.items() if cle not in cles}
    suite = f"?{urlencode(reste, doseq=True)}" if reste else ""
    if not deplace or deplace in {"index", "index.py", "[...path]", "[...path].py"}:
        return "/" + suite                 # la racine, c'est la page du simulateur
    route = deplace.lstrip("/")
    if route.endswith(".py"):
        route = route[:-3]
    if route.startswith("api/"):
        route = f"/{route}"
    elif not route.startswith("/"):
        route = f"/api/{route}"
    return route + suite


class PontAPI(DashboardHandler):
    """Sert toutes les routes du moteur depuis une seule fonction sans serveur.

    Aucune logique n'est redéfinie : le routeur du moteur (`DashboardHandler`)
    garde la main sur le chemin, le pont ne fait que le reconstituer quand
    l'hébergeur l'a déplacé dans la chaîne de requête.
    """

    def do_GET(self) -> None:  # noqa: N802 - API stdlib
        self._deleguer("GET")

    def do_POST(self) -> None:  # noqa: N802 - API stdlib
        self._deleguer("POST")

    def do_HEAD(self) -> None:  # noqa: N802 - API stdlib
        self._deleguer("HEAD")

    def _deleguer(self, methode: str) -> None:
        # Idempotent : do_HEAD rappelle self.do_GET(), qui repasse ici.
        retabli = chemin_de_pont(self.path)
        if retabli != self.path:
            self.path = retabli
        if methode == "POST":
            DashboardHandler.do_POST(self)
        elif methode == "HEAD":
            DashboardHandler.do_HEAD(self)
        else:
            DashboardHandler.do_GET(self)
