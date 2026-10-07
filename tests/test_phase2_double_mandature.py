"""Tests de R&D — points P16-P21 de la période de deux mandatures.

Les coefficients exploratoires sont vérifiés comme mécanismes de scénario,
non comme estimations empiriques ni prévisions.
"""

import unittest

from simulateur.domaines import construire_flux, decision_moteur
from simulateur.model import DecisionPolitique
from simulateur.moteur import (
    BESOIN_ANNUALISE_CAPITAL_PUBLIC_MDE,
    DELAI_MATURITE_CAPACITES_DEFENSE,
    DELAI_MATURITE_CAPITAL_HUMAIN,
    DOMMAGES_CLIMAT_ANNUALISES_MDE,
    SEUIL_SATURATION_ADMINISTRATIVE,
    MoteurSimulationSystemique,
)
from simulateur.parametres import LEVIERS, PRESETS, normaliser


def _executer(decisions):
    moteur = MoteurSimulationSystemique()
    return moteur, [moteur.appliquer_etape(decision) for decision in decisions]


class TestPhase2DeuxMandatures(unittest.TestCase):
    def test_p16_besoin_non_couvert_est_un_proxy_annuel(self):
        _, cinq_ans = _executer([
            DecisionPolitique(annee=annee) for annee in range(1, 6)
        ])
        self.assertTrue(all(r.dette_technique_infrastructures_mde == 0.0 for r in cinq_ans))

        _, dix_ans_sans_effort = _executer([
            DecisionPolitique(annee=annee, horizon_deux_mandatures=True)
            for annee in range(1, 11)
        ])
        self.assertAlmostEqual(
            dix_ans_sans_effort[-1].dette_technique_infrastructures_mde,
            BESOIN_ANNUALISE_CAPITAL_PUBLIC_MDE * 10,
            places=1,
        )

        _, dix_ans_couvert = _executer([
            DecisionPolitique(
                annee=annee,
                horizon_deux_mandatures=True,
                entretien_capital_public_mde=BESOIN_ANNUALISE_CAPITAL_PUBLIC_MDE,
            )
            for annee in range(1, 11)
        ])
        self.assertEqual(dix_ans_couvert[-1].dette_technique_infrastructures_mde, 0.0)

    def test_p17_risque_climatique_est_hors_budget_apu(self):
        _, sans_module_long = _executer([DecisionPolitique(annee=1)])
        _, avec_module_long = _executer([
            DecisionPolitique(annee=1, horizon_deux_mandatures=True)
        ])
        self.assertAlmostEqual(
            avec_module_long[0].dommages_climat_subis_mde,
            DOMMAGES_CLIMAT_ANNUALISES_MDE,
            places=2,
        )
        # Les pertes sociétales annualisées ne sont pas assimilées à une dépense APU.
        self.assertEqual(
            avec_module_long[0].deficit_nominal_mde,
            sans_module_long[0].deficit_nominal_mde,
        )
        self.assertEqual(avec_module_long[0].dommages_climat_evites_mde, 0.0)

    def test_p17_adaptation_affiche_un_evite_sans_le_compter_en_recette(self):
        _, base = _executer([
            DecisionPolitique(annee=1, horizon_deux_mandatures=True)
        ])
        _, adapte = _executer([
            DecisionPolitique(
                annee=1,
                horizon_deux_mandatures=True,
                effort_adaptation_climat_mde=1.0,
            )
        ])
        self.assertGreater(adapte[0].dommages_climat_evites_mde, 0.0)
        # Seul le décaissement d'adaptation affecte le budget ; les dommages évités
        # ne sont pas une recette publique et ne neutralisent pas ce coût.
        self.assertAlmostEqual(
            adapte[0].deficit_nominal_mde - base[0].deficit_nominal_mde,
            1.0,
            delta=0.1,
        )

    def test_p18_cohorte_humaine_arrive_apres_le_delai_expose(self):
        moteur = MoteurSimulationSystemique()
        resultats = []
        for annee in range(1, DELAI_MATURITE_CAPITAL_HUMAIN + 2):
            resultats.append(moteur.appliquer_etape(DecisionPolitique(
                annee=annee,
                capital_humain_mde=2.0 if annee == 1 else 0.0,
            )))
        self.assertEqual(resultats[DELAI_MATURITE_CAPITAL_HUMAIN - 1].capital_humain_mature_mde, 0.0)
        self.assertEqual(resultats[DELAI_MATURITE_CAPITAL_HUMAIN].capital_humain_mature_mde, 2.0)

    def test_p19_capacite_bitd_arrive_apres_la_fenetre_lpm(self):
        moteur = MoteurSimulationSystemique()
        resultats = []
        for annee in range(1, DELAI_MATURITE_CAPACITES_DEFENSE + 2):
            resultats.append(moteur.appliquer_etape(DecisionPolitique(
                annee=annee,
                montee_capacite_defense_mde=3.0 if annee == 1 else 0.0,
            )))
        self.assertEqual(resultats[DELAI_MATURITE_CAPACITES_DEFENSE - 1].capacites_defense_matures_mde, 0.0)
        self.assertEqual(resultats[DELAI_MATURITE_CAPACITES_DEFENSE].capacites_defense_matures_mde, 3.0)

    def test_p20_saturation_est_un_parametre_explicite(self):
        _, seuil = _executer([DecisionPolitique(
            annee=1, reformes_structurelles_actives=SEUIL_SATURATION_ADMINISTRATIVE
        )])
        _, surcharge = _executer([DecisionPolitique(
            annee=1, reformes_structurelles_actives=SEUIL_SATURATION_ADMINISTRATIVE + 2
        )])
        self.assertAlmostEqual(
            surcharge[0].tension_sociale_locale - seuil[0].tension_sociale_locale,
            0.6,
            places=1,
        )
        self.assertAlmostEqual(
            seuil[0].confiance_democratique - surcharge[0].confiance_democratique,
            0.3,
            places=1,
        )

    def test_les_nouveaux_leviers_sont_bornes_sources_et_cables(self):
        correspondances = {
            "entretien_capital_public": "entretien_capital_public_mde",
            "capital_humain": "capital_humain_mde",
            "montee_capacite_defense": "montee_capacite_defense_mde",
            "charge_reformes_simultanees": "reformes_structurelles_actives",
        }
        parametres = normaliser({
            "entretien_capital_public": 6.0,
            "adaptation_climat": 1.0,
            "capital_humain": 2.0,
            "montee_capacite_defense": 2.0,
            "charge_reformes_simultanees": 6.0,
        })
        decision = decision_moteur(parametres, 1, horizon=10)
        self.assertTrue(decision.horizon_deux_mandatures)
        for levier, champ in correspondances.items():
            with self.subTest(levier=levier):
                self.assertIn(levier, LEVIERS)
                self.assertEqual(getattr(decision, champ), parametres[levier])
                self.assertTrue(LEVIERS[levier].source.strip())
        flux = construire_flux(parametres, 0)
        self.assertGreater(flux["depenses_nouvelles_mde"], 0.0)
        self.assertEqual(len(LEVIERS), 101)
        self.assertIn("entretien_capital_public", PRESETS["double_mandature"]["parametres"])

    def test_p21_sortie_est_un_ledger_pas_un_score_composite(self):
        from simulateur.donnees_live import construire_contexte
        from simulateur.moteur_parametrique import simuler

        sortie = simuler({}, construire_contexte(
            utiliser_cache=False, rafraichir=False, hors_ligne=True
        ), horizon=10, avec_impacts=False)
        bilan = sortie.synthese["bilan_intergenerationnel"]
        self.assertEqual(sortie.horizon, 10)
        self.assertEqual(len(sortie.etapes), 10)
        self.assertIn("dette_publique_mde", bilan)
        self.assertIn("actifs_arrives_a_maturite_mde", bilan)
        self.assertNotIn("score", bilan)
        self.assertEqual(bilan["annee_terminal"], 10)


if __name__ == "__main__":
    unittest.main()
