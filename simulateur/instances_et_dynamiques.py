"""instances_et_dynamiques — les instances qui gravitent à tous les étages, le yoyo
des chambres, et la R&D des fentes non écrites.

Trois questions, trois objets
-----------------------------

1. **Qui juge, qui avis, qui bloque ?** Le simulateur connaissait les articles
   (`constitution_analysee`) et les manœuvres (`gouvernance_contrepouvoir`). Il lui
   manquait les *personnes morales* : Conseil constitutionnel, Conseil d'État, Cour de
   cassation, Cour des comptes, CSM, ARCOM, CNIL, Défenseur des droits, CNCCFP, CESE,
   préfet, juridictions administratives, CJUE, CEDH, Commission européenne. Chacune est
   décrite par ce que le droit dit *d'elle* : fondement, saisine, effets, et — donnée
   presque toujours oubliée — **qui la contrôle elle**.

2. **Le yoyo.** Une navette n'est pas un flux : c'est une suite de battements dont
   chacun avance, recule, bloque ou verrouille, avec un coût en jours et un coût en
   voix. `TRAJETS` encode ces suites ; `oscillation()` les calcule à partir des effectifs
   du jour (module des contre-pouvoirs) et de la fenêtre législative résiduelle, et
   `asymetrie_des_chambres()` mesure ce que le Sénat peut *retarder* mais pas *empêcher*.

3. **Les fentes.** Une fente n'est pas écrite : elle est le produit de croisements dont
   personne n'a tiré la conséquence. Elle se reconnaît à trois signes : toutes ses
   prémisses sont dans le droit (article de fiche, décision, texte du registre), aucune
   ne dit la conséquence, et la conséquence tient debout par la seule logique — donc ne
   se discute pas au fond, seulement au niveau d'attaque. `FENTES` les énumère avec
   leurs prémisses et leur **verrou de retour** : quel étage de texte il faudrait pour la
   défaire, et quel juge y aurait accès.

Ce que ce module ne fait pas
---------------------------

Il ne dit **jamais** qu'une fente est « irréfutable ». Le Conseil d'État ne juge pas la
logique, il juge la compétence, la procédure, la motivation et le respect des normes
supérieures ; la Cour de cassation et le Conseil constitutionnel idem. Ce que le module
calcule, c'est une **robustesse** : la hauteur de la base légale, la présence des
consultations obligatoires, la protection des situations individuelles, et le fait qu'une
abrogation future exige le même étage que celui qui a verrouillé. Une fente dont la base
est un décret reste attaquable par un décret.

Convention du dépôt : un modèle, pas une prophétie, et rien qui ne soit retrouvé dans un
texte. Les comportements d'instance non documentés sont marqués `a_verifier` et ne
chiffrent rien.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .constitution_analysee import ARTICLES, ORDRE_ARTICLES, article
from .gouvernance_contrepouvoir import MECANISMES, VERROUS
from .reglements_lois import REGISTRE_LEGAL

#: Date d'observation des effectifs et des pratiques : les instances ne changent pas de
#: compétence, mais elles changent de composition, et leur jurisprudence bouge.
DATE_OBSERVATION = "2026-10-12"

NIVEAUX: Tuple[str, ...] = (
    "Constitutionnel",
    "Administratif",
    "Judiciaire",
    "Financier",
    "Indépendante",
    "Parlementaire",
    "Territoriale",
    "Européenne",
    "Internationale",
    "Financière",
    "Consultative",
)

#: Ce qu'un acte d'une instance produit juridiquement. Le vocabulaire est fermé pour
#: que `robustesse()` puisse comparer deux verrous sans comparer des mots.
EFFETS: Dict[str, str] = {
    "censure": "le texte disparaît ou est promulgué amendé",
    "abrogation_rejet": "le juge refuse d'écarter la norme",
    "annulation": "l'acte disparaît rétroactivement",
    "injonction": "le juge commande une action sous délai",
    "astreinte": "l'injonction est assortie d'une somme par jour de retard",
    "sursis": "l'exécution est gelée le temps du contrôle",
    "avis": "aucune force juridique, mais un avis obligatoire non rendu vicie la procédure",
    "conformite_obligatoire": "sans la conformité, l'acte ne peut être pris",
    "constat": "rien n'est ordonné : la situation est déclarée contraire à la norme",
    "signalement": "le dossier est transmis à une autorité qui peut agir",
    "incompetence_declaree": "le juge déclare que la norme n'avait pas compétence pour statuer",
    "recommandation": "obligation de répondre, pas d'obéir",
    "mise_en_demeure": "l'État est sommé de se conformer avant sanction",
    "sanction_financiere": "pécule calculé par jour de retard (UE) ou amende (CEDH)",
    "irrecevabilite": "la norme ou la demande n'est pas examinée au fond",
}

#: Niveaux de texte, du plus attaquable au plus verrouillé. Le « verrou de retour » d'une
#: fente est le niveau le plus bas parmi ses prémisses : c'est par là qu'on la défait.
ETAGES: Tuple[str, ...] = (
    "réglementaire",
    "loi ordinaire",
    "loi organique",
    "constitutionnel",
    "constitutionnel + procédure particulière",
    "conventionnel ou droit dérivé de l'UE",
)

#: Qui peut faire annuler quoi, par étage. Un « trou » est toujours aussi un endroit où
#: le niveau d'attaque n'existe pas.
QUI_ATTAQUE: Dict[str, Tuple[str, ...]] = {
    "réglementaire": ("juge administratif (REC pour excès de pouvoir)", "exception d'illégalité devant tout juge"),
    "loi ordinaire": ("Conseil constitutionnel (a priori, art. 61 al. 1)", "QPC (art. 61-1)", "exception d'inconventionnalité devant le juge national"),
    "loi organique": ("Conseil constitutionnel obligatoire (art. 61 al. 1)", "QPC si elle légifère"),
    "constitutionnel": ("rien : le juge constitutionnel français ne censure pas la révision", "contrôle de l'identité et des exigences de forme par le Conseil constitutionnel", "CEDH/CJUE par ricochet via les actes d'application"),
    "constitutionnel + procédure particulière": ("le veto parlementaire ou le refus du Congrès/référendum", "rien après promulgation"),
    "conventionnel ou droit dérivé de l'UE": ("Commission (manquement)", "CJUE (préjudicielle ou manquement)", "juge national (écarte la norme interne contraire)"),
}


def _references(fondement: Tuple[str, ...]) -> Dict[str, List[str]]:
    """Classe les fondements : articles de fiche, identifiants du registre, autres.

    Un fondement doit être résoluble : soit un numéro d'article de la Constitution, soit
    un identifiant du `REGISTRE_LEGAL`. Ce qui n'est ni l'un ni l'autre est listé à part,
    pour que `coherence_avec_le_droit()` puisse le signaler plutôt que le laisser croire.
    """
    articles, registre, autres = [], [], []
    for ref in fondement:
        if re.fullmatch(r"\d+(-\d+)?", ref or ""):
            articles.append(ref)
        elif "_" in (ref or ""):
            registre.append(ref)
        else:
            autres.append(ref)
    return {"articles": articles, "registre": registre, "autres": autres}


@dataclass(frozen=True)
class Instance:
    """Une autorité, décrite par ce que le droit dit d'elle et par ce qui la contrôle."""

    cle: str
    nom: str
    niveau: str
    mission: str
    fondement: Tuple[str, ...] = ()
    composition: str = ""
    designation: str = ""
    saisissable_par: Tuple[str, ...] = ()
    effets: Tuple[str, ...] = ()
    peut_bloquer: Tuple[str, ...] = ()      # clés de mécanismes du module contre-pouvoirs
    verrous: Tuple[str, ...] = ()           # clés de verrous chiffrés du même module
    juge_par: str = ""
    delais: Tuple[Tuple[str, int], ...] = ()
    observation: str = ""
    fiabilite: str = "texte"                # texte | pratique | a_verifier
    leviers: Tuple[str, ...] = ()
    pistes: Tuple[str, ...] = ()

    def en_dict(self) -> Dict[str, Any]:
        refs = _references(self.fondement)
        return {
            "cle": self.cle,
            "nom": self.nom,
            "niveau": self.niveau,
            "mission": self.mission,
            "fondement": list(self.fondement),
            "fondement_resolu": {
                "articles": [f"Article {a} — {ARTICLES[a].titre}" for a in refs["articles"] if a in ARTICLES],
                "registre": [f"{i} — {REGISTRE_LEGAL[i].titre}" for i in refs["registre"] if i in REGISTRE_LEGAL],
                "non_resolu": [r for r in refs["articles"] if r not in ARTICLES] + [
                    i for i in refs["registre"] if i not in REGISTRE_LEGAL
                ],
                "autres": refs["autres"],
            },
            "composition": self.composition,
            "designation": self.designation,
            "saisissable_par": list(self.saisissable_par),
            "effets": [{"cle": e, "portee": EFFETS.get(e, "effet à qualifier")} for e in self.effets],
            "peut_bloquer": list(self.peut_bloquer),
            "verrous": [
                {"cle": v, "nom": VERROUS[v].nom, "formule": VERROUS[v].en_dict()["formule"]}
                for v in self.verrous if v in VERROUS
            ],
            "juge_par": self.juge_par,
            "delais": [{"objet": o, "jours": j} for o, j in self.delais],
            "observation": self.observation,
            "fiabilite": self.fiabilite,
            "leviers": list(self.leviers),
            "pistes": list(self.pistes),
            "observe_le": DATE_OBSERVATION,
        }


# ── LES INSTANCES ────────────────────────────────────────────────────────────────
# Un étage n'est pas un échelon : le préfet et la CJUE jugent le même acte. Les
# saisines et les délais sont rattachés aux verrous chiffrés du module des
# contre-pouvoirs pour que le même nombre ne vive pas à deux endroits.

