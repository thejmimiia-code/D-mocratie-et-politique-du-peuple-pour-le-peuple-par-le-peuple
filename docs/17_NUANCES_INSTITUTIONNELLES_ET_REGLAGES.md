# 17. Nuances institutionnelles : les réglages qui recalculent le droit

> Page produite en relisant le code (`simulateur/nuances_institutionnelles.py`) : les chiffres ci-dessous sont mesurés, pas recopiés. Pour les changer, il faut changer les règles.

Le catalogue compte **149 leviers** en 14 familles, dont **48 réglages institutionnels** (préfixe `reglage_`) répartis sur **9 niveaux** : constitutionnel, parlementaire, budgétaire, judiciaire, territorial, outre-mer, européen, participation, exception. Chacun de ces réglages est un curseur, un interrupteur ou un choix **comme les autres** — il traverse l'interface, les bulles, la page de vérification et les préréglages — et il est de plus branché sur une règle de recalcul : seuils de contre-pouvoir, délais de procédure, fenêtre législative utile, solidité des fentes non écrites et indices institutionnels.

## 1. Quatre règles qui tiennent tout l'édifice

1. **Un réglage à zéro = statu quo strict.** Aucun curseur institutionnel ne vaut autre chose que « la règle telle qu'elle est écrite » à sa valeur par défaut. Les vérifications `controles_neutres` du module le vérifient : {"seuils_identiques_au_droit": true, "trajets_identiques_au_droit": true, "fentes_unchanged": true, "indices_a_cinquante": true}.
2. **Un indice à 50 = l'état du droit**, ni bien ni mal. Un indice est une amplitude relative : 50 + ce que le réglage rapporte − ce qu'il coûte, borné à [0, 100]. Le brut restant affiché, une saturation est visible (`borne_appliquee`).
3. **Une fente verrouillée n'est pas réfutée.** Le score de défendabilité baisse, la déduction reste vraie, et `irrefutabilite` reste vide : aucun réglage ne rend une conséquence inattaquable.
4. **Rien n'est saisi à la main.** Les seuils partent de `gouvernance_contrepouvoir.seuil()`, les jours de `instances_et_dynamiques.oscillation()` (cohérence vérifiée : True), les scores de `robustesse()`. Les réglages déplacent ces valeurs par des règles écrites en clair.

## 2. Réglages par niveau

| Niveau | Réglages | dont déplacés | Articles du registre mobilisés |
|---|---:|---:|---:|
| **Constitutionnel** | 8 | 0 | 7 |
| **Parlementaire** | 7 | 0 | 6 |
| **Budgétaire** | 5 | 0 | 6 |
| **Judiciaire** | 7 | 0 | 9 |
| **Territorial** | 5 | 0 | 7 |
| **Outre-mer** | 2 | 0 | 2 |
| **Européen** | 4 | 0 | 7 |
| **Participation** | 6 | 0 | 7 |
| **Exception** | 4 | 0 | 5 |

## 3. Les 48 réglages (préfixe `reglage_`), la règle et l'effet

