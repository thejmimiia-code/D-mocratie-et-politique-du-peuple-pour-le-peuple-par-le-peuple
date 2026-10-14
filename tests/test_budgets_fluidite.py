"""tests/test_budgets_fluidite.py — les plafonds de poids, tenus par la CI.

Un budget de fluidité n'est ni un tableau de bord ni une intention : c'est une
limite qu'on oppose à une mesure, et un refus quand la mesure la franchit. Ces
contrôles tiennent quatre choses :

1. **la table est honnête** : chaque plafond vient d'une ancre datée, porte un
   motif et une sortie, et se calcule (ancre + marge) au lieu d'être recopié ;
2. **la page d'aujourd'hui tient dans son plafond**, sans lancer de serveur : les
   deux exemplaires du document (celui servi par `simulateur/interface.py` et le
   fichier publié `index.html`) pèsent moins que leur budget ;
3. **aucune charge de la page n'échappe au budget** : chaque route que la page
   appelle est soit plafonnée, soit déclarée sans plafond avec sa raison, comme
   les routes non mises en œuvre le sont déjà du côté de la couverture ;
4. **le vérificateur refuse vraiment** : un octet de plus que le plafond suffit,
   une mesure sans plafond est une anomalie, et la ligne de commande sort en
   code 1 — c'est cette sortie que la CI lit.

Le module et l'outil sont chargés par leur chemin (`charger_module`), comme le
reste des outils : le fichier sur le disque est la source, jamais un bytecode en
cache — sans quoi un sabotage testé ne serait pas le sabotage exécuté.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "outils"))

from chargement_module import charger_module  # noqa: E402

budgets = charger_module("budgets_fluidite", RACINE / "outils" / "budgets_fluidite.py")
outil = charger_module("mesurer_fluidite", RACINE / "outils" / "mesurer_fluidite.py")
couverture = charger_module(
    "couverture_des_routes", RACINE / "tests" / "test_couverture_des_routes.py"
)

CHEMIN_OUTIL = RACINE / "outils" / "mesurer_fluidite.py"


def _rapport_factice(remplacements: dict[str, int] | None = None) -> dict:
    """Un rapport de mesure fabriqué : chaque ancre, sauf ce qu'on remplace."""
    remplacements = remplacements or {}
    entrees = []
    for budget in budgets.BUDGETS:
        if budget.ou == "derive":
            continue
        octets = remplacements.get(budget.cle, budget.ancre)
        entrees.append({"cle": budget.cle, "octets": octets, "provenance": "fabriqué"})
    return {"budgets": entrees}


def _mesures_factices(remplacements: dict[str, int] | None = None) -> list:
    """Une campagne fabriquée sur les ancres, sauf les charges remplacées."""
    remplacements = remplacements or {}
    return [
        budgets.Mesure(budget.cle, remplacements.get(budget.cle, budget.ancre), "fabriqué")
        for budget in budgets.BUDGETS
        if budget.ou != "derive"
    ]


def _lancer_verificateur(rapport: dict) -> subprocess.CompletedProcess:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(rapport, f)
        chemin = f.name
    try:
        return subprocess.run(
            [sys.executable, str(CHEMIN_OUTIL), "--verifier", "--rapport-fichier", chemin],
            cwd=str(RACINE), capture_output=True, text=True, timeout=180,
        )
    finally:
        Path(chemin).unlink(missing_ok=True)