INSTANCES: Dict[str, Instance] = {
    "conseil_constitutionnel": Instance(
        cle="conseil_constitutionnel",
        nom="Conseil constitutionnel",
        niveau="Constitutionnel",
        mission="Contrôler la conformité des lois et des règlements d'assemblées, arbitrer "
                "l'éligibilité et le contentieux électoral et constitutionnel, trancher la "
                "nature juridique d'une disposition (art. 37 et 41).",
        fondement=("61", "61-1", "37", "41", "56", "58", "62", "11", "89", "CC_2017_752_DC"),
        composition="Neuf membres : trois nommés par le Président de la République, trois par le "
                    "président de l'Assemblée nationale, trois par le président du Sénat ; "
                    "renouvellement par tiers tous les trois ans, mandat de neuf ans non renouvelable ; "
                    "les anciens présidents de la République siègent de droit à vie (alinéa 1 de "
                    "l'article 56 tel que modifié en 2008 — les sièges de droit n'existent plus depuis "
                    "la révision du 23 juillet 2008 : à vérifier avant de citer un effectif de douze).",
        designation="Trois désignations partisanes qui n'obligent à rien : le président est "
                    "désigné par le Président de la République et dispose de la voix "
                    "prépondérante en cas de partage (art. 61 al. 4 « en cas de partage des voix, la "
                    "voix du président est prépondérante »).",
        saisissable_par=(
            "Président de la République, Premier ministre, présidents des deux assemblées, "
            "soixante députés ou soixante sénateurs (art. 61 al. 1 et 2)",
            "tout justiciable par le filtre des trois juridictions suprêmes (art. 61-1)",
            "Gouvernement pour la déclassification d'un texte législatif (art. 37 al. 2)",
            "Président de l'assemblée pour le recours contre une irrecevabilité (art. 44 al. 4)",
        ),
        effets=("censure", "irrecevabilite", "constat", "incompetence_declaree"),
        peut_bloquer=("saisine_conseil",),
        verrous=("saisine_conseil_signatures", "saisine_conseil_delai", "saisine_conseil_urgence"),
        juge_par="Personne. Ses décisions « ne sont susceptibles d'aucun recours » (art. 62 al. 1) : "
                 "c'est le seul verrou absolu du dispositif, et il est écrit.",
        delais=(("examen d'une loi déférée avant promulgation", 30),
                ("urgence demandée par le Gouvernement", 8)),
        observation="Aucune saisine de soixante n'a jamais été refusée faute de signatures : le "
                    "seuil est bas parce qu'il est politique. Le contentieux de l'élection "
                    "présidentielle est le seul où il statue sans filtre.",
        fiabilite="texte",
        leviers=("saisine_conseil_constitutionnel",),
        pistes=("transparence_des_saisines", "financement_des_campagnes_de_jugement"),
    ),
    "conseil_etat": Instance(
        cle="conseil_etat",
        nom="Conseil d'État",
        niveau="Administratif",
        mission="Double casquette : juge de cassation et de plein contentieux de l'administration "
                "(REC, référé-liberté, QPC en amont), et consultatif obligatoire pour les ordonnances "
                "et les projets de loi (art. 39 al. 1) ainsi que pour les décrets en Conseil d'État.",
        fondement=("39", "37", "38", "61-1", "CRPA_L123_1", "LOI_ORG_2009_403"),
        composition="Sections (intérieure, financiers, sociales, travaux publics, administratif, "
                    "rapports et études) et assemblée du contentieux ; effectifs et organisation fixés "
                    "par l'ordonnance du 31 juillet 1945 et le code de justice administrative — "
                    "chiffres à vérifier avant publication.",
        designation="Présidé par le vice-président du Conseil d'État, nommé en conseil des ministres "
                    "(art. 13) ; les membres sont des magistrats administratifs de carrière.",
        saisissable_par=(
            "tout justiciable justifiant d'un intérêt (REC)",
            "Gouvernement pour avis obligatoire sur les projets de loi et d'ordonnance",
            "déféré préfectoral pour les actes locaux dans les cas prévus par la loi",
        ),
        effets=("annulation", "injonction", "astreinte", "avis", "sursis", "constat"),
        peut_bloquer=("defossilisation", "qpc"),
        juge_par="La CEDH, sur le procès équitable (art. 6 de la Convention), et la CJUE par voie "
                 "préjudicielle depuis n'importe quelle formation administrative. La Cour de "
                 "cassation n'a rien à y voir : les deux ordres de juridiction sont séparés "
                 "(art. 66). Les avis consultatifs, en revanche, ne sont attaquables par rien — "
                 "c'est le point sensible du dispositif.",
        delais=(("référé-liberté : jugement", 2),),
        observation="Un avis non demandé ou un avis modifié sans renvoi devant la section rend "
                    "l'acte illégal : c'est par la procédure que le Conseil d'État se rend "
                    "indispensable, pas par le fond. Le contentieux de la loi repose sur ses "
                    "décisions individuelles : il ne censure jamais la loi.",
        fiabilite="pratique",
        leviers=("simplification",),
        pistes=("publications_des_saisines_conseil_etat", "comite_de_deontologie_reglementaire"),
    ),
    "cour_de_cassation": Instance(
        cle="cour_de_cassation",
        nom="Cour de cassation",
        niveau="Judiciaire",
        mission="Juge de la correcte application du droit par les juridictions judiciaires ; filtre "
                "obligé d'une QPC venue d'un procès civil, pénal ou social.",
        fondement=("64", "65", "66", "61-1", "LOI_JUSTICE_2023_1059"),
        composition="Chambres civiles, commerciales, sociale, pénale et chambre mixte ; "
                    "effectif à vérifier (ordonnance du 22 décembre 1958).",
        designation="Magistrats du siège, inamovibles (art. 64) ; la hiérarchie de la magistrature "
                    "est suivie par le CSM (art. 65).",
        saisissable_par=("tout justiciable par un pourvoi", "procureur général près la Cour de cassation",
                         "premier président pour les avis (art. L. 441-1 CJO)"),
        effets=("annulation", "censure", "irrecevabilite", "constat"),
        juge_par="CEDH (procès équitable), CJUE par préjudicielle ; ses propres arrêts ne sont "
                 "attaqués que par une nouvelle décision — la règle non écrite du revirement.",

        observation="Le pourvoi n'est pas un troisième degré : c'est un contrôle de droit. C'est ce "
                    "qui rend la fabrication d'un moyen nouveau en cassation si puissante — le fait "
                    "nouveau n'existe pas, mais l'interprétation, si.",
        fiabilite="texte",
        leviers=("budget_justice",),
        pistes=("acces_aux_arrets_de_cassation",),
    ),
    "cour_des_comptes": Instance(
        cle="cour_des_comptes",
        nom="Cour des comptes",
        niveau="Financier",
        mission="Juger les comptes des comptables publics, contrôler la gestion et, depuis 2008, "
                "assister le Parlement et le Gouvernement sur l'exécution des lois de finances et "
                "l'évaluation des politiques publiques (art. 47-2).",
        fondement=("47-2", "47", "50-1", "LOLF_ART_34", "LPF_L81"),
        composition="Chambres et pôles d'examen fixés par le code des juridictions financières ; "
                    "magistrats financiers nommés en conseil des ministres (art. 13) — effectifs à "
                    "vérifier avant de les citer.",
        designation="Magistrats financiers ; premier président nommé en conseil des ministres (art. 13).",
        saisissable_par=("présidents des deux assemblées, commissions des finances",
                         "saisine citoyenne prévue par la loi du 6 décembre 2023 — conditions à vérifier"),
        effets=("annulation", "constat", "signalement", "incompetence_declaree"),
        peut_bloquer=("audit_cour_des_comptes",),
        juge_par="La Cour de discipline budgétaire et financière (CDBF) pour les fautes des ordonnateurs ; "
                 "ses propres arrêts relèvent du Conseil d'État en cassation.",

        observation="Une évaluation d'un programme par la Cour vaut plus qu'un amendement : elle ne "
                    "change pas le budget, elle change le récit. Le levier est donc dans la date de "
                    "publication (avant ou après le vote) — à vérifier avant de l'écrire en scénario.",
        fiabilite="pratique",
        leviers=("lutte_contre_la_corruption",),
        pistes=("saisine_citoyenne_cour_des_comptes",),
    ),
    "conseil_superieur_de_la_magistrature": Instance(
        cle="conseil_superieur_de_la_magistrature",
        nom="Conseil supérieur de la magistrature",
        niveau="Constitutionnel",
        mission="Garant de l'indépendance de la magistrature : avis sur les nominations (art. 65), "
                "conseil de discipline des magistrats du siège, et depuis 2021 réception des plaintes "
                "de justiciables (art. 65 al. 6).",
        fondement=("64", "65", "66"),
        composition="Formations distinguées pour le siège et pour le parquet, présidées par le "
                    "Président de la République ; effectifs et collèges fixés par l'ordonnance "
                    "portant loi organique, à vérifier avant de citer un nombre.",
        designation="Membres magistrats élus, membres qualifiés désignés par les présidents des "
                    "assemblées et le Président de la République.",
        saisissable_par=("Gouvernement (avis conforme pour les sièges, avis simple pour le parquet)",
                         "tout justiciable (plainte depuis la révision du 23 juillet 2008)"),
        effets=("conformite_obligatoire", "avis", "signalement", "constat"),
        peut_bloquer=("nominations_bloquees",),
        juge_par="Ses avis ne se contestent pas : ils ne font pas grief. Ses décisions de discipline "
                 "relèvent du Conseil d'État. Ce qui est attaquable, ce n'est pas l'avis, c'est la "
                 "nomination prise sans l'avis conforme requis — et c'est très exactement là que se "
                 "loge le verrou.",
        observation="Un avis conforme non suivi n'est pas une illégalité : c'est une impossibilité "
                    "juridique de nommer. Le verrou est donc dans la nomination, pas dans la sanction.",
        fiabilite="texte",
        leviers=("reforme_csm", "independance_judiciaire"),
        pistes=("plaintes_justiciables_delais",),
    ),
    "autorite_de_regulation": Instance(
        cle="arcom",
        nom="Arcom",
        niveau="Indépendante",
        mission="Communication audiovisuelle et numérique : autorisations, respect des obligations, "
                "lutte contre la manipulation de l'information, régulation des plateformes en ligne.",
        fondement=("34", "11"),
        composition="Collège d'autorité indépendante : composition et renouvellement fixés par la loi "
                    "du 30 septembre 1986 modifiée (le CSA y a été fusionné avec Hadopi par "
                    "l'ordonnance du 22 décembre 2021) — nombres à vérifier avant citation.",
        designation="Désignations parlementaires majoritaires ; président nommé en conseil des "
                    "ministres selon les dispositions organiques ?",
        saisissable_par=("éditeurs, plateformes, utilisateurs via signalements",
                         "le Gouvernement et les assemblées pour des demandes d'étude"),
        effets=("sanction_financiere", "mise_en_demeure", "constat", "irrecevabilite"),
        juge_par="Le Conseil d'État sur ses décisions (recours de pleine juridiction) — donc ses "
                 "choix sont attaquables, mais ses lignes directrices le sont peu.",
        observation="L'arme n'est pas l'amende, c'est le calendrier : une mise en demeure publiée en "
                    "pleine campagne pèse plus qu'une sanction six mois plus tard.",
        fiabilite="a_verifier",
        leviers=("service_public_numerique",),
        pistes=("pluriel_et_temps_de_parole", "transparence_des_algorithmes"),
    ),
    "cnil": Instance(
        cle="cnil",
        nom="CNIL",
        niveau="Indépendante",
        mission="Protection des données personnelles, contrôle des traitements, avis sur les projets "
                "de loi et de décret, pouvoir de sanction.",
        fondement=("34", "REG_EIDAS_910_2014"),
        composition="Collège de conseillers élus par plusieurs autorités (Présidents des assemblées, "
                    "Président de la République, Cour de cassation, Conseil d'État, Cour des comptes) — "
                    "nombre exact à vérifier (loi Informatique et Libertés).",
        designation="Membres désignés par des autorités distinctes : c'est la seule instance dont la "
                    "composition est verrouillée par cinq sources différentes.",
        saisissable_par=("tout individu par plainte", "porteurs de traitements par demande d'avis",
                         "Parlement et Gouvernement pour avis obligatoires sur certains projets"),
        effets=("avis", "sanction_financiere", "sursis", "constat", "mise_en_demeure"),
        juge_par="Conseil d'État ; la CJUE par préjudicielle sur le RGPD.",
        observation="Un avis CNIL non demandé sur un traitement réglementaire rend le texte illégal — "
                    "le pouvoir de la CNIL est donc une condition de forme, pas une autorisation.",
        fiabilite="pratique",
        leviers=("souverainete_numerique_ia",),
        pistes=("registre_public_des_traitements_locaux",),
    ),
    "defenseur_des_droits": Instance(
        cle="defenseur_des_droits",
        nom="Défenseur des droits",
        niveau="Constitutionnel",
        mission="Défense des droits devant l'administration, déontologie de la sécurité, droits de "
                "l'enfant, lutte contre les discriminations (art. 71-1).",
        fondement=("71-1", "66"),
        composition="Un Défenseur nommé par le Président de la République après avis des commissions "
                    "des deux assemblées (le veto des 3/5 est possible : art. 13 al. 5), assisté de "
                    "défenseurs adjoints.",
        designation="Nommé par le pouvoir exécutif mais verrouillé par la double commission : c'est le "
                    "seul cas où le Parlement peut bloquer une nomination individuelle.",
        saisissable_par=("tout individu (gratuit, sans délai de recours contentieux suspendu ?) par saisine libre",
                         "les parlementaires, les élus, les associations", "autosaisine"),
        effets=("recommandation", "signalement", "constat", "injonction"),
        juge_par="Rien ne tranche ses recommandations : elles obligent à répondre, pas à obéir. Le "
                 "droit d'enquête est réel, la force juridique ne l'est pas.",
        observation="Il ne juge pas : il intervient par observations devant les juridictions et "
                    "publie des décisions. Le verrou ne vient donc pas d'une injonction, mais de la "
                    "publicité et du délai de réponse que l'administration doit motiver.",
        fiabilite="texte",
        leviers=("saisine_defenseur_des_droits",),
        pistes=("antidiscrimination_stats_locales",),
    ),
    "cnccfp": Instance(
        cle="cnccfp",
        nom="Commission nationale des comptes de campagne et des financements politiques",
        niveau="Financière",
        mission="Contrôler les comptes de campagne, approuver ou rejeter, et saisir le juge de "
                "l'inéligibilité.",
        fondement=("3",),
        composition="Neuf membres (Conseil d'État, Cour de cassation, Cour des comptes) ; mandat de "
                    "cinq ans renouvelable — à vérifier.",
        designation="Désignations par les trois ordres de juridiction : aucune autorité politique.",
        saisissable_par=("les candidats eux-mêmes par dépôt obligatoire", "le juge de l'éligibilité"),
        effets=("irrecevabilite", "signalement", "constat"),
        peut_bloquer=("transparence_seances",),
        juge_par="Le Conseil constitutionnel pour les élections nationales, le juge administratif pour "
                 "les locales : la CNCCFP ne se juge pas elle-même.",
        observation="Le rejet d'un compte n'est pas une sanction pénale, c'est une mort politique : "
                    "l'effet est automatique et immédiat. C'est un précédent de « verrou sans "
                    "jugement » qui peut être transposé (à vérifier avant de le proposer en scénario).",
        fiabilite="pratique",
        leviers=("reforme_casier_b2",),
        pistes=("plafond_dons_par_citoyen", "compte_rendu_temps_reel"),
    ),
    "conseil_economique_social_et_environnemental": Instance(
        cle="cese",
        nom="Conseil économique, social et environnemental",
        niveau="Consultative",
        mission="Consultation obligatoire pour les projets de loi de programme et d'orientation "
                "(art. 70) ; avis facultatif ; saisine populaire par pétition (art. 71).",
        fondement=("69", "70", "71"),
        composition="Membres désignés par organisations (salariés, employeurs, environnement, "
                    "outre-mer) — nombre et collèges fixés par l'ordonnance du 29 décembre 2004, à "
                    "vérifier.",
        designation="Désignations corporatives, pas élections : c'est ce que le RIC et la convention "
                    "citoyenne prétendent remplacer.",
        saisissable_par=("Gouvernement (avis obligatoire pour les lois de programme et de "
                         "orientation, art. 70)", "les deux assemblées", "une pétition citoyenne dont "
                         "le seuil dépend d'une loi organique jamais parue (art. 71 al. 3)"),
        effets=("avis", "constat", "irrecevabilite"),
        verrous=("lois_programmation_saisine_cee",),
        juge_par="Rien : un avis non rendu dans le délai ouvre la possibilité de publier "
                 "l'absence d'avis, mais ne bloque pas le texte. Le CESE est l'exemple type de "
                 "l'instance sans force.",
        observation="La seule fois où la pétition du CESE a fonctionné comme levier, c'est quand elle "
                    "a été relayée par une assemblée — l'avis n'a de poids que prêté.",
        fiabilite="a_verifier",
        leviers=("convention_citoyenne", "reforme_ric"),
        pistes=("seuil_pétition_cese", "avis_conforme_certaines_lois"),
    ),
    "prefet": Instance(
        cle="prefet",
        nom="Représentant de l'État dans la collectivité",
        niveau="Territoriale",
        mission="Charge des intérêts nationaux, du contrôle administratif et du respect des lois "
                "(art. 72 al. 4) ; à Paris, pouvoirs de police particuliers.",
        fondement=("72", "73", "CGCT_L1111_1", "CGCT_L1612_4"),
        composition="Un par département et par région, corps préfectoral nommément en conseil des "
                    "ministres (art. 13) pour les préfets.",
        designation="Nommé par décret en conseil des ministres : aucune élection, donc aucune "
                    "légitimité locale — c'est ce que le déféré préfectoral compense mal.",
        saisissable_par=("lui-même : le contrôle de légalité a été remplacé par une obligation de "
                         "transmission, l'illégalité étant ensuite jugée sur demande",
                         "tout administré par signalement"),
        effets=("sursis", "annulation", "mise_en_demeure", "constat"),
        peut_bloquer=("ordonnance_budgetaire",),
        juge_par="Le tribunal administratif, donc in fine le Conseil d'État ; ses actes sont "
                 "entièrement attaquables.",
        observation="Le vrai pouvoir n'est pas le déféré, c'est le délai : une transmission au "
                    "41e jour fait tomber un délibéré. C'est un levier sans texte, donc sans "
                    "recours possible contre l'opportunité.",
        fiabilite="pratique",
        leviers=("decentralisation",),
        pistes=("transmission_numerique_horodatee", "defere_obligatoire_motives"),
    ),
    "juridictions_administratives": Instance(
        cle="juridictions_administratives",
        nom="Tribunaux administratifs et cours administratives d'appel",
        niveau="Administratif",
        mission="Juger les actes des collectivités et de l'État, y compris les règlements locaux, les "
                "élections locales, le contentieux fiscal et social.",
        fondement=("72", "73", "74", "CGCT_L2121_1", "CGCT_L5217_1", "CGCT_L1612_4"),
        composition="Ordre administratif distinct de l'ordre judiciaire (art. 66) ; "
                    "ressort et nombre de juridictions à vérifier.",
        saisissable_par=("tout administré", "préfet", "concurrents (élections, commandes publiques)"),
        effets=("annulation", "injonction", "astreinte", "sursis"),
        juge_par="Conseil d'État (cassation en appel, plein contentieux en cassation).",
        observation="Le référé-liberté (48 heures) est l'arme la plus rapide du droit public "
                    "français, et elle est ouverte contre toute décision portant une atteinte grave "
                    "et manifestement illégale à une liberté — y compris un acte de campagne ou de "
                    "police municipale. Personne ne l'utilise à l'échelle.",
        fiabilite="pratique",
        leviers=("budget_justice",),
        pistes=("refere_liberte_collectif",),
    ),
    "cjue": Instance(
        cle="cjue",
        nom="Cour de justice de l'Union européenne",
        niveau="Européenne",
        mission="Assurer le respect des traités, répondre aux questions préjudicielles des juridictions "
                "nationales, juger les manquement.",
        fondement=("88-1", "TFUE_ART_126", "REGLEMENT_UE_2023_956", "REG_UE_2022_1854_SOLIDARITE"),
        composition="Un juge par État membre, avocats généraux ; sièges à Luxembourg.",
        designation="Communs d'un commun accord des gouvernements ; mandat renouvelable — détail à "
                    "vérifier.",
        saisissable_par=("Commission pour manquement", "un État contre un autre", "un particulier via "
                         "le juge national (renvoi préjudiciel, art. 267 TFUE)", "le Parlement et le "
                         "Conseil pour recours en annulation"),
        effets=("annulation", "sanction_financiere", "constat", "mise_en_demeure"),
        peut_bloquer=("subsidiarite",),
        juge_par="Personne : le droit de l'UE ne connaît pas de recours contre la CJUE — la "
                 "révision des traités est la seule porte, et elle est inexercée.",
        observation="Une question préjudicielle suspend le procès national mais aussi, en pratique, la "
                    "réforme en cours : l'attente fait loi. C'est le seul levier « externe » à la "
                    "portée d'un justiciable ordinaire.",
        fiabilite="texte",
        leviers=("integration_europeenne",),
        pistes=("cellule_nationale_de_questio_prejudicielle",),
    ),
    "cedh": Instance(
        cle="cedh",
        nom="Cour européenne des droits de l'homme",
        niveau="Internationale",
        mission="Juger les requêtes individuelles contre les États parties pour violation de la "
                "Convention (droit au procès, vie privée, expression, élections libres).",
        fondement=("55", "PREAMBULE_1946_AL11", "DDHC_ART_16"),
        composition="Un juge par État partie, élus par l'Assemblée parlementaire du Conseil de "
                    "l'Europe ; mandat non renouvelable ?",
        saisissable_par=("tout individu, après épuisement des voies de recours internes", "un État "
                         "contre un autre (rare)"),
        effets=("constat", "sanction_financiere", "mise_en_demeure"),
        juge_par="Le Comité des ministres du Conseil de l'Europe supervise l'exécution des arrêts : "
                 "c'est le seul endroit où une décision internationale devient une contrainte "
                 "budgétaire.",
        delais=(("délai de requête après la décision interne définitive", 120),),
        observation="Un arrêt de la CEDH ne défait pas le jugement national : il oblige à rouvrir — "
                    "et l'absence d'ouverture est une nouvelle violation. Le verrou est donc en "
                    "aval, dans le droit interne.",
        fiabilite="texte",
        leviers=("conformite_conventionnelle",),
        pistes=("reexamen_obligatoire_apres_cedh",),
    ),
    "commission_europeenne": Instance(
        cle="commission_europeenne",
        nom="Commission européenne",
        niveau="Européenne",
        mission="Initiative législative de l'Union, gardienne des traités, contrôle des aides d'État "
                "et du pacte budgétaire.",
        fondement=("88-1", "TFUE_ART_126", "REG_UE_2024_1263_CLAUSE"),
        saisissable_par=("plainte d'un particulier ou d'une entreprise", "un État", "elle-même "
                         "(autosaisine, notamment pour les aides d'État)"),
        effets=("mise_en_demeure", "constat", "sanction_financiere", "sursis"),
        peut_bloquer=(),
        juge_par="CJUE, en manquement comme en annulation.",
        observation="Une procédure de déficit excessif ouverte contre la France n'a jamais fait "
                    "reculer une réforme intérieure à elle seule : le calendrier, en revanche, oui.",
        fiabilite="pratique",
        leviers=("integration_europeenne",),
        pistes=("clauses_sociales_durables",),
    ),
    "conference_des_presidents": Instance(
        cle="conference_des_presidents",
        nom="Conférence des présidents de l'assemblée",
        niveau="Parlementaire",
        mission="Fixe l'ordre du jour et le calendrier, détermine la procédure de discussion, répartit "
                "le temps de parole (art. 48 al. 3, règlements).",
        fondement=("48", "51-2", "28"),
        saisissable_par=("les groupes, dont le poids arithmétique détermine tout",),
        effets=("irrecevabilite", "constat"),
        juge_par="Aucun : l'ordre du jour est un acte d'organisation interne,-insaisissable. C'est "
                 "le lieu exact où se logent les blocages sans voie de recours.",
        observation="Toute stratégie de calendrier dépend d'elle : saisir une assemblée entière est "
                    "impossible si la Conférence ne place pas. Le levier est donc la commission, pas "
                    "la séance.",
        fiabilite="pratique",
        leviers=("usage_49_3",),
        pistes=("ordre_du_jour_alternatif_reglementaire",),
    ),
    "commission_des_finances": Instance(
        cle="commission_des_finances",
        nom="Commission des finances (et commissions permanentes)",
        niveau="Parlementaire",
        mission="Examen en commission, rapports, pouvoirs d'amendement et de contrôle budgétaire ; "
                "rapporteur général, et depuis 2009 la mission d'évaluation et de contrôle (art. 51-1).",
        fondement=("43", "47", "51-1", "47-2", "LOLF_ART_34"),
        saisissable_par=("tout rapporteur, tout membre", "le Gouvernement pour demande de rapport"),
        effets=("irrecevabilite", "constat", "signalement"),
        juge_par="Aucun juge extérieur ; le contrôle est politique, par la Conférence et la séance.",
        observation="Le pouvoir réel du rapporteur général est la rédaction de l'exposé "
                    "sommaire : il fixe la doctrine d'interprétation de la loi de finances, que le "
                    "juge suit souvent.",
        fiabilite="pratique",
        leviers=("commande_publique", "simplification"),
        pistes=("audition_publique_obligatoire",),
    ),
    "office_et_missions_parlementaires": Instance(
        cle="office_et_missions_parlementaires",
        nom="Offices, missions d'évaluation et commissions d'enquête",
        niveau="Parlementaire",
        mission="Évaluer et contrôler : missions d'évaluation et de contrôle (art. 51-1), commissions "
                "d'enquête (fondement constitutionnel et réglementaire), offices sectoriels (art. 69 "
                "pour le conseil, création par résolution).",
        fondement=("51-1", "51-2", "69"),
        saisissable_par=("un groupe par session (résolution) ; droit ouvert par la révision de 2009",),
        effets=("signalement", "constat", "injonction"),
        verrous=("commission_enquete_signature",),
        juge_par="Le Conseil d'État sur les actes pris en cours d'enquête (communication de pièces) ; "
                 "le rapport, lui, n'est pas attaquable.",
        observation="Une commission d'auditionne sous serment : le faux témoignage devant elle est un "
                    "délit pénal (à vérifier avant citation). C'est le seul instrument parlementaire "
                    "avec une dent pénale.",
        fiabilite="pratique",
        leviers=("clause_revoyure_evaluation",),
        pistes=("commissions_permanentes",),
    ),
    "congres": Instance(
        cle="congres",
        nom="Congrès du Parlement",
        niveau="Constitutionnel",
        mission="Seule voie (avec le référendum de l'art. 11 tel qu'usité) d'approuver une révision "
                "constitutionnelle (art. 89).",
        fondement=("89",),
        saisissable_par=("le Président de la République, qui *peut* le convoquer quand la "
                         "deuxième lecture des deux assemblées n'a pas abouti identiquement (art. 89 "
                         "dernier alinéa)",),
        effets=("conformite_obligatoire", "constat"),
        verrous=("congres_revision",),
        juge_par="Aucun contrôle a posteriori : le Conseil constitutionnel s'est déclaré incompétent "
                 "sur la loi référendaire (décision du 6 novembre 1962) et ne censure pas une révision "
                 "adoptée par le Congrès — c'est la prémisse maîtresse des fentes d'en haut.",
        observation="Le seuil porte sur les *suffrages exprimés*, pas sur les membres : chaque "
                    "abstention abaisse le nombre de voix nécessaires. Rien dans le texte n'interdit "
                    "de le faire remarquer, et rien n'oblige à le dénoncer.",
        fiabilite="texte",
        leviers=("verrouillage_irreversibilite",),
        pistes=("seuil_congres_sur_membres",),
    ),
    "haute_cour": Instance(
        cle="haute_cour",
        nom="Haute Cour (art. 68 et 68-1)",
        niveau="Constitutionnel",
        mission="Juger le Président de la République pour « manquement à ses devoirs manifestement "
                "incompatible avec l'exercice de son mandat ».",
        fondement=("67", "68", "68-1", "68-2", "68-3"),
        saisissable_par=("un dixième des membres de chaque assemblée pour la proposition de "
                         "résolution (seuil à vérifier sur la loi organique)",),
        effets=("incompetence_declaree", "constat", "censure"),
        verrous=("haute_cour_assemblees", "haute_cour_destitution"),
        juge_par="Elle statue en dernier ressort, à la majorité des deux tiers (art. 68-1 al. 2) ; la "
                 "Une question de conventionnalité peut lui être posée par une juridiction française ; "
                 "l'état du contrôle de la CEDH sur ses propres arrêts en la matière est à vérifier.",
        observation="Le seuil des deux tiers est calculé sur les *membres*, pas sur les votants : contrairement "
                    "au Congrès, l'abstention ne sert à rien, elle nuit même. C'est une asymétrie "
                    "écrite, jamais commentée.",
        fiabilite="texte",
        leviers=("procedure_destitution",),
        pistes=("juridicite_destitution",),
    ),
    "senat": Instance(
        cle="senat",
        nom="Sénat",
        niveau="Parlementaire",
        mission="Seconde chambre : examiner, amender, retarder ; représentante des collectivités"
                "territoriales de la République (art. 24) ; pouvoir propre en outre-mer (art. 73 et 74).",
        fondement=("24", "39", "42", "45", "46", "47", "49", "50", "12", "16"),
        saisissable_par=(),
        effets=("avis", "sursis", "constat"),
        verrous=(),
        juge_par="Aucun : chaque assemblée est souveraine pour son règlement (art. 61 al. 1 pour le "
                 "contrôle a priori).",
        observation="Le Sénat ne peut pas bloquer une loi, il peut la faire attendre — et sur le "
                    "budget, 15 jours lui suffisent pour imposer un texte mort-né (art. 47 al. 2).",
        fiabilite="texte",
        leviers=("bicameralisme_equilibre",),
        pistes=("senat_territoires_plein",),
    ),
    "assemblee_nationale": Instance(
        cle="assemblee_nationale",
        nom="Assemblée nationale",
        niveau="Parlementaire",
        mission="Vote la loi, met en cause la responsabilité du Gouvernement, peut renverser le "
                "Gouvernement, dernière parole en cas de désaccord (art. 45 al. 4).",
        fondement=("24", "45", "49", "50", "12", "11", "47", "47-1"),
        verrous=("censure_signatures", "censure_voix", "49_3_delai_motion"),
        effets=("censure", "annulation"),
        juge_par="Aucun juge pour son vote, qui est l'expression de la souveraineté ; son "
                 "règlement, lui, est obligatoirement soumis au Conseil constitutionnel avant "
                 "d'être appliqué (art. 61 al. 1). C'est par le règlement qu'on peut la contraindre.",
        observation="Elle est la seule chambre dont le désaccord ne bloque pas : elle peut être "
                    "contrainte, mais pas empêchée. Le yoyo est donc à sens unique vers elle.",
        fiabilite="texte",
        leviers=("reforme_proportionnelle", "reforme_vote_blanc"),
        pistes=("droit_amendement_parlementaire",),
    ),
    "collectivites_outre_mer": Instance(
        cle="collectivites_outre_mer",
        nom="Collectivités d'outre-mer (art. 72-3 à 74)",
        niveau="Territoriale",
        mission="Adapter le droit national à leur organisation ; certaines fixent elles-mêmes des "
                "règles dans des matières délimitées (art. 73 et 74).",
        fondement=("72-3", "73", "74", "74-1", "77"),
        saisissable_par=("leurs assemblées par « consultation » ou « proposition de "
                         "résolution » transmises au Gouvernement (à vérifier avant citation)",),
        effets=("conformite_obligatoire", "constat", "avis"),
        peut_bloquer=("petition_72_1", "referendum_local"),
        juge_par="Le Conseil constitutionnel pour les lois organiques qui fixent leur statut, le "
                 "Conseil d'État pour leurs actes d'application ; le contrôle du droit de l'Union "
                 "dépend du protocole applicable à chaque collectivité — à vérifier avant citation.",
        observation="Un congrès local peut se réunir pour demander une évolution institutionnelle, et "
                    "le Gouvernement n'est tenu que de transmettre ; la consultation, elle, est "
                    "obligatoire dans les cas prévus — c'est un levier à double détente.",
        fiabilite="texte",
        leviers=("decentralisation",),
        pistes=("conference_permanente_outre_mer",),
    ),
}

