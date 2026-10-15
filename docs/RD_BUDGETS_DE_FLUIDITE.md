# R&D — Les plafonds de poids

**Passe du 14 octobre 2026.** Ce document raconte comment le simulateur, qui
savait mesurer sa fluidité, a appris à la **refuser** — et ce qu'un budget de
poids oblige à écrire, à dater et à justifier.

---

## 1. Le constat, par la mesure

`outils/mesurer_fluidite.py` existe depuis la passe « optimisation, fluidité et
lisibilité ». Il mesure, il rapporte, il ne refuse rien. Sur sept passes, la page
a donc grossi d'un cran à chaque fois — et chaque cran était justifié, ce qui est
exactement la façon dont une page devient lente : personne ne décide de la
ralentir, on décide seulement que **ce dernier ajout** en valait la peine.

Mesure du 14 octobre 2026, serveur local, mode hors ligne, octets réellement
transmis après compression (`gzip -6`, le niveau que sert `simulateur/compression.py`) :

| Charge | Brut | Compressé | Ce que c'est |
|---|---:|---:|---|
| la page entière | 465 279 o | **125 284 o** | `index.html`, publié et servi à l'identique |
| le catalogue des leviers | 275 363 o | 44 526 o | 156 leviers, leurs bornes et leurs textes courts |
| une simulation, 5 ans | — | 44 014 o | le va-et-vient de chaque curseur |
| une simulation, 10 ans | — | 48 239 o | le même, horizon double |
| le contexte « instant T » | 99 662 o | 14 330 o | 12 valeurs de référence et leur provenance |
| les nuances institutionnelles | 119 987 o | 21 929 o | 189 identifiants de seuils |
| le registre des objections | 67 185 o | 19 820 o | 24 objections longuement rédigées |
| le lexique | 49 666 o | 13 233 o | 83 termes en français ordinaire |
| les garde-fous | 30 139 o | 7 569 o | les contrôles du modèle |
| les cotations | 12 438 o | 1 725 o | sept lignes |
| l'arithmétique des contre-pouvoirs | 78 084 o | 18 207 o | 31 manœuvres, deux chambres |
| les trajets et battements | 117 238 o | 26 230 o | procédures et fentes non écrites |
| les instances | 33 775 o | 7 795 o | 26 autorités |
| **les bulles, une par levier** | 3 112 907 o | **169 866 o** | tout le texte explicatif — 18 fois la page |

Deux chiffres méritent d'être dits à part :

- **le premier écran** — la page, les sept charges du démarrage et la première
  simulation — pèse **270 501 o compressés**. C'est ce qu'un visiteur paie avant
  de pouvoir bouger son premier curseur, et donc le seul chiffre qui décide s'il
  reste ;
- **le catalogue des bulles** est, à lui seul, **plus d'une fois et demie la page
  entière**. Rien ne l'interdit : il ne pèse qu'au moment où l'on survole un
  levier, et son cache le rend invisible au deuxième appel. Un budget ne l'aurait
  pas supprimé ; il aurait dit **où** la page grossit, au lieu de laisser croire
  qu'elle grossit partout un peu.

Le plan de renforcement (`docs/19`, chantier P2‑4) demandait déjà ce chantier :
« `python3 outils/mesurer_fluidite.py` fixe un budget, et la CI échoue au-delà de
+10 % ». Ce qui manquait n'était pas l'outil de mesure, c'était la limite.

---

## 2. La décision : quatre règles

1. **On budgète ce que paie l'utilisateur** — l'octet **compressé** réellement
   transféré. Personne ne télécharge le fichier décompressé : un plafond posé sur
   les octets du disque mesure la mauvaise grandeur, et vieillit mal le jour où
   l'on passe à brotli.
2. **On ancre avant de plafonner.** Chaque budget porte la mesure datée dont il
   vient ; son plafond vaut cette ancre + une marge de 10 %. Une croissance
   légitime se paie d'un **relèvement d'ancre dans un commit qui l'explique** :
   la revue voit passer le chiffre, au lieu de découvrir un glissement six mois
   plus tard.
3. **Le temps n'est pas budgété.** Une durée dépend de la machine qui mesure : un
   plafond de millisecondes échouerait au hasard sur un serveur d'intégration
   chargé, et une CI qui échoue au hasard cesse d'être lue — c'est précisément
   l'histoire de la CI de ce dépôt (`docs/19`, § 2.1). Les durées restent
   mesurées et rapportées ; elles ne bloquent rien.
