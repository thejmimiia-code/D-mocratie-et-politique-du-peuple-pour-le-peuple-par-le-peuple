"""tests/test_contrepouvoirs_en_page.py — ce que la section doit tenir, comme texte.

La section « Contre-pouvoirs, en chiffres » a été ajoutée à la page parce que le
moteur servait deux registres entiers — `/api/contrepouvoirs` et
`/api/dynamiques` — que rien n'affichait. Le parcours JavaScript
(`tests/test_interface_navigateur.py`) exécute la section pour de vrai : il
compte les fiches rendues, compose une coalition et vérifie qu'un registre
hostile ne fait pas passer une balise. Ici, on contrôle ce qui reste vrai quand
on lit la page comme un texte : la section existe, le sommaire y mène, elle
demande bien les deux routes, elle ne recopie aucun chiffre, elle ne coûte rien
au démarrage, et chaque fiche échappe ce qu'elle affiche.
"""

from __future__ import annotations

import re
import unittest

from simulateur import interface as simulateur_interface
from simulateur.interface import HTML_PAGE

#: Le bloc de la section dans le JavaScript : du premier état au rendu des
#: verrous, qui le suit immédiatement dans la page.
DEBUT_BLOC = "let CONTREPOUVOIRS = null;"
FIN_BLOC = "function renderReglagesTouches(){"

#: Les chiffres du droit positif que la page n'écrit jamais elle-même : ils
#: viennent du serveur, sinon ils vieilliraient ici à l'insu de tout le monde.
CHIFFRES_INTERDITS = ("289", "577", "347", "385", "116", "348", "175", "209", "232")

#: Les fonctions qui composent une fiche : chacune échappe ce qu'elle affiche.
FONCTIONS_DE_FICHE = (
    "function chambreEnChiffres(", "function mecanismeEnChiffres(",
    "function trajetEnChiffres(", "function fenteEnChiffres(",
    "function strategieEnChiffres(", "function instanceEnChiffres(",
    "function boucleEnChiffres(", "function rendreArithmetique(",
    "function rendreTempsProcedures(",
)


