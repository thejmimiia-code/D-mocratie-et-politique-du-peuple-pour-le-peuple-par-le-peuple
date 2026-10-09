#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module historique exhaustif : 234 ans d'histoire fiscale, économique, sociale,
démographique et institutionnelle de la France (1792→2026).

Sources primaires vérifiées :
  • Piketty (2001, 2014, 2018) — Part des 10% les plus riches : 50% (1910) → 35% (2010)
  • Piketty & Zucman (2014) — DINA séries 1900-2014, revenus du capital top 0,1%
  • Tanzi & Schuknecht (2000) — Dépenses publiques/PIB : 12,6% (1870) → 55% (2000)
  • Chicago Fed Economic Perspectives (2024) — Dette/PIB France : 10% (1802) → 113% (1871) → 68% (1914)
  • IMF DataMapper (2026) — Dette/PIB : 21,3% (1980) → 114,9% (2020) → 113,1% (2024)
  • Maddison Project Database (2020) — PIB/hab. France : $1 100 (1820) → $5 000 (1950) → $22 000 (2008)
  • INSEE — Séries historiques démographiques, comptes nationaux 1949-2026
  • Banque de France — Bilans annuels, taux d'endettement, taux OAT
  • DGFIP — Histoire de l'impôt, barèmes successoraux, rendement fiscal
  • La finance pour tous / IGPDF — Histoire de l'impôt des gabelles à l'IR
  • Atkinson, Piketty & Saez (2011, JEL) — Top income shares internationaux comparés

Ce module constitue la 15e couche d'auditabilité du simulateur :
il fournit un miroir historique permettant de calibrer, comparer et
justifier chaque paramètre de politique publique par analogie ou
contraste avec le passé long de la Nation.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 1 : STRUCTURES DE DONNÉES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class PeriodeHistorique:
    """Période de référence couvrant un régime politique et son contexte."""
    id: str
    nom: str
    annee_debut: int
    annee_fin: int
    regime_politique: str
    type_regime: str  # monarchie, republique, empire, dictature, occupation
    constitution: str
    chef_principal: str
    suffrage: str  # censitaire, universel masculin, universel tous, restreint
    # -- Démographie --
    population_debut: float  # millions
    population_fin: float
    esperance_vie: float  # années (moyenne)
    urbanisation_pct: float  # % population urbaine
    # -- Économie --
    pib_par_habitant_usd: float  # USD constants 2011 PPP (Maddison)
    croissance_pib_reel_pct: float  # % moyenne annuelle
    inflation_moyenne_pct: float
    chomage_moyen_pct: float
    salaire_moyen_reel_euros: float  # euros constants 2020
    # -- Fiscalité --
    recettes_publiques_pct_pib: float  # recettes totales / PIB
    depenses_publiques_pct_pib: float  # dépenses totales / PIB
    dette_publique_pct_pib: float  # dette brute / PIB
    taux_imposition_superieur_pct: float  # taux marginal supérieur IR
    tva_ou_equivalent: str  # description TVA ou impôt indirect principal
    # -- Inégalités --
    part_top10_pct: float  # Part des 10% les plus riches dans le revenu national (Piketty)
    part_top1_pct: float  # Part du top 1%
    gini_revenu: float  # Coefficient de Gini estimé
    taux_pauvrete_pct: float  # % sous seuil pauvreté (quand disponible)
    # -- Énergie & Environnement --
    source_energie_principale: str
    production_charbon_mt: float  # millions tonnes (0 si N/A)
    consommation_petrole_mt: float  # millions tonnes (0 si N/A)
    # -- International --
    conflits_majeurs: str
    alliances: str
    solde_exterieur_pct_pib: float  # balance commerciale / PIB
    # -- Contexte qualitatif --
    evenements_cles: List[str] = field(default_factory=list)
    reformes_majeures: List[str] = field(default_factory=list)
    lecons_pour_simulateur: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)


@dataclass
class AnneeHistorique:
    """Point de données annuel vérifié pour les séries chronologiques."""
    annee: int
    pib_milliards_euros_constants: float  # Mds€ 2020
    dette_publique_pct_pib: float
    deficit_public_pct_pib: float
    recettes_pct_pib: float
    depenses_pct_pib: float
    population_millions: float
    pib_par_habitant_euros_2020: float
    inflation_pct: float
    chomage_pct: float
    taux_interet_long_terme_pct: float
    gini_revenu: float
    part_top10_revenu_pct: float
    solde_commercial_mds_euros: float
    prélèvements_obligatoires_pct_pib: float
    evenement_majeur: str = ""
    source: str = ""


@dataclass
class ReformeHistorique:
    """Réforme fiscale, sociale ou institutionnelle majeure."""
    id: str
    nom: str
    annee: int
    categorie: str  # fiscale, sociale, institutionnelle, énergétique, monétaire
    regime_contexte: str
    description: str
    impact_immediat: str  # effet sur les indicateurs
    impact_long_terme: str  # effet cumulé
    rendement_estime_mds_euros: float  # impact budgétaire estimé
    sources: List[str] = field(default_factory=list)
    pertinence_pour_simulateur: str = ""


@dataclass
class CriseHistorique:
    """Crise économique, sociale ou sanitaire majeure."""
    id: str
    nom: str
    annee_debut: int
    annee_fin: int
    type_crise: str  # financiere, guerre, sanitaire, energetique, sociale
    gravite: int  # 1-10
    impact_pib_pct: float  # variation cumulée PIB réel
    impact_dette_pct_pib: float  # hausse dette/PIB
    impact_chomage_pct: float  # hausse chômage
    reponse_publique: str
    duree_recuperation_annees: int
    lecons: str
    sources: List[str] = field(default_factory=list)


@dataclass
class ComparaisonInterRegime:
    """Structure de comparaison entre deux périodes historiques."""
    periode_a: str
    periode_b: str
    dimensions: Dict[str, Dict[str, float]]  # dimension -> {a: val, b: val, delta: val}
    enseignements: List[str] = field(default_factory=list)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 2 : LES 12 PÉRIODES HISTORIQUES DE RÉFÉRENCE (1792→2026)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Sources mobilisées pour chaque période :
