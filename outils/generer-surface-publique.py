#!/usr/bin/env python3
"""Écrit — ou vérifie — les fichiers que lisent les robots, à la racine du dépôt.

Vercel ne sait pas exécuter de code pour ces fichiers : il sert tels quels les
fichiers présents à la racine. Ils sont donc engendrés ici depuis
``simulateur/surface_publique.py``, qui reste la source unique — le routeur
Python (``simulateur/dashboard.py``) sert, lui, le même texte sans passer par le
disque.

Usage :
    python3 outils/generer-surface-publique.py
    python3 outils/generer-surface-publique.py --verifier
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from simulateur import surface_publique  # noqa: E402

#: Chemin publié → fichier écrit à la racine du dépôt.
FICHIERS: dict[str, str] = {
    "/robots.txt": "robots.txt",
    "/sitemap.xml": "sitemap.xml",
    "/llms.txt": "llms.txt",
    "/llms-full.txt": "llms-full.txt",
}


def ecrire(verifier: bool = False) -> int:
    ecarts: list[str] = []
    for chemin, nom in FICHIERS.items():
        attendu = surface_publique.texte(chemin)
        if attendu is None:                      # pragma: no cover - garde-fou
            print(f"ÉCHEC — {chemin} n'est pas produit par surface_publique", file=sys.stderr)
            return 1
        destination = ROOT / nom
        present = destination.read_text(encoding="utf-8") if destination.exists() else None
        if verifier:
            if present != attendu:
                ecarts.append(nom)
            else:
                print(f"  ✓ {nom} — {len(attendu)} caractères")
            continue
        if present != attendu:
            destination.write_text(attendu, encoding="utf-8")
            print(f"{nom} écrit : {len(attendu)} caractères")
        else:
            print(f"{nom} déjà à jour : {len(attendu)} caractères")
    if ecarts:
        print(
            "ÉCHEC — ces fichiers ne correspondent plus à la surface publique : "
            + ", ".join(ecarts)
            + "\n        relancez sans --verifier pour les réécrire.",
            file=sys.stderr,
        )
        return 1
    if verifier:
        print("Surface publique à jour.")
    return 0


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analyseur.add_argument(
        "--verifier",
        action="store_true",
        help="vérifie que les fichiers publiés correspondent au module, sans les écrire",
    )
    arguments = analyseur.parse_args()
    return ecrire(verifier=arguments.verifier)


if __name__ == "__main__":
    raise SystemExit(main())
