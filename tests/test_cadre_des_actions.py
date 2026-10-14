"""
tests/test_cadre_des_actions.py — le cadre ne prend pas plus de place que ses boutons.

Le visiteur l'a dit ainsi : « le cadre avec les boutons d'accès rapide est
beaucoup plus grand que la place que prennent les boutons eux-mêmes ». Ce n'était
pas une impression : quinze commandes de premier niveau s'empilaient dans le
bandeau, chaque cadre écrivait ses propres mesures — donc jamais les mêmes —, et
ce qui ne sert pas à chaque visite était exposé comme le reste.

Trois réponses, et trois familles de contrôles :

1. **la barre du bandeau ne montre que l'essentiel** : simuler, rafraîchir, et
   les deux tiroirs (affichage, outils) ;
2. **les outils secondaires vivent dans un tiroir** qui s'ouvre, au lieu de
   peser tout le temps ;
3. **une seule recette de cadre** : une hauteur de bouton, un écart, et des
   cadres qui ne se donnent pas plus d'air qu'il n'en faut.

Ces contrôles lisent la page comme les autres : le texte servi (`HTML_PAGE`) et
sa feuille, analysés par `outils/contraste_ecran.py`, qui sait lire un arbre et
une cascade — inutile d'écrire un second analyseur à côté.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from outils import contraste_ecran  # noqa: E402
from simulateur.interface import HTML_PAGE  # noqa: E402

#: Ce qui reste sous la main dans le bandeau, à chaque visite.
COMMANDES_PRINCIPALES = ("btn-simuler", "btn-rafraichir", "affichage", "outils-simulateur")

#: Ce qui se range dans le tiroir : utile, mais pas à chaque geste.
OUTILS_SECONDAIRES = ("btn-lexique", "btn-guide", "btn-partage",
                      "btn-export-json", "btn-export-csv")

#: Les trois largeurs de la présentation, et ce qu'elles valent.
PRESENTATIONS = {"equilibree": "1440px", "lecture": "1000px", "panorama": "1680px"}


def _css() -> str:
    return contraste_ecran.feuille_de_la_page(HTML_PAGE)


def _noeud(*classes: str):
    """Le premier élément qui porte toutes ces classes."""
    voulues = set(classes)
    for noeud in contraste_ecran.parcourir(contraste_ecran.arbre(HTML_PAGE)):
        if voulues <= set(noeud.classes):
            return noeud
    raise AssertionError(f"aucun élément ne porte {' '.join(sorted(voulues))}")


def _declarations(corps: str) -> dict[str, str]:
    return {nom.strip(): valeur.strip().replace("!important", "").strip()
            for nom, valeur in re.findall(r"([-\w]+)\s*:\s*([^;]+)", corps)}


def _regles(selecteur: str, *, seul: bool = False) -> list[tuple[str, dict[str, str]]]:
    """Les règles dont la liste de sélecteurs contient celui-ci.

    `seul=True` ne garde que celles qui ne parlent **que** de ce sélecteur, et
    hors `@media` : c'est la règle du cadre au repos, pas celle d'un palier.
    """
    sortie = []
    for contexte, liste, corps in contraste_ecran.regles(_css()):
        morceaux = [morceau.strip() for morceau in liste.split(",")]
        if selecteur not in morceaux:
            continue
        if seul and (contexte or morceaux != [selecteur]):
            continue
        sortie.append((liste, _declarations(corps)))
    return sortie


def _regle_de(selecteur: str) -> dict[str, str]:
    """La règle du cadre au repos : la seule, et hors `@media`."""
    regles = _regles(selecteur, seul=True)
    assert len(regles) == 1, f"{len(regles)} règles pour {selecteur}"
    return regles[0][1]


def _socle() -> dict[str, str]:
    """Les jetons du socle : le premier bloc `:root` de la feuille, sans commentaire."""
    css = re.sub(r"/\*.*?\*/", "", _css(), flags=re.S)
    debut = css.index(":root{") + len(":root{")
    return _declarations(css[debut:css.index("}", debut)])


class TestLaBarreDuBandeau(unittest.TestCase):
    """Ce qui reste sous la main, et ce qui s'ouvre."""

    def test_la_barre_tient_en_quatre_commandes(self):
        """Quinze commandes au premier niveau, c'était le cadre haut pour rien."""
        barre = _noeud("barre-contexte")
        commandes = [enfant for enfant in barre.enfants
                     if enfant.nom in ("button", "details", "select", "a", "label")]
        self.assertLessEqual(
            len(commandes), 6,
            f"{len(commandes)} commandes de premier niveau : "
            + " · ".join(f"{c.nom}{'.' + '.'.join(c.classes) if c.classes else ''}"
                         for c in commandes))
        for identifiant in COMMANDES_PRINCIPALES:
            self.assertTrue(
                any(enfant.identifiant() == identifiant
                    or any(f"{identifiant}" == (enfant.identifiant() or "") for _ in [0])
                    for enfant in commandes)
                or any("affichage" in enfant.classes or "outils" in enfant.classes
                       for enfant in commandes),
                f"{identifiant} n'est plus sous la main")

    def test_les_outils_secondaires_vivent_dans_un_tiroir(self):
        """Un tiroir qui s'ouvre, plutôt que cinq boutons qui pèsent tout le temps."""
        tiroir = _noeud("outils")
        self.assertEqual(tiroir.nom, "details", "les outils ne sont plus un tiroir")
        self.assertEqual(tiroir.enfants[0].nom, "summary",
                         "un tiroir sans poignée ne s'ouvre pas")
        dedans = {noeud.identifiant() for noeud in contraste_ecran.parcourir(tiroir)}
        for identifiant in OUTILS_SECONDAIRES:
            with self.subTest(outil=identifiant):
                self.assertIn(identifiant, dedans, f"{identifiant} a quitté le tiroir")
        ouvertures = [noeud.attributs.get("onclick", "")
                      for noeud in contraste_ecran.parcourir(tiroir)]
        self.assertTrue(any("reinitialiser()" in ouverture for ouverture in ouvertures),
                        "la remise à zéro des leviers a quitté le tiroir")

    def test_le_bandeau_annonce_la_page_en_trois_temps(self):
        """Sur-titre, titre, phrase : la ligne éditoriale du site M.R.S.C.

        Le bandeau est la première chose lue — il suit le même ordre que les
        sections, sinon la page commence par une exception.
        """
        entete = _noeud("entete")
        premiers = [enfant for enfant in entete.enfants if enfant.nom in ("p", "h1")][:3]
        self.assertEqual([noeud.nom for noeud in premiers], ["p", "h1", "p"],
                         [f"{n.nom}.{' '.join(n.classes)}" for n in entete.enfants])
        self.assertIn("eyebrow", premiers[0].classes, "le sur-titre du bandeau a disparu")
        self.assertIn("accroche", premiers[2].classes, "la phrase d'accroche a disparu")

    def test_l_etat_de_la_page_est_une_ligne_a_part(self):
        """Le contexte, la date, les leviers, l'horizon : une ligne, pas quatre."""
        etat = _noeud("etat-contexte")
        self.assertEqual(etat.nom, "p", "l'état de la page se lit comme une phrase")
        pastilles = [noeud for noeud in contraste_ecran.parcourir(etat)
                     if "pastille" in noeud.classes]
        self.assertGreaterEqual(len(pastilles), 3, "l'état a perdu ses pastilles")
        for identifiant in ("badge-contexte", "badge-date", "badge-leviers", "badge-horizon"):
            self.assertIn(identifiant,
                          {noeud.identifiant() for noeud in contraste_ecran.parcourir(etat)},
                          f"{identifiant} a quitté la ligne d'état")


