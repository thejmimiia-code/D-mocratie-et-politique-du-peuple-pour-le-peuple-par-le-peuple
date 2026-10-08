# Plan d'audit global et de mise en cohérence du simulateur

Document de travail. Il décrit de A à Z ce qui doit être audité, complété et
vérifié contre le droit et les données publiques de la République française,
avec l'état des lieux **mesuré** au moment de la rédaction.

## 0. Inventaire mesuré (état du dépôt à la date de rédaction)

| Élément | Mesure |
|---|---|
| Code Python du simulateur (`simulateur/`) | ≈ 18 300 lignes |
| Leviers de politique publique (`simulateur/parametres.py`) | 101 leviers, 14 familles, 14 presets |
| Lignes budgétaires suivies (`simulateur/domaines.py`) | `LIGNES`, `DOMAINES`, `SPECS` (voir le module) |
| Articles du registre juridique (`simulateur/reglements_lois.py`) | **49 articles**, 25 codes ou textes distincts |
| Documents Markdown du dépôt | 34 (dont 29 dans `docs/`) |
| Tests unitaires | 543 (suite complète, OK) |

## 1. Constats vérifiés (à traiter en priorité)

**Statut** : 1.1 et 1.2 traités (voir section 9). 1.3 à faire, levier par levier.

### 1.1 Lien juridique absent du moteur (manque structurel)

- **0 article du registre n'est référencé par un levier.** Le fichier
  `parametres.py` ne cite aucun identifiant de `REGISTRE_LEGAL`.
- Le champ `source` des leviers (et des `LigneBudgetaire`) est du **texte libre**
  (ex. « Article 278-0 bis CGI ; … »). Il n'est pas relié au registre et ne peut
  pas être vérifié automatiquement.
- Conséquence : les « liens croisés dynamiques » entre un levier, son article de
  loi et sa strate n'existent pas encore.

**Correction proposée** : ajouter au dataclass `Levier` un champ
`articles: tuple[str, ...] = ()` (identifiants de `REGISTRE_LEGAL`), puis un test
qui échoue si un identifiant n'existe pas dans le registre. Affichage dans la
page : la bulle du levier liste ses articles et leur texte intégral.

### 1.2 Incohérences dans le registre juridique (coquilles)

- Strate : `Europe` (4 articles) et `Européen` (2 articles) désignent la même
  chose. Il faut une seule valeur.
- Intitulés de codes en casse inégale : « Code général des impôts » et
  « Code Général des Impôts » coexistent ; « Code de l'artisanat & Code de
  commerce » et « Code Général des Impôts & Directive (UE) 2022/2523 » mélangent
  deux textes dans un seul champ.
- Le champ `strate_impactee` mélange des niveaux (`Transversal`, `Mondial`) qui ne
  sont pas des échelons du modèle gigogne (`Local`, `National`, `Europe`,
  `Mondial`). Il faut une liste fermée et documentée.

### 1.3 Sources des chiffrages à vérifier

Les `source` de leviers sont souvent des ordres de grandeur sans année ni lien
(ex. « ~5,7 millions de ménages bénéficiaires ; montant moyen ≈ 150 € »). Chaque
valeur de référence (`base_mde`, `defaut`, `minimum`, `maximum`) doit porter :
la source exacte, l'année de référence, et un lien vérifiable.

## 2. Périmètre juridique à couvrir (A à Z)

Ordre hiérarchique des normes, du plus haut au plus bas. Pour chaque niveau :
le texte de référence, les articles qui touchent la simulation, et l'état actuel.

1. **Bloc de constitutionnalité** : Constitution du 4 octobre 1958 (et ses
   révisions), Déclaration des droits de l'homme et du citoyen de 1789, Préambule
   de 1946, Charte de l'environnement de 2004.
2. **Lois organiques** : loi organique relative aux lois de finances (LOLF,
   n° 2001-692), loi organique relative à la programmation et à la gouvernance
   des finances publiques (2012), loi organique sur le référendum d'initiative
   partagée et les référendums (articles 11 et 89 de la Constitution).
3. **Lois de finances et de financement** : loi de finances de l'année (LFI),
   loi de financement de la sécurité sociale (LFSS), loi de programmation des
   finances publiques (LPFP), loi de programmation militaire (ex. loi
   n° 2023-703 du 1er août 2023, déjà présente).
