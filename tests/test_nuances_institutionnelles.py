# -*- coding: utf-8 -*-
"""Les réglages institutionnels doivent être simulables, pas décoratifs.

Contrats testés ici :
1. tout levier `reglage_*` du catalogue a une règle de recalcul déclarée ;
2. au statu quo, rien ne bouge : seuils, délais, fentes et indices rendent exactement
   les chiffres des modules de droit ;
3. les chiffres recalculés sont de l'arithmétique, pas de la prose (289 → 231 voix,
   40 → 20 jours, fenêtre 150 → 75 jours) ;
4. une fente verrouillée n'est pas réfutée : son score baisse, son `irrefutabilite`
   reste vide ;
5. aucune cible ne pointe vers un identifiant inexistant.
"""

import unittest

from simulateur.gouvernance_contrepouvoir import VERROUS, seuil
from simulateur.instances_et_dynamiques import FENTES, oscillation, robustesse
from simulateur.nuances_institutionnelles import (
    INDICES,
    NIVEAUX,
    REGLAGES,
    coherence_nuances,
    contexte_institutionnel,
    etat_des_verrous,
    delais_ajustes,
    fentes_recalculees,
    indices_nuances,
    normaliser,
    nuances_pour_article,
    nuances_pour_levier,
    reglages_catalogue,
    resume_console,
    seuils_ajustes,
    synthese_pour_api,
    tableau_des_niveaux,
    taux,
)
from simulateur.parametres import LEVIERS, PRESETS
from simulateur.reglements_lois import REGISTRE_LEGAL


class TestReglagesDeclares(unittest.TestCase):
    """Chaque curseur institutionnel doit avoir une règle appliquée par le moteur."""

    def test_volume_de_reglages(self):
        catalogue = reglages_catalogue()
        self.assertGreaterEqual(len(catalogue), 40)
        self.assertTrue(all(cle.startswith("reglage_") for cle in catalogue))

    def test_chaque_reglage_a_une_regle_et_une_cible(self):
        for cle in reglages_catalogue():
            with self.subTest(reglage=cle):
                reglage = REGLAGES[cle]
                self.assertIn(reglage["niveau"], NIVEAUX)
                self.assertTrue(reglage["regle"].strip())
                self.assertTrue(reglage["effet"].strip())
                self.assertTrue(reglage["cibles"], "aucune cible de recalcul")

    def test_coherence_interne_est_nette(self):
        coherence = coherence_nuances()
        self.assertEqual(coherence["reglages_sans_regle"], [])
        self.assertEqual(coherence["reglages_inconnus"], [])
        self.assertEqual(coherence["cibles_inconnues"], [])
        self.assertEqual(coherence["articles_hors_registre"], [])
        self.assertEqual(coherence["indices_anormaux"], [])
        self.assertEqual(coherence["apports_sans_reglage"], [])
        self.assertEqual(coherence["fentes_inaccessibles_d_un_reglage"], [])

    def test_articles_cites_existent_dans_le_registre(self):
        for cle in reglages_catalogue():
            for identifiant in LEVIERS[cle].articles:
                self.assertIn(identifiant, REGISTRE_LEGAL, f"{cle} → {identifiant}")

    def test_le_statu_quo_vaut_zero(self):
        """Un réglage à sa valeur par défaut ne doit rien imposer du tout."""
        for cle in reglages_catalogue():
            levier = LEVIERS[cle]
            with self.subTest(reglage=cle):
                self.assertEqual(levier.defaut, 0.0)
                self.assertEqual(taux(cle, normaliser({})), 0.0)

    def test_tous_les_niveaux_sont_peuples(self):
        repartition = {ligne["niveau"]: ligne["nombre_reglages"] for ligne in tableau_des_niveaux()}
        self.assertEqual(set(repartition), set(NIVEAUX))
        for niveau, nombre in repartition.items():
            self.assertGreaterEqual(nombre, 2, f"niveau {niveau} sous-peuplé")


