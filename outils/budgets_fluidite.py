#!/usr/bin/env python3
"""outils/budgets_fluidite.py — les plafonds de poids du simulateur, écrits et tenus.

Pourquoi des plafonds, après les mesures
----------------------------------------

`outils/mesurer_fluidite.py` sait mesurer ; il ne sait pas refuser. Or une page ne
devient pas lente en un jour : elle grossit d'une section par passe, chaque ajout
paraissant léger au moment où il est fait — la section « Contre-pouvoirs, en
chiffres » a ajouté 7 603 octets compressés d'un seul coup, le 13 octobre 2026.
Un chiffre mesuré de temps en temps, mais jamais opposé à une limite, ne protège
de rien : il documente le glissement.

Ce fichier écrit la limite. La mesure reste l'outil qui la confronte.

Les quatre règles du budget
---------------------------

1. **On budgète ce que paie l'utilisateur.** L'unité est l'octet **compressé**
   réellement transféré, au niveau de compression du serveur
   (`simulateur/compression.py`, ``gzip -6``, et mieux encore en brotli là où il
   existe). Le poids du fichier sur le disque n'intéresse personne : personne ne
   le télécharge décompressé.
2. **On ancre avant de plafonner.** Chaque budget porte la mesure datée dont il
   vient ; son plafond vaut cette ancre plus une marge (10 % par défaut). Une
   croissance voulue se paie d'un **relèvement d'ancre dans un commit qui
   l'explique** : c'est un acte de revue, pas un glissement invisible.
3. **Le temps n'est pas budgété.** Une durée dépend de la machine qui mesure : un
   plafond de millisecondes échouerait au hasard sur un runner chargé, et une CI
   qui échoue au hasard n'est plus lue. Les durées sont mesurées et rapportées
   par `mesurer_fluidite.py` ; elles ne bloquent aucune livraison.
4. **Un budget muet n'est pas un budget.** Chaque plafond porte son motif
   (pourquoi ce poids compte) et sa sortie (ce qu'on fait s'il est franchi). Un
   plafond sans sortie est une opinion, et une opinion ne se vérifie pas.

Ce que ce module expose
-----------------------

* `BUDGETS` : la table des plafonds, une entrée par charge mesurable ;
* `ROUTES_MESUREES` : les routes du serveur et le budget auquel chacune répond,
  pour qu'aucune charge servie n'échappe à son plafond ;
* `mesures_hors_ligne()` : ce qui se mesure sans lancer de serveur (la page), et
  que les tests vérifient à chaque poussée ;
* `verifier()` : les dépassements et les anomalies d'une campagne de mesures ;
* `rapport_texte()` : le tableau lisible, celui que la CI imprime.

Usage :

    python3 outils/mesurer_fluidite.py --verifier
"""

from __future__ import annotations

import gzip
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from simulateur.compression import NIVEAU_GZIP  # noqa: E402
from simulateur.interface import HTML_PAGE  # noqa: E402

#: Date du dernier ancrage : la mesure dont viennent les ancres de ce fichier.
#: Écrite à la main, comme les ancres elles-mêmes — c'est ce qui les rend
#: datables en revue.
DATE_ANCRAGE = "2026-10-14"

#: Marge de travail par défaut. Le plan de renforcement demandait « la CI échoue
#: au-delà de +10 % » : c'est cette règle, appliquée à chaque charge.
MARGE_DEFAUT = 10

#: Bornes de la marge. En dessous de 5 %, le plafond casse à la première ligne
#: ajoutée et devient un irritant qu'on désactive ; au-dessus de 40 %, il ne
#: borne plus rien et devient un décor.
MARGE_MIN, MARGE_MAX = 5, 40

#: Longueur minimale d'un motif et d'une sortie : de quoi finir la phrase.
LONGUEUR_TEXTE = 40

