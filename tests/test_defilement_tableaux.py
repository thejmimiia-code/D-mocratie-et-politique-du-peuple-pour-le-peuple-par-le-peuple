"""Le JavaScript qui enveloppe les tableaux larges, exécuté pour de vrai.

`tests/test_interface.py` vérifie que la page *déclare* des régions défilantes.
Ici, on exécute les deux fonctions livrées sur un DOM minimal, pour vérifier ce
qu'elles font vraiment : un tableau large reçoit sa région nommée, un tableau
déjà défilant n'est pas enveloppé deux fois, le tableau n'est pas modifié et
l'ordre du document est conservé.

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

#: Le fragment testé est **celui de la page**, pas une copie : si quelqu'un
#: réécrit la fonction, c'est la nouvelle version qui est éprouvée ici.
DEBUT = "function tableauDejaDefilant("
FIN = "function marquerSommaire("

DOM_PARTAGE = RACINE / "tests" / "dom_minimal.mjs"

PROGRAMME = r"""

const document = new Document();
const section = document.createElement("section");
document.body.appendChild(section);

// 1. Un tableau large, nu : il doit recevoir sa région.
const large = document.createElement("table");
large.setAttribute("data-legende", "Comptes nationaux simulés");
section.appendChild(large);

// 2. Un tableau déjà défilant : on n'y touche pas.
const deja = document.createElement("div");
deja.className = "defilable";
const dansDefilable = document.createElement("table");
deja.appendChild(dansDefilable);
section.appendChild(deja);

// 3. Un tableau déjà enveloppé : pas de double enveloppe.
const enveloppe = document.createElement("div");
enveloppe.className = "tableau-defilant";
const dejaEnveloppe = document.createElement("table");
enveloppe.appendChild(dejaEnveloppe);
section.appendChild(enveloppe);

const connus = [large, deja, enveloppe];
const poses = rendreTableauxDefilants();
const enfants = section.enfants;
const region = enfants.find(noeud => connus.indexOf(noeud) < 0) || null;

const rapport = {
  poses: poses,
  nombreDElements: enfants.length,
  rangRegion: region ? enfants.indexOf(region) : -1,
  region: region ? region.tagName : null,
  role: region ? region.getAttribute("role") : null,
  tabindex: region ? region.getAttribute("tabindex") : null,
  etiquette: region ? region.getAttribute("aria-label") : null,
  contientLeTableau: !!region && region.enfants.length === 1 && region.enfants[0] === large,
  tableauIntact: large.getAttribute("data-legende"),
  defilableIntact: enfants.indexOf(deja) >= 0 && deja.enfants[0] === dansDefilable,
  envelopeIntacte: enfants.indexOf(enveloppe) >= 0 && enveloppe.enfants[0] === dejaEnveloppe,
};
console.log(JSON.stringify(rapport));
"""


@unittest.skipIf(NODE is None, "Node.js n'est pas installé : contrôle d'exécution ignoré")
class TestDefilementDesTableaux(unittest.TestCase):
    """Le tableau large défile dans sa région ; rien d'autre ne bouge."""

    @classmethod
    def setUpClass(cls):
        script = "\n".join(re.findall(r"<script>(.*?)</script>", HTML_PAGE, re.S))
        debut = script.index(DEBUT)
        fin = script.index(FIN)
        cls.fragment = script[debut:fin]
        with tempfile.TemporaryDirectory(prefix="tableaux-defilants-") as temporaire:
            chemin = Path(temporaire) / "essai.mjs"
            import_ = f'import {{ Document }} from "{DOM_PARTAGE.as_uri()}";\n'
            chemin.write_text(import_ + cls.fragment + PROGRAMME, encoding="utf-8")
            resultat = subprocess.run([NODE, str(chemin)], capture_output=True, text=True, timeout=120)
        cls.retour = resultat
        if resultat.returncode == 0:
            cls.rapport = json.loads(resultat.stdout.strip().splitlines()[-1])
        else:
            cls.rapport = None

    def test_le_fragment_existe_dans_la_page(self):
        self.assertIn("function rendreTableauxDefilants(", self.fragment)

    def test_le_script_tourne_sans_erreur(self):
        self.assertEqual(self.retour.returncode, 0,
                         self.retour.stdout + self.retour.stderr)
        self.assertIsNotNone(self.rapport, self.retour.stdout + self.retour.stderr)

    def test_un_seul_tableau_a_ete_enveloppe(self):
        """Le tableau nu, et lui seul."""
        self.assertEqual(self.rapport["poses"], 1)

    def test_la_region_est_nommee_et_atteignable_au_clavier(self):
        self.assertEqual(self.rapport["region"], "DIV")
        self.assertEqual(self.rapport["role"], "region")
        self.assertEqual(self.rapport["tabindex"], "0")
        self.assertIn("Comptes nationaux simulés", self.rapport["etiquette"])
        self.assertIn("faites défiler horizontalement", self.rapport["etiquette"])

    def test_le_tableau_est_deplace_sans_etre_modifie(self):
        """Même objet, même légende : les chiffres restent ceux du moteur."""
        self.assertTrue(self.rapport["contientLeTableau"],
                        "le tableau d'origine n'est pas dans la région")
        self.assertEqual(self.rapport["tableauIntact"], "Comptes nationaux simulés")
        # La région prend la place du tableau, et une seule : le tableau large
        # n'est plus enfant direct de la section, il est dans sa région, à sa
        # place dans l'ordre de lecture.
        self.assertEqual(self.rapport["nombreDElements"], 3)
        self.assertEqual(self.rapport["rangRegion"], 0)

    def test_les_tableaux_deja_defilants_ne_sont_pas_touches(self):
        self.assertTrue(self.rapport["defilableIntact"],
                        "le tableau déjà défilant a été déplacé")
        self.assertTrue(self.rapport["envelopeIntacte"],
                        "un tableau déjà enveloppé l'a été deux fois")
