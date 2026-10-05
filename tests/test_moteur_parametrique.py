"""
tests/test_moteur_parametrique.py — Tests de l'orchestrateur paramétrique.

C'est la pièce qui transforme un vecteur de 93 leviers en trajectoire à 5 ans,
en scores de domaine et en matrice d'impacts croisés. Les tests vérifient le
contrat public (formes, bornes, déterminisme) et les propriétés économiques
attendues (sens des effets, cohérence de la référence).
"""

import json
import unittest

from simulateur.donnees_live import construire_contexte
from simulateur.moteur_parametrique import (
    calibrer_contexte,
    catalogue_complet,
    comparer,
    moteur_calibre,
    simuler,
    tableau_croise,
)
from simulateur.parametres import LEVIERS, PRESETS, normaliser


def _contexte():
    return construire_contexte(utiliser_cache=False, rafraichir=False)


def _domaine(sortie, cle):
    return next(d for d in sortie.domaines if d["cle"] == cle)


class TestContratDeSimulation(unittest.TestCase):
    """Formes et bornes de la sortie publique."""

    @classmethod
    def setUpClass(cls):
        cls.contexte = _contexte()
        cls.neutre = simuler({}, cls.contexte, avec_impacts=False)

    def test_cinq_etapes_et_tous_les_domaines(self):
        self.assertEqual(len(self.neutre.etapes), 5)
        self.assertEqual([e["annee"] for e in self.neutre.etapes], [1, 2, 3, 4, 5])
        self.assertEqual(len(self.neutre.domaines), 20)
        self.assertEqual({d["cle"] for d in self.neutre.domaines},
                         {d["cle"] for d in self.neutre.domaines})

    def test_horizon_parametrable(self):
        court = simuler({"reforme_ric": 1.0}, self.contexte, horizon=3, avec_impacts=False)
        self.assertEqual(len(court.etapes), 3)

    def test_sortie_json_serialisable(self):
        charge = self.neutre.en_dict()
        texte = json.dumps(charge, ensure_ascii=False)
        self.assertIn("synthese", charge)
        self.assertIn("journal", charge)
        self.assertGreater(len(texte), 10_000)

    def test_avertissements_explicites(self):
        """Le simulateur doit dire ce qu'il fait et ce qu'il ne fait pas."""
        textes = " ".join(self.neutre.avertissements).lower()
        self.assertIn("écart", textes)
        self.assertTrue(len(self.neutre.avertissements) >= 2)

    def test_parametres_inconnus_refuses(self):
        with self.assertRaises(ValueError):
            simuler({"levier_qui_nexiste_pas": 1.0}, self.contexte)

    def test_determinisme(self):
        jeu = {"tva_taux_normal": 1.0, "reforme_ric": 1.0}
        un = simuler(jeu, self.contexte, avec_impacts=False).en_dict()
        deux = simuler(jeu, self.contexte, avec_impacts=False).en_dict()
        self.assertEqual([e["ratio_deficit_pib"] for e in un["etapes"]],
                         [e["ratio_deficit_pib"] for e in deux["etapes"]])
        self.assertEqual([d["score"] for d in un["domaines"]],
                         [d["score"] for d in deux["domaines"]])


class TestNeutraliteEtReference(unittest.TestCase):
    """La trajectoire de référence est le point zéro de toutes les mesures."""

    @classmethod
    def setUpClass(cls):
        cls.contexte = _contexte()
        cls.neutre = simuler({}, cls.contexte, avec_impacts=False)

    def test_scores_neutres(self):
        self.assertTrue(all(abs(d["score"] - 50.0) < 0.1 for d in self.neutre.domaines))
        self.assertAlmostEqual(self.neutre.synthese["score_moyen_domaines"], 50.0, places=1)

    def test_tendances_de_reference_documentees(self):
        """Sans politique, le modèle montre une consolidation automatique."""
        budget = _domaine(self.neutre, "budget")
        self.assertIsNotNone(budget["tendance_reference"])
        self.assertLess(budget["tendance_reference"], 50.0)

    def test_aucun_impact_sans_levier(self):
        self.assertEqual(simuler({}, self.contexte, avec_impacts=True).impacts, [])

    def test_scores_identiques_a_la_reference_en_neutre(self):
        for domaine in self.neutre.domaines:
            with self.subTest(domaine=domaine["cle"]):
                self.assertAlmostEqual(domaine["score"], domaine["score_reference"], places=1)


