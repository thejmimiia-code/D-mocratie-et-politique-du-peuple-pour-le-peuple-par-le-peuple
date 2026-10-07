# R&D — DEUX MANDATURES CONSÉCUTIVES (2027-2037) : les points stratégiques systématiques de la période de dix ans

> **Statut** : recherche livrée avec prototype exécutable (moteur, scénarios,
> leviers, garde-fous, tests). Les simulations sont des explorations du modèle,
> **jamais des prévisions**.
>
> **Règle de travail permanente** : ce document est la grille de lecture A→Z du
> projet. Toute modification ultérieure du simulateur, du dossier de mandature
> ou de la doctrine doit être passée au crible des vingt-et-un points ci-dessous —
> si un point redevient aveugle, il faut le dire ici avant de livrer.

---

## 0. Vue d'ensemble du projet (état des lieux A→Z)

| Brique | Contenu | Fichier |
|---|---|---|
| Doctrine | « Du peuple, par le peuple, pour le peuple » ; 20 leviers stratégiques ; plan à +60 Md€/an en année 5 | `DOSSIER_DE_MANDATURE_GLOBAL.md` |
| Modèle gigogne | 5 échelons : local → national → européen → mondial → géopolitique | `simulateur/moteur.py`, `simulateur/model.py` |
| Simulateur paramétrable | **101 leviers** en 14 familles, **14 préréglages** doctrinaux, 20 domaines notés 0-100 | `simulateur/parametres.py`, `simulateur/domaines.py` |
| Garde-fous | 31 seuils (26 absolus + 5 en écart), « tolérable → vigilance → risqué → hors-sol » | `simulateur/seuils.py` |
| Scénarios | 11 scénarios : 4 budgétaires, 5 géopolitiques, **2 décennaux (nouveaux)** | `simulateur/scenarios.py` |
| Données publiques | Eurostat, BCE, Frankfurter, Banque mondiale (à l'instant T) | `simulateur/donnees_live.py` |
| R&D accumulées | Laboratoire mensuel, géopolitique exploratoire, registre UCDP, validation temporelle | `docs/LABORATOIRE_RD.md` et suivants |

**Constat initial de cette R&D** : tout l'édifice était pensé pour **une seule
mandature quinquennale**. L'horizon de 5 ans était écrit dans les scénarios,
dans le calibrage (« Année 5 »), dans les préréglages et dans la doctrine.
Or la période pertinente d'un projet de transformation est celle de **deux
mandatures consécutives (dix ans)** — c'est l'horizon maximal autorisé par la
doctrine elle-même (non-cumul dans le temps, levier n° 6 : « max 2 mandats
consécutifs »). Quinze points stratégiques, tous systématiques sur cette
période, manquaient. La phase initiale a inventorié P1-P15 ; la revue A→Z
de la phase 2 ajoute P16-P21, six dimensions transversales. Les 21 points
sont brainstormés, sourcés et implémentés uniquement lorsque les hypothèses
peuvent être affichées honnêtement ; le reste demeure explicitement ouvert.

---

## 1. Pourquoi dix ans est la bonne unité de temps

1. **La doctrine l'impose.** Le projet limite l'exercice du pouvoir à deux
   mandats consécutifs identiques. La période de référence du projet est donc,
   par construction, de deux mandatures.
2. **Les dettes vivent 8,5 ans.** La maturité moyenne de la dette négociable
   française est de 8,5 ans (AFT) : il faut presque deux mandatures pour que le
   stock entier soit refinancé aux nouveaux taux. Un horizon de 5 ans coupe la
   démonstration juste avant son point d'arrivée.
3. **Les investissements mûrissent au-delà du quinquennat.** EPR2 (~15 ans),
   lois de programmation militaire (LPM 2024-2030 puis ~2030-2036), prévention
   santé (effets comptables à 10 ans — déjà écrit dans le dossier de
   mandature), éducation, recherche : leurs fruits tombent pendant la
   mandature suivante.
4. **Le calendrier européen et climatique est décennal.** Cadre financier
   pluriannuel 2028-2034, objectif -55 % en 2030, neutralité 2050, cible OTAN
   de La Haye (3,5 % + 1,5 % en 2035) : tous ces verrous tombent entre les
   deux mandatures ou pendant la seconde.
5. **Le risque d'alternance devient probable.** Sur dix ans, la probabilité
   d'une alternance ou d'une cohabitation n'est plus un accident mais un
   paramètre de conception. Les réformes doivent survivre à leurs auteurs.

---

## 2. Les vingt-et-un points stratégiques systématiques (inventaire + brainstorming)

> Chaque point est noté : **Manque** (ce qui était absent), **Systématique**
> (pourquoi il revient sur toute période de deux mandatures), **Brainstorming**
> (options débattues), **Statut** (ce qui est livré dans cette R&D).

### P1. L'horizon temporel lui-même

* **Manque** : scénarios figés à 5 exercices ; pas de trajectoire 2027-2037.
* **Systématique** : toute période de deux mandatures traverse des phases que
  cinq ans ne contiennent pas (réélection, mi-parcours, fin de cycle).
* **Brainstorming** : (a) dupliquer les scénarios en les concaténant — rejeté,
  car la mandature 2 n'est pas la mandature 1 répétée ; (b) étendre l'horizon
  paramétrique — retenu : `simuler(..., horizon=10)` fonctionnait déjà dans le
  moteur, il manquait les **dynamiques propres** aux années 6 à 10 ;
  (c) scénario dédié à dix décisions explicites — retenu aussi, pour rendre la
  doctrine lisible année par année.
* **Statut** : livré. `get_scenario_double_mandature()` (10 ans) et
  `get_scenario_alternance_2032()` (stress-test) ; CLI `double_mandature`,
  `alternance_2032` ; API `/api/simuler` accepte `horizon: 10`.

### P2. Le calendrier électoral et la sanction de mi-parcours

* **Manque** : aucune élection modélisée entre 2027 et 2037.
* **Systématique** : la période contient deux présidentielles+législatives
  (2032, 2037), deux européennes (2029, 2034), deux sénatoriales partielles
  supplémentaires (2029, 2032), des municipales (2032) et des
  départementales/régionales (2028, ~2034). Chaque scrutin redistribue les
  majorités — et donc la faisabilité des réformes restantes.
* **Brainstorming** : modéliser chaque scrutin local serait surajusté ; le
  signal pertinent pour les marchés et le climat social est l'**année de
  scrutin national général**, qui renchérit le crédit de l'État (prime
  d'incertitude) et tend la société. Une prime différenciée selon que les
  réformes sont révocables ou verrouillées rend le levier P3 mesurable.
* **Statut** : livré. Champ `annee_electorale_majeure` : prime de +12 bps sur
  le spread si les réformes sont révocables, +4 bps si elles sont verrouillées ;
  incertitude sociale +2 pts (réduite à +0,8 si évaluation systématique
  active). Années électorales modélisées : année 5 (2032) et année 10 (2037).

### P3. La réversibilité des réformes et le risque d'alternance

* **Manque** : rien ne protégeait les réformes d'une abrogation en 2032.
* **Systématique** : sur deux mandatures, une alternance est un scénario
  central, pas un accident. Tout ce qui n'est pas ancré peut être défait.
* **Brainstorming** : (a) ancrage constitutionnel (art. 89, Congrès aux 3/5, ou
  art. 11) — coûteux politiquement mais maximal ; (b) lois organiques et
  autorités indépendantes — résistance moyenne ; (c) ancrage européen
  (transposition, traités) — protège de l'alternance nationale, pas de la
  renégociation ; (d) irréversibilité de fait (infrastructures, systèmes
  d'information) — la moins contestable. La doctrine doit combiner les quatre,
  dans cet ordre de priorité.
* **Statut** : livré (niveau a). Levier `verrouillage_irreversibilite`
  (+2 pts de confiance, prime électorale divisée par trois) ; garde-fou
  « Verrou constitutionnel des réformes » : **son absence est signalée en
  vigilance sur toute simulation non verrouillée**, car c'est le point aveugle
  systématique de la période. L'abrogation effective par une nouvelle majorité
  n'est pas encore modélisée (voir § Limites).

### P4. La fatigue réformiste et l'usure du capital politique

* **Manque** : le coût politique d'une réforme était constant dans le temps.
* **Systématique** : le capital politique se consomme ; la littérature et
  l'histoire (second quinquennat de de Gaulle achevé sur un référendum perdu,
  cohabitation de 1986, « fracture sociale » de 1995, non-candidature de 2012,
  dissolution de 2024) montrent que **les secondes mandatures finissent mal
  quand elles n'ont pas de doctrine propre**.
* **Brainstorming** : modéliser l'usure comme un stock exogène croissant
  (0-100) qui érode la confiance, tend la société et renchérit le risque de
  censure — sans toucher aux équilibres budgétaires (l'usure est politique,
  pas comptable). Corollaire de doctrine : la mandature 2 ne doit pas empiler
  des réformes nouvelles mais **consolider, évaluer et transmettre**.
* **Statut** : livré. Champ `usure_politique_pts` ; effets : confiance
  −0,08 pt/usure, tension +0,06 pt/usure, risque de censure +0,15 pt/usure ;
  garde-fou « Usure du capital politique » (favorable ≤ 20, tolérable ≤ 35,
  vigilance ≤ 55, risqué ≤ 75, hors-sol au-delà).

### P5. Le second dividende de la dette (cycle complet de refinancement)

* **Manque** : la baisse de la charge d'intérêts n'était jamais réinjectée.
* **Systématique** : maturité moyenne 8,5 ans ⇒ sur dix ans, **tout le stock
  est refinancé** aux taux détendus par la trajectoire de désendettement.
  L'économie d'intérêts devient une marge budgétaire nouvelle — mais seulement
  pendant la seconde mandature.
* **Brainstorming** : trois usages possibles du dividende — (a) désendettement
  supplémentaire (vertueux mais invisible pour les ménages) ; (b) restitution
  ciblée pouvoir d'achat/services publics (visible, apaisant, mais à financer
  sans recréer du déficit) ; (c) investissement à cycle long (prépare la
  décennie suivante). Doctrine proposée : **réinvestir le dividende en dépense
  gagée** (les économies d'intérêts financent la dépense, le déficit ne bouge
  pas), en priorité vers (b) puis (c).
