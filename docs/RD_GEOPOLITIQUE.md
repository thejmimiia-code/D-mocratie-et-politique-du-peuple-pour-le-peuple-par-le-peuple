# R&D géopolitique — prototype exécuté, version 1

**3 octobre 2026 · Statut : modèle exploratoire non calibré, non prédictif.**

> Ce document conserve le protocole et les résultats de la **version 1**.
> La [deuxième phase d'audit](AUDIT_LACUNES_GEOPOLITIQUES.md) ajoute la reconstitution
> des stocks, une reprise économique optionnelle, un calendrier strict et un plan
> factoriel indépendant. Les paramètres par défaut conservent les résultats v1.

## Ce qui est livré

Le module `simulateur/geopolitique.py` ajoute un moteur mensuel distinct :

- graphe orienté d'alliances avec délai et autorisation politique explicite ;
- flux physiques sectoriels, stocks, fermeture de route et substitution retardée ;
- indice conventionnel de tension avec mémoire, médiation et seuils de posture ;
- branche d'emploi nucléaire **imposée**, qui arrête la projection hors validité ;
- raccordement des pénuries au PIB et aux recettes du moteur macro existant ;
- témoins appariés et analyses de sensibilité, avec journal des entrées et résultats.

Ce travail met en œuvre une première phase du plan du
[dossier prospectif](CONFLITS_RISQUES_SYSTEMIQUES_2026.md). Il ne transforme pas
encore le dépôt en prédicteur géopolitique validé. Les dates de guerre, choix réels
des dirigeants, bilans humains, probabilités nucléaires et qualifications juridiques
ne sont pas calculés.

## Reproduire

```bash
python -m simulateur.geopolitique --sortie rd-resultats-geopolitique.json
python -m unittest discover -s tests -p 'test_*.py'
```

Python standard uniquement. Le JSON détaillé est ignoré par Git mais reste
consultable dans l'espace de travail. Il contient les cinq cas détaillés, les
hypothèses et deux grilles de sensibilité. Aucun tirage aléatoire : mêmes entrées
et même code donnent les mêmes résultats. Les mois sont **relatifs**, sans date
calendaire cachée ni correspondance avec un pays réel.

L'API Python permet d'utiliser ses propres acteurs, alliances, secteurs et
événements. La CLI lance le protocole fourni, pas un moteur de prévision en direct.

## 1. Ce qui est imposé et ce qui est calculé

| Entrées imposées au scénario | Conséquences calculées |
|---|---|
| Combats orientés (agresseur, cible) de chaque mois | Intervention d'un protecteur éligible |
| Autorisations politiques d'intervenir | Confrontation directe impliquant deux acteurs nucléaires |
| Intensité du blocus de la route commune | Flux livrés, stock restant, demande non satisfaite |
| Rupture du dialogue et médiation | Indice de tension et franchissement de seuil heuristique |
| Éventuel mois d'emploi nucléaire | Arrêt explicite du domaine de calcul |
| Paramètres physiques et coefficient économique | Activité et sorties macro par rapport au témoin |

Un mois absent du calendrier signifie **absence de combat et de blocus ce mois**,
pas reconduction implicite de l'événement précédent. Les stocks et la tension,
eux, gardent la mémoire de leur état.

Le blocus, les combats et la rupture du dialogue sont synchronisés par le scénario
commun : leur dépendance est **supposée**, pas estimée statistiquement. La tension
ne choisit ni le blocus ni une décision militaire. Le couplage est à sens unique :
scénario → géopolitique/logistique → économie. Pas de rétroaction économique vers
les décisions de guerre dans cette version.

## 2. Alliances conditionnelles

Une alliance `Alliance(protecteur, protege, delai_mois)` est orientée. Le protecteur
intervient contre l'agresseur seulement si :

1. le protégé est attaqué dans les combats **imposés** du mois ;
2. le nombre de mois consécutifs d'attaque dépasse le délai ;
3. une autorisation explicite du protecteur figure dans le scénario du mois.

Ainsi, un délai de 1 signifie une première intervention possible au deuxième mois
consécutif. Une accalmie remet le compteur à zéro. L'autorisation doit être renouvelée
chaque mois. Les interventions ne déclenchent pas récursivement toutes les alliances
dans le même pas de temps. Les pactes ne sont donc pas traités comme des déclarations
automatiques de guerre. Soutien non combattant, négociation entre alliés, engagements
contradictoires et budgets militaires ne sont pas encore modélisés.

## 3. Blocus : conservation physique

Pour un secteur, à chaque mois :

- `D` : demande, en unités physiques normalisées par mois ;
- `i` : part importée ; `e` : exposition à la route ; `b` : fraction fermée ;
- flux bloqué `B = D × i × e × b` ;
- flux de substitution `R = B × s` après le délai de blocus consécutif, sinon zéro ;
- approvisionnement `A = D − B + R` ;
- service `Q = min(D, stock_initial + A)` ;
- pénurie `U = D − Q` ;
- stock final : disponible restant, plafonné à la capacité ; surplus enregistré.

Identités testées :

```text
stock_initial + approvisionnement = servi + stock_final + excedent
demande = servi + penurie
```

La substitution récupère une fraction du flux perdu, elle ne crée pas une seconde
fois les mêmes importations. Elle cesse avec le blocus. Son délai est remis à zéro
après une interruption. Le stock initial et la capacité correspondent au même nombre
de mois de demande. **Il n'y a pas de reconstitution des stocks après la crise** :
l'offre normale égale la demande. Cette limite doit être levée avant de simuler
sérieusement une succession de crises avec reconstitution stratégique.

Le modèle représente une route agrégée commune, pas un réseau maritime détaillé.
Il ne connaît ni ports réels, ni distances, ni prix d'assurance, ni substituabilité
entre secteurs, ni priorités de rationnement, ni mortalité.

## 4. Escalade nucléaire : posture heuristique, jamais probabilité

Soit `C = 1` lorsqu'un combat imposé ou une intervention calculée oppose directement
deux acteurs déclarés nucléaires. L'indice est :

```text
T[m] = borner(0, 100,
    mémoire × T[m−1]
    + poids_confrontation × C
    + poids_rupture × rupture_dialogue
    − poids_mediation × mediation)
```

Valeurs par défaut arbitraires : mémoire 0,75 ; poids 25 / 15 / 20 ; seuils
signal 25 et alerte 60. Sous le premier seuil : veille. La rupture seule peut faire
monter l'indice : il s'agit d'une **tension conventionnelle globale** et non d'une
estimation d'intention nucléaire. La catégorie d'alerte ne mesure ni état réel de
forces stratégiques, ni compte à rebours, ni probabilité d'emploi.

La mémoire permet une diminution après la fin des hostilités ; la médiation peut
réduire l'indice sans faire disparaître des combats imposés. Les coefficients sont
**des conventions testables, non des faits géopolitiques**.

`emploi_nucleaire=True` ouvre une branche imposée et arrête la simulation **avant**
les calculs de ce mois. Aucun score ne déclenche automatiquement cet événement.
Seules les années macro entièrement terminées avant l'arrêt sont publiées : pas
de PIB post-emploi inventé. Cela modélise une frontière de validité, pas les effets
d'une explosion, d'un échange ou d'un hiver nucléaire.

## 5. Pont macroéconomique et anomalie découverte

Le moteur existant calcule le PIB tendanciel à partir d'une base fixe et d'une
puissance du taux de croissance. Un premier test a montré que modifier ce taux
chaque année effaçait le dommage au retour à la normale, et n'affectait pas le PIB
de la première année (exposant zéro).

Correction **locale au raccordement R&D**, sans réécrire les équations historiques :
`MoteurSimulationSystemique.appliquer_etape` accepte désormais le paramètre nommé
optionnel `facteur_activite=1.0`. Il multiplie le PIB tendanciel avant les
multiplicateurs existants et son indexation des recettes. La valeur par défaut
conserve le comportement antérieur ; les anciennes simulations ne changent pas.

Pour chaque année complète :

```text
u = moyenne mensuelle de Σ(poids_sectoriel × pénurie / demande)
facteur_annuel_cumulé = facteur_précédent × (1 − élasticité × u)
PIB tendanciel exposé = PIB tendanciel de référence × facteur_annuel_cumulé
```

L'élasticité par défaut est 0,04. Les poids sectoriels somment à 1. À pénurie totale
sur douze mois, le facteur est donc multiplié par 0,96. Ce choix suppose une perte
d'activité persistante, **sans rattrapage automatique** ; ce n'est pas une estimation
empirique de destruction de capital. Les effets multiplicateurs déjà présents dans
le moteur restent appliqués ensuite.

Deux moteurs neufs appliquent les mêmes décisions de statu quo. Aucune hausse
supplémentaire de pétrole, change ou taux n'est ajoutée par le pont, pour ne pas
compter deux fois une même perturbation. Le moteur macro conserve toutefois ses
propres hypothèses de base et ses indicateurs politiques heuristiques : ceux-ci
ne deviennent pas des probabilités validées grâce à ce raccordement.

## 6. Expériences réellement exécutées

### Cas central fictif

Trois acteurs A, B, C ; A et C nucléaires. A attaque B pendant 18 mois ; C protège
B avec un mois de délai et reçoit les autorisations. Fermeture de route de 80 %,
rupture du dialogue pendant la crise. Horizon 36 mois.

| Paramètre | Énergie | Composants |
|---|---:|---:|
| Demande mensuelle normalisée | 100 | 100 |
| Part importée | 60 % | 80 % |
| Exposition à la route | 80 % | 90 % |
| Stock initial / capacité | 1 mois | 1 mois |
| Fraction des pertes récupérable | 25 % | 25 % |
| Délai avant substitution | 3 mois | 3 mois |
| Poids économique conventionnel | 60 % | 40 % |

### Résultats des cinq cas

| Cas | Intervention calculée | Première alerte heuristique | Mois avec pénurie | Écart de PIB en année 3 vs témoin |
|---|---:|---:|---:|---:|
| Témoin sans crise | aucune | aucune | 0 | 0 Md€ |
| Crise centrale | mois 2 | mois 3 | 17 | −57,84 Md€ |
| Même crise + médiation, sans rupture du dialogue | mois 2 | aucune | 17 | −57,84 Md€ |
| Même crise sans autorisation d'intervenir | aucune | aucune | 17 | −57,84 Md€ |
| Emploi nucléaire imposé au mois 8 | mois 2 | mois 3 | 6 avant arrêt | non calculé |

**Ces nombres décrivent des expériences synthétiques, pas la France future.**
Le test de médiation change deux entrées — ajout de médiation et retrait de rupture —
et ne permet donc pas d'isoler causalement le seul effet de la médiation.
La même pénurie dans trois cas est attendue : le blocus y est identique et le
modèle n'invente pas qu'une médiation rouvre automatiquement une route.

### Sensibilité exécutée

**81 combinaisons physiques/économiques** : durée 6/18/30 mois × stocks 0/1/3 mois ×
substitution 0/25/75 % × élasticité 0,02/0,04/0,08.

- Écart de PIB en année 3 : de **−280,09 à 0 Md€** dans cette grille.
- Pénurie pondérée cumulée : de **0 à 13,824 mois de demande**.
- Ces extrêmes ne sont ni un intervalle de confiance ni des bornes de risque réel.

**27 combinaisons d'escalade**, scénario central inchangé : mémoire 0,5/0,75/0,9 ×
poids de confrontation 10/25/40 × seuil d'alerte 40/60/80.

- Première alerte selon les conventions : mois **2, 3, 4, 5 ou 7**.
- Dans **3 configurations sur 27**, aucune alerte.
- Ces fréquences ne sont pas des probabilités ; elles montrent pourquoi un mois
  d'alerte ne doit surtout pas être transformé en date prédite de guerre.

Total : **113 trajectoires géopolitiques** (5 cas + 81 + 27).

### Vérification logicielle

**54 tests réussis**, dont 16 nouveaux tests. Ils couvrent notamment :
conservation des flux, délai de substitution, cas de blocus total, neutralité du
témoin, autorisation et délai d'alliance, absence de contagion récursive, médiation,
désescalade, reproductibilité, bornes et valeurs non finies, arrêt nucléaire,
sensibilité économique, effet dès la première année et persistance après crise.

Ce sont des tests d'implémentation et de cohérence, **pas une validation historique**.

## 7. Conditions avant d'employer le mot « prédicteur »

1. Définir une cible observable : par exemple entrée directe d'un nouvel acteur
   dans un conflit sur un horizon donné, plutôt que « troisième guerre mondiale »
   sans définition stable. Définir aussi ce qui compte comme une non-occurrence.
2. Construire un jeu d'événements datés avec provenance, date de disponibilité,
   incertitudes d'attribution et cas sans escalade. Aucune donnée ne doit être
   connue avant sa disponibilité réelle dans un test rétrospectif.
3. Calibrer séparément les flux/élasticités et les transitions politiques ; publier
   les désaccords d'experts au lieu de les masquer par une moyenne.
4. Valider chronologiquement hors échantillon, contre des références simples ;
   mesurer fausses alertes, événements manqués et calibration. Si des probabilités
   sont estimées, publier Brier/log-loss et leur incertitude, sans extrapolation
   mécanique à l'emploi nucléaire, extrêmement rare et hors distribution.
5. Introduire routes multiples, reconstitution des stocks, délais de rétablissement,
   aide non combattante et rétroactions ; tester leur valeur ajoutée avant complexification.
6. Conserver une sortie « données insuffisantes / hors validité » et un journal
   des révisions. Des tests unitaires réussis ne remplacent aucun de ces critères.

**Non réalisé dans cette phase :** collecte/calibration historique, prévision
probabiliste, simulation des dommages nucléaires, réseau logistique réel,
modélisation de décisions autonomes de dirigeants, couverture de tous les conflits.
Aucune prétention de première mondiale ni de résultat géopolitique certain.
