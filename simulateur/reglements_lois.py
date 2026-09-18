"""
simulateur/reglements_lois.py — Registre programmatique intégral des textes de lois et règlements.
Permet d'interroger les articles de lois et leurs contraintes mathématiques dans le simulateur.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ArticleDeLoi:
    identifiant: str
    code_ou_traite: str
    article: str
    titre: str
    texte_integral: str
    strate_impactee: str  # "Local", "National", "Europe", "Mondial", "Transversal"
    effet_simulation: str


REGISTRE_LEGAL: Dict[str, ArticleDeLoi] = {
    # -------------------------------------------------------------------------
    # BLOC CONSTITUTIONNEL
    # -------------------------------------------------------------------------
    "CONST_ART_2": ArticleDeLoi(
        identifiant="CONST_ART_2",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 2, alinéa 5",
        titre="Principe républicain fondamental",
        texte_integral="Son principe est : gouvernement du peuple, par le peuple et pour le peuple.",
        strate_impactee="Transversal",
        effet_simulation="Légitime la souveraineté citoyenne directe, l'usage du RIC et la transparence des comptes.",
    ),
    "CONST_ART_3": ArticleDeLoi(
        identifiant="CONST_ART_3",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 3",
        titre="Souveraineté nationale et voies d'exercice",
        texte_integral="La souveraineté nationale appartient au peuple qui l'exerce par ses représentants et par la voie du référendum. Aucune section du peuple ni aucun individu ne peut s'en attribuer l'exercice.",
        strate_impactee="National",
        effet_simulation="Interdit la confiscation du pouvoir législatif par des oligarchies ou lobbies financiers.",
    ),
    "CONST_ART_11": ArticleDeLoi(
        identifiant="CONST_ART_11",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 11",
        titre="Référendum législatif direct",
        texte_integral="Le Président de la République peut soumettre au référendum tout projet de loi portant sur l'organisation des pouvoirs publics, sur des réformes relatives à la politique économique ou sociale de la nation et aux services publics qui y concourent.",
        strate_impactee="National",
        effet_simulation="Permet l'adoption directe par le peuple des réformes de fiscalité de l'énergie et de probité.",
    ),
    "CONST_ART_49_2": ArticleDeLoi(
        identifiant="CONST_ART_49_2",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 49, alinéa 2",
        titre="Motion de censure de l'Assemblée nationale",
        texte_integral="L'Assemblée nationale met en cause la responsabilité du Gouvernement par le vote d'une motion de censure. Une telle motion n'est recevable que si elle est signée par un dixième au moins des membres de l'Assemblée nationale. Seuls sont recensés les votes favorables à la motion de censure qui ne peut être adoptée qu'à la majorité des membres composant l'Assemblée.",
        strate_impactee="National",
        effet_simulation="Chute du gouvernement si 289 députés votent la censure, modélisée par le basculement des indépendants sous forte tension locale.",
    ),
    "CONST_ART_49_3": ArticleDeLoi(
        identifiant="CONST_ART_49_3",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 49, alinéa 3",
        titre="Engagement de responsabilité gouvernementale sans vote",
        texte_integral="Le Premier ministre peut engager la responsabilité du Gouvernement devant l'Assemblée nationale sur le vote d'un projet de loi de finances ou de financement de la sécurité sociale. Le projet est considéré comme adopté sauf si une motion de censure est votée.",
        strate_impactee="National",
        effet_simulation="En l'absence de majorité absolue, son déclenchement augmente le risque de censure si la tension sociale locale > 65/100.",
    ),
    "DDHC_ART_6": ArticleDeLoi(
        identifiant="DDHC_ART_6",
        code_ou_traite="Déclaration des Droits de l'Homme et du Citoyen de 1789",
        article="Article 6",
        titre="Égalité d'accès aux dignités et emplois publics selon les vertus",
        texte_integral="Tous les Citoyens étant égaux à ses yeux sont également admissibles à toutes dignités, places et emplois publics, selon leur capacité, et sans autre distinction que celle de leurs vertus et de leurs talents.",
        strate_impactee="National",
        effet_simulation="Fonde constitutionnellement l'exigence d'un casier judiciaire B2 vierge pour concourir à un mandat.",
    ),
    "CC_2017_752_DC": ArticleDeLoi(
        identifiant="CC_2017_752_DC",
        code_ou_traite="Jurisprudence du Conseil constitutionnel",
        article="Décision n° 2017-752 DC du 8 septembre 2017",
        titre="Conformité des peines d'inéligibilité obligatoire avec dispense motivée du juge",
        texte_integral="Le législateur peut instaurer une peine d'inéligibilité obligatoire liée à des infractions à la probité, dès lors que le juge conserve le pouvoir d'exonération par décision motivée.",
        strate_impactee="National",
        effet_simulation="Sécurise à 100 % le filtre automatisé du casier B2 contre tout risque d'annulation constitutionnelle.",
    ),

    # -------------------------------------------------------------------------
    # PROBITÉ & CODE PÉNAL
    # -------------------------------------------------------------------------
    "CP_432_10": ArticleDeLoi(
        identifiant="CP_432_10",
        code_ou_traite="Code pénal",
        article="Article 432-10",
        titre="De la concussion publique",
        texte_integral="Le fait, par une personne dépositaire de l'autorité publique, d'ordonner de percevoir des droits indus est puni de cinq ans d'emprisonnement et 500 000 € d'amende.",
        strate_impactee="National",
        effet_simulation="Inéligibilité automatique du candidat en cas de condamnation inscrite au B2.",
    ),
    "CP_432_11": ArticleDeLoi(
        identifiant="CP_432_11",
        code_ou_traite="Code pénal",
        article="Article 432-11",
        titre="De la corruption passive et du trafic d'influence",
        texte_integral="Le fait, par une personne investie d'un mandat électif public, de solliciter ou d'agréer des avantages pour accomplir ou s'abstenir d'accomplir un acte de sa fonction est puni de dix ans d'emprisonnement et 1 000 000 € d'amende.",
        strate_impactee="National",
        effet_simulation="Inéligibilité automatique et inconditionnelle.",
    ),
    "CP_432_12": ArticleDeLoi(
        identifiant="CP_432_12",
        code_ou_traite="Code pénal",
        article="Article 432-12",
        titre="De la prise illégale d'intérêts",
        texte_integral="Le fait de prendre un intérêt quelconque dans une entreprise sous sa surveillance ou liquidation est puni de cinq ans d'emprisonnement et 500 000 € d'amende.",
        strate_impactee="National",
        effet_simulation="Exclusion des fonctions exécutives et électives.",
    ),
    "CP_131_26_2": ArticleDeLoi(
        identifiant="CP_131_26_2",
        code_ou_traite="Code pénal",
        article="Article 131-26-2",
        titre="Peine complémentaire obligatoire d'inéligibilité",
        texte_integral="Le prononcé de la peine complémentaire d'inéligibilité est obligatoire à l'encontre de toute personne coupable d'un délit de concussion, corruption, prise illégale d'intérêts, favoritisme ou détournement de fonds publics.",
        strate_impactee="National",
        effet_simulation="Filtre automatisé du casier B2 écartant impérativement les candidats condamnés pour manquement à la probité.",
    ),
    "CGI_1741": ArticleDeLoi(
        identifiant="CGI_1741",
        code_ou_traite="Code général des impôts",
        article="Article 1741",
        titre="Délit général de fraude fiscale aggravée",
        texte_integral="Quiconque s'est frauduleusement soustrait au paiement total ou partiel de l'impôt est puni de cinq ans d'emprisonnement et 500 000 € d'amende (sept ans et 3 000 000 € en bande organisée).",
        strate_impactee="National",
        effet_simulation="Gisement récupéré par les algorithmes GNN (+10 Md€/an) et inéligibilité des fraudeurs fiscaux.",
    ),

    # -------------------------------------------------------------------------
    # FINANCES LOCALES & RÈGLE D'OR (CGCT)
    # -------------------------------------------------------------------------
    "CGCT_L1612_4": ArticleDeLoi(
        identifiant="CGCT_L1612_4",
        code_ou_traite="Code général des collectivités territoriales",
        article="Article L. 1612-4",
        titre="Règle d'or de l'équilibre réel budgétaire des collectivités",
        texte_integral="Le budget de la collectivité territoriale est en équilibre réel lorsque la section de fonctionnement et la section d'investissement sont respectivement votées en équilibre, l'emprunt étant interdit pour financer le fonctionnement.",
        strate_impactee="Local",
        effet_simulation="Toute baisse de DGF de l'État force une hausse de taxe foncière de 94 % de la perte subie.",
    ),
    "CGCT_L2334_1": ArticleDeLoi(
        identifiant="CGCT_L2334_1",
        code_ou_traite="Code général des collectivités territoriales",
        article="Article L. 2334-1 et suivants",
        titre="Dotation Globale de Fonctionnement (DGF)",
        texte_integral="Fixe les critères de répartition des 27,2 milliards d'euros de DGF versée par l'État aux communes et EPCI.",
        strate_impactee="Local",
        effet_simulation="Sanctuarisée dans le plan de mandature pour préserver les services de proximité ruraux.",
    ),

    # -------------------------------------------------------------------------
    # FISCALITÉ, AIDES & MARCHÉS FINANCIERS
    # -------------------------------------------------------------------------
    "LPF_L81": ArticleDeLoi(
        identifiant="LPF_L81",
        code_ou_traite="Livre des procédures fiscales",
        article="Article L. 81",
        titre="Droit de communication de l'administration fiscale",
        texte_integral="Permet aux agents du fisc d'obtenir les relevés de comptes et données auprès des banques et organismes tiers.",
        strate_impactee="National",
        effet_simulation="Étendu aux passerelles de paiement (PSP) pour les transactions transfrontalières > 50 000 €.",
    ),
    "CGI_235_TER_ZD": ArticleDeLoi(
        identifiant="CGI_235_TER_ZD",
        code_ou_traite="Code général des impôts",
        article="Article 235 ter ZD",
        titre="Taxe sur les Transactions Financières (TTF)",
        texte_integral="Taxe de 0,3 % sur les acquisitions de titres de sociétés françaises cotées de plus d'1 Md€ de capitalisation.",
        strate_impactee="Mondial",
        effet_simulation="Étendue au trading haute fréquence (>80% d'annulations) et prélevée au dépositaire Euroclear (+5 Md€/an).",
    ),
    "ENV_L229_25": ArticleDeLoi(
        identifiant="ENV_L229_25",
        code_ou_traite="Code de l'environnement",
        article="Article L. 229-25",
        titre="Bilan d'émissions de gaz à effet de serre (BEGES)",
        texte_integral="Obligation légale pour les entreprises de plus de 500 salariés de publier leur bilan carbone et plan de transition.",
        strate_impactee="National",
        effet_simulation="Condition d'éligibilité automatisée par API pour maintenir le versement des aides publiques.",
    ),

    # -------------------------------------------------------------------------
    # COMMANDE PUBLIQUE & CONSOMMATION
    # -------------------------------------------------------------------------
    "CCP_L2113_10": ArticleDeLoi(
        identifiant="CCP_L2113_10",
        code_ou_traite="Code de la commande publique",
        article="Article L. 2113-10",
        titre="Obligation légale d'allotissement des marchés publics",
        texte_integral="Les marchés sont obligatoirement passés en lots séparés pour susciter la plus large concurrence.",
        strate_impactee="Local",
        effet_simulation="Empêche les monopoles multinationaux et réserve au moins 30 % des lots aux PME locales.",
    ),
    "CCP_L2112_2": ArticleDeLoi(
        identifiant="CCP_L2112_2",
        code_ou_traite="Code de la commande publique",
        article="Article L. 2112-2",
        titre="Critères environnementaux et circuits courts",
        texte_integral="Permet d'imposer des conditions d'exécution fondées sur la réduction de l'empreinte carbone de transport.",
        strate_impactee="Local",
        effet_simulation="Protège légalement les artisans et agriculteurs de proximité dans les cantines et chantiers publics.",
    ),
    "CONSO_L470_2": ArticleDeLoi(
        identifiant="CONSO_L470_2",
        code_ou_traite="Code de la consommation",
        article="Article L. 470-2",
        titre="Sanction administrative pour marge indue et non-répercussion fiscale",
        texte_integral="Amende administrative prononcée par la DGCCRF égale à 150 % des sommes indûment perçues.",
        strate_impactee="National",
        effet_simulation="Verrouille la baisse de TVA énergie pour qu'elle profite à 100 % aux ménages sans captation par les fournisseurs.",
    ),

    # -------------------------------------------------------------------------
    # DROIT EUROPÉEN & SOUVERAINETÉ NUMÉRIQUE
    # -------------------------------------------------------------------------
    "DIR_TVA_2022_542": ArticleDeLoi(
        identifiant="DIR_TVA_2022_542",
        code_ou_traite="Union Européenne — Directive (UE) 2022/542 du Conseil",
        article="Annexe III, Point 22",
        titre="Taux réduit de TVA jusqu'à 5,5 % sur l'électricité et le gaz naturel",
        texte_integral="Autorise expressément chaque État membre de l'UE à appliquer un taux réduit de TVA jusqu'à 5,5 % sur la livraison d'électricité, de gaz naturel et de chaleur urbaine.",
        strate_impactee="Européen",
        effet_simulation="Garantit la conformité européenne totale de la baisse de TVA de 20 % à 5,5 % (-9 Md€/an).",
    ),
    "TFUE_ART_126": ArticleDeLoi(
        identifiant="TFUE_ART_126",
        code_ou_traite="Traité sur le Fonctionnement de l'Union Européenne",
        article="Article 126 & Protocole n° 12",
        titre="Procédure concernant les déficits excessifs (PDE)",
        texte_integral="Fixe le plafond de déficit public à 3,0 % du PIB et le ratio de dette à 60,0 % du PIB.",
        strate_impactee="Européen",
        effet_simulation="Sous le pacte 2024, déclenche une astreinte semestrielle de 0,05 % du PIB si l'effort annuel < 0,5 pt.",
    ),
    "REG_EIDAS_910_2014": ArticleDeLoi(
        identifiant="REG_EIDAS_910_2014",
        code_ou_traite="Règlement (UE) n° 910/2014 (eIDAS)",
        article="Articles 8 et 9",
        titre="Niveaux de garantie de l'identification électronique sécurisée",
        texte_integral="Définit les exigences du niveau de garantie 'Élevé' pour l'authentification numérique étatique.",
        strate_impactee="National",
        effet_simulation="Garantit l'immunité et l'inviolabilité des votes du RIC via FranceConnect+.",
    ),
    "OCDE_PILIER_2_CGI_223_VJ": ArticleDeLoi(
        identifiant="OCDE_PILIER_2_CGI_223_VJ",
        code_ou_traite="Code Général des Impôts & Directive (UE) 2022/2523",
        article="Art. 223 VJ et suiv. du CGI",
        titre="Imposition minimale mondiale des groupes multinationaux (Pilier 2 de l'OCDE)",
        texte_integral="Instaure un impôt complémentaire garantissant un niveau minimum effectif d'imposition de 15 % sur les bénéfices des groupes multinationaux et nationaux de grande envergure réalisant plus de 750 M€ de CA.",
        strate_impactee="Mondial",
        effet_simulation="Alimente les recettes fiscales internationales de régulation et assainit la concurrence avec les PME territoriales.",
    ),
    "REG_UE_2023_956_MACF": ArticleDeLoi(
        identifiant="REG_UE_2023_956_MACF",
        code_ou_traite="Règlement (UE) 2023/956 du Parlement européen et du Conseil",
        article="Règlement (UE) 2023/956",
        titre="Mécanisme d'Ajustement Carbone aux Frontières (MACF / CBAM)",
        texte_integral="Met en place un mécanisme d'égalisation du coût du carbone entre la production industrielle européenne soumise à l'ETS et les importations en provenance de pays tiers sans tarification carbone.",
        strate_impactee="Mondial",
        effet_simulation="Protège les filières industrielles nationales, stimule la décarbonation et génère des recettes de certificats carbone.",
    ),
    "BALE_III_REG_575_2013": ArticleDeLoi(
        identifiant="BALE_III_REG_575_2013",
        code_ou_traite="Règlement (UE) n° 575/2013 (CRR) - Accords de Bâle III / Bâle IV",
        article="Règlement CRR art. 92 & 114",
        titre="Exigences prudentielles et pondération des risques souverains bancaires",
        texte_integral="Fixe les ratios de fonds propres CET1 (Common Equity Tier 1) et encadre l'exposition des bilans bancaires aux titres de dette souveraine.",
        strate_impactee="Mondial",
        effet_simulation="Sensibilise le refinancement bancaire et le crédit aux PME au spread des obligations souveraines (OAT).",
    ),
    "OMC_GATT_ART_XX": ArticleDeLoi(
        identifiant="OMC_GATT_ART_XX",
        code_ou_traite="Accord général sur les tarifs douaniers et le commerce (GATT / OMC)",
        article="Article XX (Exceptions générales)",
        titre="Exceptions environnementales et de protection des ressources naturelles épuisables",
        texte_integral="Autorise des mesures dérogeant au libre-échange strict si elles sont nécessaires à la protection de la santé et de la vie des personnes ou à la conservation des ressources naturelles.",
        strate_impactee="Mondial",
        effet_simulation="Sécurise juridiquement l'allotissement écologique et les critères de proximité dans la commande publique.",
    ),
    "CONST_ART_24": ArticleDeLoi(
        identifiant="CONST_ART_24",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 24",
        titre="Attributions du Parlement et représentation des collectivités par le Sénat",
        texte_integral="Le Parlement vote la loi. Il contrôle l'action du Gouvernement. Il évalue les politiques publiques. Le Sénat assure la représentation des collectivités territoriales de la République.",
        strate_impactee="National",
        effet_simulation="Fonde le bicamérisme et le rôle protecteur du Sénat envers les finances locales des communes et départements.",
    ),
    "CONST_ART_47_2": ArticleDeLoi(
        identifiant="CONST_ART_47_2",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 47-2",
        titre="Mission constitutionnelle de la Cour des comptes",
        texte_integral="La Cour des comptes assiste le Parlement et le Gouvernement dans le contrôle de l'action du Gouvernement et l'exécution des lois de finances et de financement de la sécurité sociale.",
        strate_impactee="National",
        effet_simulation="Fournit les audits indépendants fondant les 24 Md€ d'économies structurelles sur les doublons et niches inefficaces.",
    ),
    "CONST_ART_61_1": ArticleDeLoi(
        identifiant="CONST_ART_61_1",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 61-1",
        titre="Question Prioritaire de Constitutionnalité (QPC)",
        texte_integral="Lorsque, à l'occasion d'une instance en cours devant une juridiction, il est soutenu qu'une disposition législative porte atteinte aux droits et libertés que la Constitution garantit, le Conseil constitutionnel peut être saisi.",
        strate_impactee="National",
        effet_simulation="Permet aux citoyens et entreprises de purger toute loi attentatoire aux droits fondamentaux ou libertés publiques.",
    ),
    "CONST_ART_71_1": ArticleDeLoi(
        identifiant="CONST_ART_71_1",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 71-1",
        titre="Statut et attributions du Défenseur des droits",
        texte_integral="Le Défenseur des droits veille au respect des droits et libertés par les administrations de l'État, les collectivités territoriales, les établissements publics et tout organisme investi d'une mission de service public.",
        strate_impactee="National",
        effet_simulation="Protège les administrés contre les dysfonctionnements des caisses sociales et services publics de proximité.",
    ),
    "DDHC_ART_14": ArticleDeLoi(
        identifiant="DDHC_ART_14",
        code_ou_traite="Déclaration des Droits de l'Homme et du Citoyen de 1789",
        article="Article 14",
        titre="Consentement démocratique à l'impôt et contrôle de son emploi",
        texte_integral="Tous les Citoyens ont le droit de constater, par eux-mêmes ou par leurs représentants, la nécessité de la contribution publique, de la consentir librement, d'en suivre l'emploi, et d'en déterminer la quotité, l'assiette, le recouvrement et la durée.",
        strate_impactee="Transversal",
        effet_simulation="Légitime la transparence budgétaire absolue et l'affectation prioritaire des impôts au service public.",
    ),
    "CHARTE_ENV_ART_1": ArticleDeLoi(
        identifiant="CHARTE_ENV_ART_1",
        code_ou_traite="Charte de l'environnement de 2004",
        article="Article 1er",
        titre="Droit à un environnement équilibré et respectueux de la santé",
        texte_integral="Chacun a le droit de vivre dans un environnement équilibré et respectueux de la santé.",
        strate_impactee="National",
        effet_simulation="Conditionne le versement des aides publiques aux entreprises à leur bilan carbone certifié (Smart Clearing BEGES).",
    ),
    "CRPA_L123_1": ArticleDeLoi(
        identifiant="CRPA_L123_1",
        code_ou_traite="Code des relations entre le public et l'administration",
        article="Article L. 123-1 (Loi ESSOC)",
        titre="Droit à l'erreur des usagers et contribuables de bonne foi",
        texte_integral="Une personne ayant méconnu pour la première fois une règle applicable à sa situation ne peut faire l'objet d'une sanction pécuniaire si elle a régularisé sa situation de bonne foi.",
        strate_impactee="National",
        effet_simulation="Distingue la simple erreur administrative des ménages/artisans de la grande fraude fiscale organisée délibérée.",
    ),
    "CCOM_L710_1": ArticleDeLoi(
        identifiant="CCOM_L710_1",
        code_ou_traite="Code de commerce",
        article="Article L. 710-1",
        titre="Statut d'établissement public des Chambres de Commerce et d'Industrie (CCI)",
        texte_integral="Les chambres de commerce et d'industrie sont des établissements publics administratifs de l'État animés par des commerçants et industriels élus, chargés de représenter les intérêts généraux de l'industrie, du commerce et des services.",
        strate_impactee="Local",
        effet_simulation="Appuie le tissu des 3,8 millions d'entreprises, gère les infrastructures (ports/aéroports) et facilite l'export des PME.",
    ),
    "CART_L711_1": ArticleDeLoi(
        identifiant="CART_L711_1",
        code_ou_traite="Code de l'artisanat & Code de commerce",
        article="Article L. 711-1",
        titre="Statut et missions des Chambres de Métiers et de l'Artisanat (CMA)",
        texte_integral="Les chambres de métiers et de l'artisanat sont des établissements publics administratifs représentant les intérêts généraux de l'artisanat, tenant le Registre national des entreprises et organisant l'apprentissage artisanal.",
        strate_impactee="Local",
        effet_simulation="Garantit l'excellence des 250 métiers manuels, la transmission des ateliers et le label Maître Artisan.",
    ),
    "CRURAL_L510_1": ArticleDeLoi(
        identifiant="CRURAL_L510_1",
        code_ou_traite="Code rural et de la pêche maritime",
        article="Article L. 510-1",
        titre="Statut et missions des Chambres d'Agriculture (CA)",
        texte_integral="Les chambres d'agriculture sont des établissements publics représentant auprès de l'État et des collectivités l'ensemble des intérêts agricoles, forestiers et du monde rural, et concourant à la transition agroécologique et à la souveraineté alimentaire.",
        strate_impactee="Local",
        effet_simulation="Protège les terres agricoles contre l'artificialisation (CDPENAF), installe les jeunes paysans et soutient les circuits courts.",
    ),
    # -------------------------------------------------------------------------
    # ASSEMBLÉES DÉLIBÉRANTES, PARLEMENT ET CORPS DE DÉCISION
    # -------------------------------------------------------------------------
    "CONST_ART_39": ArticleDeLoi(
        identifiant="CONST_ART_39",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 39",
        titre="Initiative des lois et avis préalable du Conseil d'État",
        texte_integral="L'initiative des lois appartient concurremment au Premier ministre et aux membres du Parlement. Les projets de loi sont délibérés en Conseil des ministres après avis du Conseil d'État et déposés sur le bureau de l'une des deux assemblées.",
        strate_impactee="National",
        effet_simulation="Sécurise la rédaction juridique des réformes fiscales et institutionnelles avant examen parlementaire.",
    ),
    "CONST_ART_45": ArticleDeLoi(
        identifiant="CONST_ART_45",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 45",
        titre="Navette parlementaire, Commission Mixte Paritaire (CMP) et dernier mot",
        texte_integral="Tout projet ou proposition de loi est examiné successivement dans les deux assemblées du Parlement en vue de l'adoption d'un texte identique. Lorsque par suite d'un désaccord le texte n'a pu être adopté, le Premier ministre peut provoquer la réunion d'une commission mixte paritaire chargée de proposer un texte sur les dispositions restant en discussion. Si la commission mixte ne parvient pas à l'adoption d'un texte commun, le Gouvernement peut demander à l'Assemblée nationale de statuer définitivement.",
        strate_impactee="National",
        effet_simulation="Définit les dynamiques de négociation entre députés et sénateurs, et garantit la primauté démocratique de l'Assemblée nationale élue au suffrage direct.",
    ),
    "CONST_ART_48": ArticleDeLoi(
        identifiant="CONST_ART_48",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 48",
        titre="Partage de l'ordre du jour et niches parlementaires de l'opposition",
        texte_integral="L'ordre du jour est fixé par chaque assemblée. Deux semaines de séance sur quatre sont réservées par priorité à l'examen des textes et aux débats dont le Gouvernement demande l'inscription. Un jour de séance par mois est réservé à un ordre du jour fixé par chaque assemblée à l'initiative des groupes d'opposition et des groupes minoritaires.",
        strate_impactee="National",
        effet_simulation="Permet aux oppositions de soumettre au vote des propositions de lois emblématiques (pouvoir d'achat, moralisation, proportionnelle).",
    ),
    "CONST_ART_51_2": ArticleDeLoi(
        identifiant="CONST_ART_51_2",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 51-2",
        titre="Commissions d'enquête de l'Assemblée nationale et du Sénat",
        texte_integral="Pour l'exercice des missions de contrôle et d'évaluation, des commissions d'enquête peuvent être créées au sein de chaque assemblée pour recueillir des éléments d'information sur des faits déterminés ou sur la gestion des services publics.",
        strate_impactee="National",
        effet_simulation="Arme de contrôle dotée de pouvoirs judiciaires (auditions sous serment, réquisitions de pièces) activée en cas de crise politique.",
    ),
    "CONST_ART_70": ArticleDeLoi(
        identifiant="CONST_ART_70",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 70",
        titre="Rôle consultatif du Conseil Économique, Social et Environnemental (CESE)",
        texte_integral="Le Conseil économique, social et environnemental est consulté par le Gouvernement et le Parlement sur tout problème économique, social ou environnemental. Il peut être consulté sur les projets de loi de plan et les projets de loi de finances.",
        strate_impactee="National",
        effet_simulation="Assure la représentation institutionnelle des forces syndicales, patronales, paysannes, mutualistes et écologiques de la nation.",
    ),
    "CONST_ART_71": ArticleDeLoi(
        identifiant="CONST_ART_71",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 71",
        titre="Saisine citoyenne du CESE et démocratie participative",
        texte_integral="Le Conseil économique, social et environnemental peut être saisi par voie de pétition dans les conditions fixées par la loi organique. Il peut également organiser des consultations publiques et associer des citoyens tirés au sort.",
        strate_impactee="Transversal",
        effet_simulation="Légalise le recours aux Conventions Citoyennes tirées au sort et l'examen direct des pétitions citoyennes dès 150 000 signataires.",
    ),
    "CONST_ART_72": ArticleDeLoi(
        identifiant="CONST_ART_72",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 72",
        titre="Libre administration des collectivités territoriales par des conseils élus",
        texte_integral="Les collectivités territoriales de la République sont les communes, les départements, les régions. Elles s'administrent librement par des conseils élus et disposent d'un pouvoir réglementaire pour l'exercice de leurs compétences.",
        strate_impactee="Local",
        effet_simulation="Interdit toute tutelle d'une collectivité sur une autre et protège l'autonomie des 34 935 conseils municipaux.",
    ),
    "CONST_ART_72_1": ArticleDeLoi(
        identifiant="CONST_ART_72_1",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 72-1",
        titre="Droit de pétition locale et Référendum décisionnel territorial",
        texte_integral="Les électeurs de chaque collectivité territoriale peuvent être consultés sur les décisions que les autorités de cette collectivité envisagent de prendre pour régler les affaires relevant de sa compétence. Lorsqu'il s'agit d'un projet de délibération, le projet soumis à référendum est adopté si la moitié au moins des électeurs inscrits a pris part au vote.",
        strate_impactee="Local",
        effet_simulation="Fonde le RIC communal et départemental décisionnel pour les grands projets d'aménagement et de services publics.",
    ),
    "CONST_ART_72_2": ArticleDeLoi(
        identifiant="CONST_ART_72_2",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 72-2",
        titre="Autonomie financière et péréquation des collectivités territoriales",
        texte_integral="Les collectivités territoriales bénéficient de ressources dont elles peuvent disposer librement. Les recettes fiscales et les autres ressources propres représentent une part déterminante de l'ensemble de leurs ressources. Tout transfert de compétences donne lieu à l'attribution de ressources équivalentes.",
        strate_impactee="Local",
        effet_simulation="Interdit à l'État d'imposer de nouvelles charges obligatoires aux communes et départements sans compensation intégrale en recettes.",
    ),
    "CONST_ART_89": ArticleDeLoi(
        identifiant="CONST_ART_89",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 89",
        titre="Révision de la Constitution et Congrès du Parlement à Versailles",
        texte_integral="L'initiative de la révision de la Constitution appartient concurremment au Président de la République sur proposition du Premier ministre et aux membres du Parlement. Le projet ou la proposition de révision doit être voté par les deux assemblées en termes identiques. La révision est définitive après avoir été approuvée par référendum, ou par le Parlement convoqué en Congrès à la majorité des trois cinquièmes des suffrages exprimés.",
        strate_impactee="Transversal",
        effet_simulation="Accorde un veto absolu au Sénat sur la procédure de l'article 89, imposant à l'exécutif de recourir à l'article 11 en cas de blocage conservateur.",
    ),
    "CGCT_L2121_1": ArticleDeLoi(
        identifiant="CGCT_L2121_1",
        code_ou_traite="Code général des collectivités territoriales",
        article="Article L. 2121-1",
        titre="Statut et pouvoirs délibératifs du Conseil Municipal",
        texte_integral="Le conseil municipal règle par ses délibérations les affaires de la commune. Il se réunit au moins une fois par trimestre et vote le budget primitif, arrête les comptes de gestion et fixe les taux des impôts directs locaux.",
        strate_impactee="Local",
        effet_simulation="Modélise les délibérations des 34 935 communes et l'arbitrage direct entre maintien des services publics et taux de taxe foncière.",
    ),
    "CGCT_L3121_1": ArticleDeLoi(
        identifiant="CGCT_L3121_1",
        code_ou_traite="Code général des collectivités territoriales",
        article="Article L. 3121-1",
        titre="Statut et compétences obligatoires du Conseil Départemental",
        texte_integral="Le conseil départemental règle par ses délibérations les affaires du département dans les domaines de l'action sociale, de l'autonomie des personnes et de la solidarité territoriale.",
        strate_impactee="Local",
        effet_simulation="Gère le budget des 4 solidarités humaines (RSA, APA, PCH, ASE) sous la contrainte d'extinction des recettes volatiles DMTO.",
    ),
    "CGCT_L4131_1": ArticleDeLoi(
        identifiant="CGCT_L4131_1",
        code_ou_traite="Code général des collectivités territoriales",
        article="Article L. 4131-1",
        titre="Statut et compétences stratégiques du Conseil Régional",
        texte_integral="Le conseil régional a pour mission de promouvoir le développement économique, social, sanitaire, de l'aménagement du territoire, de l'environnement, des transports et de la formation professionnelle.",
        strate_impactee="Local",
        effet_simulation="Modélise les investissements ferroviaires (TER), les lycées et la contractualisation des CPER avec l'État.",
    ),
    "CGCT_L5211_1": ArticleDeLoi(
        identifiant="CGCT_L5211_1",
        code_ou_traite="Code général des collectivités territoriales",
        article="Article L. 5211-1",
        titre="Dispositions communes aux Conseils Intercommunaux et Métropolitains (EPCI)",
        texte_integral="Les établissements publics de coopération intercommunale sont des personnes morales de droit public fondées sur le transfert volontaire ou obligatoire de compétences exercées par un conseil communautaire élu.",
        strate_impactee="Local",
        effet_simulation="Gère la Cotisation Foncière des Entreprises (CFE), l'eau, les mobilités douces et la mutualisation territoriale.",
    ),
    "TUE_ART_14": ArticleDeLoi(
        identifiant="TUE_ART_14",
        code_ou_traite="Traité sur l'Union Européenne (TUE)",
        article="Article 14",
        titre="Statut et compétences du Parlement Européen",
        texte_integral="Le Parlement européen exerce, conjointement avec le Conseil, les fonctions législative et budgétaire. Il exerce des fonctions de contrôle politique et élit le président de la Commission.",
        strate_impactee="Europe",
        effet_simulation="Codécide les directives sur la fiscalité énergétique, la décarbonation industrielle et le contrôle des frontières commerciales.",
    ),
    "TUE_ART_16": ArticleDeLoi(
        identifiant="TUE_ART_16",
        code_ou_traite="Traité sur l'Union Européenne (TUE)",
        article="Article 16",
        titre="Statut et prise de décision au Conseil de l'Union Européenne",
        texte_integral="Le Conseil exerce, conjointement avec le Parlement européen, les fonctions législative et budgétaire. Le Conseil statue à la majorité qualifiée (55 % des membres du Conseil représentant au moins 65 % de la population).",
        strate_impactee="Europe",
        effet_simulation="Décide formellement de l'activation ou de la levée de la Procédure de Déficit Excessif (PDE) et des sanctions financières associées.",
    ),
    "CONST_ART_1": ArticleDeLoi(
        identifiant="CONST_ART_1",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 1er",
        titre="Principes fondamentaux : République indivisible, laïque, démocratique, sociale et décentralisée",
        texte_integral="La France est une République indivisible, laïque, démocratique et sociale. Elle assure l'égalité devant la loi de tous les citoyens sans distinction d'origine, de race ou de religion. Son organisation est décentralisée.",
        strate_impactee="National",
        effet_simulation="Fonde l'égalité des droits sur l'ensemble du territoire national et l'autonomie de gestion des collectivités décentralisées.",
    ),
    "CONST_ART_72_3": ArticleDeLoi(
        identifiant="CONST_ART_72_3",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 72-3",
        titre="Reconnaissance constitutionnelle des populations et territoires d'Outre-mer",
        texte_integral="La République reconnaît, au sein du peuple français, les populations d'outre-mer, dans un idéal commun de liberté, d'égalité et de fraternité. La Guadeloupe, la Guyane, la Martinique, La Réunion, Mayotte, Saint-Barthélemy, Saint-Martin, Saint-Pierre-et-Miquelon, les îles Wallis et Futuna et la Polynésie française sont régis par l'article 73 pour les départements et régions d'outre-mer et par l'article 74 pour les collectivités d'outre-mer.",
        strate_impactee="Local",
        effet_simulation="Consacre l'appartenance pleine et entière des territoires ultramarins à la République indivisible.",
    ),
    "CONST_ART_73": ArticleDeLoi(
        identifiant="CONST_ART_73",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 73",
        titre="Régime législatif des DROM et Collectivités Territoriales Uniques",
        texte_integral="Dans les départements et les régions d'outre-mer, les lois et règlements sont applicables de plein droit. Ils peuvent faire l'objet d'adaptations tenant aux caractéristiques et contraintes particulières de ces collectivités. Une collectivité unique peut être substituée à un département et une région d'outre-mer.",
        strate_impactee="Local",
        effet_simulation="Autorise l'adaptation fiscale (octroi de mer) et la création des Collectivités Uniques de Guyane et Martinique.",
    ),
    "CONST_ART_74": ArticleDeLoi(
        identifiant="CONST_ART_74",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Article 74",
        titre="Statut d'autonomie des Collectivités d'Outre-mer (COM)",
        texte_integral="Les collectivités d'outre-mer régies par le présent article ont un statut qui tient compte des intérêts propres de chacune d'elles au sein de la République. Ce statut est défini par une loi organique qui fixe les compétences exercées et les conditions dans lesquelles les lois y sont applicables.",
        strate_impactee="Local",
        effet_simulation="Fonde les régimes d'autonomie fiscale et douanière de la Polynésie française, de Saint-Barthélemy, de Saint-Martin et de Saint-Pierre-et-Miquelon.",
    ),
    "CONST_TITRE_XIII": ArticleDeLoi(
        identifiant="CONST_TITRE_XIII",
        code_ou_traite="Constitution du 4 octobre 1958",
        article="Articles 76 et 77",
        titre="Statut sui generis de la Nouvelle-Calédonie (Accord de Nouméa)",
        texte_integral="Les populations de la Nouvelle-Calédonie sont appelées à se prononcer sur les dispositions de l'accord signé à Nouméa le 5 mai 1998. La loi organique détermine les compétences de l'État transférées de façon définitive aux institutions de la Nouvelle-Calédonie.",
        strate_impactee="Local",
        effet_simulation="Régit le Congrès calédonien, le gouvernement collégial et le Sénat coutumier kanak.",
    ),
    "CODE_ELEC_L16": ArticleDeLoi(
        identifiant="CODE_ELEC_L16",
        code_ou_traite="Code électoral",
        article="Article L. 16",
        titre="Répertoire Électoral Unique (REU) géré par l'INSEE",
        texte_integral="Il est tenu par l'Institut national de la statistique et des études économiques un répertoire électoral unique comprenant l'ensemble des électeurs inscrits sur les listes électorales de chaque commune et des consulats à l'étranger.",
        strate_impactee="National",
        effet_simulation="Base de données unifiée de 49,5 millions d'électeurs avec inscription automatique dès la majorité (18 ans).",
    ),
    "CODE_ELEC_L123": ArticleDeLoi(
        identifiant="CODE_ELEC_L123",
        code_ou_traite="Code électoral",
        article="Article L. 123",
        titre="Scrutin uninominal majoritaire à deux tours pour les Élections Législatives",
        texte_integral="Les députés sont élus au scrutin uninominal majoritaire à deux tours dans le cadre de 577 circonscriptions. Pour être élu au premier tour, un candidat doit recueillir la majorité absolue des suffrages et un quart des électeurs inscrits. Pour se maintenir au second tour, il faut 12,5 % des inscrits.",
        strate_impactee="National",
        effet_simulation="Régit la formation de la majorité gouvernementale à l'Assemblée nationale et les triangulaires électorales.",
    ),
    "CODE_ELEC_L260": ArticleDeLoi(
        identifiant="CODE_ELEC_L260",
        code_ou_traite="Code électoral",
        article="Article L. 260",
        titre="Scrutin de liste paritaire avec prime majoritaire de 50 % aux Élections Municipales",
        texte_integral="Les conseillers municipaux des communes de 1 000 habitants et plus sont élus au scrutin de liste bloquée paritaire à deux tours avec prime majoritaire de 50 % des sièges pour la liste arrivée en tête et répartition proportionnelle du reste.",
        strate_impactee="Local",
        effet_simulation="Assure la stabilité des exécutifs municipaux et impose la stricte parité homme-femme.",
    ),
    "CGCT_L2411_1": ArticleDeLoi(
        identifiant="CGCT_L2411_1",
        code_ou_traite="Code général des collectivités territoriales (CGCT)",
        article="Article L. 2411-1",
        titre="Sections de commune, biens indivis et droits d'affouage",
        texte_integral="Une section de commune est une personne morale de droit public possédant à titre exclusif des biens, droits ou charges distincts de ceux de la commune. Les habitants de la section ont vocation à la jouissance des biens communaux et aux droits d'affouage.",
        strate_impactee="Local",
        effet_simulation="Protège le patrimoine rural indivis (forêts, estives) au niveau des hameaux et terroirs.",
    ),
    "CODE_TRANSP_L1803_1": ArticleDeLoi(
        identifiant="CODE_TRANSP_L1803_1",
        code_ou_traite="Code des transports",
        article="Article L. 1803-1",
        titre="Principe de Continuité Territoriale entre l'Outre-mer et la Métropole",
        texte_integral="L'État garantit la continuité territoriale entre les collectivités d'outre-mer et le territoire métropolitain. Cette politique concourt à atténuer les contraintes de l'éloignement et du surcoût des transports pour les résidents ultramarins.",
        strate_impactee="Local",
        effet_simulation="Finance l'aide à la mobilité aérienne (LADOM) et les tarifs régulés pour les étudiants et familles d'Outre-mer.",
    ),
}


def get_corpus_lois() -> Dict[str, ArticleDeLoi]:
    """Retourne l'intégralité du registre légal."""
    return REGISTRE_LEGAL


