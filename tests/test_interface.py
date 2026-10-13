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
        # Le bloc coût / gain est hors de la zone repliable : il reste visible
        # même quand le détail des seuils est masqué.
        self.assertIn("cout-global-veille", self.page)
        self.assertLess(self.page.index('id="console-cout-global"'),
                        self.page.index('id="console-corps"'),
                        "le bloc coût/gain doit précéder le corps repliable")
        # Version d'interface visible pour diagnostiquer les pages périmées.
        # Le numéro n'est pas figé ici : le test vérifie la présence et la
        # forme du badge, pas une version précise — sinon chaque livraison
        # casserait la suite pour une chaîne de caractères.
        self.assertIn('id="version-interface"', self.page)
        self.assertRegex(self.page, r"Interface v\d+\.\d+\.\d+ \(\d{4}-\d{2}-\d{2}\)")
        # Les cinq niveaux de seuil sont connus du rendu.
        for niveau in ("favorable", "tolerable", "vigilance", "risque", "hors_sol"):
            self.assertIn(niveau, self.script)
        # Le bandeau hors-sol est bien produit par le rendu.
        self.assertIn("bandeau-hors-sol", self.script)

    def test_tous_les_leviers_sont_visibles_et_actionnables(self):
        """Tous les paramètres du catalogue doivent rester manipulables."""
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

    def test_horizon_cinq_ou_dix_ans_et_bilan_intergenerationnel(self):
        self.assertIn('id="horizon-simulation"', self.page)
        self.assertIn('value="10">2 mandatures', self.page)
        self.assertIn("function changerHorizon(", self.script)
        self.assertIn("horizon: horizon", self.script)
        self.assertIn("horizon: horizonCourant()", self.script)
        self.assertIn('id="bilan-intergenerationnel"', self.page)
        self.assertIn("function renderBilanIntergenerationnel(", self.script)
        self.assertIn("actifs_arrives_a_maturite_mde", self.script)

    def test_chaque_levier_recoit_l_impact_de_son_reglage(self):
        """Sous chaque curseur, l'effet mesuré du levier est affiché."""
        self.assertIn("function pucesHtml(", self.script)
        self.assertIn("function majEffetsParLevier(", self.script)
        self.assertIn("let DERNIERES_PUCES = {}", self.script)
        self.assertIn("let LEVIERS_MODIFIES = new Set()", self.script)
        self.assertIn("puce-effect", self.page)
        self.assertIn("class=\"levier${modifie ? ' modifie' : ''}${nonVerifie(levier)}\"", self.script)
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


