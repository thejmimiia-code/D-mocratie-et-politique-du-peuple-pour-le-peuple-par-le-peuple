# Fixture mensuelle : données entièrement synthétiques

`observations_synthetiques.jsonl` sert uniquement aux tests du registre temporel.
Les noms FICTIF_A/B/C, dates, sources `synthetic://` et étiquettes sont inventés.
Aucun événement réel, bilan humain, pays ou probabilité de guerre n'est représenté.
Licence : MIT, comme le dépôt. Protocole : `docs/RD_VALIDATION_TEMPORELLE.md`.

Construction déterministe, indice `i` de 0 à 23 pour janvier 2020 à décembre 2021 :

- A : positif si `i % 7` vaut 2, 3 ou 4 ;
- B : positif si `i % 5 == 0` ;
- C : positif si `i >= 14`, avec couverture incomplète aux indices 8 et 15.

Les publications ont lieu le premier jour du mois suivant, avec deux jours de
retard pour B. Disponibilité et ingestion égales à la publication dans cette fixture.
Deux révisions : A/mars 2020 corrigé de 1 à 0 le 1er février 2021 ; B/avril 2021
retiré (`null`, couverture incomplète) le 1er août 2021. Les deux changements doivent
rester invisibles aux prévisions émises avant leur disponibilité.

Ce jeu ne doit jamais être intégré à une étude de performance empirique réelle.

## Fixture du schéma GED

`ged_schema_synthetique.csv` et `contrat_ged_synthetique.json` sont également
entièrement inventés sous licence MIT. Les identifiants numériques et noms ne
représentent pas des événements UCDP. La mention 26.1 désigne le schéma testé,
pas une provenance du contenu. Cas couverts : date exacte, intervalle ambigu,
violence de type 3, doublon, événement hors périmètre et mois sans enregistrement.
Le contrat situe volontairement la disponibilité du snapshot au 3 octobre 2026
pour des événements de 2024 : il ne doit pas produire de prévisions historiques.
