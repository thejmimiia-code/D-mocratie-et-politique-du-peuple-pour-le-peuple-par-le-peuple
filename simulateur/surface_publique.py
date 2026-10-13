"""simulateur/surface_publique.py — ce que la page dit d'elle-même aux robots.

Pourquoi ce module
------------------

Une page publique n'est trouvée que si elle se décrit : un titre, une
description, une adresse canonique, un plan (`sitemap.xml`), des règles de
visite (`robots.txt`) et, pour les lecteurs automatiques — moteurs de réponse,
assistants, catalogues —, un résumé en clair (`llms.txt`).

Recopier ces éléments à quatre endroits est la façon la plus sûre de les voir
diverger : un `sitemap.xml` qui annonce une autre adresse que le
`<link rel="canonical">` de la page envoie les robots au mauvais endroit, et
personne ne s'en aperçoit avant de se demander pourquoi la page ne sort pas.

Ici, tout vient d'une seule source : les constantes ci-dessous et les textes que
ce module compose. Trois consommateurs, aucun doublon :

* ``outils/generer-surface-publique.py`` les écrit à la racine du dépôt (pour
  Vercel, qui sert les fichiers statiques tels quels) ;
* ``simulateur/dashboard.py`` les sert lui-même (pour l'hébergement Python, où
  seul le routeur du simulateur répond) ;
* ``tests/test_indexation.py`` vérifie que la page publiée dit exactement la
  même chose — c'est le seul moyen d'attraper une divergence avant un robot.

Deux règles tenues ici :

* **Aucune dépendance hors bibliothèque standard** et aucun appel réseau : un
  robot qui demande ``/llms.txt`` doit l'obtenir même si la collecte de données
  est hors ligne, et même sur un hébergeur qui n'a installé que le strict
  nécessaire.
* **Rien de faux.** Tout ce qui est écrit ici est vérifiable dans le dépôt ou
  sur la page : pas de note agrégée inventée, pas de nombre décoratif — un
  chiffre annoncé par la page est lu dans le catalogue au moment où on l'écrit.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

RACINE = Path(__file__).resolve().parent.parent

#: Caractères qu'une adresse canonique ne peut pas contenir : ils servent à
#: sortir d'un attribut HTML (`"`, `<`, `>`) ou d'un contexte d'URL.
INTERDITS = "\"'<>"

# ── L'identité publiée ──────────────────────────────────────────────────────
#
# L'adresse canonique est celle de l'alias de production Vercel. La même page
# est servie par deux hébergeurs (Vercel et Render) : c'est *la même* page, et
# le seul moyen de le dire à un moteur est de désigner une adresse canonique
# unique depuis les deux. Render reste annoncé comme la copie de secours, dans
# `llms.txt` et dans la page — un lecteur qui tombe sur l'une doit pouvoir
# trouver l'autre.
URL_CANONIQUE_PAR_DEFAUT = "https://d-mocratie-et-politique-du-peuple-p.vercel.app/"
HOTE_SECOURS = "https://simulateur-macro-politique.onrender.com/"


def _adresse_canonique() -> str:
    """L'adresse qui fait foi, surchargeable pour un miroir.

    La même page peut être servie ailleurs — un miroir, un domaine propre, une
    préproduction. Tant que ces copies déclarent **la même** adresse canonique,
    tout va bien : c'est la page d'origine qui est indexée. Mais un miroir qui
    veut être indexé lui-même doit pouvoir le dire, sans dupliquer ce module :
    il définit ``SIMULATEUR_URL_CANONIQUE`` avant de construire sa page.

    La valeur est vérifiée, et une valeur refusée arrête la construction **avec
    un message** : une adresse canonique fausse ne se voit pas à l'écran — elle
    se voit des semaines plus tard, dans les résultats de recherche, quand il
    est trop tard. Mieux vaut un échec bruyant.
    """
    import os
    import urllib.parse

    valeur = os.environ.get("SIMULATEUR_URL_CANONIQUE", "").strip()
    if not valeur:
        return URL_CANONIQUE_PAR_DEFAUT
    parties = urllib.parse.urlsplit(valeur)
    if (
        parties.scheme not in ("http", "https")
        or not parties.netloc
        or parties.query
        or parties.fragment
            or any(caractere.isspace() or caractere in INTERDITS
                   for caractere in valeur)
    ):
        raise SystemExit(
            "SIMULATEUR_URL_CANONIQUE doit être une adresse de site complète, "
            f"sans paramètre ni fragment (reçu : {valeur!r})"
        )
    return valeur if valeur.endswith("/") else valeur + "/"


#: L'adresse qui fait foi (surchargeable par ``SIMULATEUR_URL_CANONIQUE``).
URL_CANONIQUE = _adresse_canonique()

TITRE = "Simulateur Macro-Politique — Démocratie et politique du peuple"

#: Description publique. Elle est courte (un moteur en affiche environ 150
#: caractères), sans chiffre qui puisse vieillir, et sans promesse : le
#: simulateur calcule, il ne prédit pas.
DESCRIPTION = (
    "Modèle systémique ouvert : réglez les leviers de politique publique et voyez, "
    "échelon par échelon, l'effet sur les budgets, la dette et les services publics."
)

#: Accroche courte des aperçus partagés (Open Graph, Twitter) : la description
#: telle quelle dépasse la place disponible dans une vignette de discussion.
#: Elle ne promet rien que la page ne tienne : ni compte, ni profil.
ACCROCHE = "Régler un plan et voir ce qu'il change, échelon par échelon — sans compte ni profil."

DEPOT = "https://github.com/thejmimiia-code/D-mocratie-et-politique-du-peuple-pour-le-peuple-par-le-peuple"
SITE_MRSC = "https://thejmimiia-code.github.io/MRSC/"
PAGE_MRSC = SITE_MRSC + "simulateur.html"
LOGO_MRSC = SITE_MRSC + "assets/images/logo-mrsc.jpg"
ORGANISATION = "Mouvement Représentatif de la Société Civile (M.R.S.C)"
#: Les licences qu'on sait reconnaître dans le fichier `LICENSE`, et ce qui les
#: distingue. L'ordre compte : les variantes AGPL et LGPL portent, elles aussi,
#: les mots « GENERAL PUBLIC LICENSE », donc elles se testent avant la GPL.
SIGNATURES_LICENCES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("AGPL-3.0", ("GNU AFFERO GENERAL PUBLIC LICENSE", "VERSION 3")),
    ("LGPL-3.0", ("GNU LESSER GENERAL PUBLIC LICENSE", "VERSION 3")),
    ("GPL-3.0", ("GNU GENERAL PUBLIC LICENSE", "VERSION 3")),
    ("GPL-2.0", ("GNU GENERAL PUBLIC LICENSE", "VERSION 2")),
    ("Apache-2.0", ("APACHE LICENSE", "VERSION 2.0")),
    ("BSD-3-Clause", ("BSD 3-CLAUSE LICENSE",)),
    ("MIT", ("MIT LICENSE", "PERMISSION IS HEREBY GRANTED")),
)


def licence_du_depot(racine: Path = RACINE) -> str:
    """L'identifiant de la licence du dépôt, **lu** dans le fichier `LICENSE`.

    Cette fonction existe à cause d'une erreur réelle : le nom de la licence
    était recopié ici (`« MIT »`), et n'a pas suivi le passage du dépôt à la
    GPL-3.0. Trois fichiers servis aux robots — `robots.txt`, `llms.txt`,
    `llms-full.txt` — ont donc annoncé, pendant des semaines, une licence qui
    n'était plus la leur (« MIT »), à
    des moteurs et à des lecteurs automatiques, alors que le fichier `LICENSE`,
    le classificateur de `pyproject.toml`, `package.json` et le `README.md`
    disaient GPL-3.0. Une licence fausse n'est pas une coquille : c'est une
    affirmation juridique, et elle était fausse **sur ce qui est publié**.

    Elle rend `""` si le fichier est absent ou la licence non reconnue : dans ce
    cas on renvoie au fichier au lieu d'annoncer un nom. Deviner serait refaire
    l'erreur qu'on répare.
    """
    try:
        texte = (racine / "LICENSE").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    tete = texte[:4000].upper()
    for identifiant, indices in SIGNATURES_LICENCES:
        if all(indice in tete for indice in indices):
            return identifiant
    return ""


#: La licence du dépôt, telle qu'elle est écrite dans `LICENSE`. Ne pas la
#: remplacer par un nom recopié : un contrôle refuse un nom qui ne serait pas
#: celui du fichier (voir `tests/test_licence_du_depot.py`).
LICENCE = licence_du_depot()
LICENCE_URL = DEPOT + "/blob/main/LICENSE"


def mention_licence() -> str:
    """La licence telle qu'on l'écrit dans un texte publié.

    Avec un fichier reconnu : « licence GPL-3.0 ». Sans lui : un renvoi au
    fichier, jamais un nom inventé.
    """
    return f"licence {LICENCE}" if LICENCE else "licence indiquée dans le fichier LICENSE"
LANGUE = "fr"

#: Images de la page. Les chemins sont **relatifs** au document : la même page
#: est servie à la racine (Vercel, Render) et dans `simulateur/` chez le site
#: M.R.S.C, qui recopie le moteur dans un sous-dossier — un chemin absolu y
#: pointerait à côté.
IMAGE_APERCU = "og-image.png"

#: Icônes de l'onglet et du raccourci. Elles entrent dans la page en `data:` :
#: l'onglet reste reconnaissable hors ligne, et la copie embarquée par le site
#: M.R.S.C (qui vit dans un sous-dossier) n'a aucun chemin à résoudre.
ICONES = ("favicon.svg", "apple-touch-icon.png")

#: Le fichier de repli, servi à la racine pour ce qui le demande sans lire la
#: page (Google, notamment, cherche `/favicon.ico` avant tout).
ICONE_REPLI = "favicon.ico"

#: Types MIME servis par le routeur Python. Vercel les déduit de l'extension ;
#: ici, il faut les écrire.
TEXTES: dict[str, str] = {
    "/robots.txt": "text/plain; charset=utf-8",
    "/sitemap.xml": "application/xml; charset=utf-8",
    "/llms.txt": "text/plain; charset=utf-8",
        "/llms-full.txt": "text/plain; charset=utf-8",
}
IMAGES: dict[str, str] = {
    "/favicon.svg": "image/svg+xml",
    "/favicon.ico": "image/x-icon",
    "/apple-touch-icon.png": "image/png",
    "/" + IMAGE_APERCU: "image/png",
}


# ── robots.txt ──────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def robots_txt() -> str:
    """Les règles de visite, en clair, avec les raisons.

    Un seul groupe ``User-agent: *`` : tout ce qui est publié ici est fait pour
    être lu, y compris par les assistants qui répondent à une question en citant
    leurs sources. Ajouter un groupe par robot serait plus bavard et plus
    risqué — un groupe nommé remplace le groupe générique pour ce robot, donc
    chaque groupe devrait répéter l'exclusion de ``/api/``. Un seul groupe ne
    peut pas diverger de lui-même.

    La seule fermeture est ``/api/`` : ce sont des points de calcul, pas des
    pages. Les indexer ne produit que des résultats vides, et chaque visite
    coûte un calcul complet.
    """
    return f"""# robots.txt — Simulateur macro-politique — M.R.S.C.
