# Réglages du dépôt (*Edit repository details*) — état au 13 octobre 2026

Ce document est la référence des champs non versionnés du dépôt : description,
site web, sujets (*topics*) et aperçu social. L'API GitHub refuse de les modifier
avec le jeton d'intégration utilisé par l'environnement d'automatisation
(`403 Resource not accessible by integration`) : les valeurs ci-dessous sont donc
à coller dans **Settings → General → Edit repository details**.

> **Note de reprise** : la tâche complète (commandes, valeurs à coller,
> empreintes de l'image, procédure en cas de refus de l'API) est décrite dans
> [`NOTE_POUR_CLAUDE.md`](../NOTE_POUR_CLAUDE.md), à l'attention de l'agent qui
> reprendra le dépôt avec des droits d'administration.

## 0. État constaté (13 octobre 2026, par l'API GitHub)

| Champ | État | Qui peut le poser |
|---|---|---|
| **Description** | ✅ appliquée — 5 échelons, 156 leviers, données publiques en direct | fait |
| **Website** | ✅ appliqué — l'application répond (Vercel) | fait |
| **Topics** | ❌ **vide** — c'est le champ où il faut **taper chaque mot puis valider**, un par un | à la main, ou jeton d'administration |
| **Social preview** | ❓ non exposée par l'API | **à la main, obligatoirement** |

Le jeton dont dispose l'espace de travail est un jeton d'intégration sans droit
d'administration : `python3 outils/details_depot.py --appliquer` se fait refuser
(`403 Resource not accessible by integration`) et affiche le bloc à coller.
Depuis le 13 octobre 2026, ce bloc **dit ce qui a été constaté** au lieu
d'affirmer : l'outil interroge l'adresse publiée à chaque exécution, et écrit
« l'adresse n'a pas pu être vérifiée » quand le réseau manque — jamais « elle est
morte ». Voir [`RD_PREUVE_ET_OUTILLAGE.md`](RD_PREUVE_ET_OUTILLAGE.md), § 3.

---

Les quatre régions marquées `<!-- engendre:… -->` sont **écrites par
`outils/details_depot.py`** : elles recopient la description, les sujets,
l'adresse publiée et l'empreinte de l'aperçu social depuis leurs sources. Le
reste du document est de la prose, éditable à la main.

```bash
python3 outils/details_depot.py --doc           # réécrit les régions engendrées
python3 outils/details_depot.py --verifier-doc  # refuse une valeur périmée
```

Deux scripts les tiennent à jour :

```bash
python3 outils/apercu_social.py     # régénère docs/apercu_social.png (1280 × 640)
python3 outils/details_depot.py     # affiche l'état actuel et le bloc à copier
python3 outils/details_depot.py --appliquer   # tente la mise à jour par l'API GitHub
```

---

<!-- engendre:description -->
## 1. Description (271 / 350 caractères)

```
Simulateur macro-politique systémique à 5 échelons (local → européen → mondial → géopolitique) : 156 leviers croisables, 20 domaines d'impact notés 0-100, données publiques en direct (Eurostat, BCE, Banque mondiale) et console de veille des seuils tolérables et hors-sol.
```
<!-- /engendre:description -->

**Pourquoi ce changement.** La description annonçait « Modèle gigogne à
**4** échelons », alors que le moteur en compte **5** depuis l'ajout de la strate
géopolitique (`docs/08_STRATE_GEOPOLITIQUE_ET_SCENARIOS_DE_GUERRE.md`). Elle ne
mentionnait ni les leviers croisables, ni les domaines d'impact, ni les données
publiques en direct, ni la console de seuils — c'est-à-dire tout ce que le dépôt
sait faire aujourd'hui.

## 2. Site web

<!-- engendre:site-web -->
L'application est publiée à **https://d-mocratie-et-politique-du-peuple-p.vercel.app** — c'est elle, le site du dépôt.
La même page, servie par le même moteur, répond aussi sur la **copie de secours**
https://simulateur-macro-politique.onrender.com (Render, qui s'endort puis se réveille).

Ce que les robots lisent : `https://d-mocratie-et-politique-du-peuple-p.vercel.app/robots.txt`, `/sitemap.xml`, `/llms.txt`,
`/llms-full.txt` — tous engendrés par `simulateur/surface_publique.py`.
Vérification depuis n'importe quelle machine connectée :
`python3 outils/verifier-surface-en-ligne.py`.
<!-- /engendre:site-web -->

**Pourquoi ce changement.** Le champ avait été vidé, et ce document conseillait
de le laisser vide : l'adresse alors déclarée renvoyait
`404 DEPLOYMENT_NOT_FOUND`, `main` ne contenant ni page d'accueil ni fonctions
API. Depuis, `main` sert la vraie interface interactive à la racine et une
fonction Python par route du moteur : **il n'y a plus de raison de se passer
d'une application qui répond**. Le script pose d'ailleurs la question à chaque
exécution (`adresse_repond`) et, si le réseau manque, écrit « l'adresse n'a pas
pu être vérifiée » — jamais « elle est morte ». Une phrase figée ne redevient
jamais vraie toute seule ; une question posée, si.

Les URL de prévisualisation `git-…vercel.app` peuvent rester protégées par les
réglages d'accès de Vercel : c'est **l'alias stable de production** qu'il faut
déclarer, celui de la région engendrée ci-dessus.

