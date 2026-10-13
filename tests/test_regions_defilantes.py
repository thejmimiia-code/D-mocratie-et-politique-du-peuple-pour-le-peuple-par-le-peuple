"""Le nom d'une région défilante suit la taille de l'écran, exécuté pour de vrai.

Au-dessus de 640 px, un tableau large défile : sa région s'appelle « … — faites
défiler horizontalement » et on l'atteint au clavier, ce qui est exactement ce
qu'il faut. Sous 640 px, le même tableau devient une pile de cartes ; il ne
défile plus horizontalement. Deux choses deviennent alors fausses :

* la phrase promet un geste qui n'existe pas — une personne qui suit l'annonce
  du lecteur d'écran cherche un défilement absent ;
* `tabindex="0"` ajoute un arrêt de tabulation qui ne mène nulle part : au
  doigt, le clavier n'existe pas, mais sur une tablette avec clavier, oui.

Ces contrôles exécutent le JavaScript sur le DOM minimal
(`tests/dom_minimal.mjs`) avec une fenêtre simulée : large, étroite, puis
élargie — et un pli de fenêtre, pour vérifier que le renommage ne dépend pas
d'un rendu. Le tableau **fusionné**, lui, garde le défilement à toutes les
tailles : son étiquette et son arrêt doivent rester.

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

DEBUT = "function tableauDejaDefilant("   # la même tranche que le défilement
FIN = "function marquerSommaire("

SUFFIXE_DEFILEMENT = " — faites défiler horizontalement"
SUFFIXE_CARTES = " — présenté en cartes, une ligne à la fois"

PROGRAMME = r"""
// ── Deux tableaux : un étiquetable, un qui ne l'est pas (colonne fusionnée) ──
function tableau(entetes, cellules, fusion){
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const trh = document.createElement("tr");
  for (const titre of entetes){
    const th = document.createElement("th");
    th.textContent = titre;
    trh.appendChild(th);
  }
  thead.appendChild(trh);
  table.appendChild(thead);
  const tbody = document.createElement("tbody");
  const tr = document.createElement("tr");
  for (const valeur of cellules){
    const td = document.createElement("td");
    td.textContent = valeur;
    if (fusion) td.setAttribute("colspan", "2");
    tr.appendChild(td);
  }
  tbody.appendChild(tr);
  table.appendChild(tbody);
  return table;
}

const document = new Document();
const section = document.createElement("section");
document.body.appendChild(section);

const simple = tableau(["Année", "Déficit"], ["2026", "5,1 %"]);
simple.setAttribute("data-legende", "Comptes nationaux simulés");
section.appendChild(simple);

const fusion = tableau(["Année", "Déficit", "Dette"], ["2026", "5,1 %", "112 %"], true);
section.appendChild(fusion);          // pas de légende : le nom générique s'applique

const fenetre = { };
globalThis.window = fenetre;          // écran large : pas de matchMedia

const etat = () => document.querySelectorAll(".tableau-defilant").map(region => ({
  legende: region.getAttribute("data-legende"),
  nom: region.getAttribute("aria-label"),
  tabindex: region.getAttribute("tabindex"),
  role: region.getAttribute("role"),
}));
const parLegende = (releve) => Object.fromEntries(releve.map((r) => [r.legende, r]));

const poses = rendreTableauxDefilants();
const large = etat();

// ── Un téléphone : le palier de 640 px est atteint ──────────────────────────
fenetre.matchMedia = (requete) => ({ matches: requete === "screen and (max-width:640px)" });
nommerRegionsTableaux();
const etroit = etat();

// ── Le rendu repasse : le nom ne doit pas s'empiler ─────────────────────────
const posesEtroit = rendreTableauxDefilants();
const etroitApresRendu = etat();

// ── La fenêtre s'élargit : la phrase de défilement revient ──────────────────
fenetre.matchMedia = () => ({ matches: false });
nommerRegionsTableaux();
const elargi = etat();

