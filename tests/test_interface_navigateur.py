"""
tests/test_interface_navigateur.py — exécute le JavaScript de la page pour de vrai.

`tests/test_interface.py` contrôle la page comme un texte ; ici, on la fait
tourner : un DOM et un `fetch` minimaux sont fournis à Node.js, les réponses
des routes sont celles du vrai serveur (collectées juste avant), et le script
parcourt le trajet d'un utilisateur — chargement, modification d'un levier,
scénario du dépôt, filtre, réinitialisation, exports, rafraîchissement des
données publiques.

Ce test saute proprement si Node.js n'est pas installé (le reste de la suite
couvre alors le rendu statique).
"""

import json
import os
import socket
import subprocess
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

from simulateur.dashboard import create_server
from simulateur.parametres import LEVIERS

RACINE = Path(__file__).resolve().parent.parent
HARNAIS = RACINE / "tests" / "navigateur_interface.mjs"
NODE = __import__("shutil").which("node")


#: Le serveur testé ne doit jamais interroger les API publiques : sur une
#: machine connectée (CI), la collecte rendrait les tests lents et
#: dépendants du réseau. Le contexte vient donc du snapshot daté.
os.environ.setdefault("SIMULATEUR_HORS_LIGNE", "1")


class TestInterfaceDansNode(unittest.TestCase):
    """Parcours utilisateur complet, exécuté par Node sur la page servie."""

    @classmethod
    def setUpClass(cls):
        if NODE is None:
            raise unittest.SkipTest("Node.js absent : parcours navigateur non exécutable")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        cls.port = sock.getsockname()[1]
        sock.close()
        cls.serveur = create_server("127.0.0.1", cls.port)
        cls.thread = threading.Thread(target=cls.serveur.serve_forever, daemon=True)
        cls.thread.start()
        cls.charge = cls._construire_charge()
        cls._jouer_le_parcours()

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "serveur", None) is not None:
            cls.serveur.shutdown()
            cls.serveur.server_close()

    # ── Collecte des réponses réelles du serveur ──────────────────────────
    @classmethod
    def _get(cls, chemin):
        url = f"http://127.0.0.1:{cls.port}{chemin}"
        with urllib.request.urlopen(url, timeout=60) as reponse:
            return reponse.read().decode("utf-8")

    @classmethod
    def _post(cls, chemin, corps):
        requete = urllib.request.Request(
            f"http://127.0.0.1:{cls.port}{chemin}",
            data=json.dumps(corps).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(requete, timeout=120) as reponse:
            return reponse.read().decode("utf-8")

    @classmethod
    def _simuler(cls, parametres, *, horizon=5, avec_impacts=True):
        return json.loads(cls._post(
            "/api/simuler",
            {"parametres": parametres, "horizon": horizon,
             "avec_impacts": avec_impacts, "max_impacts": 16},
        ))

    @classmethod
    def _construire_charge(cls):
        page = cls._get("/")
        catalogue = json.loads(cls._get("/api/catalogue"))
        contexte = json.loads(cls._get("/api/contexte"))

        # Paramètres du préréglage de démarrage, puis le même jeu avec un
        # levier modifié : les deux réponses sont calculées ici par le serveur,
        # comme le ferait le navigateur.
        defauts = catalogue["parametres"]["defauts"]
        prereglage = dict(defauts)
        prereglage.update(catalogue["parametres"]["presets"]["mandature"]["parametres"])
        cle = "tva_taux_normal"
        assert cle in LEVIERS, f"levier attendu absent : {cle}"
        variante = dict(prereglage)
        variante[cle] = defauts[cle] + 1.0

        # Parcours complet : préréglage de démarrage, levier modifié, préréglage
        # dangereux (austérité), puis retour au neutre. Chaque réponse est
        # calculée par le serveur, dans l'ordre où la page la demandera.
        sortie_prereglage = cls._simuler(prereglage)
        sortie_variante = cls._simuler(variante)
        sortie_austerite = cls._simuler(catalogue["parametres"]["presets"]["austerite"]["parametres"])
        sortie_neutre = cls._simuler(defauts)
        sortie_decennale = cls._simuler(
            catalogue["parametres"]["presets"]["double_mandature"]["parametres"],
            horizon=10,
            avec_impacts=False,
        )

        # Le conseiller temps réel rejoue le moteur sur le même mouvement que
        # l'utilisateur (position avant → position à l'instant T).
        conseil = json.loads(cls._post("/api/conseil", {
            "parametres": variante,
            "cle": cle,
            "avant": defauts[cle],
            "apres": defauts[cle] + 1.0,
        }))

        # Sources publiques : le navigateur les interroge directement, sauf
        # celles qui ne renvoient pas d'en-tête CORS (relais /api/proxy).
        externes = {}
        for indicateur in (contexte.get("browser") or {}).values():
            for source in indicateur.get("sources", []):
                url = source.get("url")
                if url:
                    externes[url] = source.get("adaptateur")
        proxy = json.loads(cls._get("/api/proxy?indicateur=brent_usd"))
        bulle = json.loads(cls._get(f"/api/bulle?levier={cle}&detail=complet"))

        routes = ["POST /api/simuler", "POST /api/simuler#variante",
                  "POST /api/simuler#austerite", "POST /api/simuler#neutre"]
        sequence = list(zip(routes,
                            [sortie_prereglage, sortie_variante, sortie_austerite, sortie_neutre],
                            strict=True))
        return {
            "defauts": defauts,
            "sequence_simuler": [{"route": route} for route, _ in sequence]
                                 + [{"route": "POST /api/simuler#neutre"},
                                    {"route": "POST /api/simuler#decennal"}],
            "page": page,
            "api": {
                "GET /api/catalogue": catalogue,
                "GET /api/contexte": contexte,
                "GET /api/marches": json.loads(cls._get("/api/marches")),
                "GET /api/presets": json.loads(cls._get("/api/presets")),
                "GET /api/comparer": json.loads(cls._get("/api/comparer")),
                "GET /api/scenarios": json.loads(cls._get("/api/scenarios")),
                "GET /api/run": json.loads(cls._get("/api/run?scenario=choc_mondial")),
                "GET /api/proxy": proxy,
                "GET /api/bulle": bulle,
                "GET /api/bulles": json.loads(cls._get("/api/bulles?detail=resume")),
                "GET /api/garde_fous": json.loads(cls._get("/api/garde_fous")),
                "GET /api/lexique": json.loads(cls._get("/api/lexique")),
                "POST /api/simuler": sortie_prereglage,
                "POST /api/simuler#variante": sortie_variante,
                "POST /api/simuler#austerite": sortie_austerite,
                "POST /api/simuler#neutre": sortie_neutre,
                "POST /api/simuler#decennal": sortie_decennale,
                "POST /api/conseil": conseil,
                "POST /api/donnees": {"ok": True},
            },
            "externe": externes,
            "discriminant": {"cle": cle, "valeur": variante[cle]},
            "attendu": {"recettes_nouvelles_mde": sortie_variante["synthese"]["recettes_nouvelles_mde"]},
        }

    # ── Exécution ─────────────────────────────────────────────────────────
    @classmethod
    def _jouer_le_parcours(cls):
        """Joue le parcours une seule fois, pour toute la classe de tests."""
        dossier = tempfile.mkdtemp(prefix="interface-navigateur-")
        chemin_charge = Path(dossier) / "charge.json"
        chemin_rapport = Path(dossier) / "rapport.json"
        chemin_charge.write_text(json.dumps(cls.charge), encoding="utf-8")
        cls.proc = subprocess.run(
            [NODE, str(HARNAIS), str(chemin_charge), str(chemin_rapport)],
            capture_output=True, text=True, timeout=600, cwd=str(RACINE),
        )
        cls.rapport = (json.loads(chemin_rapport.read_text(encoding="utf-8"))
                       if chemin_rapport.exists() else {})

    def test_le_parcours_ne_leve_aucune_exception(self):
        """Le script servi s'exécute de bout en bout sans erreur ni alerte."""
        self.assertEqual(self.proc.returncode, 0,
                         f"sortie Node :\n{self.proc.stdout}\n{self.proc.stderr}")
        self.assertEqual(self.rapport.get("erreurs"), [])
        self.assertEqual(self.rapport.get("alertes"), [])

    def test_toutes_les_etapes_du_parcours_reussissent(self):
        """Chaque étape contrôlée par le harnais est verte."""
        etapes = self.rapport.get("etapes", [])
        self.assertGreaterEqual(len(etapes), 38, f"parcours trop court : {len(etapes)} étapes")
        echecs = [etape for etape in etapes if not etape["ok"]]
        self.assertEqual(echecs, [], f"étapes en échec : {echecs}")

    def test_les_donnees_publiques_sont_interrogees_et_relayees(self):
        """Le rafraîchissement passe par les API publiques puis /api/proxy."""
        appels = self.rapport.get("appels", [])
        externes = [appel for appel in appels if not appel.startswith(("GET /api/", "POST /api/"))]
        self.assertGreater(len(externes), 0, "aucune API publique interrogée depuis le navigateur")
        self.assertTrue(any(appel.startswith("POST /api/donnees") for appel in appels),
                        "le relevé n'est pas transmis au serveur")
        self.assertTrue(any("/api/proxy" in appel for appel in appels),
                        "les sources sans CORS ne sont pas relayées")

    def test_la_simulation_affichee_vient_du_serveur(self):
        """Le levier modifié est bien envoyé au serveur, et sa réponse affichée."""
        postes = [appel for appel in self.rapport.get("appels", [])
                  if appel.startswith("POST /api/simuler")]
        self.assertGreaterEqual(len(postes), 2,
                                "le levier modifié n'a pas déclenché de nouvelle simulation")

    def test_les_exports_sont_produits(self):
        """Les deux boutons d'export déclenchent un téléchargement."""
        telechargements = self.rapport.get("telechargements", [])
        self.assertEqual(len(telechargements), 2, f"téléchargements : {telechargements}")

    def test_un_reglage_se_partage_par_une_adresse(self):
        """Le lien ne transporte que les leviers déplacés et se relit sans confiance."""
        etapes = {etape["nom"]: etape["ok"] for etape in self.rapport.get("etapes", [])}
        for nom in ("le lien partagé reprend l'adresse de la page",
                    "le lien ne transporte que les leviers déplacés",
                    "le lien se relit à l'identique",
                    "un lien hostile ne peut pas injecter un réglage inconnu",
                    "un lien illisible est ignoré sans erreur",
                    "partager renvoie l'adresse calculée, sans copier dans le vide",
                    "l'adresse partagée est reprise à l'ouverture de la page"):
            self.assertTrue(etapes.get(nom), f"étape absente ou fausse : {nom}")

    def test_la_console_signale_l_austerite_puis_recalcule_le_scenario_de_reference(self):
        """Le rouge signale les risques; le neutre doit être recalculé, pas blanchi artificiellement."""
        etapes = {etape["nom"]: etape["ok"] for etape in self.rapport.get("etapes", [])}
        self.assertTrue(etapes.get("le bandeau hors-sol apparaît"), "aucun bandeau hors-sol affiché")
        self.assertTrue(etapes.get("au moins une strate est marquée hors-sol"))
        self.assertTrue(etapes.get("la réinitialisation recalcule le scénario de référence sans levier actif"))


if __name__ == "__main__":
    unittest.main()
