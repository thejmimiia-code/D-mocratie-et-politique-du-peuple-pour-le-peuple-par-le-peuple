"""L'arithmetique des contre-pouvoirs : les seuils doivent tomber juste.

Un seuil faux d'une voix change le verdict d'une censure. Ces tests recalculent a la
main les nombres que le module affiche, et verifient qu'aucun mecanisme n'est
decorate (chacun doit etre rattache a un article fiche).
"""

from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from simulateur.constitution_analysee import ARTICLES  # noqa: E402
from simulateur.gouvernance_contrepouvoir import (  # noqa: E402
    DATE_ETAT_ASSEMBLEES,
    ELECTEURS_INSCRITS,
    FAMILLES,
    MECANISMES,
    SIEGES_POURVUS,
    SIEGES_THEORIQUES,
    VERROUS,
    arithmetique_assemblee,
    blocages_possibles,
    chaine_de_reaction,
    coalition_necessaire,
    coherence_avec_les_fiches,
    diagnostic,
    rechercher,
    resume_console,
    seuil,
    synthese_pour_api,
    tableau_des_seuils,
)


class TestVerrousChiffres(unittest.TestCase):
    def test_article_49_censure(self):
        self.assertEqual(seuil("censure_signatures"), 58)      # 577 / 10
        self.assertEqual(seuil("censure_voix"), 289)            # majorite des membres
        self.assertEqual(VERROUS["censure_delai"].seuil(), 48)  # heures
        self.assertEqual(VERROUS["49_3_delai_motion"].seuil(), 24)
        self.assertEqual(VERROUS["censure_plafond_motions"].seuil(), 3)

    def test_article_11_rip(self):
        self.assertEqual(seuil("rip_signatures_parlement"), 185)   # un cinquieme de 925
        self.assertEqual(seuil("rip_signatures_electeurs"), math.ceil(ELECTEURS_INSCRITS / 10))
        self.assertGreater(seuil("rip_signatures_electeurs"), 4_000_000)

    def test_congres_et_haute_cour(self):
        # 3/5 des suffrages exprimes sur 925 sieges : 555, pas 556.
        self.assertEqual(seuil("congres_revision"), 555)
        self.assertEqual(seuil("haute_cour_assemblees"), 385)   # 2/3 de 577
        self.assertEqual(seuil("haute_cour_destitution"), 617)  # 2/3 de 925

    def test_delais_budgetaires(self):
        self.assertEqual(VERROUS["budget_an_delai"].seuil(), 40)
        self.assertEqual(VERROUS["budget_senat_delai"].seuil(), 15)
        self.assertEqual(VERROUS["budget_delai_total"].seuil(), 70)
        self.assertEqual(VERROUS["plfss_delai_total"].seuil(), 50)

    def test_regimes_d_exception(self):
        for cle in ("etat_urgence_delai_parlement", "etat_siege_delai_parlement"):
            with self.subTest(verrou=cle):
                self.assertEqual(VERROUS[cle].seuil(), 12)
                self.assertEqual(VERROUS[cle].sens, "ne_pas_depasser")
        self.assertEqual(VERROUS["dissolution_carence"].seuil(), 365)
        self.assertEqual(VERROUS["vacance_delai_scrutin"].seuil(), 35)

    def test_un_verrou_sans_assiette_ne_s_invente_pas_de_nombre(self):
        for cle, verrou in VERROUS.items():
            if verrou.regle == "fixe" and verrou.valeur == 0:
                with self.subTest(verrou=cle):
                    self.assertIn(verrou.assiette, ("regle", "occurrences", "electeurs_inscrits"))
                    self.assertEqual(verrou.seuil(), 0)

    def test_le_siege_vacant_ne_change_pas_le_seuil_de_censure(self):
        # L'article 49 parle des « membres composant » l'Assemblee : l'assiette est
        # l'effectif legal (577), donc 289 voix, meme avec trois sieges vacants.
        self.assertEqual(seuil("censure_voix"), 289)
        avec_effectif_reel = {"membres_assemblee_nationale": SIEGES_POURVUS["assemblee_nationale"]}
        self.assertEqual(
            seuil("censure_voix", avec_effectif_reel), 288,
            "le calcul doit rester sensible a l'assiette fournie : c'est ce qui permet "
            "de simuler une assemblee incomplete ou recomposee,",
        )


