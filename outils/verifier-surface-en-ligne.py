#!/usr/bin/env python3
"""Vérifie, en ligne, que tout ce qui est publié répond vraiment.

La suite de tests s'arrête au bord du réseau : elle contrôle ce que le dépôt
contient, jamais ce que les hébergeurs servent. C'est pourtant là que se logent
les pannes silencieuses — un fichier présent mais jamais déployé, une route
ajoutée au moteur et absente des fonctions serverless, une réécriture
d'hébergeur qui avale un chemin, une adresse canonique qui pointe vers un hôte
disparu. Rien de tout cela ne se voit dans un dépôt vert.

Deux adresses sont interrogées, parce qu'elles ne servent pas les fichiers de la
même façon : l'adresse canonique est servie par Vercel, qui publie le dépôt tel
quel ; la copie de secours est servie par Render, qui exécute le serveur Python
et fabrique les mêmes textes depuis `surface_publique.py`. Le contrôle le plus
fort possible est donc une **comparaison au caractère** : le texte servi doit
être égal à celui engendré ici, et l'image servie égale au fichier versionné.
Comparer à une photographie ne dirait rien des jours suivants.

    python3 outils/verifier-surface-en-ligne.py                  # les deux hôtes
    python3 outils/verifier-surface-en-ligne.py --hote secours   # un seul
    python3 outils/verifier-surface-en-ligne.py --essais 5       # insister

La copie de secours s'endort quand personne ne l'appelle : ses relances sont
donc normales, et le script le dit au lieu de crier à la panne. Le réseau est la
seule dépendance du script, et son absence est un échec — pas un silence : une
veille qui ne dit rien quand elle n'a rien pu vérifier ne sert à rien.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:      # le script se lance depuis n'importe où
    sys.path.insert(0, str(RACINE))

from simulateur import surface_publique as surface  # noqa: E402

#: Les adresses publiées. Elles ne bougent pas selon l'environnement : c'est le
#: réseau qu'on interroge, pas la configuration de la machine qui exécute.
HOTES = {
    "canonique": surface.URL_CANONIQUE_PAR_DEFAUT.rstrip("/"),
    "secours": surface.HOTE_SECOURS.rstrip("/"),
}

#: Routes servies en GET, interrogées sans paramètre. Une route du serveur qui
#: manquerait ici ferait échouer `tests/test_surface_en_ligne.py` : la veille ne
#: peut pas prendre du retard sur le moteur sans que la suite le dise.
ROUTES_GET = (
    "/api/catalogue",
    "/api/contexte",
    "/api/marches",
    "/api/simuler",
    "/api/comparer",
    "/api/garde_fous",
    "/api/bulles",
    "/api/lexique",
    "/api/constitution",
    "/api/contrepouvoirs",
    "/api/instances",
    "/api/dynamiques",
    "/api/nuances",
    "/api/objections",
    "/api/presets",
    "/api/scenarios",
)

#: Routes qui n'ont de sens qu'avec une question précise : on les interroge
#: avec l'exemple que la page utilise elle-même.
ROUTES_GET_AVEC_PARAMETRES = (
    "/api/run?scenario=mandature",
    "/api/bulle?levier=tva_taux_normal",
)

#: Routes POST — celles que l'interface appelle en direct, curseur en main.
#: Chacune est interrogée avec un corps minimal mais réel : une route qui
#: répond 500 sur son cas le plus simple n'est pas « accessible ». `/api/simuler`
#: est la plus importante de toutes : c'est le calcul que la page demande à
#: chaque mouvement de curseur.
ROUTES_POST = (
    ("/api/simuler", {"parametres": {}, "horizon": 3, "avec_impacts": False}),
    ("/api/donnees", {"lectures": {}}),
    ("/api/conseil", {"cle": "tva_taux_normal", "avant": 20.0, "apres": 21.0}),
    ("/api/nuances", {"parametres": {}}),
)

#: Routes écartées de la veille, et pourquoi — écrit ici pour qu'un ajout ne se
#: perde pas dans un silence. `/api/proxy` est interrogée autrement : sans
#: cible, elle doit **refuser**, et c'est la preuve qu'elle ne va pas chercher
#: n'importe quoi sur le réseau.
ROUTES_ECARTEES = {
    "/api/proxy": "dépend d'un service tiers ; sondée plus bas par son refus.",
    "/api/export": "écrit puis efface un fichier temporaire côté serveur.",
}

#: Le type de contenu attendu de chaque image, sans quoi un 200 ne veut rien
#: dire : un hébergeur qui renvoie du HTML à la place d'un PNG casse l'aperçu
#: de partage sans changer un seul code de statut.
TYPES_IMAGES = {
    "/favicon.svg": ("image/svg+xml",),
    "/favicon.ico": ("image/x-icon", "image/vnd.microsoft.icon", "image/ico"),
    "/apple-touch-icon.png": ("image/png",),
    "/og-image.png": ("image/png",),
}

#: Marque de la page d'attente de la copie de secours : elle répond 200 en
#: racontant qu'elle démarre. Confondre cela avec un succès rendrait la veille
#: complice du silence.
MARQUE_DEMARRAGE = "Application loading"

MINIMUM_TEXTE_LONG = 10_000     # `llms-full.txt` : un extrait tronqué se voit ici


class Reponse:
    """Ce qu'un hôte a répondu, sans le confondre avec ce qu'on espérait."""

    def __init__(self, statut: int, type_contenu: str, corps: bytes) -> None:
        self.statut = statut
        self.type_contenu = type_contenu
        self.corps = corps

    @property
    def texte(self) -> str:
        return self.corps.decode("utf-8", "replace")

    @property
    def en_demarrage(self) -> bool:
        return MARQUE_DEMARRAGE in self.texte or (
            self.type_contenu.startswith("text/html") and self.statut != 200
        )


def _demander(url: str, methode: str = "GET", corps: dict[str, object] | None = None,
              delai: float = 30.0) -> Reponse:
    """Un aller-retour, avec un corps de réponse plafonné.

    La lecture est plafonnée parce que certaines routes publiques renvoient
    plusieurs mégaoctets : la veille vérifie qu'elles répondent, pas qu'elles
    tiennent dans une fenêtre.
    """
    donnees = json.dumps(corps).encode("utf-8") if corps is not None else None
    requete = urllib.request.Request(url, data=donnees, method=methode)
    if donnees is not None:
        requete.add_header("Content-Type", "application/json")
    requete.add_header("Accept", "*/*")
    try:
        with urllib.request.urlopen(requete, timeout=delai) as reponse:
            return Reponse(reponse.status, reponse.headers.get("Content-Type", ""),
                           reponse.read(4_000_000))
    except urllib.error.HTTPError as erreur:
        return Reponse(erreur.code, erreur.headers.get("Content-Type", "") if erreur.headers else "",
                       erreur.read(200_000))
    except (urllib.error.URLError, TimeoutError, OSError) as erreur:
        raise SystemExit(f"Réseau injoignable pour {url} : {erreur}") from erreur


def _insister(url: str, methode: str = "GET", corps: dict[str, object] | None = None,
              essais: int = 3, attente: float = 15.0, delai: float = 30.0,
              journal: list[str] | None = None) -> Reponse:
    """Interroge, en laissant à un hôte endormi le temps de se réveiller."""
    derniere: Reponse | None = None
    for essai in range(1, essais + 1):
        reponse = _demander(url, methode, corps, delai)
        if not reponse.en_demarrage or essai == essais:
            return reponse
        derniere = reponse
        if journal is not None:
            journal.append(f"endormi, relance {essai}/{essais - 1} dans {attente:g} s")
        time.sleep(attente)
    assert derniere is not None
    return derniere


class Verdict:
    """Une épreuve : ce qu'on attendait, ce qui est arrivé, et si ça tient."""

    def __init__(self, hote: str, cible: str, attendu: str) -> None:
        self.hote = hote
        self.cible = cible
        self.attendu = attendu
        self.reussi = False
        self.detail = ""
        self.statut = 0

    def conclure(self, reussi: bool, detail: str, statut: int = 0) -> Verdict:
        self.reussi, self.detail, self.statut = reussi, detail, statut
        return self

    def ligne(self) -> str:
        marque = "✓" if self.reussi else "✗"
        statut = str(self.statut) if self.statut else "—"
        return (f"  {marque} {self.hote:<10} {self.cible:<28} {statut:>4}  "
                f"{self.detail}")