class TestTableDesPlafonds(unittest.TestCase):
    """La table des plafonds se vérifie elle-même avant de vérifier le serveur."""

    def test_chaque_plafond_a_un_motif_et_une_sortie(self):
        for budget in budgets.BUDGETS:
            with self.subTest(budget=budget.cle):
                self.assertGreaterEqual(
                    len(budget.motif), budgets.LONGUEUR_TEXTE,
                    f"{budget.cle} : un plafond sans motif est une opinion",
                )
                self.assertIn(budget.sortie, budgets.SORTIES,
                              f"{budget.cle} : sortie inconnue « {budget.sortie} »")
                self.assertGreaterEqual(
                    len(budget.sortie_texte), budgets.LONGUEUR_TEXTE,
                    f"{budget.cle} : un plafond sans sortie ne dit pas quoi faire",
                )

    def test_les_cles_sont_uniques(self):
        cles = [budget.cle for budget in budgets.BUDGETS]
        self.assertEqual(len(cles), len(set(cles)), "deux plafonds portent la même clé")

    def test_les_ancres_sont_datees_et_plausibles(self):
        ancre = date.fromisoformat(budgets.DATE_ANCRAGE)
        # Le dépôt date ses documents à Paris, la CI mesure en UTC : une journée
        # d'avance est normale, davantage serait une date inventée.
        self.assertLessEqual(ancre, date.today() + timedelta(days=1),
                             "l'ancrage est daté dans le futur")
        self.assertGreaterEqual(ancre.year, 2026, "un ancrage antérieur au simulateur public")
        for budget in budgets.BUDGETS:
            with self.subTest(budget=budget.cle):
                self.assertGreater(budget.ancre, 0, "une ancre nulle ne plafonne rien")

    def test_les_marges_sont_dans_la_fourchette_utile(self):
        for budget in budgets.BUDGETS:
            with self.subTest(budget=budget.cle):
                self.assertGreaterEqual(budget.marge_pct, budgets.MARGE_MIN,
                                        "une marge trop serrée casse au premier ajout")
                self.assertLessEqual(budget.marge_pct, budgets.MARGE_MAX,
                                     "une marge trop large ne borne plus rien")

    def test_le_plafond_se_calcule_et_ne_se_recopie_pas(self):
        for budget in budgets.BUDGETS:
            with self.subTest(budget=budget.cle):
                attendu = math.ceil(budget.ancre * (1 + budget.marge_pct / 100))
                self.assertEqual(budget.plafond, attendu)
                self.assertGreater(budget.plafond, budget.ancre,
                                   "un plafond n'est pas plus petit que son ancre")

    def test_les_plafonds_derives_sont_la_somme_de_leurs_membres(self):
        par_cle = {budget.cle: budget for budget in budgets.BUDGETS}
        derives = [budget for budget in budgets.BUDGETS if budget.ou == "derive"]
        self.assertTrue(derives, "le budget du premier écran a disparu de la table")
        for budget in derives:
            with self.subTest(budget=budget.cle):
                self.assertTrue(budget.membres, "un budget dérivé sans membres")
                for membre in budget.membres:
                    self.assertIn(membre, par_cle, f"membre inconnu « {membre} »")
                    self.assertNotEqual(par_cle[membre].ou, "derive",
                                        "un budget dérivé ne se compose pas de dérivés")
                self.assertEqual(
                    budget.ancre,
                    sum(par_cle[membre].ancre for membre in budget.membres),
                    "l'ancre du budget dérivé n'est pas la somme de ses membres",
                )

    def test_les_plafonds_non_derives_sont_tous_mesurables(self):
        for budget in budgets.BUDGETS:
            if budget.ou == "derive":
                continue
            with self.subTest(budget=budget.cle):
                self.assertIn(budget.ou, ("serveur", "les deux"))
                self.assertFalse(budget.membres, "des membres sur un plafond qui ne dérive pas")

    def test_les_routes_mesurees_n_ont_pas_de_doublon(self):
        chemins = [chemin for chemin, _ in budgets.ROUTES_MESUREES]
        self.assertEqual(len(chemins), len(set(chemins)), "une route mesurée deux fois")
        cles = [cle for _, cle in budgets.ROUTES_MESUREES]
        self.assertEqual(len(cles), len(set(cles)), "deux routes pour un même budget")


