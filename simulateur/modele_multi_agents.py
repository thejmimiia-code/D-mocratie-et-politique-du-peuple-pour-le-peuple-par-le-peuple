#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de prototype Multi-Agents pour le simulateur macro-politique.

Ce module illustre comment le formalisme SFC (top-down) peut être enrichi
par une approche multi-agents (bottom-up) pour modéliser les interactions
micro-économiques entre les acteurs de la société française.

Inspiré des projets :
  - Mesa (github.com/mesa/mesa) — Framework ABM standard
  - PolicySpace (github.com/BAFurtado/PolicySpace) — Redistribution fiscale
  - wealth-inequality-abm (github.com/cconsta1/wealth-inequality-abm) — Gini
  - SFC_models (github.com/brianr747/SFC_models) — Modèles Godley-Lavoie

Architecture :
  - AgentMénage : représente un ménage (revenu, patrimoine, décile)
  - AgentEntreprise : représente une entreprise (CA, emploi, investissement)
  - AgentEtat : représente l'État (budget, recettes, dépenses)
  - AgentCollectivite : représente une collectivité locale (DGF, TF, investissement)
  - EnvironnementMarché : le marché (prix, taux, inflation)

Principe : chaque agent prend des décisions autonomes basées sur des règles
simples, et les interactions émergentes produisent des agrégats cohérents
avec le modèle SFC (validation bottom-up → top-down).

Ce module est un PROTOTYPE DE DÉMONSTRATION. Il ne remplace pas le moteur SFC
mais le complète par une couche de granularité micro-économique.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import random
import json
from datetime import datetime


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 1 : TYPES ET ENUMERATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TypeAgent(Enum):
    """Types d'agents dans le modèle."""
    MENAGE = "ménage"
    ENTREPRISE = "entreprise"
    ETAT = "état"
    COLLECTIVITE = "collectivité"
    BANQUE = "banque"


class StrategieConsommation(Enum):
    """Stratégies de consommation des ménages."""
    KEYNESIENNE = "keynesienne"  # Propension marginale à consommer élevée
    RICARDIENNE = "ricardienne"  # Équivalence ricardienne (épargne)
    ADAPTATIVE = "adaptative"    # Ajustement basé sur l'historique


class StrategieInvestissement(Enum):
    """Stratégies d'investissement des entreprises."""
    ACCELERATEUR = "accelerateur"  # Investissement proportionnel à la demande
    TOBIN_Q = "tobin_q"           # Ratio marché/valeur de remplacement
    CAUTIOUS = "cautious"          # Investissement minimal


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 2 : AGENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class AgentMenage:
    """
    Agent ménage : représente un foyer fiscal français.
    
    Attributs basés sur les données INSEE ERFS :
    - revenu : revenu disponible annuel (€)
    - patrimoine : patrimoine net (€)
    - decile : décile de niveau de vie (1-10)
    - csp : catégorie socioprofessionnelle (1-8)
    - epargne : taux d'épargne (%)
    - consommation : consommation annuelle (€)
    """
    id: int
    revenu: float
    patrimoine: float
    decile: int  # 1-10
    csp: int     # 1-8
    strategie: StrategieConsommation = StrategieConsommation.ADAPTATIVE
    taux_epargne: float = 0.15  # 15% par défaut (moyenne INSEE)
    consommation_annuelle: float = 0.0
    historique_revenu: List[float] = field(default_factory=list)
    
    def calculer_consommation(self, inflation: float = 0.02) -> float:
        """
        Calcule la consommation basée sur la stratégie.
        
        Sources :
        - Propension marginale à consommer : 0.6-0.8 (OFCE)
        - Taux d'épargne moyen France : 15% (INSEE 2024)
        """
        if self.strategie == StrategieConsommation.KEYNESIENNE:
            # PMC élevée (0.75), peu d'épargne de précaution
            pmc = 0.75
            self.consommation_annuelle = self.revenu * pmc
        elif self.strategie == StrategieConsommation.RICARDIENNE:
            # Équivalence ricardienne : épargne anticipatoire
            pmc = 0.60
            self.consommation_annuelle = self.revenu * pmc
        else:  # ADAPTATIVE
            # Ajustement basé sur l'historique (revenu permanent)
            if len(self.historique_revenu) > 0:
                revenu_permanent = sum(self.historique_revenu[-3:]) / min(3, len(self.historique_revenu))
            else:
                revenu_permanent = self.revenu
            pmc = 0.70
            self.consommation_annuelle = revenu_permanent * pmc
        
        # Ajustement pour l'inflation
        self.consommation_annuelle *= (1 + inflation)
        
        return self.consommation_annuelle
    
    def calculer_impot_revenu(self, bareme: Dict[int, float] = None) -> float:
        """
        Calcule l'impôt sur le revenu selon le barème progressif.
        
        Source : Code général des impôts, art. 197
        Barème 2024 : 0% jusqu'à 11 294€, puis 11%, 30%, 41%, 45%
        """
        if bareme is None:
            bareme = {
                11294: 0.00,
                28797: 0.11,
                82341: 0.30,
                177106: 0.41,
                float('inf'): 0.45
            }
        
        revenu_imposable = self.revenu
        impot = 0.0
        seuil_precedent = 0.0
        
        for seuil, taux in sorted(bareme.items()):
            if revenu_imposable <= seuil:
                impot += (revenu_imposable - seuil_precedent) * taux
                break
            else:
                impot += (seuil - seuil_precedent) * taux
                seuil_precedent = seuil
        
        return impot
    
    def mettre_a_jour(self, nouveau_revenu: float):
        """Met à jour le ménage pour une nouvelle période."""
        self.historique_revenu.append(self.revenu)
        self.revenu = nouveau_revenu
        # Garder seulement les 5 dernières années
        if len(self.historique_revenu) > 5:
            self.historique_revenu = self.historique_revenu[-5:]


