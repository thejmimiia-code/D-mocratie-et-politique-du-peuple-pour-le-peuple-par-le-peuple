"""tests/test_prospective.py — le croisement des horizons et des fenêtres de veille.

Le module `simulateur/prospective.py` répond à une question simple : « jusqu'où
porte mon horizon, et qu'est-ce qu'il rencontre ? ». Il la répond en **dates**,
jamais en probabilités, et il ne dit rien que les documents du dépôt ne disent
déjà :

* `docs/CONFLITS_RISQUES_SYSTEMIQUES_2026.md` § 7 porte **quatre fenêtres de
  veille** choisies pour organiser la surveillance (« des horizons, pas des dates
  de guerre ») ;
* `docs/AUDIT_LACUNES_GEOPOLITIQUES.md` § 3 porte le **registre des lacunes**
  avec, pour chacune, le critère qui la fermerait ;
* le modèle, lui, simule **cinq ou dix ans**.

Ce fichier tient six promesses :

1. **le croisement est exact en dates** — les quatre fenêtres, aux deux horizons,
   sur une date de référence figée, et chaque marge recomptée à la main ;
2. **une borne imprécise se dit imprécise** — le document date au mois ; quand le
   verdict tient à ce mois, il est annoncé « à un mois près » ;
3. **un 29 février ne casse rien et n'allonge rien** — l'horizon se ferme le 28
   cette année-là, jamais un jour de plus ;
4. **les fenêtres sont citées, pas recopiées** — le module et le document doivent
   porter les mêmes cas, les mêmes scénarios, les mêmes signaux ; et l'audit doit
   porter les mêmes intitulés et les mêmes critères ;
5. **les preuves citées sont lisibles** — chaque fichier cité existe, et le
   symbole cité s'y trouve : une preuve qu'on ne peut pas vérifier n'en est pas une ;
6. **la route et la page tiennent** — `/api/prospective` répond, l'appel serveur
   ne peut pas lâcher, le bloc 7 de l'audit est là, la page suit l'horizon choisi
   et **ne recopie aucune date de fin** (elle affiche celles du serveur) ;
7. **ce que la page écrit est exécuté** — le bloc est construit pour de vrai dans
   Node, avec la réponse réelle de la route : quatre fenêtres, sept lacunes, et
   **aucune cellule insécable de plus de trente signes** (`.audit td.chiffre` ne
   se replie pas : une phrase y serait coupée sur un téléphone). C'est le défaut
   refusé à la passe précédente, et il ne reviendra pas ici sans rougir.
"""

from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from simulateur import prospective as pro  # noqa: E402
from simulateur.interface import HTML_PAGE  # noqa: E402
from simulateur.wsgi import application  # noqa: E402

#: La date de référence des contrôles : le jour où les fenêtres ont été écrites,
#: choisi pour que les marges soient courtes et parlantes (quinze jours entre la
#: troisième fenêtre et la fin de l'horizon de cinq ans).
DEPART = date(2026, 10, 16)

#: Node.js, s'il est là : le bloc de prospective est du JavaScript, et la seule
#: façon de savoir ce qu'il écrit est de l'exécuter.
NODE = shutil.which("node")
DOM_PARTAGE = RACINE / "tests" / "dom_minimal.mjs"

#: Le fragment éprouvé est **celui de la page** : la greffe serait réécrite que
#: c'est la nouvelle version qui serait exécutée ici.
DEBUT_BLOC = "/* Bloc « prospective »"
FIN_BLOC = "async function chargerAudit(){"

#: La règle du dépôt, écrite dans le CSS de l'audit : cette cellule ne se replie
#: pas, donc rien de long ne peut y tenir.
SIGNE_MAXIMUM = 30