4. **Un budget muet n'est pas un budget.** Chaque plafond porte son **motif** (ce
   qu'un dépassement abîmerait) et sa **sortie** (ce qu'on fait s'il est
   franchi). Un plafond sans sortie est une opinion, et une opinion ne se
   vérifie pas.

Une cinquième règle, de comptabilité : **toute route que la page appelle est soit
plafonnée, soit excusée par écrit** — comme le contrôle de couverture des routes
le fait déjà pour les routes non mises en œuvre. Un plafond qui n'existe pas
n'est pas un plafond large : c'est un angle mort.

---

## 3. La table des plafonds

Écrite dans `outils/budgets_fluidite.py` : **seize entrées** — quinze plafonds
directs et un budget dérivé (le premier écran) —, seize ancres datées des 13 et
14 octobre 2026, la marge de 10 % par défaut (20 % pour les cotations, dont la
base — sept lignes — rendrait un plafond trop serré cassant au premier ajout).

### Le relèvement du 14 octobre 2026 (passe « affichage »)

La passe « afficher sans submerger » a **voulu** cette croissance : quatre thèmes
complets, un panneau de réglages, vingt-quatre en-têtes éditoriaux et une échelle
d'espacement branchée. L'ancre de la page passe donc de **111 155 o à
119 995 o** (mesure du `index.html` régénéré, `gzip -6`), son plafond de
**122 271 o à 131 995 o**, et l'ancre du premier écran suit mécaniquement
(256 372 → **265 212 o**, plafond 291 734 o). C'est exactement l'acte de revue
prévu par la règle : une croissance assumée se paie d'un relèvement d'ancre
daté, pas d'un silence.

### Le second relèvement du 14 octobre 2026 (passe « le cadre des actions »)

Même journée, autre raison. Cette passe ajoute la **présentation à trois
largeurs** — équilibrée, lecture, panorama —, la « mise en page » du site
M.R.S.C. transposée au simulateur ; elle resserre le cadre du bandeau (18 px
de tour → 14, 14 px sous le bloc → 9, 9 px entre la barre et la ligne d'état
→ 5) ; elle répare surtout **onze textes illisibles** dans les thèmes clairs.
La page passe de **119 995 o à 123 131 o** compressés — **+2 022 o**, soit
+1,7 % — et son plafond suit mécaniquement : **131 995 o → 135 445 o**. Le
budget dérivé du premier écran suit dans la même proportion
(**265 212 o → 268 348 o**, plafond 295 183 o). La marge reste de 10 %, et
`outils/budgets_fluidite.py` reste le juge.

### Le quatrième relèvement du 14 octobre 2026 (passe « la fenêtre se comporte comme une fenêtre »)

Quatrième et dernier relèvement de la journée : **+1 287 o** (+1,0 %). Ce qui l'a
payé n'est pas une fonctionnalité de plus, c'est une **correction d'accessibilité**.
La fenêtre du lexique et du guide ne prenait pas le focus, ne le retenait pas et
ne le rendait pas : au clavier, la première tabulation menait aux curseurs de la
page, **derrière** la fenêtre ouverte, et la refermer laissait le curseur au pied
du document. Elle reçoit maintenant le focus (`tabindex="-1"` sur le dialogue),
le retient (les six familles de commandes énumérées, tabulation circulaire aux
deux bouts), le rend à qui l'a ouverte — ou, quand personne ne l'a ouverte (le
guide de première visite se montre tout seul), à la commande principale. Échap,
lui, ne ferme plus que ce qui est ouvert.

La page passe de **123 997 o à 125 284 o** compressés (brut 460 870 → 465 279 o),
son plafond de **136 397 o à 137 813 o**, et l'ancre du premier écran suit la
somme de ses membres (**269 214 o → 270 501 o**, plafond 297 552 o). La marge
reste de 10 %, et `outils/budgets_fluidite.py` reste le juge. La table des
plafonds, juste en dessous, porte les valeurs du jour.

