# R&D — Prospective : jusqu'où porte l'horizon, et ce qu'il rencontre

**Passe du 16 octobre 2026.** Ce document raconte comment le simulateur, qui sait
dire « voici l'an 5 » et « voici l'an 10 », a appris à dire **ce que cet horizon
rencontre** — sans transformer une fenêtre de veille en prévision, ni un indice
en probabilité.

---

## 1. Le constat : trois documents portaient un morceau d'avenir, aucun ne parlait

Le dépôt avait déjà tout, mais séparé :

- `docs/CONFLITS_RISQUES_SYSTEMIQUES_2026.md`, **§ 7**, écrit **quatre fenêtres de
  veille** à partir du 3 octobre 2026, avec une phrase qui engage : « des horizons,
  pas des dates de guerre » ;
- `docs/AUDIT_LACUNES_GEOPOLITIQUES.md` tient le **registre des lacunes** qui
  bloquent toute revendication prédictive — six P0, le reste en P1/P2 — avec, pour
  chacune, le critère qui la fermerait ;
- `docs/RD_VALIDATION_TEMPORELLE.md` donne le **protocole** d'évaluation : ce qui
  était disponible à une date, découpage chronologique gelé, fréquence de base,
  compétence.

Et le moteur, de son côté, simule **cinq ou dix ans** à partir du jour où l'on
ouvre la page. Aucun lien n'existait entre les deux : la page offrait un select
d'horizon qui ne disait rien de ce qui tombe dedans. Un lecteur pouvait croire
que « 10 ans » était une profondeur de champ ; c'est une **durée de calcul**.

## 2. La décision : trois règles

1. **Une fenêtre documentée porte sa source.** Le module ne réécrit pas le
   document, il le **cite** — extrait, section. Le texte des scénarios, des
   signaux et des critères est celui du document, au mot près, et un contrôle le
   vérifie lettre par lettre.
2. **Une borne imprécise se dit imprécise.** Le document date ses fenêtres au
   **mois** (« octobre 2031 ») quand le modèle calcule au **jour**. Le croisement
   publie donc sa marge en jours et l'annonce (`a_un_mois_pres`) quand le verdict
   tient à cette imprécision : « couverte à quinze jours près » n'est pas
   « couverte », et le lecteur a le droit de le savoir.
3. **Un statut de lacune ne se décide pas dans le code.** Le module **déclare**
   ce que dit le document. Un contrôle refuse qu'il s'attribue une guérison que
   l'audit n'a pas écrite, et refuse aussi que l'audit ferme une lacune que le
   code dit encore ouverte. Le code propose, le document daté dispose.

## 3. Les quatre fenêtres, telles que le document les écrit

| Clé | Bornes | Précision | Ce que la fenêtre est |
|---|---|---|---|
| `incident_majeur` | 3 octobre 2026 → 3 avril 2027 | jour / jour | Incident majeur dans un théâtre déjà tendu, extension régionale en jeu |
| `crises_simultanees` | avril 2027 → octobre 2028 | mois / mois | Deux crises simultanées compliquent la médiation et les engagements |
| `fragmentation_prolongee` | octobre 2028 → octobre 2031 | mois / mois | Fragmentation et confrontation prolongée, éventuellement multi-théâtre |
| `ordres_suivants` | novembre 2031 → **sans fin datée** | mois / aucune | Plusieurs ordres internationaux possibles, dont stabilisation |

Deux données de calendrier viennent du document et non du code : le **point de
départ** (3 octobre 2026) et le **pas d'imprécision** (un mois = 31 jours, la
borne la plus large — le module ne s'accorde pas le bénéfice du doute).

## 4. Le croisement, mesuré au 16 octobre 2026

Commande : `python3 -m simulateur.prospective` (le rapport s'ancre sur le jour ;
`--depart AAAA-MM-JJ` pour un autre départ, `--json` pour la donne brute).

| Fenêtre | Horizon 5 ans → 16 octobre 2031 | Horizon 10 ans → 16 octobre 2036 |
|---|---|---|
| `incident_majeur` | entièrement — fermée 1 657 j avant la fin | entièrement — 3 484 j |
| `crises_simultanees` | entièrement — 1 110 j | entièrement — 2 937 j |
| `fragmentation_prolongee` | entièrement — 15 j, **à un mois près** | entièrement — 1 842 j |
| `ordres_suivants` | **hors de l'horizon** — ouvre le 1ᵉʳ nov. 2031, 16 j après la fin | **partiellement** — le début tombe dedans, la fin n'est pas datée |

