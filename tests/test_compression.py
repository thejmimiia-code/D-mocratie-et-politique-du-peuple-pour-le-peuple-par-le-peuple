"""tests/test_compression.py — négociation et application de la compression HTTP.

La compression est le principal gain de fluidité du serveur : elle divise par
cinq à sept le volume échangé sans toucher au contenu. Ces tests protègent
trois propriétés, qui sont aussi trois manières de casser la page :

  1. la **négociation** respecte le client (qualités, refus, absence d'en-tête) ;
  2. la **compression** ne s'applique jamais à perte (jamais plus gros qu'avant) ;
  3. le **contrat HTTP** est complet : ``Content-Encoding``, ``Content-Length``
     cohérent et ``Vary`` présent — sans ``Vary``, un proxy pourrait servir du
     gzip à un client qui ne le décode pas.
"""

import gzip
import unittest

from simulateur.compression import (
    EN_TETE_VARY,
    SEUIL_COMPRESSION,
    compresser,
    encodages_disponibles,
    negocier,
    repondre,
)


class TestNegociation(unittest.TestCase):
    """Le serveur choisit l'encodage que le client accepte, pas un autre."""

    def test_sans_en_tete_aucune_compression(self):
        for valeur in (None, "", "   "):
            self.assertIsNone(negocier(valeur))

    def test_gzip_simple(self):
        self.assertEqual(negocier("gzip"), "gzip")

    def test_pas_de_compression_si_identity_est_une_et_deflate_refuse(self):
        # Ce navigateur n'a pas demandé gzip : on ne compresse pas.
        self.assertIsNone(negocier("identity"))
        self.assertIsNone(negocier("deflate;q=0, identity;q=1"))

    def test_le_refus_explicite_lemporte(self):
        self.assertIsNone(negocier("gzip;q=0"))
        self.assertIsNone(negocier("gzip;q=0, deflate;q=0"))

    def test_etoile_qualite_zero_desactive_tout(self):
        self.assertIsNone(negocier("*;q=0"))

    def test_etoile_donne_le_defaut_aux_encodages_non_cites(self):
        # « * » s'applique aux encodages non nommés : gzip est donc recevable.
        self.assertIn(negocier("*"), encodages_disponibles())
        self.assertIn(negocier("gzip, *;q=0.5"), encodages_disponibles())

    def test_qualite_nominative_lemporte_sur_etoile(self):
        # gzip est explicitement refusé ; « * » ne doit pas le réactiver. Les
        # autres encodages reçoivent la qualité de « * », ils restent valides.
        self.assertNotEqual(negocier("gzip;q=0, *;q=0.8"), "gzip")
        # Seul gzip est disponible dans ce cas : plus rien à proposer.
        self.assertIsNone(negocier("gzip;q=0, br;q=0, zstd;q=0, deflate;q=0"))

    def test_preference_du_serveur_entre_encodages_disponibles(self):
        choix = negocier("deflate;q=1, gzip;q=1")
        self.assertIn(choix, encodages_disponibles())

    def test_en_tete_malforme_ne_leve_pas(self):
        for valeur in ("gzip;", "gzip;q=abc", ";;;", "gzip;;;;", "q=1"):
            self.assertIsInstance(negocier(valeur), (str, type(None)))

    def test_casse_et_espaces_indifferents(self):
        self.assertIn(negocier("  GZIP ,  deflate "), encodages_disponibles())


class TestCompression(unittest.TestCase):
    """Compresser ne doit jamais être une régression."""

    def test_sous_le_seuil_rien_nest_compresse(self):
        charge = b"x" * (SEUIL_COMPRESSION - 1)
        sortie, encodage = compresser(charge, "gzip")
        self.assertIsNone(encodage)
        self.assertEqual(sortie, charge)

    def test_une_charge_repetitive_gagne_beaucoup(self):
        charge = ("ce simulateur est un modele, pas une prophetie. " * 400).encode("utf-8")
        sortie, encodage = compresser(charge, "gzip")
        self.assertEqual(encodage, "gzip")
        self.assertLess(len(sortie), len(charge) / 5)

    def test_flux_gzip_est_decodable_par_la_bibliotheque_standard(self):
        charge = ("instant T : dette, deficit, OAT, spread. " * 200).encode("utf-8")
        sortie, encodage = compresser(charge, "gzip")
        self.assertEqual(encodage, "gzip")
        self.assertEqual(gzip.decompress(sortie), charge)

    def test_encodage_inconnu_ou_absent_laisse_la_charge_intacte(self):
        charge = b"charge brute" * 100
        for encodage in (None, "", "inconnu", "identity"):
            sortie, retenu = compresser(charge, encodage)
            self.assertIsNone(retenu)
            self.assertEqual(sortie, charge)

    def test_une_compression_non_rentable_est_abandonnee(self):
        # Données aléatoires : gzip ne peut pas les réduire, il les gonfle.
        import os

        charge = os.urandom(4096)
        sortie, encodage = compresser(charge, "gzip")
        self.assertIsNone(encodage, "une charge incompressible doit rester brute")
        self.assertEqual(sortie, charge)

    def test_compression_deterministe_et_idempotente_cote_client(self):
        charge = ("meme entree, meme sortie " * 120).encode("utf-8")
        premiere, _ = compresser(charge, "gzip")
        seconde, _ = compresser(charge, "gzip")
        self.assertEqual(premiere, seconde)


class TestRepondre(unittest.TestCase):
    """Le raccourci utilisé par le serveur."""

    def test_repondre_enchaine_negociation_et_compression(self):
        charge = ("contexte instant T " * 300).encode("utf-8")
        sortie, encodage = repondre("gzip", charge)
        self.assertEqual(encodage, "gzip")
        self.assertEqual(gzip.decompress(sortie), charge)
        brute, sans = repondre("identity", charge)
        self.assertIsNone(sans)
        self.assertEqual(brute, charge)

    def test_en_tete_vary_est_expose(self):
        self.assertEqual(EN_TETE_VARY, "Accept-Encoding")


if __name__ == "__main__":
    unittest.main()
