# 🏛️ Démocratie & Politique du Peuple, par le Peuple et pour le Peuple

> *« Un outil de décision publique, d'auditabilité républicaine et de prospective souveraine — pas un jeu, pas un divertissement, mais un instrument de la souveraineté nationale. »*
> — Article 2, alinéa 5 de la Constitution du 4 octobre 1958

---

## 📌 Présentation

Ce projet est un **simulateur systémique macro-politique** de la Ve République française, conçu comme un véritable outil d'aide à la décision publique et d'auditabilité citoyenne.

Construit autour d'un **modèle gigogne à 4 strates** (Local → National → Européen → Mondial), il permet de simuler, comparer et auditer l'intégralité des politiques publiques sur un horizon quinquennal, avec un corpus de **95 articles de loi intégraux**, **25+ sources publiques certifiées**, et **166 tests de validation**.

Ce n'est pas un wrapper autour d'une API : c'est un **moteur de simulation algorithmique autonome** en Python pur, sans dépendance externe, garantissant une traçabilité mathématique complète de chaque euro public.

---

## 🏛️ Architecture : Le Modèle Gigogne à 4 Strates

Le modèle rompt avec les tableurs linéaires statiques pour reproduire la **chaîne causale fermée de l'action publique** :

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ STRATE 4 : MONDIAL & GÉOPOLITIQUE                                       │
  │ • Agence France Trésor • Spread OAT-Bund (88 pb) • Notation (AA)        │
  │ • Pétrole Brent (ICE) & TTF • Taux Fed • Parité EUR/USD                 │
  └────────────────────────────────────┬────────────────────────────────────┘
                                       │ Taux d'intérêt, prime de risque
  ┌────────────────────────────────────▼────────────────────────────────────┐
  │ STRATE 3 : CONTINENTAL / EUROPÉEN                                       │
  │ • Commission (Procédure PDE, Art. 126 TFUE) • BCE (Taux dépôt 3,75 %)  │
  │ • Eurostat (SEC 2010) • Directive TVA 2022/542 • MACF Carbone            │
  └────────────────────────────────────┬────────────────────────────────────┘
                                       │ Contrainte de déficit & normes
  ┌────────────────────────────────────▼────────────────────────────────────┐
  │ STRATE 2 : NATIONAL / ÉTAT & SÉCURITÉ SOCIALE                           │
  │ • Budget État (LOLF Art. 34) • 430 Opérateurs • CNAM (ONDAM 255 Md€)    │
  │ • CNAV (360 Md€ retraites) • 10 Déciles (D1-D10) • 8 CSP                │
  └────────────────────────────────────┬────────────────────────────────────┘
                                       │ Règle d'or CGCT L. 1612-4 & DGF
  ┌────────────────────────────────────▼────────────────────────────────────┐
  │ STRATE 1 : LOCAL & TERRITORIAL                                          │
  │ • 34 935 communes (9 strates INSEE) • 1 254 EPCI • 101 départements     │
  │ • 18 régions • 14 territoires d'Outre-mer • 10,2 M km² ZEE              │
  └─────────────────────────────────────────────────────────────────────────┘
```

### La boucle de rétroaction causale

```
Décision Publique → Impact Local → Réaction Sociale → Filtre Parlementaire
    → Alerte Européenne → Verdict Marchés → Réinjection Budgétaire (t+1)