# Export direct des instances clés pour import immédiat
CONST_ART_1 = REGISTRE_LEGAL["CONST_ART_1"]
CONST_ART_72_3 = REGISTRE_LEGAL["CONST_ART_72_3"]
CONST_ART_73 = REGISTRE_LEGAL["CONST_ART_73"]
CONST_ART_74 = REGISTRE_LEGAL["CONST_ART_74"]
CONST_TITRE_XIII = REGISTRE_LEGAL["CONST_TITRE_XIII"]
CODE_ELEC_L16 = REGISTRE_LEGAL["CODE_ELEC_L16"]
CODE_ELEC_L123 = REGISTRE_LEGAL["CODE_ELEC_L123"]
CODE_ELEC_L260 = REGISTRE_LEGAL["CODE_ELEC_L260"]
CGCT_L2411_1 = REGISTRE_LEGAL["CGCT_L2411_1"]
CODE_TRANSP_L1803_1 = REGISTRE_LEGAL["CODE_TRANSP_L1803_1"]


def rechercher_loi(mot_cle: str) -> List[ArticleDeLoi]:
    """Recherche des textes par mot-clé dans le titre, le code ou l'effet."""
    mot_cle_lower = mot_cle.lower()
    resultats = []
    for art in REGISTRE_LEGAL.values():
        if (
            mot_cle_lower in art.titre.lower()
            or mot_cle_lower in art.code_ou_traite.lower()
            or mot_cle_lower in art.effet_simulation.lower()
            or mot_cle_lower in art.article.lower()
        ):
            resultats.append(art)
    return resultats