La conclusion que la page peut écrire sans mentir : **3 des 4 fenêtres de veille
documentées tombent entièrement dans l'horizon de 5 ans** — et la quatrième
s'ouvre juste après, ce qui n'est pas un détail : c'est la fenêtre sans fin datée.

## 5. Le registre des lacunes, tel que l'audit le tient

| Priorité | Lacune | Statut au 16 octobre 2026 | Preuve citée |
|---|---|---|---|
| P0 | Cible prédictive non définie | partiellement traitée | `simulateur/validation_temporelle.py` (`CIBLES`, `Observation`) |
| P0 | Aucun jeu historique calibré | **ouverte** | aucun jeu réel importé : le corpus est synthétique et le signale |
| P0 | Dates de disponibilité et révisions absentes | partiellement traitée | `validation_temporelle.py` (`preuve_disponibilite`, `disponibilite`) |
| P0 | Pas de cas négatifs / fréquence de base | partiellement traitée | `validation_temporelle.py` (`frequence_de_base`, `competence_brier`) |
| P0 | Absence de validation hors échantillon | partiellement traitée | `validation_temporelle.py` (`evaluer`) — corpus synthétique |
| P0 | Coûts économiques incomplets | **ouverte** | les proxys sont hors budget : ni financement ni acquisition |
| P1 | Indice nucléaire non calibré | **refermée le 15 octobre 2026** | `simulateur/seuils.py` (indices `/100`, non calibrés) |

Résumé publié par le module et affiché par la page : **2 ouvertes, 4 partiellement
traitées, 1 refermée — aucune revendication prédictive n'est permise tant qu'une
lacune P0 reste ouverte.** Le registre porte son propre avertissement : c'est un
**registre de dates**, pas de prévisions, et **aucune probabilité n'est calculée
ici**.

## 6. Ce que la page en montre

Un **septième bloc** dans l'audit — « Prospective : jusqu'où porte l'horizon, et
ce qu'il rencontre » —, replié comme les six autres, alimenté par la route
`/api/prospective` et **redessiné quand l'horizon change** (le select 5/10 ans
rapelle le rendu). Trois propriétés tenues par des contrôles :

- **aucune date en dur dans le bloc** : le rendu porte ce que le serveur a écrit.
  Une date de fin recalculée en JavaScript finirait par diverger de celle du
  serveur, et deux dates pour un même horizon, c'est une de trop ;
- **les libellés citent** : les fenêtres sont affichées avec leur document et leur
  section ; les recopier ici les ferait survivre à une révision du document qui
  les porte ;
- **une route muette laisse un aveu, pas un vide** : si `/api/prospective` ne
  répond pas, le bloc garde son titre et écrit « Registre de prospective
  indisponible », sans faire jeter le reste de l'audit — la pesée de la visite et
  les six autres blocs ne dépendent pas de la prospective.

## 7. La route

`GET /api/prospective` (`?depart=AAAA-MM-JJ`, facultatif) devient la **23ᵉ route
du moteur**, servie par le même routeur que les autres (`simulateur/dashboard.py`
pour le local, `api/[...path].py` pour Vercel, `simulateur/wsgi.py` pour tout
hébergeur Python). Mesures du jour, `gzip -6` :

| Mesure | Valeur |
|---|---:|
| réponse `200 OK` | **8 029 o** bruts |
| corps compressé | **2 439 o** |
| plafond écrit (`outils/budgets_fluidite.py`) | **2 683 o** |
| marge | 244 o |

Une date illisible (`?depart=hier`) **n'est pas devinée** : la route répond
`500` avec un message d'erreur, plutôt que de retomber en silence sur la date du
jour. Ce comportement-là a son contrôle, et il en a un parce qu'il a d'abord été
écrit faux dans le test (le statut servi est « 500 Internal Server Error », pas
« 500 »).

## 8. Les contrôles, et les sabotages qui les ont éprouvés

