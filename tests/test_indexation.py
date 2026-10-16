"""
tests/test_indexation.py — la page se décrit-elle correctement aux robots ?

Ce que ce fichier surveille
---------------------------

Une page publique est trouvée si elle se décrit **de la même façon partout** :
l'en-tête de la page, `robots.txt`, `sitemap.xml`, `llms.txt`, le manifeste et
les images. Le danger n'est pas d'oublier une balise — c'est d'en corriger une
et d'en oublier une autre : une adresse canonique qui ne correspond pas à
`sitemap.xml` envoie les robots ailleurs, un aperçu qui annonce 93 leviers quand
le catalogue en compte 156 fait douter de tout le reste.

Les contrôles ici sont donc de deux sortes :

* **cohérence** — tout vient de `simulateur/surface_publique.py` ; ces tests
  refusent une divergence entre le module et ce qui est publié ;
* **honnêteté** — les nombres annoncés sont comparés au catalogue, les liens
  écrits dans les fichiers publics doivent exister, et aucune donnée structurée
  n'est acceptée si elle promet un résultat enrichi que la page n'a pas
  (`aggregateRating`, `review`, `faqPage`… les moteurs sanctionnent ces
  balisages-là, et une page qui triche n'est plus classée du tout).
"""

from __future__ import annotations

import json
import re
import socket
import struct
import subprocess
import sys
import threading
import unittest
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ElementTree
from datetime import date
from html.parser import HTMLParser
from importlib import import_module
from pathlib import Path

from simulateur import surface_publique as surface

RACINE = Path(__file__).resolve().parent.parent
PAGE = RACINE / "index.html"

#: Les fichiers publiés pour les robots, et le module qui les produit.
FICHIERS_PUBLIES = {
    "robots.txt": "/robots.txt",
    "sitemap.xml": "/sitemap.xml",
    "llms.txt": "/llms.txt",
    "llms-full.txt": "/llms-full.txt",
}

#: Les images publiées, avec leur taille réelle (largeur, hauteur).
IMAGES_PUBLIEES = {
    "og-image.png": (1200, 630),
    "apple-touch-icon.png": (180, 180),
    "docs/apercu_social.png": (1280, 640),
}


def entete_html() -> str:
    """Le contenu de `<head>`, sans le style ni les scripts."""
    page = PAGE.read_text(encoding="utf-8")
    return page[: page.index("</head>")]


