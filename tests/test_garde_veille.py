"""
tests/test_garde_veille.py — le garde-veille : ce qu'il fait, et ce qu'il tait.

La veille hebdomadaire dit si les adresses publiques répondent. Elle ne peut pas
empêcher la copie de secours de **s'endormir** : l'offre gratuite de Render
endort un service après une quinzaine de minutes sans visite, le visiteur suivant
attend une trentaine de secondes, et quand le réveil échoue il tombe sur la page
d'erreur de l'hébergeur — le **502** du 14 octobre 2026.

Le garde-veille frappe donc à la porte toutes les dix minutes pendant les heures
de consultation. Ce fichier tient les quatre promesses de ce rendez-vous :

1. **la fenêtre tient dans ce que le palier gratuit offre** — un dépassement ne
   facture pas, il **suspend** les services, ce qui est pire que le sommeil ;
2. **une visite insiste, mais pas indéfiniment** — un réveil prend une trentaine
   de secondes, et une visite abandonnée trop tôt ferait passer un réveil pour
   une panne ;
3. **il ne parle que quand l'état change** — un garde-veille qui commente
   toutes les dix minutes est un garde-veille qu'on coupe ;
4. **il ne confond ni un 502, ni une page de parking, ni le silence avec une
   application vivante.**
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from outils.chargement_module import charger_module  # noqa: E402
from simulateur import surface_publique as surface  # noqa: E402

GARDE = charger_module("garde_veille", RACINE / "outils" / "garde-veille.py")
WORKFLOW = RACINE / ".github" / "workflows" / "garde-veille.yml"
VEILLE = RACINE / ".github" / "workflows" / "veille-en-ligne.yml"
HEBERGEMENT = RACINE / "docs" / "HEBERGEMENT.md"


def _faux_hote(script: list) -> tuple:
    """Un hôte docile : rend les réponses du script, dans l'ordre.

    Chaque élément de `script` est un `Reponse` ou le mot ``"gel"`` pour un hôte
    muet. Le compte des appels est rendu à l'appelant, parce que « combien de
    fois a-t-on insisté ? » est justement ce qu'on veut vérifier.
    """
    appels: list[str] = []
    restantes = list(script)

    def demander(url: str, delai: float = 45.0):
        appels.append(url)
        reponse = restantes.pop(0) if len(restantes) > 1 else restantes[0]
        if reponse == "gel":
            return GARDE.Reponse(0, "", b"URLError: connection closed")
        return reponse

    return demander, appels


def _lexique() -> object:
    """Ce que sert vraiment notre application : du JSON, avec ses deux clés."""
    return GARDE.Reponse(200, "application/json; charset=utf-8",
                         json.dumps({"termes": [{"cle": "pib"}], "categories": []}).encode())


class TestLaFenetreTientDansLePalierGratuit(unittest.TestCase):
    """Le calendrier de GitHub parle en temps universel ; notre palier, en heures."""

    def test_la_fenetre_annoncee_est_celle_du_calendrier(self):
        """Le calendrier (imposé en clair) et la variable lue doivent dire pareil.

        GitHub n'accepte pas de variable dans `schedule:` : la fenêtre est donc
        écrite deux fois — et deux écritures qui divergent donneraient un
        contrôle qui valide une fenêtre, et un rendez-vous qui en suit une autre.
        """
        texte = WORKFLOW.read_text(encoding="utf-8")
        calendrier = re.search(r'schedule:\s*\n\s*-\s*cron:\s*"([^"]+)"', texte)
        variable = re.search(r'^\s*FENETRE:\s*"([^"]+)"', texte, re.MULTILINE)
        self.assertIsNotNone(calendrier, "le workflow n'a pas de calendrier")
        self.assertIsNotNone(variable, "la fenêtre n'est pas déclarée en variable")
        self.assertEqual(calendrier.group(1), variable.group(1),
                         "la fenêtre du calendrier et celle du contrôle divergent")
        self.assertIn('--cron "$FENETRE"', texte,
                      "la fenêtre n'est pas vérifiée avant de servir")

    def test_la_fenetre_couvre_les_heures_de_consultation(self):
        analyse = GARDE.Analyse("*/10 5-22 * * *")
        self.assertEqual(analyse.passages_par_jour, 108)
        hiver, ete = analyse.couverture_locale(1), analyse.couverture_locale(2)
        self.assertEqual(hiver, (6, 23), "la fenêtre d'hiver n'est pas 6 h → 23 h")
        self.assertEqual(ete, (7, 24), "la fenêtre d'été n'est pas 7 h → minuit")

    def test_un_depassement_est_refuse(self):
        """Le palier gratuit **suspend** au-delà du quota : pire que le sommeil."""
        jour = GARDE.Analyse("*/10 5-22 * * *")
        nuit = GARDE.Analyse("*/10 * * * *")
        self.assertFalse(jour.depasse)
        self.assertTrue(nuit.depasse, "une fenêtre 24 h/24 doit être refusée")
        self.assertLess(jour.heures_par_mois, GARDE.HEURES_OFFERTES)

    def test_le_changement_d_heure_est_dans_le_calcul(self):
        """La France change d'heure : une même fenêtre UTC ne couvre pas pareil."""
        analyse = GARDE.Analyse("*/10 5-22 * * *")
        self.assertEqual(analyse.couverture_locale(2)[0] - analyse.couverture_locale(1)[0], 1)
        self.assertIn("été", GARDE.texte_analyse(analyse))

    def test_une_expression_illisible_est_refusee(self):
        for mauvaise in ("*/10 5-22", "*/10 25-30 * * *", "*/0 5-22 * * *"):
            with self.subTest(cron=mauvaise):
                with self.assertRaises(ValueError):
                    GARDE.Analyse(mauvaise)

    def test_la_ligne_de_commande_le_dit_et_sort_en_erreur(self):
        """Le contrôle sert dans une étape de CI : son code de sortie compte."""
        ancien = sys.argv
        try:
            sys.argv = ["garde-veille", "--cron", "*/10 * * * *"]
            self.assertEqual(GARDE.main(), 1, "une fenêtre trop large doit faire échouer l'étape")
            sys.argv = ["garde-veille", "--cron", "n'importe quoi"]
            self.assertEqual(GARDE.main(), 2, "une expression illisible doit être signalée")
        finally:
            sys.argv = ancien


