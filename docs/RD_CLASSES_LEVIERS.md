# R&D — Les 5 classes de leviers : lire un budget d'un coup d'œil (12 octobre 2026)

## Objectif et statut

Le simulateur expose **156 leviers croisables** rangés en 14 familles
thématiques (fiscalité, santé, régalien, institutions…). Ce classement répond
à « dans quel domaine j'agis ». Il ne répond pas à la question que se pose un
citoyen devant un budget : **est-ce que ça fait entrer de l'argent, est-ce que
ça évite une dépense, ou est-ce que ça en engage ?**

Cette R&D ajoute cette lecture, et une seule : cinq classes de leviers, un
vocabulaire visuel fermé, et une balance qui pèse ce qui entre contre ce qui
sort. Statut : **actif** — le classement, la page, les totaux du moteur et
leurs tests sont exécutés par la suite du dépôt.

Ce que ce travail **ne fait pas** : il ne modifie aucune équation, aucun seuil,
aucune donnée source, aucun score de domaine. Il ajoute une colonne de lecture
au-dessus du moteur, et cette colonne est calculée à partir du catalogue et des
flux — jamais saisie à la main.

---

## Les cinq classes, et la règle qui les produit

| Classe | Symbole | Couleur M.R.S.C. | Motif de fond | Sens budgétaire |
|---|---|---|---|---|
| **Recettes nouvelles** | `+` | vert `#9bc77a` | uni | fait entrer de l'argent |
| **Économies d'efficacité** | `✂` | vert `#9bc77a` | hachuré | évite une sortie d'argent |
| **Dépenses et investissements** | `−` | rouge `#ff9295` | uni | engage de l'argent |
| **Règles du jeu** | `§` | bleu `#91b2e6` | pointillé | ne figure sur aucun compte |
| **Monde subi** | `≈` | or `#f2c15f` | hachuré | ne se décide pas ici |

Deux règles de lisibilité, héritées de la charte M.R.S.C. et vérifiées par les
tests (`tests/test_classes_leviers.py`) :

1. **La couleur ne porte jamais seule l'information.** Chaque classe fournit
   avec sa teinte un symbole, un libellé en toutes lettres et un motif de
   fond ; recettes et économies partagent le vert mais pas le motif. La page
   reste donc lisible en niveaux de gris, à l'impression, en contraste
   renforcé, en couleurs forcées et pour les daltonismes.
2. **Aucune teinte étrangère à la charte.** La palette est limitée aux quatre
   accents que le site applique déjà à la page intégrée (vert `#9bc77a`, rouge
   `#ff9295`, bleu `#91b2e6`, or `#f2c15f`) ; le test refuse toute autre
   valeur.

### La règle de classement, dans l'ordre où le code l'applique

`simulateur/classes_leviers.py` ne devine rien : il lit le catalogue
(`ligne` budgétaire, `champ` moteur, famille, type de levier) et applique les
règles suivantes, dans cet ordre :

1. **affectation documentée** si le levier figure dans la table des cas
   limites (voir ci-dessous) ;
2. famille « Chocs mondiaux (exogènes) » → **monde** ;
3. ni ligne budgétaire ni champ moteur → **règles** (ce sont exactement les 55
   réglages institutionnels lus par `simulateur/nuances_institutionnelles.py`) ;
4. interrupteur-drapeau (interrupteur, facteur 1,0, champ sans `_mde`) →
   **règles** ;
5. famille fiscalité (ménages, entreprises) → **recettes** ;
6. le reste → **dépenses**.

Répartition obtenue, vérifiée par `verifier_classes()` (liste vide = aucune
anomalie) :

| Classe | Leviers | Familles d'origine |
|---|---:|---:|
| Recettes nouvelles | 15 | 3 |
| Économies d'efficacité | 3 | 2 |
| Dépenses et investissements | 60 | 12 |
| Règles du jeu | 65 | 5 |
| Monde subi | 13 | 1 |
| **Total** | **156** | **14** |

### Les cas limites, écrits et motivés un par un

Le classement automatique se tromperait sur neuf leviers. Chacun a une
affectation **écrite**, motivée, et le motif est affiché par l'interface —
rien n'est classé en secret :

| Levier | Classe retenue | Pourquoi |
|---|---|---|
| `tva_energie_5_5` | dépenses | baisse de TVA : manque à gagner pour l'État, gain pour les ménages |
| `cheque_energie` | dépenses | classé en famille fiscalité, mais c'est un transfert versé (≈ 150 €, ≈ 5,7 M de bénéficiaires au catalogue) |
| `flat_tax_suppression` | dépenses | facteur −4 : la mesure coûte en régime transitoire |
| `taxe_comportements` | recettes | famille « santé » (but sanitaire), ligne budgétaire de recette (accises) |
| `fusion_doublons` | économies | +8 Md€/an d'économies de structure (dossier de mandature, volet 3) |
| `commande_publique` | économies | 200 Md€ d'achats, 3 % de gain négocié = +6 Md€/an (volet 3) |
| `simplification` | économies | charge en moins pour l'administration et les entreprises |
| `usage_49_3` | règles | le curseur compte des recours par an, pas des milliards |
| `charge_reformes_simultanees` | règles | nombre de chantiers menés de front (0 à 16), pas un montant |

