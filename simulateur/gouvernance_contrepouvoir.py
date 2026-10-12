"""
simulator/gouvernance_contrepouvoir.py — l'arithmétique des contre-pouvoirs.

`simulateur/constitution_analysee.py` répond à « que dit l'article ? ». Ce module
répond à la question qui suit, celle qui décide en pratique : **« à combien de voix,
de signatures ou de jours cela revient-il, et qu'est-ce qui peut faire échouer la
manœuvre ? »**

Trois objets, et rien de plus :

* `Verrou` — un seuil écrit dans le texte : une assiette (membres de l'assemblée,
  suffrages exprimés, électeurs inscrits, jours de délai), une fraction, un mode de
  calcul. C'est lui qui transforme « un dixième des membres » en `58` députés.
* `Mecanisme` — une manœuvre institutionnelle complète (censurer, engager par
  l'article 49 alinéa 3, dissoudre, saisir le Conseil, faire porter un texte par
  ordonnance…). Elle précise qui agit, à quelle condition, quels verrous elle
  franchit, **ce qui peut la faire échouer** et **ce qu'elle déclenche ensuite**.
* Les fonctions de calcul — `seuils_pour`, `tableau_des_seuils`, `blocages_possibles`,
  `chaine_de_reaction`, `diagnostic`.

Ce que ce module ne fait pas : il ne prédit pas l'issue. Il dit de combien de voix une
coalition a besoin et combien elle en a — la suite relève du paramétrage de
l'utilisateur et des hypothèses du modèle. Un mécanisme au vert n'est pas une promesse
de réussite : c'est une arithmétique possible.

 Convention : les nombres d'octobre 2026 (sièges pourvus, groupes, seuils de groupe)
 sont consignés dans `ETAT_ASSEMBLEES` et datés, parce qu'ils sont la seule partie de
 ce module susceptible de devenir fausse sans que la Constitution change.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

#: Date d'observation de l'état des assemblées (XVIIᵉ législature, renouvellement
#: sénatorial du 27 septembre 2026).
DATE_ETAT_ASSEMBLEES = "2026-10-12"
DATE_ETAT_ASSEMBLEES_NOTE = (
    "L'arithmétique des seuils ne bouge pas quand une législature change : ce sont "
    "les effectifs et les groupes qui vieillissent. Cette table est donc datée, et "
    "la page publique affiche la date en même temps que les nombres."
)

#: Nombre de sièges constitutionnellement possibles.
SIEGES_THEORIQUES: dict[str, int] = {"assemblee_nationale": 577, "senat": 348}
SIEGES_THEORIQUES["congres"] = sum(SIEGES_THEORIQUES.values())
SIEGES_THEORIQUES["haute_cour"] = SIEGES_THEORIQUES["congres"]

#: Effectifs réels constatés à la date ci-dessus (sièges vacants pris en compte :
#: trois circonscriptions de la XVIIᵉ législature n'étaient pas pourvues).
SIEGES_POURVUS: dict[str, int] = {"assemblee_nationale": 574, "senat": 348}
SIEGES_POURVUS["congres"] = sum(SIEGES_POURVUS.values())
SIEGES_POURVUS["haute_cour"] = SIEGES_POURVUS["congres"]

#: Le texte dit « majorité des membres composant l'Assemblée » : l'assiette est donc
#: l'effectif légal (577), pas le nombre de sièges pourvus — c'est ce qui rend une
#: censure légèrement plus facile quand des sièges sont vacants.
ASSIETES: dict[str, str] = {
    "membres_assemblee_nationale": "577 députés (effectif légal, art. 24)",
    "membres_assemblee_nationale_pourvus": "députés effectivement en siège",
    "membres_senat": "348 sénateurs (effectif légal, art. 24)",
    "membres_congres": "députés et sénateurs réunis (925 au maximum)",
    "suffrages_exprimes_congres": "suffrages exprimés au Congrès (les blancs et nuls "
                                  "sortent du décompte, art. 89)",
    "electeurs_inscrits": "électeurs inscrits sur les listes",
    "suffrages_exprimes": "suffrages exprimés au scrutin",
    "jours": "jours calendaires",
    "semaines": "semaines",
    "mois": "mois",
    "pourcentage": "pourcentage d'une base",
    "regle": "règle sans seuil chiffré",
    "occurrences": "occurrences",
    "heures": "heures",
}

#: Inscription des citoyens sur les listes (milliers) : sert aux seuils de
#: référendum et de RIP. 49 000 000 environ pour 2026 (source : registre national ;
#: arrondi volontaire, un seuil électoral ne se discute pas au millier près).
ELECTEURS_INSCRITS = 49_000_000


@dataclass(frozen=True)
class Verrou:
    """Un seuil écrit dans le texte, réduit en arithmétique."""

    cle: str
    nom: str
    article: str
    assiette: str
    regle: str = "fraction_au_moins"      # fraction_au_moins | fraction_stricte | majorite_absolue | fixe | bornes
    numerateur: int = 1
    denominateur: int = 1
    valeur: int = 0                      # pour regle == "fixe" (délais, nombre de motions)
    unite: str = ""                      # vide = unité déduite de l'assiette
    texte: str = ""
    sens: str = "atteindre"              # "atteindre" | "ne_pas_depasser" | "entre"

    def base(self, effectifs: dict[str, int] | None = None) -> int:
        donnees = effectifs or {}
        if self.assiette in donnees:
            return int(donnees[self.assiette])
        return {
            "membres_assemblee_nationale": SIEGES_THEORIQUES["assemblee_nationale"],
            "membres_assemblee_nationale_pourvus": SIEGES_POURVUS["assemblee_nationale"],
            "membres_senat": SIEGES_THEORIQUES["senat"],
            "membres_congres": SIEGES_THEORIQUES["congres"],
            "suffrages_exprimes_congres": SIEGES_THEORIQUES["congres"],
            "electeurs_inscrits": ELECTEURS_INSCRITS,
            "suffrages_exprimes": SIEGES_THEORIQUES["congres"],
            "jours": 0, "semaines": 0, "mois": 0, "pourcentage": 0,
            "regle": 0, "occurrences": 0, "heures": 0,
        }.get(self.assiette, 0)

    def seuil(self, effectifs: dict[str, int] | None = None) -> int:
        """Valeur du seuil dans l'unité de l'assiette (voix, signatures, jours)."""
        if self.regle == "fixe":
            return self.valeur
        base = self.base(effectifs)
        if self.regle == "majorite_absolue":
            return base // 2 + 1
        if self.denominateur <= 0:  # pragma: no cover - garde de fabrique
            return 0
        cible = self.numerateur * base / self.denominateur
        if self.regle == "fraction_stricte":
            return int(math.floor(cible)) + 1
        return int(math.ceil(cible))

    def en_dict(self, effectifs: dict[str, int] | None = None) -> dict[str, Any]:
        base = self.base(effectifs)
        seuil = self.seuil(effectifs)
        unite = self.unite or {"jours": "jours", "semaines": "semaines", "mois": "mois",
                               "regle": "règle", "occurrences": "occurrences",
                               "heures": "heures"}.get(
            self.assiette, "voix ou signatures" if base else "unités"
        )
        fraction = (
            f"{self.numerateur}/{self.denominateur}"
            if self.regle.startswith("fraction")
            else {"majorite_absolue": "majorité absolue", "fixe": "valeur fixée par le texte"}.get(
                self.regle, self.regle
            )
        )
        return {
            "cle": self.cle,
            "nom": self.nom,
            "article": f"Article {self.article}",
            "regle": fraction,
            "assiette": ASSIETES.get(self.assiette, self.assiette),
            "base": base,
            "seuil": seuil,
            "unite": unite,
            "sens": self.sens,
            "formule": self.formule(base, seuil),
            "texte": self.texte,
        }

    def formule(self, base: int, seuil: int) -> str:
        if self.regle == "fixe":
            unite = self.unite or ASSIETES.get(self.assiette, "")
            return f"{self.valeur} {unite}".strip()
        if not base:
            return self.texte or "aucune base chiffrée : la règle s'applique à tout moment"
        operateur = "≥" if self.sens == "atteindre" else "≤"
        return f"seuil {seuil} {operateur}, sur une assiette de {base}"


#: Les verrous du régime. Un seul endroit où le calcul est fait : si le texte
#: bouge, on corrige ici et le modèle suit.
_VERROUS_BRUTS: tuple[Verrou, ...] = (
    Verrou("censure_signatures", "Signatures nécessaires pour déposer une motion de censure", "49",
           "membres_assemblee_nationale", numerateur=1, denominateur=10,
           texte="« Une telle motion n'est recevable que si elle est signée par au moins un dixième des "
                 "membres de l'Assemblée nationale. »", ),
    Verrou("censure_voix", "Voix favorables pour renverser le Gouvernement", "49",
           "membres_assemblee_nationale", regle="majorite_absolue",
           texte="La motion est adoptée « à la majorité des membres composant l'Assemblée » ; seuls les "
                 "votes favorables sont recensés, s'abstenir revient donc à maintenir le gouvernement."),
    Verrou("censure_delai", "Délai avant le vote de la motion", "49", "heures", regle="fixe", valeur=48,
           unite="heures",
           texte="Le vote ne peut avoir lieu que quarante-huit heures après le dépôt.",
           sens="ne_pas_depasser"),
    Verrou("censure_plafond_motions", "Motions de censure par session ordinaire", "49", "occurrences",
            regle="fixe", valeur=3, unite="motions signées par un même député",
            texte="Un membre du Parlement ne peut signer plus de trois motions de censure au cours d'une "
                  "même session ordinaire (une par session extraordinaire).", sens="ne_pas_depasser"),
    Verrou("49_3_delai_motion", "Délai pour renverser un 49.3 : dépôt de la motion", "49", "heures",
           regle="fixe", valeur=24, unite="heures",
           texte="Le projet est considéré comme adopté sauf si une motion est déposée dans les vingt-quatre "
                 "heures et mise en votation.", sens="ne_pas_depasser"),
    Verrou("49_3_plafond_texte", "Usages autorisés pour un texte ordinaire par session", "49", "jours",
           regle="fixe", valeur=1,
           texte="Le Premier ministre peut recourir à cette procédure « pour un autre projet ou une "
                 "proposition de loi par session » — les projets de loi de finances et de financement de la "
                 "sécurité sociale ne sont pas comptés.", sens="ne_pas_depasser"),
    Verrou("dissolution_carence", "Délai pendant lequel une nouvelle dissolution est interdite", "12",
           "jours", regle="fixe", valeur=365,
           texte="« Ne peut avoir lieu une nouvelle dissolution dans l'année qui suit cette dissolution. »",
           sens="ne_pas_depasser"),
    Verrou("rip_signatures_parlement", "Signatures parlementaires pour un RIP (un cinquième)", "11",
           "membres_congres", numerateur=1, denominateur=5,
           texte="L'initiative est réunie « par un cinquième des membres des deux assemblées » : 116 "
                 "parlementaires sur 925."),
    Verrou("rip_signatures_electeurs", "Soutien demandé aux électeurs pour un RIP", "11",
           "electeurs_inscrits", numerateur=1, denominateur=10,
           texte="Le RIP est ouvert lorsque « un dixième des électeurs inscrits » le soutient, soit environ "
                 "4,9 millions de signatures."),
    Verrou("referendum_promulgation", "Délai de promulgation de la loi votée ou adoptée en référendum", "10",
           "jours", regle="fixe", valeur=15, texte="« Le Président de la République promulgue les lois dans "
           "les quinze jours qui suivent la transmission au Gouvernement de la loi définitivement adoptée » "
           "(et du résultat du référendum).", sens="ne_pas_depasser"),
    Verrou("promulgation_nouvelle_deliberation", "Délai laissé au Président pour demander une nouvelle "
           "délibération", "10", "jours", regle="fixe", valeur=15,
           texte="La demande de nouvelle délibération, qui ne peut être refusée, ouvre un second cycle ; la "
                 "nouvelle délibération ne peut être évitée que par le vote en termes identiques.",
           sens="ne_pas_depasser"),
    Verrou("saisine_conseil_delai", "Délai de jugement du Conseil constitutionnel saisi avant promulgation",
           "61", "jours", regle="fixe", valeur=30,
           texte="Le Conseil statue dans le mois ; huit jours en cas d'urgence déclarée par le Gouvernement."),
    Verrou("saisine_conseil_urgence", "Délai réduit en cas d'urgence (budget)", "61", "jours", regle="fixe",
           valeur=8, texte="« Il y a urgence pour le projet de loi de finances et le projet de loi de "
           "financement de la sécurité sociale déclarée par le Gouvernement. »", sens="ne_pas_depasser"),
    Verrou("saisine_conseil_signatures", "Députés ou sénateurs pouvant saisir le Conseil", "61",
           "membres_assemblee_nationale", regle="fixe", valeur=60,
           texte="Soixante députés ou soixante sénateurs — seuil fixé à 1974 pour les députés, 2008 pour "
                 "les sénateurs (projet de loi constitutionnelle de 1993 avorté) —, soit un peu plus de "
                 "10 % de l'effectif de l'Assemblée."),
    Verrou("budget_an_delai", "Délai de l'Assemblée nationale en première lecture (PLF)", "47", "jours",
           regle="fixe", valeur=40, texte="« Si l'Assemblée nationale ne s'est pas prononcée en première "
           "lecture dans le délai de soixante jours… » — quarante jours pour l'AN, quinze pour le Sénat, "
           "soixante-dix au total.", sens="ne_pas_depasser"),
    Verrou("budget_senat_delai", "Délai du Sénat saisi en deuxième vague (PLF)", "47", "jours",
           regle="fixe", valeur=15, texte="Le Sénat « doit statuer dans un délai de quinze jours ».",
           sens="ne_pas_depasser"),
    Verrou("budget_delai_total", "Délai au-delà duquel le budget peut être appliqué par ordonnance", "47",
           "jours", regle="fixe", valeur=70,
           texte="« Si le Parlement ne s'est pas prononcé dans un délai de soixante-dix jours, les "
                 "dispositions du projet peuvent être mises en vigueur par ordonnance. »",
           sens="ne_pas_depasser"),
    Verrou("plfss_delai_total", "Délai global pour le projet de loi de financement de la sécurité sociale",
           "47-1", "jours", regle="fixe", valeur=50,
           texte="Vingt jours pour l'Assemblée nationale, quinze pour le Sénat, cinquante au total, puis "
                 "ordonnance possible.", sens="ne_pas_depasser"),
    Verrou("irrecevabilite_financiere", "Base de l'irrecevabilité financière", "40", "regle", regle="fixe",
           valeur=0, unite="règle absolue",
           texte="Toute proposition ou amendement qui diminue une ressource publique ou crée ou aggrave une "
                 "charge publique est irrecevable : aucun seuil à franchir, la règle s'applique à toute "
                 "initiative parlementaire."),
    Verrou("irrecevabilite_competence_delai", "Délai du Conseil constitutionnel saisi d'une "
           "irrecevabilité de compétence", "41", "jours", regle="fixe", valeur=8,
           texte="Le Conseil constitutionnel « statue dans un délai de huit jours » sur le désaccord entre "
                  "le Gouvernement et le président de l'assemblée.", sens="ne_pas_depasser"),
    Verrou("procedure_acceleree_delai", "Délai minimal avant délibération (procédure accélérée)", "42",
           "jours", regle="fixe", valeur=15,
           texte="Six semaines en première lecture, quatre en seconde ; quinze jours avec la procédure "
                 "accélérée (PLF et PLFSS exceptés).", sens="ne_pas_depasser"),
    Verrou("cmp_composition", "Membres de la commission mixte paritaire", "45", "jours", regle="fixe",
           valeur=7, texte="Sept députés et sept sénateurs (plus sept suppléants) : la CMP est le lieu où se "
           "négocie le texte qui survivra."),
    Verrou("session_extraordinaire_signatures", "Députés pouvant décider la réunion en session "
           "extraordinaire", "29", "membres_assemblee_nationale", regle="majorite_absolue",
           texte="À la demande du Premier ministre ou de « la majorité des membres composant l'Assemblée "
                 "nationale », sur un ordre du jour déterminé."),
    Verrou("session_cloture_delai", "Durée maximale d'une session extraordinaire demandée par les "
           "députés", "29", "jours", regle="fixe", valeur=12,
           texte="Le décret de clôture intervient dès que l'ordre du jour est épuisé et au plus tard douze "
                 "jours après la réunion.", sens="ne_pas_depasser"),
    Verrou("etat_urgence_delai_parlement", "Délai avant autorisation parlementaire de l'état d'urgence",
           "36-1", "jours", regle="fixe", valeur=12,
           texte="Décrété en conseil des ministres pour douze jours ; au-delà, la prorogation ne peut être "
                 "autorisée que par la loi.", sens="ne_pas_depasser"),
    Verrou("etat_siege_delai_parlement", "Délai avant autorisation parlementaire de l'état de siège", "36",
           "jours", regle="fixe", valeur=12,
           texte="Décrété en conseil des ministres ; sa prorogation au-delà de douze jours ne peut être "
                 "autorisée que par le Parlement.", sens="ne_pas_depasser"),
    Verrou("opex_delai_autorisation", "Durée d'intervention armée sans autorisation du Parlement", "35",
           "mois", regle="fixe", valeur=4, unite="mois",
           texte="Information du Parlement dans les trois jours suivant le début de l'intervention ; au-delà "
                 "de quatre mois, la prolongation est soumise à son autorisation, l'Assemblée pouvant "
                 "decider en dernier ressort.",
           sens="ne_pas_depasser"),
    Verrou("commission_enquete_signature", "Demandes de commission d'enquête garanties par session", "51-2",
           "occurrences", regle="fixe", valeur=1, unite="commission par groupe et par session",
           texte="Chaque groupe peut faire inscrire une demande de commission d'enquête une fois par "
                 "session ordinaire (règlement de l'Assemblée) : l'opposition dispose donc d'une commission "
                 "garantie par session, sans seuil de signatures à réunir."),
    Verrou("lois_programmation_saisine_cee", "Saisine pour avis du CESE (plans et programmations)", "70",
           "regle", regle="fixe", valeur=0, unite="obligation sans délai suspensif",
           texte="« Tout plan ou tout projet de loi de programmation à caractère économique, social ou "
                 "environnemental lui est soumis pour avis » : obligation, sans effet suspensif."),
    Verrou("haute_cour_assemblees", "Voix dans chaque assemblée pour réunir la Haute Cour", "68",
           "membres_assemblee_nationale", numerateur=2, denominateur=3,
           texte="La proposition de réunion doit être adoptée « à la majorité des deux tiers des "
                 "membres » de chaque assemblée : 385 députés et 232 sénateurs."),
    Verrou("haute_cour_destitution", "Voix à la Haute Cour pour prononcer la destitution", "68",
           "membres_congres", numerateur=2, denominateur=3,
           texte="La Haute Cour statue à la majorité des deux tiers de ses membres ; seuls les votes "
                 "favorables sont recensés."),
    Verrou("congres_revision", "Suffrages exprimés au Congrès pour approuver une révision", "89",
           "suffrages_exprimes_congres", numerateur=3, denominateur=5, regle="fraction_au_moins",
           texte="« Le projet de révision n'est approuvé que s'il réunit la majorité des trois cinquièmes "
                 "des suffrages exprimés » : la base est réduite des votes blancs et nuls."),
    Verrou("nomination_veto", "Blocage d'une nomination en conseil des ministres", "13",
           "suffrages_exprimes", regle="fraction_au_moins", numerateur=3, denominateur=5,
           texte="Les commissions permanentes des deux assemblées additionnées : la nomination est "
                 "refusée si l'addition des votes négatifs représente trois cinquièmes des suffrages "
                 "exprimés dans chaque commission (imposée par la révision de 2008, jamais appliquée à "
                 "ce jour)."),
    Verrou("petition_locale", "Pétition demandant l'inscription à l'ordre du jour local", "72-1",
           "electeurs_inscrits", regle="fixe", valeur=0, unite="seuil fixé par la loi",
           texte="La loi fixe les conditions (code général des collectivités territoriales), pas la "
                 "Constitution : le seuil de signatures est un paramètre de réforme, pas un verrou "
                 "constitutionnel."),
    Verrou("referendum_local", "Référendum décisionnel local", "72-1", "electeurs_inscrits",
           regle="fixe", valeur=0, unite="seuil fixé par la loi organique",
           texte="La loi organique fixe les conditions : initiative de l'assemblée délibérante ou d'une "
                 "fraction des électeurs selon le texte organique."),
    Verrou("presidentielle_parrainages", "Présentations pour être candidat à l'élection présidentielle",
           "7", "jours", regle="fixe", valeur=500,
           texte="Cinq cents présentations d'élus (art. 3 de la loi du 6 novembre 1962), publiées au "
                 "Journal officiel le deuxième jeudi précédant le premier tour."),
    Verrou("vacance_delai_scrutin", "Délai pour procéder à une nouvelle élection présidentielle", "7",
           "jours", regle="fixe", valeur=35,
           texte="Le scrutin a lieu vingt à trente-cinq jours après la vacance ou l'empêchement ; les "
                 "pouvoirs intérimaires du président du Sénat excluent 49, 50 et 89.",
           sens="ne_pas_depasser"),
    Verrou("grace_regime", "Régime du droit de grâce", "17", "regle", regle="fixe", valeur=0,
           unite="compétence discrétionnaire",
           texte="Aucun délai ni seuil constitutionnel : le droit de grâce est discrétionnaire, l'amnistie "
                 "relève de la loi (34)."),
)

VERROUS: dict[str, Verrou] = {v.cle: v for v in _VERROUS_BRUTS}


@dataclass(frozen=True)
class Mecanisme:
    """Une manœuvre institutionnelle : qui agit, à quel prix, contre quoi, ensuite."""

    cle: str
    nom: str
    famille: str            # renverser | faire_adopter | bloquer | consulter | armer | exception
    resume: str
    articles: tuple[str, ...] = ()
    verrous: tuple[str, ...] = ()
    acteurs: str = ""
    condition: str = ""
    declenche: tuple[str, ...] = ()
    empeche_par: tuple[str, ...] = ()
    effet_modele: str = ""
    observation: str = ""
    cout: str = ""

    def en_dict(self, effectifs: dict[str, int] | None = None) -> dict[str, Any]:
        return {
            "cle": self.cle,
            "nom": self.nom,
            "famille": self.famille,
            "resume": self.resume,
            "articles": list(self.articles),
            "acteurs": self.acteurs,
            "condition": self.condition,
            "declenche": list(self.declenche),
            "empeche_par": list(self.empeche_par),
            "effet_modele": self.effet_modele,
            "observation": self.observation,
            "cout": self.cout,
            "seuils": [VERROUS[c].en_dict(effectifs) for c in self.verrous if c in VERROUS],
        }

#: Les manœuvres du régime, avec ce qui les rend possibles et ce qui les tue.
_MECANISMES_BRUTS: tuple[Mecanisme, ...] = (
    Mecanisme(
        "motion_censure", "Renverser le Gouvernement par une motion de censure", "renverser",
        "Une motion signée par un dixième des députés, votée quarante-huit heures plus tard à la majorité "
        "des membres composant l'Assemblée, sans que les abstentions comptent : le Gouvernement doit "
        "démissionner (article 50), mais rien n'oblige le Président à dissoudre.",
        articles=("49", "50", "12", "51"),
        verrous=("censure_signatures", "censure_voix", "censure_delai", "censure_plafond_motions"),
        acteurs="Au moins 58 députés signataires ; vote de la majorité absolue des 577 membres.",
        condition="Majorité des membres composant l'Assemblée (289 voix) — et non des suffrages exprimés.",
        declenche=("chute_gouvernement", "dissolution"),
        empeche_par=("article_49_3", "dissolution", "discipline_des_groupes"),
        effet_modele="Le moteur traduit la censure par un gouvernement démissionnaire, un gel du "
                     "calendrier des réformes et une prime de risque sur les taux.",
        observation="Une censure aboutie depuis 1958 hors 1962 : celle de septembre 2025 (gauche et "
                    "Rassemblement national). Deux motions rejetées le 23 janvier 2026 après les 49.3 "
                    "budgétaires.",
        cout="Élevé pour les signataires si aucune majorité alternative n'existe : le 28 septembre 2025, "
             "la censure a produit… un nouveau gouvernement et le même calendrier budgétaire.",
    ),
    Mecanisme(
        "article_49_3", "Faire adopter un texte sans vote (49 alinéa 3)", "faire_adopter",
        "Le Premier ministre engage la responsabilité du Gouvernement sur le vote d'un projet de loi de "
        "finances ou de financement de la sécurité sociale — et d'un autre texte par session — : le projet "
        "est considéré comme adopté sauf motion de censure déposée dans les vingt-quatre heures.",
        articles=("49", "47", "47-1", "50"),
        verrous=("49_3_delai_motion", "49_3_plafond_texte", "censure_voix"),
        acteurs="Le Premier ministre, après délibération en conseil des ministres.",
        condition="Un usage par session pour un texte ordinaire ; illimité pour les textes budgétaires ; "
                  "interdit pendant la vacance présidentielle (article 7).",
        declenche=("motion_censure",),
        empeche_par=("motion_censure",),
        effet_modele="Le moteur relie l'usage du 49.3 à une hausse immédiate du risque perçu et à "
                     "l'adoption du texte : c'est le levier `usage_49_3` du catalogue.",
        observation="Trois engagements en janvier 2026 pour le budget 2026 ; renoncement public affiché "
                    "ensuite pour les textes ordinaires, ce qui déplace le pouvoir d'agenda vers les "
                    "groupes et le Sénat.",
        cout="Le texte passe, la majorité reste : c'est l'économie du dispositif. Le prix est différé — "
              "dans l'opinion, dans la note souveraine, et à l'élection suivante.",
    ),
    Mecanisme(
        "engagement_responsabilite", "Demander à l'Assemblée d'approuver un programme (49 alinéa 1)",
        "renverser",
        "Le Premier ministre engage la responsabilité du Gouvernement devant l'Assemblée nationale sur son "
        "programme ou sur une déclaration de politique générale ; l'Assemblée peut la refuser, ce qui vaut "
        "désapprobation et donc démission (article 50).",
        articles=("49", "50"),
        verrous=("censure_voix",),
        acteurs="Le Premier ministre ; vote de l'Assemblée.",
        condition="Une défaite sur la question engage la même mécanique qu'une censure.",
        declenche=("chute_gouvernement",),
        empeche_par=("dissolution", "approbation_senat"),
        effet_modele="Le moteur ne modélise pas de « confiance » : le levier `sondage_majorite` "
                     "(réservé à la R&D) sert à mesurer l'écart entre soutiens affichés et majorité "
                     "réelle.",
        observation="Utilisée à l'envers dans l'histoire immédiate : une déclaration non approuvée équivaut "
                    "à une censure, ce qui explique la rareté de l'exercice.",
        cout="Faible pour le gouvernement s'il gagne ; total s'il perd.",
    ),
    Mecanisme(
        "approbation_senat", "Chercher une approbation au Sénat (49 alinéa 4)", "armer",
        "Le Premier ministre a la faculté de demander au Sénat l'approbation d'une déclaration de politique "
        "générale. Le Sénat ne peut ni renverser ni être renversé : sa voix n'a qu'un poids politique.",
        articles=("49", "24", "50"),
        acteurs="Le Premier ministre ; le Sénat (348 sénateurs, majorité à 175).",
        condition="Aucune conséquence juridique : un vote conforme, et rien de plus.",
        empeche_par=("droits_opposition",),
        effet_modele="Non chiffré dans le modèle : mechanisme de légitimité, pas de contrainte.",
        observation="Jamais utilisé depuis 1958 — alors qu'il dessine exactement la configuration de 2026 : "
                    "un gouvernement sans majorité absolue à l'Assemblée, face à un Sénat favorable.",
        cout="Coûteux à l'Assemblée, qui y lit un contournement.",
    ),
    Mecanisme(
        "referendum_legislatif", "Passer par le peuple (article 11)", "faire_adopter",
        "Le Président soumet au référendum tout projet de loi portant sur l'organisation des pouvoirs "
        "publics, les réformes économiques, sociales ou environnementales, la ratification d'un traité ; le "
        "Gouvernement peut prendre l'initiative, le Parlement peut proposer ; la loi référendaire n'est "
        "promulguée que dans les quinze jours du résultat.",
        articles=("11", "10", "60", "61", "5", "37"),
        verrous=("referendum_promulgation",),
        acteurs="Président de la République, sur délibération du Conseil des ministres ou sur proposition "
                "conjointe des deux assemblées (pour l'article 11 alinéa 4).",
        condition="Le référendum ne peut pas abroger une disposition déjà promulguée depuis moins d'un an ; "
                  "en cas de rejet, le Premier ministre doit démissionner (jurisprudence de 1969).",
        declenche=("censure_parlementaire", "decharge_gouvernement"),
        empeche_par=("censure_parlementaire", "abstention"),
        effet_modele="Le moteur n'a pas de levier référendaire : seule la voie 89 est chiffrée (cf. "
                     "`reforme_ric`, `usage_referendum_11` en pistes).",
        observation="Employé onze fois depuis 1958 ; le dernier usage date de 2000 (quinquennat). En 2026, "
                    "la menace d'un 11 a été agitée sur la fin de vie après la censure du texte par le "
                    "Sénat.",
        cout="Le gouvernement engage son existence politique sur chaque référendum.",
    ),
    Mecanisme(
        "rip", "Référendum d'initiative partagée (11 alinéas 5 à 7)", "armer",
        "Un cinquième des parlementaires, soutenu par un dixième des électeurs, peut déclencher la "
        "discussion d'une proposition de loi tendant à l'abrogation d'une disposition législative ; si le "
        "Parlement n'examine pas la proposition dans un délai de six mois, le Président peut la soumettre à "
        "référendum.",
        articles=("11", "60", "61", "39"),
        verrous=("rip_signatures_parlement", "rip_signatures_electeurs"),
        acteurs="116 parlementaires sur 925, puis 4,9 millions d'électeurs inscrits.",
        condition="Pas d'abrogation d'une disposition promulguée depuis moins d'un an ; saisine "
                  "obligatoire du Conseil constitutionnel sur la proposition.",
        declenche=("referendum_legislatif",),
        empeche_par=("obstruction_en_commission", "censure_parlementaire"),
        effet_modele="Non chiffré : le dépôt de l'EDM garde `reforme_ric` comme levier de réforme du "
                     "dispositif, pas de son activation.",
        observation="Jamais abouti : la procédure de 2019-2020 sur la privatisation d'Aéroports de Paris "
                    "a échoué sur le seuil parlementaire (245 signatures au Sénat et à l'AN, mais "
                    "l'irrecevabilité de 2020 a bloqué la suite).",
        cout="Faible pour les signataires, très élevé en temps : un an de collecte pour un résultat "
             "incertain.",
    ),
    Mecanisme(
        "dissolution", "Rendre son verdict aux électeurs (article 12)", "renverser",
        "Le Président de la République peut, après consultation du Premier ministre et des présidents des "
        "deux assemblées, dissoudre l'Assemblée nationale ; les élections ont lieu vingt à trente-cinq jours "
        "plus tard ; le Sénat et le Conseil constitutionnel restent en fonction.",
        articles=("12", "24", "28", "7", "16", "29"),
        verrous=("dissolution_carence",),
        acteurs="Le Président, après consultation (avis non conformes).",
        condition="Impossible pendant l'exercice des pouvoirs exceptionnels (16) ni en cas de vacance ; une "
                  "nouvelle dissolution interdite pendant un an.",
        declenche=("renouvellement_partiel", "election_legislatives"),
        empeche_par=("calendrier_electoral",),
        effet_modele="Dans le modèle, la dissolution est traitée comme une rupture de séquence : gel des "
                     "réformes, reprise de la dépense électorale, incertitude de taux (cf. "
                     "`calendrier_electoral`).",
        observation="Cinq dissolutions depuis 1958 (1962, 1968, 1981, 1988, 1997, 2024) — la dernière a "
                    "produit une Assemblée plus éclatée que la précédente, ce qui est la leçon à simuler.",
        cout="Le Président joue sa majorité ; 1997 est l'exemple canonique du pari perdu.",
    ),
    Mecanisme(
        "pouvoirs_exceptionnels", "Se saisir de tous les pouvoirs (article 16)", "exception",
        "Lorsque les institutions de la République, l'indépendance de la Nation, l'intégrité du territoire "
        "ou l'exécution des engagements internationaux sont menacées de manière grave et immédiate et que le "
        "fonctionnement régulier des pouvoirs publics constitutionnels est interrompu, le Président prend "
        "les mesures requises par ces circonstances, après consultation officielle.",
        articles=("16", "12", "7", "36", "36-1"),
        verrous=("vacance_delai_scrutin",),
        acteurs="Le Président, après consultation du Premier ministre, des présidents des assemblées et du "
                "Conseil constitutionnel.",
        condition="Pas de dissolution pendant l'exercice de l'article 16 ; l'Assemblée nationale ne peut "
                  "pas être dissoute ; le Parlement se réunit de plein droit ; au bout de trente jours, le "
                  "Conseil constitutionnel peut être saisi pour vérifier la continuation des circonstances.",
        declenche=("censure_parlementaire",),
        empeche_par=("controle_conseil_16", "fin_des_circonstances"),
        effet_modele="Le modèle ne simule pas l'article 16 : la variable `usage_article_16` est une "
                     "piste, non un levier chiffré.",
        observation="Une seule application pleine : du 23 avril au 29 septembre 1961. La saisine de 2026 "
                    "sur la gravité des circonstances a rappelé que le contrôle existe (décision du 22 "
                    "juillet 2026 ? à vérifier avant publication).",
        cout="Total : l'usage de l'article 16 est un aveu que le fonctionnement régulier est rompu.",
    ),
    Mecanisme(
        "etat_urgence", "Déplacer la police de l'ordre judiciaire vers l'administratif", "exception",
        "L'état d'urgence est déclaré en conseil des ministres pour douze jours, prorogé au-delà par la loi ; "
        "il ouvre perquisitions administratives, assignations à résidence, contrôles d'identité et "
        "fermetures d'établissements, sous le contrôle du juge administratif.",
        articles=("36-1", "36", "66", "16"),
        verrous=("etat_urgence_delai_parlement",),
        acteurs="Le Gouvernement (décret), puis le Parlement (loi de prorogation).",
        condition="Péril imminent résultant d'atteintes graves à l'ordre public ou calamités publiques.",
        declenche=("debats_prorogation", "contentieux_administratif"),
        empeche_par=("motion_censure", "censure_conseil"),
        effet_modele="Les régimes d'exception sont modélisés par une réduction de la contestation "
                     "enregistrée et une hausse du risque d'atteinte aux libertés (cf. "
                     "`regime_exception_jours`, en piste).",
        observation="Appliqué onze fois depuis 1955, dont 2015-2017 (post-attentats) et 2020 (état "
                    "d'urgence sanitaire, hors du champ de l'article 36-1).",
        cout="Le Parlement doit revenir toutes les douze semaines : la prorogation est un examen de "
             "conscience majoritaire.",
    ),
    Mecanisme(
        "ordonnances", "Légiférer par délégation (article 38)", "faire_adopter",
        "Le Gouvernement demande au Parlement l'autorisation de prendre, par ordonnances et dans un délai "
        "limité, des mesures normalement du domaine de la loi ; elles entrent en vigueur à publication et "
        "deviennent caduques si le projet de ratification n'est pas déposé dans le délai ; la ratification ne "
        "peut être que expresse.",
        articles=("38", "34", "37", "41", "74-1"),
        verrous=("irrecevabilite_competence_delai",),
        acteurs="Le Gouvernement, sur habilitation votée par le Parlement ; avis du Conseil d'État.",
        condition="Une habilitation se vote, donc se refuse : le texte peut tomber avant l'usage (49 "
                  "alinéa 2).",
        declenche=("censure_parlementaire", "contentieux_conseil_etat"),
        empeche_par=("motion_censure", "refus_de_ratification"),
        effet_modele="Le moteur traite l'ordonnance comme un accélérateur sans risque de censure "
                     "parlementaire du contenu, mais avec un risque de caducité (cf. "
                     "`recours_ordonnances`, en piste).",
        observation="Deux séries massives : 2017 (droit du travail, vingt-cinq ordonnances) et 2020 "
                    "(urgence sanitaire).",
        cout="Coûteux en légitimité quand il remplace le débat : c'est l'argument récurent des motions.",
    ),
    Mecanisme(
        "procedure_acceleree", "Supprimer une lecture (article 45 alinéa 3)", "faire_adopter",
        "Après une lecture par chaque assemblée, le Premier ministre peut décider qu'il n'en reste qu'une : "
        "les délais de six et quatre semaines tombent, la commission mixte paritaire peut être déclenchée "
        "plus tôt, l'Assemblée nationale peut avoir le dernier mot.",
        articles=("45", "42", "40", "44"),
        verrous=("procedure_acceleree_delai", "cmp_composition"),
        acteurs="Le Gouvernement, dès le dépôt ; les deux Conférences des présidents peuvent s'y opposer "
                "conjointement.",
        condition="Impossible pour la révision constitutionnelle et les lois organiques relatives au Sénat.",
        declenche=("commission_mixte_paritaire", "dernier_mot_assemblee"),
        empeche_par=("obstruction_en_seance", "navette_opposee"),
        effet_modele="Le modèle relie le rythme d'examen à la capacité d'obstruction : moins de navette, "
                     "moins d'amendements, mais un texte plus fragile au contentieux.",
        observation="L'accélération est devenue la norme : l'immense majorité des lois sont adoptées en "
                    "procédure accélérée.",
        cout="Faible juridiquement, élevé politiquement dans une assemblée sans majorité : le temps "
             "d'amendement est le seul pouvoir réel des groupes minoritaires.",
    ),
    Mecanisme(
        "commission_mixte_paritaire", "Négocier le texte en sept contre sept (article 45)", "bloquer",
        "Après deux lectures (une avec la procédure accélérée), le Premier ministre — ou les présidents des "
        "deux assemblées pour une proposition de loi — peut provoquer une CMP de sept députés et sept "
        "sénateurs ; son texte est voté sans amendement, sauf accord du Gouvernement ; en cas d'échec, une "
        "nouvelle lecture, puis le dernier mot de l'Assemblée nationale.",
        articles=("45", "46", "89"),
        verrous=("cmp_composition",),
        acteurs="Sept députés et sept sénateurs, à la proportionnelle des groupes.",
        condition="Pas de CMP pour la révision constitutionnelle (termes identiques exigés) ni pour les "
                  "lois organiques relatives au Sénat.",
        declenche=("dernier_mot_assemblee",),
        empeche_par=("majorite_relative", "veto_senat"),
        effet_modele="Le moteur note le passage en CMP comme un moment de compromis : il réduit la "
                     "probabilité de censure sur le texte mais augmente celle de réécriture.",
        observation="Le lieu où les chambres font tomber un texte embarrassant pour le Sénat, ou le "
                    "durcissent pour l'Assemblée.",
        cout="Aucun pour le Gouvernement s'il accepte les amendements : la CMP remplace souvent le 49.3.",
    ),
    Mecanisme(
        "irrecevabilite_financiere", "Tuer un amendement par l'article 40", "bloquer",
        "Les propositions et amendements des parlementaires ne sont pas recevables lorsque leur adoption "
        "aurait pour conséquence soit une diminution des ressources publiques, soit la création ou "
        "l'aggravation d'une charge publique.",
        articles=("40", "47", "34"),
        verrous=("irrecevabilite_financiere",),
        acteurs="Le Gouvernement ou le président d'assemblée, en séance.",
        condition="La « technique du gage » (compensation par une recette) reste admise ; le Gouvernement "
                  "peut lever le gage (44 alinéa 3).",
        empeche_par=("gage", "vote_bloque"),
        effet_modele="C'est la raison pour laquelle tant de mesures du dossier de mandature sont présentées "
                     "comme neutres : le modèle ne peut pas faire financer une dépense par un amendement "
                     "imaginaire.",
        observation="Arme de premier rang en navette budgétaire ; elle fonde l'asymétrie démocratique la "
                    "plus contestée : le Parlement peut créer un impôt, pas le supprimer.",
        cout="Aucun pour celui qui l'emploie, très élevé pour l'opposition.",
    ),
    Mecanisme(
        "vote_bloque", "Forcer un vote sans débat sur les amendements (44 alinéa 3)", "faire_adopter",
        "Si le Gouvernement le demande, l'assemblée saisie se prononce par un seul vote sur tout ou partie "
        "du texte en discussion, en ne retenant que les amendements proposés ou acceptés par le "
        "Gouvernement.",
        articles=("44", "40", "49"),
        acteurs="Le Gouvernement.",
        condition="N'engage pas la responsabilité : contrairement au 49.3, aucune motion ne peut suivre.",
        empeche_par=("rejet_du_texte",),
        declenche=(),
        effet_modele="Le modèle le traite comme l'instrument de prédilection d'un gouvernement sans "
                     "majorité absolue qui ne veut pas risquer la censure (cf. `usage_vote_bloque`, "
                     "piste).",
        observation="Son usage s'est banalisé avec les assemblées éclatées : il permet de faire vivre un "
                    "compromis sans exposer le gouvernement.",
        cout="Quasi nul sur le plan juridique ; il affaiblit le droit d'amendement, ce que le Conseil "
             "constitutionnel surveille (2018-772 DC).",
    ),
    Mecanisme(
        "saisine_conseil", "Armer le juge contre une loi (article 61)", "armer",
        "Soixante députés ou soixante sénateurs peuvent déférer une loi au Conseil constitutionnel avant sa "
        "promulgation ; la saisine suspend le délai de promulgation ; le Conseil statue dans le mois, ou "
        "huit jours en cas d'urgence.",
        articles=("61", "62", "10", "46", "61-1"),
        verrous=("saisine_conseil_signatures", "saisine_conseil_delai", "saisine_conseil_urgence"),
        acteurs="Un groupe d'opposition atteint le seuil dans la plupart des législatures (60 sièges).",
        condition="Le Conseil ne juge pas l'opportunité : il censure la violation de la Constitution.",
        declenche=("reecriture_du_texte", "censure_a_priori"),
        empeche_par=("urgence_declaree", "reecriture_anticipee"),
        effet_modele="La saisine est modélisée comme un délai de promulgation rallongé et un risque de "
                     "censure partielle (cf. `risque_censure` du moteur).",
        observation="Vingt-six saisines en 2025, onze au 23 juillet 2026 ; délai moyen constaté de dix-huit "
                    "jours en contrôle a priori, soixante-quatorze en QPC (bilan du Conseil).",
        cout="Gratuit en voix, coûteux en temps pour le gouvernement ; la censure est rarement totale.",
    ),
    Mecanisme(
        "qpc", "Contester une loi déjà votée (article 61-1)", "armer",
        "À l'occasion d'une instance, un justiciable peut soutenir qu'une disposition législative porte "
        "atteinte "
        "aux droits et libertés que la Constitution garantit ; le Conseil d'État ou la Cour de cassation "
        "renvoie, le Conseil constitutionnel statue ; la disposition est abrogée à compter de la publication "
        "ou d'une date ultérieure fixée par la décision.",
        articles=("61-1", "62", "63"),
        verrous=("saisine_conseil_delai",),
        acteurs="Tout justiciable, par avocat, dans une instance en cours.",
        condition="Caractère sérieux et nouveauté ; pas de saisine directe du citoyen ; pas de re-attaque "
                  "d'une disposition déjà déclarée conforme sans changement de circonstances.",
        declenche=("abrogation_differee", "reecriture_par_le_legislateur"),
        empeche_par=("filtrage_juridictions",),
        effet_modele="Non chiffré dans le modèle, mais il borne la portée des réformes : une mesure "
                     "sociale ou fiscale peut être annulée après son application.",
        observation="Quarante-neuf décisions au premier semestre 2026, dont dix-neuf censures (bilan du "
                    "Conseil, 30 juin 2026).",
        cout="Faible pour le requérant, très variable pour l'État : l'abrogation différée limite les "
             "remboursements dus.",
    ),
    Mecanisme(
        "referendum_local", "Décider localement par référendum (72-1)", "consulter",
        "Les projets de délibération ou d'acte relevant de la compétence d'une collectivité peuvent, à son "
        "initiative, être soumis par la voie du référendum à la décision des électeurs de cette collectivité, "
        "dans les conditions fixées par la loi organique.",
        articles=("72-1", "72", "34", "72-4"),
        verrous=("referendum_local",),
        acteurs="L'assemblée délibérante de la collectivité, ou une fraction des électeurs selon la loi "
                "organique.",
        condition="Portée limitée aux actes de la compétence de la collectivité.",
        declenche=("obligation_de_statuer",),
        empeche_par=("controle_legalite",),
        effet_modele="Le RIC local est le seul volet du référendisme que le droit permet sans révision : le "
                     "modèle le traite comme un paramètre communal (cf. `referendum_local`, piste).",
        observation="Plusieurs milliers de consultations locales depuis 2003, dont un nombre faible de "
                    "référendums décisionnels au sens de l'article 72-1 (à chiffrer avant publication).",
        cout="Faible ; mais le résultat oblige l'assemblée à statuer dans un délai organique.",
    ),
    Mecanisme(
        "petition_72_1", "Imposer une question à l'ordre du jour local (72-1)", "consulter",
        "La loi fixe les conditions dans lesquelles les électeurs d'une collectivité peuvent, par pétition, "
        "demander l'inscription à l'ordre du jour de l'assemblée délibérante d'une question relevant de sa "
        "compétence.",
        articles=("72-1", "72", "48"),
        verrous=("petition_locale",),
        acteurs="Les électeurs de la collectivité, par pétition.",
        condition="Le seuil de signatures est fixé par la loi ordinaire, pas par la Constitution : c'est un "
                  "paramètre de réforme, et donc un levier pour un législateur volontaire.",
        empeche_par=("irrecevabilite_formelle",),
        effet_modele="Non chiffré ; sert d'argument au levier `reforme_ric` sur le volet local.",
        observation="La loi du 13 août 2004 a créé la pétition, sans décret d'application longtemps : son "
                    "usage réel est marginal (à vérifier).",
        cout="Quasi nul — ce qui explique qu'il soit si peu utilisé et si peu craint.",
    ),
    Mecanisme(
        "commission_enquete", "Contrôler en éclairant (51-2)", "armer",
        "Des commissions d'enquête peuvent être créées au sein de chaque assemblée pour recueillir des "
        "éléments d'information, dans les conditions prévues par la loi ; les témoins sont entendus sous "
        "serment.",
        articles=("51-2", "24", "51-1", "34"),
        verrous=("commission_enquete_signature",),
        acteurs="Chaque groupe, une fois par session ordinaire (règlements).",
        condition="Interdit d'enquêter sur des faits donnant lieu à des poursuites judiciaires ; durée "
                  "bornée par la loi (six mois).",
        declenche=("propositions_de_loi", "rapports_publics"),
        empeche_par=("suspision_judiciaire", "droit_au_silence"),
        effet_modele="Le moteur relie les travaux de contrôle à la transparence et à la confiance (cf. "
                     "`transparence_votes`, `confiance`), pas à une décision directe.",
        observation="Les commissions sur la gestion de la crise sanitaire, l'énergie ou les finances "
                    "locales ont produit des rapports utilisés comme sources de calibrage dans ce dépôt.",
        cout="Faible pour l'initiative ; élevé pour le gouvernement mis en cause.",
    ),
    Mecanisme(
        "niche_parlementaire", "Faire adopter un texte contre le gouvernement (48 alinéa 4)",
        "faire_adopter",
        "Un jour de séance par mois est réservé à un ordre du jour arrêté par l'initiative des groupes "
        "d'opposition et des groupes minoritaires ; au Sénat, une séance par mois est réservée aux "
        "propositions d'initiative sénatoriale.",
        articles=("48", "51-1", "29", "34-1"),
        verrous=("session_extraordinaire_signatures",),
        acteurs="Un groupe d'opposition ou minoritaire ; la Conférence des présidents.",
        condition="Une niche ne garantit pas l'adoption : il faut une majorité de rechange, texte par "
                  "texte.",
        declenche=("adoption_sans_gouvernement",),
        empeche_par=("ordre_du_jour_prioritaire", "rejet_en_seance"),
        effet_modele="Le modèle note l'existence de contre-majorités parlementaires : sans majorité "
                     "absolue, toute loi peut se faire contre le Gouvernement (cf. "
                     "`droits_opposition_parlementaire`, piste).",
        observation="C'est par la niche que sont passées des réformes sociétales majeures, et que le Sénat "
                    "a fait adopter des textes que l'Assemblée refusait.",
        cout="Aucun pour le gouvernement qui la subit, sauf s'il perd un vote symbolique.",
    ),
    Mecanisme(
        "session_extraordinaire", "Rappeler le Parlement (29-30)", "armer",
        "Le Parlement est réuni en session extraordinaire à la demande du Premier ministre ou de la "
        "majorité des membres de l'Assemblée nationale, sur un ordre du jour déterminé ; lorsque la demande "
        "vient des députés, la clôture intervient au plus tard douze jours après la réunion.",
        articles=("29", "30", "28", "51"),
        verrous=("session_extraordinaire_signatures", "session_cloture_delai"),
        acteurs="Le Premier ministre, ou 289 députés.",
        condition="Ordre du jour déterminé obligatoire ; pas de demande citoyenne possible.",
        declenche=("ratification_express", "vote_budget"),
        empeche_par=("carence_du_senat",),
        effet_modele="Non chiffré : mais il borne le temps disponible pour une réforme (le moteur a un "
                     "calendrier de séance : cf. `rythme_parlementaire`, piste).",
        observation="Rarement demandée par les députés : la majorité de 289 est justement ce que les "
                    "oppositions n'ont pas.",
        cout="Faible ; son usage est surtout un signal politique.",
    ),
    Mecanisme(
        "revision_constitutionnelle", "Changer la règle du jeu (article 89)", "bloquer",
        "Le projet ou la proposition de révision est voté en termes identiques par les deux assemblées, puis "
        "approuvé par référendum — ou par le Congrès à la majorité des trois cinquièmes des suffrages "
        "exprimés.",
        articles=("89", "42", "3", "7", "12", "16", "60", "61"),
        verrous=("congres_revision",),
        acteurs="Président sur proposition du Premier ministre, ou parlementaires ; Congrès ou "
                "électeurs.",
        condition="Termes identiques exigés : le Sénat a un veto de fait. Forme républicaine "
                  "irrévisible ; aucune révision en cas d'atteinte à l'intégrité du territoire.",
        declenche=("referendum_revision", "congres"),
        empeche_par=("veto_senat", "congres_refus", "referendum_rejet"),
        effet_modele="Le modèle ne permet pas de réviser par la loi : les leviers de famille "
                     "« institutions » qui touchent à la Constitution sont explicitement présentés comme "
                     "dépendant d'une révision (`reforme_proportionnelle`, `reforme_ric`, "
                     "`verrouillage_irreversibilite`).",
        observation="Vingt-cinq révisions depuis 1958, presque toutes en Congrès ; la dernière (8 mars "
                    "2024) a inscrit la liberté garantie à la femme d'avoir recours à une IVG à "
                    "l'article 34.",
        cout="Le plus élevé de tous : une réforme constitutionnelle consomme tout le capital politique "
             "disponible.",
    ),
    Mecanisme(
        "haute_cour", "Destituer le Président (articles 67-68)", "armer",
        "Le Président n'est responsable que d'un manquement à ses devoirs manifestement incompatible avec "
        "l'exercice de son mandat, apprécié par le Parlement réuni en Haute Cour.",
        articles=("68", "67", "68-1", "26"),
        verrous=("haute_cour_assemblees", "haute_cour_destitution"),
        acteurs="Deux assemblées à deux tiers, puis la Haute Cour à deux tiers.",
        condition="Aucun fait de campagne ou de vie privée : les actes détachables relèvent du droit commun.",
        empeche_par=("refus_du_senat",),
        effet_modele="Non modélisé : le moteur ne simule pas la destitution présidentielle.",
        observation="La procédure, réformée en 2007-2008, n'a jamais abouti : engagée en 2021, elle a "
                    "échoué au Sénat.",
        cout="Aucune procédure ne coûte autant à lancer pour si peu de chances d'aboutir.",
    ),
    Mecanisme(
        "cjr", "Poursuivre un ministre pour ses actes de fonction", "armer",
        "Les membres du Gouvernement sont pénalement responsables des actes accomplis dans l'exercice de "
        "leurs fonctions et qualifiés crimes ou délits ; ils sont jugés par la Cour de justice de la "
        "République, composée de quinze juges dont douze parlementaires.",
        articles=("68-1", "68-2", "68-3", "26"),
        verrous=(),
        acteurs="Toute personne qui se prétend lésée, par plainte à la commission des requêtes.",
        condition="Fonction, pas mandat : un acte détachable relève des juridictions de droit commun.",
        empeche_par=("classement_commission_requetes",),
        effet_modele="Non chiffré ; utile comme borne de responsabilité dans le volet probité "
                     "(`reforme_anti_pantouflage`, `lutte_contre_la_corruption`).",
        observation="Filtre très étroit : la grande majorité des plaintes est classée sans suite par la "
                    "commission des requêtes.",
        cout="Faible pour le plaigneur, symbolique pour le gouvernement ; le vrai levier est "
             "l'opinion.",
    ),
    Mecanisme(
        "nominations_bloquees", "Refuser une nomination en conseil des ministres (13 alinéa 5)", "armer",
        "Les fonctions de conseiller d'État, de président de cour d'appel, de secrétaire général du "
        "gouvernement, de membre des autorités indépendantes et autres emplois ou fonctions mentionnés par la "
        "loi organique ne peuvent être attribuées qu'après avis public des commissions permanentes compétentes "
        "des deux assemblées : le président de la République ne peut pas maintenir sa nomination si l'addition "
        "des votes négatifs dans chaque commission représente au moins trois cinquièmes des suffrages "
        "exprimés au sein de chacune d'elles.",
        articles=("13", "56", "65", "57"),
        verrous=("nomination_veto",),
        acteurs="Les commissions des affaires constitutionnelles et des lois des deux assemblées.",
        condition="Le veto est rare : il faut trois cinquièmes cumulés, ce qui suppose une opposition "
                  "transversale organisée.",
        empeche_par=("majorite_de_commission",),
        effet_modele="Le modèle ne simule pas les nominations : la fiche sert à documenter le risque "
                     "d'indépendance (cf. la Cour des comptes, art. 13 et 47-2).",
        observation="En 2026, la nomination d'une ministre en exercice à la présidence de la Cour des "
                    "comptes a relancé le débat sur l'effectivité de ce veto (proposition de loi organique "
                    "du Sénat n° 404 du 16 février 2026).",
        cout="Politique : un vote négatif massif n'empêche pas la nomination, il la rend coûteuse.",
    ),
    Mecanisme(
        "vacance_presidentielle", "Continuer sans président (article 7)", "exception",
        "En cas de vacance ou d'empêchement, le président du Sénat assure l'intérim ; l'élection a lieu vingt "
        "à trente-cinq jours plus tard ; les articles 49, 50 et 89 ne peuvent être mis en œuvre, et le "
        "Président intérimaire ne peut ni dissoudre ni saisir le Conseil constitutionnel.",
        articles=("7", "12", "49", "89", "56", "61"),
        verrous=("vacance_delai_scrutin",),
        acteurs="Le président du Sénat ; le Conseil constitutionnel pour le contentieux.",
        condition="La Constitution interdit d'engager ou de poursuivre une procédure de révision pendant la "
                  "vacance.",
        empeche_par=("report_maximal_de_trente_cinq_jours",),
        effet_modele="Traité par le moteur comme une fenêtre de non-décision : les chantiers législatifs "
                     "sont gelés, la prime de taux augmente (cf. `calendrier_electoral`).",
        observation="Précédent fondateur : la démission du 28 avril 1969, avec intérim du président du "
                    "Sénat et scrutin dans le mois — et la règle non écrite qui a fait du scrutin "
                    "référendaire perdu une démission.",
        cout="Aucun pour l'intérimaire, énorme pour le calendrier des réformes.",
    ),
    Mecanisme(
        "subsidiarite", "Renvoyer la Commission sur ses competences (88-6)", "armer",
        "Les deux assemblées peuvent émettre un avis motivé sur la conformité d'un projet d'acte "
        "législatif européen au principe de subsidiarité ; à la demande de soixante députés ou de soixante "
        "sénateurs, le recours devant la Cour de justice de l'Union européenne est de droit. Le "
        "gouvernement français ne peut ni retenir l'avis ni refuser de transmettre le recours.",
        articles=("88-6", "88-4", "88-1"),
        verrous=("saisine_conseil_signatures",),
        acteurs="Soixante députés ou soixante sénateurs ; la commission des affaires européennes.",
        condition="Huit semaines entre la transmission du texte et l'inscription à l'ordre du jour du "
                  "Conseil ; un tiers des voix cumulées des parlements nationaux déclenche le "
                  "réexamen (« carton jaune »).",
        declenche=("controle_parlementaire_ue",),
        empeche_par=("negociation_en_trilogue",),
        effet_modele="Non chiffré dans le modèle : c'est une procédure d'alerte, pas un veto — utile "
                     "comme borne de souveraineté dans les scénarios européens.",
        observation="Trois cartons jaunes depuis 2009 (2012, 2013, 2016), aucun carton orange : le "
                    "dispositif est réel mais rarement décisif.",
        cout="Faible en voix, élevé en temps : huit semaines ne pèsent rien contre une présidence du "
             "Conseil pressée de conclure.",
    ),
    Mecanisme(
        "transparence_seances", "Rendre les votes lisibles (article 33)", "armer",
        "Les séances des deux assemblées sont publiques et le compte rendu intégral des débats est publié au "
        "Journal officiel ; chaque assemblée peut néanmoins siéger en comité secret à la demande du Premier "
        "ministre ou d'un dixième de ses membres.",
        articles=("33", "51-1", "48", "26"),
        verrous=(),
        acteurs="Chaque assemblée ; un dixième des membres (58 députés, 35 sénateurs) pour le huis clos.",
        condition="Le scrutin public solennel est obligatoire sur certaines questions (49, 89, motions).",
        empeche_par=("comite_secret",),
        effet_modele="La donnée de vote nominal est la base du modèle de coalition : c'est à partir d'elle "
                     "que sont calibrés les seuils de censure.",
        observation="Les comptes rendus et scrutins publics sont exploités dans le dépôt comme source "
                    "primaire de l'« instant T » du simulateur.",
        cout="Nul ; c'est un droit, pas une décision.",
    ),
    Mecanisme(
        "defossilisation", "Sortir une règle du domaine de la loi (37 alinéa 2)", "bloquer",
        "Les textes de forme législative intervenus en matière réglementaire peuvent être modifiés par "
        "décrets pris après avis motivé du Conseil d'État ; ceux intervenus postérieurement à la "
        "Constitution ne le peuvent qu'après déclaration par le Conseil constitutionnel de leur caractère "
        "réglementaire.",
        articles=("37", "34", "41", "61"),
        verrous=("irrecevabilite_competence_delai",),
        acteurs="Le Gouvernement, avec avis du Conseil d'État ; le Conseil constitutionnel en arbitre.",
        condition="Une disposition de principe ne peut être défossilisée si elle touche une garantie "
                  "constitutionnelle.",
        empeche_par=("censure_conseil", "reecriture_par_le_parlement"),
        effet_modele="Sert à chiffrer la vitesse de réforme : un gouvernement peut simplifier sans vote "
                     "dans la marge réglementaire (cf. `gouvernance_voie_reglementaire`, piste).",
        observation="Des milliers de dispositions ont été défossilisées depuis 1958 par ordonnances de "
                    "simplification ; le Conseil constitutionnel a encadré le mouvement (2005-512 DC, "
                    "2010-620 DC).",
        cout="Technique ; le débat politique porte sur la légitimité, pas sur le procédé.",
    ),
    Mecanisme(
        "ordonnance_budgetaire", "Passer outre le Parlement sur le budget (47 alinéa 3)",
        "faire_adopter",
        "Si le Parlement ne s'est pas prononcé dans les soixante-dix jours, les dispositions du projet de loi "
        "de finances peuvent être mises en vigueur par ordonnance ; si le projet n'est pas déposé en temps "
        "utile, le Gouvernement demande d'urgence l'autorisation de percevoir les impôts et ouvre par décret "
        "les crédits des services votés.",
        articles=("47", "47-1", "49", "40"),
        verrous=("budget_delai_total", "plfss_delai_total", "budget_an_delai", "budget_senat_delai"),
        acteurs="Le Gouvernement, après engagement de responsabilité le cas échéant.",
        condition="Le compte à rebours est constitutionnel : aucune obstruction ne peut l'arrêter.",
        declenche=("article_49_3",),
        empeche_par=("motion_censure",),
        effet_modele="C'est le paramétrage de `cadencement_budgetaire` : le modèle fait dépendre la "
                     "probabilité de 49.3 des jours restants avant l'échéance.",
        observation="Calendrier 2027 : PLF et PLFSS déposés le 6 octobre 2026, échéances des soixante-dix "
                    "et cinquante jours les 26 novembre et 17 décembre 2026.",
        cout="Le budget passe, la crise reste : le 49.3 budgétaire est devenu la norme des majorités "
             "relatives.",
    ),
    Mecanisme(
        "audit_cour_des_comptes", "Faire juger la sincérité des comptes (47-2)", "armer",
        "La Cour des comptes assiste le Parlement et le Gouvernement dans le contrôle de l'exécution des lois "
        "de finances et de l'application des lois de financement de la sécurité sociale, ainsi que dans "
        "l'évaluation des politiques publiques ; par ses rapports publics, elle contribue à l'information des "
        "citoyens ; les comptes des administrations publiques sont réguliers et sincères.",
        articles=("47-2", "47", "13", "34"),
        verrous=(),
        acteurs="Une assemblée, un dixième de ses membres, ou la Cour de sa propre initiative.",
        condition="La Cour ne censure pas une politique : elle juge des comptes.",
        empeche_par=("absence_de_suite",),
        effet_modele="Le modèle intègre la certification comme garde-fou de la qualité budgétaire (cf. "
                     "`qualite_depense`, `gouvernance_audit`).",
        observation="La saisine parlementaire produit un rapport public opposable : une minorité organisée "
                    "(58 députés ou 35 sénateurs) peut l'obtenir.",
        cout="Nul pour le demandeur ; variable pour le gouvernement, selon la publicité du rapport.",
    ),
)

MECANISMES: dict[str, Mecanisme] = {m.cle: m for m in _MECANISMES_BRUTS}

#: Familles de mécanismes (filtre d'affichage).
FAMILLES: tuple[str, ...] = ("renverser", "faire_adopter", "bloquer", "consulter", "armer", "exception")

#: État des assemblées à la date d'observation : il sert à traduire les seuils en
#: voix disponibles, pas à prédire une issue.
ETAT_ASSEMBLEES: dict[str, dict[str, Any]] = {
    "assemblee_nationale": {
        "legislature": "XVIIe",
        "sieges": 577,
        "pourvus": 574,
        "majorite_absolue": 289,
        "seuil_groupe": 15,
        "groupes": {
            "RN": 121, "EPR": 90, "LFI-NFP": 70, "SOC": 68, "DR": 47, "EcoS": 38,
            "LD": 37, "HOR": 35, "LIOT": 23, "GDR": 17, "UDR": 17, "NI": 11,
        },
        "soutien_gouvernement": (209, 211),
        "note": "Soutien gouvernemental compté comme la somme des groupes de la coalition et de ses "
                "alliances déclarées ; les trois sièges vacants n'abaissent pas le seuil de censure, qui "
                "porte sur l'effectif légal.",
    },
    "senat": {
        "renouvellement": "2026-09-27",
        "sieges": 348,
        "pourvus": 348,
        "majorite_absolue": 175,
        "seuil_groupe": 10,
        "groupes": {
            "LR": 124, "UCI": 63, "SER": 62, "CRCE-K": 18, "RDSE": 18, "RDPI": 16,
            "GEST": 15, "LIRT": 15, "RN-UDR": 15, "NI": 2,
        },
        "majorite_droite_et_centre": 187,
        "president": "Gérard Larcher, réélu le 1er octobre 2026",
        "note": "La majorité LR-UCI (187) détient à elle seule le veto de fait sur toute révision "
                "constitutionnelle (89 exige les termes identiques).",
    },
}


# ────────────────────────────────────────────────────────────────────────────
# CALCULS
# ────────────────────────────────────────────────────────────────────────────

def _effectifs(sieges: dict[str, int] | None = None) -> dict[str, int]:
    return dict(sieges or {})


def seuil(cle_verrou: str, effectifs: dict[str, int] | None = None) -> int:
    """Valeur du seuil (voix, signatures, jours) pour un verrou donné."""
    verrou = VERROUS.get(cle_verrou)
    return verrou.seuil(_effectifs(effectifs)) if verrou else 0


def seuils_pour(
    cle_mecanisme: str, effectifs: dict[str, int] | None = None
) -> list[dict[str, Any]]:
    """Tableau chiffré des verrous franchis par une manœuvre."""
    mecanisme = MECANISMES.get(cle_mecanisme)
    if mecanisme is None:
        return []
    donnees = _effectifs(effectifs)
    return [VERROUS[c].en_dict(donnees) for c in mecanisme.verrous if c in VERROUS]


def tableau_des_seuils(effectifs: dict[str, int] | None = None) -> dict[str, Any]:
    """Tous les verrous du régime, chiffrés pour un effectif donné."""
    donnees = _effectifs(effectifs)
    return {cle: verrou.en_dict(donnees) for cle, verrou in VERROUS.items()}


def blocages_possibles(cle_mecanisme: str) -> list[dict[str, Any]]:
    """Ce qui peut faire échouer la manœuvre, avec l'article qui l'autorise."""
    mecanisme = MECANISMES.get(cle_mecanisme)
    if mecanisme is None:
        return []
    sorties = []
    for autre in mecanisme.empeche_par:
        cible = MECANISMES.get(autre)
        articles = ", ".join(f"art. {a}" for a in (cible.articles if cible else ()))
        sorties.append({
            "cle": autre,
            "nom": cible.nom if cible else autre,
            "resume": cible.resume if cible else "obstacle décrit par la fiche du mécanisme",
            "articles": articles,
        })
    return sorties


def chaine_de_reaction(cle_mecanisme: str, profondeur: int = 3) -> list[dict[str, Any]]:
    """Ce que la manœuvre déclenche, puis ce que la suite déclenche à son tour.

    Une censure appelle une démission, qui appelle une nomination, qui appelle
    éventuellement une dissolution : la valeur du contre-pouvoir est dans la chaîne,
    pas dans le premier maillon.
    """
    vus: list[str] = []
    files: list[tuple[str, int]] = [(cle_mecanisme, 0)]
    sorties: list[dict[str, Any]] = []
    while files:
        cle, niveau = files.pop(0)
        if cle in vus or niveau > profondeur:
            continue
        vus.append(cle)
        mecanisme = MECANISMES.get(cle)
        if mecanisme is None:
            continue
        sorties.append({
            "cle": cle, "nom": mecanisme.nom, "famille": mecanisme.famille,
            "profondeur": niveau, "resume": mecanisme.resume,
            "articles": list(mecanisme.articles),
        })
        for suivant in mecanisme.declenche:
            files.append((suivant, niveau + 1))
    return sorties


def arithmetique_assemblee(nom: str) -> dict[str, Any]:
    """Seuils internes d'une assemblée, à partir de son effectif légal."""
    etat = ETAT_ASSEMBLEES.get(nom)
    if etat is None:
        return {}
    sieges = int(etat["sieges"])
    return {
        "nom": nom,
        "sieges": sieges,
        "pourvus": etat.get("pourvus", sieges),
        "majorite_absolue": sieges // 2 + 1,
        "majorite_qualifiee_3_5": math.ceil(3 * sieges / 5),
        "majorite_2_3": math.ceil(2 * sieges / 3),
        "dixieme": math.ceil(sieges / 10),
        "cinquieme": math.ceil(sieges / 5),
        "seuil_groupe": etat.get("seuil_groupe"),
        "groupes": etat.get("groupes", {}),
    }


