# 15 — La Constitution fichee article par article, et l'arithmetique des contre-pouvoirs

Deux modules ajoutent au simulateur la couche de droit constitutionnel qui lui
manquait : `simulateur/constitution_analysee.py` (les 109 articles en vigueur) et
`simulateur/gouvernance_contrepouvoir.py` (31 manœuvres et 38 seuils chiffrés).

## 1. Ce qui a ete construit

| objet | contenu |
|---|---|
| `ARTICLES` | 109 fiches, une par article en vigueur du texte officiel (Titres I → XVI, « bis » et numérotations arabes comprises) |
| `ABROGES` | 10 entrées (78 à 86, 90) avec l'article qui les abroge et une note — conservées pour l'histoire, jamais pour la simulation |
| `couverture()` | contrôle d'exhaustivité : `complet` est `True` seulement si chaque numéro attendu a sa fiche et aucune fiche ne porte un numéro inattendu |
| `MECANISMES` / `VERROUS` | 31 manœuvres (censure, 49.3, RIP, vote conforme, 44 al. 3, 47 al. 3, Congrès, Haute Cour, 16, 12, 88-6…) et 38 verrous chiffrés |
| `REGISTRE_LEGAL` | porté à 189 identifiants : les 37 entrées constitutionnelles préexistantes sont **inchangées**, 112 `CONST_*` ont été greffées |

Chaque fiche porte : `regles` (les seuils et délais), `opportunites`, `contraintes`,
`contre`, `croisements` (les articles à lire avec), `strates` (qui encaisse),
`mecanismes` (les clés du moteur), `leviers` (les clés réelles du catalogue) et
`pistes` (les leviers non chiffrés à créer).

## 2. Ouverture et interpretation du 49.3 en 2026

La revue du 12 octobre 2026 dit trois choses, écrites dans les fiches concernées :

1. l'article 49 alinéa 3 a été **utilisé en janvier 2026**, puis le gouvernement a
   affiché d'y renoncer : la fiche 49 porte donc une règle d'usage, pas une prophétie ;
2. la fenêtre législative résiduelle est d'environ **cinq mois** avant la suspension
   de l'ordre du jour : les scénarios de censure, de RIP et de congrès doivent être
   calés dessus ;
3. la session 2026-2027 s'ouvre avec une **gauche unie mais sans majorité absolue** :
   les 120 sièges du bloc le plus dense ne suffisent pas à atteindre 289.

Aucun chiffre de cette page ne vient d'un souvenir : seuils, effectifs et groupes
viennent du texte officiel (Conseil constitutionnel, à jour de la révision du
8 mars 2024) et des compositions constatées au 12 octobre 2026, consignées dans
`ETAT_ASSEMBLEES`. Les usages non retrouvés (bilan de l'article 16, nombre de
référendums locaux décisionnels, usage réel de la pétition 72-1) sont marqués
**« à vérifier avant publication »** dans les fiches, jamais chiffrés.

## 3. API

```python
from simulateur import constitution_analysee as ca
from simulateur import gouvernance_contrepouvoir as gc

ca.article("49 al. 3")            # -> la fiche de l'article 49
ca.par_bloc("XV")                 # -> les fiches du Titre XV
ca.rechercher("trois cinquièmes") # -> [{'numero', 'champ', 'extrait'}, ...]
ca.chaine(["49"])                 -> article 49 + ses croisements, avec une distance
ca.verrous_pour("usage_49_3")     -> ce qui encadre ce levier, article par article
ca.synthese_pour_api()            -> le payload JSON complet

gc.seuil("censure_voix")                          -> 289
gc.tableau_des_seuils()                             -> tous les seuils, effectifs du jour inclus
gc.coalition_necessaire("motion_censure")           -> plus petite coalition, avertissement compris
gc.blocages_possibles("article_49_3")               -> ce qui bloque un 49.3
gc.chaine_de_reaction("motion_censure")              -> censure -> dissolution
gc.coherence_avec_les_fiches()                       -> aucun mécanisme décoratif
```

`gc.coherence_avec_les_fiches()` est la clé de voûte : la `cle` de chaque mécanisme
doit apparaître dans le champ `mecanismes` d'au moins un de ses articles. Un
mécanisme qui ne sert à rien échoue donc au test, au lieu de fleurir dans la
documentation.

## 4. Ou sont les nombres, et pourquoi ils ne sont pas des leviers

`parametres.LEVIERS` compte 101 leviers et 14 familles, et ce compte est tenu par les
tests : aucun levier n'a été ajouté. Les 77 noms de « pistes » (101 occurrences, réparties
sur 80 fiches) des fiches sont la liste noire
du modèle — des objets de réforme que la Constitution permet mais que le simulateur ne
chiffre pas encore. Les promouvoir suppose d'ajouter la dépense, le rendement ou le
paramètre manquant, puis de recalibrer les comptes 101/14.

La fabrique `_a()` filtre les `leviers=` sur le catalogue (avec normalisation
d'accents) et bascule automatiquement tout nom inconnu dans `pistes` : une fiche ne
peut donc plus promettre un levier qui n'existe pas.

## 5. Verification

```bash
python3 -m unittest discover -s tests -p "test_*.py"   # 828 tests, OK (skipped=11)
python3 -c "from simulateur import constitution_analysee as ca; print(ca.resume_console())"
python3 -c "from simulateur import gouvernance_contrepouvoir as gc; print(gc.resume_console())"
python3 outils/generer-page-verification.py             # regenere docs/VERIFICATION_DONNEES.md
```

`tests/test_constitution_analysee.py` et `tests/test_gouvernance_contrepouvoir.py`
recalculent à la main les seuils (58 signatures, 289 voix, 555 au Congrès, 385 et 617
pour la Haute Cour, 40/15/70 jours budgétaires, 15 jours + majorité absolue pour le
vote conforme) et refusent toute fiche ou tout mécanisme décoratif.

## 6. Limites assumees

- **Ni route HTTP ni page d'interface** : les deux modules sont importables et testés,
  l'exposition publique reste à faire (`dashboard.py`, `pont_api.py`, puis
  `outils/generer-fonctions-api.py` et `outils/generer-index-simulateur.py --verifier`,
  qui sont obligatoires dès qu'une route ou une section est ajoutée).
- **Aucune composition d'assemblée dans un module `partis_et_chambres`** : elle vit dans
  `ETAT_ASSEMBLEES` et `arithmetique_assemblee`, pour que la date d'observation soit
  impossible à oublier.
- Le module est un **modèle** : il dit ce que le droit permet et ce qui le bloque, pas
  ce qui arrivera. La mention figure dans `synthese_pour_api()['methode']`.
