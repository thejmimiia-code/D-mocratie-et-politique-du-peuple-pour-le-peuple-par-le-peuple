"""
tests/test_classes_leviers.py — le classement des leviers se vérifie tout seul.

Le module `simulateur/classes_leviers.py` range les 156 leviers en cinq classes
(recettes, économies, dépenses, règles, monde) pour que la page du simulateur
puisse dire, sans qu'on lise un budget, ce qui entre, ce qui sort, ce qui
change une règle et ce qui vient de l'extérieur.

Ces tests protègent quatre propriétés, et aucune n'est décorative :

1. **aucun levier n'est orphelin** — chacun a exactement une classe connue,
   et les comptes par classe additionnent le catalogue entier ;
2. **le classement ne contredit pas le catalogue** — un levier sans ligne
   budgétaire et sans champ moteur est en « règles », un drapeau 0/1 aussi, et
   l'unique exception (un choc subi) est écrite, motivée et vérifiée ;
3. **chaque affectation documentée corrige vraiment la règle générale** — un
   cas limite sans explication écrite, ou qui ne corrige rien, fait échouer la
   suite ;
4. **la couleur ne porte jamais seule l'information** — palette limitée aux
   accents M.R.S.C., symbole + libellé + motif pour chaque classe, et totaux
   qui séparent les euros des unités non budgétaires.
"""

import unittest

from simulateur.classes_leviers import (
    AFFECTATIONS_DOCUMENTEES,
    CLASSES,
    CLASSES_MONETAIRES,
    DIVISEUR_MENAGES,
    MOTIF_HACHURE,
    MOTIF_POINTILLE,
    MOTIF_UNI,
    NOTE_HORS_BUDGET,
    ORDRE_CLASSES,
    SENS_AUCUN,
    SENS_ECONOMIE,
    SENS_ENTREE,
    SENS_SORTIE,
    SENS_SUBI,
    catalogue_classes,
    classe_automatique,
    classe_de,
    classes_du_catalogue,
    est_drapeau,
    est_reglage_institutionnel,
    euros_par_menage,
    leviers_par_classe,
    motif_classe,
    serie_classes,
    totaux_classe,
    verifier_classes,
)
from simulateur.domaines import construire_flux
from simulateur.parametres import LEVIERS, PRESETS

#: Palette autorisée : les accents que le site applique déjà au simulateur.
COULEURS_AUTORISEES = {"#9bc77a", "#ff9295", "#91b2e6", "#f2c15f"}

SENS_CONNUS = {SENS_ENTREE, SENS_ECONOMIE, SENS_SORTIE, SENS_AUCUN, SENS_SUBI}
MOTIFS_CONNUS = {MOTIF_UNI, MOTIF_HACHURE, MOTIF_POINTILLE}

FAMILLES_FISCALES = ("fiscalite_menages", "fiscalite_entreprises")


def _parametres_preset(cle: str) -> dict:
    """Le dictionnaire de leviers d'un préréglage (les presets sont enveloppés)."""
    return dict(PRESETS[cle]["parametres"])


def _flux_annuels(preset: str, horizon: int = 5) -> list[dict]:
    parametres = _parametres_preset(preset)
    flux_annuels = []
    for annee in range(horizon):
        flux = dict(construire_flux(parametres, annee))
        flux["annee"] = annee + 1
        flux_annuels.append(flux)
    return flux_annuels


class TestChaqueLevierAUneClasse(unittest.TestCase):
    """Le catalogue entier est couvert, sans doublon ni oubli."""

    def test_le_controle_interne_ne_trouve_aucune_anomalie(self):
        self.assertEqual(verifier_classes(), [])

    def test_chaque_levier_a_une_classe_connue(self):
        table = classes_du_catalogue()
        self.assertEqual(len(table), len(LEVIERS))
        for cle, classe in table.items():
            with self.subTest(levier=cle):
                self.assertIn(classe, ORDRE_CLASSES)

    def test_les_comptes_par_classe_additionnent_le_catalogue(self):
        groupes = leviers_par_classe()
        self.assertEqual(set(groupes), set(ORDRE_CLASSES))
        total = sum(len(cles) for cles in groupes.values())
        self.assertEqual(total, len(LEVIERS))
        vues = [cle for cles in groupes.values() for cle in cles]
        self.assertEqual(sorted(vues), sorted(LEVIERS))

    def test_un_levier_inconnu_leve_une_erreur_explicite(self):
        with self.assertRaises(KeyError):
            classe_de("levier_qui_n_existe_pas")
        with self.assertRaises(KeyError):
            classe_automatique("levier_qui_n_existe_pas")


