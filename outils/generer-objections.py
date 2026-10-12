#!/usr/bin/env python3
"""Génère les documents d'objections à partir de `simulateur/contradiction.py`.

Trois sorties, une seule source :

1. `docs/05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md` — le guide tactique. Son
   introduction et son titre sont réécrits ici ; chaque fiche existante est
   conservée mot pour mot et reçoit un bloc généré « objections fortes ».
2. `docs/20_CONTRE_MODELES.md` — les quatre modèles alternatifs auxquels le plan
   se mesure, et ce que le simulateur en dit.
3. `docs/21_OBJECTIONS_OUVERTES.md` — le registre complet : tableau des 24
   objections, texte intégral de celles qui visent le modèle, et la façon d'en
   déposer une.

Usage :

    python3 outils/generer-objections.py            # écrit les trois documents
    python3 outils/generer-objections.py --verifier # échoue si un document a pris du retard

Le mode `--verifier` est celui qu'utilisent les tests : un document qui n'est plus
la sortie du générateur est un document faux.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from simulateur.contradiction import (  # noqa: E402
    CONTRE_MODELES,
    OBJECTIONS,
    STATUTS,
    Objection,
    coherence,
    objections,
    portee_du_levier,
)

DOC_GUIDE = RACINE / "docs" / "05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md"
DOC_CONTRE_MODELES = RACINE / "docs" / "20_CONTRE_MODELES.md"
DOC_REGISTRE = RACINE / "docs" / "21_OBJECTIONS_OUVERTES.md"

DEBUT = "<!-- OBJECTIONS FORTES : bloc généré par outils/generer-objections.py, ne pas éditer à la main -->"
FIN = "<!-- fin du bloc généré -->"

TITRE_GUIDE = "# GUIDE D'AUTODÉFENSE STRATÉGIQUE — OBJECTIONS, CONCESSIONS ET RÉPONSES"

INTRODUCTION = """## I. PRÉSENTATION DU GUIDE

Ce document est le **manuel tactique de combat politique, médiatique et juridique**.  
Il est destiné à quiconque porte le projet de mandature face aux journalistes hostiles, aux éditorialistes de plateaux télévisés, aux lobbys industriels et financiers, et aux appareils partisans de l'opposition qui chercheront systématiquement à discréditer, caricaturer ou effrayer l'opinion.

Pour chacun des 10 thèmes cardinaux du plan, ce guide décompose cinq pièces :

1. **L'attaque brute** entendue dans les médias ou dans l'hémicycle.
2. **Le sophisme et la manipulation** cachés derrière la critique.
3. **La parade technique et juridique incontestable** (textes, articles de lois, jurisprudence).
4. **Les données chiffrées massues** issues des rapports officiels de l'État.
5. **La réplique de clôture (« Punchline »)** pour clore définitivement le débat en direct.

### Le renversement : répondre à la meilleure objection, pas à la plus faible

Un guide qui ne répond qu'aux attaques faciles se fait démonter par la première objection compétente — celle qu'un économiste, un juriste ou un journaliste sérieux formulera en une phrase, et que personne n'aura préparée. Chaque fiche porte donc désormais **cinq pièces supplémentaires**, rédigées dans cet ordre :

6. **La meilleure version de l'objection** — la critique écrite comme la formulerait un contradicteur compétent et honnête, pas une caricature.
7. **Ce que nous concédons** — ce que le dépôt admet, sans marchandage. Une objection sans concession est une objection qui n'a pas été lue.
8. **Ce que nous maintenons, et pourquoi** — ce qui survit à la concession. Sans cette pièce, concéder serait se rallier.
9. **Ce qui nous ferait changer d'avis** — le fait, nommé et vérifiable, qui trancherait le débat dans l'autre sens. Une position qu'aucun fait ne peut ébranler n'est pas une position, c'est une croyance.
10. **Le statut et les suites** — où en est le traitement, ce qu'il a déjà changé dans le dépôt, et la marge de manœuvre chiffrée du levier concerné.

Les statuts sont volontairement inconfortables : `réfutée` ne veut pas dire « l'adversaire était de mauvaise foi », mais « la réponse tient sous sa forme forte » ; `concédée` et `partiellement concédée` engagent à écrire ce qui change ; `en cours` et `ouverte` disent ce qui n'est pas terminé au lieu de le maquiller.

Aucun chiffre n'est recopié dans ce document : les gages viennent des leviers du catalogue (`simulateur/parametres.py`) et l'écart entre le gage et la portée maximale du levier est calculé, jamais saisi. Les objections qui visent le modèle lui-même — hypothèses, seuils, indicateurs — sont dans `docs/21_OBJECTIONS_OUVERTES.md` ; les modèles alternatifs cohérents auxquels ce plan se mesure sont dans `docs/20_CONTRE_MODELES.md`.

