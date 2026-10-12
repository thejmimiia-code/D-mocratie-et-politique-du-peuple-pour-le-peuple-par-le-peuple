# 21. Objections ouvertes : le registre

> Toute objection reçue est enregistrée ici, avec son numéro, son statut, la concession qu'elle a obtenue et la modification qu'elle a provoquée. Ce tableau est la sortie de `simulateur/contradiction.py` : une objection qui n'y figure pas n'a pas été traitée.

Les objections qui visent une **mesure** sont développées sous la fiche correspondante du guide (`docs/05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md`) ; celles qui visent le **modèle** sont développées ici, parce qu'aucune fiche ne les porte.

---

## 1. Le registre complet

| # | Objection | Famille | Statut | Suivi |
|---|---|---|---|---|
| 1 | Casier judiciaire B2 pour l'éligibilité | mesure | `partiellement_concedee` | issue #7, § 1 |
| 2 | Vote blanc invalidant | mesure | `en_cours` | issue #7, § 2 |
| 3 | Référendum d'initiative citoyenne sécurisé | mesure | `partiellement_concedee` | issue #7, § 3 |
| 4 | Traque de la grande fraude fiscale par IA | mesure | `partiellement_concedee` | issue #6 |
| 5 | Conditionnement des aides aux entreprises | mesure | `en_cours` | issue #6 |
| 6 | Taxe sur les superprofits et les rachats d'actions | mesure | `partiellement_concedee` | issue #6 |
| 7 | Extension de la taxe sur les transactions financières | mesure | `en_cours` | issue #6 |
| 8 | Fusion des doublons territoriaux | mesure | `partiellement_concedee` | issue #6 |
| 9 | Mutualisation de la commande publique | mesure | `en_cours` | issue #6 |
| 10 | Baisse de la TVA sur l'énergie à 5,5 % | mesure | `partiellement_concedee` | issue #6 |
| 11 | Recettes et dépenses figées en euros courants | modèle | `partiellement_concedee` | issue #4, H1 |
| 12 | Transmission instantanée des taux à la charge de la dette | modèle | `partiellement_concedee` | issue #4, H2 |
| 13 | Confiance démocratique : +45 points en un an, sans source | modèle | `en_cours` | issue #4 |
| 14 | Tension sociale : un plancher de 5 sur 100 pendant quatre ans | modèle | `en_cours` | issue #4 |
| 15 | Prime de risque politique modifiée seulement au-dessus de 50 Md€ d'effort | modèle | `en_cours` | issue #4 |
| 16 | Spread en dérive selon le calendrier plutôt que selon la dette | modèle | `en_cours` | issue #4 |
| 17 | Effet de falaise au seuil de 50 Md€ d'effort | modèle | `en_cours` | issue #4 |
| 18 | L'inflation est calculée mais n'alimente ni le PIB nominal ni les recettes | modèle | `en_cours` | issue #4 |
| 19 | La branche austérité ne réduit pas le déficit | modèle | `en_cours` | issue #4 |
| 20 | Un test unitaire transforme la thèse du projet en invariante | modèle | `en_cours` | issue #9, § 4 |
| 21 | Chambre citoyenne tirée au sort : le levier existe, la doctrine manque | modèle | `en_cours` | issue #7, § 4 |
| 22 | Le laboratoire montre que le seuil de 3 % ne discrimine pas | modèle | `refutee` | docs/LABORATOIRE_RD.md |
| 23 | « Notifié » n'est pas « encaissé », et il n'existe pas de réserve de gage | modèle | `en_cours` | issue #6 |
| 24 | Les hypothèses du moteur ne sont pas un jeu nommé | modèle | `ouverte` | issue #4 — chantier hypotheses.py |

### Comment lire les statuts

- **`refutee`** — traitée et la réponse tient : la critique porte à côté, sous sa forme forte.
- **`partiellement_concedee`** — une partie est admise et le texte, le chiffre ou la mesure change.
- **`concedee`** — admise entièrement : la mesure est abandonnée, remplacée ou re-écrite.
- **`en_cours`** — reconnue comme valable, traitement non terminé et suivi par une issue.
- **`ouverte`** — reçue et reconnue, chantier non engagé — le dire plutôt que de l'afficher « en cours ».

---

## 2. Les objections de modèle, développées

### 11. Recettes et dépenses figées en euros courants

« Votre modèle est faux, donc le plan est faux. »

<!-- OBJECTIONS FORTES : bloc généré par outils/generer-objections.py, ne pas éditer à la main -->

### La meilleure version de l'objection

