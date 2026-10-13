#!/usr/bin/env python3
"""
outils/details_depot.py — prépare et applique les « Edit repository details ».

Le bloc *About* du dépôt (description, site web, sujets) et l'aperçu social ne
sont pas versionnés : ce script les tient à jour à partir du contenu réel du
projet, et tente de les appliquer via l'API GitHub. Si le jeton disponible n'a
pas les droits d'administration du dépôt (l'API répond alors 403), il affiche
le bloc exact à copier dans *Edit repository details*.

    python3 outils/details_depot.py              # état actuel + bloc à copier
    python3 outils/details_depot.py --appliquer  # tente la mise à jour GitHub
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:      # le script se lance depuis n'importe où
    sys.path.insert(0, str(RACINE))

from simulateur import surface_publique as surface  # noqa: E402

DEPOT = "thejmimiia-code/D-mocratie-et-politique-du-peuple-pour-le-peuple-par-le-peuple"

#: Description du dépôt (limite GitHub : 350 caractères).
DESCRIPTION = (
    "Simulateur macro-politique systémique à 5 échelons (local → européen → mondial → "
    "géopolitique) : 156 leviers croisables, 20 domaines d'impact notés 0-100, données "
    "publiques en direct (Eurostat, BCE, Banque mondiale) et console de veille des seuils "
    "tolérables et hors-sol."
)

#: Sujets GitHub (limite : 20). Ils décrivent ce que fait le dépôt aujourd'hui.
SUJETS = [
    "france",
    "simulation",
    "politiques-publiques",
    "finances-publiques",
    "budget",
    "dette-publique",
    "democratie",
    "geopolitique",
    "open-data",
    "api-publiques",
    "eurostat",
    "banque-mondiale",
    "dashboard",
    "python",
    "modele-systemique",
    "souverainete",
    "politiques-budgetaires",
    "transparence",
    "constitution",
    "economie",
]

#: Le site web **est** l'application, à l'adresse canonique : la même que celle
#: que la page déclare aux moteurs (`surface_publique.URL_CANONIQUE_PAR_DEFAUT`).
#: Une seule source, pour que l'adresse affichée dans le dépôt ne puisse pas
#: vieillir à part de celle que servent les hébergeurs.
SITE_WEB = surface.URL_CANONIQUE_PAR_DEFAUT.rstrip("/")

#: Ce qu'on conseille si — et seulement si — l'adresse ne répond pas. Bâti sur
#: `DEPOT` : ce lien a été écrit à la main avec un nom de dépôt tronqué, et
#: renvoyait donc 404 — un repli mort dans le seul document qui sert de repli.
SITE_WEB_CONSEIL = (f"https://github.com/{DEPOT}/blob/main/"
                    "docs/SIMULATEUR_PARAMETRABLE.md")

APERCU_SOCIAL = RACINE / "docs" / "apercu_social.png"

#: Le document de référence des champs non versionnés. Ses valeurs sont
#: **engendrées** entre marques : recopiées à la main, elles ont dérivé trois
#: fois (compte de caractères, empreinte de l'image, taille), et un document qui
#: annonce une empreinte fausse fait téléverser autre chose que ce qu'il décrit.
DOCUMENT = RACINE / "docs" / "REPOSITORY_DETAILS.md"

#: `<!-- engendre:nom -->` … `<!-- /engendre:nom -->` : les quatre régions tenues
#: par ce script. Le texte hors marques est de la prose, et reste éditable.
REGIONS = ("description", "sujets", "site-web", "apercu")


def adresse_repond(adresse: str, ouvrir=None, delai: float = 5.0) -> bool | None:
    """L'adresse répond-elle ? ``None`` : on n'a pas pu savoir (réseau absent).

    Ce contrôle remplace une **affirmation figée** qui avait tort : le champ
    « Website » devait être vidé au motif que l'adresse renverrait 404. C'était
    vrai un jour, et une phrase figée ne redevient jamais vraie toute seule. Ici,
    la question est posée à chaque exécution — et quand le réseau manque, on le
    dit au lieu de conclure.
    """
    import urllib.error
    import urllib.request

    if not adresse:
        return None
    ouvrir = ouvrir or urllib.request.urlopen
    try:
        with ouvrir(adresse, timeout=delai) as reponse:
            return getattr(reponse, "status", 200) == 200
    except urllib.error.HTTPError:
        return False
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None


def _ligne_site_web(adresse_vivante: bool | None) -> str:
    """Le conseil du champ « Website », dit selon ce qui a été constaté."""
    if adresse_vivante is True:
        return (f"Website\n{SITE_WEB}\n"
                "  → l'application répond (vérifié à l'instant) : c'est elle, le site du dépôt.")
    if adresse_vivante is False:
        return (f"Website\n(vide — {SITE_WEB} ne répond pas actuellement)\n"
                f"À défaut d'application joignable, renvoyer vers la documentation :\n"
                f"{SITE_WEB_CONSEIL}")
    return (f"Website\n{SITE_WEB}\n"
            "  → publiée là ; l'adresse n'a pas pu être vérifiée depuis cette machine "
            "(réseau\n    injoignable). Gardez-la : c'est celle que la page déclare aux moteurs.")


def bloc_a_copier(adresse_vivante: bool | None = None) -> str:
    """Le bloc exact à coller dans *Edit repository details*."""
    sujets = ", ".join(SUJETS)
    return f"""\
