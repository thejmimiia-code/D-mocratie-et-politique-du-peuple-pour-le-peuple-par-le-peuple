"""Garde-fous du registre de la contradiction (`simulateur/contradiction.py`).

Ce fichier vérifie trois choses, dans l'ordre où un lecteur les vérifierait :

1. **Le registre tient debout** — sept pièces par objection, sources internes qui
   existent, sources externes datées, statuts connus, un changement écrit dès
   qu'une objection est concédée.
2. **Les documents sont la sortie du registre** — `docs/05`, `docs/20` et
   `docs/21` sont régénérés et comparés, et le gage annoncé dans le registre est
   confronté au chiffre écrit dans l'en-tête de la fiche correspondante.
3. **La promesse est servie** — la route `GET /api/objections` répond, filtre, et
   la page porte la section qui l'affiche (`index.html` inclus).
"""

from __future__ import annotations

import json
import re
import socket
import subprocess
import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from simulateur.contradiction import (  # noqa: E402
    CONTRE_MODELES,
    FAMILLES,
    OBJECTIONS,
    PROFONDEURS_MINIMALES,
    STATUTS,
    coherence,
    objections,
    portee_du_levier,
)
from simulateur.dashboard import SCENARIOS, create_server  # noqa: E402
from simulateur.parametres import LEVIERS, PRESETS  # noqa: E402

DOC_GUIDE = RACINE / "docs" / "05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md"
DOC_CONTRE_MODELES = RACINE / "docs" / "20_CONTRE_MODELES.md"
DOC_REGISTRE = RACINE / "docs" / "21_OBJECTIONS_OUVERTES.md"
GENERATEUR = RACINE / "outils" / "generer-objections.py"
MODELE_ISSUE = RACINE / ".github" / "ISSUE_TEMPLATE" / "objection.md"


class TestRegistre(unittest.TestCase):
    """Les sept pièces, les sources et les statuts — clause par clause."""

    @classmethod
    def setUpClass(cls):
        cls.objets = objections()

    def test_les_garde_fous_du_registre_sont_vides(self):
        defauts = {cle: valeurs for cle, valeurs in coherence().items() if valeurs}
        self.assertEqual(defauts, {}, f"garde-fous en défaut : {defauts}")

    def test_chaque_objection_porte_ses_sept_pieces(self):
        for o in self.objets:
            with self.subTest(objection=o.cle):
                self.assertTrue(o.titre.strip())
                self.assertIn(o.famille, FAMILLES)
                self.assertIn(o.statut, STATUTS)
                for piece, minimum in PROFONDEURS_MINIMALES.items():
                    texte = getattr(o, piece)
                    self.assertGreaterEqual(len(texte), minimum,
                                            f"{piece} trop court pour être autre chose qu'un slogan")
                self.assertTrue(o.sources, "aucune source : une objection non sourcée reste un avis")

    def test_une_objection_concedee_ecrit_ce_qu_elle_change(self):
        for o in self.objets:
            with self.subTest(objection=o.cle):
                if o.statut in {"concedee", "partiellement_concedee"}:
                    self.assertTrue(o.changements.strip(),
                                    "concéder sans écrire le changement rend la concession décorative")

    def test_les_sources_internes_correspondent_a_des_fichiers(self):
        for o in self.objets:
            for source in o.sources:
                if source.nature != "interne":
                    continue
                with self.subTest(objection=o.cle, chemin=source.chemin):
                    self.assertTrue((RACINE / source.chemin).exists(),
                                    f"source interne introuvable : {source.chemin}")

    def test_les_sources_externes_sont_datees_et_attribuees(self):
        for o in self.objets:
            for source in o.sources:
                if source.nature != "externe":
                    continue
                with self.subTest(objection=o.cle):
                    self.assertTrue(source.date.strip(), f"sans date : {source.reference}")
                    self.assertTrue(source.origine.strip(), f"sans origine : {source.reference}")

    def test_les_numeros_et_les_fiches_sont_uniques(self):
        numeros = [o.numero for o in self.objets]
        self.assertEqual(sorted(numeros), list(range(1, len(self.objets) + 1)),
                         "les numéros du registre doivent aller de 1 à N, sans trou")
        fiches = sorted(o.fiche for o in self.objets if o.famille == "mesure")
        self.assertEqual(fiches, list(range(1, 11)), "une fiche du guide par objection de mesure")

    def test_le_guide_porte_exactement_les_dix_fiches_attendues(self):
        page = DOC_GUIDE.read_text(encoding="utf-8")
        fiches = sorted(int(numero) for numero in re.findall(r"^## FICHE (\d+)", page, re.M))
        self.assertEqual(fiches, list(range(1, 11)))


