"""La veille en ligne : ce qu'elle doit couvrir, et ce qu'elle doit voir.

`outils/verifier-surface-en-ligne.py` interroge les deux adresses publiées. Ce
fichier, lui, ne les interroge pas : il serait rouge dès que l'hébergeur s'endort
ou que le réseau du poste est coupé, ce qui n'apprend rien sur le dépôt.

Il vérifie trois choses, hors ligne :

1. **La veille ne peut pas prendre du retard sur le moteur** — toute route
   servie par le serveur doit être sondée, ou écartée avec sa raison écrite.
   Sans cela, une route ajoutée aujourd'hui serait silencieusement absente de la
   veille de demain ;
2. **Ses épreuves reconnaissent un vrai succès** — un hébergeur docile fait
   passer toutes les épreuves, ce qui prouve qu'elles ne sont pas impossibles ;
3. **Ses épreuves attrapent une panne** — texte tronqué, page sans canonique,
   route disparue, hébergeur qui répond 200 en racontant qu'il démarre : chacun
   doit produire un échec précis. Un contrôle qui ne sait pas échouer ne
   contrôle rien.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from outils.chargement_module import charger_module  # noqa: E402
from simulateur import surface_publique as surface  # noqa: E402

CHEMIN = RACINE / "outils" / "verifier-surface-en-ligne.py"


def charger_veille() -> object:
    """Importe le script (son nom porte des tirets, donc pas d'import normal).

    Sans cache de bytecode : un script modifié de la même longueur dans la même
    seconde doit être relu — voir `outils/chargement_module.py`.
    """
    return charger_module("verifier_surface_en_ligne", CHEMIN)


def routes_du_serveur(methode: str) -> set[str]:
    """Les routes servies par `dashboard.py`, lues dans sa source.

    Le contrôle part de la source et non d'une liste écrite ici : c'est le
    serveur qui fait foi, et une route qu'il sert sans être sondée est
    exactement le trou que ce fichier doit rendre visible.
    """
    source = (RACINE / "simulateur" / "dashboard.py").read_text(encoding="utf-8")
    suite = source[source.index(f"def do_{methode}") + 10:]
    suivantes = [suite.find(motif) for motif in ("\n    def ", "\ndef ")]
    fin = min((index for index in suivantes if index != -1), default=len(suite))
    return set(re.findall(r'chemin == "(/api/[a-z_]+)"', suite[:fin]))


class FauxReseau:
    """Un hébergeur docile : tout répond juste, sauf ce qu'on sabote."""

    def __init__(self, veille: object, sabote: dict[str, str] | None = None,
                 une_fois: list[str] | None = None, hics: list[str] | None = None) -> None:
        self.veille = veille
        self.sabote = sabote or {}
        #: Routes qui répondent 502 **une fois**, puis juste. C'est la forme du
        #: 502 mesuré le 15 octobre 2026 : la copie de secours redéployait, une
        #: seule de ses soixante-huit adresses est tombée, et dans la seconde.
        self.hics = set(hics or ())
        #: Chemins sabotés **une seule fois** : le premier appel est faux, les
        #: suivants sont justes. C'est la forme d'un déploiement en vol — la
        #: première page servie est celle d'avant, la deuxième est la bonne.
        self.une_fois = set(une_fois or ())
        self.appels: list[str] = []

    def __call__(self, url: str, methode: str = "GET",
                 corps: dict[str, object] | None = None, delai: float = 30.0) -> object:
        self.appels.append(f"{methode} {url}")
        reponse = self.veille.Reponse
        chemin = "/" + url.split("/", 3)[3].split("?", 1)[0] if url.count("/") >= 3 else "/"
        if self.sabote.get("muet"):
            # Ni statut, ni en-têtes : l'hôte n'a **rien** répondu. C'est ce que
            # voit un coureur dont l'hôte est suspendu, ou dont la sortie réseau
            # est fermée — la passerelle répond 502, mais le TLS se coupe avant.
            return reponse(0, "", b"URLError: connection closed")
        if self.sabote.get("panne"):
            # La passerelle répond, mais personne derrière : le 502 d'un service
            # suspendu. C'est un verdict, pas un réveil — il ne s'attend pas.
            return reponse(502, "text/html; charset=utf-8",
                           b"<html><body>502 Bad Gateway</body></html>")
        if self.sabote.get("demarrage"):
            return reponse(200, "text/html; charset=utf-8",
                           b"<html><body>Application loading</body></html>")
        if "route-inconnue" in chemin or (methode == "POST" and chemin not in
                                          dict(self.veille.ROUTES_POST)):
            return reponse(404, "text/plain", b"")
        if chemin == "/api/proxy":
            return reponse(400, "application/json; charset=utf-8", b'{"error": "cible absente"}')
        if chemin.startswith("/api/"):
            if self.sabote.get(chemin) == "absent":
                return reponse(404, "text/plain", b"")
            if self.sabote.get(chemin) == "erreur":
                return reponse(200, "application/json; charset=utf-8", b'{"error": "panne"}')
            if self.sabote.get(chemin) == "sans-porte" or chemin in self.hics:
                # La passerelle répond à la place du service, sur cette route-là
                # seulement — les autres adresses de l'hôte, elles, répondent.
                self.hics.discard(chemin)
                return reponse(502, "text/html; charset=utf-8",
                               b"<html><body>502 Bad Gateway</body></html>")
            return reponse(200, "application/json; charset=utf-8", b'{"ok": true}')
        if chemin in surface.TEXTES:
            texte = surface.texte(chemin) or ""
            if self.sabote.get(chemin) == "tronque":
                texte = texte[:120]
            return reponse(200, "text/plain; charset=utf-8" if chemin != "/sitemap.xml"
                           else "application/xml; charset=utf-8", texte.encode("utf-8"))
        if chemin in surface.IMAGES:
            fichier = surface.chemin_image(chemin)
            type_contenu = {
                "/favicon.svg": "image/svg+xml",
                "/favicon.ico": "image/x-icon",
                "/apple-touch-icon.png": "image/png",
                "/og-image.png": "image/png",
            }[chemin]
            return reponse(200, type_contenu, fichier.read_bytes() if fichier else b"")
        page = f"<!DOCTYPE html><html lang=\"fr\"><head>{surface.entete_html()}</head></html>"
        une_fois_ici = "/" in self.une_fois
        if une_fois_ici:
            self.une_fois.discard("/")
        if self.sabote.get("/") == "sans-canonique" or une_fois_ici:
            page = page.replace(f'rel="canonical" href="{surface.URL_CANONIQUE}"', "")
        return reponse(200, "text/html; charset=utf-8", page.encode("utf-8"))


class TestCouverture(unittest.TestCase):
    """Une route servie doit être sondée, ou écartée avec sa raison écrite."""

    @classmethod
    def setUpClass(cls):
        cls.veille = charger_veille()

    def couverture(self, methode: str, sondees: set[str]) -> tuple[set[str], set[str]]:
        ecartees = set(self.veille.ROUTES_ECARTEES)
        routes = routes_du_serveur(methode)
        manquantes = routes - sondees - ecartees
        return routes, manquantes

    def test_les_routes_get_sont_toutes_sondees(self):
        sondees = set(self.veille.ROUTES_GET)
        sondees |= {route.split("?", 1)[0] for route in self.veille.ROUTES_GET_AVEC_PARAMETRES}
        routes, manquantes = self.couverture("GET", sondees)
        self.assertTrue(routes, "aucune route lue dans do_GET : le format de la source a changé")
        self.assertEqual(
            manquantes, set(),
            "routes servies mais absentes de la veille : " + ", ".join(sorted(manquantes)))

    def test_les_routes_post_sont_toutes_sondees(self):
        sondees = {chemin for chemin, _ in self.veille.ROUTES_POST}
        routes, manquantes = self.couverture("POST", sondees)
        self.assertTrue(routes, "aucune route lue dans do_POST : le format de la source a changé")
        self.assertEqual(
            manquantes, set(),
            "routes POST servies mais absentes de la veille : " + ", ".join(sorted(manquantes)))

    def test_chaque_route_ecartee_dit_pourquoi(self):
        for chemin, raison in self.veille.ROUTES_ECARTEES.items():
            with self.subTest(chemin=chemin):
                self.assertTrue(raison.strip(), f"{chemin} écartée sans raison écrite")
                self.assertTrue(raison.strip().endswith("."),
                                f"la raison de {chemin} doit être une phrase")

    def test_les_images_sondees_sont_celles_publiees(self):
        self.assertEqual(set(self.veille.TYPES_IMAGES), set(surface.IMAGES),
                         "une image publiée sans type attendu ne serait pas contrôlée")

    def test_la_veille_ne_sonde_que_des_adresses_publiques(self):
        for nom, adresse in self.veille.HOTES.items():
            with self.subTest(hote=nom):
                self.assertTrue(adresse.startswith("https://"),
                                f"{nom} doit être interrogée en https")
                for interdit in ("localhost", "127.0.0.1", "0.0.0.0"):
                    self.assertNotIn(interdit, adresse,
                                     f"{nom} ne doit pas viser une adresse locale")

    def test_le_script_ne_touche_pas_au_reseau_au_chargement(self):
        """L'import doit rester inerte : c'est ce qui permet de tester le reste."""
        import urllib.request

        appels = []
        vrai = urllib.request.urlopen
        urllib.request.urlopen = lambda *a, **k: appels.append(a) or vrai(*a, **k)
        try:
            charge = charger_veille()
        finally:
            urllib.request.urlopen = vrai
        self.assertEqual(appels, [], "l'import du script a ouvert une connexion")
        self.assertTrue(hasattr(charge, "sonder"))


class TestEpreuves(unittest.TestCase):
    """Ce que la veille voit : un vrai succès passe, une panne échoue."""

    @classmethod
    def setUpClass(cls):
        cls.veille = charger_veille()

    def sonder(self, sabote: dict[str, str] | None = None, hote: str = "canonique",
               une_fois: list[str] | None = None, essais: int = 1,
               hics: list[str] | None = None):
        faux = FauxReseau(self.veille, sabote, une_fois, hics)
        vrai = self.veille._demander
        self.veille._demander = faux
        try:
            verdicts = self.veille.sonder(hote, self.veille.HOTES[hote], essais, 0.0)
        finally:
            self.veille._demander = vrai
        return verdicts, faux

    def test_un_502_isole_se_reprend_quand_l_hote_est_debout(self):
        """Le 502 du 15 octobre 2026, rejoué : une route tombe, les autres répondent.

        La veille publiait « le service n'est pas derrière » pour `/api/bulles`
        alors que soixante-sept autres adresses du même hôte venaient de répondre
        200 — la plus grosse comprise. Le service ne dormait pas : Render
        redéployait la version qu'on venait de fusionner. Redemander cette
        adresse-là coûte quinze secondes ; la déclarer morte coûte la confiance.
        """
        verdicts, faux = self.sonder(hics=["/api/bulles"])
        base = self.veille.HOTES["canonique"]
        bulles = next(verdict for verdict in verdicts if verdict.cible == "/api/bulles")
        self.assertEqual(faux.appels.count(f"GET {base}/api/bulles"), 2,
                         "un 502 isolé n'a pas été repris")
        self.assertTrue(bulles.reussi, "la route n'est pas repassée au vert")
        self.assertIn("cette réponse-là manquait, pas le service", bulles.detail,
                      "le verdict ne dit pas qu'il a fallu reprendre la route")

    def test_un_502_qui_dure_ne_dit_plus_que_le_service_est_absent(self):
        """Un verdict doit dire ce qu'on a **mesuré**, pas ce qu'on suppose."""
        verdicts, faux = self.sonder({"/api/bulles": "sans-porte"})
        base = self.veille.HOTES["canonique"]
        bulles = next(verdict for verdict in verdicts if verdict.cible == "/api/bulles")
        self.assertEqual(faux.appels.count(f"GET {base}/api/bulles"), 2,
                         "la reprise n'a pas eu lieu")
        self.assertFalse(bulles.reussi)
        self.assertIn("l'hôte répondait par ailleurs", bulles.detail)
        self.assertNotIn("le service n'est pas derrière", bulles.detail)

    def test_un_hote_muet_partout_ne_se_reprend_pas(self):
        """Pas de reprise quand l'hôte n'a rien dit : ce n'est pas un à-coup.

        C'est la règle qui garde la veille à deux minutes sur un hôte suspendu :
        soixante-huit adresses reprises une fois seraient quarante minutes.
        """
        verdicts, faux = self.sonder({"panne": "oui"})
        base = self.veille.HOTES["canonique"]
        self.assertEqual(faux.appels.count(f"GET {base}/api/lexique"), 1,
                         "une panne générale a été reprise : la veille s'allonge pour rien")
        page = verdicts[0]
        self.assertIn("le service n'est pas derrière", page.detail)
        self.assertNotIn("l'hôte répondait par ailleurs", page.detail)

    def test_un_hebergeur_docile_fait_tout_passer(self):
        """Sans ce contrôle, une épreuve impossible passerait pour une exigence."""
        verdicts, faux = self.sonder()
        rates = [(verdict.cible, verdict.detail) for verdict in verdicts if not verdict.reussi]
        self.assertEqual(rates, [], f"épreuves impossibles à satisfaire : {rates}")
        self.assertGreaterEqual(len(verdicts), 30, "la veille sonde trop peu de choses")
        for attendu in ("/robots.txt", "/llms-full.txt", "/api/objections", "/api/simuler"):
            self.assertIn(f"GET {self.veille.HOTES['canonique']}{attendu}", faux.appels)

    def test_les_epreuves_POST_sont_de_vrais_POST(self):
        _, faux = self.sonder()
        for chemin, _ in self.veille.ROUTES_POST:
            self.assertIn(f"POST {self.veille.HOTES['canonique']}{chemin}", faux.appels)

    def test_un_texte_tronque_est_vu(self):
        verdicts, _ = self.sonder({"/llms-full.txt": "tronque"})
        fautifs = [verdict for verdict in verdicts if not verdict.reussi]
        self.assertEqual([verdict.cible for verdict in fautifs], ["/llms-full.txt"])
        self.assertIn("différent du texte engendré", fautifs[0].detail)

    def test_une_page_sans_canonique_est_vue(self):
        verdicts, _ = self.sonder({"/": "sans-canonique"})
        fautifs = [verdict for verdict in verdicts if not verdict.reussi]
        self.assertEqual([verdict.cible for verdict in fautifs], ["/"])
        self.assertIn("adresse canonique", fautifs[0].detail)

    def test_une_route_disparue_est_vue(self):
        verdicts, faux = self.sonder({"/api/objections": "absent"}, essais=3)
        fautifs = [verdict for verdict in verdicts if not verdict.reussi]
        self.assertEqual([verdict.cible for verdict in fautifs], ["/api/objections"])
        self.assertIn("attendu 200, reçu 404", fautifs[0].detail)
        base = self.veille.HOTES["canonique"]
        self.assertEqual(faux.appels.count(f"GET {base}/api/objections"), 1,
                         "une route absente a été redemandée trois fois pour rien")

    def test_une_route_qui_repond_une_erreur_est_vue(self):
        verdicts, _ = self.sonder({"/api/catalogue": "erreur"})
        fautifs = [verdict for verdict in verdicts if not verdict.reussi]
        self.assertEqual([verdict.cible for verdict in fautifs], ["/api/catalogue"])
        self.assertIn("répond une erreur", fautifs[0].detail)

    def test_le_rapport_s_ecrit_ou_on_le_demande(self):
        """`--rapport` existe parce que la variable du coureur ne se redirige pas."""
        import tempfile

        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "sous" / "veille.md"
            verdicts, _ = self.sonder()
            ecrits = self.veille.rapporter(verdicts, ["canonique"], [str(chemin)])
            # Pas d'égalité stricte : **en intégration continue**,
            # `GITHUB_STEP_SUMMARY` existe, et le rapport s'écrit alors aussi
            # dans le résumé de l'étape. Un contrôle qui suppose l'absence de
            # cette variable passe ici et échoue là-bas — vérifié le
            # 15 octobre 2026, quatre versions de Python d'accord pour le dire.
            self.assertIn(chemin, ecrits)
            texte = chemin.read_text(encoding="utf-8")
        self.assertIn("Veille en ligne", texte)
        self.assertIn("| hôte | cible | statut | résultat |", texte)
        self.assertIn("| ✓ canonique |", texte)

    def test_la_ligne_de_commande_honore_l_option(self):
        """Le vrai chemin : celui qu'emprunte la veille dans son étape."""
        import contextlib
        import io
        import tempfile

        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "veille.md"
            faux = FauxReseau(self.veille)
            vrai = self.veille._demander
            self.veille._demander = faux
            ancien = self.veille.sys.argv
            self.veille.sys.argv = ["veille", "--hote", "canonique", "--essais", "1",
                                    "--attente", "0", "--rapport", str(chemin)]
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    code = self.veille.main()
            finally:
                self.veille._demander = vrai
                self.veille.sys.argv = ancien
            self.assertEqual(code, 0)
            self.assertTrue(chemin.exists(),
                            "--rapport n'a pas été transmis : la page de suivi resterait vide")
            self.assertIn("Veille en ligne", chemin.read_text(encoding="utf-8"))

    def test_le_rapport_vole_aussi_vers_le_resume_de_l_etape(self):
        """En intégration continue, la variable existe : deux destinations.

        Ce n'est pas une bizarrerie, c'est la raison d'être du doublon : sur un
        coureur, le rapport doit **à la fois** remplir le résumé de l'étape — que
        GitHub affiche sans rien installer — et atterrir dans le fichier que
        l'étape suivante publie. Nier la variable, c'est ce qui a fait échouer
        quatre versions de Python d'un coup le 15 octobre 2026.
        """
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as dossier:
            resume = Path(dossier) / "resume.md"
            demande = Path(dossier) / "demande.md"
            ancien = os.environ.get("GITHUB_STEP_SUMMARY")
            os.environ["GITHUB_STEP_SUMMARY"] = str(resume)
            try:
                verdicts, _ = self.sonder()
                ecrits = self.veille.rapporter(verdicts, ["canonique"], [str(demande)])
            finally:
                if ancien is None:
                    os.environ.pop("GITHUB_STEP_SUMMARY", None)
                else:
                    os.environ["GITHUB_STEP_SUMMARY"] = ancien
            self.assertEqual(sorted(map(str, ecrits)), sorted([str(demande), str(resume)]))
            self.assertIn("Veille en ligne", resume.read_text(encoding="utf-8"))
            self.assertIn("Veille en ligne", demande.read_text(encoding="utf-8"))

    def test_sans_rapport_demande_il_ne_se_plaint_pas(self):
        """Un poste sans GitHub : le script doit rester utilisable tel quel."""
        import os

        verdicts, _ = self.sonder()
        ancien = os.environ.pop("GITHUB_STEP_SUMMARY", None)
        try:
            self.assertEqual(self.veille.rapporter(verdicts, ["canonique"], []), [])
        finally:
            if ancien is not None:
                os.environ["GITHUB_STEP_SUMMARY"] = ancien

    def test_un_502_sur_une_route_est_un_verdict_pas_un_reveil(self):
        """La passerelle sans service, sur une route : on le dit, on n'attend pas.

        Un 502 n'annonce aucun démarrage, et le répéter ne réveille rien. C'est
        ce qui faisait durer une veille sur un hôte suspendu une quarantaine de
        minutes — le genre de lenteur qui fait qu'on ne la lit plus.
        """
        verdicts, faux = self.sonder({"panne": "oui"}, essais=5)
        base = self.veille.HOTES["canonique"]
        self.assertEqual(faux.appels.count(f"GET {base}/api/lexique"), 1,
                         "une route a attendu cinq fois une passerelle qui ne répond pas")
        rate = [verdict for verdict in verdicts if not verdict.reussi]
        self.assertTrue(rate, "un 502 n'a pas été vu")
        self.assertIn("passerelle", rate[0].detail)
        self.assertIn("502", rate[0].detail)

    def test_insister_sait_quand_il_faut_attendre_et_quand_non(self):
        """Les trois règles de `_insister`, éprouvées sur lui — pas sur ses appels.

        Les épreuves de `sonder` passent `essais=1` aux routes : elles ne peuvent
        donc pas dire si l'insistance a été réservée à ce qu'il faut. Ces trois
        cas-là, si.
        """
        faux = FauxReseau(self.veille, {"muet": "oui"})
        vrai = self.veille._demander
        self.veille._demander = faux
        try:
            # 1. Le silence : on insiste — c'est un réveil en cours.
            self.veille._insister("https://exemple.test/", essais=3, attente=0.0)
            self.assertEqual(len(faux.appels), 3, "le silence n'est plus attendu")

            # 2. Un 502 : un verdict. Le répéter ne réveille rien.
            faux = FauxReseau(self.veille, {"panne": "oui"})
            self.veille._demander = faux
            self.veille._insister("https://exemple.test/", essais=3, attente=0.0)
            self.assertEqual(len(faux.appels), 1, "un 502 a été attendu trois fois")

            # 3. Un critère : on insiste tant qu'il n'est pas satisfait, et on
            #    s'arrête dès qu'il l'est.
            faux = FauxReseau(self.veille, {}, une_fois=["/"])
            self.veille._demander = faux
            reponse = self.veille._insister("https://exemple.test/", essais=5, attente=0.0,
                                            acceptable=self.veille._page_complete)
            self.assertEqual(len(faux.appels), 2, "le critère n'a pas arrêté l'attente")
            self.assertTrue(self.veille._page_complete(reponse))
        finally:
            self.veille._demander = vrai

    def test_une_page_complete_ne_se_demande_pas_deux_fois(self):
        """L'insistance s'arrête à la première page entière.

        Sans cette règle, `--essais 5` ferait cinq requêtes et quatre attentes de
        vingt secondes **à chaque passage**, même quand tout va bien : quatre-
        vingts secondes ajoutées à une veille qui n'avait rien à dire.
        """
        verdicts, faux = self.sonder(essais=5)
        base = self.veille.HOTES["canonique"]
        self.assertEqual(faux.appels.count(f"GET {base}/"), 1,
                         "une page déjà complète a été redemandée")
        self.assertTrue(verdicts[0].reussi)

    def test_la_page_attend_que_le_deploiement_arrive(self):
        """Juste après une fusion, ce qui est servi n'est pas encore le dépôt.

        Et « pas encore » n'est pas « faux » : la page est ce qu'un déploiement
        remplace en dernier. La veille le sait depuis le 15 octobre 2026, où
        elle est devenue le contrôle de l'après-fusion.
        """
        verdicts, faux = self.sonder(une_fois=["/"], essais=3)
        base = self.veille.HOTES["canonique"]
        self.assertEqual(faux.appels.count(f"GET {base}/"), 2,
                         "la page n'a pas été réessayée : un déploiement en vol "
                         "passerait pour une page cassée")
        self.assertTrue(verdicts[0].reussi, "la page n'est pas repassée au vert")

    def test_une_page_qui_repond_502_est_essayee_puis_dite(self):
        """Sur la page, un 502 se réessaie — mais le verdict reste honnête."""
        verdicts, faux = self.sonder({"panne": "oui"}, essais=3)
        base = self.veille.HOTES["canonique"]
        self.assertEqual(faux.appels.count(f"GET {base}/"), 3,
                         "la page n'attend pas le déploiement")
        self.assertFalse(verdicts[0].reussi)
        self.assertIn("passerelle", verdicts[0].detail)

    def test_une_panne_reseau_devient_un_verdict_pas_un_arret(self):
        """Un hôte muet ne doit pas emporter le rapport avec lui."""
        import urllib.error

        def explose(*_args, **_kw):
            raise urllib.error.URLError("connexion refusée")

        vrai = urllib.request.urlopen
        urllib.request.urlopen = explose
        try:
            verdicts = self.veille.sonder("canonique", self.veille.HOTES["canonique"], 1, 0.0)
        finally:
            urllib.request.urlopen = vrai
        self.assertEqual(len(verdicts), 2, "le silence de l'hôte n'a pas arrêté la veille")
        self.assertIn("aucune réponse", verdicts[0].detail)

    def test_un_hote_muet_est_dit_une_fois_pas_vingt_deux(self):
        """Un hôte qui ne répond pas du tout : une ligne, et on passe.

        Répéter la même panne sur chaque route n'ajoute pas d'information, mais
        elle coûte une sonde à chaque fois — et c'est ainsi qu'une veille devient
        si lente qu'on cesse de la lire.
        """
        verdicts, faux = self.sonder({"muet": "oui"})
        self.assertEqual(len(verdicts), 2, "la veille a répété la même panne")
        self.assertIn("non éprouvées", verdicts[1].detail)
        self.assertLessEqual(len(faux.appels), 2, "des adresses ont été sondées pour rien")

    def test_l_insistance_est_reservee_a_la_page(self):
        """Elle réveille un service endormi : les autres suivent, sans attendre."""
        faux = FauxReseau(self.veille, {"demarrage": "oui"})
        vrai = self.veille._demander
        self.veille._demander = faux
        try:
            self.veille.sonder("canonique", self.veille.HOTES["canonique"], 3, 0.0)
        finally:
            self.veille._demander = vrai
        base = self.veille.HOTES["canonique"]
        self.assertEqual(faux.appels.count(f"GET {base}/"), 3,
                         "la page n'a pas été réessayée : un réveil passerait pour une panne")
        self.assertEqual(faux.appels.count(f"GET {base}/api/lexique"), 1,
                         "une adresse autre que la page a été réessayée : la veille s'allonge")

    def test_un_hebergeur_endormi_ne_passe_pas_pour_un_succes(self):
        """Le piège propre à la copie de secours : 200 + page d'attente.

        Elle répond 200, avec du HTML, en racontant qu'elle démarre. La prendre
        pour une réponse serait le pire des silences : la veille dirait que tout
        va bien au moment précis où rien ne répond.
        """
        verdicts, _ = self.sonder({"demarrage": "oui"})
        rates = [verdict for verdict in verdicts if not verdict.reussi]
        self.assertEqual(len(rates), len(verdicts),
                         "une page d'attente a été prise pour une réponse")
        self.assertTrue(all(verdict.detail for verdict in rates),
                        "un échec sans explication ne se lit pas")


if __name__ == "__main__":
    unittest.main()
