"""
tests/test_seuils.py — garde-fous : seuils, messages et marges.

Ces tests protègent la promesse de la console de veille : chaque grandeur
surveillée doit exister réellement dans la charge utile du moteur, chaque borne
doit être ordonnée du tolérable au hors-sol, chaque message doit être formaté
(aucun « {valeur} » résiduel), et les situations dangereuses doivent être
détectées — sans crier au loup sur une trajectoire neutre.
"""

import re
import unittest
from pathlib import Path

from simulateur.domaines import DOMAINES
from simulateur.donnees_live import construire_contexte
from simulateur.interface import HTML_PAGE
from simulateur.moteur_parametrique import simuler
from simulateur.parametres import PRESETS
from simulateur.seuils import (
    DOMAINES_POPULATION,
    GARDE_FOUS,
    GARDE_FOUS_ECART,
    LIBELLES_NIVEAUX,
    LIBELLES_STRATES,
    NIVEAUX,
    RANG_NOTES,
    Borne,
    GardeFou,
    evaluer_garde_fou,
    evaluer_sortie,
    resume_court,
)


def _contexte():
    return construire_contexte(utiliser_cache=False, rafraichir=False, hors_ligne=True)


class TestLeVocabulaireDesIndices(unittest.TestCase):
    """« Indice non calibré » — jamais « probabilité » — pour l'escalade et le nucléaire.

    Mesuré le 15 octobre 2026 : la page servie annonçait « Probabilité d'escalade
    mondiale (%) · Escalade estimée à 17 % », quand le moteur commente le même
    nombre par « indice heuristique d'escalade 17.0/100 », le CLI l'imprime
    « Indice heuristique d'escalade », et `docs/08_STRATE_GEOPOLITIQUE…` ouvre sur
    « des indices heuristiques **non calibrés, et non des probabilités** ».

    C'est la lacune P1 de l'audit : renommer les concepts, pas publier une
    probabilité d'emploi sans méthode défendable. Un chiffre, un vocabulaire.
    """

    INDICES = ("probabilite_escalade_mondiale_pct", "risque_nucleaire_tactique_pct")

    def _garde(self, cle):
        for garde in GARDE_FOUS:
            if garde.cle == cle:
                return garde
        self.fail(f"le garde-fou {cle} n'existe plus")

    def test_les_deux_garde_fous_ne_s_appellent_plus_des_probabilites(self):
        for cle in self.INDICES:
            with self.subTest(cle=cle):
                garde = self._garde(cle)
                self.assertNotIn("Probabilité", garde.libelle,
                                 "la page repromet une probabilité sans méthode de calibration")
                self.assertIn("non calibré", garde.libelle,
                              "le libellé ne dit plus que l'indice n'est pas calibré")
                self.assertEqual(garde.unite, "/100",
                                 "l'unité en pourcent fait lire le chiffre comme une probabilité")

    def test_la_source_dit_ce_que_le_chiffre_n_est_pas(self):
        for cle in self.INDICES:
            with self.subTest(cle=cle):
                source = self._garde(cle).source
                self.assertTrue(source.strip(), "la source a disparu")
                self.assertRegex(source, r"non calibr|pas une probabilité|branche imposée",
                                 f"la source ne dit pas ce que le chiffre n'est pas : {source}")

    def test_la_page_n_affiche_plus_le_mot_probabilite_pour_ces_indices(self):
        """Le tableau de la strate 5, lu dans la page générée."""
        for mot in ("Probabilité d’escalade", "Probabilité d'escalade",
                    "Risque nucléaire tactique — proxy"):
            with self.subTest(mot=mot):
                self.assertNotIn(mot, HTML_PAGE,
                                 "la page a repris le vocabulaire de la probabilité")
        for attendu in ("Indice heuristique d’escalade — non calibré",
                        "Indice nucléaire tactique — non calibré"):
            with self.subTest(attendu=attendu):
                self.assertIn(attendu, HTML_PAGE,
                              "la page n'annonce plus le vocabulaire de l'indice")
        self.assertIn("unite:'/100',precision:1,sens:-1}", HTML_PAGE,
                      "les deux lignes ne sont plus lues sur 100")

    def test_le_moteur_dit_deja_indice_et_la_page_le_suit(self):
        """La source de vérité est le commentaire du moteur, pas le libellé d'hier."""
        source = Path(__file__).resolve().parents[1] / "simulateur" / "geopolitique_annuelle.py"
        texte = source.read_text(encoding="utf-8")
        self.assertIn("indice heuristique d'escalade", texte,
                      "le moteur ne dit plus « indice » : la page et lui divergent")
        self.assertRegex(texte, r"indice nucléaire \{geo\.risque_usage_nucleaire_tactique_pct",
                         "le moteur ne dit plus « indice nucléaire »")

    def test_aucun_message_ne_promet_de_calibration(self):
        """Le mot « probabilité » n'apparaît que pour dire qu'il ne s'applique pas.

        Interdire le mot serait un contrôle qui lit la présence et pas la phrase :
        « pas une probabilité » est exactement ce qu'un message doit dire. Ce qui
        est interdit, c'est de la promettre — « probabilité d'escalade », « probabilité
        d'emploi », « probabilité estimée ».
        """
        interdits = ("probabilité d'escalade", "probabilité d'emploi",
                     "probabilité estimée", "probabilité de guerre")
        for cle in self.INDICES:
            garde = self._garde(cle)
            for borne in garde.bornes:
                with self.subTest(cle=cle, seuil=borne.seuil):
                    message = borne.message.lower()
                    for interdit in interdits:
                        if interdit not in message:
                            continue
                        # La négation l'emporte : « pas une probabilité d'emploi »
                        # est exactement la phrase qu'on veut lire.
                        avant_le_mot = message.split(interdit, 1)[0]
                        self.assertRegex(avant_le_mot, r"pas (une|de)|non calibr|jamais",
                                         f"un message de seuil promet une {interdit}")
                    if "probabilité" in message:
                        self.assertRegex(message, r"pas une probabilité|non calibr",
                                         "un message parle de probabilité sans dire "
                                         "qu'elle ne s'applique pas")


