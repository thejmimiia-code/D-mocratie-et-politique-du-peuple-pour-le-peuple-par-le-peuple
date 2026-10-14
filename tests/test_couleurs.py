"""tests/test_couleurs.py — l'atelier de couleurs dit-il vrai ?

Les thèmes de la page sont jugés par un contrôle qui calcule des rapports de
contraste à partir du CSS lui-même. Ce contrôle ne vaut que si l'outil de
mesure est juste : un atelier complaisant blanchirait une couleur illisible.

Ces contrôles éprouvent l'atelier sur des valeurs connues d'avance — les deux
repères de la recommandation WCAG (blanc sur noir : 21 ; #767676 sur blanc :
4,54, le seuil AA) — puis sur les opérations que la page utilise réellement :
lire un hexadécimal court, lire un `rgba()` avec sa transparence, mélanger deux
couleurs comme `color-mix()`, poser une couleur translucide sur son fond, et
résoudre une variable de thème.

Trois refus comptent autant que les succès : une couleur illisible ne doit pas
devenir « noir », un mélange dont aucune proportion n'est écrite ne doit pas
être inventé, et une variable qui s'appelle elle-même ne doit pas boucler.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from outils import couleurs  # noqa: E402


class TestLectureDuneCouleur(unittest.TestCase):
    """Ce que la page écrit doit se lire, et ce qui s'écrit mal doit se refuser."""

    def test_hexadecimal_court_et_long(self):
        self.assertEqual(couleurs.lire("#fff"), (255.0, 255.0, 255.0, 1.0))
        self.assertEqual(couleurs.lire("#0b1220"), (11.0, 18.0, 32.0, 1.0))
        self.assertEqual(couleurs.lire("#9fb0cc"), (159.0, 176.0, 204.0, 1.0))

    def test_hexadecimal_a_huit_chiffres_porte_la_transparence(self):
        self.assertAlmostEqual(couleurs.lire("#00000080")[3], 128 / 255, places=6)

    def test_rgba_et_pourcentage(self):
        self.assertEqual(couleurs.lire("rgb(10, 20, 30)"), (10.0, 20.0, 30.0, 1.0))
        self.assertEqual(couleurs.lire("rgba(10, 20, 30, .5)"), (10.0, 20.0, 30.0, 0.5))
        self.assertEqual(couleurs.lire("rgba(10,20,30,50%)"), (10.0, 20.0, 30.0, 0.5))

    def test_transparent_est_une_couleur(self):
        self.assertEqual(couleurs.lire("transparent"), (0.0, 0.0, 0.0, 0.0))

    def test_ce_qui_n_est_pas_une_couleur_ne_devient_pas_du_noir(self):
        """L'ignorance ne se déguise pas en couleur : sinon un contrôle se tait."""
        for texte in ("", "couleur-du-ciel", "var(--texte)", "48, 45, 60", None):
            with self.subTest(texte=texte):
                self.assertIsNone(couleurs.lire(texte))


class TestMesureDuContraste(unittest.TestCase):
    """Les deux repères de la recommandation, et le seuil AA lui-même."""

    def test_blanc_sur_noir_vaut_vingt_et_un(self):
        self.assertEqual(
            round(couleurs.contraste(couleurs.lire("#ffffff"), couleurs.lire("#000000")), 1), 21.0
        )

    def test_une_seule_couleur_ne_contraste_pas(self):
        for teinte in ("#0b1220", "#38bdf8", "#e6edf7"):
            with self.subTest(teinte=teinte):
                self.assertEqual(couleurs.contraste(couleurs.lire(teinte), couleurs.lire(teinte)), 1.0)

    def test_le_gris_de_reference_du_seuil_aa(self):
        """#767676 sur blanc : le classique « juste au-dessus de 4,5 »."""
        rapport = couleurs.contraste(couleurs.lire("#767676"), couleurs.lire("#ffffff"))
        self.assertGreater(rapport, 4.5)
        self.assertAlmostEqual(rapport, 4.54, places=2)

    def test_le_sens_de_la_comparaison_ne_change_rien(self):
        clair, sombre = couleurs.lire("#fff"), couleurs.lire("#1d3268")
        self.assertEqual(couleurs.contraste(clair, sombre), couleurs.contraste(sombre, clair))


