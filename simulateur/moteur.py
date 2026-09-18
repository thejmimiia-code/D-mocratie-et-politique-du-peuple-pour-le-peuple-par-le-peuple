"""
simulateur/moteur.py — Moteur de simulation systémique à poupées russes (4 strates interconnectées).
Calé rigoureusement sur les données et contraintes à l'instant T (AFT, INSEE, Eurostat, CGCT).
"""

from typing import List, Dict, Any, Tuple
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
)


class MoteurSimulationSystemique:
    """
    Simulateur de politique macro-économique, institutionnelle et financière.
    Modélise les flux rétroactifs complets :
    Décision -> Local -> Social -> National -> Parlement -> Europe -> Marchés -> Réinjection
    """

    def __init__(
        self,
        local: EchelonLocal = None,
        national: EchelonNational = None,
        europe: EchelonEuropeen = None,
        mondial: EchelonMondial = None,
    ):
        self.local = local or EchelonLocal()
        self.national = national or EchelonNational()
        self.europe = europe or EchelonEuropeen()
        self.mondial = mondial or EchelonMondial()
        self.historique_etapes: List[ResultatEtapeSimulation] = []

        # État cumulatif des réformes constitutionnelles et civiques
        self.reforme_casier_b2_active = False
        self.reforme_vote_blanc_active = False
        self.reforme_ric_active = False
        self.reforme_regimes_speciaux_active = False
        self.reforme_anti_pantouflage_active = False
        self.reforme_non_cumul_active = False

    def appliquer_etape(self, decision: DecisionPolitique) -> ResultatEtapeSimulation:
        """
        Exécute la chaîne causale multi-strates pour un exercice fiscal.
        """
        commentaires: List[str] = []

        # =========================================================================
        # 0. CHOCS MONDIAUX (Matières Premières, Devises, Taux Mondiaux) & PIB
        # =========================================================================
        # Prise en compte des chocs exogènes mondiaux (Pétrole Brent, EUR/USD, Fed)
        if decision.choc_petrole_brent_usd != 0.0:
            self.mondial.cours_petrole_brent_usd = max(35.0, round(self.mondial.cours_petrole_brent_usd + decision.choc_petrole_brent_usd, 2))
            commentaires.append(
                f"[Strate 4 - Mondial] Choc pétrolier exogène : Brent à {self.mondial.cours_petrole_brent_usd:.1f} $/bbl ({decision.choc_petrole_brent_usd:+.1f} $)."
            )

        if decision.choc_change_eur_usd != 0.0:
            self.mondial.taux_change_eur_usd = max(0.75, round(self.mondial.taux_change_eur_usd + decision.choc_change_eur_usd, 3))
            commentaires.append(
                f"[Strate 4 - Forex] Choc de change : Parité EUR/USD à {self.mondial.taux_change_eur_usd:.3f} ({decision.choc_change_eur_usd:+.3f})."
            )

        # Calcul de la facture énergétique nationale nette (importations nettes d'hydrocarbures)
        delta_brent = self.mondial.cours_petrole_brent_usd - 82.5
        delta_change = self.mondial.taux_change_eur_usd - 1.08
        delta_facture = (delta_brent / 10.0) * 4.50 - (delta_change / 0.05) * 2.80
        self.mondial.facture_energetique_nette_mde = max(25.0, round(64.5 + delta_facture, 2))

        # Inflation globale française (IPC) répercutant l'énergie mondiale et le bouclier TVA 5,5%
        surcroit_inflation_energie = (delta_facture / 10.0) * 0.45
        rabais_inflation_tva = (decision.baisse_tva_energie_5_5_mde / 9.0) * 0.35
        self.mondial.inflation_globale_pct = max(0.5, round(2.1 + surcroit_inflation_energie - rabais_inflation_tva, 2))

        # Croissance nominale tendancielle du PIB
        pib_t = self.national.pib_nominal_mde * ((1.0 + self.national.taux_croissance_potentiel) ** (decision.annee - 1))

        # Multiplicateurs keynésiens différenciés :
        # - Rentes/Fraude/Superprofits/Pilier2 : multiplicateur récessif très faible (-0.12)
        # - Baisse de TVA énergie : multiplicateur d'expansion de la consommation (+0.75)
        # - Coupes dans les dotations aux collectivités : multiplicateur récessif fort (-0.85)
        # - Choc d'inflation importée sur l'activité : impact récessif (-0.25 par point d'inflation au-dessus de 2%)
        impact_choc_inflation = -max(0.0, (self.mondial.inflation_globale_pct - 2.0) * 3.5)
        impact_multiplicateur = (
            (decision.baisse_tva_energie_5_5_mde * 0.75)
            - ((decision.recettes_fraude_ia_mde + decision.taxe_superprofits_rachats_mde + decision.extension_ttf_mde + decision.recettes_pilier2_ocde_mde + decision.recettes_macf_carbone_mde) * 0.12)
            + (decision.delta_dotation_dgf_mde * 0.85 if decision.delta_dotation_dgf_mde < 0 else 0)
            + impact_choc_inflation
        )
        pib_annee = round(pib_t + impact_multiplicateur, 2)

        # =========================================================================
        # 1. STRATE LOCALE (Règle d'or CGCT art. L. 1612-4 & Fiscalité foncière)
        # =========================================================================
        # Répartition de la DGF versée par l'État
        part_dgf_communes = decision.delta_dotation_dgf_mde * 0.45
        part_dgf_departements = decision.delta_dotation_dgf_mde * 0.37
        part_dgf_regions = decision.delta_dotation_dgf_mde * 0.18

        self.local.bloc_communal.dgf_recue_mde += part_dgf_communes
        self.local.departements.dgf_departementale_mde += part_dgf_departements
        self.local.regions.dgf_regionale_mde += part_dgf_regions

        if decision.delta_dotation_dgf_mde < 0:
            # Transfert de charges : les collectivités ont l'interdiction d'emprunter pour fonctionner
            perte_dgf = abs(decision.delta_dotation_dgf_mde)
            hausse_taxe_fonciere = perte_dgf * 0.94
            self.local.bloc_communal.taxe_fonciere_tfpb_mde += hausse_taxe_fonciere
            # La hausse de taxe foncière frappe directement les classes moyennes propriétaires
            self.local.tension_sociale_territoriale += hausse_taxe_fonciere * 1.6
            commentaires.append(
                f"[Strate 1 - Local CGCT] Baisse DGF de {perte_dgf:.1f} Md€ -> Report forcé sur la taxe foncière (+{hausse_taxe_fonciere:.1f} Md€) et grogne locale."
            )

        # Surcoût énergétique pour les collectivités territoriales (chauffage, éclairage, cantines, bus)
        if delta_facture > 0:
            surcout_energie_collectivites = delta_facture * 0.06
            self.local.bloc_communal.depenses_fonctionnement_mde += surcout_energie_collectivites * 0.50
            self.local.departements.depenses_colleges_et_routes_mde += surcout_energie_collectivites * 0.25
            self.local.regions.depenses_transports_ter_mde += surcout_energie_collectivites * 0.25
            self.local.tension_sociale_territoriale += surcout_energie_collectivites * 0.70

        if decision.fusion_doublons_territoriaux_mde > 0:
            # Économie de gestion sur les sièges administratifs sans fermer aucun guichet
            gain_qualite = decision.fusion_doublons_territoriaux_mde * 1.6
            self.local.qualite_services_proximite = min(100.0, 64.0 + gain_qualite)
            commentaires.append(
                f"[Strate 1 - Local] Mutualisation des sièges région/département : redéploiement d'agents vers le terrain (+{gain_qualite:.1f} pts services)."
            )

        # =========================================================================
        # 2. IMPACT SOCIAL & POUVOIR D'ACHAT (Ménages & Probité Républicaine)
        # =========================================================================
        if decision.baisse_tva_energie_5_5_mde > 0:
            gain_pouvoir_achat = decision.baisse_tva_energie_5_5_mde
            self.national.pouvoir_achat_menages_index = 100.0 + (gain_pouvoir_achat / 9.0) * 3.8
            self.local.tension_sociale_territoriale = max(5.0, self.local.tension_sociale_territoriale - 9.5)
            commentaires.append(
                f"[Pouvoir d'Achat] Baisse TVA énergie à 5,5 % -> +{gain_pouvoir_achat:.1f} Md€ de pouvoir d'achat net pour les ménages (Tension -9.5 pts)."
            )

        # Impact négatif de l'inflation sur le pouvoir d'achat
        if self.mondial.inflation_globale_pct > 2.0:
            erosion_inflation = (self.mondial.inflation_globale_pct - 2.0) * 1.4
            self.national.pouvoir_achat_menages_index = max(70.0, self.national.pouvoir_achat_menages_index - erosion_inflation)
            self.local.tension_sociale_territoriale = min(100.0, self.local.tension_sociale_territoriale + erosion_inflation * 1.8)

        # Réformes constitutionnelles et civiques
        if decision.reforme_casier_b2:
            self.reforme_casier_b2_active = True
            commentaires.append("[Démocratie] Casier B2 vierge obligatoire activé pour les candidats.")
        if decision.reforme_vote_blanc_invalidant:
            self.reforme_vote_blanc_active = True
            commentaires.append("[Démocratie] Vote blanc invalidant instauré avec délai de carence 12 mois.")
        if decision.reforme_ric_souverain:
            self.reforme_ric_active = True
            self.local.tension_sociale_territoriale = max(5.0, self.local.tension_sociale_territoriale - 12.0)
            commentaires.append("[Démocratie] RIC souverain en vigueur -> apaisement démocratique profond.")
        if decision.reforme_fin_regimes_speciaux:
            self.reforme_regimes_speciaux_active = True
        if decision.reforme_anti_pantouflage_lobbys:
            self.reforme_anti_pantouflage_active = True
        if decision.reforme_non_cumul_mandats:
            self.reforme_non_cumul_active = True

        gains_civiques = 0.0
        if self.reforme_casier_b2_active: gains_civiques += 10.0
        if self.reforme_vote_blanc_active: gains_civiques += 8.0
        if self.reforme_ric_active: gains_civiques += 14.0
        if self.reforme_regimes_speciaux_active: gains_civiques += 6.0
        if self.reforme_anti_pantouflage_active: gains_civiques += 7.0
        if self.reforme_non_cumul_active: gains_civiques += 5.0

        self.national.confiance_democratique = min(100.0, 27.5 + gains_civiques)

        # =========================================================================
        # 3. STRATE NATIONALE (État, Sécurité Sociale, Déficit au sens de Maastricht)
        # =========================================================================
        # Nouvelles recettes fiscales de régulation (Volet 2 + International)
        recettes_volet2 = (
            decision.recettes_fraude_ia_mde
            + decision.conditionnement_aides_entreprises_mde
            + decision.taxe_superprofits_rachats_mde
            + decision.extension_ttf_mde
            + decision.recettes_pilier2_ocde_mde
            + decision.recettes_macf_carbone_mde
        )

        # Économies structurelles récurrentes (Volet 3)
        economies_volet3 = (
            decision.fusion_doublons_territoriaux_mde
            + decision.commande_publique_massifiee_mde
            + decision.extinction_niches_inefficaces_mde
            + decision.fraude_sociale_criminelle_mde
        )

        # Coût net de la baisse de TVA énergie
        cout_tva = decision.baisse_tva_energie_5_5_mde

        # Recettes publiques totales consolidées (APU)
        recettes_totales_apu = 1565.0 + recettes_volet2 - cout_tva

        # Effort structurel net
        effort_structurel_net = recettes_volet2 + economies_volet3 - cout_tva

        # Stabilité parlementaire et risque de motion de censure
        if self.local.tension_sociale_territoriale > 65.0:
            # Forte contestation civique -> les députés centristes/indépendants basculent vers la censure
            self.national.parlement.probabilite_motion_censure_pct = min(95.0, 52.0 + (self.local.tension_sociale_territoriale - 65.0) * 2.2)
            commentaires.append(
                f"[Parlement] Alerte censure : probabilité de chute du cabinet à {self.national.parlement.probabilite_motion_censure_pct:.1f} %."
            )
        else:
            # Climat pacifié et confiance civique en hausse
            self.national.parlement.probabilite_motion_censure_pct = max(10.0, 52.0 - (self.national.confiance_democratique * 0.4))

        # =========================================================================
        # 4. STRATE MONDIALE (Agence France Trésor, Spreads, OAT 10 ans, Rating)
        # =========================================================================
        # Resserrement monétaire Fed -> transmission au Bund allemand
        delta_bund_fed = (decision.choc_taux_fed_bps / 100.0) * 0.40

        # Règle d'ajustement du spread souverain OAT-Bund et de la prime de risque
        if effort_structurel_net >= 50.0:
            # Trajectoire de désendettement crédible reconnue par les investisseurs :
            # Détente conjointe du taux sans risque de la Zone Euro (Bund) et contraction du spread français
            detente_bund = (effort_structurel_net / 60.0) * 0.50
            self.mondial.taux_bund_allemagne_10ans = max(2.50, round(3.30 - detente_bund + delta_bund_fed, 2))
            self.mondial.spread_oat_bund_bps = max(38.0, 88.0 - (effort_structurel_net / 60.0) * 48.0)
            self.mondial.note_souveraine = "AA"
            self.mondial.prime_risque_politique_bps = max(5.0, 25.0 - (self.national.confiance_democratique / 4.0))
        elif effort_structurel_net <= 0.0:
            # Dérive budgétaire et défiance
            self.mondial.taux_bund_allemagne_10ans = round(3.30 + delta_bund_fed, 2)
            self.mondial.spread_oat_bund_bps = min(135.0, 88.0 + decision.annee * 8.0)
            if self.mondial.spread_oat_bund_bps > 105.0:
                self.mondial.note_souveraine = "A+"
                commentaires.append(
                    "[Strate 4 - Marchés] Dégradation de la note souveraine à 'A+' -> Ventes forcées de fonds indiciels internationaux."
                )
        else:
            self.mondial.taux_bund_allemagne_10ans = round(3.30 + delta_bund_fed, 2)
            self.mondial.spread_oat_bund_bps = max(50.0, 88.0 - (effort_structurel_net / 50.0) * 20.0)

        # Taux souverain OAT à 10 ans rigoureusement articulé au Bund et au spread
        self.mondial.taux_oat_france_10ans = round(self.mondial.taux_bund_allemagne_10ans + (self.mondial.spread_oat_bund_bps / 100.0), 2)

        # Transmission de l'OAT aux taux de crédit bancaire dans l'économie réelle
        self.mondial.taux_credit_pme_entreprises = round(self.mondial.taux_oat_france_10ans + 0.85, 2)
        self.mondial.taux_credit_immobilier_menages = round(self.mondial.taux_oat_france_10ans - 0.30, 2)

        # Règle de sensibilité de la charge de la dette (AFT - roll-over de maturité moyenne 8.5 ans)
        ecart_taux_base = self.mondial.taux_oat_france_10ans - 4.18
        ajustement_charge_interets = ecart_taux_base * 11.5
        charge_dette_effective = max(48.0, round(self.national.etat.charge_nette_dette_mde + ajustement_charge_interets, 2))

        # Dépenses consolidées effectives des APU
        depenses_primaires_apu = (1718.0 - self.national.etat.charge_nette_dette_mde) - economies_volet3
        depenses_totales_apu = depenses_primaires_apu + charge_dette_effective

        # Déficit public nominal consolidé (au sens de Maastricht)
        deficit_net_consolide = round(depenses_totales_apu - recettes_totales_apu, 2)
        ratio_deficit_pib = round((deficit_net_consolide / pib_annee) * 100.0, 2)

        # Stock de dette publique au sens de Maastricht
        self.national.dette_maastricht_stock_mde += deficit_net_consolide
        ratio_dette_pib = round((self.national.dette_maastricht_stock_mde / pib_annee) * 100.0, 2)

        # =========================================================================
        # 5. STRATE CONTINENTALE / EUROPÉENNE (Pacte de Stabilité, TPI, Sanctions)
        # =========================================================================
        # 5. STRATE CONTINENTALE / EUROPÉENNE (Pacte de Stabilité, TPI, Sanctions)
        # =========================================================================
        if ratio_deficit_pib <= self.europe.seuil_deficit_pde_pct:
            self.europe.statut_pde_actif = False
            self.europe.bouclier_tpi_bce_eligible = True
            self.europe.amende_sanction_semestrielle_mde = 0.0
            commentaires.append(
                f"[Strate 3 - Europe] Déficit à {ratio_deficit_pib:.2f} % <= 3.00 % : Sortie de la PDE et activation pleine du bouclier TPI de la BCE."
            )
        else:
            self.europe.statut_pde_actif = True
            # Sous le nouveau pacte, si l'ajustement structurel annuel est inférieur à 0.5% du PIB
            ajustement_realise_pct = (effort_structurel_net / pib_annee) * 100.0
            if ajustement_realise_pct >= self.europe.effort_structurel_requis_annuel_pct:
                self.europe.bouclier_tpi_bce_eligible = True
                commentaires.append(
                    f"[Strate 3 - Europe] Déficit à {ratio_deficit_pib:.2f} % : Trajectoire d'ajustement respectée (+{ajustement_realise_pct:.2f} % PIB)."
                )
            else:
                self.europe.bouclier_tpi_bce_eligible = False
                commentaires.append(
                    f"[Strate 3 - Europe] Alerte PDE : Ajustement insuffisant ({ajustement_realise_pct:.2f} % < 0.50 %) -> Risque d'astreinte financière."
                )

        # =========================================================================
        # 6. DYNAMIQUES DES ASSEMBLÉES REPRÉSENTATIVES ET DÉCISIONNELLES
        # =========================================================================
        # 1. Conseils Municipaux (34 935 communes & AMF)
        perte_dgf_val = abs(decision.delta_dotation_dgf_mde) if decision.delta_dotation_dgf_mde < 0 else 0.0
        fronde_maires = max(5.0, min(100.0, 18.0 + (perte_dgf_val * 4.5) + (self.local.tension_sociale_territoriale * 0.22)))
        self.local.conseil_municipal.fronde_fiscale_locale_indice = round(fronde_maires, 1)
        self.local.conseil_municipal.taux_revolte_maires_amf_pct = min(100.0, round(fronde_maires * 1.15, 1))

        # 2. Conseils Départementaux (101 départements & ADF - Effet de ciseau social)
        dep_sociales = 44.5 + max(0.0, (self.mondial.inflation_globale_pct - 2.0) * 1.8)
        rec_dmto = max(8.0, 12.5 - max(0.0, (self.mondial.taux_credit_immobilier_menages - 3.5) * 1.6))
        ciseau_social = max(10.0, min(100.0, 48.0 + (dep_sociales - 44.5) * 4.0 - (rec_dmto - 12.5) * 4.5 + (perte_dgf_val * 2.2)))
        dep_faillite = max(2, min(85, int(round(ciseau_social * 0.38))))
        self.local.conseil_departemental.indice_effet_ciseau_social = round(ciseau_social, 1)
        self.local.conseil_departemental.departements_alerte_faillite = dep_faillite
        if dep_faillite >= 25:
            commentaires.append(
                f"[Assemblées - Départements ADF] Alerte ciseau financier : {dep_faillite} départements en faillite technique (RSA en hausse, DMTO en berne)."
            )

        # 3. Assemblées Consulaires (CCI, CMA, Chambres d'Agriculture)
        gain_pme_commande = decision.commande_publique_massifiee_mde
        conf_cci = min(95.0, max(20.0, 52.0 + (gain_pme_commande * 3.5) - (self.mondial.taux_credit_pme_entreprises - 4.5) * 5.5))
        adh_cma = min(95.0, max(25.0, 58.0 + (gain_pme_commande * 3.8) + (2.0 if decision.baisse_tva_energie_5_5_mde > 0 else 0.0)))
        self.local.assemblees_consulaires.cci_confiance_patrons_pct = round(conf_cci, 1)
        self.local.assemblees_consulaires.cma_adhesion_artisans_pct = round(adh_cma, 1)

        # 4. Sénat (348 sénateurs - Porte-voix des collectivités territoriales, art. 24)
        hostilite_senat = max(5.0, min(100.0, 22.0 + (perte_dgf_val * 5.2) + (self.local.tension_sociale_territoriale * 0.28) - (self.national.confiance_democratique * 0.12)))
        senat_veto = hostilite_senat > 55.0
        self.national.senat.indice_hostilite_senatoriale = round(hostilite_senat, 1)
        self.national.senat.veto_reforme_constitutionnelle_art_89 = senat_veto
        self.national.senat.taux_accord_cmp_pct = max(10.0, round(85.0 - hostilite_senat * 0.65, 1))
        if senat_veto:
            commentaires.append(
                "[Assemblées - Sénat] VETO CONSTITUTIONNEL du Sénat activé (Art. 89 al. 2) : hostilité territoriale > 55/100 -> Recours nécessaire à l'Article 11 (voie référendaire directe)."
            )

        # 5. Assemblée nationale (577 députés - Vote de censure art. 49.2 & 49.3)
        base_censure = 240.0 + (self.local.tension_sociale_territoriale * 0.88) - (self.national.confiance_democratique * 0.42)
        voix_censure = max(180, min(577, int(round(base_censure))))
        gouv_censure = voix_censure >= 289
        self.national.assemblee_nationale.voix_censure_projetees = voix_censure
        self.national.assemblee_nationale.gouvernement_censure = gouv_censure

        if gouv_censure:
            climat_an = "GOUVERNEMENT CENSURÉ (Majorité absolue de 289 voix franchie)"
            commentaires.append(
                f"[Assemblées - Assemblée nationale] MOTION DE CENSURE ADOPTÉE ({voix_censure} voix >= 289) : Renversement de l'Exécutif ou dissolution (Art. 12) !"
            )
        elif voix_censure >= 275:
            climat_an = "Alerte rouge : majorité fragile à portée de motion de censure"
        elif voix_censure >= 250:
            climat_an = "Majorité relative sous haute tension parlementaire"
        else:
            climat_an = "Majorité consolidée et apaisement parlementaire républicain"
        self.national.assemblee_nationale.climat_parlementaire = climat_an

        # 6. Congrès du Parlement (Versailles - 925 membres, règle des 3/5èmes = 555 voix)
        voix_congres = max(300, min(850, int(round(925 * (0.38 + (self.national.confiance_democratique / 100.0) * 0.35 - (hostilite_senat / 320.0))))))
        congres_ok = (voix_congres >= 555) and (not senat_veto)
        self.national.congres.voix_favorables_projetees = voix_congres
        self.national.congres.majorite_3_5_atteinte = congres_ok
        self.national.congres.voie_referendaire_art_11_requise = not congres_ok

        # 7. CESE et Conventions Citoyennes délibératives
        cese_consensus = min(92.0, max(25.0, 44.0 + (10.0 if decision.baisse_tva_energie_5_5_mde > 0 else 0.0) + (decision.extinction_niches_inefficaces_mde * 1.4)))
        self.national.cese.taux_consensus_social_pct = round(cese_consensus, 1)
        consensus_citoyen = min(98.0, max(45.0, 72.0 + (12.0 if self.reforme_ric_active else 0.0) + (8.0 if self.reforme_casier_b2_active else 0.0)))
        self.national.convention_citoyenne.indice_deliberatif_consensus_pct = round(consensus_citoyen, 1)

        # 8. Parlement Européen et Conseil de l'Union Européenne
        pe_alignement = min(95.0, max(30.0, 62.0 + (8.0 if ratio_deficit_pib <= 3.0 else -10.0) + (5.0 if decision.recettes_macf_carbone_mde > 0 else 0.0)))
        self.europe.parlement_europeen.taux_alignement_directives_fr_pct = round(pe_alignement, 1)
        self.europe.conseil_ue.decision_pde_sanction_active = (ratio_deficit_pib > 3.0) and (not self.europe.bouclier_tpi_bce_eligible)

        # =========================================================================
        # 7. INSTANTANÉ DE L'ÉTAPE CONSOLIDÉE
        # =========================================================================
        resultat = ResultatEtapeSimulation(
            annee=decision.annee,
            pib_nominal_mde=pib_annee,
            deficit_nominal_mde=deficit_net_consolide,
            ratio_deficit_pib=ratio_deficit_pib,
            dette_nominale_mde=round(self.national.dette_maastricht_stock_mde, 2),
            ratio_dette_pib=ratio_dette_pib,
            charge_dette_mde=charge_dette_effective,
            recettes_publiques_totales_mde=round(recettes_totales_apu, 2),
            depenses_publiques_totales_mde=round(depenses_totales_apu, 2),
            pouvoir_achat_index=round(self.national.pouvoir_achat_menages_index, 1),
            confiance_democratique=round(self.national.confiance_democratique, 1),
            risque_censure_parlement=round(self.national.parlement.probabilite_motion_censure_pct, 1),
            tension_sociale_locale=round(self.local.tension_sociale_territoriale, 1),
            qualite_services_proximite=round(self.local.qualite_services_proximite, 1),
            produit_taxe_fonciere_mde=round(self.local.bloc_communal.taxe_fonciere_tfpb_mde, 2),
            statut_pde_europe=self.europe.statut_pde_actif,
            bouclier_tpi_actif=self.europe.bouclier_tpi_bce_eligible,
            sanction_financiere_ue=self.europe.amende_sanction_semestrielle_mde > 0,
            taux_oat_pct=round(self.mondial.taux_oat_france_10ans, 2),
            spread_bund_bps=round(self.mondial.spread_oat_bund_bps, 1),
            note_souveraine=self.mondial.note_souveraine,
            taux_credit_pme=round(self.mondial.taux_credit_pme_entreprises, 2),
            cours_petrole_usd=round(self.mondial.cours_petrole_brent_usd, 1),
            taux_change_eur_usd=round(self.mondial.taux_change_eur_usd, 3),
            facture_energetique_mde=round(self.mondial.facture_energetique_nette_mde, 1),
            inflation_globale_pct=round(self.mondial.inflation_globale_pct, 2),
            # Indicateurs des Assemblées
            voix_censure_an=voix_censure,
            gouvernement_censure=gouv_censure,
            climat_assemblee_nationale=climat_an,
            hostilite_senat_indice=round(hostilite_senat, 1),
            senat_veto_art_89=senat_veto,
            congres_majorite_3_5=congres_ok,
            departements_alerte_ciseau=dep_faillite,
            fronde_maires_indice=round(fronde_maires, 1),
            pe_taux_alignement=round(pe_alignement, 1),
            cese_consensus_social=round(cese_consensus, 1),
            consulaire_confiance_pme=round(conf_cci, 1),
            convention_citoyenne_consensus=round(consensus_citoyen, 1),
            commentaires=commentaires,
        )

        self.historique_etapes.append(resultat)
        return resultat