class TestMesuresHorsLigne(unittest.TestCase):
    """Ce qui se vérifie à chaque poussée, sans lancer de serveur."""

    def test_la_page_tient_dans_son_plafond(self):
        mesures = budgets.mesures_hors_ligne()
        depassements, anomalies = budgets.verifier(mesures, complet=False)
        self.assertEqual([(d.cle, d.mesure, d.plafond) for d in depassements], [],
                         "la page a franchi son plafond de poids")
        self.assertEqual([a.message for a in anomalies], [])

    def test_les_deux_exemplaires_de_la_page_partagent_le_plafond(self):
        budget = next(b for b in budgets.BUDGETS if b.cle == "page")
        servie = budgets.octets_de_la_page_du_module()
        publiee = budgets.octets_de_la_page_publiee()
        self.assertLessEqual(servie, budget.plafond,
                             "le document servi par le serveur dépasse le plafond")
        self.assertLessEqual(publiee, budget.plafond,
                             "le fichier publié (index.html) dépasse le plafond")

    def test_la_campagne_hors_ligne_ne_couvre_que_la_page(self):
        cles = {mesure.cle for mesure in budgets.mesures_hors_ligne()}
        self.assertEqual(cles, {"page"},
                         "hors ligne on ne mesure que la page ; le reste vient du serveur")

    def test_la_mesure_retenue_est_la_plus_lourde_des_deux(self):
        mesure = budgets.mesures_hors_ligne()[0]
        attendu = max(budgets.octets_de_la_page_du_module(),
                      budgets.octets_de_la_page_publiee())
        self.assertEqual(mesure.octets, attendu,
                         "la mesure hors ligne doit retenir le plus lourd exemplaire")

    def test_l_ancre_de_la_page_n_est_pas_perimee(self):
        mesure = budgets.mesures_hors_ligne()[0]
        budget = next(b for b in budgets.BUDGETS if b.cle == "page")
        self.assertGreaterEqual(
            mesure.octets, budget.ancre / 2,
            "l'ancre vaut plus du double de la page servie : elle n'ancre plus rien",
        )

    def test_le_rapport_hors_ligne_ne_parle_pas_de_depassement(self):
        rapport = budgets.rapport_texte(budgets.mesures_hors_ligne(), complet=False)
        self.assertIn("Aucun dépassement", rapport)
        self.assertIn(budgets.DATE_ANCRAGE, rapport, "le rapport doit porter la date d'ancrage")


class TestPlanDeMesure(unittest.TestCase):
    """Le plan et la table des plafonds se répondent, charge par charge."""

    def test_toute_charge_plafonnee_a_son_releve(self):
        attendues = {budget.cle for budget in budgets.BUDGETS if budget.ou != "derive"}
        mesurees = {cle for cle, _, _ in outil.plan_de_mesure()}
        self.assertEqual(mesurees - attendues, set(),
                         "une charge est mesurée sans plafond")
        self.assertEqual(attendues - mesurees, set(),
                         "un plafond n'est mesuré par aucune charge")

    def test_le_plan_ne_mesure_pas_deux_fois_la_meme_charge(self):
        cles = [cle for cle, _, _ in outil.plan_de_mesure()]
        self.assertEqual(len(cles), len(set(cles)), "une charge mesurée deux fois")

    def test_les_charges_du_plan_sont_des_get_ou_des_post(self):
        for cle, methode, chemin in outil.plan_de_mesure():
            with self.subTest(cle=cle):
                self.assertIn(methode, ("GET", "POST"))
                self.assertTrue(chemin.startswith("/"), "un chemin commence par une barre")

    def test_chaque_route_appelee_par_la_page_est_plafonnee_ou_excuse(self):
        servies = set(couverture.routes_servies_par_la_page())
        plafonnees = {budgets.nom_de_route(chemin) for _, _, chemin in outil.plan_de_mesure()}
        excusees = set(budgets.ROUTES_SANS_PLAFOND)
        self.assertEqual(
            servies - plafonnees - excusees, set(),
            "une route appelée par la page n'a ni plafond ni excuse de plafond",
        )

    def test_aucune_excuse_de_plafond_n_est_perimee(self):
        servies = set(couverture.routes_servies_par_la_page())
        perimees = set(budgets.ROUTES_SANS_PLAFOND) - servies
        self.assertEqual(perimees, set(),
                         f"excuse de plafond pour une route que la page n'appelle plus : {perimees}")

    def test_aucune_route_n_est_a_la_fois_plafonnee_et_excusee(self):
        plafonnees = {budgets.nom_de_route(chemin) for _, _, chemin in outil.plan_de_mesure()}
        doubles = plafonnees & set(budgets.ROUTES_SANS_PLAFOND)
        self.assertEqual(doubles, set(),
                         f"plafonnée et excusée à la fois : {doubles}")

    def test_les_excuses_de_plafond_sont_motivees(self):
        for route, raison in budgets.ROUTES_SANS_PLAFOND.items():
            with self.subTest(route=route):
                self.assertGreaterEqual(len(raison), budgets.LONGUEUR_TEXTE,
                                        f"{route} : excuse muette")

    def test_le_point_d_entree_est_nomme_page(self):
        self.assertEqual(budgets.nom_de_route("/"), "page")
        self.assertEqual(budgets.nom_de_route("/api/garde_fous"), "garde_fous")
        self.assertEqual(budgets.nom_de_route("/api/bulles?detail=resume"), "bulles")


