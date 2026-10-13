#!/usr/bin/env python3
"""Vérifie que chaque compteur annoncé dans le dépôt est le compteur du code.

Un dépôt qui annonce un vieux compte de leviers dans son `pyproject.toml`, un
autre dans la description GitHub et un troisième dans son README ne ment pas
exprès : il a laissé des chiffres écrits à la main vieillir chacun de son côté.
Le remède n'est pas de relire, c'est de comparer.

Ce contrôle lit les compteurs réels dans les modules (`LEVIERS`, `PRESETS`,
`DOMAINES`, les réglages `reglage_*`, le catalogue des scénarios, les garde-fous,
le registre de données publiques, les routes de l'API) et confronte chaque
phrase du dépôt qui les annonce au chiffre du jour. Les documents datés
(journaux, R&D, dossier d'origine) sont exemptés, avec leur raison écrite : ils
gardent les chiffres de leur époque.

Usage :

    python3 outils/verifier-compteurs.py            # par défaut, vérifie
    python3 outils/verifier-compteurs.py --liste    # règles et valeurs de référence
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

try:                                        # lancé depuis la racine du dépôt
    from outils.chargement_module import charger_module
except ImportError:                         # lancé depuis outils/
    from chargement_module import charger_module  # type: ignore[no-redef]

from simulateur.dashboard import SCENARIOS  # noqa: E402
from simulateur.domaines import DOMAINES, SPECS  # noqa: E402
from simulateur.donnees_live import INDICATEURS as INDICATEURS_PUBLICS  # noqa: E402
from simulateur.nuances_institutionnelles import reglages_catalogue  # noqa: E402
from simulateur.parametres import FAMILLES, LEVIERS, PRESETS  # noqa: E402
from simulateur.seuils import GARDE_FOUS, GARDE_FOUS_ECART  # noqa: E402
from simulateur.societe_domaines import DOMAINES_SOCIETAUX  # noqa: E402

#: Le nombre de strates du modèle gigogne : local, national, européen, mondial,
#: géopolitique. Il n'est pas déduit d'un catalogue (il n'en existe pas pour les
#: strates) : il est écrit ici une fois, et comparé partout ailleurs.
ECHELONS = 5


def _routes_api() -> int:
    """Le nombre de routes servies, lu dans le générateur de la fonction Vercel.

    Le lire là plutôt que dans `api/[...path].py` évite de compter un fichier
    engendré : c'est le générateur qui fait foi, l'autre fichier en découle.
    """
    chemin = RACINE / "outils" / "generer-fonctions-api.py"
    module = charger_module("generateur_fonctions_api", chemin)
    routes = getattr(module, "ROUTES", None)
    if routes is None:                      # repli : la table des routes du fichier engendré
        return len(re.findall(r"^\s*\"[a-z_]+\"", (RACINE / "api" / "[...path].py").read_text("utf-8"), re.M))
    return len(routes)


@dataclass(frozen=True)
class Regle:
    """Une phrase qui annonce un compteur, et le référentiel qu'elle doit suivre."""

    motif: str
    quoi: str
    ou: str
    #: Une phrase d'essai contenant ``{n}`` : elle sert à la contre-épreuve des
    #: tests, qui vérifie que chaque règle reconnaît le compteur qu'elle prétend
    #: vérifier — et refuse un faux.
    gabarit: str
    #: Le référentiel d'un second compteur cité dans le gabarit (``{autre}``), quand la
    #: phrase en annonce deux — « 20 domaines, 74 indicateurs » par exemple.
    autre: str | None = None


def _reference() -> dict[str, int]:
    """Les valeurs de référence, toutes déduites du code — jamais saisies ici."""
    # Famille « taux » (P1-3) : les trois seuils structurants du plan, vérifiés
    # comme des compteurs — 3 % déficit (Maastricht), 30 % PME (CCP L.2113-10),
    # 5,5 % TVA (directive 2022/542). Le nombre 3 est déduit de la liste
    # ci-dessous, pas saisi à la main ailleurs.
    _TAUX_STRUCTURANTS = 3
    return {
        "leviers": len(LEVIERS),
        "reglages": len(reglages_catalogue()),
        "presets": len(PRESETS),
        "familles": len(FAMILLES),
        "domaines": len(DOMAINES),
        "indicateurs": len(SPECS),
        "indicateurs_publics": len(INDICATEURS_PUBLICS),
        "domaines_societe": len(DOMAINES_SOCIETAUX),
        "garde_fous": len(GARDE_FOUS) + len(GARDE_FOUS_ECART),
        "scenarios": len(SCENARIOS),
        "echelons": ECHELONS,
        "routes": _routes_api(),
        "taux_structurants": _TAUX_STRUCTURANTS,
    }


