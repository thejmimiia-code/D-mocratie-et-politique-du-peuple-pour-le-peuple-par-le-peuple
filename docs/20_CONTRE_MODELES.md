# 20. Contre-modèles : les quatre thèses auxquelles ce plan se mesure

> Un projet qui ne se compare qu'à ses repoussoirs — le statu quo et l'austérité — gagne tous les débats qu'il organise. Ce document fait l'inverse : il expose quatre modèles alternatifs *cohérents*, écrits au mieux, et dit pour chacun ce que le simulateur en montre, ce que le dépôt leur concède, et où il ne les suit pas.
> Contenu engendré par `outils/generer-objections.py` à partir de `simulateur/contradiction.py` : aucune phrase de ce document n'existe ailleurs.

---

## État minimal, intelligence artificielle et revenu universel

*Porté par : courant techno-libertarien (Stéphane Mallard et une partie de son réseau).*

### La thèse

L'État est le problème : il produit de la dette, des règles et de la lenteur. L'intelligence artificielle permettrait de rendre le régalien moins coûteux, de remplacer une partie de la décision publique par des systèmes experts, et de financer un revenu universel par la valeur créée par les machines. Le modèle de référence est celui des places qui attirent le capital par la fiscalité légère.

### Ce que le simulateur en dit

Le catalogue ne contient pas ce modèle : le scénario le plus proche est « austérité », qui coupe et subit la fronde — insuffisant pour représenter une thèse qui promet, elle, une baisse de la dépense publique avec un revenu universel en face. Le dépôt l'assume : comparer sérieusement ce modèle suppose d'écrire un préréglage « État minimal + transfert universel », qui est un chantier, pas une réplique.

*Scénarios comparables :* `austerite`, `statut_quo`.

*Préréglages existants :* `austerite`.

### Ce que nous lui concédons

Sur le fond, le dépôt n'a pas de réponse définitive au coût de la lenteur administrative : c'est précisément l'objet du volet 3 (fusion des doublons, commande publique), et si ce volet échoue, l'argument techno-libertarien gagne du terrain.

### Où nous ne le suivons pas

La légitimité : une décision prise par un système non élu n'est pas contestable par un citoyen, et une erreur algorithmique ne se corrige que par un autre algorithme. Le simulateur lui-même en donne la démonstration — ses résultats dépendent d'hypothèses discutables, et c'est pour cela qu'il les publie. La ligne que le dépôt propose est claire : l'IA pour contrôler des flux (fraude, aides), jamais pour décider d'un droit.

### Ce qui reste ouvert

Un scénario « État minimal + revenu universel » reste à écrire pour que la comparaison soit chiffrée au lieu d'être rhétorique.

---

## Le mur de la réalité budgétaire et les barrières organisationnelles

*Porté par : Olivier Babeau (mur de la réalité) et Michel Levy Provençal (adoption).*

### La thèse

Les marges de manœuvre sont fictives : la dépense contrainte, la dette et les engagements passés laissent peu de place, et les gains annoncés par la technologie se heurtent à des délais d'organisation que personne ne finance. Un plan qui promet 60 Md€ en cinq ans ignore le temps long de l'administration.

### Ce que le simulateur en dit

Le laboratoire du dépôt donne partiellement raison à cette thèse : le seuil de 3 % de déficit ne discrimine pas les politiques testées, puisque les 500 trajectoires témoins le franchissent aussi. Ce qui reste robuste est l'écart au témoin, environ 0,73 point de PIB en moyenne. L'audit d'hypothèses ajoute sa propre correction : avec des recettes indexées sur le PIB et une transmission amortie des taux, l'atterrissage se décale vers 3,05 à 3,26 %.

*Scénarios comparables :* `statut_quo`, `choc_mondial`.

*Préréglages existants :* `statut_quo`, `choc_mondial`.

### Ce que nous lui concédons

Le calendrier est le point faible du dossier, et il est concédé : c'est la raison d'être des fiches de gage (rendement constaté, délai notifié → encaissé, base légale) et de la réserve de gage d'environ 10 Md€.

### Où nous ne le suivons pas

