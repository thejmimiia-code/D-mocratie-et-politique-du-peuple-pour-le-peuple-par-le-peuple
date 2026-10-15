"""
tests/test_premier_ecran.py — ce qu'un téléphone voit avant la première ligne.

Le visiteur l'a dit autrement : « lecture claire et confortable sur un
smartphone ». Mesuré dans Chromium le 15 octobre 2026, à 380 px, la page prenait
**863 px** de cadre — bandeau 566, sommaire 58, ruban 239 — avant le premier mot
de contenu, sur un écran de 780. Le contenu existait ; il n'était pas visible.

Ce fichier tient les quatre promesses de la réponse :

1. **le premier écran se mesure** — `outils/plafonds_premier_ecran.mjs` dit ce
   que valent bandeau + sommaire + ruban, et ce qu'ils valent au maximum ;
2. **un plafond est ancré** — chacun porte la mesure datée dont il vient, et
   aucun n'est *au-dessus* de cette mesure : un plafond qui autorise le statu
   quo ne plafonne rien ;
3. **seul le téléphone est plafonné** — au large, il y a la place ; un plafond
   qui ne se déclenche jamais est du bruit ;
4. **la page tient ce que le plafond suppose** — les règles du palier 480 px
   sont lues dans la feuille servie : les quatre commandes du ruban sur une
   rangée, deux libellés dont un seul est peint, l'horizon dit une fois, et
   aucun texte sous `--t-min`.

Ce qui demande un navigateur — la photographie — vit dans le travail
d'intégration continue ; ce qui n'en demande pas est éprouvé ici.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from outils import contraste_ecran  # noqa: E402
from simulateur.interface import HTML_PAGE  # noqa: E402

NODE = shutil.which("node")
MODULE_PLAFONDS = RACINE / "outils" / "plafonds_premier_ecran.mjs"
RUNNER = RACINE / "tests" / "plafonds_premier_ecran.mjs"
CAPTURES = RACINE / "outils" / "captures_ecran.mjs"

#: Les largeurs de téléphone : celles qu'un visiteur tient dans une main.
LARGEURS_TELEPHONE = (380, 640)


def _css() -> str:
    return contraste_ecran.feuille_de_la_page(HTML_PAGE)


def _declarations(corps: str) -> dict[str, str]:
    return {nom.strip(): valeur.strip().replace("!important", "").strip()
            for nom, valeur in re.findall(r"([-\w]+)\s*:\s*([^;]+)", corps)}


def _regles_dans(selecteur: str, *fragments: str) -> list[tuple[tuple[str, ...], dict[str, str]]]:
    """Les règles dont la liste contient ce sélecteur **et** dont un média colle.

    Rendues avec leur contexte : une règle de palier n'est pas la règle de base,
    et les confondre ferait passer un écran large pour un téléphone.
    """
    sortie = []
    for contexte, liste, corps in contraste_ecran.regles(_css()):
        if selecteur not in [morceau.strip() for morceau in liste.split(",")]:
            continue
        if all(any(fragment in bloc for bloc in contexte) for fragment in fragments):
            sortie.append((contexte, _declarations(corps)))
    return sortie


def _pose(regles: list[tuple[tuple[str, ...], dict[str, str]]]) -> dict[str, str]:
    """La dernière règle, celle qui gagne à la cascade."""
    return regles[-1][1] if regles else {}


def _plafonds() -> dict:
    """Les plafonds, tels que le module les publie — exécuté, pas relu."""
    programme = (f"import {{ PLAFONDS }} from {MODULE_PLAFONDS.as_uri()!r};"
                 "console.log(JSON.stringify(PLAFONDS));")
    resultat = subprocess.run([NODE, "--input-type=module", "-e", programme],
                              capture_output=True, text=True, cwd=str(RACINE))
    if resultat.returncode != 0:
        raise AssertionError(f"le module de plafonds ne s'exécute pas : {resultat.stderr}")
    charge = json.loads(resultat.stdout)
    return {int(largeur): limite for largeur, limite in charge.items()}


def _verdict(vues: list[dict], plafonds: dict | None = None) -> tuple[int, dict]:
    """Joue les plafonds sur des vues, comme le ferait la photographie."""
    with tempfile.TemporaryDirectory() as dossier:
        chemin = Path(dossier) / "vues.json"
        chemin.write_text(json.dumps(vues), encoding="utf-8")
        commande = [NODE, str(RUNNER), str(chemin)]
        if plafonds is not None:
            chemin_plafonds = Path(dossier) / "plafonds.json"
            chemin_plafonds.write_text(json.dumps(plafonds), encoding="utf-8")
            commande.append(str(chemin_plafonds))
        resultat = subprocess.run(commande, capture_output=True, text=True, cwd=str(RACINE))
    return resultat.returncode, json.loads(resultat.stdout)


def _vue(largeur: int, bandeau: int, sommaire: int, ruban: int, nom: str = "vue") -> dict:
    return {"nom": nom, "largeur": largeur,
            "premier_ecran": {"bandeau": bandeau, "sommaire": sommaire, "ruban": ruban,
                              "total": bandeau + sommaire + ruban}}


class TestLesPlafonds(unittest.TestCase):
    """Un plafond sans mesure datée est un chiffre choisi, pas une mesure tenue."""

    @classmethod
    def setUpClass(cls):
        if NODE is None:
            raise unittest.SkipTest("node absent : les plafonds ne s'exécutent pas")
        cls.plafonds = _plafonds()

    def test_les_largeurs_de_telephone_sont_plafonnees(self):
        for largeur in LARGEURS_TELEPHONE:
            with self.subTest(largeur=largeur):
                self.assertIn(largeur, self.plafonds,
                              f"aucun plafond à {largeur} px : le premier écran y dérive")

    def test_chaque_plafond_porte_sa_mesure_datee(self):
        for largeur, limite in self.plafonds.items():
            with self.subTest(largeur=largeur):
                self.assertGreater(limite["mesure"], 0,
                                   "un plafond sans mesure ne vient de nulle part")
                self.assertTrue(re.search(r"\d{4}", limite["quand"]),
                                f"« {limite['quand']} » ne dit pas quand la mesure a été prise")
                self.assertTrue(limite["quoi"].strip(),
                                "la mesure ne dit pas de quoi elle est faite")

    def test_aucun_plafond_n_autorise_le_statu_quo(self):
        """Un plafond au-dessus de sa mesure décrit l'existant au lieu de le corriger."""
        for largeur, limite in self.plafonds.items():
            with self.subTest(largeur=largeur):
                self.assertLess(limite["plafond"], limite["mesure"],
                                f"à {largeur} px, le plafond de {limite['plafond']} px "
                                f"autorise les {limite['mesure']} px mesurés")

    def test_seul_le_telephone_est_plafonne(self):
        """Au large, le premier écran fait 394 px sur 900 : un plafond y serait du bruit."""
        source = CAPTURES.read_text(encoding="utf-8")
        largeurs = re.search(r"largeurs:\s*\[([^\]]+)\]", source)
        self.assertIsNotNone(largeurs, "les largeurs photographiées ne se lisent plus")
        photographiees = {int(valeur) for valeur in re.findall(r"\d+", largeurs.group(1))}
        for largeur in self.plafonds:
            with self.subTest(largeur=largeur):
                self.assertIn(largeur, photographiees,
                              f"un plafond à {largeur} px ne serait jamais mesuré")
        self.assertEqual({int(largeur) for largeur in self.plafonds},
                         set(LARGEURS_TELEPHONE),
                         "les plafonds couvrent d'autres largeurs que celles du téléphone")