class TestNeutraliteAuStatuQuo(unittest.TestCase):
    """Vecteur vide = sorties du droit, au chiffre près."""

    def test_seuils_identiques_au_droit(self):
        seuils = seuils_ajustes()
        for cle, ligne in seuils.items():
            with self.subTest(seuil=cle):
                self.assertEqual(ligne["regle"], ligne["statu_quo"])
                self.assertEqual(ligne["ecart"], 0)
                self.assertEqual(ligne["reglages_appliques"], [])
        self.assertEqual(seuils["censure_voix"]["statu_quo"], int(seuil("censure_voix")))
        self.assertEqual(seuils["saisine_conseil_signatures"]["statu_quo"], 60)

    def test_delais_identiques_a_oscillation(self):
        delais = delais_ajustes()
        self.assertTrue(delais["jours_coherents_avec_oscillation"])
        self.assertEqual(delais["fenetre_residuelle_reglee"], delais["fenetre_residuelle_statu_quo"])
        for ligne in delais["trajets"]:
            with self.subTest(trajet=ligne["cle"]):
                reference = oscillation(ligne["cle"])
                self.assertEqual(ligne["jours_de_rigueur_regles"], reference["jours_de_rigueur"])
                self.assertEqual(ligne["jours_de_rigueur_statu_quo"], reference["jours_de_rigueur"])
                self.assertEqual(ligne["tenable_dans_la_fenetre"], reference["tenable_dans_la_fenetre"])

    def test_fentes_inchangees(self):
        for ligne in fentes_recalculees():
            with self.subTest(fente=ligne["cle"]):
                self.assertEqual(ligne["degre_neutralise"], 0.0)
                self.assertFalse(ligne["neutralisee"])
                self.assertEqual(ligne["robustesse_reglee"], ligne["robustesse_statu_quo"])
                self.assertEqual(ligne["robustesse_statu_quo"], int(robustesse(FENTES[ligne["cle"]])["score"]))

    def test_indices_tous_a_cinquante(self):
        indices = indices_nuances()
        self.assertEqual(set(indices), set(INDICES))
        for cle, indice in indices.items():
            with self.subTest(indice=cle):
                self.assertEqual(indice["valeur"], 50.0)
                self.assertEqual(indice["composants"], [])

    def test_console_dit_le_statu_quo(self):
        console = resume_console()
        self.assertIn("au statu quo", console)
        self.assertIn("0 déplacés", console)
        for mot in ("irréfragable", "garanti", "infaillible"):
            self.assertNotIn(mot, console)


