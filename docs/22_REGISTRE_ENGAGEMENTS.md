# 22. Registre des engagements : ce que le plan promet, et comment on le jugera

> Un projet qui annonce à l'avance la façon dont il sera jugé se rend falsifiable. Ce registre rejoue le scénario de mandature (`python3 main.py mandature`), reprend les gages du registre de la contradiction, et nomme pour chaque indicateur la source extérieure qui dira si la promesse a tenu — y compris contre le modèle.

> Document engendré par `outils/generer-registre-engagements.py` : les chiffres viennent du moteur, les gages du catalogue, jamais d'une saisie.

---

## 1. La trajectoire simulée, année par année

| Année | Déficit (% PIB) | Dette (% PIB) | OAT 10 ans | Écart Bund | Tension sociale | Confiance démocratique |
|---|---:|---:|---:|---:|---:|---:|
| An 1 | 4,86 | 122,99 | 4,16 | 85,6 pb | 14,5/100 | 72,5/100 |
| An 2 | 3,48 | 124,20 | 4,12 | 81,6 pb | 5,0/100 | 77,5/100 |
| An 3 | 1,91 | 123,81 | 4,05 | 75,0 pb | 5,0/100 | 77,5/100 |
| An 4 | 0,54 | 122,06 | 4,00 | 70,4 pb | 5,0/100 | 77,5/100 |
| An 5 | -0,73 | 119,07 | 3,35 | 47,2 pb | 5,0/100 | 77,5/100 |

Ces valeurs sont des sorties de modèle sur des hypothèses nommées (`docs/METHODOLOGIE.md`) : elles décrivent une trajectoire sous politique simulée, pas une prévision. Le dossier public reconnaît deux corrections d'hypothèses qui décalent l'atterrissage du déficit vers 3,05 à 3,26 % en année 5 (objections n° 11 et n° 12 du registre) : elles sont donc attendues, pas découvertes.

---

## 2. Ce qui sera regardé, par quelle source, et à quel seuil

| Indicateur | Source d'évaluation | Réussite | Échec |
|---|---|---|---|
| **Déficit public (% du PIB)** (aujourd'hui : 4,86 % du PIB) | INSEE, comptes nationaux (première estimation de l'année écoulée) | sous 3 % du PIB avant la fin de la mandature, et sous le statu quo simulé | au-dessus du statu quo simulé pendant deux exercices consécutifs |
| **Dette publique (% du PIB)** (aujourd'hui : 122,99 % du PIB) | INSEE, comptes nationaux — dette au sens de Maastricht | dette stabilisée puis en baisse sur les deux derniers exercices | dette toujours en hausse en fin de mandature |
| **Taux de l'OAT 10 ans** (aujourd'hui : 4,16 %) | Agence France Trésor, courbe des taux ; Banque de France | détente du taux par rapport au niveau de départ de la mandature | taux supérieur de plus d'un point au niveau de départ |
| **Écart OAT / Bund** (aujourd'hui : 85,60 points de base) | Banque de France, écart de taux à 10 ans contre l'Allemagne | écart revenu sous sa moyenne de long terme | écart supérieur à celui observé au début de la mandature |
| **Tension sociale locale (indice du modèle)** (aujourd'hui : 14,50 /100) | aucune source directe : indice du modèle, à confronter aux faits sociaux (conflits, mobilisations, baromètres de confiance) | direction à la baisse sur les trois derniers exercices | pic supérieur au niveau de départ |
| **Confiance démocratique (indice du modèle)** (aujourd'hui : 72,50 /100) | baromètre de la confiance politique (CEVIPOF) pour la tendance réelle | progression dans le baromètre réel, pas seulement dans le modèle | baisse du baromètre réel malgré la hausse simulée |

Deux indicateurs n'ont pas de source publique directe : la tension sociale et la confiance démocratique sont des indices du modèle. Le registre le dit au lieu de les présenter comme des mesures — c'est précisément l'objection n° 13, non résolue à ce jour.

---

## 3. Les gages, leur portée, et la réserve disponible

| Fiche | Mesure | Portée du levier | Gage du dossier | Réserve de portée |
|---|---|---:|---:|---:|
| 1 | Casier judiciaire B2 pour l'éligibilité | — | — | — |
| 2 | Vote blanc invalidant | — | — | — |
| 3 | Référendum d'initiative citoyenne sécurisé | — | — | — |
| 4 | Traque de la grande fraude fiscale par IA | 10 Md€/an | 10 Md€/an | 0 Md€/an |
| 5 | Conditionnement des aides aux entreprises | 20 Md€/an | 15 Md€/an | 5 Md€/an |
| 6 | Taxe sur les superprofits et les rachats d'actions | 15 Md€/an | 6 Md€/an | 9 Md€/an |
| 7 | Extension de la taxe sur les transactions financières | 8 Md€/an | 5 Md€/an | 3 Md€/an |
| 8 | Fusion des doublons territoriaux | 10 Md€/an | 8 Md€/an | 2 Md€/an |
| 9 | Mutualisation de la commande publique | 8 Md€/an | 6 Md€/an | 2 Md€/an |
| 10 | Baisse de la TVA sur l'énergie à 5,5 % | 9 Md€/an | -9 Md€/an | 0 Md€/an |

**Réserve de portée disponible : 21 Md€/an.**

Cette réserve n'est pas un rendement attendu : c'est l'écart entre ce que le dossier ose compter (les gages) et ce que le catalogue permet d'explorer (les portées). Elle répond à une objection déjà reçue — un équilibre à 60 = 60 sans marge de sécurité (objection n° 23) — et elle se vérifie en une commande : `GET /api/objections?famille=mesure`.

---

## 4. Ce que ce registre ne fait pas

- Il ne transforme pas une sortie de modèle en promesse électorale : les cibles du plan restent des objectifs politiques, et les chiffres ci-dessus sont conditionnels aux hypothèses nommées.
- Il ne prétend pas que les sources d'évaluation seront disponibles au calendrier prévu : les comptes nationaux sont révisés, et certains indicateurs n'ont pas de millésime annuel.
- Il ne clôt aucune objection : chaque ligne renvoie au numéro du registre (`docs/21_OBJECTIONS_OUVERTES.md`), où la concession et le fait de réfutation sont écrits.
