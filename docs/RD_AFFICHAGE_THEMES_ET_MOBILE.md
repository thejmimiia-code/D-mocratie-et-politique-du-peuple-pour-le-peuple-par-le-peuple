# R&D — Afficher sans submerger : quatre thèmes, une ligne éditoriale, un écran de poche

Ce document raconte la passe du 14 octobre 2026 sur **la façon dont la page se
présente** : quatre thèmes au choix du visiteur, un rythme de lecture emprunté au
site M.R.S.C., et une page qui se lit sur un téléphone sans qu'on ait à pincer
l'écran. Il ne raconte pas une refonte : le contenu, les chiffres, les routes et
les contrôles n'ont pas bougé. Ce qui a changé, c'est ce qui se passe entre le
serveur et l'œil.

---

## 1. La demande, et le constat mesuré

La demande, mot pour mot : *« Fait toute la R et D nécessaire pour faire en sorte
d'ajuster l'affichage et que les visiteurs qui viennent tester le simulateur ne
soient pas submergés par tout un tas de choses entremêlées et compactes !
Utilise la mise en page et la ligne éditoriale du dépôt du M.R.S.C sur mon dépôt
GitHub afin d'utiliser le meilleur compromis visuel et construis plusieurs thèmes
d'affichage différents pour que les visiteurs puissent en changer, et adapte le
système pour rendre la lecture claire et confortable sur un smartphone ! »*

Avant d'y répondre, la page a été mesurée comme un objet, pas comme une
intention :

| Ce qui a été mesuré | Avant cette passe |
|---|---|
| Sections de la page | 24, toutes de la même forme |
| Texte d'explication des sections | **dans le titre**, en corps plus petit (`.aide` dans le `h2`) : le lecteur butait sur un titre à deux niveaux |
| Thèmes disponibles | **un seul** — sombre, imposé |
| Densité | une seule, serrée : `padding:16px`, écart de 14 px entre les blocs |
| Réglages d'affichage | aucun : ni thème, ni taille de texte, ni densité |
| Taille de la page | 418 912 caractères |
| Contrastes vérifiés ailleurs que dans l'œil | **nulle part** : aucun contrôle ne calculait un rapport de contraste |

Le reproche n'était donc pas une impression : la page expliquait *dans ses
titres*, ne laissait aucun choix, et rien ne prouvait qu'une couleur se lisait.

## 2. Ce qui a été emprunté au site M.R.S.C., et rien d'autre

Le dépôt `thejmimiia-code/MRSC` a été **lu**, pas copié : sa feuille
(`assets/css/site.css`, 98 886 octets) a été relevée jeton par jeton pour en
tirer une dizaine de mesures, qui sont devenues des règles du simulateur.

