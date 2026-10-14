# Changelog

Toutes les modifications notables de ce projet sont documentées ici.
Format basisé sur [Keep a Changelog](https://keepachangelog.com/),
et ce projet suit [Semantic Versioning](https://semver.org/).

## [Non publié]

### L'aide cède devant ses commandes, et le contraste se mesure dans les états (14 octobre 2026)

- **La bulle qui cachait le panneau.** Le visiteur l'a décrit exactement : « la bulle du menu Affichage occulte le contenu et l'accès aux boutons ». Trois causes : l'aide était accrochée au **tiroir entier** (`<details data-aide=…>`) et non à son bouton, donc elle se déclenchait partout dans le panneau ouvert ; tant que le pointeur restait dans le porteur, **elle ne partait pas** ; et faute de place en dessous, elle se posait **au-dessus de sa cible** — c'est-à-dire sur le panneau qu'on venait d'ouvrir. Elle descend sur le `<summary>` (Affichage, Outils), **cède devant toute commande** que son porteur renferme, s'efface quand le tiroir est ouvert, et cherche trois placements (sous, dessus, collé au bas de l'écran) sans jamais recouvrir sa commande. Deux aides de plus passent du contenant à leur mot : l'étiquette « Horizon » et la case « Vue compacte ».
- **Le contraste des états, désormais mesuré.** L'outil écartait les règles de survol, de focus et d'enfoncement : c'était écrit, et c'était le trou — un visiteur vit dans ces états. Il les joue maintenant : chaque élément qui porte un état dans la feuille, plus une passe **« tout enfoncé »** où chaque bascule est activée (19 sur la page livrée : `aria-pressed`, onglets, cartes de scénario, filtres, sommaire). Les **valeurs écrites dans les champs** et **l'option choisie d'un `<select>`** comptent comme les textes qu'elles sont. **19 passes et 587 textes par combinaison, 0 faute sur les 4 thèmes × 2 largeurs.** Une règle d'état qui ne touche ni encre ni fond (un contour de focus) n'ouvre aucune passe : 193 passes inutiles ne prouveraient rien là où 19 suffisent — et 2,5 s par combinaison au lieu d'une minute.
- **Le cadre épouse ses commandes.** Le bandeau passe en **deux colonnes dès 900 px** : sur-titre, titre et phrase d'un côté, les quatre commandes de l'autre. Empilées, elles ajoutaient 34 px de hauteur et 9 px de marge sous un bloc de texte deux fois plus haut qu'elles. Le sommaire des accès rapides se règle sur les jetons (`--e-1 var(--e-2)`, `--gap-barre`) au lieu de valeurs à lui.
- **Des yeux, et une mesure qui se lit.** `outils/captures_ecran.mjs` ouvre la page dans Chromium (`.github/workflows/captures.yml`) : 4 thèmes × 4 largeurs, panneaux ouverts, états, sections. Il relève **ce qu'un doigt toucherait au centre de chaque commande** (`elementFromPoint`) — « la bulle occulte l'accès aux boutons », posée en une ligne — et publie son résumé (hauteurs des cadres, commandes recouvertes, débordement horizontal) dans l'artefact, dans le rapport de CI et en commentaire de la demande de fusion. Les images se regardent ; les chiffres se lisent sans navigateur.
- **Ce qui surveille** : **21 contrôles de cadre** (`tests/test_cadre_des_actions.py`, dont cinq sur l'aide et trois sur le bandeau en deux colonnes), **16 contrôles de contraste effectif** dont six sur les états, **235 étapes** de harnais (huit neuves jouent la souris événement par événement : la doublure du document retient ses écouteurs et connaît `closest`, `contains` et les rectangles).
- **Le coût, relevé et daté** : la page passe de **122 046 o à 123 131 o** compressés ; l'ancre est relevée dans ce commit (**plafond 135 445 o**), celle du premier écran suit (**268 348 o**, plafond 295 183 o).

### Le cadre des actions : les couleurs suivent le fond, les commandes se rangent (14 octobre 2026)

- **Le défaut a été trouvé par la mesure, pas par l'œil.** En thème « jour » et « crème », le bandeau peignait le bleu M.R.S.C. et **l'encre s'héritait du thème** : titre à **1,27:1**, phrase d'accroche à **1,64:1**, boutons « Simuler », « Rafraîchir », « Réinitialiser les leviers », « Régler les leviers » et numéros de chapitre à **1,27:1** — **onze textes illisibles** par thème clair. Les 36 contrôles de règles ne pouvaient pas le voir : chacun mesure une règle seule, jamais l'héritage.
- **`outils/contraste_ecran.py` (neuf) fait le travail du navigateur** : arbre de la page servie, cascade et spécificité, héritage des jetons, `var()`, `color-mix()`, `@media` selon la largeur (1280 et 380 px), dégradés et opacités composés, puis la formule WCAG 2.1 sur **tout texte** — 283 textes par thème sur un grand écran, 265 sur un écran de poche. Il **compte ce qu'il écarte** (règles d'état, commandes inactives) au lieu de le taire. Après réparation : **0 faute sur les huit combinaisons**, le pire cas mesuré étant **4,58:1** (soir), **4,62:1** (jour), **4,76:1** (crème), **8,16:1** (contraste).
- **Ce qui répare** : le bandeau, le bouton principal, l'onglet actif et le numéro de chapitre **écrivent leur encre** là où ils peignent un aplat de marque (`--sur-mrsc`), et le texte secondaire du thème « jour » passe de `#5a6980` à `#56637a` — les libellés des plateaux de la balance remontent de **4,34:1 à 4,73:1**, le ruban de coût de **4,38:1 à 4,74:1**.
- **Le cadre ne prend plus plus de place que ses boutons** : tour du bandeau **18 px → 14 px**, marge sous le bloc **14 px → 9 px**, écart barre → ligne d'état **9 px → 5 px**. Les trois barres de la page partagent la même hauteur de bouton (`--h-bouton`, 34 px — 44 px sur écran tactile) et le même écart (`--gap-barre`), les pastilles se contentent de 3 px de cadre, et les six outils secondaires (lexique, guide, partage, deux exports, remise à zéro) vivent dans un tiroir « Outils » qui s'ouvre au lieu de peser à chaque visite.
- **La présentation, comme la « mise en page » du site M.R.S.C.** : trois choix — **Équilibrée** (1440 px), **Lecture** (1000 px, pour suivre un texte long), **Panorama** (1680 px, pour les grilles de chiffres) — posés sur `<html data-layout="…">` **avant le premier pixel**, gardés sur l'appareil, jamais envoyés. Un seul jeton change (`--largeur-page`) : les grilles suivent d'elles-mêmes, puisqu'elles se règlent sur la place disponible.
- **Une densité, un seul réglage** : le bouton « Vue compacte » du ruban et le bouton « Compact » du panneau disent désormais la même chose, dans les deux sens — deux boutons qui portent le même nom ne peuvent pas annoncer deux états.
- **Ce qui surveille** : **38 contrôles** statiques (`tests/test_themes_en_page.py`), **10 contrôles de contraste effectif** (`tests/test_contraste_ecran.py`, neuf — dont quatre pages d'essai qui éprouvent l'instrument lui-même), **13 contrôles de cadre** (`tests/test_cadre_des_actions.py`, neuf), **227 étapes** dans le harnais navigateur et **14 sabotages posés, 14 attrapés**.
- **Le coût, relevé et daté** : la page passe de **119 995 o à 122 046 o** compressés (+2 051 o) ; l'ancre est relevée dans ce commit (**plafond 134 251 o**) et celle du premier écran suit (**267 263 o**, plafond 293 990 o).
- **`rd`** : le onzième incrément de `docs/RD_AFFICHAGE_THEMES_ET_MOBILE.md` et le treizième de `docs/RD_VISUEL_RESPONSIVE.md`.

### Afficher sans submerger : quatre thèmes, une ligne éditoriale, un écran de poche (14 octobre 2026)

- **La page ne laissait aucun choix et expliquait dans ses titres.** Un seul thème (sombre), une seule densité, aucune taille de texte — et les vingt-quatre explications de section vivaient **dans le `h2`**, dans un corps plus petit. La demande était double : ne plus submerger, et laisser le visiteur choisir.
- **Quatre thèmes complets** — **soir** (défaut d'origine), **jour** (la charte M.R.S.C. : `#f5f7fa`, `#18243b`, `#2958a2`, `#456d29`), **crème** (papier chaud, longues lectures) et **contraste renforcé** (noir pur, texte à 21:1). **47 jetons aux mêmes noms** dans les quatre : un jeton manquant dans un seul thème ferait tomber une règle dans le vide, et un contrôle compare les **noms**, jamais les valeurs.
- **Le défaut est le réglage de l'appareil, le choix du visiteur gagne toujours.** Le thème est posé **avant le premier pixel** par un script d'en-tête (sinon la page s'ouvre sombre et bascule en clair sous les yeux), gardé dans `localStorage`, et **rien ne part au serveur** — aucun `fetch` dans les fonctions de réglage. `prefers-color-scheme` n'entre pas dans la feuille de style : une media query CSS aurait écrasé un choix explicite. Un contrôle le refuse.
- **La ligne éditoriale du site M.R.S.C., relevée puis appliquée** : vingt-quatre sections en trois temps — un sur-titre en majuscules précédé du **trait vert de 25 × 3 px** de la charte, un titre, une phrase. L'explication a quitté les titres, les phrases sont devenues des phrases (majuscule, ponctuation — vérifié sur les 24), et l'**échelle d'espacement est enfin branchée** : elle était déclarée depuis la passe précédente sans qu'aucune règle ne l'emploie, un contrôle refuse désormais un jeton déclaré mais jamais utilisé.
- **Le contraste n'est pas jugé, il est calculé.** `outils/couleurs.py` donne les rapports WCAG 2.1, et un contrôle mesure **la feuille elle-même** : chaque règle qui écrit une couleur de texte est résolue depuis la palette du thème et posée sur le fond réel qu'elle reçoit. Le pire cas mesuré est passé de **3,76:1** à **5,10:1**. Trois vraies erreurs sont tombées : l'encre blanche figée sur la strate hors-sol (**3,76:1** en soir, **2,02:1** en contraste), le texte de l'onglet actif sur son dégradé de marque (**1,06:1** en contraste), et le rouge employé en petit texte (**4,04:1** en soir). Deux jetons neufs les réparent : **`--encre-pleine`** (l'encre qui tranche sur une surface vive, sombre dans un thème sombre, claire dans un thème clair) et **`--sur-mrsc`** (l'encre du bandeau de marque, claire dans les quatre thèmes puisque le bandeau reste sombre).
- **Le téléphone** : le panneau « Affichage » se replie en **feuille fixée en bas** sous 640 px (défilement qui retient son geste, cibles de 44 px, hauteur bornée) ; **cinq tailles de texte** (87 → 137 %) agrandissent les `rem` sans jamais toucher au plancher, qui reste en pixels (`--t-min:12.5px`) ; la densité ne change que trois jetons (`--pad-bloc`, `--ecart-section`, `--ecart-carte`), donc aucune règle ne peut l'oublier. Les quatre paliers, les cibles tactiles et les tableaux en cartes restent verts.
- **Deux vrai défauts trouvés au passage** : la phrase d'introduction de la matrice portait un `<span id="matrice-fraicheur">` **jamais fermé** (61 balises ouvertes pour 60 fermées), signalé par le contrôle qui compte les en-têtes éditoriaux — 23 reconnus sur 24 ; et les deux plateaux de la balance lisaient `--classe-recettes-fond` et `--classe-depenses-fond`, **disparus d'une réécriture de palette** — un navigateur ne se plaint pas d'une variable absente, le fond devenait transparent. Les deux jetons sont rétablis dans les quatre thèmes, leur repli **vaut exactement** ce que `color-mix` calcule, et la proportion est passée de 14 % à **12 %** : à 14 %, le texte secondaire du thème « jour » tombait à 4,49:1 sur le plateau des recettes.
- **Ce qui surveille** : **36 contrôles** statiques (`tests/test_themes_en_page.py`), **20 contrôles** de l'atelier de couleurs, **15 étapes neuves** dans le harnais navigateur (214 au total : le thème posé avant le rendu, l'appareil clair qui reçoit le clair, le choix gardé puis relu, `aria-pressed` qui suit, les bornes de la taille) et **22 sabotages posés, 22 attrapés** (18 sur la feuille, 4 sur le comportement).
- **Le coût, assumé et ancré** : la page passe de 418 912 à **439 540 caractères**, soit **119 995 octets compressés** — l'ancre de la page est **relevée dans ce commit** (plafond 131 995 o), et celle du budget de premier écran suit (265 212 o → plafond 291 734 o). Une croissance voulue se paie d'un relèvement d'ancre daté et expliqué, pas d'un silence.
- **`rd`** : `docs/RD_AFFICHAGE_THEMES_ET_MOBILE.md` (relevé de la charte, choix des palettes, table des contrastes mesurés, coûts, sabotages, limites assumées) et le douzième incrément de `docs/RD_VISUEL_RESPONSIVE.md`.

### Comparer les scénarios : la route servait seize simulations, la page n'en montrait aucune (14 octobre 2026)

- **Une excuse qui ne tenait pas.** Le contrôle de couverture excusait `/api/comparer` par écrit : « les préréglages se rejouent un par un dans la grille des scénarios, ce qui donne le même chiffre sans un second calcul complet ». En relisant la phrase : la grille montre les **11 scénarios historiques**, la comparaison porte sur les **16 préréglages** (austérité, justice sociale, transition écologique, verrouillage par le haut…) — deux catalogues, deux usages. Et les 300 ms supposées dissuasives sont **283 ms** mesurées, pour **73 768 octets bruts / 9 795 compressés** : moins lourde que les contre-pouvoirs, affichés la veille.
- **La section « Comparer »** : un vrai `<table>` de seize lignes et cinq colonnes chiffrées (solde des mesures en Md€/an, dette et déficit en points de PIB, risque population sur 100, nombre de seuils en alerte), une barre par solde mesurée sur **le plus fort montant servi**, verte quand le scénario dégage, rouge quand il coûte — les deux variables de la classe (`--classe-recettes`, `--classe-depenses`), jamais deux hexadécimaux de plus. La couleur ne parle pas seule : le signe et l'unité sont écrits à côté de chaque barre, qui est `aria-hidden`.
- **Un rangement à trois états** : un clic range la colonne en croissant, un second en décroissant, un troisième rend l'ordre du catalogue. `aria-sort` porte l'état, le titre est un `<button>` (un titre cliquable qui n'est pas un bouton n'existe pas au clavier), et **ranger n'est pas calculer** : le tri lit les valeurs servies sans en produire aucune.
- **Rien n'est recopié** : un contrôle statique refuse les **39 valeurs chiffrées du jour** (« 41,6 », « −474,0 », « 141,0 »…) et les **16 libellés de scénarios** — le contexte « instant T » entre dans chaque simulation, donc ces chiffres bougent d'un mois à l'autre. Un autre contrôle refuse toute opération sur les valeurs reçues (`toFixed`, `parseFloat`, `Math.pow/sqrt/log`).
- **Elle ne coûte rien au démarrage** : chargement à l'approche de l'écran (`IntersectionObserver`, marge de 400 px) avec bouton « Charger maintenant ». Le budget du premier écran reste tenu, et son contrôle vérifie que la comparaison n'entre pas dans ses membres. La route est **entrée au budget de poids le jour même** : ancre 9 795 o, plafond 10 775 o — une charge qui entre à l'écran entre au budget.
- **Ce qui la surveille** : **31 contrôles** statiques (`tests/test_comparer_en_page.py`), **10 étapes** dans le harnais navigateur (les 16 lignes rendues, le montant servi retrouvé **dans sa propre ligne** pour le scénario le plus coûteux, sa barre vérifiée au rapport servi, le repère de référence unique, les trois états du tri, un **scénario hostile** qui reste du texte), et **10 sabotages posés, 10 attrapés**.
- **Un contrôle a attrapé une vraie erreur le jour même** : le bloc JavaScript inséré *après* l'accolade ouvrante de la fonction suivante restait du JavaScript valide — `node --check` passait — mais les `let` devenaient locaux et la section restait muette. Le contrôle regarde la structure (le bloc commence et finit une ligne), pas la syntaxe.
- **`rd`** : `docs/RD_COMPARER_LES_SCENARIOS.md` (constat chiffré, décisions, coûts, sabotages, ce qu'un tableau comparatif ne peut pas dire) ; `docs/RD_CONTREPOUVOIRS_EN_PAGE.md` corrigé sur ses comptes (**16 routes mises en œuvre, 6 excusées**) et daté ; l'excuse de `/api/comparer` retirée du contrôle de couverture.

### Des plafonds de poids, mesurés et refusés (14 octobre 2026)

- **Le dépôt savait mesurer sa fluidité ; il ne savait pas la refuser.** `outils/mesurer_fluidite.py` existe depuis la passe « optimisation » et ne refusait rien : sur sept passes, la page a grossi d'un cran justifié à chaque fois — c'est exactement ainsi qu'une page devient lente. Mesure du 14 octobre 2026, en octets **compressés réellement transmis** : la page **111 155 o**, **ce que le premier écran télécharge 256 372 o**, et le catalogue des bulles **169 866 o** — trois mégaoctets bruts, une fois et demie la page entière, pour le texte explicatif des 156 leviers.
- **Quinze plafonds écrits, datés et motivés** (`outils/budgets_fluidite.py`) : chaque budget porte l'ancre du 14 octobre 2026 dont il vient, une marge de 10 %, **son motif** (ce qu'un dépassement abîmerait) et **sa sortie** (ce qu'on fait s'il est franchi). Le budget du premier écran est **dérivé** de huit charges et tombe plus tôt que la somme de leurs plafonds — 282 010 o contre 282 185 o : un plafond par charge ne protège pas une ouverture.
- **Quatre règles, dont deux qui se discutent** : on budgète l'octet compressé, jamais celui du disque (personne ne télécharge le fichier décompressé) ; on ancre avant de plafonner, pour qu'une croissance voulue se paie d'un relèvement d'ancre dans un commit qui l'explique ; **le temps n'est pas budgété**, car une durée dépend de la machine qui mesure et une CI qui échoue au hasard cesse d'être lue ; et un budget muet n'est pas un budget.
- **Aucune charge sans plafond ni excuse** : les cinq routes appelées par la page et volontairement non plafonnées (`bulle`, `conseil`, `constitution`, `donnees`, `run`) portent leur raison par écrit, et le contrôle refuse une **excuse périmée** — comme le contrôle de couverture le fait pour les routes non mises en œuvre.
- **Ce qui surveille** : **45 contrôles** (`tests/test_budgets_fluidite.py`), dont la pesée de la page **sans lancer de serveur** à chaque poussée ; **une étape de CI** (`--verifier`, code **0** tenu / **1** plafond franchi / **2** entrée illisible) qui sert le simulateur sur un port libre et mesure les quinze charges ; et **10 sabotages posés, 10 attrapés**.
- **`rd`** : `docs/RD_BUDGETS_DE_FLUIDITE.md` — le constat chiffré, les règles, la table, et ce qu'un plafond ne peut pas garantir : le relèvement d'ancre reste un acte de revue humaine, pas un contrôle automatique.

### Les contre-pouvoirs entrent dans la page : ce que le moteur servait sans écran

- **Le trou n'était pas dans un document, il était dans ce que personne ne regardait.** Le moteur sert **22 routes** ; la page en mettait en œuvre **14**. Un contrôle neuf (`tests/test_couverture_des_routes.py`) fait désormais la comptabilité : chaque route servie est soit utilisée par la page — un `fetch`, ou un lien donné au lecteur, comme les fiches de droit positif —, soit **excusée par écrit**, avec la raison et le nom de ce qui la remplace. Il refuse une excuse périmée, une excuse sans raison, une excuse portant sur une route disparue, et une citation prise pour un usage.
- **Ce qu'il a trouvé** : trois registres entiers, calculés et testés côté moteur, sans aucun écran — `/api/contrepouvoirs` (78 084 o), `/api/dynamiques` (117 238 o) et `/api/instances` (33 775 o). Ajoutés avec le contrepouvoir, le registre des objections et les nuances institutionnelles, ils n'avaient jamais suivi jusqu'à l'interface.
- **La section « Contre-pouvoirs, en chiffres »** affiche les deux premiers, juste après les verrous : l'état daté des assemblées, une barre de sièges par chambre (12 groupes à l'Assemblée, 10 au Sénat, teintes calculées), les seuils de la chambre, **une coalition qui se compose** (cocher des formations additionne leurs sièges et dit quels seuils la somme atteint, et combien de voix manquent), puis les **31 manœuvres** famille par famille avec leurs seuils chiffrés (`577 → 289 voix`), les citations d'articles liées à leur fiche, et le **temps des procédures** : quatre sens (avancer 19 battements/289 jours, reculer 2/43, bloquer 11/113, verrouiller 15/205), la fenêtre résiduelle datée, l'asymétrie, les 8 trajets battement par battement, les 12 fentes non écrites, les 15 stratégies, les 26 autorités, les 7 boucles de contrôle, les 6 étages et les 8 effets d'un juge.
- **Aucun chiffre n'est recalculé dans le navigateur** : aucun seuil du droit positif n'est écrit dans le source de la page, aucun nom de formation non plus — deux contrôles statiques le refusent. Et quand un registre ne répond pas, la page dit l'absence au lieu d'afficher des nombres recomposés.
- **Elle ne coûte rien au démarrage** : les deux routes (195 322 o bruts, **44 108 o compressés**) se chargent quand la section approche de l'écran, avec un bouton « Charger maintenant » pour les navigateurs sans observateur. Le code de la section ajoute pour sa part 7 603 octets compressés à la page, payés une fois.
- **Ce qui la surveille** : 11 contrôles de couverture, 17 contrôles statiques de la section, **13 étapes neuves dans le harnais navigateur** (les fiches rendues, les jours servis, la coalition RN + EPR + SOC + LFI-NFP = 349 sièges, les phrases de seuil qui suivent le calcul, le filtre par famille, et un **registre hostile** dont les balises ne doivent pas s'ouvrir) — et **7 sabotages posés, 7 attrapés**.
- **`rd`** : la onzième passe visuelle (`docs/RD_VISUEL_RESPONSIVE.md` : barre proportionnelle, dépliants, filtres `aria-pressed`, palier de 640 px) et le document du chantier (`docs/RD_CONTREPOUVOIRS_EN_PAGE.md`, avec ses limites assumées).
### Le colis M.R.S.C sort du dépôt (13 octobre 2026)

- **Ce dépôt est le simulateur ; il n'est pas le site de l'association.** Le dossier `livraison-mrsc/` (2,2 Mo, 5 fichiers) n'était qu'une **enveloppe de transport** vers `thejmimiia-code/MRSC` — un autre dépôt, avec ses propres permissions et son propre atelier. Rien ici n'en dépendait : ni le code, ni l'API, ni la CI, ni les tests ; le balayage de licence l'excluait même explicitement (« diffs d'un autre dépôt »). Il est retiré.
- **Ce qui part, nommément** : le correctif du site (`simulateur-securite-mrsc.patch`), le diff de repli `maj-site-e1dc6a6.patch` (2,1 Mo), le script `publier-mrsc.sh`, le mode d'emploi et le message de fusion.
- **Ce qui reste, et qui n'était pas visé** : l'**identité du projet** — le sigle M.R.S.C, le logo, le lien vers le site, la mention « valeur citoyenne non vérifiée par le M.R.S.C », l'attribution des crédits. Une quinzaine de fichiers la portent ; aucun n'est touché. C'est la signature du simulateur, pas une pièce de transport.
- **Rien n'est perdu** : le dossier reste dans l'historique Git, récupérable à tout moment à l'octet près — `git show 4b15284:livraison-mrsc/LISEZ-MOI.md`.
- **Le contrôle de licence s'allège d'autant** : `tests/test_licence_du_depot.py` portait une exemption (« ne pas lire les correctifs du colis ») devenue sans objet ; elle est retirée, la suite reste verte.

### Le colis M.R.S.C rejoué sur le moteur du soir

- **Le colis était figé sur `7d600de`** alors que le moteur avait bougé de deux fichiers utiles à la copie du site : `simulateur/interface.py` (le nom des régions défilantes suit la taille de l'écran) et `simulateur/surface_publique.py` (la licence lue dans `LICENSE`). Appliqué tel quel, le site aurait reçu un moteur amputé de ces deux correctifs — sans que rien ne le signale, puisque le reste des 42 fichiers était identique.
- **Rejoué en entier sur le sommet de `main`** (`e1dc6a6`) : copie du moteur, application du correctif du site, reconstruction de la page et des fonctions `api/`, rejeu de la CI du site, contrôles de la copie publiée. Tout est vert : les **16 protections** du site sont présentes, aucun marqueur de conflit, la page reconstruite fait **374 967 caractères** (contre 371 160), ses trois scripts JavaScript passent `node --check` et ses données structurées sont du JSON valide.
- **Le rebasage du correctif n'a pas eu à être refait** : sa version (`58bc2a21…`) s'applique toujours au moteur du jour — avec des décalages de lignes dans `interface.py`, aucun conflit. C'est pourtant le fichier où les deux chantiers se croisent : l'amont y a ajouté le nom des régions défilantes, le site y garde ses durcissements.
- **Le nouveau diff de repli**, `maj-site-e1dc6a6.patch` (2,1 Mo, 42 fichiers, SHA-256 `8afe241a…`), a été **vérifié sur un clone neuf du site** (`main` = `3f1c6ec`) : il s'applique, et après application `py_compile`, `construire-simulateur --verifier`, `verifier-site-statique`, `verifier-securite` et `verifier-integration` sont verts.
- **Reste la dernière marche, qui n'appartient pas à cet atelier** : le compte d'ici ne peut pas écrire dans `thejmimiia-code/MRSC` (`403`). La copie est faite, vérifiée et committée ; il faut la pousser depuis un compte autorisé — une commande, décrite dans `livraison-mrsc/LISEZ-MOI.md`.

> **Suite, 13 octobre 2026.** Le dossier `livraison-mrsc/` n'est plus dans le
> dépôt (entrée du même jour, plus haut) : les chemins cités ici ne s'y trouvent
> plus, et ne sont plus à suivre.

### La documentation et les détails du dépôt remis à jour

- **Les documents cessaient d'être vrais à deux endroits**, et c'est le plus coûteux : `docs/AUDIT_PR_CORRECTIONS.md` affirmait que `LICENSE` et le classificateur MIT (l'inverse est vrai — GPL-3.0), et `docs/19_PLAN_DE_RENFORCEMENT_ET_LACUNES.md` ouvrait sa lacune 2.4 au présent en annonçant une description « 4 échelons » et une adresse Vercel morte. Les deux portent désormais une **suite datée** au lieu d'une réécriture silencieuse : un audit daté reste un audit daté.
- **`docs/REPOSITORY_DETAILS.md` gagne un § 0 « État constaté »** (13 octobre 2026) : description ✅, site web ✅, **topics ❌ encore vides**, aperçu social ❓ non exposé par l'API. Et un § 4 bis : ce que le dépôt annonce de lui-même sans passer par GitHub — `robots.txt`, `llms*.txt`, les données structurées —, où la licence est **lue** dans `LICENSE`.
- **Le pas à pas est précisé là où il échouait** : les *topics* se posent **un par un** (chaque mot devient une pastille bleue à la validation par Entrée). Coller la liste entière d'un coup laisse le champ vide — c'est l'explication la plus probable de son état actuel.
- **`NOTE_POUR_CLAUDE.md`** indique sous son tableau historique où en sont les quatre champs aujourd'hui ; le `README.md` dit, dans sa section Licence, d'où vient le nom partout ailleurs.
- Le jeton disponible ici reste un jeton d'intégration sans droit d'administration : `--appliquer` se fait refuser (`403`). L'outil le dit et affiche le bloc à coller, plutôt que de faire semblant.

### La licence du dépôt est **lue**, plus recopiée — et elle était fausse en ligne

- **Trois fichiers servis aux robots annonçaient une licence qui n'est plus la leur** — « MIT » — (`robots.txt`, `llms.txt`, `llms-full.txt`) alors que le dépôt est sous **GPL-3.0** : son fichier `LICENSE`, le classificateur de `pyproject.toml`, `package.json`, la section « Licence » du `README.md` et l'API GitHub (qui annonce `gpl-3.0`) disaient tous l'inverse. Le défaut venait d'une constante recopiée sous un commentaire resté à l'ancienne licence. Une licence fausse n'est pas une coquille : c'est une affirmation **juridique**, et elle portait sur ce qui est publié.
- **`licence_du_depot()`** reconnaît ce que dit le fichier `LICENSE` (AGPL, LGPL et GPL se testent dans cet ordre — elles partagent les mots « GENERAL PUBLIC LICENSE ») et rend `""` quand il ne reconnaît rien : un renvoi au fichier, jamais un nom deviné. Toute mention publiée passe par `mention_licence()` — un seul endroit décide, le fichier.
- **L'erreur avait essaimé** : le `README.md`, `docs/RD_INDEXATION.md`, `docs/RD_IMPORT_UCDP.md`, `tests/fixtures/README.md` et `docs/RD_VALIDATION_TEMPORELLE.md` la répétaient, et les **données** de fixtures se déclaraient sous une licence que le dépôt n'a pas (74 enregistrements, un contrat, plus le cas d'essai du test de validation temporelle). 76 mentions corrigées.
- **`tests/test_licence_du_depot.py`** (23 contrôles) : la reconnaissance du fichier, avec un cas négatif — une mention **partielle** (« General Public License, version 3 » sans « GNU ») ne suffit pas à nommer une licence ; l'accord de toutes les déclarations ; et un balayage qui refuse toute ligne attribuant au projet un autre nom.
- **La première version du balayage avait trois trous, trouvés en le sabotant** : une signature élargie restait invisible (les variantes se testant dans l'ordre, l'AGPL passait avant la GPL), réduire la liste des extensions surveillées ne faisait rien échouer, et sauter tous les fichiers rendait le contrôle central vert. Corrigé par un cas négatif, par un balayage devenu **fonction éprouvable sur un faux dépôt** (chaque extension surveillée y porte une mention fautive) et par un contrôle qui exige que le balayage voie des fichiers nommés — et plus de cent. **Huit sabotages après correction, huit attrapés.** Une seule exemption, écrite, pour le fichier de test qui construit des textes de licence pour les éprouver.
- **Ce que le contrôle ne fait pas** : il ne juge pas le choix de licence. Il garantit que tout ce qui est publié dit la même chose que le fichier — un changement de licence se fait en remplaçant `LICENSE`, et tout ce qui aurait été recopié est nommé à la première exécution.

### Ce qui prouve : l'instrument de mesure mentait, deux valeurs publiées étaient fausses

- **Un sabotage qui refuse de mourir.** En éprouvant le bloc « About » du dépôt, un sabotage a continué d'agir **après avoir été restauré** : le fichier sur le disque était revenu à la bonne version, Python servait encore le bytecode du sabotage. La cause : `importlib.util.spec_from_file_location` écrit un `.pyc` et le croit valable tant que **la taille** et **l'horodatage en secondes** de la source n'ont pas bougé — remplacer `None` par `True` ne change pas la taille, et deux écritures dans la même seconde ne changent pas la seconde. Conséquence : **les sabotages ne prouvaient plus ce qu'ils prétendaient**. Six endroits du dépôt chargeaient ainsi leurs scripts.
- **`outils/chargement_module.py`** lit la source et la compile explicitement : rien n'est mis en cache, rien n'est relu d'un `.pyc`. Trois garanties tenues et contrôlées — la source est relue, `__file__` est renseigné (les scripts qui calculent leur racine en dépendent), le module est enregistré sous son nom et retiré en cas d'échec (les `@dataclass` en dépendent). `tests/test_chargement_module.py` (12 contrôles) **reproduit le piège** dans un sous-processus, à un instant fixé (l'an 2001) pour que le test ne dépende pas de l'heure qu'il est, puis montre que le chargeur du dépôt y échappe ; un contrôle refuse le retour du chargeur à cache.
- **Le bloc « About » ne recommande plus de vider le champ.** Il portait une affirmation figée — « l'ancien lien est mort » — écrite le jour où c'était vrai, jamais revue depuis : le dépôt ne renvoyait donc plus vers une application pourtant en ligne. L'adresse vient maintenant de la même source que la page publiée, la sonde `adresse_repond()` **pose la question** à chaque exécution, et elle a trois réponses : elle répond, elle ne répond pas, *je n'ai pas pu vérifier* (réseau absent) — cette troisième est écrite telle quelle, parce que se taire ferait vider le champ sans raison. « Déjà à jour » parle désormais aussi du site web.
- **Trois valeurs de `docs/REPOSITORY_DETAILS.md` avaient dérivé** : le compte de la description annoncé (270 pour **271**), l'empreinte de l'aperçu social — elle désignait **une autre image** (52 Kio annoncés, 51 Kio réels) — et un paragraphe entier recopié deux fois. Une empreinte fausse fait téléverser autre chose que ce que le document décrit. Le document est donc **engendré entre marques** pour ses quatre régions (description, sujets, site web, aperçu social) : `--doc` réécrit, `--verifier-doc` refuse une valeur périmée, la prose reste éditable.
- **La page de réglages effaçait le lien vers l'application.** `outils/reglages_depot.html` n'avait aucun contrôle : son champ « Adresse du site » partait **vide** sous un libellé qui conseillait de le laisser vide, et elle visait un nom de dépôt **tronqué** (`…-du-peuple` au lieu de `…-pour-le-peuple-par-le-peuple`) — donc un dépôt inexistant, ce qui veut dire qu'elle n'a jamais pu appliquer quoi que ce soit. Le lien de repli vers la documentation était tronqué de la même façon, dans la page **et** dans l'outil : trois liens morts. Le champ est pré-rempli, le lien est bâti sur le nom du dépôt, et l'état lu par la page signale un écart entre l'adresse déclarée et l'adresse recommandée.
- **Un défaut trouvé par les tests neufs** : `reecrire_document` plantait sur un chemin hors du dépôt (`relative_to` lève). Corrigé à la source, pas contourné.
- **25 sabotages** posés et attrapés : 6 sur le chargeur, 6 sur le bloc « About », 7 sur le document engendré, 6 sur la page de réglages. Contrôles neufs : `tests/test_chargement_module.py` (12) et `tests/test_details_depot.py` (36, dont 9 pour le document et 7 pour la page), plus le contrôle qui exige le même compte de caractères dans **tous** les documents qui l'annoncent.

### Le nom d'une région dit ce qu'elle fait, à la taille où on la lit

- **Un défaut écrit dans nos propres limites assumées** : sous 640 px, un tableau devient une pile de cartes et ne défile plus horizontalement — mais sa région continuait d'annoncer « faites défiler horizontalement », et gardait un `tabindex="0"` qui ne menait nulle part. Une personne qui suit l'annonce du lecteur d'écran cherchait un défilement inexistant ; sur une tablette à clavier, on s'arrêtait sur une région inerte.
- **`nommerRegionsTableaux()`** réécrit le nom **et** l'arrêt à partir de la légende rangée sur la région (`data-legende`), dans les deux sens : au-dessus de 640 px, « … — faites défiler horizontalement » avec l'arrêt, parce qu'on y fait défiler aux flèches ; en dessous, « … — présenté en cartes, une ligne à la fois » sans arrêt.
- **Un tableau fusionné garde tout** : ses cellules ne s'étiquettent pas, il défile vraiment, même dans 360 px — donc il garde son étiquette et son arrêt. La bascule se décide **tableau par tableau**, jamais à l'échelle de la page.
- **La question posée est celle du CSS**, mot pour mot (`screen and (max-width:640px)`) : deux façons de poser la même question finiraient par donner deux réponses, et le nom se remettrait à mentir sans qu'aucune porte ne le voie. Un contrôle refuse désormais la divergence entre la requête du CSS et celle du JavaScript.
- **Le nom ne s'empile pas** : le suffixe est recalculé depuis la légende rangée, jamais ajouté à ce qui précède — sans cela, chaque vague de rendu aurait empilé un suffixe de plus.
- **Un pli de fenêtre n'est pas un rendu** : `suivrePliDeLEcran()` écoute le redimensionnement (replié à 120 ms, comme le reste de la page) ; une rotation de téléphone n'attend pas qu'un tableau soit réécrit.
- **`tests/test_regions_defilantes.py`** (13 contrôles) exécute le JavaScript sur le DOM minimal avec une fenêtre simulée : large, étroite, élargie, un pli (deux événements coup sur coup, pour éprouver le repli) et une fenêtre sans écouteur. Quatre sabotages posés et attrapés : nom figé sur le défilement, arrêt jamais retiré, pli non écouté, nom empilé.

### Tout accessible, vérifié en ligne plutôt que supposé

- **La suite de tests s'arrête au bord du réseau** : elle contrôle ce que le dépôt contient, jamais ce que Vercel ou Render servent. `outils/verifier-surface-en-ligne.py` comble ce trou — il interroge les deux adresses publiques et compare **au caractère** : le texte servi doit être égal à celui que `surface_publique.py` engendre, l'image servie égale au fichier versionné. Comparer à une photographie ne dirait rien des jours suivants.
- **68 épreuves** : la page (canonique, description, aperçu de partage, données structurées, directives), les quatre textes et les quatre images, les seize routes GET, deux routes GET paramétrées, les quatre routes POST — dont `/api/simuler`, le calcul que la page demande à chaque mouvement de curseur — et les refus qui doivent rester des refus : une route inconnue, un proxy sans cible, un POST sur une route qui n'existe pas.
- **Le piège de la copie de secours est traité** : elle s'endort, puis répond **200 avec une page qui raconte qu'elle démarre**. La prendre pour une réponse serait le pire des silences — la veille dirait que tout va bien au moment précis où rien ne répond. Elle insiste, en le disant, et elle refuse cette page comme une réponse.
- **`.github/workflows/veille-en-ligne.yml`** l'exécute à la main et une fois par semaine, jamais à chaque poussée : une panne d'hébergeur ne doit pas faire rougir la contribution de quelqu'un d'autre. Le rapport s'écrit dans le résumé du run — un journal de job se télécharge, une page de run se lit.
- **Treize contrôles hors ligne** (`tests/test_surface_en_ligne.py`) : la veille ne peut pas prendre du retard sur le moteur (une route servie et non sondée fait échouer la suite), ses épreuves reconnaissent un vrai succès, et cinq sabotages sont attrapés — texte tronqué, page sans canonique, route disparue, route qui répond une erreur, hôte endormi. Le contrôle de couverture a d'ailleurs attrapé un trou au premier essai : le POST `/api/simuler` n'était pas sondé.
- **Résultat du premier passage** : 68 épreuves sur 68, sur les deux hébergeurs.

### Être trouvé : la page se décrit aux moteurs, aux aperçus et aux lecteurs automatiques

- **Rien ne décrivait la page.** Ni description, ni adresse canonique, ni `robots.txt`, ni plan, ni vignette : deux hébergeurs servaient la même page sans dire laquelle fait foi, et un partage affichait un lien nu. `simulateur/surface_publique.py` **est** désormais la source : `robots.txt`, `sitemap.xml`, `llms.txt`, `llms-full.txt` et l'en-tête de la page (description, canonique, directives, aperçu de partage 1200 × 630, données structurées, icônes) viennent du même endroit. `outils/generer-surface-publique.py` écrit les fichiers pour Vercel ; le serveur Python sert le même texte pour Render.
- **`robots.txt` ouvre tout, sauf `/api/`** — des points de calcul, pas des pages : les indexer ne remplit les résultats que de pages vides, et chaque visite coûte une simulation. Un seul groupe `User-agent: *` (un groupe nommé remplacerait le générique, et il faudrait répéter l'exclusion dans chacun), plus la convention `Content-Signal` qui autorise explicitement recherche, réponse assistée et entraînement — le dépôt est ouvert et ses textes sont faits pour être lus.
- **`llms-full.txt` : le contenu en texte pour qui n'exécute pas la page.** La page calcule tout en JavaScript ; un agent qui ne l'exécute pas n'y voit qu'une coquille. Le fichier (45 Ko) donne les 156 leviers avec leur clé, leurs bornes et leur description, les 20 domaines, les 11 scénarios, les 5 classes — **engendré depuis le catalogue** au moment de l'écriture, et comparé au catalogue par un test : les comptes annoncés sont ceux de l'outil publié, pas une photographie.
- **Les métadonnées ne portent aucun nombre.** La page a déjà affiché « 93 leviers » et « 38 indicateurs publics » après qu'ils étaient faux ; une description qui vieillit ne se voit jamais. Un test refuse tout chiffre dans la description et l'accroche, et vérifie qu'aucun nombre balisé dans les données structurées n'est étranger au catalogue (seule exception admise, justifiée par le code : l'échelle des notes de domaine).
- **Données structurées honnêtes** : `Organization`, `WebSite`, `WebApplication` reliés entre eux, et rien de plus. Les moteurs sanctionnent les balisages qui promettent un résultat enrichi sans contenu réel ; un test refuse `aggregateRating`, `review`, `ratingValue` et `faqPage`.
- **La page reste un fichier unique.** Deux `<link>` seulement, et aucun ne charge de fichier : `rel="canonical"` et les icônes en `data:` (décodées et comparées aux fichiers versionnés par un test). Le test d'origine a été **précisé** plutôt que contourné : tout `<link>` de chargement, tout `@import`, toute `url(http…)` et tout `<script src>` restent interdits. Un manifeste d'application a été écrit, essayé, puis retiré pour cette raison.
- **Images versionnées** : `og-image.png` (1200 × 630), `favicon.svg`, `favicon.ico` (16/32/48), `apple-touch-icon.png`, tous engendrés par `outils/apercu_social.py`, qui **lit** les comptes du catalogue au moment du dessin — une vignette qui annonce un nombre faux est une promesse non tenue.
- **Garde-fous** : `tests/test_indexation.py` (35 contrôles : en-tête, fichiers publiés, routes servies, cohérence avec le sous-dossier du site M.R.S.C), les deux générateurs ajoutés à la porte « pas de retard », et trois sabotages posés et attrapés — dont un vrai défaut de montage, l'en-tête injecté *dans* un commentaire parce que le jeton figurait aussi dans la documentation du gabarit.
- **Ce qui reste à faire, et par qui** : Search Console, Bing Webmaster Tools et la vérification en ligne demandent un compte (voir `docs/RD_INDEXATION.md`, § 10).

### Le site M.R.S.C reçoit le moteur à jour : correctif rebasé, publication prête

- **Le site M.R.S.C embarque une copie du moteur, pas un appel au service.** Sa copie venait du 8 octobre (`99491d8`) ; elle passe au moteur du 13 octobre : fluidité, lecture en clair, lexique, nuances institutionnelles, Constitution analysée, dynamiques croisées, contrepouvoir, objections — et la passe « visuel » entière.
- **Le correctif du site refusait de s'appliquer** : l'amont avait bougé sous lui, et `outils/mettre-a-jour-simulateur.py` a eu raison de s'arrêter sans rien remplacer. Il est **rebasé** dans `livraison-mrsc/simulateur-securite-mrsc.patch` — dix conflits résolus un par un dans `interface.py`, l'amont gagnant pour la typographie et ses nouvelles fonctions, le site gardant ses durcissements.
- **Rien ne se perd en silence** : les 16 protections du site absentes de l'amont sont nommées une par une, et la publication échoue si l'une d'elles disparaît. Le correctif rebasé s'applique et se retire proprement sur un clone neuf de l'amont, et les cinq fichiers obtenus sont identiques à l'octet à la copie publiée.
- **La page reconstruite est relue script par script** (`node --check`) : une fusion de HTML en conflit casse le JavaScript sans le dire, et `py_compile` ne voit pas les marqueurs de conflit dans les chaînes Python.
- **Deux ajustements d'intégration** : six routes servies par le moteur et absentes de l'API du site (`constitution`, `contrepouvoirs`, `dynamiques`, `instances`, `nuances`, `objections`), et retrait de la balise d'analytique Vercel de la copie embarquée — cette ressource n'existe pas sur le site, qui est autonome.
- **La publication reste à faire** : le jeton GitHub de cet atelier n'a pas le droit d'écrire dans `thejmimiia-code/MRSC` (403, « Resource not accessible by integration »), alors que celui du simulateur, lui, pousse normalement. `bash livraison-mrsc/publier-mrsc.sh` fait tout le reste en une commande — il copie le sommet de `main`, rejoue la CI du site, et refuse de pousser si un contrôle échoue — puis `deploy-pages.yml` publie le site. La page affiche la révision copiée d'elle-même, en lisant `PROVENANCE.json`.

> **Suite, 13 octobre 2026.** Le dossier `livraison-mrsc/` n'est plus dans le
> dépôt (entrée du même jour, plus haut) : les chemins cités ici ne s'y trouvent
> plus, et ne sont plus à suivre.

### Une seule barre collante quand l'écran se rétrécit, et la veille reste au courant

- **Deux barres se disputaient le haut de l'écran.** Le sommaire était collant à toutes les largeurs, le ruban de veille aussi (`top:0`) : sur un téléphone, la veille passait par-dessus le menu (z-index 60 contre 56) et le masquait. Sous **901 px**, il n'y a plus qu'une barre collante — le sommaire, qui porte la navigation ; le ruban reprend sa place dans le flux, en carte lisible.
- **La veille garde la parole dans la barre** : `#sommaire-veille` écrit le niveau en trois mots (« vigilance · 3 alerte(s) »), coloré **et** écrit, et mène d'un geste au détail des seuils. Son texte vient de `classeNiveau` et `etiquetteNiveau` — les mêmes fonctions que le ruban — donc les deux ne peuvent pas diverger ; `hidden` la tient hors de l'écran et du clavier tant qu'aucun diagnostic n'est connu, et un diagnostic disparu l'efface au lieu de laisser un verdict périmé. C'est un bouton, pas un lien : la marque de lecture du sommaire (`marquerLecture` suit `.sommaire a`) ne la prend jamais pour la section courante.
- **La hauteur de la barre se mesure au lieu de s'écrire.** `--collant` valait 50 px au large et 44 px en petit écran ; la barre en fait 44 et 58. Les ancres atterrissaient **sous** la barre — le titre de la section visée restait caché — et le ruban se collait 6 px trop bas, laissant une fente par laquelle on voyait défiler la page. `mesurerCollant()` écrit la hauteur réelle, `surveillerCollant()` la suit (ouverture du sommaire, rotation, zoom), et la même variable sert au décalage des ancres et à la colle du ruban : les deux barres se touchent exactement. Le repli du CSS dit désormais la vérité (44 px / 58 px) pour les navigateurs sans JavaScript, et une barre non mesurable n'écrase rien.
- **Le ruban devient une carte sur un téléphone** : titre d'abord, verdict en clair sur toute la largeur — il n'est plus tronqué, c'est lui qui porte le message —, puis les quatre commandes en deux colonnes égales de 44 px. Sur papier, la pastille de la barre ne s'imprime pas.
- **Garde-fous** : `tests/test_interface.py::TestLaBarreDeCommande` (10 contrôles statiques, dont le découpage des blocs `@media` par accolades équilibrées) et `tests/test_barre_commande.py` (10 contrôles exécutés sous Node). Un sabotage volontaire — le niveau écrit en dur dans la pastille — a été posé puis retiré : les deux harnais l'attrapent.

### Ce que le navigateur décidait à sa façon : surfaces natives, taille du texte, geste au bord

- **`color-scheme:dark`** déclaré une fois dans `:root` : barres de défilement, curseurs, cases, menus natifs et le fond derrière la page passent en sombre — jusqu'ici le navigateur les peignait en clair. La page ne suit pas le réglage du système (la palette M.R.S.C. est la seule) et un test refuse l'arrivée d'un second thème.
- **`text-size-adjust:100%`** : c'est le document qui fixe la taille du texte ; le navigateur ne la regrossit plus tout seul quand on tourne le téléphone, et le plancher de lisibilité n'est plus défait par un redimensionnement automatique. Le zoom reste libre — ni `user-scalable=no`, ni `maximum-scale` —, ce qu'un test vérifie.
- **`overscroll-behavior:contain` sur les douze surfaces qui défilent** : arrivé au bout d'un tableau, d'un journal ou d'une modale, le doigt n'entraîne plus la page derrière, et ne déclenche plus le rechargement par surprise sur Android. Le garde-fou fait le tour du CSS — toute règle qui déclare `overflow:auto|scroll` doit figurer dans la liste ; c'est ainsi que `.overlay`, la feuille de modale, a été rattrapée.
- **Garde-fous** : `tests/test_interface.py::TestCeQueLeNavigateurDecideToutSeul`.

### Le sommaire dit où l'on est, et les tableaux deviennent des cartes sur un téléphone

- **Repère de lecture** : le sommaire collant surlignait la dernière entrée *cliquée*. Sur une page de vingt-quatre sections, il désignait une section quittée depuis longtemps dès qu'on faisait défiler sans cliquer. `marquerLecture(identifiant)` est maintenant le seul endroit qui pose la marque — le clic et l'observateur de défilement l'appellent tous les deux —, la position est **annoncée** (`aria-current="location"`, pas seulement colorée) et un identifiant inconnu l'**efface** au lieu de la laisser sur l'entrée précédente. Dans une région qui défile, la première colonne colle à gauche pour qu'on sache encore quelle ligne on lit.
- **Les tableaux deviennent des cartes sous 640 px** : les tableaux de la page naissent du script, et plusieurs portent six à neuf colonnes. `tableauEnCartes(tableau)` lit la ligne d'en-tête et pose `data-label` sur chaque cellule ; le CSS en fait une carte par ligne (`tr>*::before{content:attr(data-label)}`), la première cellule servant de titre. L'en-tête sort de l'écran **sans quitter le document** (jamais `display:none`) : les lecteurs d'écran le gardent, et l'impression retrouve un tableau normal — la bascule entière est enfermée dans `@media screen`. Le libellé de chaque colonne n'est écrit qu'une fois, dans l'en-tête.
- **Les régions qui ne défilaient que pour la largeur rendent la place** : `.tableau-strate`, `.bourse-table`, `.tableau-defilant` et `.defilable` passent en `overflow:visible;max-height:none` quand ils contiennent un tableau en cartes (`:has(.tableau-cartes)`). La bascule vaut aussi pour les tableaux déjà défilants — strates, bourse, audit, modales —, qui sont justement les plus larges ; `table.tableau-cartes` tranche la spécificité contre les `min-width` de 600 px et 860 px.
- **Tout ou rien, et ça se répare** : deux lignes d'en-tête, une seule colonne, ou une cellule qui fusionne des colonnes (`colspan`, `rowspan`) — le tableau est vérifié en entier **avant** la première écriture, et n'est pas touché. S'il était déjà étiqueté, il **rend sa marque** et redevient un tableau qui défile. Le passage reprend à chaque vague de rendu (l'observateur de la page réenveloppe les tableaux écrits par le script) : un gabarit qui remplace sa cellule « en chargement… » par de vraies valeurs redevient étiquetable tout seul. `data-cartes="non"` refuse la bascule, et une étiquette déjà juste n'est pas réécrite.
- **Deux doublures de test corrigées** : `classList.toggle(classe, force)` **ajoutait** la classe quand `force` valait `false` — le contrôle « une seule entrée marquée » passait donc sur une doublure infidèle. Le correctif est dans `tests/dom_minimal.mjs` et `tests/navigateur_interface.mjs`.
- **Garde-fous** : `tests/test_interface.py::TestTableauxEnCartes` (règle d'écran, en-tête clippé, vérification avant écriture, rien de carte sur papier) et `tests/test_tableaux_en_cartes.py`, qui exécute le script sous Node — un sabotage volontaire (l'étiquette refusée ignorée) a été posé puis retiré pour vérifier que les contrôles mordent.

### Le plan en proportion au sommet de la page, et une variable qui n'existait pas

- **Les deux plateaux, en proportion** : `#resume-balance` (dans le résumé de tête) montre la part de chaque plateau dans le total des deux, en barres. La couleur ne porte rien seule — chaque côté a son mot, sa part écrite en clair (`87 %`) et son motif (hachures pour les recettes et économies, pointillés pour les dépenses). Les barres sont décoratives (`aria-hidden="true"`) : la part est écrite à côté.
- **Une seule fonction pour les deux visuels** : `partsDesPlateaux(annee)` calcule les parts une fois, et la balance comme le résumé la lisent — le résumé ne calcule toujours rien lui-même. Les deux parts somment à 100 : la seconde est le complément de la première, jamais un arrondi séparé. Sans simulation, les barres restent à zéro et les parts affichent `—`. Le harnais vérifie que les parts du résumé sont **exactement** celles des jauges de la balance, et qu'elles suivent le changement d'année.
- **`--panel-3` réparée** : la variable se définissait elle-même (`--panel-3:var(--panel-3)`) — valeur invalide au calcul, donc transparente, sans erreur ni message. Le survol et l'état actif des cartes de scénario ne changeaient donc pas de fond, et les pistes de jauge n'en avaient pas. Elle reçoit une vraie valeur, et un test refuse désormais toute propriété personnalisée qui se définirait elle-même.
- **Détails** : transition des barres coupée par `prefers-reduced-motion`, remplissage conservé à l'impression (`print-color-adjust:exact`).

### Imprimer son plan, plans d'empilement nommés, rendu différé des sections basses

- **« 🖨️ Imprimer mon plan »** : un bouton dans les actions du résumé pose `html.impression-plan`. Le mode se voit à l'écran — la page ne montre plus que le résumé, **donc on voit ce qui s'imprimera** — et le bandeau qui l'annonce propose de lancer l'impression ou de revenir à la page entière. Sur papier, il ne reste que le résumé et le crédit du mouvement ; la ligne d'attribution (adresse publique) s'imprime avec. La classe reste posée après `window.print()` — bloquant chez certains navigateurs, asynchrone chez d'autres — : c'est le bandeau, jamais un minuteur, qui ramène la page entière, et le focus revient au bouton déclencheur. Garde-fous : `TestImpressionDuPlan` dans `tests/test_interface.py`, et `tests/test_impression_plan.py`, qui exécute les trois fonctions sous Node.
- **Une seule échelle de plans** : huit variables `--z-…` déclarées dans `:root`, du fond (`--z-fond`) à la modale (`--z-modale`), avec la place réservée au bandeau d'impression (`--z-bandeau`). Les sept `z-index` numériques qui traînaient dans sept règles ont disparu ; un test refuse tout nouveau nombre écrit en clair et vérifie que chaque `var(--z-…)` employé est bien déclaré.
- **Encoches** : `max(18px,env(safe-area-inset-…))` sur les quatre bords du corps, avec valeur de repli — sans elle, toute la déclaration serait ignorée en bloc — la marge d'origine restant écrite avant pour les navigateurs qui ne connaissent pas `env()`. Le lien d'évitement suit (`top`, `left`).
- **Rendu différé** : dix sections basses (`nuances`, `verrous`, `contradiction`, `resultats`, `trajectoires`, `domaines`, `matrice`, `journal`, `provenance`, `audit`) portent `content-visibility:auto` et `contain-intrinsic-size:auto 620px` : le navigateur ne les met plus en page avant qu'on s'en approche. Rien n'est retiré du document — ancres, recherche dans la page et impression trouvent tout — et l'impression lève explicitement le différé (`section.bloc{content-visibility:visible}`).
- **Typographie** : `text-wrap:balance` sur les titres, `text-wrap:pretty` sur les paragraphes, et la modale qui suit la hauteur réellement visible (`max-height:74vh;max-height:74dvh`).

### Crédit du mouvement, cliquable, en bas de page

- **Pied de page** : la page se ferme sur « © 2026 Mouvement Représentatif de la Société Civile (M.R.S.C) », le nom du mouvement portant lui-même le lien vers <https://thejmimiia-code.github.io/MRSC/> (nouvel onglet, `rel="noopener noreferrer"`). Il suit l'attribution et la bannière, s'en distingue par `.pied.credit` (padding haut annulé, lien en gras) et reste le dernier texte balisé de la page, avant les scripts. `tests/test_interface.py::TestDonneesPubliquesDansLaPage::test_credit_du_mouvement_en_bas_de_page` verrouille le texte exact, la cible, la position en bas de page et la classe de style — trois choses qui peuvent se perdre sans bruit.

### R&D Fusion globale — toutes les optimisations et branches fusionnées proprement

- **Audit d'intégration exhaustive** (12 octobre 2026, branche `arena/2f4374f1…`) : les 14 branches `arena/*` distantes et les 4 branches `resolution/*` sont toutes **ancêtres de `main`** — `git merge-base --is-ancestor` vert pour chacune, aucune divergente ; la vérification par `git merge-tree` confirme l'absence de conflit résiduel et la parité fichier-par-fichier (`git diff --name-only` vide entre chaque tête de branche et `main` pour ses fichiers touchés). Le plan en 12 commits parallèles (géopolitique annuelle + mensuelle, 93→156 leviers, 48→55 réglages institutionnels, 7 réglages neufs, constitution fichée, Vercel unifiée, calibrage ménage, optimisation fluidité, contradiction) a été rejoué dans l'ordre chronologique et tient sans régression.
- **Synthèse des optimisations fusionnées et mesurées (R&D octobre 2026)** : **compression HTTP négociée** (`simulateur/compression.py`, 194 lignes, seuil 512 o, `Vary: Accept-Encoding`, `gzip`/`deflate`/`br`/`zstd`, 72–86 % de gain vérifié sur 7 routes), **rendu différé des 7 onglets** (`interface.py`, `renderOngletsStrates` → `rendreOngletStrate`, seuls l'onglet ouvert construit, harnais Node vérifie l'onglet vide jamais visité), **cache du catalogue de bulles** (`dashboard.py` `catalogue_bulles`, clé = horodatage contexte, plafond 6 entrées, verrou anti-concurrence, 4 538 ms → 57 ms au second appel, 7 292 ms → 79 ms mesuré localement), **lexique** (`simulateur/lexique.py`, 83 termes, 6 catégories, `/api/lexique?q=`, balisage HTML sûr, 1,6 ms pour 25 Kio), **lecture en clair** (`simulateur/clarte.py`, 505 lignes, 10 phrases fidèles/neutres/sourcées, champ `lecture` de `/api/simuler`), **fonction Vercel unique** (`api/[...path].py`, 22 routes + `verifier-source.py`, générateur `outils/generer-fonctions-api.py --verifier`), **pont WSGI unifié** (`simulateur/wsgi.py` + `pont_api.py`, routeur partagé serveur local/Vercel/WSGI). Mesure reproductible : `SIMULATEUR_HORS_LIGNE=1 python3 outils/mesurer_fluidite.py` → `POST /api/simuler` 283 Kio → 41,7 Kio (-85 %), page `/` 248 Kio → 68,7 Kio (-72 %).
- **Cohérence de licence rétablie** : `LICENSE` est GPL-3.0 et l'API GitHub l'annonce (`licenseInfo.key = gpl-3.0`), `pyproject.toml` utilisait déjà `license = { file = \"LICENSE\" }` mais gardait le classificateur `MIT` et `package.json`/`package-lock.json` annonçaient `MIT` avec un doublon `## License` MIT en fin de `README.md`. Corrigé : classificateur → `GPLv3`, `package.json` et `package-lock.json` → `GPL-3.0`, suppression du doublon `## License` MIT (la section GPL en § Licence reste l'unique référence avec droit moral L. 121-1). Vérifié : `pip install -e .` annonce `License: GNU GPL v3`, `ruff check .` vert avec `UP` conservé, 982 tests passés.
- **Documentation et garde-fous alignés** : `CONTRIBUTING.md` → Python 3.11+ (au lieu de 3.10), arbre `simulateur/` à jour (5 échelons, 156 leviers, 20 domaines, 52 indicateurs publics, 22 routes, 83 termes, 101 bulles), `tests/test_compteurs.py` vert (12 référentiels, 24 règles, famille d'interdits — aucun compteur vivant ne fige un compte de tests), 6 générateurs `--verifier` verts (`fonctions-api`, `objections`, `registre-engagements`, `doc-nuances`, `page-verification`, `index-simulateur`), `ruff 0.17.0` épinglé en CI.
- **Preuve de fin de la fusion** : `PYTHONPATH=. pytest -q` → 982 passed, 11 skipped (sans serveur) ; `SIMULATEUR_HORS_LIGNE=1 python3 outils/mesurer_fluidite.py` reproduit les gains ; `python3 outils/verifier-compteurs.py` → `compteurs à jour : 156 leviers, 55 reglages, 16 presets, 14 familles, 20 domaines, 74 indicateurs, 52 indicateurs_publics, 18 domaines_societe, 31 garde_fous, 11 scenarios, 5 echelons, 22 routes` ; `gh pr list` → 14 PR arena fusionnées, 0 ouverte sur `arena/*`.

### Corrigé — P1-1 à P1-3 : les trois chantiers certains du plan de renforcement

- **P1-1 — Recouvrement de 21 communes résorbé** : `simulateur/model.py` `bourgs_centres_count` 7 650 → 7 629 (−21 fusions 2022→2024, INSEE 01/01/2024) ; la somme des strates rurales + bourgs + villes moyennes + grandes agglomérations + 100 k + 200 k + 5 vaut désormais exactement `communes_total` = 34 935. `simulateur/web_server.py` aligné. `tests/test_territoires_elections.py` vérifie `écart = 0` au lieu de documenter 21. Preuve : `pytest tests/test_territoires_elections.py::test_typologie_communale_insee_9_strates` vert.
- **P1-2 — Date Banque mondiale dégelée** : `simulateur/donnees_live.py` `src_worldbank()` demandait `date=2024` en dur — l'instant T restait figé sur 2024 sans le dire. Corrigé : `date=2019:{année courante}` (calculée via `datetime.now(UTC).year`), adaptateur inchangé (première entrée = la plus récente). Le ruban affiche la `periode` retournée, et deux nouveaux tests verrouillent la fraîcheur : `test_url_banque_mondiale_couvre_l_annee_courante` (l'URL doit contenir l'année courante, pas 2024) et `test_reference_banque_mondiale_non_perimee` (snapshot Banque mondiale pas plus vieux que l'année précédente). Preuve : `pytest tests/test_donnees_live.py::TestFraicheurBanqueMondiale` vert.
- **P1-3 — Garde-fou étendu aux taux** : `outils/verifier-compteurs.py` ne couvrait que les comptages (leviers, domaines…). Ajout d'une famille **`taux_structurants` = 3** — 3 % de déficit (Maastricht), 30 % de commande publique réservée aux PME (CCP L.2113-10), 5,5 % de TVA énergie (directive 2022/542) — avec sa règle ` (\\d+) taux structurants` et son gabarit `les 3 taux structurants (3 % déficit, 30 % PME, 5,5 % TVA)`. Le `README.md` porte désormais cette phrase, le compteur est déduit du code, et la contre-épreuve `tests/test_compteurs.py` le couvre (bonne valeur passe, +7 échoue). Preuve : `verifier-compteurs.py` → `… 22 routes, 3 taux_structurants` et `pytest tests/test_compteurs.py` vert (12 → 13 référentiels, 24 → 25 règles).

### Ajouté — `docs/19` : le plan de renforcement, ses constats et ses preuves de fin

- `docs/19_PLAN_DE_RENFORCEMENT_ET_LACUNES.md` : l'audit du 12 octobre 2026 en une page —
  les six instruments de mesure, les trous trouvés (CI rouge, compteurs périmés, onze tests
  jamais exécutés, métadonnées GitHub bloquées faute de droits), ce qui a été corrigé, et les
  dix chantiers restants classés en trois horizons, **chacun avec sa preuve de fin**. Le
  document dit aussi ce que l'audit n'a pas trouvé et pourquoi il n'est pas indépendant.

### Ajouté — Les compteurs annoncés se déduisent du code (`outils/verifier-compteurs.py`)

- Douze référentiels lus dans le code (leviers, réglages, préréglages, familles, domaines,
  indicateurs, indicateurs publics, domaines sociétaux, garde-fous, scénarios, échelons,
  routes), **24 règles de phrase**, et une seconde famille de contrôles : les comptes qu'un
  document vivant ne doit pas annoncer du tout (le nombre de tests change à chaque commit).
- Les rapports datés (journal, R&D, audits, revues de dépôts tiers) sont exemptés, chacun
  avec sa raison écrite ; le contrôle refuse une exemption sans raison ou visant un fichier
  absent. `tests/test_compteurs.py` est la contre-épreuve : chaque règle doit accepter son
  gabarit au compte réel et rugir sur un compte faussé — une règle morte est un échec.
- Corrigés au passage : « 93 leviers croisables » dans `pyproject.toml`, la description
  GitHub et la page des réglages ; « 149 leviers » dans `outils/details_depot.py`,
  `simulateur/compression.py` et `simulateur/dashboard.py` ; « 38 indicateurs publics » au
  lieu de 52 dans trois documents ; « 33 garde-fous » au lieu de 31 dans deux fichiers ;
  « 16 routes du moteur » et « 20 routes exposées » au lieu de 22 ; « modèle gigogne à
  4 échelons » dans `simulateur/web_server.py` ; « 18 domaines d'impact » au lieu de 20 ; et
  **douze comptes de tests recopiés** dans huit documents vivants (README, CONTRIBUTING,
  NOTE_POUR_CLAUDE, docs/15, docs/16, docs/18, docs/METHODOLOGIE, docs/README). Les documents
  datés gardent les leurs. `README.md` et `docs/METHODOLOGIE.md` annonçaient Python 3.9+ alors que
  `pyproject.toml` exige 3.11 : les deux documents sont alignés sur le `requires-python`.
- La page compte désormais ses préréglages et ses scénarios comme ses leviers : lus dans les
  données servies, jamais écrits dans la phrase qui les annonce.

### Corrigé — `ruff check .` passe de 1 553 erreurs à zéro, sans changer un résultat

- La dette annoncée dans l'entrée précédente a eu son commit dédié : 1 522 corrections
  automatiques (annotations `typing.List`/`Optional` au goût du jour, imports triés et
  purgés, f-strings sans trou) et 51 corrections traitées à la main — 26 lignes vides
  nettoyées, 10 `noqa` motivés pour les imports qui suivent l'aménagement de `sys.path`,
  et 14 décisions : `B007` (itérer sur `.values()`), `C401`, `F841`, `B905` (`strict=False`
  écrit noir sur blanc).
- Une seule exception, déclarée dans `pyproject.toml` avec sa raison : la double espace de fin
  de ligne du gabarit du guide, qui vaut un saut de ligne en Markdown.
- Deux vrais défauts sont sortis du nettoyage : le contrôle de parité des routes cherchait
  `ROUTES: Tuple[str, ...]` dans le générateur et ne trouvait donc plus rien une fois les
  annotations modernisées ; et `tests/test_territoires_elections.py` calculait la somme des
  strates communales sans jamais la comparer — vérifiée, elle révèle **21 communes de
  recouvrement** (0,06 %) entre la strate rurale INSEE et le découpage du modèle, désormais
  borné et nommé.
- La CI épingle `ruff==0.17.0` : une montée de version qui change les règles doit être une
  décision, pas une surprise.

### Ajouté — La CI exécute les onze tests d'API qui ne s'exécutaient jamais

- `tests/test_societe.py` et `tests/test_histoire.py` interrogeaient `http://127.0.0.1:8000`
  sans qu'aucun serveur ne tourne : les onze cas se sautaient à chaque exécution depuis leur
  écriture. Ils acceptent maintenant l'adresse du serveur par `SIMULATEUR_BASE_URL`, et la CI
  démarre la console (`python3 -m simulateur.web_server 8000`), attend qu'elle réponde,
  exécute les deux modules — zéro saut — puis l'arrête.

### Ajouté — Organiser la contradiction : 24 objections, 4 contre-modèles, un registre daté

- `simulateur/contradiction.py` : le registre qui renverse la charge de la preuve. **24
  objections** (10 adossées aux mesures du plan, 14 aux hypothèses du moteur) portent chacune
  une citation de l'attaquant, la concession écrite, ce qui survit malgré elle, le fait qui
  ferait changer d'avis, ses sources datées et son statut ; **4 contre-modèles** cohérents
  (État minimal et revenu universel, mur de la réalité, réalisme d'adoption, orthodoxie
  budgétaire) sont mesurés au modèle dans `docs/20_CONTRE_MODELES.md`. Les gages des mesures
  sont confrontés à la portée des leviers, déduite du catalogue : **21 Md€/an de réserve de
  portée** apparaissent, calculés et non saisis.
- `outils/generer-objections.py` et `outils/generer-registre-engagements.py` engendrent
  `docs/05` (cinq pièces nouvelles par fiche), `docs/20`, `docs/21` et
  `docs/22_REGISTRE_ENGAGEMENTS.md` — ce dernier rejoue le scénario de mandature et nomme,
  indicateur par indicateur, la source extérieure qui jugera le plan, avec les seuils de
  réussite et d'échec. Les deux outils ont un mode `--verifier` que la CI exerce.
- `GET /api/objections` (filtres `famille`, `statut`, `levier`, `chercher`), la section
  *Objections* de la page avec ses quatre filtres et ses cartes de contre-modèles, sept étapes
  de plus dans le harnais Node, et `.github/ISSUE_TEMPLATE/objection.md` pour déposer une
  objection sourcée.
- `tests/test_contradiction.py` : 22 cas (garde-fous du registre, gages confrontés aux
  en-têtes de fiches, fraîcheur des documents engendrés, HTTP et page).


### Corrigé — Nettoyage de lint sur les fichiers de la passe, et mort-de-code retiré

- `simulateur/nuances_institutionnelles.py` : trois variables calculées et jamais lues dans
  `coherence_nuances()` (`chiffrees`, `index_cibles`, `liees`) supprimées — leurs contrôles sont
  produits ailleurs, en direct (`cibles_inconnues`, `apports_sans_reglage`, `reglages_sans_article`) ;
  une boucle `for … : pass` sans effet dans `reglages_touchant()` retirée ; import `Iterable` inutile,
  ligne blanche avec espaces, variables `l` renommées.
- `outils/generer-doc-nuances.py` : import inutilisé, parenthèses superflues, variables `l` renommées ;
  sa sortie est restée octet pour octet identique (contrôlée par `--verifier`).
- `simulateur/constitution_analysee.py`, `simulateur/instances_et_dynamiques.py`,
  `tests/test_constitution_analysee.py`, `tests/test_dashboard.py`,
  `tests/test_gouvernance_contrepouvoir.py` : imports inutilisés et variables `l` repris.
- La dette de style préexistante du dépôt (`typing.List`/`Dict` au lieu de `list`/`dict`, 1 196
  avertissements `UP006`/`UP035`/`UP045` déjà sur `main`) n'est **pas** reprise ici : une bascule
  mécanique de 1 400 sites dans cette branche noierait le diff. Elle mérite son propre commit,
  `ruff check . --fix`, sans changement de comportement.
- Vérifications : 956 tests OK, sept scénarios `main.py` rejoués, export JSON contrôlé, quatre
  générateurs `--verifier` à zéro. Le déploiement Vercel du projet de production, rouge sur `main`
  (l'`ImportError` du pont), est vert sur la branche.

### Ajouté — Sept réglages neufs, un plan « sans trou », et le contrat Vercel réellement tenu

- `simulateur/nuances_institutionnelles.py` : **7 réglages de plus** (55 au total, catalogue à
  **156 leviers**) — `reglage_procedure_acceleree_encadree` (0 à 45 jours),
  `reglage_nouvelle_deliberation_supprimee`, `reglage_commission_enquete_droit_de_bloc`,
  `reglage_haute_cour_non_parlementaire` (collège de 120 non parlementaires),
  `reglage_cee_consultation_prealable` (0 à 30 jours), `reglage_defenseur_saisine_directe`,
  `reglage_declassification_legislative` (0 à 30 jours). Chacun déclare ses cibles chiffrées, ses
  articles et ses apports d'indices ; aucun n'est adossé à un préréglage, et le document
  `docs/SIMULATEUR_PARAMETRABLE.md` le dit (16 préréglages recensés).
- `etat_des_verrous()` : le registre des 38 verrous est partagé en **touchés / intacts / hors
  réglage** (20 + 18, la somme est contrôlée sur trois vecteurs), avec avertissements pour les règles
  privées de leur objet par un réglage. La clé `verrous` voyage dans `contexte_institutionnel` et
  donc dans `POST /api/nuances`.
- Interface : nouvelle section `#section-verrous` (trois colonnes + neutralisations) et liste des
  réglages déplacés avec badges par catégorie de connaissance ; les citations de la Constitution
  deviennent le lien `/api/constitution?article=N` déjà utilisé pour les leviers (`articlesHtml`),
  les autres sources restent du texte. un test délègue à `outils/generer-index-simulateur.py --verifier` pour
  refuser un `index.html` qui ne serait pas la page courante, et le harnais Node contrôle le rendu du bloc.
- `docs/18_PLAN_GLOBAL_BRAINSTORMING_ET_SANS_TROU.md` : la clause « sans trou » définition par
  définition, la carte du dépôt, 32 possibilités examinées dont 6 ouvertes assumées, la table des 7
  réglages neufs, le protocole de relance et les limites.
- **Deux trous structureux corrigés.** D'une part `api/` comptait 23 fonctions générées — et le pont
  `api/[...path].py`, seul appelé par Vercel, importait une classe `PontAPI` que
  `simulateur/pont_api.py` ne définissait pas : toute l'API en production renvoyait une erreur
  d'import pendant que la suite restait verte. `simulateur/pont_api.py` définit désormais
  `chemin_de_pont()` et `PontAPI` ; `outils/generer-fonctions-api.py` n'écrit que le parapluie et
  supprime les fichiers par route ; `tests/test_vercel_runtime.py` charge la fonction unique par son
  chemin et sert deux routes par HTTP réel. D'autre part les compteurs de la documentation
  (« 149 leviers », « 48 réglages ») sont passés aux valeurs courantes dans les 10 fichiers d'état
  et `simulateur/lexique.py`, et `outils/generer-doc-nuances.py` régénère désormais les sept tableaux
  de `docs/17` avec un mode `--verifier` qui échoue si la page a pris du retard.
- `tests/test_plan_global_croisements.py` : 30 tests sur les croisements de la passe (invariants de
  registres, accessibilité des connaissances, plafonds de jours, cohérence des compteurs, contrat de
  `api/`, limites de `docs/17`).

### Ajouté — Toutes les nuances institutionnelles deviennent des réglages simulables

- `simulateur/parametres.py` : **48 nouveaux leviers** préfixés `reglage_`, qui portent le
  catalogue de 101 à **149 leviers** en 14 familles. Ils couvrent neuf niveaux —
  constitutionnel (assiette de la censure, quorum du Congrès, assiette des trois
  cinquièmes, contrôle des lois référendaires, interdiction du 49.3, verrou par loi
  organique, par révision, par engagement international), parlementaire (délais de motion,
  seuil de saisine, recours contre une irrecevabilité, droit d'amendement, part de l'ordre
  du jour, seuil de groupes, scrutin nominal), budgétaire (délais de l'article 47 à l'envers
  et à l'endroit, vote par programme, règle d'or du déficit, audit préalable), judiciaire
  (appel du filtre QPC, parquet, mandats non renouvelables, avis du Conseil d'État,
  exécution des arrêts, action de groupe), territorial et outre-mer (seuil de pétition,
  référendum local automatique, plancher de dotation, suffrage direct des EPCI et du Sénat,
  différenciation, matières transférées), européen (recours de subsidiarité, vote préalable
  sur les actes délégués, ancrage dans le droit dérivé), participation (registre des
  amendements, comptes en temps réel, chambre tirée au sort, veto suspensif de convention,
  révocation, algorithmes) et exception (contrôle du juge, durée maximale de l'état
  d'urgence, non-rétroactivité, stabilité normative).
- Ces leviers sont des objets `Levier` **ordinaires** : description, unité, bornes, profil
  quinquennal, `effets_directs` sur les thèmes du moteur, `source` citée et `articles=`
  pointant vers les identifiants du registre légal. Ils héritent donc de tout ce qui existe
  déjà — curseur dans l'interface, bulle d'interaction, ligne de la page de vérification,
  case des préréglages — et **0 vaut partout statu quo** : aucun curseur ne prétend que
  plus c'est haut, mieux c'est.
- `simulateur/nuances_institutionnelles.py`, nouvelle couche de recalcul : le réglage n'est
  pas un commentaire, il change les chiffres. **Seuils** — censure 289 → 231 voix selon
  l'assiette (avec 347 votants de quorum à la troisième modalité), Congrès 555 voix fixes
  contre 555/480/420/371 selon les votants, saisine du Conseil 60 → 40 → 15 → 0, délai
  d'examen du budget 40 → 20 jours, seuil de groupes 15 → 5, état d'urgence borné à 24 mois.
  **Calendriers** — chaque battement réglable voit ses jours de rigueur bouger (une chambre
  tirée au sort et un veto de convention ajoutent 140 jours à la navette ordinaire), et la
  fenêtre législative utile se recalcule sur la part d'ordre du jour laissée au Parlement
  (150 → 75 jours), la tenabilité de chaque trajet étant rejugée à chaque fois.
  **Fentes** — le score de défendabilité baisse quand un réglage la verrouille (censure sur
  effectif 72 → 0, référendum sans juge 79 → 0), `irrefutabilite` reste vide : un réglage
  ferme une porte, il ne rend rien inattaquable. **Huit indices** à base 50 = l'état du
  droit, avec leurs composantes affichées et la saturation visible (`borne_appliquee`).
- `GET /api/nuances` : synthèse, `?reglage=`, `?article=CONST_ART_49`, `?niveau=`,
  `?index=`, `?chercher=`, et `?parametres={…}` pour rejouer un vecteur ; `api/nuances.py`
  ajouté par le générateur (21 fonctions).
- Le préréglage « refondation démocratique » déplace désormais 6 de ces réglages, et la
  couche lui rend ce que le droit lui refuse : deux fentes verrouillées, redevabilité à 74,
  contrôle juridictionnel à 75.
- `parametres.normaliser()` : une valeur de type `choix` hors bornes est écrêtée **puis**
  validée dans la liste des modalités — l'écrêtage aux bornes s'appliquait à tout le monde
  sauf aux choix, ce qui faisait échouer le balayage de bornes du moteur.
- `docs/17_NUANCES_INSTITUTIONNELLES_ET_REGLAGES.md`, générée en relisant le module (tableau
  des 48 réglages, seuils, calendrier, fentes, indices, quatre expériences chiffrées) ;
  lignes 15, 16 et 17 ajoutées à l'index de `docs/README.md` ; compteurs « 101 leviers »
  repris en « 149 » dans README, `docs/SIMULATEUR_PARAMETRABLE.md`, `docs/REPOSITORY_DETAILS.md`,
  `docs/PLAN_AUDIT_GLOBAL.md`, `docs/HEBERGEMENT.md`, `docs/15`, `NOTE_POUR_CLAUDE.md`,
  `outils/details_depot.py` et le lexique ; `index.html` régénéré.
- 46 tests nouveaux (41 dans `tests/test_nuances_institutionnelles.py`, 5 HTTP dans
  `tests/test_dashboard.py`) dont la neutralité stricte : vecteur par défaut = chiffres des
  modules de droit, au jour et à la voix près. Suite : **919 tests**, 11 sauts.

### Ajouté — Instances qui gravitent à tous les étages, yoyo des chambres, fentes non écrites

- `simulateur/instances_et_dynamiques.py` : **26 instances** (constitutionnelles, administratives,
  judiciaires, financières, indépendantes, parlementaires, territoriales, européennes,
  internationales, plus le Président, le Gouvernement et le corps électoral), chacune décrite par
  sa saisine, ses effets et surtout **qui la contrôle** — le champ `juge_par` est obligatoire, une
  instance qui ne répond devant personne doit le dire au lieu de le taire.
- **8 trajets** en battements chiffrés (navette ordinaire, budget, révision par Congrès, révision
  par référendum, renversement, QPC, contentieux local, RIP) : chaque battement cite l'article qui
  l'autorise et un nombre de **jours de rigueur**. `oscillation()` confronte le total à la fenêtre
  législative résiduelle — 150 jours au 12 octobre 2026, constat daté et non un texte : la navette
  ordinaire (160 jours, 10 battements) n'y tient pas.
- `asymetrie_des_chambres()` mesure ce que le Sénat peut seulement retarder (jamais sur une loi
  ordinaire ni sur le budget) et où il tient un veto réel (l'article 89, sans CMP ni dernier mot).
- **15 stratégies** déjà servies (49.3, censure, abstention de la majorité, vote bloqué, article
  40, gage, motions de procédure, niche, commission d'enquête, soixante saisines, défossilisation,
  nouvelle délibération, référendum de l'article 11, procédure accélérée, référé-liberté) et
  **12 fentes et portes** : conséquences non écrites dont chaque prémisse se résout dans le dépôt,
  avec raison du silence, verrou de retour et point de vigilance.
- Deux résultats chiffrés, calculés et non commentés : le Congrès compte les suffrages exprimés
  (180 voix si 300 parlementaires votent, contre 555 sur 925 sièges) alors que la censure compte
  les membres (289, quel que soit le nombre de votants) — la même abstention, deux effets
  contraires, et aucun texte pour la dénoncer.
- `robustesse()` note la défendabilité sur un barème public et laisse `irrefutabilite` à `None` :
  le Conseil d'État contrôle la compétence, la procédure et la motivation, jamais la logique d'une
  démonstration. Un test interdit les formules qui présenteraient une fente comme gagnée.
- `coherence_avec_le_droit()` refuse toute référence orpheline (article, identifiant du registre,
  verrou, mécanisme, instance) et toute fente annoncée chiffrée sans calcul ; la normalisation
  bascule les leviers inventés dans `pistes`, comme pour les fiches constitutionnelles.
- Deux routes, `GET /api/instances` et `GET /api/dynamiques`, fonctions Vercel régénérées
  (20 routes dans `api/`), 29 tests de module et 8 tests HTTP — suite complète à 873 tests,
  `OK (skipped=11)`.
- `docs/16_INSTANCES_YOYO_ET_FENTES.md` : la méthode des trois conditions, le tableau des fentes
  et de leurs scores, et ce que le module refuse d'affirmer.


### Ajouté — La Constitution ficheée article par article et l'arithmétique des contre-pouvoirs

- `simulateur/constitution_analysee.py` : 109 fiches, une par article en vigueur du texte
  officiel (Titres I → XVI), plus 10 entrées pour les articles abrogés (78 à 86, 90).
  Chaque fiche porte ses règles chiffrées, ses opportunités, ses contraintes, les
  contre-pouvoirs qui l'encadrent, les articles à lire avec, les strates qui encaissent,
  les mécanismes du moteur et les leviers réels du catalogue. `couverture()` garantit
  l'exhaustivité, `article()` accepte « art. 49 », « 49 al. 3 » et « 49.3 ».
- La fabrique filtre les leviers sur `parametres.LEVIERS` et bascule tout nom inconnu dans
  un champ `pistes` : une fiche ne peut plus promettre un levier qui n'existe pas (101 occurrences de pistes distinctes
  aujourd'hui, aucune d'entre elles chiffrée dans le simulateur).
- `simulateur/gouvernance_contrepouvoir.py` : 31 manœuvres et 38 verrous chiffrés — signatures,
  majorités, délais, plafonds — avec `ETAT_ASSEMBLEES` daté du 12 octobre 2026
  (574 sièges pourvus à l'Assemblée, 289 pour la majorité absolue, 175 au Sénat, 555 au
  Congrès sur 925 suffrages exprimés). `coherence_avec_les_fiches()` refuse qu'un mécanisme
  ne soit relié à aucune fiche.
- Passerelle `vers_registre_legal()` : `REGISTRE_LEGAL` passe de 37 à 189 identifiants sans
  que les 37 entrées constitutionnelles préexistantes soient touchées, et chaque entrée
  greffée est marquée « synthèse de travail » avec la source et sa date.
- `simulateur/verification.py` n'importe plus le module constitutionnel au chargement
  (cycle d'imports évité) et résout les statuts à la demande, en donnant la priorité aux
  entrées manuelles.
- Deux fichiers de tests (45 cas) recalculent les seuils à la main, 8 cas testent les routes :
  suite complète à 836 tests, `OK (skipped=11)`. Les 7 échecs du harnais navigateur ont été corrigés au
  passage (`tests/navigateur_interface.mjs` extrayait le mauvais bloc `<script>`).
- Deux routes JSON : `GET /api/constitution` (`?article=`, `?bloc=`, `?fonction=`,
  `?chercher=`) et `GET /api/contrepouvoirs` (`?mecanisme=`, `?assemblee=`, `?chercher=`),
  avec 404 explicites et liste des noms connus. `outils/generer-fonctions-api.py` a été
  relancé (18 fonctions dans `api/`) et accepte maintenant les noms de route avec
  underscore : `/api/garde_fous`, déclaré par le moteur mais jamais exposé, l'est du
  même coup. Aucune section d'interface ajoutée.
- `docs/15_CONSTITUTION_FICHEE_ET_CONTRE_POUVOIRS.md` : ce qui est couvert, ce qui ne
  l'est pas, et comment le vérifier.

### Modifié — Une seule fonction Vercel pour les routes du moteur (`api/`)

- `api/` ne contient plus une fonction par route (16 fichiers) : la fonction
  attrape-tout `api/[...path].py` sert toutes les routes `/api/*` du moteur, via
  `simulateur.pont_api.PontAPI`. `api/` compte désormais 2 fonctions, sous le
  plafond de 12 de l'offre Hobby, dépassé par les 17 fichiers précédents.
- `simulateur/pont_api.py` transmet la requête au routeur existant. Si Vercel
  transmet la destination de la réécriture (`/api/[...path].py?...path=<route>`) au
  lieu de l'URL demandée, le chemin `/api/<route>?…` est rétabli avant l'appel.
- `outils/generer-fonctions-api.py` écrit `api/[...path].py` et supprime les anciennes
  fonctions générées route par route. Il refuse d'agir, sans rien modifier, si `api/`
  contient un fichier qu'il n'a pas généré. `--verifier` contrôle sans rien écrire.
  `verifier-source` reste une fonction du site, jamais supprimée.
- `/api/export` construit le CSV et le JSON en mémoire. L'ancienne version écrivait
  un fichier dans le dossier courant, impossible sur un hébergeur à fonctions dont le
  système de fichiers est en lecture seule (seul `/tmp` est inscriptible). Les réponses
  (contenu, en-têtes, nom de fichier) sont inchangées.
- `tests/test_vercel_runtime.py` : contrat de `api/`, routes servies par la fonction
  unique, 404, destination de réécriture, HEAD, export sans écriture disque, et
  générateur (suppression limitée aux fichiers générés, refus sur fichier inconnu).
- README et `docs/HEBERGEMENT.md` documentent le déploiement Vercel. Aucune règle de
  réécriture `vercel.json` n'est ajoutée. (Écrit à une passe où le générateur produisait encore un
  fichier par route : la page était donc vraie sur le papier, fausse sur le terrain. La passe
  suivante l'a rendue exacte, tests à l'appui.)

## [1.10.2] — 2026-10-08

### Ajout — Calibrage transparent des dépenses du foyer

- Dans l’onglet **Ménages**, un sélecteur choisit entre la saisie personnelle
  par poste et la structure de consommation INSEE 2025 appliquée à un total
  mensuel déclaré. Le tableau expose la base sélectionnée et, en mode INSEE,
  les parts normalisées par catégorie.
- Source, période de publication/collecte et statut de la référence sont affichés
  avec le choix. Le mode public n’écrase pas les montants personnels et ne
  modifie que le panier de consommation; les autres champs restent personnels.
- Les données du foyer restent dans la mémoire de la page : aucun envoi à l’API,
  aucun ajout au lien de partage et aucune persistance au rechargement.
- Tests statiques et parcours navigateur ajoutés pour le choix de calibrage, la
  normalisation des parts et le retour aux valeurs saisies.

## [1.10.1] — 2026-10-08

### Corrigé — Le contrat Vercel rattrape le moteur (`api/`, `index.html`)

Deux tests de `tests/test_vercel_runtime.py` échouaient sur `main` : les
artefacts générés n'avaient pas suivi le moteur. Les deux sont refaits.

- **Quatre routes manquaient dans `api/`.** `conseil` (conseiller temps réel),
  `lexique` et `marches` n'étaient pas déclarées dans le tuple `ROUTES` du
  générateur. La quatrième, `garde_fous`, était invisible pour la vérification
  elle-même : son expression régulière `(/api/[a-z]+)` ignorait le souligné, si
  bien que la route n'a jamais pu être signalée comme manquante — alors que la
  page l'appelle (`fetch('/api/garde_fous')`) et que
  `docs/SIMULATEUR_PARAMETRABLE.md` la documente. L'expression est élargie à
  `[a-z_]+`.
- **`api/` passe de 12 à 16 routes** (+ `verifier-source`, fonction du site,
  jamais écrasée). `--verifier` confirme l'accord avec le moteur.
- **`index.html` régénéré** : il datait d'avant les changements de `HTML_PAGE`
  — le générateur le disait lui-même (« index.html est différent de HTML_PAGE :
  relancer le générateur »).
- Les 16 routes sont servies par le pont WSGI, vérifiées une à une en HTTP
  (13 en GET, 3 en POST) ; `conseil` et `donnees` restent réservées au POST.
- **`README.md`** : l'offre Hobby de Vercel plafonne un déploiement à 12
  fonctions ; `api/` en compte 17, donc le déploiement Vercel est refusé sur
  l'offre gratuite. Le bouton Render, l'image Docker ou n'importe quel
  hébergeur Python servent les 16 routes depuis un seul processus.
- Tests : **540 réussis** ; `ruff check .` propre.

## [1.10.0] — 2026-10-08

### Ajout — Un lien public pour le simulateur (`simulateur/wsgi.py`)

Le dépôt contient le code, mais rien ne l'exécute : un hébergeur impose son
port, place un reverse proxy et attend une application **WSGI**. Ce module est
le pont. Il **présente chaque requête WSGI au handler HTTP existant** — la
requête est reconstituée en texte HTTP depuis l'`environ`, le handler lit et
écrit dans des flux mémoire, et les en-têtes qu'il croyait envoyer sur le réseau
sont interceptés avant d'atteindre le corps — plutôt que de dupliquer le
routeur. Conséquence : un seul jeu de routes, et ce qui est vérifié en local est
exactement ce qui tourne en ligne.

- **Trois voies de publication**, documentées dans `docs/HEBERGEMENT.md` :
  bouton **Render** en deux clics (`render.yaml`), **image Docker** publique
  dans GHCR (construite par `.github/workflows/image-docker.yml`), et la ligne
  `gunicorn … simulateur.wsgi:application` pour tout hébergeur Python.
- **Fichiers d'hébergement** : `Procfile` (Heroku, Scalingo, Clever Cloud,
  Railway, Dokku), `requirements.txt` (gunicorn **seul**, dépendance
  d'hébergement et non d'exécution), `runtime.txt` (Python 3.11.9), `Dockerfile`
  (non-root, avec sonde de santé), `.dockerignore`.
- **`PORT` et `HOST`** sont lus dans l'environnement par
  `python3 -m simulateur.dashboard` : la même commande sert en local et en
  ligne, `--port` restant prioritaire.
- En-têtes hop-by-hop écartés (`Connection`, `Server`, `Date`) : derrière un
  proxy, « Connection: close » ferait fermer la connexion à chaque requête.
- 21 tests (`tests/test_wsgi.py`), dont un qui sert réellement l'application
  par HTTP avec `wsgiref`, et la CI vérifie le point d'entrée à chaque push.
- Aucune formule, donnée source ou seuil n'est modifié.

### Ajout — Partager un réglage par lien

Un budget se discute : encore faut-il pouvoir le montrer, pas seulement le
décrire. Un bouton **🔗 Partager mes réglages** copie une adresse qui rouvre le
simulateur exactement sur les leviers affichés.

- Le lien ne transporte que les **leviers réellement déplacés** par rapport aux
  valeurs neutres du catalogue (`?sim=` + JSON compact) : quelques centaines de
  caractères, jamais les 101 paramètres.
- Une adresse reçue n'est **jamais crue** : seules les clés présentes dans le
  catalogue sont reprises, et seulement si la valeur est un nombre fini. Une
  clé inconnue, une chaîne, un tableau ou un JSON illisible sont ignorés sans
  erreur. Rien n'est injecté dans le HTML : l'avis est écrit en `textContent`.
- Le programme de départ (« mandature ») est laissé de côté quand l'adresse
  porte des réglages : sinon il s'y ajouterait et le lien ne rouvrirait pas la
  simulation partagée. Un bandeau indique combien de leviers ont été repris.
- Rien ne quitte le navigateur : l'adresse est fabriquée côté client, le
  serveur ne la voit pas passer.
- 8 étapes de plus au harnais Node (`tests/navigateur_interface.mjs`), dont
  l'aller-retour complet — réglage modifié → lien → page rouverte sur ce
  réglage — et le refus d'un lien hostile.

### Documentation

- **`docs/HEBERGEMENT.md`** : le dépannage couvre désormais le parcours
  **Blueprints** de Render — branche `main`, **Blueprint Path** vide, et le
  message « Blueprint file `render.yaml` not found on main branch », qui vient
  d'un arbre de dépôt mis en cache et se dissipe par **Retry** une fois
  `render.yaml` présent sur `main`.

## [1.9.0] — 2026-10-08

### Ajout — Compréhensible pour tous : lexique, lecture en clair, guide et sommaire

Un outil démocratique qui n'est lisible que par ceux qui savent déjà n'est pas
un outil démocratique. Quatre dispositifs, tous servis sans dépendance externe :

- **`simulateur/lexique.py`** : **83 termes** en six catégories (budget, marchés,
  Europe, géopolitique, vie quotidienne, lire le simulateur), servis par
  `GET /api/lexique` (recherche par `?q=`). Règle de rédaction : on n'explique
  pas un mot de métier par un autre mot de métier — « spread » est défini comme
  « l'écart entre le taux auquel la France emprunte et celui de l'Allemagne »,
  pas comme un « écart de rendement souverain ». Chaque entrée porte sa
  définition, un repère chiffré quand il existe, et des renvois.
- **Soulignement des termes techniques** dans les textes affichés (console de
  veille, lecture en clair, alertes, provenance) : la définition s'affiche au
  survol ou au focus clavier. Le balisage respecte les attributs HTML — un `>`
  à l'intérieur d'un `data-aide` n'est pas une fin de balise.
- **`simulateur/clarte.py`** : la **« lecture en clair »** d'une simulation. Le
  module ne calcule rien : il relit la sortie du moteur et en tire une dizaine
  de phrases complètes (solde du programme, déficit, dette, taux d'emprunt,
  pouvoir d'achat, domaines, climat social, règles européennes, alertes),
  servies dans le champ `lecture` de `/api/simuler`. Un déficit négatif est dit
  « excédent », une dépense négative « économie », et chaque lecture rappelle
  ses limites. Aucune phrase ne porte de jugement politique.
- **Guide de démarrage** en quatre étapes, affiché à la première visite
  seulement (mémorisé dans le navigateur, jamais transmis au serveur) et
  rouvrable depuis l'en-tête. **Sommaire** en haut de page : comprendre → ce que
  ça donne → régler → mesurer → vérifier.
- Interface v1.9.0.

### Ajout — Compression HTTP négociée (`simulateur/compression.py`)

- Les réponses sont compressées quand le navigateur le demande : **une
  simulation complète passe de 255 Kio à 37 Kio sur le réseau (85 %)**, le
  catalogue de 104 à 25 Kio, le contexte de 97 à 14 Kio, la page de 203 à
  57 Kio. Le contenu est identique ; aucune formule ni donnée n'est touchée.
- Négociation conforme : qualités (`q=`), refus (`q=0`), joker (`*`), préférence
  du serveur à qualité égale. Brotli et Zstandard sont utilisés s'ils sont
  importables, `gzip` sinon ; jamais requis.
- **Jamais à perte** : sous 512 octets, ou si le résultat n'est pas plus petit
  que l'original, la charge brute est renvoyée telle quelle.
- `Vary: Accept-Encoding` sur toute réponse compressible, pour qu'aucun
  intermédiaire ne redistribue du gzip à un client qui ne le décode pas.

### Ajout — Rendu différé des onglets et matrice préservée

- Les sept vues par strate ne sont plus reconstruites à chaque simulation :
  seul l'onglet ouvert l'est, les autres le sont à leur ouverture. Le harnais
  Node vérifie qu'un onglet jamais visité reste vide — c'est l'économie
  recherchée — et que chacun se remplit bien à l'activation.
- La matrice levier × domaine n'était plus recalculée pendant qu'un curseur
  bougeait, donc vidée à chaque geste : l'information disparaissait sous les
  yeux. La dernière matrice calculée est conservée, avec son état de fraîcheur
  affiché (« dernière matrice calculée ») plutôt qu'un écran vide.

### Ajout — Cache du catalogue de bulles

- `GET /api/bulles` coûtait **4,5 s** à chaque appel (101 bulles, 2,1 Mio de
  JSON). Le contenu ne dépendant que du catalogue et du contexte, il est
  mémoïsé : **57 ms** aux appels suivants, invalidé par un rafraîchissement des
  données (l'horodatage du contexte entre dans la clé de cache).

### Documentation

- **`docs/RD_OPTIMISATION_FLUIDITE.md`** : protocole, mesures exécutées, gains
  et — surtout — ce que ces mesures ne disent pas (mesures locales, rendu
  navigateur non profilé, lisibilité non mesurable automatiquement).
- **`outils/mesurer_fluidite.py`** : campagne reproductible, sans réseau,
  bibliothèque standard uniquement (`--markdown`, `--json`).

### Modifié

- Le badge de version d'interface n'est plus figé dans un test : la suite
  vérifie la forme du badge, pas un numéro précis.
- Libellé de la section « Domaines » aligné sur le lexique : un score de 50 est
  un écart **nul** avec la référence, non une « situation de départ ».

Tests : **508 réussis** (416 → 508) ; `ruff check .` propre.

## [1.8.0] — 2026-10-07

### Ajout — Vues locales, nationales, européennes, mondiales, géopolitiques, ménages et boursières

- L'interface ajoute **sept onglets** comparant chaque trajectoire au scénario
  de référence : finances territoriales observées, comptes nationaux et flux
  budgétaires par levier, repères européens, transmission mondiale/géopolitique,
  profil de ménage et marchés boursiers.
- Le profil ménage reste dans le navigateur : revenus, cotisations, IR par part
  de quotient familial, aides déclarées, panier INSEE par poste, prix projetés
  et mensualité théorique d'un prêt. Ce n'est ni une liquidation fiscale, ni
  une moyenne de foyer, ni un droit individuel; le profil n'est jamais envoyé
  à l'API.
- `/api/marches` et `simulateur/marches.py` proposent un univers **représentatif
  de 13 indices**, avec devise, source tierce, cours, variation, horodatages,
  liens de places et état de fraîcheur. Les fermetures locales/jours fériés
  possibles, retards et cours de plus de 72 h sont explicitement signalés;
  aucun cours manquant n'est remplacé par zéro.
- Les curseurs de stress et expositions P/L brutes sont séparés du moteur macro.
  Ils couvrent les tranches marginales IR (barème 2026, par part), entreprises,
  associations, organismes/établissements publics et privés, élus à titre
  personnel, communes, EPCI/métropoles, départements, régions/CTU et outre-mer.
  Les expositions sont des saisies de scénario, non des portefeuilles ou
  détentions observés; les catégories peuvent se recouvrir et sont à saisir
  sans double compte.
- Les repères territoriaux signalent les limites : hameaux/quartiers sans budget
  autonome, données OFGL agrégées, absence de projection par collectivité
  individuelle et absence de ventilation DROM/COM dans ce build. L'onglet
  national sépare flux budgétaires de leviers et comptes publics observés.
- Fraîcheur distincte du calcul : un scénario se recalcule immédiatement, mais
  les cours dépendent du fournisseur tiers et des séances de chaque place.
  Indices non exhaustifs, pas de change/frais/dividendes/fiscalité dans le P/L;
  les chocs boursiers ne modifient pas encore PIB, emploi, impôts ou dette.
- Ajustement de seuil : une baisse modélisée de pouvoir d'achat de 9,8 points
  d'indice passe en « risque » plutôt qu'en « hors-sol »; le seuil de rupture
  interne au simulateur est explicité à −15 % (ce n'est pas un seuil officiel),
  évitant qu'une trajectoire de référence déclenche seule le bandeau le plus grave.
- Interface v1.8.0. Tests : **416 réussis** ; `ruff check .` propre.

## [1.7.2] — 2026-10-07

### R&D — Phase 2 « deux mandatures consécutives » (points P16-P21)

- Le catalogue passe de **97 à 101 leviers** : rattrapage du patrimoine
  public, capital humain à cycle long, capacité BITD et charge explicite de
  réformes simultanées ; le levier d'adaptation existant est réutilisé.
- Le simulateur propose un **horizon interactif de 5 ou 10 ans** ; le choix
  est propagé à la requête `/api/simuler` et au conseiller `/api/conseil`.
  Le préréglage « Deux mandatures » sélectionne 10 ans.
- Le bilan P21 expose un **ledger intergénérationnel séparé**, sans score
  composite : dette, besoin patrimonial proxy, investissements engagés/mûrs,
  pertes climatiques annualisées et dommages évités.
- Hypothèses documentées et non prophétiques : patrimoine 145/24 Md€/an,
  climat 143/30 Md€/an (hors budget APU), ratio Barnier annualisé 8/30,
  maturités exploratoires de 8 et 6 ans ; saturation administrative =
  stress-test explicite, sans seuil officiel universel. Audit UI complété avec
  les sources Cour des comptes, PNACC-3, LPM et INSEE.
- Les dommages climatiques ne sont **pas** comptabilisés comme dépense APU ;
  les stocks de capital humain/BITD ne reçoivent pas de rendement PIB ou de
  prime de spread non mesurés.
- Interface v1.7.5. Tests : **399 réussis** ; `ruff check .` propre.

## [1.7.1] — 2026-10-06

### Corrigé — Plus aucune bulle d'aide ne recouvre les résultats

- Les infobulles volantes ne s'affichent plus **pendant un réglage en cours**
  ni **quand une bulle « interactions » est ouverte** : le badge coût/gain
  live, la fiche d'interactions et la console de veille restent lisibles,
  rien ne vient les couvrir. Le verrou est dans `survoler()`, unique chemin
  d'affichage — valable pour l'ensemble des réglages et des fonctionnalités.
- L'infobulle est aussi masquée dès le début d'un geste sur un levier et à
  l'ouverture/fermeture d'une bulle.
- Le coût / gain global des réglages croisés sort de la zone repliable : il
  est désormais juste sous le verdict de la console, toujours visible.
- Version d'interface affichée en pied de page (v1.7.4) pour repérer les
  pages périmées. Tests : 389.

## [1.7.0] — 2026-10-06

### Ajout — Coût / gain réel en direct (bulle + veille) et audit de traçabilité complet

La bulle du réglage déplacé se rafraîchit désormais **dès le mouvement**, et
deux indicateurs visuels affichent en temps réel le coût / gain réel : l'un
dans la console de veille pour les réglages globaux croisés, l'autre dans la
bulle pour le réglage précis — en rouge / vert transparent, ancrés sur les
chiffres clefs des sources officielles, citées partout.

- **`simulateur/conseil.py`** : le conseil livre maintenant le `budget` réel
  du mouvement (Δ recettes, Δ dépenses, Δ solde, Δ charge de la dette,
  Δ déficit en Md€ / pt de PIB) et les `sources` : les chiffres clefs
  officiels qui ancrent le calcul (PIB, OAT, Bund, spread, BCE, inflation,
  chômage, Brent, change), chacun avec sa valeur, sa période et sa source.
- **`simulateur/seuils.py`** : `bareme_public()` publie le barème complet des
  31 garde-fous (26 absolus + 5 en écart) avec strates, bornes et sources
  institutionnelles ; les bornes infinies sont sérialisées en JSON strict.
- **`simulateur/dashboard.py`** : route `GET /api/garde_fous` (audit).
- **`simulateur/interface.py`** :
  - la bulle du réglage porte un bloc « mesure live » qui affiche
    immédiatement « calcul en cours » dès le début du geste, puis le
    **coût / gain réel de ce réglage précis** (bannière rouge ou verte en
    transparence, détail recettes / dépenses / déficit / charge de la dette,
    sources officielles citées), rafraîchi par mise à jour DOM directe sans
    re-rendu de la grille ;
  - la console de veille affiche le **coût / gain réel des réglages globaux
    croisés** (recettes nouvelles, dépenses nouvelles, solde net, déficit et
    dette finals), recalculé à chaque simulation ;
  - nouvelle section « 🔍 Audit & traçabilité » en bas de page : sources
    officielles de chaque donnée d'entrée (valeur, période, statut, licence,
    URL), formule + source des 74 indicateurs des 20 domaines, champ + effets
    déclarés + source des 97 leviers, barème complet des garde-fous, méthode
    des dynamiques croisées — tout recoupement est possible, le simulateur
    n'est pas une boîte noire ; bouton « 🔍 Audit & sources » dans l'en-tête ;
  - pied de page et bannière **MRSC** : outil open-source produit par son
    créateur pour l'intérêt général, gratuit, paternité protégée.
- **Tests** : budget et sources du conseil, barème public, blocs live de la
  bulle et de la veille, section audit, attribution MRSC ; le harnais
  navigateur vérifie le rendu du coût global, de l'audit et du bloc live dans
  la bulle. Suite : 388 tests.

## [1.6.0] — 2026-10-06

### Ajout — Conseiller temps réel (« effet papillon ») sur chaque mouvement de réglage

Chaque geste sur un réglage — **tous** les leviers, curseurs comme
interrupteurs, sans exception — est désormais traité comme une décision : la
position à l'instant T comparée à la position avant le dernier mouvement. Le
conseiller met à jour **en temps réel** toutes les interactions et tous les
textes d'aide de la console de veille.

- **`simulateur/conseil.py`** (nouveau) : le moteur est rejoué deux fois, le
  levier à sa position d'avant puis d'après le geste, toutes choses égales ;
  la différence exacte de la décision alimente une lecture de conseiller
  spécialisé : formulation du mouvement, effets **directs** (thèmes déclarés)
  et effets **par ricochet** (les domaines qui bougent sans être déclarés —
  l'effet papillon mesuré, pas supposé), grandeurs qui basculent, garde-fous
  dont le niveau change, journal institutionnel nouveau, pistes de
  compensation et verdict global.
- **`simulateur/dashboard.py`** : route `POST /api/conseil` (corps :
  `parametres`, `cle`, `avant`, `apres`, `horizon` optionnel) ; 400 si la
  `cle` manque.
- **`simulateur/interface.py`** : panneau « 🦋 Conseiller temps réel » dans la
  console de veille ; `MOUVEMENT` capture la position d'avant chaque geste
  avant toute écriture, la simulation déclenchée appelle `/api/conseil` et
  rend la lecture, les ricochets, les garde-fous et les compensations ;
  l'aide au survol du levier rappelle le dernier mouvement.
- **Tests** : `tests/test_conseil.py` (16 tests : formulation, structure,
  isolation du mouvement, direct vs ricochet, seuils de bruit, garde-fous,
  endpoint) ; deux étapes navigateur vérifient l'appel `/api/conseil` et le
  rendu du panneau. Suite : 380 tests.

## [1.5.0] — 2026-10-06

### Ajout — R&D « deux mandatures consécutives » (2027-2037)

Inventaire et modélisation des points stratégiques qui n'existent que sur la
période de dix ans : calendrier électoral, verrou constitutionnel, usure du
capital politique, second dividende de la dette, investissements à cycle long.
Document de référence : [`docs/RD_DOUBLE_MANDATURE.md`](docs/RD_DOUBLE_MANDATURE.md).

- **`simulateur/model.py`** : six nouveaux champs de `DecisionPolitique`, tous
  neutres par défaut (`annee_electorale_majeure`, `usure_politique_pts`,
  `verrouillage_irreversibilite`, `clause_revoyure_evaluation`,
  `reinvestissement_dividende_dette_mde`, `investissements_cycle_long_mde`) ;
  trois champs de résultat (`usure_politique_pts`,
  `irreversibilite_reformes_active`, `investissements_matures_mde`).
- **`simulateur/moteur.py`** : prime de risque électorale sur le spread
  (+12 bps sans verrou, +4 bps verrouillé), usure du capital politique
  (confiance, tension, risque de censure), verrou constitutionnel
  (+2 pts de confiance), clauses de revoyure, dividende de la dette réinvesti
  (multiplicateur 0,55, dépense gagée sans déficit) et investissements à cycle
  long (coût immédiat, rendement 8 %/an plafonné 2,5 Md€ par programme après
  cinq ans : courbe en J).
- **`simulateur/scenarios.py`** : deux scénarios décennaux —
  `get_scenario_double_mandature()` (2027-2037 : mandature 1, élection 2032,
  verrou en année 6, dividende 3→8 Md€, usure croissante, élection 2037) et
  `get_scenario_alternance_2032()` (stress-test sans verrou).
- **`simulateur/cli.py`, `simulateur/dashboard.py`, `extension_eva/main.py`** :
  scénarios `double_mandature` et `alternance_2032` exposés au menu (options
  14-15), à la ligne de commande, à l'API du tableau de bord et à l'adaptateur
  ÉVA (11 scénarios au total).
- **`simulateur/parametres.py`** : quatre leviers dédiés
  (`verrouillage_irreversibilite`, `clause_revoyure_evaluation`,
  `dividende_dette_reinvesti`, `investissements_cycle_long`) et le préréglage
  « Deux mandatures consécutives (2027-2037) » — catalogue porté de **93 à
  97 leviers** et de **13 à 14 préréglages** ; bulles explicatives générées
  automatiquement pour les nouveaux leviers.
- **`simulateur/seuils.py`** : deux garde-fous nouveaux — « Usure du capital
  politique » (strate 2, cible ≤ 20 pts sur dix ans) et « Verrou
  constitutionnel des réformes » (strate 2 : l'absence de verrou est signalée
  en vigilance sur toute simulation, car c'est le risque systémique de la
  période). Garde-fous portés de 33 à 35.
- **`tests/test_double_mandature.py`** : 16 tests nouveaux — neutralité
  stricte des scénarios quinquennaux (valeurs publiées vérifiées au centième),
  complétude des scénarios décennaux, dynamiques isolées, leviers pilotant
  réellement le moteur, garde-fous présents dans le diagnostic. Compteurs mis
  à jour dans `test_integration_branches.py`, `test_dashboard.py`,
  `test_parametres.py` et `tests/navigateur_interface.mjs`.
- **Documentation** : `README.md` (scénarios et section R&D),
  `docs/README.md` (index), références « 93 leviers / 13 préréglages »
  actualisées dans la documentation vivante et les outils du dépôt
  (`outils/details_depot.py`, `outils/apercu_social.py`,
  `docs/SIMULATEUR_PARAMETRABLE.md`, `docs/REPOSITORY_DETAILS.md`).

## [1.4.3] — 2026-10-05

### Correction — Repli documentaire exprimé dans l'unité du modèle

- **`simulateur/donnees_live.py`** : la réconciliation du repli avec le snapshot
  daté applique désormais la **conversion de l'indicateur**. Le repli hors ligne
  valait l'unité de la source (Eurostat publie le PIB en **millions** d'euros) au
  lieu de celle du modèle : `pib_nominal_mde` valait 2 991 055,9 au lieu de
  2 991,06 Md€. Le défaut restait masqué tant que la collecte tournait, car le
  collecteur convertit, lui, chaque lecture ; il n'apparaissait donc que dans les
  exécutions sans réseau.
- **`simulateur/donnees_live.py`** : nouveau paramètre `hors_ligne` de
  `construire_contexte()` et variable d'environnement `SIMULATEUR_HORS_LIGNE=1`.
  Aucun appel réseau n'est alors effectué : le contexte vient du cache et du
  snapshot daté. Les tests s'en servent pour être **déterministes sur une machine
  connectée** comme hors ligne.
- **Tests** : les contextes de test sont explicitement hors ligne ; les suites qui
  démarrent un serveur posent `SIMULATEUR_HORS_LIGNE=1` (plus de collecte réseau
  pendant les tests : c'était la cause des échecs et de la lenteur de la CI).
  Nouveaux tests : conversion du repli alignée sur l'indicateur, concordance des
  deux chemins hors ligne, bornes du PIB de repli.

## [1.4.2] — 2026-10-05

### Correction — Prise en charge des sondes `HEAD` (affichage des aperçus)

- **`simulateur/dashboard.py`** : `do_HEAD` répond désormais comme `GET` mais
  sans corps (statut, `Content-Type` et `Content-Length` corrects). Les aperçus
  hébergés et les moniteurs vérifient la disponibilité par un `HEAD` : le 501
  renvoyé jusqu'ici pouvait laisser l'aperçu vide alors que le serveur
  fonctionnait. Concerne `/`, les routes `/api/*` et les exports.
- **`tests/test_dashboard.py`** : `HEAD /` et `HEAD /api/catalogue` vérifiés
  (200, en-têtes complets, corps vide).

## [1.4.1] — 2026-10-05

### Ajout — Aides au survol (infobulles) sur tous les réglages et boutons

- **`simulateur/interface.py`** : couche d'infobulle instantanée
  (`initialiserInfobulles()`, `survoler()`, `texteAideLevier()`) affichée au
  survol **et** au focus clavier, `pointer-events:none`, masquée au clic, au
  défilement et à l'ouverture d'une bulle.
- **93 réglages annotés** : curseurs, interrupteurs, étiquettes de nom et de
  valeur, cartes de levier (vue confort et vue compacte) — l'aide donne la
  famille, l'unité, la valeur courante et le défaut, la plage et le pas, la
  description, les effets déclarés, les mesures en direct sous le curseur et les
  mouvements aux bornes.
- **Boutons et contrôles annotés** : rafraîchir, réinitialiser, simuler,
  exports JSON/CSV, densité, détails des seuils, « régler les 93 leviers »,
  recherche, case de vue compacte, puces d'impact, puces de strate, cartes de
  domaine, préréglages et scénarios.
- **Tests** : 2 tests statiques de plus (couche passive, annotation des zones
  interactives) et **8 étapes de plus dans le harnais Node** (85 au total) —
  zones d'aide par réglage, contenu de l'aide, affichage, masquage, boutons
  annotés.
- **`docs/SIMULATEUR_PARAMETRABLE.md`** : sous-section « Aides au survol » du
  § 6 (tableau élément survolé → contenu).

## [1.4.0] — 2026-10-05

### Ajout — Bulles explicatives par réglage (93 leviers)

- **`simulateur/bulles.py`** (nouveau) : chaque levier reçoit une fiche
  **calculée**, jamais rédigée à la main, en trois étages :
  1. *chaîne d'interaction* — ligne budgétaire ou champ moteur → médiateurs émis
     (Md€, points, milliers) → indicateurs qui les lisent, avec coefficient et
     domaine, en signalant les relais indirects (autre échelle, agrégat
     budgétaire) et l'absence de relais ;
  2. *répercussions mesurées* — simulation réelle à chaque borne du réglage (et
     un pas au-delà du défaut), réglage isolé : score des 20 domaines, écart des
     indicateurs, niveau des 33 garde-fous, risque population, strates 1 à 5 et
     journal institutionnel ;
  3. *lecture guidée* — opportunités et désagréments classés, points à
     surveiller (garde-fous aggravés, strate concernée) et pistes de
     compensation tirées des effets déclarés des autres leviers.
  Mesure sur le catalogue actuel : **92 leviers sur 93** déplacent au moins un
  domaine à leurs bornes ; **0 médiateur orphelin** ; l'exception
  `clause_sauvegarde_defense` est documentée (effet PDE journalisé en strate 3).
- **`simulateur/interface.py`** : bouton « interactions » sur chacun des
  93 réglages, bulle dépliée **dans la carte du levier** (vue confort et vue
  compacte), donc jamais par-dessus les paramètres ; contenu chargé à la demande
  depuis `/api/bulle` et mis en cache par levier.
- **`simulateur/dashboard.py`** : `GET /api/bulles` (catalogue complet ou
  sélection, `detail=resume`, `mesure=0`) et `GET /api/bulle?levier=…`
  (fiche complète) ; levier inconnu ou détail inconnu → 400 explicite.
- **`tests/test_bulles.py`** (21 tests) : couverture des 93 bulles, mapping
  exhaustif des 44 thèmes déclarés, cohérence bilan/mesures, cache, allègement
  du détail, garde-fou sur les médiateurs orphelins, coût de calcul.
- **Harnais navigateur** : 8 étapes de plus (77 au total) — bouton sur chaque
  réglage, ouverture, contenu (chaîne, mesures, lecture, effets déclarés),
  accessibilité maintenue des 93 réglages, fermeture.
- **`docs/SIMULATEUR_PARAMETRABLE.md`** : nouvelle section 6 « Les bulles
  explicatives par réglage » (méthode, chiffres mesurés, limites).

## [1.3.0] — 2026-10-05

### Ajout — Simulateur paramétrable (remplace le tableau de bord à cartes figées)
- **`simulateur/parametres.py`** : 93 leviers de politique publique en 14 familles
  (fiscalité, dépenses, réformes institutionnelles, énergie, industrie, logement,
  défense…), 13 préréglages doctrinaux et un validateur `normaliser()` qui borne
  et type toutes les valeurs reçues du client.
- **`simulateur/domaines.py`** : 20 domaines d'action publique, 74 indicateurs
  concrets (formule lisible + source), chaîne de médiateurs annuels et notation
  0-100 par écart à la trajectoire de référence (50 = aucune politique).
- **`simulateur/moteur_parametrique.py`** : orchestrateur — trajectoire de
  référence, boucle de convergence des médiateurs, cinq exercices budgétaires sur
  les cinq échelons, synthèse, matrice d'impacts croisés levier × domaine calculée
  par différences finies, comparateur de préréglages, calibrage du contexte.
- **`simulateur/donnees_live.py`** : 38 indicateurs publics sourcés et licenciés
  (Eurostat, BCE SDMX, Frankfurter, Banque mondiale, Opendatasoft, Yahoo, Stooq),
  snapshot daté, collecte serveur (7 adaptateurs) et collecte navigateur, avec
  repli hors ligne réconcilié sur le snapshot.
- **`simulateur/seuils.py`** : 33 garde-fous répartis sur les cinq strates et
  quatre paliers (tolérable → vigilance → risqué → hors-sol), seuils absolus et
  seuils d'écart, messages chiffrant la distance de retour, indice de risque pour
  la population, marges de manœuvre et audaces possibles.
- **`simulateur/interface.py`** : page unique sans dépendance externe — ruban de
  veille collant, 93 leviers en vue confort ou compacte (une ligne par levier),
  puces d'impact sous chaque levier réglé, 20 domaines, cascade des 5 échelons,
  exports JSON/CSV, rafraîchissement des API publiques depuis le navigateur.
- **`simulateur/dashboard.py`** : routes paramétriques `/api/catalogue`,
  `/api/contexte`, `/api/simuler` (GET et POST), `/api/comparer`, `/api/presets`,
  `/api/proxy` (liste blanche du registre, pas de proxy ouvert), `/api/donnees`,
  plus les routes historiques conservées.
- **`outils/`** : `apercu_social.py` (vignette 1280 × 640), `details_depot.py`
  (réglages du dépôt), `reglages_depot.html` (application depuis le navigateur).

### Correction
- **Chocs exogènes** : ils sont désormais appliqués en niveau et mémorisés
  (`MoteurSimulationSystemique._chocs_appliques`) — un choc maintenu cinq ans ne
  s'empile plus d'année en année (Brent année 1 = année 5).
- **`tests/verificateur_js.py`** : un objet littéral dans une substitution
  (`` `${f({})}` ``) était pris pour l'accolade fermante du gabarit (faux positif),
  corrigé par suivi de la profondeur de pile à l'entrée de chaque substitution.
- **Interface** : le compteur de leviers actifs compare par clé (et non par
  position) ; la grille n'est plus reconstruite pendant la manipulation d'un
  curseur (re-rendu au relâchement).

### Documentation
- `docs/SIMULATEUR_PARAMETRABLE.md` (fonctionnement, seuils, limites assumées),
  `docs/REPOSITORY_DETAILS.md` (réglages du dépôt), `NOTE_POUR_CLAUDE.md` (note de
  reprise), `README.md`, `docs/README.md`, `CONTRIBUTING.md` (5 échelons).

### Tests
- **310 tests**, dont `test_parametres` (23), `test_domaines` (23),
  `test_donnees_live` (17), `test_moteur_parametrique` (30), `test_seuils` (26),
  `test_interface` (26), `test_dashboard` (28) ; `tests/test_interface_navigateur.py`
  exécute réellement le JavaScript de la page dans Node (69 étapes du parcours
  utilisateur, réponses du vrai serveur).

## [1.2.1] — 2026-10-03

### Correction — Dashboard web : grille de scénarios vide
- **Bug principal** : dans `renderScenarios()`, l'appel `grid.appendChild(card)` était absent.
  Les cartes de scénarios étaient bien créées en mémoire mais jamais insérées dans le DOM :
  la grille restait vide et **aucun scénario n'était cliquable** dans le dashboard web.
- **Événement explicite** : `runScenario()` s'appuyait sur la variable globale implicite `event`,
  non disponible de façon fiable hors des navigateurs qui l'exposent sur `window`.
  L'événement est désormais transmis explicitement (`card.onclick = (ev) => runScenario(key, ev)`),
  avec un repli sur `card.dataset.key` pour la surbrillance de la carte sélectionnée.
- **Exports** : les boutons « Exporter JSON / CSV » sont activés dès qu'une simulation a tourné
  (fonction `activerExports()`, appelée après le rendu des résultats).
- **Auto-run** : le scénario `mandature` est lancé automatiquement au chargement de la page.
- **Serveur** : passage à `ThreadingHTTPServer` (`daemon_threads = True`) et `protocol_version`
  `HTTP/1.1`, pour rester réactif derrière un proxy qui maintient des connexions persistantes.
  Toutes les réponses annoncent désormais un `Content-Length` exact, y compris les 404/405
  (sans quoi un client keep-alive attendrait indéfiniment la fin de la réponse).
- **6 tests de non-régression d'interface** ajoutés dans `tests/test_dashboard.py` :
  `appendChild` présent, événement explicite sans globale `event`, auto-run de `mandature`,
  9 scénarios exposés, balises `<div>` équilibrées, serveur multi-thread/HTTP 1.1 keep-alive.
  **Total : 147 tests verts** (141 précédents + 6), `ruff check .` OK.

## [1.2.0] — 2026-10-03

### Ajout — STRATE 5 : GÉOPOLITIQUE, SÉCURITÉ & CHAÎNES D'APPROVISIONNEMENT
- **Nouveau module `simulateur/geopolitique.py`** : `EchelonGeopolitique`, `PointDePassageStrategique`,
  `EffetsGeopolitiques` et la fonction de propagation `propager_geopolitique()`. Le modèle gigogne
  passe de **4 à 5 échelons** ; la strate 5 est résolue en premier et alimente les strates 4 → 1.
- **Éléments auparavant manquants, désormais intégrés** (recommandations §9 de
  `docs/ANALYSE_TENSION_GLOBALE_2026.md`, jamais implémentées) :
  indices de tension des 4 théâtres (Taïwan, Ukraine-OTAN, Iran-Israël-US, convergence des blocs),
  risque et usage nucléaire tactique, 7 chokepoints stratégiques, disponibilité des semi-conducteurs,
  effort de défense et trajectoire OTAN de La Haye, cyber-résilience NIS 2, réserves stratégiques AIE,
  clause de sauvegarde nationale du Pacte de stabilité, probabilité d'escalade mondiale.
- **13 nouveaux leviers de décision** dans `DecisionPolitique` (`blocus_taiwan_intensite`,
  `fermeture_hormuz_intensite`, `usage_nucleaire_tactique`, `cyberattaque_systemique`,
  `effort_defense_cible_pct_pib`, `mobilisation_economie_de_guerre`, `liberation_stocks_strategiques`,
  `plan_souverainete_semiconducteurs_mde`, `activation_clause_sauvegarde_nationale_ue`, deltas de tension).
- **9 nouveaux indicateurs de sortie** dans `ResultatEtapeSimulation` (tension composite, probabilité
  d'escalade mondiale, risque nucléaire, disponibilité des puces, effort et dépenses de défense,
  prime de risque géopolitique, chokepoints sous tension, réserves pétrolières).
- **5 nouveaux scénarios** : `crise_taiwan` (A), `escalade_nucleaire` (B), `hormuz` (C),
  `convergence_ww3` (D) et `resilience` (Mandature + réarmement OTAN 3,50 % du PIB).
- **CLI refondue** : catalogue central `CATALOGUE_SCENARIOS`, menu à 13 entrées, comparatif des
  9 scénarios, bloc d'analyse « Strate géopolitique » dans le détail annuel.
- **Dashboard web** : 5 nouvelles cartes de scénarios, bandeau de la strate 5 et 6 métriques
  géopolitiques supplémentaires dans l'API `/api/run`.
- **12 textes juridiques ajoutés au `REGISTRE_LEGAL`** : Constitution art. 15 et 35, LPM 2023-703,
  Traité de l'Atlantique Nord art. 3 (La Haye, 5 % du PIB) et art. 5, TUE art. 42§7,
  Règlement (UE) 2024/1263 (clause de sauvegarde), Règlement (UE) 2023/1781 (Chips Act),
  Directive (UE) 2022/2555 (NIS 2), Code de l'énergie L. 642-2, CNUDM art. 37-38, TNP art. VI.
- **28 nouveaux tests** (`tests/test_geopolitique.py`) : calibrage sourcé, non-régression des
  4 scénarios historiques, invariants stocks-flux et parité des taux sous choc de guerre,
  déterminisme bit-à-bit, non-divergence sur 15 ans de guerre mondiale continue. **Total : 61 tests verts.**
- **Documentation** : `docs/08_STRATE_GEOPOLITIQUE_ET_SCENARIOS_DE_GUERRE.md` (audit des éléments
  manquants, phases de recherche, calibrage sourcé, équations, résultats, validation).
- **Exports** : `resultats_crise_taiwan.json`, `resultats_hormuz.json`,
  `resultats_escalade_nucleaire.json`, `resultats_convergence_ww3.json`, `resultats_resilience.json`.

### Modification
- La prime de risque géopolitique est injectée **dans le spread OAT-Bund** (et non hors modèle),
  ce qui préserve exactement l'équation de parité `OAT = Bund + spread/100`.
- La prime pétrolière de chokepoint est appliquée **en niveau** (retrait puis réapplication) :
  aucune accumulation d'année en année, idempotence et non-divergence garanties.
- L'assiette fiscale est désormais indexée sur le PIB **corrigé des chocs géopolitiques**.
- Après un franchissement du seuil nucléaire, la notation souveraine ne peut pas remonter
  au-dessus de `A-` (mémoire du risque).

### Correction
- Aucune régression : les 4 scénarios historiques (`mandature`, `statut_quo`, `austerite`,
  `choc_mondial`) produisent des résultats **strictement identiques** à la version 1.1.0
  (la prime géopolitique de référence calée à l'instant T est neutralisée pour éviter tout double comptage).

## [1.1.0] — 2026-10-01

### Ajout
- **Export JSON** : les résultats de simulation peuvent être exportés vers un fichier `.json` structuré (`--export results.json`).
- **Export CSV** : les résultats peuvent être exportés vers un fichier `.csv` avec une ligne par année (`--export results.csv`).
- **Menu interactif** : deux nouvelles options (6 = export JSON, 7 = export CSV) et intégration du scénario `choc_mondial` dans le comparatif (option 5).
- **pyproject.toml** : packaging officiel avec entry-points (`simulateur-mpol`, `simulateur-mpol-run`) et métadonnées complètes.
- **CI/CD GitHub Actions** : tests sur Python 3.11–3.14, lint ruff, smoke-test incluant export JSON/CSV.
- **Benchmark script** : `benchmarks/benchmark.py` mesurant latence, It/s et usage mémoire.
- **CONTRIBUTING.md** et **CHANGELOG.md**.

### Correction
- **Bug critique** : `choc_mondial` était absent de la validation des scénarios dans `main.py` et `cli.py` (`__main__`). Le scénario était importé mais pas accessible par CLI.
- **Bug critique** : `get_scenario_choc_mondial_stagflation` n'était pas importé dans `cli.py`, provoquant un `NameError` à l'exécution.
- **Comparatif** : le scénario `choc_mondial` était manquant du comparatif multi-scénarios (option 5).

## [1.0.0] — 2026-09-20

### Ajout
- Moteur de simulation systémique à 4 échelles interconnectées (Local, National, Europe, Mondial).
- 4 scénarios de simulation : Mandature républicaine (+60 Md€/an), Statut Quo, Austérité brutale, Choc mondial stagflation.
- Corpus juridique intégré (Constitution, CGCT, directives UE, Code pénal, etc.).
- Extension ÉVA (Protocole v4.2.3) : intégration du moteur dans le cerveau cognitif d'ÉVA.
- Tests unitaires (init, cohérence strates, stress, idempotence, export).
- CLI interactive et exécution directe (`python3 main.py [scenario]`).