class TestLaVisite(unittest.TestCase):
    """Réveiller, c'est insister — mais savoir s'arrêter."""

    def test_un_hote_deja_eveille_est_visite_une_seule_fois(self):
        demander, appels = _faux_hote([_lexique()])
        verdict = GARDE.visiter("https://exemple.test/", essais=3, attente=0.0, demander=demander)
        self.assertTrue(verdict.reussi)
        self.assertEqual(len(appels), 1, "un hôte éveillé ne doit pas être sondé trois fois")
        self.assertFalse(verdict.reveil, "un hôte éveillé n'est pas « réveillé »")

    def test_un_hote_endormi_qui_se_leve_est_reconnu(self):
        """Deux essais : le service s'endormait, il a fallu frapper deux fois."""
        demander, appels = _faux_hote(["gel", _lexique()])
        verdict = GARDE.visiter("https://exemple.test/", essais=3, attente=0.0, demander=demander)
        self.assertTrue(verdict.reussi)
        self.assertEqual(len(appels), 2)
        self.assertTrue(verdict.reveil, "un réveil doit être dit : c'est l'information utile")
        self.assertIn("réveillée", verdict.detail)

    def test_la_page_d_attente_de_l_hebergeur_n_est_pas_une_reponse(self):
        """« Application loading » : l'hôte se lève, ce n'est pas encore l'app."""
        attente = GARDE.Reponse(200, "text/html; charset=utf-8",
                                b"<html><body>Application loading</body></html>")
        demander, appels = _faux_hote([attente, _lexique()])
        verdict = GARDE.visiter("https://exemple.test/", essais=3, attente=0.0, demander=demander)
        self.assertTrue(verdict.reussi)
        self.assertEqual(len(appels), 2)

    def test_un_502_est_dit_pour_ce_qu_il_est(self):
        """La passerelle sans service : le dire, plutôt que « attendu 200, reçu 502 »."""
        passerelle = GARDE.Reponse(502, "text/html; charset=utf-8",
                                   b"<html><body>502 Bad Gateway</body></html>")
        demander, _ = _faux_hote([passerelle])
        verdict = GARDE.visiter("https://exemple.test/", essais=3, attente=0.0, demander=demander)
        self.assertFalse(verdict.reussi)
        self.assertIn("passerelle", verdict.detail)
        self.assertIn("502", verdict.detail)

    def test_le_silence_ne_leve_pas_d_exception(self):
        """Un hôte muet est un **résultat**, pas une raison de tout arrêter."""
        demander, appels = _faux_hote(["gel"])
        verdict = GARDE.visiter("https://exemple.test/", essais=3, attente=0.0, demander=demander)
        self.assertFalse(verdict.reussi)
        self.assertIn("aucune réponse", verdict.detail)
        self.assertEqual(len(appels), 3, "le silence mérite qu'on insiste")

    def test_insister_s_arrete(self):
        """Trois essais demandés : trois essais, pas quatre."""
        demander, appels = _faux_hote(["gel"])
        GARDE.visiter("https://exemple.test/", essais=3, attente=0.0, demander=demander)
        self.assertEqual(len(appels), 3)

    def test_un_200_qui_n_est_pas_notre_application_est_refuse(self):
        """Un voisin qui répond 200 ne doit pas passer pour notre moteur."""
        cas = {
            "une page": GARDE.Reponse(200, "text/html", b"<html>Bienvenue</html>"),
            "un autre service": GARDE.Reponse(200, "application/json", b'{"ok": true}'),
            "du JSON tronque": GARDE.Reponse(200, "application/json", b'{"termes": [ '),
            "du JSON nu": GARDE.Reponse(200, "application/json", b"[]"),
        }
        for nom, reponse in cas.items():
            with self.subTest(cas=nom):
                demander, _ = _faux_hote([reponse])
                verdict = GARDE.visiter("https://exemple.test/", essais=1, attente=0.0,
                                        demander=demander)
                self.assertFalse(verdict.reussi, f"{nom} a passé pour notre application")

    def test_un_non_200_qui_ressemble_a_notre_json_est_refuse(self):
        """Un 502 peut très bien transporter du JSON bien formé.

        Le contrôle porte sur le **statut** autant que sur la forme : sans cela,
        une passerelle qui renvoie une erreur en JSON — cas courant — passerait
        pour une application vivante, et le garde-veille se tairait au moment
        précis où il fallait parler.
        """
        for statut in (500, 502, 503):
            with self.subTest(statut=statut):
                deguise = GARDE.Reponse(statut, "application/json",
                                        json.dumps({"termes": [], "categories": []}).encode())
                demander, _ = _faux_hote([deguise])
                verdict = GARDE.visiter("https://exemple.test/", essais=1, attente=0.0,
                                        demander=demander)
                self.assertFalse(verdict.reussi, f"un {statut} en JSON a passé pour notre application")

    def test_la_porte_frappee_est_celle_de_la_sonde_de_l_hebergeur(self):
        """`render.yaml` déclare la même adresse comme sonde de disponibilité."""
        demander, appels = _faux_hote([_lexique()])
        GARDE.visiter("https://exemple.test/", essais=1, attente=0.0, demander=demander)
        self.assertEqual(appels, [f"https://exemple.test{GARDE.SONDE}"])
        render = (RACINE / "render.yaml").read_text(encoding="utf-8")
        # Comparaison **exacte**, pas par sous-chaîne : « healthCheckPath: / »
        # est contenu dans « healthCheckPath: /api/lexique », et avalait donc
        # son propre sabotage (vu le 15 octobre 2026).
        trouve = re.search(r"^\s*healthCheckPath:\s*(\S+)\s*$", render, re.MULTILINE)
        self.assertIsNotNone(trouve, "render.yaml ne déclare plus de sonde")
        self.assertEqual(trouve.group(1), GARDE.SONDE,
                         "la sonde du garde-veille n'est plus celle de l'hébergeur")

    def test_la_cible_par_defaut_est_la_copie_de_secours(self):
        """Les adresses vivent dans un seul fichier : `surface_publique`."""
        self.assertEqual(GARDE.SECOURS, surface.HOTE_SECOURS)
        self.assertNotIn("onrender.com", WORKFLOW.read_text(encoding="utf-8"))
        self.assertNotIn("onrender.com", Path(GARDE.__file__).read_text(encoding="utf-8"))


