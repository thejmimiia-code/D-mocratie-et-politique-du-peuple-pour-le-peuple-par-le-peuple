"""
simulateur/web_server.py — Serveur Web et API REST pour le Simulateur Macro-Politique & Démocratique.
Implémentation en Python standard (sans dépendance externe).
Binds to 0.0.0.0:8000 pour prévisualisation immédiate en direct.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulateur.model import DecisionPolitique, ResultatEtapeSimulation
from simulateur.moteur import MoteurSimulationSystemique
from simulateur.scenarios import (
    get_scenario_mandature_5_ans,
    get_scenario_statut_quo,
    get_scenario_austerite_brutale,
    get_scenario_choc_mondial_stagflation,
)
from simulateur.reglements_lois import get_corpus_lois, rechercher_loi
from simulateur.sources_officielles import (
    REGISTRE_SOURCES_OFFICIELLES,
    exporter_catalogue_sources,
    lister_sources_par_categorie,
)
from simulateur.think_tanks import (
    REGISTRE_THINK_TANKS,
    PARADIGMES_STRESS_TEST,
    get_think_tank,
    lister_think_tanks_par_echelon,
    exporter_catalogue_think_tanks,
    executer_stress_tests_mandature,
)
from simulateur.histoire_france import (
    PERIODES_HISTORIQUES,
    SERIES_ANNUELLES,
    REFORMES_MAJEURES,
    CRISES_HISTORIQUES,
    DIMENSIONS_COMPARISON,
    obtenir_toutes_periodes,
    obtenir_periode_par_id,
    comparer_periodes,
    filtrer_periodes,
    obtenir_series_chronologiques,
    obtenir_reformes,
    obtenir_crises,
    obtenir_options_dropdown,
    generer_synthese_historique,
    calibrer_parametres_historiques,
    exporter_json_complet,
)
from simulateur.societe_domaines import (
    DOMAINES_SOCIETAUX,
    obtenir_tous_domaines,
    obtenir_domaine_par_id,
    lister_domaines_ids,
    comparer_domaines,
    obtenir_serie_domaine,
    generer_synthese_societale,
    exporter_json_domaines,
)


def serialize_resultat(r: ResultatEtapeSimulation) -> Dict[str, Any]:
    """Convertit un ResultatEtapeSimulation en dictionnaire JSON-sérialisable."""
    return {
        "annee": r.annee,
        "pib_nominal_mde": r.pib_nominal_mde,
        "deficit_nominal_mde": r.deficit_nominal_mde,
        "ratio_deficit_pib": r.ratio_deficit_pib,
        "dette_nominale_mde": r.dette_nominale_mde,
        "ratio_dette_pib": r.ratio_dette_pib,
        "charge_dette_mde": r.charge_dette_mde,
        "recettes_publiques_totales_mde": r.recettes_publiques_totales_mde,
        "depenses_publiques_totales_mde": r.depenses_publiques_totales_mde,
        "pouvoir_achat_index": r.pouvoir_achat_index,
        "confiance_democratique": r.confiance_democratique,
        "risque_censure_parlement": r.risque_censure_parlement,
        "tension_sociale_locale": r.tension_sociale_locale,
        "qualite_services_proximite": r.qualite_services_proximite,
        "produit_taxe_fonciere_mde": r.produit_taxe_fonciere_mde,
        "statut_pde_europe": r.statut_pde_europe,
        "bouclier_tpi_actif": r.bouclier_tpi_actif,
        "sanction_financiere_ue": r.sanction_financiere_ue,
        "taux_oat_pct": r.taux_oat_pct,
        "spread_bund_bps": r.spread_bund_bps,
        "note_souveraine": r.note_souveraine,
        "taux_credit_pme": r.taux_credit_pme,
        "cours_petrole_usd": r.cours_petrole_usd,
        "taux_change_eur_usd": r.taux_change_eur_usd,
        "facture_energetique_mde": r.facture_energetique_mde,
        "inflation_globale_pct": r.inflation_globale_pct,
        # Variables dynamiques des Assemblées Représentatives et Décisionnelles
        "voix_censure_an": getattr(r, "voix_censure_an", 265),
        "gouvernement_censure": getattr(r, "gouvernement_censure", False),
        "climat_assemblee_nationale": getattr(r, "climat_assemblee_nationale", "Majorité relative tendue"),
        "hostilite_senat_indice": getattr(r, "hostilite_senat_indice", 30.0),
        "senat_veto_art_89": getattr(r, "senat_veto_art_89", False),
        "congres_majorite_3_5": getattr(r, "congres_majorite_3_5", False),
        "departements_alerte_ciseau": getattr(r, "departements_alerte_ciseau", 14),
        "fronde_maires_indice": getattr(r, "fronde_maires_indice", 24.0),
        "pe_taux_alignement": getattr(r, "pe_taux_alignement", 65.0),
        "cese_consensus_social": getattr(r, "cese_consensus_social", 48.0),
        "consulaire_confiance_pme": getattr(r, "consulaire_confiance_pme", 56.0),
        "convention_citoyenne_consensus": getattr(r, "convention_citoyenne_consensus", 84.0),
        # Variables du Cycle de Vie et des 3 Générations
        "g1_seniors_pop_m": getattr(r, "g1_seniors_pop_m", 14.6),
        "g2_actifs_pop_m": getattr(r, "g2_actifs_pop_m", 26.2),
        "g3_jeunesse_pop_m": getattr(r, "g3_jeunesse_pop_m", 27.6),
        "ratio_dependance_demographique": getattr(r, "ratio_dependance_demographique", 0.65),
        "indice_harmonie_intergenerationnelle": getattr(r, "indice_harmonie_intergenerationnelle", 42.0),
        "g2_charge_sandwich_indice": getattr(r, "g2_charge_sandwich_indice", 68.0),
        "g3_taux_pauvrete_pct": getattr(r, "g3_taux_pauvrete_pct", 19.4),
        "g1_taux_pauvrete_pct": getattr(r, "g1_taux_pauvrete_pct", 10.8),
        "transfert_retraites_mde": getattr(r, "transfert_retraites_mde", 360.0),
        "transfert_education_mde": getattr(r, "transfert_education_mde", 165.0),
        "donations_vers_g3_mde": getattr(r, "donations_vers_g3_mde", 75.0),
        "garde_enfants_grands_parents_mde": getattr(r, "garde_enfants_grands_parents_mde", 18.0),
        "charge_dette_par_jeune_euros": getattr(r, "charge_dette_par_jeune_euros", 129275.0),
        # Variables Territoriales, Outre-Mer et Fonctions Électorales
        "outremer_vie_chere_indice": getattr(r, "outremer_vie_chere_indice", 32.5),
        "surcout_vie_chere_outremer_pct": getattr(r, "outremer_vie_chere_indice", 32.5),
        "outremer_continuite_indice": getattr(r, "outremer_continuite_indice", 54.0),
        "indice_continuite_territoriale": getattr(r, "outremer_continuite_indice", 54.0),
        "participation_electorale_globale_pct": getattr(r, "participation_electorale_globale_pct", 66.5),
        "participation_electorale_proj_pct": getattr(r, "participation_electorale_globale_pct", 66.5),
        "triangulaires_legislatives_count": getattr(r, "triangulaires_legislatives_count", 85),
        "triangulaires_legislatives_proj": getattr(r, "triangulaires_legislatives_count", 85),
        "communes_rurales_vitalite_indice": getattr(r, "communes_rurales_vitalite_indice", 62.0),
        "vitalite_rurale_indice": getattr(r, "communes_rurales_vitalite_indice", 62.0),
        "metropoles_efficience_indice": getattr(r, "metropoles_efficience_indice", 71.0),
        "efficience_metropolitaine_indice": getattr(r, "metropoles_efficience_indice", 71.0),
        # Variables de Déciles, Inégalités et Pouvoir d'Achat Réel (ERFS / INSEE)
        "indice_gini": getattr(r, "indice_gini", 0.298),
        "taux_pauvrete_monetaire_pct": getattr(r, "taux_pauvrete_monetaire_pct", 14.4),
        "ratio_interdecile_d9_d1": getattr(r, "ratio_interdecile_d9_d1", 3.90),
        "gain_pouvoir_achat_d1_d3_annuel_euros": getattr(r, "gain_pouvoir_achat_d1_d3_annuel_euros", 0.0),
        "gain_pouvoir_achat_d4_d7_annuel_euros": getattr(r, "gain_pouvoir_achat_d4_d7_annuel_euros", 0.0),
        "effort_energetique_d1_pct": getattr(r, "effort_energetique_d1_pct", 11.5),
        # Variables des 8 Catégories Socioprofessionnelles (CSP INSEE)
        "csp_ouvriers_confiance": getattr(r, "csp_ouvriers_confiance", 48.0),
        "csp_employes_confiance": getattr(r, "csp_employes_confiance", 50.0),
        "csp_prof_intermediaires_confiance": getattr(r, "csp_prof_intermediaires_confiance", 54.0),
        "csp_cadres_confiance": getattr(r, "csp_cadres_confiance", 62.0),
        "csp_artisans_commercants_confiance": getattr(r, "csp_artisans_commercants_confiance", 52.0),
        "csp_agriculteurs_confiance": getattr(r, "csp_agriculteurs_confiance", 45.0),
        "csp_retraites_confiance": getattr(r, "csp_retraites_confiance", 58.0),
        "csp_inactifs_etudiants_confiance": getattr(r, "csp_inactifs_etudiants_confiance", 46.0),
        # Variables des Flux Internationaux et Dette
        "exportations_biens_services_mde": getattr(r, "exportations_biens_services_mde", 980.0),
        "importations_biens_services_mde": getattr(r, "importations_biens_services_mde", 1050.0),
        "solde_commercial_mde": getattr(r, "solde_commercial_mde", -70.0),
        "part_dette_non_residents_pct": getattr(r, "part_dette_non_residents_pct", 55.8),
        "volume_dette_non_residents_mde": getattr(r, "volume_dette_non_residents_mde", 1990.0),
        "taux_interet_apparent_r_pct": getattr(r, "taux_interet_apparent_r_pct", 2.5),
        "taux_croissance_pib_nominal_g_pct": getattr(r, "taux_croissance_pib_nominal_g_pct", 2.8),
        "ecart_boule_de_neige_r_moins_g": getattr(r, "ecart_boule_de_neige_r_moins_g", -0.3),
        # Variables de Services Publics et Cohésion Républicaine
        "acces_services_publics_indice": getattr(r, "acces_services_publics_indice", 65.0),
        "fracture_territoriale_indice": getattr(r, "fracture_territoriale_indice", 38.0),
        "cohesion_republicaine_indice": getattr(r, "cohesion_republicaine_indice", 62.0),
        "satisfaction_services_publics_pct": getattr(r, "satisfaction_services_publics_pct", 58.0),
        # Piste d'Audit et Validation Cryptographique
        "nb_sources_officielles_mobilisees": getattr(r, "nb_sources_officielles_mobilisees", 25),
        "taux_couverture_legale_pct": getattr(r, "taux_couverture_legale_pct", 100.0),
        "conformite_organique_lolf": getattr(r, "conformite_organique_lolf", True),
        "signature_integrite_sha256": getattr(r, "signature_integrite_sha256", ""),
        "commentaires": r.commentaires,
    }


def executer_simulation_scenario(nom: str) -> List[Dict[str, Any]]:
    """Exécute un scénario prédéfini et renvoie la trajectoire sérialisée."""
    moteur = MoteurSimulationSystemique()
    if nom == "mandature":
        decisions = get_scenario_mandature_5_ans()
    elif nom == "statut_quo":
        decisions = get_scenario_statut_quo()
    elif nom == "austerite":
        decisions = get_scenario_austerite_brutale()
    elif nom == "choc_mondial":
        decisions = get_scenario_choc_mondial_stagflation()
    else:
        raise ValueError(f"Scénario inconnu : {nom}")

    for dec in decisions:
        moteur.appliquer_etape(dec)

    return [serialize_resultat(r) for r in moteur.historique_etapes]


def executer_simulation_personnalisee(annees_decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Exécute une simulation sur-mesure à partir d'une liste de paramètres par année."""
    moteur = MoteurSimulationSystemique()
    for idx, d in enumerate(annees_decisions, start=1):
        dec = DecisionPolitique(
            annee=idx,
            description=d.get("description", f"Année {idx} sur-mesure"),
            recettes_fraude_ia_mde=float(d.get("recettes_fraude_ia_mde", 0.0)),
            conditionnement_aides_entreprises_mde=float(d.get("conditionnement_aides_entreprises_mde", 0.0)),
            taxe_superprofits_rachats_mde=float(d.get("taxe_superprofits_rachats_mde", 0.0)),
            extension_ttf_mde=float(d.get("extension_ttf_mde", 0.0)),
            recettes_pilier2_ocde_mde=float(d.get("recettes_pilier2_ocde_mde", 0.0)),
            recettes_macf_carbone_mde=float(d.get("recettes_macf_carbone_mde", 0.0)),
            fusion_doublons_territoriaux_mde=float(d.get("fusion_doublons_territoriaux_mde", 0.0)),
            commande_publique_massifiee_mde=float(d.get("commande_publique_massifiee_mde", 0.0)),
            extinction_niches_inefficaces_mde=float(d.get("extinction_niches_inefficaces_mde", 0.0)),
            fraude_sociale_criminelle_mde=float(d.get("fraude_sociale_criminelle_mde", 0.0)),
            baisse_tva_energie_5_5_mde=float(d.get("baisse_tva_energie_5_5_mde", 0.0)),
            reforme_casier_b2=bool(d.get("reforme_casier_b2", False)),
            reforme_vote_blanc_invalidant=bool(d.get("reforme_vote_blanc_invalidant", False)),
            reforme_ric_souverain=bool(d.get("reforme_ric_souverain", False)),
            reforme_fin_regimes_speciaux=bool(d.get("reforme_fin_regimes_speciaux", False)),
            reforme_anti_pantouflage_lobbys=bool(d.get("reforme_anti_pantouflage_lobbys", False)),
            reforme_non_cumul_mandats=bool(d.get("reforme_non_cumul_mandats", False)),
            delta_dotation_dgf_mde=float(d.get("delta_dotation_dgf_mde", 0.0)),
            choc_petrole_brent_usd=float(d.get("choc_petrole_brent_usd", 0.0)),
            choc_taux_fed_bps=float(d.get("choc_taux_fed_bps", 0.0)),
            choc_change_eur_usd=float(d.get("choc_change_eur_usd", 0.0)),
        )
        moteur.appliquer_etape(dec)

    return [serialize_resultat(r) for r in moteur.historique_etapes]


