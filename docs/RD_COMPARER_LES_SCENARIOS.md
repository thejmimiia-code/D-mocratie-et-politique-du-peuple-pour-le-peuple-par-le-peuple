# R&D — Comparer les scénarios, à l'écran

**Passe du 14 octobre 2026.** Ce document raconte comment la route
`/api/comparer` — seize simulations faites par le moteur, servies depuis des
mois — est entrée dans la page : ce qu'elle contient, ce que l'écran en montre,
ce qui l'y surveille, et ce qu'un tableau comparatif ne peut pas dire.

---

## 1. Le constat : une route servie, testée, et jamais appelée

Le contrôle de couverture des routes (`tests/test_couverture_des_routes.py`,
passe du même jour) exige que chaque route servie soit **mise en œuvre par la
page** ou **excusée par écrit**. `/api/comparer` était excusée, avec une raison
qui semblait bonne :

> « la comparaison des 16 préréglages à l'année finale est exercée par la veille
> en ligne et par les tests du serveur ; dans la page, les préréglages se
> rejouent un par un dans la grille des scénarios, ce qui donne le même chiffre
> sans un second calcul complet. »

En la relisant, deux choses n'allaient pas :

1. **la grille des scénarios ne donne pas le même chiffre.** Elle montre les
   **11 scénarios historiques** (`/api/scenarios` : choc mondial, Taïwan,
   Hormuz…) et les rejoue à la demande ; la comparaison porte sur les **16
   préréglages** — dont l'austérité, la justice sociale, la transition
   écologique, le verrouillage par le haut — et sur leur **année finale** côte à
   côte. Deux catalogues différents, deux usages différents ;
2. **elle coûte trois cents millisecondes, pas trois secondes.** Mesure du
   14 octobre 2026 : `POST /api/simuler` prend ~35 ms ; `/api/comparer` rejoue
   seize simulations en **283 ms** et pèse **73 768 octets bruts, 9 795 octets
   compressés** — moins que les contre-pouvoirs, qui étaient pourtant affichés.

Ce que la route contient, pour chaque préréglage : son libellé, le solde de ses
mesures (recettes nouvelles moins dépenses nouvelles, à l'année terminale), la
dette et le déficit publics en points de PIB, le risque pour la population sur
100, le nombre de seuils en alerte, les scores des 20 domaines, la note
souveraine, le verdict des garde-fous et le bilan intergénérationnel. Le tableau
de l'écran en montre **cinq colonnes chiffrées**, et rien d'autre : afficher
cent quatre-vingts nombres ne serait pas une comparaison, ce serait un dump.

---

## 2. La décision : un tableau qu'on peut ranger, jamais recalculer

Trois choix, chacun avec sa raison écrite dans le code :

- **Un vrai `<table>`**, pas une grille de `<div>`. Un tableau HTML est étiqueté
  pour les lecteurs d'écran, il s'imprime, et la page sait déjà en faire une
  **carte** sur téléphone (`tableauEnCartes` : chaque valeur porte alors le nom
  de sa colonne). Aucune mise en page nouvelle à inventer.
- **Le rangement se fait par boutons de colonne**, en trois états : un clic range
  en croissant, un second en décroissant, un troisième rend l'ordre du
  catalogue. `aria-sort` porte l'état (`ascending`, `descending`, `none`) et le
  titre est un `<button>` : un titre cliquable qui n'est pas un bouton n'existe
  pas au clavier. **Ranger n'est pas calculer** : le tri lit les valeurs servies,
  il n'en produit aucune.
- **Les barres se mesurent sur le plus fort montant servi.** Le solde de chaque
  scénario est accompagné d'une barre proportionnelle, verte quand il dégage
  (recettes : `var(--classe-recettes)`), rouge quand il coûte (dépenses :
  `var(--classe-depenses)`) — les deux variables de la charte, pas deux
  hexadécimaux de plus. La barre est décorative (`aria-hidden`) : **le signe et
  l'unité sont écrits à côté**, donc la couleur ne porte jamais l'information
  seule.

Et deux limites, écrites dans la section elle-même :

- **« ce sont les scénarios du catalogue, pas vos réglages »** — la route ne
  compare que les préréglages ; les réglages du lecteur vivent dans la balance,
  plus haut. Confondre les deux serait la faute la plus facile à commettre et la
  plus coûteuse ;
- **aucun chiffre n'est recalculé dans le navigateur.** Un contrôle statique
  refuse les 39 valeurs chiffrées du jour (« 41,6 », « −474,0 », « 141,0 »,
  « 117,2 »…) et les 16 libellés des scénarios : ils viennent du serveur, sinon
  ils vieilliraient dans la page au premier changement de contexte — et le
  contexte « instant T » entre dans chaque simulation, donc ces chiffres bougent
  déjà d'un mois à l'autre.

---

## 3. Ce que la section coûte, et pourquoi elle ne coûte rien au démarrage

| Mesure du 14 octobre 2026 | Valeur |
|---|---:|
| `/api/comparer` — réponse servie | 73 768 o bruts · **9 795 o compressés** |
| calcul côté serveur (16 simulations) | **283 ms** |
| code de la section dans la page | **+2 770 o compressés** |
| page entière, après la section | **113 222 o** (document servi) · **113 885 o** (fichier publié) — plafond : 122 271 o |

La section se charge **quand elle approche de l'écran** (`IntersectionObserver`,
marge de 400 px), avec un bouton « Charger maintenant » pour les navigateurs qui
n'ont pas d'observateur. La page ne paie donc pas seize simulations à
l'ouverture : le budget du **premier écran** (282 010 o compressés) reste tenu, et
son contrôle vérifie que la comparaison n'entre pas dans ses membres.