class TestSeuilsRecalcules(unittest.TestCase):
    """L'arithmétique des seuils, réglage par réglage."""

    def test_assiette_de_la_censure(self):
        self.assertEqual(seuils_ajustes()["censure_voix"]["regle"], 289)
        sur_exprimes = seuils_ajustes({"reglage_censure_assiette": 1.0})["censure_voix"]
        self.assertEqual(sur_exprimes["regle"], 231)
        self.assertLess(sur_exprimes["regle"], 289)
        avec_quorum = seuils_ajustes({"reglage_censure_assiette": 2.0})["censure_voix"]
        self.assertEqual(avec_quorum["quorum_votants"], 347)
        self.assertIn("quorum", avec_quorum["note"])
        self.assertIn("reglage_censure_assiette", sur_exprimes["reglages_appliques"])

    def test_delais_de_censure_et_de_motion(self):
        seuils = seuils_ajustes({"reglage_delai_motion_censure": 5.0,
                                 "reglage_delai_motion_49_3": 48.0})
        self.assertEqual(seuils["censure_delai"]["regle"], 48 + 5 * 24)
        self.assertEqual(seuils["49_3_delai_motion"]["regle"], 24 + 48)

    def test_congres_assiette_et_quorum(self):
        congres = seuils_ajustes()["congres_revision"]
        self.assertEqual(congres["statu_quo"], 555)
        self.assertEqual(congres["scenarios_abstention"]["700"]["suffrages_exprimes"], 420)
        self.assertEqual(congres["scenarios_abstention"]["700"]["membres_composant"], 555)
        sur_membres = seuils_ajustes({"reglage_congres_assiette_membres": 1.0})["congres_revision"]
        self.assertIn("fixe", sur_membres["note"])
        quorum = seuils_ajustes({"reglage_congres_quorum": 50.0})["congres_revision"]
        self.assertEqual(quorum["quorum_votants"], 463)
        self.assertIn("reglage_congres_quorum", quorum["reglages_appliques"])

    def test_seuil_de_saisine_du_conseil(self):
        attendus = {0.0: 60, 1.0: 40, 2.0: 15, 3.0: 0}
        for valeur, signatures in attendus.items():
            with self.subTest(valeur=valeur):
                ligne = seuils_ajustes({"reglage_seuil_saisine_conseil": valeur})["saisine_conseil_signatures"]
                self.assertEqual(ligne["regle"], signatures)

    def test_calendrier_budgetaire(self):
        seuils = seuils_ajustes({"reglage_delai_budget_retraite": 20.0,
                                 "reglage_delai_senat_budget": 15.0})
        self.assertEqual(seuils["budget_an_delai"]["regle"], 20)
        self.assertEqual(seuils["budget_senat_delai"]["regle"], 30)
        self.assertEqual(seuils["budget_delai_total"]["regle"], 65)
        # hors bornes : le curseur est écrêté à sa valeur maximale, pas la formule
        bute = seuils_ajustes({"reglage_delai_budget_retraite": 100.0})
        self.assertEqual(bute["budget_an_delai"]["regle"], 20, "l'écretage aux bornes doit s'appliquer")
        self.assertEqual(normaliser({"reglage_delai_budget_retraite": -8.0})["reglage_delai_budget_retraite"], 0.0)
        self.assertGreaterEqual(bute["budget_delai_total"]["regle"], 20)

    def test_seuil_de_groupes_et_plafond_de_49_3(self):
        seuils = seuils_ajustes({"reglage_seuil_groupes": 10.0, "reglage_49_3_interdiction": 1.0})
        self.assertEqual(seuils["seuil_groupe_assemblee_nationale"]["regle"], 5)
        self.assertEqual(seuils["49_3_plafond_texte"]["regle"], 0)
        self.assertEqual(seuils["49_3_plafond_texte"]["statu_quo"], int(seuil("49_3_plafond_texte")))

    def test_duree_maximale_d_exception(self):
        ligne = seuils_ajustes({"reglage_plafond_etat_urgence": 12.0})["etat_urgence_duree_max_mois"]
        self.assertEqual(ligne["regle"], 12)
        self.assertIn("plein droit", ligne["note"])
        self.assertIn("prorogations", seuils_ajustes()["etat_urgence_duree_max_mois"]["note"])

    def test_tous_les_verrous_reglables_sont_des_verrous_du_registre(self):
        seuils = seuils_ajustes()
        derives = {"seuil_groupe_assemblee_nationale", "etat_urgence_duree_max_mois"}
        for cle in seuils:
            if cle in derives:
                continue
            with self.subTest(verrou=cle):
                self.assertIn(cle, VERROUS)


