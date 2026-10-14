"""outils/contraste_ecran.py — mesurer ce que l'œil reçoit, élément par élément.

Les contrôles de `tests/test_themes_en_page.py` mesurent des **règles** : ils ne
voient qu'une règle qui écrit elle-même sa couleur de texte. Or la faute la plus
fréquente est ailleurs — un fond peint par une règle, une encre héritée du
parent. `button.primaire` en est l'exemple exact : la règle peint le dégradé de
marque (`--mrsc-navy` → `--mrsc-bleu`) et n'écrit aucun `color` ; en thème
« jour », l'encre héritée est bleu nuit (`--texte:#18243b`) sur du bleu nuit.
Aucun contrôle de règle ne pouvait le voir, le visiteur si.

Cet outil fait ce qu'un navigateur fait, en plus petit :

1. il lit la page réellement servie (`index.html`) et en dresse l'arbre ;
2. il applique la feuille : cascade, spécificité, héritage des jetons,
   `var()`, `color-mix()`, `@media` selon la largeur d'écran demandée ;
3. il résout, pour chaque texte de la page, l'encre **effective** et le fond
   **réellement peint** derrière lui (dégradés compris, transparences
   composées) ;
4. il compare les deux avec la formule WCAG 2.1 et refuse tout ce qui passe
   sous le seuil — 4,5:1 pour le texte courant, 3,0:1 pour les grands textes
   et les éléments d'interface.

    python3 outils/contraste_ecran.py                     # 4 thèmes × 2 largeurs
    python3 outils/contraste_ecran.py --theme jour --largeur 380
    python3 outils/contraste_ecran.py --verbeux           # détaille aussi ce qui passe

Ce qu'il ne mesure pas, et le dit : les règles qui ne s'appliquent qu'à un état
(`:hover`, `:focus`, `:disabled`) ou à une pseudo-boîte (`::before`), et les
commandes inactives, que la norme exempte. Le nombre de règles écartées est
affiché : un contrôle qui cache ce qu'il ignore n'est pas un contrôle.
"""

from __future__ import annotations

import argparse
import html.parser
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from outils import couleurs  # noqa: E402

THEMES = ("soir", "jour", "creme", "contraste")
LARGEURS = (1280, 380)
TAILLE_RACINE = 16.0

#: Les balises qui ne se referment pas : la pile ne doit pas les attendre.
VIDES = frozenset(
    {"br", "img", "input", "meta", "link", "hr", "source", "area", "base",
     "col", "embed", "param", "track", "wbr"}
)

#: Ce qui, dans un sélecteur, décrit un état et non la page au repos.
ETATS = (":hover", ":focus-visible", ":focus", ":active", ":disabled", ":checked",
         "::before", "::after", "::marker", ":has(", ":target")

_MOTIFS_MEDIA_IGNORES = ("print", "forced-colors", "pointer:", "prefers-reduced",
                         "prefers-contrast", "orientation", "hover:")


# ── L'arbre ──────────────────────────────────────────────────────────────────
class Noeud:
    """Un élément de la page : son nom, ses attributs, ses enfants, son texte."""

    __slots__ = ("nom", "attributs", "parent", "enfants", "texte")

    def __init__(self, nom: str, attributs, parent: Noeud | None) -> None:
        self.nom = nom
        self.attributs = dict(attributs)
        self.parent = parent
        self.enfants: list[Noeud] = []
        self.texte: list[str] = []

    @property
    def classes(self) -> list[str]:
        return (self.attributs.get("class") or "").split()

    def identifiant(self) -> str:
        return self.attributs.get("id") or ""


