# Réglages du dépôt (*Edit repository details*) — état au 5 octobre 2026

Ce document est la référence des champs non versionnés du dépôt : description,
site web, sujets (*topics*) et aperçu social. L'API GitHub refuse de les modifier
avec le jeton d'intégration utilisé par l'environnement d'automatisation
(`403 Resource not accessible by integration`) : les valeurs ci-dessous sont donc
à coller dans **Settings → General → Edit repository details**.

> **Note de reprise** : la tâche complète (commandes, valeurs à coller,
> empreintes de l'image, procédure en cas de refus de l'API) est décrite dans
> [`NOTE_POUR_CLAUDE.md`](../NOTE_POUR_CLAUDE.md), à l'attention de l'agent qui
> reprendra le dépôt avec des droits d'administration.

Deux scripts les tiennent à jour :

```bash
python3 outils/apercu_social.py     # régénère docs/apercu_social.png (1280 × 640)
python3 outils/details_depot.py     # affiche l'état actuel et le bloc à copier
python3 outils/details_depot.py --appliquer   # tente la mise à jour par l'API GitHub
```

---

## 1. Description (270 / 350 caractères)

```
Simulateur macro-politique systémique à 5 échelons (local → européen → mondial → géopolitique) : 93 leviers croisables, 20 domaines d'impact notés 0-100, données publiques en direct (Eurostat, BCE, Banque mondiale) et console de veille des seuils tolérables et hors-sol.
```

**Pourquoi ce changement.** La description annonçait « Modèle gigogne à
**4** échelons », alors que le moteur en compte **5** depuis l'ajout de la strate
géopolitique (`docs/08_STRATE_GEOPOLITIQUE_ET_SCENARIOS_DE_GUERRE.md`). Elle ne
mentionnait ni les leviers croisables, ni les domaines d'impact, ni les données
publiques en direct, ni la console de seuils — c'est-à-dire tout ce que le dépôt
sait faire aujourd'hui.

## 2. Site web

Le site déclaré (`https://d-mocratie-et-politique-du-peuple-p.vercel.app`)
renvoyait `404 DEPLOYMENT_NOT_FOUND` quand la branche `main` ne contenait ni
page d'accueil ni fonctions API. La branche de travail ajoute maintenant à la
racine la vraie interface interactive du simulateur et une fonction Python
par route du moteur. Après fusion dans `main` et redéploiement Vercel, vérifier
`/`, `/api/scenarios` et `POST /api/simuler` sur cette même adresse.

Les URL de prévisualisation `git-…vercel.app` peuvent rester protégées par les
réglages d'accès de Vercel. Pour rendre l'outil public, désactiver
**Deployment Protection → Vercel Authentication** et utiliser l'alias stable
de production. Tant que le déploiement de production n'est pas vérifié, les
options sûres restent :

| Option | Valeur à saisir |
|---|---|
| Vider le champ | *(vide)* |
| Renvoyer vers la documentation du simulateur | `https://github.com/thejmimiia-code/D-mocratie-et-politique-du-peuple/blob/main/docs/SIMULATEUR_PARAMETRABLE.md` |

Le simulateur se lance aussi localement : `python -m simulateur.dashboard --port 8080`
(voir § 5 du `README.md`).

## 3. Sujets (20 / 20)

```
france, simulation, politiques-publiques, finances-publiques, budget, dette-publique,
democratie, geopolitique, open-data, api-publiques, eurostat, banque-mondiale,
dashboard, python, modele-systemique, souverainete, politiques-budgetaires,
transparence, constitution, economie
```

Aucun sujet n'était défini : le dépôt n'apparaissait dans aucune recherche
thématique. Les vingt retenus couvrent ses quatre axes réels : le **modèle**
(simulation, modele-systemique, python, dashboard), le **champ** (politiques
publiques, finances publiques, budget, dette, économie), la **doctrine**
(démocratie, constitution, souveraineté, transparence, géopolitique) et les
**données** (open data, API publiques, Eurostat, Banque mondiale).

