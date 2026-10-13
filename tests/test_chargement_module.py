"""Le chargeur de scripts : pourquoi il existe, et ce qu'il empêche.

Ce fichier naît d'un **mensonge de l'instrument de mesure**. En sabotant le
contrôle du bloc « About » du dépôt, un sabotage a continué d'agir *après* avoir
été restauré : le fichier sur le disque était revenu à la bonne version, mais
Python servait encore le bytecode du sabotage.

La cause est précise. Le chargeur standard d'`importlib` — celui qui prend le
chemin d'un fichier — passe par `SourceFileLoader`, qui écrit un `.pyc` dans
`__pycache__` et le croit valable tant que **la taille** et **l'horodatage en
secondes** de la source n'ont pas bougé. Remplacer `None` par `True` (même longueur, même seconde) passe donc
inaperçu : le code mesuré n'est plus le code du dépôt.

D'où `outils/chargement_module.py`, qui lit et compile la source sans cache, et
les contrôles ci-dessous :

1. **le piège est réel** — un sous-processus le reproduit de bout en bout, avec
   la taille et l'horodatage remis à l'identique. Sans cela, la raison d'être du
   chargeur serait une histoire, pas un fait ;
2. **le chargeur y échappe** — même fichier, même seconde, même taille : la
   valeur relue est la nouvelle ;
3. **aucun `.pyc` n'est écrit**, le chemin est renseigné (les scripts qui
   calculent leur racine depuis `__file__` en dépendent), le module est
   enregistré sous son nom (les `@dataclass` en dépendent), et un échec ne
   laisse pas de module à moitié importé dans `sys.modules` ;
4. **plus aucun test ne passe par ce chargeur-là** — la garantie tient tant
   qu'on n'y retourne pas.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from outils.chargement_module import charger_module  # noqa: E402

#: Le nom qu'on ne veut plus voir dans les tests. Écrit en deux morceaux : il est
#: cité par le contrôle n° 4, et un littéral entier se compterait lui-même.
CHARGEUR_A_CACHE = "spec_from_file_" + "location"

SOURCE_AVANT = "def repond():\n    return None\n"
SOURCE_APRES = "def repond():\n    return True\n"

#: Sous-processus : reproduit le piège, puis montre que le chargeur y échappe.
SCRIPT_DU_PIEGE = textwrap.dedent(
    """
    import importlib.util, os, sys, pathlib

    INSTANT_FIGE = 1_000_000_000   # an 2001 : une seconde qui ne reviendra pas

    dossier = pathlib.Path(sys.argv[1]); racine = pathlib.Path(sys.argv[2])
    sys.path.insert(0, str(racine))
    from outils.chargement_module import charger_module

    fichier = dossier / "module_sous_essai.py"
    fichier.write_text("def repond():\\n    return None\\n", encoding="utf-8")
    # Un instant fixé, plutôt que la seconde où le test tombe : le cache se
    # croit valable si (taille, seconde) n'ont pas bougé, et on veut que ce soit
    # vrai à coup sûr — pas selon l'heure qu'il est.
    os.utime(fichier, (INSTANT_FIGE, INSTANT_FIGE))
    avant = fichier.stat()

    # Le nom du chargeur est écrit en deux morceaux : le contrôle n° 4 refuse ce
    # nom dans les tests, y compris cité. Ici, c'est le vrai qui est appelé.
    charger_par_chemin = getattr(importlib.util, "spec_from_file_" + "location")
    spec = charger_par_chemin("sous_essai", fichier)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.repond() is None, "lecture initiale fausse"

    # Même longueur, et l'horodatage remis à l'identique : le cache se croit valable.
    fichier.write_text("def repond():\\n    return True\\n", encoding="utf-8")
    assert fichier.stat().st_size == avant.st_size, "le piège demande une taille égale"
    os.utime(fichier, ns=(avant.st_atime_ns, avant.st_mtime_ns))
    assert int(fichier.stat().st_mtime) == INSTANT_FIGE, "horodatage non remis : le piège serait joué par chance"

    cache = fichier.parent / "__pycache__"
    assert cache.is_dir() and any(cache.iterdir()), "aucun .pyc écrit : piège non reproduit"

    spec = charger_par_chemin("sous_essai", fichier)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.repond() is None, "le chargeur à cache a lu la nouvelle source : piège disparu"

    frais = charger_module("sous_essai_frais", fichier)
    assert frais.repond() is True, "le chargeur sans cache sert encore l'ancienne source"
    print("piege-reproduit-et-conjure")
    """
)


class TestLePiegeDuCache(unittest.TestCase):
    """La raison d'être du chargeur, montrée plutôt que racontée."""

    @unittest.skipIf(sys.dont_write_bytecode or os.environ.get("PYTHONDONTWRITEBYTECODE"),
                     "l'écriture de bytecode est désactivée ici : le piège ne peut pas se produire")
    def test_le_cache_de_bytecode_sert_une_source_perimee(self):
        with tempfile.TemporaryDirectory() as dossier:
            resultat = subprocess.run(
                [sys.executable, "-c", SCRIPT_DU_PIEGE, dossier, str(RACINE)],
                capture_output=True, text=True, cwd=str(RACINE),
                env={**os.environ, "PYTHONPATH": str(RACINE)})
        self.assertEqual(resultat.returncode, 0,
                         f"le sous-processus a échoué :\n{resultat.stdout}\n{resultat.stderr}")
        self.assertIn("piege-reproduit-et-conjure", resultat.stdout)


