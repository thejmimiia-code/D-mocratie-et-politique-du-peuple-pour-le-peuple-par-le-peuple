"""tests/test_couverture_des_routes.py — aucune route servie ne reste sans réponse.

Le moteur sert des routes que la page n'appelle pas toutes. Ce n'est pas un
défaut en soi : une route peut exister pour la veille en ligne, pour les tests
de la console, ou parce qu'une autre la résume. Ce qui serait un défaut, c'est
qu'une route serve du contenu que **personne** ne voit — et que personne ne
sache pourquoi.

Ce contrôle tient donc la comptabilité, dans les deux sens :

* une route servie est **servie au lecteur** par la page — un `fetch`, ou un
  lien qu'on lui donne (`href="/api/…"`) — ou **excusée** ici, avec une raison
  écrite. Une citation dans une phrase d'aide ne compte pas : elle ne fait
  rien, elle parle ;
* une excuse périmée est un mensonge : si la page appelle une route qu'on
  excuse encore, le contrôle refuse ;
* une excuse sans objet est un mensonge aussi : excuser une route que le
  serveur ne sert plus, c'est décrire un monde disparu.

La liste des routes servies est lue dans le générateur de la fonction Vercel
(`outils/generer-fonctions-api.py`, table `ROUTES`) : c'est lui qui fait foi,
la fonction déployée en découle.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "outils"))

from chargement_module import charger_module  # noqa: E402  (outil du dépôt)

from simulateur.interface import HTML_PAGE  # noqa: E402

#: Les routes servies, dans l'ordre du générateur.
ROUTES = tuple(charger_module("generateur_fonctions_api",
                              RACINE / "outils" / "generer-fonctions-api.py").ROUTES)

#: Deux façons de servir une route au lecteur : l'appeler, ou la lui confier
#: par un lien. Un appel est un `fetch('/api/…')` (ou avec des guillemets, ou
#: en gabarit). Un lien est un `href="/api/…"` construit par la page — c'est
#: ainsi que les fiches de droit positif s'ouvrent, sans requête de la page.
#: Une phrase d'aide qui cite `<code>/api/…</code>` ne compte pas : elle ne
#: fait rien, elle parle — c'est justement la confusion que ce contrôle refuse.
MOTIF_APPEL = re.compile(r"fetch\(\s*[`'\"]/api/([a-z_]+)|href=[`'\"]/api/([a-z_]+)")

#: Les routes servies que la page n'appelle pas, et pourquoi. Chaque raison
#: nomme ce qui remplace la route, ou qui l'exerce à sa place : « pas
#: d'écran » n'est pas une raison, c'est une description du problème.
ROUTES_SANS_APPEL: dict[str, str] = {
    "bulles": (
        "la page demande une bulle à la fois (`/api/bulle?levier=…`) : le catalogue complet "
        "coûte plusieurs secondes au premier appel, et l'interface n'en montre qu'une à la fois. "
        "La route reste entière pour l'API publique et pour la veille en ligne."
    ),
    "instances": (
        "vue courte de `/api/dynamiques`, que la page charge en entier : les 26 autorités y "
        "figurent, avec leurs fondements, leurs effets et leurs boucles de contrôle."
    ),
    "presets": (
        "les 16 préréglages doctrinaux arrivent avec `/api/catalogue` (`parametres.presets`), "
        "que la page charge au démarrage : le parcours vérifie qu'elle en affiche bien 16."
    ),
    "scenarios": (
        "le catalogue des scénarios est embarqué dans la page à sa construction "
        "(`outils/generer-index-simulateur.py`, jeton `===SCENARIOS_JSON===`) : la page ne "
        "redemande pas au serveur ce qu'elle porte déjà."
    ),
    "export": (
        "les exports JSON et CSV sont fabriqués dans le navigateur à partir de la simulation "
        "déjà reçue, sans aller-retour : un téléchargement ne redemande pas au serveur ce qu'il "
        "vient de calculer. La route reste pour les clients de l'API."
    ),
    "proxy": (
        "la page appelle `/api/proxy` avec l'adresse que le serveur lui donne (`proxy_url`, "
        "dans `/api/contexte`) : le nom de la route ne peut donc pas apparaître dans le source "
        "de la page, et son absence y est normale."
    ),
}

#: En deçà, ce n'est plus une raison : c'est un mot.
LONGUEUR_MINIMALE_D_UNE_RAISON = 60


def routes_servies_par_la_page(page: str = HTML_PAGE) -> set[str]:
    """Les routes que la page met en œuvre : appelées, ou données en lien."""
    return {groupe for trouve in MOTIF_APPEL.findall(page) for groupe in trouve if groupe}


class TestCouvertureDesRoutes(unittest.TestCase):
    """Chaque route servie a une réponse : appelée, ou excusée par écrit."""

    def setUp(self):
        self.servies = set(ROUTES)
        self.appelees = routes_servies_par_la_page()
        self.excusees = set(ROUTES_SANS_APPEL)

    # ── La comptabilité ───────────────────────────────────────────────────
    def test_toute_route_servie_est_appelee_ou_excusee(self):
        """Le contrôle central : pas de trou dans la couverture."""
        sans_reponse = sorted(self.servies - self.appelees - self.excusees)
        self.assertEqual(
            sans_reponse, [],
            "routes servies que la page n'appelle pas et que personne n'excuse : "
            + ", ".join(sans_reponse),
        )

    def test_aucune_route_servie_n_est_a_la_fois_appelee_et_excusee(self):
        """Une excuse qui survit à l'appel est une excuse périmée."""
        perimees = sorted(self.servies & self.appelees & self.excusees)
        self.assertEqual(
            perimees, [],
            "routes excusées alors que la page les appelle : " + ", ".join(perimees),
        )

    def test_aucune_excuse_ne_porte_sur_une_route_disparue(self):
        """Excuser une route que le serveur ne sert plus décrit un monde disparu."""
        fantomes = sorted(self.excusees - self.servies)
        self.assertEqual(
            fantomes, [],
            "routes excusées que le serveur ne sert pas : " + ", ".join(fantomes),
        )

    def test_la_page_n_appelle_aucune_route_qui_n_existe_pas(self):
        """Dans l'autre sens : un appel sans route ferait un 404 silencieux."""
        inconnues = sorted(self.appelees - self.servies)
        self.assertEqual(
            inconnues, [],
            "routes appelées par la page et non servies : " + ", ".join(inconnues),
        )

    def test_la_comptabilite_couvre_toutes_les_routes(self):
        """Les deux ensembles, mis bout à bout, font exactement la liste servie."""
        self.assertEqual(len(self.appelees & self.excusees), 0)
        self.assertEqual(
            len(self.appelees) + len(self.excusees), len(self.servies),
            f"{len(self.appelees)} appelée(s) + {len(self.excusees)} excusée(s) "
            f"pour {len(self.servies)} servie(s)",
        )

    # ── La qualité des excuses ────────────────────────────────────────────
    def test_chaque_excuse_est_une_raison_ecrite(self):
        """Une excuse tient une phrase, pas un mot."""
        courtes = sorted(
            route for route, raison in ROUTES_SANS_APPEL.items()
            if len(raison.strip()) < LONGUEUR_MINIMALE_D_UNE_RAISON
        )
        self.assertEqual(courtes, [], "excuses trop courtes pour être des raisons : "
                                      + ", ".join(courtes))

    def test_chaque_excuse_nomme_ce_qui_remplace_la_route(self):
        """Une raison dit qui fait le travail à la place — pas seulement « inutile »."""
        #: Ce qu'une raison doit nommer : une route, un fichier, un outil, un
        #: geste de la page. Sans cela, l'excuse n'apprend rien.
        marques = ("/api/", "`", ".py", "navigateur", "charge", "arrive", "exercée")
        muettes = sorted(
            route for route, raison in ROUTES_SANS_APPEL.items()
            if not any(marque in raison for marque in marques)
        )
        self.assertEqual(muettes, [], "excuses qui ne nomment rien : " + ", ".join(muettes))

    # ── L'excuse du relais, vérifiable ────────────────────────────────────
    def test_l_excuse_du_relais_nomme_une_adresse_servie(self):
        """`/api/proxy` n'est pas citée : son adresse vient du serveur.

        L'excuse serait un tour de passe-passe si personne ne fournissait cette
        adresse. Elle est donc vérifiée là où elle se fabrique.
        """
        source = (RACINE / "simulateur" / "donnees_live.py").read_text(encoding="utf-8")
        self.assertIn('"proxy_url": f"/api/proxy?indicateur=', source)
        self.assertIn("proxy_url", HTML_PAGE)

    def test_la_citation_d_une_route_ne_passe_pas_pour_un_usage(self):
        """Le motif ne confond pas une phrase d'aide avec ce que la page fait.

        Sans cela, la page pourrait citer `<code>/api/panneau</code>` et se
        croire couverte : c'est le piège que ce contrôle existe pour fermer.
        """
        citation = "Voir <code>/api/scenarios</code> pour le détail."
        self.assertEqual(routes_servies_par_la_page(citation), set())
        self.assertEqual(
            routes_servies_par_la_page("await fetch('/api/scenarios');"), {"scenarios"})
        self.assertEqual(
            routes_servies_par_la_page("await fetch(`/api/bulle?levier=x`);"), {"bulle"})
        self.assertEqual(
            routes_servies_par_la_page('await fetch("/api/donnees", {method: "POST"});'),
            {"donnees"})

    def test_un_lien_compte_comme_un_usage_de_la_route(self):
        """Une fiche ouverte dans un nouvel onglet n'est pas un appel, mais elle sert.

        `/api/constitution` ne se charge pas toute seule : la page construit un
        lien que le lecteur suit. La compter comme inutilisée enverrait
        chercher une excuse pour une route qui travaille tous les jours.
        """
        lien = ('return "Article 49" + "<a href="/api/constitution?article=49">" ')
        self.assertEqual(routes_servies_par_la_page(lien), {"constitution"})
        self.assertIn("constitution", routes_servies_par_la_page())

    def test_les_routes_servies_viennent_du_generateur(self):
        """La liste lue est celle qui engendre la fonction déployée."""
        self.assertIn("catalogue", ROUTES)
        self.assertIn("contrepouvoirs", ROUTES)
        self.assertIn("dynamiques", ROUTES)
        self.assertEqual(len(ROUTES), len(set(ROUTES)), "route servie en double")


if __name__ == "__main__":
    unittest.main()