class TestLeVerdict(unittest.TestCase):
    """Le verdict nomme la vue, la mesure, le plafond, et de combien ça dépasse."""

    @classmethod
    def setUpClass(cls):
        if NODE is None:
            raise unittest.SkipTest("node absent : les plafonds ne s'exécutent pas")

    def test_une_vue_au_dessus_est_refusee_avec_ses_chiffres(self):
        code, verdict = _verdict([_vue(380, 566, 58, 239, "accueil-jour-380")])
        self.assertEqual(code, 1, "un dépassement n'a pas fait échouer le contrôle")
        self.assertEqual(len(verdict["depassements"]), 1)
        depassement = verdict["depassements"][0]
        self.assertEqual(depassement["nom"], "accueil-jour-380")
        self.assertEqual(depassement["exces"], 863 - depassement["plafond"])
        for morceau in ("bandeau 566", "sommaire 58", "ruban 239"):
            self.assertIn(morceau, depassement["phrase"],
                          "le verdict ne dit pas où la place se perd")

    def test_une_vue_sous_le_plafond_passe(self):
        code, verdict = _verdict([_vue(380, 400, 58, 150)])
        self.assertEqual(code, 0, "une vue sous le plafond a été refusée")
        self.assertEqual(verdict["depassements"], [])
        self.assertTrue(any("tenu" in ligne for ligne in verdict["lignes"]))

    def test_une_largeur_sans_plafond_n_est_jamais_signalee(self):
        """Le grand écran n'est pas plafonné : 394 px sur 900, il y a la place."""
        code, verdict = _verdict([_vue(1280, 248, 66, 80)])
        self.assertEqual(code, 0)
        self.assertEqual(verdict["depassements"], [])

    def test_une_vue_sans_mesure_est_signalee(self):
        """On ne tient pas un plafond sur ce qu'on ne mesure pas."""
        code, verdict = _verdict([{"nom": "accueil-sans-mesure", "largeur": 380}])
        self.assertEqual(code, 1)
        self.assertIsNone(verdict["depassements"][0]["mesure"])
        self.assertIn("ne porte pas de mesure", verdict["depassements"][0]["phrase"])

    def test_le_plafond_est_lu_dans_le_module_et_non_recopie(self):
        """Le runner accepte des plafonds de passage : c'est ce qui le rend éprouvable."""
        code, verdict = _verdict([_vue(380, 566, 58, 239)], {380: {"plafond": 2000,
                                                                  "mesure": 863,
                                                                  "quand": "2026",
                                                                  "quoi": "essai"}})
        self.assertEqual(code, 0, "le runner a ignoré les plafonds qu'on lui donne")
        self.assertEqual(verdict["depassements"], [])