def _epreuve_texte(hote: str, base: str, chemin: str, essais: int,
                   attente: float) -> Verdict:
    """Le texte servi doit être **le même** que celui que le code engendre."""
    verdict = Verdict(hote, chemin, "texte identique à celui engendré")
    attendu = surface.texte(chemin)
    if attendu is None:
        return verdict.conclure(False, "chemin absent de la surface publique")
    reponse = _insister(base + chemin, essais=essais, attente=attente)
    if reponse.statut != 200:
        return verdict.conclure(False, f"attendu 200, reçu {reponse.statut}", reponse.statut)
    servi = reponse.texte
    if servi != attendu:
        ou = next((n for n, (a, b) in enumerate(zip(attendu, servi, strict=False), 1) if a != b),
                  min(len(attendu), len(servi)) + 1)
        return verdict.conclure(
            False, f"différent du texte engendré (1ᵉʳ écart au caractère {ou})",
            reponse.statut)
    if chemin == "/llms-full.txt" and len(servi) < MINIMUM_TEXTE_LONG:
        return verdict.conclure(False, f"tronqué : {len(servi)} caractères", reponse.statut)
    return verdict.conclure(
        True, f"{len(servi)} caractères, identique à celui engendré", reponse.statut)


def _epreuve_image(hote: str, base: str, chemin: str, essais: int, attente: float) -> Verdict:
    """L'image servie doit être **le fichier versionné**, au type annoncé."""
    verdict = Verdict(hote, chemin, "fichier identique au fichier versionné")
    fichier = surface.chemin_image(chemin)
    if fichier is None:
        return verdict.conclure(False, "chemin absent de la surface publique")
    reponse = _insister(base + chemin, essais=essais, attente=attente)
    if reponse.statut != 200:
        return verdict.conclure(False, f"attendu 200, reçu {reponse.statut}", reponse.statut)
    type_attendu = TYPES_IMAGES.get(chemin, ())
    if type_attendu and not any(reponse.type_contenu.startswith(t) for t in type_attendu):
        return verdict.conclure(
            False, f"type inattendu : {reponse.type_contenu or 'aucun'}", reponse.statut)
    if reponse.corps != fichier.read_bytes():
        return verdict.conclure(
            False, f"différent du fichier versionné ({len(reponse.corps)} o servis)", reponse.statut)
    return verdict.conclure(
        True, f"{len(reponse.corps)} octets, identique au fichier versionné", reponse.statut)


