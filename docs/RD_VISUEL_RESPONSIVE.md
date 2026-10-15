# R&D — Le visuel : lisible partout, compréhensible par tous

**Date : 13 octobre 2026.** Rapport de R&D daté : les chiffres cités sont ceux
du jour de l'audit (ils gardent leur époque).

## La question posée

> « Faire la R&D sur tout ce qui concerne la partie visuelle pour que ce soit
> entièrement responsive et bien organisé afin que n'importe quelle personne
> puisse comprendre en voyant les choses à l'écran ; que ce soit ludique, propre
> et pro. »

Trois exigences distinctes, qu'il faut mesurer séparément :

1. **Responsive** — la page se lit d'un téléphone de 320 px comme d'un écran de
   1920 px, sans zoom, sans défilement horizontal, sans texte illisible.
2. **Organisé** — on sait où l'on est dans une page de vingt sections, et ce
   qu'on y fait.
3. **Compréhensible, ludique, propre, pro** — les chiffres se lisent avant d'être
   interprétés, l'interaction répond, la finition ne trahit pas l'outil.

## Ce que l'audit a trouvé (état du 13 octobre 2026)

Mesures prises sur `simulateur/interface.py` (la page servie par le moteur :
45 841 caractères de CSS, 611 lignes, 453 règles).

