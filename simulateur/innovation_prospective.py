"""simulateur/innovation_prospective.py — R&D Innovation, prospective technologique et chiffrage des stocks.

Ce module prolonge la démarche de R&D et de prospective du simulateur sur trois
fronts complémentaires, ancrés sur les horizons de 5 ans (mandature) et 10 ans
(deux mandatures consécutives) :

1. **Diffusion de l'innovation et rendements de la R&D (2026-2036)** :
   Modélisation de la courbe de diffusion en S (loi logistique de diffusion
   technologique, issue des travaux sur la croissance endogène d'Aghion-Howitt et
   de France Stratégie). Délais de latence (1 à 2 ans), amorçage industriel (3 à 5 ans)
   et pleine diffusion de la Productivité Globale des Facteurs (PGF, 6 à 10 ans),
   avec un taux de retour social net de la R&D publique et privée compris entre
   25 % et 35 % à maturité.

2. **Piliers de prospective technologique et de souveraineté** :
   Cinq piliers de prospective (IA & supercalcul souverain, énergie bas-carbone & SMR,
   biotechnologies & santé souveraine, matériaux critiques & recyclage circulaire,
   agroécologie & résilience hydrique/climat) documentés avec leurs jalons 2027-2036,
   leurs cibles observables, leurs signaux de renforcement, leurs signaux contraires
   et leurs verrous scientifiques.

3. **Chiffrage économique complet des stocks de résilience (ressources / emplois)** :
   Répond à la lacune P0 des « coûts économiques incomplets » : les stocks stratégiques
   (pétrole/carburants, composants/semi-conducteurs, pharmacie/médicaments, alimentation)
   ne sont plus présumés gratuits. Leurs coûts d'acquisition (CAPEX), leurs coûts de
   portage annuel (OPEX : logistique, maintenance, rotation, 3 à 5 %/an) et leurs
   modalités d'imputation budgétaire sont explicitement calculés et comparés aux
   pertes économiques évitées en cas de choc.

4. **Stress-testing prospectif croisé** :
   Évalue l'interaction entre l'effort d'innovation, les amortisseurs de stocks et
   les chocs macroéconomiques mondiaux (pétrole, blocus technologique, stagflation).

Règles méthodologiques :
------------------------
* Aucune probabilité d'invention ou de découverte n'est calculée.
* Les rendements de R&D sont des ordres de grandeur macroéconomiques sourcés,
  non des promesses déterministes de percées scientifiques.
* Les coûts des stocks sont des comptes ressources/emplois complets et vérifiables.

Usage :
    python3 -m simulateur.innovation_prospective              # rapport lisible
    python3 -m simulateur.innovation_prospective --horizon 10 # horizon 10 ans
    python3 -m simulateur.innovation_prospective --json       # donne brute JSON
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

# ==============================================================================
# SECTION 1 : MODÉLISATION DE LA DIFFUSION DE L'INNOVATION ET RENDEMENTS SOCIAUX
# ==============================================================================

@dataclass(frozen=True)
class ParametresDiffusionRND:
    """Paramètres structurels de la fonction de diffusion de l'innovation."""

    #: Délai incompressible d'amorçage (constitution des laboratoires, appels à projets, brevets)
    delai_latence_annees: float = 1.5
    #: Année du point d'inflexion où la diffusion industrielle s'accélère
    annee_inflexion: float = 4.0
    #: Pente de la courbe logistique de diffusion (vitesse d'adoption industrielle)
    pente_logistique: float = 0.85
    #: Taux de retour social net de la R&D à maturité (sourcé MESR / OCDE : ~25-35 %)
    taux_retour_social_max: float = 0.30
    #: Élasticité de la Productivité Globale des Facteurs (PGF) par tranche de 10 Md€ de R&D
    elasticite_pgf_annuelle: float = 0.0018

    def __post_init__(self) -> None:
        if not (0.0 <= self.delai_latence_annees <= 5.0):
            raise ValueError("Le délai de latence doit être compris entre 0 et 5 ans.")
        if not (1.0 <= self.annee_inflexion <= 10.0):
            raise ValueError("L'année d'inflexion doit être comprise entre 1 et 10 ans.")
        if not (0.1 <= self.pente_logistique <= 3.0):
            raise ValueError("La pente logistique doit être comprise entre 0.1 et 3.0.")
        if not (0.05 <= self.taux_retour_social_max <= 0.80):
            raise ValueError("Le taux de retour social doit être compris entre 5 % et 80 %.")
        if not (0.0001 <= self.elasticite_pgf_annuelle <= 0.01):
            raise ValueError("L'élasticité PGF doit être comprise entre 0.01 % et 1 %.")


