"""simulateur/prospective.py — ce que le modèle peut dire d'un avenir daté.

Trois documents du dépôt portent chacun un morceau d'avenir, et jusqu'ici aucun
ne se parlait :

* `docs/CONFLITS_RISQUES_SYSTEMIQUES_2026.md` (§ 7) écrit **quatre fenêtres de
  veille** à partir du 3 octobre 2026 — « des horizons, pas des dates de guerre »,
  choisies pour organiser la surveillance, non déduites d'un modèle ;
* `docs/AUDIT_LACUNES_GEOPOLITIQUES.md` tient le **registre des lacunes** qui
  bloquent toute revendication prédictive — six P0, un P1 refermé le 15 octobre
  2026 — avec, pour chacune, le critère de résolution qui la fermerait ;
* `docs/RD_VALIDATION_TEMPORELLE.md` donne le **protocole** d'évaluation :
  millésimes disponibles à une date, découpage chronologique gelé, abstention,
  fréquence de base et compétence.

Et le moteur, lui, simule **cinq ou dix ans** depuis le jour où on ouvre la page.
Ce module fait la seule chose qui manquait : **croiser les deux, en dates**, pour
que la page puisse répondre à une question simple — « jusqu'où vais-je, et qu'est-ce
que cet horizon rencontre ? » — sans jamais transformer une fenêtre de veille en
prévision ni un indice heuristique en probabilité.

Trois règles, dans l'esprit du dépôt
------------------------------------

1. **une fenêtre documentée porte sa source** — document et section. Ce module ne
   réécrit pas le document : il le cite. Le texte des scénarios, des signaux et
   des critères est celui du document, au mot près, et un contrôle le vérifie ;
2. **une borne imprécise se dit imprécise.** Le document date ses fenêtres au
   **mois** (« octobre 2031 ») quand le modèle calcule au **jour**. Le croisement
   publie donc sa **marge en jours**, et l'annonce (`a_un_mois_pres`) quand le
   verdict tient à cette imprécision : « couverte, à deux jours près » n'est pas
   « couverte », et le lecteur a le droit de le savoir ;
3. **un statut de lacune ne se décide pas dans le code.** Le module déclare ce
   que dit le document ; un contrôle refuse qu'il s'attribue une guérison que
   l'audit n'a pas écrite, et que l'audit referme une lacune que le code dit
   encore ouverte. Le code propose, le document daté dispose.

Ce que ce module ne fait pas : il ne prédit rien, il ne convertit aucun indice en
probabilité, et il ne comble aucune lacune. Il dit où s'arrête l'horizon du
modèle, ce que la veille documentée y fait tomber, et ce qui manque encore pour
qu'une revendication prédictive soit défendable.

Usage :

    python3 -m simulateur.prospective                # le rapport, ancré sur le jour
    python3 -m simulateur.prospective --depart 2026-10-03 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date

#: Le point de départ des fenêtres : tel qu'écrit dans le document (« Point de
#: départ : 3 octobre 2026 »). C'est une donnée du document, pas du code.
DATE_DES_FENETRES = date(2026, 10, 3)

#: Le document des fenêtres, et la section qui les porte. Cités, jamais recopiés
#: en silence : les contrôles relisent le fichier pour vérifier l'accord.
DOCUMENT_FENETRES = "docs/CONFLITS_RISQUES_SYSTEMIQUES_2026.md"
SECTION_FENETRES = "§ 7 — Fenêtres temporelles plausibles : des horizons, pas des dates de guerre"

#: Le document des lacunes, et sa section de registre.
DOCUMENT_LACUNES = "docs/AUDIT_LACUNES_GEOPOLITIQUES.md"
SECTION_LACUNES = "§ 3 — Ce qui manque encore : registre priorisé"

#: Les deux horizons que le moteur sait simuler : une mandature, deux mandatures.
HORIZONS: tuple[tuple[int, str], ...] = (
    (5, "une mandature"),
    (10, "deux mandatures consécutives"),
)

#: Les trois verdicts d'un croisement, et leur sens exact :
#:  * `entierement`   — la fenêtre entière tient dans l'horizon ;
#:  * `partiellement` — l'horizon n'en couvre qu'une partie (fenêtre ouverte, ou
#:    fermée après la fin de l'horizon) ;
#:  * `hors_horizon`  — la fenêtre commence après la fin de l'horizon.
COUVERTURES = ("entierement", "partiellement", "hors_horizon")

#: Les statuts d'une lacune. `refermee` ne se déclare jamais tout seul : il faut
#: que le document porte la date de fermeture (règle 3).
STATUTS = ("ouverte", "partiellement_traitee", "refermee")

#: La précision d'une borne, telle que le document l'écrit : un jour, un mois, ou
#: rien du tout (fenêtre ouverte).
PRECISIONS = ("jour", "mois", "aucune")

#: Le seuil d'imprécision : une borne datée au mois vaut, au mieux, à trente et un
#: jours près. Un verdict qui tient dans cette bande est annoncé comme tel.
JOURS_D_UN_MOIS = 31


@dataclass(frozen=True)
class Fenetre:
    """Une fenêtre de veille, telle que le document la décrit."""

    #: Nom court, stable, utilisé par les mesures et les rapports.
    cle: str
    #: Le scénario possible sous conditions — le texte du document.
    libelle: str
    #: La borne d'ouverture, ramenée au premier jour quand le document dit « avril 2027 ».
    debut: date
    debut_precision: str
    #: La borne de fermeture — `None` quand la fenêtre est ouverte (« après octobre 2031 »).
    fin: date | None
    fin_precision: str
    #: Ce qui renforcerait l'alerte, et ce qui la contredirait — le texte du document.
    signaux_qui_renforcent: str
    signaux_contraires: str

    @property
    def source(self) -> str:
        """D'où vient cette fenêtre : document et section, cités."""
        return f"{DOCUMENT_FENETRES}, {SECTION_FENETRES}"