class TestLaSectionDesContrePouvoirs(unittest.TestCase):
    """Contrôles statiques de la section, sur la page servie."""

    @classmethod
    def setUpClass(cls):
        cls.page = HTML_PAGE
        cls.style = cls.page[cls.page.index("<style>") + len("<style>"):cls.page.index("</style>")]
        debut = cls.page.index(DEBUT_BLOC)
        cls.bloc = cls.page[debut:cls.page.index(FIN_BLOC, debut)]

    # ── Elle est là, et on peut y aller ───────────────────────────────────
    def test_la_section_existe_avec_son_ancre(self):
        self.assertIn('id="section-contrepouvoirs"', self.page)
        self.assertIn('id="contrepouvoirs-corps"', self.page)
        self.assertIn('id="contrepouvoirs-resume"', self.page)

    def test_le_sommaire_y_mene(self):
        """Une section sans entrée au sommaire est une section qu'on ne trouve pas."""
        self.assertIn('href="#section-contrepouvoirs"', self.page)
        entree = self.page[self.page.index('href="#section-contrepouvoirs"'):]
        self.assertIn("Contre-pouvoirs", entree[:400])

    def test_la_section_dit_d_ou_viennent_ses_chiffres(self):
        """L'entête nomme les deux routes : le lecteur peut les appeler lui-même."""
        entete = self.page[self.page.index('id="section-contrepouvoirs"'):]
        entete = entete[:entete.index("</h2>")]
        self.assertIn("/api/contrepouvoirs", entete)
        self.assertIn("/api/dynamiques", entete)

    # ── Ce qu'elle demande au serveur ─────────────────────────────────────
    def test_la_page_demande_les_deux_registres(self):
        self.assertIn("await Promise.all([", self.bloc)
        self.assertIn("fetch('/api/contrepouvoirs')", self.bloc)
        self.assertIn("fetch('/api/dynamiques')", self.bloc)

    def test_une_reponse_absente_ne_devient_pas_un_chiffre(self):
        """Sans réponse, la section dit l'absence : elle ne recompose rien.

        C'est la règle de la page pour l'audit et pour les verrous ; elle vaut
        ici, où un chiffre inventé se lirait comme un chiffre du droit.
        """
        self.assertTrue("pas répondu" in self.bloc,
                        "aucune fiche ne dit l'absence quand le registre ne répond pas")
        self.assertTrue("la page affiche cette absence plutôt que de reconstituer" in self.bloc,
                        "l'absence de réponse n'est pas présentée comme telle")

    # ── Elle ne recopie rien ──────────────────────────────────────────────
    def test_aucun_seuil_du_droit_positif_n_est_recopie_dans_la_page(self):
        """Les majorités des chambres viennent du serveur, jamais du source.

        Un seuil recopié ici serait juste le jour où il est écrit, et faux le
        jour où le registre change — sans que rien ne le signale.
        """
        for chiffre in CHIFFRES_INTERDITS:
            self.assertNotIn(chiffre, self.bloc,
                             f"seuil {chiffre} recopié dans la page : il doit venir du serveur")

    def test_aucun_nom_de_formation_n_est_recopie_dans_la_page(self):
        """Les groupes parlementaires sont servis, pas écrits en dur."""
        for sigle in ("'RN'", '"RN"', "'EPR'", "'LFI-NFP'", "'SOC'"):
            self.assertNotIn(sigle, self.bloc)

    def test_la_composition_des_chambres_est_lue_du_serveur(self):
        self.assertIn("donnees.assemblees", self.bloc)
        self.assertIn("chambre.groupes", self.bloc)

    # ── Ce qu'elle ne fait pas au démarrage ───────────────────────────────
    def test_la_section_ne_se_charge_pas_au_demarrage(self):
        """Deux cents kilo-octets ne se paient pas pour un bloc lu plus bas."""
        debut = self.page.index("(async function demarrer(){")
        corps = self.page[debut:debut + 4000]
        self.assertIn("observerContrepouvoirs();", corps)
        self.assertNotIn("await chargerContrepouvoirs();", corps)

    def test_un_bouton_permet_de_la_charger_a_la_main(self):
        """Sans observateur (ou s'il n'a pas fonctionné), le bouton fait le travail."""
        entete = self.page[self.page.index('id="section-contrepouvoirs"'):]
        entete = entete[:entete.index("</section>")]
        self.assertIn('onclick="chargerContrepouvoirs()"', entete)

    def test_l_observateur_ne_casse_rien_quand_il_manque(self):
        """Un navigateur sans `IntersectionObserver` garde une page qui marche."""
        debut = self.bloc.index("function observerContrepouvoirs(){")
        observateur = self.bloc[debut:]
        self.assertIn("typeof IntersectionObserver !== 'function'", observateur)
        self.assertIn("return false", observateur)
        self.assertIn("disconnect()", observateur)

    # ── Échappement, et forme ─────────────────────────────────────────────
    def test_chaque_fiche_echappe_ce_qu_elle_affiche(self):
        """Une fiche qui n'échappe rien est une fiche qui laisse passer du balisage.

        Le parcours JavaScript le prouve sur un registre hostile ; ce contrôle
        tient la règle pour toute fiche ajoutée ensuite.
        """
        for fonction in FONCTIONS_DE_FICHE:
            debut = self.bloc.index(fonction)
            suivante = self.bloc.find("\nfunction ", debut + 1)
            corps = self.bloc[debut:suivante if suivante > 0 else len(self.bloc)]
            self.assertIn("echapperTexte(", corps,
                          f"{fonction} n'échappe aucun texte du registre")

    def test_les_registres_ne_sont_pas_dumping_de_json(self):
        """Un champ inconnu se montre en puces, jamais en JSON brut."""
        self.assertIn("function champTexteHtml(", self.bloc)
        self.assertNotIn("JSON.stringify", self.bloc,
                         "un registre ne se déverse pas en JSON dans la page")

    def test_les_pastilles_de_filtre_sont_des_boutons_pressables(self):
        """`aria-pressed` dit l'état : un filtre actif ne se voit pas qu'à la couleur."""
        self.assertIn('class="cp-famille"', self.bloc)
        self.assertIn('aria-pressed="', self.bloc)
        self.assertIn("function filtrerContrepouvoirs(", self.bloc)
        self.assertIn("function basculerGroupeParlementaire(", self.bloc)

    def test_la_section_a_son_palier_de_640_px(self):
        """Les deux chambres passent l'une sous l'autre sur un téléphone."""
        regles = self.style[self.style.index("#section-contrepouvoirs"):]
        paliers = [regle for regle in re.findall(r"@media screen and \(max-width:640px\)\{[^@]*?\n\}",
                                                 self.style)
                   if "#section-contrepouvoirs" in regle]
        self.assertTrue(paliers, "aucun palier de 640 px pour la section")
        self.assertIn("grid-template-columns:1fr", paliers[0])
        self.assertIn("#section-contrepouvoirs", regles)

    def test_les_teintes_des_formations_ne_sont_pas_ecrites_a_la_main(self):
        """Une teinte par formation, calculée : douze couleurs ne se recopient pas."""
        self.assertIn("function teinteGroupe(", self.bloc)
        self.assertIn("hsl(var(--teinte),58%,52%)", self.style)
        self.assertIn("--teinte:", self.bloc)

    def test_la_description_du_module_annonce_la_section(self):
        """Le document qui décrit la page dit ce que la page contient."""
        entete = simulateur_interface.__doc__ or ""
        self.assertIn("contre-pouvoirs en chiffres", entete)
        self.assertIn("/api/contrepouvoirs", entete)
        self.assertIn("/api/dynamiques", entete)


if __name__ == "__main__":
    unittest.main()
