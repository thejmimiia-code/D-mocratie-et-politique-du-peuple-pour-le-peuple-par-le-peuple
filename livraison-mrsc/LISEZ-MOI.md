# Le site M.R.S.C reçoit le moteur à jour

Le site M.R.S.C (`thejmimiia-code/MRSC`, publié sur
[`thejmimiia-code.github.io/MRSC/`](https://thejmimiia-code.github.io/MRSC/))
n'appelle pas le simulateur : il **embarque une copie datée de son moteur**. Sa
copie venait du 8 octobre (`99491d8`). Celle-ci vient du 13 octobre (`22957da`).

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

Il a été **rebasé** sur `22957da` : réunion à trois branches, puis dix conflits
résolus un par un dans `interface.py`. La règle suivie : l'amont gagne pour la
typographie et ses nouvelles fonctions, le site garde ses durcissements.

## Ce que contient ce dossier

| Fichier | Rôle |
| --- | --- |
| `simulateur-securite-mrsc.patch` | Le correctif du site, rebasé sur `22957da` (1972 lignes, 5 fichiers). Sa cible dans le site est `outils/patchs/simulateur-securite-mrsc.patch`. |
| `publier-mrsc.sh` | La publication, en une commande, dans un dossier jetable. |
| `corps-de-pr.md` | Le message du commit **et** la description de la demande de fusion. |

## Publier

```bash
bash livraison-mrsc/publier-mrsc.sh
```

Le script clone les deux dépôts dans `/tmp/mrsc-moteur`, force la révision amont
à `22957da`, copie le correctif, lance `outils/mettre-a-jour-simulateur.py`,
reconstruit la page et les fonctions `api/`, contrôle la copie, passe les portes,
puis pousse une branche `maj-simulateur-22957da` et propose la demande de fusion.
Il ne touche jamais `main` et **ne publie rien si un contrôle échoue**.

Il faut un compte qui puisse écrire dans `thejmimiia-code/MRSC`. C'est le seul
point que cet atelier n'a pas : son jeton GitHub y est refusé
(`Permission to thejmimiia-code/MRSC.git denied`, puis
`Resource not accessible by integration` côté API). Le reste a été fait et
vérifié ici.

Une fois la demande de fusion acceptée, `deploy-pages.yml` publie le site tout
seul — la page `simulateur.html` sert alors le moteur `22957da`.

## Ce qui a été vérifié, et comment

Les contrôles du script rejouent ceux qui ont été passés à la main :

- **Les 16 protections du site** qui n'existent pas dans l'amont sont nommées une
  par une (`413 Payload Too Large`, `414 URI Too Long`, `MAX_QUERY_FIELDS`,
  `MAX_REQUEST_BODY_BYTES`, `MAX_REQUEST_TARGET_BYTES`, `MAX_SOURCE_RESPONSE_BYTES`,
  `MAX_COTATION_RESPONSE_BYTES`, `MAX_BULLES_PAR_REQUETE`,
  `DUREE_CACHE_MARCHES_SECONDES`, `DUREE_CACHE_PROXY_SECONDES`,
  `DELAI_COLLECTE_NAVIGATEUR_MS`, `DELAI_SOURCE_NAVIGATEUR_MS`,
  `LECTURES_NAVIGATEUR`, `LIMITE_JSON_SOURCE_NAVIGATEUR`,
  `SIMULATEUR_LOG_ERREURS`, `nosniff`) : le script échoue si l'une disparaît.
- **Aucun marqueur de conflit** dans la copie — `py_compile` ne les voit pas,
  ils vivent dans des chaînes Python.
- **La page reconstruite** (`simulateur/index.html`, 366 250 caractères) est
  relue **script par script** avec `node --check` : c'est là qu'une fusion de
  HTML en conflit se casse en silence. Trois scripts en ligne, tous valides.
- **Les portes du site** : `verifier-securite`, `verifier-maj-amont`,
  `verifier-integration`, `verifier-site-statique`, `verifier-rd-continue`,
  `construire-apprentissages`. `verifier-source-distante` interroge le réseau :
  depuis l'atelier il est injoignable, elle le dit et laisse la copie embarquée
  faire le calcul.

## Le correctif rebasé, en clair

`git apply --check` puis `git apply --reverse --check` sur un clone neuf de
l'amont : le correctif s'applique et se retire proprement, et les cinq fichiers
obtenus sont **identiques à l'octet** à la copie publiée ici. Un prochain
`mettre-a-jour-simulateur.py` saura donc constater ce qui est déjà intégré.
