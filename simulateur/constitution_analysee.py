"""
simulateur/constitution_analysee.py — R&D « article par article » de la Constitution
du 4 octobre 1958, à jour de la révision constitutionnelle du 8 mars 2024.

Ce module répond à une question simple, que le reste du dépôt traitait par bribes :
**qu'est-ce que le texte permet, qu'est-ce qu'il interdit, et qu'est-ce qui bloque
ce qu'il permet ?** Pour chaque article en vigueur, la fiche consignée ici sépare
explicitement :

  * les **opportunités** — les facultés ouvertes par le texte (à qui, à quelle
    condition, avec quel délai) ;
  * les **contraintes** — les verrous, seuils, délais et interdictions ;
  * les **contre-pouvoirs** — qui peut faire échec, par quel article, avec quel
    seuil ;
  * les **règles chiffrées** — les nombres écrits dans le texte (dixième,
    cinquième, trois cinquièmes, quarante-huit heures, dix jours, soixante-dix
    jours…), parce que ce sont eux qui décident de la faisabilité ;
  * les **croisements** — les autres articles avec lesquels celui-ci réagit
    (aucun article ne fonctionne seul : le 49.3 n'existe que par le 49.2, le 11
    n'existe que par le 60, l'89 n'existe que par le 3 et le 61) ;
  * les **strates** touchées et les **mécanismes** du moteur
    (`simulateur.gouvernance_contrepouvoir`) et les **leviers** du catalogue
    (`simulateur.parametres`) que l'article encadre.

Convention de rédaction
-----------------------
Les articles courts ou à forte densité normative sont cités in extenso ; les
autres font l'objet d'une **synthèse de travail** qui conserve les chiffres, les
délais et les verrous du texte. Aucun alinéa n'est réinventé : la source est
systématiquement le texte intégral publié par le Conseil constitutionnel,
consulté le 12 octobre 2026 (voir `SOURCE_CC`). Ce module n'est pas une note
juridique : il alimente un simulateur, il ne remplace ni le Conseil
constitutionnel ni un juriste.

Sommaire des titres et comptage (vérifié sur le texte officiel)
----------------------------------------------------------------
Titre I  De la souveraineté (1-4) ; Titre II  Le Président de la République
(5-19) ; Titre III  Le Gouvernement (20-23) ; Titre IV  Le Parlement (24-33) ;
Titre V  Des rapports entre le Parlement et le Gouvernement (34 à 51-2) ;
Titre VI  Des traités internationaux (52-55) ; Titre VII  Le Conseil
constitutionnel (56-63) ; Titre VIII  De l'autorité judiciaire (64-66-1) ;
Titre IX  La Haute Cour (67-68) ; Titre X  De la responsabilité pénale des
membres du Gouvernement (68-1 à 68-3) ; Titre XI  Le Conseil économique, social
et environnemental (69-71) ; Titre XI bis  Le Défenseur des droits (71-1) ;
Titre XII  Des collectivités territoriales (72 à 75-1) ; Titre XIII  Dispositions
transitoires relatives à la Nouvelle-Calédonie (76-77) ; Titre XIV  De la
francophonie et des accords d'association (87-88) ; Titre XV  De l'Union
européenne (88-1 à 88-7) ; Titre XVI  De la révision (89). Le titre XII compte
dix articles (72, 72-1, 72-2, 72-3, 72-4, 73, 74, 74-1, 75, 75-1) et le titre V
vingt-six, ce qui porte le total à cent neuf.

**109 articles en vigueur** sont fichés ci-dessous (décompte vérifié par
`couverture()` : les numéros attendus d'après le texte officiel et les numéros fichés
doivent coïncider exactement). S'y ajoutent les articles
abrogés, consignés dans `ABROGES` pour éviter qu'un scénario les réutilise par
erreur : les articles 78 à 86 (Communauté, abrogés par la loi constitutionnelle
du 4 août 1995) et l'article 90 (dispositions transitoires).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from .parametres import LEVIERS as _LEVIERS


def _sans_accents(texte: str) -> str:
    """Clé de rapprochement : « probité_vie_publique » vaut pour « probite_vie_publique »."""
    return "".join(
        c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn"
    ).lower()


#: Correspondance des clés du catalogue, accents confondus (les fiches sont
#: rédigées à la main : un accent oublié ne doit pas créer une piste fantôme).
_CIBLES_LEVIERS: dict[str, str] = {_sans_accents(c): c for c in _LEVIERS}

#: Source primaire du texte intégré ici.
SOURCE_CC = ("https://www.conseil-constitutionnel.fr/le-bloc-de-constitutionnalite/"
             "texte-integral-de-la-constitution-du-4-octobre-1958-en-vigueur")
#: Date de consultation du texte (le droit évolue : elle est affichée avec chaque fiche).
DATE_CONSULTATION = "2026-10-12"
#: État du texte.
VERSION_TEXTE = "à jour de la révision constitutionnelle du 8 mars 2024 (IVG, article 34)"

#: Échelons admis (mêmes noms que `reglements_lois.STRATES_VALIDES`).
STRATES: tuple[str, ...] = ("Local", "National", "Europe", "Mondial", "Transversal")

#: Fonctions institutionnelles (filtre d'affichage et de recherche).
FONCTIONS: tuple[str, ...] = (
    "souveraineté", "exécutif", "législatif", "procédure législative", "budget",
    "contrôle & évaluation", "autorité judiciaire", "outre-mer", "collectivités",
    "démocratie participative", "Europe & traités", "révision", "haute cour",
    "droits & libertés", "organisation",
)


@dataclass(frozen=True)
class ArticleConstitution:
    """Fiche d'un article : ce qu'il permet, ce qu'il interdit, qui peut bloquer."""

    numero: str
    titre: str
    bloc: str
    fonction: str
    autorite: str
    resume: str
    regles: tuple[str, ...] = ()
    opportunites: tuple[str, ...] = ()
    contraintes: tuple[str, ...] = ()
    contre_pouvoirs: tuple[str, ...] = ()
    croisements: tuple[str, ...] = ()
    strates: tuple[str, ...] = ("National",)
    mecanismes: tuple[str, ...] = ()
    leviers: tuple[str, ...] = ()
    #: pistes de réforme que l'article encadre mais que le catalogue ne modélise
    #: pas encore (aucun levier `LEVIERS` de ce nom : rien n'est chiffré).
    pistes: tuple[str, ...] = ()
    cite_texte: bool = False

    # ── sérialisation pour l'API et la page ────────────────────────────────
    def en_dict(self) -> dict[str, Any]:
        return {
            "numero": self.numero,
            "titre": self.titre,
            "bloc": self.bloc,
            "fonction": self.fonction,
            "autorite": self.autorite,
            "resume": self.resume,
            "regles_chiffrees": list(self.regles),
            "opportunites": list(self.opportunites),
            "contraintes": list(self.contraintes),
            "contre_pouvoirs": list(self.contre_pouvoirs),
            "croisements": list(self.croisements),
            "strates": list(self.strates),
            "mecanismes": list(self.mecanismes),
            "leviers": list(self.leviers),
            "pistes": list(self.pistes),
            "cite_texte": self.cite_texte,
            "identification": f"Article {self.numero} — {self.titre}",
            "source": SOURCE_CC,
            "version": VERSION_TEXTE,
            "consulte_le": DATE_CONSULTATION,
        }

    def verrous_texte(self) -> list[str]:
        """Tous les nombres du texte qui bornent l'action (délais, quotes, majorités)."""
        return list(self.regles)

    def bilan(self) -> dict[str, int]:
        return {
            "opportunites": len(self.opportunites),
            "contraintes": len(self.contraintes),
            "contre_pouvoirs": len(self.contre_pouvoirs),
            "regles_chiffrees": len(self.regles),
            "croisements": len(self.croisements),
        }


def _T(nom_bref: str, intitule: str) -> str:
    return f"Titre {nom_bref} — {intitule}"


Blocs = {
    "I": _T("I", "De la souveraineté"),
    "II": _T("II", "Le Président de la République"),
    "III": _T("III", "Le Gouvernement"),
    "IV": _T("IV", "Le Parlement"),
    "V": _T("V", "Des rapports entre le Parlement et le Gouvernement"),
    "VI": _T("VI", "Des traités internationaux"),
    "VII": _T("VII", "Le Conseil constitutionnel"),
    "VIII": _T("VIII", "De l'autorité judiciaire"),
    "IX": _T("IX", "La Haute Cour"),
    "X": _T("X", "De la responsabilité pénale des membres du Gouvernement"),
    "XI": _T("XI", "Le Conseil économique, social et environnemental"),
    "XI bis": _T("XI bis", "Le Défenseur des droits"),
    "XII": _T("XII", "Des collectivités territoriales"),
    "XIII": _T("XIII", "Dispositions transitoires relatives à la Nouvelle-Calédonie"),
    "XIV": _T("XIV", "De la francophonie et des accords d'association"),
    "XV": _T("XV", "De l'Union européenne"),
    "XVI": _T("XVI", "De la révision"),
}


def _a(
    numero: str,
    titre: str,
    bloc: str,
    fonction: str,
    autorite: str,
    resume: str,
    regles: Iterable[str] = (),
    opportunites: Iterable[str] = (),
    contraintes: Iterable[str] = (),
    contre: Iterable[str] = (),
    croise: Iterable[str] = (),
    strates: Iterable[str] = ("National",),
    mecanismes: Iterable[str] = (),
    leviers: Iterable[str] = (),
    pistes: Iterable[str] = (),
    cite: bool = False,
) -> ArticleConstitution:
    """Fabrique compacte des fiches (une ligne par donnée, table lisible).

    Seules les clés existant dans le catalogue (`parametres.LEVIERS`) restent dans
    `leviers` : un article ne peut être relié qu'à un réglage réellement chiffré.
    Les autres noms sont requalifiés en `pistes` — des idées de réforme que
    l'article encadre, que le modèle ne simule pas, et qu'il faut assumer comme
    telles plutôt que de les faire passer pour des paramètres.
    """
    levier_valides, pistes_restees = [], list(pistes)
    for cle in leviers:
        cle = cle.strip()
        reel = _CIBLES_LEVIERS.get(_sans_accents(cle))
        if reel:
            levier_valides.append(reel)
        elif cle:
            pistes_restees.append(cle)
    return ArticleConstitution(
        numero=numero, titre=titre, bloc=Blocs[bloc], fonction=fonction, autorite=autorite,
        resume=resume, regles=tuple(regles), opportunites=tuple(opportunites),
        contraintes=tuple(contraintes), contre_pouvoirs=tuple(contre),
        croisements=tuple(croise), strates=tuple(strates), mecanismes=tuple(mecanismes),
        leviers=tuple(levier_valides), pistes=tuple(pistes_restees),
        cite_texte=cite,
    )


# ────────────────────────────────────────────────────────────────────────────
# TITRE I — DE LA SOUVERAINETÉ (articles 1 à 4)
# ────────────────────────────────────────────────────────────────────────────

_TITRE_I: tuple[ArticleConstitution, ...] = (
    _a("1", "République indivisible, laïque, démocratique et sociale ; organisation décentralisée",
       "I", "souveraineté", "Législateur (loi) et réviseur (89)",
       "« La France est une République indivisible, laïque, démocratique et sociale. Elle assure "
       "l'égalité devant la loi de tous les citoyens sans distinction d'origine, de race ou de "
       "religion. Elle respecte toutes les croyances. Son organisation est décentralisée. » Le "
       "second alinéa impose que « la loi favorise l'égal accès des femmes et des hommes aux mandats "
       "électoraux et fonctions électives, ainsi qu'aux responsabilités professionnelles et sociales ».",
       regles=["parité : obligation de « favoriser », pas de quota auto-exécutoire",
               "le statut civil de droit commun renvoie à l'article 34 (seul visé pour l'état des personnes)"],
       opportunites=["fonde toute loi de parité, de non-cumul et de transparence de la vie publique",
                     "interdit toute tutelle d'une collectivité sur une autre via l'article 72 (indivisibilité)",
                     "justifie un service public nationalisé sans rupture du cadre (égalité devant la loi)"],
       contraintes=["interdit un « pays » ou une nation reconnue dans le corps électoral (contrôle du Conseil "
                    "constitutionnel sur les listes électorales particulières)",
                    "interdit la discrimination par l'origine, la race ou la religion dans la loi",
                    "la laïcité borne toute aide directe aux cultes (loi de 1905)"],
       contre=["Conseil constitutionnel (61, 61-1) censure la loi qui méconnaîtrait l'indivisibilité",
               "révision impossible sans 89 (et sans Congrès à 3/5 ou référendum)"],
       croise=["2", "3", "34", "72", "72-2", "75"],
       strates=["Transversal", "Local", "National"],
       mecanismes=("revision_constitutionnelle", "censure_parlementaire"),
       leviers=("reforme_parité",)),
    _a("2", "Principes et symboles de la République ; « gouvernement du peuple, par le peuple et pour le peuple »",
       "I", "souveraineté", "Constituant",
       "Quatre alinéas : langue (le français), emblème (drapeau tricolore), hymne (« La Marseillaise »), "
       "devise (« Liberté, Égalité, Fraternité ») et principe — « gouvernement du peuple, par le peuple et "
       "pour le peuple ». Le principe est la porte d'entrée de toute revendication de démocratie directe.",
       regles=["alinéa 5 (révision du 23 juillet 2008) : clause de principe, non auto-suffisante",
               "la langue constitutionnelle est le français : les actes officiels doivent l'être"],
       opportunites=["légitime le RIC, le référendum d'initiative locale et la révocabilité des mandats "
                     "comme réponse à la « captation » de la souveraineté",
                     "fondement de l'exigence de comptes rendus publics : « pour le peuple » = obligation de résultat lisible",
                     "appuyé par l'article 33 (séances publiques) et 47-2 (comptes réguliers et sincères)"],
       contraintes=["le principe n'a pas, seul, valeur de règle opposable à un législateur qui garde "
                    "l'initiative (34 et 39)",
                    "aucune « section du peuple » ne peut s'attribuer l'exercice de la souveraineté (alinéa 3 de l'article 3)"],
       contre=["Conseil constitutionnel : la portée normative de l'article 2 est reconnue mais bornée",
               "révision de l'article 2 possible par 89 seulement (la forme républicaine du gouvernement, elle, est "
               "verrouillée par l'alinéa final de l'89)"],
       croise=["3", "11", "23", "33", "47-2", "75-1", "89"],
       strates=["Transversal"],
       mecanismes=("ric_souverain", "referendum_legislatif"),
       leviers=("reforme_ric", "reforme_vote_blanc", "reforme_casier_b2")),
    _a("3", "Souveraineté nationale : représentants + référendum ; suffrage universel, égal et secret",
       "I", "souveraineté", "Corps électoral ; Parlement ; Président (11) ; électeurs locaux (72-1)",
       "« La souveraineté nationale appartient au peuple qui l'exerce par ses représentants et par la voie "
       "du référendum. Aucune section du peuple ni aucun individu ne peut s'en attribuer l'exercice. » Le "
       "suffrage est « toujours universel, égal et secret » ; sont électeurs tous les nationaux majeurs "
       "jouissant de leurs droits civils et politiques.",
       regles=["référendum = voie constitutionnelle alternative, non subsidiaire",
               "égalité du suffrage : contrôle arithmétique de la découpe des circonscriptions (25, commission indépendante)",
               "les majeurs de 18 ans ; retrait des droits civiques seulement par une décision de justice"],
       opportunites=["le référendum n'a pas de contenu obligatoire : l'article 11 en définit les objets, "
                     "l'article 89 la révision, l'article 72-1 le niveau local",
                     "ouvre la démocratie continue sans dissolution ni révision profonde (pétitions, référendums locaux)",
                     "l'égalité du suffrage permet de contester un redécoupage ou un mode de scrutin "
                     "sur-représentant les territoires peu peuplés"],
       contraintes=["interdit toute assemblée se proclamant seule représentante du peuple",
                    "interdit le mandat impératif (27) : le « donneur d'ordre » ne peut imposer son vote",
                    "le référendum d'article 11 ne peut abroger une disposition promulguée depuis moins d'un an (11 al.4)"],
       contre=["Conseil constitutionnel : juge de la régularité des scrutins (58, 59, 60) et de la recevabilité "
               "d'un RIP (61 al.1)",
               "Sénat (24) représente les collectivités : un scrutin national ne peut les effacer"],
       croise=["2", "4", "11", "24", "25", "27", "58", "59", "60", "72-1", "89"],
       strates=["National", "Local"],
       mecanismes=("referendum_legislatif", "rip", "ric_souverain", "referendum_local"),
       leviers=("reforme_ric", "reforme_vote_blanc", "reforme_proportionnelle")),
    _a("4", "Partis et groupements politiques : liberté de formation, devoir de pluralisme",
       "I", "démocratie participative", "Législateur (financement), partis, CNCCFP",
       "« Les partis et groupements politiques concourent à l'expression du suffrage. Ils se forment et "
       "exercent leur activité librement. Ils doivent respecter les principes de la souveraineté nationale "
       "et de la démocratie. » Ils contribuent à l'égal accès des femmes et des hommes ; « la loi garantit "
       "les expressions pluralistes des opinions et la participation équitable des partis […] à la vie "
       "démocratique de la Nation ».",
       regles=["financement public : aide publique liée aux résultats (1 % des suffrages au 1er tour pour la "
               "première fraction, 1,5 M€ par candidat pour la seconde, plafonds de dépenses)",
               "pas d'auto-financement occulte : compte de campagne et plafonds (code électoral L. 52-12)",
               "deux fractions de l'aide : une liée aux élus, une à l'égalité femmes/hommes (pénalité financière)"],
       opportunites=["la loi peut modifier la répartition de l'aide pour favoriser les partis structurés "
                     "nationalement, ou au contraire les petites formations (levier de pluralisme)",
                     "l'exigence constitutionnelle de « participation équitable » fonde un financement "
                     "proportionnel aux voix, et non seulement aux groupes",
                     "les règles de financement sont un levier anti-lobbying : transparence des comptes, "
                     "plafonnement, sanctions"],
       contraintes=["interdit le monopartyisme ; un parti « dissous » l'est seulement par le juge sur la base "
                    "de la loi du 10 janvier 1936 (proposition récurrente, jamais constitutionnalisée)",
                    "les partis doivent respecter souveraineté nationale et démocratie : un programme "
                    "sécessionnaire est un risque juridique, non une option institutionnelle"],
       contre=["Conseil constitutionnel (61) censure un financement qui méconnaîtrait le pluralisme",
               "CNCCFP et juge judiciaire pour les sanctions financières",
               "Parlement (49/50) peut renverser un gouvernement qui toucherait au financement sans compromis"],
       croise=["1", "3", "11", "34", "61"],
       strates=["National", "Local"],
       mecanismes=("financement_partis",),
       leviers=("reforme_financement_partis",)),
)


# ────────────────────────────────────────────────────────────────────────────
# TITRE II — LE PRÉSIDENT DE LA RÉPUBLIQUE (articles 5 à 19)
# ────────────────────────────────────────────────────────────────────────────