def coefficient_diffusion_logistique(
    annee: int,
    parametres: ParametresDiffusionRND | None = None,
) -> float:
    """Calcule la fraction de diffusion effective d'une innovation à l'année t (0.0 à 1.0).

    Utilise une fonction logistique décalée du délai de latence incompressible :
    f(t) = 1 / (1 + exp(-pente * (t - latence - inflexion)))
    """
    if annee < 1:
        raise ValueError("L'année doit être un entier positif (>= 1).")
    p = parametres or ParametresDiffusionRND()
    temps_effectif = annee - p.delai_latence_annees
    if temps_effectif <= 0:
        return 0.0
    
    # Centre de la logistique recentré sur le temps effectif
    exposant = -p.pente_logistique * (temps_effectif - (p.annee_inflexion - p.delai_latence_annees))
    # Protection contre les dépassements numériques
    exposant_borne = max(-30.0, min(30.0, exposant))
    fraction = 1.0 / (1.0 + math.exp(exposant_borne))
    return round(fraction, 4)


def trajectoire_rendement_rnd(
    effort_annuel_mde: float,
    horizon: int = 5,
    parametres: ParametresDiffusionRND | None = None,
) -> list[dict[str, Any]]:
    """Calcule la trajectoire annuelle des retombées de la R&D sur un horizon de 5 ou 10 ans.

    Pour chaque année :
      - Effort d'investissement cumulé (Md€)
      - Coefficient de diffusion de l'innovation (0 à 100 %)
      - Gain net de productivité globale des facteurs (PGF, points)
      - Rendement social annuel généré (Md€)
      - Économies sectorielles induites (énergie, santé, numérique)
    """
    if effort_annuel_mde < 0:
        raise ValueError("L'effort annuel de R&D ne peut pas être négatif.")
    if horizon not in (5, 10):
        raise ValueError("L'horizon doit valoir 5 ou 10 ans.")

    p = parametres or ParametresDiffusionRND()
    trajectoire: list[dict[str, Any]] = []
    effort_cumule = 0.0

    for annee in range(1, horizon + 1):
        effort_cumule += effort_annuel_mde
        coef_diff = coefficient_diffusion_logistique(annee, p)

        # Gain de PGF progressif pondéré par l'effort cumulé
        gain_pgf_pts = round(
            (effort_cumule / 10.0) * p.elasticite_pgf_annuelle * coef_diff * 100.0, 4
        )
        
        # Rendement social brut annuel (gains de productivité, valeur ajoutée nouvelle)
        rendement_social_mde = round(
            effort_cumule * p.taux_retour_social_max * coef_diff, 2
        )

        # Économies sectorielles ventilées (climat/énergie 35%, santé 30%, industrie/numérique 35%)
        economies_energie_mde = round(rendement_social_mde * 0.35, 2)
        economies_sante_mde = round(rendement_social_mde * 0.30, 2)
        economies_industrie_numerique_mde = round(rendement_social_mde * 0.35, 2)

        trajectoire.append({
            "annee": annee,
            "effort_annuel_mde": round(effort_annuel_mde, 2),
            "effort_cumule_mde": round(effort_cumule, 2),
            "coefficient_diffusion_pct": round(coef_diff * 100.0, 2),
            "gain_pgf_points": gain_pgf_pts,
            "rendement_social_annuel_mde": rendement_social_mde,
            "economies_sectorielles": {
                "energie_climat_mde": economies_energie_mde,
                "sante_biotech_mde": economies_sante_mde,
                "industrie_numerique_mde": economies_industrie_numerique_mde,
            },
        })

    return trajectoire


# ==============================================================================
# SECTION 2 : PILIERS DE PROSPECTIVE TECHNOLOGIQUE ET BIOPHYSIQUE (2026-2036)
# ==============================================================================

@dataclass(frozen=True)
class PilierProspective:
    """Fiche de veille et de prospective sur un axe technologique et biophysique majeur."""

    cle: str
    titre: str
    domaine_associe: str
    maturite_initiale_trl: str  # e.g., "TRL 4-5", "TRL 6", "TRL 7-8"
    horizon_maturite_cible: int  # Année cible de maturité industrielle (2027-2036)
    objectifs_quantifies: dict[str, str]
    jalons_temporels: dict[int, str]
    signaux_qui_renforcent: str
    signaux_contraires: str
    verrous_scientifiques_et_industriels: str


