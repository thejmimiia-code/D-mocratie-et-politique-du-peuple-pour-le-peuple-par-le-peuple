"""
simulateur/interface.py — Interface web du simulateur interactif.

Le module expose `HTML_PAGE` : une page unique (aucune dépendance externe,
aucun CDN) qui contient :

  * la barre de contexte « instant T » (données réelles, provenance, licences) ;
  * la **console de veille permanente** (`console-pilotage`) : verdict par strate,
    messages de seuil (tolérable → vigilance → risqué → hors-sol), risque pour la
    population, marges de manœuvre restantes et effet de la dernière modification ;
  * la cascade des 5 échelons systémiques, recalculée à chaque simulation ;
  * la grille des scénarios types (9 situations historiques du dépôt) ;
  * les préréglages doctrinaux additionnels ;
  * 93 leviers de politique publique réglables (curseurs, interrupteurs) ;
  * les 20 domaines d'action publique avec leurs indicateurs et mini-graphes ;
  * la matrice croisée levier × domaine (impacts calculés par le modèle) ;
  * le journal causal du moteur et les exports JSON/CSV ;
  * un bouton « Rafraîchir les données » qui interroge les API publiques
    directement depuis le navigateur (Eurostat, BCE, Frankfurter, World Bank…)
    puis renvoie les valeurs au serveur via `POST /api/donnees`.

Le JavaScript est volontairement sans framework : la page doit rester lisible
et auditables par des non-informaticiens, conformément à l'esprit du projet.
"""

from __future__ import annotations

