"""Couche « nuances institutionnelles » : les réglages deviennent de la géométrie.

`simulateur/parametres.py` expose des curseurs, `constitution_analysee`,
`gouvernance_contrepouvoir` et `instances_et_dynamiques` décrivent le droit. Ce module
est le pont : il lit un vecteur de paramètres et **recalcule** les seuils, les délais,
la fenêtre législative utile, l'arithmétique des fentes et une famille d'indices
institutionnels. Aucune valeur n'est saisie à la main : tout part des modules de droit,
et un vecteur de réglages à zéro laisse toutes les sorties dans leur état d'origine.

Règles de lecture :
- un curseur à sa valeur par défaut = statu quo strict, donc indice à 50,0 ;
- un indice est une *amplitude relative*, pas une note de mérite : 50 + ce que le
  réglage rapporte − ce qu'il coûte, borné à [0, 100] ;
- une fente « neutralisée » par un réglage n'est pas réfutée, elle est *verrouillée* :
  le droit a été changé, la déduction ne produit plus d'effet utile ;
- aucun score ne vaut immunité, et aucun réglage ne rend une déduction irréfragable.
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple

from .gouvernance_contrepouvoir import ETAT_ASSEMBLEES, MECANISMES, VERROUS, seuil
from .instances_et_dynamiques import (
    FENETRE_RESIDUELLE_JOURS,
    FENTES,
    INSTANCES,
    STRATEGIES,
    TRAJETS,
    arithmetique_abstention_congres,
    oscillation,
    robustesse,
)
from .parametres import LEVIERS, valeurs_par_defaut
from .reglements_lois import REGISTRE_LEGAL

__all__ = [
    "NIVEAUX",
    "REPERTOIRES",
    "FENETRES_REGLABLES",
    "SEUILS_INSSENSIBLES",
    "VERROUS_HORS_REGLAGE",
    "croisements",
    "croisement_pour",
    "normalise_numero",
    "reglages_par_connaissance",
    "REGLAGES",
    "indices_nuances",
    "contexte_institutionnel",
    "seuils_ajustes",
    "delais_ajustes",
    "fentes_recalculees",
    "tableau_des_niveaux",
    "coherence_nuances",
    "nuances_pour_article",
    "nuances_pour_levier",
    "synthese_pour_api",
    "resume_console",
]

CONGRES_EFFECTIF = 925           # 577 députés + 346 sénateurs + 2 sièges pourvus en surnombre
HYPOTHESE_VOTANTS_CENSURE = 0.80  # part des membres qui prennent part au vote, pour l'assiette « exprimés »


# ────────────────────────────────────────────────────────────────────────────
# 1. Niveaux et registre des réglages
# ────────────────────────────────────────────────────────────────────────────

#: Étiquettes de niveau, dans l'ordre d'affichage.
NIVEAUX: Tuple[str, ...] = (
    "Constitutionnel",
    "Parlementaire",
    "Budgétaire",
    "Judiciaire",
    "Territorial",
    "Outre-mer",
    "Européen",
    "Participation",
    "Exception",
)

#: Préfixe commun des leviers gérés par cette couche.
PREFIXE = "reglage_"

#: Réglages pilotés par la couche, avec la règle appliquée et ses cibles.
#: `cibles` = (type de cible, identifiant dans le module de droit). Les identifiants
#: sont contrôlés par `coherence_nuances()` : une cible inexistante fait rougir les tests.
REGLAGES: Dict[str, Dict[str, Any]] = {
    # — Étage constitutionnel —
    "reglage_censure_assiette": {
        "niveau": "Constitutionnel",
        "regle": "assiette de la majorité (membres composant / suffrages exprimés / exprimés + quorum)",
        "effet": "le poids de l'abstention dans un renversement",
        "cibles": (("verrou", "censure_voix"), ("fente", "censure_par_membres"),
                   ("index", "capacite_de_renversement")),
    },
    "reglage_congres_quorum": {
        "niveau": "Constitutionnel",
        "regle": "quorum de votants ajouté au Congrès",
        "effet": "le nombre de voix réellement nécessaires pour réviser",
        "cibles": (("verrou", "congres_revision"), ("fente", "absence_de_quorum"),
                   ("index", "capacite_de_revision")),
    },
    "reglage_congres_assiette_membres": {
        "niveau": "Constitutionnel",
        "regle": "trois cinquièmes comptés sur les membres composant du Congrès",
        "effet": "l'avantage arithmétique de l'abstention au Congrès",
        "cibles": (("verrou", "congres_revision"), ("fente", "congres_par_exprimes"),
                   ("index", "capacite_de_revision")),
    },
    "reglage_controle_loi_referendaire": {
        "niveau": "Constitutionnel",
        "regle": "la loi référendaire devient contrôlable par le Conseil constitutionnel",
        "effet": "le trou de juridiction ouvert par la décision du 6 novembre 1962",
        "cibles": (("fente", "referendum_sans_juge"), ("trajet", "revision_referendum"),
                   ("index", "controle_juridictionnel")),
    },
    "reglage_49_3_interdiction": {
        "niveau": "Constitutionnel",
        "regle": "interdiction du 49.3 hors loi de finances",
        "effet": "le nombre de textes adoptables sans vote",
        "cibles": (("verrou", "49_3_plafond_texte"), ("index", "vitesse_legislative"),
                   ("index", "capacite_de_blocage_parlementaire")),
    },
    "reglage_delai_motion_49_3": {
        "niveau": "Parlementaire",
        "regle": "heures ajoutées au délai de dépôt de la motion de censure contre un 49.3",
        "effet": "le temps laissé à l'opposition pour réunir quinze vingtièmes des signatures",
        "cibles": (("verrou", "49_3_delai_motion"), ("index", "capacite_de_renversement")),
    },
    "reglage_delai_motion_censure": {
        "niveau": "Parlementaire",
        "regle": "jours ajoutés au délai avant le vote de la motion",
        "effet": "la fenêtre de négociation des abstentions",
        "cibles": (("verrou", "censure_delai"), ("index", "capacite_de_renversement")),
    },
    "reglage_seuil_saisine_conseil": {
        "niveau": "Judiciaire",
        "regle": "seuil de saisine a priori du Conseil constitutionnel",
        "effet": "la probabilité qu'un texte soit contrôlé avant de promulguer",
        "cibles": (("verrou", "saisine_conseil_signatures"), ("index", "controle_juridictionnel")),
    },
    "reglage_recours_irrecevabilite": {
        "niveau": "Parlementaire",
        "regle": "recours collectif ouvert contre une irrecevabilité prononcée par un président de séance",
        "effet": "le contrôle de la qualification au titre de l'article 40",
        "cibles": (("fente", "irrecevabilite_sans_recours"), ("index", "controle_juridictionnel")),
    },
    "reglage_droit_amendement": {
        "niveau": "Parlementaire",
        "regle": "droit d'amendement garanti, irrecevabilité bornée et motivée",
        "effet": "la capacité du Parlement à modifier un texte en navette",
        "cibles": (("verrou", "irrecevabilite_financiere"), ("fente", "amendement_etrang"),
                   ("index", "capacite_de_blocage_parlementaire")),
    },
    "reglage_ordre_du_jour_partage": {
        "niveau": "Parlementaire",
        "regle": "part de l'ordre du jour retirée au Gouvernement, en pourcentage de la session",
        "effet": "la fenêtre législative réellement disponible pour les textes du Gouvernement",
        "cibles": (("fenetre", "utile"), ("index", "vitesse_legislative")),
    },
    "reglage_seuil_groupes": {
        "niveau": "Parlementaire",
        "regle": "baisse du seuil de constitution des groupes",
        "effet": "le nombre de groupes disposant d'une niche et du droit d'enquête",
        "cibles": (("seuil_derive", "seuil_groupe_assemblee_nationale"),
                   ("index", "capacite_de_blocage_parlementaire")),
    },
    "reglage_vote_nominal_obligatoire": {
        "niveau": "Participation",
        "regle": "scrutin public nominal obligatoire, sans délégation de vote",
        "effet": "le coût politique de l'abstention et de la fossilisation du vote",
        "cibles": (("fente", "defossilisation_sans_vote"), ("index", "redevabilite")),
    },
    # — Étage budgétaire —
    "reglage_delai_budget_retraite": {
        "niveau": "Budgétaire",
        "regle": "jours retirés au délai de l'Assemblée nationale sur la loi de finances",
        "effet": "le temps d'examen des recettes avant que le budget ne passe par ordonnance",
        "cibles": (("etape", "budget:an_vote"), ("verrou", "budget_an_delai"),
                   ("verrou", "budget_delai_total"), ("index", "vitesse_legislative")),
    },
    "reglage_delai_senat_budget": {
        "niveau": "Budgétaire",
        "regle": "jours ajoutés au délai du Sénat sur la loi de finances",
        "effet": "la part du calendrier budgétaire où le Sénat peut encore amender",
        "cibles": (("etape", "budget:senat"), ("verrou", "budget_senat_delai"),
                   ("verrou", "budget_delai_total"), ("index", "capacite_de_blocage_parlementaire")),
    },
    "reglage_vote_par_programme": {
        "niveau": "Budgétaire",
        "regle": "vote par programme et fongibilité assumée",
        "effet": "la main-mise du Parlement sur l'allocation des crédits",
        "cibles": (("index", "capacite_de_blocage_parlementaire"), ("index", "redevabilite")),
    },
    "reglage_or_du_deficit": {
        "niveau": "Budgétaire",
        "regle": "marge de déficit structurel inscrite dans la Constitution",
        "effet": "la liberté du Parlement de décider de l'effort, contre la trajectoire",
        "cibles": (("index", "ancrage_des_reformes"), ("index", "capacite_de_blocage_parlementaire")),
    },
    "reglage_audit_obligatoire_prealable": {
        "niveau": "Budgétaire",
        "regle": "avis public d'une juridiction supérieure avant dépôt d'une réforme structurelle",
        "effet": "la qualité de l'information disponible pendant la navette",
        "cibles": (("etape", "projet_ordinaire:conseil_etat_avis"), ("index", "redevabilite")),
    },
    # — Étage judiciaire —
    "reglage_appel_qpc": {
        "niveau": "Judiciaire",
        "regle": "appel du filtre de non-renvoi d'une question prioritaire de constitutionnalité",
        "effet": "le nombre de droits effectivement justiciables devant le Conseil",
        "cibles": (("mecanisme", "qpc"), ("trajet", "controle_juge"),
                   ("index", "controle_juridictionnel")),
    },
    "reglage_parquet_independant": {
        "niveau": "Judiciaire",
        "regle": "parquet nommé sur avis conforme du Conseil supérieur de la magistrature",
        "effet": "la disponibilité de l'action publique pour poursuivre un exécutif",
        "cibles": (("index", "controle_juridictionnel"), ("index", "redevabilite")),
    },
    "reglage_mandat_unique_instances": {
        "niveau": "Judiciaire",
        "regle": "mandat unique non renouvelable pour les autorités indépendantes",
        "effet": "l'indépendance vis-à-vis du pouvoir qui nomme",
        "cibles": (("index", "controle_juridictionnel"), ("index", "redevabilite")),
    },
    "reglage_publication_avis_ce": {
        "niveau": "Judiciaire",
        "regle": "publication des avis du Conseil d'État sur les projets de loi",
        "effet": "la lecture publique des réserves du juge administratif avant le vote",
        "cibles": (("etape", "projet_ordinaire:conseil_etat_avis"), ("index", "redevabilite")),
    },
    "reglage_execution_cedh": {
        "niveau": "Judiciaire",
        "regle": "délai contraignant d'exécution des arrêts, assorti d'astreinte interne",
        "effet": "la vitesse à laquelle une condamnation internationale devient un droit interne",
        "cibles": (("fente", "priorite_du_droit_derive"), ("index", "controle_juridictionnel")),
    },
    "reglage_action_de_groupe_administratif": {
        "niveau": "Judiciaire",
        "regle": "action de groupe ouverte devant le juge administratif",
        "effet": "la possibilité d'attaquer une décision réglementaire en bloc",
        "cibles": (("fente", "toucher_la_loi_par_le_decret"), ("index", "controle_juridictionnel")),
    },
    # — Étage territorial et outre-mer —
    "reglage_petition_locale_seuil": {
        "niveau": "Territorial",
        "regle": "seuil national de pétition locale, en pourcentage des inscrits",
        "effet": "l'opposabilité du droit de pétition prévu à l'article 72-1",
        "cibles": (("verrou", "petition_locale"), ("fente", "petition_dans_le_reglement"),
                   ("index", "capacite_de_blocage_parlementaire")),
    },
    "reglage_referendum_local_automatique": {
        "niveau": "Territorial",
        "regle": "référendum local de plein droit au-delà du seuil",
        "effet": "le pouvoir de l'assemblée locale de refuser la consultation",
        "cibles": (("verrou", "referendum_local"), ("trajet", "compte_a_rebours_local"),
                   ("index", "capacite_de_blocage_parlementaire")),
    },
    "reglage_senat_suffrage_direct": {
        "niveau": "Parlementaire",
        "regle": "Sénat élu au suffrage universel direct",
        "effet": "la légitimité relative des deux chambres et le poids de leur veto",
        "cibles": (("seuil_derive", "asymetrie_des_chambres"),
                   ("index", "capacite_de_blocage_parlementaire")),
    },
    "reglage_autonomie_financiere_garantie": {
        "niveau": "Territorial",
        "regle": "plancher constitutionnel de dotation locale",
        "effet": "la résistance de l'investissement local au ciseau budgétaire",
        "cibles": (("index", "capacite_de_blocage_parlementaire"), ("index", "ancrage_des_reformes")),
    },
    "reglage_epci_suffrage_direct": {
        "niveau": "Territorial",
        "regle": "élection au suffrage direct des organes intercommunaux",
        "effet": "la chaîne de légitimité entre commune et intercommunalité",
        "cibles": (("index", "redevabilite"), ("index", "uniformite_du_droit")),
    },
    "reglage_differentiation_pilotes": {
        "niveau": "Territorial",
        "regle": "nombre de collectivités en régime d'expérimentation ou de dérogation",
        "effet": "l'écart entre le droit applicable d'un territoire à l'autre",
        "cibles": (("fente", "outre_mer_comme_laboratoire"), ("index", "uniformite_du_droit")),
    },
    "reglage_outre_mer_competences": {
        "niveau": "Outre-mer",
        "regle": "matières dont une collectivité d'outre-mer fixe elle-même la règle",
        "effet": "la part du territoire où l'abrogation nationale est impossible",
        "cibles": (("fente", "outre_mer_comme_laboratoire"), ("index", "uniformite_du_droit")),
    },
    "reglage_outre_mer_congres_permament": {
        "niveau": "Outre-mer",
        "regle": "instance d'outre-mer permanente dotée d'un droit d'inscription à l'ordre du jour",
        "effet": "la transformation d'une consultation en procédure",
        "cibles": (("index", "capacite_de_blocage_parlementaire"), ("index", "redevabilite")),
    },
    # — Étage européen —
    "reglage_subsidiarite_recours": {
        "niveau": "Européen",
        "regle": "recours de droit devant la CJUE sur avis motivé de subsidiarité",
        "effet": "la justiciabilité du contrôle de subsidiarité",
        "cibles": (("fente", "priorite_du_droit_derive"), ("index", "controle_juridictionnel")),
    },
    "reglage_vote_prealable_actes_ue": {
        "niveau": "Européen",
        "regle": "résolution préalable du Parlement avant d'engager la France en Conseil",
        "effet": "la vitesse de négociation européenne de l'exécutif",
        "cibles": (("index", "vitesse_legislative"), ("index", "redevabilite")),
    },
    "reglage_ancre_ue_reforms": {
        "niveau": "Européen",
        "regle": "part de la réforme écrite en droit dérivé de l'Union",
        "effet": "la résistance de la réforme à l'abrogation unilatérale",
        "cibles": (("fente", "priorite_du_droit_derive"), ("index", "ancrage_des_reformes")),
    },
    # — Étage participation et transparence —
    "reglage_registre_amendements": {
        "niveau": "Participation",
        "regle": "registre public nominatif des amendements et de leur sort",
        "effet": "la traçabilité de la fabrique du texte pendant la navette",
        "cibles": (("fente", "defossilisation_sans_vote"), ("index", "redevabilite")),
    },
    "reglage_comptes_temps_reel": {
        "niveau": "Participation",
        "regle": "comptes de campagne publiés pendant la campagne",
        "effet": "le délai entre le financement et sa connaissance par l'électeur",
        "cibles": (("index", "redevabilite"), ("index", "capacite_de_renversement")),
    },
    "reglage_chambre_tiree_au_sort": {
        "niveau": "Constitutionnel",
        "regle": "chambre supplémentaire tirée au sort, à veto suspensif",
        "effet": "le nombre d'étages où un texte peut être arrêté",
        "cibles": (("seuil_derive", "asymetrie_des_chambres"),
                   ("etape", "projet_ordinaire:nouvelle_lecture"),
                   ("index", "capacite_de_blocage_parlementaire")),
    },
    "reglage_convention_veto_suspensif": {
        "niveau": "Participation",
        "regle": "veto suspensif d'une convention citoyenne, avec seconde lecture obligatoire",
        "effet": "un battement de plus dans la navette, sans blocage définitif",
        "cibles": (("etape", "projet_ordinaire:nouvelle_lecture"),
                   ("index", "capacite_de_blocage_parlementaire")),
    },
    "reglage_revocation_elue": {
        "niveau": "Participation",
        "regle": "référendum révocatoire déclenché par pétition",
        "effet": "la fin de mandat possible avant son terme",
        "cibles": (("trajet", "initiative_citoyenne"), ("index", "capacite_de_renversement")),
    },
    "reglage_algorithmes_transparents": {
        "niveau": "Participation",
        "regle": "audit public des algorithmes à fort impact",
        "effet": "la vérifiabilité d'une décision individuelle automatisée",
        "cibles": (("fente", "toucher_la_loi_par_le_decret"), ("index", "controle_juridictionnel")),
    },
    # — Étage sécurité juridique et exception —
    "reglage_non_retroactivite_in_minus": {
        "niveau": "Exception",
        "regle": "interdiction constitutionnelle de rétroactivité in minus",
        "effet": "la résistance d'une règle à la loi nouvelle qui l'aggrave",
        "cibles": (("fente", "priorite_du_droit_derive"), ("index", "ancrage_des_reformes")),
    },
    "reglage_stabilite_normative_annees": {
        "niveau": "Exception",
        "regle": "années de stabilité garantie d'une règle structurante",
        "effet": "la liberté de la majorité suivante de revenir sur la règle",
        "cibles": (("fente", "priorite_du_droit_derive"), ("index", "ancrage_des_reformes"),
                   ("index", "vitesse_legislative")),
    },
    "reglage_verrou_par_loi_organique": {
        "niveau": "Constitutionnel",
        "regle": "réforme renvoyée au statut de loi organique",
        "effet": "l'étage de norme nécessaire pour abroger la réforme",
        "cibles": (("fente", "nouvelle_deliberation_presidentielle"), ("index", "ancrage_des_reformes")),
    },
    "reglage_verrou_par_revision": {
        "niveau": "Constitutionnel",
        "regle": "réforme inscrite dans la Constitution",
        "effet": "l'étage de norme nécessaire pour abroger la réforme",
        "cibles": (("trajet", "revision_congres"), ("fente", "congres_par_exprimes"),
                   ("index", "ancrage_des_reformes")),
    },
    "reglage_verrou_par_engagement_international": {
        "niveau": "Européen",
        "regle": "réforme adossée à un engagement international ou européen",
        "effet": "le juge compétent pour connaître d'un retour en arrière",
        "cibles": (("fente", "priorite_du_droit_derive"), ("index", "ancrage_des_reformes")),
    },
    "reglage_controle_juge_exception": {
        "niveau": "Exception",
        "regle": "contrôle juridictionnel intégral des mesures de police en régime d'exception",
        "effet": "la durée de vie d'une mesure prise sans discussion préalable",
        "cibles": (("verrou", "etat_urgence_delai_parlement"), ("index", "controle_juridictionnel")),
    },
    "reglage_plafond_etat_urgence": {
        "niveau": "Exception",
        "regle": "durée maximale totale d'un état d'urgence, sans nouvelle loi",
        "effet": "le caractère automatique de la fin du régime d'exception",
        "cibles": (("seuil_derive", "etat_urgence_duree_max_mois"), ("index", "controle_juridictionnel")),
    },
    "reglage_procedure_acceleree_encadree": {
        "niveau": "Parlementaire",
        "regle": "jours ajoutés au délai minimal avant délibération d'un texte engagé en procédure accélérée",
        "effet": "le temps réellement laissé au Sénat, aux amendements et à la publicité du texte",
        "cibles": (("verrou", "procedure_acceleree_delai"), ("index", "vitesse_legislative"), ("index", "capacite_de_blocage_parlementaire")),
    },
    "reglage_nouvelle_deliberation_supprimee": {
        "niveau": "Constitutionnel",
        "regle": "suppression du droit présidentiel de nouvelle délibération",
        "effet": "les quinze jours pendant lesquels une loi votée peut être renvoyée en discussion",
        "cibles": (("verrou", "promulgation_nouvelle_deliberation"), ("trajet", "projet_ordinaire"), ("index", "vitesse_legislative")),
    },
    "reglage_commission_enquete_droit_de_bloc": {
        "niveau": "Parlementaire",
        "regle": "une commission d'enquête garantie par groupe et par session, en plus de celle du droit en vigueur",
        "effet": "le nombre d'enquêtes parlementaires réellement constituables sans négociation",
        "cibles": (("verrou", "commission_enquete_signature"), ("mecanisme", "commission_enquete"), ("index", "capacite_de_blocage_parlementaire")),
    },
    "reglage_haute_cour_non_parlementaire": {
        "niveau": "Judiciaire",
        "regle": "Haute Cour composée de juges et non de parlementaires, sans majorité qualifiée dans les assemblées",
        "effet": "la majorité nécessaire pour réunir la Haute Cour et pour prononcer une destitution",
        "cibles": (("verrou", "haute_cour_assemblees"), ("verrou", "haute_cour_destitution"), ("mecanisme", "haute_cour"), ("mecanisme", "cjr"), ("index", "controle_juridictionnel")),
    },
    "reglage_cee_consultation_prealable": {
        "niveau": "Participation",
        "regle": "jours de consultation obligatoire du Conseil économique, social et environnemental avant le dépôt d'un texte de programmation",
        "effet": "le délai ajouté en amont et le poids de l'avis dans la discussion",
        "cibles": (("verrou", "lois_programmation_saisine_cee"), ("index", "redevabilite"), ("index", "vitesse_legislative")),
    },
    "reglage_defenseur_saisine_directe": {
        "niveau": "Judiciaire",
        "regle": "saisine directe du Défenseur des droits par tout justiciable, sans intermédiaire d'un parlementaire",
        "effet": "le nombre de réclamations instruites et de décisions correctives obtenues",
        "cibles": (("index", "controle_juridictionnel"), ("index", "redevabilite")),
    },
    "reglage_declassification_legislative": {
        "niveau": "Constitutionnel",
        "regle": "jours ajoutés au délai laissé au Conseil pour statuer sur une déclassification ou une irrecevabilité de compétence",
        "effet": "la vitesse à laquelle un domaine revient au règlement et le Parlement reprend la main",
        "cibles": (("verrou", "irrecevabilite_competence_delai"), ("index", "uniformite_du_droit"), ("index", "vitesse_legislative")),
    },
}


#: Contributions aux indices : coefficient appliqué au taux d'ouverture du réglage
#: (0 = statu quo, 1 = borne haute). Un coefficient négatif dit ce que le réglage coûte.
APPORTS: Dict[str, Dict[str, float]] = {
    "reglage_censure_assiette": {"capacite_de_renversement": 14.0, "stabilite": -9.0},
    "reglage_congres_quorum": {"capacite_de_revision": -11.0, "redevabilite": 4.0},
    "reglage_congres_assiette_membres": {"capacite_de_revision": -9.0, "redevabilite": 5.0},
    "reglage_controle_loi_referendaire": {"controle_juridictionnel": 13.0, "vitesse_legislative": -5.0},
    "reglage_49_3_interdiction": {"capacite_de_blocage_parlementaire": 14.0, "vitesse_legislative": -13.0},
    "reglage_delai_motion_49_3": {"capacite_de_renversement": 6.0, "vitesse_legislative": -3.0},
    "reglage_delai_motion_censure": {"capacite_de_renversement": -5.0, "vitesse_legislative": -2.0},
    "reglage_seuil_saisine_conseil": {"controle_juridictionnel": 12.0, "vitesse_legislative": -6.0},
    "reglage_recours_irrecevabilite": {"controle_juridictionnel": 8.0, "capacite_de_blocage_parlementaire": 6.0},
    "reglage_droit_amendement": {"capacite_de_blocage_parlementaire": 11.0, "vitesse_legislative": -7.0},
    "reglage_ordre_du_jour_partage": {"capacite_de_blocage_parlementaire": 12.0, "vitesse_legislative": -14.0},
    "reglage_seuil_groupes": {"capacite_de_blocage_parlementaire": 7.0, "uniformite_du_droit": -2.0},
    "reglage_vote_nominal_obligatoire": {"redevabilite": 11.0, "capacite_de_renversement": 4.0},
    "reglage_delai_budget_retraite": {"vitesse_legislative": 9.0, "capacite_de_blocage_parlementaire": -10.0},
    "reglage_delai_senat_budget": {"capacite_de_blocage_parlementaire": 7.0, "vitesse_legislative": -6.0},
    "reglage_vote_par_programme": {"capacite_de_blocage_parlementaire": 6.0, "redevabilite": 4.0},
    "reglage_or_du_deficit": {"ancrage_des_reformes": 12.0, "capacite_de_blocage_parlementaire": -9.0},
    "reglage_audit_obligatoire_prealable": {"redevabilite": 8.0, "vitesse_legislative": -4.0},
    "reglage_appel_qpc": {"controle_juridictionnel": 12.0, "vitesse_legislative": -3.0},
    "reglage_parquet_independant": {"controle_juridictionnel": 13.0, "redevabilite": 6.0},
    "reglage_mandat_unique_instances": {"controle_juridictionnel": 7.0, "redevabilite": 5.0},
    "reglage_publication_avis_ce": {"redevabilite": 9.0, "controle_juridictionnel": 4.0},
    "reglage_execution_cedh": {"controle_juridictionnel": 9.0, "ancrage_des_reformes": 4.0},
    "reglage_action_de_groupe_administratif": {"controle_juridictionnel": 8.0, "capacite_de_blocage_parlementaire": 4.0},
    "reglage_petition_locale_seuil": {"capacite_de_blocage_parlementaire": 6.0, "uniformite_du_droit": -3.0},
    "reglage_referendum_local_automatique": {"capacite_de_blocage_parlementaire": 9.0, "uniformite_du_droit": -5.0},
    "reglage_senat_suffrage_direct": {"capacite_de_blocage_parlementaire": 5.0, "uniformite_du_droit": 4.0},
    "reglage_autonomie_financiere_garantie": {"uniformite_du_droit": 7.0, "capacite_de_blocage_parlementaire": 5.0},
    "reglage_epci_suffrage_direct": {"redevabilite": 6.0, "uniformite_du_droit": 3.0},
    "reglage_differentiation_pilotes": {"uniformite_du_droit": -12.0, "capacite_de_blocage_parlementaire": 3.0},
    "reglage_outre_mer_competences": {"uniformite_du_droit": -10.0, "redevabilite": 4.0},
    "reglage_outre_mer_congres_permament": {"capacite_de_blocage_parlementaire": 5.0, "redevabilite": 4.0},
    "reglage_subsidiarite_recours": {"controle_juridictionnel": 7.0, "vitesse_legislative": -4.0},
    "reglage_vote_prealable_actes_ue": {"redevabilite": 6.0, "vitesse_legislative": -7.0},
    "reglage_ancre_ue_reforms": {"ancrage_des_reformes": 14.0, "uniformite_du_droit": 6.0},
    "reglage_registre_amendements": {"redevabilite": 13.0, "vitesse_legislative": -2.0},
    "reglage_comptes_temps_reel": {"redevabilite": 11.0},
    "reglage_chambre_tiree_au_sort": {"capacite_de_blocage_parlementaire": 12.0, "vitesse_legislative": -11.0},
    "reglage_convention_veto_suspensif": {"capacite_de_blocage_parlementaire": 7.0, "vitesse_legislative": -5.0},
    "reglage_revocation_elue": {"capacite_de_renversement": 15.0, "stabilite": -12.0},
    "reglage_algorithmes_transparents": {"controle_juridictionnel": 8.0, "redevabilite": 6.0},
    "reglage_non_retroactivite_in_minus": {"ancrage_des_reformes": 8.0, "controle_juridictionnel": 5.0},
    "reglage_stabilite_normative_annees": {"ancrage_des_reformes": 11.0, "vitesse_legislative": -4.0},
    "reglage_verrou_par_loi_organique": {"ancrage_des_reformes": 7.0, "vitesse_legislative": -3.0},
    "reglage_verrou_par_revision": {"ancrage_des_reformes": 15.0, "capacite_de_revision": -14.0},
    "reglage_verrou_par_engagement_international": {"ancrage_des_reformes": 12.0, "uniformite_du_droit": 5.0},
    "reglage_controle_juge_exception": {"controle_juridictionnel": 11.0, "capacite_de_renversement": 3.0},
    "reglage_plafond_etat_urgence": {"controle_juridictionnel": 8.0, "ancrage_des_reformes": 3.0},
    "reglage_procedure_acceleree_encadree": {"vitesse_legislative": -11.0, "capacite_de_blocage_parlementaire": 9.0},
    "reglage_nouvelle_deliberation_supprimee": {"vitesse_legislative": 7.0, "capacite_de_blocage_parlementaire": -6.0},
    "reglage_commission_enquete_droit_de_bloc": {"capacite_de_blocage_parlementaire": 13.0, "redevabilite": 8.0, "vitesse_legislative": -6.0},
    "reglage_haute_cour_non_parlementaire": {"controle_juridictionnel": 10.0, "capacite_de_blocage_parlementaire": -4.0},
    "reglage_cee_consultation_prealable": {"redevabilite": 8.0, "vitesse_legislative": -6.0},
    "reglage_defenseur_saisine_directe": {"controle_juridictionnel": 9.0, "redevabilite": 5.0},
    "reglage_declassification_legislative": {"uniformite_du_droit": 6.0, "vitesse_legislative": 4.0, "controle_juridictionnel": 3.0},
}

#: Verrous qu'un réglage bien réel laisse inchangés à son maximum, et pourquoi. Ce n'est
#: pas une tolérance : `coherence_nuances()` échoue dès qu'un de ces verrous se met à bouger,
#: pour que la mention soit réexaminée et non héritée.
SEUILS_INSSENSIBLES: Dict[str, str] = {
    "congres_revision": "à assemblée plnière, les trois cinquièmes de 925 donnent 555 : le "
                        "réglage ne déplace le nombre que si l'abstention déplace l'assemblée — "
                        "voir `scenarios_abstention` du même seuil",
    "etat_urgence_delai_parlement": "le délai de ratification de douze jours est constitutionnel : "
                                    "le contrôle du juge change, pas le calendrier",
}


#: Réglages qui ne déplacent aucun nombre : ils changent la nature d'un pouvoir ou d'une
#: obligation, pas un seuil. Une exception assumée et datée vaut mieux qu'un chiffre inventé ;
#: `coherence_nuances()` exige que cette liste recouvre exactement les réglages sans cible chiffrée.
CIBLES_CHIFFREES = ("verrou", "fente", "trajet", "etape", "seuil_derive", "mecanisme", "fenetre")

REGLAGES_SANS_GEOMETRIE: Dict[str, str] = {
    "reglage_defenseur_saisine_directe": "l'article 71-1 ne fixe aucun seuil : la saisine directe ouvre une porte, elle ne déplace pas un nombre — le réglage est porté par les indices de contrôle et de redevabilité",
    "reglage_autonomie_financiere_garantie":
        "un plancher de dotation est une masse budgétaire, portée par les lignes de recette locales, "
        "pas un seuil de procédure",
    "reglage_comptes_temps_reel":
        "la transparence des comptes n'a ni délai ni quota consigné au registre des verrous",
    "reglage_epci_suffrage_direct":
        "le mode de scrutin intercommunal ne déplace ni seuil ni délai : seuls les effectifs élus "
        "changeraient, et ils ne sont pas au registre",
    "reglage_mandat_unique_instances":
        "la durée et le renouvellement des mandats d'autorité indépendante ne sont pas chiffrés "
        "dans `VERROUS`",
    "reglage_or_du_deficit":
        "un plafond de déficit est une trajectoire budgétaire (`dette`, `budget`), pas une géométrie "
        "institutionnelle",
    "reglage_outre_mer_congres_permament":
        "instance consultative sans délai ni quota au registre : son droit d'inscription est une "
        "règle d'ordre du jour, déjà portée par `reglage_ordre_du_jour_partage`",
    "reglage_parquet_independant":
        "l'avis conforme du CSM change la nature de la nomination, pas un nombre : `nomination_veto` "
        "ne porte aucun seuil chiffré",
    "reglage_vote_par_programme":
        "la structure du vote (LOLF, art. 34) ne déplace aucun des verrous chiffrés du registre",
    "reglage_vote_prealable_actes_ue":
        "l'article 88-4 n'attache aucun délai à la résolution européenne : elle est obligatoire ou "
        "ne l'est pas",
}


def reglages_sans_cible_chiffree() -> List[str]:
    """Réglages dont aucune cible ne produit de nombre recalculé."""
    orphelins: List[str] = []
    for cle in reglages_catalogue():
        types = {type_cible for type_cible, _ in REGLAGES[cle].get("cibles", ())}
        if not types & set(CIBLES_CHIFFREES):
            orphelins.append(cle)
    return sorted(orphelins)


#: Part de résistance retirée à une fente par un réglage (1.0 = verrouillée).
NEUTRALISATIONS: Dict[str, Dict[str, float]] = {
    "censure_par_membres": {"reglage_censure_assiette": 1.0},
    "congres_par_exprimes": {"reglage_congres_assiette_membres": 1.0},
    "absence_de_quorum": {"reglage_congres_quorum": 0.5},
    "referendum_sans_juge": {"reglage_controle_loi_referendaire": 1.0},
    "irrecevabilite_sans_recours": {
        "reglage_recours_irrecevabilite": 1.0, "reglage_droit_amendement": 0.6,
    },
    "defossilisation_sans_vote": {
        "reglage_vote_nominal_obligatoire": 0.6, "reglage_registre_amendements": 0.4,
    },
    "petition_dans_le_reglement": {"reglage_petition_locale_seuil": 0.8,
                                   "reglage_referendum_local_automatique": 0.5},
    "amendement_etrang": {"reglage_droit_amendement": 0.7, "reglage_seuil_groupes": 0.3},
    "priorite_du_droit_derive": {
        "reglage_non_retroactivite_in_minus": 0.3, "reglage_stabilite_normative_annees": 0.4,
        "reglage_verrou_par_engagement_international": 0.3, "reglage_ancre_ue_reforms": 0.6,
    },
    "toucher_la_loi_par_le_decret": {
        "reglage_algorithmes_transparents": 0.4, "reglage_action_de_groupe_administratif": 0.3,
    },
    "outre_mer_comme_laboratoire": {
        "reglage_outre_mer_competences": 0.5, "reglage_differentiation_pilotes": 0.4,
    },
    "nouvelle_deliberation_presidentielle": {
        "reglage_verrou_par_loi_organique": 0.4, "reglage_verrou_par_revision": 0.5,
    },
}

#: Indices rendus par la couche, avec leur définition lisible.
INDICES: Dict[str, str] = {
    "capacite_de_blocage_parlementaire":
        "ce qui est nécessaire pour arrêter un texte : amendement, ordre du jour, niches, seconde chambre",
    "capacite_de_renversement":
        "ce qui est nécessaire pour renverser : signatures, assiette, délais laissés à l'opposition",
    "controle_juridictionnel":
        "ce qui peut être porté devant un juge : saisine, QPC, parquet, exécution des arrêts",
    "redevabilite":
        "ce que l'électeur peut vérifier de son représentant : votes nommés, comptes, avis, registres",
    "ancrage_des_reformes":
        "la difficulté de défaire une réforme : étage de norme, engagement, stabilité garantie",
    "vitesse_legislative":
        "les textes pouvant être menés à leur terme dans la fenêtre résiduelle, au calendrier réel",
    "uniformite_du_droit":
        "l'identité des règles appliquées sur tout le territoire : differentiation, outre-mer, ancrage européen",
    "capacite_de_revision":
        "la facilité de réviser la Constitution : Congrès, quorum, assiette, voie référendaire",
}


# ────────────────────────────────────────────────────────────────────────────
# 2. Lecture des réglages
# ────────────────────────────────────────────────────────────────────────────

def reglages_presents() -> List[str]:
    """Les leviers du catalogue que cette couche sait recalculer."""
    return sorted(cle for cle in LEVIERS if cle in REGLAGES)


def reglages_catalogue() -> List[str]:
    """Les leviers institutionnels déclarés dans le catalogue (préfixe `reglage_`)."""
    return sorted(cle for cle in LEVIERS if cle.startswith(PREFIXE))


def _bornes(cle: str) -> Tuple[float, float]:
    levier = LEVIERS.get(cle)
    return levier.bornes if levier else (0.0, 1.0)


def normaliser(parametres: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """Vecteur des seuls réglages institutionnels, écrêté à ses bornes."""
    source = dict(valeurs_par_defaut()) if parametres is None else dict(parametres)
    vecteur: Dict[str, float] = {}
    for cle in reglages_catalogue():
        brut = source.get(cle, LEVIERS[cle].defaut)
        try:
            valeur = float(brut)
        except (TypeError, ValueError):
            valeur = float(LEVIERS[cle].defaut)
        mini, maxi = _bornes(cle)
        vecteur[cle] = max(mini, min(maxi, valeur))
    return vecteur


def taux(cle: str, vecteur: Dict[str, float]) -> float:
    """Ouverture d'un réglage, de 0 (statu quo) à 1 (borne haute)."""
    levier = LEVIERS.get(cle)
    valeur = vecteur.get(cle, 0.0)
    if levier is not None and levier.modalites:
        valeurs = [valeur_modalite for _, valeur_modalite in levier.modalites]
        mini, maxi = min(valeurs), max(valeurs)
    else:
        mini, maxi = _bornes(cle)
    if maxi <= mini:
        return 0.0
    return max(0.0, min(1.0, (valeur - mini) / (maxi - mini)))


