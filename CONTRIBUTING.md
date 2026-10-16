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
   - Python 3.11+, typage explicite, docstrings complètes
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
├── model.py              # Dataclasses des 5 échelons (Local → National → Europe → Mondial → Géopolitique)
├── moteur.py             # Moteur de calcul SFC
├── moteur_parametrique.py# Orchestrateur 156 leviers × 20 domaines (horizon 1-10 ans)
├── parametres.py         # 156 leviers (14 familles, 16 préréglages, normaliser / catalogue_public)
├── domaines.py           # 20 domaines d'impact, 74 indicateurs (evaluer_domaines)
├── societe_domaines.py   # 18 domaines sociétaux (histoire longue 1792→2026)
├── histoire_france.py    # 12 périodes (1792→2026)
├── seuils.py             # Garde-fous par strate (31 seuils, bornes & risque)
├── compression.py        # Compression HTTP négociée (gzip/deflate/br/zstd, seuil 512 o)
├── lexique.py            # 83 termes définis, API /api/lexique + balisage page
├── clarte.py             # Lecture en clair (phrases fidèles, neutres, sourcées)
├── bulles.py             # 101 bulles explicatives + cache (101 bulles, clef contexte)
├── conseil.py            # Conseiller temps réel « effet papillon » (levier isolé, budget réel)
├── sources_officielles.py# 52 indicateurs publics sourcés (Eurostat, BCE, Banque mondiale)
├── donnees_live.py       # Registre 52 indicateurs, snapshot daté, collecte CORS ou hors-ligne
├── dashboard.py          # Serveur HTTP multi-thread + API JSON (23 routes du moteur)
├── interface.py          # Page unique (156 leviers, rendu différé des 7 onglets, recherche)
├── surface_publique.py   # Ce que la page dit d'elle-même aux robots (robots.txt, sitemap.xml, llms.txt, en-tête)
├── web_server.py         # Console héritée (compatibilité, 11 scénarios)
├── pont_api.py           # Routeur unique Vercel (22 routes → api/[...path].py)
└── wsgi.py               # Point d'entrée WSGI (Render, Docker, gunicorn)
tests/
└── test_*.py             # suite de tests (le compte s'affiche à l'exécution)
docs/
└── *.md                  # volumes de référence + R&D (double mandature, géopolitique, fluidité...)
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