| Réglage | Type | Unité | Bornes | Règle appliquée | Ce que ça change |
|---|---|---|---|---|---|
| `reglage_49_3_interdiction`<br>*Interdiction du 49.3 hors loi de finances* | interrupteur | bool | 0 → 1 | interdiction du 49.3 hors loi de finances | le nombre de textes adoptables sans vote |
| `reglage_action_de_groupe_administratif`<br>*Action de groupe devant le juge administratif* | interrupteur | bool | 0 → 1 | action de groupe ouverte devant le juge administratif | la possibilité d'attaquer une décision réglementaire en bloc |
| `reglage_algorithmes_transparents`<br>*Audit public des algorithmes à fort impact* | interrupteur | bool | 0 → 1 | audit public des algorithmes à fort impact | la vérifiabilité d'une décision individuelle automatisée |
| `reglage_ancre_ue_reforms`<br>*Ancrer une réforme dans le droit dérivé de l'Union* | curseur | % du champ concerné | 0 → 100 | part de la réforme écrite en droit dérivé de l'Union | la résistance de la réforme à l'abrogation unilatérale |
| `reglage_appel_qpc`<br>*Appel possible du filtre de non-renvoi d'une QPC* | interrupteur | bool | 0 → 1 | appel du filtre de non-renvoi d'une question prioritaire de constitutionnalité | le nombre de droits effectivement justiciables devant le Conseil |
| `reglage_audit_obligatoire_prealable`<br>*Audit obligatoire avant toute réforme structurelle* | interrupteur | bool | 0 → 1 | avis public d'une juridiction supérieure avant dépôt d'une réforme structurelle | la qualité de l'information disponible pendant la navette |
| `reglage_autonomie_financiere_garantie`<br>*Plancher constitutionnel de dotation locale* | curseur | % | 0 → 30 | plancher constitutionnel de dotation locale | la résistance de l'investissement local au ciseau budgétaire |
| `reglage_censure_assiette`<br>*Assiette de la motion de censure* | choix | choix | 0 → 2 | assiette de la majorité (membres composant / suffrages exprimés / exprimés + quorum) | le poids de l'abstention dans un renversement |
| `reglage_chambre_tiree_au_sort`<br>*Chambre de la durée, membres tirés au sort* | curseur | membres | 0 → 200 | chambre supplémentaire tirée au sort, à veto suspensif | le nombre d'étages où un texte peut être arrêté |
| `reglage_comptes_temps_reel`<br>*Comptes de campagne publiés en temps réel* | interrupteur | bool | 0 → 1 | comptes de campagne publiés pendant la campagne | le délai entre le financement et sa connaissance par l'électeur |
| `reglage_congres_assiette_membres`<br>*Compter les trois cinquièmes sur les membres au Congrès* | interrupteur | bool | 0 → 1 | trois cinquièmes comptés sur les membres composant du Congrès | l'avantage arithmétique de l'abstention au Congrès |
| `reglage_congres_quorum`<br>*Quorum ajouté au Congrès* | curseur | % | 0 → 60 | quorum de votants ajouté au Congrès | le nombre de voix réellement nécessaires pour réviser |
| `reglage_controle_juge_exception`<br>*Contrôle juridictionnel intégral en régime d'exception* | interrupteur | bool | 0 → 1 | contrôle juridictionnel intégral des mesures de police en régime d'exception | la durée de vie d'une mesure prise sans discussion préalable |
| `reglage_controle_loi_referendaire`<br>*Contrôle de constitutionnalité des lois référendaires* | interrupteur | bool | 0 → 1 | la loi référendaire devient contrôlable par le Conseil constitutionnel | le trou de juridiction ouvert par la décision du 6 novembre 1962 |
| `reglage_convention_veto_suspensif`<br>*Veto suspensif d'une convention citoyenne* | interrupteur | bool | 0 → 1 | veto suspensif d'une convention citoyenne, avec seconde lecture obligatoire | un battement de plus dans la navette, sans blocage définitif |
| `reglage_delai_budget_retraite`<br>*Jours retirés au délai de l'Assemblée sur le budget* | curseur | jours | 0 → 20 | jours retirés au délai de l'Assemblée nationale sur la loi de finances | le temps d'examen des recettes avant que le budget ne passe par ordonnance |
| `reglage_delai_motion_49_3`<br>*Heures ajoutées au délai de motion contre un 49.3* | curseur | heures | 0 → 72 | heures ajoutées au délai de dépôt de la motion de censure contre un 49.3 | le temps laissé à l'opposition pour réunir quinze vingtièmes des signatures |
| `reglage_delai_motion_censure`<br>*Jours ajoutés au délai avant le vote de censure* | curseur | jours | 0 → 15 | jours ajoutés au délai avant le vote de la motion | la fenêtre de négociation des abstentions |
| `reglage_delai_senat_budget`<br>*Jours ajoutés au délai du Sénat sur le budget* | curseur | jours | 0 → 15 | jours ajoutés au délai du Sénat sur la loi de finances | la part du calendrier budgétaire où le Sénat peut encore amender |
| `reglage_differentiation_pilotes`<br>*Collectivités autorisées à déroger à titre expérimental* | curseur | collectivités | 0 → 30 | nombre de collectivités en régime d'expérimentation ou de dérogation | l'écart entre le droit applicable d'un territoire à l'autre |
| `reglage_droit_amendement`<br>*Droit d'amendement garanti, irrecevabilité 40 bornée* | interrupteur | bool | 0 → 1 | droit d'amendement garanti, irrecevabilité bornée et motivée | la capacité du Parlement à modifier un texte en navette |
| `reglage_epci_suffrage_direct`<br>*Élection au suffrage direct des intercommunalités* | interrupteur | bool | 0 → 1 | élection au suffrage direct des organes intercommunaux | la chaîne de légitimité entre commune et intercommunalité |
| `reglage_execution_cedh`<br>*Délai contraignant d'exécution des arrêts CEDH* | curseur | jours | 0 → 720 | délai contraignant d'exécution des arrêts, assorti d'astreinte interne | la vitesse à laquelle une condamnation internationale devient un droit interne |
| `reglage_mandat_unique_instances`<br>*Mandat unique non renouvelable pour les autorités indépendantes* | interrupteur | bool | 0 → 1 | mandat unique non renouvelable pour les autorités indépendantes | l'indépendance vis-à-vis du pouvoir qui nomme |
| `reglage_non_retroactivite_in_minus`<br>*Interdiction constitutionnelle de la rétroactivité in minus* | interrupteur | bool | 0 → 1 | interdiction constitutionnelle de rétroactivité in minus | la résistance d'une règle à la loi nouvelle qui l'aggrave |
| `reglage_or_du_deficit`<br>*Marge de déficit inscrite dans la Constitution* | curseur | % PIB | 0 → 3 | marge de déficit structurel inscrite dans la Constitution | la liberté du Parlement de décider de l'effort, contre la trajectoire |
| `reglage_ordre_du_jour_partage`<br>*Part de l'ordre du jour laissée au Parlement* | curseur | % | 0 → 50 | part de l'ordre du jour retirée au Gouvernement, en pourcentage de la session | la fenêtre législative réellement disponible pour les textes du Gouvernement |
| `reglage_outre_mer_competences`<br>*Matières transférées aux collectivités d'outre-mer* | curseur | matières | 0 → 20 | matières dont une collectivité d'outre-mer fixe elle-même la règle | la part du territoire où l'abrogation nationale est impossible |
| `reglage_outre_mer_congres_permament`<br>*Congrès des outre-mer permanent, avec droit d'initiative* | interrupteur | bool | 0 → 1 | instance d'outre-mer permanente dotée d'un droit d'inscription à l'ordre du jour | la transformation d'une consultation en procédure |
| `reglage_parquet_independant`<br>*Parquet nommé sur avis conforme du CSM* | interrupteur | bool | 0 → 1 | parquet nommé sur avis conforme du Conseil supérieur de la magistrature | la disponibilité de l'action publique pour poursuivre un exécutif |
| `reglage_petition_locale_seuil`<br>*Seuil de la pétition locale, en pourcentage des inscrits* | curseur | % | 0 → 20 | seuil national de pétition locale, en pourcentage des inscrits | l'opposabilité du droit de pétition prévu à l'article 72-1 |
| `reglage_plafond_etat_urgence`<br>*Durée maximale totale d'un état d'urgence* | curseur | mois | 0 → 24 | durée maximale totale d'un état d'urgence, sans nouvelle loi | le caractère automatique de la fin du régime d'exception |
| `reglage_publication_avis_ce`<br>*Publication des avis du Conseil d'État sur les projets de loi* | interrupteur | bool | 0 → 1 | publication des avis du Conseil d'État sur les projets de loi | la lecture publique des réserves du juge administratif avant le vote |
| `reglage_recours_irrecevabilite`<br>*Recours collectif contre une irrecevabilité* | interrupteur | bool | 0 → 1 | recours collectif ouvert contre une irrecevabilité prononcée par un président de séance | le contrôle de la qualification au titre de l'article 40 |
| `reglage_referendum_local_automatique`<br>*Référendum local automatique au-delà d'un seuil de pétition* | interrupteur | bool | 0 → 1 | référendum local de plein droit au-delà du seuil | le pouvoir de l'assemblée locale de refuser la consultation |
| `reglage_registre_amendements`<br>*Registre public nominatif des amendements* | interrupteur | bool | 0 → 1 | registre public nominatif des amendements et de leur sort | la traçabilité de la fabrique du texte pendant la navette |
| `reglage_revocation_elue`<br>*Référendum révocatoire local et national* | interrupteur | bool | 0 → 1 | référendum révocatoire déclenché par pétition | la fin de mandat possible avant son terme |
| `reglage_senat_suffrage_direct`<br>*Sénat élu au suffrage universel direct* | interrupteur | bool | 0 → 1 | Sénat élu au suffrage universel direct | la légitimité relative des deux chambres et le poids de leur veto |
| `reglage_seuil_groupes`<br>*Baisse du seuil de constitution des groupes* | curseur | sièges | 0 → 10 | baisse du seuil de constitution des groupes | le nombre de groupes disposant d'une niche et du droit d'enquête |
| `reglage_seuil_saisine_conseil`<br>*Seuil de saisine du Conseil constitutionnel* | choix | choix | 0 → 3 | seuil de saisine a priori du Conseil constitutionnel | la probabilité qu'un texte soit contrôlé avant de promulguer |
| `reglage_stabilite_normative_annees`<br>*Années de stabilité garantie d'une règle structurante* | curseur | années | 0 → 10 | années de stabilité garantie d'une règle structurante | la liberté de la majorité suivante de revenir sur la règle |
| `reglage_subsidiarite_recours`<br>*Recours automatique devant la CJUE sur avis de subsidiarité* | interrupteur | bool | 0 → 1 | recours de droit devant la CJUE sur avis motivé de subsidiarité | la justiciabilité du contrôle de subsidiarité |
| `reglage_verrou_par_engagement_international`<br>*Verrouiller une réforme par un engagement international* | interrupteur | bool | 0 → 1 | réforme adossée à un engagement international ou européen | le juge compétent pour connaître d'un retour en arrière |
| `reglage_verrou_par_loi_organique`<br>*Verrouiller une réforme par une loi organique* | interrupteur | bool | 0 → 1 | réforme renvoyée au statut de loi organique | l'étage de norme nécessaire pour abroger la réforme |
| `reglage_verrou_par_revision`<br>*Verrouiller une réforme par une révision constitutionnelle* | interrupteur | bool | 0 → 1 | réforme inscrite dans la Constitution | l'étage de norme nécessaire pour abroger la réforme |
| `reglage_vote_nominal_obligatoire`<br>*Scrutin public nominal obligatoire sur tout texte structurant* | interrupteur | bool | 0 → 1 | scrutin public nominal obligatoire, sans délégation de vote | le coût politique de l'abstention et de la fossilisation du vote |
| `reglage_vote_par_programme`<br>*Vote par programme et fongibilité assumée* | interrupteur | bool | 0 → 1 | vote par programme et fongibilité assumée | la main-mise du Parlement sur l'allocation des crédits |
| `reglage_vote_prealable_actes_ue`<br>*Vote préalable du Parlement sur un acte délégué européen* | interrupteur | bool | 0 → 1 | résolution préalable du Parlement avant d'engager la France en Conseil | la vitesse de négociation européenne de l'exécutif |