class TestLeClassementSuitLeCatalogue(unittest.TestCase):
    """Les règles de classement recoupent les données du catalogue."""

    def test_les_reglages_institutionnels_sont_en_regles(self):
        reglages = [cle for cle in LEVIERS if est_reglage_institutionnel(cle)]
        self.assertTrue(reglages, "le catalogue doit porter des réglages institutionnels")
        for cle in reglages:
            with self.subTest(levier=cle):
                self.assertEqual(classe_de(cle), "regles")

    def test_les_drapeaux_sont_en_regles_sauf_ceux_du_monde(self):
        drapeaux = [cle for cle in LEVIERS if est_drapeau(cle)]
        self.assertTrue(drapeaux)
        for cle in drapeaux:
            with self.subTest(levier=cle):
                if LEVIERS[cle].famille == "exogene_monde":
                    # Exception écrite : un choc subi n'est pas une décision.
                    self.assertEqual(classe_de(cle), "monde")
                    self.assertIn("exogènes", motif_classe(cle))
                else:
                    self.assertEqual(classe_de(cle), "regles")

    def test_les_familles_fiscales_vont_en_recettes_hors_cas_limites(self):
        for cle, levier in LEVIERS.items():
            if levier.famille not in FAMILLES_FISCALES:
                continue
            if est_drapeau(cle) or est_reglage_institutionnel(cle):
                continue
            if cle in AFFECTATIONS_DOCUMENTEES:
                continue
            with self.subTest(levier=cle):
                self.assertEqual(classe_automatique(cle), "recettes")

    def test_le_facteur_negatif_coute_et_ne_rapporte_pas(self):
        # `flat_tax_suppression` porte un facteur −4 : la mesure coûte, elle
        # n'est donc pas une recette, même si sa famille est fiscale.
        negatifs = [cle for cle, levier in LEVIERS.items() if (levier.facteur or 0) < 0]
        self.assertEqual(negatifs, ["flat_tax_suppression"])
        self.assertIn(LEVIERS["flat_tax_suppression"].famille, FAMILLES_FISCALES)
        self.assertEqual(classe_automatique("flat_tax_suppression"), "recettes")
        self.assertEqual(classe_de("flat_tax_suppression"), "depenses")

    def test_les_chocs_exogenes_sont_dans_monde(self):
        exogenes = [cle for cle, levier in LEVIERS.items() if levier.famille == "exogene_monde"]
        self.assertTrue(exogenes)
        for cle in exogenes:
            with self.subTest(levier=cle):
                self.assertEqual(classe_automatique(cle), "monde")
                self.assertEqual(classe_de(cle), "monde")