| Relevé dans la charte M.R.S.C. | Ce que le simulateur en a fait |
|---|---|
| `.eyebrow` : sur-titre en majuscules, `0,77 rem`, interlettrage `0,13 em`, **trait vert de 25 × 3 px** avant le mot | `.eyebrow` — le trait fait 25 × 3 px, arrondi, `var(--vert)` |
| Titres `clamp(1.9rem,3.7vw,2.8rem)`, corps `1,7` de interligne | Titres de section en `clamp(1.12rem,.7vw+.96rem,1.55rem)`, `line-height` portée à 1,65 sur les phrases d'introduction |
| `.section-heading{max-width:730px}` : le texte ne court pas sur toute la largeur | `--mesure:74ch` appliquée à `.section-intro` |
| `--content:1160px` | Conteneur ramené de 1560 px à **1440 px** (les tableaux gardent leur défilement) |
| Panneau « Affichage » (`<details>` + `<summary>`, boutons d'état, note « ces choix restent enregistrés ») | Le même objet, avec les mêmes mots : `<details class="affichage">`, quatre thèmes, deux densités, cinq tailles |
| `--button-height:48px`, `--button-radius:9px`, `--radius:20px` | Cibles de 44 px minimum sur petits écrans, rayons 8/11/14/18 px |
| `--paper:#f5f7fa`, `--ink:#18243b`, `--navy:#1d3268`, `--blue:#2958a2`, `--green:#456d29` | Le thème « Jour » du simulateur, exactement ces valeurs |

Ce qui n'a **pas** été repris : la navigation du site (Accueil, IA & société…),
son cartouche d'association, ses pages. Le simulateur n'est pas le site ; il en
parle la même langue visuelle.

## 3. Les quatre thèmes, et ce que chacun sert

Quatre palettes complètes, **47 jetons aux mêmes noms**, dans `simulateur/interface.py` :

| Thème | Pour qui / pour quoi | Encre sur fond | Fonds |
|---|---|---:|---|
| **Soir** (défaut d'origine) | l'écran du soir, la pièce sombre | `#e6edf7` sur `#131c2f` — **14,4:1** | `#0b1220` |
| **Jour** | la charte M.R.S.C., le bureau éclairé | `#18243b` sur `#ffffff` — **15,5:1** | `#f2f5fa` |
| **Crème** | les longues lectures, le papier chaud | `#2b2a26` sur `#fffdf7` — **14,1:1** | `#f6f1e6` |
| **Contraste renforcé** | malvoyance, plein soleil, écran médiocre | `#ffffff` sur `#000000` — **21:1** | noir pur, `--texte-dim` à 17,1:1 |

Trois décisions méritent d'être écrites :

- **Le défaut est le réglage de l'appareil.** Un appareil qui annonce préférer
  le clair reçoit « jour », sinon « soir » — mais **un choix explicite gagne
  toujours** et se garde. C'est le seul moyen de ne pas trahir quelqu'un qui a
  ouvert le mode sombre de son système *et* choisi « crème » ici.
- **`prefers-color-scheme` n'entre pas dans la feuille de style.** Aucune
  requête `@media (prefers-color-scheme: …)` : le choix est fait par le script
  d'en-tête, avant le premier pixel. Une media query CSS aurait écrasé le choix
  du visiteur — l'exact contraire du but. Un contrôle le refuse.
- **Le thème se pose dans `<head>`, jamais après le rendu.** Sans cela, la page
  s'ouvre sombre puis bascule en clair : c'est précisément la scène qu'on veut
  éviter. Le script d'en-tête lit `localStorage`, choisit, pose
  `data-theme` / `data-densite` / `data-texte` sur `<html>`, et **rien ne part
  sur le réseau** : aucune fonction de réglage ne contient de `fetch`.

### Deux jetons nés de la mesure

Les quatre thèmes ont hérité de deux jetons qui n'existaient pas, et chacun
répare une erreur trouvée par le calcul, pas par l'œil :

- **`--encre-pleine`** — l'encre qui tranche sur une surface vive (rouge,
  accent, vert). Elle est *sombre* dans un thème sombre et *claire* dans un
  thème clair. Avant, la strate « hors-sol » écrivait `color:#fff` sur un rouge
  vif : **3,76:1** en « soir », **2,02:1** en « contraste renforcé ». Deux
  textes illisibles, invisibles parce que personne ne mesurait.
- **`--sur-mrsc`** — l'encre du bandeau de marque. L'onglet actif des strates
  écrit son texte sur un dégradé `--mrsc-navy` → `--mrsc-bleu`, sombre dans les
  quatre thèmes : il lui faut donc une encre claire dans les quatre thèmes, y
  compris là où `--encre-pleine` est noire (thème contraste, où l'onglet tombait
  à **1,06:1**).

## 4. La lisibilité, calculée et non jugée

`outils/couleurs.py` (atelier de couleurs, 20 contrôles propres) calcule les
rapports WCAG 2.1. `tests/test_themes_en_page.py` s'en sert pour **mesurer la
feuille de style elle-même** : chaque règle qui écrit une couleur de texte est
résolue depuis la palette du thème, posée sur le fond réel que la règle lui
donne, et comparée au seuil de 4,5:1.

Le résultat, theme par theme (minimums sur l'ensemble des règles mesurées) :

| Thème | Corps de texte | Texte secondaire | Teintes de sens | Pire règle mesurée |
|---|---:|---:|---:|---:|
| Soir | 14,4:1 | 6,7:1 | 4,5 – 7,9:1 | **5,29:1** |
| Jour | 15,5:1 | 5,6:1 | 5,9 – 7,1:1 | **5,19:1** |
| Crème | 14,1:1 | 6,8:1 | 6,0 – 7,3:1 | **5,10:1** |
| Contraste | 21,0:1 | 17,1:1 | 10,4 – 14,6:1 | **9,26:1** |

Trois corrections sont nées de ce calcul, le jour même :

1. la strate hors-sol (voir `--encre-pleine` ci-dessus) ;
2. l'onglet actif des strates (voir `--sur-mrsc`) ;
3. le rouge employé en **petit texte** (`.delta.baisse`, `.resume-cout .valeur`,
   `.sommaire-veille.niveau-risque`) tombait à **4,04:1** en « soir » sur le
   second fond de carte. Les couleurs de sens sont désormais ramenées vers
   l'encre du thème (`color-mix(in srgb,var(--rouge) 72%,var(--texte))`) quand
   elles écrivent du texte : le repère de couleur reste, la lisibilité passe
   d'abord — et un contrôle balaie toute la feuille pour le vérifier.

Deux règles échappent au balayage, parce qu'elles peignent leur propre fond ;
elles sont mesurées à part, explicitement : la strate hors-sol et l'onglet actif.

## 5. La ligne éditoriale : trois temps par section

Chaque section se lit maintenant comme une page du site M.R.S.C. :

```html
<header class="section-entete">
  <p class="eyebrow">Votre plan</p>
  <h2 id="resume-titre">🧾 Votre plan en un coup d'œil</h2>
  <p class="section-intro">Les chiffres qui comptent, repris de la balance — rien n'est recalculé ici.</p>
</header>
```

- **24 sections** portent cette forme, **24 sur 24** : un contrôle refuse une
  section sans sur-titre, une section sans phrase, et un en-tête dont le
  sur-titre n'est pas suivi d'un titre.
- L'explication a **quitté les titres** : plus aucun `<h2>` ne contient de
  `.aide`.
- Les phrases sont **des phrases** : majuscule initiale, ponctuation finale —
  vérifié sur les 24, une par une.
- Le sur-titre porte le trait vert de la charte (25 × 3 px) et l'interlettrage
  `0,13 em`.
- L'échelle d'espacement (`--e-1…--e-6`) et ses trois dérivés (`--pad-bloc`,
  `--ecart-section`, `--ecart-carte`) sont **employés** : un contrôle refuse un
  jeton déclaré mais jamais utilisé — c'est ce qui restait après la passe
  précédente, où l'échelle avait été posée sans être branchée.
- Les quatre chapitres (« Régler », « Voir », « Juger », « Vérifier ») sont
  devenus des bandeaux complets : pastille numérotée agrandie, titre en
  `clamp()`, phrase de repère bornée à `--mesure`.

## 6. Le téléphone, et la densité

- **Le panneau « Affichage » se replie en feuille** sous 640 px : `position:fixed`
  en bas de l'écran, défilement propre (`overscroll-behavior:contain`, sinon le
  doigt entraîne la page derrière), boutons de 44 px de haut, hauteur bornée à
  `min(70vh,420px)`.
- **Les cinq tailles de texte** (`87`, `100`, `112`, `125`, `137 %`) agrandissent
  toute la page en `rem`. Le **plancher de lecture reste en pixels**
  (`--t-min:12.5px`) : un contrôle refuse qu'une taille de texte touche au
  plancher, un autre refuse tout `font-size` sous 12 px hors `max(var(--t-min)…)`.
  Agrandir ne peut donc pas faire passer un texte sous le seuil de lisibilité.
- **La densité** est une affaire de trois jetons : « Aéré » (défaut) donne
  `--pad-bloc: var(--e-4)`, « Compact » `var(--e-3)` — aucune règle ne connaît le
  mode, donc rien ne peut être oublié dans un coin de la page.
- Ce qui ne bouge pas : les quatre paliers (1200/900/640/480), les cibles
  tactiles de 44 px sous `(pointer:coarse)`, les tableaux convertis en cartes, le
  sommaire repliable et collant. Ces règles avaient leurs contrôles ; ils sont
  restés verts.

## 7. Ce qui surveille tout ça

| Contrôle | Nombre | Ce qu'il refuse |
|---|---:|---|
| `tests/test_themes_en_page.py` | **36** | un thème sans les mêmes jetons, un jeton qui se définit lui-même, un texte sous 4,5:1, une teinte écrite en clair dans une règle, une section sans sur-titre, une phrase sans majuscule, un réglage qui part au serveur, un panneau qui défile sans retenir son geste |
| `tests/test_couleurs.py` | 20 | un atelier de mesure complaisant (repères WCAG connus d'avance) |
| `tests/navigateur_interface.mjs` | **15 étapes neuves** (214 au total) | un thème qui ne se pose pas avant le rendu, un choix qui ne se garde pas, un appareil clair qui reçoit le sombre, un bouton qui ment sur son état, une taille qui sort de ses bornes |
| `tests/test_interface_navigateur.py` | 1 contrôle neuf | l'absence d'une de ces quinze étapes |
| Sabotages | **22 posés, 22 attrapés** | 18 sur la feuille (thème manquant, contraste affaissé, jeton récursif, teinte figée, densités identiques, taille disparue, trait de charte supprimé, en-tête retiré, phrase en minuscule, jeton employé mais non défini, teinte de plateau desserrée…), 4 sur le comportement (choix non gardé, `aria-pressed` figé, taille non bornée, appareil ignoré) |

Quatre erreurs réelles ont été trouvées par ces contrôles, pas inventées pour
la démonstration :

1. **les deux encres figées** de la strate hors-sol et de l'onglet actif
   (contrastes 3,76 / 2,02 / 1,06) ;
2. **une balise `<span>` jamais fermée** dans la phrase d'introduction de la
   matrice (`matrice-fraicheur`) : le contrôle qui compte les en-têtes éditoriaux
   l'a signalée parce que 23 en-têtes sur 24 étaient reconnus. Le document
   comptait 61 `<span>` ouverts pour 60 fermés ;
3. **un jeton employé mais jamais défini** : les deux plateaux de la balance
   lisaient `--classe-recettes-fond` et `--classe-depenses-fond`, disparus d'une
   réécriture de palette. Un navigateur ne se plaint pas d'une variable absente :
   le fond devenait simplement transparent. Les deux jetons existent désormais
   dans les quatre thèmes, et le repli écrit en clair **vaut exactement** ce que
   `color-mix` calcule à 12 % — la proportion a été mesurée, elle aussi : à
   14 %, le texte secondaire du thème « jour » tombait à 4,49:1 et 4,38:1 sur
   les deux plateaux ;
4. **six contrôles qui figeaient l'ancienne feuille** (`color-scheme:dark`
   unique, `--classe-*-fond`, dégradés `rgba()` littéraux, motifs noirs,
   `prefers-contrast` global) : ils ont été réécrits sur la forme jetonnée, et
   deux contrôles d'autres passes qui lisaient « jusqu'à la fin du titre » ont
   été élargis à « jusqu'à la fin de l'en-tête », parce que la phrase qui nomme
   la route a déménagé sous le titre.

## 8. Ce que ça coûte

| Charge | Avant | Après |
|---|---:|---:|
| `index.html` (caractères) | 418 912 | **439 540** |
| Page entière, compressée (`gzip -6`) | ~111 155 o (ancre) | **119 995 o** |
| Plafond de la page | 122 271 o | **131 995 o** (ancre relevée : 119 995 o) |
| Premier écran (budget dérivé) | 256 372 o | **265 212 o** → plafond 291 734 o |

L'ancre de la page a été **relevée dans ce commit**, comme le veut la règle du
dépôt : une croissance voulue se paie d'un relèvement d'ancre daté et expliqué.
La marge reste de 10 %, et `outils/budgets_fluidite.py` reste le juge — il ne
mesure pas une intention, il refuse un dépassement.

## 9. Limites assumées

- **Le contraste n'est pas la beauté.** Ces contrôles refusent ce qui se lit
  mal ; ils ne disent rien du goût, de la hiérarchie ressentie, de la justesse
  d'un vert. Une palette peut passer tous les seuils et rester désagréable.
- **Les rapports WCAG supposent un fond uni.** Une teinte translucide posée sur
  une image ou un dégradé n'est mesurée que sur son premier arrêt ; la mesure
  est donc une borne, pas une garantie.
- **Le rendu réel n'est pas observé.** Le harnais exécute le JavaScript sur une
  doublure de DOM ; ni lui ni les contrôles statiques ne peignent un pixel. Une
  media query mal comprise, un `clamp()` qui surprend, une police qui manque :
  cela se voit dans un navigateur, pas ici. Les quatre paliers sont contrôlés
  par leur présence, pas par capture d'écran.
- **Le thème suit l'appareil au chargement seulement** — ou quand le système
  change, si et seulement si le navigateur l'annonce (`addEventListener` sur la
  media query) et si aucun choix explicite n'a été fait. Un navigateur ancien
  qui ne l'annonce pas garde le thème posé au chargement.
