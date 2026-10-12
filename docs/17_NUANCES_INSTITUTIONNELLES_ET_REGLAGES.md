# 17. Nuances institutionnelles : les réglages qui recalculent le droit

> Page produite en relisant le code (`simulateur/nuances_institutionnelles.py`) : les chiffres ci-dessous sont mesurés, pas recopiés. Pour les changer, il faut changer les règles.

Le catalogue compte **156 leviers** en 14 familles, dont **55 réglages institutionnels** (préfixe `reglage_`) répartis sur **9 niveaux** : constitutionnel, parlementaire, budgétaire, judiciaire, territorial, outre-mer, européen, participation, exception. Chacun de ces réglages est un curseur, un interrupteur ou un choix **comme les autres** — il traverse l'interface, les bulles, la page de vérification et les 16 préréglages — et il est de plus branché sur une règle de recalcul : seuils de contre-pouvoir, délais de procédure, fenêtre législative utile, solidité des fentes non écrites et indices institutionnels. Le tout croise **99 articles** de droit positif, **38 verrous**, **12 fentes**, **8 trajets**, **31 mécanismes**, **26 instances** et **15 stratégies** — chaque pièce de chaque registre étant joignable par au moins un réglage, ou explicitement expliquée (voir la section 10).

## 1. Quatre règles qui tiennent tout l'édifice

1. **Un réglage à zéro = statu quo strict.** Aucun curseur institutionnel ne vaut autre chose que « la règle telle qu'elle est écrite » à sa valeur par défaut. Les vérifications `controles_neutres` du module le vérifient : {"seuils_identiques_au_droit": true, "trajets_identiques_au_droit": true, "fentes_inchangees": true, "indices_a_cinquante": true}.
2. **Un indice à 50 = l'état du droit**, ni bien ni mal. Un indice est une amplitude relative : 50 + ce que le réglage rapporte − ce qu'il coûte, borné à [0, 100]. Le brut restant affiché, une saturation est visible (`borne_appliquee`).
3. **Une fente verrouillée n'est pas réfutée.** Le score de défendabilité baisse, la déduction reste vraie, et `irrefutabilite` reste vide : aucun réglage ne rend une conséquence inattaquable.
4. **Rien n'est saisi à la main.** Les seuils partent de `gouvernance_contrepouvoir.seuil()`, les jours de `instances_et_dynamiques.oscillation()` (cohérence vérifiée : True), les scores de `robustesse()`. Les réglages déplacent ces valeurs par des règles écrites en clair.

## 2. Réglages par niveau

Le module ne classe rien à la main : le niveau est celui du levier, et la colonne d'articles compte les identifiants du registre légal cités par ces leviers.

| Niveau | Réglages | dont déplacés | Articles du registre mobilisés |
|---|---|---|---|
| **Constitutionnel** | 10 | 0 | 10 |
| **Parlementaire** | 9 | 0 | 10 |
| **Budgétaire** | 5 | 0 | 6 |
| **Judiciaire** | 9 | 0 | 14 |
| **Territorial** | 5 | 0 | 7 |
| **Outre-mer** | 2 | 0 | 2 |
| **Européen** | 4 | 0 | 7 |
| **Participation** | 7 | 0 | 10 |
| **Exception** | 4 | 0 | 5 |

## 3. Les 55 réglages (préfixe `reglage_`), la règle et l'effet

Tableau produit par `outils/generer-doc-nuances.py` : les colonnes *règle* et *effet* sont celles que le module applique, pas une reformulation.