#: Les cinq piliers de prospective technologique et biophysique structurant la R&D
PILIERS_PROSPECTIVE: tuple[PilierProspective, ...] = (
    PilierProspective(
        cle="ia_calcul_souverain",
        titre="IA, supercalculateurs et semi-conducteurs souverains",
        domaine_associe="numerique",
        maturite_initiale_trl="TRL 6 (démonstrateurs & supercalculateurs pétaflopiques)",
        horizon_maturite_cible=2031,
        objectifs_quantifies={
            "puissance_calcul_exaflopique": ">= 1,5 Exaflops souverains d'ici 2028 (Jules Verne)",
            "independance_modeles_ouverts": "Modèles ouverts européens entraînés sur infrastructures souveraines",
            "autonomie_puces_critiques": "Part de conception souveraine >= 30 % des besoins critiques",
        },
        jalons_temporels={
            2027: "Mise en service du supercalculateur Exascale Jules Verne à Bruyères-le-Châtel",
            2029: "Génération de modèles de fondation spécialisés recherche et services publics",
            2032: "Filière européenne de packaging avancé et puces spécialisées basse consommation",
            2036: "Calcul quantique hybride intégré aux centres nationaux de calcul intensif",
        },
        signaux_qui_renforcent="Commandes publiques massifiées, montée en cadence de fonderies européennes, adhésion communautaire aux modèles ouverts",
        signaux_contraires="Pénurie de composants avancés, dépendance accrue aux hyperscalers extra-européens, fuite des chercheurs",
        verrous_scientifiques_et_industriels="Efficience énergétique du calcul haute performance, maîtrise de la lithographie avancée et packaging 3D",
    ),
    PilierProspective(
        cle="energie_decarbonee_smr",
        titre="Énergie bas-carbone, SMR, flexibilité réseau et hydrogène vert",
        domaine_associe="energie_climat",
        maturite_initiale_trl="TRL 5-6 (conception détaillée Nuward / pilotes électrolyse)",
        horizon_maturite_cible=2033,
        objectifs_quantifies={
            "deploiement_smr": "Premier réacteur modulaire SMR tête de série opérationnel avant 2033",
            "capacite_stockage_stationnaire": "10 GW de flexibilité réseau et stockage décarboné d'ici 2035",
            "production_hydrogene_vert": "1 Mt/an d'hydrogène électrolytique pour l'industrie lourde d'ici 2032",
        },
        jalons_temporels={
            2027: "Finalisation du design de base des SMR de 300 MWe et choix des sites pilotes",
            2030: "Mise en chantier des premiers modules et couplage électrolyseurs haute température",
            2033: "Divergence et raccordement au réseau de la première unité SMR",
            2036: "Exploitation en série et export européen des modules standardisés",
        },
        signaux_qui_renforcent="Approbation par l'ASN des référentiels de sûreté SMR, baisse des coûts des électrolyseurs, contrats d'approvisionnement industriels fermes",
        signaux_contraires="Dérives de coûts et de calendrier sur les têtes de série, instabilité des chaînes de chaudronnerie nucléaire, renchérissement du coût du capital",
        verrous_scientifiques_et_industriels="Standardisation modulaire en usine, comportement des matériaux sous fort flux neutronique, pilotabilité fine de la flexibilité",
    ),
    PilierProspective(
        cle="biotech_sante_souveraine",
        titre="Biotechnologies médicales et relocalisation des principes actifs",
        domaine_associe="sante",
        maturite_initiale_trl="TRL 7 (usines pilotes & biothérapies de pointe)",
        horizon_maturite_cible=2030,
        objectifs_quantifies={
            "souverainete_principes_actifs_essentiels": "Production nationale de 80 % des 50 médicaments d'intérêt thérapeutique majeur d'ici 2030",
            "part_biomedicaments_produits_en_france": "Passage de 15 % (2024) à 40 % (2032) de la production des biomédicaments prescrits",
            "delai_reponse_pandemique": "Capacité de synthèse d'antigènes et vaccins ARNm sous 100 jours",
        },
        jalons_temporels={
            2027: "Ouverture des usines de chimie fine décarbonée pour le paracétamol, amoxicilline et anesthésiques",
            2029: "Pôles régionaux de bioproduction continue et banques de cellules souches",
            2032: "Autonomie complète sur les chaînes de principes actifs injectables d'urgence",
            2036: "Plateforme automatisée de thérapies ciblées personnalisées et vaccins thérapeutiques",
        },
        signaux_qui_renforcent="Accords pluriannuels de prix rémunérateurs pour la production locale, homologations accélérées par l'ANSM, contrats de filière pérennes",
        signaux_contraires="Pression continue sur les prix d'achat poussant à l'importation asiatique, tensions sur les intrants de biotechnologie",
        verrous_scientifiques_et_industriels="Procédés de chimie verte en flux continu, rendement de purification des bioréacteurs, stabilité thermique des ARNm",
    ),
    PilierProspective(
        cle="materiaux_critiques_recyclage",
        titre="Métaux critiques, substitution et recyclage circulaire",
        domaine_associe="industrie",
        maturite_initiale_trl="TRL 5-6 (pilotes hydrométallurgie & gisements miniers)",
        horizon_maturite_cible=2032,
        objectifs_quantifies={
            "taux_recyclage_batteries_et_aimants": "Taux de récupération >= 85 % pour lithium, cobalt, nickel et terres rares d'ici 2031",
            "autonomie_lithium_raffine": "Couverture de 50 % des besoins nationaux par le projet Emili et recyclage d'ici 2030",
            "substitution_terres_rares": "Réduction de 40 % de l'intensité en néodyme/dysprosium des moteurs électriques",
        },
        jalons_temporels={
            2027: "Entrée en service des premières giga-usines de recyclage de batteries en boucle fermée",
            2030: "Démarrage de l'extraction et du raffinage de lithium bas-carbone dans le Massif Central",
            2033: "Filière nationale de régénération des aimants permanents pour l'éolien et les transports",
            2036: "Taux de circularité supérieur à 60 % sur l'ensemble des 12 métaux stratégiques",
        },
        signaux_qui_renforcent="Règlement européen sur les matières premières critiques (CRMA) respecté, acceptabilité locale des projets miniers bas-impact, filières de collecte structurées",
        signaux_contraires="Volatilité extrême des cours mondiaux des minerais décourageant l'investissement local, recours aux solutions primaires extractives à bas coût",
        verrous_scientifiques_et_industriels="Rendement de séparation des terres rares lourdes, consommation d'eau et réactifs des procédés hydrométallurgiques",
    ),
    PilierProspective(
        cle="agroecologie_eau_climat",
        titre="Agroécologie, résilience hydrique et adaptation climatique",
        domaine_associe="agriculture",
        maturite_initiale_trl="TRL 7 (exploitations pilotes & génomique variétale)",
        horizon_maturite_cible=2032,
        objectifs_quantifies={
            "reduction_intrants_fossiles": "Baisse de 50 % des engrais azotés de synthèse via légumineuses et fertilisants décarbonés",
            "efficience_hydrique_agricole": "Économie de 30 % des prélèvements d'eau d'irrigation à rendement équivalent d'ici 2032",
            "autonomie_proteique": "Couverture à 70 % des besoins en protéines végétales animales et humaines",
        },
        jalons_temporels={
            2027: "Déploiement généralisé des capteurs d'humidité au sol et irrigation de précision goutte-à-goutte",
            2030: "Diffusion des variétés de céréales et légumineuses tolérantes aux stress hydriques et thermiques",
            2032: "Restructuration des paysages bocagers et retenues collinaires multi-usages d'infiltration",
            2036: "Modèle agroécologique résilient couvrant l'autonomie alimentaire nationale en situation de choc",
        },
        signaux_qui_renforcent="Valorisation économique des services écosystémiques, contractualisation longue avec les filières agroalimentaires, soutien massif à la transmission",
        signaux_contraires="Multiplication des sécheresses précoces détruisant les semis, concurrence d'importations non soumises aux mêmes normes environnementales",
        verrous_scientifiques_et_industriels="Mécanismes biophysiques de fixation symbiotique de l'azote à haute température, stockage de carbone dans les sols profonds",
    ),
)


