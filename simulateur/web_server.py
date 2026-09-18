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

from simulateur.model import DecisionPolitique, ResultatEtapeSimulation
from simulateur.moteur import MoteurSimulationSystemique
from simulateur.scenarios import (
    get_scenario_mandature_5_ans,
    get_scenario_statut_quo,
    get_scenario_austerite_brutale,
    get_scenario_choc_mondial_stagflation,
)
from simulateur.reglements_lois import get_corpus_lois, rechercher_loi


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
                    "sections_commune_lieux_dits": 2500,
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
                "outre_mer": [
                    {"code": "971", "nom": "Guadeloupe", "statut": "DROM (Art. 73)", "population": 384000, "assemblees": "Conseil régional + Conseil départemental"},
                    {"code": "972", "nom": "Martinique", "statut": "DROM / CTU (Art. 73)", "population": 361000, "assemblees": "Assemblée de Martinique (61 élus) + Conseil exécutif"},
                    {"code": "973", "nom": "Guyane", "statut": "DROM / CTU (Art. 73)", "population": 294000, "assemblees": "Assemblée de Guyane (55 élus) + Conseil exécutif"},
                    {"code": "974", "nom": "La Réunion", "statut": "DROM (Art. 73)", "population": 873000, "assemblees": "Conseil régional + Conseil départemental"},
                    {"code": "976", "nom": "Mayotte", "statut": "DROM / Dép-Rég (Art. 73)", "population": 310000, "assemblees": "Conseil départemental de Mayotte (26 élus)"},
                    {"code": "977", "nom": "Saint-Barthélemy", "statut": "COM (Art. 74)", "population": 10500, "assemblees": "Conseil territorial (19 élus)"},
                    {"code": "978", "nom": "Saint-Martin", "statut": "COM (Art. 74)", "population": 32000, "assemblees": "Conseil territorial (23 élus)"},
                    {"code": "975", "nom": "Saint-Pierre-et-Miquelon", "statut": "COM (Art. 74)", "population": 6000, "assemblees": "Conseil territorial (19 élus)"},
                    {"code": "986", "nom": "Wallis-et-Futuna", "statut": "COM (Art. 74)", "population": 11500, "assemblees": "Assemblée territoriale (20 élus) + 3 chefferies coutumières"},
                    {"code": "987", "nom": "Polynésie française", "statut": "COM Autonome (Art. 74)", "population": 280000, "assemblees": "Assemblée de Polynésie (57 élus) + Gouvernement polynésien"},
                    {"code": "988", "nom": "Nouvelle-Calédonie", "statut": "Sui Generis (Titre XIII Const.)", "population": 271000, "assemblees": "Congrès de Nouvelle-Calédonie (54 élus) + 3 Provinces + Sénat coutumier"},
                    {"code": "984", "nom": "Terres Australes & Antarctiques (TAAF)", "statut": "Territoire d'Outre-Mer administré", "population": 200, "assemblees": "Préfet administrateur supérieur + Conseil consultatif"},
                    {"code": "989", "nom": "Île de Clipperton", "statut": "Domaine public de l'État", "population": 0, "assemblees": "Ministre chargé des Outre-Mer"},
                    {"code": "FE", "nom": "Français établis hors de France", "statut": "Représentation mondiale (Art. 24 al. 4)", "population": 2100000, "assemblees": "11 Députés + 12 Sénateurs + AFE (90 conseillers) + 442 conseillers consulaires"}
                ],
                "souverainete_maritime_zee_km2": 10200000,
                "surcout_vie_chere_alimentaire_pct": 32.5,
                "octroi_de_mer_annuel_mde": 1.6
            })
            return

        # 10. API Élections & Démocratie
        if path == "/api/elections":
            self._envoyer_json(200, {
                "reu_electeurs_inscrits": 49500000,
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
                "referendums": [
                    {"article": "Article 11", "nature": "Référendum législatif & RIP", "declenchement": "Présidentiel sur proposition gouvernementale/parlementaire ou RIP (185 parlementaires + 4,95M électeurs)"},
                    {"article": "Article 89", "nature": "Référendum constitutionnel", "declenchement": "Obligatoire après vote conforme AN + Sénat, sauf approbation par le Congrès à Versailles (3/5èmes)"},
                    {"article": "Article 72-1", "nature": "Référendum décisionnel local", "declenchement": "Délibération d'une collectivité territoriale sur ses compétences propres (seuil participation 50%)"},
                    {"article": "Article 72-4", "nature": "Consultation statutaire d'Outre-mer", "declenchement": "Préalable obligatoire à toute évolution institutionnelle ou statutaire ultramarine"}
                ]
            })
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
        <button onclick="showTab('comparatif')">⚖️ Comparateur</button>
        <button onclick="showTab('architecture')">🏛️ Les 4 Strates</button>
        <button onclick="showTab('corpus')">📜 Corpus Juridique</button>
        <button onclick="showTab('dossier')">📖 Mandature (+60 Md€)</button>
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
            <div class="metric-row"><span>Gestion</span><strong>Commissions syndicales d'habitants</strong></div>
            <div class="metric-row"><span>Patrimoine</span><strong>Affouage, estives, forêts indivises</strong></div>
          </div>

          <div class="strate-card">
            <h4>🌾 Communes Rurales (< 1 000 hab.)</h4>
            <div class="metric-row"><span>Nombre de mairies</span><strong>25 800 communes (74 % du total)</strong></div>
            <div class="metric-row"><span>Population couverte</span><strong>15 % de la population nationale</strong></div>
            <div class="metric-row"><span>Règle d'or (L. 1612-4)</span><strong style="color:var(--accent-emerald)">Équilibre fonctionnement obligatoire</strong></div>
            <div class="metric-row"><span>Mesure Mandature</span><strong style="color:var(--accent-emerald)">Sanctuaire DGF rurale & cantines locales</strong></div>
          </div>

          <div class="strate-card">
            <h4>🏘️ Bourgs-Centres (1 000 à 9 999 hab.)</h4>
            <div class="metric-row"><span>Nombre de communes</span><strong>7 650 bourgs</strong></div>
            <div class="metric-row"><span>Population couverte</span><strong>32 % de la population nationale</strong></div>
            <div class="metric-row"><span>Équipements</span><strong>Écoles primaires, collèges, artisans</strong></div>
            <div class="metric-row"><span>Mesure Mandature</span><strong style="color:var(--accent-emerald)">Allotissement 30% commande publique aux PME</strong></div>
          </div>

          <div class="strate-card">
            <h4>🏭 Villes Moyennes (10 000 à 49 999 hab.)</h4>
            <div class="metric-row"><span>Nombre de villes</span><strong>1 280 communes</strong></div>
            <div class="metric-row"><span>Population couverte</span><strong>24 % de la population</strong></div>
            <div class="metric-row"><span>Rôle républicain</span><strong>Hôpitaux de secteur, lycées, tribunaux</strong></div>
            <div class="metric-row"><span>Mesure Mandature</span><strong style="color:var(--accent-emerald)">Réhabilitation friches & relocalisation</strong></div>
          </div>

          <div class="strate-card">
            <h4>🏙️ Grandes Agglomérations (50k à 200k)</h4>
            <div class="metric-row"><span>Nombre de pôles</span><strong>180 grandes villes & agglos</strong></div>
            <div class="metric-row"><span>Services majeurs</span><strong>CHU, universités, réseaux tramways, TGV</strong></div>
            <div class="metric-row"><span>Intercommunalité</span><strong>Communautés d'agglomération & urbaines</strong></div>
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

        <!-- Section 2 : L'Outre-Mer Républicain Intégral -->
        <h3 style="margin-bottom:12px; font-weight:800;">🌊 2. L'Outre-Mer Français Intégral (DROM, COM, Calédonie & ZEE Maritime)</h3>
        <div class="table-container" style="margin-bottom:24px;">
          <table>
            <thead>
              <tr>
                <th>Territoire Ultramarin</th>
                <th>Régime Constitutionnel</th>
                <th>Population</th>
                <th>Institutions & Assemblées</th>
                <th>Enjeux Clés & Mesures Mandature</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Guadeloupe (971)</strong></td>
                <td>DROM (Article 73)</td>
                <td>384 000 hab.</td>
                <td>Conseil régional + Conseil départemental</td>
                <td>Octroi de mer réformé, baisse coût du fret, rénovation réseaux eau.</td>
              </tr>
              <tr>
                <td><strong>Martinique (972)</strong></td>
                <td>CTU (Article 73)</td>
                <td>361 000 hab.</td>
                <td>Assemblée de Martinique (61 élus) + Conseil exécutif</td>
                <td>Collectivité Unique, bouclier vie chère, transition agro-écologique.</td>
              </tr>
              <tr>
                <td><strong>Guyane (973)</strong></td>
                <td>CTU (Article 73)</td>
                <td>294 000 hab.</td>
                <td>Assemblée de Guyane (55 élus) + Centre Spatial CSG</td>
                <td>Collectivité Unique, désenclavement routier, protection forêt amazonienne.</td>
              </tr>
              <tr>
                <td><strong>La Réunion (974)</strong></td>
                <td>DROM (Article 73)</td>
                <td>873 000 hab.</td>
                <td>Conseil régional + Conseil départemental</td>
                <td>Pôle de l'océan Indien, égalité réelle, désenclavement énergétique.</td>
              </tr>
              <tr>
                <td><strong>Mayotte (976)</strong></td>
                <td>Département-Région (Art. 73)</td>
                <td>310 000 hab.</td>
                <td>Conseil départemental de Mayotte (26 élus)</td>
                <td>Rattrapage d'infrastructures républicaines, eau potable, sécurité frontalière.</td>
              </tr>
              <tr>
                <td><strong>Saint-Barthélemy (977) & St-Martin (978)</strong></td>
                <td>COM (Article 74)</td>
                <td>42 500 hab.</td>
                <td>Conseils territoriaux autonomes (19 et 23 élus)</td>
                <td>Autonomie fiscale et douanière, coopération avec Sint Maarten.</td>
              </tr>
              <tr>
                <td><strong>Saint-Pierre-et-Miquelon (975)</strong></td>
                <td>COM (Article 74)</td>
                <td>6 000 hab.</td>
                <td>Conseil territorial (19 élus)</td>
                <td>Atlantique Nord, souveraineté halieutique, liaison aérienne directe.</td>
              </tr>
              <tr>
                <td><strong>Wallis-et-Futuna (986)</strong></td>
                <td>COM (Article 74)</td>
                <td>11 500 hab.</td>
                <td>Assemblée territoriale (20 élus) + 3 Rois coutumiers</td>
                <td>Coexistence républicaine et coutumière (Uvea, Sigave, Alo).</td>
              </tr>
              <tr>
                <td><strong>Polynésie française (987)</strong></td>
                <td>COM Autonome (Article 74)</td>
                <td>280 000 hab.</td>
                <td>Assemblée de Polynésie (57 élus) + Gouvernement propre</td>
                <td>Lois du pays, autonomie renforcée, 118 îles sur 5 archipels, ZEE Pacifique.</td>
              </tr>
              <tr>
                <td><strong>Nouvelle-Calédonie (988)</strong></td>
                <td>Sui Generis (Titre XIII Const.)</td>
                <td>271 000 hab.</td>
                <td>Congrès de la NC (54 élus) + 3 Provinces + Sénat coutumier</td>
                <td>Accord de Nouméa, collégialité gouvernementale, réconciliation et nickel.</td>
              </tr>
              <tr>
                <td><strong>TAAF (984) & Clipperton (989)</strong></td>
                <td>Domaine de l'État / Terres australes</td>
                <td>~200 scient.</td>
                <td>Préfet administrateur supérieur / Ministre Outre-mer</td>
                <td>Sanctuaires écologiques mondiaux, surveillance navale ZEE antarctique.</td>
              </tr>
              <tr>
                <td><strong>Français établis hors de France</strong></td>
                <td>Représentation mondiale (Art. 24)</td>
                <td>2,1 millions</td>
                <td>11 Députés + 12 Sénateurs + AFE (90 conseillers)</td>
                <td>442 conseillers consulaires, dématérialisation consulaire, bourses scolaires.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Section 3 : L'Armature Électorale et Démocratique -->
        <h3 style="margin-bottom:12px; font-weight:800;">🗳️ 3. L'Armature Électorale Complète de la Nation (49,5M d'électeurs)</h3>
        <div class="strates-grid" style="margin-bottom:24px;">
          <div class="strate-card">
            <h4>🇫🇷 Élection Présidentielle</h4>
            <div class="metric-row"><span>Mandat</span><strong>5 ans (Quinquennat)</strong></div>
            <div class="metric-row"><span>Mode de scrutin</span><strong>Uninominal majoritaire à 2 tours</strong></div>
            <div class="metric-row"><span>Filtre préalable</span><strong>500 parrainages d'élus (30 départements)</strong></div>
            <div class="metric-row"><span>Base constitutionnelle</span><strong>Articles 6 et 7 de la Constitution</strong></div>
          </div>

          <div class="strate-card">
            <h4>🏛️ Élections Législatives</h4>
            <div class="metric-row"><span>Sièges</span><strong>577 députés (539 Hex., 27 OM, 11 FE)</strong></div>
            <div class="metric-row"><span>Mode de scrutin</span><strong>Uninominal majoritaire à 2 tours</strong></div>
            <div class="metric-row"><span>Seuil second tour</span><strong>12,5 % des électeurs inscrits</strong></div>
            <div class="metric-row"><span>Triangulaires projetées</span><strong id="terr-triang-val">38 circonscriptions</strong></div>
          </div>

          <div class="strate-card">
            <h4>🏛️ Élections Sénatoriales</h4>
            <div class="metric-row"><span>Sièges</span><strong>348 sénateurs (renouvellement par moitié /3 ans)</strong></div>
            <div class="metric-row"><span>Corps électoral</span><strong>162 000 grands électeurs (95% municipaux)</strong></div>
            <div class="metric-row"><span>Scrutins</span><strong>Majoritaire (<3 sén.) ou proportionnel (>=3 sén.)</strong></div>
            <div class="metric-row"><span>Base légale</span><strong>Art. 24 Const. & Art. L. 279 Code électoral</strong></div>
          </div>

          <div class="strate-card">
            <h4>🗳️ Élections Municipales & EPCI</h4>
            <div class="metric-row"><span>Membres élus</span><strong>~500 000 conseillers municipaux</strong></div>
            <div class="metric-row"><span>Mode de scrutin</span><strong>Proportionnel avec prime 50% (>=1000 hab.)</strong></div>
            <div class="metric-row"><span>Parité légale</span><strong>Stricte alternance femme-homme</strong></div>
            <div class="metric-row"><span>Fléchage</span><strong>Élection directe délégués communautaires EPCI</strong></div>
          </div>

          <div class="strate-card">
            <h4>🗺️ Élections Départementales</h4>
            <div class="metric-row"><span>Sièges</span><strong>4 056 conseillers (2 054 cantons)</strong></div>
            <div class="metric-row"><span>Mode de scrutin</span><strong>Binominal paritaire (1 femme + 1 homme)</strong></div>
            <div class="metric-row"><span>Seuil maintien 2nd tour</span><strong>12,5 % des électeurs inscrits</strong></div>
            <div class="metric-row"><span>Compétences</span><strong>Solidarités sociales (RSA, APA) & collèges</strong></div>
          </div>

          <div class="strate-card">
            <h4>🚆 Élections Régionales</h4>
            <div class="metric-row"><span>Sièges</span><strong>1 757 conseillers (18 régions)</strong></div>
            <div class="metric-row"><span>Mode de scrutin</span><strong>Proportionnel de liste à 2 tours</strong></div>
            <div class="metric-row"><span>Prime majoritaire</span><strong>25 % des sièges à la liste en tête</strong></div>
            <div class="metric-row"><span>Seuils</span><strong>10% pour maintien, 5% pour fusion</strong></div>
          </div>
        </div>

        <!-- Section 4 : Le Bloc de Constitutionnalité et les Grands Codes -->
        <h3 style="margin-bottom:12px; font-weight:800;">📜 4. Les Textes Fondamentaux Constituant et Régissant la Nation</h3>
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
                <td>Art. 1 (Égalité), Art. 3 (Souveraineté nationale), Art. 6 (Volonté générale), Art. 13-14 (Consentement à l'impôt).</td>
                <td>Cadre suprême inviolable de toute décision publique républicaine.</td>
              </tr>
              <tr>
                <td><strong>Bloc de Constitutionnalité</strong></td>
                <td><strong>Préambule de la Constitution de 1946</strong></td>
                <td>Égalité homme-femme (al. 3), nationalisations des monopoles (al. 9), protection santé et famille (al. 10-11).</td>
                <td>Fonde le pacte social du berceau au tombeau et la Sécurité sociale.</td>
              </tr>
              <tr>
                <td><strong>Bloc de Constitutionnalité</strong></td>
                <td><strong>Charte de l'environnement de 2004</strong></td>
                <td>Art. 1 (Droit environnement sain), Art. 4 (Pollueur-payeur), Art. 5 (Principe de précaution).</td>
                <td>Encadre la transition écologique et la taxe carbone frontalière MACF.</td>
              </tr>
              <tr>
                <td><strong>Bloc de Constitutionnalité</strong></td>
                <td><strong>Constitution du 4 octobre 1958</strong></td>
                <td>Art. 1 (République indivisible et décentralisée), Art. 24 (Parlement), Art. 49 (Censure), Art. 72-74 (Outre-Mer).</td>
                <td>Équilibre des pouvoirs, régulation des 12 assemblées et des 4 strates.</td>
              </tr>
              <tr>
                <td><strong>Législation Républicaine</strong></td>
                <td><strong>Code électoral</strong></td>
                <td>Art. L. 16 (REU INSEE 49,5M électeurs), Art. L. 123 (Législatives), Art. L. 260 (Municipales).</td>
                <td>Garantit la sincérité, la transparence et la régularité des scrutins républicains.</td>
              </tr>
              <tr>
                <td><strong>Législation Républicaine</strong></td>
                <td><strong>Code Général des Collectivités (CGCT)</strong></td>
                <td>Art. L. 1612-4 (Règle d'or budgétaire), Art. L. 2121-1 (Communes), Art. L. 2411-1 (Sections).</td>
                <td>Équilibre de gestion des 34 935 communes et des 1 254 EPCI.</td>
              </tr>
              <tr>
                <td><strong>Législation Républicaine</strong></td>
                <td><strong>Code de la Commande Publique (CCP)</strong></td>
                <td>Art. L. 2113-10 (Allotissement obligatoire), Art. L. 2112-2 (Critères environnementaux).</td>
                <td>Réservation de 30 % des marchés publics aux PME et artisans locaux (+6 Md€).</td>
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
      if (tabName === 'comparatif') chargerComparatif();
      if (tabName === 'corpus' && allCorpusArticles.length === 0) chargerCorpus();
      if (tabName === 'dossier') chargerDossier();
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
