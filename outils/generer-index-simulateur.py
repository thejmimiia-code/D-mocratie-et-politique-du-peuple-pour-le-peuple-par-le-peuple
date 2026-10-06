#!/usr/bin/env python3
"""Génère `index.html` depuis la page interactive du moteur.

La racine Vercel doit contenir la vraie interface du simulateur, avec le
catalogue de scénarios injecté exactement comme dans ``dashboard.py``.

Usage :
    python3 outils/generer-index-simulateur.py
    python3 outils/generer-index-simulateur.py --verifier
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from simulateur.dashboard import SCENARIOS  # noqa: E402
from simulateur.interface import HTML_PAGE  # noqa: E402


def construire_page() -> str:
    """Injecte dans la page le même JSON de scénarios que le serveur local."""
    scenarios_json = json.dumps(
        {
            cle: {nom: valeur for nom, valeur in scenario.items() if nom != "fn"}
            for cle, scenario in SCENARIOS.items()
        },
        ensure_ascii=False,
    )
    if HTML_PAGE.count("===SCENARIOS_JSON===") != 1:
        raise RuntimeError("HTML_PAGE doit contenir exactement un placeholder de scénarios")
    return HTML_PAGE.replace("===SCENARIOS_JSON===", scenarios_json)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--verifier",
        action="store_true",
        help="vérifie que index.html correspond au moteur, sans l'écrire",
    )
    args = parser.parse_args()

    destination = ROOT / "index.html"
    contenu = construire_page()
    if args.verifier:
        try:
            actuel = destination.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"index.html absent ou illisible : {exc}", file=sys.stderr)
            return 1
        if actuel != contenu:
            print("index.html est différent de HTML_PAGE : relancer le générateur.", file=sys.stderr)
            return 1
        print("index.html correspond à HTML_PAGE et au catalogue des scénarios.")
        return 0

    destination.write_text(contenu, encoding="utf-8")
    print(f"Page interactive écrite dans {destination} ({len(contenu)} caractères).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
