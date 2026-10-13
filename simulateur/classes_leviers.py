"""simulateur/classes_leviers.py — les 5 classes de leviers, lisibles d'un coup d'œil.

Pourquoi ce module
------------------

Le catalogue compte 156 leviers répartis en 14 familles thématiques (fiscalité,
santé, régalien…). Classer par thème répond à la question « dans quel domaine
j'agis », jamais à celle que se pose d'abord un citoyen devant un budget :
**est-ce que ça fait entrer de l'argent, est-ce que ça évite une dépense, ou
est-ce que ça en engage ?**

Ce module ajoute cette lecture, et une seule, sans toucher au moteur :

  1. **recettes** — le levier fait entrer de l'argent (vert, symbole ``+``) ;
  2. **économies** — le levier existe pour *dépenser moins* à service égal
     (vert hachuré, symbole ``✂``) ;
  3. **depenses** — le levier engage de l'argent (rouge, symbole ``−``) ;
  4. **regles** — le levier change une règle, pas un compte (bleu, ``§``) ;
  5. **monde** — le levier décrit un choc extérieur subi (or, ``≈``).

La classe n'est **jamais déduite d'une opinion** : elle vient du catalogue
(``ligne`` budgétaire, ``champ`` moteur, famille) et, pour les cas limites, d'une
table d'affectations *motivées*, vérifiée par les tests. Deux conséquences :

* aucun levier n'est laissé de côté (le test le prouve) ;
* la règle générale se lit dans le code : un levier sans ``ligne`` **et** sans
  ``champ`` n'alimente aucun flux budgétaire — ce sont exactement les réglages
  institutionnels lus par ``nuances_institutionnelles.py`` ; les interrupteurs-
  drapeaux (``reforme_*``, ``verrouillage_*``, ``clause_*``) changent une règle,
  pas une ligne de dépenses.

Deux vigilances, écrites ici pour ne pas être oubliées
-----------------------------------------------------

1. **Le vert ne remplace pas le mot.** Une couleur ne doit jamais être le seul
   moyen de porter une information (règle de la charte M.R.S.C). Chaque classe
   fournit donc, avec sa couleur : un symbole, un libellé en toutes lettres et
   un motif de fond. L'interface peut ainsi rester lisible en niveaux de gris,
   à l'impression, en contraste renforcé et pour les daltonismes.
2. **Le montant affiché n'est pas une prévision.** Les totaux par classe
   proviennent du moteur (clés ``levier:<cle>`` et ``annee`` des flux annuels),
   montée en charge comprise : c'est une lecture du modèle, jamais un verdict.

Ordres de grandeur
------------------

Un montant en milliards d'euros ne dit rien à personne. Le module sait le
traduire en euros par ménage et par an, en **affichant son diviseur et son
statut de vérification** : l'ordre de grandeur est un outil de lecture, pas un
chiffre certifié. Voir ``DIVISEUR_MENAGES``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from simulateur.parametres import FAMILLES, LEVIERS, TYPE_INTERRUPTEUR

# ────────────────────────────────────────────────────────────────────────────
# 1. Les cinq classes
# ────────────────────────────────────────────────────────────────────────────

#: Sens financier d'une classe, du point de vue du budget public.
SENS_ENTREE = "entree"        # fait entrer de l'argent
SENS_ECONOMIE = "economie"    # évite une sortie d'argent
SENS_SORTIE = "sortie"        # engage de l'argent
SENS_AUCUN = "aucun"          # pas d'effet monétaire direct
SENS_SUBI = "subi"            # effet monétaire non décidé ici

#: Motifs de fond : la couleur ne porte jamais seule l'information.
MOTIF_UNI = "uni"
MOTIF_HACHURE = "hachure"
MOTIF_POINTILLE = "pointille"


@dataclass(frozen=True)
class ClasseLevier:
    """Une des cinq classes de leviers, telle que l'interface la présente."""

    cle: str
    ordre: int
    libelle: str
    libelle_court: str
    question: str
    definition: str
    sens: str
    symbole: str
    couleur: str
    couleur_html: str       # teinte de fond (rgba sur fond sombre)
    motif: str
    doctrine: str           # document du dépôt qui fonde la lecture budgétaire
    verdict: str            # ce que la classe dit du budget, en une phrase

    def en_dict(self) -> dict[str, Any]:
        return {
            "cle": self.cle,
            "ordre": self.ordre,
            "libelle": self.libelle,
            "libelle_court": self.libelle_court,
            "question": self.question,
            "definition": self.definition,
            "sens": self.sens,
            "symbole": self.symbole,
            "couleur": self.couleur,
            "couleur_html": self.couleur_html,
            "motif": self.motif,
            "doctrine": self.doctrine,
            "verdict": self.verdict,
            "nb_leviers": 0,          # complété par `catalogue_classes()`
            "familles": [],           # complété par `catalogue_classes()`
            "exemples": [],           # complété par `catalogue_classes()`
        }


