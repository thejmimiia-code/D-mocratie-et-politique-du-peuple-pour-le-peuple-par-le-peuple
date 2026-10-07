# R&D — Optimisation, fluidité et lisibilité (octobre 2026)

## Objectif et statut

Deux questions distinctes, traitées ensemble parce qu'elles se répondent :

1. **Fluidité.** Le simulateur recalcule tout à chaque mouvement de curseur.
   Combien de temps et combien d'octets cela coûte-t-il réellement, et que peut-on
   en retirer sans toucher aux équations ?
2. **Lisibilité.** Les sorties du moteur sont exactes et illisibles pour qui ne
   pratique pas les finances publiques. Comment les rendre compréhensibles sans
   rien ajouter aux chiffres ?

Rien de ce qui suit ne modifie une formule du modèle, une donnée source ou un
seuil. Les scores, trajectoires et garde-fous sont **identiques** avant et après
: seules la taille des échanges, le travail d'affichage et la présentation du
résultat changent. La contrepartie est vérifiable : la suite de tests passe de
416 à 508 tests, sans aucune modification de valeur attendue.

Résultat exécuté le 8 octobre 2026, branche de travail `arena/9c4ec4d0-…`.

---

## Protocole

La campagne est reproductible, sans réseau et sans dépendance :

```bash
python3 outils/mesurer_fluidite.py              # tableau lisible
python3 outils/mesurer_fluidite.py --markdown   # tableau pour ce document
python3 -m unittest discover -s tests -p "test_*.py"
```

Le script lance le serveur sur un port libre en `SIMULATEUR_HORS_LIGNE=1`,
interroge chaque route comme le ferait un navigateur, et rapporte le volume
**réellement transmis** (taille annoncée par `Content-Length`, donc mesurée sur
le fil, pas estimée) et la durée de l'aller-retour.

Deux précautions, parce qu'une mesure de performance est facile à truquer sans
le vouloir :

* **le meilleur cas est écarté au profit de la médiane** sur cinq répétitions,
  sauf mention contraire : un unique appel rapide ne prouve rien ;
* **le contexte est figé** (`SIMULATEUR_HORS_LIGNE=1`). Sans cela, une partie de
  la latence mesurée serait celle d'Eurostat ou de la BCE, pas celle du dépôt.

---

## Résultats réellement exécutés

### Volume échangé (compression HTTP négociée)

| Route | Brut | Compressé | Gain |
|---|---:|---:|---:|
| `/` (page complète) | 202,9 Kio | 56,5 Kio | 72 % |
| `/api/catalogue` | 104,3 Kio | 24,5 Kio | 77 % |
| `/api/contexte` | 97,3 Kio | 14,0 Kio | 86 % |
| `/api/garde_fous` | 29,4 Kio | 7,4 Kio | 75 % |
| `/api/lexique` | 48,5 Kio | 12,9 Kio | 73 % |
| `/api/marches` | 12,1 Kio | 1,7 Kio | 86 % |
| `POST /api/simuler` (5 ans) | 254,8 Kio | 37,4 Kio | 85 % |

Une simulation complète coûte donc **37 Kio sur le réseau au lieu de 255 Kio**,
pour exactement le même contenu. C'est le gain le plus important de cette R&D,
et le moins visible : le calcul serveur ne change pas (32 à 51 ms), c'est le
transfert qui était devenu le coût dominant.

### Temps de réponse

| Mesure | Avant | Après |
|---|---:|---:|
| `POST /api/simuler`, 5 ans | ~35 ms | 51 ms (dont compression) |
| `POST /api/simuler`, 10 ans | ~55 ms | 51 ms |
| `GET /api/bulles?detail=resume`, premier appel | 4 538 ms | 4 538 ms |
| `GET /api/bulles?detail=resume`, appels suivants | 4 538 ms | **57 ms** |

Deux lectures honnêtes de ce tableau :

* la compression **coûte** un peu de temps processeur (quelques millisecondes)
  pour gagner 85 % de volume. Sur une connexion lente ou un forfait mobile, le
  calcul est gagnant ; sur une boucle locale, il est neutre. Le seuil de
  512 octets évite de payer ce coût pour les petites réponses ;
* le catalogue complet des bulles reste lent au **premier** appel (4,5 s). Le
  cache le ramène à 57 ms ensuite, mais la lenteur initiale n'a pas disparu :
  elle est déplacée, pas supprimée. La page ne l'utilise jamais au démarrage
  (elle charge les bulles une par une, à la demande), ce qui rend le coût
  invisible en pratique.

