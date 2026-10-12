"""La Constitution fichee article par article : exhaustivite, cohérence, passerelles.

Ces tests sont le contrat du module `simulateur/constitution_analysee.py` :

* le registre couvre exactement les articles en vigueur du texte officiel ;
* une fiche ne peut s'appuyer que sur des donnees verifiables : strate du registre,
  levier reel du catalogue, article existant ;
* la greffe dans `REGISTRE_LEGAL` n'ecrase jamais une entree deja verifiee ;
* rien n'est presente comme un avis juridique : la source et sa date voyagent avec
  chaque fiche.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from simulateur.constitution_analysee import (  # noqa: E402
    ABROGES,
    ARTICLES,
    Blocs,
    DATE_CONSULTATION,
    FONCTIONS,
    NUMEROS_ABROGES,
    NUMEROS_ATTENDUS,
    ORDRE_ARTICLES,
    STRATES,
    VERSION_TEXTE,
    article,
    articles_pour_mecanisme,
    articles_pour_strate,
    chaine,
    couverture,
    opportunites_pour,
    par_bloc,
    par_fonction,
    rechercher,
    resume_console,
    synthese_pour_api,
    verrous_pour,
    vers_registre_legal,
)
from simulateur.parametres import LEVIERS  # noqa: E402
from simulateur.reglements_lois import STRATES_VALIDES  # noqa: E402

NUMERIQUE = re.compile(r"^\d+(-\d+)?$")


class TestExhaustivite(unittest.TestCase):
    def test_tous_les_articles_en_vigueur_sont_fiches(self):
        etat = couverture()
        self.assertEqual(etat["manquants"], [], "des articles du texte officiel n'ont pas de fiche")
        self.assertEqual(etat["inattendus"], [], "des fiches ne correspondent a aucun article du texte")
        self.assertTrue(etat["complet"])

    def test_comptage_officiel(self):
        # 1 a 89 avec les « bis » : le compte est verifie sur le texte integre du
        # Conseil constitutionnel, pas sur la memoire du redacteur.
        self.assertEqual(len(ORDRE_ARTICLES), 109)
        self.assertEqual(len(NUMEROS_ATTENDUS), 109)
        self.assertEqual(len(ABROGES), 10)

    def test_abroges_ne_sont_pas_en_vigueur(self):
        for entree in ABROGES:
            with self.subTest(article=entree["numero"]):
                self.assertIn(entree["numero"], NUMEROS_ABROGES)
                self.assertNotIn(entree["numero"], ARTICLES)
                self.assertIn("abroge_par", entree)
                self.assertTrue(entree["note"])

    def test_un_seul_exemplaire_par_article(self):
        self.assertEqual(len(set(ARTICLES)), len(ORDRE_ARTICLES))

    def test_trio_titres_et_numeros_coherents(self):
        for numero in ORDRE_ARTICLES:
            fiche = ARTICLES[numero]
            with self.subTest(article=numero):
                bloc_cle = fiche.bloc.split(" —")[0].replace("Titre ", "").strip()
                self.assertIn(bloc_cle, Blocs, "titre inconnu de la table des titres")


class TestContratsDeDonnees(unittest.TestCase):
    def test_strates_dans_la_liste_ferquee(self):
        for numero in ORDRE_ARTICLES:
            for strate in ARTICLES[numero].strates:
                with self.subTest(article=numero, strate=strate):
                    self.assertIn(strate, STRATES)
                    self.assertIn(strate, STRATES_VALIDES)

    def test_fonctions_dans_la_liste_declaree(self):
        for numero in ORDRE_ARTICLES:
            with self.subTest(article=numero):
                self.assertIn(ARTICLES[numero].fonction, FONCTIONS)

    def test_leviers_cites_existent_dans_le_catalogue(self):
        orphelins = {
            numero: [l for l in ARTICLES[numero].leviers if l not in LEVIERS]
            for numero in ORDRE_ARTICLES
            if any(l not in LEVIERS for l in ARTICLES[numero].leviers)
        }
        self.assertEqual(orphelins, {}, "une fiche ne peut relier un article qu'a un levier chiffre")

    def test_pistes_ne_sont_pas_des_leviers(self):
        for numero in ORDRE_ARTICLES:
            for piste in ARTICLES[numero].pistes:
                with self.subTest(article=numero, piste=piste):
                    self.assertNotIn(piste, LEVIERS, "une piste devenue levier doit etre promue")

    def test_croisements_pointent_vers_un_article_ou_un_texte_du_bloc(self):
        for numero in ORDRE_ARTICLES:
            for lien in ARTICLES[numero].croisements:
                with self.subTest(article=numero, lien=lien):
                    if NUMERIQUE.match(lien):
                        self.assertIn(lien, ARTICLES, "croisement vers un article inexistant")
                    else:
                        # references au reste du bloc (DDHC, preambule) : admises,
                        # mais nommees pour qu'on ne les confonde pas avec un numero.
                        self.assertRegex(lien, r"^(DDHC|PREAMBULE|CHARTE)")

    def test_chaque_fiche_a_le_quatuor_obligatoire(self):
        for numero in ORDRE_ARTICLES:
            fiche = ARTICLES[numero]
            bilan = fiche.bilan()
            with self.subTest(article=numero):
                self.assertGreaterEqual(bilan["opportunites"], 1)
                self.assertGreaterEqual(bilan["contraintes"], 1)
                self.assertGreaterEqual(bilan["contre_pouvoirs"], 1)
                self.assertGreaterEqual(bilan["regles_chiffrees"], 1)
                self.assertGreaterEqual(bilan["croisements"], 1)

    def test_densite_de_cloture(self):
        etat = couverture()
        for champ in ("avec_opportunites", "avec_contraintes", "avec_contre_pouvoirs",
                      "avec_regles_chiffrees", "avec_croisements", "avec_mecanismes"):
            with self.subTest(champ=champ):
                self.assertEqual(etat["densite"][champ], len(ORDRE_ARTICLES))

    def test_la_source_voyage_avec_chaque_fiche(self):
        for numero in ORDRE_ARTICLES:
            donnees = ARTICLES[numero].en_dict()
            with self.subTest(article=numero):
                self.assertTrue(donnees["source"].startswith("https://"))
                self.assertEqual(donnees["consulte_le"], DATE_CONSULTATION)
                self.assertEqual(donnees["version"], VERSION_TEXTE)
                self.assertIn("Article ", donnees["identification"])


class TestRequetes(unittest.TestCase):
    def test_article_accepte_les_formes_redactionnelles(self):
        for forme in ("49", "49 al. 3", "Article 49", "art. 49", " 89 "):
            with self.subTest(forme=forme):
                self.assertIsNotNone(article(forme))
        self.assertIsNone(article("91"))
        self.assertIsNone(article(""))

    def test_par_bloc_et_par_fonction(self):
        self.assertEqual(len(par_bloc("V")), 26)
        self.assertEqual([a.numero for a in par_bloc("Titre XII")],
                         ["72", "72-1", "72-2", "72-3", "72-4", "73", "74", "74-1", "75", "75-1"])
        self.assertEqual([a.numero for a in par_bloc("XI bis")], ["71-1"])
        self.assertEqual(par_bloc("TITRE INCONNU"), [])
        self.assertEqual([a.numero for a in par_fonction("révision")], ["89"])
        self.assertIn("47", [a.numero for a in par_fonction("budget")])

    def test_recherche_pleine_texte(self):
        résultats = rechercher("trois cinquièmes")
        self.assertTrue(résultats)
        numeros = {r["numero"] for r in résultats}
        self.assertIn("89", numeros)
        for r in résultats:
            self.assertIn(r["champ"], ("titre", "résumé", "règles chiffrées", "opportunités",
                                       "contraintes", "contre-pouvoirs", "autorité",
                                       "mécanismes", "leviers"))
            self.assertIn("extrait", r)
        self.assertEqual(rechercher("a"), [], "un terme trop court noie la recherche")

    def test_chaine_enveloppe_les_croisements(self):
        enveloppe = chaine(["49"])
        self.assertEqual(enveloppe[0]["numero"], "49")
        self.assertEqual(enveloppe[0]["distance"], 0)
        a_portee = {e["numero"] for e in enveloppe}
        # Voisins reels de l'article 49 tels que les fiches les declarent : la
        # responsabilite (50), le budget (47), la navette (45).
        for attendu in ("50", "47", "45"):
            self.assertIn(attendu, a_portee, "une chaine sans ses voisins fait croire qu'un article suffit")
        self.assertEqual([e["numero"] for e in chaine([])], [])

    def test_strates_et_mecanismes(self):
        self.assertIn("72", articles_pour_strate("Local"))
        self.assertIn("34", articles_pour_strate("National"))
        self.assertEqual(articles_pour_mecanisme("motion_censure"), ["20", "49"])
        self.assertEqual(articles_pour_mecanisme("mecanisme_inventе"), [])

    def test_verrous_et_opportunites_pour_un_levier(self):
        for cle in ("reforme_ric", "usage_49_3", "reforme_non_cumul", "convention_citoyenne"):
            verrous = verrous_pour(cle)
            with self.subTest(levier=cle):
                self.assertTrue(verrous, "le levier doit trouver au moins un article qui l'encadre")
                self.assertTrue(all(v["contraintes"] for v in verrous))
            opportunites = opportunites_pour(cle)
            self.assertTrue(all(o["opportunites"] for o in opportunites))
        self.assertEqual(verrous_pour("levier_inexistant"), [])


class TestGreffeRegistre(unittest.TestCase):
    def test_la_greffe_necrase_une_entree_existante(self):
        apports = vers_registre_legal({"CONST_ART_34", "CONST_ART_2"})
        self.assertNotIn("CONST_ART_34", apports)
        self.assertNotIn("CONST_ART_2", apports)
        self.assertEqual(len(apports) + 2, len(ARTICLES))

    def test_toutes_les_entrees_greffe_es_sont_conformes(self):
        apports = vers_registre_legal()
        self.assertTrue(apports)
        for cle, donnees in apports.items():
            with self.subTest(identifiant=cle):
                self.assertRegex(cle, r"^CONST_ART_\d+(_\d+)?$")
                self.assertEqual(set(donnees), {
                    "identifiant", "code_ou_traite", "article", "titre", "texte_integral",
                    "strate_impactee", "effet_simulation",
                })
                self.assertEqual(donnees["code_ou_traite"], "Constitution du 4 octobre 1958")
                self.assertIn(donnees["strate_impactee"], STRATES_VALIDES)
                # Une synthese doit le dire : jamais faire croire a une citation.
                self.assertIn("synthèse de travail", donnees["texte_integral"])

    def test_le_registre_final_porte_les_articles(self):
        from simulateur.reglements_lois import REGISTRE_LEGAL

        for numero in ORDRE_ARTICLES:
            cle = f"CONST_ART_{numero.replace('-', '_')}"
            with self.subTest(article=numero):
                self.assertIn(cle, REGISTRE_LEGAL)


class TestSortiesAPI(unittest.TestCase):
    def test_synthese_serialisable_et_riche(self):
        synthese = synthese_pour_api()
        json.dumps(synthese, ensure_ascii=False)
        self.assertEqual(len(synthese["articles"]), len(ORDRE_ARTICLES))
        self.assertEqual(len(synthese["abroges"]), len(ABROGES))
        self.assertEqual(synthese["couverture"]["articles_en_vigueur"], 109)
        self.assertTrue(synthese["methode"])
        titres = {t["bloc"] for t in synthese["titres"]}
        self.assertIn(Blocs["XVI"], titres)
        for ligne in synthese["fonctions"]:
            self.assertIn(ligne["nom"], FONCTIONS)

    def test_resume_console_anonce_le_comptage(self):
        console = resume_console()
        self.assertIn("109 articles en vigueur", console)
        self.assertIn("10 abrogés", console)
        self.assertIn(DATE_CONSULTATION, console)

    def test_le_module_ne_predit_rien(self):
        # Convention du depot : un modele, pas une prophetie. La fiche doit le dire.
        synthese = synthese_pour_api()
        self.assertIn("prophétie", synthese["methode"])
        self.assertIn("Synthèse de travail", synthese["methode"])


if __name__ == "__main__":
    unittest.main()