#
# Tout ce qui est publié ici est fait pour être lu, cité et analysé : c'est un
# outil citoyen à code ouvert, financé par personne et discuté publiquement.
# Les moteurs de recherche, les moteurs de réponse et les assistants qui lisent
# les contenus pour répondre à une question y sont donc les bienvenus.
#
# Une seule fermeture : /api/. Ce sont des points de calcul, pas des pages :
# les indexer ne remplit les résultats que de pages vides, et chaque visite
# déclenche une simulation complète.

User-agent: *

# Convention « Content Signals » (contentsignals.org), lue par les robots qui
# la connaissent et ignorée par les autres : recherche, réponse assistée et
# entraînement sont autorisés. Les textes publiés ici sont faits pour être lus
# et cités ; le code du dépôt est sous {mention_licence()}.
Content-Signal: search=yes, ai-input=yes, ai-train=yes

Allow: /
Disallow: /api/

# Adresses
Sitemap: {URL_CANONIQUE}sitemap.xml
# Résumé en clair pour les lecteurs automatiques : {URL_CANONIQUE}llms.txt
# Contenu complet, sans JavaScript : {URL_CANONIQUE}llms-full.txt
"""


# ── sitemap.xml ─────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def sitemap_xml() -> str:
    """Le plan du site : une seule adresse, la canonique.

    La page est un outil, pas une collection de pages : les vues (scénarios,
    scènes, onglets) sont des états internes, pas des adresses. Le plan déclare
    donc l'unique adresse publique, et n'invente ni ``lastmod`` ni ``priority`` :
    une date de modification qui n'est pas la vraie est pire que pas de date —
    les moteurs cessent de s'y fier, y compris quand elle redevient juste.
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- Plan du site : une seule page publique, la page interactive.
     Les vues (scénario, scène, onglet) ne sont pas des adresses : elles ne
     sont pas listées ici, et la page les canonicalise vers cette adresse. -->
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{URL_CANONIQUE}</loc>
    <changefreq>weekly</changefreq>
  </url>
