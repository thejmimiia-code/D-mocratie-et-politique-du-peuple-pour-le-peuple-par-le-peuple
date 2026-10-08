# Changelog

Toutes les modifications notables de ce projet sont documentées ici.
Format basisé sur [Keep a Changelog](https://keepachangelog.com/),
et ce projet suit [Semantic Versioning](https://semver.org/).

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