def niveau_de(cle: str) -> str:
    return REGLAGES.get(cle, {}).get("niveau", "Parlementaire")


# ────────────────────────────────────────────────────────────────────────────
# 3. Seuils recalculés
# ────────────────────────────────────────────────────────────────────────────

#: Unités lisibles, quand le verrou du registre ne porte que l'assiette ou un texte
#: (« seuil fixé par la loi » ne se suffit pas à lui-même).
UNITES_LISIBLES: Dict[str, str] = {
    "censure_voix": "voix",
    "congres_revision": "voix",
    "saisine_conseil_signatures": "signatures",
    "49_3_plafond_texte": "textes par session",
    "irrecevabilite_financiere": "statut de la qualification",
    "budget_delai_total": "jours",
    "petition_locale": "% des inscrits",
    "procedure_acceleree_delai": "jours",
    "promulgation_nouvelle_deliberation": "jours",
    "commission_enquete_signature": "commissions garanties par session",
    "haute_cour_assemblees": "voix par assemblée",
    "haute_cour_destitution": "voix",
    "lois_programmation_saisine_cee": "jours de consultation",
    "irrecevabilite_competence_delai": "jours",
    "referendum_local": "régime",
}

#: Verrous que cette couche sait ajuster, et nom lisible du calcul.
VERROUS_REGLAGES: Dict[str, str] = {
    "censure_voix": "majorité exigée pour renverser le Gouvernement",
    "censure_delai": "délai avant le vote de la motion de censure",
    "49_3_delai_motion": "délai de dépôt de la motion contre un 49.3",
    "49_3_plafond_texte": "nombre de textes pouvant être forcés par session",
    "saisine_conseil_signatures": "signatures pour saisir le Conseil constitutionnel",
    "budget_an_delai": "délai de l'Assemblée nationale sur la loi de finances",
    "budget_senat_delai": "délai du Sénat sur la loi de finances",
    "budget_delai_total": "calendrier budgétaire complet",
    "irrecevabilite_financiere": "base de l'irrecevabilité financière",
    "etat_urgence_delai_parlement": "délai de ratification de l'état d'urgence",
    "congres_revision": "majorité exigée au Congrès pour réviser la Constitution",
    "petition_locale": "seuil national de la pétition locale",
    "referendum_local": "déclenchement du référendum décisionnel local",
    "procedure_acceleree_delai": "jours de délai plancher avant délibération en procédure accélérée",
    "promulgation_nouvelle_deliberation": "exercice du droit de nouvelle délibération",
    "commission_enquete_signature": "commissions d'enquête garanties par groupe et par session",
    "haute_cour_assemblees": "composition de la Haute Cour",
    "haute_cour_destitution": "composition de la Haute Cour",
    "lois_programmation_saisine_cee": "jours de consultation préalable obligatoire du CESE",
    "irrecevabilite_competence_delai": "jours de délai de décision sur l'articulation loi-règlement",
}

