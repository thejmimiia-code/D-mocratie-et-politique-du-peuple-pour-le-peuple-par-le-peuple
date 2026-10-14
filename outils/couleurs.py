"""outils/couleurs.py — lire une couleur écrite dans la page, la composer, la mesurer.

La page écrit ses teintes en CSS : `#0b1220`, `rgba(147,163,189,.18)`,
`color-mix(in srgb,var(--vert) 55%,var(--texte))`. Un contrôle d'affichage doit
pouvoir dire « ce texte se lit sur ce fond », pour chaque thème, sans ouvrir un
navigateur — et sans croire sur parole la personne qui a choisi la couleur.

Ce module est l'atelier commun de ces contrôles. Il lit exactement le
sous-ensemble de syntaxe employé par la page :

- `#rgb`, `#rrggbb`, `rgb(r,g,b)`, `rgba(r,g,b,a)`, `transparent` ;
- `color-mix(in srgb, A p%, B)` avec deux couleurs et une seule proportion ;
- `var(--nom)`, résolu dans le dictionnaire de variables du thème examiné.

Il applique ensuite les formules de la recommandation WCAG 2.1 : luminance
relative, puis rapport de contraste `(L1+.05)/(L2+.05)`. Les deux chiffres qui
servent de repère sont vérifiés dans `tests/test_couleurs.py` : blanc sur noir
vaut 21, et #767676 sur blanc vaut 4,54 — le seuil AA, juste au-dessus.

Rien ici ne connaît la page : ce module ne fait que de l'arithmétique de
couleur. C'est ce qui permet de l'éprouver sur des valeurs connues, puis de
l'appliquer aux thèmes.
"""

from __future__ import annotations

import re

#: Le minimum AA pour du texte courant, et celui des grands textes et des
#: éléments d'interface (bordures, icônes, traits de graphique).
SEUIL_TEXTE = 4.5
SEUIL_LARGE = 3.0

_COULEURS_NOMMEES = {
    "transparent": (0.0, 0.0, 0.0, 0.0),
    "white": (255.0, 255.0, 255.0, 1.0),
    "black": (0.0, 0.0, 0.0, 1.0),
    "canvas": (255.0, 255.0, 255.0, 1.0),
    "canvastext": (0.0, 0.0, 0.0, 1.0),
}

_MOTIF_HEX = re.compile(r"^#([0-9a-fA-F]{3,8})$")
_MOTIF_FONCTION = re.compile(r"^(rgba?)\((.*)\)$", re.S)
_MOTIF_MIX = re.compile(r"^color-mix\(\s*in\s+srgb\s*,(.*)\)$", re.S)


def _nombres(texte: str) -> list[float]:
    return [float(m.replace("%", "")) for m in re.findall(r"[-+]?[\d.]+%?", texte)]


def lire(texte: str):
    """Renvoie `(r, g, b, a)` — composantes 0‑255, transparence 0‑1 — ou `None`.

    `None` veut dire « je ne sais pas lire cette couleur », jamais « noir » :
    un contrôle qui prend l'ignorance pour une couleur se tromperait en silence.

    >>> lire("#fff")
    (255.0, 255.0, 255.0, 1.0)
    >>> lire("rgba(10, 20, 30, .5)")
    (10.0, 20.0, 30.0, 0.5)
    >>> lire("pas une couleur") is None
    True
    """
    texte = (texte or "").strip().lower()
    if texte in _COULEURS_NOMMEES:
        return _COULEURS_NOMMEES[texte]
    hexa = _MOTIF_HEX.match(texte)
    if hexa:
        chiffres = hexa.group(1)
        if len(chiffres) in (3, 4):
            chiffres = "".join(c * 2 for c in chiffres)
        if len(chiffres) not in (6, 8):
            return None
        valeurs = [int(chiffres[i:i + 2], 16) for i in range(0, len(chiffres), 2)]
        return (
            float(valeurs[0]),
            float(valeurs[1]),
            float(valeurs[2]),
            valeurs[3] / 255 if len(valeurs) == 4 else 1.0,
        )
    fonction = _MOTIF_FONCTION.match(texte)
    if fonction:
        valeurs = _nombres(fonction.group(2))
        if len(valeurs) < 3:
            return None
        alpha = valeurs[3] if len(valeurs) > 3 else 1.0
        if "%" in fonction.group(2).split(",")[-1]:
            alpha /= 100
        return (valeurs[0], valeurs[1], valeurs[2], alpha)
    return None


def _composantes(texte: str) -> list[str]:
    """Découpe une liste d'arguments au niveau des virgules, parenthèses comprises.

    `rgba(1,2,3,.5)`, `var(--x) 55%` et `color-mix(...)` cohabitent dans les
    mêmes listes : couper naïvement sur la virgule casserait `rgb()`.
    """
    morceaux, profondeur, courant = [], 0, ""
    for caractere in texte:
        if caractere in "([":
            profondeur += 1
        elif caractere in ")]":
            profondeur -= 1
        if caractere == "," and profondeur == 0:
            morceaux.append(courant)
            courant = ""
        else:
            courant += caractere
    morceaux.append(courant)
    return [m.strip() for m in morceaux if m.strip()]


