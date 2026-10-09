from typing import Dict, List, Tuple
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
    get_scenario_alternance_2032,
    get_scenario_austerite_brutale,
    get_scenario_choc_mondial_stagflation,
    get_scenario_convergence_ww3,
    get_scenario_crise_taiwan,
    get_scenario_double_mandature,
    get_scenario_escalade_nucleaire_tactique,
    get_scenario_fermeture_hormuz,
    get_scenario_mandature_5_ans,
    get_scenario_resilience_republicaine,
    get_scenario_statut_quo,
    get_scenario_austerite_brutale,
    get_scenario_choc_mondial_stagflation,
)
from simulateur.think_tanks import (
    REGISTRE_THINK_TANKS,
    PARADIGMES_STRESS_TEST,
    executer_stress_tests_mandature,
)
from simulateur.histoire_france import (
    PERIODES_HISTORIQUES,
    SERIES_ANNUELLES,
    REFORMES_MAJEURES,
    CRISES_HISTORIQUES,
    generer_synthese_historique,
    comparer_periodes,
)
from simulateur.societe_domaines import (
    DOMAINES_SOCIETAUX,
    generer_synthese_societale,
)

# Catalogue central des scénarios : clé CLI -> (fabrique de décisions, titre affiché)
CATALOGUE_SCENARIOS: Dict[str, Tuple] = {
    "mandature": (get_scenario_mandature_5_ans, "PLAN DE MANDATURE RÉPUBLICAIN (+60 Md€ en Année 5)"),
    "statut_quo": (get_scenario_statut_quo, "STATUT QUO (Immobilisme politique et inertie)"),
    "austerite": (get_scenario_austerite_brutale, "AUSTÉRITÉ AVEUGLE (Coupes territoriales et fronde fiscale)"),
    "choc_mondial": (
        get_scenario_choc_mondial_stagflation,
        "STRESS-TEST CHOC MONDIAL (Stagflation, Pétrole >110$, Resserrement Fed)",
    ),
    "crise_taiwan": (
        get_scenario_crise_taiwan,
        "SCÉNARIO A — CRISE DE TAÏWAN (Blocus, semi-conducteurs, Chips Act souverain)",
    ),
    "hormuz": (
        get_scenario_fermeture_hormuz,
        "SCÉNARIO C — FERMETURE DU DÉTROIT D'HORMUZ (20 % du pétrole mondial, Brent > 150 $)",
    ),
    "escalade_nucleaire": (
        get_scenario_escalade_nucleaire_tactique,
        "SCÉNARIO B — ESCALADE NUCLÉAIRE TACTIQUE OTAN-RUSSIE (stress-test ultime)",
    ),
    "convergence_ww3": (
        get_scenario_convergence_ww3,
        "SCÉNARIO D — CONVERGENCE CHINE-RUSSIE-IRAN (guerre mondiale, borne supérieure de risque)",
    ),
    "resilience": (
        get_scenario_resilience_republicaine,
        "RÉSILIENCE RÉPUBLICAINE (Mandature + réarmement OTAN 3,50 % PIB + souveraineté industrielle)",
    ),
    "double_mandature": (
        get_scenario_double_mandature,
        "DEUX MANDATURES CONSÉCUTIVES 2027-2037 (10 ans : verrou constitutionnel, dividende de la dette)",
    ),
    "alternance_2032": (
        get_scenario_alternance_2032,
        "STRESS-TEST ALTERNANCE 2032 (Deux mandatures sans verrou constitutionnel)",
    ),
}

SCENARIOS_DISPONIBLES: Tuple[str, ...] = tuple(CATALOGUE_SCENARIOS)
USAGE_SCENARIOS = "|".join(SCENARIOS_DISPONIBLES)


def afficher_banniere() -> None:
    print("=" * 105)
    print("   SIMULATEUR MACRO-POLITIQUE SYSTÉMIQUE : DYNAMIQUE DES 4 STRATES INTERCONNECTÉES   ")
    print("    [1. Local / Collectivités] -> [2. National / État] -> [3. Europe / PDE] -> [4. Mondial / Marchés]    ")
    print("=" * 105)