#: Les sept lacunes du registre, dans l'ordre du module — priorité, intitulé,
#: statut. Un huitième ajout sans contrôle se verrait ici.
ATTENDU_LACUNES = [
    ("P0", "Cible prédictive non définie", "partiellement_traitee"),
    ("P0", "Aucun jeu historique calibré", "ouverte"),
    ("P0", "Dates de disponibilité et révisions absentes", "partiellement_traitee"),
    ("P0", "Pas de cas négatifs / fréquence de base", "partiellement_traitee"),
    ("P0", "Absence de validation prospective/hors échantillon", "partiellement_traitee"),
    ("P0", "Coûts économiques incomplets", "ouverte"),
    ("P1", "Indice nucléaire non calibré", "refermee"),
]


class TestLeCroisementDesHorizons(unittest.TestCase):
    """Les dates, et rien que les dates — recomptées à la main."""

    def test_les_deux_horizons_finissent_au_meme_jour(self):
        self.assertEqual(pro.fin_d_horizon(DEPART, 5), date(2031, 10, 16))
        self.assertEqual(pro.fin_d_horizon(DEPART, 10), date(2036, 10, 16))

    def test_un_horizon_de_zero_an_est_refuse(self):
        for annees in (0, -3):
            with self.subTest(annees=annees):
                with self.assertRaises(ValueError):
                    pro.fin_d_horizon(DEPART, annees)

    def test_un_29_fevrier_ne_casse_rien(self):
        """L'année cible n'a pas toujours un 29 : on ferme le 28, jamais le 1er mars.

        Un horizon ne s'allonge pas d'une bizarrerie de calendrier : s'il se
        fermait le 1er mars, dix ans dureraient un jour de plus que dix ans.
        """
        depart = date(2028, 2, 29)
        self.assertEqual(pro.fin_d_horizon(depart, 1), date(2029, 2, 28))
        self.assertEqual(pro.fin_d_horizon(depart, 3), date(2031, 2, 28))
        # Quatre ans plus tard, 2032 est bissextile : le 29 existe, et il est gardé.
        self.assertEqual(pro.fin_d_horizon(depart, 4), date(2032, 2, 29))
        self.assertLess(pro.fin_d_horizon(depart, 1), date(2029, 3, 1))
        self.assertLess(pro.fin_d_horizon(depart, 3), date(2031, 3, 1))

    def test_les_quatre_fenetres_aux_deux_horizons(self):
        """Le fait publié, figé : 3 couvertes et 1 dehors à cinq ans.

        C'est le cœur de la passe. À cinq ans, la troisième fenêtre se ferme
        quinze jours avant la fin de l'horizon — et cette borne est datée au mois,
        donc la couverture est vraie « à un mois près » ; la quatrième s'ouvre
        seize jours **après** la fin de l'horizon. À dix ans, la quatrième tombe
        dans l'horizon mais reste ouverte, donc partielle.
        """
        attendu = {
            (5, "incident_majeur"): ("entierement", 1657, False),
            (5, "crises_simultanees"): ("entierement", 1110, False),
            (5, "fragmentation_prolongee"): ("entierement", 15, True),
            (5, "ordres_suivants"): ("hors_horizon", None, True),
            (10, "incident_majeur"): ("entierement", 3484, False),
            (10, "crises_simultanees"): ("entierement", 2937, False),
            (10, "fragmentation_prolongee"): ("entierement", 1842, False),
            (10, "ordres_suivants"): ("partiellement", None, False),
        }
        for fenetre in pro.FENETRES:
            for annees, _ in pro.HORIZONS:
                croisement = pro.couverture(fenetre, DEPART, annees)
                with self.subTest(fenetre=fenetre.cle, annees=annees):
                    self.assertEqual(
                        (croisement.verdict, croisement.marge_jours, croisement.a_un_mois_pres),
                        attendu[(annees, fenetre.cle)])

    def test_la_marge_est_bien_la_difference_des_bornes(self):
        """Aucune marge n'est écrite à la main : elles se recalculent."""
        for fenetre in pro.FENETRES:
            for annees, _ in pro.HORIZONS:
                croisement = pro.couverture(fenetre, DEPART, annees)
                if croisement.marge_jours is None:
                    continue
                with self.subTest(fenetre=fenetre.cle, annees=annees):
                    fin = pro.fin_d_horizon(DEPART, annees)
                    self.assertEqual(croisement.marge_jours, (fin - fenetre.fin).days)

    def test_une_fenetre_qui_souvre_le_dernier_jour_de_l_horizon_est_dedans(self):
        """La borne exacte, trouvée par un sabotage qui restait muet.

        Le 15 octobre 2026, un sabotage a déplacé le seuil d'un jour
        (`recul > 0` → `recul >= 0`) **sans qu'aucun contrôle rougisse** : aucune
        fenêtre du document ne s'ouvre pile le dernier jour de l'horizon. La règle
        est pourtant claire — un horizon qui se ferme le 16 ouvre ses dernières
        24 heures ; une fenêtre qui commence ce jour-là est **dedans**. Ce cas-là
        a donc son contrôle, sur une fenêtre construite pour lui.
        """
        fin = pro.fin_d_horizon(DEPART, 5)
        fenetre = pro.Fenetre(
            cle="a_la_borne", libelle="Fenêtre ouverte le dernier jour de l'horizon",
            debut=fin, debut_precision="jour", fin=None, fin_precision="aucune",
            signaux_qui_renforcent="", signaux_contraires="")
        croisement = pro.couverture(fenetre, DEPART, 5)
        self.assertEqual(croisement.verdict, "partiellement",
                         "une fenêtre ouverte le dernier jour de l'horizon est dedans : "
                         "elle ne peut pas être « hors de l'horizon »")
        self.assertEqual((fenetre.debut - croisement.fin_horizon).days, 0)

    def test_une_fenetre_qui_souvre_le_lendemain_est_dehors(self):
        """La borne voisine, symétrique : un jour après, elle est dehors."""
        fin = pro.fin_d_horizon(DEPART, 5)
        fenetre = pro.Fenetre(
            cle="juste_apres", libelle="Fenêtre ouverte le lendemain",
            debut=date(fin.year, fin.month, fin.day + 1), debut_precision="jour",
            fin=None, fin_precision="aucune",
            signaux_qui_renforcent="", signaux_contraires="")
        self.assertEqual(pro.couverture(fenetre, DEPART, 5).verdict, "hors_horizon")

    def test_les_trois_verdicts_sont_ceux_declares(self):
        for fenetre in pro.FENETRES:
            for annees, _ in pro.HORIZONS:
                with self.subTest(fenetre=fenetre.cle, annees=annees):
                    self.assertIn(pro.couverture(fenetre, DEPART, annees).verdict,
                                  pro.COUVERTURES)

    def test_la_phrase_du_croisement_dit_sa_marge(self):
        """Ce qu'on lit doit permettre de juger sans recalculer."""
        fenetre = next(f for f in pro.FENETRES if f.cle == "fragmentation_prolongee")
        phrase = pro.couverture(fenetre, DEPART, 5).phrase
        self.assertIn("2031-10-01", phrase)
        self.assertIn("2031-10-16", phrase)
        self.assertIn("15 jours", phrase)
        self.assertIn("à un mois près", phrase, "la borne au mois n'est pas annoncée")

    def test_un_verdict_sans_imprecision_ne_l_annonce_pas(self):
        """L'annonce de l'imprécision doit dire vrai dans les deux sens."""
        fenetre = next(f for f in pro.FENETRES if f.cle == "incident_majeur")
        croisement = pro.couverture(fenetre, DEPART, 5)
        self.assertFalse(croisement.a_un_mois_pres)
        self.assertNotIn("à un mois près", croisement.phrase)

    def test_la_phrase_de_l_horizon_est_composee(self):
        phrase = pro.phrase_de_l_horizon(DEPART, 5)
        self.assertIn("2026-10-16", phrase)
        self.assertIn("2031-10-16", phrase)
        self.assertIn("3 des 4", phrase)
        self.assertIn("ordres_suivants", phrase)
        phrase_10 = pro.phrase_de_l_horizon(DEPART, 10)
        self.assertIn("partiellement", phrase_10)
        self.assertNotIn("rien de la veille", phrase_10)

    def test_le_registre_public_les_deux_horizons_et_leurs_phrases(self):
        registre = pro.registre(DEPART)
        self.assertEqual([h["annees"] for h in registre["horizons"]], [5, 10])
        self.assertEqual(registre["horizons"][0]["fin"], "2031-10-16")
        self.assertEqual(sorted(registre["phrases_des_horizons"]), ["10", "5"])
        self.assertEqual(registre["depart"], "2026-10-16")
        for fenetre in registre["fenetres"]:
            with self.subTest(fenetre=fenetre["cle"]):
                self.assertEqual(sorted(fenetre["couverture"]), ["10", "5"])

    def test_le_registre_ne_calcule_aucune_probabilite(self):
        """La règle du dépôt : des dates, pas de probabilités.

        Le mot peut apparaître — le critère cité de l'audit dit « pas de probabilité
        d'emploi sans méthode défendable ». Ce que le contrôle refuse, c'est une
        probabilité **affirmée** : chaque occurrence doit être niée. C'est la leçon
        du 15 octobre 2026, apprise en écrivant un contrôle trop grossier qui
        rougissait sur la phrase même qu'il fallait écrire.
        """
        texte = json.dumps(pro.registre(DEPART), ensure_ascii=False).lower()
        for interdit in ("chance sur", "risque de guerre en", " probabilité de "):
            with self.subTest(mot=interdit):
                self.assertNotIn(interdit, texte)
        for occurrence in re.finditer(r"[^.]*probabilit[^.]*", texte):
            with self.subTest(occurrence=occurrence.group(0).strip()[:60]):
                contexte = occurrence.group(0)
                self.assertTrue(any(negation in contexte
                                    for negation in ("aucune", "pas de", "jamais", "non ")),
                                f"une probabilité est affirmée sans négation : {contexte.strip()[:80]}")
        self.assertIn("aucune probabilité", texte)