#: Verrous que aucun réglage ne déplace, et pourquoi : un trou assumé est une décision,
#: un trou non dit est une omission. `coherence_nuances()` exige que la liste soit exhaustive.
VERROUS_HORS_REGLAGE: Dict[str, str] = {
    "censure_signatures": "le dixième des membres est une protection contre l'obstruction : "
                          "le faire varier ne peut pas se décréter par un curseur de politique publique",
    "censure_plafond_motions": "limitation du nombre de motions par session, touchée seulement par une "
                               "révision de l'article 51 — le simulateur la décrète hors jeu",
    "dissolution_carence": "le Président n'a aucune obligation de dissoudre après une censure : "
                           "aucun réglage du dépôt ne transforme une absence d'obligation en obligation",
    "referendum_promulgation": "le délai de promulgation après référendum n'est pas un seuil "
                               "politique : il n'existe pas de levier pour le négocier",
    "saisine_conseil_delai": "les trente jours du contrôle a priori sont un calendrier, pas un "
                             "arbitrage : seul le constituant y touche",
    "saisine_conseil_urgence": "le délai réduit en cas d'urgence est la contrepartie du délai normal",
    "plfss_delai_total": "calendrier social aligné sur celui des finances : le réglage est porté "
                         "par `reglage_delai_budget_retraite`, pas dupliqué",
    "session_extraordinaire_signatures": "un dixième des membres pour ouvrir une session "
                                         "extraordinaire : seuil de protection, jamais négocié",
    "session_cloture_delai": "la clôture relève du règlement, pas de la loi",
    "nomination_veto": "le veto du Président sur les nominations (art. 13) n'a pas d'équivalent "
                       "chiffré dans le modèle",
    "opex_delai_autorisation": "les quatre mois d'opérations extérieures : délai de information "
                               "du Parlement, non négociable politiquement",
    "etat_siege_delai_parlement": "l'état de siège ne peut pas être prorogé sans loi : règle "
                                  "absolue, aucun seuil à déplacer",
    "vacance_delai_scrutin": "les vingt à cinquante jours pour élire un nouveau Président : "
                             "calendrier, pas arbitrage",
    "grace_regime": "la grâce présidentielle n'a plus de contre-pouvoir chiffré depuis 2008",
    "presidentielle_parrainages": "les cinquante parrainages sont un filtre constitutionnel, pas "
                                  "une mesure de politique publique",
    "rip_signatures_electeurs": "le dixième des électeurs est déjà modulé par les preset "
                                "`reforme_ric` ; pas de double comptage",
    "rip_signatures_parlement": "un cinquième des membres plus dix départements : seuil du "
                                 "RIP, déjà piloté par `reforme_ric` côté moteur",
    "cmp_composition": "vingt-quatre membres de la CMP : chiffre du règlement, déjà au statu quo",
}


