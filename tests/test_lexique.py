"""tests/test_lexique.py — le vocabulaire du simulateur, vérifié.

Le lexique a une promesse simple : tout mot technique employé par la page y est
défini **en français ordinaire**. Un lexique qui définit « spread » par « écart
de rendement souverain » n'aide personne. Ces tests ne peuvent pas mesurer la
clarté d'une phrase — personne n'a inventé ça — mais ils vérifient tout ce qui
la rend possible :

* chaque terme est complet, unique et rattaché à une catégorie connue ;
* les définitions sont assez longues pour dire quelque chose, et ne
  renvoient pas à un jargon absent du lexique ;
* les renvois pointent vers des clés qui existent ;
* la recherche trouve un terme par son libellé, son alias ou sa définition ;
* le service public expose les formes à souligner, du plus long au plus court
  (sinon « point de PIB » serait mangé par « PIB »).
"""

import re
import unittest

from simulateur.lexique import (
    CATEGORIES,
    ORDRE_CATEGORIES,
    TERMES,
    Terme,
    citer,
    definir,
    lexique_public,
    rechercher,
)


class TestStructureDuLexique(unittest.TestCase):
    """Chaque entrée est exploitable par l'interface."""

    def setUp(self):
        self.cles = [terme.cle for terme in TERMES]

    def test_les_cles_sont_uniques(self):
        self.assertEqual(len(self.cles), len(set(self.cles)))

    def test_les_libelles_sont_uniques(self):
        libelles = [terme.terme.lower() for terme in TERMES]
        self.assertEqual(len(libelles), len(set(libelles)))

    def test_assez_de_termes_pour_couvrir_la_page(self):
        self.assertGreaterEqual(len(TERMES), 60)

    def test_toutes_les_categories_sont_connues(self):
        for terme in TERMES:
            self.assertIn(terme.categorie, CATEGORIES, f"catégorie inconnue : {terme.cle}")

    def test_ordre_et_categories_coherents(self):
        self.assertEqual(set(ORDRE_CATEGORIES), set(CATEGORIES))
        for categorie in CATEGORIES.values():
            self.assertTrue(categorie["libelle"].strip())
            self.assertTrue(categorie["introduction"].strip())

    def test_chaque_terme_a_une_definition_substantielle(self):
        for terme in TERMES:
            self.assertGreaterEqual(
                len(terme.definition), 60,
                f"définition trop courte pour être utile : {terme.cle}",
            )
            self.assertTrue(terme.definition.strip().endswith((".", "!", "?")),
                            f"phrase non terminée : {terme.cle}")

    def test_aucune_definition_ne_contient_de_placeholder(self):
        for terme in TERMES:
            self.assertNotIn("{}", terme.definition)
            self.assertNotIn("{", terme.repere)

    def test_les_renvois_pointent_vers_des_cles_existantes(self):
        for terme in TERMES:
            for cible in terme.voir:
                self.assertIn(cible, self.cles,
                              f"{terme.cle} renvoie vers une clé inconnue : {cible}")
            self.assertNotIn(terme.cle, terme.voir, f"{terme.cle} se renvoie à lui-même")

    def test_les_alias_ne_sont_pas_vides(self):
        for terme in TERMES:
            for forme in terme.formes:
                self.assertGreaterEqual(len(forme.strip()), 2, f"alias trop court : {terme.cle}")

    def test_les_termes_couverts_par_la_recherche_sont_nombreux(self):
        # Grandeurs incontournables de la page : elles doivent être expliquées.
        incontournables = (
            "spread", "point_base", "oat", "deficit", "dette", "charge_dette",
            "pib", "point_pib", "pde", "maastricht", "pouvoir_achat", "inflation",
            "tva", "score", "reference", "garde_fou", "strate", "ricochet",
            "levier", "domaine", "horizon", "modele",
        )
        for cle in incontournables:
            self.assertIn(cle, self.cles, f"terme incontournable absent : {cle}")

    def test_definir_renvoie_une_copie_et_none_si_absent(self):
        entree = definir("spread")
        self.assertIsNotNone(entree)
        self.assertIn("definition", entree)
        entree["definition"] = "modifié"
        self.assertNotEqual(definir("spread")["definition"], "modifié")
        self.assertIsNone(definir("terme_qui_n_existe_pas"))