#: Deux familles de délais, à ne jamais mélanger : les délais d'office (ce que l'instance
#: doit faire, en son for interne) et les délais de recours (ce qui est imposable aux
#: autres). Le champ `delais` ne porte que les premiers ; les seconds vivent dans les
#: verrous chiffrés du module des contre-pouvoirs.


# ── LE YOYO : CHAQUE BATTEMENT A UN COÛT EN JOURS ET EN VOIX ───────────────────
# Une navette n'est pas une métaphore. Chaque battement a un article pour lui, un délai
# chiffré, un sens (il avance, il recule, il bloque, il verrouille) et un coût politique.
# Les nombres viennent des fiches du module `constitution_analysee` : ils n'y sont pas
# réécrits à la main, ils sont cités par l'article qui les porte.


@dataclass(frozen=True)
class Battement:
    """Un aller-retour du texte entre deux acteurs, avec son délai constitutionnel."""

    cle: str
    de: str                       # clé d'`INSTANCES` ou acteur décrit en toutes lettres
    vers: str
    acte: str
    fondement: str = ""           # numéro d'article qui autorise le battement
    jours: int = 0                # délai maximal ou délai de rigueur, 0 = pas de délai
    sens: str = "avancer"         # avancer | reculer | bloquer | verrouiller
    condition: str = ""
    note: str = ""

    def en_dict(self) -> Dict[str, Any]:
        return {
            "cle": self.cle,
            "de": self.de,
            "vers": self.vers,
            "acte": self.acte,
            "fondement": f"Article {self.fondement}" if self.fondement in ARTICLES else self.fondement,
            "jours": self.jours,
            "sens": self.sens,
            "condition": self.condition,
            "note": self.note,
            "reversible": self.sens != "verrouiller",
        }