class TestMechanismes(unittest.TestCase):
    def test_tables_non_vides_et_familles_declarees(self):
        self.assertGreaterEqual(len(MECANISMES), 25)
        self.assertGreaterEqual(len(VERROUS), 30)
        for cle, mecanisme in MECANISMES.items():
            with self.subTest(mecanisme=cle):
                self.assertIn(mecanisme.famille, FAMILLES)
                self.assertTrue(mecanisme.nom and mecanisme.resume)
                self.assertTrue(mecanisme.acteurs, "un mecanisme sans acteur n'est pas une manœuvre")
                self.assertTrue(mecanisme.observation, "un mecanisme doit dire ce qu'on en a vu")
                self.assertTrue(mecanisme.articles, "un mecanisme doit etre ancre dans un article")

    def test_coherence_avec_les_fiches_constitutionnelles(self):
        etat = coherence_avec_les_fiches()
        self.assertTrue(etat["conforme"], etat)
        self.assertEqual(etat["mecanismes_orphelins"], [])
        self.assertEqual(etat["articles_inconnus"], [])
        self.assertEqual(etat["verrous_inexistants"], [])

    def test_les_chaines_renvoient_a_des_noms_explicites(self):
        # Un empechement peut etre un mecanisme du registre (resolu) ou un obstacle
        # decrit en toutes lettres par la fiche : dans les deux cas, le nom doit etre
        # lisible et, quand il designe un mecanisme, celui-ci doit exister.
        for cle, mecanisme in MECANISMES.items():
            for obstacle in mecanisme.empeche_par:
                with self.subTest(mecanisme=cle, empeche=obstacle):
                    self.assertRegex(obstacle, r"^[a-z0-9_]{3,}$")
            for declenche in mecanisme.declenche:
                with self.subTest(mecanisme=cle, declenche=declenche):
                    self.assertRegex(declenche, r"^[a-z0-9_]{3,}$")
        resolus = [b["cle"] for b in blocages_possibles("motion_censure") if b["cle"] in MECANISMES]
        self.assertTrue(resolus, "une manœuvre doit au moins pouvoir être bloquée par une autre")

    def test_blocages_et_chaines(self):
        blocages = {b["cle"] for b in blocages_possibles("article_49_3")}
        self.assertIn("motion_censure", blocages)
        self.assertEqual(blocages_possibles("inexistant"), [])
        chaine = [x["cle"] for x in chaine_de_reaction("motion_censure")]
        self.assertEqual(chaine[0], "motion_censure")
        self.assertIn("dissolution", chaine, "une censure appelle la question de la dissolution")
        self.assertEqual(chaine_de_reaction("inexistant"), [])

    def test_diagnostic_serialisable(self):
        etat = diagnostic()
        json.dumps(etat, ensure_ascii=False)
        self.assertEqual(etat["date_etat"], DATE_ETAT_ASSEMBLEES)
        lignes = {ligne["cle"]: ligne for ligne in etat["mecanismes"]}
        self.assertIn("motion_censure", lignes)
        seuils = {s["cle"]: s["seuil"] for s in lignes["motion_censure"]["seuils"]}
        self.assertEqual(seuils["censure_voix"], 289)
        self.assertEqual(seuils["censure_signatures"], 58)
        self.assertTrue(lignes["motion_censure"]["bloqueurs"])


class TestArithmetiqueDesAssemblees(unittest.TestCase):
    def test_effectifs_octobre_2026(self):
        an = arithmetique_assemblee("assemblee_nationale")
        self.assertEqual(an["sieges"], 577)
        self.assertEqual(an["pourvus"], 574)
        self.assertEqual(an["majorite_absolue"], 289)
        self.assertEqual(an["majorite_qualifiee_3_5"], 347)
        self.assertEqual(an["majorite_2_3"], 385)
        self.assertEqual(an["dixieme"], 58)
        self.assertEqual(sum(an["groupes"].values()), 574, "la somme des groupes doit rendre l'effectif pourvu")
        senat = arithmetique_assemblee("senat")
        self.assertEqual(senat["majorite_absolue"], 175)
        self.assertEqual(sum(senat["groupes"].values()), 348)
        self.assertEqual(arithmetique_assemblee("inconnue"), {})

    def test_coalition_necessaire_au_pire(self):
        rapport = coalition_necessaire("motion_censure")
        self.assertEqual(rapport["voix_requises"], 289)
        self.assertTrue(rapport["suffit"])
        self.assertIn("arithmétique", rapport["avertissement"])
        self.assertEqual(coalition_necessaire("inexistant"), {"erreur": "mécanisme inconnu"})

    def test_sieges_theoriques_et_pourvus(self):
        self.assertEqual(SIEGES_THEORIQUES["congres"], 925)
        self.assertEqual(SIEGES_POURVUS["congres"], 922)


class TestSortiesPartagees(unittest.TestCase):
    def test_recherche(self):
        self.assertTrue(rechercher("subsidiarite") or rechercher("subsidia"))
        self.assertEqual(rechercher("ab"), [])
        for resultat in rechercher("censure"):
            self.assertIn(resultat["type"], ("mecanisme", "verrou"))

    def test_tableau_des_seuils_et_synthese(self):
        tableau = tableau_des_seuils()
        self.assertEqual(set(tableau), set(VERROUS))
        synthese = synthese_pour_api()
        json.dumps(synthese, ensure_ascii=False)
        self.assertEqual(len(synthese["mecanismes"]), len(MECANISMES))
        self.assertTrue(synthese["avertissement"])
        for famille in synthese["familles"]:
            self.assertIn(famille["nom"], FAMILLES)

    def test_resume_console_sans_incoherence(self):
        console = resume_console()
        self.assertIn("mécanismes", console)
        self.assertNotIn("Incohérences", console)

    def test_le_module_ne_predit_pas_l_issue(self):
        for cle, mecanisme in MECANISMES.items():
            with self.subTest(mecanisme=cle):
                self.assertNotIn("garanti", mecanisme.effet_modele.lower())

    def test_tous_les_articles_cites_existent(self):
        for mecanisme in MECANISMES.values():
            for numero in mecanisme.articles:
                self.assertIn(numero, ARTICLES)


if __name__ == "__main__":
    unittest.main()
