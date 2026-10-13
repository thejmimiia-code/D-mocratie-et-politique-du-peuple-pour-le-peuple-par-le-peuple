"""Le bloc « About » du dépôt : ce qu'il recommande, et ce qu'il vérifie.

`outils/details_depot.py` produit le bloc à coller dans *Edit repository
details* — description, site web, sujets, aperçu social — et tente de
l'appliquer par l'API. Ces réglages ne sont pas versionnés : c'est le seul
endroit du projet où le texte vit dans GitHub, pas dans un fichier. D'où deux
contrôles qui comptent plus qu'ils n'en ont l'air :

* **l'adresse du site web ne peut pas vieillir à part** de celle que la page
  déclare aux moteurs : elle est lue dans `surface_publique`. Le conseil
  précédent demandait de vider ce champ au motif que l'adresse renverrait 404 ;
  c'était vrai un jour, et c'était devenu faux sans que rien ne le signale ;
* **la question est posée, pas supposée** : `adresse_repond()` interroge
  l'adresse, et dit « je n'ai pas pu vérifier » quand le réseau manque — jamais
  « c'est mort » à la place.

Aucun accès réseau ici : la sonde reçoit son ouvreur en paramètre, et les
contrôles lui donnent une réponse connue.
"""

from __future__ import annotations

import contextlib
import io
import re
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

NODE = __import__("shutil").which("node")   # même convention que test_interface_navigateur

from outils.chargement_module import charger_module  # noqa: E402
from simulateur import surface_publique as surface  # noqa: E402


def charger_outil() -> object:
    """Relit le script à chaque fois — jamais depuis un cache de bytecode.

    C'est ce test qui a mis le piège au jour : le chargeur d'origine servait un
    `.pyc` quand la source changeait de même longueur dans la même seconde, et
    un sabotage restauré continuait alors d'agir. Voir `outils/chargement_module.py`.
    """
    return charger_module("details_depot", RACINE / "outils" / "details_depot.py")


class FausseReponse:
    """Le minimum qu'un `urlopen` doit rendre : un statut et un contexte."""

    def __init__(self, statut: int) -> None:
        self.status = statut

    def __enter__(self) -> FausseReponse:
        return self

    def __exit__(self, *_arguments: object) -> bool:
        return False


def ouvreur(statut: int = 200, defaut: Exception | None = None):
    def ouvrir(url: str, timeout: float = 5.0) -> FausseReponse:
        if defaut is not None:
            raise defaut
        return FausseReponse(statut)
    return ouvrir


class TestAdresseDuSiteWeb(unittest.TestCase):
    """L'adresse publiée est une source unique, pas une phrase recopiée."""

    @classmethod
    def setUpClass(cls):
        cls.outil = charger_outil()

    def test_l_adresse_vient_de_la_surface_publique(self):
        self.assertEqual(self.outil.SITE_WEB, surface.URL_CANONIQUE_PAR_DEFAUT.rstrip("/"),
                         "l'adresse du dépôt doit être celle que la page déclare aux moteurs")

    def test_l_adresse_est_unique_dans_le_module(self):
        source = (RACINE / "outils" / "details_depot.py").read_text(encoding="utf-8")
        self.assertEqual(source.count("d-mocratie-et-politique-du-peuple-p.vercel.app"), 0,
                         "l'adresse est écrite en dur : elle vieillirait à part de la page")

    def test_la_documentation_reste_le_repli(self):
        attendu = (f"https://github.com/{self.outil.DEPOT}/blob/main/"
                   "docs/SIMULATEUR_PARAMETRABLE.md")
        self.assertEqual(self.outil.SITE_WEB_CONSEIL, attendu,
                         "un lien de repli tronqué ne mène nulle part")


