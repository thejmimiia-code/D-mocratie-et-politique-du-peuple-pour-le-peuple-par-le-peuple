"""outils/poids_de_la_page.py — où passe le poids d'une page, et qui elle appelle.

**Le fait, mesuré le 15 octobre 2026 sur la page publiée** (`index.html`, gzip -6) :
**478 837 octets bruts**, **129 569 compressés**, dont **109 102 o** de feuille de
style et **317 991 o** de script — tous deux **en ligne** — pour **51 744 o** de
balisage. Le script en ligne porte donc **66,4 %** du document. Et la page est
autonome : aucune police distante, aucune image, aucune feuille externe ; son
seul appel est un script **en même origine** (`/_vercel/insights/script.js`,
`defer`, l'analytics de la plateforme d'hébergement).

Ce que ce fichier ajoute — et ce qu'il n'ajoute pas
---------------------------------------------------

Le dépôt sait déjà plafonner ce que le réseau transporte : `outils/
budgets_fluidite.py` tient l'ancre datée, la marge de 10 %, les plafonds par
route et le budget dérivé du premier écran, et la CI refuse un dépassement. Ce
fichier **ne remet pas un second avis** sur ces nombres : il **lit** le plafond
réseau de la page dans cette table (`plafond_reseau()`) et publie la réserve.
Deux plafonds concurrents sur la même grandeur, ce serait deux juges et aucune
vérité.

Ce qui manquait, et que ce fichier tient, est ailleurs — dans deux dimensions que
les octets compressés ne voient pas :

1. **ce que l'appareil décompresse et analyse.** Un plafond de poids transféré ne
   dit rien du coût de parse : la compression fait gagner le réseau, jamais la
   mémoire du téléphone. D'où un plafond sur le **document brut**.
2. **la part du plus gros bloc.** Un document qui devient un programme — deux
   tiers de script en ligne, non cacheable et non différable séparément — coûte
   à chaque visite, même pour lire trois lignes. D'où un plafond sur la **part du
   script**, qui oblige à se poser la question du découpage *avant* que la page
   ne soit devenue un programme, pas après.
3. **et la question qu'aucun plafond ne pose : qui la page appelle-t-elle ?**
   Un `@import`, une police distante, un CDN : une requête, un délai, une
   dépendance de disponibilité — et, pour un outil citoyen, une information
   donnée à un tiers. Un `<a href>` vers une source officielle n'est pas un
   appel : c'est un lien que le visiteur décide de suivre. La distinction est le
   cœur de la mesure, et elle a une liste blanche explicite : une sous-ressource
   qui n'y est pas déclarée fait rougir.

Trois règles, comme celles du premier écran
-------------------------------------------

1. **un plafond porte sa mesure datée** (`mesure`, `quand`, `quoi`) — et quand il
   n'y a pas d'état ancien à battre, il le **dit** (`jour_zero`) au lieu
   d'inventer un « avant » ;
2. **il tient l'état mesuré** (`plafond >= mesure`), avec une marge **déclarée et
   petite** : une marge qui autorise un doublement n'est pas un plafond ;
3. **il dit où la place se perd et quoi faire** : le rapport publie chaque bloc,
   sa part, la réserve du plafond réseau et la sortie de chaque règle franchie.

Usage :

    python3 -m outils.poids_de_la_page            # le rapport lisible
    python3 -m outils.poids_de_la_page --json     # la mesure complète
    python3 -m outils.poids_de_la_page --verifier # sort en 1 si une règle casse
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

PAGE = RACINE / "index.html"

#: Le niveau de compression des mesures. Les hébergeurs servent du gzip ou du
#: brotli ; gzip niveau 6 est la convention du dépôt — reproductible partout, et
#: plutôt pessimiste (brotli ferait mieux), donc jamais complaisante.
NIVEAU_GZIP = 6

#: Le jour zéro : `index.html` est un artefact généré, réimporté avec
#: l'historique de la session, et aucun état ancien du fichier n'est mesurable
#: dans ce dépôt. Le dire est ce qui empêche un plafond de se faire passer pour
#: un cliquet.
JOUR_ZERO = "15 octobre 2026"

PLAFONDS: dict[str, dict] = {
    "brut": {
        "plafond": 505_000,
        "mesure": 479190,
        "marge": 0.0539,
        "quand": JOUR_ZERO,
        "jour_zero": True,
        "quoi": "le document brut : ce que l'appareil décompresse, analyse et "
                "garde en mémoire, 479 190 o dont 318 344 de script en ligne",
        "sortie": "Retirer du document ce qui ne sert pas la visite, ou relever "
                  "l'ancre en revue : la compression ne paie pas le parse.",
    },
    "part_js": {
        "plafond": 0.72,
        "mesure": 0.6643,
        "marge": 0.0838,
        "quand": JOUR_ZERO,
        "jour_zero": True,
        "quoi": "la part du document portée par le script en ligne : 66,4 % — un "
                "document qui devient un programme ne se cache ni ne se diffère",
        "sortie": "Découper le script en un fichier à part (cacheable, différable) "
                  "plutôt que de laisser le document devenir un programme ; le "
                  "plancher écrit est le quart laissé au contenu.",
    },
}

#: Le plafond du **réseau** n'est pas ici : il vit dans `outils/budgets_fluidite.py`,
#: avec son ancre datée, sa marge et ses plafonds par route. On le lit au lieu de
#: le recopier — deux plafonds concurrents sur la même grandeur, ce serait deux
#: juges et aucune vérité.
PLAFOND_RESEAU = ("budgets_fluidite", "page")

#: Les sous-ressources qui sont **déjà** là et qu'on assume, écrites en clair.
#: Toute autre entrée fait rougir : c'est la liste blanche de l'autonomie, et
#: elle doit être touchée à la main, jamais grossir toute seule.
SOUS_RESSOURCES_ASSUMEES = (
    #: L'analytics de la plateforme d'hébergement, en même origine, en `defer`.
    "/_vercel/insights/script.js",
)

#: Ce qu'on refuse de compter comme un appel : un lien, un `data:`, une ancre.
TYPES_QUI_NE_SONT_PAS_DES_APPELS = ("lien", "ancre", "data")


def _n(valeur) -> str:
    """Un nombre lisible, séparateurs d'espace — sans abîmer le texte autour."""
    if isinstance(valeur, float) and not float(valeur).is_integer():
        return f"{valeur:.1f}".replace(".", ",")
    return f"{int(valeur):,}".replace(",", " ")


