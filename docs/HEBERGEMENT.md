# Mettre le simulateur en ligne

Le dépôt contient tout le code, mais un dépôt n'est pas un site : rien ne
l'exécute. Ce document explique comment obtenir **une adresse publique** à
partir de ce dépôt, ce qui a été ajouté pour le permettre, et ce qu'il faut
savoir avant de la partager.

Trois voies, du plus court au plus autonome :

| Voie | Temps | Compte requis | Difficulté |
|---|---|---|---|
| [Render, bouton « Deploy »](#1-le-plus-court-render-en-deux-clics) | ~3 min | Render (gratuit) | aucune |
| [Image Docker (GHCR)](#2-limage-docker-une-commande-sur-nimporte-quelle-machine) | ~2 min | Aucun (image publique) | Docker |
| [N'importe quel hébergeur Python](#3-nimporte-quel-hébergeur-python) | ~10 min | Selon l'hébergeur | une ligne de commande |

---

## Pourquoi pas GitHub Pages ?

GitHub Pages ne sert que des **fichiers statiques** : du HTML, du CSS, du
JavaScript. Le simulateur, lui, **calcule** : 156 leviers croisés, moteur
gigogne à cinq échelons, contexte économique « à l'instant T ». Ce calcul se
fait en Python, côté serveur. Une page statique ne peut pas l'exécuter.

Il faut donc un hébergeur qui lance un processus Python — ce que font toutes
les plateformes ci-dessous, gratuitement pour un usage personnel ou associatif.

---

## 1. Le plus court : Render, en deux clics

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2Fthejmimiia-code%2FD-mocratie-et-politique-du-peuple-pour-le-peuple-par-le-peuple)

Le bouton ouvre Render, qui lit le fichier [`render.yaml`](../render.yaml) à la
racine du dépôt et pré-remplit tout : build, commande de démarrage, sonde de
disponibilité, version de Python. Il ne reste qu'à valider.

**Ce qu'il faut savoir**

- Render déploie la branche **par défaut** (`main`) : le bouton ne fonctionne
  qu'une fois les modifications fusionnées. Depuis une branche, déployez
  manuellement et choisissez cette branche à l'écran.
- Par le **tableau de bord Blueprints** plutôt que par le bouton, laissez
  **Blueprint Path** vide — le fichier est à la racine du dépôt — et **Branch**
  sur `main`. Si `render.yaml` vient d'être fusionné, la page peut afficher
  « Blueprint file `render.yaml` not found on main branch » : elle garde en
  cache l'arbre du dépôt, le bouton **Retry** suffit alors à la rafraîchir.
- L'offre gratuite **endort le service** après quelques minutes sans visite : la
  première ouverture suivante prend une trentaine de secondes, les suivantes
  sont immédiates. C'est le comportement normal du palier gratuit, pas un bug —
  et c'est ce sommeil qui, quand le réveil échoue, montre au visiteur la page
  **502** de l'hébergeur. Le dépôt visite donc la copie de secours toutes les
  dix minutes pendant les heures de consultation : voir « Le garde-veille ».
- Région `frankfurt` (la plus proche de la France), modifiable dans
  `render.yaml` avant le déploiement.
- L'adresse fournie est en HTTPS, géré par la plateforme : aucun certificat à
  installer.

---

## 2. L'image Docker : une commande sur n'importe quelle machine

Une image est publiée automatiquement par
[`.github/workflows/image-docker.yml`](../.github/workflows/image-docker.yml)
dans le registre GitHub (GHCR), à chaque poussée sur `main`. Elle est publique :

```bash
docker run -p 8080:8080 \
  ghcr.io/thejmimiia-code/d-mocratie-et-politique-du-peuple-pour-le-peuple-par-le-peuple:latest
```

Puis ouvrir <http://localhost:8080>. Sur un serveur, placer un reverse proxy
(Nginx, Caddy, Traefik) devant pour le HTTPS ; Caddy le fait seul :

```bash
caddy reverse-proxy --from simulateur.example.org --to localhost:8080
```

Construire l'image soi-même, sans attendre la publication :

```bash
docker build -t simulateur-macro-politique .
docker run -p 8080:8080 simulateur-macro-politique
```

L'image tourne **sans privilège root** et n'a besoin ni de base de données, ni
de volume, ni de secret.

---

## 3. N'importe quel hébergeur Python

Railway, Fly.io, Scalingo, Clever Cloud, Heroku, Koyeb, Render (sans le
bouton), un VPS avec systemd : tous lisent l'un des deux fichiers ci-dessous.

**`Procfile`** — reconnu automatiquement par Heroku, Scalingo, Clever Cloud,
Railway, Dokku :

```
web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 simulateur.wsgi:application
```

**Commande équivalente**, à copier telle quelle ailleurs :

```bash
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 simulateur.wsgi:application
```

Le port vient toujours de la variable d'environnement `PORT` fournie par
l'hébergeur ; ne jamais l'écrire en dur. En local, `--port` reste disponible :

```bash
python3 -m simulateur.dashboard --host 0.0.0.0 --port 8080
```

### Ce que contient le dépôt pour l'hébergement

| Fichier | Rôle |
|---|---|
| `simulateur/wsgi.py` | **Le pont.** Présente chaque requête WSGI au handler HTTP existant. C'est le seul point d'entrée utilisé en ligne. |
| `api/[...path].py` | Fonction Vercel unique : sert toutes les routes du moteur (section 4). |
| `robots.txt`, `sitemap.xml`, `llms.txt`, `llms-full.txt` | Ce que lisent les robots. Fichiers écrits à la racine (Vercel les sert tels quels) **et** routes du serveur Python (Render n'a que le routeur pour les servir). Les deux textes viennent de `simulateur/surface_publique.py` : voir [`RD_INDEXATION.md`](RD_INDEXATION.md). |
| `og-image.png`, `favicon.ico`, `favicon.svg`, `apple-touch-icon.png` | Images publiques, engendrées par `outils/apercu_social.py`. Vercel les sert comme fichiers ; le serveur Python les sert par une liste blanche (`surface_publique.IMAGES`) — les icônes de l'onglet voyagent en `data:` dans la page, et `favicon.ico` reste servi à la racine pour ce qui le demande sans lire la page. |
| `Procfile` | Commande de démarrage pour les plateformes qui le détectent. |
| `requirements.txt` | `gunicorn`, et rien d'autre — dépendance **d'hébergement**, pas d'exécution. |
| `runtime.txt` | Version de Python (`3.11.9`). Render et Heroku le lisent. |
| `render.yaml` | Recette du déploiement Render utilisée par le bouton. |
| `Dockerfile` | Image de production, non-root, avec sonde de santé. |
| `.github/workflows/image-docker.yml` | Publie l'image dans GHCR. |
| `.github/workflows/veille-en-ligne.yml` | Vérifie ce que les deux hébergeurs servent vraiment, et publie son verdict. |
| `.github/workflows/garde-veille.yml` | Empêche la copie de secours de s'endormir : une visite toutes les dix minutes. |
| `outils/garde-veille.py` | La visite elle-même, et le calcul de ce que la fenêtre coûte. |

### Pourquoi un pont WSGI plutôt qu'un second serveur

`python3 -m simulateur.dashboard` lance son propre serveur de développement.
Les hébergeurs, eux, imposent le leur (gunicorn, uWSGI, waitress) et attendent
une application WSGI. Réécrire un routeur pour eux aurait créé **deux versions
de la même application**, condamnées à diverger — la panne la plus pénible qui
soit : ça marche en local, ça casse en ligne, et rien ne le signale.

`simulateur/wsgi.py` évite cela en **branchant le handler existant** sur une
requête WSGI. Un seul routeur, une seule vérité. Techniquement : la requête est
reconstituée en texte HTTP depuis l'`environ` WSGI, le handler lit et écrit dans
des flux mémoire au lieu d'une socket, et les en-têtes qu'il croyait envoyer sur
le réseau sont interceptés avant d'atteindre le corps. Rien de plus.

Conséquence pratique : ce que vous vérifiez en local est exactement ce qui
tourne en ligne. [`tests/test_wsgi.py`](../tests/test_wsgi.py) le garantit — 21
tests, dont un qui sert réellement l'application par HTTP.

---

## 4. Vercel : une fonction pour toutes les routes

Le même dépôt se déploie sur Vercel sans fichier de configuration. Réglages à appliquer
dans le projet :

- **Framework Preset : Other**, **Build Command : vide**, **Output Directory : `.`**,
  **Install Command : vide**.
- Aucun `vercel.json` et aucune règle de réécriture globale.
- `api/` ne contient que deux fonctions. `api/[...path].py` sert toutes les routes
  `/api/*` du moteur, via `simulateur/pont_api.py`. Vercel envoie `/api/<route>` vers
  `api/[...path].py?...path=<route>` ; le pont rétablit alors le chemin demandé.
  `api/verifier-source.py` est une fonction distincte, propre au site.

Ce découpage est imposé par Vercel : chaque fichier `.py` de `api/` devient une
fonction, et l'offre Hobby refuse un déploiement qui en compte plus de 12. Une
fonction par route (dix-sept fichiers) serait donc refusée.

Le système de fichiers des fonctions est en lecture seule, à l'exception de `/tmp`.
Le cache des données publiques y est placé, et les exports sont construits en mémoire.

Pour un accès public, désactiver **Security → Deployment Protection → Vercel
Authentication**. Tant que cette protection est active, l'adresse de prévisualisation
affiche une page de connexion au lieu du simulateur.

Contrôle local, sans Vercel :

```bash
python3 outils/generer-fonctions-api.py --verifier
python3 outils/generer-index-simulateur.py --verifier
```

Après un déploiement, vérifier sur l'adresse publique :

1. le déploiement est au statut « Ready » et le journal de build ne signale aucun
   plafond de fonctions ;
2. `/api/scenarios` répond en JSON et contient `mandature` ;
3. `/api/export?scenario=mandature&format=csv` télécharge un fichier CSV ;
4. `/api/inconnue` répond 404.

Une page HTML à la place du JSON signifie que la requête n'atteint pas la fonction :
protection de déploiement encore active, ou routage à revoir.

---

## Vérifier avant de publier

Sans rien installer (le module `wsgiref` fait partie de Python) :

```bash
python3 -c "from wsgiref.simple_server import make_server; \
from simulateur.wsgi import application; \
make_server('0.0.0.0', 8080, application).serve_forever()"
```

Avec gunicorn — **exactement** la commande de production :

```bash
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:8080 --workers 2 --threads 4 simulateur.wsgi:application
```

Puis, dans un autre terminal :

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8080/            # 200
curl -s http://localhost:8080/api/lexique | head -c 120                    # du JSON
curl -s -H 'Accept-Encoding: gzip' --compressed -o /dev/null \
     -w '%{size_download} octets reçus\n' http://localhost:8080/api/contexte
```

`/api/lexique` sert de **sonde de disponibilité** : c'est une route JSON qui ne
calcule rien, idéale pour le `healthCheckPath` d'un hébergeur.

---

## Quand la copie de secours ne répond pas (502)

Deux adresses servent ce dépôt, et **elles ne tombent pas ensemble** :

| Adresse | Qui la sert | Rôle |
|---|---|---|
| <https://d-mocratie-et-politique-du-peuple-p.vercel.app/> | Vercel | **l'adresse canonique** : celle qu'on partage, celle que les moteurs indexent (elle est dans `rel="canonical"`, dans le sitemap et dans `robots.txt`) |
| <https://simulateur-macro-politique.onrender.com/> | Render | la **copie de secours** : elle exécute le serveur Python, et sert la même page quand Vercel ne peut pas |

Un **502** (« Bad Gateway ») sur la copie de secours veut dire une chose précise :
la passerelle de Render répond, mais **personne ne répond derrière elle**. Ce n'est
pas un défaut du code — l'application démarre en une seconde et sert toutes ses
routes (`gunicorn … simulateur.wsgi:application`, vérifié). C'est le service
lui-même qui n'est plus là :

- **elle dort** — comportement normal de l'offre gratuite après une quinzaine de
  minutes sans visite ; un appel la réveille en trente secondes environ ;
- **elle est suspendue** — Render suspend un service gratuit qui dépense son
  quota mensuel d'heures, ou quand une facturation n'aboutit pas ;
- **le dernier démarrage a échoué** — la cause est alors dans *Logs*.

### Réparer, dans l'ordre

1. **Réveiller** : ouvrir l'adresse et attendre une minute. Si la page arrive,
   c'était le sommeil — rien à faire de plus.
2. **Redéployer** : [tableau de bord Render](https://dashboard.render.com) → le
   service `simulateur-macro-politique` → **Manual Deploy** → **Deploy latest
   commit**. C'est ce qui répare un démarrage en échec ou un service qui ne
   répond plus. Si le service apparaît **Suspended**, le bouton **Resume** (ou
   **Unsuspend**) vient d'abord.
3. **Lire la cause** : la même page, onglet **Logs**. Un 502 après un
   redéploiement qui échoue dit pourquoi (quota, mémoire, erreur Python).
4. **Redéployer sans tableau de bord** — pour ne plus dépendre de quelqu'un
   devant l'écran : créer un **Deploy Hook** dans Render → service →
   *Settings → Deploy Hook* → **Create Deploy Hook**, puis coller l'adresse
   dans le dépôt : GitHub → *Settings → Secrets and variables → Actions* →
   **New repository secret**, nom **`RENDER_DEPLOY_HOOK`**. À partir de là,
   chaque fusion sur `main` redéploie la copie de secours, et
   [`.github/workflows/deploy-secours.yml`](../.github/workflows/deploy-secours.yml)
   peut la redéployer à la demande (onglet **Actions** → *Réveiller la copie de
   secours* → **Run workflow**). Sans ce secret, l'étape se contente de le dire :
   ce n'est pas un échec.
5. **Héberger ailleurs** — la copie de secours n'est qu'un confort : la section 2
   (image Docker) et la section 3 (n'importe quel hébergeur Python) donnent la
   même application, et `Procfile` est déjà écrit.

### Comment le savoir avant qu'un visiteur le signale

[`.github/workflows/veille-en-ligne.yml`](../.github/workflows/veille-en-ligne.yml)
interroge **les deux** adresses — page, textes pour robots, images, vingt-deux
routes — une fois par semaine, à chaque changement de la veille, et à la
demande. Son verdict est publié dans un commentaire tenu à jour sur la page
**« Veille en ligne »** du dépôt, lisible sans rien installer.

**Deux poids, deux mesures** : l'adresse canonique est celle qu'on partage, donc
son échec fait rougir la veille ; la copie de secours peut être endormie,
suspendue ou absente sans que le dépôt soit en faute — son échec est **publié**,
pas sanctionné. Une veille rouge toutes les semaines pour un service d'appoint
cesse d'être lue, et une veille qu'on ne lit plus ne sert à rien.

### Le garde-veille : empêcher le service de s'endormir

Constater la panne ne suffit pas : mieux vaut qu'elle n'arrive pas.
[`.github/workflows/garde-veille.yml`](../.github/workflows/garde-veille.yml)
visite la copie de secours **toutes les dix minutes**, pendant les heures où
l'on consulte le site — 108 visites par jour, chacune étant un seul appel à
`/api/lexique` (la même adresse que la sonde de disponibilité de `render.yaml` :
une route JSON qui ne calcule rien). Le service n'a plus le temps de s'endormir,
donc le visiteur n'attend plus trente secondes, et il ne tombe plus sur un 502.

**La fenêtre est calculée, pas choisie au hasard.** Le calendrier de GitHub
s'exprime en **temps universel** — `*/10 5-22 * * *` couvre 6 h → 23 h à Paris
en hiver, 7 h → minuit en été. La nuit, le service dort : c'est le comportement
normal du palier gratuit, et c'est ce qui garde la consommation sous les
**750 heures offertes par mois** (environ 556 h estimées, marge de 15 %). Ce
n'est pas de l'avarice : un dépassement ne facture pas, il **suspend** les
services — pire que le sommeil. `python3 outils/garde-veille.py --cron "…"` dit
ce qu'une fenêtre couvre et refuse celles qui dépassent ; l'étape de CI
« Vérifier la fenêtre » lance ce contrôle avant chaque visite. Une fenêtre 24 h/24
consommerait 738 h par mois et est **refusée** par ce contrôle.

**Il ne parle que quand ça change.** Chaque commentaire porte son état en
marqueur (`<!-- garde-veille: ok -->` ou `<!-- garde-veille: panne -->`) : c'est
le marqueur lui-même qui dit, au passage suivant, s'il y a quelque chose à
publier. La panne se dit, le retour à la normale aussi — sinon la page
raconterait une panne qui n'existe plus —, et tout le reste est silence. Un
garde-veille qui commente toutes les dix minutes est un garde-veille qu'on
coupe. Sa page est distincte de celle de la veille hebdomadaire :
**« Garde-veille — la copie de secours (Render) »**.

**Ce qu'il ne peut pas faire.**

- **Relever un service suspendu.** Une visite ne règle pas un quota épuisé ni une
  facturation en échec : il faut le tableau de bord ou le crochet de déploiement.
- **Remplacer la veille.** Il regarde un chemin (`/api/lexique`) ; la veille
  regarde soixante-huit (page, robots, sitemap, images, vingt-deux routes).
- **Garantir la seconde près.** Le calendrier de GitHub est *au mieux* : un
  passage peut être retardé de quelques minutes aux heures chargées — d'où une
  visite toutes les dix minutes, et non toutes les quinze.
- **Survivre à un dépôt endormi.** GitHub désactive les calendriers d'un dépôt
  sans activité pendant soixante jours. Le dépôt est actif ; si cela arrivait,
  l'onglet **Actions** → *Garde-veille* → **Run workflow** le relance, et un
  simple clic sur **Enable workflow** suffit à réarmer le calendrier.

Contrôle à la main, depuis n'importe quel poste :

```bash
python3 outils/garde-veille.py --ping          # frappe à la porte et raconte
python3 outils/garde-veille.py --cron "*/10 5-22 * * *"   # ce que la fenêtre couvre
```

---

## Ce qu'il faut savoir avant de partager le lien

- **Aucune donnée personnelle.** Le simulateur n'a ni base de données, ni
  compte, ni formulaire d'inscription. Aucun secret n'est à configurer.
- **Le disque est éphémère** sur la plupart des offres gratuites. Sans
  conséquence : les exports JSON/CSV sont construits en mémoire et n'écrivent
  aucun fichier.
- **Les appels sortants sont optionnels.** Le bouton « Rafraîchir les données »
  interroge des API publiques (Eurostat, BCE, Banque mondiale, Frankfurter). Si
  l'hébergeur bloque le réseau sortant, la page continue de fonctionner avec
  l'instantané embarqué dans le dépôt ; le contexte reste affiché en mode
  « référence ». Vérifié : sans réseau, `/api/contexte?refresh=1` répond 200.
- **Les journaux.** Les accès ne sont pas tracés par défaut. Pour diagnostiquer
  un déploiement, ajouter la variable d'environnement `SIMULATEUR_LOG=1`.
- **Deux workers** suffisent largement : une simulation complète prend une
  cinquantaine de millisecondes de calcul.
- **Le partage par lien suit l'adresse.** Le bouton « 🔗 Partager mes réglages »
  écrit les leviers dans l'URL : il fonctionne avec n'importe quelle adresse
  ci-dessus, sans configuration supplémentaire.

### Dépannage

| Symptôme | Cause probable |
|---|---|
| « Blueprint file `render.yaml` not found on main branch » | Render ne lit que la branche **par défaut** et garde l'arbre du dépôt en cache : le fichier n'existait pas encore sur `main` quand la page a été ouverte, ou vient tout juste d'y être fusionné. Fusionner d'abord, puis **Retry**. La création manuelle (New → Web Service) reste possible sans Blueprint. |
| Le dépôt n'apparaît pas dans la liste des Blueprints | L'application GitHub de Render n'a pas accès à ce dépôt : l'autoriser dans **GitHub → Settings → Applications → Render → Configure**, puis recharger la page. |
| « 502 Bad Gateway » sur **toutes** les adresses, sonde de disponibilité comprise | Personne ne répond derrière la passerelle : le service est **suspendu**, endormi depuis trop longtemps, ou son dernier démarrage a échoué. Voir « [Quand la copie de secours ne répond pas](#quand-la-copie-de-secours-ne-répond-pas-502) ». |
| « 502 Bad Gateway » juste après le déploiement | Le service n'écoute pas sur `$PORT` : vérifier la commande de démarrage (celle du dépôt est bonne : `gunicorn --bind 0.0.0.0:$PORT …`). |
| « No more than 12 Serverless Functions » au déploiement Vercel | `api/` contient plus de 12 fichiers `.py`. Ne garder que `[...path].py` et `verifier-source.py` ; `python3 outils/generer-fonctions-api.py` retire les fonctions générées route par route. S'il signale un fichier inconnu, le retirer ou le déplacer d'abord. |
| « 404 » sur toutes les routes, page d'accueil comprise | L'application est montée sous un préfixe (`SCRIPT_NAME`) non géré par le proxy. Servir à la racine. |
| La page s'ouvre vide | Premier réveil de l'offre gratuite : attendre ~30 s et recharger. |
| « Application failed to respond » au bout de 30 s | `--timeout` trop court au démarrage à froid ; le passer à 120 s. |
| Le contexte reste daté | Réseau sortant bloqué chez l'hébergeur : comportement attendu, voir ci-dessus. |