_TITRE_II: tuple[ArticleConstitution, ...] = (
    _a("5", "Rôle du Président : veille à la Constitution, arbitrage, continuité de l'État",
       "II", "exécutif", "Président de la République",
       "« Le Président de la République veille au respect de la Constitution. Il assure, par son arbitrage, "
       "le fonctionnement régulier des pouvoirs publics ainsi que la continuité de l'État. Il est le garant "
       "de l'indépendance nationale, de l'intégrité du territoire et du respect des traités. »",
       regles=["aucun pouvoir propre écrit ailleurs : l'article 5 est un titre d'agir, pas une compétence",
               "l'arbitrage n'est justiciable de rien (67 : irresponsabilité)"],
       opportunites=["nommer un Premier ministre non issu du premier parti (8) pour débloquer une "
                     "formation gouvernementale",
                     "saisir le Conseil constitutionnel (61) et le consulter (16, 54)",
                     "parler au Congrès (18) et, par là, imposer un agenda national sans engager de vote",
                     "déclencher la révision (89, sur proposition du Gouvernement) ou le référendum (11)"],
       contraintes=["ne peut pas révoquer un Premier ministre qui ne démissionne pas : l'alinéa 1 de "
                    "l'article 8 lie la fin des fonctions à la présentation de la démission",
                    "ne peut pas dissoudre « de confort » sans perdre la possibilité d'un gouvernement "
                    "minoritaire stable (12, 180 jours entre tours)"],
       contre=["Parlement (49, 50) : le gouvernement reste responsable devant l'Assemblée nationale",
               "Conseil constitutionnel (58, 7, 16 al. final, 68) sur les scrutins, l'empêchement, "
               "les pouvoirs exceptionnels et la destitution"],
       croise=["8", "11", "12", "16", "18", "54", "61", "68", "89"],
       mecanismes=("arbitrage_presidentiel", "dissolution", "message_congres"),
       leviers=("pouvoir_propre_president",)),
    _a("6", "Élection du Président au suffrage universel direct pour cinq ans ; deux mandats consécutifs maximum",
       "II", "souveraineté", "Corps électoral",
       "Le Président est élu à la majorité absolue des suffrages exprimés, pour cinq ans ; « nul ne peut "
       "exercer plus de deux mandats consécutifs » (alinéa ajouté le 23 juillet 2008). Les modalités "
       "(présentation par cinquante citoyens, campagne, compte de campagne) relèvent d'une loi organique.",
       regles=["mandat de 5 ans (quinquennat depuis la révision du 2 octobre 2000)",
               "2 mandats consécutifs maximum — un mandat discontinu reste possible",
               "cinquante présentations d'élus (loi organique) pour se porter candidat"],
       opportunites=["aligner l'élection présidentielle sur les législatives dans le même quinquennat "
                     "(chronologie 2002→2017) maximise l'emport législatif",
                     "le calendrier connu (20 jours au moins, 35 jours au plus avant l'expiration, art. 7) "
                     "rend le pays prévisible pour les agents économiques"],
       contraintes=["mandat figé : pas de dissolution anticipée du lien présidentiel (le 12 ne dissout "
                    "que l'Assemblée nationale)",
                    "l'article 7 interdit les articles 49, 50 et 89 pendant la vacance : pas de révision "
                    "constitutionnelle ni de censure en période électorale présidentielle"],
       contre=["Conseil constitutionnel : veille à la régularité, proclame les résultats, peut reporter "
               "le scrutin (7 al. 7 à 10)",
               "le Conseil peut déclarer l'empêchement, saisi par le Gouvernement"],
       croise=["7", "8", "49", "50", "58", "89"],
       mecanismes=("vacance_presidentielle", "report_scrutin"),
       leviers=("calendrier_electoral",)),
    _a("7", "Modalités du scrutin présidentiel : deux tours, convocation, vacance, report",
       "II", "souveraineté", "Gouvernement (convocation), Conseil constitutionnel (report, proclamation)",
       "Deux tours à quatorze jours d'intervalle, deux candidats maintenus ; scrutin ouvert sur convocation "
       "du Gouvernement ; élection du nouveau Président entre 20 et 35 jours avant l'expiration des pouvoirs "
       "du sortant. En cas de vacance ou d'empêchement, les fonctions sont provisoirement exercées par le "
       "président du Sénat (hors articles 11 et 12). Le Conseil constitutionnel peut reporter le scrutin en "
       "cas de décès ou d'empêchement d'un candidat.",
       regles=["quatorze jours entre les deux tours", "20 à 35 jours avant expiration des pouvoirs",
               "35 jours maximum de report après décision du Conseil (al. 10)",
               "interdiction des articles 49, 50 et 89 pendant la vacance ou l'empêchement définitif"],
       opportunites=["le président du Sénat assurant l'intérim, une chambre à majorité opposée peut "
                     "basculer l'intérim (1958, 1969, 1974, 2007 : à chaque fois le président du Sénat "
                     "a pesé sur la campagne)",
                     "l'impossibilité de dissoudre pendant l'intérim (11 et 12 retirés au suppléant) "
                     "stabilise la séquence électorale"],
       contraintes=["aucun référendum, aucune dissolution, aucune révision durant la vacance",
                    "impossibilité pour le suppléant de nommer librement un gouvernement de crise au-delà "
                    "des affaires courantes (usage, non texte)"],
       contre=["Conseil constitutionnel, seul juge de l'empêchement et du report",
               "le Gouvernement (alinéa 3 de l'article 8) retrouve la pleine main dès la fin de l'intérim"],
       croise=["5", "6", "8", "11", "12", "49", "50", "58", "89"],
       strates=["National", "Europe", "Mondial"],
       mecanismes=("vacance_presidentielle", "report_scrutin"),
       leviers=("calendrier_electoral",)),
    _a("8", "Nomination du Premier ministre et des ministres",
       "II", "exécutif", "Président de la République",
       "« Le Président de la République nomme le Premier ministre. Il met fin à ses fonctions sur la "
       "présentation par celui-ci de la démission du Gouvernement. » Sur proposition du Premier ministre, il "
       "nomme les autres membres du Gouvernement et met fin à leurs fonctions.",
       regles=["aucun délai de nomination écrit : le droit de blocage présidentiel est entier",
               "le Président ne peut révoquer un Premier ministre que s'il présente sa démission",
               "pas de contreseing pour la nomination du Premier ministre (19)"],
       opportunites=["gouvernement de coalition ou d'ouverture sans révision : le texte n'exige aucune "
                     "étiquette, seulement la capacité à ne pas être censuré (49.2)",
                     "remplacement ministériel « à la carte » (22, 8 al.2) pour arbitrer un budget bloqué",
                     "nommer un Premier ministre issu de la majorité relative la plus large (2024-2026 : "
                     "gouvernement sans majorité absolue, survie par non-censure)"],
       contraintes=["impossibilité de gouverner durablement sans la confiance implicite de l'Assemblée "
                    "nationale (20 al.3, 49, 50)",
                    "les fonctions ministérielles sont incompatibles avec tout mandat parlementaire (23) : "
                    "un gouvernement ne peut pas être une assemblée bis"],
       contre=["Assemblée nationale : motion de censure (49.2) ; Sénat : rien, mais l'article 49 al.4 "
               "permet de lui demander l'approbation d'une déclaration de politique générale",
               "Conseil constitutionnel : aucune saisine sur l'opportunité d'une nomination, seulement sur la "
               "loi organique qui l'encadre"],
       croise=["5", "9", "19", "20", "21", "23", "49", "50", "68-1"],
       mecanismes=("nomination_gouvernement", "gouvernement_minoritaire"),
       leviers=("droit_de_suite_pmr",)),
    _a("9", "Le Président préside le conseil des ministres",
       "II", "exécutif", "Président de la République",
       "« Le Président de la République préside le conseil des ministres. » Le Premier ministre ne peut le "
       "suppléer qu'à titre exceptionnel, par délégation expresse et pour un ordre du jour déterminé (21 al.5).",
       regles=["une seule exception écrite : la suppléance « à titre exceptionnel » (21)"],
       opportunites=["l'ordre du jour du conseil des ministres est le vrai filtre du processus législatif : "
                     "un texte non délibéré en conseil ne peut être déposé (39 al.2)",
                     "la délibération en conseil est la condition de validité des ordonnances (38) et des "
                     "décrets en conseil (13)"],
       contraintes=["un gouvernement sans feu vert présidentiel ne peut ni déposer un projet de loi ni "
                    "engager le 49.3 (49 al.3 : « après délibération du conseil des ministres »)"],
       contre=["Le Conseil constitutionnel rappelle qu'il n'appartient pas au Président de présider le "
               "Parlement ou la justice : la séparation vaut pour l'arbitrage (64 : il est « garant » de "
               "l'indépendance, pas chef)"],
       croise=["13", "21", "38", "39", "49"],
       mecanismes=("conseil_des_ministres",),
       leviers=("gouvernance_cycle_decisionnel",)),
    _a("10", "Promulgation dans les quinze jours ; demande de nouvelle délibération",
       "II", "législatif", "Président de la République",
       "Le Président promulgue les lois dans les quinze jours suivant la transmission au Gouvernement de la "
       "loi définitivement adoptée ; il peut, avant l'expiration de ce délai, demander au Parlement une "
       "nouvelle délibération de la loi ou de certains de ses articles — délibération qui « ne peut être refusée ».",
       regles=["15 jours pour promulguer", "nouvelle délibération = droit présidentiel, sans condition de fond",
               "le délai est suspendu par une saisine du Conseil constitutionnel (61 al.4)"],
       opportunites=["la demande de nouvelle délibération est un véto de fait : le texte revient devant le "
                     "Parlement, qui doit le revoter — une majorité fragile peut s'y briser",
                     "le report de promulgation laisse le temps d'une négociation (100 % des cas usités l'ont été "
                     "en conflit de compétence, non en censure)"],
       contraintes=["ne peut pas refuser de promulguer une loi votée (devoir, pas droit)",
                    "ne peut pas demander une nouvelle délibération d'une loi référendaire : le résultat "
                    "s'impose (11 al.8, 60)"],
       contre=["Parlement : il peut revoter à l'identique, et alors la promulgation devient obligatoire",
               "Conseil constitutionnel : la promulgation est interdite avant sa décision pour les lois "
               "organiques (46 al.5)"],
       croise=["11", "46", "61", "62"],
       mecanismes=("nouvelle_deliberation", "promulgation_bloquee"),
       leviers=("procedure_legislative_rythme",)),
    _a("11", "Référendum législatif et référendum d'initiative partagée (RIP)",
       "II", "démocratie participative", "Président (sur proposition du Gouvernement ou des deux assemblées) ; 1/5 du Parlement + 1/10 des électeurs",
       "Trois alinéas fondatifs : (1) le Président peut soumettre au référendum tout projet de loi portant "
       "sur l'organisation des pouvoirs publics, sur des réformes relatives à la politique économique, "
       "sociale ou environnementale et aux services publics qui y concourent, ou tendant à autoriser la "
       "ratification d'un traité ; (2) si le référendum est organisé sur proposition du Gouvernement, "
       "déclaration devant chaque assemblée suivie d'un débat ; (3) RIP : initiative d'un cinquième des "
       "membres du Parlement, soutenue par un dixième des électeurs ; (4) pas d'abrogation d'une disposition "
       "promulguée depuis moins d'un an ; (5)-(7) conditions organiques, délai d'examen, promulgation sous "
       "quinze jours ; (8) aucune nouvelle proposition sur le même sujet pendant deux ans.",
       regles=["1/5 des membres du Parlement = 116 députés et sénateurs (sur 925)",
               "1/10 des électeurs inscrits ≈ 4,9 millions de signatures (sur ~48,9 M d'inscrits)",
               "examen obligatoire par les deux assemblées dans un délai fixé par la loi organique "
               "(6 mois AN, 3 mois Sénat — loi organique du 6 novembre 2013) ; à défaut, le Président "
               "peut soumettre au référendum",
               "interdiction d'abroger une disposition promulguée depuis moins d'un an",
               "délai de 2 ans avant une nouvelle proposition de même objet après un rejet",
               "promulgation dans les 15 jours suivant la proclamation des résultats"],
       opportunites=["court-circuiter un Parlement bloqué sans dissoudre : le référendum n'exige aucune "
                     "majorité parlementaire",
                     "verrouiller une réforme contre les alternances : une loi référendaire ne peut être "
                     "abrogée que par une autre loi référendaire (jurisprudence et doctrine constantes)",
                     "le RIP impose le débat parlementaire même sans aboutir : les 4 tentatives (2013, 2015, "
                     "2019, 2019) ont toutes échoué au seuil parlementaire ou à l'étape du Sénat — la "
                     "procédure reste l'arme d'agenda de l'opposition",
                     "possibilité d'organiser un RIC par la voie du 11 si une révision antérieure le prévoit "
                     "(le texte ne le permet pas en l'état : il faut d'abord réviser)"],
       contraintes=["objet fermé : pas de référendum sur un traité contraire à la Constitution (il faut "
                    "d'abord réviser, 54), pas de référendum abrogatoire d'une loi récente, pas de "
                    "référendum sur les personnes (jurisprudence)",
                     "le Parlement peut faire échouer un RIP en ne l'inscrivant pas ou en le rejetant en "
                     "première lecture dans chaque assemblée",
                     "le Conseil constitutionnel contrôle la régularité de la procédure (61 al.1 pour les "
                     "propositions de l'article 11 ; 60 pour le scrutin)"],
       contre=["Sénat + Assemblée : rejet en 1re lecture dans les deux assemblées tue le RIP",
               "Conseil constitutionnel : contrôle des 10 % de signatures et de l'objet",
               "le Gouvernement peut retirer sa proposition avant le référendum"],
       croise=["2", "3", "10", "34", "54", "60", "61", "89", "72-1"],
       strates=["National", "Europe", "Transversal"],
       mecanismes=("referendum_legislatif", "rip", "ric_souverain"),
       leviers=("reforme_ric", "usage_referendum_11", "verrouillage_irreversibilite")),
    _a("12", "Dissolution de l'Assemblée nationale",
       "II", "exécutif", "Président de la République (après consultation du Premier ministre et des présidents d'assemblées)",
       "« Le Président de la République peut, après consultation du Premier ministre et des présidents des "
       "assemblées, prononcer la dissolution de l'Assemblée nationale. » Élections générales entre 20 et 40 "
       "jours après ; réunion de plein droit le deuxième jeudi suivant l'élection ; pas de nouvelle "
       "dissolution dans l'année qui suit ces élections.",
       regles=["20 à 40 jours entre dissolution et scrutin",
               "assemblée réunie de plein droit le 2e jeudi après l'élection ; session de droit de 15 jours "
               "si hors session ordinaire",
               "interdiction de nouvelle dissolution pendant 1 an (≈ 365 jours)",
               "impossible pendant l'article 16 (16 al.5) et, par l'effet de la coutume et de l'article 7, "
               "pas lors d'une vacance présidentielle"],
       opportunites=["arme de clarification en cas de blocage : redonne une base au gouvernement (1962, 1968, "
                     "1981, 1988, 1997, 2024)",
                     "consultation = avis conforme non requis : le Premier ministre et les présidents "
                     "d'assemblées ne peuvent pas s'y opposer juridiquement",
                     "le calendrier forcé (20-40 j) raccourcit la période d'incertitude budgétaire"],
       contraintes=["le risque est symétrique : 1997 et 2024 ont produit une assemblée moins gouvernable "
                    "que la précédente",
                    "un gouvernement démissionnaire expédie les affaires courantes entre la dissolution et "
                    "les élections : pas de nouveaux engagements de dépenses structurels",
                    "aucun référendum d'article 11 pendant la période électorale (12 + 11 ne se cumulent "
                    "pas : jurisprudence et doctrine)"],
       contre=["le corps électoral, seul contre-pouvoir sur la dissolution",
               "les présidents de groupe et le Sénat : chambre non dissoute, elle devient le point d'appui "
               "institutionnel pendant la campagne (rôle accru du Sénat de 20 à 40 jours)"],
       croise=["3", "5", "6", "7", "11", "16", "28", "32", "51", "72-1"],
       strates=["National", "Local", "Europe", "Mondial"],
       mecanismes=("dissolution", "demission_gouvernement", "gouvernement_affaires_courantes"),
       leviers=("usage_dissolution",)),
    _a("13", "Signature des ordonnances et décrets en conseil ; nominations ; avis des commissions",
       "II", "exécutif", "Président de la République ; commissions permanentes des assemblées",
       "Le Président signe ordonnances et décrets délibérés en conseil des ministres et nomme aux emplois "
       "civils et militaires de l'État. Une liste d'emplois réservés (conseillers d'État, grands chanceliers, "
       "ambassadeurs, conseillers maîtres à la Cour des comptes, préfets, officiers généraux, recteurs, "
       "directeurs d'administration centrale) est nommée en conseil. Pour les emplois « importants pour la "
       "garantie des droits et libertés ou la vie économique et sociale », la nomination est précédée d'un "
       "avis public des commissions compétentes et ne peut avoir lieu si l'addition des votes négatifs "
       "atteint trois cinquièmes des suffrages exprimés dans les deux commissions.",
       regles=["3/5 des suffrages exprimés (cumul des deux commissions) = véto parlementaire",
               "la loi organique fixe la liste des emplois soumis à avis (2010 : ~50 emplois, dont "
               "présidents d'autorités indépendantes)",
               "aucun délai pour signer ou refuser de signer un décret en conseil"],
       opportunites=["outil de refondation de la haute fonction publique : bloquer une candidature à la "
                     "tête d'une autorité ou d'une juridiction financière est à la portée d'une minorité "
                     "organisée (3/5 des exprimés)",
                     "le pouvoir de signature permet d'accélérer (ou de retenir) l'application d'une loi "
                     "votée : les décrets d'application sont le vrai point de blocage des réformes",
                     "le Président peut nommer un exécutif d'autorité indépendante dont l'indépendance est "
                     "protégée par l'irrévocabilité (cf. Cour des comptes)"],
       contraintes=["le véto de 3/5 est calculé sur les **suffrages exprimés** : s'abstenir n'est pas "
                    "faire obstacle — un blocage suppose de voter contre",
                    "les nominations ne créent aucune compétence : un directeur nommé ne peut pas "
                    "outrepasser la loi",
                    "le pouvoir de nomination ne dispense pas du contrôle du Conseil d'État sur les actes"],
       contre=["commissions permanentes des deux assemblées (avis conforme de fait)",
               "Conseil d'État (recours pour abus de pouvoir contre les mesures de nomination)",
               "Conseil constitutionnel sur la loi organique fixant la liste des emplois"],
       croise=["8", "9", "21", "38", "56", "65", "71-1"],
       mecanismes=("nominations_bloquees", "pouvoir_reglementaire"),
       leviers=("haute_fonction_publique_nomination",)),
    _a("14", "Accréditation des ambassadeurs",
       "II", "exécutif", "Président de la République",
       "« Le Président de la République accrédite les ambassadeurs et les envoyés extraordinaires auprès des "
       "puissances étrangères ; les ambassadeurs et les envoyés extraordinaires étrangers sont accrédités "
       "auprès de lui. »",
       regles=["forme régalienne : pas de vote parlementaire requis"],
       opportunites=["la diplomatie présidentielle peut porter un agenda international hors agenda "
                     "législatif (alliances, sanctions, recognition)"],
       contraintes=["engager la France vers l'extérieur sans texte législatif expose au rappel de "
                    "l'article 52-53 : tout traité engageant les finances de l'État demande une loi"],
       contre=["Parlement (53 : autorisation de ratifier ; 88-4 : résolutions européennes)",
               "Conseil constitutionnel (54 : conformité du traité)"],
       croise=["52", "53", "54", "88-4"],
       strates=["National", "Europe", "Mondial"],
       mecanismes=("diplomatie_presidentielle",)),
    _a("15", "Chef des armées ; conseils et comités supérieurs de défense",
       "II", "exécutif", "Président de la République",
       "« Le Président de la République est le chef des armées. Il préside les conseils et les comités "
       "supérieurs de la défense nationale. » Le Premier ministre est « responsable de la défense nationale » "
       "et assure l'exécution des lois (21 al.1) : la Constitution partage le sommet de la pyramide.",
       regles=["partage écrit 15/21 : le chef des armées préside, le Premier ministre dirige l'action du "
               "gouvernement et répond de l'exécution",
               "l'engagement des forces à l'étranger tombe sous le régime de l'article 35 (information sous "
               "3 jours, autorisation au-delà de 4 mois)"],
       opportunites=["l'arme de dissuasion relève du seul arbitrage présidentiel, hors vote : c'est le "
                     "noyau de souveraineté que nul gouvernement ne peut déléguer",
                     "les comités supérieurs permettent de trancher un effort de défense sans attendre une "
                     "loi de programmation (laquelle reste nécessaire pour engager des crédits pluriannuels)"],
       contraintes=["pas de guerre sans autorisation du Parlement (35 al.1) au-delà de quatre mois",
                    "toute hausse durable de l'effort suppose une loi de programmation (34 al.9) votée, "
                    "donc une majorité",
                    "un conflit de compétence avec l'Europe (PESCO, article 42 TUE) est borné par les "
                    "articles 88-1 à 88-4"],
       contre=["Parlement (35, 34, 47 pour les crédits)",
               "Conseil constitutionnel sur la loi organique et la programmation",
               "opinion et marchés : sanction politique, non juridique (chaîne de ricochet analysée par le "
               "moteur géopolitique du dépôt)"],
       croise=["21", "34", "35", "36", "47", "52", "88-1"],
       strates=["National", "Europe", "Mondial"],
       mecanismes=("engagement_militaire", "loi_programmation_militaire"),
       leviers=("effort_defense_pct_pib", "montee_capacite_defense")),
    _a("16", "Pouvoirs exceptionnels",
       "II", "organisation", "Président de la République, après consultations officielles",
       "Quand les institutions, l'indépendance, l'intégrité du territoire ou l'exécution des engagements "
       "internationaux sont menacés « d'une manière grave et immédiate » et que « le fonctionnement régulier "
       "des pouvoirs publics constitutionnels est interrompu », le Président prend les mesures exigées, après "
       "consultation officielle du Premier ministre, des présidents d'assemblées et du Conseil constitutionnel. "
       "Message à la Nation. Le Parlement se réunit de plein droit, l'Assemblée nationale ne peut être "
       "dissoute. Après 30 jours, saisine possible du Conseil ; au-delà de 60 jours, examen de plein droit.",
       regles=["conditions cumulatives du 1er alinéa (menace grave et immédiate + interruption du "
               "fonctionnement régulier)",
               "consultations obligatoires : Premier ministre, présidents des deux assemblées, Conseil "
               "constitutionnel",
               "examen par le Conseil : à 30 jours sur saisine ( Président de l'AN, du Sénat, 60 députés "
               "ou 60 sénateurs), de plein droit à 60 jours puis à tout moment",
               "aucune dissolution pendant toute la durée (16 al.4)"],
       opportunites=["gouverner par mesures réglementaires en cas de paralysie institutionnelle avérée, "
                     "sans coup d'État juridique : tout reste encadré et public (avis du Conseil)",
                     "neutralise l'arme de la censure (49) en rendant la session permanente : le Parlement "
                     "réuni de plein droit garde son droit de regard"],
       contraintes=["les mesures doivent « assurer aux pouvoirs publics constitutionnels, dans les moindres "
                    "délais, les moyens d'accomplir leur mission » : pas de réforme structurelle par 16",
                    "pas de loi : l'article 16 produit des mesures, pas un texte définitif — l'après-16 "
                    "implique de tout faire confirmer par le législateur",
                    "un seul usage : 23 avril-29 septembre 1961 (de Gaulle, putsch d'Algiers)"],
       contre=["Conseil constitutionnel (avis publics, examen de plein droit)",
               "Parlement (réunion de plein droit, 120 jours de séance non applicables)",
               "le Conseil d'État, juge de la légalité des actes pris sur le fondement du 16 (jurisprudence "
               "Camino, 1962 : contrôle réduit mais réel)"],
       croise=["5", "12", "28", "29", "51", "61"],
       strates=["National", "Europe", "Mondial"],
       mecanismes=("pouvoirs_exceptionnels",),
       leviers=("usage_article_16",)),
    _a("17", "Droit de grâce à titre individuel",
       "II", "organisation", "Président de la République",
       "« Le Président de la République a le droit de faire grâce à titre individuel. » Le droit de grâce "
       "collective (loi d'amnistie) relève de la loi (34 al.1, 4ᵉ §).",
       regles=["droit de grâce individuel ; l'amnistie, elle, relève de la loi (34)",
               "la grâce ne figure pas sur la liste des actes sans contreseing de l'article 19 (8 al.1, 11, "
               "12, 16, 18, 54, 56, 61) : elle est donc contresignée par le Premier ministre",
               "instruction par la direction des affaires criminelles et des grâces, avis du juge de "
               "l'application des peines (art. 167 du code de procédure pénale)"],
       opportunites=["correction individuelle d'une rigueur de justice (grâces présidentielles du 14 juillet)",
                     "outil symbolique de pacification sociale, sans toucher à la règle de droit"],
       contraintes=["ne peut pas effacer une peine d'inéligibilité prononcée par le juge administratif ou "
                    "judiciaire de façon à rétablir un candidat (jurisprudence)",
                    "aucune grâce « générale » : ce serait une loi d'amnistie (34)"],
       contre=["Cour de cassation et juridictions d'application des peines pour les effets concrets",
               "l'opinion publique et le Parlement (motion 50-1) pour le coût politique"],
       croise=["19", "34"],
       mecanismes=("droit_de_grace",)),
    _a("18", "Messages et parole devant le Congrès",
       "II", "exécutif", "Président de la République ; Congrès",
       "Les messages du Président sont lus devant les deux assemblées et « ne donnent lieu à aucun débat ». "
       "Depuis 2008, il « peut prendre la parole devant le Parlement réuni à cet effet en Congrès » ; sa "
       "déclaration peut donner lieu, hors sa présence, à un débat sans vote. Hors session, les assemblées "
       "sont réunies spécialement.",
       regles=["aucun vote possible sur un message ou sur la déclaration devant le Congrès",
               "vote du Congrès réservé à l'article 89 (révision) — l'alinéa final de l'18 interdit le vote",
               "convocation du Congrès : décret du Président (pour 89) ou, pour l'18, usage présidentiel"],
       opportunites=["s'adresser directement au pays via ses représentants, sans contrepartie de "
                     "responsabilité : instrument de cadrage d'un agenda en période de fragmentation",
                     "le débat hors présence du Président permet à chaque groupe de marquer sa position "
                     "sans risque de censure"],
       contraintes=["pas de vote, donc pas de validation démocratique du contenu : l'article 18 ne "
                    "légifère pas",
                    "le Congrès ne peut pas s'auto-saisir pour un vote de confiance"],
       contre=["Chaque assemblée par son règlement (organisation du débat)",
               "l'absence de vote est elle-même le garde-fou : aucun effet juridique ne peut en sortir"],
       croise=["8", "19", "32", "89"],
       mecanismes=("message_congres",)),
    _a("19", "Contreseing du Premier ministre et des ministres responsables",
       "II", "exécutif", "Premier ministre et ministres",
       "« Les actes du Président de la République autres que ceux prévus aux articles 8 (1er alinéa), 11, 12, "
       "16, 18, 54, 56 et 61 sont contresignés par le Premier ministre et, le cas échéant, par les ministres "
       "responsables. » Le contreseing rend l'acte exécutoire et transfère la responsabilité politique au "
       "Gouvernement.",
       regles=["huit exceptions listées (8 al.1, 11, 12, 16, 18, 54, 56, 61) : actes « propres » du Président",
               "un ministre peut être relevé (8 al.2), ce qui rend le contreseing polymorphe"],
       opportunites=["le Premier ministre peut refuser le contreseing, bloquant de fait un acte présidentiel "
                     "non listé (décret, nomination) — c'est l'arme discrète de la cohabitation",
                     "la liste des exceptions définit le domaine réservé sans l'écrire : défense, "
                     "diplomatie, institutions, grâce et référendum"],
       contraintes=["un acte présidentiel non contresigné est entaché d'incompétence (annulation par le "
                    "Conseil d'État)",
                    "le Président ne peut rien promulguer unilatéralement qui ne figure pas dans la liste"],
       contre=["Conseil d'État (recours contre les actes dépourvus de contreseing)",
               "le gouvernement lui-même : une démission collective (8 al.1) rend le contreseing indisponible"],
       croise=["8", "11", "12", "16", "18", "20", "54", "56", "61"],
       mecanismes=("contreseing_refuse",)),
)


# ────────────────────────────────────────────────────────────────────────────
# TITRE III — LE GOUVERNEMENT (articles 20 à 23)
# ────────────────────────────────────────────────────────────────────────────

_TITRE_III: tuple[ArticleConstitution, ...] = (
    _a("20", "Le Gouvernement détermine et conduit la politique de la Nation ; responsabilité devant le Parlement",
       "III", "exécutif", "Gouvernement",
       "« Le Gouvernement détermine et conduit la politique de la nation. Il dispose de l'administration et "
       "de la force armée. Il est responsable devant le Parlement dans les conditions et suivant les "
       "procédures prévues aux articles 49 et 50. »",
       regles=["la responsabilité est nationale (49), non sénatoriale : le Sénat ne peut censurer",
               "la « détermination » de la politique suppose la délibération en conseil des ministres (9)"],
       opportunites=["le gouvernement peut engager sa responsabilité pour faire adopter sans vote (49.3)",
                     "il fixe l'ordre du jour prioritaire (48) : la maîtrise du calendrier est le premier "
                     "des pouvoirs",
                     "il peut demander au Sénat l'approbation d'une déclaration de politique générale (49 al.4), "
                     "retournant la chambre haute en appui"],
       contraintes=["trois motions de censure maximum par session ordinaire (49 al.2) : l'opposition a un "
                    "quota, le gouvernement a une marge",
                    "toute politique conduite sans majorité relative est exposée, non invalidée : le texte "
                    "ne prévoit pas de démission automatique hors vote (50)"],
       contre=["Assemblée nationale (49.2, 49.3, 50)", "Sénat (vote consultatif, commission d'enquête 51-2)",
               "Conseil constitutionnel (61) et Cour de justice de la République (68-1 à 68-3)"],
       croise=["8", "9", "21", "22", "23", "37", "38", "48", "49", "50", "68-1"],
       mecanismes=("engagement_responsabilite", "motion_censure", "declaration_politique_generale"),
       leviers=("usage_49_3", "usage_motion_censure")),
    _a("21", "Le Premier ministre dirige l'action du Gouvernement, exerce le pouvoir réglementaire",
       "III", "exécutif", "Premier ministre",
       "Le Premier ministre dirige l'action du Gouvernement, est responsable de la défense nationale, "
       "assure l'exécution des lois, exerce le pouvoir réglementaire (sous réserve de l'article 13) et nomme "
       "aux emplois civils et militaires. Il peut déléguer, suppléer le Président dans les conseils (15) et, "
       "à titre exceptionnel, présider un conseil des ministres par délégation expresse et ordre du jour "
       "déterminé.",
       regles=["deux domaines de règlement : règlement autonome (37) et décrets d'application des lois",
               "le pouvoir réglementaire est « sous réserve de l'article 13 » : pas d'empiétement sur les "
               "nominations en conseil"],
       opportunites=["l'arme réglementaire = application ou non-application d'une loi votée : le délai des "
                     "décrets est la variable cachée de toute réforme",
                     "la voie réglementaire permet de réformer sans vote (37 : tout ce qui n'est pas la loi "
                     "est réglementaire) — le gouvernement peut donc légiférer par décret dans une marge "
                     "large, contrôlée par le Conseil d'État",
                     "les ordonnances (38) multiplient cette capacité si le Parlement habilité"],
       contraintes=["un décret contraire à la loi est annulé (Conseil d'État)",
                    "les matières de l'article 34 ne sont pas réglementables",
                    "l'engagement de la responsabilité devant l'Assemblée (49) lui est personnel : il ne "
                    "peut déléguer le 49.3"],
       contre=["Conseil d'État (annulation pour excès de pouvoir)", "Parlement (41 : irrecevabilité de "
               "tout empiétement réglementaire ; 37 al.2 : défossilisation par décret)",
               "les assemblées locales et chambres consulaires via l'impact territorial (moteur Local du dépôt)"],
       croise=["13", "19", "20", "22", "34", "37", "38", "41"],
       mecanismes=("pouvoir_reglementaire", "ordonnances"),
       leviers=("gouvernance_voie_reglementaire",)),
    _a("22", "Contreseing ministériel et délégation",
       "III", "organisation", "Ministres",
       "« Les actes du Premier ministre sont contresignés, le cas échéant, par les ministres chargés de leur "
       "exécution. » L'article 23 complète : les ministres sont responsables de leur département et peuvent "
       "recevoir délégation.",
       regles=["contreseing conditionnel (« le cas échéant ») : dépend du champ de compétence",
               "pas de délai écrit, donc pas de forclusion ministérielle"],
       opportunites=["un ministre qui refuse son contreseing signale un désaccord public et peut bloquer un "
                     "texte d'application (décret)",
                     "la délégation de signature accélère la mise en œuvre d'une réforme (préfets, directeurs)"],
       contraintes=["le refus de contreseing n'a pas d'effet juridique sur l'acte de l'autorité "
                    "investie : c'est un signal politique, sanctionné par le limogeage (8 al.2)",
                    "pas de responsabilité collégiale automatique : chaque acte renvoie à son ministre"],
       contre=["le Président (8 al.2 : fin des fonctions d'un ministre)", "l'Assemblée (motion individuelle "
               "50-1, commission d'enquête 51-2, CJR 68-1)"],
       croise=["8", "9", "19", "21", "23"],
       mecanismes=("remaniement",)),
    _a("23", "Incompatibilités des fonctions ministérielles",
       "III", "organisation", "Gouvernement, loi organique",
       "« Les fonctions de membre du Gouvernement sont incompatibles avec l'exercice de tout mandat "
       "parlementaire, de toute fonction de représentation professionnelle à caractère national et de tout "
       "emploi public ou de toute activité professionnelle. » Une loi organique fixe les conditions de "
       "remplacement ; le remplacement des parlementaires suit l'article 25.",
       regles=["incompatibilité immédiate : entrer au gouvernement = sortir du Parlement (le suppléant "
               "reprend le siège, ou l'élection partiale a lieu selon la loi organique de 1958 modifiée)",
               "l'acceptation d'un portefeuille met fin au mandat parlementaire : le suppléant est installé, "
               "et le retour du ministre dans l'hémicycle suppose de se représenter"],
       opportunites=["en cas de gouvernement minoritaire, nommer des ministres non parlementaires évite de "
                     "retirer des sièges à la majorité (effet inverse d'une « ouverture »)",
                     "la loi organique peut prévoir le remplacement temporaire : une « parenthèse "
                     "gouvernementale » sans perte de mandat est techniquement possible"],
       contraintes=["interdit de cumuler portefeuille et mandat local ou national : le lien territoire-"
                    "gouvernement doit passer par des délégations, non par un cumul",
                    "interdit toute activité professionnelle : les allers-retours avec le privé tombent sous "
                    "le contrôle de la HATVP et du code pénal (pantouflage)"],
       contre=["Conseil constitutionnel : éligibilité et inéligibilité (rôle de juge des élections via 59)",
               "HATVP, déontologie (lois du 11 octobre 2013, 14 septembre 2018 ; art. 432-13 du code pénal)"],
       croise=["8", "25", "59", "68-1"],
       mecanismes=("cumul_mandats", "remaniement"),
       leviers=("reforme_non_cumul", "reforme_anti_pantouflage")),
)


# ────────────────────────────────────────────────────────────────────────────
# TITRE IV — LE PARLEMENT (articles 24 à 33)
# ────────────────────────────────────────────────────────────────────────────

_TITRE_IV: tuple[ArticleConstitution, ...] = (
    _a("24", "Le Parlement vote la loi, contrôle, évalue ; Assemblée nationale et Sénat",
       "IV", "législatif", "Parlement (577 députés, 348 sénateurs au maximum)",
       "« Le Parlement vote la loi. Il contrôle l'action du Gouvernement. Il évalue les politiques "
       "publiques. » L'Assemblée nationale est élue au suffrage direct (577 maximum) ; le Sénat au suffrage "
       "indirect (348 maximum) et il « assure la représentation des collectivités territoriales de la "
       "République ». Les Français établis hors de France sont représentés dans les deux assemblées.",
       regles=["577 députés maximum, 348 sénateurs maximum (plafonds constitutionnels depuis 2008)",
               "sénateurs : mandat de 6 ans, renouvellement par moitié tous les 3 ans",
               "majorité absolue à l'AN = 289 voix sur 577 ; au Sénat = 175 sur 348",
               "seuil de constitution d'un groupe : 15 députés, 10 sénateurs (règlements)",
               "11 députés et 9 sénateurs représentent les Français de l'étranger"],
       opportunites=["la mission « évaluation des politiques publiques » (ajoutée en 2008) autorise des "
                     "rapports, des audits et des commissions d'enquête sans toucher au budget",
                     "le Sénat, représentant des collectivités, peut imposer son texte sur une réforme "
                     "territoriale avant l'AN (39 al.2 + 45)",
                     "en cas de dissolution, le Sénat reste en séance : la continuité législative passe par "
                     "lui pendant les 20 à 40 jours de campagne"],
       contraintes=["aucune des deux chambres n'a le dernier mot hors les cas de l'article 45",
                    "le nombre de sièges, les indemnités et le régime électoral relèvent de la loi "
                    "organique (25) : pas de réglage par simple loi",
                    "pas de délégation de vote au-delà d'un mandat (27)"],
       contre=["Conseil constitutionnel : juge des élections (59) et des règlements (61)",
               "Gouvernement (48 : ordre du jour prioritaire ; 45 : CMP et dernier mot ; 49.3)",
               "corps électoral (12 : dissolution ; renouvellement sénatorial partiel)"],
       croise=["25", "26", "27", "28", "32", "33", "45", "48", "49", "51-1", "51-2"],
       strates=["National", "Local", "Transversal"],
       mecanismes=("vote_definitif", "commission_mixte_paritaire", "evaluation_politiques_publiques"),
       leviers=("sieges_assemblee", "mode_scrutin_legislatives")),
    _a("25", "Loi organique sur les mandats ; commission indépendante pour le découpage",
       "IV", "organisation", "Législateur organique ; commission indépendante",
       "La loi organique fixe la durée des pouvoirs de chaque assemblée, le nombre de ses membres, leur "
       "indemnité, les conditions d'éligibilité, le régime des inéligibilités et des incompatibilités, ainsi "
       "que le remplacement en cas de vacance. Une commission indépendante, dont la loi fixe la composition, "
       "se prononce par un avis public sur les projets et propositions délimitant les circonscriptions "
       "législatives ou modifiant la répartition des sièges.",
       regles=["avis public obligatoire de la commission indépendante (instaurée par la révision de 2008)",
               "loi organique : saisine obligatoire du Conseil constitutionnel avant promulgation (46 al.5, 61)",
               "remplacement d'un siège vacant : scrutin partiel dans les 3 mois (loi organique de 1958 "
               "modifiée en 2021 : suppression de l'inéligibilité aux partielles pour les ministres sortants)"],
       opportunites=["durcir les conditions d'éligibilité (casier B2, déclaration de patrimoine, "
                     "limitation dans le temps) sans réviser la Constitution : tout est en loi organique",
                     "réformer l'indemnité pour conditionner le cumul de ressources ou la présence en séance",
                     "le contrôle public du découpage permet de chiffrer la déformation relative d'un "
                     "mode de scrutin dans le simulateur"],
       contraintes=["impossible de modifier le nombre de sièges par simple loi",
                    "toute inéligibilité nouvelle doit respecter la proportionnalité des peines et la "
                    "liberté du suffrage (jurisprudence constante du Conseil)",
                    "l'avis de la commission n'est pas conforme : le législateur peut s'en écarter, "
                    "au risque d'une censure"],
       contre=["Conseil constitutionnel (61)", "commission indépendante (avis public)",
               "électeurs (59 : contestation d'élection)"],
       croise=["3", "24", "27", "34", "46", "59", "61"],
       mecanismes=("red_ecoupage", "exigibilite_elus", "remplacement_siege"),
       leviers=("reforme_casier_b2", "reforme_non_cumul", "reforme_proportionnelle")),
    _a("26", "Irresponsabilité et inviolabilité parlementaire",
       "IV", "organisation", "Bureau de chaque assemblée",
       "Aucun membre du Parlement ne peut être poursuivi, recherché, arrêté, détenu ou jugé à l'occasion des "
       "opinions ou votes émis dans l'exercice de ses fonctions (immunité d'opinion, absolue). En matière "
       "criminelle ou correctionnelle, une arrestation ou toute mesure privative ou restrictive de liberté "
       "requiert l'autorisation du bureau de l'assemblée — sauf crime ou délit flagrant ou condamnation "
       "définitive. La détention, les mesures restrictives ou la poursuite sont suspendues pour la durée de la "
       "session si l'assemblée le requiert ; elle est alors réunie de plein droit pour des séances supplémentaires.",
       regles=["flagrant délit ou condamnation définitive = aucune autorisation requise",
               "demande de suspension : vote de l'assemblée (majorité des membres présents en pratique)",
               "levée d'immunité : décision du bureau, dont la composition est proportionnelle aux groupes"],
       opportunites=["l'immunité protège la parole critique en commission d'enquête (51-2) : elle est un "
                     "garde-fou du contre-pouvoir parlementaire",
                     "la demande de suspension des poursuites permet à une assemblée de ne pas être vidée "
                     "d'une partie de ses voix en cours de mandature"],
       contraintes=["ne couvre pas les propos tenus hors de l'hémicycle ou hors du mandat (réseaux sociaux, "
                    "presse) : les levées d'immunité de 2025 en témoignent",
                    "n'empêche ni une condamnation définitive ni l'inéligibilité qui en résulte",
                    "ne protège ni le chef de l'État (67) ni les ministres (68-1)"],
       contre=["l'autorité judiciaire (flagrant délit, condamnation définitive)", "le bureau de l'assemblée",
               "les électeurs (59)"],
       croise=["24", "31", "33", "51-2", "59", "67", "68", "68-1"],
       mecanismes=("levee_immunite",)),
    _a("27", "Interdiction du mandat impératif ; vote personnel",
       "IV", "souveraineté", "Parlementaires",
       "« Tout mandat impératif est nul. Le droit de vote des membres du Parlement est personnel. » La loi "
       "organique peut autoriser exceptionnellement la délégation de vote ; nul ne peut recevoir délégation "
       "de plus d'un mandat.",
       regles=["une seule délégation de vote possible, dans les cas prévus par la loi organique",
               "les consignes de parti n'ont aucun effet juridique opposable au vote"],
       opportunites=["fonde la dissidence constructive : voter la censure contre l'avis de son groupe est "
                     "juridiquement licite — c'est ce paramètre (indiscipline) qui détermine l'issue réelle "
                     "d'un scrutin de censure",
                     "rend nul tout engagement écrit de « pacte de législature » : utile pour évaluer la "
                     "solidité d'une coalition dans le modèle"],
       contraintes=["interdit la révocation populaire d'un parlementaire en droit constitutionnel actuel : "
                    "elle supposerait une révision des articles 3, 24, 25 et 27",
                    "interdit un mandat « impératif » porté par un RIC local sur des voteurs nationaux"],
       contre=["Conseil constitutionnel (59 : sincérité du suffrage)", "les instances des partis "
               "(sanction politique seulement)"],
       croise=["3", "11", "24", "25", "49", "72-1", "89"],
       strates=["National", "Local"],
       mecanismes=("revocation_mandat", "discipline_parlementaire"),
       leviers=("reforme_ric", "reforme_revocation_elus")),
    _a("28", "Session ordinaire d'octobre à juin ; cent vingt jours de séance",
       "IV", "organisation", "Chaque assemblée ; Gouvernement ou majorité d'assemblée",
       "Le Parlement se réunit de plein droit en session ordinaire qui commence le premier jour ouvrable "
       "d'octobre et prend fin le dernier jour ouvrable de juin. Le nombre de jours de séance par assemblée "
       "ne peut excéder cent vingt. Le Premier ministre, après consultation du président de l'assemblée "
       "concernée, ou la majorité des membres de chaque assemblée peut décider la tenue de jours "
       "supplémentaires. Jours et horaires sont fixés par le règlement.",
       regles=["session : 1er jour ouvrable d'octobre → dernier jour ouvrable de juin",
               "120 jours de séance maximum par assemblée et par session",
               "prolongation décidée par le Gouvernement ou par la majorité des membres de l'assemblée"],
       opportunites=["le calendrier connu permet d'anticiper les dates butoirs (budget : 47 et 47-1)",
                     "une assemblée peut décider seule des jours supplémentaires si une majorité se forme : "
                     "contre-pouvoir temporel",
                     "la session 2026-2027 s'est ouverte le 1er octobre 2026 mais s'achèvera fin février "
                     "2027 pour laisser place à la campagne présidentielle : donnée réelle de calendrier "
                     "législatif"],
       contraintes=["hors session, le Parlement ne se réunit que dans les cas prévus (12, 16, 29, 33, 89)",
                    "modifier la durée ou le rythme suppose une loi organique"],
       contre=["le Gouvernement (29 : session extraordinaire à sa demande)", "la majorité de chaque assemblée",
               "Conseil constitutionnel (61) sur les lois organiques de calendrier"],
       croise=["12", "16", "29", "30", "33", "48", "51", "89"],
       mecanismes=("session_extraordinaire", "calendrier_legislatif"),
       leviers=("rythme_parlementaire",)),
    _a("29", "Session extraordinaire : à la demande du Premier ministre ou de la majorité de l'AN",
       "IV", "organisation", "Premier ministre ; majorité absolue des députés",
       "Le Parlement est réuni en session extraordinaire à la demande du Premier ministre ou de la majorité "
       "des membres composant l'Assemblée nationale, sur un ordre du jour déterminé. Lorsque la session est "
       "tenue à la demande des députés, le décret de clôture intervient dès que l'ordre du jour est épuisé "
       "et au plus tard douze jours après la réunion. Le Premier ministre peut seul demander une nouvelle "
       "session avant l'expiration du mois suivant le décret de clôture.",
       regles=["initiative réservée : Premier ministre ou majorité absolue de l'AN (289 députés)",
               "12 jours au plus quand l'initiative vient des députés",
               "un mois de carence avant une nouvelle session demandée par le Premier ministre"],
       opportunites=["une majorité de blocage peut imposer un débat hors session (ratification, loi de "
                     "crise, révision 89) si elle atteint 289 voix",
                     "la brièveté imposée rend la session extraordinaire compatible avec une gestion de crise"],
       contraintes=["aucune demande citoyenne possible : le peuple ne peut pas convoquer le Parlement",
                    "ordre du jour déterminé obligatoire : pas de session « de débat libre »",
                    "la demande doit être régulière et vérifiée (usage : notification aux présidents d'assemblée)"],
       contre=["les présidents d'assemblée (vérification de la demande)",
               "le Gouvernement (décret de clôture, 30)"],
       croise=["28", "30", "51", "89"],
       mecanismes=("session_extraordinaire",)),
    _a("30", "Ouverture et clôture des sessions extraordinaires par décret",
       "IV", "organisation", "Président de la République",
       "« Hors les cas dans lesquels le Parlement se réunit de plein droit, les sessions extraordinaires "
       "sont ouvertes et closes par décret du Président de la République. »",
       regles=["décret signé en conseil des ministres (9, 13)",
               "réunions de plein droit : 12 (après dissolution), 16 (pouvoirs exceptionnels), 28 (session "
               "ordinaire), 33 al.3 (séances pour l'application du 26), 89 (Congrès)"],
       opportunites=["la formalisation par décret date la session : le calendrier devient opposable et "
                     "simulable (coût d'incertitude pour les marchés)"],
       contraintes=["pas de session sans ordre du jour déterminé (29)",
                    "le Gouvernement ne peut pas forcer une session hors session ordinaire sans signature "
                    "présidentielle"],
       contre=["Conseil d'État (légalité du décret)"],
       croise=["12", "16", "28", "29", "33", "89"],
       mecanismes=("session_extraordinaire",)),
    _a("31", "Accès des ministres aux deux assemblées ; commissaires du Gouvernement",
       "IV", "organisation", "Membres du Gouvernement",
       "« Les membres du Gouvernement ont accès aux deux assemblées. Ils sont entendus quand ils le "
       "demandent. Ils peuvent se faire assister par des commissaires du Gouvernement. »",
       regles=["droit d'accès permanent, sans inscription à l'ordre du jour",
               "l'article 48 réserve au moins une séance par semaine aux questions et réponses"],
       opportunites=["la négociation en direct pendant la séance remplace souvent la CMP : c'est le "
                     "levier des gouvernements sans majorité absolue",
                     "les commissaires du Gouvernement portent la technique sans exposer politiquement le "
                     "ministre"],
       contraintes=["un ministre ne vote pas (23 : incompatibilité avec tout mandat parlementaire)",
                    "la police des séances appartient au président de l'assemblée"],
       contre=["les présidents d'assemblée (police des séances)", "les groupes (51-1 : temps de parole, "
               "questions)"],
       croise=["23", "33", "45", "48", "49", "51-1"],
       mecanismes=("questions_gouvernement",)),
    _a("32", "Présidents d'assemblée : législature pour l'AN, trois ans pour le Sénat",
       "IV", "organisation", "Chaque assemblée (scrutin public, à bulletin secret)",
       "« Le président de l'Assemblée nationale est élu pour la durée de la législature. Le président du "
       "Sénat est élu après chaque renouvellement partiel. »",
       regles=["AN : mandat = durée de la législature ; Sénat : réélection après chaque renouvellement "
               "partiel (le 1er octobre 2026, Gérard Larcher a été réélu après le renouvellement du "
               "27 septembre 2026)",
               "majorité absolue au premier tour, relative aux tours suivants (règlements)"],
       opportunites=["la présidence de l'AN concentre des pouvoirs procéduraux décisifs : ordre du jour en "
                     "Conférence des présidents (48), irrecevabilité (40, 41, 44), saisine du Conseil (61), "
                     "présidence de la Haute Cour (68)",
                     "la présidence du Sénat donne l'intérim présidentiel (7) et une saisine propre du "
                     "Conseil constitutionnel : une chambre peut donc armer juridiquement l'obstruction"],
       contraintes=["le président de l'AN ne peut ni dissoudre ni renverser un gouvernement",
                    "un changement de majorité en cours de législature ne renouvelle pas le perchoir : "
                    "la reconfiguration suppose une démission volontaire (aucune motion de défiance "
                    "constitutionnelle prévue)"],
       contre=["les groupes (via le règlement et le bureau)", "Conseil constitutionnel (61 al.1 : règlement)"],
       croise=["7", "12", "28", "48", "61", "68"],
       mecanismes=("presidence_assemblees", "saisine_conseil"),
       leviers=("gouvernance_presidences",)),
    _a("33", "Publicité des séances ; comité secret",
       "IV", "contrôle & évaluation", "Chaque assemblée",
       "« Les séances des deux assemblées sont publiques. Le compte rendu intégral des débats est publié au "
       "Journal officiel. » Chaque assemblée peut siéger en comité secret à la demande du Premier ministre ou "
       "d'un dixième de ses membres.",
       regles=["1/10 des membres = 58 députés ou 35 sénateurs pour demander le huis clos",
               "compte rendu intégral publié au JO (base des votes nominatifs)"],
       opportunites=["la publicité est le fondement de tout contrôle citoyen : retransmission, votes "
                     "nominatifs, données ouvertes des scrutins (la base de données du dépôt s'en nourrit)",
                     "le scrutin public solennel obligatoire sur certaines questions (49, 89, motions) "
                     "permet de reproduire un vote nominal exact dans le modèle"],
       contraintes=["le huis clos est possible à la demande d'un dixième : la transparence n'est pas "
                    "acquise de droit",
                    "le compte rendu n'est pas une obligation de retransmission audiovisuelle : cela "
                    "relève des règlements"],
       contre=["les groupes d'opposition (51-1)", "Conseil constitutionnel (61 al.1 sur les règlements)"],
       croise=["24", "26", "31", "48", "51-1", "51-2"],
       mecanismes=("transparence_seances",),
       leviers=("transparence_votes",)),
)