- **Rien de tout cela n'est mesuré sur un vrai téléphone.** Les cibles de 44 px
  et la feuille de bas d'écran sont des règles ; elles demandent un pouce pour
  être jugées.

## 10. Ce qui a été importé du site M.R.S.C., et ce qui reste dehors

La demande portait sur **le meilleur compromis visuel** entre les deux dépôts.
Voici la liste, tenue à jour pour la prochaine passe.

**Importé le 14 octobre 2026** : le sur-titre `.eyebrow` et son **trait vert de
25 × 3 px** ; les **titres à échelle fluide** (`clamp`) et l'interligne de
lecture (1,7 pour le corps, 1,65 pour les phrases) ; la **largeur de lecture
bornée** (730 px chez M.R.S.C., `--mesure:74ch` ici) ; le **conteneur ramené de
1560 à 1440 px** ; les **rayons** (20 px de carte, 9 px de bouton) ; les
**cibles de 48 px** de la charte (44 px ici, plancher tactile) ; et le **panneau
« Affichage »** sous le même nom, avec les mêmes mots — « Ajuster la lecture »,
« ces choix restent enregistrés sur cet appareil ». Les quatre thèmes du
simulateur naissent de là : « Jour » reprend les jetons de la charte
(`#f5f7fa`, `#18243b`, `#1d3268`, `#2958a2`, `#456d29`).