#: Ce qu'on fait quand un plafond est franchi, écrit une fois par famille.
SORTIES = {
    "section": (
        "Mesurer la section ajoutée, la charger à l'approche de l'écran ou la "
        "replier derrière un bouton avant de relever l'ancre."
    ),
    "textes": (
        "Sortir les textes longs du JSON servi et les charger à la demande : le "
        "poids utile à l'écran est rarement tout le poids du registre."
    ),
    "ancre": (
        "Si la croissance est voulue, relever l'ancre et sa date dans un commit "
        "qui l'explique ; sinon, réduire avant de fusionner."
    ),
    "regenere": (
        "Régénérer index.html (python3 outils/generer-index-simulateur.py) avant "
        "de conclure : l'écart entre le fichier publié et le module est le premier suspect."
    ),
    "compression": (
        "Vérifier que la compression s'applique (Accept-Encoding, seuil de 512 o) "
        "avant d'accuser le contenu : sans elle, un poids doublé est un défaut, pas un budget."
    ),
}


@dataclass(frozen=True)
class Budget:
    """Un plafond de poids : une ancre datée, une marge, et la sortie si on dépasse."""

    #: Nom court, celui qui sert de clé dans les mesures et dans les rapports.
    cle: str
    #: Nom lisible à l'écran, tel qu'il apparaît dans le rapport de CI.
    libelle: str
    #: Octets compressés mesurés le jour de l'ancrage.
    ancre: int
    #: Pourquoi ce poids compte — ce qu'un dépassement abîmerait.
    motif: str
    #: Clé dans `SORTIES` : ce qu'on fait quand le plafond est franchi.
    sortie: str
    #: Marge appliquée à l'ancre pour obtenir le plafond.
    marge_pct: int = MARGE_DEFAUT
    #: « serveur » (il faut l'interroger), « les deux » (mesurable aussi hors
    #: ligne) ou « derive » (somme de ses membres).
    ou: str = "serveur"
    #: Membres d'un budget dérivé.
    membres: tuple[str, ...] = ()

    @property
    def plafond(self) -> int:
        """Le plafond : l'ancre majorée de sa marge, arrondie à l'octet supérieur."""
        return math.ceil(self.ancre * (1 + self.marge_pct / 100))

    @property
    def sortie_texte(self) -> str:
        """La sortie, résolue depuis `SORTIES`."""
        return SORTIES.get(self.sortie, "")


BUDGETS: tuple[Budget, ...] = (
    Budget(
        "page",
        "la page entière (le document HTML)",
        111_155,
        "Le document part avant tout le reste : chaque kilo-octet y est payé par "
        "chaque visiteur, y compris celui qui repart aussitôt.",
        "regenere",
        ou="les deux",
    ),
    Budget(
        "catalogue",
        "le catalogue des leviers",
        44_526,
        "Le plus gros JSON du démarrage : il porte les 156 leviers et leurs bornes, "
        "et conditionne le premier curseur bougé.",
        "textes",
    ),
    Budget(
        "contexte",
        "le contexte « instant T »",
        14_329,
        "Douze valeurs de référence et leur provenance : au-delà, c'est de la fiche "
        "explicative, pas de l'écran d'accueil.",
        "textes",
    ),
    Budget(
        "garde_fous",
        "les garde-fous du modèle",
        7_569,
        "Leur croissance doit rester celle des contrôles vérifiés, pas celle des "
        "commentaires qui les entourent.",
        "textes",
    ),
    Budget(
        "lexique",
        "le lexique en français ordinaire",
        13_233,
        "Charge d'un confort de lecture, servie en tâche de fond : son plafond "
        "borne ce que coûte une définition de plus.",
        "textes",
    ),
    Budget(
        "marches",
        "les cotations de marché",
        1_726,
        "Sept lignes : la petite charge qui doit rester petite. Un écart ici "
        "signalerait une erreur de conception, pas un besoin de place. Base "
        "minuscule, donc marge de 20 % : un plafond à 10 % casserait à la première "
        "cotation ajoutée, alors que le risque à surveiller est un dérapage.",
        "ancre",
        marge_pct=20,
    ),
    Budget(
        "objections",
        "le registre des objections",
        19_820,
        "Vingt-quatre objections longuement rédigées : si le registre double, c'est "
        "qu'on y a versé les fiches entières au lieu de les résumer.",
        "textes",
    ),
    Budget(
        "nuances",
        "les nuances institutionnelles",
        21_929,
        "Le registre des seuils et des verrous : il change quand le droit change, "
        "pas à chaque retouche de style.",
        "textes",
    ),
    Budget(
        "contrepouvoirs",
        "l'arithmétique des contre-pouvoirs",
        18_207,
        "Mécanismes, chambres et coalitions servis depuis le 13 octobre 2026 : ce "
        "plafond est la charge de la section qu'on vient d'ouvrir.",
        "section",
    ),
    Budget(
        "dynamiques",
        "les trajets et leurs battements",
        26_230,
        "Le registre le plus lourd après les bulles, chargé à l'approche de l'écran "
        "pour cette raison même.",
        "section",
    ),
    Budget(
        "instances",
        "les instances et les fentes",
        7_795,
        "Vingt-six instances et sept boucles : excusé comme écran, jamais comme "
        "charge — un registre non affiché reste un registre servi.",
        "section",
    ),
    Budget(
        "bulles",
        "le catalogue des bulles (une par levier)",
        169_866,
        "Le plus gros transfert du site : trois mégaoctets bruts, tout le texte "
        "explicatif des 156 leviers. Sans plafond, c'est ici que la page deviendrait lente.",
        "textes",
    ),
    Budget(
        "simuler_5ans",
        "une simulation complète sur 5 ans",
        44_014,
        "Le va-et-vient payé à chaque mouvement de curseur : la charge que "
        "l'utilisateur subit le plus souvent.",
        "textes",
    ),
    Budget(
        "simuler_10ans",
        "une simulation complète sur 10 ans",
        48_239,
        "Le même calcul sur dix ans : sa forme ne doit pas dériver d'une passe à "
        "l'autre, et 10 % suffisent à le dire.",
        "ancre",
    ),
    Budget(
        "premier_ecran",
        "ce que la page télécharge avant d'être utilisable",
        256_372,
        "La page, les sept charges du démarrage et la première simulation : le "
        "nombre qui décide si l'outil s'ouvre ou si l'on referme.",
        "section",
        ou="derive",
        membres=("page", "catalogue", "contexte", "garde_fous", "objections",
                 "lexique", "marches", "simuler_5ans"),
    ),
)