class TestVerificateur(unittest.TestCase):
    """Le refus, et rien d'autre : c'est ce que la CI exécute."""

    def test_le_verificateur_ne_signale_rien_quand_tout_tient(self):
        depassements, anomalies = budgets.verifier(_mesures_factices(), complet=True)
        self.assertEqual(depassements, [])
        self.assertEqual(anomalies, [])

    def test_un_octet_au_dessus_du_plafond_suffit(self):
        budget = next(b for b in budgets.BUDGETS if b.cle == "catalogue")
        mesures = _mesures_factices({"catalogue": budget.plafond + 1})
        depassements, _ = budgets.verifier(mesures, complet=True)
        self.assertEqual([d.cle for d in depassements], ["catalogue"])
        self.assertGreater(depassements[0].pourcent, 0)

    def test_le_plafond_atteint_n_est_pas_un_depassement(self):
        budget = next(b for b in budgets.BUDGETS if b.cle == "catalogue")
        mesures = _mesures_factices({"catalogue": budget.plafond})
        depassements, _ = budgets.verifier(mesures, complet=True)
        self.assertEqual(depassements, [], "le plafond est une limite, pas un seuil franchi")

    def test_le_budget_derive_est_plus_serre_que_la_somme_de_ses_plafonds(self):
        # Un plafond individuel par charge ne suffit pas : si toutes montent en
        # même temps à leur maximum, l'ouverture paie la somme. Le budget du
        # premier écran tombe donc plus tôt (282 185 > 282 010) — et c'est voulu.
        mesures = _mesures_factices({b.cle: b.plafond for b in budgets.BUDGETS
                                     if b.ou != "derive"})
        depassements, _ = budgets.verifier(mesures, complet=True)
        self.assertEqual([d.cle for d in depassements], ["premier_ecran"],
                         "le plafond joint du premier écran ne mord pas")

    def test_une_charge_mesuree_sans_plafond_est_une_anomalie(self):
        mesures = budgets.mesures_hors_ligne() + [budgets.Mesure("inconnue", 10, "fabriqué")]
        _, anomalies = budgets.verifier(mesures, complet=False)
        self.assertEqual([a.cle for a in anomalies], ["inconnue"])
        self.assertIn("sans plafond", anomalies[0].message)

    def test_un_plafond_sans_mesure_est_une_anomalie_en_campagne_complete(self):
        _, anomalies = budgets.verifier(budgets.mesures_hors_ligne(), complet=True)
        attendues = {b.cle for b in budgets.BUDGETS if b.cle != "page"}
        self.assertTrue(attendues.issubset({a.cle for a in anomalies}),
                        "en campagne complète, un plafond non mesuré doit être signalé")

    def test_hors_ligne_les_plafonds_du_serveur_ne_sont_pas_reclames(self):
        _, anomalies = budgets.verifier(budgets.mesures_hors_ligne(), complet=False)
        self.assertEqual(anomalies, [], "hors ligne, seul ce qui est mesuré se juge")

    def test_une_charge_mesuree_deux_fois_est_signalee(self):
        mesures = budgets.mesures_hors_ligne() * 2
        _, anomalies = budgets.verifier(mesures, complet=False)
        self.assertIn("deux fois", " ".join(a.message for a in anomalies))

    def test_un_budget_derive_ne_se_juge_pas_avec_des_membres_manquants(self):
        depassements, anomalies = budgets.verifier(budgets.mesures_hors_ligne(), complet=True)
        self.assertNotIn("premier_ecran", [d.cle for d in depassements])
        self.assertTrue([a for a in anomalies if a.cle == "premier_ecran"],
                        "un budget dérivé incomplet doit être signalé")

    def test_le_rapport_nomme_la_mesure_le_plafond_et_la_marge(self):
        budget = next(b for b in budgets.BUDGETS if b.cle == "page")
        mesure = budgets.mesures_hors_ligne()[0]
        rapport = budgets.rapport_texte([mesure], complet=False)
        self.assertIn(f"{mesure.octets:,}".replace(",", " "), rapport)
        self.assertIn(f"{budget.plafond:,}".replace(",", " "), rapport)
        self.assertIn("marge", rapport)

    def test_le_rapport_du_depassement_dit_quoi_faire(self):
        budget = next(b for b in budgets.BUDGETS if b.cle == "page")
        mesures = [budgets.Mesure("page", budget.plafond + 5_000, "fabriqué")]
        rapport = budgets.rapport_texte(mesures, complet=False)
        self.assertIn("DÉPASSÉ", rapport)
        self.assertIn(budget.sortie_texte, rapport, "un dépassement doit dire la sortie")
        self.assertIn(budget.motif, rapport, "un dépassement doit dire le motif")

    def test_le_rapport_ne_rend_pas_la_sortie_d_un_autre_plafond(self):
        page = next(b for b in budgets.BUDGETS if b.cle == "page")
        mesures = [budgets.Mesure("page", page.plafond + 1, "fabriqué")]
        rapport = budgets.rapport_texte(mesures, complet=False)
        ailleurs = budgets.SORTIES["textes"]
        self.assertNotIn(ailleurs, rapport)