def _epreuve_page(hote: str, base: str, essais: int, attente: float) -> Verdict:
    """La page doit dire d'elle-même ce que la surface publique annonce."""
    verdict = Verdict(hote, "/", "page complète et déclarée")
    reponse = _insister(base + "/", essais=essais, attente=attente, delai=60.0)
    if reponse.statut != 200 or not reponse.type_contenu.startswith("text/html"):
        return verdict.conclure(
            False, f"attendu 200 en text/html, reçu {reponse.statut} {reponse.type_contenu}",
            reponse.statut)
    page = reponse.texte
    attendus = {
        f'rel="canonical" href="{surface.URL_CANONIQUE}"': "adresse canonique",
        'name="description"': "description",
        f'property="og:image" content="{surface.URL_CANONIQUE}{surface.IMAGE_APERCU}"':
            "aperçu de partage",
        '"@type": "WebApplication"': "données structurées",
        'name="robots"': "directives d'indexation",
    }
    manquants = [libelle for motif, libelle in attendus.items() if motif not in page]
    if manquants:
        return verdict.conclure(False, "absents : " + ", ".join(manquants), reponse.statut)
    return verdict.conclure(
        True, f"{len(page)} caractères, canonique {surface.URL_CANONIQUE}", reponse.statut)


def _epreuve_json(hote: str, base: str, cible: str, essais: int, attente: float,
                  corps: dict[str, object] | None = None) -> Verdict:
    """Une route d'API doit répondre 200 **et** un JSON exploitable."""
    methode = "POST" if corps is not None else "GET"
    verdict = Verdict(hote, cible, f"{methode} 200 en JSON")
    reponse = _insister(base + cible, methode=methode, corps=corps, essais=essais,
                        attente=attente, delai=120.0)
    if reponse.statut != 200:
        return verdict.conclure(False, f"attendu 200, reçu {reponse.statut}", reponse.statut)
    if not reponse.type_contenu.startswith("application/json"):
        return verdict.conclure(
            False, f"type inattendu : {reponse.type_contenu or 'aucun'}", reponse.statut)
    try:
        charge = json.loads(reponse.texte)
    except json.JSONDecodeError as erreur:
        return verdict.conclure(False, f"JSON illisible : {erreur}", reponse.statut)
    if isinstance(charge, dict) and set(charge) == {"error"}:
        return verdict.conclure(False, f"le serveur répond une erreur : {charge['error']}",
                                reponse.statut)
    taille = f"{len(reponse.corps)} o" if len(reponse.corps) < 1_000_000 else "> 1 Mo"
    return verdict.conclure(True, f"JSON exploitable, {taille}", reponse.statut)


