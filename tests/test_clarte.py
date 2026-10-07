"""tests/test_clarte.py — la « lecture en clair » d'une simulation.

Ce module ne calcule rien : il relit une sortie du moteur et la met en phrases.
La tentation, en écrivant ce genre de traduction, est de glisser un jugement
(« c'est une bonne politique ») ou un chiffre inventé. Ces tests protègent
contre les deux :

* **fidélité** : chaque phrase reprend des grandeurs présentes dans la charge ;
  les phrases sont complètes et pondérées par un niveau ;
* **honnêteté** : le déficit négatif est dit « excédent », la dépense négative
  « économie », les limites sont rappelées à chaque lecture ;
* **robustesse** : une charge vide, partielle ou dégradée ne lève jamais — une
  lecture courte vaut mieux qu'une lecture inventée.

Le test le plus important est sans doute `test_aucune_phrase_n_invente_de_
chiffre` : il vérifie que tous les nombres affichés dans les phrases existent
déjà dans la sortie du moteur.
"""

import re
import unittest

from simulateur.clarte import (
    SEUILS,
    lecture_claire,
    milliards,
    nombre,
    signe,
)
from simulateur.donnees_live import construire_contexte
from simulateur.moteur_parametrique import simuler
from simulateur.parametres import PRESETS

NOMBRE = re.compile(r"\d[\d ]*[,.]\d+|\d+[\d ]*")


def _contexte():
    return construire_contexte(utiliser_cache=False, rafraichir=False, hors_ligne=True)


def _simuler(nom_preset: str, horizon: int = 5) -> dict:
    parametres = dict(PRESETS[nom_preset]["parametres"])
    return simuler(parametres, _contexte(), horizon=horizon).en_dict()


class TestFormatage(unittest.TestCase):
    """Les nombres sont écrits à la française, jamais en notation anglaise."""

    def test_virgule_decimale(self):
        self.assertEqual(nombre(3.35, 2), "3,35")
        self.assertEqual(nombre(1234.5, 1), "1 234,5")

    def test_valeur_absente_affichee_par_un_tiret(self):
        self.assertEqual(nombre(None), "—")
        self.assertEqual(nombre("abc"), "—")

    def test_signe(self):
        self.assertEqual(signe(1.5), "+")
        self.assertEqual(signe(-1.5), "−")
        self.assertEqual(signe(0), "")

    def test_milliards_avec_signe(self):
        self.assertEqual(milliards(12.34), "+12,3 Md€")
        self.assertEqual(milliards(-12.34), "−12,3 Md€")


class TestLectureComplete(unittest.TestCase):
    """Ce que produit une vraie simulation."""

    @classmethod
    def setUpClass(cls):
        cls.mandature = _simuler("mandature")
        cls.austerite = _simuler("austerite")
        cls.lecture = lecture_claire(cls.mandature)

    def test_structure_de_sortie(self):
        for cle in ("titre", "horizon", "resume", "lignes", "limites"):
            self.assertIn(cle, self.lecture)

    def test_chaque_ligne_est_complete(self):
        self.assertGreaterEqual(len(self.lecture["lignes"]), 5)
        for ligne in self.lecture["lignes"]:
            for cle in ("cle", "grandeur", "valeur", "texte", "niveau", "explication"):
                self.assertIn(cle, ligne)
            self.assertIn(ligne["niveau"],
                          ("favorable", "defavorable", "neutre", "inconnu"))
            self.assertGreater(len(ligne["texte"]), 40)
            self.assertTrue(ligne["texte"].endswith((".", "!", "?")),
                            f"phrase non terminée : {ligne['cle']}")

    def test_le_resume_est_une_phrase(self):
        self.assertGreater(len(self.lecture["resume"]), 30)
        self.assertTrue(self.lecture["resume"].endswith("."))

    def test_les_limites_sont_rappelees(self):
        self.assertGreaterEqual(len(self.lecture["limites"]), 2)
        self.assertTrue(any("référence" in limite for limite in self.lecture["limites"]))
        self.assertTrue(any("prévision" in limite for limite in self.lecture["limites"]))

    def test_les_grandeurs_abordent_l_essentiel(self):
        cles = {ligne["cle"] for ligne in self.lecture["lignes"]}
        for attendu in ("budget", "deficit", "dette", "emprunt", "domaines"):
            self.assertIn(attendu, cles, f"grandeur non lue : {attendu}")

    def test_une_lecture_d_austérite_signale_la_degradation_sociale(self):
        lecture = lecture_claire(self.austerite)
        niveaux = {ligne["niveau"] for ligne in lecture["lignes"]}
        self.assertIn("defavorable", niveaux)

    def test_aucune_phrase_n_invente_de_chiffre(self):
        """Tout nombre affiché dans une phrase vient de la charge du moteur."""
        autorises = self._nombres_de_la_charge(self.mandature)
        for ligne in self.lecture["lignes"]:
            for trouve in NOMBRE.findall(ligne["texte"]):
                brut = trouve.replace(" ", "").replace(",", ".")
                try:
                    valeur = float(brut)
                except ValueError:
                    continue
                self.assertTrue(
                    any(abs(valeur - connu) < 0.051 for connu in autorises)
                    or abs(valeur) in (100.0, 0.0),
                    f"nombre absent de la charge : {valeur} dans « {ligne['cle']} »",
                )

    def _nombres_de_la_charge(self, charge):
        valeurs = []

        def parcourir(objet):
            if isinstance(objet, dict):
                for valeur in objet.values():
                    parcourir(valeur)
            elif isinstance(objet, list):
                for valeur in objet:
                    parcourir(valeur)
            elif isinstance(objet, (int, float)) and not isinstance(objet, bool):
                valeurs.append(abs(float(objet)))
                # Une phrase peut arrondir (« environ 3 315 milliards ») ou
                # changer d'échelle (centièmes de point, milliers).
                valeurs.append(abs(round(float(objet))))
                valeurs.append(abs(float(objet)) / 100.0)
                valeurs.append(abs(float(objet)) * 100.0)
                # Un score de domaine se lit « par rapport à 50 » : l'écart
                # affiché (±49,2 points) est une lecture du score, pas un
                # chiffre nouveau.
                valeurs.append(abs(float(objet) - 50.0))

        parcourir(charge)
        return valeurs