Troisième relèvement de la journée, et le plus modeste : **+866 o** (+0,7 %).
Ce qui l'a payé n'est pas une fonctionnalité mais une **mise en page mesurée**.
Le plan coté du bandeau, relevé par Chromium (`outils/captures_ecran.mjs`), a
montré qu'à 1280 px la colonne de texte faisait 528 px de large — le titre y
tenait en **trois lignes** — et qu'il restait **139 px de vide** sous la barre de
commandes : un cadre de 296 px pour 35 px de boutons. Le titre s'étale désormais
sur toute la largeur, la phrase d'accroche et la ligne d'état partagent la
rangée suivante : **248 px** (moins 16 %), sans qu'un mot ait été retiré. La
page passe de **123 131 o à 123 997 o** compressés, son plafond de **135 445 o à
136 397 o**, et l'ancre du premier écran suit (**268 348 o → 269 214 o**, plafond
296 136 o). La marge reste de 10 %, et `outils/budgets_fluidite.py` reste le juge.

| Budget | Ancre | Plafond | Marge |
|---|---:|---:|---:|
| la page entière | 125 284 o | 137 813 o | 12 529 o |
| le catalogue des leviers | 44 526 o | 48 979 o | 4 453 o |
| ce que la page télécharge avant d'être utilisable | 270 501 o | 297 552 o | 27 051 o |
| les bulles | 169 866 o | 186 853 o | 16 987 o |
| une simulation, 10 ans | 48 239 o | 53 063 o | 4 824 o |
| une simulation, 5 ans | 44 014 o | 48 416 o | 4 402 o |
| les trajets et battements | 26 230 o | 28 854 o | 2 624 o |
| les nuances institutionnelles | 21 929 o | 24 122 o | 2 193 o |
| les objections | 19 820 o | 21 802 o | 1 982 o |
| l'arithmétique des contre-pouvoirs | 18 207 o | 20 028 o | 1 821 o |
| la comparaison des scénarios | 9 795 o | 10 775 o | 980 o |
| le contexte « instant T » | 14 329 o | 15 762 o | 1 433 o |
| le lexique | 13 233 o | 14 557 o | 1 324 o |
| les instances | 7 795 o | 8 575 o | 780 o |
| les garde-fous | 7 569 o | 8 326 o | 757 o |
| les cotations | 1 726 o | 2 072 o | 346 o |

**Le budget du premier écran est dérivé**, et plus serré que la somme des
plafonds individuels : si toutes les charges montaient en même temps à leur
maximum, la page qui s'ouvre paierait 282 185 o pour un plafond de 282 010 o.
C'est voulu : un plafond par charge ne protège pas une ouverture, il protège des
charges. Le contrôle correspondant est écrit, et il mord.

### Ce qui n'est pas plafonné, et pourquoi

Cinq routes appelées par la page restent sans plafond individuel. Chacune porte
sa raison dans `ROUTES_SANS_PLAFOND`, et le contrôle refuse une excuse périmée —
une raison qui ne tient plus parce que la page n'appelle plus la route :

| Route | Pourquoi aucun plafond individuel |
|---|---|
| `bulle` | une bulle unitaire, ouverte au survol : quelques centaines d'octets, déjà couverts en bloc par le plafond du catalogue des bulles |
| `conseil` | la réponse du conseiller temps réel : une phrase par ricochet, dimensionnée par le réglage et non par la page |
| `constitution` | une fiche d'article ouverte au clic : son poids est celui du droit qu'elle cite — un plafond ici plafonnerait la loi |
| `donnees` | les données publiques collectées à la demande : leur volume appartient aux sources interrogées, pas à cette page |
| `run` | le rapport complet d'une exécution, demandé à la main et jamais au chargement : le plafonner reviendrait à plafonner ce que l'utilisateur a demandé |

---

## 4. Ce qui surveille cette table

### Ce que ces plafonds ne voyaient pas : le document brut, la part du script, et qui la page appelle (15 octobre 2026)

Une mesure de poids compressé répond à « combien le réseau transporte ». Elle ne
répond pas à deux questions qu'un téléphone pose, lui :

1. **combien il décompresse et analyse.** Mesuré ce jour : **479 190 o bruts** pour
   **129 701 o** transférés — la compression fait gagner le réseau, jamais la
   mémoire de l'appareil. Le document brut a donc un plafond à lui,
   **505 000 o**, dans `outils/poids_de_la_page.py` ;