#: ⚠️ Le placeholder `===SCENARIOS_JSON===` est remplacé à la volée par le
#: catalogue des scénarios historiques (nom, description, couleur) — il doit
#: rester littéral dans ce fichier.
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Simulateur Macro-Politique — Démocratie et politique du peuple</title>
<style>
:root{
  --bg:#0b1220; --panel:#131c2f; --panel-2:#1a2540; --border:#26324d;
  --texte:#e6edf7; --texte-dim:#93a3bd; --accent:#38bdf8; --vert:#22c55e;
  --rouge:#ef4444; --ambre:#f59e0b; --violet:#a855f7; --rose:#ec4899;
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',Roboto,system-ui,sans-serif;background:
  radial-gradient(1200px 600px at 50% -10%,#16233d 0%,var(--bg) 60%);
  color:var(--texte);min-height:100vh;padding:18px;line-height:1.45}
.conteneur{max-width:1560px;margin:0 auto}
a{color:var(--accent)}
header.entete{background:linear-gradient(135deg,#12305c,#2b1e56);border:1px solid var(--border);
  border-radius:14px;padding:18px 22px;margin-bottom:14px;box-shadow:0 10px 30px rgba(0,0,0,.35)}
header.entete h1{font-size:1.45rem;letter-spacing:.2px}
header.entete p{color:var(--texte-dim);font-size:.88rem;margin-top:4px}
.barre-contexte{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:12px}
.pastille{border-radius:999px;padding:4px 12px;font-size:.75rem;border:1px solid var(--border);
  background:var(--panel);color:var(--texte-dim);white-space:nowrap}
.pastille.live{border-color:var(--vert);color:#bbf7d0;background:rgba(34,197,94,.12)}
.pastille.reference{border-color:var(--ambre);color:#fde68a;background:rgba(245,158,11,.12)}
.pastille.mixte{border-color:var(--accent);color:#bae6fd;background:rgba(56,189,248,.12)}
button{font-family:inherit;font-size:.82rem;cursor:pointer;border-radius:9px;border:1px solid var(--border);
  background:var(--panel-2);color:var(--texte);padding:8px 13px;transition:.15s}
button:hover:not(:disabled){border-color:var(--accent);transform:translateY(-1px)}
button:disabled{opacity:.45;cursor:not-allowed}
button.primaire{background:linear-gradient(135deg,#0284c7,#2563eb);border-color:#1d4ed8}
button.discret{background:transparent}
section.bloc{background:var(--panel);border:1px solid var(--border);border-radius:14px;
  padding:16px;margin-bottom:14px}
section.bloc > h2{font-size:1rem;margin-bottom:4px;display:flex;align-items:center;gap:8px}
section.bloc > h2 .aide{font-size:.75rem;color:var(--texte-dim);font-weight:400}
.grille{display:grid;gap:12px}
.grille.metrics{grid-template-columns:repeat(auto-fit,minmax(158px,1fr))}
.grille.scenarios{grid-template-columns:repeat(auto-fit,minmax(232px,1fr))}
.grille.domaines{grid-template-columns:repeat(auto-fit,minmax(330px,1fr))}
.carte{background:var(--panel-2);border:1px solid var(--border);border-radius:11px;padding:12px}
.metric .valeur{font-size:1.32rem;font-weight:600}
.metric .libelle{font-size:.74rem;color:var(--texte-dim);text-transform:uppercase;letter-spacing:.4px}
.metric .delta{font-size:.75rem;margin-top:2px}
.delta.hausse{color:var(--vert)} .delta.baisse{color:var(--rouge)} .delta.neutre{color:var(--texte-dim)}
.scenario-card{cursor:pointer;border-left:4px solid var(--accent);transition:.15s}
.scenario-card:hover{background:#22304f;transform:translateY(-2px)}
.scenario-card.actif{box-shadow:0 0 0 2px var(--accent) inset;background:#22304f}
.scenario-card h3{font-size:.9rem;margin-bottom:3px}
.scenario-card p{font-size:.76rem;color:var(--texte-dim)}
.strates-cascade{display:flex;flex-direction:column;gap:6px}
.strate{display:flex;justify-content:space-between;gap:14px;align-items:center;
  background:var(--panel-2);border:1px solid var(--border);border-left-width:4px;border-radius:10px;
  padding:9px 13px;font-size:.83rem}
.strate .titre{font-weight:600}
.strate .valeurs{display:flex;gap:14px;flex-wrap:wrap;color:var(--texte-dim);font-size:.79rem}
.strate .valeurs b{color:var(--texte)}
.leviers-grille{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}
.famille{background:var(--panel-2);border:1px solid var(--border);border-radius:11px;padding:12px}
.famille h3{font-size:.84rem;margin-bottom:8px;border-bottom:1px solid var(--border);padding-bottom:6px}
.levier{margin-bottom:11px}
.levier .ligne{display:flex;justify-content:space-between;gap:8px;font-size:.79rem;align-items:baseline}
.levier .nom{font-weight:500}
.levier .valeur{color:var(--accent);font-variant-numeric:tabular-nums;white-space:nowrap}
.levier .desc{font-size:.7rem;color:var(--texte-dim);margin-top:2px}
.levier input[type=range]{width:100%;margin-top:5px;accent-color:var(--accent)}
.levier .source{font-size:.66rem;color:#7b8aa5;font-style:italic;margin-top:3px}
.bascule{display:flex;align-items:center;gap:8px;font-size:.79rem;margin-bottom:9px}
.bascule input{width:18px;height:18px;accent-color:var(--vert)}
.recherche{width:100%;padding:9px 12px;border-radius:9px;border:1px solid var(--border);
  background:var(--panel-2);color:var(--texte);margin-bottom:10px}
.domaine{background:var(--panel-2);border:1px solid var(--border);border-radius:11px;padding:12px}
.domaine .tete{display:flex;justify-content:space-between;align-items:center;gap:10px}
.domaine .score{font-size:1.25rem;font-weight:700;font-variant-numeric:tabular-nums}
.domaine .ref{font-size:.7rem;color:var(--texte-dim)}
.domaine ul{list-style:none;margin-top:9px;font-size:.78rem}
.domaine li{display:flex;justify-content:space-between;gap:10px;padding:3px 0;
  border-bottom:1px dashed rgba(147,163,189,.18)}
.domaine li:last-child{border-bottom:none}
.domaine .indic{color:var(--texte-dim)}
table{width:100%;border-collapse:collapse;font-size:.78rem}
th,td{padding:6px 8px;text-align:right;border-bottom:1px solid var(--border);white-space:nowrap}
th:first-child,td:first-child{text-align:left}
thead th{color:var(--texte-dim);font-weight:600;position:sticky;top:0;background:var(--panel)}
.defilable{overflow:auto;max-height:430px;border-radius:9px;border:1px solid var(--border)}
.matrice td,.matrice th{text-align:center}
.matrice td.pos{background:rgba(34,197,94,.18);color:#bbf7d0}
.matrice td.neg{background:rgba(239,68,68,.16);color:#fecaca}
.matrice td.vide{color:#42506b}
.journal{max-height:260px;overflow:auto;font-size:.78rem;color:var(--texte-dim)}
.journal div{padding:3px 0;border-bottom:1px dashed rgba(147,163,189,.15)}
.alerte{background:rgba(245,158,11,.1);border:1px solid var(--ambre);color:#fde68a;
  border-radius:10px;padding:9px 12px;font-size:.78rem;margin-bottom:10px}
.svg-chart{width:100%;height:210px;background:var(--panel-2);border-radius:10px;border:1px solid var(--border)}
.pied{color:var(--texte-dim);font-size:.72rem;text-align:center;padding:14px 0 26px}
.provenance{font-size:.73rem;color:var(--texte-dim);max-height:210px;overflow:auto}
.provenance div{padding:3px 0;border-bottom:1px dashed rgba(147,163,189,.15)}
.onglets{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.onglets button.actif{background:linear-gradient(135deg,#0284c7,#2563eb);border-color:#1d4ed8}
/* ── Console de veille permanente ─────────────────────────────────────── */
.console{position:sticky;top:8px;z-index:40;border-width:2px;
  box-shadow:0 12px 34px rgba(0,0,0,.45);backdrop-filter:blur(3px)}
.console.niveau-favorable,.console.niveau-tolerable{border-color:rgba(34,197,94,.55)}
.console.niveau-vigilance{border-color:rgba(245,158,11,.65)}
.console.niveau-risque{border-color:rgba(239,68,68,.7)}
.console.niveau-hors_sol{border-color:var(--rouge);
  box-shadow:0 0 0 3px rgba(239,68,68,.28),0 12px 34px rgba(0,0,0,.5)}
.console-entete{display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap}
.console-verdict{font-weight:700;font-size:.85rem;padding:7px 14px;border-radius:999px;
  border:1px solid var(--border);max-width:720px}
.console-strates{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:8px;margin:12px 0}
.strate-puce{border:1px solid var(--border);border-left-width:5px;border-radius:9px;padding:7px 10px;
  background:var(--panel-2);font-size:.74rem}
.strate-puce b{display:block;font-size:.78rem;margin-bottom:2px}
.console-corps{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:14px}
.console-titre{font-size:.78rem;text-transform:uppercase;letter-spacing:.5px;color:var(--texte-dim);
  margin:8px 0 6px}
.niveau-favorable{color:#bbf7d0}.niveau-tolerable{color:#bbf7d0}.niveau-vigilance{color:#fde68a}
.niveau-risque{color:#fecaca}.niveau-hors_sol{color:#fff;background:rgba(239,68,68,.22)}
.strate-puce.niveau-hors_sol{border-color:var(--rouge)}
.message-seuil{border-left:3px solid var(--border);padding:6px 10px;margin-bottom:7px;
  font-size:.76rem;background:var(--panel-2);border-radius:0 8px 8px 0}
.message-seuil .tete{display:flex;justify-content:space-between;gap:8px;align-items:baseline}
.message-seuil .etiquette{font-size:.68rem;text-transform:uppercase;letter-spacing:.4px;font-weight:700}
.message-seuil p{color:var(--texte-dim);margin-top:3px}
.message-seuil .source{font-size:.66rem;color:#7b8aa5;font-style:italic;margin-top:3px;display:block}
.jauge{height:11px;border-radius:7px;background:#22304f;overflow:hidden;border:1px solid var(--border)}
.jauge > span{display:block;height:100%;transition:width .25s}
.graduations{display:flex;justify-content:space-between;font-size:.64rem;color:var(--texte-dim);margin-top:3px}
.ligne-marge{display:flex;justify-content:space-between;gap:10px;font-size:.75rem;padding:4px 0;
  border-bottom:1px dashed rgba(147,163,189,.18)}
.ligne-marge .droite{color:var(--texte-dim);white-space:nowrap}
.bandeau-hors-sol{background:linear-gradient(90deg,rgba(239,68,68,.35),rgba(239,68,68,.06));
  border:1px solid var(--rouge);border-radius:10px;padding:9px 12px;font-size:.79rem;margin-top:10px}
.bandeau-hors-sol b{font-size:.82rem;letter-spacing:.3px}
.delta-mesure{font-size:.75rem;padding:4px 0;border-bottom:1px dashed rgba(147,163,189,.18);
  display:flex;justify-content:space-between;gap:10px}
.delta-mesure .valeur{font-variant-numeric:tabular-nums;white-space:nowrap}
@media(max-width:640px){body{padding:10px}header.entete h1{font-size:1.15rem}
  .console{position:static}.console-corps{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="conteneur">

  <header class="entete">
    <h1>Simulateur Macro-Politique — Démocratie et politique, du peuple, pour le peuple, par le peuple</h1>
    <p>Choisissez vos politiques : le modèle à 5 échelons propage les effets, domaine par domaine, avec les données publiques réelles du jour.</p>
    <div class="barre-contexte">
      <span class="pastille" id="badge-contexte">contexte : chargement…</span>
      <span class="pastille" id="badge-date">—</span>
      <span class="pastille" id="badge-leviers">—</span>
      <button class="primaire" id="btn-rafraichir" onclick="rafraichirDonnees()">Rafraîchir les données (API publiques)</button>
      <button class="discret" onclick="reinitialiser()">Réinitialiser les leviers</button>
      <button class="primaire" id="btn-simuler" onclick="simuler(true)">Simuler avec impacts croisés</button>
      <button id="btn-export-json" disabled onclick="exporter('json')">Export JSON</button>
      <button id="btn-export-csv" disabled onclick="exporter('csv')">Export CSV</button>
    </div>
  </header>

  <div id="zone-alertes"></div>

  <section class="bloc">
    <h2>Contexte « instant T » <span class="aide">données publiques réellement collectées, avec provenance et licence</span></h2>
    <div class="grille metrics" id="grid-metrics"></div>
  </section>

  <section class="bloc console" id="console-pilotage">
    <div class="console-entete">
      <h2>Console de veille permanente <span class="aide">seuils tolérables → hors-sol, strate par strate, mis à jour à chaque réglage</span></h2>
      <div class="console-verdict" id="console-verdict">en attente de la première simulation…</div>
    </div>
    <div id="console-danger"></div>
    <div class="console-strates" id="console-strates"></div>
    <div class="console-corps">
      <div>
        <h3 class="console-titre">Risque pour la population</h3>
        <div id="console-population"></div>
        <h3 class="console-titre">Effet de votre dernière modification</h3>
        <div id="console-derniere-modification"></div>
      </div>
      <div>
        <h3 class="console-titre">Messages de seuil</h3>
        <div id="console-alertes"></div>
        <h3 class="console-titre">Marges de manœuvre et audaces possibles</h3>
        <div id="console-marges"></div>
      </div>
    </div>
  </section>

  <section class="bloc">
    <h2>Surface d'impact de vos choix <span class="aide">recettes, dépenses et solde des mesures activées (année 5)</span></h2>
    <div class="grille metrics" id="grid-impact"></div>
  </section>

  <section class="bloc">
    <h2>Cascade systémique des 5 échelons <span class="aide">locale → nationale → européenne → mondiale → géopolitique</span></h2>
    <div class="strates-cascade" id="strates-cascade"></div>
  </section>

  <section class="bloc">
    <h2>Scénarios types du dépôt <span class="aide">9 situations rejouées par le moteur d'origine, année par année — pour comparaison</span></h2>
    <div class="grille scenarios" id="scenario-grid"></div>
  </section>

  <section class="bloc">
    <h2>Préréglages doctrinaux <span class="aide">des combinaisons cohérentes de leviers, chargées dans le simulateur puis ajustables curseur par curseur</span></h2>
    <div class="grille scenarios" id="preset-grid"></div>
  </section>

  <section class="bloc">
    <h2>Vos leviers <span class="aide">93 paramètres : fiscalité, dépenses, réformes, énergie, institutions, chocs mondiaux</span></h2>
    <input class="recherche" id="recherche-levier" placeholder="Rechercher un levier (ex. TVA, défense, RIC, retraites…)" oninput="filtrerLeviers(this.value)">
    <div class="leviers-grille" id="leviers-grille"></div>
  </section>

  <section class="bloc">
    <h2>Résultats année par année <span class="aide">tableau détaillé des 5 échelons</span></h2>
    <div class="defilable"><table id="results-table"></table></div>
  </section>

  <section class="bloc">
    <h2>Trajectoires clés <span class="aide">déficit, dette, taux OAT, tension sociale et confiance</span></h2>
    <svg class="svg-chart" id="svg-chart" viewBox="0 0 900 210" preserveAspectRatio="none"></svg>
  </section>

  <section class="bloc">
    <h2>Domaines d'action publique <span class="aide">score 0-100 (50 = situation de départ) et indicateurs concrets</span></h2>
    <div class="grille domaines" id="domaines-grille"></div>
  </section>

  <section class="bloc">
    <h2>Matrice croisée levier × domaine <span class="aide">effet marginal de chaque levier actif, calculé par le modèle (différences finies)</span></h2>
    <div class="defilable"><table class="matrice" id="matrice-impacts"></table></div>
  </section>

  <section class="bloc">
    <h2>Journal causal du moteur <span class="aide">rétroactions générées année par année</span></h2>
    <div class="journal" id="journal"></div>
  </section>

  <section class="bloc">
    <h2>Sources, licences et fraîcheur <span class="aide">ce que le simulateur sait, et ce qu'il ne sait pas</span></h2>
    <div class="provenance" id="provenance"></div>
  </section>

  <p class="pied">
    Projet citoyen open-source — « gouvernement du peuple, par le peuple et pour le peuple »
    (Constitution du 4 octobre 1958, article 2). Les chiffres publics sont cités avec leur source ;
    les coefficients d'impact sont documentés dans chaque formule et modifiables.
  </p>
</div>

<script>
const SCENARIOS = ===SCENARIOS_JSON===;
const LIBELLES_NIVEAUX = {favorable:'favorable', tolerable:'tolérable', vigilance:'vigilance',
                          risque:'risqué', hors_sol:'hors-sol', inconnu:'non mesuré'};
//: Ce que la console surveille pour juger une modification (−1 : plus bas = mieux).
const EFFETS_SURVEILLES = [
  ['deficit_final_pct','Déficit (% du PIB)', -1, 2],
  ['dette_finale_pct','Dette (% du PIB)', -1, 1],
  ['taux_oat_final','OAT 10 ans (%)', -1, 2],
  ['spread_final_bps','Spread face au Bund (bps)', -1, 0],
  ['charge_dette_finale_mde','Charge de la dette (Md€/an)', -1, 1],
  ['tension_finale','Tension sociale', -1, 1],
  ['confiance_finale','Confiance démocratique', 1, 1],
  ['risque_censure_final_pct','Risque de censure (%)', -1, 0],
  ['solde_mesures_mde','Solde des mesures (Md€)', 1, 1],
  ['score_moyen_domaines','Score moyen des domaines', 1, 1]
];
let CATALOGUE = null;
let CONTEXTE = null;
let SORTIE = null;
let PARAMS = {};
//: Simulation précédente (paramètres envoyés + sortie) : c'est elle qui permet
//: d'afficher la conséquence de la DERNIÈRE modification, en direct.
let SIMULATION_PRECEDENTE = null;

function fmt(valeur, precision){
  if (valeur === null || valeur === undefined || Number.isNaN(valeur)) return '—';
  const p = (precision === undefined) ? 1 : precision;
  return Number(valeur).toLocaleString('fr-FR', {minimumFractionDigits:p, maximumFractionDigits:p});
}
function couleurDelta(valeur){
  if (Math.abs(valeur) < 0.05) return 'neutre';
  return valeur > 0 ? 'hausse' : 'baisse';
}
function pastille(mode){
  const libelles = {live:'données live', reference:'référence datée 2026-10-05', mixte:'données mixtes'};
  return `<span class="pastille ${mode}">${libelles[mode] || mode}</span>`;
}

/* ── Chargement du catalogue (leviers + domaines) ───────────────────────── */
async function chargerCatalogue(){
  const reponse = await fetch('/api/catalogue');
  CATALOGUE = await reponse.json();
  PARAMS = Object.assign({}, CATALOGUE.parametres.defauts);
  renderLeviers('');
  renderPresets();
}

/* ── Contexte « instant T » ─────────────────────────────────────────────── */
async function chargerContexte(rafraichir){
  const reponse = await fetch(`/api/contexte?refresh=${rafraichir ? '1' : '0'}`);
  CONTEXTE = await reponse.json();
  renderContexte();
}
function renderContexte(){
  const c = CONTEXTE.contexte;
  document.getElementById('badge-contexte').outerHTML = pastille(c.mode).replace('<span', '<span id="badge-contexte"');
  document.getElementById('badge-date').textContent = `horodatage : ${c.horodatage.replace('T',' ').slice(0,16)} UTC`;
  const metriques = [
    ['PIB nominal', fmt(c.pib_nominal_mde, 0) + ' Md€', ''],
    ['Dette publique', fmt(c.dette_publique_pct_pib, 1) + ' % PIB', ''],
    ['Déficit public', fmt(c.deficit_public_pct_pib, 1) + ' % PIB', ''],
    ['OAT 10 ans', fmt(c.taux_oat_10ans, 2) + ' %', 'spread ' + fmt(c.spread_oat_bund_bps, 0) + ' bps vs Bund'],
    ['Taux BCE (dépôt)', fmt(c.taux_bce_depot, 2) + ' %', ''],
    ['Inflation France', fmt(c.inflation_pct, 1) + ' %', 'zone euro ' + fmt(c.inflation_zone_euro_pct, 1) + ' %'],
    ['Chômage', fmt(c.chomage_pct, 1) + ' %', ''],
    ['Pétrole Brent', fmt(c.brent_usd, 2) + ' $/baril', ''],
    ['Change EUR/USD', fmt(c.eur_usd, 4), ''],
    ['Pauvreté (60 % médian)', fmt(c.taux_pauvrete_pct, 1) + ' %', 'Gini ' + fmt(c.indice_gini, 1)],
    ['Charge de la dette estimée', fmt(c.charge_dette_estimee_mde, 1) + ' Md€/an', ''],
    ['Prélèvements obligatoires', fmt(c.prelevements_obligatoires_pct_pib, 1) + ' % PIB', ''],
  ];
  document.getElementById('grid-metrics').innerHTML = metriques.map(([libelle, valeur, sous]) =>
    `<div class="carte metric"><div class="libelle">${libelle}</div>
      <div class="valeur">${valeur}</div><div class="delta neutre">${sous}</div></div>`).join('');
  const provenance = (CONTEXTE.contexte && CONTEXTE.contexte.provenance) || CONTEXTE.provenance || {};
  const lignes = Object.entries(provenance).map(([champ, info]) => {
    const statut = info.statut === 'live' ? '🟢 live' : (info.statut === 'reference' ? '🟠 référence' : '⚪ non collectée');
    const periode = info.periode ? ` · ${info.periode}` : '';
    return `<div><b>${info.libelle}</b> : ${statut}${periode} · ${info.source}
      ${info.url ? ` · <a href="${info.url}" target="_blank" rel="noopener">source</a>` : ''}
      ${info.licence ? ` · <i>${info.licence}</i>` : ''}</div>`;
  }).join('');
  const complementaires = Object.values((CONTEXTE.contexte && CONTEXTE.contexte.series_complementaires) || {});
  const blocComplementaire = complementaires.length
    ? '<div style="margin-top:10px"><b>Séries complémentaires collectées</b> (non utilisées pour le calibrage,'
      + ' conservées pour information) :<br>' + complementaires.map(info =>
        `${info.libelle} : ${fmt(info.valeur, 2)} ${info.unite} (${info.periode || '—'}) — <i>${info.licence}</i>`
      ).join('<br>') + '</div>'
    : '';
  document.getElementById('provenance').innerHTML = lignes + blocComplementaire
    + '<div style="margin-top:8px">Rappel : le mode « référence » signifie que le serveur n\'a pas pu (ou pas encore)'
    + ' interroger les API publiques. Le bouton « Rafraîchir les données » interroge directement vos API'
    + ' depuis le navigateur (puis relaie par le serveur les sources sans CORS), et transmet les valeurs au simulateur.</div>'
    + '<div style="margin-top:8px"><b>Comment lire les scores :</b> chaque domaine est noté de 0 à 100 par rapport à la'
    + ' <b>trajectoire de référence modélisée</b> (aucun levier activé) : 50 = référence, au-dessus = amélioration attendue,'
    + ' en dessous = dégradation. Les écarts affichés sont donc des <b>écarts de politique publique</b>, jamais des niveaux absolus.</div>';
}

/* ── Rafraîchissement navigateur → serveur (adapte les mêmes API) ───────── */
function extraireEurostat(charge, chemin){
  const valeur = charge.value || {};
  const cles = Object.keys(valeur);
  if (!cles.length) return null;
  let cle = chemin && valeur[chemin] !== undefined ? chemin : cles[cles.length - 1];
  let periode = null;
  try {
    const temps = charge.dimension.time.category.index;
    const codes = Object.keys(temps);
    periode = codes[Number(cle)] || codes[codes.length - 1];
  } catch (erreur) { periode = null; }
  return {valeur: Number(valeur[cle]), periode: periode};
}
function extraireSdmx(charge, chemin){
  const jeux = charge.dataSets || [];
  if (!jeux.length) return null;
  const series = jeux[0].series || {};
  const premiere = series[Object.keys(series)[0]];
  const observations = (premiere && premiere.observations) || {};
  const cles = Object.keys(observations);
  if (!cles.length) return null;
  const brut = observations[cles[0]];
  const valeur = Array.isArray(brut) ? brut[0] : brut;
  let periode = null;
  try {
    const dims = charge.structure.dimensions.observation || [];
    const temps = dims.find(d => d.role === 'time');
    if (temps && temps.values.length) periode = temps.values[0].id;
  } catch (erreur) { periode = null; }
  return {valeur: Number(valeur), periode: periode};
}
function extraireGenerique(adaptateur, charge, chemin){
  if (adaptateur === 'eurostat') return extraireEurostat(charge, chemin);
  if (adaptateur === 'sdmx') return extraireSdmx(charge, chemin);
  if (adaptateur === 'frankfurter'){
    const taux = charge.rates || {};
    const devise = chemin || Object.keys(taux)[0];
    if (taux[devise] === undefined) return null;
    return {valeur: Number(taux[devise]), periode: charge.date || null};
  }
  if (adaptateur === 'opendatasoft'){
    const resultats = charge.results || [];
    if (!resultats.length) return null;
    let brut = resultats[0];
    (chemin || '').split('.').forEach(morceau => { if (brut && brut[morceau] !== undefined) brut = brut[morceau]; });
    return {valeur: Number(brut), periode: resultats[0].date || null};
  }
  if (adaptateur === 'worldbank'){
    const obs = (charge[1] || [])[0];
    if (!obs || obs.value === null) return null;
    return {valeur: Number(obs.value), periode: obs.date || null};
  }
  if (adaptateur === 'yahoo'){
    const resultats = (charge.chart && charge.chart.result) || [];
    if (!resultats.length) return null;
    const meta = resultats[0].meta || {};
    if (meta.regularMarketPrice === undefined) return null;
    const date = meta.regularMarketTime ? new Date(meta.regularMarketTime * 1000).toISOString().slice(0,10) : null;
    return {valeur: Number(meta.regularMarketPrice), periode: date};
  }
  return null;
}
async function rafraichirDonnees(){
  const bouton = document.getElementById('btn-rafraichir');
  bouton.disabled = true; bouton.textContent = 'Interrogation des API publiques…';
  const spec = CONTEXTE.browser || {};
  const lectures = {};
  let succes = 0;
  for (const [cle, indicateur] of Object.entries(spec)){
    for (const source of indicateur.sources){
      try {
        const reponse = await fetch(source.url, {mode:'cors'});
        if (!reponse.ok) continue;
        const charge = await reponse.json();
        const lecture = extraireGenerique(source.adaptateur, charge, source.chemin);
        if (!lecture || !Number.isFinite(lecture.valeur)) continue;
        lectures[cle] = {cle: cle, valeur: lecture.valeur, periode: lecture.periode,
                         fournisseur: source.fournisseur, url: source.url, statut: 'live'};
        succes += 1;
        break;
      } catch (erreur) { /* source suivante */ }
    }
    if (!lectures[cle] && indicateur.proxy_url){
      // Repli même-origine : le serveur relaie les sources sans CORS
      // (Yahoo, Stooq, ICE/EEX). Le serveur n'accepte que les sources
      // déclarées au registre : ce n'est pas un proxy ouvert.
      try {
        const reponse = await fetch(indicateur.proxy_url);
        if (reponse.ok){
          const charge = await reponse.json();
          const lecture = charge.lecture;
          if (lecture && Number.isFinite(Number(lecture.valeur))){
            lectures[cle] = {cle: cle, valeur: Number(lecture.valeur), periode: lecture.periode,
                             fournisseur: lecture.fournisseur, url: lecture.url,
                             statut: lecture.statut === 'live' ? 'live' : 'reference'};
            if (lecture.statut === 'live') succes += 1;
          }
        }
      } catch (erreur) { /* le serveur garde ses valeurs */ }
    }
  }
  if (succes > 0){
    try {
      await fetch('/api/donnees', {method:'POST', headers:{'Content-Type':'application/json'},
                                   body: JSON.stringify({lectures: lectures})});
    } catch (erreur) { /* le serveur reste sur ses valeurs */ }
  }
  await chargerContexte(false);
  bouton.disabled = false;
  bouton.textContent = succes > 0
    ? `Rafraîchir les données (${succes} séries mises à jour)`
    : 'Rafraîchir les données (aucune source joignable)';
  if (SORTIE) simuler(false);
}

/* ── Leviers ────────────────────────────────────────────────────────────── */
function renderLeviers(filtre){
  const recherche = (filtre || '').toLowerCase();
  const zones = CATALOGUE.parametres.familles.map(famille => {
    const leviers = famille.leviers.filter(levier =>
      !recherche || levier.libelle.toLowerCase().includes(recherche)
      || levier.description.toLowerCase().includes(recherche)
      || levier.cle.includes(recherche));
    if (!leviers.length) return '';
    const contenu = leviers.map(levier => {
      const valeur = PARAMS[levier.cle];
      const valeurTexte = levier.type === 'interrupteur'
        ? (valeur >= 0.5 ? 'activé' : 'désactivé')
        : `${fmt(valeur, levier.precision)} ${levier.unite === 'bool' ? '' : levier.unite}`;
      const commande = levier.type === 'interrupteur'
        ? `<label class="bascule"><input type="checkbox" ${valeur >= 0.5 ? 'checked' : ''}
             onchange="majLevier('${levier.cle}', this.checked ? 1 : 0)"> ${levier.libelle}
             <span class="valeur">${valeurTexte}</span></label>`
        : `<div class="ligne"><span class="nom">${levier.libelle}</span>
             <span class="valeur">${valeurTexte}</span></div>
           <input type="range" min="${levier.minimum}" max="${levier.maximum}" step="${levier.pas}"
                  value="${valeur}" oninput="majLevier('${levier.cle}', parseFloat(this.value))">`;
      return `<div class="levier" data-cle="${levier.cle}">
        ${commande}
        <div class="desc">${levier.description}</div>
        ${levier.source ? `<div class="source">Source : ${levier.source}</div>` : ''}
      </div>`;
    }).join('');
    return `<div class="famille"><h3 style="color:${famille.couleur}">${famille.libelle}</h3>${contenu}</div>`;
  }).join('');
  document.getElementById('leviers-grille').innerHTML = zones
    || '<div class="carte">Aucun levier ne correspond à cette recherche.</div>';
}
function filtrerLeviers(valeur){ renderLeviers(valeur); }
function majLevier(cle, valeur){
  PARAMS[cle] = valeur;
  const carte = document.querySelector(`.levier[data-cle="${cle}"]`);
  if (carte){
    const levier = CATALOGUE.parametres.familles.flatMap(f => f.leviers).find(l => l.cle === cle);
    const cible = carte.querySelector('.valeur');
    if (cible && levier){
      cible.textContent = levier.type === 'interrupteur'
        ? (valeur >= 0.5 ? 'activé' : 'désactivé')
        : `${fmt(valeur, levier.precision)} ${levier.unite}`;
    }
  }
  planifierSimulation();
}
let minuteur = null;
function planifierSimulation(){
  document.getElementById('badge-leviers').textContent =
    `${nombreLeviersActifs()} leviers actifs — calcul en cours…`;
  if (minuteur) clearTimeout(minuteur);
  minuteur = setTimeout(() => simuler(false), 320);
}
function nombreLeviersActifs(){
  if (!CATALOGUE) return 0;
  const defauts = CATALOGUE.parametres.defauts;
  return Object.entries(PARAMS).filter(([cle, valeur]) =>
    Math.abs(valeur - defauts[cle]) > 1e-9).length;
}

/* ── Scénarios et préréglages ───────────────────────────────────────────── */
function renderScenarios(){
  const grid = document.getElementById('scenario-grid');
  grid.innerHTML = '';
  Object.entries(SCENARIOS).forEach(([key, scenario]) => {
    const card = document.createElement('div');
    card.className = 'scenario-card carte';
    card.style.borderLeftColor = scenario.couleur || '#38bdf8';
    card.dataset.key = key;
    card.innerHTML = `<h3>${scenario.nom}</h3><p>${scenario.description}</p>`;
    card.onclick = (ev) => runScenario(key, ev);
    grid.appendChild(card);
  });
}
function renderPresets(){
  const grid = document.getElementById('preset-grid');
  grid.innerHTML = '';
  Object.entries(CATALOGUE.parametres.presets).forEach(([key, preset]) => {
    const card = document.createElement('div');
    card.className = 'scenario-card carte';
    card.style.borderLeftColor = preset.couleur || '#38bdf8';
    card.innerHTML = `<h3>${preset.libelle}</h3><p>${preset.description}</p>`;
    card.onclick = (ev) => chargerPreset(key, ev);
    grid.appendChild(card);
  });
}
function chargerPreset(cle, ev){
  const preset = CATALOGUE.parametres.presets[cle];
  if (!preset) return;
  PARAMS = Object.assign({}, CATALOGUE.parametres.defauts, preset.parametres);
  renderLeviers(document.getElementById('recherche-levier').value);
  marquerCarteActive(ev, cle);
  simuler(true);
}
async function runScenario(scenario, ev){
  // Chemin « moteur d'origine » : les 9 scénarios du dépôt sont calculés par
  // les fabriques de scénarios, pas par le simulateur paramétrable. Le
  // bouton d'export reste celui de la dernière simulation paramétrique.
  const carte = ev?.target?.closest?.('.scenario-card')
    || document.querySelector(`.scenario-card[data-key="${scenario}"]`);
  if (carte) carte.classList.add('actif');
  const reponse = await fetch(`/api/run?scenario=${scenario}`);
  const donnees = await reponse.json();
  if (donnees.error){ alert('Erreur : ' + donnees.error); return; }
  afficherScenarioHistorique(donnees);
  activerExports();
}
function marquerCarteActive(ev, cle){
  document.querySelectorAll('.scenario-card').forEach(carte => carte.classList.remove('actif'));
  const carte = ev?.target?.closest?.('.scenario-card') || document.querySelector(`.scenario-card[data-key="${cle}"]`);
  if (carte) carte.classList.add('actif');
}
function afficherScenarioHistorique(donnees){
  const final = donnees.resultats[donnees.resultats.length - 1];
  document.getElementById('grid-impact').innerHTML = `
    <div class="carte metric"><div class="libelle">Scénario historique</div>
      <div class="valeur">${donnees.nom}</div>
      <div class="delta neutre">résultats du moteur d'origine (5 ans)</div></div>
    <div class="carte metric"><div class="libelle">Déficit année 5</div>
      <div class="valeur">${fmt(final.ratio_deficit_pib, 2)} % PIB</div>
      <div class="delta ${couleurDelta(-final.ratio_deficit_pib)}">dette ${fmt(final.ratio_dette_pib, 1)} % PIB</div></div>
    <div class="carte metric"><div class="libelle">OAT 10 ans</div>
      <div class="valeur">${fmt(final.taux_oat_pct, 2)} %</div>
      <div class="delta neutre">spread ${fmt(final.spread_bund_bps, 0)} bps</div></div>
    <div class="carte metric"><div class="libelle">Tension sociale</div>
      <div class="valeur">${fmt(final.tension_sociale_locale, 1)}/100</div>
      <div class="delta neutre">confiance ${fmt(final.confiance_democratique, 1)}/100</div></div>`;
  renderTableau(donnees.resultats);
  document.getElementById('badge-leviers').textContent =
    `scénario « ${donnees.nom} » — 5 exercices simulés`;
  activerExports();
}

/* ── Simulation paramétrique ────────────────────────────────────────────── */
async function simuler(avecImpacts){
  const bouton = document.getElementById('btn-simuler');
  bouton.disabled = true;
  const parametresEnvoyes = Object.assign({}, PARAMS);
  try {
    const reponse = await fetch('/api/simuler', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({parametres: parametresEnvoyes, avec_impacts: !!avecImpacts, max_impacts: 16})
    });
    const donnees = await reponse.json();
    if (donnees.error){ alert('Erreur de simulation : ' + donnees.error); return; }
    SORTIE = donnees;
    renderImpact(donnees);
    renderStrates(donnees);
    renderTableau(donnees.etapes);
    renderGraphique(donnees.etapes);
    renderDomaines(donnees);
    renderMatrice(donnees);
    renderJournal(donnees);
    renderAlertes(donnees);
    renderConsole(donnees);
    renderDerniereModification(SIMULATION_PRECEDENTE,
                               {parametres: parametresEnvoyes, sortie: donnees});
    SIMULATION_PRECEDENTE = {parametres: parametresEnvoyes, sortie: donnees};
    document.getElementById('badge-leviers').textContent =
      `${nombreLeviersActifs()} leviers actifs · score moyen ${fmt(donnees.synthese.score_moyen_domaines,1)} (référence ${fmt(donnees.synthese.score_moyen_reference,1)})`;
    activerExports();
  } catch (erreur){
    alert('Le serveur n\'a pas répondu : ' + erreur);
  } finally {
    bouton.disabled = false;
  }
}
function renderAlertes(donnees){
  const alertes = (donnees.avertissements || []).map(texte => `<div class="alerte">${texte}</div>`).join('');
  document.getElementById('zone-alertes').innerHTML = alertes;
}


/* ── Console de veille permanente ───────────────────────────────────────── */
function classeNiveau(niveau){ return 'niveau-' + (niveau || 'inconnu'); }
function etiquetteNiveau(niveau){ return LIBELLES_NIVEAUX[niveau] || niveau || 'non mesuré'; }

function renderConsole(donnees){
  const diagnostic = donnees.diagnostic;
  const verdictBoite = document.getElementById('console-verdict');
  const bloc = document.getElementById('console-pilotage');
  if (!diagnostic){
    bloc.className = 'bloc console';
    verdictBoite.className = 'console-verdict';
    verdictBoite.textContent = 'Diagnostic indisponible (serveur antérieur ?).';
    return;
  }
  const verdict = diagnostic.verdict || {};
  bloc.className = 'bloc console ' + classeNiveau(diagnostic.niveau_global);
  verdictBoite.className = 'console-verdict ' + classeNiveau(diagnostic.niveau_global);
  verdictBoite.textContent = `${etiquetteNiveau(diagnostic.niveau_global).toUpperCase()} — ${verdict.message || ''}`;

  // Bandeau d'alerte rouge : ce qui est déjà hors-sol.
  const horsSol = (diagnostic.indicateurs || []).filter(ind => ind.niveau === 'hors_sol');
  document.getElementById('console-danger').innerHTML = horsSol.length
    ? `<div class="bandeau-hors-sol"><b>⚠ HORS-SOL (${horsSol.length}) — la population ou l'État est exposé :</b><br>`
      + horsSol.map(ind => `${ind.libelle} : ${ind.valeur_texte} ${ind.unite} — strate ${ind.strate}`).join('<br>')
      + '</div>'
    : '';

  // Les cinq strates, du local au géopolitique.
  document.getElementById('console-strates').innerHTML = (diagnostic.strates || []).map(strate =>
    `<div class="strate-puce ${classeNiveau(strate.niveau)}">
       <b>${strate.libelle}</b>
       <span class="${classeNiveau(strate.niveau)}">${etiquetteNiveau(strate.niveau)}</span>
       <div class="aide">${strate.alertes.length} seuil(s) en alerte sur ${strate.indicateurs.length}</div>
     </div>`).join('');

  // Risque pour la population : jauge + piliers + consigne.
  const population = diagnostic.population || {};
  const risque = Number(population.valeur || 0);
  const couleur = risque <= 50 ? 'var(--vert)' : (risque <= 58 ? 'var(--ambre)'
    : (risque <= 68 ? '#fb923c' : 'var(--rouge)'));
  const piliers = (population.piliers || []).map(pilier => {
    const ecart = pilier.score - 50;
    return `<span class="delta ${couleurDelta(ecart)}">${pilier.cle.replace(/_/g,' ')} ${fmt(pilier.score,0)}</span>`;
  }).join(' · ');
  document.getElementById('console-population').innerHTML =
    `<div class="ligne-marge"><span>Indice de risque (0 = aucun, 100 = maximal)</span>
       <span class="droite ${classeNiveau(population.niveau)}">${fmt(risque,1)}/100 — ${etiquetteNiveau(population.niveau)}</span></div>
     <div class="jauge"><span style="width:${Math.max(2, Math.min(100, risque))}%;background:${couleur}"></span></div>
     <div class="graduations"><span>0</span><span>50 vigilance</span><span>58 risque</span><span>68 hors-sol</span><span>100</span></div>
     <div class="message-seuil ${classeNiveau(population.niveau)}"><p>${population.message || ''}</p></div>
     <div class="aide">Domaines suivis : ${piliers}</div>`;

  // Messages de seuil, du plus grave au plus doux.
  const alertes = (diagnostic.alertes || []);
  document.getElementById('console-alertes').innerHTML = alertes.length
    ? alertes.slice(0, 8).map(alerte =>
        `<div class="message-seuil ${classeNiveau(alerte.niveau)}">
           <div class="tete"><span>${alerte.libelle} · strate ${alerte.strate}</span>
             <span class="etiquette ${classeNiveau(alerte.niveau)}">${etiquetteNiveau(alerte.niveau)}</span></div>
           <p>${alerte.message}</p>
           ${alerte.source ? `<span class="source">Seuil : ${alerte.source}</span>` : ''}
         </div>`).join('')
    : '<div class="message-seuil"><p>Aucun seuil franchi : tous les garde-fous sont respectés.</p></div>';

  // Marges de manœuvre (ce qu'il reste avant le prochain seuil) et audaces.
  const marges = (diagnostic.marges || []).slice(0, 6).map(marge =>
    `<div class="ligne-marge"><span>${marge.libelle}</span>
       <span class="droite">${marge.valeur_texte} ${marge.unite} ·
         <b class="${classeNiveau(marge.prochain_niveau)}">${fmt(marge.marge, 2)} ${marge.unite}</b>
         avant « ${etiquetteNiveau(marge.prochain_niveau)} »</span></div>`).join('');
  const progres = (diagnostic.progres || []).slice(0, 4).map(progres =>
    `<div class="ligne-marge"><span>${progres.libelle}</span>
       <span class="droite">encore <b>${fmt(progres.ecart, 2)}</b> ${progres.unite} possibles avant ${progres.valeur_cible}</span></div>
     <div class="aide" style="margin:-2px 0 6px">${progres.message_cible || ''}</div>`).join('');
  document.getElementById('console-marges').innerHTML =
    (marges || '<div class="ligne-marge"><span>Aucune marge mesurable.</span></div>')
    + (progres ? `<h3 class="console-titre">Ce que vous pouvez encore oser</h3>${progres}` : '');
}

function renderDerniereModification(avant, apres){
  const zone = document.getElementById('console-derniere-modification');
  if (!avant || !apres){ zone.innerHTML = '<div class="aide">Chargez un préréglage ou bougez un curseur pour voir l\'effet d\'une mesure.</div>'; return; }
  const defauts = (CATALOGUE && CATALOGUE.parametres.defauts) || {};
  const leviers = Object.keys(apres.parametres).filter(cle =>
    Math.abs((apres.parametres[cle] || 0) - (avant.parametres[cle] || 0)) > 1e-9);
  const libelles = leviers.slice(0, 4).map(cle => {
    const levier = CATALOGUE.parametres.familles.flatMap(f => f.leviers).find(l => l.cle === cle);
    const valeur = apres.parametres[cle];
    const texte = (levier && levier.type === 'interrupteur')
      ? (valeur >= 0.5 ? 'activé' : 'désactivé')
      : `${fmt(valeur, levier ? levier.precision : 2)} ${levier && levier.unite !== 'bool' ? levier.unite : ''}`;
    const retour = defauts[cle] !== undefined && Math.abs(valeur - defauts[cle]) < 1e-9 ? ' (retour au neutre)' : '';
    return `${levier ? levier.libelle : cle} → ${texte}${retour}`;
  });
  const effets = [];
  EFFETS_SURVEILLES.forEach(([cle, libelle, sens, precision]) => {
    const a = avant.sortie.synthese[cle], b = apres.sortie.synthese[cle];
    if (a === undefined || b === undefined) return;
    const delta = b - a;
    if (Math.abs(delta) < Math.pow(10, -precision) / 2) return;
    const favorable = sens * delta > 0;
    effets.push({libelle: libelle, avant: a, apres: b, delta: delta,
                 sens: sens, precision: precision, favorable: favorable});
  });
  // Un domaine qui décroche est plus parlant qu'un agrégat : on signale le pire.
  let pireDomaine = null;
  const domainesAvant = {};
  (avant.sortie.domaines || []).forEach(d => { domainesAvant[d.cle] = d.score; });
  (apres.sortie.domaines || []).forEach(d => {
    const avantScore = domainesAvant[d.cle];
    if (avantScore === undefined) return;
    const delta = d.score - avantScore;
    if (Math.abs(delta) < 0.15) return;
    if (!pireDomaine || delta < pireDomaine.delta) pireDomaine = {libelle: d.libelle, delta: delta};
  });
  const favorables = effets.filter(e => e.favorable).length;
  const defavorables = effets.length - favorables;
  const verdict = effets.length === 0
    ? 'aucun effet mesurable sur les grandeurs surveillées'
    : (defavorables === 0 ? 'jugée favorable'
      : (favorables === 0 ? 'jugée défavorable' : `${favorables} effet(s) favorable(s), ${defavorables} défavorable(s)`));
  const niveauVerdict = effets.length === 0 ? 'inconnu'
    : (defavorables === 0 ? 'favorable' : (favorables === 0 ? 'risque' : 'vigilance'));

  zone.innerHTML =
    `<div class="message-seuil ${classeNiveau(niveauVerdict)}">
       <div class="tete"><span>${leviers.length ? leviers.length + ' levier(s) modifié(s)' : 'Aucun levier modifié'}</span>
         <span class="etiquette ${classeNiveau(niveauVerdict)}">${verdict}</span></div>
       ${libelles.length ? `<p>${libelles.join(' · ')}${leviers.length > libelles.length ? ` (+${leviers.length - libelles.length} autre(s))` : ''}</p>` : ''}
     </div>`
    + effets.map(effet =>
        `<div class="delta-mesure"><span>${effet.libelle} : ${fmt(effet.avant, effet.precision)} → ${fmt(effet.apres, effet.precision)}</span>
           <span class="valeur ${effet.favorable ? 'delta hausse' : 'delta baisse'}">
             ${effet.delta > 0 ? '+' : ''}${fmt(effet.delta, effet.precision)} ${effet.favorable ? '✓' : '✗'}</span></div>`).join('')
    + (pireDomaine ? `<div class="aide">Domaine le plus touché : <b>${pireDomaine.libelle}</b>
         (${pireDomaine.delta > 0 ? '+' : ''}${fmt(pireDomaine.delta, 1)} pt de score).</div>` : '');
}

function renderImpact(donnees){
  const s = donnees.synthese;
  const cartes = [
    ['Recettes nouvelles (an 5)', fmt(s.recettes_nouvelles_mde, 1) + ' Md€', 'mesures activées'],
    ['Dépenses nouvelles (an 5)', fmt(s.depenses_nouvelles_mde, 1) + ' Md€', 'mesures activées'],
    ['Solde des mesures', fmt(s.solde_mesures_mde, 1) + ' Md€',
      s.solde_mesures_mde >= 0 ? 'excédent de mesures' : 'coût net des mesures'],
    ['Déficit final', fmt(s.deficit_final_pct, 2) + ' % PIB',
      `référence ${fmt(s.deficit_reference_pct, 2)} % (écart ${fmt(s.deficit_ecart_pts, 2)} pt)`],
    ['Dette finale', fmt(s.dette_finale_pct, 1) + ' % PIB',
      `référence ${fmt(s.dette_reference_pct, 1)} %`],
    ['OAT 10 ans', fmt(s.taux_oat_final, 2) + ' %',
      `spread ${fmt(s.spread_final_bps, 0)} bps · note ${s.note_souveraine}`],
    ['Tension sociale', fmt(s.tension_finale, 1) + '/100',
      `confiance ${fmt(s.confiance_finale, 1)}/100`],
    ['Risque de censure', fmt(s.risque_censure_final_pct, 0) + ' %',
      s.statut_pde ? 'PDE active' : 'PDE : conforme'],
    ['Croissance cumulée', (s.croissance_supplementaire_pts >= 0 ? '+' : '') + fmt(s.croissance_supplementaire_pts, 2) + ' %',
      'PIB année 5 vs référence'],
    ['Domaines en hausse', String(s.nombre_domaines_en_hausse), `${s.nombre_domaines_en_baisse} en baisse`],
  ];
  document.getElementById('grid-impact').innerHTML = cartes.map(([libelle, valeur, sous]) =>
    `<div class="carte metric"><div class="libelle">${libelle}</div><div class="valeur">${valeur}</div>
      <div class="delta neutre">${sous}</div></div>`).join('');
}
function renderStrates(donnees){
  const dernier = donnees.etapes[donnees.etapes.length - 1];
  const strates = [
    ['Échelon 1 — Local', '#22c55e', [
      ['Tension sociale', fmt(dernier.tension_sociale_locale,1)+'/100'],
      ['Services de proximité', fmt(dernier.qualite_services_proximite,1)+'/100'],
      ['Taxe foncière', fmt(dernier.produit_taxe_fonciere_mde,1)+' Md€']]],
    ['Échelon 2 — National', '#38bdf8', [
      ['PIB', fmt(dernier.pib_nominal_mde,0)+' Md€'],
      ['Déficit', fmt(dernier.ratio_deficit_pib,2)+' % PIB'],
      ['Dette', fmt(dernier.ratio_dette_pib,1)+' % PIB'],
      ['Charge dette', fmt(dernier.charge_dette_mde,1)+' Md€'],
      ['Censure', fmt(dernier.risque_censure_parlement,0)+' %']]],
    ['Échelon 3 — Européen', '#a855f7', [
      ['PDE', dernier.statut_pde_europe ? 'ACTIVE' : 'conforme'],
      ['Bouclier TPI', dernier.bouclier_tpi_actif ? 'éligible' : 'suspendu']]],
    ['Échelon 4 — Mondial', '#f59e0b', [
      ['OAT 10 ans', fmt(dernier.taux_oat_pct,2)+' %'],
      ['Spread Bund', fmt(dernier.spread_bund_bps,0)+' bps'],
      ['Note', dernier.note_souveraine],
      ['Brent', fmt(dernier.cours_petrole_usd,1)+' $'],
      ['Inflation', fmt(dernier.inflation_globale_pct,2)+' %']]],
    ['Échelon 5 — Géopolitique', '#ef4444', [
      ['Tension géo', fmt(dernier.indice_tension_geopolitique,1)+'/100'],
      ['Chokepoints', dernier.chokepoints_sous_tension+'/7'],
      ['Défense', fmt(dernier.effort_defense_pct_pib,2)+' % PIB'],
      ['Semi-conducteurs', fmt(dernier.disponibilite_semiconducteurs_pct,0)+' %']]],
  ];
  document.getElementById('strates-cascade').innerHTML = strates.map(([titre, couleur, valeurs]) =>
    `<div class="strate" style="border-left-color:${couleur}">
       <span class="titre">${titre}</span>
       <span class="valeurs">${valeurs.map(([k,v]) => `<span>${k} : <b>${v}</b></span>`).join('')}</span>
     </div>`).join('');
}
function renderTableau(etapes){
  const colonnes = [
    ['annee','Année'],['pib_nominal_mde','PIB (Md€)'],['ratio_deficit_pib','Déficit (% PIB)'],
    ['ratio_dette_pib','Dette (% PIB)'],['charge_dette_mde','Charge dette (Md€)'],
    ['taux_oat_pct','OAT (%)'],['spread_bund_bps','Spread (bps)'],['note_souveraine','Note'],
    ['tension_sociale_locale','Tension'],['confiance_democratique','Confiance'],
    ['risque_censure_parlement','Censure (%)'],['effort_defense_pct_pib','Défense (% PIB)'],
    ['cours_petrole_usd','Brent ($)'],['inflation_globale_pct','Inflation (%)'],
    ['pouvoir_achat_index','Pouvoir achat'],['qualite_services_proximite','Services']
  ];
  const entete = colonnes.map(([, libelle]) => `<th>${libelle}</th>`).join('');
  const lignes = etapes.map(etape => `<tr>${colonnes.map(([cle]) =>
    `<td>${typeof etape[cle] === 'number' ? fmt(etape[cle], 2) : (etape[cle] ?? '—')}</td>`).join('')}</tr>`).join('');
  document.getElementById('results-table').innerHTML = `<thead><tr>${entete}</tr></thead><tbody>${lignes}</tbody>`;
}
function renderGraphique(etapes){
  const series = [
    ['Déficit (% PIB)','ratio_deficit_pib','#ef4444'],
    ['Dette (% PIB)','ratio_dette_pib','#f59e0b'],
    ['OAT (%)','taux_oat_pct','#38bdf8'],
    ['Tension','tension_sociale_locale','#a855f7'],
    ['Confiance','confiance_democratique','#22c55e'],
  ];
  const largeur = 900, hauteur = 210, marge = 30;
  const toutes = series.flatMap(([, cle]) => etapes.map(e => e[cle]));
  const maxi = Math.max(...toutes, 1), mini = Math.min(...toutes, 0);
  const x = index => marge + index * ((largeur - 2*marge) / Math.max(etapes.length - 1, 1));
  const y = valeur => hauteur - marge - ((valeur - mini) / Math.max(maxi - mini, 1)) * (hauteur - 2*marge);
  let svg = `<line x1="${marge}" y1="${hauteur-marge}" x2="${largeur-marge}" y2="${hauteur-marge}" stroke="#26324d"/>`;
  series.forEach(([libelle, cle, couleur]) => {
    const points = etapes.map((e, i) => `${x(i)},${y(e[cle])}`).join(' ');
    svg += `<polyline points="${points}" fill="none" stroke="${couleur}" stroke-width="2.5"/>`;
    etapes.forEach((e, i) => { svg += `<circle cx="${x(i)}" cy="${y(e[cle])}" r="3" fill="${couleur}"/>`; });
    svg += `<text x="${marge}" y="${18 + series.findIndex(s => s[1] === cle) * 15}" fill="${couleur}" font-size="12">${libelle}</text>`;
  });
  etapes.forEach((e, i) => {
    svg += `<text x="${x(i)}" y="${hauteur-10}" fill="#93a3bd" font-size="11" text-anchor="middle">Année ${e.annee}</text>`;
  });
  document.getElementById('svg-chart').innerHTML = svg;
}
function renderDomaines(donnees){
  document.getElementById('domaines-grille').innerHTML = donnees.domaines.map(domaine => {
    const ecart = domaine.score - domaine.score_reference;
    const deltaClasse = couleurDelta(ecart);
    const indicateurs = domaine.indicateurs.map(indicateur => {
      const variation = indicateur.variation_relative_pct;
      const favorable = indicateur.sens * variation >= 0;
      return `<li><span class="indic">${indicateur.libelle}</span>
        <span>${fmt(indicateur.valeur_finale, 1)} ${indicateur.unite}
        <span class="delta ${favorable ? 'hausse' : 'baisse'}">(${variation >= 0 ? '+' : ''}${fmt(variation,1)} %)</span></span></li>`;
    }).join('');
    return `<div class="domaine" style="border-top:3px solid ${domaine.couleur}">
      <div class="tete">
        <div><b>${domaine.libelle}</b><div class="ref">${domaine.description}</div></div>
        <div style="text-align:right">
          <div class="score" style="color:${domaine.couleur}">${fmt(domaine.score, 1)}</div>
          <div class="ref delta ${deltaClasse}">écart à la référence : ${ecart >= 0 ? '+' : ''}${fmt(ecart, 1)} pt</div>
          <div class="ref">sans politique : ${domaine.tendance_reference === null || domaine.tendance_reference === undefined ? '—' : fmt(domaine.tendance_reference, 1)}</div>
        </div>
      </div>
      <ul>${indicateurs}</ul>
    </div>`;
  }).join('');
}
function renderMatrice(donnees){
  const impacts = donnees.impacts || [];
  if (!impacts.length){
    document.getElementById('matrice-impacts').innerHTML =
      '<tbody><tr><td>Aucun levier actif : activez des leviers puis lancez « Simuler avec impacts croisés ».</td></tr></tbody>';
    return;
  }
  const domaines = donnees.domaines.map(d => d.cle);
  const libelles = donnees.domaines.map(d => d.libelle.split(' ')[0]);
  let html = '<thead><tr><th>Levier actif</th>' + libelles.map(l => `<th>${l}</th>`).join('') + '</tr></thead><tbody>';
  impacts.forEach(impact => {
    const effets = {};
    impact.effets.forEach(effet => { effets[effet.domaine] = effet.effet_score; });
    const cellules = domaines.map(cle => {
      const valeur = effets[cle];
      if (valeur === undefined) return '<td class="vide">·</td>';
      const classe = valeur > 0 ? 'pos' : 'neg';
      return `<td class="${classe}">${valeur > 0 ? '+' : ''}${fmt(valeur, 1)}</td>`;
    }).join('');
    html += `<tr><td>${impact.libelle}</td>${cellules}</tr>`;
  });
  document.getElementById('matrice-impacts').innerHTML = html + '</tbody>';
}
function renderJournal(donnees){
  const lignes = (donnees.journal || []).map(texte => `<div>${texte}</div>`).join('');
  document.getElementById('journal').innerHTML = lignes || '<div>Journal vide.</div>';
}

/* ── Actions ────────────────────────────────────────────────────────────── */
function reinitialiser(){
  PARAMS = Object.assign({}, CATALOGUE.parametres.defauts);
  renderLeviers(document.getElementById('recherche-levier').value);
  simuler(false);
}
function activerExports(){
  document.getElementById('btn-export-json').disabled = false;
  document.getElementById('btn-export-csv').disabled = false;
}
function exporter(format){
  if (!SORTIE) return;
  if (format === 'json'){
    telecharger(JSON.stringify(SORTIE, null, 2), 'simulation_parametrique.json', 'application/json');
    return;
  }
  const etapes = SORTIE.etapes;
  const colonnes = Object.keys(etapes[0]);
  const lignes = [colonnes.join(';')].concat(etapes.map(etape =>
    colonnes.map(cle => {
      const valeur = etape[cle];
      if (Array.isArray(valeur)) return '"' + valeur.join(' | ').replace(/"/g,'') + '"';
      if (typeof valeur === 'object' && valeur !== null) return '"' + JSON.stringify(valeur).replace(/"/g,'') + '"';
      return String(valeur).replace(';', ',');
    }).join(';')));
  telecharger(lignes.join('\n'), 'simulation_parametrique.csv', 'text/csv');
}
function telecharger(contenu, nom, type){
  const lien = document.createElement('a');
  lien.href = URL.createObjectURL(new Blob([contenu], {type: type + ';charset=utf-8'}));
  lien.download = nom;
  lien.click();
}

/* ── Démarrage ──────────────────────────────────────────────────────────── */
(async function demarrer(){
  await chargerCatalogue();
  renderScenarios();
  await chargerContexte(false);
  chargerPreset('mandature', null);
  activerExports();
})();
</script>
</body>
</html>
"""