</urlset>
"""


# ── llms.txt ────────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def llms_txt() -> str:
    """Résumé pour les lecteurs automatiques, au format llms.txt.

    Le format (llmstxt.org) tient en trois règles : un titre, une citation qui
    résume, puis des sections de liens. Il ne remplace pas la page — il dit à un
    assistant où est le contenu et ce qu'il contient, pour qu'une réponse citée
    ne se trompe ni d'adresse ni de nature.
    """
    return f"""# {TITRE}

> Outil citoyen à code ouvert : régler les leviers de politique publique et voir, échelon par échelon — local, national, européen, mondial, géopolitique —, ce que cela change pour les budgets, la dette, les services publics et la cohésion du pays.

Le simulateur est un modèle systémique assumé : il calcule des écarts entre des
hypothèses, il ne prédit ni élection ni croissance. Les observations réelles
(données publiques, datées, sourcées et licenciées) restent séparées des
trajectoires simulées, et chaque chiffre affiché porte sa source et sa période.

La même page est servie par deux hébergeurs ; l'adresse canonique est
{URL_CANONIQUE}. La copie de secours ({HOTE_SECOURS}) sert exactement la même
page, et le site du M.R.S.C en propose une troisième, présentée à la main.

## L'outil

- [Simulateur macro-politique]({URL_CANONIQUE}) : la page interactive — catalogue, scènes, scénarios, audit et sources ; aucun compte, aucun profilage.
- [Copie de secours, même page]({HOTE_SECOURS}) : autre hébergeur, même moteur, si le premier ne répond pas.
- [Présentation du M.R.S.C]({PAGE_MRSC}) : ce que l'outil fait et ne fait pas, en clair, sans JavaScript.
- [Le contenu complet en un fichier]({URL_CANONIQUE}llms-full.txt) : le catalogue des leviers, les domaines, les scénarios, les sources — tout en texte.
- [Code source du moteur]({DEPOT}) : {mention_licence()}, historique complet, tests.

