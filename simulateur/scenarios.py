"""
simulateur/scenarios.py — Catalogue des scénarios types de simulation sur 5 ans.
"""

from typing import List
from simulateur.model import DecisionPolitique


def get_scenario_mandature_5_ans() -> List[DecisionPolitique]:
    """
    Le scénario du Dossier de Mandature Globale (+60 Md€ en Année 5).
    Répartition graduelle et réaliste sur 5 exercices.
    """
    return [
        DecisionPolitique(
            annee=1,
            description="Année 1 : Urgence pouvoir d'achat, moralisation et premières recettes",
            recettes_fraude_ia_mde=0.0,
            conditionnement_aides_entreprises_mde=0.0,
            taxe_superprofits_rachats_mde=6.0,
            extension_ttf_mde=5.0,
            fusion_doublons_territoriaux_mde=0.0,
            commande_publique_massifiee_mde=0.0,
            extinction_niches_inefficaces_mde=4.0,
            fraude_sociale_criminelle_mde=0.0,
            baisse_tva_energie_5_5_mde=9.0,
            reforme_casier_b2=True,
            reforme_vote_blanc_invalidant=True,
            reforme_ric_souverain=True,
            reforme_fin_regimes_speciaux=True,
            reforme_anti_pantouflage_lobbys=True,
            delta_dotation_dgf_mde=0.0,
        ),
        DecisionPolitique(
            annee=2,
            description="Année 2 : Déploiement IA fraude et premières négociations commande publique",
            recettes_fraude_ia_mde=4.0,
            conditionnement_aides_entreprises_mde=0.0,
            taxe_superprofits_rachats_mde=6.0,
            extension_ttf_mde=5.0,
            fusion_doublons_territoriaux_mde=1.5,
            commande_publique_massifiee_mde=2.0,
            extinction_niches_inefficaces_mde=5.5,
            fraude_sociale_criminelle_mde=1.0,
            baisse_tva_energie_5_5_mde=9.0,
            reforme_non_cumul_mandats=True,
            delta_dotation_dgf_mde=0.0,
        ),
        DecisionPolitique(
            annee=3,
            description="Année 3 : Smart Clearing des aides (DSN) et convergence SI territoriaux",
            recettes_fraude_ia_mde=7.0,
            conditionnement_aides_entreprises_mde=7.0,
            taxe_superprofits_rachats_mde=6.0,
            extension_ttf_mde=5.0,
            fusion_doublons_territoriaux_mde=4.0,
            commande_publique_massifiee_mde=3.5,
            extinction_niches_inefficaces_mde=7.0,
            fraude_sociale_criminelle_mde=2.0,
            baisse_tva_energie_5_5_mde=9.0,
            delta_dotation_dgf_mde=0.0,
        ),
        DecisionPolitique(
            annee=4,
            description="Année 4 : Montée en puissance internationale DAC7/DAC8 et rationalisation foncière",
            recettes_fraude_ia_mde=9.0,
            conditionnement_aides_entreprises_mde=12.0,
            taxe_superprofits_rachats_mde=6.0,
            extension_ttf_mde=5.0,
            fusion_doublons_territoriaux_mde=6.5,
            commande_publique_massifiee_mde=5.0,
            extinction_niches_inefficaces_mde=7.0,
            fraude_sociale_criminelle_mde=2.5,
            baisse_tva_energie_5_5_mde=9.0,
            delta_dotation_dgf_mde=0.0,
        ),
        DecisionPolitique(
            annee=5,
            description="Année 5 : Régime de croisière stabilisé (+60 Md€ / an, déficit < 3 % PIB)",
            recettes_fraude_ia_mde=10.0,
            conditionnement_aides_entreprises_mde=15.0,
            taxe_superprofits_rachats_mde=6.0,
            extension_ttf_mde=5.0,
            fusion_doublons_territoriaux_mde=8.0,
            commande_publique_massifiee_mde=6.0,
            extinction_niches_inefficaces_mde=7.0,
            fraude_sociale_criminelle_mde=3.0,
            baisse_tva_energie_5_5_mde=9.0,
            delta_dotation_dgf_mde=0.0,
        ),
    ]


def get_scenario_statut_quo() -> List[DecisionPolitique]:
    """Scénario du Statut Quo : aucune réforme d'envergure, immobilisme."""
    return [
        DecisionPolitique(annee=i, description=f"Année {i} : Statut Quo (Immobilisme politique)")
        for i in range(1, 6)
    ]


def get_scenario_austerite_brutale() -> List[DecisionPolitique]:
    """Scénario d'austérité aveugle : coupes dans la DGF et dégradation des services."""
    return [
        DecisionPolitique(
            annee=i,
            description=f"Année {i} : Austérité brutale (-10 Md€ dotations DGF, coupes hôpitaux)",
            delta_dotation_dgf_mde=-8.0,
            fusion_doublons_territoriaux_mde=2.0,
            baisse_tva_energie_5_5_mde=0.0,
        )
        for i in range(1, 6)
    ]


def get_scenario_choc_mondial_stagflation() -> List[DecisionPolitique]:
    """
    Scénario de crise et de stress-test mondial :
    Choc pétrolier exogène (+30 $/bbl), dépréciation de l'euro (-0.08) et resserrement Fed (+75 bps).
    Permet de tester la robustesse des amortisseurs et des stabilisateurs du modèle.
    """
    return [
        DecisionPolitique(
            annee=1,
            description="Année 1 : Choc mondial d'offre (Pétrole 112.5 $/bbl, dépréciation EUR/USD, Fed +75 bps)",
            choc_petrole_brent_usd=30.0,
            choc_change_eur_usd=-0.08,
            choc_taux_fed_bps=75.0,
            baisse_tva_energie_5_5_mde=9.0,  # Bouclier d'urgence activé
            recettes_pilier2_ocde_mde=3.0,
            recettes_macf_carbone_mde=2.0,
            taxe_superprofits_rachats_mde=6.0,
            extension_ttf_mde=5.0,
        ),
        DecisionPolitique(
            annee=2,
            description="Année 2 : Persistance du choc mondial et montée en charge des recettes de régulation",
            choc_petrole_brent_usd=20.0,
            choc_change_eur_usd=-0.05,
            choc_taux_fed_bps=50.0,
            baisse_tva_energie_5_5_mde=9.0,
            recettes_fraude_ia_mde=5.0,
            conditionnement_aides_entreprises_mde=4.0,
            recettes_pilier2_ocde_mde=4.5,
            recettes_macf_carbone_mde=3.0,
            taxe_superprofits_rachats_mde=6.0,
            extension_ttf_mde=5.0,
        ),
        DecisionPolitique(
            annee=3,
            description="Année 3 : Stabilisation des marchés mondiaux et absorption par les réformes structurelles",
            choc_petrole_brent_usd=10.0,
            choc_change_eur_usd=-0.02,
            choc_taux_fed_bps=25.0,
            baisse_tva_energie_5_5_mde=9.0,
            recettes_fraude_ia_mde=8.0,
            conditionnement_aides_entreprises_mde=8.0,
            recettes_pilier2_ocde_mde=5.0,
            recettes_macf_carbone_mde=3.5,
            fusion_doublons_territoriaux_mde=5.0,
            commande_publique_massifiee_mde=4.0,
        ),
    ]
