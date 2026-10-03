# Laboratoire R&D : tenter de mettre le modèle en défaut

## Objectif et statut

Prototype exploratoire ajouté le 3 octobre 2026, sans modification des équations
existantes. L'originalité recherchée est celle des expériences dans ce dépôt :
aucune recherche d'antériorité ne permet ici de revendiquer une première mondiale.
Les résultats ne valident ni une politique ni les hypothèses macroéconomiques.

## Reproduire

```bash
python -m simulateur.laboratoire --nombre 500 --graine 20261003 --sortie rd-resultats.json
python -m unittest discover -s tests -p 'test_*.py'
```

Python standard uniquement. Le JSON contient paramètres, synthèse et trajectoires
annuelles intégrales des deux branches. Les indices d'essais commencent à zéro.
La graine et la même version du code permettent de reproduire la campagne.
Le fichier volumineux généré est ignoré par Git ; ce document conserve les constats.

## Protocole falsifiable

Chaque tirage est comparé à un statut quo exposé au **même choc**, avec un moteur
neuf par simulation. Horizon : cinq ans. Tirages indépendants uniformes :

- réalisation commune des huit leviers de recettes/économies : 0 à 100 % ;
- hausse du pétrole : 0 à 60 dollars par baril ;
- variation EUR/USD : −0,20 à 0 ;
- hausse Fed : 0 à 200 points de base ;
- année du choc : entier de 1 à 5 inclus.

Le choc est injecté une fois, pas renouvelé chaque année ; sa persistance dépend
du moteur. Les coûts de baisse de TVA et les réformes institutionnelles restent
inchangés : une faible réalisation n'annule donc pas leurs coûts et effets.
Ces bornes sont des choix d'exploration, non des intervalles de confiance.

Chaque tirage utilise cinq simulations : réformes avec chocs combinés, témoin
avec chocs combinés, puis réformes avec énergie/change seuls, taux seuls et sans
choc. Interaction sur le déficit final (points de PIB) :
`combinés − énergie/change seuls − taux seuls + sans choc`.
Une valeur non nulle suggère une non-additivité **du modèle** ; ses sorties étant
arrondies au centième, de petites différences peuvent être des artefacts.

Le laboratoire retourne le pire déficit **parmi les tirages**, pas un maximum
global. Aucun classement politique pondéré ni optimisation normative cachée.

## Résultats réellement exécutés

Campagne de 500 tirages, graine 20261003, soit 2 500 simulations quinquennales :

- 500/500 trajectoires réformées finissent sous 3 % de déficit ;
- **le témoin aussi : 500/500**. Ce seuil ne discrimine donc pas les politiques
  dans le domaine testé ; ce n'est pas une preuve de résilience réelle ;
- écart moyen du déficit réformes moins témoin : **−0,72724 point de PIB** ;
- pire déficit réformé : **1,27 %**, essai 136. Réalisation des leviers proche de
  0,118 %, pétrole +56,225 dollars, change −0,05691, Fed +18,959 pb en année 3.
  Dans cet essai, les réformes dégradent le déficit de **0,28 point** par rapport
  au témoin, tout en améliorant l'indice de pouvoir d'achat de **8,5 points** ;
- plus forte interaction absolue observée : **0,01 point**, essai 71.
  Elle ne permet pas de conclure à un effet substantiel vu les arrondis ;
- suite complète : **38 tests réussis**, dont cinq nouveaux tests du laboratoire.

## Ce que cela invite à tester ensuite

1. Auditer pourquoi même le statut quo passe sous 3 % : croissance tendancielle,
   dépenses et recettes, dynamique de dette. Ne pas confondre cette observation
   avec une erreur démontrée sans analyse des équations.
2. Exporter des métriques non arrondies avant de mesurer les interactions fines.
3. Varier les coefficients structurels, pas seulement les décisions : les
   conclusions actuelles restent conditionnelles à un moteur unique.
4. Introduire des retards et échecs distincts par levier, puis des chocs corrélés
   et répétés, avec bornes justifiées et données externes indépendantes.
5. Réserver des scénarios de validation hors exploration avant de proposer une
   stratégie adaptative : éviter de sélectionner puis valider sur les mêmes cas.

Il n'y a ici ni expérimentation sur des personnes, ni collecte de données privées,
ni preuve causale sur l'économie réelle.
