"""tests/test_themes_en_page.py — la lisibilité des quatre thèmes, mesurée.

La page propose quatre thèmes (soir, jour, crème, contraste renforcé), deux
densités et cinq tailles de texte. Ces contrôles ne vérifient pas qu'un jeton
existe : ils **calculent** ce que l'œil reçoit.

Trois choses sont mesurées, et une seule manière de les mesurer :

* **le contraste**, avec la formule WCAG 2.1 de `outils/couleurs.py` — chaque
  couleur de texte, résolue depuis la palette du thème, posée sur le fond réel
  que la règle lui donne. Un thème qui écrit `color:#fff` sur un rouge vif est
  refusé, même si la maquette était jolie ;
* **la hiérarchie éditoriale** : chaque section porte un sur-titre, un titre et
  une phrase, le sur-titre prend le trait vert de la charte, et les phrases sont
  des phrases (majuscule, point) ;
* **les réglages du visiteur** : les quatre thèmes existent, les deux densités
  sont déclarées, les cinq tailles aussi, le choix se garde sur l'appareil et
  ne part jamais au serveur.

Ce que ces contrôles ne font pas : juger du goût. Ils refusent ce qui se lit
mal, pas ce qui déplaît.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from outils import couleurs  # noqa: E402
from simulateur.interface import HTML_PAGE  # noqa: E402

THEMES = ("soir", "jour", "creme", "contraste")
SEUIL_TEXTE = 4.5          # WCAG 2.1 AA, texte courant
SEUIL_TEXTE_PRINCIPAL = 7.0  # le corps de texte : AAA, et il ne doit jamais en approcher

#: Les jetons sans lesquels une règle de la feuille tomberait dans le vide.
JETONS_INDISPENSABLES = (
    "--bg", "--panel", "--panel-2", "--panel-3", "--border", "--border-fin",
    "--texte", "--texte-dim", "--accent", "--vert", "--rouge", "--ambre",
    "--violet", "--encre-pleine", "--sur-mrsc",
    "--mrsc-navy", "--mrsc-bleu", "--mrsc-vert", "--mrsc-or", "--mrsc-rouge",
    "--ombre", "--ombre-forte", "--ombre-modale", "--voile",
    "--classe-recettes", "--classe-depenses",
    "--classe-recettes-fond", "--classe-depenses-fond",
)

#: Les couleurs de sens, mesurées sur les deux fonds de carte.
TEINTES_DE_SENS = ("--accent", "--vert", "--rouge", "--ambre", "--violet")


def _css() -> str:
    return HTML_PAGE[HTML_PAGE.index("<style>") + len("<style>"):HTML_PAGE.index("</style>")]


def _corps() -> str:
    """Le corps du document, sans le script de l'application."""
    debut = HTML_PAGE.index("<body>")
    return HTML_PAGE[debut:HTML_PAGE.index("<script", debut)]


