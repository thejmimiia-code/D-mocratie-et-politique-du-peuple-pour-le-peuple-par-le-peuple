"""La licence du dépôt : une seule source, et elle est **lue**.

Ce fichier existe à cause d'une erreur réelle, publiée. Le nom de la licence
était recopié dans `simulateur/surface_publique.py` (`LICENCE = "MIT"`), sous un
commentaire qui parlait encore de MIT. Le dépôt, lui, est sous **GPL-3.0** depuis
longtemps : son fichier `LICENSE`, le classificateur de `pyproject.toml`,
`package.json` et la section « Licence » du `README.md` le disent tous.

Résultat : trois fichiers **servis en ligne** annonçaient « licence MIT » à des
moteurs de recherche et à des lecteurs automatiques — `robots.txt`, `llms.txt`
et `llms-full.txt` —, et deux documents de R&D le répétaient. Une licence fausse
n'est pas une coquille : c'est une affirmation juridique, et celle-ci était
fausse **sur ce que publie le dépôt**.

D'où trois règles, et les contrôles qui les tiennent :

1. **le nom est lu, jamais recopié** — `licence_du_depot()` reconnaît ce que dit
   le fichier `LICENSE`, et rend `""` (un renvoi au fichier) plutôt qu'un nom
   deviné ;
2. **toutes les déclarations disent la même chose** — fichier, `pyproject.toml`,
   `package.json`, `README.md`, textes publiés, fichiers statiques de la racine ;
3. **aucun texte publié ne nomme une autre licence** — c'est le contrôle qui
   aurait attrapé l'erreur, et c'est celui que les sabotages éprouvent.
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from simulateur import surface_publique as surface  # noqa: E402

#: Les noms de licence logicielle qu'un texte du dépôt ne doit pas attribuer au
#: projet. Les licences de **données** (CC-BY-4.0, Licence Ouverte, Eurostat,
#: BCE, et la bibliothèque Frankfurter) sont hors liste : elles décrivent une
#: source ou un outil tiers, pas ce dépôt, et il est normal qu'elles diffèrent.
#: Les noms capitalisés d'ailleurs (l'université MIT) ne sont pas non plus des
#: attributions : c'est la phrase qui les porte qui compte, et elle ne parle pas
#: de licence.
NOMS_SURVEILLES = ("MIT", "Apache-2.0", "BSD-3-Clause", "GPL-2.0", "GPL-3.0",
                   "AGPL-3.0", "LGPL-3.0", "GPLv2", "GPLv3")

#: Ce que chaque nom du dépôt **désigne** : deux écritures d'une même licence ne
#: sont pas un désaccord. « GPLv3 » et « GPL-3.0 » disent la même chose ; elles
#: ne sont donc jamais signalées l'une contre l'autre.
DESIGNATION = {"GPL-3.0": "GPL-3.0", "GPLv3": "GPL-3.0", "GPL-2.0": "GPL-2.0",
               "GPLv2": "GPL-2.0", "MIT": "MIT", "Apache-2.0": "Apache-2.0",
               "BSD-3-Clause": "BSD-3-Clause", "AGPL-3.0": "AGPL-3.0",
               "LGPL-3.0": "LGPL-3.0"}

#: « licence X », « licence : X », « "licence": "X" », « sous licence X ».
ATTRIBUTION = re.compile(r"licence\s*\"?\s*:?\s*[`«\"']?\s*(" + "|".join(NOMS_SURVEILLES) + r")\b")

#: Marqueur de citation : une ligne qui **raconte** une erreur de licence — un
#: journal des modifications, une page de R&D — porte ce commentaire HTML en fin
#: de ligne. Il est invisible à la lecture et le balayage le voit. Le contrôle
#: central mesure donc la **déclaration**, pas la citation : sans ce marqueur, le
#: CHANGELOG ne pourrait plus dire ce qui a été corrigé.
MARQUEUR_CITATION = "citation historique : licence corrigée"

#: Le marqueur tel qu'il est **posé** : un commentaire HTML, jamais la citation
#: entre accents graves qui l'explique. Sans cette distinction, la phrase des
#: documents qui dit « les lignes qui racontent portent
#: `` `<!-- citation historique : licence corrigée -->` `` » serait elle-même
#: comptée comme un marqueur — et se verrait reprocher de ne rien couvrir.
MARQUEUR_POSE = re.compile(r"(?<!`)<!-- " + re.escape(MARQUEUR_CITATION) + r" -->")

#: Le commentaire tel qu'on l'écrit dans un document.
COMMENTAIRE_CITATION = f"<!-- {MARQUEUR_CITATION} -->"

#: Combien de citations marquées on accepte dans le dépôt. Ce n'est pas une
#: doctrine : c'est un garde-fou contre l'exemption en masse — marquer cent
#: lignes reviendrait à éteindre le contrôle sans le dire. Dépasser ce plafond
#: demande de se demander pourquoi, pas de relever un chiffre.
PLAFOND_CITATIONS = 15


#: Le fichier qui porte ce contrôle : il **construit** des textes de licence pour
#: éprouver la reconnaissance, et il cherche lui-même la phrase fausse. Le
#: balayer serait se demander à soi-même de ne pas citer ce qu'on pourchasse.
#: C'est la seule exemption, et le contrôle vérifie qu'elle reste la seule.
EXEMPTIONS = {"tests/" + Path(__file__).name: "le contrôle lui-même"}

#: Les extensions lues par le balayage : ce qui se publie, se documente ou se
#: configure. Les fichiers de correctif (`livraison-mrsc/*.patch`) sont des
#: diffs d'un autre dépôt : ils ne sont pas lus ici.
EXTENSIONS = (".md", ".py", ".html", ".json", ".toml", ".txt", ".yml", ".yaml")

#: Ce qui n'est pas du texte du dépôt : dépôt Git, caches, dépendances.
DOSSIERS_IGNORES = {".git", "__pycache__", "node_modules", ".venv", "venv", ".ruff_cache"}

TEXTES_DE_LICENCE = {
    "GPL-3.0": ("                    GNU GENERAL PUBLIC LICENSE\n"
                "                       Version 3, 29 June 2007\n"),
    "GPL-2.0": ("                    GNU GENERAL PUBLIC LICENSE\n"
                "                       Version 2, June 1991\n"),
    "AGPL-3.0": ("                    GNU AFFERO GENERAL PUBLIC LICENSE\n"
                 "                       Version 3, 19 November 2007\n"),
    "LGPL-3.0": ("                  GNU LESSER GENERAL PUBLIC LICENSE\n"
                 "                       Version 3, 29 June 2007\n"),
    "Apache-2.0": ("                                 Apache License\n"
                   "                           Version 2.0, January 2004\n"),
    "BSD-3-Clause": "BSD 3-Clause License\n\nCopyright (c) 2026, le dépôt\n",
    "MIT": ("MIT License\n\nCopyright (c) 2026 le dépôt\n\n"
            "Permission is hereby granted, free of charge, to any person obtaining a copy\n"),
}


class AvecUnDepotTemporaire(unittest.TestCase):
    """Un faux dépôt ne contenant qu'un `LICENSE`, pour éprouver la reconnaissance.

    Le dossier temporaire est tenu par le test (`addCleanup`) : le garder dans
    une variable locale d'une fonction le ferait détruire à la sortie de cette
    fonction, et le test lirait un dossier vide — un banc d'essai qui se
    supprime lui-même mesure surtout sa propre disparition.
    """

    def racine_avec(self, texte: str) -> Path:
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        (Path(dossier.name) / "LICENSE").write_text(texte, encoding="utf-8")
        return Path(dossier.name)


class TestReconnaissanceDeLaLicence(AvecUnDepotTemporaire):
    """`licence_du_depot()` : ce que dit le fichier, et rien d'autre."""

    def test_les_licences_courantes_sont_reconnues(self):
        for attendu, texte in TEXTES_DE_LICENCE.items():
            with self.subTest(licence=attendu):
                self.assertEqual(surface.licence_du_depot(self.racine_avec(texte)), attendu)

    def test_l_ordre_compte_pour_les_variantes_de_la_gpl(self):
        """AGPL, LGPL et GPL partagent les mots « GENERAL PUBLIC LICENSE »."""
        for attendu in ("AGPL-3.0", "LGPL-3.0", "GPL-3.0"):
            with self.subTest(licence=attendu):
                self.assertEqual(surface.licence_du_depot(
                    self.racine_avec(TEXTES_DE_LICENCE[attendu])), attendu)

    def test_une_mention_partielle_ne_suffit_pas(self):
        """Sans le mot « GNU », ce n'est pas la GPL : on ne devine pas un nom."""
        racine = self.racine_avec("General Public License\n\nVersion 3\n")
        self.assertEqual(surface.licence_du_depot(racine), "")

    def test_un_texte_inconnu_ne_donne_pas_de_nom(self):
        """On renvoie au fichier : deviner serait refaire l'erreur qu'on répare."""
        racine = self.racine_avec("Licence maison, version 7\nTous droits réservés.\n")
        self.assertEqual(surface.licence_du_depot(racine), "")

    def test_un_fichier_absent_ne_donne_pas_de_nom(self):
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        self.assertEqual(surface.licence_du_depot(Path(dossier.name)), "",
                         "sans fichier, on renvoie au fichier — on ne devine pas")

    def test_le_fichier_du_depot_est_bien_reconnu(self):
        self.assertEqual(surface.LICENCE, surface.licence_du_depot(),
                         "`LICENCE` doit être ce que dit le fichier, pas une copie figée")
        self.assertEqual(surface.LICENCE, "GPL-3.0")

    def test_la_mention_est_une_phrase(self):
        self.assertEqual(surface.mention_licence(), f"licence {surface.LICENCE}")