class TestStructureDesGardeFous(unittest.TestCase):
    """Chaque garde-fou doit être exploitable et documenté."""

    def setUp(self):
        self.gardes = list(GARDE_FOUS) + list(GARDE_FOUS_ECART)

    def test_au_moins_vingt_cinq_garde_fous(self):
        self.assertGreaterEqual(len(self.gardes), 25)
        self.assertGreaterEqual(len(GARDE_FOUS_ECART), 4)

    def test_strates_valides_et_couvertes(self):
        strates = {garde.strate for garde in self.gardes}
        self.assertTrue(strates <= set(LIBELLES_STRATES))
        for strate in (1, 2, 3, 4, 5):
            self.assertIn(strate, strates, f"aucun garde-fou pour la strate {strate}")

    def test_niveaux_connus_et_bornes_ordonnees(self):
        for garde in self.gardes:
            self.assertIn(garde.sens, {"max", "min", "note", "booleen"}, garde.cle)
            self.assertTrue(garde.bornes, garde.cle)
            for borne in garde.bornes:
                self.assertIn(borne.niveau, NIVEAUX, garde.cle)
                self.assertTrue(borne.message.strip(), garde.cle)
            # Le meilleur palier peut être « favorable » (mesures gagées) ;
            # le pire est toujours « hors_sol », porté par la borne infinie.
            if garde.sens in ("max", "note"):
                seuils = [borne.seuil for borne in garde.bornes]
                self.assertEqual(seuils, sorted(seuils), f"{garde.cle} : bornes non croissantes")
                self.assertIn(garde.bornes[0].niveau, {"favorable", "tolerable"}, garde.cle)
                self.assertEqual(garde.bornes[-1].niveau, "hors_sol", garde.cle)
                self.assertEqual(garde.bornes[-1].seuil, float("inf"), garde.cle)
            elif garde.sens == "min":
                seuils = [borne.seuil for borne in garde.bornes]
                self.assertEqual(seuils, sorted(seuils, reverse=True), f"{garde.cle} : bornes non décroissantes")
                self.assertIn(garde.bornes[0].niveau, {"favorable", "tolerable"}, garde.cle)
                self.assertEqual(garde.bornes[-1].niveau, "hors_sol", garde.cle)
                self.assertEqual(garde.bornes[-1].seuil, float("-inf"), garde.cle)

    def test_chaque_garde_fou_documente_son_seuil(self):
        sans_source = [garde.cle for garde in self.gardes if not garde.source.strip()]
        self.assertEqual(sans_source, [], f"garde-fous sans source : {sans_source}")
        for garde in self.gardes:
            self.assertTrue(garde.libelle.strip())
            self.assertGreaterEqual(garde.precision, 0)

    def test_unites_renseignees_hors_notes_et_booleens(self):
        for garde in self.gardes:
            if garde.sens in ("note", "booleen"):
                continue
            self.assertTrue(garde.unite, f"{garde.cle} : unité manquante")
            self.assertLessEqual(len(garde.unite), 14, garde.cle)

    def test_notes_connues(self):
        for rang in RANG_NOTES.values():
            self.assertGreaterEqual(rang, 1)
        self.assertLess(RANG_NOTES["AAA"], RANG_NOTES["AA-"])
        self.assertLess(RANG_NOTES["AA-"], RANG_NOTES["BBB-"])

    def test_domaines_population_existent(self):
        cles = {domaine.cle for domaine in DOMAINES}
        self.assertTrue(set(DOMAINES_POPULATION) <= cles,
                        f"domaines inconnus : {set(DOMAINES_POPULATION) - cles}")
        self.assertGreaterEqual(len(DOMAINES_POPULATION), 6)


