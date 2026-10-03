# Audit technique de la PR #11

## Défauts reproduits et corrigés

### 1. Installation Python impossible

`tool.setuptools.py-modules` était une table TOML alors que setuptools exige une
liste. `pip install --no-deps --no-build-isolation -e .` échouait à la validation des
métadonnées. La valeur est désormais `py-modules = ["main"]` dans la table
`tool.setuptools`. Le contenu et les points d'entrée du projet sont préservés.

Vérification locale : installation éditable, construction d'une wheel standard,
et lancement de `simulateur-mpol-run --help` réussis. La CI vérifie maintenant
l'installation sur sa matrice Python avant les tests.

### 2. Rapports économiques incohérents avec un arrêt déclaré

Un rapport contenant 36 mois et un arrêt nucléaire au mois 8 était accepté : le
pont macro produisait malgré tout trois années de projections. Le raccordement
vérifie désormais que la longueur correspond exactement à l'horizon, ou au nombre
de mois **précédant** l'arrêt. Mois d'arrêt hors bornes et motifs inconnus sont
refusés. Aucun changement de résultat pour les trajectoires valides.

### 3. Risque d'écraser une source

La CLI de validation permettait d'utiliser le fichier d'observations comme sortie.
L'import UCDP protégeait contre les chemins identiques et les liens symboliques,
mais pas contre deux liens physiques désignant le même fichier.

Un contrôle commun refuse ces trois formes d'alias avant le calcul et l'écriture.
Les tests exécutent réellement les CLI et vérifient que les octets sources restent
intacts. Les erreurs d'écriture de la CLI de validation sont aussi présentées comme
erreurs de commande, plutôt que comme traces Python brutes.

Cette protection n'est ni un verrou de fichiers ni une transaction atomique pour
les deux exports UCDP. Les fichiers de résultats existants peuvent toujours être
remplacés volontairement ; un archivage prospectif immuable reste à construire.

### 4. Empreinte CSV calculée sur une autre lecture

L'import ouvrait le CSV une fois pour calculer le SHA-256, puis une seconde fois
pour le parser. Une modification entre les deux pouvait dissocier le hash des
données utilisées. Le hash est désormais alimenté par les octets effectivement
transmis au parseur, en une seule lecture en flux, sans charger tout le CSV en RAM.

Un test vérifie une ouverture unique et l'empreinte exacte d'un fichier avec BOM
UTF-8 et fins de ligne CRLF. Le besoin d'archives immuables demeure : ce mécanisme
ne certifie pas l'origine des données et ne bloque pas un auteur concurrent.

## Vérifications effectuées

- **106 tests réussis**, dont neuf tests de régression supplémentaires.
- `ruff check .` réussi.
- Installation éditable et construction d'une wheel réussies localement.
- Test d'intégration CLI : import de la fixture, export JSONL, évaluation temporelle,
  six abstentions et aucune fausse prévision historique.
- Ajout des contrôles d'installation et du pipeline R&D au workflow GitHub CI.

À l'ouverture de l'audit, les contrôles GitHub affichés pour la PR concernaient
Vercel ; aucun résultat de CI Python n'était affiché. Les validations locales ne
sont pas présentées comme des exécutions réussies sur GitHub ou sur toutes les
versions Python de la matrice. Le workflow devra effectivement s'exécuter après
publication, selon les autorisations Actions du dépôt.

## Points non résolus par cet audit

- Pas de corpus réel acquis ni de validation prédictive empirique.
- Pas d'authentification automatique des preuves de disponibilité/exhaustivité.
- Pas d'archivage append-only ni de transaction multi-fichiers pour les exports.
- Les coefficients économiques et géopolitiques restent exploratoires.
- Les métadonnées de licence du projet contiennent une description « Loi 1901 —
  Open-Source et Privé », alors que `LICENSE` et le classificateur indiquent MIT.
  Cette incohérence préexistante nécessite une confirmation du propriétaire ;
  l'audit ne modifie pas de lui-même les conditions juridiques du projet.