class TestClassesEtCascadeDuPlan(unittest.TestCase):
    """La carte des classes et la cascade : ce que la page promet, en clair."""

    @classmethod
    def setUpClass(cls):
        cls.page = HTML_PAGE
        cls.script = _script(HTML_PAGE)

    def test_les_classes_sont_expliquees_avant_les_curseurs(self):
        """On lit d'abord où va l'argent, ensuite on règle les leviers."""
        self.assertIn('id="section-classes"', self.page)
        self.assertLess(self.page.index('id="section-classes"'),
                        self.page.index('id="section-leviers"'))

    def test_la_legende_la_balance_et_la_cascade_sont_dans_la_page(self):
        for identifiant in ("classes-legende", "classes-filtres", "balance-classes",
                            "grille-classes", "classes-note",
                            "cascade-classes", "cascade-marches", "cascade-note"):
            with self.subTest(identifiant=identifiant):
                self.assertIn(f'id="{identifiant}"', self.page)

    def test_la_cascade_dessine_les_marches_et_se_referme_sur_le_solde(self):
        self.assertIn("function renderCascade", self.script)
        self.assertIn("function marchesCascade", self.script)
        self.assertIn("function contributionClasse", self.script)
        # Le solde de la cascade est celui du moteur : la page n'additionne pas
        # un total parallèle.
        self.assertIn("renderCascade();", self.script)
        self.assertIn("cascade-marches", self.script)
        self.assertIn("cascade-montant", self.script)

    def test_la_page_n_entre_jamais_les_unites_dans_le_solde(self):
        """Les classes non monétaires viennent du catalogue, pas d'une liste cachée."""
        self.assertIn("function monetaireDe", self.script)
        self.assertIn("fiche.monetaire", self.script)
        self.assertIn("montant_hors_budget_mde", self.script)

    def test_l_annee_lue_se_choisit_sans_relancer_la_simulation(self):
        """Changer d'année relit la section : la simulation, elle, ne bouge pas."""
        for identifiant in ("classe-annee-prec", "classe-annee-courante",
                            "classe-annee-suiv", "classe-rythme"):
            with self.subTest(identifiant=identifiant):
                self.assertIn(f'id="{identifiant}"', self.page)
        for fonction in ("function changerAnneeClasses", "function renderRythme",
                         "function classeAnneeAffichee", "function classeReferenceAffichee"):
            with self.subTest(fonction=fonction):
                self.assertIn(fonction, self.script)
        corps = self.script[self.script.index("function changerAnneeClasses"):]
        self.assertIn("renderClasses();", corps[:400])
        self.assertNotIn("simuler(", corps[:400])

    def test_aucune_teinte_de_classe_n_est_peinte_hors_variable(self):
        """Une couleur de classe se déclare une fois, puis se lit par variable.

        La page est intégrée au site M.R.S.C., dont la feuille surcharge la
        palette : une teinte écrite en dur dans une règle de classe resterait
        accrochée à l'ancienne palette au lieu de suivre celle du site.
        """
        debut = self.page.index("/* ══ Classes de leviers")
        region = self.page[debut:self.page.index("@media print", debut)]
        # On retire les usages de variables (et les replis écrits dedans) : il ne
        # doit rester aucune couleur, sauf les voiles neutres blancs/noirs.
        sans_variables = re.sub(r"var\((?:[^()]|\([^()]*\))*\)", "var()", region)
        sans_variables = re.sub(r"color-mix\((?:[^()]|\([^()]*\))*\)", "color-mix()", sans_variables)
        for couleur in re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)", sans_variables):
            with self.subTest(couleur=couleur):
                composantes = re.findall(r"\d+", couleur)
                if couleur.startswith("#"):
                    self.fail(f"teinte écrite en dur dans les règles de classes : {couleur}")
                self.assertLessEqual(
                    len(set(composantes[:3])), 1,
                    f"seuls les voiles neutres sont admis ici, pas {couleur}")

    def test_les_plateaux_de_la_balance_suivent_la_variable_de_classe(self):
        for variable in ("--classe-recettes-fond", "--classe-depenses-fond"):
            with self.subTest(variable=variable):
                self.assertIn(f"{variable}:", self.page)
        for cote in ("entrees", "sorties"):
            with self.subTest(cote=cote):
                self.assertRegex(
                    self.page,
                    rf"\.balance-cote\.{cote}\{{[^}}]*color-mix\(in srgb,var\(--classe-")

    def test_les_barres_de_la_cascade_restent_visibles_sans_couleur(self):
        """Impression et contrastes forcés : un contour remplace la teinte."""
        forces = self.page[self.page.index("@media (forced-colors:active)"):]
        forces = forces[:forces.index("@media print")]
        self.assertIn(".cascade-piste .barre", forces)
        impression = self.page[self.page.index("@media print"):]
        self.assertIn(".cascade-piste .barre", impression[:2000])


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
        self.assertIn("situations rejouées par le moteur d'origine", self.page)
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

    def test_calibrage_menage_relie_sources_qualifiees_et_saisie_personnelle(self):
        self.assertIn('id="mode-calibrage-menage"', self.script)
        self.assertIn("Mes données personnelles saisies par poste", self.script)
        self.assertIn("Structure INSEE 2025 appliquée à mon total", self.script)
        self.assertIn("function partsPanierNational()", self.script)
        self.assertIn("function depenseBaseProfil(item)", self.script)
        self.assertIn("function modifierModeCalibrageMenage(mode)", self.script)
        self.assertIn("statut :", self.script)
        self.assertIn("publication_le", self.script)
        self.assertIn("parts INSEE renormalisées", self.script)
        self.assertIn("jamais transmis à l'API, inclus dans un lien de partage", self.script)
        self.assertIn("Le calibrage ne change pas la simulation macro.", self.script)

    def test_bulles_explicatives_par_reglage(self):
        """Chaque réglage porte un bouton qui ouvre une bulle calculée.

        La bulle doit rester **dans** la carte du levier (jamais par-dessus) :
        l'utilisateur garde tous les paramètres visibles et actionnables.
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
        # Jamais d'aide flottante par-dessus un résultat en cours de lecture :
        # ni pendant un réglage, ni quand une bulle « interactions » est ouverte.
        survoler = self.script.split("function survoler(", 1)[1].split("\nfunction ", 1)[0]
        self.assertIn("if (REGLAGE_EN_COURS || BULLE_OUVERTE){ masquerInfobulle(); return; }",
                      survoler)
        maj = self.script.split("function majLevier(", 1)[1].split("\nfunction ", 1)[0]
        self.assertIn("masquerInfobulle();", maj)
        ouvrir = self.script.split("async function ouvrirBulle(", 1)[1].split("\nfunction ", 1)[0]
        self.assertIn("masquerInfobulle();", ouvrir)
        # L'aide du levier reflète le dernier mouvement en temps réel.
        aide = self.script.split("function texteAideLevier(", 1)[1].split("\nfunction ", 1)[0]
        self.assertIn("MOUVEMENT && MOUVEMENT.cle === cle", aide)
        self.assertIn("dernier mouvement", aide)

    def test_chaque_reglage_est_annote_pour_le_survol(self):
        """Les zones interactives du catalogue portent leur aide."""
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
        self.assertIn("Hypothèses P16-P21", self.script)
        self.assertIn("145/24", self.script)
        self.assertIn("143/30", self.script)
        self.assertIn("ratio Barnier 8/30", self.script)
        self.assertIn("9004289", self.script)
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


class TestLisibilitePourTous(unittest.TestCase):
    """Compréhensible par tous : sommaire, lexique, lecture en clair, guide.

    Un outil démocratique qui n'est lisible que par ceux qui savent déjà n'est
    pas un outil démocratique. Ces tests vérifient que les quatre dispositifs
    de lisibilité sont bien servis dans la page — et qu'ils ne reposent sur
    aucune ressource externe.
    """

    @classmethod
    def setUpClass(cls):
        cls.page = HTML_PAGE
        cls.script = _script(cls.page)

    def test_un_sommaire_donne_l_ordre_de_lecture(self):
        """La page est longue : un fil d'Ariane dit où l'on est."""
        self.assertIn('id="sommaire"', self.page)
        self.assertIn("Lire dans l'ordre", self.page)
        for ancre in ("section-contexte", "section-clair", "section-leviers",
                      "section-resultats", "section-audit"):
            self.assertIn(f'href="#{ancre}"', self.page, ancre)
            self.assertIn(f'id="{ancre}"', self.page, ancre)
        self.assertIn("function marquerSommaire(", self.script)

    def test_la_section_lecture_en_clair_existe(self):
        """Les chiffres du moteur sont relus en phrases ordinaires."""
        for identifiant in ("clair-resume", "clair-lignes", "clair-limites"):
            self.assertIn(f'id="{identifiant}"', self.page, identifiant)
        self.assertIn("Lire le résultat", self.page)
        self.assertIn("function renderLecture(", self.script)
        self.assertIn("renderLecture(donnees);", self.script)

    def test_le_lexique_est_ouvrable_depuis_l_entete(self):
        self.assertIn('id="btn-lexique"', self.page)
        self.assertIn("ouvrirLexique()", self.page)
        self.assertIn("/api/lexique", self.script)
        self.assertIn("function chargerLexique(", self.script)
        self.assertIn("function rendreLexique(", self.script)
        self.assertIn("function filtrerLexique(", self.script)

    def test_les_termes_du_lexique_sont_soulignables_dans_le_texte(self):
        self.assertIn("function baliserTermes(", self.script)
        self.assertIn("function appliquerLexique(", self.script)
        self.assertIn("function marquerTextes(", self.script)
        self.assertIn("class=\"terme\"", self.script)
        # Le balisage doit respecter les attributs HTML : un « > » à
        # l'intérieur d'un `data-aide` ne doit pas être pris pour une
        # balise fermante.
        self.assertIn("guillemet", self.script)

    def test_le_guide_de_demarrage_est_disponible(self):
        self.assertIn('id="btn-guide"', self.page)
        self.assertIn("function ouvrirGuide(", self.script)
        self.assertIn("function contenuGuide(", self.script)
        self.assertIn("ETAPES_GUIDE", self.script)
        # Première visite seulement : jamais imposé deux fois.
        self.assertIn("function guideDejaVu(", self.script)
        self.assertIn("function marquerGuideVu(", self.script)
        self.assertIn("simulateur_guide_vu", self.script)
        # Le stockage peut être refusé (navigation privée) : cela ne doit pas
        # empêcher l'affichage du guide.
        self.assertIn("catch (erreur)", self.script)

    def test_la_modale_est_fermable_de_trois_facons(self):
        self.assertIn('id="overlay"', self.page)
        self.assertIn('id="modale-corps"', self.page)
        self.assertIn("function ouvrirModale(", self.script)
        self.assertIn("function fermerModale(", self.script)
        self.assertIn("function siClicDehors(", self.script)
        # Bouton, clic à l'extérieur et touche Échap.
        self.assertIn("function initialiserModale(", self.script)
        self.assertIn("Escape", self.script)

    def test_le_guide_rappelle_que_le_modele_n_est_pas_une_prophétie(self):
        self.assertIn("pas une prophétie", self.script)
        self.assertIn("référence", self.script)


class TestFluiditeDuRendu(unittest.TestCase):
    """Le rendu ne refait pas à chaque geste ce qu'il peut ne pas faire."""

    @classmethod
    def setUpClass(cls):
        cls.page = HTML_PAGE
        cls.script = _script(cls.page)

    def test_les_onglets_de_strate_sont_rendus_a_la_demande(self):
        """Seul l'onglet ouvert est construit, les autres attendent."""
        self.assertIn("function contenuOngletStrate(", self.script)
        self.assertIn("function rendreOngletStrate(", self.script)
        # L'ancien rendu massif des sept panneaux a disparu.
        self.assertNotIn("renderResultatsMenage(donnees);renderResultatsBoursiers();",
                         self.script)
        self.assertIn("if (SORTIE) rendreOngletStrate(cle, SORTIE);", self.script)

    def test_la_matrice_n_est_pas_effacee_pendant_un_reglage(self):
        """Une matrice vide sous les yeux serait une régression d'affichage."""
        self.assertIn("DERNIERE_MATRICE", self.script)
        self.assertIn('id="matrice-fraicheur"', self.page)

    def test_le_lexique_se_charge_sans_bloquer_le_demarrage(self):
        # `chargerLexique()` est appelé sans `await` : il ne retarde ni le
        # catalogue ni la première simulation.
        self.assertIn("  chargerLexique();", self.script)


