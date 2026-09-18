# DÉMOCRATIE ET POLITIQUE : DU PEUPLE, POUR LE PEUPLE, PAR LE PEUPLE
> **Plateforme de réflexion républicaine et Simulateur macro-politique systémique (Modèle gigogne à 4 échelons)**

---

## I. PRÉSENTATION DU PROJET

Ce dépôt rassemble les travaux complets de doctrine institutionnelle, le plan de mandature quinquennal chiffré (**+60 milliards d'euros par an** de marges récurrentes à l'année 5), ainsi que le **moteur de simulation algorithmique en Python** modélisant l'intégralité des flux et contraintes de l'État français, du niveau communal jusqu'aux marchés obligataires mondiaux.

> « Son principe est : gouvernement du peuple, par le peuple et pour le peuple. »  
> — *Constitution de la République française du 4 octobre 1958, Article 2, alinéa 5.*

---

## II. LE MODÈLE SYSTÉMIQUE GIGOGNE (POUPÉES RUSSES)

Le simulateur repose sur l'interconnexion dynamique de **4 échelons de contrainte** :

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │ ÉCHELON 4 : LE MONDIAL                                                  │
  │ Marchés obligataires (Taux OAT 10 ans, Spread Bund, Note souveraine)   │
  └────────────────────────────────────┬────────────────────────────────────┘
                                       │ Taux d'intérêt & Refinancement de la dette
  ┌────────────────────────────────────▼────────────────────────────────────┐
  │ ÉCHELON 3 : LE CONTINENTAL / EUROPÉEN                                   │
  │ Règles budgétaires de Maastricht (Plafond 3%), Procédure PDE, Marché    │
  └────────────────────────────────────┬────────────────────────────────────┘
                                       │ Contrainte de déficit excessif
  ┌────────────────────────────────────▼────────────────────────────────────┐
  │ ÉCHELON 2 : LE NATIONAL                                                 │
  │ Budget de l'État (PLF/PLFSS), Dette (3 568 Md€), Stabilité parlementaire│
  └────────────────────────────────────┬────────────────────────────────────┘
                                       │ Dotations de fonctionnement (DGF)
  ┌────────────────────────────────────▼────────────────────────────────────┐
  │ ÉCHELON 1 : LE LOCAL                                                    │
  │ Communes, Départements, Régions (Règle d'or, Foncier, Tension sociale)  │
  └─────────────────────────────────────────────────────────────────────────┘
```

### La boucle de rétroaction causale
$$\text{Décision Politique} \rightarrow \text{Impact Local} \rightarrow \text{Réaction Sociale} \rightarrow \text{Sanction Parlementaire} \rightarrow \text{Alerte Européenne} \rightarrow \text{Réaction Marchés} \rightarrow \text{Nouveau Budget}$$

1. **Échelon Local (Cellule de base)** : Règle d'or budgétaire imposant l'équilibre de fonctionnement. Si l'État coupe les dotations (DGF), la taxe foncière flambe, déclenchant une fronde fiscale immédiate.
2. **Échelon National (Moteur)** : PIB nominal ~3 000 Md€, dépenses ~57% PIB, recettes ~43.6% (PO) / ~52% (total), dette 3 568 Md€ (~119% PIB), charge de la dette 65 Md€/an. Risque permanent de motion de censure en cas de contestation populaire.
3. **Échelon Continental (Cadre UE)** : Procédure de Déficit Excessif (PDE) activée au-dessus de 3,0 % du PIB avec menaces de sanctions.
4. **Échelon Mondial (Marchés financiers)** : 56 % de la dette souveraine détenue par des non-résidents. Le taux de l'OAT 10 ans et le spread face au Bund allemand déterminent le coût de refinancement de l'État.

---

## III. LE SOCLE DOCUMENTAIRE

Tous les dossiers de mandature, chiffrages et textes de loi sont disponibles dans le dossier [`docs/`](docs/) et dans le document maître :

* **[`DOSSIER_DE_MANDATURE_GLOBAL.md`](DOSSIER_DE_MANDATURE_GLOBAL.md)** : Document consolidé exhaustif (Histoire, Constitutions I à VI, Panorama politique, Tabous populaires, 20 Leviers & Solutions, Trajectoire budgétaire, Coulisses techniques, Autodéfense médiatique).
* **[`docs/00_HISTOIRE_CONSTITUTIONS_ET_REVENDICATIONS.md`](docs/00_HISTOIRE_CONSTITUTIONS_ET_REVENDICATIONS.md)** : Origine Lincoln 1863, IVᵉ vs Vᵉ, panorama des républiques, propositions partisanes et think tanks, diagnostic sociologique.
* **[`docs/01_DEMOCRATIE_INSTITUTIONS.md`](docs/01_DEMOCRATIE_INSTITUTIONS.md)** : Casier judiciaire B2 obligatoire (API IJ-CJN), vote blanc invalidant avec carence de 12 mois, RIC souverain sécurisé (FranceConnect+, Helios, SecNumCloud ANSSI).
* **[`docs/02_RECETTES_ET_TRANSACTIONS.md`](docs/02_RECETTES_ET_TRANSACTIONS.md)** : Nouvelles recettes ciblées (**+36 Md€ / an**) sans hausse d'impôt sur les ménages (IA CFIA fraude, conditionnement des aides DSN, taxe superprofits et TTF au dépositaire Euroclear).
* **[`docs/03_ECONOMIES_ET_EFFICACITE_ETAT.md`](docs/03_ECONOMIES_ET_EFFICACITE_ETAT.md)** : Économies de fonctionnement (**+24 Md€ / an**) sans casse sociale (fusion doublons région/département, achats massifiés allotis 30% PME, niches inefficaces).
* **[`docs/04_POUVOIR_D_ACHAT_ET_TRAJECTOIRE.md`](docs/04_POUVOIR_D_ACHAT_ET_TRAJECTOIRE.md)** : Baisse TVA énergie à 5,5 % (**-9 Md€ / an**, gain 150-300 €/foyer), déficit ramené sous les 3 % du PIB, désendettement net de 51 Md€/an.
* **[`docs/05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md`](docs/05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md)** : 10 fiches de riposte tactique démontant les pièges des oppositions et éditorialistes.

---

## IV. UTILISATION DU SIMULATEUR

Le simulateur est développé en Python standard sans dépendance externe obligatoire.

### 1. Lancement direct du scénario de mandature
```bash
python3 main.py mandature
```

### 2. Menu interactif
```bash
python3 -m simulateur.cli
```

### 3. Exécution des tests unitaires
```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

### 4. Exemple d'utilisation en script Python
```python
from simulateur.moteur import MoteurSimulationSystemique
from simulateur.scenarios import get_scenario_mandature_5_ans

moteur = MoteurSimulationSystemique()
for decision in get_scenario_mandature_5_ans():
    res = moteur.appliquer_etape(decision)
    print(f"An {res.annee} : Déficit = {res.ratio_deficit_pib:.2f} % du PIB | Taux OAT = {res.taux_oat_pct:.2f} % | Tension = {res.tension_sociale:.1f}/100")
```

---

## V. RÉSULTATS DU PLAN DE MANDATURE (ANNÉE 5)

| Indicateur macro-économique | Situation Initiale | Année 5 (Plan de Mandature) | Impact |
|---|---|---|---|
| **Déficit public (% PIB)** | **5,07 %** (152 Md€) | **2,79 %** (89,8 Md€) | **-2,28 pts** (Sortie de la PDE européenne) |
| **Dette souveraine (% PIB)** | **118,9 %** | **Stabilisée à ~129 %** | Inversion de la trajectoire exponentielle |
| **Taux OAT 10 ans** | **4,15 %** | **3,22 %** | Détente de **93 points de base** |
| **Spread face au Bund** | **85,0 bps** | **46,8 bps** | Prime de risque française divisée par deux |
| **Tension sociale locale** | **35,0 / 100** | **5,0 / 100** | Apaisement civique par le pouvoir d'achat et le RIC |
| **Confiance démocratique** | **28,0 / 100** | **78,0 / 100** | Moralisation (B2, vote blanc, anti-pantouflage) |