---
"""


def _bloc(o: Objection) -> str:
    """Le bloc ajouté sous une fiche, ou sous une objection de modèle."""
    lignes = [
        DEBUT,
        "",
        "### La meilleure version de l'objection",
        "",
        f"> {o.objection_forte}",
        "",
    ]
    if o.attaque_faible:
        lignes += [
            "*Attaque d'origine conservée pour mémoire :*",
            "",
            f"> {o.attaque_faible}",
            "",
        ]
    lignes += [
        "### Ce que nous concédons",
        "",
        o.concession,
        "",
        "### Ce que nous maintenons, et pourquoi",
        "",
        o.maintien,
        "",
        "### Ce qui nous ferait changer d'avis",
        "",
        o.falsification,
        "",
        "### Statut et suites",
        "",
        f"**`{o.statut}`** — {STATUTS[o.statut]}.",
        "",
    ]
    if o.changements:
        lignes += [f"*Ce que cela change dans le dépôt :* {o.changements}.", ""]
    if o.suivi:
        lignes += [f"*Suivi :* {o.suivi}.", ""]
    if o.levier:
        portee = portee_du_levier(o.levier)
        if portee is not None and o.gage_mde_an is not None:
            marge = round(abs(portee) - abs(o.gage_mde_an), 2)
            lignes += [
                f"*Levier `{o.levier}`* : portée maximale **{portee} Md€/an**, gage retenu par le "
                f"dossier **{o.gage_mde_an} Md€/an**, soit une marge de portée de {marge} Md€/an "
                "non comptée dans l'équilibre.",
                "",
            ]
        else:
            lignes += [f"*Levier `{o.levier}`* : réforme sans montant au catalogue.", ""]
    lignes += ["### Sources", ""]
    for source in o.sources:
        if source.nature == "interne":
            detail = f" — {source.reference}" if source.reference else ""
            lignes.append(f"- **Interne** : `{source.chemin}`{detail}")
        else:
            origine = f" (portée par {source.origine})" if source.origine else ""
            lignes.append(f"- **Externe** : {source.reference} — *{source.date}*{origine}")
    lignes += ["", FIN]
    return "\n".join(lignes)


def _sans_bloc(texte: str) -> str:
    """Retire les blocs générés précédents, pour que la génération soit idempotente."""
    return re.sub(rf"\n*{re.escape(DEBUT)}.*?{re.escape(FIN)}\n?", "", texte, flags=re.S)


def _decouper_fiches(texte: str) -> list[tuple[int, str]]:
    """Découpe le guide en (numéro de fiche, corps du texte) sur les titres `## FICHE n`."""
    morceaux = re.split(r"\n---\n\n(?=## FICHE )", texte)
    fiches: list[tuple[int, str]] = []
    for morceau in morceaux:
        trouve = re.search(r"^## FICHE (\d+)", morceau, re.M)
        if trouve:
            # Un `---` final appartient à la séparation, pas à la fiche : sans ce
            # nettoyage, une deuxième génération empilerait les séparateurs.
            corps = re.sub(r"\n+---\s*$", "", morceau.rstrip())
            fiches.append((int(trouve.group(1)), corps))
    return fiches


def composer_guide() -> str:
    """Le guide tel qu'il doit être : introduction régénérée + blocs sous chaque fiche."""
    actuel = _sans_bloc(DOC_GUIDE.read_text(encoding="utf-8"))
    fiches = _decouper_fiches(actuel)
    if not fiches:
        raise SystemExit("aucune fiche reconnue dans docs/05 : la structure a changé")

    par_fiche = {o.fiche: o for o in objections("mesure")}
    if sorted(numero for numero, _ in fiches) != sorted(par_fiche):
        raise SystemExit(
            "les fiches du guide et les objections de mesure ne coïncident plus : "
            f"{sorted(numero for numero, _ in fiches)} contre {sorted(par_fiche)}")

    corps = [TITRE_GUIDE, "", "---", "", INTRODUCTION]
    for numero, morceau in sorted(fiches):
        corps += [morceau, "", _bloc(par_fiche[numero]), "", "---", ""]
    return "\n".join(corps).rstrip() + "\n"


