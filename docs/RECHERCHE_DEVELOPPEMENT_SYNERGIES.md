# 🔬 Capitalisation Recherche & Développement — Synergies Inter-Dépôts

> Recherche exploratoire menée le 20/09/2026 — Dépôts, idées et technologies utiles pour l'écosystème Eva / Simulateur Démocratique.

---

## 1. Dépôts Open Source Découverts

### 1.1 Simulateur Budget France — `cturkieh/france-budget-simulateur`
- **URL** : https://github.com/cturkieh/france-budget-simulateur
- **Licence** : AGPL-3.0
- **Tests** : 337 tests
- **Description** : Moteur macro-économique open source du budget de l'État français. Simulation macro-budgétaire à 5-10 ans.
- **Synergie avec notre projet** : Approche complémentaire — ils utilisent FastAPI + handlers thématiques avec coefficients sourcés (IMF, OFCE, IPP, BdF). Notre modèle SFC à 4 strates est plus ambitieux (Local→Mondial), mais leur architecture handlers peut inspirer notre refactorisation.
- **Points forts** :
  - `policy_measures.json` pour la transparence de calibration
  - `MEASURE_REGISTRY.md` auto-généré avec verrou CI anti-drift
  - Scénarios politiques paramétrés (LR 2027, Renaissance 2027)
  - Licence AGPL (plus restrictive que notre GPLv3, mais garantit la publication des forks)
- **Action recommandée** : Étudier leur architecture handlers pour modulariser notre moteur

### 1.2 SFC Models — `brianr747/SFC_models`
- **URL** : https://github.com/brianr747/SFC_models
- **Licence** : Apache-2.0
- **Stars** : 41
- **Description** : Stock-Flow Consistent models in Python. Cadre algorithmique pour construire et résoudre des modèles SFC.
- **Synergie** : C'est exactement le formalisme mathématique que nous utilisons (Godley & Lavoie). Leur approche génère les équations algorithmiquement à partir des connexions entre secteurs.
- **Points forts** :
  - Implémentation des modèles Godley-Lavoie (SIM, PC, REG)
  - Solveur itératif pour les modèles multi-équations
  - Architecture Sector/Model orientée objet
- **Action recommandée** : Vérifier la compatibilité de notre solveur SFC avec leurs conventions de nommage

### 1.3 Monetary Economics — `kennt/monetary-economics`
- **URL** : https://github.com/kennt/monetary-economics
- **Description** : Implémentation Python des modèles de Godley & Lavoie « Monetary Economics »
- **Synergie** : Référence académique pour notre modèle SFC. Notebooks IPython documentés.
- **Action recommandée** : Utiliser comme benchmark de validation de notre moteur

### 1.4 Electoral Systems Simulator — `mukhes3/electoral_sim`
- **URL** : https://github.com/mukhes3/electoral_sim
- **Article** : arXiv:2603.08752 (mars 2026)
- **Description** : Framework Python pour simuler et comparer les systèmes électoraux (plurinominal, approbation, Condorcet, proportionnelle)
- **Synergie** : Directement pertinent pour notre module « Démocratie & Droits ». Peut enrichir notre simulateur avec des métriques de représentativité.
- **Points forts** :
  - 10 systèmes électoraux implémentés
  - 8 scénarios de distribution des électeurs
  - Métrique : distance euclidienne outcome/médiane géométrique
  - Architecture modulaire (YAML config, sous-classes)
- **Action recommandée** : Intégrer les métriques de représentativité dans notre module démocratie

### 1.5 AgentSociety — `tsinghua-fib-lab/AgentSociety`
- **URL** : https://github.com/tsinghua-fib-lab/AgentSociety
- **Description** : Simulation sociale à grande échelle (10k+ agents, 5M interactions) avec agents LLM
- **Synergie** : Approche bottom-up complémentaire à notre modèle top-down. Peut servir de référence pour modéliser les réactions sociales aux politiques.
- **Action recommandée** : Surveiller l'évolution — intégration future possible

### 1.6 OpenFisca — `openfisca/calculette-impots-m-source-code`
- **URL** : https://github.com/openfisca/calculette-impots-m-source-code
- **Licence** : CeCILL 2.1
- **Description** : Code source officiel DGFIP du calculateur d'impôts sur le revenu (langage M)
- **Synergie** : Source primaire pour notre corpus juridique fiscal (95 articles). Permet de vérifier la cohérence de nos paramètres de simulation.
- **Action recommandée** : Référencer dans notre registre des sources officielles

### 1.7 AI-Geopol-Projects — `danielrosehill/AI-Geopol-Projects`
- **URL** : https://github.com/danielrosehill/AI-Geopol-Projects
- **Description** : Collection de projets IA pour la simulation géopolitique
- **Synergie** : Références pour notre Strate 4 (Mondial & Géopolitique)
- **Projets notables** :
  - **MiroFish-Offline** : Moteur d'intelligence collective multi-agents (100% local, Ollama + Neo4j)
  - **AI Diplomacy** : Modèles frontières jouant à Diplomatie
  - **OpenPolicyStack** : Stack modulaire open source pour l'aide à la décision politique

---

