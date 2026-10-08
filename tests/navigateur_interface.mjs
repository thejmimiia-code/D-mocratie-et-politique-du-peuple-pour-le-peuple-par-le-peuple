/**
 * tests/navigateur_interface.mjs — exécute réellement le JavaScript de la page.
 *
 * Usage : node tests/navigateur_interface.mjs <charge.json> <rapport.json>
 *
 * La charge JSON contient :
 *   - page    : le HTML servi par le dashboard (placeholder remplacé) ;
 *   - api     : les réponses réelles des routes du serveur, indexées
 *               « MÉTHODE chemin » (ex. « GET /api/catalogue ») ;
 *   - externe : pour chaque URL d'API publique du registre, l'adaptateur
 *               correspondant (eurostat, sdmx, frankfurter, opendatasoft,
 *               worldbank, yahoo) ; « yahoo » sert à simuler une source sans
 *               CORS, joignable seulement par /api/proxy.
 *
 * Le rapport produit liste, étape par étape, ce que le DOM simulé a reçu :
 * c'est le contrôle « la page fait bien ce qu'elle promet, avec les vraies
 * données du serveur ». Aucune dépendance externe : le DOM et fetch sont des
 * doublures minimales, écrites ici.
 */
import fs from "node:fs";

const [, , cheminCharge, cheminRapport] = process.argv;
if (!cheminCharge) {
  console.error("usage: node navigateur_interface.mjs <charge.json> [rapport.json]");
  process.exit(2);
}

const charge = JSON.parse(fs.readFileSync(cheminCharge, "utf8"));
const page = charge.page;
const api = charge.api || {};
const externe = charge.externe || {};

const rapport = {
  erreurs: [],
  alertes: [],
  telechargements: [],
  appels: [],
  blobs: [],
  etapes: [],
};

function noter(nom, condition, detail) {
  const ok = !!condition;
  rapport.etapes.push({ nom, ok, detail: detail === undefined ? null : String(detail) });
  if (!ok) rapport.erreurs.push(`${nom} : ${detail === undefined ? "échec" : detail}`);
}

/* ── DOM simulé ─────────────────────────────────────────────────────────── */
class Element {
  constructor(id, balise = "div") {
    this.id = id;
    this.tagName = balise.toUpperCase();
    this.innerHTML = "";
    this.outerHTML = "";
    this.textContent = "";
    this.value = "";
    this.disabled = false;
    this.href = "";
    this.download = "";
    Object.defineProperty(this, "className", {
      get: () => [...this._classes].join(" "),
      set: (valeur) => {
        this._classes = new Set(String(valeur || "").split(/\s+/).filter(Boolean));
      },
    });
    this.dataset = {};
    this.style = {};
    this.children = [];
    this.attributs = {};
    this._classes = new Set();
    this._enfants = {};
    this.classList = {
      add: (classe) => this._classes.add(classe),
      remove: (classe) => this._classes.delete(classe),
      contains: (classe) => this._classes.has(classe),
      toggle: (classe) => {
        if (this._classes.has(classe)) { this._classes.delete(classe); return false; }
        this._classes.add(classe);
        return true;
      },
    };
  }
  querySelector(selecteur) {
    // Utilisé pour mettre à jour l'étiquette de valeur d'un levier : on
    // renvoie un enfant stable, pour pouvoir vérifier la mise à jour.
    if (!this._enfants[selecteur]) this._enfants[selecteur] = new Element(selecteur, "span");
    return this._enfants[selecteur];
  }
  querySelectorAll() { return []; }
  appendChild(enfant) { this.children.push(enfant); return enfant; }
  setAttribute(cle, valeur) { this.attributs[cle] = valeur; }
  getAttribute(cle) { return this.attributs[cle] ?? null; }
  addEventListener() {}
  closest() { return null; }
  click() { rapport.telechargements.push({ href: this.href, download: this.download }); }
}

const elements = new Map();
const parId = (id) => {
  if (!elements.has(id)) elements.set(id, new Element(id));
  return elements.get(id);
};
const contenu = (id) => (elements.get(id)?.innerHTML || "");

globalThis.document = {
  getElementById: parId,
  querySelector: (selecteur) => new Element(selecteur),
  querySelectorAll: () => [],
  createElement: (balise) => new Element("cree-" + balise, balise),
  addEventListener: () => {},
  removeEventListener: () => {},
  body: new Element("body"),
};
globalThis.window = globalThis;
// Adresse de la page : le lien partageable s'y construit. Sans elle, le
// script lèverait une erreur au lieu de fabriquer une adresse.
globalThis.location = { origin: "http://127.0.0.1:8000", pathname: "/", search: "" };
globalThis.alert = (message) => { rapport.alertes.push(String(message)); };
globalThis.Blob = class Blob {
  constructor(parties) { this.parties = parties; this.contenu = parties.join(""); }
};
globalThis.URL.createObjectURL = (blob) => {
  rapport.blobs.push(blob.contenu);
  return "blob:simule";
};
// Les temporisations sont exécutées immédiatement : le parcours reste
// séquentiel et déterministe.
globalThis.setTimeout = (fn) => { fn(); return 0; };
globalThis.clearTimeout = () => {};

/* ── fetch simulé ───────────────────────────────────────────────────────── */
function chargeExterne(adaptateur) {
  switch (adaptateur) {
    case "eurostat":
      return { value: { "0": 2.5 }, dimension: { time: { category: { index: { "2026-08": 0 } } } } };
    case "sdmx":
      return {
        dataSets: [{ series: { "0:0": { observations: { "0": [4.0] } } } }],
        structure: { dimensions: { observation: [{ role: "time", values: [{ id: "2026-08" }] }] } },
      };
    case "frankfurter":
      return { date: "2026-10-05", base: "EUR", rates: { USD: 1.1204, CNY: 7.5118, GBP: 0.8472, CHF: 0.9311 } };
    case "opendatasoft":
      return { results: [{ date: "2026-09-01", valeur: 123.4 }] };
    case "worldbank":
      return [{}, [{ date: "2024", value: 30.4 }]];
    case "yahoo":
      // Source sans en-tête CORS : le navigateur ne peut pas la lire.
      throw new TypeError("Failed to fetch (CORS)");
    default:
      return null;
  }
}

