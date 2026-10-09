# Vérification des données du simulateur

> Page générée automatiquement le 08/10/2026 par `outils/generer-page-verification.py`. Ne pas la modifier à la main : modifier `simulateur/verification.py`.

Le simulateur affiche **toutes** ses données, y compris celles qui ne sont pas encore vérifiées. Chacune porte un statut visible à l'écran, dans une copie et sur une impression. Cette page dit, pour chaque donnée, ce qui est vérifié, ce qui ne l'est pas, et pourquoi.

## Les statuts

| Statut | Signification |
|---|---|
| **Vérifié** | Contrôlé sur une source officielle, date de consultation indiquée. |
| **Partiellement vérifié** | Une partie seulement (texte, date ou cadre) est contrôlée ; le chiffre attaché ne l'est pas. |
| **Chiffre daté** | La source est datée d'une année antérieure à 2026 : le chiffre doit être actualisé. |
| **Non vérifié** | La source citée n'a pas été consultée, ou il s'agit d'une hypothèse interne (dossier de mandature). |
| **Source inaccessible** | Une consultation a été tentée et a échoué (source introuvable, payante ou fermée). |

Une donnée non vérifiée n'est jamais masquée. Le simulateur affiche la valeur, son statut, et propose au citoyen de noter sa propre valeur sourcée. Cette valeur citoyenne est signalée comme non vérifiée à l'écran, dans une copie et sur une impression, et elle n'entre pas dans le calcul.

## Bilan

| Statut | Leviers | Articles du registre juridique |
|---|---:|---:|
| Vérifié | 1 | 9 |
| Partiellement vérifié | 9 | 3 |
| Chiffre daté | 5 | 0 |
| Non vérifié | 86 | 44 |
| Source inaccessible | 0 | 0 |

## Contribuer : une donnée, une source, une date

