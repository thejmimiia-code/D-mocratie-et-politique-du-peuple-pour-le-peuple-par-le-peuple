"""
tests/test_conseil.py — le conseiller temps réel (« effet papillon »).

Chaque mouvement de réglage est une décision : la position à l'instant T
par rapport à la position avant le dernier mouvement. Le conseiller rejoue
le moteur deux fois (levier à `avant`, puis à `apres`, toutes choses égales)
et doit rendre une lecture de spécialiste : effets directs, ricochets,
grandeurs qui basculent, garde-fous, journal et pistes de compensation.
"""

import json
import os
import socket
import threading
import unittest
import urllib.request

from simulateur.conseil import (
    GRANDEURS,
    _formuler_mouvement,
    conseil_mouvement,
)
from simulateur.dashboard import create_server
from simulateur.donnees_live import construire_contexte
from simulateur.parametres import LEVIERS

# Le conseiller ne doit jamais dépendre du réseau : contexte hors-ligne.
os.environ.setdefault("SIMULATEUR_HORS_LIGNE", "1")


def _contexte():
    return construire_contexte(utiliser_cache=False, rafraichir=False, hors_ligne=True)


class TestFormulationDuMouvement(unittest.TestCase):
    """La phrase décrit fidèlement la décision (le mouvement du réglage)."""

    def test_curseur_monte(self):
        levier = LEVIERS["tva_taux_normal"]
        phrase = _formuler_mouvement(levier, 0.0, 1.0)
        self.assertIn("monté", phrase)
        self.assertIn(levier.libelle, phrase)
        self.assertIn("de", phrase)
        self.assertIn("à", phrase)

    def test_curseur_baisse(self):
        levier = LEVIERS["dgf_delta"]
        phrase = _formuler_mouvement(levier, 0.0, -4.0)
        self.assertIn("baissé", phrase)
        self.assertIn(levier.libelle, phrase)

    def test_interrupteur_active(self):
        levier = LEVIERS["tva_energie_5_5"]
        self.assertEqual(levier.type, "interrupteur")
        phrase = _formuler_mouvement(levier, 0.0, 1.0)
        self.assertIn("activé", phrase)
        self.assertIn(levier.libelle, phrase)

    def test_interrupteur_desactive(self):
        levier = LEVIERS["tva_energie_5_5"]
        phrase = _formuler_mouvement(levier, 1.0, 0.0)
        self.assertIn("désactivé", phrase)

    def test_maintenu(self):
        levier = LEVIERS["tva_taux_normal"]
        phrase = _formuler_mouvement(levier, 1.0, 1.0)
        self.assertIn("maintenu", phrase)


