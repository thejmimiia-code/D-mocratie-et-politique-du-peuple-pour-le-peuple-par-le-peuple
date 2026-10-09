"""
tests/test_sources_et_audit.py — Tests de vérification du Registre des Sources Officielles,
de l'auditabilité en temps réel et des dynamiques socio-économiques et mondiales.
"""

import unittest
from simulateur.sources_officielles import (
    REGISTRE_SOURCES_OFFICIELLES,
    get_source,
    lister_sources_par_categorie,
    exporter_catalogue_sources,
)
from simulateur.reglements_lois import REGISTRE_LEGAL
from simulateur.moteur import MoteurSimulationSystemique
from simulateur.model import (
    DecisionPolitique,
    StrateDecilesEtInegalites,
    StrateCSPPopulations,
    StrateFluxMondiauxEtReels,
    StrateImpactCulturelEtServices,
    AuditTrailResultat,
)
from simulateur.scenarios import (
    get_scenario_mandature_5_ans,
    get_scenario_statut_quo,
    get_scenario_austerite_brutale,
    get_scenario_choc_mondial_stagflation,
)


class TestSourcesOfficielles(unittest.TestCase):
    """Vérification de la rigueur et de l'exhaustivité des sources officielles."""

    def test_nombre_minimal_sources_officielles(self):
        """Vérifie qu'au moins 20 sources officielles certifiées sont enregistrées."""
        self.assertGreaterEqual(len(REGISTRE_SOURCES_OFFICIELLES), 20)

    def test_integrite_champs_sources(self):
        """Vérifie que chaque source dispose de tous ses attributs de traçabilité."""
        for s_id, s in REGISTRE_SOURCES_OFFICIELLES.items():
            self.assertEqual(s_id, s.id_source)
            self.assertTrue(len(s.organisme) > 0, f"Organisme vide pour {s_id}")
            self.assertTrue(len(s.nom_indicateur) > 0, f"Indicateur vide pour {s_id}")
            self.assertTrue(s.url_officielle.startswith("http"), f"URL invalide pour {s_id}: {s.url_officielle}")
            self.assertTrue(len(s.millesime) > 0, f"Millésime vide pour {s_id}")
            self.assertGreaterEqual(s.intervalle_incertitude_pct, 0.0)

    def test_filtrage_categories_sources(self):
        """Vérifie le filtrage par catégories thématiques."""
        cats = ["Macroéconomie", "Marchés", "Fiscalité", "Social", "Territoires", "International", "Institutions"]
        for cat in cats:
            sources_cat = lister_sources_par_categorie(cat)
            self.assertGreater(len(sources_cat), 0, f"Aucune source trouvée pour la catégorie {cat}")

    def test_presence_sources_fondamentales(self):
        """Vérifie la présence des indicateurs clés (PIB, dette, déficit, OAT, PDE, etc.)."""
        cles_requises = [
            "INSEE_PIB_NOMINAL_2025",
            "INSEE_DEPENSES_PUBLIQUES_APU",
            "INSEE_RECETTES_PUBLIQUES_APU",
            "INSEE_DEFICIT_PUBLIC_MAASTRICHT",
            "INSEE_DETTE_PUBLIQUE_MAASTRICHT",
            "AFT_CHARGE_DETTE_NETTE",
            "AFT_PROGRAMME_EMISSION_ANNUEL",
            "AFT_DETENTION_NON_RESIDENTS",
            "BDF_TAUX_OAT_10_ANS",
            "SPREAD_OAT_BUND_10ANS",
            "BCE_TAUX_FACILITE_DEPOT",
            "CPO_ESTIMATION_FRAUDE_FISCALE",
            "DGFIP_TRAQUE_IA_CFIA",
            "CRE_DEPENSES_ELECTRICITE_GAZ",
            "INSEE_INDICE_GINI_FRANCE",
            "INSEE_TAUX_PAUVRETE_60PCT",
            "DGCL_INVENTAIRE_COMMUNES_34935",
            "DOUANES_FACTURE_ENERGETIQUE",
            "CONST_SEUIL_MAJORITE_CENSURE",
        ]
        for cle in cles_requises:
            self.assertIn(cle, REGISTRE_SOURCES_OFFICIELLES, f"Source fondamentale manquante : {cle}")
            s = get_source(cle)
            self.assertIsNotNone(s)