Vous connaissez une valeur officielle plus récente, une source plus fiable, ou vous constatez une erreur ? [Ouvrez un signalement](https://github.com/thejmimiia-code/D-mocratie-et-politique-du-peuple-pour-le-peuple-par-le-peuple/issues/new?template=donnee-a-verifier.md). Indiquez le libellé de la donnée, la valeur officielle, le lien vers la source (Légifrance, EUR-Lex, Insee, PLF, Cour des comptes…) et la date de publication.

## Leviers de politique publique

### Fiscalité des ménages

| Levier | Valeur par défaut | Statut | Source citée | Ce qui est vérifié |
|---|---|---|---|---|
| <a id="tva_taux_normal"></a>TVA — taux normal `tva_taux_normal` | 0 pts | **Chiffre daté** | Insee, comptes nationaux 2024 : consommation effective des ménages ≈ 1 560 Md€. | Source Insee « comptes nationaux 2024 » : chiffre de 2024, à actualiser. Non vérifié à ce stade. (consulté le 08/10/2026) |
| <a id="tva_energie_5_5"></a>TVA sur l'énergie à 5,5 % `tva_energie_5_5` | désactivé | **Partiellement vérifié** | CGI art. 278-0 bis B (version antérieure au 1er août 2025) ; loi n° 2025-127 du 14 février 2025, art. 20 (BOFiP BOI-RES-TVA-000209, version du 26/08/2026, consultée le 08/10/2026) ; chiffrage DOSSIER_DE_MANDATURE_GLOBAL.md (non vérifié). | Suppression du taux réduit sur l'abonnement au 1er août 2025 : vérifiée sur le BOFiP (art. 20 de la loi n° 2025-127). Périmètre du levier (consommation ou abonnement) et coût de 9 Md€/an : non vérifiés. (consulté le 08/10/2026) [lien officiel](https://bofip.impots.gouv.fr/bofip/14705-PGP.html/identifiant=BOI-RES-TVA-000209-20260826) |
| <a id="csg_crds_hausse"></a>CSG / CRDS — hausse `csg_crds_hausse` | 0 pts | **Non vérifié** | URSSAF / PLFSS ; CSG sur revenus d'activité et de remplacement. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="ir_tranche_superieure"></a>Impôt sur le revenu — tranche supérieure `ir_tranche_superieure` | 0 pts | **Non vérifié** | PLF — évaluation des voies et moyens, tranches hautes du barème. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="isf_retablissement"></a>Impôt sur la fortune (base élargie) `isf_retablissement` | désactivé | **Chiffre daté** | Rapports IGF/Conseil d'analyse économique ; ordres de grandeur IFI 2024 ≈ 2 Md€. | Ordre de grandeur IFI 2024 : chiffre daté, à actualiser. Non vérifié à ce stade. (consulté le 08/10/2026) |
| <a id="succession_reforme"></a>Droits de succession — réfaction à 100 000 € `succession_reforme` | 0 Md€ | **Non vérifié** | DGFiP, statistiques des droits de mutation à titre gratuit. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="flat_tax_suppression"></a>Flat tax du capital — suppression `flat_tax_suppression` | désactivé | **Non vérifié** | Rapport du Conseil des prélèvements obligatoires sur la fiscalité du capital. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="niches_fiscales"></a>Niches fiscales inefficaces — extinction `niches_fiscales` | 0 % | **Non vérifié** | PLF — annexe « dépenses fiscales » ; DOSSIER_DE_MANDATURE_GLOBAL.md (Volet 3). | Chiffrage interne au dossier de mandature : hypothèse, non vérifiée. |
| <a id="taxe_carbone"></a>Taxe carbone — trajectoire `taxe_carbone` | 0 €/tCO2 | **Non vérifié** | Quatre fois pour un climat ; Conseil d'analyse économique (élasticité -0,25 %/€). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="cheque_energie"></a>Chèque énergie — revalorisation `cheque_energie` | 0 Md€ | **Non vérifié** | ~5,7 millions de ménages bénéficiaires ; montant moyen ≈ 150 €. | Source citée non consultée à la date de l'audit : valeur à vérifier. |

### Fiscalité des entreprises & fraude

| Levier | Valeur par défaut | Statut | Source citée | Ce qui est vérifié |
|---|---|---|---|---|
| <a id="lutte_fraude_fiscale_ia"></a>Fraude fiscale — IA et data-mining `lutte_fraude_fiscale_ia` | 0 Md€ | **Chiffre daté** | DOSSIER_DE_MANDATURE_GLOBAL.md (Volet 2) ; Cour des comptes 2024. | Cour des comptes 2024 et dossier de mandature : chiffre daté. Non vérifié à ce stade. (consulté le 08/10/2026) |
| <a id="fraude_sociale"></a>Fraude sociale criminelle — redressement `fraude_sociale` | 0 Md€ | **Non vérifié** | DOSSIER_DE_MANDATURE_GLOBAL.md (Volet 3). | Chiffrage interne au dossier de mandature : hypothèse, non vérifiée. |
| <a id="conditionnement_aides_entreprises"></a>Aides aux entreprises — conditionnalité `conditionnement_aides_entreprises` | 0 Md€ | **Non vérifié** | DOSSIER_DE_MANDATURE_GLOBAL.md (Volet 2) ; Cour des comptes, aides économiques. | Chiffrage interne au dossier de mandature : hypothèse, non vérifiée. |
| <a id="taxe_superprofits"></a>Superprofits — contribution temporaire `taxe_superprofits` | 0 Md€ | **Partiellement vérifié** | Règlement (UE) 2022/1854, chapitre III, articles 15 à 18 (EUR-Lex, consulté le 08/10/2026, mention « No longer in force ») ; rapport COM(2023) 768 du 30/11/2023 ; chiffrage DOSSIER_DE_MANDATURE_GLOBAL.md (non vérifié). | Périmètre (pétrole, gaz, charbon, raffinage) et durée (exercices 2022 et/ou 2023) vérifiés sur le règlement, qui n'est plus en vigueur (application jusqu'au 31/12/2023). Champ modélisé (rachats d'actions) absent du règlement. Montant de 6 Md€/an : non vérifié. (consulté le 08/10/2026) [lien officiel](https://eur-lex.europa.eu/eli/reg/2022/1854/oj?locale=fr) |
| <a id="extension_ttf"></a>Taxe sur les transactions financières — extension `extension_ttf` | 0 Md€ | **Partiellement vérifié** | DOSSIER_DE_MANDATURE_GLOBAL.md ; étude d'impact Sénat sur la TTF. | Assiette actuelle (titres de capital, art. 235 ter ZD CGI) vérifiée sur Légifrance. Extension aux dérivés et +5 Md€/an : proposition non vérifiée. (consulté le 08/10/2026) [lien officiel](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000053543343) |
| <a id="impot_minimum_pilier2"></a>Impôt minimum mondial (OCDE Pilier 2) `impot_minimum_pilier2` | 0 Md€ | **Non vérifié** | Accord OCDE/G20 ; directive UE 2022/2523. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="macf_carbone_frontiere"></a>Mécanisme d'ajustement carbone aux frontières `macf_carbone_frontiere` | 0 Md€ | **Non vérifié** | Règlement UE 2023/956 — MACF en phase transitoire puis définitive. | Source citée non consultée à la date de l'audit : valeur à vérifier. |

### Protection sociale & solidarité

| Levier | Valeur par défaut | Statut | Source citée | Ce qui est vérifié |
|---|---|---|---|---|
| <a id="revalorisation_retraites"></a>Revalorisation des retraites (au-delà de l'inflation) `revalorisation_retraites` | 0 pts | **Non vérifié** | CNAV, rapport annuel ; effet retour consommation ≈ 0,4. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="revalorisation_minima_sociaux"></a>Minima sociaux — coup de pouce `revalorisation_minima_sociaux` | 0 Md€ | **Non vérifié** | DREES, minimum sociaux — 2,1 M foyers au RSA, 1,3 M bénéficiaires AAH. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="aide_logement"></a>Aides personnelles au logement (APL/ALS) `aide_logement` | 0 Md€ | **Non vérifié** | CNAF ; rapport de la Cour des comptes sur les aides au logement. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="precarite_energetique"></a>Précarité énergétique — bouclier ciblé `precarite_energetique` | 0 Md€ | **Non vérifié** | ONPE, rapport annuel sur la précarité énergétique (12 % des ménages). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="aide_alimentaire"></a>Aide alimentaire et lutte contre la pauvreté `aide_alimentaire` | 0 Md€ | **Non vérifié** | Rapports du Secours catholique / Restos du cœur ; crédits mission Solidarité. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="aide_enfance_jeunesse"></a>Protection de l'enfance & jeunesse `aide_enfance_jeunesse` | 0 Md€ | **Non vérifié** | Cour des comptes — protection de l'enfance ; convention d'objectifs État/départements. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="dependance_grand_age"></a>Autonomie & grand âge (APA, EHPAD) `dependance_grand_age` | 0 Md€ | **Non vérifié** | Rapport Libault (grand âge et autonomie) ; branche Autonomie de la Sécu. | Source citée non consultée à la date de l'audit : valeur à vérifier. |

### Santé

| Levier | Valeur par défaut | Statut | Source citée | Ce qui est vérifié |
|---|---|---|---|---|
| <a id="ondam_variation"></a>ONDAM — évolution de l'objectif de dépenses d'assurance maladie `ondam_variation` | 0 pts | **Vérifié** | LFSS pour 2026 (adoptée définitivement le 16/12/2025, promulguée le 31/12/2025) ; vidal.fr (18/12/2025) ; FIPECO, fiche ONDAM (consultée le 08/10/2026). | ONDAM 2026 = 274,4 Md€ (+3,1 %), LFSS pour 2026 (Vidal, 18/12/2025 ; La Base Lextenso, 31/12/2025). Conversion 1 point ≈ 2,7 Md€ calculée sur l'ONDAM 2025 de 265,9 Md€ (FIPECO). (consulté le 08/10/2026) [lien officiel](https://www.vidal.fr/actualites/37257-le-plfss-2026-definitivement-adopte.html) |
| <a id="hopital_public"></a>Hôpital public — investissement et emplois `hopital_public` | 0 Md€ | **Non vérifié** | Fédération hospitalière de France ; Ségur de la santé. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="deserts_medicaux"></a>Lutte contre les déserts médicaux `deserts_medicaux` | 0 Md€ | **Non vérifié** | DREES — accessibilité aux médecins généralistes ; 6 % de la population en désert. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="prevention_sante"></a>Prévention & santé publique `prevention_sante` | 0 Md€ | **Non vérifié** | OCDE, « Panorama de la santé » : 2 % des dépenses de santé en France (prévention). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="taxe_comportements"></a>Taxes comportementales (tabac, alcool, sucre) `taxe_comportements` | 0 Md€ | **Non vérifié** | OFDT / Santé publique France ; élasticité-prix du tabac ≈ −0,4. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="medicaments_souverainete"></a>Production de médicaments sur le territoire `medicaments_souverainete` | 0 Md€ | **Non vérifié** | ANSM/ANEPC — plans de sécurisation ; académie de pharmacie. | Source citée non consultée à la date de l'audit : valeur à vérifier. |

### Éducation, recherche, jeunesse

| Levier | Valeur par défaut | Statut | Source citée | Ce qui est vérifié |
|---|---|---|---|---|
| <a id="budget_education"></a>Budget de l'Éducation nationale `budget_education` | 0 Md€ | **Non vérifié** | Loi de finances — mission Enseignement scolaire (≈ 63 Md€). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="revalorisation_enseignants"></a>Revalorisation des enseignants `revalorisation_enseignants` | 0 Md€ | **Non vérifié** | Grenelle de l'éducation ; rapports IGESR sur l'attractivité du métier. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="budget_recherche"></a>Recherche & innovation (ANR, CNRS, universités) `budget_recherche` | 0 Md€ | **Non vérifié** | MESR — effort de recherche ; OCDE, taux de retour social de la R&D publique. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="formation_professionnelle"></a>Formation professionnelle & apprentissage `formation_professionnelle` | 0 Md€ | **Non vérifié** | France Compétences ; plan d'investissement dans les compétences (PIC). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="cantine_gratuite"></a>Gratuité de la restauration scolaire `cantine_gratuite` | 0 Md€ | **Non vérifié** | CNAF, évaluation des tarifs de cantine ; collectivités territoriales. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="capital_humain"></a>Capital humain : éducation & formation `capital_humain` | 0 Md€ | **Non vérifié** | DEPP / Eurostat COFOG GF09 pour les dépenses d'éducation ; délai de maturité de huit ans = hypothèse de scénario P18, sans rendement macro attribué. | Source citée non consultée à la date de l'audit : valeur à vérifier. |

### Travail, emploi, formation

| Levier | Valeur par défaut | Statut | Source citée | Ce qui est vérifié |
|---|---|---|---|---|
| <a id="smic_revalorisation"></a>SMIC — coup de pouce annuel `smic_revalorisation` | 0 pts | **Non vérifié** | Groupe d'expertise sur le SMIC ; élasticité emploi faible mais non nulle. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="partage_valeur"></a>Partage de la valeur (intéressement, dividendes) `partage_valeur` | 0 Md€ | **Non vérifié** | Loi PACTE ; rapports DARES sur l'épargne salariale (≈ 18 Md€ distribués). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="temps_de_travail"></a>Temps de travail (semaine / heures supplémentaires) `temps_de_travail` | 0 h | **Non vérifié** | Études OFCE / DARES sur la durée du travail ; conventions collectives. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="cotisations_bas_salaires"></a>Exonérations de cotisations — bas salaires `cotisations_bas_salaires` | 0 Md€ | **Non vérifié** | Comité d'évaluation des aides publiques aux entreprises ; études INSEE. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="police_sociale_emploi"></a>Contrôle du travail & lutte contre le travail dissimulé `police_sociale_emploi` | 0 Md€ | **Non vérifié** | DARES, rapports de l'inspection du travail ; plan de lutte contre le travail illégal. | Source citée non consultée à la date de l'audit : valeur à vérifier. |

### Défense, sécurité, justice

| Levier | Valeur par défaut | Statut | Source citée | Ce qui est vérifié |
|---|---|---|---|---|
| <a id="effort_defense_pct_pib"></a>Effort de défense (% du PIB) `effort_defense_pct_pib` | 2.1 % du PIB | **Non vérifié** | LPM 2024-2030 ; sommet OTAN de La Haye (5 % dont 1,5 % d'infrastructures). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="reserve_securite_nationale"></a>Réserve et préparation nationale (sécurité civile) `reserve_securite_nationale` | 0 Md€ | **Non vérifié** | Direction générale de la sécurité civile ; SNS (stratégie nationale de résilience). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="effectifs_securite"></a>Effectifs police & gendarmerie `effectifs_securite` | 0 milliers | **Non vérifié** | LOPMI 2022-2027 (8 500 créations) ; rapport IGPN/IGGN annuel. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="budget_justice"></a>Budget de la justice `budget_justice` | 0 Md€ | **Partiellement vérifié** | Loi n° 2023-1059 du 20 novembre 2023 (programmation de la justice 2023-2027), Légifrance ; comparaison européenne : CEPEJ (non vérifiée). | Loi n° 2023-1059 du 20 novembre 2023 vérifiée. Part du PIB (0,35 %) et comparaison allemande (0,5 %) : non vérifiées (CEPEJ à consulter). (consulté le 08/10/2026) [lien officiel](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000048430512) |
| <a id="lutte_criminalite_organisee"></a>Lutte contre les trafics & criminalité organisée `lutte_criminalite_organisee` | 0 Md€ | **Non vérifié** | OFDT / SSMSI — statistiques de la délinquance ; rapport Sénat sur les trafics. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="cyber_resilience"></a>Cyber-résilience (NIS 2, ANSSI, OIV) `cyber_resilience` | 0 Md€ | **Non vérifié** | ANSSI — panorama de la cybermenace ; directive NIS 2 (2022/2555). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="montee_capacite_defense"></a>Montée en capacité de défense (BITD) `montee_capacite_defense` | 0 Md€ | **Non vérifié** | Loi de programmation militaire 2024-2030 (calendrier) ; délai de six ans = hypothèse de montée en capacité, pas durée moyenne auditée. | Source citée non consultée à la date de l'audit : valeur à vérifier. |

### Énergie & climat

| Levier | Valeur par défaut | Statut | Source citée | Ce qui est vérifié |
|---|---|---|---|---|
| <a id="nucleaire_reacteurs"></a>Nouveaux réacteurs nucléaires (EPR2) `nucleaire_reacteurs` | 0 nb | **Non vérifié** | Programme EPR2 (6 réacteurs) ; Cour des comptes, coûts de la filière nucléaire. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="renouvelables"></a>Renouvelables (éolien, solaire, biogaz) `renouvelables` | 0 Md€ | **Partiellement vérifié** | Loi n° 2023-175 du 10 mars 2023 (APER), Légifrance ; RTE, « Futurs énergétiques 2050 » (référence non vérifiée à ce stade). | Loi n° 2023-175 du 10 mars 2023 vérifiée. Ratio 1 Md€ ≈ 1 point de part renouvelable : non vérifié. RTE non consulté. (consulté le 08/10/2026) [lien officiel](https://www.pyrenees-orientales.gouv.fr/Actions-de-l-Etat/Environnement-eau-risques-naturels-et-technologiques/Energies-renouvelables/Planifier-les-energies-renouvelables/Loi-d-acceleration-pour-la-production-d-energies-renouvelables-Loi-APER/La-loi-APER) |
| <a id="renovation_thermique"></a>Rénovation thermique des bâtiments `renovation_thermique` | 0 Md€ | **Non vérifié** | ANAH ; 30 % des logements sont des « passoires thermiques » (DPE E-F-G). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="adaptation_climat"></a>Adaptation au changement climatique `adaptation_climat` | 0 Md€ | **Chiffre daté** | PNACC-3 ; rapport de la Cour des comptes sur l'adaptation (2024) ; R&D deux mandatures (docs/RD_DOUBLE_MANDATURE.md, point P17). | Rapport de la Cour des comptes de 2024 : chiffre daté. Non vérifié à ce stade. (consulté le 08/10/2026) |
| <a id="transports_publics"></a>Transports publics & mobilités (TER, RER, vélo) `transports_publics` | 0 Md€ | **Partiellement vérifié** | Conseil d'orientation des infrastructures (rapport Duron) ; loi n° 2019-1428 du 24 décembre 2019 (LOM, cadre juridique). | Cadre juridique (loi n° 2019-1428 du 24/12/2019, LOM) vérifié sur ecologie.gouv.fr et Légifrance. Montants du rapport Duron : non vérifiés. (consulté le 08/10/2026) [lien officiel](https://www.ecologie.gouv.fr/loi-dorientation-des-mobilites) |
| <a id="moratoire_artificialisation"></a>Zéro artificialisation nette — mise en œuvre `moratoire_artificialisation` | désactivé | **Non vérifié** | Loi Climat et Résilience (art. 191 à 195) ; rapport ZAN 2024. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="investissements_cycle_long"></a>Investissements à cycle long (rendement différé) `investissements_cycle_long` | 0 Md€ | **Non vérifié** | PPE ; LPM 2024-2030 ; sommet OTAN de La Haye (2025) ; dossier de mandature, chiffrage prévention santé ; R&D deux mandatures (point P6). | Source citée non consultée à la date de l'audit : valeur à vérifier. |

### Industrie, numérique, souveraineté

| Levier | Valeur par défaut | Statut | Source citée | Ce qui est vérifié |
|---|---|---|---|---|
| <a id="plan_semiconducteurs"></a>Plan semi-conducteurs (Chips Act France) `plan_semiconducteurs` | 0 Md€ | **Non vérifié** | Chips Act européen (règlement 2023/1781) ; plan France 2030. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="relocalisation_industrie"></a>Relocalisations industrielles `relocalisation_industrie` | 0 Md€ | **Non vérifié** | Rapports France Industrie ; indicateur de dépendance importations (INSEE). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="souverainete_numerique_ia"></a>Souveraineté numérique & IA `souverainete_numerique_ia` | 0 Md€ | **Non vérifié** | Commission de l'IA (rapport 2024) ; stratégie nationale IA. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="service_public_numerique"></a>Services publics numériques (FranceConnect, IA administrative) `service_public_numerique` | 0 Md€ | **Non vérifié** | DINUM — rapport annuel ; baromètre de la qualité des services publics numériques. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="agriculture_souverainete"></a>Souveraineté agricole & alimentaire `agriculture_souverainete` | 0 Md€ | **Non vérifié** | Rapport Sénat sur la souveraineté alimentaire ; PAC 2023-2027. | Source citée non consultée à la date de l'audit : valeur à vérifier. |

### Logement, territoires, collectivités

| Levier | Valeur par défaut | Statut | Source citée | Ce qui est vérifié |
|---|---|---|---|---|
| <a id="dgf_delta"></a>Dotation globale de fonctionnement (DGF) `dgf_delta` | 0 Md€ | **Non vérifié** | Comité des finances locales ; CGCT art. L. 1612-4 (règle d'or budgétaire). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="logement_social"></a>Construction de logements sociaux `logement_social` | 0 milliers | **Non vérifié** | USH / Sénat — objectif SRU de 25 % de logements sociaux ; demande HLM ≈ 2 M. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="encadrement_loyers"></a>Encadrement des loyers `encadrement_loyers` | désactivé | **Partiellement vérifié** | Loi n° 2018-1021 du 23 novembre 2018 (ELAN), article 140, Légifrance ; ecologie.gouv.fr (page du 28/10/2025, consultée le 08/10/2026). | Mécanisme (loyers de référence, +20 %, -30 %) vérifié sur l'article 140 de la loi ELAN. Effets sur les loyers et l'offre : non vérifiés. (consulté le 08/10/2026) [lien officiel](https://www.legifrance.gouv.fr/eli/loi/2018/11/23/TERL1805474L/jo/article_140) |
| <a id="decentralisation"></a>Nouvelle étape de décentralisation `decentralisation` | désactivé | **Partiellement vérifié** | Rapports du Comité d'évaluation des réformes de la décentralisation ; loi n° 2022-217 du 21 février 2022 (3DS, cadre juridique). | Cadre juridique (loi n° 2022-217 du 21/02/2022, 3DS) vérifié sur ecologie.gouv.fr et l'Assemblée nationale. Chiffres des rapports du comité d'évaluation : non vérifiés. (consulté le 08/10/2026) [lien officiel](https://www.ecologie.gouv.fr/politiques-publiques/loi-3ds-relative-differenciation-decentralisation-deconcentration) |
| <a id="fusion_doublons"></a>Fusion des doublons territoriaux `fusion_doublons` | 0 Md€ | **Non vérifié** | DOSSIER_DE_MANDATURE_GLOBAL.md (Volet 3) ; Cour des comptes, opérateurs de l'État. | Chiffrage interne au dossier de mandature : hypothèse, non vérifiée. |

### État, fonction publique, simplification

| Levier | Valeur par défaut | Statut | Source citée | Ce qui est vérifié |
|---|---|---|---|---|
| <a id="point_indice"></a>Valeur du point d'indice (fonction publique) `point_indice` | 0 % | **Non vérifié** | DGAFP — rapport annuel sur l'état de la fonction publique (5,7 M d'agents). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="effectifs_etat"></a>Effectifs de l'État (variation nette) `effectifs_etat` | 0 milliers | **Non vérifié** | PLF — plafonds d'emplois ; Cour des comptes, effectifs de l'État. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="commande_publique"></a>Commande publique massifiée `commande_publique` | 0 Md€ | **Non vérifié** | DOSSIER_DE_MANDATURE_GLOBAL.md (Volet 3) ; OECP, achats publics ≈ 110 Md€. | Chiffrage interne au dossier de mandature : hypothèse, non vérifiée. |
| <a id="simplification"></a>Simplification administrative (choc de simplification) `simplification` | 0 Md€ | **Non vérifié** | Rapports du Conseil d'État sur la simplification ; indicateurs de complexité (OCDE). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="clause_revoyure_evaluation"></a>Clauses de revoyure & évaluation systématique `clause_revoyure_evaluation` | désactivé | **Non vérifié** | LOLF du 1er août 2001 ; Constitution, art. 47-2 ; R&D deux mandatures (docs/RD_DOUBLE_MANDATURE.md, point P13). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="dividende_dette_reinvesti"></a>Second dividende : charge de la dette réinvestie `dividende_dette_reinvesti` | 0 Md€ | **Non vérifié** | Agence France Trésor, maturité moyenne 8,5 ans ; R&D deux mandatures (docs/RD_DOUBLE_MANDATURE.md, point P5). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="entretien_capital_public"></a>Entretien du capital public (dette technique) `entretien_capital_public` | 0 Md€ | **Chiffre daté** | Cour des comptes, analyse de l'exécution budgétaire 2023 — gestion du patrimoine immobilier de l'État (140-150 Md€ de besoins d'investissement à l'horizon 2050) ; annualisation exploratoire documentée au point P16. | Source Cour des comptes sur l'exécution budgétaire 2023 : chiffre daté. Non vérifié à ce stade. (consulté le 08/10/2026) |
| <a id="charge_reformes_simultanees"></a>Grandes réformes menées de front `charge_reformes_simultanees` | 0 réformes simultanées | **Non vérifié** | Hypothèse de stress-test du moteur (P20), sans seuil officiel ; à documenter par délais de mise en œuvre, évaluations et capacité RH. | Source citée non consultée à la date de l'audit : valeur à vérifier. |

### Institutions & démocratie

| Levier | Valeur par défaut | Statut | Source citée | Ce qui est vérifié |
|---|---|---|---|---|
| <a id="reforme_casier_b2"></a>Casier B2 vierge obligatoire pour les candidats `reforme_casier_b2` | désactivé | **Non vérifié** | Proposition du DOSSIER_DE_MANDATURE_GLOBAL.md ; code électoral. | Chiffrage interne au dossier de mandature : hypothèse, non vérifiée. |
| <a id="reforme_vote_blanc"></a>Vote blanc invalidant `reforme_vote_blanc` | désactivé | **Non vérifié** | DOSSIER_DE_MANDATURE_GLOBAL.md ; propositions de loi sur la reconnaissance du vote blanc. | Chiffrage interne au dossier de mandature : hypothèse, non vérifiée. |
| <a id="reforme_ric"></a>Référendum d'initiative citoyenne (RIC) `reforme_ric` | désactivé | **Non vérifié** | DOSSIER_DE_MANDATURE_GLOBAL.md ; analyse comparative Suisse / Italie. | Chiffrage interne au dossier de mandature : hypothèse, non vérifiée. |
| <a id="reforme_regimes_speciaux"></a>Fin des régimes de retraite spéciaux `reforme_regimes_speciaux` | désactivé | **Non vérifié** | Rapport Delevoye ; Cour des comptes — régimes spéciaux. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="reforme_anti_pantouflage"></a>Anti-pantouflage & transparence des lobbys `reforme_anti_pantouflage` | désactivé | **Partiellement vérifié** | Code pénal, article 432-13 ; loi n° 2016-1691 du 9 décembre 2016 (Sapin II) ; HATVP. | Pantouflage (article 432-13 du Code pénal, trois ans) vérifié. Registre public des représentants d'intérêts et transparence des rendez-vous : non vérifiés dans ce lot. (consulté le 08/10/2026) [lien officiel](https://www.agence-francaise-anticorruption.gouv.fr/files/files/Guide_AFA_sport_operateurs_2022.pdf) |
| <a id="reforme_non_cumul"></a>Non-cumul des mandats étendu `reforme_non_cumul` | désactivé | **Non vérifié** | Loi organique 2014-125 ; rapports sur le renouvellement démocratique. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="verrouillage_irreversibilite"></a>Verrou constitutionnel des réformes `verrouillage_irreversibilite` | désactivé | **Non vérifié** | Constitution de 1958, art. 89 et 11 ; R&D deux mandatures (docs/RD_DOUBLE_MANDATURE.md, points P3 et P7). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="reforme_proportionnelle"></a>Scrutin proportionnel à l'Assemblée `reforme_proportionnelle` | 0 % | **Non vérifié** | Assemblée nationale — rapport sur le mode de scrutin ; comparaisons européennes. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="convention_citoyenne"></a>Convention citoyenne permanente `convention_citoyenne` | désactivé | **Non vérifié** | Convention citoyenne pour le climat (2019-2020) ; CESE. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="usage_49_3"></a>Recours à l'article 49.3 `usage_49_3` | 0 nb | **Non vérifié** | Constitution art. 49 al. 3 ; statistiques des censures (1962-2025). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="lutte_contre_la_corruption"></a>Moyens anticorruption & justice financière `lutte_contre_la_corruption` | 0 Md€ | **Non vérifié** | AFA — rapports annuels ; PNF — bilan d'activité. | Source citée non consultée à la date de l'audit : valeur à vérifier. |

### Europe, diplomatie, migration

| Levier | Valeur par défaut | Statut | Source citée | Ce qui est vérifié |
|---|---|---|---|---|
| <a id="integration_europeenne"></a>Intégration européenne (budget, dette commune, défense) `integration_europeenne` | 0 % | **Non vérifié** | Rapports sur la souveraineté européenne ; traité de Lisbonne art. 42-2. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="cooperation_internationale"></a>Aide publique au développement & climat `cooperation_internationale` | 0 Md€ | **Non vérifié** | OCDE-CAD — aide publique au développement française. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="integration_accueil"></a>Intégration des nouveaux arrivants (langue, emploi) `integration_accueil` | 0 Md€ | **Non vérifié** | Rapports de la Cour des comptes sur l'intégration ; OFII. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="maitrise_flux_migratoires"></a>Maîtrise des flux migratoires `maitrise_flux_migratoires` | désactivé | **Non vérifié** | Rapports de l'OCDE sur les migrations internationales ; Office français de l'immigration. | Source citée non consultée à la date de l'audit : valeur à vérifier. |

### Chocs mondiaux (exogènes)

| Levier | Valeur par défaut | Statut | Source citée | Ce qui est vérifié |
|---|---|---|---|---|
| <a id="choc_petrole"></a>Choc pétrolier (variation du Brent) `choc_petrole` | 0 $/baril | **Non vérifié** | Historique des chocs pétroliers (1973, 1979, 2008, 2022). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="choc_taux_fed"></a>Choc de taux (Fed / BCE) `choc_taux_fed` | 0 bps | **Non vérifié** | Cycles monétaires 2008-2025 ; transmission taux directeurs → taux 10 ans. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="choc_change"></a>Choc de change EUR/USD `choc_change` | 0 $ par € | **Non vérifié** | Effets de changes sur les importations ; élasticités du commerce extérieur. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="commerce_mondial"></a>Commerce mondial (fragmentation / accord) `commerce_mondial` | 0 % | **Non vérifié** | FMI — « géo-économie fragmentation » ; scénarios OMC. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="tension_taiwan"></a>Tension autour de Taïwan `tension_taiwan` | 0 0-100 | **Non vérifié** | Indices de tension (SIPRI, Atlantic Council) ; dépendance semi-conducteurs. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="tension_ukraine"></a>Guerre en Ukraine / relation OTAN-Russie `tension_ukraine` | 0 0-100 | **Non vérifié** | SIPRI ; rapports ONU ; dépenses militaires mondiales. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="tension_hormuz"></a>Tension au détroit d'Hormuz `tension_hormuz` | 0 0-100 | **Non vérifié** | AIE — chokepoints pétroliers mondiaux. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="blocus_taiwan"></a>Intensité d'un blocus de Taïwan `blocus_taiwan` | 0 0-1 | **Non vérifié** | Scénarios de rupture Enedis/ANSSI ; analyse des chaînes de valeur (OCDE). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="fermeture_hormuz"></a>Fermeture du détroit d'Hormuz `fermeture_hormuz` | 0 0-1 | **Non vérifié** | AIE — scenarii de rupture d'approvisionnement pétrolier. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="cyberattaque_systemique"></a>Cyberattaque systémique majeure `cyberattaque_systemique` | désactivé | **Non vérifié** | ANSSI — panorama 2025 ; NIS 2. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="escalade_nucleaire"></a>Franchissement du seuil nucléaire tactique `escalade_nucleaire` | désactivé | **Non vérifié** | SIPRI 2026 ; scénarios de dissuasion (revue Défense nationale). | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="mobilisation_guerre"></a>Discours de mobilisation / économie de guerre `mobilisation_guerre` | désactivé | **Non vérifié** | Revues de programmation militaire ; retour d'expérience 2022-2026. | Source citée non consultée à la date de l'audit : valeur à vérifier. |
| <a id="clause_sauvegarde_defense"></a>Clause de sauvegarde nationale (défense) `clause_sauvegarde_defense` | désactivé | **Non vérifié** | Pacte de stabilité réformé (2024) — clause de sauvegarde nationale. | Source citée non consultée à la date de l'audit : valeur à vérifier. |

## Textes juridiques du registre

| Article | Texte | Statut | Ce qui est vérifié |
|---|---|---|---|
| <a id="CONST_ART_2"></a>Article 2, alinéa 5 `CONST_ART_2` | Constitution du 4 octobre 1958 | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CONST_ART_3"></a>Article 3 `CONST_ART_3` | Constitution du 4 octobre 1958 | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CONST_ART_11"></a>Article 11 `CONST_ART_11` | Constitution du 4 octobre 1958 | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CONST_ART_49_2"></a>Article 49, alinéa 2 `CONST_ART_49_2` | Constitution du 4 octobre 1958 | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CONST_ART_49_3"></a>Article 49, alinéa 3 `CONST_ART_49_3` | Constitution du 4 octobre 1958 | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="DDHC_ART_6"></a>Article 6 `DDHC_ART_6` | Déclaration des Droits de l'Homme et du Citoyen de 1789 | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CC_2017_752_DC"></a>Décision n° 2017-752 DC du 8 septembre 2017 `CC_2017_752_DC` | Jurisprudence du Conseil constitutionnel | **Vérifié** | Décision du Conseil constitutionnel consultée sur Légifrance. (consulté le 08/10/2026) [lien officiel](https://www.legifrance.gouv.fr/cons/id/CONSTEXT000035597362) |
| <a id="CP_432_10"></a>Article 432-10 `CP_432_10` | Code pénal | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CP_432_11"></a>Article 432-11 `CP_432_11` | Code pénal | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CP_432_12"></a>Article 432-12 `CP_432_12` | Code pénal | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CP_131_26_2"></a>Article 131-26-2 `CP_131_26_2` | Code pénal | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CGI_1741"></a>Article 1741 `CGI_1741` | Code général des impôts | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CGCT_L1612_4"></a>Article L. 1612-4 `CGCT_L1612_4` | Code général des collectivités territoriales | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CGCT_L2334_1"></a>Article L. 2334-1 et suivants `CGCT_L2334_1` | Code général des collectivités territoriales | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="LPF_L81"></a>Article L. 81 `LPF_L81` | Livre des procédures fiscales | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CGI_235_TER_ZD"></a>Article 235 ter ZD `CGI_235_TER_ZD` | Code général des impôts | **Vérifié** | Taux de 0,4 % et seuil de capitalisation de 1 Md€ vérifiés sur Légifrance (version en vigueur au 01/01/2026, loi n° 2026-103 du 19/02/2026). Extension modélisée : proposition, non vérifiée. (consulté le 08/10/2026) [lien officiel](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000053543343) |
| <a id="ENV_L229_25"></a>Article L. 229-25 `ENV_L229_25` | Code de l'environnement | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CCP_L2113_10"></a>Article L. 2113-10 `CCP_L2113_10` | Code de la commande publique | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CCP_L2112_2"></a>Article L. 2112-2 `CCP_L2112_2` | Code de la commande publique | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CONSO_L470_2"></a>Article L. 470-2 `CONSO_L470_2` | Code de la consommation | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="DIR_TVA_2022_542"></a>Article 1er, point 22 (modifie le titre de l'annexe III de la directive 2006/112/CE) `DIR_TVA_2022_542` | Union Européenne — Directive (UE) 2022/542 du Conseil | **Vérifié** | Article 1er, point 22 de la directive 2022/542 consulté sur EUR-Lex. (consulté le 08/10/2026) [lien officiel](https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:32022L0542) |
| <a id="TFUE_ART_126"></a>Article 126 & Protocole n° 12 `TFUE_ART_126` | Traité sur le Fonctionnement de l'Union Européenne | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="REG_EIDAS_910_2014"></a>Articles 8 et 9 `REG_EIDAS_910_2014` | Règlement (UE) n° 910/2014 (eIDAS) | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="OCDE_PILIER_2_CGI_223_VJ"></a>Art. 223 VJ et suiv. du CGI `OCDE_PILIER_2_CGI_223_VJ` | Code général des impôts (transposition de la directive (UE) 2022/2523) | **Vérifié** | Transposition de la directive (UE) 2022/2523 au CGI à partir de l'article 223 VJ (impots.gouv.fr, 16/02/2026 ; EUR-Lex). (consulté le 08/10/2026) [lien officiel](https://www.impots.gouv.fr/professionnel/je-decouvre-limposition-minimale-mondiale) |
| <a id="REG_UE_2023_956_MACF"></a>Règlement (UE) 2023/956 `REG_UE_2023_956_MACF` | Règlement (UE) 2023/956 du Parlement européen et du Conseil | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="BALE_III_REG_575_2013"></a>Règlement CRR art. 92 & 114 `BALE_III_REG_575_2013` | Règlement (UE) n° 575/2013 (CRR) - Accords de Bâle III / Bâle IV | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="OMC_GATT_ART_XX"></a>Article XX (Exceptions générales) `OMC_GATT_ART_XX` | Accord général sur les tarifs douaniers et le commerce (GATT / OMC) | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CONST_ART_24"></a>Article 24 `CONST_ART_24` | Constitution du 4 octobre 1958 | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CONST_ART_47_2"></a>Article 47-2 `CONST_ART_47_2` | Constitution du 4 octobre 1958 | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CONST_ART_61_1"></a>Article 61-1 `CONST_ART_61_1` | Constitution du 4 octobre 1958 | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CONST_ART_71_1"></a>Article 71-1 `CONST_ART_71_1` | Constitution du 4 octobre 1958 | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="DDHC_ART_14"></a>Article 14 `DDHC_ART_14` | Déclaration des Droits de l'Homme et du Citoyen de 1789 | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CHARTE_ENV_ART_1"></a>Article 1er `CHARTE_ENV_ART_1` | Charte de l'environnement de 2004 | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CRPA_L123_1"></a>Article L. 123-1 (Loi ESSOC) `CRPA_L123_1` | Code des relations entre le public et l'administration | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CCOM_L710_1"></a>Article L. 710-1 `CCOM_L710_1` | Code de commerce | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CONST_ART_15"></a>Article 15 `CONST_ART_15` | Constitution du 4 octobre 1958 | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CONST_ART_35"></a>Article 35 `CONST_ART_35` | Constitution du 4 octobre 1958 | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="LPM_2023_703"></a>Article 3 et rapport annexé `LPM_2023_703` | Loi n° 2023-703 du 1er août 2023 de programmation militaire 2024-2030 | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="OTAN_ART_3"></a>Article 3 `OTAN_ART_3` | Traité de l'Atlantique Nord (4 avril 1949) & Déclaration du sommet de La Haye (25 juin 2025) | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="OTAN_ART_5"></a>Article 5 `OTAN_ART_5` | Traité de l'Atlantique Nord (4 avril 1949) | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="TFUE_ART_42_7_TUE"></a>Article 42, paragraphe 7 `TFUE_ART_42_7_TUE` | Traité sur l'Union européenne | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="REG_UE_2024_1263_CLAUSE"></a>Articles 25 et 26 (clauses de sauvegarde nationale et générale) `REG_UE_2024_1263_CLAUSE` | Règlement (UE) 2024/1263 — volet préventif du Pacte de stabilité et de croissance réformé | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="REG_UE_2023_1781_CHIPS"></a>Articles 1er et 22 à 25 `REG_UE_2023_1781_CHIPS` | Règlement (UE) 2023/1781 établissant un cadre de mesures pour renforcer l'écosystème européen des semi-conducteurs (Chips Act) | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="DIR_UE_2022_2555_NIS2"></a>Articles 20 à 23 `DIR_UE_2022_2555_NIS2` | Directive (UE) 2022/2555 concernant des mesures destinées à assurer un niveau élevé commun de cybersécurité (NIS 2) | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CENERGIE_L642_2"></a>Article L. 642-2 `CENERGIE_L642_2` | Code de l'énergie (obligations AIE / accord de 1974) | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CNUDM_ART_38"></a>Articles 37 et 38 `CNUDM_ART_38` | Convention des Nations unies sur le droit de la mer (Montego Bay, 1982) | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="TNP_ART_6"></a>Article VI `TNP_ART_6` | Traité sur la non-prolifération des armes nucléaires (1968) | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CART_L711_1"></a>Article L. 711-1 `CART_L711_1` | Code de commerce | **Vérifié** | Article L. 711-1 du Code de commerce consulté sur Légifrance : chambres de commerce et d'industrie. (consulté le 08/10/2026) [lien officiel](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000038610758) |
| <a id="CRURAL_L510_1"></a>Article L. 510-1 `CRURAL_L510_1` | Code rural et de la pêche maritime | **Non vérifié** | Texte cité non recontrôlé sur Légifrance, EUR-Lex ou le site officiel à la date de l'audit. |
| <a id="CGI_278_0_BIS_A"></a>Article 278-0 bis A `CGI_278_0_BIS_A` | Code général des impôts | **Vérifié** | BOFiP BOI-TVA-LIQ-30-20-95, version du 22/10/2025 consultée. (consulté le 08/10/2026) [lien officiel](https://bofip.impots.gouv.fr/bofip/9417-PGP.html/identifiant=BOI-TVA-LIQ-30-20-95-20251022) |
| <a id="CGI_278_0_BIS_B"></a>Article 278-0 bis B (version antérieure au 1er août 2025) `CGI_278_0_BIS_B` | Code général des impôts | **Vérifié** | Suppression du taux réduit de 5,5 % sur les abonnements (électricité ≤ 36 kVA et gaz) pour les périodes débutant à compter du 1er août 2025 : BOFiP BOI-RES-TVA-000209 (version du 26/08/2026), citant l'article 20 de la loi n° 2025-127. Texte intégral non relu sur Légifrance. (consulté le 08/10/2026) [lien officiel](https://bofip.impots.gouv.fr/bofip/14705-PGP.html/identifiant=BOI-RES-TVA-000209-20260826) |
| <a id="REG_UE_2022_1854_SOLIDARITE"></a>Articles 15 à 18 `REG_UE_2022_1854_SOLIDARITE` | Règlement (UE) 2022/1854 du Conseil du 6 octobre 2022 | **Partiellement vérifié** | Articles 15 à 18 consultés sur EUR-Lex (mention « No longer in force ») ; chapitre III applicable jusqu'au 31/12/2023 (clause finale ; rapport COM(2023) 768 du 30/11/2023). (consulté le 08/10/2026) [lien officiel](https://eur-lex.europa.eu/eli/reg/2022/1854/oj?locale=fr) |
| <a id="ELAN_ART_140"></a>Article 140 `ELAN_ART_140` | Loi n° 2018-1021 du 23 novembre 2018 (loi ELAN) | **Vérifié** | Article 140 de la loi n° 2018-1021 consulté sur Légifrance. (consulté le 08/10/2026) [lien officiel](https://www.legifrance.gouv.fr/eli/loi/2018/11/23/TERL1805474L/jo/article_140) |
| <a id="LOI_APER_2023_175"></a>Ensemble du texte ; zones d'accélération : article 15 `LOI_APER_2023_175` | Loi n° 2023-175 du 10 mars 2023 (loi APER) | **Partiellement vérifié** | Numéro et date de la loi vérifiés (source secondaire officielle). Texte Légifrance à consulter. (consulté le 08/10/2026) [lien officiel](https://www.pyrenees-orientales.gouv.fr/Actions-de-l-Etat/Environnement-eau-risques-naturels-et-technologiques/Energies-renouvelables/Planifier-les-energies-renouvelables/Loi-d-acceleration-pour-la-production-d-energies-renouvelables-Loi-APER/La-loi-APER) |
| <a id="LOI_JUSTICE_2023_1059"></a>Article 1er et rapport annexé `LOI_JUSTICE_2023_1059` | Loi n° 2023-1059 du 20 novembre 2023 (programmation de la justice) | **Vérifié** | Loi n° 2023-1059 consultée sur Légifrance. (consulté le 08/10/2026) [lien officiel](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000048430512) |
| <a id="CP_432_13"></a>Article 432-13 `CP_432_13` | Code pénal | **Partiellement vérifié** | Infraction et délai de trois ans confirmés par l'AFA (guide 2022) et l'ANSM (2020) ; texte officiel à consulter sur Légifrance. (consulté le 08/10/2026) [lien officiel](https://www.agence-francaise-anticorruption.gouv.fr/files/files/Guide_AFA_sport_operateurs_2022.pdf) |