> « Le PIB nominal de votre moteur croît de 1,9 % par an, mais la base de recettes et de dépenses primaires reste constante en euros courants sur les cinq années. Conséquence mécanique : le ratio de déficit s'améliore d'environ deux dixièmes de point sans aucune mesure, ce qui avantage toute politique simulée — y compris le statu quo, qui passe de 5,11 % à 4,85 % par pure convention de calcul. »

*Attaque d'origine conservée pour mémoire :*

> « Votre modèle est faux, donc le plan est faux. »

### Ce que nous concédons

L'hypothèse doit être rendue explicite et corrigée : recettes et dépenses suivent l'activité nominale, au moins à élasticité unitaire. Le contre-calcul documenté replace l'atterrissage du plan autour de 3,05 % en année 5 avec cette seule correction — toujours très au-dessus de zéro, mais plus sous 3 %.

### Ce que nous maintenons, et pourquoi

L'écart au statu quo reste large — de l'ordre de 1,8 point de PIB — et c'est lui que le simulateur sert à mesurer, pas une valeur absolue idéale. Le dépôt écrit depuis l'origine que le modèle n'est pas une prophétie ; corriger une hypothèse de convention ne change pas le sens du résultat.

### Ce qui nous ferait changer d'avis

Si l'indexation des recettes sur le PIB nominal ne changeait pas le classement des politiques comparées (le plan restant meilleur que le statu quo et que l'austérité), l'argument du plan serait confirmé ; si elle inversait un classement, c'est la mesure concernée qu'il faudrait réexaminer.

### Statut et suites

**`partiellement_concedee`** — une partie est admise et le texte, le chiffre ou la mesure change.

*Ce que cela change dans le dépôt :* hypothèse à basculer dans un jeu nommé (bas / central / haut), pas en dur.

*Suivi :* issue #4, H1.

### Sources

- **Interne** : `simulateur/moteur.py` — PIB nominal et base de recettes
- **Interne** : `docs/METHODOLOGIE.md` — hypothèses et conventions
- **Externe** : Audit d'issue #4 (28/09/2026), contre-calcul du commit 7536de7 — *2026* (portée par issue #4)

<!-- fin du bloc généré -->

---

### 12. Transmission instantanée des taux à la charge de la dette

« Vos chiffres ne sont pas réalistes. »

<!-- OBJECTIONS FORTES : bloc généré par outils/generer-objections.py, ne pas éditer à la main -->

### La meilleure version de l'objection

> « Votre moteur applique la variation de taux à tout le stock de dette la même année, alors que le document de référence du dépôt cite la règle de sensibilité de l'Agence France Trésor : +100 points de base donnent +3,5 Md€ la première année, +7,2 la deuxième et +15,4 la cinquième, pour une maturité moyenne de 8,5 ans. Votre plan profite donc d'une détente des taux arrivée en année 5 comme si elle s'appliquait instantanément, soit environ 9,5 Md€ d'économie au lieu de 3. »

*Attaque d'origine conservée pour mémoire :*

> « Vos chiffres ne sont pas réalistes. »

### Ce que nous concédons

La transmission doit être amortie selon le profil de refinancement, sinon l'économie d'intérêts est surestimée d'un facteur trois la dernière année. C'est un défaut de calibrage, pas d'intention.

### Ce que nous maintenons, et pourquoi

Le mécanisme de la prime de risque et de la charge d'intérêts reste correctement orienté et borné ; c'est le calendrier qui est trop rapide. Un profil amorti rend le plan moins spectaculaire en année 5 et plus crédible sur dix ans — c'est même un argument de campagne : la dette se refinance sur huit ans et demi, et un plan quinquennal est jugé sur sa trajectoire, pas sur sa dernière année.

### Ce qui nous ferait changer d'avis

Si l'on observait sur données AFT réelles une transmission plus rapide que le profil de maturité (par exemple via des émissions à taux variable ou indexées), le calendrier serait repris dans ce sens ; le document de référence du dépôt est la référence, il n'est pas mis de côté pour sauver un chiffre.

### Statut et suites

**`partiellement_concedee`** — une partie est admise et le texte, le chiffre ou la mesure change.

*Ce que cela change dans le dépôt :* profil de transmission à caler sur la maturité moyenne (8,5 ans) en option.

*Suivi :* issue #4, H2.

### Sources

- **Interne** : `simulateur/moteur.py` — charge de la dette
- **Interne** : `docs/PLAN_DU_SIMULATEUR_ET_AUDIT_INSTANT_T.md` — § II.2 — sensibilité AFT
- **Externe** : Audit d'issue #4 (28/09/2026) : +100 pb → +3,5 / +7,2 / +15,4 Md€ — *2026* (portée par issue #4)