def coalition_necessaire(cle_mecanisme: str, nom_assemblee: str = "assemblee_nationale") -> dict[str, Any]:
    """De combien de groupes la manœuvre a-t-elle besoin, étant donnée la composition ?"""
    mecanisme = MECANISMES.get(cle_mecanisme)
    if mecanisme is None:
        return {"erreur": "mécanisme inconnu"}
    donnees = arithmetique_assemblee(nom_assemblee)
    groupes = dict(donnees.get("groupes") or {})
    effectifs = {
        "membres_assemblee_nationale": donnees.get("sieges", 0),
        "membres_assemblee_nationale_pourvus": donnees.get("pourvus", 0),
        "membres_senat": donnees.get("sieges", 0),
        "membres_congres": SIEGES_THEORIQUES["congres"],
    }
    requis = 0
    for cle_verrou in mecanisme.verrous:
        verrou = VERROUS.get(cle_verrou)
        if verrou and verrou.sens == "atteindre" and verrou.assiette.startswith("membres"):
            requis = max(requis, verrou.seuil(effectifs))
    if not groupes:
        return {"erreur": "composition inconnue"}
    requis = requis or donnees.get("majorite_absolue", 0)
    ordre = sorted(groupes.items(), key=lambda kv: -kv[1])
    cumul, choisis = 0, []
    for nom, sieges in ordre:
        if cumul >= requis:
            break
        choisis.append({"groupe": nom, "sieges": sieges})
        cumul += sieges
    return {
        "mecanisme": mecanisme.nom,
        "assemblee": nom_assemblee,
        "voix_requises": requis,
        "coalition_la_plus_rapide": choisis,
        "voix_obtenues": cumul,
        "suffit": cumul >= requis > 0,
        "avertissement": (
            "Cette coalition est arithmétique : elle agrège les plus gros groupes, ce que la politique "
            "interdit presque toujours. Elle mesure un ordre de grandeur d'effort, pas un scénario."
        ),
    }


