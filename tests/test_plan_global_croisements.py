"""Garantie « sans trou » du dépôt : croisements, garde-fous et fraîcheur des documents.

Ce fichier ne teste pas un calcul isolé : il teste l'absence d'angle mort entre les registres.
Chaque test correspond à une clause de `docs/18_PLAN_GLOBAL_BRAINSTORMING_ET_SANS_TROU.md`,
de sorte qu'une promesse écrite dans la documentation soit tenue par du code — et non l'inverse.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from simulateur.gouvernance_contrepouvoir import MECANISMES, VERROUS  # noqa: E402
from simulateur.instances_et_dynamiques import FENTES, INSTANCES, STRATEGIES, TRAJETS  # noqa: E402
from simulateur.nuances_institutionnelles import (  # noqa: E402
    APPORTS,
    INDICES,
    NIVEAUX,
    REGLAGES,
    REGLAGES_SANS_GEOMETRIE,
    REPERTOIRES,
    SEUILS_INSSENSIBLES,
    UNITES_LISIBLES,
    VERROUS_HORS_REGLAGE,
    VERROUS_REGLAGES,
    coherence_nuances,
    croisement_pour,
    croisements,
    delais_ajustes,
    reglages_catalogue,
    reglages_par_connaissance,
    seuils_ajustes,
    synthese_pour_api,
)
from simulateur.parametres import FAMILLES, LEVIERS, PRESETS  # noqa: E402
from simulateur.reglements_lois import REGISTRE_LEGAL  # noqa: E402


def _ouvert(cle: str) -> float:
    """La valeur « réglage ouvert au maximum » : les interrupteurs n'ont pas de borne haute."""
    return LEVIERS[cle].maximum or 1.0

#: Les sept réglages qui fermaient les derniers registres inatteignables (docs/18, section 4).
NOUVEAUX_REGLAGES = {
    "reglage_procedure_acceleree_encadree": ("verrou", "procedure_acceleree_delai"),
    "reglage_nouvelle_deliberation_supprimee": ("verrou", "promulgation_nouvelle_deliberation"),
    "reglage_commission_enquete_droit_de_bloc": ("verrou", "commission_enquete_signature"),
    "reglage_haute_cour_non_parlementaire": ("verrou", "haute_cour_assemblees"),
    "reglage_cee_consultation_prealable": ("verrou", "lois_programmation_saisine_cee"),
    "reglage_defenseur_saisine_directe": ("instance", "defenseur_des_droits"),
    "reglage_declassification_legislative": ("verrou", "irrecevabilite_competence_delai"),
}