<!-- fin du bloc généré -->

---

### 13. Confiance démocratique : +45 points en un an, sans source

« Vos indicateurs sont des inventions. »

<!-- OBJECTIONS FORTES : bloc généré par outils/generer-objections.py, ne pas éditer à la main -->

### La meilleure version de l'objection

> « Votre indice de confiance part de 27,5 et atteint 77,5 dès l'année 2, par des bonus fixes attribués mesure par mesure (RIC +14, B2 +10, vote blanc +8, pantouflage +7, régimes spéciaux +6, non-cumul +5). Aucun de ces coefficients n'est sourcé, une confiance qui monte de 45 points en douze mois n'a aucun précédent, et votre modèle ne la fait jamais redescendre — même dans la branche austérité, où la tension sociale atteint 97 sur 100. »

*Attaque d'origine conservée pour mémoire :*

> « Vos indicateurs sont des inventions. »

### Ce que nous concédons

L'indicateur doit être calibré sur une mesure existante et datée — le baromètre de la confiance politique du CEVIPOF — avec une montée progressive et un retour à la moyenne. Une confiance qui ne redescend pas n'est pas un indicateur, c'est une décoration.

### Ce que nous maintenons, et pourquoi

L'intention est bonne : relier les réformes institutionnelles à un effet mesurable plutôt qu'à un commentaire. Et la direction de l'effet n'est pas sérieusement contestable — les réformes de transparence et de participation sont celles qui se traduisent le plus vite dans les enquêtes. Ce qui manque est l'ampleur et le rythme.

### Ce qui nous ferait changer d'avis

Si, après deux ans, l'indicateur réel du CEVIPOF ne bougeait pas dans le sens prévu par le modèle, les coefficients seraient révisés : le baromètre est public, la comparaison sera possible, et c'est précisément pour cela qu'il faut le nommer.

### Statut et suites

**`en_cours`** — reconnue comme valable, traitement non terminé et suivi par une issue.

*Ce que cela change dans le dépôt :* calibrage sur un baromètre public, montée progressive, retour à la moyenne.

*Suivi :* issue #4.

### Sources

