"""Garde-fou des compteurs : ce qui est annoncé doit être ce que le code contient.

Trois propriétés sont contrôlées ici, et la deuxième compte autant que la première :
le dépôt n'annonce aucun compteur périmé, aucun document vivant ne recopie le
compte de ses tests (il change à chaque commit), et le contrôle sait détecter ce
qu'il prétend interdire. Un garde-fou qui ne détecte rien n'est pas un garde-fou,
c'est une décoration : la contre-épreuve ci-dessous lui donne tort à chaque fois
qu'il le mérite.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

_spec = importlib.util.spec_from_file_location(
    "verifier_compteurs", RACINE / "outils" / "verifier-compteurs.py")
verificateur = importlib.util.module_from_spec(_spec)
# Enregistrer le module avant de l'exécuter : les dataclasses ont besoin de le
# retrouver dans `sys.modules` pour être construites.
sys.modules["verifier_compteurs"] = verificateur
_spec.loader.exec_module(verificateur)


class TestCompteursDuDepot(unittest.TestCase):
    """Le dépôt tel qu'il est : aucun compteur périmé, aucune exemption muette."""

    def test_aucun_compteur_perime(self):
        anomalies = verificateur.verifier(RACINE)
        self.assertEqual(anomalies, [], "compteurs périmés :\n" + "\n".join(anomalies))

    def test_aucun_document_vivant_n_annonce_le_compte_de_ses_tests(self):
        """Un compte de tests écrit dans un document est périmé au commit suivant."""
        annonces = [ligne for ligne in verificateur.verifier(RACINE)
                    if "compte de tests" in ligne]
        self.assertEqual(annonces, [], "compte de tests annoncé :\n" + "\n".join(annonces))

    def test_les_exemptions_sont_motivees_et_reelles(self):
        self.assertEqual(verificateur._raisons_des_exemptions(), [])

    def test_les_referentiels_viennent_du_code(self):
        reference = verificateur.reference()
        for cle, valeur in reference.items():
            with self.subTest(referentiel=cle):
                self.assertIsInstance(valeur, int)
                self.assertGreater(valeur, 0)
        # Les valeurs sont lues dans les modules, pas recopiées dans l'outil.
        from simulateur.domaines import DOMAINES
        from simulateur.nuances_institutionnelles import reglages_catalogue
        from simulateur.parametres import LEVIERS

        self.assertEqual(reference["leviers"], len(LEVIERS))
        self.assertEqual(reference["reglages"], len(reglages_catalogue()))
        self.assertEqual(reference["domaines"], len(DOMAINES))

    def test_chaque_referentiel_a_au_moins_une_regle(self):
        couverts = {regle.quoi for regle in verificateur.REGLES}
        self.assertEqual(couverts, set(verificateur.reference()))

    def test_le_nombre_de_routes_suit_le_generateur(self):
        """Le compte des routes vient du générateur, pas d'un fichier engendré."""
        import subprocess

        sortie = subprocess.run(
            [sys.executable, str(RACINE / "outils" / "generer-fonctions-api.py"), "--verifier"],
            capture_output=True, text=True, cwd=RACINE, check=False)
        self.assertEqual(sortie.returncode, 0, sortie.stdout + sortie.stderr)
        routes = re.findall(r'"([a-z_]+)"', (RACINE / "api" / "[...path].py").read_text("utf-8"))
        self.assertGreaterEqual(verificateur.reference()["routes"], 20)
        self.assertGreaterEqual(len(routes), 18)


class TestLeGardeFouDetecte(unittest.TestCase):
    """La contre-épreuve : le contrôle repère un compteur faux, et laisse passer un vrai."""

    @staticmethod
    def _gabarit(regle, delta: int = 0) -> str:
        """La phrase d'essai d'une règle, au compte réel (delta = 0) ou faussé."""
        reference = verificateur.reference()
        valeurs = {"n": reference[regle.quoi] + delta}
        if regle.autre:
            valeurs["autre"] = reference[regle.autre]
        return regle.gabarit.format(**valeurs)

    def _verifier(self, contenu: str, nom: str = "document.md") -> list[str]:
        with tempfile.TemporaryDirectory() as dossier:
            (Path(dossier) / nom).write_text(contenu, encoding="utf-8")
            return verificateur.verifier(dossier)

    def test_il_detecte_un_compteur_perime(self):
        anomalies = self._verifier("Le simulateur expose 93 leviers croisables.\n")
        self.assertEqual(len(anomalies), 1)
        self.assertIn("leviers croisables", anomalies[0])
        self.assertIn("156", anomalies[0], "l'anomalie doit dire le compteur réel")

    def test_il_laisse_passer_le_compteur_du_jour(self):
        reference = verificateur.reference()
        contenu = (f"Le simulateur expose {reference['leviers']} leviers croisables, "
                   f"{reference['presets']} préréglages et {reference['domaines']} domaines d'impact.\n")
        self.assertEqual(self._verifier(contenu), [])

    def test_il_detecte_un_compteur_perime_dans_du_code(self):
        anomalies = self._verifier("# transformation d'un vecteur de 93 leviers\n", nom="moteur.py")
        self.assertEqual(len(anomalies), 1)

    def test_il_ignore_un_document_date(self):
        contenu = "Le catalogue passe de 93 leviers croisables à autre chose.\n"
        self.assertEqual(self._verifier(contenu, nom="CHANGELOG.md"), [])
        self.assertEqual(self._verifier(contenu, nom="RD_UNE_EXPERIENCE.md"), [])
        self.assertEqual(self._verifier(contenu, nom="AUDIT_DE_PASSAGE.md"), [])

    def test_il_refuse_un_compte_de_tests_dans_un_document_vivant(self):
        anomalies = self._verifier("La suite passe 247 tests en une minute.\n")
        self.assertEqual(len(anomalies), 1)
        self.assertIn("compte de tests", anomalies[0])

    def test_il_accepte_un_compte_de_tests_dans_un_rapport_date(self):
        self.assertEqual(self._verifier("La suite passait 247 tests ce jour-là.\n",
                                        nom="AUDIT_DU_JOUR.md"), [])

    def test_chaque_regle_reconnait_son_propre_gabarit(self):
        """Aucune règle morte : chaque règle laisse passer son gabarit au bon compteur."""
        for regle in verificateur.REGLES:
            with self.subTest(quoi=regle.quoi, regle=regle.motif):
                juste = self._gabarit(regle)
                self.assertEqual(self._verifier(juste), [],
                                 f"la règle refuse le compteur réel : {juste}")

    def test_chaque_regle_refuse_un_compteur_faux(self):
        """Chaque règle rugit quand le compteur annoncé n'est pas le sien."""
        for regle in verificateur.REGLES:
            with self.subTest(quoi=regle.quoi, regle=regle.motif):
                faux = self._gabarit(regle, delta=7)
                anomalies = self._verifier(faux)
                self.assertEqual(len(anomalies), 1,
                                 f"la règle ne détecte pas un compteur faux : {faux}")

    def test_chaque_motif_interdit_reconnait_son_gabarit(self):
        for interdit in verificateur.MOTIFS_INTERDITS:
            with self.subTest(motif=interdit.motif):
                essai = interdit.gabarit.format(n=123)
                anomalies = self._verifier(essai)
                self.assertEqual(len(anomalies), 1,
                                 f"le motif interdit ne détecte pas « {essai} »")
                self.assertIn(interdit.raison[:40], anomalies[0])


if __name__ == "__main__":
    unittest.main()