class TestIlNeParleQueQuandCaChange(unittest.TestCase):
    """Dix minutes de silence valent mieux qu'un commentaire toutes les dix minutes."""

    def _verdict(self, reussi: bool):
        return GARDE.Verdict(reussi, "peu importe", 0.1, 1)

    def test_les_six_cas(self):
        cas = [
            ("", True, False, "un premier passage silencieux : personne n'a besoin de savoir"),
            ("", False, True, "la panne se dit"),
            (GARDE.MARQUE_OK, True, False, "tout va bien depuis un moment : se taire"),
            (GARDE.MARQUE_OK, False, True, "la panne se dit, après une période normale"),
            (GARDE.MARQUE_PANNE, True, True, "le retour à la normale se dit aussi"),
            (GARDE.MARQUE_PANNE, False, False, "la panne en cours ne se répète pas"),
        ]
        for precedent, reussi, attendu, raison in cas:
            with self.subTest(precedent=precedent or "(aucun)", reussi=reussi):
                verdict = self._verdict(reussi)
                self.assertEqual(GARDE.faut_il_publier(precedent, verdict), attendu, raison)

    def test_le_marqueur_porte_l_etat(self):
        """Rien à stocker : l'état est dans le marqueur lui-même."""
        panne = GARDE.Verdict(False, "ça ne répond pas").marqueur
        ok = GARDE.Verdict(True, "ça répond").marqueur
        self.assertNotEqual(panne, ok)
        self.assertEqual(GARDE.marqueur_du_texte(f"{panne}\n\n## Garde-veille"), panne)
        self.assertEqual(GARDE.marqueur_du_texte(f"{ok}\n\n## Garde-veille"), ok)
        self.assertEqual(GARDE.marqueur_du_texte("aucun marqueur ici"), "")

    def test_le_compte_rendu_ne_ment_pas(self):
        rate = GARDE.rapport_visite(self._verdict(False), "https://exemple.test/")
        bon = GARDE.rapport_visite(self._verdict(True), "https://exemple.test/")
        self.assertIn("ne répond pas", rate)
        self.assertIn("✗", rate)
        self.assertNotIn("ne répond pas", bon)
        self.assertIn("éveillée", bon)
        for texte in (rate, bon):
            self.assertIn(f"https://exemple.test{GARDE.SONDE}", texte)

    def test_il_n_ecrit_rien_dans_le_depot(self):
        """Le rapport va où on le demande — jamais dans un fichier du dépôt."""
        import tempfile

        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "sous" / "garde.md"
            ecrits = GARDE.ecrire("## Garde-veille\n\n✓ tout\n", [str(chemin)])
            self.assertIn(chemin, ecrits)
            self.assertIn("Garde-veille", chemin.read_text(encoding="utf-8"))
        self.assertFalse(list(RACINE.glob("garde*.md")))

    def test_l_etat_est_lisible_par_une_machine(self):
        """Le workflow ne prend aucune décision : il lit `publier=oui|non`."""
        texte = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('grep -E \'^etat=\' /tmp/garde.txt', texte)
        self.assertIn('echo "etat=${etat:-inconnu}"', texte,
                      "un garde-veille muet laisserait l'état vide")
        self.assertIn("steps.visite.outputs.publier == 'oui'", texte,
                      "le workflow publierait à chaque passage")

    def test_l_etape_du_ping_ne_s_arrete_pas_avant_d_ecrire_ses_sorties(self):
        """`run:` est exécuté avec `bash -e` : un ping raté avorterait le script.

        Et l'avortement aurait lieu **avant** l'écriture des sorties — donc au
        moment précis où il faut publier (l'hôte ne répond pas), rien ne serait
        publié. `set +e` est la ligne qui empêche cela.
        """
        texte = WORKFLOW.read_text(encoding="utf-8")
        bloc = texte[texte.index("id: visite"):texte.index("Publier seulement")]
        # **Commentaires retirés** avant de juger : le commentaire qui explique
        # `set +e` contient ces quatre caractères, et le contrôle lisait donc sa
        # propre explication au lieu du code — il avalait son sabotage.
        bloc = "\n".join(ligne for ligne in bloc.splitlines()
                         if not ligne.strip().startswith("#"))
        self.assertIn("set +e", bloc, "le ping peut avorter avant d'écrire son état")
        self.assertNotIn("exit $code", bloc, "un code de sortie ferait rougir le dépôt")
        self.assertLess(bloc.index("set +e"), bloc.index("garde-veille.py --ping"),
                        "`set +e` doit précéder l'appel, pas le suivre")
        self.assertLess(bloc.index("garde-veille.py --ping"), bloc.index("GITHUB_OUTPUT"),
                        "les sorties doivent être écrites **après** le ping")

    def test_l_etat_est_dans_le_nom_de_l_etape(self):
        """Le journal d'un run ne se télécharge pas : le nom de l'étape, si."""
        self.assertIn('name: "Conclure — ${{ steps.visite.outputs.etat }}"',
                      WORKFLOW.read_text(encoding="utf-8"))