class TestReglagesPartageables(unittest.TestCase):
    """Un réglage se transmet : c'est un lien, pas un fichier à expliquer."""

    @classmethod
    def setUpClass(cls):
        cls.page = HTML_PAGE
        cls.script = _script(cls.page)

    def test_un_bouton_de_partage_est_dans_la_barre(self):
        self.assertIn('id="btn-partage"', self.page)
        self.assertIn("onclick=\"partagerReglages()\"", self.page)
        self.assertIn('id="avis-lien"', self.page)

    def test_le_lien_ne_transporte_que_ce_qui_a_bouge(self):
        """Les 149 paramètres n'ont rien à faire dans une adresse."""
        self.assertIn("function reglagesModifies()", self.script)
        self.assertIn("function lienReglages()", self.script)
        self.assertIn("?sim=", self.script)
        # La comparaison se fait contre les valeurs neutres du catalogue.
        self.assertIn("CATALOGUE.parametres.defauts", self.script)

    def test_une_adresse_recue_n_est_jamais_crue(self):
        """Seules les clés connues du catalogue et les nombres passent."""
        self.assertIn("function reglagesDepuisLien(", self.script)
        self.assertIn("hasOwnProperty.call(defauts, cle)", self.script)
        self.assertIn("typeof valeur === 'number' && isFinite(valeur)", self.script)
        # Un JSON illisible est ignoré, jamais rendu en texte dans la page.
        self.assertIn("catch (erreur){ return repris; }", self.script)

    def test_l_avis_est_ecrit_en_texte_et_non_en_html(self):
        """L'adresse peut contenir n'importe quoi : rien n'est injecté."""
        self.assertIn("zone.textContent =", self.script)

    def test_le_programme_de_depart_ne_s_ajoute_pas_aux_reglages_repris(self):
        """Sinon le lien ne rouvrirait pas la simulation partagée."""
        self.assertIn("const depuisLien = appliquerLien();", self.script)
        self.assertIn("if (depuisLien) simuler(true); else chargerPreset('mandature', null);",
                      self.script)