## La méthode, les données et les limites

- [Sources, auditabilité et modèle]({DEPOT}/blob/main/docs/13_REGISTRE_DES_SOURCES_AUDITABILITE_ET_MODELE_SOCIO_MONDIAL.md) : d'où vient chaque chiffre, quelle licence, quelle période.
- [Méthodologie]({DEPOT}/blob/main/docs/METHODOLOGIE.md) : comment le modèle est construit, ce qu'il simplifie, ce qu'il ne sait pas faire.
- [Les cinq classes de leviers]({DEPOT}/blob/main/docs/RD_CLASSES_LEVIERS.md) : recettes, économies d'efficacité, dépenses, règles du jeu, monde subi.
- [Objections ouvertes]({DEPOT}/blob/main/docs/21_OBJECTIONS_OUVERTES.md) : les critiques adressées à l'outil, et ce qu'elles changent.
- [Hébergement et intégration]({DEPOT}/blob/main/docs/HEBERGEMENT.md) : où la page est servie, comment elle s'intègre ailleurs, quelles routes expose son API.

## Optional

- [Règles de visite]({URL_CANONIQUE}robots.txt) : tout est ouvert, sauf ``/api/`` (points de calcul).
- [Plan du site]({URL_CANONIQUE}sitemap.xml) : une adresse.
- [Dépôt du site M.R.S.C]({SITE_MRSC}) : l'association, ses fiches et ses documents.
"""


# ── llms-full.txt ───────────────────────────────────────────────────────────
def _leviers_par_classe() -> dict[str, list[Any]]:
    """Le catalogue, groupé par classe, dans l'ordre de lecture de la page."""
    from simulateur import classes_leviers
    from simulateur.parametres import LEVIERS

    groupes: dict[str, list[Any]] = {cle: [] for cle in classes_leviers.CLASSES}
    for cle, levier in LEVIERS.items():
        groupes[classes_leviers.classe_de(cle)].append(levier)
    return {
        cle: sorted(leviers, key=lambda levier: levier.libelle.lower())
        for cle, leviers in groupes.items()
        if leviers
    }