## 4. Seuils recalculés, verrou par verrou

| Verrou | Article | Unité | Droit | Réglages qui le déplacent | Note |
|---|---|---|---:|---|---|
| Voix favorables pour renverser le Gouvernement<br>`censure_voix` | 49 | voix | 289 | — | majorité des 577 membres composant — l'abstention fait obstacle à la motion, elle ne la favorise jamais |
| Délai avant le vote de la motion<br>`censure_delai` | 49 | heures | 48 | — | le délai constitutionnel est de deux jours francs ; chaque jour ajouté est un jour de négociation |
| Délai pour renverser un 49.3 : dépôt de la motion<br>`49_3_delai_motion` | 49 | heures | 24 | — | le temps de dépôt de la motion est le seul temps dont dispose l'opposition contre un 49.3 |
| Usages autorisés pour un texte ordinaire par session<br>`49_3_plafond_texte` | 49 | textes par session | 1 | — | à zéro, tout texte doit être voté : le calendrier redevient une contrainte |
| Députés ou sénateurs pouvant saisir le Conseil<br>`saisine_conseil_signatures` | 61 | signatures | 60 | — | à zéro signatures, le contrôle devient systématique et donc obligatoire pour tous les textes |
| Délai de l'Assemblée nationale en première lecture (PLF)<br>`budget_an_delai` | 47 | jours | 40 | — | en deçà de cinq jours, le délai n'est plus tenable matériellement : plancher appliqué |
| Délai du Sénat saisi en deuxième vague (PLF)<br>`budget_senat_delai` | 47 | jours | 15 | — | chaque jour donné au Sénat est retiré à la commission mixte paritaire |
| Délai au-delà duquel le budget peut être appliqué par ordonnance<br>`budget_delai_total` | 47 | jours | 70 | — | le total commande la date à laquelle le budget est réputé adopté sans vote |
| Base de l'irrecevabilité financière<br>`irrecevabilite_financiere` | 40 | statut de la qualification | 0 | — | 1 : la qualification est contrôlée par un juge, plus par le seul président de séance |
| Délai avant autorisation parlementaire de l'état d'urgence<br>`etat_urgence_delai_parlement` | 36-1 | jours | 12 | — | le délai de saisine du Parlement reste de douze jours : seul le contrôle du juge change |
| Trois cinquièmes du Congrès<br>`congres_voix` | 89 | voix | 555 | — | l'abstention fait baisser le seuil : à 700 votants, 420 voix au lieu de 555 |
| Seuil de constitution des groupes<br>`seuil_groupe_assemblee_nationale` | 51 | députés | 15 | — | chaque groupe de plus, c'est une niche et un droit d'enquête en plus |
| Durée maximale totale de l'état d'urgence<br>`etat_urgence_duree_max_mois` | 36 | mois | 0 | — | aucune durée maximale : des prorogations successives peuvent rendre le régime permanent |