## 4. Aperçu social

Téléverser **`docs/apercu_social.png`** (1280 × 640, 52 Kio, très en
deçà de la limite d'1 Mo), régénérable par `python3 outils/apercu_social.py`.
L'image reprend la palette du simulateur, ses quatre chiffres clés (93 leviers ·
20 domaines · 38 indicateurs publics · 5 échelons) et le ruban de veille avec ses
pastilles de strate.

Empreintes du fichier livré, pour vérifier que c'est bien celui-ci qui a été
téléversé :

| Format | Valeur |
|---|---|
| SHA-256 (hexadécimal) | `fcfb89acd4db575d0389384afef397451667c44c1bf2f6a7d94808897d64fc37` |
| SHA-256 (base64) | `SHA256:/PuJrNTbV10DiThK/vOXRRZnxEwb8van2UgIiX1k/Dc=` |

Téléverser **`docs/apercu_social.png`** (1280 × 640, 52 Kio), régénérable par
`python3 outils/apercu_social.py`. L'image reprend la palette du simulateur, ses
quatre chiffres clés (93 leviers · 20 domaines · 38 indicateurs publics ·
5 échelons) et le ruban de veille avec ses pastilles de strate.

## 5. Autres cases de la même page

| Réglage | Recommandation |
|---|---|
| *Include in the home page* — Releases | **activé** : l'application se lance par `python -m simulateur.dashboard` |
| *Include in the home page* — Packages | désactivé : aucun paquet publié |
| *Include in the home page* — Deployments / Environments | désactivé : pas de déploiement continu |
| Wikis / Discussions | désactivés : la documentation vit dans `docs/` |

---

## 6. Trois façons d'appliquer ces réglages

### a. Page locale `outils/reglages_depot.html` (aucun secret partagé)

Ouvrez le fichier dans votre navigateur, collez-y un **jeton jetable** restreint
à ce dépôt (*fine-grained token*, permission **Administration : Read and write**,
expiration 7 jours, à révoquer ensuite), vérifiez les valeurs pré-remplies puis
cliquez sur *Appliquer au dépôt*. La page n'appelle que `api.github.com` :
le jeton ne quitte pas votre navigateur, il n'est ni enregistré ni transmis.

### b. Interface web, en une minute

1. Sur la page du dépôt, cliquez sur la roue dentée **⚙** à côté de « About »
   (ou *Settings → General → Edit repository details*).
2. **Description** : coller le texte du § 1 (270 caractères).
3. **Website** : vider le champ, ou coller l'adresse de la documentation (§ 2).
4. **Topics** : coller les vingt sujets du § 3.
5. *Save changes*, puis **Social preview → Edit → Upload an image** et choisir
   `docs/apercu_social.png` (§ 4) — l'aperçu social n'a pas d'API, c'est le seul
   champ qui reste nécessairement manuel.

### c. API GitHub, si un jeton administrateur est disponible

```bash
GH_TOKEN=<jeton administration> python3 outils/details_depot.py --appliquer
python3 outils/details_depot.py            # vérifie ensuite l'état du dépôt
```

L'aperçu social reste manuel même par cette voie.

---

## 7. Ce qui a été mis à jour dans le dépôt lui-même

Ces éléments sont, eux, versionnés et déjà à jour :

- `README.md` — titre et présentation en « 5 échelons », section 5 consacrée au
  simulateur paramétrable (93 leviers, 20 domaines, données publiques, console) ;
- `docs/README.md` — index enrichi de `SIMULATEUR_PARAMETRABLE.md` ;
- `docs/SIMULATEUR_PARAMETRABLE.md` — fonctionnement, seuils, limites assumées ;
- `pyproject.toml` — description, mots-clés et scripts d'entrée
  (`simulateur-mpol-dashboard`, `simulateur-mpol-simuler`).
