"""La page se pèse devant le visiteur — et voici comment on l'éprouve.

Le poids de la page est déjà **mesuré et plafonné hors ligne** : `outils/
budgets_fluidite.py` tient les octets compressés de la page et de chaque route,
`outils/poids_de_la_page.py` tient ce que l'appareil décompresse et analyse, et
la CI refuse un dépassement à chaque poussée. Mais ces plafonds mesurent une
**moyenne de dépôt**, jamais la visite de quelqu'un.

D'où le bloc n° 6 de l'audit : la page lit ce que le navigateur publie pour
**cette** visite-là — `performance.getEntriesByType('navigation')` — et l'écrit
tels quels : ce qui a traversé le réseau (compressé), ce que l'appareil a
décompressé et analysé, combien de ressources ont été appelées et **chez qui**.
C'est la seule mesure de poids qu'un visiteur peut vérifier lui-même, et elle
rend publique la promesse d'autonomie du dépôt : la page n'appelle personne
d'autre qu'elle-même.

Ce fichier tient cinq promesses :

1. **le bloc existe et il est à sa place** — sixième de l'audit, après les
   dynamiques croisées, avant la bannière ;
2. **aucun chiffre n'est écrit d'avance** — les nombres sont lus, jamais
   recopiés : un « 128 ko » en dur serait un chiffre qui ne parle pas de la
   visite du lecteur ;
3. **le silence est préféré à l'estimation** — API absente, mesure non publiée,
   `transferSize` à zéro : le bloc l'écrit au lieu d'annoncer un zéro ;
4. **rien ne casse l'audit** — la pesée est sous `try/catch`, appelée après le
   `try` de `chargerAudit`, et une doublure qui jette la fait rendre son texte
   de repli sans emporter la page ;
5. **ce qui est écrit est exécuté** — les fonctions sont extraites de la page
   (jamais recopiées) et tournées dans Node sur un DOM minimal, avec quatre
   doublures de navigateur : une visite normale, une visite servie du cache, une
   visite où un autre domaine est appelé, et un navigateur qui refuse de mesurer.

Ce test saute proprement si Node.js n'est pas installé.
"""

from __future__ import annotations

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

#: Le fragment éprouvé est **celui de la page** : si quelqu'un réécrit la
#: pesée, c'est la nouvelle version qui est exécutée ici.
DEBUT = "function origineDe("
FIN = "async function chargerAudit(){"

PROGRAMME = r"""

const document = new Document();
const zone = document.createElement("div");
zone.setAttribute("id", "audit-pesee");
document.body.appendChild(zone);

// L'adresse de la page : c'est elle qui dit ce qui est « chez elle ».
const adresse = "https://d-mocratie-et-politique-du-peuple-p.example/";

/* Quatre navigateurs, quatre vérités différentes — le bloc doit dire les quatre
   sans en inventer une cinquième. */
const doublures = {
  visite: {
    getEntriesByType: function (type){
      if (type === "navigation") return [{
        name: adresse, transferSize: 131072, encodedBodySize: 131072,
        decodedBodySize: 524288, responseStart: 210, domContentLoadedEventEnd: 900,
      }];
      return [{ name: adresse + "_vercel/insights/script.js" }];
    },
  },
  cache: {
    getEntriesByType: function (type){
      if (type === "navigation") return [{
        name: adresse, transferSize: 0, encodedBodySize: 0,
        decodedBodySize: 524288, responseStart: 0, domContentLoadedEventEnd: 0,
      }];
      return [];
    },
  },
  tiers: {
    getEntriesByType: function (type){
      if (type === "navigation") return [{
        name: adresse, transferSize: 131072, decodedBodySize: 524288,
        responseStart: 50, domContentLoadedEventEnd: 400,
      }];
      return [{ name: adresse + "app.js" },
              { name: "https://cdn.exemple.test/police.woff2" }];
    },
  },
  muet: {
    getEntriesByType: function (){ throw new Error("mesure interdite"); },
  },
  absent: {},
};

const rapports = {};
Object.keys(doublures).forEach(function (nom){
  performance = doublures[nom];
  try {
    const html = auditPeseeHtml();
    const pose = peserLaVisite();
    rapports[nom] = { html: html, pose: pose, zone: zone.innerHTML,
                      memeChose: zone.innerHTML === html };
  } catch (erreur) {
    rapports[nom] = { erreur: String((erreur && erreur.message) || erreur) };
  }
});
console.log(JSON.stringify(rapports));
"""