class TestLigneDeCommande(unittest.TestCase):
    """La CI ne lit pas Python : elle lit un code de sortie."""

    @classmethod
    def setUpClass(cls):
        cls.tenu = _lancer_verificateur(_rapport_factice())
        page = next(b for b in budgets.BUDGETS if b.cle == "page")
        cls.franchi = _lancer_verificateur(
            _rapport_factice({"page": page.plafond + 1_000})
        )

    def test_code_zero_quand_les_plafonds_sont_tenus(self):
        self.assertEqual(self.tenu.returncode, 0, self.tenu.stderr[-2_000:])
        self.assertIn("Aucun dépassement", self.tenu.stdout)

    def test_code_un_quand_un_plafond_est_franchi(self):
        self.assertEqual(self.franchi.returncode, 1, self.franchi.stdout[-2_000:])
        self.assertIn("Budget de poids non tenu", self.franchi.stderr)
        self.assertIn("DÉPASSÉ", self.franchi.stdout)

    def test_le_rapport_de_ci_dit_ce_qu_il_a_mesure(self):
        self.assertIn(budgets.DATE_ANCRAGE, self.tenu.stdout)
        self.assertIn("entrées dans la table", self.tenu.stdout)
        self.assertIn("0 dépassement", self.tenu.stdout)