def _voix_censure(regle: Dict[str, float]) -> Dict[str, Any]:
    """Seuil de censure selon l'assiette retenue (calcul sur l'effectif légal)."""
    etat = ETAT_ASSEMBLEES["assemblee_nationale"]
    membres = int(etat["sieges"])
    assiette = int(regle.get("reglage_censure_assiette", 0.0))
    if assiette == 0:
        voix = int(seuil("censure_voix"))   # 289 : majorité des 577 membres composant
        return {
            "voix_requises": voix,
            "assiette": "membres composant l'Assemblée (effectif légal)",
            "formule": f"majorité des {membres} membres composant",
            "note": "l'abstention fait obstacle à la motion, elle ne la favorise jamais",
        }
    votants = int(math.floor(membres * HYPOTHESE_VOTANTS_CENSURE))
    voix = int(math.floor(votants / 2) + 1)
    resultat = {
        "voix_requises": voix,
        "assiette": "suffrages exprimés",
        "formule": f"majorité des {votants} votants (hypothèse : {HYPOTHESE_VOTANTS_CENSURE:.0%} de participation)",
        "note": "le seuil suit le nombre de votants : une abstention massive le fait baisser",
    }
    if assiette >= 2:
        quorum = int(math.ceil(membres * 0.6))
        resultat["quorum_votants"] = quorum
        resultat["note"] += (f" ; le quorum impose {quorum} votants, ce qui rend le seuil de {voix} voix "
                             "presque atteignable — le verrou se déplace de la majorité à la présence")
        resultat["assiette"] = "suffrages exprimés + quorum de présence"
    return resultat


def _congres(regle: Dict[str, float], votants: int = CONGRES_EFFECTIF) -> Dict[str, Any]:
    """Trois cinquièmes du Congrès, selon l'assiette retenue et le nombre de votants.

    Le calcul est fait pour plusieurs taux de participation parce que tout l'enjeu de
    l'assiette est là : sur les suffrages exprimés, bouder le vote fait baisser le seuil ;
    sur les membres composant, le seuil est le même à 925 comme à 617 votants.
    """
    sur_membres = regle.get("reglage_congres_assiette_membres", 0.0) >= 1.0
    seuil_sur_membres = int(math.ceil(CONGRES_EFFECTIF * 3 / 5))
    base = arithmetique_abstention_congres(votants)
    seuil_sur_exprimes = int(base["voix_requises"])
    voix = seuil_sur_membres if sur_membres else seuil_sur_exprimes
    notes: List[str] = []
    quorum_pct = float(regle.get("reglage_congres_quorum", 0.0))
    quorum = int(math.ceil(CONGRES_EFFECTIF * quorum_pct / 100.0)) if quorum_pct > 0 else 0
    if quorum:
        notes.append(f"quorum de {quorum} votants requis ({quorum_pct:.0f} % des {CONGRES_EFFECTIF} membres)")
        if quorum > voix:
            notes.append("le quorum dépasse le seuil de voix : c'est la présence qui décide, plus la majorité")
    scenarios: Dict[str, Dict[str, int]] = {}
    for participation in (925, 800, 700, 617):
        exprimes = int(arithmetique_abstention_congres(participation)["voix_requises"])
        scenarios[str(participation)] = {
            "suffrages_exprimes": exprimes,
            "membres_composant": seuil_sur_membres,
            "economie_de_voix": max(0, seuil_sur_membres - exprimes),
        }
    if not sur_membres:
        notes.append("l'abstention fait baisser le seuil : "
                     f"à 700 votants, {scenarios['700']['suffrages_exprimes']} voix au lieu de "
                     f"{seuil_sur_membres}")
    else:
        notes.append("le seuil est fixe : l'abstention ne fait gagner aucune voix")
    return {
        "voix_requises": voix,
        "assiette": "membres composant le Congrès" if sur_membres else "suffrages exprimés au Congrès",
        "effectif": CONGRES_EFFECTIF,
        "votants_simules": votants,
        "quorum_votants": quorum,
        "economie_de_voix": scenarios[str(votants)]["economie_de_voix"],
        "scenarios_abstention": scenarios,
        "formule": base["formule"],
        "note": " ; ".join(notes),
    }


