"""
simulateur/cli.py — Interface terminale pour le simulateur multi-strates (Local, National, Europe, Marchés).
"""

import csv
import json
import sys
from dataclasses import asdict, fields
from pathlib import Path

from simulateur.model import (
    ResultatEtapeSimulation,
)
from simulateur.moteur import MoteurSimulationSystemique
from simulateur.scenarios import (
    get_scenario_austerite_brutale,
    get_scenario_choc_mondial_stagflation,
    get_scenario_mandature_5_ans,
    get_scenario_statut_quo,
)


def afficher_banniere() -> None:
    print("=" * 105)
    print("   SIMULATEUR MACRO-POLITIQUE SYSTÉMIQUE : DYNAMIQUE DES 4 STRATES INTERCONNECTÉES   ")
    print("    [1. Local / Collectivités] -> [2. National / État] -> [3. Europe / PDE] -> [4. Mondial / Marchés]    ")
    print("=" * 105)


def afficher_tableau_resultats(titre: str, resultats: list[ResultatEtapeSimulation]) -> None:
    print(f"\n>>> RÉSULTATS DE LA SIMULATION : {titre}")
    print("-" * 115)
    header = (
        f"{'An':<3} | {'Déficit':<10} | {'Déf/PIB':<8} | {'Dette/PIB':<10} | "
        f"{'OAT 10a':<8} | {'Spread':<8} | {'Tension':<8} | {'Confiance':<10} | {'PDE UE':<8} | {'Note':<5}"
    )
    print(header)
    print("-" * 115)

    for r in resultats:
        pde_str = "ALERTE" if r.statut_pde_europe else "CONFORME"
        ligne = (
            f"An {r.annee:<1} | {r.deficit_nominal_mde:>6.1f} Md€ | {r.ratio_deficit_pib:>6.2f} % | {r.ratio_dette_pib:>7.1f} % | "
            f"{r.taux_oat_pct:>6.2f} % | {r.spread_bund_bps:>5.1f} bp | {r.tension_sociale_locale:>6.1f}/100| {r.confiance_democratique:>7.1f}/100 | {pde_str:<8} | {r.note_souveraine:<5}"
        )
        print(ligne)
    print("-" * 115)


def afficher_detail_annee(r: ResultatEtapeSimulation) -> None:
    print(f"\n====================== ANALYSE DÉTAILLÉE : ANNÉE {r.annee} ======================")
    print("1. STRATE LOCALE (Collectivités territoriales & Baromètre civique) :")
    print(f"   * Tension sociale territoriale : {r.tension_sociale_locale:.1f} / 100")
    print(f"   * Qualité des services publics : {r.qualite_services_proximite:.1f} / 100")
    print(f"   * Produit de la taxe foncière  : {r.produit_taxe_fonciere_mde:.2f} Md€")

    print("\n2. STRATE NATIONALE (État, Sécurité Sociale & Parlement) :")
    print(f"   * PIB nominal                  : {r.pib_nominal_mde:.1f} Md€")
    print(f"   * Déficit public consolidé     : {r.deficit_nominal_mde:.2f} Md€ ({r.ratio_deficit_pib:.2f} % du PIB)")
    print(f"   * Dette publique (Maastricht)  : {r.dette_nominale_mde:.2f} Md€ ({r.ratio_dette_pib:.2f} % du PIB)")
    print(f"   * Charge de la dette nette     : {r.charge_dette_mde:.2f} Md€/an")
    print(f"   * Pouvoir d'achat des ménages  : indice {r.pouvoir_achat_index:.1f} (base 100)")
    print(f"   * Confiance démocratique       : {r.confiance_democratique:.1f} / 100")
    print(f"   * Risque de motion de censure  : {r.risque_censure_parlement:.1f} %")

    print("\n3. STRATE CONTINENTALE (Union Européenne & Zone Euro) :")
    print(f"   * Statut Procédure Déficit (PDE): {'ACTIF (Surveillance)' if r.statut_pde_europe else 'CONFORME (< 3 % PIB)'}")
    print(f"   * Bouclier TPI de la BCE        : {'ÉLIGIBLE (Protection anti-spéculation active)' if r.bouclier_tpi_actif else 'SUSPENDU (Discipline non respectée)'}")

    print("\n4. STRATE MONDIALE (Marchés Financiers Internationaux & Économie réelle) :")
    print(f"   * Taux OAT souverain à 10 ans   : {r.taux_oat_pct:.2f} % (Spread face au Bund : {r.spread_bund_bps:.1f} bps)")
    print(f"   * Notation souveraine           : {r.note_souveraine}")
    print(f"   * Taux de crédit aux PME        : {r.taux_credit_pme:.2f} %")
    print(f"   * Pétrole Brent mondial         : {r.cours_petrole_usd:.1f} $/baril (Change EUR/USD : {r.taux_change_eur_usd:.3f})")
    print(f"   * Facture énergétique nette     : {r.facture_energetique_mde:.1f} Md€/an (Inflation IPC : {r.inflation_globale_pct:.2f} %)")

    print("\n5. JOURNAL DES ÉVÉNEMENTS & RÉTROACTIONS :")
    for comm in r.commentaires:
        print(f"   - {comm}")
    print("=" * 76)


