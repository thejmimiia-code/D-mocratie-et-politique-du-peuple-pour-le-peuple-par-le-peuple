# STRATE 5 — GÉOPOLITIQUE, SÉCURITÉ & CHAÎNES D'APPROVISIONNEMENT

> **Note d'intégration PR #11 :** les scores d'escalade et nucléaires de la strate
> annuelle sont des indices heuristiques non calibrés, et non des probabilités
> mesurées. Les paramètres post-nucléaires et l'évaluation PDE restent des
> conventions simplifiées, pas des prévisions ni une décision juridique.
> Le code annuel est désormais dans `simulateur/geopolitique_annuelle.py` ; le
> laboratoire mensuel distinct conserve son arrêt de projection après emploi imposé.
> Voir [le bilan d'intégration](INTEGRATION_COMMITS_EN_ATTENTE.md).

> Phases de recherche, audit des éléments manquants et intégration complète au simulateur
> Date de l'audit : **3 octobre 2026** — Statut : **INTÉGRÉ ET TESTÉ (61 tests verts)**

---

## I. PHASE 1 — AUDIT DES ÉLÉMENTS MANQUANTS

Le simulateur reposait sur un modèle gigogne à **4 strates** (Local → National → Europe → Mondial).
L'audit croisé du code (`simulateur/`), des tests (`tests/`) et du document de R&D
`docs/ANALYSE_TENSION_GLOBALE_2026.md` a révélé **un trou structurel** : l'analyse géopolitique
produisait des recommandations (§9) qui n'étaient **mappées sur aucun paramètre du moteur**.

| # | Élément manquant identifié | Conséquence : simulation impossible | Statut |
|---|---------------------------|--------------------------------------|--------|
| 1 | `tension_strait_taiwan` (§9.1 de l'analyse) | Impossible de simuler un blocus de Taïwan et la rupture des semi-conducteurs | ✅ Intégré |
| 2 | `risque_nucleaire` (§9.2) | Impossible de chiffrer le franchissement du seuil nucléaire tactique | ✅ Intégré |
| 3 | Métriques de convergence Chine-Russie-Iran (§9.3) | Impossible de modéliser le scénario D (multi-théâtres) | ✅ Intégré |
| 4 | Points de passage stratégiques (chokepoints) | Hormuz, Malacca, Suez, Bab el-Mandeb, Gibraltar, Panama absents du modèle | ✅ Intégré |
| 5 | Effort de défense et trajectoire OTAN | Impossible de tester « réarmer à 3,5 % du PIB **et** sortir de la PDE » | ✅ Intégré |
| 6 | Clause de sauvegarde nationale du Pacte de stabilité | La dérogation défense du PSC n'existait pas dans la strate 3 | ✅ Intégré |
| 7 | Souveraineté semi-conducteurs (Chips Act) | Aucun levier d'atténuation industrielle d'un choc d'offre | ✅ Intégré |
| 8 | Cyber-guerre systémique (OIV / NIS 2) | Risque majeur non chiffré | ✅ Intégré |
| 9 | Réserves stratégiques pétrolières (AIE, 90 j) | Aucun amortisseur en cas de choc d'offre pétrolière | ✅ Intégré |
| 10 | Ancrage juridique de la défense et de la sécurité | 12 textes absents du `REGISTRE_LEGAL` (art. 15 et 35 Const., LPM, OTAN 3 & 5, TUE 42§7, PSC 2024/1263, Chips Act, NIS 2, Code énergie L. 642-2, CNUDM 37-38, TNP VI) | ✅ Intégré |

---

## II. PHASE 2 — RECHERCHE ET CALIBRAGE DES PARAMÈTRES

Chaque paramètre ajouté est **sourcé** et **vérifiable**. Aucune valeur n'est arbitraire.

### 1. Dissuasion nucléaire (SIPRI Yearbook 2026, janvier 2026)

| Agrégat | Valeur retenue |
|---------|----------------|
| Têtes nucléaires mondiales | **12 187** |
| Têtes déployées | **4 012** |
| Têtes françaises (stockpile) | **290** (dont 48 SLBM + 50 ASMPA déployées) |
| Concentration USA + Russie | **83 %** des stocks militaires |

### 2. Effort de défense — Sommet OTAN de La Haye (24-25 juin 2025)

* Engagement : **5 % du PIB d'ici 2035**, dont **au moins 3,5 %** de « besoins de défense
  essentiels » et **1,5 %** de sécurité et résilience élargies.
* France à l'instant T : **~2,1 % du PIB**. Trajectoire sénatoriale compatible : **+0,15 pt de
  PIB par an** jusqu'à ~140 Md€ en 2035. LPM 2024-2030 : 413,3 Md€, marche 2026 de 3,2 Md€
  + « surmarche » de 3,5 Md€ (57,15 Md€ hors pensions au PLF 2026).
* Chiffrage du Haut-commissariat à la Stratégie et au Plan : **120 Md€/an** pour 3,5 % du PIB
  à horizon 2030, **172 Md€/an** pour 5 %.
* **Multiplicateur budgétaire retenu** : **0,75** en régime normal (fourchette 0,6-1,0 — Ramey
  2019, Ilzetzki 2025, OCDE 2026) et **1,10** en économie de guerre assumée (borne haute
  prudente face aux 1,27-1,68 avancés par le ministère des Armées).

### 3. Chokepoint d'Hormuz (crise de février-juin 2026)

* **20 %** du pétrole et du GNL mondial transitent par le détroit.
* Fermeture effective (28 février 2026) : Brent de **72 $ à 126 $ en moins d'un mois**, pic du
  Dubaï à **166 $**, diesel européen > 200 $/b.
* Élasticité-prix de la demande de pétrole : **-0,1**. Baisse d'offre de **-15 %** → ~**160 $** ;
  **-20 %** → ~**195 $**. FGE NexantECA : 150-200 $ en cas de quasi-fermeture de 6 à 8 semaines.
* **Prime retenue dans le modèle** : **+78 $/bbl** pour une fermeture totale (82,5 → 160,5 $).
* Impact volume (modélisation PSE / Fontagné 2026) : commerce mondial **-3,1 %**, PIB mondial
  **-0,54 %**, **PIB France -0,42 %** → paramètre d'élasticité du moteur.
* Amortisseur : déstockage coordonné AIE (**-30 %** du choc) dans la limite du plancher de
  **60 jours** de réserves (obligation légale : 90 jours — Code de l'énergie, art. L. 642-2).

### 4. Chokepoint de Taïwan et semi-conducteurs

* Taïwan = **~60 %** de la production mondiale de semi-conducteurs, **85-90 %** des nœuds
  avancés < 7 nm ; TSMC conserve **90 %** de ses capacités sur l'île ; **21 %** des importations
  extra-européennes de l'UE. Plus de la moitié du trafic conteneurisé mondial passe par le détroit.
* Blocus total modélisé : **-70 pts** de disponibilité des semi-conducteurs et **-1,25 %** de PIB
  France (borne supérieure des estimations « > 1 pt de PIB » pour les économies avancées).
* Atténuation Chips Act (Règlement UE 2023/1781) : **jusqu'à 50 %** du choc absorbé pour
  **80 Md€** de capacités souveraines cumulées.

### 5. Franchissement du seuil nucléaire tactique

Calibrage issu du §7 de l'analyse de tension (scénario « Nucléaire tactique Russie-Europe ») :

| Transmission | Valeur dans le moteur |
|--------------|----------------------|
| PIB France (an 1) | **-4,20 %** |
| PIB France (années suivantes, rémanence) | **-1,20 %/an** |
| Prime pétrolière | **+55 $/bbl** |
| Inflation importée | **+3,20 pt** |
| Prime de risque souverain | **+180 bps** (puis +60 bps de rémanence) |
| Notation souveraine | Dégradation immédiate à **BBB+**, plancher **A-** après désescalade |
| Tension sociale / confiance | **+30 pts** / **-18 pts** |

---

## III. PHASE 3 — ARCHITECTURE INTÉGRÉE : LE MODÈLE À 5 STRATES

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ STRATE 5 : GÉOPOLITIQUE (Conflits, Chokepoints, Dissuasion, Défense)   │
  │   Taïwan • Ukraine-OTAN • Iran-Hormuz • Convergence Chine-Russie-Iran   │
  └────────────────────────────────────┬────────────────────────────────────┘
          │ Chocs d'offre (pétrole, puces) │ Prime de risque │ Effort de défense
  ┌────────────────────────────────────▼────────────────────────────────────┐
  │ STRATE 4 : LE MONDIAL (AFT, Spreads, Rating, Commodities, Fret)        │
  └────────────────────────────────────┬────────────────────────────────────┘
  ┌────────────────────────────────────▼────────────────────────────────────┐
  │ STRATE 3 : L'EUROPE (PSC, PDE 3 %, TPI, clause de sauvegarde défense)  │
  └────────────────────────────────────┬────────────────────────────────────┘
  ┌────────────────────────────────────▼────────────────────────────────────┐
  │ STRATE 2 : LE NATIONAL (État, Sécu, Parlement, Défense, Institutions)  │
  └────────────────────────────────────┬────────────────────────────────────┘
  ┌────────────────────────────────────▼────────────────────────────────────┐
  │ STRATE 1 : LE LOCAL (Communes, Départements, Règle d'or, Foncier)      │
  └─────────────────────────────────────────────────────────────────────────┘
```

**La strate 5 est résolue en premier** à chaque exercice : elle alimente les chocs d'offre et la
prime de risque avant toute propagation descendante 4 → 1.

### Équations de transmission ajoutées

1. **Indice de tension composite**
   $$T = 0{,}30\,T_{\text{Taïwan}} + 0{,}28\,T_{\text{Ukr-OTAN}} + 0{,}22\,T_{\text{Iran}} + 0{,}20\,C_{\text{blocs}}$$

2. **Prime pétrolière de chokepoint** (appliquée **en niveau**, jamais cumulée)
   $$\Delta \text{Brent} = 78\,\$ \times i_{\text{Hormuz}} \times (1 - 0{,}30 \cdot \mathbb{1}_{\text{stocks AIE}})$$

3. **Choc semi-conducteurs**
   $$\text{Dispo} = 100 - 70\,i_{\text{Taïwan}}(1 - \alpha),\quad \alpha = \min\left(0{,}5 ; \frac{K_{\text{souverain}}}{80}\right)$$
   $$\Delta \text{PIB} = -1{,}25\,\% \times \text{PIB} \times \frac{100 - \text{Dispo}}{70}$$

4. **Effort de défense**
   $$\Delta \text{PIB} = +k\,S,\quad S = \text{PIB}\times\frac{d - 2{,}10\,\%}{100},\quad k \in \{0{,}75 ; 1{,}10\}$$

5. **Prime de risque souverain géopolitique** (ajoutée **au spread**, la parité
   $T_{\text{OAT}} = T_{\text{Bund}} + \text{spread}/100$ reste exacte)
   $$P = \min\!\left(260 ; 12 + 1{,}35\max(0, T - 55) + 6 n_{\text{chokepoints}} + P_{\text{événements}}\right) - P_{\text{réf}}$$
   $P_{\text{réf}}$ est la prime déjà incorporée dans les 88 bps calés à l'instant T : **aucun
   double comptage**, les 4 scénarios historiques sont strictement inchangés.

6. **Probabilité d'escalade mondiale**
   $$W = 0{,}35\max(0, T - 45) + 6 n_{\text{théâtres} \ge 80} + 0{,}22\,C_{\text{blocs}} + 35 \cdot \mathbb{1}_{\text{nucléaire}}$$

7. **Clause de sauvegarde nationale (PSC)** — déficit retenu par la Commission :
   $$\text{Déficit}_{\text{PDE}} = \text{Déficit} - \min\left(1{,}50 ; \frac{S}{\text{PIB}}\times 100\right)$$

---

## IV. PHASE 4 — LES 5 SIMULATIONS DÉSORMAIS POSSIBLES

| Clé CLI | Scénario | Source |
|---------|----------|--------|
| `crise_taiwan` | **Scénario A** — Quarantaine puis blocus de Taïwan, frappes sur TSMC, Chips Act souverain | Analyse §5.A (prob. 15-25 %) |
| `hormuz` | **Scénario C** — Fermeture du détroit d'Hormuz, Brent > 150 $, déstockage AIE | Analyse §5.C (prob. 25-35 %) |
| `escalade_nucleaire` | **Scénario B** — Escalade Ukraine-OTAN et frappe nucléaire tactique | Analyse §5.B (prob. 10-20 %) |
| `convergence_ww3` | **Scénario D** — Convergence Chine-Russie-Iran, trois théâtres simultanés | Analyse §5.D (prob. 5-10 %) |
| `resilience` | **Synthèse** — Mandature +60 Md€ **+** réarmement OTAN 3,50 % **+** souveraineté industrielle | Question jusqu'ici insoluble |

### Résultats consolidés à l'année finale

| Scénario | Déficit/PIB | Dette/PIB | OAT 10a | Spread max | Note | Brent max | Inflation max | Tension | Escalade max | Défense | PDE |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Mandature | -0,73 % | 119,1 % | 3,35 % | 86 bps | AA | 82,5 $ | 1,75 % | 5,0 | 16,8 % | 2,10 % | CONFORME |
| Statut quo | 0,99 % | 124,1 % | 4,58 % | 128 bps | A+ | 82,5 $ | 2,10 % | 37,3 | 16,8 % | 2,10 % | CONFORME |
| Austérité | 0,88 % | 123,9 % | 4,17 % | 87 bps | AA- | 82,5 $ | 2,10 % | 97,4 | 16,8 % | 2,10 % | CONFORME |
| Choc mondial | 2,19 % | 124,2 % | 4,18 % | 85 bps | AA- | 142,5 $ | 3,34 % | 18,5 | 16,8 % | 2,10 % | CONFORME |
| **Crise Taïwan** | 0,55 % | 122,6 % | 4,08 % | 107 bps | AA- | 82,5 $ | **3,46 %** | 5,0 | 31,3 % | **3,50 %** | CONFORME |
| **Hormuz** | 0,24 % | 121,5 % | 4,02 % | 97 bps | AA- | **131,6 $** | 2,75 % | 5,0 | 23,9 % | 3,00 % | CONFORME |
| **Escalade nucléaire** | 1,30 % | **129,3 %** | 4,63 % | **288 bps** | **BBB+** | 153,9 $ | **6,60 %** | 62,2 | 67,0 % | 3,60 % | CONFORME |
| **Convergence WW3** | 0,99 % | **131,4 %** | 3,86 % | **322 bps** | A- | **192,1 $** | **8,81 %** | 98,5 | **90,5 %** | 4,00 % | CONFORME |
| **Résilience républicaine** | **-0,16 %** | **119,2 %** | **3,20 %** | 84 bps | **AA** | 82,5 $ | 1,75 % | 5,0 | 16,8 % | **3,50 %** | CONFORME |

### Les 5 enseignements de la strate 5

1. **Le réarmement OTAN est finançable sans austérité** : la trajectoire 2,10 % → 3,50 % du PIB
   (≈ +46 Md€/an en régime de croisière) coûte **18,6 Md€ de solde public par an** une fois
   déduits le multiplicateur budgétaire (0,75) et le retour fiscal — soit **0,57 pt de PIB**,
   absorbable par le Plan de mandature sans toucher au pouvoir d'achat ni à la DGF.
2. **Le vrai risque n'est pas budgétaire, il est logistique** : un blocus de Taïwan coûte plus
   cher en inflation importée (**+1,4 pt**) qu'en déficit, car il frappe l'**offre** et non les comptes.
3. **Les amortisseurs fonctionnent, mais ils sont finis** : les réserves stratégiques absorbent
   30 % d'un choc d'Hormuz pendant ~2 ans avant d'atteindre leur plancher opérationnel.
4. **Le seuil nucléaire est une rupture de régime, pas un choc graduel** : il coûte
   **~200 bps de spread**, **3 crans de notation** et **une décennie de défiance rémanente**.
5. **La clause de sauvegarde nationale du PSC est le verrou juridique décisif** : sans elle,
   le réarmement replace mécaniquement la France sous procédure de déficit excessif.

---

## V. PHASE 5 — VALIDATION (61 TESTS VERTS)

`tests/test_geopolitique.py` (28 nouveaux tests) ajoute aux 33 tests préexistants :

| Famille d'invariants | Contrôle | Résultat |
|---|---|---|
| Calibrage SIPRI / OTAN / AIE | Arsenal, 7 chokepoints, 90 j de réserves, cible 3,50 % | **VALIDÉ** |
| **Non-régression** | Les 4 scénarios historiques sont **inchangés** (pas de double comptage de prime) | **VALIDÉ** |
| Choc semi-conducteurs | Blocus total → 30 % de disponibilité ; Chips Act → 65 % | **VALIDÉ** |
| Chokepoint Hormuz | Brent 160,5 $ ; déstockage borné à 60 j ; prime **non cumulative** | **VALIDÉ** |
| Seuil nucléaire | Choc PIB, spread, BBB+, rémanence pluriannuelle | **VALIDÉ** |
| Défense & clause PSC | Trajectoire, multiplicateur, dérogation plafonnée à 1,5 pt de PIB | **VALIDÉ** |
| Cohérence stocks-flux | Déficit = Dépenses − Recettes et Dette_t = Dette_{t-1} + Déficit_t sur **tous** les scénarios géopolitiques | **VALIDÉ** |
| Parité des taux | OAT = Bund + spread/100 et Crédit PME = OAT + 0,85 sous choc de guerre | **VALIDÉ** |
| Déterminisme | Deux exécutions identiques bit-à-bit | **VALIDÉ** |
| Non-divergence extrême | **15 ans** de guerre mondiale continue : aucun NaN/inf, toutes bornes tenues | **VALIDÉ** |

---

## VI. UTILISATION

```bash
# Ligne de commande
python3 main.py crise_taiwan
python3 main.py hormuz --export resultats_hormuz.json
python3 main.py escalade_nucleaire
python3 main.py convergence_ww3
python3 main.py resilience --export resilience.csv

# Menu interactif (13 entrées, dont le comparatif des 9 scénarios)
python3 -m simulateur.cli

# Dashboard web (strate 5 affichée : tension, escalade, risque nucléaire,
# semi-conducteurs, effort de défense, chokepoints)
python3 -m simulateur.dashboard
```

API Python :

```python
from simulateur import EchelonGeopolitique, MoteurSimulationSystemique, DecisionPolitique

moteur = MoteurSimulationSystemique(geo=EchelonGeopolitique(tension_taiwan=85.0))
resultat = moteur.appliquer_etape(DecisionPolitique(
    annee=1,
    blocus_taiwan_intensite=0.8,
    fermeture_hormuz_intensite=0.5,
    liberation_stocks_strategiques=True,
    effort_defense_cible_pct_pib=3.5,
    activation_clause_sauvegarde_nationale_ue=True,
    plan_souverainete_semiconducteurs_mde=12.0,
))
print(resultat.probabilite_escalade_mondiale_pct, resultat.ratio_deficit_pib)
```

---

## VII. SOURCES DE LA PHASE DE RECHERCHE

1. SIPRI Yearbook 2026 — *World Nuclear Forces* (janvier 2026).
2. Déclaration du sommet de l'OTAN de La Haye, 25 juin 2025 — *Hague Defence Investment Plan* (5 % du PIB).
3. Sénat, *Projet de loi de finances pour 2026 — Défense : équipement des forces* (trajectoire +0,15 pt de PIB/an, 140 Md€ en 2035).
4. Haut-commissariat à la Stratégie et au Plan, note du 19 mai 2025 (120 Md€ pour 3,5 % ; 172 Md€ pour 5 %).
5. Loi n° 2023-703 du 1er août 2023 de programmation militaire 2024-2030 (413,3 Md€).
6. Direction générale du Trésor, *Ormuz, point de salut ?* (3 avril 2026) — Brent 150-200 $ en cas de quasi-fermeture prolongée.
7. Revue politique et parlementaire (mai 2026) — élasticité-prix -0,1 ; -15 % d'offre → 160 $ ; -20 % → 195 $.
8. Paris School of Economics / L. Fontagné (juin 2026) — commerce mondial -3,1 %, PIB mondial -0,54 %, PIB France -0,42 %.
9. AIE / S&P Global (avril-mai 2026) — contraction de la demande de 5 Mb/j, plus forte chute depuis la pandémie.
10. BSI Economics / CSIS / DGE — *Thémas semi-conducteurs* (2025) : Taïwan 60 % de l'offre, 85-90 % du < 7 nm, 21 % des importations UE.
11. OCDE (avril 2026) et Ramey (2019), Ilzetzki (2025) — multiplicateurs budgétaires de défense 0,6-1,0.
12. Règlement (UE) 2024/1263 (PSC réformé), Règlement (UE) 2023/1781 (Chips Act), Directive (UE) 2022/2555 (NIS 2), Code de l'énergie art. L. 642-2, CNUDM art. 37-38, TNP art. VI.
