"""
tests/test_veille_publiee.py — la veille doit se lire, et ne pas crier pour rien.

La veille en ligne existait depuis la passe « indexation » et personne ne la
lisait : son verdict partait dans le *résumé d'étape*, c'est-à-dire dans un
journal de machine qu'il faut télécharger. Le 14 octobre 2026, la copie de
secours (Render) est tombée en **502** — toutes ses adresses, y compris la
sonde de disponibilité — et personne ne l'a su avant qu'un visiteur le signale.

Ce fichier tient les deux promesses qui manquaient :

1. **le verdict est publié** — un commentaire tenu à jour sur une page du dépôt,
   créée au premier passage, lisible par n'importe qui sans rien installer ;
2. **deux poids, deux mesures** — l'adresse canonique (Vercel) est celle qu'on
   partage : son échec fait rougir la veille. La copie de secours peut être
   endormie, suspendue ou absente sans que le dépôt soit en faute : son échec
   est **publié**, pas sanctionné. Une veille rouge toutes les semaines pour un
   service d'appoint cesse d'être lue, et une veille qu'on ne lit plus ne sert à
   rien.

Et la troisième, qui rend la réparation possible sans tableau de bord : un
**crochet de déploiement** optionnel. Tant qu'aucun crochet n'est configuré,
l'étape le dit et s'arrête proprement — elle ne fait pas rougir une fusion pour
un secret qui n'existe pas.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from simulateur import surface_publique as surface  # noqa: E402

VEILLE = RACINE / ".github" / "workflows" / "veille-en-ligne.yml"
CROCHET = RACINE / ".github" / "workflows" / "deploy-secours.yml"
HEBERGEMENT = RACINE / "docs" / "HEBERGEMENT.md"


class TestLaVeillePublieSonVerdict(unittest.TestCase):
    """Le rapport doit exister hors d'un journal de machine."""

    @classmethod
    def setUpClass(cls):
        cls.texte = VEILLE.read_text(encoding="utf-8")

    def test_la_veille_se_declenche_apres_chaque_fusion(self):
        """**Après une fusion** : c'est là que la question a une réponse neuve.

        Le déploiement vient d'avoir lieu ; la veille dit s'il est arrivé. Sans
        ce déclencheur, la seule vérification régulière serait un calendrier —
        or ce dépôt n'a reçu **aucun** événement `schedule` (mesuré le
        15 octobre 2026, voir `docs/HEBERGEMENT.md`) : la veille ne tournerait
        plus jamais, et sa page de suivi resterait figée sur un verdict périmé.
        """
        self.assertIn("workflow_dispatch:", self.texte)
        self.assertIn("schedule:", self.texte)
        self.assertIn("cron:", self.texte)
        bloc = self.texte[self.texte.index("\n  push:\n"):self.texte.index("permissions:")]
        self.assertIn("branches: [main]", bloc,
                      "la veille ne se déclenche pas après une fusion")
        self.assertNotIn("branches-ignore", bloc)

    def test_la_veille_s_eprouve_avant_une_fusion_qui_la_touche(self):
        """L'exercer sur ce qu'elle interroge, plutôt que le découvrir après."""
        bloc = self.texte[self.texte.index("\n  pull_request:\n"):
                          self.texte.index("permissions:")]
        for chemin in ("outils/verifier-surface-en-ligne.py",
                       "simulateur/surface_publique.py",
                       ".github/workflows/veille-en-ligne.yml"):
            with self.subTest(chemin=chemin):
                self.assertIn(chemin, bloc)

    def test_la_page_de_suivi_dit_ce_qui_a_declenche_le_passage(self):
        """Une fusion, le calendrier, une demande : trois raisons, trois lectures.

        Sans cela, un lecteur ne peut pas savoir si le verdict est **postérieur**
        à son déploiement — c'est-à-dire si la page parle de la version qu'il
        vient de mettre en ligne.
        """
        # Commentaires retirés avant de juger : la variable est aussi nommée
        # dans l'explication qui accompagne la ligne, et un contrôle qui lit
        # l'explication au lieu du code valide son propre commentaire — vu le
        # 15 octobre 2026, une fois de plus.
        lignes = [ligne for ligne in self.texte.splitlines()
                  if not ligne.strip().startswith("#")]
        code = "\n".join(lignes)
        self.assertIn("entete=$(printf", code, "l'en-tête du rapport n'est plus construit")
        # L'affectation entière : la commande s'étale sur plusieurs lignes, et
        # c'est l'ensemble qui doit porter la variable — pas la ligne du format.
        entete = code[code.index("entete=$(printf"):code.index("corps=$(printf")]
        self.assertIn("$GITHUB_EVENT_NAME", entete,
                      "l'en-tête publié ne dit plus ce qui a déclenché le passage")

    def test_elle_a_le_droit_d_ecrire_une_page(self):
        self.assertIn("issues: write", self.texte)

    def test_elle_cree_la_page_de_suivi_et_la_tient_a_jour(self):
        """Créée une fois, commentée ensuite : un rapport qui s'empile ne se lit pas."""
        self.assertIn("gh issue create", self.texte)
        self.assertIn('marqueur="<!-- veille-en-ligne -->"', self.texte)
        self.assertIn("gh api -X PATCH", self.texte)
        self.assertIn("gh api -X POST", self.texte)
        self.assertIn("gh issue list", self.texte)

    def test_le_verdict_est_publie_meme_quand_la_veille_echoue(self):
        """Sinon la panne la plus intéressante serait celle qu'on ne publie pas."""
        bloc = self.texte[self.texte.index("Publier le verdict sur la page"):]
        self.assertIn("if: always()", bloc[:400])

    def test_le_rapport_vient_du_verificateur_pas_d_un_texte_invente(self):
        self.assertIn("--rapport /tmp/veille.md", self.texte)
        self.assertIn("cat /tmp/veille.md", self.texte)

    def test_il_ne_redéfinit_pas_la_variable_reservee_du_coureur(self):
        """`GITHUB_STEP_SUMMARY` ne se laisse pas rediriger par un `env:`.

        Le 15 octobre 2026, la veille a tourné, le verdict existait, et la page
        de suivi est restée **vide** : le rapport était parti dans le résumé de
        l'étape, pas dans le fichier que l'étape suivante publiait. Le contrôle
        interdit le retour de cette façon de faire — silencieuse par nature.
        """
        self.assertNotIn("GITHUB_STEP_SUMMARY:", self.texte)
        self.assertIn("--essais 5", self.texte,
                      "la copie de secours s'endort : sans insistance, un réveil "
                      "passerait pour une panne")