## 2. Idées d'Optimisation Identifiées

### 2.1 Architecture Handler (inspiré de france-budget-simulateur)
```python
# Concept : chaque mesure fiscale = un handler avec sources
class HandlerMesure:
    nom: str
    coefficient: float
    source: str  # URL papier académique
    intervalle_confiance: Tuple[float, float]
    
    def appliquer(self, contexte: ContexteSimulation) -> ImpactMesure:
        ...
```
**Avantage** : Traçabilité coefficient→source, verrou CI anti-drift

### 2.2 Registre de Mesures Auto-généré (inspiré de france-budget-simulateur)
- Générer automatiquement un `MEASURE_REGISTRY.md` à partir du code
- Verrou CI : toute modification de coefficient sans source = échec build
- **Action** : À implémenter dans une prochaine itération

### 2.3 Métriques de Représentativité Électorale (inspiré de electoral_sim)
```python
def distance_geometrique_mediane(resultats_election, positions_electeurs):
    """Distance euclidienne entre l'outcome et la médiane géométrique"""
    mediane = np.median(positions_electeurs, axis=0)
    outcome = np.mean(resultats_election, axis=0)
    return np.linalg.norm(outcome - mediane)
```
**Avantage** : Mesure objective de la qualité démocratique

### 2.4 Validation Croisée avec SFC_models
- Comparer nos résultats avec les modèles Godley-Lavoie de référence
- SIM (modèle simple), PC (perspective comportementale), REG (régional)
- **Action** : Créer un test de validation croisée

---

## 3. Optimisations du Code Existant

### 3.1 Relecture Effectuée
| Module | Lignes | Statut | Observations |
|:---|:---:|:---:|:---|
| `model.py` | 1041 | ✅ | Architecture solide, 4 strates bien typées |
| `moteur.py` | 655 | ✅ | SFC correct, boucle causale fermée |
| `web_server.py` | 4826 | ✅ | 13 onglets, 35+ endpoints |
| `enrichissement_historique.py` | 955 | ✅ | 12 séries, 329 points |
| `societe_domaines.py` | 897 | ✅ | 18 domaines |
| `histoire_france.py` | 1535 | ✅ | 12 périodes |
| `think_tanks.py` | 1386 | ✅ | 23 think tanks |
| `reglements_lois.py` | 966 | ✅ | 95 articles |
| `sources_officielles.py` | 573 | ✅ | 25+ sources |
| `cli.py` | 291 | ✅ | 8 commandes |
| `scenarios.py` | 163 | ✅ | 4 scénarios |

**Total** : 16 220 lignes de code, 222 tests, 0 échec

### 3.2 Points d'Amélioration Identifiés
1. **Typage** : Ajouter des type hints manquants dans `web_server.py`
2. **Docstrings** : Compléter les docstrings des fonctions d'accès dans `enrichissement_historique.py`
3. **Tests** : Ajouter des tests d'intégration pour les endpoints API enrichis
4. **Documentation** : Créer un `docs/METHODOLOGIE.md` (inspiré de france-budget-simulateur)

---

## 4. Prochaines Étapes Recommandées

### Court terme (cette session)
- [x] Recherche et capitalisation des dépôts utiles
- [x] Identification des synergies
- [x] Relecture complète du code
- [x] Documentation des optimisations

### Moyen terme (prochaine session)
- [ ] Implémenter le registre de mesures auto-généré
- [ ] Ajouter les métriques de représentativité électorale
- [ ] Créer le test de validation croisée SFC
- [ ] Rédiger `docs/METHODOLOGIE.md`

### Long terme
- [ ] Étudier l'intégration d'OpenFisca pour le calcul fiscal
- [ ] Explorer MiroFish-Offline pour la simulation multi-agents
- [ ] Contribuer à electoral_sim pour le cas français

---

## 5. Sources et Références

| Projet | URL | Pertinence |
|:---|:---|:---|
| france-budget-simulateur | github.com/cturkieh/france-budget-simulateur | Architecture handlers |
| SFC_models | github.com/brianr747/SFC_models | Formalisme SFC |
| monetary-economics | github.com/kennt/monetary-economics | Godley-Lavoie |
| electoral_sim | github.com/mukhes3/electoral_sim | Systèmes électoraux |
| AgentSociety | github.com/tsinghua-fib-lab/AgentSociety | Simulation sociale |
| OpenFisca | github.com/openfisca/calculette-impots-m-source-code | Code source fiscal |
| AI-Geopol-Projects | github.com/danielrosehill/AI-Geopol-Projects | Géopolitique IA |
| OpenPolicyStack | github.com/OscarDiez/OpenPolicyStack | Stack politique IA |

---

---

## 6. Cycle 2 — Nouvelles Découvertes (20/09/2026)

### 6.1 Mesa — Framework ABM de référence
- **URL** : https://github.com/mesa/mesa
- **Stars** : 3 800+
- **Description** : Framework Python standard pour la modélisation par agents. Idéal pour simuler des systèmes complexes et explorer les comportements émergents.
- **Synergie** : Notre moteur SFC pourrait être enrichi par des agents autonomes (ménages, entreprises, État) utilisant Mesa pour modéliser les interactions micro-économiques.
- **Extensions notables** :
  - `mesa-geo` (223 stars) : Extension GIS pour la modélisation spatiale
  - `mesa-llm` (71 stars) : Intégration LLM directement dans les agents