* **Statut** : livré. Levier `dividende_dette_reinvesti` (0-15 Md€/an) :
  multiplicateur 0,55 sans creusement du déficit, apaisement social
  −0,3 pt/Md€. Le scénario `double_mandature` le monte de 3 à 8 Md€ entre les
  années 7 et 10.

### P6. Les investissements à cycle long et la courbe en J

* **Manque** : aucun investissement dont le rendement dépasse le quinquennat.
* **Systématique** : EPR2, LPM, France 2030, prévention santé, recherche :
  leur coût est payé en mandature 1, leur rendement arrive en mandature 2.
  Sans modélisation de ce décalage, le modèle récompense l'immobilisme
  d'investissement.
* **Brainstorming** : registre `(année de maturité, montant)` ; rendement
  annuel de 8 % du montant investi une fois mature, plafonné à 2,5 Md€ par
  programme (calibrage exploratoire, non calibré économétriquement) ; délai de
  maturité : 5 ans. Le coût dégrade le solde l'année de l'investissement
  (courbe en J), le rendement n'arrive qu'après.
* **Statut** : livré. Levier `investissements_cycle_long` (0-20 Md€/an) ;
  les scénarios décennaux engagent 4-6 Md€/an dès les années 4-5 (EPR2, LPM
  2024-2030 et France 2030 sont déjà lancés à l'instant T) : les premiers
  programmes mûrissent en années 9-10 — pendant la seconde mandature.

### P7. Le séquencement des réformes constitutionnelles

* **Manque** : la doctrine détaille le RIC, le vote blanc, le casier B2, mais
  aucun calendrier constituant : RIC → bilan → révision constitutionnelle →
  éventuelle assemblée constituante ne tient pas en cinq ans.
* **Systématique** : une révision constitutionnelle exige soit le Congrès
  (majorité des 3/5, négociable seulement avec un Parlement stabilisé), soit un
  référendum (risqué en année électorale). La fenêtre réaliste est le début de
  la **seconde** mandature, une fois les réformes ordinaires éprouvées.
* **Brainstorming** : séquence proposée — (1) mandature 1 : réformes
  législatives et organiques (casier B2, vote blanc, RIC, non-cumul) ;
  (2) année 5 : évaluation de bilan par clauses de revoyure avant l'élection ;
  (3) année 6 : paquet constitutionnel unique soumis au Congrès (verrou des
  acquis + équilibre des pouvoirs), plutôt que des révisions successives qui
  épuiseraient le capital politique ; (4) mandature 2 : consolidation et
  transmission.
* **Statut** : documenté ici ; le scénario `double_mandature` matérialise la
  bascule en année 6 (verrou). Le contenu du paquet constitutionnel lui-même
  reste à rédiger dans le dossier de mandature (piste ouverte).

### P8. Le calendrier européen (CFP 2028-2034, règles budgétaires, 2029)

* **Manque** : l'Europe n'entrait dans le modèle que par la PDE et le TPI.
* **Systématique** : la période contient la négociation du cadre financier
  pluriannuel 2028-2034, les européennes de 2029 et la revue des règles
  budgétaires. Un pays encore sous PDE pèse peu dans ces négociations ; un
  pays sorti de la PDE avant 2029 retrouve une voix — notamment pour
  l'harmonisation fiscale (levier n° 7 du dossier, bloqué par l'unanimité).
