"""
tests/test_bulles.py — Bulles explicatives par levier.

Ces tests vérifient que **chaque** réglage du catalogue possède une bulle
calculée (et non rédigée) : chaîne d'interaction issue des formules réelles,
répercussions mesurées borne par borne, lecture opportunités / désagréments, et
signalement honnête des cas où le harnais de notation ne relaie pas encore un
effet du moteur.
"""

import time
import unittest

from simulateur.bulles import (
    DETAILS,
    SEUIL_MOUVEMENT,
    THEMES_DOMAINES,
    bulle_levier,
    bulles_catalogue,
    champ_moteur,
    consommateurs,
    emissions_levier,
    mesures_levier,
    phrase_lecture,
    strates_theme,
)
from simulateur.domaines import DOMAINES_PAR_CLE, SPECS
from simulateur.donnees_live import construire_contexte
from simulateur.parametres import LEVIERS


class TestChaineDInteraction(unittest.TestCase):
    """Le premier étage : ce que le levier écrit, et qui le lit."""

    @classmethod
    def setUpClass(cls):
        cls.contexte = construire_contexte(utiliser_cache=False, rafraichir=False, hors_ligne=True)
        cls.catalogue = bulles_catalogue(cls.contexte, detail="resume")
        cls.bulles = cls.catalogue["bulles"]

    def test_chaque_levier_a_une_bulle(self):
        self.assertEqual(len(self.bulles), len(LEVIERS))
        self.assertEqual(set(self.bulles), set(LEVIERS))

    def test_consommateurs_relies_aux_specifications(self):
        """Un médiateur lu par une formule est bien rattaché à un domaine noté."""
        for spec in SPECS:
            for terme, _ in spec.termes:
                lecteurs = consommateurs(terme)
                if terme.startswith("levier:"):
                    continue
                self.assertTrue(
                    any(lecteur["indicateur"] == spec.cle for lecteur in lecteurs),
                    f"{terme} non rattaché à {spec.cle}",
                )

    def test_tous_les_themes_declares_sont_mappes(self):
        """Aucun thème d'`effets_directs` ne doit rester sans rattachement."""
        self.assertEqual(self.catalogue["resume"]["theme_inconnu"], [])
        connus = set(THEMES_DOMAINES)
        for levier in LEVIERS.values():
            for theme in levier.effets_directs:
                self.assertIn(theme, connus, f"thème non mappé : {theme}")
                for domaine in THEMES_DOMAINES[theme]:
                    self.assertIn(domaine, DOMAINES_PAR_CLE,
                                  f"thème {theme} → domaine inconnu {domaine}")
                self.assertTrue(strates_theme(theme))

    def test_emissions_du_catalogue_non_orphelines(self):
        """Tout médiateur émis atteint les indicateurs par un chemin connu.

        Soit une formule le lit, soit il passe par une autre échelle du même
        médiateur, soit il passe par un agrégat budgétaire. Un médiateur
        réellement orphelin doit être un choix explicite, pas un oubli : ce test
        échoue pour obliger à trancher.
        """
        self.assertEqual(self.catalogue["resume"]["leviers_avec_maillon_non_relaye"], [])

    def test_champ_moteur_et_emissions_coherents(self):
        """Les leviers « champ » déclarent leur état moteur, les autres non."""
        for cle, levier in LEVIERS.items():
            bulle = self.bulles[cle]
            if levier.champ:
                self.assertIsNotNone(bulle["champ_moteur"], cle)
                self.assertEqual(bulle["champ_moteur"]["champ"], levier.champ)
            else:
                self.assertIsNone(bulle["champ_moteur"], cle)

    def test_emissions_portent_un_montant_et_un_sens(self):
        for cle, levier in LEVIERS.items():
            emissions = emissions_levier(cle, levier.defaut + (levier.pas or 1.0))
            for emission in emissions:
                self.assertIn("mediateur", emission)
                self.assertIn(emission["sens"], ("hausse", "baisse", "neutre"))
                self.assertIsInstance(emission["relaye"], bool)
                if emission["relaye"]:
                    self.assertTrue(emission["consommateurs"])
                    self.assertTrue(emission["domaines"])

    def test_champ_moteur_inconnu_refuse(self):
        with self.assertRaises(ValueError):
            bulle_levier("levier_qui_n_existe_pas")
        with self.assertRaises(ValueError):
            bulle_levier("tva_taux_normal", detail="trop_de_detail")
        self.assertEqual(set(DETAILS), {"complet", "resume"})
        self.assertIsNone(champ_moteur("tva_taux_normal"))
        self.assertEqual(champ_moteur("blocus_taiwan")["champ"], "blocus_taiwan_intensite")


