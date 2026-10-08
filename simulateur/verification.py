"""
simulateur/verification.py — Statut de vérification de chaque donnée affichée.

Principe : aucune valeur n'est présentée comme vérifiée tant qu'une source
officielle n'a pas été consultée et datée. Chaque levier et chaque article du
registre juridique porte donc un **statut**, une **date de consultation**, un
**lien** et une **note** qui dit précisément ce qui est vérifié et ce qui ne
l'est pas.

Statuts :

- ``verifie``       : la valeur ou le texte a été contrôlé sur une source officielle.
- ``partiel``       : une partie seulement (le texte, la date ou le cadre) est vérifiée ;
                      le chiffre ou l'effet attaché ne l'est pas.
- ``date_decalee``  : la source est datée (année antérieure) ; le chiffre doit être actualisé.
- ``non_verifie``   : la source citée n'a pas été consultée, ou il s'agit d'une hypothèse interne.
- ``inaccessible``  : une consultation a été tentée et a échoué (source introuvable, payante, fermée).

La page publique qui détaille tous les statuts et explique comment contribuer
est générée par ``outils/generer-page-verification.py`` (``docs/VERIFICATION_DONNEES.md``).
Une donnée non vérifiée reste affichée : elle porte le statut, un renvoi vers la
page, et le simulateur propose au citoyen de noter sa propre valeur sourcée.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Date de l'audit de vérification (fuseau Europe/Paris).
DATE_AUDIT = "2026-10-08"

#: Page publique qui détaille les statuts et reçoit les contributions citoyennes.
PAGE_VERIFICATION = (
    "https://github.com/thejmimiia-code/D-mocratie-et-politique-du-peuple-pour-le-peuple-par-le-peuple"
    "/blob/main/docs/VERIFICATION_DONNEES.md"
)

#: Formulaire de signalement d'une donnée à vérifier (modèle d'issue GitHub).
FORMULAIRE_CONTRIBUTION = (
    "https://github.com/thejmimiia-code/D-mocratie-et-politique-du-peuple-pour-le-peuple-par-le-peuple"
    "/issues/new?template=donnee-a-verifier.md"
)

STATUTS: dict[str, str] = {
    "verifie": "Vérifié",
    "partiel": "Partiellement vérifié",
    "date_decalee": "Chiffre daté",
    "non_verifie": "Non vérifié",
    "inaccessible": "Source inaccessible",
}


@dataclass(frozen=True)
class Verification:
    statut: str
    verifie_le: str = ""
    source_url: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if self.statut not in STATUTS:
            raise ValueError(f"statut inconnu : {self.statut!r}")


NON_VERIFIE_DEFAUT = "Source citée non consultée à la date de l'audit : valeur à vérifier."
INTERNE_DOSSIER = "Chiffrage interne au dossier de mandature : hypothèse, non vérifiée."

#: Leviers dont au moins une partie a été contrôlée sur une source officielle ou
#: secondaire explicitement citée (voir `docs/PLAN_AUDIT_GLOBAL.md`, lots 2 et 3).
VERIFICATIONS_LEVIERS: dict[str, Verification] = {
    "tva_energie_5_5": Verification(
        "partiel", DATE_AUDIT,
        "https://bofip.impots.gouv.fr/bofip/14705-PGP.html/identifiant=BOI-RES-TVA-000209-20260826",
        "Suppression du taux réduit sur l'abonnement au 1er août 2025 : vérifiée sur le BOFiP "
        "(art. 20 de la loi n° 2025-127). Périmètre du levier (consommation ou abonnement) et "
        "coût de 9 Md€/an : non vérifiés.",
    ),
    "taxe_superprofits": Verification(
        "partiel", DATE_AUDIT,
        "https://eur-lex.europa.eu/eli/reg/2022/1854/oj?locale=fr",
        "Périmètre (pétrole, gaz, charbon, raffinage) et durée (exercices 2022 et/ou 2023) "
        "vérifiés sur le règlement, qui n'est plus en vigueur (application jusqu'au 31/12/2023). "
        "Champ modélisé (rachats d'actions) absent du règlement. Montant de 6 Md€/an : non vérifié.",
    ),
    "transports_publics": Verification(
        "partiel", DATE_AUDIT,
        "https://www.ecologie.gouv.fr/loi-dorientation-des-mobilites",
        "Cadre juridique (loi n° 2019-1428 du 24/12/2019, LOM) vérifié sur ecologie.gouv.fr et Légifrance. "
        "Montants du rapport Duron : non vérifiés.",
    ),
    "decentralisation": Verification(
        "partiel", DATE_AUDIT,
        "https://www.ecologie.gouv.fr/politiques-publiques/loi-3ds-relative-differenciation-decentralisation-deconcentration",
        "Cadre juridique (loi n° 2022-217 du 21/02/2022, 3DS) vérifié sur ecologie.gouv.fr et l'Assemblée nationale. "
        "Chiffres des rapports du comité d'évaluation : non vérifiés.",
    ),
    "extension_ttf": Verification(
        "partiel", DATE_AUDIT,
        "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000053543343",
        "Assiette actuelle (titres de capital, art. 235 ter ZD CGI) vérifiée sur Légifrance. "
        "Extension aux dérivés et +5 Md€/an : proposition non vérifiée.",
    ),
    "encadrement_loyers": Verification(
        "partiel", DATE_AUDIT,
        "https://www.legifrance.gouv.fr/eli/loi/2018/11/23/TERL1805474L/jo/article_140",
        "Mécanisme (loyers de référence, +20 %, -30 %) vérifié sur l'article 140 de la loi ELAN. "
        "Effets sur les loyers et l'offre : non vérifiés.",
    ),
    "renouvelables": Verification(
        "partiel", DATE_AUDIT,
        "https://www.pyrenees-orientales.gouv.fr/Actions-de-l-Etat/Environnement-eau-risques-naturels-et-technologiques/Energies-renouvelables/Planifier-les-energies-renouvelables/Loi-d-acceleration-pour-la-production-d-energies-renouvelables-Loi-APER/La-loi-APER",
        "Loi n° 2023-175 du 10 mars 2023 vérifiée. Ratio 1 Md€ ≈ 1 point de part renouvelable : "
        "non vérifié. RTE non consulté.",
    ),
    "budget_justice": Verification(
        "partiel", DATE_AUDIT,
        "https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000048430512",
        "Loi n° 2023-1059 du 20 novembre 2023 vérifiée. Part du PIB (0,35 %) et comparaison "
        "allemande (0,5 %) : non vérifiées (CEPEJ à consulter).",
    ),
    "reforme_anti_pantouflage": Verification(
        "partiel", DATE_AUDIT,
        "https://www.agence-francaise-anticorruption.gouv.fr/files/files/Guide_AFA_sport_operateurs_2022.pdf",
        "Pantouflage (article 432-13 du Code pénal, trois ans) vérifié. Registre public des "
        "représentants d'intérêts et transparence des rendez-vous : non vérifiés dans ce lot.",
    ),
    "ondam_variation": Verification(
        "verifie", DATE_AUDIT,
        "https://www.vidal.fr/actualites/37257-le-plfss-2026-definitivement-adopte.html",
        "ONDAM 2026 = 274,4 Md€ (+3,1 %), LFSS pour 2026 (Vidal, 18/12/2025 ; La Base Lextenso, "
        "31/12/2025). Conversion 1 point ≈ 2,7 Md€ calculée sur l'ONDAM 2025 de 265,9 Md€ (FIPECO).",
    ),
    # Chiffres dont la source est datée d'une année antérieure à 2026 (à actualiser).
    "tva_taux_normal": Verification(
        "date_decalee", DATE_AUDIT, "",
        "Source Insee « comptes nationaux 2024 » : chiffre de 2024, à actualiser. Non vérifié à ce stade.",
    ),
    "isf_retablissement": Verification(
        "date_decalee", DATE_AUDIT, "",
        "Ordre de grandeur IFI 2024 : chiffre daté, à actualiser. Non vérifié à ce stade.",
    ),
    "entretien_capital_public": Verification(
        "date_decalee", DATE_AUDIT, "",
        "Source Cour des comptes sur l'exécution budgétaire 2023 : chiffre daté. Non vérifié à ce stade.",
    ),
    "adaptation_climat": Verification(
        "date_decalee", DATE_AUDIT, "",
        "Rapport de la Cour des comptes de 2024 : chiffre daté. Non vérifié à ce stade.",
    ),
    "lutte_fraude_fiscale_ia": Verification(
        "date_decalee", DATE_AUDIT, "",
        "Cour des comptes 2024 et dossier de mandature : chiffre daté. Non vérifié à ce stade.",
    ),
}

#: Articles du registre dont le texte ou le numéro a été contrôlé (lots 1 à 3).
VERIFICATIONS_ARTICLES: dict[str, Verification] = {
    "CC_2017_752_DC": Verification(
        "verifie", DATE_AUDIT,
        "https://www.legifrance.gouv.fr/cons/id/CONSTEXT000035597362",
        "Décision du Conseil constitutionnel consultée sur Légifrance.",
    ),
    "OCDE_PILIER_2_CGI_223_VJ": Verification(
        "verifie", DATE_AUDIT,
        "https://www.impots.gouv.fr/professionnel/je-decouvre-limposition-minimale-mondiale",
        "Transposition de la directive (UE) 2022/2523 au CGI à partir de l'article 223 VJ "
        "(impots.gouv.fr, 16/02/2026 ; EUR-Lex).",
    ),
    "CART_L711_1": Verification(
        "verifie", DATE_AUDIT,
        "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000038610758",
        "Article L. 711-1 du Code de commerce consulté sur Légifrance : chambres de commerce et d'industrie.",
    ),
    "DIR_TVA_2022_542": Verification(
        "verifie", DATE_AUDIT,
        "https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:32022L0542",
        "Article 1er, point 22 de la directive 2022/542 consulté sur EUR-Lex.",
    ),
    "CGI_278_0_BIS_A": Verification(
        "verifie", DATE_AUDIT,
        "https://bofip.impots.gouv.fr/bofip/9417-PGP.html/identifiant=BOI-TVA-LIQ-30-20-95-20251022",
        "BOFiP BOI-TVA-LIQ-30-20-95, version du 22/10/2025 consultée.",
    ),
    "CGI_235_TER_ZD": Verification(
        "verifie", DATE_AUDIT,
        "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000053543343",
        "Taux de 0,4 % et seuil de capitalisation de 1 Md€ vérifiés sur Légifrance (version en vigueur "
        "au 01/01/2026, loi n° 2026-103 du 19/02/2026). Extension modélisée : proposition, non vérifiée.",
    ),
    "CGI_278_0_BIS_B": Verification(
        "verifie", DATE_AUDIT,
        "https://bofip.impots.gouv.fr/bofip/14705-PGP.html/identifiant=BOI-RES-TVA-000209-20260826",
        "Suppression du taux réduit de 5,5 % sur les abonnements (électricité ≤ 36 kVA et gaz) pour "
        "les périodes débutant à compter du 1er août 2025 : BOFiP BOI-RES-TVA-000209 (version du "
        "26/08/2026), citant l'article 20 de la loi n° 2025-127. Texte intégral non relu sur Légifrance.",
    ),
    "REG_UE_2022_1854_SOLIDARITE": Verification(
        "partiel", DATE_AUDIT,
        "https://eur-lex.europa.eu/eli/reg/2022/1854/oj?locale=fr",
        "Articles 15 à 18 consultés sur EUR-Lex (mention « No longer in force ») ; chapitre III "
        "applicable jusqu'au 31/12/2023 (clause finale ; rapport COM(2023) 768 du 30/11/2023).",
    ),
    "ELAN_ART_140": Verification(
        "verifie", DATE_AUDIT,
        "https://www.legifrance.gouv.fr/eli/loi/2018/11/23/TERL1805474L/jo/article_140",
        "Article 140 de la loi n° 2018-1021 consulté sur Légifrance.",
    ),
    "LOI_APER_2023_175": Verification(
        "partiel", DATE_AUDIT,
        "https://www.pyrenees-orientales.gouv.fr/Actions-de-l-Etat/Environnement-eau-risques-naturels-et-technologiques/Energies-renouvelables/Planifier-les-energies-renouvelables/Loi-d-acceleration-pour-la-production-d-energies-renouvelables-Loi-APER/La-loi-APER",
        "Numéro et date de la loi vérifiés (source secondaire officielle). Texte Légifrance à consulter.",
    ),
    "LOI_JUSTICE_2023_1059": Verification(
        "verifie", DATE_AUDIT,
        "https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000048430512",
        "Loi n° 2023-1059 consultée sur Légifrance.",
    ),
    "CP_432_13": Verification(
        "partiel", DATE_AUDIT,
        "https://www.agence-francaise-anticorruption.gouv.fr/files/files/Guide_AFA_sport_operateurs_2022.pdf",
        "Infraction et délai de trois ans confirmés par l'AFA (guide 2022) et l'ANSM (2020) ; "
        "texte officiel à consulter sur Légifrance.",
    ),
}


def _note_defaut(source: str) -> str:
    if "DOSSIER_DE_MANDATURE" in source:
        return INTERNE_DOSSIER
    return NON_VERIFIE_DEFAUT


def verification_levier(cle: str, source: str = "") -> Verification:
    """Statut d'un levier. Sans entrée explicite, la donnée est « non vérifiée »."""
    if cle in VERIFICATIONS_LEVIERS:
        return VERIFICATIONS_LEVIERS[cle]
    return Verification("non_verifie", "", "", _note_defaut(source))


def verification_article(identifiant: str) -> Verification:
    """Statut d'un article du registre juridique."""
    if identifiant in VERIFICATIONS_ARTICLES:
        return VERIFICATIONS_ARTICLES[identifiant]
    return Verification(
        "non_verifie", "", "",
        "Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit.",
    )


def en_dict(cle: str, source: str = "") -> dict[str, str]:
    """Forme sérialisable, consommée par l'interface et l'API."""
    v = verification_levier(cle, source)
    return {
        "statut": v.statut,
        "libelle": STATUTS[v.statut],
        "verifie_le": v.verifie_le,
        "source_url": v.source_url,
        "note": v.note,
        "page": f"{PAGE_VERIFICATION}#{cle}",
        "formulaire": FORMULAIRE_CONTRIBUTION,
    }
