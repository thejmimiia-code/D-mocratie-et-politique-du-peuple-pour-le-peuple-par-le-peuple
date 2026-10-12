# 18. Plan global, brainstorming de chaque possibilité et garantie « sans trou »

> Cette page n'est pas une déclaration d'intention : c'est l'état vérifié du croisement
> de tous les registres du dépôt, la liste des possibilités examinées une par une, et le
> protocole qui empêche le résultat de se dégrader. Chaque chiffre est lu dans le code au
> moment de la rédaction ; la commande `python3 -m unittest tests.test_plan_global_croisements`
> rejoue la vérification à chaque modification.

---

## 1. Ce que « sans trou » veut dire, ici, opérationnellement

Un trou n'est pas « un sujet qu'on n'a pas encore traité ». Dans ce dépôt, un trou est une
**promesse implicite non tenue** : une donnée annoncée par un module et introuvable dans un
autre, un chiffre affiché sans règle de calcul, une route documentée qui n'existe pas, un
document que personne n'indexe. Cinq clauses règlent le cas, et chacune est tenue par du code :

1. **Tout ce qui est chiffré est déduit.** Les seuils viennent de `gouvernance_contrepouvoir.seuil()`,
   les jours de `instances_et_dynamiques.oscillation()`, les scores de `robustesse()`, les strates
   des thèmes d'effet des leviers. Aucun registre ne recopie un nombre écrit ailleurs :
   `coherence_nuances()` vérifie que les listes d'exceptions ne sont pas devenues des fourre-tout.
2. **Tout ce qui est croisé est atteignable.** Chaque pièce des six registres (verrous, fentes,
   trajets, mécanismes, instances, stratégies) doit être joignable par au moins un réglage par le
   chemin des articles — sauf un verrou qu'aucun curseur ne peut déplacer, qui est alors *expliqué*
   ligne par ligne. L'invariant s'appelle `connaissances_inaccessibles` et doit rester vide.
3. **Tout ce qui est écrit est généré ou vérifié.** `docs/17`, `docs/VERIFICATION_DONNEES.md`,
   `index.html`, l'aperçu social et la liste des leviers de `docs/SIMULATEUR_PARAMETRABLE.md` sont
   produits par des scripts ; la suite de tests échoue si la page a pris du retard sur le module.
4. **Tout ce qui est exposé est testé en HTTP.** Chaque route a son test (`TestNuancesServies`,
   `TestInstancesServies`, `TestConstitutionServie`, …), et `tests/navigateur_interface.mjs` rejoue
   le parcours complet du navigateur sur des réponses réelles du serveur — 141 étapes.
5. **Une limite assumée s'écrit.** Ce qui n'est pas simulable est nommé, avec la raison, dans le
   module et dans la documentation (18 verrous hors réglage, 9 réglages sans géométrie chiffrable,
   les quatre limites de `synthese_pour_api()`).

---

## 2. La carte du dépôt, avec ses compteurs

