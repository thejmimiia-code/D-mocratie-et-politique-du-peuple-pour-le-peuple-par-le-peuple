# R&D v3 — registre versionné et évaluation chronologique

**3 octobre 2026 · Protocole `validation-mensuelle-v1` · Données de démonstration synthétiques.**

## Résultat de cette phase

Cette phase traite une partie des lacunes P0 de l'[audit précédent](AUDIT_LACUNES_GEOPOLITIQUES.md) :
contrat d'observations mensuelles, import JSONL strict, millésimes disponibles à une
date donnée, abstention et comparaison chronologique de deux références simples.

**Aucun pays réel n'est évalué, aucune probabilité de guerre mondiale ou d'emploi
nucléaire n'est calculée.** Aucun modèle n'a été calibré sur des conflits réels.
L'indice de tension de `geopolitique.py` n'est pas converti en probabilité.

Fichiers livrés :

- `simulateur/validation_temporelle.py` : import, registre, références et évaluation ;
- `tests/fixtures/observations_synthetiques.jsonl` : 74 lignes, 72 cellules territoire/mois
  et deux révisions, toutes signalées `synthetique` ;
- `tests/test_validation_temporelle.py` : 17 tests supplémentaires.

Les expériences et équations géopolitiques antérieures restent inchangées.

## 1. Cible limitée, distincte d'une guerre mondiale

Identifiant : `presence_affrontement_organise_v1`.

Définition de travail : **au moins un affrontement armé documenté impliquant un
acteur armé organisé dans une unité territoriale et un mois donnés**. L'unité doit
être définie avant une étude réelle. La valeur 1 représente une présence, 0 une
absence selon le protocole d'observation, et `null` une couverture insuffisante.
Ce n'est ni le début d'une guerre, ni son intensité, ni son nombre de victimes,
ni une attribution de responsabilité juridique.

Dans la démonstration, les unités `FICTIF_A`, `FICTIF_B`, `FICTIF_C` et les valeurs
sont inventées. Elles testent le logiciel, pas cette définition sur le terrain.
Pour des données réelles, il faudra un guide de codage et un adaptateur propre à
chaque fournisseur : ce module ne prétend pas agréger correctement UCDP, ACLED ou
d'autres bases sans travail supplémentaire.

## 2. Contrat d'observation mensuelle

Exemple d'une ligne JSONL :

```json
{"identifiant":"FICTIF_A:2020-01","unite":"FICTIF_A","mois":"2020-01","revision":1,"cible":"presence_affrontement_organise_v1","valeur":0,"couverture":"complete","nature":"synthetique","source":"synthetic://fixture-v1","version_source":"1","licence":"MIT","preuve_disponibilite":"synthetic://calendrier-impose","publication":"2020-02-01","disponibilite":"2020-02-01","ingestion":"2020-02-01"}
```

| Champ / règle | Rôle |
|---|---|
| Identifiant stable, unité, mois | Une seule identité par cellule ; une identité ne change pas de cellule |
| Révision entière positive | Plusieurs versions possibles, mais jamais deux fois la même révision |
| Cible fixée | Empêche de mélanger des événements incompatibles dans une même évaluation |
| Valeur et couverture | `complete` exige 0 ou 1 entier ; `incomplete` exige `null` |
| Nature | Le registre refuse le mélange `observee` / `synthetique` |
| Source, version et licence | Métadonnées obligatoires de provenance et réutilisation |
| Preuve de disponibilité | Référence obligatoire à conserver ; son authenticité n'est pas vérifiée automatiquement |
| Publication | Date de publication de cette révision, pas date de l'affrontement |
| Disponibilité | Date à laquelle cette version est attestée accessible publiquement |
| Ingestion | Date d'entrée de cette version dans le système local |

Le mois est au format `AAAA-MM`, les dates au format `AAAA-MM-JJ`.
L'import refuse les champs inconnus, les champs obligatoires absents, les clés JSON
dupliquées et les valeurs incohérentes, avec le numéro de ligne en erreur.

Pour ce produit mensuel complet, la chronologie imposée est :

```text
premier jour du mois suivant <= publication <= disponibilité <= ingestion
```

Le contrat ne convient donc pas directement à une dépêche publiée pendant le mois
ou à une observation événementielle à la journée. Une couche d'agrégation devra
produire les étiquettes mensuelles après clôture, avec sa traçabilité propre.