class EnTete(HTMLParser):
    """Relève les balises `<head>` qui décident de l'indexation."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.langue = ""
        self.titre = ""
        self.metas: list[dict[str, str]] = []
        self.liens: list[dict[str, str]] = []
        self.scripts_structurees: list[str] = []
        self.ressources_distantes: list[tuple[str, str]] = []
        self.dans_titre = False
        self._type_script = ""
        self._dans_structurees = False
        self._tampon: list[str] = []

    def handle_starttag(self, tag, attrs):
        attributs = {nom: (valeur or "") for nom, valeur in attrs}
        if tag == "html":
            self.langue = attributs.get("lang", "")
        elif tag == "title":
            self.dans_titre = True
        elif tag == "meta":
            self.metas.append(attributs)
        elif tag == "link":
            self.liens.append(attributs)
        elif tag == "script":
            self._type_script = attributs.get("type", "").lower()
            self._dans_structurees = self._type_script == "application/ld+json"
            self._tampon = []
        elif tag in ("img", "iframe", "embed", "source") and attributs.get("src", "").startswith(
            ("http://", "https://")
        ):
            self.ressources_distantes.append((tag, attributs["src"]))

    def handle_data(self, data):
        if self.dans_titre:
            self.titre += data
        if self._dans_structurees:
            self._tampon.append(data)

    def handle_endtag(self, tag):
        if tag == "title":
            self.dans_titre = False
        elif tag == "script" and self._dans_structurees:
            self.scripts_structurees.append("".join(self._tampon))
            self._dans_structurees = False

    # ── commodités ──────────────────────────────────────────────────────────
    def meta(self, nom: str, valeur: str) -> list[dict[str, str]]:
        return [
            balise
            for balise in self.metas
            if balise.get(nom, "").lower() == valeur.lower()
        ]

    def meta_unique(self, nom: str, valeur: str) -> dict[str, str]:
        trouves = self.meta(nom, valeur)
        if len(trouves) != 1:
            raise AssertionError(
                f"attendu une seule balise <meta {nom}=\"{valeur}\">, trouvé {len(trouves)}"
            )
        return trouves[0]

    def lien(self, relation: str) -> list[dict[str, str]]:
        return [
            balise
            for balise in self.liens
            if relation in balise.get("rel", "").lower().split()
        ]


class BaseIndexation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE.read_text(encoding="utf-8")
        cls.entete = EnTete()
        cls.entete.feed(entete_html())


class TestEnTetePublic(BaseIndexation):
    """Ce qu'un moteur lit avant d'exécuter quoi que ce soit."""

    def test_langue_et_titre(self):
        self.assertEqual(self.entete.langue, surface.LANGUE)
        self.assertEqual(self.entete.titre, surface.TITRE)

    def test_description_presente_et_de_bonne_longueur(self):
        description = self.entete.meta_unique("name", "description")["content"]
        self.assertEqual(description, surface.DESCRIPTION)
        # Un moteur tronque au-delà d'environ 160 caractères, et une description
        # trop courte n'apprend rien.
        self.assertGreaterEqual(len(description), 50)
        self.assertLessEqual(len(description), 160)

    def test_robots_autorise_l_indexation_et_les_extraits_longs(self):
        contenu = self.entete.meta_unique("name", "robots")["content"]
        directives = {morceau.strip().lower() for morceau in contenu.split(",")}
        self.assertIn("index", directives)
        self.assertIn("follow", directives)
        self.assertIn("max-snippet:-1", directives)
        self.assertIn("max-image-preview:large", directives)
        self.assertNotIn("noindex", directives)
        self.assertNotIn("nofollow", directives)
        self.assertNotIn("nosnippet", directives)

    def test_adresse_canonique_unique(self):
        liens = self.entete.lien("canonical")
        self.assertEqual(len(liens), 1, "une seule adresse canonique, sinon aucune ne fait foi")
        self.assertEqual(liens[0]["href"], surface.URL_CANONIQUE)
        self.assertTrue(surface.URL_CANONIQUE.endswith("/"))

    def test_apercu_de_partage_complet(self):
        for propriete in ("og:type", "og:title", "og:description", "og:url", "og:image", "og:locale"):
            with self.subTest(propriete=propriete):
                balise = self.entete.meta_unique("property", propriete)
                self.assertTrue(balise["content"].strip())
        self.assertEqual(self.entete.meta_unique("property", "og:url")["content"], surface.URL_CANONIQUE)
        self.assertEqual(self.entete.meta_unique("property", "og:locale")["content"], "fr_FR")
        self.assertEqual(
            self.entete.meta_unique("property", "og:image")["content"],
            surface.URL_CANONIQUE + surface.IMAGE_APERCU,
        )
        # Les dimensions annoncées doivent être celles du fichier : un aperçu
        # rogné au hasard s'affiche mal, et les réseaux préfèrent alors ne rien
        # montrer du tout.
        self.assertEqual(self.entete.meta_unique("property", "og:image:width")["content"], "1200")
        self.assertEqual(self.entete.meta_unique("property", "og:image:height")["content"], "630")
        self.assertTrue(self.entete.meta_unique("property", "og:image:alt")["content"].strip())

    def test_apercu_des_messages_courts(self):
        self.assertEqual(
            self.entete.meta_unique("name", "twitter:card")["content"], "summary_large_image"
        )
        self.assertEqual(
            self.entete.meta_unique("name", "twitter:image")["content"],
            surface.URL_CANONIQUE + surface.IMAGE_APERCU,
        )

    def test_les_icones_voyagent_dans_la_page(self):
        """Les icônes sont en `data:` : rien à charger, rien à résoudre.

        La page est un fichier unique, servie à la racine (Vercel, Render) et
        recopiée dans un sous-dossier par le site M.R.S.C. Une icône en `data:`
        se moque des deux : elle s'affiche hors ligne et chez tout le monde.

        Le contrôle ne se contente pas de la forme : il **décode** chaque
        `data:` et compare les octets à ceux du fichier versionné. Sans cela,
        une icône vide ou tronquée passerait inaperçue.
        """
        import base64
        import urllib.parse

        for relation, fichier in zip(("icon", "apple-touch-icon"), surface.ICONES, strict=True):
            with self.subTest(fichier=fichier):
                balises = self.entete.lien(relation)
                self.assertEqual(len(balises), 1)
                href = balises[0]["href"]
                self.assertTrue(href.startswith("data:"), "icône en data: attendue")
                self.assertNotIn("http", href.split(",", 1)[0].replace("data:", ""))
                entete_donnees, _, donnees = href.partition(",")
                if "base64" in entete_donnees:
                    octets = base64.b64decode(donnees)
                else:
                    octets = urllib.parse.unquote(donnees).encode("utf-8")
                self.assertEqual(octets, (RACINE / fichier).read_bytes(),
                                 f"{fichier} : le contenu embarqué a divergé du fichier")

    def test_le_fichier_de_repli_de_licone_reste_publie(self):
        """`/favicon.ico` est demandé sans lire la page : il doit exister."""
        self.assertTrue((RACINE / surface.ICONE_REPLI).is_file())
        self.assertIn("/" + surface.ICONE_REPLI, surface.IMAGES)

    def test_aucune_ressource_distante(self):
        self.assertEqual(self.entete.ressources_distantes, [])
        self.assertNotIn("<link rel=\"stylesheet\" href=\"http", self.page)
        self.assertNotIn("<script src=", self.page)

    def test_donnees_structurees_presentes_et_honnetes(self):
        self.assertEqual(len(self.entete.scripts_structurees), 1)
        donnees = json.loads(self.entete.scripts_structurees[0])
        self.assertEqual(donnees["@context"], "https://schema.org")
        types = [noeud.get("@type") for noeud in donnees["@graph"]]
        self.assertEqual(types, ["Organization", "WebSite", "WebApplication"])

        outil = next(noeud for noeud in donnees["@graph"] if noeud["@type"] == "WebApplication")
        self.assertEqual(outil["url"], surface.URL_CANONIQUE)
        self.assertEqual(outil["name"], surface.TITRE)
        self.assertEqual(outil["license"], surface.LICENCE_URL)
        self.assertEqual(outil["codeRepository"], surface.DEPOT)
        self.assertIs(outil["isAccessibleForFree"], True)
        self.assertEqual(outil["offers"]["price"], "0")
        self.assertEqual(outil["inLanguage"], surface.LANGUE)
        self.assertTrue(outil["featureList"])

        # Aucune promesse de résultat enrichi : la page n'a ni avis, ni note
        # agrégée, ni foire aux questions balisée.
        interdits = {"aggregateRating", "review", "reviews", "ratingValue", "faqPage"}
        presents = interdits.intersection(json.dumps(donnees).split('"'))
        self.assertEqual(presents, set(), f"balisage interdit : {sorted(presents)}")

    def test_donnees_structurees_sans_danger_pour_la_page(self):
        """Le bloc JSON-LD est du texte *dans* la page : il ne doit pas en sortir."""
        bloc = self.entete.scripts_structurees[0]
        self.assertNotIn("</script", bloc.lower())
        self.assertNotIn("<!--", bloc)
        # U+2028 et U+2029 terminent une ligne en JavaScript : échappés, jamais bruts.
        self.assertNotIn("\u2028", bloc)
        self.assertNotIn("\u2029", bloc)

    def test_les_metadonnees_ne_promettent_aucun_nombre(self):
        """Un compte dans une description vieillit sans que personne ne le voie.

        « 93 leviers », « 38 indicateurs » : la page a déjà affiché ces nombres
        après qu'ils étaient faux. Les métadonnées ne portent donc **aucun**
        nombre — les comptes vivent dans `llms-full.txt` et dans la page, où un
        contrôle les compare au catalogue (`outils/verifier-compteurs.py`).
        """
        for nom, texte in (("DESCRIPTION", surface.DESCRIPTION), ("ACCROCHE", surface.ACCROCHE)):
            with self.subTest(champ=nom):
                self.assertIsNone(re.search(r"\d", texte), f"{nom} annonce un nombre")

    def test_les_comptes_des_donnees_structurees_sont_dans_le_catalogue(self):
        """Ce qui est balisé reste vérifiable : aucun chiffre étranger au catalogue."""
        donnees = json.loads(self.entete.scripts_structurees[0])
        outil = next(noeud for noeud in donnees["@graph"] if noeud["@type"] == "WebApplication")
        texte = " ".join(outil["featureList"]) + outil["description"]
        annonces = {int(nombre) for nombre in re.findall(r"(?<![\d,.])-?\d{2,}(?![\d,.])", texte)}
        du_catalogue = {
            len(import_module("simulateur.parametres").LEVIERS),
            len(import_module("simulateur.domaines").DOMAINES),
            len(import_module("simulateur.classes_leviers").CLASSES),
            len(import_module("simulateur.donnees_live").INDICATEURS),
        }
        # Seule exception admise : l'échelle des notes de domaine (« notés de 0 à
        # 100 »). Ce n'est pas un compte, et l'exception est elle-même justifiée
        # par le catalogue : sans l'échelle déclarée dans `domaines.py`, elle
        # tombe et le nombre redevient suspect.
        source_domaines = (RACINE / "simulateur" / "domaines.py").read_text(encoding="utf-8")
        echelle = {100} if re.search(r"\b0-100\b|0 à 100", source_domaines) else set()
        self.assertTrue(
            annonces <= du_catalogue | echelle,
            f"nombres hors catalogue : {sorted(annonces - du_catalogue - echelle)}",
        )


class TestFichiersPublies(unittest.TestCase):
    """Les fichiers que les robots demandent avant la page."""

    def test_les_fichiers_correspondent_au_module(self):
        """S'ils divergent, c'est Vercel qui servira l'ancien texte, pas le module."""
        resultat = subprocess.run(
            [sys.executable, "outils/generer-surface-publique.py", "--verifier"],
            cwd=RACINE,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)

    def test_chaque_fichier_annonce_est_ecrit(self):
        for nom, chemin in FICHIERS_PUBLIES.items():
            with self.subTest(fichier=nom):
                fichier = RACINE / nom
                self.assertTrue(fichier.is_file(), f"{nom} absent de la racine")
                contenu = fichier.read_text(encoding="utf-8")
                self.assertEqual(contenu, surface.texte(chemin))
                self.assertTrue(contenu.endswith("\n"))
                self.assertNotIn("====", contenu, "gabarit non rempli")

    def test_robots_txt_ouvre_et_ne_ferme_que_les_points_de_calcul(self):
        contenu = (RACINE / "robots.txt").read_text(encoding="utf-8")
        self.assertEqual(contenu.count("User-agent:"), 1)
        self.assertIn("User-agent: *", contenu)
        self.assertIn("Allow: /", contenu)
        self.assertIn("Disallow: /api/", contenu)
        self.assertNotRegex(contenu, r"(?m)^\s*Disallow:\s*/\s*$")
        self.assertNotIn("noindex", contenu.lower())
        self.assertIn("Content-Signal: search=yes, ai-input=yes, ai-train=yes", contenu)
        # Le plan doit être annoncé à l'adresse qui fait foi, en absolu : un
        # chemin relatif est refusé par les robots qui suivent cette directive.
        self.assertIn(f"Sitemap: {surface.URL_CANONIQUE}sitemap.xml", contenu)

    def test_sitemap_declare_une_seule_adresse_et_la_bonne(self):
        arbre = ElementTree.fromstring((RACINE / "sitemap.xml").read_text(encoding="utf-8"))
        espace = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        adresses = [noeud.text for noeud in arbre.iter(f"{espace}loc")]
        self.assertEqual(adresses, [surface.URL_CANONIQUE])
        # Ni date de modification inventée, ni priorité décorative.
        for balise in ("lastmod", "priority"):
            self.assertEqual(list(arbre.iter(f"{espace}{balise}")), [])

    def test_llms_txt_se_lit_comme_une_fiche(self):
        contenu = (RACINE / "llms.txt").read_text(encoding="utf-8")
        self.assertTrue(contenu.startswith("# "))
        lignes = contenu.splitlines()
        self.assertTrue(any(ligne.startswith("> ") for ligne in lignes), "résumé en citation attendu")
        self.assertIn(f"]({surface.URL_CANONIQUE})", contenu)
        self.assertIn(surface.DEPOT, contenu)
        self.assertTrue(any(ligne.startswith("## Optional") for ligne in lignes))

    def test_llms_full_contient_tout_le_catalogue(self):
        from simulateur.classes_leviers import CLASSES
        from simulateur.dashboard import SCENARIOS
        from simulateur.domaines import DOMAINES
        from simulateur.parametres import LEVIERS

        contenu = (RACINE / "llms-full.txt").read_text(encoding="utf-8")
        manquants = [cle for cle in LEVIERS if f"`{cle}`" not in contenu]
        self.assertEqual(manquants, [], f"leviers absents du résumé : {manquants[:5]}")
        manquants = [cle for cle in SCENARIOS if f"`{cle}`" not in contenu]
        self.assertEqual(manquants, [], f"scénarios absents : {manquants}")
        for domaine in DOMAINES:
            self.assertIn(f"`{domaine.cle}`", contenu)
        for classe in CLASSES:
            self.assertIn(f"`{classe}`", contenu)
        # Les comptes annoncés sont ceux du catalogue, pas une photographie.
        self.assertIn(f"{len(LEVIERS)} leviers réglables", contenu)
        self.assertIn(f"{len(DOMAINES)} domaines d'impact", contenu)
        self.assertIn(f"{len(SCENARIOS)} scénarios types", contenu)
        # Deux fois la taille de la page, pas trois : un fichier énorme n'est
        # jamais lu jusqu'au bout par personne.
        self.assertLess(len(contenu), 400_000)

    def test_llms_txt_cite_le_registre_de_prospective(self):
        """Un lecteur automatique doit savoir que l'outil ne prédit pas.

        Ce qu'il ne trouve pas dans ce fichier, il ne le saura pas : la route de
        prospective et sa nature — un **registre de dates**, jamais des
        probabilités — s'écrivent donc là où un assistant les lit.
        """
        contenu = (RACINE / "llms.txt").read_text(encoding="utf-8")
        self.assertIn("RD_PROSPECTIVE.md", contenu)
        self.assertIn("/api/prospective", contenu)
        # Et la négation doit être **là** : un fichier qui ne dit nulle part que
        # l'outil ne calcule pas de probabilités laisse le lecteur automatique
        # supposer l'inverse. Un sabotage l'a montré : retirer la phrase entière
        # ne faisait rougir aucun contrôle, puisque plus aucune ligne ne portait
        # le mot à désamorcer.
        self.assertRegex(contenu.lower(),
                         r"(jamais|aucun\w*|pas)(\s+\S+){0,2}\s+probabilit",
                         "le fichier ne dit nulle part, en clair, que l'outil ne "
                         "calcule pas de probabilités")
        # Le mot « probabilités » est celui qu'il faut désamorcer : il doit être
        # précédé de la négation, sinon la phrase promet une prévision.
        for ligne in contenu.splitlines():
            if "probabilit" in ligne:
                self.assertRegex(ligne.lower(), r"(jamais|aucun\w*|pas)(\s+\S+){0,2}\s+probabilit",
                                 f"une probabilité est annoncée sans être démentie : {ligne}")

    def test_llms_full_porte_la_prospective_engendree(self):
        """Les fenêtres, les horizons et les lacunes : ceux du module, pas d'une copie."""
        from simulateur import prospective as pro

        contenu = (RACINE / "llms-full.txt").read_text(encoding="utf-8")
        jour = date.today()
        registre = pro.registre(jour)
        self.assertIn("Ce que le modèle peut dire d'un avenir daté", contenu)
        for horizon in registre["horizons"]:
            self.assertIn(f"horizon de **{horizon['annees']} ans**", contenu)
            self.assertIn(f"jusqu'au **{horizon['fin']}**", contenu,
                          "la fin d'horizon du fichier doit être recalculée, pas recopiée")
        for fenetre in registre["fenetres"]:
            self.assertIn(fenetre["libelle"], contenu,
                          "une fenêtre du document doit être citée telle quelle")
        self.assertIn("sans fin datée", contenu)
        self.assertIn(pro.resume_des_lacunes(), contenu,
                      "l'état des lacunes publié n'est plus celui du module")
        # Et la négation doit être **là** : un fichier qui ne dit nulle part que
        # l'outil ne calcule pas de probabilités laisse le lecteur automatique
        # supposer l'inverse. Un sabotage l'a montré : retirer la phrase entière
        # ne faisait rougir aucun contrôle, puisque plus aucune ligne ne portait
        # le mot à désamorcer.
        self.assertRegex(contenu.lower(),
                         r"(jamais|aucun\w*|pas)(\s+\S+){0,2}\s+probabilit",
                         "le fichier ne dit nulle part, en clair, que l'outil ne "
                         "calcule pas de probabilités")
        for ligne in contenu.splitlines():
            if "probabilit" in ligne:
                self.assertRegex(ligne.lower(), r"(jamais|aucun\w*|pas)(\s+\S+){0,2}\s+probabilit",
                                 f"une probabilité est annoncée sans être démentie : {ligne}")

    def test_la_section_prospective_est_engendree_et_non_recopiee(self):
        """Deux dates d'engendrement, deux textes : une date en dur serait vue ici.

        Sans ce contrôle, écrire la fin d'horizon du jour dans le générateur
        passerait — le jour de sa rédaction. La section est donc engendrée à deux
        dates éloignées, et l'on refuse qu'elle dise la même chose.
        """
        from datetime import date as _date

        from simulateur import prospective as pro

        lundi = "\n".join(surface._section_prospective(_date(2026, 10, 16)))
        dans_quatre_ans = "\n".join(surface._section_prospective(_date(2030, 10, 16)))
        self.assertNotEqual(lundi, dans_quatre_ans,
                            "la section ne dépend pas du jour : elle est figée")
        for annees, _ in pro.HORIZONS:
            fin = pro.fin_d_horizon(_date(2030, 10, 16), annees).isoformat()
            self.assertIn(f"jusqu'au **{fin}**", dans_quatre_ans,
                          "la fin d'horizon n'est pas celle que le module calcule")
        self.assertIn("2035-10-16", dans_quatre_ans, "l'horizon de cinq ans depuis 2030")

    def test_les_liens_du_depot_existent(self):
        """Un lien mort dans un fichier public est une porte fermée."""
        for nom in ("llms.txt", "llms-full.txt"):
            contenu = (RACINE / nom).read_text(encoding="utf-8")
            liens = re.findall(r"\((https://[^)\s]+)\)", contenu)
            internes = [lien for lien in liens if lien.startswith(surface.DEPOT + "/blob/main/")]
            self.assertTrue(internes, f"{nom} ne renvoie vers aucun document du dépôt")
            for lien in internes:
                chemin = urllib.parse.unquote(lien.split("/blob/main/", 1)[1].split("#")[0])
                with self.subTest(fichier=nom, cible=chemin):
                    self.assertTrue((RACINE / chemin).is_file(), f"{chemin} introuvable")

    def test_le_jeton_de_l_entete_est_remplace_partout(self):
        """Le gabarit porte le jeton, la page publiée n'en porte plus aucun.

        C'est le piège de ce montage : un jeton oublié, et la page part en ligne
        sans description ni adresse canonique — ou, pire, avec l'en-tête caché
        dans un commentaire, ce qui est arrivé pendant l'écriture de ce module.
        """
        from simulateur.interface import HTML_PAGE

        page = PAGE.read_text(encoding="utf-8")
        self.assertEqual(HTML_PAGE.count("===ENTETE_PUBLIQUE==="), 0,
                         "le gabarit doit être résolu au chargement")
        self.assertEqual(page.count("===ENTETE_PUBLIQUE==="), 0)
        self.assertEqual(page.count('rel="canonical"'), 1)
        self.assertEqual(page.count("application/ld+json"), 1)
        # L'en-tête ne doit pas se retrouver *dans* un commentaire : un jeton
        # remplacé au mauvais endroit donne une page parfaitement valide, que
        # personne ne voit et que les moteurs ignorent. On retire donc les
        # commentaires du `<head>` : tout doit encore être là.
        debut = page.index("<title>")
        fin = page.index("<style>", debut)
        sans_commentaires = re.sub(r"<!--.*?-->", "", page[debut:fin], flags=re.S)
        self.assertIn('name="description"', sans_commentaires)
        self.assertIn('rel="canonical"', sans_commentaires)
        self.assertIn("application/ld+json", sans_commentaires)

    def test_les_images_ont_la_taille_annoncee(self):
        for nom, (largeur, hauteur) in IMAGES_PUBLIEES.items():
            with self.subTest(image=nom):
                fichier = RACINE / nom
                self.assertTrue(fichier.is_file(), f"{nom} absent")
                with fichier.open("rb") as flux:
                    entete = flux.read(24)
                self.assertEqual(entete[:8], b"\x89PNG\r\n\x1a\n", f"{nom} n'est pas un PNG")
                self.assertEqual(
                    struct.unpack(">II", entete[16:24]), (largeur, hauteur),
                    f"{nom} n'est pas en {largeur} × {hauteur}",
                )

    def test_les_icones_sont_valides(self):
        icone = (RACINE / "favicon.ico").read_bytes()
        self.assertEqual(icone[:4], b"\x00\x00\x01\x00", "favicon.ico mal formé")
        # Trois tailles dans un seul fichier : 16, 32 et 48 pixels.
        self.assertEqual(struct.unpack_from("<H", icone, 4)[0], 3)
        svg = ElementTree.fromstring((RACINE / "favicon.svg").read_text(encoding="utf-8"))
        self.assertTrue(svg.tag.endswith("svg"))
        self.assertIn("aria-label", (RACINE / "favicon.svg").read_text(encoding="utf-8"))

    def test_aucune_image_ne_depend_de_pillow_a_l_execution(self):
        """Les images sont écrites à la main **et** versionnées.

        Le module qui les sert ne doit importer ni Pillow ni quoi que ce soit
        d'autre : un hébergeur qui n'a installé que le strict nécessaire doit
        pouvoir servir l'icône.
        """
        source = (RACINE / "simulateur" / "surface_publique.py").read_text(encoding="utf-8")
        for interdit in ("PIL", "requests", "urllib.request"):
            self.assertNotIn(interdit, source)


