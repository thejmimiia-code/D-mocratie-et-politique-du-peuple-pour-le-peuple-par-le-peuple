"""
tests/test_parametres.py — Tests de la table des leviers et des préréglages.

Le simulateur promet : « l'ensemble des paramètres croisables dynamiquement ».
Ces tests verrouillent ce contrat : chaque levier est décrit, borné, documenté,
et chaque préréglage ne référence que des leviers existants.
"""

import json
import unittest

from simulateur.parametres import (
    FAMILLES,
    LEVIERS,
    PRESETS,
    TYPE_CHOIX,
    TYPE_CIBLE,
    TYPE_CURSEUR,
    TYPE_INTERRUPTEUR,
    catalogue_public,
    leviers_par_famille,
    normaliser,
    resume_effets_lever,
    valeurs_par_defaut,
)

TYPES_CONNUS = {TYPE_CURSEUR, TYPE_INTERRUPTEUR, TYPE_CIBLE, TYPE_CHOIX}


class TestTableDesLeviers(unittest.TestCase):
    """Chaque levier doit être utilisable par l'interface et par le moteur."""

    def test_volume_minimal(self):
        # « et plus si tu peux » : le tableau de bord doit exposer largement
        # plus que la poignée de paramètres du tableau de bord initial.
        self.assertGreaterEqual(len(LEVIERS), 90)
        self.assertGreaterEqual(len(FAMILLES), 10)

    def test_chaque_levier_est_complet(self):
        for cle, levier in LEVIERS.items():
            with self.subTest(levier=cle):
                self.assertEqual(cle, levier.cle)
                self.assertTrue(levier.libelle.strip())
                self.assertTrue(levier.description.strip(), "description manquante")
                self.assertIn(levier.type, TYPES_CONNUS)
                self.assertIn(levier.famille, FAMILLES)
                self.assertTrue(levier.unite.strip())
                self.assertIsInstance(levier.precision, int)
                self.assertGreaterEqual(levier.precision, 0)
                # Un levier doit être rattaché au moteur et/ou documenté.
                self.assertTrue(
                    levier.champ or levier.ligne or levier.effets_directs or levier.type == TYPE_CHOIX,
                    "aucun rattachement au moteur",
                )

    def test_bornes_coherentes(self):
        for cle, levier in LEVIERS.items():
            with self.subTest(levier=cle):
                mini, maxi = levier.bornes
                self.assertLessEqual(mini, maxi, "bornes inversées")
                self.assertGreaterEqual(levier.defaut, mini)
                self.assertLessEqual(levier.defaut, maxi)
                if levier.type != TYPE_INTERRUPTEUR:
                    self.assertGreater(levier.pas, 0.0)
                if levier.type == TYPE_INTERRUPTEUR:
                    self.assertEqual((mini, maxi), (0.0, 1.0))
                    self.assertIn(levier.defaut, (0.0, 1.0))
                if levier.type == TYPE_CHOIX:
                    valeurs = [valeur for _, valeur in levier.modalites]
                    self.assertIn(levier.defaut, valeurs)

    def test_profil_temporel_sur_cinq_ans(self):
        """Chaque levier monte en puissance sur les 5 années de mandature."""
        for cle, levier in LEVIERS.items():
            with self.subTest(levier=cle):
                self.assertEqual(len(levier.profil), 5)
                for coefficient in levier.profil:
                    self.assertGreaterEqual(coefficient, 0.0)
                    self.assertLessEqual(coefficient, 1.0)

    def test_familles_regroupent_tous_les_leviers(self):
        regroupement = leviers_par_famille()
        total = sum(len(leviers) for leviers in regroupement.values())
        self.assertEqual(total, len(LEVIERS))
        for levier in LEVIERS.values():
            self.assertIn(levier.cle, [item.cle for item in regroupement[levier.famille]])

    def test_valeurs_par_defaut_neutres(self):
        defauts = valeurs_par_defaut()
        self.assertEqual(set(defauts), set(LEVIERS))
        # L'état neutre vaut zéro pour les curseurs : la référence doit être le statu quo.
        neutres = [
            cle for cle, levier in LEVIERS.items()
            if levier.type == TYPE_CURSEUR and levier.defaut != 0.0
        ]
        # Les seuls curseurs non nuls sont les niveaux « cible » (ex. effort de défense).
        for cle in neutres:
            with self.subTest(levier=cle):
                self.assertEqual(LEVIERS[cle].type, TYPE_CIBLE)
                self.assertTrue(LEVIERS[cle].champ, "une cible doit piloter un champ du moteur")

    def test_cible_pilote_un_niveau_et_non_un_delta(self):
        """Régression : un levier « cible » fixe un niveau, il ne s'ajoute pas au réel."""
        for cle, levier in LEVIERS.items():
            if levier.type != TYPE_CIBLE:
                continue
            with self.subTest(levier=cle):
                self.assertIsNotNone(levier.champ)
                self.assertGreater(levier.maximum, levier.minimum)

    def test_resume_effets_de_chaque_levier(self):
        for cle in LEVIERS:
            with self.subTest(levier=cle):
                self.assertTrue(resume_effets_lever(cle).strip())