class TestGagesEtPortees(unittest.TestCase):
    """Le chiffre du dossier est confronté à celui du levier, jamais recopié à l'aveugle."""

    def test_chaque_levier_cite_existe(self):
        for o in objections():
            if o.levier:
                with self.subTest(objection=o.cle):
                    self.assertIn(o.levier, LEVIERS)

    def test_les_gages_du_registre_sont_ceux_des_fiches(self):
        """Le gage est écrit dans l'en-tête de la fiche : les deux doivent coïncider."""
        page = DOC_GUIDE.read_text(encoding="utf-8")
        annonces = {}
        for numero, titre in re.findall(r"^## FICHE (\d+) : (.+)$", page, re.M):
            montant = re.search(r"\(([+-]?\d+(?:[.,]\d+)?)\s*Md€", titre)
            annonces[int(numero)] = float(montant.group(1).replace(",", ".")) if montant else None
        self.assertEqual(sorted(annonces), list(range(1, 11)))
        for o in objections("mesure"):
            with self.subTest(objection=o.cle):
                self.assertEqual(o.gage_mde_an, annonces[o.fiche],
                                 f"fiche {o.fiche} : le registre et l'en-tête ne disent pas la même chose")

    def test_la_portee_est_deduite_du_catalogue(self):
        """Un levier sans champ en Md€ n'a pas de portée : le registre n'en invente pas."""
        for o in objections():
            if not o.levier:
                continue
            with self.subTest(objection=o.cle):
                portee = portee_du_levier(o.levier)
                self.assertEqual(portee, portee_du_levier(o.levier), "lecture instable")
                if o.gage_mde_an is not None:
                    self.assertIsNotNone(portee, "un gage sans portée de levier n'est pas vérifiable")
                    self.assertGreaterEqual(abs(portee) + 1e-9, abs(o.gage_mde_an),
                                            "un gage au-dessus de la portée du levier est impossible")
                if o.levier.startswith("reforme_") and o.gage_mde_an is None:
                    self.assertIsNone(portee, "une réforme institutionnelle n'a pas de portée en Md€")

    def test_la_marge_de_portee_est_la_somme_des_ecarts(self):
        """La réserve affichée est calculée, jamais saisie."""
        attendu = round(sum(abs(portee_du_levier(o.levier) or 0) - abs(o.gage_mde_an or 0)
                            for o in objections() if o.gage_mde_an is not None), 2)
        from simulateur.contradiction import synthese_pour_api

        self.assertEqual(synthese_pour_api()["portees"]["marge_totale_mde"], attendu)
        self.assertGreater(attendu, 0, "aucune marge : le registre et le catalogue se contredisent")


class TestContreModeles(unittest.TestCase):
    """Un contre-modèle cite des scénarios et des préréglages qui existent vraiment."""

    def test_les_contre_modeles_citent_des_scenarios_reels(self):
        self.assertGreaterEqual(len(CONTRE_MODELES), 4)
        for modele in CONTRE_MODELES.values():
            with self.subTest(contre_modele=modele.cle):
                self.assertTrue(modele.scenarios, "un contre-modèle sans scénario n'est pas testable")
                for cle in modele.scenarios:
                    self.assertIn(cle, SCENARIOS, f"scénario inconnu : {cle}")

    def test_les_contre_modeles_citent_des_presets_reels(self):
        for modele in CONTRE_MODELES.values():
            for cle in modele.presets:
                with self.subTest(contre_modele=modele.cle):
                    self.assertIn(cle, PRESETS)

    def test_chaque_contre_modele_dit_ce_qu_il_lui_concede(self):
        for modele in CONTRE_MODELES.values():
            with self.subTest(contre_modele=modele.cle):
                self.assertTrue(modele.ce_que_le_simulateur_en_dit.strip())
                self.assertTrue(modele.concession.strip())
                self.assertTrue(modele.divergence.strip())