#: Les cinq classes, dans l'ordre d'affichage. Les couleurs sont celles de la
#: charte M.R.S.C adaptées au fond sombre du simulateur (accents que le site
#: applique déjà à la page intégrée) : vert #9bc77a, rouge #ff9295, bleu
#: #91b2e6, or #f2c15f. Aucune teinte étrangère n'est introduite.
CLASSES: dict[str, ClasseLevier] = {
    "recettes": ClasseLevier(
        cle="recettes", ordre=1,
        libelle="Recettes nouvelles",
        libelle_court="Recettes",
        question="Qui paie, et combien cela rapporte-t-il ?",
        definition=(
            "Mesures qui font entrer de l'argent dans les caisses publiques : "
            "fiscalité, recouvrement de la fraude, extinction de niches "
            "inefficaces, accises. Le curseur règle l'intensité ; le montant lu "
            "est un gain annuel pour le budget."
        ),
        sens=SENS_ENTREE, symbole="+", couleur="#9bc77a",
        couleur_html="rgba(155,199,122,.14)", motif=MOTIF_UNI,
        doctrine="docs/02_RECETTES_ET_TRANSACTIONS.md",
        verdict="Fait entrer de l'argent",
    ),
    "economies": ClasseLevier(
        cle="economies", ordre=2,
        libelle="Économies d'efficacité",
        libelle_court="Économies",
        question="Qu'est-ce qu'on arrête de payer à vide ?",
        definition=(
            "Mesures dont la finalité est de réduire la dépense publique à "
            "service égal : doublons de structure, achats publics négociés, "
            "simplification administrative. Elles ne ferment pas de guichet : "
            "elles suppriment de la dépense redondante."
        ),
        sens=SENS_ECONOMIE, symbole="✂", couleur="#9bc77a",
        couleur_html="rgba(155,199,122,.10)", motif=MOTIF_HACHURE,
        doctrine="docs/03_ECONOMIES_ET_EFFICACITE_ETAT.md",
        verdict="Évite une sortie d'argent",
    ),
    "depenses": ClasseLevier(
        cle="depenses", ordre=3,
        libelle="Dépenses et investissements",
        libelle_court="Dépenses",
        question="À quoi sert l'argent engagé ?",
        definition=(
            "Mesures qui engagent de l'argent public : services publics, "
            "transferts aux ménages, investissement, réarmement — et aussi les "
            "baisses de prélèvements, qui coûtent au budget en rendant du "
            "pouvoir d'achat. Le curseur règle le montant annuel."
        ),
        sens=SENS_SORTIE, symbole="−", couleur="#ff9295",
        couleur_html="rgba(255,146,149,.13)", motif=MOTIF_UNI,
        doctrine="docs/04_POUVOIR_D_ACHAT_ET_TRAJECTOIRE.md",
        verdict="Engage de l'argent",
    ),
    "regles": ClasseLevier(
        cle="regles", ordre=4,
        libelle="Règles du jeu",
        libelle_court="Règles",
        question="Qui décide, qui contrôle, et dans quel délai ?",
        definition=(
            "Réformes institutionnelles et réglages de contre-pouvoir : motion "
            "de censure, référendum, parquet, délais, transparence. Ces leviers "
            "ne figurent sur aucune ligne budgétaire du modèle : ils changent "
            "la manière de décider, pas le montant dépensé."
        ),
        sens=SENS_AUCUN, symbole="§", couleur="#91b2e6",
        couleur_html="rgba(145,178,230,.12)", motif=MOTIF_POINTILLE,
        doctrine="docs/07_INSTITUTIONS_DE_LA_REPUBLIQUE_DROITS_ET_CHAMBRES_CONSULAIRES.md",
        verdict="Change les règles, pas les comptes",
    ),
    "monde": ClasseLevier(
        cle="monde", ordre=5,
        libelle="Monde subi",
        libelle_court="Monde",
        question="Qu'est-ce qui vient de l'extérieur ?",
        definition=(
            "Chocs extérieurs : pétrole, taux, change, tensions, blocus, "
            "cyberattaque. Ce ne sont pas des décisions de politique publique "
            "mais des hypothèses de contexte, utiles pour éprouver un plan — "
            "jamais pour vanter un résultat."
        ),
        sens=SENS_SUBI, symbole="≈", couleur="#f2c15f",
        couleur_html="rgba(242,193,95,.12)", motif=MOTIF_HACHURE,
        doctrine="docs/08_STRATE_GEOPOLITIQUE_ET_SCENARIOS_DE_GUERRE.md",
        verdict="Ne se décide pas ici",
    ),
}