def _description_courte(texte: str, limite: int = 320) -> str:
    """Première phrase(s) d'un texte, sans couper au milieu d'un mot."""
    if len(texte) <= limite:
        return texte
    coupe = texte.rfind(" ", 0, limite)
    return (texte[:coupe] if coupe > 0 else texte[:limite]).rstrip(" ,;:") + "…"


@lru_cache(maxsize=1)
def llms_complet() -> str:
    """Tout le contenu public en un seul fichier texte.

    C'est la réponse à « que contient cet outil ? » pour un lecteur qui ne joue
    pas la page : chaque levier avec sa classe, son unité et ses bornes, chaque
    domaine d'impact, chaque scénario type, et les sources. Les descriptions
    longues sont coupées — le fichier reste lisible d'un bout à l'autre, et la
    page reste la référence.
    """
    from simulateur import classes_leviers
    from simulateur.dashboard import SCENARIOS
    from simulateur.domaines import DOMAINES
    from simulateur.donnees_live import INDICATEURS
    from simulateur.parametres import LEVIERS

    lignes: list[str] = [
        f"# {TITRE} — le contenu, en texte",
        "",
        f"> {DESCRIPTION}",
        "",
        f"Adresse canonique : <{URL_CANONIQUE}>",
        f"Code source ({mention_licence()}) : [dépôt du simulateur]({DEPOT})",
        f"Présentation par le M.R.S.C : [page du site]({PAGE_MRSC})",
        "",
        "Ce fichier est engendré par `simulateur/surface_publique.py` à partir du",
        "catalogue du moteur : les nombres et les libellés qui suivent sont ceux de",
        "l'outil publié, pas une copie figée. Les descriptions sont coupées à la",
        "première phrase utile ; la page interactive donne le texte entier.",
        "",
        "## Ce que contient l'outil",
        "",
        f"- {len(LEVIERS)} leviers réglables, rangés en {len(classes_leviers.CLASSES)} classes ;",
        f"- {len(DOMAINES)} domaines d'impact, notés de 0 à 100 ;",
        f"- {len(INDICATEURS)} indicateurs publics collectés à la source, avec provenance, période et licence ;",
        f"- {len(SCENARIOS)} scénarios types rejouables, année par année ;",
        "- 5 échelons en cascade : local, national, européen, mondial, géopolitique ;",
        "- un audit qui affiche, pour chaque réglage, sa plage, son effet déclaré et sa source.",
        "",
        "## Les classes de leviers",
        "",
    ]
    for cle, classe in sorted(classes_leviers.CLASSES.items(), key=lambda item: item[1].ordre):
        lignes += [
            f"### {classe.libelle} ({classe.symbole}) — `{cle}`",
            "",
            f"{classe.question} {classe.definition}",
            "",
        ]
        for levier in _leviers_par_classe().get(cle, []):
            bornes = ""
            if levier.type == "curseur":
                bornes = f" — de {levier.minimum:g} à {levier.maximum:g} {levier.unite}, défaut {levier.defaut:g}"
            lignes.append(
                f"- **{levier.libelle}** (`{levier.cle}`){bornes} : {_description_courte(levier.description)}"
            )
        lignes.append("")

    lignes += ["## Les domaines d'impact", ""]
    for domaine in DOMAINES:
        lignes.append(f"- **{domaine.libelle}** (`{domaine.cle}`) : {domaine.description}")
    lignes.append("")

    lignes += ["## Les scénarios types", ""]
    for cle, scenario in sorted(SCENARIOS.items(), key=lambda item: item[1]["nom"]):
        lignes.append(f"- **{scenario['nom']}** (`{cle}`) : {scenario['description']}")
    lignes.append("")

    lignes += [
        "## Ce que l'outil ne fait pas",
        "",
        "- il ne prédit ni élection ni croissance : c'est un modèle, donc une simplification assumée ;",
        "- il ne remplace ni l'expertise des services publics ni le débat démocratique ;",
        "- il ne demande ni compte ni identité ; les requêtes de données passent par son propre serveur.",
        "",
        "## Sources",
        "",
        "Les observations réelles viennent de sources publiques (Eurostat, Banque centrale",
        "européenne, Banque mondiale, Frankfurter, Opendatasoft, Yahoo, Stooq), chacune avec sa",
        "période, sa licence et sa date de relevé.",
        "",
        f"[Registre des sources, de l'auditabilité et du modèle]({DEPOT}/blob/main/"
        "docs/13_REGISTRE_DES_SOURCES_AUDITABILITE_ET_MODELE_SOCIO_MONDIAL.md)",
        "",
        f"[Méthodologie du modèle]({DEPOT}/blob/main/docs/METHODOLOGIE.md)",
        "",
    ]
    return "\n".join(lignes)