class TestLaMesureEstBranchee(unittest.TestCase):
    """Un plafond qu'on se contente d'afficher ne plafonne rien."""

    def test_l_outil_mesure_les_trois_cadres_du_premier_ecran(self):
        source = CAPTURES.read_text(encoding="utf-8")
        self.assertIn('hauteurDe(".entete")', source)
        self.assertIn('hauteurDe(".sommaire")', source)
        self.assertIn('hauteurDe(".ruban-veille")', source)
        self.assertIn("total: bandeau + sommaire + ruban", source,
                      "le premier écran n'est plus la somme de ses cadres")

    def test_l_outil_echoue_quand_un_plafond_est_depasse(self):
        source = CAPTURES.read_text(encoding="utf-8")
        self.assertIn("depassements(rapport)", source,
                      "l'outil ne confronte plus ses mesures aux plafonds")
        self.assertIn("process.exit(1)", source,
                      "un plafond dépassé ne fait plus échouer la photographie")

    def test_l_outil_publie_le_verdict_dans_le_resume(self):
        source = CAPTURES.read_text(encoding="utf-8")
        self.assertIn("lignes_premier_ecran(rapport)", source,
                      "le résumé ne dit plus où en est le premier écran")
        self.assertIn("plan(\".ruban-veille\")", source,
                      "le ruban n'est plus détaillé : on ne saurait pas où il prend sa hauteur")


