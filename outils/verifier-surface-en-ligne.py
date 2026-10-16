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

**Deux moments où la réponse n'est pas encore la bonne.** Un service endormi met
une trentaine de secondes à se lever ; un déploiement, une à deux minutes à
arriver. Dans les deux cas, ce qui est servi n'est pas encore ce que le dépôt
engendre — et « pas encore » n'est pas « faux ». **La page** est donc réessayée
quelle que soit la réponse (c'est elle, aussi, qui réveille) ; les autres
adresses suivent à un seul essai, parce qu'un hôte déjà réveillé répond du
premier coup et qu'un hôte qui ne répond pas ne se réveille pas davantage parce
qu'on l'a redemandé — un compte en toutes lettres vieillirait ici à chaque route
neuve, et c'est la veille elle-même qui annonce son nombre d'épreuves.

**Et un 502 peut n'être qu'un à-coup.** Mesure du 15 octobre 2026, treize
heures quarante-cinq, copie de secours : la veille publie « le service n'est pas
derrière » pour `/api/bulles` — alors que, dans le **même passage**, soixante-sept
autres adresses du même hôte venaient de répondre 200, la plus grosse comprise.
Le service ne dormait donc pas : Render redéployait la version qu'on venait de
fusionner, et c'est cette réponse-là qui n'était pas arrivée. Un hôte qui répond
ailleurs est un hôte **debout** : c'est le seul cas où la veille se permet une
reprise, une seule, sur la route fautive — et où son verdict cesse de dire
« le service n'est pas derrière », parce que c'est faux.
"""

from __future__ import annotations

import argparse
import functools
import json
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
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
    "/api/prospective",
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
        """L'hôte dit-il lui-même qu'il est en train de démarrer ?

        Uniquement s'il le dit : la page d'attente de la copie de secours
        (« Application loading »). Tout autre non-200 — un **502** de passerelle,
        un 503 — est une **panne**, pas un réveil. Les confondre coûtait cher :
        un hôte tombé faisait insister chaque sonde cinq fois, et la veille
        durait trois quarts d'heure au lieu de deux minutes.
        """
        return MARQUE_DEMARRAGE in self.texte

    @property
    def muet(self) -> bool:
        """Aucune réponse du tout : le réseau a lâché, ou l'hôte n'a pas répondu
        dans le délai. Cela, on le retente — c'est le cas d'un service qui se
        réveille vraiment."""
        return self.statut == 0


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
        # Un hôte qui ne répond pas est un **résultat**, pas une raison de tout
        # arrêter : la veille doit pouvoir dire « celle-là ne répond pas » et
        # continuer à vérifier les autres. Sans cela, une seule adresse muette
        # rendait le rapport inutilisable — et le rapport est tout ce qu'on lit.
        return Reponse(0, "", f"{type(erreur).__name__}: {erreur}".encode())


def _insister(url: str, methode: str = "GET", corps: dict[str, object] | None = None,
              essais: int = 3, attente: float = 15.0, delai: float = 30.0,
              journal: list[str] | None = None, acceptable=None) -> Reponse:
    """Interroge, en laissant à un hôte endormi — ou à un déploiement — le temps.

    Sans `acceptable`, on insiste quand l'hôte annonce son démarrage ou quand il
    n'a **rien** répondu : c'est le temps du réveil, et un 502 est un verdict.

    Avec `acceptable`, on insiste **tant que** la réponse ne satisfait pas ce
    critère. C'est le cas de la page, et d'elle seule : juste après une fusion,
    un déploiement est en vol, et la page est exactement ce qu'un déploiement
    remplace en dernier. Attendre, c'est laisser à Vercel ou à Render le temps
    d'arriver ; ne pas attendre, c'est appeler « faux » ce qui n'est que « pas
    encore » — et faire rougir une fusion pour un déploiement en cours.

    Une réponse **satisfaisante** s'arrête là, sans attendre : une veille qui
    demanderait cinq fois une page déjà bonne ajouterait quatre-vingts secondes
    à chaque passage pour rien.
    """
    derniere: Reponse | None = None
    for essai in range(1, max(1, essais) + 1):
        derniere = _demander(url, methode, corps, delai)
        if essai == max(1, essais):
            return derniere
        if acceptable is not None:
            bonne = bool(acceptable(derniere))
        else:
            bonne = not (derniere.en_demarrage or derniere.muet)
        if bonne:
            return derniere
        if journal is not None:
            journal.append(f"pas encore prêt, relance {essai}/{max(1, essais) - 1} "
                           f"dans {attente:g} s")
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


#: Les statuts d'une passerelle qui répond à la place du service : ce sont les
#: seuls où la question « le service est-il derrière ? » se pose.
PASSERELLE = (502, 503, 504)


def _reponse_lisible(reponse: Reponse, hote_debout: bool = False) -> str:
    """Ce qu'on écrit quand l'hôte n'a pas répondu 200 — sans jargon.

    `hote_debout` est la seule chose que la veille sache **de source sûre** :
    d'autres adresses de ce même hôte ont répondu 200 dans ce passage. Le dire
    évite la phrase fausse du 15 octobre 2026 — « le service n'est pas derrière »
    écrit sur un service qui venait de répondre soixante-sept fois.
    """
    if reponse.muet:
        detail = reponse.texte.strip() or "aucune réponse"
        return f"aucune réponse de l'hôte ({detail})"
    if reponse.statut in PASSERELLE:
        if hote_debout:
            return (f"la passerelle répond {reponse.statut} sur cette adresse, alors que "
                    f"l'hôte répondait par ailleurs : ce n'est pas le service qui dort, "
                    f"c'est cette réponse-là qui n'arrive pas")
        return (f"la passerelle répond {reponse.statut} : le service n'est pas "
                f"derrière (endormi, suspendu, ou démarrage en échec)")
    return f"attendu 200, reçu {reponse.statut}"


def _epreuve_texte(hote: str, base: str, chemin: str, essais: int,
                   attente: float, hote_debout: bool = False) -> Verdict:
    """Le texte servi doit être **le même** que celui que le code engendre."""
    verdict = Verdict(hote, chemin, "texte identique à celui engendré")
    attendu = surface.texte(chemin)
    if attendu is None:
        return verdict.conclure(False, "chemin absent de la surface publique")
    reponse = _insister(base + chemin, essais=essais, attente=attente)
    if reponse.statut != 200:
        return verdict.conclure(False, _reponse_lisible(reponse, hote_debout), reponse.statut)
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


def _epreuve_image(hote: str, base: str, chemin: str, essais: int, attente: float,
                   hote_debout: bool = False) -> Verdict:
    """L'image servie doit être **le fichier versionné**, au type annoncé."""
    verdict = Verdict(hote, chemin, "fichier identique au fichier versionné")
    fichier = surface.chemin_image(chemin)
    if fichier is None:
        return verdict.conclure(False, "chemin absent de la surface publique")
    reponse = _insister(base + chemin, essais=essais, attente=attente)
    if reponse.statut != 200:
        return verdict.conclure(False, _reponse_lisible(reponse, hote_debout), reponse.statut)
    type_attendu = TYPES_IMAGES.get(chemin, ())
    if type_attendu and not any(reponse.type_contenu.startswith(t) for t in type_attendu):
        return verdict.conclure(
            False, f"type inattendu : {reponse.type_contenu or 'aucun'}", reponse.statut)
    if reponse.corps != fichier.read_bytes():
        return verdict.conclure(
            False, f"différent du fichier versionné ({len(reponse.corps)} o servis)", reponse.statut)
    return verdict.conclure(
        True, f"{len(reponse.corps)} octets, identique au fichier versionné", reponse.statut)


#: Ce que la page doit dire d'elle-même. Chaque motif porte son nom lisible :
#: un échec qui dit « absents : adresse canonique » se corrige ; « page
#: incomplète » se cherche.
ATTENDUS_PAGE: dict[str, str] = {
    f'rel="canonical" href="{surface.URL_CANONIQUE}"': "adresse canonique",
    'name="description"': "description",
    f'property="og:image" content="{surface.URL_CANONIQUE}{surface.IMAGE_APERCU}"':
        "aperçu de partage",
    '"@type": "WebApplication"': "données structurées",
    'name="robots"': "directives d'indexation",
}


def _page_complete(reponse: Reponse) -> bool:
    """La page est-elle arrivée **entière** ?

    Sert de critère à `_insister` : tant que la page est incomplète, on attend —
    c'est ce que fait un déploiement en vol. Le critère dit « entière », le
    verdict dira « ce qui manque ».
    """
    if reponse.statut != 200 or not reponse.type_contenu.startswith("text/html"):
        return False
    return all(motif in reponse.texte for motif in ATTENDUS_PAGE)


def _epreuve_page(hote: str, base: str, essais: int, attente: float,
                  hote_debout: bool = False) -> Verdict:
    """La page doit dire d'elle-même ce que la surface publique annonce."""
    verdict = Verdict(hote, "/", "page complète et déclarée")
    # `acceptable=_page_complete` : la page est ce qu'un déploiement remplace en
    # dernier, et c'est elle aussi qui réveille un service endormi. Voir `_insister`.
    reponse = _insister(base + "/", essais=essais, attente=attente, delai=60.0,
                        acceptable=_page_complete)
    if reponse.statut != 200:
        return verdict.conclure(False, _reponse_lisible(reponse, hote_debout), reponse.statut)
    if not reponse.type_contenu.startswith("text/html"):
        return verdict.conclure(
            False, f"attendu du text/html, reçu {reponse.type_contenu or 'aucun type'}",
            reponse.statut)
    page = reponse.texte
    manquants = [libelle for motif, libelle in ATTENDUS_PAGE.items() if motif not in page]
    if manquants:
        return verdict.conclure(False, "absents : " + ", ".join(manquants), reponse.statut)
    return verdict.conclure(
        True, f"{len(page)} caractères, canonique {surface.URL_CANONIQUE}", reponse.statut)


def _epreuve_json(hote: str, base: str, cible: str, essais: int, attente: float,
                  corps: dict[str, object] | None = None,
                  hote_debout: bool = False) -> Verdict:
    """Une route d'API doit répondre 200 **et** un JSON exploitable."""
    methode = "POST" if corps is not None else "GET"
    verdict = Verdict(hote, cible, f"{methode} 200 en JSON")
    reponse = _insister(base + cible, methode=methode, corps=corps, essais=essais,
                        attente=attente, delai=120.0)
    if reponse.statut != 200:
        return verdict.conclure(False, _reponse_lisible(reponse, hote_debout), reponse.statut)
    if not reponse.type_contenu.startswith("application/json"):
        return verdict.conclure(
            False, f"type inattendu : {reponse.type_contenu or 'aucun'}", reponse.statut)
    try:
        charge = json.loads(reponse.texte)
    except json.JSONDecodeError:
        debut = reponse.texte.strip().replace("\n", " ")[:80]
        return verdict.conclure(False, f"ce n'est pas du JSON : « {debut} »",
                                reponse.statut)
    if isinstance(charge, dict) and set(charge) == {"error"}:
        return verdict.conclure(False, f"le serveur répond une erreur : {charge['error']}",
                                reponse.statut)
    taille = f"{len(reponse.corps)} o" if len(reponse.corps) < 1_000_000 else "> 1 Mo"
    return verdict.conclure(True, f"JSON exploitable, {taille}", reponse.statut)


def _epreuve_refus(hote: str, base: str, cible: str, essais: int, attente: float,
                   hote_debout: bool = False) -> Verdict:
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
    if reponse.statut == 0:
        return verdict.conclure(False, _reponse_lisible(reponse, hote_debout), reponse.statut)
    if reponse.statut >= 500:
        return verdict.conclure(False, f"erreur serveur ({reponse.statut})", reponse.statut)
    return verdict.conclure(True, f"refus propre ({reponse.statut})", reponse.statut)


def _epreuve_post_refuse(hote: str, base: str, essais: int, attente: float,
                         hote_debout: bool = False) -> Verdict:
    """Un POST sur une route qui n'existe pas doit être refusé, pas servi."""
    verdict = Verdict(hote, "POST /api/route-inconnue", "refusé sans erreur serveur")
    reponse = _insister(base + "/api/route-inconnue", methode="POST", corps={},
                        essais=essais, attente=attente)
    if reponse.statut in (200, 201):
        return verdict.conclure(False, "accepté (200) pour une route inconnue", reponse.statut)
    if reponse.statut == 0:
        return verdict.conclure(False, _reponse_lisible(reponse, hote_debout), reponse.statut)
    if reponse.statut >= 500:
        return verdict.conclure(False, f"erreur serveur ({reponse.statut})", reponse.statut)
    return verdict.conclure(True, f"refus propre ({reponse.statut})", reponse.statut)


def sonder(hote: str, base: str, essais: int, attente: float) -> list[Verdict]:
    """Toutes les épreuves d'un hôte, dans l'ordre où la page les expose.

    **L'insistance est réservée à la première sonde.** C'est la page qui réveille
    un service endormi : elle seule mérite qu'on attende et qu'on recommence.
    Les vingt et une autres suivent à un seul essai — un hôte déjà réveillé
    répond du premier coup, et un hôte qui ne répond pas ne se réveille pas
    davantage parce qu'on lui a demandé vingt-deux fois. Sans cette règle, une
    copie de secours suspendue faisait durer la veille une quarantaine de
    minutes, ce qui est exactement le genre de lenteur qui fait qu'on ne la lit
    plus.

    **Et si la page ne répond pas du tout**, l'hôte est déclaré muet une fois
    pour toutes : répéter la même panne sur chaque route ajoute des lignes, pas
    de l'information, et coûte une sonde à chaque fois.

    Ces épreuves-ci sont rendues **rejouables** (voir `_sondes`) pour une seule
    raison : `_reprendre_les_oublis`, juste après, reprend les 502 isolés d'un
    hôte qui répond par ailleurs.
    """
    sondes = _sondes(hote, base, essais, attente)
    page = sondes[0]()                       # la page d'abord : c'est elle qui réveille
    if page.statut == 0:
        muet = Verdict(hote, "(toutes les autres adresses)", "répondre")
        muet.conclure(False, "non éprouvées : l'hôte ne répond à aucune adresse", 0)
        return [page, muet]
    verdicts = [page] + [sonde() for sonde in sondes[1:]]
    return _reprendre_les_oublis(sondes, verdicts, attente)


def _sondes(hote: str, base: str, essais: int,
            attente: float) -> list[Callable[..., Verdict]]:
    """Les épreuves d'un hôte, chacune sachant se rejouer.

    Rendues sous forme d'appelables plutôt que jouées ici : reprendre une épreuve
    demande de savoir **laquelle** reprendre, et de la reprendre en lui disant ce
    qu'on a appris entre-temps — qu'une autre adresse du même hôte a répondu.
    Une liste de verdicts ne se relance pas ; une liste de fonctions, si.
    """
    une = 1
    sondes: list[Callable[..., Verdict]] = [
        functools.partial(_epreuve_page, hote, base, essais, attente)]
    sondes += [functools.partial(_epreuve_texte, hote, base, chemin, une, attente)
               for chemin in surface.TEXTES]
    sondes += [functools.partial(_epreuve_image, hote, base, chemin, une, attente)
               for chemin in surface.IMAGES]
    sondes += [functools.partial(_epreuve_json, hote, base, chemin, une, attente)
               for chemin in ROUTES_GET]
    sondes += [functools.partial(_epreuve_json, hote, base, chemin, une, attente)
               for chemin in ROUTES_GET_AVEC_PARAMETRES]
    sondes += [functools.partial(_epreuve_json, hote, base, chemin, une, attente, corps=corps)
               for chemin, corps in ROUTES_POST]
    sondes += [functools.partial(_epreuve_refus, hote, base, "/api/route-inconnue", une, attente),
               functools.partial(_epreuve_refus, hote, base, "/api/proxy", une, attente),
               functools.partial(_epreuve_post_refuse, hote, base, une, attente)]
    return sondes


def _reprendre_les_oublis(sondes: list[Callable[..., Verdict]], verdicts: list[Verdict],
                          attente: float) -> list[Verdict]:
    """Un 502 isolé sur un hôte qui répond : une reprise, une seule.

    Ce n'est pas de l'indulgence, c'est une mesure. Un hôte qui a répondu 200
    ailleurs dans le **même passage** n'est pas endormi : il redéploie peut-être,
    ou il a lâché une réponse. Redemander cette adresse-là coûte une quinzaine de
    secondes et évite de publier une panne qui n'existe pas — c'est exactement
    ce qui est arrivé le 15 octobre 2026 à `/api/bulles` de la copie de secours,
    revenue bonne dans la seconde, pendant que le rapport la disait morte.

    **Et si l'hôte n'a rien répondu nulle part, il n'y a aucune reprise** : ce
    n'est plus un à-coup, c'est une panne. Insister n'y changerait rien et une
    veille sur un hôte suspendu durerait quarante minutes au lieu de deux.
    """
    if not any(verdict.reussi for verdict in verdicts):
        return verdicts
    for index, verdict in enumerate(verdicts):
        if verdict.reussi or verdict.statut not in PASSERELLE:
            continue
        time.sleep(attente)
        reprise = sondes[index](hote_debout=True)
        if reprise.reussi:
            reprise.detail += " — cette réponse-là manquait, pas le service"
        else:
            reprise.detail += " (reprise après un 502)"
        verdicts[index] = reprise
    return verdicts


def rapporter(verdicts: list[Verdict], hotes: list[str],
              fichiers: list[str] | None = None) -> list[Path]:
    """Écrit le rapport là où on le lira — au moins un endroit.

    Un journal de job se télécharge ; la page du run, elle, se lit. GitHub offre
    pour cela le *résumé de l'étape*, que le script remplit par la variable
    `GITHUB_STEP_SUMMARY`.

    **Cette variable ne se laisse pas rediriger.** Une étape de workflow a beau
    la redéfinir dans son `env:`, le coureur garde la sienne : le rapport part
    alors dans le résumé de l'étape, et l'étape suivante — qui doit le publier —
    cherche un fichier qui n'existe pas. C'est précisément ce qui est arrivé le
    15 octobre 2026 : la veille tournait, le verdict existait, et la page de
    suivi restait vide. D'où `--rapport`, une adresse nommée par l'appelant, qui
    ne dépend d'aucune convention de la plateforme.
    """
    import os

    ecrits: list[Path] = []
    for chemin in list(fichiers or []) + ([os.environ["GITHUB_STEP_SUMMARY"]]
                                          if os.environ.get("GITHUB_STEP_SUMMARY") else []):
        ecrits.append(Path(chemin))
    if not ecrits:
        return ecrits
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
    texte = "\n".join(lignes) + "\n"
    for chemin in ecrits:
        chemin.parent.mkdir(parents=True, exist_ok=True)
        with chemin.open("a", encoding="utf-8") as rapport:
            rapport.write(texte)
    return ecrits


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analyseur.add_argument("--hote", choices=sorted(HOTES), action="append",
                           help="hôte à interroger (défaut : les deux)")
    analyseur.add_argument("--essais", type=int, default=3,
                           help="tentatives par adresse, pour un hôte endormi (défaut : 3)")
    analyseur.add_argument("--attente", type=float, default=15.0,
                           help="secondes entre deux tentatives (défaut : 15)")
    analyseur.add_argument("--rapport", action="append", metavar="FICHIER",
                           help="où écrire le rapport (en plus du résumé GitHub) ; "
                                "répétable, `-` pour la sortie standard")
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

    fichiers = [chemin for chemin in (options.rapport or []) if chemin != "-"]
    rapporter(verdicts, hotes, fichiers)
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
