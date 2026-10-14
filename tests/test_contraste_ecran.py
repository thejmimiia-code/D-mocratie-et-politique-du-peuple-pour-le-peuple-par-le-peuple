"""
tests/test_contraste_ecran.py — la page lue comme un navigateur la peint.

`tests/test_themes_en_page.py` mesure des **règles** : chacune avec ses propres
couleurs. Il lui manque l'héritage. Un élément qui peint un fond et laisse
l'encre venir de son parent traverse toutes ses mailles — et c'est exactement
ce qui est arrivé : en thème « jour », le bandeau peignait le bleu M.R.S.C. et
le titre héritait l'encre sombre du thème (1,26:1), sans qu'aucun contrôle de
règle ne puisse le voir.

`outils/contraste_ecran.py` fait donc le travail du navigateur : cascade,
spécificité, héritage des jetons, `var()`, `color-mix()`, `@media` selon la
largeur, dégradés et opacité composés, puis la formule WCAG 2.1 sur chaque
texte de la page réellement servie.

Ces contrôles-ci font deux choses :

1. ils exécutent l'outil sur la page livrée — quatre thèmes, deux largeurs — et
   refusent le moindre texte sous le seuil ;
2. ils **éprouvent l'instrument lui-même** sur de minuscules pages d'essai :
   une dont la faute est certaine (un bouton sans encre), une qui est juste, une
   dont un jeton manque. Un instrument qui ne voit rien passerait le point 1.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from outils import contraste_ecran  # noqa: E402
from simulateur.interface import HTML_PAGE  # noqa: E402

#: La page d'essai fautive : le bouton peint le dégradé de marque et n'écrit
#: aucune encre — celle du thème lui tombe dessus, sombre sur sombre.
PAGE_CASSEE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><title>essai</title><style>
:root,[data-theme="jour"]{
--texte:#18243b; --panel:#ffffff; --bg:#ffffff;
}
body{background:var(--bg);color:var(--texte)}
p{margin:6px 0}
button.primaire{background:linear-gradient(135deg,#1d3268,#2958a2);border:0;padding:8px}
</style></head>
<body>
<p>Un paragraphe ordinaire, bien lisible sur son fond.</p>
<button class="primaire">Simuler</button>
</body></html>
"""

#: La même page, avec l'encre écrite : c'est la correction, et l'outil doit se
#: taire.
PAGE_JUSTE = PAGE_CASSEE.replace(
    "button.primaire{background", "button.primaire{color:#ffffff;background")

#: Un jeton employé mais jamais défini : la feuille d'un thème en cours
#: d'écriture. L'outil ne peut pas résoudre cette encre — il ne doit ni tomber,
#: ni inventer une couleur pour se donner raison.
PAGE_MUETTE = """<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><title>essai</title><style>
:root,[data-theme="jour"]{
--texte:#18243b; --bg:#ffffff;
}
body{background:var(--bg);color:var(--texte)}
p{color:var(--jeton-qui-nexiste-pas);margin:6px 0}
</style></head>
<body><p>Un texte dont l'encre n'existe pas.</p></body></html>
"""


class TestLaPageLivreeSeLit(unittest.TestCase):
    """Ce que le visiteur voit, mesuré sur la page réellement servie."""

    @classmethod
    def setUpClass(cls):
        cls.rapport = contraste_ecran.auditer(HTML_PAGE)

    def test_aucun_texte_ne_passe_sous_le_seuil(self):
        """Quatre thèmes, deux largeurs : 283 et 265 textes, aucune faute."""
        fautes = [f"{theme} / {largeur} px : {mesure.ligne()}"
                  for (theme, largeur), rapport in self.rapport.items()
                  for mesure in rapport["fautes"]]
        self.assertEqual(fautes, [], "textes illisibles :\n" + "\n".join(fautes))

    def test_la_mesure_couvre_vraiment_la_page(self):
        """Un instrument qui ne mesure rien passerait le contrôle précédent.

        Le seuil est bas (deux cents textes) et volontairement large : ce qui
        est vérifié ici n'est pas un nombre exact — il bouge à chaque section
        ajoutée — mais la **couverture** : un audit qui ne verrait que le
        bandeau ne prouve rien.
        """
        for (theme, largeur), rapport in self.rapport.items():
            with self.subTest(theme=theme, largeur=largeur):
                self.assertGreater(len(rapport["mesures"]), 200,
                                   f"{len(rapport['mesures'])} textes mesurés seulement")

    def test_le_bandeau_et_les_boutons_sont_dans_la_mesure(self):
        """Les deux endroits où la faute a été trouvée ne peuvent pas en sortir."""
        mesures, _, _ = contraste_ecran.mesurer(HTML_PAGE, "jour", 1280)
        chemins = [mesure.chemin for mesure in mesures]
        self.assertTrue(any("header" in chemin for chemin in chemins),
                        "le bandeau n'est pas mesuré")
        self.assertTrue(any("barre-contexte" in chemin for chemin in chemins),
                        "les boutons de la barre ne sont pas mesurés")

    def test_les_deux_largeurs_ne_mesurent_pas_la_meme_page(self):
        """Un écran de poche cache des choses : les deux mesures diffèrent.

        Si les deux largeurs rendaient le même nombre de textes, c'est que la
        largeur ne serait pas lue — et l'audit mobile ne serait qu'un décor.
        """
        bureau = len(self.rapport[("soir", 1280)]["mesures"])
        poche = len(self.rapport[("soir", 380)]["mesures"])
        self.assertNotEqual(bureau, poche, "les deux largeurs mesurent la même page")