class TestNouveauxArticlesLois(unittest.TestCase):
    """Vérification des nouveaux articles de lois et règlements intégrés."""

    def test_articles_juridiques_cles(self):
        articles = [
            "CONST_ART_61",          # Contrôle a priori Conseil constitutionnel
            "LOLF_ART_34",           # Domaine exclusif et ordonnancement loi de finances
            "DIRECTIVE_UE_2022_542", # Taux réduit TVA énergie 5,5%
            "REGLEMENT_UE_2023_956", # MACF / CBAM taxe carbone aux frontières
            "LOI_ORG_2009_403",      # Études d'impact obligatoires des projets de loi
        ]
        for art in articles:
            self.assertIn(art, REGISTRE_LEGAL, f"Article manquant : {art}")
            loi = REGISTRE_LEGAL[art]
            self.assertTrue(len(loi.texte_integral) > 20)
            self.assertTrue(len(loi.effet_simulation) > 10)


class TestMoteurDynamiquesSocialesEtMondiales(unittest.TestCase):
    """Vérification des calculs granulaires socio-économiques et des flux mondiaux."""

    def test_scenario_mandature_reduction_inegalites_et_pauvrete(self):
        """Vérifie que le Plan de Mandature améliore le Gini, la pauvreté et les CSP."""
        moteur = MoteurSimulationSystemique()
        for dec in get_scenario_mandature_5_ans():
            moteur.appliquer_etape(dec)

        res5 = moteur.historique_etapes[-1]

        # 1. Déciles et Gini
        self.assertLess(res5.indice_gini, 0.298)  # Gini s'améliore
        self.assertLess(res5.taux_pauvrete_monetaire_pct, 14.4)  # Pauvreté recule
        self.assertGreater(res5.gain_pouvoir_achat_d1_d3_annuel_euros, 200.0)  # Gain tangible

        # 2. Catégories socioprofessionnelles
        self.assertGreater(res5.csp_ouvriers_confiance, 60.0)
        self.assertGreater(res5.csp_artisans_commercants_confiance, 65.0)

        # 3. Flux mondiaux et effet boule de neige r - g
        self.assertLess(res5.ecart_boule_de_neige_r_moins_g, 0.0)  # g > r : désendettement spontané !
        self.assertGreater(len(res5.signature_integrite_sha256), 8)

        # 4. Helper properties
        self.assertIsInstance(res5.deciles, StrateDecilesEtInegalites)
        self.assertIsInstance(res5.csp, StrateCSPPopulations)
        self.assertIsInstance(res5.flux_mondiaux, StrateFluxMondiauxEtReels)
        self.assertIsInstance(res5.services_publics, StrateImpactCulturelEtServices)
        self.assertIsInstance(res5.audit_trail, AuditTrailResultat)

    def test_scenario_austerite_aggravation_inegalites(self):
        """Vérifie qu'une austérité aveugle dégrade le Gini et la confiance ouvrière."""
        moteur = MoteurSimulationSystemique()
        etapes = []
        for dec in get_scenario_austerite_brutale():
            etapes.append(moteur.appliquer_etape(dec))

        res_aust5 = etapes[-1]
        self.assertGreater(res_aust5.indice_gini, 0.298)
        self.assertGreater(res_aust5.taux_pauvrete_monetaire_pct, 14.4)
        self.assertLess(res_aust5.csp_ouvriers_confiance, 35.0)


if __name__ == "__main__":
    unittest.main()
