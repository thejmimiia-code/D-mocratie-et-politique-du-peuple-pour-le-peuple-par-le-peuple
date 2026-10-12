"""Instances, yoyo et fentes : rien de décoratif, rien d'inventé.

Trois familles d'exigences, aucune négociable :

* les références : toute prémisses d'une fente, tout fondement d'une instance, tout
  article d'un trajet doit se résoudre dans le dépôt ;
* l'arithmétique : les battements se comptent en jours de rigueur, les seuils se
  recalculent, et l'effet chiffré d'une fente doit tomber juste ;
* la modestie : aucune fente ne se présente comme un droit acquis, aucun score comme une
  immunité — le juge contrôle la compétence et la procédure, pas la beauté du raisonnement.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from simulateur import instances_et_dynamiques as dyn  # noqa: E402
from simulateur.constitution_analysee import ARTICLES  # noqa: E402
from simulateur.gouvernance_contrepouvoir import MECANISMES, VERROUS, seuil  # noqa: E402
from simulateur.parametres import LEVIERS  # noqa: E402
from simulateur.reglements_lois import REGISTRE_LEGAL  # noqa: E402


class TestRegistres(unittest.TestCase):
    def test_les_quatre_registres_sont_peuples(self):
        self.assertGreaterEqual(len(dyn.INSTANCES), 25)
        self.assertGreaterEqual(len(dyn.TRAJETS), 6)
        self.assertGreaterEqual(len(dyn.STRATEGIES), 12)
        self.assertGreaterEqual(len(dyn.FENTES), 10)

    def test_aucune_reference_orpheline(self):
        etat = dyn.coherence_avec_le_droit()
        self.assertTrue(etat["conforme"], etat["problemes"])
        for champ in etat["problemes"]:
            self.fail(f"problème de cohérence non traité : {champ} -> {etat['problemes'][champ]}")

    def test_les_niveaux_et_les_effets_sont_dans_le_vocabulaire_ferme(self):
        for cle, valeur in dyn.INSTANCES.items():
            with self.subTest(instance=cle):
                self.assertIn(valeur.niveau, dyn.NIVEAUX)
                for effet in valeur.effets:
                    self.assertIn(effet, dyn.EFFETS)
                self.assertTrue(valeur.mission and valeur.juge_par)
                self.assertTrue(valeur.fondement, "une instance sans fondement est une opinion")

    def test_les_leviers_filtr_ne_sont_jamais_des_verrous_perdus(self):
        # La normalisation ne doit retirer que des leviers inexistants (ils rejoignent
        # `pistes`), jamais un verrou ou un mécanisme : ce serait une référence cassée.
        etat = dyn.coherence_avec_le_droit()
        for cle, retraits in etat["filtres_appliques"].items():
            for retrait in retraits:
                with self.subTest(instance=cle, retrait=retrait):
                    self.assertTrue(retrait.startswith("levier:"), retrait)

    def test_leviers_valides_et_pistes_etanches(self):
        for cle, valeur in dyn.INSTANCES.items():
            for levier in valeur.leviers:
                self.assertIn(levier, LEVIERS)
            for piste in valeur.pistes:
                self.assertNotIn(piste, LEVIERS, "une piste promue levier doit être déclarée ailleurs")

    def test_strategies_documentees(self):
        for cle, valeur in dyn.STRATEGIES.items():
            with self.subTest(strategie=cle):
                self.assertIn(valeur.famille, dyn.FAMILLES_STRATEGIE)
                self.assertTrue(valeur.comptage, "une stratégie sans nombre qui décide est un voeu")
                self.assertTrue(valeur.deja_vue, "une stratégie doit dire qu'elle a déjà servi")
                self.assertTrue(valeur.condition)
                for numero in valeur.fondement:
                    self.assertIn(numero, ARTICLES)
                if valeur.instance:
                    self.assertIn(valeur.instance, dyn.INSTANCES)


class TestArithmetiqueDuYoyo(unittest.TestCase):
    def test_navette_ordinaire_ne_tient_pas_dans_la_fenetre_residuelle(self):
        calcul = dyn.oscillation("projet_ordinaire")
        self.assertEqual(calcul["battements"], 10)
        self.assertEqual(calcul["jours_de_rigueur"], 160)
        self.assertLess(dyn.FENETRE_RESIDUELLE_JOURS, calcul["jours_de_rigueur"])
        self.assertFalse(calcul["tenable_dans_la_fenetre"])
        self.assertLess(calcul["etapes_tenables"], calcul["battements"])
        # Retard imposable : 28 jours de Sénat + 30 jours de saisine du Conseil.
        self.assertEqual(calcul["retard_imposable"], 58)
        self.assertEqual(calcul["jours_des_verrous"], 15)
        self.assertIn("Article 42", calcul["etapes"][4]["fondement"])

    def test_le_budget_est_le_seul_calendrier_qui_tranche(self):
        calcul = dyn.oscillation("budget")
        jours = {e["acte"]: e["jours"] for e in calcul["etapes"]}
        self.assertIn("quarante jours", " ".join(e["condition"] for e in calcul["etapes"]))
        self.assertEqual(calcul["jours_de_rigueur"], sum(jours.values()))
        self.assertIn(70, jours.values())
        self.assertIn(15, jours.values())
        self.assertIn(40, jours.values())
        texte = calcul["nom"] + " " + " ".join(
            " ".join(str(e.get(k) or "") for k in ("acte", "condition", "note"))
            for e in calcul["etapes"]
        )
        self.assertIn("ordonnance", texte)
        self.assertTrue(any("soixante-dix" in e["acte"] for e in calcul["etapes"]))

    def test_asymetrie_reelle_entre_les_chambres(self):
        lignes = {a["trajet"]: a for a in dyn.asymetrie_des_chambres()}
        self.assertFalse(lignes["projet_ordinaire"]["veto_reel"])
        self.assertFalse(lignes["budget"]["veto_reel"])
        self.assertTrue(lignes["revision_congres"]["veto_reel"])
        self.assertIn("45 al. 4", lignes["projet_ordinaire"]["fondement_du_veto"])
        self.assertIn("89", lignes["revision_congres"]["fondement_du_veto"])

    def test_rapport_de_temps_ne_preduit_rien(self):
        rapport = dyn.rapport_de_temps()
        self.assertEqual(rapport["trajets"], len(dyn.TRAJETS))
        self.assertEqual(rapport["fenetre_residuelle_jours"], dyn.FENETRE_RESIDUELLE_JOURS)
        self.assertIn("rigueur", rapport["avertissement"])
        totaux = sum(v["jours"] for v in rapport["par_sens"].values())
        self.assertEqual(totaux, sum(
            b.jours for valeur in dyn.TRAJETS.values() for b in valeur.etapes
        ))

    def test_trajet_accepte_le_numero_d_article(self):
        self.assertEqual(dyn.trajet("47").cle, "budget")
        self.assertEqual(dyn.trajet("89").cle, "revision_congres")
        self.assertIsNone(dyn.trajet("trajet_inexistant"))
        self.assertIn("erreur", dyn.oscillation("inexistant"))

    def test_battement_verrouillant_n_est_pas_reversible(self):
        for cle, valeur in dyn.TRAJETS.items():
            for battement in valeur.etapes:
                with self.subTest(trajet=cle, battement=battement.cle):
                    self.assertIn(battement.sens, ("avancer", "reculer", "bloquer", "verrouiller"))
                    sortie = battement.en_dict()
                    self.assertEqual(sortie["reversible"], battement.sens != "verrouiller")
                    if battement.fondement:
                        self.assertIn(battement.fondement, ARTICLES)


class TestFentes(unittest.TestCase):
    def test_toutes_les_premisses_se_resolvent(self):
        for cle, fente in dyn.FENTES.items():
            self.assertGreaterEqual(len(fente.premisses), 2, cle)
            for premise in fente.premisses:
                with self.subTest(fente=cle, premisse=premise):
                    resolu = dyn._resoudre(premise)
                    self.assertTrue(resolu["resolu"], resolu)
                    if resolu["genre"] == "art":
                        self.assertIn(resolu["valeur"], ARTICLES)
                    elif resolu["genre"] == "reg":
                        self.assertIn(resolu["valeur"], REGISTRE_LEGAL)

    def test_une_fente_dit_porquoi_elle_n_est_pas_ecrite(self):
        for cle, fente in dyn.FENTES.items():
            with self.subTest(fente=cle):
                self.assertTrue(fente.raison_du_silence)
                self.assertTrue(fente.ce_que_ca_change)
                self.assertTrue(fente.point_de_vigilance)
                self.assertTrue(fente.condition_de_verrouillage)
                self.assertIn(fente.type, ("fente", "porte", "droit_sans_juge"))
                self.assertIn(fente.etage, dyn.ETAGES)

    def test_le_congres_se_calcule_sur_les_votants(self):
        plein = dyn.arithmetique_abstention_congres(925)
        self.assertEqual(plein["voix_requises"], 555)
        self.assertEqual(plein["economie_de_voix"], 0)
        creux = dyn.arithmetique_abstention_congres(300)
        self.assertEqual(creux["voix_requises"], 180)
        self.assertEqual(creux["economie_de_voix"], 375)
        self.assertEqual(creux["voix_requises"], seuil("congres_revision", {
            "suffrages_exprimes_congres": 300
        }))

    def test_la_censure_ne_se_calcule_pas_sur_les_votants(self):
        effet = dyn.effets_de_fente("censure_par_membres")
        self.assertEqual(effet["voix_requises"], 289)
        self.assertEqual(effet["avec_effectif_reel"], 288)
        self.assertIn("inverse", effet["lecture"])

    def test_robustesse_est_bornee_et_jamais_absolue(self):
        for cle, fente in dyn.FENTES.items():
            score = dyn.robustesse(fente)
            with self.subTest(fente=cle):
                self.assertLessEqual(score["score"], sum(dyn.POIDS_ROBUSTESSE.values()))
                self.assertGreaterEqual(score["score"], 0)
                self.assertIsNone(score["irrefutabilite"])
                self.assertIn("compétence", score["limite"])
                self.assertEqual(sum(score["details"].values()), score["score"])

    def test_les_fentes_ne_se_disent_jamais_gagnantes(self):
        for cle, fente in dyn.FENTES.items():
            texte = " ".join((fente.nom, fente.deduction, fente.ce_que_ca_change,
                              fente.condition_de_verrouillage)).lower()
            with self.subTest(fente=cle):
                for mot in ("irréfutable", "à coup sûr", "impossible à contester", "gagnée d'avance"):
                    self.assertNotIn(mot, texte)

    def test_etage_de_verrouillage_nomme_les_voies_d_attaque(self):
        for cle, fente in dyn.FENTES.items():
            etage = dyn.etage_de_verrouillage(fente)
            with self.subTest(fente=cle):
                self.assertIn(etage["etage"], dyn.ETAGES)
                self.assertTrue(etage["reversible_par"])
                self.assertEqual(dyn.QUI_ATTAQUE[etage["etage"]], tuple(etage["reversible_par"]))

    def test_une_fente_chiffree_a_un_calcul(self):
        for cle, fente in dyn.FENTES.items():
            chiffre = dyn.effets_de_fente(cle)["type"] != "non_chiffree"
            with self.subTest(fente=cle):
                self.assertEqual(bool(fente.computation), chiffre)


class TestChaineDeControle(unittest.TestCase):
    def test_le_conseil_constitutionnel_ne_se_juge_pas(self):
        chaine = dyn.qui_juge("conseil_constitutionnel")
        self.assertEqual(chaine["longueur"], 1)
        self.assertIn("aucun recours", chaine["chaine"][0]["controle_par"])
        self.assertFalse(chaine["sans_recours"])

    def test_la_loi_referendaire_n_a_aucune_instance_saisissable(self):
        boucles = {b["cle"]: b for b in dyn.boucle_de_controles()}
        self.assertTrue(boucles["loi_referendaire"]["sans_controle"])
        self.assertFalse(boucles["loi"]["sans_controle"])
        self.assertGreaterEqual(len(boucles["decret"]["voies_de_recours"]), 3)

    def test_instances_pour_article_et_saisines(self):
        self.assertIn("conseil_constitutionnel", [i["cle"] for i in dyn.instances_pour_article("61")])
        self.assertIn("gouvernement", [i["cle"] for i in dyn.instances_pour_article("49")])
        self.assertEqual(dyn.instances_pour_article("9999"), [])
        saisines = dyn.saisines_pour("soixante")
        self.assertTrue(saisines)
        self.assertTrue(all(s["instance"] == "conseil_constitutionnel" for s in saisines))
        self.assertEqual(dyn.saisines_pour("ab"), [])

    def test_strategies_et_fentes_se_filtrent(self):
        for famille in dyn.FAMILLES_STRATEGIE:
            for valeur in dyn.strategies_pour(famille=famille):
                self.assertEqual(valeur["famille"], famille)
        self.assertTrue(dyn.strategies_pour(instance_cle="conseil_constitutionnel"))
        sur_89 = dyn.fentes_pour(numero="89")
        self.assertIn("congres_par_exprimes", [f["cle"] for f in sur_89])
        self.assertEqual(dyn.fentes_pour(type_fente="droit_sans_juge")[0]["cle"],
                         "irrecevabilite_sans_recours")


class TestSortiesPartagees(unittest.TestCase):
    def test_recherche_insensible_aux_accents(self):
        avec = {r["cle"] for r in dyn.rechercher("abstention")}
        sans = {r["cle"] for r in dyn.rechercher("ABSTENTION")}
        self.assertEqual(avec, sans)
        self.assertIn("congres_par_exprimes", avec)
        self.assertIn("censure_par_membres", avec)
        self.assertEqual(dyn.rechercher("ab"), [])

    def test_synthese_serialisable_et_prudente(self):
        synthese = dyn.synthese_pour_api()
        json.dumps(synthese, ensure_ascii=False)
        self.assertEqual(len(synthese["instances"]), len(dyn.INSTANCES))
        self.assertEqual(len(synthese["fentes"]), len(dyn.FENTES))
        self.assertEqual(synthese["date_observation"], dyn.DATE_OBSERVATION)
        self.assertIn("pas un droit", synthese["avertissement"])
        self.assertIn("Conseil d'État", synthese["avertissement"])
        self.assertTrue(synthese["coherence"]["conforme"])
        for etage in synthese["etages"]:
            self.assertIn(etage, synthese["qui_attaque"])

    def test_resume_console_sans_avertissement(self):
        console = dyn.resume_console()
        self.assertIn("instances", console)
        self.assertIn(str(dyn.FENETRE_RESIDUELLE_JOURS), console)
        self.assertNotIn("⚠", console)

    def test_aucun_mecanisme_invente_dans_le_registre(self):
        for cle, valeur in dyn.INSTANCES.items():
            for blocage in valeur.peut_bloquer:
                with self.subTest(instance=cle, mecanisme=blocage):
                    self.assertIn(blocage, MECANISMES)
        for cle, valeur in dyn.TRAJETS.items():
            for blocage in valeur.blocages:
                with self.subTest(trajet=cle, mecanisme=blocage):
                    self.assertIn(blocage, MECANISMES)

    def test_les_chiffres_partages_avec_les_autres_modules(self):
        # Le module ne doit jamais redéfinir un seuil : il le demande.
        self.assertEqual(dyn.arithmetique_abstention_congres(925)["voix_requises"],
                         seuil("congres_revision"))
        effet = dyn.effets_de_fente("censure_par_membres")
        self.assertEqual(effet["voix_requises"], VERROUS["censure_voix"].seuil())


if __name__ == "__main__":
    unittest.main()
