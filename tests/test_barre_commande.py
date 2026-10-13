"""La barre de commande, exécutée : sa hauteur, et ce qu'elle annonce.

Sous 901 px, il n'y a de place que pour **une** barre collante : le sommaire.
La veille n'y perd pas la parole — son verdict tient dans une pastille, qui
vient de la même source que le ruban.

Ce que ces contrôles exécutent pour de vrai :

* `mesurerCollant` écrit la hauteur **réelle** de la barre dans `--collant` —
  c'est ce qui empêche les ancres d'atterrir sous la barre, et le ruban de
  veille de se coller à la mauvaise distance ;
* une barre qui n'a pas de hauteur mesurable (absente, masquée, doublure sans
  `getBoundingClientRect`) n'écrase rien : la valeur de repli du CSS tient ;
* `surveillerCollant` observe bien la barre, et un changement de hauteur —
  ouverture du sommaire, rotation — rappelle la mesure ;
* `peindreVeilleCourte` dit le niveau en toutes lettres (la couleur ne porte
  rien seule), et l'efface quand le diagnostic disparaît au lieu de laisser un
  verdict périmé.

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

# Les morceaux sont pris dans la page, jamais recopiés : c'est le code livré
# qui s'exécute. Quatre extraits suffisent — la barre et sa mesure, le niveau
# et ses mots, la pastille, et la bascule du sommaire qui rappelle la mesure.
MORCEAUX = (
    ("function mesurerCollant(", "function pointerGrossier("),
    ("function basculerSommaire(", "function mesurerCollant("),
    ("function classeNiveau(", "function renderConsole("),
    ("const LIBELLES_NIVEAUX", "};"),
)

PROGRAMME = r"""
const nav = document.createElement("nav");
nav.setAttribute("id", "sommaire");
nav.className = "sommaire";
const pastille = document.createElement("button");
pastille.setAttribute("id", "sommaire-veille");
pastille.setAttribute("hidden", "");
nav.appendChild(pastille);
document.body.appendChild(nav);

const racine = document.documentElement;
const lire = (nom) => racine.style.getPropertyValue(nom);
const rapport = {};

// 1. Une barre sans hauteur mesurable n'écrase pas le repli du CSS.
rapport.repli = lire("--collant");
rapport.mesureSansRect = mesurerCollant();
rapport.repliApres = lire("--collant");

// 2. La barre annonce sa hauteur : 58 px mesurés sur un téléphone.
let hauteur = 58;
nav.getBoundingClientRect = () => ({height: hauteur});
rapport.mesure = mesurerCollant();
rapport.collant = lire("--collant");

// 3. L'observateur suit : le sommaire s'ouvre, la barre grandit, la mesure suit.
globalThis.__observateur = null;
globalThis.ResizeObserver = class {
  constructor(rappel) { this.rappel = rappel; globalThis.__observateur = this; }
  observe(cible) { this.cible = cible; }
};
rapport.surveille = surveillerCollant();
rapport.observeLaBarre = !!(globalThis.__observateur && globalThis.__observateur.cible === nav);
hauteur = 176;
globalThis.__observateur.rappel();
rapport.collantApresOuverture = lire("--collant");

// 4. Une hauteur nulle laisse la dernière mesure en place : mieux vaut une
//    valeur approchée qu'un zéro qui collerait tout au bord.
hauteur = 0;
rapport.mesureNulle = mesurerCollant();
rapport.collantEncore = lire("--collant");

// 5. La pastille : cachée tant qu'aucun diagnostic n'est connu.
rapport.pastilleAuDepart = {cachee: pastille.hidden, attribut: pastille.hasAttribute("hidden")};

// 6. Puis peinte, avec le niveau écrit en toutes lettres.
rapport.peinture = peindreVeilleCourte({niveau_global: "vigilance", verdict: {nombre_alertes: 3}});
rapport.pastille = {
  cachee: pastille.hidden,
  attribut: pastille.hasAttribute("hidden"),
  texte: pastille.textContent,
  classe: pastille.classList.contains("sommaire-veille"),
  niveau: pastille.classList.contains("niveau-vigilance"),
  titre: pastille.title,
};

// 7. Le diagnostic disparu efface la pastille : pas de verdict périmé.
rapport.peintureSans = peindreVeilleCourte(null);
rapport.pastilleApres = {cachee: pastille.hidden, attribut: pastille.hasAttribute("hidden")};

// 8. Hors-sol : le mot change, et la classe avec lui.
peindreVeilleCourte({niveau_global: "hors_sol", verdict: {nombre_alertes: 12}});
rapport.horsSol = {texte: pastille.textContent, niveau: pastille.classList.contains("niveau-hors_sol")};