**Déjà importé aux passes précédentes** : la palette `--mrsc-*` (navy, bleu,
vert, or, rouge et leurs clairs), le vert des recettes et le rouge des dépenses
pour les classes de leviers, les crédits « © 2026 Mouvement Représentatif de la
Société Civile (M.R.S.C) » avec le lien vers le site, le sigle et le logo, et la
mention « valeur citoyenne non vérifiée par le M.R.S.C ».

**Ce qui n'est pas repris, et pourquoi** :

| Élément du site M.R.S.C. | Pourquoi il reste dehors |
|---|---|
| La navigation générale (Accueil, IA & société, Apprendre, Documents, Liens utiles, Localisation, Transparence, Nous contacter) | Le simulateur est **une page**, servie par deux hébergeurs et recopiée dans le site. Une navigation renverrait vers des pages qui n'existent pas dans ce dépôt — et le lien vers le site est déjà dans les crédits |
| Le bandeau de chiffres clés (5 échelons · 100+ leviers · 20 domaines · 11 scénarios · 52 indicateurs · 0 compte) | La page porte ces chiffres **en direct** (leviers actifs, comptes de la balance, 20 domaines, 11 scénarios). Un bandeau figé mentirait dès le premier réglage |
| Le bloc « Ce qu'il fait — et ce qu'il ne fait pas » | Le simulateur a plus précis : « Traçabilité », « Audit & traçabilité », et les sections servies par le moteur (nuances, contre-pouvoirs, objections) |
| Les fiches « Apprendre » (dossier documentaire) | Ce sont les documents de `docs/`. Les recopier dans la page la ferait grossir de plusieurs centaines de kilo-octets — le budget de page les refuserait — et figerait des contenus qui vivent dans le dépôt |
| Le formulaire « Nous contacter » | Il n'existe aucun service de messagerie côté simulateur : un formulaire qui ne mène nulle part vaut moins qu'une absence |
| L'`iframe` d'intégration du site | C'est le site qui intègre le simulateur, pas l'inverse ; en intégrer un ici ferait une page dans la page |
| `html[data-layout="lecture"|"panorama"]` (940 / 1480 px) | **Importé le 14 octobre 2026**, onzième incrément ci-dessous, sous forme de trois présentations — Équilibrée (1440 px), Lecture (1000 px), Panorama (1680 px). Ce qui a décidé de la largeur : les phrases sont bornées par `--mesure` mais les **grilles** ne l'étaient pas, et un écran très large les étirait sur quatre colonnes sans intérêt |

