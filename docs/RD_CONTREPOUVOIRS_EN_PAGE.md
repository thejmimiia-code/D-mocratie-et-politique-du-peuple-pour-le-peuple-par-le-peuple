# R&D — Les contre-pouvoirs entrent dans la page

**Passe du 14 octobre 2026.** Ce document raconte un trou que personne n'avait
mesuré, comment il a été trouvé, ce qui a été montré à l'écran, et ce qui reste
hors de l'écran — avec la raison écrite de chaque absence.

---

## 1. Le constat, par la mesure

Le moteur sert **22 routes**. La page en mettait en œuvre **14**. Les huit
autres n'étaient pas des oublis : chacune était appelée ailleurs — par la veille
en ligne, par les tests du serveur, par les clients de l'API. Mais **rien ne le
disait**, et rien ne le vérifiait. C'est ainsi qu'on découvre, un an plus tard,
qu'un contenu servi tous les jours n'a jamais été lu par personne.

Le contrôle de couverture (`tests/test_couverture_des_routes.py`, écrit dans
cette passe) a transformé la question en comptabilité : chaque route servie est
soit **mise en œuvre par la page** — un `fetch`, ou un lien qu'elle donne au
lecteur, comme les fiches de droit positif —, soit **excusée par écrit**, avec
la raison et le nom de ce qui la remplace.

Il a nommé ce que l'œil ne voyait pas. Trois registres entiers, calculés par le
moteur, contrôlés par ses tests, **sans aucun écran** : ils pesaient 229 097
octets à eux trois.

| Route | Volume (brut) | Ce qu'elle contient | Écran, avant cette passe |
|---|---:|---|---|
| `/api/contrepouvoirs` | 78 084 o | 31 manœuvres institutionnelles, leurs seuils chiffrés, les 6 familles, la composition des deux chambres | aucun |
| `/api/dynamiques` | 117 238 o | 8 trajets législatifs (47 battements), 12 fentes non écrites, 15 stratégies, 26 autorités, 7 boucles de contrôle, 6 étages de normes | aucun |
| `/api/instances` | 33 775 o | vue courte des mêmes autorités | aucun |

Les deux premiers modules du moteur — `simulateur/gouvernance_contrepouvoir.py`
et `simulateur/instances_et_dynamiques.py` — ont été ajoutés avec leurs tests et
leurs sources ; la page, elle, n'a jamais suivi. Le site M.R.S.C, lui, exposait
même ces familles à son API publique avant que la page ne les affiche.

---

## 2. La décision

**Deux blocs, une section, un seul chargement.** « Contre-pouvoirs, en chiffres »
se place juste après les verrous, dont elle est la suite logique : les verrous
disent ce qui tient ou lâche sous un curseur, l'arithmétique dit ce que chaque
manœuvre exige et ce que chaque trajet coûte en jours de rigueur.

Trois règles ont guidé l'écriture :

1. **Aucun chiffre n'est recalculé dans le navigateur.** La page additionne ce
   que le serveur lui donne, jamais ce qu'elle croit savoir. Aucun seuil du
   droit positif n'est écrit dans le source de la page — le contrôle statique
   refuse les majorités de la Constitution jusque dans le JavaScript.
2. **Quand le registre ne répond pas, la page dit l'absence.** Elle n'affiche
   pas des nombres recomposés, qui se liraient comme des nombres du droit.
   C'est la règle déjà suivie pour l'audit et pour les verrous.
3. **L'état vit en mémoire, le rendu en découle.** Cocher une formation ou
   filtrer une famille recalcule l'affichage à partir de l'état : un seul chemin
   pour un seul résultat, donc un seul endroit où se tromper.

**Le chargement ne coûte rien au démarrage.** Les deux routes pèsent 195 322
octets bruts, **44 108 octets compressés**. Elles ne sont pas chargées au
démarrage : un `IntersectionObserver` les demande quand la section approche de
l'écran, et un bouton « Charger maintenant » fait le même travail s'il manque —
un navigateur sans observateur garde une page qui marche.

**Ce que la page paie quand même :** le code de la section ajoute **7 603
octets compressés** à la page (110 141 o compressés après la passe). C'est le
prix de trente-et-une fiches lisibles, et il se paie une fois.

---

## 3. Ce que la section montre

### Bloc 1 — L'arithmétique des contre-pouvoirs

- **L'état des assemblées, daté.** Le registre porte sa date (`date_etat_des_assemblees`) ;
  la page l'affiche. Une composition parlementaire non datée est une composition
  qu'on croit éternelle.