#: Les quatre fenêtres du document § 7, dans son ordre. Les bornes datées au mois
#: sont ramenées au **premier jour du mois** : c'est la lecture la plus favorable à
#: la couverture, et le croisement publie sa marge pour que le lecteur puisse en
#: juger. Les libellés et les signaux sont ceux du document.
FENETRES: tuple[Fenetre, ...] = (
    Fenetre(
        cle="incident_majeur",
        libelle="Incident majeur dans un théâtre déjà tendu, extension régionale "
                "en jours ou semaines",
        debut=date(2026, 10, 3), debut_precision="jour",
        fin=date(2027, 4, 3), fin_precision="jour",
        signaux_qui_renforcent="Combats directs confirmés entre puissances, "
                               "représailles répétées, rupture des canaux",
        signaux_contraires="Cessez-le-feu observé, enquêtes, désengagement, "
                           "échanges militaires rétablis",
    ),
    Fenetre(
        cle="crises_simultanees",
        libelle="Deux crises simultanées compliquent la médiation et les engagements",
        debut=date(2027, 4, 1), debut_precision="mois",
        fin=date(2028, 10, 1), fin_precision="mois",
        signaux_qui_renforcent="Mobilisations durables, extension d'un blocus, "
                               "engagements militaires croisés",
        signaux_contraires="Accords sectoriels, transparence des exercices, "
                           "rétablissement des routes",
    ),
    Fenetre(
        cle="fragmentation_prolongee",
        libelle="Fragmentation et confrontation prolongée, éventuellement multi-théâtres",
        debut=date(2028, 10, 1), debut_precision="mois",
        fin=date(2031, 10, 1), fin_precision="mois",
        signaux_qui_renforcent="Érosion persistante des mécanismes de limitation et "
                               "répétition d'incidents non contenus",
        signaux_contraires="Nouveaux accords vérifiables, réduction des incidents, "
                           "coopération de crise",
    ),
    Fenetre(
        cle="ordres_suivants",
        libelle="Plusieurs ordres internationaux possibles, dont stabilisation",
        debut=date(2031, 11, 1), debut_precision="mois",
        fin=None, fin_precision="aucune",
        signaux_qui_renforcent="Impossible de dater sérieusement un basculement avec "
                               "cette méthode",
        signaux_contraires="Réévaluer plutôt qu'extrapoler une tendance indéfiniment",
    ),
)