# ────────────────────────────────────────────────────────────────────────────
# TITRE V — RAPPORTS PARLEMENT / GOUVERNEMENT (articles 34 à 51-2)
# ────────────────────────────────────────────────────────────────────────────

_TITRE_V: tuple[ArticleConstitution, ...] = (
    _a("34", "Domaine de la loi (IVG ajoutée par la révision du 8 mars 2024)",
       "V", "procédure législative", "Parlement",
       "La loi fixe les règles concernant les droits civiques et les garanties fondamentales des citoyens "
       "(dont la liberté, le pluralisme et l'indépendance des médias), la nationalité, l'état et la capacité "
       "des personnes, les régimes matrimoniaux, les successions et libéralités, la détermination des crimes "
       "et délits et des peines, la procédure pénale, l'amnistie, la création de nouveaux ordres de "
       "juridiction et le statut des magistrats, l'assiette, le taux et les modalités de recouvrement des "
       "impositions, le régime d'émission de la monnaie, le régime électoral, la création de catégories "
       "d'établissements publics, les garanties des fonctionnaires, les nationalisations et privatisations. "
       "Elle détermine les principes fondamentaux de l'organisation générale de la défense, de la libre "
       "administration des collectivités, de l'enseignement, de la préservation de l'environnement, du "
       "régime de la propriété, du droit du travail, du droit syndical et de la sécurité sociale. Depuis le "
       "8 mars 2024 : « La loi détermine les conditions dans lesquelles s'exerce la liberté garantie à la "
       "femme d'avoir recours à une interruption volontaire de grossesse. » Les lois de finances, les lois "
       "de financement de la sécurité sociale et les lois de programmation — dont les orientations "
       "pluriannuelles des finances publiques, qui « s'inscrivent dans l'objectif d'équilibre des comptes des "
       "administrations publiques » — sont rattachées au même article.",
       regles=["une trentaine de matières réservées au domaine de la loi",
               "lois de programmation = objectifs, pas de droits opposables (jurisprudence constante)",
               "les orientations pluriannuelles des finances publiques doivent être fixées par loi de "
               "programmation (LOLF + loi organique de 2012)",
               "précisions et compléments possibles par loi organique (dernier alinéa)"],
       opportunites=["toute réforme fiscale, sociale ou environnementale est législative : c'est le "
                     "bouclier contre un démantèlement par simple décret",
                     "la liste étant limitative, tout le reste est réglementaire (37) : un gouvernement "
                     "peut réformer vite dans la marge résiduelle",
                     "les lois de programmation verrouillent une trajectoire pluriannuelle (défense, "
                     "climat, finances publiques) : outil de crédibilisation vis-à-vis des marchés",
                     "l'alinéa IVG montre la technique du « verrouillage par renvoi » : constitutionnaliser "
                     "un principe sans en figer le contenu"],
       contraintes=["un amendement qui aggrave une charge publique ou diminue une recette est irrecevable (40)",
                    "une disposition législative hors domaine peut être modifiée par décret (37 al.2, 41)",
                    "le Parlement ne peut ni s'auto-saisir du pouvoir réglementaire ni adresser d'injonction "
                    "au Gouvernement (34-1)"],
       contre=["Gouvernement (41 : irrecevabilité ; 44 al.3 : vote bloqué ; 45 : CMP, dernier mot ; 38 : "
               "ordonnances)", "Conseil constitutionnel (61 et 61-1 : incompétence négative et droits "
               "constitutionnels)", "collectivités territoriales (72 : pouvoir réglementaire propre)"],
       strates=["National", "Local", "Europe", "Transversal"],
       croise=["37", "38", "40", "41", "45", "46", "47", "47-1", "72", "72-2", "73"],
       mecanismes=("domaine_loi_reglement", "loi_programmation", "defossilisation"),
       leviers=("efficacite_legislative", "verrouillage_par_loi_programmation")),
    _a("34-1", "Résolutions des assemblées ; irrecevabilité des injonctions",
       "V", "contrôle & évaluation", "Chaque assemblée ; Gouvernement",
       "« Les assemblées peuvent voter des résolutions dans les conditions fixées par la loi organique. "
       "Sont irrecevables et ne peuvent être inscrites à l'ordre du jour les propositions de résolution dont "
       "le Gouvernement estime que leur adoption ou leur rejet serait de nature à mettre en cause sa "
       "responsabilité ou qu'elles contiennent des injonctions à son égard. »",
       regles=["résolutions non contraignantes", "irrecevabilité appréciée par le Gouvernement puis par le "
               "président d'assemblée", "voies de la responsabilité fermées hors 49 et 50"],
       opportunites=["arme de cadrage politique pour une assemblée sans majorité : résolution d'orientation, "
                     "résolution européenne (88-4), résolution de subsidiarité (88-6)",
                     "formaliser une demande sociale sans renverser le gouvernement : soupape du régime"],
       contraintes=["interdiction d'injonction au Gouvernement", "aucun effet juridique sur les tiers",
                    "le Gouvernement peut faire tomber la résolution en la jugeant attentatoire à sa "
                    "responsabilité"],
       contre=["le Gouvernement (irrecevabilité)", "la Conférence des présidents (inscription)"],
       croise=["34", "49", "50", "88-4", "88-6"],
       mecanismes=("resolution_assemblee",)),
    _a("35", "Déclaration de guerre ; interventions armées à l'étranger",
       "V", "exécutif", "Parlement ; Gouvernement",
       "« La déclaration de guerre est autorisée par le Parlement. » Le Gouvernement informe le Parlement de "
       "sa décision de faire intervenir les forces armées à l'étranger au plus tard trois jours après le début "
       "de l'intervention, en précisant les objectifs ; cette information peut donner lieu à un débat sans "
       "vote. Lorsque la durée de l'intervention excède quatre mois, le Gouvernement soumet sa prolongation à "
       "l'autorisation du Parlement, et peut demander à l'Assemblée nationale de décider en dernier ressort. "
       "Si le Parlement n'est pas en session à l'expiration des quatre mois, il se prononce à l'ouverture de "
       "la session suivante.",
       regles=["information sous 3 jours", "autorisation de prolongation au-delà de 4 mois",
               "priorité d'inscription (48 al.3)", "l'AN peut trancher en dernier ressort",
               "à défaut de session : report à l'ouverture de la session suivante"],
       opportunites=["le débat sans vote responsabilise sans risque de censure : configuration d'un "
                     "gouvernement minoritaire en période de tensions extérieures",
                     "l'autorisation de prolongation est un véritable contre-pouvoir de guerre, exercé à "
                     "plusieurs reprises (2011, 2013, 2015, 2018)",
                     "la clause de dernier ressort évite un blocage sénatorial sur l'engagement extérieur"],
       contraintes=["aucun engagement durable sans autorisation : le Gouvernement ne peut dépasser quatre "
                    "mois unilatéralement",
                    "la déclaration de guerre elle-même suppose une autorisation préalable (jamais utilisée "
                    "sous la Vᵉ République)",
                    "une autorisation refusée ne peut pas être contournée par un nouvel engagement segmenté "
                    "(règle de continuité de l'intervention)"],
       contre=["Parlement (autorisation, rejet)", "Conseil constitutionnel (61 sur la loi d'autorisation)",
               "opinion publique (sanction électorale)"],
       strates=["National", "Europe", "Mondial"],
       croise=["15", "21", "34", "48", "52", "53", "55", "88-1"],
       mecanismes=("engagement_militaire", "prolongation_opex"),
       leviers=("engagement_exterieur_mois",)),
    _a("36", "État de siège",
       "V", "organisation", "Conseil des ministres ; Parlement",
       "« L'état de siège est décrété en Conseil des ministres. Sa prorogation au-delà de douze jours ne "
       "peut être autorisée que par le Parlement. »",
       regles=["12 jours sans autorisation parlementaire", "décret en conseil des ministres (9, 13)",
               "transfert des pouvoirs de police à l'autorité militaire (code de la défense)"],
       opportunites=["rétablissement de l'ordre sans suspension de la Constitution : alternative graduée à "
                     "l'article 16",
                     "le débat de prorogation oblige à un diagnostic public de la crise"],
       contraintes=["régime jamais appliqué depuis 1958 (l'état d'urgence, lui, l'a été à de nombreuses "
                    "reprises)", "mesures disproportionnées pour une crise non militaire",
                    "la prorogation suppose un vote : un Gouvernement minoritaire peut la perdre"],
       contre=["Parlement (prorogation)", "Conseil d'État (contrôle adapté des mesures)", "CEDH (art. 15)"],
       croise=["16", "34", "36-1", "66", "66-1"],
       mecanismes=("etat_de_siege", "etat_urgence"),
       leviers=("regime_exception_jours",)),
    _a("36-1", "État d'urgence",
       "V", "organisation", "Conseil des ministres ; loi de prorogation",
       "L'état d'urgence est déclaré en Conseil des ministres, sur tout ou partie du territoire, en cas de "
       "péril imminent résultant d'atteintes graves à l'ordre public ou d'événements présentant le caractère "
       "de calamité publique ; la prorogation au-delà de douze jours est autorisée par la loi, qui en fixe la "
       "durée (dispositions issues de la loi constitutionnelle du 21 juillet 2008).",
       regles=["12 jours par décret, puis loi", "mesures : perquisitions administratives, assignations à "
               "résidence, contrôles d'identité, fermetures d'établissements (loi du 3 avril 1955 modifiée)",
               "le juge administratif exerce un contrôle d'adaptation"],
       opportunites=["régime gradué qui maintient le Parlement au centre, contrairement au 16",
                     "la loi de prorogation peut prévoir des clauses de renvoi (péremption, réexamen)"],
       contraintes=["les mesures ne sont pas des lois : chacune est attaquable",
                    "l'état d'urgence sanitaire a dû être organisé hors du champ de l'article 36-1 par une "
                    "loi ordinaire (loi du 23 mars 2020 ; décision 2020-800 DC du 26 mars 2020)",
                    "la prorogation prolonge un contentieux administratif massif et une contestation politique"],
       contre=["Parlement (vote de prorogation)", "Conseil d'État et juge judiciaire",
               "Conseil constitutionnel (61 sur la loi de prorogation)"],
       croise=["16", "34", "36", "66", "66-1"],
       mecanismes=("etat_urgence",),
       leviers=("regime_exception_jours",)),
    _a("37", "Domaine réglementaire résiduel ; défossilisation",
       "V", "procédure législative", "Gouvernement ; Conseil constitutionnel",
       "« Les matières autres que celles qui sont du domaine de la loi ont un caractère réglementaire. » Les "
       "textes de forme législative intervenues en ces matières avant l'entrée en vigueur de la Constitution "
       "peuvent être modifiés par décrets pris après avis du Conseil d'État ; ceux intervenus après ne le "
       "peuvent que si le Conseil constitutionnel a déclaré leur caractère réglementaire.",
       regles=["défossilisation : décret en Conseil d'État après avis motivé",
               "le Conseil constitutionnel statue en 8 jours sur la demande de l'article 41",
               "la frontière 34/37 est le socle de la compétence réglementaire autonome"],
       opportunites=["réformer sans vote dans le domaine résiduel : levier de rapidité le plus sous-estimé "
                     "de la Constitution",
                     "nettoyer par décret des strates législatives obsolètes (simplification du droit)",
                     "arbitrer le « bon niveau » : une mesure réglementaire ne sera pas amendable par "
                     "l'opposition — mais sera attaquable devant le juge"],
       contraintes=["un décret empiétant sur la loi est annulé (Conseil d'État)",
                    "le Gouvernement ne peut pas s'auto-habiliter : hors 38, la loi reste nécessaire",
                    "la défossilisation des textes postérieurs à 1958 suppose une décision du Conseil "
                    "constitutionnel, donc une procédure longue"],
       contre=["Parlement (41 : irrecevabilité en séance)", "Conseil constitutionnel (arbitre de la "
               "compétence)", "Conseil d'État (annulation des décrets illégaux)"],
       croise=["34", "38", "41", "44", "47-2"],
       mecanismes=("domaine_loi_reglement", "defossilisation"),
       leviers=("gouvernance_voie_reglementaire",)),
    _a("37-1", "Dispositions expérimentales",
       "V", "collectivités", "Législateur ; pouvoir réglementaire",
       "« La loi et le règlement peuvent comporter, pour un objet et une durée limités, des dispositions à "
       "caractère expérimental. » (créé par la loi constitutionnelle du 28 mars 2003)",
       regles=["double limite d'objet et de durée", "évaluation préalable à la pérennisation",
               "interdiction de toucher aux conditions essentielles d'exercice d'une liberté publique "
               "(règle rappelée pour les collectivités, 72 al.4)"],
       opportunites=["voie réaliste pour tester un RIC local, une organisation du travail, un revenu de "
                     "base ou une gouvernance sanitaire sans réviser la Constitution",
                     "produit la preuve par l'exemple que le simulateur peut chiffrer : paramétrer, mesurer, "
                     "généraliser ou abandonner",
                     "neutralise l'objection du « précédent » : l'expérimentation est bornée par hypothèse"],
       contraintes=["à l'échéance, sans texte de pérennisation, la mesure disparaît (effet de sablier)",
                    "le Conseil constitutionnel censure une expérimentation imprécise dans son objet ou sa "
                    "durée (2003-469 DC, 2005-512 DC)",
                    "le droit à l'expérimentation ne crée pas un droit à la généralisation"],
       contre=["Conseil constitutionnel (61)", "Conseil d'État (maintien en vigueur, évaluation)",
               "collectivités (droit de retrait de l'expérimentation)"],
       strates=["Local", "National"],
       croise=["34", "72", "72-1", "72-2", "73"],
       mecanismes=("experimentalisation",),
       leviers=("duree_experimentation_mois", "collectivites_experimentales")),
    _a("38", "Ordonnances",
       "V", "procédure législative", "Gouvernement ; loi d'habilitation",
       "Le Gouvernement peut, pour l'exécution de son programme, demander au Parlement l'autorisation de "
       "prendre par ordonnances, pendant un délai limité, des mesures normalement du domaine de la loi. Les "
       "ordonnances sont prises en Conseil des ministres après avis du Conseil d'État ; elles entrent en "
       "vigueur dès leur publication mais deviennent caduques si le projet de loi de ratification n'est pas "
       "déposé avant la date fixée par la loi d'habilitation ; elles ne peuvent être ratifiées que de manière "
       "expresse. À l'expiration du délai, elles ne peuvent plus être modifiées que par la loi dans les "
       "matières législatives.",
       regles=["délai d'habilitation fixé par la loi (usuellement 3 à 12 mois)",
               "ratification expresse ; défaut de dépôt dans les délais = caducité",
               "avis du Conseil d'État et délibération en conseil des ministres obligatoires",
               "avant ratification, les ordonnances sont attaquables devant le Conseil d'État ; après "
               "ratification, seulement devant le Conseil constitutionnel (jurisprudence constante)"],
       opportunites=["réformer vite sans obstruction permanente tout en restant dans le cadre "
                     "démocratique : l'habilitation est votée",
                     "verrouiller une réforme contre les alternances si elle est ratifiée expressément",
                     "dans un calendrier pré-électoral, c'est l'outil dont les effets survivent à la "
                     "législature : les habilitations de 2017 (droit du travail) et de 2020 (urgence "
                     "sanitaire) en sont les deux usages les plus massifs",
                     "après l'engagement public de renoncement à l'article 49 alinéa 3 pris en 2026, "
                     "l'ordonnance redevient l'alternative de calendrier pour les textes non budgétaires"],
       contraintes=["une habilitation peut être renversée par motion de censure avant l'usage (49.2)",
                    "les ordonnances non ratifiées restent modifiables par décret pour leur partie "
                    "réglementaire, donc précaires",
                    "un amendement contraire à la délégation est irrecevable (41) : l'opposition ne peut "
                    "pas amender le contenu",
                    "l'avis public du Conseil d'État est exigeant : les ordonnances mal préparées sont "
                    "censurées ou rectifiées"],
       contre=["Parlement (vote de l'habilitation, refus de ratification)", "Conseil d'État (contrôle des "
               "ordonnances en vigueur comme actes administratifs)", "Conseil constitutionnel (61 sur la "
               "loi d'habilitation et sur la loi de ratification)"],
       croise=["9", "13", "34", "37", "41", "47", "47-1", "49", "74-1"],
       mecanismes=("ordonnances", "ratification_express", "caducite_ordonnance"),
       leviers=("recours_ordonnances", "usage_49_3")),
    _a("39", "Initiative des lois ; délibération en conseil ; ordre de saisine ; étude d'impact",
       "V", "procédure législative", "Premier ministre, parlementaires, Conseil d'État",
       "L'initiative des lois appartient concurremment au Premier ministre et aux membres du Parlement. Les "
       "projets sont délibérés en Conseil des ministres après avis du Conseil d'État et déposés sur le bureau "
       "de l'une des deux assemblées ; les PLF et PLFSS sont soumis en premier lieu à l'Assemblée nationale ; "
       "les projets ayant pour principal objet l'organisation des collectivités territoriales sont soumis en "
       "premier lieu au Sénat, sans préjudice du premier alinéa de l'article 44. La présentation des projets "
       "répond aux conditions fixées par une loi organique (étude d'impact, coûts, évaluations préalables) ; "
       "la Conférence des présidents peut faire obstacle à l'inscription en cas de méconnaissance, sous "
       "contrôle du Conseil constitutionnel saisi pour 8 jours. Le président d'une assemblée peut soumettre "
       "une proposition de loi pour avis au Conseil d'État, sauf opposition de son auteur.",
       regles=["PLF/PLFSS : Assemblée nationale d'abord", "réforme territoriale : Sénat d'abord",
               "8 jours au Conseil constitutionnel en cas de litige sur la loi organique de présentation",
               "délibération en conseil des ministres = condition de dépôt d'un projet"],
       opportunites=["choisir la chambre de première saisine : instrument tactique réel (le Sénat est "
                     "favorable sur la territorialité, l'AN sur le budgétaire)",
                     "le dépôt d'une proposition de loi, sans étude d'impact obligatoire, est l'arme "
                     "législative de l'opposition — son inscription dépend de l'article 48 (niche)",
                     "l'obligation d'étude d'impact est un garde-fou opposable : elle permet de bloquer un "
                     "projet bâclé ou de le forcer à être sérieux"],
       contraintes=["un projet sans délibération en conseil des ministres est irrégulier",
                    "un projet mal présenté peut être écarté par la Conférence des présidents",
                    "l'initiative parlementaire ne peut rien sur le budget (40 + 39 al.2)"],
       contre=["Conférence des présidents (48) et Conseil constitutionnel (61)", "Conseil d'État (avis, "
               "qualité rédactionnelle)", "Sénat (première saisine territoriale)"],
       croise=["9", "21", "34", "40", "42", "43", "45", "47", "47-1", "48", "72"],
       mecanismes=("choix_assemble_premiere", "qualite_legislative", "deposit_texte"),
       leviers=("qualite_legislative_etude_impact",)),
    _a("40", "Irrecevabilité financière",
       "V", "budget", "Président d'assemblée ; Gouvernement",
       "« Les propositions et amendements formulés par les membres du Parlement ne sont pas recevables "
       "lorsque leur adoption aurait pour conséquence soit une diminution des ressources publiques, soit la "
       "création ou l'aggravation d'une charge publique. »",
       regles=["appréciation en séance par le président de l'assemblée, sur demande du Gouvernement ou d'office",
               "la « technique du gage » (compensation par une recette nouvelle) est admise",
               "aucun recours devant le Conseil constitutionnel contre une irrecevabilité prononcée en séance"],
       opportunites=["pour le Gouvernement : l'arme n° 1 contre les amendements de dépense en navette",
                     "pour l'opposition : le gage et la rédaction en « hausse de recette équivalente » "
                     "permettent de faire aboutir des mesures sociales",
                     "pour le modèle : c'est la contrainte qui explique pourquoi tant de mesures du dossier "
                     "de mandature sont présentées comme « neutres » ou gagées"],
       contraintes=["interdit toute baisse d'impôt ou hausse de dépense d'initiative parlementaire non "
                    "gagée : par exemple la TVA à 5,5 % sur l'énergie doit être portée par un projet de "
                    "loi gouvernemental",
                    "asymétrie démocratique majeure : le Parlement peut voter une taxe, pas la supprimer",
                    "le contournement par sous-amendement est combattu par la pratique des présidents"],
       contre=["le Gouvernement peut accepter un gage (44 al.3 : vote bloqué sur les amendements qu'il "
               "accepte)", "la navette (45) peut rééquilibrer le texte"],
       croise=["34", "39", "44", "45", "47", "47-1", "72-2"],
       strates=["National", "Local", "Transversal"],
       mecanismes=("irrecevabilite_financiere", "gage"),
       leviers=("regle_or_parlementaire", "tva_energie_5_5")),
    _a("41", "Irrecevabilité pour incompétence négative du législateur",
       "V", "procédure législative", "Gouvernement ou président d'assemblée ; Conseil constitutionnel",
       "S'il apparaît au cours de la procédure législative qu'une proposition ou un amendement n'est pas du "
       "domaine de la loi ou est contraire à une délégation accordée en vertu de l'article 38, le "
       "Gouvernement ou le président de l'assemblée saisie peut opposer l'irrecevabilité. En cas de désaccord, "
       "le Conseil constitutionnel, saisi par l'un ou l'autre, statue dans un délai de huit jours.",
       regles=["8 jours pour le Conseil constitutionnel", "opposable à tout moment de la procédure",
               "la loi votée hors domaine peut ensuite être défossilisée (37 al.2)"],
       opportunites=["le président d'assemblée peut résister seul au Gouvernement et saisir le Conseil : "
                     "contre-pouvoir procédural du perchoir",
                     "le Gouvernement peut écarter un amendement qui empiète sur son domaine pour gagner "
                     "du temps de séance"],
       contraintes=["l'opposition ne peut pas contester au fond une irrecevabilité opposée à bon escient",
                    "la frontière 34/37 est parfois ténue : le Conseil constitutionnel arbitre au cas par cas"],
       contre=["Conseil constitutionnel (arbitre)", "Parlement (réécriture dans le domaine de la loi)"],
       croise=["34", "37", "38", "44", "61"],
       mecanismes=("irrecevabilite_competence",)),
    _a("42", "Discussion en séance : texte de la commission ; délais de 6 et 4 semaines",
       "V", "procédure législative", "Commissions ; Conférence des présidents",
       "La discussion en séance porte sur le texte adopté par la commission saisie (ou, à défaut, sur le "
       "texte déposé). Pour les projets de révision constitutionnelle, les PLF et PLFSS, la discussion de "
       "première lecture devant la première assemblée saisie porte sur le texte présenté par le Gouvernement. "
       "En première lecture, la discussion ne peut intervenir devant la première assemblée saisie qu'à "
       "l'expiration d'un délai de six semaines après le dépôt, et devant la seconde qu'à l'expiration de "
       "quatre semaines à compter de la transmission ; ces délais tombent en cas de procédure accélérée et "
       "ne s'appliquent ni aux PLF ni aux PLFSS ni aux projets relatifs aux états de crise.",
       regles=["6 semaines (première assemblée) / 4 semaines (seconde)", "15 jours en procédure accélérée",
               "délais non applicables : PLF, PLFSS, états de crise",
               "projet de révision : discussion sur le texte du Gouvernement (89)"],
       opportunites=["la prime au texte de commission permet un compromis rédactionnel en amont du vote : "
                     "indispensable pour un gouvernement sans majorité absolue",
                     "la procédure accélérée (45) supprime une lecture : levier temporel majeur dans un "
                     "calendrier de fin de législature"],
       contraintes=["les délais raccourcis réduisent le temps d'amendement et l'examen citoyen",
                    "un texte non adopté en commission est discuté sur le texte initial, souvent moins "
                    "consensuel"],
       contre=["Conférence des présidents (calendrier)", "commissions (contenu du texte discuté)",
               "Conseil constitutionnel (61 sur la sincérité de la procédure)"],
       croise=["43", "45", "46", "47", "47-1", "48", "89"],
       mecanismes=("navette", "procedure_acceleree", "delai_examen"),
       leviers=("navette_lectures", "usage_procedure_acceleree")),
    _a("43", "Commissions permanentes (huit au plus) et commissions spéciales",
       "V", "organisation", "Chaque assemblée",
       "« Les projets et propositions de loi sont envoyés pour examen à l'une des commissions permanentes dont "
       "le nombre est limité à huit dans chaque assemblée. » À la demande du Gouvernement ou de l'assemblée, "
       "une commission spéciale peut être désignée.",
       regles=["8 commissions permanentes maximum par assemblée", "commission spéciale à la demande du "
               "Gouvernement ou de l'assemblée", "candidatures publiées avant l'ouverture de la session"],
       opportunites=["la commission spéciale permet un regard transversal (climat, institutions, santé) et "
                     "contourne l'enfermement sectoriel",
                     "la présidence de la commission des Finances ou des Affaires sociales est un pouvoir "
                     "considérable sur le contenu voté (souvent dévolu à l'opposition par convention)"],
       contraintes=["le plafond de 8 favorise les textes fourre-tout",
                    "la répartition des présidences à la représentation proportionnelle rend les "
                    "majorités de commission instables en assemblée éclatée"],
       contre=["les groupes (51-1)", "la Conférence des présidents (choix de la commission saisie)"],
       croise=["42", "44", "46", "48", "51-1", "51-2"],
       mecanismes=("commission_permanente", "commission_speciale")),
    _a("44", "Droit d'amendement ; motions procédurales ; vote bloqué",
       "V", "procédure législative", "Parlementaires et Gouvernement",
       "Le droit d'amendement appartient aux membres du Parlement et au Gouvernement, en séance ou en "
       "commission selon les règlements, dans le cadre d'une loi organique. Après l'ouverture du débat, le "
       "Gouvernement peut s'opposer à l'examen de tout amendement non préalablement soumis à la commission. "
       "Si le Gouvernement le demande, l'assemblée saisie se prononce par un seul vote sur tout ou partie du "
       "texte en discussion, en retenant uniquement les amendements proposés ou acceptés par le Gouvernement.",
       regles=["irrecevabilité des amendements sans lien, même indirect, avec le texte (45 al.1)",
               "motions : préalable, exception d'irrecevabilité, question préalable, renvoi à la commission",
               "vote bloqué : un seul vote, amendements écartés sans débat"],
       opportunites=["le vote bloqué verrouille le compromis sans engager la responsabilité : alternative au "
                     "49.3, moins coûteuse en légitimité — instrument central d'un gouvernement minoritaire",
                     "la motion préalable permet à l'opposition de poser une question de fond sans disperser "
                     "le vote",
                     "les compromis en commission font passer des mesures sans scrutin solennel"],
       contraintes=["en assemblée éclatée, le rejet des motions procédurales s'obtient à la majorité "
                    "relative : le Gouvernement gagne souvent par défaut",
                    "l'appréciation du « lien » relève du président d'assemblée : filtre politique",
                    "le droit d'amendement est un objectif de valeur constitutionnelle : son encadrement "
                    "excessif est censurable (2018-772 DC, 2019-789 DC, 2023-855 DC)"],
       contre=["présidents d'assemblée (irrecevabilité)", "Conseil constitutionnel (61)",
               "groupes (48 : ordre du jour, 51-1 : droits)"],
       croise=["40", "41", "42", "45", "46", "48", "49", "51-1"],
       mecanismes=("amendements", "vote_bloque", "motions_procedurales"),
       leviers=("droit_amendement", "usage_vote_bloque")),
    _a("45", "Navette, CMP, dernier mot de l'AN, procédure accélérée",
       "V", "procédure législative", "Premier ministre, présidents des deux assemblées, Assemblée nationale",
       "Tout projet ou proposition est examiné successivement dans les deux assemblées en vue de l'adoption "
       "d'un texte identique ; tout amendement est recevable en première lecture dès lors qu'il présente un "
       "lien, même indirect, avec le texte déposé ou transmis. Après deux lectures par chaque assemblée (une "
       "seule en procédure accélérée, sauf opposition conjointe des deux Conférences des présidents), le "
       "Premier ministre — ou, pour une proposition de loi, les présidents des deux assemblées agissant "
       "conjointement — peut provoquer une commission mixte paritaire chargée de proposer un texte sur les "
       "dispositions restant en discussion. Le texte de la CMP est voté sans amendement sauf accord du "
       "Gouvernement. En cas d'échec, le Gouvernement peut, après une nouvelle lecture par chaque assemblée, "
       "demander à l'Assemblée nationale de statuer définitivement.",
       regles=["CMP : 7 députés + 7 sénateurs (plus 7 suppléants chacun)",
               "procédure accélérée : 1 lecture par assemblée au lieu de 2 (usage : plus de 80 % des textes)",
               "nouvelle lecture : l'AN peut reprendre le texte de la CMP ou son dernier texte voté modifié "
               "des amendements du Sénat",
               "aucun dernier mot possible pour les projets de révision (89) ni pour les lois organiques "
               "relatives au Sénat (46 al.4)"],
       opportunites=["le dernier mot de l'AN est l'arme d'une majorité relative : le socle gouvernemental "
                     "(209 sièges en octobre 2026) peut achever une navette si le Sénat ne durcit pas le "
                     "texte au point de rendre la reprise impossible",
                     "demander au Sénat de statuer en dernier ressort (dérogation possible pour certains "
                     "textes territoriaux) : reconnaît le poids de la chambre haute",
                     "provoquer l'échec de la CMP est une tactique de négociation : elle rouvre un cycle de "
                     "lecture et un temps politique"],
       contraintes=["toute révision constitutionnelle exige l'accord en termes identiques des deux "
                    "assemblées (89) : le Sénat détient un veto de fait",
                    "la CMP ne porte que sur les dispositions restant en discussion",
                    "la procédure accélérée ne peut être engagée sur les lois organiques touchant le Sénat"],
       contre=["Sénat (amendements conservés, hostilité territoriale)", "Conférences des présidents "
               "(opposition conjointe à l'accélération)", "Conseil constitutionnel (61)"],
       croise=["39", "42", "43", "44", "46", "47", "49", "72", "89"],
       strates=["National", "Local"],
       mecanismes=("navette", "commission_mixte_paritaire", "dernier_mot_assemblee", "procedure_acceleree"),
       leviers=("navette_lectures", "usage_procedure_acceleree")),
    _a("46", "Lois organiques : majorité absolue en dernière lecture, veto sénatorial, saisine obligatoire",
       "V", "procédure législative", "Parlement ; Conseil constitutionnel",
       "Les lois organiques sont votées et modifiées selon un régime dérogatoire : délai de 6 semaines (ou "
       "15 jours en procédure accélérée) avant délibération en première lecture ; application de l'article 45 "
       "mais, faute d'accord, l'Assemblée nationale ne peut adopter en dernière lecture qu'à la majorité "
       "absolue de ses membres ; les lois organiques relatives au Sénat doivent être votées dans les mêmes "
       "termes par les deux assemblées ; promulgation seulement après déclaration de conformité par le "
       "Conseil constitutionnel.",
       regles=["majorité absolue de l'AN (289/577) en dernière lecture si la CMP échoue",
               "15 jours de délai minimal avec procédure accélérée",
               "saisine obligatoire du Conseil constitutionnel (46 al.5)",
               "lois organiques « Sénat » : mêmes termes exigés (veto absolu de la chambre haute)"],
       opportunites=["négocier avec le Sénat devient rationnel : le veto sur ses propres règles est absolu",
                     "une réforme institutionnelle peut être adoptée par paliers organiques (statut de "
                     "l'élu, RIC local, pétitions) sans révision de la Constitution"],
       contraintes=["réforme du mode de scrutin, nombre de sièges, régime électoral : lois organiques, donc "
                    "inaccessibles à une majorité relative",
                    "la censure du Conseil impose une reprise du texte, avec ses délais",
                    "le Sénat peut tuer une loi organique électorale en amendant (ex. 2022 : échec de la "
                    "proportionnelle à 20 %)"],
       contre=["Sénat (veto absolu sur ses règles)", "Conseil constitutionnel (censure)",
               "AN à défaut de 289 voix"],
       croise=["24", "25", "34", "42", "45", "61"],
       mecanismes=("loi_organique", "saisine_obligatoire"),
       leviers=("reforme_proportionnelle", "reforme_elections_loi_organique")),
    _a("47", "Lois de finances : 40 + 15 + 70 jours, ordonnance à défaut",
       "V", "budget", "Parlement ; Gouvernement",
       "Le Parlement vote les projets de loi de finances dans les conditions prévues par une loi organique "
       "(LOLF du 1er août 2001). Si l'Assemblée nationale ne s'est pas prononcée en première lecture dans le "
       "délai de quarante jours après le dépôt, le Gouvernement saisit le Sénat qui doit statuer dans un délai "
       "de quinze jours ; il est ensuite procédé comme à l'article 45. Si le Parlement ne s'est pas prononcé "
       "dans un délai de soixante-dix jours, les dispositions du projet peuvent être mises en vigueur par "
       "ordonnance. Si la loi de finances n'a pas été déposée en temps utile pour être promulguée avant le "
       "début de l'exercice, le Gouvernement demande d'urgence l'autorisation de percevoir les impôts et ouvre "
       "par décret les crédits des services votés. Les délais sont suspendus hors session.",
       regles=["40 jours pour l'AN en première lecture", "15 jours pour le Sénat", "70 jours au total",
               "à défaut : application par ordonnance (47 al.3)",
               "à défaut de dépôt dans les temps : perception des impôts et services votés par décret",
               "calendrier réel : PLF 2027 présenté en conseil des ministres le 1er octobre 2026, déposé le "
               "6 octobre 2026, échéance des 70 jours le 26 novembre 2026"],
       opportunites=["le compte à rebours constitutionnel structure toute la négociation budgétaire : c'est "
                     "la racine de l'usage du 49.3 (trois usages en janvier 2026 pour le budget 2026)",
                     "l'ordonnance du 70e jour désarme l'obstruction : aucune paralysie budgétaire possible",
                     "la règle des services votés garantit la continuité du service public même sans loi "
                     "votée"],
       contraintes=["aucune économie ni recette ne peut naître d'un amendement non gouvernemental (40)",
                    "la première assemblée saisie est contrainte (AN) : pas de renversement de l'ordre",
                    "les cibles de déficit s'inscrivent dans le cadre européen (art. 126 TFUE, règlement "
                    "(UE) 2024/1263 du pacte réformé)"],
       contre=["AN (rejet du texte → 49.3 ou ordonnance)", "Sénat (réécriture, majorité absolue sur les "
               "recettes)", "Cour des comptes (47-2, certification)", "Conseil constitutionnel (61 : "
               "censure de cavaliers et de surcharge normative)"],
       strates=["National", "Europe", "Local", "Mondial"],
       croise=["34", "39", "40", "42", "45", "47-1", "47-2", "49", "88-1", "88-4"],
       mecanismes=("budget_delais", "ordonnance_budgetaire", "services_votes"),
       leviers=("cadencement_budgetaire", "usage_49_3", "effort_structurel_mde")),
    _a("47-1", "Lois de financement de la sécurité sociale : 20 + 15 + 50 jours",
       "V", "budget", "Parlement ; Gouvernement",
       "Le Parlement vote les projets de loi de financement de la sécurité sociale dans les conditions "
       "prévues par une loi organique ; si l'AN ne s'est pas prononcée dans un délai de vingt jours, le "
       "Gouvernement saisit le Sénat qui doit statuer dans les quinze jours ; si le Parlement ne s'est pas "
       "prononcé dans un délai de cinquante jours, les dispositions du projet peuvent être mises en œuvre par "
       "ordonnance. Les délais sont suspendus hors session et pendant les semaines sans séance.",
       regles=["20 jours AN, 15 jours Sénat, 50 jours au total",
               "le Parlement fixe les objectifs de dépenses (ONDAM) et les recettes prévisionnelles, pas les "
               "montants par caisse",
               "calendrier réel : PLFSS 2027 déposé le 6 octobre 2026, échéance des 50 jours le 17 décembre "
               "2026"],
       opportunites=["la brièveté du délai (20 jours) rend l'agenda social négociable sous pression : levier "
                     "pour une réforme paramétrique",
                     "la voie de l'ordonnance (50 jours) ferme la porte à l'obstruction",
                     "l'avis du CESE (70) et les travaux de la Cour (47-2) arment la négociation avec les "
                     "partenaires sociaux"],
       contraintes=["les amendements aggravant la charge sociale sont irrecevables (40)",
                    "les réformes de retraites, santé, famille relèvent de la loi (34) : pas de décret",
                    "les mesures d'économie doivent respecter l'égalité devant les charges publiques (DDHC "
                    "art. 13) sous contrôle du Conseil (61, 61-1)"],
       contre=["Sénat (réécriture forte, majorité de droite et du centre depuis le 27 septembre 2026)",
               "AN (motion de censure en cas de 49.3)", "Conseil constitutionnel (61)"],
       strates=["National", "Local", "Europe"],
       croise=["34", "40", "47", "49", "70", "47-2", "72-2"],
       mecanismes=("budget_delais", "ordonnance_budgetaire"),
       leviers=("cadencement_budgetaire", "ondam_variation")),
    _a("47-2", "Cour des comptes : assistance au Parlement, sincérité des comptes publics",
       "V", "contrôle & évaluation", "Cour des comptes ; Parlement ; Gouvernement",
       "« La Cour des comptes assiste le Parlement dans le contrôle de l'action du Gouvernement. Elle assiste "
       "le Parlement et le Gouvernement dans le contrôle de l'exécution des lois de finances et de "
       "l'application des lois de financement de la sécurité sociale ainsi que dans l'évaluation des "
       "politiques publiques. Par ses rapports publics, elle contribue à l'information des citoyens. Les "
       "comptes des administrations publiques sont réguliers et sincères. Ils donnent une image fidèle du "
       "résultat de leur gestion, de leur patrimoine et de leur situation financière. »",
       regles=["obligation de comptes « réguliers et sincères » à valeur constitutionnelle",
               "saisine par une assemblée : art. 58 de la LOLF (rapports demandés par les présidents ou "
               "par 1/10 des membres)",
               "les rapports publics sont la base documentaire de l'évaluation"],
       opportunites=["la saisine parlementaire produit un rapport public : arme de transparence à la portée "
                     "d'une minorité organisée (1/10 = 58 députés ou 35 sénateurs)",
                     "la certification des comptes fournit une mesure externe de la qualité budgétaire, "
                     "mobilisable comme garde-fou dans le simulateur",
                     "l'évaluation des politiques publiques permet de réallouer sur critères chiffrés"],
       contraintes=["la Cour ne censure pas une politique : elle juge des comptes, pas des choix",
                    "son premier président est nommé en conseil des ministres (13) sans seuil de blocage "
                    "exprès : la nomination, en février 2026, d'une ministre du Budget en exercice a relancé "
                    "le débat sur l'indépendance (proposition de loi organique du Sénat n° 404, "
                    "16 février 2026)",
                    "les suites données aux rapports restent discrétionnaires"],
       contre=["Parlement (saisine, auditions, réponses obligatoires du Gouvernement)",
               "citoyens et presse (publicité des rapports)",
               "Conseil constitutionnel (statut des magistrats financiers, art. 13 et 34)"],
       strates=["National", "Local", "Europe"],
       croise=["13", "34", "47", "47-1", "51-2", "72-2"],
       mecanismes=("audit_cour_des_comptes", "sincerite_comptes", "nomination_independance"),
       leviers=("gouvernance_audit", "qualite_depense")),
    _a("48", "Ordre du jour : priorité gouvernementale, semaine de contrôle, jour de l'opposition",
       "V", "contrôle & évaluation", "Chaque assemblée ; Gouvernement ; groupes",
       "Sans préjudice des trois derniers alinéas de l'article 28, l'ordre du jour est fixé par chaque "
       "assemblée. Deux semaines de séance sur quatre sont réservées par priorité, dans l'ordre fixé par le "
       "Gouvernement, à ses textes. Sont aussi inscrits par priorité à sa demande : les PLF, les PLFSS, les "
       "textes transmis par l'autre assemblée depuis six semaines au moins, les projets relatifs aux états de "
       "crise et les demandes d'autorisation de l'article 35. Une semaine sur quatre est réservée au contrôle "
       "et à l'évaluation. Un jour de séance par mois est réservé à un ordre du jour arrêté à l'initiative "
       "des groupes d'opposition et minoritaires. Une séance par semaine au moins est réservée par priorité "
       "aux questions des parlementaires et aux réponses du Gouvernement.",
       regles=["2 semaines/4 au Gouvernement ; 1 semaine/4 au contrôle ; 1 jour/mois à l'opposition et aux "
               "minoritaires ; 1 séance/semaine de questions ; au Sénat, une séance par mois réservée aux "
               "propositions d'initiative sénatoriale",
               "textes transmis depuis 6 semaines : priorité d'inscription",
               "les ordres du jour sont arrêtés en Conférence des présidents puis ratifiés en séance"],
       opportunites=["la « niche » (jour de l'opposition) est le seul espace où un texte d'opposition ou "
                     "sénatorial aboutit sans le Gouvernement : voie réelle des réformes sociétales et "
                     "institutionnelles",
                     "la semaine de contrôle permet d'imposer audits et questions sans risque de censure",
                     "un gouvernement minoritaire peut échanger des priorités d'ordre du jour contre des "
                     "voix : monnaie d'échange mesurable"],
       contraintes=["le Gouvernement conserve la priorité sur l'essentiel du calendrier",
                    "les résolutions (34-1) et questions avec débat ne contraignent pas l'exécutif",
                    "sans accord en Conférence des présidents, le calendrier est bloqué par la navette"],
       contre=["Conférence des présidents", "groupes d'opposition (51-1)",
               "Conseil constitutionnel (61 sur les règles de programmation du calendrier)"],
       croise=["28", "29", "34-1", "42", "44", "49", "51-1", "51-2"],
       mecanismes=("ordre_du_jour", "niche_parlementaire", "questions_gouvernement"),
       leviers=("agenda_parlementaire",)),
    _a("49", "Responsabilité gouvernementale : DPG, censure, 49.3, approbation par le Sénat",
       "V", "législatif", "Premier ministre ; Assemblée nationale ; Sénat (al. 4)",
       "Al. 1 : le Premier ministre, après délibération du conseil des ministres, engage devant l'Assemblée "
       "nationale la responsabilité du Gouvernement sur son programme ou éventuellement sur une déclaration "
       "de politique générale. Al. 2 : l'AN met en cause cette responsabilité par une motion de censure, "
       "recevable si signée par au moins un dixième des membres ; le vote ne peut avoir lieu que "
       "quarante-huit heures après le dépôt ; seuls les votes favorables sont recensés ; la motion est "
       "adoptée à la majorité des membres composant l'Assemblée ; un député ne peut signer plus de trois "
       "motions par session ordinaire (une par session extraordinaire). Al. 3 : le Premier ministre peut, "
       "après délibération en conseil, engager la responsabilité sur le vote d'un PLF ou d'un PLFSS — le "
       "projet est considéré comme adopté sauf motion déposée dans les vingt-quatre heures et votée — et "
       "peut recourir à cette procédure pour un autre projet ou une proposition de loi par session. Al. 4 : "
       "le Premier ministre a la faculté de demander au Sénat l'approbation d'une déclaration de politique "
       "générale.",
       regles=["1/10 des signatures : 58 députés (sur 577)", "48 heures avant le vote de censure",
               "majorité absolue des membres : 289 voix", "seuls les votes favorables sont comptés "
               "(s'abstenir = maintenir le gouvernement)", "24 heures pour déposer une motion après un 49.3",
               "un usage du 49.3 par session pour un texte ordinaire, les PLF et PLFSS n'étant pas comptés",
               "trois motions de censure au plus par session ordinaire",
               "trois engagements de responsabilité par l'alinéa 3 en janvier 2026 pour le budget 2026, "
               "suivis d'un engagement public de renoncement à son usage pour les textes ordinaires"],
       opportunites=["le 49.3 achète du temps pour faire adopter sans vote : il préserve l'exécution "
                     "budgétaire mais consomme de la légitimité (le moteur mesure ces deux effets)",
                     "le renoncement au 49.3 — engagement public pris à l'été 2026 devant le Parlement — "
                     "transfère le pouvoir d'agenda vers les groupes et fait du Sénat un arbitre : "
                     "configurer cette variante est le test de robustesse d'une réforme",
                     "la motion de censure fonctionne quand elle agrège au-delà des clivages : celle de "
                     "septembre 2025 a renversé le gouvernement par une coalition de gauche et le "
                     "Rassemblement national, sans programme commun — le comptage des seuls votes favorables "
                     "rend cette agrégation possible",
                     "l'article 49 al. 4, jamais utilisé, permet de chercher une approbation au Sénat : "
                     "légitimité territoriale pour un gouvernement sans majorité absolue à l'AN",
                     "l'article 49 al. 1 (DPG) a été utilisé en sens inverse : rejeter une DPG équivaut à "
                     "une censure (1962, article 50)"],
       contraintes=["la censure votée impose la démission (50), sans dissolution automatique ni arbitrage "
                    "constitutionnel",
                    "le 49.3 est fermé pour les propositions de loi hors le cas de l'alinéa 3, pour les "
                    "motions, et pendant la vacance présidentielle (7 al. 11)",
                    "un gouvernement démissionnaire expédie les affaires courantes : le 49.3 achète du "
                    "temps, pas une majorité",
                    "le Sénat ne peut être censuré ni censurer : la bicaméralité n'offre pas de double "
                    "verrou de responsabilité"],
       contre=["les 289 voix de l'AN", "le Sénat (voix consultative, al. 4)",
               "le Conseil constitutionnel (incompétent sur le vote, compétent sur la procédure et la loi "
               "organique)", "l'histoire : très peu de censures abouties (1962, 2025) — le constituant de "
               "1958 a voulu cette faiblesse"],
       croise=["8", "20", "38", "44", "45", "47", "47-1", "50", "51", "68-1", "89"],
       strates=["National", "Local", "Europe", "Mondial"],
       mecanismes=("motion_censure", "engagement_responsabilite", "article_49_3", "approbation_senat",
                   "declaration_politique_generale"),
       leviers=("usage_49_3", "usage_motion_censure", "nombre_49_3_par_session")),
    _a("50", "Censure ou désapprobation : obligation de démission",
       "V", "législatif", "Assemblée nationale ; Premier ministre ; Président",
       "« Lorsque l'Assemblée nationale adopte une motion de censure ou lorsqu'elle désapprouve le programme "
       "ou une déclaration de politique générale du Gouvernement, le Premier ministre doit remettre au "
       "Président de la République la démission du Gouvernement. »",
       regles=["aucun délai écrit de démission (usage : immédiat, sous 24-48 h)",
               "le Président peut refuser la démission ou différer (aucune obligation d'accepter "
               "immédiatement)",
               "aucune obligation de dissoudre : 12 est une faculté"],
       opportunites=["la séquence censure → démission → nomination (2025 : chute de Bayrou, gouvernement "
                     "Lecornu) est entièrement modélisable, avec ses effets de ricochet sur les marchés, la "
                     "note souveraine et la tension sociale",
                     "le Président garde l'initiative de la nomination : une chambre censurante sans "
                     "majorité alternative ne gouverne pas"],
       contraintes=["la censure sans majorité alternative produit l'instabilité par itération (quatre "
                    "Premiers ministres entre 2022 et 2026)",
                    "un gouvernement démissionnaire ne peut pas engager de dépense structurelle nouvelle ni "
                    "demander un 49.3 de fond"],
       contre=["le Président (8)", "les groupes (défaut de coalition de gouvernement)", "le corps électoral "
               "(12 ou échéance naturelle de 2027)"],
       croise=["8", "12", "20", "49", "68", "7"],
       strates=["National", "Mondial", "Europe"],
       mecanismes=("chute_gouvernement", "gouvernement_affaires_courantes", "coalition_alternative"),
       leviers=("usage_motion_censure",)),
    _a("50-1", "Déclarations suivies de débat, avec vote facultatif sans engagement de responsabilité",
       "V", "contrôle & évaluation", "Gouvernement ; groupe parlementaire (51-1)",
       "Devant l'une ou l'autre des assemblées, le Gouvernement peut, de sa propre initiative ou à la demande "
       "d'un groupe parlementaire au sens de l'article 51-1, faire sur un sujet déterminé une déclaration qui "
       "donne lieu à débat et peut, s'il le décide, faire l'objet d'un vote sans engager sa responsabilité.",
       regles=["le vote n'a aucun effet sur la responsabilité", "l'initiative appartient aussi à un groupe",
               "aucune obligation de voter pour le Gouvernement"],
       opportunites=["le vote consultatif est la sonde de majorité du régime : le moteur l'utilise pour "
                     "estimer la probabilité réelle de censure sur un texte donné",
                     "à la demande d'un groupe, il force une explication du Gouvernement sans risque "
                     "institutionnel"],
       contraintes=["aucune conséquence juridique : un vote défavorable n'impose rien",
                    "le Gouvernement peut refuser le vote, vidant la procédure de son sens"],
       contre=["le Gouvernement (arbitre du vote)", "l'opinion (sanction électorale)"],
       croise=["20", "31", "48", "49", "51-1"],
       mecanismes=("vote_consultatif", "test_majorite"),
       leviers=("sondage_majorite",)),
    _a("51", "Report de droit de la clôture de session pour l'application de l'article 49",
       "V", "organisation", "Assemblées",
       "« La clôture de la session ordinaire ou des sessions extraordinaires est de droit retardée pour "
       "permettre, le cas échéant, l'application de l'article 49. À cette même fin, des séances "
       "supplémentaires sont de droit. »",
       regles=["report automatique (de plein droit)", "séances supplémentaires de droit : le plafond de 120 "
               "jours (28) est levé"],
       opportunites=["garantit qu'une censure puisse être votée, même en fin de session : on ne peut pas "
                     "sauver un budget par la clôture",
                     "symétriquement, garantit qu'un 49.3 aille à son terme"],
       contraintes=["l'obstruction temporelle (ne pas voter avant la clôture) est neutralisée",
                    "le coût politique d'une session prolongée reste à la charge du gouvernement comme de "
                    "l'opposition"],
       contre=["— : aucune autorité ne peut s'y opposer, c'est le verrou qui protège le jeu démocratique"],
       croise=["28", "29", "49"],
       mecanismes=("report_cloture_session",)),
    _a("51-1", "Droits des groupes parlementaires, droits spécifiques de l'opposition et des minoritaires",
       "V", "démocratie participative", "Chaque assemblée (règlement, contrôle du Conseil constitutionnel)",
       "« Le règlement de chaque assemblée détermine les droits des groupes parlementaires constitués en son "
       "sein. Il reconnaît des droits spécifiques aux groupes d'opposition de l'assemblée intéressée ainsi "
       "qu'aux groupes minoritaires. » (ajouté en 2008)",
       regles=["seuil de groupe : 15 députés, 10 sénateurs",
               "droits : ordre du jour (48), questions, temps de parole, moyens, présidences de commissions, "
               "droit de création d'une commission d'enquête par groupe et par session",
               "règlements obligatoirement soumis au Conseil constitutionnel avant application (61 al.1)"],
       opportunites=["les droits des groupes structurent la négociation en l'absence de majorité absolue : "
                     "ils transforment une chambre éclatée en système de coalitions",
                     "un groupe peut saisir le Conseil constitutionnel (60 députés ou sénateurs, art. 61), "
                     "demander une session extraordinaire (29, avec la majorité), obtenir une commission "
                     "d'enquête (51-2)"],
       contraintes=["un groupe qui passe sous le seuil redevient « non inscrit » : la percée RN-UDR au "
                    "Sénat (15 sièges) le 27 septembre 2026 change le jeu précisément parce qu'elle crée un "
                    "groupe — le seuil est un objet politique",
                    "les droits sont dans le règlement, donc modifiables à la majorité : précarité "
                    "institutionnelle"],
       contre=["Conseil constitutionnel (61 al.1 : règlement)", "bureau de l'assemblée (moyens, "
               "composition)"],
       croise=["24", "43", "48", "50-1", "51-2", "61"],
       mecanismes=("droits_opposition", "seuil_groupe"),
       leviers=("droits_opposition_parlementaire",)),
    _a("51-2", "Commissions d'enquête",
       "V", "contrôle & évaluation", "Chaque assemblée (loi + règlement)",
       "« Pour l'exercice des missions de contrôle et d'évaluation définies au premier alinéa de l'article "
       "24, des commissions d'enquête peuvent être créées au sein de chaque assemblée pour recueillir, dans "
       "les conditions prévues par la loi, des éléments d'information. » La loi détermine leurs règles "
       "d'organisation et de fonctionnement ; les conditions de création sont fixées par le règlement.",
       regles=["droit de création pour chaque groupe une fois par session ordinaire (AN, art. 141 du "
               "règlement ; Sénat, art. 20)", "durée des missions : 6 mois maximum (loi du 19 avril 1991 "
               "modifiée), 60 jours pour les missions courantes selon les règlements",
               "interdiction d'enquêter sur des faits ayant donné lieu à des poursuites judiciaires et "
               "se rapportant à ces poursuites (ordonnance du 17 novembre 1958, art. 6)",
               "témoins entendus sous serment ; sanctions pour faux témoignage"],
       opportunites=["contre-pouvoir non budgétaire : auditions sous serment, obligation de répondre, "
                     "publicité des travaux",
                     "les rapports de commissions sont des sources primaires pour calibrer l'« instant T » "
                     "du simulateur (santé, énergie, finances locales, immigration)",
                     "ils nourrissent des propositions de loi votables par la niche (48)"],
       contraintes=["ne peuvent ni juger ni sanctionner : séparation des pouvoirs",
                    "leur périmètre est borné par l'autorité de la chose jugée et par l'article 16 de la "
                    "DDHC",
                    "un rapport peut être minoritaire : l'usage politique des conclusions est incertain"],
       contre=["Gouvernement (demande de suspension en cas de poursuites)", "autorité judiciaire (sursis)",
               "bureau de l'assemblée (moyens, calendrier)"],
       croise=["24", "34", "48", "51-1", "66"],
       mecanismes=("commission_enquete", "controle_parlementaire"),
       leviers=("commissions_enquete_par_session",)),
)