// 9. Un diagnostic sans verdict ne fait pas jeter la pastille.
rapport.sansVerdict = peindreVeilleCourte({niveau_global: "favorable"});
rapport.sansVerdictTexte = pastille.textContent;

// 10. Et là où la pastille n'existe pas, la fonction le dit sans jeter.
const sauvegarde = document.getElementById;
document.getElementById = () => null;
rapport.pastilleAbsente = peindreVeilleCourte({niveau_global: "vigilance", verdict: {}});
rapport.collantSansBarre = mesurerCollant();
document.getElementById = sauvegarde;

console.log(JSON.stringify(rapport));
"""


@unittest.skipIf(NODE is None, "Node.js n'est pas installé : contrôle d'exécution ignoré")
class TestLaBarreDeCommande(unittest.TestCase):
    """La barre dit sa hauteur, et la veille y garde la parole."""

    @classmethod
    def setUpClass(cls):
        script = "\n".join(re.findall(r"<script>(.*?)</script>", HTML_PAGE, re.S))
        morceaux = []
        for debut, fin in MORCEAUX:
            depart = script.index(debut)
            arrivee = script.index(fin, depart)
            if debut.startswith("const "):
                arrivee = script.index(fin, depart) + len(fin)
            morceaux.append(script[depart:arrivee])
        fragment = "\n".join(morceaux)
        with tempfile.TemporaryDirectory(prefix="barre-commande-") as temporaire:
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

    def test_une_barre_sans_hauteur_mesurable_laisse_le_repli_du_css(self):
        self.assertEqual(self.rapport["repli"], "", "aucune valeur n'est écrite d'avance")
        self.assertEqual(self.rapport["mesureSansRect"], 0)
        self.assertEqual(self.rapport["repliApres"], "",
                         "sans mesure, la valeur de repli du CSS reste la seule")

    def test_la_hauteur_mesuree_est_ecrite_dans_la_variable(self):
        self.assertEqual(self.rapport["mesure"], 58)
        self.assertEqual(self.rapport["collant"], "58px")

    def test_l_observateur_suit_les_changements_de_hauteur(self):
        self.assertTrue(self.rapport["surveille"])
        self.assertTrue(self.rapport["observeLaBarre"], "l'observateur suit la barre, pas le corps")
        self.assertEqual(self.rapport["collantApresOuverture"], "176px",
                         "le sommaire ouvert est plus haut : la mesure suit")

    def test_une_hauteur_nulle_ne_colle_rien_au_bord(self):
        self.assertEqual(self.rapport["mesureNulle"], 0)
        self.assertEqual(self.rapport["collantEncore"], "176px",
                         "une barre masquée ne remet pas la variable à zéro")

    def test_la_pastille_dort_tant_qu_aucun_diagnostic_n_est_connu(self):
        self.assertTrue(self.rapport["pastilleAuDepart"]["cachee"])
        self.assertTrue(self.rapport["pastilleAuDepart"]["attribut"])

    def test_la_pastille_dit_le_niveau_en_toutes_lettres(self):
        self.assertTrue(self.rapport["peinture"])
        pastille = self.rapport["pastille"]
        self.assertFalse(pastille["cachee"])
        self.assertFalse(pastille["attribut"], "l'attribut part avec le réveil")
        self.assertEqual(pastille["texte"], "vigilance · 3 alerte(s)")
        self.assertTrue(pastille["classe"])
        self.assertTrue(pastille["niveau"])
        self.assertIn("Veille permanente", pastille["titre"])

    def test_le_diagnostic_disparu_efface_la_pastille(self):
        self.assertFalse(self.rapport["peintureSans"])
        self.assertTrue(self.rapport["pastilleApres"]["cachee"])
        self.assertTrue(self.rapport["pastilleApres"]["attribut"])

    def test_le_mot_du_niveau_suit_le_niveau(self):
        self.assertEqual(self.rapport["horsSol"]["texte"], "hors-sol · 12 alerte(s)")
        self.assertTrue(self.rapport["horsSol"]["niveau"])
        self.assertEqual(self.rapport["sansVerdictTexte"], "favorable · 0 alerte(s)",
                         "un verdict absent se lit zéro, il ne fait pas jeter")

    def test_sans_pastille_dans_la_page_rien_ne_jette(self):
        self.assertFalse(self.rapport["pastilleAbsente"])
        self.assertEqual(self.rapport["collantSansBarre"], 0)