# ==============================================================================
# SECTION 3 : CHIFFRAGE ÉCONOMIQUE COMPLET DES STOCKS DE RÉSILIENCE (P0)
# ==============================================================================

@dataclass(frozen=True)
class StockResilience:
    """Fiche de dimensionnement et de coût d'un stock stratégique national."""

    ressource: str
    secteur: str
    volume_mois: float  # Volume cible en mois de consommation nationale
    cout_acquisition_mde_par_mois: float  # Valeur marchande d'un mois de stock (Md€)
    taux_portage_annuel: float = 0.04  # Coût annuel de portage/maintenance (4 % / an)
    duree_amortissement_annees: int = 10  # Amortissement des infrastructures de stockage
    reconstitution_urgence_mde_par_mois: float = 0.0  # Surcoût en cas de reconstitution de crise

    def __post_init__(self) -> None:
        if not self.ressource.strip() or not self.secteur.strip():
            raise ValueError("La ressource et le secteur doivent être des chaînes non vides.")
        if not (0.1 <= self.volume_mois <= 24.0):
            raise ValueError("Le volume en mois doit être compris entre 0.1 et 24 mois.")
        if not (0.01 <= self.cout_acquisition_mde_par_mois <= 100.0):
            raise ValueError("Le coût d'acquisition doit être compris entre 0.01 et 100 Md€/mois.")
        if not (0.005 <= self.taux_portage_annuel <= 0.20):
            raise ValueError("Le taux de portage annuel doit être compris entre 0.5 % et 20 %.")
        if self.duree_amortissement_annees not in (5, 10, 20):
            raise ValueError("La durée d'amortissement doit être de 5, 10 ou 20 ans.")

    @property
    def valeur_stock_total_mde(self) -> float:
        """Valeur totale immobilisée du stock (Md€)."""
        return round(self.volume_mois * self.cout_acquisition_mde_par_mois, 3)

    @property
    def cout_portage_annuel_mde(self) -> float:
        """Coût annuel récurrent de gardiennage, maintenance, assurance et rotation (Md€)."""
        return round(self.valeur_stock_total_mde * self.taux_portage_annuel, 3)

    @property
    def amortissement_annuel_infrastructures_mde(self) -> float:
        """Charge annuelle d'amortissement des infrastructures spécialisées (cuves, hangars, silos)."""
        # Infrastructure évaluée forfaitairement à 15 % de la valeur du stock
        cout_infrastructure = self.valeur_stock_total_mde * 0.15
        return round(cout_infrastructure / self.duree_amortissement_annees, 3)


