"""
tests/test_interface.py — Tests statiques de la page du simulateur.

L'interface est une page unique servie par le serveur, dont tout le JavaScript
vit dans une chaîne Python. Ces tests protègent ce qui ne se voit qu'à
l'exécution dans le navigateur : cohérence des identifiants, équilibre des
délimiteurs, absence de dépendance externe, et présence des contrôles promis
(curseurs, interrupteurs, exports, provenance, rafraîchissement).
"""

import re
import unittest

from simulateur.interface import HTML_PAGE
from tests.verificateur_js import verifier_js


def _script(page: str) -> str:
    return "\n".join(re.findall(r"<script>(.*?)</script>", page, re.S))


def _identifiants_referencés(script: str) -> set[str]:
    trouve = set(re.findall(r"getElementById\('([^']+)'\)", script))
    trouve |= set(re.findall(r"getElementById\(\"([^\"]+)\"\)", script))
    return trouve


class TestStructureDeLaPage(unittest.TestCase):
    """Le document servi doit être autonome et bien formé."""

    @classmethod
    def setUpClass(cls):
        cls.page = HTML_PAGE
        cls.script = _script(cls.page)

    def test_page_unique_sans_dependance_externe(self):
        """Aucune ressource distante : la page doit vivre hors ligne."""
        self.assertNotIn("<script src=", self.page)
        self.assertNotIn("<link ", self.page)
        self.assertNotIn("@import", self.page)
        self.assertGreater(len(self.page), 20_000)

    def test_balises_div_equilibrees(self):
        self.assertEqual(len(re.findall(r"<div\b", self.page)),
                         len(re.findall(r"</div>", self.page)))

    def test_javascript_equilibre(self):
        """Accolades, parenthèses et gabarits du JS doivent être appariés."""
        equipre, message = verifier_js(self.script)
        self.assertTrue(equipre, message)

    def test_chaque_identifiant_utilise_existe(self):
        declares = set(re.findall(r'id="([^"]+)"', self.page))
        self.assertTrue(_identifiants_referencés(self.script))
        self.assertFalse(_identifiants_referencés(self.script) - declares,
                         "getElementById sur un identifiant absent du document")

    def test_placeholder_des_scenarios(self):
        self.assertIn("===SCENARIOS_JSON===", self.page)

    def test_aucune_globale_implicite_event(self):
        self.assertIsNone(re.search(r"(?<![\w$])event(?![\w$])", self.script))


class TestCascadeDesCinqEchelons(unittest.TestCase):
    """La mise en situation doit montrer les 5 échelons du modèle."""

    def test_les_cinq_strates_sont_nommees(self):
        for strate in ("locale", "nationale", "européenne", "mondiale", "géopolitique"):
            with self.subTest(strate=strate):
                self.assertIn(strate, HTML_PAGE)

    def test_rendu_de_la_cascade(self):
        self.assertIn("strates-cascade", HTML_PAGE)
        self.assertIn("renderStrates", HTML_PAGE)


class TestControlesUtilisateur(unittest.TestCase):
    """L'utilisateur doit pouvoir tout piloter lui-même."""

    @classmethod
    def setUpClass(cls):
        cls.page = HTML_PAGE
        cls.script = _script(cls.page)

    def test_leviers_rendus_avec_curseurs_et_recherche(self):
        self.assertIn("function renderLeviers", self.script)
        self.assertIn('type="range"', self.script)
        self.assertIn('type="checkbox"', self.script)
        self.assertIn("recherche-levier", self.page)
        self.assertIn("function filtrerLeviers", self.script)

    def test_recalcul_a_la_volée_avec_anti_rebond(self):
        """Chaque mouvement de curseur reprogramme une simulation différée."""
        self.assertIn("function planifierSimulation", self.script)
        self.assertIn("setTimeout", self.script)
        self.assertIn("minuteur", self.script)

    def test_simulation_serveur_et_impacts_croises(self):
        self.assertIn("/api/simuler", self.script)
        self.assertIn("avec_impacts", self.script)
        self.assertIn("function renderMatrice", self.script)
        self.assertIn("matrice-impacts", self.page)

    def test_reinitialisation_et_presets(self):
        self.assertIn("function reinitialiser", self.script)
        self.assertIn("function chargerPreset", self.script)
        # Le compteur de leviers actifs compare par clé : comparer par position
        # donnait un compte faux dès que l'ordre des paramètres changeait.
        compteur = self.script.split("function nombreLeviersActifs()")[1].split("\nfunction ")[0]
        self.assertIn("Object.entries(PARAMS).filter(([cle, valeur])", compteur)
        self.assertIn("defauts[cle]", compteur)
        # Deux grilles, deux usages : scénarios du dépôt (moteur d'origine) et
        # préréglages doctrinaux (simulateur paramétrable).
        self.assertIn("9 situations rejouées par le moteur d'origine", self.page)
        self.assertIn("chargées dans le simulateur puis ajustables", self.page)
        self.assertIn("preset-grid", self.page)

    def test_exports(self):
        for element in ("btn-export-json", "btn-export-csv", "function exporter",
                        "function telecharger"):
            with self.subTest(element=element):
                self.assertIn(element, self.page)
        self.assertIn("function activerExports", self.script)

    def test_domaines_et_indicateurs_affiches(self):
        self.assertIn("domaines-grille", self.page)
        self.assertIn("function renderDomaines", self.script)
        self.assertIn("variation_relative_pct", self.script)
        self.assertIn("tendance_reference", self.script)

    def test_journal_causal_affiche(self):
        self.assertIn("function renderJournal", self.script)
        self.assertIn("journal", self.page)


class TestDonneesPubliquesDansLaPage(unittest.TestCase):
    """Le rafraîchissement « instant T » se fait depuis le navigateur."""

    @classmethod
    def setUpClass(cls):
        cls.page = HTML_PAGE
        cls.script = _script(cls.page)

    def test_bouton_de_rafraichissement(self):
        self.assertIn("btn-rafraichir", self.page)
        self.assertIn("function rafraichirDonnees", self.script)
        self.assertIn("/api/donnees", self.script)

    def test_adaptateurs_de_sources_publiques(self):
        for adaptateur in ("extraireEurostat", "extraireSdmx", "extraireGenerique",
                           "frankfurter", "opendatasoft", "worldbank", "yahoo"):
            with self.subTest(adaptateur=adaptateur):
                self.assertIn(adaptateur, self.script)

    def test_repli_par_le_serveur(self):
        """Les sources sans CORS passent par le relais du serveur (/api/proxy)."""
        self.assertIn("proxy_url", self.script)
        # L'URL du relais est fournie par le serveur (registre d'indicateurs) :
        # le navigateur ne fabrique jamais d'URL arbitraire.
        self.assertIn("indicateur.proxy_url", self.script)

    def test_provenance_et_licences_affichees(self):
        self.assertIn("provenance", self.page)
        self.assertIn("licence", self.script)
        self.assertIn("series_complementaires", self.script)

    def test_semantique_des_scores_expliquee(self):
        """Un score ne veut rien dire s'il n'est pas expliqué à l'utilisateur."""
        self.assertIn("Comment lire les scores", self.page)
        self.assertIn("trajectoire de référence", self.page)
        self.assertIn("écarts de politique publique", self.page)


if __name__ == "__main__":
    unittest.main()