```

**La Règle d'or budgétaire locale (CGCT L. 1612-4) :** Toute baisse unilatérale de dotation d'État (DGF) est répercutée à 94 % en hausse de taxe foncière par les maires, déclenchant une fronde fiscale immédiate.

**L'effet boule de neige de la dette (r − g) :**
```
Δdt = [(r − g) / (1 + g)] × d(t−1) − spt
```
- Immobilisme : r − g = +1,35 pt → la dette explose.
- Plan de Mandature : r − g = −1,43 pt → **désendettement automatique**.

---

## 🚀 Pourquoi ce projet ?

À l'heure où les arbitrages budgétaires sont opaques, où les citoyens n'ont aucune visibilité sur les conséquences réelles des réformes, et où les débats politiques manquent de rigueur chiffrée, ce projet démontre qu'il est possible de :

- **Simuler** exhaustivement chaque levier d'action publique (+20 leviers)
- **Auditer** chaque euro avec une source officielle vérifiable
- **Comparer** 4 trajectoires macro-politiques à horizon quinquennal
- **Stress-tester** les politiques face aux chocs mondiaux et aux contradictions des think tanks

Ce projet s'adresse aux décideurs publics, aux chercheurs, aux citoyens éclairés et à tous ceux qui croient en une démocratie fondée sur la transparence des données et la rigueur de l'analyse.

---

## 📊 Résultats Comparatifs du Plan de Mandature (Année 5)

| Indicateur | Situation Initiale | Statut Quo (An 5) | Austérité (An 5) | **Plan Mandature** | Source |
|:---|:---:|:---:|:---:|:---:|:---|
| **Déficit public (% PIB)** | 5,07 % | 4,85 % | 4,65 % | **1,8 % (2,6 % An 4)** | INSEE / Eurostat |
| **Dette publique (% PIB)** | 118,3 % | 133,7 % | 133,3 % | **Stabilisée puis reflux** | AFT |
| **Charge nette d'intérêts** | 66,5 Md€/an | 82,4 Md€/an | 76,0 Md€/an | **56,9 Md€/an** | Direction du Budget |
| **Taux OAT France 10 ans** | 4,18 % | 4,58 % | 4,17 % | **3,35 %** | Banque de France |
| **Spread OAT-Bund** | 88,0 pb | 128,0 pb | 87,2 pb | **47,2 pb** | BCE / BDF |
| **Dynamique dette (r − g)** | +1,35 pt | +1,20 pt | +0,85 pt | **−1,43 pt** | Équation différentielle |
| **Indice de Gini** | 0,298 | 0,312 | 0,320 | **0,272** | INSEE ERFS |
| **Pauvreté monétaire (60 %)** | 14,4 % | 15,2 % | 16,5 % | **12,0 %** | DREES |
| **Gain net annuel D1-D3** | 0 € | −85 € | −140 € | **+365 €/an** | Baisse TVA énergie |
| **Confiance Ouvriers** | 48,0/100 | 28,5/100 | 22,0/100 | **74,0/100** | DARES |
| **Confiance Artisans/PME** | 52,0/100 | 35,0/100 | 30,0/100 | **82,0/100** | Allotissement 30 % PME |
| **Tension sociale territoriale** | 36,3/100 | 37,3/100 | 97,4/100 | **5,0/100** | Apaisement civique |
| **Majorité censure (AN)** | 265 voix | 275 voix | 295 voix (Chute) | **140 voix** | Seuil 289 voix |
| **Harmonie Générations (IEHI)** | 42,0/100 | 38,0/100 | 25,0/100 | **83,1/100** | Pacte 3 générations |

---

## 🖥️ Installation & Utilisation

### Prérequis

- **Python 3.9+** (Standard Library uniquement — zéro dépendance tierce obligatoire)

### Démarrage rapide

```bash
# Cloner le dépôt
git clone https://github.com/thejmimiia-code/D-mocratie-et-politique-du-peuple-pour-le-peuple-par-le-peuple.git
cd D-mocratie-et-politique-du-peuple-pour-le-peuple-par-le-peuple