class TestLeRendezVous(unittest.TestCase):
    """Ce que le workflow doit et ne doit pas faire."""

    @classmethod
    def setUpClass(cls):
        cls.texte = WORKFLOW.read_text(encoding="utf-8")

    def test_il_est_planifie_manuel_et_declenche_par_toute_poussee(self):
        """Trois déclencheurs, et le troisième est la leçon du 15 octobre 2026.

        Le calendrier de GitHub n'avait livré aucun passage une heure après la
        fusion : le réveil ne peut pas reposer sur lui seul. Toute poussée en
        est un second — et il ne doit porter **aucun filtre**, sinon une fusion
        ordinaire le manquerait.
        """
        self.assertIn("schedule:", self.texte)
        self.assertIn("workflow_dispatch:", self.texte)
        self.assertRegex(self.texte, r"\n  push:\n",
                         "le rendez-vous doit réagir à toute poussée")
        bloc = self.texte[self.texte.index("\n  push:\n"):self.texte.index("permissions:")]
        self.assertNotIn("branches-ignore", bloc,
                         "un filtre ferait manquer la poussée d'une fusion")
        self.assertNotIn("paths:", bloc,
                         "un filtre ferait manquer la poussée d'une fusion")

    def test_il_a_le_droit_de_commenter(self):
        self.assertIn("issues: write", self.texte)

    def test_il_ne_fait_pas_rougir_le_depot_pour_un_service_d_appoint(self):
        """Un rendez-vous toutes les dix minutes ne doit pas crier à chaque fois.

        Le code de sortie du garde-veille est **dit**, jamais propagé : un dépôt
        rouge toutes les dix minutes pour un service d'appoint serait un dépôt
        qu'on cesse de regarder. C'est la veille hebdomadaire qui juge — et
        seulement l'adresse canonique.
        """
        bloc = self.texte[self.texte.index("id: visite"):self.texte.index("Publier seulement")]
        self.assertNotIn("exit 1", bloc)
        self.assertNotIn("exit $code", bloc)
        self.assertIn("code de sortie du garde-veille", bloc,
                      "le code doit être dit, pas propagé")
        self.assertNotIn("✗ canonique", self.texte,
                         "le garde-veille n'est pas juge de l'adresse canonique")

    def test_il_n_ecrit_rien_dans_le_depot(self):
        self.assertIn("permissions:", self.texte)
        self.assertIn("contents: read", self.texte)
        self.assertNotIn("contents: write", self.texte)

    def test_sa_page_n_est_pas_celle_de_la_veille(self):
        """Deux rendez-vous, deux pages : sinon ils se réécriraient mutuellement."""
        titre = re.search(r'^\s*PAGE:\s*"([^"]+)"', self.texte, re.MULTILINE).group(1)
        veille = VEILLE.read_text(encoding="utf-8")
        self.assertNotIn(titre, veille)
        self.assertIn("Garde-veille", titre)
        self.assertIn("veille-en-ligne", veille)
        self.assertNotIn("garde-veille:", veille)

    def test_le_commentaire_du_workflow_explique_la_fenetre(self):
        """Le fichier porte son propre mode d'emploi, en tête, avant le moindre `on:`."""
        entete = self.texte[:self.texte.index("\non:")]
        for mot in ("temps universel", "750", "suspend", "endort"):
            with self.subTest(mot=mot):
                self.assertIn(mot, entete, f"l'en-tête du workflow ne dit pas « {mot} »")