def _sans_commentaires(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _palette(nom: str) -> dict[str, str]:
    motif = re.compile(
        rf"(?:^|\n)(?:\[data-theme=\"{nom}\"\]|:root,\[data-theme=\"{nom}\"\])\{{(.*?)\n\}}", re.S)
    trouve = motif.search(_css())
    assert trouve, f"palette de thème absente : {nom}"
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", trouve.group(1)))


def _blocs(texte: str, contexte: tuple[str, ...] = ()):
    """Toutes les règles d'une feuille, avec le @media / @supports qui les porte."""
    sortie, position = [], 0
    while position < len(texte):
        ouvrante = texte.find("{", position)
        if ouvrante < 0:
            break
        entete = texte[position:ouvrante].strip()
        niveau, curseur = 1, ouvrante + 1
        while niveau and curseur < len(texte):
            if texte[curseur] == "{":
                niveau += 1
            elif texte[curseur] == "}":
                niveau -= 1
            curseur += 1
        corps = texte[ouvrante + 1:curseur - 1]
        if entete.startswith("@"):
            sortie.extend(_blocs(corps, contexte + (entete,)))
        else:
            sortie.append((contexte, entete, corps))
        position = curseur
    return sortie


def _regles_visibles():
    """Les règles qui s'appliquent à l'écran — ni l'impression, ni les couleurs forcées."""
    for contexte, selecteur, corps in _blocs(_sans_commentaires(_css())):
        if any("print" in bloc or "forced-colors" in bloc for bloc in contexte):
            continue
        yield selecteur, corps


def _regle(selecteur: str) -> dict[str, str]:
    for candidat, corps in _regles_visibles():
        if candidat.strip().split(",")[0].strip() == selecteur:
            return dict(re.findall(r"([-\w]+)\s*:\s*([^;]+)", corps))
    return {}


def _derniere_regle(selecteur: str) -> dict[str, str]:
    """La dernière règle d'un sélecteur : dans une feuille, la dernière gagne."""
    trouve = {}
    for candidat, corps in _regles_visibles():
        if candidat.strip().split(",")[0].strip() == selecteur:
            trouve = dict(re.findall(r"([-\w]+)\s*:\s*([^;]+)", corps))
    return trouve


def _couleur(expression: str, variables: dict[str, str]):
    return couleurs.resoudre(expression, variables)


def _fond_de_la_regle(valeur: str, variables: dict[str, str], dessous):
    """Le fond réellement peint : un dégradé prend son premier arrêt."""
    valeur = valeur.strip()
    if valeur.endswith(")") and ("gradient(" in valeur):
        arret = re.split(r",(?![^()]*\))", valeur[valeur.index("(") + 1:-1])[0]
        return _couleur(re.split(r"\s+\d", arret)[0], variables)
    return _couleur(valeur, variables)


class TestLesQuatreThemes(unittest.TestCase):
    """Ce que chaque thème doit déclarer pour que la page tienne debout."""

    def test_chaque_theme_declare_les_memes_jetons(self):
        """Un jeton manquant dans un seul thème, et la règle tombe dans le vide.

        Le contrôle compare les **noms**, jamais les valeurs : c'est ce qui
        permet d'ajouter une teinte à un thème sans laisser les trois autres
        en arrière.
        """
        noms = {theme: set(_palette(theme)) for theme in THEMES}
        self.assertGreaterEqual(len(noms["soir"]), 44, f"palette trop pauvre : {len(noms['soir'])} jetons")
        for theme, jetons in noms.items():
            with self.subTest(theme=theme):
                self.assertEqual(jetons, noms["soir"],
                                 f"jetons manquants ou en trop en « {theme} » : "
                                 f"{sorted(jetons ^ noms['soir'])}")

    def test_chaque_theme_annonce_son_sens_au_navigateur(self):
        """`color-scheme` décide des barres de défilement et des champs natifs."""
        clairs = [theme for theme in THEMES if "color-scheme:light" in _bloc_de_theme(theme)]
        sombres = [theme for theme in THEMES if "color-scheme:dark" in _bloc_de_theme(theme)]
        self.assertEqual(sorted(clairs), ["creme", "jour"])
        self.assertEqual(sorted(sombres), ["contraste", "soir"])

    def test_les_jetons_indispensables_existent_partout(self):
        for theme in THEMES:
            palette = _palette(theme)
            for jeton in JETONS_INDISPENSABLES:
                with self.subTest(theme=theme, jeton=jeton):
                    self.assertIn(jeton, palette, f"{jeton} absent du thème « {theme} »")
                    self.assertTrue(palette[jeton].strip(), f"{jeton} vide en « {theme} »")

    def test_aucun_jeton_ne_se_definit_lui_meme(self):
        """`--panel:var(--panel)` est une boucle silencieuse : la couleur disparaît.

        Le cas s'est produit : une réécriture de palette avait remplacé des
        valeurs par leurs propres noms, et les fonds devenaient transparents
        sans qu'aucun contrôle ne le voie.
        """
        for theme in THEMES:
            for jeton, valeur in _palette(theme).items():
                with self.subTest(theme=theme, jeton=jeton):
                    self.assertNotIn(f"var({jeton})", valeur,
                                     f"{jeton} se lit lui-même dans le thème « {theme} »")

    def test_toute_valeur_de_couleur_se_resout(self):
        """Un jeton qui ne se calcule pas est un jeton qui ne s'affichera pas."""
        obscurs = []
        for theme in THEMES:
            palette = _palette(theme)
            for jeton, valeur in palette.items():
                if jeton.startswith(("--ombre", "--voile")) or "gradient" in valeur:
                    continue
                if couleurs.resoudre(valeur, palette) is None:
                    obscurs.append(f"{theme}{jeton}")
        self.assertEqual(obscurs, [], f"jetons illisibles : {obscurs}")

    def test_le_theme_de_l_appareil_est_lu_par_la_page_pas_par_la_feuille(self):
        """`prefers-color-scheme` n'appartient pas au CSS : le choix se fait en JS.

        Sinon un thème clair choisi à la main resterait écrasé par le réglage du
        système — l'exact contraire de ce que le visiteur vient de demander.
        """
        self.assertNotIn("prefers-color-scheme", _sans_commentaires(_css()))
        self.assertIn("prefers-color-scheme: light", HTML_PAGE)


def _bloc_de_theme(nom: str) -> str:
    motif = re.compile(
        rf"(?:^|\n)(?:\[data-theme=\"{nom}\"\]|:root,\[data-theme=\"{nom}\"\])\{{(.*?)\n\}}", re.S)
    trouve = motif.search(_css())
    return trouve.group(1) if trouve else ""


class TestLesJetonsSontBranches(unittest.TestCase):
    """Un jeton employé mais jamais défini ne se voit pas : il disparaît."""

    def test_aucune_variable_employee_n_est_absente(self):
        """Toute `var(--x)` de la feuille doit être définie quelque part.

        Le cas s'est produit : les deux plateaux de la balance lisaient
        `--classe-recettes-fond` et `--classe-depenses-fond`, disparus d'une
        réécriture de palette. Le fond devenait transparent, et rien ne le
        disait — un navigateur ne se plaint pas d'une variable absente.
        """
        css = _sans_commentaires(_css())
        definies = set(re.findall(r"(--[\w-]+)\s*:", css))
        # La page pose aussi des variables en ligne (style="--teinte:…") et le
        # script en calcule (setProperty) : elles comptent comme définies.
        reste = HTML_PAGE[HTML_PAGE.index("</style>"):]
        definies |= set(re.findall(r"(--[\w-]+)\s*:", reste))
        definies |= set(re.findall(r"setProperty\(\s*['\"](--[\w-]+)", reste))
        employees = set(re.findall(r"var\(\s*(--[\w-]+)", css))
        self.assertGreater(len(employees), 40, "la feuille n'emploie presque aucune variable")
        self.assertEqual(sorted(employees - definies), [],
                         "variables employées mais jamais définies")

    def test_les_deux_plateaux_de_la_balance_suivent_la_variable_de_classe(self):
        """La teinte des plateaux se calcule, et son repli est écrit juste.

        La règle emploie `color-mix()` sur la variable de classe ; la première
        déclaration, elle, est un repli que lisent les navigateurs qui ne
        comprennent pas `color-mix`. Ce repli doit valoir **exactement** ce que
        le mélange produit, sinon deux navigateurs affichent deux fonds
        différents — et la proportion, elle, est mesurée : à 14 % le texte
        secondaire passait sous 4,5:1 en « jour ».
        """
        part = 12  # pour cent, comme `color-mix(in srgb, … 12%, …)`
        for theme in THEMES:
            palette = _palette(theme)
            panneau = _couleur("var(--panel)", palette)
            for classe, fond in (("--classe-recettes", "--classe-recettes-fond"),
                                 ("--classe-depenses", "--classe-depenses-fond")):
                with self.subTest(theme=theme, jeton=fond):
                    self.assertIn(fond, palette, f"{fond} manquant en « {theme} »")
                    declaree = _couleur(f"var({fond})", palette)
                    composee = couleurs.melanger(_couleur(f"var({classe})", palette), panneau, part)
                    self.assertIsNotNone(declaree)
                    self.assertLessEqual(
                        max(abs(a - b) for a, b in zip(declaree[:3], composee[:3], strict=True)), 1.0,
                        f"{theme} : {fond} ne vaut pas {part} % de {classe} sur --panel")
            # La règle, elle, se relit : c'est elle qui peint. Une proportion
            # écrite dans le CSS et une autre dans le jeton repli, et deux
            # navigateurs affichent deux fonds — ou un texte illisible.
            for selecteur, jeton in ((".balance-cote.entrees", "--classe-recettes"),
                                     (".balance-cote.sorties", "--classe-depenses")):
                with self.subTest(theme=theme, regle=selecteur):
                    regle = _regle(selecteur)
                    melanges = re.findall(r"color-mix\(in srgb,var\((--[\w-]+)\) (\d+)%", regle.get("background", ""))
                    self.assertTrue(melanges, f"{selecteur} : la teinte n'est plus calculée")
                    for reference, pourcentage in melanges:
                        self.assertEqual(reference, jeton)
                        self.assertEqual(int(pourcentage), part,
                                         f"{selecteur} : {pourcentage} % au lieu de {part} %")
                        teinte = couleurs.melanger(_couleur(f"var({reference})", palette),
                                                   _couleur("var(--panel)", palette), int(pourcentage))
                        for encre in ("--texte", "--texte-dim"):
                            rapport = couleurs.contraste(_couleur(f"var({encre})", palette), teinte)
                            self.assertGreaterEqual(
                                rapport, SEUIL_TEXTE,
                                f"{theme} : {encre} sur la teinte de {selecteur} = {rapport:.2f}:1")

            # Le texte posé sur ces fonds, y compris le plus petit.
            for fond in ("--classe-recettes-fond", "--classe-depenses-fond"):
                for encre in ("--texte", "--texte-dim"):
                    with self.subTest(theme=theme, fond=fond, encre=encre):
                        rapport = couleurs.contraste(_couleur(f"var({encre})", palette),
                                                     _couleur(f"var({fond})", palette))
                        self.assertGreaterEqual(
                            rapport, SEUIL_TEXTE,
                            f"{theme} : {encre} sur {fond} = {rapport:.2f}:1")


class TestContrastesDesQuatreThemes(unittest.TestCase):
    """Le contrôle qui compte : ce que l'œil reçoit, thème par thème."""

    def test_le_texte_principal_se_lit_sur_les_quatre_fonds(self):
        for theme in THEMES:
            palette = _palette(theme)
            avant = _couleur("var(--texte)", palette)
            for fond in ("--bg", "--panel", "--panel-2", "--panel-3"):
                with self.subTest(theme=theme, fond=fond):
                    rapport = couleurs.contraste(avant, _couleur(f"var({fond})", palette))
                    self.assertIsNotNone(rapport, f"{theme} : --texte sur {fond} illisible")
                    self.assertGreaterEqual(
                        rapport, SEUIL_TEXTE_PRINCIPAL,
                        f"{theme} : --texte sur {fond} = {rapport:.2f}:1, sous le seuil de {SEUIL_TEXTE_PRINCIPAL}")

    def test_le_texte_secondaire_se_lit_sur_les_deux_panneaux(self):
        """Les mentions en petit (dates, unités, légendes) restent lisibles."""
        for theme in THEMES:
            palette = _palette(theme)
            avant = _couleur("var(--texte-dim)", palette)
            for fond in ("--panel", "--panel-2"):
                with self.subTest(theme=theme, fond=fond):
                    rapport = couleurs.contraste(avant, _couleur(f"var({fond})", palette))
                    self.assertGreaterEqual(rapport, SEUIL_TEXTE,
                                            f"{theme} : --texte-dim sur {fond} = {rapport:.2f}:1")

    def test_les_teintes_de_sens_se_lisent_sur_le_panneau(self):
        """Vert, rouge, ambre, violet : des couleurs de texte, pas seulement de fond."""
        for theme in THEMES:
            palette = _palette(theme)
            for jeton in TEINTES_DE_SENS:
                with self.subTest(theme=theme, jeton=jeton):
                    rapport = couleurs.contraste(_couleur(f"var({jeton})", palette),
                                                 _couleur("var(--panel)", palette))
                    self.assertGreaterEqual(rapport, SEUIL_TEXTE,
                                            f"{theme} : {jeton} sur --panel = {rapport:.2f}:1")

    def test_l_encre_pleine_tranche_sur_les_surfaces_vives(self):
        """Les bandeaux pleins (rouge, accent, vert) portent la bonne encre.

        `--encre-pleine` est sombre dans un thème sombre et claire dans un thème
        clair : c'est elle qui rend les pastilles pleines lisibles partout.
        """
        for theme in THEMES:
            palette = _palette(theme)
            avant = _couleur("var(--encre-pleine)", palette)
            for fond in ("--rouge", "--accent", "--vert"):
                with self.subTest(theme=theme, fond=fond):
                    rapport = couleurs.contraste(avant, _couleur(f"var({fond})", palette))
                    self.assertGreaterEqual(rapport, SEUIL_TEXTE,
                                            f"{theme} : --encre-pleine sur {fond} = {rapport:.2f}:1")

    def test_l_encre_de_marque_se_lit_sur_le_bandeau_mrsc(self):
        """Le bandeau M.R.S.C. reste sombre dans les quatre thèmes : l'encre aussi."""
        for theme in THEMES:
            palette = _palette(theme)
            avant = _couleur("var(--sur-mrsc)", palette)
            for fond in ("--mrsc-navy", "--mrsc-bleu"):
                with self.subTest(theme=theme, fond=fond):
                    rapport = couleurs.contraste(avant, _couleur(f"var({fond})", palette))
                    self.assertGreaterEqual(rapport, SEUIL_TEXTE,
                                            f"{theme} : --sur-mrsc sur {fond} = {rapport:.2f}:1")

    def test_aucune_regle_n_ecrit_un_texte_sous_le_seuil(self):
        """Le balayage : toute règle qui écrit une couleur de texte est mesurée.

        Le fond de référence est le panneau, et le second fond de carte — le
        plus clair des deux dans un thème sombre, donc le pire cas. Deux règles
        peignent leur propre fond : elles sont mesurées à part, juste après.
        """
        exceptions = {
            '.onglets-strates button[aria-selected="true"]',
            ".ruban-strate.niveau-hors_sol",
            # Ces deux règles peignent un aplat de marque et écrivent leur
            # encre : c'est `test_aucune_regle_ne_peint_un_aplat_de_marque_…`
            # qui les mesure, sur le fond qu'elles peignent vraiment.
            "button.primaire",
            ".onglets button.actif",
            ".chapitre-num",
        }
        fautes = []
        for selecteur, corps in _regles_visibles():
            declaration = re.search(r"(?<![\w-])color\s*:\s*([^;]+)", corps)
            if not declaration or "var(--" not in declaration.group(1):
                continue
            if selecteur.strip() in exceptions:
                continue
            for theme in THEMES:
                palette = _palette(theme)
                avant = _couleur(declaration.group(1).strip(), palette)
                if avant is None:
                    continue
                for fond in ("--panel", "--panel-2"):
                    rapport = couleurs.contraste(avant, _couleur(f"var({fond})", palette))
                    if rapport is not None and rapport < SEUIL_TEXTE:
                        fautes.append(f"{theme} : {selecteur.strip()[:40]} sur {fond} = {rapport:.2f}:1")
        self.assertEqual(fautes, [], "textes sous le seuil de lisibilité : " + " · ".join(fautes))

    def test_les_deux_regles_a_fond_propre_se_lisent_aussi(self):
        """Un onglet actif et une strate hors-sol portent leur propre fond."""
        for theme in THEMES:
            palette = _palette(theme)
            with self.subTest(theme=theme, regle="strate hors-sol"):
                regle = _regle(".ruban-strate.niveau-hors_sol")
                self.assertIn("var(--rouge)", regle.get("background", ""))
                rapport = couleurs.contraste(_couleur(regle["color"], palette),
                                             _couleur("var(--rouge)", palette))
                self.assertGreaterEqual(rapport, SEUIL_TEXTE,
                                        f"{theme} : strate hors-sol = {rapport:.2f}:1")
            with self.subTest(theme=theme, regle="onglet actif"):
                regle = _regle('.onglets-strates button[aria-selected="true"]')
                encre = _couleur(regle["color"], palette)
                fonds = re.findall(r"var\((--[\w-]+)\)", regle.get("background", ""))
                self.assertTrue(fonds, "l'onglet actif a perdu son fond de marque")
                for fond in fonds:
                    rapport = couleurs.contraste(encre, _couleur(f"var({fond})", palette))
                    self.assertGreaterEqual(rapport, SEUIL_TEXTE,
                                            f"{theme} : onglet actif sur {fond} = {rapport:.2f}:1")

    def test_aucune_regle_ne_peint_un_aplat_de_marque_sans_ecrire_son_encre(self):
        """Le défaut trouvé en vrai : un bouton peint en bleu M.R.S.C. sans encre.

        `button.primaire` peignait le dégradé de marque et laissait l'encre
        s'hériter du thème : bleu nuit sur bleu nuit en « jour » (1,26:1), donc
        invisible. Ce contrôle-ci est structurel : il exige qu'une règle qui
        peint un aplat de marque **écrive** l'encre qui va dessus, et que cette
        encre se lise sur chacun des arrêts du fond.
        """
        fautes = []
        for selecteur, corps in _regles_visibles():
            fond = re.search(r"(?<![\w-])background\s*:\s*([^;]+)", corps)
            if not fond:
                continue
            jetons = [jeton for jeton in re.findall(r"var\((--[\w-]+)\)", fond.group(1))
                      if jeton.startswith("--mrsc-")]
            if not jetons:
                continue
            encre = re.search(r"(?<![\w-])color\s*:\s*([^;]+)", corps)
            if not encre:
                fautes.append(f"{selecteur.strip()[:44]} peint {jetons[0]} sans écrire son encre")
                continue
            for theme in THEMES:
                palette = _palette(theme)
                avant = _couleur(encre.group(1).strip(), palette)
                for jeton in jetons:
                    rapport = couleurs.contraste(avant, _couleur(f"var({jeton})", palette))
                    if rapport is not None and rapport < SEUIL_TEXTE:
                        fautes.append(f"{theme} : {selecteur.strip()[:36]} sur {jeton} = {rapport:.2f}:1")
        self.assertEqual(fautes, [], "aplats de marque sans encre lisible : " + " · ".join(fautes))

    def test_le_bandeau_suit_le_theme_au_lieu_de_la_marque(self):
        """Le fond du bandeau est peint avec les jetons du thème, jamais avec la marque.

        Un dégradé qui partait du bleu M.R.S.C. pour finir dans le papier clair
        laissait la moitié du bandeau sombre sous une encre sombre : c'est ce
        que le visiteur a vu avant tout contrôle.
        """
        regle = _regle("header.entete")
        jetons = re.findall(r"var\((--[\w-]+)\)", regle.get("background", ""))
        self.assertTrue(jetons, "le bandeau n'a plus de fond")
        for jeton in jetons:
            with self.subTest(jeton=jeton):
                self.assertFalse(jeton.startswith("--mrsc-"),
                                 f"le bandeau peint {jeton} : une couleur de marque ne suit pas les thèmes")
        for theme in THEMES:
            palette = _palette(theme)
            avant = _couleur(regle.get("color", "var(--texte)"), palette)
            for jeton in jetons:
                rapport = couleurs.contraste(avant, _couleur(f"var({jeton})", palette))
                self.assertGreaterEqual(rapport, SEUIL_TEXTE,
                                        f"{theme} : l'encre du bandeau sur {jeton} = {rapport:.2f}:1")

    def test_aucune_regle_n_ecrit_de_teinte_en_clair(self):
        """Hors palettes, impression et couleurs forcées, aucune couleur littérale.

        C'est ce qui garantit qu'un thème neuf n'oublie rien : une teinte écrite
        en clair dans une règle ne suivrait aucun des quatre thèmes.
        """
        # `hsl(var(--teinte),58%,52%)` n'est pas une teinte figée : elle vient
        # d'un jeton. Seules les couleurs écrites en dur sont refusées.
        litteral = re.compile(r"#[0-9a-fA-F]{3,8}\b|\brgba?\((?!var\()|\bhsla?\((?!var\()|\b(?:white|black)\b")
        proprietes = re.compile(r"(?<![\w-])(color|background|background-color|border-color|"
                                r"border|border-left|border-right|border-top|border-bottom|"
                                r"box-shadow|outline|fill|stroke)\s*:\s*([^;]+)")
        coupables = []
        for selecteur, corps in _regles_visibles():
            if "data-theme" in selecteur or selecteur.strip().startswith(":root"):
                continue
            for propriete, valeur in proprietes.findall(corps):
                if litteral.search(valeur):
                    coupables.append(f"{selecteur.strip()[:44]} → {propriete}:{valeur.strip()[:40]}")
        self.assertEqual(coupables, [], "teintes figées dans les règles : " + " · ".join(coupables))


class TestLesReglagesDuVisiteur(unittest.TestCase):
    """Thème, densité, taille du texte : trois préférences, aucune trace au serveur."""

    def test_le_panneau_d_affichage_propose_les_quatre_themes(self):
        corps = _corps()
        self.assertIn('<details class="affichage"', corps)
        for theme in THEMES:
            with self.subTest(theme=theme):
                self.assertIn(f'data-theme-choix="{theme}"', corps)
        self.assertEqual(corps.count("data-densite-choix="), 2)
        self.assertIn("Affichage", corps)

    def test_les_boutons_disent_l_etat_pas_seulement_l_action(self):
        """`aria-pressed` est ce qui fait entendre « thème en vigueur » à un lecteur d'écran.

        L'état de départ est écrit dans le document — la densité aérée est celle
        qui s'applique — et le script le tient à jour au clic (éprouvé par le
        parcours du harnais, qui choisit un thème et relit `aria-pressed`).
        """
        for theme in THEMES:
            with self.subTest(theme=theme):
                self.assertRegex(_corps(), rf'data-theme-choix="{theme}"[^>]*aria-pressed="(?:true|false)"')
        self.assertRegex(_corps(), r'data-densite-choix="aere"[^>]*aria-pressed="true"')
        self.assertRegex(_corps(), r'data-densite-choix="compact"[^>]*aria-pressed="false"')
        self.assertIn('aria-label="Réduire la taille du texte"', _corps())
        self.assertIn('aria-label="Agrandir la taille du texte"', _corps())
        self.assertIn('role="status" aria-live="polite"', _corps())

    def test_le_choix_est_pose_avant_le_premier_rendu(self):
        """Le script d'en-tête précède le corps : pas de bascule visible."""
        entete = HTML_PAGE[HTML_PAGE.index("</style>"):HTML_PAGE.index("<body>")]
        self.assertIn("documentElement", entete)
        self.assertIn("setAttribute('data-theme', theme)", entete)
        self.assertIn("localStorage", entete)
        self.assertIn("prefers-color-scheme: light", entete)
        # Un choix inconnu ou absent retombe sur la préférence de l'appareil.
        self.assertIn("themes.indexOf(theme) < 0", entete)
        self.assertIn("'aere' : densite", entete)

    def test_les_deux_densites_resserrent_sans_ecraser(self):
        """Compact divise l'espacement, jamais la lisibilité."""
        doux = _regle('html[data-densite="aere"]')
        serre = _regle('html[data-densite="compact"]')
        self.assertEqual(set(doux), set(serre), "les deux densités ne posent pas les mêmes jetons")
        self.assertEqual(set(doux), {"--pad-bloc", "--ecart-section", "--ecart-carte"})
        for jeton in doux:
            with self.subTest(jeton=jeton):
                self.assertNotEqual(doux[jeton], serre[jeton], f"{jeton} ne change pas avec la densité")
        # Aéré est bien l'état par défaut : c'est lui que le :root porte.
        socle = re.search(r":root\{(.*?)\n\}", _css(), re.S).group(1)
        self.assertIn("--pad-bloc:var(--e-4)", socle)

    def test_les_cinq_tailles_de_texte_sont_proposees(self):
        for niveau, pourcentage in (("87", "87.5%"), ("100", "100%"), ("112", "112.5%"),
                                    ("125", "125%"), ("137", "137.5%")):
            with self.subTest(niveau=niveau):
                self.assertIn(f'html[data-texte="{niveau}"]{{font-size:{pourcentage}}}', _css())

    def test_le_plancher_de_lecture_ne_suit_pas_la_taille_choisie(self):
        """`--t-min` reste en pixels : l'agrandir en `%` ferait passer du texte sous 12 px."""
        socle = re.search(r":root\{(.*?)\n\}", _css(), re.S).group(1)
        self.assertIn("--t-min:12.5px", socle)
        for niveau in ("87", "100", "112", "125", "137"):
            with self.subTest(niveau=niveau):
                regle = re.search(rf'html\[data-texte="{niveau}"\]\{{([^}}]*)\}}', _css()).group(1)
                self.assertNotIn("--t-min", regle, "une taille de texte ne doit pas toucher au plancher")

    def test_les_reglages_ne_quittent_pas_l_appareil(self):
        """Aucun envoi au serveur : le thème n'est pas une donnée personnelle."""
        for nom in ("function choisirTheme(", "function choisirDensite(", "function changerTailleTexte("):
            debut = HTML_PAGE.index(nom)
            corps = HTML_PAGE[debut:HTML_PAGE.index("\n}\n", debut)]
            with self.subTest(fonction=nom):
                self.assertNotIn("fetch(", corps)
                self.assertIn("localStorage", HTML_PAGE[HTML_PAGE.index("function retenirAffichage("):])
        self.assertIn("Ces choix restent enregistrés sur cet appareil", _corps())

    def test_le_panneau_se_replie_en_feuille_sur_un_ecran_etroit(self):
        """Sous 640 px, le panneau flotte en bas et ses boutons font 44 px."""
        portee = {}
        for contexte, selecteur, corps in _blocs(_sans_commentaires(_css())):
            if any("max-width:640px" in c for c in contexte) and ".affichage" in selecteur:
                portee[selecteur.strip()] = corps
        self.assertTrue(portee, "aucune règle d'affichage sous 640 px")
        self.assertIn("position:fixed", portee.get(".affichage-panneau", ""))
        self.assertIn("max-height", portee.get(".affichage-panneau", ""))
        self.assertIn("min-height:44px", portee.get(".affichage-choix", ""))

    def test_le_panneau_retient_son_geste(self):
        """Un panneau qui défile sans retenir son geste entraîne la page derrière."""
        for selecteur, corps in _regles_visibles():
            if ".affichage-panneau" not in selecteur:
                continue
            for nom, valeur in re.findall(r"([-\w]+)\s*:\s*([^;]+)", corps):
                if nom == "overscroll-behavior":
                    self.assertIn("contain", valeur)
                    return
        self.fail("le panneau ne retient plus son geste : overscroll-behavior a disparu")


class TestLaLigneEditoriale(unittest.TestCase):
    """Les sections se lisent en trois temps, comme les pages du site M.R.S.C."""

    def test_chaque_section_a_son_sur_titre_son_titre_et_sa_phrase(self):
        corps = _corps()
        sections = len(re.findall(r"<section\b", corps))
        entetes = corps.count('<header class="section-entete">')
        surtitres = len(re.findall(r'<header class="section-entete">\s*<p class="eyebrow">', corps))
        phrases = corps.count('class="section-intro"')
        titres = len(re.findall(
            r'<header class="section-entete">\s*<p class="eyebrow">.*?</p>\s*<h2\b[^>]*>', corps, re.S))
        self.assertEqual(sections, entetes, f"{sections} sections, {entetes} en-têtes éditoriaux")
        self.assertGreaterEqual(sections, 20, "trop peu de sections pour que la ligne éditoriale compte")
        self.assertEqual(surtitres, sections)
        self.assertEqual(phrases, sections)
        self.assertEqual(titres, sections, "un en-tête sans sur-titre suivi d'un h2")

    def test_plus_aucune_explication_collee_dans_un_titre(self):
        """L'ancienne forme mettait l'explication dans le `h2`, en petit : fini."""
        for titre in re.findall(r"<h2>(.*?)</h2>", _corps(), re.S):
            with self.subTest(titre=titre[:40]):
                self.assertNotIn('class="aide"', titre)
                self.assertNotIn('class="eyebrow"', titre)

    def test_le_sur_titre_porte_le_trait_de_la_charte(self):
        regle = _regle(".eyebrow")
        self.assertIn("uppercase", regle.get("text-transform", ""))
        self.assertEqual(regle.get("letter-spacing", "").replace(" ", ""), ".13em")
        self.assertIn("var(--accent)", regle.get("color", ""))
        barre = _regle(".eyebrow::before")
        self.assertEqual(barre.get("width"), "25px")
        self.assertEqual(barre.get("height"), "3px")
        self.assertIn("var(--vert)", barre.get("background", ""))

    def test_les_phrases_d_introduction_sont_des_phrases(self):
        """Une majuscule au début, un point à la fin — sur les vingt-quatre."""
        fautes = []
        for phrase in re.findall(r'<p class="section-intro">(.*?)</p>', _corps(), re.S):
            texte = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", phrase)).strip()
            premiere = next((c for c in texte if c.isalpha()), "")
            if not premiere.isupper():
                fautes.append(f"« {texte[:40]}… » commence en minuscule")
            if texte[-1] not in ".!?:»…":
                fautes.append(f"« {texte[-30:]} » ne se termine pas par une ponctuation")
        self.assertEqual(fautes, [], " · ".join(fautes))

    def test_le_titre_de_section_suit_une_echelle(self):
        regle = _regle(".section-entete h2")
        self.assertIn("clamp(", regle.get("font-size", ""), "le titre ne suit pas une échelle fluide")
        self.assertNotIn("section.bloc > h2{", _sans_commentaires(_css()))

    def test_l_echelle_d_espacement_est_employee(self):
        """Une échelle déclarée et jamais employée ne règle rien."""
        css = _sans_commentaires(_css())
        for jeton in ("--e-2", "--e-3", "--e-4", "--pad-bloc", "--ecart-section", "--ecart-carte",
                      "--rayon-2", "--rayon-3", "--mesure"):
            with self.subTest(jeton=jeton):
                self.assertGreater(css.count(f"var({jeton})"), 0, f"{jeton} déclaré mais jamais employé")

    def test_le_conteneur_borne_la_longueur_de_ligne(self):
        regle = _regle(".conteneur")
        self.assertIn("max-width", regle)
        mesure = re.search(r"--mesure:\s*([^;]+);", _css()).group(1).strip()
        self.assertRegex(mesure, r"^\d+ch$", "la longueur de ligne doit se mesurer en caractères")
        self.assertIn("var(--mesure)", _regle(".section-intro").get("max-width", ""))


class TestLeSocleNeBougePas(unittest.TestCase):
    """Ce qu'aucun thème, aucune densité, aucune taille ne doit casser."""

    def test_le_plancher_de_lecture_est_toujours_12_5_px(self):
        self.assertIn("--t-min:12.5px", _css())

    def test_aucun_texte_sous_douze_pixels_hors_plancher(self):
        """Le plancher se contourne toujours par un `font-size` en dur : on le refuse."""
        fautes = []
        for declaration in re.finditer(r"font-size\s*:\s*([^;}]+)", _sans_commentaires(_css())):
            valeur = declaration.group(1).strip()
            if valeur.startswith("max(var(--t-min)") or valeur.startswith("clamp("):
                continue
            for nombre in re.findall(r"(\d+(?:\.\d+)?)px", valeur):
                if float(nombre) < 12:
                    fautes.append(f"font-size:{valeur}")
        self.assertEqual(fautes, [], "tailles sous 12 px : " + " · ".join(fautes))

    def test_les_quatre_paliers_sont_toujours_la(self):
        paliers = re.findall(r"max-width:(\d+)px", _css())
        for palier in ("1200", "900", "640", "480"):
            with self.subTest(palier=palier):
                self.assertIn(palier, paliers, f"le palier {palier} px a disparu")

    def test_les_cibles_tactiles_restent_a_44_px(self):
        self.assertIn("(pointer:coarse)", _css())
        bloc = _css()[_css().index("(pointer:coarse)"):]
        self.assertIn("min-height:44px", bloc[:2000])


if __name__ == "__main__":
    unittest.main()