class TestFraicheurDesDocuments(unittest.TestCase):
    """Les trois documents sont la sortie du générateur, pas une copie à la main."""

    def test_le_generateur_ne_prend_pas_de_retard(self):
        proc = subprocess.run([sys.executable, str(GENERATEUR), "--verifier"],
                              capture_output=True, text=True, cwd=str(RACINE), timeout=300)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("documents à jour", proc.stdout)

    def test_les_documents_existent_et_portent_leur_titre(self):
        for chemin, titre in ((DOC_CONTRE_MODELES, "Contre-modèles"),
                              (DOC_REGISTRE, "Objections ouvertes")):
            with self.subTest(document=chemin.name):
                contenu = chemin.read_text(encoding="utf-8")
                self.assertIn(titre, contenu)
                self.assertIn("outils/generer-objections.py", contenu)

    def test_le_guide_annonce_le_renversement(self):
        page = DOC_GUIDE.read_text(encoding="utf-8")
        # L'introduction nomme les cinq pièces : on ne compte qu'à partir de la
        # première fiche, sinon chaque titre serait compté deux fois.
        page = page[page.index("## FICHE 1"):]
        for titre in ("La meilleure version de l'objection", "Ce que nous concédons",
                      "Ce que nous maintenons, et pourquoi",
                      "Ce qui nous ferait changer d'avis", "Statut et suites"):
            with self.subTest(titre=titre):
                self.assertEqual(page.count(titre), 10, f"« {titre} » doit apparaître sous chaque fiche")

    def test_le_modele_d_issue_objection_existe(self):
        contenu = MODELE_ISSUE.read_text(encoding="utf-8")
        for rubrique in ("name:", "about:", "labels:", "Mesure ou passage visé", "Objection",
                         "Source", "Chiffre ou hypothèse alternative", "changer d'avis"):
            with self.subTest(rubrique=rubrique):
                self.assertIn(rubrique, contenu)


class TestObjectionsServies(unittest.TestCase):
    """La route et la page : ce qui est écrit est servi, et ce qui est servi est affiché."""

    @classmethod
    def setUpClass(cls):
        socket_libre = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_libre.bind(("127.0.0.1", 0))
        cls.port = socket_libre.getsockname()[1]
        socket_libre.close()
        cls.serveur = create_server("127.0.0.1", cls.port)
        cls.thread = threading.Thread(target=cls.serveur.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        cls.serveur.server_close()

    def _get(self, chemin: str):
        url = f"http://127.0.0.1:{self.__class__.port}{chemin}"
        with urllib.request.urlopen(url, timeout=30) as reponse:
            return reponse.status, json.loads(reponse.read().decode("utf-8"))

    def test_la_route_sert_tout_le_registre(self):
        statut, donnees = self._get("/api/objections")
        self.assertEqual(statut, 200)
        self.assertEqual(donnees["comptes"]["total"], len(OBJECTIONS))
        self.assertGreaterEqual(len(donnees["contre_modeles"]), 4)
        self.assertEqual(donnees["garde_fous"], {})
        for cle in ("portees", "statuts", "familles", "limites"):
            self.assertIn(cle, donnees)
        premier = donnees["objections"][0]
        for champ in ("objection_forte", "concession", "maintien", "falsification", "sources",
                      "statut_libelle", "portee_mde", "gage_mde_an", "marge_de_portee_mde"):
            self.assertIn(champ, premier)

    def test_les_filtres_trient_sans_recalculer(self):
        _, mesures = self._get("/api/objections?famille=mesure")
        self.assertEqual(mesures["total"], 10)
        self.assertTrue(all(o["famille"] == "mesure" for o in mesures["objections"]))
        _, modeles = self._get("/api/objections?famille=modele")
        self.assertEqual(modeles["total"], len(OBJECTIONS) - 10)
        _, concede = self._get("/api/objections?statut=partiellement_concedee")
        self.assertTrue(concede["objections"])
        self.assertTrue(all(o["statut"] == "partiellement_concedee" for o in concede["objections"]))
        _, levier = self._get("/api/objections?levier=lutte_fraude_fiscale_ia")
        self.assertEqual(levier["total"], 1)
        self.assertEqual(levier["objections"][0]["portee_mde"], 10.0)
        _, texte = self._get("/api/objections?chercher=ANSSI")
        self.assertTrue(texte["objections"])

    def test_un_filtre_inconnu_est_refuse_en_le_disant(self):
        for chemin in ("/api/objections?statut=nawak", "/api/objections?famille=nawak"):
            with self.subTest(chemin=chemin):
                with self.assertRaises(urllib.error.HTTPError) as capture:
                    self._get(chemin)
                self.assertEqual(capture.exception.code, 404)

    def test_la_page_porte_la_section_et_l_index_est_a_jour(self):
        from simulateur import interface

        self.assertIn('id="section-contradiction"', interface.HTML_PAGE)
        for identifiant in ("objections-corps", "contre-modeles-corps", "contradiction-resume"):
            self.assertIn(f'id="{identifiant}"', interface.HTML_PAGE)
        self.assertIn("chargerObjections('')", interface.HTML_PAGE)
        index = (RACINE / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="section-contradiction"', index)
        self.assertIn('href="#section-contradiction"', index)


if __name__ == "__main__":
    unittest.main()