globalThis.fetch = async (url, options = {}) => {
  const methode = (options.method || "GET").toUpperCase();
  const brut = String(url);
  rapport.appels.push(`${methode} ${brut}`);
  if (brut.startsWith("/api/")) {
    const chemin = brut.split("?")[0];
    let cle = `${methode} ${chemin}`;
    if (cle === "POST /api/simuler") {
      // Les réponses sont servies dans l'ordre où le parcours les demande, et
      // chacune a été calculée par le vrai serveur pour ces paramètres précis.
      const envoye = JSON.parse(options.body || "{}");
      rapport.postes_simuler = rapport.postes_simuler || [];
      const rang = rapport.postes_simuler.length;
      const sequence = charge.sequence_simuler || [];
      if (rang < sequence.length) cle = sequence[rang].route;
      rapport.postes_simuler.push({
        cle: cle,
        horizon: envoye.horizon,
        leviers_actifs: Object.keys(envoye.parametres || {}).length,
        premier_levier_actif: Object.entries(envoye.parametres || {})
          .filter(([nom]) => (charge.defauts || {})[nom] !== undefined
                             && Math.abs(envoye.parametres[nom] - charge.defauts[nom]) > 1e-9)
          .map(([nom]) => nom).slice(0, 6),
      });
    }
    const corps = api[cle];
    if (corps === undefined) {
      return { ok: false, status: 404, json: async () => ({ error: "route absente du test : " + cle }) };
    }
    return { ok: true, status: 200, json: async () => corps };
  }
  const adaptateur = externe[brut];
  if (!adaptateur) return { ok: false, status: 404, json: async () => ({}) };
  const corps = chargeExterne(adaptateur);
  return { ok: true, status: 200, json: async () => corps };
};

