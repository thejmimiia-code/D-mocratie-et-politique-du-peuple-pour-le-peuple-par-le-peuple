# NOTE POUR CLAUDE — mettre à jour les réglages du dépôt

> **Destinataire :** Claude, au retour de tes crédits. Le travail technique est
> livré et testé ; il reste **une tâche de configuration GitHub**, bloquée par un
> manque de droits que la session précédente ne pouvait pas contourner.
> Compte 10 minutes, dont 8 pour retrouver les droits d'administration.

---

## 0. En une minute : ce qu'il y a à faire

```bash
# 1. Es-tu administrateur de ce dépôt ? (sans « admin: true », passe au § 4)
gh api repos/thejmimiia-code/D-mocratie-et-politique-du-peuple \
  --jq '.permissions'

# 2. Lecture de l'état actuel + bloc à copier
python3 outils/details_depot.py

# 3. Application par l'API (description, site web, 20 sujets)
python3 outils/details_depot.py --appliquer

# 4. Vérification
gh api repos/thejmimiia-code/D-mocratie-et-politique-du-peuple \
  --jq '{description, homepage, topics}'
```

Puis **une seule action manuelle**, impossible par API : téléverser
`docs/apercu_social.png` dans *Social preview* — à faire faire par l'utilisateur
(voir § 3, étape 5).

---

## 1. Objectif

Le bloc **« About »** du dépôt (bouton ⚙ à côté du titre, ou *Settings → General
→ Edit repository details*) décrit encore l'ancienne génération du projet. Il
faut le rendre fidèle à ce que le dépôt fait aujourd'hui.

| Champ | État au 5 octobre 2026 (constaté par API) | État cible |
|---|---|---|
| **Description** | « Plateforme de réflexion républicaine et Simulateur macro-politique systémique (**Modèle gigogne à 4 échelons**) » | la description du § 2 (270 caractères) |
| **Website** | `https://d-mocratie-et-politique-du-peuple-p.vercel.app` → **renvoie 404** (vérifié) | vide, ou la documentation (§ 2) |
| **Topics** | *aucun* | les 20 sujets du § 2 |
| **Social preview** | aucune image | `docs/apercu_social.png` (1280 × 640) |

Pourquoi c'est important : la description annonce **4 échelons** alors que le
moteur en compte **5** (la strate géopolitique a été ajoutée), et elle ne dit
rien des 101 leviers, des 20 domaines d'impact, des données publiques en direct
ni de la console de veille — c'est-à-dire de tout ce qui fait la valeur du
dépôt. Aucun sujet n'étant défini, le dépôt n'apparaît dans aucune recherche
thématique, et l'aperçu social est vide au partage d'un lien.

---

## 2. Les valeurs exactes (à coller telles quelles)

### Description — 270 / 350 caractères

```
Simulateur macro-politique systémique à 5 échelons (local → européen → mondial → géopolitique) : 101 leviers croisables, 20 domaines d'impact notés 0-100, données publiques en direct (Eurostat, BCE, Banque mondiale) et console de veille des seuils tolérables et hors-sol.
```

### Website

- *Recommandé* : **vider le champ** (l'instance Vercel n'existe plus) ;
- ou, à défaut d'application hébergée, renvoyer vers la documentation :
  `https://github.com/thejmimiia-code/D-mocratie-et-politique-du-peuple/blob/main/docs/SIMULATEUR_PARAMETRABLE.md`

### Topics — 20 / 20

```
france, simulation, politiques-publiques, finances-publiques, budget,
dette-publique, democratie, geopolitique, open-data, api-publiques, eurostat,
banque-mondiale, dashboard, python, modele-systemique, souverainete,
politiques-budgetaires, transparence, constitution, economie
```

Ces vingt sujets couvrent les quatre axes du dépôt : le **modèle** (simulation,
modele-systemique, python, dashboard), le **champ** (politiques-publiques,
finances-publiques, budget, dette-publique, economie), la **doctrine**
(democratie, constitution, souverainete, transparence, geopolitique) et les
**données** (open-data, api-publiques, eurostat, banque-mondiale).

### Social preview

Fichier à téléverser : **`docs/apercu_social.png`** — 1280 × 640, 52 Kio
(limite GitHub : 1 Mo). Régénérable par `python3 outils/apercu_social.py`
(dépendance : Pillow, hors du cœur du dépôt).

Empreintes du fichier livré, **à vérifier avant téléversement** :