### Travail d'affichage (côté navigateur)

Mesure indirecte : le nombre de panneaux reconstruits à chaque simulation.

| Ce qui est reconstruit à chaque simulation | Avant | Après |
|---|---:|---:|
| Panneaux de strate (onglets) | 7 | 1 (l'onglet ouvert) |
| Matrice levier × domaine | vidée puis reconstruite | conservée si non recalculée |

Le rendu des sept vues (local, national, Europe, monde, géopolitique, ménages,
bourse) représentait l'essentiel du travail d'affichage : six d'entre elles
étaient construites pour rien, puisque seul l'onglet ouvert est visible. Elles
sont désormais construites **à l'ouverture de l'onglet**.

La matrice croisée levier × domaine exige une simulation par levier : pendant
qu'un curseur bouge, elle n'est pas recalculée — elle était donc effacée à
chaque geste, ce qui faisait disparaître l'information sous les yeux. La
dernière matrice calculée est conservée, et son état de fraîcheur est affiché
(« dernière matrice calculée »), plutôt que de laisser croire à un bug.

---

## Ce qui a été fait

### 1. Compression HTTP négociée — `simulateur/compression.py`

Module de 200 lignes, bibliothèque standard uniquement. Il fait deux choses :

* **négocier** l'encodage à partir de `Accept-Encoding`, en respectant les
  qualités (`q=`), les refus (`q=0`) et le joker (`*`). Un refus nominatif
  l'emporte toujours sur un joker acceptant ; à qualité égale, la préférence du
  serveur départage (meilleur ratio d'abord), car c'est lui qui connaît le coût
  de chaque algorithme ;
* **compresser**, mais seulement si cela sert : sous 512 octets, ou si le
  résultat n'est pas plus petit que l'original, la charge brute est renvoyée
  telle quelle. Un serveur ne doit jamais renvoyer une réponse compressée plus
  lourde — le test `test_une_compression_non_rentable_est_abandonnee` vérifie
  cette propriété sur des données aléatoires, qui sont incompressibles.

Brotli et Zstandard sont utilisés **s'ils sont importables** (CPython ≥ 3.14 ou
module tiers) ; leur absence n'est pas une erreur, `gzip` est le repli.

`Vary: Accept-Encoding` accompagne toute réponse compressible. Sans cet
en-tête, un intermédiaire pourrait servir du gzip à un client qui ne le décode
pas : la page deviendrait illisible. C'est un test.

### 2. Rendu différé des onglets

`renderOngletsStrates()` construisait sept panneaux à chaque simulation ;
`rendreOngletStrate()` ne construit plus que l'onglet ouvert, et
`afficherOngletStrate()` construit l'onglet au moment où il devient visible.
Le harnais Node (`tests/navigateur_interface.mjs`) a été mis à jour en
conséquence : il parcourt les sept onglets un par un, vérifie que chacun se
remplit à l'ouverture, et vérifie aussi qu'un onglet jamais visité **reste
vide** — c'est précisément l'économie recherchée.

### 3. Cache du catalogue de bulles — `catalogue_bulles()` dans `dashboard.py`

Les 101 bulles « détail complet » demandent environ 4,6 s de calcul et
2,1 Mio de JSON. Le contenu ne dépend que du catalogue des leviers et du
contexte « instant T » : il est donc identique d'une requête à l'autre. La clé
de cache contient l'horodatage du contexte, de sorte qu'un « Rafraîchir les
données » invalide naturellement le cache. Un verrou évite que deux requêtes
concurrentes ne calculent la même chose ; le cache est plafonné à six entrées.

### 4. Lexique — `simulateur/lexique.py`

83 termes, six catégories, servis par `GET /api/lexique` (avec `?q=`).
Principe de rédaction : **on n'explique pas un mot de métier par un autre mot de
métier**. « Spread » est défini par « l'écart entre le taux auquel la France
emprunte et celui de l'Allemagne », pas par « écart de rendement souverain ».
Chaque entrée porte une définition, un repère chiffré quand il existe, et des
renvois vers les termes voisins.

Trois usages dans la page :

* un **panneau** ouvrable depuis l'en-tête, avec recherche ;
* le **soulignement** des termes techniques dans les textes affichés (console,
  lecture en clair, alertes, provenance), dont la définition s'affiche au survol
  ou au focus clavier ;
* une **liste de formes** publiée par l'API, triée du plus long au plus court,
  pour que « point de PIB » gagne sur « PIB » au moment de baliser un texte.

Le balisage est le seul endroit un peu délicat de cette R&D : un `data-aide`
peut contenir du HTML (`<b>…</b>`), donc un `>` ne marque pas forcément la fin
d'une balise. Le parcours respecte les guillemets ; un test vérifie qu'un
attribut contenant `<b>PIB</b> dette` ressort intact.

Son coût a été mesuré, parce qu'une expression régulière à 286 alternatives
lancée sur toute la page à chaque simulation aurait pu coûter plus cher que la
fluidité qu'elle est censée servir : **1,6 ms pour 25 Kio de HTML** comportant
480 termes à souligner (V8, Node 22). Les cinq zones balisées restent donc
sous la dizaine de millisecondes, très en dessous du délai de 180 ms qui
regroupe les mouvements de curseur.

### 5. Lecture en clair — `simulateur/clarte.py`

Le module **ne calcule rien**. Il relit une sortie de simulation et en tire une
dizaine de phrases complètes, dans l'ordre des questions que l'on se pose :
combien l'État gagne ou perd, où vont le déficit et la dette, à quel prix il
emprunte, ce que ça change pour les ménages, quels secteurs bougent, où sont
les alertes. La sortie est ajoutée au champ `lecture` des réponses de
`/api/simuler`.

Trois règles de rédaction, chacune couverte par un test :

* **fidélité** : un nombre affiché dans une phrase doit exister dans la charge
  du moteur (`test_aucune_phrase_n_invente_de_chiffre`) ;
* **honnêteté** : un déficit négatif est dit « excédent », une dépense négative
  « économie », un domaine qui ne bouge pas n'est pas désigné comme « le plus
  pénalisé » ;
* **neutralité** : aucune phrase ne dit « c'est bien » ou « c'est mal ». Les
  niveaux (favorable / défavorable / neutre) qualifient un écart par rapport à
  la référence, pas un jugement politique.

### 6. Guide de démarrage et sommaire

Quatre étapes, affichées à la première visite seulement (mémorisé dans le
navigateur, jamais envoyé au serveur) : vous êtes aux commandes · tout est
comparé à une référence · la veille vous prévient · vérifiez tout. Le guide est
rouvrable depuis l'en-tête, et la navigation privée — où le stockage est refusé
— n'empêche pas son affichage.

Le sommaire rappelle l'ordre de lecture : *comprendre → ce que ça donne →
régler → mesurer → vérifier*, avec des raccourcis vers les sections.

---

## Ce que ces mesures ne disent pas

À garder en tête avant de citer ce document :

1. **Les mesures sont locales.** Elles ont été faites sur une boucle locale,
   sans réseau, sans proxy, avec un seul client. Le gain de volume est
   structurel (il se retrouvera partout) ; les durées, elles, dépendent de la
   machine et de la charge.
2. **La compression ne remplace pas la sobriété.** Une réponse de 255 Kio
   compressée à 37 Kio reste une réponse de 255 Kio à désérialiser côté client.
   La réduction réelle du volume — retirer du payload les textes statiques déjà
   présents dans le catalogue (formules et sources des indicateurs, ~50 Kio sur
   les deux jeux de domaines) — reste ouverte ; elle a été écartée ici parce
   qu'elle touche au contrat de l'API publique, pas seulement à la page.
3. **Le rendu navigateur n'a pas été profilé.** Faute d'instrumentation
   sérieuse dans cet environnement (pas de navigateur réel), le gain du rendu
   différé est compté en panneaux construits, pas en millisecondes. C'est une
   borne haute raisonnable, pas une mesure.
4. **La lisibilité ne se mesure pas automatiquement.** Les tests vérifient la
   présence, la complétude et la non-contradiction des définitions ; ils ne
   vérifient pas qu'une phrase est claire. Seule une relecture humaine le peut,
   et les définitions du lexique méritent d'être relues par quelqu'un qui
   découvre le sujet.

## Suite envisagée

1. Profiler le rendu dans un vrai navigateur (Performance API) avant d'optimiser
   davantage : on ignore encore si le coût est dans le DOM ou dans le calcul.
2. Réduire le payload de `/api/simuler` en retirant les textes statiques déjà
   servis par `/api/catalogue`, avec un paramètre explicite pour conserver la
   forme complète aux clients de l'API.
3. Découper `/api/bulles` en pages : le cache masque le problème, il ne le
   résout pas — un premier appel à 4,5 s reste un premier appel à 4,5 s.
4. Faire relire le lexique par des non-spécialistes et tenir un journal des
   termes mal compris : c'est la seule métrique de lisibilité qui vaille.
