#!/usr/bin/env python3
"""Génère `docs/22_REGISTRE_ENGAGEMENTS.md` : ce que le plan promet, et comment on le jugera.

Un projet qui publie d'avance la façon dont il sera évalué est plus difficile à
défendre par l'esquive, et plus facile à auditer. Ce document croise trois
sources, aucune recopiée :

1. **Les chiffres** viennent du moteur, rejoué ici sur le scénario de mandature
   (même chemin que `python3 main.py mandature`), année par année.
2. **Les gages et leur portée** viennent du registre de la contradiction
   (`simulateur/contradiction.py`), qui les déduit des leviers du catalogue.
3. **Les sources d'évaluation** sont nommées dans `SUIVI`, avec le seuil de
   réussite et le seuil d'échec : c'est la partie que le dépôt s'engage à
   regarder en face dans cinq ans.

Usage :

    python3 outils/generer-registre-engagements.py
    python3 outils/generer-registre-engagements.py --verifier
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from dataclasses import asdict  # noqa: E402
from contextlib import redirect_stdout  # noqa: E402
from io import StringIO  # noqa: E402

from simulateur.contradiction import objections, portee_du_levier  # noqa: E402
from simulateur.moteur import MoteurSimulationSystemique  # noqa: E402
from simulateur.scenarios import get_scenario_mandature_5_ans  # noqa: E402

DOC = RACINE / "docs" / "22_REGISTRE_ENGAGEMENTS.md"

#: Chaque indicateur suivi : l'unité, la source publique qui permettra de le vérifier,
#: et les deux seuils de lecture. Aucun de ces chiffres ne vient du modèle : ce sont
#: les repères extérieurs contre lesquels le modèle acceptera d'être jugé.
SUIVI: dict[str, dict[str, str]] = {
    "ratio_deficit_pib": {
        "nom": "Déficit public (% du PIB)",
        "unite": "% du PIB",
        "source": "INSEE, comptes nationaux (première estimation de l'année écoulée)",
        "reussite": "sous 3 % du PIB avant la fin de la mandature, et sous le statu quo simulé",
        "echec": "au-dessus du statu quo simulé pendant deux exercices consécutifs",
    },
    "ratio_dette_pib": {
        "nom": "Dette publique (% du PIB)",
        "unite": "% du PIB",
        "source": "INSEE, comptes nationaux — dette au sens de Maastricht",
        "reussite": "dette stabilisée puis en baisse sur les deux derniers exercices",
        "echec": "dette toujours en hausse en fin de mandature",
    },
    "taux_oat_pct": {
        "nom": "Taux de l'OAT 10 ans",
        "unite": "%",
        "source": "Agence France Trésor, courbe des taux ; Banque de France",
        "reussite": "détente du taux par rapport au niveau de départ de la mandature",
        "echec": "taux supérieur de plus d'un point au niveau de départ",
    },
    "spread_bund_bps": {
        "nom": "Écart OAT / Bund",
        "unite": "points de base",
        "source": "Banque de France, écart de taux à 10 ans contre l'Allemagne",
        "reussite": "écart revenu sous sa moyenne de long terme",
        "echec": "écart supérieur à celui observé au début de la mandature",
    },
    "tension_sociale_locale": {
        "nom": "Tension sociale locale (indice du modèle)",
        "unite": "/100",
        "source": "aucune source directe : indice du modèle, à confronter aux faits sociaux "
                  "(conflits, mobilisations, baromètres de confiance)",
        "reussite": "direction à la baisse sur les trois derniers exercices",
        "echec": "pic supérieur au niveau de départ",
    },
    "confiance_democratique": {
        "nom": "Confiance démocratique (indice du modèle)",
        "unite": "/100",
        "source": "baromètre de la confiance politique (CEVIPOF) pour la tendance réelle",
        "reussite": "progression dans le baromètre réel, pas seulement dans le modèle",
        "echec": "baisse du baromètre réel malgré la hausse simulée",
    },
}


def _fr(valeur: float, decimales: int = 2) -> str:
    """Un nombre écrit à la française : virgule décimale, comme dans les documents du dépôt."""
    return f"{valeur:.{decimales}f}".replace(".", ",")


def _ligne_valeur(valeur: object, unite: str) -> str:
    if isinstance(valeur, bool):
        return "oui" if valeur else "non"
    if isinstance(valeur, (int, float)):
        return f"{_fr(float(valeur))} {unite}".strip()
    return f"{valeur} {unite}".strip()


def _trajectoire() -> list[dict]:
    """Rejoue le scénario de mandature sans rien afficher.

    Même chemin que `python3 main.py mandature` — le moteur, les mêmes décisions —
    mais la sortie console du CLI est capturée : un générateur de document n'a pas
    à écrire un tableau dans le terminal de celui qui le lance.
    """
    moteur = MoteurSimulationSystemique()
    for decision in get_scenario_mandature_5_ans():
        moteur.appliquer_etape(decision)
    with redirect_stdout(StringIO()):
        return [asdict(etape) for etape in moteur.historique_etapes]


def composer() -> str:
    """Le registre, régénéré : moteur rejoué, gages déduits, sources nommées."""
    etapes = _trajectoire()
    lignes = [
        "# 22. Registre des engagements : ce que le plan promet, et comment on le jugera",
        "",
        "> Un projet qui annonce à l'avance la façon dont il sera jugé se rend falsifiable. "
        "Ce registre rejoue le scénario de mandature (`python3 main.py mandature`), reprend les "
        "gages du registre de la contradiction, et nomme pour chaque indicateur la source "
        "extérieure qui dira si la promesse a tenu — y compris contre le modèle.",
        "",
        "> Document engendré par `outils/generer-registre-engagements.py` : les chiffres "
        "viennent du moteur, les gages du catalogue, jamais d'une saisie.",
        "",
        "---",
        "",
        "## 1. La trajectoire simulée, année par année",
        "",
        "| Année | Déficit (% PIB) | Dette (% PIB) | OAT 10 ans | Écart Bund | Tension sociale "
        "| Confiance démocratique |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for etape in etapes:
        lignes.append(
            f"| An {etape['annee']} | {_fr(etape['ratio_deficit_pib'])} "
            f"| {_fr(etape['ratio_dette_pib'])} | {_fr(etape['taux_oat_pct'])} "
            f"| {_fr(etape['spread_bund_bps'], 1)} pb "
            f"| {_fr(etape['tension_sociale_locale'], 1)}/100 "
            f"| {_fr(etape['confiance_democratique'], 1)}/100 |")
    lignes += [
        "",
        "Ces valeurs sont des sorties de modèle sur des hypothèses nommées "
        "(`docs/METHODOLOGIE.md`) : elles décrivent une trajectoire sous politique simulée, pas "
        "une prévision. Le dossier public reconnaît deux corrections d'hypothèses qui décalent "
        "l'atterrissage du déficit vers 3,05 à 3,26 % en année 5 (objections n° 11 et n° 12 du "
        "registre) : elles sont donc attendues, pas découvertes.",
        "",
        "---",
        "",
        "## 2. Ce qui sera regardé, par quelle source, et à quel seuil",
        "",
        "| Indicateur | Source d'évaluation | Réussite | Échec |",
        "|---|---|---|---|",
    ]
    for cle, suivi in SUIVI.items():
        exemple = next((etape[cle] for etape in etapes if cle in etape), None)
        lignes.append(f"| **{suivi['nom']}** (aujourd'hui : "
                      f"{_ligne_valeur(exemple, suivi['unite'])}) | {suivi['source']} "
                      f"| {suivi['reussite']} | {suivi['echec']} |")
    lignes += [
        "",
        "Deux indicateurs n'ont pas de source publique directe : la tension sociale et la "
        "confiance démocratique sont des indices du modèle. Le registre le dit au lieu de les "
        "présenter comme des mesures — c'est précisément l'objection n° 13, non résolue à ce jour.",
        "",
        "---",
        "",
        "## 3. Les gages, leur portée, et la réserve disponible",
        "",
        "| Fiche | Mesure | Portée du levier | Gage du dossier | Réserve de portée |",
        "|---|---|---:|---:|---:|",
    ]
    reserve = 0.0
    for objection in objections("mesure"):
        if objection.gage_mde_an is None:
            lignes.append(f"| {objection.fiche} | {objection.titre} | — | — | — |")
            continue
        portee = portee_du_levier(objection.levier)
        marge = round(abs(portee or 0) - abs(objection.gage_mde_an), 2)
        reserve += marge
        lignes.append(f"| {objection.fiche} | {objection.titre} | {_fr(portee, 0)} Md€/an "
                      f"| {_fr(objection.gage_mde_an, 0)} Md€/an | {_fr(marge, 0)} Md€/an |")
    lignes += [
        "",
        f"**Réserve de portée disponible : {_fr(reserve, 0)} Md€/an.**",
        "",
        "Cette réserve n'est pas un rendement attendu : c'est l'écart entre ce que le dossier "
        "ose compter (les gages) et ce que le catalogue permet d'explorer (les portées). Elle "
        "répond à une objection déjà reçue — un équilibre à 60 = 60 sans marge de sécurité "
        "(objection n° 23) — et elle se vérifie en une commande : "
        "`GET /api/objections?famille=mesure`.",
        "",
        "---",
        "",
        "## 4. Ce que ce registre ne fait pas",
        "",
        "- Il ne transforme pas une sortie de modèle en promesse électorale : les cibles du plan "
        "restent des objectifs politiques, et les chiffres ci-dessus sont conditionnels aux "
        "hypothèses nommées.",
        "- Il ne prétend pas que les sources d'évaluation seront disponibles au calendrier "
        "prévu : les comptes nationaux sont révisés, et certains indicateurs n'ont pas de "
        "millésime annuel.",
        "- Il ne clôt aucune objection : chaque ligne renvoie au numéro du registre "
        "(`docs/21_OBJECTIONS_OUVERTES.md`), où la concession et le fait de réfutation sont "
        "écrits.",
        "",
    ]
    return "\n".join(lignes)


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--verifier", action="store_true",
                           help="n'écrit rien et échoue si le registre a pris du retard")
    options = analyseur.parse_args()
    contenu = composer()
    actuel = DOC.read_text(encoding="utf-8") if DOC.exists() else ""
    if actuel == contenu:
        print(f"à jour : {DOC.relative_to(RACINE)}")
        return 0
    if options.verifier:
        print(f"registre des engagements en retard : {DOC.relative_to(RACINE)}", file=sys.stderr)
        return 1
    DOC.write_text(contenu, encoding="utf-8")
    print(f"écrit : {DOC.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