def fichiers_surveilles(racine: Path = RACINE) -> list[Path]:
    """Les fichiers du dépôt qui peuvent attribuer une licence au projet.

    Fonction plutôt que méthode : les contrôles l'appellent sur un **faux
    dépôt** pour vérifier qu'elle regarde bien partout. Un balayage qu'on ne
    peut pas éprouver ailleurs ne prouve rien ici — la première version de ce
    fichier ne regardait plus que le Markdown et le Python si on le lui
    demandait, et personne ne s'en apercevait.
    """
    fichiers: list[Path] = []
    for chemin in racine.rglob("*"):
        if not chemin.is_file() or chemin.suffix not in EXTENSIONS:
            continue
        relatif = chemin.relative_to(racine)
        if DOSSIERS_IGNORES & set(relatif.parts):
            continue
        if chemin.name == "LICENSE":            # le texte de la licence elle-même
            continue
        if str(relatif) in EXEMPTIONS:
            continue
        if relatif.parts and relatif.parts[0] == "livraison-mrsc":
            continue                            # diffs d'un autre dépôt, non publiés ici
        fichiers.append(chemin)
    return fichiers


def attributions_etrangeres(racine: Path = RACINE) -> list[str]:
    """Les lignes qui **attribuent** au projet une licence autre que la sienne.

    Une ligne qui porte `MARQUEUR_CITATION` est sautée : elle raconte l'erreur au
    lieu de la commettre. Le marqueur est un geste conscient, et son nombre est
    borné par `PLAFOND_CITATIONS`.
    """
    coupables: list[str] = []
    for chemin in fichiers_surveilles(racine):
        texte = chemin.read_text(encoding="utf-8", errors="replace")
        for numero, ligne in enumerate(texte.splitlines(), 1):
            if MARQUEUR_POSE.search(ligne):
                continue
            for nom in ATTRIBUTION.findall(ligne):
                if DESIGNATION[nom] != DESIGNATION.get(surface.LICENCE, surface.LICENCE):
                    coupables.append(f"{chemin.relative_to(racine)}:{numero} → {nom}")
    return coupables