def _r(motif: str, quoi: str, ou: str, gabarit: str, autre: str | None = None) -> Regle:
    return Regle(motif, quoi, ou, gabarit, autre)


@dataclass(frozen=True)
class Interdit:
    """Un compte qu'un document vivant ne doit pas annoncer, et la raison.

    Le nombre de tests change à chaque commit : l'écrire dans un document, c'est
    programmer sa propre péremption. Un document vivant renvoie à la commande ;
    seuls les rapports datés gardent le chiffre du jour où ils ont été écrits.
    """

    motif: str
    raison: str
    gabarit: str


MOTIFS_INTERDITS: tuple[Interdit, ...] = (
    Interdit(r"(\d+) tests\b",
             "un compte de tests se lit à l'exécution de la suite, il ne se recopie pas "
             "dans un document vivant — seul un rapport daté garde le chiffre de son jour",
             "la suite passe {n} tests"),
)


REGLES: tuple[Regle, ...] = (
    # ── Leviers et réglages ────────────────────────────────────────────────
    _r(r"(\d+)\s+leviers croisables", "leviers",
       "pyproject, description GitHub, page des réglages",
       "Le simulateur expose {n} leviers croisables."),
    _r(r"vecteur (?:complet )?de (\d+) leviers", "leviers",
       "docstrings du serveur, du moteur et des tests",
       "# transformation d'un vecteur de {n} leviers"),
    _r(r"table des (\d+) leviers", "leviers", "commentaires des tests du serveur",
       "elles servent la table des {n} leviers"),
    _r(r"catalogue des (\d+) leviers", "leviers", "docstrings de compression et du serveur",
       "le catalogue des {n} leviers tient en mémoire"),
    _r(r"les (\d+) leviers `reglage_", "reglages", "enceinte technique de docs/17",
       "les {n} leviers `reglage_*` sont dans LEVIERS"),
    _r(r"dont (\d+) réglages institutionnels", "reglages", "docstrings du catalogue des réglages",
       "dont {n} réglages institutionnels"),
    _r(r"répartis en (\d+) familles", "familles", "lexique servi à l'interface",
       "répartis en {n} familles"),
    _r(r"leviers, (\d+) familles", "familles", "documents d'état du plan",
       "leviers, {n} familles, préréglages"),
    # ── Préréglages, scénarios, échelons ──────────────────────────────────
    _r(r"(\d+) préréglages\b", "presets", "interface, index.html et documents d'état",
       "Périmètre chiffré : {n} préréglages, scénarios."),
    _r(r"(\d+) presets\b", "presets", "docstring du catalogue",
       "un catalogue de {n} presets"),
    _r(r"(\d+) scénarios types", "scenarios", "page des scénarios",
       "les {n} scénarios types du dépôt"),
    _r(r"catalogue(?: de)? (\d+) scénarios", "scenarios", "docstrings du catalogue",
       "un catalogue de {n} scénarios"),
    _r(r"à (\d+) échelons", "echelons", "README, serveur web, page et description GitHub",
       "Modèle systémique gigogne à {n} échelons"),
    # ── Domaines, indicateurs, garde-fous ─────────────────────────────────
    _r(r"(\d+) domaines d'impact", "domaines", "README, pyproject et description GitHub",
       "{n} domaines d'impact notés de 0 à 100"),
    _r(r"(\d+) domaines d'action publique", "domaines", "README, section du simulateur",
       "**{n} domaines d'action publique**"),
    _r(r"(\d+) domaines, (\d+) indicateurs", "domaines", "NOTE_POUR_CLAUDE, table des briques",
       "{n} domaines, {autre} indicateurs", "indicateurs"),
    _r(r"domaines, (\d+) indicateurs", "indicateurs", "NOTE_POUR_CLAUDE, table des briques",
       "domaines, {n} indicateurs"),
    _r(r"(\d+) indicateurs concrets", "indicateurs", "README, rubrique du simulateur",
       "{n} indicateurs concrets"),
    _r(r"(\d+) indicateurs \(formule", "indicateurs", "page publique des méthodes",
       "{n} indicateurs (formule + source)"),
    _r(r"(\d+) indicateurs publics", "indicateurs_publics", "NOTE_POUR_CLAUDE et docs de présentation",
       "registre de {n} indicateurs publics"),
    _r(r"(\d+) domaines sociétaux", "domaines_societe", "README, CONTRIBUTING et CLI",
       "synthèse des {n} domaines sociétaux"),
    _r(r"(\d+) garde-fous", "garde_fous", "README, docs et page publique des méthodes",
       "les {n} garde-fous du modèle"),
    # ── Routes servies ────────────────────────────────────────────────────
    _r(r"(\d+) routes (?:du moteur|exposées|servies|d'API)", "routes",
       "README, docs et docstring de la fonction Vercel",
       "la fonction unique sert {n} routes du moteur"),
    # ── Taux structurants (P1-3) ────────────────────────────────────────
    _r(r"(\d+) taux structurants", "taux_structurants",
       "README et garde-fou des taux (Maastricht 3 %, PME 30 %, TVA 5,5 %)",
       "les {n} taux structurants (3 % déficit, 30 % PME, 5,5 % TVA)"),
)