_FABRIQUES = {
    "/robots.txt": robots_txt,
    "/sitemap.xml": sitemap_xml,
    "/llms.txt": llms_txt,
    "/llms-full.txt": llms_complet,
}


def texte(chemin: str) -> str | None:
    """Le texte publié pour ce chemin, ou ``None`` si ce chemin n'en a pas."""
    fabrique = _FABRIQUES.get(chemin)
    return fabrique() if fabrique else None


def chemin_image(chemin: str) -> Path | None:
    """Le fichier d'image publié pour ce chemin, ou ``None``.

    Le nom est cherché dans la liste blanche ``IMAGES`` : aucun chemin venu de
    la requête ne peut faire lire autre chose que ces quelques fichiers.
    """
    if chemin not in IMAGES:
        return None
    return RACINE / chemin.lstrip("/")


# ── L'en-tête de la page ────────────────────────────────────────────────────
@lru_cache(maxsize=8)
def donnee_uri(nom: str) -> str:
    """Le fichier d'icône, en `data:` — donc **dans** la page.

    La page est un fichier unique : elle doit s'ouvrir hors ligne, et la copie
    que le site M.R.S.C embarque vit dans un sous-dossier, où un chemin absolu
    pointerait à côté. Une icône en `data:` règle les deux cas et ne coûte que
    quelques kilo-octets. Si le fichier manque, la fonction rend une chaîne vide
    et l'en-tête omet simplement le lien : jamais d'icône cassée, jamais de page
    qui refuse de se charger pour une image.
    """
    import base64
    import mimetypes
    import urllib.parse

    fichier = RACINE / nom
    if nom not in ICONES or not fichier.is_file():
        return ""
    donnees = fichier.read_bytes()
    type_mime = mimetypes.guess_type(nom)[0] or "application/octet-stream"
    if type_mime == "image/svg+xml":
        # Le SVG est du texte : on le garde lisible, en n'échappant que ce qui
        # doit l'être dans une adresse (les `#` des couleurs, les chevrons).
        return "data:image/svg+xml," + urllib.parse.quote(
            donnees.decode("utf-8"), safe=""
        )
    return f"data:{type_mime};base64," + base64.b64encode(donnees).decode("ascii")


