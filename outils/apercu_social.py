#!/usr/bin/env python3
"""outils/apercu_social.py — les images publiques du projet.

Trois familles, un seul dessin et une seule palette (celle de
`simulateur/interface.py`) :

* **l'aperçu social du dépôt** — 1280 × 640, la vignette que GitHub affiche
  lorsqu'un lien vers le dépôt est partagé. GitHub ne l'accepte que par
  l'interface web : ce script la produit, elle est téléversée ensuite dans
  *Edit repository details* (« Social preview ») ;
* **l'aperçu de la page** — `og-image.png`, 1200 × 630, l'image annoncée par
  `<meta property="og:image">` : c'est elle qu'affichent les aperçus des
  moteurs, des messageries et des réseaux sociaux ;
* **les icônes** — `favicon.svg` (dessiné en clair, lisible par tous les
  navigateurs récents), `favicon.ico` (le repli des vieux onglets, plusieurs
  tailles dans un seul fichier) et `apple-touch-icon.png` (180 × 180, l'icône
  d'un raccourci sur téléphone). Les deux dernières entrent dans la page en
  `data:` : l'onglet et le raccourci sont reconnaissables sans qu'aucun fichier
  soit chargé.

    python3 outils/apercu_social.py                # écrit les cinq images
    python3 outils/apercu_social.py --verifier     # contrôle les fichiers écrits

Le dessin reprend la palette du simulateur et ses quatre chiffres clés, **lus
dans le catalogue** au moment où l'image est faite : une vignette qui annonce un
nombre faux est une promesse non tenue, et le catalogue bouge. Seule dépendance :
Pillow (`pip install pillow`).
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # Pillow ne sert qu'ici : le simulateur, lui, n'en dépend pas.
    raise SystemExit(
        "Pillow est nécessaire pour dessiner l'aperçu de partage.\n"
        "    python3 -m pip install Pillow\n"
        "Les images publiées restent versionnées dans le dépôt : ce message ne\n"
        "signale pas un défaut des fichiers, seulement une dépendance absente."
        "\n\n(La suite de tests le sait : ce contrôle est sauté sans Pillow, et la\n"
        "CI l'installe pour qu'il tourne vraiment.)"
    ) from None

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:      # le script se lance depuis n'importe où
    sys.path.insert(0, str(RACINE))

# ── Palette du simulateur (identique à `simulateur/interface.py`) ───────────
FOND_HAUT = (11, 18, 32)
FOND_BAS = (22, 35, 61)
CARTE = (26, 37, 64)
BORDURE = (38, 50, 77)
TEXTE = (230, 237, 247)
TEXTE_DIM = (147, 163, 189)
ACCENT = (56, 189, 248)
VERT = (34, 197, 94)
AMBRE = (245, 158, 11)
VIOLET = (168, 85, 247)
ROUGE = (239, 68, 68)

# ── Palette de l'icône (accents M.R.S.C. éclaircis, comme la page) ──────────
NAVY = (29, 50, 104)
VERT_CLAIR = (155, 199, 122)
BLEU_CLAIR = (145, 178, 230)
OR_CLAIR = (242, 193, 95)

CHEMIN_POLICES = Path("/usr/share/fonts/truetype/dejavu")

#: Format de l'aperçu social de GitHub, puis de l'aperçu de la page.
TAILLE_DEPOT = (1280, 640)
TAILLE_APERCU = (1200, 630)
TAILLE_APPLE = 180


def police(nom: str, taille: int) -> ImageFont.FreeTypeFont:
    """Charge une police DejaVu, avec repli sur la police par défaut."""
    chemin = CHEMIN_POLICES / nom
    if chemin.exists():
        return ImageFont.truetype(str(chemin), taille)
    return ImageFont.load_default(size=taille)


def degrade(largeur: int, hauteur: int) -> Image.Image:
    """Fond dégradé vertical, du bleu nuit au bleu ardoise."""
    image = Image.new("RGB", (largeur, hauteur), FOND_BAS)
    dessin = ImageDraw.Draw(image)
    for y in range(hauteur):
        part = y / max(hauteur - 1, 1)
        couleur = tuple(
            int(FOND_HAUT[i] + (FOND_BAS[i] - FOND_HAUT[i]) * part) for i in range(3)
        )
        dessin.line([(0, y), (largeur, y)], fill=couleur)
    return image


def centrer(dessin: ImageDraw.ImageDraw, texte: str, y: int, largeur: int,
            police_texte: ImageFont.FreeTypeFont, couleur: tuple[int, int, int]) -> None:
    """Écrit un texte centré horizontalement."""
    gauche, _, droite, _ = dessin.textbbox((0, 0), texte, font=police_texte)
    dessin.text(((largeur - (droite - gauche)) / 2 - gauche, y), texte,
                font=police_texte, fill=couleur)


def chip(dessin: ImageDraw.ImageDraw, x: int, y: int, texte: str,
         police_texte: ImageFont.FreeTypeFont, couleur: tuple[int, int, int],
         remplissage: tuple[int, int, int] | None = None) -> int:
    """Pastille arrondie ; retourne l'abscisse de fin."""
    marge_x, marge_y = 14, 7
    gauche, haut, droite, bas = dessin.textbbox((0, 0), texte, font=police_texte)
    largeur, hauteur = (droite - gauche) + 2 * marge_x, (bas - haut) + 2 * marge_y
    boite = [x, y, x + largeur, y + hauteur]
    if remplissage:
        dessin.rounded_rectangle(boite, radius=hauteur // 2, fill=remplissage,
                                 outline=couleur, width=1)
    else:
        dessin.rounded_rectangle(boite, radius=hauteur // 2, outline=couleur, width=2)
    dessin.text((x + marge_x - gauche, y + marge_y - haut), texte,
                font=police_texte, fill=couleur)
    return x + largeur


def chiffres_cles() -> list[tuple[str, str, tuple[int, int, int]]]:
    """Les quatre chiffres de la vignette, lus dans le catalogue publié."""
    from simulateur.classes_leviers import CLASSES
    from simulateur.domaines import DOMAINES
    from simulateur.donnees_live import INDICATEURS
    from simulateur.parametres import LEVIERS

    return [
        (str(len(LEVIERS)), "leviers croisables", ACCENT),
        (str(len(DOMAINES)), "domaines notés 0-100", VERT),
        (str(len(INDICATEURS)), "indicateurs publics", AMBRE),
        (str(len(CLASSES)), "classes de leviers", VIOLET),
    ]


def construire(largeur: int = TAILLE_DEPOT[0], hauteur: int = TAILLE_DEPOT[1]) -> Image.Image:
    """Compose l'aperçu (dépôt ou page : même dessin, deux formats)."""
    image = degrade(largeur, hauteur)
    dessin = ImageDraw.Draw(image)

    # Filet supérieur : rappel de la « console de veille » du simulateur.
    dessin.rectangle([0, 0, largeur, 6], fill=ACCENT)

    police_titre = police("DejaVuSans-Bold.ttf", 58)
    police_sous_titre = police("DejaVuSans.ttf", 25)
    police_chiffre = police("DejaVuSans-Bold.ttf", 52)
    police_etiquette = police("DejaVuSans.ttf", 19)
    police_mini = police("DejaVuSans.ttf", 17)
    police_mono = police("DejaVuSansMono.ttf", 18)

    centrer(dessin, "Simulateur Macro-Politique", 62, largeur, police_titre, TEXTE)
    centrer(dessin, "Démocratie et politique : du peuple, pour le peuple, par le peuple",
            136, largeur, police_sous_titre, TEXTE_DIM)

    # Les quatre chiffres clés, en cartes. Ils sont lus dans le catalogue : une
    # vignette qui annonce un nombre faux est une promesse non tenue, et le
    # catalogue bouge à chaque nappe de leviers ajoutée.
    chiffres = chiffres_cles()
    largeur_carte, espace = 262, 24
    total = len(chiffres) * largeur_carte + (len(chiffres) - 1) * espace
    x = (largeur - total) // 2
    y_carte, hauteur_carte = 200, 132
    for nombre, etiquette, couleur in chiffres:
        dessin.rounded_rectangle(
            [x, y_carte, x + largeur_carte, y_carte + hauteur_carte],
            radius=16, fill=CARTE, outline=BORDURE, width=1,
        )
        dessin.rounded_rectangle([x, y_carte, x + 5, y_carte + hauteur_carte],
                                 radius=3, fill=couleur)
        gauche, _, droite, _ = dessin.textbbox((0, 0), nombre, font=police_chiffre)
        dessin.text((x + (largeur_carte - (droite - gauche)) / 2 - gauche, y_carte + 20),
                    nombre, font=police_chiffre, fill=couleur)
        gauche, _, droite, _ = dessin.textbbox((0, 0), etiquette, font=police_etiquette)
        dessin.text((x + (largeur_carte - (droite - gauche)) / 2 - gauche, y_carte + 90),
                    etiquette, font=police_etiquette, fill=TEXTE_DIM)
        x += largeur_carte + espace

    # Le ruban de veille : strates et verdict, comme dans l'interface. Le
    # verdict est une illustration de l'interface, pas un résultat de calcul.
    y_ruban = 372
    gauche, _, droite, _ = dessin.textbbox((0, 0), "VEILLE PERMANENTE", font=police_mono)
    largeur_etiquette = droite - gauche
    largeur_pastilles = 5 * 44 + 4 * 8
    largeur_verdict = 260
    total_ruban = largeur_etiquette + 26 + largeur_pastilles + 26 + largeur_verdict
    x = (largeur - total_ruban) // 2
    hauteur_ruban = 52
    dessin.rounded_rectangle(
        [x, y_ruban, x + total_ruban, y_ruban + hauteur_ruban],
        radius=14, fill=(14, 26, 48), outline=BORDURE, width=1,
    )
    dessin.text((x + 18, y_ruban + 17), "VEILLE PERMANENTE", font=police_mono,
                fill=TEXTE_DIM)
    x_pastille = x + 18 + largeur_etiquette + 26
    for indice, couleur in enumerate((VERT, VERT, AMBRE, AMBRE, VIOLET), start=1):
        dessin.rounded_rectangle(
            [x_pastille, y_ruban + 13, x_pastille + 44, y_ruban + 39],
            radius=8, fill=tuple(min(255, c // 3 + 20) for c in couleur),
            outline=couleur, width=1,
        )
        texte = f"S{indice}"
        gauche, haut, droite, bas = dessin.textbbox((0, 0), texte, font=police_mini)
        dessin.text((x_pastille + (44 - (droite - gauche)) / 2 - gauche,
                     y_ruban + (26 - (bas - haut)) / 2 - haut + 13),
                    texte, font=police_mini, fill=couleur)
        x_pastille += 52
    verdict = "VIGILANCE · 7 alertes"
    gauche, _, droite, _ = dessin.textbbox((0, 0), verdict, font=police_mini)
    largeur_texte = droite - gauche
    x_verdict = x + total_ruban - 18 - largeur_texte - 28
    dessin.rounded_rectangle(
        [x_verdict - 14, y_ruban + 11, x + total_ruban - 14, y_ruban + 41],
        radius=15, outline=AMBRE, width=2,
    )
    dessin.text((x_verdict, y_ruban + 17), verdict, font=police_mini, fill=AMBRE)

    from simulateur.domaines import DOMAINES

    centrer(dessin, f"Chaque curseur se répercute en direct sur les {len(DOMAINES)} domaines "
                    "et les 5 échelons", 452, largeur, police_etiquette, TEXTE)

    # Pied : sources publiques (gauche) et dépôt (droite).
    dessin.line([(64, 528), (largeur - 64, 528)], fill=BORDURE, width=1)
    dessin.text((64, 548), "Données publiques en direct : Eurostat · BCE · "
                           "Banque mondiale · Frankfurter", font=police_mini, fill=TEXTE_DIM)
    depot = "github.com/thejmimiia-code"
    gauche, _, droite, _ = dessin.textbbox((0, 0), depot, font=police_mini)
    dessin.text((largeur - 64 - (droite - gauche), 548), depot,
                font=police_mini, fill=ACCENT)
    dessin.text((64, 578), "5 échelons : local · national · européen · mondial · géopolitique",
                font=police_mini, fill=TEXTE_DIM)
    seuils = "seuils tolérables → hors-sol, strate par strate"
    gauche, _, droite, _ = dessin.textbbox((0, 0), seuils, font=police_mini)
    dessin.text((largeur - 64 - (droite - gauche), 578), seuils,
                font=police_mini, fill=ROUGE)
    return image


def construire_icone(taille: int) -> Image.Image:
    """L'icône : le carré arrondi de la charte, trois barres, un filet d'accent.

    Trois barres qui montent disent la même chose que la page — des classes de
    leviers, une cascade — sans une lettre à rendre lisible en 16 pixels. Le
    même dessin est écrit en SVG juste à côté, aux mêmes proportions.
    """
    image = Image.new("RGBA", (taille, taille), (0, 0, 0, 0))
    dessin = ImageDraw.Draw(image)
    dessin.rounded_rectangle([0, 0, taille - 1, taille - 1],
                             radius=int(taille * 0.22), fill=NAVY + (255,))
    # Filet d'accent, en haut : le rappel de la console.
    marge = int(taille * 0.20)
    dessin.rounded_rectangle([marge, int(taille * 0.16), taille - marge,
                              int(taille * 0.22)], radius=int(taille * 0.03),
                             fill=ACCENT + (255,))
    # Trois barres, à la même ligne de base, de hauteurs croissantes.
    ligne_base = int(taille * 0.78)
    largeur_barre = int(taille * 0.16)
    for part_gauche, hauteur, couleur in (
        (0.20, 0.22, VERT_CLAIR),
        (0.42, 0.34, BLEU_CLAIR),
        (0.64, 0.46, OR_CLAIR),
    ):
        gauche = int(taille * part_gauche)
        dessin.rounded_rectangle(
            [gauche, ligne_base - int(taille * hauteur), gauche + largeur_barre, ligne_base],
            radius=int(taille * 0.05), fill=couleur + (255,),
        )
    return image


def svg_icone(taille: int = 64) -> str:
    """Le même dessin, en clair : le SVG sert d'abord parce qu'il se lit."""
    def cote(part: float) -> str:
        return f"{part * taille:.2f}".rstrip("0").rstrip(".")

    ligne_base = 0.78
    barres = (
        (0.20, 0.22, "#9bc77a"),
        (0.42, 0.34, "#91b2e6"),
        (0.64, 0.46, "#f2c15f"),
    )
    morceaux = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {taille} {taille}" '
        f'role="img" aria-label="Simulateur macro-politique — M.R.S.C.">',
        f'<rect width="{taille}" height="{taille}" rx="{cote(0.22)}" fill="#1d3268"/>',
        f'<rect x="{cote(0.20)}" y="{cote(0.16)}" width="{cote(0.60)}" '
        f'height="{cote(0.06)}" rx="{cote(0.03)}" fill="#38bdf8"/>',
    ]
    for part_gauche, hauteur, couleur in barres:
        morceaux.append(
            f'<rect x="{cote(part_gauche)}" y="{cote(ligne_base - hauteur)}" '
            f'width="{cote(0.16)}" height="{cote(hauteur)}" rx="{cote(0.05)}" '
            f'fill="{couleur}"/>'
        )
    morceaux.append("</svg>")
    return "".join(morceaux) + "\n"


def dimensions_png(chemin: Path) -> tuple[int, int]:
    """Largeur et hauteur lues dans l'en-tête IHDR, sans dépendance."""
    with chemin.open("rb") as flux:
        en_tete = flux.read(24)
    if en_tete[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{chemin.name} n'est pas un PNG")
    return struct.unpack(">II", en_tete[16:24])


def ecrire(verifier: bool = False) -> int:
    """Écrit les cinq images publiques (ou vérifie celles qui sont là)."""
    attendues: list[tuple[Path, tuple[int, int]]] = [
        (RACINE / "docs" / "apercu_social.png", TAILLE_DEPOT),
        (RACINE / "og-image.png", TAILLE_APERCU),
        (RACINE / "apple-touch-icon.png", (TAILLE_APPLE, TAILLE_APPLE)),
    ]
    if verifier:
        manquantes = [chemin.name for chemin, _ in attendues if not chemin.exists()]
        for chemin, (largeur, hauteur) in attendues:
            if chemin.exists() and dimensions_png(chemin) != (largeur, hauteur):
                manquantes.append(f"{chemin.name} (mauvaise taille)")
        for nom in ("favicon.ico", "favicon.svg"):
            if not (RACINE / nom).exists():
                manquantes.append(nom)
        if manquantes:
            print("ÉCHEC — images publiques absentes ou de mauvaise taille : "
                  + ", ".join(manquantes), file=sys.stderr)
            return 1
        print("Images publiques en place : aperçu du dépôt, aperçu de la page, "
              "icônes.")
        return 0

    for chemin, taille in attendues:
        image = (construire(*taille)
                 if chemin.name in ("apercu_social.png", "og-image.png")
                 else construire_icone(taille[0]))
        chemin.parent.mkdir(parents=True, exist_ok=True)
        image.save(chemin, "PNG", optimize=True)
        print(f"{chemin.relative_to(RACINE)} écrit : {taille[0]} × {taille[1]}, "
              f"{chemin.stat().st_size / 1024:.0f} Kio")

    icone = construire_icone(256)
    chemin_ico = RACINE / "favicon.ico"
    icone.save(chemin_ico, format="ICO",
               sizes=[(16, 16), (32, 32), (48, 48)])
    print(f"favicon.ico écrit : 16, 32 et 48 pixels, "
          f"{chemin_ico.stat().st_size / 1024:.0f} Kio")

    chemin_svg = RACINE / "favicon.svg"
    chemin_svg.write_text(svg_icone(), encoding="utf-8")
    print(f"favicon.svg écrit : {len(svg_icone())} caractères")
    return 0


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analyseur.add_argument("--verifier", action="store_true",
                           help="contrôle les images publiées sans les réécrire")
    analyseur.add_argument("--sortie", default=None,
                           help="écrit seulement l'aperçu du dépôt à cet endroit")
    arguments = analyseur.parse_args()

    if arguments.sortie:
        chemin = Path(arguments.sortie)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        image = construire(*TAILLE_DEPOT)
        image.save(chemin, "PNG", optimize=True)
        print(f"Aperçu social écrit : {chemin} ({chemin.stat().st_size / 1024:.0f} Kio)")
        return 0
    return ecrire(verifier=arguments.verifier)


if __name__ == "__main__":
    raise SystemExit(main())