class TestSondeDeLAdresse(unittest.TestCase):
    """Répond, ne répond pas, ou « je ne sais pas » : trois réponses distinctes."""

    @classmethod
    def setUpClass(cls):
        cls.outil = charger_outil()

    def test_une_adresse_qui_repond_est_vraie(self):
        self.assertTrue(self.outil.adresse_repond("https://exemple.fr", ouvrir=ouvreur(200)))

    def test_un_404_est_faux(self):
        self.assertFalse(self.outil.adresse_repond("https://exemple.fr", ouvrir=ouvreur(404)))

    def test_un_404_leve_est_faux_aussi(self):
        """`urlopen` lève sur un 404 ; la sonde ne doit pas confondre avec une panne."""
        self.assertFalse(self.outil.adresse_repond(
            "https://exemple.fr",
            ouvrir=ouvreur(defaut=urllib.error.HTTPError("u", 404, "introuvable", None, None))))

    def test_un_reseau_absent_dit_je_ne_sais_pas(self):
        self.assertIsNone(self.outil.adresse_repond(
            "https://exemple.fr",
            ouvrir=ouvreur(defaut=urllib.error.URLError("hors ligne"))))

    def test_une_adresse_vide_ne_se_sonde_pas(self):
        self.assertIsNone(self.outil.adresse_repond(""))


class TestBlocACopier(unittest.TestCase):
    """Le bloc dit ce qui a été constaté, et rien de plus."""

    @classmethod
    def setUpClass(cls):
        cls.outil = charger_outil()
        cls.vivante = cls.outil.bloc_a_copier(True)
        cls.morte = cls.outil.bloc_a_copier(False)
        cls.inconnue = cls.outil.bloc_a_copier(None)

    def test_l_adresse_vivante_est_recommandee_telle_quelle(self):
        self.assertIn(self.outil.SITE_WEB, self.vivante)
        self.assertIn("l'application répond", self.vivante)
        self.assertNotIn("(vide", self.vivante,
                         "on ne vide pas un champ qui mène à une application joignable")

    def test_une_adresse_morte_renvoie_vers_la_documentation(self):
        self.assertIn("ne répond pas", self.morte)
        self.assertIn(self.outil.SITE_WEB_CONSEIL, self.morte)
        self.assertIn("(vide", self.morte)

    def test_une_adresse_non_verifiee_est_recommandee_et_dite_telle(self):
        """Se taire serait le pire : le champ resterait vide sans raison."""
        self.assertIn(self.outil.SITE_WEB, self.inconnue)
        self.assertIn("n'a pas pu être vérifiée", self.inconnue)
        self.assertNotIn("(vide", self.inconnue)

    def test_le_bloc_rappelle_ce_que_les_robots_lisent(self):
        for chemin in ("robots.txt", "sitemap.xml", "llms.txt", "llms-full.txt"):
            with self.subTest(chemin=chemin):
                self.assertIn(chemin, self.vivante)

    def test_le_bloc_tient_dans_les_limites_de_github(self):
        self.assertLessEqual(len(self.outil.DESCRIPTION), 350)
        self.assertLessEqual(len(self.outil.SUJETS), 20)
        self.assertEqual(len(set(self.outil.SUJETS)), len(self.outil.SUJETS),
                         "un sujet en double en écraserait un autre")
        self.assertEqual(len(self.outil.DESCRIPTION), len(self.outil.DESCRIPTION.strip()))


class TestEtatDuDepot(unittest.TestCase):
    """« Déjà à jour » est un jugement : il porte aussi sur le champ Website."""

    def executer(self, etat: dict) -> str:
        outil = charger_outil()
        outil.etat_actuel = lambda: etat
        with contextlib.redirect_stdout(io.StringIO()) as sortie:
            outil.sys.argv = ["details_depot.py", "--sans-reseau"]
            outil.main()
        return sortie.getvalue()

    def etat(self, **remplacements: object) -> dict:
        etat = {"description": self.outil_ref.DESCRIPTION,
                "homepage": self.outil_ref.SITE_WEB,
                "topics": list(self.outil_ref.SUJETS)}
        etat.update(remplacements)
        return etat

    @property
    def outil_ref(self):
        if not hasattr(self, "_outil_ref"):
            self._outil_ref = charger_outil()
        return self._outil_ref

    def test_un_depot_complet_est_dit_a_jour(self):
        self.assertIn("Déjà à jour", self.executer(self.etat()))

    def test_un_champ_website_vide_n_est_pas_a_jour(self):
        """Le vrai piège : sans cette comparaison, l'outil se tairait un jour de trop."""
        sortie = self.executer(self.etat(homepage=""))
        self.assertNotIn("Déjà à jour", sortie)
        self.assertIn(self.outil_ref.SITE_WEB, sortie)

    def test_un_champ_website_avec_barre_finale_est_a_jour(self):
        self.assertIn("Déjà à jour", self.executer(self.etat(homepage=self.outil_ref.SITE_WEB + "/")))

    def test_une_description_differente_n_est_pas_a_jour(self):
        self.assertNotIn("Déjà à jour", self.executer(self.etat(description="autre chose")))