def _epreuve_refus(hote: str, base: str, cible: str, essais: int, attente: float) -> Verdict:
    """Ce qui doit être refusé le soit : une route inconnue, un proxy sans cible.

    Un 200 inattendu ici est le signe d'une réécriture d'hébergeur qui répond à
    tout — le genre de réglage qui rend une API « accessible » au sens où une
    porte ouverte sur la rue est accessible.
    """
    verdict = Verdict(hote, cible, "refusé (ni 200 ni 500)")
    reponse = _insister(base + cible, essais=essais, attente=attente)
    if reponse.statut == 200:
        return verdict.conclure(False, "répond 200 : la route ne devrait pas exister",
                                reponse.statut)
    if reponse.statut >= 500:
        return verdict.conclure(False, f"erreur serveur ({reponse.statut})", reponse.statut)
    return verdict.conclure(True, f"refus propre ({reponse.statut})", reponse.statut)


def _epreuve_post_refuse(hote: str, base: str, essais: int, attente: float) -> Verdict:
    """Un POST sur une route qui n'existe pas doit être refusé, pas servi."""
    verdict = Verdict(hote, "POST /api/route-inconnue", "refusé sans erreur serveur")
    reponse = _insister(base + "/api/route-inconnue", methode="POST", corps={},
                        essais=essais, attente=attente)
    if reponse.statut in (200, 201):
        return verdict.conclure(False, "accepté (200) pour une route inconnue", reponse.statut)
    if reponse.statut >= 500:
        return verdict.conclure(False, f"erreur serveur ({reponse.statut})", reponse.statut)
    return verdict.conclure(True, f"refus propre ({reponse.statut})", reponse.statut)