────────────────────────────────────────────────────────────────────────────
EDIT REPOSITORY DETAILS — à coller tel quel
────────────────────────────────────────────────────────────────────────────

Description ({len(DESCRIPTION)} / 350 caractères)
{DESCRIPTION}

{_ligne_site_web(adresse_vivante)}

Topics ({len(SUJETS)} / 20)
{sujets}

Social preview
Téléverser l'image : {APERCU_SOCIAL.relative_to(RACINE)}
(1280 × 640, régénérée par `python3 outils/apercu_social.py`)

Mise en ligne (déjà faite, pour mémoire)
  Application  : {SITE_WEB} — Vercel
  Copie de secours : {surface.HOTE_SECOURS.rstrip('/')} — Render, même page, même moteur
  Ce que les robots lisent : {SITE_WEB}/robots.txt, /sitemap.xml, /llms.txt, /llms-full.txt
  Vérification : `python3 outils/verifier-surface-en-ligne.py`

Réglages recommandés dans la même page
  ☑ Include in the home page … non (projet de recherche, pas de vitrine)
  ☑ Releases : activées (l'application se lance par `python -m simulateur.dashboard`)
  ☑ Packages : inutile pour ce dépôt
────────────────────────────────────────────────────────────────────────────
"""


def _nom_lisible(chemin: Path) -> str:
    """Le chemin tel qu'on l'affiche : relatif au dépôt quand il y est."""
    try:
        return str(chemin.relative_to(RACINE))
    except ValueError:                      # hors du dépôt : un test, par exemple
        return str(chemin)


def _chiffres_du_catalogue() -> list[str]:
    """Les comptes vivants du catalogue, lus ici et non recopiés.

    L'aperçu social et ce document annoncent les mêmes nombres : les lire tous
    les deux au même endroit est la seule façon qu'ils ne se contredisent pas.
    """
    from simulateur.domaines import DOMAINES
    from simulateur.donnees_live import INDICATEURS
    from simulateur.parametres import LEVIERS

    return [f"{len(LEVIERS)} leviers", f"{len(DOMAINES)} domaines",
            f"{len(INDICATEURS)} indicateurs publics", "5 échelons"]


def _empreinte_image() -> tuple[int, str, str] | None:
    """(octets, SHA-256 hexadécimal, SHA-256 base64) du fichier versionné."""
    import base64
    import hashlib

    if not APERCU_SOCIAL.is_file():
        return None
    octets = APERCU_SOCIAL.read_bytes()
    empreinte = hashlib.sha256(octets).digest()
    return len(octets), empreinte.hex(), "SHA256:" + base64.b64encode(empreinte).decode()


def _bloc_description() -> str:
    return (f"## 1. Description ({len(DESCRIPTION)} / 350 caractères)\n\n"
            f"```\n{DESCRIPTION}\n```")


def _bloc_sujets() -> str:
    return (f"## 3. Sujets ({len(SUJETS)} / 20)\n\n"
            f"```\n{', '.join(SUJETS)}\n```")


def _bloc_site_web() -> str:
    secours = surface.HOTE_SECOURS.rstrip("/")
    return "\n".join([
        f"L'application est publiée à **{SITE_WEB}** — c'est elle, le site du dépôt.",
        "La même page, servie par le même moteur, répond aussi sur la **copie de secours**",
        f"{secours} (Render, qui s'endort puis se réveille).",
        "",
        f"Ce que les robots lisent : `{SITE_WEB}/robots.txt`, `/sitemap.xml`, `/llms.txt`,",
        "`/llms-full.txt` — tous engendrés par `simulateur/surface_publique.py`.",
        "Vérification depuis n'importe quelle machine connectée :",
        "`python3 outils/verifier-surface-en-ligne.py`.",
    ])


def _bloc_apercu() -> str:
    empreinte = _empreinte_image()
    if empreinte is None:
        return (f"⚠️ `{APERCU_SOCIAL.relative_to(RACINE)}` est absent : le régénérer par "
                "`python3 outils/apercu_social.py`.")
    octets, hexadecimal, base64_ = empreinte
    kio = round(octets / 1024)
    chiffres = " · ".join(_chiffres_du_catalogue())
    return "\n".join([
        f"Téléverser **`{APERCU_SOCIAL.relative_to(RACINE)}`** (1280 × 640, {kio} Kio — "
        f"{octets} octets),",
        "régénérable par `python3 outils/apercu_social.py`. L'image reprend la palette du",
        f"simulateur, ses chiffres clés — {chiffres} —",
        "et le ruban de veille avec ses pastilles de strate.",
        "",
        "Empreintes du fichier versionné, pour vérifier que c'est bien celui-ci qui a été",
        "téléversé dans *Social preview* :",
        "",
        "| Format | Valeur |",
        "|---|---|",
        f"| Octets | `{octets}` |",
        f"| SHA-256 (hexadécimal) | `{hexadecimal}` |",
        f"| SHA-256 (base64) | `{base64_}` |",
    ])


def _regions_engendrees() -> dict[str, str]:
    return {"description": _bloc_description(), "sujets": _bloc_sujets(),
            "site-web": _bloc_site_web(), "apercu": _bloc_apercu()}


def _decouper(texte: str, nom: str) -> tuple[str, str, str] | None:
    """(avant, contenu, après) entre les marques, ou None si elles manquent."""
    debut, fin = f"<!-- engendre:{nom} -->", f"<!-- /engendre:{nom} -->"
    if texte.count(debut) != 1 or texte.count(fin) != 1:
        return None
    i = texte.index(debut) + len(debut)
    j = texte.index(fin)
    if j < i:
        return None
    return texte[:i], texte[i:j], texte[j:]


def verifier_document(chemin: Path = DOCUMENT) -> list[str]:
    """Les régions du document sont-elles à jour ? Vide : oui."""
    if not chemin.is_file():
        return [f"{chemin} est absent"]
    texte = chemin.read_text(encoding="utf-8")
    anomalies: list[str] = []
    for nom, contenu in _regions_engendrees().items():
        parties = _decouper(texte, nom)
        if parties is None:
            anomalies.append(f"région « {nom} » : marques absentes ou en double")
            continue
        actuel = parties[1].strip("\n")
        if actuel != contenu.strip("\n"):
            anomalies.append(f"région « {nom} » : valeur périmée "
                             f"(`python3 outils/details_depot.py --doc` la réécrit)")
    return anomalies


def reecrire_document(chemin: Path = DOCUMENT) -> int:
    """Réécrit les seules régions engendrées ; la prose est laissée intacte."""
    if not chemin.is_file():
        print(f"{chemin} est absent", file=sys.stderr)
        return 1
    texte = chemin.read_text(encoding="utf-8")
    for nom, contenu in _regions_engendrees().items():
        parties = _decouper(texte, nom)
        if parties is None:
            print(f"région « {nom} » introuvable : marques absentes ou en double", file=sys.stderr)
            return 1
        texte = f"{parties[0]}\n{contenu}\n{parties[2]}"
    chemin.write_text(texte, encoding="utf-8")
    print(f"{_nom_lisible(chemin)} : régions engendrées réécrites "
          f"({', '.join(_regions_engendrees())}).")
    return 0


def _gh(*arguments: str) -> tuple[int, str]:
    gh = shutil.which("gh")
    if gh is None:
        return 127, "gh CLI absent"
    proc = subprocess.run([gh, *arguments], capture_output=True, text=True, cwd=str(RACINE))
    return proc.returncode, (proc.stdout or proc.stderr).strip()


def etat_actuel() -> dict | None:
    """Lit les réglages actuels du dépôt (None si l'API est indisponible)."""
    code, sortie = _gh("api", f"repos/{DEPOT}",
                       "--jq", "{description,homepage,topics,visibility,license:.license.spdx_id}")
    if code != 0:
        print(f"Lecture impossible ({code}) : {sortie[:200]}", file=sys.stderr)
        return None
    try:
        return json.loads(sortie)
    except json.JSONDecodeError:
        print(f"Réponse inattendue : {sortie[:200]}", file=sys.stderr)
        return None


def appliquer(adresse_vivante: bool | None = None) -> int:
    """Tente la mise à jour ; retourne 0 si elle a abouti."""
    # PATCH /repos : description, site web, puis un champ `topics[]` répété par sujet.
    arguments = ["api", "-X", "PATCH", f"repos/{DEPOT}",
                 "-f", f"description={DESCRIPTION}",
                 "-f", f"homepage={SITE_WEB}"]
    for sujet in SUJETS:
        arguments += ["-f", f"topics[]={sujet}"]
    code, sortie = _gh(*arguments)
    if code == 0:
        print("Réglages appliqués par l'API.")
        return 0
    print(f"L'API a refusé la mise à jour ({code}) : {sortie[:200]}")
    print("Le jeton disponible est un jeton d'intégration sans droit d'administration.\n")
    print(bloc_a_copier(adresse_vivante))
    return 1


def main() -> int:
    analyseur = argparse.ArgumentParser(description="Réglages du dépôt (About, sujets, aperçu)")
    analyseur.add_argument("--appliquer", action="store_true",
                           help="tente la mise à jour via l'API GitHub")
    analyseur.add_argument("--sans-reseau", action="store_true",
                           help="ne pas sonder l'adresse publiée (exécution hors ligne)")
    analyseur.add_argument("--doc", action="store_true",
                           help="réécrit les régions engendrées de docs/REPOSITORY_DETAILS.md")
    analyseur.add_argument("--verifier-doc", action="store_true",
                           help="contrôle ces régions (code de sortie 1 si périmées)")
    arguments = analyseur.parse_args()

    if arguments.verifier_doc:
        anomalies = verifier_document()
        if anomalies:
            for anomalie in anomalies:
                print(f"  ✗ {anomalie}")
            return 1
        print(f"{_nom_lisible(DOCUMENT)} : régions engendrées à jour.")
        return 0
    if arguments.doc:
        return reecrire_document()

    adresse_vivante = None if arguments.sans_reseau else adresse_repond(SITE_WEB)

    etat = etat_actuel()
    if etat:
        print("État actuel :")
        print(f"  description : {etat.get('description')}")
        print(f"  website     : {etat.get('homepage') or '(vide)'}")
        print(f"  topics      : {etat.get('topics') or '(aucun)'}")
        print()
        if (etat.get("description") == DESCRIPTION
                and (etat.get("homepage") or "") .rstrip("/") == SITE_WEB
                and set(etat.get("topics") or []) == set(SUJETS)):
            print("Déjà à jour, rien à faire.")
            return 0
    if arguments.appliquer:
        return appliquer(adresse_vivante)
    print(bloc_a_copier(adresse_vivante))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