@dataclass(frozen=True)
class Lacune:
    """Une lacune du registre priorisé, et son statut déclaré."""

    #: Le rang du registre : P0 bloque toute revendication prédictive, P1 rend les
    #: mécanismes plus réalistes, P2 est une extension.
    priorite: str
    #: L'intitulé de la lacune, tel que le document l'écrit.
    libelle: str
    #: Le critère de résolution proposé par le document — cité au mot près.
    critere: str
    #: `ouverte`, `partiellement_traitee` ou `refermee`.
    statut: str
    #: Ce qui soutient le statut déclaré : un fichier du dépôt, et le symbole qui
    #: répond à la lacune quand il y en a un. Un contrôle vérifie que le fichier
    #: existe et que le symbole s'y trouve : une preuve citée doit être lisible.
    preuve: str
    #: La date de fermeture, quand le document la porte.
    fermee_le: str | None = None


#: Les six lacunes P0 — celles qui bloquent une revendication prédictive — et le
#: P1 refermé le 15 octobre 2026, gardé comme témoin du mécanisme de fermeture.
#: Les statuts ci-dessous sont une lecture des preuves citées ; `refermee` exige
#: en plus l'accord du document, vérifié par les contrôles.
LACUNES: tuple[Lacune, ...] = (
    Lacune(
        priorite="P0",
        libelle="Cible prédictive non définie",
        critere="Définition observable, horizon, unité géographique et règle de "
                "labellisation publiés",
        statut="partiellement_traitee",
        preuve="simulateur/validation_temporelle.py (CIBLES, Observation : cible, "
               "unité, fenêtre et règle de labellisation d'un corpus synthétique)",
    ),
    Lacune(
        priorite="P0",
        libelle="Aucun jeu historique calibré",
        critere="Jeu versionné, provenance, couverture et licence documentées",
        statut="ouverte",
        preuve="aucun jeu réel n'est importé : le corpus de démonstration est "
               "synthétique et le signale",
    ),
    Lacune(
        priorite="P0",
        libelle="Dates de disponibilité et révisions absentes",
        critere="Table « connue à la date t » et test automatisé contre les fuites "
                "temporelles",
        statut="partiellement_traitee",
        preuve="simulateur/validation_temporelle.py (preuve_disponibilite, "
               "disponibilite, ingestion : une observation ne sert qu'à partir du "
               "moment où elle était disponible)",
    ),
    Lacune(
        priorite="P0",
        libelle="Pas de cas négatifs / fréquence de base",
        critere="Échantillon incluant crises contenues et périodes sans escalade",
        statut="partiellement_traitee",
        preuve="simulateur/validation_temporelle.py (frequence_de_base, "
               "competence_brier, avertissements_echantillon)",
    ),
    Lacune(
        priorite="P0",
        libelle="Absence de validation prospective/hors échantillon",
        critere="Découpage chronologique gelé, référence simple, erreurs et "
                "calibration publiées",
        statut="partiellement_traitee",
        preuve="simulateur/validation_temporelle.py (evaluer : découpage "
               "chronologique, abstention, deux références simples) — sur un corpus "
               "synthétique : aucun modèle calibré n'est publié",
    ),
    Lacune(
        priorite="P0",
        libelle="Coûts économiques incomplets",
        critere="Comptes ressources/emplois, coût d'acquisition, financement et "
                "absence de double comptage",
        statut="partiellement_traitee",
        preuve="simulateur/innovation_prospective.py (StockResilience, "
               "compte_ressources_emplois_resilience : comptes complets, "
               "CAPEX 30,9 Md€ et OPEX 1,65 Md€/an)",
    ),
    Lacune(
        priorite="P1",
        libelle="Indice nucléaire non calibré",
        critere="Renommer/documenter les concepts, pas de probabilité d'emploi sans "
                "méthode défendable",
        statut="refermee",
        preuve="simulateur/seuils.py (indices heuristiques non calibrés, unité /100)",
        fermee_le="15 octobre 2026",
    ),
)