* **Brainstorming** : la trajectoire du plan (déficit sous 3 % dès l'année 5)
  est précisément la condition de la fenêtre d'influence française de
  2029-2030 ; la clause de sauvegarde nationale « défense » (déjà modélisée)
  reste l'outil de flexibilité pour le réarmement sans rompre la crédibilité.
* **Statut** : analysé ; le modèle existant (PDE/TPI/spread) suffit à mesurer
  la crédibilité ; aucun champ nouveau nécessaire. À re-vérifier à chaque
  modification des règles européennes dans le moteur.

### P9. L'horloge démographique (retraites, dépendance)

* **Manque** : aucune dynamique de vieillissement.
* **Systématique** : les projections du COR placent la fenêtre
  d'équilibre/déséquilibre des retraites dans les années 2030, en pleine
  seconde mandature ; la dépendance (grand âge) croît mécaniquement avec les
  classes du baby-boom.
* **Brainstorming** : deux options — (a) ajouter un module démographique
  complet (lourd, hors périmètre de cette R&D) ; (b) traiter la pression
  démographique comme un **poste de dépense tendanciel** que la seconde
  mandature doit financer par le dividende de la dette (P5) plutôt que par la
  dette. Option (b) retenue pour l'instant.
* **Statut** : documenté ; le levier existant `dependance_grand_age` et le
  dividende réinvesti couvrent le premier ordre de grandeur. Module
  démographique explicite : piste ouverte.

### P10. Les budgets carbone comme unité de temps climatique

* **Manque** : le climat entrait par la taxe carbone et le MACF, pas par les
  budgets carbone.
* **Systématique** : la SNBC découpe la trajectoire en budgets carbone
  quinquennaux — **deux mandatures = deux budgets carbone**, c'est l'unité de
  compte naturelle de la politique climatique ; l'objectif -55 % de 2030 tombe
  exactement à la charnière des deux mandatures.
* **Brainstorming** : ajouter un indicateur d'écart au budget carbone courant
  et un garde-fou dédié ; articuler avec le domaine `energie_climat` existant.
* **Statut** : piste ouverte, non implémenté à ce stade (les données de budgets
  carbone nécessitent une source supplémentaire ; à traiter avec la même
  rigueur « instant T » que le reste du simulateur).

### P11. La probabilité d'au moins un choc majeur sur dix ans

* **Manque** : les chocs existent (pétrole, taïwan, hormuz, nucléaire) mais
  jamais articulés à la période de dix ans.
* **Systématique** : la fréquence observée des chocs majeurs (2008, 2011-2012,
  2020, 2022) est d'environ un tous les quatre à sept ans : **sur deux
  mandatures, la probabilité d'au moins un choc majeur est proche de 1**. La
  mandature 1 doit donc reconstruire les tampons (stocks, marges budgétaires,
  capacités) que la mandature 2 devra consommer.
* **Brainstorming** : rôles asymétriques des deux mandatures — la première
  réforme et reconstitue les tampons ; la seconde encaisse. Stress-test
  recommandé : `double_mandature` + `choc_mondial` en années 7-8 (combinable
  dès aujourd'hui via les leviers du simulateur paramétrable).
* **Statut** : documenté ; combinaison possible avec les leviers de choc
  existants. Un scénario combiné dédié est une piste ouverte.

### P12. La dynamique de confiance et le « syndrome de la seconde mandature »

* **Manque** : la confiance montait avec les réformes et s'arrêtait là.
* **Systématique** : l'histoire des secondes mandatures françaises est une
  régularité : la confiance monte en première mandature, puis s'érode si les
  résultats ne sont pas **ressentis** (écart promesse/résultat) et si le
  pouvoir s'use sans projet de transmission.
* **Brainstorming** : doctrine de la « seconde mandature utile » — consolider
  plutôt qu'empiler ; évaluer publiquement (revoyure) ; restituer le dividende
  (P5) pour rendre les résultats sensibles ; préparer la succession (le
  non-cumul dans le temps l'impose : personne ne se représente).
* **Statut** : livré côté modèle (verrou +2 confiance, revoyure +1, usure
  érode) ; la doctrine est écrite dans ce document.

### P13. L'évaluation systématique et les clauses de revoyure

* **Manque** : aucune réforme n'était évaluée avant prolongation.
* **Systématique** : sans protocole d'évaluation, la seconde mandature navigue
  à vue : quelles mesures prolonger, ajuster, abroger ? L'évaluation est aussi
  la contrepartie démocratique du verrou constitutionnel (on ne verrouille que
  ce qui est prouvé).
* **Brainstorming** : chaque réforme majeure reçoit une clause de revoyure à
  date fixe (LOLF, Cour des comptes, art. 47-2) ; le résultat d'évaluation
  conditionne la prolongation ; les années électorales deviennent des moments
  d'évaluation plutôt que des sauts dans l'inconnu.
* **Statut** : livré. Levier `clause_revoyure_evaluation` (+1 confiance,
  incertitude électorale sociale réduite de 2,0 à 0,8 pt) ; active dans le
  scénario `double_mandature` dès l'année 5.

### P14. Le renouvellement des personnes et la transmission

* **Manque** : la fin programmée des deux mandatures n'avait pas de suite.
* **Systématique** : la doctrine du non-cumul dans le temps (max 2) signifie
  qu'à la fin de la période, **l'équipe sortante ne se représente pas**. La
  mémoire institutionnelle et les compétences doivent être transmises, sous
  peine de perdre dix ans d'apprentissage.
* **Brainstorming** : le levier n° 6 du dossier propose déjà un « Collège
  civique consultatif des anciens parlementaires » (archivistes et auditeurs
  auprès des nouveaux élus, sans indemnité supplémentaire). À compléter par :
  tuilage documenté des dossiers longs (EPR2, LPM), archives ouvertes des
  évaluations (P13), formation des successeurs aux outils de pilotage.
* **Statut** : documenté ; le Collège civique existe déjà dans la doctrine —
  son calendrier de mise en place doit viser l'année 8-9, pas la dernière
  année.

### P15. La cohérence des plans budgétaires pluriannuels successifs

* **Manque** : la LPFP (loi de programmation des finances publiques) n'était
  pas un objet du modèle.
* **Systématique** : le nouveau cadre budgétaire européen impose des plans
  structurels nationaux de moyen terme (4 à 7 ans) : la période de dix ans en
  traverse **trois**. Chaque changement de plan est un moment de vérité où la
  crédibilité se gagne ou se perd face aux marchés et à la Commission.
* **Brainstorming** : articuler la trajectoire du simulateur avec les
  échéances de dépôt des plans (2025-2028 déjà adopté, puis ~2029, ~2033) ;
  l'effort structurel de 0,5 pt/an exigé sous PDE doit rester lisible sur
  chaque plan.
* **Statut** : documenté ; le champ `effort_structurel` existant porte déjà
  l'essentiel ; un rappel des échéances de plans sera ajouté dans la
  trajectoire quand le cadre sera stabilisé côté européen.


### P16. Le patrimoine public, la maintenance et la dette technique

* **Manque** : le modèle regardait surtout les nouveaux investissements ; il ne
  distinguait pas le coût d'un ouvrage neuf de l'entretien du patrimoine déjà
  construit (bâtiments, ponts, rail, écoles et hôpitaux).
* **Systématique** : dix ans de maintenance sous-financée laissent un besoin de
  rattrapage aux équipes suivantes ; une dépense reportée n'est pas une économie
  définitive. Il faut toutefois séparer besoin immobilier, entretien courant,
  mise aux normes et adaptation climatique pour éviter les doubles comptes.
* **Brainstorming** : suivre les inventaires d'actifs par propriétaire et leur
  état physique ; comparer le maintien en condition, le remplacement, la
  fermeture et la rénovation ; publier par secteur les restes à faire et les
  coûts de cycle de vie.
* **Statut** : un levier d'entretien/rattrapage et un **proxy de besoin non
  couvert** sont ajoutés à l'horizon long. La Cour des comptes estimait les
  besoins d'investissement des bâtiments publics à 140-150 Md€ à l'horizon
  2050 ; le modèle annualise le point central (145 / 24 = 6,04 Md€/an, fenêtre
  de scénario 2026-2050). Ce n'est ni un besoin officiel d'entretien annuel ni
  une dette comptable observée. Le proxy augmente ou diminue à raison d'un euro
  par euro de besoin annualisé non couvert ; il n'est pas converti en déficit,
  pénalité de qualité ou coût de réparation sans données sectorielles.
* **Source** : [Cour des comptes, analyse de l'exécution budgétaire 2023 —
  gestion du patrimoine immobilier de l'État](https://www.ccomptes.fr/sites/default/files/2024-04/NEB-2023-Gestion-patrimoine-immobilier-Etat.pdf).

### P17. L'adaptation climatique, les dommages et leur incidence

* **Manque** : l'horizon de cinq ans ne rendait pas visible la différence entre
  l'argent dépensé pour l'adaptation et les pertes climatiques qui pourraient
  être évitées sur plusieurs décennies.
* **Systématique** : prévention, protection littorale, eau, bâtiments et
  résilience ont des échéances de vie longues ; leurs bénéfices ne se lisent pas
  dans le seul solde budgétaire annuel.
* **Brainstorming** : construire des trajectoires par aléa et territoire,
  distinguer pertes assurées, pertes non assurées, reste à charge public et
  dommages macroéconomiques ; comparer plusieurs scénarios climatiques et
  horizons, sans traiter les pertes privées comme une dépense de l'État.
* **Statut** : le PNACC-3 rapporte 143 Md€ de sinistres climatiques cumulés
  estimés sur 2020-2050. Le prototype affiche 143/30 = 4,77 Md€/an comme
  **moyenne annualisée uniforme de scénario**, sans prétendre que chaque année
  subit ce montant. Le PNACC-3 rapporte également, pour des projets du fonds
  Barnier, 1 € investi pour 8 € de dommages évités. Le prototype annualise ce
  rapport sur 30 ans (8/30 par euro de stock d'adaptation) uniquement comme
  hypothèse exploratoire. Les dommages subis/évités restent **hors budget APU** ;
  seul le décaissement choisi d'adaptation affecte les dépenses publiques.
* **Sources** : [PNACC-3](https://www.ecologie.gouv.fr/sites/default/files/documents/PNACC3.pdf) ;
  [présentation officielle du PNACC-3 (10 mars 2025)](https://www.ecologie.gouv.fr/sites/default/files/documents/20250310_PNACC3_DP.pdf).

### P18. Le capital humain, l'éducation et les cohortes de formation

* **Manque** : le coût d'une dépense éducative apparaissait immédiatement,
  tandis que la temporalité des compétences acquises n'était pas distinguée.
* **Systématique** : les cohortes formées pendant la première mandature
  poursuivent leur scolarité, formation ou reconversion au cours de la seconde ;
  les mesures d'entrée et les résultats d'apprentissage ne sont pas simultanés.
* **Brainstorming** : suivre les résultats par cohorte, territoire et origine
  sociale (acquis, qualification, emploi, salaires), distinguer formation initiale
  et continue et intégrer les délais propres à chaque filière.
* **Statut** : le levier supplémentaire est comptabilisé immédiatement comme
  dépense ; le moteur enregistre le stock arrivé à maturité après **huit ans**,
  délai de scénario choisi pour rendre visible un cycle long. Aucun rendement
  PIB, salarial ni retour fiscal automatique n'est appliqué : le stock est exposé
  séparément tant qu'une évaluation causale par filière n'est pas intégrée.
* **Sources de mesure à raccorder** : [DEPP, L'état de l'École 2025](https://www.education.gouv.fr/depp/l-etat-de-l-ecole-2025-467767) ;
  données Eurostat COFOG GF09. Le délai de huit ans est une hypothèse de scénario,
  pas une statistique DEPP/OCDE.

### P19. La capacité industrielle de défense et les délais de production

* **Manque** : les crédits de défense pouvaient être lus comme une capacité
  opérationnelle immédiate ; l'outil industriel, les compétences, les chaînes
  d'approvisionnement et les stocks ont des délais distincts.
* **Systématique** : la LPM 2024-2030 traverse une mandature et son actualisation
  en 2026 prolonge des engagements jusqu'en 2030. Les commandes aujourd'hui
  financées structurent l'offre industrielle des années suivantes.
* **Brainstorming** : suivre commande → capacité/usine → cadence → livraison →
  disponibilité opérationnelle, par segment ; distinguer capacité nominale,
  carnet de commandes, dépendances et stocks réellement disponibles.
* **Statut** : un registre de cohortes d'investissements BITD rend visible le
  stock « arrivé à maturité » après six ans, proxy inspiré de la fenêtre de la
  LPM 2024-2030. Le décaissement est compté dès l'année où il est décidé ; le
  stock mature n'est pas automatiquement converti en baisse de spread, confiance
  ou disponibilité militaire. Il ne s'agit pas d'une durée moyenne auditée.
* **Source** : [Ministère des Armées, actualisation de la LPM 2024-2030
  (avril 2026)](https://www.defense.gouv.fr/sites/default/files/ministere-armees/LPM.pdf).

### P20. La capacité d'exécution de l'État et la simultanéité des réformes

* **Manque** : les réformes étaient empilées comme si les administrations
  disposaient d'une capacité illimitée, sans conflit de calendrier, de compétences
  ou de conduite du changement.
* **Systématique** : sur dix ans, les chantiers s'enchaînent ; le nombre de
  réformes simultanées et les ressources (agents, systèmes, budgets, élus locaux)
  influencent la mise en œuvre et le délai avant résultat.
* **Brainstorming** : compter les chantiers majeurs réellement ouverts, mesurer
  les postes vacants, délais de décrets, taux de réalisation et écarts à
  l'évaluation ; séquencer ou arrêter les projets sous-performants. Ne pas
  assimiler automatiquement « interrupteur activé » et réforme exécutée.
* **Statut** : un levier explicite permet à l'utilisateur de choisir le nombre
  de réformes majeures menées de front (il n'est pas déduit des interrupteurs).
  Le seuil central 8 et les effets de stress (+0,3 pt de tension et −0,15 pt de
  confiance par réforme au-delà) sont **hypothétiques**, non des seuils officiels.
  Ils doivent être soumis à une analyse de sensibilité et ne sont pas des
  estimations causales.
* **Pistes de données** : bilans annuels de performance de la Cour des comptes,
  délais de mise en œuvre des lois, inspections et évaluations LOLF ; aucun seuil
  universel ne ressort de ces sources.

### P21. Le bilan intergénérationnel sans score composite caché

* **Manque** : dette, actifs construits, besoin de rattrapage, transition
  climatique et structure démographique pouvaient être agrégés ou commentés
  ensemble sans afficher leur unité, leur porteur ni leur période.
* **Systématique** : deux mandatures redistribuent dans le temps coûts et
  avantages ; un euro de dette, un stock de compétences et un dommage climatique
  évité ne sont ni fongibles ni portés par les mêmes ménages/générations.
* **Brainstorming** : publier côte à côte dette nominale et dette/PIB, besoins
  patrimoniaux non couverts, investissements engagés et arrivés à maturité,
  risques climatiques évités et incidence par âge/revenu/territoire. N'additionner
  ces composantes qu'avec des pondérations explicites, justifiées et débattues.
* **Statut** : le JSON et la page présentent un **ledger de composantes**, sans
  indicateur synthétique « de fardeau » ni pourcentage fabriqué de nouveaux
  électeurs. La démographie est contextualisée par les projections INSEE 2026 :
  scénario central à 69,8 millions d'habitants en 2037 ; le solde naturel serait
  négatif à partir de 2025. Cela ne permet pas de déduire mécaniquement le
  renouvellement de l'électorat (inscription, âge électoral, migrations et
  participation restent à traiter).
* **Source** : [INSEE, projections de population 2026 à l'horizon 2070](https://www.insee.fr/fr/statistiques/9004289).

---

## 3. Traduction dans le code (ce qui est livré)

### 3.1 Champs de décision (`simulateur/model.py`)

Neufs champs, tous neutres par défaut (les 9 scénarios quinquennaux restent
strictement identiques, vérifié par test) :

| Champ | Type | Effet moteur |
|---|---|---|
| `annee_electorale_majeure` | bool | prime de spread +12 bps (÷3 si verrou), tension +2 pts (÷2,5 si revoyure), confiance −1 (sauf verrou) |
| `usure_politique_pts` | 0-100 | confiance −0,08×usure, tension +0,06×usure, risque de censure +0,15×usure |
| `verrouillage_irreversibilite` | bool | confiance +2, prime électorale 12→4 bps |
| `clause_revoyure_evaluation` | bool | confiance +1, incertitude électorale 2,0→0,8 pt |
| `reinvestissement_dividende_dette_mde` | Md€ | multiplicateur +0,55, déficit inchangé (dépense gagée), tension −0,3/Md€ |
| `investissements_cycle_long_mde` | Md€ | coût immédiat (solde dégradé), rendement 8 %/an plafonné 2,5 Md€ par programme après 5 ans |

### 3.2 Quatre leviers et un préréglage (`simulateur/parametres.py`)

* `verrouillage_irreversibilite` (interrupteur) — famille Institutions & démocratie ;
* `clause_revoyure_evaluation` (interrupteur) — famille État, fonction publique ;
* `dividende_dette_reinvesti` (0-15 Md€/an, montée en charge 0→100 % sur 5 ans) ;
* `investissements_cycle_long` (0-20 Md€/an) ;
* préréglage **« Deux mandatures consécutives (2027-2037) »** : le plan de
  mandature + les quatre leviers ci-dessus (le 14ᵉ préréglage du catalogue).

Le catalogue passe de 93 à **97 leviers** et de 13 à **14 préréglages** ; les
bulles explicatives des quatre nouveaux leviers sont générées automatiquement
par `simulateur/bulles.py`.

### 3.3 Deux scénarios décennaux (`simulateur/scenarios.py`, `simulateur/cli.py`)

```bash
python3 main.py double_mandature      # 2027-2037, verrou + dividende + cycle long
python3 main.py alternance_2032       # stress-test : dix ans sans verrou
```

| Année | Événement modélisé (`double_mandature`) |
|---|---|
| 1-3 | Plan de mandature quinquennal (identique au dossier global) |
| 4-5 | + investissements à cycle long déjà engagés (EPR2, LPM, France 2030) ; **année 5 = élection 2032** (prime d'incertitude, évaluation de bilan) |
| 6 | Investiture de la mandature 2, **verrou constitutionnel** des réformes |
| 7-10 | Régime de croisière, **dividende de la dette** 3→8 Md€ réinvestis, investissements 5-6 Md€/an, **usure** 10→30, **élection 2037** en année 10 |

### 3.4 Deux garde-fous (`simulateur/seuils.py`)

* **Usure du capital politique** (strate 2) : favorable ≤ 20, tolérable ≤ 35,
  vigilance ≤ 55, risqué ≤ 75, hors-sol au-delà ; cible : rester sous 20 sur
  dix ans.
* **Verrou constitutionnel des réformes** (strate 2) : actif → tolérable ;
  **absent → vigilance**, avec l'explication du risque systémique d'alternance
  sur la période de deux mandatures.

### 3.5 Tests (`tests/test_double_mandature.py` + mises à jour)

16 tests nouveaux : neutralité stricte des scénarios quinquennaux (valeurs du
README vérifiées au centième), complétude des scénarios décennaux, dynamiques
isolées (J-curve, dividende gagé, usure, prime électorale), leviers pilotant
réellement le moteur, présence des garde-fous dans le diagnostic. Les
compteurs de scénarios (11), de préréglages (14) et de leviers (97) sont mis à
jour dans `test_integration_branches.py`, `test_dashboard.py`,
`test_parametres.py` et `tests/navigateur_interface.mjs`.


### 3.6 Phase 2 — leviers, hypothèses et horizon interactif

La phase 2 ajoute quatre leviers (entretien/rattrapage du patrimoine, capital
humain à cycle long, capacité industrielle de défense, charge de réformes
simultanées) et réutilise le levier d'adaptation climatique déjà présent. Le
catalogue passe de **97 à 101 leviers** ; les 14 préréglages, les 11 scénarios
et les 31 garde-fous existants sont conservés. Le préréglage « Deux mandatures »
charge des valeurs illustratives (6 Md€/an de patrimoine, 1 Md€/an d'adaptation,
2 Md€/an de capital humain et de BITD, six réformes simultanées) — ce ne sont
pas des recommandations ni des dépenses observées.

- `POST /api/simuler` accepte maintenant `horizon` de 1 à 10 ans ; le sélecteur
  interactif propose 5 ou 10 ans. Les phases longues sont explicitement signalées
  dans la sortie, le conseiller effet papillon reprend le même horizon et le
  préréglage décennal sélectionne 10 ans.
- P16 suit un besoin patrimonial non couvert par cumul simple d'euros ; il est
  un proxy distinct de la dette Maastricht, sans surcoût macro inventé.
- P17 sépare les pertes climatiques annualisées et évitées (hors APU) des
  dépenses d'adaptation qui, elles, sont comptées au budget.
- P18/P19 exposent des stocks cohortés arrivés à maturité après 8/6 ans, sans
  taux de rendement PIB ni baisse de spread supposés.
- P20 n'infère pas la charge d'exécution depuis les interrupteurs du catalogue :
  l'utilisateur renseigne explicitement la simultanéité ; le seuil/coefficient
  reste un stress-test documenté.
- P21 ajoute `synthese.bilan_intergenerationnel` : dette, besoin patrimonial,
  investissements cumulés, stocks mûrs et risque climatique, séparés par unité.
  Aucun indicateur composite ou taux de renouvellement électoral n'est inventé.
- Le bloc « Transmission entre générations » est visible dans l'interface, dans
  les scénarios de 5 ou 10 ans et dans les exports. Les tests dédiés vérifient
  délais, séparation budget/dommages, mappage des leviers et neutralité 5 ans.


---

## 4. Résultats exécutés (moteur calé à l'instant T, données de référence)

> Exécution réelle du 7 octobre 2026 (`MoteurSimulationSystemique`, calibrage
> par défaut du projet). Avertissement : le solde au-delà de l'année 5 est la
> conséquence mécanique de marges récurrentes constantes (+60 Md€/an) sur un
> PIB nominal croissant ; une doctrine réaliste recyclera l'excédent
> supplémentaire (voir Limites).

### 4.1 Trajectoire « deux mandatures » avec les hypothèses P16-P20 (années 5 à 10)

| Année | Déficit (% PIB) | Dette (% PIB) | OAT 10 ans | Spread (bps) | Tension | Confiance | Usure | Inv. cycle long mûrs | Besoin patrimonial non couvert (proxy) | Dommages climat évités/an (proxy) |
|---|---|---|---|---|---|---|---|---|---|---|
| 5 (élection 2032) | −0,22 | 121,1 | 3,47 % | 59,2 | 5,8 | 77,5 | 0 | 0 | 0,21 Md€ | 1,33 Md€ |
| 6 (verrou) | −1,23 | 117,6 | 3,35 % | 47,2 | 5,0 | **80,5** | 0 | 0 | 0,25 Md€ | 1,60 Md€ |
| 7 (dividende 3 Md€) | −2,14 | 113,2 | 3,35 % | 47,2 | 4,1 | 80,5 | 0 | 0 | 0,29 Md€ | 1,87 Md€ |
| 8 | −3,04 | 108,0 | 3,35 % | 47,2 | 4,1 | 79,7 | 10 | 0 | 0,33 Md€ | 2,13 Md€ |
| 9 (1ʳᵉ maturité) | −3,95 | 102,0 | 3,35 % | 47,2 | 4,1 | 78,9 | 20 | 4 Md€ | 0,38 Md€ | 2,40 Md€ |
| 10 (élection 2037) | −4,83 | **95,2** | 3,39 % | **51,2** | 5,2 | 78,1 | 30 | 9 Md€ | 0,42 Md€ | 2,67 Md€ |

Le risque climatique annualisé de référence affiché est 4,77 Md€/an (hors budget APU) ;
le besoin patrimonial non couvert est un proxy de l'annualisation Cour des comptes,
pas une dette comptable. À la fin de l'année 10, les stocks éducatif et BITD mûrs
valent respectivement 4 et 8 Md€ dans le scénario, sans rendement PIB/spread ajouté.
La dette passe sous 100 % du PIB seulement en année 10. Le verrou constitutionnel
plafonne la prime électorale de 2037 à +4 bps (51,2 − 47,2) ; la confiance culmine
en année 6 puis cède à l'usure, sans revenir sous son niveau de fin de mandature 1.

### 4.2 Comparaison à l'année 10 : avec verrou vs alternance sans verrou

| Indicateur (année 10) | Double mandature (verrou) | Alternance 2032 (sans verrou) | Écart |
|---|---|---|---|
| Spread OAT-Bund | 51,2 bps | 59,2 bps | **+8 bps** (prime 2037 : 4 vs 12 bps) |
| Tension sociale | 5,2 / 100 | 11,2 / 100 | +6,0 |
| Confiance démocratique | 78,1 / 100 | 70,9 / 100 | −7,2 |
| Risque de censure | 25,3 % | 33,7 % | +8,4 pts |
| Usure politique | 30 / 100 | 70 / 100 | +40 |
| Dette (% PIB) | 95,2 | 94,1 | +1,2 pts (le scénario verrouillé finance plus d'investissements en mandature 2) |

Lecture : cette comparaison de scénarios ne constitue **pas une attribution
causale isolée au verrou**. L'alternance gèle aussi des investissements de
seconde mandature et le réinvestissement de dividendes ; ces choix modifient le
solde et la dette. Les écarts de confiance, climat social et spread doivent être
lus à la lumière de l'ensemble des hypothèses affichées, pas comme l'effet pur
d'une disposition constitutionnelle.

### 4.3 Garde-fous (console de veille)

* Sur le préréglage « Deux mandatures » : `usure_politique_pts` → favorable ;
  `irreversibilite_reformes_active` → tolérable.
* Sur toute simulation sans verrou (y compris les préréglages existants) :
  `irreversibilite_reformes_active` → **vigilance**, message expliquant le
  risque d'abrogation par alternance — c'est le rappel permanent du point
  aveugle de la période.

### 4.4 Lecture P21 du bilan intergénérationnel

Le bilan de fin de trajectoire est un ledger et non un score : dette publique
95,2 % du PIB ; besoin patrimonial non couvert (proxy) 0,42 Md€ ; investissements
à cycle long cumulés, stocks arrivés à maturité ; dommages climatiques annualisés
4,77 Md€ et dommages évités estimés 2,67 Md€/an (hors budget APU). Les stocks
mûrs ne sont pas soustraits de la dette financière et les pertes évitées ne sont
pas présentées comme des recettes de l'État. Chaque unité et hypothèse reste
visible dans l'export JSON et la section « Transmission entre générations ».

---

## 5. Limites assumées du prototype

1. **L'abrogation effective n'est pas modélisée.** Le scénario
   `alternance_2032` mesure les effets de marché et de climat de l'absence de
   verrou, mais pas le détricotage des réformes elles-mêmes (les réformes
   activées restent actives dans le moteur). Modèle d'abrogation : piste
   ouverte.
2. **L'usure est exogène.** Elle est passée en paramètre du scénario, pas
   dérivée du contenu des réformes. Un endogénéisation (nombre de réformes
   contestées × intensité) est une amélioration possible.
3. **Le rendement des investissements à cycle long (8 %/an, plafond 2,5 Md€)
   est exploratoire**, comme tout le reste du modèle : il illustre la forme de
   la courbe en J, pas un taux de retour mesuré.
4. **L'excédent croissant au-delà de l'année 5** est la conséquence mécanique
   de marges constantes dans un modèle sans recyclage politique. La doctrine
   doit décrire le recyclage (dividende, baisses ciblées, investissement) —
   c'est l'objet du chantier « volet 4 du plan décennal ».
5. **Le calendrier électoral est simplifié** : seules les années de scrutin
   national général (2032, 2037) sont modélisées ; les scrutins intermédiaires
   (européennes 2029-2034, municipales 2032) ne le sont pas encore.
6. **Le simulateur interactif propose 5 ou 10 ans**, mais pas encore une durée
   intermédiaire par défaut. L'horizon décennal est le point de départ du
   prototype P16-P21 ; ses hypothèses annualisées ne constituent pas une
   prévision de trajectoire.
7. **Pas de module démographique par âge ni de budgets carbone** (P9, P10) :
   documentés, non implémentés. P21 reprend le contexte INSEE, mais ne calcule
   pas la part des nouveaux électeurs, faute de données et de méthode adaptées.
8. **Annualisations P16/P17** : les 145/24 Md€ et 143/30 Md€ sont des
   transformations de grandeurs cumulées/horizon 2050 en moyenne de scénario ;
   elles ne sont ni des crédits annuels votés ni une trajectoire annuelle
   climatique observée. Le ratio Barnier est spécifique aux projets étudiés.
9. **Maturités P18/P19** : huit et six ans servent à rendre visibles des délais
   longs ; aucune productivité, amélioration scolaire, cadence militaire ou
   détente de taux n'est inférée automatiquement.
10. **Capacité d'exécution P20** : seuil huit et coefficients sont des paramètres
    hypothétiques. Tester au moins les seuils 5/8/12 avant toute interprétation.
11. **Incidence P21** : le ledger n'attribue pas encore actifs et passifs par
    âge, revenu, territoire ou cohorte ; les stocks ne sont pas additionnés à la
    dette en un solde patrimonial net.


---

## 6. Grille de relecture permanente (à appliquer à toute modification future)

Toute modification du projet doit répondre, point par point, à ces questions :

1. La modification tient-elle sur **une** mandature ou sur **deux** ? Si elle
   produit ses effets au-delà de cinq ans, la courbe en J (P6) est-elle
   respectée ?
2. Survit-elle à une **alternance** (P3) ? Faut-il un verrou supplémentaire ?
3. Consomme-t-elle du **capital politique** (P4) ? Où en est l'usure dans le
   calendrier des deux mandatures ?
4. Change-t-elle la **trajectoire de dette** (P5) et donc le dividende de la
   seconde mandature ?
5. Tombe-t-elle sur une **année électorale** (P2) ? La prime d'incertitude
   est-elle prise en compte ?
6. Respecte-t-elle le **calendrier européen** (P8, P15) et les **budgets
   carbone** (P10) ?
7. Est-elle **évaluable** (P13) avec une clause de revoyure datée ?
8. Qui la **reprend** à la fin des deux mandatures (P14) ?
9. Les **tests de neutralité** (scénarios quinquennaux inchangés) sont-ils
   toujours verts ?
10. Le **besoin patrimonial** P16 est-il séparé de la dette comptable, daté et
    annualisé sans être présenté comme un crédit voté ?
11. Les **pertes climatiques** P17 restent-elles distinctes des dépenses APU et
    des recettes publiques ; le rapport coût/efficacité est-il transférable ?
12. Les délais de **formation et de maturité BITD** P18/P19 ont-ils une source
    ou sont-ils étiquetés comme hypothèse, sans rendement non mesuré ?
13. La **capacité administrative** P20 est-elle renseignée explicitement, avec
    seuil testé en sensibilité plutôt qu'inféré du nombre de curseurs ?
14. Le ledger **P21** sépare-t-il unités et porteurs des coûts/actifs ; évite-t-il
    un score composite ou une part de nouveaux électeurs fabriqués ?

---

*Document rédigé le 7 octobre 2026 dans le cadre de la R&D continue du dépôt.
Toutes les valeurs chiffrées de la section 4 sont issues d'exécutions réelles
du simulateur à la date de rédaction.*