4. **Codes** : Code général des impôts (CGI), Livre des procédures fiscales,
   Code de la sécurité sociale, Code général des collectivités territoriales
   (CGCT), Code de la commande publique, Code du travail, Code de l'éducation,
   Code de la santé publique, Code de l'environnement, Code de l'énergie, Code
   pénal, Code de la consommation, Code de commerce, Code rural et de la pêche
   maritime, Code des relations entre le public et l'administration.
5. **Décrets, arrêtés, circulaires** : seulement quand ils fixent un chiffre
   utilisé par le simulateur (barèmes, taux, plafonds, SMIC, point d'indice).
6. **Droit de l'Union européenne** : Traité sur l'Union européenne (TUE), Traité
   sur le fonctionnement de l'UE (TFUE), règlements et directives cités (Pacte de
   stabilité et de croissance, CRR, Chips Act, NIS 2, eIDAS, etc.).
7. **Engagements internationaux** : traité de l'Atlantique Nord, traité de
   non-prolifération (1968), convention de Montego Bay (1982), accords OMC/GATT.
8. **Jurisprudence** : décisions du Conseil constitutionnel et du Conseil d'État
   qui bornent un levier (ex. principes d'égalité devant l'impôt).

**Sources officielles à utiliser comme référence** (à citer avec la date de
consultation) :

