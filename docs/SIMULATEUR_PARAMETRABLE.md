# Simulateur paramétrable — piloter 101 leviers et voir l'impact sur 20 domaines

> Tableau de bord unique, sans dépendance externe : `python -m simulateur.dashboard --port 8080`
> (ou `simulateur-mpol-dashboard` après installation).

Ce document décrit le fonctionnement interne du simulateur interactif introduit
en octobre 2026. Il remplace le tableau de bord à cartes généralistes : au lieu
de proposer quatre scénarios figés, il expose **tous les paramètres** du modèle,
les croise dynamiquement, et recalcule les impacts domaine par domaine à chaque
mouvement de curseur. Le sélecteur d'horizon propose une ou deux mandatures
(5 ou 10 ans) ; l'API accepte également les horizons intermédiaires de 1 à 10.

---

## 1. Vue d'ensemble

```
┌──────────────────────────── navigateur (page unique) ────────────────────────────┐
│ 101 leviers (curseurs, interrupteurs, cibles)   ← leviers →   20 domaines notés    │
│ recherche, préréglages, exports JSON/CSV        service       0-100 + indicateurs │
│ « Rafraîchir les données » → API publiques en direct (fetch CORS)                 │
└───────────────┬───────────────────────────────────────────┬─────────────────────┘
                │ GET /api/catalogue, /api/contexte          │ POST /api/donnees
                │ POST /api/simuler (leviers)               │ (valeurs relevées)
┌───────────────▼───────────────────────────────────────────▼─────────────────────┐
│ serveur HTTP (bibliothèque standard, multi-thread, HTTP/1.1)                    │
│  · moteur_parametrique.simuler()  → horizon 1-10 × 5 échelons + domaines       │
│  · parametres.normaliser()        → validation et bornage des 101 leviers        │
│  · domaines.evaluer_domaines()    → 74 indicateurs concrets, scores 0-100       │
│  · donnees_live.construire_contexte() → chiffres publics datés et sourcés       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

| Module | Rôle |
|---|---|
| `simulateur/parametres.py` | 101 leviers (14 familles), 14 préréglages doctrinaux, `normaliser()`, `catalogue_public()` |
| `simulateur/domaines.py` | 20 domaines, 74 indicateurs spécifiés (formule + source), `construire_flux()`, `decision_moteur()` |
| `simulateur/seuils.py` | garde-fous par strate : bornes, messages, marges, risque population |
| `simulateur/moteur_parametrique.py` | orchestrateur : trajectoire de référence, boucle de convergence, scores, matrice d'impacts |
| `simulateur/donnees_live.py` | registre de 38 indicateurs publics (38 sources licenciées), snapshot daté, collecte |
| `simulateur/moteur.py`, `model.py` | moteur systémique à 5 échelons (inchangé) |
| `simulateur/dashboard.py` | serveur HTTP + API JSON |
| `simulateur/interface.py` | page HTML unique (CSS et JavaScript embarqués, zéro CDN) |
| `simulateur/lexique.py` | 83 termes définis en français ordinaire, servis par `/api/lexique` |
| `simulateur/clarte.py` | relecture d'une sortie de simulation en phrases ordinaires (champ `lecture`) |
| `simulateur/compression.py` | négociation et application de la compression HTTP (bibliothèque standard) |

---

## 2. Les 101 leviers

Chaque levier est un objet `Levier` documenté : clé, libellé, famille, description,
unité, type, valeur par défaut, bornes, pas, profil temporel de 5 ans (au-delà,
la dernière fraction est maintenue) et rattachement au moteur (`champ` de
`DecisionPolitique`, `ligne` budgétaire ou effets directs documentés).

| Type | Comportement | Exemple |
|---|---|---|
| `curseur` | montant en Md€ ou en points ; 0 = statu quo | TVA (+1 pt ≈ +7,8 Md€), budget éducation, ONDAM |
| `interrupteur` | réforme binaire (0/1) | RIC, vote blanc, ISF, 49.3 |
| `cible` | **niveau** visé, jamais un incrément | effort de défense en % du PIB |

Deux règles structurent le moteur :

1. **Les leviers « cible » fixent un niveau.** Le moteur ne fait jamais
   « niveau actuel + montant » : il compare le niveau voulu à la référence, ce
   qui garantit l'idempotence du moteur sur l'horizon sélectionné.
2. **Les chocs exogènes sont appliqués en niveau.** Un choc pétrolier maintenu
   cinq ans reste à +X $/baril : il ne s'empile pas d'année en année
   (`MoteurSimulationSystemique._chocs_appliques`).

### 2 bis. Un horizon d'une ou deux mandatures

La barre d'en-tête offre **5 ans** (une mandature) ou **10 ans** (deux
mandatures). L'API `/api/simuler` accepte `horizon` de 1 à 10 ; ce choix est
également transmis au conseiller temps réel, au journal et au bilan de sortie.
Le préréglage `double_mandature` sélectionne 10 ans automatiquement.

La R&D de la période longue (P16-P21, détaillée dans
[`RD_DOUBLE_MANDATURE.md`](RD_DOUBLE_MANDATURE.md)) suit quatre nouveaux
leviers et réutilise l'adaptation climatique existante :

- besoin de patrimoine public non couvert, annualisé comme **proxy** à partir
  de l'estimation Cour des comptes à l'horizon 2050 (pas une dette comptable) ;
- dommages climatiques annualisés et évités, séparés du budget APU ;
- stocks d'investissements éducatifs et de défense arrivés à maturité après un
  délai exploratoire (sans rendement macro présumé) ;
- charge de réformes simultanées explicitement choisie par l'utilisateur,
  avec seuil de saturation présenté comme stress-test.

Le bloc **Transmission entre générations** affiche ces composantes sans score
composite. Les coefficients/hypothèses P16-P21 et leurs sources sont
reproduits dans l'audit de bas de page. Les valeurs ne sont pas des prévisions.

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
*Vue compacte*, *Régler les 101 leviers*. Le ruban mesure 44 pixels de haut :
il ne recouvre jamais les paramètres.

### Tous les paramètres, visibles et actionnables

- **Vue confort** : une carte par famille, chaque levier avec sa description,
  sa source et son curseur.
- **Vue compacte** (bascule dans la barre des leviers) : une ligne par levier —
  nom, curseur, valeur — pour que **les 101 paramètres** tiennent à l'écran.
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
visible pendant que l'on règle les 101 leviers. Elle répond à trois questions,
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

### 🦋 Le conseiller temps réel (effet papillon)

Chaque mouvement de réglage est traité comme une **décision** : sa position à
l'instant T par rapport à sa position **avant** le dernier mouvement. Pour
**tous** les leviers, curseurs comme interrupteurs, le serveur rejoue le
moteur deux fois — le levier à sa position d'avant, puis à sa position
d'après, toutes choses égales par ailleurs (`simulateur/conseil.py`, route
`/api/conseil`) — et la différence mesurée alimente un panneau qui s'actualise
à chaque geste, comme un conseiller spécialisé :

- **la formulation du mouvement** (« vous avez monté TVA taux normal de 0 à 1 »,
  « vous avez activé… ») et un verdict global ;
- **les effets directs** (domaines déclarés au catalogue pour ce levier) et
  **les ricochets** — les domaines qui bougent sans être déclarés, c'est
  l'effet papillon mesuré par le moteur plutôt que supposé ;
- **les grandeurs qui basculent** (déficit, dette, OAT, spread, tension,
  confiance, censure, croissance, score moyen) avec leur sens favorable ;
- **les garde-fous dont le niveau change** (avant → après, avec le message du
  barème) ;
- **le journal institutionnel nouveau** déclenché par la décision ;
- **des pistes de compensation** : les leviers non actionnés dont l'effet
  déclaré soutient le domaine le plus dégradé.

L'aide au survol du levier (`texteAideLevier`) rappelle elle aussi le dernier
mouvement, si bien que chaque message explicatif reste cohérent avec le geste
en cours. Rien n'est rédigé levier par levier : tout est dérivé du catalogue,
du moteur et du barème, donc le conseil reste exact quand le modèle évolue.

### 💶 Le coût / gain réel, en direct, partout où l'on règle

Deux indicateurs visuels mesurent l'argent réel à chaque instant :

1. **Dans la bulle du réglage déplacé** : dès le début du geste, le bloc
   « mesure live » annonce le calcul, puis affiche le **coût ou gain réel de
   ce réglage précis** — bannière rouge (coût) ou verte (gain) en
   transparence, avec le détail recettes / dépenses / déficit / charge de la
   dette et les sources officielles qui ancrent le chiffre. La mise à jour se
   fait par écriture DOM directe, sans re-rendu de la grille : le chiffre est
   lisible dès la fin du mouvement.
2. **Dans la console de veille** : le **coût / gain réel des réglages globaux
   croisés** — recettes nouvelles, dépenses nouvelles, solde net de l'ensemble
   des leviers actifs, déficit et dette finals — recalculé à chaque
   simulation, donc à chaque mouvement.

Les deux affichages descendent du même calcul : deux exécutions réelles du
moteur (levier à sa position d'avant, puis d'après), dont on soustrait les
flux budgétaires de la dernière année. Chaque chiffre est traçable : le
conseil cite les valeurs officielles d'ancrage (PIB, OAT, BCE, inflation…)
avec leur source et leur période.

### 🔍 Audit & traçabilité : le simulateur à livre ouvert

La section « Audit & traçabilité » en bas de page rend tout recoupement
possible, ce n'est pas une boîte noire :

1. **sources officielles des données d'entrée** — valeur retenue, période,
   statut (live / référence), source, URL, licence ;
2. **les 20 domaines et leurs 74 indicateurs** — la formule du score et la
   source de chaque chiffre ;
3. **les 101 leviers** — champ / ligne budgétaire, effets déclarés (thème et
   coefficient), source ;
4. **les 31 garde-fous** (`GET /api/garde_fous`) — strate, bornes
   (seuil → niveau) et source institutionnelle de chaque seuil ;
5. **la méthode des dynamiques croisées** — différences finies, scores
   0-100 contre la trajectoire de référence, double exécution du conseiller.

Le pied de page porte la bannière **MRSC** : outil open-source produit par son
créateur pour l'intérêt général, d'utilisation gratuite, dont nul ne peut
s'attribuer la paternité.

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

## 6. Les bulles explicatives par réglage

Chaque réglage porte un bouton **« interactions »** : la fiche s'ouvre **dans la
carte du levier** (jamais par-dessus), donc les 101 paramètres restent visibles et
actionnables pendant la lecture. Le contenu n'est pas rédigé à la main : il est
calculé par `simulateur/bulles.py` à partir du catalogue, des 74 formules
d'indicateurs et du moteur, puis servi par `GET /api/bulle?levier=…`.

Une bulle répond à trois questions, dans cet ordre :

1. **Que déclenche ce réglage ?** La chaîne technique réelle, lue dans le code :
   ligne budgétaire ou champ du moteur → médiateurs émis (Md€, points,
   milliers…) → indicateurs qui les lisent (avec leur coefficient) → domaines
   notés. Quand un médiateur n'est lu par aucune formule, la bulle le dit :
   soit il passe par une autre échelle du même médiateur (`_mde` vs `_pts`),
   soit par l'agrégat budgétaire, soit — cas rare et signalé — il n'atteint
   pas les scores. Un levier piloté par un champ du moteur (DGF, plan
   semi-conducteurs, clause de sauvegarde défense…) affiche en plus l'état
   interne atteint.
2. **Quelles répercussions, à quelles amplitudes ?** Pour chaque borne du
   réglage (et pour un pas au-delà du défaut), une simulation réelle compare le
   réglage isolé — tous les autres leviers restent neutres — à la trajectoire de
   référence : score des 20 domaines, écart chiffré des indicateurs (les
   12 plus forts), niveau des 33 garde-fous, risque population, verdict par
   strate et **journal institutionnel** (« Report forcé sur la taxe foncière »,
   « Alerte censure : probabilité de chute du cabinet à 87,5 % », « Sortie de la
   PDE », « Plan semi-conducteurs : résilience de 25 % face à un blocus »…).
3. **Opportunités ou désagréments ?** Une lecture guidée : gains classés,
   pertes classées, points à surveiller (garde-fous franchis ou aggravés, strate
   concernée), puis des **pistes de compensation** tirées des effets déclarés au
   catalogue des autres leviers — de quoi corriger un désagrément sans
   improviser.

État mesuré sur le catalogue actuel (réglage isolé, bornes des 101 leviers) :

| Constat | Valeur |
|---|---|
| Leviers déplaçant au moins un domaine à leurs bornes | **100 / 101** |
| Leviers dont un médiateur n'atteint pas les scores | **0** (tous passent par une formule, une autre échelle ou un agrégat) |
| Seuil de mouvement retenu | 0,2 point de score |
| Exception documentée | `clause_sauvegarde_defense` : aucun domaine ne bouge, mais la sortie des dépenses de défense du calcul PDE est journalisée en strate 3 |
| Coût de calcul d'une bulle | ≈ 25 ms (mise en cache par contexte) |
| Coût du catalogue complet | ≈ 4,5 s au **premier** appel (`GET /api/bulles`), ≈ 57 ms ensuite : le catalogue est mémoïssé tant que le contexte « instant T » n'a pas changé |

Réglages possibles : `GET /api/bulles?detail=resume` (sans le détail indicateur
par indicateur ni le journal) et `?mesure=0` (chaîne d'interaction seule).

### Aides au survol : chaque réglage s'explique sans clic

Passer la souris (ou poser le focus clavier) sur un curseur, un interrupteur, une
étiquette de valeur, un bouton, une case à cocher, une carte de domaine, un
préréglage ou un scénario affiche une **infobulle instantanée** — sans attendre
le délai du `title` natif du navigateur et sans recouvrir durablement l'écran :

| Élément survolé | Contenu de l'infobulle |
|---|---|
| Curseur ou interrupteur d'un levier | libellé, famille, unité, **valeur actuelle** et défaut, plage et pas, description, **effets déclarés** au catalogue, **mesures en direct** sous le curseur, mouvements aux bornes et rappel de la bulle |
| Bouton « interactions » | ce que la bulle contient et le fait qu'elle s'ouvre dans la carte |
| Boutons d'action | ce que fait le bouton (rafraîchir, réinitialiser, simuler, exporter, densité, détails des seuils) |
| Puces d'impact et puces de strate | domaine et sens de l'effet mesuré, niveau du garde-fou et nombre de seuils en alerte |
| Cartes de domaine | description, score, écart à la référence, tendance sans politique, nombre d'indicateurs |
| Préréglages et scénarios | contenu et effet du clic (charger les leviers / rejouer le moteur d'origine) |

La couche d'infobulle est **passive** (`pointer-events:none`) : elle ne capte
aucun clic, disparaît au départ de la souris, au clic, au défilement et à
l'ouverture d'une bulle — les 101 paramètres restent donc tous actionnables.
Lecture du code : `initialiserInfobulles()`, `survoler()`, `texteAideLevier()`
dans `simulateur/interface.py`.

Lecture du module : `simulateur/bulles.py` — thèmes déclarés → domaines
(`THEMES_DOMAINES`), échelons traversés par thème (`THEMES_STRATES`), index des
consommateurs de chaque médiateur, mesures par borne, lecture guidée.

---

## 7. Impacts croisés (matrice levier × domaine)

La matrice n'est pas saisie à la main : pour chaque levier actif, le modèle
**rejoue la simulation avec ce seul levier ramené à sa valeur neutre** et mesure
la variation de score de chaque domaine (différences finies, cache par empreinte
SHA-256 des paramètres et du contexte). L'effet affiché est donc la contribution
marginale du levier à la politique en cours, domaine par domaine.

---

## 8. Cascade des 5 échelons

L'interface affiche, année par année, l'état des cinq strates : locale (tension,
services de proximité, taxe foncière), nationale (PIB, déficit, dette, charge de
la dette, censure), européenne (PDE, bouclier TPI), mondiale (OAT, spread, note
souveraine, Brent, inflation) et géopolitique (tension, chokepoints, effort de
défense, semi-conducteurs). Le journal causal reprend les commentaires produits
par le moteur à chaque étape.

---

## 9. Exécution et API

```bash
python -m simulateur.dashboard --host 0.0.0.0 --port 8080 [--rafraichir]
python -m simulateur.moteur_parametrique --preset mandature --json
python -m simulateur.moteur_parametrique --levier effort_defense_pct_pib=3.5 --levier reforme_ric=1
```

| Route | Méthode | Contenu |
|---|---|---|
| `/` | GET | page unique du simulateur |
| `/api/catalogue` | GET | familles, 101 leviers, 14 préréglages, 20 domaines |
| `/api/contexte` | GET | contexte instant T + provenance + sources navigateur + diagnostic |
| `/api/marches` | GET | catalogue de 13 indices; `?refresh=1` demande une collecte auprès du fournisseur tiers et ne garantit pas le temps réel |
| `/api/simuler` | GET/POST | simulation paramétrique (étapes, domaines, synthèse, impacts, **diagnostic de seuils**, **lecture en clair**) ; `horizon` jusqu'à 10 ans pour la période de deux mandatures (`docs/RD_DOUBLE_MANDATURE.md`) |
| `/api/comparer` | GET | comparaison des 14 préréglages **avec leur verdict de garde-fous** |
| `/api/conseil` | POST | conseiller temps réel : lecture du **dernier mouvement** d'un levier (`cle`, `avant`, `apres`, `parametres`, `horizon`) — effets directs, ricochets, grandeurs, garde-fous, journal, compensations, **budget réel (Md€) et sources officielles** |
| `/api/garde_fous` | GET | barème complet des 31 garde-fous : strates, bornes, sources institutionnelles (audit) |
| `/api/bulles` | GET | bulles explicatives du catalogue (`?levier=`, `?detail=resume`, `?mesure=0`) |
| `/api/bulle` | GET | bulle d'un levier : chaîne d'interaction, mesures par borne, lecture guidée |
| `/api/lexique` | GET | lexique « compréhensible pour tous » : 83 termes en 6 catégories, avec recherche `?q=` et la liste des formes à souligner |
| `/api/presets` | GET | préréglages seuls |
| `/api/proxy` | GET | relais d'une source du registre (liste blanche) |
| `/api/donnees` | POST | valeurs relevées par le navigateur → recalibrage |
| `/api/scenarios`, `/api/run`, `/api/export` | GET | scénarios historiques du dépôt (compatibilité) |

---

## 10. Réglages du dépôt

L'aperçu social, la description, les sujets et le site web déclarés sont tenus à
jour dans [`REPOSITORY_DETAILS.md`](REPOSITORY_DETAILS.md), avec les scripts
`outils/details_depot.py` (bloc à coller) et `outils/apercu_social.py` (image
1280 × 640).

## 10 bis. Compréhensible pour tous

Le simulateur manipule des grandeurs que personne n'emploie dans la vie
courante. Cette section regroupe les quatre dispositifs qui rendent la page
lisible sans rien retirer à la rigueur du modèle — et sans jamais ajouter un
chiffre qui ne serait pas déjà calculé.

### 📖 Le lexique (`GET /api/lexique`)

83 termes en six catégories, définis **en français ordinaire**. La règle de
rédaction est stricte : on n'explique pas un mot de métier par un autre mot de
métier. « Spread » devient « l'écart entre le taux auquel la France emprunte et
celui de l'Allemagne », pas « un écart de rendement souverain ». Chaque entrée
porte sa définition, un repère chiffré quand il existe, et des renvois vers les
termes voisins.

Trois usages dans la page :

| Usage | Comportement |
|---|---|
| Panneau (bouton « 📖 Lexique ») | liste complète, recherche instantanée, regroupée par catégorie |
| Soulignement dans les textes | les termes techniques des messages affichés sont soulignés en pointillé ; la définition s'affiche au survol ou au focus clavier |
| API | `?q=` filtre sur le libellé, les alias et le texte des définitions |

Le balisage respecte les attributs HTML : un `>` situé à l'intérieur d'un
attribut `data-aide` (qui peut contenir du HTML) n'est pas traité comme une fin
de balise — sinon la page serait corrompue au premier `data-aide` venu.

### 🧭 La « lecture en clair » (`simulateur/clarte.py`)

Le module **ne calcule rien** : il relit la sortie du moteur et en tire une
dizaine de phrases complètes, dans l'ordre des questions que l'on se pose
vraiment — combien l'État gagne ou perd, où vont le déficit et la dette, à quel
prix il emprunte, ce que ça change pour les ménages, quels secteurs bougent, où
sont les alertes. Le résultat est servi dans le champ `lecture` de
`/api/simuler`.

Trois règles, chacune couverte par un test :

1. **fidélité** — tout nombre affiché dans une phrase existe dans la charge du
   moteur ;
2. **honnêteté** — un déficit négatif est annoncé comme un excédent, une dépense
   négative comme une économie, un domaine qui ne bouge pas n'est pas désigné
   comme « le plus pénalisé » ;
3. **neutralité** — aucune phrase ne dit « c'est bien » ou « c'est mal ». Les
   niveaux (favorable / défavorable / neutre) qualifient un écart par rapport à
   la référence du modèle, pas un jugement politique.

### ❓ Le guide de démarrage

Quatre étapes, affichées à la **première visite** : vous êtes aux commandes ·
tout est comparé à une référence · la veille vous prévient · vérifiez tout. Le
guide est mémorisé dans le navigateur (`localStorage`) et n'est **jamais**
transmis au serveur ; en navigation privée, où le stockage est refusé, il
s'affiche à nouveau plutôt que de disparaître. Rouvrable depuis l'en-tête.

### 🗺️ Le sommaire

La page est longue : un bandeau en haut rappelle l'ordre de lecture —
*comprendre → ce que ça donne → régler → mesurer → vérifier* — avec des
raccourcis vers chaque section.

## 10 ter. Fluidité mesurée

Les chiffres ci-dessous sont exécutés, reproductibles par
`python3 outils/mesurer_fluidite.py`, et détaillés — limites comprises — dans
[`RD_OPTIMISATION_FLUIDITE.md`](RD_OPTIMISATION_FLUIDITE.md).

| Ce qui était lent | Ce qui l'expliquait | Ce qui est fait |
|---|---|---|
| Simulation : 255 Kio échangés à chaque geste | le JSON de sortie, en clair | compression HTTP négociée → **37 Kio** |
| Catalogue : 104 Kio | idem | **25 Kio** |
| Contexte : 97 Kio | idem | **14 Kio** |
| Sept vues de strate reconstruites à chaque simulation | six panneaux invisibles | rendu à l'ouverture de l'onglet |
| Matrice levier × domaine vidée pendant les réglages | non recalculée pendant le geste | dernière matrice conservée, fraîcheur annoncée |
| `/api/bulles` : 4,5 s par appel | 101 bulles recalculées | mémoïsation → **57 ms** |

Trois garde-fous : la compression ne s'applique **jamais à perte** (sous
512 octets, ou si le résultat n'est pas plus petit, la charge brute est
renvoyée) ; `Vary: Accept-Encoding` accompagne toute réponse compressible, pour
qu'aucun intermédiaire ne serve du gzip à un client qui ne le décode pas ; et
rien de tout cela ne modifie une formule, une donnée source ou un seuil.

## 11. Limites assumées

1. **Modèle, pas prophétie.** Les coefficients sont documentés et sourcés
   (multiplicateurs OFCE/FMI, élasticités INSEE, loi d'Okun 1 pt ≈ 150 000
   emplois) mais restent des choix. Ils sont lisibles, contestables et
   modifiables dans `domaines.py`.
2. **Écarts, jamais niveaux.** Voir l'avertissement du § 4.
3. **Horizon sélectionnable de 5 ou 10 ans.** Il n'y a pas encore de module démographique détaillé par âge ni de budgets carbone ; les hypothèses P16-P21 sont des scénarios exploratoires, pas des prévisions.
4. **Sources non redistribuables** (Yahoo, Stooq) : elles servent au rafraîchissement
   en direct, pas à l'embarquement de données ; le snapshot embarqué ne contient
   que des valeurs de sources réutilisables ou de référence documentaire du projet.
5. **Un proxy fermé.** `/api/proxy` n'accepte que les 38 indicateurs du registre,
   jamais une URL fournie par le client.

---

## 12. Strates, budget ménage et stress-test boursier

La section « Effets comparés par strate » réunit sept panneaux : local,
national, Europe, monde, géopolitique, ménages et bourse. Les trajectoires
macro comparées sont les écarts entre le scénario réglé et la référence neutre;
les repères observés restent séparés des valeurs simulées.

### Local, comptes publics et échelles territoriales

Les repères OFGL 2025 sont des agrégats par grands niveaux (communes, EPCI,
départements, régions/CTU), pas les comptes de la commune de l'utilisateur.
La taxonomie va du hameau/quartier à l'État et distingue la France
métropolitaine, DROM et COM, mais une catégorie absente de données ventilées
n'est pas fabriquée : hameaux, budgets de collectivités individuelles et
comptes DROM/COM séparés ne sont pas simulés. L'onglet national juxtapose les
comptes INSEE observés et les variations directes par source de recettes ou
poste de dépense du moteur; cette liste de leviers n'est pas un budget complet.

### Profil ménage

Les montants de salaire, cotisations, revenus imposables, transferts, dépenses
par poste et capital de prêt sont saisis dans l'état local de la page. Ils ne
sont pas envoyés au serveur. L'IR s'appuie sur le barème 2026 des revenus 2025
par part de quotient familial : les taux affichés sont des taux marginaux, pas
des classes sociales, des seuils de patrimoine ou le taux moyen du foyer.
L'impact des aides est une répartition de flux macro selon les effectifs
nationaux publiés, seulement si l'utilisateur déclare son éligibilité; aucun
droit individuel n'est attribué.

### Cotations et stress-test

`simulateur/marches.py` interroge à la demande Yahoo Finance pour 13 indices
représentatifs (CAC 40, grands indices européens, américains et asiatiques,
entre autres). Les cours ne sont pas stockés dans le dépôt. Le tableau donne la
devise source, le dernier niveau, la variation de séance, l'horodatage du cours
et la date de collecte. Le statut « dernier cours » signale une date locale
antérieure (fermeture/jour férié possible ou flux retardé); « ancien » signale
plus de 72 heures. Les calendriers de jours fériés ne sont pas intégrés et la
latence exacte du fournisseur n'est pas garantie : vérifier la page de la place
avant de réutiliser un cours.

Les curseurs boursiers définissent des chocs hypothétiques et les montants
exposés par catégorie (IR, entreprises, associations, collectivités aux
échelles disponibles, organismes/établissements publics ou privés, élus à titre
personnel). Le P/L est une multiplication brute exposition × variation, sans
impôt, frais, dividendes, conversion de devises ni valeur réelle de portefeuille.
Ne pas saisir deux fois une même exposition dans une catégorie agrégée et ses
sous-niveaux. Le stress n'est pas encore transmis au PIB, à l'emploi, au déficit
ou aux recettes de l'État. Le recalcul local est instantané; la fraîcheur du
cours dépend du fournisseur et des séances, elle ne l'est pas nécessairement.