# ────────────────────────────────────────────────────────────────────────────
# TITRE VI — DES TRAITÉS INTERNATIONAUX (articles 52 à 55)
# ────────────────────────────────────────────────────────────────────────────

_TITRE_VI: tuple[ArticleConstitution, ...] = (
    _a("52", "Négociation et ratification des traités",
       "VI", "Europe & traités", "Président de la République ; Gouvernement",
       "« Le Président de la République négocie et ratifie les traités. Il est informé de toute négociation "
       "tendant à la conclusion d'un accord international non soumis à ratification. »",
       regles=["le Président ratifie, le Gouvernement négocie et signe",
               "les accords non soumis à ratification échappent au vote, mais le Président en est informé"],
       opportunites=["la France peut engager une négociation européenne ou commerciale sans loi "
                     "préalable : vitesse d'action en période de crise",
                     "les accords « exécutifs » permettent des ajustements techniques (énergie, "
                     "interconnexions, défense) hors navette"],
       contraintes=["tout traité engageant les finances de l'État, modifiant des dispositions législatives, "
                    "relatif à l'état des personnes ou comportant cession de territoire exige une loi "
                    "(53)",
                    "aucune ratification possible si le Conseil constitutionnel relève une clause "
                    "contraire sans révision préalable (54)"],
       contre=["Parlement (53, 88-4)", "Conseil constitutionnel (54)", "CEDH et droit de l'UE (55)"],
       croise=["14", "53", "54", "55", "88-1", "88-4"],
       strates=["National", "Europe", "Mondial"],
       mecanismes=("negociation_internationale",)),
    _a("53", "Traités devant être ratifiés par la loi ; consentement des populations en cas de territoire",
       "VI", "Europe & traités", "Parlement",
       "Les traités de paix, de commerce, ceux relatifs à l'organisation internationale, ceux qui engagent "
       "les finances de l'État, ceux qui modifient des dispositions de nature législative, ceux relatifs à "
       "l'état des personnes et ceux comportant cession, échange ou adjonction de territoire ne peuvent être "
       "ratifiés ou approuvés qu'en vertu d'une loi ; ils ne prennent effet qu'après ratification ou "
       "approbation. « Nulle cession, nul échange, nulle adjonction de territoire n'est valable sans le "
       "consentement des populations intéressées. »",
       regles=["autorisation = loi (donc navette 45, irrecevabilité 40, saisine 61 possibles)",
               "consentement des populations pour tout changement de territoire",
               "les engagements de dépense liés à un traité entrent dans le champ du 34 et du 47"],
       opportunites=["la loi d'autorisation est un point de passage où le Parlement peut assortir la "
                     "ratification de conditions (clauses sociales, climatiques, réciprocité)",
                     "le débat sur un traité est un débat sur la politique économique et sociale "
                     "(levier de coalition)"],
       contraintes=["un traité non autorisé par la loi ne peut être ratifié : la voie unilatérale de "
                    "l'exécutif est fermée",
                    "les accords commerciaux de compétence mixte européenne supposent aussi la ratification "
                    "nationale (218 TFUE)"],
       contre=["Parlement (rejet de la loi d'autorisation)", "Conseil constitutionnel (54, 61)",
               "populations concernées (53 al.3)"],
       croise=["34", "47", "52", "54", "55", "88-5"],
       strates=["National", "Europe", "Mondial", "Local"],
       mecanismes=("ratification_traite", "consultation_territoire"),
       leviers=("ratification_traite",)),
    _a("53-1", "Accords européens sur l'examen des demandes d'asile ; droit d'asile",
       "VI", "droits & libertés", "Législateur ; République",
       "La République peut conclure avec les États européens liés par des engagements identiques en matière "
       "d'asile des accords déterminant leurs compétences respectives pour l'examen des demandes. « Même si "
       "la demande n'entre pas dans leur compétence en vertu de ces accords, les autorités de la République "
       "ont toujours le droit de donner asile à tout étranger persécuté en raison de son action en faveur de "
       "la liberté ou qui sollicite la protection de la France pour un autre motif. »",
       regles=["primauté du droit d'asile national sur la répartition européenne (règlement de Dublin)",
               "alinéa issu de la révision du 25 juin 1992 (Maastricht)"],
       opportunites=["la France peut déroger unilatéralement au mécanisme d'examen communautaire pour "
                     "protéger : marge souveraine écrite",
                     "fonde constitutionnellement une politique d'accueil sélective et assumée"],
       contraintes=["impossible de se lier à un système européen qui priverait la France du droit de donner "
                    "asile", "l'allocation de compétences doit rester compatible avec la DDHC et le "
                    "préambule de 1946 (alinéa 4 : droit d'asile)"],
       contre=["Conseil constitutionnel (61, 61-1 sur la loi d'asile)", "CEDH (art. 3)",
               "juges administratifs (OFPRA/CNDA)"],
       croise=["34", "55", "88-1", "53"],
       strates=["National", "Europe"],
       mecanismes=("asile_europe",)),
    _a("53-2", "Reconnaissance de la juridiction de la Cour pénale internationale",
       "VI", "droits & libertés", "Président ; Parlement",
       "« La République peut reconnaître la juridiction de la Cour pénale internationale dans les conditions "
       "prévues par le traité signé le 18 juillet 1998. » (créé par la révision du 22 janvier 1999, après "
       "la décision 98-408 DC qui exigeait une révision avant la ratification du Statut de Rome)",
       regles=["révision préalable exigée quand un engagement international contredit la Constitution (54)",
               "la reconnaissance de la CPI est constitutionnelle depuis 1999"],
       opportunites=["la France peut coopérer avec la CPI sans nouveau verrou constitutionnel",
                     "précédent méthodologique : la voie 54 → révision 89 → ratification"],
       contraintes=["l'immunité présidentielle (67) et parlementaire (26) coexiste avec la compétence de la "
                    "CPI : la loi organique a dû préciser les modalités de coopération",
                    "pas de soumission à une juridiction pénale internationale autre que la CPI sans "
                    "disposition expresse"],
       contre=["Conseil constitutionnel (54)", "Parlement (53 : loi d'autorisation)"],
       croise=["26", "53", "54", "67"],
       strates=["National", "Mondial"],
       mecanismes=("cooperation_penale_internationale",)),
    _a("54", "Contrôle de constitutionnalité des engagements internationaux avant ratification",
       "VI", "contrôle & évaluation", "Conseil constitutionnel",
       "Si le Conseil constitutionnel, saisi par le Président de la République, le Premier ministre, le "
       "président de l'une ou l'autre assemblée ou soixante députés ou soixante sénateurs, déclare qu'un "
       "engagement international comporte une clause contraire à la Constitution, l'autorisation de ratifier "
       "ne peut intervenir qu'après révision de la Constitution.",
       regles=["saisine : 4 autorités + 60 députés ou 60 sénateurs", "délai de 1 mois (8 jours sur demande "
               "d'urgence du Gouvernement, art. 61 al.3, applicable par renvoi de la pratique)",
               "effet : obligation de réviser avant de ratifier"],
       opportunites=["une minorité parlementaire (60) peut obliger à clarifier la conformité d'un traité "
                     "avant tout engagement",
                     "la saisine suspend de fait le calendrier de ratification : pouvoir d'agenda"],
       contraintes=["si la clause est contraire, deux choix seulement : renégocier ou réviser (89)",
                    "l'absence de saisine ne purgerait pas le risque a posteriori (61-1 sur la loi de "
                    "transposition)"],
       contre=["Conseil constitutionnel (seul juge)", "Parlement (89 : vote de la révision, veto du Sénat)"],
       croise=["53", "55", "61", "88-1", "89"],
       strates=["National", "Europe", "Mondial"],
       mecanismes=("controle_conformite_traite", "revision_prealable"),
       leviers=("souverainete_europeenne",)),
    _a("55", "Supériorité des traités sur les lois",
       "VI", "Europe & traités", "Juges judiciaires et administratifs",
       "« Les traités ou accords régulièrement ratifiés ou approuvés ont, dès leur publication, une autorité "
       "supérieure à celle des lois, sous réserve, pour chaque accord ou traité, de son application par "
       "l'autre partie. »",
       regles=["condition de réciprocité d'application", "effet direct seulement si le traité le prévoit",
               "la Constitution reste au sommet : le Conseil constitutionnel ne contrôle pas la loi au "
               "regard des traités (jurisprudence constante, décision 2004-496 D du 29 juillet 2004)"],
       opportunites=["le droit de l'UE et la CEDH deviennent des leviers d'action pour les citoyens et les "
                     "collectivités (inapplication d'une loi nationale incompatible)",
                     "l'invocabilité de compatibilité permet de faire évoluer des règles sans loi nouvelle"],
       contraintes=["une loi contraire à un traité est écartée par le juge ordinaire, mais pas censurée par "
                    "le Conseil constitutionnel : hiérarchie à deux vitesses",
                    "le constituant de 2004 a refusé d'inscrire la primauté du droit de l'UE dans la "
                    "Constitution (projet avorté)"],
       contre=["juges nationaux (écartent la loi incompatible)", "CJUE et CEDH",
               "Conseil constitutionnel (incompétence de principe, sauf bloc de constitutionnalité)"],
       croise=["54", "61", "61-1", "88-1"],
       strates=["National", "Europe", "Mondial", "Local"],
       mecanismes=("primaute_droit_international",)),
)


