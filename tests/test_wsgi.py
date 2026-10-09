"""tests/test_wsgi.py — le pont WSGI utilisé pour héberger le simulateur.

Ce module est le seul endroit où l'on vérifie que **le même routeur** sert la
page en local et chez un hébergeur. S'il casse, la page tourne encore sur le
poste et plus en ligne — le pire des deux mondes, car rien ne le signale.

Cinq propriétés sont protégées :

  1. le **statut** est au format WSGI (``"200 OK"``, code *et* libellé) ;
  2. les **flux** sont reconstruits correctement : ligne de requête, en-têtes,
     corps de POST et chaîne de requête ;
  3. la **réponse** est complète et cohérente : ``Content-Length`` exact, corps
     vidé en HEAD, aucune ligne ``HTTP/1.1`` collée au début du HTML ;
  4. la **compression** continue de se négocier à travers le pont ;
  5. une **erreur** applicative devient un 500 propre, jamais une exception qui
     remonte jusqu'au serveur (un hébergeur répondrait 502 sans explication).

Aucune dépendance : ``wsgiref`` fait partie de la bibliothèque standard, et
aucun test n'ouvre le réseau (tout reste sur la boucle locale).
"""

from __future__ import annotations

import gzip
import io
import json
import threading
import unittest
import urllib.error
import urllib.request
from contextlib import redirect_stderr
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import patch
from wsgiref.simple_server import WSGIRequestHandler, make_server

from simulateur.dashboard import DashboardHandler
from simulateur.wsgi import (
    application as application_wsgi,
)
from simulateur.wsgi import (
    creer_application,
)