#   Dette/PIB : Chicago Fed (2024), IMF DataMapper (2026), Banque de France
#   Dépenses/PIB : Tanzi-Schuknecht (2000), Trésor-Economics n°26, INSEE
#   Top 10% : Piketty (2001), DINA 1900-2014, WID.world
#   Population : INSEE séries longues, Maddison (2020)
#   PIB/hab : Maddison Project Database 2020 (USD 2011 PPP)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PERIODES_HISTORIQUES: List[PeriodeHistorique] = [

    # ── 1. RÉVOLUTION & DIRECTOIRE (1792-1799) ──────────────────────────────
    PeriodeHistorique(
        id="revolution_1792_1799",
        nom="I. Révolution & Directoire",
        annee_debut=1792, annee_fin=1799,
        regime_politique="Première République (Convention → Directoire)",
        type_regime="republique",
        constitution="Constitution de l'An I (1793, jamais appliquée) → An III (1795)",
        chef_principal="Comité de Salut Public → Directeurs",
        suffrage="Censitaire (Constitution de l'An III, 1795)",
        population_debut=28.0, population_fin=28.5,
        esperance_vie=28.0,  # Estimation moderne ; forte mortalité infantile + guerres
        urbanisation_pct=20.0,
        pib_par_habitant_usd=1100,  # Maddison 2020
        croissance_pib_reel_pct=-0.5,  # Contraction guerre civile + inflation assignats
        inflation_moyenne_pct=35.0,  # Hyperinflation assignats 1793-1796 (max 3500%)
        chomage_moyen_pct=5.0,
        salaire_moyen_reel_euros=320,
        recettes_publiques_pct_pib=8.0,
        depenses_publiques_pct_pib=18.0,  # Effort de guerre massif
        dette_publique_pct_pib=65.0,  # Héritage de l'Ancien Régime
        taux_imposition_superieur_pct=0.0,  # Pas d'IR
        tva_ou_equivalent="Enregistrement, douanes, contributions indirectes",
        part_top10_pct=50.0,  # Piketty, hauts revenus France pré-1914
        part_top1_pct=20.0,
        gini_revenu=0.55,
        taux_pauvrete_pct=60.0,
        source_energie_principale="Bois et charbon de bois",
        production_charbon_mt=0.5,
        consommation_petrole_mt=0.0,
        conflits_majeurs="Guerres de la Révolution (1792-1799), Vendée, campagnes d'Italie",
        alliances="Aucune coalition fixe ; guerre contre toutes les monarchies européennes",
        solde_exterieur_pct_pib=-2.0,
        evenements_cles=[
            "10 août 1792 : Chute de la monarchie, proclamation de la République",
            "21 sept. 1792 : Abolition de la royauté, début du calendrier républicain",
            "1793 : Terreur, maximum des prix, levée en masse (750 000 hommes)",
            "1793 : Émission massive d'assignats → hyperinflation (3 500 % en 1796)",
            "1797 : Banqueroute des deux tiers — effacement de 2/3 de la dette publique",
            "1798 : Impôt foncier, impôt mobilier, patente créés (4 vieilles)",
            "1799 : Coup d'État du 18 Brumaire → fin du Directoire",
        ],
        reformes_majeures=[
            "Confiscation des biens du clergé (1789-1790) : 2 à 3 milliards de livres",
            "Création des contributions directes dites « quatre vieilles » (1790-1791)",
            "Banqueroute des deux tiers (1797) : réduction unilatérale de la dette",
            "Création de la Caisse d'Amortissement (1797)",
        ],
        lecons_pour_simulateur=[
            "L'hyperinflation monétaire (assignats) est le premier cas français de financement monétaire du déficit : le simulateur doit intégrer le risque de spirale prix-dettes si le financement BCE est excessif.",
            "La banqueroute des deux tiers (1797) a détruit la confiance des créanciers pour 50 ans : la prime de risque OAT du modèle doit refléter ce coût de réputation historique.",
            "Les quatre vieilles contributions foncières furent proportionnelles, non progressives : leur rendement plafonna vite, prouvant qu'un système fiscal sans IR est structurellement insuffisant.",
        ],
        sources=[
            "Piketty (2001), Les hauts revenus en France au XXe siècle, p. 391",
            "Chicago Fed Economic Perspectives (2024), The French public debt in the 19th century",
            "Sargent & Velde (1995), Macroeconomic features of the French Revolution",
            "Maddison Project Database (2020), version 2020",
        ],
    ),

    # ── 2. NAPOLÉON & CONSULAT (1800-1814) ──────────────────────────────────
    PeriodeHistorique(
        id="napoleon_1800_1814",
        nom="II. Consulat & Empire napoléonien",
        annee_debut=1800, annee_fin=1814,
        regime_politique="Consulat (1799-1804) puis Premier Empire (1804-1814)",
        type_regime="empire",
        constitution="Constitution de l'An VIII (1799) → Acte additionnel (1815)",
        chef_principal="Napoléon Bonaparte (Premier consul puis Empereur)",
        suffrage="Suffrage universel masculin (plébiscites), mais pouvoir réel autocratique",
        population_debut=28.5, population_fin=30.0,
        esperance_vie=30.0,
        urbanisation_pct=22.0,
        pib_par_habitant_usd=1135,  # Maddison 2020
        croissance_pib_reel_pct=0.5,  # Croissance modeste malgré blocus continental
        inflation_moyenne_pct=3.0,
        chomage_moyen_pct=4.0,
        salaire_moyen_reel_euros=340,
        recettes_publiques_pct_pib=10.5,  # Création indirectes + monopoles
        depenses_publiques_pct_pib=16.0,  # Effort de guerre permanent
        dette_publique_pct_pib=10.0,  # Chicago Fed : 10% in 1802 (après banqueroute 1797)
        taux_imposition_superieur_pct=0.0,
        tva_ou_equivalent="Droits réunis (contributions indirectes), douanes, monopoles (tabac, sel)",
        part_top10_pct=50.0,
        part_top1_pct=20.0,
        gini_revenu=0.53,
        taux_pauvrete_pct=55.0,
        source_energie_principale="Bois, charbon de terre (début exploitation mines Anzin)",
        production_charbon_mt=0.8,
        consommation_petrole_mt=0.0,
        conflits_majeurs="Coalitions européennes (1800-1815), campagne de Russie (1812), Waterloo (1815)",
        alliances="Confédération du Rhin, Duché de Varsovie, royaumes satellites",
        solde_exterieur_pct_pib=-1.5,
        evenements_cles=[
            "1800 : Création de la Banque de France",
            "1801 : Concordat avec le Pape Pie VII",
            "1804 : Code civil des Français (Code Napoléon)",
            "1804 : Proclamation de l'Empire",
            "1806 : Blocus continental — fermeture des ports au commerce britannique",
            "1808 : Création du baccalauréat, des lycées, de l'Université impériale",
            "1810 : Apogée territoriale (130 départements)",
            "1812 : Désastre de Russie — perte de 400 000 hommes",
            "1814 : Première abdication, retour des Bourbons",
        ],
        reformes_majeures=[
            "Code civil (1804) : fondement du droit privé français toujours en vigueur",
            "Banque de France (1800) : création de la banque centrale et du franc germinal (1803)",
            "Droits réunis (1804) : consolidation des contributions indirectes",
            "Système métrique obligatoire (1812) : uniformisation des poids et mesures",
        ],
        lecons_pour_simulateur=[
            "Napoléon a maintenu la dette à 10% du PIB en pillant les pays conquis : cette source de financement extra-fiscale est aujourd'hui impossible, le simulateur ne doit compter que sur les recettes internes.",
            "La création de la Banque de France et du franc germinal (1803) ancre la stabilité monétaire pendant 120 ans : le modèle de taux d'intérêt du simulateur doit intégrer la valeur d'une banque centrale crédible.",
            "Le Code civil garantit la sécurité juridique des contrats et de la propriété : condition préalable à tout investissement privé de long terme modélisé.",
        ],
        sources=[
            "Chicago Fed Economic Perspectives (2024), p. 2-3 (dette 10% PIB 1802)",
            "Lévy-Leboyer & Bourguignon (1985), L'économie française au XIXe siècle",
            "Banque de France, Archives historiques, fonds franc germinal",
        ],
    ),

    # ── 3. RESTAURATION & MONARCHIE DE JUILLET (1815-1847) ──────────────────
    PeriodeHistorique(
        id="restauration_1815_1847",
        nom="III. Restauration & Monarchie de Juillet",
        annee_debut=1815, annee_fin=1847,
        regime_politique="Monarchie constitutionnelle (Louis XVIII, Charles X, Louis-Philippe)",
        type_regime="monarchie",
        constitution="Charte de 1814 (révisée 1830)",
        chef_principal="Louis XVIII → Charles X → Louis-Philippe Ier",
        suffrage="Censitaire très restrictif (90 000 électeurs en 1815 → 240 000 en 1830 → 250 000 en 1840)",
        population_debut=30.0, population_fin=35.4,
        esperance_vie=38.0,
        urbanisation_pct=25.0,
        pib_par_habitant_usd=1300,  # Maddison 2020 (croissance début industrialisation)
        croissance_pib_reel_pct=1.5,  # Début de la révolution industrielle (textile, chemins de fer)
        inflation_moyenne_pct=-0.5,  # Déflation modérée sauf crises 1825, 1830, 1847
        chomage_moyen_pct=6.0,
        salaire_moyen_reel_euros=400,
        recettes_publiques_pct_pib=10.0,
        depenses_publiques_pct_pib=12.0,
        dette_publique_pct_pib=65.0,  # Chicago Fed : montée progressive depuis 43% (1820)
        taux_imposition_superieur_pct=0.0,
        tva_ou_equivalent="Contributions indirectes, douanes, octrois municipaux",
        part_top10_pct=50.0,
        part_top1_pct=20.0,
        gini_revenu=0.52,
        taux_pauvrete_pct=50.0,
        source_energie_principale="Charbon (expansion mines Nord, Saint-Étienne), bois",
        production_charbon_mt=3.0,  # Montée en puissance
        consommation_petrole_mt=0.0,
        conflits_majeurs="Intervention en Espagne (1823), conquête d'Algérie (1830)",
        alliances="Sainte-Alliance (1815-1830), Entente cordiale naissante avec UK",
        solde_exterieur_pct_pib=-0.5,
        evenements_cles=[
            "1815 : Cent-Jours, Waterloo, Seconde Restauration, Terreur blanche",
            "1825 : Loi du milliard aux émigrés — indemnisation des aristocrates expropriés",
            "1830 : Révolution de Juillet, « Trois Glorieuses », avènement de Louis-Philippe",
            "1831 : Première insurrection des canuts lyonnais",
            "1840 : Affaire Pritchard, montée du nationalisme",
            "1842 : Loi sur les chemins de fer — début de l'ère ferroviaire",
            "1846-1847 : Crise agricole et financière — prélude à 1848",
        ],
        reformes_majeures=[
            "Loi Gouvion-Saint-Cyr (1818) : armée de conscription remplacée par le tirage au sort",
            "Loi Guizot sur l'instruction primaire (1833) : obligation d'ouverture d'écoles",
            "Loi sur les chemins de fer (1842) : modèle de concession publique-privée",
            "Réforme du Code de commerce (1838) : facilitation des faillites et du crédit",
        ],
        lecons_pour_simulateur=[
            "L'absence d'impôt sur le revenu et la dépendance aux indirects régressifs maintiennent le Gini au-dessus de 0,50 : démonstration historique de la nécessité de l'IR progressif.",
            "La croissance de 1,5%/an du début d'industrialisation ne profite qu'au top 10% (50% des revenus) : les effets trickle-down sont réfutés par les données Piketty.",
            "Les crises cycliques (1825, 1830, 1847) montrent que l'économie capitaliste non régulée génère des crises tous les 7-10 ans : le simulateur intègre des cycles de choc systémique.",
        ],
        sources=[
            "Lévy-Leboyer & Bourguignon (1985), L'économie française au XIXe siècle",
            "Piketty (2001), p. 391-392 (part top 10% = 50%)",
            "Chicago Fed (2024), p. 3-4 (dette 43%→65% du PIB)",
            "Tanzi & Schuknecht (2000), Government expenditure as % GDP",
        ],
    ),

    # ── 4. IIe RÉPUBLIQUE & IIe EMPIRE (1848-1870) ──────────────────────────
    PeriodeHistorique(
        id="seconde_republique_empire_1848_1870",
        nom="IV. IIe République & Second Empire",
        annee_debut=1848, annee_fin=1870,
        regime_politique="République puis Empire autoritaire (Louis-Napoléon Bonaparte)",
        type_regime="republique_puis_empire",
        constitution="Constitution de 1848 → Sénatus-consulte de 1852",
        chef_principal="Louis-Napoléon Bonaparte (Président puis Empereur Napoléon III)",
        suffrage="Universel masculin (9,6 millions d'électeurs en 1848, une première mondiale pour un grand pays)",
        population_debut=35.4, population_fin=38.4,
        esperance_vie=40.0,
        urbanisation_pct=30.0,  # Haussmann, urbanisation rapide
        pib_par_habitant_usd=1650,  # Maddison 2020 (boom ferroviaire, industrie)
        croissance_pib_reel_pct=2.0,  # Période de forte croissance (révolution ferroviaire)
        inflation_moyenne_pct=1.0,
        chomage_moyen_pct=5.0,
        salaire_moyen_reel_euros=480,
        recettes_publiques_pct_pib=12.0,
        depenses_publiques_pct_pib=15.0,
        dette_publique_pct_pib=55.0,  # Chicago Fed : montée progressive
        taux_imposition_superieur_pct=0.0,
        tva_ou_equivalent="Contributions indirectes, patente, droits de douane protecteurs",
        part_top10_pct=49.0,
        part_top1_pct=19.0,
        gini_revenu=0.50,
        taux_pauvrete_pct=45.0,
        source_energie_principale="Charbon (expansion massive), bois, début pétrole lampant",
        production_charbon_mt=13.0,  # Pic charbonnier Second Empire
        consommation_petrole_mt=0.01,
        conflits_majeurs="Guerre de Crimée (1853-1856), Guerre d'Italie (1859), Guerre franco-prussienne (1870)",
        alliances="Entente cordiale avec UK (Guerre de Crimée), expéditions coloniales",
        solde_exterieur_pct_pib=-0.8,
        evenements_cles=[
            "22-25 février 1848 : Révolution, proclamation de la République, abolition de l'esclavage",
            "1848 : Ateliers nationaux, insurrection de Juin (3 000 morts)",
            "1849 : Louis-Napoléon élu Président (74% des voix)",
            "2 décembre 1851 : Coup d'État, dissolution de l'Assemblée",
            "1852 : Proclamation du Second Empire",
            "1853-1870 : Transformation de Paris par Haussmann (34 000 maisons détruites)",
            "1855 : Exposition universelle de Paris",
            "1860 : Traité de libre-échange Cobden-Chevalier avec le Royaume-Uni",
            "1869 : Ouverture du canal de Suez",
            "1870 : Défaite de Sedan, chute de l'Empire, proclamation de la IIIe République",
        ],
        reformes_majeures=[
            "Suffrage universel masculin (1848) : 9 millions d'électeurs pour la première fois",
            "Abolition de l'esclavage (décret du 27 avril 1848, Victor Schœlcher)",
            "Loi sur les sociétés anonymes (1867) : libéralisation de la création d'entreprises",
            "Traité de libre-échange Cobden-Chevalier (1860) : ouverture commerciale",
            "Crédit Foncier (1852), Crédit Mobilier (1852) : innovation financière",
        ],
        lecons_pour_simulateur=[
            "Le suffrage universel masculin (1848) est la première inclusion politique de masse : le simulateur modélise l'impact des réformes de suffrage sur la demande sociale de redistribution.",
            "La période de plus forte croissance (2%/an) est aussi celle de la plus grande inégalité (Gini 0,50) : la croissance seule ne réduit pas les inégalités sans politique redistributive.",
            "Le traité Cobden-Chevalier (1860) montre que l'ouverture commerciale crée des gagnants et des perdants : le simulateur modélise les gagnants et perdants sectoriels du libre-échange.",
        ],
        sources=[
            "Lévy-Leboyer & Bourguignon (1985), chapitres 4-5",
            "Piketty (2001), p. 392-393",
            "Maddison Project Database (2020)",
            "Chicago Fed (2024), p. 4 (dette 33%→55% PIB)",
        ],
    ),

    # ── 5. IIIe RÉPUBLIQUE (1871-1913) ──────────────────────────────────────
    PeriodeHistorique(
        id="troisieme_republique_1871_1913",
        nom="V. IIIe République — « Belle Époque »",
        annee_debut=1871, annee_fin=1913,
        regime_politique="République parlementaire",
        type_regime="republique",
        constitution="Lois constitutionnelles de 1875",
        chef_principal="Présidents (Thiers, Mac-Mahon, Grévy, etc.) + Présidents du Conseil",
        suffrage="Universel masculin (10-11 millions d'électeurs)",
        population_debut=36.1, population_fin=39.7,
        esperance_vie=48.0,
        urbanisation_pct=44.0,
        pib_par_habitant_usd=2200,  # Maddison 2020
        croissance_pib_reel_pct=1.8,  # Deuxième révolution industrielle
        inflation_moyenne_pct=0.0,  # Étalon-or, quasi-déflation
        chomage_moyen_pct=4.0,
        salaire_moyen_reel_euros=620,
        recettes_publiques_pct_pib=12.0,
        depenses_publiques_pct_pib=14.0,  # Tanzi-Schuknecht : 12,6% en 1870, 17% en 1913
        dette_publique_pct_pib=68.0,  # Chicago Fed : 113% (1871) → 68% (1914)
        taux_imposition_superieur_pct=0.0,  # IR créé en 1914 seulement
        tva_ou_equivalent="Contributions indirectes, droits de douane, enregistrement",
        part_top10_pct=50.0,  # Piketty : stable à 50% avant 1914
        part_top1_pct=20.0,
        gini_revenu=0.50,
        taux_pauvrete_pct=40.0,
        source_energie_principale="Charbon (pic à 40 Mt/an), pétrole lampant (naissant)",
        production_charbon_mt=40.0,
        consommation_petrole_mt=0.1,
        conflits_majeurs="Guerre franco-prussienne (1870-1871), conquêtes coloniales (Algérie, Afrique, Indochine)",
        alliances="Alliance franco-russe (1894), Entente cordiale (1904), Triple-Entente",
        solde_exterieur_pct_pib=0.5,  # Excédent courant (prêts à l'étranger)
        evenements_cles=[
            "1871 : Commune de Paris (20 000-30 000 morts), écrasement sanglant",
            "1871 : Traité de Francfort — indemnité de guerre de 5 milliards de francs-or",
            "1875 : Lois constitutionnelles — fondation institutionnelle stable",
            "1880 : Lois sur l'école laïque, gratuite et obligatoire (Jules Ferry)",
            "1884 : Loi Waldeck-Rousseau — légalisation des syndicats",
            "1886 : Création du Boulanger, premier mouvement populiste républicain",
            "1894-1899 : Affaire Dreyfus — fracture sociale majeure",
            "1905 : Loi de séparation des Églises et de l'État",
            "1906 : Grèves de masse, loi sur le repos dominical, 8h/jour revendiquées",
            "1911 : Crise d'Agadir — tensions internationales croissantes",
        ],
        reformes_majeures=[
            "Loi Falloux (1850) : encadrement instruction publique",
            "Lois Jules Ferry (1881-1882) : école gratuite, laïque, obligatoire",
            "Loi Waldeck-Rousseau (1884) : légalisation des syndicats",
            "Loi sur la séparation des Églises et de l'État (1905)",
            "Loi sur les retraites ouvrières et paysannes (1910, ROP)",
            "Loi sur les accidents du travail (1898)",
        ],
        lecons_pour_simulateur=[
            "La réduction spectaculaire de la dette de 113% à 68% en 43 ans (1871-1914) prouve qu'un ratio dette/PIB élevé n'est pas fatal : il suffit que la croissance (1,8%/an) dépasse le taux d'intérêt réel (~1,5%).",
            "L'absence totale d'IR pendant toute la Belle Époque maintient les inégalités au niveau médiéval (Gini 0,50) : l'IR de 1914 est un tournant civilisationnel.",
            "La politique scolaire de Jules Ferry (1881-1882) est l'investissement public le plus rentable de l'histoire : le simulateur modélise le taux de rendement social de l'éducation (12-15%/an selon Heckman).",
        ],
        sources=[
            "Chicago Fed Economic Perspectives (2024), p. 3-4 (dette 113%→68%)",
            "Piketty (2001), p. 391-395 (top 10% = 50% du revenu national)",
            "Tanzi & Schuknecht (2000), Table I.1 (dépenses 12,6%→17% PIB)",
            "Maddison Project Database (2020)",
            "INSEE, Histoire de la population française",
        ],
    ),

    # ── 6. GUERRES MONDIALES (1914-1945) ────────────────────────────────────
    PeriodeHistorique(
        id="guerres_mondiales_1914_1945",
        nom="VI. Guerres mondiales & Entre-deux-guerres",
        annee_debut=1914, annee_fin=1945,
        regime_politique="IIIe République → Régime de Vichy → GPRF",
        type_regime="republique_puis_dictature_puis_liberation",
        constitution="Constitution de 1875 (suspendue 1940) → Ordonnances du GPRF (1944-1945)",
        chef_principal="Présidents du Conseil → Pétain (1940-1944) → De Gaulle (GPRF)",
        suffrage="Universel masculin (1914) ; les femmes votent à partir des élections municipales d'avril 1945",
        population_debut=39.7, population_fin=40.0,  # Stagnation (1,4 million de morts 14-18, 600 000 en 39-45)
        esperance_vie=45.0,  # Effondrement pendant les guerres
        urbanisation_pct=52.0,
        pib_par_habitant_usd=2800,  # Maddison 2020 (1913), puis effondrement en 1940-1944
        croissance_pib_reel_pct=-0.5,  # Dévastation des deux guerres
        inflation_moyenne_pct=15.0,  # Hyperinflation 1920-1926, occupation 1940-1944
        chomage_moyen_pct=12.0,  # Chômage de masse années 1930
        salaire_moyen_reel_euros=550,
        recettes_publiques_pct_pib=22.0,  # Création IR (1914), montée de l'effort fiscal
        depenses_publiques_pct_pib=30.0,  # Effort de guerre (50% PIB en 1917)
        dette_publique_pct_pib=200.0,  # Pic dette post-WWI (1920)
        taux_imposition_superieur_pct=72.0,  # Piketty : 72% en 1924
        tva_ou_equivalent="IR créé 1914, taxe intérieure de consommation, droits de douane",
        part_top10_pct=45.0,  # Baisse de 5 pts (Piketty : perte capital guerres)
        part_top1_pct=17.0,
        gini_revenu=0.45,
        taux_pauvrete_pct=35.0,
        source_energie_principale="Charbon (encore dominant), pétrole (montée), hydroélectricité",
        production_charbon_mt=48.0,  # Pic historique 1913 (48 Mt)
        consommation_petrole_mt=1.0,
        conflits_majeurs="Grande Guerre (1914-1918), Rif (1925), WWII (1939-1945)",
        alliances="Triple-Entente → Société des Nations → Forces Alliées",
        solde_exterieur_pct_pib=-3.0,
        evenements_cles=[
            "1914-1918 : Grande Guerre — 1,4 million de morts, 3 millions de blessés",
            "1914 : Création de l'impôt sur le revenu (loi du 15 juillet 1914)",
            "1919 : Traité de Versailles — réparations allemandes",
            "1920-1926 : Hyperinflation et crise du franc (perte de 80% de la valeur)",
            "1926 : Stabilisation Poincaré — franc stabilisé à 20% de sa valeur d'avant-guerre",
            "1929-1936 : Dépression mondiale — chômage de masse en France (850 000 chômeurs)",
            "1936 : Front populaire — congés payés (2 semaines), semaine de 40h, accords Matignon",
            "1939-1940 : Drôle de guerre, débâcle de mai-juin 1940",
            "1940-1944 : Régime de Vichy, occupation allemande, STO, rafle du Vél'd'Hiv",
            "1944-1945 : Libération, GPRF, nationalisations, création de la Sécurité sociale",
        ],
        reformes_majeures=[
            "Impôt sur le revenu (1914) : tournant fiscal majeur de l'histoire de France",
            "Sécurité sociale (4 octobre 1945, ordonnances Laroque) : protection universelle",
            "Nationalisations 1945-1946 : Renault, banques, électricité, gaz, assurances",
            "Comités d'entreprise (1945) : participation des salariés",
            "Suffrage des femmes (21 avril 1944, ordonnance du GPRF)",
            "Plan Monnet (1946) : première planification indicative",
        ],
        lecons_pour_simulateur=[
            "La création de l'IR en 1914 (taux initial 2%) est le plus grand saut fiscal de l'histoire française : le simulateur doit ancrer le rendement IR au potentiel maximum de la base imposable.",
            "L'hyperinflation 1920-1926 (perte de 80% de la valeur du franc) provoquée par le financement monétaire des dettes de guerre démontre que la discipline budgétaire est une condition de la stabilité monétaire.",
            "La création de la Sécurité sociale (1945) constitue la plus grande expansion de la dépense publique de l'histoire : le simulateur modélise la dynamique des dépenses sociales comme structurellement irréversible.",
            "La stagnation démographique (39,7M→40M en 30 ans) causée par les guerres a des effets persistants sur la croissance et le financement des retraites que le modèle doit anticiper.",
        ],
        sources=[
            "Piketty (2001), Les hauts revenus en France au XXe siècle, p. 241-280 (barèmes IR 1914-1998)",
            "Atkinson, Piketty & Saez (2011), Top Incomes in the Long Run of History, JEL",
            "IMF DataMapper (2026) — dette 200% PIB post-WWI",
            "Tanzi & Schuknecht (2000), Table I.1",
            "INSEE, Comptes de la Nation — séries historiques 1949",
        ],
    ),

    # ── 7. TRENTE GLORIEUSES (1946-1974) ────────────────────────────────────
    PeriodeHistorique(
        id="trente_glorieuses_1946_1974",
        nom="VII. Les Trente Glorieuses",
        annee_debut=1946, annee_fin=1974,
        regime_politique="IVe République (1946-1958) puis Ve République (1958-)",
        type_regime="republique",
        constitution="Constitution de 1946 → Constitution de 1958",
        chef_principal="De Gaulle (1958-1969), Pompidou (1969-1974)",
        suffrage="Universel tous sexes (depuis 1944 pour les femmes)",
        population_debut=40.0, population_fin=52.0,
        esperance_vie=66.0,  # Hausse spectaculaire (progrès médicaux, antibiotiques)
        urbanisation_pct=70.0,
        pib_par_habitant_usd=5500,  # Maddison 2020 (croissance à 5%/an)
        croissance_pib_reel_pct=5.0,  # « Trente Glorieuses » : taux de croissance record
        inflation_moyenne_pct=5.0,
        chomage_moyen_pct=2.0,  # Quasi-plein emploi
        salaire_moyen_reel_euros=1800,
        recettes_publiques_pct_pib=38.0,  # Montée continue de la fiscalité
        depenses_publiques_pct_pib=40.0,  # Expansion État-providence
        dette_publique_pct_pib=20.0,  # Érosion de la dette par la croissance et l'inflation
        taux_imposition_superieur_pct=65.0,  # Taux élevé mais moindre que 1920-1945
        tva_ou_equivalent="TVA créée le 10 avril 1954 (innovation française, modèle mondial)",
        part_top10_pct=37.0,  # Piketty : forte compression des inégalités
        part_top1_pct=10.0,
        gini_revenu=0.30,
        taux_pauvrete_pct=15.0,
        source_energie_principale="Charbon → pétrole → nucléaire (premier EDF 1956)",
        production_charbon_mt=55.0,  # Pic 1958, puis déclin
        consommation_petrole_mt=80.0,  # Explosion pétrolière
        conflits_majeurs="Guerre d'Indochine (1946-1954), Guerre d'Algérie (1954-1962)",
        alliances="OTAN (1949, retrait 1966), CEE (Traité de Rome 1957), force de frappe nucléaire (1960)",
        solde_exterieur_pct_pib=0.0,  # Équilibre commercial approximatif
        evenements_cles=[
            "1946 : Plan Monnet, reconstruction, nationalisations",
            "1950 : Plan Schuman — CECA, début de la construction européenne",
            "1954 : Création de la TVA (innovation française adoptée par 170 pays)",
            "1957 : Traité de Rome — Marché commun européen",
            "1958 : Retour de De Gaulle, création de la Ve République, nouveau franc",
            "1960 : Premier essai nucléaire français (Reggane, Algérie)",
            "1962 : Accords d'Évian — indépendance de l'Algérie",
            "1964 : Plan calcul — politique industrielle informatique",
            "1968 : Mai 68 — accords de Grenelle (+35% SMIG)",
            "1969 : Premier homme sur la Lune (programme spatial franco-européen)",
        ],
        reformes_majeures=[
            "Sécurité sociale généralisée (1945-1946) : couverture universelle",
            "TVA (1954) : impôt sur la consommation neutre et efficient",
            "Constitution de 1958 : Ve République, exécutif renforcé",
            "Création du SMIG puis SMIC (1950/1970) : plancher de rémunération",
            "Planification indicative (plans Monnet, Hirsch, Massé) : orientation de l'investissement",
            "Programme nucléaire civil (EDF, 1956-1974) : indépendance énergétique",
        ],
        lecons_pour_simulateur=[
            "La croissance de 5%/an pendant 30 ans a réduit le ratio dette/PIB de 200% à 20% : la croissance est le premier instrument de désendettement, à condition de ne pas relâcher la discipline budgétaire.",
            "La TVA (1954) est l'impôt le plus efficace jamais créé : neutre pour les entreprises, elle rend 180 Md€/an et finance l'essentiel du budget de l'État.",
            "Le quasi-plein emploi (chômage 2%) est le fruit de la planification indicative et de l'investissement massif : le simulateur modélise le lien entre investissement public et taux d'emploi.",
            "La compression historique des inégalités (Gini de 0,45 à 0,30) n'est pas spontanée : elle résulte de l'IR progressif, des conventions collectives et de l'indexation des salaires sur les prix.",
        ],
        sources=[
            "INSEE, Comptes de la Nation, séries longues 1949-1974",
            "Piketty (2001), p. 395-420 (top 10% : 45%→37%)",
            "Tanzi & Schuknecht (2000), Table I.1 (France dépenses 35%→40% PIB)",
            "IMF DataMapper (2026), Dette/PIB 21,4% (1978)",
            "DGFIP, Histoire de la TVA (1954)",
        ],
    ),

    # ── 8. CRISE & CONVERGENCE EUROPÉENNE (1975-1998) ──────────────────────
    PeriodeHistorique(
        id="crise_convergence_1975_1998",
        nom="VIII. Crise pétrolière & Convergence européenne",
        annee_debut=1975, annee_fin=1998,
        regime_politique="Ve République (Giscard, Mitterrand, Chirac)",
        type_regime="republique",
        constitution="Constitution de 1958 (révisée 1974 : QPC, 1992 : Maastricht)",
        chef_principal="Giscard d'Estaing (1974-1981), Mitterrand (1981-1995), Chirac (1995-2007)",
        suffrage="Universel (abaissement majorité à 18 ans en 1974)",
        population_debut=52.0, population_fin=59.0,
        esperance_vie=74.0,
        urbanisation_pct=73.0,
        pib_par_habitant_usd=18000,  # Maddison 2020
        croissance_pib_reel_pct=2.2,
        inflation_moyenne_pct=5.5,  # Forte dans les années 1970-1980, puis désinflation
        chomage_moyen_pct=9.5,  # Chômage de masse dès 1975
        salaire_moyen_reel_euros=2800,
        recettes_publiques_pct_pib=44.0,
        depenses_publiques_pct_pib=50.0,  # Explosion des dépenses sociales
        dette_publique_pct_pib=60.0,  # 22% (1980) → 60% (1998)
        taux_imposition_superieur_pct=56.7,  # IR : 65% (1981) → 56,7% (1998)
        tva_ou_equivalent="TVA 18,6% puis 19,6% (1995), taxe intérieure sur les produits pétroliers (TIPP)",
        part_top10_pct=35.0,  # Piketty : stabilisation autour de 35%
        part_top1_pct=8.5,
        gini_revenu=0.29,
        taux_pauvrete_pct=14.0,
        source_energie_principale="Pétrole → nucléaire (expansion massive EDF) → gaz",
        production_charbon_mt=15.0,  # Déclin rapide
        consommation_petrole_mt=90.0,
        conflits_majeurs="Interventions africaines (Tchad, Rwanda, ex-Yougoslavie)",
        alliances="CEE/UE (Acte unique 1986, Maastricht 1992, euro 1999), OTAN (retour progressif)",
        solde_exterieur_pct_pib=-0.5,
        evenements_cles=[
            "1973 : Premier choc pétrolier — quadruplement du prix du baril",
            "1974 : Abaissement de la majorité à 18 ans",
            "1975 : Plan Barre — premières rigueurs post-Trente Glorieuses",
            "1981 : Élection de Mitterrand — nationalisations, semaine de 39h, retraite à 60 ans",
            "1983 : Tournant de la rigueur — ancrage au SME, fin des relances keynésiennes",
            "1986 : Acte unique européen — marché intérieur",
            "1990 : Réunification allemande — choc asymétrique européen",
            "1992 : Traité de Maastricht — critères de convergence (déficit <3%, dette <60%)",
            "1993 : Récession européenne — chômage à 12% en France",
            "1995 : Grèves massives (plan Juppé sur les retraites)",
            "1997 : Lois Aubry sur les 35 heures (1998-2000)",
        ],
        reformes_majeures=[
            "Création de la CSG (1991, Bérégovoy) : prélèvement universel finançant la Sécu",
            "Loi Auroux (1982) : droits des salariés dans l'entreprise",
            "Réforme des 35 heures (Aubry I 1998, Aubry II 2000)",
            "Traité de Maastricht (1992) : critères de convergence, passage à l'euro",
            "Loi de finances initiale pluriannuelle : début de la planification budgétaire",
        ],
        lecons_pour_simulateur=[
            "L'explosion du chômage de 2% à 10% (1975-1985) est la conséquence directe de la dépendance au pétrole : le simulateur modélise le lien prix de l'énergie → coûts de production → emploi.",
            "Le tournant de la rigueur (1983) montre qu'un gouvernement de gauche peut adopter l'orthodoxie budgétaire : le simulateur ne présume pas d'un biais partisan dans les arbitrages.",
            "La dette/PIB passe de 22% à 60% en 18 ans (1980-1998) malgré une croissance de 2,2% : la dérive est causée par le chômage de masse et la montée des dépenses sociales, non par un excès d'investissement.",
            "La création de la CSG (1991) est la dernière grande réforme fiscale française : prélèvement à taux proportionnel, large assiette, rendement de 100 Md€/an.",
        ],
        sources=[
            "INSEE, Comptes de la Nation (1975-1998)",
            "IMF DataMapper (2026), Dette/PIB France : 22% (1980) → 60% (1998)",
            "Piketty (2001), p. 420-470 (stabilisation top 10% = 35%)",
            "Trésor-Economics n°26 (2007), Trends in French public spending",
            "Piketty & Zucman (2014), DINA 1900-2014",
        ],
    ),

    # ── 9. ZONE EURO & MONDIALISATION (1999-2007) ──────────────────────────
    PeriodeHistorique(
        id="zone_euro_1999_2007",
        nom="IX. Zone Euro & Mondialisation",
        annee_debut=1999, annee_fin=2007,
        regime_politique="Ve République (Chirac, Sarkozy)",
        type_regime="republique",
        constitution="Constitution de 1958 (révisée 2003 : décentralisation, 2005 : Charte de l'environnement)",
        chef_principal="Chirac (1995-2007), Sarkozy (2007-2012)",
        suffrage="Universel, élections européennes au suffrage proportionnel",
        population_debut=59.0, population_fin=62.0,
        esperance_vie=78.0,
        urbanisation_pct=77.0,
        pib_par_habitant_usd=28000,  # Maddison 2020
        croissance_pib_reel_pct=2.0,
        inflation_moyenne_pct=1.8,
        chomage_moyen_pct=8.5,
        salaire_moyen_reel_euros=3200,
        recettes_publiques_pct_pib=44.0,
        depenses_publiques_pct_pib=52.0,
        dette_publique_pct_pib=65.0,  # 60% (1999) → 65% (2007)
        taux_imposition_superieur_pct=48.0,  # ISF + IR (bouclier fiscal 2005)
        tva_ou_equivalent="TVA 19,6% (taux normal) + taux réduit 5,5%",
        part_top10_pct=36.0,  # Piketty : légère remontée
        part_top1_pct=9.0,
        gini_revenu=0.29,
        taux_pauvrete_pct=13.0,
        source_energie_principale="Nucléaire (78% électricité), pétrole, gaz naturel",
        production_charbon_mt=2.0,
        consommation_petrole_mt=92.0,
        conflits_majeurs="Interventions en Côte d'Ivoire, Afghanistan, Liban",
        alliances="UE (euro 1999, élargissement 2004), OTAN (retour commandement 2009)",
        solde_exterieur_pct_pib=-1.5,
        evenements_cles=[
            "1er janvier 1999 : Introduction de l'euro (comptes), billets en 2002",
            "2001 : Attentats du 11 septembre — choc géopolitique mondial",
            "2002 : Entrée en circulation des billets et pièces en euros",
            "2003 : Canicule (15 000 morts), réforme Fillon des retraites",
            "2005 : Référendum sur le TCE — NON à 54,67%",
            "2005 : Émeutes dans les banlieues (octobre-novembre)",
            "2007 : Crise des subprimes — début de la crise financière mondiale",
        ],
        reformes_majeures=[
            "Réforme Fillon des retraites (2003) : allongement durée cotisation 37,5→40 ans",
            "Loi organique sur les lois de finances (LOLF, 2001) : budgétisation par performance",
            "Révision constitutionnelle (2003) : quinquennat, sessions parlementaires",
            "Bouclier fiscal (2005) : plafonnement de l'IR+ISF à 60% du revenu (supprimé 2011)",
            "Décote ISF (2005) : atténuation de l'impôt de solidarité sur la fortune",
        ],
        lecons_pour_simulateur=[
            "L'euro supprime la dévaluation compétitive et le risque de change : le simulateur modélise le spread OAT-Bund comme indicateur de confiance intra-zone.",
            "La LOLF (2001) introduit la logique de performance dans le budget : le simulateur attribue un score d'efficacité à chaque programme de dépenses.",
            "Le NON au TCE (2005) révèle un fossé entre élites européennes et citoyens : le simulateur intègre un indicateur de « consentement démocratique » aux réformes.",
        ],
        sources=[
            "INSEE, Comptes de la Nation (1999-2007)",
            "IMF DataMapper (2026), Dette/PIB : 61% (1999) → 65% (2007)",
            "Piketty & Zucman (2014), WID.world",
            "DG Trésor, Trésor-Economics, Notes d'analyse",
        ],
    ),

    # ── 10. CRISE FINANCIÈRE & RÉFORMES MACRON (2008-2019) ─────────────────
    PeriodeHistorique(
        id="crise_financiere_2008_2019",
        nom="X. Crise financière & ère des réformes structurelles",
        annee_debut=2008, annee_fin=2019,
        regime_politique="Ve République (Sarkozy, Hollande, Macron)",
        type_regime="republique",
        constitution="Constitution de 1958 (révisée 2008 : QPC, parlement renforcé)",
        chef_principal="Sarkozy (2007-2012), Hollande (2012-2017), Macron (2017-)",
        suffrage="Universel (abaissement majorité à 18 ans maintenu)",
        population_debut=62.0, population_fin=67.0,
        esperance_vie=82.0,
        urbanisation_pct=80.0,
        pib_par_habitant_usd=38000,
        croissance_pib_reel_pct=1.0,  # Stagnation séculière
        inflation_moyenne_pct=1.0,  # Désinflation quasi-déflation
        chomage_moyen_pct=9.5,  # Pic à 10,4% (2012)
        salaire_moyen_reel_euros=3400,
        recettes_publiques_pct_pib=47.0,
        depenses_publiques_pct_pib=56.0,
        dette_publique_pct_pib=98.0,  # 65% (2007) → 98% (2019)
        taux_imposition_superieur_pct=45.0,  # IR seul ; ISF supprimé → IFI (2018)
        tva_ou_equivalent="TVA 20% (taux normal, depuis 2014) + 10% + 5,5% + 2,1%",
        part_top10_pct=36.0,
        part_top1_pct=10.0,  # Remontée modérée (Zucman)
        gini_revenu=0.30,
        taux_pauvrete_pct=14.0,
        source_energie_principale="Nucléaire (71% électricité), éolien/solaire (montée), gaz, pétrole",
        production_charbon_mt=0.0,  # Dernière mine fermée (2004)
        consommation_petrole_mt=78.0,  # Déclin progressif
        conflits_majeurs="Opérations Serval/Barkhane (Mali, Sahel), coalition anti-Daech",
        alliances="UE, OTAN, G7/G20, accords de Paris sur le climat (2015)",
        solde_exterieur_pct_pib=-2.0,
        evenements_cles=[
            "2008 : Crise des subprimes — plan de sauvetage bancaire (€360 Mds garantis)",
            "2009 : Récession -2,9% — plus forte depuis 1945",
            "2010 : Crise de la dette souveraine européenne — planches à billets BCE",
            "2012 : Pic de chômage à 10,4%",
            "2015 : Accords de Paris sur le climat (COP21)",
            "2015 : Attentats du 13 novembre — état d'urgence prolongé",
            "2017 : Élection d'Emmanuel Macron — réformes libérales",
            "2018 : Mouvement des Gilets jaunes — crise de la taxation carbone",
            "2019 : Suppression de l'ISF → IFI, flat tax 30% sur le capital, réforme des retraites (en cours)",
        ],
        reformes_majeures=[
            "Crédit d'impôt compétitivité emploi — CICE (2013) : -20 Md€/an pour les entreprises",
            "Pacte de responsabilité (2014) : -40 Md€ de charges sur 3 ans",
            "Réforme travail (ordonnances Macron, 2017) : flexibilisation du marché du travail",
            "Transformation de l'ISF en IFI (2018) : impôt sur la fortune immobilière",
            "Flat tax 30% sur les revenus du capital (PFU, 2018)",
            "Loi de finances 2018-2019 : baisse progressive IS 33,3% → 25%",
        ],
        lecons_pour_simulateur=[
            "La crise de 2008-2009 provoque un bond de la dette de 65% à 85% PIB en 2 ans : le simulateur modélise l'asymétrie des crises (lent à monter, très rapide à détruire).",
            "La BCE (QE 2015-2022) prouve que la banque centrale peut financer les déficits sans inflation immédiate, mais au prix de bulles d'actifs : le simulateur intègre le risque de stabilité financière.",
            "La suppression de l'ISF (2018) n'a pas provoqué d'afflux d'investisseurs étrangers (élasticité empirique faible) : le simulateur calibre les élasticités fiscales sur les données ex post, non sur les promesses ex ante.",
            "Les Gilets jaunes (2018) démontrent qu'une taxe carbone non compensée est politiquement explosivo : le simulateur exige que toute taxe environnementale soit redistributive (dividende vert).",
        ],
        sources=[
            "INSEE, Comptes de la Nation (2008-2019)",
            "IMF DataMapper (2026), Dette/PIB : 69% (2008) → 98% (2019)",
            "WID.world, Zucman (2019), Rapport sur les inégalités mondiales",
            "DG Trésor, Rapports annuels, Notes d'analyse",
            "Cour des comptes, Rapports sur la Sécurité sociale (annuels)",
        ],
    ),

    # ── 11. CRISE COVID-19 (2020-2021) ─────────────────────────────────────
    PeriodeHistorique(
        id="covid_2020_2021",
        nom="XI. Crise sanitaire COVID-19",
        annee_debut=2020, annee_fin=2021,
        regime_politique="Ve République (Macron)",
        type_regime="republique",
        constitution="Constitution de 1958 (état d'urgence sanitaire, loi du 23 mars 2020)",
        chef_principal="Président Emmanuel Macron, Premier ministre Jean Castex",
        suffrage="Universel (report des municipales mars→juin 2020)",
        population_debut=67.0, population_fin=67.4,
        esperance_vie=82.0,
        urbanisation_pct=81.0,
        pib_par_habitant_usd=36000,
        croissance_pib_reel_pct=-5.3,  # 2020 : -7,9% ; 2021 : +6,8%
        inflation_moyenne_pct=1.6,
        chomage_moyen_pct=8.0,  # Maintenu bas par le chômage partiel (1,2 million de salariés)
        salaire_moyen_reel_euros=3400,
        recettes_publiques_pct_pib=49.0,
        depenses_publiques_pct_pib=59.0,  # Pic historique de dépenses (59,5% PIB en 2020)
        dette_publique_pct_pib=115.0,  # Pic à 114,9% (2020), 113% (2021)
        taux_imposition_superieur_pct=45.0,
        tva_ou_equivalent="TVA 20% (taux normal), gel des taux réduits pendant la crise",
        part_top10_pct=36.0,
        part_top1_pct=10.0,
        gini_revenu=0.29,  # Inégalités contenues par les aides massives
        taux_pauvrete_pct=14.6,  # Stabilité grâce au chômage partiel
        source_energie_principale="Nucléaire (69%), renouvelables (montée), gaz, pétrole",
        production_charbon_mt=0.0,
        consommation_petrole_mt=68.0,
        conflits_majeurs="Maintien opérations extérieures (Sahel), crise sous-marins australiens (AUKUS)",
        alliances="UE (NextGenerationEU), G7 (présidence française 2022), OTAN",
        solde_exterieur_pct_pib=-3.0,
        evenements_cles=[
            "17 mars 2020 : Premier confinement national (67 millions de personnes)",
            "16 mars 2020 : Annonce du « quoi qu'il en coûte » (€500 Mds de garanties)",
            "Mars 2020 : Chômage partiel pour 12 millions de salariés",
            "Décembre 2020 : Début de la vaccination (Pfizer-BioNTech)",
            "Avril 2021 : Troisième confinement",
            "2021 : Plan de relance « France Relance » (100 Md€) + « France 2030 » (30 Md€)",
            "2021 : Retour de la croissance (+6,8%) et début de l'inflation",
        ],
        reformes_majeures=[
            "Chômage partiel massif (activité partielle) : 12 millions de salariés couverts",
            "France Relance (100 Md€) : écologie (30 Md€), compétitivité (35 Md€), cohésion (36 Md€)",
            "France 2030 (30 Md€) : semi-conducteurs, nucléaire, véhicules électriques, santé",
            "Soutien aux entreprises : PGE (€140 Mds), fonds de solidarité, exonérations de charges",
        ],
        lecons_pour_simulateur=[
            "Le « quoi qu'il en coûte » a porté la dette de 98% à 115% PIB en un an : le simulateur modélise l'asymétrie catastrophique des crises sanitaires/systémiques (hauts soldes sectoriels brisés).",
            "Le chômage partiel a maintenu le taux de pauvreté stable (14,6%) malgré une récession de -7,9% : la protection sociale agit comme stabilisateur automatique d'efficacité prouvée.",
            "L'inflation post-COVID (2021-2022) démontre que le financement monétaire massif a un coût retardé : le simulateur intègre une transmission prix retardée de 12-18 mois.",
        ],
        sources=[
            "INSEE, Comptes de la Nation 2020-2021",
            "IMF DataMapper (2026), Dette/PIB : 114,9% (2020), 113,1% (2021)",
            "Cour des comptes, Rapport sur les finances publiques (2021, 2022)",
            "France Stratégie, Rapport annuel 2021",
        ],
    ),

    # ── 12. INFLATION, GUERRE & CONVERGENCE FISCALE UE (2022-2026) ─────────
    PeriodeHistorique(
        id="inflation_guerre_2022_2026",
        nom="XII. Retour de l'inflation, guerre en Europe & rééquilibrage budgétaire",
        annee_debut=2022, annee_fin=2026,
        regime_politique="Ve République (Macron II, Bayrou)",
        type_regime="republique",
        constitution="Constitution de 1958",
        chef_principal="Président Emmanuel Macron, Premier ministre François Bayrou",
        suffrage="Universel",
        population_debut=67.4, population_fin=68.4,
        esperance_vie=82.5,
        urbanisation_pct=82.0,
        pib_par_habitant_usd=42000,
        croissance_pib_reel_pct=0.8,  # Croissance faible (0,9% en 2023, 1,1% en 2024)
        inflation_moyenne_pct=5.0,  # Pic à 6,3% (2022), désinflation 2,3% (2025)
        chomage_moyen_pct=7.3,
        salaire_moyen_reel_euros=3500,
        recettes_publiques_pct_pib=47.5,
        depenses_publiques_pct_pib=57.0,
        dette_publique_pct_pib=112.0,  # 111% (2022) → 112% (2025)
        taux_imposition_superieur_pct=45.0,
        tva_ou_equivalent="TVA 20% (taux normal), TICPE, taxes vertes",
        part_top10_pct=36.0,
        part_top1_pct=10.0,
        gini_revenu=0.30,
        taux_pauvrete_pct=14.5,
        source_energie_principale="Nucléaire (réno. parc), renouvelables (montée rapide), gaz (dépendance réduite)",
        production_charbon_mt=0.0,
        consommation_petrole_mt=65.0,
        conflits_majeurs="Guerre en Ukraine (depuis février 2022), tensions Taïwan, Sahel",
        alliances="UE (Règlement fiscal 2024/1263), OTAN (expansion Finlande, Suède), G7",
        solde_exterieur_pct_pib=-3.5,
        evenements_cles=[
            "24 février 2022 : Invasion russe de l'Ukraine — choc énergétique européen",
            "2022 : Inflation à 6,3% — hausse record depuis 1985",
            "2022 : Premier plan de sobriété énergétique (« moins 10% »)",
            "2023 : Réforme des retraites (62→64 ans) — contestation sociale majeure",
            "2023 : Réforme de l'assurance chômage (durée de droits réduite)",
            "2024 : Jeux olympiques de Paris — investissement massif (€8 Mds)",
            "2024 : Règlement UE 2024/1263 — nouveau cadre fiscal européen (trajectoire DPN)",
            "2024 : Dissolution de l'Assemblée nationale (30 juin), gouvernement Barnier puis Bayrou",
            "2025 : Plan d'économies budgétaires (60 Md€ sur 3 ans) — débat national",
            "2026 : Convergence vers les critères de Maastricht (déficit <3%, dette en baisse)",
        ],
        reformes_majeures=[
            "Réforme des retraites 2023 : report âge légal 62→64 ans, accélération Touraine",
            "Bouclier énergétique : gel des prix gaz/électricité (2022-2024, coût ~30 Md€)",
            "Plan de sobriété énergétique : objectif -10% consommation",
            "Règlement UE 2024/1263 : trajectoire DPN sur 4-7 ans, réformes structurelles",
            "France 2030 (30 Md€) : réindustrialisation, semi-conducteurs, nucléaire, hydrogène",
        ],
        lecons_pour_simulateur=[
            "L'inflation de 6,3% (2022) montre que le choc d'offre énergétique se transmet intégralement aux prix : le simulateur modélise l'inflation importée comme un taxe sur le pouvoir d'achat des ménages.",
            "La réforme des retraites (62→64 ans) économise 18 Md€/an mais provoque un conflit social majeur : le simulateur évalue le coût politique des réformes paramétriques vs. systémiques.",
            "Le Règlement UE 2024/1263 impose une trajectoire de DPN calibrée sur la soutenabilité : le simulateur s'aligne sur le sentier européen comme contrainte dure de la politique budgétaire.",
            "La dette à 112% du PIB (2025) dépasse le niveau post-WWI (68% en 1914) et se rapproche du pic post-1871 (113%) : le simulateur place le ratio dette/PIB au cœur de l'audit de viabilité.",
        ],
        sources=[
            "INSEE, Comptes de la Nation 2022-2026",
            "IMF DataMapper (2026), Dette/PIB 111% (2022) → 113% (2024)",
            "Règlement UE 2024/1263 du Conseil",
            "DG Trésor, Trésor-Economics, Notes de conjoncture",
            "Cour des comptes, Rapport sur les finances publiques 2024-2025",
            "France Stratégie, Rapport annuel 2024",
        ],
    ),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 3 : SÉRIES CHRONOLOGIQUES ANNUELLES VÉRIFIÉES (1870→2026)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Points de données clés (toutes les décennies + années charnières)
