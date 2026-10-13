"""Le passage en cartes, exécuté pour de vrai : qui est étiqueté, et qui ne l'est pas.

Sous 640 px, une ligne de tableau devient une carte : chaque valeur porte le nom
de sa colonne (`data-label`). Ce qui compte ici, c'est la retenue :

* un tableau à deux lignes d'en-tête ne sait pas à quelle colonne appartient une
  valeur : il garde le défilement ;
* un tableau dont une cellule fusionne des colonnes (`colspan`, `rowspan`) ne
  s'étiquette pas non plus ;
* et quand un tableau ne convient pas, **aucune** de ses cellules n'est
  touchée : un tableau à moitié étiqueté serait pire qu'un tableau qui défile.

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

DEBUT = "function tableauEnCartes("
FIN = "function rendreTableauxDefilants("

PROGRAMME = r"""
function tableau(entetes, lignes, secondes){
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  for (const rangee of [entetes].concat(secondes || [])){
    const trh = document.createElement("tr");
    for (const titre of rangee){
      const th = document.createElement("th");
      th.textContent = titre;
      trh.appendChild(th);
    }
    thead.appendChild(trh);
  }
  table.appendChild(thead);
  const tbody = document.createElement("tbody");
  for (const ligne of lignes){
    const tr = document.createElement("tr");
    for (const cellule of ligne){
      const td = document.createElement(cellule.balise || "td");
      td.textContent = cellule.valeur;
      if (cellule.fusion) td.setAttribute(cellule.fusion, "2");
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  return table;
}

const etiquettes = (table) => table.querySelectorAll("tbody tr")
  .map(ligne => ligne.querySelectorAll("td, th").map(cellule => cellule.getAttribute("data-label")));
const v = (valeur) => ({ valeur: valeur });

const rapport = {};

// 1. Un tableau simple, à une seule ligne d'en-tête.
const simple = tableau(["Année", "Déficit", "Dette"],
                       [["2026", "5,1 %", "112 %"], ["2027", "4,8 %", "113 %"]]);
rapport.simple = tableauEnCartes(simple);
rapport.etiquettes = etiquettes(simple);
rapport.marque = simple.getAttribute("data-cartes");
rapport.classe = simple.classList.contains("tableau-cartes");

// 2. Deuxième passage : rien de neuf, mais toujours vrai.
rapport.simple2 = tableauEnCartes(simple);
rapport.etiquettesApres = etiquettes(simple);

// 3. Deux lignes d'en-tête : on ne sait pas à quelle colonne appartient une
//    valeur, donc on ne touche à rien.
const double = tableau(["Année", "Déficit"], [["bis", "haut"]],
                       [["2026", "5,1 %"], ["2027", "4,8 %"]]);
rapport.doubleEntete = tableauEnCartes(double);
rapport.doubleEtiquettes = etiquettes(double).flat().filter(Boolean).length;

// 4. Une cellule qui fusionne deux colonnes : tout le tableau y renonce.
const fusion = tableau(["Année", "Déficit", "Dette"],
                       [[v("2026"), {valeur: "5,1 %", fusion: "colspan"}, v("112 %")]]);
rapport.fusion = tableauEnCartes(fusion);
rapport.fusionEtiquettes = etiquettes(fusion).flat().filter(Boolean).length;
rapport.fusionMarque = fusion.getAttribute("data-cartes");

// 5. Un tableau peut refuser la bascule, explicitement.
const refuse = tableau(["Année", "Déficit"], [["2026", "5,1 %"]]);
refuse.setAttribute("data-cartes", "non");
rapport.refus = tableauEnCartes(refuse);
rapport.refusEtiquettes = etiquettes(refuse).flat().filter(Boolean).length;

// 6. Une ligne qui commence par son titre (`<th scope="row">`) reste alignée :
//    les cellules de corps comptent comme les autres.
const titre = tableau(["Année", "Déficit", "Dette"],
                      [[{valeur: "2026", balise: "th"}, v("5,1 %"), v("112 %")]]);
rapport.titreRangee = tableauEnCartes(titre);
rapport.etiquettesTitre = etiquettes(titre);

// 7. Le tableau se répare tout seul : un gabarit qui remplace la cellule de
//    remplissage par de vraies valeurs redevient étiquetable.
const remis = tableau(["Année", "Déficit", "Dette"],
                      [[v("2026"), {valeur: "en cours", fusion: "colspan"}, v("112 %")]]);
rapport.avantReparation = tableauEnCartes(remis);
const celluleReparee = remis.querySelectorAll("tbody tr td")[1];
celluleReparee.removeAttribute("colspan");
celluleReparee.textContent = "5,1 %";
rapport.repare = tableauEnCartes(remis);
rapport.repareMarque = remis.getAttribute("data-cartes");
rapport.repareEtiquettes = etiquettes(remis);

// 8. Et à l'envers : un tableau déjà en cartes qui reçoit une cellule fusionnée
//    rend sa marque au lieu de rester à moitié en carte.
const perdu = tableau(["Année", "Déficit", "Dette"], [["2026", "5,1 %", "112 %"]]);
tableauEnCartes(perdu);
perdu.querySelectorAll("tbody tr td")[2].setAttribute("colspan", "2");
rapport.perdu = tableauEnCartes(perdu);
rapport.perduMarque = perdu.getAttribute("data-cartes");
rapport.perduClasse = perdu.classList.contains("tableau-cartes");

console.log(JSON.stringify(rapport));
"""


@unittest.skipIf(NODE is None, "Node.js n'est pas installé : contrôle d'exécution ignoré")
class TestTableauxEnCartes(unittest.TestCase):
    """Sous 640 px, une ligne de tableau devient une carte étiquetée."""

    @classmethod
    def setUpClass(cls):
        script = "\n".join(re.findall(r"<script>(.*?)</script>", HTML_PAGE, re.S))
        fragment = script[script.index(DEBUT):script.index(FIN)]
        with tempfile.TemporaryDirectory(prefix="cartes-tableaux-") as temporaire:
            chemin = Path(temporaire) / "essai.mjs"
            import_ = f'import {{ Document }} from "{DOM_PARTAGE.as_uri()}";\n'
            chemin.write_text(import_ + "const document = new Document();\n" + fragment
                              + PROGRAMME, encoding="utf-8")
            cls.retour = subprocess.run([NODE, str(chemin)], capture_output=True,
                                        text=True, timeout=120)
        cls.rapport = (json.loads(cls.retour.stdout.strip().splitlines()[-1])
                       if cls.retour.returncode == 0 else None)

    def test_le_script_tourne_sans_erreur(self):
        self.assertEqual(self.retour.returncode, 0, self.retour.stdout + self.retour.stderr)
        self.assertIsNotNone(self.rapport, self.retour.stdout + self.retour.stderr)

    def test_chaque_valeur_recoit_le_nom_de_sa_colonne(self):
        self.assertTrue(self.rapport["simple"])
        self.assertEqual(self.rapport["etiquettes"],
                         [["Année", "Déficit", "Dette"], ["Année", "Déficit", "Dette"]])
        self.assertEqual(self.rapport["marque"], "oui")
        self.assertTrue(self.rapport["classe"], "la classe porte les règles d'écran étroit")

    def test_le_second_passage_ne_change_rien(self):
        self.assertTrue(self.rapport["simple2"])
        self.assertEqual(self.rapport["etiquettesApres"], self.rapport["etiquettes"])

    def test_un_tableau_a_deux_en_tetes_garde_le_defilement(self):
        self.assertFalse(self.rapport["doubleEntete"])
        self.assertEqual(self.rapport["doubleEtiquettes"], 0)

    def test_une_cellule_fusionnee_fait_renoncer_tout_le_tableau(self):
        self.assertFalse(self.rapport["fusion"])
        self.assertEqual(self.rapport["fusionEtiquettes"], 0,
                         "tout ou rien : aucune cellule touchée")
        self.assertIsNone(self.rapport["fusionMarque"])

    def test_un_tableau_peut_refuser_la_bascule(self):
        self.assertFalse(self.rapport["refus"])
        self.assertEqual(self.rapport["refusEtiquettes"], 0)

    def test_une_ligne_qui_commence_par_son_titre_reste_alignee(self):
        self.assertTrue(self.rapport["titreRangee"])
        self.assertEqual(self.rapport["etiquettesTitre"], [["Année", "Déficit", "Dette"]])

    def test_un_tableau_repare_se_remet_en_cartes_tout_seul(self):
        """Le passage a lieu à chaque vague de rendu, pas une fois pour toutes."""
        self.assertFalse(self.rapport["avantReparation"])
        self.assertTrue(self.rapport["repare"])
        self.assertEqual(self.rapport["repareMarque"], "oui")
        self.assertEqual(self.rapport["repareEtiquettes"],
                         [["Année", "Déficit", "Dette"]])

    def test_un_tableau_devenu_incoherent_rend_sa_marque(self):
        self.assertFalse(self.rapport["perdu"])
        self.assertIsNone(self.rapport["perduMarque"],
                          "mieux vaut un tableau qui défile qu'une carte à moitié faite")
        self.assertFalse(self.rapport["perduClasse"])