def _jours(nombre: int) -> str:
    """« 1 jour », « 1 657 jours » : le nombre et son accord, écrits ensemble."""
    return f"{nombre:,}".replace(",", "\u202f") + (" jour" if abs(nombre) == 1 else " jours")


def fin_d_horizon(depart: date, annees: int) -> date:
    """La fin d'un horizon de `annees` ans : même jour, `annees` ans plus tard.

    Un 29 février n'existe pas dans toutes les années : l'horizon se ferme alors
    le 28 — un jour plus tôt, jamais un jour de plus, parce qu'un horizon ne
    s'allonge pas d'une bizarrerie de calendrier.
    """
    if annees < 1:
        raise ValueError("un horizon se compte en années entières positives")
    try:
        return depart.replace(year=depart.year + annees)
    except ValueError:                       # 29 février : l'année cible n'en a pas
        return depart.replace(year=depart.year + annees, day=28)


@dataclass(frozen=True)
class Croisement:
    """Une fenêtre documentée confrontée à un horizon du modèle."""

    fenetre: Fenetre
    annees: int
    fin_horizon: date
    verdict: str
    #: Jours entre la fermeture de la fenêtre et la fin de l'horizon — positif
    #: quand la fenêtre se ferme **avant** la fin de l'horizon. `None` quand la
    #: fenêtre est ouverte ou hors de l'horizon.
    marge_jours: int | None
    #: Vrai quand le verdict tient à une borne que le document date au mois :
    #: la couverture est alors vraie « à un mois près », et le dit.
    a_un_mois_pres: bool
    #: La phrase publiée — écrite depuis les dates, jamais recopiée.
    phrase: str


def _marge_imprecise(fenetre: Fenetre, marge: int | None) -> bool:
    """Le verdict dépend-il d'une borne datée au mois ?

    On regarde la borne qui décide du verdict : la fermeture de la fenêtre pour un
    verdict « entièrement », son ouverture pour un « hors horizon ». Si cette borne
    est datée au mois et que la marge tient dans ce mois, le verdict est vrai **à
    un mois près** — et le croisement doit le dire.
    """
    if marge is None or abs(marge) >= JOURS_D_UN_MOIS:
        return False
    if marge >= 0:
        return fenetre.fin_precision == "mois"
    return fenetre.debut_precision == "mois"


def couverture(fenetre: Fenetre, depart: date, annees: int) -> Croisement:
    """Ce qu'un horizon de `annees` ans, ouvert le `depart`, fait de la fenêtre."""
    fin_horizon = fin_d_horizon(depart, annees)
    recul = (fenetre.debut - fin_horizon).days

    if recul > 0:
        return Croisement(
            fenetre=fenetre, annees=annees, fin_horizon=fin_horizon,
            verdict="hors_horizon", marge_jours=None,
            a_un_mois_pres=_marge_imprecise(fenetre, -recul),
            phrase=f"hors de l'horizon : la fenêtre s'ouvre le {fenetre.debut.isoformat()}, "
                   f"{_jours(recul)} après la fin de l'horizon "
                   f"({fin_horizon.isoformat()}).",
        )

    if fenetre.fin is None:
        return Croisement(
            fenetre=fenetre, annees=annees, fin_horizon=fin_horizon,
            verdict="partiellement", marge_jours=None, a_un_mois_pres=False,
            phrase="partiellement couverte : son début tombe dans l'horizon, mais elle n'a "
                   "aucune fin datée — l'horizon n'en couvre qu'un morceau, et le document "
                   "ne dit pas lequel.",
        )

    marge = (fin_horizon - fenetre.fin).days
    verdict = "entierement" if marge >= 0 else "partiellement"
    imprecise = _marge_imprecise(fenetre, marge)
    if verdict == "entierement":
        phrase = (f"entièrement dans l'horizon : la fenêtre se ferme le "
                  f"{fenetre.fin.isoformat()}, {_jours(marge)} avant la fin de l'horizon "
                  f"({fin_horizon.isoformat()}).")
    else:
        phrase = (f"partiellement couverte : la fenêtre se ferme le "
                  f"{fenetre.fin.isoformat()}, {_jours(-marge)} après la fin de l'horizon "
                  f"({fin_horizon.isoformat()}).")
    if imprecise:
        phrase += (" Le document date cette borne au mois, pas au jour : la couverture "
                   "est vraie à un mois près.")
    return Croisement(fenetre=fenetre, annees=annees, fin_horizon=fin_horizon,
                      verdict=verdict, marge_jours=marge, a_un_mois_pres=imprecise,
                      phrase=phrase)


