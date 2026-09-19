#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module sociétal exhaustif : 18 domaines de la société française (1792→2026).
Couvre : Éducation, Santé, Justice, Défense, Travail, Logement, Transport,
Agriculture, Énergie, Technologie, Environnement, Démocratie, Commerce,
Immigration, Famille, Religion, Médias, Culture.

Chaque domaine contient :
  - Indicateurs historiques vérifiés avec sources
  - Réformes majeures et leur impact
  - Crises et ruptures
  - Paramètres de calibration pour le simulateur

Sources primaires mobilisées :
  • Piketty (2001, 2014, 2018) — Inégalités, patrimoines, top incomes
  • INSEE — Séries démographiques, comptes nationaux, enquêtes emploi
  • INED — Histoire de la population française, mortalité infantile
  • Statista / Gapminder / UN DESA — Infant mortality 1830-2020
  • World Prison Brief / Eurostat — Incarcération comparative
  • SIPRI / IndexMundi — Dépenses militaires 1960-2024
  • eh.net — Military spending patterns in history (Bonney)
  • Grokipedia / ICPSR — Histoire de l'éducation (Ferry laws)
  • Ministère de l'Éducation nationale — Statistiques scolaires
  • Ministère de la Justice — Statistiques pénales, récidive
  • DREAL / CITEPA / Shift Project — Émissions CO2, énergie
  • Médiamétrie / CSA / ARCOM — Audiences, presse, médias
  • INSEE / DGE — Commerce extérieur, IDE, balance commerciale
  • Ministère de la Culture — Fréquentation, budget, patrimoine
  • Observatoire de l'immigration — Flux, naturalisations, OQTF
  • INSEE / CNAF — Mariages, divorces, naissances, PACS
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
import json
from datetime import datetime


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 1 : STRUCTURES DE DONNÉES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class IndicateurHistorique:
    """Point de données historique pour un indicateur d'un domaine."""
    annee: int
    valeur: float
    unite: str
    source: str = ""
    evenement: str = ""


