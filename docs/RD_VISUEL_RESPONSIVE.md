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

Quatre fichiers de tests **exécutent** le code, ils ne le relisent pas :

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

Le DOM minuscule commun aux deux premiers vit dans `tests/dom_minimal.mjs` : il
fournit classes, attributs, enfants et ordre du document, et rien d'autre.



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
