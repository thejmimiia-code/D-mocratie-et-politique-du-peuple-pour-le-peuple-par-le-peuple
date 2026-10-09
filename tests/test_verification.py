"""Transparence : chaque donnée porte un statut, et « vérifié » exige une source datée."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from simulateur import verification as v  # noqa: E402
from simulateur.parametres import LEVIERS  # noqa: E402
from simulateur.reglements_lois import REGISTRE_LEGAL  # noqa: E402


class TestStatutsDeVerification(unittest.TestCase):
    def test_chaque_levier_a_un_statut_valide(self):
        for cle, levier in LEVIERS.items():
            with self.subTest(levier=cle):
                self.assertIn(v.verification_levier(cle, levier.source).statut, v.STATUTS)

    def test_chaque_article_a_un_statut_valide(self):
        for identifiant in REGISTRE_LEGAL:
            with self.subTest(article=identifiant):
                self.assertIn(v.verification_article(identifiant).statut, v.STATUTS)

    def test_aucune_entree_orpheline(self):
        self.assertEqual(set(v.VERIFICATIONS_LEVIERS) - set(LEVIERS), set())
        self.assertEqual(set(v.VERIFICATIONS_ARTICLES) - set(REGISTRE_LEGAL), set())

    def test_verifie_et_partiel_exigent_une_source_datee(self):
        for table in (v.VERIFICATIONS_LEVIERS, v.VERIFICATIONS_ARTICLES):
            for cle, entree in table.items():
                if entree.statut in ("verifie", "partiel"):
                    with self.subTest(cle=cle):
                        self.assertTrue(entree.source_url.startswith("https://"), cle)
                        self.assertRegex(entree.verifie_le, r"^\d{4}-\d{2}-\d{2}$")

    def test_une_donnee_sans_entree_est_non_verifiee_et_le_dit(self):
        inconnue = v.verification_levier("cle_inexistante", "Source quelconque")
        self.assertEqual(inconnue.statut, "non_verifie")
        self.assertIn("non consultée", inconnue.note)

    def test_hypothese_du_dossier_est_signalee_comme_interne(self):
        bilan = v.verification_levier("cle_inexistante", "DOSSIER_DE_MANDATURE_GLOBAL.md (Volet 3)")
        self.assertIn("hypothèse", bilan.note)

    def test_statut_inconnu_refuse(self):
        with self.assertRaises(ValueError):
            v.Verification("certifie")

    def test_catalogue_expose_le_statut_et_le_renvoi(self):
        dictionnaire = LEVIERS["ondam_variation"].en_dict()
        statut = dictionnaire["verification"]
        self.assertEqual(statut["statut"], "verifie")
        self.assertTrue(statut["page"].endswith("VERIFICATION_DONNEES.md#ondam_variation"))
        self.assertIn("issues/new", statut["formulaire"])


class TestPageEtInterface(unittest.TestCase):
    def test_page_publique_synchronisee_avec_le_code(self):
        commande = subprocess.run(
            [sys.executable, "outils/generer-page-verification.py", "--verifier"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(commande.returncode, 0, commande.stdout + commande.stderr)

    def test_page_liste_chaque_levier_et_article(self):
        page = (ROOT / "docs" / "VERIFICATION_DONNEES.md").read_text(encoding="utf-8")
        for cle in LEVIERS:
            with self.subTest(levier=cle):
                self.assertIn(f'<a id="{cle}"></a>', page)
        for identifiant in REGISTRE_LEGAL:
            with self.subTest(article=identifiant):
                self.assertIn(f'<a id="{identifiant}"></a>', page)

    def test_interface_affiche_statut_et_saisie_citoyenne(self):
        from simulateur.interface import HTML_PAGE

        for marqueur in ("badgeVerificationHtml", "saisieCitoyenneHtml", "NON VÉRIFIÉE PAR LE MRSC",
                         "Ce chiffre n'entre pas dans le calcul", "@media print", "non-verifie"):
            with self.subTest(marqueur=marqueur):
                self.assertIn(marqueur, HTML_PAGE)


if __name__ == "__main__":
    unittest.main()