#: Fichiers de garde-fou : ils citent des compteurs périmés pour les interdire, ou
#: mesurent le contrôle lui-même. Les vérifier reviendrait à leur interdire leur travail.
FICHIERS_DE_GARDE: dict[str, str] = {
    "verifier-compteurs.py": "garde-fou des compteurs : il nomme les motifs comparés et la "
                             "référence de chaque famille",
    "test_compteurs.py": "contre-épreuve du garde-fou : elle écrit et cite volontairement des "
                         "compteurs faux, dans des dossiers temporaires, pour vérifier la détection",
    "test_plan_global_croisements.py": "garde-fou documentaire : il repose au garde-fou général la "
                                       "question des compteurs, et cite les anciens pour mémoire",
}

#: Constats d'audit : ils citent les compteurs périmés comme pièces à conviction — c'est
#: leur travail, et les vérifier reviendrait à leur interdire de dire ce qu'ils ont trouvé.
CONSTATS_D_AUDIT: dict[str, str] = {
    "19_PLAN_DE_RENFORCEMENT_ET_LACUNES.md": "constat d'audit daté du 12 octobre 2026 : il cite les "
                                             "compteurs périmés pour montrer ce qui a été corrigé, "
                                             "et les chiffres du jour lui servent de colonne « réel »",
}

#: Documents datés : ils gardent les chiffres de leur époque, et la raison est écrite.
#: Le contrôle refuse une exemption sans raison assez longue pour être une raison.
DOCUMENTS_DATES: dict[str, str] = {
    "CHANGELOG.md": "journal des modifications : chaque entrée décrit l'état du jour où elle a été écrite",
    "RD_*": "rapports de R&D datés : le compte de tests y fait partie de la mesure publiée",
    "AUDIT_*": "rapports d'audit datés : le compte de tests y est une pièce du constat",
    "RECHERCHE_DEVELOPPEMENT_SYNERGIES.md": "revue de dépôts tiers, datée : les comptes de tests "
                                            "sont ceux des projets examinés, pas les nôtres",
    "RD_DOUBLE_MANDATURE.md": "R&D datée : le chiffre de l'époque est une pièce du raisonnement",
    "DOSSIER_DE_MANDATURE_GLOBAL.md": "dossier d'origine conservé tel quel, chiffres de sa rédaction",
    "08_STRATE_GEOPOLITIQUE_ET_SCENARIOS_DE_GUERRE.md": "audit daté du 3 octobre 2026 : il compte les "
                                                          "tests de sa livraison, pas ceux d'aujourd'hui",
    "14_SYNTHESE_MONDIALE_DES_THINK_TANKS_ET_CONTRADICTIONS_SYSTEMIQUES.md": "synthèse datée de revue de "
                                                                            "littérature : ses mesures sont "
                                                                            "celles de sa rédaction",
    "AUDIT_LACUNES_GEOPOLITIQUES.md": "rapport d'audit daté : le compte de tests y est une pièce du constat",
    "AUDIT_PR_CORRECTIONS.md": "rapport de revue daté : le compte de tests y est une pièce du constat",
    "INTEGRATION_COMMITS_EN_ATTENTE.md": "note d'intégration datée : elle décrit l'état d'un lot précis",
    "LABORATOIRE_RD.md": "rapport d'expérience daté : le compte de tests fait partie de la mesure",
    "PLAN_DU_SIMULATEUR_ET_AUDIT_INSTANT_T.md": "architecture d'origine du modèle, écrite avant la "
                                                "strate géopolitique : elle décrit quatre échelons "
                                                "par construction et garde ce chiffre",
}

#: Suffixes lus : le dépôt est un mélange de Python, de Markdown, de TOML et de HTML généré.
SUFFIXES = {".py", ".md", ".toml", ".html", ".json", ".yml", ".yaml"}

#: Répertoires ignorés (dépendances, caches, historique Git).
IGNORES = {".git", "__pycache__", "node_modules", ".venv", "dist", "build", "outils"}


def reference() -> dict[str, int]:
    """Les compteurs du jour, pour l'affichage et pour les contre-épreuves."""
    return _reference()