#: Ordre d'affichage des classes.
ORDRE_CLASSES: tuple[str, ...] = tuple(
    cle for cle, _ in sorted(CLASSES.items(), key=lambda item: item[1].ordre)
)


# ────────────────────────────────────────────────────────────────────────────
# 2. Affectations motivées (les cas limites, un par un)
# ────────────────────────────────────────────────────────────────────────────

#: Levier → (classe, motif). Chaque ligne corrige une lecture automatique qui
#: tromperait un lecteur. Le motif est affiché par l'interface : rien n'est
#: classé en secret.
AFFECTATIONS_DOCUMENTEES: dict[str, tuple[str, str]] = {
    # ── Baisses de prélèvements : une recette en moins est une dépense ─────
    "tva_energie_5_5": (
        "depenses",
        "Baisse de TVA sur l'énergie : manque à gagner pour l'État, gain pour "
        "les ménages. Le médiateur du moteur porte d'ailleurs le nom de "
        "« baisse_tva_energie_5_5_mde » et se soustrait du solde.",
    ),
    "cheque_energie": (
        "depenses",
        "Classé dans la famille fiscalité, mais c'est un transfert versé aux "
        "ménages (≈ 150 € pour ≈ 5,7 millions de bénéficiaires, source citée "
        "au catalogue) : de l'argent qui sort.",
    ),
    "flat_tax_suppression": (
        "depenses",
        "Supprimer la flat tax fait monter l'imposition du capital mais baisse "
        "les recettes nettes en régime transitoire : le catalogue porte un "
        "facteur négatif (−4), donc un coût.",
    ),
    # ── Recettes qui ne viennent pas de la famille fiscalité ───────────────
    "taxe_comportements": (
        "recettes",
        "Accises tabac, alcool, sucre : la famille est « santé » (le but est "
        "sanitaire) mais la ligne budgétaire est une recette.",
    ),
    # ── Économies : les trois seuls leviers de dépense évitée ──────────────
    "fusion_doublons": (
        "economies",
        "Fusion des doublons territoriaux : le dossier de mandature (volet 3) "
        "la chiffre en +8 Md€/an d'économies de structure, sans fermer de "
        "guichet.",
    ),
    "commande_publique": (
        "economies",
        "Commande publique massifiée : 200 Md€ d'achats, 3 % de gain négocié "
        "= +6 Md€/an (volet 3). C'est une dépense évitée, pas une dépense "
        "nouvelle.",
    ),
    "simplification": (
        "economies",
        "Choc de simplification : normes redondantes, commissions et doublons "
        "de contrôle supprimés ; l'effet visé est une charge en moins, pour "
        "l'administration comme pour les entreprises.",
    ),
    # ── Compteurs déguisés en montants : ils ne mesurent pas des euros ─────
    "usage_49_3": (
        "regles",
        "Le curseur compte des recours au 49.3 par an, pas des milliards : le "
        "médiateur « usage_49_3 » est un compteur, lu comme un nombre par les "
        "formules de censure. La frontière avec « dépenses » est simple : un "
        "levier va en dépenses dès que le modèle lui attache une ligne de coût "
        "réelle (proportionnelle, convention citoyenne, anticorruption).",
    ),
    "charge_reformes_simultanees": (
        "regles",
        "Nombre de grands chantiers menés de front (0 à 16) : c'est une charge "
        "de pilotage pour le stress-test, pas un montant budgétaire.",
    ),
}