if __name__ == "__main__":
    unittest.main()


class TestSocleResponsive(unittest.TestCase):
    """La page tient sur tous les écrans, et le prouve.

    Ces contrôles protègent les mesures de `docs/RD_VISUEL_RESPONSIVE.md` :
    un texte illisible, un tableau qui déborde ou une cible tactile trop petite
    doivent faire échouer la suite, pas se découvrir sur un téléphone.
    """

    @classmethod
    def setUpClass(cls):
        cls.page = HTML_PAGE
        cls.css = cls.page[cls.page.index("<style>") + len("<style>"):cls.page.index("</style>")]
        cls.script = _script(cls.page)

    def test_le_plancher_de_lisibilite_est_declare(self):
        """--t-min est le plancher de lecture : il est écrit une fois, ici."""
        self.assertIn("--t-min:12.5px", self.css)

    def test_aucune_taille_de_texte_ne_passe_sous_le_plancher(self):
        """Tout texte sous 12 px est passé par `max(var(--t-min), …)`.

        Pourquoi `max()` : les réglages d'agrandissement du site (125 %, 150 %)
        agrandissent les `rem`. Un plancher en pixels seul les casserait ; les
        deux ensemble gardent la lisibilité et l'agrandissement.
        """
        fautives = []
        for regle in re.findall(r"font-size:([^;}\n]+)", self.css):
            valeur = regle.strip()
            if "max(var(--t-min)" in valeur:
                continue
            mesure = re.fullmatch(r"(\d*\.?\d+)(rem|em|px)", valeur)
            if not mesure:
                continue
            px = float(mesure.group(1)) * (16 if mesure.group(2) in ("rem", "em") else 1)
            if px < 12:
                fautives.append(valeur)
        self.assertEqual(fautives, [], "tailles sous le plancher de lecture : " + ", ".join(fautives))

    def test_quatre_paliers_d_ecran(self):
        """Téléphone, grand téléphone, tablette, portable : quatre paliers."""
        for palier in ("max-width:1200px", "max-width:900px", "max-width:640px", "max-width:480px"):
            with self.subTest(palier=palier):
                self.assertIn(palier, self.css)

    def test_le_tactile_et_les_champs_ont_leurs_regles(self):
        """44 px de cible, 16 px dans un champ (sinon iOS zoome au focus)."""
        self.assertIn("(pointer:coarse)", self.css)
        bloc = self.css[self.css.index("(pointer:coarse)"):]
        self.assertIn("min-height:44px", bloc)
        self.assertIn("font-size:max(16px,1rem)", bloc)

    def test_les_tableaux_larges_defilent_dans_leur_region(self):
        """Un tableau large défile dans sa région, il ne pousse pas la page."""
        self.assertIn(".tableau-defilant{", self.css)
        regle = self.css[self.css.index(".tableau-defilant{"):]
        self.assertIn("overflow:auto", regle[:120])
        self.assertIn("max-width:100%", regle[:120])
        self.assertIn("function rendreTableauxDefilants(", self.script)
        self.assertIn("function tableauDejaDefilant(", self.script)
        # La région est nommée et atteignable au clavier.
        self.assertIn("setAttribute('role', 'region')", self.script)
        self.assertIn("setAttribute('tabindex', '0')", self.script)
        self.assertIn("faites défiler horizontalement", self.script)
        # Les tableaux créés après coup (strates, audit, bourse) sont couverts.
        self.assertIn("MutationObserver", self.script)
        self.assertIn("rendreTableauxDefilants();", self.script)

    def test_les_enfants_de_grille_peuvent_retenir(self):
        """Sans `min-width:0`, un enfant refuse de rétrécir et déborde."""
        self.assertRegex(self.css, r"\.grille>\*[^{}]*\{[^}]*min-width:0")
        self.assertRegex(self.css, r"\.leviers-grille>\*[^{}]*\{[^}]*min-width:0")

    def test_le_sommaire_se_replie_et_reste_en_haut(self):
        """Vingt sections sans repère : le sommaire accompagne la lecture."""
        self.assertIn('id="sommaire-bascule"', self.page)
        self.assertIn('aria-controls="sommaire-liste"', self.page)
        self.assertIn('id="sommaire-liste"', self.page)
        self.assertIn("function basculerSommaire(", self.script)
        self.assertIn(".sommaire.ouverte .sommaire-liste{display:flex", self.css)
        # La règle collante est celle des grands écrans : le sommaire suit la
        # lecture au lieu de disparaître dès la première section.
        self.assertIn(".sommaire{position:sticky", self.css)

    def test_le_lien_d_evitement_ouvre_la_page(self):
        """Premier élément focalisable : on saute l'en-tête au clavier."""
        self.assertIn('<body>\n<a class="lien-evitement" href="#sommaire">', self.page)
        self.assertIn(".lien-evitement:focus-visible{transform:none}", self.css)

    def test_le_theme_n_ecrit_plus_ses_teintes_dans_les_regles(self):
        """Une couleur se déclare dans :root, jamais dans une règle."""
        self.assertNotIn("#7b8aa5", self.css)
        self.assertIn("--panel-3:", self.css)
        self.assertNotIn("#22304f", self.css)


