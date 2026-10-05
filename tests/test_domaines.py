"""
tests/test_domaines.py — Tests de la grille des domaines d'action publique.

Chaque domaine agrège des indicateurs concrets, chacun décrit par une formule
linéaire documentée. Ces tests vérifient la complétude de la grille, la
résolution des termes (aucun coefficient ne pointe dans le vide) et la
neutralité de l'état de référence.
"""

import json
import unittest
from dataclasses import fields

from simulateur.domaines import (
    DOMAINES,
    DOMAINES_PAR_CLE,
    ECART_MAX_INDICATEUR,
    FAMILLES_RECETTES,
    LEVIERS,
    SENSIBILITE_SCORE,
    SPECS,
    MediateursAnnee,
    catalogue_domaines,
    construire_flux,
    decision_moteur,
    evaluer_indicateur,
)
from simulateur.moteur_parametrique import simuler
from simulateur.parametres import normaliser


class TestGrilleDesDomaines(unittest.TestCase):
    """La grille doit couvrir largement l'action publique."""

    def test_volume_et_unicite(self):
        self.assertGreaterEqual(len(DOMAINES), 18)
        cles = [domaine.cle for domaine in DOMAINES]
        self.assertEqual(len(cles), len(set(cles)))
        self.assertEqual(set(DOMAINES_PAR_CLE), set(cles))

    def test_chaque_domaine_est_decrit(self):
        for domaine in DOMAINES:
            with self.subTest(domaine=domaine.cle):
                self.assertTrue(domaine.libelle.strip())
                self.assertTrue(domaine.description.strip())
                self.assertRegex(domaine.couleur, r"^#[0-9a-fA-F]{6}$")
                self.assertGreaterEqual(domaine.priorite, 0)
                self.assertLessEqual(domaine.priorite, 100)

    def test_chaque_domaine_a_au_moins_deux_indicateurs(self):
        for domaine in DOMAINES:
            indicateurs = [spec for spec in SPECS if spec.domaine == domaine.cle]
            with self.subTest(domaine=domaine.cle):
                self.assertGreaterEqual(len(indicateurs), 2)

    def test_indicateurs_complets(self):
        for spec in SPECS:
            with self.subTest(indicateur=spec.cle):
                self.assertTrue(spec.libelle.strip())
                self.assertIn(spec.domaine, DOMAINES_PAR_CLE)
                self.assertIn(spec.sens, (-1, 1), "le sens doit indiquer si la hausse est bonne")
                self.assertTrue(spec.formule.strip(), "formule non documentée")
                self.assertTrue(spec.source.strip(), "source non documentée")
                self.assertTrue(spec.termes or not isinstance(spec.base, str))

    def test_cles_d_indicateurs_uniques(self):
        cles = [spec.cle for spec in SPECS]
        self.assertEqual(len(cles), len(set(cles)))

    def test_catalogue_serialisable(self):
        catalogue = catalogue_domaines()
        self.assertEqual(len(catalogue), len(DOMAINES))
        charge = json.dumps(catalogue, ensure_ascii=False)
        self.assertIn("indicateurs", charge)