def seuils_ajustes(parametres: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, Any]]:
    """Chaque verrou réglable, avec sa valeur de droit et sa valeur réglée."""
    regle = normaliser(parametres)
    resultat: Dict[str, Dict[str, Any]] = {}
    censure = _voix_censure(regle)
    congres = _congres(regle)
    seuils = {cle: int(seuil(cle)) for cle in VERROUS_REGLAGES}

    applicables: Dict[str, Tuple[Any, List[str], str]] = {
        "censure_voix": (
            censure["voix_requises"],
            ["reglage_censure_assiette"],
            censure["note"],
        ),
        "censure_delai": (
            seuils["censure_delai"] + 24 * int(regle.get("reglage_delai_motion_censure", 0.0)),
            ["reglage_delai_motion_censure"],
            "le délai constitutionnel est de deux jours francs ; chaque jour ajouté est un jour de négociation",
        ),
        "49_3_delai_motion": (
            seuils["49_3_delai_motion"] + int(regle.get("reglage_delai_motion_49_3", 0.0)),
            ["reglage_delai_motion_49_3"],
            "le temps de dépôt de la motion est le seul temps dont dispose l'opposition contre un 49.3",
        ),
        "49_3_plafond_texte": (
            0 if regle.get("reglage_49_3_interdiction", 0.0) >= 1.0 else seuils["49_3_plafond_texte"],
            ["reglage_49_3_interdiction"],
            "à zéro, tout texte doit être voté : le calendrier redevient une contrainte",
        ),
        "saisine_conseil_signatures": (
            {0: 60, 1: 40, 2: 15, 3: 0}[int(regle.get("reglage_seuil_saisine_conseil", 0.0))],
            ["reglage_seuil_saisine_conseil"],
            "à zéro signatures, le contrôle devient systématique et donc obligatoire pour tous les textes",
        ),
        "budget_an_delai": (
            max(5, seuils["budget_an_delai"] - int(regle.get("reglage_delai_budget_retraite", 0.0))),
            ["reglage_delai_budget_retraite"],
            "en deçà de cinq jours, le délai n'est plus tenable matériellement : plancher appliqué",
        ),
        "budget_senat_delai": (
            seuils["budget_senat_delai"] + int(regle.get("reglage_delai_senat_budget", 0.0)),
            ["reglage_delai_senat_budget"],
            "chaque jour donné au Sénat est retiré à la commission mixte paritaire",
        ),
        "budget_delai_total": (
            max(20, seuils["budget_delai_total"]
                - int(regle.get("reglage_delai_budget_retraite", 0.0))
                + int(regle.get("reglage_delai_senat_budget", 0.0))),
            ["reglage_delai_budget_retraite", "reglage_delai_senat_budget"],
            "le total commande la date à laquelle le budget est réputé adopté sans vote",
        ),
        "petition_locale": (
            int(regle.get("reglage_petition_locale_seuil", 0.0)),
            ["reglage_petition_locale_seuil"],
            "0 = aucun seuil national : la loi organique de l'article 72-1 n'est jamais parue, "
            "chaque assemblée locale fixe le sien ; un pourcentage le rend opposable partout",
        ),
        "referendum_local": (
            1 if regle.get("reglage_referendum_local_automatique", 0.0) >= 1.0 else 0,
            ["reglage_referendum_local_automatique"],
            "1 = la consultation a lieu de plein droit au seuil atteint : l'assemblée locale ne "
            "peut plus seulement en décider l'opportunité",
        ),
        "irrecevabilite_financiere": (
            1 if regle.get("reglage_droit_amendement", 0.0) >= 1.0 else 0,
            ["reglage_droit_amendement"],
            "1 : la qualification est contrôlée par un juge, plus par le seul président de séance",
        ),
        "etat_urgence_delai_parlement": (
            seuils["etat_urgence_delai_parlement"],
            ["reglage_controle_juge_exception"],
            "le délai de saisine du Parlement reste de douze jours : seul le contrôle du juge change",
        ),
        "procedure_acceleree_delai": (
            seuils["procedure_acceleree_delai"]
            + int(regle.get("reglage_procedure_acceleree_encadree", 0.0)),
            ["reglage_procedure_acceleree_encadree"],
            "le délai plancher est le seul freinage automatique de la navette courte : le "
            "relever rend le texte discutable sans toucher au vote",
        ),
        "promulgation_nouvelle_deliberation": (
            0 if regle.get("reglage_nouvelle_deliberation_supprimee", 0.0) >= 1.0
            else seuils["promulgation_nouvelle_deliberation"],
            ["reglage_nouvelle_deliberation_supprimee"],
            "à zéro jour, plus aucun texte ne repart en navette après le vote final : la "
            "promulgation suit immédiatement",
        ),
        "commission_enquete_signature": (
            max(1, seuils["commission_enquete_signature"]
                + int(regle.get("reglage_commission_enquete_droit_de_bloc", 0.0))),
            ["reglage_commission_enquete_droit_de_bloc"],
            "une garantie de plus, c'est une enquête par an et par groupe qui n'a plus à être "
            "négociée avec la majorité",
        ),
        "haute_cour_assemblees": (
            HAUTE_COUR_COLLEGE if regle.get("reglage_haute_cour_non_parlementaire", 0.0) >= 1.0
            else seuils["haute_cour_assemblees"],
            ["reglage_haute_cour_non_parlementaire"],
            "un collège de juges n'a pas à être réuni par un vote politique : la condition "
            "d'ouverture disparaît, l'affaire est jugée sur saisine",
        ),
        "haute_cour_destitution": (
            HAUTE_COUR_COLLEGE if regle.get("reglage_haute_cour_non_parlementaire", 0.0) >= 1.0
            else seuils["haute_cour_destitution"],
            ["reglage_haute_cour_non_parlementaire"],
            "deux tiers d'un collège de cent quatre-vingts juges professionnels, ce n'est plus "
            "le même décompte : la sanction devient juridique et non parlementaire",
        ),
        "lois_programmation_saisine_cee": (
            seuils["lois_programmation_saisine_cee"]
            + int(regle.get("reglage_cee_consultation_prealable", 0.0)),
            ["reglage_cee_consultation_prealable"],
            "à zéro jour, l'avis reste facultatif et postérieur ; chaque jour obligatoire est un "
            "jour de discussion sociale avant le dépôt, et un motif juridique de recours",
        ),
        "irrecevabilite_competence_delai": (
            seuils["irrecevabilite_competence_delai"]
            + int(regle.get("reglage_declassification_legislative", 0.0)),
            ["reglage_declassification_legislative"],
            "le délai du Conseil est le seul temps pendant lequel un article peut être "
            "reclassé sans révision : à zéro jour ajouté, la frontière loi-règlement bouge "
            "au moment même de la discussion",
        ),
    }
    for cle, (valeur_reglee, leviers, note) in applicables.items():
        verrou = VERROUS[cle]
        base = int(verrou.valeur) if cle == "irrecevabilite_financiere" else int(seuil(cle))
        ligne = {
            "cle": cle,
            "nom": verrou.nom,
            "article": verrou.article,
            "unite": UNITES_LISIBLES.get(cle, verrou.unite or verrou.assiette),
            "statu_quo": base,
            "regle": int(valeur_reglee),
            "ecart": int(valeur_reglee) - base,
            "reglages_appliques": [un for un in leviers if regle.get(un, 0.0) != LEVIERS[un].defaut],
            "note": note,
            "assiette": censure["assiette"] if cle == "censure_voix" else verrou.assiette,
            "libelle_reglage": VERROUS_REGLAGES[cle],
        }
        if cle == "censure_voix":
            ligne["note"] = f"{censure['formule']} — {censure['note']}"
            ligne["quorum_votants"] = int(censure.get("quorum_votants", 0))
        resultat[cle] = ligne

    resultat["congres_revision"] = {
        "cle": "congres_revision",
        "nom": VERROUS["congres_revision"].nom,
        "article": "89",
        "unite": "voix",
        "statu_quo": int(seuil("congres_revision")),
        "regle": congres["voix_requises"],
        "ecart": congres["voix_requises"] - int(seuil("congres_revision")),
        "assiette": congres["assiette"],
        "quorum_votants": congres["quorum_votants"],
        "economie_de_voix": congres["economie_de_voix"],
        "scenarios_abstention": congres["scenarios_abstention"],
        "formule": congres["formule"],
        "reglages_appliques": [
            cle for cle in ("reglage_congres_assiette_membres", "reglage_congres_quorum")
            if regle.get(cle, 0.0) != LEVIERS[cle].defaut
        ],
        "note": congres["note"],
        "libelle_reglage": "majorité exigée au Congrès pour réviser la Constitution",
    }
    resultat["seuil_groupe_assemblee_nationale"] = {
        "cle": "seuil_groupe_assemblee_nationale",
        "nom": "Seuil de constitution des groupes",
        "article": "51",
        "unite": "députés",
        "statu_quo": int(ETAT_ASSEMBLEES["assemblee_nationale"]["seuil_groupe"]),
        "regle": max(1, int(ETAT_ASSEMBLEES["assemblee_nationale"]["seuil_groupe"])
                     - int(regle.get("reglage_seuil_groupes", 0.0))),
        "ecart": -int(regle.get("reglage_seuil_groupes", 0.0)),
        "reglages_appliques": ([ "reglage_seuil_groupes"]
                               if regle.get("reglage_seuil_groupes", 0.0) else []),
        "note": "chaque groupe de plus, c'est une niche et un droit d'enquête en plus",
        "libelle_reglage": "nombre de sièges pour former un groupe",
    }
    mois = int(regle.get("reglage_plafond_etat_urgence", 0.0))
    resultat["etat_urgence_duree_max_mois"] = {
        "cle": "etat_urgence_duree_max_mois",
        "nom": "Durée maximale totale de l'état d'urgence",
        "article": "36",
        "unite": "mois",
        "statu_quo": 0,
        "regle": mois,
        "ecart": mois,
        "reglages_appliques": (["reglage_plafond_etat_urgence"] if mois else []),
        "note": ("aucune durée maximale : des prorogations successives peuvent rendre le régime permanent"
                 if mois == 0 else
                 f"au-delà de {mois} mois, le régime cesse de plein droit sans nouvelle loi"),
        "libelle_reglage": "fin automatique du régime d'exception",
    }
    return resultat


# ────────────────────────────────────────────────────────────────────────────
# 4. Délais, fenêtre et trajets
# ────────────────────────────────────────────────────────────────────────────

#: Étapes auxquelles la couche ajoute ou retire des jours : `trajet:etape` →
#: liste de (levier, jours par unité de réglage). Un nombre négatif est un retrait.
#: La journée parlementaire de l'étape « nouvelle_lecture » vaut un aller-retour complet.
ALLER_RETOUR_JOURS = 70
AVIS_CONSEIL_ETAT_JOURS = 15
#: Collège de la Haute Cour non parlementaire : 180 juges, deux tiers = 120 voix.
HAUTE_COUR_COLLEGE = 120
SAISINE_CONTROLE_JOURS = 30   # le Conseil statue dans le mois, la promulgation est suspendue
APPEL_FILTRE_JOURS = 60       # un second filtre, c'est un mois de plus avant la décision à fond

#: Les fenêtres de temps que les réglages peuvent rogner. Une seule aujourd'hui : la part
#: d'ordre du jour laissée au Gouvernement pendant la session.
FENETRES_REGLABLES: Tuple[str, ...] = ("utile",)

ETAPES_REGLABLES: Dict[str, Tuple[Tuple[str, int], ...]] = {
    "budget:an_vote": (("reglage_delai_budget_retraite", -1),),
    "budget:senat": (("reglage_delai_senat_budget", 1),),
    "renversement:delai": (("reglage_delai_motion_censure", 1),),
    "projet_ordinaire:conseil_etat_avis": (("reglage_audit_obligatoire_prealable",
                                            AVIS_CONSEIL_ETAT_JOURS),),
    "revision_referendum:referendum": (("reglage_controle_loi_referendaire", SAISINE_CONTROLE_JOURS),),
    "controle_juge:filtre": (("reglage_appel_qpc", APPEL_FILTRE_JOURS),),
    "projet_ordinaire:nouvelle_lecture": (("reglage_chambre_tiree_au_sort", 0),
                                          ("reglage_convention_veto_suspensif",
                                           ALLER_RETOUR_JOURS)),
}