Le mur n'est pas une muraille : les leviers de recouvrement, de niches et de doublons sont documentés par la Cour des comptes et le Sénat, et le dépôt ne table sur aucune croissance magique — le plan est un plan de marges, pas de croissance.

### Ce qui reste ouvert

Un échéancier de déploiement par levier (cadrage, pilote, généralisation) reste à écrire dans les fiches de gage.

---

## Les gains de l'IA viennent de la réorganisation du travail

*Porté par : Carlos Diaz (réalisme d'adoption) et la littérature sur les gains de productivité.*

### La thèse

Un outil ne produit pas de gain : c'est la réorganisation du travail autour de l'outil qui le produit. Promettre des milliards d'économies sans dire quels agents changent de mission revient à promettre des économies fictives.

### Ce que le simulateur en dit

Le moteur chiffre des rendements, pas des transitions : il ne dit rien du nombre d'agents à former ni du délai d'apprentissage. Le préréglage « mandature » applique les profils de montée en charge, mais la montée en charge est une courbe, pas un plan de réaffectation.

*Scénarios comparables :* `mandature`, `double_mandature`.

*Préréglages existants :* `mandature`, `double_mandature`.

### Ce que nous lui concédons

« Fusion des doublons, zéro licenciement » doit devenir un plan de réaffectation chiffré : effectifs concernés, missions d'accueil, formation, calendrier. Tant que ce n'est pas écrit, la thèse est fondée.

### Où nous ne le suivons pas

La contrainte n'est pas budgétaire mais organisationnelle, et le dépôt ne propose aucune suppression de poste : le non-remplacement sur les fonctions de siège laisse le temps de la réaffectation. Le coût de la transition doit être budgété, pas nié.

### Ce qui reste ouvert

Chiffrer le coût de la réaffectation (formation, accompagnement) et le soustraire du gain affiché, plutôt que de le laisser implicite.

---

## L'ajustement budgétaire orthodoxe, sans réforme institutionnelle

*Porté par : courant de la consolidation budgétaire.*

### La thèse

Seule compte la trajectoire de dette : il faut couper la dépense, réformer les retraites, conditionner les prestations, et éviter tout ce qui ressemble à une promesse de baisse d'impôt non financée. Les réformes institutionnelles sont un luxe qui retarde l'ajustement.

### Ce que le simulateur en dit

Les scénarios « austérité » et « statut quo » encadrent cette thèse. Le statu quo dégrade ; l'austérité dégrade la tension sociale et la qualité des services de proximité, avec un spread qui ne s'améliore pas dans la version actuelle du moteur — défaut de modélisation reconnu (objection sur la prime de risque), ce qui affaiblit provisoirement la comparaison dans les deux sens.

*Scénarios comparables :* `statut_quo`, `austerite`.

*Préréglages existants :* `statut_quo`, `austerite`.

### Ce que nous lui concédons

Le dépôt partage le constat : la dette est le principal facteur de vulnérabilité, et un plan qui l'ignorerait serait un mauvais plan. Les 51 Md€ de désendettement net sont la réponse à cette objection.

### Où nous ne le suivons pas

L'ajustement par la seule dépense bute sur deux limites que le modèle donne : la tension sociale produit un coût politique et financier (prime de risque), et certaines coupes augmentent la dépense ailleurs (santé, précarité, sécurité). Le dépôt préfère chercher la marge dans le recouvrement et les niches plutôt que dans les prestations.

### Ce qui reste ouvert

Un préréglage « consolidation orthodoxe » chiffré manque : le scénario d'austérité actuel est trop grossier pour trancher le débat.

---

## Ce que ce document ne prétend pas

Il ne prétend pas que ces quatre thèses soient fausses : il prétend qu'elles sont discutables avec des chiffres, et il nomme ce qui manque encore pour trancher — un préréglage « État minimal », un échéancier de déploiement par levier, un coût de réaffectation chiffré, une consolidation orthodoxe modélisée. Tant que ces pièces manquent, le dépôt dit qu'elles manquent plutôt que de faire semblant d'avoir répondu.