**38 contrôles** (`tests/test_prospective.py`), en cinq familles : le croisement
des horizons (13), la citation des documents (5), l'accord registre/document (5),
la route et la page (9), et **le bloc exécuté pour de vrai dans Node** (6) — le
fragment est celui de la page, la réponse est celle de la route, et ce qui est
vérifié est le HTML réellement fabriqué.

**16 sabotages, 16 attrapés.** Chaque sabotage applique une modification réelle au
code ou au document, exécute la suite, compte les rouges, puis restaure le fichier
— restauration vérifiée par empreinte SHA-256 des quatre fichiers touchés. Quatre
ont d'abord **passé inaperçus**, et aucun des quatre n'a été « réparé » en
affaiblissant la vérification :

1. **le seuil d'un verdict déplacé d'un jour** (`recul > 0` → `recul >= 0`) —
   muet parce qu'aucune fenêtre du document ne s'ouvre pile le dernier jour de
   l'horizon. Deux contrôles neufs tiennent désormais la **borne exacte** et son
   lendemain : un horizon qui se ferme le 16 ouvre ses dernières 24 heures ;
2. **une preuve citant un symbole tronqué** (`frequence_de_bas`) — mon contrôle
   cherchait par **sous-chaîne**, et un préfixe passait pour le symbole. Il exige
   maintenant une **frontière de mot** ;
3. **le plafond de la route retiré de la table** — la garde des plafonds mordait,
   mais mon script ne la jugeait pas : c'est le **verdict du sabotage** qui était
   faux, pas le contrôle ;
4. **l'ancre du plafond inventée** (2 439 → 3 000) — le contrôle documentaire
   acceptait qu'une ancre soit annoncée « quelque part » dans le document, et le
   nombre 3 000 pouvait venir d'un autre budget. Désormais **la ligne du tableau
   est le registre** : elle doit porter l'ancre, le plafond **et** la marge, liés
   sur une seule ligne.

La leçon des quatre est la même et vaut pour les passes suivantes : *un sabotage
qui ne mord pas n'accuse pas le sabotage, il accuse le contrôle.*

### Le défaut trouvé en relisant la greffe, avant de livrer

La cellule des bornes d'une fenêtre était un `td.chiffre` — donc insécable
(`.audit td.chiffre{white-space:nowrap}`) —, et pour la fenêtre **sans fin datée**
elle faisait **quarante signes** : « à partir du 2031-11-01, sans fin datée ».
Sur un téléphone, ce texte aurait été **coupé**, dans le bloc même dont le but est
d'être lu. C'est le défaut refusé à la passe précédente, qui revenait par une
porte que la passe précédente n'avait pas fermée : son contrôle lit le balisage
**écrit**, et ce HTML-là n'existe qu'au moment où le navigateur le fabrique.

Deux réparations, et la seconde compte plus que la première :

1. la borne s'écrit court — « début → sans fin datée », **27 signes** — et
   l'explication (« le document n'écrit aucune fin à cette fenêtre ») passe dans
   la colonne qui se **replie** ;
2. **six contrôles exécutent le bloc** dans Node, avec la réponse réelle de la
   route sous les deux horizons : ils comptent **onze cellules insécables**
   (quatre bornes, sept rangs de lacune) et refusent toute cellule de plus de
   **trente signes**. Le sabotage qui remet la phrase longue rougit les deux
   contrôles — le défaut ne reviendra pas en silence.

## 9. Limites assumées

- **Ce module ne prédit rien.** Il met en regard un horizon de calcul et des
  fenêtres **documentées** ; aucune ne se déduit du modèle, et le module l'écrit.
- **Les fenêtres vieillissent.** Elles sont datées d'un document daté : le jour où
  `CONFLITS_RISQUES_SYSTEMIQUES_2026.md` est révisé, un contrôle rouge le dit au
  lieu de laisser la page citer un texte qui n'existe plus.
- **Le registre est un état, pas un plan.** « 2 ouvertes, 4 partiellement
  traitées, 1 refermée » décrit ce que l'audit écrit au 16 octobre 2026 ; fermer
  une lacune P0 demande des données calibrées et une évaluation indépendante, pas
  une ligne de plus dans un fichier.
- **Les deux lacunes P0 restantes gardent leur conséquence** : tant qu'elles sont
  ouvertes, la seule lecture honnête du modèle reste celle du dépôt — un
  **explorateur d'hypothèses chiffrées**, pas un système de prévision.