# ────────────────────────────────────────────────────────────────────────────
# TITRE VII — LE CONSEIL CONSTITUTIONNEL (articles 56 à 63)
# ────────────────────────────────────────────────────────────────────────────

_TITRE_VII: tuple[ArticleConstitution, ...] = (
    _a("56", "Composition et nomination des membres du Conseil constitutionnel",
       "VII", "contrôle & évaluation", "Président de la République, présidents des assemblées",
       "Neuf membres, mandat de neuf ans non renouvelable, renouvellement par tiers tous les trois ans ; "
       "trois nommés par le Président de la République, trois par le président de l'AN, trois par le "
       "président du Sénat ; la procédure de l'article 13 (avis des commissions, véto de 3/5) s'applique ; "
       "les anciens Présidents de la République sont membres de droit à vie ; le président du Conseil est "
       "nommé par le Président de la République et a voix prépondérante en cas de partage.",
       regles=["9 membres nommés + membres de droit à vie (anciens présidents)", "mandat de 9 ans non "
               "renouvelable", "renouvellement par tiers tous les 3 ans",
               "véto parlementaire si les votes négatifs atteignent 3/5 des suffrages exprimés dans les deux "
               "commissions additionnées"],
       opportunites=["la pratique des nominations montre que le véto de 3/5 des commissions est quasi "
                     "impossible à atteindre politiquement : le seuil est un garde-fou faible",
                     "les présidents des deux assemblées nomment trois membres chacun : un Sénat à majorité "
                     "opposée arme donc juridiquement la chambre haute (deux nominations + trois "
                     "sénateurs siégeant au CSM)",
                     "la voix prépondérante du président nommé peut faire basculer une décision à 4-4"],
       contraintes=["incompatibilité avec la fonction ministérielle ou parlementaire (57)",
                    "pas de renouvellement : un président ne peut pas « refaire » le Conseil à son image en "
                    "un quinquennat (tiers seulement)",
                    "la présence des anciens présidents à vie est critiquée mais non abrogée : elle "
                    "dépend d'une révision (89)"],
       contre=["commissions permanentes des deux assemblées (3/5 cumulés)", "Sénat (trois nominations)",
               "opinion publique et presse (coût politique d'une nomination partisane)"],
       croise=["13", "57", "61", "63", "89"],
       mecanismes=("nomination_sages", "renouvellement_tiers"),
       leviers=("composition_conseil_constitutionnel",)),
    _a("57", "Incompatibilités des membres du Conseil constitutionnel",
       "VII", "organisation", "Loi organique",
       "« Les fonctions de membre du Conseil constitutionnel sont incompatibles avec celles de ministre ou "
       "de membre du Parlement. Les autres incompatibilités sont fixées par une loi organique. »",
       regles=["incompatibilités détaillées par l'ordonnance du 7 novembre 1958 (modification en 2020 : "
               "compatible avec certaines fonctions locales ? non — mandat local incompatible depuis 2008)",
               "serment devant le Président de la République (art. 2 bis de l'ordonnance de 1958, ajouté en "
               "2011)"],
       opportunites=["renforcer la liste des incompatibilités par la loi organique (post-cabinet, "
                     "activités de conseil) est une mesure anti-pantouflage directement opposable"],
       contraintes=["aucune incompatibilité ne peut être créée par simple loi : loi organique",
                    "le statut des membres n'empêche pas les controverses sur l'indépendance des nommés "
                    "(2025-2026)"],
       contre=["Conseil constitutionnel lui-même (auto-saisine sur la loi organique, 61)",
               "Parlement (vote de la loi organique, veto du Sénat sur ses textes)"],
       croise=["13", "56", "63"],
       mecanismes=("independance_juges",)),
    _a("58", "Régularité de l'élection présidentielle ; proclamation des résultats",
       "VII", "souveraineté", "Conseil constitutionnel",
       "« Le Conseil constitutionnel veille à la régularité de l'élection du Président de la République. Il "
       "examine les réclamations et proclame les résultats du scrutin. »",
       regles=["publication au Journal officiel de la liste des présentations (cinq cents signatures) au "
               "deuxième jeudi précédant le premier tour",
               "réclamation dans les dix jours suivant la proclamation",
               "comptes de campagne : le Conseil statue dans les six mois du dépôt (art. L. 52-12 et "
               "suivants du code électoral)"],
       opportunites=["le contentieux des comptes de campagne est un levier de sanction réelle : rejet, "
                     "réduction du remboursement, inéligibilité d'un an",
                     "la proclamation est la date qui clôt l'incertitude politique : utile pour caler le "
                     "« jour 1 » d'une mandature dans le moteur"],
       contraintes=["le Conseil ne peut pas annuler l'élection sans motifs graves (jurisprudence)",
                    "le Conseil est juge de sa propre saisine : pas d'appel (62)"],
       contre=["— (le Conseil est le juge final ; seul le constituant peut modifier la compétence)"],
       croise=["3", "6", "7", "59", "62"],
       strates=["National"],
       mecanismes=("contentieux_electoral",)),
    _a("59", "Contentieux des élections législatives et sénatoriales",
       "VII", "souveraineté", "Conseil constitutionnel",
       "« Le Conseil constitutionnel statue, en cas de contestation, sur la régularité de l'élection des "
       "députés et des sénateurs. »",
       regles=["réclamation dans les 10 jours suivant la proclamation (art. R. 119 du code électoral)",
               "le Conseil peut annuler l'élection et déclarer inéligible le candidat (1 an maximum)",
               "quasi-chronique : une dizaine d'annulations par législature (2024 : 8 saisines, "
               "annulations dont celles déclarant des démissions d'office en 2025)"],
       opportunites=["l'annulation d'une élection modifie la composition de l'assemblée et donc les seuils "
                     "(289) : le contentieux électoral est un paramètre du modèle de coalition",
                     "le Conseil peut régulariser la représentation des Français de l'étranger, des "
                     "outre-mer et des collectivités à règles particulières"],
       contraintes=["pas de saisine citoyenne hors le cadre des électeurs de la circonscription",
                    "les décisions sont sans recours (62) : pas d'appel politique"],
       contre=["— (jugement en dernier ressort)"],
       croise=["3", "24", "25", "58", "62"],
       strates=["National", "Local"],
       mecanismes=("contentieux_electoral", "vacance_siege"),
       leviers=("renouvellement_partiel",)),
    _a("60", "Régularité des opérations de référendum",
       "VII", "souveraineté", "Conseil constitutionnel",
       "« Le Conseil constitutionnel veille à la régularité des opérations de référendum prévues aux "
       "articles 11 et 89 et au titre XV. Il en proclame les résultats. »",
       regles=["avis obligatoires du Gouvernement avant l'organisation (art. 46 et suivants de "
               "l'ordonnance de 1958)", "la proclamation est la date de départ du délai de promulgation "
               "(15 jours, art. 11 al. 8)",
               "matériel de vote et affichage officiel réglementés (art. R. 181 et suivants du code "
               "électoral)"],
       opportunites=["le Conseil peut annuler des résultats partiels (1969 ? non — 2000 NC ; usage "
                     "marginal mais réel), et surtout il encadre la campagne : égalité du temps de parole",
                     "la proclamation datée permet de sécuriser la réforme : la loi référendaire est "
                     "immédiatement exécutoire"],
       contraintes=["aucun recours contre le résultat lui-même au fond : le Conseil juge la régularité, pas "
                    "le bien-fondé",
                    "le référendum ne peut être organisé hors session que dans les cas prévus (11, 89)"],
       contre=["— (le juge est le dernier mot)"],
       croise=["3", "11", "61", "72-1", "88-5", "89"],
       mecanismes=("referendum_legislatif", "revision_constitutionnelle", "controle_referendum"),
       leviers=("usage_referendum_11",)),
    _a("61", "Contrôle a priori des lois organiques, règlements d'assemblée et lois",
       "VII", "contrôle & évaluation", "Conseil constitutionnel",
       "Les lois organiques, avant leur promulgation, les propositions de loi mentionnées à l'article 11 "
       "avant qu'elles ne soient soumises au référendum, et les règlements des assemblées parlementaires, "
       "avant leur mise en application, doivent être soumis au Conseil constitutionnel. Aux mêmes fins, les "
       "lois peuvent être déférées avant promulgation par le Président de la République, le Premier "
       "ministre, le président de l'AN, le président du Sénat ou soixante députés ou soixante sénateurs. Le "
       "Conseil statue dans le mois, ou huit jours en cas d'urgence à la demande du Gouvernement ; la saisine "
       "suspend le délai de promulgation.",
       regles=["saisine obligatoire : lois organiques, règlements des assemblées, propositions de loi "
               "visant l'article 11 (RIP)",
               "saisine facultative : soixante députés ou soixante sénateurs (révision du 29 octobre 1974)",
               "un mois ; huit jours en cas d'urgence déclarée par le Gouvernement",
               "effet : suspension du délai de promulgation (10)"],
       opportunites=["soixante signatures suffisent : c'est l'arme juridictionnelle la plus rentable de "
                     "l'arsenal d'opposition. Le Conseil constitutionnel a enregistré vingt-six saisines de "
                     "contrôle a priori en 2025 et onze au 23 juillet 2026, avec un délai moyen constaté de "
                     "dix-huit jours (bilan public du Conseil)",
                     "la saisine suspend la promulgation : elle retarde l'entrée en vigueur d'une réforme "
                     "de plusieurs semaines, ce qui a un effet mesurable sur le calendrier",
                     "le Conseil peut censurer des « cavaliers » (dispositions sans lien avec le texte) et "
                     "forcer une réécriture"],
       contraintes=["une loi promulguée sans saisine échappe au contrôle a priori : il ne reste que la QPC "
                    "(61-1), qui ne porte que sur les droits et libertés",
                    "le Conseil ne juge pas l'opportunité : il censure la violation de la Constitution",
                    "l'urgence déclarée par le Gouvernement ramène le délai à 8 jours : l'obstruction "
                    "juridique a un prix temporel"],
       contre=["le Gouvernement peut réécrire le texte et représenter la navette",
               "— : aucune autorité ne peut réformer une décision du Conseil, sauf le constituant"],
       croise=["10", "11", "25", "34", "41", "46", "54", "61-1", "62", "63"],
       strates=["National", "Local", "Europe"],
       mecanismes=("saisine_conseil", "censure_a_priori"),
       leviers=("saisine_conseil_constitutionnel",)),
    _a("61-1", "Question prioritaire de constitutionnalité (QPC)",
       "VII", "droits & libertés", "Justiciable ; Conseil d'État ou Cour de cassation ; Conseil constitutionnel",
       "« Lorsque, à l'occasion d'une instance en cours devant une juridiction, il est soutenu qu'une "
       "disposition législative porte atteinte aux droits et libertés que la Constitution garantit, le Conseil "
       "constitutionnel peut être saisi de cette question sur renvoi du Conseil d'État ou de la Cour de "
       "cassation qui se prononce dans un délai déterminé. » (révision du 23 juillet 2008)",
       regles=["double filtre : condition de sérieux et de nouveauté devant la juridiction du fond, puis "
               "renvoi par le Conseil d'État ou la Cour de cassation",
               "trois mois pour la juridiction suprême, trois mois pour le Conseil constitutionnel (loi "
               "organique du 10 décembre 2009)",
               "quarante-neuf décisions QPC rendues au premier semestre 2026, délai moyen constaté de "
               "soixante-quatorze jours (bilan public du Conseil)"],
       opportunites=["arme du citoyen et des entreprises contre une loi déjà promulguée : aucun délai pour "
                     "agir, seulement une instance en cours",
                     "l'abrogation différée (62 al.3) permet une transition douce, donc une réforme possible "
                     "sans chaos rétroactif",
                     "le contentieux fiscal et social est massivement QPC-able : levier de "
                     "reconfiguration des politiques publiques"],
       contraintes=["ne porte que sur les droits et libertés garantis, pas sur l'organisation des pouvoirs",
                    "une disposition déjà déclarée conforme ne peut être re-attaquée, sauf changement des "
                    "circonstances",
                    "le justiciable doit passer par un avocat et une instance : pas de saisine directe"],
       contre=["le législateur peut réécrire la disposition abrogée (dans le respect de la décision)",
               "les juridictions du fond filtrent les renvois (10 % de taux de renvoi environ)"],
       croise=["34", "61", "62", "63"],
       strates=["National", "Local", "Europe"],
       mecanismes=("qpc", "abrogation_differee"),
       leviers=("acces_droit",)),
    _a("62", "Effet des décisions du Conseil constitutionnel",
       "VII", "contrôle & évaluation", "Conseil constitutionnel",
       "Une disposition déclarée inconstitutionnelle sur le fondement de l'article 61 ne peut être "
       "promulguée ni mise en application. Sur le fondement de l'article 61-1, elle est abrogée à compter de "
       "la publication de la décision ou d'une date ultérieure fixée par le Conseil, qui détermine les "
       "conditions et limites de remise en cause des effets produits. « Les décisions du Conseil "
       "constitutionnel ne sont susceptibles d'aucun recours. Elles s'imposent aux pouvoirs publics et à "
       "toutes les autorités administratives et juridictionnelles. »",
       regles=["censure = interdiction de promulguer (a priori) ou abrogation (a posteriori)",
               "report d'abrogation jusqu'à 6 mois dans la pratique (18 mois maximum selon les cas)",
               "chose jugée absolue : aucun recours",
               "effets acquis : la remise en cause est encadrée par la décision elle-même"],
       opportunites=["pour un requérant : l'effet utile d'une QPC gagnée peut être rétroactif (instance en "
                     "cours) — le seul levier de « réparation » du système",
                     "pour un gouvernement : anticiper la censure par une réécriture conforme réduit le "
                     "risque d'abrogation en cascade"],
       contraintes=["une décision ne peut être révisée que par une décision ultérieure (changement de "
                    "circonstances)",
                    "le législateur ne peut pas contourner une censure en reproduisant la disposition "
                    "identique",
                    "l'abrogation différée crée une zone d'insécurité juridique temporaire"],
       contre=["— : autorité absolue de la chose jugée", "le constituant seul (89) peut renverser un "
               "principe dégagé hors texte"],
       croise=["61", "61-1", "63", "89"],
       mecanismes=("autorite_chose_jugee", "abrogation_reportee"),
       leviers=("securite_juridique",)),
    _a("63", "Loi organique sur l'organisation et la procédure du Conseil constitutionnel",
       "VII", "organisation", "Législateur organique",
       "« Une loi organique détermine les règles d'organisation et de fonctionnement du Conseil "
       "constitutionnel, la procédure qui est suivie devant lui et notamment les délais ouverts pour le "
       "saisir de contestations. » (ordonnance du 7 novembre 1958 modifiée, notamment en 2008-2009 et "
       "2021-2022)",
       regles=["délais de saisine : dix jours pour contester un scrutin, un mois pour déclarer une QPC "
               "devant la juridiction du fond",
               "procédure QPC : trois mois devant la juridiction suprême, trois mois devant le Conseil",
               "délibération en formation de neuf (les membres de droit peuvent siéger) ; quorum de sept"],
       opportunites=["raccourcir les délais de jugement (débat récurrent en 2025-2026 sur la saturation du "
                     "Conseil) est réglable en loi organique : levier de fluidité",
                     "ouvrir la parole aux tiers (memoranda d'associations, « amis de la cour ») a été "
                     "engagé par la réforme de 2010, peut être élargi"],
       contraintes=["la loi organique est elle-même contrôlée (61) : pas d'auto-organisation discrétionnaire",
                    "aucun recours contre la procédure (62)"],
       contre=["Conseil constitutionnel (contrôle de la loi organique)", "Parlement (navette, veto du "
               "Sénat sur les textes organiques le concernant)"],
       croise=["56", "57", "61", "61-1", "62"],
       mecanismes=("procédure_conseil",)),
)


# ────────────────────────────────────────────────────────────────────────────
# TITRE VIII — DE L'AUTORITÉ JUDICIAIRE (articles 64 à 66-1)
# ────────────────────────────────────────────────────────────────────────────

_TITRE_VIII: tuple[ArticleConstitution, ...] = (
    _a("64", "Le Président garant de l'indépendance de l'autorité judiciaire ; inamovibilité des magistrats du siège",
       "VIII", "autorité judiciaire", "Président ; CSM ; législateur organique",
       "« Le Président de la République est garant de l'indépendance de l'autorité judiciaire. Il est assisté "
       "par le Conseil supérieur de la magistrature. Une loi organique porte statut des magistrats. Les "
       "magistrats du siège sont inamovibles. »",
       regles=["inamovibilité des magistrats du siège (pas du parquet)",
               "le statut des magistrats est une loi organique (donc veto sénatorial possible)",
               "le Conseil constitutionnel n'est pas un organe de l'autorité judiciaire (jurisprudence)"],
       opportunites=["l'inamovibilité est le socle du contrôle du pouvoir : elle rend le juge capable "
                     "d'annuler l'exécutif sans risque de carrière",
                     "le Président, « garant », dispose d'une parole publique et d'un pouvoir de nomination "
                     "au CSM (65) : levier d'indépendance ou d'influence, selon l'usage"],
       contraintes=["le parquet reste hiérarchisé sous l'autorité du garde des Sceaux : politique pénale "
                    "pilotée par l'exécutif (réforme avortée de 2013)",
                    "le Gouvernement ne peut pas muter un magistrat du siège contre son gré",
                    "toute réforme du statut passe par la loi organique : procédure lourde (46)"],
       contre=["CSM (avis conformes et propositions, 65)", "cour de cassation", "Parlement (lois de "
               "programmation 34, budget 47)"],
       croise=["13", "65", "66", "34"],
       mecanismes=("independance_justice", "statut_magistrats"),
       leviers=("budget_justice", "independance_parquet")),
    _a("65", "Conseil supérieur de la magistrature : deux formations, nominations et discipline",
       "VIII", "autorité judiciaire", "CSM (16 membres)",
       "Le CSM comprend une formation compétente à l'égard des magistrats du siège et une formation "
       "compétente à l'égard de ceux du parquet. La formation « siège » est présidée par le premier "
       "président de la Cour de cassation, et comprend cinq magistrats du siège, un magistrat du parquet, "
       "un conseiller d'État, un avocat et six personnalités qualifiées désignées respectivement par le "
       "Président de la République, le président de l'AN et le président du Sénat (deux chacun, procédure de "
       "l'article 13 in fine). Elle fait des propositions pour certaines nominations et donne un avis "
       "conforme pour les autres magistrats du siège ; la formation « parquet » donne son avis sur les "
       "nominations du parquet ; elle statue comme conseil de discipline. Une plainte peut être adressée par "
       "tout justiciable au président de la formation concernée.",
       regles=["neuf membres par formation, présidée respectivement par le premier président de la Cour de "
               "cassation (siège) et par le procureur général près cette Cour (parquet) ; formation "
               "plénière dans les cas où les deux sont compétentes",
               "six personnalités qualifiées — deux désignées par le Président de la République, deux par "
               "le président de l'AN, deux par le président du Sénat — après la procédure de l'article 13 "
               "in fine (trois cinquièmes de votes négatifs cumulés = nomination refusée)",
               "le ministre de la Justice assiste à la formation compétente à l'égard des magistrats du "
               "parquet, pas à celle du siège",
               "droit de plainte direct du justiciable (loi organique du 27 juillet 2010)"],
       opportunites=["bloquer une personnalité qualifiée au CSM par un vote négatif massif est un levier "
                     "d'influence parlementaire sur la justice",
                     "le justiciable qui saisit le CSM transforme la discipline en contre-pouvoir citoyen",
                     "les avis publics du CSM sur la déontologie (2024-2026) sont des signaux exploitables "
                     "par le modèle (indépendance perçue)"],
       contraintes=["le président de la République ne peut pas imposer une nomination du siège contre "
                    "l'avis conforme du CSM",
                    "la réforme de la nomination du parquet (2013) a échoué faute de majorité au Congrès : "
                    "sans révision, le garde des Sceaux garde la main",
                    "le CSM ne peut être auto-saisi en discipline par un magistrat"],
       contre=["Cour de cassation (discipline en appel)", "Conseil constitutionnel (61 sur les lois "
               "organiques)", "Parlement (avis 3/5 sur les personnalités qualifiées)"],
       croise=["13", "64", "66", "34"],
       mecanismes=("csm_nomination", "plainte_justiciable"),
       leviers=("gouvernance_justice",)),
    _a("66", "Nul ne peut être arbitrairement détenu ; l'autorité judiciaire gardienne de la liberté individuelle",
       "VIII", "droits & libertés", "Autorité judiciaire",
       "« Nul ne peut être arbitrairement détenu. L'autorité judiciaire, gardienne de la liberté "
       "individuelle, assure le respect de ce principe dans les conditions prévues par la loi. »",
       regles=["garde à vue : 48 h maximum en matière criminelle (24 h en correctionnelle, renouvelables), "
               "contrôle du juge (code de procédure pénale)",
               "rétention administrative : délais fixés par la loi (CESEDA), contrôle judiciaire",
               "état d'urgence et état de siège déplacent une partie du contrôle vers l'administratif, sous "
               "censure du juge (36, 36-1)"],
       opportunites=["le contrôle juridictionnel des mesures de police (perquisitions administratives, "
                     "assignations) est le contre-pouvoir le plus rapide en période d'exception",
                     "les questions prioritaires (61-1) sur la détention sont fréquentes et font évoluer la "
                     "loi sans nouvelle majorité"],
       contraintes=["la loi fixe les conditions : le juge ne peut pas créer la règle",
                    "en période de pouvoirs exceptionnels (16), le contrôle est réduit mais non supprimé"],
       contre=["le législateur peut modifier les procédures dans les limites constitutionnelles",
               "le juge judiciaire est incompétent sur certains actes administratifs (répartition "
               "historique, contestée)"],
       croise=["16", "34", "36", "36-1", "61-1", "64", "66-1"],
       mecanismes=("liberte_individuelle", "controle_juge_liberte"),
       leviers=("effectifs_justice_penale",)),
    _a("66-1", "Abolition de la peine de mort",
       "VIII", "droits & libertés", "Constituant",
       "« Nul ne peut être condamné à la peine de mort. » (loi constitutionnelle du 19 février 2007)",
       regles=["valeur constitutionnelle, donc opposable au législateur et au pouvoir réglementaire",
               "interdit toute ratification d'un engagement international rétablissant la peine "
               "capitale (54)"],
       opportunites=["c'est l'exemple type d'un verrou de droit : il rend une politique non négociable et "
                     "donc non modélisable comme variable",
                     "fonde la position diplomatique française (moratoire universel)"],
       contraintes=["aucune révision ne peut rétablir la peine de mort sans toucher à l'article 66-1 et aux "
                    "engagements européens (protocole n° 13 CEDH)",
                    "le constituant lui-même a verrouillé la forme républicaine (89 al.5) mais pas ce "
                    "point : la révision reste juridiquement possible, politiquement exclue"],
       contre=["CEDH (protocole n° 13)", "droit de l'UE (Charte des droits fondamentaux, art. 2)"],
       croise=["53", "54", "66", "89"],
       mecanismes=("verrou_droit_fondamental",)),
)


# ────────────────────────────────────────────────────────────────────────────
# TITRE IX — LA HAUTE COUR (67-68) ; TITRE X — MEMBRES DU GOUVERNEMENT (68-1 à 68-3)
# ────────────────────────────────────────────────────────────────────────────

