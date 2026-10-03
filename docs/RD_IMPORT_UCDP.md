# R&D v4 — adapter une source réelle sans inventer les observations

**3 octobre 2026 · Adaptateur `import-ged-26.1-v1` · Validation sur fixtures synthétiques uniquement.**

## 1. Bilan exact de cette phase

Livré et exécuté :

- vérification documentaire du périmètre, de la licence annoncée et des variables
  UCDP GED 26.1 ;
- adaptateur CSV local vers le registre mensuel, avec contrat de provenance ;
- cible UCDP distincte de la cible générale précédente ;
- gestion des dates ambiguës, doublons et mois sans enregistrement ;
- vérification que des données disponibles seulement en 2026 ne produisent pas
  artificiellement des prévisions historiques pour 2024.

**Non réalisé : téléchargement et analyse d'un corpus UCDP réel.** Les requêtes
HTTPS directes depuis le sandbox vers UCDP ont échoué lors de cette phase avec une
erreur TLS (`SSL_ERROR_SYSCALL` / `TLS/SSL connection has been closed`). La requête
au CSV Candidate par l'outil de lecture web a également échoué. En revanche, les
pages documentaires et les premières sections du codebook ont été consultées par
l'outil web. Cela permet de développer contre le schéma, pas de certifier la
compatibilité avec tous les enregistrements du fichier réel.

Aucune donnée observée n'a été remplacée par des données inventées. Le fichier de
test, ses résultats et son contrat portent tous la mention `synthetique`.

## 2. Découvertes documentaires qui changent le protocole

### Une source ouverte, mais un périmètre spécifique

