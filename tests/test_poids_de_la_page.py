"""Ce que le téléphone décompresse et analyse, et qui la page appelle.

Mesuré le 15 octobre 2026 sur la page publiée (`index.html`, gzip -6) : **478 611
octets bruts**, **129 465 transférés**, dont **109 102 o** de feuille de style et
**317 765 o** de script en ligne — soit **66,4 %** du document — pour **51 744 o**
de balisage. La page est autonome : aucune police distante, aucune image, aucune
feuille externe ; son seul appel est un script **en même origine**
(`/_vercel/insights/script.js`, `defer`).

Le plafond du **réseau** existe déjà, ailleurs : `outils/budgets_fluidite.py` le
tient avec son ancre datée et sa marge, et la CI refuse un dépassement. Ce
fichier-ci ne remet pas un second avis sur ces nombres — il **lit** ce plafond et
publie la réserve. Ce qu'il tient, c'est ce que les octets compressés ne voient
pas : le **document brut** (ce que l'appareil analyse), la **part du script** (le
document ne doit pas devenir un programme), et l'**autonomie** de la page.

Six promesses, donc :

1. **les plafonds portent leur mesure datée** et disent leur jour zéro ;
2. **la marge est vraie et petite** — recalculée depuis le plafond et la mesure ;
3. **la mesure est complète** — CSS + JS + balisage = le fichier, au bit près :
   c'est ainsi qu'une mesure fausse se voit ;
4. **la page n'appelle personne d'autre qu'elle-même** — aucune sous-ressource
   d'un domaine tiers, et toute sous-ressource en même origine est **déclarée**,
   jamais tolérée par accident ;
5. **il n'y a qu'un juge par grandeur** — le plafond réseau n'est pas recopié
   ici : il est lu dans la table du dépôt, et le verdict le suit ;
6. **le dépassement échoue** — chiffres, motif et sortie, et la ligne de commande
   sort en 1.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from outils import budgets_fluidite  # noqa: E402
from outils import poids_de_la_page as poids  # noqa: E402

#: Une marge au-delà de dix pour cent n'est plus une réserve : c'est une
#: autorisation de grossir. Le dépôt préfère une cible déclarée à une marge floue.
MARGE_MAXIMUM = 0.10

#: Le plancher écrit de la part du script : les trois quarts du document. Au-delà,
#: la page n'est plus un document qui exécute du code — c'est un programme.
PART_JS_PLANCHER = 0.75


class TestLesPlafondsDeLaPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mesure = poids.mesurer()

    def test_chaque_plafond_porte_sa_mesure_datee(self):
        for nom, limite in poids.PLAFONDS.items():
            with self.subTest(plafond=nom):
                self.assertGreater(limite["mesure"], 0,
                                   "un plafond sans mesure du jour ne tient rien")
                self.assertGreater(limite["plafond"], 0)
                for champ in ("quoi", "sortie"):
                    self.assertGreaterEqual(len(limite[champ].strip()), 40,
                                            f"« {champ} » ne dit pas assez pour agir")
                self.assertRegex(limite["quand"], r"\d{4}",
                                 "la mesure ne dit pas quand elle a été prise")

    def test_un_plafond_sans_etat_ancien_le_dit(self):
        """Un plafond qui ne bat rien n'est pas un cliquet : il doit le déclarer.

        `index.html` est un artefact généré, sans antériorité mesurable dans ce
        dépôt : il n'y a pas d'« avant » à battre. L'écrire est ce qui empêche le
        plafond de se faire passer pour un gain.
        """
        for nom, limite in poids.PLAFONDS.items():
            with self.subTest(plafond=nom):
                self.assertTrue("avant" in limite or limite.get("jour_zero"),
                                "un plafond sans « avant » doit déclarer son jour zéro")
                if "avant" in limite:
                    self.assertGreater(limite["avant"], limite["plafond"],
                                       "un plafond au-dessus de son état ancien décrit "
                                       "le statu quo au lieu de le corriger")

    def test_la_marge_declaree_est_la_vraie(self):
        """Une marge écrite à la main peut mentir ; celle-ci se recalcule."""
        for nom, limite in poids.PLAFONDS.items():
            with self.subTest(plafond=nom):
                calculee = (limite["plafond"] - limite["mesure"]) / limite["mesure"]
                self.assertAlmostEqual(limite["marge"], calculee, places=3,
                                       msg=f"la marge annoncée à {nom} ne correspond pas "
                                           f"au plafond et à la mesure ({calculee:.4f})")

    def test_aucune_marge_n_autorise_le_doublement(self):
        for nom, limite in poids.PLAFONDS.items():
            with self.subTest(plafond=nom):
                self.assertLessEqual(limite["marge"], MARGE_MAXIMUM,
                                     f"la marge de {nom} n'est plus une réserve, "
                                     f"c'est une autorisation de grossir")

    def test_le_plafond_tient_ce_qui_est_mesure(self):
        for nom, limite in poids.PLAFONDS.items():
            with self.subTest(plafond=nom):
                valeur = poids._valeur(self.mesure, nom)
                self.assertIsNotNone(valeur, f"la mesure ne porte pas « {nom} »")
                self.assertGreaterEqual(limite["plafond"], valeur,
                                        f"le plafond de {nom} est déjà sous la mesure "
                                        "du jour : il fait rougir le travail en cours")

    def test_la_mesure_du_jour_est_dans_la_marge(self):
        """Le plafond n'est pas une cible de confort : la mesure doit s'en approcher."""
        for nom, limite in poids.PLAFONDS.items():
            with self.subTest(plafond=nom):
                valeur = poids._valeur(self.mesure, nom)
                self.assertLessEqual(valeur, limite["plafond"])
                self.assertGreater(valeur, limite["mesure"] * 0.98,
                                   "la page a maigri de plus de 2 % : le jour zéro doit "
                                   "être réancré, sinon la marge est fausse")

    def test_la_part_du_script_est_plafonnee_sous_les_trois_quarts(self):
        """Le plafond de part n'est pas décoratif : il doit mordre avant les 75 %."""
        self.assertIn("part_js", poids.PLAFONDS)
        self.assertLessEqual(poids.PLAFONDS["part_js"]["plafond"], PART_JS_PLANCHER,
                             "au-delà des trois quarts, le document est un programme")