_TITRE_IX_X: tuple[ArticleConstitution, ...] = (
    _a("67", "Irresponsabilité du Président pour les actes accomplis en cette qualité",
       "IX", "haute cour", "Président de la République",
       "« Le Président de la République n'est pas responsable des actes accomplis en cette qualité, sous "
       "réserve des dispositions des articles 53-2 et 68. » Il ne peut, durant son mandat, devant aucune "
       "juridiction ou autorité administrative française, être requis de témoigner non plus que faire "
       "l'objet d'une action, d'un acte d'information, d'instruction ou de poursuite ; les délais de "
       "prescription sont suspendus ; les procédures peuvent être engagées à l'expiration d'un délai d'un "
       "mois suivant la cessation des fonctions.",
       regles=["irresponsabilité, pas immunité pénale au sens large : les actes détachables sont "
               "poursuivables par la voie de droit commun selon la jurisprudence (2024-2026 : contentieux "
               "des auditions libres)",
               "délai d'un mois après la cessation des fonctions", "prescription suspendue"],
       opportunites=["l'ancien président redevient justiciable un mois après la fin du mandat : le "
                     "contentieux post-mandature est un paramètre de risque politique réel",
                     "la réserve de l'article 68 (manquement aux devoirs) reste la seule exception en "
                     "fonctions"],
       contraintes=["impossibilité de contraindre le Président à témoigner pendant le mandat",
                    "les actes de campagne relèvent du juge ordinaire, pas de la Haute Cour (jurisprudence "
                    "constante depuis 2024)"],
       contre=["les juridictions de droit commun après le mandat", "la Haute Cour (68) pendant le mandat"],
       croise=["53-2", "68", "26", "68-1"],
       mecanismes=("irresponsabilite_presidentielle", "procédure_haute_cour"),
       leviers=("regime_immunites",)),
    _a("68", "Destitution du Président devant la Haute Cour",
       "IX", "haute cour", "Parlement réuni en Haute Cour",
       "Le Président ne peut être destitué qu'en cas de manquement à ses devoirs manifestement incompatible "
       "avec l'exercice de son mandat ; la destitution est prononcée par le Parlement constitué en Haute "
       "Cour. La proposition de réunion adoptée par une assemblée est aussitôt transmise à l'autre, qui se "
       "prononce dans les quinze jours. La Haute Cour est présidée par le président de l'Assemblée "
       "nationale ; elle statue dans un délai d'un mois, à bulletins secrets. Les décisions sont prises à la "
       "majorité des deux tiers des membres composant l'assemblée concernée ou la Haute Cour ; toute "
       "délégation de vote est interdite ; seuls les votes favorables sont recensés.",
       regles=["proposition de réunion adoptée par chaque assemblée à la majorité des deux tiers de ses "
               "membres (385 députés sur 577 ; 232 sénateurs sur 348)",
               "la seconde assemblée se prononce dans les quinze jours de la transmission",
               "la Haute Cour statue dans le mois, à bulletins secrets, à la majorité des deux tiers des "
               "membres la composant",
               "aucune délégation de vote ; seuls les votes favorables sont recensés",
               "la procédure n'a jamais abouti depuis 2008 : engagée en 2021, elle a échoué au Sénat"],
       opportunites=["la révision du 1er juillet 2008 a remplacé la « haute trahison » par un manquement "
                     "apprécié par les assemblées elles-mêmes, avec une procédure contradictoire (loi "
                     "organique du 29 novembre 2011)",
                     "le double filtre (deux assemblées, puis la Haute Cour) en fait une arme de sanction "
                     "utilisable seulement en cas de coalition très large : c'est sa fonction dissuasive"],
       contraintes=["seuil quasi inatteignable sans effondrement de la majorité présidentielle : c'est le "
                    "sens du verrou (le constituant a voulu une procédure d'exception)",
                    "le manquement doit être « manifestement incompatible » : appréciation politique, non "
                    "juridique",
                    "aucun recours : la décision est immédiate et emporte inéligibilité"],
       contre=["les deux tiers des deux assemblées", "le Sénat (filtre politique, en séance publique, dans "
               "les quinze jours)",
               "le Conseil constitutionnel (incompétent sur l'opportunité, compétent sur la loi organique "
               "du 29 novembre 2011)"],
       croise=["7", "26", "65", "67", "68-1", "71-1"],
       mecanismes=("haute_cour", "procedure_destitution"),
       leviers=("regime_immunites",)),
    _a("68-1", "Responsabilité pénale des membres du Gouvernement devant la CJR",
       "X", "haute cour", "Cour de justice de la République",
       "« Les membres du Gouvernement sont pénalement responsables des actes accomplis dans l'exercice de "
       "leurs fonctions et qualifiés crimes ou délits au moment où ils ont été commis. Ils sont jugés par la "
       "Cour de justice de la République. » La CJR est liée par la définition des crimes et délits et par la "
       "détermination des peines résultant de la loi.",
       regles=["compétence limitée aux actes « dans l'exercice des fonctions »",
               "les faits antérieurs ou détachables relèvent du droit commun",
               "la CJR a été créée par la loi constitutionnelle du 27 juillet 1993 (révision), réformée en "
               "2007 (suppression de la « délibération préalable »)"],
       opportunites=["la plainte de tout justiciable auprès de la commission des requêtes ouvre une voie de "
                     "contrôle pénal de l'exécutif : contre-pouvoir individuel",
                     "la CJR statue en premier et dernier ressort : la procédure est rapide (mais "
                     "l'absence d'appel est critiquée, réformes proposées en 2025-2026)"],
       contraintes=["pas d'appel ni de cassation sur le fond (cassation possible pour vice de procédure)",
                    "la qualification « d'exercice des fonctions » filtre l'essentiel des plaintes "
                    "(classement très fréquent par la commission des requêtes)",
                    "les faits couverts par la prescription ne peuvent plus être jugés",
                    "en pratique la très grande majorité des plaintes est classée par la commission des "
                    "requêtes"],
       contre=["commission des requêtes (classement)", "Conseil constitutionnel (61 sur la loi "
               "organique)", "Parlement (éventuelle réforme de la CJR : révision 89)"],
       croise=["23", "26", "67", "68-2", "68-3"],
       mecanismes=("cjr", "plainte_ministre"),
       leviers=("probité_vie_publique",)),
    _a("68-2", "Composition et saisine de la CJR",
       "X", "haute cour", "CJR (15 juges) ; commission des requêtes",
       "La CJR comprend quinze juges : douze parlementaires élus en leur sein et en nombre égal par "
       "l'Assemblée nationale et par le Sénat après chaque renouvellement, et trois magistrats du siège à la "
       "Cour de cassation, dont l'un préside. Toute personne qui se prétend lésée par un crime ou délit "
       "commis par un membre du Gouvernement dans l'exercice de ses fonctions peut porter plainte auprès d'une "
       "commission des requêtes, qui ordonne soit le classement, soit la transmission au procureur général "
       "près la Cour de cassation aux fins de saisine ; celui-ci peut aussi saisir d'office la CJR sur avis "
       "conforme de la commission.",
       regles=["quinze juges : douze parlementaires élus en nombre égal par chaque assemblée (six et six) "
               "plus trois magistrats du siège à la Cour de cassation, dont l'un préside",
               "commission des requêtes de six membres (trois magistrats hors hiérarchie, un conseiller "
               "d'État, un conseiller maître à la Cour des comptes, un avocat), inamovibles",
               "pas de jury populaire, pas de juridiction du second degré"],
       opportunites=["une plainte documentée sur un acte ministériel (gestion de crise, police sanitaire, "
                     "ordre public) reste le seul moyen, pour un justiciable, de poursuivre pénalement un "
                     "ministre pour ses actes de fonction",
                     "la composition parlementaire de la Cour (six députés, six sénateurs) rend la "
                     "procédure sensible au rapport de forces des assemblées : variable politique "
                     "modélisable"],
       contraintes=["classement très fréquent par la commission des requêtes : le filtre est un verrou "
                    "majeur",
                    "la responsabilité pénale individuelle n'implique pas la responsabilité politique : un "
                    "ministre condamné n'est pas automatiquement déchu",
                    "la CJR ne peut être saisie pour des actes collectifs du conseil des ministres"],
       contre=["commission des requêtes (classement)", "président de la CJR (filtrage de la procédure)",
               "Conseil constitutionnel (61)"],
       croise=["68-1", "68-3", "26", "32"],
       mecanismes=("cjr",)),
    _a("68-3", "Application rétroactive des règles de la CJR",
       "X", "haute cour", "—",
       "« Les dispositions du présent titre sont applicables aux faits commis avant son entrée en vigueur. » "
       "(dérogation constitutionnelle au principe de non-rétroactivité de la loi pénale plus sévère, "
       "justifiée par la nature procédurale de la règle)",
       regles=["exception écrite à l'article 8 de la DDHC (légalité des infractions) limitée à la "
               "compétence juridictionnelle"],
       opportunites=["rappelle que le constituant peut, explicitement, lever une garantie pour la procédure "
                     "(et non pour le fond) : technique utile pour réformer une juridiction sans amnistie"],
       contraintes=["ne peut pas créer d'incrimination rétroactive", "ne s'applique qu'au titre X"],
       contre=["Conseil constitutionnel (contrôle du respect de l'art. 8 DDHC)", "CEDH (art. 7)"],
       croise=["68-1", "68-2", "DDHC-8"],
       mecanismes=("retroactivite_procedure",)),
)


# ────────────────────────────────────────────────────────────────────────────
# TITRE XI — CESE (69-71) ; TITRE XI bis — DÉFENSEUR DES DROITS (71-1)
# ────────────────────────────────────────────────────────────────────────────

_TITRE_XI: tuple[ArticleConstitution, ...] = (
    _a("69", "Avis du CESE sur les projets et propositions ; saisine par pétition",
       "XI", "démocratie participative", "CESE (175 membres, plafond 233)",
       "« Le Conseil économique, social et environnemental, saisi par le Gouvernement, donne son avis sur "
       "les projets de loi, d'ordonnance ou de décret ainsi que sur les propositions de lois qui lui sont "
       "soumis. » Un membre peut être désigné pour exposer l'avis devant les assemblées. Le CESE « peut "
       "être saisi par voie de pétition dans les conditions fixées par une loi organique » et fait connaître "
       "au Gouvernement et au Parlement les suites qu'il propose.",
       regles=["avis rendu dans un délai d'un mois (deux mois sur pétition ou autosaisine)",
               "pétition recevable si elle est soutenue par cent cinquante mille personnes (loi organique du "
               "14 avril 2010)",
               "la Conférence des présidents du CESE examine la recevabilité avant enregistrement"],
       opportunites=["la pétition citoyenne au CESE est la seule procédure nationale directe inscrite dans "
                     "la Constitution : un levier RIC-adjacent immédiatement mobilisable",
                     "un avis du CESE, public, pèse dans la négociation sociale et dans la préparation d'une "
                     "loi (70)",
                     "la désignation d'un rapporteur devant le Parlement donne une tribune aux corps "
                     "intermédiaires"],
       contraintes=["avis consultatifs : le Gouvernement n'est pas lié (sauf saisine obligatoire pour les "
                    "textes à caractère économique, social ou environnemental, art. 70 al.2)",
                    "le bureau du CESE a refusé d'enregistrer certaines pétitions (2023-2025), ce qui a "
                    "ouvert un débat contentieux : la procédure est encadrée mais peu sûre",
                    "aucun veto, aucune suspension du calendrier législatif"],
       contre=["le Gouvernement (saisine, suites données)", "le Parlement (peut ignorer l'avis)",
               "le Conseil constitutionnel (61 sur la loi organique des pétitions)"],
       croise=["70", "71", "71-1", "34", "72-1"],
       strates=["National", "Local"],
       mecanismes=("petition_cese", "avis_cese"),
       leviers=("democratie_participative",)),
    _a("70", "Saisine facultative du CESE ; obligation pour les plans et projets de loi de programmation",
       "XI", "contrôle & évaluation", "Gouvernement ; Parlement",
       "« Le Conseil économique, social et environnemental peut être consulté par le Gouvernement et le "
       "Parlement sur tout problème de caractère économique, social ou environnemental. Le Gouvernement peut "
       "également le consulter sur les projets de loi de programmation définissant les orientations "
       "pluriannuelles des finances publiques. Tout plan ou tout projet de loi de programmation à caractère "
       "économique, social ou environnemental lui est soumis pour avis. »",
       regles=["saisine obligatoire pour les plans et projets de programmation (alinéa 2)",
               "loi organique du 28 décembre 2012 : les lois de programmation des finances publiques sont "
               "transmises au CESE",
               "la consultation du CESE n'interrompt pas la navette"],
       opportunites=["faire saisir le CESE par le Parlement (senatus ou motion) produit un avis public qui "
                     "légitime une position sociale sans contraindre le Gouvernement",
                     "l'obligation de saisine sur la programmation des finances publiques est un point de "
                     "passage pour une coalition sociale (syndicats + employeurs) dans un débat budgétaire"],
       contraintes=["avis, pas décision : le calendrier n'est pas suspendu (sauf auto-saisine du "
                    "Gouvernement)",
                    "le CESE ne peut pas être saisi par les citoyens directement (sauf la voie de la "
                    "pétition, art. 69)"],
       contre=["le Gouvernement (choix d'organiser l'avis avant ou après dépôt)", "le Parlement (adoption "
               "du texte en dépit de l'avis)"],
       croise=["69", "34", "47", "71"],
       mecanismes=("consultation_cee", "loi_programmation"),
       leviers=("dialogue_social",)),
    _a("71", "Composition et fonctionnement du CESE fixés par loi organique",
       "XI", "organisation", "Législateur organique",
       "« La composition du Conseil économique, social et environnemental, dont le nombre de membres ne peut "
       "excéder deux cent trente-trois, et ses règles de fonctionnement sont fixées par une loi organique. »",
       regles=["plafond constitutionnel de deux cent trente-trois membres ; le Conseil compte "
               "cent soixante-quinze membres en activité (écart à documenter dans le modèle)",
               "trois collèges d'environ 51 % (vie démocratique et cohésion sociale), 34 % (dialogue "
               "social, économique et professionnel) et 15 % (environnements et territoires)",
               "mandat de cinq ans renouvelable ; membres désignés par décret, pour la majeure partie sur "
               "proposition des organisations représentatives"],
       opportunites=["réformer la composition du CESE (tirage au sort partiel, citoyens) est possible par "
                     "loi organique : c'est la porte d'entrée institutionnelle d'une assemblée citoyenne "
                     "sans révision de la Constitution",
                     "augmenter le nombre de membres jusqu'au plafond de deux cent trente-trois permettrait "
                     "d'accueillir des collèges nouveaux sans réviser la Constitution",
                     "le modèle retient 175 membres (simulateur/model.py) : l'écart avec le plafond "
                     "constitutionnel est une marge de réforme à documenter"],
       contraintes=["toute modification de la composition relève de la loi organique : accord du "
                    "Parlement + conformité du Conseil constitutionnel (46)",
                    "la nomination des membres par décret (sur proposition des organisations) reste "
                    "politique : l'indépendance est relative"],
       contre=["Conseil constitutionnel (61 : obligation de saisine)", "le Gouvernement (décrets de "
               "nomination)"],
       croise=["69", "70", "25", "46"],
       mecanismes=("composition_cee", "tirage_au_sort_assemblee"),
       leviers=("convention_citoyenne", "reforme_cee")),
    _a("71-1", "Défenseur des droits",
       "XI bis", "droits & libertés",
       "Défenseur des droits (révision du 23 juillet 2008 ; reprend le Médiateur de la République, la "
       "HALDE, le Défenseur des enfants et la CNDSI)",
       "« Le Défenseur des droits veille au respect des droits et libertés par les administrations de "
       "l'État, les collectivités territoriales, les établissements publics, ainsi que par tout organisme "
       "investi d'une mission de service public […] Il peut être saisi, dans les conditions prévues par la "
       "loi organique, par toute personne s'estimant lésée […] Il peut se saisir d'office. » Il est nommé "
       "pour six ans non renouvelables après la procédure de l'article 13 et rend compte de son activité au "
       "Président de la République et au Parlement.",
       regles=["mandat de 6 ans non renouvelable", "procédure de l'article 13 in fine : 3/5 de votes "
               "négatifs = blocage", "incompatibilité avec les fonctions de ministre ou parlementaire",
               "saisine libre par toute personne (gratuite, sans formalisme)",
               "plus de cent mille saisines directes par an, sans frais ni formalisme (rapports d'activité "
               "2024-2025)"],
       opportunites=["la saisine gratuite et directe du Défenseur des droits est le contre-pouvoir le plus "
                     "accessible du paysage institutionnel : aucun avocat, aucun délai",
                     "ses décisions (délibérations) et ses « observations devant le juge » font évoluer la "
                     "jurisprudence sans loi",
                     "un parlementaire peut le saisir pour mission sur un thème donné, et son rapport annuel "
                     "alimente l'évaluation des politiques publiques (24, 47-2)"],
       contraintes=["avis et recommandations non contraignants : seule l'audience du juge l'est",
                    "il ne peut être saisi d'une affaire en cours devant un juge que dans les conditions "
                    "prévues par la loi organique",
                    "la procédure de nomination laisse un pouvoir discrétionnaire au Président : l'avis "
                    "parlementaire n'a bloqué personne à ce jour"],
       contre=["le juge (il ne se substitue pas)", "le Gouvernement (suit ou non les recommandations)",
               "les commissions des deux assemblées (avis de nomination)"],
       croise=["13", "24", "47-2", "61-1", "69"],
       strates=["National", "Local", "Europe"],
       mecanismes=("defenseur_droits", "saisine_citoyenne"),
       leviers=("acces_droit", "probité_vie_publique")),
)




# ────────────────────────────────────────────────────────────────────────────
# TITRE XII — DES COLLECTIVITÉS TERRITORIALES (articles 72 à 75-1)
# ────────────────────────────────────────────────────────────────────────────

_TITRE_XII: tuple[ArticleConstitution, ...] = (
    _a("72", "Collectivités de la République ; administration libre ; dérogation expérimentale",
       "XII", "collectivités", "Loi ; loi organique ; collectivités territoriales",
       "Les collectivités territoriales de la République sont les communes, les départements, les régions, "
       "les collectivités à statut particulier et les collectivités d'outre-mer régies par l'article 74 ; "
       "toute autre collectivité est créée par la loi, le cas échéant en lieu et place d'une ou plusieurs "
       "collectivités. Elles « ont vocation à prendre les décisions pour l'ensemble des compétences qui "
       "peuvent le mieux être mises en œuvre à leur échelon ». Dans les conditions prévues par la loi, elles "
       "s'administrent librement par des conseils élus et disposent d'un pouvoir réglementaire pour l'exercice "
       "de leurs compétences. Dans les conditions prévues par la loi organique, et sauf lorsque sont en cause "
       "les conditions essentielles d'exercice d'une liberté publique ou d'un droit constitutionnellement "
       "garanti, elles peuvent, lorsque la loi ou le règlement l'a prévu, déroger à titre expérimental et pour "
       "un objet et une durée limités aux règles législatives ou réglementaires qui régissent l'exercice de "
       "leurs compétences. Aucune collectivité ne peut exercer une tutelle sur une autre ; la loi peut "
       "autoriser l'une d'elles ou un groupement à organiser les modalités de leur action commune. Dans les "
       "collectivités de la République, le représentant de l'État a la charge des intérêts nationaux, du "
       "contrôle administratif et du respect des lois.",
       regles=["cinq catégories de collectivités énumérées ; toute autre est créée par la loi",
               "pouvoir réglementaire local reconnu par la Constitution elle-même",
               "la dérogation expérimentale suppose une habilitation (loi ou règlement), un objet et une "
               "durée limités",
               "aucune tutelle d'une collectivité sur une autre",
               "le préfet garde le contrôle administratif et le respect des lois"],
       opportunites=["la clause de dérogation expérimentale est la porte ouverte au « droit à l'essai » "
                     "réclamé par les territoires : possible sans révision, par simple habilitation",
                     "créer une collectivité à statut particulier par la loi (2015 : Alsace, Guyane, "
                     "Martinique ; 2018 : Corse) sans toucher à la Constitution",
                     "le pouvoir réglementaire local permet d'ajuster urbanisme, mobilité et organisation "
                     "scolaire sans loi nouvelle",
                     "l'interdiction de tutelle laisse entière la liberté des coopérations volontaires "
                     "(établissements publics de coopération intercommunale, conventions territoriales)"],
       contraintes=["les conditions essentielles d'exercice d'une liberté publique ne peuvent être "
                    "expérimentées localement",
                    "aucune délibération locale ne peut contredire la loi hors habilitation : l'acte serait "
                    "annulé",
                    "toute création ou extension de compétence doit s'accompagner de ressources (72-2)",
                    "la libre administration n'interdit pas un contrôle de légalité renforcé"],
       contre=["le représentant de l'État (déféré au juge administratif)",
               "le juge administratif (annulation des actes illégaux)",
               "le Conseil constitutionnel (61 sur la loi, 61-1 par la QPC)",
               "les électeurs de la collectivité (72-1 : pétition, référendum local)"],
       strates=["Local", "National", "Transversal"],
       croise=["34", "37", "37-1", "72-1", "72-2", "72-4", "73", "74", "88-1"],
       mecanismes=("decentralisation", "experimentalisation_locale", "controle_legalite",
                   "pouvoir_reglementaire_local"),
       leviers=("autonomie_locale", "differenciation_outre_mer")),
    _a("72-1", "Pétition locale, référendum local, consultation sur les collectivités",
       "XII", "démocratie participative", "Électeurs de chaque collectivité ; loi et loi organique",
       "La loi fixe les conditions dans lesquelles les électeurs de chaque collectivité territoriale peuvent, "
       "par l'exercice du droit de pétition, demander l'inscription à l'ordre du jour de l'assemblée "
       "délibérante de cette collectivité d'une question relevant de sa compétence. Dans les conditions "
       "prévues par la loi organique, les projets de délibération ou d'acte relevant de la compétence d'une "
       "collectivité territoriale peuvent, à son initiative, être soumis, par la voie du référendum, à la "
       "décision des électeurs de cette collectivité. Lorsqu'il est envisagé de créer une collectivité dotée "
       "d'un statut particulier ou de modifier son organisation, il peut être décidé par la loi de consulter "
       "les électeurs inscrits dans les collectivités intéressées ; la modification des limites des "
       "collectivités territoriales peut également donner lieu à consultation dans les conditions prévues par "
       "la loi.",
       regles=["pétition : seuil de signatures, conditions d'examen et de publicité fixés par la loi "
               "(code général des collectivités territoriales), non par la Constitution",
               "référendum local : organisé à l'initiative de la collectivité, dans les conditions de la loi "
               "organique",
               "un projet soumis à référendum ne peut être abandonné par l'assemblée que dans les cas et "
               "délais fixés par la loi organique",
               "consultation sur création, organisation ou limites : la loi peut la décider — elle est "
               "obligatoire dans les cas des articles 73 et 72-4"],
       opportunites=["le référendum d'initiative locale existe déjà en droit : c'est un levier mobilisable "
                     "par loi organique, à distinguer dans le modèle du RIC national qui exigerait l'article "
                     "11 ou une révision",
                     "la pétition d'ordre du jour est l'outil le moins coûteux d'agenda démocratique local",
                     "les consultations de redécoupage (fusions de communes, régions) montrent que le "
                     "consentement local réduit fortement le contentieux"],
       contraintes=["le référendum local ne peut porter que sur un acte de la compétence de la collectivité",
                    "rien dans la Constitution n'oblige le législateur à créer un référendum national "
                     "d'initiative citoyenne : l'article 72-1 ne le couvre pas",
                    "une consultation informelle n'a pas de valeur juridique contraignante pour "
                     "l'assemblée, ce que le Conseil constitutionnel rappelle constamment"],
       contre=["l'assemblée délibérante (elle arrête l'ordre du jour et peut écarter une pétition "
               "irrégulière)", "le représentant de l'État (déféré de l'acte soumis à référendum)",
               "le juge administratif (légalité des conditions d'organisation)"],
       strates=["Local", "National"],
       croise=["3", "27", "34", "37-1", "72", "72-2", "72-4", "89"],
       mecanismes=("petition_72_1", "referendum_local", "consultation_red_ecoupage"),
       leviers=("reforme_ric", "referendum_local_seuil", "referendum_local")),
    _a("72-2", "Ressources propres, part déterminante, péréquation",
       "XII", "budget", "Législateur ; loi organique ; collectivités",
       "Les collectivités territoriales bénéficient de ressources dont elles peuvent disposer librement dans "
       "les conditions fixées par la loi. Elles peuvent recevoir tout ou partie du produit des impositions de "
       "toutes natures ; la loi peut les autoriser à en fixer l'assiette et le taux dans les limites "
       "qu'elle détermine. Les recettes fiscales et les autres ressources propres des collectivités "
       "territoriales représentent, pour chaque catégorie de collectivités, une part déterminante de "
       "l'ensemble de leurs ressources ; la loi organique fixe les conditions de mise en œuvre de cette "
       "règle. Tout transfert de compétences entre l'État et les collectivités s'accompagne de ressources "
       "équivalentes à celles qui étaient consacrées à leur exercice ; toute création ou extension de "
       "compétences augmentant les dépenses est accompagnée de ressources déterminées par la loi. La loi "
       "prévoit des dispositifs de péréquation destinés à favoriser l'égalité entre les collectivités.",
       regles=["« part déterminante » de ressources propres : planchers par catégorie fixés par la loi "
               "organique du 29 juillet 2004 (ordre de grandeur : environ 60 % pour les communes, 58 % pour "
               "les départements, 59 % pour les régions), avec un mécanisme de fraction dynamique depuis la "
               "suppression progressive de la CVAE",
               "ressources équivalentes pour tout transfert de compétence",
               "ressources déterminées par la loi pour toute création ou extension de compétence",
               "obligation constitutionnelle de péréquation"],
       opportunites=["l'exigence de ressources propres est une arme contre la recentralisation par décret : "
                     "une charge nouvelle sans financement est inconstitutionnelle",
                     "la part déterminante est un indicateur chiffré directement simulable : le modèle suit "
                     "son évolution comme mesure de l'autonomie réelle",
                     "la péréquation, verticale et horizontale, peut être renforcée par simple loi"],
       contraintes=["la loi fixe les limites : aucune autonomie fiscale pleine sans habilitation expresse",
                    "une réforme des dotations qui détruirait la part déterminante d'une catégorie de "
                    "collectivités est censurable par le Conseil constitutionnel",
                    "l'État ne peut pas compenser une compétence nouvelle par une seule hausse de la "
                    "dotation globale de fonctionnement si elle n'est pas « déterminée par la loi » de façon "
                    "suffisante",
                    "les amendements parlementaires créant une charge locale sont irrecevables (40)"],
       contre=["le législateur (vote les ressources)", "la loi organique (part déterminante)",
               "la Cour des comptes et les chambres régionales et territoriales (47-2)",
               "les électeurs locaux (impôt local)"],
       strates=["Local", "National", "Transversal"],
       croise=["34", "40", "47", "72", "73", "74"],
       mecanismes=("autonomie_financiere_locale", "perequation", "transfert_competences"),
       leviers=("part_ressources_propres", "effort_perequation")),
    _a("72-3", "Populations d'outre-mer ; rattachement aux articles 73 et 74",
       "XII", "outre-mer", "Législateur",
       "« La République reconnaît, au sein du peuple français, les populations d'outre-mer, dans un idéal "
       "commun de liberté, d'égalité et de fraternité. » La Guadeloupe, la Guyane, la Martinique, La Réunion, "
       "Mayotte, Saint-Barthélemy, Saint-Martin, Saint-Pierre-et-Miquelon, les îles Wallis et Futuna et la "
       "Polynésie française sont régies par l'article 73 pour les départements et les régions d'outre-mer et "
       "pour les collectivités créées en application du dernier alinéa de l'article 73, et par l'article 74 "
       "pour les autres collectivités. Le statut de la Nouvelle-Calédonie est régi par le titre XIII. La loi "
       "détermine le régime législatif et l'organisation particulière des Terres australes et antarctiques "
       "françaises et de Clipperton. (créé par la loi constitutionnelle du 28 mars 2003)",
       regles=["dix collectivités ultramarines énumérées par la Constitution",
               "partage entre article 73 (identité législative et adaptations) et article 74 (statut "
               "organique)",
               "la Nouvelle-Calédonie relève du titre XIII, hors du champ du titre XII",
               "les Terres australes et antarctiques françaises et Clipperton relèvent de la simple loi"],
       opportunites=["toute réforme institutionnelle ultramarine commence par identifier l'article "
                     "applicable : c'est la grille qui distingue une habilitation (73) d'un statut (74)",
                     "l'article 72-3 ancre l'outre-mer dans la Constitution et limite une lecture purement "
                     "budgétaire de la réforme"],
       contraintes=["aucune collectivité nouvelle hors liste sans respecter les articles 72, 73 et 74",
                    "le passage de l'article 74 à l'article 73 suppose le consentement préalable des "
                    "électeurs (72-4)",
                    "l'égalité devant la loi reste le principe : les adaptations doivent être justifiées par "
                    "des caractéristiques et contraintes particulières"],
       contre=["les électeurs des collectivités concernées (72-4)", "le Conseil constitutionnel (61)",
               "le Sénat (24 : représentation des collectivités ; 39 : première saisine territoriale)"],
       strates=["Local", "National", "Europe", "Mondial"],
       croise=["72", "73", "74", "76", "77", "88-1"],
       mecanismes=("statut_outre_mer",),
       leviers=("outre_mer_statut",)),
    _a("72-4", "Changement de régime 73 ↔ 74 : consentement préalable des électeurs",
       "XII", "outre-mer", "Électeurs de la collectivité ; loi organique ; Président",
       "Aucun changement, pour tout ou partie de l'une des collectivités mentionnées au deuxième alinéa de "
       "l'article 72-3, de l'un vers l'autre des régimes prévus par les articles 73 et 74 ne peut intervenir "
       "sans que le consentement des électeurs de la collectivité ou de la partie de collectivité intéressée "
       "ait été préalablement recueilli dans les conditions prévues à l'alinéa suivant ; ce changement est "
       "décidé par une loi organique. Le Président de la République, sur proposition du Gouvernement pendant "
       "la durée des sessions ou sur proposition conjointe des deux assemblées publiées au Journal officiel, "
       "peut décider de consulter les électeurs d'une collectivité territoriale située outre-mer sur une "
       "question relative à son organisation, à ses compétences ou à son régime législatif. Lorsque la "
       "consultation porte sur un changement prévu à l'alinéa précédent et est organisée sur proposition du "
       "Gouvernement, celui-ci fait devant chaque assemblée une déclaration qui est suivie d'un débat.",
       regles=["consentement préalable des électeurs : la consultation ne peut pas intervenir après la "
               "décision",
               "décision prise par loi organique (censure obligatoire, 46 al.5 et 61)",
               "initiative présidentielle de consultation : sur proposition du Gouvernement en session, ou "
               "sur proposition conjointe des deux assemblées",
               "déclaration du Gouvernement suivie d'un débat dans chaque assemblée lorsque la consultation "
               "porte sur un changement de régime"],
       opportunites=["c'est le mécanisme constitutionnel d'autodétermination interne pour les collectivités "
                     "ultramarines de droit commun : mobilisable sans révision",
                     "la consultation peut porter sur l'organisation, les compétences ou le régime "
                     "législatif : le périmètre est large"],
       contraintes=["une réforme du régime sans consultation préalable est inconstitutionnelle",
                    "une consultation organisée hors ce cadre n'a pas la même valeur juridique",
                    "les listes électorales retenues pour la consultation font contentieux (cf. article 77 "
                    "en Nouvelle-Calédonie)"],
       contre=["les électeurs de la collectivité (consentement requis)", "le Conseil constitutionnel (61)",
               "le Sénat (veto sur les lois organiques relatives à son organisation, 46 al.4)"],
       strates=["Local", "National"],
       croise=["3", "11", "34", "46", "72-3", "73", "74", "77", "89"],
       mecanismes=("consultation_outre_mer", "changement_regime"),
       leviers=("outre_mer_statut", "consultation_autodetermination")),
    _a("73", "Départements et régions d'outre-mer : adaptations et habilitations",
       "XII", "outre-mer", "Collectivités régies par l'article 73 ; loi et règlement",
       "Dans les départements et les régions d'outre-mer, les lois et règlements sont applicables de plein "
       "droit et peuvent faire l'objet d'adaptations tenant aux caractéristiques et contraintes particulières "
       "de ces collectivités, décidées par ces collectivités si elles y ont été habilitées, selon le cas, par "
       "la loi ou par le règlement. Par dérogation et pour tenir compte de leurs spécificités, elles peuvent "
       "être habilitées à fixer elles-mêmes les règles applicables sur leur territoire dans un nombre limité "
       "de matières pouvant relever du domaine de la loi ou du règlement — à l'exclusion de la nationalité, "
       "des droits civiques, des garanties des libertés publiques, de l'état et de la capacité des personnes, "
       "de l'organisation de la justice, du droit pénal, de la procédure pénale, de la politique étrangère, "
       "de la défense, de la sécurité et de l'ordre publics, de la monnaie, du crédit et des changes, ainsi "
       "que du droit électoral, énumération précisée et complétée par la loi organique. Cette faculté n'est "
       "pas applicable au département et à la région de La Réunion. Les habilitations sont décidées à la "
       "demande de la collectivité, dans les conditions prévues par une loi organique, et ne peuvent "
       "intervenir lorsque sont en cause les conditions essentielles d'exercice d'une liberté publique ou d'un "
       "droit constitutionnellement garanti. La création d'une collectivité se substituant à un département "
       "et une région d'outre-mer, ou l'institution d'une assemblée délibérante unique, ne peut intervenir "
       "sans le consentement des électeurs selon les formes du second alinéa de l'article 72-4.",
       regles=["identité législative de principe ; adaptation seulement sur habilitation",
               "liste constitutionnelle de matières fermées à l'habilitation (nationalité à droit électoral)",
               "exception expresse pour La Réunion",
               "assemblée unique ou collectivité unique : consentement des électeurs requis",
               "Mayotte est régie par l'article 73 depuis la départementalisation de 2011"],
       opportunites=["l'habilitation « à la demande » permet une différenciation normative sans réécrire la "
                     "Constitution : c'est le cadre de la loi 3DS du 21 février 2022",
                     "fixer localement des règles relevant du domaine de la loi (fiscalité locale, "
                     "urbanisme, droit social adapté) est un levier de politique économique territoriale",
                     "les zonages fiscaux ultramarins (octroi de mer, zones franches globales d'activité) "
                     "relèvent de cette logique d'adaptation"],
       contraintes=["impossible d'adapter le droit électoral, la justice, le droit pénal, la monnaie ou les "
                    "garanties des libertés publiques",
                    "l'habilitation doit être demandée par la collectivité : l'État ne peut pas l'imposer",
                    "une habilitation imprécise dans son objet ou sa durée est censurée",
                    "les délibérations prises sur habilitation sont contrôlées par le Conseil d'État, puis "
                    "par le Conseil constitutionnel une fois ratifiées par la loi"],
       contre=["le Conseil constitutionnel (61 ; 61-1 sur les dispositions ratifiées)",
               "le Conseil d'État (délibérations non ratifiées)",
               "les électeurs (72-4)", "l'État (compétences régaliennes)"],
       strates=["Local", "National", "Europe"],
       croise=["34", "37", "72", "72-3", "72-4", "74", "74-1", "88-1"],
       mecanismes=("habilitation_legislative", "differenciation_normative"),
       leviers=("differenciation_outre_mer", "habilitation_73")),
    _a("74", "Collectivités d'outre-mer : statut fixé par la loi organique",
       "XII", "outre-mer", "Législateur organique ; assemblée délibérante de la collectivité",
       "Les collectivités d'outre-mer régies par l'article 74 ont un statut qui tient compte des intérêts "
       "propres de chacune d'elles au sein de la République. Ce statut est défini par une loi organique, prise "
       "après avis de l'assemblée délibérante, qui fixe les conditions d'applicabilité des lois et règlements, "
       "les compétences de la collectivité (le transfert de compétences de l'État ne peut porter sur les "
       "matières énumérées au quatrième alinéa de l'article 73), les règles d'organisation et de "
       "fonctionnement des institutions et le régime électoral de son assemblée délibérante, ainsi que les "
       "conditions dans lesquelles ses institutions sont consultées sur les projets et propositions de loi, les "
       "projets d'ordonnance ou de décret et la ratification d'engagements internationaux dans les matières "
       "relevant de sa compétence. Pour les collectivités dotées de l'autonomie, la loi organique peut "
       "également prévoir un contrôle juridictionnel spécifique du Conseil d'État sur certaines catégories "
       "d'actes de l'assemblée délibérante, la faculté pour celle-ci de modifier une loi promulguée "
       "postérieurement à l'entrée en vigueur du statut lorsque le Conseil constitutionnel a constaté "
       "qu'elle intervenait dans son domaine de compétence, des mesures justifiées par les nécessités locales "
       "en matière d'accès à l'emploi, de droit d'établissement et de protection du patrimoine foncier, et la "
       "participation de la collectivité, sous le contrôle de l'État, à l'exercice des compétences que l'État "
       "conserve. Les autres modalités sont définies et modifiées par la loi après consultation de "
       "l'assemblée délibérante.",
       regles=["statut = loi organique, prise après avis de l'assemblée délibérante (avis obligatoire : son "
               "absence ou sa précipitation a déjà entraîné la censure)",
               "compétences de l'État non transférables : mêmes matières qu'au quatrième alinéa de "
               "l'article 73",
               "consultation de l'assemblée délibérante sur les textes particuliers et sur la ratification "
               "d'engagements internationaux dans ses compétences",
               "mesures locales possibles : accès à l'emploi, droit d'établissement, foncier",
               "contrôle juridictionnel spécifique du Conseil d'État pour les collectivités autonomes, avec "
               "des délais de déféré particuliers fixés par chaque statut"],
       opportunites=["la voie du statut organique est celle de l'autonomie « à la carte » (Saint-Pierre-et-"
                     "Miquelon 2003, Polynésie française, Wallis-et-Futuna, Saint-Barthélemy et Saint-Martin "
                     "2007)",
                     "la faculté de modifier une loi promulguée après l'entrée en vigueur du statut, après "
                     "constat du Conseil constitutionnel, est une dérogation unique : la collectivité "
                     "devient législateur dans son domaine",
                     "les mesures locales d'accès à l'emploi et de protection foncière répondent à la "
                     "tension immobilière et sociale ultramarine"],
       contraintes=["tout changement de nature du statut relève de la loi organique : accord des deux "
                    "assemblées (46) et censure obligatoire (61)",
                    "la participation aux compétences conservées par l'État reste « sous le contrôle de "
                    "l'État » et dans le respect des garanties nationales des libertés publiques",
                    "l'avis de la collectivité n'est pas conforme : le contourner est un risque politique, "
                    "pas un veto juridique",
                    "les délais de déféré et de jugement relèvent de chaque statut : à vérifier dans les "
                    "lois organiques avant de les chiffrer dans un scénario"],
       contre=["le Conseil constitutionnel (61 sur la loi organique)", "le Conseil d'État (contrôle "
               "juridictionnel spécifique)", "l'État (compétences régaliennes, relations extérieures)",
               "les électeurs de la collectivité (72-4 en cas de changement de régime)"],
       strates=["Local", "National", "Europe", "Mondial"],
       croise=["34", "53", "72-3", "72-4", "73", "74-1", "76", "77"],
       mecanismes=("statut_organique_outre_mer", "autonomie_legislative", "mesures_locales"),
       leviers=("outre_mer_statut", "autonomie_outre_mer")),
    _a("74-1", "Ordonnances outre-mer",
       "XII", "outre-mer", "Gouvernement ; Parlement (ratification sous dix-huit mois)",
       "Dans les collectivités d'outre-mer visées à l'article 74 et en Nouvelle-Calédonie, le Gouvernement "
       "peut, par ordonnances, dans les matières qui demeurent de la compétence de l'État, étendre, avec les "
       "adaptations nécessaires, les dispositions de nature législative en vigueur en métropole ou adapter à "
       "l'organisation particulière de la collectivité concernée les dispositions de nature législative en "
       "vigueur, sous réserve que la loi n'ait pas expressément exclu, pour les dispositions en cause, le "
       "recours à cette procédure. Les ordonnances sont prises en conseil des ministres après avis des "
       "assemblées délibérantes intéressées et du Conseil d'État ; elles entrent en vigueur dès leur "
       "publication et deviennent caduques en l'absence de ratification par le Parlement dans le délai de "
       "dix-huit mois suivant cette publication. (créé par la loi constitutionnelle du 23 juillet 2008)",
       regles=["périmètre limité aux matières restant de la compétence de l'État",
               "double avis préalable : assemblée délibérante de la collectivité et Conseil d'État",
               "caducité automatique à défaut de ratification expresse dans les dix-huit mois",
               "la loi peut exclure expressément le recours à cette procédure"],
       opportunites=["aligner rapidement le droit local sur le droit national (transposition, sécurité, "
                     "continuité territoriale) sans mobiliser la navette",
                     "la caducité de dix-huit mois garantit que le Parlement garde la main in fine"],
       contraintes=["impossible d'étendre ou d'adapter une loi pour une matière déjà transférée à la "
                    "collectivité",
                    "un oubli de l'avis de l'assemblée délibérante expose l'ordonnance à la censure ou à "
                    "l'annulation",
                    "un refus de ratifier emporte disparition de l'ordonnance"],
       contre=["le Parlement (défaut de ratification)", "les assemblées délibérantes (avis)",
               "le Conseil constitutionnel (61)", "le Conseil d'État (recours contre les ordonnances non "
               "ratifiées)"],
       strates=["Local", "National"],
       croise=["38", "74", "76", "77"],
       mecanismes=("ordonnances_outre_mer", "caducite_ordonnance"),
       leviers=("outre_mer_statut", "recours_ordonnances")),
    _a("75", "Statut civil personnel (droit coutumier)",
       "XII", "outre-mer", "Législateur",
       "« Les citoyens de la République qui n'ont pas le statut civil de droit commun, seul visé à "
       "l'article 34, conservent leur statut personnel tant qu'ils n'y ont pas renoncé. »",
       regles=["le statut civil de droit commun est le seul que la loi puisse organiser (34)",
               "le statut personnel est protégé constitutionnellement, et il est individuel : nul n'y est "
               "contraint",
               "la renonciation est volontaire et individuelle"],
       opportunites=["protège les juridictions et règles de droit local (foncier et statut civil en "
                     "Nouvelle-Calédonie, justice criminelle coutumière à Wallis-et-Futuna)",
                     "toute évolution du droit coutumier suppose l'accord des intéressés : la réforme "
                     "consentie est plus stable que la réforme imposée"],
       contraintes=["impossible d'imposer un statut coutumier à des citoyens qui ne le demandent pas : "
                    "égalité devant la loi",
                    "le statut personnel ne peut déroger aux droits fondamentaux garantis par le bloc de "
                    "constitutionnalité",
                    "Mayotte : le vote de 2009 puis la départementalisation de 2011 ont engagé l'alignement "
                    "sur le statut civil de droit commun"],
       contre=["les justiciables (renonciation individuelle)", "le législateur (34)",
               "le Conseil constitutionnel (61, 61-1)"],
       strates=["Local", "National"],
       croise=["1", "6", "34", "72-3", "73", "74", "77"],
       mecanismes=("statut_coutumier",),
       leviers=("outre_mer_statut",)),
    _a("75-1", "Les langues régionales appartiennent au patrimoine de la France",
       "XII", "droits & libertés", "Législateur ; collectivités",
       "« Les langues régionales appartiennent au patrimoine de la France. » (loi constitutionnelle du 23 "
       "juillet 2008)",
       regles=["formulation patrimoniale, non normative : l'article ne crée ni droit à l'enseignement ni "
               "obligation de service public linguistique",
               "l'article 2 demeure : « La langue de la République est le français »",
               "la Charte européenne des langues régionales ou minoritaires reste incompatible avec la "
               "Constitution sans révision (Conseil constitutionnel, décision 2001-445 DC du 15 juin 2001)"],
       opportunites=["base constitutionnelle des lois sur les langues (loi du 21 mai 2021 relative à la "
                     "protection patrimoniale des langues régionales et à leur promotion : enseignement "
                     "bilingue, signalétique, médias)",
                     "les collectivités peuvent financer la politique linguistique locale (offices publics, "
                     "filières bilingues) : levier culturel et éducatif"],
       contraintes=["ni enseignement immersif obligatoire ni coofficialité en l'état du droit",
                    "la ratification de la Charte exige une révision de la Constitution : le projet de "
                    "révision de 2021 n'a pas abouti",
                    "la loi de 2021 a été partiellement censurée sur l'enseignement de la langue dans les "
                    "écoles publiques : le législateur ne peut pas imposer ce que l'article 2 réserve"],
       contre=["le Conseil constitutionnel (égalité des citoyens, article 2)",
               "le Sénat (réserve classique sur l'unité linguistique)",
               "l'État (programme et statut des enseignants)"],
       strates=["National", "Local", "Europe"],
       croise=["1", "2", "34", "53", "54", "72", "89"],
       mecanismes=("politique_linguistique", "ratification_charte_langues"),
       leviers=("politique_linguistique",)),
)