def afficher_tableau_resultats(titre: str, resultats: List[ResultatEtapeSimulation]) -> None:
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
    print(f"   * Solde commercial extérieur    : {r.solde_commercial_mde:.1f} Md€ (Export: {r.exportations_biens_services_mde:.1f} Md€ / Import: {r.importations_biens_services_mde:.1f} Md€)")
    print(f"   * Détention dette non-résidents : {r.part_dette_non_residents_pct:.1f} % ({r.volume_dette_non_residents_mde:.1f} Md€)")
    print(f"   * Dynamique dette boule de neige: r - g = {r.ecart_boule_de_neige_r_moins_g:+.2f} pt ({'DÉCRUE SPONTANÉE' if r.ecart_boule_de_neige_r_moins_g < 0 else 'EXPLOSION SPONTANÉE'})")

    print("\n5. STRATE SOCIALE, DÉCILES & INÉGALITÉS (Données certifiées ERFS / INSEE) :")
    print(f"   * Indice d'inégalité de Gini    : {r.indice_gini:.3f} (Réf. base: 0.298)")
    print(f"   * Taux de pauvreté monétaire 60%: {r.taux_pauvrete_monetaire_pct:.1f} % (Réf. base: 14.4 %)")
    print(f"   * Rapport interdécile D9 / D1   : {r.ratio_interdecile_d9_d1:.2f} (Réf. base: 3.90)")
    print(f"   * Gain pouvoir d'achat D1-D3    : {r.gain_pouvoir_achat_d1_d3_annuel_euros:+.0f} €/an par ménage modeste")
    print(f"   * Confiance Ouvriers / Artisans : Ouvriers {r.csp_ouvriers_confiance:.1f}/100 | Artisans {r.csp_artisans_commercants_confiance:.1f}/100")

    print("\n6. PISTE D'AUDITABILITÉ & TRAÇABILITÉ SCIENTIFIQUE :")
    print(f"   * Empreinte intégrité SHA256    : {r.signature_integrite_sha256}")
    print(f"   * Sources officielles certifiées: {r.nb_sources_officielles_mobilisees} indicateurs reliés (INSEE, DGFIP, AFT, BCE)")
    print(f"   * Taux de couverture légale     : {r.taux_couverture_legale_pct:.1f} % (95 articles de loi sans paramètre orphelin)")
    print(f"   * Conformité organique LOLF/CGCT: {'CONFORME' if r.conformite_organique_lolf else 'ALERTE'}")

    print("\n5. STRATE GÉOPOLITIQUE (Conflits, Chokepoints, Dissuasion & Défense) :")
    print(f"   * Indice de tension composite   : {r.indice_tension_geopolitique:.1f} / 100")
    print(f"   * Indice heuristique d'escalade : {r.probabilite_escalade_mondiale_pct:.1f}/100")
    print(f"   * Indice nucléaire (heuristique): {r.risque_nucleaire_tactique_pct:.1f}/100")
    print(f"   * Chokepoints sous tension      : {r.chokepoints_sous_tension} / 7")
    print(f"   * Disponibilité semi-conducteurs: {r.disponibilite_semiconducteurs_pct:.1f} %")
    print(f"   * Réserves stratégiques pétrole : {r.stocks_strategiques_petrole_jours:.0f} jours (minimum AIE : 90 j)")
    print(f"   * Effort de défense             : {r.effort_defense_pct_pib:.2f} % du PIB ({r.depenses_defense_mde:.1f} Md€) — cible OTAN 3,50 %")
    print(f"   * Prime de risque géopolitique  : {r.prime_risque_geopolitique_bps:.0f} bps")

    print("\n6. JOURNAL DES ÉVÉNEMENTS & RÉTROACTIONS :")
    print("\n7. JOURNAL DES ÉVÉNEMENTS & RÉTROACTIONS :")
    for comm in r.commentaires:
        print(f"   - {comm}")
    print("=" * 76)


def executer_scenario(
    nom_scenario: str,
    export_path: str | None = None,
) -> List[ResultatEtapeSimulation]:
    moteur = MoteurSimulationSystemique()

    if nom_scenario not in CATALOGUE_SCENARIOS:
        raise ValueError(
            f"Scénario inconnu : {nom_scenario}. Scénarios disponibles : {USAGE_SCENARIOS}"
        )
    fabrique, titre = CATALOGUE_SCENARIOS[nom_scenario]
    decisions = fabrique()

    for dec in decisions:
        moteur.appliquer_etape(dec)

    afficher_tableau_resultats(titre, moteur.historique_etapes)

    if export_path:
        export_scenario(nom_scenario, moteur.historique_etapes, export_path)

    return moteur.historique_etapes


def export_scenario(
    nom_scenario: str,
    resultats: List[ResultatEtapeSimulation],
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
    resultats: List[ResultatEtapeSimulation],
    chemin: str,
) -> str:
    """Exporte les résultats vers un fichier JSON structuré."""
    payload = {
        "scenario": nom_scenario,
        "modele": "Gigogne 5 échelons (Local, National, Europe, Mondial, Géopolitique)",
        "nombre_etapes": len(resultats),
        "resultats": [asdict(r) for r in resultats],
    }
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\n>>> Export JSON : {chemin}")
    return chemin