class TestLaPageTientLePlafond(unittest.TestCase):
    """Les règles du palier 480 px, relues dans la feuille servie."""

    def _telephone(self, selecteur: str) -> list[tuple[tuple[str, ...], dict[str, str]]]:
        return _regles_dans(selecteur, "max-width:480px")

    def test_quatre_commandes_tiennent_sur_une_rangee(self):
        """Deux rangées de 44 px coûtaient 51 px de haut pour 44 px de boutons."""
        pose = self._telephone(".ruban-veille .ruban-actions")
        self.assertTrue(pose, "les commandes du ruban ne sont plus réglées pour un téléphone")
        colonnes = _pose(pose).get("grid-template-columns", "")
        self.assertIn("repeat(4", colonnes.replace(" ", ""),
                      f"les quatre commandes ne tiennent plus sur une rangée : {colonnes}")

    def test_la_cible_du_doigt_n_a_pas_ete_rognee(self):
        """44 px : c'est la cible du doigt, pas du décor."""
        for _contexte, pose in self._telephone(".ruban-veille .ruban-actions button"):
            with self.subTest(pose=pose):
                self.assertNotIn("min-height", pose,
                                 "la règle du téléphone rabote la hauteur du bouton")
                self.assertNotIn("height", pose, "la règle du téléphone fixe la hauteur")
                if "font-size" in pose:
                    self.assertRegex(pose["font-size"], r"max\(var\(--t-min\)",
                                     "un libellé de commande sous le plancher de lecture : "
                                     + pose["font-size"])

    def test_un_seul_libelle_est_peint_a_la_fois(self):
        """Le long dit tout, le court tient dans 80 px : jamais les deux ensemble."""
        base = [pose for contexte, pose in _regles_dans(".ruban-veille .mot-court")
                if not contexte]
        self.assertTrue(base, "le libellé court n'est plus masqué au large")
        self.assertEqual(base[-1].get("display"), "none")
        courts = self._telephone(".ruban-veille .mot-court")
        longs = self._telephone(".ruban-veille .mot-long")
        self.assertEqual(_pose(courts).get("display"), "inline",
                         "le libellé court ne s'affiche pas sur un téléphone")
        self.assertEqual(_pose(longs).get("display"), "none",
                         "le libellé long reste peint sur un téléphone")

    def test_chaque_commande_du_ruban_porte_ses_deux_libelles(self):
        for identifiant in ("btn-console-details", "btn-densite", "aller-leviers", "aller-audit"):
            with self.subTest(bouton=identifiant):
                self.assertIn(f'id="{identifiant}-long"', HTML_PAGE,
                              f"{identifiant} n'a plus de libellé long repéré")
                self.assertIn(f'id="{identifiant}-court"', HTML_PAGE,
                              f"{identifiant} n'a plus de libellé court repéré")

    def test_les_deux_libelles_sont_ecrits_ensemble(self):
        """Sinon le premier clic remet le libellé long, et le ruban regonfle."""
        source = HTML_PAGE[HTML_PAGE.index("function direLeBouton"):]
        source = source[:source.index("\nfunction ", 10)]
        self.assertIn("'-long'", source, "le libellé long n'est plus écrit")
        self.assertIn("'-court'", source, "le libellé court n'est plus écrit")
        self.assertIn("bouton.textContent = long", source,
                      "une page sans repères ne retombe plus sur le libellé long")
        for fonction in ("function basculerDensite", "function basculerDetailsConsole"):
            with self.subTest(fonction=fonction):
                corps = HTML_PAGE[HTML_PAGE.index(fonction):][:1400]
                self.assertIn("direLeBouton(", corps,
                              f"{fonction} écrit encore un seul libellé")
                self.assertNotIn("bouton.textContent =", corps,
                                 f"{fonction} réécrit le bouton en clair, spans compris")

    def test_l_horizon_ne_se_dit_qu_une_fois_sur_un_telephone(self):
        """Le select porte l'horizon ; la pastille le répétait sur une rangée entière."""
        cache = self._telephone("#badge-horizon")
        self.assertTrue(cache, "la pastille d'horizon n'est plus écartée sur un téléphone")
        self.assertEqual(_pose(cache).get("display"), "none")
        self.assertNotIn('id="horizon-simulation" class', HTML_PAGE)
        self.assertIn('id="horizon-simulation"', HTML_PAGE,
                      "le select qui porte l'horizon a disparu : il ne se dit plus du tout")
        self.assertIn("changerHorizon", HTML_PAGE,
                      "rien ne relie plus le select à l'état de la page")

    def test_la_barre_du_bandeau_se_range_en_deux_colonnes(self):
        """Trois rangées dont une trouée pour quatre commandes : deux suffisent."""
        pose = self._telephone("header.entete .barre-contexte")
        self.assertTrue(pose, "la barre du bandeau n'est plus réglée pour un téléphone")
        colonnes = _pose(pose).get("grid-template-columns", "").replace(" ", "")
        self.assertIn("repeat(2", colonnes,
                      f"la barre ne se range plus en deux colonnes : {colonnes}")

    def test_la_lecture_ne_retrecit_pas(self):
        """C'est la mise en page qui se resserre, pas le texte qui rétrécit."""
        for selecteur in ("header.entete h1", "header.entete .accroche"):
            with self.subTest(selecteur=selecteur):
                for _contexte, pose in self._telephone(selecteur):
                    if "font-size" in pose:
                        self.assertRegex(pose["font-size"], r"max\(var\(--t-min\)",
                                         f"{selecteur} rétrécit sous le plancher de lecture")


if __name__ == "__main__":
    unittest.main()