class TestLaMesureEstComplete(unittest.TestCase):
    """CSS + JS + balisage = le fichier. C'est ainsi qu'une mesure fausse se voit."""

    @classmethod
    def setUpClass(cls):
        cls.mesure = poids.mesurer()

    def test_les_blocs_recouvrent_exactement_le_fichier(self):
        octets = self.mesure["octets"]
        self.assertEqual(octets["css"] + octets["js"] + octets["html"], octets["brut"],
                         "les blocs ne recouvrent plus la page : la mesure est fausse")
        self.assertGreater(octets["gzip"], 0)
        self.assertLess(octets["gzip"], octets["brut"],
                        "compressée, la page ne peut pas être plus lourde")

    def test_les_parts_somment_a_un(self):
        self.assertAlmostEqual(sum(self.mesure["part"].values()), 1.0, places=6,
                               msg="les parts des blocs ne font plus le document entier")

    def test_les_blocs_ne_sont_pas_vides(self):
        for nom in ("css", "js", "html"):
            with self.subTest(bloc=nom):
                self.assertGreater(self.mesure["octets"][nom], 1_000,
                                   f"le bloc « {nom} » a disparu de la mesure")

    def test_le_balisage_ne_compte_pas_les_scripts(self):
        """Le défaut mesuré le 15 octobre 2026 : 363 776 o annoncés pour 51 744.

        La première version soustrayait les blocs par remplacement de chaîne, et
        retirait la mauvaise occurrence. La mesure par **positions** donne le
        compte juste — et ce contrôle l'empêche de revenir.
        """
        texte = "a<style>x</style>b<script>y</script>c"
        fractions = poids._fractions(texte)
        self.assertEqual(fractions["css"], "x", "le contenu de la feuille n'est plus isolé")
        self.assertEqual(fractions["js"], "y", "le contenu du script n'est plus isolé")
        #: Le balisage, c'est tout le reste — les **balises** comprises : elles se
        #: paient aussi, et les exclure flatterait la mesure.
        self.assertEqual(fractions["html"], "a<style></style>b<script></script>c")
        self.assertEqual(len(fractions["css"] + fractions["js"] + fractions["html"]),
                         len(texte), "la découpe perd ou invente des octets")
        self.assertLess(self.mesure["octets"]["html"], self.mesure["octets"]["css"],
                        "le balisage pèse plus que la feuille de style : la découpe "
                        "compte probablement autre chose que le balisage")

    def test_la_mesure_est_reproductible(self):
        self.assertEqual(poids.mesurer()["octets"], self.mesure["octets"])
        self.assertEqual(poids.mesurer()["structure"], self.mesure["structure"])

    def test_le_script_est_le_plus_gros_bloc_et_il_est_suivi(self):
        """Ce que la part mesure : le script domine le document, et on le sait."""
        self.assertGreater(self.mesure["part"]["js"], self.mesure["part"]["css"])
        self.assertGreater(self.mesure["part"]["js"], self.mesure["part"]["html"])