class TestCeQuiResteAPoser(unittest.TestCase):
    """`manques()` : la liste des champs non posés, déduite de l'état lu.

    Trois documents racontaient ce qui restait à faire, chacun à sa façon — et
    aucun ne pouvait savoir si c'était encore vrai. L'outil le calcule
    maintenant à chaque exécution ; ces contrôles vérifient qu'il le fait dans
    l'ordre de la fenêtre GitHub, et qu'il n'oublie pas l'aperçu social, qui est
    le seul champ qu'aucune API ne pose.
    """

    @classmethod
    def setUpClass(cls):
        cls.outil = charger_outil()

    def etat(self, **remplacements: object) -> dict:
        etat = {"description": self.outil.DESCRIPTION,
                "homepage": self.outil.SITE_WEB,
                "topics": list(self.outil.SUJETS)}
        etat.update(remplacements)
        return etat

    def test_un_depot_complet_ne_laisse_que_l_apercu_social(self):
        reste = self.outil.manques(self.etat())
        self.assertEqual(len(reste), 1, reste)
        self.assertIn("aperçu social", reste[0])
        self.assertIn("à la main", reste[0])

    def test_les_sujets_vides_sont_nommes(self):
        reste = self.outil.manques(self.etat(topics=[]))
        self.assertTrue(any("sujets" in manque for manque in reste), reste)
        self.assertIn("20", " ".join(reste), "le compte attendu doit être dit")

    def test_un_seul_sujet_manquant_suffit_a_signaler_la_liste(self):
        incomplets = list(self.outil.SUJETS)[:-1]
        self.assertTrue(any("sujets" in manque for manque in self.outil.manques(self.etat(topics=incomplets))))

    def test_l_ordre_est_celui_de_la_fenetre(self):
        """La liste suit la fenêtre GitHub : description, site web, sujets, aperçu."""
        reste = self.outil.manques(self.etat(topics=[], description="autre chose", homepage=""))
        self.assertIn("description", reste[0])
        self.assertIn("site web", reste[1])
        self.assertTrue(any("sujets" in manque for manque in reste[2:]), reste)
        self.assertIn("aperçu social", reste[-1])

    def test_un_etat_illisible_est_dit_tel_quel(self):
        reste = self.outil.manques(None)
        self.assertEqual(len(reste), 1, reste)
        self.assertIn("pas pu être lu", reste[0])

    def test_le_rapport_affiche_la_liste(self):
        outil = charger_outil()
        outil.etat_actuel = lambda: self.etat(topics=[])
        with contextlib.redirect_stdout(io.StringIO()) as sortie:
            outil.sys.argv = ["details_depot.py", "--sans-reseau"]
            outil.main()
        self.assertIn("reste à poser", sortie.getvalue())
        self.assertIn("sujets", sortie.getvalue())


