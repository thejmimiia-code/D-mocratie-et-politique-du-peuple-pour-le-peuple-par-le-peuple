#!/usr/bin/env python3
"""outils/mesurer_fluidite.py — mesure reproductible de la fluidité du serveur.

Pourquoi cet outil
------------------

« C'est plus fluide » est une opinion ; « la réponse de simulation passe de
257 Kio à 38 Kio » est une mesure. Ce script sert le simulateur sur un port
libre, interroge ses routes comme le ferait un navigateur, et rapporte deux
choses :

1. **le volume échangé**, brut et compressé : c'est ce que paie l'utilisateur
   sur une connexion ordinaire, et la seule grandeur qui explique
   l'impression de lenteur quand le calcul ne prend que 35 ms ;
2. **le temps de réponse**, en particulier l'effet du cache des bulles, dont
   le calcul complet coûtait plusieurs secondes.

`--verifier` confronte ces volumes à la table des plafonds
(`outils/budgets_fluidite.py`) et sort en code 1 dès qu'une charge franchit son
budget : c'est l'étape que la CI exécute, et c'est ce qui distingue une mesure
d'un engagement.

Il n'installe rien et n'écrit rien : bibliothèque standard uniquement, comme le
reste du dépôt.

Usage
-----

    python3 outils/mesurer_fluidite.py                    # tableau lisible
    python3 outils/mesurer_fluidite.py --markdown         # tableau pour la doc
    python3 outils/mesurer_fluidite.py --repetitions 7
    python3 outils/mesurer_fluidite.py --verifier         # plafonds de poids, code de sortie
    python3 outils/mesurer_fluidite.py --verifier --rapport-fichier mesure.json

Le serveur est lancé en ``SIMULATEUR_HORS_LIGNE=1`` : aucune API publique
n'est interrogée, les mesures ne dépendent donc pas du réseau.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import socket
import statistics
import sys
import threading
import time
import urllib.request
from http.client import HTTPConnection
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

try:                                        # lancé comme script : outils/ est sur le chemin
    import budgets_fluidite as plafonds
except ImportError:                         # importé par chemin (tests, autres outils)
    from outils import budgets_fluidite as plafonds  # type: ignore[no-redef]

os.environ.setdefault("SIMULATEUR_HORS_LIGNE", "1")

from simulateur.dashboard import create_server  # noqa: E402


def _port_libre() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class Serveur:
    """Serveur éphémère, arrêté quoi qu'il arrive."""

    def __init__(self) -> None:
        self.port = _port_libre()
        self.serveur = create_server("127.0.0.1", self.port)
        self.thread = threading.Thread(target=self.serveur.serve_forever, daemon=True)
        self.thread.start()

    def arreter(self) -> None:
        self.serveur.shutdown()
        self.serveur.server_close()

    def taille(self, chemin: str, encodage: str | None) -> int:
        """Taille réellement transmise pour un GET, avec ou sans compression."""
        connexion = HTTPConnection("127.0.0.1", self.port, timeout=120)
        entetes = {"Accept-Encoding": encodage} if encodage else {}
        connexion.request("GET", chemin, headers=entetes)
        reponse = connexion.getresponse()
        reponse.read()
        annonce = int(reponse.getheader("Content-Length") or 0)
        connexion.close()
        return annonce

    def temps(self, chemin: str, encodage: str | None = "gzip") -> float:
        """Durée du meilleur aller-retour, en millisecondes."""
        connexion = HTTPConnection("127.0.0.1", self.port, timeout=120)
        entetes = {"Accept-Encoding": encodage} if encodage else {}
        debut = time.perf_counter()
        connexion.request("GET", chemin, headers=entetes)
        reponse = connexion.getresponse()
        reponse.read()
        duree = (time.perf_counter() - debut) * 1000
        connexion.close()
        return duree

    def post(self, chemin: str, corps: dict, encodage: str = "gzip") -> tuple[float, int]:
        charge = json.dumps(corps).encode("utf-8")
        connexion = HTTPConnection("127.0.0.1", self.port, timeout=300)
        debut = time.perf_counter()
        connexion.request(
            "POST", chemin, body=charge,
            headers={"Content-Type": "application/json", "Accept-Encoding": encodage},
        )
        reponse = connexion.getresponse()
        reponse.read()
        duree = (time.perf_counter() - debut) * 1000
        taille = int(reponse.getheader("Content-Length") or 0)
        connexion.close()
        return duree, taille