class TestResumeDeTeteEtChapitres(unittest.TestCase):
    """Comprendre sans faire défiler vingt sections.

    Le résumé de tête ne recalcule rien : il relit la balance. Les chapitres
    donnent quatre temps dans une page qui n'en finissait pas de commencer.
    """

    @classmethod
    def setUpClass(cls):
        cls.page = HTML_PAGE
        cls.script = _script(cls.page)

    def test_le_resume_de_tete_est_en_haut_de_page(self):
        for identifiant in ("resume", "resume-titre", "resume-phrase", "resume-solde",
                            "resume-entrees", "resume-sorties", "resume-menage"):
            with self.subTest(identifiant=identifiant):
                self.assertIn(f'id="{identifiant}"', self.page)
        # Il se place après l'en-tête, avant la première section de contenu.
        debut_resume = self.page.index('id="resume"')
        self.assertLess(self.page.index("</header>"), debut_resume)
        self.assertLess(debut_resume, self.page.index('id="section-contexte"'))

    def test_le_resume_relit_la_balance_au_lieu_de_recalculer(self):
        self.assertIn("function renderResume(", self.script)
        # Les valeurs viennent des mêmes fonctions que la balance…
        corps = self.script[self.script.index("function renderResume("):]
        corps = corps[:corps.index("\n}")]
        for source in ("classeAnneeAffichee()", "fmtSigne(", "fmtMenage(", "statutDiviseur()"):
            with self.subTest(source=source):
                self.assertIn(source, corps)
        # …et la phrase est celle du verdict, reprise telle quelle.
        self.assertIn("balance-verdict", corps)
        # La balance appelle le résumé : deux affichages, un seul calcul.
        balance = self.script[self.script.index("function renderBalance("):]
        balance = balance[:balance.index("\nfunction ")]   # la fonction seule
        self.assertIn("renderResume();", balance)

    def test_les_quatre_chapitres_sont_dans_le_deroule(self):
        for identifiant in ("chapitre-comprendre", "chapitre-mesurer",
                            "chapitre-regler", "chapitre-verifier"):
            with self.subTest(identifiant=identifiant):
                self.assertIn(f'id="{identifiant}"', self.page)
        # Chaque chapitre précède la première section qu'il ouvre.
        for chapitre, section in (("chapitre-comprendre", "section-contexte"),
                                  ("chapitre-mesurer", "section-impact"),
                                  ("chapitre-regler", "section-scenarios"),
                                  ("chapitre-verifier", "section-contradiction")):
            with self.subTest(chapitre=chapitre):
                self.assertLess(self.page.index(f'id="{chapitre}"'),
                                self.page.index(f'id="{section}"'))

    def test_les_mouvements_restent_discrets_et_arretables(self):
        """Le geste reçoit une réponse ; l'utilisateur peut la couper."""
        self.assertIn(".resume .metric{transition:", self.page)
        self.assertIn(".cascade-piste .barre,.balance-cote .jauge-classe span{transition:", self.page)
        bloc = self.page[self.page.index("@media (prefers-reduced-motion:reduce){"):]
        self.assertIn("transition:none", bloc[:400])
