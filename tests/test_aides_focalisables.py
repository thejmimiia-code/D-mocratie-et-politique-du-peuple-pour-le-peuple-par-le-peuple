"""Les aides de la page, exécutées pour de vrai : au doigt et au clavier.

Deux comportements invisibles au simple examen du texte, donc éprouvés ici sur
un DOM minimal (`tests/dom_minimal.mjs`) :

* une infobulle s'ouvre au survol **et au focus** ; sur un appareil tactile, ni
  l'un ni l'autre n'existent — les éléments annotés qui ne sont pas déjà des
  boutons, des liens ou des champs doivent donc devenir focalisables ;
* sur ordinateur, personne ne doit hériter de vingt-sept arrêts de tabulation
  supplémentaires pour autant ;
* le sommaire ouvert au doigt se referme une fois la destination choisie.

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

PROGRAMME_AIDES = r"""
const page = document.body;
const bouton = document.createElement("button");
bouton.setAttribute("data-aide", "un bouton");
const lien = document.createElement("a");
lien.setAttribute("data-aide", "un lien");
const texte = document.createElement("span");
texte.setAttribute("data-aide", "un texte explicatif");
const levier = document.createElement("div");
levier.setAttribute("data-aide-levier", "un levier");
const dejaFocalisable = document.createElement("span");
dejaFocalisable.setAttribute("data-aide", "déjà focalisable autrement");
dejaFocalisable.setAttribute("tabindex", "-1");
const champ = document.createElement("input");
champ.setAttribute("data-aide", "un champ de saisie");
for (const noeud of [bouton, lien, texte, levier, dejaFocalisable, champ]) page.appendChild(noeud);

globalThis.window = {};                    // ordinateur : pas de matchMedia
const sansTactile = rendreAidesFocalisables();
const poses = rendreAidesFocalisables(true);   // appareil tactile
const poses2 = rendreAidesFocalisables(true);  // deuxième passage : rien à faire

console.log(JSON.stringify({
  sansTactile: sansTactile,
  poses: poses,
  poses2: poses2,
  texte: texte.getAttribute("tabindex"),
  levier: levier.getAttribute("tabindex"),
  bouton: bouton.getAttribute("tabindex"),
  lien: lien.getAttribute("tabindex"),
  champ: champ.getAttribute("tabindex"),
  dejaFocalisable: dejaFocalisable.getAttribute("tabindex"),
}));
"""

PROGRAMME_SOMMAIRE = r"""
const nav = document.createElement("nav");
nav.className = "sommaire ouverte";
const bouton = document.createElement("button");
bouton.setAttribute("aria-expanded", "true");
const lien = document.createElement("a");
document.body.appendChild(nav);
nav.appendChild(bouton);
nav.appendChild(lien);
document.getElementById = (id) => {
  if (id === "sommaire") return nav;
  if (id === "sommaire-bascule") return bouton;
  return null;
};

marquerSommaire(lien);

const rapport = {
  ouverte: nav.classList.contains("ouverte"),
  classeDuLien: lien.classList.contains("actif"),
  annonce: bouton.getAttribute("aria-expanded"),
};

// Le sommaire déjà refermé reste refermé.
const nav2 = document.createElement("nav");
nav2.className = "sommaire";
const bouton2 = document.createElement("button");
bouton2.setAttribute("aria-expanded", "false");
document.getElementById = (id) => {
  if (id === "sommaire") return nav2;
  if (id === "sommaire-bascule") return bouton2;
  return null;
};
marquerSommaire(null);
rapport.resteFermee = !nav2.classList.contains("ouverte");
rapport.annonceInchangee = bouton2.getAttribute("aria-expanded");
console.log(JSON.stringify(rapport));
"""


@unittest.skipIf(NODE is None, "Node.js n'est pas installé : contrôle d'exécution ignoré")
class _EssaiNode(unittest.TestCase):
    """Outil commun : extrait les fonctions livrées et les fait tourner."""

    programme = ""

    @classmethod
    def _executer(cls, programme):
        script = "\n".join(re.findall(r"<script>(.*?)</script>", HTML_PAGE, re.S))
        fragment = script[script.index(DEBUT):script.index(FIN)]
        with tempfile.TemporaryDirectory(prefix="aides-page-") as temporaire:
            chemin = Path(temporaire) / "essai.mjs"
            import_ = f'import {{ Document }} from "{DOM_PARTAGE.as_uri()}";\n'
            chemin.write_text(import_ + "const document = new Document();\n" + fragment + programme,
                              encoding="utf-8")
            resultat = subprocess.run([NODE, str(chemin)], capture_output=True, text=True, timeout=120)
        return resultat

    @classmethod
    def setUpClass(cls):
        cls.retour = cls._executer(cls.programme)
        cls.rapport = (json.loads(cls.retour.stdout.strip().splitlines()[-1])
                       if cls.retour.returncode == 0 else None)


class TestAidesFocalisables(_EssaiNode):
    """Une aide se consulte au doigt, sans polluer le clavier d'un ordinateur."""

    programme = PROGRAMME_AIDES

    def test_le_script_tourne_sans_erreur(self):
        self.assertEqual(self.retour.returncode, 0, self.retour.stdout + self.retour.stderr)
        self.assertIsNotNone(self.rapport, self.retour.stdout + self.retour.stderr)

    def test_sans_appareil_tactile_aucun_arret_n_est_ajoute(self):
        self.assertEqual(self.rapport["sansTactile"], 0)

    def test_sur_appareil_tactile_les_annotations_non_focalisables_le_deviennent(self):
        self.assertEqual(self.rapport["poses"], 2, "le texte et le levier annotés")
        self.assertEqual(self.rapport["texte"], "0")
        self.assertEqual(self.rapport["levier"], "0")

    def test_les_elements_deja_focalisables_ne_sont_pas_touches(self):
        self.assertIsNone(self.rapport["bouton"])
        self.assertIsNone(self.rapport["lien"])
        self.assertIsNone(self.rapport["champ"])
        self.assertEqual(self.rapport["dejaFocalisable"], "-1",
                         "un élément qui a déjà un ordre de tabulation est laissé tel quel")

    def test_le_second_passage_ne_fait_rien(self):
        self.assertEqual(self.rapport["poses2"], 0)


class TestSommaireQuiSeReferme(_EssaiNode):
    """Choisir une destination referme le sommaire ouvert au doigt."""

    programme = PROGRAMME_SOMMAIRE

    def test_le_script_tourne_sans_erreur(self):
        self.assertEqual(self.retour.returncode, 0, self.retour.stdout + self.retour.stderr)
        self.assertIsNotNone(self.rapport, self.retour.stdout + self.retour.stderr)

    def test_le_sommaire_ouvert_se_referme_et_l_annonce_suit(self):
        self.assertFalse(self.rapport["ouverte"])
        self.assertEqual(self.rapport["annonce"], "false")
        self.assertTrue(self.rapport["classeDuLien"], "la destination choisie reste marquée")

    def test_un_sommaire_deja_referme_n_est_pas_touche(self):
        self.assertTrue(self.rapport["resteFermee"])
        self.assertEqual(self.rapport["annonceInchangee"], "false")