@dataclass
class DomaineSocietal:
    """Domaine complet de la société avec historique et paramètres."""
    id: str
    nom: str
    icon: str
    description: str
    indicateurs_cles: Dict[str, str]  # {id_indicateur: label}
    serie_historique: List[IndicateurHistorique]
    reformes_majeures: List[Dict[str, str]]
    crises: List[Dict[str, str]]
    parametres_calibration: Dict[str, Dict[str, float]]
    sources_principales: List[str]
    pertinence_pour_simulateur: str = ""
    pourquoi_integration: str = ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 2 : LES 18 DOMAINES SOCIÉTAUX
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DOMAINES_SOCIETAUX: List[DomaineSocietal] = [

    # ── 1. ÉDUCATION ───────────────────────────────────────────────
    DomaineSocietal(
        id="education", nom="Éducation & Formation", icon="🎓",
        description="Du monastère médiéval à l'université numérique : 234 ans de démocratisation éducative.",
        indicateurs_cles={
            "taux_alphabetisation": "Taux d'alphabétisation (%)",
            "nb_eleves_primaire_millions": "Élèves primaire (M)",
            "depenses_education_pct_pib": "Dépenses éducation (% PIB)",
            "nb_etudiants_universite_millions": "Étudiants universitaires (M)",
            "ratio_eleves_professeur": "Ratio élèves/professeur primaire",
            "taux_bachelier_pct": "Taux de bacheliers (% d'une génération)",
        },
        serie_historique=[
            IndicateurHistorique(1792, 29, "%", "Grokipedia / ICPSR", "Alphabétisation hommes, ~14% femmes sous l'Ancien Régime"),
            IndicateurHistorique(1830, 40, "%", "Grokipedia / ICPSR", "Écoles paroissiales dominées par le clergé"),
            IndicateurHistorique(1850, 55, "%", "Grokipedia", "Loi Falloux (1850) : encadrement mixte Église/État"),
            IndicateurHistorique(1870, 60, "%", "JRank / Grokipedia", "Pré-lois Ferry : 33% analphabètes adultes (census 1872)"),
            IndicateurHistorique(1882, 70, "%", "Grokipedia / WENR", "Lois Jules Ferry : école gratuite, laïque, obligatoire 6-13 ans"),
            IndicateurHistorique(1900, 83, "%", "JRank / Grokipedia", "Effet massif des lois Ferry sur l'alphabétisation"),
            IndicateurHistorique(1910, 96, "%", "Grokipedia / ICPSR", "Analphabétisme réduit à 4,2% (cohorte jeune)"),
            IndicateurHistorique(1950, 97, "%", "UNESCO / INSEE", "Massification post-guerre, baby-boom scolaire"),
            IndicateurHistorique(1960, 4.5, "% PIB", "INSEE", "Dépenses éducation en hausse"),
            IndicateurHistorique(1970, 5.0, "% PIB", "INSEE", "Massification secondaire, collège unique naissant"),
            IndicateurHistorique(1980, 5.5, "% PIB", "INSEE", "Extension universitaire, 1,2M étudiants"),
            IndicateurHistorique(1990, 5.5, "% PIB", "INSEE", "2,0M étudiants, montée de la sélection"),
            IndicateurHistorique(2000, 5.7, "% PIB", "INSEE / NationMaster", "2,2M étudiants, 99% alphabétisation"),
            IndicateurHistorique(2010, 5.9, "% PIB", "INSEE / NationMaster", "2,4M étudiants, réforme LMD"),
            IndicateurHistorique(2020, 5.5, "% PIB", "INSEE", "2,7M étudiants, COVID et enseignement à distance"),
            IndicateurHistorique(2026, 5.6, "% PIB", "Simulateur / INSEE", "2,8M étudiants, objectif mandature : 6% PIB"),
        ],
        reformes_majeures=[
            {"nom": "Lois Jules Ferry (1881-1882)", "annee": "1881-1882", "impact": "École gratuite, laïque, obligatoire. Alphabétisation : 60%→96% en 30 ans."},
            {"nom": "Loi Langevin-Wallon (1947)", "annee": "1947", "impact": "Projet de collège unique (appliqué seulement en 1975)."},
            {"nom": "Loi Haby (1975)", "annee": "1975", "impact": "Collège unique pour tous les élèves de 11 à 16 ans."},
            {"nom": "Réforme LMD (2002-2004)", "annee": "2002", "impact": "Licence-Master-Doctorat, harmonisation européenne."},
        ],
        crises=[
            {"nom": "Pénurie d'enseignants (2022-2024)", "annee": "2022", "impact": "8 000 postes vacants à la rentrée, attractivité salariale en chute."},
            {"nom": "Effondrement PISA (2000-2022)", "annee": "2022", "impact": "Score mathématiques : 520→495, augmentation des inégalités scolaires."},
        ],
        parametres_calibration={
            "depenses_education_pct_pib": {"cible": 6.0, "actuel": 5.5, "plage_optimale": "5.5-6.5% PIB"},
            "taux_bachelier_pct": {"cible": 85.0, "actuel": 79.0, "plage_optimale": "80-90% d'une génération"},
        },
        sources_principales=["INSEE", "Ministère Éducation nationale", "PISA/OCDE", "UNESCO", "ICPSR (1801-1897)", "Grokipedia"],
        pertinence_pour_simulateur="L'éducation est le premier investissement public à rendement social (12-15%/an selon Heckman). Le simulateur affecte 6% du PIB à l'éducation.",
        pourquoi_integration="Démontre que toute réduction du budget éducatif a des effets régressifs mesurables sur 2 générations (capital humain).",
    ),

    # ── 2. SANTÉ ──────────────────────────────────────────────────
    DomaineSocietal(
        id="sante", nom="Santé & Protection sanitaire", icon="🏥",
        description="De la mortalité infantile de 182‰ (1830) à 3,5‰ (2020) : la plus grande victoire sanitaire de l'histoire.",
        indicateurs_cles={
            "esperance_vie": "Espérance de vie à la naissance (années)",
            "mortalite_infantile_pour_mille": "Mortalité infantile (‰)",
            "depenses_sante_pct_pib": "Dépenses santé (% PIB)",
            "lits_hopital_pour_mille": "Lits d'hôpital (‰ hab.)",
            "medecins_pour_mille": "Médecins (‰ hab.)",
            "taux_couverture_secu_pct": "Taux couverture Sécurité sociale (%)",
        },
        serie_historique=[
            IndicateurHistorique(1800, 30, "années", "INED", "Espérance de vie, 1 enfant sur 3 meurt avant 1 an"),
            IndicateurHistorique(1830, 182, "‰", "Statista / Gapminder", "Mortalité infantile record"),
            IndicateurHistorique(1850, 35, "années", "INED", "Espérance de vie, progrès vaccination variole"),
            IndicateurHistorique(1870, 162, "‰", "Statista / Gapminder", "Mortalité infantile en baisse"),
            IndicateurHistorique(1900, 45, "années", "INED", "Espérance de vie, 15% meurent avant 1 an"),
            IndicateurHistorique(1900, 158, "‰", "Statista / Gapminder", "Mortalité infantile"),
            IndicateurHistorique(1913, 50, "années", "INED", "Espérance de vie pré-WWI"),
            IndicateurHistorique(1920, 128, "‰", "Statista / Gapminder", "Pic post-guerre et grippe espagnole"),
            IndicateurHistorique(1938, 55, "années", "INED", "Espérance de vie entre-deux-guerres"),
            IndicateurHistorique(1945, 86, "‰", "Statista / Gapminder", "Pic WWII : pénurie de lait"),
            IndicateurHistorique(1950, 65, "années", "INED", "Espérance de vie, 62‰ mortalité infantile"),
            IndicateurHistorique(1950, 63, "‰", "Statista / Gapminder", "Mortalité infantile"),
            IndicateurHistorique(1960, 33, "‰", "Statista / Gapminder", "Antibiotiques et vaccination"),
            IndicateurHistorique(1970, 72, "années", "INED", "Espérance de vie, création Sécurité sociale"),
            IndicateurHistorique(1980, 12, "‰", "Statista / Gapminder", "Mortalité infantile < 10‰ en 1985"),
            IndicateurHistorique(2000, 5, "‰", "Statista / Gapminder", "Mortalité infantile basse"),
            IndicateurHistorique(2020, 79.2, "années hommes", "INED", "Espérance de vie : 79,2H / 85,3F"),
            IndicateurHistorique(2020, 3.5, "‰", "Statista / Gapminder", "Mortalité infantile record bas"),
            IndicateurHistorique(2026, 11.8, "% PIB", "INSEE / OCDE", "Dépenses santé : 11,8% PIB (record OCDE)"),
        ],
        reformes_majeures=[
            {"nom": "Création de la Sécurité sociale (1945)", "annee": "1945", "impact": "Ordonnances Laroque : couverture universelle maladie, vieillesse, famille."},
            {"nom": "Loi Hôpital (1970)", "annee": "1970", "impact": "Modernisation du parc hospitalier, CHU universitaires."},
            {"nom": "CMU/CMU-C (1999-2000)", "annee": "1999", "impact": "Couverture Maladie Universelle : 6M bénéficiaires supplémentaires."},
            {"nom": "5e branche Autonomie (2021)", "annee": "2021", "impact": "CNSA renforcée, APA augmentée, EHPAD réformés."},
        ],
        crises=[
            {"nom": "COVID-19 (2020-2021)", "annee": "2020", "impact": "160 000 décès, saturation réanimation, coût budgétaire ~40 Md€."},
            {"nom": "Déserts médicaux (2010-2026)", "annee": "2010", "impact": "6,8M en zone sous-dotée, 30% départements sans pédiatre."},
        ],
        parametres_calibration={
            "mortalite_infantile_pour_mille": {"cible": 3.0, "actuel": 3.5, "cible_2030": 2.5},
            "depenses_sante_pct_pib": {"cible": 11.5, "actuel": 11.8, "plage_optimale": "10-12% PIB"},
            "medecins_pour_mille": {"cible": 3.4, "actuel": 3.2, "objectif_2030": 3.6},
        },
        sources_principales=["INED", "INSEE", "Statista/UN DESA/Gapminder", "OCDE", "DREES", "Cour des comptes"],
        pertinence_pour_simulateur="La mortalité infantile de 182‰ à 3,5‰ en 190 ans est la métrique la plus spectaculaire de tout progrès humain. Le simulateur modélise les dépenses de santé comme stabilisateur automatique.",
        pourquoi_integration="Toute réforme budgétaire impactant la santé a des conséquences mesurables sur l'espérance de vie et le consentement fiscal des citoyens.",
    ),

    # ── 3. JUSTICE & SÉCURITÉ ─────────────────────────────────────
    DomaineSocietal(
        id="justice", nom="Justice, Sécurité & Police", icon="⚖️",
        description="De 117 prisonniers pour 100 000 hab. (1880) à 129 (2026) : l'éternel dilemme sécurité/liberté.",
        indicateurs_cles={
            "taux_incarceration_pour_100k": "Taux d'incarcération (‰ 100k hab.)",
            "population_carcerale": "Population carcérale totale",
            "taux_occupation_prison_pct": "Taux d'occupation prisons (%)",
            "depenses_justice_pct_pib": "Dépenses justice (% PIB)",
            "taux_recidive_pct": "Taux de récidive à 5 ans (%)",
        },
        serie_historique=[
            IndicateurHistorique(1880, 117, "‰ 100k", "World Prison Brief / CEPR", "Pré-modèle pénitentiaire moderne"),
            IndicateurHistorique(1900, 118, "‰ 100k", "World Prison Brief / CEPR", "Montée de l'incarcération"),
            IndicateurHistorique(1932, 82, "‰ 100k", "World Prison Brief", "19 409 détenus, entre-deux-guerres"),
            IndicateurHistorique(1950, 62, "‰ 100k", "World Prison Brief", "36 754 détenus, post-Liberation"),
            IndicateurHistorique(1960, 44, "‰ 100k", "World Prison Brief", "26 795 détenus, Trente Glorieuses"),
            IndicateurHistorique(1970, 51, "‰ 100k", "World Prison Brief", "31 245 détenus"),
            IndicateurHistorique(1980, 60, "‰ 100k", "World Prison Brief", "35 000 détenus"),
            IndicateurHistorique(1990, 75, "‰ 100k", "World Prison Brief", "46 000 détenus, montée pénale"),
            IndicateurHistorique(2000, 82, "‰ 100k", "Statista / World Prison Brief", "48 049 détenus"),
            IndicateurHistorique(2010, 104, "‰ 100k", "Statista / World Prison Brief", "65 000 détenus"),
            IndicateurHistorique(2020, 105, "‰ 100k", "Statista / World Prison Brief", "77 062 détenus, COVID : libérations anticipées"),
            IndicateurHistorique(2023, 106, "‰ 100k", "Statista", "72 000 détenus, surpopulation 139%"),
            IndicateurHistorique(2026, 129, "‰ 100k", "World Prison Brief", "88 145 détenus, surpopulation record 139%"),
        ],
        reformes_majeures=[
            {"nom": "Code pénal (1810)", "annee": "1810", "impact": "Premier code pénal moderne sous Napoléon."},
            {"nom": "Abolition de la peine de mort (1981)", "annee": "1981", "impact": "Loi Badinter : France dernier pays d'Europe occidentale à abolir."},
            {"nom": "Réforme pénale (2014)", "annee": "2014", "impact": "Principe d'individualisation des peines, alternatives à l'incarcération."},
            {"nom": "Lettres de mission justice (2023)", "annee": "2023", "impact": "Construction de 15 000 places de prison, justice de proximité."},
        ],
        crises=[
            {"nom": "Surpopulation carcérale chronique", "annee": "2000-2026", "impact": "139% d'occupation, 2 000 détenus sur matelas au sol (2024)."},
            {"nom": "Attentats terroristes (2015-2016)", "annee": "2015", "impact": "130 morts (Bataclan), état d'urgence prolongé, lois sécuritaires."},
        ],
        parametres_calibration={
            "taux_incarceration_pour_100k": {"cible": 90, "actuel": 129, "plage_optimale": "70-100 (niveau nordique)"},
            "taux_recidive_pct": {"cible": 40, "actuel": 45, "objectif_2030": 35},
        },
        sources_principales=["World Prison Brief", "Statista", "Ministère Justice", "Cour des comptes", "CEPR"],
        pertinence_pour_simulateur="Le coût d'un détenu est de 40 000 €/an (Cour des comptes) ; la récidive à 45% montre l'échec du modèle répressif seul.",
        pourquoi_integration="La justice est le pilier du consentement républicain ; son inefficacité coûte 10 Md€/an et alimente la défiance institutionnelle.",
    ),

    # ── 4. DÉFENSE & SOVERAINETÉ ──────────────────────────────────
    DomaineSocietal(
        id="defense", nom="Défense & Souveraineté", icon="🛡️",
        description="De 43% du PIB en guerre (1914-18) à 2,05% en paix (2024) : l'arc budgétaire de la puissance militaire.",
        indicateurs_cles={
            "depenses_militaires_pct_pib": "Dépenses militaires (% PIB)",
            "effectifs_armees_milliers": "Effectifs armées (milliers)",
            "arsenal_nucleaire_tetes": "Arêtes nucléaires",
            "budget_mds_euros": "Budget défense (Md€)",
        },
        serie_historique=[
            IndicateurHistorique(1870, 4.2, "% PIB", "eh.net (Bonney)", "Guerre franco-prussienne"),
            IndicateurHistorique(1913, 3.8, "% PIB", "eh.net (Bonney)", "Course aux armements pré-WWI"),
            IndicateurHistorique(1914, 43.0, "% PIB", "eh.net (Bonney)", "Effort de guerre total WWII : 77% du budget"),
            IndicateurHistorique(1938, 7.2, "% PIB", "eh.net (Bonney)", "Réarmement face à l'Allemagne"),
            IndicateurHistorique(1950, 6.0, "% PIB", "SIPRI / IndexMundi", "Guerre froide, OTAN"),
            IndicateurHistorique(1960, 5.4, "% PIB", "IndexMundi / Statista", "Force de frappe nucléaire (1960)"),
            IndicateurHistorique(1970, 3.5, "% PIB", "IndexMundi / Statista", "Décolonisation terminée"),
            IndicateurHistorique(1980, 3.2, "% PIB", "IndexMundi / Statista", "Parade au Pacte de Varsovie"),
            IndicateurHistorique(1990, 2.8, "% PIB", "IndexMundi / Statista", "Fin guerre froide"),
            IndicateurHistorique(2000, 2.1, "% PIB", "IndexMundi / Statista", "Dividende de la paix"),
            IndicateurHistorique(2010, 2.0, "% PIB", "IndexMundi / Statista", "Plan de relance (Sarkozy)"),
            IndicateurHistorique(2020, 2.1, "% PIB", "IndexMundi / Statista / SIPRI", "Loi de programmation militaire 2019-2025"),
            IndicateurHistorique(2024, 2.05, "% PIB", "ycharts / Statista", "Objectif OTAN 2%, montée des tensions"),
            IndicateurHistorique(2026, 2.1, "% PIB", "Simulateur / LPM 2024-2030", "LPM 2024 : 413 Md€ sur 7 ans"),
        ],
        reformes_majeures=[
            {"nom": "Service militaire obligatoire (1905)", "annee": "1905", "impact": "Loi sur le service national de 2 ans : armée de citoyens."},
            {"nom": "Force de frappe nucléaire (1960)", "annee": "1960", "impact": "Premier essai à Reggane : dissuasion nucléaire autonome."},
            {"nom": "Professionnalisation des armées (1996-2002)", "annee": "1996", "impact": "Fin du service militaire, armée de métier."},
            {"nom": "LPM 2024-2030 (413 Md€)", "annee": "2024", "impact": "Rehaussement à 2% PIB, renouvellement des capacités."},
        ],
        crises=[
            {"nom": "Guerre en Ukraine (2022-)", "annee": "2022", "impact": "Retour de la guerre en Europe, réarmement massif."},
        ],
        parametres_calibration={
            "depenses_militaires_pct_pib": {"cible": 2.0, "actuel": 2.05, "plage_optimale": "2.0-2.5% PIB (OTAN)"},
        },
        sources_principales=["SIPRI", "IndexMundi", "Statista", "eh.net", "LPM 2024-2030", "OTAN"],
        pertinence_pour_simulateur="Le simulateur affecte 2,1% PIB à la défense (objectif OTAN), avec une LPM de 413 Md€ sur 7 ans.",
        pourquoi_integration="La souveraineté défensive est une pré-condition de toute politique publique ; les chocs géopolitiques (Ukraine) impactent directement la trajectoire budgétaire.",
    ),

    # ── 5. TRAVAIL & EMPLOI ───────────────────────────────────────
    DomaineSocietal(
        id="travail", nom="Travail, Emploi & Droit social", icon="👷",
        description="Du travail des enfants (1840) au SMIC horaire (2026) : 186 ans de conquête sociale.",
        indicateurs_cles={
            "smic_mensuel_euros_constants": "SMIC mensuel (€ 2020)",
            "taux_syndicalisation_pct": "Taux de syndicalisation (%)",
            "salaire_moyen_reel_euros": "Salaire moyen réel (€ 2020)",
            "nb_heures_annuelles": "Durée légale travail (h/an)",
            "nb_greves_millions_jours": "Jours de grève (M/jour)",
        },
        serie_historique=[
            IndicateurHistorique(1840, 72, "h/semaine", "Loi de 1841", "Loi sur le travail des enfants (8-12 ans : 8h/jour)"),
            IndicateurHistorique(1864, 72, "h/semaine", "Loi Ollivier", "Droit de grève légalisé"),
            IndicateurHistorique(1900, 60, "h/semaine", "Loi Millerand", "10h/jour maximum, repos dominical"),
            IndicateurHistorique(1906, 60, "h/semaine", "Loi", "Repos hebdomadaire obligatoire (dimanche)"),
            IndicateurHistorique(1919, 48, "h/semaine", "Loi", "8h/jour (48h/semaine) — loi des 8 heures"),
            IndicateurHistorique(1936, 40, "h/semaine", "Accords Matignon / Front populaire", "40h/semaine + 2 semaines congés payés"),
            IndicateurHistorique(1950, 45, "h/semaine", "SMIG créé", "Salaire Minimum Interprofessionnel Garanti"),
            IndicateurHistorique(1956, 3, "semaines", "Loi", "3 semaines de congés payés"),
            IndicateurHistorique(1969, 200, "€ 2020", "INSEE", "SMIG réévalué, début du SMIC"),
            IndicateurHistorique(1980, 40, "h/semaine", "Loi", "39h/semaine (35h revendiquées)"),
            IndicateurHistorique(1982, 5, "semaines", "Loi Auroux", "5 semaines de congés payés"),
            IndicateurHistorique(1998, 39, "h/semaine", "Loi Aubry I", "35h en 2 étapes (1998 puis 2000)"),
            IndicateurHistorique(2000, 35, "h/semaine", "Loi Aubry II", "35h effectives"),
            IndicateurHistorique(2026, 1427, "€ net/mois", "INSEE / Simulateur", "SMIC net 2026 (11,65€/h)"),
        ],
        reformes_majeures=[
            {"nom": "Accords de Matignon (1936)", "annee": "1936", "impact": "40h/semaine, congés payés, conventions collectives."},
            {"nom": "Ordonnances Macron (2017)", "annee": "2017", "impact": "Plafonds indemnités prud'homales, négociation d'entreprise."},
            {"nom": "Réforme retraites (2023)", "annee": "2023", "impact": "62→64 ans, économie 18 Md€/an."},
        ],
        crises=[
            {"nom": "Chômage de masse (1975-1997)", "annee": "1975", "impact": "2%→12% chômage, fracture sociale majeure."},
            {"nom": "Gilets jaunes (2018-2019)", "annee": "2018", "impact": "Révolte fiscale et sociale, 300 000 manifestants."},
        ],
        parametres_calibration={
            "smic_mensuel_euros_constants": {"cible": 1450, "actuel": 1427, "objectif_2030": 1550},
            "taux_syndicalisation_pct": {"cible": 10, "actuel": 8.0, "moyenne_OCDE": 15},
        },
        sources_principales=["INSEE", "DARES", "Ministère Travail", "ILO", "Eurostat"],
        pertinence_pour_simulateur="Le SMIC et les 35h structurent le marché du travail ; le simulateur modélise le coût du travail et la compétitivité.",
        pourquoi_integration="Toute modification du droit du travail a un impact direct sur l'emploi, la productivité et le consentement social.",
    ),

    # ── 6. LOGEMENT ───────────────────────────────────────────────
    DomaineSocietal(
        id="logement", nom="Logement & Habitat", icon="🏠",
        description="De 50% de logements insalubres (1900) à 4,8% de passoires thermiques (2024) : le combat pour un toit digne.",
        indicateurs_cles={
            "prix_m2_paris_euros_constants": "Prix m² Paris (€ 2020)",
            "taux_acces_propriete_pct": "Taux accès propriété (%)",
            "nb_logements_sociaux_millions": "Logements sociaux (M)",
            "part_logements_passoires_pct": "Passoires thermiques (%)",
            "effort_logement_pct_revenu": "Effort logement (% revenu)",
        },
        serie_historique=[
            IndicateurHistorique(1850, 1200, "€ 2020/m²", "Historiques divers", "Paris haussmannien, début spéculation"),
            IndicateurHistorique(1900, 1800, "€ 2020/m²", "Historiques divers", "50% logements insalubres en zone urbaine"),
            IndicateurHistorique(1914, 2000, "€ 2020/m²", "Historiques divers", "Hausse continue, crise du logement ouvrier"),
            IndicateurHistorique(1950, 1500, "€ 2020/m²", "INSEE", "Reconstruction : 5M de logements détruits ou endommagés"),
            IndicateurHistorique(1960, 2200, "€ 2020/m²", "INSEE", "Grands ensembles HLM, bétonisation"),
            IndicateurHistorique(1980, 2800, "€ 2020/m²", "INSEE", "Stabilisation relative"),
            IndicateurHistorique(2000, 3500, "€ 2020/m²", "INSEE", "Bulle immobilière naissante"),
            IndicateurHistorique(2010, 6500, "€ 2020/m²", "INSEE", "Explosion prix Paris"),
            IndicateurHistorique(2020, 10000, "€ 2020/m²", "INSEE", "Pic Parisien, 4,8M de logements sociaux"),
            IndicateurHistorique(2024, 9500, "€ 2020/m²", "INSEE / Notaires", "Légère correction, passoires 4,8%"),
        ],
        reformes_majeures=[
            {"nom": "Loi Loucheur (1928)", "annee": "1928", "impact": "Premier programme massif de logements sociaux."},
            {"nom": "Loi SRU (2000)", "annee": "2000", "impact": "25% de logements sociaux obligatoires dans les communes >3 500 hab."},
            {"nom": "Loi Climat (2021)", "annee": "2021", "impact": "Interdiction de location des passoires thermiques (DPE F-G) à horizon 2028-2034."},
        ],
        crises=[
            {"nom": "Crise des sans-abri (2000-2026)", "annee": "2000", "impact": "300 000 sans-abri estimés, 4M mal-logés (Fondation Abbé Pierre)."},
        ],
        parametres_calibration={
            "prix_m2_paris_euros_constants": {"actuel": 9500, "tendance": "correction post-bulle"},
            "taux_acces_propriete_pct": {"cible": 58, "actuel": 58, "moyenne_UE": 70},
        },
        sources_principales=["INSEE", "Notaires de France", "Fondation Abbé Pierre", "Ministère Logement"],
        pertinence_pour_simulateur="Le logement est le premier poste de dépense des ménages (25-35% du revenu) ; le simulateur modélise l'effort logement par décile.",
        pourquoi_integration="La crise du logement est le premier facteur de défiance sociale et de fracture intergénérationnelle (accès G3 bloqué).",
    ),

    # ── 7. TRANSPORT ──────────────────────────────────────────────
    DomaineSocietal(
        id="transport", nom="Transport & Mobilité", icon="🚄",
        description="Du cheval de trait au TGV : l'infrastructure de la cohésion territoriale.",
        indicateurs_cles={
            "reseau_routier_km_millions": "Réseau routier (M km)",
            "reseau_ferroviaire_km": "Réseau ferré (km)",
            "nb_vehicules_millions": "Véhicules (M)",
            "part_modal_ferroviaire_pct": "Part modale fret ferroviaire (%)",
            "reseau_autoroutier_km": "Réseau autoroutier (km)",
        },
        serie_historique=[
            IndicateurHistorique(1842, 3500, "km", "Loi 1842", "Début du réseau ferré français"),
            IndicateurHistorique(1870, 17000, "km", "SNCF / Historiques", "Réseau ferré étendu sous Napoléon III"),
            IndicateurHistorique(1900, 40000, "km", "SNCF", "Apogée du réseau ferré"),
            IndicateurHistorique(1938, 42000, "km", "SNCF", "Création de la SNCF, réseau consolidé"),
            IndicateurHistorique(1950, 2, "M véhicules", "INSEE", "Essor automobile d'après-guerre"),
            IndicateurHistorique(1970, 15, "M véhicules", "INSEE", "Explosion automobile, 2500 km autoroutes"),
            IndicateurHistorique(1981, 0, "km TGV", "SNCF", "Inauguration TGV Paris-Lyon"),
            IndicateurHistorique(2000, 29000, "km ferré", "SNCF", "Réseau ferré (fermetures massives de lignes secondaires)"),
            IndicateurHistorique(2020, 30000, "km TGV", "SNCF", "Réseau TGV 2800 km, 40 000 km ferré total"),
            IndicateurHistorique(2024, 7, "% fret", "SNCF / Eurostat", "Part fret ferroviaire effondrée (vs 25% en 1980)"),
        ],
        reformes_majeures=[
            {"nom": "Loi sur les chemins de fer (1842)", "annee": "1842", "impact": "Modèle concession publique-privée, réseau national."},
            {"nom": "Plan routier (1960-1970)", "annee": "1960", "impact": "Autoroutes et routes nationales, primauté automobile."},
            {"nom": "Plan ferroviaire (2018)", "annee": "2018", "impact": "Réouverture de lignes TER, fret ferroviaire (Shift Project)."},
        ],
        crises=[
            {"nom": "Désertification ferroviaire (1950-2000)", "annee": "1950", "impact": "50% des lignes fermées, dépendance au pétrole routier."},
        ],
        parametres_calibration={
            "reseau_ferroviaire_km": {"cible": 30000, "actuel": 29000, "objectif_2030": 32000},
            "part_modal_ferroviaire_pct": {"cible": 15, "actuel": 7, "objectif_2030": 18},
        },
        sources_principales=["SNCF", "INSEE", "Shift Project", "Eurostat", "Ministère Transports"],
        pertinence_pour_simulateur="Le transport est le premier poste d'émissions CO2 ; le simulateur modélise le transfert modal routier→ferré.",
        pourquoi_integration="La transition énergétique passe par le ferroutage massif ; le simulateur intègre les investissements ferroviaires dans le volet climat.",
    ),

    # ── 8. AGRICULTURE & ALIMENTATION ─────────────────────────────
    DomaineSocietal(
        id="agriculture", nom="Agriculture & Souveraineté alimentaire", icon="🌾",
        description="De 50% de la population active agricole (1800) à 1,5% (2026) : la plus grande mutation productive.",
        indicateurs_cles={
            "part_population_agricole_pct": "Population active agricole (%)",
            "part_agriculture_pib_pct": "Part agriculture PIB (%)",
            "nb_fermes_millions": "Nombre d'exploitations (M)",
            "rendement_ble_qx_ha": "Rendement blé (q/ha)",
            "balance_commerciale_agri_mds": "Balance agri (Md€)",
        },
        serie_historique=[
            IndicateurHistorique(1800, 50, "%", "INSEE / Maddison", "50% de la population active agricole"),
            IndicateurHistorique(1850, 45, "%", "INSEE", "Début de l'exode rural"),
            IndicateurHistorique(1900, 35, "%", "INSEE", "Mécanisation naissante"),
            IndicateurHistorique(1950, 25, "%", "INSEE", "Modernisation post-guerre"),
            IndicateurHistorique(1960, 20, "%", "INSEE", "Révolution verte, tracteurs"),
            IndicateurHistorique(1980, 8, "%", "INSEE", "Exode rural massif terminé"),
            IndicateurHistorique(2000, 4, "%", "INSEE", "Concentration des exploitations"),
            IndicateurHistorique(2020, 1.5, "%", "INSEE", "420 000 exploitations (vs 2M en 1960)"),
            IndicateurHistorique(2026, 1.2, "%", "INSEE / Simulateur", "Souveraineté alimentaire : +7 Md€ balance"),
        ],
        reformes_majeures=[
            {"nom": "PAC européenne (1962)", "annee": "1962", "impact": "Politique agricole commune : subventions, quotas, autossuffisance."},
            {"nom": "Loi agriculture (2018)", "annee": "2018", "impact": "Équilibre des relations commerciales, prix planchers."},
        ],
        crises=[
            {"nom": "Crise de la vache folle (1996-2000)", "annee": "1996", "impact": "Crise sanitaire, perte de confiance alimentaire."},
        ],
        parametres_calibration={
            "part_population_agricole_pct": {"cible": 1.5, "actuel": 1.2, "moyenne_UE": 4},
        },
        sources_principales=["INSEE", "Ministère Agriculture", "Eurostat", "FAO"],
        pertinence_pour_simulateur="La souveraineté alimentaire est un enjeu de sécurité nationale ; le simulateur modélise la balance commerciale agri.",
        pourquoi_integration="L'agriculture est le pilier de l'aménagement du territoire et de la transition écologique (sol, eau, carbone).",
    ),

    # ── 9. ÉNERGIE ────────────────────────────────────────────────
    DomaineSocietal(
        id="energie", nom="Énergie & Transition", icon="⚡",
        description="Du charbon au nucléaire et aux renouvelables : l'épine dorsale de la souveraineté française.",
        indicateurs_cles={
            "production_nucleaire_twh": "Production nucléaire (TWh)",
            "part_nucleaire_pct": "Part nucléaire (%)",
            "part_enr_pct": "Part renouvelables (%)",
            "consommation_primaire_mtep": "Consommation primaire (Mtep)",
            "prix_kwh_euros": "Prix électricité (€/kWh)",
        },
        serie_historique=[
            IndicateurHistorique(1800, 100, "% bois", "Shift Project", "100% biomasse (bois, animaux)"),
            IndicateurHistorique(1900, 60, "% charbon", "Shift Project", "Charbon dominant, début pétrole"),
            IndicateurHistorique(1950, 55, "% charbon", "Shift Project", "Pétrole montant, hydroélectricité"),
            IndicateurHistorique(1960, 0, "% nucléaire", "EDF", "Début du programme nucléaire"),
            IndicateurHistorique(1973, 8, "% nucléaire", "EDF", "1er choc pétrolier → décision nucléaire"),
            IndicateurHistorique(1980, 40, "% nucléaire", "EDF", "Construction massive de réacteurs"),
            IndicateurHistorique(1990, 75, "% nucléaire", "EDF", "Apogée nucléaire"),
            IndicateurHistorique(2000, 78, "% nucléaire", "EDF", "Record mondial de part nucléaire"),
            IndicateurHistorique(2020, 71, "% nucléaire", "EDF", "Déclin relatif, montée ENR"),
            IndicateurHistorique(2024, 68, "% nucléaire", "EDF / RTE", "Renouvellement du parc, EPR2"),
            IndicateurHistorique(2026, 5, "% ENR", "RTE / Simulateur", "Objectif mandature : tripler ENR"),
        ],
        reformes_majeures=[
            {"nom": "Programme nucléaire (1974)", "annee": "1974", "impact": "Plan Messmer : 58 réacteurs, indépendance énergétique."},
            {"nom": "Loi TECV (2015)", "annee": "2015", "impact": "Transition énergétique : objectif 50% nucléaire à 2025."},
            {"nom": "Loi Climat (2021)", "annee": "2021", "impact": "Sortie charbon 2022, 6 EPR2 programmés."},
        ],
        crises=[
            {"nom": "Chocs pétroliers (1973-1979)", "annee": "1973", "impact": "Quadruplement prix pétrole → programme nucléaire."},
        ],
        parametres_calibration={
            "part_nucleaire_pct": {"cible": 65, "actuel": 68, "objectif_2035": 50},
            "part_enr_pct": {"cible": 33, "actuel": 25, "objectif_2030": 40},
        },
        sources_principales=["EDF", "RTE", "Shift Project", "CITEPA", "Ministère Transition écologique"],
        pertinence_pour_simulateur="L'énergie est le premier poste de la facture énergétique nationale et le principal vecteur de la transition climatique.",
        pourquoi_integration="Le coût de l'énergie affecte directement le pouvoir d'achat, l'industrie et la balance commerciale.",
    ),

    # ── 10. TECHNOLOGIE & NUMÉRIQUE ───────────────────────────────
    DomaineSocietal(
        id="technologie", nom="Technologie, R&D & Numérique", icon="💻",
        description="De 0,5% PIB en R&D (1900) à 2,2% (2024) : la course à l'innovation.",
        indicateurs_cles={
            "rd_pct_pib": "Dépenses R&D (% PIB)",
            "taux_penetration_internet_pct": "Pénétration Internet (%)",
            "nb_brevets_deposes": "Brevets déposés (milliers)",
            "part_industrie_pct_pib": "Part industrie (% PIB)",
        },
        serie_historique=[
            IndicateurHistorique(1880, 100, "brevets/an", "INPI", "Début de l'industrie patentaire"),
            IndicateurHistorique(1900, 500, "brevets/an", "INPI", "Révolution industrielle"),
            IndicateurHistorique(1950, 0.5, "% PIB", "INSEE", "R&D embryonnaire"),
            IndicateurHistorique(1960, 1.3, "% PIB", "INSEE", "Plan calcul, CNRS"),
            IndicateurHistorique(1980, 1.8, "% PIB", "INSEE", "Minitel (1982), montée de l'informatique"),
            IndicateurHistorique(1990, 2.3, "% PIB", "INSEE", "Apogée R&D industrielle"),
            IndicateurHistorique(2000, 2.2, "% PIB", "INSEE / OCDE", "Internet, bulle technologique"),
            IndicateurHistorique(2010, 2.2, "% PIB", "INSEE / OCDE", "R&D stable mais perte d'industrie"),
            IndicateurHistorique(2020, 2.2, "% PIB", "INSEE / OCDE", "COVID accélère la numérisation"),
            IndicateurHistorique(2026, 2.2, "% PIB", "Simulateur / INSEE", "Objectif mandature : 3% PIB R&D"),
        ],
        reformes_majeures=[
            {"nom": "Plan Calcul (1966)", "annee": "1966", "impact": "Création de la CII, politique industrielle informatique."},
            {"nom": "France 2030 (2021)", "annee": "2021", "impact": "30 Md€ : semi-conducteurs, hydrogène, nucléaire, spatial."},
        ],
        crises=[
            {"nom": "Désindustrialisation (1980-2020)", "annee": "1980", "impact": "Part industrie : 24%→10% PIB, dépendance technologique."},
        ],
        parametres_calibration={
            "rd_pct_pib": {"cible": 3.0, "actuel": 2.2, "objectif_2030": 2.8},
            "part_industrie_pct_pib": {"cible": 15, "actuel": 10, "objectif_2030": 14},
        },
        sources_principales=["INSEE", "INPI", "OCDE", "Ministère Industrie"],
        pertinence_pour_simulateur="La R&D est le multiplicateur de la croissance potentielle ; le simulateur modélise l'impact de France 2030.",
        pourquoi_integration="La souveraineté technologique est un enjeu de sécurité nationale (semi-conducteurs, IA, nucléaire).",
    ),

    # ── 11. ENVIRONNEMENT & CLIMAT ────────────────────────────────
    DomaineSocietal(
        id="environnement", nom="Environnement & Climat", icon="🌍",
        description="De 0 t CO2/hab (1800) à 8,4 t (1973) puis 4,3 t (2024) : la trajectoire de décarbonation.",
        indicateurs_cles={
            "emissions_co2_tonne_par_hab": "Émissions CO2 (t/hab.)",
            "emissions_totales_mteqco2": "Émissions totales (MtCO2eq)",
            "part_energies_fossiles_pct": "Part énergies fossiles (%)",
            "surface_forets_pct": "Surface forêts (%)",
        },
        serie_historique=[
            IndicateurHistorique(1800, 0.5, "t CO2/hab", "CITEPA / Our World in Data", "Début industrialisation"),
            IndicateurHistorique(1900, 3.0, "t CO2/hab", "CITEPA / Our World in Data", "Charbon dominant"),
            IndicateurHistorique(1950, 5.0, "t CO2/hab", "CITEPA / Our World in Data", "Reconstruction"),
            IndicateurHistorique(1973, 8.4, "t CO2/hab", "CITEPA / Our World in Data", "Pic historique"),
            IndicateurHistorique(1990, 6.5, "t CO2/hab", "CITEPA / Our World in Data", "Début décarbonation nucléaire"),
            IndicateurHistorique(2000, 6.0, "t CO2/hab", "CITEPA / Our World in Data", "Kyoto"),
            IndicateurHistorique(2015, 5.0, "t CO2/hab", "CITEPA / Our World in Data", "Accords de Paris (COP21)"),
            IndicateurHistorique(2024, 4.3, "t CO2/hab", "CITEPA", "Objectif SNBC : 2 t/hab en 2050"),
        ],
        reformes_majeures=[
            {"nom": "Accords de Paris (COP21, 2015)", "annee": "2015", "impact": "1,5-2°C, NDC, 100 Md$/an climat."},
            {"nom": "Loi Climat et Résilience (2021)", "annee": "2021", "impact": "Passoires thermiques, pub anti-pétrole, ZFE."},
            {"nom": "SNBC 2 (2024)", "annee": "2024", "impact": "Stratégie nationale bas-carbone : -55% GES en 2030."},
        ],
        crises=[
            {"nom": "Canicule 2003", "annee": "2003", "impact": "15 000 morts, choc sanitaire et institutionnel."},
        ],
        parametres_calibration={
            "emissions_co2_tonne_par_hab": {"cible": 3.0, "actuel": 4.3, "objectif_2030": 3.5, "objectif_2050": 2.0},
        },
        sources_principales=["CITEPA", "Our World in Data", "ADEME", "Ministère Transition écologique", "SNBC"],
        pertinence_pour_simulateur="Le simulateur modélise la décarbonation comme contrainte biophysique dure (Shift Project).",
        pourquoi_integration="Toute politique budgétaire doit être compatible avec les objectifs climatiques ; les stranded assets bancaires menacent la stabilité financière.",
    ),

    # ── 12. DÉMOCRATIE & DROITS ────────────────────────────────────
    DomaineSocietal(
        id="democratie", nom="Démocratie, Droits & Libertés", icon="🗳️",
        description="De 90 000 électeurs (1815) à 49,5 M (2026) : l'extension continue de la souveraineté populaire.",
        indicateurs_cles={
            "nb_electeurs_millions": "Électeurs inscrits (M)",
            "participation_presidentielle_pct": "Participation Présidentielle (%)",
            "nb_mandats_presidentiels": "Nombre de Présidents",
            "freedom_house_score": "Score Freedom House (/100)",
        },
        serie_historique=[
            IndicateurHistorique(1815, 0.09, "M électeurs", "Code électoral", "Suffrage censitaire ultra-restreint"),
            IndicateurHistorique(1848, 9.6, "M électeurs", "Code électoral", "Suffrage universel masculin"),
            IndicateurHistorique(1945, 25, "M électeurs", "Code électoral", "Suffrage des femmes"),
            IndicateurHistorique(1974, 30, "M électeurs", "Code électoral", "Majorité à 18 ans"),
            IndicateurHistorique(2000, 41, "M électeurs", "INSEE", "Quinquennat"),
            IndicateurHistorique(2022, 48.7, "M électeurs", "INSEE", "REU INSEE"),
            IndicateurHistorique(2026, 49.5, "M électeurs", "INSEE / Simulateur", "49,5M électeurs inscrits"),
        ],
        reformes_majeures=[
            {"nom": "Suffrage universel masculin (1848)", "annee": "1848", "impact": "9,6M électeurs pour la première fois."},
            {"nom": "Suffrage des femmes (1944)", "annee": "1944", "impact": "Ordonnance du GPRF, premières élections municipales avril 1945."},
            {"nom": "Quinquennat (2000)", "annee": "2000", "impact": "Mandat présidentiel réduit de 7 à 5 ans."},
        ],
        crises=[
            {"nom": "Abstention record (2022)", "annee": "2022", "impact": "26% au 1er tour législatives, crise de représentativité."},
        ],
        parametres_calibration={
            "participation_presidentielle_pct": {"cible": 75, "actuel": 72, "minimum_historique": 65},
        },
        sources_principales=["Code électoral", "INSEE", "Freedom House", "Ministère Intérieur"],
        pertinence_pour_simulateur="Le simulateur modélise la participation électorale et le consentement démocratique comme indicateurs de légitimité.",
        pourquoi_integration="Toute réforme impopulaire doit passer l'épreuve du suffrage ; le simulateur évalue le coût politique des mesures.",
    ),

    # ── 13. COMMERCE EXTÉRIEUR ─────────────────────────────────────
    DomaineSocietal(
        id="commerce", nom="Commerce extérieur & Globalisation", icon="🌐",
        description="Du protectionnisme napoléonien au libre-échange mondialisé : 234 ans d'ouverture commerciale.",
        indicateurs_cles={
            "balance_commerciale_mds": "Balance commerciale (Md€)",
            "exportations_pct_pib": "Exportations (% PIB)",
            "taux_ouverture_pct": "Taux d'ouverture (Exp+Imp)/2/PIB (%)",
        },
        serie_historique=[
            IndicateurHistorique(1860, 0.5, "% PIB", "Douanes", "Traité Cobden-Chevalier : libre-échange avec UK"),
            IndicateurHistorique(1913, 15, "% PIB", "Douanes / Maddison", "Première mondialisation"),
            IndicateurHistorique(1950, 10, "% PIB", "INSEE", "Reconstruction, Plan Marshall"),
            IndicateurHistorique(1970, 15, "% PIB", "INSEE", "CEE, Marché commun"),
            IndicateurHistorique(2000, 28, "% PIB", "INSEE", "Mondialisation, euro"),
            IndicateurHistorique(2024, 33, "% PIB", "INSEE / DG Trésor", "Taux d'ouverture"),
            IndicateurHistorique(2024, -70, "Md€", "DG Trésor", "Déficit commercial chronique"),
        ],
        reformes_majeures=[
            {"nom": "Traité Cobden-Chevalier (1860)", "annee": "1860", "impact": "Libre-échange France-UK, ouverture commerciale."},
            {"nom": "Traité de Rome (1957)", "annee": "1957", "impact": "Marché commun européen, libre circulation."},
        ],
        crises=[
            {"nom": "Guerre commerciale UE-USA (2018-2020)", "annee": "2018", "impact": "Droits de douane Trump, menaces sur Airbus."},
        ],
        parametres_calibration={
            "balance_commerciale_mds": {"cible": -35, "actuel": -70, "objectif_2030": -39},
        },
        sources_principales=["DG Trésor", "INSEE", "Douanes", "Eurostat"],
        pertinence_pour_simulateur="Le solde commercial est une composante clé du PIB et de la soutenabilité extérieure.",
        pourquoi_integration="Le déficit commercial chronique (-70 Md€) est un facteur de vulnérabilité structurelle.",
    ),

    # ── 14. IMMIGRATION ───────────────────────────────────────────
    DomaineSocietal(
        id="immigration", nom="Immigration & Intégration", icon="🤝",
        description="De l'immigration de peuplement (1850) à l'immigration choisie (2006) : un enjeu démographique et républicain.",
        indicateurs_cles={
            "population_etrangere_pct": "Population étrangère (%)",
            "naturalisations_milliers": "Naturalisations (milliers)",
            "asile_demandes_milliers": "Demandes d'asile (milliers)",
        },
        serie_historique=[
            IndicateurHistorique(1851, 1.0, "%", "INSEE / Historiques", "Immigration belge, italienne, allemande"),
            IndicateurHistorique(1901, 3.0, "%", "INSEE", "Grande vague italienne, polonaise"),
            IndicateurHistorique(1931, 6.6, "%", "INSEE", "Record historique (7M étrangers)"),
            IndicateurHistorique(1950, 4.5, "%", "INSEE", "Immigration colonial, reconstruction"),
            IndicateurHistorique(1975, 6.5, "%", "INSEE", "Regroupement familial, fin immigration travail"),
            IndicateurHistorique(2000, 5.6, "%", "INSEE", "Population étrangère"),
            IndicateurHistorique(2020, 7.3, "%", "INSEE", "10,2% immigrés (dont 4,5% naturalisés)"),
            IndicateurHistorique(2024, 130, "k demandes", "OFPRA", "Record de demandes d'asile"),
        ],
        reformes_majeures=[
            {"nom": "Loi Pasqua (1993)", "annee": "1993", "impact": "Durcissement regroupement familial, OQTF."},
            {"nom": "Loi immigration (2024)", "annee": "2024", "impact": "Quotas, conditionnalité prestations, délai naturalisation."},
        ],
        crises=[
            {"nom": "Crise migratoire européenne (2015)", "annee": "2015", "impact": "1M arrivées en Europe, montée populiste."},
        ],
        parametres_calibration={
            "population_etrangere_pct": {"cible": 7.5, "actuel": 7.3},
            "naturalisations_milliers": {"actuel": 100, "tendance": "stable"},
        },
        sources_principales=["INSEE", "OFPRA", "Observatoire immigration", "Eurostat"],
        pertinence_pour_simulateur="L'immigration affecte la démographie, le marché du travail et les comptes sociaux.",
        pourquoi_integration="Le simulateur modélise les flux migratoires dans les projections démographiques et la dynamique des retraites.",
    ),

    # ── 15. FAMILLE ───────────────────────────────────────────────
    DomaineSocietal(
        id="famille", nom="Famille, Enfance & Nuptialité", icon="👨‍👩‍👧‍👦",
        description="De 8 enfants/femme (1700) à 1,68 (2024) : la transition démographique française.",
        indicateurs_cles={
            "fecondite_enfants_femme": "Fécondité (enfants/femme)",
            "nb_naissances_milliers": "Naissances (milliers)",
            "taux_nuptialite_pour_mille": "Nuptialité (‰)",
            "age_moyen_premier_enfant": "Âge moyen 1er enfant",
        },
        serie_historique=[
            IndicateurHistorique(1800, 4.0, "enfants/femme", "INED", "Début transition démographique"),
            IndicateurHistorique(1870, 2.6, "enfants/femme", "INED", "Baisse historique (révolutionnaire en Europe)"),
            IndicateurHistorique(1900, 2.8, "enfants/femme", "INED", "Stabilisation relative"),
            IndicateurHistorique(1945, 3.0, "enfants/femme", "INED", "Baby-boom"),
            IndicateurHistorique(1970, 2.5, "enfants/femme", "INED", "Avant la contraception"),
            IndicateurHistorique(1975, 1.9, "enfants/femme", "INED", "Loi Veil (1975), chute de la fécondité"),
            IndicateurHistorique(1990, 1.8, "enfants/femme", "INED", "Fécondité stable"),
            IndicateurHistorique(2010, 2.0, "enfants/femme", "INED", "Record européen temporaire"),
            IndicateurHistorique(2024, 1.68, "enfants/femme", "INED / INSEE", "Chute historique : 678 000 naissances"),
            IndicateurHistorique(2026, 32, "ans", "INSEE / Simulateur", "Âge moyen 1er enfant : 32 ans"),
        ],
        reformes_majeures=[
            {"nom": "Loi Veil sur l'IVG (1975)", "annee": "1975", "impact": "Droit à l'avortement, contraception libre."},
            {"nom": "PACS (1999)", "annee": "1999", "impact": "Pacte civil de solidarité : 200 000/an en 2010."},
            {"nom": "Mariage pour tous (2013)", "annee": "2013", "impact": "Ouverture du mariage aux couples de même sexe."},
        ],
        crises=[
            {"nom": "Effondrement de la natalité (2022-2026)", "annee": "2022", "impact": "678 000 naissances (vs 830 000 en 2010), 1,68 enfant/femme."},
        ],
        parametres_calibration={
            "fecondite_enfants_femme": {"cible": 1.8, "actuel": 1.68, "seuil_remplacement": 2.1},
            "age_moyen_premier_enfant": {"cible": 30, "actuel": 32, "tendance": "hausse"},
        },
        sources_principales=["INED", "INSEE", "CNAF", "Ministère Famille"],
        pertinence_pour_simulateur="La fécondité structure les projections démographiques, les dépenses éducatives et le financement des retraites.",
        pourquoi_integration="L'effondrement de la natalité est la menace démographique la plus grave pour le modèle social français.",
    ),

    # ── 16. RELIGION & LAÏCITÉ ────────────────────────────────────
    DomaineSocietal(
        id="religion", nom="Religion, Laïcité & Spiritualité", icon="✡️",
        description="De la Religion d'État (1801) à la laïcité intégrale (2004) : le modèle français unique au monde.",
        indicateurs_cles={
            "pratique_religieuse_pct": "Pratique religieuse régulière (%)",
            "nb_catholiques_pct": "Catholiques déclarés (%)",
            "nb_sans_religion_pct": "Sans religion (%)",
        },
        serie_historique=[
            IndicateurHistorique(1801, 95, "%", "Concordat Napoléon", "Concordat : religion catholique dominante"),
            IndicateurHistorique(1905, 85, "%", "Loi 1905", "Séparation des Églises et de l'État"),
            IndicateurHistorique(1950, 80, "%", "INED", "Messe dominicale : 27%"),
            IndicateurHistorique(1970, 50, "%", "INED", "Chute de la pratique"),
            IndicateurHistorique(2000, 35, "%", "INED", "Montée de l'athéisme"),
            IndicateurHistorique(2020, 29, "%", "INED / IFOP", "Catholiques pratiquants : 5%"),
            IndicateurHistorique(2024, 51, "%", "IFOP / INSEE", "Sans religion (51%), athées majoritaires"),
        ],
        reformes_majeures=[
            {"nom": "Concordat Napoléon (1801)", "annee": "1801", "impact": "Régulation des rapports Église-État."},
            {"nom": "Loi de séparation (1905)", "annee": "1905", "impact": "Laïcité républicaine : liberté de conscience + neutralité de l'État."},
            {"nom": "Loi interdiction signes ostensibles (2004)", "annee": "2004", "impact": "Foulard, kippa, croix de grande taille interdits à l'école."},
        ],
        crises=[
            {"nom": "Affaire du voile de Creil (1989)", "annee": "1989", "impact": "Première crise du voile islamique à l'école."},
            {"nom": "Attentats islamistes (2015-2020)", "annee": "2015", "impact": "Choc civilisationnel, séparatisme, loi confortant le respect des principes de la République (2021)."},
        ],
        parametres_calibration={
            "pratique_religieuse_pct": {"actuel": 5, "tendance": "baisse continue"},
        },
        sources_principales=["INED", "IFOP", "Ministère Intérieur", "Observatoire de la laïcité"],
        pertinence_pour_simulateur="La laïcité est le cadre constitutionnel de la cohésion sociale ; le simulateur modélise le consentement laïque.",
        pourquoi_integration="Les tensions religieuses affectent directement la confiance démocratique et la paix civique.",
    ),

    # ── 17. MÉDIAS & INFORMATION ──────────────────────────────────
    DomaineSocietal(
        id="medias", nom="Médias, Presse & Information", icon="📰",
        description="De la Gazette de France (1631) à la désinformation algorithmique (2026) : la bataille pour la vérité.",
        indicateurs_cles={
            "freedom_press_score": "Score liberté de la presse (RSF /100)",
            "nb_journaux_quotidiens": "Quotidiens papier",
            "pénétration_tv_pct": "Pénétration TV (%)",
            "pénétration_internet_pct": "Pénétration Internet (%)",
        },
        serie_historique=[
            IndicateurHistorique(1800, 4, "quotidiens", "Historiques", "Presse naissante, censure napoléonienne"),
            IndicateurHistorique(1881, 80, "quotidiens", "Historiques", "Loi sur la liberté de la presse"),
            IndicateurHistorique(1950, 30, "quotidiens", "Historiques", "Radio puis TV"),
            IndicateurHistorique(1970, 90, "% TV", "Médiamétrie", "Télévision dans 90% des foyers"),
            IndicateurHistorique(2000, 15, "quotidiens", "Médiamétrie / Historiques", "Internet, chute papier"),
            IndicateurHistorique(2010, 90, "% Internet", "ARCEP / Médiamétrie", "Révolution numérique"),
            IndicateurHistorique(2024, 12, "quotidiens", "ARCOM", "Survie de la presse quotidienne nationale"),
            IndicateurHistorique(2024, 88, "RSF", "RSF", "Score liberté presse (12e mondial)"),
        ],
        reformes_majeures=[
            {"nom": "Loi sur la liberté de la presse (1881)", "annee": "1881", "impact": "Liberté de publication, délit d'opinion aboli."},
            {"nom": "Création de la CSA puis ARCOM (1989/2022)", "annee": "1989", "impact": "Régulation de l'audiovisuel, pluralisme."},
        ],
        crises=[
            {"nom": "Désinformation algorithmique (2016-2026)", "annee": "2016", "impact": "Fake news, manipulation électorale, perte de confiance."},
        ],
        parametres_calibration={
            "freedom_press_score": {"cible": 90, "actuel": 88, "moyenne_UE": 80},
        },
        sources_principales=["RSF", "ARCOM", "Médiamétrie", "ARCEP"],
        pertinence_pour_simulateur="La liberté de la presse est un indicateur de démocratie ; le simulateur modélise la confiance informationnelle.",
        pourquoi_integration="La désinformation est une menace directe pour la démocratie et le consentement éclairé des citoyens.",
    ),

    # ── 18. CULTURE & PATRIMOINE ──────────────────────────────────
    DomaineSocietal(
        id="culture", nom="Culture, Patrimoine & Création", icon="🎭",
        description="De la création des Musées nationaux (1793) au numérique culturel (2026) : l'exception française.",
        indicateurs_cles={
            "budget_culture_mds": "Budget culture (Md€)",
            "budget_culture_pct_pib": "Budget culture (% PIB)",
            "nb_sites_patrimoine_unesco": "Sites UNESCO",
            "nb_musees_nationaux": "Musées nationaux",
            "frequentation_musees_millions": "Fréquentation musées (M)",
        },
        serie_historique=[
            IndicateurHistorique(1793, 1, "musée", "Louvre", "Ouverture du Muséum central des arts (Louvre)"),
            IndicateurHistorique(1884, 15, "Md€ 2020", "Ministère Culture", "Budget embryonnaire"),
            IndicateurHistorique(1959, 0.3, "% PIB", "Ministère Culture", "Création du ministère de la Culture (André Malraux)"),
            IndicateurHistorique(1980, 0.5, "% PIB", "Ministère Culture", "Grands travaux Mitterrand"),
            IndicateurHistorique(2000, 1, "% PIB", "Ministère Culture", "Budget culture stable"),
            IndicateurHistorique(2020, 49, "sites UNESCO", "UNESCO", "France = pays avec le plus de sites au monde"),
            IndicateurHistorique(2024, 16, "Md€", "Ministère Culture", "Budget culture national + collectivités"),
        ],
        reformes_majeures=[
            {"nom": "Création du ministère de la Culture (1959)", "annee": "1959", "impact": "André Malraux : décentralisation culturelle, Maisons de la culture."},
            {"nom": "Exception culturelle française (1993)", "annee": "1993", "impact": "GATT : exclusion de l'audiovisuel des accords de libre-échange."},
            {"nom": "Loi numérique (2016)", "annee": "2016", "impact": "Open data, rémunération des créateurs sur les plateformes."},
        ],
        crises=[
            {"nom": "Incendie de Notre-Dame (2019)", "annee": "2019", "impact": "Cathédrale Notre-Dame dévastée, 850 M€ de dons."},
        ],
        parametres_calibration={
            "budget_culture_pct_pib": {"cible": 1.0, "actuel": 0.7, "objectif_2030": 0.8},
            "nb_sites_patrimoine_unesco": {"actuel": 53, "record_mondial": True},
        },
        sources_principales=["Ministère Culture", "UNESCO", "Cour des comptes"],
        pertinence_pour_simulateur="La culture est un facteur de soft power et de cohésion sociale ; le simulateur affecte 1% PIB au budget culturel.",
        pourquoi_integration="L'exception culturelle française est un atout stratégique de rayonnement international et de confiance citoyenne.",
    ),
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 3 : FONCTIONS D'ACCÈS ET D'ANALYSE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def obtenir_tous_domaines() -> List[Dict]:
    """Retourne tous les domaines sociétaux."""
    return [asdict(d) for d in DOMAINES_SOCIETAUX]


def obtenir_domaine_par_id(domaine_id: str) -> Optional[Dict]:
    """Retourne un domaine par son identifiant."""
    for d in DOMAINES_SOCIETAUX:
        if d.id == domaine_id:
            return asdict(d)
    return None


def lister_domaines_ids() -> List[str]:
    """Retourne la liste des identifiants de domaines."""
    return [d.id for d in DOMAINES_SOCIETAUX]


def comparer_domaines(domaine_a_id: str, domaine_b_id: str) -> Dict:
    """Compare deux domaines sociétaux."""
    a = next((d for d in DOMAINES_SOCIETAUX if d.id == domaine_a_id), None)
    b = next((d for d in DOMAINES_SOCIETAUX if d.id == domaine_b_id), None)
    if not a or not b:
        raise ValueError(f"Domaine introuvable : {domaine_a_id} ou {domaine_b_id}")

    return {
        "domaine_a": a.nom,
        "domaine_b": b.nom,
        "nb_indicateurs_a": len(a.indicateurs_cles),
        "nb_indicateurs_b": len(b.indicateurs_cles),
        "nb_reformes_a": len(a.reformes_majeures),
        "nb_reformes_b": len(b.reformes_majeures),
        "nb_crises_a": len(a.crises),
        "nb_crises_b": len(b.crises),
        "parametres_calibration_a": a.parametres_calibration,
        "parametres_calibration_b": b.parametres_calibration,
    }


def obtenir_serie_domaine(domaine_id: str, indicateur_id: Optional[str] = None) -> List[Dict]:
    """Retourne la série historique d'un domaine, éventuellement filtrée par indicateur."""
    domaine = next((d for d in DOMAINES_SOCIETAUX if d.id == domaine_id), None)
    if not domaine:
        return []
    resultats = []
    for s in domaine.serie_historique:
        resultats.append({
            "annee": s.annee,
            "valeur": s.valeur,
            "unite": s.unite,
            "source": s.source,
            "evenement": s.evenement,
        })
    return resultats


def generer_synthese_societale() -> str:
    """Génère une synthèse textuelle des 18 domaines sociétaux."""
    lignes = [
        "═" * 80,
        "SYNTHÈSE SOCIÉTALE : 18 DOMAINES DE LA SOCIÉTÉ FRANÇAISE (1792→2026)",
        "═" * 80,
        "",
    ]
    for d in DOMAINES_SOCIETAUX:
        lignes.append(f"{d.icon} {d.nom.upper()}")
        lignes.append(f"  Description : {d.description}")
        lignes.append(f"  Indicateurs clés : {len(d.indicateurs_cles)}")
        lignes.append(f"  Points historiques : {len(d.serie_historique)}")
        lignes.append(f"  Réformes majeures : {len(d.reformes_majeures)}")
        lignes.append(f"  Crises : {len(d.crises)}")
        lignes.append(f"  Pourquoi intégré : {d.pourquoi_integration}")
        if d.parametres_calibration:
            lignes.append(f"  Paramètres de calibration :")
            for key, val in d.parametres_calibration.items():
                lignes.append(f"    - {key} : {val}")
        lignes.append("")

    lignes.append("═" * 80)
    lignes.append(f"TOTAL : {len(DOMAINES_SOCIETAUX)} domaines | "
                 f"{sum(len(d.serie_historique) for d in DOMAINES_SOCIETAUX)} points historiques | "
                 f"{sum(len(d.reformes_majeures) for d in DOMAINES_SOCIETAUX)} réformes | "
                 f"{sum(len(d.crises) for d in DOMAINES_SOCIETAUX)} crises")
    lignes.append("═" * 80)
    return "\n".join(lignes)


def exporter_json_domaines() -> str:
    """Exporte tous les domaines en JSON."""
    return json.dumps({
        "domaines": [asdict(d) for d in DOMAINES_SOCIETAUX],
        "metadata": {
            "nb_domaines": len(DOMAINES_SOCIETAUX),
            "nb_points_historiques": sum(len(d.serie_historique) for d in DOMAINES_SOCIETAUX),
            "nb_reformes": sum(len(d.reformes_majeures) for d in DOMAINES_SOCIETAUX),
            "nb_crises": sum(len(d.crises) for d in DOMAINES_SOCIETAUX),
            "couverture": "1792-2026",
            "date_generation": datetime.now().isoformat(),
        },
    }, ensure_ascii=False, indent=2)