def exporter_csv(
    nom_scenario: str,
    resultats: List[ResultatEtapeSimulation],
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
        print("  -- Trajectoires budgétaires et politiques --")
        print("  1. Plan de Mandature quinquennal (+60 Md€ / an)")
        print("  2. Statut Quo (Immobilisme et dérive financière)")
        print("  3. Austérité aveugle (Coupes territoriales et fronde fiscale)")
        print("  4. Stress-Test Choc Mondial (Stagflation, Pétrole, Fed)")
        print("  -- Strate 5 : scénarios géopolitiques et de sécurité --")
        print("  5. Scénario A : Crise de Taïwan (blocus & semi-conducteurs)")
        print("  6. Scénario C : Fermeture du détroit d'Hormuz (choc pétrolier)")
        print("  7. Scénario B : Escalade nucléaire tactique OTAN-Russie")
        print("  8. Scénario D : Convergence Chine-Russie-Iran (guerre mondiale)")
        print("  9. Résilience républicaine (Mandature + réarmement OTAN 3,50 % PIB)")
        print(" -- Profondeur temporelle : deux mandatures consécutives (10 ans) --")
        print(" 14. Deux mandatures consécutives 2027-2037 (verrou, dividende de la dette)")
        print(" 15. Stress-test : alternance 2032 (réformes non verrouillées)")
        print("  -- Outils --")
        print(" 10. Comparer TOUS les scénarios à l'Année 5")
        print(" 11. Exporter le Plan de Mandature en JSON")
        print(" 12. Exporter le Plan de Mandature en CSV")
        print(" 13. Quitter")

        choix = input("\nVotre choix (1-15) : ").strip()
        raccourcis = {
            "1": "mandature",
            "2": "statut_quo",
            "3": "austerite",
            "4": "choc_mondial",
            "5": "crise_taiwan",
            "6": "hormuz",
            "7": "escalade_nucleaire",
            "8": "convergence_ww3",
            "9": "resilience",
            "14": "double_mandature",
            "15": "alternance_2032",
        }
        if choix in raccourcis:
            res = executer_scenario(raccourcis[choix])
            afficher_detail_annee(res[-1])
        elif choix == "10":
            print("\n" + "=" * 105)
            print("COMPARATIF STRATÉGIQUE DES 5 STRATES À L'ANNÉE FINALE")
            print("=" * 105)
            synthese = []
            for cle, (_, titre_sc) in CATALOGUE_SCENARIOS.items():
                res = executer_scenario(cle)
                synthese.append((titre_sc.split("(")[0].strip()[:38], res[-1]))
            print("\n>>> SYNTHÈSE CROISÉE À L'ANNÉE FINALE :")
            for nom_court, r in synthese:
                print(
                    f" - {nom_court:<38} : Déficit = {r.ratio_deficit_pib:>6.2f} % | OAT = {r.taux_oat_pct:>5.2f} % | "
                    f"Tension = {r.tension_sociale_locale:>5.1f}/100 | Géo = {r.indice_tension_geopolitique:>5.1f}/100 | "
                    f"Indice escalade = {r.probabilite_escalade_mondiale_pct:>5.1f}/100 | "
                    f"PDE = {'ALERTE' if r.statut_pde_europe else 'CONFORME'}"
                )
        elif choix == "11":
            res = executer_scenario("mandature")
            export_scenario("mandature", res, "mandature_simulateur.json")
            print("Export JSON terminé.")
        elif choix == "12":
            res = executer_scenario("mandature")
            export_scenario("mandature", res, "mandature_simulateur.csv")
            print("Export CSV terminé.")
        elif choix == "13":
            print("\nFermeture du simulateur.")
            break
        else:
            print("Choix invalide.")


def afficher_stress_tests_cli():
    """Affiche les résultats d'évaluation des 5 paradigmes de stress-test."""
    print("\n" + "=" * 105)
    print("AUDIT CONTRADICTOIRE : ÉVALUATION DES 5 PARADIGMES DE STRESS-TEST (23 THINK TANKS)")
    print("=" * 105)
    res = executer_stress_tests_mandature(None, None, None, None, None)
    for k, st in res.items():
        print(f"\n[{st.statut}] {st.titre} — Score: {st.score_robustesse_sur_100:.0f} %")
        print(f"  * Rationale scientifique : {st.justification_scientifique}")
        print("  * Critères audités :")
        for ck, cv in st.criteres_analyses.items():
            conf_str = "OK" if cv["conforme"] else "ÉCHEC"
            print(f"    - {ck:<42}: {cv['valeur']} {cv['unite']} [{conf_str}]")
        print("  * Réponses aux brèches soulevées :")
        for rep in st.reponses_systemiques:
            print(f"    -> {rep}")


def afficher_think_tanks_cli():
    """Affiche le répertoire synthétique des 23 think tanks répertoriés."""
    print("\n" + "=" * 105)
    print("RÉPERTOIRE MONDIAL DES 23 THINK TANKS AUDITÉS (LOCAL À MONDIAL)")
    print("=" * 105)
    for tt_id, tt in REGISTRE_THINK_TANKS.items():
        print(f"\n• [{tt.echelon.upper()}] {tt.nom} ({tt.sigle}) — Siège: {tt.pays_siege}")
        print(f"  Orientation : {tt.epistemologie} | Direction: {tt.directeur_ou_fondateur}")
        print(f"  Objection   : {tt.objections_anticipees[0]}")
        print(f"  Pourquoi    : {tt.pourquoi_integration}")
        print(f"  Réponse     : {tt.reponse_du_simulateur}")


def afficher_histoire_cli():
    """Affiche la synthèse historique et les périodes de référence."""
    print(generer_synthese_historique())
    print(f"\n{len(PERIODES_HISTORIQUES)} périodes historiques | {len(SERIES_ANNUELLES)} points chronologiques | {len(REFORMES_MAJEURES)} réformes majeures | {len(CRISES_HISTORIQUES)} crises systémiques")


def afficher_societe_cli():
    """Affiche la synthèse des 18 domaines sociétaux."""
    print(generer_synthese_societale())


def afficher_comparaison_historique_cli(a_id: str, b_id: str):
    """Compare deux périodes historiques en mode CLI."""
    comp = comparer_periodes(a_id, b_id)
    print(f"\n{'=' * 80}")
    print(f"COMPARAISON : {comp.periode_a}  ↔  {comp.periode_b}")
    print('=' * 80)
    for dim_key, indicateurs in comp.dimensions.items():
        print(f"\n--- {dim_key.upper()} ---")
        for attr, vals in indicateurs.items():
            delta_str = f"{vals['delta']:+.2f}" if vals['delta'] is not None else "-"
            print(f"  {vals.get('label', attr):<45} A={vals['a']:<12} B={vals['b']:<12} Δ={delta_str}")
    if comp.enseignements:
        print(f"\n{'=' * 80}")
        print("ENSEIGNEMENTS :")
        for e in comp.enseignements:
            print(f"  💡 {e}")


def comparer_tous_scenarios():
    """Exécute et compare les 4 scénarios."""
    print("\n" + "=" * 105)
    print("COMPARATIF STRATÉGIQUE DES 4 STRATES À L'ANNÉE 5")
    print("=" * 105)
    m_res = executer_scenario("mandature")
    sq_res = executer_scenario("statut_quo")
    au_res = executer_scenario("austerite")
    ch_res = executer_scenario("choc_mondial")
    print("\n>>> SYNTHÈSE CROISÉE À L'ANNÉE 5 :")
    print(f" - Plan Mandature : Déficit = {m_res[-1].ratio_deficit_pib:.2f} % | OAT = {m_res[-1].taux_oat_pct:.2f} % | Tension = {m_res[-1].tension_sociale_locale:.1f}/100 | PDE = {'ALERTE' if m_res[-1].statut_pde_europe else 'CONFORME'}")
    print(f" - Statut Quo     : Déficit = {sq_res[-1].ratio_deficit_pib:.2f} % | OAT = {sq_res[-1].taux_oat_pct:.2f} % | Tension = {sq_res[-1].tension_sociale_locale:.1f}/100 | PDE = {'ALERTE' if sq_res[-1].statut_pde_europe else 'CONFORME'}")
    print(f" - Austérité      : Déficit = {au_res[-1].ratio_deficit_pib:.2f} % | OAT = {au_res[-1].taux_oat_pct:.2f} % | Tension = {au_res[-1].tension_sociale_locale:.1f}/100 | PDE = {'ALERTE' if au_res[-1].statut_pde_europe else 'CONFORME'}")
    print(f" - Choc Mondial   : Déficit = {ch_res[-1].ratio_deficit_pib:.2f} % | OAT = {ch_res[-1].taux_oat_pct:.2f} % | Tension = {ch_res[-1].tension_sociale_locale:.1f}/100 | PDE = {'ALERTE' if ch_res[-1].statut_pde_europe else 'CONFORME'}")


if __name__ == "__main__":
    usage = f"Usage: python3 -m simulateur.cli [{USAGE_SCENARIOS}] [--export <path.json|csv>]"
    if len(sys.argv) > 1:
        # Supporte : scenario [scenario] [--export <path.json|csv>]
        scenario = sys.argv[1].lower()
        if scenario in SCENARIOS_DISPONIBLES:
            export_path = None
            if "--export" in sys.argv:
                idx = sys.argv.index("--export")
                if idx + 1 < len(sys.argv):
                    export_path = sys.argv[idx + 1]
                else:
                    print(usage)
                    sys.exit(1)
            executer_scenario(scenario, export_path=export_path)
        else:
            print(usage)
            sys.exit(1)
    else:
        lancer_menu_interactif()