2. **quelle part du document est du programme.** Le script en ligne pèse
   **318 344 o**, soit **66,4 %** de la page : non cacheable séparément, non
   différable, payé à chaque visite même pour lire trois lignes. Le plafond écrit
   est **les trois quarts du document** (72 %) : au-delà, la question n'est plus
   « faut-il découper ? » mais « pourquoi ne l'a-t-on pas fait ? » ;
3. **qui la page appelle.** Ni police distante, ni CDN, ni image ailleurs : un
   outil citoyen qui tire une ressource chez un tiers lui dit qui le lit. Le seul
   appel est `/_vercel/insights/script.js`, **en même origine** et en `defer` ;
   toute autre sous-ressource doit être **déclarée** avec sa raison, et une
   sous-ressource d'un domaine tiers fait rougir.

**Et surtout : un seul juge par grandeur.** Ces deux plafonds-là ne touchent pas
au poids transféré, qui reste tenu par la table ci-dessus : `outils/
poids_de_la_page.py` **lit** l'ancre et le plafond de la page dans
`outils/budgets_fluidite.py` et publie la réserve du jour (**8 112 o**, soit 5,9 %
du plafond ; les 518 o de cette passe sont dedans). Il n'y a donc pas deux avis
sur le même nombre — il y en a un, et un contrôle refuse qu'un second
apparaisse.

**Ce que le visiteur, lui, peut vérifier.** Le bloc 6 de l'audit, « Ce que cette
visite a coûté : la page se pèse devant vous », lit
`performance.getEntriesByType('navigation')` et affiche pour **cette** visite :
transféré, décompressé et analysé, ressources appelées et leur origine, premier
octet et page rendue. Aucun chiffre n'est écrit d'avance ; quand le navigateur ne
publie rien, le bloc l'écrit au lieu d'estimer. C'est la seule mesure de poids
qu'un lecteur peut contrôler lui-même — et elle rend publique la promesse
d'autonomie, au lieu de la laisser dans un fichier de configuration.

### 45 contrôles (`tests/test_budgets_fluidite.py`)

Quatre familles, dans l'ordre où elles protègent :