class TestLesFenetresCitentLeDocument(unittest.TestCase):
    """Le module ne réécrit pas le document : il le cite."""

    @classmethod
    def setUpClass(cls):
        cls.document = (RACINE / pro.DOCUMENT_FENETRES).read_text(encoding="utf-8")
        cls.audit = (RACINE / pro.DOCUMENT_LACUNES).read_text(encoding="utf-8")

    def test_le_document_porte_les_quatre_fenetres(self):
        for bornes in ("3 octobre 2026–3 avril 2027", "Avril 2027–octobre 2028",
                       "Octobre 2028–octobre 2031", "Après octobre 2031"):
            with self.subTest(bornes=bornes):
                self.assertIn(bornes, self.document,
                              "le document ne porte plus cette fenêtre : le module le cite "
                              "faussement")

    def test_chaque_libelle_est_le_texte_du_document(self):
        for fenetre in pro.FENETRES:
            with self.subTest(fenetre=fenetre.cle):
                self.assertIn(fenetre.libelle, self.document)
                self.assertIn(fenetre.signaux_qui_renforcent, self.document)
                self.assertIn(fenetre.signaux_contraires, self.document)

    def test_le_document_dit_que_ce_ne_sont_pas_des_previsions(self):
        """Le module reprend cet avertissement : il doit exister pour être repris."""
        for phrase in ("des horizons, pas des dates de guerre",
                       "Point de départ : **3 octobre 2026**",
                       "non déduites d'un modèle statistique",
                       "Aucun pic de risque",
                       "ne prétendent\npas que le risque augmente mécaniquement avec le temps"):
            with self.subTest(phrase=phrase[:40]):
                self.assertIn(phrase, self.document)
        avertissement = pro.registre(DEPART)["avertissement"]
        self.assertIn("plan de veille", avertissement)
        self.assertIn("non déduites d'un modèle", avertissement)
        self.assertIn("Aucune probabilité n'est calculée", avertissement)

    def test_chaque_lacune_est_le_texte_de_l_audit(self):
        for lacune in pro.LACUNES:
            with self.subTest(lacune=lacune.libelle):
                self.assertIn(lacune.libelle, self.audit)
                self.assertIn(lacune.critere, self.audit)

    def test_l_audit_cite_la_route_et_les_modules_du_module(self):
        """Les preuves citées doivent exister, symbole compris."""
        for lacune in pro.LACUNES:
            chemin = re.match(r"([\w/.-]+\.py)", lacune.preuve)
            if chemin is None:
                continue
            fichier = RACINE / chemin.group(1)
            with self.subTest(lacune=lacune.libelle, fichier=chemin.group(1)):
                self.assertTrue(fichier.exists(), "une preuve cite un fichier absent")
                contenu = fichier.read_text(encoding="utf-8")
                for symbole in re.findall(r"\(([\w, _]+)\)", lacune.preuve):
                    for nom in [s.strip() for s in symbole.split(",") if s.strip()]:
                        # Frontière de mot obligatoire : « frequence_de_bas » est un
                        # préfixe de « frequence_de_base », et un contrôle par
                        # sous-chaîne laissait passer un symbole tronqué. Trouvé par
                        # un sabotage, le 15 octobre 2026.
                        self.assertRegex(contenu, rf"\b{re.escape(nom)}\b",
                                         f"la preuve cite « {nom} », absent de "
                                         f"{chemin.group(1)}")


