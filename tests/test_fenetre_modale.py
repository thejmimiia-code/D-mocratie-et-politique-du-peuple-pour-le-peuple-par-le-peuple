"""
tests/test_fenetre_modale.py — la fenêtre se comporte comme une fenêtre.

Le lexique, le guide et le détail des seuils s'ouvrent dans une fenêtre
(`#overlay` + `#modale`). Elle se fermait de trois façons — bouton, clic à
l'extérieur, touche Échap — mais **le clavier n'y entrait pas et n'en sortait
pas** :

* ouvrir la fenêtre ne déplaçait pas le focus : la première tabulation menait
  aux commandes de la page, **derrière** la fenêtre ouverte, invisible et
  pourtant actionnable ;
* rien ne retenait la tabulation : on traversait la fenêtre, puis la page
  entière, et le lecteur au clavier se retrouvait au pied de page sans avoir
  rien vu ;
* fermer la fenêtre laissait le curseur là où le navigateur l'avait laissé —
  au mieux sur le corps du document, au pire trois sections plus bas ;
* Échap était capté même quand rien n'était ouvert : la touche qui sert à
  quitter un champ ou à interrompre un chargement était prise au visiteur.

Ce que ces contrôles-ci gardent, ce sont les gestes : **le focus entre, il ne
sort pas, il revient**. Ils lisent la page servie (`HTML_PAGE`) et son script,
comme les autres contrôles statiques du dépôt ; les gestes eux-mêmes sont joués
touche par touche dans `tests/navigateur_interface.mjs`, et mesurés pour de bon
par `outils/captures_ecran.mjs` dans un Chromium.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from simulateur.interface import HTML_PAGE  # noqa: E402


def _script(page: str) -> str:
    return "\n".join(re.findall(r"<script>(.*?)</script>", page, re.S))


def _corps(script: str, nom: str) -> str:
    """Le corps d'une fonction déclarée, accolades comprises.

    On compte les accolades : une fonction qui en renferme une autre (le
    gestionnaire de touches en contient) ne se lit pas à la première fermante.
    """
    debut = script.index(f"function {nom}(")
    ouvrante = script.index("{", debut)
    niveau = 0
    for position in range(ouvrante, len(script)):
        if script[position] == "{":
            niveau += 1
        elif script[position] == "}":
            niveau -= 1
            if niveau == 0:
                return script[ouvrante:position + 1]
    raise AssertionError(f"la fonction {nom} n'est pas refermée")


class TestLaFenetreEstUnDialogue(unittest.TestCase):
    """Une fenêtre annoncée comme telle, et visable par le script."""

    @classmethod
    def setUpClass(cls):
        cls.page = HTML_PAGE
        cls.script = _script(cls.page)

    def test_le_dialogue_est_annonce_comme_tel(self):
        """`role="dialog"`, modal, titré — et le titre existe vraiment."""
        balise = re.search(r"<div class=\"modale\"[^>]*>", self.page)
        self.assertIsNotNone(balise, "la fenêtre a perdu son conteneur")
        attributs = balise.group(0)
        self.assertIn('role="dialog"', attributs)
        self.assertIn('aria-modal="true"', attributs)
        reference = re.search(r'aria-labelledby="([^"]+)"', attributs)
        self.assertIsNotNone(reference, "la fenêtre n'annonce plus son titre")
        self.assertIn(f'id="{reference.group(1)}"', self.page,
                      "la fenêtre renvoie à un titre qui n'existe pas")

    def test_la_fenetre_peut_recevoir_le_focus(self):
        """`tabindex="-1"` : sans lui, un navigateur refuse de la viser.

        C'est la seule chose que la doublure de Node ne peut pas vérifier — un
        nœud sans `tabindex` n'y change rien, alors qu'un vrai navigateur laisse
        le focus sur le corps du document et le lecteur au clavier nulle part.
        """
        balise = re.search(r"<div class=\"modale\"[^>]*>", self.page)
        self.assertIn('tabindex="-1"', balise.group(0),
                      "la fenêtre ne peut plus être visée par le focus")

    def test_la_fenetre_se_ferme_toujours_de_trois_facons(self):
        """Le bouton, le clic dehors, la touche — rien n'a été perdu."""
        self.assertIn('onclick="fermerModale()"', self.page)
        self.assertIn("siClicDehors(event)", self.page)
        self.assertIn("function siClicDehors(", self.script)
        self.assertIn("Escape", _corps(self.script, "initialiserModale"))