| Registre | Where | Taille | État du croisement |
|---|---|---:|---|
| Leviers de politique publique | `simulateur/parametres.py` → `LEVIERS` | **156** | 14 familles, tous rattachés à au moins un domaine mesurable |
| Réglages institutionnels | `simulateur/nuances_institutionnelles.py` → `REGLAGES` | **55** | un par levier `reglage_*`, zéro orphelin dans les deux sens |
| Préréglages doctrinaux | `PRESETS` | **16** | `assemblees_souveraines` et `verrouillage_par_le_haut` explorent la géométrie institutionnelle |
| Fiches d'articles analysés | `simulateur/constitution_analysee.py` | 109 | chaque levier qui cite un article le cite dans le registre |
| Registre légal | `simulateur/reglements_lois.py` → `REGISTRE_LEGAL` | 189 identifiants | `articles_hors_registre` doit rester vide |
| Articles croisés | `croisements()` | **99 numéros** | index déduit des citations des six modules, jamais saisi |
| Verrous (seuils chiffrés) | `gouvernance_contrepouvoir.VERROUS` | **38** | 20 réglables, 18 expliqués hors réglage — partition stricte, vérifiée |
| Mécanismes | `MECANISMES` | **31** | 31 joignables par un réglage |
| Instances et autorités | `instances_et_dynamiques.INSTANCES` | **26** | 26 joignables |
| Trajets procéduraux | `TRAJETS` | **8** | 8 joignables, 8 avec jours de rigueur calculés |
| Fentes non écrites | `FENTES` | **12** | 12 ciblées par un réglage, 0 inatteignable |
| Stratégies d'usage | `STRATEGIES` | **15** | 15 joignables |
| Indices institutionnels | `INDICES` | **8** | base 50 au statu quo, borne haute et brut affichés |
| Seuils recalculés | `seuils_ajustes()` | **22** | écart à zéro au statu quo, tous les sens vérifiés |
| Strates | `tableau_des_strates()` | 5 | 1 locale (13 réglages) · 2 nationale (55) · 3 européenne (21) · 4 mondiale (19) · 5 géopolitique (5) |
| Domaines d'impact | `simulateur/domaines.py` | 20 | notés 0-100, un thème inconnu fait échouer le test du catalogue allégé |
| Routes d'API | `simulateur/dashboard.py`, `api/*.py` | 21 GET + 3 POST | générées par `outils/generer-fonctions-api.py`, appariées une à une |
| Modules `simulateur/` | 40 fichiers | tous cités dans un document | zéro module orphelin |
| Documents | `docs/*.md` | 43 | tous indexés dans `docs/README.md` |

---

## 3. Le brainstorming : chaque possibilité, examinée, et son sort

La méthode : pour chaque possibilité découverte pendant l'audit — un manque, une faille, un
raccourci, une question que le lecteur se poserait — on décide entre *fermer maintenant*, *fermer
avec une limite écrite*, ou *laisser ouvert en le nommant*. Les trois sont légitimes ; le seul
interdit est le silence.

