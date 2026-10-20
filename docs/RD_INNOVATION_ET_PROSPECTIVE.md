# R&D — Innovation, prospective technologique et chiffrage économique des stocks (2026-2036)

**Passe du 20 octobre 2026 · Module `simulateur/innovation_prospective.py` · Horizons 5 et 10 ans.**

Ce document formalise l'avancée de R&D sur la **prospective de l'innovation technologique**,
la **diffusion de la Productivité Globale des Facteurs (PGF)** et le **chiffrage économique
complet des stocks de résilience** (traitement de la lacune P0 des « coûts économiques incomplets »).

---

## 1. Le constat : trois dimensions manquantes dans la prospective existante

Jusqu'ici, les travaux de prospective du dépôt (`simulateur/prospective.py`,
`docs/RD_PROSPECTIVE.md`, `docs/AUDIT_LACUNES_GEOPOLITIQUES.md`) croisaient avec rigueur les
horizons calendaires (5 et 10 ans) avec les quatre fenêtres de veille documentées.
Cependant, trois angles morts subsistaient :

1. **L'innovation était traitée comme un coût instantané sans dynamique de diffusion** :
   Le levier `budget_recherche` (+15 Md€/an max) et les investissements de souveraineté
   numérique ou industrielle étaient comptabilisés comme des dépenses budgétaires annuelles
   immédiates, sans modéliser le temps d'amorçage des laboratoires (1 à 2 ans), la courbe de
   diffusion industrielle en S (3 à 5 ans) et le plein rendement de la Productivité Globale des
   Facteurs (PGF / TFP) sur le cycle décennal (6 à 10 ans).
2. **L'hypothèse de gratuité des stocks de résilience (lacune P0)** :
   Dans les simulations géopolitiques antérieures, les réserves physiques (pétrole, métaux,
   médicaments, alimentation) étaient modélisées en flux physiques purs sans compte
   ressources/emplois explicite. Or, constituer et porter 3 à 6 mois de stocks nationaux
   mobilise des dizaines de milliards d'euros de capital public (CAPEX) et génère des coûts
   récurrents de gardiennage, maintenance et rotation (OPEX, 3 à 5 % par an).
3. **L'absence de cartographie des transitions technologiques et biophysiques structurantes** :
   Les ruptures technologiques (supercalculateurs exaflopiques, SMR, thérapies ARNm, recyclage
   des métaux critiques, agroécologie) n'étaient pas suivies par des jalons temporels explicites
   ni par des signaux de renforcement et d'infirmation vérifiables.

---

## 2. Principes et règles de modélisation

1. **Diffusion logistique continue (S-curve)** :
   La diffusion d'une vague d'innovations suit une loi logistique décalée d'un délai de latence :
   $$\text{Diffusion}(t) = \frac{1}{1 + e^{-\beta \cdot (t - t_{\text{latence}} - t_{\text{inflexion}})}}$$
   Pour $t \le t_{\text{latence}}$, la diffusion est nulle ($\text{Diffusion} = 0$).
2. **Taux de retour social net de la R&D sourcé** :
   Conformément aux synthèses empiriques du MESR, de France Stratégie et de l'OCDE, le taux de
   retour social net de la R&D publique et privée atteint **25 % à 35 %** à pleine maturité.
   Ce rendement se traduit par des gains d'efficience énergétique, une réduction des coûts
   de santé par l'innovation thérapeutique et des gains de productivité industrielle.
3. **Comptabilité ressources/emplois stricte (zéro gratuité, zéro double comptage)** :
   - **Immobilisation en capital (CAPEX)** : Comptabilisée au bilan de l'État en actifs publics
     stratégiques réels, gagée sur des ressources d'investissement.
   - **Charge récurrente de portage (OPEX)** : Inscrite en dépenses de fonctionnement de l'État
     (3,5 % à 5 % par an selon la dégradation physique de la ressource).
   - **Amortissement des infrastructures** : Amortissement linéaire sur 10 ans des cuves, silos
     et salles blanches sécurisées.

---