def composer_contre_modeles() -> str:
    lignes = [
        "# 20. Contre-modèles : les quatre thèses auxquelles ce plan se mesure",
        "",
        "> Un projet qui ne se compare qu'à ses repoussoirs — le statu quo et l'austérité — gagne "
        "tous les débats qu'il organise. Ce document fait l'inverse : il expose quatre modèles "
        "alternatifs *cohérents*, écrits au mieux, et dit pour chacun ce que le simulateur en "
        "montre, ce que le dépôt leur concède, et où il ne les suit pas.",
        "> Contenu engendré par `outils/generer-objections.py` à partir de "
        "`simulateur/contradiction.py` : aucune phrase de ce document n'existe ailleurs.",
        "",
        "---",
        "",
    ]
    for modele in CONTRE_MODELES.values():
        lignes += [
            f"## {modele.titre}",
            "",
            f"*Porté par : {modele.porte_par}.*",
            "",
            "### La thèse",
            "",
            modele.these,
            "",
            "### Ce que le simulateur en dit",
            "",
            modele.ce_que_le_simulateur_en_dit,
            "",
        ]
        if modele.scenarios:
            scenarios = ", ".join(f"`{cle}`" for cle in modele.scenarios)
            lignes += [f"*Scénarios comparables :* {scenarios}.", ""]
        if modele.presets:
            presets = ", ".join(f"`{cle}`" for cle in modele.presets)
            lignes += [f"*Préréglages existants :* {presets}.", ""]
        lignes += [
            "### Ce que nous lui concédons",
            "",
            modele.concession,
            "",
            "### Où nous ne le suivons pas",
            "",
            modele.divergence,
            "",
        ]
        if modele.ouverts:
            lignes += ["### Ce qui reste ouvert", "", modele.ouverts, ""]
        lignes += ["---", ""]
    lignes += [
        "## Ce que ce document ne prétend pas",
        "",
        "Il ne prétend pas que ces quatre thèses soient fausses : il prétend qu'elles sont "
        "discutables avec des chiffres, et il nomme ce qui manque encore pour trancher — un "
        "préréglage « État minimal », un échéancier de déploiement par levier, un coût de "
        "réaffectation chiffré, une consolidation orthodoxe modélisée. Tant que ces pièces "
        "manquent, le dépôt dit qu'elles manquent plutôt que de faire semblant d'avoir répondu.",
        "",
    ]
    return "\n".join(lignes)


def composer_registre() -> str:
    lignes = [
        "# 21. Objections ouvertes : le registre",
        "",
        "> Toute objection reçue est enregistrée ici, avec son numéro, son statut, la concession "
        "qu'elle a obtenue et la modification qu'elle a provoquée. Ce tableau est la sortie de "
        "`simulateur/contradiction.py` : une objection qui n'y figure pas n'a pas été traitée.",
        "",
        "Les objections qui visent une **mesure** sont développées sous la fiche correspondante du "
        "guide (`docs/05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md`) ; celles qui visent le "
        "**modèle** sont développées ici, parce qu'aucune fiche ne les porte.",
        "",
        "---",
        "",
        "## 1. Le registre complet",
        "",
        "| # | Objection | Famille | Statut | Suivi |",
        "|---|---|---|---|---|",
    ]
    for o in objections():
        famille = "mesure" if o.famille == "mesure" else "modèle"
        lignes.append(f"| {o.numero} | {o.titre} | {famille} | `{o.statut}` | {o.suivi or '—'} |")
    lignes += [
        "",
        "### Comment lire les statuts",
        "",
    ]
    for statut, definition in STATUTS.items():
        lignes.append(f"- **`{statut}`** — {definition}.")
    lignes += [
        "",
        "---",
        "",
        "## 2. Les objections de modèle, développées",
        "",
    ]
    for o in objections("modele"):
        lignes += [f"### {o.numero}. {o.titre}", "", o.attaque_faible, "", _bloc(o), "", "---", ""]
    lignes += [
        "## 3. Comment déposer une objection",
        "",
        "Une objection se dépose par le modèle d'issue **« Objection sourcée »** "
        "(`.github/ISSUE_TEMPLATE/objection.md`) : mesure visée, objection en une phrase, source "
        "datée, chiffre alternatif proposé, et ce qui ferait changer d'avis celui qui la formule. "
        "Une objection sans source est examinée comme une question, pas comme une objection : "
        "c'est le minimum pour que le débat porte sur des faits.",
        "",
        "Le registre n'est pas trié par confort : les objections **concédées** et **en cours** y "
        "restent visibles, avec leur numéro. Une objection qui disparaîtrait du tableau serait le "
        "premier signe que ce dépôt ne s'audite plus lui-même.",
        "",
    ]
    return "\n".join(lignes)


def ecrire(verifier: bool) -> int:
    """Écrit les trois documents, ou vérifie qu'ils sont à jour. Renvoie un code de sortie."""
    garde_fous = {cle: valeurs for cle, valeurs in coherence().items() if valeurs}
    if garde_fous:
        print("garde-fous du registre en défaut :", garde_fous, file=sys.stderr)
        return 1

    attendus = {
        DOC_GUIDE: composer_guide(),
        DOC_CONTRE_MODELES: composer_contre_modeles(),
        DOC_REGISTRE: composer_registre(),
    }
    retards = []
    for chemin, contenu in attendus.items():
        actuel = chemin.read_text(encoding="utf-8") if chemin.exists() else ""
        if actuel == contenu:
            continue
        if verifier:
            retards.append(chemin.name)
        else:
            chemin.write_text(contenu, encoding="utf-8")
            print(f"écrit : {chemin.relative_to(RACINE)}")

    if verifier and retards:
        print("documents en retard sur le registre : " + ", ".join(retards), file=sys.stderr)
        return 1
    if verifier:
        print("objections : documents à jour "
              f"({len(OBJECTIONS)} objections, {len(CONTRE_MODELES)} contre-modèles)")
    return 0


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--verifier", action="store_true",
                           help="n'écrit rien et échoue si un document a pris du retard")
    options = analyseur.parse_args()
    return ecrire(options.verifier)


if __name__ == "__main__":
    raise SystemExit(main())