def _parametres_depuis_catalogue(serveur: Serveur) -> dict:
    with urllib.request.urlopen(
        f"http://127.0.0.1:{serveur.port}/api/catalogue", timeout=60
    ) as reponse:
        catalogue = json.loads(reponse.read().decode("utf-8"))
    parametres = dict(catalogue["parametres"]["defauts"])
    parametres.update(catalogue["parametres"]["presets"]["mandature"]["parametres"])
    return parametres


def plan_de_mesure() -> list[tuple[str, str, str]]:
    """Ce que la campagne mesure : (clé de budget, méthode, chemin).

    La table des routes vient du budget lui-même (`ROUTES_MESUREES`) ; les deux
    simulations s'y ajoutent. `tests/test_budgets_fluidite.py` compare ce plan aux
    plafonds — aucune charge mesurée sans budget, aucun budget sans mesure — et aux
    routes que la page appelle, pour qu'aucune ne reste sans plafond ni sans motif.
    """
    plan = [(cle, "GET", chemin) for chemin, cle in plafonds.ROUTES_MESUREES]
    plan.append(("simuler_5ans", "POST", "/api/simuler"))
    plan.append(("simuler_10ans", "POST", "/api/simuler"))
    return plan


def mesurer(repetitions: int = 5) -> dict:
    """Exécute la campagne de mesure et renvoie un rapport structuré."""
    serveur = Serveur()
    try:
        parametres = _parametres_depuis_catalogue(serveur)

        # Le cache des bulles se paie au premier appel : on le mesure avant les
        # volumes, sinon la campagne relèverait un temps chaud et croirait avoir
        # gagné quelque chose.
        temps_bulles = [serveur.temps("/api/bulles?detail=resume")
                        for _ in range(3)]

        mesures: list[plafonds.Mesure] = []
        lignes_get = []
        for chemin, cle in plafonds.ROUTES_MESUREES:
            brut = serveur.taille(chemin, None)
            compresse = serveur.taille(chemin, "gzip")
            provenance = f"GET {chemin} (serveur, gzip {compresse} o)"
            if cle == "page":
                # Le fichier publié compte autant que la réponse du serveur : c'est
                # lui que sert l'hébergeur statique, et c'est le même document.
                publiee = plafonds.octets_de_la_page_publiee()
                if publiee > compresse:
                    compresse = publiee
                provenance = (f"GET / {brut} o bruts, index.html {publiee} o "
                              f"compressés (retenu : {compresse} o)")
            lignes_get.append({
                "route": chemin,
                "brut": brut,
                "compresse": compresse,
                "gain": (1 - compresse / brut) if brut else 0.0,
            })
            mesures.append(plafonds.Mesure(cle, compresse, provenance))

        duree_brute, taille_brute = min(
            serveur.post("/api/simuler",
                         {"parametres": parametres, "horizon": 5,
                          "avec_impacts": True, "max_impacts": 16}, "identity")
            for _ in range(repetitions)
        )
        durees_gzip = [serveur.post(
            "/api/simuler",
            {"parametres": parametres, "horizon": 5,
             "avec_impacts": True, "max_impacts": 16}, "gzip")[0]
            for _ in range(repetitions)]
        _, taille_gzip = serveur.post(
            "/api/simuler",
            {"parametres": parametres, "horizon": 5,
             "avec_impacts": True, "max_impacts": 16}, "gzip")

        durees_10ans = [serveur.post(
            "/api/simuler",
            {"parametres": parametres, "horizon": 10,
             "avec_impacts": True, "max_impacts": 16}, "gzip")[0]
            for _ in range(repetitions)]
        _, taille_10ans = serveur.post(
            "/api/simuler",
            {"parametres": parametres, "horizon": 10,
             "avec_impacts": True, "max_impacts": 16}, "gzip")

        mesures.append(plafonds.Mesure("simuler_5ans", taille_gzip,
                              "POST /api/simuler, horizon 5 (gzip)"))
        mesures.append(plafonds.Mesure("simuler_10ans", taille_10ans,
                              "POST /api/simuler, horizon 10 (gzip)"))

        return {
            "get": lignes_get,
            "budgets": [
                {"cle": mesure.cle, "octets": mesure.octets,
                 "provenance": mesure.provenance}
                for mesure in mesures
            ],
            "simuler": {
                "brut_octets": taille_brute,
                "compresse_octets": taille_gzip,
                "gain": 1 - taille_gzip / taille_brute if taille_brute else 0.0,
                "min_ms_brut": duree_brute,
                "mediane_ms_gzip": statistics.median(durees_gzip),
                "mediane_ms_10ans": statistics.median(durees_10ans),
                "compresse_10ans_octets": taille_10ans,
            },
            "bulles": {
                "premier_ms": temps_bulles[0],
                "suivants_ms": temps_bulles[1:],
            },
            "gzip_disponible": "gzip" in gzip.__name__,
        }
    finally:
        serveur.arreter()