## 3. Les 5 Piliers de Prospective Technologique & Biophysique (2026-2036)

| Pilier | Clé | Maturité TRL initiale | Horizon cible | Objectif clé 2030-2036 |
|---|---|---|:---:|---|
| **IA & Calcul souverain** | `ia_calcul_souverain` | TRL 6 | 2031 | $\ge$ 1,5 Exaflops souverains (Jules Verne) & modèles ouverts spécialisés |
| **Énergie décarbonée & SMR** | `energie_decarbonee_smr` | TRL 5-6 | 2033 | 1ᵉ unité SMR raccordée, 10 GW de stockage & 1 Mt/an d'hydrogène vert |
| **Biotech & Santé souveraine** | `biotech_sante_souveraine` | TRL 7 | 2030 | Production locale de 80 % des 50 médicaments majeurs d'urgence |
| **Métaux critiques & Recyclage** | `materiaux_critiques_recyclage` | TRL 5-6 | 2032 | Récupération $\ge$ 85 % lithium/cobalt/terres rares, extraction Emili |
| **Agroécologie & Eau** | `agroecologie_eau_climat` | TRL 7 | 2032 | -50 % engrais de synthèse, -30 % prélèvements d'eau d'irrigation |

Chaque pilier est assorti dans le code de ses **signaux qui renforceraient l'alerte**, de ses
**signaux contraires** et de ses **verrous scientifiques et industriels**, permettant une veille
dynamique non prophétique.

---

## 4. Chiffrage Économique Complet des Stocks Stratégiques de Résilience

Panier national dimensionné aux besoins de sécurité civile et industrielle :

| Réserve stratégique | Secteur | Volume | Actif immobilisé (CAPEX) | Portage annuel (OPEX) | Amortissement annuel | Charge budgétaire annuelle |
|---|---|:---:|---:|---:|---:|---:|
| **Carburants & Pétrole (AIE/CPSSP)** | Énergie | 3,0 mois | 13,50 Md€ | 0,473 Md€ | 0,202 Md€ | **0,675 Md€/an** |
| **Composants & Semi-conducteurs** | Industrie / Défense | 6,0 mois | 7,20 Md€ | 0,324 Md€ | 0,108 Md€ | **0,432 Md€/an** |
| **Médicaments d'urgence (MITM)** | Santé | 4,0 mois | 4,00 Md€ | 0,200 Md€ | 0,060 Md€ | **0,260 Md€/an** |
| **Céréales & Semences de secours** | Agriculture | 2,5 mois | 2,00 Md€ | 0,080 Md€ | 0,030 Md€ | **0,110 Md€/an** |
| **Métaux critiques (Lithium/Terres rares)** | Industrie / Transition | 6,0 mois | 4,20 Md€ | 0,105 Md€ | 0,063 Md€ | **0,168 Md€/an** |
| **TOTAL NATIONAL** | — | — | **30,90 Md€** | **1,182 Md€/an** | **0,463 Md€/an** | **1,645 Md€/an** |

### Imputation budgétaire :
- Sur un horizon de **5 ans** (une mandature) : La charge cumulée d'entretien s'élève à **8,25 Md€**.
- Sur un horizon de **10 ans** (deux mandatures) : La charge cumulée s'élève à **16,45 Md€**.
- L'acquisition initiale de 30,90 Md€ constitue un actif patrimonial gagé, éliminant tout reproche
  de coût caché ou de stock virtuel sans financement.

---

## 5. Résultats Expérimentaux des Trajectoires et Stress-Tests

### A. Trajectoire des rendements de la R&D (Base 5 Md€/an d'effort pérenne)