@dataclass
class AgentEntreprise:
    """
    Agent entreprise : représente une PME ou grande entreprise.
    
    Sources :
    - Nombre d'entreprises France : 4,1 millions (INSEE 2024)
    - Part PME (< 250 salariés) : 99,8%
    - Investissement moyen : 20-25% du CA (INSEE)
    """
    id: int
    ca_annuel: float  # Chiffre d'affaires
    effectifs: int
    investissement: float
    strategie: StrategieInvestissement = StrategieInvestissement.ACCELERATEUR
    secteur: str = "services"
    dette: float = 0.0
    
    def decider_investissement(self, demande: float, taux_interet: float = 0.04) -> float:
        """
        Décide du niveau d'investissement selon la stratégie.
        
        Sources :
        - Accélérateur : investissement = α × ΔDemande
        - Tobin Q : investissement si Q > 1
        - Cautious : investissement minimal (entretien)
        """
        if self.strategie == StrategieInvestissement.ACCELERATEUR:
            # Coefficient d'accélération : 0.2-0.3 (modèles SFC)
            alpha = 0.25
            self.investissement = max(0, alpha * demande * self.ca_annuel)
        elif self.strategie == StrategieInvestissement.TOBIN_Q:
            # Q = Valeur marché / Coût de remplacement
            q = self.ca_annuel / max(self.investissement, 1) if self.investissement > 0 else 1.5
            if q > 1:
                self.investissement = 0.20 * self.ca_annuel
            else:
                self.investissement = 0.05 * self.ca_annuel
        else:  # CAUTIOUS
            self.investissement = 0.10 * self.ca_annuel  # Maintenance
        
        # Coût du crédit impacte l'investissement
        if taux_interet > 0.05:  # Seuil de sensibilité
            facteur = max(0.5, 1 - (taux_interet - 0.05) * 5)
            self.investissement *= facteur
        
        return self.investissement
    
    def payer_impot_societes(self, taux: float = 0.25) -> float:
        """
        Calcule l'impôt sur les sociétés.
        
        Source : CGI art. 219 — Taux normal 25% (2024)
        """
        benefice = max(0, self.ca_annuel * 0.08)  # Marge nette ~8%
        return benefice * taux


