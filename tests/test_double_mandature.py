"""
tests/test_double_mandature.py — R&D « deux mandatures consécutives » (2027-2037).

Protège la couche de profondeur temporelle du simulateur
(docs/RD_DOUBLE_MANDATURE.md) : neutralité des scénarios quinquennaux,
scénarios décennaux, leviers dédiés, dynamique du moteur et garde-fous.
"""

import unittest

from simulateur.cli import CATALOGUE_SCENARIOS
from simulateur.donnees_live import construire_contexte
from simulateur.model import DecisionPolitique
from simulateur.moteur import (
    DELAI_MATURITE_INVESTISSEMENTS,
    MoteurSimulationSystemique,
)
from simulateur.moteur_parametrique import simuler
from simulateur.parametres import LEVIERS, PRESETS, normaliser
from simulateur.scenarios import (
    get_scenario_alternance_2032,
    get_scenario_double_mandature,
    get_scenario_mandature_5_ans,
    get_scenario_statut_quo,
)
from simulateur.seuils import GARDE_FOUS


def _executer(decisions):
    moteur = MoteurSimulationSystemique()
    resultats = [moteur.appliquer_etape(d) for d in decisions]
    return moteur, resultats


class TestNeutraliteDesNouveauxChamps(unittest.TestCase):
    """Les scénarios existants ne doivent pas bouger d'un iota."""

    def test_statut_quo_identique_au_calibrage_documente(self):
        _, resultats = _executer(get_scenario_statut_quo())
        self.assertEqual(len(resultats), 5)
        final = resultats[-1]
        # Champs de profondeur temporelle neutres par défaut.
        self.assertEqual(final.usure_politique_pts, 0.0)
        self.assertFalse(final.irreversibilite_reformes_active)
        self.assertEqual(final.investissements_matures_mde, 0.0)
        self.assertFalse(any("[Deux mandatures]" in c for r in resultats for c in r.commentaires))

    def test_mandature_quinquennale_inchangee(self):
        _, resultats = _executer(get_scenario_mandature_5_ans())
        final = resultats[-1]
        # Valeurs publiées dans le README (section V, exécution 2d36d3a).
        self.assertEqual(final.ratio_deficit_pib, -0.73)
        self.assertEqual(round(final.ratio_dette_pib, 1), 119.1)
        self.assertEqual(final.taux_oat_pct, 3.35)
        self.assertEqual(round(final.spread_bund_bps, 1), 47.2)
        self.assertEqual(final.usure_politique_pts, 0.0)
        self.assertEqual(final.investissements_matures_mde, 0.0)