def _fonction(nom: str, script: str) -> str:
    """Le texte d'une fonction de la page, repérée par son nom."""
    debut = script.index(f"function {nom}(")
    fin = script.index("\n}\n", debut) + 3
    return script[debut:fin]


class TestLeBlocDePeseeDansLaPage(unittest.TestCase):
    """Ce qui se vérifie sans exécuter une ligne de JavaScript."""

    @classmethod
    def setUpClass(cls):
        cls.page = HTML_PAGE
        cls.script = "\n".join(re.findall(r"<script>(.*?)</script>", HTML_PAGE, re.S))
        cls.debut = cls.script.index(DEBUT)
        cls.fragment = cls.script[cls.debut:cls.script.index(FIN, cls.debut)]

    def test_les_blocs_de_l_audit_sont_numerotes_sans_trou(self):
        """La numérotation de 1 à N, sans saut ni doublon.

        Ce contrôle comptait les blocs (« six blocs numérotés ») : il vieillissait
        à chaque bloc ajouté — c'est arrivé au septième, le 15 octobre 2026, et il
        a fallu le réécrire. Ce qu'il doit tenir n'est pas un nombre, c'est une
        **suite** : les blocs se suivent, et celui de la pesée est là.
        """
        section = self.page[self.page.index('id="section-audit"'):]
        section = section[:section.index("</section>")]
        ids = re.findall(r'<details id="audit-([a-z]+)-details"', section)
        summaries = re.findall(r"<summary>(\d+)\.", section)
        self.assertEqual(summaries, [str(rang) for rang in range(1, len(ids) + 1)],
                         f"la numérotation de l'audit saute un rang ou se répète ({ids})")
        self.assertGreaterEqual(len(ids), 6, "l'audit a perdu des blocs en route")
        self.assertIn("pesee", ids)
        self.assertIn('id="audit-pesee"', section)
        self.assertIn('<div class="corps" id="audit-pesee">', section)

    def test_le_bloc_vient_apres_les_dynamiques_et_avant_la_banniere(self):
        """Un bloc de mesure se lit après les méthodes, pas au milieu d'elles."""
        section = self.page[self.page.index('id="section-audit"'):]
        section = section[:section.index("</section>")]
        self.assertLess(section.index('id="audit-methodes-details"'),
                        section.index('id="audit-pesee-details"'))
        self.assertLess(section.index('id="audit-pesee-details"'),
                        section.index("Bannière MRSC"))

    def test_le_bloc_est_annonce_dans_l_en_tete_de_l_audit(self):
        """Ce que l'audit contient doit être annoncé là où il se présente."""
        self.assertIn("tel que votre navigateur le mesure", self.page)

    def test_aucun_chiffre_de_poids_n_est_ecrit_d_avance(self):
        """Le défaut qu'on refuse : un poids en dur qui ne parle pas de la visite.

        Le bloc ne doit porter **aucune** grandeur en kilo-octets écrite à la
        main : tout ce qui s'affiche vient de `performance`. Un chiffre recopié
        dirait le poids d'une autre visite, et vieillirait sans prévenir.
        """
        self.assertNotRegex(self.fragment, r"\d+\s*ko",
                            "un poids est écrit en dur dans la pesée")
        self.assertNotRegex(self.fragment, r"\b\d{2,4}\s*(Mo|Ko|ko|Mo)\b")

    def test_les_quatre_grandeurs_sont_lues_dans_le_navigateur(self):
        for grandeur in ("transferSize", "encodedBodySize", "decodedBodySize",
                         "getEntriesByType"):
            with self.subTest(grandeur=grandeur):
                self.assertIn(grandeur, self.fragment)

    def test_la_pesee_ne_depend_d_aucune_route_et_ne_retarde_rien(self):
        """On ne bloque pas le démarrage pour une mesure d'audit."""
        appel = "  peserLaVisite();"
        self.assertEqual(self.script.count(appel), 1,
                         "la pesée doit être appelée une fois, et une seule")
        debut_audit = self.script.index("async function chargerAudit(){")
        fin_audit = self.script.index("\nasync function ", debut_audit + 1)
        corps = self.script[debut_audit:fin_audit]
        self.assertIn("peserLaVisite();", corps)
        self.assertNotIn("await peserLaVisite", corps)
        # Après le `catch` : une route muette ne doit pas emporter la pesée.
        self.assertLess(corps.index("} catch (erreur)"), corps.index("peserLaVisite();"))

    def test_le_silence_est_prefere_a_l_estimation(self):
        """Quand le navigateur ne publie rien, le bloc ne publie rien non plus."""
        self.assertIn("ne publie pas la mesure", self.fragment)
        self.assertIn("préfère ne rien afficher plutôt qu’un chiffre estimé", self.fragment)

    def test_le_cache_et_l_origine_sont_dits(self):
        self.assertIn("cache de votre appareil", self.fragment)
        self.assertIn("n’appelle aucun autre domaine", self.fragment)
        self.assertIn("à justifier", self.fragment)

    def test_le_bloc_ne_cree_aucun_style_neuf(self):
        """Il réutilise le balisage et les classes de l'audit — rien de neuf à charger."""
        for classe in ('class="corps"', 'id="audit-pesee"'):
            with self.subTest(classe=classe, ou="balisage"):
                self.assertIn(classe, self.page)
        for classe in ('class="source-note"', 'class="chiffre"', "<table>"):
            with self.subTest(classe=classe, ou="pesée"):
                self.assertIn(classe, self.fragment)


