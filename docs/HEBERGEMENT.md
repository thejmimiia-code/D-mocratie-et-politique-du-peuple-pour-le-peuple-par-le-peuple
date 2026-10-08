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
JavaScript. Le simulateur, lui, **calcule** : 101 leviers croisés, moteur
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
  sont immédiates. C'est le comportement normal du palier gratuit, pas un bug.
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
| `Procfile` | Commande de démarrage pour les plateformes qui le détectent. |
| `requirements.txt` | `gunicorn`, et rien d'autre — dépendance **d'hébergement**, pas d'exécution. |
| `runtime.txt` | Version de Python (`3.11.9`). Render et Heroku le lisent. |
| `render.yaml` | Recette du déploiement Render utilisée par le bouton. |
| `Dockerfile` | Image de production, non-root, avec sonde de santé. |
| `.github/workflows/image-docker.yml` | Publie l'image dans GHCR. |

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
  `/api/*` du moteur, via `simulateur/pont_api.py`. `api/verifier-source.py` est une
  fonction distincte, propre au site.

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
| « 502 Bad Gateway » juste après le déploiement | Le service n'écoute pas sur `$PORT` : vérifier la commande de démarrage. |
| « No more than 12 Serverless Functions » au déploiement Vercel | `api/` contient plus de 12 fichiers `.py`. Ne garder que `[...path].py` et `verifier-source.py` ; `python3 outils/generer-fonctions-api.py` retire les fonctions générées route par route. S'il signale un fichier inconnu, le retirer ou le déplacer d'abord. |
| « 404 » sur toutes les routes, page d'accueil comprise | L'application est montée sous un préfixe (`SCRIPT_NAME`) non géré par le proxy. Servir à la racine. |
| La page s'ouvre vide | Premier réveil de l'offre gratuite : attendre ~30 s et recharger. |
| « Application failed to respond » au bout de 30 s | `--timeout` trop court au démarrage à froid ; le passer à 120 s. |
| Le contexte reste daté | Réseau sortant bloqué chez l'hébergeur : comportement attendu, voir ci-dessus. |