class TestResolutionDesTermes(unittest.TestCase):
    """Aucun coefficient ne doit pointer vers un médiateur inexistant."""

    @classmethod
    def setUpClass(cls):
        """Collecte les médiateurs réellement produits par le moteur."""
        from simulateur.donnees_live import construire_contexte
        from simulateur.moteur_parametrique import (
            _boucle_mediateurs,
            _executer_serie,
            _mediteurs_annee,
            _valeurs_indicateurs,
        )

        cls.disponibles = {champ.name for champ in fields(MediateursAnnee)}
        contexte = construire_contexte(utiliser_cache=False, rafraichir=False, hors_ligne=True)

        # Trajectoire de référence : tous leviers neutres.
        moteur_ref, flux_ref = _executer_serie({}, contexte, 5)
        meds_ref = [
            _mediteurs_annee(resultat, flux_ref[i], contexte, i, 0.0, None)
            for i, resultat in enumerate(moteur_ref.historique_etapes)
        ]
        valeurs_ref = _valeurs_indicateurs(meds_ref, contexte)
        for mediateur in meds_ref:
            cls.disponibles |= set(mediateur.flux)
            cls.disponibles |= set(mediateur.ecarts)

        # Politiques contrastées : redistribution, consolidation, dépense, guerre.
        jeux = (
            {},
            {"isf_retablissement": 1.0, "ir_tranche_superieure": 3.0, "niches_fiscales": 6.0,
             "succession_reforme": 2.0, "csg_crds_hausse": 1.0},
            {"reforme_ric": 1.0, "reforme_proportionnelle": 1.0, "decentralisation": 1.0,
             "encadrement_loyers": 1.0},
            {"budget_education": 12.0, "hopital_public": 9.0, "logement_social": 8.0,
             "effectifs_securite": 20.0, "effort_defense_pct_pib": 3.5,
             "relocalisation_industrie": 12.0, "aide_logement": 4.0},
            {"lutte_fraude_fiscale_ia": 22.0, "commande_publique": 12.0,
             "fusion_doublons": 6.0, "fraude_sociale": 4.0},
        )
        for jeu in jeux:
            moteur, flux = _executer_serie(normaliser(jeu), contexte, 5)
            cumul = 0.0
            mediateurs = []
            for i, resultat in enumerate(moteur.historique_etapes):
                cumul += (flux[i].get("recettes_nouvelles_mde", 0.0)
                          - flux[i].get("depenses_nouvelles_mde", 0.0))
                mediateurs.append(_mediteurs_annee(resultat, flux[i], contexte, i, cumul,
                                                   meds_ref[i]))
            mediateurs, _ = _boucle_mediateurs(mediateurs, valeurs_ref, contexte, passes=4)
            for mediateur in mediateurs:
                cls.disponibles |= set(mediateur.flux)
                cls.disponibles |= set(mediateur.ecarts)

    def test_termes_resolus(self):
        manquants = {}
        for spec in SPECS:
            for mediateur, _ in spec.termes:
                if mediateur not in self.disponibles:
                    manquants.setdefault(mediateur, []).append(spec.cle)
        self.assertFalse(manquants, f"termes non alimentés : {manquants}")

    def test_bases_resolues(self):
        """Chaque base textuelle doit correspondre à un champ du contexte réel."""
        from simulateur.donnees_live import construire_contexte
        contexte = construire_contexte(utiliser_cache=False, rafraichir=False, hors_ligne=True)
        for spec in SPECS:
            if not isinstance(spec.base, str):
                continue
            with self.subTest(indicateur=spec.cle):
                # `_base_indicateur` lève une KeyError si la base est inconnue.
                evaluer_indicateur(spec, MediateursAnnee(), contexte) or True


class TestNeutraliteEtMonotonie(unittest.TestCase):
    """Sans levier activé, aucun domaine ne doit s'écarter de la référence."""

    def test_ecart_max_borne_les_indicateurs(self):
        self.assertGreater(ECART_MAX_INDICATEUR, 0.0)
        self.assertLess(ECART_MAX_INDICATEUR, 1.0)
        self.assertGreater(SENSIBILITE_SCORE, 0.0)

    def test_scores_neutres_a_cinquante(self):
        """Sans levier, le score mesure un impact nul : 50 partout."""
        sortie = simuler({}, avec_impacts=False)
        for domaine in sortie.domaines:
            with self.subTest(domaine=domaine["cle"]):
                self.assertAlmostEqual(domaine["score"], 50.0, places=1)
                self.assertAlmostEqual(domaine["score_reference"], 50.0, places=1)

    def test_la_tendance_de_reference_est_exposee(self):
        """Le user doit voir aussi « ce qui se passerait sans rien décider »."""
        sortie = simuler({}, avec_impacts=False)
        tendances = [d["tendance_reference"] for d in sortie.domaines]
        self.assertTrue(all(t is not None for t in tendances))
        self.assertNotEqual(set(tendances), {50.0})

    def test_scores_toujours_entre_zero_et_cent(self):
        for preset in ({}, {"lutte_fraude_fiscale_ia": 22.0}, {"effort_defense_pct_pib": 3.5},
                       {"hopital_public": 30.0, "reforme_ric": 1.0}):
            sortie = simuler(preset, avec_impacts=False)
            for domaine in sortie.domaines:
                with self.subTest(domaine=domaine["cle"]):
                    self.assertGreaterEqual(domaine["score"], 0.0)
                    self.assertLessEqual(domaine["score"], 100.0)

    def test_un_levier_de_depense_ameliore_son_domaine(self):
        """Monotonie : financer la santé ne peut pas dégrader l'indicateur santé."""
        sans = simuler({}, avec_impacts=False)
        avec = simuler({"hopital_public": 8.0, "ondam_variation": 3.0,
                        "medicaments_souverainete": 2.0}, avec_impacts=False)
        sante_sans = next(d for d in sans.domaines if d["cle"] == "sante")
        sante_avec = next(d for d in avec.domaines if d["cle"] == "sante")
        self.assertGreater(sante_avec["score"], sante_sans["score"])

    def test_une_recette_degrade_le_pouvoir_d_achat(self):
        sans = simuler({}, avec_impacts=False)
        avec = simuler({"tva_taux_normal": 2.0, "csg_crds_hausse": 1.5}, avec_impacts=False)
        avant = next(d for d in sans.domaines if d["cle"] == "pouvoir_achat")
        apres = next(d for d in avec.domaines if d["cle"] == "pouvoir_achat")
        self.assertLess(apres["score"], avant["score"])


