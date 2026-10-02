# Résultats de Simulation — Simulateur Macro-Politique Systémique

> **Généré le :** 2 octobre 2026
> **Moteur :** Gigogne 4 échelons (Local → National → Europe → Mondial)
> **Python :** 3.14.7
> **Commits de référence :** `d06b6a0` (enrichissement), `7536de7` (dossier de mandature)
> **Exports machine :** `resultats_mandature.json`, `resultats_statut_quo.json`, `resultats_austerite.json`, `resultats_choc_mondial.json`

---

## 📋 Méthode

Les résultats ci-dessous sont produits par une exécution réelle du simulateur Python
(`python -m simulateur.cli`), sans aucune approximation manuelle. Les tableaux présentent
les 5 étapes de chaque scénario (sauf le stress-test Choc Mondial, limité à 3 étapes
par nature du choc macroéconomique).

### Scénarios

| # | Menu | Code CLI | Description |
|---|------|----------|-------------|
| 1 | 1 | `mandature` | Plan de Mandature (+60 Md€/an de leviers à l'An 5) |
| 2 | 2 | `statut_quo` | Immobilisme politique et dérive financière |
| 3 | 3 | `austerite` | Coupes territoriales et fronde fiscale |
| 4 | 4 | `choc_mondial` | Stress-test stagflation + pétrole >110$ + resserrement Fed |

---

## 1. PLAN DE MANDATURE (Années 1-5)

```
>>> RÉSULTATS DE LA SIMULATION : PLAN DE MANDATURE RÉPUBLICAIN (+60 Md€ en Année 5)
An  | Déficit    | Déf/PIB  | Dette/PIB  | OAT 10a   | Spread   | Tension  | Confiance  | PDE UE   | Note
---------------------------------------------------------------------------------------------------------------
An 1 | 146.8 Md€ |  4.86 %  | 123.0 %    | 4.16 %    | 85.6 bp  | 14.5/100 |  72.5/100 | ALERTE   | AA-
An 2 | 136.3 Md€ |  4.43 %  | 125.2 %    | 4.12 %    | 81.6 bp  |  5.0/100 |  77.5/100 | ALERTE   | AA-
An 3 | 119.0 Md€ |  3.80 %  | 126.6 %    | 4.05 %    | 75.0 bp  |  5.0/100 |  77.5/100 | ALERTE   | AA-
An 4 | 106.9 Md€ |  3.35 %  | 127.6 %    | 4.00 %    | 70.4 bp  |  5.0/100 |  77.5/100 | ALERTE   | AA-
An 5 |  92.5 Md€ |  2.84 %  | 128.1 %    | 3.35 %    | 47.2 bp  |  5.0/100 |  77.5/100 | CONFORME | AA
```

### Commentaires clés (Année 5)
- **[Strate 1 - Local]** Mutualisation des sièges région/département : redéploiement
  d'agents vers le terrain (+12.8 pts services).
- **[Pouvoir d'Achat]** Baisse TVA énergie à 5,5 % → +9.0 Md€ de pouvoir d'achat net.
- **[Strate 3 - Europe]** Déficit à 2.84 % ≤ 3.00 % : sortie de la PDE, activation pleine
  du bouclier TPI de la BCE.

---

## 2. STATUT QUO (Années 1-5)

```
>>> RÉSULTATS DE LA SIMULATION : STATUT QUO (Immobilisme politique et inertie)
An  | Déficit    | Déf/PIB  | Dette/PIB  | OAT 10a   | Spread   | Tension  | Confiance  | PDE UE   | Note
---------------------------------------------------------------------------------------------------------------
An 1 | 153.9 Md€ |  5.11 %  | 123.5 %    | 4.26 %    | 96.0 bp  | 36.3/100 |  27.5/100 | ALERTE   | AA-
An 2 | 154.8 Md€ |  5.04 %  | 126.2 %    | 4.34 %    | 104.0 bp | 36.5/100 |  27.5/100 | ALERTE   | AA-
An 3 | 155.8 Md€ |  4.98 %  | 128.8 %    | 4.42 %    | 112.0 bp | 36.8/100 |  27.5/100 | ALERTE   | A+
An 4 | 156.7 Md€ |  4.91 %  | 131.3 %    | 4.50 %    | 120.0 bp | 37.0/100 |  27.5/100 | ALERTE   | A+
An 5 | 157.6 Md€ |  4.85 %  | 133.7 %    | 4.58 %    | 128.0 bp | 37.3/100 |  27.5/100 | ALERTE   | A+
```

---

## 3. AUSTÉRITÉ AVEUGLE (Années 1-5)

```
>>> RÉSULTATS DE LA SIMULATION : AUSTÉRITÉ AVEUGLE (Coupes territoriales et fronde fiscale)
An  | Déficit    | Déf/PIB  | Dette/PIB  | OAT 10a   | Spread   | Tension  | Confiance  | PDE UE   | Note
---------------------------------------------------------------------------------------------------------------
An 1 | 150.9 Md€ |  5.02 %  | 123.6 %    | 4.17 %    | 87.2 bp  | 48.3/100 |  27.5/100 | ALERTE   | AA-
An 2 | 150.9 Md€ |  4.92 %  | 126.2 %    | 4.17 %    | 87.2 bp  | 60.6/100 |  27.5/100 | ALERTE   | AA-
An 3 | 150.9 Md€ |  4.83 %  | 128.7 %    | 4.17 %    | 87.2 bp  | 72.9/100 |  27.5/100 | ALERTE   | AA-
An 4 | 150.9 Md€ |  4.74 %  | 131.1 %    | 4.17 %    | 87.2 bp  | 85.1/100 |  27.5/100 | ALERTE   | AA-
An 5 | 150.9 Md€ |  4.65 %  | 133.3 %    | 4.17 %    | 87.2 bp  | 97.4/100 |  27.5/100 | ALERTE   | AA-
```

> **Note :** le déficit nominal reste constant à 150,9 Md€ (austérité = coupes budgétaires
> sans leviers structurels → le déficit nominal ne s'améliore pas, mais la dette/PIB
> s'aggrave par inflation désinflationniste). La tension sociale grimpe de 48.3 à 97.4/100.

---

## 4. CHOC MONDIAL — Stress-Test (Années 1-3)

```
>>> RÉSULTATS DE LA SIMULATION : STRESS-TEST CHOC MONDIAL (Stagflation, Pétrole >110$, Resserrement Fed)
An  | Déficit    | Déf/PIB  | Dette/PIB  | OAT 10a   | Spread   | Tension  | Confiance  | PDE UE   | Note
---------------------------------------------------------------------------------------------------------------
An 1 | 149.1 Md€ |  4.94 %  | 123.2 %    | 4.45 %    | 85.2 bp  | 28.7/100 |  27.5/100 | ALERTE   | AA-
An 2 | 136.0 Md€ |  4.43 %  | 125.4 %    | 4.31 %    | 80.6 bp  | 23.2/100 |  27.5/100 | ALERTE   | AA-
An 3 | 128.5 Md€ |  4.10 %  | 127.2 %    | 4.18 %    | 78.2 bp  | 18.5/100 |  27.5/100 | ALERTE   | AA-
```

> **Note :** le choc stagflationniste est limité à 3 étapes (la simulation s'arrête
> quand la phase de crise se transforme en reprise). L'effet du resserrement monétaire
> Fed est capté par la hausse de court terme de l'OAT (4.45 %) puis décroissance
> progressive.

---

## 🔄 SYNTHÈSE CROISÉE À L'ANNÉE 5

| Scénario         | Déficit | OAT 10a | Tension | Confiance | PDE UE  | Dette/PIB |
|---|---|---|---|---|---|---|
| **Plan Mandature**  | **2.84 %** | **3.35 %** | **5.0/100** | **77.5/100** | ✅ CONFORME | 128.1 % |
| **Statut Quo**      | 4.85 % | 4.58 % | 37.3/100 | 27.5/100 | ⚠️ ALERTE | 133.7 % |
| **Austérité**       | 4.65 % | 4.17 % | 97.4/100 | 27.5/100 | ⚠️ ALERTE | 133.3 % |
| **Choc Mondial**    | 4.10 % | 4.18 % | 18.5/100 | 27.5/100 | ⚠️ ALERTE | 127.2 % |

### Analyse

1. **Plan de Mandature** : le seul scénario sortant de la PDE à l'An 5 (2.84 % ≤ 3 %),
   avec la plus basse tension sociale (5.0/100) et la plus haute confiance démocratique.
2. **Statut Quo** : trajectoire exponentielle de la dette (123→134 %) et du spread
   (85→128 bps). Risque de percolation vers la zone euro.
3. **Austérité** : tension sociale maximale (97.4/100 à l'An 5) — scénario le plus
   explosif en termes de conflits sociaux.
4. **Choc Mondial** : stress-test passager — le pire impact est à l'An 1 (4.94 % de
   déficit), puis reprise progressive.

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