#: Panier de stocks stratégiques nationaux de référence (chiffré aux prix réels)
STOCKS_STRATEGIQUES_NATIONAUX: tuple[StockResilience, ...] = (
    StockResilience(
        ressource="Pétrole brut et carburants raffinés (obligation AIE/CPSSP 90 jours)",
        secteur="energie",
        volume_mois=3.0,
        cout_acquisition_mde_par_mois=4.5,  # 3 mois = 13,5 Md€ d'actifs pétroliers
        taux_portage_annuel=0.035,  # 3,5 % (rotation obligatoire des distillats)
        duree_amortissement_annees=10,
    ),
    StockResilience(
        ressource="Composants électroniques, semi-conducteurs et puces critiques",
        secteur="industrie_defense",
        volume_mois=6.0,
        cout_acquisition_mde_par_mois=1.2,  # 6 mois = 7,2 Md€
        taux_portage_annuel=0.045,  # 4,5 % (obsolescence technique et atmosphère contrôlée)
        duree_amortissement_annees=10,
    ),
    StockResilience(
        ressource="Médicaments d'intérêt thérapeutique majeur et anesthésiques d'urgence",
        secteur="sante",
        volume_mois=4.0,
        cout_acquisition_mde_par_mois=1.0,  # 4 mois = 4,0 Md€
        taux_portage_annuel=0.050,  # 5,0 % (rotation des péremptions pharmacologiques)
        duree_amortissement_annees=10,
    ),
    StockResilience(
        ressource="Céréales de réserve, semences et intrants alimentaires de sécurité",
        secteur="agriculture",
        volume_mois=2.5,
        cout_acquisition_mde_par_mois=0.8,  # 2,5 mois = 2,0 Md€
        taux_portage_annuel=0.040,  # 4,0 % (ventilation des silos et lutte contre les nuisibles)
        duree_amortissement_annees=10,
    ),
    StockResilience(
        ressource="Métaux critiques (lithium, cobalt, titane, terres rares)",
        secteur="industrie_transition",
        volume_mois=6.0,
        cout_acquisition_mde_par_mois=0.7,  # 6 mois = 4,2 Md€
        taux_portage_annuel=0.025,  # 2,5 % (faible dégradation physique, stockage passif)
        duree_amortissement_annees=10,
    ),
)