class _Lecteur(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.racine = Noeud("document", {}, None)
        self.pile = [self.racine]

    def handle_starttag(self, balise, attributs):
        noeud = Noeud(balise, attributs, self.pile[-1])
        self.pile[-1].enfants.append(noeud)
        if balise not in VIDES:
            self.pile.append(noeud)

    def handle_startendtag(self, balise, attributs):
        self.pile[-1].enfants.append(Noeud(balise, attributs, self.pile[-1]))

    def handle_endtag(self, balise):
        for rang in range(len(self.pile) - 1, 0, -1):
            if self.pile[rang].nom == balise:
                del self.pile[rang:]
                return

    def handle_data(self, donnee):
        if donnee.strip():
            self.pile[-1].texte.append(donnee.strip())


def arbre(page: str, theme: str | None = None, densite: str = "aere") -> Noeud:
    """L'arbre de la page, réglé comme le navigateur le ferait au chargement.

    Le thème et la densité ne sont pas des paramètres de la feuille : ils vivent
    sur `<html>` (`data-theme`, `data-densite`). Les poser ici, c'est rejouer ce
    que fait le script d'en-tête de la page — sans quoi la cascade répondrait
    toujours « soir », et le contrôle serait aveugle aux trois autres thèmes.
    """
    lecteur = _Lecteur()
    lecteur.feed(page)
    if theme is not None:
        for noeud in parcourir(lecteur.racine):
            if noeud.nom == "html":
                noeud.attributs["data-theme"] = theme
                noeud.attributs.setdefault("data-densite", densite)
                break
    return lecteur.racine


def parcourir(noeud: Noeud):
    yield noeud
    for enfant in noeud.enfants:
        yield from parcourir(enfant)


# ── La feuille ───────────────────────────────────────────────────────────────
def feuille_de_la_page(page: str) -> str:
    debut = page.index("<style>") + len("<style>")
    return page[debut:page.index("</style>", debut)]


def _sans_commentaires(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _blocs(texte: str, contexte: tuple[str, ...] = ()):
    """Toutes les règles d'une feuille, avec le `@media` qui les porte."""
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


def regles(css: str):
    """Toutes les règles d'une feuille, avec leur contexte `@media`.

    Publié pour les contrôles : ils ont besoin de lire la même feuille que
    l'outil, pas d'en réécrire un analyseur à côté.
    """
    return _blocs(_sans_commentaires(css))


def _media_s_applique(contexte, largeur: int) -> bool:
    for bloc in contexte:
        texte = bloc.replace(" ", "").lower()
        if any(motif in texte for motif in _MOTIFS_MEDIA_IGNORES):
            return False
        for condition in re.finditer(r"\((min|max)-width:(\d+(?:\.\d+)?)px\)", texte):
            borne = float(condition.group(2))
            if condition.group(1) == "max" and largeur > borne:
                return False
            if condition.group(1) == "min" and largeur < borne:
                return False
    return True


def _decouper(sequence: str):
    """`'a > b c'` → `[(composé, relation_avec_la_gauche), …]`."""
    morceaux, courant, profondeur, relation = [], "", 0, " "
    for caractere in sequence:
        if caractere in "([":
            profondeur += 1
        elif caractere in ")]":
            profondeur -= 1
        if caractere == ">" and profondeur == 0:
            morceaux.append((courant.strip(), relation))
            courant, relation = "", ">"
        elif caractere.isspace() and profondeur == 0:
            if courant.strip():
                morceaux.append((courant.strip(), relation))
                courant, relation = "", " "
        else:
            courant += caractere
    if courant.strip():
        morceaux.append((courant.strip(), relation))
    return morceaux


_MOTIF_COMPOSE = re.compile(
    r"(?P<tag>[a-zA-Z][\w-]*|\*)?"
    r"(?P<reste>(?:#[-\w]+|\.[-\w]+|\[[^\]]*\]|:(?:not\([^)]*\)|root|first-child|last-child|last-of-type|only-child|empty))*)"
)
_MOTIF_BOUT = re.compile(r"#[-\w]+|\.[-\w]+|\[[^\]]*\]|:[a-zA-Z-]+(?:\([^)]*\))?")


def _analysable(selecteur: str) -> bool:
    return not any(etat in selecteur for etat in ETATS)


def _compose(morceau: str):
    """Un composé simple : balise, #id, .classes, [attributs], :not(…)."""
    trouve = _MOTIF_COMPOSE.fullmatch(morceau)
    if not trouve:
        return None
    compose = {"tag": trouve.group("tag"), "id": None, "classes": [], "attributs": [],
               "interdits": [], "contraintes": []}
    for bout in _MOTIF_BOUT.findall(trouve.group("reste") or ""):
        if bout.startswith("#"):
            compose["id"] = bout[1:]
        elif bout.startswith("."):
            compose["classes"].append(bout[1:])
        elif bout.startswith("["):
            contenu = bout[1:-1]
            if "=" in contenu:
                nom, valeur = contenu.split("=", 1)
                compose["attributs"].append((nom.strip(), valeur.strip().strip("\"'")))
            else:
                compose["attributs"].append((contenu.strip(), None))
        elif bout.startswith(":not("):
            interdit = _compose(bout[5:-1])
            if interdit is None:
                return None
            compose["interdits"].append(interdit)
        elif bout == ":root":
            compose["tag"] = "html"
        else:
            compose["contraintes"].append(bout[1:])
    return compose


def _premier_enfant(noeud: Noeud) -> bool:
    if noeud.parent is None:
        return True
    return noeud.parent.enfants[0] is noeud


def _dernier_enfant(noeud: Noeud) -> bool:
    if noeud.parent is None:
        return True
    return noeud.parent.enfants[-1] is noeud


def _correspond_compose(noeud: Noeud, compose) -> bool:
    if compose["tag"] not in (None, "*") and noeud.nom != compose["tag"]:
        return False
    if compose["id"] and noeud.identifiant() != compose["id"]:
        return False
    if not set(compose["classes"]) <= set(noeud.classes):
        return False
    for nom, valeur in compose["attributs"]:
        if nom not in noeud.attributs:
            return False
        if valeur is not None and noeud.attributs[nom] != valeur:
            return False
    for contrainte in compose["contraintes"]:
        if contrainte == "first-child" and not _premier_enfant(noeud):
            return False
        if contrainte == "last-child" and not _dernier_enfant(noeud):
            return False
        if contrainte == "last-of-type":
            suivants = [e for e in (noeud.parent.enfants if noeud.parent else [])
                        if e.nom == noeud.nom]
            if suivants and suivants[-1] is not noeud:
                return False
        if contrainte in ("only-child", "empty"):
            return False
    for interdit in compose["interdits"]:
        if interdit["contraintes"] == ["disabled"] or interdit["tag"] == "disabled":
            if "disabled" in noeud.attributs:
                return False
        elif _correspond_compose(noeud, interdit):
            return False
    return True


def _correspond(noeud: Noeud, chaines) -> bool:
    compose, relation = chaines[-1]
    if not _correspond_compose(noeud, compose):
        return False
    if len(chaines) == 1:
        return True
    gauche = chaines[:-1]
    if relation == ">":
        return noeud.parent is not None and _correspond(noeud.parent, gauche)
    ancetre = noeud.parent
    while ancetre is not None:
        if _correspond(ancetre, gauche):
            return True
        ancetre = ancetre.parent
    return False


def _specificite(chaines) -> tuple[int, int, int]:
    """(identifiants, classes et attributs, balises) — la règle du CSS."""
    ids = classes = tags = 0
    for compose, _ in chaines:
        ids += 1 if compose["id"] else 0
        classes += len(compose["classes"]) + len(compose["attributs"])
        classes += 1 if compose["contraintes"] or compose["interdits"] else 0
        tags += 1 if compose["tag"] and compose["tag"] != "*" else 0
    return (ids, classes, tags)


def _cle_du_compose(compose) -> list[str]:
    """Les seaux où ranger une règle : par identifiant, par classe, par balise."""
    cles = []
    if compose["id"]:
        cles.append("#" + compose["id"])
    cles.extend("." + classe for classe in compose["classes"])
    if compose["tag"] and compose["tag"] != "*":
        cles.append(compose["tag"])
    if not cles:
        cles.append("*")
    return cles


def _declarations(corps: str) -> dict[str, str]:
    return {nom.strip(): valeur.strip().replace("!important", "").strip()
            for nom, valeur in re.findall(r"([-\w]+)\s*:\s*([^;]+)", corps)}


class Feuille:
    """La feuille applicable à une largeur, indexée pour aller vite."""

    def __init__(self, css: str, largeur: int):
        self.largeur = largeur
        self.ecartees: list[str] = []
        self.index: dict[str, list] = {}
        for numero, (contexte, selecteur, corps) in enumerate(_blocs(_sans_commentaires(css))):
            if not _media_s_applique(contexte, largeur):
                continue
            for sequence in _decouper_selecteurs(selecteur):
                if not _analysable(sequence) or "bloc-de-theme" in sequence:
                    self.ecartees.append(sequence)
                    continue
                chaines = _decouper(sequence)
                composes = [(compose, relation) for compose, relation in
                            ((_compose(morceau), relation) for morceau, relation in chaines)]
                if any(compose is None for compose, _ in composes):
                    self.ecartees.append(sequence)
                    continue
                regle = (_specificite(composes), numero, composes, _declarations(corps))
                for cle in _cle_du_compose(composes[-1][0]):
                    self.index.setdefault(cle, []).append(regle)

    def correspondantes(self, noeud: Noeud):
        candidates = self.index.get("*", [])
        for cle in ["#" + noeud.identifiant()] if noeud.identifiant() else []:
            candidates = candidates + self.index.get(cle, [])
        for classe in noeud.classes:
            candidates = candidates + self.index.get("." + classe, [])
        candidates = candidates + self.index.get(noeud.nom, [])
        vues, sortie = set(), []
        for regle in candidates:
            if id(regle) in vues:
                continue
            vues.add(id(regle))
            if _correspond(noeud, regle[2]):
                sortie.append(regle)
        sortie.sort(key=lambda regle: (regle[0], regle[1]))
        return sortie


def _decouper_selecteurs(selecteur: str) -> list[str]:
    """Sépare les sélecteurs d'une liste, sans couper dans `[attr="a, b"]`."""
    morceaux, courant, profondeur = [], "", 0
    for caractere in selecteur:
        if caractere in "([":
            profondeur += 1
        elif caractere in ")]":
            profondeur -= 1
        if caractere == "," and profondeur == 0:
            morceaux.append(courant.strip())
            courant = ""
        else:
            courant += caractere
    if courant.strip():
        morceaux.append(courant.strip())
    return [morceau for morceau in morceaux if morceau]


def _palette(css: str, theme: str) -> dict[str, str]:
    motif = re.compile(
        rf"(?:^|\n)(?:\[data-theme=\"{theme}\"\]|:root,\[data-theme=\"{theme}\"\])\{{(.*?)\n\}}", re.S)
    trouve = motif.search(css)
    assert trouve, f"palette absente : {theme}"
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", trouve.group(1)))


# ── La cascade sur un élément ────────────────────────────────────────────────
def _jetons_couleur(valeur: str) -> list[str]:
    """Toutes les couleurs d'une valeur CSS : dégradés, mélanges, transparences."""
    jetons, i = [], 0
    while i < len(valeur):
        if valeur.startswith("color-mix(", i):
            profondeur, j = 0, i
            while j < len(valeur):
                if valeur[j] == "(":
                    profondeur += 1
                elif valeur[j] == ")":
                    profondeur -= 1
                    if profondeur == 0:
                        break
                j += 1
            jetons.append(valeur[i:j + 1])
            i = j + 1
            continue
        trouve = re.match(r"var\(--[\w-]+(?:\s*,[^)]*)?\)|#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|\b(?:transparent|white|black)\b", valeur[i:])
        if trouve:
            jetons.append(trouve.group(0))
            i += len(trouve.group(0))
        else:
            i += 1
    return jetons


def _longueur_px(valeur: str, variables: dict, heritage: float | None) -> float | None:
    """Une taille en pixels : `rem`, `px`, `em`, et le pire cas d'un `clamp()`."""
    if valeur is None:
        return heritage
    valeur = valeur.strip()
    possibles = []
    for morceau in re.findall(r"[-+]?[\d.]+(?:rem|px|em|pt)", valeur):
        nombre = float(re.match(r"[-+]?[\d.]+", morceau).group(0))
        unite = morceau[len(re.match(r"[-+]?[\d.]+", morceau).group(0)):]
        if unite == "rem":
            possibles.append(nombre * TAILLE_RACINE)
        elif unite == "px":
            possibles.append(nombre)
        elif unite == "pt":
            possibles.append(nombre * 4 / 3)
        elif unite == "em":
            possibles.append(nombre * (heritage or TAILLE_RACINE))
    if "var(--" in valeur and not possibles:
        for nom in re.findall(r"var\((--[\w-]+)", valeur):
            if nom in variables:
                suite = _longueur_px(variables[nom], variables, heritage)
                if suite is not None:
                    possibles.append(suite)
    if not possibles:
        return heritage
    return min(possibles)


class Style:
    """L'encre, le fond et la taille tels que le navigateur les compose."""

    def __init__(self, racine: Noeud, feuille: Feuille, palette: dict):
        self.feuille = feuille
        self.palette = palette
        self.voir: dict[int, dict] = {}
        self._preparer(racine, {})

    def _preparer(self, noeud: Noeud, variables_parent: dict):
        regles = self.feuille.correspondantes(noeud)
        variables = dict(variables_parent)
        propre: dict[str, str] = {}
        for _, _, _, declarations in regles:
            for nom, valeur in declarations.items():
                if nom.startswith("--"):
                    variables[nom] = valeur
                else:
                    propre[nom] = valeur
        self.voir[id(noeud)] = {"variables": variables, "propre": propre, "regles": regles,
                                "parent": id(noeud.parent) if noeud.parent else None}
        for enfant in noeud.enfants:
            self._preparer(enfant, variables)

    # — valeurs héritées —
    def _herite(self, noeud: Noeud, propriete: str, defaut):
        courant = noeud
        while courant is not None:
            entree = self.voir.get(id(courant))
            if entree and propriete in entree["propre"]:
                return entree["propre"][propriete], entree["variables"]
            courant = courant.parent
        return defaut, {}

    def variables(self, noeud: Noeud) -> dict:
        return self.voir[id(noeud)]["variables"]

    def encre(self, noeud: Noeud):
        valeur, variables = self._herite(noeud, "color", "var(--texte)")
        melange = dict(self.palette)
        melange.update(variables)
        return couleurs.resoudre(valeur, melange)

    def taille(self, noeud: Noeud) -> float:
        courant, taille, garde = noeud, None, 0
        while courant is not None and garde < 40:
            entree = self.voir.get(id(courant))
            if entree and "font-size" in entree["propre"]:
                variables = dict(self.palette)
                variables.update(entree["variables"])
                mesure = _longueur_px(entree["propre"]["font-size"], variables, taille)
                if mesure is not None:
                    return mesure
            courant = courant.parent
            garde += 1
        return TAILLE_RACINE

    def poids(self, noeud: Noeud) -> int:
        valeur, _ = self._herite(noeud, "font-weight", "400")
        if valeur in ("bold", "bolder"):
            return 700
        if valeur == "lighter":
            return 300
        try:
            return int(float(valeur))
        except (TypeError, ValueError):
            return 400

    def opacite(self, noeud: Noeud) -> float:
        facteur, courant = 1.0, noeud
        while courant is not None:
            entree = self.voir.get(id(courant))
            if entree and "opacity" in entree["propre"]:
                try:
                    facteur *= float(entree["propre"]["opacity"])
                except ValueError:
                    pass
            courant = courant.parent
        return facteur

    def _peinture(self, noeud: Noeud):
        """Le fond peint par cet élément, ou `None` : liste de couleurs candidates."""
        entree = self.voir.get(id(noeud))
        if not entree:
            return None
        valeur = entree["propre"].get("background-color") or entree["propre"].get("background")
        if not valeur or valeur.strip() in ("none", "transparent", "initial"):
            return None
        variables = dict(self.palette)
        variables.update(entree["variables"])
        candidates = []
        for jeton in _jetons_couleur(valeur):
            if jeton == "transparent":
                continue
            couleur = couleurs.resoudre(jeton, variables)
            if couleur is not None:
                candidates.append(couleur)
        return candidates or None

    def fond(self, noeud: Noeud):
        """Le fond réellement vu derrière ce texte : couches composées."""
        couches = []
        courant = noeud
        while courant is not None:
            peinture = self._peinture(courant)
            if peinture:
                couches.append(peinture)
            courant = courant.parent
        candidats = [couleurs.resoudre("var(--bg)", self.palette) or (0, 0, 0, 1)]
        for couche in reversed(couches):
            melanges = []
            for dessus in couche:
                for dessous in candidats:
                    melanges.append(couleurs.composer(dessus, dessous))
            candidats = melanges[:8] or candidats
        return candidats

    def cache(self, noeud: Noeud) -> bool:
        courant = noeud
        while courant is not None:
            if "hidden" in courant.attributs:
                return True
            entree = self.voir.get(id(courant))
            if entree and entree["propre"].get("display") == "none":
                return True
            if entree and entree["propre"].get("visibility") == "hidden":
                return True
            courant = courant.parent
        return False

    def inactif(self, noeud: Noeud) -> bool:
        courant = noeud
        while courant is not None:
            if "disabled" in courant.attributs:
                return True
            courant = courant.parent
        return False


# ── La mesure ────────────────────────────────────────────────────────────────
def _chemin(noeud: Noeud) -> str:
    """Le chemin utile : ce qui identifie l'élément, pas les `div` anonymes."""
    morceaux, courant = [], noeud
    while courant is not None and courant.nom != "document":
        if courant.identifiant() or courant.classes or courant is noeud:
            bout = courant.nom
            if courant.identifiant():
                bout += "#" + courant.identifiant()
            if courant.classes:
                bout += "." + ".".join(courant.classes[:2])
            morceaux.append(bout)
        courant = courant.parent
    return " > ".join(reversed(morceaux[-3:]))


def _seuil(taille: float, poids: int) -> float:
    if taille >= 24 or (taille >= 18.66 and poids >= 700):
        return couleurs.SEUIL_LARGE
    return couleurs.SEUIL_TEXTE


class Mesure:
    __slots__ = ("chemin", "texte", "encre", "fond", "rapport", "seuil", "exempte")

    def __init__(self, chemin, texte, encre, fond, rapport, seuil, exempte=False):
        self.chemin, self.texte, self.encre, self.fond = chemin, texte, encre, fond
        self.rapport, self.seuil, self.exempte = rapport, seuil, exempte

    def ligne(self) -> str:
        return (f"{self.chemin}  « {self.texte[:52]} »  "
                f"{self.rapport:.2f}:1 (seuil {self.seuil:.1f})  "
                f"{couleurs.vers_hexa(self.encre)} sur {couleurs.vers_hexa(self.fond)}")


def mesurer(page: str, theme: str, largeur: int) -> tuple[list[Mesure], Feuille, dict]:  # noqa: D401
    """Toutes les mesures d'une page : ce qui passe, ce qui échoue, ce qu'on écarte."""
    css = feuille_de_la_page(page)
    palette = _palette(css, theme)
    feuille = Feuille(css, largeur)
    sommet = arbre(page, theme)
    style = Style(sommet, feuille, palette)
    mesures, exemptes = [], []
    for noeud in parcourir(sommet):
        if not noeud.texte:
            continue
        if style.cache(noeud):
            continue
        texte = " ".join(noeud.texte)
        if not texte.strip():
            continue
        encre = style.encre(noeud)
        if encre is None or encre[3] == 0:
            continue
        fonds = style.fond(noeud)
        seuil = _seuil(style.taille(noeud), style.poids(noeud))
        opacite = style.opacite(noeud)
        pire = None
        for fond in fonds:
            visuel = couleurs.composer((encre[0], encre[1], encre[2], opacite), fond)
            rapport = couleurs.contraste(visuel, fond)
            if rapport is None:
                continue
            if pire is None or rapport < pire[0]:
                pire = (rapport, visuel, fond)
        if pire is None:
            continue
        mesure = Mesure(_chemin(noeud), texte, pire[1], pire[2], pire[0], seuil, style.inactif(noeud))
        (exemptes if mesure.exempte else mesures).append(mesure)
    return mesures, feuille, {"exemptes": exemptes, "regles_ecartees": feuille.ecartees}


def auditer(page: str, themes=THEMES, largeurs=LARGEURS):
    """Le rapport complet : une entrée par thème et par largeur."""
    rapport = {}
    for theme in themes:
        for largeur in largeurs:
            mesures, feuille, details = mesurer(page, theme, largeur)
            fautes = [mesure for mesure in mesures if mesure.rapport < mesure.seuil - 1e-9]
            rapport[(theme, largeur)] = {"mesures": mesures, "fautes": fautes, **details}
    return rapport


def _page_par_defaut() -> str:
    fichier = RACINE / "index.html"
    if fichier.exists():
        return fichier.read_text(encoding="utf-8")
    from simulateur.interface import HTML_PAGE  # noqa: PLC0415

    return HTML_PAGE


def main(argv=None) -> int:
    analyseur = argparse.ArgumentParser(description="Mesure le contraste réel de chaque texte de la page.")
    analyseur.add_argument("--theme", choices=THEMES, help="un seul thème")
    analyseur.add_argument("--largeur", type=int, help="une seule largeur d'écran")
    analyseur.add_argument("--verbeux", action="store_true", help="détaille aussi ce qui passe")
    analyseur.add_argument("--page", help="un autre fichier que index.html")
    options = analyseur.parse_args(argv)

    page = Path(options.page).read_text(encoding="utf-8") if options.page else _page_par_defaut()
    themes = (options.theme,) if options.theme else THEMES
    largeurs = (options.largeur,) if options.largeur else LARGEURS

    total_fautes = 0
    for theme in themes:
        for largeur in largeurs:
            mesures, feuille, details = mesurer(page, theme, largeur)
            fautes = [mesure for mesure in mesures if mesure.rapport < mesure.seuil - 1e-9]
            total_fautes += len(fautes)
            print(f"═══ thème « {theme} » · écran de {largeur} px ═══")
            print(f"    {len(mesures)} textes mesurés · {len(fautes)} sous le seuil · "
                  f"{len(details['exemptes'])} commandes inactives exemptées · "
                  f"{len(feuille.ecartees)} règles hors état (survol, focus, impression)")
            for mesure in fautes:
                print("  ✗ " + mesure.ligne())
            if options.verbeux:
                for mesure in mesures:
                    if mesure.rapport >= mesure.seuil:
                        print("  ✓ " + mesure.ligne())
            if not fautes:
                print("  ✓ tout se lit")
    return 1 if total_fautes else 0


if __name__ == "__main__":
    raise SystemExit(main())