class TestProprietesEconomiques(unittest.TestCase):
    """Sens des effets : chaque politique doit aller dans le sens attendu."""

    @classmethod
    def setUpClass(cls):
        cls.contexte = _contexte()
        cls.neutre = simuler({}, cls.contexte, avec_impacts=False)

    def test_une_recette_ameliore_le_budget(self):
        sortie = simuler({"tva_taux_normal": 1.5}, self.contexte, avec_impacts=False)
        self.assertGreater(sortie.synthese["recettes_nouvelles_mde"], 0.0)
        self.assertLess(sortie.synthese["deficit_final_pct"],
                        sortie.synthese["deficit_reference_pct"])
        self.assertGreater(_domaine(sortie, "budget")["score"], 50.0)

    def test_une_depense_est_bien_comptee(self):
        sortie = simuler({"hopital_public": 6.0}, self.contexte, avec_impacts=False)
        self.assertGreater(sortie.synthese["depenses_nouvelles_mde"], 0.0)
        self.assertGreater(_domaine(sortie, "sante")["score"], 50.0)

    def test_austerite_degrades_le_climat_social(self):
        sortie = simuler(PRESETS["austerite"]["parametres"], self.contexte, avec_impacts=False)
        self.assertGreater(sortie.synthese["tension_finale"], self.neutre.synthese["tension_finale"])
        self.assertLess(_domaine(sortie, "democratie")["score"], 50.0)

    def test_consolidation_credible_detend_le_spread(self):
        sortie = simuler(PRESETS["mandature"]["parametres"], self.contexte, avec_impacts=False)
        self.assertLess(sortie.synthese["spread_final_bps"], self.neutre.synthese["spread_final_bps"])

    def test_choc_geopolitique_degrades_l_ensemble(self):
        """Fermeture d'Hormuz : le choc domine la riposte, sauf sur la résilience."""
        sortie = simuler(PRESETS["hormuz"]["parametres"], self.contexte, avec_impacts=False)
        self.assertLess(sortie.synthese["score_moyen_domaines"], 42.0)
        self.assertLess(_domaine(sortie, "budget")["score"], 30.0)
        self.assertLess(_domaine(sortie, "pouvoir_achat")["score"], 30.0)
        # La riposte publique (nucléaire, renouvelables, chèques énergie) se voit :
        self.assertGreater(_domaine(sortie, "resilience")["score"], 50.0)

    def test_les_chocs_ne_s_accumulent_pas_sur_cinq_ans(self):
        """Un choc maintenu doit rester au même niveau d'une année sur l'autre."""
        sortie = simuler({"choc_petrole": 40.0}, self.contexte, avec_impacts=False)
        brents = [etape["cours_petrole_usd"] for etape in sortie.etapes]
        self.assertEqual(len({round(b, 1) for b in brents}), 1)
        self.assertLess(brents[0], 250.0)

    def test_guerre_nucleaire_n_est_pas_un_scenario_heureux(self):
        sortie = simuler(PRESETS["escalade_nucleaire"]["parametres"],
                         self.contexte, avec_impacts=False)
        self.assertLess(sortie.synthese["score_moyen_domaines"], 45.0)
        self.assertLess(_domaine(sortie, "budget")["score"], 30.0)

    def test_scenario_de_mandature_ameliore_la_moyenne(self):
        sortie = simuler(PRESETS["mandature"]["parametres"], self.contexte, avec_impacts=False)
        self.assertGreater(sortie.synthese["score_moyen_domaines"], 55.0)


class TestContexteEtCalibrage(unittest.TestCase):
    """Le moteur doit être recalé sur les données publiques du jour."""

    def test_calibrer_contexte_transmet_les_valeurs_reelles(self):
        contexte = _contexte()
        moteur = calibrer_contexte(moteur_calibre(contexte), contexte)
        self.assertAlmostEqual(moteur.reference["taux_oat_pct"], contexte.taux_oat_10ans, places=2)
        self.assertAlmostEqual(moteur.reference["taux_bund_pct"], contexte.taux_bund_10ans, places=3)
        self.assertAlmostEqual(moteur.national.pib_nominal_mde, contexte.pib_nominal_mde, places=1)
        self.assertAlmostEqual(moteur.reference["spread_bps"], contexte.spread_oat_bund_bps, places=1)

    def test_le_contexte_est_traçable_dans_la_sortie(self):
        contexte = _contexte()
        sortie = simuler({}, contexte, avec_impacts=False).en_dict()
        self.assertEqual(sortie["contexte"]["mode"], contexte.mode)
        self.assertTrue(sortie["contexte"]["provenance"])
        self.assertEqual(sortie["contexte"]["pib_nominal_mde"], contexte.pib_nominal_mde)

    def test_un_contexte_live_change_les_resultats(self):
        """Une donnée rafraîchie doit réellement déplacer la trajectoire."""
        base = _contexte()
        from dataclasses import replace
        chere = replace(base, taux_oat_10ans=base.taux_oat_10ans + 1.5)
        moteur_base = calibrer_contexte(moteur_calibre(base), base)
        moteur_cher = calibrer_contexte(moteur_calibre(chere), chere)
        self.assertGreater(moteur_cher.reference["taux_oat_pct"],
                           moteur_base.reference["taux_oat_pct"])