def compte_ressources_emplois_resilience(
    stocks: tuple[StockResilience, ...] = STOCKS_STRATEGIQUES_NATIONAUX,
    horizon_annees: int = 5,
) -> dict[str, Any]:
    """Établit le compte ressources/emplois complet et l'imputation budgétaire des stocks de résilience.

    Démontre que les réserves stratégiques ont un coût économique explicite, sans gratuité
    ni double comptage :
      - EMPLOIS : Coût d'acquisition du capital immobilisé + Coûts annuels de portage cumulés.
      - RESSOURCES : Financement par dotation d'investissement public amortie + Ligne budgétaire de fonctionnement.
    """
    if horizon_annees not in (5, 10):
        raise ValueError("L'horizon doit valoir 5 ou 10 ans.")

    valeur_totale_stocks = sum(s.valeur_stock_total_mde for s in stocks)
    portage_annuel_total = sum(s.cout_portage_annuel_mde for s in stocks)
    amortissement_annuel_total = sum(s.amortissement_annuel_infrastructures_mde for s in stocks)

    portage_cumule = round(portage_annuel_total * horizon_annees, 2)
    amortissement_cumule = round(amortissement_annuel_total * horizon_annees, 2)
    charge_annuelle_totale = round(portage_annuel_total + amortissement_annuel_total, 2)
    cout_global_sur_horizon = round(valeur_totale_stocks + portage_cumule + amortissement_cumule, 2)

    lignes_details = [
        {
            "ressource": s.ressource,
            "secteur": s.secteur,
            "volume_mois": s.volume_mois,
            "valeur_stock_total_mde": s.valeur_stock_total_mde,
            "cout_portage_annuel_mde": s.cout_portage_annuel_mde,
            "amortissement_annuel_mde": s.amortissement_annuel_infrastructures_mde,
            "charge_annuelle_mde": round(
                s.cout_portage_annuel_mde + s.amortissement_annuel_infrastructures_mde, 3
            ),
        }
        for s in stocks
    ]

    return {
        "horizon_annees": horizon_annees,
        "nombre_stocks_geres": len(stocks),
        "valeur_totale_capital_immobilise_mde": round(valeur_totale_stocks, 2),
        "cout_portage_annuel_total_mde": round(portage_annuel_total, 2),
        "amortissement_annuel_infrastructures_mde": round(amortissement_annuel_total, 2),
        "charge_budgetaire_annuelle_mde": charge_annuelle_totale,
        "charge_budgetaire_cumulee_horizon_mde": round(
            charge_annuelle_totale * horizon_annees, 2
        ),
        "cout_global_programme_mde": cout_global_sur_horizon,
        "imputation_comptable": {
            "section_investissement_capex": "Comptabilisé en immobilisation corporelle / actifs publics stratégiques",
            "section_fonctionnement_opex": "Charge récurrente de portage et logistique inscrite au budget de l'État",
            "neutralite_patrimoniale": "L'acquisition crée un actif réel équivalent à la dette d'acquisition",
        },
        "details_par_stock": lignes_details,
    }


# ==============================================================================
# SECTION 4 : STRESS-TESTING PROSPECTIF CROISÉ (INNOVATION x RÉSILIENCE x CHOCS)
# ==============================================================================

@dataclass(frozen=True)
class ScenarioChocProspectif:
    """Définition d'un scénario de choc prospectif combiné."""

    nom: str
    description: str
    hausse_petrole_usd: float
    perte_approvisionnement_composants_pct: float
    choc_taux_interets_bps: float
    duree_mois: int


SCENARIOS_CHOCS_PROSPECTIFS: dict[str, ScenarioChocProspectif] = {
    "choc_energetique_severe": ScenarioChocProspectif(
        nom="Choc énergétique et pétrolier sévère (Brent +50 $)",
        description="Fermeture partielle de détroits et flambée durable du baril à 130 $ pendant 12 mois.",
        hausse_petrole_usd=50.0,
        perte_approvisionnement_composants_pct=10.0,
        choc_taux_interets_bps=100.0,
        duree_mois=12,
    ),
    "blocus_composants_technologiques": ScenarioChocProspectif(
        nom="Rupture majeure des chaînes technologiques (Taïwan / semi-conducteurs)",
        description="Pénurie aiguë de composants électroniques avancés et arrêt de lignes industrielles.",
        hausse_petrole_usd=15.0,
        perte_approvisionnement_composants_pct=60.0,
        choc_taux_interets_bps=50.0,
        duree_mois=18,
    ),
    "stagflation_multi_theatres": ScenarioChocProspectif(
        nom="Stagflation géopolitique globale multi-théâtres",
        description="Conjonction d'un choc énergétique, de ruptures logistiques et d'un resserrement monétaire.",
        hausse_petrole_usd=40.0,
        perte_approvisionnement_composants_pct=40.0,
        choc_taux_interets_bps=150.0,
        duree_mois=24,
    ),
}


