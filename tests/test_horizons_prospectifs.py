"""
tests/test_horizons_prospectifs.py — ce que « 5 ans » et « 10 ans » veulent dire.

Vérifié le 15 octobre 2026. La page annonçait : « les dynamiques à maturation
longue s'activent à partir du sixième exercice ». Le moteur dit autre chose, et
la mesure ci-dessous le montre : sur un scénario de dix ans, ces deux dynamiques
sont comptées **dès le premier exercice** ; sur un scénario de cinq ans, elles
restent strictement nulles. Ce n'est pas la sixième année qui les ouvre, c'est
la durée du scénario.

Deux runs, un contexte neutre, aucun levier activé — donc rien à interpréter :

| Exercice | Besoin non couvert de capital public | Dommages climatiques comptés |
|---:|---:|---:|
| 1 | 6,04 Md€ | 4,77 Md€/an |
| 5 | 30,21 Md€ | 4,77 Md€/an |
| 10 | 60,42 Md€ | 4,77 Md€/an |
| à 5 ans, année 1..5 | 0,00 | 0,00 |

Et la contrepartie qui rend la phrase vraie : sur les cinq premiers exercices,
les deux scénarios ne divergent **que** par ces deux séries, toutes deux hors
budget (proxys non ajoutés au déficit). Déficit et dette sont identiques au
centime près — « 5 ans » n'est pas « 10 ans tronqué », c'est la même trajectoire
budgétaire, avec deux dettes invisibles en plus.

Ce fichier tient quatre promesses :

1. **à cinq ans, les dynamiques longues sont absentes** — chaque exercice, et le
   bilan terminal ;
2. **à dix ans, elles sont comptées dès le premier exercice** — et le besoin non
   couvert suit les exercices ;
3. **les deux séries restent hors budget** — le déficit et la dette des cinq
   premiers exercices sont ceux du scénario quinquennal ;
4. **la page dit ce que le moteur fait** — l'aide de l'horizon a été corrigée le
   15 octobre 2026 : plus de « sixième exercice », mais « dès le premier
   exercice d'un scénario de 10 ans ».
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from simulateur.domaines import decision_moteur  # noqa: E402
from simulateur.donnees_live import construire_contexte  # noqa: E402
from simulateur.interface import HTML_PAGE  # noqa: E402
from simulateur.moteur import BESOIN_ANNUALISE_CAPITAL_PUBLIC_MDE  # noqa: E402
from simulateur.moteur_parametrique import simuler  # noqa: E402

#: Les deux séries de maturation longue : elles n'existent que si le scénario
#: couvre plus d'une mandature, et elles ne touchent jamais le budget.
SERIES_LONGUES = ("dette_technique_infrastructures_mde", "dommages_climat_subis_mde")

#: Les séries budgétaires : elles doivent être les mêmes à 5 et à 10 ans.
SERIES_BUDGET = ("deficit_nominal_mde", "dette_nominale_mde")


class TestLesDeuxHorizonsProspectifs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contexte = construire_contexte(utiliser_cache=False, rafraichir=False,
                                           hors_ligne=True)
        cls.cinq = simuler({}, cls.contexte, horizon=5, avec_impacts=False)
        cls.dix = simuler({}, cls.contexte, horizon=10, avec_impacts=False)

    def test_a_cinq_ans_les_dynamiques_longues_restent_absentes(self):
        for etape in self.cinq.etapes:
            for serie in SERIES_LONGUES:
                with self.subTest(annee=etape["annee"], serie=serie):
                    self.assertEqual(etape[serie], 0.0,
                                     "une dynamique de longue durée s'invite dans "
                                     "un scénario d'une seule mandature")
        bilan = self.cinq.synthese["bilan_intergenerationnel"]
        self.assertEqual(bilan["besoin_non_couvert_capital_public_mde"], 0.0)
        self.assertEqual(bilan["risque_climat_annualise_hors_budget_mde"], 0.0)
        self.assertEqual(bilan["dommages_climat_evites_annualises_hors_budget_mde"], 0.0)

    def test_a_dix_ans_elles_sont_comptees_des_le_premier_exercice(self):
        premier = self.dix.etapes[0]
        self.assertGreater(premier["dette_technique_infrastructures_mde"], 0.0,
                           "le besoin non couvert n'est pas compté au premier exercice")
        self.assertGreater(premier["dommages_climat_subis_mde"], 0.0,
                           "les dommages climatiques ne sont pas comptés au premier exercice")
        # La page disait « à partir du sixième exercice » : c'est faux, et voici
        # l'écart, mesuré. Le sixième exercice n'a rien d'un seuil.
        sixieme = self.dix.etapes[5]
        self.assertAlmostEqual(sixieme["dommages_climat_subis_mde"],
                               premier["dommages_climat_subis_mde"], places=6,
                               msg="les dommages changent d'un exercice à l'autre : "
                                   "le sixième n'est plus un seuil, c'est une année")

    def test_le_besoin_non_couvert_suit_les_exercices(self):
        valeurs = [etape["dette_technique_infrastructures_mde"] for etape in self.dix.etapes]
        self.assertEqual(len(valeurs), 10)
        self.assertEqual(valeurs, sorted(valeurs), "le besoin non couvert recule")
        pas = [b - a for a, b in zip(valeurs, valeurs[1:], strict=False)]
        self.assertLess(max(pas) - min(pas), 0.02,
                        "le besoin n'est plus annualisé au même rythme : il devient "
                        "une courbe, pas une hypothèse de scénario")
        self.assertAlmostEqual(valeurs[0], BESOIN_ANNUALISE_CAPITAL_PUBLIC_MDE, places=2,
                               msg="le premier exercice ne vaut pas l'hypothèse annualisée")
        bilan = self.dix.synthese["bilan_intergenerationnel"]
        self.assertAlmostEqual(bilan["besoin_non_couvert_capital_public_mde"],
                               valeurs[-1], places=6,
                               msg="le bilan terminal ne relit pas la dernière année")

    def test_les_deux_series_longues_restent_hors_budget(self):
        """Le proxy de besoin et le risque climatique ne sont pas des dépenses."""
        note = self.dix.synthese["bilan_intergenerationnel"]["note_methodologique"]
        self.assertIn("séparées", note)
        for etape in self.dix.etapes:
            with self.subTest(annee=etape["annee"]):
                self.assertIn("dommages_climat_subis_mde", etape)
        # Le risque climatique est annualisé : il ne s'accumule pas dans le temps.
        risques = [etape["dommages_climat_subis_mde"] for etape in self.dix.etapes]
        self.assertEqual(len(set(risques)), 1,
                         "le risque climatique se compose comme une dette : ce n'est "
                         "plus un dommage annuel, c'est un stock à interpréter")

    def test_les_deux_scenarios_ne_divergent_que_par_ces_series(self):
        """Cinq ans, ce n'est pas dix ans tronqué — et la mesure le dit au centime."""
        for annee, (court, long) in enumerate(
                zip(self.cinq.etapes, self.dix.etapes, strict=False), start=1):
            divergentes = {cle for cle in court
                           if isinstance(court[cle], (int, float))
                           and isinstance(long.get(cle), (int, float))
                           and abs(court[cle] - long[cle]) > 1e-9}
            with self.subTest(annee=annee):
                self.assertEqual(divergentes, set(SERIES_LONGUES),
                                 "les deux scénarios divergent ailleurs que par les "
                                 "dynamiques de maturation longue")
            for cle in SERIES_BUDGET:
                with self.subTest(annee=annee, serie=cle):
                    self.assertAlmostEqual(court[cle], long[cle], places=6,
                                           msg="une série budgétaire dépend de la durée "
                                               "du scénario : elle n'est plus causale")

    def test_l_horizon_de_deux_mandatures_est_celui_du_scenario(self):
        """Le drapeau suit la durée simulée, pas le numéro de l'exercice."""
        self.assertIs(decision_moteur({}, 1, horizon=10).horizon_deux_mandatures, True)
        self.assertIs(decision_moteur({}, 1, horizon=5).horizon_deux_mandatures, False)
        self.assertIs(decision_moteur({}, 5, horizon=5).horizon_deux_mandatures, False)

    def test_la_page_dit_ce_que_le_moteur_fait(self):
        """L'aide de l'horizon : mesurée le 15 octobre 2026, donc corrigée."""
        debut = HTML_PAGE.index('id="horizon-simulation"')
        aide = HTML_PAGE[HTML_PAGE.rindex("data-aide=", 0, debut):debut]
        self.assertIn("dès le premier exercice", aide,
                      "l'aide de l'horizon ne dit pas quand les dynamiques longues "
                      "s'ouvrent")
        self.assertIn("10 ans", aide, "l'aide ne dit plus quel horizon les ouvre")
        self.assertNotIn("sixième", aide,
                         "l'aide promet un seuil que le moteur ne connaît pas")
        self.assertIn('value="5"', HTML_PAGE, "l'horizon d'une mandature a disparu")
        self.assertIn('value="10"', HTML_PAGE, "l'horizon de deux mandatures a disparu")


if __name__ == "__main__":
    unittest.main()