class TestRoutesDuServeur(unittest.TestCase):
    """Ce que le serveur Python (Render, poste local) répond réellement."""

    @classmethod
    def setUpClass(cls):
        from simulateur.dashboard import create_server

        bouche = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        bouche.bind(("127.0.0.1", 0))
        cls.port = bouche.getsockname()[1]
        bouche.close()
        cls.serveur = create_server("127.0.0.1", cls.port)
        cls.fil = threading.Thread(target=cls.serveur.serve_forever, daemon=True)
        cls.fil.start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        cls.serveur.server_close()

    def demander(self, chemin: str, methode: str = "GET"):
        demande = urllib.request.Request(
            f"http://127.0.0.1:{self.__class__.port}{chemin}", method=methode
        )
        with urllib.request.urlopen(demande, timeout=30) as reponse:
            return reponse.status, dict(reponse.headers), reponse.read()

    def test_les_fichiers_pour_robots_sont_servis(self):
        for nom, chemin in FICHIERS_PUBLIES.items():
            with self.subTest(fichier=nom):
                statut, entetes, corps = self.demander(chemin)
                self.assertEqual(statut, 200)
                self.assertEqual(entetes.get("Content-Type"), surface.TEXTES[chemin])
                self.assertEqual(corps.decode("utf-8"), surface.texte(chemin))
                self.assertIn("max-age=", entetes.get("Cache-Control", ""))

    def test_les_images_publiques_sont_servies(self):
        for chemin, type_mime in surface.IMAGES.items():
            with self.subTest(image=chemin):
                statut, entetes, corps = self.demander(chemin)
                self.assertEqual(statut, 200)
                self.assertEqual(entetes.get("Content-Type"), type_mime)
                self.assertEqual(corps, (RACINE / chemin.lstrip("/")).read_bytes())

    def test_une_requete_de_tete_ne_renvoie_pas_de_corps(self):
        statut, entetes, corps = self.demander("/robots.txt", methode="HEAD")
        self.assertEqual(statut, 200)
        self.assertEqual(corps, b"")
        self.assertGreater(int(entetes["Content-Length"]), 100)

    def test_un_chemin_d_image_hors_liste_est_refuse(self):
        with self.assertRaises(urllib.error.HTTPError) as capture:
            self.demander("/../simulateur/dashboard.py")
        self.assertIn(capture.exception.code, (400, 404))

    def test_l_api_repond_toujours(self):
        """Les nouvelles routes ne doivent pas avoir mangé les anciennes."""
        statut, _, corps = self.demander("/api/lexique")
        self.assertEqual(statut, 200)
        self.assertIn("termes", json.loads(corps.decode("utf-8")))