class TestImpactsCroises(unittest.TestCase):
    """La matrice levier × domaine est calculée par le modèle, pas saisie."""

    @classmethod
    def setUpClass(cls):
        cls.contexte = _contexte()
        cls.jeu = {
            "tva_taux_normal": 1.0,
            "hopital_public": 6.0,
            "lutte_fraude_fiscale_ia": 10.0,
            "reforme_ric": 1.0,
        }
        cls.sortie = simuler(cls.jeu, cls.contexte, avec_impacts=True, max_leviers_impacts=6)

    def test_impacts_presents_et_structures(self):
        self.assertTrue(self.sortie.impacts)
        for impact in self.sortie.impacts:
            with self.subTest(levier=impact["levier"]):
                self.assertIn(impact["levier"], LEVIERS)
                self.assertIn("effets", impact)
                self.assertTrue(impact["effets"])
                for effet in impact["effets"]:
                    self.assertIn(effet["domaine"], {d["cle"] for d in self.sortie.domaines})
                    self.assertNotEqual(effet["effet_score"], 0.0)

    def test_impacts_tries_par_intensite(self):
        intensites = [max(abs(e["effet_score"]) for e in i["effets"])
                      for i in self.sortie.impacts]
        self.assertEqual(intensites, sorted(intensites, reverse=True))

    def test_impacts_limites_au_nombre_demande(self):
        self.assertLessEqual(len(self.sortie.impacts), 6)

    def test_tableau_croise_coherent(self):
        croise = tableau_croise(self.sortie.impacts)
        self.assertEqual(len(croise["domaines"]), 20)
        self.assertEqual(croise["colonnes_domaines"], [d["cle"] for d in croise["domaines"]])
        for ligne in croise["lignes"]:
            for domaine, effet in ligne["effets"].items():
                self.assertIn(domaine, croise["colonnes_domaines"])
                self.assertNotEqual(effet, 0.0)

    def test_impacts_idempotents(self):
        """Le cache d'impacts ne doit pas changer les valeurs."""
        autre = simuler(self.jeu, self.contexte, avec_impacts=True, max_leviers_impacts=6)
        self.assertEqual(json.dumps(self.sortie.impacts, sort_keys=True),
                         json.dumps(autre.impacts, sort_keys=True))


class TestComparaisonEtCatalogue(unittest.TestCase):
    """Outils d'exploration : comparer les préréglages, décrire l'offre."""

    def test_comparer_tous_les_presets(self):
        resultat = comparer(contexte=_contexte())
        self.assertEqual(len(resultat["comparaison"]), len(PRESETS))
        for entree in resultat["comparaison"]:
            with self.subTest(preset=entree["cle"]):
                self.assertIn(entree["cle"], PRESETS)
                self.assertEqual(len(entree["scores"]), 20)
                self.assertIn("score_moyen_domaines", entree["synthese"])

    def test_comparer_un_sous_ensemble(self):
        resultat = comparer(
            {"austerite": PRESETS["austerite"]["parametres"]}, contexte=_contexte()
        )
        self.assertEqual(len(resultat["comparaison"]), 1)

    def test_catalogue_complet(self):
        catalogue = catalogue_complet()
        self.assertEqual(set(catalogue), {"parametres", "domaines", "familles"})
        self.assertEqual(len(catalogue["domaines"]), 20)
        self.assertEqual(len(catalogue["parametres"]["presets"]), len(PRESETS))
        json.dumps(catalogue, ensure_ascii=False)

    def test_normaliser_borne_tout(self):
        normes = normaliser(dict.fromkeys(LEVIERS, 1000000.0))
        for cle, valeur in normes.items():
            mini, maxi = LEVIERS[cle].bornes
            self.assertLessEqual(valeur, maxi)
            self.assertGreaterEqual(valeur, mini)


if __name__ == "__main__":
    unittest.main()