class TestStructureDuConseil(unittest.TestCase):
    """Le conseil est complet et chaque champ est exploitable par l'interface."""

    @classmethod
    def setUpClass(cls):
        cls.contexte = _contexte()

    def _conseil(self, cle, avant, apres, parametres=None):
        return conseil_mouvement(
            parametres if parametres is not None else {cle: apres},
            cle, avant, apres, self.contexte)

    def test_structure_minimale(self):
        conseil = self._conseil("tva_taux_normal", 0.0, 1.0)
        for champ in ("cle", "libelle", "mouvement", "verdict_niveau",
                      "domaines", "ricochets", "grandeurs", "garde_fous",
                      "journal", "compensations", "lecture"):
            self.assertIn(champ, conseil, f"champ manquant : {champ}")
        self.assertEqual(conseil["cle"], "tva_taux_normal")
        self.assertIn(conseil["libelle"], LEVIERS["tva_taux_normal"].libelle)
        self.assertIn("phrase", conseil["mouvement"])
        self.assertEqual(conseil["mouvement"]["avant"], 0.0)
        self.assertEqual(conseil["mouvement"]["apres"], 1.0)

    def test_le_mouvement_est_isole(self):
        """Toutes choses égales : seul le levier bougé doit créer la différence.

        On rejoue le même conseil deux fois : les champs structurés sont
        déterministes pour un état donné du modèle.
        """
        a = self._conseil("tva_taux_normal", 0.0, 1.0)
        b = self._conseil("tva_taux_normal", 0.0, 1.0)
        self.assertEqual(a["domaines"], b["domaines"])
        self.assertEqual(a["grandeurs"], b["grandeurs"])

    def test_domaines_distinguent_direct_et_ricochet(self):
        conseil = self._conseil("tva_energie_5_5", 0.0, 1.0)
        domaines = conseil["domaines"]
        self.assertTrue(domaines, "un mouvement de la TVA énergie doit bouger des domaines")
        for domaine in domaines:
            self.assertIn("direct", domaine)
            self.assertIn("favorable", domaine)
            # favorable = le delta va dans le bon sens
            self.assertEqual(domaine["favorable"], domaine["delta"] > 0)
        # les ricochets sont exactement les domaines non déclarés
        self.assertEqual(conseil["ricochets"], [d for d in domaines if not d["direct"]])

    def test_aucun_bruit_sous_le_seuil(self):
        """Un mouvement nul ne doit pas inventer d'effets."""
        conseil = self._conseil("tva_taux_normal", 1.0, 1.0)
        self.assertEqual(conseil["domaines"], [])
        self.assertEqual(conseil["grandeurs"], [])
        self.assertIn("maintenu", conseil["mouvement"]["phrase"])

    def test_grandeurs_surveillees_sont_coherentes(self):
        conseil = self._conseil("tva_taux_normal", 0.0, 2.0)
        sens_par_cle = {entree[0]: entree[3] for entree in GRANDEURS}
        for grandeur in conseil["grandeurs"]:
            self.assertIn(grandeur["cle"], sens_par_cle)
            self.assertEqual(grandeur["favorable"],
                             sens_par_cle[grandeur["cle"]] * grandeur["delta"] > 0)

    def test_garde_fous_reperes_quand_le_niveau_change(self):
        # -12 % de DGF fait basculer la tension locale et le risque de censure.
        conseil = self._conseil("dgf_delta", 0.0, -12.0)
        cles = {g["cle"] for g in conseil["garde_fous"]}
        self.assertTrue(any("tension" in c.lower() or "censure" in c.lower() for c in cles)
                        or cles, "le mouvement -12 % DGF doit toucher des garde-fous")
        for garde in conseil["garde_fous"]:
            self.assertNotEqual(garde["niveau_avant"], garde["niveau_apres"])
            self.assertIn("aggrave", garde)

    def test_lecture_decrit_la_chaine(self):
        conseil = self._conseil("tva_energie_5_5", 0.0, 1.0)
        self.assertIn(conseil["libelle"], conseil["lecture"])
        if conseil["ricochets"]:
            self.assertIn("ricochet", conseil["lecture"].lower())


class TestEndpointConseil(unittest.TestCase):
    """La route /api/conseil du dashboard relaie le conseiller."""

    @classmethod
    def setUpClass(cls):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        cls.port = sock.getsockname()[1]
        sock.close()
        cls.serveur = create_server("127.0.0.1", cls.port)
        cls.thread = threading.Thread(target=cls.serveur.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.serveur.shutdown()
        cls.serveur.server_close()

    def _post(self, corps):
        requete = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/conseil",
            data=json.dumps(corps).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(requete, timeout=120) as reponse:
                return reponse.status, json.loads(reponse.read().decode("utf-8"))
        except urllib.error.HTTPError as erreur:
            return erreur.code, json.loads(erreur.read().decode("utf-8"))

    def test_conseil_serveur(self):
        statut, conseil = self._post({
            "parametres": {"tva_taux_normal": 1.0},
            "cle": "tva_taux_normal",
            "avant": 0.0,
            "apres": 1.0,
        })
        self.assertEqual(statut, 200)
        self.assertEqual(conseil["cle"], "tva_taux_normal")
        self.assertIn("lecture", conseil)
        self.assertIn("phrase", conseil["mouvement"])

    def test_conseil_sans_cle_rejete(self):
        statut, corps = self._post({"parametres": {}})
        self.assertEqual(statut, 400)
        self.assertIn("error", corps)

    def test_conseil_interrupteur_serveur(self):
        statut, conseil = self._post({
            "parametres": {"tva_energie_5_5": 1.0},
            "cle": "tva_energie_5_5",
            "avant": 0.0,
            "apres": 1.0,
        })
        self.assertEqual(statut, 200)
        self.assertIn("activé", conseil["mouvement"]["phrase"])


if __name__ == "__main__":
    unittest.main()