Le simulateur se lance aussi localement : `python -m simulateur.dashboard --port 8080`
(voir § 5 du `README.md`).

<!-- engendre:sujets -->
## 3. Sujets (20 / 20)

```
france, simulation, politiques-publiques, finances-publiques, budget, dette-publique, democratie, geopolitique, open-data, api-publiques, eurostat, banque-mondiale, dashboard, python, modele-systemique, souverainete, politiques-budgetaires, transparence, constitution, economie
```
<!-- /engendre:sujets -->

Aucun sujet n'était défini : le dépôt n'apparaissait dans aucune recherche
thématique. Les vingt retenus couvrent ses quatre axes réels : le **modèle**
(simulation, modele-systemique, python, dashboard), le **champ** (politiques
publiques, finances publiques, budget, dette, économie), la **doctrine**
(démocratie, constitution, souveraineté, transparence, géopolitique) et les
**données** (open data, API publiques, Eurostat, Banque mondiale).

## 4. Aperçu social

<!-- engendre:apercu -->
Téléverser **`docs/apercu_social.png`** (1280 × 640, 51 Kio — 52171 octets),
régénérable par `python3 outils/apercu_social.py`. L'image reprend la palette du
simulateur, ses chiffres clés — 156 leviers · 20 domaines · 52 indicateurs publics · 5 échelons —
et le ruban de veille avec ses pastilles de strate.

Empreintes du fichier versionné, pour vérifier que c'est bien celui-ci qui a été
téléversé dans *Social preview* :

| Format | Valeur |
|---|---|
| Octets | `52171` |
| SHA-256 (hexadécimal) | `2ecba5b1b72d6ab6372eb3f1ada9c6e4bd9b4ef3cfef824257eaf6f9aa714ebd` |
| SHA-256 (base64) | `SHA256:LsulsbctarY3LrPxranG5L2bTvPP74JCV+r2+apxTr0=` |
<!-- /engendre:apercu -->

## 4 bis. Ce que le dépôt annonce de lui-même (et qui n'est pas un réglage GitHub)

À côté de l'encadré « About », trois surfaces publiques décrivent le projet — et
elles sont, elles, **versionnées** :

- `/robots.txt`, `/llms.txt`, `/llms-full.txt` : règles de visite, résumé et
  contenu en texte pour les robots et les lecteurs automatiques. Ils annoncent la
  **licence du dépôt**, et ce nom n'y est pas recopié : il est **lu** dans le
  fichier `LICENSE` (`simulateur/surface_publique.py`). Cette correction vient
  d'une erreur réelle — ces fichiers annonçaient une autre licence que celle du
  dépôt (voir [`RD_PREUVE_ET_OUTILLAGE.md`](RD_PREUVE_ET_OUTILLAGE.md), § 6) ;
- les **données structurées** de la page (`WebApplication`) portent
  `license: …/blob/main/LICENSE` : l'adresse du fichier, jamais un nom qui
  pourrait vieillir ;
- `tests/test_licence_du_depot.py` refuse toute ligne du dépôt qui attribuerait
  au projet une autre licence que celle de son fichier.

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
2. **Description** : coller le texte du § 1 — déjà appliquée au 13 octobre 2026,
   à recoller seulement si elle a bougé.
3. **Website** : coller l'adresse de l'application (§ 2) — déjà appliqué.
4. **Topics** : taper les vingt sujets du § 3 **un par un** — chaque mot devient
   une pastille bleue quand on valide par Entrée. Coller la liste entière d'un
   coup laisse le champ vide : c'est le piège de ce champ, et la raison la plus
   probable pour laquelle il est encore vide.
5. *Save changes*, puis **Social preview → Edit → Upload an image** et choisir
   `docs/apercu_social.png` (§ 4) — l'aperçu social n'a pas d'API : c'est le seul
   champ qui **reste** nécessairement manuel, même avec tous les droits. Vérifier
   ensuite que le champ « Topics » a bien gardé ses pastilles (un enregistrement
   sans effet ne se voit qu'en rechargeant la page).

### c. API GitHub, si un jeton administrateur est disponible

```bash
GH_TOKEN=<jeton administration> python3 outils/details_depot.py --appliquer
python3 outils/details_depot.py            # vérifie ensuite l'état du dépôt
```

L'aperçu social reste manuel même par cette voie — GitHub ne l'expose par aucune
API. Contrôle de l'effet : `python3 outils/details_depot.py` relit l'état et
compare le champ *Website* à l'adresse que la page déclare aux moteurs.

---

## 7. Ce qui a été mis à jour dans le dépôt lui-même

Ces éléments sont, eux, versionnés et déjà à jour :

- `README.md` — titre et présentation en « 5 échelons », section 5 consacrée au
  simulateur paramétrable (156 leviers, 20 domaines, données publiques, console) ;
- `docs/README.md` — index enrichi de `SIMULATEUR_PARAMETRABLE.md` ;
- `docs/SIMULATEUR_PARAMETRABLE.md` — fonctionnement, seuils, limites assumées ;
- `pyproject.toml` — description, mots-clés et scripts d'entrée
  (`simulateur-mpol-dashboard`, `simulateur-mpol-simuler`).
