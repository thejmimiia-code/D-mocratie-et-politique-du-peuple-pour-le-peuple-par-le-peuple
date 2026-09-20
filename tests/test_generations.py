"""
tests/test_generations.py — Tests unitaires et d'intégration du cycle de vie et des 3 générations.
Vérifie la cohérence des cohortes G1, G2, G3, des flux croisés intergénérationnels
et de l'Indice d'Harmonie Intergénérationnelle (IEHI).
"""

import unittest
from simulateur.model import (
    CohorteGeneration1Seniors,
    CohorteGeneration2Actifs,
    CohorteGeneration3Jeunesse,
    FluxCroisesIntergenerationnels,
    StrateCycleDeVieEtGenerations,
    DecisionPolitique,
    ResultatEtapeSimulation,
)
from simulateur.moteur import MoteurSimulationSystemique
from simulateur.scenarios import (
    get_scenario_mandature_5_ans,
    get_scenario_statut_quo,
    get_scenario_austerite_brutale,
)


class TestCycleDeVieEtGenerations(unittest.TestCase):
    """Vérification des cohortes, flux croisés et dynamiques intergénérationnelles."""

    def test_instanciation_et_valeurs_par_defaut(self):
        """Vérifie les effectifs de départ conformes à la démographie française."""
        g1 = CohorteGeneration1Seniors()
        g2 = CohorteGeneration2Actifs()
        g3 = CohorteGeneration3Jeunesse()
        flux = FluxCroisesIntergenerationnels()

        # Cohorte G1 : 14.6M de 65 ans et plus
        self.assertAlmostEqual(g1.population_millions, 14.6)
        self.assertGreater(g1.part_patrimoine_national_pct, 50.0)
        self.assertGreater(g1.garde_enfants_benevole_mde, 10.0)

        # Cohorte G2 : 26.2M d'actifs 35-64 ans
        self.assertAlmostEqual(g2.population_millions, 26.2)
        self.assertGreater(g2.actifs_occupes_millions, 20.0)
        self.assertGreater(g2.indice_charge_sandwich, 50.0)

        # Cohorte G3 : 27.6M d'enfants et jeunes 0-34 ans
        self.assertAlmostEqual(g3.population_millions, 27.6)
        self.assertGreater(g3.taux_pauvrete_pct, 15.0)

        # Flux croisés : retraites et éducation
        self.assertGreater(flux.transfert_retraites_g2_vers_g1_mde, 300.0)
        self.assertGreater(flux.transfert_education_g2_vers_g3_mde, 150.0)
        self.assertGreater(flux.transfert_garde_enfants_g1_vers_g3_mde, 15.0)

    def test_simulation_mandature_dynamique_generations(self):
        """Vérifie l'amélioration de l'harmonie intergénérationnelle sur le plan de mandature."""
        moteur = MoteurSimulationSystemique()
        scenario = get_scenario_mandature_5_ans()

        resultats = [moteur.appliquer_etape(dec) for dec in scenario]
        self.assertEqual(len(resultats), 5)

        an1 = resultats[0]
        an5 = resultats[4]

        # 1. Évolution de la charge de la génération sandwich G2
        self.assertLess(
            an5.g2_charge_sandwich_indice,
            an1.g2_charge_sandwich_indice,
            "Le fardeau de la génération sandwich doit être soulagé en Année 5."
        )

        # 2. Évolution du taux de pauvreté de la jeunesse G3
        self.assertLess(
            an5.g3_taux_pauvrete_pct,
            an1.g3_taux_pauvrete_pct,
            "La pauvreté des jeunes doit reculer grâce à la TVA à 5.5% et aux cantines locales."
        )

        # 3. Indice d'harmonie intergénérationnelle
        self.assertGreater(
            an5.indice_harmonie_intergenerationnelle,
            an1.indice_harmonie_intergenerationnelle,
            "L'indice d'harmonie intergénérationnelle doit progresser sur le quinquennat."
        )
        self.assertGreater(an5.indice_harmonie_intergenerationnelle, 70.0)

        # 4. Propriété generations
        gen_vue = an5.generations
        self.assertIsInstance(gen_vue, StrateCycleDeVieEtGenerations)
        self.assertEqual(gen_vue.g1_seniors.population_millions, an5.g1_seniors_pop_m)
        self.assertEqual(gen_vue.g2_actifs.indice_charge_sandwich, an5.g2_charge_sandwich_indice)
        self.assertEqual(gen_vue.g3_jeunesse.taux_pauvrete_pct, an5.g3_taux_pauvrete_pct)

    def test_comparatif_austerite_vs_mandature_sur_les_generations(self):
        """Vérifie que l'austérité aggrave la pauvreté des jeunes et le fardeau des actifs."""
        moteur_austerite = MoteurSimulationSystemique()
        res_austerite = [moteur_austerite.appliquer_etape(d) for d in get_scenario_austerite_brutale()]

        moteur_mandature = MoteurSimulationSystemique()
        res_mandature = [moteur_mandature.appliquer_etape(d) for d in get_scenario_mandature_5_ans()]

        an5_aust = res_austerite[4]
        an5_mand = res_mandature[4]

        # La charge sandwich sous austérité doit être significativement plus lourde
        self.assertGreater(
            an5_aust.g2_charge_sandwich_indice,
            an5_mand.g2_charge_sandwich_indice + 20.0,
            "L'austérité brutale doit surcharger la génération sandwich."
        )

        # La pauvreté des jeunes doit être plus élevée sous austérité
        self.assertGreater(
            an5_aust.g3_taux_pauvrete_pct,
            an5_mand.g3_taux_pauvrete_pct,
            "L'austérité sans redistribution détériore la situation des jeunes."
        )

        # L'indice d'harmonie intergénérationnelle s'effondre sous austérité
        self.assertLess(
            an5_aust.indice_harmonie_intergenerationnelle,
            an5_mand.indice_harmonie_intergenerationnelle - 30.0,
            "L'harmonie intergénérationnelle doit être brisée sous austérité."
        )

    def test_mesures_specifiques_aide_aidants_et_donations(self):
        """Vérifie l'impact des leviers ciblés (aidants et donations)."""
        moteur = MoteurSimulationSystemique()
        dec_specifique = DecisionPolitique(
            annee=1,
            soutien_proches_aidants_autonomie_mde=4.0,
            incitation_donations_intergenerationnelles=True,
            reforme_dotation_emancipation_jeunesse=True,
        )
        res = moteur.appliquer_etape(dec_specifique)

        # Les donations vers G3 doivent être supérieures à la normale (75 Md€)
        self.assertGreater(res.donations_vers_g3_mde, 85.0)

        # La pauvreté de la jeunesse doit être diminuée par la dotation d'émancipation
        self.assertLess(res.g3_taux_pauvrete_pct, 17.5)


if __name__ == "__main__":
    unittest.main()