def sonder(hote: str, base: str, essais: int, attente: float) -> list[Verdict]:
    """Toutes les épreuves d'un hôte, dans l'ordre où la page les expose."""
    verdicts = [_epreuve_page(hote, base, essais, attente)]
    verdicts += [_epreuve_texte(hote, base, chemin, essais, attente)
                 for chemin in surface.TEXTES]
    verdicts += [_epreuve_image(hote, base, chemin, essais, attente)
                 for chemin in surface.IMAGES]
    verdicts += [_epreuve_json(hote, base, chemin, essais, attente)
                 for chemin in ROUTES_GET]
    verdicts += [_epreuve_json(hote, base, chemin, essais, attente)
                 for chemin in ROUTES_GET_AVEC_PARAMETRES]
    verdicts += [_epreuve_json(hote, base, chemin, essais, attente, corps=corps)
                 for chemin, corps in ROUTES_POST]
    verdicts.append(_epreuve_refus(hote, base, "/api/route-inconnue", essais, attente))
    verdicts.append(_epreuve_refus(hote, base, "/api/proxy", essais, attente))
    verdicts.append(_epreuve_post_refuse(hote, base, essais, attente))
    return verdicts


def rapporter(verdicts: list[Verdict], hotes: list[str]) -> None:
    """Écrit le rapport dans la page du run, quand GitHub le demande.

    Un journal de job se télécharge ; la page du run, elle, se lit. Sans cela,
    la seule trace lisible de cette veille serait un `curl` dans un terminal —
    c'est-à-dire rien pour qui ouvre le dépôt par son navigateur. GitHub appelle
    cela le *résumé de l'étape* : le script s'y conforme sans dépendre de quoi
    que ce soit d'autre que la variable d'environnement.
    """
    import os

    chemin = os.environ.get("GITHUB_STEP_SUMMARY")
    if not chemin:
        return
    rates = [verdict for verdict in verdicts if not verdict.reussi]
    lignes = [
        f"## Veille en ligne — {'tout répond' if not rates else f'{len(rates)} échec(s)'}",
        "",
        f"{len(verdicts)} épreuves sur " + ", ".join(HOTES[nom] for nom in hotes) + ".",
        "",
    ]
    if rates:
        lignes += ["### Ce qui ne répond pas", ""]
        lignes += [f"- **{verdict.hote}** `{verdict.cible}` — {verdict.detail}"
                   for verdict in rates]
        lignes += [""]
    lignes += ["<details><summary>Le détail, épreuve par épreuve</summary>", "",
               "| hôte | cible | statut | résultat |", "| --- | --- | --- | --- |"]
    for verdict in verdicts:
        marque = "✓" if verdict.reussi else "✗"
        detail = verdict.detail.replace("|", "\\|")
        statut = verdict.statut or "—"
        lignes.append(f"| {marque} {verdict.hote} | `{verdict.cible}` | {statut} | {detail} |")
    lignes += ["", "</details>", ""]
    with Path(chemin).open("a", encoding="utf-8") as rapport:
        rapport.write("\n".join(lignes) + "\n")


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analyseur.add_argument("--hote", choices=sorted(HOTES), action="append",
                           help="hôte à interroger (défaut : les deux)")
    analyseur.add_argument("--essais", type=int, default=3,
                           help="tentatives par adresse, pour un hôte endormi (défaut : 3)")
    analyseur.add_argument("--attente", type=float, default=15.0,
                           help="secondes entre deux tentatives (défaut : 15)")
    options = analyseur.parse_args()

    hotes = options.hote or sorted(HOTES)
    verdicts: list[Verdict] = []
    for nom in hotes:
        base = HOTES[nom]
        print(f"\n\033[1m{nom} — {base}\033[0m")
        trouves = sonder(nom, base, max(1, options.essais), max(0.0, options.attente))
        for verdict in trouves:
            print(verdict.ligne())
        verdicts += trouves

    rapporter(verdicts, hotes)
    rates = [verdict for verdict in verdicts if not verdict.reussi]
    print()
    if rates:
        print(f"{len(rates)} épreuve(s) en échec sur {len(verdicts)} :")
        for verdict in rates:
            print(f"  ✗ {verdict.hote} {verdict.cible} — {verdict.detail}")
        return 1
    print(f"Tout répond : {len(verdicts)} épreuves passées sur "
          f"{', '.join(HOTES[nom] for nom in hotes)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