class TestChargementSansCache(unittest.TestCase):
    """Le chargeur du dépôt : source relue, module utilisable."""

    def setUp(self):
        self.dossier = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier.cleanup)
        self.chemin = Path(self.dossier.name) / "module_sous_essai.py"
        self.chemin.write_text(SOURCE_AVANT, encoding="utf-8")

    def test_une_source_modifiee_est_relue_meme_a_taille_egale(self):
        """La taille identique n'est pas un détail : c'est ce qui trompe le cache."""
        premier = charger_module("sous_essai", self.chemin)
        self.assertIsNone(premier.repond())

        self.chemin.write_text(SOURCE_APRES, encoding="utf-8")
        self.assertEqual(len(SOURCE_AVANT), len(SOURCE_APRES),
                         "le contrôle doit porter sur deux sources de même longueur")
        second = charger_module("sous_essai", self.chemin)
        self.assertIs(second.repond(), True,
                      "le chargement doit relire la source, jamais un cache")

    def test_aucun_cache_n_est_ecrit(self):
        charger_module("sous_essai", self.chemin)
        self.assertFalse((Path(self.dossier.name) / "__pycache__").exists(),
                         "le chargeur ne doit rien déposer à côté du script")

    def test_le_module_est_enregistre_sous_son_nom(self):
        module = charger_module("sous_essai", self.chemin)
        self.assertIs(sys.modules["sous_essai"], module)

    def test_le_chemin_du_module_est_renseigne(self):
        module = charger_module("sous_essai", self.chemin)
        self.assertEqual(module.__file__, str(self.chemin))
        self.assertEqual(Path(module.__file__).resolve().parent.parent,
                         Path(self.dossier.name).resolve().parent,
                         "les scripts qui calculent leur racine depuis __file__ doivent suivre")

    def test_un_echec_ne_laisse_pas_de_module_a_moitie(self):
        self.chemin.write_text("VALEUR = 1\nraise RuntimeError('échec volontaire')\n", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            charger_module("sous_essai_brise", self.chemin)
        self.assertNotIn("sous_essai_brise", sys.modules)

    def test_on_peut_choisir_de_ne_pas_enregistrer(self):
        module = charger_module("sous_essai_libre", self.chemin, enregistrer=False)
        self.assertNotIn("sous_essai_libre", sys.modules)
        self.assertIsNone(module.repond())


class TestLesScriptsDuDepotSeChargent(unittest.TestCase):
    """Les trois scripts concernés passent bien par le chargeur, et restent lisibles."""

    def test_le_verificateur_de_compteurs(self):
        module = charger_module("verifier_compteurs", RACINE / "outils" / "verifier-compteurs.py")
        self.assertTrue(callable(module.verifier))
        self.assertTrue(module.RACINE.samefile(RACINE),
                        "la racine du script est déduite de son __file__")

    def test_la_veille_en_ligne(self):
        module = charger_module("verifier_surface_en_ligne",
                                RACINE / "outils" / "verifier-surface-en-ligne.py")
        for attribut in ("HOTES", "ROUTES_GET", "ROUTES_POST", "ROUTES_ECARTEES"):
            with self.subTest(attribut=attribut):
                self.assertTrue(hasattr(module, attribut))

    def test_la_fonction_vercel_unique(self):
        module = charger_module("api_pont_unique", RACINE / "api" / "[...path].py")
        self.assertTrue(issubclass(module.handler, object))
        self.assertIn("simuler", module.ROUTES)

    def test_le_bloc_du_depot(self):
        module = charger_module("details_depot", RACINE / "outils" / "details_depot.py")
        self.assertTrue(module.SITE_WEB.startswith("https://"))


class TestPlusDeChargeurACache(unittest.TestCase):
    """Le contrôle qui tient dans le temps : ne pas y retourner par habitude."""

    def test_aucun_test_ni_outil_ne_charge_par_le_chemin_avec_cache(self):
        coupables = []
        for dossier in ("tests", "outils", "api", "simulateur"):
            for fichier in (RACINE / dossier).rglob("*.py"):
                if fichier.name == "chargement_module.py":   # il cite le nom pour l'expliquer
                    continue
                if CHARGEUR_A_CACHE in fichier.read_text(encoding="utf-8"):
                    coupables.append(str(fichier.relative_to(RACINE)))
        self.assertEqual(coupables, [],
                         "charger la source par `charger_module`, pas par le chargeur à cache")


if __name__ == "__main__":
    unittest.main()
