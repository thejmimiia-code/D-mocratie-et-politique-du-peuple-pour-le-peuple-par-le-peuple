# Point sur les commits et intégration des branches — 3 octobre 2026

## Inventaire distant

Une seule PR ouverte lors du recensement : **#11**, initialement en conflit avec
`main`. La PR **#10** avait déjà été fusionnée. L'inspection des références distantes
a aussi identifié une branche sans PR contenant quatre commits non fusionnés.

| Commit | Objet | Décision de cet audit |
|---|---|---|
| `3a7d3c2` | Analyse documentaire des tensions mondiales | Déjà dans `main`, conservée avec avertissement méthodologique |
| `b729306` | Strate annuelle, 5 scénarios, CLI/dashboard/ÉVA et tests | Déjà fusionné par #10 ; intégré sans supprimer ses fonctionnalités |
| `61fce09` | Fusion de #10 | Base de l'intégration |
| `d790d67` | Laboratoires R&D, import et validation temporelle | Lot #11 conservé et testé avec la nouvelle base |
| `938dc22` | Installation, fichiers et contrôle des arrêts | Lot #11 conservé ; aide CLI corrigée pour son contrôle d'installation |
| `62ce03c` | Multi-agents, web, société/histoire, documentation et GPLv3 | Différé : divergence importante, contrôle de style non satisfait et choix de licence à clarifier |
| `15c7a67` | Manifeste et restrictions d'usage dans le README | Différé : dépend du lot précédent et comporte des conditions de réutilisation à clarifier |
| `67e3440` | Catalogue R&D et correction de titre | Différé avec le lot dont il dépend ; pas de vérification indépendante de toutes les références externes |
| `ba62c3d` | Correction du nom du fondateur dans ce README | Différé avec son README de référence ; contenu non supprimé de la branche distante |

Branche différée : `arena/01a0b3da-d-mocratie-et-politique-du-peu`, tête `ba62c3d`.
Elle diverge depuis `7536de7` et représente environ 20 900 lignes ajoutées sur
49 fichiers par rapport à l'ancêtre commun avec `main`. Elle n'est donc pas un
simple complément de quelques lignes à la PR #11.

L'examen inclut l'historique et les différences de commits, les interfaces en
collision, les tests, les chemins d'entrée web/CLI, le prototype multi-agents et
les changements de licence/README. Il ne constitue pas une certification juridique
ni une vérification de chaque affirmation documentaire externe de cette branche.

## Résolution des trois collisions #10 / #11

Les deux développements avaient créé indépendamment `simulateur/geopolitique.py`
et `tests/test_geopolitique.py`. Le moteur macro importait donc une interface
incompatible avec le laboratoire mensuel.

- **Annuel** : code de #10 isolé dans `simulateur/geopolitique_annuelle.py`, tests
  préservés dans `tests/test_geopolitique_annuelle.py`.
- **Mensuel** : `simulateur/geopolitique.py` et ses tests conservent leur API et leur CLI.
- Les anciens imports publics annuels depuis `simulateur.geopolitique` sont
  conservés par délégation différée ; les imports internes du moteur vont directement
  vers le module annuel pour éviter une dépendance circulaire.
- Le moteur macro conserve **les deux** contributions : strate annuelle et
  `facteur_activite` optionnel. Ce facteur s'applique aussi à la base de calcul
  du budget de défense et des chocs annuels.
- Les deux ensembles de contrôles CI sont conservés.

Un problème supplémentaire a été trouvé : `main.py --help` affichait l'aide mais
renvoyait le code d'erreur 1, ce qui faisait échouer le contrôle d'installation
ajouté précédemment. `--help` et `-h` renvoient désormais correctement 0.

## Cohérence scientifique : ne pas fusionner des significations incompatibles

Les champs historiques de la strate annuelle nommés `probabilite_*` sont conservés
pour compatibilité des exports. Ils résultent de formules déterministes sans
calibration probabiliste. L'affichage CLI/dashboard les présente désormais comme
**indices heuristiques sur 100** ; le journal exporté explicite cette limite.

Le scénario annuel applique des coefficients post-nucléaires conventionnels. Le
laboratoire mensuel conserve au contraire son arrêt hors domaine de validité à
l'emploi imposé. Les deux ne sont pas présentés comme une même estimation ; aucune
probabilité réelle ni conséquence nucléaire validée n'est déduite de leur coexistence.
L'évaluation simplifiée de la PDE n'est pas non plus une décision juridique réelle.

## Tests réellement exécutés

### Lot intégré #10 + #11

- **141 tests réussis**, sans test ignoré : 106 tests de #11, 28 tests annuels de #10,
  et 7 nouveaux tests d'intégration.
- `ruff check .` réussi.
- Comparaison par processus séparés du snapshot `origin/main` et du code intégré :
  **identité numérique exacte des neuf scénarios annuels**, à toutes les étapes,
  sur tous les champs de résultat hors commentaires, avec paramètres par défaut.
- Neuf scénarios lancés par la CLI avec export JSON, et par l'API du dashboard.
- Neuf scénarios de l'adaptateur ÉVA testés avec un bus simulé, sans prétendre à
  une connexion au système ÉVA réel.
- Campagnes mensuelles et résilience relancées ; import et validation temporelle
  exécutés en chaîne. Le cas sans connaissances historiques continue de s'abstenir.
- Installation éditable et aide du point d'entrée validées localement.

La comparaison numérique n'est pas une validation empirique des coefficients.
Ces résultats locaux ne prouvent pas une exécution GitHub de toute la matrice Python.

### Branche différée `ba62c3d`

L'arbre a été extrait dans un répertoire temporaire ignoré, sans changer de branche
ni modifier sa référence distante.

- `unittest discover` : **247 tests recensés, 236 exécutés avec succès, 11 ignorés**.
- Ruff avec les règles du dépôt principal : **483 signalements**, dont 412 proposés
  comme corrigeables automatiquement ; aucune correction automatique n'a été
  appliquée aveuglément à cette branche.
- Le fichier `LICENSE` devient GPLv3, tandis que le README ajoute des restrictions
  commerciales et de réutilisation politique. Ces textes doivent être rendus
  cohérents avec la licence choisie avant leur intégration. Aucune nouvelle licence
  n'est imposée par cet audit ; MIT reste en place pour le lot #11.

**Décision : ne pas confondre tests unitaires verts et autorisation d'une fusion
aveugle.** Les quatre commits de cette branche restent disponibles, non supprimés,
pour une intégration dédiée après clarification des conditions d'usage et résolution
des divergences avec les fonctionnalités actuelles de `main`.