def stress_test_innovation_resilience(
    effort_rnd_annuel_mde: float = 5.0,
    avec_stocks_resilience: bool = True,
    cle_choc: str = "stagflation_multi_theatres",
    horizon_annees: int = 5,
) -> dict[str, Any]:
    """Exécute un stress-test prospectif comparant la vulnérabilité du système avec ou sans innovation et stocks.

    Compare 4 branches :
      1. Témoin vulnérable (sans R&D accrue, sans stocks renforcés)
      2. R&D seule (gains de productivité et d'efficience énergétique, mais sans stocks d'urgence)
      3. Stocks seuls (protection immédiate contre la pénurie, mais sans gains d'efficience à terme)
      4. Politique combinée R&D + Stocks (résilience systémique maximale)
    """
    if cle_choc not in SCENARIOS_CHOCS_PROSPECTIFS:
        raise ValueError(f"Scénario de choc inconnu : {cle_choc}")
    choc = SCENARIOS_CHOCS_PROSPECTIFS[cle_choc]

    # Dommages bruts annuels sans protection (en Md€ de PIB)
    dommages_bruts_annuels_pib_mde = (
        (choc.hausse_petrole_usd * 0.45)  # 1 $ de baril en plus coûte ~0,45 Md€ de facture énergétique nette
        + (choc.perte_approvisionnement_composants_pct * 0.60)  # Pénurie industrielle de composants
        + (choc.choc_taux_interets_bps * 0.12)  # Coût du refinancement de la dette publique
    )

    compte_stocks = compte_ressources_emplois_resilience(horizon_annees=horizon_annees)
    charge_annuelle_stocks = compte_stocks["charge_budgetaire_annuelle_mde"]

    trajectoire_rnd = trajectoire_rendement_rnd(effort_rnd_annuel_mde, horizon=horizon_annees)

    resultats_annuels: list[dict[str, Any]] = []

    perte_cumulee_temoin = 0.0
    perte_cumulee_rnd_seule = 0.0
    perte_cumulee_stocks_seuls = 0.0
    perte_cumulee_combinee = 0.0

    for annee in range(1, horizon_annees + 1):
        rnd_etape = trajectoire_rnd[annee - 1]
        gain_efficience_rnd = rnd_etape["rendement_social_annuel_mde"]

        # Facteur d'amortissement par les stocks physiques (évite ~65 % des arrêts de production)
        amortissement_stocks_mde = dommages_bruts_annuels_pib_mde * 0.65 if avec_stocks_resilience else 0.0

        # Pertes nettes selon les 4 branches
        perte_temoin = dommages_bruts_annuels_pib_mde
        perte_rnd = max(0.0, dommages_bruts_annuels_pib_mde - gain_efficience_rnd) + effort_rnd_annuel_mde
        perte_stocks = max(0.0, dommages_bruts_annuels_pib_mde - amortissement_stocks_mde) + charge_annuelle_stocks
        perte_combinee = max(
            0.0,
            dommages_bruts_annuels_pib_mde - amortissement_stocks_mde - gain_efficience_rnd
        ) + effort_rnd_annuel_mde + charge_annuelle_stocks

        perte_cumulee_temoin += perte_temoin
        perte_cumulee_rnd_seule += perte_rnd
        perte_cumulee_stocks_seuls += perte_stocks
        perte_cumulee_combinee += perte_combinee

        resultats_annuels.append({
            "annee": annee,
            "dommages_bruts_choc_mde": round(dommages_bruts_annuels_pib_mde, 2),
            "perte_nette_temoin_mde": round(perte_temoin, 2),
            "perte_nette_rnd_seule_mde": round(perte_rnd, 2),
            "perte_nette_stocks_seuls_mde": round(perte_stocks, 2),
            "perte_nette_combinee_mde": round(perte_combinee, 2),
            "economie_combinee_vs_temoin_mde": round(perte_temoin - perte_combinee, 2),
        })

    gain_cumule_combinaison = round(perte_cumulee_temoin - perte_cumulee_combinee, 2)
    ratio_cout_benefice = round(
        (perte_cumulee_temoin - perte_cumulee_combinee)
        / ((effort_rnd_annuel_mde * horizon_annees) + (charge_annuelle_stocks * horizon_annees)),
        2,
    )

    return {
        "choc": asdict(choc),
        "horizon_annees": horizon_annees,
        "effort_rnd_annuel_mde": effort_rnd_annuel_mde,
        "charge_annuelle_stocks_mde": charge_annuelle_stocks,
        "perte_cumulee_temoin_mde": round(perte_cumulee_temoin, 2),
        "perte_cumulee_rnd_seule_mde": round(perte_cumulee_rnd_seule, 2),
        "perte_cumulee_stocks_seuls_mde": round(perte_cumulee_stocks_seuls, 2),
        "perte_cumulee_combinee_mde": round(perte_cumulee_combinee, 2),
        "gain_net_cumule_mde": gain_cumule_combinaison,
        "ratio_cout_benefice_resilience": ratio_cout_benefice,
        "synthese_analytique": (
            f"Sous le scénario « {choc.nom} », la combinaison d'une politique de R&D active "
            f"({effort_rnd_annuel_mde} Md€/an) et de stocks stratégiques financés "
            f"({charge_annuelle_stocks} Md€/an) permet d'éviter {gain_cumule_combinaison} Md€ "
            f"de pertes économiques sur {horizon_annees} ans, soit un ratio de rendement "
            f"social et de protection de {ratio_cout_benefice} € préservé par euro investi."
        ),
        "trajectoire_annuelle": resultats_annuels,
    }


# ==============================================================================
# SECTION 5 : RAPPORT COMPLET ET LIGNE DE COMMANDE
# ==============================================================================