def executer_scenario(
    nom_scenario: str,
    export_path: str | None = None,
) -> list[ResultatEtapeSimulation]:
    moteur = MoteurSimulationSystemique()

    if nom_scenario == "mandature":
        decisions = get_scenario_mandature_5_ans()
        titre = "PLAN DE MANDATURE RÉPUBLICAIN (+60 Md€ en Année 5)"
    elif nom_scenario == "statut_quo":
        decisions = get_scenario_statut_quo()
        titre = "STATUT QUO (Immobilisme politique et inertie)"
    elif nom_scenario == "austerite":
        decisions = get_scenario_austerite_brutale()
        titre = "AUSTÉRITÉ AVEUGLE (Coupes territoriales et fronde fiscale)"
    elif nom_scenario == "choc_mondial":
        decisions = get_scenario_choc_mondial_stagflation()
        titre = "STRESS-TEST CHOC MONDIAL (Stagflation, Pétrole >110$, Resserrement Fed)"
    else:
        raise ValueError(f"Scénario inconnu : {nom_scenario}")

    for dec in decisions:
        moteur.appliquer_etape(dec)

    afficher_tableau_resultats(titre, moteur.historique_etapes)

    if export_path:
        export_scenario(nom_scenario, moteur.historique_etapes, export_path)

    return moteur.historique_etapes


def export_scenario(
    nom_scenario: str,
    resultats: list[ResultatEtapeSimulation],
    export_path: str,
) -> str:
    """
    Exporte les résultats de simulation vers un fichier.

    Détecte le format à partir de l'extension du fichier (.json ou .csv).
    Retourne le chemin absolu du fichier généré.
    """
    chemin = Path(export_path).expanduser().resolve()

    if chemin.suffix.lower() == ".json":
        return exporter_json(nom_scenario, resultats, str(chemin))
    elif chemin.suffix.lower() == ".csv":
        return exporter_csv(nom_scenario, resultats, str(chemin))
    else:
        raise ValueError(
            f"Format d'export non supporté : '{chemin.suffix}'. "
            "Utilisez .json ou .csv"
        )


def exporter_json(
    nom_scenario: str,
    resultats: list[ResultatEtapeSimulation],
    chemin: str,
) -> str:
    """Exporte les résultats vers un fichier JSON structuré."""
    payload = {
        "scenario": nom_scenario,
        "modele": "Gigogne 4 échelons (Local, National, Europe, Mondial)",
        "nombre_etapes": len(resultats),
        "resultats": [asdict(r) for r in resultats],
    }
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\n>>> Export JSON : {chemin}")
    return chemin


def exporter_csv(
    nom_scenario: str,
    resultats: list[ResultatEtapeSimulation],
    chemin: str,
) -> str:
    """Exporte les résultats vers un fichier CSV (une ligne par année)."""
    champs = [f.name for f in fields(ResultatEtapeSimulation)]
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=champs, extrasaction="ignore")
        writer.writeheader()
        for r in resultats:
            d = asdict(r)
            # Convertit la liste de commentaires en chaîne pour le CSV
            if isinstance(d.get("commentaires"), list):
                d["commentaires"] = "; ".join(d["commentaires"])
            writer.writerow(d)
    print(f"\n>>> Export CSV : {chemin}")
    return chemin