class TestMelangeEtComposition(unittest.TestCase):
    """`color-mix()` et la transparence : les deux opérations de la page."""

    def test_melange_a_part_egale(self):
        self.assertEqual(
            couleurs.melanger(couleurs.lire("#000"), couleurs.lire("#fff"), 50),
            (127.5, 127.5, 127.5, 1.0),
        )

    def test_melange_avec_transparent_garde_l_alpha(self):
        """`color-mix(in srgb, #93a3bd 18%, transparent)` = rgba(147,163,189,.18)."""
        melange = couleurs.melanger(couleurs.lire("#93a3bd"), (0.0, 0.0, 0.0, 0.0), 18)
        self.assertEqual(melange[:3], (147.0, 163.0, 189.0))
        self.assertAlmostEqual(melange[3], 0.18, places=4)

    def test_composer_une_teinte_sur_son_fond(self):
        """Un fond translucide se pose sur le papier, il ne le remplace pas."""
        papier = couleurs.lire("#f5f7fa")
        fond = couleurs.composer(couleurs.lire("rgba(41,88,162,.12)"), papier)
        self.assertEqual(fond[3], 1.0)
        self.assertGreater(couleurs.contraste(couleurs.lire("#18243b"), fond), 10)

    def test_composer_sans_fond_rend_la_couleur_telle_quelle(self):
        self.assertEqual(couleurs.composer(couleurs.lire("#fff"), None), couleurs.lire("#fff"))


class TestResolutionDesVariables(unittest.TestCase):
    """Un thème est un dictionnaire de variables : le contrôle doit le traverser."""

    def setUp(self):
        self.variables = {"--fond": "#0b1220", "--texte": "#e6edf7", "--doux": "var(--texte)"}

    def test_variable_simple_et_variable_qui_en_appelle_une_autre(self):
        self.assertEqual(couleurs.resoudre("var(--fond)", self.variables), (11.0, 18.0, 32.0, 1.0))
        self.assertEqual(couleurs.resoudre("var(--doux)", self.variables), (230.0, 237.0, 247.0, 1.0))

    def test_variable_absente_prend_son_repli(self):
        self.assertEqual(
            couleurs.resoudre("var(--inconnue, #fff)", self.variables), (255.0, 255.0, 255.0, 1.0)
        )
        self.assertIsNone(couleurs.resoudre("var(--inconnue)", self.variables))

    def test_melange_de_deux_couleurs_du_theme(self):
        melange = couleurs.resoudre("color-mix(in srgb,var(--texte) 50%,var(--fond))", self.variables)
        self.assertEqual(melange, (120.5, 127.5, 139.5, 1.0))

    def test_melange_avec_transparent(self):
        melange = couleurs.resoudre("color-mix(in srgb,var(--texte) 20%,transparent)", self.variables)
        self.assertEqual(melange[:3], (230.0, 237.0, 247.0))
        self.assertAlmostEqual(melange[3], 0.2, places=4)

    def test_une_proportion_absente_ne_s_invente_pas(self):
        self.assertIsNone(
            couleurs.resoudre("color-mix(in srgb,var(--texte),var(--fond))", self.variables)
        )

    def test_une_variable_qui_s_appelle_elle_meme_ne_boucle_pas(self):
        self.assertIsNone(couleurs.resoudre("var(--ronde)", {"--ronde": "var(--ronde)"}))

    def test_ecriture_hexadecimale_pour_les_rapports(self):
        self.assertEqual(couleurs.vers_hexa(couleurs.lire("#0B1220")), "#0b1220")


if __name__ == "__main__":
    unittest.main()
