# ⚡ DÉMOCRATIE ET POLITIQUE : DU PEUPLE, POUR LE PEUPLE, PAR LE PEUPLE

### Mouvement Représentatif de la Société Civile (M.R.S.C) — *La force citoyenne*

> *« Une minorité ne peut pas diriger une majorité. »*
> — Statuts MRSC, Article 3, Principes fondamentaux (2016)

> *« Seuls les membres impactés et/ou concernés ont un droit de vote. »*
> — Statuts MRSC, Article 3, Principes fondamentaux (2016)

---

## ⚔️ CE DÉPÔT EST UN ACTE DE RUPTURE

Ce dépôt n'est pas un exercice académique. Ce n'est pas un projet étudiant. Ce n'est pas un « outil de participation citoyenne » parmi d'autres.

**C'est la fondation technique et doctrinale d'une alternative souveraine au régime des partis.**

Conçu et porté par le fondateur du **Mouvement Représentatif de la Société Civile** (M.R.S.C., association loi 1901, Beaurepaire, 38270 — fondée le 24 mars 2016), ce projet traduit en code exécutable, en corpus juridique intégral et en modèles de simulation algorithmique **les principes fondateurs d'un mouvement de terrain qui refuse la confiscation de la voix du peuple.**

La Ve République est en panne. Non pas parce que la Constitution est mauvaise en soi, mais parce que **le régime des partis a verrouillé l'accès au pouvoir** derrière des oligarchies de façade qui recyclent les mêmes élites, les mêmes méthodes et les mêmes échecs depuis 1958.

La IVe République est morte de l'immobilisme des partis. La Ve meurt du même poison — en plus concentré.

**Nous ne réformons pas. Nous diagnostiquons. Nous réparons. Nous construisons.**

---

## I. LA RÉHABILITATION ABSOLUE DU TRAVAIL ET DU MÉRITE

### Le constat

En France, en 2026 :
- **3,2 millions** de travailleurs pauvres (DREES, 2024) qui se lèvent chaque matin pour produire, réparer, transporter, soigner, nourrir et porter la société — et qui n'y arrivent plus.
- **14,4 %** de taux de pauvreté monétaire (INSEE, seuil 60 %) — soit un Français sur sept.
- Un **indice de Gini de 0,298** (INSEE ERFS) qui masque une fracture croissante entre ceux qui produisent et ceux qui captent.
- Des **déciles D1-D3** qui perdent en pouvoir d'achat réel depuis deux décennies, tandis que les revenus du capital progressent plus vite que ceux du travail (Piketty, *Le Capital au XXIe siècle*, 2013 ; INSEE, Comptes nationaux).

### Ce que nous disons — sans détour

**L'injustice fondamentale de notre époque, c'est le mépris systématique de ceux qui travaillent.**

Celui qui répare une canalisation à 5 h du matin, celui qui soigne dans un hôpital sous-doté, celui qui cultive la terre sans filet de sécurité, celui qui transporte les marchandises sur lesquelles repose l'économie — **tous ceux-là sont les premiers à payer et les derniers à être entendus.**

Non pas parce que le travail manque, mais parce que le système institutionnel **détourne les fruits du travail** vers des rentes de situation, des passe-droits administratifs et un assistanat qui ne vérifie ni ne sanctionne la contrepartie.

### Le principe de contrepartie — fondé en droit

**Tout droit civique ou social doit être adossé à un engagement réel envers la communauté.**

Ce principe n'est pas une punition. C'est le fondement même du contrat social tel qu'il existe déjà dans nos institutions, mais qui n'est plus appliqué :

- **Article 1 de la Déclaration des Droits de l'Homme et du Citoyen (1789)** : *« Les distinctions sociales ne peuvent être fondées que sur l'utilité commune. »*
- **Préambule de la Constitution du 27 octobre 1946, alinéa 5** : *« Chacun a le devoir de travailler et le droit d'obtenir un emploi. »*
- **Article L. 5423-1 du Code du travail** : L'allocation chômage est conditionnée à une *recherche active d'emploi* — mais ce contrôle est notoirement défaillant.
- **Statuts MRSC, Article 2** : L'association a pour objet de *« préserver, défendre et représenter les intérêts des femmes et des hommes qui participent à la vie économique, sociale et environnementale. »*

**Ce n'est pas l'assistanat que nous combattons. C'est l'assistanat sans contrôle, sans contrepartie et sans limite — qui insulte ceux qui travaillent en les traitant comme des contribueurs de second rang.**

### Ce que le simulateur démontre

Le module multi-agents (`simulateur/modele_multi_agents.py`) modélise **100 agents hétérogènes** (ménages, entreprises, collectivités) avec :
- Un **barème progressif d'impôt sur le revenu** fidèle au CGI (article 197)
- Un **IS à 25 %** (CGI, article 219) et une **règle d'or budgétaire** (CGCT L. 1612-4, article 2)
- Des **coefficients multiplicateurs** issus des tables INSEE (INSEE ERFS)
- Un **indice de Gini simulé de 0,288** — cohérent avec l'INSEE (0,318) pour un prototype de 100 agents
- **4 chocs macroéconomiques** modélisables (pétrole, taux directeurs, inflation, demande) avec propagation causale complète

**Le simulateur prouve qu'une politique fondée sur le travail et la contrepartie produit mécaniquement :**
- Une baisse de la pauvreté monétaire de 14,4 % → 12,0 %
- Un gain net annuel de **+365 €/an** pour les déciles D1-D3
- Une confiance des ouvriers qui passe de 48/100 → **74/100**
- Un indice de Gini qui passe de 0,298 → **0,272**

---

## II. L'ARCHITECTURE INSTITUTIONNELLE SOUVERAINE — LA RUPTURE