class TestLeRegistreEtLeDocumentSAccordent(unittest.TestCase):
    """Un statut déclaré dans le code doit l'être aussi dans le document daté.

    La règle 3 du module : le code propose, le document dispose. Concrètement,
    une lacune ne peut pas se dire **refermée** dans le code si le document ne
    porte pas sa date de fermeture.
    """

    @classmethod
    def setUpClass(cls):
        cls.audit = (RACINE / pro.DOCUMENT_LACUNES).read_text(encoding="utf-8")

    def test_le_registre_du_module_est_celui_attendu(self):
        self.assertEqual([(lacune.priorite, lacune.libelle, lacune.statut) for lacune in pro.LACUNES],
                         ATTENDU_LACUNES)

    def test_une_lacune_refermee_porte_la_date_du_document(self):
        for lacune in pro.LACUNES:
            if lacune.statut != "refermee":
                continue
            with self.subTest(lacune=lacune.libelle):
                self.assertIsNotNone(lacune.fermee_le,
                                     "une lacune refermée doit porter sa date")
                ligne = next((texte for texte in self.audit.splitlines()
                              if lacune.libelle in texte), "")
                self.assertIn(lacune.fermee_le, ligne,
                              "le document ne date pas cette fermeture : le code s'attribue "
                              "une guérison que l'audit n'a pas écrite")

    def test_aucune_lacune_ouverte_ne_se_dit_refermee(self):
        """Une lacune reste ouverte tant que la preuve n'est pas un jeu réel."""
        refermees = [lacune for lacune in pro.LACUNES if lacune.statut == "refermee"]
        self.assertEqual([lacune.libelle for lacune in refermees],
                         ["Indice nucléaire non calibré"],
                         "une lacune s'est refermée sans que ce contrôle soit révisé")

    def test_le_document_compte_les_memes_priorites(self):
        lignes = [texte for texte in self.audit.splitlines()
                  if re.match(r"^\| P[012] \|", texte)]
        for lacune in pro.LACUNES:
            with self.subTest(lacune=lacune.libelle):
                self.assertTrue(any(f"| {lacune.priorite} |" in ligne
                                    and lacune.libelle in ligne for ligne in lignes),
                                "cette lacune a changé de rang dans le document")

    def test_le_resume_du_registre_est_accorde(self):
        resume = pro.resume_des_lacunes()
        self.assertIn("2 ouvertes", resume)
        self.assertIn("4 partiellement traitées", resume)
        self.assertIn("1 refermée", resume)
        self.assertIn("aucune revendication prédictive", resume)