# ────────────────────────────────────────────────────────────────────────────
# TITRE XIII — NOUVELLE-CALÉDONIE (76-77) ; TITRE XIV — FRANCOPHONIE (87-88)
# ────────────────────────────────────────────────────────────────────────────

_TITRE_XIII_XIV: tuple[ArticleConstitution, ...] = (
    _a("76", "Consultation de 1998 sur l'accord de Nouméa",
       "XIII", "outre-mer", "Peuple de Nouvelle-Calédonie ; loi organique",
       "« Les populations de la Nouvelle-Calédonie sont appelées à se prononcer avant le 31 décembre 1998 "
       "sur les dispositions de l'accord signé à Nouméa le 5 mai 1998 et publié le 27 mai 1998 au Journal "
       "officiel de la République française. » Sont admises à participer au scrutin les personnes remplissant "
       "les conditions fixées à l'article 2 de la loi n° 88-1028 du 9 novembre 1988. Les mesures nécessaires à "
       "l'organisation du scrutin sont prises par décret en Conseil d'État délibéré en conseil des ministres. "
       "(créé par la loi constitutionnelle du 20 juillet 1998)",
       regles=["accord de Nouméa approuvé par 71,99 % des suffrages exprimés à la consultation du 8 "
               "novembre 1998",
               "corps électoral spécial défini par renvoi à la loi du 9 novembre 1988",
               "organisation du scrutin par décret en Conseil d'État délibéré en conseil des ministres "
               "(9, 13)"],
       opportunites=["le précédent calédonien est la matrice constitutionnelle d'une évolution convenue : un "
                     "accord politique local devient norme organique après consultation",
                     "le renvoi constitutionnel à un « tableau » fige le corps électoral : c'est la technique "
                     "utilisée pour verrouiller une composition électorale contre les installations "
                     "récentes"],
       contraintes=["l'échéance de 1998 est passée, mais l'article reste en vigueur comme fondement du "
                    "statut : une disposition transitoire n'est pas nécessairement abrogée",
                    "modifier le corps électoral par la seule loi est impossible : un projet de révision "
                    "constitutionnelle sur ce point, engagé au printemps 2024, est devenu caduc avec la "
                    "dissolution de juin 2024"],
       contre=["les forces politiques indépendantistes (contestation du gel du corps électoral)",
               "les provinces et le Congrès (institutions locales)",
               "le Conseil constitutionnel (61 sur la loi organique)"],
       strates=["Local", "National", "Mondial"],
       croise=["9", "13", "72-3", "77"],
       mecanismes=("accord_politique_outre_mer", "corps_electoral_special"),
       leviers=("outre_mer_statut",)),
    _a("77", "Loi organique calédonienne : transferts, institutions, citoyenneté, autodétermination",
       "XIII", "outre-mer", "Législateur organique ; assemblée délibérante de la Nouvelle-Calédonie",
       "Après approbation de l'accord lors de la consultation prévue à l'article 76, la loi organique, prise "
       "après avis de l'assemblée délibérante de la Nouvelle-Calédonie, détermine, pour assurer l'évolution de "
       "la Nouvelle-Calédonie dans le respect des orientations définies par cet accord : les compétences de "
       "l'État transférées de façon définitive, l'échelonnement et les modalités de ces transferts ainsi que "
       "la répartition des charges ; les règles d'organisation et de fonctionnement des institutions et les "
       "conditions dans lesquelles certaines catégories d'actes de l'assemblée délibérante peuvent être "
       "soumises avant publication au contrôle du Conseil constitutionnel ; les règles relatives à la "
       "citoyenneté, au régime électoral, à l'emploi et au statut civil coutumier ; les conditions et les "
       "délais dans lesquels les populations intéressées sont amenées à se prononcer sur l'accession à la "
       "pleine souveraineté. Les autres mesures nécessaires sont définies par la loi. Pour la définition du "
       "corps électoral appelé à élire les membres des assemblées délibérantes de la Nouvelle-Calédonie et des "
       "provinces, le tableau de référence est celui dressé à l'occasion du scrutin prévu à l'article 76, y "
       "compris les personnes non admises à y participer.",
       regles=["compétences régaliennes laissées à l'État (nationalité, droits civiques, justice, défense, "
               "monnaie, ordre public, relations extérieures) : la liste détaillée figure dans la loi "
               "organique n° 99-209 du 19 mars 1999",
               "contrôle a priori par le Conseil constitutionnel de certaines catégories d'actes du Congrès, "
               "sur saisine des autorités de la collectivité",
               "trois consultations d'autodétermination organisées en 2018, 2020 et 2021, toutes "
               "défavorables à l'indépendance, la dernière marquée par un boycott indépendantiste et une "
               "participation très faible",
               "gel du corps électoral : dérogation constitutionnelle expresse issue du dernier alinéa de "
               "l'article 77, admise par le Conseil constitutionnel en QPC"],
       opportunites=["le titre XIII est le seul mécanisme constitutionnel interne d'accession à la pleine "
                     "souveraineté : il a produit trois scrutins et peut en organiser d'autres après un "
                     "accord politique",
                     "la loi organique peut bâtir des institutions originales (gouvernement collégial, "
                     "Sénat coutumier, conseil régional des communautés de communes) : laboratoire "
                     "institutionnel mobilisable comme hypothèse de simulation",
                     "l'échelonnement des transferts permet une autonomie graduée plutôt qu'une rupture"],
       contraintes=["aucune modification du corps électoral par simple loi : le verrou du dernier alinéa "
                    "s'y oppose",
                    "toute évolution suppose l'accord des forces politiques locales (l'accord de Bougival de "
                    "l'été 2024, signé sans les indépendantistes, n'a produit aucune révision) et le "
                    "consentement des électeurs",
                    "les transferts de compétences doivent être accompagnés de la répartition des charges : "
                    "le contentieux financier est ouvert",
                    "les matière régaliennes non transférables excluent une police et une justice "
                    "entièrement locales"],
       contre=["le Conseil constitutionnel (61, 61-1, contrôle a priori des actes du Congrès)",
               "les électeurs calédoniens (consultations d'autodétermination)",
               "le Sénat coutumier (avis sur l'identité kanak)",
               "l'État (ordre public : l'état d'urgence a été décrété en mai 2024, 36-1)"],
       strates=["Local", "National", "Mondial", "Europe"],
       croise=["1", "36-1", "72-3", "74", "74-1", "76", "89"],
       mecanismes=("autodetermination", "corps_electoral_special", "transfert_competences_organique"),
       leviers=("outre_mer_statut", "consultation_autodetermination")),
    _a("87", "Francophonie et coopération",
       "XIV", "Europe & traités", "République",
       "« La République participe au développement de la solidarité et de la coopération entre les États et "
       "les peuples ayant le français en partage. » (créé par la loi constitutionnelle du 4 août 1995, en "
       "remplacement du titre de la Communauté)",
       regles=["obligation de moyen (« participe »), non de résultat",
               "aucune organisation permanente ni transfert de compétences : la francophonie n'est pas un "
               "ordre juridique intégré"],
       opportunites=["fonde une diplomatie d'influence (éducation, droit, médias) à bas coût comparé aux "
                     "instruments de puissance",
                     "la coopération juridique francophone exporte le modèle institutionnel "
                     "(Conseils constitutionnels, écoles de magistrats)"],
       contraintes=["budget limité et voté en loi de finances : peu de marge hors arbitrage",
                    "aucune contrainte réciproque : l'article n'oblige personne"],
       contre=["les partenaires (souveraineté égale)", "le Parlement (34, 47 : vote des moyens)"],
       strates=["National", "Mondial", "Europe"],
       croise=["52", "53", "88", "88-1", "75-1"],
       mecanismes=("cooperation_regionale",),
       leviers=("diplomatie_influence",)),
    _a("88", "Accords d'association",
       "XIV", "Europe & traités", "Président ; loi d'autorisation (53)",
       "« La République peut conclure des accords avec des États qui désirent s'associer à elle pour "
       "développer leurs civilisations. » (résidu du chapitre d'association de la Communauté, rédaction de la "
       "loi constitutionnelle du 4 août 1995)",
       regles=["relève de l'article 53 dès que le contrat engage les finances de l'État ou modifie des "
               "dispositions législatives : autorisation par la loi",
               "aucune institution commune, aucune citoyenneté : coopération volontaire"],
       opportunites=["adosser une politique de développement (santé, éducation, langue) à un cadre "
                     "juridique bilatéral durable",
                     "négocier des accords culturels et universitaires sans ouverture d'un débat sur "
                     "l'intégration"],
       contraintes=["article quasi dormant depuis 1995 : aucune infrastructure juridique nouvelle n'a été "
                    "créée sur son fondement",
                    "un accord d'association ne crée aucun droit pour ses bénéficiaires sans loi interne"],
       contre=["le Parlement (53 : loi d'autorisation)",
               "le Conseil constitutionnel (54 en cas de clause contraire à la Constitution)"],
       strates=["National", "Mondial"],
       croise=["52", "53", "54", "87"],
       mecanismes=("accord_association",)),
)


# ────────────────────────────────────────────────────────────────────────────
# TITRE XV — DE L'UNION EUROPÉENNE (articles 88-1 à 88-7)
# ────────────────────────────────────────────────────────────────────────────

_TITRE_XV: tuple[ArticleConstitution, ...] = (
    _a("88-1", "Participation à l'Union européenne",
       "XV", "Europe & traités", "République ; TUE et TFUE (Lisbonne)",
       "« La République participe à l'Union européenne constituée d'États qui ont choisi librement d'exercer "
       "en commun certaines de leurs compétences en vertu du traité sur l'Union européenne et du traité sur le "
       "fonctionnement de l'Union européenne, tels qu'ils résultent du traité signé à Lisbonne le 13 décembre "
       "2007. » (rédaction issue de la loi constitutionnelle du 4 octobre 2008)",
       regles=["base constitutionnelle de la participation, créée par la révision de 2008",
               "l'Union n'exerce que des compétences attribuées (« certaines de leurs compétences »)",
               "la référence est figée sur l'état des traités issu de Lisbonne : au-delà, l'article 54 puis "
               "l'article 89 s'appliquent"],
       opportunites=["permet les adaptations du droit national au droit dérivé sans révision à chaque "
                     "réforme des traités, tant que l'objet reste dans le cadre de Lisbonne",
                     "rend possible une politique européenne volontariste (marché unique, énergie, défense) "
                     "y compris par coopérations renforcées"],
       contraintes=["principe d'attribution : l'Union ne peut pas s'auto-saisir d'une compétence",
                    "un transfert nouveau de souveraineté exige une révision (précédents : Maastricht, "
                    "Amsterdam, Lisbonne, mécanisme européen de stabilité en 2012)",
                    "le Conseil constitutionnel vérifie que la transposition ne méconnaît aucune "
                    "disposition « inhérente à l'identité ou aux intérêts spécifiques de la France "
                    "» (jurisprudence constante)"],
       contre=["le Conseil constitutionnel (61, 61-1)", "le Parlement (88-4 et 88-6)",
               "la Cour de justice de l'Union européenne (55, 88-6)",
               "les électeurs (88-5 pour une adhésion)"],
       strates=["Europe", "National", "Local", "Mondial"],
       croise=["34", "53", "54", "55", "88-2", "88-4", "88-5", "88-6", "88-7", "89"],
       mecanismes=("appartenance_ue", "transfert_competences"),
       leviers=("souverainete_europeenne", "alignement_reglementaire_ue")),
    _a("88-2", "Mandat d'arrêt européen",
       "XV", "Europe & traités", "Législateur",
       "« La loi fixe les règles relatives au mandat d'arrêt européen en application des actes pris par les "
       "institutions de l'Union européenne. » (créé par la loi constitutionnelle du 1ᵉʳ mars 2004)",
       regles=["transposition par la loi du 9 mars 2004 pour la décision-cadre 2002/584/JAI (code de "
               "procédure pénale, art. 695 et suivants)",
               "motifs de non-exécution limitativement énumérés : la loi ne peut pas en ajouter de généraux",
               "droits de la personne remise encadrés par les directives relatives aux droits procéduraux "
               "(accès à un avocat, directive 2013/48/UE)"],
       opportunites=["la reconnaissance mutuelle accélère l'entraide pénale contre la criminalité organisée "
                     "et le terrorisme, sans procédure d'extradition diplomatique",
                     "la loi peut préciser les garanties procédurales nationales dans les limites du "
                     "droit de l'Union"],
       contraintes=["la France ne peut pas subordonner l'exécution du mandat à une condition générale de "
                    "réciprocité : la CJUE censure (affaire LM, C-619/18)",
                    "le Conseil constitutionnel veille à ce que la remise respecte la sauvegarde de la "
                    "liberté individuelle (66)",
                    "le procureur général près la cour d'appel est seul à saisir la chambre de l'instruction"],
       contre=["la CJUE (questions préjudicielles sur le mandat)", "le Conseil constitutionnel (61, 61-1)",
               "la CEDH (articles 5 et 6 de la Convention)"],
       strates=["Europe", "National"],
       croise=["34", "55", "66", "88-1", "88-7"],
       mecanismes=("reconnaissance_mutuelle", "remise_individuelle"),
       leviers=("espace_penal_europeen",)),
    _a("88-3", "Droit de vote municipal des citoyens de l'Union résidant en France",
       "XV", "souveraineté", "Législateur organique ; résidents de l'Union",
       "« Sous réserve de réciprocité et selon les modalités prévues par le Traité sur l'Union européenne "
       "signé le 7 février 1992, le droit de vote et d'éligibilité aux élections municipales peut être accordé "
       "aux seuls citoyens de l'Union résidant en France. Ces citoyens ne peuvent exercer les fonctions de "
       "maire ou d'adjoint ni participer à la désignation des électeurs sénatoriaux et à l'élection des "
       "sénateurs. Une loi organique votée dans les mêmes termes par les deux assemblées détermine les "
       "conditions d'application du présent article. »",
       regles=["réciprocité exigée (les autres États membres doivent accorder un droit équivalent aux "
               "Français résidant chez eux)",
               "fonctions de maire ou d'adjoint fermées, comme la désignation des grands électeurs sénatoriaux",
               "loi organique votée dans les mêmes termes : le Sénat dispose donc d'un veto absolu (46 al.4)",
               "mis en œuvre par la loi organique du 25 mai 1998 et les articles L. 227 et suivants du code "
               "électoral"],
       opportunites=["l'ouverture du scrutin municipal aux résidents de l'Union a ajouté plusieurs "
                     "centaines de milliers d'électeurs sur les listes complémentaires",
                     "l'exemple montre qu'une modification du corps électoral est possible par révision + "
                     "loi organique, sans transfert de compétence matériel",
                     "étendre le droit de vote aux résidents non européens à d'autres scrutins, ou leur "
                     "confier une fonction élective, heurterait l'article 3 (« les nationaux ») : seule une "
                     "révision par l'article 89 le permettrait"],
       contraintes=["asymétrie démocratique : on peut être conseiller municipal, jamais maire",
                    "aucun poids dans l'élection du Sénat, donc dans la représentation des collectivités",
                    "toute extension à d'autres scrutins suppose une révision de l'article 3, donc les "
                    "termes identiques des deux assemblées puis le référendum ou les trois cinquièmes du "
                    "Congrès"],
       contre=["le Conseil constitutionnel (61 sur la loi organique ; 59 sur le contentieux électoral)",
               "les deux assemblées (vote en termes identiques exigé)",
               "les États partenaires (condition de réciprocité)"],
       strates=["National", "Europe", "Local"],
       croise=["3", "24", "34", "46", "72", "88-1"],
       mecanismes=("droit_vote_etrangers", "reciprocite"),
       leviers=("droit_vote_etrangers_locaux",)),
    _a("88-4", "Résolutions européennes et commission des affaires européennes",
       "XV", "Europe & traités", "Chaque assemblée ; Gouvernement",
       "Le Gouvernement soumet à l'Assemblée nationale et au Sénat, dès leur transmission au Conseil de "
       "l'Union européenne, les projets d'actes législatifs européens et les autres projets ou propositions "
       "d'actes de l'Union. Selon des modalités fixées par le règlement de chaque assemblée, des résolutions "
       "européennes peuvent être adoptées, le cas échéant en dehors des sessions, sur ces projets et "
       "propositions ainsi que sur tout document émanant d'une institution de l'Union. Au sein de chaque "
       "assemblée parlementaire est instituée une commission chargée des affaires européennes. (créé par la "
       "loi constitutionnelle du 1ᵉʳ mars 2005, renforcé par celle du 4 octobre 2008)",
       regles=["transmission obligatoire dès la saisine du Conseil de l'Union",
               "résolutions adoptables hors session ; modalités fixées par les règlements, eux-mêmes "
               "contrôlés avant application (61 al.1)",
               "une commission des affaires européennes dans chaque assemblée, saisie pour avis même quand "
               "elle n'est pas saisie au fond",
               "en matière de justice et d'affaires intérieures, délai de huit semaines entre transmission et "
               "inscription à l'ordre du jour du Conseil (protocoles de Lisbonne)"],
       opportunites=["la résolution européenne est le seul instrument par lequel une assemblée mandate "
                     "formellement son gouvernement avant un Conseil",
                     "la commission spécialisée peut se saisir pour avis de tout texte et peser sur le "
                     "mandat de négociation",
                     "les avis motivés de l'article 88-6 passent par le canal ouvert ici : le Parlement "
                     "national est un acteur direct du contrôle de subsidiarité"],
       contraintes=["la résolution ne lie pas le Gouvernement : seuls la pression politique et l'article 50-1 "
                    "(débat) produisent des effets",
                    "les compromis se nouent souvent en trilogue avant le vote de la résolution : asymétrie "
                    "d'information structurelle",
                    "aucun veto, aucune obligation de suivre l'avis de l'assemblée"],
       contre=["le Gouvernement (conduite de la négociation)", "la Conférence des présidents (inscription)",
               "le Conseil constitutionnel (61 al.1 sur le règlement)"],
       strates=["Europe", "National"],
       croise=["34-1", "48", "50-1", "61", "88-1", "88-5", "88-6"],
       mecanismes=("controle_parlementaire_ue", "resolution_europeenne", "carton_jaune"),
       leviers=("controle_permanent_ue",)),
    _a("88-5", "Référendum obligatoire pour toute adhésion à l'Union",
       "XV", "souveraineté", "Président de la République ; motion des deux assemblées à trois cinquièmes",
       "« Tout projet de loi autorisant la ratification d'un traité relatif à l'adhésion d'un État à l'Union "
       "européenne est soumis au référendum par le Président de la République. Toutefois, par le vote d'une "
       "motion adoptée en termes identiques par chaque assemblée à la majorité des trois cinquièmes, le "
       "Parlement peut autoriser l'adoption du projet de loi selon la procédure prévue au troisième alinéa de "
       "l'article 89. » [cet article n'est pas applicable aux adhésions faisant suite à une conférence "
       "intergouvernementale dont la convocation a été décidée par le Conseil européen avant le 1ᵉʳ juillet "
       "2004]",
       regles=["référendum de règle pour toute adhésion : l'obligation résulte de la décision 2004-505 DC du "
               "25 novembre 2004, qui exigeait une révision pour ratifier l'adhésion de dix États, d'où la "
               "loi constitutionnelle du 1ᵉʳ mars 2005",
               "voie détournée possible par motion en termes identiques à trois cinquièmes dans chaque "
               "assemblée (347 députés sur 577 ; 209 sénateurs sur 348)",
               "l'exception transitoire ne visait que les adhésions roumaine et bulgare"],
       opportunites=["le verrou référendaire rend toute adhésion politiquement coûteuse : c'est un garde-fou "
                     "contre un élargissement décidé d'en haut",
                     "la voie du Congrès reste théoriquement ouverte : à configurer comme scénario alternatif "
                     "dans le simulateur"],
       contraintes=["impossible de faire ratifier une adhésion par la seule loi",
                    "trois cinquièmes dans chaque assemblée : majorité qualifiée hors de portée sans accord "
                    "des principaux groupes",
                    "le référendum ne peut porter que sur le projet de loi autorisant la ratification : pas "
                    "de question libre",
                    "une sortie de l'Union (retrait d'un État membre) ne relève pas de cet article : elle "
                    "suit l'article 50 du TUE"],
       contre=["les électeurs (référendum)", "chaque assemblée à trois cinquièmes (motion)",
               "le Conseil constitutionnel (61 sur la loi autorisant la ratification)"],
       strates=["National", "Europe"],
       croise=["3", "11", "50", "53", "54", "72-4", "88-1", "89"],
       mecanismes=("referendum_adhesion", "motion_congres"),
       leviers=("elargissement_ue",)),
    _a("88-6", "Contrôle de subsidiarité : avis motivés et recours devant la CJUE",
       "XV", "contrôle & évaluation", "Chaque assemblée ; soixante députés ou soixante sénateurs",
       "L'Assemblée nationale ou le Sénat peuvent émettre un avis motivé sur la conformité d'un projet d'acte "
       "législatif européen au principe de subsidiarité ; l'avis est adressé par le président de l'assemblée "
       "concernée aux présidents du Parlement européen, du Conseil et de la Commission européenne, le "
       "Gouvernement en étant informé. Chaque assemblée peut former un recours devant la Cour de justice de "
       "l'Union européenne contre un acte législatif européen pour violation du principe de subsidiarité ; le "
       "recours est transmis à la Cour par le Gouvernement. À cette fin, des résolutions peuvent être adoptées, "
       "le cas échéant en dehors des sessions, selon des modalités d'initiative et de discussion fixées par le "
       "règlement de chaque assemblée ; à la demande de soixante députés ou de soixante sénateurs, le recours "
       "est de droit.",
       regles=["délai de huit semaines entre la transmission du projet d'acte et l'inscription à l'ordre du "
               "jour du Conseil (protocoles n° 1 et 2 annexés aux traités)",
               "carton jaune : un tiers des voix attribuées aux parlements nationaux, soit dix-huit sur "
               "cinquante-quatre depuis le retrait du Royaume-Uni → la Commission réexamine",
               "carton orange : 55 % des voix, soit trente → la Commission doit motiver le maintien, et le "
               "législateur européen peut écarter le texte dès l'origine",
               "soixante députés ou soixante sénateurs : le recours devant la CJUE est de droit, le "
               "Gouvernement ne peut pas le refuser"],
       opportunites=["soixante signatures transforment une minorité en justiciable du droit de l'Union : "
                     "c'est le contre-pouvoir parlementaire le plus sous-utilisé de la Ve République",
                     "un avis motivé français coordonné avec d'autres parlements a déjà fait reculer la "
                     "Commission (cartons jaunes de 2012 sur le règlement « Monti II », de 2013 sur le "
                     "Parquet européen, de 2016 sur la directive « travailleurs détachés » ; aucun carton "
                     "orange à ce jour)",
                     "le recours devant la CJUE est une arme contentieuse contre un texte "
                     "surcompétent"],
       contraintes=["la Commission n'est pas tenue de suivre un avis motivé : la procédure est politique",
                    "le Gouvernement « transmet » le recours : il ne peut le refuser mais en pilote la "
                    "rédaction",
                    "huit semaines sont courtes face au rythme des négociations en trilogue"],
       contre=["la Commission (garde des traités)", "le Conseil et le Parlement européen (décision)",
               "la CJUE (contrôle juridictionnel)"],
       strates=["Europe", "National", "Local"],
       croise=["48", "61", "88-1", "88-4", "88-5"],
       mecanismes=("subsidiarite", "carton_jaune", "recours_cjue"),
       leviers=("controle_permanent_ue", "alerte_subsidiarite")),
    _a("88-7", "Opposition parlementaire aux clauses de passerelle européennes",
       "XV", "Europe & traités", "Chaque assemblée (motion en termes identiques)",
       "« Par le vote d'une motion adoptée en termes identiques par l'Assemblée nationale et le Sénat, le "
       "Parlement peut s'opposer à une modification des règles d'adoption d'actes de l'Union européenne dans "
       "les cas prévus, au titre de la révision simplifiée des traités ou de la coopération judiciaire civile, "
       "par le traité sur l'Union européenne et le traité sur le fonctionnement de l'Union européenne, tels "
       "qu'ils résultent du traité signé à Lisbonne le 13 décembre 2007. »",
       regles=["vise les clauses de passerelle : article 48 § 6 du TUE (révision simplifiée du TFUE) et "
               "article 81 § 3 du TFUE (coopération judiciaire civile)",
               "motion en termes identiques des deux assemblées = opposition de droit, notifiée au Conseil "
               "européen et à la Commission dans un délai de six mois",
               "le Gouvernement français doit alors s'opposer à la décision au Conseil européen",
               "créé par la loi constitutionnelle du 4 octobre 2008"],
       opportunites=["c'est le seul veto parlementaire national direct sur une décision européenne : le "
                     "passage à la majorité qualifiée est conditionné à l'accord des deux chambres",
                     "la seule menace d'adoption de la motion sert d'argument de négociation au "
                     "gouvernement français",
                     "la motion peut être travaillée hors session par la commission des affaires "
                     "européennes (88-4)"],
       contraintes=["exige la même motion dans les deux assemblées : le Sénat peut donc faire échec au veto "
                    "comme le rendre possible",
                    "ne couvre pas les autres passerelles des traités (politique étrangère et de défense, "
                    "politique sociale) : le verrou français est partiel",
                    "la motion n'oblige que le négociateur français, pas le Conseil européen"],
       contre=["le Conseil européen (décision, soumise à l'approbation des États membres selon leurs "
               "exigences constitutionnelles)", "les deux assemblées (rejet de la motion = liberté rendue au "
               "Gouvernement)", "le Conseil constitutionnel (incompétent sur la motion)"],
       strates=["Europe", "National"],
       croise=["34-1", "53", "54", "88-1", "88-4", "88-5"],
       mecanismes=("passerelle_ue", "veto_parlementaire_motion"),
       leviers=("souverainete_europeenne", "clause_passerelle")),
)