Une révision ultérieure ne peut être publiée ou disponible avant la précédente.
L'ordre d'ingestion peut différer : le choix de la version connue se fait par
numéro de révision, pas par ordre des lignes du fichier.

## 3. Deux notions de connaissance, explicitement séparées

- **Mode local, par défaut** : seules les versions déjà ingérées sont accessibles.
  C'est une reconstitution du savoir disponible au système.
- **Mode public, optionnel** : une version attestée publiquement disponible peut
  être utilisée même si elle a été ingérée plus tard. C'est un scénario de
  connaissance publique historique, pas une preuve que notre système prévoyait
  effectivement quoi que ce soit à cette époque.

Les dates n'ayant pas d'heure, une prévision émise au début du premier jour du mois
utilise seulement les données connues **à la clôture de la veille**. Une publication
du jour d'émission n'est pas présumée déjà disponible. On évite ainsi une hypothèse
favorable cachée sur l'heure de publication.

L'instantané retient la dernière révision admissible. Si cette révision retire
l'étiquette (`null`), l'ancienne valeur ne réapparaît pas. Un mois absent, incomplet
ou retiré n'est **jamais** transformé en zéro.

Une chaîne non vide dans `preuve_disponibilite` ne prouve rien à elle seule. Les
preuves de publication, archives et licences doivent encore être vérifiées par
le responsable du jeu réel ; le code ne peut pas détecter un horodatage mensonger.

## 4. Références et protocole chronologique

Au début de chaque mois cible, chaque unité explicitement choisie reçoit deux
références si elle dispose d'au moins six mois antérieurs connus et complets :

1. **Fréquence lissée** : `p = (nombre de mois positifs + 1) / (nombre de mois + 2)`.
2. **Dernier état lissé** : `p = (dernière étiquette connue + 1) / 3`, donc 1/3 ou 2/3.

Le second modèle utilise le dernier mois **connu**, pas forcément le mois précédent.
Sa date est exportée pour rendre visible le retard d'observation. Aucun mécanisme
ne masque une donnée ancienne en la présentant comme actuelle.

Le minimum de six est fixé avant la démonstration, sans optimisation sur les résultats.
Les mois n'ont pas besoin d'être consécutifs : ce choix et l'absence de pondération
de fraîcheur restent des limites. Les unités sont fournies explicitement, pour ne
pas déduire l'univers de prévision des seuls territoires apparaissant dans le futur.

La fenêtre d'apprentissage s'étend au fil du temps : des observations anciennes
deviennent utilisables une fois publiées/ingérées. Il s'agit d'une évaluation
chronologique à origines successives, pas d'un découpage aléatoire et pas d'une
prévision de 18 mois émise en une seule fois.

Chaque prévision exporte son origine, sa borne de connaissance, le mois cible, le
nombre d'observations et **la liste exacte des identifiants/révisions utilisés**.
Les scores utilisent une vérité d'évaluation figée à une date annoncée. Une
révision peut faire évoluer cette vérité et les scores, sans changer les anciennes
prévisions : c'est pourquoi la date et les versions d'évaluation sont conservées.

Les deux références sont évaluées sur les mêmes cellules admissibles. Le rapport
expose séparément :

- abstentions pour historique insuffisant, comptées par unité/origine ;
- exclusions pour vérité inconnue/incomplète, comptées par modèle/cellule ;
- prévisions et révisions réellement utilisées ;
- empreintes SHA-256 du registre canonique et du module de calcul.

Une empreinte fournit un contrôle d'intégrité, pas un certificat d'authenticité ni
un archivage immuable. La commande peut écraser un rapport : une véritable étude
prospective devra ajouter un dépôt horodaté en écriture append-only.

## 5. Mesures publiées, sans score unique trompeur

- **Brier** : moyenne de `(p − y)²`, plus faible = meilleur.
- **Log-loss** : moyenne de `−log(p)` si positif, `−log(1−p)` sinon ; probabilités
  bornées numériquement à `[10⁻¹⁵, 1−10⁻¹⁵]` pour cette mesure uniquement.
- **Matrice d'alerte** : vrais positifs, fausses alertes, événements manqués et vrais
  négatifs au seuil fixé `p >= 0,5`.
- **Calibration descriptive** : cinq classes de largeur 0,2 ; moyenne des
  probabilités, fréquence observée et effectif. Intervalles fermés à gauche et
  ouverts à droite, sauf le dernier qui inclut 1.

