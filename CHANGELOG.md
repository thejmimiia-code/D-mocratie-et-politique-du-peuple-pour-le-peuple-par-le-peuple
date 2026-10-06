# Changelog

Toutes les modifications notables de ce projet sont documentées ici.
Format basisé sur [Keep a Changelog](https://keepachangelog.com/),
et ce projet suit [Semantic Versioning](https://semver.org/).

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