L'arithmétique du Congrès, telle que la couche la calcule (assiette suffrages exprimés contre assiette membres composant) :

| Votants | Sur exprimés | Sur membres | Voix économisées par l'abstention |
|---:|---:|---:|---:|
| 925 | 555 | 555 | 0 |
| 800 | 480 | 555 | 75 |
| 700 | 420 | 555 | 135 |
| 617 | 371 | 555 | 184 |

## 5. Calendriers : ce que les réglages font aux délais de rigueur

Fenêtre législative résiduelle : 150 jours au statu quo, 150 jours avec les réglages en l'état. Textes forcables par session : 1.

| Trajet | Battements | Jours de rigueur | Retard imposable | Tenable ? | Marge |
|---|---:|---:|---:|---|---:|
| Projet de loi ordinaire, procédure avec procédure accélérée | 10 | 160 | 58 | **non** | -10 j |
| Loi de finances : le calendrier qui ne pardonne pas | 8 | 148 | 38 | oui | 2 j |
| Révision constitutionnelle par la voie du Congrès | 6 | 85 | 28 | oui | 65 j |
| Réforme institutionnelle par l'article 11 (voie référendaire) | 5 | 45 | 30 | oui | 105 j |
| Renverser le Gouvernement : le yoyo le plus court | 5 | 2 | 2 | oui | 148 j |
| Faire juger une loi par la QPC : le trajet le plus lent | 5 | 180 | 0 | **non** | -30 j |
| Faire plier une décision locale : le contentieux de l'acte | 4 | 30 | 0 | oui | 120 j |
| RIP : le trajet qui n'a jamais abouti | 4 | 0 | 0 | oui | 150 j |

