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


class TestVerificateurJS(unittest.TestCase):
    """Le vérificateur doit accepter le JS valide et refuser l'invalide."""

    def test_objets_litteraux_dans_les_substitutions(self):
        # Un objet vide ou imbriqué dans un `${…}` ne doit pas être confondu
        # avec l'accolade fermante de la substitution.
        for script in ("const a = `${f({})}`;",
                       "const a = `<b class=\"${g((x || {}).y)}\">${h(1)}</b>`;",
                       "const a = `${liste.map(v => `${v}`).join('')}`;"):
            avec, message = verifier_js(script)
            self.assertTrue(avec, f"{script} → {message}")

    def test_erreurs_reelles_detectees(self):
        for script in ("function f(){ if (a) { return 1; }", "function f(){} }",
                       "const a = `${f(1)};", "const a = `${f(1)}`;)"):
            avec, _ = verifier_js(script)
            self.assertFalse(avec, script)


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

    def test_console_de_veille_permanente(self):
        """La veille tient en un ruban : elle ne recouvre jamais les leviers."""
        self.assertIn('id="console-pilotage"', self.page)
        self.assertIn('id="ruban-veille"', self.page)
        # Seul le ruban est épinglé, et il tient sur une ligne.
        ruban = self.page.split(".ruban-veille{", 1)[1].split("}", 1)[0]
        self.assertIn("position:sticky", ruban.replace(" ", ""))
        console = self.page.split(".console{", 1)[1].split("}", 1)[0]
        self.assertNotIn("position:sticky", console.replace(" ", ""))
        self.assertIn("flex-wrap:wrap", ruban.replace(" ", ""))
        # Le corps de la console est repliable : on peut libérer l'écran.
        self.assertIn("console-corps", self.page)
        self.assertIn(".console-corps.replie{display:none}", self.page)
        self.assertIn("function basculerDetailsConsole()", self.script)
        self.assertIn("classList.toggle('replie')", self.script)
        for identifiant in ("console-verdict", "console-strates", "console-danger",
                            "console-population", "console-derniere-modification",
                            "console-alertes", "console-marges", "console-conseil",
                            "console-cout-global"):
            self.assertIn(f'id="{identifiant}"', self.page, identifiant)
        self.assertIn("function renderConsole(", self.script)
        self.assertIn("function renderDerniereModification(", self.script)
        # Le conseiller temps réel (« effet papillon ») est branché sur la page.
        self.assertIn("function majConseilTempsReel(", self.script)
        self.assertIn("function renderConseil(", self.script)
        self.assertIn("let MOUVEMENT = null;", self.script)
        self.assertIn("let DERNIER_CONSEIL = null;", self.script)
        self.assertIn("/api/conseil", self.script)
        self.assertIn("effet papillon", self.page.lower())
        # Le coût / gain réel des réglages globaux croisés est dans la veille.
        self.assertIn("function renderCoutGlobal(", self.script)
        self.assertIn("Coût / gain réel des réglages globaux croisés", self.page)
        self.assertIn(".cout-gain.gain{", self.page)
        self.assertIn(".cout-gain.cout{", self.page)
        # Les cinq niveaux de seuil sont connus du rendu.
        for niveau in ("favorable", "tolerable", "vigilance", "risque", "hors_sol"):
            self.assertIn(niveau, self.script)
        # Le bandeau hors-sol est bien produit par le rendu.
        self.assertIn("bandeau-hors-sol", self.script)

    def test_tous_les_leviers_sont_visibles_et_actionnables(self):
        """Les 93 paramètres doivent être affichés, groupés et manipulables."""
        self.assertIn('id="section-leviers"', self.page)
        self.assertIn('id="compteur-leviers"', self.page)
        self.assertIn('id="case-densite"', self.page)
        self.assertIn("function basculerDensite(", self.script)
        # La vue dense change la classe de la grille et des familles.
        self.assertIn("'leviers-grille' + (VUE_COMPACTE ? ' compacte' : '')", self.script)
        self.assertIn("' compacte' : ''", self.script)
        self.assertIn("function filtreCourant()", self.script)
        self.assertIn("function allerAuxLeviers()", self.script)
        # Chaque levier continu/entier est un curseur qui déclenche la
        # simulation en direct, sans rechargement ni bouton à presser.
        self.assertIn("oninput=\"majLevier(", self.script)
        self.assertIn("parseFloat(this.value)", self.script)
        self.assertIn("onchange=\"terminerReglage()\"", self.script)
        # L'interrupteur bascule aussi, et clôt le réglage.
        self.assertIn("majLevier('${levier.cle}', this.checked ? 1 : 0); terminerReglage()", self.script)
        # Le compte des leviers affichés est permanent.
        self.assertIn("levier(s) affiché(s)", self.script)

    def test_chaque_levier_recoit_l_impact_de_son_reglage(self):
        """Sous chaque curseur, l'effet mesuré du levier est affiché."""
        self.assertIn("function pucesHtml(", self.script)
        self.assertIn("function majEffetsParLevier(", self.script)
        self.assertIn("let DERNIERES_PUCES = {}", self.script)
        self.assertIn("let LEVIERS_MODIFIES = new Set()", self.script)
        self.assertIn("puce-effect", self.page)
        self.assertIn("class=\"levier${modifie ? ' modifie' : ''}\"", self.script)
        # Les effets viennent de la matrice du modèle quand elle est demandée…
        self.assertIn("(donnees.impacts || []).forEach(impact =>", self.script)
        # …et de la comparaison des deux dernières simulations sinon.
        self.assertIn("Math.abs((parametresEnvoyes[cle] || 0) - (precedente.parametres[cle] || 0)) > 1e-9",
                      self.script)
        # La grille n'est pas reconstruite pendant qu'un curseur est manipulé,
        # sinon le curseur serait remplacé sous les doigts de l'utilisateur.
        self.assertIn("if (!REGLAGE_EN_COURS) renderLeviers(filtreCourant());", self.script)
        self.assertIn("REGLAGE_EN_COURS = true", self.script)
        # Le mouvement (position avant vs position à l'instant T) est capturé
        # pour TOUS les leviers, avant toute écriture de la nouvelle valeur.
        maj = self.script.split("function majLevier(", 1)[1].split("\nfunction ", 1)[0]
        self.assertIn("MOUVEMENT = {cle: cle, avant: PARAMS[cle]}", maj)
        self.assertLess(maj.index("MOUVEMENT = {cle: cle, avant: PARAMS[cle]}"),
                        maj.index("PARAMS[cle] = valeur"),
                        "la position d'avant doit être lue avant l'écriture")

    def test_console_branchee_sur_chaque_simulation(self):
        """Chaque simulation recalcule la console et l'effet de la mesure."""
        simuler = self.script.split("async function simuler(", 1)[1].split("\nfunction ", 1)[0]
        self.assertIn("renderConsole(donnees);", simuler)
        self.assertIn("renderCoutGlobal(donnees);", simuler)
        self.assertIn("renderDerniereModification(", simuler)
        self.assertIn("majConseilTempsReel(parametresEnvoyes);", simuler)
        self.assertIn("SIMULATION_PRECEDENTE", simuler)
        # C'est bien le jeu de paramètres envoyé qui est mémorisé, pas l'objet
        # mutable `PARAMS` (sinon la comparaison porterait sur le même objet).
        self.assertIn("parametresEnvoyes = Object.assign({}, PARAMS)", simuler)
        # Le ruban est alimenté par le même diagnostic, sans requête de plus :
        # `simuler` appelle `renderConsole`, qui remplit le ruban.
        rendu = self.script.split("function renderConsole(", 1)[1].split("\nfunction ", 1)[0]
        self.assertIn("'ruban-veille'", rendu)
        self.assertIn("document.getElementById('ruban-strates')", rendu)
        self.assertIn("document.getElementById('ruban-population')", rendu)

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

    def test_bulles_explicatives_par_reglage(self):
        """Chaque réglage porte un bouton qui ouvre une bulle calculée.

        La bulle doit rester **dans** la carte du levier (jamais par-dessus) :
        l'utilisateur garde ses 93 paramètres visibles et actionnables.
        """
        self.assertIn("bulle-bouton", self.page)
        self.assertIn("bulle-levier", self.page)
        self.assertIn(".bulle-levier{grid-column:1/-1", self.page)
        self.assertIn("data-bulle", self.script)
        self.assertIn("function ouvrirBulle", self.script)
        self.assertIn("function bulleHtml", self.script)
        self.assertIn("async function chargerBulle", self.script)
        self.assertIn("/api/bulle?levier=", self.script)
        # Le bouton est présent dans les deux vues et la bulle suit le levier.
        self.assertEqual(self.script.count("&#39;"), 0)
        self.assertIn("${bouton}", self.script)
        self.assertIn("${pucesHtml(levier.cle)}${zoneCoutLiveHtml(levier.cle)}${bulleHtml(levier.cle)}", self.script)

    def test_bulle_ne_souvre_que_pour_le_levier_choisi(self):
        """Une seule bulle ouverte à la fois, uniquement pour son levier."""
        self.assertIn("if (BULLE_OUVERTE !== cle) return '';", self.script)
        self.assertIn("BULLE_OUVERTE = cle;", self.script)
        self.assertIn("BULLE_OUVERTE = null;", self.script)

    def test_bulle_rafraichie_en_direct_avec_cout_gain_reel(self):
        """La bulle du réglage se rafraîchit dès le mouvement, avec le coût /
        gain réel de ce réglage précis, en rouge / vert transparent."""
        # Le bloc live est rendu dans chaque bulle, au sommet de la fiche.
        self.assertIn('id="bulle-live"', self.script)
        self.assertIn("function bulleLiveHtml(", self.script)
        self.assertIn("function coutGainHtml(", self.script)
        self.assertIn("function majBulleLive(", self.script)
        # Mise à jour DOM directe (sans re-rendu) dès la réponse du conseiller.
        self.assertIn("majBulleLive();", self.script)
        # Retour immédiat dès le début du geste, avant même la réponse serveur.
        maj = self.script.split("function majLevier(", 1)[1].split("\nfunction ", 1)[0]
        self.assertIn("if (BULLE_OUVERTE === cle)", maj)
        self.assertIn("Mesure du coût / gain réel", maj)
        # Rouge / vert en transparence, comme le bandeau hors-sol.
        self.assertIn(".cout-gain.gain{background:linear-gradient(90deg,rgba(34,197,94,.34)", self.page)
        self.assertIn(".cout-gain.cout{background:linear-gradient(90deg,rgba(239,68,68,.34)", self.page)
        # Le conseil stocké alimente la bulle et cite les sources officielles.
        self.assertIn("DERNIER_CONSEIL = conseil;", self.script)
        self.assertIn("sources officielles", self.script)

    def test_badge_cout_gain_visible_sous_le_levier_et_dans_le_ruban(self):
        """Les indicateurs visuels temps réel sont visibles sans ouvrir la
        bulle : un badge sous le levier manipulé, une puce dans le ruban."""
        # Le badge est rendu dans chaque carte de levier, vue confort et compacte.
        self.assertIn("function badgeCoutLiveHtml(", self.script)
        self.assertIn("function zoneCoutLiveHtml(", self.script)
        self.assertIn("function majBadgeCoutLive(", self.script)
        self.assertIn("function placeholderMesure(", self.script)
        self.assertIn("${zoneCoutLiveHtml(levier.cle)}", self.script)
        # Il apparaît dans les deux gabarits (confort et compact).
        self.assertEqual(self.script.count("${zoneCoutLiveHtml(levier.cle)}"), 2)
        # Le ruban porte la puce coût / gain, alimentée à chaque simulation.
        self.assertIn('id="ruban-cout"', self.page)
        self.assertIn("ruban-cout", self.script)
        self.assertIn(".ruban-cout.gain{", self.page)
        self.assertIn(".ruban-cout.cout{", self.page)
        self.assertIn(".cout-live.gain{", self.page)
        self.assertIn(".cout-live.cout{", self.page)
        # renderCoutGlobal met à jour le ruban et la console.
        rendu = self.script.split("function renderCoutGlobal(", 1)[1].split("\nfunction ", 1)[0]
        self.assertIn("ruban-cout", rendu)
        self.assertIn("console-cout-global", rendu)

    def test_infobulles_au_survol_des_reglages(self):
        """Curseurs, interrupteurs et boutons s'expliquent au survol.

        L'aide est affichée par une couche fixe et passive : elle ne capte
        aucun clic et disparaît quand la souris repart, donc les réglages
        restent tous actionnables.
        """
        self.assertIn('id="infobulle"', self.page)
        self.assertIn(".infobulle{position:fixed", self.page)
        self.assertIn("pointer-events:none", self.page)
        self.assertIn("[data-aide],[data-aide-levier]{cursor:help}", self.page)
        for fonction in ("elementInfobulle", "levierParCle", "texteAideLevier",
                         "texteAideElement", "positionnerInfobulle", "afficherInfobulle",
                         "masquerInfobulle", "survoler", "initialiserInfobulles"):
            with self.subTest(fonction=fonction):
                self.assertIn(f"function {fonction}", self.script)
        self.assertIn("initialiserInfobulles();", self.script)
        # Survol, sortie de souris, focus clavier, clic (pour ne pas masquer l'aide).
        for evenement in ("mouseover", "mouseout", "focusin", "focusout", "mousedown", "scroll"):
            self.assertIn(evenement, self.script)
        # L'aide du levier reflète le dernier mouvement en temps réel.
        aide = self.script.split("function texteAideLevier(", 1)[1].split("\nfunction ", 1)[0]
        self.assertIn("MOUVEMENT && MOUVEMENT.cle === cle", aide)
        self.assertIn("dernier mouvement", aide)

    def test_chaque_reglage_est_annote_pour_le_survol(self):
        """Les zones interactives des 93 leviers portent leur aide."""
        self.assertGreaterEqual(self.script.count('data-aide-levier="${levier.cle}"'), 6)
        self.assertIn('<input type="range" data-aide-levier=', self.script)
        self.assertIn('<input type="checkbox" data-aide-levier=', self.script)
        self.assertIn('data-aide="${texteAide}"', self.script)          # cartes de domaine
        self.assertIn("card.setAttribute('data-aide'", self.script)      # scénarios/préréglages
        self.assertIn("data-aide=\"${texteAide}\"", self.script)       # puces d'impact
        # Les boutons de la page (en-tête, ruban, barre des leviers) sont annotés.
        self.assertGreaterEqual(self.page.count('data-aide="'), 10)

    def test_bulle_guide_opportunites_et_desagrements(self):
        """Le contenu doit guider : chaîne, répercussions, garde-fous, pistes."""
        for marqueur in ("Chaîne d'interaction", "Répercussions mesurées",
                         "Effets déclarés au catalogue", "Opportunités", "Désagréments",
                         "À surveiller", "Pistes de compensation"):
            with self.subTest(marqueur=marqueur):
                self.assertIn(marqueur, self.script)
        self.assertIn("bulle-domaine", self.page)
        self.assertIn(".bulle-levier .bulle-domaine.pos", self.page)
        self.assertIn(".bulle-levier .bulle-domaine.neg", self.page)

    def test_semantique_des_scores_expliquee(self):
        """Un score ne veut rien dire s'il n'est pas expliqué à l'utilisateur."""
        self.assertIn("Comment lire les scores", self.page)
        self.assertIn("trajectoire de référence", self.page)
        self.assertIn("écarts de politique publique", self.page)

    def test_section_audit_tracabilite_en_bas_de_page(self):
        """Pas de boîte noire : sources, formules, seuils et méthode sont
        livrés en bas de page, vérifiables et recoupables."""
        self.assertIn('id="section-audit"', self.page)
        for identifiant in ("audit-sources", "audit-domaines", "audit-leviers",
                            "audit-gardefous", "audit-methodes"):
            self.assertIn(f'id="{identifiant}"', self.page, identifiant)
        # Les cinq blocs de recoupement et leur rendu.
        self.assertIn("Audit &amp; traçabilité", self.page)
        self.assertIn("function chargerAudit(", self.script)
        self.assertIn("function auditSourcesHtml(", self.script)
        self.assertIn("function auditDomainesHtml(", self.script)
        self.assertIn("function auditLeviersHtml(", self.script)
        self.assertIn("function auditGardeFousHtml(", self.script)
        self.assertIn("function auditMethodesHtml(", self.script)
        self.assertIn("chargerAudit();", self.script)
        # Le barème des garde-fous est servi par une route dédiée.
        self.assertIn("/api/garde_fous", self.script)
        # L'échappement protège l'audit de toute injection.
        self.assertIn("function echapperTexte(", self.script)
        # Un bouton de l'en-tête mène à l'audit.
        self.assertIn("allerAudit()", self.script)
        self.assertIn("function allerAudit(", self.script)

    def test_attribution_et_banniere_mrsc(self):
        """L'outil est open-source sous bannière MRSC : la paternité est
        protégée et l'usage gratuit, énoncés en bas de page."""
        self.assertIn("Bannière MRSC", self.page)
        self.assertIn("MRSC", self.page)
        self.assertIn("nul ne peut s'en attribuer", self.page.lower())
        self.assertIn("par le peuple, pour le peuple", self.page.lower())


if __name__ == "__main__":
    unittest.main()