// ── Le pli de la fenêtre, sans rendu : l'écouteur est-il posé et efficace ? ──
let ecouteur = null;
const fenetreAvecEcoute = {
  addEventListener: (type, manipulation) => { if (type === "resize") ecouteur = manipulation; },
  matchMedia: () => ({ matches: true }),
};
globalThis.window = fenetreAvecEcoute;
const suivi = suivrePliDeLEcran();
if (ecouteur){ ecouteur(); ecouteur(); }        // deux plis coup sur coup
await new Promise((suite) => setTimeout(suite, 250));   // le temps du repli
const apresPli = etat();

// ── Une fenêtre sans écouteur : le garde-fou répond non, et la vague suivante
//    (ici appelée à la main) suffit à remettre les noms d'aplomb ─────────────
globalThis.window = {};
const suiviSansEcouteur = suivrePliDeLEcran();
nommerRegionsTableaux();
const sansEcouteur = etat();

console.log(JSON.stringify({
  poses, posesEtroit, suivi, suiviSansEcouteur,
  large: parLegende(large),
  etroit: parLegende(etroit),
  etroitApresRendu: parLegende(etroitApresRendu),
  elargi: parLegende(elargi),
  apresPli: parLegende(apresPli),
  sansEcouteur: parLegende(sansEcouteur),
  nombreDeRegions: large.length,
}));
"""


@unittest.skipIf(NODE is None, "Node.js n'est pas installé : contrôle d'exécution ignoré")
class TestRegionsDefilantes(unittest.TestCase):
    """Le nom dit ce que la région fait, à la taille où on la lit."""

    @classmethod
    def setUpClass(cls):
        script = "\n".join(re.findall(r"<script>(.*?)</script>", HTML_PAGE, re.S))
        cls.script = script
        cls.fragment = script[script.index(DEBUT):script.index(FIN)]
        with tempfile.TemporaryDirectory(prefix="regions-defilantes-") as temporaire:
            chemin = Path(temporaire) / "essai.mjs"
            import_ = f'import {{ Document }} from "{DOM_PARTAGE.as_uri()}";\n'
            chemin.write_text(import_ + cls.fragment + PROGRAMME, encoding="utf-8")
            cls.retour = subprocess.run([NODE, str(chemin)], capture_output=True,
                                        text=True, timeout=120)
        cls.rapport = (json.loads(cls.retour.stdout.strip().splitlines()[-1])
                       if cls.retour.returncode == 0 else None)

    def region(self, releve: str, legende: str) -> dict:
        return self.rapport[releve][legende]

    def test_le_script_tourne_sans_erreur(self):
        self.assertEqual(self.retour.returncode, 0, self.retour.stdout + self.retour.stderr)
        self.assertIsNotNone(self.rapport, self.retour.stdout + self.retour.stderr)

    def test_les_deux_tableaux_ont_leur_region(self):
        self.assertEqual(self.rapport["nombreDeRegions"], 2)
        self.assertEqual(self.rapport["poses"], 2)
        self.assertEqual(self.rapport["posesEtroit"], 0,
                         "la seconde vague ne réenveloppe rien")

    def test_un_ecran_large_nomme_le_defilement_et_garde_l_arret(self):
        etat = self.region("large", "Comptes nationaux simulés")
        self.assertEqual(etat["role"], "region")
        self.assertEqual(etat["tabindex"], "0")
        self.assertTrue(etat["nom"].endswith(SUFFIXE_DEFILEMENT), etat["nom"])

    def test_sur_un_telephone_la_phrase_dit_les_cartes(self):
        etat = self.region("etroit", "Comptes nationaux simulés")
        self.assertTrue(etat["nom"].endswith(SUFFIXE_CARTES), etat["nom"])
        self.assertNotIn("faites défiler", etat["nom"],
                         "la phrase ne doit pas promettre un défilement absent")

    def test_sur_un_telephone_l_arret_de_tabulation_disparait(self):
        """Un arrêt de tabulation qui ne mène nulle part est un piège, pas une aide."""
        etat = self.region("etroit", "Comptes nationaux simulés")
        self.assertIsNone(etat["tabindex"])
        self.assertEqual(etat["role"], "region",
                         "la région reste annoncée : elle est nommée et exploitable")

    def test_un_tableau_fusionne_garde_son_etiquette_et_son_arret(self):
        """Ses cellules ne s'étiquettent pas : il défile, même dans 360 px."""
        large = self.region("large", "Tableau de résultats")
        etroit = self.region("etroit", "Tableau de résultats")
        self.assertTrue(large["nom"].endswith(SUFFIXE_DEFILEMENT))
        self.assertEqual(etroit["nom"], large["nom"])
        self.assertEqual(etroit["tabindex"], "0")

    def test_la_legende_du_tableau_devient_le_nom_de_la_region(self):
        self.assertEqual(self.region("large", "Comptes nationaux simulés")["legende"],
                         "Comptes nationaux simulés")
        self.assertTrue(self.region("large", "Tableau de résultats")["nom"].startswith(
            "Tableau de résultats —"))

    def test_le_nom_ne_s_empile_pas_d_une_vague_a_l_autre(self):
        """Le nom se réécrit à partir de la légende rangée : jamais deux suffixes."""
        for legende in ("Comptes nationaux simulés", "Tableau de résultats"):
            with self.subTest(legende=legende):
                self.assertEqual(self.region("etroitApresRendu", legende)["nom"],
                                 self.region("etroit", legende)["nom"])
        nom = self.region("etroit", "Comptes nationaux simulés")["nom"]
        self.assertEqual(nom.count("cartes"), 1, nom)
        self.assertEqual(nom.count("défiler"), 0, nom)
        # Le tableau fusionné, lui, garde la phrase du défilement — et une seule.
        fusion = self.region("etroit", "Tableau de résultats")["nom"]
        self.assertEqual(fusion.count("défiler"), 1, fusion)
        self.assertEqual(fusion.count("cartes"), 0, fusion)

    def test_elargir_la_fenetre_restaure_la_phrase_de_defilement(self):
        for legende in ("Comptes nationaux simulés", "Tableau de résultats"):
            with self.subTest(legende=legende):
                self.assertEqual(self.region("elargi", legende)["nom"],
                                 self.region("large", legende)["nom"])
                self.assertEqual(self.region("elargi", legende)["tabindex"], "0")

    def test_un_pli_de_fenetre_renomme_sans_attendre_un_rendu(self):
        """Le pli n'est pas un rendu : sans cela, l'étiquette restait fausse."""
        self.assertTrue(self.rapport["suivi"], "l'écouteur du pli n'a pas été posé")
        self.assertEqual(self.region("apresPli", "Comptes nationaux simulés")["nom"],
                         self.region("etroit", "Comptes nationaux simulés")["nom"])
        self.assertIsNone(self.region("apresPli", "Comptes nationaux simulés")["tabindex"])

    def test_une_fenetre_sans_ecouteur_ne_casse_rien_et_le_dit(self):
        self.assertFalse(self.rapport["suiviSansEcouteur"])
        self.assertEqual(self.region("sansEcouteur", "Comptes nationaux simulés")["nom"],
                         self.region("large", "Comptes nationaux simulés")["nom"])

    def test_la_requete_du_javascript_est_celle_du_css(self):
        """Deux façons de poser la même question finiraient par diverger.

        Le CSS bascule en cartes dans `screen and (max-width:640px)` ; si le
        JavaScript interrogeait `(max-width:640px)` tout court, les deux
        pourraient ne plus répondre la même chose (impression, media types) et
        le nom se remettrait à mentir sans qu'aucune autre porte ne le voie.
        """
        self.assertIn("window.matchMedia('screen and (max-width:640px)')", self.script)
        # La requête est dans la feuille de style, pas dans le script : c'est le
        # CSS qui bascule en cartes, le JavaScript ne fait que poser la question.
        self.assertIn("@media screen and (max-width:640px)", HTML_PAGE)

    def test_le_nom_de_region_vient_d_une_seule_phrase(self):
        """La légende de repli et les deux suffixes s'écrivent une seule fois."""
        for motif in ("Tableau de résultats", "— faites défiler horizontalement",
                      "— présenté en cartes"):
            with self.subTest(motif=motif):
                self.assertLessEqual(
                    self.script.count(motif), 2,
                    f"« {motif} » recopié : le nom se réécrit à partir de la légende rangée")


if __name__ == "__main__":
    unittest.main()