- **Interne** : `simulateur/moteur.py` — confiance démocratique, bonus par mesure
- **Interne** : `docs/METHODOLOGIE.md` — conventions et limites
- **Externe** : Baromètre de la confiance politique (CEVIPOF) — mesure de référence à adopter — *annuel* (portée par issue #4)

<!-- fin du bloc généré -->

---

### 14. Tension sociale : un plancher de 5 sur 100 pendant quatre ans

« Vos courbes sont trop lisses pour être vraies. »

<!-- OBJECTIONS FORTES : bloc généré par outils/generer-objections.py, ne pas éditer à la main -->

### La meilleure version de l'objection

> « Votre tension sociale tombe à 5 sur 100 dès l'année 2 et y reste quatre ans : aucune société ne vit quatre années d'apaisement parfait après une décennie de conflits sociaux, de gilets jaunes et de réforme des retraites. Le plancher devrait être plus haut, avec des chocs et des effets décroissants. »

*Attaque d'origine conservée pour mémoire :*

> « Vos courbes sont trop lisses pour être vraies. »

### Ce que nous concédons

Le plancher est invraisemblablement bas : il doit remonter de l'ordre de 15 à 20, avec des chocs possibles et une décrue progressive des effets d'une mesure. Un modèle où la tension ne peut pas remonter après un choc décrit un pays pacifié par hypothèse, pas une société réelle.

### Ce que nous maintenons, et pourquoi

Le sens de l'effet est défendable : lever une injustice fiscale et rendre du pouvoir d'achat fait baisser la tension, et le modèle sert à comparer des politiques entre elles. Un plancher plus haut ne change pas le classement ; il change la crédibilité de la courbe, et c'est déjà beaucoup.

### Ce qui nous ferait changer d'avis

Si un plancher à 15 inversait le classement entre le plan et le statu quo sur la tension, c'est que l'effet des mesures était surestimé, et la revue porterait sur les coefficients de baisse, pas sur le plancher.

### Statut et suites

**`en_cours`** — reconnue comme valable, traitement non terminé et suivi par une issue.

*Ce que cela change dans le dépôt :* plancher à relever et effets à rendre décroissants.

*Suivi :* issue #4.

### Sources

- **Interne** : `simulateur/moteur.py` — tension sociale locale
- **Externe** : Audit d'issue #4 (28/09/2026) : « quatre ans à 5/100 n'est pas crédible » — *2026* (portée par issue #4)

<!-- fin du bloc généré -->

---

### 15. Prime de risque politique modifiée seulement au-dessus de 50 Md€ d'effort

« Votre marché ne réagit pas à la politique. »

<!-- OBJECTIONS FORTES : bloc généré par outils/generer-objections.py, ne pas éditer à la main -->

### La meilleure version de l'objection

> « Votre scénario d'austérité atteint 97 sur 100 de tension sociale et un spread reste inchangé à 87,2 points de base — parce que la prime de risque politique n'est modifiée que dans la branche où l'effort dépasse 50 Md€. Autrement dit, votre modèle contredit son propre récit : les marchés ne sanctionnent jamais un pays que vous décrivez au bord de la fronde. »

*Attaque d'origine conservée pour mémoire :*

> « Votre marché ne réagit pas à la politique. »

### Ce que nous concédons

La prime de risque doit dépendre de la tension et du risque de censure dans toutes les branches — c'est une erreur de cohérence interne, et c'est le genre de défaut qu'un économiste relève en dix minutes.

### Ce que nous maintenons, et pourquoi

L'économie du modèle garde son sens : c'est bien la crédibilité budgétaire qui commande le spread à long terme, et le plan améliore la trajectoire de dette. Corriger la fonction élargit le canal politique sans casser le canal budgétaire.

### Ce qui nous ferait changer d'avis

Si, prime élargie, l'austérité cessait d'être la politique la plus coûteuse en spread, l'hypothèse selon laquelle les marchés sanctionnent la contestation serait à revoir — le contraire d'un problème : ce serait un résultat.

### Statut et suites

**`en_cours`** — reconnue comme valable, traitement non terminé et suivi par une issue.

*Ce que cela change dans le dépôt :* prime de risque à rendre dépendante de la tension partout.

*Suivi :* issue #4.

### Sources

- **Interne** : `simulateur/moteur.py` — branche effort ≥ 50 Md€
- **Externe** : Audit d'issue #4 (28/09/2026) : austérité à 97/100 de tension, spread inchangé — *2026* (portée par issue #4)

<!-- fin du bloc généré -->

---

### 16. Spread en dérive selon le calendrier plutôt que selon la dette

« Votre spread suit une pente arbitraire. »

<!-- OBJECTIONS FORTES : bloc généré par outils/generer-objections.py, ne pas éditer à la main -->

### La meilleure version de l'objection

> « Votre spread suit une pente de 8 points de base par an indexée sur le numéro de l'année, pas sur le ratio de dette, ni sur le déficit, ni sur le risque perçu. Une convention de calendrier n'est pas un modèle financier : deux pays ayant la même dette mais des élections à des dates différentes n'ont pas des spreads différents. »

*Attaque d'origine conservée pour mémoire :*

> « Votre spread suit une pente arbitraire. »

### Ce que nous concédons

La dérive doit être fonction du ratio de dette et du déficit, la pente devenant un effet de second ordre explicitement nommé comme hypothèse. En l'état, le spread est une horloge : il avance avec le calendrier, pas avec la situation du pays.

### Ce que nous maintenons, et pourquoi

Une prime de calendrier très faible peut se défendre (primes d'échéance électorale documentées dans la littérature), mais elle doit rester un résidu étiqueté, pas le moteur principal. Le fait que le dépôt indexe déjà le spread au solde primaire va dans le bon sens.

### Ce qui nous ferait changer d'avis

Si, spread recalculé sur la dette seule, le scénario de référence produisait des écarts d'OAT de plus de 50 points de base par rapport aux niveaux observés en 2025, la fonction serait recalibrée sur les niveaux observés.

### Statut et suites

**`en_cours`** — reconnue comme valable, traitement non terminé et suivi par une issue.

*Ce que cela change dans le dépôt :* spread à adosser au ratio de dette et au déficit.

*Suivi :* issue #4.

### Sources

- **Interne** : `simulateur/moteur.py` — spread de référence 88 + 8 × année
- **Externe** : Audit d'issue #4 (28/09/2026) — *2026* (portée par issue #4)

<!-- fin du bloc généré -->

---

### 17. Effet de falaise au seuil de 50 Md€ d'effort

« Votre modèle se joue à un dixième de milliard. »

<!-- OBJECTIONS FORTES : bloc généré par outils/generer-objections.py, ne pas éditer à la main -->

### La meilleure version de l'objection

> « Franchir 50,1 Md€ d'effort structurel fait gagner une note et 40 points de base de spread, tandis que 49,9 Md€ n'ont aucun effet : votre résultats dépendent d'un seuil binaire, donc toute politique peut être “optimisée” en le frôlant du bon côté. Un modèle dont la réponse est une marche d'escalier n'est pas robuste. »

*Attaque d'origine conservée pour mémoire :*

> « Votre modèle se joue à un dixième de milliard. »

### Ce que nous concédons

La marche doit devenir une transition continue — sigmoïde ou interpolation — et le seuil rester affiché comme convention de lecture, non comme bascule. Un modèle dont un dixième de milliard change la note souveraine n'est pas exploitable en débat, et se fait démonter en une phrase.

### Ce que nous maintenons, et pourquoi

La marche existe parce qu'un seuil a une signification institutionnelle réelle : c'est le point où le plan cesse d'être un ajustement et devient un changement de trajectoire. La remplacer par une transition douce conserve l'idée sans le saut.

### Ce qui nous ferait changer d'avis

Si la version continue déplaçait le classement des préréglages (par exemple si l'austérité devenait moins mauvaise que le plan à effort égal), la fonction serait revue — le classement est le résultat que nous affirmons.

### Statut et suites

**`en_cours`** — reconnue comme valable, traitement non terminé et suivi par une issue.

*Ce que cela change dans le dépôt :* seuil à lisser ; le catalogue affiche déjà l'effort requis.

*Suivi :* issue #4.

### Sources

- **Interne** : `simulateur/moteur.py` — seuil effort ≥ 50 Md€
- **Interne** : `simulateur/seuils.py` — garde-fous et barème public
- **Externe** : Audit d'issue #4 (28/09/2026) — *2026* (portée par issue #4)

<!-- fin du bloc généré -->

---

### 18. L'inflation est calculée mais n'alimente ni le PIB nominal ni les recettes

« Vous affichez une inflation décorative. »

<!-- OBJECTIONS FORTES : bloc généré par outils/generer-objections.py, ne pas éditer à la main -->

### La meilleure version de l'objection

> « Votre moteur calcule un taux d'inflation, l'affiche, et ne le transmet ni au PIB nominal ni aux recettes : 2,1 % d'inflation plus une croissance réelle ne donnent pas 1,9 % de croissance nominale. L'inflation est donc un ornement, alors que c'est elle qui décide si la dette se dévalue en euros courants. »

*Attaque d'origine conservée pour mémoire :*

> « Vous affichez une inflation décorative. »

### Ce que nous concédons

Le nominal doit être égal au réel plus l'inflation, appliqué aux recettes et aux dépenses ; c'est une correction d'identité comptable, pas un choix doctrinal, et elle est vérifiable sur la comptabilité nationale avant d'être portée dans le modèle.

### Ce que nous maintenons, et pourquoi

Les trajectoires de ratio restent dans des ordres de grandeur plausibles, et la direction du biais est connue : la transmission de l'inflation aux recettes nominales améliore le dénominateur du ratio de dette. Rendre ce canal visible rend le modèle attaquable sur des faits, ce qui est préférable à un ornement.

### Ce qui nous ferait changer d'avis

Si l'identité nominal = réel + inflation produisait des trajectoires de dette incompatibles avec les niveaux observés (par exemple une dette nominale qui baisse sans excédent primaire), les hypothèses d'inflation seraient révisées.

### Statut et suites

**`en_cours`** — reconnue comme valable, traitement non terminé et suivi par une issue.

*Ce que cela change dans le dépôt :* identité comptable à appliquer (nominal = réel + inflation).

*Suivi :* issue #4.

### Sources

- **Interne** : `simulateur/moteur.py` — inflation globale
- **Externe** : Audit d'issue #4 (28/09/2026) — *2026* (portée par issue #4)

<!-- fin du bloc généré -->

---

### 19. La branche austérité ne réduit pas le déficit

« Vous vous donnez un adversaire facile. »

<!-- OBJECTIONS FORTES : bloc généré par outils/generer-objections.py, ne pas éditer à la main -->

### La meilleure version de l'objection

> « Votre scénario d'austérité maintient le déficit constant à 150,9 Md€ : une austérité qui ne réduit pas le déficit n'existe pas, et vous l'utilisez comme repoussoir. Aucun adversaire sérieux ne défend une politique de coupes qui ne coupe rien : vous gagnez contre une caricature que vous avez écrite. »

*Attaque d'origine conservée pour mémoire :*

> « Vous vous donnez un adversaire facile. »

### Ce que nous concédons

Le scénario doit modéliser les coupes, puis leurs effets récessifs — c'est-à-dire un déficit qui baisse d'abord, une activité qui ralentit ensuite, et une dette qui ne s'améliore pas autant qu'annoncé. C'est plus honnête et plus difficile.

### Ce que nous maintenons, et pourquoi

Même corrigée, l'austérité reste perdante sur les indicateurs sociaux — tension, confiance, services de proximité — et c'est ce que le dépôt compare. Le débat n'est pas « couper ou ne pas couper », mais « couper quoi, et avec quel effet sur les gens ».

### Ce qui nous ferait changer d'avis

Si une austérité modélisée correctement (coupes réelles, multiplicateur négatif) donnait un déficit final meilleur que le plan tout en dégradant la tension, le dépôt devrait le dire : le plan ne serait pas la seule politique efficace, il serait la meilleure sur les indicateurs humains.

### Statut et suites

**`en_cours`** — reconnue comme valable, traitement non terminé et suivi par une issue.

*Ce que cela change dans le dépôt :* scénario d'austérité à réécrire avec coupes et effets récessifs.

*Suivi :* issue #4.

### Sources

- **Interne** : `simulateur/scenarios.py` — get_scenario_austerite_brutale()
- **Externe** : Audit d'issue #4 (28/09/2026) : « une austérité qui ne réduit pas le déficit est un homme de paille » — *2026* (portée par issue #4)

<!-- fin du bloc généré -->

---

### 20. Un test unitaire transforme la thèse du projet en invariante

« Vos tests sont verts parce qu'ils testent vos conclusions. »

<!-- OBJECTIONS FORTES : bloc généré par outils/generer-objections.py, ne pas éditer à la main -->

### La meilleure version de l'objection

> « Le test d'atterrissage de la mandature affirme un déficit inférieur à 3 %, un spread sous 55 points de base, un OAT sous 3,50 % et une note AA : ce ne sont pas des invariantes, c'est la thèse du projet recopiée en assertions. Corriger une hypothèse qui déplace le déficit de 2,84 % à 3,05 % ferait échouer la suite — ce qui pousse mécaniquement à ne pas corriger les hypothèses. Un dépôt qui dit vouloir être audité a construit un verrou contre son propre audit. »

*Attaque d'origine conservée pour mémoire :*

> « Vos tests sont verts parce qu'ils testent vos conclusions. »

### Ce que nous concédons

Les tests doivent être séparés : invariantes (identités comptables, bornes, déterminisme, neutralité du vecteur par défaut) d'un côté, objectifs politiques du plan nommés comme tels de l'autre, avec le jeu d'hypothèses utilisé. Tant que les deux sont mêlés, la correction des hypothèses est structurellement freinée.

### Ce que nous maintenons, et pourquoi

Les objectifs politiques restent légitimes : un plan de mandature a des cibles, et les tester évite les régressions silencieuses. Ce qui change est leur statut — objectif déclaré, avec la mention de l'hypothèse — et non leur présence.

### Ce qui nous ferait changer d'avis

Si séparer les deux familles de tests ne changeait rien à la capacité de détecter une régression, la séparation serait cosmétique ; elle est donc accompagnée d'un test de neutralité (le vecteur par défaut ne déplace rien) qui, lui, est une vraie invariante.

### Statut et suites

**`en_cours`** — reconnue comme valable, traitement non terminé et suivi par une issue.

*Ce que cela change dans le dépôt :* séparation invariantes / objectifs à mener dans tests/.

*Suivi :* issue #9, § 4.

### Sources

- **Interne** : `tests/test_simulateur.py` — scénario d'atterrissage de la mandature
- **Externe** : Audit d'issue #9 (28/09/2026) : la thèse transformée en assertion — *2026* (portée par issue #9)

<!-- fin du bloc généré -->

---

### 21. Chambre citoyenne tirée au sort : le levier existe, la doctrine manque

« Des citoyens tirés au sort seront manipulés par les lobbies. »

<!-- OBJECTIONS FORTES : bloc généré par outils/generer-objections.py, ne pas éditer à la main -->

### La meilleure version de l'objection

> « Le volet démocratique annonce un levier de chambre citoyenne, et le simulateur expose un curseur de membres tirés au sort — mais la section du dossier qui définit son pouvoir n'existe pas. Quatre modèles sont possibles (consultatif, mise à l'agenda, troisième chambre à veto suspensif, jury d'évaluation ex post) et ils n'ont pas les mêmes conséquences institutionnelles. Le retour d'expérience de la Convention citoyenne pour le climat l'a montré : le statut juridique des conclusions doit être fixé *avant* le tirage au sort, sinon la déception nourrit la défiance qu'on prétendait réduire. »

*Attaque d'origine conservée pour mémoire :*

> « Des citoyens tirés au sort seront manipulés par les lobbies. »

### Ce que nous concédons

Le dossier doit choisir explicitement un modèle et écrire le statut de ses conclusions, ou dire qu'il ne tranche pas encore. Un curseur sans doctrine est un trou, pas une avance.

### Ce que nous maintenons, et pourquoi

La chambre tirée au sort répond à un manque documenté : l'entre-soi des notables, et l'appareil du levier est déjà sensible au nombre de membres et au verrou constitutionnel de l'article 24. Le modèle « mise à l'agenda », avec précédent ostbelgien, a l'avantage d'obliger sans remplacer le suffrage universel.

### Ce qui nous ferait changer d'avis

Si le Conseil constitutionnel jugeait qu'une troisième chambre à veto suspensif méconnaît le suffrage universel, le modèle serait abandonné au profit de la mise à l'agenda, et l'article 24 resterait dans le registre des verrous.

### Statut et suites

**`en_cours`** — reconnue comme valable, traitement non terminé et suivi par une issue.

*Ce que cela change dans le dépôt :* section doctrinale à écrire ; quatre modèles à comparer dans docs/20.

*Suivi :* issue #7, § 4.

### Sources

- **Interne** : `simulateur/parametres.py` — levier reglage_chambre_tiree_au_sort
- **Interne** : `docs/01_DEMOCRATIE_INSTITUTIONS.md` — levier 8 — chambre citoyenne
- **Externe** : Conventions citoyennes françaises (climat 2019-2020, fin de vie 2022-2023) ; conseil citoyen d'Ostbelgien (2019) — *2019 à 2023* (portée par issue #7)

<!-- fin du bloc généré -->

---

### 22. Le laboratoire montre que le seuil de 3 % ne discrimine pas

« Vos simulations ne prouvent rien. »

<!-- OBJECTIONS FORTES : bloc généré par outils/generer-objections.py, ne pas éditer à la main -->

### La meilleure version de l'objection

> « Votre propre laboratoire, 500 tirages et 2 500 simulations, conclut que les 500 trajectoires réformées passent sous 3 % de déficit — mais les 500 trajectoires témoins aussi. Le seuil sur lequel repose toute la communication du plan ne distingue donc pas les politiques testées dans le domaine exploré. Publier cela et continuer à dire “sous 3 % en cinq ans” est une contradiction. »

*Attaque d'origine conservée pour mémoire :*

> « Vos simulations ne prouvent rien. »

### Ce que nous concédons

Le seuil ne doit pas être présenté comme un résultat discriminant : ce qu'il faut afficher, c'est l'écart au témoin (de l'ordre de 0,73 point de PIB en moyenne dans le laboratoire), et la probabilité d'atterrissage calculée sur une fourchette d'hypothèses, pas sur un point estimé.

### Ce que nous maintenons, et pourquoi

L'écart au témoin, lui, est un résultat : il ne dépend pas du seuil, et il est mesuré sur 500 tirages avec des chocs aléatoires. C'est la seule affirmation que le laboratoire autorise, et elle suffit à justifier l'existence du plan.

### Ce qui nous ferait changer d'avis

Si l'écart moyen au témoin devenait nul ou changeait de signe sous des hypothèses plausibles (transmission amortie des taux, recettes indexées), le laboratoire le dirait et le plan serait révisé — c'est exactement ce qu'un protocole falsifiable sert à produire.

### Statut et suites

**`refutee`** — traitée et la réponse tient : la critique porte à côté, sous sa forme forte.

*Ce que cela change dans le dépôt :* discours à recadrer sur l'écart au témoin, le seuil restant un objectif.

*Suivi :* docs/LABORATOIRE_RD.md.

### Sources

- **Interne** : `docs/LABORATOIRE_RD.md` — campagne de 500 tirages, graine 20261003
- **Interne** : `simulateur/laboratoire.py` — protocole d'écart au témoin

<!-- fin du bloc généré -->

---

### 23. « Notifié » n'est pas « encaissé », et il n'existe pas de réserve de gage

« Vos 60 Md€ sont une addition d'espérances. »

<!-- OBJECTIONS FORTES : bloc généré par outils/generer-objections.py, ne pas éditer à la main -->

### La meilleure version de l'objection

> « Vos deux plus gros leviers de recettes sont des recettes de contrôle : un taux de transformation du notifié vers l'encaissé de 60 à 70 % et un délai de deux à quatre ans. Un équilibre annoncé à 60 = 60, sans réserve, suppose que les neuf leviers donnent tous leur rendement maximal la même année — c'est une probabilité faible présentée comme une certitude. »

*Attaque d'origine conservée pour mémoire :*

> « Vos 60 Md€ sont une addition d'espérances. »

### Ce que nous concédons

Chaque levier doit porter une fiche de gage : rendement retenu en fourchette, rendement constaté du dispositif existant, base légale à créer ou modifier, délai notifié → encaissé, objections connues. Et l'équilibre doit inclure une réserve de gage — de l'ordre de 10 Md€ identifiés mais non comptés — pour absorber la sous-exécution.

### Ce que nous maintenons, et pourquoi

L'équilibre à 60 Md€ n'est pas une promesse d'exécution : c'est un ordre de grandeur de marges récurrentes, et le dépôt le présente ainsi depuis l'origine. Écrire les fourchettes rend l'ensemble plus solide, pas plus faible : une réserve annoncée est un argument en débat.

### Ce qui nous ferait changer d'avis

Si, fiche par fiche, la somme des rendements bas tombait sous 45 Md€, le plan ne tiendrait pas son équilibre affiché et devrait soit étaler l'atterrissage, soit chercher de nouvelles mesures — le registre des engagements dirait lequel.

### Statut et suites

**`en_cours`** — reconnue comme valable, traitement non terminé et suivi par une issue.

*Ce que cela change dans le dépôt :* fiches de gage et réserve à écrire levier par levier.

*Suivi :* issue #6.

### Sources

- **Interne** : `docs/02_RECETTES_ET_TRANSACTIONS.md` — matrices de leviers
- **Externe** : Audit d'issue #6 (28/09/2026) : transformation 60-70 %, délai 2-4 ans, réserve de gage d'environ 10 Md€ — *2026* (portée par issue #6)

<!-- fin du bloc généré -->

---

### 24. Les hypothèses du moteur ne sont pas un jeu nommé

« Changez une hypothèse et tout s'effondre. »

<!-- OBJECTIONS FORTES : bloc généré par outils/generer-objections.py, ne pas éditer à la main -->

### La meilleure version de l'objection

> « Un modèle dont les paramètres structurels sont écrits en dur ne peut pas être audité : le lecteur ne sait pas ce qui relève du fait, de la convention ou du choix politique. Tant que les hypothèses ne sont pas un objet nommé, avec une valeur basse, centrale et haute et une source pour chacune, vos résultats restent un point estimé présenté comme une trajectoire. »

*Attaque d'origine conservée pour mémoire :*

> « Changez une hypothèse et tout s'effondre. »

### Ce que nous concédons

Il faut un jeu d'hypothèses nommé, lu par le moteur, avec bas / central / haut et source, et un tirage de type Monte-Carlo qui rende une fourchette et une probabilité d'atterrissage au lieu d'une valeur unique.

### Ce que nous maintenons, et pourquoi

Le moteur reste déterministe et reproductible à hypothèses fixées : c'est ce qui permet de comparer des politiques entre elles. Nommer les hypothèses ne rend pas le modèle flou, cela rend la comparaison interprétable.

### Ce qui nous ferait changer d'avis

Si la fourchette obtenue était si large que le classement des politiques changeait d'un tirage à l'autre, le dépôt devrait le dire : c'est un résultat, et il vaudrait mieux que n'importe quelle certitude fabriquée.

### Statut et suites

**`ouverte`** — reçue et reconnue, chantier non engagé — le dire plutôt que de l'afficher « en cours ».

*Suivi :* issue #4 — chantier hypotheses.py.

### Sources

- **Interne** : `docs/METHODOLOGIE.md` — hypothèses, équations, conventions d'arrondi
- **Externe** : Audit d'issue #4 (28/09/2026) : proposition d'un jeu d'hypothèses et d'un Monte-Carlo à 1 000 tirages — *2026* (portée par issue #4)

<!-- fin du bloc généré -->

---

## 3. Comment déposer une objection

Une objection se dépose par le modèle d'issue **« Objection sourcée »** (`.github/ISSUE_TEMPLATE/objection.md`) : mesure visée, objection en une phrase, source datée, chiffre alternatif proposé, et ce qui ferait changer d'avis celui qui la formule. Une objection sans source est examinée comme une question, pas comme une objection : c'est le minimum pour que le débat porte sur des faits.

Le registre n'est pas trié par confort : les objections **concédées** et **en cours** y restent visibles, avec leur numéro. Une objection qui disparaîtrait du tableau serait le premier signe que ce dépôt ne s'audite plus lui-même.