Une affectation qui **ne corrigerait rien** (classe identique à la règle
générale) est refusée par le contrôle interne : une exception inutile laisse
croire à un arbitrage là où le catalogue suffisait.

---

## La balance, et les deux lectures du budget

La section « Les 5 classes de leviers » de la page affiche une balance à deux
plateaux — ce qui entre (recettes + économies) contre ce qui sort (dépenses) —
et un solde. Elle affiche **aussi** le compte du moteur, sans le masquer, car
les deux lectures ne coïncident pas et l'écart s'explique par trois causes
nommées :

1. une **baisse de prélèvements** compte comme une recette nouvelle dans le
   constructeur de flux alors qu'elle coûte ;
2. une **économie d'efficacité** compte comme une dépense nouvelle alors
   qu'elle rapporte ;
3. les **drapeaux 0/1** (réformes institutionnelles) comptent comme des
   dépenses alors qu'ils ne portent aucun euro.

Résultats réellement exécutés sur le préréglage de mandature, année 4 :

| Lecture | Chiffre |
|---|---:|
| Recettes nouvelles (classe) | +49,10 Md€/an |
| Économies d'efficacité (classe) | +11,50 Md€/an |
| Dépenses et investissements (classe) | −9,00 Md€/an |
| **Solde des classes** | **+51,60 Md€/an** |
| Recettes nouvelles (moteur) | +58,10 Md€/an |
| Dépenses nouvelles (moteur) | +16,50 Md€/an |
| **Solde du moteur** | **+41,60 Md€/an** |
| Unités hors budget (règles) | 5,00 (dont aucun euro) |

### Le signe est conservé, jamais remplacé par une valeur absolue

Découverte de cette R&D : le préréglage « austérité » **baisse** les budgets
(`dgf_delta = −12`, `budget_education = −6`…). Les montants de la classe
« dépenses » y sont donc **négatifs** (−31,90 Md€/an) et le solde positif
(+31,90 Md€/an). Une valeur absolue aurait fait passer une coupe de 31,9 Md€
pour une dépense de 31,9 Md€ : exactement le contresens que ce classement
existe pour éviter. Le module expose donc, pour chaque classe, le montant
**signé** et le montant **absolu** — le second mesurant le volume remué sans
prétendre à un solde.

Un test dédié protège ce cas : `test_un_plan_de_coupes_ne_passe_pas_pour_un_plan_de_depenses`.

---

## Ce que la page en fait

* **Grille des leviers** : chaque carte porte sa classe en fond (teinte douce),
  en bordure gauche (filet coloré), en pastille (symbole + libellé court) et en
  motif de fond ; les familles qui ne portent qu'une classe en héritent la
  teinte, celles qui en portent plusieurs affichent leurs pastilles côte à
  côte au lieu de cacher la diversité.
* **Filtres** : une légende cliquable et une barre de filtres permettent de ne
  voir que les leviers d'une classe ; le bouton « Mes leviers seulement »
  restreint la grille aux leviers effectivement déplacés.
* **Fiche par levier** : la classe, le motif du classement, la montée en charge
  déclarée au catalogue (cinq barres) et, quand le levier porte un montant, un
  ordre de grandeur **en euros par ménage et par an** — avec son diviseur
  affiché et son statut (« ordre de grandeur à vérifier », diviseur ≈ 30
  millions de ménages). Pour les classes « règles » et « monde », aucune
  conversion en euros n'est faite : un drapeau 0/1 ou un dollar de baril ne se
  convertit pas en euros par ménage, et la fiche liste les unités réelles
  (libellé + valeur + unité du catalogue) au lieu de les additionner.