# Lancer l'interface web (Cockpit Décisionnel)
python3 main.py web 8000
# → Accessible sur http://localhost:8000
```

### Commandes CLI

```bash
python3 main.py mandature      # Plan de Mandature quinquennal (+60 Md€/an)
python3 main.py statut_quo     # Scénario d'immobilisme politique
python3 main.py austerite      # Scénario d'austérité aveugle
python3 main.py choc_mondial   # Stress-test choc mondial (Pétrole >110$, Fed +150 bps)
python3 main.py comparatif     # Synthèse comparative des 4 trajectoires
python3 main.py --stress-tests # 5 paradigmes de stress-test contradictoires
python3 main.py --think-tanks  # Répertoire mondial des 23 think tanks
python3 main.py --histoire     # Base historique de la France (1792→2026)
python3 main.py --societe      # 18 domaines sociétaux avec indicateurs sourcés
python3 main.py menu           # Menu interactif en terminal
```

### Suite de tests

```bash
python3 -m unittest discover tests
# → 166 tests, 0 échec (11 HTTP skippés), ~1.1s
```

---

## 🖥️ Interface Web — 13 Onglets Experts

| Onglet | Contenu |
|:---|:---|
| 📊 **Simulateur** | Cockpit temps réel des 20 leviers d'action politique, propagation sur 5 ans |
| 📖 **Mandature** | Lecteur documentaire des volumes d'ingénierie publique |
| ⚖️ **Comparateur** | Confrontation directe des 4 trajectoires macro-politiques |
| 🏛️ **Les 4 Strates** | Visualisation causale gigogne (Local → National → Europe → Mondial) |
| 👥 **Social** | Déciles (D1-D10), Gini, pauvreté, CSP |
| 🔄 **Simulation** | Modélisation SFC temps réel |
| 🇪🇺 **Européen** | Contraintes PDE, BCE, directives |
| 📈 **Marchés** | OAT, spread, notation, matières premières |
| 📉 **Décomposition** | Ventilation détaillée des flux budgétaires |
| 💰 **Finance** | Trajectoire dette, charge d'intérêts, r − g |
| 🔬 **Think Tanks** | 23 laboratoires d'idées mondiaux, stress-tests (5 paradigmes) |
| 📚 **Histoire** | 12 périodes historiques, 19 séries temporelles (1792→2026) |
| 🌍 **Société** | 18 domaines sociétaux, indicateurs historiques, réformes, crises |

---

## 📚 Documentation — 14 Volumes de Référence

| Volume | Contenu |
|:---|:---|
| **[Dossier de Mandature](DOSSIER_DE_MANDATURE_GLOBAL.md)** | Document maître consolidé (946 lignes) : Constitutions I→VI, 20 leviers, trajectoire quinquennale |
| **[00 — Histoire & Constitutions](docs/00_HISTOIRE_CONSTITUTIONS_ET_REVENDICATIONS.md)** | Origines républicaines (Lincoln 1863), comparatif IVᵉ vs Vᵉ, think tanks |
| **[01 — Démocratie & Institutions](docs/01_DEMOCRATIE_INSTITUTIONS.md)** | Casier B2, vote blanc invalidant, RIC souverain (FranceConnect+, Helios) |
| **[02 — Recettes & Transactions](docs/02_RECETTES_ET_TRANSACTIONS.md)** | +36 Md€/an : CFIA (+10), Smart Clearing (+15), superprofits (+6), TTF (+5) |
| **[03 — Économies & Efficacité](docs/03_ECONOMIES_ET_EFFICACITE_ETAT.md)** | +24 Md€/an : fusion doublons (+8), commande publique (+6), niches (+7), fraude (+3) |
| **[04 — Pouvoir d'achat & Trajectoire](docs/04_POUVOIR_D_ACHAT_ET_TRAJECTOIRE.md)** | TVA énergie 5,5 % (−9 Md€/an), équilibre global, déficit < 3 % PIB |
| **[05 — Guide d'autodéfense](docs/05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md)** | 10 fiches de riposte : attaques, pièges, sophismes démontés |
| **[06 — Corpus juridique intégral](docs/06_CORPUS_JURIDIQUE_ET_REGLEMENTAIRE_INTEGRAL.md)** | 95 articles : Constitution, DDHC, CGI, CGCT, TFUE, Code commande publique |
| **[07 — Institutions & Chambres consulaires](docs/07_INSTITUTIONS_DE_LA_REPUBLIQUE_DROITS_ET_CHAMBRES_CONSULAIRES.md)** | Conseil constitutionnel, Cour des comptes, CCI, CMA, CA |
| **[08 — Assemblées représentatives](docs/08_ASSEMBLEES_REPRESENTATIVES_ET_DECISIONNELLES.md)** | 12 assemblées : AN (577), Sénat (348), Congrès (925), CESE, PE (720) |
| **[09 — Cycle de vie & Générations](docs/09_CYCLE_DE_VIE_ET_FLUX_INTERGENERATIONNELS.md)** | 9 périodes de vie, matrice flux croisés, IEHI |
| **[10 — Territoires & Outre-Mer](docs/10_STRATES_TERRITORIALES_OUTRE_MER_ET_FONCTIONS_ELECTORALES.md)** | 9 strates, 14 territoires ultramarins, 10,2 M km² ZEE, 8 scrutins |
| **[11 — Panorama territoires & Élections](docs/11_PANORAMA_EXHAUSTIF_TERRITOIRES_OUTRE_MER_ELECTIONS_ET_LEGISLATION.md)** | Fiches exhaustives ultramarin, modes de scrutin, 90 textes fondateurs |
| **[12 — Gouvernance budgétaire & Bercy](docs/12_GOUVERNANCE_BUDGETAIRE_ARBITRAGES_MINISTERIELS_ET_SURVIE_POLITIQUE.md)** | Profils ministres, fabrication PLF en 12 étapes, jauges de survie |
| **[13 — Sources & Auditabilité](docs/13_REGISTRE_DES_SOURCES_AUDITABILITE_ET_MODELE_SOCIO_MONDIAL.md)** | 25+ sources certifiées, 95 articles, 10 déciles, Gini, 8 CSP, SFC |
| **[14 — Think Tanks & Contradictions](docs/14_SYNTHESE_MONDIALE_DES_THINK_TANKS_ET_CONTRADICTIONS_SYSTEMIQUES.md)** | 23 think tanks (Local→Mondial), 5 stress-tests, robustesse 100 % |
| **[Plan du Simulateur](docs/PLAN_DU_SIMULATEUR_ET_AUDIT_INSTANT_T.md)** | Architecture technique & audit crash-test des redondances |

---

## 🔍 Sources & Auditabilité

Chaque donnée intégrée au simulateur est adossée à une **source publique certifiée** avec lien d'accès direct en données ouvertes :

| Catégorie | Sources |
|:---|:---|
| **Données macroéconomiques** | INSEE, Eurostat, Banque de France, FMI |
| **Finances publiques** | DGFIP, Agence France Trésor, Cour des comptes |
| **Marchés & Obligations** | BCE, Euroclear, ICE (Brent, TTF) |
| **Social & Démographie** | DREES, DARES, INED, INSEE ERFS |
| **Énergie & Climat** | Shift Project, CITEPA, RTE, CRE |
| **Droit & Institutions** | Légifrance, Conseil constitutionnel, EUR-Lex |
| **International** | OCDE, SIPRI, World Prison Brief, RSF, UNESCO |

**Principe fondamental :** *zéro paramètre orphelin* — chaque variable du modèle est traçable jusqu'à sa source officielle.

---

## 🌐 Vision & Éthique

Ce projet s'inscrit dans une démarche de **transparence démocratique totale** :

- **Neutralité politique** : le simulateur ne prend pas parti, il éclaire les conséquences
- **Auditabilité absolue** : chaque chiffre, chaque formule, chaque source est vérifiable
- **Rigueur mathématique** : modèle SFC (Stock-Flow Consistent), signatures SHA256
- **Accessibilité** : 100 % Python standard, zéro dépendance, exécutable sur tout ordinateur
- **Souveraineté des données** : aucune requête externe, aucune collecte, aucune dépendance au cloud

> *« La démocratie ne se décrète pas, elle se prouve — par la transparence des comptes, la rigueur de l'analyse et l'accessibilité des données à chaque citoyen. »*

---

## 🛡️ Communauté

| Standard | Fichier |
|:---|:---|
| 📄 Licence | [LICENSE](LICENSE) — GNU GPLv3 |
| 🤝 Code de conduite | [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — Contributor Covenant v1.4 |
| 🧭 Guide de contribution | [CONTRIBUTING.md](CONTRIBUTING.md) |
| 🔒 Politique de sécurité | [SECURITY.md](SECURITY.md) |
| 🐛 Signaler un bug | [Template Bug](/.github/ISSUE_TEMPLATE/bug_report.md) |
| ✨ Proposer une amélioration | [Template Feature](/.github/ISSUE_TEMPLATE/feature_request.md) |
| 📋 Pull Request | [Template PR](/.github/pull_request_template.md) |

---

## ⚙️ Charte Technique

| Critère | Valeur |
|:---|:---|
| **Langage** | Python 3.9+ (Standard Library) |
| **Dépendances externes** | Aucune (zéro) |
| **Architecture** | Orienté objet, multi-agents gigognes, cohérence stocks-flux (SFC) |
| **Intégrité** | Signatures SHA256 déterministes sur chaque vecteur d'état annuel |
| **Tests** | 166 tests, 0 échec, ~1.1s |
| **Documentation** | 14 volumes, 95 articles de loi, 25+ sources certifiées |
| **Interface** | Web (13 onglets, 35+ endpoints API REST) + CLI (8 commandes) |
| **Licence** | GNU GPLv3 |

---

## 📄 Licence

Ce projet est mis à disposition sous licence **[GNU General Public License v3.0](LICENSE)**.

Projet libre républicain dédié à la transparence citoyenne, à la recherche académique et à la décision publique.

---

<p align="center">
<strong>Fondé sur les valeurs de responsabilité, de loyauté, d'humanité, d'empathie, de moralité et d'éthique.</strong><br>
<a href="http://www.mrsc.fr?utm_source=github">Mouvement Représentatif de la Société Civile (MRSC)</a>
</p>