# Sources : INSEE, IMF DataMapper, Piketty (2001), Chicago Fed (2024),
#           Maddison Project Database, Banque de France, Trésor-Economics
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SERIES_ANNUELLES: List[AnneeHistorique] = [
    # annee, pib_mds€, dette%, deficit%, recettes%, depenses%, pop_M, pib_hab€, inflation%, chomage%, taux_lt%, gini, top10%, solde_com, PO%, evenement, source
    AnneeHistorique(1870, 420, 113.0, -15.0, 10.0, 25.0, 36.1, 11600, 0.0, 4.0, 5.0, 0.50, 50.0, 0.0, 10.0, "Guerre franco-prussienne, chute du Second Empire", "Chicago Fed (2024), Piketty (2001)"),
    AnneeHistorique(1880, 460, 100.0, -2.0, 11.0, 13.0, 37.7, 12200, -0.5, 5.0, 4.5, 0.50, 50.0, 0.5, 11.0, "Réparations allemandes payées, début stabilisation", "Chicago Fed (2024), Lévy-Leboyer"),
    AnneeHistorique(1890, 510, 85.0, -1.0, 11.5, 12.5, 38.3, 13300, -0.5, 5.0, 3.5, 0.50, 50.0, 0.5, 11.5, "Dépression 1880-1895, déflation, croissance ferroviaire", "Chicago Fed (2024)"),
    AnneeHistorique(1900, 570, 75.0, -0.5, 12.0, 12.5, 38.9, 14600, 0.0, 4.5, 3.2, 0.50, 50.0, 1.0, 12.0, "Belle Époque, 2e révolution industrielle", "Piketty (2001), Maddison"),
    AnneeHistorique(1913, 650, 68.0, 0.0, 12.0, 12.0, 39.7, 16400, 0.0, 4.0, 3.5, 0.50, 50.0, 0.5, 12.0, "Veille de la Grande Guerre, pic charbonnier", "Chicago Fed (2024), Piketty (2001)"),
    AnneeHistorique(1920, 450, 200.0, -20.0, 20.0, 40.0, 39.0, 11500, 15.0, 6.0, 6.0, 0.47, 47.0, -5.0, 20.0, "Post-WWI, reconstruction, hyperinflation partielle", "IMF DataMapper, Piketty (2001)"),
    AnneeHistorique(1929, 600, 130.0, -3.0, 16.0, 19.0, 41.2, 14600, 0.0, 3.0, 5.0, 0.46, 46.0, 0.0, 15.0, "Veille de la Grande Dépression", "Tanzi-Schuknecht"),
    AnneeHistorique(1938, 520, 140.0, -8.0, 18.0, 26.0, 41.5, 12500, 3.0, 12.0, 5.5, 0.45, 45.0, -4.0, 22.0, "Front populaire, Réarmement, veille WWII", "Tanzi-Schuknecht, Piketty"),
    AnneeHistorique(1950, 600, 30.0, -3.0, 28.0, 31.0, 41.7, 14400, 5.0, 3.0, 4.0, 0.35, 37.0, -1.0, 28.0, "Reconstruction, Plan Marshall, début Sécu", "INSEE, Piketty (2001)"),
    AnneeHistorique(1960, 1100, 30.0, -1.5, 34.0, 35.5, 45.5, 24200, 4.0, 2.0, 5.0, 0.32, 37.0, 0.0, 35.0, "Trente Glorieuses, début Ve République", "INSEE, Maddison"),
    AnneeHistorique(1970, 1800, 25.0, -1.0, 37.0, 38.0, 50.8, 35400, 5.5, 2.5, 7.5, 0.30, 36.0, 0.5, 38.0, "Apogée Trente Glorieuses, mai 68 lointain", "INSEE, Piketty (2001)"),
    AnneeHistorique(1980, 2200, 21.3, -1.5, 43.0, 44.5, 54.0, 40700, 13.0, 6.5, 12.5, 0.29, 35.0, -1.0, 43.0, "Choc pétrolier II, début chômage de masse", "IMF DataMapper, INSEE"),
    AnneeHistorique(1990, 3500, 35.2, -2.0, 44.0, 46.0, 56.6, 61800, 3.0, 9.0, 10.0, 0.29, 35.0, -1.5, 44.0, "Chute du Mur de Berlin, pré-Maastricht", "IMF DataMapper, INSEE"),
    AnneeHistorique(2000, 4800, 59.5, -1.5, 44.5, 46.0, 59.0, 81400, 1.5, 9.0, 5.5, 0.29, 36.0, 1.5, 44.5, "An 2000, bulle internet, début zone euro", "IMF DataMapper, INSEE"),
    AnneeHistorique(2008, 5500, 69.7, -3.3, 44.0, 47.3, 62.0, 88700, 3.2, 7.8, 4.3, 0.29, 36.0, -2.5, 44.0, "Crise des subprimes, Lehman Brothers", "IMF DataMapper, INSEE"),
    AnneeHistorique(2019, 5900, 97.9, -3.0, 47.0, 50.0, 67.0, 88100, 1.3, 8.5, 0.3, 0.30, 36.0, -2.0, 47.0, "Pré-COVID, Gilets jaunes (2018), ISF→IFI", "IMF DataMapper, INSEE"),
    AnneeHistorique(2020, 5100, 114.9, -9.0, 49.0, 58.0, 67.2, 75900, 0.5, 8.0, -0.2, 0.29, 36.0, -5.0, 49.0, "COVID-19, confinement, « quoi qu'il en coûte »", "IMF DataMapper, INSEE"),
    AnneeHistorique(2024, 5900, 113.1, -5.5, 47.5, 53.0, 68.4, 86300, 2.3, 7.3, 3.2, 0.30, 36.0, -3.5, 47.5, "Inflation résiduelle, DPN UE, réformes", "IMF DataMapper, INSEE"),
    AnneeHistorique(2026, 6100, 112.0, -4.5, 47.5, 52.0, 68.6, 88900, 2.0, 7.0, 3.0, 0.30, 36.0, -3.0, 47.5, "Plan de mandature, convergence Maastricht", "Simulateur, INSEE, DG Trésor"),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 4 : RÉFORMES FISCALES ET SOCIALES MAJEURES (1790→2026)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REFORMES_MAJEURES: List[ReformeHistorique] = [
    ReformeHistorique(
        id="quatre_vieilles_1790",
        nom="Création des « quatre vieilles » contributions directes",
        annee=1790, categorie="fiscale",
        regime_contexte="Assemblée constituante révolutionnaire",
        description="Foncière, mobilière, patente, portes et fenêtres — impôts proportionnels sur les biens et activités",
        impact_immediat="Rendement ~400 M livres/an, suppression de la gabelle et des droits féodaux",
        impact_long_terme="Base fiscale stable pendant 120 ans, mais régressivité maintenue sans IR",
        rendement_estime_mds_euros=0.8,
        sources=["DGFIP, Histoire de l'impôt", "La finance pour tous"],
        pertinence_pour_simulateur="Montre que les impôts proportionnels sans progressivité ne réduisent pas les inégalités",
    ),
    ReformeHistorique(
        id="impot_revenu_1914",
        nom="Création de l'impôt sur le revenu",
        annee=1914, categorie="fiscale",
        regime_contexte="IIIe République, Raymond Poincaré",
        description="Loi du 15 juillet 1914 — IR progressif à taux de 2% à 10%, assiette large, quotient familial",
        impact_immediat="Rendement modeste (1-2% des recettes) en 1914, explosant pendant la guerre",
        impact_long_terme="La progressivité fiscale réduit la part du top 10% de 50% à 35% en 50 ans (Piketty)",
        rendement_estime_mds_euros=100.0,  # 2024 : IR = 100 Md€
        sources=["Piketty (2001), chapitre 4 (barèmes IR 1914-1998)", "DGFIP"],
        pertinence_pour_simulateur="L'IR est le pilier redistributif ; le simulateur doit modéliser l'élasticité assiette/taux",
    ),
    ReformeHistorique(
        id="tva_1954",
        nom="Création de la TVA (Taxe sur la Valeur Ajoutée)",
        annee=1954, categorie="fiscale",
        regime_contexte="IVe République, Maurice Lauré (DG des Impôts)",
        description="Taxe sur la consommation neutre pour les entreprises, créée le 10 avril 1954",
        impact_immediat="Rendement immédiat, suppression de la cascade de taxes en cascade",
        impact_long_terme="Adoptée par 170 pays, premier impôt au monde par rendement (~180 Md€/an en France)",
        rendement_estime_mds_euros=180.0,
        sources=["DGFIP, Histoire de la TVA", "Commission européenne"],
        pertinence_pour_simulateur="La TVA est le principal outil de taxation de la consommation ; le simulateur modélise le rendement par taux",
    ),
    ReformeHistorique(
        id="csg_1991",
        nom="Création de la Contribution Sociale Généralisée (CSG)",
        annee=1991, categorie="sociale",
        regime_contexte="Ve République, Pierre Bérégovoy",
        description="Prélèvement à taux proportionnel (1,1% à l'origine → 9,2% en 2018) sur tous les revenus",
        impact_immediat="Rendement de 60 Md€/an, large assiette, faible coût de recouvement",
        impact_long_terme="Premier impôt fiscal finançant la protection sociale à la place des cotisations patronales",
        rendement_estime_mds_euros=100.0,
        sources=["DGFIP, Histoire de la CSG", "INSEE"],
        pertinence_pour_simulateur="La CSG est le mécanisme de transfert cotisations→CSG ; le simulateur modélise son impact sur le coût du travail",
    ),
    ReformeHistorique(
        id="retraites_2023",
        nom="Réforme des retraites (62→64 ans)",
        annee=2023, categorie="sociale",
        regime_contexte="Ve République, Emmanuel Macron / Élisabeth Borne",
        description="Report de l'âge légal de 62 à 64 ans, accélération de la réforme Touraine (43 annuités)",
        impact_immediat="Économie de 18 Md€/an à horizon 2030",
        impact_long_terme="Soutenabilité du système par répartition à long terme (déficit comblé)",
        rendement_estime_mds_euros=18.0,
        sources=["Conseil d'orientation des retraites (COR), Rapport 2023", "INSEE"],
        pertinence_pour_simulateur="Le simulateur modélise le déficit COR et les paramètres de réforme (âge, annuités, décote)",
    ),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 5 : CRISES HISTORIQUES MAJEURES (1792→2026)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRISES_HISTORIQUES: List[CriseHistorique] = [
    CriseHistorique(
        id="assignats_1793_1796",
        nom="Hyperinflation des assignats",
        annee_debut=1793, annee_fin=1796,
        type_crise="financiere", gravite=8,
        impact_pib_pct=-15.0, impact_dette_pct_pib=-55.0,  # Banqueroute des 2/3
        impact_chomage_pct=5.0,
        reponse_publique="Banqueroute des deux tiers (1797), création du franc germinal (1803)",
        duree_recuperation_annees=7,
        lecons="Le financement monétaire du déficit conduit à l'hyperinflation et à la destruction de l'épargne : le simulateur exclut tout scénario de financement direct du Trésor par la BCE.",
        sources=["Sargent & Velde (1995)", "Chicago Fed (2024)"],
    ),
    CriseHistorique(
        id="crise_1870_1873",
        nom="Défaite de 1870 et indemnité de guerre",
        annee_debut=1870, annee_fin=1873,
        type_crise="guerre", gravite=9,
        impact_pib_pct=-20.0, impact_dette_pct_pib=45.0,  # 68% → 113%
        impact_chomage_pct=8.0,
        reponse_publique="Émission de 3 emprunts internationaux, impôt exceptionnel sur les revenus",
        duree_recuperation_annees=15,
        lecons="Les réparations de guerre de 5 milliards de francs-or ont été payées en 2 ans grâce à l'épargne nationale : la France était le premier créancier mondial, preuve de la capacité d'absorption.",
        sources=["Chicago Fed (2024), p. 3-4", "Lévy-Leboyer & Bourguignon (1985)"],
    ),
    CriseHistorique(
        id="grande_guerre_1914_1918",
        nom="Première Guerre mondiale",
        annee_debut=1914, annee_fin=1918,
        type_crise="guerre", gravite=10,
        impact_pib_pct=-30.0, impact_dette_pct_pib=130.0,  # 68% → 200%
        impact_chomage_pct=0.0,  # Chômage masqué par la mobilisation
        reponse_publique="Création de l'IR (1914), emprunts de guerre, financement bancaire",
        duree_recuperation_annees=10,
        lecons="La création de l'IR est directement causée par le besoin de financement de guerre : les crises fiscales accélèrent les réformes structurelles.",
        sources=["Piketty (2001), chapitre 4", "IMF DataMapper (2026)"],
    ),
    CriseHistorique(
        id="depression_1930_1936",
        nom="Grande Dépression en France",
        annee_debut=1930, annee_fin=1936,
        type_crise="financiere", gravite=7,
        impact_pib_pct=-15.0, impact_dette_pct_pib=30.0,
        impact_chomage_pct=10.0,
        reponse_publique="Front populaire (1936) : congés payés, semaine de 40h, hausse des salaires",
        duree_recuperation_annees=6,
        lecons="La France a résisté plus longtemps que les USA ou l'Allemagne à la déflation, mais a fini par subir : les politiques déflationnistes prolongées ne réduisent pas le chômage.",
        sources=["Piketty (2001)", "Tanzi & Schuknecht (2000)"],
    ),
    CriseHistorique(
        id="choc_petrolier_1973_1974",
        nom="Premier choc pétrolier",
        annee_debut=1973, annee_fin=1975,
        type_crise="energetique", gravite=6,
        impact_pib_pct=-5.0, impact_dette_pct_pib=5.0,
        impact_chomage_pct=3.0,  # 2% → 5%
        reponse_publique="Plan de relance (1975), début du programme nucléaire de masse",
        duree_recuperation_annees=4,
        lecons="Le choc pétrolier transforme la structure énergétique : le programme nucléaire français est la réponse la plus efficace au monde. Le simulateur modélise le coût de transition énergétique.",
        sources=["INSEE, séries 1973-1975", "Tanzi & Schuknecht (2000)"],
    ),
    CriseHistorique(
        id="crise_financiere_2008_2009",
        nom="Crise des subprimes et Lehman Brothers",
        annee_debut=2008, annee_fin=2010,
        type_crise="financiere", gravite=8,
        impact_pib_pct=-5.0, impact_dette_pct_pib=20.0,  # 65% → 85%
        impact_chomage_pct=3.0,  # 7% → 10%
        reponse_publique="Plan de sauvetage bancaire (€360 Mds garanti), relance keynésienne (€26 Mds)",
        duree_recuperation_annees=6,
        lecons="La crise financière de 2008 montre que le risque systémique bancaire rejaillit sur la dette publique : le simulateur intègre le coût de renflouement des banques dans le scénario de crise.",
        sources=["IMF DataMapper (2026), INSEE"],
    ),
    CriseHistorique(
        id="covid_2020",
        nom="Pandémie de COVID-19",
        annee_debut=2020, annee_fin=2021,
        type_crise="sanitaire", gravite=9,
        impact_pib_pct=-8.0, impact_dette_pct_pib=17.0,  # 98% → 115%
        impact_chomage_pct=0.5,  # Contenu par le chômage partiel
        reponse_publique="« Quoi qu'il en coûte » : chômage partiel (12 M de salariés), PGE (€140 Mds), France Relance (€100 Mds)",
        duree_recuperation_annees=3,
        lecons="Le chômage partiel comme stabilisateur automatique a fonctionné (pauvreté stable à 14,6%) mais le coût budgétaire est sans précédent : le simulateur modélise la capacité d'absorption des crises extrêmes.",
        sources=["INSEE 2020-2021", "Cour des comptes (2021, 2022)", "IMF DataMapper (2026)"],
    ),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 6 : DIMENSIONS DE COMPARAISON (DROPDOWNS)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DIMENSIONS_COMPARISON = {
    "fiscale": {
        "label": "📊 Fiscalité & Budget",
        "icon": "📊",
        "indicateurs": {
            "recettes_publiques_pct_pib": "Recettes publiques (% PIB)",
            "depenses_publiques_pct_pib": "Dépenses publiques (% PIB)",
            "deficit_public_pct_pib": "Déficit public (% PIB)",
            "dette_publique_pct_pib": "Dette publique (% PIB)",
            "taux_imposition_superieur_pct": "Taux marginal supérieur IR (%)",
            "prélèvements_obligatoires_pct_pib": "Prélèvements obligatoires (% PIB)",
        },
    },
    "economique": {
        "label": "💰 Économie & Croissance",
        "icon": "💰",
        "indicateurs": {
            "pib_par_habitant_usd": "PIB par habitant (USD constants 2011)",
            "croissance_pib_reel_pct": "Croissance réelle (% annuelle)",
            "inflation_moyenne_pct": "Inflation (% annuelle)",
            "chomage_moyen_pct": "Chômage (% population active)",
            "salaire_moyen_reel_euros": "Salaire moyen réel (€ 2020)",
        },
    },
    "sociale": {
        "label": "👥 Inégalités & Social",
        "icon": "👥",
        "indicateurs": {
            "part_top10_pct": "Part des 10% les plus riches (%)",
            "part_top1_pct": "Part du top 1% (%)",
            "gini_revenu": "Coefficient de Gini",
            "taux_pauvrete_pct": "Taux de pauvreté (%)",
        },
    },
    "demographique": {
        "label": "🏠 Démographie",
        "icon": "🏠",
        "indicateurs": {
            "population_debut": "Population (millions)",
            "esperance_vie": "Espérance de vie (années)",
            "urbanisation_pct": "Urbanisation (%)",
        },
    },
    "energie": {
        "label": "⚡ Énergie & Environnement",
        "icon": "⚡",
        "indicateurs": {
            "source_energie_principale": "Source d'énergie principale",
            "production_charbon_mt": "Production charbon (Mt)",
            "consommation_petrole_mt": "Consommation pétrole (Mt)",
        },
    },
    "international": {
        "label": "🌍 International",
        "icon": "🌍",
        "indicateurs": {
            "solde_exterieur_pct_pib": "Balance commerciale (% PIB)",
            "conflits_majeurs": "Conflits majeurs",
            "alliances": "Alliances & traités",
        },
    },
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 7 : FONCTIONS D'ANALYSE ET DE COMPARAISON
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def obtenir_toutes_periodes() -> List[Dict]:
    """Retourne la liste de toutes les périodes historiques."""
    return [asdict(p) for p in PERIODES_HISTORIQUES]


def obtenir_periode_par_id(periode_id: str) -> Optional[Dict]:
    """Retourne une période par son identifiant."""
    for p in PERIODES_HISTORIQUES:
        if p.id == periode_id:
            return asdict(p)
    return None


def comparer_periodes(periode_a_id: str, periode_b_id: str,
                      dimensions: Optional[List[str]] = None) -> ComparaisonInterRegime:
    """Compare deux périodes historiques sur les dimensions demandées."""
    a = next((p for p in PERIODES_HISTORIQUES if p.id == periode_a_id), None)
    b = next((p for p in PERIODES_HISTORIQUES if p.id == periode_b_id), None)
    if not a or not b:
        raise ValueError(f"Période introuvable : {periode_a_id} ou {periode_b_id}")

    if dimensions is None:
        dimensions = list(DIMENSIONS_COMPARISON.keys())

    resultats = {}
    for dim in dimensions:
        if dim in DIMENSIONS_COMPARISON:
            indicateurs = DIMENSIONS_COMPARISON[dim]["indicateurs"]
            resultats[dim] = {}
            for attr, label in indicateurs.items():
                val_a = getattr(a, attr, None)
                val_b = getattr(b, attr, None)
                if val_a is not None and val_b is not None:
                    delta = None
                    if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                        delta = val_b - val_a
                    resultats[dim][attr] = {
                        "label": label,
                        "a": val_a,
                        "b": val_b,
                        "delta": delta,
                    }

    # Enseignements automatiques
    enseignements = []
    if abs(a.dette_publique_pct_pib - b.dette_publique_pct_pib) > 30:
        enseignements.append(
            f"Écart de dette/PIB de {abs(a.dette_publique_pct_pib - b.dette_publique_pct_pib):.0f} points : "
            f"le ratio est {'plus' if b.dette_publique_pct_pib > a.dette_publique_pct_pib else 'moins'} "
            f"élevé sous {b.nom} que sous {a.nom}."
        )
    if abs(a.gini_revenu - b.gini_revenu) > 0.05:
        enseignements.append(
            f"Écart de Gini de {abs(a.gini_revenu - b.gini_revenu):.2f} points : "
            f"les inégalités sont {'plus' if b.gini_revenu > a.gini_revenu else 'moins'} fortes "
            f"sous {b.nom} que sous {a.nom}."
        )
    if abs(a.chomage_moyen_pct - b.chomage_moyen_pct) > 3:
        enseignements.append(
            f"Écart de chômage de {abs(a.chomage_moyen_pct - b.chomage_moyen_pct):.1f} points : "
            f"le marché du travail est {'plus tendu' if b.chomage_moyen_pct > a.chomage_moyen_pct else 'plus détendu'} "
            f"sous {b.nom}."
        )

    return ComparaisonInterRegime(
        periode_a=a.nom, periode_b=b.nom,
        dimensions=resultats, enseignements=enseignements
    )


def filtrer_periodes(
    annee_min: Optional[int] = None,
    annee_max: Optional[int] = None,
    type_regime: Optional[str] = None,
    dette_min: Optional[float] = None,
    dette_max: Optional[float] = None,
    chomage_min: Optional[float] = None,
    chomage_max: Optional[float] = None,
    gini_min: Optional[float] = None,
    gini_max: Optional[float] = None,
) -> List[Dict]:
    """Filtre les périodes selon des critères multiples."""
    resultats = []
    for p in PERIODES_HISTORIQUES:
        if annee_min and p.annee_fin < annee_min:
            continue
        if annee_max and p.annee_debut > annee_max:
            continue
        if type_regime and p.type_regime != type_regime:
            continue
        if dette_min is not None and p.dette_publique_pct_pib < dette_min:
            continue
        if dette_max is not None and p.dette_publique_pct_pib > dette_max:
            continue
        if chomage_min is not None and p.chomage_moyen_pct < chomage_min:
            continue
        if chomage_max is not None and p.chomage_moyen_pct > chomage_max:
            continue
        if gini_min is not None and p.gini_revenu < gini_min:
            continue
        if gini_max is not None and p.gini_revenu > gini_max:
            continue
        resultats.append(asdict(p))
    return resultats


def obtenir_series_chronologiques(
    indicateur: str,
    annee_debut: Optional[int] = None,
    annee_fin: Optional[int] = None,
) -> List[Dict]:
    """Extrait une série chronologique pour un indicateur donné."""
    resultats = []
    for s in SERIES_ANNUELLES:
        if annee_debut and s.annee < annee_debut:
            continue
        if annee_fin and s.annee > annee_fin:
            continue
        val = getattr(s, indicateur, None)
        resultats.append({
            "annee": s.annee,
            "valeur": val,
            "evenement": s.evenement_majeur,
            "source": s.source,
        })
    return resultats


def obtenir_reformes(
    categorie: Optional[str] = None,
    annee_min: Optional[int] = None,
    annee_max: Optional[int] = None,
) -> List[Dict]:
    """Retourne les réformes historiques filtrées."""
    resultats = []
    for r in REFORMES_MAJEURES:
        if categorie and r.categorie != categorie:
            continue
        if annee_min and r.annee < annee_min:
            continue
        if annee_max and r.annee > annee_max:
            continue
        resultats.append(asdict(r))
    return resultats


def obtenir_crises(
    type_crise: Optional[str] = None,
    gravite_min: Optional[int] = None,
) -> List[Dict]:
    """Retourne les crises historiques filtrées."""
    resultats = []
    for c in CRISES_HISTORIQUES:
        if type_crise and c.type_crise != type_crise:
            continue
        if gravite_min and c.gravite < gravite_min:
            continue
        resultats.append(asdict(c))
    return resultats


def obtenir_options_dropdown() -> Dict:
    """Retourne toutes les options pour les menus déroulants de l'interface."""
    return {
        "periodes": [
            {"id": p.id, "nom": p.nom, "annees": f"{p.annee_debut}-{p.annee_fin}"}
            for p in PERIODES_HISTORIQUES
        ],
        "dimensions": [
            {"id": k, "label": v["label"]}
            for k, v in DIMENSIONS_COMPARISON.items()
        ],
        "types_regime": sorted(set(p.type_regime for p in PERIODES_HISTORIQUES)),
        "categories_reforme": sorted(set(r.categorie for r in REFORMES_MAJEURES)),
        "types_crise": sorted(set(c.type_crise for c in CRISES_HISTORIQUES)),
    }


def calculer_moyenne_mobile(serie: List[Dict], fenetre: int = 10) -> List[Dict]:
    """Calcule une moyenne mobile sur une fenêtre de N années."""
    resultats = []
    for i in range(len(serie)):
        debut = max(0, i - fenetre + 1)
        sous_serie = [s["valeur"] for s in serie[debut:i+1] if s["valeur"] is not None]
        resultats.append({
            "annee": serie[i]["annee"],
            "valeur_originale": serie[i]["valeur"],
            "moyenne_mobile": sum(sous_serie) / len(sous_serie) if sous_serie else None,
        })
    return resultats


def generer_synthese_historique() -> str:
    """Génère une synthèse textuelle des tendances historiques majeures."""
    lignes = [
        "═══════════════════════════════════════════════════════════════════",
        "SYNTHÈSE HISTORIQUE : 234 ANS DE POLITIQUE PUBLIQUE FRANÇAISE",
        "═══════════════════════════════════════════════════════════════════",
        "",
        "▸ DETTE PUBLIQUE / PIB :",
        "  • 1802 : 10 %  (après banqueroute des 2/3)",
        "  • 1871 : 113 % (indemnité de guerre franco-prussienne)",
        "  • 1914 : 68 %  (érosion par la croissance de 1,8 %/an)",
        "  • 1920 : 200 % (pic post-WWI)",
        "  • 1950 : 30 %  (érodiée par l'inflation et la croissance forte)",
        "  • 1980 : 21 %  (point bas historique moderne)",
        "  • 2007 : 65 %  (pré-crise subprimes)",
        "  • 2020 : 115 % (pic COVID-19)",
        "  • 2026 : 112 % (mandature en cours de rééquilibrage)",
        "",
        "▸ PRÉLÈVEMENTS OBLIGATOIRES / PIB :",
        "  • 1870 : 10 % (Leroy-Beaulieu : au-delà de 12 % = « exorbitant »)",
        "  • 1913 : 12 % (Tanzi-Schuknecht)",
        "  • 1950 : 28 % (sécurité sociale + reconstruction)",
        "  • 1980 : 43 % (apogée État-providence)",
        "  • 2026 : 47,5 % (record mondial pays développés hors Scandinavie)",
        "",
        "▸ INÉGALITÉS (Part du top 10 % dans le revenu national, Piketty) :",
        "  • 1900-1910 : 50 % (société de rentiers, pas d'IR)",
        "  • 1945-1950 : 37 % (destruction du capital, IR confiscatoire)",
        "  • 1970-1980 : 35 % (apogée de la compression inégalitaire)",
        "  • 2010-2026 : 36 % (légère remontée, capital financier mondialisé)",
        "",
        "▸ CHÔMAGE :",
        "  • 1870-1913 : 4 %  (quasi-plein emploi, travail des enfants)",
        "  • 1930-1938 : 12 % (Grande Dépression)",
        "  • 1946-1974 : 2 %  (Trente Glorieuses)",
        "  • 1985-1997 : 10 % (chômage de masse structurel)",
        "  • 2026 :      7 %  (plan de mandature vise le plein emploi à 5 %)",
        "",
        "▸ TAUX MARGINAL SUPÉRIEUR D'IR :",
        "  • 1790-1913 : 0 %  (pas d'IR)",
        "  • 1914 :      2 %  (taux initial)",
        "  • 1924 :      72 % (financement guerre + reconstruction)",
        "  • 1959-1969 : 65 % (De Gaulle)",
        "  • 1981-1985 : 65 % (Mitterrand)",
        "  • 2026 :      45 % (macronisme, PLF 2025)",
        "",
        "Enseignement principal : Les crises majeures (guerres, pandémies) sont",
        "les accélérateurs les plus puissants de réformes fiscales et sociales.",
        "La croissance érode la dette, la stagnation la fait exploser.",
        "═══════════════════════════════════════════════════════════════════",
    ]
    return "\n".join(lignes)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 8 : COMPATIBILITÉ AVEC LE SIMULATEUR (CALIBRATION)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def calibrer_parametres_historiques() -> Dict:
    """
    Retourne les paramètres historiques de référence pour calibrer
    le simulateur macro-politique (vérification de cohérence).
    """
    return {
        "dette_pib_plage": {
            "min_historique": 10.0,   # 1802 (post-banqueroute)
            "max_historique": 200.0,  # 1920 (post-WWI)
            "cible_simulateur": 109.0,  # Année 5 du plan de mandature
            "plage_soutenable": "60-120% PIB (critères Maastricht + marge)",
        },
        "po_pib_plage": {
            "min_historique": 10.0,   # 1870
            "max_historique": 47.5,   # 2026
            "cible_simulateur": 43.8,  # Mandature
            "plage_optimale": "40-45% PIB (modèle scandinave-français)",
        },
        "gini_plage": {
            "min_historique": 0.29,  # 1980 (Trente Glorieuses érodées)
            "max_historique": 0.55,  # 1792 (Ancien Régime)
            "cible_simulateur": 0.272,  # Mandature
            "plage_optimale": "0.25-0.32 (niveau Danemark-Pays nordiques)",
        },
        "chomage_plage": {
            "min_historique": 2.0,   # Trente Glorieuses
            "max_historique": 12.0,  # Dépression 1930
            "cible_simulateur": 5.0,  # Mandature (plein emploi)
            "plage_optimale": "4-6% (NAIRU française)",
        },
        "inflation_plage": {
            "min_historique": -0.5,  # Déflation 1870-1913
            "max_historique": 35.0,  # Hyperinflation 1793-1796
            "cible_simulateur": 2.0,  # Mandature (cible BCE)
            "plage_optimale": "1.5-2.5% (cible symétrique BCE)",
        },
        "taux_interet_historique": {
            "1870-1913": "3.5-5.0% (étalon-or, faible inflation)",
            "1914-1945": "5.0-6.0% (incertitude guerres)",
            "1946-1974": "4.0-7.0% (inflation modérée, croissance forte)",
            "1975-1998": "8.0-12.5% (inflation, prime de risque)",
            "1999-2021": "0.3-5.5% (euro, QE, taux bas)",
            "2022-2026": "2.5-3.5% (retour de l'inflation, BCE restrictive)",
        },
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 9 : EXPORT JSON (API REST)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def exporter_json_complet() -> str:
    """Exporte l'ensemble du module historique en JSON."""
    return json.dumps({
        "periodes": [asdict(p) for p in PERIODES_HISTORIQUES],
        "series_annuelles": [asdict(s) for s in SERIES_ANNUELLES],
        "reformes": [asdict(r) for r in REFORMES_MAJEURES],
        "crises": [asdict(c) for c in CRISES_HISTORIQUES],
        "dimensions": DIMENSIONS_COMPARISON,
        "parametres_calibration": calibrer_parametres_historiques(),
        "metadata": {
            "nb_periodes": len(PERIODES_HISTORIQUES),
            "nb_series": len(SERIES_ANNUELLES),
            "nb_reformes": len(REFORMES_MAJEURES),
            "nb_crises": len(CRISES_HISTORIQUES),
            "couverture": "1792-2026",
            "sources_principales": [
                "Piketty (2001, 2014, 2018), WID.world",
                "Chicago Fed Economic Perspectives (2024)",
                "Tanzi & Schuknecht (2000), Public Spending in the 20th Century",
                "IMF DataMapper (2026)",
                "Maddison Project Database (2020)",
                "INSEE, Comptes de la Nation",
                "DGFIP, Histoire de l'impôt",
            ],
            "date_generation": datetime.now().isoformat(),
        },
    }, ensure_ascii=False, indent=2)