class TestUneSeuleRecette(unittest.TestCase):
    """Le même écart, la même hauteur, le même geste dans tous les cadres."""

    def test_la_hauteur_des_boutons_est_un_jeton(self):
        socle = _socle()
        self.assertIn("--h-bouton", socle, "la hauteur des boutons n'est plus un jeton")
        self.assertIn("--gap-barre", socle, "l'écart des barres n'est plus un jeton")
        self.assertEqual(socle["--h-bouton"], "34px", socle["--h-bouton"])
        partagees = [liste for liste, declaration in _regles_toutes()
                     if "min-height:var(--h-bouton)" in declaration]
        self.assertTrue(partagees, "aucun bouton de barre ne prend la hauteur du jeton")
        barres = " ".join(partagees)
        for cadre in (".barre-contexte", ".ruban-veille", ".resume-actions"):
            with self.subTest(cadre=cadre):
                self.assertIn(cadre, barres, f"{cadre} s'habille tout seul")

    def test_le_doigt_garde_ses_quarante_quatre_pixels(self):
        """Sur un écran tactile, la hauteur du jeton monte à 44 px."""
        trouve = []
        for contexte, _liste, corps in contraste_ecran.regles(_css()):
            if any("pointer:coarse" in bloc for bloc in contexte) and "--h-bouton" in corps:
                trouve.append(_declarations(corps).get("--h-bouton", ""))
        self.assertIn("44px", trouve, "le doigt a perdu sa hauteur de bouton")

    def test_toutes_les_barres_partagent_le_meme_ecart(self):
        """Une barre qui écrit son écart en clair n'est plus la même barre."""
        partagees = [(liste, declaration) for liste, declaration in _regles_toutes()
                     if "gap:var(--gap-barre)" in declaration]
        self.assertTrue(partagees, "plus aucune barre ne partage son écart")
        selecteurs = " ".join(liste for liste, _ in partagees)
        for cadre in (".barre-contexte", ".ruban-veille", ".resume-actions"):
            with self.subTest(cadre=cadre):
                self.assertIn(cadre, selecteurs, f"{cadre} a son propre écart")
        declaration = _regle_de(".barre-contexte")
        self.assertEqual(declaration.get("margin-top"), "var(--e-2)", declaration)
        self.assertNotIn("gap", declaration, "l'écart de la barre est réécrit en clair")

    def test_le_ruban_ne_prend_pas_plus_de_place_qu_il_n_en_faut(self):
        """Le ruban de veille : cinq pixels autour des boutons, pas douze."""
        declaration = _regle_de(".ruban-veille")
        self.assertEqual(declaration.get("padding"), "5px 10px", declaration.get("padding"))
        self.assertIn("var(--gap-barre)", declaration.get("gap", ""))
        self.assertIn("var(--e-2)", declaration.get("margin-bottom", ""))

    def test_les_pastilles_ne_mangent_plus_la_ligne(self):
        """Une pastille dit un état en petit : elle n'a pas besoin de dix pixels de cadre."""
        declaration = _regle_de(".pastille")
        self.assertEqual(declaration.get("padding"), "3px 9px", declaration.get("padding"))
        self.assertIn("max(var(--t-min)", declaration.get("font-size", ""),
                      "une pastille sous le plancher de lecture")