Les jours sont des délais de rigueur, pas des durées prévisibles : les réglages déplacent la contrainte de calendrier, jamais sa réalité.

## 6. Fentes : solidité avant / après réglages

| Fente | Type | Étage | Solidité | Réglages déclarés | Effet d'un réglage |
|---|---|---|---:|---|---|
| Faire écarter une loi par un juge ordinaire, sans le Conseil<br>`priorite_du_droit_derive` | fente | conventionnel ou droit dérivé de l'UE | 92/92 | `reglage_ancre_ue_reforms`, `reglage_non_retroactivite_in_minus`, `reglage_stabilite_normative_annees`, `reglage_verrou_par_engagement_international` | aucun réglage ne touche cette fente |
| Le Congrès se calcule sur les votants, pas sur les sièges<br>`congres_par_exprimes` | fente | constitutionnel | 82/82 | `reglage_congres_assiette_membres` | aucun réglage ne touche cette fente |
| Ni quorum, ni seuil de participation : le silence est la règle<br>`absence_de_quorum` | fente | constitutionnel | 82/82 | `reglage_congres_quorum` | aucun réglage ne touche cette fente |
| Le Président peut renvoyer la loi au Parlement, sans motif<br>`nouvelle_deliberation_presidentielle` | porte | constitutionnel | 82/82 | `reglage_verrou_par_loi_organique`, `reglage_verrou_par_revision` | aucun réglage ne touche cette fente |
| Entre l'adoption populaire et la promulgation, il n'y a personne<br>`referendum_sans_juge` | fente | conventionnel ou droit dérivé de l'UE | 79/79 | `reglage_controle_loi_referendaire` | aucun réglage ne touche cette fente |
| Le recours contre une irrecevabilité n'est ouvert qu'à celui qui ne le veut pas<br>`irrecevabilite_sans_recours` | droit_sans_juge | constitutionnel | 75/75 | `reglage_droit_amendement`, `reglage_recours_irrecevabilite` | aucun réglage ne touche cette fente |
| Le seuil de pétition locale, personne ne l'a fixé : l'assemblée le fixera<br>`petition_dans_le_reglement` | fente | réglementaire | 75/75 | `reglage_petition_locale_seuil`, `reglage_referendum_local_automatique` | aucun réglage ne touche cette fente |
| L'abstention est un vote de confiance<br>`censure_par_membres` | fente | constitutionnel | 72/72 | `reglage_censure_assiette` | aucun réglage ne touche cette fente |
| Le droit peut être différent quelque part, sans révision<br>`outre_mer_comme_laboratoire` | porte | loi organique | 70/70 | `reglage_differentiation_pilotes`, `reglage_outre_mer_competences` | aucun réglage ne touche cette fente |
| Réécrire la loi par décret, avec l'accord forcé du législateur<br>`defossilisation_sans_vote` | fente | réglementaire | 67/67 | `reglage_registre_amendements`, `reglage_vote_nominal_obligatoire` | aucun réglage ne touche cette fente |
| Contourner l'article 61-1 en attaquant l'acte d'application<br>`toucher_la_loi_par_le_decret` | fente | réglementaire | 67/67 | `reglage_action_de_groupe_administratif`, `reglage_algorithmes_transparents` | aucun réglage ne touche cette fente |
| Le cavalier est irrecevable, et c'est tout<br>`amendement_etrang` | fente | loi ordinaire | 65/65 | `reglage_droit_amendement`, `reglage_seuil_groupes` | aucun réglage ne touche cette fente |