class TestDelaisEtFenetre(unittest.TestCase):
    """Le temps réglé : ce qui tient dans la fenêtre, ce qui ne tient plus."""

    def _trajet(self, cle, parametres=None):
        return next(ligne for ligne in delais_ajustes(parametres)["trajets"] if ligne["cle"] == cle)

    def test_part_parlementaire_reduit_la_fenetre(self):
        regle = delais_ajustes({"reglage_ordre_du_jour_partage": 50.0})
        self.assertEqual(regle["fenetre_residuelle_reglee"], 75)
        self.assertFalse(self._trajet("budget", {"reglage_ordre_du_jour_partage": 50.0})["tenable_dans_la_fenetre"])
        self.assertTrue(self._trajet("budget")["tenable_dans_la_fenetre"])

    def test_retirer_des_jours_budget_rapetisse_le_trajet(self):
        ligne = self._trajet("budget", {"reglage_delai_budget_retraite": 12.0})
        self.assertEqual(ligne["jours_de_rigueur_regles"], 136)
        etape = next(e for e in ligne["etapes"] if e["cle"] == "an_vote")
        self.assertEqual(etape["jours_regles"], 28)
        self.assertIn("reglage_delai_budget_retraite", etape["reglages_appliques"])

    def test_deux_lectures_supplementaires_sortent_du_calendrier(self):
        ligne = self._trajet("projet_ordinaire", {"reglage_chambre_tiree_au_sort": 120.0,
                                                 "reglage_convention_veto_suspensif": 1.0})
        etape = next(e for e in ligne["etapes"] if e["cle"] == "nouvelle_lecture")
        self.assertEqual(etape["jours_regles"], 140)
        self.assertFalse(ligne["tenable_dans_la_fenetre"])
        self.assertGreater(ligne["jours_de_rigueur_regles"], ligne["jours_de_rigueur_statu_quo"])

    def test_audit_prealable_allonge_le_depart(self):
        ligne = self._trajet("projet_ordinaire", {"reglage_audit_obligatoire_prealable": 1.0})
        etape = next(e for e in ligne["etapes"] if e["cle"] == "conseil_etat_avis")
        self.assertEqual(etape["jours_regles"], 45)

    def test_delai_de_motion_alonge_le_yoyo(self):
        ligne = self._trajet("renversement", {"reglage_delai_motion_censure": 4.0})
        self.assertEqual(ligne["jours_de_rigueur_regles"], 6)
        self.assertEqual(ligne["retard_imposable"], oscillation("renversement")["retard_imposable"])

    def test_interdire_le_49_3_supprime_les_textes_forcables(self):
        self.assertEqual(delais_ajustes()["textes_forcables_par_session"], 1)
        self.assertEqual(delais_ajustes({"reglage_49_3_interdiction": 1.0})["textes_forcables_par_session"], 0)


class TestFentesVerrouillees(unittest.TestCase):
    """Un réglage ferme une fente : il ne la réfute pas."""

    def _fente(self, cle, parametres=None):
        return next(ligne for ligne in fentes_recalculees(parametres) if ligne["cle"] == cle)

    def test_fermetures_franches(self):
        for fente, levier, valeur in (
            ("censure_par_membres", "reglage_censure_assiette", 2.0),
            ("referendum_sans_juge", "reglage_controle_loi_referendaire", 1.0),
            ("irrecevabilite_sans_recours", "reglage_recours_irrecevabilite", 1.0),
        ):
            with self.subTest(fente=fente):
                ligne = self._fente(fente, {levier: valeur})
                self.assertTrue(ligne["neutralisee"], ligne["note"])
                self.assertEqual(ligne["robustesse_reglee"], 0)
                self.assertEqual(ligne["degre_neutralise"], 1.0)
                self.assertIsNone(ligne["irrefutabilite"])
                self.assertIn("verrouillée", ligne["note"])

    def test_verrouillages_partiels(self):
        ligne = self._fente("defossilisation_sans_vote", {"reglage_vote_nominal_obligatoire": 1.0})
        self.assertFalse(ligne["neutralisee"])
        self.assertGreater(ligne["robustesse_reglee"], 0)
        self.assertLess(ligne["robustesse_reglee"], ligne["robustesse_statu_quo"])
        cumule = self._fente("defossilisation_sans_vote", {"reglage_vote_nominal_obligatoire": 1.0,
                                                            "reglage_registre_amendements": 1.0})
        self.assertLess(cumule["robustesse_reglee"], ligne["robustesse_reglee"])
        self.assertEqual(len(cumule["reglages_appliques"]), 2)

    def test_une_fente_augmente_de_vitesse_pas_de_score(self):
        ligne = self._fente("petition_dans_le_reglement", {"reglage_petition_locale_seuil": 8.0})
        self.assertLess(ligne["robustesse_reglee"], ligne["robustesse_statu_quo"])
        self.assertIn("reglage_petition_locale_seuil", ligne["reglages_appliques"])
        self.assertTrue(ligne["condition_de_verrouillage"].strip())

    def test_treize_fentes_toutes_recalculees(self):
        lignes = fentes_recalculees({"reglage_49_3_interdiction": 1.0})
        self.assertEqual(len(lignes), len(FENTES))
        self.assertEqual({ligne["cle"] for ligne in lignes}, set(FENTES))
        self.assertTrue(all(ligne["robustesse_reglee"] <= ligne["robustesse_statu_quo"] for ligne in lignes))

    def test_arithmetique_exposee_dans_les_fentes_chiffrees(self):
        congres = self._fente("congres_par_exprimes", {"reglage_congres_quorum": 60.0})
        self.assertEqual(congres["lecture_reglee"]["statu_quo"], "555 voix sur 925 suffrages exprimés")
        self.assertEqual(congres["lecture_reglee"]["scenarios"]["800"]["economie_de_voix"], 75)
        censure = self._fente("censure_par_membres", {"reglage_censure_assiette": 1.0})
        self.assertIn("231 voix", censure["lecture_reglee"]["regle"])