- Légifrance : https://www.legifrance.gouv.fr (lois, codes, décrets, jurisprudence)
- Conseil constitutionnel : https://www.conseil-constitutionnel.fr
- EUR-Lex (droit de l'UE) : https://eur-lex.europa.eu
- Budget de l'État (PLF, LFI, rapports annexés) : https://www.budget.gouv.fr
- Insee (comptes nationaux, séries) : https://www.insee.fr
- Cour des comptes (situation et perspectives des finances publiques) : https://www.ccomptes.fr
- Données ouvertes de l'État : https://www.data.gouv.fr

## 3. Couverture par échelon (modèle gigogne)

Pour chaque échelon, lister les leviers existants, les manques, et les
interactions à câbler vers l'échelon supérieur.

| Échelon | Exemples de manques à examiner |
|---|---|
| Local : communes, EPCI, départements, régions | Dotations (DGF), fiscalité locale, compétences du CGCT, pouvoir d'achat local |
| National : État, Sécurité sociale, collectivités | Recettes et dépenses par mission LOLF, dette, déficit, agences |
| Institutions et démocratie | RIC (loi organique), mandats, transparence des comptes, chambres consulaires |
| Europe | Contributions au budget UE, règles budgétaires, marchés financiers |
| Mondial | Prix de l'énergie, risques géopolitiques, commerce, taux d'intérêt de référence |

## 4. Méthode pour chaque manque détecté

1. **Identifier** le texte ou le fait réel (chiffre, règle, institution).
2. **Vérifier** sa source officielle, son année et son lien.
3. **Créer** le levier (curseur, choix, interrupteur ou cible) avec : libellé,
   description, unité, bornes, défaut, `source`, `articles`, `domaines` et
   `effets_directs`.
4. **Câbler** les liens croisés : ligne budgétaire, domaine, strate, article.
5. **Tester** : le levier apparaît dans le catalogue, la simulation le prend en
   compte, et la validation des liens (étape 1.1) passe.
6. **Documenter** dans `docs/` et dans le lexique (`simulateur/lexique.py`).

## 5. Accessibilité et transparence (exigence transversale)

- Référentiel : **RGAA 4.1** (Référentiel général d'amélioration de l'accessibilité)
  et **WCAG 2.2 niveau AA**, à contrôler sur la page `index.html` et sur
  `simulateur/interface.py`.
- Chaque chiffre affiché doit pouvoir être remonté à sa source (lien vers
  l'article ou la publication officielle).
- Langage clair : le lexique doit définir chaque terme technique.
- Aucune dépendance qui impose un compte ou un outil propriétaire pour lire le
  simulateur.

## 6. Points de brainstorming ouverts

- **Granularité des leviers** : faut-il un levier par article de loi, ou un
  levier par décision politique qui s'appuie sur plusieurs articles ?
- **Années de référence** : les chiffres doivent-ils tous porter sur une même
  année (ex. 2025), ou chacun sur sa dernière année publiée ?
- **Version des textes** : figer une date de consultation pour chaque article,
  car les textes de Légifrance évoluent.
- **Statut du modèle** : le simulateur est une aide à la réflexion, pas un outil
  de prévision. Chaque sortie doit le rappeler.

## 7. Ordre d'exécution proposé

1. Corriger les coquilles du registre (1.2) — faible risque, pas de changement de résultat.
2. Ajouter le champ `articles` et sa validation (1.1) — pas de changement de résultat.
3. Vérifier les sources et les chiffres de référence (1.3), levier par levier.
4. Compléter le registre juridique par niveau (section 2), en commençant par les
   codes qui touchent un levier existant.
5. Combler les manques par échelon (section 3), levier par levier, avec tests.
6. Audit d'accessibilité (section 5) et mise à jour de la documentation.

## 8. Limites

- Ce plan ne remplace pas une relecture par un juriste ni par un économiste de
  finances publiques. Les textes sont à citer, pas à réinterpréter.
- Les chiffres changent chaque année (lois de finances). Chaque valeur doit être
  datée.
- Les changements de valeurs modifient les résultats du simulateur et les tests
  qui les figent : ils doivent être faits par lots, avec revue.

## 9. Journal d'exécution

### Lot 1 — coquilles du registre (fait)

- `Européen` remplacé par `Europe` (2 articles) ; liste fermée `STRATES_VALIDES`
  et test associé.
- « Code Général des Impôts & Directive (UE) 2022/2523 » : intitulé séparé en
  « Code général des impôts (transposition de la directive (UE) 2022/2523) ».
  Source : Légifrance / EUR-Lex, dispositions au CGI à partir de l'article 223 VJ.
- « Code de l'artisanat & Code de commerce » (L. 711-1) : corrigé en
  « Code de commerce ». L. 711-1 concerne les chambres de commerce et d'industrie
  (Légifrance).
- Directive (UE) 2022/542, « Annexe III, Point 22 » : corrigé en « Article 1er,
  point 22 » qui modifie le titre de l'annexe III (EUR-Lex).
- Vérifié sans modification : décision n° 2017-752 DC du 8 septembre 2017 (loi pour
  la confiance dans la vie politique, Légifrance).

### Lot 2 — liens croisés levier → article (fait partiellement)

- Champ `Levier.articles` ajouté, sérialisé dans `en_dict()`.
- 9 liens posés, uniquement là où la source écrite du levier cite un texte du
  registre : `effort_defense_pct_pib`, `investissements_cycle_long`,
  `montee_capacite_defense`, `verrouillage_irreversibilite`,
  `clause_revoyure_evaluation`, `usage_49_3`, `clause_sauvegarde_defense`,
  `macf_carbone_frontiere`.
- Tests : aucun lien orphelin ; liens clés présents.

### À faire (non traité, faute de source vérifiée à ce stade)

- Articles cités par des leviers mais absents du registre : `Article 278-0 bis CGI`
  (tva_energie_5_5), `Règlement UE 2022/1854` (taxe_superprofits), `PLFSS`/ONDAM,
  loi ELAN art. 140, loi Sapin II, loi 3DS, loi LOM, loi APER, loi de programmation
  de la justice 2023-2027. Chacun doit être ajouté avec son lien Légifrance ou
  EUR-Lex avant d'être relié.
- `CGI_235_TER_ZD` (Mondial) : numéro d'article à vérifier.
- Valeurs chiffrées (`base_mde`, `defaut`, bornes, `source`) : contrôle levier par
  levier, avec année et lien. Aucune valeur modifiée à ce stade.

### Lot 3 — textes manquants ajoutés et descriptions corrigées (8 octobre 2026)

Date de consultation de toutes les sources : **08/10/2026**. Pour les pages
secondaires (cabinets, presse, fournisseurs), la date de publication de la page
est indiquée ; à remplacer par le texte officiel dès qu'il est consulté.

| Point | Source retenue | Date de la source | Action |
|---|---|---|---|
| TVA énergie (CGI 278-0 bis B) : abonnements électricité et gaz au taux de 5,5 % supprimé au 1er août 2025 ; facture au taux normal de 20 % | fournisseurs-electricite.com ; dune-energie.fr ; Ekwateur | 18/08/2026 ; 04/09/2026 ; 20/01/2026 | Description du levier `tva_energie_5_5` corrigée ; carburants retirés (taux normal) ; article ajouté |
| TVA rénovation énergétique (CGI 278-0 bis A) : 5,5 % ; chaudières fossiles exclues depuis le 1er mars 2025 | BOFiP BOI-TVA-LIQ-30-20-95 (version du 22/10/2025) | 22/10/2025 | Article ajouté au registre |
| Contribution de solidarité (règlement (UE) 2022/1854, articles 15 à 18) : limitée aux bénéfices 2022/2023, taux minimum 33 % | EUR-Lex | 06/10/2022 (texte) | Levier `taxe_superprofits` : périmètre corrigé (pétrole, gaz, charbon, raffinage) ; « transport maritime » et « rachats d'actions » retirés ; article ajouté |
| Encadrement des loyers (loi ELAN, article 140) : expérimentation à la demande des territoires | Légifrance ; ecologie.gouv.fr | 23/11/2018 (texte) ; 28/10/2025 (page) | Levier `encadrement_loyers` : « généralisation » retiré ; article ajouté |
| Loi APER, n° 2023-175 du 10/03/2023 | Légifrance (référence) ; préfecture des Pyrénées-Orientales | 08/12/2025 (page) | Article ajouté ; levier `renouvelables` relié |
| Loi de programmation de la justice, n° 2023-1059 du 20/11/2023 (article 1er et rapport annexé) | Légifrance | 20/11/2023 (texte) | Article ajouté ; levier `budget_justice` relié |
| ONDAM 2026 : 274,4 Md€ (+3,1 %), LFSS pour 2026 | Vidal (adoption) ; La Base Lextenso ; FIPECO | 18/12/2025 ; 31/12/2025 ; 04/07/2025 | Levier `ondam_variation` : « ≈ 260 Md€ » remplacé par 274,4 Md€ (LFSS 2026) |
| Pantouflage (Code pénal 432-13 : trois ans, 200 000 € d'amende) | AFA, guide (2022) ; ANSM, fiche 3 (2020) ; avocat (08/09/2026) | 2020 à 2026 | Article ajouté ; levier `reforme_anti_pantouflage` relié |

Vérifié sans changement : décision n° 2017-752 DC du 8 septembre 2017 (Légifrance,
texte de la décision) ; directive (UE) 2022/2523 transposée au CGI à partir de
l'article 223 VJ (EUR-Lex et sources fiscales, 2024-2026).

**Non vérifié, à ne pas présenter comme établi :**

- `CGI_235_TER_ZD` : aucun texte officiel trouvé à cette date. À retirer ou à
  remplacer par l'article exact.
- Tous les chiffrages issus du `DOSSIER_DE_MANDATURE_GLOBAL.md` (9 Md€ pour la TVA
  énergie, 6 Md€ pour la contribution, ratio renouvelables, etc.). Ils restent
  des hypothèses du dossier, signalées comme telles dans les descriptions.
- La comparaison européenne de la justice (0,35 % du PIB contre 0,5 % en
  Allemagne) : source CEPEJ à consulter.
- `tva_taux_normal` : base de 780 Md€ et 1 560 Md€ de consommation des ménages :
  à rattacher à une publication Insee précise.
- Modélisation : le levier `tva_energie_5_5` alimente le moteur avec un effet
  (9 Md€, effets directs) dont le point de départ (taux normal de 20 % sur
  l'abonnement depuis le 1er août 2025) doit être revu. Aucune valeur de
  simulation n'a été modifiée à ce stade.

### Lot 4 — transparence : statut de vérification de chaque donnée (8 octobre 2026)

- `simulateur/verification.py` : statuts `verifie`, `partiel`, `date_decalee`, `non_verifie`, `inaccessible` ; une source vérifiée exige une URL et une date (contrôlé par test).
- 7 leviers ont un statut explicite (1 vérifié, 6 partiels, 5 datés de 2025 ou antérieurement) ; tous les autres sont `non_verifie` avec la mention de leur source citée. Aucun n'est encore `inaccessible` : aucune consultation n'a échoué à ce stade.
- `docs/VERIFICATION_DONNEES.md` est généré par `outils/generer-page-verification.py` (`--verifier` en contrôle) : une ligne par levier et par article, avec ancre.
- Le simulateur affiche le statut sous chaque levier, un lien vers la page et un formulaire de signalement (`.github/ISSUE_TEMPLATE/donnee-a-verifier.md`). Le citoyen peut saisir sa propre valeur et sa source : elle est marquée « NON VÉRIFIÉE PAR LE MRSC » à l'écran et à l'impression, et n'entre pas dans le calcul.
- Aucune valeur n'a été modifiée dans ce lot : aucune correction sans source officielle datée.
- Reste à faire : vérifier les chiffres « date décalée » sur des sources 2026 ; traiter `tva_energie_5_5` et `taxe_superprofits` (sources incorrectes, à corriger après relecture de la modélisation) ; vérifier CGI 235 ter ZD, loi 3DS et LOM ; confronter DOSSIER_DE_MANDATURE aux sources datées.