## 7. Les huit indices institutionnels

| Indice | Définition | Valeur | Composantes |
|---|---|---:|---:|
| `capacite_de_blocage_parlementaire` | ce qui est nécessaire pour arrêter un texte : amendement, ordre du jour, niches, seconde chambre | 50/100 | 0 |
| `capacite_de_renversement` | ce qui est nécessaire pour renverser : signatures, assiette, délais laissés à l'opposition | 50/100 | 0 |
| `controle_juridictionnel` | ce qui peut être porté devant un juge : saisine, QPC, parquet, exécution des arrêts | 50/100 | 0 |
| `redevabilite` | ce que l'électeur peut vérifier de son représentant : votes nommés, comptes, avis, registres | 50/100 | 0 |
| `ancrage_des_reformes` | la difficulté de défaire une réforme : étage de norme, engagement, stabilité garantie | 50/100 | 0 |
| `vitesse_legislative` | les textes pouvant être menés à leur terme dans la fenêtre résiduelle, au calendrier réel | 50/100 | 0 |
| `uniformite_du_droit` | l'identité des règles appliquées sur tout le territoire : differentiation, outre-mer, ancrage européen | 50/100 | 0 |
| `capacite_de_revision` | la facilité de réviser la Constitution : Congrès, quorum, assiette, voie référendaire | 50/100 | 0 |