class TestIndices(unittest.TestCase):
    """Les indices sont des amplitudes relatives, pas des notes de mérite."""

    def test_six_à_huit_indices(self):
        self.assertGreaterEqual(len(INDICES), 7)
        self.assertEqual(set(indices_nuances()), set(INDICES))

    def test_monotone_et_bornee(self):
        base = indices_nuances()
        for valeur in (0.0, 10.0, 25.0, 50.0):
            indices = indices_nuances({"reglage_ordre_du_jour_partage": valeur})
            self.assertGreaterEqual(indices["capacite_de_blocage_parlementaire"]["valeur"],
                                    base["capacite_de_blocage_parlementaire"]["valeur"])
            self.assertLessEqual(indices["vitesse_legislative"]["valeur"],
                                 base["vitesse_legislative"]["valeur"])
        for indice in indices.values():
            self.assertGreaterEqual(indice["valeur"], 0.0)
            self.assertLessEqual(indice["valeur"], 100.0)

    def test_borne_appliquee_quand_saature(self):
        indices = indices_nuances({cle: LEVIERS[cle].bornes[1] for cle in reglages_catalogue()})
        self.assertEqual(indices["vitesse_legislative"]["valeur"], 0.0)
        self.assertTrue(indices["vitesse_legislative"]["borne_appliquee"])
        self.assertLess(indices["vitesse_legislative"]["brut"], -50.0)
        self.assertEqual(indices["controle_juridictionnel"]["valeur"], 100.0)

    def test_composantes_traçables(self):
        indices = indices_nuances({"reglage_parquet_independant": 1.0, "reglage_appel_qpc": 1.0})
        controle = indices["controle_juridictionnel"]
        self.assertEqual({c["reglage"] for c in controle["composants"]},
                         {"reglage_parquet_independant", "reglage_appel_qpc"})
        for composante in controle["composants"]:
            self.assertIn(composante["reglage"], REGLAGES)
            self.assertTrue(composante["regle"].strip())
        self.assertGreater(controle["valeur"], 50.0)
        self.assertIn("parquet", controle["lecture"])

    def test_lectures_redigees(self):
        indices = indices_nuances({"reglage_revocation_elue": 1.0})
        self.assertIn("augmente", indices["capacite_de_renversement"]["lecture"])
        self.assertIn("état du droit", indices_nuances()["redevabilite"]["lecture"])