def _kio(octets: int) -> str:
    return f"{octets / 1024:,.1f} Kio".replace(",", " ")


def rapport_texte(resultat: dict) -> str:
    lignes = ["Mesure de fluidité — serveur local, mode hors ligne", ""]
    lignes.append(f"{'Route':<22}{'brut':>12}{'gzip':>12}{'gain':>9}")
    lignes.append("-" * 55)
    for ligne in resultat["get"]:
        lignes.append(
            f"{ligne['route']:<22}{_kio(ligne['brut']):>12}{_kio(ligne['compresse']):>12}"
            f"{ligne['gain'] * 100:>8.0f} %"
        )
    simuler = resultat["simuler"]
    lignes.append("-" * 55)
    lignes.append(f"{'POST /api/simuler':<22}{_kio(simuler['brut_octets']):>12}"
                  f"{_kio(simuler['compresse_octets']):>12}{simuler['gain'] * 100:>8.0f} %")
    lignes.append("")
    lignes.append(f"Simulation 5 ans  : médiane {simuler['mediane_ms_gzip']:.0f} ms "
                  f"(sans compression : meilleur cas {simuler['min_ms_brut']:.0f} ms)")
    lignes.append(f"Simulation 10 ans : médiane {simuler['mediane_ms_10ans']:.0f} ms, "
                  f"{_kio(simuler.get('compresse_10ans_octets', 0))} compressés")
    bulles = resultat["bulles"]
    lignes.append(f"Catalogue de bulles : {bulles['premier_ms']:.0f} ms au premier appel, "
                  f"puis {min(bulles['suivants_ms']):.0f} ms (cache)")
    return "\n".join(lignes)


def rapport_markdown(resultat: dict) -> str:
    lignes = ["| Route | Brut | Compressé | Gain |", "|---|---:|---:|---:|"]
    for ligne in resultat["get"]:
        lignes.append(f"| `{ligne['route']}` | {_kio(ligne['brut'])} | "
                      f"{_kio(ligne['compresse'])} | {ligne['gain'] * 100:.0f} % |")
    simuler = resultat["simuler"]
    lignes.append(f"| `POST /api/simuler` (5 ans) | {_kio(simuler['brut_octets'])} | "
                  f"{_kio(simuler['compresse_octets'])} | {simuler['gain'] * 100:.0f} % |")
    return "\n".join(lignes)


def main(argv: list[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.split("\n")[2])
    analyseur.add_argument("--markdown", action="store_true",
                           help="sortie en tableau Markdown (pour la documentation)")
    analyseur.add_argument("--json", action="store_true", help="sortie JSON brute")
    analyseur.add_argument("--repetitions", type=int, default=5,
                           help="répétitions par mesure (défaut : 5)")
    analyseur.add_argument("--verifier", action="store_true",
                           help="confronter les volumes aux plafonds de poids "
                                "(outils/budgets_fluidite.py) et sortir en code 1 "
                                "si un plafond est franchi")
    analyseur.add_argument("--rapport-fichier", type=Path, default=None,
                           help="relire un rapport JSON enregistré au lieu de "
                                "mesurer (contrôle du contrat de sortie)")
    arguments = analyseur.parse_args(argv)

    if arguments.rapport_fichier is not None:
        if not arguments.rapport_fichier.is_file():
            print(f"Rapport introuvable : {arguments.rapport_fichier}", file=sys.stderr)
            return 2
        try:
            resultat = json.loads(arguments.rapport_fichier.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as erreur:
            print(f"Rapport illisible ({erreur}) : {arguments.rapport_fichier}",
                  file=sys.stderr)
            return 2
    else:
        resultat = mesurer(arguments.repetitions)

    mesures = [plafonds.Mesure(**entree) for entree in resultat.get("budgets", [])]

    if arguments.verifier:
        depassements, anomalies = plafonds.verifier(mesures, complet=True)
        print(plafonds.rapport_texte(mesures, complet=True))
        print(f"\nAncres du {plafonds.DATE_ANCRAGE} — "
              f"{len(mesures)} charge(s) mesurée(s), "
              f"{len(depassements)} dépassement(s), {len(anomalies)} anomalie(s).")
        if depassements or anomalies:
            print("Budget de poids non tenu.", file=sys.stderr)
            return 1
        return 0

    if arguments.json:
        print(json.dumps(resultat, ensure_ascii=False, indent=2))
    elif arguments.markdown:
        print(rapport_markdown(resultat))
    else:
        print(rapport_texte(resultat))
    return 0


if __name__ == "__main__":
    sys.exit(main())