class TestLeDocumentDesReglages(unittest.TestCase):
    """`docs/REPOSITORY_DETAILS.md` recopie des valeurs : qu'elles soient justes.

    Ce document est la référence des champs non versionnés du dépôt. Recopiées à
    la main, ses valeurs ont dérivé trois fois : compte de caractères annoncé
    faux d'une unité, empreinte de l'aperçu social étrangère au fichier versionné
    (elle désignait une image plus ancienne), taille arrondie au kilo-octet
    supérieur. Un document qui donne l'empreinte d'une autre image fait
    téléverser autre chose que ce qu'il décrit — sans que rien ne le signale.

    D'où les régions engendrées, et ces contrôles : la valeur juste **et** une
    seule fois, une valeur périmée refusée, et une réécriture qui répare sans
    toucher à la prose.
    """

    @classmethod
    def setUpClass(cls):
        cls.outil = charger_outil()
        cls.document = RACINE / "docs" / "REPOSITORY_DETAILS.md"
        cls.texte = cls.document.read_text(encoding="utf-8")

    def copie(self, texte: str) -> Path:
        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        chemin = Path(dossier.name) / "REPOSITORY_DETAILS.md"
        chemin.write_text(texte, encoding="utf-8")
        return chemin

    def test_les_regions_engendrees_sont_a_jour(self):
        self.assertEqual(self.outil.verifier_document(), [],
                         "le document annonce une valeur périmée — lancer `--doc`")

    def test_l_empreinte_du_document_est_celle_du_fichier_versionne(self):
        import base64
        import hashlib

        octets = (RACINE / "docs" / "apercu_social.png").read_bytes()
        empreinte = hashlib.sha256(octets).digest()
        for description, valeur in (("hexadécimale", empreinte.hex()),
                                    ("base64", "SHA256:" + base64.b64encode(empreinte).decode()),
                                    ("le nombre d'octets", str(len(octets)))):
            with self.subTest(valeur=description):
                self.assertIn(valeur, self.texte,
                              f"l'empreinte {description} du document n'est pas celle du fichier")

    def test_la_description_et_son_compte_sont_ceux_de_l_outil(self):
        self.assertIn(self.outil.DESCRIPTION, self.texte)
        self.assertIn(f"## 1. Description ({len(self.outil.DESCRIPTION)} / 350 caractères)", self.texte)

    def test_les_sujets_sont_ceux_de_l_outil(self):
        for sujet in self.outil.SUJETS:
            with self.subTest(sujet=sujet):
                self.assertIn(sujet, self.texte)
        self.assertIn(f"## 3. Sujets ({len(self.outil.SUJETS)} / 20)", self.texte)

    #: « 13 octobre 2026 » en tête du § 0 — le reste du titre est libre.
    DATE_ETAT = re.compile(r"^## 0\. État constaté \((\d{1,2} [a-zéûîôàç]+ 20\d{2})", re.M)

    def date_de_l_etat(self) -> str:
        bloc = self.DATE_ETAT.search(self.texte)
        self.assertIsNotNone(bloc, "le § 0 « État constaté » a disparu de la référence")
        return bloc.group(1)

    def test_l_etat_constate_porte_une_date(self):
        """Un état sans date ne peut pas vieillir : il reste faux pour toujours.

        C'est la leçon des deux documents qui annonçaient encore, au présent, une
        description « 4 échelons » et une adresse morte. Une affirmation datée
        se juge ; une affirmation sans date se croit.
        """
        mois = ("janvier|février|mars|avril|mai|juin|juillet|août|septembre|"
                "octobre|novembre|décembre")
        self.assertRegex(self.date_de_l_etat(), rf"^\d{{1,2}} ({mois}) 20\d{{2}}$",
                         "la date doit être écrite en toutes lettres (jour, mois, année)")

    def test_la_date_de_l_etat_n_est_pas_dans_l_avenir(self):
        import datetime

        jour, mois, annee = self.date_de_l_etat().split()
        mois_numero = ("janvier février mars avril mai juin juillet août septembre "
                       "octobre novembre décembre").split().index(mois) + 1
        date = datetime.date(int(annee), mois_numero, int(jour))
        self.assertLessEqual(date, datetime.date.today(),
                             "un état constaté ne peut pas être daté dans l'avenir")

    def test_le_document_et_l_outil_s_accordent_sur_ce_qui_reste(self):
        """Les deux endroits qui disent « ce qui reste » nomment les mêmes champs."""
        reste = charger_outil().manques({"description": self.outil.DESCRIPTION,
                                         "homepage": self.outil.SITE_WEB, "topics": []})
        for manque in reste:
            mot = "Topics" if "sujets" in manque else "aperçu social"
            with self.subTest(manque=manque):
                self.assertIn(mot, self.texte,
                              f"le document ne dit rien de « {mot} », que l'outil signale")

    def test_l_adresse_publiee_est_au_document(self):
        self.assertIn(self.outil.SITE_WEB, self.texte)
        self.assertIn("**Website** : coller l'adresse de l'application",
                      self.texte, "le pas à pas doit renvoyer vers la région engendrée")

    def test_aucune_valeur_engendree_n_est_recopiee(self):
        """Recopier une valeur à la main, c'est la laisser vieillir toute seule."""
        for valeur in (self.outil.DESCRIPTION, ", ".join(self.outil.SUJETS)):
            with self.subTest(valeur=valeur[:40]):
                self.assertEqual(self.texte.count(valeur), 1,
                                 "cette valeur doit apparaître une fois : elle est engendrée")

    def test_une_valeur_perimee_est_refusee(self):
        perime = self.texte.replace(self.outil._empreinte_image()[1], "0" * 64, 1)
        anomalies = self.outil.verifier_document(self.copie(perime))
        self.assertEqual(len(anomalies), 1, anomalies)
        self.assertIn("apercu", anomalies[0])

    def test_des_marques_absentes_sont_refusees(self):
        sans = self.texte.replace("<!-- engendre:site-web -->", "", 1)
        anomalies = self.outil.verifier_document(self.copie(sans))
        self.assertEqual(len(anomalies), 1, anomalies)
        self.assertIn("marques absentes", anomalies[0])

    def test_la_reecriture_repare_sans_toucher_a_la_prose(self):
        chemin = self.copie(self.texte.replace("52 171", "12 345", 1)
                            .replace("51 Kio", "9 Kio", 1)
                            .replace(self.outil._empreinte_image()[1], "0" * 64, 1))
        self.assertTrue(self.outil.verifier_document(chemin), "la copie sabotée doit être refusée")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.outil.reecrire_document(chemin), 0)
        self.assertEqual(self.outil.verifier_document(chemin), [])
        reecrit = chemin.read_text(encoding="utf-8")
        self.assertIn("**Pourquoi ce changement.**", reecrit, "la prose doit survivre à la réécriture")
        self.assertIn("## 5. Autres cases de la même page", reecrit)

    def test_un_document_absent_est_signale(self):
        anomalies = self.outil.verifier_document(Path("/tmp/ne-existe-pas/absent.md"))
        self.assertEqual(len(anomalies), 1)
        self.assertIn("absent", anomalies[0])