#: Les routes du serveur mesurées, et le budget auquel chacune répond. Cette
#: table est la seule source : le budget ne peut pas ignorer une route mesurée,
#: et la mesure ne peut pas oublier une charge budgétée (le contrôle
#: `tests/test_budgets_fluidite.py` compare les deux listes).
ROUTES_MESUREES: tuple[tuple[str, str], ...] = (
    ("/", "page"),
    ("/api/catalogue", "catalogue"),
    ("/api/contexte", "contexte"),
    ("/api/garde_fous", "garde_fous"),
    ("/api/lexique", "lexique"),
    ("/api/marches", "marches"),
    ("/api/objections", "objections"),
    ("/api/nuances", "nuances"),
    ("/api/contrepouvoirs", "contrepouvoirs"),
    ("/api/dynamiques", "dynamiques"),
    ("/api/instances", "instances"),
    ("/api/bulles?detail=resume", "bulles"),
)

#: Les routes que la page appelle et qu'on ne plafonne **pas** individuellement.
#: Ce n'est pas un oubli : c'est un choix, et un choix se motive comme une
#: excuse. La règle tenue par `tests/test_budgets_fluidite.py` : toute route
#: appelée par la page est soit plafonnée, soit déclarée ici avec sa raison —
#: et une raison qui ne tient plus est signalée comme une excuse périmée.
ROUTES_SANS_PLAFOND: dict[str, str] = {
    "bulle": (
        "Une bulle unitaire, ouverte au survol d'un levier : quelques centaines "
        "d'octets, déjà couverts en bloc par le plafond du catalogue des bulles."
    ),
    "conseil": (
        "La réponse du conseiller temps réel, écrite pour un réglage : une phrase "
        "par ricochet, dimensionnée par le réglage et non par la page."
    ),
    "constitution": (
        "Une fiche d'article ouverte au clic : son poids est celui du droit qu'elle "
        "cite, pas celui de l'écran — un plafond ici plafonnerait la loi."
    ),
    "donnees": (
        "Les données publiques collectées à la demande : leur volume appartient aux "
        "sources interrogées (Eurostat, BCE, Banque mondiale), pas à cette page."
    ),
    "run": (
        "Le rapport complet d'une exécution, demandé à la main et jamais au "
        "chargement : le plafonner reviendrait à plafonner ce que l'utilisateur a demandé."
    ),
}


