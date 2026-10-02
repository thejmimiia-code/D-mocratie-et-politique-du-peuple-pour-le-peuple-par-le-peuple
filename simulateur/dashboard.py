#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simulateur/dashboard.py — Dashboard web interactif pour le Simulateur Macro-Politique.

Serveur HTTP léger (bibliothèque standard uniquement) offrant une interface
visuelle pour faire tourner le simulateur en direct, visualiser la cascade
des 4 strates, et exporter les résultats.

Usage :
    python -m simulateur.dashboard [--host 0.0.0.0] [--port 8080]
    python3 -m simulateur.dashboard
"""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from simulateur.moteur import MoteurSimulationSystemique
from simulateur.scenarios import (
    get_scenario_mandature_5_ans,
    get_scenario_statut_quo,
    get_scenario_austerite_brutale,
    get_scenario_choc_mondial_stagflation,
)
from simulateur.cli import export_scenario

# ─── Catalogue des scénarios ──────────────────────────────────────────────────

SCENARIOS: Dict[str, Dict[str, Any]] = {
    "mandature": {
        "nom": "Plan de Mandature Républicaine",
        "description": "Réformes structurelles +60 Md€/an en Année 5. Déficit < 3% PIB.",
        "couleur": "#22c55e",
        "fn": get_scenario_mandature_5_ans,
    },
    "statut_quo": {
        "nom": "Statut Quo",
        "description": "Immobilisme politique et dérive financière budgétaire.",
        "couleur": "#f59e0b",
        "fn": get_scenario_statut_quo,
    },
    "austerite": {
        "nom": "Austérité Brute",
        "description": "Coupes territoriales et fronde fiscale. Tension sociale élevée.",
        "couleur": "#ef4444",
        "fn": get_scenario_austerite_brutale,
    },
    "choc_mondial": {
        "nom": "Choc Mondial (Stagflation)",
        "description": "Chocs exogènes : pétrole +30$, Fed +75 bps, EUR déprécié.",
        "couleur": "#8b5cf6",
        "fn": get_scenario_choc_mondial_stagflation,
    },
}


# ─── HTML Templates ──────────────────────────────────────────────────────────

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simulateur Macro-Politique — Dashboard</title>
    <style>
        :root {
            --bg: #0f172a;
            --card: #1e293b;
            --card-hover: #334159;
            --text: #e2e8f0;
            --text-dim: #94a3b8;
            --accent: #38bdf8;
            --green: #22c55e;
            --red: #ef4444;
            --amber: #f59e0b;
            --purple: #8b5cf6;
            --border: #334159;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            text-align: center; margin-bottom: 30px; padding: 20px;
            background: linear-gradient(135deg, #1e3a8a, #3730a3);
            border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }
        .header h1 { font-size: 1.8rem; margin-bottom: 5px; }
        .header p { color: var(--text-dim); font-size: 0.9rem; }
        .strates-cascade {
            display: flex; flex-direction: column; gap: 8px;
            margin: 30px 0; position: relative;
        }
        .strate {
            background: var(--card); border: 2px solid var(--border);
            border-radius: 10px; padding: 18px;
            transition: all 0.3s ease; cursor: pointer;
        }
        .strate:hover { border-color: var(--accent); transform: translateY(-2px); }
        .strate .strate-title {
            display: flex; align-items: center; gap: 10px;
            font-size: 1.1rem; font-weight: 700; margin-bottom: 8px;
        }
        .strate-badge {
            display: inline-block; width: 28px; height: 28px;
            border-radius: 50%; text-align: center;
            line-height: 28px; font-weight: 700; font-size: 0.85rem;
        }
        .strate-1 { background: rgba(34,197,94,0.15); border-color: var(--green); }
        .strate-1 .strate-badge { background: var(--green); color: #0f172a; }
        .strate-2 { background: rgba(56,189,248,0.15); border-color: var(--accent); }
        .strate-2 .strate-badge { background: var(--accent); color: #0f172a; }
        .strate-3 { background: rgba(139,92,246,0.15); border-color: var(--purple); }
        .strate-3 .strate-badge { background: var(--purple); color: #fff; }
        .strate-4 { background: rgba(245,158,11,0.15); border-color: var(--amber); }
        .strate-4 .strate-badge { background: var(--amber); color: #0f172a; }
        .strates-arrow {
            text-align: center; color: var(--text-dim);
            font-size: 1.5rem; padding: 0 20px;
        }
        .grid-metrics {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px; margin: 20px 0;
        }
        .metric-card {
            background: var(--card); border-radius: 10px; padding: 18px;
            text-align: center; border: 1px solid var(--border);
        }
        .metric-card .label {
            color: var(--text-dim); font-size: 0.75rem;
            text-transform: uppercase; letter-spacing: 1px;
        }
        .metric-card .value { font-size: 1.6rem; font-weight: 800; }
        .metric-card .unit { font-size: 0.85rem; color: var(--text-dim); }
        .status-badge {
            display: inline-block; padding: 3px 10px; border-radius: 20px;
            font-size: 0.75rem; font-weight: 600;
        }
        .status-conforme { background: rgba(34,197,94,0.2); color: var(--green); }
        .status-alerte { background: rgba(239,68,68,0.2); color: var(--red); }
        .scenario-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 15px; margin: 20px 0;
        }
        .scenario-card {
            background: var(--card); border: 2px solid var(--border);
            border-radius: 10px; padding: 18px; cursor: pointer;
            transition: all 0.3s ease;
        }
        .scenario-card:hover {
            border-color: var(--accent); transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }
        .scenario-card.selected { border-color: var(--accent); }
        .scenario-card .scenario-name {
            font-size: 1.1rem; font-weight: 700; margin-bottom: 6px; display: flex;
            align-items: center; gap: 8px;
        }
        .scenario-card .scenario-desc {
            color: var(--text-dim); font-size: 0.85rem; line-height: 1.4;
        }
        .btn {
            background: var(--accent); color: #0f172a; border: none;
            padding: 10px 24px; border-radius: 8px; font-size: 0.9rem;
            font-weight: 700; cursor: pointer; transition: all 0.2s;
            margin-right: 8px;
        }
        .btn:hover { background: #7dd3fc; transform: scale(1.03); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .btn-json { background: #22c55e; color: #0f172a; }
        .btn-csv { background: #f59e0b; color: #0f172a; }
        .btn-json:hover { background: #4ade80; }
        .btn-csv:hover { background: #fbbf24; }
        .btn:active { transform: scale(0.97); }
        .results-table {
            width: 100%; border-collapse: collapse; margin: 15px 0;
            font-size: 0.85rem;
        }
        .results-table th {
            background: var(--card-hover); padding: 10px 12px;
            text-align: left; color: var(--text-dim);
            font-weight: 600; text-transform: uppercase;
            font-size: 0.72rem; letter-spacing: 0.5px;
        }
        .results-table td {
            padding: 8px 12px; border-bottom: 1px solid var(--border);
        }
        .results-table tr:hover { background: rgba(255,255,255,0.02); }
        .chart-container {
            background: var(--card); border-radius: 10px;
            padding: 20px; margin: 15px 0; border: 1px solid var(--border);
        }
        .chart-title {
            font-size: 0.95rem; font-weight: 600;
            margin-bottom: 12px; color: var(--text-dim);
        }
        .svg-chart { width: 100%; height: 160px; }
        .bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
        .bar-label { width: 100px; font-size: 0.8rem; color: var(--text-dim); text-align: right; }
        .bar-track { flex: 1; height: 18px; background: #334159; border-radius: 9px; overflow: hidden; }
        .bar-fill { height: 100%; border-radius: 9px; transition: width 0.5s ease; }
        .bar-value { width: 80px; font-size: 0.8rem; font-weight: 600; }
        .commentaires {
            margin-top: 15px; padding: 12px; background: #0f172a;
            border-radius: 8px; border-left: 3px solid var(--accent);
        }
        .commentaires ul { list-style: none; }
        .commentaires li {
            padding: 4px 0; color: var(--text-dim); font-size: 0.82rem;
            border-bottom: 1px solid rgba(255,255,255,0.03);
        }
        .commentaires li:before {
            content: "▸ "; color: var(--accent);
        }
        .hidden { display: none; }
        .loading {
            text-align: center; padding: 40px; color: var(--text-dim);
        }
        .action-bar {
            display: flex; justify-content: space-between;
            align-items: center; margin: 20px 0;
        }
        .action-bar h2 { font-size: 1.1rem; }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>Simulateur Macro-Politique Systémique</h1>
        <p>Modèle gigogne à 4 échelons — Local → National → Europe → Mondial</p>
    </div>

    <div class="strates-cascade">
        <div class="strate strate-1">
            <div class="strate-title">
                <span class="strate-badge">1</span>
                ÉCHELON LOCAL — Collectivités Territoriales
            </div>
            <p style="color:var(--text-dim);font-size:0.85rem;">
                Communes, Départements, Régions — Règle d'or budgétaire (CGCT L.1612-4).
                Tension sociale et qualité des services de proximité.
            </p>
        </div>
        <div class="strates-arrow">↓ Taux d'intérêt & Refinancement de la dette</div>
        <div class="strate strate-2">
            <div class="strate-title">
                <span class="strate-badge">2</span>
                ÉCHELON NATIONAL — État, Sécurité Sociale, Parlement
            </div>
            <p style="color:var(--text-dim);font-size:0.85rem;">
                PIB 3 015 Md€, Déficit, Dette (3 568 Md€ / 119% PIB),
                Pouvoir d'achat, Confiance démocratique.
            </p>
        </div>
        <div class="strates-arrow">↓ Contrainte de déficit excessif (PDE)</div>
        <div class="strate strate-3">
            <div class="strate-title">
                <span class="strate-badge">3</span>
                ÉCHELON CONTINENTAL — Union Européenne, Zone Euro, BCE
            </div>
            <p style="color:var(--text-dim);font-size:0.85rem;">
                Procédure Déficit Excessif (< 3% PIB), Spread Bund/OAT,
                Bouclier TPI de la BCE.
            </p>
        </div>
        <div class="strates-arrow">↓ Marchés financiers internationaux</div>
        <div class="strate strate-4">
            <div class="strate-title">
                <span class="strate-badge">4</span>
                ÉCHELON MONDIAL — Marchés obligataires, Taux, Change, Pétrole
            </div>
            <p style="color:var(--text-dim);font-size:0.85rem;">
                Taux OAT 10 ans, Spread Bund, Notation souveraine,
                Taux de crédit PME, Pétrole Brent, EUR/USD.
            </p>
        </div>
    </div>

    <div class="action-bar">
        <h2>Sélectionnez un scénario</h2>
        <div>
            <button class="btn btn-json" onclick="runAndExport('json')" disabled id="btn-export-json">Exporter JSON</button>
            <button class="btn btn-csv" onclick="runAndExport('csv')" disabled id="btn-export-csv">Exporter CSV</button>
        </div>
    </div>

    <div class="scenario-grid" id="scenario-grid"></div>

    <div id="results-area">
        <div class="loading">Sélectionnez un scénario pour commencer la simulation.</div>
    </div>
</div>

<script>
const SCENARIOS = ===SCENARIOS_JSON===;

let currentScenario = null;
let currentResults = null;

// Rend la grille de scénarios
function renderScenarios() {
    const grid = document.getElementById('scenario-grid');
    grid.innerHTML = '';
    Object.entries(SCENARIOS).forEach(([key, info]) => {
        const card = document.createElement('div');
        card.className = 'scenario-card';
        card.innerHTML = `
            <div class="scenario-name">
                <span class="dot" style="background:${info.couleur}"></span>
                ${info.nom}
            </div>
            <div class="scenario-desc">${info.description}</div>
        `;
        card.onclick = () => runScenario(key);
    });
}

// Lance une simulation
async function runScenario(scenario) {
    currentScenario = scenario;
    const card = event?.target?.closest?.('.scenario-card');
    if (card) {
        document.querySelectorAll('.scenario-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
    }
    document.getElementById('results-area').innerHTML = '<div class="loading">Simulation en cours…</div>';

    try {
        const resp = await fetch(`/api/run?scenario=${scenario}`);
        const data = await resp.json();
        if (data.error) throw new Error(data.error);
        currentResults = data.resultats;
        renderResults(data);
    } catch(e) {
        document.getElementById('results-area').innerHTML =
            `<div class="loading">Erreur : ${e.message}</div>`;
        console.error(e);
    }
}

// Exécute et exporte
function runAndExport(format) {
    if (!currentScenario) return;
    const url = `/api/export?scenario=${currentScenario}&format=${format}`;
    window.open(url, '_blank');
}

// Rendu des résultats
function renderResults(data) {
    const resultats = data.resultats;
    const info = SCENARIOS[currentScenario];

    let html = '';

    // Métriques clés (Année 5)
    const last = resultats[resultats.length - 1];
    const pdeStatus = last.statut_pde_europe ? 'ALERTE' : 'CONFORME';
    const pdeClass = last.statut_pde_europe ? 'status-alerte' : 'status-conforme';
    const tpiClass = last.bouclier_tpi_actif ? 'status-conforme' : 'status-alerte';

    html += `<div class="grid-metrics">
        <div class="metric-card"><div class="label">Déficit à l'An 5</div>
            <div><span class="value">${last.ratio_deficit_pib.toFixed(2)}</span><span class="unit">% PIB</span></div></div>
        <div class="metric-card"><div class="label">Taux OAT 10a</div>
            <div><span class="value">${last.taux_oat_pct.toFixed(2)}</span><span class="unit">%</span></div></div>
        <div class="metric-card"><div class="label">Tension Sociale</div>
            <div><span class="value">${last.tension_sociale_locale.toFixed(1)}</span><span class="unit">/100</span></div></div>
        <div class="metric-card"><div class="label">Confiance Démocratique</div>
            <div><span class="value">${last.confiance_democratique.toFixed(1)}</span><span class="unit">/100</span></div></div>
        <div class="metric-card"><div class="label">Note Souveraine</div>
            <div><span class="value">${last.note_souveraine}</span></div></div>
        <div class="metric-card"><div class="label">PDE UE</div>
            <div><span class="status-badge ${pdeClass}">${pdeStatus}</span></div></div>
        <div class="metric-card"><div class="label">Bouclier TPI BCE</div>
            <div><span class="status-badge ${tpiClass}">${last.bouclier_tpi_actif ? 'Actif' : 'Suspendu'}</span></div></div>
        <div class="metric-card"><div class="label">Pouvoir d'Achat</div>
            <div><span class="value">${last.pouvoir_achat_index.toFixed(1)}</span><span class="unit"> (base 100)</span></div></div>
    </div>`;

    // Graphique : Déficit & Taux OAT par an
    const maxDef = Math.max(...resultats.map(r => r.deficit_nominal_mde));
    const maxOat = Math.max(...resultats.map(r => r.taux_oat_pct));
    html += `<div class="chart-container">
        <div class="chart-title">Évolution budgétaire & taux d'intérêt (5 ans)</div>`;
    resultats.forEach(r => {
        const deficitPct = (r.deficit_nominal_mde / maxDef) * 100;
        const oatPct = (r.taux_oat_pct / maxOat) * 100;
        html += `<div class="bar-row">
            <div class="bar-label">An ${r.annee} Déficit</div>
            <div class="bar-track"><div class="bar-fill" style="width:${deficitPct}%;background:${info.couleur}"></div></div>
            <div class="bar-value">${r.deficit_nominal_mde.toFixed(1)} Md€</div>
        </div>
        <div class="bar-row" style="margin-bottom:2px">
            <div class="bar-label" style="width:120px">Taux OAT</div>
            <div class="bar-track"><div class="bar-fill" style="width:${oatPct}%;background:#38bdf8"></div></div>
            <div class="bar-value">${r.taux_oat_pct.toFixed(2)}%</div>
        </div>`;
    });
    html += '</div>';

    // Tension sociale
    const maxTension = Math.max(...resultats.map(r => r.tension_sociale_locale));
    html += `<div class="chart-container">
        <div class="chart-title">Tension sociale territoriale & Confiance démocratique</div>`;
    resultats.forEach(r => {
        const tPct = (r.tension_sociale_locale / Math.max(maxTension, 1)) * 100;
        const cPct = (r.confiance_democratique / 100) * 100;
        html += `<div class="bar-row">
            <div class="bar-label">An ${r.annee} Tension</div>
            <div class="bar-track"><div class="bar-fill" style="width:${tPct}%;background:${r.tension_sociale_locale > 30 ? '#ef4444' : '#22c55e'}"></div></div>
            <div class="bar-value">${r.tension_sociale_locale.toFixed(1)}</div>
        </div>
        <div class="bar-row" style="margin-bottom:2px">
            <div class="bar-label" style="width:120px">Confiance</div>
            <div class="bar-track"><div class="bar-fill" style="width:${cPct}%;background:#22c55e"></div></div>
            <div class="bar-value">${r.confiance_democratique.toFixed(1)}</div>
        </div>`;
    });
    html += '</div>';

    // Tableau détaillé
    html += `<table class="results-table">
        <thead><tr>
            <th>An</th><th>Déficit</th><th>Déf/PIB</th><th>Dette/PIB</th>
            <th>OAT</th><th>Spread</th><th>Tension</th><th>Confiance</th>
            <th>PDE</th><th>Note</th><th>Pouvoir</th>
        </tr></thead><tbody>`;
    resultats.forEach(r => {
        const pdeStr = r.statut_pde_europe ? 'ALERTE' : 'CONFORME';
        const pdeCls = r.statut_pde_europe ? 'status-alerte' : 'status-conforme';
        html += `<tr>
            <td>${r.annee}</td>
            <td>${r.deficit_nominal_mde.toFixed(1)} Md€</td>
            <td>${r.ratio_deficit_pib.toFixed(2)}%</td>
            <td>${r.ratio_dette_pib.toFixed(1)}%</td>
            <td>${r.taux_oat_pct.toFixed(2)}%</td>
            <td>${r.spread_bund_bps.toFixed(1)} bp</td>
            <td>${r.tension_sociale_locale.toFixed(1)}</td>
            <td>${r.confiance_democratique.toFixed(1)}</td>
            <td><span class="status-badge ${pdeCls}">${pdeStr}</span></td>
            <td>${r.note_souveraine}</td>
            <td>${r.pouvoir_achat_index.toFixed(1)}</td>
        </tr>`;
    });
    html += '</tbody></table>';

    // Analyse détaillée de l'année finale
    html += `<div class="commentaires">
        <div class="chart-title">Journal des événements — Année ${last.annee}</div>
        <ul>`;
    (last.commentaires || []).forEach(comm => {
        html += `<li>${comm}</li>`;
    });
    if (!last.commentaires || !last.commentaires.length) {
        html += `<li>Aucun événement à signaler.</li>`;
    }
    html += `</ul></div>`;

    // Enable export buttons
    document.getElementById('btn-export-json').disabled = false;
    document.getElementById('btn-export-csv').disabled = false;

    document.getElementById('results-area').innerHTML = html;
}

// Init
renderScenarios();
</script>
</body>
</html>
"""