def phrase_de_l_horizon(depart: date, annees: int) -> str:
    """Ce qu'un horizon rencontre : combien de fenêtres, et ce qu'il en reste.

    La phrase est **composée** depuis les croisements — jamais écrite à la main —
    pour qu'un changement de date ou de document la change, au lieu de la laisser
    mentir en silence.
    """
    croisements = [couverture(fenetre, depart, annees) for fenetre in FENETRES]
    entieres = [c for c in croisements if c.verdict == "entierement"]
    dehors = [c for c in croisements if c.verdict == "hors_horizon"]
    partielles = [c for c in croisements if c.verdict == "partiellement"]
    fin = fin_d_horizon(depart, annees)
    morceaux = [f"Du {depart.isoformat()} au {fin.isoformat()}"]
    morceaux.append(f"{len(entieres)} des {len(croisements)} fenêtres de veille documentées "
                    f"tombent entièrement dans cet horizon")
    if partielles:
        cles = ", ".join(c.fenetre.cle for c in partielles)
        morceaux.append(f"{len(partielles)} n'y tombe que partiellement ({cles})")
    if dehors:
        cles = ", ".join(c.fenetre.cle for c in dehors)
        morceaux.append(f"{len(dehors)} commence après la fin de l'horizon ({cles})")
    if len(entieres) == len(croisements):
        morceaux.append("rien de la veille documentée ne sort de cet horizon")
    return " : ".join(morceaux[:1]) + " — " + " ; ".join(morceaux[1:]) + "."


def horodatage_des_fenetres() -> str:
    """Le point de départ des fenêtres, tel que le document l'écrit."""
    return DATE_DES_FENETRES.isoformat()


def compte_des_lacunes() -> dict[str, int]:
    """Le registre compté par statut — l'état de ce qui manque, en trois nombres."""
    comptes = dict.fromkeys(STATUTS, 0)
    for lacune in LACUNES:
        comptes[lacune.statut] += 1
    return comptes


def registre(depart: date) -> dict:
    """Le registre complet, pour l'API et la page.

    `depart` est la date d'ouverture de l'horizon — le jour où l'on simule. Elle
    n'est jamais devinée ici : c'est l'appelant qui la donne, ce qui rend le
    registre reproductible et le contrôle possible sur des dates fixes.
    """
    horizons = [{"annees": annees, "libelle": libelle,
                 "fin": fin_d_horizon(depart, annees).isoformat()}
                for annees, libelle in HORIZONS]
    fenetres = []
    for fenetre in FENETRES:
        croisements = {str(annees): couverture(fenetre, depart, annees)
                       for annees, _ in HORIZONS}
        fenetres.append({
            "cle": fenetre.cle,
            "libelle": fenetre.libelle,
            "debut": fenetre.debut.isoformat(),
            "debut_precision": fenetre.debut_precision,
            "fin": fenetre.fin.isoformat() if fenetre.fin else None,
            "fin_precision": fenetre.fin_precision,
            "signaux_qui_renforcent": fenetre.signaux_qui_renforcent,
            "signaux_contraires": fenetre.signaux_contraires,
            "source": fenetre.source,
            "couverture": {annees: {"verdict": c.verdict, "marge_jours": c.marge_jours,
                                    "a_un_mois_pres": c.a_un_mois_pres,
                                    "phrase": c.phrase,
                                    "fin_horizon": c.fin_horizon.isoformat()}
                           for annees, c in croisements.items()},
        })
    lacunes = [{"priorite": lacune.priorite, "libelle": lacune.libelle,
                "critere": lacune.critere, "statut": lacune.statut,
                "preuve": lacune.preuve, "fermee_le": lacune.fermee_le}
               for lacune in LACUNES]
    return {
        "depart": depart.isoformat(),
        "fenetres_datees_du": horodatage_des_fenetres(),
        "source_fenetres": f"{DOCUMENT_FENETRES}, {SECTION_FENETRES}",
        "source_lacunes": f"{DOCUMENT_LACUNES}, {SECTION_LACUNES}",
        "horizons": horizons,
        "fenetres": fenetres,
        "lacunes": lacunes,
        "lacunes_par_statut": compte_des_lacunes(),
        "phrases_des_horizons": {str(annees): phrase_de_l_horizon(depart, annees)
                                 for annees, _ in HORIZONS},
        "avertissement": "Registre de dates, pas de prévisions : les fenêtres sont un plan "
                         "de veille écrit dans un document du dépôt, non déduites d'un "
                         "modèle ; les indices du modèle sont heuristiques et non calibrés. "
                         "Aucune probabilité n'est calculée ici.",
    }