class TestDeuxPoidsDeuxMesures(unittest.TestCase):
    """L'adresse partagée décide de la couleur ; la copie de secours informe."""

    @classmethod
    def setUpClass(cls):
        cls.texte = VEILLE.read_text(encoding="utf-8")

    def test_l_adresse_canonique_fait_rougir_la_veille(self):
        self.assertRegex(self.texte, r"grep -qE '\^\\\| ✗ canonique '")

    def test_la_copie_de_secours_est_publiee_sans_sanction(self):
        bloc = self.texte[self.texte.index("Rouge seulement si"):]
        self.assertRegex(bloc, r"grep -qE '\^\\\| ✗ secours '")
        # Le seul « exit 1 » de cette étape vise l'absence de rapport et
        # l'échec canonique : la copie de secours, non.
        self.assertNotRegex(bloc, r"✗ secours .*\n.*exit 1")

    def test_aucun_hebergeur_n_est_ecrit_en_dur(self):
        """Les adresses vivent dans un seul fichier : `surface_publique`."""
        for nom, texte in (("veille", self.texte), ("crochet", CROCHET.read_text(encoding="utf-8"))):
            with self.subTest(fichier=nom):
                self.assertNotIn("onrender.com", texte)
                self.assertNotIn("vercel.app", texte)


class TestLeCrochetEstOptionnel(unittest.TestCase):
    """Réveiller la copie de secours sans tableau de bord — quand on l'a décidé."""

    @classmethod
    def setUpClass(cls):
        cls.texte = CROCHET.read_text(encoding="utf-8")

    def test_il_se_declenche_apres_chaque_fusion_et_a_la_demande(self):
        self.assertIn("push:", self.texte)
        self.assertIn("branches: [main]", self.texte)
        self.assertIn("workflow_dispatch:", self.texte)

    def test_sans_crochet_l_etape_ne_fait_rien_et_le_dit(self):
        self.assertIn("secrets.RENDER_DEPLOY_HOOK", self.texte)
        self.assertIn('if [ -z "$CROCHET" ]', self.texte)
        bloc = self.texte[self.texte.index('if [ -z "$CROCHET" ]'):]
        # Le mot « fi » se cache dans « configuré » : on cherche le `fi` de
        # fermeture, seul sur sa ligne, pas la première syllabe venue.
        fermeture = re.search(r"\n\s*fi\b", bloc)
        self.assertIsNotNone(fermeture, "le bloc `if` du crochet n'est pas refermé")
        self.assertIn("exit 0", bloc[:fermeture.start()],
                      "sans crochet, l'étape doit s'arrêter proprement")

    def test_avec_crochet_il_est_utilise_pour_de_vrai(self):
        self.assertIn('curl -fsS -X POST "$CROCHET"', self.texte)
        self.assertIn("exit 1", self.texte,
                      "un crochet muet doit se voir : c'est le signe d'un crochet périmé")

    def test_il_n_ecrit_rien_dans_le_depot(self):
        self.assertIn("permissions:", self.texte)
        self.assertNotIn("contents: write", self.texte)

    def test_le_mode_d_emploi_est_dans_la_documentation(self):
        """Le secret ne sert à rien si personne ne sait où le coller."""
        doc = HEBERGEMENT.read_text(encoding="utf-8")
        self.assertIn("Deploy Hook", doc)
        self.assertIn("RENDER_DEPLOY_HOOK", doc)
        self.assertIn("veille-en-ligne.yml", doc)


class TestLaPanneSeRepareEnDeuxClics(unittest.TestCase):
    """Ce que dit la documentation quand un visiteur annonce un 502."""

    @classmethod
    def setUpClass(cls):
        cls.doc = HEBERGEMENT.read_text(encoding="utf-8")

    def test_la_documentation_nomme_la_panne_et_la_reparation(self):
        for mot in ("502", "Manual Deploy", "Resume", "suspendu"):
            with self.subTest(mot=mot):
                self.assertIn(mot, self.doc,
                              f"la réparation ne dit pas « {mot} »")

    def test_la_documentation_distingue_les_deux_adresses(self):
        """Savoir laquelle tombe change tout : la copie de secours n'est pas le site."""
        self.assertIn(surface.HOTE_SECOURS, self.doc)
        self.assertIn(surface.URL_CANONIQUE, self.doc)
        self.assertIn("copie de secours", self.doc)


if __name__ == "__main__":
    unittest.main()