Un échantillon vide produit des scores `null`, jamais un score parfait. Une classe
vide de calibration reste explicitement vide. Ces petites tables n'établissent pas
une calibration robuste : aucune barre d'incertitude ou significativité n'est
estimée ici, notamment en présence de dépendance temporelle et géographique.

## 6. Exécution et résultats réellement obtenus

```bash
python -m simulateur.validation_temporelle \
  --observations tests/fixtures/observations_synthetiques.jsonl \
  --debut 2020-07-01 --fin 2021-12-01 \
  --evaluation-au 2022-02-01 \
  --unites FICTIF_A FICTIF_B FICTIF_C \
  --sortie rd-resultats-validation.json

python -m unittest discover -s tests -p 'test_*.py'
```

Jeu inventé : 24 mois, trois unités, deux couvertures incomplètes, une correction
tardive et un retrait d'étiquette. La deuxième unité publie avec deux jours de
retard. Les révisions sont délibérées pour provoquer les cas limites.

Sur 54 cellules unité/mois cibles : trois abstentions communes, puis trois cellules
non évaluables. Il reste **48 cellules comparables par référence**. Le rapport
contient six exclusions car chacune des trois cellules concerne deux modèles.

| Référence — données SYNTHÉTIQUES | Brier | Log-loss | Vrais positifs | Fausses alertes | Événements manqués | Vrais négatifs |
|---|---:|---:|---:|---:|---:|---:|
| Fréquence lissée | 0,259770 | 0,733876 | 0 | 2 | 18 | 28 |
| Dernier état lissé | 0,222222 | 0,636514 | 10 | 8 | 8 | 22 |

Le dernier état obtient de meilleurs scores sur cet exemple mais davantage de
fausses alertes. **Cela ne prouve aucune supériorité sur des conflits réels.** Les
trajectoires ont été inventées ; les résultats servent à vérifier les calculs et
à montrer le compromis entre alertes et événements manqués.

Empreinte canonique du registre de cette exécution :

```text
fffeea119fb8fada3f63bcd82b0f5c8412d68e92d2b7d181bc22a0de43b5c3a4
```

Vérifications : **83 tests réussis**, dont 17 nouveaux tests ; `ruff check .` réussi.
Les tests couvrent notamment révisions futures, mutation du futur sans effet sur
le passé, retraits, publication le jour d'émission, mode public/local, abstentions,
chronologie, import strict, scores connus et échantillons vides.

## 7. Ce qui est résolu et ce qui ne l'est pas

| Sujet | État à la fin de cette phase |
|---|---|
| Contrat et import d'étiquettes mensuelles | Implémentés et testés |
| Instantanés versionnés / prévention logicielle des fuites | Implémentés, sous réserve de dates d'entrée honnêtes |
| Comparaison chronologique de références | Exécutée sur données synthétiques uniquement |
| Cible réelle validée et guide de codage | Non réalisés ; définition de travail seulement |
| Connecteur fournisseur et agrégation des événements | Non réalisés |
| Vérification des archives et droits de réutilisation réels | Non réalisée |
| Échantillon réel couvrant périodes positives et négatives | Non constitué |
| Calibration du moteur géopolitique | Non réalisée |
| Calibration probabiliste / incertitude / validation indépendante | Non réalisées |
| Prévisions prospectives archivées avant les événements | Non réalisées |

### Prochaine expérience utile

Choisir un fournisseur et une cible compatible, vérifier sa licence et ses archives,
constituer un petit corpus réel versionné **sans inventer les périodes négatives**,
puis geler avant exécution la période de test et les unités. Comparer les références
sur ce corpus avant d'ajouter un modèle complexe. Une évaluation fondée uniquement
sur des données révisées actuelles devra être qualifiée de rétrospective limitée,
pas de reconstitution fidèle d'une prévision historique.

Les coûts logistiques, réseaux multi-routes, interdépendances industrielles et
effets humains de l'audit précédent restent également ouverts. Cette phase ne
prétend pas les avoir résolus en ajoutant un protocole statistique.

## Addendum — adaptateur GED (R&D v4)

Un [adaptateur local du schéma UCDP GED 26.1](RD_IMPORT_UCDP.md) est désormais testé.
Le registre accepte sa cible spécifique `presence_evenement_letal_ucdp_v1`, mais
interdit de la mélanger avec la cible générale d'affrontements. L'acquisition réelle
a été bloquée par la connectivité lors de cette phase ; les tests d'import restent
synthétiques et aucune validation prédictive sur données observées n'est revendiquée.