class TestCroisementsSansTrou(unittest.TestCase):
    """Clause 2 : toute pièce de tout registre est joignable, ou explicitement expliquée."""

    @classmethod
    def setUpClass(cls):
        cls.coherence = coherence_nuances()
        cls.croisement = croisements()

    def test_aucune_connaissance_inaccessible(self):
        self.assertEqual(self.coherence["connaissances_inaccessibles"], [],
                         f"trou de croisement : {self.coherence['connaissances_inaccessibles']}")

    def test_partition_stricte_des_verrous(self):
        reglables = set(self.coherence["verrous_reglables"])
        expliques = set(self.coherence["verrous_expliques_hors_reglage"])
        self.assertFalse(reglables & expliques, "un verrou ne peut pas être réglable et hors réglage")
        self.assertEqual(reglables | expliques, set(VERROUS))
        self.assertEqual(self.coherence["verrous_non_expliques"], [])
        self.assertEqual(self.coherence["verrous_inventes"], [])
        self.assertEqual(self.coherence["verrous_doublement_classes"], [])

    def test_index_inverse_couvre_tout_un_registre(self):
        for categorie, repertoire in REPERTOIRES.items():
            with self.subTest(registre=categorie):
                index = reglages_par_connaissance(categorie)
                self.assertEqual(set(index), set(repertoire))
                ligne = self.coherence["accesibilite_des_connaissances"][categorie]
                self.assertEqual(ligne["total"], len(repertoire))
                self.assertEqual(ligne["avec_reglage"] + len(ligne["sans_reglage"]), len(repertoire))

    def test_fentes_trajets_et_strates_sont_tous_couverts(self):
        self.assertEqual(self.coherence["trajets_sans_reglage"], [])
        self.assertEqual(self.coherence["fentes_inaccessibles_d_un_reglage"], [])
        self.assertEqual(self.coherence["fentes_non_ciblees"], [])
        self.assertEqual(self.coherence["reglages_sans_strate"], [])
        self.assertEqual(self.coherence["strates_couvertes"], [1, 2, 3, 4, 5])

    def test_index_d_article_est_coherent(self):
        self.assertGreaterEqual(len(self.croisement), 90)
        catalogue = set(reglages_catalogue())
        for numero, ligne in self.croisement.items():
            with self.subTest(article=numero):
                self.assertTrue(re.fullmatch(r"\d+(-\d+)*", numero), numero)
                self.assertTrue(ligne["reglages"] or ligne["verrous"] or ligne["fentes"]
                                or ligne["trajets"] or ligne["mecanismes"] or ligne["instances"]
                                or ligne["strategies"],
                                f"l'article {numero} est indexé sans rien rattacher")
                self.assertTrue(set(ligne["reglages"]) <= catalogue)
                for cle in ligne["reglages"]:
                    self.assertIn(numero, {_numero(i) for i in LEVIERS[cle].articles})

    def test_chaque_reglage_rattache_au_moins_un_article(self):
        self.assertEqual(self.coherence["reglages_sans_article"], [])
        self.assertEqual(self.coherence["articles_hors_registre"], [])
        for cle in reglages_catalogue():
            with self.subTest(reglage=cle):
                for identifiant in LEVIERS[cle].articles:
                    if identifiant.startswith("CONST_ART_"):
                        self.assertIn(identifiant, REGISTRE_LEGAL)

    def test_croisement_pour_accepte_toutes_les_notations(self):
        attendu = croisement_pour("49")
        for notation in ("article 49", "CONST_ART_49", "art. 49.3", "49 alinéa 3"):
            with self.subTest(notation=notation):
                self.assertEqual(croisement_pour(notation)["reglages"], attendu["reglages"])
        vu = croisement_pour("72-1")
        self.assertTrue(vu["reglages"])
        self.assertEqual(set(vu), {
            "article", "identifiant_registre", "present_dans_le_registre", "reglages", "verrous",
            "mecanismes", "instances", "fentes", "trajets", "strategies", "seuils", "compte",
            "fiches",
        })
        self.assertEqual(vu["compte"]["reglages"], len(vu["reglages"]))
        # un article sans réglage n'est pas une erreur : c'est un article du droit commun
        vide = croisement_pour("zzz")
        self.assertEqual(vide["reglages"], [])
        self.assertFalse(vide["present_dans_le_registre"])

    def test_reglages_touchent_des_connaissances_reelles(self):
        for cle, reglage in REGLAGES.items():
            for type_cible, identifiant in reglage["cibles"]:
                with self.subTest(reglage=cle, cible=f"{type_cible}:{identifiant}"):
                    if type_cible in REPERTOIRES:
                        self.assertIn(identifiant, REPERTOIRES[type_cible])
                    elif type_cible == "index":
                        self.assertIn(identifiant, INDICES)
                    elif type_cible == "etape":
                        trajet, _, etape = identifiant.partition(":")
                        self.assertIn(trajet, TRAJETS)
                        self.assertIn(etape, {e.cle for e in TRAJETS[trajet].etapes})
                    elif type_cible == "fenetre":
                        from simulateur.nuances_institutionnelles import FENETRES_REGLABLES
                        self.assertIn(identifiant, FENETRES_REGLABLES)
                    else:
                        self.assertEqual(type_cible, "seuil_derive",
                                         f"type de cible inconnu : {type_cible}")


def _numero(identifiant: str) -> str:
    trouve = re.search(r"(\d+(?:-\d+)?)", str(identifiant).replace("_", "-"))
    return trouve.group(1) if trouve else str(identifiant)