def _proportion(morceau: str) -> tuple[str, float | None]:
    """Sépare une couleur de sa proportion : « var(--vert) 55% » → (« var(--vert) », 55)."""
    mesure = re.search(r"([\d.]+)%\s*$", morceau)
    if not mesure:
        return morceau.strip(), None
    return morceau[: mesure.start()].strip(), float(mesure.group(1))


def melanger(une, autre, proportion: float):
    """Mélange deux couleurs comme `color-mix(in srgb, …)`, en prémultipliant l'alpha.

    >>> melanger((0, 0, 0, 1), (255, 255, 255, 1), 50)
    (127.5, 127.5, 127.5, 1.0)
    """
    poids = proportion / 100
    alpha = une[3] * poids + autre[3] * (1 - poids)
    if alpha == 0:
        return (0.0, 0.0, 0.0, 0.0)
    return tuple(
        round((une[i] * une[3] * poids + autre[i] * autre[3] * (1 - poids)) / alpha, 4)
        for i in range(3)
    ) + (round(alpha, 4),)


def resoudre(expression, variables: dict, profondeur: int = 0):
    """Résout une couleur CSS avec les variables d'un thème. `None` si illisible.

    Une valeur peut déjà être une couleur calculée (un mélange composé par
    l'appelant) : dans ce cas, elle passe telle quelle.

    >>> resoudre("color-mix(in srgb,var(--v) 50%,#fff)", {"--v": "#000"})
    (127.5, 127.5, 127.5, 1.0)
    >>> resoudre((10.0, 20.0, 30.0, 1.0), {})
    (10.0, 20.0, 30.0, 1.0)
    """
    if profondeur > 8:  # une variable qui s'appelle elle-même ne boucle pas
        return None
    if isinstance(expression, tuple):
        return expression
    expression = (expression or "").strip()
    melange = _MOTIF_MIX.match(expression)
    if melange:
        morceaux = [_proportion(m) for m in _composantes(melange.group(1))]
        if len(morceaux) != 2:
            return None
        (gauche, part_gauche), (droite, part_droite) = morceaux
        if part_gauche is None and part_droite is None:
            return None
        if part_gauche is None:
            part_gauche = 100 - part_droite
        elif part_droite is None:
            part_droite = 100 - part_gauche
        gauche = resoudre(gauche, variables, profondeur + 1)
        droite = resoudre(droite, variables, profondeur + 1)
        if gauche is None or droite is None:
            return None
        # Les deux proportions se normalisent : « 70 % + 60 % » pèsent 70/130.
        total = part_gauche + part_droite
        return melanger(gauche, droite, 100 * part_gauche / total)
    variable = re.match(r"^var\(\s*(--[\w-]+)\s*(?:,([^)]*))?\)$", expression, re.S)
    if variable:
        nom, repli = variable.group(1), variable.group(2)
        if nom in variables:
            return resoudre(variables[nom], variables, profondeur + 1)
        return resoudre(repli, variables, profondeur + 1) if repli else None
    return lire(expression)


def composer(dessus, dessous):
    """Pose une couleur semi-transparente sur son fond : `rgba(.18)` sur du papier.

    >>> composer((0, 0, 0, .5), (255, 255, 255, 1))
    (127.5, 127.5, 127.5, 1.0)
    """
    if dessus is None:
        return dessous
    if dessous is None or dessus[3] >= 1:
        return dessus
    alpha = dessus[3] + dessous[3] * (1 - dessus[3])
    if alpha == 0:
        return (0.0, 0.0, 0.0, 0.0)
    return tuple(
        round((dessus[i] * dessus[3] + dessous[i] * dessous[3] * (1 - dessus[3])) / alpha, 4)
        for i in range(3)
    ) + (round(alpha, 4),)


def _canal(valeur: float) -> float:
    valeur = valeur / 255
    return valeur / 12.92 if valeur <= 0.04045 else ((valeur + 0.055) / 1.055) ** 2.4


def luminance(couleur) -> float:
    """Luminance relative WCAG d'une couleur opaque.

    >>> round(luminance((255, 255, 255, 1)), 3)
    1.0
    >>> round(luminance((0, 0, 0, 1)), 3)
    0.0
    """
    return round(
        0.2126 * _canal(couleur[0]) + 0.7152 * _canal(couleur[1]) + 0.0722 * _canal(couleur[2]), 6
    )


def contraste(une, autre) -> float:
    """Rapport de contraste WCAG entre deux couleurs, de 1 à 21.

    >>> round(contraste((0, 0, 0, 1), (255, 255, 255, 1)), 1)
    21.0
    """
    clairs = sorted((luminance(une), luminance(autre)), reverse=True)
    return round((clairs[0] + 0.05) / (clairs[1] + 0.05), 3)


def vers_hexa(couleur) -> str:
    """Écrit une couleur opaque en hexadécimal : la forme lisible dans un rapport."""
    rouge, vert, bleu = (int(round(c)) for c in couleur[:3])
    return f"#{rouge:02x}{vert:02x}{bleu:02x}"