class TestLaPageDeReglages(unittest.TestCase):
    """`outils/reglages_depot.html` applique les réglages : qu'elle dise la même chose.

    Cette page n'avait aucun contrôle, et elle portait pourtant la valeur la plus
    coûteuse du dépôt : son champ « Adresse du site » partait **vide**, sous un
    libellé qui conseillait de le laisser vide (« l'ancienne adresse Vercel
    renvoie 404 »). Cliquer sur *Appliquer au dépôt* effaçait donc le lien vers
    l'application — exactement ce qu'un formulaire de réglages ne doit pas faire.
    """

    @classmethod
    def setUpClass(cls):
        cls.outil = charger_outil()
        cls.chemin = RACINE / "outils" / "reglages_depot.html"
        cls.page = cls.chemin.read_text(encoding="utf-8")

    def test_la_description_du_formulaire_est_celle_de_l_outil(self):
        bloc = re.search(r'<textarea id="description">(.*?)</textarea>', self.page, re.S)
        self.assertIsNotNone(bloc, "le champ description a disparu de la page")
        self.assertEqual(bloc.group(1).strip(), self.outil.DESCRIPTION)
        self.assertIn("`${description.length} / 350 caractères`", self.page,
                      "le compte doit se calculer sur le champ, jamais être recopié")

    def test_les_sujets_du_formulaire_sont_ceux_de_l_outil(self):
        bloc = re.search(r"const SUJETS = \[(.*?)\];", self.page, re.S)
        self.assertIsNotNone(bloc, "la liste des sujets a disparu de la page")
        self.assertEqual(re.findall(r"'([^']+)'", bloc.group(1)), self.outil.SUJETS)

    def test_le_depot_vise_est_le_bon(self):
        bloc = re.search(r"const DEPOT = '([^']+)';", self.page)
        self.assertIsNotNone(bloc)
        self.assertEqual(bloc.group(1), self.outil.DEPOT)

    def test_l_adresse_du_site_est_pre_remplie(self):
        bloc = re.search(r'<input id="site"[^>]*value="([^"]+)"', self.page)
        self.assertIsNotNone(bloc, "le champ du site web n'est pas pré-rempli")
        self.assertEqual(bloc.group(1), self.outil.SITE_WEB)

    def test_le_lien_de_documentation_de_la_page_vise_le_bon_depot(self):
        attendu = (f"https://github.com/{self.outil.DEPOT}/blob/main/"
                   "docs/SIMULATEUR_PARAMETRABLE.md")
        self.assertIn(attendu, self.page)

    def test_la_page_ne_propose_plus_de_vider_le_champ(self):
        self.assertNotIn("laisser vide", self.page,
                         "le champ ne doit plus être présenté comme à vider")

    def test_la_page_n_annonce_aucune_taille_d_image(self):
        """Une taille recopiée vieillit : l'aperçu social a été régénéré depuis."""
        self.assertNotIn("Kio", self.page,
                         "renvoyer au fichier, sans en annoncer la taille (voir --doc)")

    @unittest.skipIf(NODE is None, "node absent : le contrôle de syntaxe est sauté")
    def test_le_script_de_la_page_est_valide(self):
        for numero, bloc in enumerate(re.findall(r"<script>(.*?)</script>", self.page, re.S)):
            with self.subTest(bloc=numero):
                with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                                 encoding="utf-8") as fichier:
                    fichier.write(bloc)
                    chemin = fichier.name
                self.addCleanup(Path(chemin).unlink)
                resultat = subprocess.run([NODE, "--check", chemin], capture_output=True, text=True)
                self.assertEqual(resultat.returncode, 0,
                                 f"JavaScript invalide :\n{resultat.stderr}")