def rapport_prospective_innovation(
    depart: date | None = None,
    horizon: int = 5,
    effort_rnd_mde: float = 5.0,
) -> dict[str, Any]:
    """Génère le rapport consolidé de R&D, innovation et prospective."""
    date_depart = depart or date.today()
    if horizon not in (5, 10):
        raise ValueError("L'horizon doit valoir 5 ou 10 ans.")

    diffusion_rnd = trajectoire_rendement_rnd(effort_rnd_mde, horizon=horizon)
    compte_stocks = compte_ressources_emplois_resilience(horizon_annees=horizon)
    stress_test = stress_test_innovation_resilience(
        effort_rnd_annuel_mde=effort_rnd_mde,
        avec_stocks_resilience=True,
        cle_choc="stagflation_multi_theatres",
        horizon_annees=horizon,
    )

    return {
        "date_evaluation": date_depart.isoformat(),
        "horizon_annees": horizon,
        "effort_annuel_rnd_mde": effort_rnd_mde,
        "piliers_prospective": [asdict(p) for p in PILIERS_PROSPECTIVE],
        "diffusion_rnd": diffusion_rnd,
        "compte_stocks_resilience": compte_stocks,
        "stress_test_combinaison": stress_test,
        "avertissement": (
            "R&D et prospective systémique : les rendements de R&D modélisent une diffusion "
            "logistique standardisée et les coûts de stocks représentent un compte ressources/emplois "
            "complet. Aucune probabilité d'invention ou de découverte n'est postulée."
        ),
    }


def lignes_rapport(depart: date, horizon: int) -> list[str]:
    """Construit un affichage textuel soigné pour le terminal."""
    data = rapport_prospective_innovation(depart, horizon=horizon)
    out: list[str] = [
        f"=== RAPPORT R&D, INNOVATION & PROSPECTIVE (Horizon {horizon} ans — {depart.isoformat()}) ===",
        "",
        "## 1. Piliers de Prospective Technologique & Biophysique (2026-2036)",
    ]

    for p in PILIERS_PROSPECTIVE:
        out.append(f"  • [{p.cle}] {p.titre} (Cible {p.horizon_maturite_cible}, {p.maturite_initiale_trl})")
        out.append(f"    - Renforcerait : {p.signaux_qui_renforcent}")
        out.append(f"    - Écarterait   : {p.signaux_contraires}")

    out.append("")
    out.append("## 2. Compte Économique des Stocks de Résilience (Comptes complets, sans gratuité)")
    cs = data["compte_stocks_resilience"]
    out.append(f"  • Actifs immobilisés : {cs['valeur_totale_capital_immobilise_mde']} Md€")
    out.append(f"  • Charge budgétaire annuelle : {cs['charge_budgetaire_annuelle_mde']} Md€/an")
    out.append(f"  • Charge cumulée ({horizon} ans) : {cs['charge_budgetaire_cumulee_horizon_mde']} Md€")

    out.append("")
    out.append("## 3. Retombées de la R&D & Productivité Globale des Facteurs")
    for etape in data["diffusion_rnd"]:
        out.append(
            f"  • An {etape['annee']} : Diffusion {etape['coefficient_diffusion_pct']:.1f} % | "
            f"Gain PGF +{etape['gain_pgf_points']:.3f} pts | "
            f"Rendement social +{etape['rendement_social_annuel_mde']} Md€/an"
        )

    out.append("")
    out.append("## 4. Stress-Test Croisé (Stagflation Multi-Théâtres)")
    st = data["stress_test_combinaison"]
    out.append(f"  • Pertes cumulées sans protection : {st['perte_cumulee_temoin_mde']} Md€")
    out.append(f"  • Pertes avec R&D + Stocks : {st['perte_cumulee_combinee_mde']} Md€")
    out.append(f"  • Gain net préservé : {st['gain_net_cumule_mde']} Md€ (Ratio {st['ratio_cout_benefice_resilience']})")
    out.append(f"  • {st['synthese_analytique']}")

    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--depart", default=date.today().isoformat(),
                        help="Date d'évaluation (AAAA-MM-JJ)")
    parser.add_argument("--horizon", type=int, choices=(5, 10), default=5,
                        help="Horizon de simulation (5 ou 10 ans)")
    parser.add_argument("--rnd", type=float, default=5.0,
                        help="Effort annuel de R&D en Md€ (défaut 5.0)")
    parser.add_argument("--json", action="store_true", help="Sortie brute JSON")
    args = parser.parse_args(argv)

    try:
        depart = date.fromisoformat(args.depart)
    except ValueError:
        print(f"Date illisible : {args.depart!r} (attendu AAAA-MM-JJ)", file=sys.stderr)
        return 2

    if args.json:
        data = rapport_prospective_innovation(depart, horizon=args.horizon, effort_rnd_mde=args.rnd)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    for ligne in lignes_rapport(depart, args.horizon):
        print(ligne)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