class TestLaRouteEtLaPage(unittest.TestCase):
    """La surface : la route répond, la page l'affiche et suit l'horizon."""

    @classmethod
    def setUpClass(cls):
        cls.page = HTML_PAGE

    @staticmethod
    def _appeler(chemin: str, query: str = "") -> tuple[str, dict]:
        sortie: dict = {}

        def start_response(statut, entetes):
            sortie["statut"] = statut

        environ = {"REQUEST_METHOD": "GET", "PATH_INFO": chemin, "QUERY_STRING": query,
                   "wsgi.input": io.BytesIO(b""), "REMOTE_ADDR": "127.0.0.1"}
        corps = b"".join(application(environ, start_response))
        return sortie["statut"], json.loads(corps)

    def test_la_route_repond_avec_le_registre(self):
        statut, donnees = self._appeler("/api/prospective", "depart=2026-10-16")
        self.assertEqual(statut, "200 OK")
        self.assertEqual(donnees["depart"], "2026-10-16")
        self.assertEqual(len(donnees["fenetres"]), 4)
        self.assertEqual(len(donnees["lacunes"]), 7)
        self.assertEqual(donnees["lacunes_par_statut"]["ouverte"], 2)

    def test_la_route_accepte_une_date_et_la_rejette_si_elle_est_illisible(self):
        statut, donnees = self._appeler("/api/prospective", "depart=2030-01-01")
        self.assertEqual(statut, "200 OK")
        self.assertEqual(donnees["depart"], "2030-01-01")
        statut, donnees = self._appeler("/api/prospective", "depart=hier")
        self.assertIn("500", statut, "une date illisible doit être refusée, pas devinée")
        self.assertIn("error", donnees)

    def test_le_bloc_7_est_dans_l_audit_apres_la_pesee(self):
        section = self.page[self.page.index('id="section-audit"'):]
        section = section[:section.index("</section>")]
        # L'ordre est celui des blocs de l'audit : la pesée, puis la prospective.
        self.assertLess(section.index("6."), section.index('id="audit-prospective-details"'))
        self.assertIn('<div class="corps" id="audit-prospective">', section)
        resumes = re.findall(r"<summary>(\d+)\.", section)
        self.assertEqual(resumes, ["1", "2", "3", "4", "5", "6", "7"])

    def test_l_en_tete_de_l_audit_annonce_la_prospective(self):
        self.assertIn("une page de prospective", self.page)

    def test_l_appel_n_a_pas_lieu_de_lacher(self):
        """Une route muette laisse un aveu, jamais une page cassée."""
        self.assertIn("La prospective a sa propre route", self.page)
        # Le module est lu dans un try/catch : la panne devient un état, pas une erreur.
        debut = self.page.index("async function chargerProspective(){")
        fin = self.page.index("\n}\n", debut)
        corps = self.page[debut:fin]
        self.assertIn("try {", corps)
        self.assertIn("catch (erreur)", corps)
        self.assertIn("PROSPECTIVE = null", corps)
        self.assertIn("Registre de prospective indisponible", self.page)

    def test_la_page_suit_l_horizon_choisi(self):
        """Changer d'horizon redit le bloc, sans recharger la page."""
        debut = self.page.index("function changerHorizon(")
        corps = self.page[debut:self.page.index("\n}\n", debut)]
        self.assertIn("rendreProspective();", corps)
        self.assertIn("horizonCourant()", self.page,
                      "la page ne dit plus quel horizon elle affiche")

    def test_la_page_ne_recopie_aucune_date_de_fin(self):
        """Les dates affichées viennent du serveur : la page n'en invente aucune.

        Le défaut qu'on refuse : une date de fin d'horizon recalculée en
        JavaScript finirait par diverger de celle du serveur — deux dates pour un
        même horizon, c'est une de trop.
        """
        debut = self.page.index("/* Bloc « prospective »")
        fin = self.page.index("async function chargerAudit(){")
        fragment = self.page[debut:fin]
        self.assertNotRegex(fragment, r"\b20[0-9]{2}-[0-9]{2}-[0-9]{2}\b",
                            "une date en dur a été écrite dans le bloc de prospective")
        self.assertNotIn("setFullYear", fragment)
        self.assertIn("horizon.fin", fragment, "la fin d'horizon doit venir du serveur")
        self.assertIn("PROSPECTIVE.source_fenetres", fragment,
                      "le bloc doit dire quel document il cite")

    def test_l_horizon_du_select_est_le_meme_que_celui_du_module(self):
        """Deux horizons dans la page, deux horizons dans le module : les mêmes."""
        select = re.search(r'id="horizon-simulation"[^>]*>(.*?)</select>', self.page, re.S)
        self.assertIsNotNone(select, "le select d'horizon a disparu de la page")
        valeurs = re.findall(r'<option value="(\d+)"', select.group(1))
        self.assertEqual([int(v) for v in valeurs], [annees for annees, _ in pro.HORIZONS],
                         "le select et le module ne proposent plus les mêmes horizons")

    def test_la_prospective_est_dans_la_surface_de_la_page(self):
        """La route est appelée par la page — donc plafonnée ou excusée, jamais oubliée."""
        self.assertIn("fetch('/api/prospective')", self.page)