def environ_wsgi(
    methode: str = "GET",
    chemin: str = "/",
    query: str = "",
    corps: bytes = b"",
    script: str = "",
    entetes: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Fabrique un ``environ`` WSGI minimal mais réaliste."""
    env: Dict[str, Any] = {
        "REQUEST_METHOD": methode,
        "SCRIPT_NAME": script,
        "PATH_INFO": chemin,
        "QUERY_STRING": query,
        "SERVER_PROTOCOL": "HTTP/1.1",
        "REMOTE_ADDR": "127.0.0.1",
        "wsgi.input": io.BytesIO(corps),
    }
    for nom, valeur in (entetes or {}).items():
        env["HTTP_" + nom.upper().replace("-", "_")] = valeur
    if corps:
        env["CONTENT_LENGTH"] = str(len(corps))
        env["CONTENT_TYPE"] = "application/json"
    return env


def appeler(environ: Dict[str, Any]) -> Tuple[str, Dict[str, str], bytes]:
    """Joue une requête WSGI et rend (statut, en-têtes, corps)."""
    capture: Dict[str, Any] = {}

    def demarrer(statut: str, entetes: List[Tuple[str, str]]) -> None:
        capture["statut"] = statut
        capture["entetes"] = entetes

    corps = b"".join(application_wsgi(environ, demarrer))
    return capture["statut"], dict(capture["entetes"]), corps


class TestStatutEtEnTetes(unittest.TestCase):
    """Le contrat WSGI lui-même : un statut complet et des en-têtes propres."""

    def test_le_statut_porte_le_code_et_le_libelle(self):
        # « 200 » seul ferait échouer gunicorn : WSGI exige « 200 OK ».
        statut, _, _ = appeler(environ_wsgi(chemin="/api/lexique"))
        self.assertEqual(statut, "200 OK")
        self.assertTrue(statut[0].isdigit())

    def test_les_entetes_hop_by_hop_sont_ecartees(self):
        # « Connection » et « Server » sont du ressort du serveur, pas de
        # l'application : les laisser passer créerait des doublons et, pour
        # Connection, une réponse illégale derrière un reverse proxy.
        _, entetes, _ = appeler(environ_wsgi(chemin="/api/lexique"))
        noms = {nom.lower() for nom in entetes}
        self.assertNotIn("connection", noms)
        self.assertNotIn("server", noms)
        self.assertNotIn("date", noms)

    def test_content_length_annonce_la_longueur_reelle(self):
        for chemin in ("/", "/api/lexique", "/api/contexte"):
            _, entetes, corps = appeler(environ_wsgi(chemin=chemin))
            self.assertEqual(int(entetes["Content-Length"]), len(corps), chemin)

    def test_le_bloc_d_entetes_ne_fuit_pas_dans_le_corps(self):
        # Sans l'interception de flush_headers, la ligne « HTTP/1.1 200 OK »
        # serait écrite dans wfile et précéderait le HTML.
        _, _, corps = appeler(environ_wsgi())
        self.assertTrue(corps.startswith(b"<!DOCTYPE html>"))
        self.assertNotIn(b"HTTP/1.1", corps[:200])


class TestRoutage(unittest.TestCase):
    """Le pont transmet fidèlement ce que le client a demandé."""

    def test_la_page_d_accueil_est_servie(self):
        statut, entetes, corps = appeler(environ_wsgi())
        self.assertEqual(statut, "200 OK")
        self.assertIn("text/html", entetes["Content-Type"])
        self.assertIn("SCENARIOS", corps.decode("utf-8"))

    def test_une_route_de_l_api_repond_en_json(self):
        _, entetes, corps = appeler(environ_wsgi(chemin="/api/lexique"))
        self.assertIn("application/json", entetes["Content-Type"])
        donnees = json.loads(corps)
        self.assertGreater(donnees["total"], 0)

    def test_une_route_inconnue_rend_404(self):
        statut, _, corps = appeler(environ_wsgi(chemin="/api/inexistante"))
        self.assertTrue(statut.startswith("404"), statut)
        self.assertEqual(corps, b"")

    def test_la_chaine_de_requete_est_transmise(self):
        _, _, corps = appeler(environ_wsgi(chemin="/api/lexique", query="q=spread"))
        donnees = json.loads(corps)
        self.assertEqual(donnees["recherche"], "spread")
        self.assertGreater(len(donnees["termes"]), 0)

    def test_le_prefixe_de_montage_est_conserve(self):
        # Monté sous « /simulateur », l'application doit continuer à router :
        # oublier SCRIPT_NAME renvoie 404 chez l'hébergeur.
        statut, _, _ = appeler(
            environ_wsgi(chemin="/api/lexique", script="/simulateur")
        )
        self.assertEqual(statut, "200 OK")

    def test_le_corps_d_un_post_est_lu(self):
        charge = json.dumps({"scenario": "statut_quo", "horizon": 5}).encode()
        statut, _, corps = appeler(
            environ_wsgi("POST", "/api/simuler", corps=charge)
        )
        self.assertEqual(statut, "200 OK")
        donnees = json.loads(corps)
        self.assertIn("lecture", donnees)
        self.assertGreater(len(donnees["lecture"]["lignes"]), 0)

    def test_un_corps_illisible_ne_fait_pas_tomber_le_processus(self):
        # Un client qui envoie n'importe quoi doit recevoir une erreur HTTP,
        # pas faire exploser le worker.
        statut, _, _ = appeler(
            environ_wsgi("POST", "/api/simuler", corps=b"ceci n'est pas du json")
        )
        self.assertTrue(statut[0].isdigit(), statut)

    def test_head_annonce_la_longueur_sans_envoyer_le_corps(self):
        statut_complet, entetes_get, corps_get = appeler(environ_wsgi("GET"))
        statut_tete, entetes_tete, corps_tete = appeler(environ_wsgi("HEAD"))
        self.assertEqual(statut_tete, statut_complet)
        self.assertEqual(corps_tete, b"")
        self.assertEqual(entetes_tete["Content-Length"], entetes_get["Content-Length"])
        self.assertGreater(len(corps_get), 0)


class TestCompressionTraversLePont(unittest.TestCase):
    """La négociation d'encodage survit au passage par WSGI."""

    def test_gzip_est_applique_et_annonce(self):
        _, entetes, corps = appeler(
            environ_wsgi(chemin="/api/lexique", entetes={"Accept-Encoding": "gzip"})
        )
        self.assertEqual(entetes["Content-Encoding"], "gzip")
        self.assertEqual(entetes["Vary"], "Accept-Encoding")
        json.loads(gzip.decompress(corps))  # décompressible et valide

    def test_identity_donne_une_reponse_brute(self):
        _, entetes, corps = appeler(
            environ_wsgi(chemin="/api/lexique",
                         entetes={"Accept-Encoding": "identity"})
        )
        self.assertNotIn("Content-Encoding", entetes)
        self.assertTrue(corps.startswith(b"{"))

    def test_sans_en_tete_client_la_reponse_reste_lisible(self):
        _, entetes, corps = appeler(environ_wsgi(chemin="/api/lexique"))
        self.assertNotIn("Content-Encoding", entetes)
        json.loads(corps)


class TestRobustesse(unittest.TestCase):
    """Une panne applicative devient une réponse, jamais une exception."""

    def test_une_exception_devient_un_500_avec_trace_dans_les_journaux(self):
        erreurs = io.StringIO()
        with patch.object(DashboardHandler, "do_GET", side_effect=RuntimeError("boom")):
            with redirect_stderr(erreurs):
                statut, entetes, corps = appeler(environ_wsgi())
        self.assertTrue(statut.startswith("500"), statut)
        self.assertIn("text/plain", entetes["Content-Type"])
        self.assertEqual(int(entetes["Content-Length"]), len(corps))
        # La trace part dans les journaux de l'hébergeur, pas dans la réponse.
        self.assertIn("RuntimeError", erreurs.getvalue())
        self.assertNotIn(b"Traceback", corps)

    def test_l_application_est_reutilisable_entre_les_requetes(self):
        # gunicorn n'en construit qu'une et la réutilise pour toutes les
        # requêtes : aucune requête ne doit en modifier une autre.
        application = creer_application()
        resultats = []
        for _ in range(3):
            capture: Dict[str, Any] = {}

            def demarrer(statut, entetes, destination=capture):
                destination["statut"] = statut
                destination["entetes"] = entetes

            corps = b"".join(application(environ_wsgi(chemin="/api/lexique"), demarrer))
            resultats.append((capture["statut"], corps))
        self.assertEqual(len({statut for statut, _ in resultats}), 1)
        self.assertEqual(len({corps for _, corps in resultats}), 1)


class TestDerriereUnVraiServeurWSGI(unittest.TestCase):
    """Bout en bout : wsgiref sert l'application par HTTP, comme en ligne."""

    @classmethod
    def setUpClass(cls) -> None:
        class Silencieux(WSGIRequestHandler):
            def log_message(self, *args: Any) -> None:
                pass

        cls.serveur = make_server("127.0.0.1", 0, application_wsgi,
                                  handler_class=Silencieux)
        cls.port = cls.serveur.server_address[1]
        cls.thread = threading.Thread(target=cls.serveur.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.serveur.shutdown()
        cls.serveur.server_close()
        cls.thread.join(timeout=5)

    def _url(self, chemin: str) -> str:
        return f"http://127.0.0.1:{self.port}{chemin}"

    def _get(self, chemin: str, entetes: Optional[Dict[str, str]] = None):
        requete = urllib.request.Request(self._url(chemin), headers=entetes or {})
        try:
            with urllib.request.urlopen(requete, timeout=30) as reponse:
                return reponse.status, reponse.headers, reponse.read()
        except urllib.error.HTTPError as erreur:
            return erreur.code, erreur.headers, erreur.read()

    def test_la_page_est_servie_par_http(self):
        statut, entetes, corps = self._get("/")
        self.assertEqual(statut, 200)
        self.assertIn("text/html", entetes.get("Content-Type", ""))
        self.assertTrue(corps.startswith(b"<!DOCTYPE html>"))

    def test_une_api_est_servie_par_http(self):
        statut, _, corps = self._get("/api/lexique")
        self.assertEqual(statut, 200)
        self.assertGreater(json.loads(corps)["total"], 0)

    def test_le_404_traverse_le_serveur(self):
        statut, _, _ = self._get("/api/inexistante")
        self.assertEqual(statut, 404)

    def test_un_post_passe_par_le_serveur(self):
        requete = urllib.request.Request(
            self._url("/api/simuler"),
            data=json.dumps({"scenario": "austerite", "horizon": 5}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(requete, timeout=60) as reponse:
            donnees = json.loads(reponse.read())
        self.assertIn("lecture", donnees)
        self.assertTrue(donnees["lecture"]["resume"])


if __name__ == "__main__":
    unittest.main()