def delais_ajustes(parametres: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Chaque trajet, ses jours de rigueur et leur tenabilité dans la fenêtre réglée."""
    regle = normaliser(parametres)
    part_parlementaire = float(regle.get("reglage_ordre_du_jour_partage", 0.0))
    fenetre = int(round(FENETRE_RESIDUELLE_JOURS * (1.0 - part_parlementaire / 100.0)))
    trajets: List[Dict[str, Any]] = []
    for cle, trajet in TRAJETS.items():
        reference = oscillation(cle)
        etapes = []
        total_statu_quo = 0
        total_regle = 0
        for etape in trajet.etapes:
            jours = int(etape.jours)
            identifiant = f"{cle}:{etape.cle}"
            reglages_appliques: List[str] = []
            delta = 0
            for levier, pas in ETAPES_REGLABLES.get(identifiant, ()):
                valeur = regle.get(levier, 0.0)
                if pas == 0:
                    # le réglage est une échelle, pas un nombre de jours : une chambre
                    # tirée au sort ajoute un aller-retour, quel que soit son effectif
                    contribution = ALLER_RETOUR_JOURS if valeur > 0 else 0
                else:
                    contribution = int(round(pas * valeur))
                if contribution:
                    delta += contribution
                    reglages_appliques.append(levier)
            jours_regles = max(0, jours + delta)
            total_statu_quo += jours
            total_regle += jours_regles
            etapes.append({
                "cle": etape.cle,
                "acte": etape.acte,
                "fondement": etape.fondement,
                "jours_statu_quo": jours,
                "jours_regles": jours_regles,
                "delta_jours": delta,
                "reglages_appliques": reglages_appliques,
            })
        trajets.append({
            "cle": cle,
            "nom": trajet.nom,
            "categorie": trajet.categorie,
            "etapes": etapes,
            "jours_de_rigueur_statu_quo": total_statu_quo,
            "jours_de_rigueur_regles": total_regle,
            "fenetre_residuelle": fenetre,
            "tenable_dans_la_fenetre": total_regle <= fenetre,
            "marge_jours": fenetre - total_regle,
            "retard_imposable": int(reference["retard_imposable"]),
            "battements": len(trajet.etapes),
            "issue": trajet.issue,
        })
    forcables = 0 if regle.get("reglage_49_3_interdiction", 0.0) >= 1.0 else 1
    chambre_en_plus = int(regle.get("reglage_chambre_tiree_au_sort", 0.0)) > 0
    veto_convention = regle.get("reglage_convention_veto_suspensif", 0.0) >= 1.0
    battements_supplementaires = (1 if chambre_en_plus else 0) + (1 if veto_convention else 0)
    return {
        "trajets": trajets,
        "fenetre_residuelle_statu_quo": FENETRE_RESIDUELLE_JOURS,
        "fenetre_residuelle_reglee": fenetre,
        "part_ordre_du_jour_parlementaire": part_parlementaire,
        "textes_forcables_par_session": forcables,
        "delai_execution_cedh_jours": int(regle.get("reglage_execution_cedh", 0.0)),
        "battements_ajoutes_par_reglages": battements_supplementaires,
        "jours_coherents_avec_oscillation": all(
            ligne["jours_de_rigueur_statu_quo"] == oscillation(ligne["cle"])["jours_de_rigueur"]
            for ligne in trajets
        ),
        "avertissement": "Les jours sont des délais de rigueur, pas des durées prévisibles : "
                        "les réglages déplacent la contrainte de calendrier, jamais sa réalité.",
    }


# ────────────────────────────────────────────────────────────────────────────
# 5. Fentes : ce que les réglages changent à une déduction
# ────────────────────────────────────────────────────────────────────────────

def _degre_neutralisation(cle_fente: str, regle: Dict[str, float]) -> Tuple[float, List[str]]:
    reglages = NEUTRALISATIONS.get(cle_fente, {})
    reste = 1.0
    appliques: List[str] = []
    for levier, poids in reglages.items():
        ouverture = taux(levier, regle) if levier in LEVIERS else 0.0
        if ouverture > 0.0:
            reste *= (1.0 - poids * ouverture)
            appliques.append(levier)
    return max(0.0, min(1.0, 1.0 - reste)), appliques


def fentes_recalculees(parametres: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Les fentes du droit, avec l'effet des réglages sur leur arithmétique et leur solidité."""
    regle = normaliser(parametres)
    seuils = seuils_ajustes(regle)
    lignes: List[Dict[str, Any]] = []
    for cle, fente in FENTES.items():
        degre, appliques = _degre_neutralisation(cle, regle)
        brut = robustesse(fente)
        score = int(round(brut["score"] * (1.0 - 0.7 * degre)))
        if degre >= 0.999:
            score = 0
        lecture: Dict[str, Any] = {}
        congres_ligne = seuils["congres_revision"]
        if cle == "censure_par_membres":
            lecture = {
                "statu_quo": "289 voix sur 577 membres composant",
                "regle": f"{seuils['censure_voix']['regle']} voix, "
                         f"assiette {seuils['censure_voix'].get('assiette', 'membres composant').lower()}",
                "chiffre_reglage": "reglage_censure_assiette",
            }
        elif cle == "congres_par_exprimes":
            lecture = {
                "statu_quo": f"{congres_ligne['statu_quo']} voix sur {CONGRES_EFFECTIF} suffrages exprimés",
                "regle": f"{congres_ligne['regle']} voix, "
                         f"{congres_ligne.get('assiette', 'suffrages exprimés').lower()}",
                "scenarios": congres_ligne["scenarios_abstention"],
                "chiffre_reglage": "reglage_congres_assiette_membres",
            }
        elif cle == "absence_de_quorum":
            quorum = int(congres_ligne.get("quorum_votants", 0))
            lecture = {
                "statu_quo": "aucun quorum n'est exigé dans les deux assemblées ni au Congrès",
                "regle": (f"quorum de {quorum} votants au Congrès ; rien pour les assemblées"
                          if quorum else "aucun quorum ajouté"),
                "chiffre_reglage": "reglage_congres_quorum",
            }
        lignes.append({
            "cle": cle,
            "nom": fente.nom,
            "type": fente.type,
            "sens": fente.sens,
            "etage": fente.etage,
            "robustesse_statu_quo": int(brut["score"]),
            "robustesse_reglee": score,
            "degre_neutralise": round(degre, 3),
            "neutralisee": degre >= 0.999,
            "reglages_appliques": appliques,
            "condition_de_verrouillage": fente.condition_de_verrouillage,
            "ce_que_ca_change": fente.ce_que_ca_change,
            "lecture_reglee": lecture or None,
            "note": ("verrouillée par le réglage : la déduction reste vraie, elle ne produit plus d'effet utile"
                     if degre >= 0.999 else
                     ("partiellement verrouillée : le réglage réduit la portée sans fermer la déduction"
                      if degre > 0.0 else "aucun réglage ne touche cette fente")),
            "irrefutabilite": None,
        })
    lignes.sort(key=lambda ligne: -ligne["robustesse_reglee"])
    return lignes


# ────────────────────────────────────────────────────────────────────────────
# 5 bis. Croisements : un article, tout ce qu'il règle et tout ce qu'il débloque
# ────────────────────────────────────────────────────────────────────────────

def _numero(identifiant: str) -> str:
    """`CONST_ART_88_6` → `88-6` ; les autres textes gardent leur identifiant brut."""
    if identifiant.startswith("CONST_ART_"):
        return identifiant[len("CONST_ART_"):].replace("_", "-")
    return ""


def _citations(objet: Any) -> List[str]:
    """Les numéros d'article cités par un objet d'un module de droit.

    Les modules citent tantôt `articles`, tantôt `fondement` (liste ou prose), tantôt un
    `fondement_resolu`. On ne garde que le premier nombre de chaque citation : « 65 al. 6 »
    cite l'article 65, pas l'article 6.
    """
    bruts: List[str] = []
    for champ in ("articles", "fondement"):
        valeur = getattr(objet, champ, None)
        if isinstance(valeur, str):
            bruts.append(valeur)
        elif valeur:
            bruts.extend(str(item) for item in valeur)
    resolu = getattr(objet, "fondement_resolu", None)
    if isinstance(resolu, dict):
        bruts.extend(str(item) for item in resolu.get("articles", ()))
    numeros: set = set()
    for brut in bruts:
        trouve = re.search(r"(\d+(?:-\d+)?)", brut)
        if trouve:
            numeros.add(trouve.group(1))
    return sorted(numeros, key=lambda item: (len(item), item))


def croisements() -> Dict[str, Dict[str, List[str]]]:
    """Index article → {réglages, verrous, mécanismes, instances, fentes, trajets, stratégies}.

    Tout est déduit des citations déjà portées par les modules : aucun lien n'est saisi à la
    main, donc aucun lien ne peut pourrir en silence.
    """
    index: Dict[str, Dict[str, List[str]]] = {}

    def ajouter(numero: str, categorie: str, cle: str) -> None:
        if not numero:
            return
        ligne = index.setdefault(numero, {c: [] for c in (
            "reglages", "verrous", "mecanismes", "instances", "fentes", "trajets", "strategies")})
        if cle not in ligne[categorie]:
            ligne[categorie].append(cle)

    for cle in reglages_catalogue():
        for identifiant in LEVIERS[cle].articles:
            ajouter(_numero(identifiant), "reglages", cle)
    for cle, verrou in VERROUS.items():
        ajouter(str(verrou.article), "verrous", cle)
    for cle, mecanisme in MECANISMES.items():
        for numero in _citations(mecanisme):
            ajouter(numero, "mecanismes", cle)
    for cle, instance in INSTANCES.items():
        for numero in _citations(instance):
            ajouter(numero, "instances", cle)
    for cle, fente in FENTES.items():
        for numero in _citations(fente):
            ajouter(numero, "fentes", cle)
    for cle, trajet in TRAJETS.items():
        for numero in _citations(trajet):
            ajouter(numero, "trajets", cle)
        for etape in trajet.etapes:
            for numero in re.findall(r"(\d+(?:-\d+)?)", str(etape.fondement or "")):
                ajouter(numero, "trajets", cle)
    for cle, strategie in STRATEGIES.items():
        for numero in _citations(strategie):
            ajouter(numero, "strategies", cle)
    for ligne in index.values():
        for categorie in ligne:
            ligne[categorie].sort()
    return dict(sorted(index.items(), key=lambda item: (len(item[0]), item[0])))


#: Les six registres de connaissance que la couche doit pouvoir croiser.
REPERTOIRES: Dict[str, Dict[str, Any]] = {
    "verrou": VERROUS,
    "fente": FENTES,
    "trajet": TRAJETS,
    "mecanisme": MECANISMES,
    "instance": INSTANCES,
    "strategie": STRATEGIES,
}


def reglages_par_connaissance(categorie: str) -> Dict[str, List[str]]:
    """Index inverse : pour chaque verrou / fente / trajet / mécanisme / instance / stratégie,
    les réglages qui la touchent — par cible déclarée puis par citation d'article."""
    champ = {"verrou": "verrous", "fente": "fentes", "trajet": "trajets",
             "mecanisme": "mecanismes", "instance": "instances", "strategie": "strategies"}[categorie]
    index: Dict[str, List[str]] = {}
    for ligne in croisements().values():
        for cle in ligne[champ]:
            index.setdefault(cle, [])
            for levier in ligne["reglages"]:
                if levier not in index[cle]:
                    index[cle].append(levier)
    for levier, reglage in REGLAGES.items():
        for type_cible, identifiant in reglage.get("cibles", ()):
            if type_cible == "etape":
                identifiant = identifiant.split(":")[0]
                type_cible = "trajet"
            if type_cible != categorie:
                continue
            index.setdefault(identifiant, [])
            if levier not in index[identifiant]:
                index[identifiant].append(levier)
    return {cle: sorted(cles) for cle, cles in sorted(index.items())}


def normalise_numero(valeur: str) -> str:
    """`49`, `article 49`, `CONST_ART_49`, `art. 72-1` → `49`, `72-1`."""
    texte = str(valeur or "").strip()
    trouve = re.search(r"(\d+(?:-\d+)?)", texte.replace("_", "-"))
    return trouve.group(1) if trouve else texte


def croisement_pour(numero: str) -> Dict[str, Any]:
    """
    Tout ce qu'un article dresse comme pouvoir, comme contrainte et comme réglage.

    Le numéro accepte toutes les notations usuelles (`49`, `article 49`, `CONST_ART_49`,
    `art. 72-1`) : les navigateurs, les fiches et les tests n'écrivent pas tous pareil.
    """
    numero = normalise_numero(numero)
    ligne = croisements().get(numero, {cle: [] for cle in (
        "reglages", "verrous", "mecanismes", "instances", "fentes", "trajets", "strategies")})
    vecteur = valeurs_par_defaut()
    seuils = {cle: valeur for cle, valeur in seuils_ajustes(vecteur).items() if cle in ligne["verrous"]}
    fentes = {entree["cle"]: entree for entree in fentes_recalculees(vecteur)
              if entree["cle"] in ligne["fentes"]}
    return {
        "article": numero,
        "identifiant_registre": f"CONST_ART_{numero.replace('-', '_')}",
        "present_dans_le_registre": f"CONST_ART_{numero.replace('-', '_')}" in REGISTRE_LEGAL,
        **ligne,
        "seuils": seuils,
        "fentes": fentes,
        "fiches": nuances_pour_article(f"CONST_ART_{numero.replace('-', '_')}"),
        "compte": {cle: len(valeurs) for cle, valeurs in ligne.items()},
    }


def reglages_touchant(categorie: str, cle: str) -> List[str]:
    """Les réglages qui touchent un verrou, une fente, un trajet, un mécanisme ou une instance."""
    if categorie == "reglage":
        return []
    resultat: List[str] = []
    for levier in reglages_catalogue():
        for type_cible, identifiant in REGLAGES[levier].get("cibles", ()):
            if type_cible in ("index", "seuil_derive", "mecanisme") and categorie != type_cible:
                continue
            if type_cible == "etape":
                _, _, identifiant = identifiant.partition(":")
            if type_cible == categorie and identifiant == cle and levier not in resultat:
                resultat.append(levier)
    for ligne in croisements().values():
        if cle in ligne.get(categorie + "s", []) if categorie != "verrou" else cle in ligne["verrous"]:
            for levier in ligne["reglages"]:
                if levier not in resultat:
                    resultat.append(levier)
    return sorted(resultat)


def strates_touchees(cle: str) -> List[int]:
    """Les strates du simulateur (1 locale → 5 géopolitique) que ce réglage traverse."""
    from .bulles import strates_theme
    strates: set = set()
    for theme in LEVIERS[cle].effets_directs:
        strates.update(strates_theme(theme))
    return sorted(int(num) for num in strates)


def par_strate(parametres: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Réglages déplacés par strate, avec les seuils et les fentes concernés."""
    regle = normaliser(parametres)
    seuils = seuils_ajustes(regle)
    fentes = {ligne["cle"]: ligne for ligne in fentes_recalculees(regle)}
    lignes: Dict[int, Dict[str, Any]] = {}
    for cle in reglages_catalogue():
        for strate in strates_touchees(cle) or [2]:
            ligne = lignes.setdefault(strate, {
                "strate": strate, "reglages": [], "reglages_actifs": [],
                "verrous_touches": [], "fentes_verrouillees": []})
            ligne["reglages"].append(cle)
            if regle.get(cle, 0.0) != LEVIERS[cle].defaut:
                ligne["reglages_actifs"].append(cle)
            for type_cible, identifiant in REGLAGES[cle].get("cibles", ()):
                if type_cible == "verrou" and identifiant in seuils:
                    if seuils[identifiant]["reglages_appliques"]:
                        ligne["verrous_touches"].append(identifiant)
                if type_cible == "fente" and identifiant in fentes:
                    if fentes[identifiant]["neutralisee"]:
                        ligne["fentes_verrouillees"].append(identifiant)
    for ligne in lignes.values():
        for champ in ("verrous_touches", "fentes_verrouillees", "reglages", "reglages_actifs"):
            ligne[champ] = sorted(set(ligne[champ]))
        ligne["libelle"] = _LIBELLE_STRATE.get(ligne["strate"], f"strate {ligne['strate']}")
    return [lignes[cle] for cle in sorted(lignes)]


_LIBELLE_STRATE = {
    1: "communes, intercommunalités, départements, régions",
    2: "nation : loi, règlement, budgétaire",
    3: "Union européenne et zone euro",
    4: "mondial : commerce, dette, énergie",
    5: "géopolitique : tensions et chokepoints",
}


# ────────────────────────────────────────────────────────────────────────────
# 6. Indices institutionnels
# ────────────────────────────────────────────────────────────────────────────

def indices_nuances(parametres: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, Any]]:
    """Sept indices + un : 50 = l'état du droit, ni bien ni mal, tel qu'il est écrit."""
    regle = normaliser(parametres)
    indices: Dict[str, Dict[str, Any]] = {}
    for cle, definition in INDICES.items():
        composants: List[Dict[str, Any]] = []
        brut = 0.0
        for levier, contributions in APPORTS.items():
            if cle not in contributions:
                continue
            coefficient = contributions[cle]
            ouverture = taux(levier, regle)
            points = coefficient * ouverture
            if abs(points) < 1e-9:
                continue
            brut += points
            composants.append({
                "reglage": levier,
                "libelle": LEVIERS[levier].libelle,
                "taux": round(ouverture, 3),
                "points": round(points, 2),
                "regle": REGLAGES.get(levier, {}).get("regle", ""),
            })
        composants.sort(key=lambda ligne: -abs(ligne["points"]))
        valeur = max(0.0, min(100.0, 50.0 + brut))
        indices[cle] = {
            "cle": cle,
            "nom": cle.replace("_", " "),
            "definition": definition,
            "valeur": round(valeur, 1),
            "brut": round(brut, 1),
            "statu_quo": 50.0,
            "ecart": round(valeur - 50.0, 1),
            "borne_appliquee": valeur != 50.0 + brut,
            "composants": composants,
            "lecture": _lecture_indice(cle, valeur, composants),
        }
    return indices


def _lecture_indice(cle: str, valeur: float, composants: List[Dict[str, Any]]) -> str:
    ecart = round(valeur - 50.0, 1)
    if abs(ecart) < 0.6:
        return "état du droit : aucun réglage institutionnel n'a été déplacé"
    mouvement = "augmente" if ecart > 0 else "diminue"
    premier = composants[0]["libelle"].lower() if composants else "le réglage"
    return (f"{mouvement} de {abs(ecart):g} point{'s' if abs(ecart) >= 2 else ''} l'« {cle.replace('_', ' ')} », "
            f"sous l'effet de {premier}")


# ────────────────────────────────────────────────────────────────────────────
# 7. Tableau par niveau, contexte, cohérence
# ────────────────────────────────────────────────────────────────────────────

def tableau_des_strates(parametres: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Même tableau, lu dans la grille à cinq échelons du simulateur."""
    return par_strate(parametres)


def tableau_des_niveaux(parametres: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Pour chaque niveau, les réglages actifs et leurs effets agrégés sur les domaines."""
    regle = normaliser(parametres)
    lignes: List[Dict[str, Any]] = []
    for niveau in NIVEAUX:
        cles = [cle for cle in reglages_catalogue() if niveau_de(cle) == niveau]
        actifs = [cle for cle in cles if regle.get(cle, 0.0) != LEVIERS[cle].defaut]
        domaines: Dict[str, float] = {}
        for cle in actifs:
            effet = LEVIERS[cle].effets_directs
            for theme, coefficient in effet.items():
                domaines[theme] = round(domaines.get(theme, 0.0) + coefficient * regle[cle], 2)
        articles = sorted({
            identifiant for cle in cles for identifiant in LEVIERS[cle].articles
        })
        lignes.append({
            "niveau": niveau,
            "reglages": cles,
            "reglages_actifs": actifs,
            "nombre_reglages": len(cles),
            "domaines_affectes": dict(sorted(domaines.items(), key=lambda item: -abs(item[1]))),
            "articles": articles,
            "verdict": (f"{len(actifs)} réglage{'s' if len(actifs) > 1 else ''} déplacé"
                        f"{'s' if len(actifs) > 1 else ''} sur {len(cles)}"
                        if actifs else f"niveau au statu quo ({len(cles)} réglages disponibles)"),
        })
    return lignes


def contexte_institutionnel(parametres: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Tout ce que la couche sait calculer, en un objet sérialisable."""
    regle = normaliser(parametres)
    return {
        "reglages": {
            cle: {
                "valeur": regle[cle],
                "defaut": LEVIERS[cle].defaut,
                "taux": round(taux(cle, regle), 3),
                "niveau": niveau_de(cle),
                "libelle": LEVIERS[cle].libelle,
                "unite": LEVIERS[cle].unite,
                "type": LEVIERS[cle].type,
                "regle": REGLAGES.get(cle, {}).get("regle", ""),
                "effet": REGLAGES.get(cle, {}).get("effet", ""),
                "cibles": [list(cible) for cible in REGLAGES.get(cle, {}).get("cibles", ())],
                "articles": list(LEVIERS[cle].articles),
                "strates": strates_touchees(cle),
                "sans_geometrie": REGLAGES_SANS_GEOMETRIE.get(cle, ""),
                "deplace": regle[cle] != LEVIERS[cle].defaut,
            }
            for cle in reglages_catalogue()
        },
        "seuils": seuils_ajustes(regle),
        "delais": delais_ajustes(regle),
        "fentes": fentes_recalculees(regle),
        "indices": indices_nuances(regle),
        "niveaux": tableau_des_niveaux(regle),
        "strates": par_strate(regle),
        "verrous": etat_des_verrous(regle),
        "resume": {
            "reglages_disponibles": len(reglages_catalogue()),
            "reglages_deplaces": sum(1 for cle in reglages_catalogue()
                                     if regle[cle] != LEVIERS[cle].defaut),
            "fentes_neutralisees": [ligne["cle"] for ligne in fentes_recalculees(regle) if ligne["neutralisee"]],
            "trajets_tenables": sum(1 for ligne in delais_ajustes(regle)["trajets"]
                                    if ligne["tenable_dans_la_fenetre"]),
            "trajets": len(TRAJETS),
            "articles_croises": len(croisements()),
            "strates_touchees": sorted({strate for cle in reglages_catalogue()
                                        for strate in strates_touchees(cle)}),
            "reglages_sans_geometrie": len(REGLAGES_SANS_GEOMETRIE),
        },
    }


def coherence_nuances() -> Dict[str, Any]:
    """Contrôles internes : rien ne doit être déclaré sans exister, ni exister sans règle."""
    catalogue = reglages_catalogue()
    declares = reglages_presents()
    manquants = [cle for cle in catalogue if cle not in REGLAGES]
    orphelins = [cle for cle in REGLAGES if cle not in LEVIERS]
    cibles_inconnues: List[str] = []
    for cle, reglage in REGLAGES.items():
        for type_cible, identifiant in reglage.get("cibles", ()):
            if type_cible == "verrou" and identifiant not in VERROUS:
                cibles_inconnues.append(f"{cle}:{type_cible}:{identifiant}")
            elif type_cible == "fente" and identifiant not in FENTES:
                cibles_inconnues.append(f"{cle}:{type_cible}:{identifiant}")
            elif type_cible == "trajet" and identifiant not in TRAJETS:
                cibles_inconnues.append(f"{cle}:{type_cible}:{identifiant}")
            elif type_cible == "etape":
                trajet, _, etape = identifiant.partition(":")
                if trajet not in TRAJETS:
                    cibles_inconnues.append(f"{cle}:{type_cible}:{identifiant}")
                elif etape and etape not in {e.cle for e in TRAJETS[trajet].etapes}:
                    cibles_inconnues.append(f"{cle}:{type_cible}:{identifiant}")
            elif type_cible == "index" and identifiant not in INDICES:
                cibles_inconnues.append(f"{cle}:{type_cible}:{identifiant}")
            elif type_cible == "mecanisme" and identifiant not in MECANISMES:
                cibles_inconnues.append(f"{cle}:{type_cible}:{identifiant}")
            elif type_cible == "fenetre" and identifiant not in FENETRES_REGLABLES:
                cibles_inconnues.append(f"{cle}:{type_cible}:{identifiant}")
            elif type_cible not in ("verrou", "fente", "trajet", "etape", "index",
                                    "mecanisme", "fenetre", "seuil_derive"):
                cibles_inconnues.append(f"{cle}:type_inconnu:{type_cible}")
    articles_fausses = sorted({
        identifiant for cle in catalogue for identifiant in LEVIERS[cle].articles
        if identifiant not in REGISTRE_LEGAL
    })
    indices = indices_nuances()
    indices_fous = [cle for cle, ligne in indices.items()
                    if not 0.0 <= ligne["valeur"] <= 100.0]
    seuils = seuils_ajustes()
    delais = delais_ajustes()
    neutres = {
        "seuils_identiques_au_droit": all(
            ligne["regle"] == ligne["statu_quo"] for ligne in seuils.values()
        ),
        "trajets_identiques_au_droit": all(
            ligne["jours_de_rigueur_regles"] == ligne["jours_de_rigueur_statu_quo"]
            for ligne in delais["trajets"]
        ),
        "fentes_inchangees": all(ligne["degre_neutralise"] == 0.0 for ligne in fentes_recalculees()),
        "indices_a_cinquante": all(ligne["valeur"] == 50.0 for ligne in indices.values()),
    }
    fentes_ciblees = sorted({
        identifiant for reglage in REGLAGES.values()
        for type_cible, identifiant in reglage.get("cibles", ()) if type_cible == "fente"
    })
    fentes_orphelines = sorted(set(FENTES) - set(fentes_ciblees))
    apports_orphelins = sorted(set(APPORTS) - set(catalogue))
    lignes_strates = par_strate()
    reglages_sans_strate = sorted(
        set(catalogue) - {cle for ligne in lignes_strates for cle in ligne["reglages"]})
    without_geometry = reglages_sans_cible_chiffree()
    verrous_tous = set(VERROUS)
    lignes_croisements = croisements()
    accessibles = {}
    for categorie, repertoire in REPERTOIRES.items():
        index_inverse = reglages_par_connaissance(categorie)
        reglables = {cle for cle, cles in index_inverse.items() if cles}
        accessibles[categorie] = {
            "total": len(repertoire),
            "avec_reglage": len(reglables),
            "sans_reglage": sorted(set(repertoire) - reglables),
            "index_inverse": index_inverse,
        }
    trajets_sans_reglage = accessibles["trajet"]["sans_reglage"]
    fentes_sans_reglage = accessibles["fente"]["sans_reglage"]
    # Le contrat « zéro trou », dans sa forme la plus exigeante : chaque pièce de chaque
    # registre doit être joignable par au moins un réglage, sauf les verrous qu'un réglage
    # ne peut pas déplacer et qui sont alors explicitement expliqués plus haut.
    connaissances_inaccessibles = sorted(
        f"{categorie}:{cle}"
        for categorie, repertoire in REPERTOIRES.items()
        for cle in repertoire
        if not accessibles[categorie]["index_inverse"].get(cle)
        and not (categorie == "verrou" and cle in VERROUS_HORS_REGLAGE)
    )
    return {
        "verrous_non_expliques": sorted(verrous_tous - set(VERROUS_REGLAGES) - set(VERROUS_HORS_REGLAGE)),
        "verrous_doublement_classes": sorted(set(VERROUS_REGLAGES) & set(VERROUS_HORS_REGLAGE)),
        "verrous_inventes": sorted((set(VERROUS_REGLAGES) | set(VERROUS_HORS_REGLAGE)) - verrous_tous),
        "reglages_sans_cible_chiffree": [cle for cle in without_geometry if cle not in REGLAGES_SANS_GEOMETRIE],
        # Un verrou annoncé « réglable » doit soit bouger à l'ouverture de son réglage, soit
        # être déclaré insensible avec une raison. Les deux erreurs sont attrapées ici.
        "seuils_insensibles_perimes": sorted(
            cle for cle in SEUILS_INSSENSIBLES
            if cle not in VERROUS_REGLAGES
            or not SEUILS_INSSENSIBLES[cle].strip()
            or seuils_ajustes({reglage: (LEVIERS[reglage].maximum or 1.0)
                               for reglage in reglages_touchant("verrou", cle)}
                              ).get(cle, {}).get("ecart", 0)),
        "verrous_reglables_sans_explication": sorted(
            cle for cle in VERROUS_REGLAGES
            if cle not in SEUILS_INSSENSIBLES
            and not reglages_touchant("verrou", cle)),
        "verrous_doublement_classes_note": sorted(
            cle for cle, ligne in seuils_ajustes().items()
            if len(ligne["reglages_appliques"]) > 2),
        "exemptions_perimees": sorted(
            cle for cle in REGLAGES_SANS_GEOMETRIE if cle not in without_geometry),
        "exemptions_vides": sorted(cle for cle, raison in REGLAGES_SANS_GEOMETRIE.items()
                                   if not raison.strip()),
        "reglages_sans_article": sorted(cle for cle in catalogue if not LEVIERS[cle].articles),
        "strates_couvertes": sorted({strate for cle in catalogue for strate in strates_touchees(cle)}),
        # Un réglage qui ne traverserait aucune strate serait un réglage invisible : la
        # strate est déduite des thèmes d'effet, jamais déclarée à la main.
        "reglages_sans_strate": reglages_sans_strate,
        "trajets_sans_reglage": trajets_sans_reglage,
        "connaissances_inaccessibles": connaissances_inaccessibles,
        "accesibilite_des_connaissances": {
            categorie: {cle: valeur for cle, valeur in ligne.items()
                        if cle != "index_inverse"}
            for categorie, ligne in accessibles.items()
        },
        "total_connaissances": {
            "verrous": len(VERROUS), "fentes": len(FENTES), "trajets": len(TRAJETS),
            "mecanismes": len(MECANISMES), "instances": len(INSTANCES),
            "strategies": len(STRATEGIES), "articles_croises": len(lignes_croisements),
        },
        # Un réglage peut traverser plusieurs strates : la somme des compteurs dépasse
        # donc le nombre de réglages. C'est la couverture qui doit être exhaustive.
        "reglages_par_strate": {str(ligne["strate"]): len(ligne["reglages"])
                                for ligne in lignes_strates},
        "reglages_catalogue": len(catalogue),
        "reglages_declares": len(declares),
        "reglages_sans_regle": manquants,
        "reglages_inconnus": orphelins,
        "cibles_inconnues": cibles_inconnues,
        "articles_hors_registre": articles_fausses,
        "indices_anormaux": indices_fous,
        # Deux façons de manquer une fente : ne la déclarer cible d'aucun réglage, ou ne
        # la rendre joignable par aucun réglage par le chemin des articles. Les deux
        # listes doivent rester vides — ce sont elles qui garantissent « zéro trou ».
        "fentes_ciblees_par_un_reglage": fentes_ciblees,
        "fentes_non_ciblees": fentes_orphelines,
        "fentes_inaccessibles_d_un_reglage": fentes_sans_reglage,
        "apports_sans_reglage": apports_orphelins,
        # Les verrous réellement déplacés par le vecteur courant — déduit des écarts,
        # jamais d'une liste recopiée (une liste recopiée ment dès qu'un nom change).
        "verrous_regles": sorted(cle for cle, ligne in seuils.items() if ligne["reglages_appliques"]),
        "verrous_reglables": sorted(set(VERROUS_REGLAGES) & verrous_tous),
        "verrous_expliques_hors_reglage": sorted(set(VERROUS_HORS_REGLAGE) & verrous_tous),
        "controles_neutres": neutres,
    }


def nuances_pour_article(identifiant: str) -> List[Dict[str, Any]]:
    """Les réglages qui touchent un article (identifiant du registre légal)."""
    lignes = []
    for cle in reglages_catalogue():
        if identifiant in LEVIERS[cle].articles:
            lignes.append({
                "reglage": cle,
                "libelle": LEVIERS[cle].libelle,
                "niveau": niveau_de(cle),
                "regle": REGLAGES.get(cle, {}).get("regle", ""),
                "effet": REGLAGES.get(cle, {}).get("effet", ""),
            })
    return lignes


def nuances_pour_levier(cle: str) -> Dict[str, Any]:
    """Fiche d'un réglage : ce qu'il change, où, et avec quel effet mesuré."""
    if cle not in LEVIERS:
        return {"erreur": "levier inconnu", "cle": cle}
    vecteur = {cle: LEVIERS[cle].maximum if LEVIERS[cle].type != "choix" else max(
        v for _, v in (LEVIERS[cle].modalites or [(0.0, 0.0)]))}
    seuils = seuils_ajustes(vecteur)
    fentes = [ligne for ligne in fentes_recalculees(vecteur) if cle in ligne["reglages_appliques"]]
    indices = {
        nom: ligne for nom, ligne in indices_nuances(vecteur).items()
        if any(composant["reglage"] == cle for composant in ligne["composants"])
    }
    touches = [
        {"verrou": ligne["cle"], "nom": ligne["nom"], "statu_quo": ligne["statu_quo"],
         "regle": ligne["regle"], "unite": ligne["unite"]}
        for ligne in seuils.values()
        if cle in ligne["reglages_appliques"]
    ]
    return {
        "cle": cle,
        "libelle": LEVIERS[cle].libelle,
        "description": LEVIERS[cle].description,
        "source": LEVIERS[cle].source,
        "articles": list(LEVIERS[cle].articles),
        "niveau": niveau_de(cle),
        "regle": REGLAGES.get(cle, {}).get("regle", ""),
        "effet": REGLAGES.get(cle, {}).get("effet", ""),
        "bornes": list(_bornes(cle)),
        "touchant": touches,
        "fentes_affectees": [
            {"cle": ligne["cle"], "nom": ligne["nom"], "robustesse_statu_quo": ligne["robustesse_statu_quo"],
             "robustesse_reglee": ligne["robustesse_reglee"], "neutralisee": ligne["neutralisee"]}
            for ligne in fentes
        ],
        "indices_affectes": [
            {"cle": nom, "valeur_borne_haute": ligne["valeur"], "definition": ligne["definition"]}
            for nom, ligne in sorted(indices.items())
        ],
        "effets_domaines": dict(LEVIERS[cle].effets_directs),
    }


# ────────────────────────────────────────────────────────────────────────────
# 8. Sorties
# ────────────────────────────────────────────────────────────────────────────

def _verrous_neutralises(regle: Dict[str, float]) -> Dict[str, List[str]]:
    """Verrous privés de leur objet par un réglage déplacé : `{verrou: [réglages]}`."""
    resultat: Dict[str, List[str]] = {}
    for cle, reglages in NEUTRALISATIONS.items():
        actifs = sorted(levier for levier, poids in reglages.items()
                        if poids and taux(levier, regle) > 0)
        if actifs:
            resultat[cle] = actifs
    return resultat


def etat_des_verrous(parametres: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Où en est chaque verrou du registre avec le vecteur de réglages actif.

    Trois colonnes, et rien d'autre : `touches` (un réglage déplacé le bouge ou le
    neutralise), `intacts` (le verrou existe, aucun réglage ne le atteint — la
    protection tient), `hors_reglage` (le verrou ne peut pas être atteint par un
    curseur, et `VERROUS_HORS_REGLAGE` dit pourquoi). La somme doit faire exactement
    les 38 verrous de `gouvernance_contrepouvoir.VERROUS` : c'est ce que contrôle
    `coherence_nuances()`, et c'est ce que la page affiche sans rien inventer.
    """
    regle = normaliser(parametres)
    seuils = seuils_ajustes(regle)
    touches: List[Dict[str, Any]] = []
    intacts: List[Dict[str, Any]] = []
    hors_reglage: List[Dict[str, Any]] = []
    for cle, verrou in VERROUS.items():
        ligne = seuils.get(cle)
        occurrence: Dict[str, Any] = {
            "cle": cle,
            "nom": verrou.nom,
            "article": verrou.article,
            "registre": "gouvernance_contrepouvoir.VERROUS",
        }
        if ligne is not None:
            occurrence.update(
                unite=ligne["unite"],
                seuil_statu_quo=ligne["statu_quo"],
                seuil_regule=ligne["regle"],
                ecart=ligne["ecart"],
                reglages=ligne["reglages_appliques"],
                note=ligne["note"],
            )
            (touches if ligne["reglages_appliques"] else intacts).append(occurrence)
            continue
        neutralise_par = _verrous_neutralises(regle).get(cle, [])
        if neutralise_par:
            occurrence.update(reglages=sorted(neutralise_par),
                              note="neutralisé : la règle n'a plus d'objet")
            touches.append(occurrence)
            continue
        occurrence["explication"] = VERROUS_HORS_REGLAGE.get(cle, "")
        occurrence["reglages"] = reglages_touchant("verrou", cle)
        hors_reglage.append(occurrence)
    return {
        "total": len(VERROUS),
        "touches": touches,
        "intacts": intacts,
        "hors_reglage": hors_reglage,
        # Une neutralisation porte souvent sur une règle *dérivée* (l'assiette de la
        # censure, le décompte au Congrès) qui n'a pas d'entrée dans VERROUS : le
        # libellé vient donc du réglage qui neutralise, jamais d'un inventaire.
        "avertissements": [
            {"cle": cle,
             "nom": (VERROUS[cle].nom if cle in VERROUS
                     else VERROUS_REGLAGES.get(cle, cle)),
             "article": (VERROUS[cle].article if cle in VERROUS
                         else (LEVIERS[reglages[0]].articles or ("",))[0]),
             "reglages": reglages,
             "message": f"règle privée de son objet par {', '.join(reglages)}"}
            for cle, reglages in _verrous_neutralises(regle).items()
        ],
    }


def synthese_pour_api(parametres: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Ce que sert `/api/nuances` : le contexte complet, plus sa lecture courte."""
    contexte = contexte_institutionnel(parametres)
    indices = contexte["indices"]
    return {
        "objet": "nuances_institutionnelles",
        "date_observation": "2026-10-12",
        "champ": "réglages institutionnels, seuils, délais, fentes et indices, recalculés",
        "statut": "couche de calcul : aucune valeur n'est saisie, tout part des modules de droit",
        "reglages": contexte["reglages"],
        "seuils": contexte["seuils"],
        "delais": contexte["delais"],
        "fentes": contexte["fentes"],
        "indices": indices,
        "niveaux": contexte["niveaux"],
        "strates": contexte["strates"],
        "verrous": contexte["verrous"],
        "croisements": croisements(),
        "resume": contexte["resume"],
        "coherence": coherence_nuances(),
        "limites": [
            "un indice à 50 est l'état du droit, pas une moyenne de bonheur",
            "les jours sont des délais de rigueur, pas des durées prévisibles",
            "une fente neutralisée est verrouillée par un réglage, jamais réfutée",
            "aucun réglage ne rend une déduction irréfragable : les scores ne valent pas immunité",
        ],
    }


def resume_console(parametres: Optional[Dict[str, Any]] = None) -> str:
    """Lecture texte, une ligne par information utile."""
    synthese = synthese_pour_api(parametres)
    regle = normaliser(parametres)
    lignes: List[str] = []
    lignes.append(f"Réglages institutionnels : {synthese['resume']['reglages_disponibles']} disponibles, "
                  f"{synthese['resume']['reglages_deplaces']} déplacés")
    for ligne in sorted(synthese["seuils"].values(), key=lambda d: -abs(d["ecart"]))[:6]:
        fleche = "—" if not ligne["ecart"] else f"{ligne['ecart']:+d}"
        lignes.append(f"  seuil {ligne['nom']} : {ligne['regle']} {ligne['unite']} "
                      f"(droit : {ligne['statu_quo']}, écart {fleche})")
    for trajet in synthese["delais"]["trajets"]:
        if trajet["jours_de_rigueur_regles"] != trajet["jours_de_rigueur_statu_quo"] or not trajet["tenable_dans_la_fenetre"]:
            etat = "tenable" if trajet["tenable_dans_la_fenetre"] else "HORS FENÊTRE"
            lignes.append(f"  trajet {trajet['nom']} : {trajet['jours_de_rigueur_regles']} jours "
                          f"(droit : {trajet['jours_de_rigueur_statu_quo']}), fenêtre {trajet['fenetre_residuelle']} j → {etat}")
    neutralisees = synthese["resume"]["fentes_neutralisees"]
    lignes.append("  fentes verrouillées par les réglages : "
                  + (", ".join(neutralisees) if neutralisees else "aucune"))
    for cle, indice in sorted(synthese["indices"].items(), key=lambda item: -abs(item[1]["ecart"])):
        lignes.append(f"  indice {cle.replace('_', ' ')} : {indice['valeur']:g}/100 "
                      f"({indice['ecart']:+g} vs droit)")
    lignes.append("  " + synthese["delais"]["avertissement"])
    lignes.append("  " + ("tous les réglages sont au statu quo : les sorties sont celles des modules de droit"
                          if not any(regle[cle] != LEVIERS[cle].defaut for cle in regle) else
                          "les chiffres ci-dessus sont recalculés à partir des seuls réglages déplacés"))
    return "\n".join(lignes)