class TestNormalisation(unittest.TestCase):
    """L'API accepte des entrées approximatives ; le moteur, jamais."""

    def test_vecteur_complet_et_borne(self):
        resultat = normaliser({})
        self.assertEqual(set(resultat), set(LEVIERS))
        self.assertEqual(resultat, valeurs_par_defaut())
        for cle, valeur in resultat.items():
            mini, maxi = LEVIERS[cle].bornes
            self.assertGreaterEqual(valeur, mini)
            self.assertLessEqual(valeur, maxi)

    def test_ecretage_aux_bornes(self):
        borne = LEVIERS["tva_taux_normal"]
        self.assertEqual(normaliser({"tva_taux_normal": 80.0})["tva_taux_normal"], borne.maximum)
        self.assertEqual(normaliser({"tva_taux_normal": -80.0})["tva_taux_normal"], borne.minimum)

    def test_cle_inconnue_leve_une_erreur_explicite(self):
        with self.assertRaises(ValueError) as capture:
            normaliser({"levier_imaginaire": 3.0})
        self.assertIn("levier_imaginaire", str(capture.exception))

    def test_interrupteurs_acceptent_booleens_et_textes(self):
        for brut, attendu in [(True, 1.0), (False, 0.0), ("oui", 1.0), ("non", 0.0), (0.9, 1.0)]:
            with self.subTest(brut=brut):
                self.assertEqual(normaliser({"reforme_ric": brut})["reforme_ric"], attendu)

    def test_valeur_illisible_leve_une_erreur_explicite(self):
        with self.assertRaises(ValueError) as capture:
            normaliser({"reforme_ric": "peut-être"})
        self.assertIn("reforme_ric", str(capture.exception))

    def test_none_retombe_sur_le_defaut(self):
        self.assertEqual(
            normaliser({"tva_taux_normal": None})["tva_taux_normal"],
            LEVIERS["tva_taux_normal"].defaut,
        )

    def test_normalisation_idempotente(self):
        entree = {"tva_taux_normal": 2.0, "reforme_ric": 1.0, "effort_defense_pct_pib": 3.2}
        une_fois = normaliser(entree)
        deux_fois = normaliser(une_fois)
        self.assertEqual(une_fois, deux_fois)


class TestPresets(unittest.TestCase):
    """Les préréglages sont des points d'entrée sûrs et documentés."""

    def test_presets_presents(self):
        attendus = {
            "statut_quo", "mandature", "resilience", "austerite", "transition_ecologique",
            "justice_sociale", "choc_mondial", "crise_geopolitique", "crise_taiwan",
            "hormuz", "escalade_nucleaire", "convergence_ww3", "refondation_democratique",
        }
        self.assertEqual(set(PRESETS), attendus)

    def test_chaque_preset_est_decrit(self):
        for cle, preset in PRESETS.items():
            with self.subTest(preset=cle):
                self.assertTrue(preset["libelle"].strip())
                self.assertTrue(preset["description"].strip())
                self.assertRegex(preset["couleur"], r"^#[0-9a-fA-F]{6}$")

    def test_presets_ne_referencent_que_des_leviers_valides(self):
        for cle, preset in PRESETS.items():
            with self.subTest(preset=cle):
                inconnus = set(preset["parametres"]) - set(LEVIERS)
                self.assertFalse(inconnus, f"leviers inconnus : {sorted(inconnus)}")
                normaliser(preset["parametres"])  # ne doit pas lever

    def test_statu_quo_est_le_vecteur_neutre(self):
        self.assertEqual(normaliser(PRESETS["statut_quo"]["parametres"]), valeurs_par_defaut())

    def test_les_presets_activent_reellement_des_leviers(self):
        for cle, preset in PRESETS.items():
            if cle == "statut_quo":
                continue
            with self.subTest(preset=cle):
                self.assertGreaterEqual(len(preset["parametres"]), 3)


class TestCataloguePublic(unittest.TestCase):
    """Le catalogue servi au navigateur doit être complet et sérialisable."""

    def test_structure(self):
        catalogue = catalogue_public()
        self.assertEqual(set(catalogue), {"familles", "presets", "defauts"})
        self.assertEqual(len(catalogue["presets"]), len(PRESETS))
        self.assertEqual(set(catalogue["defauts"]), set(LEVIERS))

    def test_tous_les_leviers_sont_dans_les_familles(self):
        catalogue = catalogue_public()
        cles = [levier["cle"] for famille in catalogue["familles"] for levier in famille["leviers"]]
        self.assertEqual(sorted(cles), sorted(LEVIERS))

    def test_json_serialisable(self):
        charge = json.dumps(catalogue_public(), ensure_ascii=False)
        self.assertIn("familles", charge)
        self.assertGreater(len(charge), 10_000)


if __name__ == "__main__":
    unittest.main()