*Vérifié en ligne le 14 octobre 2026 : le site sert toujours « Simulateur
macro-politique » avec son bandeau de chiffres clés et sa copie embarquée du
simulateur (révision lisible dans la page). Rien ici n'en dépend — la copie
embarquée est sortie de ce dépôt par décision de son auteur — mais la langue
visuelle, elle, est partagée.*

## 11. Le onzième incrément : l'encre, le cadre, la présentation (14 octobre 2026)

Le visiteur a écrit : « certains thèmes n'apparaissent pas correctement, les
couleurs des boutons ne sont pas adaptées par rapport au fond, ce qui fait que la
lecture est difficile ; il y a trop d'espace entre deux blocs ; le cadre avec les
boutons d'accès rapide est beaucoup plus grand que la place que prennent les
boutons eux-mêmes. » Les trois griefs étaient mesurables, et les trois étaient
justes.

### 11.1 Ce que la mesure a trouvé

`outils/contraste_ecran.py` est né de ce grief. Les contrôles de la §4 mesurent
des **règles** : ils ne voient pas l'héritage, et la faute vivait exactement là.
L'audit de la version en ligne du 14 octobre a rendu onze textes illisibles par
thème clair :

| Texte | Encre héritée | Fond peint | Rapport |
|---|---|---|---:|
| le titre du bandeau | `#18243b` (« jour ») | `#1d3268` | **1,27:1** |
| la phrase d'accroche | `#5a6980` | `#1d3268` | **1,64:1** |
| « Simuler avec impacts croisés » | `#18243b` | `#1d3268` | **1,27:1** |
| « Rafraîchir les données » | `#18243b` | `#1d3268` | **1,27:1** |
| « Réinitialiser les leviers » | `#18243b` | `#1d3268` | **1,27:1** |
| « Régler les leviers » (plan et ruban) | `#18243b` | `#1d3268` | **1,27:1** |
| les quatre numéros de chapitre | `#18243b` | `#1d3268` | **1,27:1** |

