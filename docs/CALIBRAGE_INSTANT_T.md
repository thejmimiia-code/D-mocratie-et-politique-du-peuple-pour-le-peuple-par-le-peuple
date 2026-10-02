# Fichier de Calibrage — Instant T (Septembre 2026)

> **Date de calibration :** septembre 2026
> **Source unique de vérité :** `simulateur/model.py` — `EchelonNational`, `EchelonMondial`, `EchelonLocal`, `EchelonEuropeen`
> **Règle :** toute valeur affichée dans le README, le CLI ou les exports JSON doit être **identique** à celle définie dans `model.py`. Ce fichier liste les données de référence et leurs sources publiques.

---

## 📅 Date de référence

| Champ | Valeur | Source |
|---|---|---|
| Date d'instant T | Septembre 2026 | `model.py` docstring + conventions de projet |
| PIB nominal (France) | 3 015 Md€ | INSEE — Compte national, niveau de vie (2026, est. projeté) |
| Taux de change EUR/USD | 1,08 | Banque de France — série historique (2026-09) |
| Pétrole Brent | 82,5 USD/baril | ICE/Brent spot (2026-09) |
| Taux OAT 10 ans | 4,18 % | Actualisation par rapport aux spreads SDE — données BCE/France |
| Bund allemand 10 ans | 3,30 % | Banque centrale allemande (Bundesbank) |
| Spread OAT-Bund | 88 bps | Différence directe (4,18 % - 3,30 %) |
| Note souveraine | AA- | S&P / Fitch (sept. 2026) |
| Dette publique consolidée | 3 568 Md€ (~118,9 % PIB) | INSEE — Dette publique (2026) |
| Tension sociale locale | 36,0 / 100 | Indice interne ÉVA (grogne contribuables + usagers) |
| Confiance démocratique | 27,5 / 100 | IFOP — Baromètre confiance institutions (2026-09) |

---

## 🧮 Tableau de correspondance (README ↔ model.py ↔ résultats)

| Indicateur | model.py (instant T) | README An 5 (corrigé) | Résultat simulation An 5 |
|---|---|---|---|
| **Déficit public** | 145 Md€ (5,07 % PIB) | 2,84 % (92,5 Md€) | 2,84 % (92,5 Md€) |
| **Dette souveraine** | 3 568 Md€ (118,9 % PIB) | 128,1 % PIB | 128,1 % PIB |
| **Taux OAT 10 ans** | 4,18 % | 3,35 % | 3,35 % |
| **Spread OAT-Bund** | 88 bps | 47,2 bps | 47,2 bps |
| **Tension sociale** | 36,0/100 | 5,0/100 | 5,0/100 |
| **Confiance démocrate** | 27,5/100 | 77,5/100 | 77,5/100 |
| **Charge annuelle dette** | 66,5 Md€ | — | — |
| **Prix Brent** | 82,50 USD | — | — |
| **Cours gaz TTF** | 38,00 €/MWh | — | — |
| **Carbon market (ETS)** | 72 €/t | — | — |
| **Facture énergie nette** | 64,5 Md€ | — | — |
| **Taux Fed Funds** | 5,33 % | — | — |
| **Taux BCE dépôt** | 3,75 % | — | — |
| **Inflation globale** | 2,1 % | — | — |
| **Taux crédit PME** | 4,90 % | — | — |
| **Taux crédit immobilier** | 3,85 % | — | — |
| **Part dette non-résidents** | 55,8 % | — | — |
| **Maturité dette moyenne** | 8,5 ans | — | — |

---

## 🔧 Incohérences corrigées (issue #5)

Les incohérences suivantes ont été détectées et corrigées :

1. **README → model.py discrepancy** :
   - OAT initial : README disait 4,15 % → model.py = 4,18 % ✅
   - Spread initial : README disait 85,0 bps → model.py = 88,0 bps ✅
   - Tension sociale initiale : README disait 35,0 → model.py = 36,0 ✅
   - Confiance initial : README disait 28,0 → model.py = 27,5 ✅
   - Déficit initial : README disait 152 Md€ → model.py = 145 Md€ ✅

2. **Section V README → Résultats simulation** :
   - Déficit An 5 : 2,79 % → 2,84 % (valeur simulation réelle)
   - OAT An 5 : 3,22 % → 3,35 % (valeur simulation réelle)
   - Spread An 5 : 46,8 bps → 47,2 bps (valeur simulation réelle)
   - Confiance An 5 : 78,0 → 77,5 (valeur simulation réelle)
   - Dette An 5 : ~129 % → 128,1 % (valeur simulation réelle)

3. **Ajout de date source** : toutes les valeurs sont calées sur "septembre 2026" avec provenance INSEE/Banque de France/BCE/S&P.

---

## 🔄 Procédure de vérification avant commit

1. Simuler : `python -m simulateur.cli <scenario> --export resultats.json`
2. Extraire les valeurs JSON `ratio_deficit_pib`, `taux_oat_pct`, `spread_bund_bps`, `tension_sociale_locale`, `confiance_democratique`
3. Comparer avec `docs/RESULTATS_SIMULATION.md`
4. Toute différence >0,1 pt = échec de la CI

> Source du choc : émis par la CI GitHub Actions (`.github/workflows/ci.yml`).
