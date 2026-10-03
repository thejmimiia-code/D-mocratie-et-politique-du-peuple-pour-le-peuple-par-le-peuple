# Recherche des lacunes — deuxième phase R&D

**3 octobre 2026 · Modèle `geo-rd-v2` · Audit exploratoire, pas prévision.**

## Bilan

L'audit croise le code, des expériences de régression et trois ressources externes
sur les données de conflit, l'évaluation prédictive et les stocks énergétiques.
Quatre limitations ont reçu une première correction **optionnelle**, une validation
des entrées a été renforcée et un registre des manques persistants est publié ici.
Aucune donnée réelle n'a été importée ou utilisée pour calibrer les paramètres.

### Ce que la recherche documentaire change

- **Disponibilité et révision des observations.** L'API UCDP distingue des versions
  du jeu annuel GED et des publications Candidate mensuelles/trimestrielles. Il
  faudra conserver les millésimes réellement disponibles au moment de chaque
  prévision, pas simplement télécharger aujourd'hui un historique révisé.
  La seconde phrase est une recommandation méthodologique de cet audit.
  [1](https://ucdp.uu.se/apidocs/)
- **Évaluation et cible.** VIEWS décrit des prévisions de violence armée à horizons
  mensuels, des évaluations régulières et des tests hors échantillon. Cela constitue
  un précédent méthodologique, pas une validation de notre indice ni un modèle
  transférable automatiquement à une guerre mondiale ou à l'emploi nucléaire.
  [1](https://viewsforecasting.org/early-warning-system/)
- **Les unités des stocks comptent.** L'obligation AIE est exprimée en au moins
  90 jours **d'importations nettes de pétrole**, pas 90 jours de demande énergétique
  totale. Des stocks peuvent être commerciaux, publics ou détenus à l'étranger.
  Nos mois de demande sectorielle ne peuvent donc pas être calibrés en remplaçant
  aveuglément `stock_mois` par 3. Accessibilité, composition, conversion d'unités
  et débit de déstockage restent à documenter.
  [1](https://www.iea.org/about/oil-security-and-emergency-response)

Sources consultées le 3 octobre 2026. Les résultats synthétiques ci-dessous
proviennent du code exécuté, pas de ces publications.

## 1. Corrections apportées

### A. Stock initial ≠ capacité et reconstitution matérielle

Avant : le stock initial définissait aussi la capacité ; il était consommable mais
ne pouvait jamais être reconstitué. Une deuxième crise était donc pénalisée par
construction, indépendamment des décisions d'approvisionnement entre les deux.

Ajouts à `Secteur` :

- `capacite_stock_mois=None` : conserve par défaut l'ancienne capacité ; une valeur
  explicite doit être au moins égale au stock initial ;
- `reconstitution_mensuelle=0` : quantité supplémentaire disponible, en fraction
  de la demande mensuelle, uniquement quand le blocus global vaut zéro.

```text
capacité = demande × capacité_en_mois
reconstitution = min(capacité − stock_initial_du_mois,
                     demande × taux_reconstitution)
approvisionnement = demande − flux_bloqué + substitution + reconstitution
```

La reconstitution est donc une entrée matérielle déclarée, pas un crédit de stock
sans origine. Le journal inclut cette entrée et la capacité. La conservation des
flux est toujours testée. **Cette offre supplémentaire est une hypothèse** : ses
coûts, sa provenance géographique et sa capacité industrielle ne sont pas modélisés.
On ne peut pas conclure de ces essais que constituer davantage de stocks serait
gratuit ou toujours optimal. Pas de reconstitution sous blocus même partiel dans
cette première version : choix conservateur explicite, pas loi physique.

### B. Tester le retour d'activité plutôt que présumer une perte éternelle

Ajout à `Parametres` : `recuperation_annuelle=0`, fraction de l'écart d'activité
résorbée au cours d'une année complète sans pénurie. Une tolérance numérique
`1e-12` distingue le zéro des résidus d'arrondi.

Si le facteur d'activité antérieur est `F` et le taux de reprise `r` :

```text
année sans pénurie : F' = F + r × (1 − F)
année avec pénurie : F' = F × (1 − élasticité × pénurie_moyenne)
```

`F'` ne dépasse jamais 1. Le paramètre par défaut conserve la persistance de la v1.
Une reprise de l'activité ne remet **pas** la dette à zéro : les états du moteur
macro continuent de porter les déficits passés. Cette reprise n'est pas une
simulation de reconstruction industrielle ; son coût et son financement manquent.

### C. Ne plus dissimuler les trous du calendrier

`simuler(..., calendrier_complet=True)` exige un événement explicite pour chaque
mois de l'horizon et refuse un calendrier incomplet. Un mois explicitement calme
est représenté par `Evenement(mois=...)`.

Le mode historique permissif reste disponible par défaut pour les scénarios
synthétiques. Il expose désormais `mois_supposes_calmes`, uniquement pour la période
calculée avant un éventuel arrêt. **Ce mode ne doit pas servir à assimiler une
absence d'observation réelle à une absence de conflit.** Le mode strict assure la
couverture du calendrier, pas la véracité ou l'exhaustivité des observations.

### D. Séparer médiation et état du dialogue

`cas_experimental` accepte désormais `rupture_dialogue` indépendamment de
`mediation`. La valeur `None` conserve le comportement historique. Un plan factoriel
2 × 2 permet de garder identiques les combats, autorisations et pénuries, en ne
changeant qu'une variable politique à la fois.

Le seuil reste heuristique : isoler un effet dans le code n'établit pas son effet
causal dans le monde réel.

### E. Validation des entrées

Le pont macro refuse désormais une trajectoire aux mois non consécutifs, une
pénurie hors [0, 1] et des paramètres non finis. Les nouveaux paramètres sont
bornés ; le secteur doit avoir un nom non blanc ; les valeurs textuelles ou
booléennes ne sont pas acceptées à la place de coefficients numériques.
Il ne s'agit pas encore d'un schéma d'import/export intégralement validé.

## 2. Expériences réellement lancées

```bash
python -m simulateur.audit_geopolitique --sortie rd-resultats-audit-geopolitique.json
python -m simulateur.geopolitique --sortie rd-resultats-geopolitique-v2.json
python -m unittest discover -s tests -p 'test_*.py'
```

### Deux crises identiques : les réserves entre les crises changent le résultat

Secteur fictif : demande 100 unités/mois, importations 80 %, exposition 90 %, stock
initial 100 unités et capacité 200. Blocus de 80 % aux mois 1–6 puis 13–18 ; six
mois de répit entre les crises. Substitution de 25 % après trois mois consécutifs.
Calendrier complet, horizon de 36 mois. Les quantités ne décrivent aucun pays réel.

Résultats sans récupération économique :

| Offre supplémentaire hors blocus / demande mensuelle | Stock avant deuxième crise | Pénurie cumulée deuxième crise, mois de demande | Écart PIB année 3 vs témoin |
|---|---:|---:|---:|
| 0 % | 0 unités | 3,024 | −52,47 Md€ |
| 25 % | 150 unités | 1,524 | −36,92 Md€ |
| 50 % | 200 unités | 1,024 | −31,74 Md€ |

La première crise est identique entre ces cas. La différence de deuxième crise
vient de l'approvisionnement supplémentaire pendant le répit, **pas d'une création
gratuite de matière**. Ces calculs ne comptabilisent toutefois pas le coût de cet
approvisionnement dans les finances publiques.

Chaque cas est testé avec une récupération économique annuelle de 0 %, 50 % et
100 % : neuf trajectoires au total. Dans le cas sans reconstitution, l'écart de PIB
de troisième année passe respectivement à −52,47 / −26,23 / 0 Md€.
**Avec un PIB revenu au niveau témoin, la dette reste supérieure de 37,28 Md€**
dans cette expérience. Retour de l'activité ≠ effacement des pertes passées.

### Médiation et dialogue : quatre trajectoires contrôlées

| Médiation imposée | Rupture du dialogue imposée | Première alerte heuristique |
|---|---|---:|
| non | non | mois 5 |
| non | oui | mois 3 |
| oui | non | aucune |
| oui | oui | mois 6 |

Les pénuries et interventions d'alliance sont identiques entre ces quatre cas.
La comparaison des deux lignes « rupture oui » isole l'effet **conventionnel** de
la médiation : alerte au mois 6 plutôt qu'au mois 3. Ce n'est pas une mesure de
l'efficacité réelle de la diplomatie.

### Vérifications exécutées

- **13 nouvelles trajectoires expérimentales** : neuf cas de stocks/reprise et
  quatre cas de dialogue/médiation.
- **100 calendriers synthétiques supplémentaires** dans un test à graine fixe,
  chacun sur 24 mois, avec conservation des flux et respect des capacités.
- Relance de la campagne antérieure de **113 trajectoires** ; régression numérique
  du cas central préservée : pénurie cumulée 5,5664 et écart final −57,84 Md€.
- **66 tests réussis**, dont 12 nouveaux tests dans cette phase.
- **`ruff check .` : réussi**. Pas de nouvelle dépendance d'exécution ; Ruff a été
  installé dans un environnement virtuel uniquement pour le contrôle de style.

Ces vérifications établissent une cohérence logicielle, pas une fiabilité prédictive.

## 3. Ce qui manque encore : registre priorisé

P0 = indispensable avant toute revendication prédictive ; P1 = indispensable
pour rendre les mécanismes plus réalistes ; P2 = extensions après validation.

| Priorité | Lacune persistante | Risque de conclusion trompeuse | Critère de résolution proposé |
|---|---|---|---|
| P0 | Cible prédictive non définie | Un score de tension pris pour une probabilité de guerre | Définition observable, horizon, unité géographique et règle de labellisation publiés |
| P0 | Aucun jeu historique calibré | Coefficients arbitraires présentés comme estimés | Jeu versionné, provenance, couverture et licence documentées |
| P0 | Dates de disponibilité et révisions absentes | Utiliser des informations futures lors d'un test rétrospectif | Table « connue à la date t » et test automatisé contre les fuites temporelles |
| P0 | Pas de cas négatifs / fréquence de base | Succès apparent en n'étudiant que les crises ayant escaladé | Échantillon incluant crises contenues et périodes sans escalade |
| P0 | Absence de validation prospective/hors échantillon | Confondre explication a posteriori et prévision | Découpage chronologique gelé, référence simple, erreurs et calibration publiées |
| P0 | Coûts économiques incomplets | Stocks et reprise apparaissent sans financement | Comptes ressources/emplois, coût d'acquisition, financement et absence de double comptage |
| P1 | Une route agrégée, pas de réseau | Ignorer des itinéraires saturés ou des dépendances communes | Réseau de capacités et délais, tests de coupures simultanées |
| P1 | Poids sectoriels sans chaînes de production | Une moyenne masque un composant indispensable | Matrice entrées-sorties et comparaison de plusieurs règles de production |
| P1 | Stocks supposés immédiatement mobilisables | Surestimer les réserves disponibles pendant une crise | Débit maximal de sortie, accessibilité, pertes et unités homogènes |
| P1 | Autorisation militaire et blocus imposés | Présenter un scénario choisi comme une décision prédite | Modèle de décision distinct, validé, ou étiquetage systématique « imposé » |
| P1 | Alliances simplifiées | Ni soutien non combattant, ni engagements contradictoires | Typologie des engagements et règles de résolution explicites, cas de test |
| P1 | Pas de dynamique multi-théâtres/capacité militaire | Un acteur peut intervenir sans coût d'opportunité | Ressources limitées, arbitrages et délais vérifiables |
| P1 | Boucle macro → décision absente | Ignorer l'effet politique des pertes économiques | Hypothèses alternatives de rétroaction, tests de stabilité, validation séparée |
| P1 | Temporalité mensuelle/annuelle | Masquer un choc bref aigu ou un rattrapage intra-annuel | Sensibilité au pas de temps et comparaison de plusieurs agrégations |
| P1 | Indice nucléaire non calibré | Confondre affrontement entre États nucléaires et emploi nucléaire | Renommer/documenter les concepts, pas de probabilité d'emploi sans méthode défendable |
| P1 | Effets humains et distributifs absents | Un PIB moyen peut masquer une catastrophe localisée | Indicateurs sectoriels/civils séparés, données et limites éthiques documentées |
| P2 | Cyber, espace, eau, santé et climat non couplés | Ignorer des causes communes et propagations de pannes | Sous-modèles ciblés avec paramètres observables plutôt qu'un score global opaque |
| P2 | Incertitude structurelle limitée | Même modèle répété pris pour diversité des futurs | Comparaison de mécanismes concurrents, pas seulement variation des coefficients |

### Nucléaire : une limite qui doit rester explicite

Le champ historique `confrontation_nucleaire_directe` signifie **combat entre deux
acteurs déclarés nucléaires**, pas usage d'une arme nucléaire. L'emploi reste une
branche imposée qui arrête le calcul. Une estimation des dommages sanitaires,
environnementaux ou des conséquences mondiales exigerait des modèles spécialisés ;
il ne faut pas remplir ce manque avec un multiplicateur économique improvisé.

## 4. Prochaine étape recommandée : les données avant de nouveaux scores

Un contrat minimal pour de futures observations devrait contenir :

```text
identifiant stable ; source ; version ; licence
intervalle de l'événement ; précision temporelle ; date de publication
première disponibilité vérifiable ; date d'ingestion ; date/version de révision
acteurs ; type d'événement ; territoire ; statut confirmé/incertain
couverture d'observation ; attribution contestée ; sources réellement indépendantes
```

L'importateur ne doit pas transformer une donnée absente en zéro. Il faut aussi
séparer la date d'une observation de celle à laquelle elle est disponible au
prévisionniste. Les transformations, exclusions et corrections doivent être
rejouables. **Ce contrat est une spécification à implémenter, pas un importateur
livré dans cette phase.**

Avant tout score probabiliste : choisir une seule cible limitée, réserver une
période de test intacte, comparer à une fréquence de base estimée uniquement sur
le passé, puis publier fausses alertes et événements manqués. Le cas très rare de
l'emploi nucléaire ne doit pas être assimilé aux événements de conflit ordinaires.

**Conclusion :** le modèle sait mieux représenter certaines hypothèses de résilience.
Il ne sait toujours pas prévoir le déclenchement d'une guerre. La principale lacune
n'est plus l'absence d'un score supplémentaire : c'est l'absence de données calibrées
et d'une évaluation indépendante de ce que ce score prétend annoncer.

## Addendum — R&D v3

Une première partie du contrat de données et du banc d'évaluation est maintenant
[implémentée et testée](RD_VALIDATION_TEMPORELLE.md) : observations mensuelles
versionnées, instantanés à date, contrôles anti-fuite et références chronologiques.
La démonstration reste entièrement synthétique ; collecte réelle, agrégation des
événements, calibration et évaluation indépendante restent à réaliser.