def resume_des_lacunes() -> str:
    """Le registre en une phrase, accordée : « 2 ouvertes, 4 partiellement traitées, … »."""
    accords = {
        "ouverte": ("ouverte", "ouvertes"),
        "partiellement_traitee": ("partiellement traitée", "partiellement traitées"),
        "refermee": ("refermée", "refermées"),
    }
    comptes = compte_des_lacunes()
    morceaux = [f"{nombre} {accords[statut][1 if nombre > 1 else 0]}"
                for statut, nombre in comptes.items() if nombre]
    return ", ".join(morceaux) + " — aucune revendication prédictive n'est permise tant qu'une " \
                                  "lacune P0 reste ouverte."


def lignes(depart: date) -> list[str]:
    """Le rapport lisible — ce que la ligne de commande imprime."""
    sortie = [f"**Prospective** : horizon ouvert le {depart.isoformat()} ; fenêtres de veille "
              f"documentées à partir du {horodatage_des_fenetres()} "
              f"({DOCUMENT_FENETRES})."]
    for annees, libelle in HORIZONS:
        fin = fin_d_horizon(depart, annees)
        sortie.append(f"\n## Horizon {annees} ans ({libelle}) — jusqu'au {fin.isoformat()}")
        sortie.append(phrase_de_l_horizon(depart, annees))
        for fenetre in FENETRES:
            croisement = couverture(fenetre, depart, annees)
            marque = {"entierement": "✅", "partiellement": "◐",
                      "hors_horizon": "⛔"}[croisement.verdict]
            sortie.append(f"- {marque} {fenetre.cle} ({croisement.verdict}) : "
                          f"{croisement.phrase}")
    sortie.append("\n## Ce qui bloque encore : " + resume_des_lacunes())
    for lacune in LACUNES:
        marque = {"ouverte": "⛔", "partiellement_traitee": "◐", "refermee": "✅"}[lacune.statut]
        fermeture = f" (refermée le {lacune.fermee_le})" if lacune.fermee_le else ""
        sortie.append(f"- {marque} {lacune.priorite} {lacune.libelle} — {lacune.statut}"
                      f"{fermeture} ; preuve : {lacune.preuve}.")
    return sortie


def main(argv: list[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analyseur.add_argument("--depart", default=date.today().isoformat(),
                           help="date d'ouverture de l'horizon (AAAA-MM-JJ)")
    analyseur.add_argument("--json", action="store_true", help="le registre complet, en JSON")
    args = analyseur.parse_args(argv)
    try:
        depart = date.fromisoformat(args.depart)
    except ValueError:
        print(f"date illisible : {args.depart!r} (attendu AAAA-MM-JJ)", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(registre(depart), ensure_ascii=False, indent=2))
        return 0
    for ligne in lignes(depart):
        print(ligne)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