class TestAdresseCanoniqueSurchargeable(unittest.TestCase):
    """Un miroir doit pouvoir dire qu'il est la page — sans dupliquer le module.

    La même page est servie par plusieurs hébergeurs : tant que tous déclarent
    la même adresse canonique, c'est celle-là qui est indexée. Mais un domaine
    propre, une préproduction ou un miroir peut vouloir être indexé pour lui-
    même : `SIMULATEUR_URL_CANONIQUE` le lui permet. Une valeur fausse, elle,
    arrête la construction **avec un message** : une adresse canonique erronée
    ne se voit pas à l'écran, elle se voit des semaines plus tard dans les
    résultats de recherche.
    """

    CODE = "import simulateur.surface_publique as s; print(s.URL_CANONIQUE)"

    def lancer(self, valeur: str | None = None) -> tuple[int, str]:
        import os

        environ = dict(os.environ)
        environ.pop("SIMULATEUR_URL_CANONIQUE", None)
        if valeur is not None:
            environ["SIMULATEUR_URL_CANONIQUE"] = valeur
        resultat = subprocess.run(
            [sys.executable, "-c", self.CODE],
            cwd=RACINE, capture_output=True, text=True, env=environ, timeout=120,
        )
        sortie = (resultat.stdout or resultat.stderr).strip().splitlines()
        return resultat.returncode, sortie[-1] if sortie else ""

    def test_sans_variable_l_adresse_par_defaut_fait_foi(self):
        code, sortie = self.lancer()
        self.assertEqual(code, 0, sortie)
        self.assertEqual(sortie, surface.URL_CANONIQUE_PAR_DEFAUT)

    def test_une_adresse_valide_est_reprise_avec_sa_barre_finale(self):
        for valeur in ("https://exemple.fr/outil", "https://exemple.fr/outil/"):
            with self.subTest(valeur=valeur):
                code, sortie = self.lancer(valeur)
                self.assertEqual(code, 0, sortie)
                self.assertEqual(sortie, "https://exemple.fr/outil/")

    def test_une_adresse_dangereuse_est_refusee_bruyamment(self):
        for valeur in ("javascript:alert(1)", "https://ex.fr/a?x=1", "https://ex.fr/a b",
                       "<svg onload=alert(1)>", "/chemin/relatif"):
            with self.subTest(valeur=valeur):
                code, sortie = self.lancer(valeur)
                self.assertNotEqual(code, 0, "une adresse invalide doit arrêter la construction")
                self.assertIn("SIMULATEUR_URL_CANONIQUE", sortie)

    def test_la_surcharge_change_le_plan_et_les_regles(self):
        """Le plan, les règles et le résumé suivent l'adresse — pas seulement l'en-tête."""
        import os

        environ = dict(os.environ)
        environ["SIMULATEUR_URL_CANONIQUE"] = "https://exemple.fr/outil/"
        code = (
            "from simulateur import surface_publique as s;"
            "print(s.URL_CANONIQUE);print(s.robots_txt().splitlines()[-3]);"
            "print(s.sitemap_xml().split('<loc>')[1].split('</loc>')[0]);"
            "print(s.llms_txt().count('https://exemple.fr/outil/'))"
        )
        resultat = subprocess.run([sys.executable, "-c", code], cwd=RACINE,
                                  capture_output=True, text=True, env=environ, timeout=120)
        self.assertEqual(resultat.returncode, 0, resultat.stderr)
        lignes = resultat.stdout.strip().splitlines()
        self.assertEqual(lignes[0], "https://exemple.fr/outil/")
        self.assertIn("exemple.fr/outil/sitemap.xml", lignes[1])
        self.assertEqual(lignes[2], "https://exemple.fr/outil/")
        self.assertGreater(int(lignes[3]), 1)