| # | Possibilité examinée | Décision | Ce qui a été fait |
|---|---|---|---|
| 1 | Les 48 nuances institutionnelles n'étaient que du commentaire, pas du droit simulable | fermée (nappe précédente) | `reglage_*` : curseurs, interrupteurs et choix branchés sur des règles de recalcul |
| 2 | Le Congrès avait une clé de verrou inventée (`congres_voix`) | fermée | branchement sur le vrai verrou `congres_revision` ; le `seuil()` sert 555 voix, pas un souvenir |
| 3 | Les instances étaient inatteignables par article (`fondement` en liste ignoré) | fermée | `_citations()` normalise listes et tuples : 26/26 instances joignables |
| 4 | Un verrou non réglable comptait comme un trou | fermée | `VERROUS_HORS_REGLAGE` : 18 raisons écrites, partition vérifiée par `verrous_non_expliques` |
| 5 | Des réglages n'auraient pu être qualifiés de « géométriques » sans nombre | fermée | `REGLAGES_SANS_GEOMETRIE` avec 9 exemptions motivées, et `exemptions_perimees` qui rugit si une exemption devient fausse |
| 6 | Haute Cour, CJR, CESE, Défenseur des droits, commissions d'enquête, procédure accélérée, art. 37/41 : aucun réglage n'y menait | **fermée dans cette passe** | 7 nouveaux réglages (`reglage_haute_cour_non_parlementaire`, `reglage_cee_consultation_prealable`, `reglage_defenseur_saisine_directe`, `reglage_commission_enquete_droit_de_bloc`, `reglage_procedure_acceleree_encadree`, `reglage_declassification_legislative`, `reglage_nouvelle_deliberation_supprimee`) |
| 7 | Deux trajets n'étaient réglables par personne (`revision_referendum`, `controle_juge`) | fermée | contrôle référendaire = +30 j avant promulgation ; appel QPC = +60 j de double filtre. `trajets_sans_reglage` est passé à vide |
| 8 | Les réglages n'avaient aucun marqueur exploitable par l'interface | fermée | `tags=("nuance_institutionnelle", niveau)` sur les 55 leviers — le champ existait, il était vide |
| 9 | La couche était invisible dans la page | fermée | section « Nuances institutionnelles » : indices, seuils, délais, fentes, strates, garde-fous — recalculée à chaque simulation par `POST /api/nuances` ; le bloc « Verrous : ce qui tient, ce qui lâche » ajoute la partition des 38 règles de blocage et la liste des réglages déplacés (`etat_des_verrous()`, section 4 bis) |
| 10 | Un levier rattaché à un article n'en laissait rien voir | fermée | puce « droit positif » dans la carte du levier, lien direct vers `/api/constitution?article=N` |
| 11 | `GET /api/nuances?article=` ne renvoyait que des réglages | fermée | `croisement_pour()` renvoie l'article entier : réglages, verrous, mécanismes, instances, fentes, trajets, stratégies, seuils et fiches — et accepte `49`, `article 49`, `CONST_ART_49`, `art. 72-1` |
| 12 | Trois autres routes savaient calculer un seuil mais pas rappeler le réglage qui le déplace | fermée | `/api/constitution`, `/api/instances`, `/api/contrepouvoirs` exposent `reglages` |
| 13 | Le vecteur complet ne tenait pas dans une URL pour `/api/nuances` | fermée | `POST /api/nuances` (mêmes calculs, même méthode `_repondre_nuances`, y compris sur Vercel via `pont_api`) |
| 14 | Un `POST /api/nuances` muet aurait cassé en production | fermée | `test_post_accepte_le_vecteur_complet` : corps rempli et corps vide |
| 15 | La liste des routes du docstring décrivait 5 routes en moins | fermée | docstring complétée (`conseil`, `garde_fous`, `lexique`, `presets`, `proxy`, `marches`, catalogue, et les trois POST) — le test de parité route↔docstring la maintient |
| 16 | Aucun préréglage ne testait la couche institutionnelle seule | fermée | `assemblees_souveraines` (37 réglages ouverts, zéro ligne budgétaire) et `verrouillage_par_le_haut` (7 verrouillages) |
| 17 | `docs/17` était écrit à la main et ne pouvait que pourrir | fermée | `outils/generer-doc-nuances.py` régénère sept sections (dont une nouvelle « verrous expliqués hors réglage » et une « cinq strates ») et un mode `--verifier` refuse le déséquilibre |
| 18 | L'aperçu social annonçait 101 leviers | fermée | `outils/apercu_social.py` lit `LEVIERS` et `DOMAINES` ; image régénérée |
| 19 | 16 documents n'étaient indexés nulle part | fermée | section « Documents de travail » dans `docs/README.md`, et un test exige que `docs/*.md` soit indexé |
| 20 | Un thème d'effet hors des 20 domaines aurait pollué les bulles | fermée | le catalogue allégé teste `theme_inconnu` ; le réglage CESE est passé de `dialogue_social` (inexistant) à `participation` |
| 21 | Deux clés de `coherence_nuances()` étaient fausses (`connaissances_lyingees`, Intersection de types différents) | fermée | remplacées par `accesibilite_des_connaissances` et `connaissances_inaccessibles`, calculées sur `reglages_par_connaissance()` |
| 22 | Une clé publique était anglophone (`fentes_unchanged`) et un doublon de clé figurait dans `VERROUS_REGLAGES` | fermées | `fentes_inchangees` ; doublon supprimé |
| 23 | Le compteur de leviers du catalogue était écrit en dur dans dix documents | fermée | tous repris à 156, plus les compteurs de réglages (48→55) et de préréglages (14→16) — et le test qui fige la liste des préréglages oblige à le faire |
| 24 | Rien n'obligeait à ce que chaque réglage touche au moins une strate | fermée | `reglages_sans_strate` ajouté aux garde-fous |
| 25 | Les garde-fous n'étaient visibles que dans les tests | fermée | la section de page affiche tout liste non vide en rouge, avec le nom de la liste |
| 26 | Le parcours navigateur ne prouvait rien pour la couche | fermée | quatre étapes ajoutées au harnais Node : section rendue, seuil 231 visible, garde-fous présent, puces d'article |
| **Ouvertes, assumées** | | | |
| 27 | Les 18 verrous hors réglage restent non simulables | ouverte, nommée | chacun porte sa raison ; les rendre réglables demanderait d'inventer une règle que le droit ne donne pas |
| 28 | Aucun réglage ne simule une *révision* elle-même (art. 89 autre que le seuil) | ouverte, nommée | le modèle déplace les nombres que le droit laisse déplacer ; il ne simule pas le pouvoir constituant |
| 29 | Les fentes ne sont pas chiffrées en euros | ouverte, nommée | `robustesse()` est une défendabilité 0-100 ; aucune source ne permet un montant |
| 30 | Pas de « coût » monétaire pour les 55 réglages | ouverte, nommée | `MECANISMES.cout` existe pour les mécanismes ; l'ajouter aux réglages supposerait des hypothèses non sourcées |
| 31 | Le citoyen ne peut pas encore exporter *que* la couche institutionnelle | ouverte | `outils/generer-export` n'existe pas ; la section est imprimable, l'export JSON complet si |
| 32 | Aucune arène locale ne simule l'articulation des 5 strates entre elles | ouverte, partielle | `bulles.py` strate par strate ; un scénario « la commune bloque la nation » reste à écrire |