def diagnostic(effectifs: dict[str, int] | None = None) -> dict[str, Any]:
    """Tableau de bord : chaque mécanisme, ses seuils chiffrés, ses bloqueurs."""
    donnees = _effectifs(effectifs)
    lignes = []
    for cle in MECANISMES:
        mecanisme = MECANISMES[cle]
        lignes.append({
            "cle": cle,
            "nom": mecanisme.nom,
            "famille": mecanisme.famille,
            "articles": list(mecanisme.articles),
            "seuils": seuils_pour(cle, donnees),
            "bloqueurs": [b["cle"] for b in blocages_possibles(cle)],
            "declenche": list(mecanisme.declenche),
            "observation": mecanisme.observation,
            "cout": mecanisme.cout,
        })
    return {
        "date_etat": DATE_ETAT_ASSEMBLEES,
        "effectifs": {"assemblee_nationale": arithmetique_assemblee("assemblee_nationale"),
                      "senat": arithmetique_assemblee("senat")},
        "mecanismes": lignes,
    }


def rechercher(terme: str) -> list[dict[str, Any]]:
    """Recherche dans les mécanismes et les verrous."""
    mot = (terme or "").strip().lower()
    if len(mot) < 3:
        return []
    sorties = []
    for cle, mecanisme in MECANISMES.items():
        champ = " ".join((mecanisme.nom, mecanisme.resume, mecanisme.acteurs, mecanisme.condition,
                          mecanisme.observation)).lower()
        if mot in champ:
            sorties.append({"type": "mecanisme", "cle": cle, "nom": mecanisme.nom,
                            "articles": list(mecanisme.articles)})
    for cle, verrou in VERROUS.items():
        if mot in " ".join((verrou.nom, verrou.texte)).lower():
            sorties.append({"type": "verrou", "cle": cle, "nom": verrou.nom,
                            "articles": [verrou.article]})
    return sorties