Le mécanisme est toujours le même : un élément **peint** un fond de marque et
**n'écrit pas** d'encre — l'encre du thème lui tombe dessus. En « soir » et
« contraste », l'encre du thème est claire, donc la faute était invisible ; en
« jour » et « crème », elle est sombre.

### 11.2 L'instrument, et ce qu'il refuse de cacher

L'outil lit la page **réellement servie** (`index.html`), en dresse l'arbre,
applique la feuille (cascade, spécificité, héritage, `var()`, `color-mix()`,
`@media` selon la largeur demandée), compose les fonds (dégradés, transparences,
`opacity`) et compare chaque texte à son fond réel avec la formule WCAG 2.1.

Il affiche **ce qu'il écarte** : les règles d'état (`:hover`, `:focus`,
`:disabled`, `::before`) et les commandes inactives, que la norme exempte. Un
contrôle qui tait ce qu'il ignore n'est pas un contrôle.

    python3 outils/contraste_ecran.py                        # 4 thèmes × 2 largeurs
    python3 outils/contraste_ecran.py --theme jour --verbeux  # le détail, ligne à ligne

### 11.3 La réparation

- **Le bandeau suit le thème** : `header.entete` garde son dégradé de jetons
  (`--entete-1` → `--entete-2`, blancs en « jour », papier en « crème », nuit en
  « soir ») et **écrit son encre** ; un contrôle refuse désormais qu'il peigne un
  jeton de marque.