@dataclass(frozen=True)
class Trajet:
    """Une suite ordonnée de battements : le chemin réel d'un texte ou d'une manœuvre."""

    cle: str
    nom: str
    categorie: str                # legislatif | budgetaire | constitutionnel | controle | exception
    etapes: Tuple[Battement, ...]
    articles: Tuple[str, ...] = ()
    issue: str = ""
    blocages: Tuple[str, ...] = ()      # clés de mécanismes capables d'arrêter le trajet
    note: str = ""

    def en_dict(self, donnees: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        etapes = [b.en_dict() for b in self.etapes]
        jours = sum(b.jours for b in self.etapes)
        return {
            "cle": self.cle,
            "nom": self.nom,
            "categorie": self.categorie,
            "articles": list(self.articles),
            "etapes": etapes,
            "battements": len(etapes),
            "jours_theoriques": jours,
            "jours_bloquants": sum(b.jours for b in self.etapes if b.sens in ("reculer", "bloquer")),
            "blocages": [
                {"cle": c, "nom": MECANISMES[c].nom} for c in self.blocages if c in MECANISMES
            ],
            "issue": self.issue,
            "note": self.note,
        }


#: Constat du 12 octobre 2026, pas une loi : le temps politique restant avant la fin de
#: la session. Il sert à répondre à « est-ce que ça passe encore ? », jamais à prédire.
FENETRE_RESIDUELLE_JOURS = 150
FENETRE_RESIDUELLE_NOTE = (
    "Cinq mois de fenêtre législative résiduelle constatés au 12 octobre 2026 : au-delà, "
    "l'ordre du jour est suspendu de plein droit. Ce nombre ne vient d'aucun texte — c'est "
    "le seul chiffre du module qui soit un constat daté, et il doit être recalculé à chaque "
    "revue."
)


def _b(cle: str, de: str, vers: str, acte: str, fondement: str = "", jours: int = 0,
       sens: str = "avancer", condition: str = "", note: str = "") -> Battement:
    return Battement(cle, de, vers, acte, fondement, jours, sens, condition, note)


TRAJETS: Dict[str, Trajet] = {
    "projet_ordinaire": Trajet(
        cle="projet_ordinaire",
        nom="Projet de loi ordinaire, procédure avec procédure accélérée",
        categorie="legislatif",
        articles=("39", "42", "43", "44", "45", "46", "10", "61"),
        etapes=(
            _b("conseil_ministres", "gouvernement", "conseil_des_ministres",
               "Délibération avant dépôt", "39", 0, "avancer",
               condition="Obligatoire pour un projet : sans elle, le dépôt est irrégulier.",
               note="Aucun délai : le Gouvernement peut laisser mûrir, et un projet qui traîne "
                    "au Conseil d'État n'est jamais en retard."),
            _b("conseil_etat_avis", "gouvernement", "conseil_etat",
               "Demande d'avis", "39", 30, "avancer",
               condition="Avis obligatoire sur les projets de loi et d'ordonnance.",
               note="L'avis n'est pas public et ne se conteste pas : c'est un pouvoir de "
                    "réécriture du texte avant même qu'il n'existe."),
            _b("depot", "gouvernement", "conference_des_presidents",
               "Inscription à l'ordre du jour", "48", 15, "avancer",
               condition="Quinze jours francs après dépôt pour un texte non accéléré, sauf urgence.",
               note="Un texte transmis depuis six semaines a priorité d'inscription : attendre ne sert"
                    "pas à le faire tomber, mais à user du retard comme d'une arme sur l'agenda."),
            _b("commission", "conference_des_presidents", "commission_permanente",
               "Examen en commission et dépôt du rapport", "43", 0, "avancer",
               condition="Le texte discuté en séance est celui de la commission, pas celui du dépôt.",
               note="Battement le plus sous-estimé du trajet : la commission réécrit l'essentiel du"
                    "texte avant la lumière, et son rapport lie la discussion."),
            _b("seance_an", "commission_permanente", "assemblee_nationale",
               "Première lecture en séance", "42", 42, "avancer",
               condition="Six semaines après le dépôt devant la première assemblée (quatre "
                         "devant la seconde) ; quinze jours en procédure accélérée.",
               note="Les motions d'obstruction (préalable, exception d'irrecevabilité, question "
                    "préalable, renvoi) se jouent ici, avant le fond."),
            _b("senat", "assemblee_nationale", "senat",
               "Examen et amendent du Sénat", "42", 28, "reculer",
               condition="Quatre semaines avant la discussion en séance, six sans accélérée.",
               note="Le Sénat ne peut que retarder ou enrichir : sur une loi ordinaire, son "
                    "rejet n'y change rien."),
            _b("cmp", "senat", "commission_mixte_paritaire",
               "Commission mixte paritaire (sept plus sept)", "45", 0, "bloquer",
               condition="Une seule réunion ; son échec doit être constaté.",
               note="Le seul battement où sept députés et sept sénateurs peuvent écrire un texte "
                    "que les 577 et les 348 n'avaient pas voté."),
            _b("nouvelle_lecture", "commission_mixte_paritaire", "assemblee_nationale",
               "Nouvelle lecture et dernier mot", "45", 0, "verrouiller",
               condition="L'Assemblée nationale statue définitivement ; elle peut reprendre le "
                         "texte de la CMP ou son dernier texte amendé par le Sénat.",
               note="Verrou : à partir d'ici, plus aucune chambre haute ne peut s'y opposer."),
            _b("saisine", "assemblee_nationale", "conseil_constitutionnel",
               "Saisine éventuelle avant promulgation", "61", 30, "bloquer",
               condition="Soixante députés ou soixante sénateurs ; un mois, huit jours si "
                         "l'urgence a été déclarée.",
               note="Dernier battement utile pour une opposition : après la promulgation, seule "
                    "la QPC reste, et elle ne vise que les dispositions législatives."),
            _b("promulgation", "conseil_constitutionnel", "president_de_la_republique",
               "Promulgation", "10", 15, "verrouiller",
               condition="Quinze jours à compter de la transmission, suspendus par une saisine.",
               note="Verrou définitif : la promulgation rend la loi exécutoire et le délai "
                    "présidentiel n'a jamais été utilisé pour bloquer — le droit de renvoyer en "
                    "nouvelle délibération, si."),
        ),
        issue="Le texte est promulgué, amendé ou censuré ; la fenêtre de contestation se ferme "
              "à la promulgation, et se rouvre partiellement par la QPC au procès.",
        blocages=("motion_censure", "article_49_3", "irrecevabilite_financiere", "vote_bloque",
                  "saisine_conseil", "commission_mixte_paritaire"),
        note="Total des délais de rigueur : quatre-vingt-dix jours de navette accélérée, sans "
             "compter les semaines de séance ni les deux semaines de saisine.",
    ),
    "budget": Trajet(
        cle="budget",
        nom="Loi de finances : le calendrier qui ne pardonne pas",
        categorie="budgetaire",
        articles=("47", "58", "40", "44", "47-1", "16"),
        etapes=(
            _b("conseil_ministres", "gouvernement", "conseil_des_ministres",
               "Délibération du projet de loi de finances", "39", 0, "avancer",
               condition="Première assemblée saisie : l'Assemblée nationale, obligatoirement (39 al. 2)."),
            _b("depot_obligatoire", "gouvernement", "assemblee_nationale",
               "Dépôt du PLF", "47", 0, "avancer",
               condition="Dépôt sur le bureau de l'AN au plus tard le premier mardi d'octobre.",
               note="Ce délai n'est assorti d'aucune sanction sur le dépôt lui-même : la sanction "
                    "tombe sur les recettes, pas sur le Gouvernement."),
            _b("an_vote", "assemblee_nationale", "assemblee_nationale",
               "Premier vote de l'Assemblée", "47", 40, "avancer",
               condition="L'AN doit se prononcer en premier lieu dans les quarante jours.",
               note="À défaut de se prononcer, le Gouvernement saisit le Sénat : le temps "
                    "parlementaire est converti en temps gouvernemental."),
            _b("senat", "assemblee_nationale", "senat",
               "Examen par le Sénat", "47", 15, "reculer",
               condition="Le Sénat dispose de quinze jours, en premier comme en seconde lecture.",
               note="Quinze jours pour amender un budget de cinq cents pages : le Sénat ne peut "
                    "que faire des propositions, pas des blocages."),
            _b("cmp", "senat", "commission_mixte_paritaire",
               "Commission mixte paritaire", "45", 8, "bloquer",
               condition="La CMP est convoquée après le désaccord : elle a une réunion, pas un"
                         "délai constitutionnel.",
               note="Sur le budget, la CMP aboutit presque toujours : soixante-dix jours au total "
                     "n'autorisent pas le luxe d'un échec."),
            _b("nouvelle_lecture", "commission_mixte_paritaire", "assemblee_nationale",
               "Nouvelle lecture et dernier mot", "45", 0, "verrouiller",
               condition="L'AN statue définitivement ; le Sénat ne peut plus que rejeter.",
               note="Verrou : après la dernière lecture, la chambre haute constate, elle ne se"
                    "négocie plus."),
            _b("soixante_dix_jours", "assemblee_nationale", "gouvernement",
               "Issue à soixante-dix jours", "47", 70, "verrouiller",
               condition="Si le Parlement ne s'est pas prononcé dans les soixante-dix jours, le "
                         "Gouvernement peut mettre en vigueur par ordonnance.",
               note="Le battement le plus commenté et le moins utilisé : son existence suffit à "
                    "faire accepter des délais que le Parlement n'accepterait pas sinon."),
            _b("saisine", "gouvernement", "conseil_constitutionnel",
               "Saisine obligatoire de la loi de finances", "61", 15, "bloquer",
               condition="Loi de finances : saisine obligatoire du Conseil constitutionnel.",
               note="C'est le seul grand texte dont la conformité est vérifiée à coup sûr avant "
                    "promulgation — et donc le seul dont les arbitrages internes ne peuvent pas "
                    "être cachés au juge."),
        ),
        issue="Soixante-dix jours, ou le budget passe par ordonnance. Le calendrier remplace le vote.",
        blocages=("motion_censure", "article_49_3", "ordonnance_budgetaire", "irrecevabilite_financiere"),
        note="Calendrier réel constaté : PLF 2027 présenté en conseil des ministres le "
             "1er octobre 2026, déposé le 6 octobre 2026, échéance des soixante-dix jours le "
             "26 novembre 2026.",
    ),
    "revision_congres": Trajet(
        cle="revision_congres",
        nom="Révision constitutionnelle par la voie du Congrès",
        categorie="constitutionnel",
        articles=("89", "42", "61", "46"),
        etapes=(
            _b("initiative", "gouvernement", "conseil_des_ministres",
               "Initiative présidentielle ou gouvernementale", "89", 0, "avancer",
               condition="Pas d'initiative parlementaire en matière de révision.",
               note="Le premier verrou est là : aucune opposition ne peut inscrire une révision, "
                    "elle peut seulement la subir ou la voter."),
            _b("premiere_assemblee", "conseil_des_ministres", "assemblee_nationale",
               "Première délibération", "42", 42, "avancer",
               condition="Six semaines avant la discussion en séance (délais de l'art. 42 al. 3)."),
            _b("seconde_assemblee", "assemblee_nationale", "senat",
               "Seconde délibération", "42", 28, "bloquer",
               condition="Quatre semaines ; et surtout : vote en termes identiques exigé.",
               note="C'est le seul grand trajet où le Sénat a un veto réel : ni CMP, ni dernier "
                    "mot. Un Sénat hostile enterre la révision, il ne la retarde pas."),
            _b("choix_de_la_voie", "senat", "president_de_la_republique",
               "Congrès ou référendum", "89", 0, "verrouiller",
               condition="Le Président choisit ; le Congrès n'exige que les trois cinquièmes des "
                         "suffrages exprimés.",
               note="Le battement le plus rentable de tout le droit constitutionnel : le seuil "
                    "porte sur les exprimés, donc sur ceux qui votent. Chaque abstention baisse "
                    "le nombre de voix requises — calcul vérifié par le module des contre-pouvoirs."),
            _b("vote_congres", "president_de_la_republique", "congres",
               "Vote en Congrès", "89", 0, "verrouiller",
               condition="555 suffrages sur une base de 925 au 12 octobre 2026 ; scrutins publics.",
               note="Aucune saisine du Conseil constitutionnel n'est ouverte après le vote : la "
                    "révision promulguée échappe au contrôle a priori comme a posteriori."),
            _b("promulgation", "congres", "president_de_la_republique",
               "Promulgation", "10", 15, "verrouiller",
               condition="Quinze jours.",
               note="Une révision est verrouillée à l'étage le plus haut : il en faudra une autre "
                    "pour la défaire, donc les mêmes trois cinquièmes, ou un référendum."),
        ),
        issue="Trois verrous successifs : initiative fermée, veto du Sénat, seuil des exprimés. "
              "Le quatrième — l'absence de juge après coup — est le plus solide.",
        blocages=("revision_constitutionnelle", "referendum_legislatif", "saisine_conseil"),
        note="Deux matières échappent à la révision : la forme républicaine du gouvernement et le"
             "principe du suffrage universel, égal et secret — à citer sur l'alinéa exact de"
             "l'article 89 après vérification.",
    ),
    "revision_referendum": Trajet(
        cle="revision_referendum",
        nom="Réforme institutionnelle par l'article 11 (voie référendaire)",
        categorie="constitutionnel",
        articles=("11", "61", "10", "58"),
        etapes=(
            _b("initiative", "gouvernement", "conseil_des_ministres",
               "Délibération et projet de loi", "11", 0, "avancer",
               condition="Objet limité : l'organisation des pouvoirs publics, les réformes "
                         "relatives à la politique économique, sociale ou environnementale et "
                         "les services publics qui en concourent.",
               note="La frontière avec l'article 89 n'est tracée nulle part : c'est le point "
                    "d'appui de toute la controverse."),
            _b("parlement", "conseil_des_ministres", "assemblee_nationale",
               "Débat et vote des deux assemblées", "11", 0, "avancer",
               condition="Le texte doit être délibéré par les deux assemblées en termes identiques.",
               note="Un refus du Parlement n'enterre pas la réforme : il ne fait que fermer la "
                    "voie de la promulgation immédiate."),
            _b("saisine_obligatoire", "assemblee_nationale", "conseil_constitutionnel",
               "Saisine obligatoire avant la promulgation ?", "61", 30, "bloquer",
               condition="Le Conseil constitutionnel est compétent pour la loi votée par le "
                         "Parlement, pas pour la loi référendaire (décision du 6 novembre 1962).",
               note="Le battement manquant : entre le vote parlementaire et le référendum, "
                    "personne ne juge. C'est l'exemple même de la fente non écrite."),
            _b("referendum", "president_de_la_republique", "peuple",
               "Référendum", "11", 0, "verrouiller",
               condition="Aucun seuil de participation exigé par la Constitution.",
               note="Une abstention massive peut donc faire passer une réforme avec une minorité "
                    "de suffrages exprimés — ce n'est écrit nulle part, et c'est exactement ce "
                    "que le texte autorise."),
            _b("promulgation", "peuple", "president_de_la_republique",
               "Promulgation dans les quinze jours", "10", 15, "verrouiller",
               condition="Promulgation, puis publication.",
               note="Verrou absolu : la loi référendaire ne peut être ni censurée ni "
                    "révisée par la voie ordinaire ; seule une autre loi référendaire y "
                    "revient, ou un engagement international pris après."),
        ),
        issue="Voie la plus verrouillée du droit français, et la moins contrôlée : ce qui la "
              "rend forte est exactement ce qui la rend inquiétante.",
        blocages=("referendum_legislatif", "saisine_conseil", "motion_censure"),
        note="Précédent fondateur : 1962, l'élection du Président au suffrage universel direct,"
             "engagée par l'article 11 après un vote défavorable sur le projet de révision (détail de"
             "chronologie à vérifier avant publication). La révision de 2008 a écarté l'idée de"
             "soumettre les lois référendaires au Conseil constitutionnel : le silence est donc"
             "entretenu, et non ignoré.",
    ),
    "renversement": Trajet(
        cle="renversement",
        nom="Renverser le Gouvernement : le yoyo le plus court",
        categorie="exception",
        articles=("49", "50", "12", "51-1"),
        etapes=(
            _b("depot", "opposition", "assemblee_nationale",
               "Dépôt d'une motion de censure motivée et signée", "49", 0, "avancer",
               condition="Dixième des membres (58 signatures) ; trois motions par session pour un "
                         "même signataire.",
               note="Le dépôt est public immédiatement : la sanction politique précède le vote."),
            _b("delai", "assemblee_nationale", "assemblee_nationale",
               "Délai de quarante-huit heures", "49", 2, "bloquer",
               condition="Le vote ne peut intervenir avant deux jours francs.",
               note="Deux jours pour négocier les abstentions : c'est le seul battement où le "
                    "temps travaille pour l'initiative."),
            _b("vote", "assemblee_nationale", "assemblee_nationale",
               "Vote à la majorité des membres composant l'Assemblée", "49", 0, "verrouiller",
               condition="289 voix sur 577, quel que soit le nombre de votants.",
               note="Asymétrie décisive : ici l'abstention sert le Gouvernement, contrairement au "
                    "Congrès. Le yoyo retourne la même arithmétique selon l'assiette."),
            _b("chute", "assemblee_nationale", "president_de_la_republique",
               "Démission du Gouvernement", "50", 0, "verrouiller",
               condition="Le Président *doit* prendre acte ; aucun pouvoir de dissoudre à la place.",
               note="À vérifier dans la jurisprudence : la dissolution de 1962 a suivi une "
                    "défaite, jamais remplacé une censure."),
            _b("dissolution", "president_de_la_republique", "peuple",
               "Dissolution après une censure ?", "12", 0, "bloquer",
               condition="Interdite dans l'année qui suit une dissolution ; jamais pendant "
                         "l'article 16.",
               note="Le battement qui ferme la boucle : la censure ne peut plus être "
                    "immédiatement révoquée par les urnes, et c'est ce qui la rend sérieuse."),
        ),
        issue="Un seul vote, une seule assiette : tout se joue sur la distinction entre "
              "« membres » et « exprimés ».",
        blocages=("motion_censure", "article_49_3", "dissolution", "engagement_responsabilite"),
        note="Aucune motion de censure n'a été adoptée sous la Ve République. Le décompte de la"
             "motion de 1967 est à vérifier avant publication : les dépôts et les rejets sont"
             "documentés, pas les chiffres précis.",
    ),
    "controle_juge": Trajet(
        cle="controle_juge",
        nom="Faire juger une loi par la QPC : le trajet le plus lent",
        categorie="controle",
        articles=("61-1", "37", "55", "53"),
        etapes=(
            _b("instance", "justiciable", "juge_du_fond",
               "Écriture distincte et motivée devant la juridiction du fond", "61-1", 0, "avancer",
               condition="Doit être soulevée devant le juge du fond, « à l'occasion d'une instance ».",
               note="Elle ne peut pas être soulevée d'office, ni par un avocat seul sans client : "
                    "la fente est dans l'obligation de la partie, pas du juge."),
            _b("filtre", "juge_du_fond", "conseil_etat_ou_cour_de_cassation",
               "Trois conditions : applicabilité, absence de censure antérieure, sérieux", "61-1", 0,
               "bloquer",
               note="Le filtre est un pouvoir de non-jugement : il ne motive presque jamais au "
                    "fond, et ne se conteste pas."),
            _b("renvoi", "conseil_etat_ou_cour_de_cassation", "conseil_constitutionnel",
               "Décision de renvoi dans les trois mois", "61-1", 90, "avancer"),
            _b("jugement", "conseil_constitutionnel", "conseil_constitutionnel",
               "Trois mois pour trancher", "61-1", 90, "verrouiller",
               condition="Délais réduits à un mois en cas d'urgence, sursis à exécution possible.",
               note="Pratique constatée au premier semestre 2026 : soixante-quinze jours en moyenne — "
                    "le texte ne promet pas ces délais, la pratique les tient."),
            _b("effet", "conseil_constitutionnel", "toutes_les_juridictions",
               "Abrogation et effet sur les instances non jugées", "62", 0, "verrouiller",
               condition="L'abrogation est applicable à toutes les affaires non jugées définitivement.",
               note="Le battement le plus sous-estimé du droit français : une décision de QPC "
                    "rouvre des procès clos en appel mais pas encore pourvus en cassation."),
        ),
        issue="Deux ans de procédure pour faire censurer une disposition : la QPC n'est pas une "
              "arme rapide, c'est une pelle.",
        blocages=("qpc", "saisine_conseil", "niche_parlementaire"),
        note="La QPC ne juge pas les règlements et ne rouvre pas les affaires tranchées en"
             "dernier ressort : son effet est borné par l'article 62 lui-même.",
    ),
    "compte_a_rebours_local": Trajet(
        cle="compte_a_rebours_local",
        nom="Faire plier une décision locale : le contentieux de l'acte",
        categorie="controle",
        articles=("72", "39", "37", "34"),
        etapes=(
            _b("deliberation", "elu_local", "collectivite",
               "Délibération de l'assemblée locale", "72", 0, "avancer",
               condition="Caractère exécutoire après transmission au représentant de l'État.",
               note="La transmission ne valide pas : elle ouvre le délai pendant lequel le "
                    "préfet peut déférer et le juge suspendre."),
            _b("transmission", "collectivite", "prefet",
               "Transmission et contrôle de légalité", "72", 30, "avancer",
               condition="Le préfet peut déférer et demander la suspension.",
               note="Le vrai levier est le 41e jour : une délibération devenue exécutoire se "
                    "défère encore, mais ne se suspend plus aussi vite."),
            _b("recours", "administré", "tribunal_administratif",
               "Recours pour excès de pouvoir et référé-suspension", "72", 0, "bloquer",
               condition="Deux mois pour le REC ; suspension si l'urgence et le doute sont "
                         "réunis (référé-liberté : quarante-huit heures).",
               note="Le juge annule l'acte, jamais la délibération future : on ne gagne pas une "
                    "politique, on gagne un délai."),
            _b("injonction", "tribunal_administratif", "collectivite",
               "Injonction et astreinte", "72", 0, "verrouiller",
               condition="Le juge peut commander une inscription budgétaire ou la reprise d'un "
                         "agent illégalement écarté.",
               note="Verrou : une délibération annulée est réputée n'avoir jamais existé ; si "
                    "l'exécution de la loi locale est engagée entre-temps, la collectivité a "
                    "créé des droits que l'annulation ne supprime pas."),
        ),
        issue="Au niveau local, la force ne vient pas du vote : elle vient du délai de "
              "transmission et de l'urgence.",
        blocages=("petition_72_1", "referendum_local", "audit_cour_des_comptes"),
        note="Le budget de droit (art. L. 1612-4 CGCT) et l'inscription d'office sont les deux "
             "seuls cas où le préfet écrit à la place de l'assemblée : c'est un pouvoir "
             "réglmentaire, pas constitutionnel.",
    ),
    "initiative_citoyenne": Trajet(
        cle="initiative_citoyenne",
        nom="RIP : le trajet qui n'a jamais abouti",
        categorie="constitutionnel",
        articles=("11", "45", "61", "58"),
        etapes=(
            _b("proposition", "opposition_parlementaire", "conseil_constitutionnel",
               "Proposition de loi signée par un cinquième des membres des deux assemblées", "11", 0,
               "avancer", condition="185 signatures sur 925 ; contrôle de conformité par le Conseil.",
               note="Premier filtre, politique : les auteurs sont nommément publics."),
            _b("soutien", "peuple", "conseil_constitutionnel",
               "Un dixième des électeurs inscrits", "11", 0, "bloquer",
               condition="Quatre-vingt-dix jours de collecte pour un dixième des électeurs inscrits,"
                         "soit environ 4 900 000 soutiens (art. 11 al. 2 et loi organique du"
                         "6 novembre 2013).",
               note="Aucun RIP n'a abouti depuis 2008 ; le nombre de soutiens effectivement"
                    "recueillis à chaque tentative est à vérifier avant publication."),
            _b("examen", "conseil_constitutionnel", "assemblee_nationale",
               "Inscription et examen par les deux assemblées", "11", 0, "avancer",
               condition="Six mois devant l'AN, trois devant le Sénat ; à défaut d'inscription, "
                         "le Président *peut* soumettre au référendum.",
               note="Le battement qui rend tout possible et rien obligatoire : le délai "
                    "n'est assorti d'aucune sanction pour l'assemblée qui n'inscrit pas."),
            _b("referendum", "president_de_la_republique", "peuple",
               "Soumission au référendum", "11", 0, "verrouiller",
               condition="Interdiction d'abroger une disposition promulguée depuis moins d'un an.",
               note="Et deux ans avant une nouvelle proposition de même objet après un rejet : "
                    "le yoyo est amorti par un délai de carence, écrit lui."),
        ),
        issue="Le seul trajet du droit français où chaque étape est franchissable et où aucune "
              "n'est jamais franchie : les verrous sont des délais sans sanction.",
        blocages=("rip", "referendum_legislatif", "saisine_conseil"),
        note="Le mécanisme a été verrouillé en pratique par l'exigence d'initiative parlementaire "
             "concomitante : sans 185 signatures, la collecte n'existe pas.",
    ),
}


def trajet(cle: str) -> Optional[Trajet]:
    """Trajet par sa clé, tolérant aux notations usuelles (« budget », « 47 »)."""
    if not cle:
        return None
    propore = cle.strip().lower().replace(" ", "_").replace("/", "_")
    if propore in TRAJETS:
        return TRAJETS[propore]
    for cle_trajet, value in TRAJETS.items():
        if propore in cle_trajet or propore in {a.lower() for a in value.articles}:
            if propore == cle_trajet:
                return value
    # Recherche par article : « 47 » doit mener au trajet budgétaire, pas au premier.
    candidats = [(c, t) for c, t in TRAJETS.items() if propore in t.articles]
    if len(candidats) == 1:
        return candidats[0][1]
    return None


def oscillation(cle: str, jours_restants: Optional[int] = None) -> Dict[str, Any]:
    """Le trajet traduit en temps : ce qui reste, ce qui bloque, ce qui verrouille.

    Le calcul est déterministe et borné par les délais de rigueur des articles cités :
    aucune probabilité, aucune prédiction.
    """
    value = trajet(cle) if isinstance(cle, str) else cle
    if value is None:
        return {"erreur": "trajet inconnu", "trajets": sorted(TRAJETS)}
    reste = FENETRE_RESIDUELLE_JOURS if jours_restants is None else int(jours_restants)
    lignes = [b.en_dict() for b in value.etapes]
    jours = sum(b.jours for b in value.etapes)
    bloquants = [b for b in value.etapes if b.sens in ("reculer", "bloquer")]
    verrous_de_txt = [b for b in value.etapes if b.sens == "verrouiller"]
    depot = sum(b.jours for b in value.etapes)
    etapes_tenables = 0
    cumul = 0
    for battement in value.etapes:
        cumul += battement.jours
        if cumul <= reste:
            etapes_tenables += 1
    return {
        "cle": value.cle,
        "nom": value.nom,
        "categorie": value.categorie,
        "battements": len(lignes),
        "etapes": lignes,
        "jours_de_rigueur": jours,
        "jours_des_verrous": sum(b.jours for b in verrous_de_txt),
        # Retard imposable : les battements qui reculent ou bloquent, en jours de rigueur.
        "retard_imposable": sum(b.jours for b in bloquants),
        "tenable_dans_la_fenetre": etapes_tenables == len(value.etapes),
        "etapes_tenables": etapes_tenables,
        "fenetre_residuelle": {
            "jours": reste,
            "note": FENETRE_RESIDUELLE_NOTE,
            "restant_apres_trajet": reste - depot,
        },
        "article_cles": list(value.articles),
        "issue": value.issue,
    }


def asymetrie_des_chambres() -> List[Dict[str, Any]]:
    """Ce que le Sénat peut retarder, ce qu'il peut empêcher — trajet par trajet.

    La règle non écrite du bicamérisme français tient en une distinction : sur une loi
    ordinaire, le désaccord se résout par l'Assemblée nationale ; sur une révision et sur
    les lois organiques intéressant le Sénat, il ne se résout pas.
    """
    sorties = []
    # Les deux derniers trajets ne sont pas des navettes ordinaires, mais ce sont eux
    # qui portent un veto : c'est justement la comparaison qui intéresse.
    for cle in ("projet_ordinaire", "budget", "revision_congres", "revision_referendum"):
        value = TRAJETS[cle]
        retard = sum(b.jours for b in value.etapes if b.de == "assemblee_nationale"
                     and b.vers in ("senat", "commission_mixte_paritaire"))
        peut_empecher = any(
            b.vers == "senat" and b.sens == "bloquer" for b in value.etapes
        ) or cle == "revision_congres"
        sorties.append({
            "trajet": cle,
            "nom": value.nom,
            "jours_de_retard_imposables": retard,
            "veto_reel": peut_empecher,
            "fondement_du_veto": "89 al. 4 (termes identiques exigés)" if peut_empecher
                                 else "45 al. 4 (dernier mot de l'Assemblée)",
        })
    return sorties


def rapport_de_temps() -> Dict[str, Any]:
    """Vue d'ensemble : quels battements usent qui, en jours de rigueur."""
    par_sens: Dict[str, Dict[str, int]] = {}
    for value in TRAJETS.values():
        for battement in value.etapes:
            case = par_sens.setdefault(battement.sens, {"battements": 0, "jours": 0})
            case["battements"] += 1
            case["jours"] += battement.jours
    return {
        "trajets": len(TRAJETS),
        "battements": sum(len(v.etapes) for v in TRAJETS.values()),
        "par_sens": par_sens,
        "fenetre_residuelle_jours": FENETRE_RESIDUELLE_JOURS,
        "avertissement": (
            "Les jours sont des délais de rigueur, pas des durées prévisibles : ils "
            "disent ce que la procédure peut imposer, pas ce qu'elle prendra."
        ),
    }


INSTANCES["president_de_la_republique"] = Instance(
    cle="president_de_la_republique",
    nom="Président de la République",
    niveau="Constitutionnel",
    mission="Arbitre : promulgue, peut dissoudre, préside le Conseil des ministres, saisit le "
            "Congrès, dispose des pouvoirs exceptionnels (art. 5, 10, 11, 12, 16).",
    fondement=("5", "8", "10", "11", "12", "13", "16", "56", "58", "61", "89"),
    composition="Une personne, élue pour cinq ans au suffrage universel direct (art. 6).",
    designation="Élection à deux tours, sur présentation par cinq cents élus (art. 58 et loi "
                "organique) — seuil contesté, débat permanent.",
    saisissable_par=(),
    effets=("conformite_obligatoire", "annulation", "constat"),
    peut_bloquer=("dissolution", "vacance_presidentielle", "pouvoirs_exceptionnels"),
    verrous=("dissolution_carence", "vacance_delai_scrutin", "presidentielle_parrainages"),
    juge_par="La Haute Cour pour les manquements à ses devoirs (art. 68) ; rien pour ses "
             "décisions d'arbitrage, qui ne sont pas des actes administratifs.",
    observation="Presque tous ses pouvoirs sont des pouvoirs de calendrier ou de regard : c'est "
                "ce qui rend ses décisions peu attaquables et politiquement très coûteuses.",
    fiabilite="texte",
)
INSTANCES["gouvernement"] = Instance(
    cle="gouvernement",
    nom="Gouvernement (Premier ministre et ministres)",
    niveau="Constitutionnel",
    mission="Détermine et conduit la politique de la nation ; dispose de l'administration et de "
            "la force armée ; exerce le pouvoir réglementaire (art. 20, 21, 37 al. 1).",
    fondement=("8", "9", "13", "20", "21", "34", "37", "38", "39", "40", "41", "44", "47", "49"),
    composition="Le Premier ministre, puis les ministres nommés sur sa proposition (art. 8).",
    designation="Nommé par le Président de la République ; renversable par l'Assemblée nationale.",
    saisissable_par=(),
    effets=("conformite_obligatoire", "injonction", "constat"),
    peut_bloquer=("engagement_responsabilite", "article_49_3", "ordonnances", "procedure_acceleree",
                  "defossilisation", "irrecevabilite_financiere"),
    verrous=("49_3_plafond_texte", "49_3_delai_motion", "irrecevabilite_financiere"),
    juge_par="Le juge administratif pour ses actes réglementaires, le Parlement pour son "
             "existence, le Conseil constitutionnel pour la répartition des compétences.",
    observation="Le Gouvernement est la seule instance qui puisse à la fois écrire le texte, "
                "choisir son calendrier, borner son contenu par l'article 40 et engager sa "
                "disparition : tous les yoyo du module partent de là.",
    fiabilite="texte",
)
INSTANCES["peuple"] = Instance(
    cle="peuple",
    nom="Corps électoral",
    niveau="Constitutionnel",
    mission="Souveraineté nationale exercée par les référendums, les élections et, depuis la "
            "révision de 2008, l'initiative partagée (art. 3 et 11).",
    fondement=("3", "6", "11", "23", "24", "25", "33"),
    composition="Environ 49 millions d'électeurs inscrits (base retenue par le module des "
                "contre-pouvoirs pour les seuils de pétition).",
    designation="Suffrage universel, égal et secret.",
    saisissable_par=("le référendum n'est jamais ouvert d'office : il faut une décision "
                     "présidentielle (art. 11) ou une révision adoptée (art. 89)",
                     "les pétitions locales dépendent d'une loi organique jamais parue (art. 72-1)"),
    effets=("conformite_obligatoire", "constat"),
    peut_bloquer=("referendum_legislatif", "referendum_local", "rip", "petition_72_1"),
    verrous=("rip_signatures_electeurs", "referendum_promulgation"),
    leviers=("reforme_ric", "convention_citoyenne", "reforme_vote_blanc"),
    pistes=("quorum_referendum", "seuil_petition_national"),
    juge_par="Le Conseil constitutionnel pour la régularité des opérations (art. 58 et 59) ; "
             "aucun juge pour le résultat, qui n'est pas un acte.",
    observation="La seule instance du registre dont aucune décision n'est attaquable au fond — "
                "et dont le silence, l'abstention, est un effet juridique plein.",
    fiabilite="texte",
)

# ── NORMALISATION : PAS UNE CLÉ INVENTÉE NE DOIT SURVIVRE ──────────────────────
# Même discipline que `constitution_analysee` : une référence de mécanisme, de verrou ou
# de levier qui ne figure pas au catalogue est retirée du champ et signalée. Une liste
# d'attracteurs n'a de valeur que si elle est adressable.

FILTRES_NORMALISATION: Dict[str, List[str]] = {}


def _normaliser() -> Dict[str, List[str]]:
    from .parametres import LEVIERS

    signales: Dict[str, List[str]] = {}
    for cle, instance in list(INSTANCES.items()):
        retraits = []
        verrous = []
        for v in instance.verrous:
            if v in VERROUS:
                verrous.append(v)
            else:
                retraits.append(f"verrou:{v}")
        bloquants = []
        for m in instance.peut_bloquer:
            if m in MECANISMES:
                bloquants.append(m)
            else:
                retraits.append(f"mecanisme:{m}")
        leviers, pistes = [], list(instance.pistes)
        for l in instance.leviers:
            if l in LEVIERS:
                leviers.append(l)
            else:
                pistes.append(l)
                retraits.append(f"levier:{l}")
        if retraits:
            signales[cle] = retraits
        INSTANCES[cle] = Instance(
            **{
                **{champ: getattr(instance, champ) for champ in instance.__dataclass_fields__},
                "verrous": tuple(verrous),
                "peut_bloquer": tuple(bloquants),
                "leviers": tuple(leviers),
                "pistes": tuple(dict.fromkeys(pistes)),
            }
        )
    return signales


# ── LES STRATÉGIES : CE QUI A DÉJÀ SERVI ────────────────────────────────────────


@dataclass(frozen=True)
class Strategie:
    """Une manœuvre décrite par sa base légale, son coût et la parade qui l'a tuée."""

    cle: str
    nom: str
    famille: str                  # faire_avancer | faire_reculer | armer | contourner | verrouiller
    acte: str
    fondement: Tuple[str, ...] = ()
    condition: str = ""
    comptage: str = ""             # le nombre qui décide : voix, jours, signatures
    verrous: Tuple[str, ...] = ()
    deja_vue: str = ""             # antécédents documentés, jamais supposés
    contree_par: Tuple[str, ...] = ()
    instance: str = ""
    fiabilite: str = "texte"
    pistes: Tuple[str, ...] = ()

    def en_dict(self) -> Dict[str, Any]:
        return {
            "cle": self.cle,
            "nom": self.nom,
            "famille": self.famille,
            "acte": self.acte,
            "fondement": list(self.fondement),
            "fondement_resolu": [
                f"Article {f}" if f in ARTICLES else f for f in self.fondement
            ],
            "condition": self.condition,
            "comptage": self.comptage,
            "deja_vue": self.deja_vue,
            "contree_par": list(self.contree_par),
            "instance": self.instance,
            "fiabilite": self.fiabilite,
            "pistes": list(self.pistes),
        }


FAMILLES_STRATEGIE: Tuple[str, ...] = (
    "faire_avancer", "faire_reculer", "armer", "contourner", "verrouiller",
)

STRATEGIES: Dict[str, Strategie] = {
    "engagement_49_3": Strategie(
        cle="engagement_49_3",
        nom="Faire adopter sans vote en engageant la responsabilité",
        famille="faire_avancer",
        acte="Le Premier ministre demande à l'Assemblée de ne pas renverser le Gouvernement, "
             "ce qui vaut adoption du texte.",
        fondement=("49",),
        condition="Un texte par déclaration, ou cinq par session ; motion de censure dans les "
                  "vingt-quatre heures, à 289 voix.",
        comptage="58 signatures pour déposer, 289 pour renverser, 24 heures pour décider.",
        deja_vue="Utilisé en janvier 2026, puis abandonné publiquement par le Gouvernement, qui "
                 "a affiché préférer négocier texte par texte.",
        contree_par=("motion_censure", "navette", "saisine_conseil"),
        instance="assemblee_nationale",
        pistes=("plafond_49_3_par_session",),
    ),
    "motion_censure": Strategie(
        cle="motion_censure",
        nom="Renverser plutôt qu'amender",
        famille="faire_reculer",
        acte="Déposer une motion motivée ; le 49.3 déposé devient alors la seule voie pour faire "
             "tomber le texte avec le Gouvernement.",
        fondement=("49", "50"),
        condition="Dixième des membres ; le vote ne peut avoir lieu que deux jours francs "
                  "après le dépôt ; trois motions par session pour un même signataire.",
        comptage="58 signatures, 289 voix.",
        deja_vue="Aucune motion adoptée sous la Ve République.",
        contree_par=("abstention_de_la_majorite", "discipline_des_groupes"),
        instance="assemblee_nationale",
    ),
    "abstention_de_la_majorite": Strategie(
        cle="abstention_de_la_majorite",
        nom="Ne pas voter pour faire échouer la censure",
        famille="verrouiller",
        acte="Comme le seuil est calculé sur les membres et non sur les votants, l'abstention "
             "compte comme un soutien.",
        fondement=("49",),
        condition="Il suffit que 289 voix ne se dégagent pas : cinq abstentions sur les bancs "
                  "de la majorité valent cinq votes favorables.",
        comptage="289 sur 577, quel que soit le nombre de votants.",
        deja_vue="Mécanique constante de tous les scrutins de censure.",
        contree_par=("vote_obligatoire_reglementaire",),
        instance="assemblee_nationale",
        pistes=("scrutin_public_obligatoire_motion",),
    ),
    "vote_bloque": Strategie(
        cle="vote_bloque",
        nom="Un seul vote, les amendements écartés",
        famille="faire_avancer",
        acte="Le Gouvernement peut accepter certains amendements et faire voter par bloc le "
             "reste du texte.",
        fondement=("44",),
        condition="Motivée ; un recours existe devant le président de l'assemblée, pas devant "
                  "le juge.",
        comptage="Zéro voix de plus, zéro jour de moins.",
        deja_vue="Pratique courante en seconde lecture et en nouvelle lecture.",
        contree_par=("saisine_conseil", "irrecevabilite_financiere"),
        instance="conference_des_presidents",
    ),
    "irrecevabilite_financiere_opposee": Strategie(
        cle="irrecevabilite_financiere_opposee",
        nom="Tuer l'amendement par l'article 40",
        famille="faire_reculer",
        acte="Opposer l'irrecevabilité à tout amendement qui diminue une ressource ou aggrave "
             "une charge ; le président de l'assemblée tranche, sans recours devant le Conseil.",
        fondement=("40", "44"),
        condition="Appréciation en séance ; le « gage » permet de contourner en compensant.",
        comptage="Aucun seuil : une formule suffit.",
        deja_vue="Utilisée contre les propositions de dépenses nouvelles, y compris d'initiative "
                 "majoritaire.",
        contree_par=("technique_du_gage", "reforme_article_40"),
        instance="assemblee_nationale",
        pistes=("critere_40_public_motive",),
    ),
    "technique_du_gage": Strategie(
        cle="technique_du_gage",
        nom="Gager pour passer l'article 40",
        famille="contourner",
        acte="Attacher une recette équivalente à toute dépense nouvelle pour échapper à "
             "l'irrecevabilité financière.",
        fondement=("40",),
        condition="Admise par la pratique des présidents ; le Conseil constitutionnel ne censure "
                  "pas le gage, il censure l'insincérité.",
        comptage="Une ligne de recette suffit, son montant n'a jamais à être réaliste.",
        deja_vue="Le procédé est vieux comme la Ve République et sert surtout à inscrire une "
                 "revendication au Journal officiel.",
        contree_par=("irrecevabilite_financiere_opposee",),
        instance="commission_des_finances",
    ),
    "motions_de_procedure": Strategie(
        cle="motions_de_procedure",
        nom="Vider la séance avant le fond",
        famille="faire_reculer",
        acte="Motion préalable, exception d'irrecevabilité, question préalable, renvoi à la "
             "commission : chacune est un vote, donc une victoire possible.",
        fondement=("42", "44"),
        condition="Priorité à la motion préalable ; vote à main levée ou ordinaire selon les "
                  "règlements.",
        comptage="Une majorité relative suffit, contrairement à la censure.",
        deja_vue="Arme classique des chambres alignées, inefficace quand la majorité est "
                 "constituée.",
        contree_par=("vote_bloque", "ordre_du_jour_gouvernemental"),
        instance="assemblee_nationale",
    ),
    "niche_parlementaire": Strategie(
        cle="niche_parlementaire",
        nom="Incrire un texte que le Gouvernement ne veut pas",
        famille="armer",
        acte="Utiliser le jour mensuel réservé à l'opposition et aux groupes minoritaires, et la "
             "semaine de contrôle.",
        fondement=("48", "51-1", "29"),
        condition="Ordre du jour arrêté par la Conférence des présidents : le tirage au sort des "
                  "textes, dans certains règlements, décide du sujet.",
        comptage="Un jour par mois, une semaine sur quatre.",
        deja_vue="Les niches ont produit des lois entières — et des blocages, faute de "
                 "majorité de séance.",
        contree_par=("conference_des_presidents",),
        instance="conference_des_presidents",
        pistes=("ordre_du_jour_alternatif_reglementaire",),
    ),
    "resolution_enquete": Strategie(
        cle="resolution_enquete",
        nom="Une commission d'enquête par groupe et par session",
        famille="armer",
        acte="Résolution de groupe ; pouvoirs d'investigation, serment, publication du rapport.",
        fondement=("51-1", "51-2"),
        condition="Une par groupe par session ; le Gouvernement peut s'opposer pour saisine "
                  "parallèle du juge.",
        comptage="Aucun seuil de signatures au-delà du groupe constitué (15 députés, 10 sénateurs).",
        deja_vue="Droit ouvert par la révision de 2009 ; son usage s'est banalisé.",
        contree_par=("avis_favorable_du_gouvernement", "secret_de_l_enquete_judiciaire"),
        instance="office_et_missions_parlementaires",
        verrous=("commission_enquete_signature",),
    ),
    "saisine_conseil": Strategie(
        cle="saisine_conseil",
        nom="Soixante signatures pour suspendre la promulgation",
        famille="armer",
        acte="Saisir le Conseil constitutionnel : le délai de promulgation est suspendu, le texte "
             "ne peut être modifié que par une nouvelle loi.",
        fondement=("61", "10"),
        condition="Soixante députés ou soixante sénateurs ; un mois, huit jours en urgence.",
        comptage="60 voix, 30 jours — le meilleur rapport prix/résultat du droit parlementaire.",
        deja_vue="Utilisée à chaque majorité incertaine depuis 1974 ; la saisine systématique "
                 "des lois de finances est, elle, obligatoire.",
        contree_par=("reforme_du_conseil", "depeche_au_conseil"),
        instance="conseil_constitutionnel",
        verrous=("saisine_conseil_signatures", "saisine_conseil_delai"),
    ),
    "defossilisation": Strategie(
        cle="defossilisation",
        nom="Nettoyer la loi par décret",
        famille="contourner",
        acte="Demander au Conseil constitutionnel de constater le caractère réglementaire d'une "
             "disposition, puis la modifier par décret en Conseil d'État après avis motivé.",
        fondement=("37", "41"),
        condition="Huit jours de délai pour le Conseil ; avis du Conseil d'État obligatoire.",
        comptage="Zéro voix : une demande du Gouvernement.",
        deja_vue="Pratique installée, devenue un outil de simplification annuel.",
        contree_par=("refus_de_declasser", "principe_de_suprematie_de_la_loi"),
        instance="conseil_constitutionnel",
    ),
    "rectification_de_calendrier": Strategie(
        cle="rectification_de_calendrier",
        nom="Redemander une lecture pour reprendre la main",
        famille="faire_avancer",
        acte="Déclarer l'urgence, demander une nouvelle délibération, ou reprendre le texte de la "
             "CMP plutôt que le sien.",
        fondement=("45", "10"),
        condition="La nouvelle délibération présidentielle n'est soumise à aucune condition de "
                  "fond ; elle ne peut être refusée par le Parlement, qui re-vote.",
        comptage="Quinze jours de promulgation suspendue.",
        deja_vue="La demande de nouvelle délibération n'a presque jamais servi : c'est un pouvoir "
                 "dont l'existence suffit.",
        contree_par=("motion_preableble", "navette"),
        instance="president_de_la_republique",
    ),
    "referendum_par_11": Strategie(
        cle="referendum_par_11",
        nom="Court-circuiter le Sénat et le Conseil",
        famille="contourner",
        acte="Adopter une réforme institutionnelle par l'article 11 plutôt que par l'article 89 : "
             "pas de veto du Sénat, pas de contrôle de constitutionnalité.",
        fondement=("11", "89", "61"),
        condition="Objet limité par le texte ; délibération des deux assemblées en termes "
                  "identiques requise pour la promulgation directe.",
        comptage="Aucun seuil de participation.",
        deja_vue="1962 (élection du Président), 1969 (Sénat et régionalisation — rejetée, "
                 "démission qui a suivi : enchaînement à vérifier).",
        contree_par=("motion_censure", "refus_du_senat"),
        instance="president_de_la_republique",
        fiabilite="pratique",
    ),
    "procedure_acceleree": Strategie(
        cle="procedure_acceleree",
        nom="Supprimer une navette",
        famille="faire_avancer",
        acte="Déclarer la procédure accélérée : une lecture par assemblée au lieu de deux.",
        fondement=("45", "42"),
        condition="Ouverte au Gouvernement, possible pour les propositions ; ses effets sont "
                  "contenus si le désaccord persiste (CMP).",
        comptage="Deux mois gagnés sur six.",
        deja_vue="Plus de 80 % des textes adoptés.",
        contree_par=("demande_de_deuxieme_lecture_par_l_un_des_deux_assemblages",),
        instance="assemblee_nationale",
    ),
    "refere_liberte": Strategie(
        cle="refere_liberte",
        nom="Quarante-huit heures contre une décision exécutive",
        famille="armer",
        acte="Saisir le juge administratif en référé-liberté contre un acte portant une atteinte "
             "grave et manifestement illégale à une liberté fondamentale.",
        fondement=("32", "66", "72", "34"),
        condition="Urgence et atteinte à une liberté ; aucun filtre, aucun mémoire préalable.",
        comptage="Deux jours, contre des mois pour un recours au fond.",
        deja_vue="Arme des associations et des élus locaux ; la jurisprudence sur les "
                 "conditions d'accueil et la police administrative est abondante.",
        contree_par=("decret_en_conseil_des_ministres", "loi_formelle"),
        instance="juridictions_administratives",
        fiabilite="pratique",
    ),
}


# ── LES FENTES : CE QUE NUL N'ÉCRIT, CE QUE TOUT AUTORISE ───────────────────────


@dataclass(frozen=True)
class Fente:
    """Une conséquence non écrite, tenue par la seule combinaison de textes écrits.

    Trois champs la distinguent d'une invention : `premisses` (toutes résolubles dans le
    droit du dépôt), `raison_du_silence` (pourquoi ce n'est pas écrit) et
    `verrou_de_retour` (l'étage de texte nécessaire pour la défaire, donc l'étage par
    lequel elle est attaquable).
    """

    cle: str
    nom: str
    type: str                      # fente | porte | droit_sans_juge
    sens: str                      # a_qui_sert_le_trou
    deduction: str
    premisses: Tuple[str, ...]
    articles: Tuple[str, ...] = ()
    raison_du_silence: str = ""
    ce_que_ca_change: str = ""
    etage: str = "loi ordinaire"
    condition_de_verrouillage: str = ""
    point_de_vigilance: str = ""
    computation: str = ""          # nom de la fonction qui recalcule l'effet chiffré
    fiabilite: str = "deduite"     # deduite | a_verifier | ecrite_sous_usee
    instances: Tuple[str, ...] = ()
    pistes: Tuple[str, ...] = ()

    def en_dict(self) -> Dict[str, Any]:
        return {
            "cle": self.cle,
            "nom": self.nom,
            "type": self.type,
            "sens": self.sens,
            "deduction": self.deduction,
            "premisses": [{"pre": p, "resolu": _resoudre(p)} for p in self.premisses],
            "articles": list(self.articles),
            "raison_du_silence": self.raison_du_silence,
            "ce_que_ca_change": self.ce_que_ca_change,
            "etage_de_verrouillage": self.etage,
            "condition_de_verrouillage": self.condition_de_verrouillage,
            "point_de_vigilance": self.point_de_vigilance,
            "effet_chiffre": effets_de_fente(self.cle),
            "robustesse": robustesse(self),
            "fiabilite": self.fiabilite,
            "instances": list(self.instances),
            "pistes": list(self.pistes),
            "observe_le": DATE_OBSERVATION,
        }


def _resoudre(premisse: str) -> Dict[str, Any]:
    """Vérifie une prémisses : « art:89 », « reg:LOI_ORG_2009_403 », « verrou:x »,
    « mecanisme:x », « instance:x », « jurisprudence:x » (non vérifiable ici)."""
    genre, _, valeur = (premisse or "").partition(":")
    sortie = {"genre": genre, "valeur": valeur, "resolu": False, "libelle": "", "verifiable": True}
    if genre == "art":
        fiche = article(valeur)
        sortie["resolu"] = fiche is not None
        sortie["libelle"] = f"Article {valeur} — {fiche.titre}" if fiche else ""
    elif genre == "reg":
        entree = REGISTRE_LEGAL.get(valeur)
        sortie["resolu"] = entree is not None
        sortie["libelle"] = f"{valeur} — {entree.titre}" if entree else ""
    elif genre == "verrou":
        verrou = VERROUS.get(valeur)
        sortie["resolu"] = verrou is not None
        sortie["libelle"] = verrou.nom if verrou else ""
    elif genre == "mecanisme":
        mecanisme = MECANISMES.get(valeur)
        sortie["resolu"] = mecanisme is not None
        sortie["libelle"] = mecanisme.nom if mecanisme else ""
    elif genre == "instance":
        instance = INSTANCES.get(valeur)
        sortie["resolu"] = instance is not None
        sortie["libelle"] = instance.nom if instance else ""
    elif genre == "jurisprudence":
        # Assumé : une décision de juge n'est pas dans le dépôt, elle est citée datée.
        sortie["resolu"] = True
        sortie["verifiable"] = False
        sortie["libelle"] = f"décision citée : {valeur}"
    return sortie


FENTES: Dict[str, Fente] = {
    "congres_par_exprimes": Fente(
        cle="congres_par_exprimes",
        nom="Le Congrès se calcule sur les votants, pas sur les sièges",
        type="fente",
        sens="à qui peut réunir une majorité absolue sans l'avoir",
        deduction="L'article 89 exige « la majorité des trois cinquièmes des suffrages "
                  "exprimés ». Le dénominateur n'est donc pas le nombre de parlementaires "
                  "mais celui de ceux qui votent : chaque abstention, chaque bulletin blanc, "
                  "chaque non-volant abaisse le nombre de voix requises. À 300 votants, 180 "
                  "voix suffisent au lieu de 555.",
        premisses=("art:89", "verrou:congres_revision", "art:27"),
        articles=("89",),
        raison_du_silence="Parce que le constituant de 1969 a repris la formule de 1958 sans "
                          "corriger l'assiette, et que personne n'a eu intérêt à fermer la "
                          "porte : le seuil bas arrange celui qui gouverne comme celui qui "
                          "menace de ne pas voter.",
        ce_que_ca_change="Une révision peut être adoptée par une minorité de l'assemblée "
                         "réunie, sans qu'aucune règle n'ait été enfreinte.",
        etage="constitutionnel",
        condition_de_verrouillage="Verrouillée dès l'adoption : la révision promulguée ne "
                                  "s'attaque plus, il en faut une autre. Pour fermer la fente, "
                                  "il faudrait une révision… de l'article 89.",
        point_de_vigilance="Rien à contrôler pour le Conseil d'État : le Congrès n'est pas une "
                           "autorité administrative, et les opérations de vote relèvent de "
                           "l'organisation interne. Le seul garde-fou est la publicité du "
                           "scrutin — les votes sont publics, ce qui rend la manœuvre coûteuse "
                           "en noms, pas en voix.",
        computation="abstention_congres",
        fiabilite="deduite",
        instances=("congres", "senat", "assemblee_nationale"),
        pistes=("seuil_congres_sur_membres", "quorum_congres"),
    ),
    "censure_par_membres": Fente(
        cle="censure_par_membres",
        nom="L'abstention est un vote de confiance",
        type="fente",
        sens="au Gouvernement",
        deduction="L'article 49 exige « la majorité des membres composant l'Assemblée "
                  "nationale » : l'assiette est l'effectif légal, 577, jamais le nombre de "
                  "votants. Une majorité qui s'abstient, qui ne vient pas, ou qui ne vote que "
                  "des bulletins blancs protège le Gouvernement. Les trois sièges vacants au "
                  "12 octobre 2026 jouent dans le même sens : ils rendent la censure plus "
                  "difficile, jamais plus facile.",
        premisses=("art:49", "verrou:censure_voix", "art:27"),
        articles=("49", "27"),
        raison_du_silence="La formule « membres composant » est un vestige de 1958, votée pour "
                          "rendre la censure difficile ; personne n'a voulu la « corriger » en "
                          "sens inverse depuis, parce qu'elle protège tous les gouvernements, y "
                          "composés futurs.",
        ce_que_ca_change="Le calcul d'une majorité de gouvernement ne se fait pas sur les voix "
                         "favorables mais sur les voix opposées : une majorité de 289 est une "
                         "majorité d'absence organisée.",
        etage="constitutionnel",
        condition_de_verrouillage="Elle tient tant que l'article 49 n'est pas révisé : "
                                  "aucune loi ordinaire, aucun règlement ne peut changer "
                                  "l'assiette.",
        point_de_vigilance="Aucun recours : un scrutin de censure est un acte parlementaire, "
                           "jamais un acte administratif. Le Conseil constitutionnel lui-même "
                           "ne juge pas le vote, seulement le règlement qui l'organise.",
        computation="censure_sur_effectif",
        fiabilite="deduite",
        instances=("assemblee_nationale",),
        pistes=("vote_obligatoire_motion", "compte_rendu_nominal_seance"),
    ),
    "referendum_sans_juge": Fente(
        cle="referendum_sans_juge",
        nom="Entre l'adoption populaire et la promulgation, il n'y a personne",
        type="fente",
        sens="à l'exécutif qui veut imposer une réforme institutionnelle",
        deduction="Le Conseil constitutionnel ne peut être saisi des lois qu'« avant leur "
                  "promulgation » (61 al. 1), et il s'est déclaré incompétent sur la loi votée "
                  "directement par le peuple (décision du 6 novembre 1962). L'article 11 permet "
                  "de réformer l'organisation des pouvoirs publics par voie référendaire. Ces "
                  "trois textes, lus ensemble, produisent une réforme constitutionnelle qui "
                  "n'est, à aucun moment, soumise à un juge constitutionnel — et la révision de "
                  "2008 a expressément écarté l'idée de combler ce vide.",
        premisses=("art:11", "art:61", "art:89", "art:10",
                    "jurisprudence:Conseil constitutionnel, 6 novembre 1962"),
        articles=("11", "61", "89", "10"),
        raison_du_silence="Ce n'est pas un oubli, c'est un arbitrage : reconnaître une "
                          "compétence du Conseil sur le suffrage direct, ce serait mettre le "
                          "peuple au-dessus du juge et le juge au-dessus du peuple à la fois.",
        ce_que_ca_change="Une voie d'en haut, plus rapide que l'article 89 (pas de 3/5, pas de "
                         "veto du Sénat) et juridiquement blindée après coup.",
        etage="conventionnel ou droit dérivé de l'UE",
        condition_de_verrouillage="Rien de verrouillé vers le bas, et rien non plus vers le "
                                  "haut : seule une autre loi référendaire, ou un engagement "
                                  "international, peut contredire la réforme — la CEDH ou la "
                                  "CJUE restant, par les actes d'application, la seule porte.",
        point_de_vigilance="Le point faible n'est pas la loi référendaire mais ses décrets "
                           "d'application : le Conseil d'État, lui, est pleinement compétent "
                           "pour annuler un décret contraire aux lois et principes "
                           "constitutionnels — y compris ceux qu'une loi référendaire n'a pas "
                           "expressément prévus.",
        fiabilite="deduite",
        instances=("conseil_constitutionnel", "president_de_la_republique", "conseil_etat"),
        pistes=("controle_juridictionnel_loi_referendaire",),
    ),
    "defossilisation_sans_vote": Fente(
        cle="defossilisation_sans_vote",
        nom="Réécrire la loi par décret, avec l'accord forcé du législateur",
        type="fente",
        sens="au Gouvernement",
        deduction="L'article 37 alinéa 2 permet au Gouvernement de faire constater qu'une "
                  "disposition législative est réglementaire, puis de la modifier par décret en "
                  "Conseil d'État après avis. L'article 41 impose au président de l'assemblée de "
                  "saisir le Conseil constitutionnel en cas de désaccord, dans les huit jours. "
                  "Résultat : une règle votée par le Parlement peut être réécrite sans vote, "
                  "et le seul arbitre est une instance saisie par celui qui veut changer la "
                  "règle.",
        premisses=("art:37", "art:41", "art:34", "art:13", "verrou:irrecevabilite_competence_delai"),
        articles=("37", "41", "34", "13"),
        raison_du_silence="Parce que la frontière des compétences est un équilibre négocié en "
                          "1958 et que personne n'a intérêt à la rendre mécanique dans l'autre "
                          "sens : le Parlement garde le dernier mot s'il vote une loi qui "
                          "confirme la règle, et il ne le fait presque jamais.",
        ce_que_ca_change="Un gouvernement peut simplifier, actualiser ou vider de son sens un "
                         "dispositif législatif au rythme des décrets, sans jamais engager sa "
                         "responsabilité.",
        etage="réglementaire",
        condition_de_verrouillage="Verrou de retour très bas : la fente est attaquable par le "
                                  "juge administratif, qui annule le décret s'il méconnaît un "
                                  "principe ou une compétence. Une fois le déclassement acquis, "
                                  "en revanche, la règle tombe d'un décret suivant — ce qui la "
                                  "rend puissante et fragile à la fois.",
        point_de_vigilance="Le Conseil d'État contrôle : la consultation de la commission "
                           "compétente, l'avis motivé, l'absence de portée normative nouvelle, "
                           "et le respect des compétences que l'article 34 réserve au "
                           "législateur. Un déclassement qui réforme au fond est annulé.",
        fiabilite="deduite",
        instances=("conseil_etat", "conseil_constitutionnel"),
        pistes=("encadrement_des_declassements", "bilan_public_des_defossilisations"),
    ),
    "irrecevabilite_sans_recours": Fente(
        cle="irrecevabilite_sans_recours",
        nom="Le recours contre une irrecevabilité n'est ouvert qu'à celui qui ne le veut pas",
        type="droit_sans_juge",
        sens="à la majorité de séance",
        deduction="L'article 44 alinéa 4 ouvre un recours contre l'irrecevabilité opposée par le "
                  "président de l'assemblée, mais ce recours appartient au président de "
                  "l'assemblée : si celui-ci ne saisit pas le Conseil constitutionnel, aucun "
                  "groupe, aucun député, aucun juge ne peut le faire. Le contre-pouvoir est "
                  "donc confié à l'autorité dont on conteste l'arbitrage.",
        premisses=("art:44", "art:61", "art:40"),
        articles=("44", "40", "61"),
        raison_du_silence="Le constituant de 2008 a voulu protéger le président de séance, "
                          "considéré comme impartial ; la critique est que l'impartialité d'un "
                          "homme politique est une convention, pas une garantie.",
        ce_que_ca_change="Une majorité peut écarter un amendement en le déclarant irrecevable, "
                         "sans risque de censure : la seule sanction est politique, immédiate, "
                         "et ne se prouve pas.",
        etage="constitutionnel",
        condition_de_verrouillage="Ne se referme que par une révision, ou par une modification "
                                  "du règlement — laquelle, elle, est obligatoirement soumise au "
                                  "Conseil constitutionnel (61 al. 1). C'est la seule brèche : "
                                  "ouvrir le recours à soixante membres ferme la fente sans "
                                  "toucher à la Constitution.",
        point_de_vigilance="Le juge administratif n'est pas saisi des actes d'une assemblée ; le "
                           "Conseil constitutionnel n'est saisi que du règlement. Toute demande "
                           "dirigée contre un acte de séance est irrecevable — c'est même le "
                           "fondement de la fente.",
        fiabilite="deduite",
        instances=("conseil_constitutionnel", "assemblee_nationale", "senat"),
        pistes=("recours_collectif_irrecevabilite", "motivation_obligatoire_44"),
    ),
    "amendement_etrang": Fente(
        cle="amendement_etrang",
        nom="Le cavalier est irrecevable, et c'est tout",
        type="fente",
        sens="à qui veut faire voter un amendement sans débat propre",
        deduction="L'article 45 alinéa 3 interdit les amendements « sans lien, même indirect, "
                  "avec le texte en discussion » ; l'irrecevabilité est prononcée en séance par "
                  "le président de l'assemblée, et la décision ne peut être contestée que par le "
                  "recours du quatrième alinéa de l'article 44. Autrement dit : l'interdiction "
                  "existe, la sanction n'existe pas pour l'amendement irrégulier, seulement pour "
                  "l'irrecevabilité.",
        premisses=("art:45", "art:44", "art:40"),
        articles=("45", "44", "40"),
        raison_du_silence="Parce que le Conseil constitutionnel censure les cavaliers *législatifs* "
                          "sur saisine, mais que la censure ne fait pas disparaître le vote "
                          "politique qui l'a permis : la sanction intervient après.",
        ce_que_ca_change="Glisser une disposition dans un texte populaire ou technique reste la "
                         "seule façon de faire adopter une réforme qui n'aurait pas eu "
                         "d'ordre du jour. Et si le Conseil censure, le texte principal survit.",
        etage="loi ordinaire",
        condition_de_verrouillage="Le verrou est celui de la saisine : sans soixante "
                                  "signatures, un cavalier entre en vigueur. C'est un trou qui ne "
                                  "se referme que par le droit de saisine automatique — "
                                  "c'est-à-dire en rendant le Conseil constitutionnel juge de la "
                                  "navigation, ce qu'aucun gouvernement n'a voulu.",
        point_de_vigilance="Sur un cavalier devenu loi, la QPC reste ouverte contre ses "
                            "dispositions détachables ; le Conseil d'État, lui, ne censure pas la "
                            "loi, mais peut refuser d'appliquer un décret dont la base est "
                            "censurée.",
        computation="",
        fiabilite="deduite",
        instances=("conseil_constitutionnel", "assemblee_nationale"),
        pistes=("saisine_automatique_cavaliers",),
    ),
    "toucher_la_loi_par_le_decret": Fente(
        cle="toucher_la_loi_par_le_decret",
        nom="Contourner l'article 61-1 en attaquant l'acte d'application",
        type="fente",
        sens="aux requérants",
        deduction="La QPC ne porte que sur les « dispositions législatives » (61-1) : une loi "
                  "promulguée ne peut plus être censurée qu'à travers elle. Mais l'illégalité "
                  "d'une loi se juge par ricochet : tout acte réglementaire doit respecter la "
                  "loi et les principes généraux, et le juge administratif annule un décret "
                  "dont la base est entachée. Le chemin le plus court pour faire tomber une "
                  "règle législative est donc de ne pas l'attaquer.",
        premisses=("art:61-1", "art:34", "art:37", "art:13", "instance:conseil_etat"),
        articles=("61-1", "34", "37", "13"),
        raison_du_silence="Parce que le contentieux de la légalité est un héritage du Conseil "
                          "d'État, antérieur à la QPC, et que le constituant de 2008 n'a pas "
                          "articulé les deux voies — expression du « ne rien écrire qui "
                          "n'oblige personne ».",
        ce_que_ca_change="Une loi votée il y a trente ans, jamais déférée, peut être neutralisée "
                         "par ses décrets : le verrou n'est pas dans le texte mais dans son "
                         "application.",
        etage="réglementaire",
        condition_de_verrouillage="Se déverrouille dans l'autre sens : écrire la règle "
                                   "exactement dans la loi, sans renvoyer au décret, supprime la "
                                   "prise. À l'inverse, laisser un décret fixer l'essentiel, c'est "
                                   "offrir la porte.",
        point_de_vigilance="Le Conseil d'État annule pour illégalité de l'acte, pas pour "
                           "constitutionalité de la loi : la décision ne vaut que pour le décret "
                           "attaqué. C'est la limite stratégique de la manœuvre.",
        fiabilite="deduite",
        instances=("conseil_etat", "juridictions_administratives", "conseil_constitutionnel"),
        pistes=("exception_d_illegalite_systematique",),
    ),
    "priorite_du_droit_derive": Fente(
        cle="priorite_du_droit_derive",
        nom="Faire écarter une loi par un juge ordinaire, sans le Conseil",
        type="fente",
        sens="aux requérants",
        deduction="L'article 55 donne aux traités « une autorité supérieure à celle des lois » ; "
                  "l'article 88-1 inscrit le droit de l'Union dans l'ordre interne. Il en résulte "
                  "que tout juge — judiciaire ou administratif — peut écarter une loi contraire à "
                  "une norme internationale directement effective, sans passer par le Conseil "
                  "constitutionnel, dont la compétence sur la loi promulguée se limite à la QPC. "
                  "Aucune disposition ne l'écrit, et la pratique constitutionnelle française le "
                  "reconnaît depuis la fin des années 1980.",
        premisses=("art:55", "art:88-1", "art:61-1", "art:61", "instance:cjue"),
        articles=("55", "88-1", "61-1", "61"),
        raison_du_silence="Parce que l'articulation a été faite par les juges, pas par le "
                          "constituant : le résultat est une règle de compétence non écrite, "
                          "dont la hiérarchie exacte avec la QPC dépend de la jurisprudence, "
                          "donc change.",
        ce_que_ca_change="Le Parlement peut être contourné sans être révisé : la norme "
                         "contraire est écartée, la loi survit formellement, et le gouvernement "
                         "n'a plus qu'à aligner le règlement.",
        etage="conventionnel ou droit dérivé de l'UE",
        condition_de_verrouillage="Une telle priorité ne se verrouille que par la dénonciation "
                                  "du traité ou le retrait — c'est-à-dire à un étage politique, "
                                  "pas juridique. C'est ce qui la rend robuste et ce qui la rend "
                                  "non démocratique, selon le côté d'où on la regarde.",
        point_de_vigilance="Le juge national ne peut ni abroger ni condamner : il écarte. Une "
                           "loi contraire mais non directement effective reste appliquée "
                           "jusqu'à ce que le législateur la reprenne — le Conseil d'État, "
                           "lui, enjoint de modifier le règlement contraire.",
        fiabilite="deduite",
        instances=("cjue", "conseil_etat", "cour_de_cassation", "commission_europeenne"),
        pistes=("cellule_gouvernementale_conformite_ue",),
    ),
    "petition_dans_le_reglement": Fente(
        cle="petition_dans_le_reglement",
        nom="Le seuil de pétition locale, personne ne l'a fixé : l'assemblée le fixera",
        type="fente",
        sens="aux minorités locales",
        deduction="L'article 72-1 ouvre la consultation locale et la pétition tendant à inscrire "
                  "une question à l'ordre du jour « dans les conditions fixées par la loi "
                  "organique ». Cette loi organique n'a jamais été prise. Comme le règlement de "
                  "l'assemblée délibérante régit déjà ce qui n'est pas réservé à la loi, un "
                  "conseil municipal peut inscrire son propre seuil dans son règlement ; et "
                  "comme le règlement communal n'est pas soumis au Conseil constitutionnel, la "
                  "seule contestation vient du juge administratif, sur la légalité de l'acte — "
                  "pas sur son opportunité.",
        premisses=("art:72-1", "reg:CGCT_L2121_1", "verrou:petition_locale", "art:34"),
        articles=("72-1", "34", "72"),
        raison_du_silence="Parce que le constituant de 2003 a renvoyé à une loi organique qui "
                          "n'est jamais venue : le vide n'est pas une faute, c'est une "
                          "compétence laissée là, et celui qui la prend ne viole rien.",
        ce_que_ca_change="Une minorité municipale peut se donner à elle-même un droit "
                         "d'inscription que la République n'a jamais osé organiser : c'est "
                         "exactement le RIC local, construit par en bas et sans révision.",
        etage="réglementaire",
        condition_de_verrouillage="Le verrou est double et fragile : la loi organique future "
                                  "peut écraser le seuil local, mais elle ne pourra pas "
                                  "rétroactivement annuler les pétitions déjà déposées sous le "
                                  "règlement — et le Conseil d'État censurera une rétroactivité "
                                  "qui porterait atteinte aux situations constituées.",
        point_de_vigilance="Le préfet défère le règlement ; le juge contrôle la proportion du "
                           "seuil et la liberté de délibérer. Une pétition à un seuil trop bas "
                           "(par exemple 1 % des inscrits) a été censurée dans le contentieux "
                           "administratif ? — à vérifier avant publication ; le principe du "
                           "contrôle, lui, est constant.",
        fiabilite="a_verifier",
        instances=("collectivites_outre_mer", "prefet", "juridictions_administratives"),
        pistes=("loi_organique_72_1", "seuil_petition_national_par_defaut"),
    ),
    "absence_de_quorum": Fente(
        cle="absence_de_quorum",
        nom="Ni quorum, ni seuil de participation : le silence est la règle",
        type="fente",
        sens="à qui gagne sans mobiliser",
        deduction="La Constitution n'exige aucun seuil de participation pour le référendum de "
                  "l'article 11 comme pour celui de l'article 89, et n'oblige aucune assemblée à "
                  "un quorum pour réviser — l'article 89 se borne à exiger les trois cinquièmes "
                  "des suffrages exprimés au Congrès. Le silence est total, donc le vide "
                  "constitue la règle : une réforme institutionnelle peut être adoptée par une "
                  "fraction du corps électoral et une fraction des parlementaires, sans "
                  "qu'aucun texte ne puisse être invoqué contre elle.",
        premisses=("art:11", "art:89", "art:3", "verrou:congres_revision"),
        articles=("11", "89", "3"),
        raison_du_silence="Le quorum a été refusé en 1958 comme en 2008, parce qu'il transforme "
                          "l'abstention en arme : le silence protège le pouvoir établi autant "
                          "que le réformateur.",
        ce_que_ca_change="Les deux fentes précédentes — Congrès sur exprimés, référendum sans "
                         "seuil — se renforcent : le même vide, aux deux niveaux, produit la "
                         "même possibilité.",
        etage="constitutionnel",
        condition_de_verrouillage="Une règle de quorum ne peut être que constitutionnelle ou "
                                  "organique ; inscrite dans un règlement, elle serait "
                                  "abrogeable par le suivant, ce qui ne verrouille rien.",
        point_de_vigilance="Le Conseil constitutionnel veille, sur les lois organiques et les "
                           "règlements, à ce qu'un quorum ajouté ne paralyse pas "
                           "l'institution ; il ne peut rien contre l'absence de quorum, qui "
                           "n'est une atteinte à rien d'écrit.",
        computation="quorum_absent",
        fiabilite="deduite",
        instances=("congres", "peuple", "conseil_constitutionnel"),
        pistes=("quorum_referendum", "quorum_congres"),
    ),
    "outre_mer_comme_laboratoire": Fente(
        cle="outre_mer_comme_laboratoire",
        nom="Le droit peut être différent quelque part, sans révision",
        type="porte",
        sens="aux réformateurs qui n'ont pas la majorité nationale",
        deduction="Les articles 72-3 à 74 permettent l'adaptation, l'habilitation et, dans "
                  "certains cas, la fixation locale des règles ; l'article 73 autorise des "
                  "mesures spécifiques sans toucher au texte national. Le croisement est "
                  "immédiat : une réforme impossible en métropole peut être écrite pour une "
                  "collectivité, y devenir une pratique, puis être généralisée par la voie "
                  "ordinaire — sans jamais avoir exigé une majorité qualifiée nationale.",
        premisses=("art:73", "art:74", "art:72", "art:34", "art:72-3"),
        articles=("72-3", "73", "74", "34"),
        raison_du_silence="Parce que l'outre-mer est traité comme un contentieux et non comme "
                          "une méthode : le constituant de 2003 a ouvert la porte du "
                          "différencié, le débat politique n'y a jamais vu un laboratoire.",
        ce_que_ca_change="Il devient possible de tester institutionnellement une réforme "
                         "complexe à coût politique limité, avec un retour d'expérience "
                         "législatif écrit.",
        etage="loi organique",
        condition_de_verrouillage="Une habilitation locale se reprend par la même loi ; le "
                                  "verrouillage vient de la durée : une pratique installée et "
                                  "contrôlée par la Cour des comptes locale crée des droits qui "
                                  "ne s'éteignent pas par abrogation sèche.",
        point_de_vigilance="Le Conseil constitutionnel contrôle le respect des compétences et "
                           "l'existence de l'intérêt local ; le Conseil d'État, les actes "
                           "d'application. Rien ne contrôle l'opportunité du test — c'est le "
                           "cœur de la porte.",
        fiabilite="ecrite_sous_usee",
        instances=("collectivites_outre_mer", "conseil_constitutionnel", "cour_des_comptes"),
        pistes=("conference_permanente_outre_mer", "clause_de_revoyure_territoriale"),
    ),
    "nouvelle_deliberation_presidentielle": Fente(
        cle="nouvelle_deliberation_presidentielle",
        nom="Le Président peut renvoyer la loi au Parlement, sans motif",
        type="porte",
        sens="au chef de l'État qui veut gagner un cycle",
        deduction="L'article 10 permet au Président, avant l'expiration du délai de "
                  "promulgation, de demander au Parlement une nouvelle délibération de la loi ou "
                  "de certains articles ; cette demande ne peut être refusée. Elle n'exige "
                  "aucune motivation, ne déclenche aucun contrôle, et suspend de fait la mise en "
                  "vigueur — le temps de la renégociation.",
        premisses=("art:10", "art:45", "verrou:promulgation_nouvelle_deliberation"),
        articles=("10", "45"),
        raison_du_silence="Peu usitée parce qu'elle place le Président dans le débat "
                          "parlementaire, ce que la Ve République a voulu éviter : le pouvoir "
                          "est là, inutilisé, et donc gratuit pour qui l'ose.",
        ce_que_ca_change="Un cycle complet de navette peut être relancé sans que personne n'ait "
                         "à justifier — et sans saisir le Sénat d'un veto, ce qui peut suffire à "
                         "faire basculer une majorité de séance.",
        etage="constitutionnel",
        condition_de_verrouillage="Le verrou est la nouvelle délibération elle-même : le "
                                  "Parlement peut voter de nouveau à l'identique, et alors la "
                                  "promulgation devient obligatoire.",
        point_de_vigilance="Aucun recours contre la demande de nouvelle délibération : ce n'est "
                           "pas un acte administratif, et le Conseil constitutionnel ne juge pas "
                           "l'usage de l'article 10. En revanche, la loi issue de la nouvelle "
                           "délibération peut être saisie à nouveau.",
        fiabilite="ecrite_sous_usee",
        instances=("president_de_la_republique", "assemblee_nationale", "senat"),
        pistes=("motivation_demandee_nouvelle_deliberation",),
    ),
}


def arithmetique_abstention_congres(votants: int) -> Dict[str, Any]:
    """Combine l'article 89 et l'arithmétique des contre-pouvoirs pour montrer l'effet."""
    from .gouvernance_contrepouvoir import seuil as seuil_chiffre

    base = int(votants)
    requis = seuil_chiffre("congres_revision", {"suffrages_exprimes_congres": base})
    return {
        "suffrages_exprimes": base,
        "voix_requises": requis,
        "theoriques": 925,
        "economie_de_voix": max(0, seuil_chiffre("congres_revision") - requis),
        "formule": "trois cinquièmes des suffrages exprimés",
        "lecture": (
            f"{requis} voix suffisent quand {base} parlementaires votent, alors que le Congrès "
            f"au complet en exige {seuil_chiffre('congres_revision')} sur 925 sièges."
        ),
    }


def effets_de_fente(cle: str) -> Dict[str, Any]:
    """Les fentes qui se chiffrent se chiffrent ; les autres n'inventent rien."""
    if cle == "congres_par_exprimes":
        return {
            "type": "abstention_congres",
            "calcul": [arithmetique_abstention_congres(n) for n in (925, 700, 500, 300)],
        }
    if cle == "censure_par_membres":
        from .gouvernance_contrepouvoir import seuil as seuil_chiffre

        return {
            "type": "censure_sur_effectif",
            "assiette": "membres composant l'Assemblée (effectif légal)",
            "voix_requises": seuil_chiffre("censure_voix"),
            "avec_effectif_reel": seuil_chiffre(
                "censure_voix", {"membres_assemblee_nationale": 574}
            ),
            "lecture": "l'abstention ne fait pas baisser le seuil : elle le rend plus dur à "
                       "atteindre, ce qui est exactement l'inverse du Congrès.",
        }
    if cle == "absence_de_quorum":
        return {
            "type": "quorum_absent",
            "quorum_referendum": None,
            "quorum_congres": None,
            "note": "aucun chiffre : c'est l'absence de règle qui produit l'effet",
        }
    return {"type": "non_chiffree", "note": "aucune arithmétique disponible pour cette fente"}


# ── FONCTIONS PARTAGÉES ─────────────────────────────────────────────────────────

#: Barème de robustesse. Il est volontairement brutal : il ne note pas la valeur
#: politique d'une fente, il note la solidité de ce qui la rend défendable.
POIDS_ROBUSTESSE: Dict[str, int] = {
    "base_ecrite": 30,
    "clarte_de_competence": 20,
    "procedure_ancre": 20,
    "hauteur_d_etage": 20,
    "resistance_a_l_abrogation": 10,
}

ARTICLES_DE_COMPETENCE = ("34", "37", "39", "44", "45", "47", "48", "61", "89")


def robustesse(fente: Fente) -> Dict[str, Any]:
    """Score de défendabilité d'une fente, barème公开 et recalculable.

    Rien ici ne dit qu'une fente est « irréfutable ». Le barème mesure quatre choses que
    le Conseil d'État et le Conseil constitutionnel vérifient vraiment : la base écrite,
    la clarté de la compétence invoquée, l'ancrage de la procédure, et la hauteur de
    l'étage où la fente se loge. La cinquième ligne note la difficulté à la défaire.
    """
    premisses = [_resoudre(p) for p in fente.premisses]
    ecrites = [p for p in premisses if p["resolu"] and p["verifiable"]]
    total_premisses = max(1, len(premisses))
    base_ecrite = round(POIDS_ROBUSTESSE["base_ecrite"] * len(ecrites) / total_premisses)

    numeros = {p["valeur"] for p in premisses if p["genre"] == "art"}
    clarte = POIDS_ROBUSTESSE["clarte_de_competence"] if numeros & set(ARTICLES_DE_COMPETENCE) else 10

    annees_procedure = [p for p in premisses if p["genre"] in ("reg", "instance", "verrou")]
    procedure = POIDS_ROBUSTESSE["procedure_ancre"] if len(annees_procedure) >= 2 else (
        12 if annees_procedure else 5
    )

    etage = fente.etage if fente.etage in ETAGES else ETAGES[0]
    hauteur = round(POIDS_ROBUSTESSE["hauteur_d_etage"] * (ETAGES.index(etage) + 1) / len(ETAGES))
    resistance = round(POIDS_ROBUSTESSE["resistance_a_l_abrogation"] * (ETAGES.index(etage) + 1) / len(ETAGES))

    score = base_ecrite + clarte + procedure + hauteur + resistance
    if score >= 85:
        note = "solide : attaquable seulement à l'étage où elle se loge"
    elif score >= 65:
        note = "défendable : la base écrite tient, la procédure doit être irréprochable"
    elif score >= 45:
        note = "discutable : tient par la logique, pas par un texte qui la nomme"
    else:
        note = "fragile : à ne pas présenter comme un droit, seulement comme une lecture"
    return {
        "score": score,
        "bareme": POIDS_ROBUSTESSE,
        "details": {
            "base_ecrite": base_ecrite,
            "clarte_de_competence": clarte,
            "procedure_ancre": procedure,
            "hauteur_d_etage": hauteur,
            "resistance_a_l_abrogation": resistance,
        },
        "premisses_non_verifiables": [p["valeur"] for p in premisses if not p["verifiable"]],
        "note": note,
        "irrefutabilite": None,
        "limite": (
            "aucun score ne vaut immunité : le juge contrôle la compétence, la procédure, "
            "la motivation et les normes supérieures, jamais la cohérence d'une démonstration"
        ),
    }


def etage_de_verrouillage(fente: Fente) -> Dict[str, Any]:
    """Par quel étage de texte la fente se défait, et qui y a accès."""
    etage = fente.etage if fente.etage in ETAGES else ETAGES[0]
    return {
        "cle": fente.cle,
        "etage": etage,
        "hauteur": ETAGES.index(etage) + 1,
        "reversible_par": list(QUI_ATTAQUE.get(etage, ())),
        "regle": "le niveau d'attaque est le niveau le plus bas de la chaîne : une fente "
                 "assise sur un décret s'attaque par un décret",
    }


def instance(cle: str) -> Optional[Instance]:
    """Instance par sa clé, ou par un début de nom (« conseil » finds Conseil d'État)."""
    propre = (cle or "").strip().lower()
    if propre in INSTANCES:
        return INSTANCES[propre]
    for cle_instance, value in INSTANCES.items():
        if propre and (propre in cle_instance or propre in value.nom.lower()):
            return value
    return None


def instances_pour_article(numero: str) -> List[Dict[str, Any]]:
    """Les instances dont un article fonde, limite ou arme une compétence."""
    propre = (numero or "").strip()
    fiche = article(propre)
    if fiche is None:
        return []
    sorties = []
    for cle, value in INSTANCES.items():
        citee = propre in value.fondement
        liee = bool(set(value.peut_bloquer) & set(fiche.mecanismes))
        if citee or liee:
            sorties.append({
                "cle": cle,
                "nom": value.nom,
                "niveau": value.niveau,
                "lien": "fondement" if citee else "mécanisme partagé",
                "effets": list(value.effets),
            })
    return sorties


def saisines_pour(acteur: str) -> List[Dict[str, Any]]:
    """Ce qu'un acteur (groupe, électeur, justiciable, soixante-signataires) peut déclencher."""
    mot = (acteur or "").strip().lower()
    if len(mot) < 3:
        return []
    sorties = []
    for cle, value in INSTANCES.items():
        for saisine in value.saisissable_par:
            if mot in saisine.lower():
                seuils = [
                    {"cle": v, "formule": VERROUS[v].en_dict()["formule"]}
                    for v in value.verrous if v in VERROUS
                ]
                sorties.append({
                    "instance": cle,
                    "nom": value.nom,
                    "niveau": value.niveau,
                    "saisine": saisine,
                    "effets": list(value.effets),
                    "seuils": seuils,
                })
                break
    return sorties


def qui_juge(cle: str) -> Dict[str, Any]:
    """La chaîne de contrôle d'une instance, jusqu'à ce qu'elle bute sur le silence."""
    valeur = instance(cle)
    if valeur is None:
        return {"erreur": "instance inconnue", "instances": sorted(INSTANCES)}
    chaine = [{"cle": valeur.cle, "nom": valeur.nom, "controle_par": valeur.juge_par}]
    vus = {valeur.cle}
    courant = valeur
    for _ in range(5):
        suivant = None
        for autre in INSTANCES.values():
            if autre.cle in vus:
                continue
            if autre.cle in courant.juge_par or autre.nom.lower() in courant.juge_par.lower():
                suivant = autre
                break
        if suivant is None:
            break
        chaine.append({"cle": suivant.cle, "nom": suivant.nom, "controle_par": suivant.juge_par})
        vus.add(suivant.cle)
        courant = suivant
    return {
        "depart": valeur.cle,
        "chaine": chaine,
        "longueur": len(chaine),
        "bout_de_chaine": chaine[-1]["controle_par"],
        "sans_recours": "aucun" not in chaine[-1]["controle_par"].lower()
                        and "personne" not in chaine[-1]["controle_par"].lower()
                        and len(chaine) < 5,
    }


def boucle_de_controles() -> List[Dict[str, Any]]:
    """Les boucles de contrôle complètes : où elles se ferment, où elles n'existent pas."""
    boucles = {
        "decret": ("réglementaire", ["préfet", "juridictions_administratives", "conseil_etat", "cjue"]),
        "loi": ("loi ordinaire", ["conseil_constitutionnel", "conseil_etat", "cour_de_cassation", "cjue", "cedh"]),
        "loi_organique": ("loi organique", ["conseil_constitutionnel"]),
        "reglement_assemblee": ("loi organique", ["conseil_constitutionnel"]),
        "revision": ("constitutionnel", ["conseil_constitutionnel", "peuple", "congres"]),
        "loi_referendaire": ("constitutionnel", []),
        "acte_local": ("réglementaire", ["prefet", "juridictions_administratives", "cour_des_comptes"]),
    }
    sorties = []
    for cle, (etage, cles) in boucles.items():
        maillons = [INSTANCES[c] for c in cles if c in INSTANCES]
        sorties.append({
            "cle": cle,
            "etage_attaque": etage,
            "voies_de_recours": [
                {"cle": m.cle, "nom": m.nom, "effets": list(m.effets)} for m in maillons
            ],
            "absentes": [c for c in cles if c not in INSTANCES],
            "sans_controle": not maillons,
            "lecture": (
                "aucune instance saisissable : c'est la définition même d'un pouvoir sans "
                "contre-pouvoir juridictionnel" if not maillons else
                f"{len(maillons)} voies de recours, dont au moins une mène hors de France"
            ),
        })
    return sorties


def strategies_pour(
    famille: Optional[str] = None, instance_cle: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Les stratégies documentées, filtrables par famille ou par instance."""
    sorties = []
    for value in STRATEGIES.values():
        if famille and value.famille != famille:
            continue
        if instance_cle and value.instance != instance_cle:
            continue
        sorties.append(value.en_dict())
    return sorties


def fentes_pour(numero: Optional[str] = None, type_fente: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fentes et portes, filtrables par article ou par nature."""
    sorties = []
    for value in FENTES.values():
        if numero and numero not in value.articles:
            continue
        if type_fente and value.type != type_fente:
            continue
        sorties.append({
            "cle": value.cle,
            "nom": value.nom,
            "type": value.type,
            "sens": value.sens,
            "articles": list(value.articles),
            "etage": value.etage,
            "score": robustesse(value)["score"],
            "fiabilite": value.fiabilite,
        })
    return sorties


def rechercher(terme: str) -> List[Dict[str, Any]]:
    """Recherche plein texte sur les quatre registres du module."""
    mot = _sans_accents((terme or "").strip())
    if len(mot) < 3:
        return []
    sorties = []
    registres = [
        ("instance", INSTANCES, ("nom", "mission", "observation", "composition", "juge_par")),
        ("strategie", STRATEGIES, ("nom", "acte", "condition", "deja_vue")),
        ("fente", FENTES, ("nom", "deduction", "raison_du_silence", "ce_que_ca_change",
                           "point_de_vigilance")),
        ("trajet", TRAJETS, ("nom", "issue", "note")),
    ]
    for genre, table, champs in registres:
        for cle, value in table.items():
            for champ in champs:
                texte = _sans_accents(str(getattr(value, champ, "")))
                if mot in texte:
                    index = texte.find(mot)
                    sortie = _sans_accents(str(getattr(value, champ, "")))
                    sorties.append({
                        "type": genre,
                        "cle": cle,
                        "nom": getattr(value, "nom", cle),
                        "champ": champ,
                        "extrait": "…" + sortie[max(0, index - 60):index + len(mot) + 90] + "…",
                    })
                    break
    return sorties


def _sans_accents(texte: str) -> str:
    """Repli d'indexation : la recherche doit marcher avec ou sans accents."""
    if not texte:
        return ""
    decompose = unicodedata.normalize("NFD", texte.lower())
    return "".join(c for c in decompose if not unicodedata.combining(c))


def coherence_avec_le_droit() -> Dict[str, Any]:
    """Aucune référence du module ne doit pointer dans le vide.

    C'est le contrat anti-décoration : une instance dont l'article n'existe pas, une
    stratégie dont l'instance est inventée, une fente dont une prémisses n'est pas
    résoluble, ou une fente annoncée chiffrée sans calcul disponible — tout remonte ici.
    """
    problemes: Dict[str, List[str]] = {
        "instances_niveau_invalide": [],
        "instances_effet_inconnu": [],
        "instances_fondement_non_resolu": [],
        "instances_verrou_inexistant": [],
        "strategies_famille_inconnue": [],
        "strategies_instance_inconnue": [],
        "strategies_article_inexistant": [],
        "fentes_premisse_non_resolue": [],
        "fentes_etage_inconnu": [],
        "fentes_chiffrage_incoherent": [],
        "trajets_article_inexistant": [],
        "trajets_blocage_inexistant": [],
    }
    for cle, value in INSTANCES.items():
        if value.niveau not in NIVEAUX:
            problemes["instances_niveau_invalide"].append(f"{cle}:{value.niveau}")
        for effet in value.effets:
            if effet not in EFFETS:
                problemes["instances_effet_inconnu"].append(f"{cle}:{effet}")
        refs = _references(value.fondement)
        for numero in refs["articles"]:
            if numero not in ARTICLES:
                problemes["instances_fondement_non_resolu"].append(f"{cle}:art {numero}")
        for ident in refs["registre"]:
            if ident not in REGISTRE_LEGAL:
                problemes["instances_fondement_non_resolu"].append(f"{cle}:{ident}")
        for verrou in value.verrous:
            if verrou not in VERROUS:
                problemes["instances_verrou_inexistant"].append(f"{cle}:{verrou}")
    for cle, value in STRATEGIES.items():
        if value.famille not in FAMILLES_STRATEGIE:
            problemes["strategies_famille_inconnue"].append(f"{cle}:{value.famille}")
        if value.instance and value.instance not in INSTANCES:
            problemes["strategies_instance_inconnue"].append(f"{cle}:{value.instance}")
        for numero in value.fondement:
            if numero not in ARTICLES:
                problemes["strategies_article_inexistant"].append(f"{cle}:{numero}")
    for cle, value in FENTES.items():
        for premise in value.premisses:
            if not _resoudre(premise)["resolu"]:
                problemes["fentes_premisse_non_resolue"].append(f"{cle}:{premise}")
        if value.etage not in ETAGES:
            problemes["fentes_etage_inconnu"].append(f"{cle}:{value.etage}")
        chiffre = effets_de_fente(cle)["type"] != "non_chiffree"
        if bool(value.computation) != chiffre:
            problemes["fentes_chiffrage_incoherent"].append(cle)
    for cle, value in TRAJETS.items():
        for numero in value.articles:
            if numero not in ARTICLES:
                problemes["trajets_article_inexistant"].append(f"{cle}:{numero}")
        for blocage in value.blocages:
            if blocage not in MECANISMES:
                problemes["trajets_blocage_inexistant"].append(f"{cle}:{blocage}")
    vides = [k for k, v in problemes.items() if not v]
    for cle in vides:
        problemes.pop(cle)
    return {
        "instances": len(INSTANCES),
        "trajets": len(TRAJETS),
        "strategies": len(STRATEGIES),
        "fentes": len(FENTES),
        "filtres_appliques": FILTRES_NORMALISATION,
        "problemes": problemes,
        "conforme": not problemes,
    }


def synthese_pour_api() -> Dict[str, Any]:
    """Le payload complet, sérialisable en JSON, avec ses dates et ses limites."""
    tableaux = []
    for cle in INSTANCES:
        donnees = INSTANCES[cle].en_dict()
        tableaux.append({k: donnees[k] for k in (
            "cle", "nom", "niveau", "mission", "fondement", "effets", "peut_bloquer",
            "juge_par", "fiabilite", "delais", "saisissable_par",
        )})
    return {
        "titre": "Instances, yoyo parlementaire et fentes non écrites",
        "accroche": (
            "Qui peut saisir quoi, combien de battements tient une navette, et ce que la "
            "logique des textes permet sans que personne ne l'ait écrit."
        ),
        "avertissement": (
            "Une fente n'est pas un droit : c'est une conséquence qui tient parce que ses "
            "prémisses sont écrites et que personne n'en a tiré la conséquence. Le score de "
            "robustesse mesure la défendabilité, jamais l'immunité : le Conseil d'État contrôle "
            "la compétence, la procédure et la motivation, pas la beauté du raisonnement."
        ),
        "date_observation": DATE_OBSERVATION,
        "methode": (
            "Trois registres reliés : les instances (compétence, saisine, effets, contrôle), "
            "les trajets (battements chiffrés en jours de rigueur, issus des fiches "
            "constitutionnelles), les stratégies et les fentes (déductions dont chaque "
            "prémisses est résoluble dans le dépôt). Les nombres viennent des verrous du "
            "module des contre-pouvoirs, jamais d'une estimation maison."
        ),
        "niveaux": list(NIVEAUX),
        "effets": EFFETS,
        "etages": list(ETAGES),
        "qui_attaque": QUI_ATTAQUE,
        "instances": tableaux,
        "trajets": [oscillation(cle) for cle in TRAJETS],
        "asymetrie": asymetrie_des_chambres(),
        "rapport_de_temps": rapport_de_temps(),
        "strategies": [value.en_dict() for value in STRATEGIES.values()],
        "fentes": [value.en_dict() for value in FENTES.values()],
        "boucles_de_controle": boucle_de_controles(),
        "coherence": coherence_avec_le_droit(),
        "fenetre_residuelle": {
            "jours": FENETRE_RESIDUELLE_JOURS,
            "note": FENETRE_RESIDUELLE_NOTE,
        },
    }


def resume_console() -> str:
    coherent = coherence_avec_le_droit()
    lignes = [
        f"Instances et dynamiques — {len(INSTANCES)} instances, {len(TRAJETS)} trajets, "
        f"{len(STRATEGIES)} stratégies, {len(FENTES)} fentes et portes.",
        f"État constaté le {DATE_OBSERVATION} ; fenêtre législative résiduelle de "
        f"{FENETRE_RESIDUELLE_JOURS} jours.",
    ]
    chiffrees = sum(1 for c in FENTES if effets_de_fente(c)["type"] != "non_chiffree")
    lignes.append(
        f"Déductions non écrites : {sum(1 for f in FENTES.values() if f.type == 'fente')} fentes, "
        f"{sum(1 for f in FENTES.values() if f.type == 'porte')} portes, "
        f"{sum(1 for f in FENTES.values() if f.type == 'droit_sans_juge')} droits sans juge, "
        f"{chiffrees} chiffrées par le calcul des seuils."
    )
    if coherent["conforme"]:
        lignes.append(" Cohérence avec le droit : aucune référence orpheline.")
    else:
        lignes.append(f" ⚠ Incohérences : {coherent['problemes']}")
    if FILTRES_NORMALISATION:
        lignes.append(f" Références retirées car absentes du catalogue : {FILTRES_NORMALISATION}")
    return "\n".join(lignes)


FILTRES_NORMALISATION = _normaliser()
