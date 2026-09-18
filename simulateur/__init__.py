"""
Package simulateur — Moteur macro-politique et systémique.
"""

from simulateur.model import (
    EchelonLocal,
    EchelonNational,
    EchelonEuropeen,
    EchelonMondial,
    DecisionPolitique,
    ResultatEtapeSimulation,
    SousSecteurBlocCommunal,
    SousSecteurDepartements,
    SousSecteurRegions,
    SousSecteurEtatCentral,
    SousSecteurSecuriteSociale,
    SousSecteurParlement,
    SousSecteurChambresConsulaires,
    SousSecteurInstitutionsRepublique,
)
from simulateur.moteur import MoteurSimulationSystemique
from simulateur.scenarios import (
    get_scenario_mandature_5_ans,
    get_scenario_statut_quo,
    get_scenario_austerite_brutale,
    get_scenario_choc_mondial_stagflation,
)
from simulateur.reglements_lois import (
    ArticleDeLoi,
    REGISTRE_LEGAL,
    get_corpus_lois,
    rechercher_loi,
)
from simulateur.web_server import demarrer_serveur_web

__all__ = [
    "EchelonLocal",
    "EchelonNational",
    "EchelonEuropeen",
    "EchelonMondial",
    "DecisionPolitique",
    "ResultatEtapeSimulation",
    "SousSecteurBlocCommunal",
    "SousSecteurDepartements",
    "SousSecteurRegions",
    "SousSecteurEtatCentral",
    "SousSecteurSecuriteSociale",
    "SousSecteurParlement",
    "SousSecteurChambresConsulaires",
    "SousSecteurInstitutionsRepublique",
    "MoteurSimulationSystemique",
    "get_scenario_mandature_5_ans",
    "get_scenario_statut_quo",
    "get_scenario_austerite_brutale",
    "get_scenario_choc_mondial_stagflation",
    "ArticleDeLoi",
    "REGISTRE_LEGAL",
    "get_corpus_lois",
    "rechercher_loi",
    "demarrer_serveur_web",
]