/* ── Extraction et exécution du script de la page ───────────────────────── */
const extrait = page.match(/<script>([\s\S]*?)<\/script>/);
if (!extrait) {
  console.error("aucun <script> trouvé dans la page");
  process.exit(2);
}
// La fonction de démarrage est déclarée dans une IIFE anonyme : on capte sa
// promesse pour attendre la fin du chargement initial avant d'agir.
const source = extrait[1].replace(
  /\(async function demarrer\(\)\{/,
  "globalThis.__demarrage = (async function demarrer(){"
);
if (source === extrait[1]) {
  console.error("fonction demarrer() introuvable : la page n'est pas exécutable");
  process.exit(2);
}

const programme = `
  (async () => {
    ${source}
    await globalThis.__demarrage;
    const api = { elements: globalThis.__elements };
    for (const nom of ['chargerCatalogue','chargerContexte','renderContexte','renderLeviers',
                       'filtrerLeviers','majLevier','planifierSimulation','nombreLeviersActifs',
                       'renderScenarios','renderPresets','chargerPreset','runScenario',
                       'simuler','renderAlertes','renderImpact','renderStrates','renderTableau',
                       'renderGraphique','renderDomaines','renderMatrice','renderJournal',
                       'reinitialiser','activerExports','exporter','rafraichirDonnees',
                       'terminerReglage','basculerDensite','basculerDetailsConsole','allerAuxLeviers',
                       'horizonCourant','changerHorizon','renderBilanIntergenerationnel',
                       'filtreCourant','pucesHtml','majEffetsParLevier',
                       'ouvrirBulle','chargerBulle','htmlBulle','bulleBoutonHtml','libelleDomaine',
                       'initialiserInfobulles','survoler','masquerInfobulle','afficherInfobulle',
                       'texteAideLevier','texteAideElement','puceHtml',
                       'extraireEurostat','extraireSdmx','extraireGenerique',
                       'afficherOngletStrate','renderOngletsStrates','rafraichirMarches',
                       'calculerStressMarche','modifierStressMarche','modifierExpositionActeur',
                       'chargerLexique','definirLexique','baliserTermes','appliquerLexique',
                       'marquerTextes','rendreLexique','filtrerLexique','ouvrirLexique',
                       'ouvrirModale','fermerModale','ouvrirGuide','contenuGuide','guideDejaVu',
                       'reglagesModifies','lienReglages','reglagesDepuisLien','appliquerLien',
                       'partagerReglages','avisLien',
                       'renderLecture','marquerSommaire','contenuOngletStrate','rendreOngletStrate',
                       'modifierProfilMenage','modifierModeCalibrageMenage','depenseBaseProfil']) {
      api[nom] = eval(nom);
    }
    api.etat = () => ({ PARAMS: PARAMS, CATALOGUE: CATALOGUE, CONTEXTE: CONTEXTE,
                        SORTIE: SORTIE, MARCHES: MARCHES, ONGLET_STRATE_ACTIF: ONGLET_STRATE_ACTIF,
                        PROFIL_MENAGE: PROFIL_MENAGE, MODE_CALIBRAGE_MENAGE: MODE_CALIBRAGE_MENAGE,
                        LEXIQUE: LEXIQUE, LEXIQUE_PAR_CLE: LEXIQUE_PAR_CLE,
                        REGEX_TERMES: REGEX_TERMES });
    return api;
  })()
`;
globalThis.__elements = elements;

const tourner = () => new Promise((suite) => setImmediate(suite));
let apiPage = null;
try {
  apiPage = await eval(programme);
} catch (erreur) {
  rapport.erreurs.push("le script de la page a levé une exception : " + (erreur && erreur.stack || erreur));
}
if (!apiPage) {
  if (cheminRapport) fs.writeFileSync(cheminRapport, JSON.stringify(rapport, null, 2));
  console.log(JSON.stringify(rapport, null, 2));
  process.exit(1);
}

// Le démarrage lance des simulations sans les attendre : on vide la boucle
// d'événements avant de contrôler le rendu.
for (let i = 0; i < 6; i += 1) await tourner();

/* 1. Démarrage : catalogue, presets, contexte, préréglage actif. */
const leviersComplets = (contenu("leviers-grille").match(/class="levier[ "]/g) || []).length;
noter("charge le catalogue des leviers", leviersComplets > 50, `${leviersComplets} cartes`);
noter("affiche les 14 préréglages", (elements.get("preset-grid")?.children.length || 0) === 14,
      `${elements.get("preset-grid")?.children.length} cartes`);
noter("affiche les 11 scénarios", (elements.get("scenario-grid")?.children.length || 0) === 11,
      `${elements.get("scenario-grid")?.children.length} cartes`);
noter("affiche les métriques du contexte instant T", contenu("grid-metrics").includes("PIB nominal"));
noter("affiche la provenance des chiffres", contenu("provenance").length > 200);
noter("affiche l'impact du préréglage de démarrage", contenu("grid-impact").includes("carte metric"));
noter("remplit le tableau année par année", contenu("results-table").includes("<tbody>"));
/* Rendu des onglets : seul l'onglet ouvert est construit, les autres attendent
   d'être activés. On parcourt donc les sept onglets un par un — c'est le
   trajet réel d'un lecteur — et l'on vérifie que chacun se remplit à
   l'activation. Le panneau qui n'a pas encore été visité reste vide : c'est
   l'économie de calcul recherchée. */
const attendusOnglets = {
  local: "Finances locales observées",
  national: "Comptes nationaux simulés",
  europe: "Indicateurs européens simulés",
  mondial: "Trajectoire mondiale du moteur",
  geopolitique: "Indice de tension géopolitique",
  menages: "Profil modifiable",
  boursier: "Rafraîchir les cotations",
};
noter("l'onglet ouvert au démarrage est le seul rendu avant toute visite",
      contenu("panneau-strate-local").includes(attendusOnglets.local)
      && contenu("panneau-strate-national") === "",
      `national : ${contenu("panneau-strate-national").length} caractère(s)`);
for (const cle of Object.keys(attendusOnglets)) {
  apiPage.afficherOngletStrate(cle);
  for (let i = 0; i < 2; i += 1) await tourner();
}
noter("les onglets local, national, européen, mondial, géopolitique, ménages et boursier se rendent à l'ouverture",
      Object.keys(attendusOnglets).every((cle) => {
        const cible = cle === "menages" ? "menage-resultats" : `panneau-strate-${cle}`;
        return contenu(cible).includes(attendusOnglets[cle]);
      }),
      Object.keys(attendusOnglets)
        .filter((cle) => !contenu(cle === "menages" ? "menage-resultats" : `panneau-strate-${cle}`)
          .includes(attendusOnglets[cle])).join(", ") || "les sept vues sont rendues");
const clesOnglets = ['local','national','europe','mondial','geopolitique','menages','boursier'];
clesOnglets.forEach(cle => apiPage.afficherOngletStrate(cle));
noter("la navigation active les sept onglets au clavier et par ARIA",
      apiPage.etat().ONGLET_STRATE_ACTIF === "boursier"
      && elements.get("tab-strate-boursier")?.attributs["aria-selected"] === "true"
      && elements.get("tab-strate-boursier")?.tabIndex === 0
      && elements.get("tab-strate-local")?.tabIndex === -1);
apiPage.afficherOngletStrate("local");
noter("le profil ménage n'est pas présenté comme un budget observé",
      contenu("menage-resultats").includes("jamais transmis à l'API")
      && contenu("panneau-strate-menages").includes("pas budget observé"));
const contexteCalibrage = apiPage.etat().CONTEXTE;
const panierCalibrage = contexteCalibrage?.observatoire?.menages?.panier_national_2025;
noter("le choix de calibrage expose la source, la période et le statut INSEE",
      contenu("panneau-strate-menages").includes('id="mode-calibrage-menage"')
      && contenu("panneau-strate-menages").includes(panierCalibrage?.statut || "statut non renseigné")
      && contenu("panneau-strate-menages").includes(panierCalibrage?.publication_le || "date de publication"));
apiPage.modifierProfilMenage({dataset:{profil:"depense_alimentation"},type:"number",value:"123.45"});
apiPage.modifierModeCalibrageMenage("insee");
apiPage.modifierProfilMenage({dataset:{profil:"depenses_panier_total_mensuel"},type:"number",value:"2000"});
const profilCalibrage = apiPage.etat().PROFIL_MENAGE;
const totalCalibrageAvantEnergie = profilCalibrage.depenses_panier_total_mensuel;
apiPage.modifierProfilMenage({dataset:{profil:"depense_energie_mensuelle"},type:"number",value:"250"});
noter("le champ énergie reste une donnée personnelle modifiable en mode INSEE",
      Math.abs(profilCalibrage.depense_energie_mensuelle - 250) < 0.001
      && Math.abs(profilCalibrage.depenses_panier_total_mensuel - totalCalibrageAvantEnergie) < 0.001);
const partsPubliees = panierCalibrage?.part_depense_finale_pct || [];
const clesProfilDepenses = new Set(Object.keys(profilCalibrage)
  .filter(cle => cle.startsWith("depense_")).map(cle => cle.slice("depense_".length)));
const sommePartsUtilisees = partsPubliees
  .filter(ligne => clesProfilDepenses.has(ligne.cle) && Number(ligne.part) > 0)
  .reduce((somme, ligne) => somme + Number(ligne.part), 0);
const partAlimentation = partsPubliees.find(ligne => ligne.cle === "alimentation")?.part;
const depenseCalibree = apiPage.depenseBaseProfil({cle:"alimentation"});
const attendueCalibree = 2000 * Number(partAlimentation) / sommePartsUtilisees;
noter("le calibrage INSEE relie les parts qualifiées au total personnel sans écraser les saisies",
      apiPage.etat().MODE_CALIBRAGE_MENAGE === "insee"
      && Number.isFinite(depenseCalibree)
      && Math.abs(depenseCalibree - attendueCalibree) < 0.001
      && Math.abs(profilCalibrage.depense_alimentation - 123.45) < 0.001,
      `montant calibré ${depenseCalibree} €; attendu ${attendueCalibree} €`);
apiPage.modifierModeCalibrageMenage("personnel");
noter("le retour au mode personnel restaure les montants saisis",
      apiPage.etat().MODE_CALIBRAGE_MENAGE === "personnel"
      && Math.abs(apiPage.depenseBaseProfil({cle:"alimentation"}) - 123.45) < 0.001);
noter("la vue boursière cite l'horodatage et les limites de son flux",
      contenu("panneau-strate-boursier").includes("Horodatage du cours")
      && contenu("panneau-strate-boursier").includes("possiblement différés")
      && contenu("panneau-strate-boursier").includes("collecté"));
noter("la couverture distingue hameaux, métropoles, France métropolitaine et outre-mer",
      contenu("panneau-strate-local").includes("Hameau")
      && contenu("panneau-strate-local").includes("EPCI et métropoles")
      && contenu("panneau-strate-local").includes("France métropolitaine")
      && contenu("panneau-strate-local").includes("DROM / COM"));
noter("les expositions boursières territoriales sont détaillées sans devenir des données observées",
      contenu("panneau-strate-boursier").includes("Communes / communes nouvelles")
      && contenu("panneau-strate-boursier").includes("DROM / COM / Nouvelle-Calédonie")
      && contenu("panneau-strate-boursier").includes("exposition saisie"));
noter("le budget national distingue recettes fiscales, dépenses et solde des leviers",
      contenu("panneau-strate-national").includes("Impôt sur le revenu")
      && contenu("panneau-strate-national").includes("Dépenses publiques simulées")
      && contenu("panneau-strate-national").includes("Solde net des leviers"));
noter("trace les courbes du graphique", contenu("svg-chart").includes("<polyline"));
const cotationsChargees = apiPage.etat().MARCHES?.indices || [];
noter("charge les 13 repères boursiers déclarés", cotationsChargees.length === 13,
      `${cotationsChargees.length} indices`);
if (cotationsChargees.length){
  cotationsChargees.filter(x => x.cle !== 'cac40').forEach(x => apiPage.modifierStressMarche(x.cle,'actif',false));
  apiPage.modifierStressMarche('cac40','actif',true);
  apiPage.modifierStressMarche('cac40','choc',10);
  apiPage.modifierExpositionActeur('ir_0',10000);
}
noter("un choc boursier met à jour la plus-value brute du groupe saisi",
      Math.abs((apiPage.calculerStressMarche?.().stressPct || 0) - (cotationsChargees.length ? 10 : 0)) < 0.01
      && (cotationsChargees.length === 0 || contenu("pnl-acteur-ir_0").includes("1 000,00 €")));
noter("le stress de portefeuille ne déclenche pas une fausse simulation macro",
      (rapport.postes_simuler || []).length === 1,
      `${(rapport.postes_simuler || []).length} appel(s) de simulation après chargement initial`);
noter("le POST de simulation porte tout le catalogue",
      rapport.postes_simuler?.[0]?.leviers_actifs === leviersComplets,
      `${rapport.postes_simuler?.[0]?.leviers_actifs} levier(s) transmis`);
const impactPrereglage = contenu("grid-impact");

/* 2. Un levier modifié par l'utilisateur relance la simulation. */
const cleLevier = charge.discriminant.cle;
const defauts = apiPage.etat().CATALOGUE.parametres.defauts;
apiPage.majLevier(cleLevier, defauts[cleLevier] + 1.0);
for (let i = 0; i < 6; i += 1) await tourner();
// Le curseur est relâché : `change` déclenche le re-rendu avec les puces.
apiPage.terminerReglage();
noter("mémorise la valeur du levier", apiPage.etat().PARAMS[cleLevier] === defauts[cleLevier] + 1.0,
      `valeur : ${apiPage.etat().PARAMS[cleLevier]}`);
noter("compte le levier comme actif", apiPage.nombreLeviersActifs() >= 1,
      `${apiPage.nombreLeviersActifs()} actif(s)`);
noter("redemande une simulation au serveur",
      (rapport.postes_simuler || []).some((poste) => poste.cle === "POST /api/simuler#variante"));
noter("l'impact affiché change avec le levier", contenu("grid-impact") !== impactPrereglage);
const synthese = apiPage.etat().SORTIE?.synthese || {};
noter("le nouveau résultat vient du serveur (pas d'un cache)",
      Math.abs((synthese.recettes_nouvelles_mde || 0) - (charge.attendu?.recettes_nouvelles_mde ?? -1)) < 0.05,
      `${synthese.recettes_nouvelles_mde} Md€ attendu ${charge.attendu?.recettes_nouvelles_mde}`);
noter("recalcule les domaines", contenu("domaines-grille").length > 500,
      `${contenu("domaines-grille").length} caractères`);
noter("recalcule la cascade des 5 échelons", contenu("strates-cascade").includes("Échelon 5 — Géopolitique"));
noter("signale l'absence de tension par un journal", contenu("journal").length > 0);
noter("le ruban de veille est renseigné",
      /tolérable|vigilance|risqué|hors-sol|favorable/i.test(
        elements.get("ruban-verdict")?.textContent || ""),
      elements.get("ruban-verdict")?.textContent);
noter("le ruban porte les cinq strates",
      (contenu("ruban-strates").match(/ruban-strate/g) || []).length === 5,
      `${(contenu("ruban-strates").match(/ruban-strate/g) || []).length} strates`);
noter("le ruban affiche le risque population",
      /risque population/.test(contenu("ruban-population")), contenu("ruban-population"));
noter("le levier réglé est mis en évidence",
      contenu("leviers-grille").includes("levier modifie")
      || contenu("leviers-grille").includes('class="levier modifie"'),
      (contenu("leviers-grille").match(/levier modifie/g) || []).length + " levier(s) marqué(s)");
noter("le levier réglé reçoit ses puces d'impact",
      contenu("leviers-grille").includes("puce-effect"),
      (contenu("leviers-grille").match(/puce-effect/g) || []).length + " puce(s)");
/* Le conseiller temps réel (« effet papillon ») : le geste est une décision —
   position avant vs position à l'instant T — rejouée par le moteur. */
for (let i = 0; i < 6; i += 1) await tourner();
noter("le mouvement du levier interroge le conseiller temps réel",
      rapport.appels.some((appel) => appel.startsWith("POST /api/conseil")),
      rapport.appels.filter((appel) => appel.startsWith("POST /api/conseil")).length + " appel(s)");
noter("le conseiller rend la décision et ses ricochets dans la console",
      /Effet papillon|ricochet|directs|Conseiller/i.test(contenu("console-conseil")),
      contenu("console-conseil").slice(0, 140));
noter("la veille affiche le coût / gain réel des réglages globaux croisés",
      /Coût réel|Gain réel|effet budgétaire net nul/i.test(contenu("console-cout-global")),
      contenu("console-cout-global").slice(0, 120));
noter("le conseil cite le coût ou le gain réel du mouvement",
      /Coût réel|Gain réel|cout-gain/i.test(contenu("console-conseil")),
      (contenu("console-conseil").match(/cout-gain/g) || []).length + " bloc(s)");
noter("le levier manipulé affiche le badge coût / gain réel en temps réel",
      /cout-live (gain|cout|neutre)|Mesure du coût/i.test(contenu("leviers-grille")),
      (contenu("leviers-grille").match(/cout-live/g) || []).length + " badge(s)");
noter("le ruban de veille affiche le coût / gain réel du programme actif",
      /coût réel|gain réel|effet net/i.test(elements.get("ruban-cout")?.textContent || ""),
      elements.get("ruban-cout")?.textContent);
noter("l'audit de traçabilité est rendu en bas de page",
      contenu("audit-gardefous").includes("Déficit public")
      && contenu("audit-domaines").includes("Formule du score")
      && contenu("audit-sources").includes("Grandeur d'entrée"),
      "sources " + contenu("audit-sources").length
      + " car. ; domaines " + contenu("audit-domaines").length
      + " car. ; garde-fous " + contenu("audit-gardefous").length + " car.");
noter("le compteur annonce les leviers affichés et modifiés",
      new RegExp(leviersComplets + " levier\\(s\\) affiché\\(s\\)")
        .test(elements.get("compteur-leviers")?.textContent || ""),
      elements.get("compteur-leviers")?.textContent);

/* 2 bis. Vue compacte : chaque paramètre sur une ligne. */
apiPage.basculerDensite(true);
for (let i = 0; i < 2; i += 1) await tourner();
const compacts = (contenu("leviers-grille").match(/class="levier compact/g) || []).length;
noter("la vue compacte affiche tous les leviers", compacts === leviersComplets,
      `${compacts} leviers compacts`);
const curseurs = (contenu("leviers-grille").match(/oninput="majLevier/g) || []).length;
const bascules = (contenu("leviers-grille").match(/onchange="majLevier/g) || []).length;
noter("chaque levier compact garde sa commande", curseurs + bascules === leviersComplets,
      `${curseurs} curseurs + ${bascules} interrupteurs = ${curseurs + bascules} commandes`);
noter("le libellé du bouton de densité bascule",
      (elements.get("btn-densite")?.textContent || "").includes("confort"),
      elements.get("btn-densite")?.textContent);
apiPage.basculerDensite(false);
for (let i = 0; i < 2; i += 1) await tourner();
noter("le retour en vue confort restaure les descriptions",
      contenu("leviers-grille").includes("class=\"desc\""));

/* 2 ter. Le détail des seuils se replie pour libérer l'écran. */
apiPage.basculerDetailsConsole();
for (let i = 0; i < 2; i += 1) await tourner();
noter("le corps de la console se replie",
      elements.get("console-corps")?.classList.contains("replie") === true);
apiPage.basculerDetailsConsole();
noter("le corps de la console se déplie",
      elements.get("console-corps")?.classList.contains("replie") === false);

/* 2 quater. Bulles explicatives : un bouton par réglage, contenu calculé. */
const boutonsBulle = (contenu("leviers-grille").match(/class="bulle-bouton/g) || []).length;
noter("chaque réglage porte un bouton de bulle explicative", boutonsBulle >= leviersComplets,
      `${boutonsBulle} boutons`);
await apiPage.ouvrirBulle(cleLevier);
for (let i = 0; i < 6; i += 1) await tourner();
const grilleBulle = contenu("leviers-grille");
noter("la bulle s'ouvre dans la carte du levier", grilleBulle.includes("bulle-levier"));
noter("la bulle décrit la chaîne d'interaction", grilleBulle.includes("Chaîne d'interaction"));
noter("la bulle affiche les répercussions mesurées", grilleBulle.includes("Répercussions mesurées"));
noter("la bulle guide opportunités et désagréments", /Opportunités|Désagréments/.test(grilleBulle));
noter("la bulle cite les effets déclarés au catalogue", grilleBulle.includes("Effets déclarés au catalogue"));
noter("la bulle affiche le coût / gain réel du réglage en direct",
      grilleBulle.includes("bulle-live") && /cout-gain (gain|cout|neutre)/.test(grilleBulle),
      (grilleBulle.match(/cout-gain/g) || []).length + " bloc(s) coût/gain dans la bulle");
noter("la bulle laisse les 101 réglages accessibles",
      (grilleBulle.match(/class="levier[ "]/g) || []).length === leviersComplets,
      `${(grilleBulle.match(/class="levier[ "]/g) || []).length} cartes`);
await apiPage.ouvrirBulle(cleLevier);
for (let i = 0; i < 2; i += 1) await tourner();
noter("la bulle se referme", !contenu("leviers-grille").includes("bulle-levier"));

/* 2 quinquies. Aides au survol : chaque réglage s'explique sans clic. */
const zonesAide = (contenu("leviers-grille").match(/data-aide-levier=/g) || []).length;
noter("chaque réglage porte une zone d'aide au survol", zonesAide >= leviersComplets * 4,
      `${zonesAide} zones pour ${leviersComplets} réglages`);
const aideReglage = apiPage.texteAideLevier(cleLevier);
noter("l'aide décrit plage, défaut et valeur courante",
      aideReglage.includes("plage") && aideReglage.includes("défaut")
      && aideReglage.includes("valeur actuelle"),
      aideReglage.slice(0, 110));
noter("l'aide annonce les effets déclarés au catalogue",
      aideReglage.includes("Effets déclarés"), aideReglage.slice(0, 110));
const cibleAide = { getAttribute: (nom) => (nom === "data-aide-levier" ? cleLevier : null) };
apiPage.survoler(cibleAide);
noter("l'infobulle s'affiche au survol d'un réglage",
      elements.get("infobulle")?.classList.contains("visible") === true);
noter("l'infobulle reprend le libellé du réglage",
      contenu("infobulle").includes("TVA"), contenu("infobulle").slice(0, 90));
noter("la couche d'infobulle ne capte aucun clic",
      /pointer-events:none/.test(charge.page));
apiPage.masquerInfobulle();
noter("l'infobulle disparaît au départ de la souris",
      elements.get("infobulle")?.classList.contains("visible") === false);
/* Aucune aide flottante ne doit recouvrir une bulle « interactions » ouverte :
   le résultat affiché derrière doit rester lisible. */
await apiPage.ouvrirBulle(cleLevier);
for (let i = 0; i < 4; i += 1) await tourner();
apiPage.survoler(cibleAide);
noter("aucune infobulle ne recouvre la bulle « interactions » ouverte",
      elements.get("infobulle")?.classList.contains("visible") === false,
      "infobulle masquée tant qu'une bulle est ouverte");
await apiPage.ouvrirBulle(cleLevier);
for (let i = 0; i < 2; i += 1) await tourner();
apiPage.survoler(cibleAide);
noter("l'infobulle revient une fois la bulle refermée",
      elements.get("infobulle")?.classList.contains("visible") === true);
apiPage.masquerInfobulle();
const boutonsAnnotes = (charge.page.match(/data-aide="/g) || []).length;
noter("les boutons d'action portent aussi une aide", boutonsAnnotes >= 10,
      `${boutonsAnnotes} éléments annotés dans la page`);

/* 3. Sorties attendues peuplées après simulation paramétrique. */
for (const id of ["strates-cascade", "results-table", "svg-chart", "domaines-grille",
                  "matrice-impacts", "journal"]) {
  noter(`rend ${id}`, contenu(id).length > 40, `${contenu(id).length} caractères`);
}
noter("matrice d'impacts chiffrée", /\d+([.,]\d+)?\s*(pt|%|\+|-)/.test(contenu("matrice-impacts")),
      contenu("matrice-impacts").slice(0, 120));

/* 3 bis. Console de veille permanente : messages de seuil et garde-fous. */
noter("la console affiche un verdict", /tolérable|vigilance|risqué|hors-sol|favorable/i.test(
  elements.get("console-verdict")?.textContent || ""), elements.get("console-verdict")?.textContent);
noter("la console décrit les cinq strates", (contenu("console-strates").match(/strate-puce/g) || []).length >= 4,
      `${(contenu("console-strates").match(/strate-puce/g) || []).length} strates`);
noter("la console mesure le risque pour la population",
      contenu("console-population").includes("Indice de risque"));
noter("la console affiche des messages de seuil", contenu("console-alertes").length > 60,
      `${contenu("console-alertes").length} caractères`);
noter("la console donne des marges ou des audaces", contenu("console-marges").length > 60);
noter("l'effet de la dernière modification est affiché",
      contenu("console-derniere-modification").includes("TVA")
      || contenu("console-derniere-modification").includes("modifié"),
      contenu("console-derniere-modification").slice(0, 140));

/* 3 quater. Lecture en clair : les mêmes chiffres, en phrases ordinaires. */
const lecture = apiPage.etat().SORTIE?.lecture || {};
const lignesClaires = lecture.lignes || [];
noter("la simulation porte une lecture en clair", lignesClaires.length >= 3,
      `${lignesClaires.length} phrase(s)`);
noter("chaque phrase de la lecture est complète et pondérée",
      lignesClaires.every(ligne => typeof ligne.texte === "string" && ligne.texte.length > 40
        && typeof ligne.niveau === "string" && typeof ligne.valeur === "string"),
      lignesClaires.map(ligne => ligne.niveau).join(", "));
noter("la lecture est rendue dans la page", contenu("clair-lignes").includes("clair-ligne")
      && (contenu("clair-lignes").match(/clair-ligne/g) || []).length >= 3,
      `${(contenu("clair-lignes").match(/clair-ligne/g) || []).length} ligne(s) affichée(s)`);
noter("la lecture rappelle ses limites", (contenu("clair-limites").match(/<li>/g) || []).length >= 2,
      `${(contenu("clair-limites").match(/<li>/g) || []).length} limite(s) affichée(s)`);
noter("la synthèse de lecture est affichée",
      (elements.get("clair-resume")?.textContent || "").length > 30,
      elements.get("clair-resume")?.textContent);

/* 3 quinquies. Lexique : le jargon expliqué, souligné et cherchable. */
await apiPage.chargerLexique();
const lexiqueCharge = apiPage.etat();
noter("le lexique est chargé depuis l'API",
      Object.keys(lexiqueCharge.LEXIQUE_PAR_CLE || {}).length >= 40,
      `${Object.keys(lexiqueCharge.LEXIQUE_PAR_CLE || {}).length} terme(s) indexé(s)`);
const balise = apiPage.baliserTermes("<p>Le spread et la dette publique augmentent.</p>");
noter("les termes techniques sont soulignés dans les textes",
      (balise.match(/class="terme"/g) || []).length >= 2, balise.slice(0, 160));
noter("le soulignement ne touche jamais l'intérieur d'une balise",
      apiPage.baliserTermes('<span data-aide="<b>PIB</b> dette">le PIB</span>')
        .includes('data-aide="<b>PIB</b> dette"'),
      apiPage.baliserTermes('<span data-aide="<b>PIB</b> dette">le PIB</span>'));
noter("un terme déjà souligné n'est pas réenveloppé",
      apiPage.baliserTermes(balise) === balise);
apiPage.ouvrirLexique("");
for (let i = 0; i < 2; i += 1) await tourner();
noter("le lexique s'ouvre dans une modale",
      elements.get("overlay")?.classList.contains("visible") === true);
noter("le lexique regroupe ses termes par catégorie",
      (contenu("modale-corps").match(/lexique-categorie/g) || []).length >= 4,
      `${(contenu("modale-corps").match(/lexique-categorie/g) || []).length} catégorie(s)`);
apiPage.filtrerLexique("spread");
noter("la recherche filtre le lexique",
      contenu("modale-corps").includes("Spread")
      && !contenu("modale-corps").includes("Taxe foncière"),
      contenu("modale-corps").slice(0, 120));
/* Le balisage s'applique aux textes réellement rendus : la console de veille
   contient des attributs `data-aide` dont la valeur est du HTML — un « > »
   interne ne doit pas être pris pour une fin de balise. */
apiPage.marquerTextes();
const consoleMarquee = contenu("console-corps");
noter("le soulignement du lexique ne corrompt pas les aides de la console",
      contenu("console-corps").includes('data-aide="<b>')
      || !contenu("console-corps").includes("data-aide="),
      consoleMarquee.slice(0, 140));
noter("les textes de la lecture en clair sont balisés à leur tour",
      contenu("clair-lignes").includes('class="terme"')
      || !/PIB|dette|déficit/i.test(contenu("clair-lignes")),
      contenu("clair-lignes").slice(0, 140));
apiPage.fermerModale();
noter("la modale se referme",
      elements.get("overlay")?.classList.contains("visible") === false);
apiPage.ouvrirGuide();
noter("le guide de démarrage décrit quatre étapes",
      (contenu("modale-corps").match(/guide-etape/g) || []).length === 4,
      `${(contenu("modale-corps").match(/guide-etape/g) || []).length} étape(s)`);
apiPage.fermerModale();

/* 3 ter. Un préréglage dangereux doit déclencher l'alerte hors-sol. */
apiPage.chargerPreset("austerite", null);
for (let i = 0; i < 6; i += 1) await tourner();
noter("charger un préréglage dangereux demande une simulation",
      (rapport.postes_simuler || []).length >= 3, `${(rapport.postes_simuler || []).length} simulations`);
noter("le bandeau hors-sol apparaît", contenu("console-danger").includes("HORS-SOL"),
      contenu("console-danger").slice(0, 120));
noter("le verdict global passe au rouge",
      /hors-sol|risqué/i.test(elements.get("console-verdict")?.textContent || ""),
      elements.get("console-verdict")?.textContent);
noter("la strate locale signale la tension sociale",
      /tension/i.test(contenu("console-alertes")), contenu("console-alertes").slice(0, 120));
noter("au moins une strate est marquée hors-sol",
      (contenu("console-strates").match(/niveau-hors_sol/g) || []).length >= 1);

/* 4. Les scénarios du dépôt rejouent le moteur d'origine (chemin historique). */
await apiPage.runScenario("choc_mondial", null);
for (let i = 0; i < 4; i += 1) await tourner();
noter("appelle /api/run pour un scénario du dépôt",
      rapport.appels.some((appel) => appel.includes("/api/run?scenario=choc_mondial")));
noter("affiche le scénario historique", contenu("grid-impact").includes("Scénario historique"));
noter("le tableau montre les résultats du moteur d'origine",
      contenu("results-table").includes("<tbody>") && contenu("results-table").length > 500);

/* 5. Filtre, puis retour au neutre : la console doit revenir au vert. */
apiPage.filtrerLeviers("retraite");
const restreints = (contenu("leviers-grille").match(/class="levier[ "]/g) || []).length;
noter("le filtre réduit la liste", restreints > 0 && restreints < leviersComplets,
      `${restreints} sur ${leviersComplets}`);
apiPage.reinitialiser();
for (let i = 0; i < 10; i += 1) await tourner();
const tousNuls = Object.entries(apiPage.etat().PARAMS)
  .every(([cle, valeur]) => Math.abs(valeur - defauts[cle]) < 1e-9);
noter("la réinitialisation remet tous les leviers au neutre", tousNuls);
noter("la grille complète est rétablie",
      (contenu("leviers-grille").match(/class="levier[ "]/g) || []).length === leviersComplets);
const posteNeutre = rapport.postes_simuler?.at(-1);
noter("la réinitialisation recalcule le scénario de référence sans levier actif",
      tousNuls && posteNeutre?.cle === "POST /api/simuler#neutre"
      && (posteNeutre?.premier_levier_actif || []).length === 0,
      `${posteNeutre?.cle} · alertes de référence : ${contenu("console-danger").slice(0,140)}`);
noter("le verdict reste calculé après réinitialisation",
      /tolérable|vigilance|risqué|hors-sol|favorable/i.test(
        elements.get("console-verdict")?.textContent || ""));

/* 6. Exports. */
apiPage.exporter("json");
apiPage.exporter("csv");
let jsonValide = false;
let csvLignes = 0;
if (rapport.blobs.length >= 2) {
  try {
    const objet = JSON.parse(rapport.blobs[0]);
    jsonValide = Array.isArray(objet.etapes) && objet.etapes.length === 5 && !!objet.domaines;
  } catch (erreur) { jsonValide = false; }
  csvLignes = rapport.blobs[1].trim().split("\n").length;
}
noter("l'export JSON contient les 5 étapes et les domaines", jsonValide);
noter("l'export CSV contient l'en-tête et 5 années", csvLignes === 6, `${csvLignes} lignes`);
noter("les deux téléchargements sont déclenchés", rapport.telechargements.length === 2,
      `${rapport.telechargements.length} liens`);

/* 7. Rafraîchissement : les API publiques sont interrogées, puis relayées. */
await apiPage.rafraichirDonnees();
const appelsExternes = rapport.appels.filter((appel) => !appel.includes("/api/"));
noter("interroge les API publiques en direct", appelsExternes.length > 0, `${appelsExternes.length} appels`);
noter("transmet le relevé au serveur", rapport.appels.some((appel) => appel.startsWith("POST /api/donnees")));
noter("relaie par /api/proxy les sources sans CORS",
      rapport.appels.some((appel) => appel.includes("/api/proxy")));
noter("récapitule les séries mises à jour dans le bouton",
      /séries mises à jour|aucune source joignable/.test(elements.get("btn-rafraichir")?.textContent || ""),
      elements.get("btn-rafraichir")?.textContent);
noter("aucune boîte d'alerte ouverte", rapport.alertes.length === 0, rapport.alertes.join(" | "));

/* 8. L'horizon décennal est envoyé au moteur et son bilan reste lisible. */
apiPage.changerHorizon(10);
for (let i = 0; i < 6; i += 1) await tourner();
const appelDecennal = rapport.postes_simuler?.at(-1);
noter("le sélecteur accepte deux mandatures", apiPage.horizonCourant() === 10
      && elements.get("horizon-simulation")?.value === "10");
noter("la requête envoie l'horizon de dix ans", appelDecennal?.horizon === 10,
      JSON.stringify(appelDecennal));
noter("le résultat rend dix étapes et le bilan intergénérationnel",
      apiPage.etat().SORTIE?.horizon === 10
      && apiPage.etat().SORTIE?.etapes?.length === 10
      && contenu("bilan-intergenerationnel").includes("Besoin de patrimoine non couvert"));

/* 9. Adaptateurs d'extraction, testés isolément sur des charges réalistes. */
const eurostat = apiPage.extraireEurostat(chargeExterne("eurostat"), "0");
noter("adaptateur Eurostat", eurostat && eurostat.valeur === 2.5 && eurostat.periode === "2026-08");
const sdmx = apiPage.extraireSdmx(chargeExterne("sdmx"));
noter("adaptateur SDMX", sdmx && sdmx.valeur === 4.0 && sdmx.periode === "2026-08");
const frankfurter = apiPage.extraireGenerique("frankfurter", chargeExterne("frankfurter"), "USD");
noter("adaptateur Frankfurter", frankfurter && frankfurter.valeur === 1.1204);
const ods = apiPage.extraireGenerique("opendatasoft", chargeExterne("opendatasoft"), "valeur");
noter("adaptateur Opendatasoft", ods && ods.valeur === 123.4);
const bm = apiPage.extraireGenerique("worldbank", chargeExterne("worldbank"), null);
noter("adaptateur Banque mondiale", bm && bm.valeur === 30.4 && bm.periode === "2024");
const yahoo = apiPage.extraireGenerique("yahoo",
  { chart: { result: [{ meta: { regularMarketPrice: 101.69, regularMarketTime: 1759600000 } }] } }, null);
noter("adaptateur Yahoo (via proxy)", yahoo && yahoo.valeur === 101.69);

/* 10. Lien partageable : un réglage se transmet par l'adresse, et rien d'autre. */
apiPage.majLevier(cleLevier, defauts[cleLevier] + 3.0);
const lienPartage = apiPage.lienReglages();
noter("le lien partagé reprend l'adresse de la page",
      lienPartage.startsWith("http://") && lienPartage.includes("?sim="), lienPartage.slice(0, 70));
const brutLien = new URL(lienPartage).searchParams.get("sim") || "{}";
const reprisLien = JSON.parse(brutLien);
noter("le lien ne transporte que les leviers déplacés",
      Object.keys(reprisLien).length > 0 && Object.keys(reprisLien).length < 40
      && Object.prototype.hasOwnProperty.call(reprisLien, cleLevier),
      `${Object.keys(reprisLien).length} levier(s) : ${Object.keys(reprisLien).slice(0, 4).join(", ")}`);
noter("le lien se relit à l'identique",
      JSON.stringify(apiPage.reglagesDepuisLien(brutLien)) === JSON.stringify(reprisLien),
      JSON.stringify(apiPage.reglagesDepuisLien(brutLien)) === JSON.stringify(reprisLien)
        ? "aller-retour fidèle" : "le contenu relu diffère");
const hostile = apiPage.reglagesDepuisLien(
  JSON.stringify({ [cleLevier]: 5, levier_invente: 99, texte: "bonjour", liste: [1, 2] }));
noter("un lien hostile ne peut pas injecter un réglage inconnu",
      Object.keys(hostile).length === 1 && hostile[cleLevier] === 5, JSON.stringify(hostile));
noter("un lien illisible est ignoré sans erreur",
      Object.keys(apiPage.reglagesDepuisLien("ceci n'est pas du json")).length === 0
      && Object.keys(apiPage.reglagesDepuisLien(null)).length === 0
      && Object.keys(apiPage.reglagesDepuisLien(JSON.stringify([1, 2, 3]))).length === 0);
noter("partager renvoie l'adresse calculée, sans copier dans le vide",
      (await apiPage.partagerReglages()) === lienPartage);
noter("un lien absent ne déclenche aucun réglage repris",
      apiPage.reglagesDepuisLien("").tva_taux_normal === undefined);

/* Le trajet complet : on repart du neutre, puis on ouvre l'adresse. */
apiPage.majLevier(cleLevier, defauts[cleLevier]);
globalThis.location.search = "?sim=" + encodeURIComponent(brutLien);
const applique = apiPage.appliquerLien();
noter("l'adresse partagée est reprise à l'ouverture de la page",
      applique === true
      && apiPage.etat().PARAMS[cleLevier] === defauts[cleLevier] + 3.0
      && (elements.get("avis-lien")?.textContent || "").includes("levier"),
      `appliqué : ${applique} · valeur ${apiPage.etat().PARAMS[cleLevier]} · avis « ${elements.get("avis-lien")?.textContent || ""} »`);
globalThis.location.search = "";

/* ── Rapport ────────────────────────────────────────────────────────────── */
rapport.elements = Object.fromEntries(
  [...elements.entries()].map(([id, el]) => [id, (el.innerHTML || el.textContent || "").length])
);
rapport.nombre_appels = rapport.appels.length;
const bilan = {
  etapes: rapport.etapes.length,
  reussies: rapport.etapes.filter((etape) => etape.ok).length,
  erreurs: rapport.erreurs,
  alertes: rapport.alertes,
  appels: rapport.appels.length,
  appels_externes: rapport.appels.filter((appel) => !appel.includes("/api/")).length,
  telechargements: rapport.telechargements.map((lien) => lien.download),
};
console.log(JSON.stringify(bilan, null, 2));
if (cheminRapport) fs.writeFileSync(cheminRapport, JSON.stringify(rapport, null, 2));
if (rapport.erreurs.length) process.exit(1);