class TestLaDocumentationExpliqueLeRendezVous(unittest.TestCase):
    """Un rendez-vous qu'on ne comprend pas est un rendez-vous qu'on coupe."""

    @classmethod
    def setUpClass(cls):
        cls.doc = HEBERGEMENT.read_text(encoding="utf-8")

    def test_elle_nomme_le_garde_veille_et_son_calendrier(self):
        for mot in ("garde-veille", "toutes les dix minutes", "temps universel",
                    "750", "heures"):
            with self.subTest(mot=mot):
                self.assertIn(mot, self.doc, f"la documentation ne dit pas « {mot} »")

    def test_la_section_est_titree(self):
        """Un titre, pas seulement des mots qui traînent : c'est lui qu'on cherche."""
        self.assertIn("### Le garde-veille", self.doc)

    def test_elle_dit_les_deux_limites(self):
        """Ce qu'il ne peut pas faire : relever un service suspendu."""
        self.assertIn("suspendu", self.doc)
        self.assertIn("Garde-veille", self.doc)

    def test_elle_renvoie_au_fichier_du_rendez_vous(self):
        self.assertIn("garde-veille.yml", self.doc)

    def test_elle_dit_que_toute_poussee_reveille(self):
        """Le second déclencheur, et la raison : le calendrier peut être en retard."""
        self.assertIn("Toute poussée le déclenche aussi", self.doc)

    def test_elle_donne_la_porte_de_secours(self):
        """Le calendrier de GitHub est « au mieux » : une autre porte doit exister.

        Elle est faite d'une adresse et de deux services gratuits — et elle ne
        dépend ni de GitHub, ni d'un secret du dépôt.
        """
        self.assertIn("#### Une seconde porte, indépendante de GitHub", self.doc,
                      "la porte de secours n'a plus de section à elle")
        self.assertIn("cron-job.org", self.doc)
        self.assertIn("UptimeRobot", self.doc)
        self.assertIn("alerte", self.doc,
                      "une porte de secours qui ne prévient personne n'en est pas une")
        self.assertIn(f"{GARDE.SECOURS.rstrip('/')}{GARDE.SONDE}", self.doc,
                      "la seconde porte ne dit pas quelle adresse interroger")

    def test_elle_dit_ou_lire_l_etat(self):
        """Un nom d'étape se lit ; un journal de run ne se télécharge pas."""
        self.assertIn("Conclure — **ok**", self.doc)
        self.assertIn("nom d'étape se lit", self.doc,
                      "la documentation ne dit pas où lire l'état")

    def test_les_ancres_citees_existent_vraiment(self):
        """Un renvoi vers une section qui n'existe pas ne mène nulle part.

        Écrit après avoir écrit soi-même l'ancre fausse : le titre
        « Le garde-veille : empêcher le service de s'endormir » donne
        `#le-garde-veille--empêcher-…` — **deux** tirets, parce que GitHub
        remplace l'espace avant *et* après le deux-points. L'ancre est donc
        calculée, pas devinée.
        """
        titres = {self._ancre(titre) for titre in
                  re.findall(r"^#{2,4}\s+(.*)$", self.doc, re.MULTILINE)}
        cites = []
        for fichier in list((RACINE / "docs").glob("*.md")) + [RACINE / "CHANGELOG.md",
                                                              RACINE / "docs" / "README.md"]:
            texte = fichier.read_text(encoding="utf-8")
            for lien in re.findall(r"HEBERGEMENT\.md#([^)\s]+)", texte):
                cites.append((fichier.name, lien))
        self.assertTrue(cites, "plus aucun renvoi vers la documentation d'hébergement ?")
        for nom, lien in cites:
            with self.subTest(fichier=nom, ancre=lien):
                self.assertIn(lien, titres, f"{nom} renvoie vers une section inexistante")

    @staticmethod
    def _ancre(titre: str) -> str:
        """L'ancre GitHub d'un titre : minuscules, ponctuation retirée, espaces en tirets."""
        sans_ponctuation = re.sub(r"[^\w\s-]", "", titre.strip().lower(), flags=re.UNICODE)
        return sans_ponctuation.replace(" ", "-")


if __name__ == "__main__":
    unittest.main()