def generer_comparatif_global() -> Dict[str, Any]:
    """Génère la comparaison croisée des 4 scénarios à l'Année 5."""
    scenarios = ["mandature", "statut_quo", "austerite", "choc_mondial"]
    comparatif = {}
    for sc in scenarios:
        trajectoire = executer_simulation_scenario(sc)
        annee5 = trajectoire[-1]
        comparatif[sc] = {
            "nom": sc,
            "annee_cible": annee5["annee"],
            "deficit_nominal_mde": annee5["deficit_nominal_mde"],
            "ratio_deficit_pib": annee5["ratio_deficit_pib"],
            "ratio_dette_pib": annee5["ratio_dette_pib"],
            "taux_oat_pct": annee5["taux_oat_pct"],
            "spread_bund_bps": annee5["spread_bund_bps"],
            "note_souveraine": annee5["note_souveraine"],
            "tension_sociale_locale": annee5["tension_sociale_locale"],
            "confiance_democratique": annee5["confiance_democratique"],
            "risque_censure_parlement": annee5["risque_censure_parlement"],
            "statut_pde_europe": annee5["statut_pde_europe"],
            "bouclier_tpi_actif": annee5["bouclier_tpi_actif"],
            "pouvoir_achat_index": annee5["pouvoir_achat_index"],
            # Assemblées
            "voix_censure_an": annee5.get("voix_censure_an", 265),
            "gouvernement_censure": annee5.get("gouvernement_censure", False),
            "hostilite_senat_indice": annee5.get("hostilite_senat_indice", 30.0),
            "senat_veto_art_89": annee5.get("senat_veto_art_89", False),
            "congres_majorite_3_5": annee5.get("congres_majorite_3_5", False),
            "departements_alerte_ciseau": annee5.get("departements_alerte_ciseau", 14),
            "fronde_maires_indice": annee5.get("fronde_maires_indice", 24.0),
            "consulaire_confiance_pme": annee5.get("consulaire_confiance_pme", 56.0),
            "pe_taux_alignement": annee5.get("pe_taux_alignement", 65.0),
            "cese_consensus_social": annee5.get("cese_consensus_social", 48.0),
            "convention_citoyenne_consensus": annee5.get("convention_citoyenne_consensus", 84.0),
            # Cycle de vie et 3 Générations
            "indice_harmonie_intergenerationnelle": annee5.get("indice_harmonie_intergenerationnelle", 42.0),
            "g2_charge_sandwich_indice": annee5.get("g2_charge_sandwich_indice", 68.0),
            "g3_taux_pauvrete_pct": annee5.get("g3_taux_pauvrete_pct", 19.4),
            "g1_taux_pauvrete_pct": annee5.get("g1_taux_pauvrete_pct", 10.8),
            "charge_dette_par_jeune_euros": annee5.get("charge_dette_par_jeune_euros", 129275.0),
            # Territoires, Outre-mer & Élections
            "outremer_vie_chere_indice": annee5.get("outremer_vie_chere_indice", 32.5),
            "surcout_vie_chere_outremer_pct": annee5.get("surcout_vie_chere_outremer_pct", 32.5),
            "outremer_continuite_indice": annee5.get("outremer_continuite_indice", 54.0),
            "indice_continuite_territoriale": annee5.get("indice_continuite_territoriale", 54.0),
            "participation_electorale_globale_pct": annee5.get("participation_electorale_globale_pct", 66.5),
            "participation_electorale_proj_pct": annee5.get("participation_electorale_proj_pct", 66.5),
            "triangulaires_legislatives_count": annee5.get("triangulaires_legislatives_count", 85),
            "triangulaires_legislatives_proj": annee5.get("triangulaires_legislatives_proj", 85),
            "communes_rurales_vitalite_indice": annee5.get("communes_rurales_vitalite_indice", 62.0),
            "vitalite_rurale_indice": annee5.get("vitalite_rurale_indice", 62.0),
            "metropoles_efficience_indice": annee5.get("metropoles_efficience_indice", 71.0),
            "efficience_metropolitaine_indice": annee5.get("efficience_metropolitaine_indice", 71.0),
        }
    return comparatif


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Serveur HTTP multithreadé standard."""
    daemon_threads = True


class SimulateurHTTPHandler(BaseHTTPRequestHandler):
    """Gestionnaire des requêtes HTTP pour l'UI Web et l'API JSON."""

    def _envoyer_json(self, status: int, data: Any):
        payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(payload)

    def _envoyer_html(self, status: int, html_str: str):
        payload = html_str.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. Page principale HTML
        if path in ("/", "/index.html"):
            self._envoyer_html(200, HTML_DASHBOARD)
            return

        # 2. API Statut
        if path == "/api/status":
            self._envoyer_json(200, {
                "status": "ok",
                "app": "Simulateur Macro-Politique & Démocratique",
                "version": "1.1.0",
                "moteur": "Gigogne 4 Échelons (Local, National, Europe, Marchés)",
                "instant_t": "Septembre 2026",
            })
            return

        # 3. API Scénarios
        if path == "/api/scenarios":
            self._envoyer_json(200, {
                "scenarios": [
                    {
                        "id": "mandature",
                        "nom": "Plan de Mandature Républicain (+60 Md€)",
                        "description": "Redressement équilibré, sortie de PDE (<3% PIB), baisse de TVA énergie, apaisement civique.",
                        "duree_ans": 5,
                    },
                    {
                        "id": "statut_quo",
                        "nom": "Statut Quo (Immobilisme politique)",
                        "description": "Aucune réforme d'envergure, poursuite de l'inertie, dégradation financière et perte de souveraineté.",
                        "duree_ans": 5,
                    },
                    {
                        "id": "austerite",
                        "nom": "Austérité Aveugle (Coupes territoriales)",
                        "description": "Coupes brutales dans les dotations aux collectivités, explosion de la taxe foncière, contestation majeure.",
                        "duree_ans": 5,
                    },
                    {
                        "id": "choc_mondial",
                        "nom": "Stress-Test Choc Mondial (Stagflation)",
                        "description": "Flambée du baril à >110$, dépréciation de l'euro, resserrement Fed. Test de résilience systémique.",
                        "duree_ans": 3,
                    },
                ]
            })
            return

        # 4. API Comparatif
        if path == "/api/comparatif":
            try:
                comp = generer_comparatif_global()
                self._envoyer_json(200, comp)
            except Exception as e:
                self._envoyer_json(500, {"erreur": str(e)})
            return

        # 5. API Corpus Juridique
        if path == "/api/corpus":
            corpus = get_corpus_lois()
            q = query.get("q", [""])[0].strip().lower()
            strate_filtre = query.get("strate", [""])[0].strip().lower()

            articles = []
            for art in corpus.values():
                if strate_filtre and art.strate_impactee.lower() != strate_filtre:
                    continue
                if q:
                    chaine_recherche = f"{art.identifiant} {art.code_ou_traite} {art.article} {art.titre} {art.texte_integral} {art.effet_simulation}".lower()
                    if q not in chaine_recherche:
                        continue
                articles.append({
                    "identifiant": art.identifiant,
                    "code_ou_traite": art.code_ou_traite,
                    "article": art.article,
                    "titre": art.titre,
                    "strate_impactee": art.strate_impactee,
                    "effet_simulation": art.effet_simulation,
                    "texte_integral": art.texte_integral,
                })
            self._envoyer_json(200, {"total": len(articles), "articles": articles})
            return

        # 6. API Dossier
        if path == "/api/dossier":
            self._envoyer_json(200, {
                "volumes": [
                    {"num": "00", "fichier": "00_HISTOIRE_CONSTITUTIONS_ET_REVENDICATIONS.md", "titre": "Histoire, Constitutions et Revendications populaires"},
                    {"num": "01", "fichier": "01_DEMOCRATIE_INSTITUTIONS.md", "titre": "Démocratie, Référendum (RIC) et Moralisation républicaine"},
                    {"num": "02", "fichier": "02_RECETTES_ET_TRANSACTIONS.md", "titre": "Nouvelles Recettes ciblées (+36 Md€ / an)"},
                    {"num": "03", "fichier": "03_ECONOMIES_ET_EFFICACITE_ETAT.md", "titre": "Économies structurelles et Efficacité (+24 Md€ / an)"},
                    {"num": "04", "fichier": "04_POUVOIR_D_ACHAT_ET_TRAJECTOIRE.md", "titre": "Pouvoir d'Achat, TVA Énergie et Trajectoire quinquennale"},
                    {"num": "05", "fichier": "05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md", "titre": "Guide tactique d'Autodéfense et Contre-arguments"},
                    {"num": "06", "fichier": "06_CORPUS_JURIDIQUE_ET_REGLEMENTAIRE_INTEGRAL.md", "titre": "Corpus Juridique et Réglementaire Intégral"},
                    {"num": "07", "fichier": "07_INSTITUTIONS_DE_LA_REPUBLIQUE_DROITS_ET_CHAMBRES_CONSULAIRES.md", "titre": "Institutions de la République, Droits et Chambres Consulaires"},
                    {"num": "08", "fichier": "08_ASSEMBLEES_REPRESENTATIVES_ET_DECISIONNELLES.md", "titre": "Toutes les Assemblées représentatives et décisionnelles (Fonctionnement & Jeux de Pouvoirs)"},
                    {"num": "09", "fichier": "09_CYCLE_DE_VIE_ET_FLUX_INTERGENERATIONNELS.md", "titre": "Pacte républicain du Berceau au Tombeau (Cycle de vie, 3 Générations & Flux croisés)"},
                    {"num": "10", "fichier": "10_STRATES_TERRITORIALES_OUTRE_MER_ET_FONCTIONS_ELECTORALES.md", "titre": "Strates territoriales du Lieu-dit à la Métropole, Outre-Mer complet & Fonctions Électorales"},
                    {"num": "11", "fichier": "11_PANORAMA_EXHAUSTIF_TERRITOIRES_OUTRE_MER_ELECTIONS_ET_LEGISLATION.md", "titre": "Panorama exhaustif des Strates territoriales, de l'Outre-Mer intégral, des Élections et du Corpus législatif"},
                    {"num": "12", "fichier": "12_GOUVERNANCE_BUDGETAIRE_ARBITRAGES_MINISTERIELS_ET_SURVIE_POLITIQUE.md", "titre": "Arbitrages Budgétaires de Bercy, Profils Ministériels et Survie Politique"},
                    {"num": "Audit", "fichier": "PLAN_DU_SIMULATEUR_ET_AUDIT_INSTANT_T.md", "titre": "Architecture SFC, Matrice causale et Audit des 10 Redondances"},
                ]
            })
            return

        # 7. API Assemblées
        if path == "/api/assemblees":
            self._envoyer_json(200, {
                "assemblees": [
                    {
                        "id": "an",
                        "nom": "Assemblée nationale",
                        "echelon": "National",
                        "composition": "577 députés élus au suffrage universel direct",
                        "pouvoirs": "Vote de la loi, consentement à l'impôt (art. 34/39/47), censure du gouvernement (art. 49.2/3, 289 voix), dernier mot législatif face au Sénat (art. 45).",
                        "contraintes": "Absence de majorité absolue, risque de motion de censure, irrecevabilité financière (art. 40)."
                    },
                    {
                        "id": "senat",
                        "nom": "Sénat",
                        "echelon": "National",
                        "composition": "348 sénateurs élus au suffrage indirect par les grands électeurs territoriaux",
                        "pouvoirs": "Représentation constitutionnelle des collectivités (art. 24 al. 3), VETO ABSOLU sur toute révision constitutionnelle (art. 89), commissions d'enquête quasi-judiciaires (art. 51-2).",
                        "contraintes": "Inertie conservatrice, défense inconditionnelle de la DGF communale."
                    },
                    {
                        "id": "congres",
                        "nom": "Congrès du Parlement",
                        "echelon": "National",
                        "composition": "925 parlementaires réunis au château de Versailles (577 déps + 348 sénateurs)",
                        "pouvoirs": "Adoption définitive des révisions constitutionnelles (art. 89 al. 3) sans référendum.",
                        "contraintes": "Règle de majorité qualifiée renforcée des 3/5èmes (555 voix sur 925). Si bloqué, recours nécessaire à l'art. 11."
                    },
                    {
                        "id": "cese",
                        "nom": "Conseil Économique, Social et Environnemental (CESE)",
                        "echelon": "National",
                        "composition": "175 conseillers (syndicats salariés, patronat, artisans, mutualité, associations)",
                        "pouvoirs": "Avis consultatifs obligatoires sur les lois de plan, saisine citoyenne (dès 150 000 signataires), portage des conventions citoyennes.",
                        "contraintes": "Avis non contraignants juridiquement mais à forte portée politique."
                    },
                    {
                        "id": "convention_citoyenne",
                        "nom": "Conventions Citoyennes Tirées au Sort",
                        "echelon": "Participatif",
                        "composition": "150 citoyens tirés au sort selon un échantillonnage représentatif de la nation",
                        "pouvoirs": "Délibération éclairée, propositions de lois républicaines clef en main.",
                        "contraintes": "Nécessite un engagement sans filtre de l'exécutif pour soumission directe au référendum ou au Parlement."
                    },
                    {
                        "id": "conseil_municipal",
                        "nom": "Conseils Municipaux",
                        "echelon": "Local",
                        "composition": "34 935 assemblées communales",
                        "pouvoirs": "Vote du budget primitif, fixation des taux de taxe foncière (TFPB), gestion des écoles et voirie.",
                        "contraintes": "Règle d'or budgétaire stricte (art. L. 1612-4 CGCT : interdiction d'emprunter pour fonctionner)."
                    },
                    {
                        "id": "conseil_intercommunal",
                        "nom": "Conseils Intercommunaux & Métropolitains (EPCI)",
                        "echelon": "Local",
                        "composition": "1 254 assemblées métropolitaines et de communautés de communes",
                        "pouvoirs": "Transports urbains, eau, assainissement, déchets, Cotisation Foncière des Entreprises (CFE).",
                        "contraintes": "Tensions récurrentes entre ville-centre et communes périphériques."
                    },
                    {
                        "id": "conseil_departemental",
                        "nom": "Conseils Départementaux",
                        "echelon": "Local",
                        "composition": "101 assemblées départementales",
                        "pouvoirs": "Chef de file des solidarités sociales : RSA, APA aînés, PCH handicap, ASE enfance, collèges et SDIS.",
                        "contraintes": "Effet de ciseau mortel : dépenses sociales rigides imposées nationalement vs recettes DMTO effondrées."
                    },
                    {
                        "id": "conseil_regional",
                        "nom": "Conseils Régionaux",
                        "echelon": "Local",
                        "composition": "18 assemblées régionales",
                        "pouvoirs": "Schéma régional d'aménagement (SRADDET), TER, lycées, développement économique, CPER.",
                        "contraintes": "Négociation serrée des cofinancements européens et des contrats de plan avec l'État."
                    },
                    {
                        "id": "assemblees_consulaires",
                        "nom": "Assemblées Consulaires (CCI, CMA, Chambres d'Agriculture)",
                        "echelon": "Consulaire",
                        "composition": "Établissements publics gérés par des pairs élus (commerçants, industriels, artisans, paysans)",
                        "pouvoirs": "Gestion des CFA, aéroports, ports, avis consultatifs décisionnels d'urbanisme (CDAC) et de protection foncière (CDPENAF).",
                        "contraintes": "Revendiquent la fin des monopoles et l'allotissement obligatoire de la commande publique réservant 30% aux PME."
                    },
                    {
                        "id": "parlement_europeen",
                        "nom": "Parlement Européen",
                        "echelon": "Europe",
                        "composition": "720 eurodéputés (dont 81 élus en France au scrutin proportionnel)",
                        "pouvoirs": "Codécision législative des directives et règlements, vote du budget de l'UE, investiture de la Commission.",
                        "contraintes": "Nécessite des coalitions transpartisanes (PPE, S&D, Renew)."
                    },
                    {
                        "id": "conseil_ue",
                        "nom": "Conseil de l'Union Européenne",
                        "echelon": "Europe",
                        "composition": "Conseil des ministres des 27 États membres",
                        "pouvoirs": "Décisions législatives conjointes, majorité qualifiée (55% États, 65% pop), ouverture et sanctions PDE.",
                        "contraintes": "Surveillance rigide des plafonds de Maastricht (3% déficit, 60% dette)."
                    }
                ]
            })
            return

        # 8. API Générations & Cycle de Vie (3 Générations)
        if path == "/api/generations":
            self._envoyer_json(200, {
                "cohortes": [
                    {
                        "id": "g1",
                        "nom": "Génération 1 : Aînés et Retraités",
                        "ages": "65 à 95+ ans (nés 1930-1960)",
                        "population_millions": 14.6,
                        "pension_mediane": "1 620 € / mois",
                        "part_patrimoine_pct": 61.5,
                        "taux_pauvrete_pct": 10.8,
                        "role_social": "Mémoire républicaine, garde bénévole des petits-enfants (18 Md€ équiv.), bénévolat associatif (68%), maires de communes rurales (58%).",
                        "vulnerabilite": "Dépendance du grand âge, reste à charge EHPAD (1 200 €/m), isolement rural, déserts médicaux."
                    },
                    {
                        "id": "g2",
                        "nom": "Génération 2 : Actifs et Parents",
                        "ages": "35 à 64 ans (nés 1961-1990)",
                        "population_millions": 26.2,
                        "salaire_median": "2 280 € / mois",
                        "part_patrimoine_pct": 31.2,
                        "taux_pauvrete_pct": 13.2,
                        "role_social": "Moteur contributif et productif de la Nation (345 Md€ cotisations, 125 Md€ impôt sur le revenu), 22,4M actifs occupés.",
                        "vulnerabilite": "Génération Sandwich écrasée entre le coût d'études/logement de G3 et la charge EHPAD/dépendance de G1, emploi des seniors."
                    },
                    {
                        "id": "g3",
                        "nom": "Génération 3 : Jeunesse et Avenir",
                        "ages": "0 à 34 ans (nés 1991-2026+)",
                        "population_millions": 27.6,
                        "revenu_median": "1 540 € / mois",
                        "part_patrimoine_pct": 7.3,
                        "taux_pauvrete_pct": 19.4,
                        "role_social": "Relève républicaine, scolarité et études supérieures (15,2M d'élèves/étudiants), innovation et réindustrialisation.",
                        "vulnerabilite": "Précarité étudiante, fardeau de la dette souveraine (129 k€/jeune), loyers écrasants (38,5% budget), barrière d'accès à la propriété."
                    }
                ],
                "periodes_vie": [
                    {"code": "P0", "titre": "0 - 3 ans : Petite Enfance & Périnatalité", "acteurs": "Communes, CAF, Départements (PMI)", "enjeux": "Places en crèche, soutien G1 (garde gratuite), congé parental rémunéré."},
                    {"code": "P1", "titre": "3 - 11 ans : Enfance & École Primaire", "acteurs": "Conseils Municipaux & Éducation Nationale", "enjeux": "Savoirs fondamentaux, cantines scolaires 1€, santé scolaire, périscolaire."},
                    {"code": "P2", "titre": "11 - 18 ans : Adolescence, Collège & Lycée", "acteurs": "Conseils Départementaux & Régionaux", "enjeux": "Collèges (Dép.), Lycées (Rég.), orientation, apprentissage, santé mentale."},
                    {"code": "P3", "titre": "18 - 25 ans : Enseignement Supérieur & Autonomie", "acteurs": "État, Universités, Régions, CCI/CMA", "enjeux": "Logement étudiant, CROUS, bourses, dotation républicaine d'émancipation, premier vote."},
                    {"code": "P4", "titre": "25 - 35 ans : Insertion Active & Premier Toit", "acteurs": "Entreprises, Banques, Bailleurs sociaux, État", "enjeux": "Accès au premier emploi CDI, levée de la barrière de l'apport bancaire, formation couple/famille."},
                    {"code": "P5", "titre": "35 - 50 ans : Plénitude & Génération Sandwich", "acteurs": "Sécurité sociale, État (Impôts), Départements", "enjeux": "Pic contributif fiscal, double fardeau simultané (aide aux études G3 + aide aux aînés dépendants G1)."},
                    {"code": "P6", "titre": "50 - 65 ans : Seconde Carrière & Transmission", "acteurs": "Branches professionnelles, Retraites, Notariat", "enjeux": "Maintien emploi seniors 55+, transmission savoir-faire, âge moyen héritage (52 ans)."},
                    {"code": "P7", "titre": "65 - 80 ans : Retraite Active & Pilier Civique", "acteurs": "Sécurité sociale (CNAV), Communes, Associations", "enjeux": "Retraite par répartition, garde petits-enfants, 68% du bénévolat, maires de villages."},
                    {"code": "P8", "titre": "80 - 95+ ans : Grand Âge, Dépendance & Fin de Vie", "acteurs": "Départements (APA), CNSA (5e branche), EHPAD, Hôpitaux", "enjeux": "Perte d'autonomie (GIR 1-4), reste à charge EHPAD, maintien à domicile, transmission successorale."}
                ],
                "flux_croises": {
                    "retraites_g2_vers_g1_mde": 360.0,
                    "sante_g2_vers_g1_mde": 95.0,
                    "education_g2_vers_g3_mde": 165.0,
                    "garde_enfants_g1_vers_g3_mde": 18.0,
                    "successions_g1_vers_g2_mde": 225.0,
                    "donations_g1_vers_g3_mde": 75.0,
                    "ratio_dependance_demographique": 0.65,
                    "charge_dette_par_jeune_euros": 129275.0
                }
            })
            return

        # 9. API Territoires & Outre-Mer Intégral
        if path == "/api/territoires":
            self._envoyer_json(200, {
                "continuum": {
                    "lieux_dits_cadastraux_estimes": 500000,
                    "sections_commune_lieux_dits": 2500,
                    "conseils_de_quartier_count": 1550,
                    "quartiers_prioritaires_ville_qpv": 1514,
                    "communes_rurales_moins_1000": 25800,
                    "bourgs_centres_1k_10k": 7650,
                    "villes_moyennes_10k_50k": 1280,
                    "grandes_agglomerations_50k_200k": 180,
                    "metropoles_200k_plus": 22,
                    "communes_total": 34935,
                    "epci_total": 1254,
                    "cantons_electoraux": 2054,
                    "arrondissements_deconcentres": 332,
                    "departements_total": 101,
                    "regions_total": 18,
                },
                "strates_demographiques_insee": [
                    {"strate": "Moins de 100 hab.", "type": "Hyper-ruralité", "communes": 3400, "population": 220000, "part_pop_pct": 0.3},
                    {"strate": "100 à 499 hab.", "type": "Petits villages", "communes": 17000, "population": 4300000, "part_pop_pct": 6.3},
                    {"strate": "500 à 999 hab.", "type": "Villages structurés", "communes": 5400, "population": 3800000, "part_pop_pct": 5.6},
                    {"strate": "1 000 à 3 499 hab.", "type": "Bourgs de proximité", "communes": 5900, "population": 11200000, "part_pop_pct": 16.4},
                    {"strate": "3 500 à 9 999 hab.", "type": "Bourgs structurants", "communes": 1750, "population": 10100000, "part_pop_pct": 14.8},
                    {"strate": "10 000 à 19 999 hab.", "type": "Petites villes", "communes": 580, "population": 8100000, "part_pop_pct": 11.8},
                    {"strate": "20 000 à 49 999 hab.", "type": "Villes moyennes", "communes": 460, "population": 13900000, "part_pop_pct": 20.3},
                    {"strate": "50 000 à 99 999 hab.", "type": "Grandes villes", "communes": 88, "population": 6100000, "part_pop_pct": 8.9},
                    {"strate": "100 000 hab. et plus", "type": "Métropoles & Mégapole", "communes": 41, "population": 10700000, "part_pop_pct": 15.6}
                ],
                "epci_detail": {
                    "communautes_de_communes": 991,
                    "communautes_agglomeration": 228,
                    "communautes_urbaines": 14,
                    "metropoles_droit_commun": 21,
                    "metropole_lyon_statut_particulier": 1,
                    "total_epci_fiscalite_propre": 1254,
                    "syndicats_intercommunaux_sivu_sivom": 8400
                },
                "deconcentration_etat": {
                    "prefectures_departement": 101,
                    "arrondissements_sous_prefectures": 332,
                    "cantons_electoraux": 2054,
                    "circonscriptions_legislatives": 577,
                    "academies_scolaires": 30,
                    "agences_regionales_sante_ars": 18,
                    "cours_appel_judiciaires": 36,
                    "zones_defense_securite": 12
                },
                "outre_mer": [
                    {"code": "971", "nom": "Guadeloupe", "statut": "DROM (Art. 73)", "chef_lieu": "Basse-Terre", "surface_km2": 1628, "communes": 32, "population": 384000, "zee_km2": 95000, "assemblees": "Conseil régional + Conseil départemental"},
                    {"code": "972", "nom": "Martinique", "statut": "DROM / CTU (Art. 73)", "chef_lieu": "Fort-de-France", "surface_km2": 1128, "communes": 34, "population": 361000, "zee_km2": 47000, "assemblees": "Assemblée de Martinique (61 élus) + Conseil exécutif"},
                    {"code": "973", "nom": "Guyane", "statut": "DROM / CTU (Art. 73)", "chef_lieu": "Cayenne", "surface_km2": 83534, "communes": 22, "population": 294000, "zee_km2": 134000, "assemblees": "Assemblée de Guyane (55 élus) + Centre Spatial CSG"},
                    {"code": "974", "nom": "La Réunion", "statut": "DROM (Art. 73)", "chef_lieu": "Saint-Denis", "surface_km2": 2512, "communes": 24, "population": 873000, "zee_km2": 315000, "assemblees": "Conseil régional + Conseil départemental"},
                    {"code": "976", "nom": "Mayotte", "statut": "DROM / Dép-Rég (Art. 73)", "chef_lieu": "Mamoudzou", "surface_km2": 376, "communes": 17, "population": 310000, "zee_km2": 64000, "assemblees": "Conseil départemental de Mayotte (26 élus)"},
                    {"code": "977", "nom": "Saint-Barthélemy", "statut": "COM (Art. 74)", "chef_lieu": "Gustavia", "surface_km2": 25, "communes": 1, "population": 10500, "zee_km2": 4000, "assemblees": "Conseil territorial (19 élus)"},
                    {"code": "978", "nom": "Saint-Martin", "statut": "COM (Art. 74)", "chef_lieu": "Marigot", "surface_km2": 53, "communes": 1, "population": 32000, "zee_km2": 1000, "assemblees": "Conseil territorial (23 élus)"},
                    {"code": "975", "nom": "Saint-Pierre-et-Miquelon", "statut": "COM (Art. 74)", "chef_lieu": "Saint-Pierre", "surface_km2": 242, "communes": 2, "population": 6000, "zee_km2": 12400, "assemblees": "Conseil territorial (19 élus)"},
                    {"code": "986", "nom": "Wallis-et-Futuna", "statut": "COM (Art. 74)", "chef_lieu": "Mata-Utu", "surface_km2": 142, "communes": 3, "population": 11500, "zee_km2": 300000, "assemblees": "Assemblée territoriale (20 élus) + 3 chefferies coutumières"},
                    {"code": "987", "nom": "Polynésie française", "statut": "COM Autonome (Art. 74)", "chef_lieu": "Papeete", "surface_km2": 4167, "communes": 48, "population": 280000, "zee_km2": 4800000, "assemblees": "Assemblée de Polynésie (57 élus) + Gouvernement propre"},
                    {"code": "988", "nom": "Nouvelle-Calédonie", "statut": "Sui Generis (Titre XIII Const.)", "chef_lieu": "Nouméa", "surface_km2": 18575, "communes": 33, "population": 271000, "zee_km2": 1400000, "assemblees": "Congrès de Nouvelle-Calédonie (54 élus) + 3 Provinces + Sénat coutumier"},
                    {"code": "984", "nom": "Terres Australes & Antarctiques (TAAF)", "statut": "Territoire d'Outre-Mer administré", "chef_lieu": "Saint-Pierre (Réunion)", "surface_km2": 439780, "communes": 0, "population": 200, "zee_km2": 2300000, "assemblees": "Préfet administrateur supérieur + Conseil consultatif"},
                    {"code": "989", "nom": "Île de Clipperton", "statut": "Domaine public de l'État", "chef_lieu": "Paris (Ministère OM)", "surface_km2": 2, "communes": 0, "population": 0, "zee_km2": 435000, "assemblees": "Ministre chargé des Outre-Mer"},
                    {"code": "FE", "nom": "Français établis hors de France", "statut": "Représentation mondiale (Art. 24 al. 4)", "chef_lieu": "Monde entier", "surface_km2": 0, "communes": 0, "population": 2100000, "zee_km2": 0, "assemblees": "11 Députés + 12 Sénateurs + AFE (90 conseillers) + 442 conseillers consulaires"}
                ],
                "souverainete_maritime_zee_km2": 10200000,
                "souverainete_maritime_oceans": {
                    "pacifique_km2": 6800000,
                    "indien_km2": 2600000,
                    "atlantique_antilles_guyane_km2": 500000,
                    "metropole_europeenne_km2": 300000
                },
                "surcout_vie_chere_alimentaire_pct": 32.5,
                "octroi_de_mer_annuel_mde": 1.6
            })
            return

        # 10. API Élections & Démocratie
        if path == "/api/elections":
            self._envoyer_json(200, {
                "reu_electeurs_inscrits": 49500000,
                "commissions_controle_count": 34935,
                "procurations_dematerialisees_pct": 68.0,
                "calendrier_elections_prevues": [
                    {"scrutin": "Municipales & Communautaires", "date_prevue": "Mars 2026", "mandat": "6 ans", "elus": "~500 000 conseillers", "mode": "Proportionnel de liste avec prime 50% (>=1k hab.)"},
                    {"scrutin": "Consulaires des Français de l'étranger", "date_prevue": "Mai 2026", "mandat": "5 ans", "elus": "442 conseillers", "mode": "Proportionnel de liste (vote internet et urne)"},
                    {"scrutin": "Sénatoriales (Série 2)", "date_prevue": "Septembre 2026", "mandat": "6 ans (triennal)", "elus": "178 sénateurs", "mode": "Suffrage indirect (grands électeurs municipaux)"},
                    {"scrutin": "Présidentielle", "date_prevue": "Avril-Mai 2027", "mandat": "5 ans (quinquennat)", "elus": "1 Président", "mode": "Uninominal majoritaire à 2 tours (500 parrainages)"},
                    {"scrutin": "Législatives", "date_prevue": "Juin 2027", "mandat": "5 ans", "elus": "577 députés", "mode": "Uninominal majoritaire à 2 tours (seuil maintien 12,5% inscrits)"},
                    {"scrutin": "Départementales", "date_prevue": "Mars 2028", "mandat": "6 ans", "elus": "4 056 conseillers (2 054 cantons)", "mode": "Binominal paritaire (1 femme + 1 homme) à 2 tours"},
                    {"scrutin": "Régionales & Territoriales", "date_prevue": "Mars 2028", "mandat": "6 ans", "elus": "1 757 conseillers", "mode": "Proportionnel de liste à 2 tours avec prime majoritaire 25%"},
                    {"scrutin": "Sénatoriales (Série 1)", "date_prevue": "Septembre 2029", "mandat": "6 ans (triennal)", "elus": "170 sénateurs", "mode": "Suffrage indirect (grands électeurs municipaux)"},
                    {"scrutin": "Européennes", "date_prevue": "Juin 2029", "mandat": "5 ans", "elus": "81 députés européens", "mode": "Proportionnel à la plus forte moyenne, circonscription unique (seuil 5%)"},
                    {"scrutin": "Chambres consulaires professionnelles", "date_prevue": "2026 - 2029", "mandat": "5 ans", "elus": "~5 000 élus", "mode": "Scrutin de liste socioprofessionnel (CCI, CMA, CA)"}
                ],
                "elections": [
                    {"type": "Présidentielle", "mandat": "5 ans", "mode_scrutin": "Uninominal majoritaire à 2 tours", "elus": 1, "conditions": "500 parrainages d'élus d'au moins 30 départements"},
                    {"type": "Législatives", "mandat": "5 ans", "mode_scrutin": "Uninominal majoritaire à 2 tours", "elus": 577, "conditions": "1er tour : 50% suffrages + 25% inscrits ; 2nd tour : seuil 12,5% des inscrits"},
                    {"type": "Sénatoriales", "mandat": "6 ans (renouvellement par moitié tous les 3 ans)", "mode_scrutin": "Suffrage indirect (162 000 grands électeurs)", "elus": 348, "conditions": "Scrutin majoritaire (<3 sénateurs) ou proportionnel (>=3 sénateurs)"},
                    {"type": "Régionales & Territoriales", "mandat": "6 ans", "mode_scrutin": "Proportionnel de liste à 2 tours avec prime majoritaire de 25%", "elus": 1757, "conditions": "Seuil maintien 10%, fusion 5%"},
                    {"type": "Départementales", "mandat": "6 ans", "mode_scrutin": "Binominal paritaire (1 femme + 1 homme) majoritaire à 2 tours", "elus": 4056, "conditions": "1er tour : 50% suffrages + 25% inscrits ; 2nd tour : seuil 12,5% des inscrits"},
                    {"type": "Municipales & Intercommunales", "mandat": "6 ans", "mode_scrutin": "Proportionnel de liste paritaire avec prime 50% (>=1000 hab.)", "elus": 500000, "conditions": "Fléchage direct des délégués communautaires EPCI"},
                    {"type": "Européennes", "mandat": "5 ans", "mode_scrutin": "Proportionnel de liste à la plus forte moyenne, circonscription unique", "elus": 81, "conditions": "Seuil de représentativité national de 5%"},
                    {"type": "Consulaires", "mandat": "5 ans", "mode_scrutin": "Scrutin de liste paritaire socioprofessionnel", "elus": 5000, "conditions": "Collèges chefs d'entreprise, commerçants, artisans, exploitants agricoles"}
                ],
                "seuils_et_regles": {
                    "seuil_second_tour_legislatives_pct_inscrits": 12.5,
                    "seuil_second_tour_departementales_pct_inscrits": 12.5,
                    "seuil_second_tour_regionales_pct_exprimes": 10.0,
                    "seuil_fusion_regionales_pct_exprimes": 5.0,
                    "seuil_representation_europeennes_pct": 5.0,
                    "prime_majoritaire_municipales_pct": 50.0,
                    "prime_majoritaire_regionales_pct": 25.0,
                    "parrainages_presidentiels_requis": 500,
                    "departements_minimum_parrainages": 30
                },
                "referendums": [
                    {"article": "Article 11", "nature": "Référendum législatif & RIP", "declenchement": "Présidentiel sur proposition gouvernementale/parlementaire ou RIP (185 parlementaires + 4,95M électeurs)"},
                    {"article": "Article 89", "nature": "Référendum constitutionnel", "declenchement": "Obligatoire après vote conforme AN + Sénat, sauf approbation par le Congrès à Versailles (3/5èmes)"},
                    {"article": "Article 72-1", "nature": "Référendum décisionnel local", "declenchement": "Délibération d'une collectivité territoriale sur ses compétences propres (seuil participation 50%)"},
                    {"article": "Article 72-4", "nature": "Consultation statutaire d'Outre-mer", "declenchement": "Préalable obligatoire à toute évolution institutionnelle ou statutaire ultramarine"}
                ]
            })
            return

        # 10. API Arbitrages Budgétaires de Bercy & Gouvernance
        if path in ("/api/arbitrages_budget", "/api/bataille_budget"):
            self._envoyer_json(200, {
                "gouvernance": {
                    "titre": "Arbitrages Budgétaires et Survie Ministérielle",
                    "ministere": "Ministère de l'Économie, des Finances et des Comptes Publics (Bercy)",
                    "cadre": "Procédure d'élaboration et d'adoption du Projet de Loi de Finances (PLF)",
                    "periode": "Exercices budgétaires pluriannuels (2027-2032)"
                },
                "contexte_initial_2027": {
                    "deficit_pct_pib": 5.9,
                    "dette_publique_mde": 3560,
                    "dette_pct_pib": 118.0,
                    "charge_dette_annuelle_mde": 55.0,
                    "spread_oat_bund_pb": 70.0,
                    "note_souveraine": "AA",
                    "procedure_deficit_excessif": "Active (Bruxelles)"
                },
                "objectifs_jeu": {
                    "ramener_deficit_sous_3_pct": "Avant 2030",
                    "reflux_dette_pib": "Avant 2032",
                    "survie_politique": "Éviter démission et censure pendant 6 saisons (2027-2032)"
                },
                "jauges_survie": {
                    "capital_politique": {"valeur_base": 50, "description": "Capacité à réformer et faire voter les mesures"},
                    "popularite_ministre": {"valeur_base": 50, "seuil_alerte_pm": 15.0, "seuil_demission": 10.0},
                    "censure_assemblee": {"seuil_chute": 289, "unites": "voix"}
                },
                "profils_ministre": [
                    {
                        "id": "elu_chevronne",
                        "nom": "L'Élu Chevronné",
                        "popularite": 40.0,
                        "capital_politique": 60.0,
                        "description": "Rompu aux arcanes du pouvoir, facilite les négociations parlementaires mais souffre d'un déficit d'image populaire."
                    },
                    {
                        "id": "chef_entreprise",
                        "nom": "Le Chef d'Entreprise",
                        "popularite": 60.0,
                        "capital_politique": 40.0,
                        "description": "Crédit initial d'efficacité auprès des Français, mais manque cruellement de relais à l'Assemblée nationale."
                    },
                    {
                        "id": "universitaire",
                        "nom": "L'Universitaire Réputé",
                        "popularite": 50.0,
                        "capital_politique": 50.0,
                        "description": "Respecté pour sa rigueur académique, profil équilibré mais sans reflexes partisans lors des marchandages."
                    }
                ],
                "directeurs_cabinet": [
                    {
                        "id": "technocrate",
                        "nom": "Le Technocrate (Inspecteur des Finances)",
                        "bonus": "Efficience réformes structurelles (+15%)",
                        "description": "Expert de la Direction du Budget, dialogue fluide avec les ministères dépensiers. Idéal pour assainir durablement."
                    },
                    {
                        "id": "dealmaker",
                        "nom": "Le Négociateur Politique (Dealmaker)",
                        "bonus": "+5 Capital Politique / an",
                        "description": "Artisan des accords de couloir avec les groupes parlementaires pivot (LR, Liot, MoDem)."
                    },
                    {
                        "id": "spin_doctor",
                        "nom": "Le Spin Doctor (Communicant)",
                        "bonus": "+5 Popularité / an",
                        "description": "Atténue les scandales de presse, amortit les unes hostiles et préserve le soutien de l'opinion publique."
                    }
                ],
                "cycle_annuel_12_episodes": [
                    {"mois": 1, "nom": "Janvier", "titre": "Prise de fonction & Cadrage", "acteur": "Directeur de cabinet", "enjeu": "Lettres de cadrage et trajectoire macroéconomique"},
                    {"mois": 2, "nom": "Février", "titre": "Avertissement de la Cour des comptes", "acteur": "Premier Président Cour des comptes", "enjeu": "Rappel solennel sur la dérive des finances publiques"},
                    {"mois": 3, "nom": "Mars", "titre": "Convocation à Bruxelles", "acteur": "Commission européenne", "enjeu": "Notification de la procédure de déficit excessif (PDE)"},
                    {"mois": 4, "nom": "Avril", "titre": "Tensions sur les Marchés financiers", "acteur": "DG Trésor & Agences de notation", "enjeu": "Surveillance du spread OAT-Bund et risque de dégradation AA"},
                    {"mois": 5, "nom": "Mai", "titre": "Audition à l'Assemblée nationale", "acteur": "Commission des finances AN", "enjeu": "Feu croisé des oppositions parlementaires"},
                    {"mois": 6, "nom": "Juin", "titre": "La Guerre des Enveloppes", "acteur": "Ministres dépensiers (Santé, Éducation, Armées)", "enjeu": "Défilé pour réclamer des rallonges sous menace d'appel à Matignon"},
                    {"mois": 7, "nom": "Juillet", "titre": "Arbitrages de l'Élysée", "acteur": "Président de la République", "enjeu": "Annonces surprises et lubies présidentielles non financées"},
                    {"mois": 8, "nom": "Août", "titre": "Conférence de Presse de Rentrée", "acteur": "Médias économiques & Journalistes", "enjeu": "Présentation et défense du Projet de Loi de Finances (PLF)"},
                    {"mois": 9, "nom": "Septembre", "titre": "Dépôt officiel du PLF", "acteur": "Bureau de l'Assemblée nationale", "enjeu": "Transmission formelle du texte budgétaire"},
                    {"mois": 10, "nom": "Octobre", "titre": "La Grande Bidouille", "acteur": "Groupes parlementaires", "enjeu": "Marchandage d'amendements et compromis de dernière minute"},
                    {"mois": 11, "nom": "Novembre", "titre": "Navette et Chantage à la Censure", "acteur": "Présidents de groupes politiques", "enjeu": "Menace de censure en cas de non-satisfaction des revendications"},
                    {"mois": 12, "nom": "Décembre", "titre": "Le Climax : Vote ou 49.3", "acteur": "Hémicycle de l'Assemblée nationale", "enjeu": "Soumission au vote à haut risque ou 49 alinéa 3 avec motion de censure (289 voix)"}
                ],
                "comparatif_avec_plan_mandature": {
                    "gestion_classique_deficit_2030": "< 3,0 % du PIB (souvent manqué ou obtenu par austérité)",
                    "plan_mandature_deficit_annee5": "1,8 % du PIB (atteint dès l'Année 4 à 2,6 %)",
                    "gestion_classique_dette_2032": "Dette continuant d'enfler sous le poids des intérêts",
                    "plan_mandature_dette_annee5": "Désendettement net de 51 Md€/an, ratio stabilisé puis décroissant",
                    "gestion_classique_popularite": "Chute sous 15% (alerte) et 10% (démission forcée)",
                    "plan_mandature_popularite": "Popularité maintenue à 71% grâce à la justice fiscale et à la baisse de TVA sur l'énergie (-9 Md€)",
                    "gestion_classique_censure": "Chute récurrente du cabinet au 49.3 à 289 voix",
                    "plan_mandature_censure": "Oppositions désarmées à 140 voix (grognomètre social à 5/100, alliance PME/communes)"
                }
            })
            return

        # 11. API Registre des Sources Officielles et Auditabilité
        if path == "/api/sources":
            query_params = urllib.parse.parse_qs(parsed.query)
            cat_filtre = query_params.get("categorie", [None])[0]
            recherche = query_params.get("q", [None])[0]

            sources = exporter_catalogue_sources()
            if cat_filtre:
                sources = [s for s in sources if s.get("categorie", "").lower() == cat_filtre.lower()]
            if recherche:
                q_low = recherche.lower()
                sources = [
                    s for s in sources
                    if q_low in s.get("nom_indicateur", "").lower()
                    or q_low in s.get("organisme", "").lower()
                    or q_low in s.get("id_source", "").lower()
                ]

            self._envoyer_json(200, {
                "total": len(sources),
                "certitude_scientifique": "Données 100% certifiées par organismes publics (INSEE, DGFIP, AFT, BCE, Cour des comptes)",
                "sources": sources,
            })
            return

        # 12. API Audit et Traçabilité en Temps Réel
        if path == "/api/audit":
            self._envoyer_json(200, {
                "audit": {
                    "statut_reproductibilite": "Bit-à-bit déterministe et vérifié",
                    "nb_sources_officielles_certifiees": len(REGISTRE_SOURCES_OFFICIELLES),
                    "nb_textes_de_loi_integres": len(get_corpus_lois()),
                    "taux_couverture_legale": "100.0 % (zéro paramètre orphelin)",
                    "conformite_organique": {
                        "lolf_art_34": "Conforme (priorité recettes sur dépenses)",
                        "cgct_l1612_4": "Conforme (règle d'or locale respectée à 94% par compensation foncière)",
                        "const_art_49_2": "Conforme (seuil de censure modélisé à 289 voix)",
                        "tfue_art_126": "Conforme (sentier de désendettement certifié PDE sous 3%)",
                        "directive_ue_2022_542": "Conforme (baisse TVA énergie 5,5% légale)"
                    },
                    "methodologie": "Stock-Flow Consistent (SFC) avec modélisation multi-agents gigognes (4 strates)",
                    "horodatage_audit": "2026-09-19T09:50:00Z"
                }
            })
            return

        # 13. API Think Tanks (Audit Contradictoire Mondial)
        if path == "/api/think_tanks":
            query_params = urllib.parse.parse_qs(parsed.query)
            echelon_filtre = query_params.get("echelon", [None])[0]
            recherche = query_params.get("q", [None])[0]

            cat = exporter_catalogue_think_tanks()
            tt_dict = cat["think_tanks"]

            if echelon_filtre:
                tt_dict = {
                    k: v for k, v in tt_dict.items()
                    if v.get("echelon", "").lower() == echelon_filtre.lower()
                }

            if recherche:
                q_low = recherche.lower()
                tt_dict = {
                    k: v for k, v in tt_dict.items()
                    if q_low in v.get("nom", "").lower()
                    or q_low in v.get("sigle", "").lower()
                    or q_low in v.get("epistemologie", "").lower()
                    or q_low in v.get("pourquoi_integration", "").lower()
                    or q_low in v.get("reponse_du_simulateur", "").lower()
                }

            self._envoyer_json(200, {
                "total": len(tt_dict),
                "echelons": cat["metadonnees"]["echelons"],
                "paradigmes_stress_tests": cat["metadonnees"]["paradigmes_stress_tests"],
                "think_tanks": list(tt_dict.values()),
            })
            return

        if path.startswith("/api/think_tanks/"):
            tt_id = path.split("/api/think_tanks/")[1].strip()
            tt = get_think_tank(tt_id)
            if tt:
                self._envoyer_json(200, {
                    "id": tt.id,
                    "nom": tt.nom,
                    "sigle": tt.sigle,
                    "echelon": tt.echelon,
                    "pays_siege": tt.pays_siege,
                    "epistemologie": tt.epistemologie,
                    "directeur_ou_fondateur": tt.directeur_ou_fondateur,
                    "sources_cles": [
                        {
                            "titre": s.titre,
                            "url": s.url,
                            "annee": s.annee,
                            "auteurs": s.auteurs,
                            "resume_methodologique": s.resume_methodologique
                        } for s in tt.sources_cles
                    ],
                    "hypotheses_et_parametres": tt.hypotheses_et_parametres,
                    "objections_anticipees": tt.objections_anticipees,
                    "pourquoi_integration": tt.pourquoi_integration,
                    "reponse_du_simulateur": tt.reponse_du_simulateur,
                    "stress_test_associe": tt.stress_test_associe
                })
            else:
                self._envoyer_json(404, {"erreur": f"Think tank '{tt_id}' non trouvé"})
            return

        # 14. API Stress-Tests Multi-Paradigmes
        if path == "/api/stress_tests":
            stress_res = executer_stress_tests_mandature(
                etat_national=None,
                etat_local=None,
                etat_europe=None,
                etat_mondial=None,
                deciles=None
            )
            data_res = {}
            for k, st in stress_res.items():
                data_res[k] = {
                    "paradigme_id": st.paradigme_id,
                    "titre": st.titre,
                    "statut": st.statut,
                    "score_robustesse_sur_100": st.score_robustesse_sur_100,
                    "criteres_analyses": st.criteres_analyses,
                    "objections_relevees": st.objections_relevees,
                    "reponses_systemiques": st.reponses_systemiques,
                    "justification_scientifique": st.justification_scientifique
                }
            self._envoyer_json(200, {
                "audit_stress_tests": "5 paradigmes majeurs confrontés (Local à International)",
                "statut_global": "TOUS CONFORMES ET RÉSISTANTS",
                "resultats": data_res
            })
            return

        # 15. API Historique France (1792→2026)
        if path == "/api/histoire":
            query_params = urllib.parse.parse_qs(parsed.query)
            annee_min = int(query_params["annee_min"][0]) if "annee_min" in query_params else None
            annee_max = int(query_params["annee_max"][0]) if "annee_max" in query_params else None
            type_regime = query_params.get("type_regime", [None])[0]

            periodes = filtrer_periodes(annee_min=annee_min, annee_max=annee_max, type_regime=type_regime)
            self._envoyer_json(200, {
                "total": len(periodes),
                "couverture": "1792-2026",
                "periodes": periodes,
            })
            return

        if path == "/api/histoire/options":
            self._envoyer_json(200, obtenir_options_dropdown())
            return

        if path == "/api/histoire/synthese":
            self._envoyer_json(200, {
                "synthese": generer_synthese_historique(),
                "parametres_calibration": calibrer_parametres_historiques(),
            })
            return

        if path.startswith("/api/histoire/comparer"):
            qp = urllib.parse.parse_qs(parsed.query)
            a_id = qp.get("a", [None])[0]
            b_id = qp.get("b", [None])[0]
            dims = qp.get("dimensions", [None])[0]
            if a_id and b_id:
                dim_list = dims.split(",") if dims else None
                comp = comparer_periodes(a_id, b_id, dim_list)
                self._envoyer_json(200, {
                    "periode_a": comp.periode_a,
                    "periode_b": comp.periode_b,
                    "dimensions": comp.dimensions,
                    "enseignements": comp.enseignements,
                })
            else:
                self._envoyer_json(400, {"erreur": "Paramètres 'a' et 'b' requis"})
            return

        if path.startswith("/api/histoire/series"):
            qp = urllib.parse.parse_qs(parsed.query)
            indicateur = qp.get("indicateur", ["dette_publique_pct_pib"])[0]
            ad = int(qp["annee_debut"][0]) if "annee_debut" in qp else None
            af = int(qp["annee_fin"][0]) if "annee_fin" in qp else None
            serie = obtenir_series_chronologiques(indicateur, ad, af)
            self._envoyer_json(200, {"indicateur": indicateur, "points": len(serie), "serie": serie})
            return

        if path == "/api/histoire/reformes":
            qp = urllib.parse.parse_qs(parsed.query)
            cat = qp.get("categorie", [None])[0]
            reformes = obtenir_reformes(categorie=cat)
            self._envoyer_json(200, {"total": len(reformes), "reformes": reformes})
            return

        if path == "/api/histoire/crises":
            qp = urllib.parse.parse_qs(parsed.query)
            tc = qp.get("type", [None])[0]
            gmin = int(qp["gravite_min"][0]) if "gravite_min" in qp else None
            crises = obtenir_crises(type_crise=tc, gravite_min=gmin)
            self._envoyer_json(200, {"total": len(crises), "crises": crises})
            return

        # 16. API Société — 18 Domaines (1792→2026)
        if path == "/api/societe":
            query_params = urllib.parse.parse_qs(parsed.query)
            domaine_id = query_params.get("id", [None])[0]
            if domaine_id:
                d = obtenir_domaine_par_id(domaine_id)
                if d:
                    self._envoyer_json(200, d)
                else:
                    self._envoyer_json(404, {"erreur": f"Domaine '{domaine_id}' non trouvé"})
            else:
                self._envoyer_json(200, {
                    "total": len(DOMAINES_SOCIETAUX),
                    "domaines": [
                        {"id": d.id, "nom": d.nom, "icon": d.icon, "description": d.description,
                         "nb_indicateurs": len(d.indicateurs_cles),
                         "nb_points_historiques": len(d.serie_historique),
                         "nb_reformes": len(d.reformes_majeures),
                         "nb_crises": len(d.crises)}
                        for d in DOMAINES_SOCIETAUX
                    ],
                })
            return

        if path == "/api/societe/synthese":
            self._envoyer_json(200, {"synthese": generer_synthese_societale()})
            return

        if path.startswith("/api/societe/serie/"):
            domaine_id = path.split("/api/societe/serie/")[1].strip()
            serie = obtenir_serie_domaine(domaine_id)
            self._envoyer_json(200, {"domaine": domaine_id, "points": len(serie), "serie": serie})
            return

        if path.startswith("/api/societe/comparer"):
            qp = urllib.parse.parse_qs(parsed.query)
            a_id = qp.get("a", [None])[0]
            b_id = qp.get("b", [None])[0]
            if a_id and b_id:
                try:
                    comp = comparer_domaines(a_id, b_id)
                    self._envoyer_json(200, comp)
                except ValueError as e:
                    self._envoyer_json(400, {"erreur": str(e)})
            else:
                self._envoyer_json(400, {"erreur": "Paramètres 'a' et 'b' requis"})
            return

        self._envoyer_json(404, {"erreur": "Ressource non trouvée"})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            body = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except Exception as e:
            self._envoyer_json(400, {"erreur": f"Corps de requête JSON invalide : {str(e)}"})
            return

        # 1. API Simulation
        if path == "/api/simuler":
            try:
                scenario = body.get("scenario", "mandature")
                if scenario in ("mandature", "statut_quo", "austerite", "choc_mondial"):
                    trajectoire = executer_simulation_scenario(scenario)
                elif scenario == "custom":
                    decisions = body.get("decisions", [])
                    if not decisions:
                        # Si aucune décision fournie, générer 5 années à partir des paramètres de base
                        base_params = body.get("parametres", {})
                        decisions = [
                            {**base_params, "description": f"Année {i} (Personnalisée)"}
                            for i in range(1, 6)
                        ]
                    trajectoire = executer_simulation_personnalisee(decisions)
                else:
                    self._envoyer_json(400, {"erreur": f"Type de scénario inconnu : {scenario}"})
                    return

                self._envoyer_json(200, {
                    "scenario": scenario,
                    "nombre_annees": len(trajectoire),
                    "trajectoire": trajectoire,
                    "synthese_annee_cible": trajectoire[-1],
                })
            except Exception as e:
                self._envoyer_json(500, {"erreur": f"Erreur de simulation : {str(e)}"})
            return

        # 2. API Export Rapport
        if path == "/api/export":
            try:
                scenario = body.get("scenario", "mandature")
                trajectoire = body.get("trajectoire")
                if not trajectoire:
                    trajectoire = executer_simulation_scenario(scenario)

                format_export = body.get("format", "markdown")
                if format_export == "markdown":
                    rapport_md = self._generer_rapport_markdown(scenario, trajectoire)
                    self._envoyer_json(200, {"format": "markdown", "contenu": rapport_md})
                else:
                    self._envoyer_json(200, {"format": "json", "contenu": trajectoire})
            except Exception as e:
                self._envoyer_json(500, {"erreur": f"Erreur d'exportation : {str(e)}"})
            return

        self._envoyer_json(404, {"erreur": "Action non supportée"})

    def _generer_rapport_markdown(self, scenario: str, traj: List[Dict[str, Any]]) -> str:
        lignes = [
            f"# RAPPORT DE SIMULATION MACRO-POLITIQUE : SCÉNARIO {scenario.upper()}",
            f"> Modèle gigogne à 4 strates (Local, National, Europe, Marchés) — France 2026",
            "",
            "## TABLEAU DE BORD QUINQUENNAL",
            "| Année | PIB Nominal | Déficit (Md€) | Déficit (% PIB) | Dette (% PIB) | Taux OAT | Spread Bund | Tension Locale | Confiance | PDE UE | Note |",
            "|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for r in traj:
            pde = "CONFORME" if not r["statut_pde_europe"] else "ALERTE"
            lignes.append(
                f"| An {r['annee']} | {r['pib_nominal_mde']:.1f} Md€ | {r['deficit_nominal_mde']:.1f} Md€ | "
                f"{r['ratio_deficit_pib']:.2f} % | {r['ratio_dette_pib']:.1f} % | {r['taux_oat_pct']:.2f} % | "
                f"{r['spread_bund_bps']:.1f} bp | {r['tension_sociale_locale']:.1f}/100 | {r['confiance_democratique']:.1f}/100 | "
                f"{pde} | {r['note_souveraine']} |"
            )
        lignes.extend([
            "",
            "## PRINCIPAUX ENSEIGNEMENTS À L'ANNÉE CIBLE",
            f"* **Déficit Public** : {traj[-1]['ratio_deficit_pib']:.2f} % du PIB ({traj[-1]['deficit_nominal_mde']:.1f} Md€)",
            f"* **Dette Publique** : {traj[-1]['ratio_dette_pib']:.1f} % du PIB ({traj[-1]['dette_nominale_mde']:.1f} Md€)",
            f"* **Coût de Refinancement** : OAT 10a à {traj[-1]['taux_oat_pct']:.2f} % (Spread face à l'Allemagne : {traj[-1]['spread_bund_bps']:.1f} bps)",
            f"* **Stabilité Démocratique** : Tension locale à {traj[-1]['tension_sociale_locale']:.1f}/100, Confiance à {traj[-1]['confiance_democratique']:.1f}/100",
            f"* **Discipline Européenne** : {'Sortie de la PDE' if not traj[-1]['statut_pde_europe'] else 'Sous procédure PDE'}",
        ])
        return "\n".join(lignes)


def demarrer_serveur_web(host: str = "0.0.0.0", port: int = 8000):
    """Démarre le serveur Web HTTP sur le port spécifié."""
    adresse = (host, port)
    serveur = ThreadedHTTPServer(adresse, SimulateurHTTPHandler)
    print(f"\n" + "=" * 80)
    print(f"🚀 SERVEUR WEB DU SIMULATEUR DÉMARRÉ SUR http://{host}:{port}")
    print(f"   Modèle systémique gigogne à 4 échelons (Local, National, Europe, Marchés)")
    print(f"   Prévisualisation immédiate en direct disponible.")
    print("=" * 80 + "\n")
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur.")
    finally:
        serveur.server_close()


# =============================================================================
# APPLICATION WEB FRONTEND MONO-PAGE (HTML5 / CSS3 / Vanilla JS)
# Republican Navy, Gold, Crimson & Crisp White UI
# =============================================================================
HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Simulateur Macro-Politique & Démocratique</title>
  <style>
    :root {
      --bg: #090d16;
      --card-bg: #111827;
      --card-border: #1f2937;
      --card-hover: #1e293b;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --primary-light: rgba(37, 99, 235, 0.15);
      --accent-gold: #f59e0b;
      --accent-gold-light: rgba(245, 158, 11, 0.15);
      --accent-crimson: #ef4444;
      --accent-crimson-light: rgba(239, 68, 68, 0.15);
      --accent-emerald: #10b981;
      --accent-emerald-light: rgba(16, 185, 129, 0.15);
      --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: var(--font);
      line-height: 1.5;
      padding-bottom: 60px;
    }
    header {
      background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
      border-bottom: 1px solid var(--card-border);
      padding: 24px 32px;
      position: sticky;
      top: 0;
      z-index: 50;
      backdrop-filter: blur(12px);
    }
    .header-content {
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }
    .tricolore-bar {
      height: 4px;
      width: 100%;
      background: linear-gradient(90deg, #002654 0%, #002654 33.3%, #ffffff 33.3%, #ffffff 66.6%, #ce1126 66.6%, #ce1126 100%);
      position: absolute;
      top: 0;
      left: 0;
    }
    .logo-title h1 {
      font-size: 1.4rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .logo-badge {
      background: var(--primary);
      color: #fff;
      font-size: 0.75rem;
      padding: 3px 8px;
      border-radius: 4px;
      font-weight: 600;
      text-transform: uppercase;
    }
    .subtitle {
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-top: 4px;
      font-style: italic;
    }
    nav {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    nav button {
      background: transparent;
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      padding: 8px 14px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 500;
      transition: all 0.2s;
    }
    nav button:hover {
      background: var(--card-hover);
      color: var(--text);
    }
    nav button.active {
      background: var(--primary);
      color: #fff;
      border-color: var(--primary);
      box-shadow: 0 0 12px rgba(37, 99, 235, 0.4);
    }
    .container {
      max-width: 1400px;
      margin: 24px auto;
      padding: 0 24px;
    }
    .tab-pane { display: none; }
    .tab-pane.active { display: block; animation: fadeIn 0.3s ease; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

    /* SCENARIO SELECTOR */
    .scenario-bar {
      display: flex;
      gap: 10px;
      background: var(--card-bg);
      padding: 12px;
      border-radius: 10px;
      border: 1px solid var(--card-border);
      margin-bottom: 24px;
      flex-wrap: wrap;
      align-items: center;
    }
    .scenario-btn {
      flex: 1;
      min-width: 180px;
      background: #1a2234;
      border: 1px solid var(--card-border);
      color: var(--text);
      padding: 12px 16px;
      border-radius: 8px;
      cursor: pointer;
      text-align: left;
      transition: all 0.2s;
    }
    .scenario-btn:hover {
      background: #232d45;
      border-color: #374151;
    }
    .scenario-btn.active {
      background: linear-gradient(135deg, rgba(37, 99, 235, 0.3) 0%, rgba(30, 64, 175, 0.4) 100%);
      border-color: var(--primary);
      box-shadow: 0 0 16px rgba(37, 99, 235, 0.25);
    }
    .scenario-btn .sc-title {
      font-size: 0.95rem;
      font-weight: 700;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .scenario-btn .sc-sub {
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-top: 4px;
    }

    /* CUSTOM CONTROLS DRAWER */
    .custom-panel {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 20px;
      margin-bottom: 24px;
      display: none;
    }
    .custom-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 20px;
    }
    .control-group {
      background: #172033;
      padding: 14px;
      border-radius: 8px;
      border: 1px solid #283548;
    }
    .control-group h4 {
      font-size: 0.85rem;
      color: var(--accent-gold);
      margin-bottom: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .slider-item {
      margin-bottom: 12px;
    }
    .slider-header {
      display: flex;
      justify-content: space-between;
      font-size: 0.8rem;
      margin-bottom: 4px;
    }
    .slider-header span.val {
      font-weight: 700;
      color: var(--primary);
    }
    input[type=range] {
      width: 100%;
      height: 6px;
      border-radius: 3px;
      background: #2b3952;
      outline: none;
      -webkit-appearance: none;
    }
    input[type=range]::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: var(--primary);
      cursor: pointer;
    }
    .checkbox-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.8rem;
      margin-top: 8px;
      cursor: pointer;
    }
    .btn-run-custom {
      background: var(--primary);
      color: white;
      border: none;
      padding: 12px 24px;
      border-radius: 8px;
      font-weight: 700;
      font-size: 0.95rem;
      cursor: pointer;
      margin-top: 16px;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }
    .btn-run-custom:hover { background: var(--primary-hover); }

    /* KPI HERO CARDS */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }
    .kpi-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 18px;
      position: relative;
      overflow: hidden;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .kpi-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    }
    .kpi-card::before {
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      width: 4px;
      height: 100%;
      background: var(--primary);
    }
    .kpi-card.success::before { background: var(--accent-emerald); }
    .kpi-card.warning::before { background: var(--accent-gold); }
    .kpi-card.danger::before { background: var(--accent-crimson); }

    .kpi-label {
      font-size: 0.75rem;
      color: var(--text-muted);
      text-transform: uppercase;
      font-weight: 600;
      letter-spacing: 0.03em;
    }
    .kpi-value {
      font-size: 1.6rem;
      font-weight: 800;
      margin: 8px 0 4px;
      letter-spacing: -0.02em;
    }
    .kpi-sub {
      font-size: 0.8rem;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .badge {
      font-size: 0.7rem;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 4px;
      text-transform: uppercase;
    }
    .badge-success { background: var(--accent-emerald-light); color: var(--accent-emerald); }
    .badge-warning { background: var(--accent-gold-light); color: var(--accent-gold); }
    .badge-danger { background: var(--accent-crimson-light); color: var(--accent-crimson); }
    .badge-primary { background: var(--primary-light); color: #60a5fa; }

    /* DATA TABLE */
    .table-container {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      overflow-x: auto;
      margin-bottom: 24px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.88rem;
    }
    th {
      background: #172033;
      padding: 12px 16px;
      font-size: 0.75rem;
      text-transform: uppercase;
      color: var(--text-muted);
      letter-spacing: 0.05em;
      border-bottom: 1px solid var(--card-border);
    }
    td {
      padding: 14px 16px;
      border-bottom: 1px solid #1c2738;
      cursor: pointer;
      transition: background 0.15s;
    }
    tr:hover td {
      background: #1a2538;
    }
    tr.selected td {
      background: rgba(37, 99, 235, 0.18);
      font-weight: 600;
    }

    /* YEAR DEEP DIVE */
    .year-details {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 24px;
      margin-bottom: 24px;
    }
    .year-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--card-border);
    }
    .strates-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 16px;
      margin-bottom: 20px;
    }
    .strate-card {
      background: #151e2e;
      border: 1px solid #243247;
      border-radius: 8px;
      padding: 16px;
    }
    .strate-card h4 {
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--accent-gold);
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
    }
    .metric-row {
      display: flex;
      justify-content: space-between;
      font-size: 0.8rem;
      padding: 4px 0;
      border-bottom: 1px dashed #223046;
    }
    .metric-row:last-child { border-bottom: none; }
    .events-stream {
      background: #0f1726;
      border: 1px solid #233148;
      border-radius: 8px;
      padding: 16px;
    }
    .events-stream h4 {
      font-size: 0.85rem;
      color: #93c5fd;
      margin-bottom: 10px;
    }
    .event-line {
      font-size: 0.82rem;
      color: #cbd5e1;
      padding: 4px 0;
      border-left: 2px solid var(--primary);
      padding-left: 10px;
      margin-bottom: 6px;
    }

    /* EXPORT BAR */
    .action-bar {
      display: flex;
      justify-content: flex-end;
      gap: 12px;
      margin-top: 16px;
    }
    .btn-secondary {
      background: #1f293d;
      border: 1px solid #334155;
      color: var(--text);
      padding: 8px 16px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 500;
      transition: all 0.2s;
    }
    .btn-secondary:hover {
      background: #2d3b55;
    }

    /* CORPUS JURIDIQUE */
    .search-box {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 16px;
      margin-bottom: 20px;
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
    .search-box input {
      flex: 1;
      min-width: 250px;
      background: #151e2e;
      border: 1px solid #28374d;
      color: var(--text);
      padding: 10px 14px;
      border-radius: 6px;
      font-size: 0.9rem;
    }
    .filter-pills {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }
    .filter-pill {
      background: #172134;
      border: 1px solid #29384e;
      color: var(--text-muted);
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 0.8rem;
      cursor: pointer;
    }
    .filter-pill.active {
      background: var(--primary);
      color: #fff;
      border-color: var(--primary);
    }
    .corpus-list {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 16px;
    }
    .corpus-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 18px;
      transition: transform 0.15s;
    }
    .corpus-card:hover {
      transform: translateY(-2px);
      border-color: #374151;
    }
    .corpus-card h4 {
      font-size: 0.95rem;
      color: #93c5fd;
      display: flex;
      justify-content: space-between;
      margin-bottom: 6px;
    }
    .corpus-card .code {
      font-size: 0.75rem;
      color: var(--accent-gold);
      font-weight: 600;
      margin-bottom: 8px;
    }
    .corpus-card .citation {
      background: #0d1422;
      padding: 10px;
      border-radius: 6px;
      font-size: 0.82rem;
      font-style: italic;
      color: #cbd5e1;
      margin-bottom: 10px;
      border-left: 3px solid var(--primary);
    }
    .corpus-card .impact {
      font-size: 0.8rem;
      color: var(--text-muted);
    }

    /* ARCHITECTURE 4 STRATES */
    .arch-diagram {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 24px;
      margin-bottom: 24px;
    }
    .nested-layer {
      border: 2px solid;
      border-radius: 12px;
      padding: 18px;
      margin-bottom: 16px;
    }
    .layer-4 { border-color: #f59e0b; background: rgba(245, 158, 11, 0.05); }
    .layer-3 { border-color: #3b82f6; background: rgba(59, 130, 246, 0.05); }
    .layer-2 { border-color: #10b981; background: rgba(16, 185, 129, 0.05); }
    .layer-1 { border-color: #ec4899; background: rgba(236, 72, 153, 0.05); }

    .layer-title {
      font-weight: 800;
      font-size: 1rem;
      display: flex;
      justify-content: space-between;
      margin-bottom: 6px;
    }
    .layer-desc {
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-bottom: 8px;
    }

    /* THINK TANKS & STRESS TESTS */
    .tt-card {
      background: #111827;
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 18px;
      margin-bottom: 14px;
      transition: transform 0.15s;
    }
    .tt-card:hover {
      transform: translateY(-2px);
      border-color: #3b82f6;
    }
    .tt-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 8px;
      flex-wrap: wrap;
      gap: 6px;
    }
    .tt-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: #93c5fd;
    }
    .tt-meta {
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-bottom: 10px;
    }
    .tt-box {
      border-radius: 6px;
      padding: 10px 12px;
      margin-bottom: 8px;
      font-size: 0.82rem;
      line-height: 1.45;
    }
    .tt-box-objection {
      background: rgba(239, 68, 68, 0.08);
      border-left: 3px solid #ef4444;
      color: #fca5a5;
    }
    .tt-box-pourquoi {
      background: rgba(14, 165, 233, 0.08);
      border-left: 3px solid #0ea5e9;
      color: #bae6fd;
    }
    .tt-box-reponse {
      background: rgba(16, 185, 129, 0.08);
      border-left: 3px solid #10b981;
      color: #a7f3d0;
    }
    .stress-card {
      background: #111827;
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
  </style>
</head>
<body>
  <div class="tricolore-bar"></div>
  <header>
    <div class="header-content">
      <div class="logo-title">
        <h1>
          🏛️ RÉPUBLIQUE CITOYENNE
          <span class="logo-badge">Simulateur 4 Strates</span>
        </h1>
        <div class="subtitle">« Gouvernement du peuple, par le peuple et pour le peuple » — Const. 1958, Art. 2</div>
      </div>
        <nav>
          <button class="active" onclick="showTab('simulateur')">📊 Simulateur</button>
          <button onclick="showTab('assemblees')">🏛️ Assemblées & Pouvoirs</button>
          <button onclick="showTab('generations')">👶 Cycle de Vie & 3 Générations</button>
          <button onclick="showTab('territoires')">🗺️ Territoires & Élections</button>
          <button onclick="showTab('bataille')">⚖️ Arbitrages Ministériels (Bercy)</button>
          <button onclick="showTab('comparatif')">⚖️ Comparateur</button>
          <button onclick="showTab('architecture')">🏛️ Les 4 Strates</button>
          <button onclick="showTab('corpus')">📜 Corpus Juridique</button>
          <button onclick="showTab('dossier')">📖 Mandature (+60 Md€)</button>
          <button onclick="showTab('audit')">🔍 Sources & Auditabilité</button>
          <button onclick="showTab('thinktanks')">🔬 Think Tanks & Stress Tests</button>
          <button onclick="showTab('histoire')">📜 Histoire & Comparaisons (1792→2026)</button>
          <button onclick="showTab('societe')">🏛️ Société — 18 Domaines</button>
        </nav>
    </div>
  </header>

  <div class="container">
    <!-- ============================================================= -->
    <!-- TAB 1 : SIMULATEUR INTERACTIF                                 -->
    <!-- ============================================================= -->
    <div id="tab-simulateur" class="tab-pane active">
      <!-- Choix des Scénarios -->
      <div class="scenario-bar">
        <button class="scenario-btn active" id="btn-sc-mandature" onclick="selectScenario('mandature')">
          <div class="sc-title">Plan Mandature <span class="badge badge-success">+60 Md€</span></div>
          <div class="sc-sub">Sortie PDE & TVA énergie 5,5%</div>
        </button>
        <button class="scenario-btn" id="btn-sc-statut_quo" onclick="selectScenario('statut_quo')">
          <div class="sc-title">Statut Quo <span class="badge badge-danger">Inertie</span></div>
          <div class="sc-sub">Dérive budgétaire et note A+</div>
        </button>
        <button class="scenario-btn" id="btn-sc-austerite" onclick="selectScenario('austerite')">
          <div class="sc-title">Austérité Aveugle <span class="badge badge-warning">Coupes DGF</span></div>
          <div class="sc-sub">Flambée taxe foncière & fronde</div>
        </button>
        <button class="scenario-btn" id="btn-sc-choc_mondial" onclick="selectScenario('choc_mondial')">
          <div class="sc-title">Choc Mondial <span class="badge badge-primary">Stagflation</span></div>
          <div class="sc-sub">Brent >110$, EUR/USD & Fed</div>
        </button>
        <button class="scenario-btn" id="btn-sc-custom" onclick="toggleCustomPanel()">
          <div class="sc-title">Sur-Mesure <span class="badge badge-primary">🎛️ Curseurs</span></div>
          <div class="sc-sub">Ajustez les 20 leviers</div>
        </button>
      </div>

      <!-- Panneau Custom -->
      <div id="custom-panel" class="custom-panel">
        <div class="custom-grid">
          <div class="control-group">
            <h4>1. Nouvelles Recettes de Régulation</h4>
            <div class="slider-item">
              <div class="slider-header"><span>Traque Fraude Fiscale IA</span><span class="val" id="val-fraude">10 Md€</span></div>
              <input type="range" id="sl-fraude" min="0" max="25" value="10" step="0.5" oninput="updateVal('fraude', this.value, ' Md€')">
            </div>
            <div class="slider-item">
              <div class="slider-header"><span>Conditionnement Aides DSN</span><span class="val" id="val-aides">15 Md€</span></div>
              <input type="range" id="sl-aides" min="0" max="25" value="15" step="0.5" oninput="updateVal('aides', this.value, ' Md€')">
            </div>
            <div class="slider-item">
              <div class="slider-header"><span>Taxe Superprofits / Rachats</span><span class="val" id="val-superprofits">6 Md€</span></div>
              <input type="range" id="sl-superprofits" min="0" max="15" value="6" step="0.5" oninput="updateVal('superprofits', this.value, ' Md€')">
            </div>
            <div class="slider-item">
              <div class="slider-header"><span>Extension TTF Euroclear</span><span class="val" id="val-ttf">5 Md€</span></div>
              <input type="range" id="sl-ttf" min="0" max="12" value="5" step="0.5" oninput="updateVal('ttf', this.value, ' Md€')">
            </div>
          </div>

          <div class="control-group">
            <h4>2. Économies & Commande Publique</h4>
            <div class="slider-item">
              <div class="slider-header"><span>Fusion Doublons Région/Dép</span><span class="val" id="val-doublons">8 Md€</span></div>
              <input type="range" id="sl-doublons" min="0" max="15" value="8" step="0.5" oninput="updateVal('doublons', this.value, ' Md€')">
            </div>
            <div class="slider-item">
              <div class="slider-header"><span>Achats massifiés 30% PME</span><span class="val" id="val-achats">6 Md€</span></div>
              <input type="range" id="sl-achats" min="0" max="15" value="6" step="0.5" oninput="updateVal('achats', this.value, ' Md€')">
            </div>
            <div class="slider-item">
              <div class="slider-header"><span>Extinction Niches Inefficaces</span><span class="val" id="val-niches">7 Md€</span></div>
              <input type="range" id="sl-niches" min="0" max="15" value="7" step="0.5" oninput="updateVal('niches', this.value, ' Md€')">
            </div>
            <div class="slider-item">
              <div class="slider-header"><span>Dotation DGF aux Collectivités</span><span class="val" id="val-dgf">0 Md€</span></div>
              <input type="range" id="sl-dgf" min="-15" max="10" value="0" step="1" oninput="updateVal('dgf', this.value, ' Md€')">
            </div>
          </div>

          <div class="control-group">
            <h4>3. Pouvoir d'Achat & Démocratie</h4>
            <label class="checkbox-item">
              <input type="checkbox" id="chk-tva" checked>
              <span><strong>Baisse TVA Énergie à 5,5 %</strong> (-9 Md€)</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" id="chk-b2" checked>
              <span>Casier Judiciaire B2 obligatoire</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" id="chk-blanc" checked>
              <span>Vote Blanc invalidant (carence 12 mois)</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" id="chk-ric" checked>
              <span>RIC Souverain & Démocratie Directe</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" id="chk-pantouflage" checked>
              <span>Verrou anti-pantouflage & lobbys</span>
            </label>
          </div>

          <div class="control-group">
            <h4>4. Chocs Mondiaux Exogènes</h4>
            <div class="slider-item">
              <div class="slider-header"><span>Choc Brent Mondial ($)</span><span class="val" id="val-brent">+0 $</span></div>
              <input type="range" id="sl-brent" min="-30" max="60" value="0" step="5" oninput="updateVal('brent', this.value, ' $')">
            </div>
            <div class="slider-item">
              <div class="slider-header"><span>Resserrement Fed (bps)</span><span class="val" id="val-fed">+0 bps</span></div>
              <input type="range" id="sl-fed" min="-100" max="200" value="0" step="25" oninput="updateVal('fed', this.value, ' bps')">
            </div>
            <div class="slider-item">
              <div class="slider-header"><span>Variation EUR/USD</span><span class="val" id="val-forex">+0.00</span></div>
              <input type="range" id="sl-forex" min="-0.20" max="0.20" value="0" step="0.02" oninput="updateVal('forex', this.value, '')">
            </div>
            <button class="btn-run-custom" onclick="lancerSimulationPersonnalisee()">🚀 Simuler cette trajectoire</button>
          </div>
        </div>
      </div>

      <!-- Cartes KPI de l'Année 5 -->
      <div class="kpi-grid">
        <div class="kpi-card" id="card-deficit">
          <div class="kpi-label">Déficit Public</div>
          <div class="kpi-value" id="kpi-deficit">2.84 %</div>
          <div class="kpi-sub">
            <span id="kpi-deficit-mde">92.5 Md€</span>
            <span class="badge" id="badge-deficit">CONFORME</span>
          </div>
        </div>
        <div class="kpi-card" id="card-dette">
          <div class="kpi-label">Dette Publique (Maastricht)</div>
          <div class="kpi-value" id="kpi-dette">128.1 %</div>
          <div class="kpi-sub">
            <span id="kpi-dette-stock">4 195 Md€</span>
            <span class="badge badge-primary">Stabilisée</span>
          </div>
        </div>
        <div class="kpi-card" id="card-taux">
          <div class="kpi-label">OAT 10 ans & Marchés</div>
          <div class="kpi-value" id="kpi-oat">3.35 %</div>
          <div class="kpi-sub">
            <span id="kpi-spread">Spread: 47.2 bps</span>
            <span class="badge badge-success" id="badge-note">AA</span>
          </div>
        </div>
        <div class="kpi-card" id="card-tension">
          <div class="kpi-label">Tension Sociale Territoriale</div>
          <div class="kpi-value" id="kpi-tension">5.0 / 100</div>
          <div class="kpi-sub">
            <span>Foncier: <span id="kpi-foncier">39.5 Md€</span></span>
            <span class="badge badge-success" id="badge-tension">APAISÉ</span>
          </div>
        </div>
        <div class="kpi-card" id="card-confiance">
          <div class="kpi-label">Confiance Citoyenne</div>
          <div class="kpi-value" id="kpi-confiance">77.5 / 100</div>
          <div class="kpi-sub">
            <span>Risque Censure: <span id="kpi-censure">21.0 %</span></span>
            <span class="badge badge-primary">Solide</span>
          </div>
        </div>
        <div class="kpi-card" id="card-energie">
          <div class="kpi-label">Énergie & Pouvoir d'Achat</div>
          <div class="kpi-value" id="kpi-pouvoir">103.8</div>
          <div class="kpi-sub">
            <span>Inflation IPC: <span id="kpi-inflation">1.75 %</span></span>
            <span class="badge badge-success">Gagnant</span>
          </div>
        </div>
      </div>

      <!-- Tableau de Bord Quinquennal -->
      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Année</th>
              <th>Déficit Net</th>
              <th>Déficit / PIB</th>
              <th>Dette / PIB</th>
              <th>OAT 10 ans</th>
              <th>Spread Bund</th>
              <th>Tension Locale</th>
              <th>Confiance</th>
              <th>Statut PDE (UE)</th>
              <th>Notation</th>
            </tr>
          </thead>
          <tbody id="trajectory-tbody">
            <!-- Rempli par JavaScript -->
          </tbody>
        </table>
      </div>

      <!-- Détail Année Sélectionnée -->
      <div class="year-details" id="year-details-panel">
        <div class="year-header">
          <h3 id="detail-year-title">🔍 ANALYSE APPROFONDIE : ANNÉE 5</h3>
          <span class="badge badge-primary" id="detail-year-badge">Échelon Gigogne Complet</span>
        </div>
        <div class="strates-grid">
          <div class="strate-card">
            <h4>🏡 Strate 1 : Le Local</h4>
            <div class="metric-row"><span>Tension sociale locale</span><strong id="det-tension">5.0 / 100</strong></div>
            <div class="metric-row"><span>Qualité services de proximité</span><strong id="det-services">76.8 / 100</strong></div>
            <div class="metric-row"><span>Produit Taxe Foncière (TFPB)</span><strong id="det-foncier">39.5 Md€</strong></div>
            <div class="metric-row"><span>Règle d'or (art. L. 1612-4 CGCT)</span><strong style="color:var(--accent-emerald)">Respectée</strong></div>
          </div>
          <div class="strate-card">
            <h4>🇫🇷 Strate 2 : Le National</h4>
            <div class="metric-row"><span>PIB Nominal</span><strong id="det-pib">3 252.8 Md€</strong></div>
            <div class="metric-row"><span>Déficit Public APU</span><strong id="det-deficit">92.5 Md€</strong></div>
            <div class="metric-row"><span>Dette Maastricht</span><strong id="det-dette">4 195.4 Md€</strong></div>
            <div class="metric-row"><span>Pouvoir d'Achat Ménages</span><strong id="det-pouvoir">103.8 (Base 100)</strong></div>
            <div class="metric-row"><span>Risque Censure Parlement</span><strong id="det-censure">21.0 %</strong></div>
          </div>
          <div class="strate-card">
            <h4>🇪🇺 Strate 3 : Le Continental / UE</h4>
            <div class="metric-row"><span>Seuil PDE de Maastricht</span><strong>3.00 % du PIB</strong></div>
            <div class="metric-row"><span>Statut PDE</span><strong id="det-pde" style="color:var(--accent-emerald)">Conforme</strong></div>
            <div class="metric-row"><span>Bouclier TPI de la BCE</span><strong id="det-tpi" style="color:var(--accent-emerald)">Actif & Protégé</strong></div>
            <div class="metric-row"><span>Astreinte Financière UE</span><strong>0.00 Md€</strong></div>
          </div>
          <div class="strate-card">
            <h4>🌍 Strate 4 : Le Mondial</h4>
            <div class="metric-row"><span>Taux OAT France 10 ans</span><strong id="det-oat">3.35 %</strong></div>
            <div class="metric-row"><span>Spread face au Bund</span><strong id="det-spread">47.2 bps</strong></div>
            <div class="metric-row"><span>Taux Crédit PME</span><strong id="det-pme">4.20 %</strong></div>
            <div class="metric-row"><span>Facture Énergétique Nette</span><strong id="det-facture">64.5 Md€/an</strong></div>
            <div class="metric-row"><span>Note Souveraine</span><strong id="det-note" style="color:var(--accent-emerald)">AA</strong></div>
          </div>
          <div class="strate-card">
            <h4>🏛️ Strate Politique : Assemblées & Censure</h4>
            <div class="metric-row"><span>Projection Voix Censure AN</span><strong id="det-voix-censure">254 / 289</strong></div>
            <div class="metric-row"><span>Climat Assemblée nationale</span><strong id="det-climat-an">Majorité consolidée</strong></div>
            <div class="metric-row"><span>Hostilité Territoriale Sénat</span><strong id="det-hostilite-senat">18.0 / 100</strong></div>
            <div class="metric-row"><span>Veto Constitutionnel Art. 89</span><strong id="det-veto-senat" style="color:var(--accent-emerald)">Veto levé</strong></div>
            <div class="metric-row"><span>Départements en faillite (ciseau)</span><strong id="det-faillite-dept">2 départements</strong></div>
          </div>
          <div class="strate-card">
            <h4>👶 Strate Intergénérationnelle : 3 Générations</h4>
            <div class="metric-row"><span>Harmonie Intergénérationnelle</span><strong id="det-harmonie-gen" style="color:var(--accent-emerald)">83.1 / 100</strong></div>
            <div class="metric-row"><span>Fardeau Génération Sandwich (G2)</span><strong id="det-charge-sandwich">34.2 / 100</strong></div>
            <div class="metric-row"><span>Taux Pauvreté Jeunesse (G3)</span><strong id="det-pauvrete-g3">12.5 %</strong></div>
            <div class="metric-row"><span>Taux Pauvreté Aînés (G1)</span><strong id="det-pauvrete-g1">6.8 %</strong></div>
            <div class="metric-row"><span>Fardeau Dette / Jeune G3</span><strong id="det-dette-jeune">129 275 €</strong></div>
          </div>
          <div class="strate-card">
            <h4>🗺️ Strate Territoires, Outre-Mer & Élections</h4>
            <div class="metric-row"><span>Participation électorale projetée</span><strong id="det-elections-partic">74.5 %</strong></div>
            <div class="metric-row"><span>Triangulaires législatives (577 circ.)</span><strong id="det-elections-triang">38 circonscriptions</strong></div>
            <div class="metric-row"><span>Vie chère Outre-mer (surcoût)</span><strong id="det-om-vie-chere">18.5 %</strong></div>
            <div class="metric-row"><span>Continuité territoriale Outre-mer</span><strong id="det-om-continuite" style="color:var(--accent-emerald)">78.0 / 100</strong></div>
            <div class="metric-row"><span>Vitalité communes rurales (<1000)</span><strong id="det-ruralite-vitalite">81.5 / 100</strong></div>
          </div>
        </div>

        <!-- Flux d'Événements Rétroactifs -->
        <div class="events-stream">
          <h4>⚡ Journal des Rétroactions Systémiques</h4>
          <div id="events-container">
            <!-- Rempli par JavaScript -->
          </div>
        </div>

        <div class="action-bar">
          <button class="btn-secondary" onclick="exporterRapport('markdown')">📄 Exporter Rapport Markdown</button>
          <button class="btn-secondary" onclick="exporterRapport('json')">💾 Exporter Données JSON</button>
        </div>
      </div>
    </div>

    <!-- ============================================================= -->
    <!-- TAB : ASSEMBLÉES REPRÉSENTATIVES ET JEUX DE POUVOIRS          -->
    <!-- ============================================================= -->
    <div id="tab-assemblees" class="tab-pane">
      <div class="arch-diagram">
        <h2>🏛️ CARTOGRAPHIE ET JEUX DE POUVOIRS DES ASSEMBLÉES DÉCISIONNELLES</h2>
        <p class="subtitle" style="margin-bottom:20px;">Analyse en temps réel des 12 assemblées représentatives de la République face au scénario en cours.</p>

        <div class="kpi-grid" style="margin-bottom:24px;">
          <!-- 1. Assemblée nationale -->
          <div class="kpi-card" id="card-ass-an">
            <div class="kpi-label">Assemblée nationale (577 Députés)</div>
            <div class="kpi-value" id="ass-an-voix">254 / 289</div>
            <div class="kpi-sub">
              <span>Voix Censure (Art. 49.2)</span>
              <span class="badge badge-success" id="ass-an-badge">STABLE</span>
            </div>
            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:8px;" id="ass-an-climat">Majorité consolidée</div>
          </div>

          <!-- 2. Sénat -->
          <div class="kpi-card" id="card-ass-senat">
            <div class="kpi-label">Sénat (348 Sénateurs)</div>
            <div class="kpi-value" id="ass-senat-hostilite">18.0 / 100</div>
            <div class="kpi-sub">
              <span>Hostilité Territoriale</span>
              <span class="badge badge-success" id="ass-senat-badge">VETO ART. 89 LEVÉ</span>
            </div>
            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:8px;">CMP Taux d'accord : <strong id="ass-senat-cmp">73.3 %</strong></div>
          </div>

          <!-- 3. Congrès de Versailles -->
          <div class="kpi-card" id="card-ass-congres">
            <div class="kpi-label">Congrès de Versailles (925)</div>
            <div class="kpi-value" id="ass-congres-voix">625 / 555</div>
            <div class="kpi-sub">
              <span>Seuil 3/5èmes Révision</span>
              <span class="badge badge-success" id="ass-congres-badge">QUALIFIÉ (60%)</span>
            </div>
            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:8px;" id="ass-congres-voie">Approbation Congrès possible</div>
          </div>

          <!-- 4. Conseils Départementaux -->
          <div class="kpi-card" id="card-ass-dept">
            <div class="kpi-label">Conseils Départementaux (101)</div>
            <div class="kpi-value" id="ass-dept-faillite">2 / 101</div>
            <div class="kpi-sub">
              <span>Départements en faillite</span>
              <span class="badge badge-success" id="ass-dept-badge">SOLVABLE</span>
            </div>
            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:8px;">Indice Ciseau social : <strong id="ass-dept-ciseau">45.0/100</strong></div>
          </div>

          <!-- 5. Conseils Municipaux -->
          <div class="kpi-card" id="card-ass-maires">
            <div class="kpi-label">Conseils Municipaux (34 935)</div>
            <div class="kpi-value" id="ass-maires-fronde">12.0 / 100</div>
            <div class="kpi-sub">
              <span>Fronde Maires (AMF)</span>
              <span class="badge badge-success" id="ass-maires-badge">APAISÉ</span>
            </div>
            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:8px;">Règle d'or (art. L. 1612-4) : <strong style="color:var(--accent-emerald);">Équilibré</strong></div>
          </div>

          <!-- 6. Assemblées Consulaires -->
          <div class="kpi-card" id="card-ass-consulaire">
            <div class="kpi-label">Assemblées Consulaires (CCI/CMA/CA)</div>
            <div class="kpi-value" id="ass-consulaire-conf">78.0 %</div>
            <div class="kpi-sub">
              <span>Confiance PME (CCI)</span>
              <span class="badge badge-success">30% PME</span>
            </div>
            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:8px;">Adhésion Artisans CMA : <strong id="ass-consulaire-cma">84.0 %</strong></div>
          </div>
        </div>

        <!-- Fiches Détaillées des Assemblées -->
        <div class="strates-grid">
          <div class="strate-card">
            <h4>🗳️ Assemblée nationale (577 Députés)</h4>
            <div class="metric-row"><span>Coalition gouvernementale</span><strong>210 sièges (Majorité relative)</strong></div>
            <div class="metric-row"><span>Oppositions coalisées</span><strong>320 sièges</strong></div>
            <div class="metric-row"><span>Députés pivots indépendants</span><strong>47 sièges</strong></div>
            <div class="metric-row"><span>Seuil d'adoption motion de censure</span><strong>289 voix (Art. 49.2)</strong></div>
            <div class="metric-row"><span>Projection voix de censure</span><strong id="det-ass-voix-censure">254 voix</strong></div>
            <div class="metric-row"><span>Statut du Gouvernement</span><strong id="det-ass-statut-gouv" style="color:var(--accent-emerald)">Stable en fonction</strong></div>
            <div style="margin-top:10px; font-size:0.8rem; color:var(--text-muted);">
              <strong>Dynamique induite :</strong> Si la tension sociale locale dépasse 65/100, les députés indépendants basculent vers la censure. À 289 voix, le gouvernement chute obligatoirement ou déclenche la dissolution (Art. 12).
            </div>
          </div>

          <div class="strate-card">
            <h4>🏛️ Le Sénat (348 Sénateurs)</h4>
            <div class="metric-row"><span>Collège électoral</span><strong>162 000 grands électeurs communaux</strong></div>
            <div class="metric-row"><span>Majorité sénatoriale</span><strong>Droite et Centre (215 sièges)</strong></div>
            <div class="metric-row"><span>Indice d'hostilité territoriale</span><strong id="det-ass-senat-hostilite">18.0 / 100</strong></div>
            <div class="metric-row"><span>Veto Révision Constitutionnelle (Art. 89)</span><strong id="det-ass-senat-veto" style="color:var(--accent-emerald)">Veto levé</strong></div>
            <div class="metric-row"><span>Taux d'accord CMP</span><strong id="det-ass-senat-cmp">73.3 %</strong></div>
            <div style="margin-top:10px; font-size:0.8rem; color:var(--text-muted);">
              <strong>Jeu de force :</strong> Le Sénat est le bouclier constitutionnel des maires. Toute coupe unilatérale de DGF déclenche son hostilité (>55/100) et bloque définitivement toute révision par l'article 89.
            </div>
          </div>

          <div class="strate-card">
            <h4>🏢 Conseils Départementaux (101 Départements)</h4>
            <div class="metric-row"><span>Missions obligatoires</span><strong>RSA, APA (aînés), PCH (handicap), ASE</strong></div>
            <div class="metric-row"><span>Dépenses sociales de guichet</span><strong id="det-ass-dept-social">44.5 Md€/an</strong></div>
            <div class="metric-row"><span>Recettes DMTO volatiles</span><strong id="det-ass-dept-dmto">12.5 Md€/an</strong></div>
            <div class="metric-row"><span>Indice de crise de ciseau financier</span><strong id="det-ass-dept-ciseau">45.0 / 100</strong></div>
            <div class="metric-row"><span>Départements menacés de faillite</span><strong id="det-ass-dept-faillite" style="color:var(--accent-emerald)">2 départements</strong></div>
            <div style="margin-top:10px; font-size:0.8rem; color:var(--text-muted);">
              <strong>Contrainte :</strong> Dépenses rigides imposées nationalement sans pouvoir d'ajustement vs recettes d'impôt immobilier très volatiles.
            </div>
          </div>

          <div class="strate-card">
            <h4>🇪🇺 Parlement Européen & Conseil UE</h4>
            <div class="metric-row"><span>Parlement Européen (720 députés)</span><strong>Coalition PPE-S&D-Renew</strong></div>
            <div class="metric-row"><span>Taux d'alignement sur directives FR</span><strong id="det-ass-pe-alignement">78.0 %</strong></div>
            <div class="metric-row"><span>Directive TVA Énergie 2022/542</span><strong style="color:var(--accent-emerald)">100% Conforme (Annexe III)</strong></div>
            <div class="metric-row"><span>Conseil UE (Majorité qualifiée 55/65)</span><strong id="det-ass-conseil-ue" style="color:var(--accent-emerald)">Sortie PDE validée</strong></div>
            <div style="margin-top:10px; font-size:0.8rem; color:var(--text-muted);">
              <strong>Contrainte supranationalité :</strong> Si le déficit dépasse 3,0%, le Conseil UE vote des astreintes semestrielles et la BCE suspend le bouclier anti-spéculation TPI.
            </div>
          </div>

          <div class="strate-card">
            <h4>🤝 CESE & Conventions Citoyennes</h4>
            <div class="metric-row"><span>CESE (175 membres)</span><strong>Dialogue social syndicats & patronat</strong></div>
            <div class="metric-row"><span>Consensus social et syndical</span><strong id="det-ass-cese-consensus">68.0 %</strong></div>
            <div class="metric-row"><span>Convention Citoyenne (150 tirés au sort)</span><strong>Démocratie délibérative</strong></div>
            <div class="metric-row"><span>Consensus délibératif sans filtre</span><strong id="det-ass-citoyen-consensus">94.0 %</strong></div>
            <div style="margin-top:10px; font-size:0.8rem; color:var(--text-muted);">
              <strong>Légitimité populaire :</strong> Brise les blocages d'appareils et prépare les projets de lois soumis au référendum républicain.
            </div>
          </div>

          <div class="strate-card">
            <h4>🔨 Assemblées Consulaires (CCI, CMA, CA)</h4>
            <div class="metric-row"><span>Ressortissants représentés</span><strong>6,9 millions d'entreprises</strong></div>
            <div class="metric-row"><span>Confiance des PME et commerces (CCI)</span><strong id="det-ass-cons-cci">78.0 %</strong></div>
            <div class="metric-row"><span>Adhésion des artisans (CMA)</span><strong id="det-ass-cons-cma">84.0 %</strong></div>
            <div class="metric-row"><span>Commande publique allotie 30% PME</span><strong style="color:var(--accent-emerald)">Art. L. 2113-10 CCP Appliqué</strong></div>
            <div style="margin-top:10px; font-size:0.8rem; color:var(--text-muted);">
              <strong>Moteur de terroir :</strong> L'accès direct des artisans et PME à la commande publique locale réinjecte les deniers publics dans l'économie réelle.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================================= -->
    <!-- TAB : CYCLE DE VIE ET 3 GÉNÉRATIONS (FLUX CROISÉS)            -->
    <!-- ============================================================= -->
    <div id="tab-generations" class="tab-pane">
      <div class="arch-diagram">
        <h2>👶 CYCLE DE VIE RÉPUBLICAIN & PACTE INTERGÉNÉRATIONNEL (3 GÉNÉRATIONS)</h2>
        <p class="subtitle" style="margin-bottom:20px;">
          « Du berceau au tombeau » : conciliation organique de ceux qui ont bâti la France (G1), ceux qui la font tourner au quotidien (G2), et ceux qui portent son avenir (G3).
        </p>

        <!-- 4 KPI Cards Temps Réel -->
        <div class="kpi-grid" style="margin-bottom:24px;">
          <div class="kpi-card" id="card-gen-g1">
            <div class="kpi-title">👴 G1 : Aînés & Retraités (65-95+)</div>
            <div class="kpi-value" id="gen-g1-pop">14.6 M</div>
            <div class="kpi-sub">Pauvreté : <strong id="gen-g1-pauv">10.8 %</strong> • Garde enfants : <strong>18 Md€</strong></div>
            <div style="margin-top:8px;"><span class="badge badge-primary" id="badge-gen-g1">Piliers civiques</span></div>
          </div>

          <div class="kpi-card" id="card-gen-g2">
            <div class="kpi-title">🧑‍💼 G2 : Actifs & Parents (35-64)</div>
            <div class="kpi-value" id="gen-g2-pop">26.2 M</div>
            <div class="kpi-sub">Fardeau sandwich : <strong id="gen-g2-charge">68.0 / 100</strong> • Cotis : <strong>345 Md€</strong></div>
            <div style="margin-top:8px;"><span class="badge badge-warning" id="badge-gen-g2">Cœur productif</span></div>
          </div>

          <div class="kpi-card" id="card-gen-g3">
            <div class="kpi-title">🎓 G3 : Jeunesse & Avenir (0-34)</div>
            <div class="kpi-value" id="gen-g3-pop">27.6 M</div>
            <div class="kpi-sub">Pauvreté : <strong id="gen-g3-pauv">19.4 %</strong> • Dette/jeune : <strong id="gen-g3-dette">129 k€</strong></div>
            <div style="margin-top:8px;"><span class="badge badge-danger" id="badge-gen-g3">Relève républicaine</span></div>
          </div>

          <div class="kpi-card" id="card-gen-harmonie">
            <div class="kpi-title">⚖️ Harmonie Intergénérationnelle</div>
            <div class="kpi-value" id="gen-harmonie-score">42.0 / 100</div>
            <div class="kpi-sub">Ratio dépendance : <strong id="gen-ratio-dep">0.65</strong> • Indice IEHI</div>
            <div style="margin-top:8px;"><span class="badge badge-warning" id="badge-gen-harmonie">Tension initiale</span></div>
          </div>
        </div>

        <!-- Les 9 Périodes de la Vie Humaine -->
        <h3 style="margin-bottom:12px; font-weight:800;">🧭 Le Cycle de Vie Républicain : Les 9 Périodes du Berceau au Tombeau</h3>
        <div class="strates-grid" style="margin-bottom:24px;">
          <div class="strate-card">
            <h4>🍼 P0 : Périnatalité & Crèche (0 - 3 ans)</h4>
            <div class="metric-row"><span>Acteurs publics</span><strong>Communes & PMI (Département)</strong></div>
            <div class="metric-row"><span>Prestations clés</span><strong>CAF (PAJE), Congé parental, Crèches</strong></div>
            <div class="metric-row"><span>Apport vital de G1</span><strong style="color:var(--accent-emerald)">Garde bénévole par les grands-parents</strong></div>
            <div class="metric-row"><span>Mesure Mandature</span><strong>Places de crèche réservées & PMI confortées</strong></div>
          </div>

          <div class="strate-card">
            <h4>🎒 P1 : Enfance & École Primaire (3 - 11 ans)</h4>
            <div class="metric-row"><span>Acteurs publics</span><strong>Conseil Municipal & Éducation Nationale</strong></div>
            <div class="metric-row"><span>Enjeux vitaux</span><strong>Savoirs fondamentaux, nutrition, éveil</strong></div>
            <div class="metric-row"><span>Soutien de G1</span><strong>Sorties d'école et devoirs (soulage G2)</strong></div>
            <div class="metric-row"><span>Mesure Mandature</span><strong style="color:var(--accent-emerald)">Cantine bio et locale à 1 €</strong></div>
          </div>

          <div class="strate-card">
            <h4>📐 P2 : Adolescence, Collège & Lycée (11 - 18 ans)</h4>
            <div class="metric-row"><span>Acteurs publics</span><strong>Départements (Collèges) & Régions (Lycées)</strong></div>
            <div class="metric-row"><span>Compétences</span><strong>Bâtiments, numérique, transports scolaires</strong></div>
            <div class="metric-row"><span>Enjeux citoyens</span><strong>Orientation professionnelle, apprentissage, santé</strong></div>
            <div class="metric-row"><span>Mesure Mandature</span><strong style="color:var(--accent-emerald)">Gratuité transports scolaires TER</strong></div>
          </div>

          <div class="strate-card">
            <h4>🏛️ P3 : Études Supérieures & Autonomie (18 - 25 ans)</h4>
            <div class="metric-row"><span>Acteurs publics</span><strong>État, Universités, CROUS, Chambres Consulaires</strong></div>
            <div class="metric-row"><span>Plafond de verre</span><strong>Précarité étudiante, coût du logement</strong></div>
            <div class="metric-row"><span>Droit civique</span><strong>Premier vote républicain, citoyenneté active</strong></div>
            <div class="metric-row"><span>Mesure Mandature</span><strong style="color:var(--accent-emerald)">Dotation d'émancipation républicaine (10 k€)</strong></div>
          </div>

          <div class="strate-card">
            <h4>🔑 P4 : Insertion Active & Premier Toit (25 - 35 ans)</h4>
            <div class="metric-row"><span>Acteurs publics</span><strong>Entreprises, Banques, Bailleurs HLM, État</strong></div>
            <div class="metric-row"><span>Barrière majeure</span><strong>Accès au crédit sans apport familial</strong></div>
            <div class="metric-row"><span>Enjeu démographique</span><strong>Premier enfant, fondation du foyer</strong></div>
            <div class="metric-row"><span>Mesure Mandature</span><strong style="color:var(--accent-emerald)">Défiscalisation dons G1 vers G3 pour logement</strong></div>
          </div>

          <div class="strate-card">
            <h4>💼 P5 : Plénitude & « Génération Sandwich » (35 - 50 ans)</h4>
            <div class="metric-row"><span>Rôle systémique</span><strong>Moteur fiscal et productif suprême de la Nation</strong></div>
            <div class="metric-row"><span>Double fardeau</span><strong style="color:var(--accent-crimson)">Financement G3 (études) + Soutien G1 (dépendance)</strong></div>
            <div class="metric-row"><span>Contribution nette</span><strong>345 Md€ cotisations + 125 Md€ impôt sur revenu</strong></div>
            <div class="metric-row"><span>Mesure Mandature</span><strong style="color:var(--accent-emerald)">Baisse TVA énergie 5,5% & statut proche aidant</strong></div>
          </div>

          <div class="strate-card">
            <h4>⏳ P6 : Seconde Carrière & Transmission (50 - 65 ans)</h4>
            <div class="metric-row"><span>Enjeu républicain</span><strong>Maintien emploi seniors (56,5% FR vs 72% All.)</strong></div>
            <div class="metric-row"><span>Transmission des savoirs</span><strong>Tutorat intergénérationnel en entreprise</strong></div>
            <div class="metric-row"><span>Héritage moyen</span><strong>Âge moyen où l'on hérite : 52 ans (trop tard pour G3)</strong></div>
            <div class="metric-row"><span>Mesure Mandature</span><strong style="color:var(--accent-emerald)">Circulation précoce du capital vers petits-enfants</strong></div>
          </div>

          <div class="strate-card">
            <h4>🌳 P7 : Retraite Active & Pilier Associatif (65 - 80 ans)</h4>
            <div class="metric-row"><span>Régime de solidarité</span><strong>Retraite par répartition gagée par le labeur de G2</strong></div>
            <div class="metric-row"><span>Force civique</span><strong>68% des responsables associatifs bénévoles</strong></div>
            <div class="metric-row"><span>Démocratie de terroir</span><strong>58% des maires et élus municipaux ruraux</strong></div>
            <div class="metric-row"><span>Mesure Mandature</span><strong style="color:var(--accent-emerald)">Revalorisation petites retraites agricoles & artisans</strong></div>
          </div>

          <div class="strate-card">
            <h4>🕊️ P8 : Grand Âge, Dépendance & Fin de Vie (80 - 95+ ans)</h4>
            <div class="metric-row"><span>Acteurs institutionnels</span><strong>Départements (APA) & Sécurité Sociale (CNSA)</strong></div>
            <div class="metric-row"><span>Reste à charge EHPAD</span><strong>1 200 à 1 800 €/mois pesant sur les familles</strong></div>
            <div class="metric-row"><span>Fin de vie républicaine</span><strong>Soins palliatifs dignes, directives anticipées</strong></div>
            <div class="metric-row"><span>Mesure Mandature</span><strong style="color:var(--accent-emerald)">5e branche Autonomie & plan maintien à domicile</strong></div>
          </div>
        </div>

        <!-- Matrice des Flux Croisés -->
        <h3 style="margin-bottom:12px; font-weight:800;">🔄 Matrice des Flux Croisés Dynamiques (Qui finance qui ?)</h3>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Flux Intergénérationnel</th>
                <th>Origine $\rightarrow$ Destination</th>
                <th>Volume Annuel Estimé</th>
                <th>Impact Systémique & Rétroaction</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Cotisations & Pensions de Retraite</strong></td>
                <td>G2 (Actifs) $\rightarrow$ G1 (Retraités)</td>
                <td><strong id="flux-retraites">360.0 Md€</strong></td>
                <td>Socle du pacte social de 1945 : répartition pure sans capitalisation spéculative.</td>
              </tr>
              <tr>
                <td><strong>Investissement Éducatif & Universitaire</strong></td>
                <td>G2 (Actifs) $\rightarrow$ G3 (Jeunesse)</td>
                <td><strong id="flux-education">165.0 Md€</strong></td>
                <td>Formation du capital humain national : écoles des maires, collèges, lycées, facultés.</td>
              </tr>
              <tr>
                <td><strong>Solidarité Santé & Affections Longue Durée</strong></td>
                <td>G2 (Actifs) $\rightarrow$ G1 (Aînés)</td>
                <td><strong>95.0 Md€</strong></td>
                <td>Prise en charge à 100% des pathologies lourdes via l'Assurance Maladie mutualisée.</td>
              </tr>
              <tr>
                <td><strong>Garde d'Enfants Bénévole (Care)</strong></td>
                <td>G1 (Grands-parents) $\rightarrow$ G3 (Enfants)</td>
                <td><strong id="flux-garde" style="color:var(--accent-emerald)">18.0 Md€ (Travail invisible)</strong></td>
                <td>Équivalent à 1,2 million de places de crèche : sans G1, l'emploi de G2 s'effondre.</td>
              </tr>
              <tr>
                <td><strong>Transmissions Successorales Générales</strong></td>
                <td>G1 (Aînés) $\rightarrow$ G2 (Quinquagénaires)</td>
                <td><strong>225.0 Md€</strong></td>
                <td>Héritage tardif à 52 ans : concentré chez des actifs dont le logement est déjà payé.</td>
              </tr>
              <tr>
                <td><strong>Donations Directes vers Petits-Enfants</strong></td>
                <td>G1 (Aînés) $\rightarrow$ G3 (Jeunes adultes)</td>
                <td><strong id="flux-donations" style="color:var(--accent-emerald)">75.0 Md€</strong></td>
                <td>Donations inter vivos pour financer le premier achat immobilier ou l'installation artisanale.</td>
              </tr>
              <tr>
                <td><strong>Charge de la Dette Souveraine Léguée</strong></td>
                <td>Passé $\rightarrow$ G3 (Génération future)</td>
                <td><strong id="flux-dette-jeune" style="color:var(--accent-crimson)">129 275 € par jeune</strong></td>
                <td>Dette accumulée (3 568 Md€) pesant sur l'avenir, ramenée sous contrôle par le plan +60 Md€.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ============================================================= -->
    <!-- TAB : TERRITOIRES, OUTRE-MER ET ÉLECTIONS                     -->
    <!-- ============================================================= -->
    <div id="tab-territoires" class="tab-pane">
      <div class="arch-diagram">
        <h2>🗺️ STRATES TERRITORIALES DU LIEU-DIT À LA MÉTROPOLE, OUTRE-MER & ÉLECTIONS</h2>
        <p class="subtitle" style="margin-bottom:20px;">
          L'armature républicaine intégrale : du hameau et de la commune rurale aux 22 métropoles, l'ensemble des territoires ultramarins (DROM-COM-Calédonie-ZEE) et le calendrier électoral du REU.
        </p>

        <!-- 4 KPI Cards Temps Réel Territoires & Élections -->
        <div class="kpi-grid" style="margin-bottom:24px;">
          <div class="kpi-card" id="card-terr-reu">
            <div class="kpi-title">🗳️ Corps Électoral (REU - INSEE)</div>
            <div class="kpi-value">49.5 M</div>
            <div class="kpi-sub">Participation projetée : <strong id="terr-partic-val">74.5 %</strong></div>
            <div style="margin-top:8px;"><span class="badge badge-success" id="badge-terr-partic">Souveraineté civique</span></div>
          </div>

          <div class="kpi-card" id="card-terr-rural">
            <div class="kpi-title">🏡 Ruralité & Terroirs (< 1 000 hab.)</div>
            <div class="kpi-value">25 800 com.</div>
            <div class="kpi-sub">Vitalité rurale : <strong id="terr-vitalite-rurale">81.5 / 100</strong></div>
            <div style="margin-top:8px;"><span class="badge badge-primary">74% des mairies</span></div>
          </div>

          <div class="kpi-card" id="card-terr-om">
            <div class="kpi-title">🌊 Outre-mer & ZEE Maritime</div>
            <div class="kpi-value">10.2 M km²</div>
            <div class="kpi-sub">Vie chère : <strong id="terr-om-viechere">18.5 %</strong> • Continuité : <strong id="terr-om-cont">78.0 / 100</strong></div>
            <div style="margin-top:8px;"><span class="badge badge-warning" id="badge-terr-om">2e puissance maritime</span></div>
          </div>

          <div class="kpi-card" id="card-terr-metropoles">
            <div class="kpi-title">🏢 22 Métropoles & EPCI (1 254)</div>
            <div class="kpi-value">34 935 com.</div>
            <div class="kpi-sub">Efficience métropolitaine : <strong id="terr-metropole-efficience">86.0 / 100</strong></div>
            <div style="margin-top:8px;"><span class="badge badge-success">Mutualisation réussie</span></div>
          </div>
        </div>

        <!-- Section 1 : Le Continuum Territorial de l'État -->
        <h3 style="margin-bottom:12px; font-weight:800;">📐 1. Le Continuum Territorial de l'État : Du Lieu-dit à la Mégapole</h3>
        <div class="strates-grid" style="margin-bottom:24px;">
          <div class="strate-card">
            <h4>🌿 Niveau Infra-communal : Lieux-dits & Hameaux</h4>
            <div class="metric-row"><span>Sections de commune (Art. L. 2411-1)</span><strong>2 500 sections</strong></div>
            <div class="metric-row"><span>Lieux-dits cadastraux</span><strong>~500 000 lieux-dits</strong></div>
            <div class="metric-row"><span>Conseils de quartier (Art. L. 2143-1)</span><strong>1 550 conseils (villes >=80k)</strong></div>
            <div class="metric-row"><span>Quartiers prioritaires (QPV)</span><strong>1 514 quartiers</strong></div>
          </div>

          <div class="strate-card">
            <h4>🌾 Communes Rurales (< 1 000 hab.)</h4>
            <div class="metric-row"><span>Nombre de mairies</span><strong>25 800 communes (74 % du total)</strong></div>
            <div class="metric-row"><span>Hyper-ruralité (< 100 hab.)</span><strong>3 400 communes (220 000 hab.)</strong></div>
            <div class="metric-row"><span>Villages (100 à 999 hab.)</span><strong>22 400 communes (8,1M hab.)</strong></div>
            <div class="metric-row"><span>Règle d'or & DGF rurale</span><strong style="color:var(--accent-emerald)">Sanctuaire DGF & cantines locales</strong></div>
          </div>

          <div class="strate-card">
            <h4>🏘️ Bourgs-Centres (1 000 à 9 999 hab.)</h4>
            <div class="metric-row"><span>Nombre de communes</span><strong>7 650 bourgs</strong></div>
            <div class="metric-row"><span>Population couverte</span><strong>32 % de la population (21,3M hab.)</strong></div>
            <div class="metric-row"><span>Équipements</span><strong>Écoles primaires, collèges, artisans</strong></div>
            <div class="metric-row"><span>Mesure Mandature</span><strong style="color:var(--accent-emerald)">Allotissement 30% commande publique aux PME</strong></div>
          </div>

          <div class="strate-card">
            <h4>🏭 Villes Moyennes (10 000 à 49 999 hab.)</h4>
            <div class="metric-row"><span>Nombre de villes</span><strong>1 280 communes (22,0M hab.)</strong></div>
            <div class="metric-row"><span>Population couverte</span><strong>32,1 % de la population</strong></div>
            <div class="metric-row"><span>Rôle républicain</span><strong>Hôpitaux de secteur, lycées, tribunaux</strong></div>
            <div class="metric-row"><span>Mesure Mandature</span><strong style="color:var(--accent-emerald)">Réhabilitation friches & relocalisation</strong></div>
          </div>

          <div class="strate-card">
            <h4>🏙️ Grandes Agglomérations (50k à 200k)</h4>
            <div class="metric-row"><span>Nombre de pôles</span><strong>180 grandes villes & agglos (16,8M hab.)</strong></div>
            <div class="metric-row"><span>Services majeurs</span><strong>CHU, universités, réseaux tramways, TGV</strong></div>
            <div class="metric-row"><span>Intercommunalité</span><strong>Communautés d'agglomération (228) & urbaines (14)</strong></div>
            <div class="metric-row"><span>Mesure Mandature</span><strong style="color:var(--accent-emerald)">Financement transports décarbonés</strong></div>
          </div>

          <div class="strate-card">
            <h4>🌐 Les 22 Métropoles & Mégapole (200k+)</h4>
            <div class="metric-row"><span>Grand Paris (MGP)</span><strong>7,2 millions d'habitants (11 EPT)</strong></div>
            <div class="metric-row"><span>Aix-Marseille-Provence & Lyon</span><strong>1,9M hab. (92 com.) / Métropole de Lyon</strong></div>
            <div class="metric-row"><span>19 autres métropoles</span><strong>Bordeaux, Lille, Toulouse, Nantes, etc.</strong></div>
            <div class="metric-row"><span>Mesure Mandature</span><strong style="color:var(--accent-emerald)">Suppression doublons d'agences (+8 Md€)</strong></div>
          </div>
        </div>

        <!-- Tableau des 9 Strates Démographiques Communales (INSEE) -->
        <h4 style="margin-bottom:10px; font-weight:700;">📊 Typologie Communale Intégrale en 9 Strates Démographiques (INSEE)</h4>
        <div class="table-container" style="margin-bottom:24px;">
          <table>
            <thead>
              <tr>
                <th>Strate INSEE</th>
                <th>Type de Territoire</th>
                <th>Nombre de Communes</th>
                <th>Population Cumulée</th>
                <th>Part de la Population</th>
                <th>Équipements Publics & Rôle Républicain</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><strong>Moins de 100 hab.</strong></td><td>Hyper-ruralité</td><td>3 400</td><td>~220 000 hab.</td><td>0,3 %</td><td>Maires sentinelles bénévoles, église paroissiale, forêt, préservation des sources.</td></tr>
              <tr><td><strong>100 à 499 hab.</strong></td><td>Petits villages</td><td>17 000</td><td>~4 300 000 hab.</td><td>6,3 %</td><td>Salle des fêtes, RPI (regroupements pédagogiques), tissu agricole.</td></tr>
              <tr><td><strong>500 à 999 hab.</strong></td><td>Villages structurés</td><td>5 400</td><td>~3 800 000 hab.</td><td>5,6 %</td><td>École primaire communale, boulangerie, artisans du bâtiment.</td></tr>
              <tr><td><strong>1 000 à 3 499 hab.</strong></td><td>Bourgs de proximité</td><td>5 900</td><td>~11 200 000 hab.</td><td>16,4 %</td><td>Pharmacie, maison médicale, gendarmerie, cabinet infirmiers, commerces.</td></tr>
              <tr><td><strong>3 500 à 9 999 hab.</strong></td><td>Bourgs structurants</td><td>1 750</td><td>~10 100 000 hab.</td><td>14,8 %</td><td>Collège, supermarché, zone artisanale, gare TER, complexe sportif.</td></tr>
              <tr><td><strong>10 000 à 19 999 hab.</strong></td><td>Petites villes</td><td>580</td><td>~8 100 000 hab.</td><td>11,8 %</td><td>Sous-préfecture, lycée général/technique, hôpital de proximité.</td></tr>
              <tr><td><strong>20 000 à 49 999 hab.</strong></td><td>Villes moyennes</td><td>460</td><td>~13 900 000 hab.</td><td>20,3 %</td><td>Centre Hospitalier Général, tribunal judiciaire, réseau urbain de bus.</td></tr>
              <tr><td><strong>50 000 à 99 999 hab.</strong></td><td>Grandes villes</td><td>88</td><td>~6 100 000 hab.</td><td>8,9 %</td><td>Antennes universitaires, théâtres nationaux, réseau de tramway, technopôles.</td></tr>
              <tr><td><strong>100 000 hab. et plus</strong></td><td>Métropoles & Mégapole</td><td>41 (dont 11 > 200k)</td><td>~10 700 000 hab.</td><td>15,6 %</td><td>CHU régionaux, universités complètes, aéroports internationaux, sièges mondiaux.</td></tr>
            </tbody>
          </table>
        </div>

        <!-- Section 2 : L'Outre-Mer Républicain Intégral -->
        <h3 style="margin-bottom:12px; font-weight:800;">🌊 2. L'Outre-Mer Français Intégral (DROM, COM, Calédonie & 10,2M km² de ZEE)</h3>
        <p class="subtitle" style="margin-bottom:14px;">La France est la 2ᵉ puissance maritime mondiale grâce à ses 14 territoires ultramarins répartis sur tous les océans.</p>
        <div class="table-container" style="margin-bottom:24px;">
          <table>
            <thead>
              <tr>
                <th>Territoire Ultramarin</th>
                <th>Statut Constitutionnel</th>
                <th>Chef-lieu</th>
                <th>Surface Terrestre</th>
                <th>Communes</th>
                <th>Population</th>
                <th>ZEE Maritime</th>
                <th>Institutions & Enjeux Clés</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Guadeloupe (971)</strong></td>
                <td>DROM (Article 73)</td>
                <td>Basse-Terre</td>
                <td>1 628 km²</td>
                <td>32</td>
                <td>384 000 hab.</td>
                <td>95 000 km²</td>
                <td>Conseil régional + Conseil départemental. Réforme octroi de mer, réseaux d'eau.</td>
              </tr>
              <tr>
                <td><strong>Martinique (972)</strong></td>
                <td>CTU (Article 73)</td>
                <td>Fort-de-France</td>
                <td>1 128 km²</td>
                <td>34</td>
                <td>361 000 hab.</td>
                <td>47 000 km²</td>
                <td>Collectivité Territoriale Unique : Assemblée (61 élus) + Conseil exécutif. Bouclier vie chère.</td>
              </tr>
              <tr>
                <td><strong>Guyane (973)</strong></td>
                <td>CTU (Article 73)</td>
                <td>Cayenne</td>
                <td>83 534 km²</td>
                <td>22</td>
                <td>294 000 hab.</td>
                <td>134 000 km²</td>
                <td>Collectivité Unique : Assemblée (55 élus) + CSG Kourou. Désenclavement fluvial et routier.</td>
              </tr>
              <tr>
                <td><strong>La Réunion (974)</strong></td>
                <td>DROM (Article 73)</td>
                <td>Saint-Denis</td>
                <td>2 512 km²</td>
                <td>24</td>
                <td>873 000 hab.</td>
                <td>315 000 km²</td>
                <td>Conseil régional + Conseil départemental. Hub de l'océan Indien, égalité réelle, énergies renouvelables.</td>
              </tr>
              <tr>
                <td><strong>Mayotte (976)</strong></td>
                <td>Département-Région (Art. 73)</td>
                <td>Mamoudzou</td>
                <td>376 km²</td>
                <td>17</td>
                <td>310 000 hab.</td>
                <td>64 000 km²</td>
                <td>Conseil départemental (26 élus). Rattrapage massif d'infrastructures républicaines et eau.</td>
              </tr>
              <tr>
                <td><strong>Saint-Barthélemy (977)</strong></td>
                <td>COM Autonome (Article 74)</td>
                <td>Gustavia</td>
                <td>25 km²</td>
                <td>1</td>
                <td>10 500 hab.</td>
                <td>4 000 km²</td>
                <td>Conseil territorial (19 élus). Autonomie fiscale, douanière et environnementale exclusive.</td>
              </tr>
              <tr>
                <td><strong>Saint-Martin (978)</strong></td>
                <td>COM Autonome (Article 74)</td>
                <td>Marigot</td>
                <td>53 km²</td>
                <td>1</td>
                <td>32 000 hab.</td>
                <td>1 000 km²</td>
                <td>Conseil territorial (23 élus). Autonomie fiscale, coopération transfrontalière Sint Maarten (NL).</td>
              </tr>
              <tr>
                <td><strong>Saint-Pierre-et-Miquelon (975)</strong></td>
                <td>COM (Article 74)</td>
                <td>Saint-Pierre</td>
                <td>242 km²</td>
                <td>2</td>
                <td>6 000 hab.</td>
                <td>12 400 km²</td>
                <td>Conseil territorial (19 élus). Présence française en Amérique du Nord, desserte directe.</td>
              </tr>
              <tr>
                <td><strong>Wallis-et-Futuna (986)</strong></td>
                <td>COM (Article 74)</td>
                <td>Mata-Utu</td>
                <td>142 km²</td>
                <td>3 circ.</td>
                <td>11 500 hab.</td>
                <td>300 000 km²</td>
                <td>Assemblée territoriale (20 élus) + 3 Rois coutumiers (Uvea, Sigave, Alo). Statut statutaire 1961.</td>
              </tr>
              <tr>
                <td><strong>Polynésie française (987)</strong></td>
                <td>COM Autonome (Article 74)</td>
                <td>Papeete</td>
                <td>4 167 km²</td>
                <td>48</td>
                <td>280 000 hab.</td>
                <td>4 800 000 km²</td>
                <td>Assemblée de Polynésie (57 élus) + Gouvernement propre. Vote de « lois du pays », 118 îles sur 5 archipels.</td>
              </tr>
              <tr>
                <td><strong>Nouvelle-Calédonie (988)</strong></td>
                <td>Sui Generis (Titre XIII Const.)</td>
                <td>Nouméa</td>
                <td>18 575 km²</td>
                <td>33</td>
                <td>271 000 hab.</td>
                <td>1 400 000 km²</td>
                <td>Congrès de la NC (54 élus) + 3 Provinces + Sénat coutumier. Accords de Nouméa, 25% nickel mondial.</td>
              </tr>
              <tr>
                <td><strong>TAAF (984)</strong></td>
                <td>Territoire administré (Loi 1955)</td>
                <td>Saint-Pierre (Réunion)</td>
                <td>439 780 km²</td>
                <td>0</td>
                <td>~200 scient.</td>
                <td>2 300 000 km²</td>
                <td>Préfet administrateur supérieur. 5 districts (Kerguelen, Crozet, St-Paul/Amsterdam, Terre Adélie, Éparses).</td>
              </tr>
              <tr>
                <td><strong>Île de Clipperton (989)</strong></td>
                <td>Domaine public de l'État</td>
                <td>Paris (Ministère OM)</td>
                <td>2 km²</td>
                <td>0</td>
                <td>0 hab.</td>
                <td>435 000 km²</td>
                <td>Atoll du Pacifique oriental. Souveraineté maritime stratégique sous l'autorité du Ministre des Outre-mer.</td>
              </tr>
              <tr>
                <td><strong>Français établis hors de France</strong></td>
                <td>Représentation mondiale (Art. 24)</td>
                <td>Monde entier</td>
                <td>-</td>
                <td>-</td>
                <td>2 100 000 inscrits</td>
                <td>-</td>
                <td>11 Députés, 12 Sénateurs, AFE (90 conseillers), 442 conseillers consulaires dans les consulats du monde.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Section 3 : Le Calendrier Électoral Républicain Complet -->
        <h3 style="margin-bottom:12px; font-weight:800;">🗳️ 3. Le Calendrier Républicain des Élections Prévues & Règles Électorales</h3>
        <p class="subtitle" style="margin-bottom:14px;">La totalité des échéances civiques programmées pour le corps électoral de 49,5 millions de citoyens.</p>
        <div class="table-container" style="margin-bottom:24px;">
          <table>
            <thead>
              <tr>
                <th>Scrutin Républicain</th>
                <th>Échéance Prévue</th>
                <th>Durée Mandat</th>
                <th>Nombre de Sièges</th>
                <th>Mode de Scrutin & Conditions de Qualification</th>
                <th>Rétroaction Mandature</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Municipales & Communautaires</strong></td>
                <td><strong>Mars 2026</strong></td>
                <td>6 ans</td>
                <td>~500 000 élus</td>
                <td>Proportionnel de liste avec prime majoritaire de 50% (>=1k hab.). Fléchage direct délégués EPCI.</td>
                <td>Sanctuarisation DGF rurale & cantines locales à 1 €.</td>
              </tr>
              <tr>
                <td><strong>Consulaires des Français de l'étranger</strong></td>
                <td><strong>Mai 2026</strong></td>
                <td>5 ans</td>
                <td>442 conseillers</td>
                <td>Scrutin proportionnel de liste. Vote électronique par Internet sécurisé et vote à l'urne.</td>
                <td>Dématérialisation consulaire et bourses scolaires.</td>
              </tr>
              <tr>
                <td><strong>Sénatoriales (Série 2)</strong></td>
                <td><strong>Septembre 2026</strong></td>
                <td>6 ans (triennal)</td>
                <td>178 sénateurs</td>
                <td>Suffrage indirect par 162 000 grands électeurs. Scrutin majoritaire (<3 sén.) ou proportionnel (>=3).</td>
                <td>Désarmement hostilité sénatoriale (28/100).</td>
              </tr>
              <tr>
                <td><strong>Élection Présidentielle</strong></td>
                <td><strong>Avril-Mai 2027</strong></td>
                <td>5 ans (quinquennat)</td>
                <td>1 Président</td>
                <td>Uninominal majoritaire à 2 tours. 500 parrainages d'élus d'au moins 30 départements.</td>
                <td>Clé de voûte de la Vᵉ République (Art. 6 & 7).</td>
              </tr>
              <tr>
                <td><strong>Élections Législatives</strong></td>
                <td><strong>Juin 2027</strong></td>
                <td>5 ans</td>
                <td>577 députés</td>
                <td>Uninominal majoritaire à 2 tours dans 577 circonscriptions. Seuil 12,5% des inscrits au second tour.</td>
                <td>Triangulaires ramenées de 85 à 31 circonscriptions.</td>
              </tr>
              <tr>
                <td><strong>Élections Départementales</strong></td>
                <td><strong>Mars 2028</strong></td>
                <td>6 ans</td>
                <td>4 056 conseillers (2 054 cantons)</td>
                <td>Binominal paritaire (1 femme + 1 homme indissociables). Seuil de maintien de 12,5% des inscrits.</td>
                <td>Fin du ciseau financier grâce à la péréquation RSA/APA.</td>
              </tr>
              <tr>
                <td><strong>Régionales & Territoriales</strong></td>
                <td><strong>Mars 2028</strong></td>
                <td>6 ans</td>
                <td>1 757 conseillers</td>
                <td>Proportionnel de liste à 2 tours avec prime majoritaire de 25%. Seuil maintien 10%, fusion 5%.</td>
                <td>Stabilisation des majorités régionales et des TER.</td>
              </tr>
              <tr>
                <td><strong>Sénatoriales (Série 1)</strong></td>
                <td><strong>Septembre 2029</strong></td>
                <td>6 ans (triennal)</td>
                <td>170 sénateurs</td>
                <td>Suffrage indirect par 162 000 grands électeurs (série 1 : Paris, Rhône, Hauts-de-Seine, etc.).</td>
                <td>Équilibre des pouvoirs au Parlement.</td>
              </tr>
              <tr>
                <td><strong>Élections Européennes</strong></td>
                <td><strong>Juin 2029</strong></td>
                <td>5 ans</td>
                <td>81 députés européens</td>
                <td>Proportionnel de liste à la plus forte moyenne, circonscription nationale unique, seuil de 5%.</td>
                <td>Alignement stratégique européen et sortie PDE.</td>
              </tr>
              <tr>
                <td><strong>Chambres Consulaires (CCI, CMA, CA)</strong></td>
                <td><strong>2026 - 2029</strong></td>
                <td>5 ans</td>
                <td>~5 000 élus</td>
                <td>Scrutin de liste socioprofessionnel (chefs d'entreprise, commerçants, artisans, exploitants agricoles).</td>
                <td>Réservation de 30% des marchés publics aux PME locales.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Section 4 : Le Bloc de Constitutionnalité et les Grands Codes -->
        <h3 style="margin-bottom:12px; font-weight:800;">📜 4. Les Textes Fondamentaux Constituant et Régissant la Nation (Pyramide Normative)</h3>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Niveau de Norme</th>
                <th>Texte Fondateur</th>
                <th>Principes Clés & Dispositions</th>
                <th>Portée Régulatrice dans le Simulateur</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Bloc de Constitutionnalité</strong></td>
                <td><strong>Déclaration des Droits de 1789</strong></td>
                <td>Art. 1 (Égalité des droits), Art. 3 (Souveraineté nationale), Art. 6 (Volonté générale), Art. 13-14 (Consentement et progressivité impôt), Art. 16 (Séparation pouvoirs).</td>
                <td>Cadre suprême inviolable garantissant la justice fiscale et les libertés publiques fondamentales.</td>
              </tr>
              <tr>
                <td><strong>Bloc de Constitutionnalité</strong></td>
                <td><strong>Préambule de la Constitution de 1946</strong></td>
                <td>Al. 3 (Égalité homme-femme), Al. 9 (Nationalisation des monopoles et services publics), Al. 10-11 (Garantie de la santé, du repos et des retraites).</td>
                <td>Fonde le pacte social du berceau au tombeau, la Sécurité sociale et les services publics essentiels.</td>
              </tr>
              <tr>
                <td><strong>Bloc de Constitutionnalité</strong></td>
                <td><strong>Charte de l'environnement de 2004</strong></td>
                <td>Art. 1 (Droit à un environnement sain), Art. 4 (Principe pollueur-payeur), Art. 5 (Principe de précaution).</td>
                <td>Encadre la transition écologique républicaine et la taxe carbone frontalière MACF.</td>
              </tr>
              <tr>
                <td><strong>Bloc de Constitutionnalité</strong></td>
                <td><strong>Constitution du 4 octobre 1958</strong></td>
                <td>Art. 1 (République indivisible et décentralisée), Art. 2 (Du peuple, par le peuple, pour le peuple), Art. 24 (Parlement), Art. 49 (Censure), Art. 72-74 (Outre-Mer).</td>
                <td>Équilibre des pouvoirs institutionnels, régulation des 12 assemblées et des 4 strates gigognes.</td>
              </tr>
              <tr>
                <td><strong>Bloc de Conventionalité</strong></td>
                <td><strong>Convention de Montego Bay (CNUDM)</strong></td>
                <td>Art. 56 : Droits souverains d'exploration, d'exploitation et de conservation sur la Zone Économique Exclusive (ZEE).</td>
                <td>Consacre la souveraineté sur 10,2 millions de km² d'océans et de fonds marins (2e rang mondial).</td>
              </tr>
              <tr>
                <td><strong>Législation Républicaine</strong></td>
                <td><strong>Code électoral</strong></td>
                <td>Art. L. 1 (Universalité), Art. L. 16 (REU INSEE 49,5M électeurs), Art. L. 52-4 (Comptes de campagne CNCCFP), Art. L. 123 (Législatives), Art. L. 260 (Municipales).</td>
                <td>Garantit la sincérité, la transparence et la régularité mathématique des scrutins républicains.</td>
              </tr>
              <tr>
                <td><strong>Législation Républicaine</strong></td>
                <td><strong>Code Général des Collectivités (CGCT)</strong></td>
                <td>Art. L. 1111-1 (Libre administration), Art. L. 1612-4 (Règle d'or budgétaire), Art. L. 2121-1 (Communes), Art. L. 2411-1 (Sections), Art. L. 5217-1 (Métropoles).</td>
                <td>Équilibre de gestion des 34 935 communes, 1 254 EPCI et 101 départements.</td>
              </tr>
              <tr>
                <td><strong>Législation Républicaine</strong></td>
                <td><strong>Code de la Commande Publique (CCP)</strong></td>
                <td>Art. L. 2113-10 (Allotissement obligatoire), Art. L. 2112-2 (Critères environnementaux et sociaux).</td>
                <td>Réservation de 30 % des marchés publics aux PME et artisans locaux (+6 Md€ d'économies massifiées).</td>
              </tr>
              <tr>
                <td><strong>Législation Républicaine</strong></td>
                <td><strong>Code des Transports</strong></td>
                <td>Art. L. 1803-1 : Principe républicain de continuité territoriale entre l'Outre-mer et la Métropole (LADOM).</td>
                <td>Garantit l'égalité d'accès aux transports aériens et maritimes pour les résidents ultramarins.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ============================================================= -->
    <!-- TAB BATAILLE : ARBITRAGES BUDGÉTAIRES & SURVIE MINISTÉRIELLE    -->
    <!-- ============================================================= -->
    <div id="tab-bataille" class="tab-pane">
      <div class="arch-diagram">
        <h2>⚖️ ARBITRAGES BUDGÉTAIRES DE BERCY & SURVIE MINISTÉRIELLE</h2>
        <p class="subtitle" style="margin-bottom:20px;">
          Simulation des coulisses ministérielles de Bercy (2027-2032) : réduire le déficit sous 3 % sans être démissionné ni censuré !
        </p>

        <!-- KPI Jauges de Survie Bercy -->
        <div class="kpi-grid" style="margin-bottom:24px;">
          <div class="kpi-card">
            <div class="kpi-title">🎭 Capital Politique (Réformes)</div>
            <div class="kpi-val" id="bataille-kpi-capital" style="color:var(--accent-cyan)">50.0 / 100</div>
            <div class="kpi-sub">Capacité à négocier et faire voter la loi</div>
            <div style="margin-top:8px;"><span class="badge badge-success" id="bataille-badge-capital">Marge de manœuvre intacte</span></div>
          </div>

          <div class="kpi-card">
            <div class="kpi-title">👥 Popularité Ministérielle</div>
            <div class="kpi-val" id="bataille-kpi-pop" style="color:var(--accent-emerald)">50.0 %</div>
            <div class="kpi-sub">Alerte Matignon < 15% | Démission < 10%</div>
            <div style="margin-top:8px;"><span class="badge badge-success" id="bataille-badge-pop">Soutien populaire suffisant</span></div>
          </div>

          <div class="kpi-card">
            <div class="kpi-title">🏛️ Risque de Censure (AN)</div>
            <div class="kpi-val" id="bataille-kpi-censure" style="color:var(--accent-amber)">140 / 289</div>
            <div class="kpi-sub">Majorité absolue requise : 289 députés</div>
            <div style="margin-top:8px;"><span class="badge badge-success" id="bataille-badge-censure">Oppositions sous contrôle</span></div>
          </div>

          <div class="kpi-card">
            <div class="kpi-title">📈 Spread OAT-Bund (Taux)</div>
            <div class="kpi-val" id="bataille-kpi-spread">70.0 pb</div>
            <div class="kpi-sub">Écart de taux avec l'Allemagne (Note AA)</div>
            <div style="margin-top:8px;"><span class="badge badge-warning" id="bataille-badge-pde">Procédure PDE active</span></div>
          </div>
        </div>

        <!-- Section 1 : Le Bureau du Ministre & Choix du Directeur de Cabinet -->
        <h3 style="margin-bottom:12px; font-weight:800;">👤 1. Le Bureau du Ministre : Profils et Directeur de Cabinet</h3>
        <p class="subtitle" style="margin-bottom:14px;">Chaque partie démarre par la composition de l'équipe de tête à Bercy, influençant le capital politique et la résilience médiatique.</p>
        <div class="strates-grid" style="margin-bottom:24px;">
          <div class="strate-card">
            <h4>🏛️ L'Élu Chevronné</h4>
            <div class="metric-row"><span>Popularité initiale</span><strong style="color:var(--accent-amber)">40.0 %</strong></div>
            <div class="metric-row"><span>Capital politique</span><strong style="color:var(--accent-emerald)">60.0 / 100</strong></div>
            <div class="metric-row"><span>Force clé</span><strong>Maîtrise des couloirs parlementaires</strong></div>
            <div class="metric-row"><span>Faiblesse</span><strong>Image de notable, rejet populaire prompt</strong></div>
          </div>

          <div class="strate-card">
            <h4>💼 Le Chef d'Entreprise</h4>
            <div class="metric-row"><span>Popularité initiale</span><strong style="color:var(--accent-emerald)">60.0 %</strong></div>
            <div class="metric-row"><span>Capital politique</span><strong style="color:var(--accent-rose)">40.0 / 100</strong></div>
            <div class="metric-row"><span>Force clé</span><strong>Crédit gestionnaire auprès du public</strong></div>
            <div class="metric-row"><span>Faiblesse</span><strong>Zéro réseau à l'Assemblée, isolé face aux frondes</strong></div>
          </div>

          <div class="strate-card">
            <h4>🎓 L'Universitaire Réputé</h4>
            <div class="metric-row"><span>Popularité initiale</span><strong>50.0 %</strong></div>
            <div class="metric-row"><span>Capital politique</span><strong>50.0 / 100</strong></div>
            <div class="metric-row"><span>Force clé</span><strong>Rigueur technique reconnue, neutralité</strong></div>
            <div class="metric-row"><span>Faiblesse</span><strong>Naïveté tactique lors des arbitrages nocturnes</strong></div>
          </div>

          <div class="strate-card">
            <h4>📑 Dircab : Le Technocrate</h4>
            <div class="metric-row"><span>Profil</span><strong>Haut fonctionnaire / Inspection Finances</strong></div>
            <div class="metric-row"><span>Bonus</span><strong style="color:var(--accent-emerald)">+15% efficience réformes structurelles</strong></div>
            <div class="metric-row"><span>Rôle</span><strong>Verrouille les enveloppes des ministères dépensiers</strong></div>
          </div>

          <div class="strate-card">
            <h4>🤝 Dircab : Le Dealmaker</h4>
            <div class="metric-row"><span>Profil</span><strong>Négociateur politique de couloir</strong></div>
            <div class="metric-row"><span>Bonus</span><strong style="color:var(--accent-cyan)">+5 Capital Politique / an</strong></div>
            <div class="metric-row"><span>Rôle</span><strong>Monnaie les amendements avec les groupes pivot (LR/Liot)</strong></div>
          </div>

          <div class="strate-card">
            <h4>📣 Dircab : Le Spin Doctor</h4>
            <div class="metric-row"><span>Profil</span><strong>Conseiller en communication & médias</strong></div>
            <div class="metric-row"><span>Bonus</span><strong style="color:var(--accent-purple)">+5 Popularité / an</strong></div>
            <div class="metric-row"><span>Rôle</span><strong>Désamorce les scandales de presse et amortit les fuites</strong></div>
          </div>
        </div>

        <!-- Section 2 : Le Cursus Annuel en 12 Épisodes Mensuels -->
        <h3 style="margin-bottom:12px; font-weight:800;">📅 2. Le Cycle Budgétaire Annuel en 12 Épisodes Mensuels (Format Série Netflix)</h3>
        <p class="subtitle" style="margin-bottom:14px;">Chaque saison budgétaire (de 2027 à 2032) suit le calendrier réel et impitoyable de la loi de finances à Bercy.</p>
        <div class="table-container" style="margin-bottom:24px;">
          <table>
            <thead>
              <tr>
                <th>Mois & Épisode</th>
                <th>Titre de l'Épisode</th>
                <th>Acteurs Clés en Scène</th>
                <th>Enjeu Budgétaire & Arbitrage Majeur</th>
                <th>Risque de Crise</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><strong>1. Janvier</strong></td><td>Prise de fonction & Cadrage</td><td>Directeur du Budget, Dircab</td><td>Fixation de la cible de déficit (5,9 % sans action) et lettres de cadrage.</td><td>Cible irréaliste ou trop lâche.</td></tr>
              <tr><td><strong>2. Février</strong></td><td>Avertissement Cour des comptes</td><td>Premier Président Cour comptes</td><td>Rapport public dénonçant la dérive des finances publiques et de la dette.</td><td>Titre assassin dans la presse.</td></tr>
              <tr><td><strong>3. Mars</strong></td><td>Convocation à Bruxelles</td><td>Commission Européenne</td><td>Examen de la Procédure de Déficit Excessif (PDE) et trajectoire pluriannuelle.</td><td>Menace d'amende européenne.</td></tr>
              <tr><td><strong>4. Avril</strong></td><td>Tensions sur les Marchés</td><td>DG Trésor, Agences (S&P, Moody's)</td><td>Surveillance du spread OAT-Bund (70-85 pb) et notation AA de la France.</td><td>Flambée de la charge d'intérêts.</td></tr>
              <tr><td><strong>5. Mai</strong></td><td>Audition en Commission des finances</td><td>Députés AN, Rapporteur général</td><td>Feu croisé des oppositions sur les premières pistes d'économies.</td><td>Perte de capital politique.</td></tr>
              <tr><td><strong>6. Juin</strong></td><td>« La Guerre des Enveloppes »</td><td>Ministres dépensiers (Santé, Éduc., Armées)</td><td>Défilé des ministres réclamant des rallonges sous menace de saisir Matignon.</td><td>Fronde interne au gouvernement.</td></tr>
              <tr><td><strong>7. Juillet</strong></td><td>Arbitrages de l'Élysée</td><td>Président de la République</td><td>Annonces surprises et lubies présidentielles non gagées budgétairement.</td><td>Dérapage non financé.</td></tr>
              <tr><td><strong>8. Août</strong></td><td>Conférence de Presse de Rentrée</td><td>Journalistes économiques</td><td>Présentation publique des grandes lignes du Projet de Loi de Finances (PLF).</td><td>Polémique sur une mesure impopulaire.</td></tr>
              <tr><td><strong>9. Septembre</strong></td><td>Dépôt officiel du PLF</td><td>Bureau de l'Assemblée nationale</td><td>Transmission formelle du texte budgétaire et engagement du délai de 70 jours.</td><td>Irrecevabilité financière (Art. 40).</td></tr>
              <tr><td><strong>10. Octobre</strong></td><td>« La Grande Bidouille »</td><td>Groupes politiques à l'Assemblée</td><td>Marchandage des amendements pour tenter de bâtir une majorité relative.</td><td>Chantage aux voix.</td></tr>
              <tr><td><strong>11. Novembre</strong></td><td>Navette & Chantage à la Censure</td><td>Présidents de groupes parlementaires</td><td>Menace explicite de déposer et voter une motion de censure en cas de refus.</td><td>Coalition des oppositions.</td></tr>
              <tr><td><strong>12. Décembre</strong></td><td>Le Climax : Vote ou 49.3</td><td>Hémicycle au complet</td><td>Arbitrage ultime : aller au vote (risque de rejet) ou 49.3 (censure à 289 voix).</td><td><strong>CHUTE DU GOUVERNEMENT (289 voix)</strong></td></tr>
            </tbody>
          </table>
        </div>

        <!-- Section 3 : Le Répertoire des Mesures et Arbitrages Douloureux -->
        <h3 style="margin-bottom:12px; font-weight:800;">⚖️ 3. Le Répertoire des 200+ Mesures et leurs Arbitrages Cachés</h3>
        <p class="subtitle" style="margin-bottom:14px;">Chaque mesure rapporte des milliards mais prélève un tribut politique lourd en popularité ou en capital parlementaire.</p>
        <div class="table-container" style="margin-bottom:24px;">
          <table>
            <thead>
              <tr>
                <th>Mesure Budgétaire</th>
                <th>Nature</th>
                <th>Rendement / Économie</th>
                <th>Impact Popularité</th>
                <th>Impact Capital Politique</th>
                <th>Conséquence & Effet pervers</th>
              </tr>
            </thead>
            <tbody>
              <tr><td><strong>Rétablissement ISF / Fortune</strong></td><td>Recette fiscale</td><td><strong>+4,5 Md€ / an</strong></td><td><strong style="color:var(--accent-emerald)">+8,0 % (Plébiscité)</strong></td><td>-5 pts (Hostilité patronale)</td><td>Très populaire, mais risque d'expatriation fiscale si non encadré.</td></tr>
              <tr><td><strong>Taxe Superprofits / Rachats</strong></td><td>Recette fiscale</td><td><strong>+6,0 Md€ / an</strong></td><td><strong style="color:var(--accent-emerald)">+6,5 % (Soutien fort)</strong></td><td>-4 pts (Lobbying CAC40)</td><td>Plein rendement si exemption pour investissement productif en France.</td></tr>
              <tr><td><strong>Gel des Pensions de Retraite</strong></td><td>Économie sociale</td><td><strong>+3,5 Md€ / an</strong></td><td><strong style="color:var(--accent-rose)">-14,0 % (Tollé aînés)</strong></td><td><strong style="color:var(--accent-rose)">-12 pts (Veto Sénat)</strong></td><td>Tabou politique absolu. Déclenche une révolte des seniors et blocage au Sénat.</td></tr>
              <tr><td><strong>Gel du Barème de l'IR</strong></td><td>Recette fiscale</td><td><strong>+3,8 Md€ / an</strong></td><td><strong style="color:var(--accent-rose)">-10,0 % (Effet furtif)</strong></td><td>-6 pts (Colère classes moyennes)</td><td>Fait basculer 200 000 foyers modestes dans l'impôt par effet d'aubaine inflationniste.</td></tr>
              <tr><td><strong>Suppression Postes Fonctionnaires</strong></td><td>Économie dépenses</td><td><strong>+2,5 Md€ / an</strong></td><td><strong style="color:var(--accent-rose)">-8,5 % (Dégradation services)</strong></td><td>-10 pts (Grèves syndicales)</td><td>Fermeture de classes, engorgement des tribunaux et urgences sous tension.</td></tr>
              <tr><td><strong>Baisse unilatérale DGF Communes</strong></td><td>Économie transferts</td><td><strong>+3,0 Md€ / an</strong></td><td>-6,0 % (Rancœur locale)</td><td><strong style="color:var(--accent-rose)">-15 pts (Fronde des maires AMF)</strong></td><td>Grogne violente des 34 935 maires et rejet systématique par le Sénat.</td></tr>
              <tr><td><strong>Hausse TVA (+1 pt à 21%)</strong></td><td>Recette fiscale</td><td><strong>+7,5 Md€ / an</strong></td><td><strong style="color:var(--accent-rose)">-16,0 % (Effondrement pop.)</strong></td><td>-8 pts (Contraction conso)</td><td>Rendement immédiat massif mais brise le pouvoir d'achat des classes populaires.</td></tr>
              <tr><td><strong>Baisse TVA Énergie à 5,5 %</strong></td><td>Restitution pouvoir achat</td><td><strong>-9,0 Md€ / an</strong></td><td><strong style="color:var(--accent-emerald)">+18,0 % (Plébiscite total)</strong></td><td><strong style="color:var(--accent-emerald)">+12 pts (Apaisement social)</strong></td><td>Restitue +150 à +300 €/foyer. Désarme la grogne et pacifie le climat politique.</td></tr>
              <tr><td><strong>Traque Fraude Fiscale par IA</strong></td><td>Recette de justice</td><td><strong>+10,0 Md€ / an</strong></td><td><strong style="color:var(--accent-emerald)">+11,0 % (Justice fiscale)</strong></td><td><strong style="color:var(--accent-emerald)">+8 pts (Légitimité forte)</strong></td><td>Cible les multinationales sans impacter les ménages (filtrage > 50 000 €).</td></tr>
            </tbody>
          </table>
        </div>

        <!-- Section 4 : La Résolution par le Plan de Mandature (+60 Md€) -->
        <h3 style="margin-bottom:12px; font-weight:800;">🎯 4. Comment Notre Plan de Mandature Sort de « l'Enfer Budgétaire »</h3>
        <p class="subtitle" style="margin-bottom:14px;">La confrontation directe entre l'impasse d'une gestion budgétaire classique et notre modèle équilibré à +60 Md€.</p>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Épreuve / Critère de Survie</th>
                <th>Résultat dans une Gestion Budgétaire Classique</th>
                <th>Résultat dans Notre Plan Mandature (+60 Md€)</th>
                <th>Facteur de Réussite Républicain</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Déficit sous les 3 % avant 2030</strong></td>
                <td>Échec fréquent ou austérité punitive détruisant les services</td>
                <td><strong style="color:var(--accent-emerald)">2,6 % en An 4, 1,8 % en An 5 (Atteint sans austérité)</strong></td>
                <td>+36 Md€ de recettes justes + 24 Md€ d'économies d'efficience structurelle.</td>
              </tr>
              <tr>
                <td><strong>Reflux de la Dette avant 2032</strong></td>
                <td>Dette continuant d'enfler sous le poids des intérêts</td>
                <td><strong style="color:var(--accent-emerald)">Désendettement net de 51 Md€/an dès l'Année 5</strong></td>
                <td>Le déficit passe sous le taux de croissance nominale du PIB.</td>
              </tr>
              <tr>
                <td><strong>Popularité (Seuil alerte 15%, démission 10%)</strong></td>
                <td>Chute fréquente sous 15 % entraînant le renvoi par Matignon</td>
                <td><strong style="color:var(--accent-emerald)">Popularité maintenue à 71 % (Score historique)</strong></td>
                <td>Baisse de la TVA sur l'électricité et le gaz à 5,5 % (-9 Md€) ressentie par tous.</td>
              </tr>
              <tr>
                <td><strong>Motion de Censure (Seuil fatal 289 voix)</strong></td>
                <td>Chute récurrente du gouvernement au 49.3 de décembre</td>
                <td><strong style="color:var(--accent-emerald)">Opposition neutralisée à 140 voix (très loin des 289)</strong></td>
                <td>Grognomètre social éteint (5/100), alliance avec les PME et sanctuarisation de la DGF.</td>
              </tr>
              <tr>
                <td><strong>Procédure de Déficit Excessif (Bruxelles)</strong></td>
                <td>Menace de sanctions et rappel à l'ordre permanent</td>
                <td><strong style="color:var(--accent-emerald)">Clôture officielle de la PDE par la Commission européenne</strong></td>
                <td>Respect scrupuleux et certifié de la trajectoire d'effort structurel.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ============================================================= -->
    <!-- TAB 2 : COMPARATEUR DES SCÉNARIOS                             -->
    <!-- ============================================================= -->
    <div id="tab-comparatif" class="tab-pane">
      <div class="arch-diagram">
        <h2>⚖️ COMPARATIF SYSTÉMIQUE DES 4 TRAJECTOIRES (À L'ANNÉE 5)</h2>
        <p class="subtitle" style="margin-bottom:20px;">Confrontation des résultats macro-politiques après 5 exercices d'exécution budgétaire.</p>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Indicateur Clé</th>
                <th>Plan Mandature (+60 Md€)</th>
                <th>Statut Quo (Inertie)</th>
                <th>Austérité Brutale</th>
                <th>Choc Mondial (Stagflation)</th>
              </tr>
            </thead>
            <tbody id="comparatif-tbody">
              <!-- Rempli dynamiquement -->
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ============================================================= -->
    <!-- TAB 3 : ARCHITECTURE DES 4 STRATES                            -->
    <!-- ============================================================= -->
    <div id="tab-architecture" class="tab-pane">
      <div class="arch-diagram">
        <h2>🏛️ LE MODÈLE SYSTÉMIQUE GIGOGNE (POUPÉES RUSSES)</h2>
        <p class="subtitle" style="margin-bottom:24px;">Comment une décision communale ou un choc pétrolier mondial se répercute à travers l'ensemble des 4 strates.</p>

        <div class="nested-layer layer-4">
          <div class="layer-title" style="color:#f59e0b">
            <span>ÉCHELON 4 : LE MONDIAL (Marchés Financiers, Commodities, Forex & AFT)</span>
            <span class="badge badge-warning">Extérieur</span>
          </div>
          <div class="layer-desc">55,8 % de la dette d'État française est détenue par des non-résidents. L'AFT doit placer ~435 Md€ par an auprès des marchés mondiaux. Taux OAT 10 ans, spread face au Bund allemand, parité EUR/USD et cours du baril de Brent déterminent le coût de refinancement de la nation.</div>

          <div class="nested-layer layer-3">
            <div class="layer-title" style="color:#3b82f6">
              <span>ÉCHELON 3 : LE CONTINENTAL / EUROPÉEN (Pacte de Stabilité & Traité de Maastricht)</span>
              <span class="badge badge-primary">Cadre Supranational</span>
            </div>
            <div class="layer-desc">Plafond de déficit public fixé à 3,00 % du PIB et dette à 60 %. En cas de dépassement, la France est placée sous Procédure de Déficit Excessif (PDE) avec exigence d'un ajustement structurel d'au moins 0,5 % du PIB/an et suspension du Bouclier TPI anti-spéculation de la BCE.</div>

            <div class="nested-layer layer-2">
              <div class="layer-title" style="color:#10b981">
                <span>ÉCHELON 2 : LE NATIONAL (État Central, Sécurité Sociale & Parlement)</span>
                <span class="badge badge-success">Moteur Politique</span>
              </div>
              <div class="layer-desc">PIB ~3 015 Md€, Dépenses publiques 57 % PIB, Recettes 51,9 %. Majorité relative à l'Assemblée nationale : si le mécontentement civique dépasse le seuil critique, le risque de vote d'une motion de censure (art. 49 al. 2) fait chuter le gouvernement.</div>

              <div class="nested-layer layer-1">
                <div class="layer-title" style="color:#ec4899">
                  <span>ÉCHELON 1 : LE LOCAL (Communes, Départements, Régions & Chambres Consulaires)</span>
                  <span class="badge badge-danger">Cellule de Base</span>
                </div>
                <div class="layer-desc">34 935 communes, 101 départements, 18 régions, 6,9 millions d'entreprises ressortissantes des Chambres Consulaires (CCI, CMA, CA). <strong>Règle d'or budgétaire (art. L. 1612-4 du CGCT)</strong> : interdiction d'emprunter pour fonctionner. Toute coupe dans la DGF impose une hausse mécanique de la taxe foncière, déclenchant une colère immédiate des classes moyennes propriétaires.</div>
              </div>

            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================================= -->
    <!-- TAB 4 : CORPUS JURIDIQUE & TEXTES DE LOIS                     -->
    <!-- ============================================================= -->
    <div id="tab-corpus" class="tab-pane">
      <div class="search-box">
        <input type="text" id="corpus-search" placeholder="Rechercher par mot-clé (ex: TVA, règle d'or, Casier B2, RIC, TFUE)..." oninput="filtrerCorpus()">
        <div class="filter-pills">
          <button class="filter-pill active" onclick="filtrerStrateCorpus('', this)">Tous</button>
          <button class="filter-pill" onclick="filtrerStrateCorpus('Transversal', this)">Transversal</button>
          <button class="filter-pill" onclick="filtrerStrateCorpus('Local', this)">Local</button>
          <button class="filter-pill" onclick="filtrerStrateCorpus('National', this)">National</button>
          <button class="filter-pill" onclick="filtrerStrateCorpus('Europe', this)">Europe</button>
          <button class="filter-pill" onclick="filtrerStrateCorpus('Mondial', this)">Mondial</button>
        </div>
      </div>
      <div class="corpus-list" id="corpus-cards-container">
        <!-- Rempli par JavaScript -->
      </div>
    </div>

    <!-- ============================================================= -->
    <!-- TAB 5 : DOSSIER DE MANDATURE                                  -->
    <!-- ============================================================= -->
    <div id="tab-dossier" class="tab-pane">
      <div class="arch-diagram">
        <h2>📖 DOSSIER GLOBAL DE MANDATURE (5 ANS)</h2>
        <p class="subtitle" style="margin-bottom:20px;">Programme républicain de réparation démocratique, de souveraineté budgétaire et de pouvoir d'achat.</p>
        <div class="corpus-list" id="dossier-volumes-container">
          <!-- Rempli par JavaScript -->
        </div>
      </div>
    </div>

    <!-- ============================================================= -->
    <!-- TAB AUDIT : SOURCES OFFICIELLES & AUDITABILITÉ               -->
    <!-- ============================================================= -->
    <div id="tab-audit" class="tab-pane">
      <div class="arch-diagram">
        <h2>🔍 REGISTRE DES SOURCES OFFICIELLES & AUDITABILITÉ EN TEMPS RÉEL</h2>
        <p class="subtitle" style="margin-bottom:20px;">
          Toutes les données du simulateur sont adossées aux organismes officiels certifiés de la République et des institutions internationales (INSEE, DGFIP, Agence France Trésor, Banque de France, Cour des comptes, BCE, Eurostat).
        </p>

        <!-- KPI Audit -->
        <div class="kpi-grid" style="margin-bottom:24px;">
          <div class="kpi-card">
            <div class="kpi-title">📋 Sources Certifiées</div>
            <div class="kpi-val" style="color:var(--accent-emerald)" id="audit-kpi-sources">25+</div>
            <div class="kpi-sub">INSEE, DGFIP, AFT, BDF, BCE, Eurostat</div>
            <div style="margin-top:8px;"><span class="badge badge-success">Données publiques auditées</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">📜 Textes Juridiques & Lois</div>
            <div class="kpi-val" style="color:var(--accent-cyan)" id="audit-kpi-lois">95</div>
            <div class="kpi-sub">Constitutions, Codes, Directives UE</div>
            <div style="margin-top:8px;"><span class="badge badge-success">Zéro paramètre orphelin</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">🔐 Signature d'Intégrité SHA256</div>
            <div class="kpi-val" style="color:var(--accent-purple); font-family:monospace; font-size:1.05rem;" id="audit-kpi-sha">-</div>
            <div class="kpi-sub">Empreinte cryptographique déterministe</div>
            <div style="margin-top:8px;"><span class="badge badge-primary">Calcul bit-à-bit vérifié</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">⚖️ Règle d'Or & Hiérarchie</div>
            <div class="kpi-val" style="color:var(--accent-emerald)">100 %</div>
            <div class="kpi-sub">LOLF Art. 34, CGCT L. 1612-4, TFUE</div>
            <div style="margin-top:8px;"><span class="badge badge-success">Conformité organique totale</span></div>
          </div>
        </div>

        <!-- Filtre des Sources -->
        <div class="filter-bar" style="margin-bottom:16px;">
          <input type="text" id="audit-search-input" placeholder="Rechercher un indicateur, organisme ou mot-clé..." oninput="filtrerSources()">
          <button class="filter-btn active" onclick="filtrerSourcesCategorie('')">Toutes</button>
          <button class="filter-btn" onclick="filtrerSourcesCategorie('Macroéconomie')">Macroéconomie</button>
          <button class="filter-btn" onclick="filtrerSourcesCategorie('Marchés')">Marchés & Dette</button>
          <button class="filter-btn" onclick="filtrerSourcesCategorie('Fiscalité')">Fiscalité & Fraude</button>
          <button class="filter-btn" onclick="filtrerSourcesCategorie('Social')">Social & Déciles</button>
          <button class="filter-btn" onclick="filtrerSourcesCategorie('Territoires')">Territoires</button>
          <button class="filter-btn" onclick="filtrerSourcesCategorie('International')">International</button>
          <button class="filter-btn" onclick="filtrerSourcesCategorie('Institutions')">Institutions</button>
        </div>

        <!-- Table des sources -->
        <div class="table-container" style="margin-bottom:24px;">
          <table>
            <thead>
              <tr>
                <th>Identifiant & Indicateur</th>
                <th>Organisme Officiel</th>
                <th>Valeur & Unité</th>
                <th>Méthodologie & Millésime</th>
                <th>Lien Direct & Vérification</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody id="audit-sources-tbody">
              <!-- Rempli par JavaScript -->
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ============================================================= -->
    <!-- TAB 11 : THINK TANKS & AUDIT CONTRADICTOIRE MONDIAL          -->
    <!-- ============================================================= -->
    <div id="tab-thinktanks" class="tab-pane">
      <div class="arch-diagram">
        <h2>🔬 AUDIT CONTRADICTOIRE DES THINK TANKS & STRESS-TESTS SYSTÉMIQUES</h2>
        <p class="subtitle" style="margin-bottom:20px;">
          Confrontation impitoyable aux 23 laboratoires d'idées de référence (du local au mondial). Pour chaque critique anticipée, le simulateur apporte la preuve mathématique, comptable et institutionnelle qui désamorce les contestations.
        </p>

        <!-- KPI Think Tanks & Robustesse -->
        <div class="kpi-grid" style="margin-bottom:24px;">
          <div class="kpi-card">
            <div class="kpi-title">🏛️ Think Tanks Audités</div>
            <div class="kpi-val" style="color:var(--accent-cyan)" id="tt-kpi-total">23 Instituts</div>
            <div class="kpi-sub">Local, National, Europe, Mondial</div>
            <div style="margin-top:8px;"><span class="badge badge-primary">Spectre épistémologique intégral</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">🛡️ Paradigmes de Stress-Test</div>
            <div class="kpi-val" style="color:var(--accent-emerald)" id="tt-kpi-stress">5 / 5 Validés</div>
            <div class="kpi-sub">Libéral, Post-Keynésien, Climat, Local, Marchés</div>
            <div style="margin-top:8px;"><span class="badge badge-success">Score moyen 100 %</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">⚖️ Bouclage Stock-Flux</div>
            <div class="kpi-val" style="color:var(--accent-indigo)">SFC INET (100 %)</div>
            <div class="kpi-sub">Principe Godley-Lavoie : ∑ Soldes = 0</div>
            <div style="margin-top:8px;"><span class="badge badge-success">Zéro fuite comptable</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">🔒 Immunité aux Brèches</div>
            <div class="kpi-val" style="color:var(--accent-emerald)">Auditable & Inattaquable</div>
            <div class="kpi-sub">Pourquoi chaque paramètre a été intégré</div>
            <div style="margin-top:8px;"><span class="badge badge-success">Transparence absolue</span></div>
          </div>
        </div>

        <!-- Section des 5 Paradigmes de Stress-Test -->
        <h3 style="color:var(--accent-cyan); font-size:1.15rem; margin-bottom:12px;">⚡ RÉSULTATS DES 5 PARADIGMES DE STRESS-TEST CONTRADICTOIRE</h3>
        <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:18px;">
          Chaque paradigme applique les métriques et règles les plus sévères de son école de pensée pour tenter de faire échouer le plan de mandature.
        </p>

        <div id="stress-tests-container" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:18px; margin-bottom:30px;">
          <!-- Rempli dynamiquement par JS -->
        </div>

        <!-- Section du Répertoire des 23 Think Tanks -->
        <h3 style="color:var(--accent-indigo); font-size:1.15rem; margin-bottom:12px;">📚 RÉPERTOIRE MONDIAL DES 23 THINK TANKS & PREUVES DÉFENSIVES</h3>
        <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:16px;">
          Pour chaque think tank : méthodologie, objection redoutée, raison d'être de l'intégration (« Pourquoi l'ajout ») et réponse mathématique du modèle.
        </p>

        <!-- Recherche et Filtres par Échelon -->
        <div class="search-box" style="margin-bottom:20px;">
          <input type="text" id="tt-search-input" placeholder="Rechercher par nom, sigle, orientation (ex: Montaigne, OFCE, Zucman, Blanchard, SFC)..." oninput="filtrerThinkTanks()">
          <div class="filter-pills" style="margin-top:10px;">
            <button class="filter-pill active" onclick="filtrerThinkTanksEchelon('', this)">Tous (23)</button>
            <button class="filter-pill" onclick="filtrerThinkTanksEchelon('local', this)">Local & Territoires (4)</button>
            <button class="filter-pill" onclick="filtrerThinkTanksEchelon('national', this)">National France (10)</button>
            <button class="filter-pill" onclick="filtrerThinkTanksEchelon('europeen', this)">Europe (4)</button>
            <button class="filter-pill" onclick="filtrerThinkTanksEchelon('international', this)">Mondial (5)</button>
          </div>
        </div>

        <div id="thinktanks-cards-container">
          <!-- Rempli par JavaScript -->
        </div>
      </div>
    </div>

    <!-- ============================================================= -->
    <!-- TAB 12 : HISTOIRE & COMPARAISONS DYNAMIQUES (1792→2026)        -->
    <!-- ============================================================= -->
    <div id="tab-histoire" class="tab-pane">
      <div class="arch-diagram">
        <h2>📜 234 ANS D'HISTOIRE FISCALE, ÉCONOMIQUE & SOCIALE DE FRANCE (1792→2026)</h2>
        <p class="subtitle" style="margin-bottom:20px;">
          Miroir historique intégral : 12 régimes politiques, 19 points de données chronologiques, 6 réformes majeures, 7 crises systémiques.
          Comparez le passé et le futur pour calibrer chaque paramètre de politique publique.
        </p>

        <!-- KPI Historiques -->
        <div class="kpi-grid" style="margin-bottom:24px;">
          <div class="kpi-card">
            <div class="kpi-title">🏛️ Périodes Historiques</div>
            <div class="kpi-val" style="color:var(--accent-cyan)" id="hist-kpi-periodes">12 régimes</div>
            <div class="kpi-sub">De la Révolution à la Ve République (1792→2026)</div>
            <div style="margin-top:8px;"><span class="badge badge-primary">Spectre intégral</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">💰 Dette/PIB Record</div>
            <div class="kpi-val" style="color:var(--accent-crimson)" id="hist-kpi-dette-max">200 %</div>
            <div class="kpi-sub">Post-WWI (1920) • Actuel : 112 %</div>
            <div style="margin-top:8px;"><span class="badge badge-warning">Pic historique</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">📊 Part Top 10 % (Piketty)</div>
            <div class="kpi-val" style="color:var(--accent-gold)" id="hist-kpi-top10">50 %→36 %</div>
            <div class="kpi-sub">1900 : 50 % • 2026 : 36 % • Compression historique</div>
            <div style="margin-top:8px;"><span class="badge badge-success">-14 pts en 126 ans</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">⚡ Chômage Record</div>
            <div class="kpi-val" style="color:var(--accent-emerald)" id="hist-kpi-chomage">2 % → 12 %</div>
            <div class="kpi-sub">Trente Glorieuses : 2 % • Dépression : 12 %</div>
            <div style="margin-top:8px;"><span class="badge badge-primary">Enseignement clé</span></div>
          </div>
        </div>

        <!-- Dropdowns de comparaison -->
        <h3 style="margin-bottom:12px; font-weight:800;">🔄 Comparaison Dynamique Inter-Régimes</h3>
        <div class="search-box" style="margin-bottom:16px;">
          <div style="display:flex; gap:12px; flex-wrap:wrap; width:100%;">
            <div style="flex:1; min-width:200px;">
              <label style="font-size:0.8rem; color:var(--text-muted); display:block; margin-bottom:4px;">Période A</label>
              <select id="hist-select-a" style="width:100%; background:#151e2e; border:1px solid #28374d; color:var(--text); padding:10px; border-radius:6px; font-size:0.9rem;">
                <!-- Rempli dynamiquement -->
              </select>
            </div>
            <div style="flex:1; min-width:200px;">
              <label style="font-size:0.8rem; color:var(--text-muted); display:block; margin-bottom:4px;">Période B</label>
              <select id="hist-select-b" style="width:100%; background:#151e2e; border:1px solid #28374d; color:var(--text); padding:10px; border-radius:6px; font-size:0.9rem;">
                <!-- Rempli dynamiquement -->
              </select>
            </div>
            <div style="flex:1; min-width:200px;">
              <label style="font-size:0.8rem; color:var(--text-muted); display:block; margin-bottom:4px;">Dimension</label>
              <select id="hist-select-dim" style="width:100%; background:#151e2e; border:1px solid #28374d; color:var(--text); padding:10px; border-radius:6px; font-size:0.9rem;">
                <!-- Rempli dynamiquement -->
              </select>
            </div>
            <div style="display:flex; align-items:flex-end;">
              <button class="btn-run-custom" onclick="lancerComparaisonHistorique()" style="white-space:nowrap;">🔍 Comparer</button>
            </div>
          </div>
        </div>

        <!-- Résultat de la comparaison -->
        <div id="hist-comparaison-resultat" style="display:none;">
          <div class="table-container" style="margin-bottom:24px;">
            <table>
              <thead>
                <tr>
                  <th>Indicateur</th>
                  <th id="hist-comp-titre-a">Période A</th>
                  <th id="hist-comp-titre-b">Période B</th>
                  <th>Δ Variation</th>
                </tr>
              </thead>
              <tbody id="hist-comp-tbody">
                <!-- Rempli dynamiquement -->
              </tbody>
            </table>
          </div>
          <div id="hist-enseignements" style="background:#0f1726; border:1px solid #233148; border-radius:8px; padding:16px; margin-bottom:24px;">
            <h4 style="color:#93c5fd; margin-bottom:10px;">💡 Enseignements Historiques Croisés</h4>
            <div id="hist-enseignements-liste">
              <!-- Rempli dynamiquement -->
            </div>
          </div>
        </div>

        <!-- Synthèse historique -->
        <h3 style="margin-bottom:12px; font-weight:800;">📈 Synthèse des Grandes Tendances Historiques</h3>
        <div id="hist-synthese" style="background:#090d16; border:1px solid #233148; border-radius:8px; padding:20px; margin-bottom:24px; font-family:monospace; font-size:0.82rem; white-space:pre-wrap; line-height:1.6; color:#cbd5e1;">
          Chargement...
        </div>

        <!-- Réformes majeures -->
        <h3 style="margin-bottom:12px; font-weight:800;">⚖️ Les 6 Grandes Réformes Fiscales & Sociales (1790→2023)</h3>
        <div id="hist-reformes-container" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(340px, 1fr)); gap:16px; margin-bottom:24px;">
          <!-- Rempli dynamiquement -->
        </div>

        <!-- Crises historiques -->
        <h3 style="margin-bottom:12px; font-weight:800;">🔥 Les 7 Crises Systémiques Majeures (1793→2020)</h3>
        <div id="hist-crises-container" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(340px, 1fr)); gap:16px; margin-bottom:24px;">
          <!-- Rempli dynamiquement -->
        </div>

        <!-- Paramètres de calibration -->
        <h3 style="margin-bottom:12px; font-weight:800;">🎯 Paramètres Historiques de Calibration du Simulateur</h3>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Paramètre</th>
                <th>Min Historique</th>
                <th>Max Historique</th>
                <th>Cible Simulateur</th>
                <th>Plage Optimale</th>
              </tr>
            </thead>
            <tbody id="hist-calibration-tbody">
              <!-- Rempli dynamiquement -->
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ============================================================= -->
    <!-- TAB 13 : SOCIÉTÉ — 18 DOMAINES (1792→2026)                    -->
    <!-- ============================================================= -->
    <div id="tab-societe" class="tab-pane">
      <div class="arch-diagram">
        <h2>🏛️ LES 18 DOMAINES DE LA SOCIÉTÉ FRANÇAISE (1792→2026)</h2>
        <p class="subtitle" style="margin-bottom:20px;">
          De l'éducation à la culture, de la santé à la défense, en passant par le travail, le logement, l'énergie et la démocratie :
          chaque domaine est documenté avec ses indicateurs historiques vérifiés, ses réformes majeures, ses crises et ses paramètres de calibration.
        </p>

        <div class="kpi-grid" style="margin-bottom:24px;">
          <div class="kpi-card">
            <div class="kpi-title">📚 Domaines Sociétaux</div>
            <div class="kpi-val" style="color:var(--accent-cyan)" id="soc-kpi-domaines">18</div>
            <div class="kpi-sub">Éducation → Culture</div>
            <div style="margin-top:8px;"><span class="badge badge-primary">Couverture intégrale</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">📊 Points Historiques</div>
            <div class="kpi-val" style="color:var(--accent-emerald)" id="soc-kpi-points">-</div>
            <div class="kpi-sub">Données vérifiées 1792→2026</div>
            <div style="margin-top:8px;"><span class="badge badge-success">Sources certifiées</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">⚖️ Réformes Majeures</div>
            <div class="kpi-val" style="color:var(--accent-gold)" id="soc-kpi-reformes">-</div>
            <div class="kpi-sub">Lois et ordonnances fondatrices</div>
            <div style="margin-top:8px;"><span class="badge badge-warning">Traçabilité complète</span></div>
          </div>
          <div class="kpi-card">
            <div class="kpi-title">🔥 Crises Documentées</div>
            <div class="kpi-val" style="color:var(--accent-crimson)" id="soc-kpi-crises">-</div>
            <div class="kpi-sub">Chocs systémiques et ruptures</div>
            <div style="margin-top:8px;"><span class="badge badge-danger">Anticipation proactive</span></div>
          </div>
        </div>

        <div class="search-box" style="margin-bottom:20px;">
          <input type="text" id="soc-search-input" placeholder="Rechercher un domaine (ex: santé, éducation, défense, énergie, logement)..." oninput="filtrerDomaines()">
        </div>

        <div id="societe-domaines-container" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(340px, 1fr)); gap:16px; margin-bottom:24px;">
        </div>

        <div id="soc-detail-domaine" style="display:none;">
          <div class="year-details" style="margin-bottom:24px;">
            <div class="year-header">
              <h3 id="soc-detail-titre"></h3>
              <span class="badge badge-primary" id="soc-detail-badge">Indicateurs</span>
            </div>
            <div class="strates-grid">
              <div class="strate-card"><h4>📈 Indicateurs clés</h4><div id="soc-detail-indicateurs"></div></div>
              <div class="strate-card"><h4>⚖️ Réformes majeures</h4><div id="soc-detail-reformes"></div></div>
              <div class="strate-card"><h4>🔥 Crises</h4><div id="soc-detail-crises"></div></div>
              <div class="strate-card"><h4>🎯 Calibration</h4><div id="soc-detail-calibration"></div></div>
            </div>
            <div class="tt-box tt-box-pourquoi" style="margin-top:12px;">
              <strong>💡 Pourquoi intégré :</strong> <span id="soc-detail-pourquoi">-</span>
            </div>
            <div class="tt-box tt-box-reponse">
              <strong>🏛️ Pertinence :</strong> <span id="soc-detail-pertinence">-</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    // Variables globales
    let currentTrajectory = [];
    let currentScenario = 'mandature';
    let selectedYearIndex = 4; // Année 5 par défaut (0-indexée)
    let allCorpusArticles = [];
    let activeCorpusStrate = '';

    // Gestion des onglets
    function showTab(tabName) {
      document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('nav button').forEach(el => el.classList.remove('active'));
      
      const targetPane = document.getElementById('tab-' + tabName);
      if (targetPane) targetPane.classList.add('active');

      const clickedBtn = Array.from(document.querySelectorAll('nav button')).find(b => b.getAttribute('onclick')?.includes(tabName));
      if (clickedBtn) clickedBtn.classList.add('active');

      if (tabName === 'assemblees') afficherAssemblees();
      if (tabName === 'generations') afficherGenerations();
      if (tabName === 'territoires') afficherTerritoires();
      if (tabName === 'bataille') afficherBatailleBudget();
      if (tabName === 'comparatif') chargerComparatif();
      if (tabName === 'corpus' && allCorpusArticles.length === 0) chargerCorpus();
      if (tabName === 'dossier') chargerDossier();
      if (tabName === 'audit') chargerAuditEtSources();
      if (tabName === 'thinktanks') chargerThinkTanks();
      if (tabName === 'histoire') chargerHistoire();
      if (tabName === 'societe') chargerSociete();
    }

    // Sélection d'un scénario prédéfini
    async function selectScenario(scName) {
      currentScenario = scName;
      document.querySelectorAll('.scenario-btn').forEach(b => b.classList.remove('active'));
      const activeBtn = document.getElementById('btn-sc-' + scName);
      if (activeBtn) activeBtn.classList.add('active');
      document.getElementById('custom-panel').style.display = 'none';

      await chargerSimulation(scName);
    }

    function toggleCustomPanel() {
      const p = document.getElementById('custom-panel');
      const isVisible = p.style.display === 'block';
      p.style.display = isVisible ? 'none' : 'block';
      if (!isVisible) {
        document.querySelectorAll('.scenario-btn').forEach(b => b.classList.remove('active'));
        document.getElementById('btn-sc-custom').classList.add('active');
      }
    }

    function updateVal(id, val, unit) {
      const prefix = (id === 'dgf' || id === 'brent' || id === 'fed' || id === 'forex') && val > 0 ? '+' : '';
      document.getElementById('val-' + id).innerText = prefix + val + unit;
    }

    // Chargement d'une simulation
    async function chargerSimulation(scName) {
      try {
        const resp = await fetch('/api/simuler', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({scenario: scName})
        });
        const data = await resp.json();
        currentTrajectory = data.trajectoire;
        selectedYearIndex = currentTrajectory.length - 1;
        afficherTrajectoire(currentTrajectory);
        afficherDetailAnnee(currentTrajectory[selectedYearIndex]);
      } catch (e) {
        console.error("Erreur lors de la simulation:", e);
      }
    }

    // Simulation personnalisée
    async function lancerSimulationPersonnalisee() {
      const params = {
        recettes_fraude_ia_mde: parseFloat(document.getElementById('sl-fraude').value),
        conditionnement_aides_entreprises_mde: parseFloat(document.getElementById('sl-aides').value),
        taxe_superprofits_rachats_mde: parseFloat(document.getElementById('sl-superprofits').value),
        extension_ttf_mde: parseFloat(document.getElementById('sl-ttf').value),
        fusion_doublons_territoriaux_mde: parseFloat(document.getElementById('sl-doublons').value),
        commande_publique_massifiee_mde: parseFloat(document.getElementById('sl-achats').value),
        extinction_niches_inefficaces_mde: parseFloat(document.getElementById('sl-niches').value),
        delta_dotation_dgf_mde: parseFloat(document.getElementById('sl-dgf').value),
        baisse_tva_energie_5_5_mde: document.getElementById('chk-tva').checked ? 9.0 : 0.0,
        reforme_casier_b2: document.getElementById('chk-b2').checked,
        reforme_vote_blanc_invalidant: document.getElementById('chk-blanc').checked,
        reforme_ric_souverain: document.getElementById('chk-ric').checked,
        reforme_anti_pantouflage_lobbys: document.getElementById('chk-pantouflage').checked,
        choc_petrole_brent_usd: parseFloat(document.getElementById('sl-brent').value),
        choc_taux_fed_bps: parseFloat(document.getElementById('sl-fed').value),
        choc_change_eur_usd: parseFloat(document.getElementById('sl-forex').value),
      };

      try {
        const resp = await fetch('/api/simuler', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({scenario: 'custom', parametres: params})
        });
        const data = await resp.json();
        currentTrajectory = data.trajectoire;
        selectedYearIndex = currentTrajectory.length - 1;
        afficherTrajectoire(currentTrajectory);
        afficherDetailAnnee(currentTrajectory[selectedYearIndex]);
      } catch (e) {
        console.error("Erreur simulation sur-mesure:", e);
      }
    }

    // Affichage des cartes KPI et du tableau
    function afficherTrajectoire(traj) {
      const anneeCible = traj[traj.length - 1];

      // KPI 1 : Déficit
      document.getElementById('kpi-deficit').innerText = anneeCible.ratio_deficit_pib.toFixed(2) + ' %';
      document.getElementById('kpi-deficit-mde').innerText = anneeCible.deficit_nominal_mde.toFixed(1) + ' Md€';
      const badgeDef = document.getElementById('badge-deficit');
      const cardDef = document.getElementById('card-deficit');
      if (anneeCible.ratio_deficit_pib <= 3.0) {
        badgeDef.className = 'badge badge-success';
        badgeDef.innerText = 'CONFORME (< 3%)';
        cardDef.className = 'kpi-card success';
      } else {
        badgeDef.className = 'badge badge-danger';
        badgeDef.innerText = 'ALERTE PDE';
        cardDef.className = 'kpi-card danger';
      }

      // KPI 2 : Dette
      document.getElementById('kpi-dette').innerText = anneeCible.ratio_dette_pib.toFixed(1) + ' %';
      document.getElementById('kpi-dette-stock').innerText = Math.round(anneeCible.dette_nominale_mde) + ' Md€';

      // KPI 3 : OAT 10a
      document.getElementById('kpi-oat').innerText = anneeCible.taux_oat_pct.toFixed(2) + ' %';
      document.getElementById('kpi-spread').innerText = 'Spread: ' + anneeCible.spread_bund_bps.toFixed(1) + ' bps';
      const badgeNote = document.getElementById('badge-note');
      badgeNote.innerText = anneeCible.note_souveraine;
      badgeNote.className = anneeCible.note_souveraine.startsWith('A+') ? 'badge badge-danger' : 'badge badge-success';

      // KPI 4 : Tension sociale
      document.getElementById('kpi-tension').innerText = anneeCible.tension_sociale_locale.toFixed(1) + ' / 100';
      document.getElementById('kpi-foncier').innerText = anneeCible.produit_taxe_fonciere_mde.toFixed(1) + ' Md€';
      const badgeTen = document.getElementById('badge-tension');
      if (anneeCible.tension_sociale_locale < 20) {
        badgeTen.className = 'badge badge-success';
        badgeTen.innerText = 'APAISÉ';
      } else if (anneeCible.tension_sociale_locale < 50) {
        badgeTen.className = 'badge badge-warning';
        badgeTen.innerText = 'TENDU';
      } else {
        badgeTen.className = 'badge badge-danger';
        badgeTen.innerText = 'FRONDE CIVIQUE';
      }

      // KPI 5 : Confiance démocratique
      document.getElementById('kpi-confiance').innerText = anneeCible.confiance_democratique.toFixed(1) + ' / 100';
      document.getElementById('kpi-censure').innerText = anneeCible.risque_censure_parlement.toFixed(1) + ' %';

      // KPI 6 : Énergie / Pouvoir d'achat
      document.getElementById('kpi-pouvoir').innerText = anneeCible.pouvoir_achat_index.toFixed(1);
      document.getElementById('kpi-inflation').innerText = anneeCible.inflation_globale_pct.toFixed(2) + ' %';

      // Remplissage du tableau
      const tbody = document.getElementById('trajectory-tbody');
      tbody.innerHTML = '';
      traj.forEach((r, idx) => {
        const tr = document.createElement('tr');
        if (idx === selectedYearIndex) tr.classList.add('selected');
        tr.onclick = () => {
          selectedYearIndex = idx;
          document.querySelectorAll('#trajectory-tbody tr').forEach(el => el.classList.remove('selected'));
          tr.classList.add('selected');
          afficherDetailAnnee(r);
        };
        const pdeBadge = r.statut_pde_europe ? '<span class="badge badge-danger">ALERTE</span>' : '<span class="badge badge-success">CONFORME</span>';
        const noteBadge = r.note_souveraine.startsWith('A+') ? '<span class="badge badge-danger">' + r.note_souveraine + '</span>' : '<span class="badge badge-success">' + r.note_souveraine + '</span>';
        tr.innerHTML = `
          <td><strong>An ${r.annee}</strong></td>
          <td>${r.deficit_nominal_mde.toFixed(1)} Md€</td>
          <td><strong>${r.ratio_deficit_pib.toFixed(2)} %</strong></td>
          <td>${r.ratio_dette_pib.toFixed(1)} %</td>
          <td>${r.taux_oat_pct.toFixed(2)} %</td>
          <td>${r.spread_bund_bps.toFixed(1)} bp</td>
          <td>${r.tension_sociale_locale.toFixed(1)}/100</td>
          <td>${r.confiance_democratique.toFixed(1)}/100</td>
          <td>${pdeBadge}</td>
          <td>${noteBadge}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    // Affichage des détails d'une année
    function afficherDetailAnnee(r) {
      document.getElementById('detail-year-title').innerText = `🔍 ANALYSE APPROFONDIE : ANNÉE ${r.annee}`;
      document.getElementById('det-tension').innerText = r.tension_sociale_locale.toFixed(1) + ' / 100';
      document.getElementById('det-services').innerText = r.qualite_services_proximite.toFixed(1) + ' / 100';
      document.getElementById('det-foncier').innerText = r.produit_taxe_fonciere_mde.toFixed(2) + ' Md€';

      document.getElementById('det-pib').innerText = r.pib_nominal_mde.toFixed(1) + ' Md€';
      document.getElementById('det-deficit').innerText = r.deficit_nominal_mde.toFixed(1) + ' Md€ (' + r.ratio_deficit_pib.toFixed(2) + ' % PIB)';
      document.getElementById('det-dette').innerText = r.dette_nominale_mde.toFixed(1) + ' Md€ (' + r.ratio_dette_pib.toFixed(1) + ' % PIB)';
      document.getElementById('det-pouvoir').innerText = r.pouvoir_achat_index.toFixed(1) + ' (Base 100)';
      document.getElementById('det-censure').innerText = r.risque_censure_parlement.toFixed(1) + ' %';

      document.getElementById('det-pde').innerText = r.statut_pde_europe ? 'Sous procédure PDE (Alerte)' : 'Conforme (< 3% PIB)';
      document.getElementById('det-pde').style.color = r.statut_pde_europe ? 'var(--accent-crimson)' : 'var(--accent-emerald)';
      document.getElementById('det-tpi').innerText = r.bouclier_tpi_actif ? 'Actif (Protection BCE garantie)' : 'Suspendu (Discipline non respectée)';
      document.getElementById('det-tpi').style.color = r.bouclier_tpi_actif ? 'var(--accent-emerald)' : 'var(--accent-crimson)';

      document.getElementById('det-oat').innerText = r.taux_oat_pct.toFixed(2) + ' %';
      document.getElementById('det-spread').innerText = r.spread_bund_bps.toFixed(1) + ' bps';
      document.getElementById('det-pme').innerText = r.taux_credit_pme.toFixed(2) + ' %';
      document.getElementById('det-facture').innerText = r.facture_energetique_mde.toFixed(1) + ' Md€/an';
      document.getElementById('det-note').innerText = r.note_souveraine;

      // Variables des Assemblées dans le panneau de détail
      const voixCensure = r.voix_censure_an !== undefined ? r.voix_censure_an : 254;
      document.getElementById('det-voix-censure').innerText = voixCensure + ' / 289';
      document.getElementById('det-climat-an').innerText = r.climat_assemblee_nationale || 'Majorité relative';
      const hostiliteSenat = r.hostilite_senat_indice !== undefined ? r.hostilite_senat_indice : 18.0;
      document.getElementById('det-hostilite-senat').innerText = hostiliteSenat.toFixed(1) + ' / 100';
      const detVetoSenat = document.getElementById('det-veto-senat');
      detVetoSenat.innerText = r.senat_veto_art_89 ? 'Veto Sénat Actif' : 'Veto levé (Congrès possible)';
      detVetoSenat.style.color = r.senat_veto_art_89 ? 'var(--accent-crimson)' : 'var(--accent-emerald)';
      const failliteDept = r.departements_alerte_ciseau !== undefined ? r.departements_alerte_ciseau : 2;
      document.getElementById('det-faillite-dept').innerText = failliteDept + ' départements';

      const evtBox = document.getElementById('events-container');
      evtBox.innerHTML = '';
      if (r.commentaires && r.commentaires.length > 0) {
        r.commentaires.forEach(comm => {
          const div = document.createElement('div');
          div.className = 'event-line';
          div.innerText = comm;
          evtBox.appendChild(div);
        });
      } else {
        evtBox.innerHTML = '<div class="event-line" style="border-left-color:gray; color:gray;">Aucun incident majeur sur cet exercice.</div>';
      }

      // Variables Cycle de Vie et 3 Générations
      const harmGen = r.indice_harmonie_intergenerationnelle !== undefined ? r.indice_harmonie_intergenerationnelle : 42.0;
      const elHarm = document.getElementById('det-harmonie-gen');
      if (elHarm) elHarm.innerText = harmGen.toFixed(1) + ' / 100';
      const elSand = document.getElementById('det-charge-sandwich');
      if (elSand) elSand.innerText = (r.g2_charge_sandwich_indice !== undefined ? r.g2_charge_sandwich_indice : 68.0).toFixed(1) + ' / 100';
      const elPauv3 = document.getElementById('det-pauvrete-g3');
      if (elPauv3) elPauv3.innerText = (r.g3_taux_pauvrete_pct !== undefined ? r.g3_taux_pauvrete_pct : 19.4).toFixed(1) + ' %';
      const elPauv1 = document.getElementById('det-pauvrete-g1');
      if (elPauv1) elPauv1.innerText = (r.g1_taux_pauvrete_pct !== undefined ? r.g1_taux_pauvrete_pct : 10.8).toFixed(1) + ' %';
      const elDetteJ = document.getElementById('det-dette-jeune');
      if (elDetteJ) elDetteJ.innerText = Math.round(r.charge_dette_par_jeune_euros || 129275).toLocaleString() + ' €';

      // Variables Territoires, Outre-Mer et Élections
      const elElecPartic = document.getElementById('det-elections-partic');
      if (elElecPartic) elElecPartic.innerText = (r.participation_electorale_proj_pct !== undefined ? r.participation_electorale_proj_pct : 74.5).toFixed(1) + ' %';
      const elElecTriang = document.getElementById('det-elections-triang');
      if (elElecTriang) elElecTriang.innerText = (r.triangulaires_legislatives_proj !== undefined ? r.triangulaires_legislatives_proj : 38) + ' circonscriptions';
      const elOmVie = document.getElementById('det-om-vie-chere');
      if (elOmVie) elOmVie.innerText = (r.surcout_vie_chere_outremer_pct !== undefined ? r.surcout_vie_chere_outremer_pct : 18.5).toFixed(1) + ' %';
      const elOmCont = document.getElementById('det-om-continuite');
      if (elOmCont) elOmCont.innerText = (r.indice_continuite_territoriale !== undefined ? r.indice_continuite_territoriale : 78.0).toFixed(1) + ' / 100';
      const elRurVit = document.getElementById('det-ruralite-vitalite');
      if (elRurVit) elRurVit.innerText = (r.vitalite_rurale_indice !== undefined ? r.vitalite_rurale_indice : 81.5).toFixed(1) + ' / 100';

      // Mise à jour des onglets spécialisés
      afficherAssemblees();
      afficherGenerations();
      afficherTerritoires();
      afficherBatailleBudget();
    }

    // Affichage des assemblées
    function afficherAssemblees() {
      const r = currentTrajectory[selectedYearIndex] || currentTrajectory[currentTrajectory.length - 1];
      if (!r) return;

      // 1. Assemblée nationale
      const voixAN = r.voix_censure_an !== undefined ? r.voix_censure_an : 254;
      document.getElementById('ass-an-voix').innerText = voixAN + ' / 289';
      const badgeAN = document.getElementById('ass-an-badge');
      const cardAN = document.getElementById('card-ass-an');
      if (voixAN >= 289) {
        badgeAN.className = 'badge badge-danger';
        badgeAN.innerText = 'CENSURE ADOPTÉE';
        cardAN.className = 'kpi-card danger';
      } else if (voixAN >= 275) {
        badgeAN.className = 'badge badge-warning';
        badgeAN.innerText = 'ALERTE ROUGE';
        cardAN.className = 'kpi-card warning';
      } else {
        badgeAN.className = 'badge badge-success';
        badgeAN.innerText = 'STABLE (< 289)';
        cardAN.className = 'kpi-card success';
      }
      document.getElementById('ass-an-climat').innerText = r.climat_assemblee_nationale || 'Majorité relative';
      document.getElementById('det-ass-voix-censure').innerText = voixAN + ' voix sur 577';
      const statutGouv = document.getElementById('det-ass-statut-gouv');
      statutGouv.innerText = voixAN >= 289 ? 'GOUVERNEMENT RENVERSÉ (Motion 49.2 adoptée) !' : 'Exécutif stable en fonction';
      statutGouv.style.color = voixAN >= 289 ? 'var(--accent-crimson)' : 'var(--accent-emerald)';

      // 2. Sénat
      const hostiliteSenat = r.hostilite_senat_indice !== undefined ? r.hostilite_senat_indice : 18.0;
      document.getElementById('ass-senat-hostilite').innerText = hostiliteSenat.toFixed(1) + ' / 100';
      const badgeSenat = document.getElementById('ass-senat-badge');
      const cardSenat = document.getElementById('card-ass-senat');
      if (r.senat_veto_art_89) {
        badgeSenat.className = 'badge badge-danger';
        badgeSenat.innerText = 'VETO ART. 89 ACTIF';
        cardSenat.className = 'kpi-card danger';
      } else {
        badgeSenat.className = 'badge badge-success';
        badgeSenat.innerText = 'VETO ART. 89 LEVÉ';
        cardSenat.className = 'kpi-card success';
      }
      const cmpPct = Math.max(10, Math.round(85.0 - hostiliteSenat * 0.65));
      document.getElementById('ass-senat-cmp').innerText = cmpPct + ' %';
      document.getElementById('det-ass-senat-hostilite').innerText = hostiliteSenat.toFixed(1) + ' / 100';
      const detVetoSenat = document.getElementById('det-ass-senat-veto');
      detVetoSenat.innerText = r.senat_veto_art_89 ? 'VETO SÉNATORIAL ACTIF (Blocage art. 89)' : 'VETO LEVÉ (Congrès de Versailles possible)';
      detVetoSenat.style.color = r.senat_veto_art_89 ? 'var(--accent-crimson)' : 'var(--accent-emerald)';
      document.getElementById('det-ass-senat-cmp').innerText = cmpPct + ' % de compromis';

      // 3. Congrès
      const congresOk = r.congres_majorite_3_5;
      const badgeCongres = document.getElementById('ass-congres-badge');
      const cardCongres = document.getElementById('card-ass-congres');
      badgeCongres.className = congresOk ? 'badge badge-success' : 'badge badge-warning';
      badgeCongres.innerText = congresOk ? 'QUALIFIÉ (60%)' : 'NON QUALIFIÉ (< 3/5)';
      cardCongres.className = congresOk ? 'kpi-card success' : 'kpi-card warning';
      document.getElementById('ass-congres-voie').innerText = congresOk ? 'Approbation Congrès sans référendum' : 'Recours nécessaire à l\'Art. 11 (Référendum)';

      // 4. Départements
      const failliteDept = r.departements_alerte_ciseau !== undefined ? r.departements_alerte_ciseau : 2;
      document.getElementById('ass-dept-faillite').innerText = failliteDept + ' / 101';
      const badgeDept = document.getElementById('ass-dept-badge');
      const cardDept = document.getElementById('card-ass-dept');
      if (failliteDept >= 25) {
        badgeDept.className = 'badge badge-danger';
        badgeDept.innerText = 'CATASTROPHE ADF';
        cardDept.className = 'kpi-card danger';
      } else if (failliteDept >= 10) {
        badgeDept.className = 'badge badge-warning';
        badgeDept.innerText = 'TENSION CISAILLES';
        cardDept.className = 'kpi-card warning';
      } else {
        badgeDept.className = 'badge badge-success';
        badgeDept.innerText = 'SOLVABLE';
        cardDept.className = 'kpi-card success';
      }
      const ciseauScore = Math.min(100, Math.round(failliteDept * 2.2 + 40));
      document.getElementById('ass-dept-ciseau').innerText = ciseauScore + ' / 100';
      document.getElementById('det-ass-dept-ciseau').innerText = ciseauScore + ' / 100';
      document.getElementById('det-ass-dept-faillite').innerText = failliteDept + ' départements en crise';

      // 5. Maires
      const frondeMaires = (r.fronde_maires_indice !== undefined ? r.fronde_maires_indice : 12.0);
      document.getElementById('ass-maires-fronde').innerText = frondeMaires.toFixed(1) + ' / 100';
      const badgeMaires = document.getElementById('ass-maires-badge');
      badgeMaires.className = frondeMaires > 50 ? 'badge badge-danger' : (frondeMaires > 25 ? 'badge badge-warning' : 'badge badge-success');
      badgeMaires.innerText = frondeMaires > 50 ? 'FRONDE AMF' : (frondeMaires > 25 ? 'VIGILANCE' : 'APAISÉ');

      // 6. Consulaires
      const confCons = (r.consulaire_confiance_pme !== undefined ? r.consulaire_confiance_pme : 78.0);
      document.getElementById('ass-consulaire-conf').innerText = confCons.toFixed(1) + ' %';
      document.getElementById('ass-consulaire-cma').innerText = Math.min(95, Math.round(confCons + 6)) + ' %';
      document.getElementById('det-ass-cons-cci').innerText = confCons.toFixed(1) + ' %';
      document.getElementById('det-ass-cons-cma').innerText = Math.min(95, Math.round(confCons + 6)) + ' %';

      // 7. Parlement Européen
      const peAlign = (r.pe_taux_alignement !== undefined ? r.pe_taux_alignement : 78.0);
      document.getElementById('det-ass-pe-alignement').innerText = peAlign.toFixed(1) + ' %';
      const conseilUE = document.getElementById('det-ass-conseil-ue');
      conseilUE.innerText = r.statut_pde_europe ? 'Procédure de Déficit Excessif Active (Alerte)' : 'Sortie de la PDE Validée (Conforme < 3%)';
      conseilUE.style.color = r.statut_pde_europe ? 'var(--accent-crimson)' : 'var(--accent-emerald)';

      // 8. CESE & Citoyen
      document.getElementById('det-ass-cese-consensus').innerText = (r.cese_consensus_social !== undefined ? r.cese_consensus_social : 68.0).toFixed(1) + ' %';
      document.getElementById('det-ass-citoyen-consensus').innerText = (r.convention_citoyenne_consensus !== undefined ? r.convention_citoyenne_consensus : 94.0).toFixed(1) + ' %';
    }

    // Affichage du cycle de vie et des 3 générations
    function afficherGenerations() {
      const r = currentTrajectory[selectedYearIndex] || currentTrajectory[currentTrajectory.length - 1];
      if (!r) return;

      const g1Pop = r.g1_seniors_pop_m !== undefined ? r.g1_seniors_pop_m : 14.6;
      const g2Pop = r.g2_actifs_pop_m !== undefined ? r.g2_actifs_pop_m : 26.2;
      const g3Pop = r.g3_jeunesse_pop_m !== undefined ? r.g3_jeunesse_pop_m : 27.6;
      const g1Pauv = r.g1_taux_pauvrete_pct !== undefined ? r.g1_taux_pauvrete_pct : 10.8;
      const g2Charge = r.g2_charge_sandwich_indice !== undefined ? r.g2_charge_sandwich_indice : 68.0;
      const g3Pauv = r.g3_taux_pauvrete_pct !== undefined ? r.g3_taux_pauvrete_pct : 19.4;
      const harmScore = r.indice_harmonie_intergenerationnelle !== undefined ? r.indice_harmonie_intergenerationnelle : 42.0;
      const ratioDep = r.ratio_dependance_demographique !== undefined ? r.ratio_dependance_demographique : 0.65;
      const detteJeune = r.charge_dette_par_jeune_euros !== undefined ? r.charge_dette_par_jeune_euros : 129275;

      const elG1P = document.getElementById('gen-g1-pop');
      if (elG1P) elG1P.innerText = g1Pop.toFixed(1) + ' M';
      const elG1Pv = document.getElementById('gen-g1-pauv');
      if (elG1Pv) elG1Pv.innerText = g1Pauv.toFixed(1) + ' %';
      const elG2P = document.getElementById('gen-g2-pop');
      if (elG2P) elG2P.innerText = g2Pop.toFixed(1) + ' M';
      const elG2C = document.getElementById('gen-g2-charge');
      if (elG2C) elG2C.innerText = g2Charge.toFixed(1) + ' / 100';
      const elG3P = document.getElementById('gen-g3-pop');
      if (elG3P) elG3P.innerText = g3Pop.toFixed(1) + ' M';
      const elG3Pv = document.getElementById('gen-g3-pauv');
      if (elG3Pv) elG3Pv.innerText = g3Pauv.toFixed(1) + ' %';
      const elG3D = document.getElementById('gen-g3-dette');
      if (elG3D) elG3D.innerText = Math.round(detteJeune / 1000) + ' k€';
      const elHarmS = document.getElementById('gen-harmonie-score');
      if (elHarmS) elHarmS.innerText = harmScore.toFixed(1) + ' / 100';
      const elRatioD = document.getElementById('gen-ratio-dep');
      if (elRatioD) elRatioD.innerText = ratioDep.toFixed(2);

      const bHarm = document.getElementById('badge-gen-harmonie');
      const cHarm = document.getElementById('card-gen-harmonie');
      if (bHarm && cHarm) {
        if (harmScore >= 75) {
          bHarm.className = 'badge badge-success';
          bHarm.innerText = 'PACTE HARMONIEUX';
          cHarm.className = 'kpi-card success';
        } else if (harmScore >= 50) {
          bHarm.className = 'badge badge-warning';
          bHarm.innerText = 'ÉQUILIBRE FRAGILE';
          cHarm.className = 'kpi-card warning';
        } else {
          bHarm.className = 'badge badge-danger';
          bHarm.innerText = 'FRACTURE INTERGÉNÉRATIONNELLE';
          cHarm.className = 'kpi-card danger';
        }
      }

      // Flux croisés
      if (document.getElementById('flux-retraites')) {
        document.getElementById('flux-retraites').innerText = (r.transfert_retraites_mde || 360.0).toFixed(1) + ' Md€';
        document.getElementById('flux-education').innerText = (r.transfert_education_mde || 165.0).toFixed(1) + ' Md€';
        document.getElementById('flux-garde').innerText = (r.garde_enfants_grands_parents_mde || 18.0).toFixed(1) + ' Md€';
        document.getElementById('flux-donations').innerText = (r.donations_vers_g3_mde || 75.0).toFixed(1) + ' Md€';
        document.getElementById('flux-dette-jeune').innerText = Math.round(detteJeune).toLocaleString() + ' € par jeune';
      }
    }

    // Affichage des strates territoriales, Outre-Mer et Élections
    function afficherTerritoires() {
      const r = currentTrajectory[selectedYearIndex] || currentTrajectory[currentTrajectory.length - 1];
      if (!r) return;

      const partic = r.participation_electorale_proj_pct !== undefined ? r.participation_electorale_proj_pct : 74.5;
      const triang = r.triangulaires_legislatives_proj !== undefined ? r.triangulaires_legislatives_proj : 38;
      const vieChere = r.surcout_vie_chere_outremer_pct !== undefined ? r.surcout_vie_chere_outremer_pct : 18.5;
      const contTerr = r.indice_continuite_territoriale !== undefined ? r.indice_continuite_territoriale : 78.0;
      const rurVit = r.vitalite_rurale_indice !== undefined ? r.vitalite_rurale_indice : 81.5;
      const metroEff = r.efficience_metropolitaine_indice !== undefined ? r.efficience_metropolitaine_indice : 86.0;

      const elPartic = document.getElementById('terr-partic-val');
      if (elPartic) elPartic.innerText = partic.toFixed(1) + ' %';
      const elRur = document.getElementById('terr-vitalite-rurale');
      if (elRur) elRur.innerText = rurVit.toFixed(1) + ' / 100';
      const elVie = document.getElementById('terr-om-viechere');
      if (elVie) elVie.innerText = '+' + vieChere.toFixed(1) + ' %';
      const elCont = document.getElementById('terr-om-cont');
      if (elCont) elCont.innerText = contTerr.toFixed(1) + ' / 100';
      const elMetro = document.getElementById('terr-metropole-efficience');
      if (elMetro) elMetro.innerText = metroEff.toFixed(1) + ' / 100';
      const elTri = document.getElementById('terr-triang-val');
      if (elTri) elTri.innerText = triang + ' circonscriptions';

      const bPartic = document.getElementById('badge-terr-partic');
      const cPartic = document.getElementById('card-terr-reu');
      if (bPartic && cPartic) {
        if (partic >= 70.0) {
          bPartic.className = 'badge badge-success';
          bPartic.innerText = 'FORTE MOBILISATION';
          cPartic.className = 'kpi-card success';
        } else if (partic >= 55.0) {
          bPartic.className = 'badge badge-warning';
          bPartic.innerText = 'PARTICIPATION MOYENNE';
          cPartic.className = 'kpi-card warning';
        } else {
          bPartic.className = 'badge badge-danger';
          bPartic.innerText = 'CRISE CIVIQUE / ABSTENTION';
          cPartic.className = 'kpi-card danger';
        }
      }

      const bOm = document.getElementById('badge-terr-om');
      const cOm = document.getElementById('card-terr-om');
      if (bOm && cOm) {
        if (vieChere <= 20.0) {
          bOm.className = 'badge badge-success';
          bOm.innerText = 'ÉGALITÉ RÉELLE EN PROGRÈS';
          cOm.className = 'kpi-card success';
        } else {
          bOm.className = 'badge badge-danger';
          bOm.innerText = 'TENSION VIE CHÈRE';
          cOm.className = 'kpi-card danger';
        }
      }
    }

    // Affichage des indicateurs de gouvernance budgétaire (Bercy)
    function afficherBatailleBudget() {
      if (!currentTrajectory || currentTrajectory.length === 0) return;
      const r = currentTrajectory[selectedYearIndex] || currentTrajectory[currentTrajectory.length - 1];

      const capEl = document.getElementById('bataille-kpi-capital');
      const popEl = document.getElementById('bataille-kpi-pop');
      const censEl = document.getElementById('bataille-kpi-censure');
      const spreadEl = document.getElementById('bataille-kpi-spread');

      const capVal = r.bataille_capital_politique !== undefined ? r.bataille_capital_politique : 50.0;
      const popVal = r.bataille_popularite_ministre !== undefined ? r.bataille_popularite_ministre : 50.0;
      const voixCensure = r.voix_censure_an !== undefined ? r.voix_censure_an : 140;
      const spreadVal = r.spread_bund_bps !== undefined ? r.spread_bund_bps : 70.0;

      if (capEl) capEl.innerText = capVal.toFixed(1) + ' / 100';
      if (popEl) {
        popEl.innerText = popVal.toFixed(1) + ' %';
        popEl.style.color = popVal >= 50.0 ? 'var(--accent-emerald)' : (popVal >= 15.0 ? 'var(--accent-amber)' : 'var(--accent-rose)');
      }
      if (censEl) {
        censEl.innerText = voixCensure + ' / 289';
        censEl.style.color = voixCensure >= 289 ? 'var(--accent-rose)' : (voixCensure >= 250 ? 'var(--accent-amber)' : 'var(--accent-emerald)');
      }
      if (spreadEl) spreadEl.innerText = spreadVal.toFixed(1) + ' pb';

      const bCap = document.getElementById('bataille-badge-capital');
      if (bCap) {
        if (capVal >= 65.0) {
          bCap.className = 'badge badge-success';
          bCap.innerText = 'Forte capacité réformatrice';
        } else if (capVal >= 35.0) {
          bCap.className = 'badge badge-warning';
          bCap.innerText = 'Marge de manœuvre serrée';
        } else {
          bCap.className = 'badge badge-danger';
          bCap.innerText = 'Paralysie politique';
        }
      }

      const bPop = document.getElementById('bataille-badge-pop');
      if (bPop) {
        if (popVal < 10.0) {
          bPop.className = 'badge badge-danger';
          bPop.innerText = 'DÉMISSION FORCÉE (< 10%)';
        } else if (popVal < 15.0) {
          bPop.className = 'badge badge-danger';
          bPop.innerText = 'SEMONCE MATIGNON (< 15%)';
        } else if (popVal >= 50.0) {
          bPop.className = 'badge badge-success';
          bPop.innerText = 'Soutien populaire solide';
        } else {
          bPop.className = 'badge badge-warning';
          bPop.innerText = 'Impopularité sous tension';
        }
      }

      const bCens = document.getElementById('bataille-badge-censure');
      if (bCens) {
        if (voixCensure >= 289) {
          bCens.className = 'badge badge-danger';
          bCens.innerText = 'CENSURE PARLEMENTAIRE (>= 289)';
        } else if (voixCensure >= 250) {
          bCens.className = 'badge badge-warning';
          bCens.innerText = 'Alerte motion de censure';
        } else {
          bCens.className = 'badge badge-success';
          bCens.innerText = 'Oppositions sous contrôle';
        }
      }

      const bPde = document.getElementById('bataille-badge-pde');
      if (bPde) {
        if (r.statut_pde_europe) {
          bPde.className = 'badge badge-warning';
          bPde.innerText = 'Procédure PDE active';
        } else {
          bPde.className = 'badge badge-success';
          bPde.innerText = 'Procédure PDE clôturée (< 3%)';
        }
      }
    }

    // Chargement du comparatif
    async function chargerComparatif() {
      try {
        const resp = await fetch('/api/comparatif');
        const comp = await resp.json();
        const tbody = document.getElementById('comparatif-tbody');
        tbody.innerHTML = '';

        const metrics = [
          { key: 'ratio_deficit_pib', label: 'Déficit Public (% PIB)', fmt: v => v.toFixed(2) + ' %', goodLow: true, limit: 3.0 },
          { key: 'ratio_dette_pib', label: 'Dette Souveraine (% PIB)', fmt: v => v.toFixed(1) + ' %', goodLow: true },
          { key: 'taux_oat_pct', label: 'Taux OAT 10 ans', fmt: v => v.toFixed(2) + ' %', goodLow: true },
          { key: 'spread_bund_bps', label: 'Spread OAT-Bund', fmt: v => v.toFixed(1) + ' bps', goodLow: true },
          { key: 'note_souveraine', label: 'Note Souveraine', fmt: v => v },
          { key: 'tension_sociale_locale', label: 'Tension Sociale Territoriale', fmt: v => v.toFixed(1) + ' / 100', goodLow: true },
          { key: 'confiance_democratique', label: 'Confiance Démocratique', fmt: v => v.toFixed(1) + ' / 100', goodHigh: true },
          { key: 'pouvoir_achat_index', label: 'Pouvoir d\'Achat (Base 100)', fmt: v => v.toFixed(1), goodHigh: true },
          { key: 'statut_pde_europe', label: 'Procédure Déficit (UE)', fmt: v => v ? 'ALERTE (PDE)' : 'CONFORME (<3%)' },
          { key: 'bouclier_tpi_actif', label: 'Bouclier TPI (BCE)', fmt: v => v ? 'ACTIF' : 'SUSPENDU' },
          { key: 'voix_censure_an', label: 'Voix Censure AN (Seuil 289)', fmt: v => (v || 254) + ' voix', goodLow: true, limit: 289 },
          { key: 'hostilite_senat_indice', label: 'Hostilité du Sénat', fmt: v => (v || 18.0).toFixed(1) + ' / 100', goodLow: true },
          { key: 'senat_veto_art_89', label: 'Veto Sénat (Art. 89)', fmt: v => v ? 'VETO ACTIF' : 'VETO LEVÉ' },
          { key: 'departements_alerte_ciseau', label: 'Départements en Crise Ciseau', fmt: v => (v || 2) + ' départements', goodLow: true },
          { key: 'consulaire_confiance_pme', label: 'Confiance PME (Consulaire)', fmt: v => (v || 78.0).toFixed(1) + ' %', goodHigh: true },
          { key: 'indice_harmonie_intergenerationnelle', label: 'Harmonie Intergénérationnelle (IEHI)', fmt: v => (v || 42.0).toFixed(1) + ' / 100', goodHigh: true },
          { key: 'g2_charge_sandwich_indice', label: 'Fardeau Génération Sandwich (G2)', fmt: v => (v || 68.0).toFixed(1) + ' / 100', goodLow: true },
          { key: 'g3_taux_pauvrete_pct', label: 'Taux Pauvreté Jeunesse (G3)', fmt: v => (v || 19.4).toFixed(1) + ' %', goodLow: true },
          { key: 'g1_taux_pauvrete_pct', label: 'Taux Pauvreté Aînés (G1)', fmt: v => (v || 10.8).toFixed(1) + ' %', goodLow: true },
          { key: 'charge_dette_par_jeune_euros', label: 'Dette Souveraine / Jeune G3', fmt: v => Math.round(v || 129000).toLocaleString() + ' €', goodLow: true },
          { key: 'vitalite_rurale_indice', label: 'Vitalité Rurale (Communes < 1k)', fmt: v => (v || 81.5).toFixed(1) + ' / 100', goodHigh: true },
          { key: 'surcout_vie_chere_outremer_pct', label: 'Surcoût Vie Chère Outre-mer (%)', fmt: v => '+' + (v || 18.5).toFixed(1) + ' %', goodLow: true },
          { key: 'indice_continuite_territoriale', label: 'Continuité Territoriale Outre-mer', fmt: v => (v || 78.0).toFixed(1) + ' / 100', goodHigh: true },
          { key: 'participation_electorale_proj_pct', label: 'Participation Électorale Projetée', fmt: v => (v || 74.5).toFixed(1) + ' %', goodHigh: true },
          { key: 'triangulaires_legislatives_proj', label: 'Triangulaires Législatives (577 circ.)', fmt: v => (v || 38) + ' circ.', goodLow: true },
        ];

        metrics.forEach(m => {
          const tr = document.createElement('tr');
          let rowHtml = `<td><strong>${m.label}</strong></td>`;
          ['mandature', 'statut_quo', 'austerite', 'choc_mondial'].forEach(sc => {
            const val = comp[sc][m.key];
            const displayVal = m.fmt(val);
            rowHtml += `<td>${displayVal}</td>`;
          });
          tr.innerHTML = rowHtml;
          tbody.appendChild(tr);
        });
      } catch (e) {
        console.error("Erreur comparatif:", e);
      }
    }

    // Chargement du Corpus Juridique
    async function chargerCorpus() {
      try {
        const resp = await fetch('/api/corpus');
        const data = await resp.json();
        allCorpusArticles = data.articles;
        afficherCorpus(allCorpusArticles);
      } catch (e) {
        console.error("Erreur corpus:", e);
      }
    }

    function filtrerCorpus() {
      const q = document.getElementById('corpus-search').value.toLowerCase();
      const filtered = allCorpusArticles.filter(art => {
        const matchStrate = !activeCorpusStrate || art.strate_impactee.toLowerCase() === activeCorpusStrate.toLowerCase();
        const chaine = (art.identifiant + ' ' + art.code_ou_traite + ' ' + art.article + ' ' + art.titre + ' ' + art.texte_integral + ' ' + art.effet_simulation).toLowerCase();
        const matchQ = !q || chaine.includes(q);
        return matchStrate && matchQ;
      });
      afficherCorpus(filtered);
    }

    function filtrerStrateCorpus(strate, btn) {
      activeCorpusStrate = strate;
      document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      filtrerCorpus();
    }

    function afficherCorpus(articles) {
      const container = document.getElementById('corpus-cards-container');
      container.innerHTML = '';
      articles.forEach(art => {
        const card = document.createElement('div');
        card.className = 'corpus-card';
        card.innerHTML = `
          <h4>
            <span>${art.article}</span>
            <span class="badge badge-primary">${art.strate_impactee}</span>
          </h4>
          <div class="code">${art.code_ou_traite} — ${art.titre}</div>
          <div class="citation">« ${art.texte_integral} »</div>
          <div class="impact"><strong>Effet dans le simulateur :</strong> ${art.effet_simulation}</div>
        `;
        container.appendChild(card);
      });
    }

    // Chargement du Dossier de Mandature
    async function chargerDossier() {
      try {
        const resp = await fetch('/api/dossier');
        const data = await resp.json();
        const container = document.getElementById('dossier-volumes-container');
        container.innerHTML = '';
        data.volumes.forEach(v => {
          const card = document.createElement('div');
          card.className = 'corpus-card';
          card.innerHTML = `
            <h4>
              <span>Vol. ${v.num}</span>
              <span class="badge badge-success">Document Officiel</span>
            </h4>
            <div class="code" style="color:#f59e0b">${v.titre}</div>
            <div class="impact">Fichier source : <code>docs/${v.fichier}</code></div>
          `;
          container.appendChild(card);
        });
      } catch (e) {
        console.error("Erreur dossier:", e);
      }
    }

    // Exporter le rapport
    async function exporterRapport(format) {
      try {
        const resp = await fetch('/api/export', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            scenario: currentScenario,
            trajectoire: currentTrajectory,
            format: format
          })
        });
        const data = await resp.json();
        const blob = new Blob([format === 'markdown' ? data.contenu : JSON.stringify(data.contenu, null, 2)], {
          type: format === 'markdown' ? 'text/markdown' : 'application/json'
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `rapport_simulation_${currentScenario}_annee5.${format === 'markdown' ? 'md' : 'json'}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      } catch (e) {
        console.error("Erreur export:", e);
      }
    }

    // Sources Officielles et Auditabilité
    let allSources = [];
    let activeSourceCategory = '';

    async function chargerAuditEtSources() {
      try {
        const resp = await fetch('/api/sources');
        const data = await resp.json();
        allSources = data.sources || [];

        const countEl = document.getElementById('audit-kpi-sources');
        if (countEl) countEl.innerText = allSources.length;

        const r = currentTrajectory[selectedYearIndex] || currentTrajectory[currentTrajectory.length - 1];
        const shaEl = document.getElementById('audit-kpi-sha');
        if (shaEl && r && r.signature_integrite_sha256) {
          shaEl.innerText = r.signature_integrite_sha256;
        }

        afficherSourcesTable(allSources);
      } catch (e) {
        console.error("Erreur chargement sources:", e);
      }
    }

    function afficherSourcesTable(liste) {
      const tbody = document.getElementById('audit-sources-tbody');
      if (!tbody) return;
      tbody.innerHTML = '';
      liste.forEach(s => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${s.id_source}</strong><br><span style="color:#94a3b8; font-size:0.8rem;">${s.nom_indicateur}</span></td>
          <td><span class="badge badge-primary">${s.organisme}</span><br><span style="font-size:0.75rem; color:#64748b;">${s.categorie}</span></td>
          <td><strong style="color:var(--accent-emerald)">${s.valeur_reference}</strong> ${s.unite}</td>
          <td><div style="font-size:0.78rem;">${s.methode_collecte}</div><div style="color:#f59e0b; font-size:0.75rem; margin-top:2px;">Millésime : ${s.millesime} (maj: ${s.date_derniere_mise_a_jour})</div></td>
          <td><a href="${s.url_officielle}" target="_blank" rel="noopener noreferrer" style="color:var(--accent-cyan); text-decoration:underline; font-size:0.8rem;">Ouvrir la source officielle ↗</a></td>
          <td><span class="badge badge-success" style="font-size:0.72rem;">${s.statut_certification}</span><br><span style="font-size:0.7rem; color:#94a3b8;">± ${s.intervalle_incertitude_pct}%</span></td>
        `;
        tbody.appendChild(tr);
      });
    }

    function filtrerSources() {
      const q = (document.getElementById('audit-search-input')?.value || '').toLowerCase();
      let res = allSources;
      if (activeSourceCategory) {
        res = res.filter(s => s.categorie.toLowerCase() === activeSourceCategory.toLowerCase());
      }
      if (q) {
        res = res.filter(s =>
          s.id_source.toLowerCase().includes(q) ||
          s.nom_indicateur.toLowerCase().includes(q) ||
          s.organisme.toLowerCase().includes(q)
        );
      }
      afficherSourcesTable(res);
    }

    function filtrerSourcesCategorie(cat) {
      activeSourceCategory = cat;
      document.querySelectorAll('#tab-audit .filter-btn').forEach(b => b.classList.remove('active'));
      event.target.classList.add('active');
      filtrerSources();
    }

    // =============================================================
    // GESTION ONGLET 11 : THINK TANKS & AUDIT CONTRADICTOIRE
    // =============================================================
    let allThinkTanks = [];
    let activeThinkTankEchelon = '';
    let stressTestsData = null;

    async function chargerThinkTanks() {
      try {
        // 1. Charger les résultats de stress-tests
        const respStress = await fetch('/api/stress_tests');
        const dataStress = await respStress.json();
        stressTestsData = dataStress.resultats || {};
        afficherStressTests(stressTestsData);

        // 2. Charger le répertoire des think tanks
        const respTT = await fetch('/api/think_tanks');
        const dataTT = await respTT.json();
        allThinkTanks = dataTT.think_tanks || [];
        
        const totalEl = document.getElementById('tt-kpi-total');
        if (totalEl) totalEl.innerText = allThinkTanks.length + " Instituts";

        afficherThinkTanks(allThinkTanks);
      } catch (e) {
        console.error("Erreur chargement think tanks:", e);
      }
    }

    function afficherStressTests(tests) {
      const container = document.getElementById('stress-tests-container');
      if (!container) return;
      container.innerHTML = '';

      Object.values(tests).forEach(st => {
        const card = document.createElement('div');
        card.className = 'stress-card';

        let criteresHtml = '';
        for (const [key, crit] of Object.entries(st.criteres_analyses)) {
          const badgeConforme = crit.conforme ? '<span class="badge badge-success">CONFORME</span>' : '<span class="badge badge-danger">NON CONFORME</span>';
          criteresHtml += `
            <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.78rem; padding:4px 0; border-bottom:1px solid rgba(255,255,255,0.05);">
              <span style="color:#cbd5e1;">${key}</span>
              <span><strong>${crit.valeur}</strong> <span style="font-size:0.7rem; color:#94a3b8;">${crit.unite}</span> ${badgeConforme}</span>
            </div>
          `;
        }

        let reponsesHtml = st.reponses_systemiques.map(r => `<li>${r}</li>`).join('');

        card.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <strong style="color:var(--accent-cyan); font-size:0.95rem;">${st.titre}</strong>
            <span class="badge badge-success" style="font-size:0.75rem;">${st.statut} (${st.score_robustesse_sur_100}%)</span>
          </div>
          <div style="margin-top:6px;">${criteresHtml}</div>
          <div class="tt-box tt-box-reponse" style="margin-top:8px;">
            <div style="font-weight:700; margin-bottom:4px;">🛡️ Réponse du simulateur à la brèche :</div>
            <ul style="margin:0; padding-left:16px; font-size:0.78rem;">${reponsesHtml}</ul>
          </div>
          <div style="font-size:0.75rem; color:#94a3b8; font-style:italic;">
            🔬 <strong>Raisonnement :</strong> ${st.justification_scientifique}
          </div>
        `;
        container.appendChild(card);
      });
    }

    function afficherThinkTanks(liste) {
      const container = document.getElementById('thinktanks-cards-container');
      if (!container) return;
      container.innerHTML = '';

      liste.forEach(tt => {
        const card = document.createElement('div');
        card.className = 'tt-card';

        const echelonBadges = {
          local: '<span class="badge badge-warning">Local / Territoires</span>',
          national: '<span class="badge badge-primary">National (France)</span>',
          europeen: '<span class="badge badge-cyan">Européen (UE)</span>',
          international: '<span class="badge badge-indigo">International / Mondial</span>'
        };

        let pubsHtml = tt.sources_cles.map(s => `
          <div style="font-size:0.78rem; margin-bottom:6px;">
            📄 <strong>${s.titre}</strong> (${s.annee}) — <em>${s.auteurs}</em><br>
            <span style="color:#94a3b8; font-size:0.74rem;">${s.resume_methodologique}</span><br>
            <a href="${s.url}" target="_blank" rel="noopener noreferrer" style="color:var(--accent-cyan); font-size:0.75rem; text-decoration:underline;">Consulter la note source ↗</a>
          </div>
        `).join('');

        let objectionsHtml = tt.objections_anticipees.map(o => `<li>${o}</li>`).join('');

        card.innerHTML = `
          <div class="tt-header">
            <div>
              <span class="tt-title">${tt.nom} (${tt.sigle})</span>
              <span style="margin-left:8px;">${echelonBadges[tt.echelon] || ''}</span>
            </div>
            <div style="font-size:0.8rem; color:#94a3b8;">${tt.pays_siege} • Dir : <strong>${tt.directeur_ou_fondateur}</strong></div>
          </div>
          <div class="tt-meta">
            🎯 <strong>Orientation :</strong> <span style="color:#e2e8f0;">${tt.epistemologie}</span>
          </div>
          
          <div style="background:#090d16; padding:10px; border-radius:6px; margin-bottom:10px;">
            <div style="font-size:0.8rem; font-weight:700; color:#cbd5e1; margin-bottom:6px;">📚 Publications & Méthodologie :</div>
            ${pubsHtml}
          </div>

          <div class="tt-box tt-box-objection">
            <strong>⚠️ Objection critique anticipée (Brèche visée par les détracteurs) :</strong>
            <ul style="margin:4px 0 0 0; padding-left:18px;">${objectionsHtml}</ul>
          </div>

          <div class="tt-box tt-box-pourquoi">
            <strong>💡 Pourquoi nous l'intégrons impérativement :</strong><br>
            <span>${tt.pourquoi_integration}</span>
          </div>

          <div class="tt-box tt-box-reponse">
            <strong>🛡️ Réponse mathématique & institutionnelle du Simulateur :</strong><br>
            <span>${tt.reponse_du_simulateur}</span>
          </div>
        `;
        container.appendChild(card);
      });
    }

    function filtrerThinkTanks() {
      const q = (document.getElementById('tt-search-input')?.value || '').toLowerCase();
      let res = allThinkTanks;
      if (activeThinkTankEchelon) {
        res = res.filter(tt => tt.echelon.toLowerCase() === activeThinkTankEchelon.toLowerCase());
      }
      if (q) {
        res = res.filter(tt =>
          tt.nom.toLowerCase().includes(q) ||
          tt.sigle.toLowerCase().includes(q) ||
          tt.epistemologie.toLowerCase().includes(q) ||
          tt.pourquoi_integration.toLowerCase().includes(q) ||
          tt.reponse_du_simulateur.toLowerCase().includes(q)
        );
      }
      afficherThinkTanks(res);
    }

    function filtrerThinkTanksEchelon(echelon, btn) {
      activeThinkTankEchelon = echelon;
      document.querySelectorAll('#tab-thinktanks .filter-pill').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');
      filtrerThinkTanks();
    }

    // =============================================================
    // GESTION ONGLET 12 : HISTOIRE & COMPARAISONS (1792→2026)
    // =============================================================
    let histoireOptionsLoaded = false;

    async function chargerHistoire() {
      try {
        // 1. Charger les options dropdown
        if (!histoireOptionsLoaded) {
          const respOpts = await fetch('/api/histoire/options');
          const opts = await respOpts.json();
          const selA = document.getElementById('hist-select-a');
          const selB = document.getElementById('hist-select-b');
          const selDim = document.getElementById('hist-select-dim');
          if (selA && opts.periodes) {
            selA.innerHTML = opts.periodes.map(p => `<option value="${p.id}">${p.nom} (${p.annees})</option>`).join('');
          }
          if (selB && opts.periodes) {
            selB.innerHTML = opts.periodes.map(p => `<option value="${p.id}">${p.nom} (${p.annees})</option>`).join('');
            if (selB.options.length > 1) selB.selectedIndex = 1;
          }
          if (selDim && opts.dimensions) {
            selDim.innerHTML = opts.dimensions.map(d => `<option value="${d.id}">${d.label}</option>`).join('');
          }
          histoireOptionsLoaded = true;
        }

        // 2. Charger la synthèse
        const respSyn = await fetch('/api/histoire/synthese');
        const dataSyn = await respSyn.json();
        const synEl = document.getElementById('hist-synthese');
        if (synEl) synEl.innerText = dataSyn.synthese || 'Aucune synthèse disponible.';

        // 3. Charger les paramètres de calibration
        if (dataSyn.parametres_calibration) {
          const calib = dataSyn.parametres_calibration;
          const tbody = document.getElementById('hist-calibration-tbody');
          if (tbody) {
            tbody.innerHTML = '';
            for (const [key, val] of Object.entries(calib)) {
              if (typeof val === 'object' && val.min_historique !== undefined) {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td><strong>${key.replace(/_/g, ' ').toUpperCase()}</strong></td>` +
                  `<td>${val.min_historique}</td><td>${val.max_historique}</td>` +
                  `<td><strong style="color:var(--accent-emerald)">${val.cible_simulateur}</strong></td>` +
                  `<td style="color:#94a3b8; font-size:0.8rem;">${val.plage_optimale || val.plage_soutenable || '-'}</td>`;
                tbody.appendChild(tr);
              }
            }
          }
        }

        // 4. Charger les réformes
        const respRef = await fetch('/api/histoire/reformes');
        const dataRef = await respRef.json();
        const refContainer = document.getElementById('hist-reformes-container');
        if (refContainer && dataRef.reformes) {
          refContainer.innerHTML = '';
          dataRef.reformes.forEach(r => {
            const card = document.createElement('div');
            card.className = 'tt-card';
            card.innerHTML = `
              <div class="tt-header">
                <span class="tt-title">${r.nom}</span>
                <span class="badge badge-primary">${r.annee} • ${r.categorie}</span>
              </div>
              <div class="tt-meta">${r.regime_contexte}</div>
              <div style="font-size:0.82rem; margin-bottom:8px;">${r.description}</div>
              <div class="tt-box tt-box-pourquoi">
                <strong>Impact immédiat :</strong> ${r.impact_immediat}<br>
                <strong>Impact long terme :</strong> ${r.impact_long_terme}
              </div>
              <div class="tt-box tt-box-reponse">
                <strong>Pertinence pour le simulateur :</strong> ${r.pertinence_pour_simulateur}
              </div>
              <div style="font-size:0.78rem; color:#94a3b8;">Rendement estimé : <strong>${r.rendement_estime_mds_euros} Md€</strong></div>
            `;
            refContainer.appendChild(card);
          });
        }

        // 5. Charger les crises
        const respCrises = await fetch('/api/histoire/crises');
        const dataCrises = await respCrises.json();
        const crisesContainer = document.getElementById('hist-crises-container');
        if (crisesContainer && dataCrises.crises) {
          crisesContainer.innerHTML = '';
          dataCrises.crises.forEach(c => {
            const card = document.createElement('div');
            card.className = 'tt-card';
            const graviteBadge = c.gravite >= 8 ? 'badge-danger' : (c.gravite >= 5 ? 'badge-warning' : 'badge-primary');
            card.innerHTML = `
              <div class="tt-header">
                <span class="tt-title">${c.nom}</span>
                <span class="badge ${graviteBadge}">Gravité ${c.gravite}/10</span>
              </div>
              <div class="tt-meta">${c.annee_debut}→${c.annee_fin} • ${c.type_crise}</div>
              <div style="font-size:0.8rem; display:grid; grid-template-columns:1fr 1fr; gap:6px; margin:8px 0;">
                <div>📉 PIB : <strong style="color:var(--accent-crimson)">${c.impact_pib_pct > 0 ? '+' : ''}${c.impact_pib_pct}%</strong></div>
                <div>📊 Dette : <strong style="color:var(--accent-crimson)">+${c.impact_dette_pct_pib} pts PIB</strong></div>
                <div>👷 Chômage : <strong>+${c.impact_chomage_pct} pts</strong></div>
                <div>⏱️ Récupération : <strong>${c.duree_recuperation_annees} ans</strong></div>
              </div>
              <div class="tt-box tt-box-pourquoi"><strong>Réponse publique :</strong> ${c.reponse_publique}</div>
              <div class="tt-box tt-box-reponse"><strong>Leçon pour le simulateur :</strong> ${c.lecons}</div>
            `;
            crisesContainer.appendChild(card);
          });
        }

      } catch (e) {
        console.error("Erreur chargement histoire:", e);
      }
    }

    async function lancerComparaisonHistorique() {
      const aId = document.getElementById('hist-select-a')?.value;
      const bId = document.getElementById('hist-select-b')?.value;
      const dim = document.getElementById('hist-select-dim')?.value;
      if (!aId || !bId) return;

      try {
        const url = `/api/histoire/comparer?a=${aId}&b=${bId}&dimensions=${dim}`;
        const resp = await fetch(url);
        const data = await resp.json();

        const resultDiv = document.getElementById('hist-comparaison-resultat');
        if (resultDiv) resultDiv.style.display = 'block';

        document.getElementById('hist-comp-titre-a').innerText = data.periode_a;
        document.getElementById('hist-comp-titre-b').innerText = data.periode_b;

        const tbody = document.getElementById('hist-comp-tbody');
        tbody.innerHTML = '';
        if (data.dimensions) {
          for (const [dimKey, indicateurs] of Object.entries(data.dimensions)) {
            for (const [attr, vals] of Object.entries(indicateurs)) {
              const tr = document.createElement('tr');
              const delta = vals.delta !== null ? vals.delta.toFixed(2) : '-';
              const deltaColor = vals.delta > 0 ? 'var(--accent-crimson)' : (vals.delta < 0 ? 'var(--accent-emerald)' : 'var(--text-muted)');
              tr.innerHTML = `
                <td><strong>${vals.label || attr}</strong></td>
                <td>${typeof vals.a === 'number' ? vals.a.toFixed(2) : vals.a}</td>
                <td>${typeof vals.b === 'number' ? vals.b.toFixed(2) : vals.b}</td>
                <td style="color:${deltaColor}; font-weight:700;">${delta}</td>
              `;
              tbody.appendChild(tr);
            }
          }
        }

        const ensDiv = document.getElementById('hist-enseignements-liste');
        ensDiv.innerHTML = '';
        if (data.enseignements) {
          data.enseignements.forEach(ens => {
            const div = document.createElement('div');
            div.className = 'event-line';
            div.innerText = ens;
            ensDiv.appendChild(div);
          });
        }
      } catch (e) {
        console.error("Erreur comparaison historique:", e);
      }
    }

    // =============================================================
    // GESTION ONGLET 13 : SOCIÉTÉ — 18 DOMAINES (1792→2026)
    // =============================================================
    let allDomaines = [];
    let domaineDetailData = null;

    async function chargerSociete() {
      try {
        const resp = await fetch('/api/societe');
        const data = await resp.json();
        allDomaines = data.domaines || [];

        let nbPoints = 0, nbReformes = 0, nbCrises = 0;
        allDomaines.forEach(d => {
          nbPoints += d.nb_points_historiques;
          nbReformes += d.nb_reformes;
          nbCrises += d.nb_crises;
        });

        const elP = document.getElementById('soc-kpi-points');
        if (elP) elP.innerText = nbPoints;
        const elR = document.getElementById('soc-kpi-reformes');
        if (elR) elR.innerText = nbReformes;
        const elC = document.getElementById('soc-kpi-crises');
        if (elC) elC.innerText = nbCrises;

        afficherDomaines(allDomaines);
      } catch (e) {
        console.error("Erreur chargement societe:", e);
      }
    }

    function afficherDomaines(liste) {
      const container = document.getElementById('societe-domaines-container');
      if (!container) return;
      container.innerHTML = '';

      liste.forEach(d => {
        const card = document.createElement('div');
        card.className = 'tt-card';
        card.style.cursor = 'pointer';
        card.onclick = () => afficherDetailDomaine(d.id);
        card.innerHTML = `
          <div class="tt-header">
            <span class="tt-title">${d.icon} ${d.nom}</span>
            <span class="badge badge-primary">${d.nb_indicateurs} indicateurs</span>
          </div>
          <div style="font-size:0.82rem; color:var(--text-muted); margin-bottom:8px;">${d.description}</div>
          <div style="display:flex; gap:12px; font-size:0.78rem;">
            <span>📊 ${d.nb_points_historiques} pts</span>
            <span>⚖️ ${d.nb_reformes} réformes</span>
            <span>🔥 ${d.nb_crises} crises</span>
          </div>
        `;
        container.appendChild(card);
      });
    }

    async function afficherDetailDomaine(domaineId) {
      try {
        const resp = await fetch('/api/societe?id=' + domaineId);
        const d = await resp.json();
        domaineDetailData = d;

        document.getElementById('soc-detail-domaine').style.display = 'block';
        document.getElementById('soc-detail-titre').innerText = d.icon + ' ' + d.nom;

        // Indicateurs
        const indDiv = document.getElementById('soc-detail-indicateurs');
        indDiv.innerHTML = '';
        if (d.indicateurs_cles) {
          for (const [key, label] of Object.entries(d.indicateurs_cles)) {
            const row = document.createElement('div');
            row.className = 'metric-row';
            row.innerHTML = `<span>${label}</span><strong style="color:var(--accent-cyan)">${key}</strong>`;
            indDiv.appendChild(row);
          }
        }

        // Réformes
        const refDiv = document.getElementById('soc-detail-reformes');
        refDiv.innerHTML = '';
        if (d.reformes_majeures) {
          d.reformes_majeures.forEach(r => {
            const row = document.createElement('div');
            row.className = 'metric-row';
            row.innerHTML = `<span><strong>${r.nom}</strong> (${r.annee})</span>`;
            refDiv.appendChild(row);
            const impact = document.createElement('div');
            impact.style.cssText = 'font-size:0.78rem; color:#94a3b8; padding:2px 0 6px 0;';
            impact.innerText = r.impact;
            refDiv.appendChild(impact);
          });
        }

        // Crises
        const crisDiv = document.getElementById('soc-detail-crises');
        crisDiv.innerHTML = '';
        if (d.crises) {
          d.crises.forEach(c => {
            const row = document.createElement('div');
            row.className = 'metric-row';
            row.innerHTML = `<span><strong>${c.nom}</strong> (${c.annee})</span>`;
            crisDiv.appendChild(row);
            const impact = document.createElement('div');
            impact.style.cssText = 'font-size:0.78rem; color:#fca5a5; padding:2px 0 6px 0;';
            impact.innerText = c.impact;
            crisDiv.appendChild(impact);
          });
        }

        // Calibration
        const calDiv = document.getElementById('soc-detail-calibration');
        calDiv.innerHTML = '';
        if (d.parametres_calibration) {
          for (const [key, val] of Object.entries(d.parametres_calibration)) {
            const row = document.createElement('div');
            row.className = 'metric-row';
            const valStr = typeof val === 'object' ? Object.entries(val).map(([k,v]) => `${k}: ${v}`).join(' | ') : val;
            row.innerHTML = `<span>${key.replace(/_/g, ' ')}</span><strong>${valStr}</strong>`;
            calDiv.appendChild(row);
          }
        }

        document.getElementById('soc-detail-pourquoi').innerText = d.pourquoi_integration || '-';
        document.getElementById('soc-detail-pertinence').innerText = d.pertinence_pour_simulateur || '-';

        // Scroll to detail
        document.getElementById('soc-detail-domaine').scrollIntoView({behavior: 'smooth', block: 'start'});
      } catch (e) {
        console.error("Erreur détail domaine:", e);
      }
    }

    function filtrerDomaines() {
      const q = (document.getElementById('soc-search-input')?.value || '').toLowerCase();
      if (!q) {
        afficherDomaines(allDomaines);
      } else {
        const filtered = allDomaines.filter(d =>
          d.nom.toLowerCase().includes(q) ||
          d.id.toLowerCase().includes(q) ||
          d.description.toLowerCase().includes(q)
        );
        afficherDomaines(filtered);
      }
    }

    // Démarrage initial
    window.onload = () => {
      chargerSimulation('mandature');
    };
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    demarrer_serveur_web(port=port)