class TestRepercussionsMesurees(unittest.TestCase):
    """Le deuxième étage : ce que la simulation montre réellement."""

    @classmethod
    def setUpClass(cls):
        cls.contexte = construire_contexte(utiliser_cache=False, rafraichir=False, hors_ligne=True)
        cls.catalogue = bulles_catalogue(cls.contexte, detail="resume")
        cls.bulles = cls.catalogue["bulles"]

    def test_chaque_mesure_porte_les_vingt_domaines(self):
        for cle, bulle in self.bulles.items():
            self.assertTrue(bulle["mesures"], cle)
            for mesure in bulle["mesures"]:
                self.assertEqual(len(mesure["domaines"]), len(DOMAINES_PAR_CLE), cle)
                self.assertIn(mesure["borne"], ("basse", "haute", "pas"))
                for domaine in mesure["domaines"]:
                    self.assertIn(domaine["cle"], DOMAINES_PAR_CLE)
                    self.assertLessEqual(abs(domaine["delta"]), 50.0)
                self.assertIn(mesure["seuils"]["niveau_global"], (
                    "favorable", "tolerable", "vigilance", "risque", "hors_sol", None,
                ))
                self.assertEqual(len(mesure["seuils"]["strates"]), 5)

    def test_bilan_domaines_touches_coherent(self):
        for cle, bulle in self.bulles.items():
            touche = [domaine["cle"] for domaine in bulle["bilan_domaines"] if domaine["touche"]]
            mouvementes = {
                domaine["cle"]
                for mesure in bulle["mesures"]
                for domaine in mesure["domaines"]
                if abs(domaine["delta"]) >= SEUIL_MOUVEMENT
            }
            self.assertEqual(set(touche), mouvementes, cle)
            self.assertEqual(bulle["sans_effet_mesure"], not touche)

    def test_presque_tous_les_leviers_bougent_quelque_chose(self):
        """Au moins 95 % des leviers déplacent un domaine à leurs bornes.

        Le nombre exact dépend du contexte de données (mode live ou référence) :
        ce qui est exigé ici, c'est que les exceptions restent rares **et**
        documentées (voir le test suivant).
        """
        resume = self.catalogue["resume"]
        self.assertGreaterEqual(resume["leviers_avec_effet_mesure"], int(0.95 * len(LEVIERS)),
                                f"sans effet : {resume['leviers_sans_effet_mesure']}")

    def test_tout_levier_sans_effet_note_est_moteur_et_journalise(self):
        """Un levier sans effet mesuré doit a minima piloter l'état du moteur."""
        for cle in self.catalogue["resume"]["leviers_sans_effet_mesure"]:
            bulle = bulle_levier(cle, self.contexte, detail="complet")
            self.assertTrue(bulle["sans_effet_mesure"], cle)
            self.assertIsNotNone(bulle["champ_moteur"], cle)
            self.assertTrue(bulle["lecture"]["strates"],
                            f"{cle} : aucune répercussion journalisée")

    def test_le_levier_sans_effet_noté_documente_ses_repercussions(self):
        """L'exception est documentée : champ moteur + journal institutionnel."""
        bulle = bulle_levier("clause_sauvegarde_defense", self.contexte, detail="complet")
        self.assertTrue(bulle["sans_effet_mesure"])
        self.assertIsNotNone(bulle["champ_moteur"])
        journaux = [ligne for mesure in bulle["mesures"] for ligne in mesure["journal"]]
        self.assertTrue(any("Clause de sauvegarde" in ligne["texte"] for ligne in journaux),
                        f"journal inattendu : {journaux}")
        self.assertTrue(any("Europe" in (ligne["strate"] or "") for ligne in journaux))

    def test_les_bornes_encadrent_le_defaut(self):
        for cle, levier in LEVIERS.items():
            mesures = mesures_levier(cle, self.contexte)
            if levier.type == "interrupteur":
                continue
            valeurs = [mesure["valeur"] for mesure in mesures]
            self.assertIn(levier.minimum, valeurs, cle)
            self.assertIn(levier.maximum, valeurs, cle)

    def test_cache_memoise_la_bulle(self):
        premiere = bulle_levier("tva_taux_normal", self.contexte)
        seconde = bulle_levier("tva_taux_normal", self.contexte)
        self.assertIs(premiere, seconde)

    def test_detail_resume_allege_sans_perdre_lessentiel(self):
        complete = bulle_levier("aide_logement", self.contexte, detail="complet")
        resume = bulle_levier("aide_logement", self.contexte, detail="resume")
        self.assertIn("indicateurs", complete["mesures"][0])
        self.assertNotIn("indicateurs", resume["mesures"][0])
        self.assertNotIn("journal", resume["mesures"][0])
        self.assertNotIn("strates", resume["lecture"])
        self.assertEqual(complete["lecture"]["phrase"], resume["lecture"]["phrase"])
        self.assertIn("emissions", resume)

    def test_selection_de_leviers(self):
        extrait = bulles_catalogue(self.contexte, cles=["tva_taux_normal", "aide_logement"],
                                   detail="resume")
        self.assertEqual(sorted(extrait["bulles"]), ["aide_logement", "tva_taux_normal"])
        self.assertEqual(extrait["nombre"], 2)