def coherence_avec_les_fiches() -> dict[str, Any]:
    """Contrôle de recoupement avec `simulateur.constitution_analysee`.

    Le vocabulaire des fiches est ouvert (il décrit finement les mécanismes), mais
    chaque mécanisme défini ici doit être rattaché à au moins un article fiché, et
    chaque article cité doit exister : sinon la table est decorative.
    """
    from .constitution_analysee import ARTICLES

    orphelins = []
    for cle, mecanisme in MECANISMES.items():
        rattache = any(cle in ARTICLES[numero].mecanismes for numero in mecanisme.articles)
        if not rattache:
            orphelins.append(cle)
    articles_inconnus = sorted({
        a for m in MECANISMES.values() for a in m.articles if a not in ARTICLES
    })
    verrous_manquants = sorted({
        v for m in MECANISMES.values() for v in m.verrous if v not in VERROUS
    })
    return {
        "mecanismes": len(MECANISMES),
        "verrous": len(VERROUS),
        "mecanismes_orphelins": orphelins,
        "articles_inconnus": articles_inconnus,
        "verrous_inexistants": verrous_manquants,
        "conforme": not (orphelins or articles_inconnus or verrous_manquants),
    }


def synthese_pour_api() -> dict[str, Any]:
    """Charge utile pour la page « contre-pouvoirs » et pour l'API."""
    return {
        "titre": "L'arithmétique des contre-pouvoirs",
        "accroche": "De combien de voix, de signatures et de jours chaque manœuvre "
                    "institutionnelle a réellement besoin — et ce qui peut la faire échouer.",
        "avertissement": (
            "Un mécanisme « au vert » n'est pas une promesse de réussite : ces nombres "
            "disent de combien de voix une coalition a besoin, pas si elle existera."
        ),
        "date_etat_des_assemblees": DATE_ETAT_ASSEMBLEES,
        "familles": [
            {"nom": f, "mecanismes": [c for c, m in MECANISMES.items() if m.famille == f]}
            for f in FAMILLES
        ],
        "mecanismes": [m.en_dict() for m in MECANISMES.values()],
        "verrous": tableau_des_seuils(),
        "assemblees": {
            "assemblee_nationale": arithmetique_assemblee("assemblee_nationale"),
            "senat": arithmetique_assemblee("senat"),
        },
        "coherence": coherence_avec_les_fiches(),
    }