* **Balance** : les deux plateaux, un solde signé, la comparaison avec la
  trajectoire de référence (leviers neutres, donc plateaux à zéro : tout ce qui
  est pesé est l'effet du plan), les deux lectures du moteur, et le détail des
  trois causes d'écart.
* **Cascade du plan** : sous la balance, un escalier sur un axe unique. Chaque
  classe part du cumul laissé par la précédente et le déplace de sa
  contribution — les recettes et les économies l'augmentent, les dépenses le
  diminuent ; une **coupe** (montant négatif dans « dépenses », cas du
  préréglage d'austérité) le fait **remonter**, et la marche l'annonce en
  toutes lettres. La dernière marche est le solde, calculé par la même règle
  que le module (`entrées − sorties`) : la cascade se referme donc exactement
  sur le chiffre de la balance, et le test navigateur vérifie cette égalité sur
  trois plans différents (préréglage de mandature, austérité, retour au
  neutre). Chaque marche nomme les leviers qui la déplacent (montant signé de
  chacun) — le total dit combien, les puces disent par qui. Les unités hors
  budget restent dehors, nommées une à une sous l'escalier.

  Sur le préréglage de mandature, la cascade se lit d'un trait :
  `+49,10` (recettes) `+11,50` (économies) `−9,00` (dépenses) `= +51,60` Md€/an.
  Sur l'austérité : `+31,90` de coupes viennent **augmenter** le cumul — c'est
  précisément ce qu'un tableau de dépenses ne montre pas.
* **Rythme du plan** : un sélecteur d'année (`‹ an précédent` / `an suivant ›`)
  relit toute la section — balance, cascade, cinq cartes — à l'année choisie,
  **sans relancer la simulation** (le moteur a livré les cinq années d'un coup).
  Une phrase chiffrée dit ce que le plan met de temps à produire :
  l'an 1 porte 19 % du solde de l'an 5 sur le préréglage de mandature
  (`+9,8` contre `+51,6` Md€/an). Quand la comparaison n'a pas de sens — solde
  final nul, ou de signe opposé à celui de l'an 1 — elle n'est pas faite et la
  page le dit, plutôt que d'afficher un pourcentage trompeur.
* **Info-bulles** : la classe et son motif sont ajoutés à la bulle explicative
  existante de chaque levier ; la page n'explique rien qu'elle n'affiche
  ailleurs.

Le calcul des totaux par classe vit dans `simulateur/classes_leviers.py` et
voyage avec chaque simulation (`classes_annuelles`, `classes_reference` de
`SortieSimulation`) : la page n'additionne aucun montant elle-même, elle
affiche la lecture du moteur, exactement comme pour les autres résultats.

Le catalogue le dit lui-même : chaque classe part avec un drapeau `monetaire`
(déduit de `CLASSES_MONETAIRES`, jamais recopié dans la page) et chaque levier
avec sa classe et le motif de son classement. La page n'a donc rien à deviner —
ni quelle classe porte des euros, ni à quelle classe appartient un levier.

Dernier point de méthode, pour l'intégration au site : **aucune teinte de
classe n'est écrite en dur dans une règle de style**. Les couleurs sont
déclarées une seule fois (variables `--classe-*`, teintes de fond comprises) et
lues par variable ; les deux plateaux de la balance recalculent même leur teinte
à l'usage avec `color-mix(in srgb, var(--classe-recettes|depenses) 14%,
transparent)`, avec un repli écrit pour les navigateurs qui ne connaissent pas
`color-mix`. Conséquence : quand la page est reprise par le site M.R.S.C., dont
la feuille surcharge la palette (`CSS_RETOUR` de
`outils/construire-simulateur.py`), les classes suivent la palette du site au
lieu de rester accrochées à l'ancienne. Un test lit la région CSS des classes,
retire les usages de variables et vérifie qu'il ne reste que des voiles neutres
(blanc/noir) — c'est-à-dire qu'aucune teinte d'identité ne s'y cache.

---

## Protocole reproductible

```bash
python3 -c "from simulateur.classes_leviers import verifier_classes; print(verifier_classes())"
python3 -c "
from simulateur.parametres import PRESETS
from simulateur.domaines import construire_flux
from simulateur.classes_leviers import totaux_classe
print(totaux_classe(construire_flux(PRESETS['mandature']['parametres'], 4))['solde_mde'])"
python3 -m unittest tests.test_classes_leviers -v
python3 outils/generer-index-simulateur.py --verifier
python3 -m unittest discover -s tests -p "test_*.py"
```

---

## Limites assumées

* **Le diviseur de ménages (≈ 30 millions) est un ordre de grandeur**, pas un
  chiffre vérifié à la source dans cette session : la page l'affiche avec ce
  statut, et le dépôt garde sa règle (un chiffre non vérifié se présente comme
  tel).
* **Les unités des classes « règles » et « monde » ne sont pas des euros** :
  elles ne sont ni additionnées entre elles ni fondues dans le solde. Le total
  « hors budget » mesure l'écart introduit par le constructeur de flux, pas une
  grandeur économique.
* **Le classement est un choix éditorial explicite** sur neuf leviers. Il est
  documenté, motivé et affiché ; il n'est pas déduit d'une opinion, mais il ne
  prétend pas être la seule lecture possible — un lecteur qui n'est pas
  d'accord peut lire le motif et le contester pièce par pièce.
* **La balance ne remplace pas le diagnostic du moteur** (déficit, dette,
  garde-fous) : elle répond à « qu'est-ce que ce plan fait entrer et sortir »,
  pas à « est-ce tenable ». Les deux sections restent côte à côte.
