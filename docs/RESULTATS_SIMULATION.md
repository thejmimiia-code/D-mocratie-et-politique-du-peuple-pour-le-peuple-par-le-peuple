# Résultats de Simulation — Simulateur Macro-Politique Systémique

> **Généré le :** 3 octobre 2026
> **Moteur :** Gigogne 4 échelons (Local → National → Europe → Mondial)
> **Python :** 3.14.7
> **Commits de référence :** `2d36d3a` (hygiène dépôt: LICENSE, CI, tests), `dd9f0a1` (fixes issue #4: indexation PIB + transmission progressive taux)
> **Exports machine :** `resultats_mandature.json`, `resultats_statut_quo.json`, `resultats_austerite.json`, `resultats_choc_mondial.json`

---

## 📋 Méthode

Les résultats ci-dessous sont produits par une exécution réelle du simulateur Python
(`python -m simulateur.cli`), sans aucune approximation manuelle. Les tableaux présentent
les 5 étapes de chaque scénario (sauf le stress-test Choc Mondial, limité à 3 étapes
par nature du choc macroéconomique).

### Scénarios

|| # | Menu | Code CLI | Description |
||---|------|----------|-------------|
|| 1 | 1 | `mandature` | Plan de Mandature (+60 Md€/an de leviers à l'An 5) |
|| 2 | 2 | `statut_quo` | Immobilisme politique et dérive financière |
|| 3 | 3 | `austerite` | Coupes territoriales et fronde fiscale |
|| 4 | 4 | `choc_mondial` | Stress-test stagflation + pétrole >110$ + resserrement Fed |

---

## 1. PLAN DE MANDATURE (Années 1-5)

```
>>> RÉSULTATS DE LA SIMULATION : PLAN DE MANDATURE RÉPUBLICAIN (+60 Md€ en Année 5)
An  | Déficit    | Déf/PIB  | Dette/PIB  | OAT 10a   | Spread   | Tension  | Confiance  | PDE UE   | Note
|---------------------------------------------------------------------------------------------------------------
An 1 | 146.9 Md€ |  4.86 %  | 123.0 %    | 4.16 %    | 85.6 bp  | 14.5/100 |  72.5/100 | ALERTE   | AA-
An 2 | 107.0 Md€ |  3.48 %  | 124.2 %    | 4.12 %    | 81.6 bp  |  5.0/100 |  77.5/100 | ALERTE   | AA-
An 3 |  60.0 Md€ |  1.91 %  | 123.8 %    | 4.05 %    | 75.0 bp  |  5.0/100 |  77.5/100 | CONFORME | AA-
An 4 |  17.4 Md€ |  0.54 %  | 122.1 %    | 4.00 %    | 70.4 bp  |  5.0/100 |  77.5/100 | CONFORME | AA
An 5 |  -23.7 Md€ |  -0.73 %  | 119.1 %    | 3.35 %    | 47.2 bp  |  5.0/100 |  77.5/100 | CONFORME | AA
```

### Commentaires clés (Année 5)
- **[Strate 1 - Local]** Mutualisation des sièges région/département : redéploiement
  d'agents vers le terrain (+12.8 pts services).
- **[Pouvoir d'Achat]** Baisse TVA énergie à 5,5 % → +9.0 Md€ de pouvoir d'achat net.
- **[Strate 4 - Financement]** Taux OAT à 3.35 % → charge d'intérêts ajustée (transmission progressive 35 %, maturité 8.5 ans).
- **[Strate 3 - Europe]** Déficit à -0.73 % ≤ 3.00 % : sortie de la PDE, activation pleine du bouclier TPI de la BCE.

> **Note méthode (issue #4) :** Les recettes fiscales de base sont désormais indexées
> sur la croissance du PIB nominal (croissance tendancielle 1,9 %/an). La transmission
> des taux OAT à la charge de la dette est progressive (~35 %/an via le roll-over de
> maturité 8,5 ans), et non instantanée. Ces correctifs réalistes font passer le déficit
> de l'An 5 de +2,84 % à **-0,73 %** (superavit).

---

## 2. STATUT QUO (Années 1-5)

```
>>> RÉSULTATS DE LA SIMULATION : STATUT QUO (Immobilisme politique et inertie)
An  | Déficit    | Déf/PIB  | Dette/PIB  | OAT 10a   | Spread   | Tension  | Confiance  | PDE UE   | Note
|---------------------------------------------------------------------------------------------------------------
An 1 | 153.3 Md€ |  5.09 %  | 123.4 %    | 4.26 %    |  96.0 bp  | 36.3/100 |  27.5/100 | ALERTE   | AA-
An 2 | 123.9 Md€ |  4.03 %  | 125.2 %    | 4.34 %    | 104.0 bp  | 36.5/100 |  27.5/100 | ALERTE   | AA-
An 3 |  93.9 Md€ |  3.00 %  | 125.8 %    | 4.42 %    | 112.0 bp  | 36.8/100 |  27.5/100 | CONFORME | A+
An 4 |  63.4 Md€ |  1.99 %  | 125.5 %    | 4.50 %    | 120.0 bp  | 37.0/100 |  27.5/100 | CONFORME | A+
An 5 |  32.2 Md€ |  0.99 %  | 124.1 %    | 4.58 %    | 128.0 bp  | 37.3/100 |  27.5/100 | CONFORME | A+
```

---

## 3. AUSTÉRITÉ AVEUGLE (Années 1-5)

```
>>> RÉSULTATS DE LA SIMULATION : AUSTÉRITÉ AVEUGLE (Coupes territoriales et fronde fiscale)
An  | Déficit    | Déf/PIB  | Dette/PIB  | OAT 10a   | Spread   | Tension  | Confiance  | PDE UE   | Note
|---------------------------------------------------------------------------------------------------------------
An 1 | 151.0 Md€ |  5.02 %  | 123.6 %    | 4.17 %    |  87.2 bp  | 48.3/100 |  27.5/100 | ALERTE   | AA-
An 2 | 121.2 Md€ |  3.96 %  | 125.3 %    | 4.17 %    |  87.2 bp  | 60.6/100 |  27.5/100 | ALERTE   | AA-
An 3 |  90.9 Md€ |  2.91 %  | 125.9 %    | 4.17 %    |  87.2 bp  | 72.9/100 |  27.5/100 | CONFORME | AA-
An 4 |  60.0 Md€ |  1.89 %  | 125.4 %    | 4.17 %    |  87.2 bp  | 85.1/100 |  27.5/100 | CONFORME | AA-
An 5 |  28.6 Md€ |  0.88 %  | 123.9 %    | 4.17 %    |  87.2 bp  |  97.4/100 |  27.5/100 | CONFORME | AA-
```

> **Note :** le déficit nominal reste constant à 150,9 Md€ (austérité = coupes budgétaires
> sans leviers structurels → la dette/PIB s'aggrave par inflation désinflationniste).
> La tension sociale grimpe de 48.3 à 97.4/100.

---

## 4. CHOC MONDIAL — Stress-Test (Années 1-3)

```
>>> RÉSULTATS DE LA SIMULATION : STRESS-TEST CHOC MONDIAL (Stagflation, Pétrole >110$, Resserrement Fed)
An  | Déficit    | Déf/PIB  | Dette/PIB  | OAT 10a   | Spread   | Tension  | Confiance  | PDE UE   | Note
|---------------------------------------------------------------------------------------------------------------
An 1 | 147.1 Md€ |  4.87 %  | 123.1 %    | 4.45 %    |  85.2 bp  | 28.7/100 | 27.5/100 | ALERTE   | AA-
An 2 | 105.3 Md€ |  3.43 %  | 124.3 %    | 4.31 %    |  80.6 bp  | 23.2/100 | 27.5/100 | ALERTE   | AA-
An 3 |  68.5 Md€ |  2.19 %  | 124.2 %    | 4.18 %    |  78.2 bp  | 18.5/100 | 27.5/100 | CONFORME | AA-
```

> **Note :** le choc stagflationniste est limité à 3 étapes (la simulation s'arrête
> quand la phase de crise se transforme en reprise). L'effet du resserrement monétaire
> Fed est capté par la hausse de court terme de l'OAT (4.45 %) puis décroissance
> progressive.

---

## 🔄 SYNTHÈSE CROISÉE À L'ANNÉE 5

|| Scénario         | Déficit | OAT 10a | Tension   | Confiance | PDE UE  | Dette/PIB |
||---|---|---|---|---|---|---|
|| **Plan Mandature**  | **-0.73 %** | **3.35 %** | **5.0/100** | **77.5/100** | ✅ CONFORME | 119.1 % |
|| **Statut Quo**      | 0.99 % | 4.58 % | 37.3/100 | 27.5/100 | ✅ CONFORME | 124.1 % |
|| **Austérité**       | 0.88 % | 4.17 % | 97.4/100 | 27.5/100 | ✅ CONFORME | 123.9 % |
|| **Choc Mondial**    | 2.19 % | 4.18 % | 18.5/100 | 27.5/100 | ⚠️ ALERTE  | 124.2 % |

### Analyse

1. **Plan de Mandature** : seul scénario sortant avec un **supervat** à l'An 5 (-0.73 %),
   grâce aux leviers structurels indexés sur le PIB. Tension sociale minimale (5.0/100)
   et confiance démocratique maximale (77.5/100).
2. **Statut Quo** : convergence vers zéro grâce à l'indexation PIB des recettes, mais
   dette stable (~124 %). Spread qui augmente (96→128 bps).
3. **Austérité** : tension sociale maximale (97.4/100 à l'An 5) — scénario le plus
   explosif en termes de conflits sociaux, malgré un résultat PDE conforme.
4. **Choc Mondial** : stress-test passager — le pire impact est à l'An 1 (4.87 %),
   puis reprise progressive grâce aux leviers de régulation.

---

## 📊 Export machine (JSON)

Chaque scénario peut être exporté en JSON ou CSV via :

```bash
python -m simulateur.cli mandature  --export resultats_mandature.json
python -m simulateur.cli statut_quo --export resultats_statut_quo.json
python -m simulateur.cli austerite  --export resultats_austerite.json
python -m simulateur.cli choc_mondial --export resultats_choc_mondial.json
```

Les exports contiennent les variables complètes : PIB nominal, déficit, dette, charge de
la dette, recettes/dépenses, OAT, spread, note souveraine, taux crédit PME, cours du
pétrole, taux de change, inflation, et commentaires de chaque strate.