class TestAffectationsDocumentees(unittest.TestCase):
    """Chaque exception au classement automatique est écrite et vérifiable."""

    def test_chaque_affectation_vise_un_levier_reel(self):
        for cle in AFFECTATIONS_DOCUMENTEES:
            with self.subTest(affectation=cle):
                self.assertIn(cle, LEVIERS)

    def test_chaque_affectation_est_motivee_et_pointe_une_classe_connue(self):
        for cle, (classe, motif) in AFFECTATIONS_DOCUMENTEES.items():
            with self.subTest(affectation=cle):
                self.assertIn(classe, ORDRE_CLASSES)
                self.assertGreaterEqual(len(motif.strip()), 40,
                                        "un motif court n'explique rien")

    def test_le_motif_affiche_est_celui_de_l_affectation(self):
        for cle, (_, motif) in AFFECTATIONS_DOCUMENTEES.items():
            with self.subTest(affectation=cle):
                self.assertEqual(motif_classe(cle), motif)

    def test_aucune_affectation_n_est_un_doublon_de_la_regle(self):
        # Une affectation n'a d'intérêt que si elle corrige la lecture
        # automatique du catalogue.
        for cle, (classe, _) in AFFECTATIONS_DOCUMENTEES.items():
            with self.subTest(affectation=cle):
                self.assertNotEqual(
                    classe, classe_automatique(cle),
                    "affectation inutile : la règle générale donnait déjà cette classe")
                self.assertEqual(classe_de(cle), classe)

    def test_les_quatre_lectures_limites_du_dossier_sont_couvertes(self):
        # Baisses de prélèvements, transfert classé en fiscalité, économies
        # d'efficacité, compteurs déguisés en montants : les quatre familles de
        # cas limites repérées dans le dossier ont leur affectation écrite.
        attendus = {
            "tva_energie_5_5": "depenses", "cheque_energie": "depenses",
            "flat_tax_suppression": "depenses", "taxe_comportements": "recettes",
            "fusion_doublons": "economies", "commande_publique": "economies",
            "simplification": "economies", "usage_49_3": "regles",
            "charge_reformes_simultanees": "regles",
        }
        for cle, classe in attendus.items():
            with self.subTest(levier=cle):
                self.assertIn(cle, AFFECTATIONS_DOCUMENTEES)
                self.assertEqual(classe_de(cle), classe)


class TestCouleurJamaisSeule(unittest.TestCase):
    """La lisibilité ne dépend pas de la teinte : symbole, libellé, motif."""

    def test_la_palette_reste_dans_la_charte_mrsc(self):
        for cle, fiche in CLASSES.items():
            with self.subTest(classe=cle):
                self.assertIn(fiche.couleur, COULEURS_AUTORISEES)

    def test_chaque_classe_porte_symbole_libelle_et_motif(self):
        for cle, fiche in CLASSES.items():
            with self.subTest(classe=cle):
                self.assertTrue(fiche.symbole.strip())
                self.assertTrue(fiche.libelle.strip())
                self.assertTrue(fiche.libelle_court.strip())
                self.assertTrue(fiche.verdict.strip())
                self.assertTrue(fiche.question.strip())
                self.assertTrue(fiche.definition.strip())
                self.assertIn(fiche.motif, MOTIFS_CONNUS)
                self.assertIn(fiche.sens, SENS_CONNUS)
                self.assertTrue(fiche.doctrine.startswith("docs/"))

    def test_les_symboles_et_motifs_ne_sont_pas_identiques(self):
        # Deux classes ne doivent pas se confondre en niveaux de gris : soit le
        # symbole diffère, soit le motif diffère.
        vues = [(fiche.symbole, fiche.motif) for fiche in CLASSES.values()]
        self.assertEqual(len(set(vues)), len(vues))

    def test_les_sens_descrivent_le_budget_sans_ambiguite(self):
        self.assertEqual(CLASSES["recettes"].sens, SENS_ENTREE)
        self.assertEqual(CLASSES["economies"].sens, SENS_ECONOMIE)
        self.assertEqual(CLASSES["depenses"].sens, SENS_SORTIE)
        self.assertEqual(CLASSES["regles"].sens, SENS_AUCUN)
        self.assertEqual(CLASSES["monde"].sens, SENS_SUBI)

    def test_recettes_et_economies_partagent_le_vert_mais_pas_le_motif(self):
        self.assertEqual(CLASSES["recettes"].couleur, CLASSES["economies"].couleur)
        self.assertNotEqual(CLASSES["recettes"].motif, CLASSES["economies"].motif)

    def test_la_vue_publique_est_complete(self):
        vue = catalogue_classes()
        self.assertEqual(vue["ordre"], list(ORDRE_CLASSES))
        self.assertIn("diviseur_menages", vue)
        self.assertIn("note_solde", vue)
        self.assertEqual(len(vue["classes"]), len(ORDRE_CLASSES))
        total = 0
        for fiche in vue["classes"]:
            with self.subTest(classe=fiche["cle"]):
                self.assertGreater(fiche["nb_leviers"], 0)
                self.assertGreater(fiche["familles_nb"], 0)
                self.assertTrue(fiche["exemples"])
                for exemple in fiche["exemples"]:
                    self.assertIn(exemple["cle"], LEVIERS)
                    self.assertEqual(classe_de(exemple["cle"]), fiche["cle"])
                total += fiche["nb_leviers"]
        self.assertEqual(total, len(LEVIERS))

    def test_le_catalogue_dit_quelles_classes_portent_des_euros(self):
        """La page n'a pas à deviner : l'information voyage avec le catalogue."""
        vue = catalogue_classes()
        monetaires = [fiche["cle"] for fiche in vue["classes"] if fiche["monetaire"]]
        self.assertEqual(monetaires, list(CLASSES_MONETAIRES))
        for fiche in vue["classes"]:
            with self.subTest(classe=fiche["cle"]):
                self.assertEqual(fiche["monetaire"], fiche["cle"] in CLASSES_MONETAIRES)