def entete_html() -> str:
    """Les balises du `<head>` que lisent les moteurs, les aperçus et les robots.

    Elle est injectée dans la page au chargement du module
    (`simulateur/interface.py`) : la page servie par Vercel, celle servie par
    Render et celle que le site M.R.S.C recopie dans `simulateur/` portent donc
    exactement les mêmes balises, sans recopie manuelle nulle part.
    """
    icone = donnee_uri(ICONES[0])
    raccourci = donnee_uri(ICONES[1])
    lignes = [
        f'<meta name="description" content="{DESCRIPTION}">',
        '<meta name="theme-color" content="#0b1220">',
        f'<link rel="canonical" href="{URL_CANONIQUE}">',
        '<meta name="robots" content="index, follow, max-snippet:-1, '
        'max-image-preview:large, max-video-preview:-1">',
    ]
    if icone:
        lignes.append(f'<link rel="icon" href="{icone}">')
    if raccourci:
        lignes.append(f'<link rel="apple-touch-icon" href="{raccourci}">')
    lignes += [
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Simulateur Macro-Politique — M.R.S.C.">',
        '<meta property="og:locale" content="fr_FR">',
        f'<meta property="og:title" content="{TITRE}">',
        f'<meta property="og:description" content="{ACCROCHE}">',
        f'<meta property="og:url" content="{URL_CANONIQUE}">',
        f'<meta property="og:image" content="{URL_CANONIQUE}{IMAGE_APERCU}">',
        '<meta property="og:image:type" content="image/png">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta property="og:image:alt" content="Aperçu de l\'outil : titre, '
        'quatre chiffres clés et ruban de veille permanente.">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{TITRE}">',
        f'<meta name="twitter:description" content="{ACCROCHE}">',
        f'<meta name="twitter:image" content="{URL_CANONIQUE}{IMAGE_APERCU}">',
        '<script type="application/ld+json">',
        json.dumps(donnees_structurees(), ensure_ascii=False, indent=2),
        "</script>",
    ]
    return "\n".join(lignes) + "\n"


# ── Données structurées (JSON-LD) ───────────────────────────────────────────
def donnees_structurees() -> dict[str, Any]:
    """Ce que la page est, en données lisibles par une machine.

    Trois nœuds, reliés entre eux : le site, l'outil, et l'organisation qui le
    publie. Rien d'autre — pas de note agrégée, pas d'avis, pas de prix : les
    moteurs pénalisent les balisages qui promettent des résultats enrichis sans
    contenu réel derrière.

    La classe ``GovernmentApplication`` décrit l'usage (politique publique) ;
    ``applicationCategory`` accepte un texte libre, et cette valeur est celle
    qui se lit le mieux dans les catalogues.
    """
    organisation = SITE_MRSC + "#organisation"
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": organisation,
                "name": ORGANISATION,
                "url": SITE_MRSC,
                "logo": LOGO_MRSC,
                "sameAs": [DEPOT],
            },
            {
                "@type": "WebSite",
                "@id": URL_CANONIQUE + "#site",
                "url": URL_CANONIQUE,
                "name": TITRE,
                "description": DESCRIPTION,
                "inLanguage": LANGUE,
                "publisher": {"@id": organisation},
            },
            {
                "@type": "WebApplication",
                "@id": URL_CANONIQUE + "#outil",
                "name": TITRE,
                "url": URL_CANONIQUE,
                "description": DESCRIPTION,
                "applicationCategory": "GovernmentApplication",
                "operatingSystem": "Web",
                "browserRequirements": "JavaScript activé pour la simulation ; la page reste lisible sans lui.",
                "inLanguage": LANGUE,
                "isAccessibleForFree": True,
                "license": LICENCE_URL,
                "codeRepository": DEPOT,
                "featureList": [
                    "Régler les leviers de politique publique et lire l'effet, échelon par échelon",
                    "Comparer des scénarios types, année par année",
                    "Auditer chaque réglage : plage, effet déclaré, source",
                    "Croiser les mesures avec les domaines d'impact notés de 0 à 100",
                    "Exporter la simulation en JSON ou CSV",
                ],
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
                "publisher": {"@id": organisation},
                "isPartOf": {"@id": URL_CANONIQUE + "#site"},
            },
        ],
    }


def json_donnees_structurees() -> str:
    """Les données structurées, prêtes à être servies (compactes)."""
    return json.dumps(donnees_structurees(), ensure_ascii=False, separators=(",", ":"))
