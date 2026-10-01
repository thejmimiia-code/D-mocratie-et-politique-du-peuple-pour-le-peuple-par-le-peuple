# Contributing

Merci de votre intérêt pour le **Simulateur Macro-Politique Systémique** !

## Philosophie du projet

Ce simulateur modélise l'intégration dynamique de 4 échelons de contrainte :
Local → National → Europe → Mondial. Chaque décision politique a des
répercussions systémiques mesurables et chiffrables.

**Principe directeur** : toute modification doit être **vérifiable par preuve réelle**
(finish_reason=stop, tests passants, résultats reproductibles).

## Environnement de travail

```bash
# 1. Créer un venv dédié
python3 -m venv .venv

# 2. Activer
source .venv/bin/activate      # Linux/macOS
.venv/Scripts/activate         # Windows

# 3. (Optionnel) Installer les dépendances dev
pip install -e ".[dev]"

# 4. Lancer les tests
python -m unittest discover -s tests -p "test_*.py" -v

# 5. Lancer le simulateur
python3 main.py mandature
python3 -m simulateur.cli          # menu interactif
```

## Standards de code

- **Zéro dépendance externe** : le simulateur s'appuie uniquement sur la
  bibliothèque standard Python. Ne pas introduire de dépendance sans justification.
- **Précision des données** : toutes les valeurs calées sur des sources officielles
  (INSEE, Eurostat, Ministère des Finances, BCE). Vérifier chaque chiffre.
- **Tests obligatoires** : toute modification de logique de simulation nécessite
  un test correspondant dans `tests/`.
- **Type hints** : toutes les fonctions doivent être typées (mypy strict).
- **Lint** : `ruff check .` doit passer sans erreur.

## Pull requests

1. Fork du dépôt
2. Branche depuis `main` : `git checkout -b feat/nom-functionnalite`
3. Commits avec `git-cz` ou messages clairs
4. Tests + lint passent
5. PR avec description claire du changement et justification économique/politique

## Scénarios disponibles

| Scénario             | Description                                      |
|----------------------|--------------------------------------------------|
| `mandature`          | Plan de mandature quinquennal (+60 Md€/an en Y5) |
| `statut_quo`         | Immobilisme politique et dérive financière       |
| `austerite`          | Coupes territoriales et fronde fiscale           |
| `choc_mondial`       | Stagflation, pétrole >110$, resserrement Fed      |

## Export

```bash
# Export JSON
python3 main.py mandature --export mandature.json

# Export CSV
python3 main.py choc_mondial --export choc_mondial.csv
```

## Aide

Besoin d'aide ? Ouvrez une issue avec le label `question`.