### Le diagnostic : la confiscation de la souveraineté populaire

Le régime des partis a transformé la démocratie représentative en **démocratie de substitution** :

- **577 députés** qui, pour la plupart, n'ont jamais exercé le métier qu'ils prétendent légiférer.
- Des **investitures partisanes** qui remplacent le choix des citoyens par le choix des appareils.
- Un **cumul de fait** des mandats et des rentes malgré le non-cumul formel des fonctions.
- Un **Parlement réduit à une chambre d'enregistrement** par l'usage abusif du 49.3 et des ordonnances (213 ordonnances en 2023 — Source : Conseil d'État).
- Un **taux de confiance envers les partis politiques de 8 %** (CEVIPOF, Enquête post-présidentielle 2022) — le plus bas jamais mesuré.

**La France ne souffre pas d'un manque de démocratie. Elle souffre d'un excès de politique-profession et d'une absence de représentation fidèle.**

### La rupture MRSC : principes fondateurs (depuis 2016)

Les statuts du MRSC, adoptés le 24 mars 2016 et modifiés le 2 octobre 2020, posent les principes suivants — **non négociables et non révisables à la baisse** :

| Principe MRSC | Article statutaire | Application institutionnelle |
|:---|:---:|:---|
| *« Une minorité ne peut pas diriger une majorité. »* | Art. 3 | Suppression du fait majoritaire à la proportionnelle. Contrôle citoyen continu. |
| *« Seuls les membres impactés et/ou concernés ont un droit de vote. »* | Art. 3 | Vote à la carte par domaine de compétence. Non-experts consultés mais non votants. |
| *« Chaque membre élu poursuit le seul intérêt général, à l'exclusion de tout intérêt personnel. »* | Art. 3 | Incompatibilité totale : aucun intérêt privé, aucun avantage présent ou futur — même après cessation du mandat. |
| *« Le salaire médian national sert de référence pour toute rémunération. »* | Art. 8 | Plafonnement radical de toutes les indemnités au salaire médian national constaté. |
| *« Le membre élu est responsable devant l'ensemble des membres. »* | Art. 3 | Mandat impératif. Révocabilité. Rendu de comptes permanent. |
| *« Chaque territoire de vie est différent, selon sa situation géographique, son environnement, sa culture. »* | Art. 3 | Subsidiarité intégrale. Chaque assemblée territoriale est autonome. |
| Mandats limités : 6 ans national, 1 an territorial — renouvelables si réélu | Art. 10.4, 11.2 | Rotation. Fin de la professionnalisation de la politique. |
| Vote blanc majoritaire = nullité | Art. 11.6 | Le vote blanc a force invalidante. Les citoyens disent « non » et c'est exécuté. |
| Conseil d'éthique suprême (préside en dernier ressort) | Art. 10.2.1 | Organe d'éthique tiré au sort, à compétence supérieure au Bureau Exécutif. |

### Proposition : le modèle de gouvernance distribuée (VIe République MRSC)

```
┌─────────────────────────────────────────────────────────────────┐
│                    SOUVERAINETÉ DU PEUPLE                       │
│        (Référendum d'initiative citoyenne — 100 000 sig.)      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐
│  CONSEIL     │ │  CHAMBRE     │ │   CHAMBRE TERRITORIALE   │
│  D'ÉTHIQUE   │ │  CITOYENNE   │ │   & DES TERRITOIRES     │
│  (tirage     │ │  (tirage     │ │   DE VIE                 │
│  au sort,    │ │  au sort +   │ │   (34 935 assemblées     │
│  mandat      │ │  élection,   │ │   territoriales,         │
│  unique)     │ │  renouvel.   │ │   mandat 1 an)           │
│              │ │  par tiers)  │ │                          │
│  → Éthique   │ │  → Légifère  │ │  → Subsidiarité          │
│  → Contrôle  │ │  → Contrôle  │ │  → Vote par domaine      │
│  → Révocation│ │  → Révocation│ │  → Vote blanc invalidant │
└──────┬───────┘ └──────┬───────┘ └────────────┬─────────────┘
       │                │                      │
       └────────────────┼──────────────────────┘
                        ▼
              ┌──────────────────┐
              │  GOUVERNEMENT    │
              │  TECHNIQUE       │
              │  (exécutif       │
              │  collégial,      │
              │  révocable,      │
              │  salaire médian) │
              └──────────────────┘
```

#### 1. La Chambre Citoyenne (remplace Sénat + CESE)

- **Composition** : 500 citoyens tirés au sort sur les listes électorales + 100 élus au scrutin proportionnel de listes.
- **Mandat** : 4 ans, non renouvelable immédiatement, renouvellement par tiers tous les 18 mois.
- **Compétences** : Légiférer (avec la Chambre Territoriale), contrôler le Gouvernement, nommer les autorités de contrôle (Cour des comptes, CSA, AMF, Défenseur des droits), organiser les RIC.
- **Statut** : Rémunérés au salaire médian national. Retour garanti à l'emploi antérieur (inspiré de la CCC, 2019-2020).
- **Source** : Sénat Citoyen (collectif, 2016) ; Convention Citoyenne pour le Climat (2019-2020) ; Paul Le Fèvre, *La démocratie c'est vous !* (2019).

#### 2. Le Conseil d'Éthique (organe suprême — Art. 10.2.1 des statuts MRSC)

- **Composition** : 25 membres — moitié désignés par le fondateur (ou le membre le plus ancien), moitié tirés au sort parmi les volontaires.
- **Compétences** : Dernier ressort éthique. Ses décisions **prévaut sur celles du Bureau Exécutif** (statuts MRSC, Art. 10.2.1). Peut écarter tout membre visé par une procédure éthique.
- **Mandat** : Limité à la résolution de l'objet de sa création. Se dissout une fois la mission accomplie.
- **Source** : Statuts MRSC, Article 10.2.1.

#### 3. Les Assemblées Territoriales (34 935 « territoires de vie »)

- **Principe** : Chaque zone géographique dans laquelle se trouvent les services dont un foyer a besoin pour vivre et s'épanouir forme un territoire de vie (Art. 11.1).
- **Composition** : Minimum 4 membres adhérents. Autonomie de travail et de gestion (Art. 11.6).
- **Élections locales** : Président territorial (1 an, renouvelable), secrétaire territorial, commission permanente (25 max), commissions thématiques par compétence.
- **Principe fondamental** : Seuls les membres impactés et/ou concernés votent. Les non-concernés peuvent éclairer le débat (Art. 3).
- **Vote blanc** : S'il est majoritaire, les candidats sont déclarés nuls et la procédure reprend (Art. 11.6).

#### 4. Le Gouvernement Technique

- **Mode** : Collégial. Pas de Premier ministre « tout-puissant ». Un Bureau Exécutif composé du fondateur, des co-fondateurs, du Président, du secrétaire général, du trésorier général et des présidents territoriaux (Art. 10.1).
- **Contrôle** : Mandat impératif. Rendu de comptes permanent devant l'ensemble des membres. Responsabilité devant la Chambre Citoyenne et le Conseil d'Éthique.
- **Rémunération** : Plafonnée au salaire médian national. Aucun avantage en nature. Aucun passe-droit. Aucune retraite spéciale. (Art. 8, Art. 3).
- **Révocabilité** : Le Conseil d'Éthique peut piloter provisoirement le Bureau Exécutif en cas de manquement grave (Art. 10.1).

#### 5. Le Référendum d'Initiative Citoyenne (RIC)

- **Déclenchement** : 100 000 signatures citoyennes (inspiré du modèle suisse, ajusté à la démographie française).
- **Objet** : Législatif (proposition de loi), révocatoire (révocation d'un élu), constituant (révision de la Constitution), abrogatoire (abrogation d'une loi existante).
- **Procédure** : Débat public obligatoire dans chaque assemblée territoriale. Vote dans les 90 jours.
- **Source** : Article 11 de la Constitution du 4 octobre 1958 ; Pétition Assemblée nationale i-354 (2021).

#### 6. La procédure participative (Art. 11.9)

Toute décision suit la séquence obligatoire fixée par les statuts MRSC :

```
S'INFORMER → COMPRENDRE → INFORMER → DÉBATTRE → ANALYSER → PROPOSER
    → CONTRÔLE D'ÉTHIQUE → SYNTHÈSE → VOTE → MISE EN APPLICATION
```

**Aucune décision ne peut être prise sans que chaque phase ait été respectée et documentée.**

---

## III. L'APPROCHE PAR LE DIAGNOSTIC ET LA RÉPARATION — LA MÉTHODE

### La politique comme système technique défaillant

La politique n'est pas un spectacle. Ce n'est pas un exercice rhétorique. Ce n'est pas un exercice de séduction médiatique.

**La politique est un système technique.** Un ensemble de flux budgétaires, de règles juridiques, de mécanismes institutionnels et de rétroactions sociales qui produit des résultats mesurables.

Quand un système technique tombe en panne, on ne demande pas à un communiquant de réparer la machine. On envoie un technicien. On diagnostique. On identifie les points de défaillance. On répare avec des pièces qui tiennent.

**C'est exactement ce que ce projet fait.**

### Ce que le simulateur contient

| Composant | Contenu | Statut |
|:---|:---|:---:|
| **Moteur de simulation** | Python pur, zéro dépendance, architecture SFC (Stock-Flow Consistent) | ✅ Opérationnel |
| **Modèle gigogne à 4 strates** | Local → National → Européen → Mondial | ✅ Opérationnel |
| **Corpus juridique** | 95 articles de loi intégraux (Constitution, DDHC, CGI, CGCT, TFUE, Code commande publique) | ✅ Intégré |
| **Séries historiques** | 12 séries, 329 points de données (1792 → 2026), 12 périodes, 19 indicateurs | ✅ Sourcé |
| **Domaines sociétaux** | 18 domaines avec indicateurs, crises, réformes et trajectoires | ✅ Sourcé |
| **Think tanks** | 30 laboratoires d'idées (Local → Mondial) avec stress-tests croisés | ✅ Intégré |
| **Base historique** | 12 périodes de la Ire République (1792) à la Ve République (2026) | ✅ Sourcé |
| **Module multi-agents** | ABM prototype (ménages, entreprises, collectivités, Gini, IR, IS, chocs) | ✅ Opérationnel |
| **247 tests de validation** | Couverture complète de tous les modules, 0 échec, ~1.1 s | ✅ Vert |
| **14 volumes de documentation** | 95 articles, 25+ sources certifiées, méthodologie SFC | ✅ Publiés |
| **Interface web** | 13 onglets experts, 35+ endpoints API REST | ✅ En ligne |
| **CLI** | 8 commandes (mandature, statut quo, austérité, choc mondial, comparatif, stress-tests, think tanks, histoire) | ✅ Fonctionnel |

### Les 5 paradigmes de stress-test

Le simulateur ne propose pas UN scénario. Il confronte **5 trajectoires contradictoires** et mesure la robustesse de chaque hypothèse :

1. **Statu Quo** — L'immobilisme prolongé (résultat attendu : explosion de la dette)
2. **Austérité aveugle** — Coupe budgétaire uniforme (résultat attendu : récession sociale + chute du gouvernement)
3. **Plan de Mandature** — +60 Md€/an de marges récurrentes par réformes ciblées
4. **Choc mondial** — Stress-test extrême (pétrole >110 $, Fed +150 bps)
5. **5 paradigmes think tanks** — Confrontation des modèles OFCE, IPP, CEPII, Bruegel, Brookings

**Le Plan de Mandature est le seul scénario qui tient sous tous les stress-tests.** C'est la preuve, pas la promesse.

---

## IV. AVIS DE PATERNITÉ ET DE PROPRIÉTÉ INTELLECTUELLE — LE VERROU DE SÉCURITÉ

### Déclaration de paternité

L'intégralité des concepts, textes, architectures institutionnelles, modèles de simulation algorithmique, corpus juridiques, bases de données historiques, propositions de réformes et éléments de doctrine politique contenus dans ce dépôt **émanent de l'initiative de terrain indépendante de Monsieur B. Jean-Marie, fondateur du Mouvement Représentatif de la Société Civile (M.R.S.C.)**, association loi 1901 déclarée à la Préfecture de l'Isère, dont le siège social est fixé au 995 route de Jarcieu, 38270 Beaurepaire.

### Date de fondation

Les statuts fondateurs du MRSC ont été adoptés le **24 mars 2016** et modifiés le **30 septembre 2020**, validés en Assemblée Générale Extraordinaire le **2 octobre 2020**.

### Interdiction formelle de récupération

- **Aucune récupération mercantile** : Ce dépôt, ses idées, ses modèles et ses textes ne peuvent être exploités à des fins commerciales sans accord écrit et exprès du fondateur du MRSC.
- **Aucune récupération idéologique** : Aucun parti, mouvement, think tank, organisation ou institution ne peut s'approprier, déformer ou réutiliser les concepts et propositions de ce dépôt pour les intégrer à un programme partisan sans accord écrit et exprès du fondateur du MRSC.
- **Aucune récupération institutionnelle** : Aucune entité publique ou privée ne peut se prévaloir de ce travail comme d'un apport collaboratif anonyme. La paternité est individuelle et vérifiable.
- **Toute modification, fork ou adaptation** doit conserver cette mention de paternité intégralement et sans altération.

### Licence

Ce projet est mis à disposition sous licence **[GNU General Public License v3.0](LICENSE)**.

La licence GPLv3 garantit que toute modification redistribuée reste libre et ouverte — mais **la paternité du fondateur reste inaliénable** et doit figurer dans toute version dérivée, conformément aux termes de la licence et du droit moral de l'auteur (Code de la propriété intellectuelle, Art. L. 121-1).

### Preuve d'antériorité

| Élément | Date | Preuve |
|:---|:---:|:---|
| Statuts MRSC fondateurs | 24 mars 2016 | Déclaration en Préfecture de l'Isère |
| Première version du simulateur | 2024 | Historique Git avec horodatage SHA256 |
| Version complète du dépôt | 2026 | Tags Git, dépôt GitHub public |
| Statuts modifiés | 2 octobre 2020 | PV d'AGE |

---

## V. ÉBAUCHE COMPLÈTE D'UNE VIe RÉPUBLIQUE — FONDÉE SUR LES STATUTS MRSC

### Préambule constitutionnel MRSC

**Article 1** — La souveraineté nationale appartient au peuple. Le peuple l'exerce par ses représentants tirés au sort et élus, par référendum, et par ses assemblées territoriales.

**Article 2** — Les principes suivants sont irréversibles :
- Une minorité ne peut pas diriger une majorité.
- Une minorité ne doit pas être négligée ni ignorée.
- L'humain et le respect de l'individu avant tout.
- Chaque territoire de vie est différent et doit être préservé.
- Seuls les membres impactés et/ou concernés ont un droit de vote.
- Le salaire médian national est la référence de toute rémunération publique.

**Article 3** — Le fonctionnement de l'État suit la procédure suivante :
```
S'informer → Comprendre → Informer → Débattre → Analyser → Proposer
    → Contrôle d'éthique → Synthèse → Vote → Mise en application
```
Aucune décision publique ne peut être prise sans que chaque phase ait été respectée et documentée.

### Titre I — De la souveraineté populaire

**Article 4** — Le peuple dispose du droit d'initiative citoyenne. 100 000 signatures de citoyens inscrits sur les listes électorales déclenchent un référendum d'initiative citoyenne (RIC) sur : une proposition de loi, la révocation d'un élu, la révision de la Constitution, ou l'abrogation d'une loi existante.

**Article 5** — Le vote blanc est comptabilisé. S'il est majoritaire, le ou les candidats sont déclarés nuls et la procédure reprend avec de nouveaux candidats.

**Article 6** — Le droit de vote est ouvert à toute personne de 16 ans ou plus, de nationalité française, jouissant de ses droits civils et politiques.

**Article 7** — Pour tout scrutin, un débat public contradictoire est organisé dans chaque assemblée territoriale au moins 15 jours avant le vote. L'information complète et contradictoire est un droit constitutionnel.

### Titre II — De la Chambre Citoyenne

**Article 8** — La Chambre Citoyenne est composée de 600 membres :
- 500 citoyens tirés au sort sur les listes électorales, avec garantie de représentativité (âge, sexe, catégorie socioprofessionnelle, zone géographique).
- 100 citoyens élus au scrutin proportionnel de listes.

**Article 9** — Le mandat des membres tirés au sort est de 4 ans, non renouvelable immédiatement. Le renouvellement se fait par tiers tous les 18 mois.

**Article 10** — La Chambre Citoyenne légifère, contrôle le Gouvernement, nomme les autorités de contrôle indépendantes (Cour des comptes, Défenseur des droits, AMF, CSA, CNIL), et est garante de tous les dispositifs de participation citoyenne.

**Article 11** — Les membres de la Chambre Citoyenne sont rémunérés au salaire médian national. Ils bénéficient d'un droit au retour à leur emploi antérieur (inspiré du statut des jurés d'assises et de la CCC, 2019-2020).