class TestGeometrieDesReglages(unittest.TestCase):
    """Clause 1 : les nombres viennent du droit, et zéro veut dire le droit."""

    def test_catalogues_en_miroir(self):
        reglages = {cle for cle in LEVIERS if cle.startswith("reglage_")}
        self.assertEqual(set(REGLAGES), reglages)
        self.assertFalse(set(APPORTS) - reglages, "un apport sans réglage est un indice fantôme")
        # Presque tous les réglages doivent peser sur un indice : ceux qui n'en touchent
        # aucun sont une exception, pas la norme.
        couverts = {cle for cle, apports in APPORTS.items() if apports}
        self.assertGreaterEqual(len(couverts & reglages), len(reglages) - 2)
        self.assertGreaterEqual(len(reglages), 55)

    def test_tag_de_niveau_sur_chaque_reglage(self):
        for cle in reglages_catalogue():
            with self.subTest(reglage=cle):
                self.assertEqual(LEVIERS[cle].tags,
                                 ("nuance_institutionnelle", REGLAGES[cle]["niveau"]))
                self.assertIn(REGLAGES[cle]["niveau"], NIVEAUX)

    def test_quatre_valeurs_par_defaut_sont_le_droit(self):
        self.assertEqual(self._ecarts(), dict.fromkeys(seuils_ajustes(), 0))
        from simulateur.gouvernance_contrepouvoir import seuil as seuil_d_droit
        for cle, ligne in seuils_ajustes().items():
            with self.subTest(seuil=cle):
                if cle in VERROUS:
                    self.assertEqual(ligne["statu_quo"], int(seuil_d_droit(cle)),
                                     "le statut quo doit être la valeur du droit, pas un chiffre recopié")
                self.assertTrue(ligne["unite"], f"aucune unité lisible pour {cle}")
                self.assertTrue(ligne["nom"].strip() and ligne["article"])

    def test_delais_statu_quo_et_fenetre(self):
        delais = delais_ajustes()
        self.assertEqual([ligne["cle"] for ligne in delais["trajets"]], list(TRAJETS))
        self.assertEqual(delais["fenetre_residuelle_statu_quo"],
                         delais["fenetre_residuelle_reglee"])
        for ligne in delais["trajets"]:
            with self.subTest(trajet=ligne["cle"]):
                self.assertEqual(ligne["jours_de_rigueur_regles"], ligne["jours_de_rigueur_statu_quo"])
                self.assertEqual(ligne["tenable_dans_la_fenetre"],
                                 ligne["jours_de_rigueur_statu_quo"]
                                 <= delais["fenetre_residuelle_statu_quo"])
        self.assertTrue(delais["jours_coherents_avec_oscillation"])

    def test_reglable_doit_deplacer_quand_on_ouvre(self):
        """Un verrou annoncé réglable bouge, ou dit pourquoi il ne bouge pas."""
        for cle_verrou in VERROUS_REGLAGES:
            declarants = sorted(cle for cle, reglage in REGLAGES.items()
                                for type_cible, identifiant in reglage["cibles"]
                                if type_cible == "verrou" and identifiant == cle_verrou)
            with self.subTest(verrou=cle_verrou):
                self.assertTrue(declarants, f"{cle_verrou} est annoncé réglable sans réglage")
                ajuste = seuils_ajustes({cle: _ouvert(cle) for cle in declarants})[cle_verrou]
                self.assertTrue(set(ajuste["reglages_appliques"]) <= set(declarants),
                                "un seuil reconnaît un réglage qui ne le déclare pas")
                self.assertEqual(sorted(ajuste["reglages_appliques"]), sorted(declarants),
                                 "tous les déclarants doivent être appliqués, sinon la règle est muette")
                if cle_verrou in SEUILS_INSSENSIBLES:
                    self.assertGreaterEqual(len(SEUILS_INSSENSIBLES[cle_verrou]), 40,
                                            "un verrou insensible sans raison écrite est un trou")
                else:
                    self.assertNotEqual(ajuste["ecart"], 0,
                                        f"{cle_verrou} ne bouge pas quand on ouvre {declarants} "
                                        "et n'est déclaré nulle part")
        coherence = coherence_nuances()
        self.assertEqual(coherence["seuils_insensibles_perimes"], [])
        self.assertEqual(coherence["verrous_reglables_sans_explication"], [])

    def test_indices_ne_saturent_qu_en_le_disant(self):
        indices = synthese_pour_api()["indices"]
        for cle, ligne in indices.items():
            with self.subTest(indice=cle):
                self.assertTrue(0.0 <= ligne["valeur"] <= 100.0)
                if ligne["borne_appliquee"]:
                    self.assertIn(ligne["valeur"], (0.0, 100.0))

    @staticmethod
    def _ecarts():
        return {cle: ligne["ecart"] for cle, ligne in seuils_ajustes().items()}