class TestLesComptesAnnoncesDansLesDocuments(unittest.TestCase):
    """Le compte de caractères annoncé : le même partout, et le bon.

    Il a été faux (270 pour 271) dans deux documents, dont celui qui sert de
    référence. Un écart d'une unité ne se voit pas à la lecture : il se contrôle.
    """

    #: Les documents qui annoncent le compte. La page de réglages en est absente :
    #: elle l'affiche par calcul, donc elle ne peut pas se tromper.
    DOCUMENTS = ("README.md", "CONTRIBUTING.md", "NOTE_POUR_CLAUDE.md",
                 "docs/REPOSITORY_DETAILS.md")

    def test_le_compte_de_la_description_est_le_meme_partout(self):
        outil = charger_outil()
        annonces = 0
        for nom in self.DOCUMENTS:
            chemin = RACINE / nom
            if not chemin.is_file():
                continue
            for ligne, texte in enumerate(chemin.read_text(encoding="utf-8").splitlines(), 1):
                for nombre in re.findall(r"(\d{2,3})\s*/\s*350", texte):
                    annonces += 1
                    with self.subTest(document=nom, ligne=ligne):
                        self.assertEqual(int(nombre), len(outil.DESCRIPTION),
                                         f"{nom}:{ligne} annonce un compte faux")
        self.assertGreater(annonces, 0, "aucun document n'annonce plus le compte : "
                                        "ce contrôle ne mesure alors plus rien")


if __name__ == "__main__":
    unittest.main()
