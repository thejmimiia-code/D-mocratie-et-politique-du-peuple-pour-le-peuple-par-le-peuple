#!/usr/bin/env python3
"""
outils/generer-doc-nuances.py — régénère les tableaux de `docs/17_NUANCES_INSTITUTIONNELLES_ET_REGLAGES.md`.

La documentation de la couche « nuances institutionnelles » est faite de prose (les
sections 1, 8 et 9, écrites à la main) et de sept tableaux qui, eux, ne sont que des
projections du module. Un chiffre recopié pourrit dès qu'un réglage est ajouté — c'est
exactement le défaut que cette page doit dénoncer chez les autres. Donc : les tableaux
sont générés, la prose reste libre.

    python3 outils/generer-doc-nuances.py              # réécrit les tableaux
    python3 outils/generer-doc-nuances.py --verifier   # sort en 1 si la page a pris du retard

Les sections sont repérées à leurs titres numérotés (`## 2. …`, `## 3. …`). Le générateur
remplace le corps de chaque section visée — jamais la prose des autres.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from simulateur.gouvernance_contrepouvoir import VERROUS  # noqa: E402
from simulateur.nuances_institutionnelles import (  # noqa: E402
    APPORTS,
    INDICES,
    NIVEAUX,
    REGLAGES,
    VERROUS_HORS_REGLAGE,
    coherence_nuances,
    delais_ajustes,
    fentes_recalculees,
    indices_nuances,
    reglages_catalogue,
    seuils_ajustes,
    tableau_des_niveaux,
    tableau_des_strates,
)
from simulateur.parametres import LEVIERS, PRESETS  # noqa: E402

CHEMIN = RACINE / "docs" / "17_NUANCES_INSTITUTIONNELLES_ET_REGLAGES.md"
TITRE_SECTION_3 = "Les {n} réglages (préfixe `reglage_`), la règle et l'effet"


def ligne(*cellules: str) -> str:
    return "| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in cellules) + " |"


def tableau(entete: tuple, lignes: list) -> str:
    corps = [ligne(*entete), "|" + "---|" * len(entete)] + [ligne(*c) for c in lignes]
    return "\n".join(corps)


def section_compteurs() -> str:
    reglages = reglages_catalogue()
    coherence = coherence_nuances()
    total = len(LEVIERS)
    return (
        f"Le catalogue compte **{total} leviers** en {len({lev.famille for lev in LEVIERS.values()})} "
        f"familles, dont **{len(reglages)} réglages institutionnels** (préfixe `reglage_`) "
        f"répartis sur **{len(NIVEAUX)} niveaux** : "
        + ", ".join(n.lower() for n in NIVEAUX)
        + f". Chacun de ces réglages est un curseur, un interrupteur ou un choix **comme les "
        "autres** — il traverse l'interface, les bulles, la page de vérification et les "
        f"{len(PRESETS)} préréglages — et il est de plus branché sur une règle de recalcul : "
        "seuils de contre-pouvoir, délais de procédure, fenêtre législative utile, solidité des "
        "fentes non écrites et indices institutionnels. "
        f"Le tout croise **{coherence['total_connaissances']['articles_croises']} articles** de "
        f"droit positif, **{coherence['total_connaissances']['verrous']} verrous**, "
        f"**{coherence['total_connaissances']['fentes']} fentes**, "
        f"**{coherence['total_connaissances']['trajets']} trajets**, "
        f"**{coherence['total_connaissances']['mecanismes']} mécanismes**, "
        f"**{coherence['total_connaissances']['instances']} instances** et "
        f"**{coherence['total_connaissances']['strategies']} stratégies** — chaque pièce de chaque "
        "registre étant joignable par au moins un réglage, ou explicitement expliquée "
        "(voir la section 10)."
    )


def section_niveaux() -> str:
    lignes = []
    for niveau in tableau_des_niveaux():
        lignes.append((
            f"**{niveau['niveau']}**", niveau["nombre_reglages"], len(niveau["reglages_actifs"]),
            len(niveau["articles"]),
        ))
    return ("Le module ne classe rien à la main : le niveau est celui du levier, et la colonne "
            "d'articles compte les identifiants du registre légal cités par ces leviers.\n\n"
            + tableau(("Niveau", "Réglages", "dont déplacés", "Articles du registre mobilisés"),
                      lignes))


def section_reglages() -> str:
    lignes = []
    for cle in sorted(reglages_catalogue()):
        levier, reglage = LEVIERS[cle], REGLAGES[cle]
        bornes = ("0 → 1" if levier.type == "interrupteur"
                  else f"{levier.minimum:g} → {levier.maximum:g}")
        lignes.append((
            f"`{cle}`<br>*{levier.libelle}*", levier.type, levier.unite, bornes,
            reglage.get("regle", ""), reglage.get("effet", ""),
        ))
    return ("Tableau produit par `outils/generer-doc-nuances.py` : les colonnes *règle* et *effet* "
            "sont celles que le module applique, pas une reformulation.\n\n"
            + tableau(("Réglage", "Type", "Unité", "Bornes", "Règle appliquée", "Ce que ça change"),
                      lignes))


def section_seuils() -> str:
    lignes = []
    for cle, valeur in seuils_ajustes().items():
        lignes.append((
            f"`{cle}`", valeur["nom"], valeur["article"], valeur["statu_quo"], valeur["regle"],
            f"{valeur['ecart']:+d}" if valeur["ecart"] else "—", valeur["unite"],
            ", ".join(valeur["reglages_appliques"]) or "—",
        ))
    explicites = "\n\n".join(
        f"- `{cle}` — {VERROUS[cle].nom} : {VERROUS_HORS_REGLAGE[cle]}"
        for cle in sorted(VERROUS_HORS_REGLAGE)
    )
    return ("Les verrous dont un réglage déplace le nombre, avec la valeur de droit et la valeur "
             "réglée au statu quo (tous les écarts sont donc à zéro tant qu'aucun curseur ne "
             "bouge) :\n\n"
             + tableau(("Verrou", "Nom", "Article", "Droit", "Réglé", "Écart", "Unité",
                        "Réglages"), lignes)
             + "\n\n## 4 bis. Les verrous qu'aucun réglage ne déplace, et pourquoi\n\n"
               "Un trou assumé et daté est une décision ; un trou non dit est une omission. Ces "
               f"{len(VERROUS_HORS_REGLAGE)} verrous sont hors d'atteinte d'un curseur de politique "
               "publique, et la raison est écrite ici plutôt que laissée à l'interprétation :\n\n"
               + explicites
            )


def section_delais() -> str:
    delais = delais_ajustes()
    lignes = [(f"`{t['cle']}`", t["nom"], t["categorie"], t["jours_de_rigueur_statu_quo"],
               t["jours_de_rigueur_regles"], "tenable" if t["tenable_dans_la_fenetre"]
               else "**HORS FENÊTRE**") for t in delais["trajets"]]
    jours = delais
    return ("Huit trajets, leurs jours de rigueur et leur tenue dans la fenêtre résiduelle de la "
             "session. Le calendrier n'est pas un ornement : c'est lui qui décide si une réforme "
             "tient dans un quinquennat.\n\n"
             + tableau(("Trajet", "Nom", "Catégorie", "Droit (jours)", "Réglé (jours)",
                        "Fenêtre"), lignes)
             + f"\n\nFenêtre résiduelle : {jours['fenetre_residuelle_statu_quo']} jours au statu quo, "
               f"{jours['fenetre_residuelle_reglee']} réglés. Textes forcables par session : "
               f"{jours['textes_forcables_par_session']}. Cohérence des jours avec l'oscillation "
               f"des assemblées : `{jours['jours_coherents_avec_oscillation']}`."
            )


def section_fentes() -> str:
    lignes = [(f"`{f['cle']}`", f["nom"], f["etage"], f["sens"], f["robustesse_statu_quo"],
               f["robustesse_reglee"], "verrouillée" if f["neutralisee"] else "ouverte",
               ", ".join(f["reglages_appliques"]) or "—") for f in fentes_recalculees()]
    return ("Solidité avant / après réglages, notée en défendabilité (0-100) et jamais en "
             "irréfragabilité : une fente n'est jamais « fermée », elle est rendue inutilisable "
             "par un réglage qui la précède dans le trajet.\n\n"
             + tableau(("Fente", "Nom", "Étage", "Profite à", "Solidité droit", "Solidité réglée",
                        "État", "Réglages"), lignes))


def section_indices() -> str:
    lignes = []
    pour = indices_nuances()
    for cle in INDICES:
        ligne = pour[cle]
        contributeurs = [c for c, apports in APPORTS.items() if cle in apports]
        lignes.append((f"`{cle}`", ligne["nom"], f"{ligne['valeur']:g}",
                       ligne["definition"], len(contributeurs)))
    return (f"Les {len(INDICES)} indices de la couche : base 50 au statu quo, somme pondérée des "
            "apports des réglages déplacés, bornée à [0, 100]. Un coefficient négatif est une "
            "perte, pas un bug.\n\n"
            + tableau(("Indice", "Nom", "Valeur", "Définition", "Réglages contributeurs"), lignes))


def section_strates() -> str:
    lignes = [(f"{s['strate']}", s["libelle"], len(s["reglages"]), len(s["reglages_actifs"]),
               len(s["verrous_touches"]), len(s["fentes_verrouillees"]))
              for s in tableau_des_strates()]
    return ("Les cinq strates du simulateur (celles des bulles et de l'onglet « Effets comparés "
            "par strate »), lues du point de vue institutionnel : la strate est déduite des thèmes "
            "d'effet de chaque réglage, jamais déclarée à la main.\n\n"
            + tableau(("Strate", "Niveau", "Réglages", "Déplacés", "Verrous touchés",
                       "Fentes verrouillées"), lignes))


def section_coherence() -> str:
    coherence = coherence_nuances()
    trous = {cle: valeur for cle, valeur in coherence.items()
             if isinstance(valeur, list) and cle not in ("fentes_ciblees_par_un_reglage",
                                                         "verrous_regles", "verrous_reglables",
                                                         "verrous_expliques_hors_reglage",
                                                         "fentes_couvertes_par_reglages")}
    lignes = [(f"`{cle}`", "aucun trou" if not valeur else f"**{len(valeur)}** : "
               + ", ".join(f"`{x}`" for x in valeur[:8]) + ("…" if len(valeur) > 8 else ""))
              for cle, valeur in sorted(trous.items()) if isinstance(valeur, list)]
    acces = tableau(("Registre", "Total", "Joignables par un réglage"),
                    [(f"`{cle}`", v["total"], v["avec_reglage"])
                     for cle, v in coherence["accesibilite_des_connaissances"].items()])
    return ("Contrôle exécuté par `coherence_nuances()` — le même que celui qu'exécute la suite de "
            "tests. Tant que toutes les lignes ci-dessous disent « aucun trou », la couche est "
            "sans angle mort ; la moindre liste non vide est une faute à corriger dans le module, "
            "pas dans ce document.\n\n"
            + tableau(("Garde-fou", "Résultat"), lignes)
            + "\n\nAccessibilité des registres, déduite des citations d'articles des modules "
              "`gouvernance_contrepouvoir` et `instances_et_dynamiques` :\n\n" + acces
            + f"\n\n**Limites.** {len(coherence['reglages_sans_cible_chiffree'])} réglage(s) sans "
              f"cible chiffrée, {coherence['reglages_catalogue']} réglages au catalogue, "
              f"{len(VERROUS_HORS_REGLAGE)} verrous expliqués hors réglage. Le module ne prétend "
              "pas simuler une révision constitutionnelle : il déplace les nombres que le droit "
              "laisse déplacer, et dit explicitement ceux qu'il ne peut pas toucher.")


#: Sections dont le corps est un tableau : elles seules sont régénérées.
SECTIONS = {
    "2": section_niveaux,
    "3": section_reglages,
    "4": section_seuils,
    "5": section_delais,
    "6": section_fentes,
    "7": section_indices,
    "10": section_coherence,
}


def reconstruire(texte: str) -> str:
    lignes = texte.split("\n")
    index_titres = []
    for i, ligne in enumerate(lignes):
        if (m := re.match(r"^## (\d+)\.", ligne)):
            index_titres.append((i, m.group(1)))
    # 1. le paragraphe de compte rendu, juste sous le titre de premier niveau
    corps = "\n".join(lignes[:index_titres[0][0]])
    nouveau = reconstruire_intro(corps) + "\n"
    # 2. chaque section visée, de titre à titre suivant
    for position, (debut, numero) in enumerate(index_titres):
        fin = (index_titres[position + 1][0] if position + 1 < len(index_titres)
               else len(lignes))
        titre = lignes[debut]
        if numero == "8" and "strates" not in titre.lower():
            # la section 8 est la prose « quatre expériences » : on ajoute les strates
            # après la section 7, une seule fois (repérée par son propre titre).
            nouveau += "\n".join(lignes[debut:fin]) + "\n"
            continue
        generateur = SECTIONS.get(numero)
        if generateur is None or numero == "9":
            nouveau += "\n".join(lignes[debut:fin]) + "\n"
            continue
        if numero == "3":
            titre = f"## 3. {TITRE_SECTION_3.format(n=len(reglages_catalogue()))}"
        nouveau += titre + "\n\n" + generateur() + "\n\n"
        if numero == "7":
            nouveau += "## 7 bis. Les cinq strates\n\n" + section_strates() + "\n\n"
    nouveau = re.sub(
        r"(Les vérifications `controles_neutres` du module le vérifient : )\{[^{}]*\}",
        lambda m: m.group(1) + json.dumps(coherence_nuances()["controles_neutres"],
                                          ensure_ascii=False),
        nouveau,
    )
    return re.sub(r"\n{3,}", "\n\n", nouveau).strip() + "\n"


def reconstruire_intro(corps: str) -> str:
    lignes = corps.split("\n")
    for i, ligne in enumerate(lignes):
        if ligne.startswith("Le catalogue compte"):
            fin = i
            while fin < len(lignes) and lignes[fin].strip():
                fin += 1
            lignes[i:fin] = [section_compteurs()]
            break
    return "\n".join(lignes)


def main() -> int:
    analyseur = argparse.ArgumentParser(description="Régénère les tableaux de docs/17.")
    analyseur.add_argument("--verifier", action="store_true",
                           help="ne rien écrire, sortir en 1 si la page n'est pas à jour")
    arguments = analyseur.parse_args()
    texte = CHEMIN.read_text(encoding="utf-8")
    reconstruit = reconstruire(texte)
    if arguments.verifier:
        if reconstruit.strip() != texte.strip():
            print("docs/17 a pris du retard sur le module : relancer "
                  "`python3 outils/generer-doc-nuances.py`.")
            return 1
        print("docs/17 est à jour.")
        return 0
    CHEMIN.write_text(reconstruit, encoding="utf-8")
    print(f"{CHEMIN.name} régénéré : {len(reconstruit.splitlines())} lignes, "
          f"{len(reglages_catalogue())} réglages, {len(VERROUS)} verrous.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