| Format | Valeur |
|---|---|
| SHA-256 (hexadécimal) | ef13cf3ad353daccb90eb9f44e96311f54bc7225e7f4554f0309b6aa364beb5d |
| SHA-256 (base64) | `SHA256:7xPPOtNT2sy5Drn0TpYxH1S8ciXn9FVPAwm2qjZL610=` |

```bash
python3 -c "import hashlib;print(hashlib.sha256(open('docs/apercu_social.png','rb').read()).hexdigest())"
```

---

## 3. Marche à suivre pas à pas

1. **Vérifier les droits** — `gh api repos/…/… --jq '.permissions'` doit contenir
   `"admin": true`. La session précédente avait `admin: true` en lecture mais se
   faisait refuser l'écriture en `403 Resource not accessible by integration`
   (jeton d'intégration sans permission *Administration*).
2. **Prévisualiser** — `python3 outils/details_depot.py` affiche l'état actuel et
   le bloc exact à recopier si l'API reste fermée. Le script est idempotent : il
   indique « Déjà à jour, rien à faire » quand tout est appliqué.
3. **Appliquer** — `python3 outils/details_depot.py --appliquer`. Le script
   envoie un `PATCH /repos/…` avec la description, le site web (vide) et les
   vingt sujets (GitHub **remplace** la liste : c'est le jeu complet qui est
   envoyé, pas un ajout).
4. **Vérifier par relecture** — la commande de vérification du § 0 doit renvoyer
   la nouvelle description, `homepage: ""`, et les 20 sujets. En cas de doute sur
   la casse des sujets, GitHub les normalise en minuscules.
5. **Aperçu social (manuel, non contournable)** — il n'existe aucun point d'API
   pour cette image. Trois voies, par ordre de simplicité :
   - demander à l'utilisateur : *« Settings → General → Social preview → Edit →
     Upload an image → docs/apercu_social.png »* (et lui donner l'empreinte du
     § 2 s'il veut vérifier le fichier) ;
   - lui faire ouvrir `outils/reglages_depot.html`, qui applique description,
     site Web et sujets **depuis son navigateur** avec un jeton jetable ;
   - sinon, recopier à la main depuis `python3 outils/details_depot.py`.

---

## 4. Si l'API refuse toujours (403)

Lire le message exact. Trois causes possibles, par fréquence :

| Message | Cause | Solution |
|---|---|---|
| `Resource not accessible by integration` | le jeton est un jeton d'**intégration** (Arena) sans permission *Administration* | réautoriser la connexion GitHub d'Arena avec le dépôt **et** la permission *Administration : Read and write*, ou passer par la page locale du § 3.5 |
| `Bad credentials` | jeton révoqué ou expiré | reconnecter GitHub dans Arena |
| `Not Found` sur un dépôt existant | le jeton n'a pas accès à **ce** dépôt (jeton *fine-grained* limité à d'autres dépôts) | élargir l'accès du jeton à ce dépôt |

**Règle absolue : ne jamais demander de jeton, de mot de passe ou de code 2FA
dans la conversation.** Si des droits manquent, la sortie est : (a) faire
réautoriser la connexion dans Arena, ou (b) faire ouvrir
`outils/reglages_depot.html` à l'utilisateur — le jeton y reste dans son
navigateur et n'est envoyé qu'à `api.github.com`.

Un SHA-256 ne sert **pas** d'authentification : une empreinte identifie une
donnée, elle ne l'autorise pas. Si l'on t'en transmet une, elle sert à vérifier
un fichier (comme au § 2), jamais à se connecter.

---

## 5. Definition of done

- [ ] `gh api … --jq .description` renvoie exactement la description du § 2
- [ ] `gh api … --jq .homepage` renvoie `""` (ou l'URL de documentation choisie)
- [ ] `gh api … --jq '.topics | length'` renvoie `20`
- [ ] l'aperçu social est téléversé (`docs/apercu_social.png`, empreinte vérifiée)
- [ ] `python3 outils/details_depot.py` affiche « Déjà à jour, rien à faire »
- [ ] `python3 -m unittest discover -s tests -p "test_*.py"` reste vert (**399 tests**)
- [ ] `ruff check .` reste vert
- [ ] la section « Réglages du dépôt » de `docs/REPOSITORY_DETAILS.md` est à jour,
      et cette note peut être supprimée ou marquée comme faite

---

## 6. Contexte du dépôt au moment de la note (7 octobre 2026)

Le dépôt a changé de nature : le tableau de bord à quatre cartes figées est
remplacé par un **simulateur paramétrable**.

| Brique | Contenu |
|---|---|
| `simulateur/parametres.py` | 101 leviers en 14 familles, 14 préréglages doctrinaux, `normaliser()` |
| `simulateur/domaines.py` | 20 domaines, 74 indicateurs (formule + source), médiateurs annuels |
| `simulateur/moteur_parametrique.py` | références, convergence, scores 0-100, matrice d'impacts croisés, horizon 1-10 ans et ledger P21 |
| `simulateur/donnees_live.py` | 38 indicateurs publics (Eurostat, BCE, Frankfurter, Banque mondiale, Opendatasoft, Yahoo, Stooq) |
| `simulateur/seuils.py` | 31 garde-fous (26 absolus + 5 en écart) par strate : tolérable → vigilance → risqué → hors-sol ; `bareme_public()` pour l'audit |
| `simulateur/conseil.py` | conseiller temps réel (« effet papillon ») : chaque mouvement rejoué avant/après, directs + ricochets, garde-fous, compensations |
| `simulateur/interface.py` | page unique : ruban de veille, 101 leviers, 20 domaines, exports |
| `simulateur/dashboard.py` | API JSON : `/api/catalogue`, `/contexte`, `/simuler`, `/comparer`, `/conseil`, `/garde_fous`, `/presets`, `/proxy`, `/donnees` |
| `tests/` | **399 tests verts**, dont un harnais Node qui exécute réellement la page |

État Git au 7 octobre 2026 : branche `arena/43a71329-d-mocratie-et-politique-du-peu`,
**PR #16 ouverte** vers `main` ; l'évolution P16-P21 et l'horizon interactif sont
sur la même branche de travail.

---

## 7. Conventions et pièges du dépôt

- **Tests** : `python3 -m unittest discover -s tests -p "test_*.py"` — `pytest`
  n'est pas installé dans l'environnement d'automatisation.
- **Lint** : `ruff check .` doit passer (règles `E, F, W, I, B, UP, C4`).
- **Zéro dépendance externe** dans le simulateur (bibliothèque standard
  uniquement). Seule exception assumée : `outils/apercu_social.py` a besoin de
  Pillow, et ne sert qu'à la vignette.
- **Le JavaScript de la page est testé pour de vrai** : `tests/verificateur_js.py`
  (équilibre des délimiteurs) et `tests/navigateur_interface.mjs`, exécuté par
  `tests/test_interface_navigateur.py` (saute proprement si Node est absent).
  Toute modification de `interface.py` doit garder ces deux garde-fous verts.
- **Fichiers en CRLF** : `README.md` et d'autres fichiers du dépôt utilisent des
  fins de ligne Windows. Un `sed`/`replace` de motif sans `\r` échoue
  silencieusement : préférer un script Python avec assertion d'unicité du motif.
- **Ne jamais travailler sur `main`** : l'automatisation pousse sur la branche
  `arena/*` de la session et ouvre une PR.
- **Modèle, pas prophétie** : les scores comparent une politique à la
  trajectoire de référence du modèle (50 = aucune politique), jamais à un idéal
  absolu — l'interface et la documentation le rappellent, garder ce cadrage.

---

## 8. Chantiers ouverts, hors périmètre de cette note

À traiter seulement si l'utilisateur le demande (vérifiés dans le code au moment
de la rédaction) :

1. **`simulateur/donnees_live.py` l. 333** — l'URL Banque mondiale fige
   `date=2024` : les séries ne se mettront pas à jour toutes seules. À rendre
   paramétrable par `INDICATEURS[...]`.
2. **Sensibilité de `effort_structurel_mde`** — la ligne existe
   (`domaines.py` l. 189, alimentée par `moteur_parametrique.py` l. 195 : cumul
   du solde des mesures, plancher 0). Vérifier qu'une politique nouvelle la fait
   bien bouger avant de s'appuyer dessus pour le spread.
3. **Proxy et CORS** — `/api/proxy` (Yahoo, Stooq, sources sans en-tête CORS) n'a
   été vérifié qu'en `curl` : un essai dans un vrai navigateur reste à faire
   lorsque le simulateur est servi publiquement.
4. **Environnement sans réseau** : la collecte live ne peut pas être testée
   depuis l'automatisation (seuls github.com et pypi.org sont joignables). C'est
   le navigateur de l'utilisateur qui interroge les API puis poste sur
   `/api/donnees` — c'est le comportement attendu, pas un bug.

---

*Note rédigée le 5 octobre 2026 par la session Arena `01a10c67`. Si tu termines
la tâche, coche la § 5, mets `docs/REPOSITORY_DETAILS.md` à jour et supprime ce
fichier (ou remplace-le par « fait le … »).*
