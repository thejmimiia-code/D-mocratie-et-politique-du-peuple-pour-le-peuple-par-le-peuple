# Le site M.R.S.C reçoit le moteur à jour

Le site M.R.S.C (`thejmimiia-code/MRSC`, publié sur
[`thejmimiia-code.github.io/MRSC/`](https://thejmimiia-code.github.io/MRSC/))
n'appelle pas le simulateur : il **embarque une copie datée de son moteur**. Sa
copie venait du 8 octobre (`99491d8`) ; celle-ci vient du 13 octobre, indexation
comprise : la page du site se décrit enfin aux moteurs, aux aperçus de partage et
aux lecteurs automatiques.

Ce dossier est un **colis de transport** : une fois le site publié, il peut être
supprimé sans dommage — le correctif vit alors dans le dépôt du site, à
`outils/patchs/simulateur-securite-mrsc.patch`, à côté de la copie qu'il décrit.

## Pourquoi c'est un paquet et pas un simple `push`

Le moteur du site n'est pas le moteur de l'amont : le site ajoute par-dessus son
propre **correctif** de durcissement (plafonds de requête, plafonds de réponse,
en-têtes, échappement des textes, exclusion des cibles locales, enveloppes
défilantes des tableaux d'audit). Ce correctif est écrit comme un diff à
appliquer : il refusait de s'appliquer sur la nouvelle copie, et l'outil officiel
du site a donc eu raison de s'arrêter (`Le correctif local du site n'est plus
applicable… Aucun fichier du moteur local n'a été remplacé`).

Il a été **rebasé** sur le moteur du jour : réunion à trois branches
(`git merge-file` — moteur neuf, moteur d'origine du correctif, copie du site),
**sans conflit cette fois**, la base choisie étant celle du correctif et non une
copie antérieure du moteur. La règle suivie : l'amont gagne pour la typographie
et ses nouvelles fonctions, le site garde ses durcissements. La page
reconstruite porte **trois scripts JavaScript en ligne, tous valides**, plus un
bloc de données structurées — une fusion de HTML en conflit casse le JavaScript
sans le dire, et `py_compile` ne voit pas les marqueurs de conflit qui vivent
dans des chaînes Python.

## Ce que contient ce dossier

| Fichier | Rôle |
| --- | --- |
| `simulateur-securite-mrsc.patch` | Le correctif du site, rebasé sur le moteur du jour (1995 lignes, 5 fichiers, empreinte `58bc2a21…`). Sa cible
dans le site est `outils/patchs/simulateur-securite-mrsc.patch`. |
| `publier-mrsc.sh` | La publication, en une commande, dans un dossier jetable. |
| `corps-de-pr.md` | Le message du commit **et** la description de la demande de fusion. |

## Publier

```bash
bash livraison-mrsc/publier-mrsc.sh
```

Le script clone les deux dépôts dans `/tmp/mrsc-moteur`, copie **le sommet de
`main`** (c'est ce qui garde la veille du site au vert), rejoue la CI du site,
contrôle la copie, puis pousse une branche `maj-moteur-<révision>` et propose la
demande de fusion. Il ne touche jamais `main` et **ne publie rien si un contrôle
échoue**. Troisième argument possible : une révision précise, pour rejouer une
publication à l'identique.

Il faut un compte qui puisse écrire dans `thejmimiia-code/MRSC`. C'est le seul
point que cet atelier n'a pas : son jeton GitHub y est refusé
(`Permission to thejmimiia-code/MRSC.git denied`, puis
`Resource not accessible by integration` côté API). Le reste a été fait et
vérifié ici.

Une fois la demande de fusion acceptée, `deploy-pages.yml` publie le site tout
seul. La page affiche ensuite la révision copiée **d'elle-même** : elle lit
`simulateur/PROVENANCE.json` au chargement (attribut `data-simulateur-revision`
de `simulateur.html`), il n'y a donc aucun texte de version à réécrire à la main.

## Ce qui a été vérifié, et comment

Le script rejoue tout cela, et échoue si un point ne tient plus :

- **La CI du site, exactement** : `py_compile` des modules, des fonctions `api/`
  et des outils, `construire-apprentissages.py --verifier`,
  `construire-simulateur.py --verifier`, `verifier-rd-continue`,
  `verifier-site-statique`, `verifier-securite`, `verifier-integration`.
- **Les 16 protections du site** qui n'existent pas dans l'amont, nommées une par
  une : `413 Payload Too Large`, `414 URI Too Long`, `MAX_QUERY_FIELDS`,
  `MAX_REQUEST_BODY_BYTES`, `MAX_REQUEST_TARGET_BYTES`, `MAX_SOURCE_RESPONSE_BYTES`,
  `MAX_COTATION_RESPONSE_BYTES`, `MAX_BULLES_PAR_REQUETE`,
  `DUREE_CACHE_MARCHES_SECONDES`, `DUREE_CACHE_PROXY_SECONDES`,
  `DELAI_COLLECTE_NAVIGATEUR_MS`, `DELAI_SOURCE_NAVIGATEUR_MS`,
  `LECTURES_NAVIGATEUR`, `LIMITE_JSON_SOURCE_NAVIGATEUR`,
  `SIMULATEUR_LOG_ERREURS`, `nosniff`.
- **Aucun marqueur de conflit** dans la copie.
- **La page reconstruite** (`simulateur/index.html`, 371 160 caractères) relue
  **script par script** avec `node --check` ; ses données structurées sont
  décodées comme du JSON, et non comme du JavaScript (les confondre faisait
  échouer `node --check` sur du JSON parfaitement valide — vu en vrai à ce
  rebasage).
- **La veille** : `verifier-maj-amont` doit dire « à jour » — la copie est le
  sommet de `main`, donc le rendez-vous hebdomadaire du site ne sonne pas pour
  rien. `verifier-source-distante` interroge le réseau : injoignable depuis
  l'atelier, elle le dit et laisse la copie embarquée faire le calcul.

## Le correctif rebasé, en clair

`git apply --check` puis `git apply --reverse --check` sur un clone neuf de
l'amont : le correctif s'applique et se retire proprement, et les cinq fichiers
obtenus sont **identiques à l'octet** à la copie publiée ici.

La copie gagne en passant l'**en-tête public** du moteur (description, aperçu de
partage 1200 × 630, données structurées, icônes) : le site ne recopie plus ces
balises à la main. Seule l'adresse change, et le site la déclare lui-même —
`SIMULATEUR_URL_CANONIQUE=https://thejmimiia-code.github.io/MRSC/simulateur/`,
posée dans le bloc d'adaptation du correctif. C'est la porte
`verifier-site-statique.py` du site qui a révélé le besoin : elle refusait une
canonique venue d'ailleurs, à raison.