def _exempte(nom: str) -> bool:
    """Le fichier est-il un document daté, ou un garde-fou, de la liste d'exemptions ?"""
    for motif in (*DOCUMENTS_DATES, *FICHIERS_DE_GARDE, *CONSTATS_D_AUDIT):
        if motif.endswith("*"):
            if nom.startswith(motif[:-1]):
                return True
        elif nom == motif:
            return True
    return False


def verifier(racine: Path | str = RACINE) -> list[str]:
    """Retourne les anomalies trouvées : liste vide = tous les compteurs sont à jour."""
    racine = Path(racine)
    attendu = _reference()
    anomalies: list[str] = []
    for chemin in sorted(racine.rglob("*")):
        if not chemin.is_file() or chemin.suffix not in SUFFIXES:
            continue
        if any(partie in IGNORES for partie in chemin.parts):
            continue
        if _exempte(chemin.name):
            continue
        try:
            texte = chemin.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if chemin.suffix == ".md":
            for interdit in MOTIFS_INTERDITS:
                for correspondance in re.finditer(interdit.motif, texte):
                    ligne = texte[:correspondance.start()].count("\n") + 1
                    try:
                        relatif = chemin.relative_to(racine)
                    except ValueError:
                        relatif = chemin.name
                    anomalies.append(
                        f"{relatif}:{ligne} — « {correspondance.group(0)} » : {interdit.raison}")
        for regle in REGLES:
            for correspondance in re.finditer(regle.motif, texte):
                annonce = int(correspondance.group(1))
                if annonce == attendu[regle.quoi]:
                    continue
                ligne = texte[:correspondance.start()].count("\n") + 1
                try:
                    relatif = chemin.relative_to(racine)
                except ValueError:              # racine passée à la main (tests)
                    relatif = chemin.name
                anomalies.append(
                    f"{relatif}:{ligne} — « {correspondance.group(0)} » alors que le "
                    f"compteur réel de {regle.quoi} est {attendu[regle.quoi]} ({regle.ou})")
    uniques: list[str] = []
    for ligne in anomalies:
        if ligne not in uniques:
            uniques.append(ligne)
    return uniques


def _raisons_des_exemptions() -> list[str]:
    """Un garde-fou sur les exemptions : pas de raison courte, pas d'exemption creuse."""
    exemptions = {**DOCUMENTS_DATES, **FICHIERS_DE_GARDE, **CONSTATS_D_AUDIT}
    noms_presents = {chemin.name for chemin in RACINE.rglob("*") if chemin.is_file()}
    soucis = [f"{nom} : exemption sans raison écrite" for nom, raison in exemptions.items()
              if len(raison) < 40]
    for nom, raison in exemptions.items():
        if nom in noms_presents:
            continue
        if nom.endswith("*") and any(fichier.startswith(nom[:-1]) for fichier in noms_presents):
            continue
        soucis.append(f"{nom} : exemption « {raison[:30]}… » sans fichier")
    return soucis


def main() -> int:
    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("--liste", action="store_true",
                           help="affiche les compteurs de référence et les règles, sans vérifier")
    options = analyseur.parse_args()

    if options.liste:
        print("Compteurs de référence, lus dans le code :")
        for cle, valeur in sorted(_reference().items()):
            print(f"  {cle:20s} {valeur}")
        print("\nRègles vérifiées :")
        for regle in REGLES:
            print(f"  [{regle.quoi:19s}] {regle.ou}")
        print("\nComptes qu'un document vivant ne doit pas annoncer :")
        for interdit in MOTIFS_INTERDITS:
            print(f"  {interdit.gabarit:34s} {interdit.raison}")
        print("\nFichiers de garde-fou, exemptés avec leur raison :")
        for nom, raison in FICHIERS_DE_GARDE.items():
            print(f"  {nom} — {raison}")
        print("\nConstats d'audit, exemptés avec leur raison :")
        for nom, raison in CONSTATS_D_AUDIT.items():
            print(f"  {nom} — {raison}")
        print("\nDocuments datés, exemptés avec leur raison :")
        for nom, raison in DOCUMENTS_DATES.items():
            print(f"  {nom} — {raison}")
        return 0

    soucis = _raisons_des_exemptions()
    anomalies = verifier(RACINE)
    if anomalies or soucis:
        for ligne in anomalies + soucis:
            print("compteur périmé : " + ligne, file=sys.stderr)
        print(f"\n{len(anomalies) + len(soucis)} écart(s) : un compteur se déduit du code, "
              "il ne se relit pas.", file=sys.stderr)
        return 1
    attendu = _reference()
    print("compteurs à jour : " + ", ".join(f"{valeur} {cle}" for cle, valeur in attendu.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