# ────────────────────────────────────────────────────────────────────────────
# 3. Lecture d'un levier : sa classe, son sens, ses exceptions
# ────────────────────────────────────────────────────────────────────────────

def est_drapeau(cle: str) -> bool:
    """Le levier est-il un interrupteur-drapeau (réforme), pas un montant ?

    Un drapeau se reconnaît sans liste écrite à la main : interrupteur, facteur
    de 1, aucune ligne budgétaire, et un champ qui n'est pas un montant en Md€
    (les montants du moteur finissent tous par ``_mde``). C'est la définition
    qui sert au classement **et** au contrôle croisé des tests.
    """
    levier = LEVIERS[cle]
    return (
        levier.type == TYPE_INTERRUPTEUR
        and levier.facteur == 1.0
        and levier.ligne is None
        and bool(levier.champ)
        and not str(levier.champ).endswith("_mde")
    )


def est_reglage_institutionnel(cle: str) -> bool:
    """Le levier est-il un réglage institutionnel sans flux budgétaire ?

    Aucune ligne budgétaire, aucun champ moteur : le levier n'alimente que la
    couche des nuances institutionnelles (seuils, délais, garde-fous). Le test
    des classes vérifie que ces 55 leviers sont exactement ceux-là.
    """
    levier = LEVIERS[cle]
    return levier.ligne is None and levier.champ is None


def classe_automatique(cle: str) -> str:
    """Ce que le catalogue dit d'un levier, **sans** affectation documentée.

    C'est la règle générale, dans l'ordre des tests :

    1. famille « Chocs mondiaux (exogènes) » → monde ;
    2. ni ligne ni champ → règles (réglages institutionnels) ;
    3. interrupteur-drapeau (réforme) → règles ;
    4. famille fiscalité (ménages, entreprises) → recettes ;
    5. le reste → dépenses.

    Les affectations documentées corrigent cette lecture (baisses de
    prélèvements, économies d'efficacité, compteurs déguisés en montants) :
    elles sont testées une par une, et aucune n'a le droit d'être un doublon
    silencieux de la règle générale.
    """
    if cle not in LEVIERS:
        raise KeyError(f"levier inconnu du catalogue : {cle!r}")
    levier = LEVIERS[cle]
    if levier.famille == "exogene_monde":
        return "monde"
    if est_reglage_institutionnel(cle):
        return "regles"
    if est_drapeau(cle):
        return "regles"
    if levier.famille in ("fiscalite_menages", "fiscalite_entreprises"):
        return "recettes"
    return "depenses"


def classe_de(cle: str) -> str:
    """Classe d'un levier : affectation documentée si elle existe, règle sinon."""
    if cle in AFFECTATIONS_DOCUMENTEES:
        return AFFECTATIONS_DOCUMENTEES[cle][0]
    return classe_automatique(cle)


def motif_classe(cle: str) -> str:
    """Motif affiché à côté de la classe : « règle générale » ou justification."""
    if cle in AFFECTATIONS_DOCUMENTEES:
        return AFFECTATIONS_DOCUMENTEES[cle][1]
    classe = classe_de(cle)
    levier = LEVIERS[cle]
    if classe == "monde":
        return "Famille « Chocs mondiaux (exogènes) » : hypothèse de contexte."
    if classe == "regles" and est_reglage_institutionnel(cle):
        return ("Aucune ligne budgétaire, aucun champ moteur : réglage de "
                "contre-pouvoir lu par la couche des nuances institutionnelles.")
    if classe == "regles":
        return ("Interrupteur de réforme : le champ est un drapeau (0/1), pas "
                "un montant en millions ou milliards.")
    if classe == "recettes":
        return (f"Famille « {FAMILLES[levier.famille]['libelle']} » : le champ "
                "est une recette encaissée par l'État.")
    return (f"Famille « {FAMILLES[levier.famille]['libelle']} » : le levier "
            "engage une dépense ou un transfert.")