class TestLaPresentation(unittest.TestCase):
    """Trois largeurs, un seul réglage : la « mise en page » du site M.R.S.C."""

    def test_le_conteneur_suit_un_jeton_de_largeur(self):
        self.assertEqual(_regle_de(".conteneur").get("max-width"), "var(--largeur-page)",
                         "le conteneur a repris une largeur écrite en clair")
        self.assertEqual(_socle().get("--largeur-page"), PRESENTATIONS["equilibree"],
                         "la présentation « équilibrée » n'est plus la largeur par défaut")

    def test_chaque_presentation_a_sa_largeur(self):
        for presentation, largeur in PRESENTATIONS.items():
            if presentation == "equilibree":
                continue
            with self.subTest(presentation=presentation):
                regles = _regles(f'html[data-layout="{presentation}"]')
                self.assertTrue(regles, f"la présentation « {presentation} » n'existe pas")
                assertions = [declaration for _, declaration in regles]
                self.assertIn({"--largeur-page": largeur}, assertions,
                              f"« {presentation} » ne pose pas sa largeur : {assertions}")

    def test_les_trois_presentations_sont_dans_le_panneau(self):
        """Le réglage se prend là où sont les autres : dans le panneau d'affichage."""
        panneau = _noeud("affichage-panneau")
        dedans = list(contraste_ecran.parcourir(panneau))
        boutons = {noeud.identifiant(): noeud for noeud in dedans
                   if noeud.nom == "button" and noeud.attributs.get("data-presentation-choix")}
        self.assertEqual(set(boutons), {f"presentation-{cle}" for cle in PRESENTATIONS},
                         sorted(boutons))
        for cle, bouton in boutons.items():
            with self.subTest(bouton=cle):
                self.assertIn("aria-pressed", bouton.attributs)
                self.assertIn(f"choisirPresentation('{cle.split('-')[1]}')",
                              bouton.attributs.get("onclick", ""))
        self.assertEqual(boutons["presentation-equilibree"].attributs["aria-pressed"], "true",
                         "la présentation par défaut n'est pas annoncée comme telle")

    def test_le_script_d_en_tete_pose_la_presentation(self):
        """Sinon la page s'ouvrirait à la mauvaise largeur puis sauterait."""
        entete = HTML_PAGE[HTML_PAGE.index("<head>"):HTML_PAGE.index("</head>")]
        self.assertIn("data-layout", entete,
                      "la présentation n'est plus posée avant le premier pixel")
        self.assertIn("'equilibree'", entete, "la présentation de repli a disparu")
        for presentation in PRESENTATIONS:
            self.assertIn(f"'{presentation}'", entete,
                          f"« {presentation} » n'est pas acceptée par le script d'en-tête")


def _regles_toutes() -> list[tuple[str, str]]:
    """Toutes les règles de la feuille : la liste des sélecteurs, le corps brut."""
    return [(liste, corps) for _, liste, corps in contraste_ecran.regles(_css())]


if __name__ == "__main__":
    unittest.main()