| Réglage | Type | Unité | Bornes | Règle appliquée | Ce que ça change |
|---|---|---|---|---|---|
| `reglage_49_3_interdiction`<br>*Interdiction du 49.3 hors loi de finances* | interrupteur | bool | 0 → 1 | interdiction du 49.3 hors loi de finances | le nombre de textes adoptables sans vote |
| `reglage_action_de_groupe_administratif`<br>*Action de groupe devant le juge administratif* | interrupteur | bool | 0 → 1 | action de groupe ouverte devant le juge administratif | la possibilité d'attaquer une décision réglementaire en bloc |
| `reglage_algorithmes_transparents`<br>*Audit public des algorithmes à fort impact* | interrupteur | bool | 0 → 1 | audit public des algorithmes à fort impact | la vérifiabilité d'une décision individuelle automatisée |
| `reglage_ancre_ue_reforms`<br>*Ancrer une réforme dans le droit dérivé de l'Union* | curseur | % du champ concerné | 0 → 100 | part de la réforme écrite en droit dérivé de l'Union | la résistance de la réforme à l'abrogation unilatérale |
| `reglage_appel_qpc`<br>*Appel possible du filtre de non-renvoi d'une QPC* | interrupteur | bool | 0 → 1 | appel du filtre de non-renvoi d'une question prioritaire de constitutionnalité | le nombre de droits effectivement justiciables devant le Conseil |
| `reglage_audit_obligatoire_prealable`<br>*Audit obligatoire avant toute réforme structurelle* | interrupteur | bool | 0 → 1 | avis public d'une juridiction supérieure avant dépôt d'une réforme structurelle | la qualité de l'information disponible pendant la navette |
| `reglage_autonomie_financiere_garantie`<br>*Plancher constitutionnel de dotation locale* | curseur | % | 0 → 30 | plancher constitutionnel de dotation locale | la résistance de l'investissement local au ciseau budgétaire |
| `reglage_cee_consultation_prealable`<br>*Consultation préalable obligatoire du CESE sur les programmations* | curseur | jours | 0 → 30 | jours de consultation obligatoire du Conseil économique, social et environnemental avant le dépôt d'un texte de programmation | le délai ajouté en amont et le poids de l'avis dans la discussion |
| `reglage_censure_assiette`<br>*Assiette de la motion de censure* | choix | choix | 0 → 2 | assiette de la majorité (membres composant / suffrages exprimés / exprimés + quorum) | le poids de l'abstention dans un renversement |
| `reglage_chambre_tiree_au_sort`<br>*Chambre de la durée, membres tirés au sort* | curseur | membres | 0 → 200 | chambre supplémentaire tirée au sort, à veto suspensif | le nombre d'étages où un texte peut être arrêté |
| `reglage_commission_enquete_droit_de_bloc`<br>*Deux commissions d'enquête garanties par groupe et par session* | interrupteur | bool | 0 → 1 | une commission d'enquête garantie par groupe et par session, en plus de celle du droit en vigueur | le nombre d'enquêtes parlementaires réellement constituables sans négociation |
| `reglage_comptes_temps_reel`<br>*Comptes de campagne publiés en temps réel* | interrupteur | bool | 0 → 1 | comptes de campagne publiés pendant la campagne | le délai entre le financement et sa connaissance par l'électeur |
| `reglage_congres_assiette_membres`<br>*Compter les trois cinquièmes sur les membres au Congrès* | interrupteur | bool | 0 → 1 | trois cinquièmes comptés sur les membres composant du Congrès | l'avantage arithmétique de l'abstention au Congrès |
| `reglage_congres_quorum`<br>*Quorum ajouté au Congrès* | curseur | % | 0 → 60 | quorum de votants ajouté au Congrès | le nombre de voix réellement nécessaires pour réviser |
| `reglage_controle_juge_exception`<br>*Contrôle juridictionnel intégral en régime d'exception* | interrupteur | bool | 0 → 1 | contrôle juridictionnel intégral des mesures de police en régime d'exception | la durée de vie d'une mesure prise sans discussion préalable |
| `reglage_controle_loi_referendaire`<br>*Contrôle de constitutionnalité des lois référendaires* | interrupteur | bool | 0 → 1 | la loi référendaire devient contrôlable par le Conseil constitutionnel | le trou de juridiction ouvert par la décision du 6 novembre 1962 |
| `reglage_convention_veto_suspensif`<br>*Veto suspensif d'une convention citoyenne* | interrupteur | bool | 0 → 1 | veto suspensif d'une convention citoyenne, avec seconde lecture obligatoire | un battement de plus dans la navette, sans blocage définitif |
| `reglage_declassification_legislative`<br>*Délai de décision sur une irrecevabilité de compétence* | curseur | jours | 0 → 30 | jours ajoutés au délai laissé au Conseil pour statuer sur une déclassification ou une irrecevabilité de compétence | la vitesse à laquelle un domaine revient au règlement et le Parlement reprend la main |
| `reglage_defenseur_saisine_directe`<br>*Saisine directe du Défenseur des droits* | interrupteur | bool | 0 → 1 | saisine directe du Défenseur des droits par tout justiciable, sans intermédiaire d'un parlementaire | le nombre de réclamations instruites et de décisions correctives obtenues |
| `reglage_delai_budget_retraite`<br>*Jours retirés au délai de l'Assemblée sur le budget* | curseur | jours | 0 → 20 | jours retirés au délai de l'Assemblée nationale sur la loi de finances | le temps d'examen des recettes avant que le budget ne passe par ordonnance |
| `reglage_delai_motion_49_3`<br>*Heures ajoutées au délai de motion contre un 49.3* | curseur | heures | 0 → 72 | heures ajoutées au délai de dépôt de la motion de censure contre un 49.3 | le temps laissé à l'opposition pour réunir quinze vingtièmes des signatures |
| `reglage_delai_motion_censure`<br>*Jours ajoutés au délai avant le vote de censure* | curseur | jours | 0 → 15 | jours ajoutés au délai avant le vote de la motion | la fenêtre de négociation des abstentions |
| `reglage_delai_senat_budget`<br>*Jours ajoutés au délai du Sénat sur le budget* | curseur | jours | 0 → 15 | jours ajoutés au délai du Sénat sur la loi de finances | la part du calendrier budgétaire où le Sénat peut encore amender |
| `reglage_differentiation_pilotes`<br>*Collectivités autorisées à déroger à titre expérimental* | curseur | collectivités | 0 → 30 | nombre de collectivités en régime d'expérimentation ou de dérogation | l'écart entre le droit applicable d'un territoire à l'autre |
| `reglage_droit_amendement`<br>*Droit d'amendement garanti, irrecevabilité 40 bornée* | interrupteur | bool | 0 → 1 | droit d'amendement garanti, irrecevabilité bornée et motivée | la capacité du Parlement à modifier un texte en navette |
| `reglage_epci_suffrage_direct`<br>*Élection au suffrage direct des intercommunalités* | interrupteur | bool | 0 → 1 | élection au suffrage direct des organes intercommunaux | la chaîne de légitimité entre commune et intercommunalité |
| `reglage_execution_cedh`<br>*Délai contraignant d'exécution des arrêts CEDH* | curseur | jours | 0 → 720 | délai contraignant d'exécution des arrêts, assorti d'astreinte interne | la vitesse à laquelle une condamnation internationale devient un droit interne |
| `reglage_haute_cour_non_parlementaire`<br>*Haute Cour composée de juges non parlementaires* | interrupteur | bool | 0 → 1 | Haute Cour composée de juges et non de parlementaires, sans majorité qualifiée dans les assemblées | la majorité nécessaire pour réunir la Haute Cour et pour prononcer une destitution |
| `reglage_mandat_unique_instances`<br>*Mandat unique non renouvelable pour les autorités indépendantes* | interrupteur | bool | 0 → 1 | mandat unique non renouvelable pour les autorités indépendantes | l'indépendance vis-à-vis du pouvoir qui nomme |
| `reglage_non_retroactivite_in_minus`<br>*Interdiction constitutionnelle de la rétroactivité in minus* | interrupteur | bool | 0 → 1 | interdiction constitutionnelle de rétroactivité in minus | la résistance d'une règle à la loi nouvelle qui l'aggrave |
| `reglage_nouvelle_deliberation_supprimee`<br>*Supprimer le droit de nouvelle délibération* | interrupteur | bool | 0 → 1 | suppression du droit présidentiel de nouvelle délibération | les quinze jours pendant lesquels une loi votée peut être renvoyée en discussion |
| `reglage_or_du_deficit`<br>*Marge de déficit inscrite dans la Constitution* | curseur | % PIB | 0 → 3 | marge de déficit structurel inscrite dans la Constitution | la liberté du Parlement de décider de l'effort, contre la trajectoire |
| `reglage_ordre_du_jour_partage`<br>*Part de l'ordre du jour laissée au Parlement* | curseur | % | 0 → 50 | part de l'ordre du jour retirée au Gouvernement, en pourcentage de la session | la fenêtre législative réellement disponible pour les textes du Gouvernement |
| `reglage_outre_mer_competences`<br>*Matières transférées aux collectivités d'outre-mer* | curseur | matières | 0 → 20 | matières dont une collectivité d'outre-mer fixe elle-même la règle | la part du territoire où l'abrogation nationale est impossible |
| `reglage_outre_mer_congres_permament`<br>*Congrès des outre-mer permanent, avec droit d'initiative* | interrupteur | bool | 0 → 1 | instance d'outre-mer permanente dotée d'un droit d'inscription à l'ordre du jour | la transformation d'une consultation en procédure |
| `reglage_parquet_independant`<br>*Parquet nommé sur avis conforme du CSM* | interrupteur | bool | 0 → 1 | parquet nommé sur avis conforme du Conseil supérieur de la magistrature | la disponibilité de l'action publique pour poursuivre un exécutif |
| `reglage_petition_locale_seuil`<br>*Seuil de la pétition locale, en pourcentage des inscrits* | curseur | % | 0 → 20 | seuil national de pétition locale, en pourcentage des inscrits | l'opposabilité du droit de pétition prévu à l'article 72-1 |
| `reglage_plafond_etat_urgence`<br>*Durée maximale totale d'un état d'urgence* | curseur | mois | 0 → 24 | durée maximale totale d'un état d'urgence, sans nouvelle loi | le caractère automatique de la fin du régime d'exception |
| `reglage_procedure_acceleree_encadree`<br>*Délai plancher avant délibération en procédure accélérée* | curseur | jours | 0 → 45 | jours ajoutés au délai minimal avant délibération d'un texte engagé en procédure accélérée | le temps réellement laissé au Sénat, aux amendements et à la publicité du texte |
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

