#!/usr/bin/env python3
"""Empêcher la copie de secours de s'endormir — et dire quand elle ne répond plus.

Le problème, en une phrase
--------------------------
L'offre gratuite de Render **endort** un service après une quinzaine de minutes
sans visite. Le visiteur suivant attend une trentaine de secondes — et, quand le
réveil échoue, il tombe sur la page d'erreur de l'hébergeur : un **502 Bad
Gateway**, « ce service est actuellement indisponible ». C'est exactement ce qui
est arrivé le 14 octobre 2026, et ce n'était pas notre code (l'application
démarre en 880 ms et sert ses vingt-deux routes ; vérifié).

Le garde-veille frappe donc à la porte **régulièrement pendant les heures où
l'on consulte le site** : le service n'a plus le temps de s'endormir, et le
visiteur n'attend plus.

Ce que fait ce script
---------------------
1. ``--ping`` : frappe à la porte et vérifie que c'est bien **notre
   application** qui répond — le lexique, en JSON — et non la page d'attente de
   l'hébergeur ou un 502 de passerelle. Il insiste, parce qu'un réveil prend du
   temps, et il dit **combien de temps**.
2. ``--cron`` : relit la fenêtre du rendez-vous et dit ce qu'elle couvre en
   France — **en hiver comme en été**, puisque le calendrier de GitHub s'exprime
   en temps universel et que la France change d'heure. Il **refuse** une fenêtre
   qui consommerait plus que ce que le palier gratuit offre, parce qu'un
   dépassement ne facture pas : il **suspend** les services. Pire que le
   sommeil.
3. ``--etat-precedent`` : ne parle que pour annoncer un **changement** — la
   panne, puis le retour à la normale. Un garde-veille qui commente toutes les
   dix minutes est un garde-veille qu'on coupe.

Usage :
    python3 outils/garde-veille.py --ping
    python3 outils/garde-veille.py --ping --rapport /tmp/garde.md
    python3 outils/garde-veille.py --cron "*/10 5-22 * * *"
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
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from simulateur import surface_publique as surface  # noqa: E402

#: La copie de secours : la même page, le même moteur, sur un autre hébergeur.
SECOURS = surface.HOTE_SECOURS

#: La porte à laquelle on frappe. `render.yaml` déclare **la même** adresse
#: comme `healthCheckPath` : un chemin JSON qui ne calcule rien (49 666 octets,
#: 4,5 ms), donc idéal pour réveiller un service sans rien lui demander.
SONDE = "/api/lexique"

#: Ce qu'un service endormi dit de lui-même pendant qu'il démarre.
MARQUE_DEMARRAGE = "Application loading"

#: Le palier gratuit de Render offre un nombre d'heures d'instance par mois et
#: par compte. Un dépassement ne facture pas : il **suspend**.
HEURES_OFFERTES = 750

#: La part qu'on s'autorise. Le reste est la marge — un compte peut porter
#: d'autres services gratuits, et le mois de février n'est pas le mois de mars.
MARGE = 0.85

#: Une visite garde le service éveillé une quinzaine de minutes. On compte donc
#: un quart d'heure après la **dernière** visite de la journée.
RESIDU = 0.25

#: Les états publiés dans la page de suivi. Le marqueur **porte l'état** : c'est
#: ce qui permet de savoir, au passage suivant, s'il y a quelque chose à dire.
MARQUE_OK = "<!-- garde-veille: ok -->"
MARQUE_PANNE = "<!-- garde-veille: panne -->"


# ── La fenêtre du rendez-vous ───────────────────────────────────────────────


def _champ(champ: str, minimum: int, maximum: int) -> list[int]:
    """Les valeurs d'un champ de cron : `*`, `a-b`, `*/n`, `a,b,c`.

    Le calendrier de GitHub s'écrit en cinq champs (`minute heure jour mois
    jour-semaine`) et en **temps universel**. On ne lit ici que les deux
    premiers, mais on refuse un champ illisible plutôt que de l'ignorer : une
    expression comprise de travers donnerait une fenêtre fausse, donc des heures
    consommées fausses.
    """
    valeurs: set[int] = set()
    for morceau in champ.split(","):
        morceau = morceau.strip()
        if morceau == "*":
            valeurs.update(range(minimum, maximum + 1))
            continue
        pas = 1
        if "/" in morceau:
            morceau, _, brut = morceau.partition("/")
            pas = int(brut)
            if pas <= 0:
                raise ValueError("pas nul")
        if morceau in ("*", ""):
            debut, fin = minimum, maximum
        elif "-" in morceau:
            debut, _, fin = morceau.partition("-")
            debut, fin = int(debut), int(fin)
        else:
            debut = fin = int(morceau)
        if debut < minimum or fin > maximum or debut > fin:
            raise ValueError(f"hors bornes : {debut}-{fin}")
        valeurs.update(range(debut, fin + 1, pas))
    return sorted(valeurs)


class Analyse:
    """Ce qu'une expression de cron dit vraiment, une fois traduite en France."""

    def __init__(self, cron: str) -> None:
        champs = cron.split()
        if len(champs) != 5:
            raise ValueError(f"un cron a cinq champs, pas {len(champs)} : {cron!r}")
        self.cron = cron
        self.minutes = _champ(champs[0], 0, 59)
        self.heures_utc = _champ(champs[1], 0, 23)

    @property
    def passages_par_jour(self) -> int:
        return len(self.minutes) * len(self.heures_utc)

    def couverture_locale(self, decalage: int) -> tuple[int, int]:
        """La fenêtre couverte, en heures locales, pour un décalage donné.

        Chaque visite garde le service éveillé un moment : la couverture ne
        s'arrête donc pas à la dernière visite, elle s'arrête un peu après.
        """
        premier = self.heures_utc[0] + decalage
        dernier = self.heures_utc[-1] + decalage
        if premier >= 24 and dernier >= 24:
            premier, dernier = premier - 24, dernier - 24
        return premier, dernier

    @property
    def heures_par_jour(self) -> float:
        return len(self.heures_utc) + RESIDU

    @property
    def heures_par_mois(self) -> float:
        # 30,44 : la longueur moyenne d'un mois, année bissextile comprise.
        return self.heures_par_jour * 30.44

    @property
    def plafond(self) -> float:
        return HEURES_OFFERTES * MARGE

    @property
    def depasse(self) -> bool:
        return self.heures_par_mois > self.plafond


def texte_analyse(analyse: Analyse) -> str:
    """Le verdict, en clair, avec ses deux saisons et son coût."""
    hiver = analyse.couverture_locale(1)
    ete = analyse.couverture_locale(2)
    lignes = [
        f"Rendez-vous `{analyse.cron}` — {analyse.passages_par_jour} visites par jour",
        "",
        f"- hiver (Paris = UTC+1) : de {hiver[0]} h à {hiver[1]} h",
        f"- été (Paris = UTC+2) : de {ete[0]} h à {ete[1]} h",
        f"- heures d'instance consommées : {analyse.heures_par_mois:.0f} h par mois "
        f"(plafond {analyse.plafond:.0f} h — {HEURES_OFFERTES} h offertes, "
        f"marge de {100 - MARGE * 100:.0f} %)",
        "",
    ]
    if analyse.depasse:
        lignes += [
            "**Cette fenêtre est refusée.** Le palier gratuit ne facture pas un "
            "dépassement : il **suspend** les services. Réduire les heures "
            "couvertes, ou augmenter le pas de `minute`.",
        ]
    else:
        lignes += ["La fenêtre tient dans ce que le palier gratuit offre."]
    return "\n".join(lignes)


# ── La visite ───────────────────────────────────────────────────────────────


class Reponse:
    """Ce que l'hôte a répondu — y compris quand il n'a rien répondu."""

    def __init__(self, statut: int, type_contenu: str, corps: bytes,
                 duree: float = 0.0) -> None:
        self.statut = statut
        self.type_contenu = type_contenu
        self.corps = corps
        self.duree = duree

    @property
    def texte(self) -> str:
        return self.corps.decode("utf-8", "replace")

    @property
    def muet(self) -> bool:
        """Aucune réponse du tout : le réseau a lâché, ou le délai est passé."""
        return self.statut == 0

    @property
    def en_demarrage(self) -> bool:
        """L'hôte dit-il lui-même qu'il démarre ? Le réveil, en un mot."""
        return MARQUE_DEMARRAGE in self.texte

    @property
    def est_notre_application(self) -> bool:
        """Le lexique servi est-il le nôtre ?

        Un 200 de la part d'un voisin — une page de parking, un proxy — ne doit
        pas passer pour une application vivante. C'est le lexique qu'on demande,
        c'est le lexique qu'on attend.
        """
        if self.statut != 200:
            return False
        try:
            charge = json.loads(self.texte)
        except json.JSONDecodeError:
            return False
        return isinstance(charge, dict) and "termes" in charge and "categories" in charge


def _demander(url: str, delai: float = 45.0) -> Reponse:
    """Une requête, sans jamais lever : un hôte muet est un **résultat**."""
    debut = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=delai) as flux:
            return Reponse(flux.status, flux.headers.get("Content-Type", ""),
                           flux.read(), time.monotonic() - debut)
    except urllib.error.HTTPError as erreur:
        return Reponse(erreur.code, erreur.headers.get("Content-Type", "") if erreur.headers else "",
                       erreur.read() or b"", time.monotonic() - debut)
    except (urllib.error.URLError, TimeoutError, OSError) as erreur:
        return Reponse(0, "", f"{type(erreur).__name__}: {erreur}".encode(),
                       time.monotonic() - debut)


class Verdict:
    """Le résultat d'une visite : réussi ou non, et de quoi le raconter."""

    def __init__(self, reussi: bool, detail: str, duree: float = 0.0,
                 essais: int = 0, reveil: bool = False) -> None:
        self.reussi = reussi
        self.detail = detail
        self.duree = duree
        self.essais = essais
        self.reveil = reveil

    @property
    def marqueur(self) -> str:
        return MARQUE_OK if self.reussi else MARQUE_PANNE


def _lisible(reponse: Reponse) -> str:
    """Ce qu'on écrit quand ça n'a pas répondu — sans jargon, et sans douter."""
    if reponse.muet:
        return f"aucune réponse de l'hôte ({reponse.texte.strip() or 'silence'})"
    if reponse.statut in (502, 503, 504):
        return (f"la passerelle répond {reponse.statut} : le service n'est pas "
                f"derrière (endormi ou réveil en échec)")
    if reponse.statut == 200:
        debut = reponse.texte.strip().replace("\n", " ")[:70]
        return f"200 reçu, mais ce n'est pas notre application : « {debut} »"
    return f"attendu 200, reçu {reponse.statut}"


def visiter(base: str = SECOURS, essais: int = 3, attente: float = 10.0,
            delai: float = 45.0, demander=None) -> Verdict:
    """Frapper à la porte, insister, et raconter ce qui s'est passé.

    L'insistance est **le sujet ici** : un service endormi met une trentaine de
    secondes à se lever, et une visite abandonnée trop tôt laisserait croire à
    une panne. Elle est bornée — `essais` fois, avec `attente` entre les deux :
    au pire quelques minutes, une seule adresse à la fois.
    """
    demander = demander or _demander
    url = base.rstrip("/") + SONDE
    debut = time.monotonic()
    reponse = None
    for essai in range(1, max(1, essais) + 1):
        reponse = demander(url, delai)
        duree = time.monotonic() - debut
        if reponse.est_notre_application:
            # Un réveil, ça se voit : il a fallu plusieurs essais, ou la réponse
            # a mis plus de cinq secondes à venir. Le dire, parce que c'est
            # l'information la plus utile de tout ce script — c'est ce qui
            # distingue « le service s'endort » de « le service va bien ».
            reveil = essai > 1 or reponse.duree > 5.0
            mot = "réveillée" if reveil else "déjà éveillée"
            suite = ("du premier coup" if essai == 1
                     else f"au {essai}ᵉ essai, après {duree:.1f} s")
            detail = f"{mot} : le lexique répond ({len(reponse.corps)} o), {suite}"
            return Verdict(True, detail, duree, essai, reveil)
        if essai < max(1, essais):
            time.sleep(max(0.0, attente))
    duree = time.monotonic() - debut
    return Verdict(False, _lisible(reponse), duree, max(1, essais))


# ── Ce qu'on dit, et quand on le dit ────────────────────────────────────────


def marqueur_du_texte(texte: str) -> str:
    """L'état porté par un commentaire existant, ou une chaîne vide.

    C'est le marqueur lui-même qui **est** l'état : il n'y a donc rien à
    stocker, rien à relire d'un passage à l'autre, et rien à oublier.
    """
    for marqueur in (MARQUE_PANNE, MARQUE_OK):
        if marqueur in texte:
            return marqueur
    return ""


def faut_il_publier(precedent: str, verdict: Verdict) -> bool:
    """Publier seulement un **changement** d'état.

    Trois cas : la panne (on le dit), le retour à la normale (on le dit aussi —
    sinon la page resterait à raconter une panne qui n'existe plus), et tout le
    reste (silence). Le premier passage silencieux est voulu : personne n'a
    besoin d'apprendre que tout va bien toutes les dix minutes.
    """
    return bool(verdict.marqueur != precedent) and (
        verdict.marqueur == MARQUE_PANNE or bool(precedent))


def rapport_visite(verdict: Verdict, base: str = SECOURS) -> str:
    """Le compte rendu d'une visite, en clair."""
    ligne = "✓" if verdict.reussi else "✗"
    return "\n".join([
        f"## Garde-veille — {'éveillée' if verdict.reussi else 'ne répond pas'}",
        "",
        f"{ligne} {base.rstrip('/')}{SONDE} — {verdict.detail} "
        f"({verdict.duree:.1f} s, {verdict.essais} essai(s))",
        "",
    ])


def ecrire(texte: str, fichiers: list[str] | None = None) -> list[Path]:
    """Écrit le rapport là où on le lira (et dans le résumé d'étape sur un coureur)."""
    import os

    ecrits: list[Path] = []
    for chemin in list(fichiers or []):
        ecrits.append(Path(chemin))
    resume = os.environ.get("GITHUB_STEP_SUMMARY")
    if resume:
        ecrits.append(Path(resume))
    for chemin in ecrits:
        chemin.parent.mkdir(parents=True, exist_ok=True)
        with chemin.open("a", encoding="utf-8") as flux:
            flux.write(texte + "\n")
    return ecrits


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analyseur.add_argument("--ping", action="store_true",
                           help="frapper à la porte de la copie de secours")
    analyseur.add_argument("--cron", metavar="EXPRESSION",
                           help="analyser une fenêtre de rendez-vous au lieu de visiter")
    analyseur.add_argument("--base", default=SECOURS,
                           help="l'adresse à visiter (défaut : la copie de secours)")
    analyseur.add_argument("--essais", type=int, default=3,
                           help="visites avant de conclure (défaut : 3)")
    analyseur.add_argument("--attente", type=float, default=10.0,
                           help="secondes entre deux visites (défaut : 10)")
    analyseur.add_argument("--delai", type=float, default=45.0,
                           help="secondes avant d'abandonner une visite (défaut : 45)")
    analyseur.add_argument("--rapport", action="append", metavar="FICHIER",
                           help="où écrire le compte rendu (répétable)")
    analyseur.add_argument("--etat-precedent", default="", metavar="MARQUEUR",
                           help="le marqueur du commentaire existant, s'il y en a un")
    options = analyseur.parse_args()

    if options.cron:
        try:
            analyse = Analyse(options.cron)
        except ValueError as erreur:
            print(f"Fenêtre illisible : {erreur}", file=sys.stderr)
            return 2
        print(texte_analyse(analyse))
        return 1 if analyse.depasse else 0

    if not options.ping:
        analyseur.error("rien à faire : --ping ou --cron")

    verdict = visiter(options.base, options.essais, options.attente, options.delai)
    texte = rapport_visite(verdict, options.base)
    print(texte)
    ecrire(texte, options.rapport)

    # Deux lignes lisibles par une machine : l'état, et s'il y a quelque chose à
    # publier. Le workflow n'a donc aucune décision à prendre, seulement des
    # gestes à faire.
    print(f"etat={'ok' if verdict.reussi else 'panne'}")
    print("publier=" + ("oui" if faut_il_publier(options.etat_precedent, verdict) else "non"))
    return 0 if verdict.reussi else 1


if __name__ == "__main__":
    raise SystemExit(main())