La route est entrée dans la table des plafonds (`outils/budgets_fluidite.py`) le
jour même : ancre **9 795 o**, plafond **10 775 o**. Une charge qui entre à
l'écran entre aussi au budget — c'est désormais la même discipline.

**Le plafond de la page, lui, n'a pas été relevé.** La marge de 10 % ancrée la
veille (11 116 o) a absorbé la section (2 770 o), et il reste **8 386 o** avant
plafond : c'est exactement ce à quoi sert une marge — payer une section voulue
sans réécrire l'engagement à chaque fois.

---

## 4. Ce qui surveille cette section

### 31 contrôles (`tests/test_comparer_en_page.py`)

Trois familles : la section est là et le sommaire y mène ; la route est appelée
une fois, sans rien recalculer ; le rangement et l'affichage respectent les
règles de la maison. Quelques-uns méritent d'être nommés :

- **aucun chiffre du jour, aucun libellé de scénario** dans la page (39 valeurs et
  16 libellés refusés nommément) ;
- **le bloc est au niveau du script, pas dans une fonction** — ce contrôle-là a
  attrapé une vraie erreur le jour même : inséré après l'accolade ouvrante de la
  fonction suivante, le bloc restait du JavaScript valide, `node --check` passait,
  et les `let` devenaient locaux en silence ;
- **aucune opération sur les valeurs servies** (`toFixed`, `parseFloat`,
  `Math.pow/sqrt/log` interdits dans le bloc) ;
- **le plancher de lisibilité** : aucune taille de texte de la section n'est
  écrite sous le plancher `--t-min`, y compris au palier de 640 px ;
- **les deux couleurs viennent de la charte** et un solde négatif change de
  teinte, pas de disposition ;
