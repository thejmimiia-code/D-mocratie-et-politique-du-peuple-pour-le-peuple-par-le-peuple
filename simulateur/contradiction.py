"""Registre des objections fortes, des concessions et des réponses (docs/05, 20 et 21).

Le guide d'autodéfense du dépôt préparait des ripostes : il répondait à l'attaque la
plus faible, pas à la meilleure. Ce module renverse la charge. Une objection n'y est
pas une caricature à démonter, c'est une thèse qu'on écrit au mieux avant d'y répondre.

Chaque entrée porte sept pièces, et aucune n'est facultative :

1. ``attaque_faible`` — l'attaque telle qu'on l'entend, conservée pour mémoire : elle
   explique pourquoi le guide d'origine répondait à côté.
2. ``objection_forte`` — la même critique rédigée comme le ferait un contradicteur
   compétent et honnête, avec ce qui la rend difficile.
3. ``concession`` — ce que le dépôt admet, sans marchandage. Une objection sans
   concession est une objection qu'on n'a pas lue.
4. ``maintien`` — ce qui survit à la concession, et pourquoi. Sans cette pièce, la
   concession serait un ralliement.
5. ``falsification`` — le fait, nommé et vérifiable, qui ferait changer d'avis. Une
   position qu'aucun fait ne peut ébranler n'est pas une position, c'est une croyance.
6. ``sources`` — internes (un chemin du dépôt, avec sa section) ou externes (une
   référence datée déjà citée par le dépôt ou par un de ses audits). Le module refuse
   une source interne qui ne correspond à aucun fichier.
7. ``statut`` et ``changements`` — où en est le traitement, et ce qu'il a déjà changé
   dans le dépôt. Un statut « concédée » sans changement écrit est refusé.

Les chiffres ne sont jamais recopiés : la cible d'une mesure vient du levier du
catalogue (``parametres.LEVIERS``), par ``rendement_du_levier()``. Une mesure dont le
levier n'existe pas est refusée au chargement du module.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from simulateur.parametres import LEVIERS

#: Les quatre statuts possibles d'une objection, avec leur définition exacte.
STATUTS: dict[str, str] = {
    "refutee": "traitée et la réponse tient : la critique porte à côté, sous sa forme forte",
    "partiellement_concedee": "une partie est admise et le texte, le chiffre ou la mesure change",
    "concedee": "admise entièrement : la mesure est abandonnée, remplacée ou re-écrite",
    "en_cours": "reconnue comme valable, traitement non terminé et suivi par une issue",
    "ouverte": "reçue et reconnue, chantier non engagé — le dire plutôt que de l'afficher « en cours »",
}

#: Les deux familles d'objections : celles qui visent une mesure, celles qui visent le modèle.
FAMILLES: dict[str, str] = {
    "mesure": "vise une mesure chiffrée du plan de mandature (les dix fiches du guide)",
    "modele": "vise une hypothèse, un seuil ou une écriture du simulateur lui-même",
}

#: Longueurs minimales, en caractères, pour qu'une pièce soit autre chose qu'un slogan.
PROFONDEURS_MINIMALES: dict[str, int] = {
    "objection_forte": 220,
    "concession": 160,
    "maintien": 200,
    "falsification": 120,
}


@dataclass(frozen=True)
class Source:
    """Une pièce justificative : un fichier du dépôt, ou une référence externe datée."""

    nature: str  # « interne » ou « externe »
    reference: str
    #: Pour une source interne : chemin relatif au dépôt. Pour une source externe : vide.
    chemin: str = ""
    #: Date ou millésime de la référence, obligatoire pour une source externe.
    date: str = ""
    #: Pièce d'origine quand l'objection vient d'un audit : « issue #7 », « docs/18 »…
    origine: str = ""


@dataclass(frozen=True)
class Objection:
    """Une objection écrite au mieux, et la réponse du dépôt, pièce par pièce."""

    cle: str
    numero: int
    famille: str  # clé de FAMILLES
    titre: str
    #: Levier du catalogue visé, quand l'objection vise une mesure chiffrée.
    levier: str = ""
    #: Gage retenu par le dossier, en Md€ par an, négatif s'il s'agit d'un coût.
    #: Vérifié contre l'en-tête de la fiche correspondante dans docs/05.
    gage_mde_an: float | None = None
    #: Fiche du guide (1 à 10) pour les objections de la famille « mesure ».
    fiche: int = 0
    attaque_faible: str = ""
    objection_forte: str = ""
    concession: str = ""
    maintien: str = ""
    falsification: str = ""
    statut: str = "en_cours"
    changements: str = ""
    suivi: str = ""
    sources: tuple[Source, ...] = field(default_factory=tuple)

    @property
    def statut_libelle(self) -> str:
        return STATUTS[self.statut]


@dataclass(frozen=True)
class ContreModele:
    """Un modèle alternatif cohérent, auquel le plan se mesure — pas un repoussoir."""

    cle: str
    titre: str
    porte_par: str
    these: str
    ce_que_le_simulateur_en_dit: str
    concession: str
    divergence: str
    ouverts: str = ""
    #: Clés de scénarios réellement servies par `/api/scenarios`.
    scenarios: tuple[str, ...] = ()
    #: Clés de préréglages réelles du catalogue.
    presets: tuple[str, ...] = ()


def _s_interne(chemin: str, section: str = "", origine: str = "") -> Source:
    return Source(nature="interne", reference=section, chemin=chemin, origine=origine)


def _s_externe(reference: str, date: str, origine: str = "") -> Source:
    return Source(nature="externe", reference=reference, date=date, origine=origine)


# --------------------------------------------------------------------------------------
# Les dix objections de mesure : une par fiche du guide, adossée à son levier réel
# --------------------------------------------------------------------------------------

OBJECTIONS: dict[str, Objection] = {
    "casier_b2": Objection(
        cle="casier_b2",
        numero=1,
        fiche=1,
        famille="mesure",
        titre="Casier judiciaire B2 pour l'éligibilité",
        levier="reforme_casier_b2",
        attaque_faible="« C'est une dérive autoritaire : les juges élimineront les candidats d'opposition. »",
        objection_forte=(
            "« Votre guide cite la validation de 2017 et omet la censure de 2010 : le Conseil "
            "constitutionnel a censuré l'inéligibilité *automatique* de l'article L. 7 du code "
            "électoral au nom de l'individualisation des peines (art. 8 de la DDHC). Or votre "
            "dispositif confie à un filtre algorithmique branché sur le casier le soin d'écarter "
            "un candidat : c'est une automaticité, et c'est un algorithme — non un juge — qui "
            "décide de l'accès à une fonction élective. Ce qui est constitutionnel, c'est une "
            "peine prononcée par un juge ; votre passerelle IJ-CJN doit donc vérifier une peine "
            "existante, pas la créer. Tant que la rédaction ne le dit pas, la mesure est censurable. »"
        ),
        concession=(
            "Le filtre automatique tel qu'il est rédigé au volet 1 n'est pas défendable : la "
            "vérification doit porter sur une peine déjà prononcée (art. 131-26-2 du code pénal, "
            "étendu aux atteintes à la probité), et l'interrogation du casier n'est qu'un moyen "
            "de la constater. La voie juridique change, pas seulement la plaidoirie."
        ),
        maintien=(
            "L'exigence de probité tient : des centaines de professions réglementées — sécurité, "
            "banque, fonction publique — imposent un casier vierge pour des responsabilités sans "
            "commune mesure avec la gestion d'un budget public. Le Conseil constitutionnel a validé "
            "la peine complémentaire obligatoire d'inéligibilité dès lors que le juge peut en "
            "dispenser par décision motivée. Ce qui reste à obtenir est une extension du champ de "
            "cette peine, pas un pouvoir nouveau donné à une machine."
        ),
        falsification=(
            "Si une décision du Conseil constitutionnel censurait l'extension de l'article "
            "131-26-2 CP à l'ensemble des atteintes à la probité, ou si la CNIL jugeait que "
            "l'interrogation automatisée du bulletin n° 2 en préfecture excède le traitement "
            "autorisé, nous renoncerions à la vérification automatisée au profit d'une attestation "
            "délivrée par le juge, et le dirions dans le volet 1."
        ),
        statut="partiellement_concedee",
        changements="volet 1 à réécrire sur l'option « extension de la peine » plutôt que « filtre »",
        suivi="issue #7, § 1",
        sources=(
            _s_interne("docs/01_DEMOCRATIE_INSTITUTIONS.md", "§ II.2 — verrous constitutionnels"),
            _s_interne("docs/05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md", "FICHE 1"),
            _s_externe("Conseil constitutionnel, décisions n° 2010-6/7 QPC (11 juin 2010) "
                       "et n° 2017-752 DC (8 septembre 2017)", "2010 et 2017", "issue #7"),
        ),
    ),
    "vote_blanc": Objection(
        cle="vote_blanc",
        numero=2,
        fiche=2,
        famille="mesure",
        titre="Vote blanc invalidant",
        levier="reforme_vote_blanc",
        attaque_faible="« Vous allez plonger le pays dans le chaos et la vacance perpétuelle. »",
        objection_forte=(
            "« Avec un seuil à 50 % des exprimés, votre mesure ne se déclenchera jamais : c'est "
            "une réforme symbolique vendue comme un outil de régulation. La variante qui la rend "
            "opérante — le blanc arrivé en tête — est précisément celle que vous écartez, parce "
            "qu'elle rend une élection annulable au premier tour d'une présidentielle éclatée. "
            "Pire, votre guide affirme deux choses invérifiables : le coût de 150 M€ par tour "
            "n'est pas sourcé, et « aucun électorat n'a réitéré un rejet blanc » ne s'appuie sur "
            "aucun précédent comparable, puisque la reconnaissance du vote blanc n'existe nulle "
            "part à ce niveau. Vous mélangez le fait et le souhait. »"
        ),
        concession=(
            "Deux affirmations du guide doivent être sourcées ou retirées ; le seuil de 50 % des "
            "exprimés est, en pratique, inatteignable, et le dépôt doit le dire au lieu de laisser "
            "croire à un mécanisme fréquent. La demande existe et propose une autre règle : des "
            "pétitions déposées sur la plateforme de l'Assemblée nationale retiennent la variante "
            "« blanc en tête ». Comparer les trois règles est un travail à faire, pas une faiblesse "
            "à masquer."
        ),
        maintien=(
            "La reconnaissance du vote blanc ne coûte rien au contribuable et son coût "
            "d'organisation est déjà couvert par la réfaction sur les dotations publiques des "
            "partis concernés : l'argument budgétaire de la fiche tient. Et le choix du seuil est "
            "un choix politique assumé — la prudence institutionnelle contre l'effectivité — qu'il "
            "faut présenter comme tel, avec sa contrepartie assumée : une réforme qui ne se "
            "déclenche presque jamais protège la stabilité et ne répare pas la défiance."
        ),
        falsification=(
            "Si trois scrutins nationaux consécutifs montraient une part de blanc stable et faible "
            "malgré la reconnaissance du vote blanc, la mesure devrait être présentée comme "
            "symbolique et non comme un instrument de régulation ; symétriquement, si le seuil de "
            "50 % des exprimés était atteint une seule fois, nos hypothèses d'effet seraient à "
            "réviser, car nous les croyons aujourd'hui improbables."
        ),
        statut="en_cours",
        changements="deux affirmations du guide à sourcer ou retirer ; les trois règles à comparer",
        suivi="issue #7, § 2",
        sources=(
            _s_interne("docs/01_DEMOCRATIE_INSTITUTIONS.md", "§ III — procédure et clef de carence"),
            _s_interne("docs/05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md", "FICHE 2"),
            _s_externe("Pétitions de l'Assemblée nationale n° 5046 (26/01/2026) et n° 5638 "
                       "(07/04/2026)", "2026", "issue #7"),
        ),
    ),
    "ric": Objection(
        cle="ric",
        numero=3,
        fiche=3,
        famille="mesure",
        titre="Référendum d'initiative citoyenne sécurisé",
        levier="reforme_ric",
        attaque_faible="« Les hackers russes truqueront les pétitions et les fermes de bots "
                       "imposeront des lois démagogiques. »",
        objection_forte=(
            "« Vous promettez un référendum national en ligne “aussi impossible à pirater que la "
            "Banque de France”. Aucun État de l'Union européenne n'organise de scrutin politique "
            "national par internet, et le guide de l'ANSSI sur le vote par internet porte "
            "explicitement sur les élections non politiques ; le référentiel de la CNIL va dans le "
            "même sens. En France, le vote en ligne pour un scrutin politique existe seulement pour "
            "les Français de l'étranger. Le secret du vote et la vérifiabilité universelle du "
            "dépouillement sont en tension : c'est la phrase qu'un expert citera contre tout le "
            "projet. Et votre RIC révocatoire se heurte à l'article 27 de la Constitution : "
            "“tout mandat impératif est nul”. »"
        ),
        concession=(
            "Le canal numérique ne doit pas être le mode par défaut du vote d'un référendum "
            "national. La collecte de signatures est un problème différent — authenticité et "
            "unicité, sans secret — et y convient : FranceConnect+ et la plateforme de pétitions "
            "de l'Assemblée le font déjà. Le RIC révocatoire national doit être abandonné, limité "
            "aux exécutifs locaux, ou explicitement justifié contre l'article 27."
        ),
        maintien=(
            "Le seuil de 500 000 signatures est dans la norme des démocraties à initiative "
            "populaire (Suisse, Italie, Californie) et le verrou du Conseil constitutionnel avant "
            "vote protège les droits fondamentaux ; ce n'est pas la quantité de signatures, mais le "
            "passage de « peut » à « doit » qui change le rapport de force. La signature "
            "électronique reste défendable pour la phase de collecte, qui n'a pas à garantir le "
            "secret du vote."
        ),
        falsification=(
            "Si l'ANSSI ou le Conseil d'État confirmait qu'un vote national à enjeu politique ne "
            "peut garantir à la fois le secret et la vérifiabilité, nous fixerions le vote papier "
            "en bureau comme seul canal et ne garderions le numérique que pour la signature ; si le "
            "Conseil constitutionnel jugeait le RIC révocatoire national contraire à l'article 27, "
            "nous le retirerions du texte."
        ),
        statut="partiellement_concedee",
        changements="canal de vote à redéfinir (papier par défaut) ; RIC révocatoire à trancher",
        suivi="issue #7, § 3",
        sources=(
            _s_interne("docs/01_DEMOCRATIE_INSTITUTIONS.md", "§ IV — RIC"),
            _s_interne("docs/05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md", "FICHE 3"),
            _s_externe("ANSSI, guide du vote par internet (mis à jour 2026) ; CNIL, délibération "
                       "n° 2019-053 ; Constitution, art. 27", "2019 à 2026", "issue #7"),
        ),
    ),
    "fraude_fiscale_ia": Objection(
        cle="fraude_fiscale_ia",
        numero=4,
        fiche=4,
        famille="mesure",
        titre="Traque de la grande fraude fiscale par IA",
        levier="lutte_fraude_fiscale_ia",
        gage_mde_an=10.0,
        attaque_faible="« C'est de l'argent magique, et vos algorithmes fliqueront tout le monde. »",
        objection_forte=(
            "« Votre ligne de 10 Md€ par an est un rendement *encaissé*, alors que le bilan 2025 de "
            "la DGFiP affiche 17,1 Md€ notifiés pour 11,4 Md€ encaissés, dont 2,8 Md€ seulement "
            "attribués à l'IA — et les effectifs de contrôle baissent. Doubler le recouvrement "
            "actuel en cinq ans, avec un taux de transformation notifié → encaissé de l'ordre de "
            "60 à 70 % et des délais de deux à quatre ans, suppose une bascule que rien n'annonce. "
            "Votre seuil de protection à 50 000 € réduit encore l'assiette accessible. »"
        ),
        concession=(
            "Le rendement annoncé est un rendement encaissé, et l'atterrissage en année 5 est trop "
            "rapide : le dépôt doit écrire « +10 Md€ notifiés, 6 à 7 Md€ encaissés » ou viser "
            "l'année 7. Le délai et le taux de transformation entrent dans le chiffrage, pas dans "
            "une note de bas de page."
        ),
        maintien=(
            "Le gisement n'est pas en cause : la fraude fiscale est chiffrée entre 80 et 100 Md€ "
            "par an et les précédents étrangers cités par la fiche — système SII en Espagne, "
            "facturation électronique en Italie — montrent qu'un investissement technologique "
            "produit des résultats rapidement. Récupérer 6 à 10 Md€ reste une fraction du gisement. "
            "Ce qui est en débat est la vitesse, pas l'existence de l'argent."
        ),
        falsification=(
            "Si le prochain bilan de la DGFiP montrait que la part encaissée grâce à l'IA stagne "
            "sous 2 Md€ par an, nous réduirions l'échéancier à la moitié du montant et le "
            "déplacerions en année 7, plutôt que de conserver une ligne que les faits démentent."
        ),
        statut="partiellement_concedee",
        changements="échéancier et fourchette (notifié / encaissé) à porter dans les hypothèses",
        suivi="issue #6",
        sources=(
            _s_interne("docs/02_RECETTES_ET_TRANSACTIONS.md", "§ fraude fiscale"),
            _s_interne("docs/05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md", "FICHE 4"),
            _s_externe("DGFiP, bilan du contrôle fiscal 2025 : 17,1 Md€ notifiés, 11,4 Md€ "
                       "encaissés, 2,8 Md€ via l'IA", "2025", "issue #6"),
        ),
    ),
    "conditionnement_aides": Objection(
        cle="conditionnement_aides",
        numero=5,
        fiche=5,
        famille="mesure",
        titre="Conditionnement des aides aux entreprises",
        levier="conditionnement_aides_entreprises",
        gage_mde_an=15.0,
        attaque_faible="« Vous coulez la compétitivité et vous inventez le Gosplan. »",
        objection_forte=(
            "« La commission d'enquête du Sénat recense 2 267 dispositifs d'aide, 211 Md€ au sens "
            "large, 108 Md€ au sens strict, dont 255 aides — environ 43 Md€ — ne sont ni suivies ni "
            "évaluées. Conditionner 15 Md€ suppose de toucher des dispositifs qui ont chacun leur "
            "base légale, leurs bénéficiaires et parfois leur cadre européen : votre “Smart "
            "Clearing” règle la mécanique de contrôle, pas le droit. Et un contrat en cours ne se "
            "dénonce pas parce qu'un croisement de données a changé d'avis. »"
        ),
        concession=(
            "La difficulté est juridique et calendaire, pas technique : 15 Md€ en année 5 sans "
            "échéancier par famille d'aides est invendable. Le dépôt doit publier la liste des "
            "dispositifs visés, famille par famille, et l'ordre de passage en revue."
        ),
        maintien=(
            "Le volume existe et il est documenté : 255 dispositifs non évalués, soit de l'ordre de "
            "43 Md€. Conditionner n'est pas supprimer : l'entreprise qui maintient ses emplois et "
            "n'extrait pas de dividende exceptionnel conserve son aide, sans formulaire "
            "supplémentaire. Et l'exclusion des entreprises de moins de 250 salariés limite "
            "l'impact administratif aux groupes qui ont les moyens de le porter."
        ),
        falsification=(
            "Si la revue de dépenses, dispositif par dispositif, montrait un rendement total "
            "inférieur à 5 Md€ à droit constant, la cible serait ramenée à ce montant et le reste "
            "du gage cherché ailleurs — l'équilibre à 60 = 60 est une cible, pas une identité."
        ),
        statut="en_cours",
        changements="liste des dispositifs et échéancier à publier avant tout chiffrage définitif",
        suivi="issue #6",
        sources=(
            _s_interne("docs/03_ECONOMIES_ET_EFFICACITE_ETAT.md", "§ conditionnement des aides"),
            _s_interne("docs/05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md", "FICHE 5"),
            _s_externe("Sénat, commission d'enquête sur les aides publiques aux entreprises "
                       "(juillet 2025) : 211 Md€ au sens large, 108 Md€ au sens strict, "
                       "255 aides non évaluées", "2025", "issue #6"),
        ),
    ),
    "superprofits": Objection(
        cle="superprofits",
        numero=6,
        fiche=6,
        famille="mesure",
        titre="Taxe sur les superprofits et les rachats d'actions",
        levier="taxe_superprofits",
        gage_mde_an=6.0,
        attaque_faible="« Les capitaux et les sièges sociaux vont fuir vers la Suisse ou les "
                       "États-Unis. »",
        objection_forte=(
            "« Votre assiette est conjoncturelle : la contribution sur la rente inframarginale de "
            "2023 a rapporté très en deçà des prévisions, et une taxe assise sur les rachats "
            "d'actions dépend du cycle boursier. Vous comptez 6 Md€ par an comme une recette "
            "permanente, alors que la France prélève déjà une contribution exceptionnelle sur les "
            "grandes entreprises : rien ne garantit que vos deux assiettes ne se recouvrent pas. »"
        ),
        concession=(
            "Le rendement doit être présenté comme conjoncturel et hors socle, ou l'assiette "
            "resserrée sur les seuls rachats d'actions ; la superposition avec la contribution "
            "exceptionnelle existante doit être documentée avant que le chiffre entre dans "
            "l'équilibre."
        ),
        maintien=(
            "La matière est là : le CAC 40 a distribué plus de 90 Md€ à ses actionnaires en 2023 "
            "et 2024, et la clause d'exonération productive à 100 % répond à l'argument de la "
            "fuite : réinvestir en France, dans les machines, la décarbonation, la recherche ou "
            "les salaires annule la taxe. Ce n'est donc pas un prélèvement sur l'investissement."
        ),
        falsification=(
            "Si deux exercices consécutifs donnaient un rendement inférieur à 2 Md€ par an, la "
            "recette serait sortie du socle permanent et le gage reconstitué ailleurs."
        ),
        statut="partiellement_concedee",
        changements="recette à sortir du socle permanent ou à réassoir sur les rachats d'actions",
        suivi="issue #6",
        sources=(
            _s_interne("docs/02_RECETTES_ET_TRANSACTIONS.md", "§ superprofits et rachats d'actions"),
            _s_interne("docs/05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md", "FICHE 6"),
            _s_externe("Rendement de la contribution sur la rente inframarginale (2023) très "
                       "inférieur aux prévisions initiales — à re-sourcer", "2023", "issue #6"),
        ),
    ),
    "extension_ttf": Objection(
        cle="extension_ttf",
        numero=7,
        fiche=7,
        famille="mesure",
        titre="Extension de la taxe sur les transactions financières",
        levier="extension_ttf",
        gage_mde_an=5.0,
        attaque_faible="« Les traders videront La Défense en deux heures. »",
        objection_forte=(
            "« La TTF française rapporte de l'ordre de 2 Md€ par an : vous en attendez 5, soit "
            "deux fois et demie plus, en élargissant l'assiette au dénouement-livraison. Mais "
            "cette extension bute sur les exemptions de tenue de marché et sur le risque que la "
            "compensation se déplace ; et le précédent britannique que vous citez — le Stamp Duty — "
            "démontre qu'une taxe ne tue pas une place, pas qu'elle rapporte ce que vous annoncez. »"
        ),
        concession=(
            "Le rendement de l'extension est incertain : il doit être adossé aux volumes "
            "réellement compensés et dénoués en France, avec un mécanisme anti-contournement "
            "évalué avant publication. 5 Md€ est une cible d'étude d'impact, pas un acquis."
        ),
        maintien=(
            "Le principe d'émission reste l'argument décisif : un titre français négocié à Londres "
            "reste taxable au dépositaire, donc délocaliser une salle de marché ne fait pas "
            "disparaître la matière imposable. Le Stamp Duty prouve la survie de la place de "
            "Londres malgré des décennies de taxe : ce point de la fiche n'est pas atteint."
        ),
        falsification=(
            "Si l'étude d'impact montrait une perte de volumes compensés à Paris supérieure au "
            "gain fiscal attendu, nous abandonnerions l'extension du dépositaire pour ne garder "
            "qu'un élargissement d'assiette strictement mesuré."
        ),
        statut="en_cours",
        changements="chiffrage à adosser aux volumes réels ; mécanisme anti-contournement à évaluer",
        suivi="issue #6",
        sources=(
            _s_interne("docs/02_RECETTES_ET_TRANSACTIONS.md", "§ extension de la TTF"),
            _s_interne("docs/05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md", "FICHE 7"),
            _s_externe("Rendement de la TTF française de l'ordre de 2 Md€ par an — à vérifier "
                       "sur le PLF le plus récent", "2025", "issue #6"),
        ),
    ),
    "fusion_doublons": Objection(
        cle="fusion_doublons",
        numero=8,
        fiche=8,
        famille="mesure",
        titre="Fusion des doublons territoriaux",
        levier="fusion_doublons",
        gage_mde_an=8.0,
        attaque_faible="« Vous démantèlez l'État et détruisez les services publics de proximité. »",
        objection_forte=(
            "« La Cour des comptes, sur les fusions de régions de 2016, n'a pas constaté "
            "d'économies nettes à court terme : vos 8 Md€ par an en cinq ans contredisent le seul "
            "précédent français comparable. Et “zéro licenciement” avec 8 Md€ d'économies reste "
            "une équation non écrite : où passent les agents, sur quelles missions, avec quelle "
            "formation ? Sans le dire, vos économies sont des économies fictives. »"
        ),
        concession=(
            "8 Md€ à cinq ans est ambitieux au regard du précédent de 2016 : la cible doit être "
            "étalée ou réduite, et l'économie présentée comme un plan de réaffectation chiffré — "
            "effectifs, missions, calendrier de formation — et non comme un solde."
        ),
        maintien=(
            "Le gisement est documenté par la Cour des comptes elle-même, qui chiffre le "
            "millefeuille à plus de 10 à 12 Md€ par an : chevauchements d'ingénierie, syndicats "
            "mixtes sans activité, comités sans objet. Et la fiche ne propose aucune suppression de "
            "poste : le non-remplacement sur les fonctions de siège est l'outil, pas le licenciement."
        ),
        falsification=(
            "Si le premier exercice complet ne dégageait pas au moins 1,5 Md€ d'économies "
            "constatées par la Cour des comptes, la cible serait révisée et le calendrier étalé, "
            "sans chercher dans le rapport une ligne qui sauve le chiffre."
        ),
        statut="partiellement_concedee",
        changements="cible à étaler et à écrire comme plan de réaffectation chiffré",
        suivi="issue #6",
        sources=(
            _s_interne("docs/03_ECONOMIES_ET_EFFICACITE_ETAT.md", "§ fusion des doublons"),
            _s_interne("docs/05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md", "FICHE 8"),
            _s_externe("Cour des comptes, suites des fusions de régions de 2016 : pas d'économies "
                       "nettes à court terme — à citer précisément", "2016 à 2024", "issue #6"),
        ),
    ),
    "commande_publique": Objection(
        cle="commande_publique",
        numero=9,
        fiche=9,
        famille="mesure",
        titre="Mutualisation de la commande publique",
        levier="commande_publique",
        gage_mde_an=6.0,
        attaque_faible="« Vos centrales d'achat tueront les artisans locaux au profit d'Amazon. »",
        objection_forte=(
            "« Votre fiche demande deux choses contraires : massifier pour obtenir 3 % de gain et "
            "allotter pour réserver 30 % des lots aux PME — or l'allotissement renchérit souvent le "
            "prix unitaire. Le périmètre des 200 Md€ n'est pas défini (État, collectivités, "
            "hôpitaux ?), et un gain uniforme de 3 % sur des familles d'achats aux élasticités "
            "très différentes — énergie, consommables hospitaliers, travaux — n'a pas de base "
            "documentée. »"
        ),
        concession=(
            "Le périmètre doit être défini et le gain différencié par famille d'achats ; les gains "
            "de massification doivent être démontrés sur un pilote avant d'être généralisés dans "
            "le chiffrage."
        ),
        maintien=(
            "La massification porte sur des achats standardisés — énergie, médicaments, "
            "consommables — que les TPE ne fournissent pas : la réserver aux familles où les PME "
            "sont absentes lève la contradiction avec l'allotissement. Les 200 Md€ de commande "
            "publique ne sont pas en débat, et 3 % sur les seules familles centralisables est un "
            "ordre de grandeur défendable."
        ),
        falsification=(
            "Si le pilote sur une famille d'achats ne dégageait pas au moins la moitié du gain "
            "annoncé, le chiffrage serait réduit d'autant et la cible portée à périmètre réduit."
        ),
        statut="en_cours",
        changements="périmètre et gain par famille d'achats à publier ; pilote avant généralisation",
        suivi="issue #6",
        sources=(
            _s_interne("docs/03_ECONOMIES_ET_EFFICACITE_ETAT.md", "§ commande publique"),
            _s_interne("docs/05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md", "FICHE 9"),
            _s_externe("Code de la commande publique, art. L. 2113-10 (allotissement) et "
                       "L. 2112-2 (critères) — cités par la fiche", "2018 à 2026",
                       "docs/05, FICHE 9"),
        ),
    ),
    "tva_energie": Objection(
        cle="tva_energie",
        numero=10,
        fiche=10,
        famille="mesure",
        titre="Baisse de la TVA sur l'énergie à 5,5 %",
        levier="tva_energie_5_5",
        gage_mde_an=-9.0,
        attaque_faible="« C'est illégal en Europe et Total empochera la différence. »",
        objection_forte=(
            "« Bercy chiffre la mesure à 6,8 Md€ — 4,5 pour l'électricité, 2,3 pour le gaz — pas "
            "9. Qui plus est, le taux réduit sur les abonnements a été supprimé par la loi de "
            "finances pour 2025, à effet du 1er août 2025 : votre mesure consiste à rouvrir un "
            "régime que le législateur vient de fermer, ce qui suppose de revenir sur une décision "
            "récente et de la financer. Enfin, un verrou de répercussion inscrit dans la loi ne "
            "garantit rien si le régulateur ne dispose pas des moyens de le faire respecter sur "
            "des factures d'abonnement. »"
        ),
        concession=(
            "Le chiffre de 9 Md€ n'est pas vérifié et le dépôt le reconnaît lui-même dans le "
            "catalogue : le coût doit être ramené à la fourchette 6,8 à 9 Md€ selon le périmètre "
            "retenu — abonnement seul ou abonnement et consommation. Le financement (superprofits, "
            "niches) doit être recalculé sur ce montant, sans quoi l'équilibre est faux."
        ),
        maintien=(
            "La mesure est légale : la directive (UE) 2022/542 autorise explicitement les États "
            "membres à appliquer un taux réduit à l'électricité, au gaz naturel et aux réseaux de "
            "chaleur. Taxer le chauffage au taux d'un produit de luxe reste un choix politique "
            "contestable, et le gain de pouvoir d'achat par foyer — même recalculé sur 6,8 Md€ — "
            "reste réel : la mesure n'a pas besoin des 9 Md€ pour tenir son argument."
        ),
        falsification=(
            "Si le chiffrage définitif d'un projet de loi de finances confirmait 6,8 Md€ tout "
            "compris, le coût affiché dans le volet 4 serait corrigé et le financement rééquilibré ; "
            "si la CRE ou la DGCCRF établissaient que le verrou de répercussion est incontrôlable, "
            "la mesure serait refusée par le principe « pas de baisse annoncée, pas de baisse "
            "constatée »."
        ),
        statut="partiellement_concedee",
        changements="coût à ramener à la fourchette 6,8-9 Md€ ; financement à rééquilibrer",
        suivi="issue #6",
        sources=(
            _s_interne("docs/04_POUVOIR_D_ACHAT_ET_TRAJECTOIRE.md", "§ TVA énergie"),
            _s_interne("docs/05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md", "FICHE 10"),
            _s_interne("simulateur/parametres.py", "levier tva_energie_5_5 : « chiffrage non vérifié »"),
            _s_externe("Bercy (06/2024) : 4,5 Md€ électricité + 2,3 Md€ gaz = 6,8 Md€ ; "
                       "loi n° 2025-127 du 14 février 2025, art. 20", "2024 et 2025", "issue #6"),
        ),
    ),
}


# --------------------------------------------------------------------------------------
# Les objections de modèle : elles visent le simulateur, pas une mesure
# --------------------------------------------------------------------------------------

OBJECTIONS.update({
    "modele_recettes_non_indexees": Objection(
        cle="modele_recettes_non_indexees",
        numero=11,
        famille="modele",
        titre="Recettes et dépenses figées en euros courants",
        attaque_faible="« Votre modèle est faux, donc le plan est faux. »",
        objection_forte=(
            "« Le PIB nominal de votre moteur croît de 1,9 % par an, mais la base de recettes et "
            "de dépenses primaires reste constante en euros courants sur les cinq années. "
            "Conséquence mécanique : le ratio de déficit s'améliore d'environ deux dixièmes de "
            "point sans aucune mesure, ce qui avantage toute politique simulée — y compris le "
            "statu quo, qui passe de 5,11 % à 4,85 % par pure convention de calcul. »"
        ),
        concession=(
            "L'hypothèse doit être rendue explicite et corrigée : recettes et dépenses suivent "
            "l'activité nominale, au moins à élasticité unitaire. Le contre-calcul documenté "
            "replace l'atterrissage du plan autour de 3,05 % en année 5 avec cette seule "
            "correction — toujours très au-dessus de zéro, mais plus sous 3 %."
        ),
        maintien=(
            "L'écart au statu quo reste large — de l'ordre de 1,8 point de PIB — et c'est lui que "
            "le simulateur sert à mesurer, pas une valeur absolue idéale. Le dépôt écrit depuis "
            "l'origine que le modèle n'est pas une prophétie ; corriger une hypothèse de "
            "convention ne change pas le sens du résultat."
        ),
        falsification=(
            "Si l'indexation des recettes sur le PIB nominal ne changeait pas le classement des "
            "politiques comparées (le plan restant meilleur que le statu quo et que l'austérité), "
            "l'argument du plan serait confirmé ; si elle inversait un classement, c'est la mesure "
            "concernée qu'il faudrait réexaminer."
        ),
        statut="partiellement_concedee",
        changements="hypothèse à basculer dans un jeu nommé (bas / central / haut), pas en dur",
        suivi="issue #4, H1",
        sources=(
            _s_interne("simulateur/moteur.py", "PIB nominal et base de recettes"),
            _s_interne("docs/METHODOLOGIE.md", "hypothèses et conventions"),
            _s_externe("Audit d'issue #4 (28/09/2026), contre-calcul du commit 7536de7", "2026",
                       "issue #4"),
        ),
    ),
    "modele_transmission_taux": Objection(
        cle="modele_transmission_taux",
        numero=12,
        famille="modele",
        titre="Transmission instantanée des taux à la charge de la dette",
        attaque_faible="« Vos chiffres ne sont pas réalistes. »",
        objection_forte=(
            "« Votre moteur applique la variation de taux à tout le stock de dette la même année, "
            "alors que le document de référence du dépôt cite la règle de sensibilité de l'Agence "
            "France Trésor : +100 points de base donnent +3,5 Md€ la première année, +7,2 la "
            "deuxième et +15,4 la cinquième, pour une maturité moyenne de 8,5 ans. Votre plan "
            "profite donc d'une détente des taux arrivée en année 5 comme si elle s'appliquait "
            "instantanément, soit environ 9,5 Md€ d'économie au lieu de 3. »"
        ),
        concession=(
            "La transmission doit être amortie selon le profil de refinancement, sinon l'économie "
            "d'intérêts est surestimée d'un facteur trois la dernière année. C'est un défaut de "
            "calibrage, pas d'intention."
        ),
        maintien=(
            "Le mécanisme de la prime de risque et de la charge d'intérêts reste correctement "
            "orienté et borné ; c'est le calendrier qui est trop rapide. Un profil amorti rend le "
            "plan moins spectaculaire en année 5 et plus crédible sur dix ans — c'est même un "
            "argument de campagne : la dette se refinance sur huit ans et demi, et un plan "
            "quinquennal est jugé sur sa trajectoire, pas sur sa dernière année."
        ),
        falsification=(
            "Si l'on observait sur données AFT réelles une transmission plus rapide que le profil "
            "de maturité (par exemple via des émissions à taux variable ou indexées), le calendrier "
            "serait repris dans ce sens ; le document de référence du dépôt est la référence, il "
            "n'est pas mis de côté pour sauver un chiffre."
        ),
        statut="partiellement_concedee",
        changements="profil de transmission à caler sur la maturité moyenne (8,5 ans) en option",
        suivi="issue #4, H2",
        sources=(
            _s_interne("simulateur/moteur.py", "charge de la dette"),
            _s_interne("docs/PLAN_DU_SIMULATEUR_ET_AUDIT_INSTANT_T.md",
                       "§ II.2 — sensibilité AFT"),
            _s_externe("Audit d'issue #4 (28/09/2026) : +100 pb → +3,5 / +7,2 / +15,4 Md€", "2026",
                       "issue #4"),
        ),
    ),
    "modele_confiance_democratique": Objection(
        cle="modele_confiance_democratique",
        numero=13,
        famille="modele",
        titre="Confiance démocratique : +45 points en un an, sans source",
        attaque_faible="« Vos indicateurs sont des inventions. »",
        objection_forte=(
            "« Votre indice de confiance part de 27,5 et atteint 77,5 dès l'année 2, par des bonus "
            "fixes attribués mesure par mesure (RIC +14, B2 +10, vote blanc +8, pantouflage +7, "
            "régimes spéciaux +6, non-cumul +5). Aucun de ces coefficients n'est sourcé, une "
            "confiance qui monte de 45 points en douze mois n'a aucun précédent, et votre modèle "
            "ne la fait jamais redescendre — même dans la branche austérité, où la tension "
            "sociale atteint 97 sur 100. »"
        ),
        concession=(
            "L'indicateur doit être calibré sur une mesure existante et datée — le baromètre de la "
            "confiance politique du CEVIPOF — avec une montée progressive et un retour à la "
            "moyenne. Une confiance qui ne redescend pas n'est pas un indicateur, c'est une "
            "décoration."
        ),
        maintien=(
            "L'intention est bonne : relier les réformes institutionnelles à un effet mesurable "
            "plutôt qu'à un commentaire. Et la direction de l'effet n'est pas sérieusement "
            "contestable — les réformes de transparence et de participation sont celles qui se "
            "traduisent le plus vite dans les enquêtes. Ce qui manque est l'ampleur et le rythme."
        ),
        falsification=(
            "Si, après deux ans, l'indicateur réel du CEVIPOF ne bougeait pas dans le sens prévu "
            "par le modèle, les coefficients seraient révisés : le baromètre est public, la "
            "comparaison sera possible, et c'est précisément pour cela qu'il faut le nommer."
        ),
        statut="en_cours",
        changements="calibrage sur un baromètre public, montée progressive, retour à la moyenne",
        suivi="issue #4",
        sources=(
            _s_interne("simulateur/moteur.py", "confiance démocratique, bonus par mesure"),
            _s_interne("docs/METHODOLOGIE.md", "conventions et limites"),
            _s_externe("Baromètre de la confiance politique (CEVIPOF) — mesure de référence à "
                       "adopter", "annuel", "issue #4"),
        ),
    ),
    "modele_tension_plancher": Objection(
        cle="modele_tension_plancher",
        numero=14,
        famille="modele",
        titre="Tension sociale : un plancher de 5 sur 100 pendant quatre ans",
        attaque_faible="« Vos courbes sont trop lisses pour être vraies. »",
        objection_forte=(
            "« Votre tension sociale tombe à 5 sur 100 dès l'année 2 et y reste quatre ans : "
            "aucune société ne vit quatre années d'apaisement parfait après une décennie de "
            "conflits sociaux, de gilets jaunes et de réforme des retraites. Le plancher devrait "
            "être plus haut, avec des chocs et des effets décroissants. »"
        ),
        concession=(
            "Le plancher est invraisemblablement bas : il doit remonter de l'ordre de 15 à 20, "
            "avec des chocs possibles et une décrue progressive des effets d'une mesure. Un "
            "modèle où la tension ne peut pas remonter après un choc décrit un pays pacifié par "
            "hypothèse, pas une société réelle."
        ),
        maintien=(
            "Le sens de l'effet est défendable : lever une injustice fiscale et rendre du pouvoir "
            "d'achat fait baisser la tension, et le modèle sert à comparer des politiques entre "
            "elles. Un plancher plus haut ne change pas le classement ; il change la crédibilité "
            "de la courbe, et c'est déjà beaucoup."
        ),
        falsification=(
            "Si un plancher à 15 inversait le classement entre le plan et le statu quo sur la "
            "tension, c'est que l'effet des mesures était surestimé, et la revue porterait sur "
            "les coefficients de baisse, pas sur le plancher."
        ),
        statut="en_cours",
        changements="plancher à relever et effets à rendre décroissants",
        suivi="issue #4",
        sources=(
            _s_interne("simulateur/moteur.py", "tension sociale locale"),
            _s_externe("Audit d'issue #4 (28/09/2026) : « quatre ans à 5/100 n'est pas "
                       "crédible »", "2026", "issue #4"),
        ),
    ),
    "modele_prime_de_risque": Objection(
        cle="modele_prime_de_risque",
        numero=15,
        famille="modele",
        titre="Prime de risque politique modifiée seulement au-dessus de 50 Md€ d'effort",
        attaque_faible="« Votre marché ne réagit pas à la politique. »",
        objection_forte=(
            "« Votre scénario d'austérité atteint 97 sur 100 de tension sociale et un spread reste "
            "inchangé à 87,2 points de base — parce que la prime de risque politique n'est "
            "modifiée que dans la branche où l'effort dépasse 50 Md€. Autrement dit, votre modèle "
            "contredit son propre récit : les marchés ne sanctionnent jamais un pays que vous "
            "décrivez au bord de la fronde. »"
        ),
        concession=(
            "La prime de risque doit dépendre de la tension et du risque de censure dans toutes "
            "les branches — c'est une erreur de cohérence interne, et c'est le genre de défaut "
            "qu'un économiste relève en dix minutes."
        ),
        maintien=(
            "L'économie du modèle garde son sens : c'est bien la crédibilité budgétaire qui "
            "commande le spread à long terme, et le plan améliore la trajectoire de dette. "
            "Corriger la fonction élargit le canal politique sans casser le canal budgétaire."
        ),
        falsification=(
            "Si, prime élargie, l'austérité cessait d'être la politique la plus coûteuse en "
            "spread, l'hypothèse selon laquelle les marchés sanctionnent la contestation serait "
            "à revoir — le contraire d'un problème : ce serait un résultat."
        ),
        statut="en_cours",
        changements="prime de risque à rendre dépendante de la tension partout",
        suivi="issue #4",
        sources=(
            _s_interne("simulateur/moteur.py", "branche effort ≥ 50 Md€"),
            _s_externe("Audit d'issue #4 (28/09/2026) : austérité à 97/100 de tension, spread "
                       "inchangé", "2026", "issue #4"),
        ),
    ),
    "modele_spread_en_derive": Objection(
        cle="modele_spread_en_derive",
        numero=16,
        famille="modele",
        titre="Spread en dérive selon le calendrier plutôt que selon la dette",
        attaque_faible="« Votre spread suit une pente arbitraire. »",
        objection_forte=(
            "« Votre spread suit une pente de 8 points de base par an indexée sur le numéro de "
            "l'année, pas sur le ratio de dette, ni sur le déficit, ni sur le risque perçu. Une "
            "convention de calendrier n'est pas un modèle financier : deux pays ayant la même "
            "dette mais des élections à des dates différentes n'ont pas des spreads différents. »"
        ),
        concession=(
            "La dérive doit être fonction du ratio de dette et du déficit, la pente devenant un "
            "effet de second ordre explicitement nommé comme hypothèse. En l'état, le spread est "
            "une horloge : il avance avec le calendrier, pas avec la situation du pays."
        ),
        maintien=(
            "Une prime de calendrier très faible peut se défendre (primes d'échéance électorale "
            "documentées dans la littérature), mais elle doit rester un résidu étiqueté, pas le "
            "moteur principal. Le fait que le dépôt indexe déjà le spread au solde primaire va "
            "dans le bon sens."
        ),
        falsification=(
            "Si, spread recalculé sur la dette seule, le scénario de référence produisait des "
            "écarts d'OAT de plus de 50 points de base par rapport aux niveaux observés en 2025, "
            "la fonction serait recalibrée sur les niveaux observés."
        ),
        statut="en_cours",
        changements="spread à adosser au ratio de dette et au déficit",
        suivi="issue #4",
        sources=(
            _s_interne("simulateur/moteur.py", "spread de référence 88 + 8 × année"),
            _s_externe("Audit d'issue #4 (28/09/2026)", "2026", "issue #4"),
        ),
    ),
    "modele_seuil_falaise": Objection(
        cle="modele_seuil_falaise",
        numero=17,
        famille="modele",
        titre="Effet de falaise au seuil de 50 Md€ d'effort",
        attaque_faible="« Votre modèle se joue à un dixième de milliard. »",
        objection_forte=(
            "« Franchir 50,1 Md€ d'effort structurel fait gagner une note et 40 points de base de "
            "spread, tandis que 49,9 Md€ n'ont aucun effet : votre résultats dépendent d'un seuil "
            "binaire, donc toute politique peut être “optimisée” en le frôlant du bon côté. Un "
            "modèle dont la réponse est une marche d'escalier n'est pas robuste. »"
        ),
        concession=(
            "La marche doit devenir une transition continue — sigmoïde ou interpolation — et le "
            "seuil rester affiché comme convention de lecture, non comme bascule. Un modèle dont "
            "un dixième de milliard change la note souveraine n'est pas exploitable en débat, et "
            "se fait démonter en une phrase."
        ),
        maintien=(
            "La marche existe parce qu'un seuil a une signification institutionnelle réelle : "
            "c'est le point où le plan cesse d'être un ajustement et devient un changement de "
            "trajectoire. La remplacer par une transition douce conserve l'idée sans le saut."
        ),
        falsification=(
            "Si la version continue déplaçait le classement des préréglages (par exemple si "
            "l'austérité devenait moins mauvaise que le plan à effort égal), la fonction serait "
            "revue — le classement est le résultat que nous affirmons."
        ),
        statut="en_cours",
        changements="seuil à lisser ; le catalogue affiche déjà l'effort requis",
        suivi="issue #4",
        sources=(
            _s_interne("simulateur/moteur.py", "seuil effort ≥ 50 Md€"),
            _s_interne("simulateur/seuils.py", "garde-fous et barème public"),
            _s_externe("Audit d'issue #4 (28/09/2026)", "2026", "issue #4"),
        ),
    ),
    "modele_inflation_non_transmise": Objection(
        cle="modele_inflation_non_transmise",
        numero=18,
        famille="modele",
        titre="L'inflation est calculée mais n'alimente ni le PIB nominal ni les recettes",
        attaque_faible="« Vous affichez une inflation décorative. »",
        objection_forte=(
            "« Votre moteur calcule un taux d'inflation, l'affiche, et ne le transmet ni au PIB "
            "nominal ni aux recettes : 2,1 % d'inflation plus une croissance réelle ne donnent pas "
            "1,9 % de croissance nominale. L'inflation est donc un ornement, alors que c'est elle "
            "qui décide si la dette se dévalue en euros courants. »"
        ),
        concession=(
            "Le nominal doit être égal au réel plus l'inflation, appliqué aux recettes et aux "
            "dépenses ; c'est une correction d'identité comptable, pas un choix doctrinal, et "
            "elle est vérifiable sur la comptabilité nationale avant d'être portée dans le "
            "modèle."
        ),
        maintien=(
            "Les trajectoires de ratio restent dans des ordres de grandeur plausibles, et la "
            "direction du biais est connue : la transmission de l'inflation aux recettes nominales "
            "améliore le dénominateur du ratio de dette. Rendre ce canal visible rend le modèle "
            "attaquable sur des faits, ce qui est préférable à un ornement."
        ),
        falsification=(
            "Si l'identité nominal = réel + inflation produisait des trajectoires de dette "
            "incompatibles avec les niveaux observés (par exemple une dette nominale qui baisse "
            "sans excédent primaire), les hypothèses d'inflation seraient révisées."
        ),
        statut="en_cours",
        changements="identité comptable à appliquer (nominal = réel + inflation)",
        suivi="issue #4",
        sources=(
            _s_interne("simulateur/moteur.py", "inflation globale"),
            _s_externe("Audit d'issue #4 (28/09/2026)", "2026", "issue #4"),
        ),
    ),
    "modele_austerite_homme_de_paille": Objection(
        cle="modele_austerite_homme_de_paille",
        numero=19,
        famille="modele",
        titre="La branche austérité ne réduit pas le déficit",
        attaque_faible="« Vous vous donnez un adversaire facile. »",
        objection_forte=(
            "« Votre scénario d'austérité maintient le déficit constant à 150,9 Md€ : une "
            "austérité qui ne réduit pas le déficit n'existe pas, et vous l'utilisez comme "
            "repoussoir. Aucun adversaire sérieux ne défend une politique de coupes qui ne coupe "
            "rien : vous gagnez contre une caricature que vous avez écrite. »"
        ),
        concession=(
            "Le scénario doit modéliser les coupes, puis leurs effets récessifs — c'est-à-dire un "
            "déficit qui baisse d'abord, une activité qui ralentit ensuite, et une dette qui ne "
            "s'améliore pas autant qu'annoncé. C'est plus honnête et plus difficile."
        ),
        maintien=(
            "Même corrigée, l'austérité reste perdante sur les indicateurs sociaux — tension, "
            "confiance, services de proximité — et c'est ce que le dépôt compare. Le débat n'est "
            "pas « couper ou ne pas couper », mais « couper quoi, et avec quel effet sur les "
            "gens »."
        ),
        falsification=(
            "Si une austérité modélisée correctement (coupes réelles, multiplicateur négatif) "
            "donnait un déficit final meilleur que le plan tout en dégradant la tension, le dépôt "
            "devrait le dire : le plan ne serait pas la seule politique efficace, il serait la "
            "meilleure sur les indicateurs humains."
        ),
        statut="en_cours",
        changements="scénario d'austérité à réécrire avec coupes et effets récessifs",
        suivi="issue #4",
        sources=(
            _s_interne("simulateur/scenarios.py", "get_scenario_austerite_brutale()"),
            _s_externe("Audit d'issue #4 (28/09/2026) : « une austérité qui ne réduit pas le "
                       "déficit est un homme de paille »", "2026", "issue #4"),
        ),
    ),
    "modele_tests_de_thèse": Objection(
        cle="modele_tests_de_thèse",
        numero=20,
        famille="modele",
        titre="Un test unitaire transforme la thèse du projet en invariante",
        attaque_faible="« Vos tests sont verts parce qu'ils testent vos conclusions. »",
        objection_forte=(
            "« Le test d'atterrissage de la mandature affirme un déficit inférieur à 3 %, un "
            "spread sous 55 points de base, un OAT sous 3,50 % et une note AA : ce ne sont pas "
            "des invariantes, c'est la thèse du projet recopiée en assertions. Corriger une "
            "hypothèse qui déplace le déficit de 2,84 % à 3,05 % ferait échouer la suite — ce qui "
            "pousse mécaniquement à ne pas corriger les hypothèses. Un dépôt qui dit vouloir être "
            "audité a construit un verrou contre son propre audit. »"
        ),
        concession=(
            "Les tests doivent être séparés : invariantes (identités comptables, bornes, "
            "déterminisme, neutralité du vecteur par défaut) d'un côté, objectifs politiques du "
            "plan nommés comme tels de l'autre, avec le jeu d'hypothèses utilisé. Tant que les "
            "deux sont mêlés, la correction des hypothèses est structurellement freinée."
        ),
        maintien=(
            "Les objectifs politiques restent légitimes : un plan de mandature a des cibles, et "
            "les tester évite les régressions silencieuses. Ce qui change est leur statut — "
            "objectif déclaré, avec la mention de l'hypothèse — et non leur présence."
        ),
        falsification=(
            "Si séparer les deux familles de tests ne changeait rien à la capacité de détecter "
            "une régression, la séparation serait cosmétique ; elle est donc accompagnée d'un test "
            "de neutralité (le vecteur par défaut ne déplace rien) qui, lui, est une vraie "
            "invariante."
        ),
        statut="en_cours",
        changements="séparation invariantes / objectifs à mener dans tests/",
        suivi="issue #9, § 4",
        sources=(
            _s_interne("tests/test_simulateur.py", "scénario d'atterrissage de la mandature"),
            _s_externe("Audit d'issue #9 (28/09/2026) : la thèse transformée en assertion", "2026",
                       "issue #9"),
        ),
    ),
    "modele_chambre_tiree_au_sort": Objection(
        cle="modele_chambre_tiree_au_sort",
        numero=21,
        famille="modele",
        titre="Chambre citoyenne tirée au sort : le levier existe, la doctrine manque",
        attaque_faible="« Des citoyens tirés au sort seront manipulés par les lobbies. »",
        objection_forte=(
            "« Le volet démocratique annonce un levier de chambre citoyenne, et le simulateur "
            "expose un curseur de membres tirés au sort — mais la section du dossier qui définit "
            "son pouvoir n'existe pas. Quatre modèles sont possibles (consultatif, mise à "
            "l'agenda, troisième chambre à veto suspensif, jury d'évaluation ex post) et ils n'ont "
            "pas les mêmes conséquences institutionnelles. Le retour d'expérience de la "
            "Convention citoyenne pour le climat l'a montré : le statut juridique des conclusions "
            "doit être fixé *avant* le tirage au sort, sinon la déception nourrit la défiance "
            "qu'on prétendait réduire. »"
        ),
        concession=(
            "Le dossier doit choisir explicitement un modèle et écrire le statut de ses "
            "conclusions, ou dire qu'il ne tranche pas encore. Un curseur sans doctrine est un "
            "trou, pas une avance."
        ),
        maintien=(
            "La chambre tirée au sort répond à un manque documenté : l'entre-soi des notables, et "
            "l'appareil du levier est déjà sensible au nombre de membres et au verrou "
            "constitutionnel de l'article 24. Le modèle « mise à l'agenda », avec précédent "
            "ostbelgien, a l'avantage d'obliger sans remplacer le suffrage universel."
        ),
        falsification=(
            "Si le Conseil constitutionnel jugeait qu'une troisième chambre à veto suspensif "
            "méconnaît le suffrage universel, le modèle serait abandonné au profit de la mise à "
            "l'agenda, et l'article 24 resterait dans le registre des verrous."
        ),
        statut="en_cours",
        changements="section doctrinale à écrire ; quatre modèles à comparer dans docs/20",
        suivi="issue #7, § 4",
        sources=(
            _s_interne("simulateur/parametres.py", "levier reglage_chambre_tiree_au_sort"),
            _s_interne("docs/01_DEMOCRATIE_INSTITUTIONS.md", "levier 8 — chambre citoyenne"),
            _s_externe("Conventions citoyennes françaises (climat 2019-2020, fin de vie "
                       "2022-2023) ; conseil citoyen d'Ostbelgien (2019)", "2019 à 2023",
                       "issue #7"),
        ),
    ),
    "modele_laboratoire_non_discriminant": Objection(
        cle="modele_laboratoire_non_discriminant",
        numero=22,
        famille="modele",
        titre="Le laboratoire montre que le seuil de 3 % ne discrimine pas",
        attaque_faible="« Vos simulations ne prouvent rien. »",
        objection_forte=(
            "« Votre propre laboratoire, 500 tirages et 2 500 simulations, conclut que les 500 "
            "trajectoires réformées passent sous 3 % de déficit — mais les 500 trajectoires "
            "témoins aussi. Le seuil sur lequel repose toute la communication du plan ne "
            "distingue donc pas les politiques testées dans le domaine exploré. Publier cela et "
            "continuer à dire “sous 3 % en cinq ans” est une contradiction. »"
        ),
        concession=(
            "Le seuil ne doit pas être présenté comme un résultat discriminant : ce qu'il faut "
            "afficher, c'est l'écart au témoin (de l'ordre de 0,73 point de PIB en moyenne dans le "
            "laboratoire), et la probabilité d'atterrissage calculée sur une fourchette "
            "d'hypothèses, pas sur un point estimé."
        ),
        maintien=(
            "L'écart au témoin, lui, est un résultat : il ne dépend pas du seuil, et il est mesuré "
            "sur 500 tirages avec des chocs aléatoires. C'est la seule affirmation que le "
            "laboratoire autorise, et elle suffit à justifier l'existence du plan."
        ),
        falsification=(
            "Si l'écart moyen au témoin devenait nul ou changeait de signe sous des hypothèses "
            "plausibles (transmission amortie des taux, recettes indexées), le laboratoire le "
            "dirait et le plan serait révisé — c'est exactement ce qu'un protocole falsifiable "
            "sert à produire."
        ),
        statut="refutee",
        changements="discours à recadrer sur l'écart au témoin, le seuil restant un objectif",
        suivi="docs/LABORATOIRE_RD.md",
        sources=(
            _s_interne("docs/LABORATOIRE_RD.md", "campagne de 500 tirages, graine 20261003"),
            _s_interne("simulateur/laboratoire.py", "protocole d'écart au témoin"),
        ),
    ),
    "modele_fiches_de_gage": Objection(
        cle="modele_fiches_de_gage",
        numero=23,
        famille="modele",
        titre="« Notifié » n'est pas « encaissé », et il n'existe pas de réserve de gage",
        attaque_faible="« Vos 60 Md€ sont une addition d'espérances. »",
        objection_forte=(
            "« Vos deux plus gros leviers de recettes sont des recettes de contrôle : un taux de "
            "transformation du notifié vers l'encaissé de 60 à 70 % et un délai de deux à quatre "
            "ans. Un équilibre annoncé à 60 = 60, sans réserve, suppose que les neuf leviers "
            "donnent tous leur rendement maximal la même année — c'est une probabilité faible "
            "présentée comme une certitude. »"
        ),
        concession=(
            "Chaque levier doit porter une fiche de gage : rendement retenu en fourchette, "
            "rendement constaté du dispositif existant, base légale à créer ou modifier, délai "
            "notifié → encaissé, objections connues. Et l'équilibre doit inclure une réserve de "
            "gage — de l'ordre de 10 Md€ identifiés mais non comptés — pour absorber la "
            "sous-exécution."
        ),
        maintien=(
            "L'équilibre à 60 Md€ n'est pas une promesse d'exécution : c'est un ordre de grandeur "
            "de marges récurrentes, et le dépôt le présente ainsi depuis l'origine. Écrire les "
            "fourchettes rend l'ensemble plus solide, pas plus faible : une réserve annoncée est "
            "un argument en débat."
        ),
        falsification=(
            "Si, fiche par fiche, la somme des rendements bas tombait sous 45 Md€, le plan ne "
            "tiendrait pas son équilibre affiché et devrait soit étaler l'atterrissage, soit "
            "chercher de nouvelles mesures — le registre des engagements dirait lequel."
        ),
        statut="en_cours",
        changements="fiches de gage et réserve à écrire levier par levier",
        suivi="issue #6",
        sources=(
            _s_interne("docs/02_RECETTES_ET_TRANSACTIONS.md", "matrices de leviers"),
            _s_externe("Audit d'issue #6 (28/09/2026) : transformation 60-70 %, délai 2-4 ans, "
                       "réserve de gage d'environ 10 Md€", "2026", "issue #6"),
        ),
    ),
    "modele_hypotheses_non_nommees": Objection(
        cle="modele_hypotheses_non_nommees",
        numero=24,
        famille="modele",
        titre="Les hypothèses du moteur ne sont pas un jeu nommé",
        attaque_faible="« Changez une hypothèse et tout s'effondre. »",
        objection_forte=(
            "« Un modèle dont les paramètres structurels sont écrits en dur ne peut pas être "
            "audité : le lecteur ne sait pas ce qui relève du fait, de la convention ou du choix "
            "politique. Tant que les hypothèses ne sont pas un objet nommé, avec une valeur basse, "
            "centrale et haute et une source pour chacune, vos résultats restent un point estimé "
            "présenté comme une trajectoire. »"
        ),
        concession=(
            "Il faut un jeu d'hypothèses nommé, lu par le moteur, avec bas / central / haut et "
            "source, et un tirage de type Monte-Carlo qui rende une fourchette et une probabilité "
            "d'atterrissage au lieu d'une valeur unique."
        ),
        maintien=(
            "Le moteur reste déterministe et reproductible à hypothèses fixées : c'est ce qui "
            "permet de comparer des politiques entre elles. Nommer les hypothèses ne rend pas le "
            "modèle flou, cela rend la comparaison interprétable."
        ),
        falsification=(
            "Si la fourchette obtenue était si large que le classement des politiques changeait "
            "d'un tirage à l'autre, le dépôt devrait le dire : c'est un résultat, et il vaudrait "
            "mieux que n'importe quelle certitude fabriquée."
        ),
        statut="ouverte",
        changements="",
        suivi="issue #4 — chantier hypotheses.py",
        sources=(
            _s_interne("docs/METHODOLOGIE.md", "hypothèses, équations, conventions d'arrondi"),
            _s_externe("Audit d'issue #4 (28/09/2026) : proposition d'un jeu d'hypothèses et d'un "
                       "Monte-Carlo à 1 000 tirages", "2026", "issue #4"),
        ),
    ),
})


# --------------------------------------------------------------------------------------
# Les contre-modèles : quatre thèses cohérentes, pas quatre épouvantails
# --------------------------------------------------------------------------------------

CONTRE_MODELES: dict[str, ContreModele] = {
    "techno_libertarien": ContreModele(
        cle="techno_libertarien",
        titre="État minimal, intelligence artificielle et revenu universel",
        porte_par="courant techno-libertarien (Stéphane Mallard et une partie de son réseau)",
        these=(
            "L'État est le problème : il produit de la dette, des règles et de la lenteur. "
            "L'intelligence artificielle permettrait de rendre le régalien moins coûteux, de "
            "remplacer une partie de la décision publique par des systèmes experts, et de financer "
            "un revenu universel par la valeur créée par les machines. Le modèle de référence est "
            "celui des places qui attirent le capital par la fiscalité légère."
        ),
        ce_que_le_simulateur_en_dit=(
            "Le catalogue ne contient pas ce modèle : le scénario le plus proche est "
            "« austérité », qui coupe et subit la fronde — insuffisant pour représenter une thèse "
            "qui promet, elle, une baisse de la dépense publique avec un revenu universel en face. "
            "Le dépôt l'assume : comparer sérieusement ce modèle suppose d'écrire un préréglage "
            "« État minimal + transfert universel », qui est un chantier, pas une réplique."
        ),
        concession=(
            "Sur le fond, le dépôt n'a pas de réponse définitive au coût de la lenteur "
            "administrative : c'est précisément l'objet du volet 3 (fusion des doublons, "
            "commande publique), et si ce volet échoue, l'argument techno-libertarien gagne du "
            "terrain."
        ),
        divergence=(
            "La légitimité : une décision prise par un système non élu n'est pas contestable par "
            "un citoyen, et une erreur algorithmique ne se corrige que par un autre algorithme. Le "
            "simulateur lui-même en donne la démonstration — ses résultats dépendent d'hypothèses "
            "discutables, et c'est pour cela qu'il les publie. La ligne que le dépôt propose est "
            "claire : l'IA pour contrôler des flux (fraude, aides), jamais pour décider d'un droit."
        ),
        ouverts=(
            "Un scénario « État minimal + revenu universel » reste à écrire pour que la "
            "comparaison soit chiffrée au lieu d'être rhétorique."
        ),
        scenarios=("austerite", "statut_quo"),
        presets=("austerite",),
    ),
    "mur_de_la_realite": ContreModele(
        cle="mur_de_la_realite",
        titre="Le mur de la réalité budgétaire et les barrières organisationnelles",
        porte_par="Olivier Babeau (mur de la réalité) et Michel Levy Provençal (adoption)",
        these=(
            "Les marges de manœuvre sont fictives : la dépense contrainte, la dette et les "
            "engagements passés laissent peu de place, et les gains annoncés par la technologie se "
            "heurtent à des délais d'organisation que personne ne finance. Un plan qui promet 60 "
            "Md€ en cinq ans ignore le temps long de l'administration."
        ),
        ce_que_le_simulateur_en_dit=(
            "Le laboratoire du dépôt donne partiellement raison à cette thèse : le seuil de 3 % de "
            "déficit ne discrimine pas les politiques testées, puisque les 500 trajectoires témoins "
            "le franchissent aussi. Ce qui reste robuste est l'écart au témoin, environ 0,73 point "
            "de PIB en moyenne. L'audit d'hypothèses ajoute sa propre correction : avec des "
            "recettes indexées sur le PIB et une transmission amortie des taux, l'atterrissage se "
            "décale vers 3,05 à 3,26 %."
        ),
        concession=(
            "Le calendrier est le point faible du dossier, et il est concédé : c'est la raison "
            "d'être des fiches de gage (rendement constaté, délai notifié → encaissé, base légale) "
            "et de la réserve de gage d'environ 10 Md€."
        ),
        divergence=(
            "Le mur n'est pas une muraille : les leviers de recouvrement, de niches et de doublons "
            "sont documentés par la Cour des comptes et le Sénat, et le dépôt ne table sur aucune "
            "croissance magique — le plan est un plan de marges, pas de croissance."
        ),
        ouverts=(
            "Un échéancier de déploiement par levier (cadrage, pilote, généralisation) reste à "
            "écrire dans les fiches de gage."
        ),
        scenarios=("statut_quo", "choc_mondial"),
        presets=("statut_quo", "choc_mondial"),
    ),
    "realisme_adoption": ContreModele(
        cle="realisme_adoption",
        titre="Les gains de l'IA viennent de la réorganisation du travail",
        porte_par="Carlos Diaz (réalisme d'adoption) et la littérature sur les gains de productivité",
        these=(
            "Un outil ne produit pas de gain : c'est la réorganisation du travail autour de l'outil "
            "qui le produit. Promettre des milliards d'économies sans dire quels agents changent "
            "de mission revient à promettre des économies fictives."
        ),
        ce_que_le_simulateur_en_dit=(
            "Le moteur chiffre des rendements, pas des transitions : il ne dit rien du nombre "
            "d'agents à former ni du délai d'apprentissage. Le préréglage « mandature » applique "
            "les profils de montée en charge, mais la montée en charge est une courbe, pas un plan "
            "de réaffectation."
        ),
        concession=(
            "« Fusion des doublons, zéro licenciement » doit devenir un plan de réaffectation "
            "chiffré : effectifs concernés, missions d'accueil, formation, calendrier. Tant que ce "
            "n'est pas écrit, la thèse est fondée."
        ),
        divergence=(
            "La contrainte n'est pas budgétaire mais organisationnelle, et le dépôt ne propose "
            "aucune suppression de poste : le non-remplacement sur les fonctions de siège laisse le "
            "temps de la réaffectation. Le coût de la transition doit être budgété, pas nié."
        ),
        ouverts=(
            "Chiffrer le coût de la réaffectation (formation, accompagnement) et le soustraire du "
            "gain affiché, plutôt que de le laisser implicite."
        ),
        scenarios=("mandature", "double_mandature"),
        presets=("mandature", "double_mandature"),
    ),
    "orthodoxie_budgetaire": ContreModele(
        cle="orthodoxie_budgetaire",
        titre="L'ajustement budgétaire orthodoxe, sans réforme institutionnelle",
        porte_par="courant de la consolidation budgétaire",
        these=(
            "Seule compte la trajectoire de dette : il faut couper la dépense, réformer les "
            "retraites, conditionner les prestations, et éviter tout ce qui ressemble à une "
            "promesse de baisse d'impôt non financée. Les réformes institutionnelles sont un luxe "
            "qui retarde l'ajustement."
        ),
        ce_que_le_simulateur_en_dit=(
            "Les scénarios « austérité » et « statut quo » encadrent cette thèse. Le statu quo "
            "dégrade ; l'austérité dégrade la tension sociale et la qualité des services de "
            "proximité, avec un spread qui ne s'améliore pas dans la version actuelle du moteur — "
            "défaut de modélisation reconnu (objection sur la prime de risque), ce qui affaiblit "
            "provisoirement la comparaison dans les deux sens."
        ),
        concession=(
            "Le dépôt partage le constat : la dette est le principal facteur de vulnérabilité, et "
            "un plan qui l'ignorerait serait un mauvais plan. Les 51 Md€ de désendettement net "
            "sont la réponse à cette objection."
        ),
        divergence=(
            "L'ajustement par la seule dépense bute sur deux limites que le modèle donne : la "
            "tension sociale produit un coût politique et financier (prime de risque), et certaines "
            "coupes augmentent la dépense ailleurs (santé, précarité, sécurité). Le dépôt préfère "
            "chercher la marge dans le recouvrement et les niches plutôt que dans les prestations."
        ),
        ouverts=(
            "Un préréglage « consolidation orthodoxe » chiffré manque : le scénario d'austérité "
            "actuel est trop grossier pour trancher le débat."
        ),
        scenarios=("statut_quo", "austerite"),
        presets=("statut_quo", "austerite"),
    ),
}


def portee_du_levier(cle: str) -> float | None:
    """La portée maximale d'un levier, en Md€ par an, déduite du catalogue.

    Un levier ne porte un montant que si le champ qu'il pilote est libellé en Md€
    (``_mde``) : un interrupteur institutionnel comme le casier judiciaire ou le RIC
    n'a pas de portée monétaire, et le module refuse d'en inventer une. Pour un
    curseur, la portée est son maximum ; pour un interrupteur monétaire, c'est son
    facteur ; pour un curseur en pourcentage, c'est le maximum multiplié par le
    facteur (les niches fiscales, par exemple : 100 % de 90 Md€ ne font pas 90 Md€).
    """
    levier = LEVIERS[cle]
    if not (levier.champ or "").endswith("_mde"):
        return None
    reference = levier.maximum if levier.maximum is not None else 1.0
    return round(reference * levier.facteur, 2)


def objections(famille: str | None = None) -> list[Objection]:
    """Les objections du registre, filtrées par famille et triées par numéro."""
    lignes = [o for o in OBJECTIONS.values() if famille is None or o.famille == famille]
    return sorted(lignes, key=lambda o: o.numero)


def filtrer(
    famille: str | None = None,
    statut: str | None = None,
    levier: str | None = None,
    chercher: str | None = None,
) -> list[Objection]:
    """Filtre le registre comme le fait l'API : famille, statut, levier, texte libre."""
    lignes = objections(famille)
    if statut:
        lignes = [o for o in lignes if o.statut == statut]
    if levier:
        lignes = [o for o in lignes if o.levier == levier]
    if chercher:
        aiguille = chercher.strip().lower()
        lignes = [o for o in lignes if aiguille in
                  " ".join((o.titre, o.objection_forte, o.concession, o.maintien,
                            o.falsification)).lower()]
    return lignes