- **Un aplat de marque écrit son encre** : `button.primaire`,
  `.onglets button.actif` et `.chapitre-num` prennent `--sur-mrsc`, et un
  contrôle structurel l'exige — il refuse toute règle qui peint `--mrsc-*` sans
  écrire de `color`, et vérifie le rapport sur chaque arrêt du dégradé, dans les
  quatre thèmes.
- **Le texte secondaire remonte** : `--texte-dim` du thème « jour » passe de
  `#5a6980` à `#56637a`. Les libellés des plateaux de la balance passent de
  **4,34:1 à 4,73:1**, le ruban de coût de **4,38:1 à 4,74:1**.
- **Le résultat** : pire cas mesuré **4,58:1** (« soir »), **4,62:1** (« jour »),
  **4,76:1** (« crème »), **8,16:1** (« contraste ») — et zéro faute sur les
  huit combinaisons thème × largeur, 283 textes mesurés par combinaison.

### 11.4 Le cadre, et la place qu'il prend

Le bandeau portait quinze commandes de premier niveau. Il en porte quatre :
simuler, rafraîchir, et les deux tiroirs (affichage, outils) ; les six outils
secondaires s'ouvrent. Le tour du bandeau passe de 18 px à 14, la marge sous le
bloc de 14 px à 9, l'écart entre la barre et la ligne d'état de 9 px à 5, et les
trois barres de la page partagent la même hauteur de bouton (`--h-bouton`,
34 px — 44 px sur écran tactile) et le même écart (`--gap-barre`).

### 11.5 La présentation, importée du site M.R.S.C.

Le site de l'association propose une « mise en page » : équilibrée, lecture,
panorama. Le simulateur la reprend telle quelle dans son panneau d'affichage :

| Présentation | Largeur | Ce qu'elle sert |
|---|---:|---|
| **Équilibrée** (défaut) | 1440 px | la page telle qu'elle a été dessinée |
| **Lecture** | 1000 px | suivre un texte long sans perdre la ligne |
| **Panorama** | 1680 px | faire tenir les grilles de chiffres côte à côte |