- **le document annonce le nombre de contrôles du fichier** (31 aujourd'hui) :
  un chiffre écrit à la main dans un document se périme, sauf s'il est vérifié.

### 10 étapes dans le harnais navigateur

Le parcours exécute la section pour de vrai (`tests/navigateur_interface.mjs`,
200 étapes au total) : il compte les 16 lignes rendues, vérifie que **le montant
de la ligne du scénario le plus coûteux est celui que le serveur a calculé**
(« Assemblées souveraines » : −474,0 Md€/an servi, retrouvé dans sa propre
ligne), que **sa barre vaut exactement le rapport servi** (100 % quand il est le
plus fort), que **le scénario de référence est marqué une fois**, que le premier
clic range en croissant (« Deux mandatures consécutives » — 27,6 de risque), le
second en décroissant (« Escalade nucléaire tactique » — 70,4), le troisième rend
l'ordre du catalogue, et qu'un **scénario hostile** (`libelle = "<img src=x
onerror=alert(1)>"`) reste du texte.

### 10 sabotages, 10 attrapés

| Sabotage | Contrôle qui l'attrape |
|---|---|
| le montant affiché arrondi à la main (`toFixed`) | aucune opération sur les valeurs servies |
| le bloc replacé dans la fonction suivante | le bloc est au niveau du script |
| un second `fetch('/api/comparer')` ajouté | la route est appelée une seule fois |
| l'échelle des barres fixée à 100 Md€ | les barres se mesurent sur le plus fort montant servi |
| le libellé du scénario non échappé | chaque fonction de rendu échappe ce qu'elle affiche |
| `aria-sort` retiré du titre | le rangement est annoncé aux lecteurs d'écran |
| le troisième clic qui ne rend pas l'ordre | le rangement a trois états |
| les deux couleurs remplacées par des hexadécimaux | les deux couleurs viennent de la charte |
| la légende qui perd la définition du solde | la légende dit ce que les colonnes mesurent |
| le lien du sommaire retiré | le sommaire y mène |

**Deux contrôles ont dû être durcis, et c'est le plus instructif.** Le premier :
une étape du harnais vérifiait que « le montant affiché est celui que le serveur
a calculé » — mais elle portait sur le **premier** scénario, dont le solde est
nul : elle cherchait « 0,0 » dans un tableau qui en contient partout. Elle était
vraie, et vide de sens. Elle porte maintenant sur le scénario **le plus coûteux**
(« Assemblées souveraines », −474,0 Md€/an), cherche le montant **dans sa propre
ligne**, et vérifie en plus que sa barre vaut le rapport servi — deux assertions
qui ne peuvent pas passer par accident. Le second :

**Un sabotage a d'abord échappé au contrôle.** Le
huitième — remplacer `var(--classe-recettes)` par `#22c55e` — n'a rien cassé :
la vérification cherchait les deux variables **dans la feuille de style
entière**, où elles apparaissent pour d'autres sections. Le contrôle a été
resserré : les variables sont désormais cherchées dans les règles de
`#section-comparaison` seulement. Ce que la campagne de sabotage a attrapé là
n'est pas un défaut de la page, c'est un contrôle qui mesurait à côté — et sans
la campagne, il aurait été compté comme une protection.

---

## 5. Ce qu'un tableau comparatif ne dit pas

- **Il ne dit pas ce qu'il faut choisir.** Classer seize politiques publiques
  sur cinq colonnes est un exercice de lecture, pas un verdict : deux scénarios
  peuvent dégager autant et ne pas répartir la même chose, et aucun des cinq
  chiffres ne mesure la justice du partage. Les 20 domaines notés sont servis
  par la route ; le tableau n'en montre aucun, et c'est un choix assumé — les
  afficher noierait la comparaison.
- **Il ne montre pas le chemin.** Un solde annuel ne dit rien du calendrier, des
  investissements à cycle long ni des effets différés. Le bilan
  intergénérationnel est servi pour chaque scénario ; il n'est pas affiché.
- **Il n'est pas une prévision.** Chaque ligne est une simulation sous les
  hypothèses documentées du modèle, avec le contexte du jour. Changer une donnée
  de contexte déplace les chiffres — c'est précisément pourquoi aucun n'est écrit
  dans la page.
- **Le classement est un rang, pas un écart.** Ranger par risque met côte à côte
  27,6 et 70,4 ; le tableau ne dit pas si 27,6 est acceptable — cette lecture-là
  appartient au lecteur et au débat public.
- **Le tri appartient à qui regarde.** Un lecteur peut ranger par dette et
  croire qu'il a trouvé l'ordre des priorités ; l'ordre du catalogue, lui, ne
  porte aucun jugement.

---

## 6. Reste ouvert

1. **Comparer les réglages du lecteur aux préréglages.** Aujourd'hui la section
   compare le catalogue à lui-même : le lecteur ne peut pas voir où *son* plan
   se place. La route accepte une liste de jeux de paramètres (`comparer()`
   prend `scenarios`), mais le serveur ne l'expose pas en `POST` — c'est un
   chantier d'API, pas de mise en page. Le jour où il existera, la ligne du
   lecteur s'ajoutera au tableau, marquée comme telle.
2. **Trier par plusieurs colonnes** (par exemple : déficit contenu *puis* risque
   faible). Le rangement actuel n'en connaît qu'une : au-delà, la page ferait des
   choix que le lecteur doit faire lui-même.
3. **Afficher les 20 domaines du scénario choisi**, en dépliant une ligne —
   l'écran de détail existe déjà pour la simulation courante ; l'ajouter ici
   demanderait de nommer ce qu'on affiche et pourquoi, comme partout ailleurs.
4. **Mesurer le rendu réel du tableau** dans un vrai navigateur (Performance
   API) : seize lignes, sept cellules et une barre chacune, c'est petit, mais on
   ne le sait que par estimation.