def nom_de_route(chemin: str) -> str:
    """Le nom d'une route tel que la page l'appelle (« catalogue », « simuler »…)."""
    correspondance = re.match(r"^/api/([a-z_]+)", chemin)
    return correspondance.group(1) if correspondance else "page"


@dataclass(frozen=True)
class Mesure:
    """Un poids relevé, et d'où il vient."""

    cle: str
    octets: int
    provenance: str


@dataclass(frozen=True)
class Depassement:
    """Un plafond franchi : de combien, et dans quelle proportion."""

    cle: str
    libelle: str
    mesure: int
    plafond: int
    motif: str
    sortie: str

    @property
    def pourcent(self) -> float:
        """Le dépassement, en pourcentage du plafond."""
        return 100 * (self.mesure / self.plafond - 1)


@dataclass(frozen=True)
class Anomalie:
    """Un budget et une mesure qui ne se répondent pas."""

    cle: str
    message: str


def octets_compresses(charge: bytes, niveau: int = NIVEAU_GZIP) -> int:
    """Le poids compressé d'une charge, au niveau de compression du serveur."""
    return len(gzip.compress(charge, compresslevel=niveau))


def octets_de_la_page_du_module() -> int:
    """Le poids compressé du document que le serveur tient en mémoire."""
    return octets_compresses(HTML_PAGE.encode("utf-8"))


def octets_de_la_page_publiee() -> int:
    """Le poids compressé du fichier publié (`index.html`, servi par l'hébergeur)."""
    return octets_compresses((RACINE / "index.html").read_bytes())


def mesures_hors_ligne() -> list[Mesure]:
    """Ce qui se mesure sans serveur : la page, dans ses deux exemplaires.

    Les deux doivent tenir sous le même plafond — celui servi à l'adresse en
    ligne (`simulateur/interface.py`) et celui publié en fichier (`index.html`,
    servi par l'hébergeur statique) —, d'où le maximum.
    """
    servie = octets_de_la_page_du_module()
    publiee = octets_de_la_page_publiee()
    return [
        Mesure(
            "page",
            max(servie, publiee),
            f"HTML_PAGE {servie} o, index.html {publiee} o",
        )
    ]


def verifier(
    mesures: list[Mesure],
    *,
    budgets: tuple[Budget, ...] = BUDGETS,
    complet: bool = False,
) -> tuple[list[Depassement], list[Anomalie]]:
    """Confronte une campagne de mesures aux plafonds.

    `complet` dit si la campagne prétend avoir tout mesuré : dans ce cas, un
    plafond sans mesure est une anomalie. Hors ligne, la campagne est partielle
    par construction (la page seule) et les plafonds du serveur sont simplement
    non jugés.
    """
    par_cle: dict[str, Mesure] = {}
    anomalies: list[Anomalie] = []
    for mesure in mesures:
        if mesure.cle in par_cle:
            anomalies.append(Anomalie(mesure.cle, "charge mesurée deux fois dans la même campagne"))
        par_cle[mesure.cle] = mesure

    connues = {budget.cle for budget in budgets}
    for mesure in mesures:
        if mesure.cle not in connues:
            anomalies.append(Anomalie(
                mesure.cle,
                "charge mesurée sans plafond : lui en donner un dans BUDGETS, "
                "ou expliquer pourquoi elle n'en a pas",
            ))

    depassements: list[Depassement] = []
    signalees = {anomalie.cle for anomalie in anomalies}
    for budget in budgets:
        octets: int | None = None
        if budget.ou == "derive":
            if all(membre in par_cle for membre in budget.membres):
                octets = sum(par_cle[membre].octets for membre in budget.membres)
            elif complet and budget.cle not in signalees:
                absents = sorted(m for m in budget.membres if m not in par_cle)
                anomalies.append(Anomalie(
                    budget.cle,
                    f"budget dérivé incomplet : mesure(s) absente(s) — {', '.join(absents)}",
                ))
                signalees.add(budget.cle)
        elif budget.cle in par_cle:
            octets = par_cle[budget.cle].octets
        elif complet:
            anomalies.append(Anomalie(
                budget.cle,
                "plafond sans mesure : la campagne doit mesurer cette charge",
            ))
        if octets is not None and octets > budget.plafond:
            depassements.append(Depassement(
                budget.cle, budget.libelle, octets, budget.plafond,
                budget.motif, budget.sortie_texte,
            ))
    return depassements, anomalies