class TestExemptionsEtLimites(unittest.TestCase):
    """Clause 5 : une limite est écrite, datée, et vérifiée comme périmée si elle l'est."""

    def test_raisons_des_verrous_hors_reglage(self):
        self.assertEqual(len(VERROUS_HORS_REGLAGE) + len(VERROUS_REGLAGES), len(VERROUS))
        for cle, raison in VERROUS_HORS_REGLAGE.items():
            with self.subTest(verrou=cle):
                self.assertGreaterEqual(len(raison), 40, "une exemption d'une ligne ne justifie rien")
                self.assertNotIn(cle, VERROUS_REGLAGES)

    def test_exemptions_de_geometrie_sont_motivees(self):
        self.assertEqual(coherence_nuances()["exemptions_vides"], [])
        self.assertEqual(coherence_nuances()["exemptions_perimees"], [])
        for cle, raison in REGLAGES_SANS_GEOMETRIE.items():
            with self.subTest(reglage=cle):
                self.assertIn(cle, REGLAGES)
                self.assertGreaterEqual(len(raison), 40)

    def test_limites_affichees_avec_la_synthese(self):
        limites = synthese_pour_api()["limites"]
        self.assertGreaterEqual(len(limites), 3)
        self.assertTrue(any("50" in ligne and "état du droit" in ligne for ligne in limites))


class TestReglagesAjoutes(unittest.TestCase):
    """Section 4 de docs/18 : les sept réglages qui fermaient les derniers trous."""

    def test_chaque_nouveau_reglage_ferme_ce_qu_il_annonce(self):
        for cle, (type_cible, identifiant) in NOUVEAUX_REGLAGES.items():
            with self.subTest(reglage=cle):
                self.assertIn(cle, REGLAGES, f"{cle} manque au catalogue")
                self.assertIn(cle, LEVIERS)
                cibles: dict = {}
                for categorie, name in REGLAGES[cle]["cibles"]:
                    cibles.setdefault(categorie, []).append(name)
                if type_cible == "verrou":
                    self.assertIn(identifiant, cibles.get("verrou", []),
                                  f"{cle} n'annonce pas viser le verrou {identifiant}")
                    ajuste = seuils_ajustes({cle: _ouvert(cle)})[identifiant]
                    self.assertNotEqual(ajuste["ecart"], 0,
                                        f"{cle} ouvert au maximum ne déplace pas {identifiant}")
                    self.assertIn(cle, ajuste["reglages_appliques"])
                else:
                    self.assertIn(cle, reglages_par_connaissance(type_cible)[identifiant])

    def test_les_registres_fermes_le_restant_par_article(self):
        attendus = {
            "instance": ["office_et_missions_parlementaires",
                         "conseil_economique_social_et_environnemental",
                         "defenseur_des_droits", "haute_cour"],
            "mecanisme": ["haute_cour", "cjr", "commission_enquete"],
            "strategie": ["procedure_acceleree", "rectification_de_calendrier",
                          "resolution_enquete", "defossilisation"],
        }
        for categorie, cles in attendus.items():
            index = reglages_par_connaissance(categorie)
            for cle in cles:
                with self.subTest(registre=categorie, cle=cle):
                    self.assertTrue(index[cle], f"aucun réglage ne joint {categorie}:{cle}")

    def test_l_unite_lisible_existe_pour_les_nouveaux_seuils(self):
        for cle_verrou in ("procedure_acceleree_delai", "promulgation_nouvelle_deliberation",
                           "commission_enquete_signature", "haute_cour_assemblees",
                           "haute_cour_destitution", "lois_programmation_saisine_cee",
                           "irrecevabilite_competence_delai"):
            with self.subTest(verrou=cle_verrou):
                self.assertIn(cle_verrou, UNITES_LISIBLES)
                self.assertTrue(UNITES_LISIBLES[cle_verrou].strip())