class TestHonnêtetéDesPhrases(unittest.TestCase):
    """Dire « excédent » quand le solde est positif, « économie » quand il baisse."""

    def test_un_deficit_negatif_est_lu_comme_un_excedent(self):
        charge = {
            "synthese": {"deficit_final_pct": -2.5, "deficit_reference_pct": -1.0,
                         "deficit_ecart_pts": -1.5},
            "etapes": [{}],
            "horizon": 5,
        }
        lecture = lecture_claire(charge)
        ligne = [ligne2 for ligne2 in lecture["lignes"] if ligne2["cle"] == "deficit"][0]
        self.assertIn("excédent", ligne["texte"].lower())
        self.assertNotIn("déficit de", ligne["texte"].lower())

    def test_une_dépense_negative_est_lue_comme_une_economie(self):
        charge = {
            "synthese": {"recettes_nouvelles_mde": 0.0, "depenses_nouvelles_mde": -20.0,
                         "solde_mesures_mde": 20.0},
            "etapes": [{}],
            "horizon": 5,
        }
        lecture = lecture_claire(charge)
        ligne = [ligne2 for ligne2 in lecture["lignes"] if ligne2["cle"] == "budget"][0]
        self.assertIn("économiser", ligne["texte"].lower())
        self.assertNotIn("−20,0 Md€ de dépenses en plus", ligne["texte"])

    def test_aucun_domaine_ne_bouge_est_dit_explicitement(self):
        charge = {
            "synthese": {},
            "etapes": [{}],
            "horizon": 5,
            "domaines": [{"cle": "sante", "libelle": "Santé", "score": 50.0}
                         for _ in range(3)],
        }
        lecture = lecture_claire(charge)
        ligne = [ligne2 for ligne2 in lecture["lignes"] if ligne2["cle"] == "domaines"][0]
        self.assertIn("ne bouge", ligne["texte"])
        self.assertNotIn("Le plus pénalisé", ligne["texte"])

    def test_le_plus_penalise_n_est_cite_que_s_il_existe(self):
        charge = {
            "synthese": {},
            "etapes": [{}],
            "horizon": 5,
            "domaines": [
                {"cle": "sante", "libelle": "Santé", "score": 58.0},
                {"cle": "climat", "libelle": "Climat", "score": 50.0},
            ],
        }
        lecture = lecture_claire(charge)
        ligne = [ligne2 for ligne2 in lecture["lignes"] if ligne2["cle"] == "domaines"][0]
        self.assertIn("Le plus aidé", ligne["texte"])
        self.assertNotIn("Le plus pénalisé", ligne["texte"])

    def test_le_statut_europeen_booleen_est_traduit(self):
        for valeur, attendu in ((True, "sous procédure"), (False, "conforme")):
            charge = {"synthese": {"statut_pde": valeur}, "etapes": [{}], "horizon": 5}
            ligne = [ligne2 for ligne2 in lecture_claire(charge)["lignes"] if ligne2["cle"] == "europe"][0]
            self.assertEqual(ligne["valeur"], attendu)


class TestRobustesse(unittest.TestCase):
    """Une charge dégradée ne casse jamais la page."""

    def test_charge_vide(self):
        lecture = lecture_claire({})
        self.assertEqual(lecture["lignes"], [])
        self.assertIn("référence", lecture["resume"])

    def test_charge_non_dictionnaire(self):
        # Une sortie qui n'est même pas un dictionnaire : on ne lit rien, mais
        # on ne lève pas — la page continue de s'afficher.
        lecture = lecture_claire(None)
        self.assertEqual(lecture["lignes"], [])
        self.assertIn("indisponible", lecture["titre"].lower())

    def test_synthese_vide(self):
        lecture = lecture_claire({"synthese": {}, "etapes": [], "horizon": 5})
        self.assertEqual(lecture["lignes"], [])
        self.assertIn("référence", lecture["resume"])

    def test_horizon_repercute(self):
        lecture = lecture_claire(_simuler("mandature", horizon=10))
        self.assertEqual(lecture["horizon"], 10)

    def test_valeurs_none_ignorees(self):
        charge = {"synthese": {"deficit_final_pct": None, "dette_finale_pct": None,
                               "taux_oat_final": None, "tension_finale": None,
                               "confiance_finale": None},
                  "etapes": [{}], "horizon": 5}
        lecture = lecture_claire(charge)
        self.assertEqual(lecture["lignes"], [])

    def test_les_seuils_sont_positifs(self):
        for valeur in SEUILS.values():
            self.assertGreater(valeur, 0)


if __name__ == "__main__":
    unittest.main()