# ────────────────────────────────────────────────────────────────────────────
# TITRE XVI — DE LA RÉVISION (article 89)
# ────────────────────────────────────────────────────────────────────────────

_TITRE_XVI: tuple[ArticleConstitution, ...] = (
    _a("89", "Révision de la Constitution : navette, référendum ou Congrès à trois cinquièmes",
       "XVI", "révision", "Président sur proposition du Premier ministre ; parlementaires ; électeurs ou "
       "Congrès",
       "L'initiative de la révision de la Constitution appartient concurremment au Président de la République "
       "sur proposition du Premier ministre et aux membres du Parlement. Le projet ou la proposition de "
       "révision doit être examiné dans les conditions de délai fixées au troisième alinéa de l'article 42 et "
       "voté par les deux assemblées en termes identiques. La révision est définitive après avoir été "
       "approuvée par référendum. Toutefois, le projet de révision n'est pas présenté au référendum lorsque le "
       "Président de la République décide de le soumettre au Parlement convoqué en Congrès ; dans ce cas, le "
       "projet de révision n'est approuvé que s'il réunit la majorité des trois cinquièmes des suffrages "
       "exprimés. Le bureau du Congrès est celui de l'Assemblée nationale. Aucune procédure de révision ne peut "
       "être engagée ou poursuivie lorsqu'il est porté atteinte à l'intégrité du territoire. La forme "
       "républicaine du Gouvernement ne peut faire l'objet d'une révision.",
       regles=["délais de l'article 42 alinéa 3 : six semaines avant la délibération en séance devant la "
               "première assemblée, quatre semaines devant la seconde",
               "vote en termes identiques des deux assemblées : ni commission mixte paritaire ni dernier mot "
               "de l'Assemblée nationale",
               "Congrès : majorité des trois cinquièmes des suffrages exprimés (555 voix sur 925 sièges "
               "théoriques ; le décompte se fait sur les sièges pourvus au jour du vote)",
               "référendum : aucun seuil de participation n'est exigé par le texte",
               "aucune révision engagée ou poursuivie en cas d'atteinte à l'intégrité du territoire",
               "la forme républicaine du gouvernement est irrevisible (alinéa 5)"],
       opportunites=["la voie du Congrès évite le référendum : la très grande majorité des révisions depuis "
                     "1958 y a été approuvée, la seule révision adoptée par référendum étant celle du "
                     "6 novembre 1962 sur l'élection du Président au suffrage universel direct",
                     "l'initiative parlementaire existe (proposition de révision) mais suppose le même "
                     "parcours, y compris l'accord du Sénat",
                     "réviser est le seul chemin pour instaurer un mandat parlementaire révocable, un RIC "
                     "national, la proportionalité du scrutin ou la suppression de l'article 49 alinéa 3",
                     "un gouvernement sans majorité stable peut chercher à verrouiller une politique par une "
                     "révision « de protection » plutôt que par une loi, réversible à merci"],
       contraintes=["aucune révision par en bas : le peuple ne peut ni amender ni proposer la Constitution ; "
                    "le RIP (11 al.5) ne porte que sur l'abrogation d'une disposition législative",
                    "le Sénat détient un veto de fait : une seule amendment de forme suffit à rompre les "
                    "termes identiques",
                    "en cas de vacance de la présidence ou entre les deux tours, l'article 7 interdit "
                    "d'engager ou de poursuivre une procédure de révision",
                    "le Conseil constitutionnel se déclare incompétent pour juger d'une loi constitutionnelle "
                    "comme d'une loi référendaire (décision 62-20 LOM du 6 novembre 1962) : aucun garde-fou "
                    "judiciaire sur le fond",
                    "une proposition de révision non votée en termes identiques avant la fin de la "
                    "législature devient caduque en pratique"],
       contre=["les électeurs (rejet en référendum : le projet tombe)",
               "le Sénat (amendement ou rejet = fin de la procédure)",
               "les trois cinquièmes des suffrages exprimés au Congrès",
               "l'article 89 alinéas 4 et 5 (intégrité du territoire, forme républicaine) comme limites "
               "absolues"],
       strates=["National", "Local", "Europe", "Transversal"],
       croise=["3", "7", "11", "12", "16", "42", "45", "46", "54", "60", "61", "72-1", "88-5"],
       mecanismes=("revision_constitutionnelle", "congres", "referendum_revision"),
       leviers=("revision_constitutionnelle", "verrouillage_irreversibilite")),
)


# ────────────────────────────────────────────────────────────────────────────
# ARTICLES ABROGÉS — consignés pour qu'aucun scénario ne les réutilise
# ────────────────────────────────────────────────────────────────────────────

ABROGES: tuple[dict[str, str], ...] = (
    {"numero": "78", "titre": "Compétences législatives et réglementaires de la Communauté",
     "abroge_par": "Loi constitutionnelle n° 95-880 du 4 août 1995",
     "note": "Titre XII « Des collectivités territoriales de la République » dans sa rédaction de 1958 "
             "puis de la Communauté ; le dispositif institué par la loi constitutionnelle du 4 juin 1960 a "
             "été vidé de son objet par les indépendances et les évolutions statutaires, puis abrogé en "
             "1995."},
    {"numero": "79", "titre": "Les six compétences de la Communauté (politique étrangère, défense, "
     "économie et finances, justice et haut conseil, ordre public, enseignement supérieur et recherche)",
     "abroge_par": "Loi constitutionnelle du 4 août 1995",
     "note": "Liste des compétences transférées aux institutions communes, remplacées de fait par les accords "
             "de défense, la zone franc et les coopérations bilatérales."},
    {"numero": "80", "titre": "Le Sénat de la Communauté", "abroge_par": "Loi constitutionnelle du 4 août 1995",
     "note": "Chambre commune de représentation des États et territoires de la Communauté."},
    {"numero": "81", "titre": "Le Conseil de la Communauté", "abroge_par": "Loi constitutionnelle du "
     "4 août 1995",
     "note": "Organe exécutif de la Communauté, composé des chefs d'État ou de gouvernement, présidé par le "
             "Président de la République française."},
    {"numero": "82", "titre": "Le Président de la République, président du Conseil de la Communauté",
     "abroge_par": "Loi constitutionnelle du 4 août 1995",
     "note": "Initiative des actes communs et représentation de la Communauté ; délégation possible en cas "
             "d'empêchement."},
    {"numero": "83", "titre": "La Cour arbitrale de la Communauté", "abroge_par": "Loi constitutionnelle du "
     "4 août 1995",
     "note": "Juridiction chargée des différends nés de l'interprétation ou de la validité des actes "
             "communautaires."},
    {"numero": "84", "titre": "Les lois-cadres de la Communauté", "abroge_par": "Loi constitutionnelle du "
     "4 août 1995",
     "note": "Procédure législative commune : vote par le Sénat de la Communauté après consultation, "
             "application dans les États membres."},
    {"numero": "85", "titre": "Le plan et les actes communs de la Communauté",
     "abroge_par": "Loi constitutionnelle du 4 août 1995",
     "note": "Coordination économique et plans communs de développement."},
    {"numero": "86", "titre": "La citoyenneté de la Communauté", "abroge_par": "Loi constitutionnelle du "
     "4 août 1995",
     "note": "Libre circulation et droits communs aux citoyens de la Communauté ; restée sans application "
             "effective."},
    {"numero": "90", "titre": "Dispositions transitoires relatives au Conseil supérieur de la magistrature",
     "abroge_par": "Loi constitutionnelle n° 2008-1031 du 23 juillet 2008",
     "note": "Prévoyait la composition provisoire du Conseil supérieur de la magistrature jusqu'à l'entrée en "
             "vigueur de la loi organique ; devenu sans objet, abrogé par la réforme constitutionnelle de 2008 "
             "qui a réorganisé le CSM (65)."},
)

# ────────────────────────────────────────────────────────────────────────────
# ASSEMBLAGE — registre complet, dans l'ordre du texte officiel
# ────────────────────────────────────────────────────────────────────────────

#: Les titres dans l'ordre de la Constitution, tels que publiés par le Conseil
#: constitutionnel (le titre XI bis et le titre XIV sont intercalés).
_TITRES: tuple[tuple[str, tuple[ArticleConstitution, ...]], ...] = (
    ("I", _TITRE_I),
    ("II", _TITRE_II),
    ("III", _TITRE_III),
    ("IV", _TITRE_IV),
    ("V", _TITRE_V),
    ("VI", _TITRE_VI),
    ("VII", _TITRE_VII),
    ("VIII", _TITRE_VIII),
    ("IX-X", _TITRE_IX_X),
    ("XI", _TITRE_XI),
    ("XII", _TITRE_XII),
    ("XIII-XIV", _TITRE_XIII_XIV),
    ("XV", _TITRE_XV),
    ("XVI", _TITRE_XVI),
)

#: Table de numérotation officielle : sert à détecter une fiche manquante.
#: 1 à 89, y compris les « bis » et « ter » écrits sous forme 34-1, 88-7, etc.
NUMEROS_ATTENDUS: tuple[str, ...] = (
    "1", "2", "3", "4",
    "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
    "20", "21", "22", "23",
    "24", "25", "26", "27", "28", "29", "30", "31", "32", "33",
    "34", "34-1", "35", "36", "36-1", "37", "37-1", "38", "39", "40", "41", "42", "43", "44",
    "45", "46", "47", "47-1", "47-2", "48", "49", "50", "50-1", "51", "51-1", "51-2",
    "52", "53", "53-1", "53-2", "54", "55",
    "56", "57", "58", "59", "60", "61", "61-1", "62", "63",
    "64", "65", "66", "66-1",
    "67", "68",
    "68-1", "68-2", "68-3",
    "69", "70", "71",
    "71-1",
    "72", "72-1", "72-2", "72-3", "72-4", "73", "74", "74-1", "75", "75-1",
    "76", "77",
    "87", "88",
    "88-1", "88-2", "88-3", "88-4", "88-5", "88-6", "88-7",
    "89",
)

#: Articles abrogés, numérotés dans le texte historique (consignés dans ABROGES).
NUMEROS_ABROGES: tuple[str, ...] = ("78", "79", "80", "81", "82", "83", "84", "85", "86", "90")


def _cle_tri(numero: str) -> tuple[int, int]:
    """Clé de tri : « 34-1 » vient après « 34 », « 51-2 » après « 51-1 »."""
    base, _, suffixe = numero.partition("-")
    try:
        return int(base), int(suffixe) if suffixe else 0
    except ValueError:  # pragma: no cover - numérotation en « bis » historique
        return int(base), 99


#: Registres des fiches en vigueur, indexées par numéro d'article.
ARTICLES: dict[str, ArticleConstitution] = {}
for _bloc, _fiches in _TITRES:
    for _fiche in _fiches:
        if _fiche.numero in ARTICLES:  # garde-fou contre un doublon silencieux
            raise ValueError(f"fiche en double pour l'article {_fiche.numero}")
        ARTICLES[_fiche.numero] = _fiche

#: Ordre de lecture du texte officiel.
ORDRE_ARTICLES: tuple[str, ...] = tuple(sorted(ARTICLES, key=_cle_tri))


# ────────────────────────────────────────────────────────────────────────────
# CONSULTATION
# ────────────────────────────────────────────────────────────────────────────

_ALINEA = re.compile(r"\s*(?:al\.?|alinéa|paragraphe)\s*\d+\s*(?:bis|ter)?$", re.IGNORECASE)
_POINT_ALINEA = re.compile(r"\.(\d+)$")


def article(numero: str) -> ArticleConstitution | None:
    """Fiche d'un article, ou None.

    Tolère les notations usuelles : « Article 49 », « art. 49 », « 49 al. 3 » et
    « 49.3 » renvoient tous à la fiche de l'article 49 — l'alinéa n'a pas de fiche
    propre, c'est l'article qui porte la règle.
    """
    cleaned = (numero or "").strip().lower()
    for prefixe in ("article ", "art. ", "art "):
        if cleaned.startswith(prefixe):
            cleaned = cleaned[len(prefixe):]
    cleaned = _ALINEA.sub("", cleaned)
    cleaned = _POINT_ALINEA.sub("", cleaned)
    cleaned = cleaned.replace("bis", "").replace("ter", "").strip()
    for candidat in (cleaned, cleaned.replace("-", "‑")):
        if candidat in ARTICLES:
            return ARTICLES[candidat]
    return None


def par_bloc(bloc: str) -> list[ArticleConstitution]:
    """Fiches d'un titre (« V », « Titre V », «XI bis »…)."""
    cle = (bloc or "").strip()
    for prefixe in ("Titre ", "titre "):
        if cle.startswith(prefixe):
            cle = cle[len(prefixe):]
    cle = cle.split(" —")[0].strip()
    libelle = Blocs.get(cle, "")
    return [f for f in (ARTICLES[n] for n in ORDRE_ARTICLES) if f.bloc == libelle] if libelle else []


def par_fonction(fonction: str) -> list[ArticleConstitution]:
    """Fiches relevant d'une fonction institutionnelle (`FONCTIONS`)."""
    return [ARTICLES[n] for n in ORDRE_ARTICLES if ARTICLES[n].fonction == fonction]


def rechercher(terme: str, limite: int = 25) -> list[dict[str, Any]]:
    """Recherche pleine texte dans les fiches : numéro, champ touché, extrait."""
    mot = (terme or "").strip().lower()
    if len(mot) < 2:
        return []
    champs = (
        ("titre", "titre"), ("résumé", "resume"), ("règles chiffrées", "regles"),
        ("opportunités", "opportunites"), ("contraintes", "contraintes"),
        ("contre-pouvoirs", "contre_pouvoirs"), ("autorité", "autorite"),
        ("mécanismes", "mecanismes"), ("leviers", "leviers"),
    )
    resultats: list[dict[str, Any]] = []
    for numero in ORDRE_ARTICLES:
        fiche = ARTICLES[numero]
        for libelle, attribut in champs:
            valeur = getattr(fiche, attribut)
            morceaux = (valeur,) if isinstance(valeur, str) else tuple(valeur)
            for morceau in morceaux:
                if mot in morceau.lower():
                    position = morceau.lower().find(mot)
                    debut = max(0, position - 60)
                    resultats.append({
                        "numero": numero,
                        "identification": f"Article {numero} — {fiche.titre}",
                        "bloc": fiche.bloc,
                        "champ": libelle,
                        "extrait": ("…" if debut else "") + morceau[debut:position + len(mot) + 90] + "…",
                    })
                    break
            else:
                continue
            break
        if len(resultats) >= limite:
            break
    return resultats


def chaine(articles: Iterable[str]) -> list[dict[str, Any]]:
    """Enveloppe d'articles : d'abord ceux demandés, puis leurs croisements directs.

    Utilité : aucun article ne fonctionne seul. Demander « 49 » doit faire remonter
    le 50 (démission), le 12 (dissolution possible), le 47 (budget) — sans quoi le
    lecteur croit que la censure suffit à faire tomber un gouvernement.
    """
    vus: list[str] = []
    for numero in articles:
        cle = (numero or "").strip()
        if cle and cle not in vus and cle in ARTICLES:
            vus.append(cle)
    bordure: list[str] = []
    for numero in list(vus):
        for lien in ARTICLES[numero].croisements:
            lien = lien.strip()
            if lien in ARTICLES and lien not in vus and lien not in bordure:
                bordure.append(lien)
    sortie: list[dict[str, Any]] = []
    for numero in vus:
        fiche = ARTICLES[numero]
        entete = {**fiche.en_dict(), "distance": 0}
        sortie.append(entete)
    for numero in sorted(bordure, key=_cle_tri):
        fiche = ARTICLES[numero]
        sortie.append({**fiche.en_dict(), "distance": 1})
    return sortie


def verrous_pour(levier: str) -> list[dict[str, Any]]:
    """Contraintes et seuils constitutionnels opposables à un levier du catalogue."""
    cle = (levier or "").strip()
    sorties = []
    for numero in ORDRE_ARTICLES:
        fiche = ARTICLES[numero]
        if cle and cle in fiche.leviers:
            sorties.append({
                "numero": numero,
                "identification": f"Article {numero} — {fiche.titre}",
                "bloc": fiche.bloc,
                "contraintes": list(fiche.contraintes),
                "regles_chiffrees": list(fiche.regles),
                "contre_pouvoirs": list(fiche.contre_pouvoirs),
                "mecanismes": list(fiche.mecanismes),
            })
    return sorties


def opportunites_pour(levier: str) -> list[dict[str, Any]]:
    """Facultés ouvertes par la Constitution à un levier du catalogue."""
    cle = (levier or "").strip()
    sorties = []
    for numero in ORDRE_ARTICLES:
        fiche = ARTICLES[numero]
        if cle and cle in fiche.leviers:
            sorties.append({
                "numero": numero,
                "identification": f"Article {numero} — {fiche.titre}",
                "bloc": fiche.bloc,
                "opportunites": list(fiche.opportunites),
                "regles_chiffrees": list(fiche.regles),
            })
    return sorties


def articles_pour_strate(strate: str) -> list[str]:
    """Numéros des articles dont l'effet touche une strate (`STRATES`)."""
    return [n for n in ORDRE_ARTICLES if strate in ARTICLES[n].strates]


def articles_pour_mecanisme(mecanisme: str) -> list[str]:
    """Numéros des articles qui organisent un mécanisme du moteur."""
    return [n for n in ORDRE_ARTICLES if mecanisme in ARTICLES[n].mecanismes]


def couverture() -> dict[str, Any]:
    """État du registre : compteurs, écarts éventuels, densité par titre."""
    par_titre: dict[str, int] = {}
    for numero in ORDRE_ARTICLES:
        par_titre[ARTICLES[numero].bloc] = par_titre.get(ARTICLES[numero].bloc, 0) + 1
    manquants = [n for n in NUMEROS_ATTENDUS if n not in ARTICLES]
    inattendus = [n for n in ORDRE_ARTICLES if n not in NUMEROS_ATTENDUS]
    densite = {
        "avec_opportunites": sum(1 for n in ORDRE_ARTICLES if ARTICLES[n].opportunites),
        "avec_contraintes": sum(1 for n in ORDRE_ARTICLES if ARTICLES[n].contraintes),
        "avec_contre_pouvoirs": sum(1 for n in ORDRE_ARTICLES if ARTICLES[n].contre_pouvoirs),
        "avec_regles_chiffrees": sum(1 for n in ORDRE_ARTICLES if ARTICLES[n].regles),
        "avec_croisements": sum(1 for n in ORDRE_ARTICLES if ARTICLES[n].croisements),
        "avec_mecanismes": sum(1 for n in ORDRE_ARTICLES if ARTICLES[n].mecanismes),
        "avec_leviers": sum(1 for n in ORDRE_ARTICLES if ARTICLES[n].leviers),
    }
    total = len(ORDRE_ARTICLES)
    return {
        "articles_en_vigueur": total,
        "articles_attendus": len(NUMEROS_ATTENDUS),
        "articles_abroges_consignes": len(ABROGES),
        "manquants": manquants,
        "inattendus": inattendus,
        "complet": not manquants and not inattendus,
        "densite": densite,
        "densite_pct": {k: round(100.0 * v / total, 1) if total else 0.0 for k, v in densite.items()},
        "par_titre": par_titre,
        "source": SOURCE_CC,
        "consulte_le": DATE_CONSULTATION,
        "version": VERSION_TEXTE,
    }


# ────────────────────────────────────────────────────────────────────────────
# PASSERELLES
# ────────────────────────────────────────────────────────────────────────────

def vers_registre_legal(
    deja_presents: Iterable[str] | None = None,
) -> dict[str, dict[str, str]]:
    """Fiches converties au format `reglements_lois.ArticleDeLoi`.

    Seuls les identifiants absents du registre existant sont produits : les
    trente-sept `CONST_ART_*` déjà vérifiés (qui portent leur propre citation) ne
    sont jamais écrasés. La clé suit la convention du registre :
    « CONST_ART_49_2 » pour l'article 49 alinéa 2, « CONST_ART_72_1 » pour
    l'article 72-1.
    """
    connus = set(deja_presents or ())
    sorties: dict[str, dict[str, str]] = {}
    for numero in ORDRE_ARTICLES:
        fiche = ARTICLES[numero]
        identifiant = "CONST_ART_" + numero.replace("-", "_")
        if identifiant in connus:
            continue
        chaine_verrous = " ; ".join(fiche.contraintes[:3]) or "aucun verrou consigné"
        chaine_opportunites = " ; ".join(fiche.opportunites[:2]) or "aucune faculté consignée"
        sorties[identifiant] = {
            "identifiant": identifiant,
            "code_ou_traite": "Constitution du 4 octobre 1958",
            "article": f"Article {numero}",
            "titre": fiche.titre,
            # Le registre juridique attend un texte : on y consigne la synthèse,
            # explicitement marquée comme telle, avec la source et sa date.
            "texte_integral": (
                f"[synthèse de travail, {VERSION_TEXTE}, source consultée le "
                f"{DATE_CONSULTATION}] {fiche.resume}"
            ),
            "strate_impactee": fiche.strates[0] if fiche.strates else "National",
            "effet_simulation": (
                f"Ce que le texte permet : {chaine_opportunites}. "
                f"Ce qui bloque : {chaine_verrous}."
            ),
        }
    return sorties


def greffe_sur_registre() -> dict[str, Any]:
    """Tente la fusion avec `reglements_lois.REGISTRE_LEGAL` (import toléré en échec)."""
    try:  # pragma: no cover - le registre existe dans le dépôt
        from . import reglements_lois as _rl
    except Exception:  # noqa: BLE001 - utilisation hors paquet
        try:
            import reglements_lois as _rl  # type: ignore
        except Exception:
            return {"disponible": False, "ajoutes": 0, "exists": 0}
    connus = set(_rl.REGISTRE_LEGAL)
    apports = vers_registre_legal(connus)
    for identifiant, donnees in apports.items():
        _rl.REGISTRE_LEGAL[identifiant] = _rl.ArticleDeLoi(**donnees)
    return {"disponible": True, "ajoutes": len(apports), "exists": len(connus)}


def synthese_pour_api() -> dict[str, Any]:
    """Charge utile de la page « Constitution analysée » et de l'API /constitution."""
    return {
        "titre": "Constitution analysée article par article",
        "accroche": (
            "Ce que la Constitution de 1958 permet, ce qu'elle interdit, et qui peut "
            "bloquer ce qu'elle permet."
        ),
        "methode": (
            "Pour chaque article en vigueur : règles chiffrées, opportunités, contraintes, "
            "contre-pouvoirs, croisements avec les autres articles, strates touchées, "
            "mécanismes du moteur et leviers du catalogue. Synthèse de travail adossée au "
            "texte officiel ; les articles courts sont cités in extenso. Un modèle, pas une "
            "prophétie : ces fiches disent ce que le droit permet et ce qui le bloque, jamais "
            "ce qui arrivera."
        ),
        "source": SOURCE_CC,
        "version": VERSION_TEXTE,
        "consulte_le": DATE_CONSULTATION,
        "couverture": couverture(),
        "fonctions": [
            {"nom": f, "articles": [a.numero for a in par_fonction(f)]} for f in FONCTIONS
        ],
        "titres": [
            {"bloc": libelle, "articles": [a.numero for a in par_bloc(cle)]}
            for cle, libelle in ((c, Blocs[c]) for c in _BLOCS_ORDONNES)
        ],
        "articles": [ARTICLES[n].en_dict() for n in ORDRE_ARTICLES],
        "abroges": list(ABROGES),
    }


#: Ordre d'affichage des titres (le titre XI bis et les titres IX/X sont fusionnés
#: dans les tables, mais l'affichage suit la numération officielle).
_BLOCS_ORDONNES: tuple[str, ...] = (
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XI bis", "XII",
    "XIII", "XIV", "XV", "XVI",
)


def bloc_de(numero: str) -> str:
    """Titre officiel d'un article (« Titre V — Des rapports… »)."""
    fiche = article(numero)
    return fiche.bloc if fiche else ""


def resume_console() -> str:
    """Bloc de texte pour `python -m simulateur.cli` et les journaux."""
    etat = couverture()
    lignes = [
        f"Constitution analysée — {etat['articles_en_vigueur']} articles en vigueur, "
        f"{etat['articles_abroges_consignes']} abrogés consignés.",
        f"Texte : {VERSION_TEXTE} (source consultée le {DATE_CONSULTATION}).",
    ]
    if etat["manquants"]:
        lignes.append("Articles attendus non fichés : " + ", ".join(etat["manquants"]))
    if etat["inattendus"]:
        lignes.append("Articles fichés hors numérotation officielle : "
                      + ", ".join(etat["inattendus"]))
    lignes.append("Densité : " + ", ".join(
        f"{k.replace('_', ' ')} {v} %" for k, v in etat["densite_pct"].items()
    ))
    return "\n".join(lignes)


__all__ = [
    "ABROGES", "ARTICLES", "Blocs", "DATE_CONSULTATION", "FONCTIONS",
    "NUMEROS_ABROGES", "NUMEROS_ATTENDUS", "ORDRE_ARTICLES", "SOURCE_CC", "STRATES",
    "VERSION_TEXTE", "ArticleConstitution", "articles_pour_mecanisme",
    "articles_pour_strate", "bloc_de", "chaine", "couverture", "greffe_sur_registre",
    "opportunites_pour", "par_bloc", "par_fonction", "rechercher", "resume_console",
    "synthese_pour_api", "verrous_pour", "vers_registre_legal",
]