class TestTotauxParClasse(unittest.TestCase):
    """Les totaux lisent le moteur : euros dans le solde, unités à part."""

    @classmethod
    def setUpClass(cls):
        cls.flux = construire_flux(_parametres_preset("mandature"), 4)
        cls.totaux = totaux_classe(cls.flux)

    def test_le_solde_des_classes_ne_melange_pas_les_unites(self):
        classes = self.totaux["classes"]
        for cle in CLASSES_MONETAIRES:
            with self.subTest(classe=cle):
                self.assertGreater(classes[cle]["montant_mde"], 0)
                self.assertEqual(classes[cle]["montant_hors_budget_mde"], 0.0)
        # Règles et monde : des unités, pas des euros — jamais dans le solde.
        self.assertGreater(classes["regles"]["montant_hors_budget_mde"], 0)
        for cle in ("regles", "monde"):
            with self.subTest(classe=cle):
                self.assertEqual(classes[cle]["montant_mde"], 0.0)

    def test_le_solde_est_entrees_moins_sorties(self):
        self.assertAlmostEqual(
            self.totaux["solde_mde"],
            round(self.totaux["entrees_mde"] - self.totaux["sorties_mde"], 3),
            places=3)

    def test_les_deux_lectures_du_moteur_restent_visibles(self):
        self.assertIn("recettes_moteur_mde", self.totaux)
        self.assertIn("depenses_moteur_mde", self.totaux)
        self.assertEqual(self.totaux["recettes_moteur_mde"],
                         round(self.flux["recettes_nouvelles_mde"], 3))
        self.assertEqual(self.totaux["depenses_moteur_mde"],
                         round(self.flux["depenses_nouvelles_mde"], 3))
        # Le solde des classes et le solde du moteur ne peuvent pas être
        # identiques sur ce préréglage : les leviers d'efficacité n'y sont pas
        # comptés de la même façon, et la page l'explique au lieu de le taire.
        self.assertNotEqual(self.totaux["solde_mde"],
                            round(self.totaux["recettes_moteur_mde"]
                                  - self.totaux["depenses_moteur_mde"], 3))

    def test_les_drapeaux_ne_gonflent_pas_le_solde(self):
        # Les cinq drapeaux du préréglage pèsent 5 unités : mesurées, rangées
        # hors budget, et jamais fondues dans le solde des classes.
        self.assertEqual(self.totaux["hors_budget_mde"], 5.0)
        self.assertIn("Hors solde", NOTE_HORS_BUDGET)
        self.assertIn("note_hors_budget", self.totaux)

    def test_un_choc_exogene_n_entre_pas_dans_le_solde(self):
        parametres = _parametres_preset("choc_mondial")
        attendus = sorted(
            cle for cle, levier in LEVIERS.items()
            if levier.famille == "exogene_monde"
            and (parametres.get(cle) or 0) != 0
            and classe_de(cle) == "monde")
        self.assertTrue(attendus)
        totaux = totaux_classe(construire_flux(parametres, 4))
        self.assertEqual(totaux["classes"]["monde"]["montant_mde"], 0.0)
        self.assertGreater(totaux["classes"]["monde"]["montant_hors_budget_mde"], 0)
        actifs = sorted(entree["cle"] for entree in totaux["classes"]["monde"]["leviers"])
        self.assertEqual(actifs, attendus)

    def test_la_serie_annuelle_couvre_toutes_les_annees(self):
        flux_annuels = _flux_annuels("mandature", horizon=5)
        serie = serie_classes(flux_annuels)
        self.assertEqual(len(serie), len(flux_annuels))
        self.assertEqual([bloc["annee"] for bloc in serie], [1, 2, 3, 4, 5])
        # La montée en charge déclarée ne fait pas décroître les recettes de la
        # première à la dernière année de ce préréglage.
        self.assertLessEqual(serie[0]["classes"]["recettes"]["montant_mde"],
                             serie[-1]["classes"]["recettes"]["montant_mde"])

    def test_les_leviers_actifs_sont_listes_par_classe(self):
        for cle, bloc in self.totaux["classes"].items():
            with self.subTest(classe=cle):
                self.assertEqual(len(bloc["leviers"]), bloc["nb_actifs"])
                for entree in bloc["leviers"]:
                    self.assertEqual(classe_de(entree["cle"]), cle)

    def test_un_plan_de_coupes_ne_passe_pas_pour_un_plan_de_depenses(self):
        # Le préréglage « austérité » baisse les budgets : les montants de la
        # classe « dépenses » doivent être négatifs, et le solde positif. Une
        # valeur absolue ferait passer une coupe de 31,9 Md€ pour une dépense.
        totaux = totaux_classe(construire_flux(_parametres_preset("austerite"), 4))
        depenses = totaux["classes"]["depenses"]
        self.assertLess(depenses["montant_mde"], 0)
        self.assertGreater(depenses["montant_absolu_mde"], 0)
        self.assertGreater(totaux["solde_mde"], 0)
        self.assertLess(totaux["sorties_mde"], 0)
        self.assertEqual(totaux["entrees_mde"], 0.0)

    def test_le_montant_absolu_mesure_le_volume_sans_signes(self):
        bloc = self.totaux["classes"]["recettes"]
        self.assertEqual(
            bloc["montant_absolu_mde"],
            round(sum(abs(entree["montant_mde"]) for entree in bloc["leviers"]), 3))

    def test_un_flux_vide_ne_produit_pas_de_faux_totaux(self):
        totaux = totaux_classe({})
        self.assertEqual(totaux["entrees_mde"], 0.0)
        self.assertEqual(totaux["sorties_mde"], 0.0)
        self.assertEqual(totaux["solde_mde"], 0.0)
        for bloc in totaux["classes"].values():
            self.assertEqual(bloc["nb_actifs"], 0)
            self.assertEqual(bloc["leviers"], [])


class TestEurosParMenage(unittest.TestCase):
    """La traduction en euros par ménage affiche son diviseur et son statut."""

    def test_conversion_lineaire(self):
        self.assertAlmostEqual(euros_par_menage(30.0), 1000.0, places=6)
        self.assertAlmostEqual(euros_par_menage(3.0), 100.0, places=6)
        self.assertEqual(euros_par_menage(0.0), 0.0)
        self.assertEqual(euros_par_menage(-3.0), -100.0)

    def test_diviseur_declare_et_statut_visible(self):
        self.assertGreater(DIVISEUR_MENAGES["valeur"], 0)
        self.assertTrue(DIVISEUR_MENAGES["libelle"])
        self.assertIn("vérifier", DIVISEUR_MENAGES["statut"])
        self.assertIn("ordre de grandeur", DIVISEUR_MENAGES["note"].lower())

    def test_diviseur_nul_refuse(self):
        with self.assertRaises(ValueError):
            euros_par_menage(3.0, diviseur=0)


if __name__ == "__main__":
    unittest.main()