def resume_console() -> str:
    etat = coherence_avec_les_fiches()
    lignes = [
        f"Contre-pouvoirs — {etat['mecanismes']} mécanismes, {etat['verrous']} verrous chiffrés.",
        f"État des assemblées constaté le {DATE_ETAT_ASSEMBLEES} : "
        f"majorité absolue à {arithmetique_assemblee('assemblee_nationale')['majorite_absolue']} députés, "
        f"{arithmetique_assemblee('senat')['majorite_absolue']} sénateurs ; "
        f"Congrès à {seuil('congres_revision')} suffrages exprimés (base {SIEGES_THEORIQUES['congres']}).",
    ]
    if not etat["conforme"]:
        lignes.append(
            "Incohérences : "
            + f"orphelins {etat['mecanismes_orphelins']}, "
            + f"articles inconnus {etat['articles_inconnus']}, "
            + f"verrous manquants {etat['verrous_inexistants']}"
        )
    return "\n".join(lignes)


__all__ = [
    "ASSIETES", "DATE_ETAT_ASSEMBLEES", "ELECTEURS_INSCRITS", "FAMILLES", "MECANISMES",
    "SIEGES_POURVUS", "SIEGES_THEORIQUES", "VERROUS", "Mecanisme", "Verrou",
    "arithmetique_assemblee", "blocages_possibles", "chaine_de_reaction", "coherence_avec_les_fiches",
    "coalition_necessaire", "diagnostic", "rechercher", "resume_console", "seuil", "seuils_pour",
    "synthese_pour_api", "tableau_des_seuils",
]