class TestRecherche(unittest.TestCase):
    """On doit trouver un mot par son nom, son alias ou son contenu."""

    def test_recherche_vide_renvoie_tout(self):
        self.assertEqual(len(rechercher("")), len(TERMES))
        self.assertEqual(len(rechercher(None)), len(TERMES))

    def test_recherche_par_libelle(self):
        trouves = rechercher("spread")
        self.assertTrue(any(terme.cle == "spread" for terme in trouves))

    def test_recherche_par_alias(self):
        # « bp » est l'alias de « point de base » : le lecteur tape souvent ça.
        self.assertTrue(any(terme.cle == "point_base" for terme in rechercher("bp")))
        self.assertTrue(any(terme.cle == "point_base" for terme in rechercher("centième")))

    def test_recherche_insensible_a_la_casse_et_aux_espaces(self):
        self.assertTrue(any(terme.cle == "dette" for terme in rechercher("DETTE")))
        self.assertTrue(any(terme.cle == "pouvoir_achat"
                            for terme in rechercher("  POUVOIR   D'ACHAT ")))

    def test_recherche_sans_resultat(self):
        self.assertEqual(rechercher("xyzzytrovnb"), [])

    def test_citer_releve_les_termes_d_un_texte(self):
        cles = {terme.cle for terme in citer("Le spread se creuse face au Bund allemand.")}
        self.assertIn("spread", cles)
        self.assertIn("bund", cles)
        self.assertEqual(citer(""), [])
        self.assertEqual(citer(None), [])


class TestServicePublic(unittest.TestCase):
    """La charge utile servie à la page."""

    def setUp(self):
        self.charge = lexique_public()

    def test_structure_attendue(self):
        for cle in ("nombre", "total", "recherche", "categories", "termes", "formes"):
            self.assertIn(cle, self.charge)

    def test_les_categories_sont_toutes_publiees_et_comptees(self):
        self.assertEqual({c["cle"] for c in self.charge["categories"]}, set(ORDRE_CATEGORIES))
        total_compte = sum(c["nombre"] for c in self.charge["categories"])
        self.assertEqual(total_compte, self.charge["nombre"])

    def test_les_formes_sont_triees_du_plus_long_au_plus_court(self):
        # « point de PIB » doit être reconnu avant « PIB » au balisage, sinon
        # le soulignement se fait sur le mauvais mot.
        longueurs = [len(item["forme"]) for item in self.charge["formes"]]
        self.assertEqual(longueurs, sorted(longueurs, reverse=True))

    def test_chaque_forme_pointe_vers_une_cle_connue(self):
        cles = {terme.cle for terme in TERMES}
        for item in self.charge["formes"]:
            self.assertIn(item["cle"], cles)

    def test_la_recherche_est_repercutée_dans_la_charge(self):
        filtree = lexique_public("spread")
        self.assertLessEqual(filtree["nombre"], self.charge["total"])
        self.assertEqual(filtree["recherche"], "spread")
        self.assertTrue(any(t["cle"] == "spread" for t in filtree["termes"]))

    def test_un_terme_est_une_dataclass_serialisable(self):
        entree = definir("dette")
        for cle in ("cle", "terme", "categorie", "definition", "repere", "formes", "voir"):
            self.assertIn(cle, entree)
        self.assertIsInstance(entree["formes"], (list, tuple))


class TestLisibiliteDesDefinitions(unittest.TestCase):
    """Garder le cap : du français, pas du jargon qui renvoie au jargon."""

    #: Mots qui, employés dans une définition, trahissent une définition
    #: circulaire — on les tolère seulement s'ils sont eux-mêmes définis.
    JARGON = re.compile(
        r"\b(spread|OAT|Bund|bp|PDE|Maastricht|IPCH|CSG|CRDS|PLF|PLFSS|DGF|"
        r"BITD|OTAN|SIPRI|ISF|IFI|TTF|EPCI|PME)\b",
        re.IGNORECASE,
    )

    def test_le_jargon_employe_dans_une_definition_est_lui_meme_defini(self):
        cles_couvertes = set()
        for terme in TERMES:
            cles_couvertes.update(terme.voir)
        for terme in TERMES:
            for mot in self.JARGON.findall(terme.definition):
                self.assertTrue(
                    any(mot.lower() in [f.lower() for f in autre.formes] or
                        mot.lower() == autre.terme.lower()
                        for autre in TERMES),
                    f"« {mot} » employé dans « {terme.cle} » sans être défini",
                )

    def test_les_definitions_ne_sont_pas_des_listes_de_mots_cles(self):
        for terme in TERMES:
            self.assertGreater(
                terme.definition.count(" "), 12,
                f"définition trop télégraphique : {terme.cle}",
            )

    def test_aucun_terme_n_est_laisse_sans_categorie_lisible(self):
        for terme in TERMES:
            self.assertTrue(CATEGORIES[terme.categorie]["libelle"])
            self.assertIsInstance(Terme(**{
                "cle": terme.cle, "terme": terme.terme, "categorie": terme.categorie,
                "definition": terme.definition,
            }), Terme)


if __name__ == "__main__":
    unittest.main()