@dataclass
class AgentCollectivite:
    """
    Agent collectivité locale : représente une commune ou EPCI.
    
    Sources :
    - 34 935 communes (INSEE)
    - 1 254 EPCI (Banatic)
    - DGF : 50 Md€/an
    - Taxe foncière : 43,5 Md€/an
    
    Règle d'or CGCT L. 1612-4 :
    Toute baisse de DGF est répercutée à 94% en hausse de TF.
    """
    id: int
    type_collectivite: str  # "commune", "epci", "departement", "region"
    population: int
    dotation_etat: float  # DGF en €
    taxe_fonciere: float  # TFPB en €
    investissement: float
    dette: float = 0.0
    
    def appliquer_regle_or(self, variation_dgf: float) -> float:
        """
        Applique la règle d'or budgétaire locale (CGCT L. 1612-4).
        
        Retourne la variation de taxe foncière résultante.
        
        Source : Cour des comptes — 94% de répercussion
        """
        # Coefficient de répercussion
        coefficient = 0.94
        
        # Hausse de TF = baisse de DGF × coefficient
        variation_tf = -variation_dgf * coefficient
        
        # Mise à jour
        self.dotation_etat += variation_dgf
        self.taxe_fonciere += variation_tf
        
        return variation_tf
    
    def calculer_poids_politique(self) -> float:
        """
        Calcule le poids politique de la collectivité.
        
        Facteurs : population, nombre d'élus, budget
        """
        poids_population = min(1.0, self.population / 100000)
        poids_budget = min(1.0, (self.dotation_etat + self.taxe_fonciere) / 1e9)
        
        return (poids_population + poids_budget) / 2


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 3 : ENVIRONNEMENT DE MARCHÉ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class EnvironnementMarche:
    """
    Environnement de marché : agrège les conditions macroéconomiques.
    
    Sources :
    - Taux BCE : 3,75% (2024)
    - Inflation : 2,0% (INSEE 2024)
    - Spread OAT-Bund : 88 pb (BCE)
    - Pétrole Brent : ~80 $/bbl (ICE)
    """
    taux_directeur: float = 0.0375  # BCE
    inflation: float = 0.02
    spread_oat_bund: float = 0.0088
    prix_petrole: float = 80.0
    pib_nominal: float = 2955e9  # Md€
    croissance_pib: float = 0.011
    
    def calculer_taux_credit(self, risque: float = 0.0) -> float:
        """
        Calcule le taux de crédit pour un agent donné.
        
        Taux = taux directeur + spread + prime de risque
        """
        return self.taux_directeur + self.spread_oat_bund + risque
    
    def simuler_choc(self, type_choc: str, intensite: float) -> Dict:
        """
        Simule un choc macroéconomique.
        
        Types de chocs :
        - "petrole" : hausse du prix du pétrole
        - "taux" : hausse des taux directeurs
        - "inflation" : hausse de l'inflation
        - "demande" : choc de demande (récession)
        """
        impact = {}
        
        if type_choc == "petrole":
            self.prix_petrole *= (1 + intensite)
            impact["inflation_supplementaire"] = intensite * 0.3  # Pass-through 30%
            impact["pib_impact"] = -intensite * 0.1  # Élasticité -0.1
            
        elif type_choc == "taux":
            self.taux_directeur += intensite
            impact["credit_impact"] = -intensite * 0.5  # Élasticité -0.5
            impact["dette_impact"] = intensite * 0.8  # Coût du service
            
        elif type_choc == "inflation":
            self.inflation += intensite
            impact["pouvoir_achat_impact"] = -intensite
            impact["salaire_reel_impact"] = -intensite * 0.7
            
        elif type_choc == "demande":
            self.croissance_pib += intensite  # intensite négative = récession
            impact["chomage_impact"] = -intensite * 2  # Loi d'Okun
            impact["recettes_impact"] = intensite * 0.5  # Élasticité
            
        return impact
    
    def mettre_a_jour_periode(self):
        """Met à jour l'environnement pour une nouvelle période."""
        # Croissance endogène
        self.pib_nominal *= (1 + self.croissance_pib + self.inflation)
        
        # Ajustement des prix relatifs
        self.prix_petrole *= (1 + random.gauss(0, 0.05))  # Volatilité


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 4 : MODÈLE DE SIMULATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ModeleMultiAgents:
    """
    Modèle de simulation multi-agents pour le simulateur macro-politique.
    
    Ce modèle simule les interactions entre :
    - Ménages (consommation, épargne, impôts)
    - Entreprises (production, investissement, emploi)
    - Collectivités (DGF, taxe foncière, investissement local)
    - Environnement (taux, inflation, croissance)
    
    Le modèle produit des agrégats cohérents avec le modèle SFC (validation).
    """
    
    def __init__(self, nb_menages: int = 100, nb_entreprises: int = 10):
        self.menages: List[AgentMenage] = []
        self.entreprises: List[AgentEntreprise] = []
        self.collectivites: List[AgentCollectivite] = []
        self.environnement = EnvironnementMarche()
        self.historique: List[Dict] = []
        
        # Initialisation des agents
        self._initialiser_menages(nb_menages)
        self._initialiser_entreprises(nb_entreprises)
        self._initialiser_collectivites()
    
    def _initialiser_menages(self, nb: int):
        """
        Initialise les ménages avec des distributions réalistes.
        
        Source : INSEE ERFS 2024
        - Décile 1 : ~8 000 €/an
        - Décile 5 : ~21 000 €/an
        - Décile 10 : ~48 000 €/an
        """
        revenus_par_decile = {
            1: 8000, 2: 12000, 3: 15000, 4: 18000, 5: 21000,
            6: 25000, 7: 29000, 8: 34000, 9: 42000, 10: 48000
        }
        
        for i in range(nb):
            decile = (i % 10) + 1
            revenu_base = revenus_par_decile[decile]
            # Variation aléatoire ±20%
            revenu = revenu_base * (0.8 + random.random() * 0.4)
            
            patrimoine = revenu * (2 + random.random() * 8)  # 2-10x le revenu
            csp = min(8, max(1, decile // 2 + 1))
            
            strategie = random.choice(list(StrategieConsommation))
            
            menage = AgentMenage(
                id=i,
                revenu=revenu,
                patrimoine=patrimoine,
                decile=decile,
                csp=csp,
                strategie=strategie
            )
            self.menages.append(menage)
    
    def _initialiser_entreprises(self, nb: int):
        """
        Initialise les entreprises.
        
        Source : INSEE 2024
        - 4,1 millions d'entreprises
        - 99,8% sont des PME
        - CA moyen PME : ~1,5 M€
        """
        for i in range(nb):
            ca = 1.5e6 * (0.5 + random.random() * 2)
            effectifs = max(1, int(ca / 150000))  # Productivité ~150k€/salarié
            
            strategie = random.choice(list(StrategieInvestissement))
            
            entreprise = AgentEntreprise(
                id=i,
                ca_annuel=ca,
                effectifs=effectifs,
                investissement=ca * 0.20,
                strategie=strategie,
                secteur=random.choice(["industrie", "services", "commerce", "construction"])
            )
            self.entreprises.append(entreprise)
    
    def _initialiser_collectivites(self):
        """
        Initialise quelques collectivités représentatives.
        
        Source : INSEE, DGCL
        """
        collectivites_exemple = [
            AgentCollectivite(
                id=0, type_collectivite="commune",
                population=5000, dotation_etat=500000,
                taxe_fonciere=300000, investissement=200000
            ),
            AgentCollectivite(
                id=1, type_collectivite="commune",
                population=50000, dotation_etat=5000000,
                taxe_fonciere=3000000, investissement=2000000
            ),
            AgentCollectivite(
                id=2, type_collectivite="departement",
                population=500000, dotation_etat=50000000,
                taxe_fonciere=30000000, investissement=20000000
            ),
        ]
        self.collectivites = collectivites_exemple
    
    def simuler_periode(self, annee: int) -> Dict:
        """
        Simule une période (1 an) du modèle multi-agents.
        
        Retourne les agrégats calculés bottom-up.
        """
        resultats = {
            "annee": annee,
            "consommation_totale": 0,
            "investissement_total": 0,
            "epargne_totale": 0,
            "impots_menages_total": 0,
            "impots_entreprises_total": 0,
            "taxe_fonciere_totale": 0,
            "dotation_etat_totale": 0,
        }
        
        # 1. Ménages : consommation et impôts
        for menage in self.menages:
            # Ajustement du revenu pour la croissance
            nouveau_revenu = menage.revenu * (1 + self.environnement.croissance_pib)
            menage.mettre_a_jour(nouveau_revenu)
            
            # Consommation
            consommation = menage.calculer_consommation(self.environnement.inflation)
            resultats["consommation_totale"] += consommation
            
            # Épargne
            epargne = menage.revenu - consommation
            resultats["epargne_totale"] += max(0, epargne)
            
            # Impôts
            impot = menage.calculer_impot_revenu()
            resultats["impots_menages_total"] += impot
        
        # 2. Entreprises : investissement et impôts
        for entreprise in self.entreprises:
            # Demande agrégée (simplifiée)
            demande = resultats["consommation_totale"] / max(1, len(self.entreprises))
            
            # Investissement
            taux_credit = self.environnement.calculer_taux_credit()
            investissement = entreprise.decider_investissement(demande, taux_credit)
            resultats["investissement_total"] += investissement
            
            # Impôts
            is_impot = entreprise.payer_impot_societes()
            resultats["impots_entreprises_total"] += is_impot
        
        # 3. Collectivités : règle d'or
        for col in self.collectivites:
            # Variation DGF (simplifiée : stable)
            variation_dgf = 0
            col.appliquer_regle_or(variation_dgf)
            
            resultats["taxe_fonciere_totale"] += col.taxe_fonciere
            resultats["dotation_etat_totale"] += col.dotation_etat
        
        # 4. Mise à jour environnement
        self.environnement.mettre_a_jour_periode()
        
        # 5. Historique
        self.historique.append(resultats)
        
        return resultats
    
    def calculer_gini(self) -> float:
        """
        Calcule le coefficient de Gini des revenus des ménages.
        
        Source : Formule standard — Banque mondiale
        """
        revenus = sorted([m.revenu for m in self.menages])
        n = len(revenus)
        
        if n == 0 or sum(revenus) == 0:
            return 0.0
        
        # Formule de Gini
        numerateur = sum((2 * (i + 1) - n - 1) * revenus[i] for i in range(n))
        denominateur = n * sum(revenus)
        
        return numerateur / denominateur if denominateur != 0 else 0.0
    
    def simuler_multiples_periodes(self, nb_annees: int = 5, annee_debut: int = 2024) -> List[Dict]:
        """
        Simule plusieurs années et retourne l'historique complet.
        """
        resultats = []
        for annee in range(annee_debut, annee_debut + nb_annees):
            r = self.simuler_periode(annee)
            r["gini"] = self.calculer_gini()
            resultats.append(r)
        
        return resultats
    
    def exporter_resultats(self) -> str:
        """Exporte les résultats en JSON."""
        return json.dumps({
            "modele": "multi-agents",
            "nb_menages": len(self.menages),
            "nb_entreprises": len(self.entreprises),
            "nb_collectivites": len(self.collectivites),
            "historique": self.historique,
            "environnement": {
                "taux_directeur": self.environnement.taux_directeur,
                "inflation": self.environnement.inflation,
                "spread_oat_bund": self.environnement.spread_oat_bund,
                "pib_nominal": self.environnement.pib_nominal,
                "croissance_pib": self.environnement.croissance_pib,
            },
            "metadata": {
                "date_generation": datetime.now().isoformat(),
                "sources": [
                    "INSEE ERFS 2024",
                    "Code général des impôts art. 197",
                    "CGCT L. 1612-4",
                    "BCE (taux directeur)",
                    "OFCE (propension marginale à consommer)",
                ],
            },
        }, ensure_ascii=False, indent=2)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 5 : FONCTIONS D'ACCÈS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def creer_modele_demo(nb_menages: int = 100, nb_entreprises: int = 10) -> ModeleMultiAgents:
    """Crée un modèle de démonstration."""
    return ModeleMultiAgents(nb_menages, nb_entreprises)


def executer_simulation(nb_annees: int = 5, nb_menages: int = 100) -> Dict:
    """
    Exécute une simulation complète et retourne les résultats.
    
    Args:
        nb_annees: Nombre d'années à simuler
        nb_menages: Nombre de ménages dans le modèle
    
    Returns:
        Dictionnaire avec l'historique et les métriques
    """
    modele = creer_modele_demo(nb_menages)
    historique = modele.simuler_multiples_periodes(nb_annees)
    
    return {
        "historique": historique,
        "gini_initial": historique[0]["gini"] if historique else 0,
        "gini_final": historique[-1]["gini"] if historique else 0,
        "consommation_initiale": historique[0]["consommation_totale"] if historique else 0,
        "consommation_finale": historique[-1]["consommation_totale"] if historique else 0,
    }


if __name__ == "__main__":
    # Démonstration
    print("=" * 60)
    print("SIMULATION MULTI-AGENTS — PROTOTYPE")
    print("=" * 60)
    
    resultats = executer_simulation(nb_annees=5, nb_menages=100)
    
    print(f"\nRésultats sur 5 ans :")
    print(f"  Gini initial : {resultats['gini_initial']:.3f}")
    print(f"  Gini final   : {resultats['gini_final']:.3f}")
    print(f"  Consommation : {resultats['consommation_initiale']/1e6:.1f}M€ → {resultats['consommation_finale']/1e6:.1f}M€")
    
    print("\nHistorique :")
    for r in resultats["historique"]:
        print(f"  {r['annee']}: Conso={r['consommation_totale']/1e6:.1f}M€ | "
              f"Inv={r['investissement_total']/1e6:.1f}M€ | "
              f"Gini={r['gini']:.3f}")