class TestReferencesReelles(unittest.TestCase):
    """Les garde-fous doivent pointer sur des champs qui existent vraiment."""

    @classmethod
    def setUpClass(cls):
        cls.sortie = simuler({}, _contexte(), avec_impacts=False)
        cls.charge = cls.sortie.en_dict()

    def test_cles_des_etapes_existent(self):
        champs = set(self.charge["etapes"][-1])
        inconnus = [garde.cle for garde in GARDE_FOUS + GARDE_FOUS_ECART
                    if garde.ou == "etape" and garde.cle not in champs]
        self.assertEqual(inconnus, [], f"champs absents des étapes : {inconnus}")

    def test_cles_de_synthese_existent(self):
        synthese = set(self.charge["synthese"])
        inconnus = [garde.cle for garde in GARDE_FOUS + GARDE_FOUS_ECART
                    if garde.ou == "synthese"
                    and garde.cle not in synthese
                    and garde.cle != "charge_dette_pib"]  # recalculé depuis la charge et le PIB
        self.assertEqual(inconnus, [], f"champs absents de la synthèse : {inconnus}")

    def test_diagnostic_accompagne_chaque_simulation(self):
        diagnostic = self.sortie.diagnostic
        self.assertEqual(diagnostic["niveau_global"], diagnostic["verdict"]["niveau"])
        self.assertEqual(len(diagnostic["strates"]), len({g.strate for g in GARDE_FOUS + GARDE_FOUS_ECART}))
        self.assertEqual(diagnostic["barème"], list(NIVEAUX))
        self.assertIn(diagnostic["population"]["niveau"], NIVEAUX)


class TestApplicationDesBornes(unittest.TestCase):
    """La mécanique des bornes, testée sur des cas fabriqués."""

    def _garde(self, seuils):
        return GardeFou(
            cle="essai", libelle="Essai", strate=2, sens="max",
            bornes=tuple(Borne(seuil, niveau, f"message {niveau} ({{valeur}} / {{seuil}} / {{marge}})")
                         for seuil, niveau in seuils),
        )

    def test_sens_max_choisit_la_borne_franchie(self):
        garde = self._garde([(3.0, "tolerable"), (5.0, "vigilance"), (float("inf"), "hors_sol")])
        self.assertEqual(evaluer_garde_fou(garde, 2.0)["niveau"], "tolerable")
        self.assertEqual(evaluer_garde_fou(garde, 3.5)["niveau"], "vigilance")
        self.assertEqual(evaluer_garde_fou(garde, 12.0)["niveau"], "hors_sol")

    def test_marge_vers_le_prochain_seuil(self):
        garde = self._garde([(3.0, "tolerable"), (5.0, "vigilance"), (float("inf"), "hors_sol")])
        resultat = evaluer_garde_fou(garde, 4.4)
        self.assertAlmostEqual(resultat["marge"], 0.6, places=3)
        self.assertEqual(resultat["prochain_seuil"], 5.0)
        self.assertEqual(resultat["prochain_niveau"], "hors_sol")

    def test_hors_sol_indique_la_distance_de_retour(self):
        garde = self._garde([(3.0, "tolerable"), (5.0, "vigilance"), (float("inf"), "hors_sol")])
        resultat = evaluer_garde_fou(garde, 6.5)
        self.assertEqual(resultat["niveau"], "hors_sol")
        self.assertAlmostEqual(resultat["marge"], 1.5, places=3)
        self.assertNotIn("{", resultat["message"])
        self.assertIn("1,5", resultat["message"])

    def test_valeur_absente_retourne_none(self):
        garde = self._garde([(3.0, "tolerable"), (float("inf"), "hors_sol")])
        self.assertIsNone(evaluer_garde_fou(garde, None))

    def test_booleen(self):
        garde = GardeFou(cle="drapeau", libelle="Drapeau", strate=3, sens="booleen",
                         bornes=(Borne(1.0, "risque", "actif"), Borne(0.0, "tolerable", "inactif")))
        self.assertEqual(evaluer_garde_fou(garde, True)["niveau"], "risque")
        self.assertEqual(evaluer_garde_fou(garde, False)["niveau"], "tolerable")