def coherence() -> dict[str, list[str]]:
    """Les garde-fous du registre, sous forme de listes : vides = tout va bien.

    Le contrat est le même que celui de `coherence_nuances()` : une anomalie n'est pas
    signalée par une exception, mais par une liste que les tests et la page exigent vide.
    """
    manquants: list[str] = []
    trop_courts: list[str] = []
    sources_vides: list[str] = []
    statuts_inconnus: list[str] = []
    changements_manquants: list[str] = []
    leviers_inconnus: list[str] = []
    numeros_doubles: list[str] = []
    fiches_inconnues: list[str] = []
    sans_origine: list[str] = []

    numeros: dict[int, str] = {}
    fiches: dict[int, str] = {}
    for cle, o in OBJECTIONS.items():
        if o.numero in numeros:
            numeros_doubles.append(f"{cle} et {numeros[o.numero]} portent le numéro {o.numero}")
        numeros[o.numero] = cle
        if o.famille not in FAMILLES:
            manquants.append(f"{cle} : famille inconnue {o.famille}")
        for piece, minimum in PROFONDEURS_MINIMALES.items():
            texte = getattr(o, piece)
            if len(texte) < minimum:
                trop_courts.append(f"{cle}.{piece} : {len(texte)} caractères < {minimum}")
        if not o.sources:
            sources_vides.append(cle)
        if o.statut not in STATUTS:
            statuts_inconnus.append(f"{cle} : {o.statut}")
        if o.statut in {"concedee", "partiellement_concedee"} and not o.changements:
            changements_manquants.append(f"{cle} : statut concédé sans changement écrit")
        if o.levier:
            if o.levier not in LEVIERS:
                leviers_inconnus.append(f"{cle} : {o.levier}")
            if not o.attaque_faible:
                manquants.append(f"{cle} : mesure sans attaque faible conservée")
        if o.famille == "mesure":
            if not o.fiche:
                fiches_inconnues.append(f"{cle} : objection de mesure sans fiche")
            if o.fiche in fiches:
                fiches_inconnues.append(
                    f"fiche {o.fiche} revendiquée par {cle} et {fiches[o.fiche]}")
            fiches[o.fiche] = cle
        for source in o.sources:
            if source.nature not in {"interne", "externe"}:
                manquants.append(f"{cle} : nature de source inconnue {source.nature}")
            if not source.reference.strip():
                sources_vides.append(f"{cle} : source sans référence")
            if source.nature == "externe" and not source.date:
                sources_vides.append(f"{cle} : source externe sans date ({source.reference})")
            if source.nature == "externe" and not source.origine:
                sans_origine.append(f"{cle} : {source.reference}")

    gages_sans_portee: list[str] = []
    gages_au_dessus_de_la_portee: list[str] = []
    for cle, o in OBJECTIONS.items():
        if o.gage_mde_an is None:
            continue
        portee = portee_du_levier(o.levier) if o.levier else None
        if portee is None:
            gages_sans_portee.append(f"{cle} : gage de {o.gage_mde_an} Md€ sans portée de levier")
            continue
        if abs(o.gage_mde_an) > abs(portee) + 1e-9:
            gages_au_dessus_de_la_portee.append(
                f"{cle} : gage {o.gage_mde_an} Md€ > portée {portee} Md€ du levier {o.levier}")

    modeles_incomplets = [c for c, m in CONTRE_MODELES.items()
                          if len(m.these) < 200 or len(m.ce_que_le_simulateur_en_dit) < 200
                          or len(m.concession) < 150 or len(m.divergence) < 150]
    return {
        "objections_incompletes": trop_courts,
        "sources_manquantes": sources_vides,
        "sources_externes_sans_origine": sans_origine,
        "statuts_inconnus": statuts_inconnus,
        "changements_manquants": changements_manquants,
        "leviers_inconnus": leviers_inconnus,
        "numeros_doubles": numeros_doubles,
        "fiches_inconnues": fiches_inconnues,
        "gages_sans_portee": gages_sans_portee,
        "gages_au_dessus_de_la_portee": gages_au_dessus_de_la_portee,
        "contre_modeles_incomplets": modeles_incomplets,
        "sans_concession": [cle for cle, o in OBJECTIONS.items() if not o.concession.strip()],
    }


