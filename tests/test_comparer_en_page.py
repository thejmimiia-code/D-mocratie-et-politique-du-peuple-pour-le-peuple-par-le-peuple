"""tests/test_comparer_en_page.py — ce que la section « Comparer » doit tenir.

Le moteur servait `/api/comparer` — les préréglages du catalogue rejoués par le
moteur, côte à côte à leur année finale — et la page ne l'appelait pas : la
couverture des routes l'excusait par écrit. Cette section lui donne son écran.

Le parcours JavaScript (`tests/test_interface_navigateur.py`) exécute la section
pour de vrai : il compte les lignes rendues, range le tableau par une colonne et
vérifie qu'un registre hostile ne fait pas passer une balise. Ici, on contrôle ce
qui reste vrai quand on lit la page comme un texte : la section existe, le
sommaire y mène, elle demande la bonne route — et une seule fois —, elle ne
recopie aucun chiffre ni aucun libellé du catalogue, elle ne coûte rien au
démarrage, elle échappe ce qu'elle affiche, et son rangement ne touche à aucune
valeur servie.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

from simulateur import interface as simulateur_interface
from simulateur.interface import HTML_PAGE

RACINE = Path(__file__).resolve().parents[1]

#: Le bloc de la section dans le JavaScript : de son premier état au rendu des
#: réglages institutionnels, qui le suit immédiatement dans la page.
DEBUT_BLOC = "let COMPARAISON = null;"
FIN_BLOC = "function renderReglagesTouches(){"

#: Les fonctions qui écrivent dans la page : chacune échappe ce qu'elle affiche.
FONCTIONS_DE_RENDU = (
    "function enteteComparaisonHtml(", "function ligneComparaisonHtml(",
    "function rendreComparaison(",
)

#: Les colonnes du tableau : leur ordre est celui du contrat affiché, et le
#: contrôle le compare à celui du rendu — un décalage d'une colonne afficherait
#: la dette sous l'étiquette du déficit.
COLONNES = ("solde", "dette", "deficit", "risque", "alertes")

#: Les chiffres que le serveur calcule pour les préréglages : la page ne les
#: écrit jamais elle-même. Ils vieilliraient ici au premier changement de
#: contexte, sans que personne ne le voie — et ils changent déjà d'un mois à
#: l'autre, puisque le contexte « instant T » entre dans chaque simulation.
CHIFFRES_INTERDITS = (
    "41,6", "93,0", "98,1", "96,1", "101,7", "103,1", "141,0", "117,2",
    "148,5", "146,2", "118,2", "111,5", "135,4", "272,8", "52,1", "21,7",
    "89,5", "95,2", "98,4", "99,7", "106,7", "104,3", "103,8", "101,2",
    "27,8", "27,6", "33,7", "63,0", "34,0", "39,1", "60,6", "67,1", "66,1",
    "68,3", "70,4", "51,8", "37,0", "43,3", "48,7",
)

#: Les libellés des scénarios, servis par la route : les recopier ici les
#: figerait, et une reformulation côté serveur n'atteindrait jamais l'écran.
LIBELLES_INTERDITS = (
    "Statu quo", "Plan de mandature", "Deux mandatures",
    "Résilience républicaine", "Austérité brute", "Transition écologique",
    "Justice sociale", "choc mondial", "crise géopolitique",
    "Crise de Taïwan", "Détroit d'Hormuz", "Escalade nucléaire",
    "Convergence Chine", "Refondation démocratique", "Assemblées souveraines",
    "Verrouillage par le haut",
)


class TestLaSectionComparer(unittest.TestCase):
    """Contrôles statiques de la section, sur la page servie."""

    @classmethod
    def setUpClass(cls):
        cls.page = HTML_PAGE
        cls.style = cls.page[cls.page.index("<style>") + len("<style>"):cls.page.index("</style>")]
        debut = cls.page.index(DEBUT_BLOC)
        cls.bloc = cls.page[debut:cls.page.index(FIN_BLOC, debut)]

    def test_le_bloc_est_au_niveau_du_script_et_non_dans_une_fonction(self):
        """Le piège vu pour de vrai : inséré après l'accolade ouvrante de la fonction
        suivante, le bloc reste du JavaScript valide — mais ses `let` deviennent
        locaux et la section ne s'affiche plus. Le contrôle regarde la structure,
        pas la syntaxe."""
        self.assertIn("\n" + DEBUT_BLOC, self.page, "le bloc ne commence pas une ligne")
        self.assertIn("}\n" + FIN_BLOC, self.page,
                      "le bloc doit se terminer avant la fonction suivante, ligne à ligne")

    # ── Elle est là, et on peut y aller ───────────────────────────────────
    def test_la_section_existe_avec_son_ancre(self):
        self.assertIn('id="section-comparaison"', self.page)
        self.assertIn('id="comparaison-corps"', self.page)
        self.assertIn('id="comparaison-resume"', self.page)

    def test_le_sommaire_y_mene(self):
        """Une section sans entrée au sommaire est une section qu'on ne trouve pas."""
        self.assertIn('href="#section-comparaison"', self.page)
        entree = self.page[self.page.index('href="#section-comparaison"'):]
        entree = entree[:entree.index("</a>")]
        self.assertIn("Comparer", entree)
        self.assertIn("data-aide=", entree, "une entrée de sommaire sans aide à la lecture")

    def test_l_entete_nomme_la_route_et_l_annee(self):
        entete = self.page[self.page.index('id="section-comparaison"'):]
        entete = entete[:entete.index("</h2>")]
        self.assertIn("/api/comparer", entete,
                      "l'entête doit dire d'où viennent les chiffres")
        self.assertIn("année finale", entete)

    # ── La route est appelée, une seule fois, et sans recalcul ────────────
    def test_la_page_appelle_la_route_une_seule_fois(self):
        self.assertEqual(self.page.count("fetch('/api/comparer')"), 1)

    def test_aucun_chiffre_du_catalogue_n_est_ecrit_dans_la_page(self):
        for chiffre in CHIFFRES_INTERDITS:
            with self.subTest(chiffre=chiffre):
                self.assertNotIn(chiffre, self.page,
                                 f"le chiffre {chiffre} est écrit dans la page : il vient du serveur")

    def test_aucun_libelle_de_scenario_n_est_ecrit_dans_la_page(self):
        for libelle in LIBELLES_INTERDITS:
            with self.subTest(libelle=libelle):
                self.assertNotIn(libelle, self.page,
                                 f"« {libelle} » est écrit dans la page : il vient du serveur")

    def test_la_section_ne_recalcule_rien(self):
        """Aucune opération sur les valeurs servies, hors mise à l'échelle des barres."""
        interdit = re.compile(r"toFixed|parseFloat|Math\.(pow|sqrt|log)")
        self.assertIsNone(interdit.search(self.bloc),
                          "la section doit afficher les chiffres reçus, pas les recombiner")

    def test_la_section_ne_sert_pas_les_valeurs_par_une_seconde_porte(self):
        """Une seule fonction lit les valeurs servies : le rendu et le tri s'y accordent."""
        self.assertEqual(self.bloc.count("function valeurComparaison("), 1)
        for fonction in ("function lignesRangeesComparaison(", "function ligneComparaisonHtml(",
                         "function maximumSoldeComparaison("):
            self.assertIn(fonction, self.bloc)

    # ── Elle ne coûte rien au démarrage ───────────────────────────────────
    def test_le_chargement_est_observe_et_non_impose(self):
        demarrer = self.page[self.page.index("async function demarrer(){"):]
        demarrer = demarrer[:demarrer.index("\n}")]
        self.assertIn("observerComparaison();", demarrer,
                      "la section doit s'annoncer au démarrage, sans charger")
        self.assertNotIn("await chargerComparaison();", demarrer,
                         "la page ne doit pas payer seize simulations à l'ouverture")
        self.assertNotIn("chargerComparaison();\n  await", demarrer)

    def test_l_observateur_est_tolerant(self):
        """Sans `IntersectionObserver`, la section retourne false et le bouton prend le relais."""
        observateur = self.bloc[self.bloc.index("function observerComparaison("):]
        self.assertIn("typeof IntersectionObserver !== 'function'", observateur)
        self.assertIn("return false", observateur)
        self.assertIn("rootMargin: '400px'", observateur,
                      "le chargement à l'approche doit anticiper le défilement")

    def test_un_bouton_manuel_fait_le_meme_travail(self):
        self.assertIn('onclick="chargerComparaison()"', self.page)
        self.assertIn("Charger maintenant", self.page)
        self.assertIn("Charger maintenant", self.page, "le bouton doit être nommé en clair")

    def test_une_erreur_reseau_est_dite_et_non_recomposee(self):
        self.assertIn("Array.isArray(corps.comparaison)", self.bloc)
        rendre = self.bloc[self.bloc.index("function rendreComparaison("):]
        self.assertIn("n\\'a pas répondu", rendre)
        self.assertIn("/api/comparer", rendre)
        self.assertIn("plutôt que de ", rendre,
                      "la page doit dire l'absence au lieu de reconstituer des chiffres")

    # ── Le rangement : trois états, aucune valeur touchée ─────────────────
    def test_le_rangement_a_trois_etats(self):
        trier = self.bloc[self.bloc.index("function trierComparaison("):]
        trier = trier[:trier.index("\n}")]
        self.assertIn("SENS_TRI_COMPARAISON = 1", trier, "le premier clic range en croissant")
        self.assertIn("SENS_TRI_COMPARAISON = -1", trier, "le second clic inverse")
        self.assertIn("TRI_COMPARAISON = ''", trier, "le troisième rend l'ordre du catalogue")

    def test_le_rangement_est_annonce_aux_lecteurs_d_ecran(self):
        self.assertIn("aria-sort=", self.bloc)
        for sens in ("ascending", "descending", "none"):
            self.assertIn(sens, self.bloc, f"état de tri manquant : {sens}")
        self.assertIn("scope=\"col\"", self.bloc)
        self.assertIn("scope=\"row\"", self.bloc)

    def test_les_titres_de_colonne_sont_des_boutons(self):
        """Un titre cliquable doit être un bouton : sinon il n'existe pas au clavier."""
        self.assertIn('<button type="button" class="cmp-tri"', self.bloc)
        self.assertIn("#section-comparaison .cmp-tri{", self.style,
                      "le bouton de colonne doit être stylé comme cliquable")

    def test_les_colonnes_du_rendu_sont_celles_annoncees(self):
        self.assertIn("const colonnes = ['solde', 'dette', 'deficit', 'risque', 'alertes']",
                      self.bloc)
        for colonne in COLONNES:
            with self.subTest(colonne=colonne):
                self.assertIn(f"{colonne}:", self.bloc)
                self.assertIn(f"valeurComparaison(ligne, '{colonne}')", self.bloc)

    # ── Les barres : la couleur ne parle jamais seule ─────────────────────
    def test_les_barres_se_mesurent_sur_le_plus_fort_montant_servi(self):
        self.assertIn("function maximumSoldeComparaison(", self.bloc)
        self.assertIn("Math.max(plus, Math.abs(valeurComparaison(ligne, 'solde')))", self.bloc)
        rendre = self.bloc[self.bloc.index("function rendreComparaison("):]
        self.assertIn("const maximum = maximumSoldeComparaison(lignes);", rendre,
                      "l'échelle doit se calculer sur les lignes reçues, une fois par rendu")

    def test_la_barre_est_decorative_et_le_chiffre_ecrit(self):
        self.assertIn("aria-hidden=\"true\"", self.bloc)
        ligne = self.bloc[self.bloc.index("function ligneComparaisonHtml("):]
        self.assertIn("fmtSigne(solde, 1)", ligne, "le montant signé doit rester écrit")

    def test_les_deux_couleurs_viennent_de_la_charte(self):
        """Les variables sont cherchées dans les règles de **cette** section : les
        chercher dans la feuille entière laisserait passer deux hexadécimaux
        recopiés ici, puisque les mêmes variables servent ailleurs (sabotage vu)."""
        regles = "\n".join(re.findall(r"#section-comparaison[^\n{]*\{[^}]*\}", self.style))
        self.assertIn("var(--classe-recettes)", regles,
                      "la barre d'un solde positif doit prendre la teinte des recettes de la charte")
        self.assertIn("var(--classe-depenses)", regles,
                      "la barre d'un solde négatif doit prendre la teinte des dépenses de la charte")
        self.assertIn(".cmp-barre.negatif span", regles,
                      "un solde négatif doit changer de teinte, pas de disposition")

    def test_le_tableau_est_un_vrai_tableau(self):
        """Un tableau HTML est étiqueté et devient une carte au téléphone : pas une grille de div."""
        self.assertIn('<table class="cmp-table">', self.bloc)
        self.assertIn("<caption>", self.bloc)
        self.assertIn("</thead><tbody>", self.bloc)

    # ── Échappement et accès ──────────────────────────────────────────────
    def test_chaque_fonction_de_rendu_echappe_ce_qu_elle_affiche(self):
        for fonction in FONCTIONS_DE_RENDU:
            with self.subTest(fonction=fonction):
                corps = self.bloc[self.bloc.index(fonction):]
                corps = corps[:corps.index("\n}\n")]
                self.assertIn("echapperTexte(", corps,
                              f"{fonction} affiche du texte servi sans l'échapper")

    def test_le_libelle_du_scenario_est_echappe(self):
        ligne = self.bloc[self.bloc.index("function ligneComparaisonHtml("):]
        self.assertIn("echapperTexte(ligne.libelle)", ligne)

    def test_les_reperes_sont_designes_par_leur_cle(self):
        """Une clé ne change pas quand la formulation change : le repère suit la donnée."""
        ligne = self.bloc[self.bloc.index("function ligneComparaisonHtml("):]
        self.assertIn("ligne.cle === 'statut_quo'", ligne)
        self.assertIn("ligne.cle === 'mandature'", ligne)
        self.assertIn("référence (inertie)", ligne)

    def test_le_tableau_dit_que_ce_ne_sont_pas_les_reglages_du_lecteur(self):
        corps = self.page[self.page.index('id="comparaison-corps"'):]
        corps = corps[:corps.index("</section>")]
        self.assertIn("pas vos réglages", corps)

    def test_aucune_balise_ne_s_ouvre_dans_le_texte_de_la_section(self):
        section = self.page[self.page.index('id="section-comparaison"'):]
        section = section[:section.index("</section>")]
        for balise in re.findall(r"<(img|script|svg)\b", section):
            self.fail(f"balise ouverte dans la section : <{balise}")

    def test_la_legende_dit_ce_que_les_colonnes_mesurent(self):
        section = self.page[self.page.index('id="section-comparaison"'):]
        section = section[:section.index("</section>")]
        for mot in ("solde des mesures", "dette", "déficit", "risque population", "alertes"):
            with self.subTest(mot=mot):
                self.assertIn(mot, section.lower())

    def test_la_section_tient_au_palier_de_640_px(self):
        media = self.style[self.style.index("@media screen and (max-width:640px){\n  #section-comparaison"):]
        self.assertIn("#section-comparaison .cmp-barre", media,
                      "le palier de 640 px doit garder la barre lisible")

    def test_le_plancher_de_lisibilite_est_respecte(self):
        """Aucune taille de texte de la section n'est écrite en dur : le plancher s'applique."""
        for regle in re.findall(r"#section-comparaison[^\n{]*\{[^}]*\}", self.style):
            for taille in re.findall(r"font-size:([^;}]+)", regle):
                with self.subTest(regle=regle[:40]):
                    self.assertTrue(taille.startswith("max(var(--t-min)") or taille.endswith("rem"),
                                    f"taille de texte hors plancher : {taille}")

    def test_la_docstring_du_module_annonce_la_section(self):
        doc = simulateur_interface.__doc__ or ""
        self.assertIn("comparaison des préréglages", doc)
        self.assertIn("/api/comparer", doc)


class TestLeDocumentSuitLeCode(unittest.TestCase):
    """Le document de la passe annonce le nombre de contrôles de ce fichier.

    C'est la même discipline que le budget de poids : un document qui annonce
    « trente contrôles » se périme au premier contrôle ajouté, et personne ne
    relit un chiffre écrit à la main. Ici, c'est le chiffre qui suit le fichier.
    """

    DOCUMENT = "docs/RD_COMPARER_LES_SCENARIOS.md"

    def test_le_document_annonce_le_nombre_de_controles_du_fichier(self):
        suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
        nombre = suite.countTestCases()
        texte = (RACINE / self.DOCUMENT).read_text(encoding="utf-8")
        self.assertIn(f"{nombre} contrôles", texte,
                      f"{self.DOCUMENT} doit annoncer {nombre} contrôles "
                      f"(le fichier en compte {nombre})")


if __name__ == "__main__":
    unittest.main()
