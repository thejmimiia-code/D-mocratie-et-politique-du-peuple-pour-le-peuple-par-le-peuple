#!/usr/bin/env python3
"""
benchmarks/benchmark.py — Benchmark de performance du simulateur.

Mesure la latence par étape, le débit (It/s), et l'usage mémoire.
Utilise uniquement la bibliothèque standard (aucune dépendance externe).
"""

from __future__ import annotations

import gc
import json
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any

# Ajout de la racine au PYTHONPATH
RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from simulateur.moteur import MoteurSimulationSystemique  # noqa: E402
from simulateur.scenarios import (  # noqa: E402
    get_scenario_austerite_brutale,
    get_scenario_choc_mondial_stagflation,
    get_scenario_convergence_ww3,
    get_scenario_crise_taiwan,
    get_scenario_escalade_nucleaire_tactique,
    get_scenario_fermeture_hormuz,
    get_scenario_mandature_5_ans,
    get_scenario_resilience_republicaine,
    get_scenario_statut_quo,
)

SCENARIOS: list[tuple[str, callable]] = [
    ("mandature", get_scenario_mandature_5_ans),
    ("statut_quo", get_scenario_statut_quo),
    ("austerite", get_scenario_austerite_brutale),
    ("choc_mondial", get_scenario_choc_mondial_stagflation),
    ("crise_taiwan", get_scenario_crise_taiwan),
    ("hormuz", get_scenario_fermeture_hormuz),
    ("escalade_nucleaire", get_scenario_escalade_nucleaire_tactique),
    ("convergence_ww3", get_scenario_convergence_ww3),
    ("resilience", get_scenario_resilience_republicaine),
]


def benchmark_scenario(nom: str, scenario_fn: callable) -> dict[str, Any]:
    """Benchmark un scénario : latence, débit, mémoire."""
    gc.collect()
    tracemalloc.start()

    moteur = MoteurSimulationSystemique()
    decisions = scenario_fn()

    start = time.perf_counter()
    for dec in decisions:
        moteur.appliquer_etape(dec)
    elapsed = time.perf_counter() - start

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    nb_etapes = len(moteur.historique_etapes)
    return {
        "scenario": nom,
        "etapes": nb_etapes,
        "temps_total_s": round(elapsed, 4),
        "temps_par_etape_ms": round((elapsed / nb_etapes) * 1000, 3),
        "debit_it_s": round(nb_etapes / elapsed, 1) if elapsed > 0 else 0,
        "memoire_peak_kb": round(peak / 1024, 1),
    }


def benchmark_reproductibilite(nom: str, scenario_fn: callable, iterations: int = 10) -> dict[str, Any]:
    """Vérifie que N exécutions produisent des résultats identiques (déterminisme)."""
    results = []
    for _ in range(iterations):
        moteur = MoteurSimulationSystemique()
        for dec in scenario_fn():
            moteur.appliquer_etape(dec)
        dernier = moteur.historique_etapes[-1]
        results.append((dernier.ratio_deficit_pib, dernier.taux_oat_pct, dernier.tension_sociale_locale))

    unique = set(results)
    return {
        "scenario": nom,
        "iterations": iterations,
        "resultats_identiques": len(unique) == 1,
        "valeurs_uniques": len(unique),
    }


def main() -> None:
    print("=" * 70)
    print("   BENCHMARK : Simulateur Macro-Politique Systémique")
    print("=" * 70)

    all_results: list[dict[str, Any]] = []

    for nom, fn in SCENARIOS:
        r = benchmark_scenario(nom, fn)
        all_results.append(r)
        print(f"\n[{nom}]")
        print(f"  Étapes         : {r['etapes']}")
        print(f"  Temps total    : {r['temps_total_s']:.4f} s")
        print(f"  Temps/étape    : {r['temps_par_etape_ms']:.3f} ms")
        print(f"  Débit          : {r['debit_it_s']:.1f} it/s")
        print(f"  Mémoire pic    : {r['memoire_peak_kb']:.1f} KB")

    print("\n" + "=" * 70)
    print("   TEST DE RÉPRODUCTIBILITÉ (déterminisme)")
    print("=" * 70)

    for nom, fn in SCENARIOS:
        rep = benchmark_reproductibilite(nom, fn, iterations=10)
        status = "OK ✅" if rep["resultats_identiques"] else "FAIL ❌"
        print(f"\n[{nom}] {rep['iterations']} itérations → {status} (valeurs uniques: {rep['valeurs_uniques']})")

    # Export du rapport de benchmark
    report = {
        "benchmark": "simulateur-macro-politique",
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "resultats": all_results,
    }
    out_path = RACINE / "benchmarks" / "benchmark_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n>>> Rapport de benchmark : {out_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
