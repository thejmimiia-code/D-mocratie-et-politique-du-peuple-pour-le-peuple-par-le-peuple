"""
simulateur/model.py — Modélisation des 4 strates systémiques interconnectées :
Local (Communes/Dép/Rég), National (État/Sécu/Parlement), Continental (UE/BCE/PDE), Mondial (AFT/Marchés/Spreads).
Données réelles calées à l'instant T (septembre 2026).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


# =============================================================================
# STRATE 1 : ÉCHELON LOCAL (La Cellule de Base Territoriale)
# =============================================================================

@dataclass
class SousSecteurBlocCommunal:
    """Communes et Intercommunalités (EPCI)."""
    depenses_fonctionnement_mde: float = 85.0   # Salaires, crèches, voirie, police municipale
    depenses_investissement_mde: float = 42.0   # Bâtiments scolaires, transition, eau
    dgf_recue_mde: float = 12.2                 # Dotation globale de fonctionnement
    taxe_fonciere_tfpb_mde: float = 39.5        # Produit de la taxe foncière sur les propriétés bâties
    cfe_et_autres_impots_mde: float = 35.0      # Cotisation Foncière des Entreprises, taxe de séjour


@dataclass
class SousSecteurDepartements:
    """Conseils Départementaux (Action sociale et solidarité)."""
    depenses_sociales_obligatoires_mde: float = 44.5  # RSA, APA (aînés), PCH (handicap), ASE (enfance)
    depenses_colleges_et_routes_mde: float = 18.0
    recettes_dmto_droits_mutation_mde: float = 12.5   # "Frais de notaire" (extrêmement volatils)
    fraction_tva_nationale_mde: float = 16.5          # Part de TVA transférée en compensation
    dgf_departementale_mde: float = 10.0


@dataclass
class SousSecteurRegions:
    """Conseils Régionaux (Développement économique, TER, Lycées)."""
    depenses_transports_ter_mde: float = 14.5
    depenses_lycees_formation_mde: float = 18.5
    fraction_tva_regionale_mde: float = 12.0
    fraction_ticpe_mde: float = 8.0
    dgf_regionale_mde: float = 5.0


@dataclass
class SousSecteurChambresConsulaires:
    """Réseau consulaire territorial (CCI, CMA, Chambres d'Agriculture - Établissements Publics Administratifs)."""
    ressortissants_entreprises_milliers: float = 6900.0   # 3,8M CCI + 1,9M CMA + 1,2M CA
    taxe_frais_de_chambres_mde: float = 1.35              # TFC assise sur CFE et taxe additionnelle TFPNB
    taux_survie_pme_locales_pct: float = 68.5             # Taux de pérennité des PME après 5 ans
    taux_insertion_apprentissage_pct: float = 78.0        # Apprentis formés par les CFA et écoles consulaires
    surfaces_agricoles_preservees_pct: float = 98.2       # Rôle CA / CDPENAF contre l'artificialisation des sols


# =============================================================================
# ASSEMBLÉES REPRÉSENTATIVES ET DÉCISIONNELLES (Pouvoirs, Contraintes & Jeux de Force)
# =============================================================================

@dataclass
class AssembleeConseilMunicipal:
    """Les 34 935 Conseils Municipaux (Suffrage universel direct).
    Décident des budgets communaux, des taux de taxe foncière (TFPB) et des services de proximité.
    Soumis à la Règle d'or budgétaire (art. L. 1612-4 du CGCT).
    """
    communes_total: int = 34935
    taux_moyen_tfpb_pct: float = 38.5
    fronde_fiscale_locale_indice: float = 24.0      # 0-100 (explose en cas de baisse de DGF)
    budget_equilibre_regle_dor: bool = True
    taux_revolte_maires_amf_pct: float = 18.0


@dataclass
class AssembleeConseilIntercommunal:
    """Les 1 254 Conseils Communautaires et Métropolitains (EPCI à fiscalité propre).
    Compétences transférées : mobilité urbaine, eau, assainissement, déchets, CFE intercommunale.
    """
    epci_total: int = 1254
    taux_integration_metropolitaine_pct: float = 74.0
    tensions_centre_peripherie_indice: float = 32.0


@dataclass
class AssembleeConseilDepartemental:
    """Les 101 Conseils Départementaux (Suffrage universel binominal paritaire).
    Gestionnaires des solidarités obligatoires : RSA, APA, PCH, ASE.
    Soumis au redoutable 'effet de ciseau' (dépenses rigides vs recettes DMTO effondrées).
    """
    departements_total: int = 101
    indice_effet_ciseau_social: float = 52.0        # Alerte rouge si > 70
    departements_alerte_faillite: int = 14
    depenses_sociales_rsa_apa_mde: float = 44.5
    recettes_dmto_volatiles_mde: float = 12.5


@dataclass
class AssembleeConseilRegional:
    """Les 18 Conseils Régionaux (Suffrage universel direct de liste).
    Stratèges du territoire : TER, lycées, développement économique, CPER État-Région.
    """
    regions_total: int = 18
    depenses_ter_lycees_mde: float = 33.0
    taux_engagement_cper_etat_pct: float = 78.0
    acceptabilite_fusion_doublons_pct: float = 62.0


@dataclass
class AssembleeConsulaireDetail:
    """Les Assemblées Générales Consulaires (CCI, CMA, Chambres d'Agriculture).
    6,9 millions d'entreprises, artisans et agriculteurs représentés.
    Avis consultatifs décisionnels en aménagement commercial (CDAC) et foncier (CDPENAF).
    """
    ressortissants_milliers: float = 6900.0
    cci_confiance_patrons_pct: float = 56.0
    cma_adhesion_artisans_pct: float = 64.0
    ca_adhesion_agricole_pct: float = 52.0
    soutien_allotissement_30pct_pme: float = 88.0


@dataclass
class AssembleeNationaleDetail:
    """Assemblée nationale (577 députés - Suffrage universel direct).
    Cœur décisionnel du pouvoir législatif et du consentement à l'impôt (art. 24, 34, 39, 45, 49).
    """
    sieges_total: int = 577
    sieges_majorite: int = 210                      # Coalition présidentielle / gouvernementale
    sieges_opposition_gauche: int = 180
    sieges_opposition_droite_nat: int = 140
    sieges_independants_pivots: int = 47            # Charnière déterminante en majorité relative
    seuil_majorite_absolue: int = 289
    voix_censure_projetees: int = 265               # Projection du vote de censure art. 49.2
    gouvernement_censure: bool = False              # True si voix_censure >= 289
    recours_49_3_count: int = 0                     # Arme d'adoption forcée sans vote
    taux_adoption_textes_pct: float = 68.0
    climat_parlementaire: str = "Majorité relative sous haute tension"


@dataclass
class AssembleeSenatDetail:
    """Sénat (348 sénateurs - Suffrage universel indirect par les grands électeurs territoriaux).
    Chambre haute, gardien constitutionnel des collectivités territoriales (art. 24 al. 3).
    Détient un VETO ABSOLU sur les révisions constitutionnelles (art. 89).
    """
    sieges_total: int = 348
    sieges_majorite_senatoriale: int = 215          # Droite et Centre
    sieges_opposition_senat: int = 133
    indice_hostilite_senatoriale: float = 30.0      # 0-100 (flambe si coupes dans la DGF des maires)
    veto_reforme_constitutionnelle_art_89: bool = False # Si hostilité > 60, bloque la révision
    taux_accord_cmp_pct: float = 55.0               # Succès des Commissions Mixtes Paritaires
    commissions_enquete_offensives: int = 2         # Pouvoirs d'investigation quasi-judiciaires
    posture_senat: str = "Vigilance territoriale républicaine"


@dataclass
class AssembleeCongresDetail:
    """Congrès du Parlement (925 parlementaires réunis à Versailles).
    Assemblée décisionnelle suprême pour l'approbation des révisions constitutionnelles (art. 89).
    """
    sieges_total: int = 925                         # 577 députés + 348 sénateurs
    seuil_trois_cinquiemes: int = 555               # 60 % des suffrages exprimés
    voix_favorables_projetees: int = 485
    majorite_3_5_atteinte: bool = False
    voie_referendaire_art_11_requise: bool = True   # Voie gaullienne directe


@dataclass
class AssembleeCESEDetail:
    """Conseil Économique, Social et Environnemental (175 membres - art. 70 & 71 Constitution).
    Chambre constitutionnelle de concertation sociale, environnementale et citoyenne.
    """
    membres_total: int = 175
    taux_consensus_social_pct: float = 48.0
    avis_favorables_rendus: int = 6
    petitions_citoyennes_instruites: int = 3        # Droit de saisine citoyenne (150 000 signataires)
    posture_syndicale: str = "Attentisme vigilant"


@dataclass
class AssembleeConventionCitoyenneDetail:
    """Convention Citoyenne / Assemblée de démocratie délibérative (150 citoyens tirés au sort).
    Instance d'élaboration de consensus sans filtre sur les tabous de la société.
    """
    citoyens_tires_au_sort: int = 150
    indice_deliberatif_consensus_pct: float = 84.0
    propositions_clef_en_main: int = 12
    adhesion_populaire_pct: float = 76.0


@dataclass
class AssembleeParlementEuropeenDetail:
    """Parlement Européen (720 députés européens - 81 FR).
    Codécide les directives (TVA taux réduits, CSRD, taxe carbone MACF) et vote le budget de l'UE.
    """
    sieges_total: int = 720
    sieges_france: int = 81
    coalition_majoritaire: str = "Grand Centre (PPE - S&D - Renew)"
    taux_alignement_directives_fr_pct: float = 65.0
    conformite_directive_tva_2022_542: bool = True


@dataclass
class AssembleeConseilUEDetail:
    """Conseil de l'Union Européenne (Conseil des ministres des 27 États).
    Assemblée décisionnelle intergouvernementale (règle de majorité qualifiée : 55% États, 65% pop).
    Déclenche et lève la Procédure de Déficit Excessif (PDE - art. 126 TFUE).
    """
    etats_membres: int = 27
    seuil_majorite_qualifiee_atteint: bool = True
    decision_pde_sanction_active: bool = False


@dataclass
class EchelonLocal:
    """Strate consolidée des Collectivités Territoriales et Acteurs Économiques de Terroir."""
    bloc_communal: SousSecteurBlocCommunal = field(default_factory=SousSecteurBlocCommunal)
    departements: SousSecteurDepartements = field(default_factory=SousSecteurDepartements)
    regions: SousSecteurRegions = field(default_factory=SousSecteurRegions)
    chambres_consulaires: SousSecteurChambresConsulaires = field(default_factory=SousSecteurChambresConsulaires)

    # Assemblées décisionnelles et représentatives locales
    conseil_municipal: AssembleeConseilMunicipal = field(default_factory=AssembleeConseilMunicipal)
    conseil_intercommunal: AssembleeConseilIntercommunal = field(default_factory=AssembleeConseilIntercommunal)
    conseil_departemental: AssembleeConseilDepartemental = field(default_factory=AssembleeConseilDepartemental)
    conseil_regional: AssembleeConseilRegional = field(default_factory=AssembleeConseilRegional)
    assemblees_consulaires: AssembleeConsulaireDetail = field(default_factory=AssembleeConsulaireDetail)

    # Indicateurs consolidés de la strate locale
    dette_locale_totale_mde: float = 252.0
    tension_sociale_territoriale: float = 36.0        # Indice 0-100 (grogne des contribuables et usagers)
    qualite_services_proximite: float = 64.0          # Indice 0-100 (santé de proximité, guichets, transports)


# =============================================================================
# STRATE 2 : ÉCHELON NATIONAL (Le Moteur Institutionnel & Budgétaire)
# =============================================================================

@dataclass
class SousSecteurEtatCentral:
    """Budget général de l'État (APUC)."""
    recettes_fiscales_nettes_mde: float = 345.0       # TVA nette d'État, IR, IS, TICPE résiduelle
    depenses_ministeres_primaires_mde: float = 465.0  # Masse salariale fonctionnaires, Éducation, Défense, Justice
    charge_nette_dette_mde: float = 66.5              # Charge annuelle des intérêts des titres d'État
    deficit_budgetaire_etat_mde: float = 145.0        # Déficit propre du budget de l'État


@dataclass
class SousSecteurSecuriteSociale:
    """Administrations de Sécurité Sociale (ASSO - CNAM, CNAV, CNAF, CNSA)."""
    recettes_cotisations_et_csg_mde: float = 650.0   # Cotisations patronales/salariales, CSG, CRDS
    depenses_prestations_mde: float = 662.0          # Assurance maladie (ONDAM), Retraites, Famille
    deficit_securite_sociale_mde: float = 12.0       # Déficit structurel des régimes de base


@dataclass
class SousSecteurParlement:
    """Climat politique et équilibre des forces à l'Assemblée nationale."""
    sieges_coalition_gouvernementale: int = 210       # Majorité relative (sur 577 sièges)
    seuil_censure_absolue: int = 289                  # Majorité requise pour renverser le gouvernement
    probabilite_motion_censure_pct: float = 52.0      # Risque de censure calculé
    recours_article_49_3_count: int = 0               # Nombre d'utilisations du 49.3


@dataclass
class SousSecteurInstitutionsRepublique:
    """Garanties constitutionnelles, juridictions suprêmes et corps de contrôle républicains."""
    conseil_constitutionnel_conformite_pct: float = 100.0 # Conformité aux décisions DC et QPC (art. 61 et 61-1)
    cour_des_comptes_evaluation_efficience: float = 72.0  # Indice d'efficience et audit des comptes publics (art. 47-2)
    conseil_etat_securite_juridique_pct: float = 96.0     # Taux de validation préalable des projets de lois (art. 39)
    defenseur_des_droits_recours_regles_pct: float = 84.0 # Taux de médiation réussie des usagers (art. 71-1)


@dataclass
class EchelonNational:
    """Strate consolidée de la Nation et de ses Institutions républicaines."""
    pib_nominal_mde: float = 3015.0                   # PIB nominal français à l'instant T
    taux_croissance_potentiel: float = 0.019          # 1,9 % de croissance nominale tendancielle
    etat: SousSecteurEtatCentral = field(default_factory=SousSecteurEtatCentral)
    securite_sociale: SousSecteurSecuriteSociale = field(default_factory=SousSecteurSecuriteSociale)
    parlement: SousSecteurParlement = field(default_factory=SousSecteurParlement)
    institutions: SousSecteurInstitutionsRepublique = field(default_factory=SousSecteurInstitutionsRepublique)

    # Assemblées représentatives et délibératives nationales
    assemblee_nationale: AssembleeNationaleDetail = field(default_factory=AssembleeNationaleDetail)
    senat: AssembleeSenatDetail = field(default_factory=AssembleeSenatDetail)
    congres: AssembleeCongresDetail = field(default_factory=AssembleeCongresDetail)
    cese: AssembleeCESEDetail = field(default_factory=AssembleeCESEDetail)
    convention_citoyenne: AssembleeConventionCitoyenneDetail = field(default_factory=AssembleeConventionCitoyenneDetail)

    # Indicateurs civiques et macro-sociaux
    dette_maastricht_stock_mde: float = 3568.0        # Dette publique consolidée au sens de Maastricht
    confiance_democratique: float = 27.5              # Indice 0-100 (confiance dans les institutions)
    pouvoir_achat_menages_index: float = 100.0        # Base 100


# =============================================================================
# STRATE 3 : ÉCHELON CONTINENTAL / EUROPÉEN (Le Cadre de Contrainte)
# =============================================================================

@dataclass
class EchelonEuropeen:
    """Strate de l'Union Européenne et de la Zone Euro."""
    # Règles budgétaires du Pacte de Stabilité réformé (avril 2024)
    seuil_deficit_pde_pct: float = 3.00               # Plafond de 3.0 % du PIB
    seuil_dette_pacte_pct: float = 60.0               # Plafond de 60.0 % du PIB
    effort_structurel_requis_annuel_pct: float = 0.50 # 0.5 pt de PIB d'effort annuel sous PDE
    statut_pde_actif: bool = True                     # La France est sous procédure de déficit excessif
    amende_sanction_semestrielle_mde: float = 1.50    # 0,05 % du PIB d'astreinte financière

    # Assemblées décisionnelles européennes
    parlement_europeen: AssembleeParlementEuropeenDetail = field(default_factory=AssembleeParlementEuropeenDetail)
    conseil_ue: AssembleeConseilUEDetail = field(default_factory=AssembleeConseilUEDetail)

    # Politique Monétaire de la Banque Centrale Européenne (BCE)
    taux_depot_bce_pct: float = 2.50                  # Taux de référence de la BCE
    quantitative_tightening_actif: bool = True        # La BCE ne réinvestit plus les OAT échues
    bouclier_tpi_bce_eligible: bool = False           # TPI actif UNIQUEMENT si discipline budgétaire respectée

    # Compétitivité et Marché Unique
    competitivite_fiscale_relative: float = 46.0      # Indice 0-100 face à l'Allemagne/Espagne/Italie


# =============================================================================
# STRATE 4 : ÉCHELON MONDIAL (Marchés Financiers, Matières Premières & Géopolitique)
# =============================================================================

@dataclass
class EchelonMondial:
    """Strate des Marchés Financiers Internationaux, Matières Premières, Banques Centrales et AFT."""
    # Structure de détention et refinancement de la dette d'État
    part_dette_detenue_non_residents: float = 0.558   # 55,8 % de la dette d'État entre les mains de non-résidents
    maturite_moyenne_dette_ans: float = 8.5           # Durée de vie moyenne du portefeuille de l'AFT
    besoin_financement_brut_annuel_mde: float = 435.0 # ~285 Md€ dette échue à renouveler + ~150 Md€ déficit

    # Taux, Spreads et Notation financière souveraine
    taux_oat_france_10ans: float = 4.18               # Taux souverain à 10 ans de la France
    taux_bund_allemagne_10ans: float = 3.30           # Taux sans risque allemand
    spread_oat_bund_bps: float = 88.0                 # Écart de taux en points de base (88 bps)
    note_souveraine: str = "AA-"                      # Notation financière S&P / Fitch / Moody's (Aa3)
    prime_risque_politique_bps: float = 25.0          # Prime de risque spécifique liée aux incertitudes

    # Marchés Mondiaux de l'Énergie & Matières Premières (Commodities)
    cours_petrole_brent_usd: float = 82.5             # Prix du baril de Brent (USD/baril)
    cours_gaz_naturel_ttf_eur_mwh: float = 38.0       # Gaz TTF de référence européen (€/MWh)
    prix_tonne_carbone_ets_eur: float = 72.0          # Quota Système d'échange de quotas d'émission UE (€/t CO2)
    facture_energetique_nette_mde: float = 64.5       # Solde déficitaire des importations nettes d'énergie (Md€/an)

    # Système Monétaire International & Banques Centrales
    taux_directeur_fed_pct: float = 5.33              # Taux Fed Funds target aux États-Unis (%)
    taux_directeur_bce_depot_pct: float = 3.75         # Taux de facilité de dépôt BCE (%)
    taux_change_eur_usd: float = 1.08                 # Parité de change EUR/USD ($ par €)
    indice_fret_maritime_scfi: float = 2450.0         # Shanghai Containerized Freight Index (SCFI)

    # Commerce International & Réglementations Globales
    taux_imposition_pilier2_ocde_pct: float = 15.0    # Accord OCDE Pilier 2 - Impôt minimum mondial (CGI art. 223 VJ)
    croissance_commerce_mondial_pct: float = 2.8      # Croissance en volume du commerce mondial (%)

    # Transmission à l'économie réelle
    taux_credit_immobilier_menages: float = 3.85      # Impact direct de l'OAT sur le crédit aux particuliers
    taux_credit_pme_entreprises: float = 4.90         # Coût d'emprunt des PME françaises
    inflation_globale_pct: float = 2.1                # Taux d'inflation globale répercuté (IPC France)


# =============================================================================
# CYCLE DE VIE ET 3 GÉNÉRATIONS (Dynamiques et Flux Croisés)
# =============================================================================

@dataclass
class CohorteGeneration1Seniors:
    """Génération 1 : Aînés et Retraités (65 à 95+ ans).
    Piliers de la mémoire républicaine, détenteurs du patrimoine foncier, engagés dans le bénévolat
    associatif et les mandats de maires ruraux, mais confrontés à la perte d'autonomie et au reste à charge d'EHPAD.
    """
    population_millions: float = 14.6
    pension_moyenne_mensuelle_euros: float = 1620.0
    taux_pauvrete_pct: float = 10.8
    part_patrimoine_national_pct: float = 61.5
    depenses_sante_ald_mde: float = 112.0
    depenses_apa_dependance_mde: float = 14.5
    garde_enfants_benevole_mde: float = 18.0          # Économie collective estimée de la garde des petits-enfants
    taux_maintien_domicile_satisfaisant: float = 58.0 # % des aînés satisfaits de l'aide à domicile


@dataclass
class CohorteGeneration2Actifs:
    """Génération 2 : Actifs et Parents (35 à 64 ans).
    Le cœur productif et fiscal de la Nation. Subit la contrainte de la 'génération sandwich' :
    doit financer à la fois les études et le logement des enfants (G3) tout en assumant la charge morale
    et le reste à charge d'EHPAD des parents âgés dépendants (G1).
    """
    population_millions: float = 26.2
    actifs_occupes_millions: float = 22.4
    salaire_moyen_mensuel_euros: float = 2650.0
    taux_pauvrete_pct: float = 13.2
    cotisations_sociales_versees_mde: float = 345.0
    impots_directs_verses_mde: float = 125.0
    indice_charge_sandwich: float = 68.0              # 0 à 100 : tension subie simultanément pour G1 et G3
    taux_emploi_seniors_55_64_pct: float = 56.5       # Emploi des seniors (56,5 % en France vs 72 % All.)
    proches_aidants_millions: float = 4.5             # 4,5M d'actifs aidant un parent vulnérable


@dataclass
class CohorteGeneration3Jeunesse:
    """Génération 3 : Enfants, Scolaires, Étudiants et Jeunes Travailleurs (0 à 34 ans).
    L'avenir de la Nation. Fragilisée par la précarité étudiante, le coût exorbitant du logement,
    l'accès difficile au premier emploi et le fardeau de la dette souveraine léguée sans compensation.
    """
    population_millions: float = 27.6
    scolaires_etudiants_millions: float = 15.2
    taux_pauvrete_pct: float = 19.4                   # 19,4 % sous le seuil de pauvreté (alerte républicaine)
    taux_chomage_jeunes_pct: float = 17.5             # % des 15-24 ans actifs au chômage
    depense_education_recue_mde: float = 165.0        # Budget consolidé Éducation État + Collectivités
    part_loyer_dans_budget_pct: float = 38.5          # Poids écrasant du loyer dans le reste à vivre
    taux_abstention_electorale_pct: float = 61.8      # Abstention aux scrutins législatifs et régionaux
    indice_acces_propriete: float = 28.0              # 0 à 100 : barrière à l'accession sans dotation familiale


@dataclass
class FluxCroisesIntergenerationnels:
    """Matrice des flux croisés financiers, démographiques, patrimoniaux et de soin (Care)."""
    transfert_retraites_g2_vers_g1_mde: float = 360.0 # Cotisations vieillesse payées par les actifs
    transfert_sante_g2_vers_g1_mde: float = 95.0      # Part CSG/cotisations finançant les soins des 60+ ans
    transfert_education_g2_vers_g3_mde: float = 165.0 # Investissement éducatif mutualisé
    transfert_aide_familiale_g2_vers_g3_mde: float = 48.0 # Pensions alimentaires et hébergement familial
    transfert_garde_enfants_g1_vers_g3_mde: float = 18.0  # Garde bénévole (1,2 million de places équivalentes)
    transfert_successions_g1_vers_g2_mde: float = 225.0   # Successions à 52 ans en moyenne
    transfert_donations_g1_vers_g3_mde: float = 75.0      # Donations directes vers les petits-enfants
    ratio_dependance_demographique: float = 0.65       # (Inactifs G1 + G3) / Actifs G2
    indice_harmonie_intergenerationnelle: float = 42.0 # Indice composite d'équité 0 à 100
    charge_dette_par_jeune_euros: float = 129275.0     # Stock de dette publique / population G3


@dataclass
class StrateCycleDeVieEtGenerations:
    """Modèle consolidé des 3 générations et des flux croisés de solidarité."""
    g1_seniors: CohorteGeneration1Seniors = field(default_factory=CohorteGeneration1Seniors)
    g2_actifs: CohorteGeneration2Actifs = field(default_factory=CohorteGeneration2Actifs)
    g3_jeunesse: CohorteGeneration3Jeunesse = field(default_factory=CohorteGeneration3Jeunesse)
    flux_croises: FluxCroisesIntergenerationnels = field(default_factory=FluxCroisesIntergenerationnels)


# =============================================================================
# VECTEUR DE DÉCISION & RÉSULTAT CONSOLIDÉ
# =============================================================================

@dataclass
class DecisionPolitique:
    """Vecteur de politique publique appliqué pour une année donnée."""
    annee: int = 1
    description: str = "Décision annuelle"

    # Nouvelles recettes fiscales de régulation (Md€)
    recettes_fraude_ia_mde: float = 0.0
    conditionnement_aides_entreprises_mde: float = 0.0
    taxe_superprofits_rachats_mde: float = 0.0
    extension_ttf_mde: float = 0.0
    recettes_pilier2_ocde_mde: float = 0.0            # Recette fiscale : impôt minimum mondial 15% (CGI 223 VJ)
    recettes_macf_carbone_mde: float = 0.0            # Recette : Mécanisme d'ajustement carbone aux frontières (UE)

    # Économies structurelles & fonctionnement (Md€)
    fusion_doublons_territoriaux_mde: float = 0.0
    commande_publique_massifiee_mde: float = 0.0
    extinction_niches_inefficaces_mde: float = 0.0
    fraude_sociale_criminelle_mde: float = 0.0

    # Restitution pouvoir d'achat (Md€)
    baisse_tva_energie_5_5_mde: float = 0.0

    # Réformes institutionnelles & démocratiques (bool)
    reforme_casier_b2: bool = False
    reforme_vote_blanc_invalidant: bool = False
    reforme_ric_souverain: bool = False
    reforme_fin_regimes_speciaux: bool = False
    reforme_anti_pantouflage_lobbys: bool = False
    reforme_non_cumul_mandats: bool = False

    # Politiques d'équité intergénérationnelle & Cycle de Vie
    reforme_dotation_emancipation_jeunesse: bool = False      # Dotation 10 000 € à 18 ans (études/permis/caution)
    soutien_proches_aidants_autonomie_mde: float = 0.0        # Budget dédié soulageant G2 et renforçant l'APA de G1
    incitation_donations_intergenerationnelles: bool = False  # Abattement fiscal ciblé pour dons de G1 vers G3

    # Transferts financiers aux collectivités (DGF)
    delta_dotation_dgf_mde: float = 0.0

    # Chocs et variables macro-financières exogènes mondiales
    choc_petrole_brent_usd: float = 0.0               # Exogène : variation du baril (ex: +25 $/bbl)
    choc_taux_fed_bps: float = 0.0                    # Exogène : resserrement Fed en bps (ex: +50 bps)
    choc_change_eur_usd: float = 0.0                  # Exogène : variation de la parité (ex: -0.08)


@dataclass
class ResultatEtapeSimulation:
    """Instantané complet des 4 strates après propagation systémique."""
    annee: int
    pib_nominal_mde: float

    # Échelon National
    deficit_nominal_mde: float
    ratio_deficit_pib: float
    dette_nominale_mde: float
    ratio_dette_pib: float
    charge_dette_mde: float
    recettes_publiques_totales_mde: float
    depenses_publiques_totales_mde: float
    pouvoir_achat_index: float
    confiance_democratique: float
    risque_censure_parlement: float

    # Échelon Local
    tension_sociale_locale: float
    qualite_services_proximite: float
    produit_taxe_fonciere_mde: float

    # Échelon Européen
    statut_pde_europe: bool
    bouclier_tpi_actif: bool
    sanction_financiere_ue: bool

    # Échelon Mondial
    taux_oat_pct: float
    spread_bund_bps: float
    note_souveraine: str
    taux_credit_pme: float
    cours_petrole_usd: float = 82.5
    taux_change_eur_usd: float = 1.08
    facture_energetique_mde: float = 64.5
    inflation_globale_pct: float = 2.1

    # Dynamiques des Assemblées Représentatives et Décisionnelles
    voix_censure_an: int = 265                        # Assemblée nationale : projection motion de censure art. 49.2
    gouvernement_censure: bool = False                # Vrai si voix_censure_an >= 289
    climat_assemblee_nationale: str = "Majorité relative tendue"
    hostilite_senat_indice: float = 30.0              # Sénat : indice d'hostilité (défense des collectivités)
    senat_veto_art_89: bool = False                   # Veto constitutionnel absolu du Sénat sur l'article 89
    congres_majorite_3_5: bool = False                # Majorité qualifiée des 3/5èmes au Congrès de Versailles
    departements_alerte_ciseau: int = 14              # Conseils départementaux : départements en crise financière
    fronde_maires_indice: float = 24.0                # Conseils municipaux : indice de grogne des maires (AMF)
    pe_taux_alignement: float = 65.0                  # Parlement Européen : soutien de coalition aux directives
    cese_consensus_social: float = 48.0               # CESE : taux d'adhésion syndicale et socioprofessionnelle
    consulaire_confiance_pme: float = 56.0            # Chambres consulaires : confiance patrons PME et artisans
    convention_citoyenne_consensus: float = 84.0      # Convention citoyenne tirée au sort : consensus délibératif

    # Dynamiques du Cycle de Vie et des 3 Générations
    g1_seniors_pop_m: float = 14.6                    # Génération 1 (65+) en millions
    g2_actifs_pop_m: float = 26.2                     # Génération 2 (35-64) en millions
    g3_jeunesse_pop_m: float = 27.6                   # Génération 3 (0-34) en millions
    ratio_dependance_demographique: float = 0.65      # Ratio inactifs (G1+G3) / Actifs occupés G2
    indice_harmonie_intergenerationnelle: float = 42.0 # Score d'équité intergénérationnelle (0-100)
    g2_charge_sandwich_indice: float = 68.0           # Fardeau de la génération sandwich G2 (0-100)
    g3_taux_pauvrete_pct: float = 19.4                # Taux de pauvreté de la jeunesse (G3)
    g1_taux_pauvrete_pct: float = 10.8                # Taux de pauvreté des aînés (G1)
    transfert_retraites_mde: float = 360.0            # Cotisations retraites G2 -> G1
    transfert_education_mde: float = 165.0            # Budget éducation & enseignement supérieur G2 -> G3
    donations_vers_g3_mde: float = 75.0               # Flux de transmission patrimoniale directe vers G3
    garde_enfants_grands_parents_mde: float = 18.0    # Valeur économique de la garde bénévole G1 -> G3
    charge_dette_par_jeune_euros: float = 129275.0    # Fardeau de dette publique pesant sur chaque citoyen de G3

    commentaires: List[str] = field(default_factory=list)

    @property
    def generations(self) -> "StrateCycleDeVieEtGenerations":
        """Reconstitue la vue détaillée de la strate intergénérationnelle."""
        return StrateCycleDeVieEtGenerations(
            g1_seniors=CohorteGeneration1Seniors(
                population_millions=self.g1_seniors_pop_m,
                taux_pauvrete_pct=self.g1_taux_pauvrete_pct,
                garde_enfants_benevole_mde=self.garde_enfants_grands_parents_mde,
            ),
            g2_actifs=CohorteGeneration2Actifs(
                population_millions=self.g2_actifs_pop_m,
                indice_charge_sandwich=self.g2_charge_sandwich_indice,
            ),
            g3_jeunesse=CohorteGeneration3Jeunesse(
                population_millions=self.g3_jeunesse_pop_m,
                taux_pauvrete_pct=self.g3_taux_pauvrete_pct,
                depense_education_recue_mde=self.transfert_education_mde,
            ),
            flux_croises=FluxCroisesIntergenerationnels(
                transfert_retraites_g2_vers_g1_mde=self.transfert_retraites_mde,
                transfert_education_g2_vers_g3_mde=self.transfert_education_mde,
                transfert_donations_g1_vers_g3_mde=self.donations_vers_g3_mde,
                transfert_garde_enfants_g1_vers_g3_mde=self.garde_enfants_grands_parents_mde,
                ratio_dependance_demographique=self.ratio_dependance_demographique,
                indice_harmonie_intergenerationnelle=self.indice_harmonie_intergenerationnelle,
                charge_dette_par_jeune_euros=self.charge_dette_par_jeune_euros,
            ),
        )
