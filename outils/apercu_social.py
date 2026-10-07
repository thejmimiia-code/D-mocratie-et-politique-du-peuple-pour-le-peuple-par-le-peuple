#!/usr/bin/env python3
"""
outils/apercu_social.py — génère l'aperçu social du dépôt (1280 × 640).

L'aperçu social (« Social preview » dans *Edit repository details*) est la
vignette affichée lorsqu'un lien vers le dépôt est partagé. GitHub ne l'accepte
que par l'interface web : ce script produit donc l'image, à téléverser ensuite
dans les réglages du dépôt.

    python3 outils/apercu_social.py                # → docs/apercu_social.png
    python3 outils/apercu_social.py --sortie /tmp/apercu.png

Le dessin reprend la palette du simulateur et ses quatre chiffres clés, sans
dépendance autre que Pillow (`pip install pillow`).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RACINE = Path(__file__).resolve().parent.parent
LARGEUR, HAUTEUR = 1280, 640

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

CHEMIN_POLICES = Path("/usr/share/fonts/truetype/dejavu")


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


def centrer(dessin: ImageDraw.ImageDraw, texte: str, y: int,
            police_texte: ImageFont.FreeTypeFont, couleur: tuple[int, int, int]) -> None:
    """Écrit un texte centré horizontalement."""
    gauche, haut, droite, bas = dessin.textbbox((0, 0), texte, font=police_texte)
    dessin.text(((LARGEUR - (droite - gauche)) / 2 - gauche, y), texte,
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


def construire() -> Image.Image:
    """Compose l'aperçu social."""
    image = degrade(LARGEUR, HAUTEUR)
    dessin = ImageDraw.Draw(image)

    # Filet supérieur : rappel de la « console de veille » du simulateur.
    dessin.rectangle([0, 0, LARGEUR, 6], fill=ACCENT)

    police_titre = police("DejaVuSans-Bold.ttf", 58)
    police_sous_titre = police("DejaVuSans.ttf", 25)
    police_chiffre = police("DejaVuSans-Bold.ttf", 52)
    police_etiquette = police("DejaVuSans.ttf", 19)
    police_mini = police("DejaVuSans.ttf", 17)
    police_mono = police("DejaVuSansMono.ttf", 18)

    centrer(dessin, "Simulateur Macro-Politique", 62, police_titre, TEXTE)
    centrer(dessin, "Démocratie et politique : du peuple, pour le peuple, par le peuple",
            136, police_sous_titre, TEXTE_DIM)

    # Les quatre chiffres clés, en cartes.
    chiffres = [
        ("101", "leviers croisables", ACCENT),
        ("20", "domaines notés 0-100", VERT),
        ("38", "indicateurs publics", AMBRE),
        ("5", "échelons en cascade", VIOLET),
    ]
    largeur_carte, espace = 262, 24
    total = len(chiffres) * largeur_carte + (len(chiffres) - 1) * espace
    x = (LARGEUR - total) // 2
    y_carte, hauteur_carte = 200, 132
    for nombre, etiquette, couleur in chiffres:
        dessin.rounded_rectangle(
            [x, y_carte, x + largeur_carte, y_carte + hauteur_carte],
            radius=16, fill=CARTE, outline=BORDURE, width=1,
        )
        dessin.rounded_rectangle([x, y_carte, x + 5, y_carte + hauteur_carte],
                                 radius=3, fill=couleur)
        gauche, haut, droite, _ = dessin.textbbox((0, 0), nombre, font=police_chiffre)
        dessin.text((x + (largeur_carte - (droite - gauche)) / 2 - gauche, y_carte + 20),
                    nombre, font=police_chiffre, fill=couleur)
        gauche, haut, droite, _ = dessin.textbbox((0, 0), etiquette, font=police_etiquette)
        dessin.text((x + (largeur_carte - (droite - gauche)) / 2 - gauche, y_carte + 90),
                    etiquette, font=police_etiquette, fill=TEXTE_DIM)
        x += largeur_carte + espace

    # Le ruban de veille : strates et verdict, comme dans l'interface.
    y_ruban = 372
    gauche, haut, droite, _ = dessin.textbbox((0, 0), "VEILLE PERMANENTE", font=police_mono)
    largeur_etiquette = droite - gauche
    largeur_pastilles = 5 * 44 + 4 * 8
    largeur_verdict = 260
    total_ruban = largeur_etiquette + 26 + largeur_pastilles + 26 + largeur_verdict
    x = (LARGEUR - total_ruban) // 2
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
    gauche, haut, droite, bas = dessin.textbbox((0, 0), verdict, font=police_mini)
    largeur_texte = droite - gauche
    x_verdict = x + total_ruban - 18 - largeur_texte - 28
    dessin.rounded_rectangle(
        [x_verdict - 14, y_ruban + 11, x + total_ruban - 14, y_ruban + 41],
        radius=15, outline=AMBRE, width=2,
    )
    dessin.text((x_verdict, y_ruban + 17), verdict, font=police_mini, fill=AMBRE)

    centrer(dessin, "Chaque curseur se répercute en direct sur les 20 domaines "
                    "et les 5 échelons", 452, police_etiquette, TEXTE)

    # Pied : sources publiques (gauche) et dépôt (droite).
    dessin.line([(64, 528), (LARGEUR - 64, 528)], fill=BORDURE, width=1)
    dessin.text((64, 548), "Données publiques en direct : Eurostat · BCE · "
                           "Banque mondiale · Frankfurter", font=police_mini, fill=TEXTE_DIM)
    depot = "github.com/thejmimiia-code"
    gauche, haut, droite, _ = dessin.textbbox((0, 0), depot, font=police_mini)
    dessin.text((LARGEUR - 64 - (droite - gauche), 548), depot,
                font=police_mini, fill=ACCENT)
    dessin.text((64, 578), "5 échelons : local · national · européen · mondial · géopolitique",
                font=police_mini, fill=TEXTE_DIM)
    seuils = "seuils tolérables → hors-sol, strate par strate"
    gauche, haut, droite, _ = dessin.textbbox((0, 0), seuils, font=police_mini)
    dessin.text((LARGEUR - 64 - (droite - gauche), 578), seuils,
                font=police_mini, fill=ROUGE)
    return image


def main() -> None:
    analyseur = argparse.ArgumentParser(description="Aperçu social du dépôt (1280 × 640)")
    analyseur.add_argument("--sortie", default=str(RACINE / "docs" / "apercu_social.png"))
    arguments = analyseur.parse_args()
    chemin = Path(arguments.sortie)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    image = construire()
    assert image.size == (LARGEUR, HAUTEUR)
    image.save(chemin, "PNG", optimize=True)
    print(f"Aperçu social écrit : {chemin} ({chemin.stat().st_size / 1024:.0f} Kio)")


if __name__ == "__main__":
    main()