---

## 4. Les sept réglages ajoutés dans cette passe, et ce qu'ils prouvent

| Réglage | Règle appliquée | Verrou déplacé (droit → réglé au maximum) | Registre fermé |
|---|---|---|---|
| `reglage_procedure_acceleree_encadree` | jours ajoutés au plancher avant délibération | `procedure_acceleree_delai` : 15 → 60 j | stratégie `procedure_acceleree` |
| `reglage_nouvelle_deliberation_supprimee` | suppression du droit de nouvelle délibération | `promulgation_nouvelle_deliberation` : 15 → 0 j | stratégie `rectification_de_calendrier`, trajet `projet_ordinaire` |
| `reglage_commission_enquete_droit_de_bloc` | deux commissions garanties par groupe et par session | `commission_enquete_signature` : 1 → 2 | instance `office_et_missions_parlementaires`, stratégie `resolution_enquete`, mécanisme `commission_enquete` |
| `reglage_haute_cour_non_parlementaire` | collège de juges, plus de vote politique préalable | `haute_cour_assemblees` : 385 → 120 ; `haute_cour_destitution` : 617 → 120 | mécanismes `haute_cour` et `cjr`, instance `haute_cour` |
| `reglage_cee_consultation_prealable` | jours de consultation obligatoire avant dépôt | `lois_programmation_saisine_cee` : 0 → 30 j | instance `conseil_economique_social_et_environnemental` |
| `reglage_defenseur_saisine_directe` | saisine sans intermédiaire | aucun (exemption écrite) | instance `defenseur_des_droits` |
| `reglage_declassification_legislative` | délai du Conseil sur l'articulation loi-règlement | `irrecevabilite_competence_delai` : 8 → 38 j | stratégie `defossilisation` |

Chacun respecte les quatre règles de la section 1 : zéro au défaut laisse le droit intact (l'écart
est à zéro, vérifié), la borne haute est un choix de politique publique déjà formulé ailleurs, la
base légale est citée dans le registre, et l'effet sur les indices est écrit en clair avec son coût.

---

## 4 bis. Deux trous structureux trouvés en chemin, et ce qui les empêche de revenir

Un plan « sans trou » se juge aux deux défauts qu'il a fait disparaître dans la passe, parce qu'ils
auraient rendu tout le reste faux.

**1. Vingt-trois fonctions Vercel au lieu de deux, et un pont qui n'existait pas.**
`outils/generer-fonctions-api.py` écrivait un fichier par route *plus* le parapluie : 23 fonctions
déclarées, là où `docs/HEBERGEMENT.md` promet deux fonctions et où l'offre Hobby plafonne à douze.
Pis : `api/[...path].py` importait `PontAPI`, classe que `simulateur/pont_api.py` ne définissait
pas — la fonction appelée par Vercel pour toute URL `/api/…` levait donc un `ImportError`, tandis
que les tests, eux, importaient les fichiers par route et ne la voyaient jamais. L'état déployé
était cassé, la suite verte.