class TestFraicheurDesDocuments(unittest.TestCase):
    """Clause 3 : ce qui est écrit est produit. Un document figé est un document faux."""

    @classmethod
    def setUpClass(cls):
        cls.scripts = ["outils/generer-doc-nuances.py", "outils/generer-page-verification.py",
                       "outils/generer-index-simulateur.py", "outils/generer-fonctions-api.py",
                       "outils/generer-objections.py", "outils/generer-registre-engagements.py",
                       # Ce que lisent les robots : les fichiers de la racine et les
                       # images publiées doivent correspondre au module et au catalogue.
                       "outils/generer-surface-publique.py", "outils/apercu_social.py"]

    def test_les_generateurs_ne_prennent_pas_de_retard(self):
        for script in self.scripts:
            with self.subTest(generateur=script):
                proc = subprocess.run(
                    [sys.executable, script, "--verifier"], cwd=str(RACINE),
                    capture_output=True, text=True, timeout=600,
                )
                self.assertEqual(proc.returncode, 0,
                                 f"{script} --verifier : {proc.stdout}{proc.stderr}")

    def test_docs_17_porte_le_nombre_de_reglages_reel(self):
        page = (RACINE / "docs" / "17_NUANCES_INSTITUTIONNELLES_ET_REGLAGES.md").read_text("utf-8")
        lignes = re.findall(r"^\| `(reglage_[a-z0-9_]+)`", page, re.M)
        self.assertEqual(sorted(set(lignes)), sorted(reglages_catalogue()))
        self.assertIn(f"Les {len(reglages_catalogue())} réglages", page)
        self.assertIn(f"**{len(LEVIERS)} leviers**", page)
        self.assertIn(f"{len(PRESETS)} préréglages", page)

    def test_compteurs_des_documents_d_etat(self):
        """Délègue au garde-fou général des compteurs (`outils/verifier-compteurs.py`).

        Les motifs périmés connus sont cités ici pour mémoire : le contrôle qui les
        cherche couvre désormais leviers, réglages, préréglages, familles, domaines,
        indicateurs, garde-fous, scénarios, échelons et routes — et refuse qu'un
        document vivant annonce le compte de ses tests.
        """
        import importlib.util

        chemin = RACINE / "outils" / "verifier-compteurs.py"
        spec = importlib.util.spec_from_file_location("verifier_compteurs", chemin)
        module = importlib.util.module_from_spec(spec)
        sys.modules["verifier_compteurs"] = module
        spec.loader.exec_module(module)
        anomalies = module.verifier(RACINE)
        self.assertEqual(anomalies, [],
                         "compteur périmé — régénérer la page ou reprendre le chiffre : "
                         + "; ".join(anomalies))

    def test_tout_document_est_indexe(self):
        index = (RACINE / "docs" / "README.md").read_text(encoding="utf-8")
        orphelins = [chemin.name for chemin in sorted((RACINE / "docs").glob("*.md"))
                     if chemin.name != "README.md" and f"({chemin.name})" not in index]
        self.assertEqual(orphelins, [], "documents sans porte d'entrée : " + ", ".join(orphelins))

    def test_tout_module_simulateur_est_cite(self):
        corpus = "\n".join(chemin.read_text(encoding="utf-8")
                           for chemin in list((RACINE / "docs").glob("*.md"))
                           + [(RACINE / "README.md"), (RACINE / "NOTE_POUR_CLAUDE.md")])
        orphelins = [chemin.stem for chemin in sorted((RACINE / "simulateur").glob("*.py"))
                     if chemin.stem != "__init__" and chemin.stem not in corpus]
        self.assertEqual(orphelins, [], "modules que personne ne documente : " + ", ".join(orphelins))

    def test_docs_18_annonce_les_chiffres_verifies(self):
        page = (RACINE / "docs" / "18_PLAN_GLOBAL_BRAINSTORMING_ET_SANS_TROU.md").read_text("utf-8")
        for annonce in (f"**{len(LEVIERS)}**", f"**{len(reglages_catalogue())}**",
                        f"**{len(PRESETS)}**", f"**{len(VERROUS)}**", f"**{len(INSTANCES)}**",
                        f"**{len(MECANISMES)}**", f"**{len(STRATEGIES)}**", f"**{len(FENTES)}**",
                        f"**{len(TRAJETS)}**"):
            with self.subTest(annonce=annonce):
                self.assertIn(annonce, page)
        for cle in NOUVEAUX_REGLAGES:
            self.assertIn(cle, page, f"{cle} ajouté au code mais absent du plan global")