Les verrous dont un réglage déplace le nombre, avec la valeur de droit et la valeur réglée au statu quo (tous les écarts sont donc à zéro tant qu'aucun curseur ne bouge) :

| Verrou | Nom | Article | Droit | Réglé | Écart | Unité | Réglages |
|---|---|---|---|---|---|---|---|
| `censure_voix` | Voix favorables pour renverser le Gouvernement | 49 | 289 | 289 | — | voix | — |
| `censure_delai` | Délai avant le vote de la motion | 49 | 48 | 48 | — | heures | — |
| `49_3_delai_motion` | Délai pour renverser un 49.3 : dépôt de la motion | 49 | 24 | 24 | — | heures | — |
| `49_3_plafond_texte` | Usages autorisés pour un texte ordinaire par session | 49 | 1 | 1 | — | textes par session | — |
| `saisine_conseil_signatures` | Députés ou sénateurs pouvant saisir le Conseil | 61 | 60 | 60 | — | signatures | — |
| `budget_an_delai` | Délai de l'Assemblée nationale en première lecture (PLF) | 47 | 40 | 40 | — | jours | — |
| `budget_senat_delai` | Délai du Sénat saisi en deuxième vague (PLF) | 47 | 15 | 15 | — | jours | — |
| `budget_delai_total` | Délai au-delà duquel le budget peut être appliqué par ordonnance | 47 | 70 | 70 | — | jours | — |
| `petition_locale` | Pétition demandant l'inscription à l'ordre du jour local | 72-1 | 0 | 0 | — | % des inscrits | — |
| `referendum_local` | Référendum décisionnel local | 72-1 | 0 | 0 | — | régime | — |
| `irrecevabilite_financiere` | Base de l'irrecevabilité financière | 40 | 0 | 0 | — | statut de la qualification | — |
| `etat_urgence_delai_parlement` | Délai avant autorisation parlementaire de l'état d'urgence | 36-1 | 12 | 12 | — | jours | — |
| `procedure_acceleree_delai` | Délai minimal avant délibération (procédure accélérée) | 42 | 15 | 15 | — | jours | — |
| `promulgation_nouvelle_deliberation` | Délai laissé au Président pour demander une nouvelle délibération | 10 | 15 | 15 | — | jours | — |
| `commission_enquete_signature` | Demandes de commission d'enquête garanties par session | 51-2 | 1 | 1 | — | commissions garanties par session | — |
| `haute_cour_assemblees` | Voix dans chaque assemblée pour réunir la Haute Cour | 68 | 385 | 385 | — | voix par assemblée | — |
| `haute_cour_destitution` | Voix à la Haute Cour pour prononcer la destitution | 68 | 617 | 617 | — | voix | — |
| `lois_programmation_saisine_cee` | Saisine pour avis du CESE (plans et programmations) | 70 | 0 | 0 | — | jours de consultation | — |
| `irrecevabilite_competence_delai` | Délai du Conseil constitutionnel saisi d'une irrecevabilité de compétence | 41 | 8 | 8 | — | jours | — |
| `congres_revision` | Suffrages exprimés au Congrès pour approuver une révision | 89 | 555 | 555 | — | voix | — |
| `seuil_groupe_assemblee_nationale` | Seuil de constitution des groupes | 51 | 15 | 15 | — | députés | — |
| `etat_urgence_duree_max_mois` | Durée maximale totale de l'état d'urgence | 36 | 0 | 0 | — | mois | — |

## 4 bis. Les verrous qu'aucun réglage ne déplace, et pourquoi

Un trou assumé et daté est une décision ; un trou non dit est une omission. Ces 18 verrous sont hors d'atteinte d'un curseur de politique publique, et la raison est écrite ici plutôt que laissée à l'interprétation :

- `censure_plafond_motions` — Motions de censure par session ordinaire : limitation du nombre de motions par session, touchée seulement par une révision de l'article 51 — le simulateur la décrète hors jeu

- `censure_signatures` — Signatures nécessaires pour déposer une motion de censure : le dixième des membres est une protection contre l'obstruction : le faire varier ne peut pas se décréter par un curseur de politique publique

- `cmp_composition` — Membres de la commission mixte paritaire : vingt-quatre membres de la CMP : chiffre du règlement, déjà au statu quo

- `dissolution_carence` — Délai pendant lequel une nouvelle dissolution est interdite : le Président n'a aucune obligation de dissoudre après une censure : aucun réglage du dépôt ne transforme une absence d'obligation en obligation

- `etat_siege_delai_parlement` — Délai avant autorisation parlementaire de l'état de siège : l'état de siège ne peut pas être prorogé sans loi : règle absolue, aucun seuil à déplacer

- `grace_regime` — Régime du droit de grâce : la grâce présidentielle n'a plus de contre-pouvoir chiffré depuis 2008

- `nomination_veto` — Blocage d'une nomination en conseil des ministres : le veto du Président sur les nominations (art. 13) n'a pas d'équivalent chiffré dans le modèle

- `opex_delai_autorisation` — Durée d'intervention armée sans autorisation du Parlement : les quatre mois d'opérations extérieures : délai de information du Parlement, non négociable politiquement

- `plfss_delai_total` — Délai global pour le projet de loi de financement de la sécurité sociale : calendrier social aligné sur celui des finances : le réglage est porté par `reglage_delai_budget_retraite`, pas dupliqué

- `presidentielle_parrainages` — Présentations pour être candidat à l'élection présidentielle : les cinquante parrainages sont un filtre constitutionnel, pas une mesure de politique publique

- `referendum_promulgation` — Délai de promulgation de la loi votée ou adoptée en référendum : le délai de promulgation après référendum n'est pas un seuil politique : il n'existe pas de levier pour le négocier

- `rip_signatures_electeurs` — Soutien demandé aux électeurs pour un RIP : le dixième des électeurs est déjà modulé par les preset `reforme_ric` ; pas de double comptage

- `rip_signatures_parlement` — Signatures parlementaires pour un RIP (un cinquième) : un cinquième des membres plus dix départements : seuil du RIP, déjà piloté par `reforme_ric` côté moteur

- `saisine_conseil_delai` — Délai de jugement du Conseil constitutionnel saisi avant promulgation : les trente jours du contrôle a priori sont un calendrier, pas un arbitrage : seul le constituant y touche

- `saisine_conseil_urgence` — Délai réduit en cas d'urgence (budget) : le délai réduit en cas d'urgence est la contrepartie du délai normal

- `session_cloture_delai` — Durée maximale d'une session extraordinaire demandée par les députés : la clôture relève du règlement, pas de la loi

- `session_extraordinaire_signatures` — Députés pouvant décider la réunion en session extraordinaire : un dixième des membres pour ouvrir une session extraordinaire : seuil de protection, jamais négocié

- `vacance_delai_scrutin` — Délai pour procéder à une nouvelle élection présidentielle : les vingt à cinquante jours pour élire un nouveau Président : calendrier, pas arbitrage

## 5. Calendriers : ce que les réglages font aux délais de rigueur

Huit trajets, leurs jours de rigueur et leur tenue dans la fenêtre résiduelle de la session. Le calendrier n'est pas un ornement : c'est lui qui décide si une réforme tient dans un quinquennat.

| Trajet | Nom | Catégorie | Droit (jours) | Réglé (jours) | Fenêtre |
|---|---|---|---|---|---|
| `projet_ordinaire` | Projet de loi ordinaire, procédure avec procédure accélérée | legislatif | 160 | 160 | **HORS FENÊTRE** |
| `budget` | Loi de finances : le calendrier qui ne pardonne pas | budgetaire | 148 | 148 | tenable |
| `revision_congres` | Révision constitutionnelle par la voie du Congrès | constitutionnel | 85 | 85 | tenable |
| `revision_referendum` | Réforme institutionnelle par l'article 11 (voie référendaire) | constitutionnel | 45 | 45 | tenable |
| `renversement` | Renverser le Gouvernement : le yoyo le plus court | exception | 2 | 2 | tenable |
| `controle_juge` | Faire juger une loi par la QPC : le trajet le plus lent | controle | 180 | 180 | **HORS FENÊTRE** |
| `compte_a_rebours_local` | Faire plier une décision locale : le contentieux de l'acte | controle | 30 | 30 | tenable |
| `initiative_citoyenne` | RIP : le trajet qui n'a jamais abouti | constitutionnel | 0 | 0 | tenable |

Fenêtre résiduelle : 150 jours au statu quo, 150 réglés. Textes forcables par session : 1. Cohérence des jours avec l'oscillation des assemblées : `True`.

## 6. Fentes : solidité avant / après réglages

Solidité avant / après réglages, notée en défendabilité (0-100) et jamais en irréfragabilité : une fente n'est jamais « fermée », elle est rendue inutilisable par un réglage qui la précède dans le trajet.

| Fente | Nom | Étage | Profite à | Solidité droit | Solidité réglée | État | Réglages |
|---|---|---|---|---|---|---|---|
| `priorite_du_droit_derive` | Faire écarter une loi par un juge ordinaire, sans le Conseil | conventionnel ou droit dérivé de l'UE | aux requérants | 92 | 92 | ouverte | — |
| `congres_par_exprimes` | Le Congrès se calcule sur les votants, pas sur les sièges | constitutionnel | à qui peut réunir une majorité absolue sans l'avoir | 82 | 82 | ouverte | — |
| `absence_de_quorum` | Ni quorum, ni seuil de participation : le silence est la règle | constitutionnel | à qui gagne sans mobiliser | 82 | 82 | ouverte | — |
| `nouvelle_deliberation_presidentielle` | Le Président peut renvoyer la loi au Parlement, sans motif | constitutionnel | au chef de l'État qui veut gagner un cycle | 82 | 82 | ouverte | — |
| `referendum_sans_juge` | Entre l'adoption populaire et la promulgation, il n'y a personne | conventionnel ou droit dérivé de l'UE | à l'exécutif qui veut imposer une réforme institutionnelle | 79 | 79 | ouverte | — |
| `irrecevabilite_sans_recours` | Le recours contre une irrecevabilité n'est ouvert qu'à celui qui ne le veut pas | constitutionnel | à la majorité de séance | 75 | 75 | ouverte | — |
| `petition_dans_le_reglement` | Le seuil de pétition locale, personne ne l'a fixé : l'assemblée le fixera | réglementaire | aux minorités locales | 75 | 75 | ouverte | — |
| `censure_par_membres` | L'abstention est un vote de confiance | constitutionnel | au Gouvernement | 72 | 72 | ouverte | — |
| `outre_mer_comme_laboratoire` | Le droit peut être différent quelque part, sans révision | loi organique | aux réformateurs qui n'ont pas la majorité nationale | 70 | 70 | ouverte | — |
| `defossilisation_sans_vote` | Réécrire la loi par décret, avec l'accord forcé du législateur | réglementaire | au Gouvernement | 67 | 67 | ouverte | — |
| `toucher_la_loi_par_le_decret` | Contourner l'article 61-1 en attaquant l'acte d'application | réglementaire | aux requérants | 67 | 67 | ouverte | — |
| `amendement_etrang` | Le cavalier est irrecevable, et c'est tout | loi ordinaire | à qui veut faire voter un amendement sans débat propre | 65 | 65 | ouverte | — |

## 7. Les huit indices institutionnels

Les 8 indices de la couche : base 50 au statu quo, somme pondérée des apports des réglages déplacés, bornée à [0, 100]. Un coefficient négatif est une perte, pas un bug.

| Indice | Nom | Valeur | Définition | Réglages contributeurs |
|---|---|---|---|---|
| `capacite_de_blocage_parlementaire` | capacite de blocage parlementaire | 50 | ce qui est nécessaire pour arrêter un texte : amendement, ordre du jour, niches, seconde chambre | 22 |
| `capacite_de_renversement` | capacite de renversement | 50 | ce qui est nécessaire pour renverser : signatures, assiette, délais laissés à l'opposition | 6 |
| `controle_juridictionnel` | controle juridictionnel | 50 | ce qui peut être porté devant un juge : saisine, QPC, parquet, exécution des arrêts | 17 |
| `redevabilite` | redevabilite | 50 | ce que l'électeur peut vérifier de son représentant : votes nommés, comptes, avis, registres | 18 |
| `ancrage_des_reformes` | ancrage des reformes | 50 | la difficulté de défaire une réforme : étage de norme, engagement, stabilité garantie | 9 |
| `vitesse_legislative` | vitesse legislative | 50 | les textes pouvant être menés à leur terme dans la fenêtre résiduelle, au calendrier réel | 23 |
| `uniformite_du_droit` | uniformite du droit | 50 | l'identité des règles appliquées sur tout le territoire : differentiation, outre-mer, ancrage européen | 11 |
| `capacite_de_revision` | capacite de revision | 50 | la facilité de réviser la Constitution : Congrès, quorum, assiette, voie référendaire | 3 |

## 7 bis. Les cinq strates

Les cinq strates du simulateur (celles des bulles et de l'onglet « Effets comparés par strate »), lues du point de vue institutionnel : la strate est déduite des thèmes d'effet de chaque réglage, jamais déclarée à la main.

| Strate | Niveau | Réglages | Déplacés | Verrous touchés | Fentes verrouillées |
|---|---|---|---|---|---|
| 1 | communes, intercommunalités, départements, régions | 13 | 0 | 0 | 0 |
| 2 | nation : loi, règlement, budgétaire | 55 | 0 | 0 | 0 |
| 3 | Union européenne et zone euro | 21 | 0 | 0 | 0 |
| 4 | mondial : commerce, dette, énergie | 19 | 0 | 0 | 0 |
| 5 | géopolitique : tensions et chokepoints | 5 | 0 | 0 | 0 |

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
| `simulateur/parametres.py` | les 55 leviers `reglage_*`, bornés et sourcés, dans `LEVIERS` |
| `tests/test_nuances_institutionnelles.py` | 41 cas : neutralité, arithmétique, verrouillages, indices, croisements |
| `api/nuances.py` | fonction sans serveur, générée par `outils/generer-fonctions-api.py` |

## 10. Cohérence mesurée et limites

Contrôle exécuté par `coherence_nuances()` — le même que celui qu'exécute la suite de tests. Tant que toutes les lignes ci-dessous disent « aucun trou », la couche est sans angle mort ; la moindre liste non vide est une faute à corriger dans le module, pas dans ce document.

| Garde-fou | Résultat |
|---|---|
| `apports_sans_reglage` | aucun trou |
| `articles_hors_registre` | aucun trou |
| `cibles_inconnues` | aucun trou |
| `connaissances_inaccessibles` | aucun trou |
| `exemptions_perimees` | aucun trou |
| `exemptions_vides` | aucun trou |
| `fentes_inaccessibles_d_un_reglage` | aucun trou |
| `fentes_non_ciblees` | aucun trou |
| `indices_anormaux` | aucun trou |
| `reglages_inconnus` | aucun trou |
| `reglages_sans_article` | aucun trou |
| `reglages_sans_cible_chiffree` | aucun trou |
| `reglages_sans_regle` | aucun trou |
| `reglages_sans_strate` | aucun trou |
| `seuils_insensibles_perimes` | aucun trou |
| `strates_couvertes` | **5** : `1`, `2`, `3`, `4`, `5` |
| `trajets_sans_reglage` | aucun trou |
| `verrous_doublement_classes` | aucun trou |
| `verrous_doublement_classes_note` | aucun trou |
| `verrous_inventes` | aucun trou |
| `verrous_non_expliques` | aucun trou |
| `verrous_reglables_sans_explication` | aucun trou |

Accessibilité des registres, déduite des citations d'articles des modules `gouvernance_contrepouvoir` et `instances_et_dynamiques` :

| Registre | Total | Joignables par un réglage |
|---|---|---|
| `verrou` | 38 | 30 |
| `fente` | 12 | 12 |
| `trajet` | 8 | 8 |
| `mecanisme` | 31 | 31 |
| `instance` | 26 | 26 |
| `strategie` | 15 | 15 |

**Limites.** 0 réglage(s) sans cible chiffrée, 55 réglages au catalogue, 18 verrous expliqués hors réglage. Le module ne prétend pas simuler une révision constitutionnelle : il déplace les nombres que le droit laisse déplacer, et dit explicitement ceux qu'il ne peut pas toucher.