def _nombre(valeur: int) -> str:
    return f"{valeur:,}".replace(",", " ")


def _ligne(libelle: str, largeur: int, mesure: int, budget: Budget) -> str:
    marge = budget.plafond - mesure
    if marge >= 0:
        verdict = f"tenu, {_nombre(marge)} o de marge"
    else:
        verdict = f"DÉPASSÉ de {_nombre(-marge)} o ({100 * (mesure / budget.plafond - 1):+.1f} %)"
    return (f"  {libelle:<{largeur}} {_nombre(mesure):>9} "
            f"{_nombre(budget.plafond):>9}  {verdict}")


def rapport_texte(
    mesures: list[Mesure],
    *,
    budgets: tuple[Budget, ...] = BUDGETS,
    complet: bool = True,
) -> str:
    """Le tableau lisible d'une campagne : mesuré, plafond, marge, verdict."""
    par_cle = {mesure.cle: mesure for mesure in mesures}
    largeur = max(len(budget.libelle) for budget in budgets)
    lignes = [
        f"Plafonds de poids — octets compressés transmis (gzip -{NIVEAU_GZIP}), "
        f"ancres du {DATE_ANCRAGE}",
        f"  {'charge':<{largeur}} {'mesuré':>9} {'plafond':>9}  verdict",
        f"  {'-' * largeur} {'-' * 9} {'-' * 9}  {'-' * 30}",
    ]
    for budget in budgets:
        if budget.ou == "derive":
            if all(membre in par_cle for membre in budget.membres):
                octets = sum(par_cle[membre].octets for membre in budget.membres)
                lignes.append(_ligne(budget.libelle, largeur, octets, budget))
            else:
                lignes.append(f"  {budget.libelle:<{largeur}} {'—':>9} "
                              f"{_nombre(budget.plafond):>9}  somme non mesurable ici")
        elif budget.cle in par_cle:
            lignes.append(_ligne(budget.libelle, largeur, par_cle[budget.cle].octets, budget))
        elif complet:
            lignes.append(f"  {budget.libelle:<{largeur}} {'—':>9} "
                          f"{_nombre(budget.plafond):>9}  plafond sans mesure")
        else:
            lignes.append(f"  {budget.libelle:<{largeur}} {'—':>9} "
                          f"{_nombre(budget.plafond):>9}  non jugé hors ligne "
                          f"(ancre : {_nombre(budget.ancre)} o)")
    for mesure in mesures:
        lignes.append(f"      {mesure.cle} : {mesure.provenance}")

    depassements, anomalies = verifier(mesures, budgets=budgets, complet=complet)
    lignes.append("")
    if depassements:
        lignes.append(f"{len(depassements)} plafond(s) franchi(s) :")
        for depassement in depassements:
            lignes.append(f"  · {depassement.libelle} — {depassement.motif}")
            lignes.append(f"    sortie : {depassement.sortie}")
    if anomalies:
        lignes.append(f"{len(anomalies)} anomalie(s) de budget :")
        for anomalie in anomalies:
            lignes.append(f"  · {anomalie.cle} : {anomalie.message}")
    if not depassements and not anomalies:
        nombre = sum(1 for budget in budgets if budget.ou != "derive")
        lignes.append(
            f"Aucun dépassement, aucune anomalie ({nombre} plafonds dans la table)."
        )
    return "\n".join(lignes)


def main() -> int:
    """Rapport hors ligne : la page seule, ce que les tests vérifient."""
    mesures = mesures_hors_ligne()
    print(rapport_texte(mesures, complet=False))
    depassements, anomalies = verifier(mesures, complet=False)
    return 1 if (depassements or anomalies) else 0


if __name__ == "__main__":
    raise SystemExit(main())