Le centre de téléchargement UCDP annonce des données gratuites sous **CC BY 4.0**,
avec obligation de citer les publications associées. Cette annonce a été consultée ;
les notices accompagnant une archive réellement acquise devront aussi être conservées.
[1](https://ucdp.uu.se/downloads/)

Le codebook GED 26.1 décrit une couverture du 1er janvier 1989 au 31 décembre 2025.
Un événement correspond à une violence organisée létale : au moins un décès direct
dans l'une des estimations basse, centrale ou haute. Les trois types sont les
conflits étatiques, les conflits non étatiques et la violence unilatérale contre
des civils. Les événements peuvent être retenus hors des années dépassant le seuil
annuel de 25 morts dès lors que les critères d'inclusion des dyades sont satisfaits.
[1](https://ucdp.uu.se/downloads/ged/ged261.pdf)

**Conséquence de conception :** notre cible antérieure « affrontement organisé »
n'est pas interchangeable avec GED. La nouvelle cible est
`presence_evenement_letal_ucdp_v1` : présence mensuelle d'au moins un événement
retenu dans le snapshot GED fourni, dans le pays codé par la source. Les événements
de violence unilatérale ne sont pas supprimés. Ce n'est ni un décompte de toutes
les violences mondiales ni une mesure de « troisième guerre mondiale ».

### L'identifiant persistant est `id`

Le codebook recommande `id`, et non `relid`, pour identifier les événements entre
versions. Les estimations `low`, `best`, `high` sont distinctes. La date peut être
un intervalle : `date_start` / `date_end`, accompagné de `date_prec` (1 à 5).
[1](https://ucdp.uu.se/downloads/ged/ged261.pdf)

**Conséquence de conception :** les doublons sont traités par `id` ; aucun décès
n'est réparti artificiellement entre les mois d'un intervalle incertain.

### La date d'une dépêche n'est pas la disponibilité d'une version du jeu

La variable `source_date` désigne les dates des sources sous-jacentes ; le codebook
indique même une valeur par défaut `1753-01-01` lorsque cette date manque.
[1](https://ucdp.uu.se/downloads/ged/ged261.pdf)

**Conséquence de conception :** l'adaptateur n'utilise jamais `source_date` comme
date de publication, disponibilité ou ingestion du snapshot. Ces trois dates sont
renseignées dans un contrat explicite avec une référence de preuve. Une source
journalistique ancienne ne prouve pas que la codification révisée actuelle était
accessible à cette époque.

## 3. Fonctionnement de l'adaptateur

Module : `simulateur/import_ucdp.py`. Entrée : CSV local **déjà décompressé** et
contrat JSON. Aucun téléchargement réseau implicite, aucun token demandé, aucune
extraction d'archive non contrôlée. Le schéma annuel 26.1 est le seul déclaré pris
en charge ; le flux Candidate n'est pas assimilé au jeu annuel.

Champs CSV obligatoires :

```text
id, country, country_id, type_of_violence,
date_start, date_end, date_prec, low, best, high
```

Les autres colonnes sont acceptées mais ne deviennent pas des variables
prédictives. Les noms de pays ne servent pas de clés : la clé territoriale est
`UCDP_COUNTRY_<country_id>`. Le lieu enregistré est celui de l'événement, pas
nécessairement celui d'un acteur impliqué.

Contrôles :

- en-tête complet et non dupliqué, lecture CSV avec guillemets et BOM UTF-8 ;
- nombres entiers, type de violence 1/2/3, précision temporelle 1–5 ;
- intervalle ordonné dans la couverture 1989–2025 et date exacte cohérente ;
- `0 <= low <= best <= high`, avec `high >= 1` ;
- date au format ISO ou timestamp de minuit, sans troncature de texte arbitraire ;
- `id` répété à contenu strictement identique : ignoré et comptabilisé ;
- même `id`, contenu différent : arrêt pour arbitrage, pas choix silencieux ;
- validation également des lignes hors du périmètre demandé.

Ces contrôles sont volontairement stricts. Une anomalie éventuelle du vrai fichier
arrêtera l'import plutôt que d'être corrigée sans journal. L'exécution sur le jeu
complet reste nécessaire pour vérifier les cas particuliers non documentés.

## 4. Règles d'agrégation mensuelle

Chaque pays/mois demandé reçoit des listes d'identifiants et un motif auditable.

| Situation | Étiquette produite |
|---|---|
| Au moins un événement dont tout l'intervalle tient dans ce mois | `1` |
| Aucun événement précisément localisable dans le mois, mais intervalle traversant ce mois et un autre | `null` |
| Aucun enregistrement et exhaustivité non attestée | `null` |
| Aucun enregistrement ni intervalle ambigu, snapshot déclaré exhaustif pour le périmètre | `0` |

La première règle l'emporte : un événement bien localisé suffit à établir une
présence enregistrée, même si un autre est ambigu. « Certain » dans le journal
signifie **localisable dans un seul mois selon les dates encodées**, pas certitude
sur les décès, l'attribution ou l'exhaustivité de la violence réelle.

La comparaison porte sur l'intervalle original. Exemple : un événement de mars à
avril reste ambigu même si l'utilisateur ne sélectionne que mars. Le filtre ne
transforme pas une information incertaine en date précise.

Les identifiants d'un intervalle ambigu apparaissent dans plusieurs cellules pour
indiquer les mois possibles. **Il ne faut pas additionner ces occurrences comme
s'il s'agissait d'événements distincts.** Aucune somme de victimes n'est produite.

### La signification limitée d'un zéro

`couverture_exhaustive` vaut `false` par défaut. Pour l'activer, le contrat doit
inclure `preuve_exhaustivite`. Cela doit attester que le fichier contient toutes
les lignes du snapshot pertinentes pour le périmètre, et non une pagination ou
un extrait incomplet. La chaîne de preuve est obligatoire, mais le programme ne
vérifie pas automatiquement son authenticité.

Même avec cette attestation, zéro signifie **aucun enregistrement admissible dans
ce snapshot**, pas « aucune violence réelle ». Les biais de collecte et critères
GED restent présents. Le mot `complete` du registre décrit ici l'évaluabilité de
la cible relative au snapshot ; il ne certifie pas une observation complète du monde.

## 5. Contrat et traçabilité

Le contrat renseigne version, nature, source, licence, dates de publication,
disponibilité et ingestion, preuve de disponibilité, période, pays et éventuelle
preuve d'exhaustivité. La période doit être clôturée avant la publication déclarée.

Pour `nature=observee`, la licence attendue est `CC-BY-4.0` et la source doit être
HTTPS. Cela ne certifie ni le domaine ni le contenu : un opérateur doit vérifier
la provenance. Les fixtures emploient `synthetique`, une source `synthetic://` et
la licence MIT du dépôt, **jamais une fausse attribution de données à UCDP**.

Le rapport contient :

- empreinte SHA-256 du CSV brut, du module et du registre canonique ;
- contrat complet et compteurs d'import ;
- observations produites ;
- identifiants des événements justifiant chaque cellule et motif du résultat.

Les entrées et sorties ne peuvent pas désigner le même chemin. Les exports
`rd-resultats*.jsonl` et les archives sous `data/externe/` sont ignorés par Git.
L'importateur lit en flux mais garde en mémoire les empreintes des identifiants et
les lignées retenues : ce n'est pas encore une solution optimisée pour tous les
volumes. Le CSV n'est pas verrouillé pendant les deux passes de lecture ; il doit
rester immuable pendant l'import pour que l'empreinte corresponde au contenu traité.

Cette version produit une révision mensuelle numéro 1 pour **un seul snapshot**.
Fusionner plusieurs snapshots exigera une couche d'historisation et de retrait des
étiquettes : concaténer des imports actuels n'est pas cette couche. Le registre
refuse les révisions dupliquées plutôt que de prétendre avoir reconstruit le passé.

## 6. Expériences réellement exécutées

```bash
python -m simulateur.import_ucdp \
  --csv tests/fixtures/ged_schema_synthetique.csv \
  --contrat tests/fixtures/contrat_ged_synthetique.json
```

Fixture entièrement inventée : six lignes CSV, cinq identifiants uniques, dont
un hors périmètre, quatre retenus et un doublon exact ignoré. Les six cellules
mensuelles demandées produisent :

- **2 positives, 0 négative, 4 inconnues**, sans attestation d'exhaustivité ;
- **2 positives, 2 négatives, 2 inconnues**, avec attestation synthétique explicite.

Les deux mois ambigus restent inconnus même dans le deuxième cas. Le test contient
un événement de violence unilatérale et un intervalle débordant du filtre temporel.

### Test de non-antidatage

Les événements fictifs sont datés de 2024, mais leur snapshot est déclaré disponible
le 3 octobre 2026. Cette commande demande volontairement une évaluation historique
impossible avec les seules connaissances disponibles à l'époque :

```bash
python -m simulateur.validation_temporelle \
  --observations rd-resultats-observations-ucdp.jsonl \
  --debut 2024-01-01 --fin 2024-06-01 --evaluation-au 2026-10-03 \
  --unites UCDP_COUNTRY_101 --minimum 1 \
  --sortie rd-resultats-hindcast-garde-fou.json
```

Résultat : **6 abstentions, 0 prévision, scores non calculables (`null`)**.
C'est le comportement voulu. Antidater le snapshot pour obtenir un score serait
une fuite temporelle, pas un progrès scientifique.

Vérification de la suite complète : **97 tests réussis**, dont 14 nouveaux tests.
`ruff check .` réussi. Les tests couvrent provenance, arrondis non imputés,
intervalles, clés, retraits de périmètre, doublons, contrat, aller-retour JSONL et
protection contre la confusion de cibles.

## 7. Étape suivante et verrous restants

1. **Acquérir une archive officielle authentifiée**, conserver son codebook et ses
   notices, la stocker hors Git et enregistrer son empreinte.
2. Lancer l'adaptateur sur un petit périmètre annoncé avant analyse ; traiter les
   anomalies sans changer silencieusement la définition des étiquettes.
3. Vérifier un échantillon manuellement et documenter pourquoi le périmètre est
   exhaustif ou ne l'est pas. Ne pas inventer les mois négatifs.
4. Obtenir des **millésimes historiques réellement disponibles à chaque origine**,
   ou démarrer une collecte prospective et attendre les observations futures.
5. Si l'on choisit une analyse rétrospective à partir d'un seul snapshot révisé,
   la nommer ainsi et ne pas lui attribuer une validité prédictive prospective.

La calibration des mécanismes d'alliances, de blocus et d'escalade n'est pas réalisée.
Le registre ne résout ni les critères d'inclusion rétrospectifs, ni les biais de
couverture, ni les intentions non observables. Aucun résultat réel de performance
prédictive n'est revendiqué dans cette phase.

### Attribution documentaire à conserver lors d'un usage réel

Le codebook demande de citer : Sundberg, Ralph et Erik Melander (2013),
« Introducing the UCDP Georeferenced Event Dataset », *Journal of Peace Research*,
50(4), 523–532 ; et, lorsque pertinent, Högbladh, Stina (2026), *UCDP GED Codebook
version 26.1*, Department of Peace and Conflict Research, Uppsala University.
La version du jeu doit figurer dans les analyses.
[1](https://ucdp.uu.se/downloads/ged/ged261.pdf)