class TestScenariosDecennaux(unittest.TestCase):
    """Les deux scénarios de la période de dix ans sont complets et cohérents."""

    def test_double_mandature_couvre_dix_exercices(self):
        scenario = get_scenario_double_mandature()
        self.assertEqual(len(scenario), 10)
        self.assertEqual([d.annee for d in scenario], list(range(1, 11)))
        # Les deux années électorales majeures sont modélisées (2032 et 2037).
        electorales = [d.annee for d in scenario if d.annee_electorale_majeure]
        self.assertEqual(electorales, [5, 10])
        # Le verrou constitutionnel n'arrive qu'avec la mandature 2.
        self.assertFalse(scenario[4].verrouillage_irreversibilite)
        self.assertTrue(all(d.verrouillage_irreversibilite for d in scenario[5:]))
        # Le second dividende de la dette est réinvesti en mandature 2.
        self.assertTrue(any(d.reinvestissement_dividende_dette_mde > 0 for d in scenario[5:]))
        # L'usure du capital politique croît au fil de la seconde mandature.
        usures = [d.usure_politique_pts for d in scenario[5:]]
        self.assertEqual(usures, sorted(usures))
        self.assertGreater(usures[-1], usures[0])

    def test_alternance_2032_couvre_dix_exercices_sans_verrou(self):
        scenario = get_scenario_alternance_2032()
        self.assertEqual(len(scenario), 10)
        self.assertEqual([d.annee for d in scenario], list(range(1, 11)))
        # Aucune année de la mandature 2 n'est verrouillée ni réinvestie.
        self.assertFalse(any(d.verrouillage_irreversibilite for d in scenario[5:]))
        self.assertFalse(any(d.reinvestissement_dividende_dette_mde > 0 for d in scenario[5:]))
        self.assertFalse(any(d.investissements_cycle_long_mde > 0 for d in scenario[5:]))
        # L'usure y monte plus haut que dans la trajectoire verrouillée.
        self.assertGreater(max(d.usure_politique_pts for d in scenario[5:]), 60.0)

    def test_scenarios_enregistres_dans_le_catalogue_cli(self):
        for cle, export in (("double_mandature", get_scenario_double_mandature),
                            ("alternance_2032", get_scenario_alternance_2032)):
            with self.subTest(scenario=cle):
                fabrique, titre = CATALOGUE_SCENARIOS[cle]
                self.assertEqual(len(fabrique()), len(export()))
                self.assertTrue(titre.strip())

    def test_double_mandature_s_execute_sans_diverger(self):
        moteur, resultats = _executer(get_scenario_double_mandature())
        final = resultats[-1]
        self.assertEqual(final.annee, 10)
        # Désendettement net sur la période de dix ans.
        self.assertLess(final.ratio_dette_pib, resultats[4].ratio_dette_pib)
        # Les investissements engagés en fin de mandature 1 mûrissent en mandature 2.
        self.assertGreater(final.investissements_matures_mde, 0.0)
        # Aucun indicateur ne sort de ses bornes physiques.
        for r in resultats:
            self.assertGreaterEqual(r.tension_sociale_locale, 0.0)
            self.assertLessEqual(r.tension_sociale_locale, 100.0)
            self.assertGreaterEqual(r.confiance_democratique, 0.0)
            self.assertLessEqual(r.confiance_democratique, 100.0)

    def test_le_verrou_divise_la_prime_electorale(self):
        """À année électorale égale, le verrou constitutionnel coûte moins cher."""
        _, avec_verrou = _executer(get_scenario_double_mandature())
        _, sans_verrou = _executer(get_scenario_alternance_2032())
        # Année 10 : élection de 2037 dans les deux trajectoires.
        self.assertLess(avec_verrou[-1].spread_bund_bps, sans_verrou[-1].spread_bund_bps)
        # La mandature verrouillée garde une confiance supérieure malgré l'usure.
        self.assertGreater(avec_verrou[-1].confiance_democratique,
                           sans_verrou[-1].confiance_democratique)
        self.assertLess(avec_verrou[-1].tension_sociale_locale,
                        sans_verrou[-1].tension_sociale_locale)


class TestDynamiquesDuMoteur(unittest.TestCase):
    """Chaque dynamique de la période de dix ans est isolée et mesurable."""

    def test_investissement_cycle_long_coute_puis_rapporte(self):
        base = DecisionPolitique(annee=1)
        investi = DecisionPolitique(annee=1, investissements_cycle_long_mde=10.0)
        _, sans = _executer([base])
        _, avec = _executer([investi])
        # Courbe en J : le solde se dégrade l'année de l'investissement
        # (le déficit nominal augmente du montant investi).
        self.assertAlmostEqual(
            avec[0].deficit_nominal_mde - sans[0].deficit_nominal_mde, 10.0, delta=0.1
        )
        # Aucune maturité avant le délai documenté.
        moteur = MoteurSimulationSystemique()
        for annee in range(1, DELAI_MATURITE_INVESTISSEMENTS + 2):
            r = moteur.appliquer_etape(DecisionPolitique(
                annee=annee,
                investissements_cycle_long_mde=10.0 if annee == 1 else 0.0,
            ))
        # Le rendement du premier programme arrive exactement à maturité.
        self.assertEqual(r.investissements_matures_mde, 10.0)
        self.assertEqual(len(moteur.investissements_differes), 1)

    def test_dividende_dette_apaise_sans_creuser_le_deficit(self):
        _, sans = _executer([DecisionPolitique(annee=1)])
        _, avec = _executer([DecisionPolitique(annee=1, reinvestissement_dividende_dette_mde=5.0)])
        # Dépense gagée : le déficit ne se creuse pas du montant réinvesti.
        self.assertAlmostEqual(avec[0].deficit_nominal_mde, sans[0].deficit_nominal_mde, delta=0.5)
        # Le corps social est apaisé.
        self.assertLess(avec[0].tension_sociale_locale, sans[0].tension_sociale_locale)

    def test_usure_politique_fragilise_la_majorite(self):
        _, sans = _executer([DecisionPolitique(annee=1)])
        _, avec = _executer([DecisionPolitique(annee=1, usure_politique_pts=60.0)])
        self.assertGreater(avec[0].risque_censure_parlement, sans[0].risque_censure_parlement)
        self.assertLess(avec[0].confiance_democratique, sans[0].confiance_democratique)
        self.assertEqual(avec[0].usure_politique_pts, 60.0)

    def test_annee_electorale_rencherit_le_spread_sans_verrou(self):
        _, neutre = _executer([DecisionPolitique(annee=1)])
        _, elect = _executer([DecisionPolitique(annee=1, annee_electorale_majeure=True)])
        _, elect_verrou = _executer([DecisionPolitique(
            annee=1, annee_electorale_majeure=True, verrouillage_irreversibilite=True)])
        prime_sans_verrou = elect[0].spread_bund_bps - neutre[0].spread_bund_bps
        prime_verrouille = elect_verrou[0].spread_bund_bps - neutre[0].spread_bund_bps
        self.assertGreater(prime_sans_verrou, prime_verrouille)
        self.assertGreater(prime_sans_verrou, 0.0)
        self.assertTrue(elect_verrou[0].irreversibilite_reformes_active)


