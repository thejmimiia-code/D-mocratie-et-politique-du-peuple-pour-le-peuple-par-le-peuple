#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py — Extension ÉVA : Simulateur Macro-Politique & Démocratique (Protocole 4.2.3)
=====================================================================================

Cette extension intègre le modèle systémique gigogne à 4 échelons (Local, National,
Europe, Marchés) au cœur cognitif d'ÉVA.
Elle permet à ÉVA de tester des scénarios budgétaires, d'évaluer la trajectoire de la
dette souveraine, et de mesurer les impacts sur le pouvoir d'achat et la tension sociale.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Any, List

RACINE = Path(__file__).resolve().parents[2]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from eva.extensions.bus import EventBus  # noqa: E402

EVENEMENT_DEMANDE = "politique.simulation.demande.v1"
EVENEMENT_REPONSE = "politique.simulation.reponse.v1"


class ExtensionSimulateurPolitique:
    """Extension conforme au Protocole ÉVA v4.2.3."""

    def __init__(self, extension_id: str):
        if not extension_id:
            raise ValueError("extension_id obligatoire : le superviseur l'injecte (§4).")
        self.extension_id = extension_id
        self._initialized = False
        self.pid = None

    async def install(self) -> bool:
        """Installation idempotente (aucune dépendance externe requise)."""
        return True

    async def start(self) -> None:
        """Démarrage et souscription sur le bus d'ÉVA."""
        self.pid = os.getpid()
        EventBus.subscribe(
            EVENEMENT_DEMANDE,
            self.on_event,
            extension_id=self.extension_id,
        )
        self._initialized = True

    async def stop(self) -> None:
        """Arrêt propre de l'extension."""
        self._initialized = False

    async def health_check(self) -> dict:
        """Vérification de l'état de santé du simulateur."""
        if not self._initialized:
            return {"status": "degraded", "message": "Simulateur non initialisé"}
        return {"status": "healthy", "pid": self.pid, "modele": "Gigogne 4 échelons (FR/UE/Monde)"}

    def on_event(self, donnees: dict) -> dict:
        """
        Traite une demande de simulation soumise par ÉVA.
        Format d'entrée attendu :
        {
            "scenario": "mandature" | "statut_quo" | "austerite",
            "annee_cible": 5 (optionnel, 1-5)
        }
        """
        scenario = donnees.get("scenario", "mandature")
        annee_cible = int(donnees.get("annee_cible", 5))

        resultats = self._executer_simulation(scenario)
        reponse = {
            "source": self.extension_id,
            "scenario": scenario,
            "annee_cible": annee_cible,
            "resultats_trajectoire": resultats,
            "synthese_annee_cible": resultats[min(annee_cible, len(resultats)) - 1],
        }

        # Publication de la réponse sur le bus ÉVA
        rapport = EventBus.publier(EVENEMENT_REPONSE, reponse)
        return {"publie": True, "destinataires": rapport.get("destinataires", 0), "reponse": reponse}

    def _executer_simulation(self, scenario: str) -> List[Dict[str, Any]]:
        """Moteur de calcul des 4 échelons (Local, National, Europe, Monde)."""
        from simulateur.moteur import MoteurSimulationSystemique
        from simulateur.scenarios import (
            get_scenario_mandature_5_ans,
            get_scenario_statut_quo,
            get_scenario_austerite_brutale,
            get_scenario_choc_mondial_stagflation,
        )

        moteur = MoteurSimulationSystemique()
        if scenario == "mandature":
            decisions = get_scenario_mandature_5_ans()
        elif scenario == "austerite":
            decisions = get_scenario_austerite_brutale()
        elif scenario == "choc_mondial":
            decisions = get_scenario_choc_mondial_stagflation()
        else:
            decisions = get_scenario_statut_quo()

        historique = []
        for dec in decisions:
            res = moteur.appliquer_etape(dec)
            historique.append({
                "annee": res.annee,
                "pib_nominal_mde": res.pib_nominal_mde,
                "deficit_mde": res.deficit_nominal_mde,
                "ratio_deficit_pib": res.ratio_deficit_pib,
                "dette_mde": res.dette_nominale_mde,
                "ratio_dette_pib": res.ratio_dette_pib,
                "charge_dette_mde": res.charge_dette_mde,
                "recettes_publiques_totales_mde": res.recettes_publiques_totales_mde,
                "depenses_publiques_totales_mde": res.depenses_publiques_totales_mde,
                "pouvoir_achat_index": res.pouvoir_achat_index,
                "confiance_democratique": res.confiance_democratique,
                "risque_censure_parlement": res.risque_censure_parlement,
                "tension_sociale": res.tension_sociale_locale,
                "qualite_services_proximite": res.qualite_services_proximite,
                "produit_taxe_fonciere_mde": res.produit_taxe_fonciere_mde,
                "pde_europe_conforme": not res.statut_pde_europe,
                "bouclier_tpi_actif": res.bouclier_tpi_actif,
                "taux_oat_pct": res.taux_oat_pct,
                "spread_bund_bps": res.spread_bund_bps,
                "note_souveraine": res.note_souveraine,
                "taux_credit_pme": res.taux_credit_pme,
                "cours_petrole_usd": res.cours_petrole_usd,
                "taux_change_eur_usd": res.taux_change_eur_usd,
                "facture_energetique_mde": res.facture_energetique_mde,
                "inflation_globale_pct": res.inflation_globale_pct,
                "commentaires": res.commentaires,
            })

        return historique