def lancer_menu_interactif() -> None:
    afficher_banniere()
    while True:
        print("\nCHOISISSEZ UN SCÉNARIO À TESTER :")
        print("  1. Lancer le Plan de Mandature quinquennal (+60 Md€ / an)")
        print("  2. Lancer le Statut Quo (Immobilisme et dérive financière)")
        print("  3. Lancer l'Austérité aveugle (Coupes territoriales et fronde fiscale)")
        print("  4. Lancer le Stress-Test Choc Mondial (Stagflation, Pétrole, Fed)")
        print("  5. Comparer les scénarios côte-à-côte à l'Année 5")
        print("  6. Exporter le Plan de Mandature en JSON")
        print("  7. Exporter le Plan de Mandature en CSV")
        print("  8. Quitter")

        choix = input("\nVotre choix (1-8) : ").strip()
        if choix == "1":
            res = executer_scenario("mandature")
            afficher_detail_annee(res[-1])
        elif choix == "2":
            res = executer_scenario("statut_quo")
            afficher_detail_annee(res[-1])
        elif choix == "3":
            res = executer_scenario("austerite")
            afficher_detail_annee(res[-1])
        elif choix == "4":
            res = executer_scenario("choc_mondial")
            afficher_detail_annee(res[-1])
        elif choix == "5":
            print("\n" + "=" * 105)
            print("COMPARATIF STRATÉGIQUE DES 4 STRATES À L'ANNÉE 5")
            print("=" * 105)
            m_res = executer_scenario("mandature")
            sq_res = executer_scenario("statut_quo")
            au_res = executer_scenario("austerite")
            cm_res = executer_scenario("choc_mondial")
            print("\n>>> SYNTHÈSE CROISÉE À L'ANNÉE 5 :")
            print(f" - Plan Mandature : Déficit = {m_res[-1].ratio_deficit_pib:.2f} % | OAT = {m_res[-1].taux_oat_pct:.2f} % | Tension = {m_res[-1].tension_sociale_locale:.1f}/100 | PDE = {'ALERTE' if m_res[-1].statut_pde_europe else 'CONFORME'}")
            print(f" - Statut Quo     : Déficit = {sq_res[-1].ratio_deficit_pib:.2f} % | OAT = {sq_res[-1].taux_oat_pct:.2f} % | Tension = {sq_res[-1].tension_sociale_locale:.1f}/100 | PDE = {'ALERTE' if sq_res[-1].statut_pde_europe else 'CONFORME'}")
            print(f" - Austérité      : Déficit = {au_res[-1].ratio_deficit_pib:.2f} % | OAT = {au_res[-1].taux_oat_pct:.2f} % | Tension = {au_res[-1].tension_sociale_locale:.1f}/100 | PDE = {'ALERTE' if au_res[-1].statut_pde_europe else 'CONFORME'}")
            print(f" - Choc Mondial   : Déficit = {cm_res[-1].ratio_deficit_pib:.2f} % | OAT = {cm_res[-1].taux_oat_pct:.2f} % | Tension = {cm_res[-1].tension_sociale_locale:.1f}/100 | PDE = {'ALERTE' if cm_res[-1].statut_pde_europe else 'CONFORME'}")
        elif choix == "6":
            res = executer_scenario("mandature")
            export_scenario("mandature", res, "mandature_simulateur.json")
            print("Export JSON terminé.")
        elif choix == "7":
            res = executer_scenario("mandature")
            export_scenario("mandature", res, "mandature_simulateur.csv")
            print("Export CSV terminé.")
        elif choix == "8":
            print("\nFermeture du simulateur.")
            break
        else:
            print("Choix invalide.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Supporte : scenario [scenario] [--export <path.json|csv>]
        scenario = sys.argv[1].lower()
        if scenario in ("mandature", "statut_quo", "austerite", "choc_mondial"):
            export_path = None
            if "--export" in sys.argv:
                idx = sys.argv.index("--export")
                if idx + 1 < len(sys.argv):
                    export_path = sys.argv[idx + 1]
                else:
                    print("Usage: python3 -m simulateur.cli [scenario] [--export <path.json|csv>]")
                    sys.exit(1)
            executer_scenario(scenario, export_path=export_path)
        elif scenario == "--export":
            print("Usage: python3 -m simulateur.cli [mandature|statut_quo|austerite|choc_mondial] [--export <path.json|csv>]")
            sys.exit(1)
        else:
            print("Usage: python3 -m simulateur.cli [mandature|statut_quo|austerite|choc_mondial] [--export <path.json|csv>]")
            sys.exit(1)
    else:
        lancer_menu_interactif()