@unittest.skipIf(NODE is None, "Node.js n'est pas installé : contrôle d'exécution ignoré")
class TestLaPeseeExecutee(unittest.TestCase):
    """Les fonctions de la page, tournées pour de vrai sur un DOM minimal."""

    @classmethod
    def setUpClass(cls):
        script = "\n".join(re.findall(r"<script>(.*?)</script>", HTML_PAGE, re.S))
        fragment = script[script.index(DEBUT):script.index(FIN, script.index(DEBUT))]
        import_ = f'import {{ Document }} from "{DOM_PARTAGE.as_uri()}";\n'
        cls.source = import_ + _fonction("fmt", script) + "\n" + fragment + PROGRAMME
        with tempfile.TemporaryDirectory(prefix="pesee-visite-") as temporaire:
            chemin = Path(temporaire) / "essai.mjs"
            chemin.write_text(cls.source, encoding="utf-8")
            cls.retour = subprocess.run([NODE, str(chemin)], capture_output=True,
                                        text=True, timeout=120)
        cls.rapports = (json.loads(cls.retour.stdout.strip().splitlines()[-1])
                        if cls.retour.returncode == 0 else None)

    def test_le_script_tourne_sans_erreur(self):
        self.assertEqual(self.retour.returncode, 0,
                         self.retour.stdout + self.retour.stderr)
        self.assertIsNotNone(self.rapports, self.retour.stdout + self.retour.stderr)

    def test_aucun_rapport_ne_porte_d_erreur(self):
        """Les cinq navigateurs passent — y compris celui qui refuse de mesurer."""
        for nom, rapport in self.rapports.items():
            with self.subTest(navigateur=nom):
                self.assertNotIn("erreur", rapport,
                                 f"la pesée jette sur un navigateur « {nom} » : "
                                 f"{rapport.get('erreur')}")

    def test_la_zone_recoit_la_pesee(self):
        self.assertTrue(self.rapports["visite"]["pose"])
        self.assertTrue(self.rapports["visite"]["memeChose"],
                        "la zone ne porte pas ce que la fonction a rendu")

    def test_une_visite_normale_dit_les_quatre_chiffres(self):
        """128 ko transférés, 512 ko analysés, 1 ressource, toutes chez elle."""
        html = self.rapports["visite"]["html"]
        self.assertIn("128,0 ko", html)          # 131 072 o compressés
        self.assertIn("512,0 ko", html)          # 524 288 o décompressés
        self.assertIn("toutes chez elle", html)
        self.assertIn("0,21 s", html)            # premier octet
        self.assertIn("0,90 s", html)            # page rendue
        self.assertIn("1", html)

    def test_un_navigateur_muet_ne_recoit_aucun_chiffre(self):
        """Pas d'API, pas de mesure : le texte de repli, et pas un nombre."""
        html = self.rapports["absent"]["html"]
        self.assertIn("ne publie pas la mesure", html)
        self.assertNotIn("ko", html)
        self.assertNotIn("non publié", html)

    def test_une_visite_en_cache_ne_se_dit_pas_gratuite(self):
        """Zéro transféré n'est pas « la page ne coûte rien » : c'est le cache."""
        html = self.rapports["cache"]["html"]
        self.assertIn("aucun octet transféré", html)
        self.assertIn("cache de votre appareil", html)
        self.assertIn("512,0 ko", html, "la taille analysée reste publiée")
        self.assertNotIn("0,0 ko", html)

    def test_un_appel_hors_de_l_adresse_est_signale(self):
        """Si un CDN entre un jour dans la page, le visiteur le lit ici."""
        html = self.rapports["tiers"]["html"]
        self.assertIn("hors de son adresse", html)
        self.assertIn("à justifier", html)
        self.assertNotIn("toutes chez elle", html)

    def test_le_poids_transfere_dit_ce_qu_il_comprend(self):
        """Le nombre doit dire ce qu'il mesure, sans quoi il se compare mal.

        `transferSize` compte **tout** l'échange (en-têtes compris) ; le plafond du
        dépôt mesure un corps de document en gzip -6. Confondre les deux ferait
        croire à un dépassement qui n'existe pas — ou l'inverse.
        """
        for nom, rapport in self.rapports.items():
            if "html" not in rapport or "transférés" not in rapport["html"]:
                continue
            with self.subTest(navigateur=nom):
                self.assertIn("en-têtes compris", rapport["html"],
                              "le poids transféré ne dit pas si les en-têtes sont comptés")

    def test_aucune_cellule_nowrap_ne_porte_une_phrase(self):
        """Le défaut attrapé en relisant la greffe du 15 octobre 2026.

        `.audit td.chiffre` interdit le retour à la ligne (`white-space:nowrap`) :
        une phrase dans une telle cellule déborde du cadre au lieu de se replier,
        et le lecteur d'un téléphone lit une phrase coupée. Les cellules alignées
        sur les chiffres ne portent donc que **des nombres et des unités** ; le
        texte long va dans une cellule ordinaire, qui se replie.
        """
        for nom, rapport in self.rapports.items():
            if "html" not in rapport:
                continue
            for contenu in re.findall(r'<td class="chiffre">(.*?)</td>', rapport["html"], re.S):
                with self.subTest(navigateur=nom, contenu=contenu[:40]):
                    self.assertLessEqual(len(contenu), 30,
                                         "une cellule non repliable porte une phrase : "
                                         "elle sera coupée sur un téléphone")

    def test_une_mesure_qui_jette_ne_casse_pas_l_audit(self):
        """`getEntriesByType` qui lève : repli, jamais de trace d'erreur."""
        rapport = self.rapports["muet"]
        self.assertNotIn("erreur", rapport)
        self.assertIn("ne publie pas la mesure", rapport["html"])


if __name__ == "__main__":
    unittest.main()