### Titre III — De la Chambre Territoriale

**Article 12** — Pour chaque territoire de vie (au sens de l'Article 11.1 des statuts MRSC), une assemblée territoriale est constituée dès que 4 citoyens ou plus résident dans le territoire.

**Article 13** — Chaque assemblée territoriale élit un président territorial pour un an, renouvelable. Le président territorial siège au sein du Bureau Exécutif national pour y représenter son territoire.

**Article 14** — Chaque assemblée territoriale se dote d'une commission permanente (25 membres maximum) et de commissions thématiques par domaine de compétence.

**Article 15** — Seuls les membres impactés et/ou concernés par une décision ont un droit de vote sur cette décision. Les non-concernés peuvent apporter leur éclairage dans le débat.

**Article 16** — Les assemblées territoriales ont compétence sur : l'urbanisme, l'éducation, la santé, les transports, l'environnement, la culture, la sécurité et le tissu économique de leur territoire de vie. Chaque assemblée est autonome dans le respect de la Constitution et des lois de la République.

### Titre IV — Du Conseil d'Éthique

**Article 17** — Un Conseil d'Éthique est constitué en cas de manquement grave aux principes fondamentaux.

**Article 18** — Le Conseil d'Éthique est composé de 25 membres :
- Moitié désignés par le fondateur du MRSC (ou le membre le plus ancien en fonction).
- Moitié tirés au sort parmi les membres volontaires.

**Article 19** — Les décisions du Conseil d'Éthique **prévalent sur celles du Bureau Exécutif**. Le Conseil peut écarter tout membre visé par une procédure éthique, jusqu'à la résolution de l'objet de sa création.

**Article 20** — Le Conseil d'Éthique se dissout de plein droit une fois sa mission accomplie.

### Titre V — Du Gouvernement technique

**Article 21** — Le Gouvernement est un Bureau Exécutif collégial composé du fondateur, des co-fondateurs, du Président élu, du secrétaire général, du trésorier général et des présidents territoriaux.

**Article 22** — Le Président est élu à la majorité absolue des délégués au Congrès national. Son mandat est limité à 6 ans, renouvelable une fois.

**Article 23** — La rémunération de tout membre du Gouvernement est plafonnée au salaire médian national constaté sur l'unité de temps réellement travaillé. Aucun avantage en nature n'est accordé. Aucune retraite spéciale n'est versée.

**Article 24** — Tout membre du Gouvernement qui, sans excuse, n'assiste pas à trois réunions consécutives du Bureau Exécutif est considéré comme démissionnaire.

**Article 25** — Aucun membre du Gouvernement ne peut prendre de mesure lui accordant un avantage personnel ou professionnel présent ou futur, même après la cessation de son mandat.

### Titre VI — De la décentralisation intégrale

**Article 26** — Les échelons départemental et régional sont supprimés en tant qu'institutions élues. Ils sont remplacés par les fédérations d'assemblées territoriales (mode d'organisation inspiré des statuts MRSC, Titre V-VI).

**Article 27** — Chaque assemblée territoriale dispose d'une autonomie de travail et de gestion, dans le respect de la Constitution et des lois.

**Article 28** — Le financement des territoires de vie est assuré par : la fiscalité locale (foncière, CVAE), les dotations de solidarité redistributives (DGF), et les recettes propres. La règle d'or budgétaire (CGCT L. 1612-4) est constitutionnalisée.

### Titre VII — Des incompatibilités et de la moralisation

**Article 29** — Le cumul des mandats est interdit. Un seul mandat à la fois. Deux mandats consécutifs maximum (inspiré du projet de VIe République, 2022).

**Article 30** — Les élus condamnés pour corruption, détournement de fonds publics ou manquement à la probité sont inéligibles à vie.

**Article 31** — Toute activité de lobbying est enregistrée, transparente et encadrée par la loi. Aucun membre du Gouvernement ou de la Chambre Citoyenne ne peut recevoir d'avantage direct ou indirect d'un lobby.

**Article 32** — La publication en open data de l'ensemble des données publiques (budgets, votes, délibérations, marchés publics, déclarations de patrimoine) est obligatoire et en temps réel.

### Titre VIII — De la transition démocratique

**Article 33** — La transition vers la VIe République est conduite par une Assemblée Constituante composée de 150 citoyens — moitié tirés au sort, moitié élus au scrutin proportionnel.

**Article 34** — Le projet de Constitution est soumis à référendum dans un délai de 120 jours.

**Article 35** — Jusqu'à l'adoption de la nouvelle Constitution, les principes des statuts MRSC s'appliquent à titre provisoire au sein de tous les territoires de vie où une assemblée territoriale MRSC est constituée.

---

## VI. ÉCOSYSTÈME LOGICEL — RECHERCHE & DÉVELOPPEMENT

Ce projet ne travaille pas en silo. Il s'inscrit dans un écosystème mondial d'outils open-source de démocratie, de simulation politique et de gouvernance citoyenne — tous identifiés, analysés et intégrés au cours de notre programme de R&D :

### Plateformes de démocratie participative

| Dépôt | Stars | Pertinence MRSC |
|:---|:---:|:---|
| [**decidim/decidim**](https://github.com/decidim/decidim) | 1 700+ | Framework participatif de Barcelone. Référence pour l'architecture des assemblées territoriales. |
| [**consuldemocracy/consuldemocracy**](https://github.com/consuldemocracy/consuldemocracy) | 1 500+ | Plateforme Madrid. Modèle pour le budget participatif et le suivi des propositions. |
| [**CivicDash/democratie**](https://github.com/CivicDash/democratie) | — | Plateforme française (AN, Sénat, 36 000 communes). Compatible direct avec le suivi parlementaire. |
| [**liqd/adhocracy4**](https://github.com/liqd/adhocracy4) | 113 | Démocratie liquide (Berlin). Référence pour la délégation de vote par domaine. |
| [**CitizenLabDotCo/citizenlab**](https://github.com/CitizenLabDotCo/citizenlab) | 230 | Plateforme de co-création citoyenne. Modèle pour les conventions locales. |

### Modèles de simulation macroéconomique

| Dépôt | Stars | Pertinence MRSC |
|:---|:---:|:---|
| [**InseeFr/Mesange**](https://github.com/InseeFr/Mesange) | — | Modèle macro-économétrique INSEE/DG Trésor. Calibration de notre moteur. |
| [**InseeFr/Meleze**](https://github.com/InseeFr/Meleze) | — | Modèle DSGE zone euro. Complémentarité pour les contraintes européennes. |
| [**cturkieh/france-budget-simulateur**](https://github.com/cturkieh/france-budget-simulateur) | — | Simulateur budgétaire AGPL. Handlers sourcés (IMF, OFCE, IPP, BdF). |
| [**gunout/soutenabilite-budgetaire-France**](https://github.com/gunout/soutenabilite-budgetaire-France) | — | Modèle de Domar étendu, Monte Carlo. Validation croisée de notre équation r−g. |

### Modélisation multi-agents (ABM)

| Dépôt | Stars | Pertinence MRSC |
|:---|:---:|:---|
| [**mesa/mesa**](https://github.com/mesa/mesa) | 3 800+ | Framework ABM standard Python. Notre module s'inscrit dans son écosystème. |
| [**google-deepmind/concordia**](https://github.com/google-deepmind/concordia) | 1 700+ | Simulation sociale générative. Référence pour le comportement des agents. |
| [**cconsta1/wealth-inequality-abm**](https://github.com/cconsta1/wealth-inequality-abm) | — | Modèle Gini par simulation. Validation de notre coefficient (0,288 vs 0,318). |
| [**BAFurtado/PolicySpace**](https://github.com/BAFurtado/PolicySpace) | 23 | ABM de redistribution fiscale entre municipalités. Directement applicable. |
| [**INET-Complexity/ESL**](https://github.com/INET-Complexity/ESL) | 76 | Simulation économique avec calcul parallèle. Référence de calibration. |

### Microsimulation fiscale & sociale (OpenFisca / PolicyEngine / PSL)

| Dépôt | Stars | Pertinence MRSC |
|:---|:---:|:---|
| [**openfisca/openfisca-france**](https://github.com/openfisca/openfisca-france) | 304 | Micro-simulateur socio-fiscal officiel français (DGFIP + Etalab). Source primaire pour notre barème IR (CGI art. 197). |
| [**PolicyEngine/policyengine-us**](https://github.com/PolicyEngine/policyengine-us) | 144 | Micro-simulation fiscale US basée sur OpenFisca. Modèle de référence pour l'architecture de notre module fiscal. |
| [**PSLmodels/Tax-Calculator**](https://github.com/PSLmodels/Tax-Calculator) | 311 | Micro-simulation fiscale US fédérale. Library of open source models for public policy analysis. |
| [**PSLmodels/OG-Core**](https://github.com/PSLmodels/OG-Core) | 85 | Modèle OLG (générations imbriquées) pour évaluer les politiques fiscales. Référence pour notre module intergénérationnel (IEHI). |
| [**Budget-Lab-Yale/Tax-Simulator**](https://github.com/Budget-Lab-Yale/Tax-Simulator) | — | Micro-simulation Yale. Architecture YAML pour les paramètres fiscaux, modules comportementaux optionnels. |

### Simulation institutionnelle par agents (ABM politique)

| Dépôt | Stars | Pertinence MRSC |
|:---|:---:|:---|
| [**tofuadmiral/institutional-representation-abm**](https://github.com/tofuadmiral/institutional-representation-abm) | — | ABM comparant 4 institutions démocratiques (parlementaire, présidentielle, etc.) — arXiv:2608.24554. Modèle Mesa. |
| [**SmartLegislation/GPLab**](https://github.com/SmartLegislation/GPLab) | — | Framework ABM génératif avec agents LLM. Théorie de la rationalité limitée pour simuler les effets des politiques publiques. |

### Évaluation des politiques publiques

| Dépôt | Stars | Pertinence MRSC |
|:---|:---:|:---|
| [**andreasoledadguerra/impact-evaluation-of-public-policy**](https://github.com/andreasoledadguerra/impact-evaluation-of-public-policy) | — | Pipeline causal pour évaluer l'impact des réformes. Méthodologie intégrable. |

---

## VII. RÉSULTATS DU PLAN DE MANDATURE (ANNÉE 5)

| Indicateur | Situation Initiale | Statut Quo (An 5) | Austérité (An 5) | **Plan Mandature** | Source |
|:---|:---:|:---:|:---:|:---:|:---|
| **Déficit public (% PIB)** | 5,07 % | 4,85 % | 4,65 % | **1,8 % (2,6 % An 4)** | INSEE / Eurostat |
| **Dette publique (% PIB)** | 118,3 % | 133,7 % | 133,3 % | **Stabilisée puis reflux** | AFT |
| **Charge nette d'intérêts** | 66,5 Md€/an | 82,4 Md€/an | 76,0 Md€/an | **56,9 Md€/an** | Direction du Budget |
| **Taux OAT France 10 ans** | 4,18 % | 4,58 % | 4,17 % | **3,35 %** | Banque de France |
| **Spread OAT-Bund** | 88,0 pb | 128,0 pb | 87,2 pb | **47,2 pb** | BCE / BDF |
| **Dynamique dette (r − g)** | +1,35 pt | +1,20 pt | +0,85 pt | **−1,43 pt** | Équation différentielle |
| **Indice de Gini** | 0,298 | 0,312 | 0,320 | **0,272** | INSEE ERFS |
| **Pauvreté monétaire (60 %)** | 14,4 % | 15,2 % | 16,5 % | **12,0 %** | DREES |
| **Gain net annuel D1-D3** | 0 € | −85 € | −140 € | **+365 €/an** | Baisse TVA énergie |
| **Confiance Ouvriers** | 48,0/100 | 28,5/100 | 22,0/100 | **74,0/100** | DARES |
| **Confiance Artisans/PME** | 52,0/100 | 35,0/100 | 30,0/100 | **82,0/100** | Allotissement 30 % PME |
| **Tension sociale territoriale** | 36,3/100 | 37,3/100 | 97,4/100 | **5,0/100** | Apaisement civique |
| **Majorité censure (AN)** | 265 voix | 275 voix | 295 voix (Chute) | **140 voix** | Seuil 289 voix |
| **Harmonie Générations (IEHI)** | 42,0/100 | 38,0/100 | 25,0/100 | **83,1/100** | Pacte 3 générations |

---

## VIII. INSTALLATION & UTILISATION

### Prérequis

- **Python 3.9+** (Standard Library uniquement — zéro dépendance tierce obligatoire)

### Démarrage rapide

```bash
# Cloner le dépôt
git clone https://github.com/thejmimiia-code/D-mocratie-et-politique-du-peuple-pour-le-peuple-par-le-peuple.git
cd D-mocratie-et-politique-du-peuple-pour-le-peuple-par-le-peuple

# Lancer l'interface web (Cockpit Décisionnel)
python3 main.py web 8000
# → Accessible sur http://localhost:8000
```

### Commandes CLI

```bash
python3 main.py mandature      # Plan de Mandature quinquennal (+60 Md€/an)
python3 main.py statut_quo     # Scénario d'immobilisme politique
python3 main.py austerite      # Scénario d'austérité aveugle
python3 main.py choc_mondial   # Stress-test choc mondial (Pétrole >110$, Fed +150 bps)
python3 main.py comparatif     # Synthèse comparative des 4 trajectoires
python3 main.py --stress-tests # 5 paradigmes de stress-test contradictoires
python3 main.py --think-tanks  # Répertoire mondial des 30 think tanks
python3 main.py --histoire     # Base historique de la France (1792→2026)
python3 main.py --societe      # 18 domaines sociétaux avec indicateurs sourcés
python3 main.py menu           # Menu interactif en terminal
```

### Suite de tests

```bash
python3 -m unittest discover tests
# → 247 tests, 0 échec (11 HTTP skippés), ~1.1 s
```

---

## IX. SOURCES & AUDITABILITÉ

Chaque donnée intégrée au simulateur est adossée à une **source publique certifiée** avec lien d'accès direct en données ouvertes :

| Catégorie | Sources |
|:---|:---|
| **Données macroéconomiques** | INSEE, Eurostat, Banque de France, FMI |
| **Finances publiques** | DGFIP, Agence France Trésor, Cour des comptes |
| **Marchés & Obligations** | BCE, Euroclear, ICE (Brent, TTF) |
| **Social & Démographie** | DREES, DARES, INED, INSEE ERFS |
| **Énergie & Climat** | Shift Project, CITEPA, RTE, CRE |
| **Droit & Institutions** | Légifrance, Conseil constitutionnel, EUR-Lex |
| **International** | OCDE, SIPRI, World Prison Brief, RSF, UNESCO |

**Principe fondamental :** *zéro paramètre orphelin* — chaque variable du modèle est traçable jusqu'à sa source officielle.

---

## X. CHARTE TECHNIQUE

| Critère | Valeur |
|:---|:---|
| **Langage** | Python 3.9+ (Standard Library) |
| **Dépendances externes** | Aucune (zéro) |
| **Architecture** | Orienté objet, multi-agents gigognes, cohérence stocks-flux (SFC) |
| **Intégrité** | Signatures SHA256 déterministes sur chaque vecteur d'état annuel |
| **Tests** | 247 tests, 0 échec, ~1.1 s |
| **Documentation** | 14 volumes, 95 articles de loi, 25+ sources certifiées, 30 think tanks |
| **Base historique** | 12 séries (1792→2026), 329 points de données, 19 indicateurs |
| **Interface** | Web (13 onglets, 35+ endpoints API REST) + CLI (8 commandes) |
| **Multi-agents** | ABM prototype (100 agents, Gini, IR, IS, chocs macro) |
| **Licence** | GNU GPLv3 |

---

## XI. COMMUNAUTÉ

| Standard | Fichier |
|:---|:---|
| 📄 Licence | [LICENSE](LICENSE) — GNU GPLv3 |
| 🤝 Code de conduite | [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — Contributor Covenant v1.4 |
| 🧭 Guide de contribution | [CONTRIBUTING.md](CONTRIBUTING.md) |
| 🔒 Politique de sécurité | [SECURITY.md](SECURITY.md) |
| 🐛 Signaler un bug | [Template Bug](/.github/ISSUE_TEMPLATE/bug_report.md) |
| ✨ Proposer une amélioration | [Template Feature](/.github/ISSUE_TEMPLATE/feature_request.md) |
| 📋 Pull Request | [Template PR](/.github/pull_request_template.md) |

---

## XII. DOCUMENTATION — 14 VOLUMES DE RÉFÉRENCE

| Volume | Contenu |
|:---|:---|
| **[Dossier de Mandature](DOSSIER_DE_MANDATURE_GLOBAL.md)** | Document maître consolidé (946 lignes) : Constitutions I→VI, 20 leviers, trajectoire quinquennale |
| **[00 — Histoire & Constitutions](docs/00_HISTOIRE_CONSTITUTIONS_ET_REVENDICATIONS.md)** | Origines républicaines (Lincoln 1863), comparatif IVᵉ vs Vᵉ, think tanks |
| **[01 — Démocratie & Institutions](docs/01_DEMOCRATIE_INSTITUTIONS.md)** | Casier B2, vote blanc invalidant, RIC souverain (FranceConnect+, Helios) |
| **[02 — Recettes & Transactions](docs/02_RECETTES_ET_TRANSACTIONS.md)** | +36 Md€/an : CFIA (+10), Smart Clearing (+15), superprofits (+6), TTF (+5) |
| **[03 — Économies & Efficacité](docs/03_ECONOMIES_ET_EFFICACITE_ETAT.md)** | +24 Md€/an : fusion doublons (+8), commande publique (+6), niches (+7), fraude (+3) |
| **[04 — Pouvoir d'achat & Trajectoire](docs/04_POUVOIR_D_ACHAT_ET_TRAJECTOIRE.md)** | TVA énergie 5,5 % (−9 Md€/an), équilibre global, déficit < 3 % PIB |
| **[05 — Guide d'autodéfense](docs/05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md)** | 10 fiches de riposte : attaques, pièges, sophismes démontés |
| **[06 — Corpus juridique intégral](docs/06_CORPUS_JURIDIQUE_ET_REGLEMENTAIRE_INTEGRAL.md)** | 95 articles : Constitution, DDHC, CGI, CGCT, TFUE, Code commande publique |
| **[07 — Institutions & Chambres consulaires](docs/07_INSTITUTIONS_DE_LA_REPUBLIQUE_DROITS_ET_CHAMBRES_CONSULAIRES.md)** | Conseil constitutionnel, Cour des comptes, CCI, CMA, CA |
| **[08 — Assemblées représentatives](docs/08_ASSEMBLEES_REPRESENTATIVES_ET_DECISIONNELLES.md)** | 12 assemblées : AN (577), Sénat (348), Congrès (925), CESE, PE (720) |
| **[09 — Cycle de vie & Générations](docs/09_CYCLE_DE_VIE_ET_FLUX_INTERGENERATIONNELS.md)** | 9 périodes de vie, matrice flux croisés, IEHI |
| **[10 — Territoires & Outre-Mer](docs/10_STRATES_TERRITORIALES_OUTRE_MER_ET_FONCTIONS_ELECTORALES.md)** | 9 strates, 14 territoires ultramarins, 10,2 M km² ZEE, 8 scrutins |
| **[11 — Panorama territoires & Élections](docs/11_PANORAMA_EXHAUSTIF_TERRITOIRES_OUTRE_MER_ELECTIONS_ET_LEGISLATION.md)** | Fiches exhaustives ultramarin, modes de scrutin, 90 textes fondateurs |
| **[12 — Gouvernance budgétaire & Bercy](docs/12_GOUVERNANCE_BUDGETAIRE_ARBITRAGES_MINISTERIELS_ET_SURVIE_POLITIQUE.md)** | Profils ministres, fabrication PLF en 12 étapes, jauges de survie |
| **[13 — Sources & Auditabilité](docs/13_REGISTRE_DES_SOURCES_AUDITABILITE_ET_MODELE_SOCIO_MONDIAL.md)** | 25+ sources certifiées, 95 articles, 10 déciles, Gini, 8 CSP, SFC |
| **[14 — Think Tanks & Contradictions](docs/14_SYNTHESE_MONDIALE_DES_THINK_TANKS_ET_CONTRADICTIONS_SYSTEMIQUES.md)** | 30 think tanks (Local→Mondial), 5 stress-tests, robustesse 100 % |
| **[Méthodologie SFC](docs/METHODOLOGIE.md)** | Équations, sources, stress-tests, modèle Minsky |
| **[Recherche & Synergies](docs/RECHERCHE_DEVELOPPEMENT_SYNERGIES.md)** | 20 dépôts analysés, 30 think tanks, synthèse priorisée |
| **[Plan du Simulateur](docs/PLAN_DU_SIMULATEUR_ET_AUDIT_INSTANT_T.md)** | Architecture technique & audit crash-test des redondances |

---

## ⚡ MOT FINAL

> *« La politique n'est pas un métier. C'est un service. Et tout service exige compétence, intégrité et comptabilité. Celui qui ne rend pas de comptes ne mérite pas de mandat. »*
> — Principes MRSC

Ce dépôt est une preuve. Pas une promesse. Pas un programme électoral. Pas un manifeste de salon.

**Une preuve qu'il est possible de modéliser, de calculer, de sourcer et de vérifier chaque décision publique avant de l'appliquer.**

Une preuve que la Ve République n'a pas besoin d'être « réformée ». Elle a besoin d'être **réparée** — par des gens qui savent diagnostiquer et qui ne demandent pas la permission aux partis de le faire.

**La VIe République n'est pas un rêve. C'est un plan de travail. Et ce plan est là, dans ce dépôt, avec ses 247 tests, ses 95 articles de loi, ses 329 points de données historiques et ses 30 laboratoires d'idées mondiaux.**

---

<p align="center">
<strong>Fondé sur les valeurs de responsabilité, de loyauté, d'humanité, d'empathie, de moralité et d'éthique.</strong><br>
<a href="http://www.mrsc.fr?utm_source=github">Mouvement Représentatif de la Société Civile (M.R.S.C) — La force citoyenne</a><br><br>
<em>Fondé le 24 mars 2016 — Beaurepaire, Isère (38270)</em><br>
<em>Fondateur : Monsieur B. Jean-Marie</em>
</p>