def classe(cle: str) -> ClasseLevier:
    """Fiche complète de la classe d'un levier."""
    return CLASSES[classe_de(cle)]


def sens_du_montant(cle: str) -> str:
    """Sens budgétaire de la classe : ``+1`` entrée, ``−1`` sortie, ``0`` aucun."""
    sens = CLASSES[classe_de(cle)].sens
    if sens in (SENS_ENTREE, SENS_ECONOMIE):
        return "+1"
    if sens == SENS_SORTIE:
        return "-1"
    return "0"


def leviers_par_classe() -> dict[str, list[str]]:
    """Les clés de leviers de chaque classe, dans l'ordre du catalogue."""
    groupes: dict[str, list[str]] = {cle: [] for cle in ORDRE_CLASSES}
    for cle in LEVIERS:
        groupes[classe_de(cle)].append(cle)
    return groupes


def classes_du_catalogue() -> dict[str, str]:
    """Table ``levier → classe``, pour l'API et pour les tests."""
    return {cle: classe_de(cle) for cle in LEVIERS}


# ────────────────────────────────────────────────────────────────────────────
# 4. Totaux par classe : lire le moteur, pas l'intention
# ────────────────────────────────────────────────────────────────────────────

def _montants_leviers(flux: dict[str, Any]) -> dict[str, float]:
    """Extrait ``levier:<cle>`` d'un flux annuel du moteur."""
    montants: dict[str, float] = {}
    for nom, valeur in flux.items():
        if not nom.startswith("levier:") or not isinstance(valeur, (int, float)):
            continue
        montants[nom[len("levier:"):]] = float(valeur)
    return montants


#: Classes dont les montants sont des euros décidés ici. Les deux autres
#: n'entrent pas dans le solde : leurs valeurs (drapeaux 0/1, dollars du baril,
#: points de tension) ne sont pas des montants budgétaires, même si le
#: constructeur de flux les additionne comme tels — écart connu et affiché.
CLASSES_MONETAIRES: tuple[str, ...] = ("recettes", "economies", "depenses")

NOTE_HORS_BUDGET = (
    "Hors solde : ces leviers ne portent pas de montant budgétaire (drapeaux "
    "0/1 d'un côté, hypothèses de contexte de l'autre). Le constructeur de flux "
    "les additionne néanmoins comme des montants : l'écart est mesuré et "
    "affiché séparément, jamais fondu dans le solde."
)


def totaux_classe(flux: dict[str, Any]) -> dict[str, Any]:
    """Totaux par classe pour **un** flux annuel du moteur (une année).

    Le signe est conservé, jamais remplacé par une valeur absolue : un plan
    d'austérité baisse des budgets, ces baisses sont donc **négatives** dans la
    classe « dépenses » — les afficher en positif ferait passer une coupe pour
    une dépense. Chaque classe porte ainsi :

    * ``montant_mde`` — la somme signée des leviers actifs (le sens de lecture
      dépend de la classe : +17,5 de « recettes » est une recette, −31,9 de
      « dépenses » est une coupe de 31,9 Md€/an) ;
    * ``montant_absolu_mde`` — la somme des valeurs absolues, pour mesurer le
      volume remué sans prétendre à un solde ;
    * ``nb_actifs``, ``leviers``, ``familles``.

    Les classes « règles » et « monde » ne portent pas d'euros : leurs valeurs
    (drapeaux 0/1, dollars du baril, points de tension) vont dans
    ``montant_hors_budget_mde`` et n'entrent **jamais** dans le solde.
    """
    montants = _montants_leviers(flux)
    par_classe: dict[str, dict[str, Any]] = {}
    for cle in ORDRE_CLASSES:
        par_classe[cle] = {
            "cle": cle, "montant_mde": 0.0, "montant_absolu_mde": 0.0,
            "montant_hors_budget_mde": 0.0, "nb_actifs": 0, "leviers": [],
            "familles": [], "monetaire": cle in CLASSES_MONETAIRES,
        }
    for nom, montant in montants.items():
        if nom not in LEVIERS or montant == 0.0:
            continue
        cle = classe_de(nom)
        bloc = par_classe[cle]
        if cle in CLASSES_MONETAIRES:
            bloc["montant_mde"] += montant
            bloc["montant_absolu_mde"] += abs(montant)
        else:
            bloc["montant_hors_budget_mde"] += abs(montant)
        bloc["nb_actifs"] += 1
        bloc["leviers"].append({"cle": nom, "montant_mde": round(montant, 3)})
        famille = LEVIERS[nom].famille
        if famille not in bloc["familles"]:
            bloc["familles"].append(famille)
    for bloc in par_classe.values():
        bloc["montant_mde"] = round(bloc["montant_mde"], 3)
        bloc["montant_absolu_mde"] = round(bloc["montant_absolu_mde"], 3)
        bloc["montant_hors_budget_mde"] = round(bloc["montant_hors_budget_mde"], 3)
        bloc["leviers"].sort(key=lambda item: -abs(item["montant_mde"]))
    entree = par_classe["recettes"]["montant_mde"] + par_classe["economies"]["montant_mde"]
    sortie = par_classe["depenses"]["montant_mde"]
    return {
        "classes": par_classe,
        "entrees_mde": round(entree, 3),
        "sorties_mde": round(sortie, 3),
        "solde_mde": round(entree - sortie, 3),
        "hors_budget_mde": round(
            par_classe["regles"]["montant_hors_budget_mde"]
            + par_classe["monde"]["montant_hors_budget_mde"], 3),
        "note_hors_budget": NOTE_HORS_BUDGET,
        "recettes_moteur_mde": round(float(flux.get("recettes_nouvelles_mde", 0.0)), 3),
        "depenses_moteur_mde": round(float(flux.get("depenses_nouvelles_mde", 0.0)), 3),
        "annee": int(flux.get("annee", 0) or 0),
    }


