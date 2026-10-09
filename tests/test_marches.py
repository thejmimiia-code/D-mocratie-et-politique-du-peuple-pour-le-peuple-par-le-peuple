"""Tests hors ligne du catalogue et du contrat des cotations boursières."""

import json
import unittest
from datetime import datetime, timezone
UTC = timezone.utc
from unittest.mock import patch

from simulateur import marches


class _Reponse:
    def __init__(self, charge: dict):
        self._contenu = json.dumps(charge).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self._contenu


def _charge_yahoo(symbole: str) -> dict:
    maintenant = datetime.now(UTC).timestamp()
    return {
        "chart": {
            "result": [{
                "meta": {
                    "symbol": symbole,
                    "currency": "EUR",
                    "longName": "Indice de test",
                    "fullExchangeName": "Place de test",
                    "regularMarketPrice": 1234.5,
                    "regularMarketTime": maintenant,
                    "regularMarketChange": -12.5,
                    "regularMarketChangePercent": -1.0,
                    "chartPreviousClose": 1247.0,
                    "regularMarketDayHigh": 1250.0,
                    "regularMarketDayLow": 1230.0,
                    "regularMarketVolume": 456,
                },
            }],
            "error": None,
        },
    }


class TestCatalogueMarches(unittest.TestCase):
    def setUp(self):
        with marches._CACHE_VERROU:
            marches._CACHE_COTATIONS.clear()

    def tearDown(self):
        with marches._CACHE_VERROU:
            marches._CACHE_COTATIONS.clear()

    def test_univers_representatif_et_identifiants_uniques(self):
        cles = [marche["cle"] for marche in marches.MARCHES_ACTIONS]
        symboles = [marche["symbole"] for marche in marches.MARCHES_ACTIONS]
        self.assertEqual(len(cles), 13)
        self.assertEqual(len(set(cles)), len(cles))
        self.assertEqual(len(set(symboles)), len(symboles))
        self.assertIn("cac40", cles)
        self.assertIn("sp500", cles)
        self.assertIn("shanghai_composite", cles)

    def test_metadonnees_sans_reseau_ne_fabriquent_aucun_cours(self):
        resultat = marches.obtenir_cotations(actualiser=False)
        self.assertEqual(resultat["nombre_indices"], 13)
        self.assertEqual(len(resultat["indices"]), 13)
        self.assertTrue(all(x["cours"] is None for x in resultat["indices"]))
        self.assertTrue(all(x["statut"] == "indisponible" for x in resultat["indices"]))

    def test_collecte_conserve_le_cours_la_variation_et_les_horodatages(self):
        def urlopen(requete, timeout):
            self.assertGreater(timeout, 0)
            symbole = next(
                (x["symbole"] for x in marches.MARCHES_ACTIONS if x["symbole"] in requete.full_url),
                marches.MARCHES_ACTIONS[0]["symbole"],
            )
            return _Reponse(_charge_yahoo(symbole))

        with patch.object(marches.urllib.request, "urlopen", side_effect=urlopen):
            resultat = marches.obtenir_cotations(actualiser=True, timeout=0.5)

        self.assertEqual(resultat["statut_collecte"], "ok")
        self.assertTrue(all(x["statut"] == "observé" for x in resultat["indices"]))
        cac = next(x for x in resultat["indices"] if x["cle"] == "cac40")
        self.assertEqual(cac["cours"], 1234.5)
        self.assertEqual(cac["variation_jour_pct"], -1.0)
        self.assertEqual(cac["devise"], "EUR")
        self.assertTrue(cac["horodatage_cours_utc"])
        self.assertIn("euronext", cac["page_officielle"].lower())

    def test_ancienne_seance_ne_se_presente_pas_comme_cotation_du_jour(self):
        maintenant = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)  # lundi, heure locale Europe/Paris
        cotation = marches._fraicheur_cotation({
            "horodatage_cours_utc": "2026-10-02T15:00:00+00:00",  # vendredi
            "fuseau_horaire_place": "Europe/Paris",
        }, maintenant=maintenant)
        self.assertEqual(cotation["statut"], "dernier cours")
        self.assertEqual(cotation["date_cours_locale"], "2026-10-02")
        self.assertIn("hors séance", cotation["etat_place"])
        self.assertIn("flux différé", cotation["etat_place"])

    def test_cours_trop_ancien_est_signale_comme_perime(self):
        maintenant = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)
        cotation = marches._fraicheur_cotation({
            "horodatage_cours_utc": "2026-10-01T12:00:00+00:00",
            "fuseau_horaire_place": "Europe/Paris",
        }, maintenant=maintenant, cache=True)
        self.assertEqual(cotation["statut"], "ancien")
        self.assertGreater(cotation["age_heures"], 72)
        self.assertIn("périmée", cotation["etat_place"])

    def test_echec_reseau_affiche_indisponible_et_non_un_faux_zero(self):
        def echec(*_args, **_kwargs):
            raise OSError("réseau indisponible")

        with patch.object(marches.urllib.request, "urlopen", side_effect=echec):
            resultat = marches.obtenir_cotations(actualiser=True, timeout=0.1)

        self.assertEqual(resultat["statut_collecte"], "partielle")
        self.assertTrue(all(x["cours"] is None for x in resultat["indices"]))
        self.assertTrue(all(x["statut"] == "indisponible" for x in resultat["indices"]))
        self.assertTrue(all(x["erreur_rafraichissement"] for x in resultat["indices"]))


if __name__ == "__main__":
    unittest.main()