- **Une barre de sièges par chambre**, une part par formation : 12 groupes à
  l'Assemblée nationale (577 sièges, 574 pourvus), 10 au Sénat (348 sièges). Les
  teintes sont **calculées** (`137.5°` par rang, méthode de la section d'or) :
  aucune couleur de groupe n'est écrite à la main, donc aucune ne vieillit avec
  un remaniement.
- **Les seuils de la chambre** : majorité absolue, trois cinquièmes, deux tiers,
  un cinquième, un dixième, seuil de groupe constitué — tous servis, tous
  affichés, aucun recopié.
- **Une coalition qui se compose.** Cocher des formations additionne leurs
  sièges et dit quels seuils **de la chambre** la somme atteint, et combien de
  voix manquent pour le suivant. La page accompagne le chiffre d'une phrase de
  prudence : cette somme dit ce qu'une coalition pèse, pas ce qu'un texte
  devient — le seuil propre à chaque manœuvre est dans sa fiche. Sans cette
  phrase, un total affiché deviendrait une prédiction.
- **Les 31 manœuvres, famille par famille** : résumé, qui agit, condition, les
  seuils chiffrés (`577 → 289 voix`), la citation du texte, ce que la manœuvre
  déclenche, ce qui peut l'empêcher, ce qu'elle devient dans le moteur,
  l'observation historique et le coût politique. Les articles cités renvoient à
  leur fiche servie par `/api/constitution` — un lien seulement là où la fiche
  existe, jamais une adresse inventée qui rendrait un 404 au lecteur.
- **Le filtre par famille** : six pastilles, `aria-pressed` pour dire l'état,
  un second clic pour revenir à tout.

### Bloc 2 — Le temps des procédures

- **Le rapport de temps**, en quatre sens : avancer (19 battements, 289 jours),
  reculer (2, 43), bloquer (11, 113), verrouiller (15, 205). Le tableau porte
  l'avertissement du registre : « les jours sont des délais de rigueur, pas des
  durées prévisibles ».
- **La fenêtre législative résiduelle** (150 jours au 12 octobre 2026), avec sa
  note : c'est le seul chiffre du module qui soit un constat daté, pas une règle.
- **L'asymétrie** : pour chaque trajet, les jours de retard opposables, si un
  veto existe vraiment, et son fondement.
- **Les 8 trajets, battement par battement** : acte, de qui vers qui, fondement,
  jours, condition — la navette se lit au lieu de se deviner.
- **Les 12 fentes non écrites**, **les 15 stratégies**, **les 26 autorités**,
  **les 7 boucles de contrôle**, **les 6 étages de normes** et leurs attaquants,
  les **8 effets** qu'un juge peut produire : chaque collection que le serveur
  envoie est rendue, dans un dépliant, sans que la page en résume ni n'en cache
  une ligne.

---

## 4. Ce qui surveille cette section

### Le contrôle de couverture (`tests/test_couverture_des_routes.py`, 11 contrôles)

| Ce qu'il refuse | Pourquoi |
|---|---|
| une route servie que la page n'utilise pas et que personne n'excuse | c'est le trou d'origine : du contenu servi, jamais lu |
| une route à la fois utilisée et excusée | une excuse périmée est un mensonge |
| une excuse portant sur une route disparue | excuser un monde qui n'existe plus |
| un appel de la page vers une route non servie | un 404 silencieux |
| une excuse de moins de soixante signes | un mot n'est pas une raison |
| une excuse qui ne nomme pas ce qui remplace la route | « inutile » n'apprend rien |
| une citation prise pour un usage | `<code>/api/scenarios</code>` dans une phrase d'aide ne fait rien, elle parle |

Les six routes excusées à ce jour : `bulles` (la page demande une bulle à la
fois), `instances` (vue courte de `dynamiques`, chargée en entier), `presets`
(portés par `/api/catalogue`), `scenarios` (embarqués dans la page à sa
construction), `export` (fabriqué dans le navigateur), `proxy` (appelée avec
l'adresse que le serveur donne). L'excuse du relais est **vérifiée là où elle se
fabrique** : `proxy_url` existe bien dans `simulateur/donnees_live.py`.

  > **Suite, 14 octobre 2026.** `comparer` était la septième, avec la raison
  > « les préréglages se rejouent un par un dans la grille des scénarios, ce qui
  > donne le même chiffre sans un second calcul complet ». Deux erreurs dans une
  > phrase : la grille des scénarios montre les **11 scénarios historiques**, pas
  > les **16 préréglages**, et la comparaison coûte **283 ms** pour
  > **9 795 octets compressés** — moins que les contre-pouvoirs affichés dans
  > cette même passe. La route a désormais son écran (`docs/RD_COMPARER_LES_SCENARIOS.md`),
  > et l'excuse a été retirée du contrôle : c'est le contrôle qui a demandé la
  > preuve, et la preuve qui a démenti la raison.

### Les contrôles de la section (`tests/test_contrepouvoirs_en_page.py`, 17 contrôles)

La section existe et a son ancre, le sommaire y mène, l'entête nomme les deux
routes, la page demande bien les deux registres, une réponse absente reste une
absence, **aucune majorité du droit positif n'est recopiée** dans le source,
**aucun nom de formation non plus**, la composition vient du serveur, le
chargement n'a pas lieu au démarrage, le bouton existe, l'observateur manquant
ne casse rien, chaque fiche échappe ce qu'elle affiche, aucun registre ne se
déverse en JSON, les pastilles de filtre sont des boutons pressables, la section
a son palier de 640 px, les teintes sont calculées, et la description du module
annonce la section.

### Le parcours dans le navigateur (`tests/navigateur_interface.mjs`, 13 étapes neuves)

Le harnais Node exécute la section pour de vrai, avec les réponses du vrai
serveur : il compte les fiches rendues (31 manœuvres, 6 familles, 2 chambres,
22 formations, 68 dépliants), vérifie que les jours affichés sont ceux du
serveur, compose une coalition (RN + EPR + SOC + LFI-NFP = 349 sièges), vérifie
que les phrases sur les seuils atteints suivent le calcul, filtre une famille,
et **injecte un registre hostile** (`<img src=x onerror=…>`, `<script>`,
`<svg onload=…>`) pour vérifier qu'aucune balise n'est interprétée.

### Les sabotages

Sept sabotages posés, sept attrapés : l'échappement retiré d'une fiche, un seuil
recopié dans la page, une excuse périmée, un appel retiré de la page, le
chargement remis au démarrage, une excuse sans raison, un filtre qui ne filtre
plus. Deux d'entre eux n'ont été reconnus qu'après correction du **motif
cherché** dans le rapport — le contrôle mordait, c'est la vérification du
sabotage qui était mal écrite. C'est noté ici parce que c'est exactement le
genre d'erreur que ce dépôt préfère écrire que cacher.

---

## 5. Limites assumées

- **Aucun navigateur réel dans l'environnement d'écriture** : le harnais exécute
  le JavaScript avec un DOM et un `fetch` simulés. La structure est vérifiée, le
  rendu visuel ne l'est pas. Les paliers de 640 px et le plancher de lisibilité
  sont contrôlés comme du texte, pas comme une image.
- **La section est dense.** Trente-et-une manœuvres et soixante-huit dépliants
  font un bloc long ; les dépliants sont fermés par défaut, et le filtre par
  famille est là pour cela. Une relecture humaine sur téléphone reste la seule
  mesure qui vaille.
- **La coalition ne dit pas ce qui passe.** Elle dit ce qu'une somme pèse face
  aux seuils de la chambre. Passer des seuils de la chambre aux chances d'un
  texte demanderait d'articuler chaque manœuvre à la composition réelle — c'est
  le travail du moteur, pas celui de la page, et la page le dit à l'écran.
- **Une route reste sans écran**, avec sa raison écrite : `/api/instances` (vue
  courte de `/api/dynamiques`, chargée en entier). Ce ne sont plus des trous
  silencieux : ce sont des choix, et le contrôle les tient. (`/api/comparer` a
  quitté cette liste le 14 octobre 2026 : elle est affichée, donc l'excuse a dû
  disparaître — une excuse périmée est un mensonge.)
- **La date du registre n'est pas une veille.** `date_etat_des_assemblees` est
  écrite dans le module ; la page l'affiche, elle ne la rafraîchit pas. Un
  remaniement ne se verrait pas tout seul — c'est le même angle mort que les
  snapshots de `donnees_live.py`, traité là-bas par un test de péremption.

---

## 6. Ce qui reste ouvert

1. **Le taux de couverture comme mesure permanente** : le contrôle compte
   aujourd'hui **16 routes mises en œuvre pour 6 excusées** (au 14 octobre 2026).
   Une passe future pourrait refuser une baisse sans décision écrite — mais un
   chiffre de couverture qui ne bouge jamais est un chiffre qu'on cesse de
   regarder.
2. ~~**`/api/comparer` en écran**~~ — **fait le 14 octobre 2026** : le tableau des
   16 préréglages est en ligne, avec son rangement par colonne et ses barres
   mesurées sur le plus fort montant servi (`docs/RD_COMPARER_LES_SCENARIOS.md`).
   La crainte de dupliquer la grille des scénarios était fondée sur une erreur de
   lecture : les deux ne montrent pas le même catalogue.
3. **Une relecture humaine** de la section sur téléphone et au lecteur d'écran :
   c'est la seule mesure que ce document ne peut pas fournir.