class TestCoherenceAvecLeSite(unittest.TestCase):
    """La copie publiée par le site M.R.S.C vit dans un sous-dossier."""

    def test_aucune_ressource_de_la_page_ne_depend_d_un_hote(self):
        """Rien de ce qui se charge ne pointe vers un autre hôte."""
        entete = entete_html()
        for balise in re.findall(r"<link\b[^>]*>", entete):
            with self.subTest(balise=balise[:60]):
                self.assertTrue('rel="canonical"' in balise or "data:" in balise)
        # L'aperçu de partage, lui, est **absolu** : c'est une adresse annoncée
        # aux robots, pas un fichier chargé par la page — le robot qui lit la
        # page ne cherche pas les autres fichiers sur le même hôte que la page.
        self.assertIn(f'content="{surface.URL_CANONIQUE}{surface.IMAGE_APERCU}"', entete)

    def test_le_module_ne_charge_rien_au_dela_de_la_bibliotheque_standard(self):
        """`surface_publique` est importé par le serveur : il doit rester léger."""
        source = (RACINE / "simulateur" / "surface_publique.py").read_text(encoding="utf-8")
        importés = set(re.findall(r"^import (\w+)|^from (\w+)", source, re.M))
        paquets = {paquet for paire in importés for paquet in paire if paquet}
        self.assertTrue(paquets <= {"__future__", "json", "functools", "pathlib", "typing", "simulateur"},
                        f"imports inattendus : {sorted(paquets)}")


if __name__ == "__main__":
    unittest.main()