def citations_marquees(racine: Path = RACINE) -> list[str]:
    """Les lignes marquées comme citations historiques, pour les compter."""
    marquees: list[str] = []
    for chemin in fichiers_surveilles(racine):
        texte = chemin.read_text(encoding="utf-8", errors="replace")
        for numero, ligne in enumerate(texte.splitlines(), 1):
            if MARQUEUR_POSE.search(ligne):
                marquees.append(f"{chemin.relative_to(racine)}:{numero}")
    return marquees


class TestToutesLesDeclarationsDisentLaMemeChose(unittest.TestCase):
    """Fichier, `pyproject.toml`, `package.json`, `README.md` : un seul nom."""

    ORDRE_GPL3 = ("GNU GENERAL PUBLIC LICENSE", "VERSION 3")

    def test_le_fichier_license(self):
        texte = (RACINE / "LICENSE").read_text(encoding="utf-8", errors="replace").upper()
        for indice in self.ORDRE_GPL3:
            with self.subTest(indice=indice):
                self.assertIn(indice, texte)

    def test_le_classificateur_de_pyproject(self):
        donnees = tomllib.loads((RACINE / "pyproject.toml").read_text(encoding="utf-8"))
        classificateurs = donnees["project"]["classifiers"]
        licences = [c for c in classificateurs if c.startswith("License ::")]
        self.assertEqual(len(licences), 1, licences)
        self.assertIn("GPLv3", licences[0])

    def test_le_champ_license_de_package_json(self):
        donnees = json.loads((RACINE / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(donnees["license"], surface.LICENCE)

    def test_la_section_licence_du_readme(self):
        texte = (RACINE / "README.md").read_text(encoding="utf-8")
        self.assertIn("GNU General Public License v3.0", texte)
        for trouve in ATTRIBUTION.findall(texte):
            with self.subTest(licence=trouve):
                self.assertEqual(DESIGNATION[trouve], DESIGNATION[surface.LICENCE],
                                 "le README attribue au projet une autre licence")

    def test_le_projet_ne_se_declare_pas_sous_une_autre_licence(self):
        """Le contrôle central : le nom de la licence du dépôt, où qu'il soit écrit."""
        coupables = attributions_etrangeres()
        self.assertEqual(coupables, [],
                         "une autre licence est attribuée au projet : " + " ; ".join(coupables))

    def test_les_citations_historiques_sont_marquees_et_bornees(self):
        """Raconter l'erreur est permis ; éteindre le contrôle ne l'est pas."""
        marquees = citations_marquees()
        self.assertTrue(marquees, "le marqueur n'est utilisé nulle part : "
                                  "soit l'histoire a été réécrite, soit il a été retiré")
        self.assertLessEqual(len(marquees), PLAFOND_CITATIONS,
                             "trop de lignes marquées : l'exemption sert de coupe-circuit — "
                             + ", ".join(marquees))

    def test_le_plafond_reste_un_garde_fou(self):
        """Un plafond à dix mille ne borne rien : il doit rester petit, et suffire."""
        self.assertLessEqual(PLAFOND_CITATIONS, 20,
                             "un plafond haut ne protège plus de l'exemption en masse")
        self.assertGreaterEqual(PLAFOND_CITATIONS, len(citations_marquees()),
                                "le dépôt dépasse son propre plafond : le relever se justifie, "
                                "le contourner non")

    def test_chaque_marqueur_justifie_sa_presence(self):
        """Un marqueur posé sur une ligne qui ne cite rien est un marqueur de trop.

        Sans ce contrôle, marquer large reviendrait à étendre l'exemption sans le
        dire — et un marqueur inutile finirait par passer inaperçu, puis par
        couvrir une vraie déclaration.
        """
        inutiles: list[str] = []
        for chemin in fichiers_surveilles():
            texte = chemin.read_text(encoding="utf-8", errors="replace")
            for numero, ligne in enumerate(texte.splitlines(), 1):
                if MARQUEUR_POSE.search(ligne) and not ATTRIBUTION.search(ligne):
                    inutiles.append(f"{chemin.relative_to(RACINE)}:{numero}")
        self.assertEqual(inutiles, [],
                         "marqueur posé sans citation à couvrir : " + ", ".join(inutiles))

    def test_une_citation_marquee_n_est_plus_signalee(self):
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        racine = Path(dossier.name)
        (racine / "journal.md").write_text(
            f"Le dépôt est sous licence {surface.LICENCE}.\n"
            f"La page annonçait « licence MIT » à tort. {COMMENTAIRE_CITATION}\n",
            encoding="utf-8")
        self.assertEqual(attributions_etrangeres(racine), [],
                         "une citation marquée ne doit pas être signalée")

    def test_le_balayage_regarde_les_fichiers_qui_comptent(self):
        """Un balayage qui ne voit rien ne prouve rien.

        Sans ce contrôle, vider la liste des extensions surveillées — ou sortir
        de la boucle dès la première ligne — rendrait le contrôle central vert
        en ne regardant plus aucun fichier.
        """
        vus = {str(chemin.relative_to(RACINE)) for chemin in fichiers_surveilles()}
        for attendu in ("README.md", "CHANGELOG.md", "pyproject.toml", "package.json",
                        "robots.txt", "llms.txt", "llms-full.txt", "index.html",
                        "simulateur/surface_publique.py", "outils/details_depot.py"):
            with self.subTest(fichier=attendu):
                self.assertIn(attendu, vus)
        self.assertGreater(len(vus), 100, "le balayage a l'air de sauter des fichiers")

    def test_le_balayage_attrape_une_mention_dans_chaque_type_de_fichier(self):
        """Chaque extension surveillée est bien lue — y compris les fichiers servis."""
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        racine = Path(dossier.name)
        for extension in EXTENSIONS:
            (racine / f"exemple{extension}").write_text("Publié sous licence MIT.\n",
                                                        encoding="utf-8")
        rapport = attributions_etrangeres(racine)
        for extension in EXTENSIONS:
            with self.subTest(extension=extension):
                self.assertTrue(any(f"exemple{extension}" in ligne for ligne in rapport),
                                f"un fichier {extension} fautif n'a pas été signalé")

    def test_l_exemption_prevue_ne_s_applique_qu_a_elle(self):
        """Une exemption qui déborde laisserait passer n'importe quoi."""
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        racine = Path(dossier.name)
        (racine / "tests").mkdir()
        exempte = next(iter(EXEMPTIONS))
        (racine / exempte).write_text("licence MIT\n", encoding="utf-8")
        (racine / "tests" / "autre_test.py").write_text("licence MIT\n", encoding="utf-8")
        rapport = attributions_etrangeres(racine)
        self.assertEqual(len(rapport), 1, rapport)
        self.assertIn("autre_test.py", rapport[0])


class TestCeQuiEstPublieAnnonceLaBonneLicence(unittest.TestCase):
    """Les textes servis aux robots, et les fichiers posés à la racine."""

    TEXTES = ("robots.txt", "llms.txt", "llms-full.txt")

    def _textes_publies(self) -> dict[str, str]:
        return {"robots.txt": surface.robots_txt(), "llms.txt": surface.llms_txt(),
                "llms-full.txt": surface.llms_complet(), "page": surface.entete_html()}

    def test_aucun_texte_publie_ne_nomme_une_autre_licence(self):
        for nom, texte in self._textes_publies().items():
            for trouve in ATTRIBUTION.findall(texte):
                with self.subTest(texte=nom, licence=trouve):
                    self.assertEqual(DESIGNATION[trouve], DESIGNATION[surface.LICENCE])

    def test_les_exemptions_sont_minimales_et_vivent_encore(self):
        """Une exemption qui ne sert plus est un trou laissé ouvert."""
        for chemin, raison in EXEMPTIONS.items():
            with self.subTest(chemin=chemin):
                self.assertTrue((RACINE / chemin).is_file(), f"{chemin} a disparu : {raison}")
        self.assertEqual(len(EXEMPTIONS), 1, "chaque exemption doit être justifiée par écrit")

    def test_la_licence_est_annoncee_la_ou_on_l_attend(self):
        textes = self._textes_publies()
        self.assertIn("licence GPL-3.0", textes["robots.txt"])
        self.assertIn(f"licence {surface.LICENCE}", textes["llms.txt"])
        self.assertIn(f"licence {surface.LICENCE}", textes["llms-full.txt"])

    def test_les_fichiers_statiques_de_la_racine_sont_a_jour(self):
        """Ce sont ceux que Vercel sert tels quels : ils doivent dire la même chose."""
        for nom in self.TEXTES:
            chemin = RACINE / nom
            self.assertTrue(chemin.is_file(), f"{nom} a disparu de la racine")
            contenu = chemin.read_text(encoding="utf-8")
            with self.subTest(fichier=nom):
                self.assertNotIn("licence MIT", contenu,
                                 "fichier statique périmé — relancer outils/generer-surface-publique.py")
                self.assertEqual(ATTRIBUTION.findall(contenu), [surface.LICENCE]
                                 if ATTRIBUTION.search(contenu) else [],
                                 f"{nom} n'annonce pas la licence du dépôt")


if __name__ == "__main__":
    unittest.main()