class TestRapportManquant(unittest.TestCase):
    """Un rapport absent ne doit pas se confondre avec un budget franchi."""

    def test_un_rapport_introuvable_est_dit_et_sort_en_code_deux(self):
        resultat = subprocess.run(
            [sys.executable, str(CHEMIN_OUTIL), "--verifier",
             "--rapport-fichier", str(RACINE / "outils" / "rapport-absent.json")],
            cwd=str(RACINE), capture_output=True, text=True, timeout=180,
        )
        self.assertEqual(resultat.returncode, 2, "2 : l'entrée était mauvaise, pas le budget")
        self.assertIn("introuvable", resultat.stderr)

    def test_un_rapport_illisible_est_dit(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write("{ pas du json")
            chemin = f.name
        try:
            resultat = subprocess.run(
                [sys.executable, str(CHEMIN_OUTIL), "--verifier",
                 "--rapport-fichier", chemin],
                cwd=str(RACINE), capture_output=True, text=True, timeout=180,
            )
        finally:
            Path(chemin).unlink(missing_ok=True)
        self.assertEqual(resultat.returncode, 2)
        self.assertIn("illisible", resultat.stderr)


class TestDocumentEtCode(unittest.TestCase):
    """Le document de R&D annonce la table et les chiffres du code.

    Un document de passe qui annonce « quinze plafonds » et « 42 contrôles » se
    périme tout seul dès qu'un plafond ou un contrôle est ajouté : c'est
    exactement ce que le dépôt reproche aux compteurs écrits à la main
    (`outils/verifier-compteurs.py`). Ces trois contrôles-ci font le lien dans
    l'autre sens — celui du document qui doit suivre le code.

    Les passages **datés** (la suite du 14 octobre 2026 dans `docs/19`) gardent
    les chiffres de leur époque, comme le veut la convention du dépôt : ils ne
    sont pas comptés ici.
    """

    DOCUMENTS = ("docs/RD_BUDGETS_DE_FLUIDITE.md", "CHANGELOG.md", "README.md")

    @staticmethod
    def _texte() -> str:
        return "\n".join((RACINE / chemin).read_text(encoding="utf-8")
                         for chemin in TestDocumentEtCode.DOCUMENTS)

    def test_le_document_annonce_les_ancres_et_les_plafonds_du_code(self):
        texte = self._texte()
        for budget in budgets.BUDGETS:
            with self.subTest(budget=budget.cle):
                ancre = f"{budget.ancre:,}".replace(",", " ")
                plafond = f"{budget.plafond:,}".replace(",", " ")
                self.assertIn(plafond, texte,
                              f"{budget.cle} : le plafond {plafond} o n'est annoncé nulle part")
                self.assertIn(f"{ancre} o", texte,
                              f"{budget.cle} : l'ancre {ancre} o n'est annoncée nulle part")

    def test_le_tableau_du_document_a_autant_de_lignes_que_de_plafonds(self):
        document = (RACINE / "docs" / "RD_BUDGETS_DE_FLUIDITE.md").read_text(encoding="utf-8")
        lignes = [ligne for ligne in document.splitlines()
                  if ligne.startswith("| ") and ligne.rstrip().endswith(" o |")]
        self.assertEqual(len(lignes), len(budgets.BUDGETS),
                         "le tableau des plafonds du document n'a plus le bon nombre de lignes")

    def test_les_documents_annoncent_le_nombre_exact_de_controles(self):
        suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
        nombre = suite.countTestCases()
        for chemin in self.DOCUMENTS:
            with self.subTest(document=chemin):
                texte = (RACINE / chemin).read_text(encoding="utf-8")
                self.assertIn(f"{nombre} contrôles", texte,
                              f"{chemin} annonce un nombre de contrôles qui n'est plus le bon "
                              f"(le fichier en compte {nombre})")


class TestOutilsCoherents(unittest.TestCase):
    """L'outil de mesure et la table des plafonds ne peuvent pas diverger."""

    def test_l_outil_partage_la_table_des_plafonds(self):
        # Même objet, pas une copie : deux copies de la table divergeraient en
        # silence, et c'est la mesure qui lirait la mauvaise.
        self.assertIs(outil.plafonds, budgets)
        self.assertEqual(outil.plafonds.ROUTES_MESUREES, budgets.ROUTES_MESUREES)

    def test_le_rapport_de_mesure_porte_les_charges_du_budget(self):
        attendues = {b.cle for b in budgets.BUDGETS if b.ou != "derive"}
        self.assertTrue(attendues.issubset({cle for cle, _, _ in outil.plan_de_mesure()}))

    def test_la_page_en_ligne_et_le_fichier_publie_sont_le_meme_document(self):
        # Le budget couvre les deux : si le fichier publié n'était plus engendré
        # depuis le module, son poids suivrait sa propre route.
        self.assertGreater(budgets.octets_de_la_page_publiee(), 50_000)
        self.assertGreater(budgets.octets_de_la_page_du_module(), 50_000)


if __name__ == "__main__":
    unittest.main()