class TestLInstrumentEstEprouve(unittest.TestCase):
    """Un contrôle qui n'attrape rien ne prouve rien : on le met à l'épreuve."""

    def test_il_attrape_un_bouton_sans_encre(self):
        """Le défaut réel, reproduit en trois lignes : il doit être refusé."""
        mesures, _, _ = contraste_ecran.mesurer(PAGE_CASSEE, "jour", 1280)
        fautes = [mesure for mesure in mesures if mesure.rapport < mesure.seuil]
        self.assertEqual(len(fautes), 1, [mesure.ligne() for mesure in mesures])
        self.assertLess(fautes[0].rapport, 2.0, fautes[0].ligne())
        self.assertIn("Simuler", fautes[0].texte)

    def test_il_se_tait_sur_la_meme_page_corrigee(self):
        """L'encre écrite, et la faute disparaît : la correction suffit."""
        mesures, _, _ = contraste_ecran.mesurer(PAGE_JUSTE, "jour", 1280)
        fautes = [mesure.ligne() for mesure in mesures if mesure.rapport < mesure.seuil]
        self.assertEqual(fautes, [], fautes)

    def test_un_jeton_absent_ne_fait_pas_tomber_l_outil(self):
        """Ce qui ne peut pas être résolu n'est pas mesuré — et n'est pas jugé."""
        mesures, _, _ = contraste_ecran.mesurer(PAGE_MUETTE, "jour", 1280)
        fautes = [mesure.ligne() for mesure in mesures if mesure.rapport < mesure.seuil]
        self.assertEqual(fautes, [], fautes)

    def test_l_outil_compte_ce_qu_il_ecarte(self):
        """Un contrôle qui cache ce qu'il ignore n'est pas un contrôle."""
        _, feuille, details = contraste_ecran.mesurer(HTML_PAGE, "soir", 1280)
        self.assertGreater(len(feuille.ecartees), 0,
                           "aucune règle écartée : l'outil prétend tout mesurer")
        self.assertGreaterEqual(len(details["exemptes"]), 1,
                                "les commandes inactives ne sont plus exemptées")
        for mesure in details["exemptes"]:
            self.assertTrue(mesure.exempte)


class TestLaFeuilleEstLueCommeUnNavigateur(unittest.TestCase):
    """Les briques de la lecture CSS, éprouvées une par une."""

    def test_les_themes_sont_tous_lus(self):
        """Les quatre palettes se lisent, et aucune n'est vide."""
        for theme in contraste_ecran.THEMES:
            with self.subTest(theme=theme):
                palette = contraste_ecran._palette(  # noqa: SLF001
                    contraste_ecran.feuille_de_la_page(HTML_PAGE), theme)
                self.assertGreater(len(palette), 40, f"{theme} : {len(palette)} jetons")

    def test_les_largeurs_suivent_les_medias(self):
        """Une règle de poche ne s'applique pas sur un grand écran."""
        feuille_bureau = contraste_ecran.Feuille(
            contraste_ecran.feuille_de_la_page(HTML_PAGE), 1280)
        feuille_poche = contraste_ecran.Feuille(
            contraste_ecran.feuille_de_la_page(HTML_PAGE), 380)
        self.assertGreater(len(feuille_poche.ecartees), len(feuille_bureau.ecartees),
                           "aucune règle de poche n'a été écartée sur un grand écran")


if __name__ == "__main__":
    unittest.main()