class TestCroisements(unittest.TestCase):
    """Les réglages voyagent avec le reste du simulateur : bulles, preset, articles."""

    def test_fiche_de_reglage(self):
        fiche = nuances_pour_levier("reglage_censure_assiette")
        self.assertEqual(fiche["niveau"], "Constitutionnel")
        self.assertEqual([t["verrou"] for t in fiche["touchant"]], ["censure_voix"])
        self.assertIn("CONST_ART_49", fiche["articles"])
        self.assertTrue(fiche["indices_affectes"])
        self.assertTrue(fiche["effets_domaines"])
        self.assertTrue(fiche["bornes"][1] >= 2.0)

    def test_fiche_d_un_reglage_inconnu(self):
        self.assertEqual(nuances_pour_levier("pas_un_reglage")["erreur"], "levier inconnu")

    def test_recroisement_par_article(self):
        lignes = nuances_pour_article("CONST_ART_49")
        cles = {ligne["reglage"] for ligne in lignes}
        self.assertIn("reglage_49_3_interdiction", cles)
        self.assertIn("reglage_censure_assiette", cles)
        for ligne in lignes:
            self.assertIn("CONST_ART_49", LEVIERS[ligne["reglage"]].articles)

    def test_le_preset_de_refondation_deplace_des_reglages(self):
        synthese = synthese_pour_api(PRESETS["refondation_democratique"]["parametres"])
        deplaces = synthese["resume"]["reglages_deplaces"]
        self.assertGreaterEqual(deplaces, 5)
        self.assertGreater(synthese["indices"]["redevabilite"]["valeur"], 50.0)
        self.assertIn("irrecevabilite_sans_recours", synthese["resume"]["fentes_neutralisees"])

    def test_letat_des_verrous_partage_le_registre_sans_en_rien_perdre(self):
        """`etat_des_verrous` est la source du bloc « verrous » de la page : il doit
        couvrir les 38 verrous, une seule fois chacun, sans en inventer."""
        for vecteur in ({}, {"reglage_censure_assiette": 1},
                        {cle: 1.0 for cle in reglages_catalogue()}):
            etat = etat_des_verrous(vecteur)
            with self.subTest(reglages=len(vecteur)):
                toutes = [o["cle"] for groupe in ("touches", "intacts", "hors_reglage")
                          for o in etat[groupe]]
                self.assertEqual(etat["total"], len(VERROUS))
                self.assertEqual(sorted(toutes), sorted(VERROUS))
                self.assertEqual(len(toutes), len(set(toutes)))
                for objet in toutes:
                    self.assertTrue(VERROUS[objet].nom)
                for objet in etat["hors_reglage"]:
                    self.assertTrue(objet["explication"],
                                    f"verrou hors réglage sans explication : {objet['cle']}")
                    # Aucun seuil n'est recalculé pour lui : c'est justement ce que
                    # « hors réglage » veut dire. Les réglages listés ici ne sont que
                    # ceux qui mentionnent la règle, pour que la page l'explique.
                    self.assertNotIn("seuil_regule", objet)
                    self.assertNotIn("seuil_statu_quo", objet)
                    for levier in objet["reglages"]:
                        self.assertIn(levier, LEVIERS)
                for ligne in etat["touches"]:
                    self.assertTrue(ligne["reglages"])
                    for levier in ligne["reglages"]:
                        self.assertIn(levier, LEVIERS)

    def test_les_verrous_neutralises_sont_signales_comme_avertissements(self):
        etat = etat_des_verrous({"reglage_censure_assiette": 1})
        avertissements = {ligne["cle"]: ligne for ligne in etat["avertissements"]}
        self.assertIn("censure_par_membres", avertissements)
        self.assertEqual(avertissements["censure_par_membres"]["reglages"],
                         ["reglage_censure_assiette"])
        self.assertTrue(avertissements["censure_par_membres"]["article"])
        self.assertEqual(etat_des_verrous({})["avertissements"], [])

    def test_contexte_serialisable_et_borne(self):
        contexte = contexte_institutionnel({cle: 1.0 for cle in reglages_catalogue()})
        self.assertEqual(set(contexte), {"reglages", "seuils", "delais", "fentes", "indices",
                                         "niveaux", "strates", "verrous", "resume"})
        self.assertEqual([ligne["strate"] for ligne in contexte["strates"]], [1, 2, 3, 4, 5])
        self.assertTrue(all(ligne["reglages"] for ligne in contexte["strates"]))
        for ligne in contexte["reglages"].values():
            self.assertTrue(ligne["strates"])
        self.assertEqual(len(contexte["reglages"]), len(reglages_catalogue()))
        for cle, ligne in contexte["reglages"].items():
            with self.subTest(reglage=cle):
                self.assertTrue(ligne["deplace"] or ligne["valeur"] == LEVIERS[cle].defaut)
                self.assertIn(ligne["type"], ("curseur", "choix", "interrupteur", "cible"))
                self.assertGreaterEqual(ligne["taux"], 0.0)
                self.assertLessEqual(ligne["taux"], 1.0)

    def test_entree_de_console_apres_reglage(self):
        console = resume_console({"reglage_censure_assiette": 2.0})
        self.assertIn("censure", console)
        self.assertIn("verrouillées", console)
        self.assertIn("referendum", resume_console({"reglage_controle_loi_referendaire": 1.0}))


if __name__ == "__main__":
    unittest.main()