1. **la table est honnête** — un motif et une sortie par plafond (≥ 40 caractères
   chacun), des clés uniques, une date d'ancrage ISO ni future ni antérieure au
   projet, une marge dans `[5 %, 40 %]`, un plafond **calculé** (ancre × marge,
   arrondi à l'octet supérieur) et jamais recopié, un budget dérivé égal à la
   somme de ses membres, aucun membre non déclaré ;
2. **la page d'aujourd'hui tient** — les deux exemplaires du document (celui que
   le serveur tient en mémoire et le fichier `index.html` publié) sont pesés
   **sans lancer de serveur**, à chaque poussée de la CI ; la mesure retenue est
   la plus lourde des deux, ce qui est vérifié ; l'ancre de la page n'est pas
   périmée (elle ne vaut pas plus du double de ce qui est servi) ;
3. **aucune charge n'échappe au budget** — le plan de mesure et la table des
   plafonds se répondent charge par charge (aucune charge mesurée sans plafond,
   aucun plafond sans mesure), chaque route appelée par la page est plafonnée ou
   excusée, aucune excuse n'est périmée, aucune route n'est à la fois plafonnée
   et excusée ;
4. **le vérificateur refuse vraiment** — un octet au-dessus du plafond suffit,
   le plafond atteint n'est pas un dépassement, une charge mesurée sans plafond
   est une anomalie, une mesure en double aussi, un budget dérivé incomplet
   aussi, et la ligne de commande sort en **0** (tenu), **1** (plafond franchi)
   ou **2** (entrée illisible) — c'est ce code que la CI lit.

### 10 sabotages, 10 attrapés

Chaque contrôle a été cassé exprès, un par un, dans une copie du dépôt :

| Sabotage | Contrôle qui l'attrape |
|---|---|
| le plafond de la page rabaissé sous le poids servi | la page tient dans son plafond |
| un motif mis à vide | motif et sortie obligatoires |
| la marge par défaut portée à 80 % | marge dans la fourchette utile |
| le plafond recopié (ancre + 1 000) au lieu d'être calculé | le plafond se calcule |
| une charge ajoutée au plan de mesure sans plafond | toute charge mesurée a un plafond |
| une excuse posée pour une route que la page n'appelle pas | aucune excuse périmée |
| un vérificateur qui ne refuse plus rien | la ligne de commande sort en 1 |
| une route mesurée deux fois | pas de doublon dans le plan |
| un budget dérivé décroché de ses membres | le dérivé est la somme des membres |
| la mesure hors ligne retenant le plus léger exemplaire | la mesure retient le plus lourd |

**Trois de ces sabotages sont attrapés d'abord par le contrôle du document**,
celui qui exige que les ancres et les plafonds annoncés soient ceux du code. Le
document ayant été mis à jour en même temps que le code — ce que ferait un
saboteur soigneux —, les contrôles de fond mordent à leur tour ; vérifié le
14 octobre 2026 : le plafond de la page rabaissé (`test_la_page_tient_dans_son_plafond`,
6 échecs), la marge portée à 80 % (`test_les_marges_sont_dans_la_fourchette_utile`,
31 échecs), le plafond recopié (`test_le_plafond_se_calcule_et_ne_se_recopie_pas`,
36 échecs).

### Dans la CI, à chaque poussée

- **les tests** mesurent hors ligne la page et refusent un dépassement, sans
  serveur : c'est le contrôle payé à chaque exécution de la suite ;
- **une étape dédiée** (`smoke-test`) exécute
  `python3 outils/mesurer_fluidite.py --verifier --repetitions 1` : elle sert le
  simulateur sur un port libre, mesure les seize charges et échoue sur la
  première qui franchit son plafond. Le tableau qu'elle imprime porte les ancres,
  les plafonds, la marge restante et, en cas de refus, le motif et la sortie.

---

## 5. Ce que ces plafonds ne disent pas

- **Ils ne disent rien du rendu.** Le poids transféré n'est pas le coût
  d'affichage : une page légère peut être lente à peindre si son JavaScript
  construit 40 000 nœuds. La limite connue reste celle de `docs/19`, § 5 : la CI
  n'a pas de vrai navigateur.
- **Ils ne mesurent pas le temps.** Voir la règle 3 : les durées sont mesurées,
  rapportées, jamais bloquantes.
- **Ils dépendent d'un geste humain : le relèvement d'ancre.** Un budget ne peut
  pas empêcher quelqu'un de relever les seize ancres dans le même commit. Ce
  qu'il garantit, c'est que ce geste soit **visible, daté et commentable** — la
  garantie est celle de la revue, pas celle du test.
- **L'unité est `gzip -6`.** Sur un interpréteur qui fournit brotli, le serveur
  fait mieux que le plafond : le budget est donc conservateur, jamais complaisant.
- **Quelques octets bougent tout seuls.** Une valeur du contexte ou des cotations
  peut varier d'un octet entre deux mesures : c'est pourquoi les plafonds portent
  des marges, et pourquoi le contrôle du jour est un plafond et non une égalité.

---

## 6. Reste ouvert

1. **Budgéter le temps, autrement.** Une durée absolue ne se plafonne pas ; un
   **rapport** se plafonne. Par exemple : le deuxième appel au catalogue des
   bulles doit rester au moins cinq fois plus rapide que le premier (c'est le
   cache), et une simulation de 10 ans ne doit pas coûter plus du double d'une
   simulation de 5 ans. Ces rapports-là sont mesurables, stables, et
   attrapables par un sabotage — à instruire.
2. **Découper `/api/bulles` en pages** (`docs/RD_OPTIMISATION_FLUIDITE.md`,
   suite envisagée n° 3). Le plafond ne règle pas le premier appel à froid : il
   rend seulement la question visible et chiffrée.
3. ~~**Afficher le poids réellement transféré à l'écran**~~ — **fait le
   15 octobre 2026** : bloc 6 de l'audit, « Ce que cette visite a coûté : la page
   se pèse devant vous ». `performance.getEntriesByType('navigation')[0]` donne
   le poids transféré, le poids décompressé, les ressources appelées et leur
   origine, le premier octet et la page rendue. **Aucun chiffre écrit d'avance**
   (un contrôle refuse tout poids en dur), et le silence est préféré à
   l'estimation quand le navigateur ne publie rien. Reste ouvert : ce que le
   **cache** fait gagner d'une visite à l'autre, que seul un relevé successif
   montrerait.
4. **Plafonner les routes d'appoint** (`bulle`, `conseil`, `donnees`, `run`,
   `constitution`) le jour où l'une d'elles deviendra lourde : aujourd'hui elles
   sont excusées avec leur raison, et le contrôle refusera de laisser une raison
   périmée dans le fichier.