class TestFluxEtDecision(unittest.TestCase):
    """Le pont entre les leviers et le moteur doit rester cohérent."""

    def test_flux_vides_quand_aucun_leverier(self):
        flux = construire_flux(normaliser({}), 0)
        self.assertEqual(flux.get("recettes_nouvelles_mde", 0.0), 0.0)
        self.assertEqual(flux.get("depenses_nouvelles_mde", 0.0), 0.0)

    def test_flux_signes(self):
        """Une recette augmente les recettes, une dépense augmente les dépenses."""
        flux = construire_flux(normaliser({"tva_taux_normal": 1.0, "hopital_public": 4.0}), 0)
        self.assertGreater(flux["recettes_nouvelles_mde"], 0.0)
        self.assertGreater(flux["depenses_nouvelles_mde"], 0.0)  # convention : + = dépense
        self.assertGreater(flux.get("sante_mde", 0.0), 0.0)

    def test_profil_temporel_applique(self):
        parametres = normaliser({"reforme_ric": 1.0})
        debut = construire_flux(parametres, 0)
        fin = construire_flux(parametres, 4)
        self.assertLess(abs(debut["depenses_nouvelles_mde"]), abs(fin["depenses_nouvelles_mde"]))

    def test_decision_transmet_les_montants(self):
        """Un levier de dépense alimente la décision avec son profil temporel."""
        parametres = normaliser({"budget_education": 10.0})
        levier = LEVIERS["budget_education"]
        decision = decision_moteur(parametres, 1)
        self.assertAlmostEqual(
            decision.depenses_prioritaires_mde, 10.0 * levier.profil[0], places=1
        )
        self.assertEqual(decision.annee, 1)
        annee_cinq = decision_moteur(parametres, 5)
        self.assertGreater(annee_cinq.depenses_prioritaires_mde,
                           decision.depenses_prioritaires_mde)

    def test_familles_recettes_identifiees(self):
        for famille in FAMILLES_RECETTES:
            self.assertIn(famille, {levier.famille for levier in LEVIERS.values()})


class TestEvaluationDunIndicateur(unittest.TestCase):
    """La fonction linéaire documentée doit être vérifiable à la main."""

    def test_indicateur_absolu(self):
        from simulateur.donnees_live import construire_contexte
        contexte = construire_contexte(utiliser_cache=False, rafraichir=False, hors_ligne=True)
        spec = next(s for s in SPECS if not s.unite.startswith(("%", "indice")) and s.termes)
        mediateurs = MediateursAnnee()
        mediateur, coefficient = spec.termes[0]
        mediateurs.flux[mediateur] = 1.0
        attendu = round(spec.base + coefficient, spec.precision) if not isinstance(spec.base, str) else None
        valeur = evaluer_indicateur(spec, mediateurs, contexte)
        if attendu is not None:
            self.assertAlmostEqual(valeur, attendu, places=max(0, spec.precision - 1))

    def test_mediateurs_vides_ne_changent_rien(self):
        from simulateur.donnees_live import construire_contexte
        contexte = construire_contexte(utiliser_cache=False, rafraichir=False, hors_ligne=True)
        mediateurs = MediateursAnnee()
        for spec in SPECS:
            if isinstance(spec.base, str):
                continue
            with self.subTest(indicateur=spec.cle):
                self.assertAlmostEqual(
                    evaluer_indicateur(spec, mediateurs, contexte), round(spec.base, spec.precision),
                    places=spec.precision,
                )

    def test_planchers_et_plafonds_respectes(self):
        from simulateur.donnees_live import construire_contexte
        contexte = construire_contexte(utiliser_cache=False, rafraichir=False, hors_ligne=True)
        mediateurs = MediateursAnnee()
        for mediateur in {terme for spec in SPECS for terme, _ in spec.termes}:
            mediateurs.flux[mediateur] = 1e6
            mediateurs.ecarts[mediateur] = 1e6
        for spec in SPECS:
            with self.subTest(indicateur=spec.cle):
                valeur = evaluer_indicateur(spec, mediateurs, contexte)
                if spec.plancher is not None:
                    self.assertGreaterEqual(valeur, round(spec.plancher, spec.precision))
                if spec.plafond is not None:
                    self.assertLessEqual(valeur, round(spec.plafond, spec.precision))


class TestEvaluerDomaines(unittest.TestCase):
    """L'évaluation complète retourne 5 années d'indicateurs par domaine."""

    def test_structure_de_sortie(self):
        sortie = simuler({"hopital_public": 5.0}, avec_impacts=False)
        self.assertEqual(len(sortie.domaines), len(DOMAINES))
        for domaine in sortie.domaines:
            with self.subTest(domaine=domaine["cle"]):
                self.assertIn("indicateurs", domaine)
                self.assertGreaterEqual(len(domaine["indicateurs"]), 2)
                for indicateur in domaine["indicateurs"]:
                    self.assertEqual(len(indicateur["serie"]), 5)
                    self.assertTrue(indicateur["formule"])
                    self.assertTrue(indicateur["source"])
                    self.assertIn(indicateur["sens"], (-1, 1))


if __name__ == "__main__":
    unittest.main()