def serie_classes(flux_annuels: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Totaux par classe pour chaque année d'une simulation."""
    return [totaux_classe(flux) for flux in (flux_annuels or [])]


# ────────────────────────────────────────────────────────────────────────────
# 5. Traduire les milliards : euros par ménage et par an
# ────────────────────────────────────────────────────────────────────────────

#: Diviseur retenu pour la traduction « Md€ → € par ménage et par an ».
#: Il s'agit d'un **ordre de grandeur**, pas d'un chiffre vérifié à la source
#: dans cette session : il est affiché avec son statut, et le dépôt garde sa
#: règle — un chiffre non vérifié se présente comme tel (voir
#: docs/VERIFICATION_DONNEES.md et la section « citizen » de la page).
DIVISEUR_MENAGES: dict[str, Any] = {
    "valeur": 30_000_000,
    "libelle": "≈ 30 millions de ménages",
    "statut": "ordre de grandeur à vérifier",
    "note": (
        "Diviseur utilisé pour donner un ordre de grandeur en euros par ménage "
        "et par an. À confirmer par une source Insee consultée directement "
        "avant toute reprise officielle ; le simulateur l'affiche comme une "
        "conversion indicative."
    ),
}


def euros_par_menage(montant_mde: float,
                     diviseur: int | None = None) -> float:
    """Convertit des Md€/an en euros par ménage et par an (ordre de grandeur)."""
    mde = float(montant_mde or 0.0)
    nb = int(DIVISEUR_MENAGES["valeur"] if diviseur is None else diviseur)
    if nb <= 0:
        raise ValueError("le diviseur de ménages doit être strictement positif")
    return round(mde * 1_000_000_000 / nb, 2)


# ────────────────────────────────────────────────────────────────────────────
# 6. Vue sérialisable pour l'interface
# ────────────────────────────────────────────────────────────────────────────

#: Nombre d'exemples de leviers cités par classe dans la vue publique.
EXEMPLES_PAR_CLASSE = 4


def catalogue_classes() -> dict[str, Any]:
    """Vue complète des classes, prête à être servie avec le catalogue."""
    groupes = leviers_par_classe()
    classes: list[dict[str, Any]] = []
    for cle in ORDRE_CLASSES:
        fiche = CLASSES[cle].en_dict()
        cles = groupes[cle]
        fiche["nb_leviers"] = len(cles)
        # Dérivé, jamais saisi : la page peut ainsi décider seule ce qui entre
        # dans un solde en euros et ce qui n'y entre pas.
        fiche["monetaire"] = cle in CLASSES_MONETAIRES
        familles: list[str] = []
        for levier_cle in cles:
            famille = LEVIERS[levier_cle].famille
            if famille not in familles:
                familles.append(famille)
        fiche["familles"] = [{"cle": f, "libelle": FAMILLES[f]["libelle"]} for f in familles]
        fiche["familles_nb"] = len(familles)
        # Exemples : les leviers les plus « unitaires » d'abord (un montant
        # significatif), puis l'ordre du catalogue — jamais un tri caché.
        def poids(item: str) -> tuple[float, int]:
            levier = LEVIERS[item]
            montant = abs(levier.facteur) * max(abs(levier.maximum or 0.0),
                                                abs(levier.minimum or 0.0), 1.0)
            return (-montant, list(LEVIERS).index(item))
        fiche["exemples"] = [
            {"cle": item, "libelle": LEVIERS[item].libelle}
            for item in sorted(cles, key=poids)[:EXEMPLES_PAR_CLASSE]
        ]
        classes.append(fiche)
    return {
        "definition": (
            "Chaque levier appartient à une seule classe. Le vert fait entrer de "
            "l'argent ou évite une dépense, le rouge engage de l'argent, le bleu "
            "change les règles, l'or vient de l'extérieur. Symbole, libellé et "
            "motif doublent la couleur : l'information reste lisible sans elle."
        ),
        "ordre": list(ORDRE_CLASSES),
        "classes": classes,
        "diviseur_menages": dict(DIVISEUR_MENAGES),
        "note_solde": (
            "Deux lectures coexistent et ne sont jamais confondues : celle des "
            "classes (recettes + économies − dépenses) et celle du moteur "
            "(recettes_nouvelles_mde − depenses_nouvelles_mde), qui range les "
            "leviers d'efficacité parmi les montants nouveaux. Les deux sont "
            "affichées."
        ),
    }


def verifier_classes() -> list[str]:
    """Contrôle interne du classement : retourne la liste des anomalies.

    Vide = chaque levier a une classe connue, chaque affectation documentée
    vise un levier réel, chaque réglage institutionnel est bien en « règles »,
    et la palette ne contient que les accents M.R.S.C.
    """
    anomalies: list[str] = []
    connues = set(ORDRE_CLASSES)
    for cle in LEVIERS:
        classe_cle = classe_de(cle)
        if classe_cle not in connues:
            anomalies.append(f"{cle} : classe inconnue « {classe_cle} »")
    for cle, (classe_cle, motif) in AFFECTATIONS_DOCUMENTEES.items():
        if cle not in LEVIERS:
            anomalies.append(f"affectation documentée pour un levier inconnu : {cle}")
            continue
        if classe_cle not in connues:
            anomalies.append(f"affectation documentée vers une classe inconnue : {cle}")
        if len(motif.strip()) < 40:
            anomalies.append(f"motif trop court pour être vérifiable : {cle}")
        if classe_cle == classe_automatique(cle):
            # Une exception qui ne corrige rien est un mensonge par omission :
            # elle laisse croire à un arbitrage là où le catalogue suffisait.
            anomalies.append(f"affectation documentée inutile (règle déjà suivie) : {cle}")
    for cle in LEVIERS:
        if est_reglage_institutionnel(cle) and classe_de(cle) != "regles":
            anomalies.append(f"réglage institutionnel classé hors « règles » : {cle}")
        if (est_drapeau(cle) and classe_de(cle) != "regles"
                and LEVIERS[cle].famille != "exogene_monde"):
            anomalies.append(f"interrupteur-drapeau classé hors « règles » : {cle}")
    couleurs_autorisees = {"#9bc77a", "#ff9295", "#91b2e6", "#f2c15f"}
    for fiche in CLASSES.values():
        if fiche.couleur not in couleurs_autorisees:
            anomalies.append(f"couleur hors charte M.R.S.C : {fiche.cle} → {fiche.couleur}")
        if not fiche.symbole.strip() or not fiche.libelle.strip():
            anomalies.append(f"classe sans symbole ou sans libellé : {fiche.cle}")
        if fiche.motif not in (MOTIF_UNI, MOTIF_HACHURE, MOTIF_POINTILLE):
            anomalies.append(f"motif inconnu : {fiche.cle} → {fiche.motif}")
    return anomalies