class TestDiagnosticDesPrereglages(unittest.TestCase):
    """Les situations doivent être jugées comme un humain les lirait."""

    @classmethod
    def setUpClass(cls):
        cls.contexte = _contexte()
        cls.diagnostics = {}
        for cle in ("statut_quo", "mandature", "austerite", "escalade_nucleaire",
                    "transition_ecologique", "resilience"):
            cls.diagnostics[cle] = simuler(
                PRESETS[cle]["parametres"], cls.contexte, avec_impacts=False
            ).diagnostic

    def test_la_trajectoire_neutre_ne_est_pas_hors_sol(self):
        self.assertNotEqual(self.diagnostics["statut_quo"]["niveau_global"], "hors_sol")
        self.assertEqual(self.diagnostics["statut_quo"]["verdict"]["nombre_hors_sol"], 0)

    def test_la_mandature_ne_met_pas_la_population_en_danger(self):
        diagnostic = self.diagnostics["mandature"]
        self.assertNotEqual(diagnostic["niveau_global"], "hors_sol")
        self.assertIn(diagnostic["population"]["niveau"], {"tolerable", "vigilance"})

    def test_l_austerite_met_la_population_en_risque(self):
        diagnostic = self.diagnostics["austerite"]
        self.assertIn(diagnostic["population"]["niveau"], {"risque", "hors_sol"})
        self.assertGreater(diagnostic["population"]["valeur"], 58.0)

    def test_la_guerre_totale_est_hors_sol_partout(self):
        diagnostic = self.diagnostics["escalade_nucleaire"]
        self.assertEqual(diagnostic["niveau_global"], "hors_sol")
        self.assertEqual(diagnostic["population"]["niveau"], "hors_sol")
        self.assertGreaterEqual(diagnostic["verdict"]["nombre_hors_sol"], 5)
        self.assertEqual(diagnostic["verdict"]["strates_en_alerte"], [1, 2, 3, 4, 5])

    def test_un_programme_non_gage_declenche_le_garde_fou_budgetaire(self):
        alertes = self.diagnostics["resilience"]["alertes"]
        solde = [a for a in alertes if a["cle"] == "solde_mesures_mde"]
        self.assertTrue(solde, "le coût net des mesures doit être signalé")
        self.assertEqual(solde[0]["niveau"], "hors_sol")
        # Le message doit chiffrer l'effort de retour, jamais laisser un « — ».
        self.assertRegex(solde[0]["message"], r"\d")
        self.assertNotIn("—", solde[0]["message"])

    def test_les_messages_sont_formates(self):
        for cle, diagnostic in self.diagnostics.items():
            for alerte in diagnostic["alertes"]:
                self.assertNotIn("{", alerte["message"], f"{cle} / {alerte['libelle']}")
                self.assertNotIn("}", alerte["message"], f"{cle} / {alerte['libelle']}")

    def test_verdict_coherent_avec_les_strates(self):
        for diagnostic in self.diagnostics.values():
            niveaux = [strate["niveau"] for strate in diagnostic["strates"]]
            niveaux.append(diagnostic["population"]["niveau"])
            attendu = max(niveaux, key=NIVEAUX.index)
            self.assertEqual(diagnostic["niveau_global"], attendu)

    def test_marges_et_progres_exploitables(self):
        diagnostic = self.diagnostics["transition_ecologique"]
        self.assertTrue(diagnostic["marges"])
        for marge in diagnostic["marges"]:
            self.assertGreater(marge["marge"], 0)
            self.assertIn(marge["prochain_niveau"], NIVEAUX)
            self.assertNotIn("note", marge["cle"])
        for progres in diagnostic["progres"]:
            self.assertGreater(progres["ecart"], 0)
            self.assertGreater(len(progres["message_cible"]), 10)


class TestRobustesse(unittest.TestCase):
    """Le diagnostic ne doit jamais faire échouer une simulation."""

    def test_charge_vide(self):
        diagnostic = evaluer_sortie({})
        self.assertIn(diagnostic["niveau_global"], NIVEAUX + ("inconnu",))
        self.assertEqual(diagnostic["alertes"], [])
        self.assertEqual(diagnostic["marges"], [])
        self.assertEqual(diagnostic["verdict"]["nombre_hors_sol"], 0)

    def test_resume_court(self):
        diagnostic = simuler(PRESETS["mandature"]["parametres"], _contexte(),
                             avec_impacts=False).diagnostic
        resume = resume_court(diagnostic)
        self.assertEqual(resume["niveau_global"], diagnostic["niveau_global"])
        self.assertEqual(resume["libelle"], LIBELLES_NIVEAUX[diagnostic["niveau_global"]])
        self.assertLessEqual(len(resume["premieres_alertes"]), 3)
        self.assertIsInstance(resume["risque_population"], float)

    def test_libelles_francais_des_niveaux(self):
        for niveau in NIVEAUX:
            self.assertTrue(LIBELLES_NIVEAUX[niveau])
        self.assertEqual(LIBELLES_NIVEAUX["hors_sol"], "hors-sol")
        self.assertTrue(re.match(r"^\d$", "1"))  # garde-fou de lisibilité du fichier


if __name__ == "__main__":
    unittest.main()