- **Action recommandée** : Prototype d'un modèle multi-agents pour la Strate 1 (Local)

### 6.2 Concordia — Google DeepMind
- **URL** : https://github.com/google-deepmind/concordia
- **Stars** : 1 700+
- **Description** : Bibliothèque de simulation sociale générative. Agents avec personnalités, mémoires et objectifs distincts.
- **Synergie** : Référence académique pour modéliser les réactions sociales aux politiques publiques.
- **Action recommandée** : Étudier l'architecture pour enrichir notre module Société (18 domaines)

### 6.3 OASIS — Simulation à 1 Million d'Agents
- **URL** : https://github.com/camel-ai/oasis
- **Stars** : Élevé
- **Description** : Simulateur de médias sociaux à grande échelle (1M agents). Modélise la propagation d'information, la polarisation de groupe et le comportement grégaire.
- **Synergie** : Directement pertinent pour notre module Médias & Information et pour modéliser l'opinion publique face aux réformes.
- **Action recommandée** : Intégrer les métriques de polarisation dans le simulateur

### 6.4 SocioVerse — Fudan University
- **URL** : https://github.com/FudanDISC/SocioVerse
- **Description** : Modèle du monde pour simulation sociale avec 10 millions d'utilisateurs réels.
- **Synergie** : Validation empirique de nos hypothèses sur les réactions sociales.
- **Action recommandée** : Référence pour calibrer nos modèles de comportement électoral

### 6.5 PolicySpace — Redistribution Fiscale
- **URL** : https://github.com/BAFurtado/PolicySpace
- **Stars** : 23
- **Description** : Modèle multi-agents pour évaluer la redistribution fiscale entre municipalités.
- **Synergie** : DIRECTEMENT pertinent pour notre Strate 1 (Local) et la règle d'or CGCT L. 1612-4.
- **Action recommandée** : Étudier leur modèle pour enrichir notre simulation territoriale

### 6.6 wealth-inequality-abm — Inégalités avec Gini
- **URL** : https://github.com/cconsta1/wealth-inequality-abm
- **Description** : Modèle Mesa simulant l'émergence des inégalités de richesse avec coefficient de Gini.
- **Synergie** : Validation de nos séries Gini (30 points, 1970→2023) par simulation bottom-up.
- **Action recommandée** : Comparer les résultats de simulation avec nos données historiques

### 6.7 Helipad — Framework ABM Économique
- **URL** : https://github.com/charwick/helipad
- **Documentation** : https://helipad.dev
- **Licence** : MIT
- **Description** : Framework ABM Python avec courbe d'apprentissage faible, grande flexibilité et visualisation puissante.
- **Synergie** : Alternative légère à Mesa pour prototyper rapidement des modèles économiques.
- **Action recommandée** : Évaluer pour les prototypes rapides

### 6.8 ESL — Economic Simulation Library
- **URL** : https://github.com/INET-Complexity/ESL
- **Stars** : 76
- **Description** : Bibliothèque extensive pour développer, tester et calibrer des modèles multi-agents économiques et financiers. Supporte le calcul parallèle.
- **Synergie** : Référence INET pour la modélisation macroéconomique ABM.
- **Action recommandée** : Étudier les méthodes de calibration

### 6.9 Impact Evaluation of Public Policy
- **URL** : https://github.com/andreasoledadguerra/impact-evaluation-of-public-policy
- **Description** : Pipeline Python modulaire pour évaluer l'impact causal des politiques publiques (design expérimental, analyse statistique, reproductibilité).
- **Synergie** : Méthodologie d'évaluation d'impact transférable à notre simulateur pour valider les scénarios.
- **Action recommandée** : Intégrer la méthodologie d'évaluation d'impact dans les tests de robustesse

### 6.10 AgentTorch — ABM Différenciable à Grande Échelle
- **URL** : https://github.com/AgentTorch
- **Description** : Modélisation multi-agents différenciable supportant des millions d'agents. Utilisé pour la simulation pandémique et l'économie.
- **Synergie** : Performance et scalabilité pour les simulations à grande échelle.
- **Action recommandée** : Surveiller l'évolution pour les futures optimisations

---

## 7. Synthèse des Priorités

### Haute priorité (intégration immédiate)
1. **Mesa** : Framework standard pour ABM — à intégrer comme option de simulation bottom-up
2. **PolicySpace** : Modèle de redistribution fiscale — directement pertinent
3. **wealth-inequality-abm** : Validation Gini par simulation

### Moyenne priorité (prochaine session)
4. **Concordia** : Simulation sociale générative
5. **OASIS** : Métriques de polarisation
6. **ESL** : Méthodes de calibration

### Basse priorité (veille)
7. **Helipad** : Alternative légère
8. **AgentTorch** : Scalabilité future
9. **SocioVerse** : Validation empirique

---

*Document généré automatiquement — Cycles de recherche & développement du 20/09/2026*