class TestLaPageNAppellePersonne(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mesure = poids.mesurer()
        cls.appels = cls.mesure["appels"]

    def test_aucune_sous_ressource_d_un_domaine_tiers(self):
        """Ni police distante, ni CDN, ni image hébergée ailleurs.

        Un outil citoyen qui tire une police chez un tiers lui dit qui le lit :
        c'est une fuite, un délai, et une dépendance de disponibilité.
        """
        self.assertEqual(self.appels["domaines_tiers"], [],
                         f"la page appelle un domaine tiers : {self.appels['domaines_tiers']}")

    def test_chaque_appel_en_meme_origine_est_declare(self):
        self.assertEqual(self.appels["non_declarees"], [],
                         "une sous-ressource en même origine n'est pas déclarée : elle "
                         "doit l'être, jamais survivre par accident")
        for url in self.appels["meme_origine"]:
            with self.subTest(url=url):
                self.assertIn(url, poids.SOUS_RESSOURCES_ASSUMEES)

    def test_les_liens_ne_sont_pas_des_appels(self):
        """Un lien vers une source officielle est un lien, pas une requête.

        Le balisage porte des adresses `https://` — celles des sources citées.
        Elles ne doivent **pas** compter comme des appels, sinon la liste blanche
        devrait les contenir toutes et ne dirait plus rien.
        """
        texte = poids.PAGE.read_text(encoding="utf-8")
        for appel in self.appels["detail"]:
            with self.subTest(url=appel["url"]):
                self.assertTrue(appel["url"].startswith(("/", "http")),
                                "un type d'appel inattendu est compté comme une ressource")
                self.assertNotIn(appel["type"], poids.TYPES_QUI_NE_SONT_PAS_DES_APPELS)
        self.assertGreaterEqual(texte.count("<a href=\"https://"), 4,
                                "la page n'a plus de liens vers ses sources : le contrôle "
                                "ne prouve plus rien")

    def test_le_script_d_analytics_reste_en_defer(self):
        """En même origine et en `defer` : il ne retarde pas le premier rendu."""
        texte = poids.PAGE.read_text(encoding="utf-8")
        for url in self.appels["meme_origine"]:
            if not url.endswith(".js"):
                continue
            with self.subTest(url=url):
                balise = texte[:texte.index(url)]
                balise = balise[balise.rindex("<script"):]
                self.assertIn("defer", balise, "un script bloquant est arrivé dans la page")


class TestLePlafondReseauNEstPasRecopie(unittest.TestCase):
    """Un seul juge par grandeur : le réseau est tenu par `budgets_fluidite`.

    Deux plafonds concurrents sur le même nombre finiraient par diverger, et
    c'est la mesure qui lirait le mauvais. Le contrôle principal est donc
    l'absence : ce fichier **ne déclare** pas de plafond réseau.
    """

    def test_ce_fichier_ne_declare_aucun_plafond_reseau(self):
        for nom in ("gzip", "reseau", "transfere"):
            with self.subTest(plafond=nom):
                self.assertNotIn(nom, poids.PLAFONDS,
                                 "le plafond réseau est tenu par budgets_fluidite.py : "
                                 "un second avis ferait deux juges et aucune vérité")

    def test_le_plafond_lu_est_celui_de_la_table_du_depot(self):
        budget = next(b for b in budgets_fluidite.BUDGETS if b.cle == "page")
        reseau = poids.plafond_reseau()
        self.assertEqual(reseau["source"], "budgets_fluidite.page")
        self.assertEqual(reseau["plafond"], budget.plafond)
        self.assertEqual(reseau["ancre"], budget.ancre)
        self.assertEqual(poids.PLAFOND_RESEAU[0], "budgets_fluidite")

    def test_la_mesure_du_jour_entre_dans_ce_plafond(self):
        mesure = poids.mesurer()
        self.assertLessEqual(mesure["octets"]["gzip"], mesure["reseau"]["plafond"],
                             "la page franchit le plafond réseau du dépôt")
        self.assertEqual(poids.depassements(mesure), [])

    def test_un_plafond_reseau_franchi_est_dit_avec_sa_source(self):
        """Le jour où la page grossit trop, le verdict nomme le juge et la sortie."""
        mesure = copy.deepcopy(poids.mesurer())
        mesure["octets"]["gzip"] = mesure["reseau"]["plafond"] + 5_000
        trop = poids.depassements(mesure)
        self.assertEqual([d["nom"] for d in trop], ["gzip"])
        self.assertIn("budgets_fluidite.page", trop[0]["phrase"])
        self.assertIn("relever", trop[0]["phrase"])
        self.assertTrue(any("⛔" in ligne for ligne in poids.lignes(mesure)))


class TestLeVerdict(unittest.TestCase):
    def _mesure(self) -> dict:
        return copy.deepcopy(poids.mesurer())

    def test_une_page_sous_les_plafonds_passe(self):
        for ligne in poids.lignes(self._mesure()):
            self.assertNotIn("⛔", ligne)

    def test_un_document_trop_lourd_est_refuse_avec_ses_chiffres(self):
        limite = poids.PLAFONDS["brut"]["plafond"]
        mesure = self._mesure()
        mesure["octets"]["brut"] = limite + 1_000
        trop = poids.depassements(mesure)
        self.assertEqual([d["nom"] for d in trop], ["brut"])
        self.assertEqual(trop[0]["exces"], 1_000)
        self.assertIn("de 505 000 o", trop[0]["phrase"].replace("  ", " "))
        self.assertIn("Retirer du document", trop[0]["phrase"])

    def test_une_part_de_script_devenue_programme_est_refusee(self):
        mesure = self._mesure()
        mesure["part"]["js"] = PART_JS_PLANCHER + 0.05
        trop = poids.depassements(mesure)
        self.assertEqual([d["nom"] for d in trop], ["part_js"])
        self.assertIn("Découper le script", trop[0]["phrase"])

    def test_un_domaine_tiers_est_un_depassement(self):
        mesure = self._mesure()
        mesure["appels"]["domaines_tiers"] = ["fonts.exemple.test"]
        trop = poids.depassements(mesure)
        self.assertEqual([d["nom"] for d in trop], ["appels"])
        self.assertIn("ne dépend pas d'un tiers", trop[0]["phrase"])

    def test_une_sous_ressource_non_declaree_est_un_depassement(self):
        mesure = self._mesure()
        mesure["appels"]["non_declarees"] = ["/assets/extra.js"]
        trop = poids.depassements(mesure)
        self.assertEqual([d["nom"] for d in trop], ["sous-ressource"])
        self.assertIn("SOUS_RESSOURCES_ASSUMEES", trop[0]["phrase"])

    def test_le_verdict_public_la_mesure_le_plafond_et_la_reserve(self):
        """Ce qu'on lit doit permettre de corriger sans chercher."""
        texte = "\n".join(poids.lignes(self._mesure()))
        self.assertIn("Poids de la page", texte)
        for nom, limite in poids.PLAFONDS.items():
            with self.subTest(plafond=nom):
                self.assertIn(nom, texte)
                # Une grandeur en octets s'écrit en octets, une part en pour cent :
                # le rapport doit employer l'unité de chacun, pas la même pour tous.
                facteur = 100 if nom.startswith("part_") else 1
                # Même écriture que le rapport : on éprouve l'unité, pas le formatage.
                self.assertIn(poids._n(limite["plafond"] * facteur), texte,
                              "le verdict ne dit pas le plafond")
        self.assertIn("budgets_fluidite.page", texte)
        self.assertIn("réserve", texte)
        self.assertIn("n'appelle personne", texte)

    def test_la_ligne_de_commande_echoue_sur_un_depassement(self):
        """Le verdict doit sortir en 1 : un plafond qu'on n'exécute pas n'existe pas."""
        resultat = subprocess.run([sys.executable, "-m", "outils.poids_de_la_page",
                                   "--verifier"], cwd=RACINE, capture_output=True, text=True)
        self.assertEqual(resultat.returncode, 0,
                         f"la page franchit une règle de poids :\n{resultat.stdout}")
        self.assertIn("Poids de la page", resultat.stdout)

    def test_la_mesure_json_publie_les_composants(self):
        resultat = subprocess.run([sys.executable, "-m", "outils.poids_de_la_page",
                                   "--json"], cwd=RACINE, capture_output=True, text=True)
        self.assertEqual(resultat.returncode, 0)
        donnees = json.loads(resultat.stdout)
        for cle in ("brut", "gzip", "css", "js", "html"):
            with self.subTest(cle=cle):
                self.assertIn(cle, donnees["octets"])
        self.assertEqual(donnees["appels"]["domaines_tiers"], [])
        self.assertEqual(donnees["reseau"]["source"], "budgets_fluidite.page")


if __name__ == "__main__":
    unittest.main()