Un seul jeton change (`--largeur-page`) ; les grilles suivent d'elles-mêmes.
Le choix est posé sur `<html data-layout="…">` **avant le premier pixel** (sinon
la page s'ouvrirait à la mauvaise largeur puis sauterait), gardé sur l'appareil,
et jamais envoyé au serveur.

### 11.6 Une densité, un seul réglage

Le ruban de veille portait un bouton « Vue compacte » et le panneau un bouton
« Compact » : deux noms pour un même réglage, qui pouvaient diverger. Ils
s'écrivent maintenant l'un l'autre — dans les deux sens — et l'état est retenu.

### 11.7 Ce qui surveille

| Contrôle | Fichier | Ce qu'il refuse |
|---|---|---:|
| contraste effectif | `tests/test_contraste_ecran.py` (10) | un texte sous le seuil dans l'un des huit cas, une mesure qui ne couvrirait pas la page, un instrument qui deviendrait aveugle |
| cadre des actions | `tests/test_cadre_des_actions.py` (13) | une barre qui regonfle, un outil qui ressort du tiroir, une mesure écrite en clair, une présentation sans largeur ou absente du panneau |
| règles et jetons | `tests/test_themes_en_page.py` (38) | un aplat de marque sans encre, un bandeau peint avec un jeton de marque, un jeton employé mais non défini |
| le geste, exécuté | `tests/navigateur_interface.mjs` (227 étapes) | un réglage qui ne se pose pas, ne se retient pas, ou ne ressort pas du catalogue |

**14 sabotages posés, 14 attrapés.** Trois ont d'abord échappé : le lexique
« sorti » du tiroir par une classe (il était toujours dedans), le doublon de
`const compact` qui n'a été vu que par le harnais — `node --check` passait, le
script levait à l'exécution —, et la densité du panneau, que rien ne vérifiait
avant qu'une étape ne soit ajoutée. C'est le rôle de la campagne : elle a
d'abord trouvé les trous des contrôles, pas celles du code.

## 12. Le douzième incrément : l'aide, le cadre, l'état (14 octobre 2026)

Trois phrases du visiteur, trois chantiers — et une leçon commune : ce qui
gêne à l'écran n'est presque jamais ce qu'on croit mesurer.

> « La bulle d'information occulte le contenu et l'accès aux différents
> boutons ! La bulle devrait uniquement s'afficher quand la souris passe le
> bouton "Affichage" et disparaître quand elle n'est plus dessus. »

### 12.1 Une infobulle explique un contenant, pas ses commandes

L'aide du panneau « Affichage » était accrochée au **tiroir entier**
(`<details data-aide=…>`). Trois conséquences, toutes mesurables :

1. elle se déclenchait **partout dans le panneau ouvert** — le pointeur n'avait
   qu'à entrer dans une des six commandes pour la faire venir ;
2. le gestionnaire de sortie ne la cachait pas tant que le pointeur restait dans
   le porteur (`if (cherche(evenement.relatedTarget)) return;`) : elle restait
   donc affichée **pendant tout l'usage du panneau** ;
3. `positionnerInfobulle` choisissait le dessus de la cible quand le bas ne
   suffisait pas — pour un `<details>` ouvert, « le dessus » est **le panneau
   lui-même**.

La règle écrite maintenant tient en une phrase : *une infobulle cède devant
toute commande que son contenant renferme*, et s'efface dès que ce contenant est
ouvert. Elle vit dans `commandeInterne()` et `estOuvert()`, et le harnais la joue
événement par événement — survol, sortie, focus, tiroir ouvert, champ annoncé.

### 12.2 Ce qu'un état cache

L'outil de contraste écartait les états, et **le disait** : « ce qu'il ne mesure
pas : les règles qui ne s'appliquent qu'à un état ». C'était honnête, et c'était
le trou : un visiteur vit dans ces états-là. `mesurer_etats` les joue :

- pour chaque élément dont la feuille prévoit un état **qui touche une encre ou
  un fond**, une passe est ouverte (l'élément est mis dans cet état, sa
  descendance est mesurée) ;
- une passe **« tout enfoncé »** active toutes les bascules : 19 sur la page
  livrée (`aria-pressed`, onglets de strate, cartes de scénario, filtres de
  classes, sommaire, année de la balance) ;
- les **valeurs écrites dans les champs** et **l'option choisie d'un `select`**
  sont mesurées comme des textes — elles s'affichent.

Deux choix gardent l'outil utile : une règle d'état qui ne pose qu'un contour de
focus n'ouvre **aucune** passe (193 passes pour rien n'auraient rien prouvé,
19 suffisent), et une passe qui ne montre aucun texte n'est pas retenue. Coût :
**2,5 s** par thème et par largeur, contre une minute avec les 193 passes.

**Résultat** : 4 thèmes × 2 largeurs, 19 passes, 587 textes mesurés par
combinaison, **0 faute**. La commande enfoncée, la carte active, l'onglet choisi,
le filtre coché : tout se lit, dans les quatre palettes.

### 12.3 Le cadre qui était plus grand que ses boutons

Le bandeau empilait sur-titre, titre, phrase, puis les quatre commandes. Sa
hauteur était donc celle de son texte **plus** 34 px de commandes **plus** 9 px
de marge — alors que le texte fait déjà deux fois la hauteur des boutons. Dès
900 px, il se lit maintenant en deux colonnes (texte à gauche, commandes à
droite, ligne d'état en dessous) ; en dessous de 900 px, la colonne unique
reprend ses droits et les quatre paliers restent la loi.

### 12.4 Voir, enfin

`outils/captures_ecran.mjs` ouvre la page dans Chromium et la photographie
(4 thèmes × 4 largeurs, panneaux ouverts, états, sections), puis relève en texte
ce qu'un doigt toucherait au centre de chaque commande (`elementFromPoint`) et
la hauteur des cadres. Deux leçons de méthode :

- **une image ne se lit pas par un agent** : le résumé chiffré, lui, passe par
  l'artefact, le rapport de CI et le commentaire de la demande de fusion ;
- **un relevé n'est pas un contrôle** : les contrôles, eux, restent dans
  `tests/` — l'artefact sert à regarder, les tests à refuser.