# ─── API Responses ───────────────────────────────────────────────────────────

def run_simulation_api(scenario: str) -> Dict[str, Any]:
    """Exécute une simulation et retourne les résultats en format API."""
    if scenario not in SCENARIOS:
        return {"error": f"Scénario inconnu : {scenario}"}

    moteur = MoteurSimulationSystemique()
    decisions = SCENARIOS[scenario]["fn"]()

    for dec in decisions:
        moteur.appliquer_etape(dec)

    resultats = []
    for r in moteur.historique_etapes:
        resultats.append({
            "annee": r.annee,
            "pib_nominal_mde": round(r.pib_nominal_mde, 2),
            "deficit_nominal_mde": round(r.deficit_nominal_mde, 2),
            "ratio_deficit_pib": round(r.ratio_deficit_pib, 2),
            "dette_nominale_mde": round(r.dette_nominale_mde, 2),
            "ratio_dette_pib": round(r.ratio_dette_pib, 2),
            "charge_dette_mde": round(r.charge_dette_mde, 2),
            "recettes_publiques_totales_mde": round(r.recettes_publiques_totales_mde, 2),
            "depenses_publiques_totales_mde": round(r.depenses_publiques_totales_mde, 2),
            "pouvoir_achat_index": round(r.pouvoir_achat_index, 2),
            "confiance_democratique": round(r.confiance_democratique, 2),
            "risque_censure_parlement": round(r.risque_censure_parlement, 2),
            "tension_sociale_locale": round(r.tension_sociale_locale, 2),
            "qualite_services_proximite": round(r.qualite_services_proximite, 2),
            "produit_taxe_fonciere_mde": round(r.produit_taxe_fonciere_mde, 2),
            "statut_pde_europe": r.statut_pde_europe,
            "bouclier_tpi_actif": r.bouclier_tpi_actif,
            "sanction_financiere_ue": r.sanction_financiere_ue,
            "taux_oat_pct": round(r.taux_oat_pct, 2),
            "spread_bund_bps": round(r.spread_bund_bps, 2),
            "note_souveraine": r.note_souveraine,
            "taux_credit_pme": round(r.taux_credit_pme, 2),
            "cours_petrole_usd": round(r.cours_petrole_usd, 2),
            "taux_change_eur_usd": round(r.taux_change_eur_usd, 3),
            "facture_energetique_mde": round(r.facture_energetique_mde, 2),
            "inflation_globale_pct": round(r.inflation_globale_pct, 2),
            "commentaires": r.commentaires,
        })

    return {
        "scenario": scenario,
        "nom": SCENARIOS[scenario]["nom"],
        "resultats": resultats,
    }