```
 Année | Effort cumulé | Diffusion logistique | Gain PGF (pts) | Rendement social brut
-------+---------------+----------------------+----------------+-----------------------
 An 1  |       5.0 Md€ |                0.0 % |     +0.000 pts |           0.00 Md€/an
 An 2  |      10.0 Md€ |               15.4 % |     +0.028 pts |          +0.46 Md€/an
 An 3  |      15.0 Md€ |               29.9 % |     +0.081 pts |          +1.35 Md€/an
 An 4  |      20.0 Md€ |               50.0 % |     +0.180 pts |          +3.00 Md€/an
 An 5  |      25.0 Md€ |               70.1 % |     +0.315 pts |          +5.25 Md€/an
-------+---------------+----------------------+----------------+-----------------------
 An 6  |      30.0 Md€ |               84.5 % |     +0.457 pts |          +7.61 Md€/an
 An 7  |      35.0 Md€ |               92.8 % |     +0.584 pts |          +9.74 Md€/an
 An 8  |      40.0 Md€ |               96.8 % |     +0.697 pts |         +11.61 Md€/an
 An 9  |      45.0 Md€ |               98.6 % |     +0.799 pts |         +13.31 Md€/an
 An 10 |      50.0 Md€ |               99.4 % |     +0.894 pts |         +14.91 Md€/an
```

### B. Stress-Test Croisé : Choc de Stagflation Géopolitique Multi-Théâtres

Évaluation sur un choc majeur combinant pétrole (+40 $/baril), pénurie de composants (-40 %)
et hausse des taux (+150 bps) :

| Horizon | Pertes sans protection (Témoin) | Pertes R&D seule | Pertes Stocks seuls | Pertes combinées (R&D + Stocks) | Gain net évité | Ratio coût/bénéfice |
|---|---:|---:|---:|---:|---:|---:|
| **5 ans** | 300,00 Md€ | 314,94 Md€ | 113,25 Md€ | **128,19 Md€** | **+171,81 Md€** | **5,17 € évité / € investi** |
| **10 ans** | 600,00 Md€ | 582,76 Md€ | 226,50 Md€ | **209,26 Md€** | **+390,74 Md€** | **5,88 € évité / € investi** |

**Enseignement fondamental** : À 5 ans, les stocks physiques jouent le rôle principal de
tampon d'urgence face aux pénuries immédiates. À 10 ans, la montée en puissance de la R&D
transforme l'appareil productif (baisse de l'intensité énergétique et dépendance réduite aux
composants extérieurs), rendant la combinaison **R&D + Stocks** nettement supérieure à toute
politique unilatérale.

---

## 6. Vérifications et outillage

- Commande de simulation directe : `python3 -m simulateur.innovation_prospective --horizon 5` (ou `10`, `--json`).
- Commande CLI unifiée du simulateur : `python3 -m simulateur.cli --innovation` et `python3 -m simulateur.cli --prospective`.
- API REST et Serveur Web interactif :
  - `GET /api/innovation` : rapport consolidé d'innovation et rendements R&D.
  - `GET /api/innovation/piliers` : fiches détaillées des 5 piliers technologiques souverains.
  - `GET /api/innovation/stocks` : compte complet de ressources et emplois des réserves stratégiques.
  - `GET /api/innovation/stress_test` : moteur de stress-testing multi-chocs.
  - `GET /api/prospective` : registre des fenêtres de veille et suivi d'audit des lacunes (P0/P1/P2).
  - Onglet interactif **« 🚀 Prospective & R&D (2026-2036) »** dans le dashboard web (`simulateur/web_server.py`).
- Suites de tests : `tests/test_innovation_prospective.py`, `tests/test_prospective.py`, `tests/test_cli.py`, `tests/test_web_server.py`.
- Statut de la lacune P0 : Les comptes de ressources/emplois et les coûts d'acquisition/portage
  étant formellement intégrés, la lacune P0 « Coûts économiques incomplets » dispose désormais de son
  cadre d'évaluation unifié.

---

## 7. Limites assumées

- **Pas de prophétie scientifique** : Ce module ne prédit pas la découverte fortuite d'une percée
  technologique majeure (e.g., supraconductivité à température ambiante). Il modélise les rendements
  moyens observés historiquement sur les investissements de R&D organisés.
- **Hypothèse de stabilité institutionnelle** : Les trajectoires supposent la continuité de l'effort
  budgétaire et l'absence de rupture politique abrogeant les programmes de recherche en cours.
