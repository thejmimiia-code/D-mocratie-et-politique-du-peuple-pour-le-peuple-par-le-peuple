# 19. Plan de renforcement : ce qui manquait, ce qui est corrigé, ce qui reste

> **Audit du 12 octobre 2026.** Ce document ne raconte pas le projet : il recense les trous
> trouvés en le mesurant, dit lesquels sont bouchés, et classe les autres. Chaque constat
> porte la commande qui le vérifie — un constat qu'on ne peut pas rejouer est une opinion.

---

## 1. La méthode : chercher les trous par la mesure, pas par la relecture

Six instruments, tous exécutables sans réseau ni dépendance :

| Instrument | Ce qu'il mesure | Commande |
|---|---|---|
| Suite de tests | le comportement promis | `python3 -m unittest discover -s tests -p "test_*.py"` |
| Générateurs en mode contrôle | la fraîcheur des documents engendrés | `python3 outils/<generateur>.py --verifier` |
| Garde-fou des compteurs | les chiffres annoncés dans le dépôt | `python3 outils/verifier-compteurs.py` |
| Croisements documentaires | l'existence des garde-fous annoncés | `python3 -m unittest tests.test_plan_global_croisements` |
| Harnais Node | la page réellement servie, exécutée | `python3 -m unittest tests.test_interface_navigateur` |
| Analyse statique | le style et les imports morts | `ruff check .` |

Deux principes ont guidé le reste : **un chiffre se déduit**, il ne se recopie pas ; et
**une limite qui n'est pas écrite est une limite cachée**.

---

## 2. Ce que l'audit a trouvé

### 2.1 La CI était rouge sur `main`, et personne ne le voyait plus

Le job `lint` échouait à chaque poussée : `ruff check .` relevait **1 553 avertissements**
sur `main` (994 `UP006` — `typing.List` au lieu de `list`, 140 `UP045`, 114 `UP035`,
98 `W293`, 77 `F401`, 52 `I001`, 22 `E402`). Une croix rouge permanente apprend surtout à
ignorer la croix rouge : la dernière fusion a été faite avec la CI rouge.

*État : corrigé.* `ruff check .` est vert, et la version de ruff est désormais épinglée dans
la CI (`pip install ruff==0.17.0`) : une montée de version qui change les règles doit être une
décision, pas une surprise du lundi matin.

Deux vrais défauts sont sortis de ce nettoyage — aucun n'était visible avant :

1. **Le contrôle de parité des routes ne contrôlait plus rien.** Il cherchait la chaîne
   `ROUTES: Tuple[str, ...]` dans le générateur ; la modernisation des annotations
   (`UP006`) écrivait `tuple[str, ...]`, et l'expression ne trouvait plus le registre
   (elle levait même une exception, masquée en erreur de test). Corrigé : l'expression
   accepte les deux écritures et une règle de compteur vérifie le nombre de routes servies.
2. **Un test calculait une somme et ne la comparait à rien.** La somme des strates
   communales (`tests/test_territoires_elections.py`) était affectée puis abandonnée ;
   vérifiée, elle révèle un **recouvrement de 21 communes (0,06 %)** entre la strate
   « rurales » (définition INSEE du rural) et le découpage en classes du modèle. L'écart est
   maintenant borné et nommé, et il reste à résorber (chantier P1-1).

### 2.1 bis Une deuxième croix rouge, sur le même commit

Le même commit porte deux contrôles Vercel : le projet de production est **vert**, et un
second projet (`…-aazf`, un ancien nom de projet resté branché) **échoue à chaque poussée** —
sur `main` comme sur les branches :

```bash
gh api repos/thejmimiia-code/D-mocratie-et-politique-du-peuple-pour-le-peuple-par-le-peuple/commits/df092fe/status \
  --jq '.statuses[] | "\(.context) → \(.state)"'
```