# ─── HTTP Handler ────────────────────────────────────────────────────────────

class DashboardHandler(BaseHTTPRequestHandler):
    """Handler HTTP pour le dashboard web."""

    def log_message(self, format: str, *args) -> None:
        """Silence les logs serveur pour une sortie propre."""
        pass

    def _send_html(self, content: str) -> None:
        body = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data: Dict[str, Any]) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: str) -> None:
        if not os.path.exists(path):
            self.send_response(404)
            self.end_headers()
            return
        with open(path, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Disposition", f'attachment; filename="{os.path.basename(path)}"')
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/" or path == "":
            scenarios_json = json.dumps(
                {k: v for k, v in SCENARIOS.items()},
                ensure_ascii=False,
            )
            html = HTML_PAGE.replace('===SCENARIOS_JSON===', scenarios_json)
            self._send_html(html)

        elif path == "/api/run":
            scenario = query.get("scenario", ["mandature"])[0]
            try:
                result = run_simulation_api(scenario)
                self._send_json(result)
            except Exception as e:
                self._send_json({"error": str(e), "traceback": traceback.format_exc()})

        elif path == "/api/scenarios":
            self._send_json({
                "scenarios": {
                    k: {
                        "nom": v["nom"],
                        "description": v["description"],
                        "couleur": v["couleur"],
                    }
                    for k, v in SCENARIOS.items()
                }
            })

        elif path == "/api/export":
            scenario = query.get("scenario", ["mandature"])[0]
            fmt = query.get("format", ["json"])[0]
            try:
                result = run_simulation_api(scenario)
                if "error" in result:
                    self._send_json(result)
                    return
                # Génère le fichier export
                fname = f"{scenario}_simulateur.{fmt}"
                fpath = os.path.join(os.getcwd(), fname)
                if fmt == "json":
                    payload = {
                        "scenario": scenario,
                        "nom": SCENARIOS[scenario]["nom"],
                        "modele": "Gigogne 4 échelons",
                        "resultats": result["resultats"],
                    }
                    with open(fpath, "w", encoding="utf-8") as f:
                        json.dump(payload, f, ensure_ascii=False, indent=2)
                elif fmt == "csv":
                    import csv as csv_mod
                    fieldnames = list(result["resultats"][0].keys())
                    with open(fpath, "w", newline="", encoding="utf-8") as f:
                        writer = csv_mod.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                        writer.writeheader()
                        for r in result["resultats"]:
                            if isinstance(r.get("commentaires"), list):
                                r["commentaires"] = "; ".join(r["commentaires"])
                            writer.writerow(r)
                else:
                    self._send_json({"error": "Format non supporté. Utilisez json ou csv."})
                    return
                self._send_file(fpath)
                os.remove(fpath)
            except Exception as e:
                self._send_json({"error": str(e), "traceback": traceback.format_exc()})

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        self.send_response(405)
        self.end_headers()


# ─── Server ──────────────────────────────────────────────────────────────────

def create_server(host: str = "0.0.0.0", port: int = 8080) -> HTTPServer:
    """Crée le serveur HTTP du dashboard."""
    server = HTTPServer((host, port), DashboardHandler)
    return server


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dashboard web du Simulateur Macro-Politique Systémique"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Adresse d'écoute (défaut: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port d'écoute (défaut: 8080)")
    args = parser.parse_args()

    server = create_server(args.host, args.port)
    print(f"  Dashboard lancé : http://{args.host}:{args.port}")
    print(f"  Scénarios : {', '.join(SCENARIOS.keys())}")
    print(f"  Appuyez sur Ctrl+C pour arrêter.")
    print(f"  {'=' * 60}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Arrêt du dashboard.")
        server.shutdown()


if __name__ == "__main__":
    main()