Depuis : le générateur n'écrit **que** `api/[...path].py`, supprime les fichiers par route, et son
`--verifier` échoue si le parapluie est absent, périmé, ou si une fonction par route traîne encore.
`simulateur/pont_api.py` définit `chemin_de_pont()` (six formes d'URL testées) et `PontAPI`, qui ne
redéfinit aucune logique : il rend le chemin que l'hébergeur a déplacé dans la chaîne de requête,
puis laisse `DashboardHandler` router. `tests/test_vercel_runtime.py` charge le parapluie **par
chemin** (son nom n'est pas un nom de module) et sert pour de vrai `GET /api/scenarios` et
`POST /api/simuler` par-dessus ; `tests/test_plan_global_croisements.py` refuse tout fichier
étranger dans `api/`.

**2. La promesse d'interface n'était pas dans le fichier.**
La passe précédente avait noté « UI branchée » ; `index.html`, généré à partir de `HTML_PAGE`, ne
contenait ni la section des verrous ni les puces de réglages. Une note de travail n'est pas un
diff. Le bloc existe maintenant vraiment, côté serveur d'abord : `etat_des_verrous()` partage les
38 verrous du registre en touchés / intacts / hors réglage (la somme doit faire 38, testée sur trois
vecteurs), et signale en avertissements les règles privées de leur objet par un réglage — l'assiette
de la censure, le décompte au Congrès. La page ne calcule rien : `#section-verrous` met en forme
`NUANCES.verrous`, réutilise `articlesHtml()` pour que chaque citation devienne le lien déjà utilisé
ailleurs vers `/api/constitution?article=N`, et liste sous `#reglages-corps` chaque réglage déplacé
avec ses badges de catégories. Le harnais Node contrôle les six points (18 lignes hors réglage,
`289 → 231`, un lien `article=49`), et `tests/test_interface_navigateur.py` refuse un `index.html` qui ne serait pas la page courante,
en déléguant à `outils/generer-index-simulateur.py --verifier` — le même contrôle que celui de la
liste des générateurs, pas une copie de la logique du générateur dans un test. La leçon mérite d'être
écrite : régénérer la page à la main par `open(…).write(HTML_PAGE)` laisse le placeholder
`===SCENARIOS_JSON===` en place, et le fichier obtenu, pourtant « identique à `HTML_PAGE` », ne vaut
plus rien hors ligne.

---

## 5. Le protocole de relance

Pour rejouer l'audit complet après n'importe quelle modification :

```bash
# 1. les invariants de croisement et la fraîcheur des documents générés
python3 -m unittest tests.test_plan_global_croisements -v

# 2. toute la suite (~1 minute)
python3 -m unittest discover -s tests -p "test_*.py"

# 3. régénérer ce qui est produit, puis contrôler qu'il ne reste aucun écart
python3 outils/generer-doc-nuances.py
python3 outils/generer-page-verification.py
python3 outils/generer-index-simulateur.py
python3 outils/generer-fonctions-api.py --verifier
python3 outils/apercu_social.py
git diff --stat            # doit être vide si la doc, les routes et la page suivaient
```

Écrire un nouveau réglage demande cinq lignes de plus, pas cinquante : une entrée dans `REGLAGES`,
une dans `APPORTS`, un `Levier` dont `articles` cite le bon numéro, la règle dans `applicables` si
il déplace un nombre — et le test de garde-fous refuse toute autre combinaison (réglage sans
article, verrou oublié, exemption périmée, strate non couverte).

---

## 6. Ce que cette page ne prétend pas

Elle ne prétend pas que le modèle est juste : elle prétend qu'il n'a **pas d'angle mort non dit**.
Un chiffre faux reste possible — il est alors traçable à la règle qui l'a produit dans
`simulateur/nuances_institutionnelles.py`, et c'est là qu'il faut le corriger, jamais dans un
document. Les prédictions restent des écarts de modèle sur des hypothèses affichées ; la fenêtre de
150 jours, l'effectif de 925 au Congrès et le taux de participation de 80 % pour la censure sont
des hypothèses, pas des constats, et elles sont nommées à chaque fois qu'elles entrent dans un
calcul.