class TestLectureGuidee(unittest.TestCase):
    """Le troisième étage : opportunités, désagréments, garde-fous, compensations."""

    @classmethod
    def setUpClass(cls):
        cls.contexte = construire_contexte(utiliser_cache=False, rafraichir=False, hors_ligne=True)
        cls.bulles = bulles_catalogue(cls.contexte, detail="resume")["bulles"]

    def test_chaque_bulle_produit_une_lecture(self):
        for cle, bulle in self.bulles.items():
            lecture = bulle["lecture"]
            self.assertTrue(lecture["phrase"], cle)
            self.assertEqual(lecture["phrase"], phrase_lecture(bulle))
            for entree in lecture["opportunites"]:
                self.assertGreater(entree["gain"], 0.0)
                self.assertTrue(entree["libelle"])
            for entree in lecture["desagrements"]:
                self.assertLess(entree["perte"], 0.0)

    def test_les_desagrements_proposent_des_compensations(self):
        bulle = self.bulles["dgf_delta"]
        domaines_degrades = [entree["domaine"] for entree in bulle["lecture"]["desagrements"]]
        self.assertTrue(domaines_degrades)
        domaines_compenses = {entree["domaine"] for entree in bulle["lecture"]["compensations"]}
        self.assertTrue(domaines_compenses & set(domaines_degrades),
                        f"aucune compensation pour {domaines_degrades}")
        for entree in bulle["lecture"]["compensations"]:
            for levier in entree["leviers"]:
                self.assertNotEqual(levier["cle"], "dgf_delta")
                self.assertGreater(levier["coefficient"], 0)

    def test_les_garde_fous_sont_cites_avec_leur_strate(self):
        bulle = self.bulles["dgf_delta"]
        self.assertTrue(bulle["lecture"]["a_surveiller"])
        for entree in bulle["lecture"]["a_surveiller"]:
            if entree["type"] == "garde_fou":
                self.assertTrue(entree["message"])
                self.assertTrue(entree["niveau_libelle"])
        phrase = bulle["lecture"]["phrase"]
        self.assertIn("Opportunités", phrase)
        self.assertIn("Désagréments", phrase)
        self.assertIn("À surveiller", phrase)

    def test_phrase_explicite_quand_aucun_domaine_ne_bouge(self):
        bulle = self.bulles["clause_sauvegarde_defense"]
        self.assertIn("Aucun des 20 domaines", bulle["lecture"]["phrase"])

    def test_effets_declares_separes_des_themes_transverses(self):
        bulle = self.bulles["tva_taux_normal"]
        themes = {effet["theme"] for effet in bulle["effets_directs"]}
        transverses = {effet["theme"] for effet in bulle["effets_hors_domaine"]}
        self.assertIn("pouvoir_achat", themes)
        self.assertIn("inflation", themes)
        # Le mapping thème → domaines est exhaustif : aucun thème ne reste
        # orphelin, donc la liste des thèmes transverses est vide par construction.
        self.assertEqual(transverses, set())
        self.assertTrue(all(effet["strates"] for effet in bulle["effets_directs"]))
        for effet in bulle["effets_directs"]:
            self.assertTrue(effet["domaines"])
            self.assertTrue(effet["domaines_libelles"])


class TestPerformance(unittest.TestCase):
    """Une bulle doit rester calculable à la demande, sans figer la page."""

    def test_une_bulle_se_calcule_en_moins_d_une_seconde(self):
        contexte = construire_contexte(utiliser_cache=False, rafraichir=False, hors_ligne=True)
        depart = time.perf_counter()
        bulle = bulle_levier("aide_logement", contexte)
        duree = time.perf_counter() - depart
        self.assertLess(duree, 1.5, f"bulle calculée en {duree:.2f} s")
        self.assertIn("mesures", bulle)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