def _pct(fraction: float, precision: int = 1) -> str:
    """Une proportion en pour cent, à la française : virgule décimale, espace avant."""
    return f"{100 * fraction:.{precision}f}".replace(".", ",") + " %"


def _fractions(texte: str) -> dict[str, str]:
    """Les blocs en ligne de la page : feuille de style, scripts, balisage.

    Le balisage se mesure **par positions**, pas par soustraction de chaînes :
    remplacer la première occurrence d'un bloc retiré un jour la mauvaise, et le
    compte devient faux sans que rien ne le dise. Une mesure fausse est pire
    qu'une mesure absente.
    """
    blocs: list[tuple[int, int, str]] = []
    for m in re.finditer(r"<style[^>]*>(.*?)</style>", texte, re.S):
        blocs.append((m.start(1), m.end(1), "css"))
    for m in re.finditer(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", texte, re.S):
        blocs.append((m.start(1), m.end(1), "js"))
    blocs.sort()
    sortie = {"css": "", "js": "", "html": ""}
    curseur = 0
    for debut, fin, genre in blocs:
        sortie["html"] += texte[curseur:debut]
        sortie[genre] += texte[debut:fin]
        curseur = fin
    sortie["html"] += texte[curseur:]
    return sortie


def sous_ressources(texte: str) -> list[dict[str, str]]:
    """Ce que la page **appelle** : scripts, feuilles, images, `url()` distants.

    Un `<a href>` n'est pas un appel : c'est un lien que le visiteur décide de
    suivre. La distinction est le cœur de la mesure.
    """
    trouvees: list[dict[str, str]] = []

    def noter(kind: str, url: str) -> None:
        if url.startswith(("data:", "#", "mailto:")):
            return
        hote = urlparse(url).netloc
        trouvees.append({"type": kind, "url": url, "hote": hote or "(même origine)",
                         "meme_origine": not hote})

    for m in re.finditer(r"<script[^>]*\bsrc=[\"']([^\"']+)[\"']", texte):
        noter("script", m.group(1))
    for m in re.finditer(r"<link[^>]*\bhref=[\"']([^\"']+)[\"'][^>]*>", texte):
        balise = m.group(0)
        rel = re.search(r"rel=[\"']([^\"']+)[\"']", balise)
        if rel and any(mot in rel.group(1) for mot in ("stylesheet", "preload", "icon")):
            noter("feuille" if "stylesheet" in rel.group(1) else "ressource", m.group(1))
    for m in re.finditer(r"<img[^>]*\bsrc=[\"']([^\"']+)[\"']", texte):
        noter("image", m.group(1))
    for m in re.finditer(r"url\([\"']?(https?://[^)\"']+)", texte):
        noter("css-url", m.group(1))
    return trouvees


def plafond_reseau() -> dict:
    """Le plafond du poids transféré, **lu** dans la table du dépôt.

    Le lire plutôt que le recopier : deux plafonds concurrents sur la même
    grandeur finiraient par diverger, et c'est la mesure qui lirait le mauvais.
    """
    from outils import budgets_fluidite as budgets

    module, cle = PLAFOND_RESEAU
    budget = next(b for b in budgets.BUDGETS if b.cle == cle)
    return {"source": f"{module}.{cle}", "ancre": budget.ancre,
            "plafond": budget.plafond, "marge_pct": budget.marge_pct}


def mesurer(chemin: Path = PAGE, avec_reseau: bool = True) -> dict:
    """La mesure du jour, complète et reproductible."""
    octets = chemin.read_bytes()
    texte = octets.decode("utf-8")
    blocs = _fractions(texte)
    tailles = {
        "brut": len(octets),
        "gzip": len(gzip.compress(octets, NIVEAU_GZIP)),
        "css": len(blocs["css"].encode("utf-8")),
        "js": len(blocs["js"].encode("utf-8")),
        "html": len(blocs["html"].encode("utf-8")),
    }
    appels = sous_ressources(texte)
    tiers = [appel for appel in appels if not appel["meme_origine"]]
    mesure = {
        "fichier": chemin.name,
        "octets": tailles,
        "part": {nom: tailles[nom] / tailles["brut"] for nom in ("css", "js", "html")},
        "structure": {
            "lignes": texte.count("\n") + 1,
            "balises": len(re.findall(r"<[a-zA-Z]", texte)),
            "identifiants": len(re.findall(r' id="', texte)),
        },
        "appels": {
            "nombre": len(appels),
            "meme_origine": [appel["url"] for appel in appels if appel["meme_origine"]],
            "domaines_tiers": sorted({appel["hote"] for appel in tiers}),
            "non_declarees": sorted({appel["url"] for appel in appels
                                     if appel["meme_origine"]
                                     and appel["url"] not in SOUS_RESSOURCES_ASSUMEES}),
            "detail": appels,
        },
    }
    mesure["reseau"] = plafond_reseau() if avec_reseau else None
    return mesure


def _valeur(mesure: dict, nom: str):
    """La grandeur visée : un bloc d'octets (`brut`) ou une part (`part_js`)."""
    if nom.startswith("part_"):
        return mesure["part"].get(nom[5:])
    return mesure["octets"].get(nom)


def depassements(mesure: dict, plafonds: dict[str, dict] | None = None,
                 reseau: dict | None = None) -> list[dict]:
    """Les règles franchies, avec de quoi corriger sans chercher."""
    plafonds = PLAFONDS if plafonds is None else plafonds
    reseau = (mesure.get("reseau") if reseau is None else reseau)
    sortie: list[dict] = []

    for nom, limite in plafonds.items():
        valeur = _valeur(mesure, nom)
        if valeur is None:
            sortie.append({"nom": nom, "mesure": None, "plafond": limite["plafond"],
                           "exces": None,
                           "phrase": f"la mesure ne porte pas « {nom} »"})
            continue
        if valeur > limite["plafond"]:
            unite = "%" if nom.startswith("part_") else " o"
            facteur = 100 if nom.startswith("part_") else 1
            sortie.append({
                "nom": nom, "mesure": valeur, "plafond": limite["plafond"],
                "exces": valeur - limite["plafond"],
                "phrase": f"{nom} : {_n(valeur * facteur)}{unite} pour un plafond de "
                          f"{_n(limite['plafond'] * facteur)}{unite} — {limite['quoi']}. "
                          f"{limite['sortie']}",
            })

    if mesure["appels"]["domaines_tiers"]:
        sortie.append({
            "nom": "appels", "mesure": len(mesure["appels"]["domaines_tiers"]),
            "plafond": 0, "exces": len(mesure["appels"]["domaines_tiers"]),
            "phrase": "la page appelle un domaine tiers : "
                      + ", ".join(mesure["appels"]["domaines_tiers"])
                      + ". Un outil citoyen ne dépend pas d'un tiers — le retirer, "
                        "ou l'assumer dans la liste blanche en le justifiant.",
        })
    for url in mesure["appels"]["non_declarees"]:
        sortie.append({
            "nom": "sous-ressource", "mesure": url, "plafond": 0, "exces": None,
            "phrase": "une sous-ressource en même origine n'est pas déclarée : "
                      f"« {url} ». Elle doit entrer dans SOUS_RESSOURCES_ASSUMEES "
                      "avec sa raison — jamais survivre par accident.",
        })

    if reseau is not None and mesure["octets"]["gzip"] > reseau["plafond"]:
        sortie.append({
            "nom": "gzip", "mesure": mesure["octets"]["gzip"],
            "plafond": reseau["plafond"],
            "exces": mesure["octets"]["gzip"] - reseau["plafond"],
            "phrase": f"le poids transféré dépasse le plafond réseau de la page "
                      f"({reseau['source']}) : {_n(mesure['octets']['gzip'])} o pour "
                      f"{_n(reseau['plafond'])} o. Ce plafond n'est pas ici : c'est "
                      "l'ancre de `outils/budgets_fluidite.py` qu'il faut relever en "
                      "revue, ou la page qu'il faut réduire.",
        })
    return sortie


def lignes(mesure: dict, plafonds: dict[str, dict] | None = None) -> list[str]:
    """Ce qu'on écrit : où passe le poids, ce que la page appelle, ce qui casse."""
    plafonds = PLAFONDS if plafonds is None else plafonds
    detail = mesure["octets"]
    part = mesure["part"]
    sortie = [f"**Poids de la page** : {_n(detail['brut'])} o bruts, "
              f"{_n(detail['gzip'])} o transférés (gzip {NIVEAU_GZIP}) — "
              f"feuille de style {_n(detail['css'])} ({_pct(part['css'])}), "
              f"script en ligne {_n(detail['js'])} ({_pct(part['js'])}), "
              f"balisage {_n(detail['html'])} ({_pct(part['html'])})."]

    for nom, limite in plafonds.items():
        valeur = _valeur(mesure, nom)
        if valeur is None:
            continue
        facteur = 100 if nom.startswith("part_") else 1
        unite = "%" if nom.startswith("part_") else " o"
        marque = "**DÉPASSÉ**" if valeur > limite["plafond"] else "tenu"
        ancrage = ("jour zéro, aucun état ancien à battre" if limite.get("jour_zero")
                   else f"ancré sur {limite.get('avant', '?')} le {limite['quand']}")
        sortie.append(f"- {nom} : {_n(valeur * facteur)}{unite} pour un plafond de "
                      f"{_n(limite['plafond'] * facteur)}{unite} — {marque} "
                      f"(marge {_pct(limite['marge'])}, {ancrage}) ; {limite['quoi']}.")

    reseau = mesure.get("reseau")
    if reseau is not None:
        reserve = reseau["plafond"] - detail["gzip"]
        part_reserve = reserve / reseau["plafond"]
        sortie.append(f"- réseau : {_n(detail['gzip'])} o transférés pour le plafond "
                      f"de {_n(reseau['plafond'])} o tenu par `{reseau['source']}` "
                      f"(ancre {_n(reseau['ancre'])} o, marge {reseau['marge_pct']} %) "
                      f"— réserve {_n(reserve)} o ({_pct(part_reserve)} du plafond).")

    appels = mesure["appels"]
    if appels["domaines_tiers"]:
        sortie.append("- ⛔ La page appelle " + ", ".join(appels["domaines_tiers"])
                      + " : un outil citoyen ne dépend pas d'un tiers.")
    else:
        sortie.append(f"- **La page n'appelle personne d'autre qu'elle-même** : "
                      f"{appels['nombre']} sous-ressource(s), toutes en même origine"
                      + (f", déclarée(s) (`{appels['meme_origine'][0]}`)."
                         if appels["meme_origine"] else "."))

    for depassement in depassements(mesure, plafonds, reseau):
        sortie.append(f"- ⛔ {depassement['phrase']}")
    return sortie


def main(argv: list[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analyseur.add_argument("--page", type=Path, default=PAGE)
    analyseur.add_argument("--json", action="store_true",
                           help="la mesure complète, en JSON")
    analyseur.add_argument("--verifier", action="store_true",
                           help="sortir en 1 si une règle est franchie")
    args = analyseur.parse_args(argv)
    try:
        mesure = mesurer(args.page)
    except OSError as erreur:
        print(f"page illisible : {erreur}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(mesure, ensure_ascii=False, indent=2))
        return 0
    for ligne in lignes(mesure):
        print(ligne)
    if args.verifier:
        return 1 if depassements(mesure) else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