Le projet de production, lui, n'échoue pas systématiquement : il est vert sur `df092fe`
(l'état de `main`) et sur un commit de cette branche, puis rouge sur le suivant — où seuls des
documents et le journal ont bougé. Sans accès aux journaux Vercel, la cause est indiagnosticable
d'ici : elle est donc écrite comme telle, plutôt que devinée.

*État : non corrigé, et hors de portée du dépôt.* Le remède n'est pas dans le code : il faut
débrancher ou réparer ces projets dans Vercel (P1‑4). Tant qu'ils échouent, la conclusion
« la CI est rouge » reste vraie pour qui regarde la page du commit plutôt que ses jobs — et une
croix rouge qu'on ne peut pas réparer dans le dépôt apprend la même chose qu'une CI rouge :
à l'ignorer.

### 2.2 Le dépôt annonçait des compteurs périmés

Relevé le 12 octobre 2026 :

| Annonce trouvée | Où | Réel |
|---|---|---|
| « 93 leviers croisables » | `pyproject.toml`, `outils/reglages_depot.html`, deux tests | **156** |
| « 149 leviers croisables » | `outils/details_depot.py`, `simulateur/compression.py`, `simulateur/dashboard.py` | **156** |
| « 38 indicateurs publics » | `NOTE_POUR_CLAUDE.md`, `docs/REPOSITORY_DETAILS.md`, `docs/SIMULATEUR_PARAMETRABLE.md` | **52** |
| « 33 garde-fous » | `simulateur/bulles.py`, `docs/SIMULATEUR_PARAMETRABLE.md` | **31** (26 absolus + 5 en écart) |
| « 16 routes du moteur » / « 20 routes exposées » | `README.md`, `docs/16_INSTANCES_YOYO_ET_FENTES.md` | **22** |
| « modèle gigogne à 4 échelons » | `simulateur/web_server.py` | **5** |
| « Python 3.9+ » | `README.md`, `docs/METHODOLOGIE.md` | **3.11+** (`requires-python`) |
| « 18 domaines d'impact » | `README.md`, `CONTRIBUTING.md`, gabarit d'issue | **20** |

Pire : **six documents vivants recopiaient le compte de leurs tests** (166, 222, 247, 399,
836, 873, 922 — tous différents, tous périmés). Un compte de tests change à chaque commit :
l'écrire dans un document, c'est programmer sa propre péremption.

*État : corrigé et gardé.* `outils/verifier-compteurs.py` lit douze référentiels dans le code
(leviers, réglages, préréglages, familles, domaines, indicateurs, indicateurs publics,
domaines sociétaux, garde-fous, scénarios, échelons, routes) et confronte chaque phrase du
dépôt qui les annonce au chiffre du jour — 24 règles de phrase, plus une seconde famille :
les comptes qu'un document vivant ne doit pas annoncer (les tests). Les rapports datés
(journal, R&D, audits, revues de dépôts tiers) sont exemptés, **chacun avec sa raison
écrite**, et le contrôle refuse une exemption sans raison.

`tests/test_compteurs.py` est la contre-épreuve : chaque règle doit accepter son gabarit au
compte réel **et rugir sur un compte faussé**. Une règle morte est un test qui échoue.

### 2.3 Onze tests ne s'exécutaient jamais

`tests/test_societe.py` et `tests/test_histoire.py` interrogent un serveur sur
`http://127.0.0.1:8000`. Aucun serveur n'étant lancé en CI, ils se sautaient — « 11 sauts »
affichés à chaque exécution depuis leur écriture. Le serveur qui les sert est la console
héritée (`python3 -m simulateur.web_server`), et les tests acceptent maintenant une adresse
par variable d'environnement.

*État : corrigé.* La CI démarre la console, attend qu'elle réponde, exécute les deux modules
(zéro saut), puis l'arrête. Les onze tests sont désormais de vrais contrôles.

### 2.4 Le dépôt GitHub annonce encore l'ancien monde

*Ce que l'audit relevait (5 octobre 2026)* : la description du dépôt disait « Modèle
gigogne à 4 échelons », l'adresse du site pointait vers une instance Vercel qui renvoyait
404, et aucun sujet n'était défini. `python3 outils/details_depot.py` affiche l'état
constaté et le bloc à coller.

*État au 13 octobre 2026 : à moitié corrigé, et le reste bloqué à dessein.*

- **Corrigé côté dépôt** : la description et les sujets des documents sont à jour et
  **engendrés** (`outils/details_depot.py --doc`, contrôlés par `--verifier-doc`) ; l'adresse
  du site n'est plus « morte » — elle sert l'application, et l'outil **pose la question**
  (`adresse_repond`) au lieu de l'affirmer, avec une troisième réponse honnête quand le
  réseau manque. La page `outils/reglages_depot.html` porte enfin des contrôles : elle
  proposait de vider le champ, et visait un nom de dépôt tronqué — donc un dépôt inexistant.
  Voir `docs/RD_PREUVE_ET_OUTILLAGE.md`.
- **Appliqué par le propriétaire (constaté le 13 octobre 2026, par l'API GitHub)** : la
  **description** et le **site web** du dépôt sont à jour — la description annonce les
  5 échelons et les 156 leviers, et le champ *Website* porte l'adresse de l'application.
- **Reste à faire** : les **sujets** (`topics` est toujours vide — c'est le champ où il faut
  taper chaque mot puis valider, un par un) et l'**aperçu social**, que GitHub n'accepte
  qu'à la main. Le bloc exact est affiché par `python3 outils/details_depot.py` ; l'état est
  tenu à jour dans `docs/REPOSITORY_DETAILS.md`.
- **Pourquoi je ne l'applique pas moi-même** : le jeton dont dispose l'espace de travail est
  un jeton d'intégration sans droit d'administration — l'API refuse
  (`403 Resource not accessible by integration`), et l'outil le dit au lieu de faire
  semblant. Cette limite ne dépend pas du code.

### 2.5 Ce que l'audit n'a pas trouvé

Il faut le dire aussi, sinon la liste des trous ressemble à un catalogue de courses :
la suite est verte, les huit documents engendrés sont à jour, aucun module du simulateur
n'est orphelin de documentation, les garde-fous annoncés existent, et la page servie est
réellement parcourue par un harnais Node qui simule les gestes de l'utilisateur.

  > **Suite, 14 octobre 2026.** L'audit avait regardé les documents, les compteurs,
  > les tests et la CI — pas la **couverture de l'interface**. Un contrôle neuf
  > (`tests/test_couverture_des_routes.py`) a posé la question qui manquait : chaque
  > route servie par le moteur est-elle mise en œuvre par la page, ou excusée par
  > écrit ? Il a trouvé trois registres servis **sans aucun écran**
  > (`/api/contrepouvoirs`, `/api/dynamiques`, `/api/instances`, 229 097 octets à eux
  > trois). Les deux premiers sont désormais affichés dans la section « Contre-pouvoirs,
  > en chiffres » ; le troisième est excusé, avec sa raison, parce qu'il est la vue
  > courte du second. Le trou n'était pas dans un document : il était dans ce que
  > personne ne regardait.

---

## 3. Ce qui a été ajouté dans cette passe

Ordre chronologique, du plus visible au plus discret.

1. **Organiser la contradiction** (le renversement de charge) — `simulateur/contradiction.py` :
   **24 objections** (10 adossées aux mesures du plan, 14 aux hypothèses du moteur), chacune
   avec sa concession, le fait de réfutation qui ferait changer d'avis, et ses sources ;
   **4 contre-modèles** dans `docs/20_CONTRE_MODELES.md` ; le registre servi par
   `GET /api/objections` et affiché dans la section *Objections* de la page ; le gabarit
   d'issue « Objection sourcée » ; **les engagements datés** dans
   `docs/22_REGISTRE_ENGAGEMENTS.md`, engendrés en rejouant le scénario de mandature, avec
   la source extérieure qui jugera chaque indicateur et les seuils de réussite et d'échec.
   Les gages y sont confrontés à la portée des leviers : **21 Md€/an de réserve de portée**,
   calculée et non saisie.
2. **Le garde-fou des compteurs** — `outils/verifier-compteurs.py` (12 référentiels,
   24 règles, une famille d'interdits motivés) et `tests/test_compteurs.py` (contre-épreuve).
3. **La CI réparée** — ruff à zéro, ruff épinglé, onze tests d'API exécutés pour de bon.
4. **Ce document** — qui dit ce qui reste, et comment le vérifier.

---

## 4. Le plan : ce qui reste, par ordre de rendement

Chaque chantier porte sa preuve de fin : ce qu'il faudra montrer pour dire « c'est fait ».

### P1 — Petits, certains, vérifiables tout de suite

| # | Chantier | Pourquoi | Preuve de fin |
|---|---|---|---|
| P1‑1 | **Résorber le recouvrement de 21 communes** entre la strate rurale et les classes du modèle (`simulateur/model.py`) | une somme de strates qui dépasse son propre total est une incohérence de données, pas un détail d'arrondi | le test de `tests/test_territoires_elections.py` passe sans l'écart documenté |
| P1‑2 | **Figer la date des données Banque mondiale** : l'URL de `simulateur/donnees_live.py` porte `date=2024` en dur, donc l'« instant T » peut rester figé sur 2024 sans que rien ne le signale | une donnée en direct qui n'avance plus sans le dire viole la promesse affichée | un indicateur daté dans le ruban, et un test qui refuse une période de plus d'un an |
| P1‑4 | **Débrancher ou réparer le projet Vercel fantôme** (`…-aazf`) qui échoue sur `main` comme sur les branches | une croix rouge qu'on ne peut pas réparer dans le dépôt apprend la même chose qu'une CI rouge : à l'ignorer | le statut du dernier commit ne porte plus de contrôle en échec |
| P1‑3 | **Étendre le garde-fou aux taux et aux parts** annoncés (« 30 % aux PME », « 3 % du PIB », « 5,5 % de TVA ») : aujourd'hui seuls les comptages du code sont couverts | ce sont les chiffres les plus cités dans les débats publics, donc les plus coûteux à voir vieillir | `outils/verifier-compteurs.py` couvre une famille « taux », avec contre-épreuve |

### P2 — Chantiers de fond, à décider avant de coder

| # | Chantier | Pourquoi | Preuve de fin |
|---|---|---|---|
| P2‑1 | **Décider du sort de la console héritée** (`simulateur/web_server.py`, ~4 800 lignes, cinq gabarits HTML) : ses familles d'API (`/api/societe`, `/api/histoire`) ne sont servies ni par le routeur du dashboard ni par la fonction unique déployée ; le site en ligne ne les expose donc pas | deux serveurs, deux contrats : le jour où l'un dérive, plus personne ne sait lequel fait foi | une décision écrite, puis soit le portage des familles dans `simulateur/dashboard.py`, soit un renvoi assumé « console locale » dans `docs/HEBERGEMENT.md` |
| P2‑2 | **Automatiser le suivi du registre d'engagements** : les 6 indicateurs de `docs/22` sont vérifiables à la main ; trois d'entre eux ont une source publique interrogeable | un registre d'engagements qu'on ne relit pas devient un monument | `GET /api/engagements` renvoie, pour chaque indicateur, la dernière valeur publiée et l'écart au seuil |
| P2‑3 | **Ouvrir les objections du registre comme issues** (`outils/ouvrir-objections.py`) en réutilisant le gabarit « Objection sourcée » | le registre vit dans un document ; les objections vivent dans les discussions | les 24 objections existent en issues, avec leur numéro dans `docs/21` |
| P2‑4 | **Budgéter le poids de la page** : `index.html` pèse 249 416 caractères, et la page charge catalogues et scénarios au démarrage | la fluidité est une qualité politique : une page lente n'est pas lue | `python3 outils/mesurer_fluidite.py` fixe un budget, et la CI échoue au-delà de +10 % |

### P3 — Long terme, à instruire

| # | Chantier | Pourquoi |
|---|---|---|
| P3‑1 | **Vérifier les sources externes par un contrôle programmé** (liens, millésimes, disponibilité) | les sources citées vieillissent sans prévenir ; un lien mort est une affirmation morte |
| P3‑2 | **Renforcer l'expérience du laboratoire** : le seuil de 3 % y est indifférenciant (500 tirages sur 2 500 simulations ne séparent rien), documenté dans `docs/LABORATOIRE_RD.md` | un test qui ne discrimine pas donne une fausse assurance |
| P3‑3 | **Rendre NOTE_POUR_CLAUDE.md exécutable** : ses cases à cocher deviendraient un script (`outils/verifier-depot.py`), y compris l'empreinte de l'aperçu social | une liste de courses non vérifiée est une liste de courses oubliée |

---

## 5. Les limites de ce plan

- **L'auditeur n'est pas indépendant.** Le même agent a écrit le plan et le code qu'il
  décrit ; les constats cités sont rejouables par commande, c'est la seule garantie offerte.
- **Les compteurs ne sont pas des formules.** Vérifier qu'un document annonce 156 leviers ne
  dit rien de la justesse de leurs coefficients : ce contrôle-là est celui de
  `docs/METHODOLOGIE.md` et des sources, pas celui de cet outil.
- **La CI ne teste pas la page dans un vrai navigateur** : le harnais Node exécute le
  JavaScript de la page avec un `fetch` simulé. Le rendu visuel, l'accessibilité et les
  feuilles de style restent hors de portée des contrôles automatiques.
- **Rien ici ne dépend d'un réseau.** Les données publiques en direct sont donc vérifiées par
  des tests hors ligne sur des instantanés datés : une panne d'Eurostat en production ne se
  verrait pas dans la suite.
- Ce plan ne prétend pas être exhaustif : il liste ce que six instruments ont vu le
  12 octobre 2026. Les instruments suivants verront autre chose.
