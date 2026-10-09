#!/usr/bin/env python3
"""Génère `docs/VERIFICATION_DONNEES.md` : le statut de chaque donnée du simulateur.

La page est produite à partir du code (leviers, registre juridique, statuts de
`simulateur/verification.py`) : elle ne peut pas diverger du simulateur.

Usage :
    python3 outils/generer-page-verification.py            # écrit la page
    python3 outils/generer-page-verification.py --verifier # échoue si elle est obsolète
"""

from __future__ import annotations
from typing import List

import argparse
import sys
from collections import Counter
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from simulateur.parametres import FAMILLES, LEVIERS  # noqa: E402
from simulateur.reglements_lois import REGISTRE_LEGAL  # noqa: E402
from simulateur.verification import (  # noqa: E402
    DATE_AUDIT,
    FORMULAIRE_CONTRIBUTION,
    STATUTS,
    verification_article,
    verification_levier,
)

DESTINATION = RACINE / "docs" / "VERIFICATION_DONNEES.md"


def cellule(texte: str) -> str:
    return (texte or "").replace("|", "\\|").replace("\n", " ").strip() or "—"


def lien(url: str, libelle: str = "source") -> str:
    return f"[{libelle}]({url})" if url else "—"


def date_fr(iso: str) -> str:
    return "/".join(reversed(iso.split("-"))) if iso else "—"


def page() -> str:
    lignes: List[str] = []
    ecrire = lignes.append

    compte_leviers = Counter(verification_levier(c, levier.source).statut for c, levier in LEVIERS.items())
    compte_articles = Counter(verification_article(i).statut for i in REGISTRE_LEGAL)

    ecrire("# Vérification des données du simulateur")
    ecrire("")
    ecrire(
        f"> Page générée automatiquement le {date_fr(DATE_AUDIT)} par `outils/generer-page-verification.py`. "
        "Ne pas la modifier à la main : modifier `simulateur/verification.py`."
    )
    ecrire("")
    ecrire(
        "Le simulateur affiche **toutes** ses données, y compris celles qui ne sont pas "
        "encore vérifiées. Chacune porte un statut visible à l'écran, dans une copie et "
        "sur une impression. Cette page dit, pour chaque donnée, ce qui est vérifié, ce qui ne "
        "l'est pas, et pourquoi."
    )
    ecrire("")
    ecrire("## Les statuts")
    ecrire("")
    ecrire("| Statut | Signification |")
    ecrire("|---|---|")
    definitions = {
        "verifie": "Contrôlé sur une source officielle, date de consultation indiquée.",
        "partiel": "Une partie seulement (texte, date ou cadre) est contrôlée ; le chiffre attaché ne l'est pas.",
        "date_decalee": "La source est datée d'une année antérieure à 2026 : le chiffre doit être actualisé.",
        "non_verifie": "La source citée n'a pas été consultée, ou il s'agit d'une hypothèse interne (dossier de mandature).",
        "inaccessible": "Une consultation a été tentée et a échoué (source introuvable, payante ou fermée).",
    }
    for cle, libelle in STATUTS.items():
        ecrire(f"| **{libelle}** | {definitions[cle]} |")
    ecrire("")
    ecrire(
        "Une donnée non vérifiée n'est jamais masquée. Le simulateur affiche la valeur, son "
        "statut, et propose au citoyen de noter sa propre valeur sourcée. Cette valeur "
        "citoyenne est signalée comme non vérifiée à l'écran, dans une copie et sur une "
        "impression, et elle n'entre pas dans le calcul."
    )
    ecrire("")
    ecrire("## Bilan")
    ecrire("")
    ecrire("| Statut | Leviers | Articles du registre juridique |")
    ecrire("|---|---:|---:|")
    for cle, libelle in STATUTS.items():
        ecrire(f"| {libelle} | {compte_leviers.get(cle, 0)} | {compte_articles.get(cle, 0)} |")
    ecrire("")
    ecrire("## Contribuer : une donnée, une source, une date")
    ecrire("")
    ecrire(
        f"Vous connaissez une valeur officielle plus récente, une source plus fiable, ou vous "
        f"constatez une erreur ? [Ouvrez un signalement]({FORMULAIRE_CONTRIBUTION}). "
        "Indiquez le libellé de la donnée, la valeur officielle, le lien vers la source "
        "(Légifrance, EUR-Lex, Insee, PLF, Cour des comptes…) et la date de publication."
    )
    ecrire("")
    ecrire("## Leviers de politique publique")
    ecrire("")
    for cle_famille, famille in FAMILLES.items():
        leviers = [(c, levier) for c, levier in LEVIERS.items() if levier.famille == cle_famille]
        if not leviers:
            continue
        ecrire(f"### {famille['libelle']}")
        ecrire("")
        ecrire("| Levier | Valeur par défaut | Statut | Source citée | Ce qui est vérifié |")
        ecrire("|---|---|---|---|---|")
        for cle, levier in leviers:
            v = verification_levier(cle, levier.source)
            defaut = f"{levier.defaut:g} {levier.unite}" if levier.unite != "bool" else ("activé" if levier.defaut >= 0.5 else "désactivé")
            detail = v.note
            if v.verifie_le:
                detail += f" (consulté le {date_fr(v.verifie_le)})"
            if v.source_url:
                detail += f" {lien(v.source_url, 'lien officiel')}"
            ecrire(
                f"| <a id=\"{cle}\"></a>{cellule(levier.libelle)} `{cle}` | {cellule(defaut)} | "
                f"**{STATUTS[v.statut]}** | {cellule(levier.source)} | {cellule(detail)} |"
            )
        ecrire("")
    ecrire("## Textes juridiques du registre")
    ecrire("")
    ecrire("| Article | Texte | Statut | Ce qui est vérifié |")
    ecrire("|---|---|---|---|")
    for identifiant, art in REGISTRE_LEGAL.items():
        v = verification_article(identifiant)
        detail = v.note
        if v.verifie_le:
            detail += f" (consulté le {date_fr(v.verifie_le)})"
        if v.source_url:
            detail += f" {lien(v.source_url, 'lien officiel')}"
        ecrire(
            f"| <a id=\"{identifiant}\"></a>{cellule(art.article)} `{identifiant}` | "
            f"{cellule(art.code_ou_traite)} | **{STATUTS[v.statut]}** | {cellule(detail)} |"
        )
    ecrire("")
    return "\n".join(lignes) + "\n"


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analyseur.add_argument("--verifier", action="store_true", help="échoue si la page est obsolète")
    options = analyseur.parse_args()
    contenu = page()
    if options.verifier:
        actuel = DESTINATION.read_text(encoding="utf-8") if DESTINATION.is_file() else ""
        if actuel != contenu:
            print("docs/VERIFICATION_DONNEES.md est obsolète : relancer le générateur.", file=sys.stderr)
            return 1
        print("docs/VERIFICATION_DONNEES.md correspond aux statuts du simulateur.")
        return 0
    DESTINATION.write_text(contenu, encoding="utf-8")
    print(f"Page écrite : {DESTINATION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
