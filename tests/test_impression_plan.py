"""L'impression d'un plan, exécutée pour de vrai : ouverture, tirage, retour.

Trois comportements qu'aucune relecture de texte ne peut prouver, donc éprouvés
ici sur un DOM minimal (`tests/dom_minimal.mjs`) :

* le mode « mon plan » se pose sur la racine du document — c'est lui que la
  feuille de style écoute pour ne garder que le résumé ;
* `window.print()` est appelé **une fois par demande**, jamais au chargement de
  la page : un tirage surprise serait le pire des défauts ;
* la page revient entière, et le focus revient sur le bouton qui a ouvert le
  mode au lieu de se perdre dans une barre qui disparaît ;
* une impression refusée par le navigateur ne laisse ni exception ni page
  amputée : le bandeau offre de réessayer ou de revenir.

Ce test saute proprement si Node.js n'est pas installé.
"""

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from simulateur.interface import HTML_PAGE

RACINE = Path(__file__).resolve().parent.parent
NODE = shutil.which("node")
DOM_PARTAGE = RACINE / "tests" / "dom_minimal.mjs"

DEBUT = "function pointerGrossier("
FIN = "/* ── Lecture en clair"

PROGRAMME_IMPRESSION = r"""
/* Une racine, un bouton déclencheur, et une fenêtre qui compte les impressions
   au lieu de les ouvrir : rien d'autre n'est nécessaire, et tout le reste jette
   (voir dom_minimal.mjs). */
const racine = document.createElement("html");
document.documentElement = racine;
const declencheur = document.createElement("button");
declencheur.classList.add("discret");
declencheur.focus = function () { declencheur.focalise = true; };
document.getElementById = (id) => (id === "bouton-imprimer-plan" ? declencheur : null);

let impressions = 0;
globalThis.window = { print(){ impressions += 1; } };

const rapport = { avant: racine.classList.contains("impression-plan") };
rapport.ouvert = imprimerPlan();
rapport.pendant = racine.classList.contains("impression-plan");
rapport.impressions1 = impressions;
// Le bandeau du mode relance l'impression sans quitter le mode.
rapport.relance = lancerImpression();
rapport.impressions2 = impressions;
rapport.modeTenu = racine.classList.contains("impression-plan");
// Puis on revient à la page entière.
rapport.quitte = quitterImpressionPlan();
rapport.apres = racine.classList.contains("impression-plan");
rapport.focusRendu = declencheur.focalise === true;
rapport.impressionsFin = impressions;

// Deuxième situation : le navigateur refuse l'impression.
let refusees = 0;
globalThis.window = { print(){ refusees += 1; throw new Error("refus"); } };
const racine2 = document.createElement("html");
document.documentElement = racine2;
rapport.refusSansException = (function(){
  try { imprimerPlan(); return true; } catch (erreur) { return false; }
})();
rapport.refusCompte = refusees;
rapport.refusGardeLeMode = racine2.classList.contains("impression-plan");
rapport.refusSeRepare = (quitterImpressionPlan() && !racine2.classList.contains("impression-plan"));

// Troisième situation : un navigateur sans impression programmée.
globalThis.window = {};
const racine3 = document.createElement("html");
document.documentElement = racine3;
rapport.sansPrintRendFaux = imprimerPlan() === false;
rapport.sansPrintGardeLeMode = racine3.classList.contains("impression-plan");
rapport.sansPrintSeRepare = (quitterImpressionPlan() && !racine3.classList.contains("impression-plan"));

// Quatrième situation : un document sans racine (page en cours de construction).
globalThis.window = { print(){ throw new Error("ne doit pas être appelé"); } };
delete document.documentElement;
rapport.sansRacineRendFaux = imprimerPlan() === false;

console.log(JSON.stringify(rapport));
"""


@unittest.skipIf(NODE is None, "Node.js n'est pas installé : contrôle d'exécution ignoré")
class TestImpressionDuPlanExecutee(unittest.TestCase):
    """Le mode s'ouvre, l'impression part sur demande, la page revient entière."""

    @classmethod
    def setUpClass(cls):
        script = "\n".join(re.findall(r"<script>(.*?)</script>", HTML_PAGE, re.S))
        fragment = script[script.index(DEBUT):script.index(FIN)]
        with tempfile.TemporaryDirectory(prefix="impression-plan-") as temporaire:
            chemin = Path(temporaire) / "essai.mjs"
            import_ = f'import {{ Document }} from "{DOM_PARTAGE.as_uri()}";\n'
            chemin.write_text(import_ + "const document = new Document();\n" + fragment
                              + PROGRAMME_IMPRESSION, encoding="utf-8")
            cls.retour = subprocess.run([NODE, str(chemin)], capture_output=True,
                                        text=True, timeout=120)
        cls.rapport = (json.loads(cls.retour.stdout.strip().splitlines()[-1])
                       if cls.retour.returncode == 0 else None)

    def test_le_script_tourne_sans_erreur(self):
        self.assertEqual(self.retour.returncode, 0, self.retour.stdout + self.retour.stderr)
        self.assertIsNotNone(self.rapport, self.retour.stdout + self.retour.stderr)

    def test_le_mode_s_ouvre_sur_la_racine_du_document(self):
        self.assertFalse(self.rapport["avant"], "rien n'est posé avant la demande")
        self.assertTrue(self.rapport["ouvert"])
        self.assertTrue(self.rapport["pendant"], "la feuille de style écoute cette classe")

    def test_l_impression_part_une_fois_par_demande(self):
        self.assertEqual(self.rapport["impressions1"], 1)
        self.assertEqual(self.rapport["impressions2"], 2, "le bandeau relance un tirage")
        self.assertTrue(self.rapport["modeTenu"], "relancer l'impression ne quitte pas le mode")

    def test_revenir_ramene_la_page_entiere_et_le_focus(self):
        self.assertTrue(self.rapport["quitte"])
        self.assertFalse(self.rapport["apres"])
        self.assertTrue(self.rapport["focusRendu"],
                        "le focus revient au bouton, pas dans une barre qui disparaît")
        self.assertEqual(self.rapport["impressionsFin"], 2, "aucun tirage supplémentaire")

    def test_une_impression_refusee_ne_casse_rien(self):
        self.assertTrue(self.rapport["refusSansException"])
        self.assertEqual(self.rapport["refusCompte"], 1)
        self.assertTrue(self.rapport["refusGardeLeMode"], "le bandeau sert à réessayer")
        self.assertTrue(self.rapport["refusSeRepare"])

    def test_un_navigateur_sans_impression_programmee_reste_utilisable(self):
        self.assertTrue(self.rapport["sansPrintRendFaux"])
        self.assertTrue(self.rapport["sansPrintGardeLeMode"])
        self.assertTrue(self.rapport["sansPrintSeRepare"])
        self.assertTrue(self.rapport["sansRacineRendFaux"],
                        "un document sans racine rend faux, sans exception")