## 8. Quatre expériences, chiffrées par le module

**a) Compter la censure sur les suffrages exprimés**

- `0` (statu quo) → **289 voix**, assiette membres composant l'Assemblée (effectif légal)
- `1` (majorité des exprimés) → **231 voix**, assiette suffrages exprimés
- `2` (exprimés + quorum) → **231 voix**, assiette suffrages exprimés + quorum de présence, quorum 347 votants
- fente `censure_par_membres` : solidité 72 → **0**, neutralisée : True, `irrefutabilite` = None

**b) Deux lectures de plus dans la navette**

- une chambre tirée au sort et un veto suspensif de convention ajoutent un aller-retour chacun : 160 → **300 jours** de délais de rigueur, fenêtre 150 → tenable : **False**
- indice `vitesse_legislative` : 50 → 38.4

**c) Rendre l'ordre du jour parlementaire**

| Part parlementaire | Fenêtre utile | Le budget (148 j de délais) tient-il ? |
|---:|---:|---|
| 0 % | 150 j | oui |
| 25 % | 112 j | **non** |
| 50 % | 75 j | **non** |

**d) Le préréglage « refondation démocratique »**

- 6 réglages institutionnels déplacés par le preset : `reglage_controle_loi_referendaire`, `reglage_petition_locale_seuil`, `reglage_recours_irrecevabilite`, `reglage_registre_amendements`, `reglage_seuil_saisine_conseil`, `reglage_vote_nominal_obligatoire`
- fentes verrouillées : referendum_sans_juge, irrecevabilite_sans_recours ; redevabilité 74/100 ; contrôle juridictionnel 75/100

## 9. API et fichiers

```
GET /api/nuances      ?parametres={"reglage_petition_locale_seuil":8} · ?reglage=…
                      ?article=CONST_ART_49 · ?niveau=Territorial · ?index=… · ?chercher=…
```

| Fichier | Rôle |
|---|---|
| `simulateur/nuances_institutionnelles.py` | la couche : registre des réglages, seuils, délais, fentes, indices, cohérence |
| `simulateur/parametres.py` | les 48 leviers `reglage_*`, bornés et sourcés, dans `LEVIERS` |
| `tests/test_nuances_institutionnelles.py` | 41 cas : neutralité, arithmétique, verrouillages, indices, croisements |
| `api/nuances.py` | fonction sans serveur, générée par `outils/generer-fonctions-api.py` |

## 10. Cohérence mesurée et limites

- réglages du catalogue sans règle : [] ; cibles inconnues : [] ; articles hors registre : 0 ; fentes sans réglage : [] ; indices anormaux : []
- 189 identifiants du registre légal servent de liens croisés, et les 13 seuils recalculés s'appuient sur les 12 fentes et les 8 trajets décrits aux documents 15 et 16
- **non simulé, volontairement** : aucun de ces réglages ne porte de ligne budgétaire (les réformes de procédure sont modélisées par leurs effets, pas par une dépense) ; aucune probabilité d'occurrence n'est calculée — la couche dit ce que le droit imposerait, pas si la majorité le voudrait ; les délais restent des délais de rigueur
- un réglage ne vaut pas promulgation : passer de 289 à 231 voix suppose une révision constitutionnelle, donc l'article 89 et ses propres seuils — que cette même couche permet de durcir : les curseurs se contredisent parfois, c'est le modèle qui tranche, pas l'auteur
