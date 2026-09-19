# Guide de contribution

Merci de votre intérêt pour le **Simulateur Macro-Politique & Démocratique** !
Ce projet est un outil d'aide à la décision publique, auditable et transparent.
Toute contribution constructive est la bienvenue.

## Comment contribuer

### Signaler un problème (Issue)

Utilisez les modèles d'issue fournis :
- **Bug** : pour signaler un dysfonctionnement technique
- **Amélioration** : pour proposer une nouvelle fonctionnalité ou une correction de données

### Proposer une modification (Pull Request)

1. **Forkez** le dépôt
2. **Créez une branche** dédiée : `git checkout -b feature/votre-modification`
3. **Conventions de code** :
   - Python 3.10+, typage explicite, docstrings complètes
   - Toute donnée chiffrée doit être sourcée (INSEE, DGFIP, AFT, BCE, etc.)
   - 100% des tests doivent passer avant soumission
4. **Tests** : ajoutez des tests pour toute nouvelle fonctionnalité dans `tests/`
5. **Documentation** : mettez à jour le README et les fichiers `docs/` si nécessaire
6. **Soumettez** votre PR avec une description claire des changements

### Conventions de données

Toute donnée intégrée au simulateur **doit** :
- Être adossée à une source officielle vérifiable (INSEE, DGFIP, Banque de France, Eurostat, etc.)
- Inclure l'URL d'accès direct à la source
- Préciser la méthodologie de collecte (SEC 2010, ERFS, etc.)
- Être accompagnée de l'intervalle de confiance si disponible

### Structure du projet

```
simulateur/
├── model.py              # Dataclasses des 4 échelons
├── moteur.py             # Moteur de calcul SFC
├── scenarios.py          # 4 scénarios prédéfinis
├── reglements_lois.py    # 95 articles de loi
├── sources_officielles.py# 25+ sources certifiées
├── think_tanks.py        # 23 think tanks audités
├── histoire_france.py    # 12 périodes (1792→2026)
├── societe_domaines.py   # 18 domaines sociétaux
├── cli.py                # Interface terminale
└── web_server.py         # Serveur HTTP et API REST
tests/
└── test_*.py             # 166 tests (unittest)
docs/
└── *.md                  # 14 volumes de référence
```

### Lancer les tests

```bash
python3 -m unittest discover tests
```

### Lancer le serveur web

```bash
python3 main.py web 8000
```

## Normes éthiques

Ce projet a pour vocation d'être un **outil d'aide à la décision publique**
et non un instrument partisan. Les contributions doivent :
- Respecter la neutralité politique du projet
- Présenter les données de manière objective et sourcée
- Anticiper et documenter les objections légitimes
- Ne jamais déformer des données officielles

## Licence

Ce projet est sous licence **GNU General Public License v3.0** (GPLv3).
En contribuant, vous acceptez que vos contributions soient publiées sous cette licence.

## Contact

Pour toute question, ouvrez une issue sur le dépôt GitHub.