| Constat | Mesure | Pourquoi c'est un défaut |
|---|---|---|
| Aucune règle de débordement | `overflow-x` : **0** occurrence ; 17 tableaux dans la page publiée, **2** seulement dans une région défilante | Un tableau large (jusqu'à `min-width:860px`) pousse toute la page : sur un téléphone, la page entière devient glissante |
| Un seul point de rupture | 1 `@media (max-width:640px)` utile (les 5 autres sont `print`, `forced-colors`, `reduced-motion`) | Entre 641 px et 1024 px, aucune règle ne s'applique : c'est le domaine des tablettes |
| Textes trop petits | **56 règles** sous 12 px, jusqu'à **9,6 px** (`—0,6 rem`) | « N'importe quelle personne » n'inclut pas les yeux de 20 ans : en dessous de 12 px, on ne lit plus, on devine |
| Aucune typographie fluide | `clamp()` : **0** occurrence ; 149 tailles figées | La même taille en 360 px et en 1920 px : soit trop petite, soit trop grande |
| Formulaires sous 16 px | `select` à **12,5 px** | Sur iOS, un champ sous 16 px déclenche un zoom automatique : la page bouge toute seule |
| Couleurs en dur | **136** hex et **69** `rgba()` hors `:root`, dont `#7b8aa5` **11 fois** | Une couleur répétée ne suit aucune palette : impossible de la faire évoluer (le site M.R.S.C. surcharge la sienne) |
| Cibles tactiles | Boutons à ~35 px de haut (`padding:8px 13px`, `font-size:.82rem`) | Sous 44 px, on rate son doigt — et on ne sait plus si l'on a cliqué |
| Sommaire non collant | `<nav class="sommaire">` en haut de page, 20 sections en dessous | Passé la première section, on ne sait plus où l'on est ni ce qui reste à voir |

## Les décisions

### 1. Le débordement se traite là où il naît, pas à la fin

`overflow-x:hidden` sur `body` aurait masqué le symptôme en rendant le contenu
inaccessible. Trois règles suffisent :

- `min-width:0` sur les enfants de grille et de `flex` — par défaut, un enfant
  refuse de rétrécir sous la taille de son contenu, et pousse la page ;
- chaque tableau large est posé dans une **région défilante nommée**
  (`.tableau-defilant`, `role="region"`, `tabindex="0"`,
  `aria-label="… — faites défiler horizontalement"`) : le tableau défile, la page
  non ;
- l'enveloppe est posée **en JavaScript, une fois pour toutes** — y compris sur
  les tableaux que le moteur crée après coup (strates, audit, bourse, nuances) —
  et jamais sur ceux qui défilent déjà.

### 2. La lisibilité a un plancher, pas un plafond

Une échelle fluide pour ce qui doit grandir (`clamp()` sur les titres et les
chiffres-clés) et un **plancher** pour ce qui doit rester lisible :
`font-size:max(var(--t-min), …)` sur les 56 tailles trop petites, avec
`--t-min:12,5 px`. Le plancher s'écrit en dur une fois, puis se lit partout.

Pourquoi `max()` et non un simple agrandissement : les réglages de texte du site
(100 %, 125 %, 150 %) agrandissent les `rem`. Un plancher en `px` seul casserait
l'agrandissement ; `max()` garde les deux propriétés — jamais moins de 12,5 px,
et toujours plus grand quand l'utilisateur demande plus grand.

### 3. Quatre paliers, et des grilles qui n'en ont pas besoin

`480 px` (téléphone), `640 px` (grand téléphone), `900 px` (tablette),
`1200 px` (portable). Là où c'est possible, on préfère `auto-fit` +
`minmax(min(100%, Xpx), 1fr)` : la grille s'ajuste seule, sans palier — le palier
ne sert qu'à ce que l'`auto-fit` ne sait pas faire (ordre de lecture, densité,
affichage ou masquage d'un élément).

### 4. Le tactile et les formulaires se déclarent

`@media (pointer:coarse)` : cibles de 44 px minimum, champs à 16 px minimum
(fin du zoom intempestif d'iOS), curseurs plus faciles à saisir. La souris garde
sa densité : la page ne s'alourdit pas pour tout le monde.

### 5. Une couleur se déclare une fois

Les teintes en dur passent en variables de thème (`--panel-3`, `--texte-dim`),
comme les couleurs de classe l'avaient déjà fait. Le site M.R.S.C., qui
surcharge la palette, suit alors sans réécriture.

## Deuxième incrément — l'organisation et la compréhension

Le socle rend la page lisible ; il ne dit pas encore **où l'on est ni ce
qu'on vient chercher**. Deux ajouts, sans déplacer une seule section (les
ancres, les identifiants et l'ordre du document restent ceux du moteur) :

- **Un résumé de tête** (« 🧾 Votre plan en un coup d'œil ») juste après
  l'en-tête : le solde du plan, ce qui entre, ce qui sort, l'ordre de grandeur
  par ménage, et **la phrase du verdict reprise mot pour mot de la balance**.
  Le bandeau ne calcule rien : `renderResume()` est appelé par
  `renderBalance()`, avec les mêmes fonctions (`classeAnneeAffichee`,
  `fmtSigne`, `fmtMenage`, `statutDiviseur`). Deux affichages, un seul calcul —
  c'est la seule façon d'être sûr qu'ils ne finiront pas par se contredire.
- **Quatre chapitres** dans le déroulé — *Comprendre*, *Mesurer*, *Régler*,
  *Vérifier* — qui découpent la vingtaine de sections en quatre temps, chacun
  avec sa phrase d'entrée.

Les mouvements restent discrets : les cartes se soulèvent légèrement, les
barres de la cascade et les jauges de la balance glissent au lieu de sauter,
et `prefers-reduced-motion` coupe tout.

## Troisième incrément — la deuxième passe : ce qui restait

Le socle et l'organisation ont tenu ; une seconde mesure a trouvé cinq défauts
de plus, aucun visible sur un grand écran.

| Constat | Mesure | Conséquence |
|---|---|---|
| L'impression coupait le contenu | `.defilable` et `.tableau-strate` à **430 px**, `.journal` à 260, `.provenance` à 210, `.bourse-table` à 520, tous en `overflow:auto` | Sur papier, un tableau de 1 200 lignes en imprimait onze — sans le dire |
| Le graphique se déformait | `<svg viewBox="0 0 900 210" preserveAspectRatio="none">` dans un bloc `width:100%` | À 350 px de large, 900 unités écrasées : libellés illisibles ; et aucun nom, donc rien pour un lecteur d'écran |
| Les aides n'existaient qu'au survol | **27** des 58 annotations `data-aide` sont portées par des éléments non focalisables | Au doigt, pas de survol : l'explication restait inaccessible |
| La tablette était mal servie | deux panneaux de 330 px dans 700 px de large | Colonnes étriquées, alors que le palier 900 px existait déjà pour d'autres blocs |
| Les écrans de 320-480 px | quatre chiffres dans quatre colonnes d'environ 132 px | « +49,1 Md€/an » ne tenait pas dans sa colonne |

Décisions :

- **Impression, troisième bloc `@media print`** : les plafonds de hauteur
  tombent (`max-height:none;overflow:visible`), les barres collantes
  redeviennent statiques, les fonds sombres passent en blanc, et une ligne de
  tableau ne se coupe plus en deux. À l'écran, rien ne change.
- **Le graphique a sa région** : `.graphique` défile horizontalement et le
  dessin garde 640 px de large minimum — il perd son étirement sur grand écran,
  garde son échelle sur petit. Il reçoit `role="img"` et un nom : il existe
  enfin pour un lecteur d'écran.
- **Les aides au doigt** : `rendreAidesFocalisables()` rend focalisables les
  seuls éléments annotés qui ne sont ni un bouton, ni un lien, ni un champ —
  **et seulement sur appareil tactile** (`pointer:coarse`), pour ne pas ajouter
  vingt-sept arrêts de tabulation à un clavier d'ordinateur. Le second passage
  ne fait rien.
- **Tablette** : un seul panneau large dans la console au-dessous de 900 px, et
  les sept onglets de strate défilent au lieu de s'écraser.
- **Très petits écrans** : deux colonnes, valeur du résumé ramenée à 1,2 rem.
- **Finitions** : `overflow-wrap:break-word` sur le corps (un mot long ne
  déborde plus), sommaire ouvert plafonné à 46 % de la hauteur visible, et
  `prefers-contrast:more` honoré (bordures et textes secondaires renforcés).

## Quatrième incrément — imprimer son plan, et les restes de l'empilement

Le troisième incrément avait rendu l'impression **complète** : vingt-quatre
sections, toutes entières, sur du papier. Complet n'est pas utile. Une mesure de
plus a trouvé quatre défauts.

| Constat | Mesure | Conséquence |
|---|---|---|
| Aucune commande d'impression | `window.print` appelé **0** fois dans la page | Pour ne sortir que son plan, il fallait imprimer les vingt-quatre sections et trier à la main |
| Les plans d'empilement écrits en clair | **7** règles portaient `z-index:56`, `60`, `80`, `120`, `200` | Savoir ce qui passe devant quoi demandait de relire les sept règles ; une couche nouvelle ne pouvait que deviner sa place |
| La page ignorait les encoches | `env(safe-area-inset-*)` : **0** usage | La marge de 18 px tombait sous la barre d'état en portrait, sous l'encoche en paysage |
| Dix sections basses mises en page d'avance | `content-visibility` : **0** usage | Le navigateur calculait la mise en page de l'audit, des matrices et du journal avant qu'on s'en approche |

Décisions :

- **Un mode, pas une capture** : « 🖨️ Imprimer mon plan » (dans les actions du
  résumé) pose `html.impression-plan` — la page ne montre plus que le résumé,
  **donc on voit ce qui s'imprimera** — et le bandeau qui l'annonce propose de
  lancer l'impression ou de revenir à la page entière. Sur papier, il ne reste
  que le résumé et le crédit du mouvement ; la ligne d'attribution
  (`thejmimiia-code.github.io/MRSC/simulateur.html`) s'imprime avec, pour
  qu'une feuille détachée dise d'où elle vient.
- **Aucun pari sur le moment où le navigateur rend la main** : `window.print()`
  est bloquant chez certains navigateurs, asynchrone chez d'autres. La classe
  reste donc posée après l'appel, et c'est le bandeau — pas un minuteur — qui
  ramène la page entière. Le focus revient sur le bouton déclencheur, jamais
  dans une barre qui vient de disparaître.
- **Une seule échelle de plans** : huit variables `--z-…` déclarées dans `:root`,
  du fond (`--z-fond:0`) à la modale (`--z-modale:200`), avec la place réservée
  au bandeau (`--z-bandeau:160`). Aucun `z-index` numérique ne subsiste dans une
  règle, et un test vérifie que tout `var(--z-…)` employé est déclaré : une
  faute de frappe passerait sinon pour un plan nul, sans le moindre signal.
- **Les encoches** : la marge du corps passe par
  `max(18px,env(safe-area-inset-…))` sur les quatre bords, avec valeur de repli
  (`env(…,0px)`) — sans elle, toute la déclaration serait ignorée en bloc. La
  marge d'origine reste écrite avant, pour les navigateurs qui ne connaissent
  pas `env()`. Le lien d'évitement suit (`top`, `left`).
- **Rendu différé** : dix sections basses portent `content-visibility:auto` et
  `contain-intrinsic-size:auto 620px` (une hauteur de remplacement, sans quoi la
  barre de défilement sauterait à chaque section atteinte). Rien n'est retiré du
  document : les ancres, la recherche dans la page et l'impression trouvent
  tout — et l'impression lève explicitement le différé
  (`section.bloc{content-visibility:visible}`).
- **Finitions typographiques** : `text-wrap:balance` sur les titres,
  `text-wrap:pretty` sur les paragraphes, et la modale qui suit la hauteur
  réellement visible (`max-height:74vh;max-height:74dvh`) — sur un téléphone,
  `vh` compte la barre d'adresse, `dvh` non.

## Cinquième incrément — le plan se voit, et une couleur qui n'existait pas

Deux manques, trouvés à la lecture du thème plutôt qu'à l'écran.

| Constat | Mesure | Conséquence |
|---|---|---|
| Les montants sans leur proportion | le résumé de tête donnait quatre nombres ; la balance, quinze sections plus bas, était le seul endroit où l'on voyait les deux plateaux se répondre | Pour savoir si le plan pèse plutôt sur les recettes ou sur les dépenses, il fallait descendre |
| `--panel-3:var(--panel-3)` | la variable se définissait **elle-même** : invalide au calcul, donc transparente, sans erreur ni message | Le survol des cartes de scénario ne changeait rien et les pistes de jauge n'avaient pas de fond — deux défauts invisibles à la lecture comme à l'écran |

Décisions :

- **Une barre par plateau, au sommet** : `#resume-balance` montre la part de
  chaque plateau dans le total des deux, juste après les montants et avant les
  boutons. La couleur ne porte rien seule : chaque côté a son mot (« Recettes +
  économies », « Dépenses engagées »), sa part écrite en clair (`87 %`) et son
  motif — hachures pour l'un, pointillés pour l'autre.
- **Une seule fonction pour les deux visuels** : `partsDesPlateaux(annee)`
  calcule les parts une fois, et la balance comme le résumé la lisent — la règle
  du résumé reste qu'il ne calcule rien lui-même. Les deux parts somment
  toujours à 100 : la seconde est le complément de la première, jamais un
  arrondi séparé qui donnerait 99 ou 101.
- **Sans simulation, rien à moitié rempli** : le retour « aucune année » remet
  les deux barres à zéro et les parts à `—`.
- **Le mouvement s'arrête avec les autres** : la transition des barres est
  coupée par `prefers-reduced-motion`, et sur papier elles gardent leur
  remplissage (`print-color-adjust:exact`) — les parts étant écrites en clair,
  l'information survit même si le navigateur refuse d'imprimer les fonds.
- **La variable réparée** : `--panel-3` reçoit une vraie valeur, et un test
  refuse désormais toute propriété personnalisée qui se définirait elle-même.
  C'est le genre de faute qui ne se voit pas : aucune erreur, aucune alerte —
  simplement une couleur qui n'arrive jamais.

## Sixième incrément — le repère du sommaire dit où l'on est, pas où l'on a cliqué

Constat : le sommaire collant surlignait la dernière entrée **cliquée**. La page
compte désormais vingt-quatre sections : dès qu'on fait défiler sans cliquer, le
repère indiquait un endroit où l'on n'était plus.

| Constat | Mesure | Conséquence |
|---|---|---|
| Le repère suit le clic, pas la lecture | `.sommaire a.actif` n'était posée que par `onclick` | en défilant, le sommaire désignait une section quittée depuis longtemps |
| La marque n'existait qu'en couleur | aucune annonce d'état | la position courante n'existait pas pour un lecteur d'écran |
| Dans une région défilante, la ligne perdait son nom | la première colonne glissait avec le reste | au bout de trois colonnes glissées, on ne sait plus quelle ligne on lit |

Décisions :

- **Un seul endroit pose la marque** : `marquerLecture(identifiant)` — le clic
  (`marquerSommaire`) et l'observateur de défilement l'appellent tous les deux,
  donc le sommaire ne peut plus dire deux choses à la fois. Un identifiant
  inconnu **efface** la marque au lieu de la laisser sur l'entrée précédente.
- **La marque est annoncée** : `aria-current="location"` accompagne la classe
  `.actif`. Un repère qui n'existe qu'en couleur n'existe pas pour tout le monde.
- **L'observateur** (`observerLecture`) suit les sections repères
  (`section.bloc[id]`) avec `rootMargin:'0px 0px -70% 0px'` : la section lue est
  celle dont le haut est le plus proche du haut de la fenêtre, ce qui donne une
  marque stable quand deux sections se disputent l'écran.
- **La première colonne reste en place** : dans une région défilante, la
  première cellule colle à gauche (`position:sticky;left:0`) avec un fond plein
  — sans lui, le texte passerait dessous — et une ombre discrète qui dit qu'il y
  a de la suite. Sur papier, la colonne reprend sa place (`position:static`).

Deux doublures de test ont été corrigées au passage : `classList.toggle(classe,
force)` **ajoutait** la classe quand `force` valait `false`. Le contrôle « une
seule entrée marquée » passait donc sur une doublure infidèle — le genre de vert
qui ne prouve rien.

## Septième incrément — le tableau devient une carte sur un téléphone

Constat : les tableaux de la page sont tous écrits par le script, et plusieurs
portent six à neuf colonnes (`min-width` de 600 px pour les strates, 860 px pour
la bourse). Dans 360 px, on fait glisser la ligne sous ses yeux, et l'en-tête a
disparu depuis longtemps.

| Constat | Mesure | Conséquence |
|---|---|---|
| Neuf colonnes dans 360 px | `.tableau-strate table{min-width:600px}`, `.bourse-table table{min-width:860px}` | une ligne à la fois, sans son en-tête : on lit des nombres sans savoir ce qu'ils sont |
| Aucun libellé de colonne dans les cellules | aucun `data-label` dans la page ; les dix-sept tableaux naissent du script | étiqueter à la main demandait de toucher dix-sept gabarits — et le rendu suivant effaçait tout |
| Le tableau est réécrit à chaque frappe | l'observateur de la page réenveloppe les tableaux à chaque vague de rendu | un étiquetage posé une seule fois au chargement ne survivrait pas |

Décisions :

- **Le libellé se déduit, il ne s'écrit pas deux fois** : `tableauEnCartes(tableau)`
  lit la ligne d'en-tête et pose `data-label` sur chaque cellule ; en CSS,
  `tr>*::before{content:attr(data-label)}` l'affiche sous 640 px. Personne ne
  maintient une seconde liste de noms de colonnes.
- **La ligne devient une carte, la première cellule devient le titre** : sa
  colonne est déjà écrite par la ligne elle-même, son libellé serait redondant
  (`::before{content:none}`).
- **L'en-tête quitte l'écran sans quitter le document** : la ligne d'en-tête est
  réduite à un pixel (`clip-path:inset(50%)`), jamais `display:none` — elle
  reste pour les lecteurs d'écran, et l'impression retrouve un tableau normal,
  toute la bascule étant enfermée dans `@media screen`.
- **Les régions qui ne défilaient que pour la largeur rendent la place** :
  `.tableau-strate`, `.bourse-table`, `.tableau-defilant` et `.defilable`
  passent en `overflow:visible;max-height:none` **quand** ils contiennent un
  tableau en cartes (`:has(.tableau-cartes)`).
- **La bascule vaut aussi pour les tableaux déjà défilants** : c'est justement
  là qu'il y a le plus de colonnes (strates, bourse, audit, modales). La
  première colonne y colle à gauche, et ne colle plus dès que la carte prend la
  place (`position:static`).
- **Tout ou rien, et ça se répare** : le tableau entier est vérifié **avant** la
  première écriture. Deux lignes d'en-tête, une seule colonne, ou une cellule
  qui fusionne des colonnes (`colspan`, `rowspan`) : il n'est pas étiqueté du
  tout — et s'il l'était déjà, il **rend sa marque** et redevient un tableau qui
  défile. Le passage reprend à chaque vague de rendu, donc un gabarit qui
  remplace sa cellule « en chargement… » par de vraies valeurs redevient
  étiquetable tout seul. Un tableau peut aussi refuser la bascule :
  `data-cartes="non"`.
- **La spécificité compte** : `.bourse-table table{min-width:860px}` (une classe,
  un type) battait `.tableau-cartes{min-width:0}` (une classe seule). C'est
  `table.tableau-cartes` qui tranche — sans quoi les tableaux les plus larges
  auraient débordé de leur propre carte.
- **On n'écrit pas deux fois la même étiquette** : le passage ayant lieu à
  chaque rendu, une cellule qui porte déjà le bon `data-label` est laissée
  tranquille.

## Huitième incrément — ce que le navigateur décidait à sa façon

Trois détails ne se voyaient pas dans le CSS : ils se décidaient ailleurs, dans
le navigateur, sans que la page ait son mot à dire.

| Constat | Mesure | Conséquence |
|---|---|---|
| Une page sombre sans mot sur elle-même | aucun `color-scheme` | barres de défilement, curseurs, cases et menus natifs restés clairs sur fond sombre, et un fond blanc derrière le doigt qui tire la page |
| Le texte redimensionné par le navigateur | aucun `text-size-adjust` | sur iOS, le texte regrossit seul quand on tourne le téléphone : le plancher de lisibilité ne veut plus dire grand-chose |
| Le geste qui traverse les surfaces | aucun `overscroll-behavior` | arrivé au bout d'un tableau ou d'une modale, le doigt entraînait la page derrière — et sur Android, tirait le rechargement |

Décisions :

- **`color-scheme:dark`, une fois pour toutes** : déclaré dans `:root`. La page
  ne suit pas le réglage du système — la palette M.R.S.C. est la seule — et un
  test refuse l'arrivée de `prefers-color-scheme`, qui ferait deux thèmes à
  maintenir.
- **`text-size-adjust:100%` sur `html`** : c'est le document qui fixe la taille
  du texte. Et le zoom reste libre : ni `user-scalable=no`, ni `maximum-scale=1`
  — un test le vérifie, parce que c'est la première chose qu'un gabarit recopie.
- **Le geste s'arrête au bord** : les douze surfaces qui défilent —
  `.defilable`, `.journal`, `.provenance`, `.tableau-strate`, `.bourse-table`,
  `.overlay`, `.modale-corps`, `.graphique`, `.tableau-defilant`, `.sommaire`,
  `.sommaire-liste`, `.onglets-strates` — portent `overscroll-behavior:contain`.
  Le contrôle fait le tour du CSS : **toute** règle qui déclare un
  `overflow:auto` ou `scroll` doit figurer dans cette liste. C'est ainsi que
  `.overlay` — la feuille de modale, oubliée par l'inventaire à la main — a été
  rattrapée : un premier jet qui range `.modale-fond`, une classe qui n'existe
  pas, ne prouve rien.

## Neuvième incrément — une seule barre collante, et une veille qui reste au courant

Signalé depuis un téléphone, et vérifiable dans la feuille : **deux barres se
disputaient le haut de l'écran**.

| Constat | Mesure | Conséquence |
|---|---|---|
| Deux barres collantes, au même endroit | `.sommaire{position:sticky;top:0}` **et** `.ruban-veille{position:sticky;top:0}` — le ruban ne recevait `top:var(--collant)` qu'au-dessus de 641 px, et le sommaire est collant à toutes les largeurs | sur un téléphone, le ruban passait **par-dessus** le sommaire (z-index 60 contre 56) : le menu disparaissait sous la veille |
| La hauteur de la barre était **écrite à la main** | `--collant:50px` au large et `44px` en petit écran, pour une barre qui en fait 44 et 58 | les ancres atterrissaient sous la barre (le titre de la section visée restait caché), et le ruban se collait 6 px trop bas : par la fente, on voyait défiler la page |
| Le ruban, une fois qu'il n'est plus collant, se lit mal | titre, verdict tronqué à une ligne, cinq strates, population, coût et quatre boutons dans une même rangée | en fenêtre comprimée, la rangée se replie en un bloc confus ; en téléphone, les boutons s'empilent de travers |

Décisions :

- **Une seule barre collante sous 901 px** : c'est le sommaire, qui porte la
  navigation. Le ruban reprend sa place dans le flux, en carte lisible. Il n'y a
  donc plus deux choses à faire tenir dans la même bande de 44 px.
- **La veille ne perd pas la parole** : une pastille dans la barre
  (`#sommaire-veille`) écrit le niveau en trois mots — « vigilance · 3
  alerte(s) » —, colorée **et** écrite, et qui mène d'un geste au détail des
  seuils. Son texte vient de `classeNiveau` et `etiquetteNiveau`, les mêmes
  fonctions que le ruban : les deux ne peuvent pas raconter deux choses
  différentes. Avant le premier diagnostic, l'attribut `hidden` la tient hors de
  l'écran comme du clavier ; un diagnostic qui disparaît l'efface au lieu de
  laisser un verdict périmé.
- **Un bouton, pas un lien** : la pastille n'entre pas dans le mécanisme de
  marque du sommaire (`marquerLecture` suit `.sommaire a`) — sans quoi la
  position de lecture aurait marqué la veille à la place de la section lue.
- **La hauteur de la barre se mesure** : `mesurerCollant()` écrit la hauteur
  réelle dans `--collant`, et `surveillerCollant()` la remesure à chaque
  changement — ouverture du sommaire, rotation, zoom du texte. La même variable
  sert au décalage des ancres (`scroll-margin-top`) et à la colle du ruban :
  les deux barres se touchent exactement, sans fente ni recouvrement. Le repli
  du CSS dit maintenant la vérité (44 px et 58 px) pour les navigateurs sans
  JavaScript, et une barre non mesurable — absente, masquée — n'écrase rien.
- **Le ruban devient une carte sur un téléphone** : titre d'abord, verdict en
  clair sur toute la largeur (il n'a plus à être tronqué, c'est lui qui porte le
  message), puis les quatre commandes en deux colonnes égales, chacune assez
  haute pour le doigt.
- **La pastille ne s'imprime pas** : la barre du téléphone n'a rien à faire sur
  une feuille, où le ruban dit déjà tout.

## Dixième incrément — le nom de la région suit la taille de l'écran

Le défaut était écrit noir sur blanc dans les limites assumées de ce rapport :
sous 640 px, un tableau devient une pile de cartes, `overflow` repasse à
`visible` — et la région continuait pourtant d'annoncer « faites défiler
horizontalement ». Deux choses fausses à la fois :

* une personne qui suit l'annonce du lecteur d'écran cherche un défilement qui
  n'existe pas : au mieux elle perd son temps, au pire elle croit la page
  cassée ;
* `tabindex="0"` restait posé sur une région qui ne défile plus : un arrêt de
  tabulation qui ne mène nulle part. C'est le défaut des « vingt-sept arrêts »
  évités sur ordinateur, mais au doigt — sur une tablette à clavier, on y passe
  et rien ne s'y passe.

### Ce qui change

`nommerRegionsTableaux()` réécrit le nom **et** l'arrêt à partir de la légende
rangée sur la région (`data-legende`), dans les deux sens :

| Palier | Nom | Arrêt de tabulation |
| --- | --- | --- |
| Plus de 640 px | « … — faites défiler horizontalement » | `tabindex="0"`, parce qu'on y fait défiler aux flèches |
| 640 px ou moins, tableau étiquetable | « … — présenté en cartes, une ligne à la fois » | retiré : il n'y a plus rien à faire défiler |
| 640 px ou moins, tableau **fusionné** | « … — faites défiler horizontalement » | conservé : celui-là défile vraiment |

Trois décisions de détail, qui sont chacune un piège évité :

1. **La question posée est celle du CSS**, mot pour mot :
   `window.matchMedia('screen and (max-width:640px)')`. C'est le CSS qui bascule
   en cartes ; deux façons de poser la même question finiraient par donner deux
   réponses, et le nom se remettrait à mentir sans qu'aucune porte ne le voie.
2. **La bascule se décide tableau par tableau** : un tableau dont une cellule
   fusionne des colonnes garde le défilement, donc son étiquette et son arrêt.
3. **Le nom se réécrit, il ne s'ajoute pas** : le suffixe est recalculé à partir
   de la légende rangée sur la région. Sans cela, chaque vague de rendu aurait
   empilé un suffixe de plus — le contrôle serre cela de près (un seul
   « cartes », zéro « défiler », sur les deux états).

Le renommage ne dépend pas d'un rendu : `suivrePliDeLEcran()` écoute le pli de
la fenêtre (replié à 120 ms, comme le reste de la page). Un pli n'est pas un
rendu, et une rotation de téléphone n'attend pas qu'un tableau soit réécrit.

### Ce que le contrôle a demandé, et pourquoi ce n'est pas un détail

Le fragment JavaScript est **exécuté** sur le DOM minimal avec une fenêtre
simulée : large, étroite, puis élargie, plus un pli de fenêtre réel (deux
événements coup sur coup, pour éprouver le repli) et une fenêtre sans écouteur.
Quatre sabotages ont été posés puis retirés pour vérifier que ces contrôles
mordent :

| Sabotage | Attrapé par |
| --- | --- |
| Le nom reste celui du défilement | `test_sur_un_telephone_la_phrase_dit_les_cartes` (et le pli de fenêtre) |
| L'arrêt de tabulation n'est jamais retiré | `test_sur_un_telephone_l_arret_de_tabulation_disparait` |
| Le pli de fenêtre n'est plus écouté | `test_un_pli_de_fenetre_renomme_sans_attendre_un_rendu` |
| Le nom s'empile au lieu de se réécrire | `test_le_nom_ne_s_empile_pas_d_une_vague_a_l_autre` (9 échecs) |

---

## Onzième incrément — les contre-pouvoirs en chiffres

Le registre des contre-pouvoirs et celui du temps des procédures n'avaient aucun
écran. Ils en ont un : deux blocs dans une section neuve, juste après les
verrous, dont voici ce qui relève de l'affichage — le contenu et le contrôle
sont décrits dans [`RD_CONTREPOUVOIRS_EN_PAGE.md`](RD_CONTREPOUVOIRS_EN_PAGE.md).

- **Une barre de sièges par chambre, une part par formation.** La largeur est
  une proportion (`width:…%`), la teinte est **calculée** par rang
  (`hsl(var(--teinte) 58% 52%)`, `--teinte` posée en style en ligne) : douze
  groupes se distinguent sans qu'aucune couleur ne soit écrite à la main. Une
  palette recopiée aurait survécu à trois remaniements sans être relue.
- **Les seuils de la chambre en pastilles**, les manœuvres en dépliants
  (`<details>`) : la section fait deux mille signes de haut, pas douze. Un
  lecteur qui cherche une manœuvre ouvre la sienne ; les autres restent des
  titres.
- **Les filtres sont des boutons pressables**, avec `aria-pressed` : l'état d'un
  filtre ne se lit pas seulement à la couleur. Même règle pour les formations
  cochées — la coalition se compose au clavier comme à la souris.
- **Les nombres sont tous tabulaires** (`ui-monospace`, `font-variant-numeric` là
  où la page en a déjà) : des colonnes de sièges et de jours ne dansent pas d'une
  ligne à l'autre.
- **Le plancher de lisibilité s'applique comme ailleurs** : tout ce qui descend
  sous 12,5 px passe par `max(var(--t-min), …)`, comme le reste de la page — et
  pour les réglages d'agrandissement du site (125 %, 150 %), ces `rem` suivent.
- **Un palier de 640 px pour la section** : les deux chambres se rangent l'une
  sous l'autre (`grid-template-columns:1fr`), la barre de sièges s'amincit de
  16 à 12 px, et les résumés de dépliants reprennent la taille du corps.
- **Ce qui n'a pas été touché** : la palette M.R.S.C, les quatre paliers du
  socle, la densité des tableaux d'audit. Une section neuve se range dans les
  règles existantes ; elle n'en invente pas.

## Douzième incrément — quatre thèmes, une ligne éditoriale, un écran de poche

La passe du 14 octobre 2026 ne touche pas au contenu : elle change **ce qui se
passe entre le serveur et l'œil**. Le détail complet — relevé de la charte
M.R.S.C., choix des palettes, contrastes mesurés, coût en octets et limites —
est dans [`RD_AFFICHAGE_THEMES_ET_MOBILE.md`](RD_AFFICHAGE_THEMES_ET_MOBILE.md).
Ce qui relève de l'affichage, ici :

- **Quatre thèmes** (`soir`, `jour`, `crème`, `contraste renforcé`), **47 jetons
  aux mêmes noms** dans chacun, `color-scheme` déclaré par thème. Le choix du
  visiteur est posé sur `<html>` **avant le premier pixel** par un script
  d'en-tête, gardé dans `localStorage`, et n'est jamais envoyé au serveur.
- **Le défaut est le réglage de l'appareil** — et `prefers-color-scheme`
  n'apparaît **pas** dans la feuille : une media query CSS aurait écrasé le choix
  explicite du visiteur. Un contrôle refuse son retour dans le CSS.
- **La ligne éditoriale empruntée au site M.R.S.C.** : vingt-quatre sections en
  trois temps — un sur-titre en majuscules précédé du **trait vert de 25 × 3 px**
  de la charte, un titre, puis une phrase. L'explication a quitté les titres.
- **L'échelle d'espacement est branchée** : `--e-1…--e-6` et ses dérivés
  (`--pad-bloc`, `--ecart-section`, `--ecart-carte`) commandent les sections et
  les cartes ; la densité « Compact » ne fait que changer ces trois jetons.
- **La largeur de lecture est bornée** : conteneur ramené à 1440 px, phrases
  d'introduction limitées à `--mesure` (74 caractères) — les tableaux larges
  gardent leur défilement plutôt que d'imposer une page étroite.
- **Le panneau « Affichage » se replie en feuille** sous 640 px : fixé en bas,
  défilement qui retient son geste, cibles de 44 px, hauteur bornée.
- **Cinq tailles de texte** (87 → 137 %) agrandissent les `rem` sans jamais
  toucher au plancher, qui reste en pixels : agrandir ne peut pas créer un texte
  illisible.

Deux erreurs d'affichage trouvées par la mesure, pas par l'œil : l'encre blanche
figée sur la strate hors-sol (**3,76:1** en « soir », **2,02:1** en
« contraste ») et le texte de l'onglet actif sur son dégradé de marque
(**1,06:1** en « contraste »). Deux jetons neufs les réparent — `--encre-pleine`
et `--sur-mrsc`.

## Treizième incrément — l'encre qui manquait, et le cadre qui se resserre

Le douzième incrément avait réparé ce que la mesure des **règles** pouvait voir.
Il restait ce qu'elle ne pouvait pas voir : un élément qui **peint un fond** et
laisse l'encre venir de son parent. Le visiteur l'a signalé avant les contrôles —
« certains thèmes n'apparaissent pas correctement, les couleurs des boutons ne
sont pas adaptées par rapport au fond ».

### Ce qui était cassé, et pourquoi aucun contrôle ne le voyait

En « jour » et « crème », le bandeau peignait le dégradé de marque
(`--mrsc-navy` → `--entete-2`) et le titre, la phrase d'accroche, les boutons
« Simuler », « Rafraîchir », « Réinitialiser », « Régler les leviers » et les
quatre numéros de chapitre **héritaient** l'encre sombre du thème : **1,27:1**
pour les boutons et le titre, **1,64:1** pour l'accroche. Onze textes illisibles
par thème clair, invisibles pour les trente-six contrôles de règles — chacun
mesure une règle seule, avec ses propres couleurs.

### L'instrument

`outils/contraste_ecran.py` (neuf) fait ce qu'un navigateur fait, en plus petit :
il lit la page servie, en dresse l'arbre, applique la feuille (cascade,
spécificité, héritage des jetons, `var()`, `color-mix()`, `@media` selon la
largeur), compose les fonds réellement peints (dégradés, transparences,
`opacity`) et compare chaque texte à son fond réel. Il **compte ce qu'il
écarte** — règles d'état, commandes inactives — au lieu de le taire.

### Le cadre

Le bandeau portait quinze commandes de premier niveau ; il en porte quatre, et
les six outils secondaires s'ouvrent dans un tiroir. Le tour du bandeau passe de
18 px à 14, la marge sous le bloc de 14 px à 9, l'écart entre la barre et la
ligne d'état de 9 px à 5. Les trois barres de la page (bandeau, ruban de veille,
actions du plan) partagent la même hauteur de bouton et le même écart — deux
jetons, `--h-bouton` (34 px, 44 px sur écran tactile) et `--gap-barre`.

### La présentation

Trois largeurs, comme la « mise en page » du site M.R.S.C. : **Équilibrée**
(1440 px, le défaut), **Lecture** (1000 px), **Panorama** (1680 px). Le choix vit
sur `<html data-layout="…">`, posé avant le premier pixel, gardé sur l'appareil.
Un seul jeton change (`--largeur-page`) : les grilles suivent d'elles-mêmes, et
les quatre paliers d'écran restent la loi — une présentation ne remplace pas la
mise en page responsive, elle la borne.

### Ce que ça change pour les paliers

Rien n'est cassé aux quatre paliers : les contrôles de contraste tournent à
1280 px et à 380 px, dans les quatre thèmes, et les huit combinaisons sont
vertes. Le pire cas mesuré est **4,58:1** (« soir »), **4,62:1** (« jour »),
**4,76:1** (« crème »), **8,16:1** (« contraste »).

## Quatorzième incrément — l'aide qui cachait le panneau, et l'état qu'on ne mesurait pas

Deux défauts signalés le même jour, liés par la même cause : l'outil regardait
une chose, le visiteur en vivait une autre.

### La bulle qui recouvrait ses propres boutons

Le panneau « Affichage » s'ouvrait sous une bulle qui ne partait pas : l'aide
était accrochée au tiroir entier, le gestionnaire de sortie ne la cachait pas
tant que le pointeur restait dans le porteur, et son placement de repli la
posait **sur** le panneau. Corrigé par une règle : l'aide explique un contenant,
elle cède devant toute commande qu'il renferme, et s'efface dès que le contenant
est ouvert. Trois placements sont possibles (sous, dessus, bas de l'écran), et
aucun ne recouvre la commande expliquée. Neuf étapes du harnais jouent la souris
et le clavier ; le sabotage du repérage d'avant les fait échouer.

### L'état, angle mort du contraste

Le contraste était mesuré **au repos**, et l'outil disait écarter les états.
C'est exactement là qu'un visiteur passe son temps : survol, focus, clic,
bascule. Il mesure maintenant 19 passes par page et par largeur, dont « tout
enfoncé » (19 bascules forcées) — 587 textes mesurés, 0 faute dans les quatre
thèmes, aux deux largeurs. Sur un écran de poche, 551 textes.

### Le cadre large

Le bandeau passe en deux colonnes au large : le texte à gauche (sur-titre,
titre, phrase), les quatre commandes à droite, la ligne d'état en dessous. Le
seuil, d'abord posé à 900 px, est relevé à 1200 px par la mesure du quinzième
incrément — à 900 px, un plafond de 46 % cassait les commandes en trois rangées. La hauteur du cadre devient celle de son contenu, au lieu d'être la
somme de son texte et d'une rangée de boutons. Le sommaire des accès rapides se
règle sur les jetons d'espacement, comme les trois barres.

## Quinzième incrément — le plan coté, et deux mesures fausses

Le visiteur l'avait dit en une phrase : « le cadre avec les boutons d'accès
rapide est beaucoup plus grand que la place que prennent les boutons eux-mêmes ».
L'outil de captures savait photographier la page et additionner des hauteurs ; il
ne savait pas dire **où**. Il publie désormais le **plan coté de chaque cadre** :
pour chaque enfant peint, sa position et sa taille relatives au cadre. C'est ce
plan qui a répondu, et la réponse était plus précise que l'impression.

### Ce que le plan a montré, à 1280 px

| Ce qui occupe le bandeau | Avant | Après |
|---|---:|---:|
| la colonne de texte | 528 px | 571 px |
| le titre | 3 lignes (89 px) | 2 lignes (59 px), sur toute la largeur |
| la barre de commandes | 651 × 35 px | 651 × 35 px |
| le vide sous la barre | 139 px | 0 |
| la ligne d'état | 1201 × 69 px | 589 × 101 px, sous les commandes |
| **le cadre** | **296 px** | **248 px** |

Rien n'a été retiré : le titre a gagné la largeur de la page, et la rangée qui
restait vide sous les quatre commandes porte maintenant la ligne d'état — ce
qu'un cadre doit faire de sa place, la donner à son contenu. Sous 641 px, le
rembourrage du bandeau suit l'écran (`clamp(9px, 1.6vw, 22px)`) : une seule
règle, là où deux se contredisaient — la mesure avait montré 14 px de marge
intérieure à 380 px pour 35 px de boutons, parce que la règle du grand écran,
écrite plus bas, l'emportait.

### Le sommaire : 290 px de cadre pour 25 px de pastilles

Le même plan coté a rendu un second verdict, plus embarrassant : la liste du
sommaire faisait **290 px de haut** — dix-huit pastilles de 25 px centrées
verticalement dans du vide — et le sommaire est **collant**. La feuille de style
n'a rien à se reprocher : le balisage du lien « Objections » était cassé, son
attribut `data-aide` avalait le balisage des deux liens suivants, et les
**217 caractères** de son texte retombaient **en nœud de texte** dans la liste,
où ils se repliaient en paragraphe. Un enfant flex anonyme : il n'est pas dans
`children`, donc le plan ne le voyait pas, et le navigateur le peignait
sagement au milieu des pastilles.

Trois conséquences, toutes réparées : un paragraphe fantôme dans la barre, un
lien « Objections » qui n'existait pas, et `--collant` — la hauteur de barre que
le script mesure pour y ranger les ancres — annoncée à **290 px**, donc **toutes
les ancres de la page 290 px trop bas**. Aujourd'hui : **66 px** à 1280, **37 px**
à 900, 58 px sur écran de poche. `index.html` brut ne bouge pas d'un octet
(878 caractères remplacés par 878).

### Deux mesures fausses, corrigées avant d'accuser la page

**Les « commandes recouvertes » étaient un cri de dix-sept faux positifs par
vue.** Un `<details>` fermé garde la géométrie de ses boutons — Chromium les
garde en mémoire de mise en page sans les peindre —, leurs rectangles retombent
sur le texte du bandeau, et la sonde accusait celui-ci. La règle est désormais
stricte : la commande doit être **peinte**, c'est-à-dire apparaître **elle-même**
dans la pile des éléments sous son centre, et ce qu'un panneau déplié, une
fenêtre de dialogue ou une infobulle masque **volontairement** ne compte pas
comme une gêne — un panneau ouvert est là pour ça.

**Les rangées se comptaient mal.** Le premier compte prenait les `offsetTop`
distincts pour des rangées : faux dès que des voisins ont des hauteurs
différentes et sont centrés verticalement — un chapelet de pastilles et de
séparateurs annonçait trois rangées là où il y en avait une. Le compte suit
maintenant le **chevauchement vertical** (plus de la moitié du plus petit), et le
sommaire des accès rapides, annoncé en trois rangées, se révèle sur **une**.

### Voir la page, pas seulement la mesurer

Un plan coté ne remplace pas des yeux. `outils/captures_ecran.mjs` photographie la
page dans un vrai Chromium, par la CI (`.github/workflows/captures.yml`) :
**quatre thèmes × quatre largeurs** — 1280, 900, 640, 380 px —, plus les deux
panneaux ouverts (Affichage, Outils) aux deux extrêmes, les états (survol,
densité resserrée), trois sections visitées, et le guide de première visite dans
la vue qui lui revient. La CI publie les images en artefact et, avec elles, un
**résumé en texte** — hauteurs, rangées, enfants, plan coté — dans le rapport du
travail et en commentaire de la demande de fusion : les images pour l'œil, les
chiffres pour la revue, sans qu'aucune ne dépende de l'autre.

Ce que cet outil a coûté, et ce qu'il a rapporté le jour même : un plafond de
46 % qui cassait quatre commandes en trois rangées à 900 px, un bandeau de
296 px pour 35 px de boutons, un sommaire collant de 290 px pour 25 px de
pastilles, et un chevauchement de barres collantes à 900 px — aucun de ces
défauts n'était visible dans une feuille de style, tous l'étaient dans une
mesure de rendu.

### Ce que la mesure ne dira jamais

Le plan dit les positions, pas la beauté. « 139 px de vide » est un fait, « le
cadre paraissait grand » est un jugement — et c'est le visiteur qui l'avait
porté. Les images restent dans l'artefact, pour l'œil ; les chiffres, dans le
commentaire de demande de fusion, pour la revue.

## Seizième incrément — le clavier, et la fenêtre qui l'ignore

Le visiteur ne l'a pas signalé : personne, sur un écran tactile ou à la souris,
ne s'en aperçoit. C'est en relisant le parcours de la modale — trois façons de la
fermer, aucune d'ouvrir le clavier — que le défaut est apparu, et il était
complet.

### Ce qui n'allait pas

| Le geste | Ce qui se passait |
|---|---|
| la fenêtre s'ouvre | le focus reste sur la page, **derrière** |
| on tabule | on traverse les curseurs de la page, invisibles et pourtant actionnables |
| on tabule encore | on sort par le bas du document, fenêtre toujours ouverte |
| la fenêtre se referme | le curseur reste où il était — souvent au pied de page |
| Échap, rien d'ouvert | la touche est captée pour rien : plus de sortie de champ |

### Ce que la fenêtre fait maintenant

Le focus **entre** — le dialogue porte `tabindex="-1"`, sans quoi un navigateur
refuse de le viser ; c'est la seule chose que la doublure de Node ne sait pas
vérifier, d'où un contrôle statique exprès. Il **ne sort pas** : les six familles
de commandes sont énumérées (`a[href]`, `button`, `summary`, `input`, `select`,
`textarea`), la tabulation est circulaire aux deux bouts, et un focus perdu hors
de la fenêtre y est ramené. Il **revient** à qui l'a ouverte — ou à la commande
principale quand personne ne l'a ouverte, car le guide de première visite se
montre tout seul et rendrait sinon le focus au corps du document. Échap ne ferme
plus que ce qui est ouvert.

L'adresse peut demander le guide : `?guide=1`. C'est un lien de démonstration,
une classe, une capture — et le moyen, pour `outils/captures_ecran.mjs`, d'ouvrir
la fenêtre comme un visiteur la reçoit, plutôt qu'en appelant une fonction
interne.

### Les épreuves, et l'épreuve de l'épreuve

23 contrôles neufs et 7 étapes de harnais (les touches sont jouées événement par
événement ; la doublure du document sait désormais poser et suivre le focus).
Six sabotages posés, six attrapés ; trois posés sur les gestes, trois attrapés.

La **première campagne ne prouvait rien** : les trois sabotages passaient, tous
les trois. La raison est instructive — `tests/test_interface_navigateur.py`
importe le serveur, qui lit la page **au moment de l'import** : patcher le
fichier puis jouer dans le même processus revient à mesurer l'ancienne version.
Le lanceur d'épreuve ouvre désormais un **processus neuf** pour chaque sabotage.
Une épreuve qui ne peut pas échouer ne dit rien : elle se vérifie elle-même.

### Ce que la mesure a fait de plus

Le guide est photographié dans un vrai Chromium **à 1280, 640 et 380 px** — une
fenêtre qui ne tient pas sur un téléphone ne sert à rien — et le voyage au clavier
y est joué pour de bon : la fenêtre est ouverte par `?guide=1`, quatorze
tabulations puis trois en arrière sont comptées hors de la fenêtre, la touche
Échap est pressée, et le nom du porteur du focus est publié dans le résumé de la
demande de fusion.

## Dix-septième incrément — le premier écran d'un téléphone

### Le défaut, mesuré

Le visiteur demandait une « lecture claire et confortable sur un smartphone ».
La mesure, dans Chromium le 15 octobre 2026, a dit autre chose : à **380 px**, la
page prenait **863 px** avant la première ligne de contenu — bandeau 566,
sommaire 58, ruban de veille 239 — sur un écran de 780. À **640 px**, 614 px. Le
contenu existait ; il n'était pas visible. Le plan du bandeau disait où : un
titre de quatre lignes (96 px), une phrase de quatre lignes (97 px), quatre
commandes en trois rangées dont une trouée par un seul bouton (116 px), et une
ligne d'état de cinq rangées de pastilles (184 px, dont une pastille qui répétait
mot pour mot l'horizon du select juste à côté).

### Ce qui a changé

Rien n'a été retiré. Le titre et la phrase **gardent leur corps** — c'est
l'interligne qui se resserre, parce qu'on ne rétrécit pas la lecture pour gagner
de la place. Les quatre commandes du bandeau se rangent en deux colonnes au lieu
de trois rangées. Les pastilles se rapprochent, et l'horizon se dit **une fois**
(le select le porte, `changerHorizon` écrit les deux depuis la même variable).
Le ruban devient une carte plus dense : quatre commandes sur **une** rangée, au
lieu de deux rangées de deux qui coûtaient 51 px de haut pour 44 px de boutons.
Chaque commande y porte un libellé **long** (écran large) et un libellé **court**
(téléphone, où « Masquer le détail des seuils » n'aurait pas tenu dans 80 px) :
`direLeBouton` écrit les deux **ensemble**, sinon le premier clic remettrait le
long et le ruban regonflerait sous les doigts. Le nom accessible ne change pas
(`aria-label`), et la cible du doigt reste à 44 px.

| Largeur | Avant | Après | Détail |
|---|---:|---:|---|
| 380 px | **863** | **693** | bandeau 566 → 483, ruban 239 → 152, sommaire 58 |
| 640 px | **614** | **517** | bandeau 350 → 335, ruban 206 → 124, sommaire 58 |

### Le plafond, et pourquoi il est ancré

Un gain non tenu se reperd. `outils/plafonds_premier_ecran.mjs` porte donc les
plafonds du premier écran — **720 px à 380**, **540 px à 640** —, chacun avec la
mesure datée dont il vient et l'état ancien qu'il doit battre. La photographie
échoue si un plafond est dépassé, et le résumé publie le verdict : la marge est
**d'une rangée**, assez pour les chiffres qui changent d'une simulation à
l'autre, trop peu pour cacher une rangée de plus. Trois règles tenues par les
contrôles : aucun plafond au-dessus de l'état ancien (il décrirait le statu quo
au lieu de le corriger), aucun plafond sous la mesure du jour (il ferait rougir
un travail en cours), et **seul le téléphone est plafonné** — au large, le
premier écran fait 394 px sur 900, la place n'y manque pas.

Le résumé des captures publie désormais aussi le **plan du ruban** et celui de la
**ligne d'état** : mesurés depuis le début, jamais montrés. C'est là que la
hauteur se perdait sans qu'on sache qui la prenait.

## Dix-huitième incrément — les pastilles d'état, et le texte qu'on ne lit qu'une fois

### Le défaut, mesuré

À **380 px**, la ligne d'état du bandeau prenait **140 px en quatre rangées** — pour
trois pastilles. L'une d'elles faisait **deux lignes** à elle seule :
`16 leviers actifs · simulation 5 ans · score moyen 51,3 (référence 50,0)`, alors
que le score est **déjà** dans le résumé de tête. Le téléphone relisait ce qu'il
venait d'afficher, sur deux lignes, dans l'élément le plus étroit de la page : le
même défaut que l'horizon dit deux fois, corrigé à la passe précédente, resté
intact sur les autres pastilles.

### Ce qui a changé

Le couple de libellés `long` / `court` n'est plus une affaire de ruban : il
devient la règle de la **page** — `.mot-court{display:none}` au large, bascule au
palier **640 px** —, et les pastilles d'état le reprennent. Chacune porte ses deux
textes : `live` · `référence datée` · `mixte`, l'horodatage nu sur téléphone,
`N leviers — calcul…`, `N exercices simulés`, `N leviers · H ans`.

`display:none` sort le texte écarté de l'arbre d'accessibilité : ce qui est peint
est ce qui est lu, une fois, sans doublon — donc pas d'`aria-hidden` sur les
textes d'état, contrairement aux libellés des commandes du ruban dont le nom
accessible est tenu à part par `aria-label`. Les deux textes d'une pastille sont
écrits **ensemble** par `direLaPastille()`, sinon la pastille annoncerait l'état
précédent ; la fonction retombe sur le texte long quand la page ne porte pas ses
deux repères.

### Le gain, mesuré, et le cliquet resserré

| Largeur | Avant la passe | Après | Plafond (avant → après) |
|---|---:|---:|---|
| 380 px | 693 | **646** | 720 → **673** |
| 640 px | 517 | **488** | 540 → **515** |

À 380 px, la ligne d'état passe de **quatre rangées (140 px) à trois (93 px)** :
la pastille de deux lignes qui répétait le score n'en fait plus qu'une. Le cliquet
est resserré d'autant — un gain qu'on ne relève pas se reperd —, avec la même
marge d'une rangée. Et le rapport de mesure lit désormais `innerText` : il montre
le libellé **peint**, `référence datée du projet` à 1280 px et `référence datée` à
380 px, au lieu d'additionner les deux.

### Le contrôle du ruban, requalifié — pas amolli

`tests/test_interface.py` lisait dans le palier 640 l'affichage des libellés
courts du ruban. Cette règle ayant changé de propriétaire, le contrôle lit
désormais ce qui reste **sien** : la carte du ruban — quatre colonnes, cible du
doigt de 44 px, verdict qui se lit en entier. La règle des libellés est tenue par
`tests/test_premier_ecran.py`, et maintenant pour le ruban **et** pour les
pastilles. Un contrôle qui aurait continué de lire une règle déplacée aurait
rougi sur du travail juste ; le déplacer sans le remplacer aurait laissé la carte
sans garde.

### Dix sabotages, dix attrapés

Courts non masqués au large, courts non peints sur téléphone, long laissé peint
sur téléphone, texte court retiré d'une pastille, `aria-hidden` posé sur un texte
d'état, écriture du texte court supprimée, pastille écrite en clair sans son
texte court, contexte sans texte court, ruban remis en deux colonnes, cible du
doigt rabotée sous 44 px.

## Dix-neuvième incrément — la dernière rangée du bandeau d'un téléphone

### Le défaut, mesuré

À 380 px, le bandeau faisait **436 px** — et sa ligne d'état **trois rangées**.
Trois pastilles ne tenaient plus côte à côte : la plus large était l'horodatage,
`2026-10-15 15:09 UTC`, **157 px** mesurés. Le titre et la phrase d'accroche
prenaient quatre lignes chacun (96 et 85 px). Rien n'était cassé ; tout était long.

### Ce qui a changé

L'horodatage porte **deux formes du même instant**, écrites depuis une seule
lecture du contexte : la forme longue pour l'écran large, `15/10 15:09` — onze
signes — pour la rangée d'un téléphone. Le contexte et les leviers tiennent alors
à côté, et la ligne d'état passe de trois rangées à deux. Les pastilles se
resserrent d'un cran, et la phrase d'accroche resserre son interligne **sans
changer de corps** : la lecture ne rétrécit pas pour gagner une rangée.

### Le gain, mesuré, et le cliquet resserré

| Largeur | Avant la passe | Après | Plafond (avant → après) |
|---|---:|---:|---|
| 380 px | 646 | **603** | 673 → **630** |
| 640 px | 488 | **460** | 515 → **487** |

À 380 px, la ligne d'état passe de **trois rangées (91 px) à deux (64)** : le
contexte (114 px), l'horodatage court (90) et les leviers (113) tiennent sur la
même rangée — `16 leviers actifs`, car le select voisin dit déjà la durée. Le
bandeau passe de 420 à **393 px**. Le cliquet suit la mesure à marge constante.

### Ce qui n'a pas changé, et pourquoi

Le titre garde son corps. Le descendre d'un cran aurait gagné une ligne, mais
c'est la première chose que l'œil lit, et la page dit depuis le premier jour
qu'elle ne rétrécit pas la lecture pour tenir dans un écran. Ce qui cède ici, ce
sont des **répétitions** — un horodatage qui redit son année et son fuseau sur
l'écran le plus étroit — pas des corps de texte.

## Ce qui est vérifié, et comment

Les garde-fous ci-dessous sont dans `tests/test_interface.py` : ils échouent si
quelqu'un réintroduit les défauts mesurés plus haut.

- aucune taille de texte sous `--t-min` (sauf les cas explicitement exemptés) ;
- présence des quatre paliers et de `(pointer:coarse)` ;
- présence de `min-width:0` sur les enfants de grille ;
- présence de `rendreTableauxDefilants(` et de `.tableau-defilant` avec
  `role="region"` et `tabindex="0"` ;
- présence du lien d'évitement, en premier élément focalisable de la page ;
- résumé de tête au-dessus de la première section, alimenté par les mêmes
  fonctions que la balance, et appelé par elle ;
- quatre chapitres, chacun avant la première section qu'il ouvre ;
- mouvements coupables par `prefers-reduced-motion` ;
- impression sans plafond de hauteur, graphique nommé et à échelle gardée,
  aides tactiles, contraste renforcé, grille à deux colonnes sous 480 px ;
- impression d'un plan : la commande du résumé, le mode visible à l'écran, le
  papier qui ne garde que le plan et le crédit, et le bandeau qui ne s'imprime
  jamais ;
- échelle de plans déclarée dans `:root`, aucun `z-index` numérique dans une
  règle, tout `var(--z-…)` employé déclaré ;
- encoches sur les quatre bords **avec valeur de repli**, sections basses en
  rendu différé et différé levé à l'impression, modale en `dvh` ;
- le plan en proportion : les deux barres du résumé, leurs parts écrites en
  clair, un motif de chaque côté, et une seule fonction partagée avec les jauges
  de la balance ; sans simulation, les barres restent à zéro ;
- aucune propriété personnalisée ne se définit elle-même — `--panel-3` portait
  sa propre boucle, donc une couleur qui n'arrivait jamais.
- ce que le navigateur décidait seul : `color-scheme:dark` déclaré une fois et
  aucun `prefers-color-scheme`, `text-size-adjust:100%`, zoom laissé libre, et
  **toute** surface déclarant un défilement qui retient son geste ;
- la barre de commande : une seule barre collante sous 901 px, la pastille dans
  la barre (et non dans la liste qui défile), un bouton et non un lien, cachée
  sans diagnostic, son texte pris aux mêmes fonctions que le ruban, la hauteur
  mesurée et suivie, le repli du CSS qui dit la vraie hauteur, le ruban en carte
  sous 640 px, et rien de tout cela sur papier ;
- le repère de lecture : `marquerLecture` appelée par le clic **et** par
  l'observateur, `aria-current` posé avec la classe, un identifiant inconnu qui
  efface la marque au lieu de la laisser ;
- le passage en cartes : la bascule dans la requête de 640 px, l'en-tête clippé
  et **jamais** `display:none`, `content:attr(data-label)`, la première cellule
  en titre, la première colonne qui ne colle plus, et la vérification qui
  précède toute écriture ;
- aucune règle de carte dans les blocs d'impression (le papier garde un tableau) ;

Sept fichiers de tests **exécutent** le code, ils ne le relisent pas :

- `tests/test_defilement_tableaux.py` fait tourner l'enveloppement des tableaux
  sur un DOM minimal et vérifie qu'un seul tableau est enveloppé, que la région
  est nommée et atteignable au clavier, que le tableau n'est pas modifié et que
  les tableaux déjà défilants sont laissés tranquilles ;
- `tests/test_aides_focalisables.py` vérifie qu'un ordinateur ne gagne aucun
  arrêt de tabulation, qu'un appareil tactile gagne exactement les deux aides
  qui en avaient besoin, que les éléments déjà focalisables sont laissés tels
  quels, et que le sommaire ouvert se referme en annonçant son état ;
- `tests/navigateur_interface.mjs` demande au parcours réel que le résumé de
  tête porte **le solde de la balance** (comparaison de texte), que sa phrase
  soit celle du verdict, qu'un changement d'année relise le résumé, et que les
  proportions affichées soient **exactement** celles des jauges de la balance
  (`87 % / 13 %` sur le préréglage de référence) — la preuve qu'une seule
  fonction alimente les deux visuels ;
- `tests/test_impression_plan.py` ouvre le mode d'impression sur un DOM
  minimal : `window.print()` part **une fois par demande** (jamais au
  chargement), le bandeau relance le tirage sans quitter le mode, le retour
  ramène la page entière **et le focus sur le bouton**, et une impression
  refusée ne laisse ni exception ni page amputée.

`tests/test_tableaux_en_cartes.py` exécute le passage en cartes sur un DOM
minimal : un tableau simple reçoit le nom de sa colonne sur chaque valeur, un
tableau à deux lignes d'en-tête ou à cellule fusionnée n'est **pas** touché
(zéro étiquette — tout ou rien), une cellule réparée rend le tableau étiquetable,
et un tableau devenu incohérent rend sa marque. Un sabotage volontaire du
script (l'étiquette refusée ignorée) a été posé puis retiré pour vérifier que ces
contrôles mordent.

`tests/test_regions_defilantes.py` exécute le nom des régions : large, étroite,
élargie, avec un pli de fenêtre et sans écouteur — le tableau fusionné garde son
étiquette et son arrêt, le nom ne s'empile jamais, et le garde-fou qui refuse une
fenêtre sans écouteur ne casse rien.

`tests/test_barre_commande.py` exécute la barre : une hauteur mesurable est
écrite dans `--collant`, une hauteur nulle laisse la valeur de repli en place,
l'observateur suit bien la barre et rappelle la mesure quand elle grandit, la
pastille dit le niveau en toutes lettres (« hors-sol · 12 alerte(s) »), un
diagnostic disparu l'efface et une pastille absente ne fait rien jeter.

Le DOM minuscule commun à quatre de ces fichiers vit dans `tests/dom_minimal.mjs` :
il fournit classes, attributs, enfants et ordre du document, et rien d'autre.



## Limites assumées

- **Aucun navigateur dans l'environnement d'écriture** : pas de capture d'écran,
  donc pas de contrôle visuel direct. Les garde-fous sont structurels et
  mesurables ; le contrôle du rendu réel reste humain (téléphone, tablette,
  zoom 200 %, contraste renforcé, impression).
- **Les couleurs de la palette M.R.S.C. ne sont pas retouchées** : les contrastes
  de la page intégrée sont ceux du site, et une retouche ici ferait diverger les
  deux.
- **La densité des tableaux d'audit reste supérieure à celle du reste** : c'est
  voulu (audit et traçabilité), et le plancher de lisibilité s'y applique.

- ~~**Le nom de la région ne suit pas la bascule**~~ : corrigé au dixième
  incrément, ci-dessus. Le nom et l'arrêt de tabulation suivent le palier, dans
  les deux sens, et la question posée au navigateur est celle que le CSS tranche.
- **`:has()`** : les quatre règles qui rendent la place supposent `:has()`. Sans
  lui, les cartes s'affichent quand même, dans une boîte qui garde son plafond de
  hauteur — une dégradation, pas une rupture.

- **La pastille est un résumé** : elle dit le niveau et le nombre d'alertes, pas
  lesquelles. Le détail reste dans la console, à un geste de là — et en dessous
  de 901 px, la feuille de style n'affirme plus que la veille soit collante.