class TestLeviersEtPreset(unittest.TestCase):
    """Les quatre leviers de la période de dix ans pilotent réellement le moteur."""

    CLEFS = (
        "verrouillage_irreversibilite",
        "clause_revoyure_evaluation",
        "dividende_dette_reinvesti",
        "investissements_cycle_long",
    )

    def test_leviers_catalogues_et_champes(self):
        champs_attendus = {
            "verrouillage_irreversibilite": "verrouillage_irreversibilite",
            "clause_revoyure_evaluation": "clause_revoyure_evaluation",
            "dividende_dette_reinvesti": "reinvestissement_dividende_dette_mde",
            "investissements_cycle_long": "investissements_cycle_long_mde",
        }
        for cle, champ in champs_attendus.items():
            with self.subTest(levier=cle):
                self.assertIn(cle, LEVIERS)
                self.assertEqual(LEVIERS[cle].champ, champ)
                self.assertTrue(LEVIERS[cle].source.strip())

    def test_leviers_passent_par_decision_moteur(self):
        from simulateur.domaines import decision_moteur
        parametres = normaliser({
            "verrouillage_irreversibilite": 1.0,
            "clause_revoyure_evaluation": 1.0,
            "dividende_dette_reinvesti": 5.0,
            "investissements_cycle_long": 6.0,
        })
        decision = decision_moteur(parametres, 5)
        self.assertTrue(decision.verrouillage_irreversibilite)
        self.assertTrue(decision.clause_revoyure_evaluation)
        self.assertGreater(decision.reinvestissement_dividende_dette_mde, 0.0)
        self.assertGreater(decision.investissements_cycle_long_mde, 0.0)

    def test_preset_double_mandature_se_simule(self):
        contexte = construire_contexte(utiliser_cache=False, rafraichir=False, hors_ligne=True)
        sortie = simuler(PRESETS["double_mandature"]["parametres"], contexte, avec_impacts=False)
        self.assertEqual(len(sortie.etapes), 5)
        # Le verrou constitutionnel est actif en fin de trajectoire.
        self.assertTrue(sortie.etapes[-1]["irreversibilite_reformes_active"])
        # Le garde-fou du verrou voyage avec le diagnostic de la simulation.
        cles_diagnostic = {e["cle"] for e in sortie.diagnostic["indicateurs"]}
        self.assertIn("irreversibilite_reformes_active", cles_diagnostic)
        self.assertIn("usure_politique_pts", cles_diagnostic)


class TestGardeFousDoubleMandature(unittest.TestCase):
    """La console de veille surveille l'usure et le verrou constitutionnel."""

    def test_garde_fous_enregistres(self):
        cles = {garde.cle for garde in GARDE_FOUS}
        self.assertIn("usure_politique_pts", cles)
        self.assertIn("irreversibilite_reformes_active", cles)

    def test_diagnostic_mesure_les_deux_grandeurs(self):
        contexte = construire_contexte(utiliser_cache=False, rafraichir=False, hors_ligne=True)
        sortie = simuler(PRESETS["double_mandature"]["parametres"], contexte, avec_impacts=False)
        indicateurs = {e["cle"]: e for e in sortie.diagnostic["indicateurs"]}
        self.assertIn("usure_politique_pts", indicateurs)
        self.assertIn("irreversibilite_reformes_active", indicateurs)
        # Verrou actif : le garde-fou n'est pas en alerte.
        self.assertIn(indicateurs["irreversibilite_reformes_active"]["niveau"],
                      ("favorable", "tolerable"))


if __name__ == "__main__":
    unittest.main()