@unittest.skipIf(NODE is None, "Node.js n'est pas installé : contrôle d'exécution ignoré")
class TestLeBlocDeProspectiveExecute(unittest.TestCase):
    """Le bloc, construit pour de vrai, avec la réponse réelle de la route.

    Un contrôle statique lit du texte ; celui-ci exécute la page. C'est ce qui a
    manqué au premier jet de cette passe : la cellule des bornes d'une fenêtre
    sans fin datée faisait **quarante signes** dans un `td.chiffre` — insécable —
    et aucun contrôle statique ne pouvait le voir, puisque ce HTML-là n'existe
    qu'au moment où le navigateur le fabrique.
    """

    @classmethod
    def setUpClass(cls):
        script = "\n".join(re.findall(r"<script>(.*?)</script>", HTML_PAGE, re.S))
        fragment = script[script.index(DEBUT_BLOC):script.index(FIN_BLOC,
                                                                 script.index(DEBUT_BLOC))]
        sortie: dict = {}

        def start_response(statut, entetes):
            sortie["statut"] = statut

        environ = {"REQUEST_METHOD": "GET", "PATH_INFO": "/api/prospective",
                   "QUERY_STRING": f"depart={DEPART.isoformat()}",
                   "wsgi.input": io.BytesIO(b""), "REMOTE_ADDR": "127.0.0.1"}
        cls.reponse = json.loads(b"".join(application(environ, start_response)))
        cls.statut = sortie["statut"]

        def fonction(nom: str) -> str:
            debut = script.index(f"function {nom}(")
            return script[debut:script.index("\n}\n", debut) + 3]

        programme = f"""
const document = new Document();
const zone = document.createElement("div");
zone.setAttribute("id", "audit-prospective");
document.body.appendChild(zone);

let HORIZON_SIMULATION = 5;
{fonction("horizonCourant")}
{fonction("echapperTexte")}
{fragment}

const PROSPECTIVE_SERVIE = {json.dumps(cls.reponse, ensure_ascii=False)};
const rendus = {{}};
[5, 10].forEach(function (annees){{
  HORIZON_SIMULATION = annees;
  PROSPECTIVE = PROSPECTIVE_SERVIE;
  rendus[String(annees)] = {{ html: auditProspectiveHtml(), pose: rendreProspective() }};
}});

// Et la panne : la route muette ne doit pas fabriquer de chiffres.
HORIZON_SIMULATION = 5;
PROSPECTIVE = null;
const muet = auditProspectiveHtml();
console.log(JSON.stringify({{ rendus: rendus, muet: muet }}));
"""
        import_ = f'import {{ Document }} from "{DOM_PARTAGE.as_uri()}";\n'
        cls.source = import_ + programme
        with tempfile.TemporaryDirectory(prefix="prospective-bloc-") as temporaire:
            chemin = Path(temporaire) / "essai.mjs"
            chemin.write_text(cls.source, encoding="utf-8")
            cls.retour = subprocess.run([NODE, str(chemin)], capture_output=True,
                                        text=True, timeout=120)
        cls.rapports = (json.loads(cls.retour.stdout.strip().splitlines()[-1])
                        if cls.retour.returncode == 0 else None)

    def _html(self, annees: int) -> str:
        self.assertIsNotNone(self.rapports, self.retour.stdout + self.retour.stderr)
        return self.rapports["rendus"][str(annees)]["html"]

    def test_le_bloc_se_construit_sans_erreur(self):
        self.assertEqual(self.retour.returncode, 0,
                         self.retour.stdout + self.retour.stderr)
        self.assertEqual(self.statut, "200 OK")
        for annees in (5, 10):
            self.assertTrue(self.rapports["rendus"][str(annees)]["pose"],
                            "le bloc doit se poser dans sa zone")

    def test_aucune_cellule_insecable_ne_depasse_trente_signes(self):
        """La règle du dépôt, vérifiée sur le HTML réellement fabriqué."""
        for annees in (5, 10):
            cellules = re.findall(r'<td class="chiffre">(.*?)</td>', self._html(annees), re.S)
            self.assertEqual(len(cellules), 11,
                             "quatre bornes de fenêtre et sept rangs de lacune")
            for cellule in cellules:
                self.assertLessEqual(
                    len(cellule), SIGNE_MAXIMUM,
                    f"« {cellule} » fait {len(cellule)} signes dans une cellule "
                    "insécable : sur un téléphone, ce texte serait coupé")

    def test_le_bloc_montre_les_quatre_fenetres_et_les_sept_lacunes(self):
        html = self._html(5)
        self.assertEqual(html.count("<tr>"), 4 + 1 + 7 + 1,
                         "quatre fenêtres, quatre en-têtes, sept lacunes et un en-tête")
        for fenetre in self.reponse["fenetres"]:
            self.assertIn(fenetre["libelle"], html,
                          "une fenêtre du document doit être citée telle quelle")
            self.assertIn(fenetre["source"], html, "sa source aussi")
        for lacune in self.reponse["lacunes"]:
            self.assertIn(lacune["libelle"], html)
            self.assertIn(lacune["critere"], html, "et ce qui la fermerait")

    def test_la_fenetre_sans_fin_datée_le_dit_sans_se_couper(self):
        """Le cas trouvé en relisant : elle s'écrit court, et s'explique à côté."""
        for annees in (5, 10):
            html = self._html(annees)
            self.assertIn("2031-11-01 → sans fin datée", html)
            self.assertIn("le document n’écrit aucune fin à cette fenêtre", html)
            self.assertNotIn("à partir du 2031-11-01, sans fin datée", html,
                             "la phrase ne tient pas dans une cellule insécable")

    def test_les_couvertures_suivent_l_horizon_choisi(self):
        """Cinq ans et dix ans ne racontent pas la même chose."""
        cinq, dix = self._html(5), self._html(10)
        self.assertNotEqual(cinq, dix, "les deux horizons rendent le même texte")
        self.assertIn("⛔", cinq, "à cinq ans, la quatrième fenêtre est hors horizon")
        self.assertIn("◐", dix, "à dix ans, elle n'est couverte que partiellement")
        self.assertIn("à un mois près", cinq,
                      "la fenêtre à quinze jours de la fin doit dire son imprécision")

    def test_une_route_muette_laisse_un_aveu_sans_tableau(self):
        self.assertIsNotNone(self.rapports, self.retour.stdout + self.retour.stderr)
        muet = self.rapports["muet"]
        self.assertIn("Registre de prospective indisponible", muet)
        self.assertNotIn("<table>", muet, "pas de tableau sans données")
        self.assertNotIn("<td", muet, "ni de cellule vide à remplir")


if __name__ == "__main__":
    unittest.main()
