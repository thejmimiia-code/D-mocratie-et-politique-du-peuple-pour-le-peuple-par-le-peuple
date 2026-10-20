# 16 — Instances, yoyo des chambres et fentes non écrites

`simulateur/instances_et_dynamiques.py` ajoute la troisième couche : après les articles
(`constitution_analysee`) et les manœuvres (`gouvernance_contrepouvoir`), **qui** agit,
**combien de temps** ça tient, et **ce que personne n'a écrit alors que tout le permet**.

## 1. Trois registres, une même discipline

| registre | contenu | ce qui le rend vérifiable |
|---|---|---|
| `INSTANCES` (26) | Conseil constitutionnel, Conseil d'État, Cour de cassation, Cour des comptes, CSM, ARCOM, CNIL, Défenseur des droits, CNCCFP, CESE, préfet, juridictions administratives, CJUE, CEDH, Commission européenne, Conférence des présidents, commissions, Congrès, Haute Cour, Sénat, Assemblée, outre-mer, Président, Gouvernement, corps électoral | `fondement` ne cite que des **articles de fiche** ou des **identifiants du `REGISTRE_LEGAL`** ; `juge_par` est obligatoire : une instance qui ne répond devant personne doit le dire |
| `TRAJETS` (8) | battements de la navette ordinaire, du budget, de la révision par Congrès, de la révision par référendum, du renversement, de la QPC, du contentieux local, du RIP | chaque battement porte un `fondement` d'article et des `jours` **de rigueur** — pas des durées prévues |
| `STRATEGIES` (15) et `FENTES` (12) | ce qui a déjà servi, et ce qui n'est écrit nulle part | toute prémisses se résout dans le dépôt ; le barème de robustesse est public |

La normalisation est la même que pour les fiches : un levier inexistant est retiré du
champ `leviers` et bascule dans `pistes`. Le registre des `filtres_appliques` de
`coherence_avec_le_droit()` les énumère — rien ne disparaît en silence, et aucun verrou
ni mécanisme inventé ne survit (les tests le refusent).

## 2. Le yoyo, en jours et en voix

    python3 -c "from simulateur.instances_et_dynamiques import oscillation; \
                 print(oscillation('projet_ordinaire'))"

Résultat au 2026-10-12 :

