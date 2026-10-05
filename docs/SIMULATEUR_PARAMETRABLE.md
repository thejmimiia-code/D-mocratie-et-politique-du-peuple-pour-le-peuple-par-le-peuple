# Simulateur paramétrable — piloter 93 leviers et voir l'impact sur 20 domaines

> Tableau de bord unique, sans dépendance externe : `python -m simulateur.dashboard --port 8080`
> (ou `simulateur-mpol-dashboard` après installation).

Ce document décrit le fonctionnement interne du simulateur interactif introduit
en octobre 2026. Il remplace le tableau de bord à cartes généralistes : au lieu
de proposer quatre scénarios figés, il expose **tous les paramètres** du modèle,
les croise dynamiquement, et recalcule les impacts domaine par domaine à chaque
mouvement de curseur.

---

## 1. Vue d'ensemble

```
┌──────────────────────────── navigateur (page unique) ────────────────────────────┐
│ 93 leviers (curseurs, interrupteurs, cibles)   ← leviers →   20 domaines notés    │
│ recherche, préréglages, exports JSON/CSV        service       0-100 + indicateurs │
│ « Rafraîchir les données » → API publiques en direct (fetch CORS)                 │
└───────────────┬───────────────────────────────────────────┬─────────────────────┘
                │ GET /api/catalogue, /api/contexte          │ POST /api/donnees
                │ POST /api/simuler (leviers)               │ (valeurs relevées)
┌───────────────▼───────────────────────────────────────────▼─────────────────────┐
│ serveur HTTP (bibliothèque standard, multi-thread, HTTP/1.1)                    │
│  · moteur_parametrique.simuler()  → 5 étapes × 5 échelons + domaines + impacts  │
│  · parametres.normaliser()        → validation et bornage des 93 leviers        │
│  · domaines.evaluer_domaines()    → 74 indicateurs concrets, scores 0-100       │
│  · donnees_live.construire_contexte() → chiffres publics datés et sourcés       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

| Module | Rôle |
|---|---|
| `simulateur/parametres.py` | 93 leviers (14 familles), 13 préréglages doctrinaux, `normaliser()`, `catalogue_public()` |
| `simulateur/domaines.py` | 20 domaines, 74 indicateurs spécifiés (formule + source), `construire_flux()`, `decision_moteur()` |
| `simulateur/seuils.py` | garde-fous par strate : bornes, messages, marges, risque population |
| `simulateur/moteur_parametrique.py` | orchestrateur : trajectoire de référence, boucle de convergence, scores, matrice d'impacts |
| `simulateur/donnees_live.py` | registre de 38 indicateurs publics (38 sources licenciées), snapshot daté, collecte |
| `simulateur/moteur.py`, `model.py` | moteur systémique à 5 échelons (inchangé) |
| `simulateur/dashboard.py` | serveur HTTP + API JSON |
| `simulateur/interface.py` | page HTML unique (CSS et JavaScript embarqués, zéro CDN) |

---

## 2. Les 93 leviers

Chaque levier est un objet `Levier` documenté : clé, libellé, famille, description,
unité, type, valeur par défaut, bornes, pas, profil temporel sur 5 ans, et
rattachement au moteur (`champ` de `DecisionPolitique`, `ligne` budgétaire ou
effets directs documentés).

| Type | Comportement | Exemple |
|---|---|---|
| `curseur` | montant en Md€ ou en points ; 0 = statu quo | TVA (+1 pt ≈ +7,8 Md€), budget éducation, ONDAM |
| `interrupteur` | réforme binaire (0/1) | RIC, vote blanc, ISF, 49.3 |
| `cible` | **niveau** visé, jamais un incrément | effort de défense en % du PIB |

Deux règles structurent le moteur :

1. **Les leviers « cible » fixent un niveau.** Le moteur ne fait jamais
   « niveau actuel + montant » : il compare le niveau voulu à la référence, ce
   qui garantit l'idempotence de la simulation sur cinq ans.
2. **Les chocs exogènes sont appliqués en niveau.** Un choc pétrolier maintenu
   cinq ans reste à +X $/baril : il ne s'empile pas d'année en année
   (`MoteurSimulationSystemique._chocs_appliques`).

---

## 3. Données publiques « à l'instant T »

`donnees_live.py` tient un registre d'indicateurs : identifiant, libellé, unité,
précision, **sources publiques** (URL d'API, licence, page de licence) et
**snapshot daté** de dernière vérification (`DATE_VERIFICATION`).

- Sources principales : Eurostat (réutilisation libre, décision 2011/833/UE),
  BCE (SDMX, attribution), Frankfurter/BCE (MIT), Banque mondiale (CC-BY 4.0),
  Yahoo Finance et Stooq (prototype, non redistribuable).
- Hors ligne, le simulateur affiche le dernier chiffre **vérifié et daté** : le
  repli documentaire est automatiquement recalé sur le snapshot (test
  `test_repli_aligne_sur_le_snapshot`), il ne peut donc pas y avoir deux
  vérités pour un même champ.
- En ligne, l'ordre est : lecture live → snapshot daté → repli documentaire.
  Chaque valeur affichée porte son statut (`live` / `référence`), sa période,
  son fournisseur et sa licence.
- **Le navigateur prend le relais** quand le serveur n'a pas d'accès réseau : le
  bouton « Rafraîchir les données » interroge les API directement depuis votre
  poste (adaptateurs JavaScript identiques aux adaptateurs Python) puis poste le
  relevé sur `/api/donnees`, qui recalibre le contexte. Les sources sans CORS
  (Yahoo, Stooq, ICE/EEX) passent par le relais *same-origin* `/api/proxy`, qui
  n'accepte **que** les sources déclarées au registre.

Snapshot de référence (vérifié le 5 octobre 2026) : PIB 2 991,06 Md€, dette
115,6 % du PIB, déficit 5,1 %, OAT 10 ans 4,00 %, Bund 3,185 % (spread 81,5 bps),
taux BCE 2,50 %, IPCH France 0,7 %, chômage 8,2 %, Brent 101,69 $, EUR/USD 1,1204.

---

## 4. Comment lire les scores (0-100)

```
score_domaine = 50 + 50 × tanh( 16 × moyenne( écart relatif signé ) )
```

- **50 = politique sans effet** : la trajectoire simulée est identique à la
  trajectoire de référence (tous leviers neutres).
- **> 50 = amélioration** attendue du domaine, **< 50 = dégradation**.
- Chaque indicateur est plafonné à ±15 % d'écart, pour qu'un indicateur volatil
  (chômage, spread) ne sature pas à lui seul son domaine.
- Le tableau de bord affiche aussi, pour chaque domaine, la **tendance sans
  politique** : ce que le modèle prévoit si l'on ne décide rien (par exemple la
  consolidation budgétaire automatique, qui améliore le domaine budget).

> ⚠️ **Les écarts ne sont pas des niveaux absolus.** La trajectoire de référence
> inclut l'indexation automatique des recettes sur le PIB nominal du modèle.
> Comparer un score à 50 compare donc *votre politique* à *l'absence de
> décision*, pas la France à un idéal.

### Les 20 domaines

Économie · Budget, dette & marchés · Fiscalité & prélèvements · Emploi & travail ·
Pouvoir d'achat · Pauvreté & précarité · Santé · Éducation & jeunesse ·
Recherche & innovation · Sécurité & justice · Défense & souveraineté ·
Énergie & climat · Industrie & commerce · Numérique & IA · Logement & territoires ·
Agriculture & alimentation · Démocratie & institutions · Solidarité & cohésion ·
Europe & monde · Résilience & risques systémiques.

Chaque indicateur porte sa **formule lisible** et sa **source** ; l'interface les
affiche, et `tests/test_domaines.py` vérifie qu'aucun coefficient ne pointe vers
un médiateur inexistant (les 102 termes sont couverts par des politiques réelles).

---

### Le ruban : la veille en une ligne

La console complète vit dans le flux de la page (elle défile) ; c'est un
**ruban compact et collant** qui reste seul en haut de l'écran : verdict,
compteur d'alertes et de hors-sol, cinq pastilles de strate (S1…S5), risque
pour la population, et trois boutons — *Masquer le détail des seuils*,
*Vue compacte*, *Régler les 93 leviers*. Le ruban mesure 44 pixels de haut :
il ne recouvre jamais les paramètres.

### Tous les paramètres, visibles et actionnables

- **Vue confort** : une carte par famille, chaque levier avec sa description,
  sa source et son curseur.
- **Vue compacte** (bascule dans la barre des leviers) : une ligne par levier —
  nom, curseur, valeur — pour que **les 93 paramètres** tiennent à l'écran.
- Chaque geste part immédiatement : anti-rebond de 180 ms, puis simulation.
- Pendant la manipulation d'un curseur, la grille **n'est pas reconstruite**
  (sinon le curseur serait remplacé sous les doigts) ; elle l'est au relâchement.
- Sous chaque levier touché, ses **puces d'impact** : l'effet mesuré par le
  modèle sur les deux ou trois domaines les plus concernés, en points de score.
  Elles proviennent des impacts croisés quand on les demande, et sinon de la
  comparaison entre les deux dernières simulations (attribution directe quand un
  seul levier a bougé).
- Un compteur permanent indique combien de leviers sont affichés et combien
  sont modifiés ; les leviers modifiés sont mis en évidence.

## 5. La console de veille permanente

En haut de la page, une console **épinglée** suit le défilement : elle reste
visible pendant que l'on règle les 93 leviers. Elle répond à trois questions,
en permanence et sans clic supplémentaire (le diagnostic voyage avec chaque
simulation, aucune requête en plus) :

1. **Où en est-on ?** Un verdict global (favorable → tolérable → vigilance →
   risqué → hors-sol) et une puce par strate : locale, nationale, européenne,
   mondiale, géopolitique.
2. **Qu'est-ce qui est dangereux ?** Les messages de seuil, du plus grave au
   plus doux, avec la valeur mesurée, le seuil franchi et sa source
   institutionnelle. Un bandeau rouge apparaît dès qu'une grandeur est hors-sol.
3. **Que peut-on encore faire ?** Les **marges de manœuvre** (ce qu'il reste
   avant le prochain seuil) et les **audaces possibles** (ce qu'on peut encore
   oser avant d'atteindre l'objectif), pour régler au plus fin sans danger.

S'y ajoute le bloc « effet de votre dernière modification » : chaque mouvement
de curseur est comparé à la simulation précédente et affiché en différentiel
(déficit, dette, OAT, spread, charge, tension, confiance, censure, solde des
mesures, score moyen), avec la mention du domaine le plus touché et un verdict
— « jugée favorable », « mixte », « jugée défavorable ».

### Indice de risque pour la population

Huit domaines qui touchent directement les ménages (pouvoir d'achat, pauvreté,
santé, éducation, emploi, logement, solidarité, sécurité) donnent un indice de
0 à 100 (50 = aucune politique) :

| Indice | Lecture |
|---|---|
| ≤ 50 | tolérable — les ménages ne sont pas exposés |
| 50 à 58 | vigilance — effets perceptibles, à accompagner |
| 58 à 68 | risqué — les pertes l'emportent, corriger avant d'avancer |
| > 68 | hors-sol — la population paie les mesures |

### Barème des seuils (extraits)

| Strate | Grandeur | tolérable | vigilance | risqué | hors-sol |
|---|---|---|---|---|---|
| 2 | Déficit (% PIB) | ≤ 3,0 | ≤ 4,5 | ≤ 5,5 | > 5,5 |
| 2 | Dette (% PIB) | ≤ 90 | ≤ 125 | ≤ 145 | > 145 |
| 2 | Charge de la dette (% PIB) | ≤ 2,0 | ≤ 3,0 | ≤ 4,0 | > 4,0 |
| 4 | OAT 10 ans (%) | ≤ 3,5 | ≤ 4,5 | ≤ 5,5 | > 5,5 |
| 3 | Spread vs Bund (bps) | ≤ 80 | ≤ 150 | ≤ 250 | > 250 |
| 1 | Pouvoir d'achat (base 100) | ≥ 99,0 | ≥ 97,5 | ≥ 95,5 | < 95,5 |
| 1 | Tension sociale (/100) | ≤ 45 | ≤ 60 | ≤ 75 | > 75 |
| 1 | Confiance démocratique (/100) | ≥ 30 | ≥ 22 | ≥ 15 | < 15 |
| 5 | Stocks pétroliers (jours, AIE) | ≥ 90 | ≥ 75 | ≥ 60 | < 60 |
| 5 | Effort de défense (% PIB) | ≥ 2,5 | ≥ 2,0 | ≥ 1,5 | < 1,5 |
| 5 | Risque nucléaire tactique (%) | ≤ 8 | ≤ 20 | ≤ 35 | > 35 |

Les garde-fous « écart » comparent, eux, la trajectoire choisie à la trajectoire
neutre : déficit (±0,25 / 1 / 2 pt), dette (0,5 / 3 / 6 pt), croissance
(0 / −0,5 / −1,5 pt), **équilibre des mesures** (0 / −10 / −25 Md€ par an) et
score moyen des domaines (48 / 44 / 38).

Lecture du module : `simulateur/seuils.py` (bornes, sources, messages) ; le
diagnostic est attaché à chaque `SortieSimulation` et exposé par
`/api/simuler` et `/api/comparer`.

## 6. Impacts croisés (matrice levier × domaine)

La matrice n'est pas saisie à la main : pour chaque levier actif, le modèle
**rejoue la simulation avec ce seul levier ramené à sa valeur neutre** et mesure
la variation de score de chaque domaine (différences finies, cache par empreinte
SHA-256 des paramètres et du contexte). L'effet affiché est donc la contribution
marginale du levier à la politique en cours, domaine par domaine.

---

## 7. Cascade des 5 échelons

L'interface affiche, année par année, l'état des cinq strates : locale (tension,
services de proximité, taxe foncière), nationale (PIB, déficit, dette, charge de
la dette, censure), européenne (PDE, bouclier TPI), mondiale (OAT, spread, note
souveraine, Brent, inflation) et géopolitique (tension, chokepoints, effort de
défense, semi-conducteurs). Le journal causal reprend les commentaires produits
par le moteur à chaque étape.

---

## 8. Exécution et API

```bash
python -m simulateur.dashboard --host 0.0.0.0 --port 8080 [--rafraichir]
python -m simulateur.moteur_parametrique --preset mandature --json
python -m simulateur.moteur_parametrique --levier effort_defense_pct_pib=3.5 --levier reforme_ric=1
```

| Route | Méthode | Contenu |
|---|---|---|
| `/` | GET | page unique du simulateur |
| `/api/catalogue` | GET | familles, 93 leviers, 13 préréglages, 20 domaines |
| `/api/contexte` | GET | contexte instant T + provenance + sources navigateur + diagnostic |
| `/api/simuler` | GET/POST | simulation paramétrique (étapes, domaines, synthèse, impacts, **diagnostic de seuils**) |
| `/api/comparer` | GET | comparaison des 13 préréglages **avec leur verdict de garde-fous** |
| `/api/presets` | GET | préréglages seuls |
| `/api/proxy` | GET | relais d'une source du registre (liste blanche) |
| `/api/donnees` | POST | valeurs relevées par le navigateur → recalibrage |
| `/api/scenarios`, `/api/run`, `/api/export` | GET | scénarios historiques du dépôt (compatibilité) |

---

## 9. Réglages du dépôt

L'aperçu social, la description, les sujets et le site web déclarés sont tenus à
jour dans [`REPOSITORY_DETAILS.md`](REPOSITORY_DETAILS.md), avec les scripts
`outils/details_depot.py` (bloc à coller) et `outils/apercu_social.py` (image
1280 × 640).

## 10. Limites assumées

1. **Modèle, pas prophétie.** Les coefficients sont documentés et sourcés
   (multiplicateurs OFCE/FMI, élasticités INSEE, loi d'Okun 1 pt ≈ 150 000
   emplois) mais restent des choix. Ils sont lisibles, contestables et
   modifiables dans `domaines.py`.
2. **Écarts, jamais niveaux.** Voir l'avertissement du § 4.
3. **Horizon de 5 ans**, pas de projection démographique ni de cycle long.
4. **Sources non redistribuables** (Yahoo, Stooq) : elles servent au rafraîchissement
   en direct, pas à l'embarquement de données ; le snapshot embarqué ne contient
   que des valeurs de sources réutilisables ou de référence documentaire du projet.
5. **Un proxy fermé.** `/api/proxy` n'accepte que les 38 indicateurs du registre,
   jamais une URL fournie par le client.