def ligne_pour_api(o: Objection) -> dict:
    """La forme servie par `GET /api/objections` pour une objection."""
    portee = portee_du_levier(o.levier) if o.levier else None
    marge = None
    if portee is not None and o.gage_mde_an is not None:
        marge = round(abs(portee) - abs(o.gage_mde_an), 2)
    return {
        "cle": o.cle,
        "numero": o.numero,
        "famille": o.famille,
        "fiche": o.fiche,
        "titre": o.titre,
        "levier": o.levier,
        "levier_libelle": LEVIERS[o.levier].libelle if o.levier else "",
        "portee_mde": portee,
        "gage_mde_an": o.gage_mde_an,
        "marge_de_portee_mde": marge,
        "attaque_faible": o.attaque_faible,
        "objection_forte": o.objection_forte,
        "concession": o.concession,
        "maintien": o.maintien,
        "falsification": o.falsification,
        "statut": o.statut,
        "statut_libelle": o.statut_libelle,
        "changements": o.changements,
        "suivi": o.suivi,
        "sources": [
            {"nature": source.nature, "reference": source.reference, "chemin": source.chemin,
             "date": source.date, "origine": source.origine}
            for source in o.sources
        ],
    }


def synthese_pour_api() -> dict:
    """Ce que `GET /api/objections` renvoie : le registre, les comptes et les garde-fous."""
    lignes = []
    for o in objections():
        lignes.append(ligne_pour_api(o))
    comptes = {statut: sum(1 for o in OBJECTIONS.values() if o.statut == statut) for statut in STATUTS}
    return {
        "objections": lignes,
        "contre_modeles": [
            {
                "cle": m.cle, "titre": m.titre, "porte_par": m.porte_par, "these": m.these,
                "ce_que_le_simulateur_en_dit": m.ce_que_le_simulateur_en_dit,
                "concession": m.concession, "divergence": m.divergence, "ouverts": m.ouverts,
                "scenarios": list(m.scenarios), "presets": list(m.presets),
            }
            for m in CONTRE_MODELES.values()
        ],
        "comptes": {
            "total": len(OBJECTIONS),
            "par_famille": {f: sum(1 for o in OBJECTIONS.values() if o.famille == f) for f in FAMILLES},
            "par_statut": comptes,
            "contre_modeles": len(CONTRE_MODELES),
        },
        "statuts": STATUTS,
        "familles": FAMILLES,
        "portees": {
            "par_levier": {cle: portee_du_levier(cle) for cle in LEVIERS
                           if portee_du_levier(cle) is not None
                           and any(o.levier == cle and o.gage_mde_an is not None
                                   for o in OBJECTIONS.values())},
            "marge_totale_mde": round(sum(
                abs(portee_du_levier(o.levier) or 0) - abs(o.gage_mde_an or 0)
                for o in OBJECTIONS.values() if o.gage_mde_an is not None), 2),
            "lecture": "La portée est le maximum du levier ; le gage est la cible du dossier. "
                       "L'écart est une réserve de gage disponible, pas un rendement attendu.",
        },
        "limites": [
            "Une objection « réfutée » signifie que la réponse tient sous sa forme forte, pas que "
            "la critique était de mauvaise foi.",
            "Les concessions engagent : elles indiquent ce que le dépôt admet, et le changement "
            "attendu est écrit.",
            "Les sources externes sont celles déjà citées par le dépôt ou par ses audits ; elles "
            "ne remplacent pas une vérification à jour.",
        ],
        "garde_fous": {cle: valeurs for cle, valeurs in coherence().items() if valeurs},
    }