- navette ordinaire : **10 battements, 160 jours de rigueur** — la fenêtre législative résiduelle n'en compte que 150, donc `tenable_dans_la_fenetre` est **Faux** : un texte qui part aujourd'hui ne finit pas sa navette ordinaire avant la suspension de l'ordre du jour ;
- retard imposable par le Sénat et la saisine : 58 jours ;
- `asymetrie_des_chambres()` : veto réel du Sénat **uniquement** sur la révision (89 al. 4 (termes identiques exigés)) — jamais sur la loi ordinaire ni sur le budget (45 al. 4 (dernier mot de l'Assemblée)).

Le seul chiffre du module qui ne vienne pas d'un texte est la fenêtre de
150 jours : c'est un **constat daté**, et la note le dit.

## 3. Les fentes : la R&D du dépôt

Une fente est admise au registre à trois conditions, contrôlées par les tests :

1. **deux prémisses au minimum**, chacune résoluble (`art:`, `reg:`, `verrou:`,
   `mecanisme:`, `instance:`) — une prémisse de type `jurisprudence:` est tolérée mais
   marquée `verifiable: False` et interdit le score maximal ;
2. une **raison du silence** : expliquer pourquoi ce n'est pas écrit, sinon c'est un oubli,
   pas une fente ;
3. un **verrou de retour** nommé : l'étage de texte nécessaire pour la défaire, et donc
   l'étage par lequel elle est attaquable.

| clé | de quoi il s'agit | nature | robustesse | étage | prémisses |
|---|---|---|---|---|---|
| `priorite_du_droit_derive` | Faire écarter une loi par un juge ordinaire, sans le Conseil | fente | 92 | conventionnel ou droit dérivé de l'UE | 5 prémisses, toutes résolues |
| `congres_par_exprimes` | Le Congrès se calcule sur les votants, pas sur les sièges | fente | 82 | constitutionnel | 3 prémisses, toutes résolues |
| `absence_de_quorum` | Ni quorum, ni seuil de participation : le silence est la règle | fente | 82 | constitutionnel | 4 prémisses, toutes résolues |
| `nouvelle_deliberation_presidentielle` | Le Président peut renvoyer la loi au Parlement, sans motif | porte | 82 | constitutionnel | 3 prémisses, toutes résolues |
| `referendum_sans_juge` | Entre l'adoption populaire et la promulgation, il n'y a personne | fente | 79 | conventionnel ou droit dérivé de l'UE | 5 prémisses, toutes résolues |
| `irrecevabilite_sans_recours` | Le recours contre une irrecevabilité n'est ouvert qu'à celui qui ne le veut pas | droit_sans_juge | 75 | constitutionnel | 3 prémisses, toutes résolues |
| `petition_dans_le_reglement` | Le seuil de pétition locale, personne ne l'a fixé : l'assemblée le fixera | fente | 75 | réglementaire | 4 prémisses, toutes résolues |
| `censure_par_membres` | L'abstention est un vote de confiance | fente | 72 | constitutionnel | 3 prémisses, toutes résolues |
| `outre_mer_comme_laboratoire` | Le droit peut être différent quelque part, sans révision | porte | 70 | loi organique | 5 prémisses, toutes résolues |
| `defossilisation_sans_vote` | Réécrire la loi par décret, avec l'accord forcé du législateur | fente | 67 | réglementaire | 5 prémisses, toutes résolues |
| `toucher_la_loi_par_le_decret` | Contourner l'article 61-1 en attaquant l'acte d'application | fente | 67 | réglementaire | 5 prémisses, toutes résolues |
| `amendement_etrang` | Le cavalier est irrecevable, et c'est tout | fente | 65 | loi ordinaire | 3 prémisses, toutes résolues |

Deux résultats méritent d'être lus deux fois :

- **`congres_par_exprimes`** — l'article 89 compte les *suffrages exprimés*. Le module ne
  le commente pas, il le calcule : 555 voix sur 925 sièges,
  180 si 300 parlementaires votent seulement. Rien n'est enfreint, rien n'est écrit :
  c'est de l'arithmétique appliquée à une assiette que personne n'a corrigée.
- **`censure_par_membres`** — l'article 49 compte les *membres composant* l'Assemblée :
  289 voix, quel que soit le nombre de votants. Le même geste (s'abstenir) produit l'effet
  exactement inverse selon la chambre. Cette asymétrie ne figure dans aucun commentaire
  d'article du dépôt ; elle est la conséquence directe de deux mots différents.

Le registre compte aussi un **droit sans juge** (`irrecevabilite_sans_recours`) : le
recours contre une irrecevabilité opposée en séance appartient au seul président de
l'assemblée. Et une **boucle sans issue**, mesurée par `boucle_de_controles()` : la
loi référendaire n'a aucune instance saisissable — la décision du 6 novembre 1962 n'est pas
un texte du dépôt, elle est signalée comme prémisse non vérifiable, et le score le dit.

## 4. Ce que le module refuse de dire

`robustesse()` note de 0 à 100 la **défendabilité** (base écrite, clarté de la compétence,
ancrage de la procédure, hauteur de l'étage, résistance à l'abrogation). Le champ
`irrefutabilite` est systématiquement `None`, et la `limite` rappelle que le Conseil d'État
contrôle la compétence, la procédure et la motivation — jamais la cohérence d'une
démonstration. Une fente assise sur un décret s'attaque par un décret : c'est exactement ce
que mesure `etage_de_verrouillage()`.

Aucune fente ne se présente comme gagnée : le test `test_les_fentes_ne_se_disent_jamais_gagnantes`
interdit les formules du type « à coup sûr », « irréfragable », « gagnée d'avance ». Les
faits d'actualité non retrouvés dans le dépôt (bilans de saisines, décomptes de 1967,
nombres d'effectifs de certaines autorités) restent marqués `a_verifier` dans les champs
de prose et ne chiffrent jamais un scénario.

## 5. Routes et vérification

    GET /api/instances      ?instance=conseil_etat · ?article=49 · ?saisine=soixante · ?chercher=…
    GET /api/dynamiques     ?trajet=47 · ?fente=congres_par_exprimes · ?strategie=… · ?famille=armer
                            · ?boucles=1 ; sans paramètre, la synthèse complète

    python3 outils/generer-fonctions-api.py --verifier      # 24 routes exposées
    python3 -m unittest discover -s tests -p "test_*.py"   # OK (skipped=11)

## 6. Limites

- Pas de section d'interface : les routes et les modules font foi.
- `FENTES` est un registre de **conséquences déduites**, pas un catalogue de réformes : la
  mise en œuvre d'une fente suppose son propre étage de texte, et le module ne le rédige pas.
- Les délais des battements sont des délais de rigueur ; les durées réelles de séance, les
  temps de commission et les usages de la Conférence des présidents ne sont pas modélisés.