class TestPariteDesRoutes(unittest.TestCase):
    """Clause 4 : ce que la docstring promet existe, et ce qui existe est promis."""

    def test_routes_du_dashboard_et_fonctions_vercel(self):
        source = (RACINE / "simulateur" / "dashboard.py").read_text(encoding="utf-8")
        do_get = source[source.index("    def do_GET"):source.index("    def do_POST")]
        routes = sorted(set(re.findall(r'chemin == "(/api/[a-z_]+)"', do_get))
                        | set(re.findall(r'chemin == "(/api/[a-z_]+)"',
                                          source[source.index("    def do_POST"):])))
        generee = (RACINE / "outils" / "generer-fonctions-api.py").read_text(encoding="utf-8")
        registre = re.search(r"ROUTES: [\w.]+\[str, \.\.\.\] = \((.*?)\n\)", generee, re.S)
        cibles = sorted(f"/api/{nom}" for nom in re.findall(r'"([a-z_]+)"', registre.group(1)))
        self.assertEqual(len(routes), len(cibles),
                         f"routes servies {routes} contre registre {cibles}")
        for route in cibles:
            with self.subTest(route=route):
                self.assertIn(route, routes, f"{route} est générée mais pas servie localement")
        for route in routes:
            with self.subTest(route=route):
                self.assertIn(route, source[:source.index("    def do_GET")],
                              f"{route} est servie mais absente de la docstring du module")

    def test_une_seule_fonction_vercel_par_deploiement(self):
        """Chaque `.py` de `api/` devient une fonction ; l'offre Hobby plafonne à douze.

        La liste des routes du moteur est donc servie par un pont unique, et `api/`
        ne contient que ce pont plus les fonctions propres au site.
        """
        outil = (RACINE / "outils" / "generer-fonctions-api.py").read_text(encoding="utf-8")
        registre = re.search(r"ROUTES: [\w.]+\[str, \.\.\.\] = \((.*?)\n\)", outil, re.S)
        cibles = sorted(nom for nom in re.findall(r'"([a-z_]+)"', registre.group(1)))
        site = sorted(nom for nom in re.findall(
            r'"([a-z-]+)"',
            re.search(r"FONCTIONS_DU_SITE: [\w.]+\[str, \.\.\.\] = \((.*?)\)", outil, re.S).group(1)))
        dossiers = sorted(chemin.stem for chemin in (RACINE / "api").glob("*.py"))
        self.assertEqual(dossiers, sorted(["[...path]", *site]),
                         "api/ contient une fonction par route : revenir au pont unique")
        self.assertLessEqual(len(dossiers), 12, "encore sous le plafond Vercel")
        pont = (RACINE / "api" / "[...path].py").read_text(encoding="utf-8")
        for route in cibles:
            with self.subTest(route=route):
                self.assertIn(f'"{route}"', pont,
                              f"la route {route} n'est pas servie par la fonction unique")

    def test_presets_sont_tous_servis_et_cites(self):
        self.assertGreaterEqual(len(PRESETS), 16)
        self.assertEqual(len(FAMILLES), 14)
        corpus = "\n".join(chemin.read_text(encoding="utf-8")
                           for chemin in sorted((RACINE / "docs").glob("*.md")))
        for cle in PRESETS:
            with self.subTest(preset=cle):
                self.assertIn(cle, corpus,
                              f"le préréglage {cle} n'est décrit dans aucun document")
        for cle in PRESETS["assemblees_souveraines"]["parametres"]:
            self.assertTrue(cle.startswith("reglage_"),
                            "le préréglage institutionnel ne doit déplacer que des réglages")


if __name__ == "__main__":
    unittest.main(verbosity=2)