class TestLeFocusEntreEtSort(unittest.TestCase):
    """Les trois gestes : entrer, rester, revenir."""

    @classmethod
    def setUpClass(cls):
        cls.script = _script(HTML_PAGE)

    def test_la_fenetre_retient_qui_l_a_ouverte(self):
        """Le focus ne rentre pas tout seul, et il ne revient pas à personne."""
        corps = _corps(self.script, "ouvrirModale")
        self.assertIn("fenetreOrigine", corps,
                      "la fenêtre n'a plus mémoire de qui l'a ouverte")
        self.assertIn("document.activeElement", corps)
        self.assertIn("donnerLeFocusALaFenetre()", corps,
                      "ouvrir la fenêtre ne donne plus le focus")

    def test_le_focus_entre_dans_la_fenetre(self):
        """Viser la fenêtre, et refuser de casser si le navigateur dit non."""
        corps = _corps(self.script, "donnerLeFocusALaFenetre")
        self.assertIn("getElementById('modale')", corps)
        self.assertIn(".focus()", corps)
        self.assertIn("try", corps, "un focus refusé doit pouvoir l'être sans casse")

    def test_le_focus_revient_a_qui_l_a_ouvert(self):
        corps = _corps(self.script, "fermerModale")
        self.assertIn("rendreLeFocus()", corps,
                      "refermer la fenêtre ne rend plus le focus")

    def test_sans_porteur_le_focus_va_a_la_commande_principale(self):
        """Le guide s'ouvre tout seul : personne, alors, ne l'a ouvert.

        Rendre le focus au corps du document laisserait le lecteur au clavier
        sans point de départ. Il prend la commande principale — celle par où
        l'on commence, juste sous la fenêtre refermée.
        """
        corps = _corps(self.script, "rendreLeFocus")
        self.assertIn("btn-simuler", corps,
                      "le repli du focus a disparu : le guide de première visite "
                      "rendrait le focus au corps du document")

    def test_un_element_range_ne_reprend_pas_le_focus(self):
        """Un bouton de tiroir refermé n'a plus de boîte : le viser ne mène nulle part."""
        corps = _corps(self.script, "peutPrendreLeFocus")
        self.assertIn("estVisible", corps,
                      "la fenêtre ne vérifie plus que ce qu'elle vise est bien rendu")
        self.assertIn("document.body", corps)
        self.assertIn("document.documentElement", corps)
        visible = _corps(self.script, "estVisible")
        self.assertIn("getClientRects", visible)
        self.assertIn("disabled", visible)


class TestLaTabulationNeSortPas(unittest.TestCase):
    """Tant que la fenêtre est ouverte, le clavier reste dedans."""

    @classmethod
    def setUpClass(cls):
        cls.script = _script(HTML_PAGE)

    def test_les_commandes_de_la_fenetre_sont_énumérées(self):
        """Les six familles de commandes — la constante s'écrit en deux morceaux."""
        self.assertIn("COMMANDES_FENETRE", self.script)
        declaration = re.search(r"COMMANDES_FENETRE = (.*?);", self.script, re.S)
        self.assertIsNotNone(declaration, "la liste des commandes de la fenêtre a disparu")
        liste = "".join(re.findall(r"'([^']*)'", declaration.group(1)))
        for famille in ("a[href]", "button", "summary", "input", "select", "textarea"):
            self.assertIn(famille, liste, f"{famille} a quitté la liste des commandes")
        self.assertNotIn("tabindex", liste,
                         "la fenêtre elle-même ne doit pas être une étape de tabulation")

    def test_la_tabulation_est_retenue_aux_deux_bouts(self):
        """Le dernier commande la première, la première commande la dernière."""
        corps = _corps(self.script, "retenirLeFocus")
        self.assertIn("shiftKey", corps, "la tabulation arrière n'est plus traitée")
        self.assertIn("preventDefault", corps,
                      "sans preventDefault, le navigateur sort de la fenêtre")
        self.assertIn("dernier", corps)
        self.assertIn("premier", corps)
        # Le parcours circulaire : chaque bout renvoie à l'autre.
        self.assertRegex(corps, r"premier\.focus\(\)")
        self.assertRegex(corps, r"dernier\.focus\(\)")

    def test_la_touche_tab_est_traitee_quand_la_fenetre_est_ouverte(self):
        corps = _corps(self.script, "initialiserModale")
        self.assertIn("'Tab'", corps)
        self.assertIn("retenirLeFocus", corps)

    def test_echap_ne_ferme_que_ce_qui_est_ouvert(self):
        """Ailleurs, la touche reste au navigateur : quitter un champ, arrêter un chargement."""
        corps = _corps(self.script, "initialiserModale")
        self.assertIn("fenetreVisible()", corps,
                      "Échap est de nouveau capté sans condition")
        self.assertRegex(corps, r"if \(ouverte\) fermerModale\(\)")

    def test_un_focus_perdu_revient_dans_la_fenetre(self):
        """Le cas du pointeur : le focus a pu partir ailleurs, on le ramène."""
        corps = _corps(self.script, "retenirLeFocus")
        self.assertIn("indexOf", corps,
                      "la fenêtre ne vérifie plus si le focus est encore chez elle")


class TestLeGuideParLAdresse(unittest.TestCase):
    """« ?guide=1 » : montrer l'accueil de l'outil à la demande."""

    @classmethod
    def setUpClass(cls):
        cls.script = _script(HTML_PAGE)

    def test_l_adresse_peut_demander_le_guide(self):
        corps = _corps(self.script, "lienDemandeLeGuide")
        self.assertIn("URLSearchParams", corps)
        self.assertIn("'guide'", corps)
        self.assertIn("try", corps, "une adresse illisible doit être sans effet")

    def test_le_guide_demande_ne_se_note_pas_comme_vu(self):
        """Sinon la démonstration d'aujourd'hui priverait de guide la visite de demain."""
        depart = self.script.index("if (lienDemandeLeGuide())")
        bloc = self.script[depart:self.script.index("rendreTableauxDefilants", depart)]
        self.assertIn("ouvrirGuide()", bloc)
        marquage = bloc.index("marquerGuideVu()")
        # Le marquage vit dans la branche « première visite », pas dans celle de
        # l'adresse : entre les deux, l'alternative explicite doit se lire.
        self.assertIn("else if (!guideDejaVu())", bloc[:marquage],
                      "le guide demandé par l'adresse est noté comme lu")
        self.assertEqual(bloc.count("marquerGuideVu()"), 1)
        self.assertLess(bloc.index("else if"), marquage)
        # Et le guide s'ouvre bien dans les deux cas.
        self.assertEqual(bloc.count("ouvrirGuide()"), 2)


if __name__ == "__main__":
    unittest.main()
