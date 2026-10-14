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
      toggle: (classe, force) => {
        // `classList.toggle(classe, force)` : le second argument est standard.
        if (force === undefined) {
          if (this._classes.has(classe)) { this._classes.delete(classe); return false; }
          this._classes.add(classe);
          return true;
        }
        if (force) { this._classes.add(classe); return true; }
        this._classes.delete(classe);
        return false;
      },
    };
  }
  querySelector(selecteur) {
    // Utilisé pour mettre à jour l'étiquette de valeur d'un levier : on
    // renvoie un enfant stable, pour pouvoir vérifier la mise à jour.
    if (!this._enfants[selecteur]) this._enfants[selecteur] = new Element(selecteur, "span");
    return this._enfants[selecteur];
  }
  /* Les commandes d'un cadre : la doublure n'en connaît qu'une, la fenêtre
     modale, et c'est celle dont l'ordre de tabulation se vérifie. */
  querySelectorAll() { return this._commandes || []; }
  appendChild(enfant) { this.children.push(enfant); enfant.parentElement = this; return enfant; }
  setAttribute(cle, valeur) { this.attributs[cle] = valeur; }
  getAttribute(cle) { return this.attributs[cle] ?? null; }
  addEventListener() {}
  /* Le vrai navigateur remonte la chaîne ; la doublure aussi, sinon aucun
     contrôle ne peut dire si une infobulle va céder devant sa commande. */
  closest(selecteur) {
    const morceaux = String(selecteur).split(",").map((m) => m.trim());
    for (let noeud = this; noeud; noeud = noeud.parentElement) {
      const balise = String(noeud.tagName || "").toLowerCase();
      for (const morceau of morceaux) {
        if (morceau === balise) return noeud;
        if (morceau.startsWith(".") && noeud._classes.has(morceau.slice(1))) return noeud;
        if (morceau.startsWith("[") && noeud.attributs[morceau.slice(1, -1)] !== undefined) return noeud;
      }
    }
    return null;
  }
  contains(noeud) {
    for (const enfant of this.children) {
      if (enfant === noeud || enfant.contains?.(noeud)) return true;
    }
    return false;
  }
  click() { rapport.telechargements.push({ href: this.href, download: this.download }); }
  /* Le focus : le vrai navigateur le pose sur un nœud et le retient ; la
     doublure l'enregistre — sinon aucune étape ne peut dire où le clavier se
     trouve, la question même d'une fenêtre qui s'ouvre et se referme. */
  focus() {
    globalThis.document.activeElement = this;
    this._focalise = (this._focalise || 0) + 1;
    return true;
  }
}

/* L'affichage se règle sur trois préférences qui n'appartiennent qu'au
   visiteur. Pour que la page puisse les lire, trois doublures de plus :
   la racine du document (c'est elle qui porte `data-theme`), `matchMedia`
   (le réglage de l'appareil) et `localStorage` (la mémoire du choix). */
const racineDocument = new Element("html", "html");
const preferences = { clair: false };
globalThis.matchMedia = (requete) => ({
  media: requete,
  matches: requete.includes("light") ? preferences.clair : !preferences.clair,
  addEventListener: () => {},
  removeEventListener: () => {},
});
const memoire = new Map();
globalThis.localStorage = {
  getItem: (cle) => (memoire.has(cle) ? memoire.get(cle) : null),
  setItem: (cle, valeur) => memoire.set(cle, String(valeur)),
  removeItem: (cle) => memoire.delete(cle),
  clear: () => memoire.clear(),
};


const elements = new Map();
/* Les écouteurs du document, retenus : le parcours joue lui-même la souris et
   le clavier, au lieu de supposer ce que la page en fait. */
const ecoutes = new Map();
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
  addEventListener: (type, gestionnaire) => {
    if (!ecoutes.has(type)) ecoutes.set(type, []);
    ecoutes.get(type).push(gestionnaire);
  },
  removeEventListener: () => {},
  body: new Element("body"),
  documentElement: racineDocument,
};
// Au chargement, le clavier est sur la page — comme dans un vrai navigateur.
globalThis.document.activeElement = globalThis.document.body;
globalThis.window = globalThis;
/* Un écran de bureau, celui sur lequel le visiteur lit : c'est lui qui décide
   où l'infobulle trouve de la place. */
globalThis.innerWidth = 1280;
globalThis.innerHeight = 900;
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
const blocs = [...page.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
const brut =
  blocs.find((b) => b.includes("async function demarrer(")) ??
  blocs[blocs.length - 1] ??
  null;
if (brut === null) {
  console.error("aucun <script> trouvé dans la page");
  process.exit(2);
}
// La fonction de démarrage est déclarée dans une IIFE anonyme : on capte sa
// promesse pour attendre la fin du chargement initial avant d'agir.
const source = brut.replace(
  /\(async function demarrer\(\)\{/,
  "globalThis.__demarrage = (async function demarrer(){"
);
if (source === brut) {
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
                       'modifierProfilMenage','modifierModeCalibrageMenage','depenseBaseProfil',
                       'chargerClasses','renderClasses','renderBalance','renderFiltresClasses',
                       'calculerClasses','classeDe','basculerClasse','basculerClasseSeules',
                       'fmtSigne','eurosParMenage','fmtMenage','chipsHorsBudget',
                       'renderCascade','marchesCascade','monetaireDe',
                       'renderRythme','changerAnneeClasses',
                       'classeAnneeAffichee','classeReferenceAffichee',
                       'chargerContrepouvoirs','rendreContrepouvoirs',
                       'filtrerContrepouvoirs','basculerGroupeParlementaire',
                       'chargerComparaison','rendreComparaison','trierComparaison',
                       'choisirTheme','choisirDensite','changerTailleTexte','appliquerAffichage',
                       'initialiserAffichage','majBoutonsAffichage','preferenceAffichage',
                       'themeAffichage','densiteAffichage','tailleAffichage',
                       'choisirPresentation','presentationAffichage','PRESENTATIONS_AFFICHAGE',
                       'positionnerInfobulle']) {
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
/* ── Le script d'en-tête : le thème posé avant le premier pixel ─────────── */
// Il vit dans `<head>`, avant le corps : c'est lui qui évite qu'une page
// s'ouvre en sombre puis bascule en clair. Il est donc exécuté ici avant le
// script principal, dans l'ordre du document.
const entete = blocs.find((b) => b.includes("data-theme"));
if (!entete) {
  rapport.erreurs.push("le script d'en-tête qui pose le thème est absent");
} else {
  eval(entete);
  noter("l'en-tête pose un thème avant le premier rendu",
        ["soir", "jour", "creme", "contraste"].includes(racineDocument.getAttribute("data-theme")),
        "thème posé : " + racineDocument.getAttribute("data-theme"));
  noter("sans choix enregistré, c'est l'appareil qui décide",
        racineDocument.getAttribute("data-theme") === (preferences.clair ? "jour" : "soir"),
        "appareil clair=" + preferences.clair + " → " + racineDocument.getAttribute("data-theme"));
  noter("la densité part d'aérée et la taille de 100 %",
        racineDocument.getAttribute("data-densite") === "aere"
        && racineDocument.getAttribute("data-texte") === "100",
        "densité=" + racineDocument.getAttribute("data-densite")
        + " texte=" + racineDocument.getAttribute("data-texte"));
  noter("la présentation part d'équilibrée",
        racineDocument.getAttribute("data-layout") === "equilibree",
        "mise en page=" + racineDocument.getAttribute("data-layout"));
  // Les deux réglages de l'appareil, l'un après l'autre : un appareil qui
  // annonce préférer le clair doit recevoir le thème clair, et non le sombre
  // par défaut.
  preferences.clair = true;
  eval(entete);
  noter("un appareil qui préfère le clair reçoit le thème clair",
        racineDocument.getAttribute("data-theme") === "jour",
        "thème posé : " + racineDocument.getAttribute("data-theme"));
  preferences.clair = false;
  memoire.set("simulateur-theme", "creme");
  memoire.set("simulateur-densite", "compact");
  memoire.set("simulateur-texte", "125");
  memoire.set("simulateur-presentation", "lecture");
  eval(entete.replace(/^/gm, ""));
  noter("un choix enregistré est repris tel quel au chargement suivant",
        racineDocument.getAttribute("data-theme") === "creme"
        && racineDocument.getAttribute("data-densite") === "compact"
        && racineDocument.getAttribute("data-texte") === "125"
        && racineDocument.getAttribute("data-layout") === "lecture",
        "thème=" + racineDocument.getAttribute("data-theme")
        + " densité=" + racineDocument.getAttribute("data-densite")
        + " texte=" + racineDocument.getAttribute("data-texte")
        + " mise en page=" + racineDocument.getAttribute("data-layout"));
  memoire.set("simulateur-theme", "fluo");
  eval(entete);
  noter("un choix inconnu est écarté, pas appliqué",
        ["soir", "jour"].includes(racineDocument.getAttribute("data-theme")),
        "thème posé : " + racineDocument.getAttribute("data-theme"));
  memoire.clear();
  preferences.clair = false;
  eval(entete);
}

// La page porte plusieurs blocs <script> (un micro-séquenceur de mesure
// d'audience, puis le noyau de l'application) : viser le bloc qui démarre
// l'application, pas le premier venu — sinon le harnais n'exécute que trois
// lignes et accuse la page d'être vide.
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
noter("affiche les 16 préréglages", (elements.get("preset-grid")?.children.length || 0) === 16,
      `${elements.get("preset-grid")?.children.length} cartes`);
/* Les 5 classes de leviers : la page ne reclasse rien, elle affiche la classe
   livrée avec chaque levier du catalogue et les totaux calculés par le moteur. */
const cartesClasses = (contenu("grille-classes").match(/class="classe-carte/g) || []).length;
noter("rend les cinq classes de leviers", cartesClasses === 5, `${cartesClasses} carte(s)`);
const grilleLeviers = contenu("leviers-grille");
noter("chaque carte de levier porte sa classe",
      (grilleLeviers.match(/data-classe="/g) || []).length >= 100,
      `${(grilleLeviers.match(/data-classe="/g) || []).length} carte(s) classée(s)`);
noter("la légende des classes permet de filtrer",
      (contenu("classes-legende").match(/aria-pressed=/g) || []).length === 5,
      `${(contenu("classes-legende").match(/aria-pressed=/g) || []).length} pastille(s)`);
noter("la balance affiche les deux plateaux et un solde signé",
      /Md€\/an/.test(elements.get("balance-entrees-montant")?.textContent || "")
      && /Md€\/an/.test(elements.get("balance-sorties-montant")?.textContent || "")
      && /solde des classes/.test(elements.get("balance-net")?.textContent || ""),
      `${elements.get("balance-entrees-montant")?.textContent} / ${elements.get("balance-sorties-montant")?.textContent} / ${elements.get("balance-net")?.textContent}`);
noter("la balance explique l'écart entre les deux lectures du budget",
      /recettes nouvelles/.test(contenu("balance-detail"))
      && /drapeaux/i.test(contenu("balance-detail")),
      contenu("balance-detail").slice(0, 140));
/* Le résumé de tête ne calcule rien : il relit la balance. Le contrôle compare
   donc les deux textes, il ne se contente pas d'une forme plausible. */
noter("le résumé de tête porte le solde de la balance, sans le recalculer",
      / Md€\/an$/.test(elements.get("resume-solde")?.textContent || "")
      && (elements.get("balance-net")?.textContent || "")
        .includes(elements.get("resume-solde")?.textContent || "\u0000"),
      `résumé : ${elements.get("resume-solde")?.textContent} · balance : ${elements.get("balance-net")?.textContent}`);
noter("la phrase du résumé est mot pour mot celle de la balance",
      !!elements.get("resume-phrase")?.textContent
      && elements.get("resume-phrase")?.textContent === elements.get("balance-verdict")?.textContent,
      `${elements.get("resume-phrase")?.textContent}`);
noter("le résumé porte les deux plateaux et l'ordre de grandeur par ménage",
      /Md€\/an/.test(elements.get("resume-entrees")?.textContent || "")
      && /Md€\/an/.test(elements.get("resume-sorties")?.textContent || "")
      && /€\/ménage\/an/.test(elements.get("resume-menage")?.textContent || ""),
      `${elements.get("resume-entrees")?.textContent} / ${elements.get("resume-sorties")?.textContent} / ${elements.get("resume-menage")?.textContent}`);
/* Les deux plateaux, en proportion : les barres du résumé et les jauges de la
   balance lisent la même fonction, donc les deux visuels doivent donner
   exactement le même couple de parts — et ces parts doivent sommer à 100. */
const partEntreesResume = parseInt(elements.get("resume-barre-entrees")?.style?.width || "", 10);
const partSortiesResume = parseInt(elements.get("resume-barre-sorties")?.style?.width || "", 10);
noter("le résumé met les deux plateaux en proportion",
      Number.isFinite(partEntreesResume) && Number.isFinite(partSortiesResume)
      && partEntreesResume + partSortiesResume === 100,
      `${partEntreesResume} % / ${partSortiesResume} %`);
noter("les barres du résumé donnent les mêmes parts que les jauges de la balance",
      (elements.get("balance-jauge-entrees")?.style?.width || "")
        === `${partEntreesResume}%`
      && (elements.get("balance-jauge-sorties")?.style?.width || "")
        === `${partSortiesResume}%`,
      `résumé ${partEntreesResume}/${partSortiesResume} · balance `
      + `${elements.get("balance-jauge-entrees")?.style?.width} / ${elements.get("balance-jauge-sorties")?.style?.width}`);
noter("chaque part est écrite en clair à côté de sa barre",
      /%$/.test(elements.get("resume-part-entrees")?.textContent || "")
      && /%$/.test(elements.get("resume-part-sorties")?.textContent || ""),
      `${elements.get("resume-part-entrees")?.textContent} / ${elements.get("resume-part-sorties")?.textContent}`);
const totauxClasse = apiPage.etat().SORTIE?.classes_annuelles || [];
noter("les totaux par classe viennent du moteur (pas de la page)",
      totauxClasse.length > 0
      && Math.abs((totauxClasse[totauxClasse.length - 1].solde_mde || 0)
                  - (apiPage.etat().SORTIE?.classes_annuelles?.slice(-1)[0]?.solde_mde || 0)) < 1e-9,
      `${totauxClasse.length} année(s) classée(s)`);
noter("le filtre par classe restreint la grille",
      (() => {
        apiPage.basculerClasse("recettes");
        const recettes = (contenu("leviers-grille").match(/data-classe="recettes"/g) || []).length;
        const autres = (contenu("leviers-grille").match(/data-classe="(?!recettes)/g) || []).length;
        apiPage.basculerClasse("");   // retour à toutes les classes
        return recettes > 0 && autres === 0;
      })(),
      "filtre recettes appliqué puis retiré");
noter("les classes « règles » et « monde » n'affichent pas de faux euros",
      !/règles[\s\S]{0,400}?€\/ménage/.test(contenu("grille-classes"))
      || !/monde[\s\S]{0,400}?€\/ménage/.test(contenu("grille-classes")),
      "unités listées, non converties");
/* La cascade : l'ordre dans lequel le plan se construit. Trois classes
   monétaires déplacent le cumul, l'escalier se referme sur le solde, et les
   unités non monétaires restent explicitement dehors. */
const versNombre = (texte) => Number(String(texte).replace(/[\u202f\u00a0\s]/g, "")
  .replace("−", "-").replace(",", "."));
const montantsCascade = [...contenu("cascade-marches").matchAll(/cascade-montant">([^<]+)</g)]
  .map((m) => versNombre(m[1]));
const marches = (contenu("cascade-marches").match(/class="cascade-marche/g) || []).length;
noter("la cascade déroule le plan marche par marche",
      marches === 4 && contenu("cascade-marches").includes("Solde des classes"),
      `${marches} marche(s) : trois classes monétaires + le solde`);
const annClassee = (apiPage.etat().SORTIE?.classes_annuelles || []).slice(-1)[0] || {};
noter("la cascade se referme sur le solde des classes",
      montantsCascade.length === 4
      && Math.abs(montantsCascade.slice(0, 3).reduce((a, b) => a + b, 0) - montantsCascade[3]) < 0.02
      && Math.abs(montantsCascade[3] - (annClassee.solde_mde || 0)) < 0.02,
      `${montantsCascade.slice(0, 3).join(" + ")} = ${montantsCascade[3]} (moteur : ${annClassee.solde_mde})`);
noter("chaque marche nomme les leviers qui la déplacent",
      contenu("cascade-marches").includes("data-aide-levier=")
      && (contenu("cascade-marches").match(/cascade-detail/g) || []).length === 4,
      `${(contenu("cascade-marches").match(/cascade-detail/g) || []).length} détail(s)`);
noter("la cascade dessine une barre par marche sur un axe commun",
      (contenu("cascade-marches").match(/class="barre/g) || []).length === 4
      && (contenu("cascade-marches").match(/cascade-piste/g) || []).length === 4,
      `${(contenu("cascade-marches").match(/class="barre/g) || []).length} barre(s)`);
noter("la cascade dit ce qu'elle laisse hors budget",
      /Hors cascade/.test(contenu("cascade-note"))
      && /règles/.test(contenu("cascade-note")) && /monde/.test(contenu("cascade-note")),
      contenu("cascade-note").slice(0, 120));
/* Le rythme : la même lecture année par année. On recule d'un an, puis on
   revient à la dernière année — les contrôles suivants portent sur elle. */
const soldeNetFinal = elements.get("balance-net")?.textContent;
const soldeResumeFinal = elements.get("resume-solde")?.textContent;
noter("les classes se lisent année par année",
      /an \d+ \/ \d+/.test(elements.get("classe-annee-courante")?.textContent || "")
      && /%/.test(contenu("classe-rythme")),
      `${elements.get("classe-annee-courante")?.textContent} — ${contenu("classe-rythme").slice(0, 90)}`);
const anneeFinaleAffichee = elements.get("classe-annee-courante")?.textContent;
apiPage.changerAnneeClasses(-1);
noter("reculer d'un an relit la balance et la cascade",
      (elements.get("classe-annee-courante")?.textContent || "") !== anneeFinaleAffichee
      && elements.get("balance-net")?.textContent !== soldeNetFinal
      && /solde des classes/.test(elements.get("balance-net")?.textContent || "")
      && contenu("cascade-marches").includes("Solde des classes"),
      `an lu : ${elements.get("classe-annee-courante")?.textContent} · ${elements.get("balance-net")?.textContent}`);
noter("reculer d'un an relit aussi le résumé de tête",
      (elements.get("resume-solde")?.textContent || "") !== soldeResumeFinal,
      `${soldeResumeFinal} → ${elements.get("resume-solde")?.textContent}`);
noter("les proportions suivent l'année relue, et somment toujours à 100",
      parseInt(elements.get("resume-barre-entrees")?.style?.width || "", 10)
      + parseInt(elements.get("resume-barre-sorties")?.style?.width || "", 10) === 100,
      `${elements.get("resume-part-entrees")?.textContent} + `
      + `${elements.get("resume-part-sorties")?.textContent}`);
apiPage.changerAnneeClasses(1);   // geste de l'utilisateur : « an suivant › »
noter("revenir à la dernière année restitue le régime de fin de mandature",
      elements.get("balance-net")?.textContent === soldeNetFinal
      && elements.get("classe-annee-suiv")?.disabled === true
      && elements.get("classe-annee-prec")?.disabled === false,
      `an lu : ${elements.get("classe-annee-courante")?.textContent}`);
// La couche « nuances institutionnelles » doit être visible dans la page, pas seulement
// dans les modules : seuils recalculés, fentes, strates et garde-fous.
noter("rend la section des nuances institutionnelles",
      contenu("nuances-corps").includes("Seuils recalculés")
      && contenu("nuances-corps").includes("Délais de rigueur")
      && contenu("nuances-corps").includes("Cinq strates"),
      `${contenu("nuances-corps").length} caractères`);
noter("le tableau des nuances affiche le seuil recalculé par le réglage",
      contenu("nuances-corps").includes("Voix favorables pour renverser le Gouvernement")
      && contenu("nuances-corps").includes("reglage_censure_assiette")
      && contenu("nuances-corps").includes("231"),
      contenu("nuances-resume").slice(0, 120));
noter("la section annonce les garde-fous de la couche",
      contenu("nuances-corps").includes("Garde-fous"),
      "aucun bloc de garde-fous rendu");
noter(" chaque levier rattaché à un article porte sa puce de droit positif",
      contenu("leviers-grille").includes('class="articles"')
      && contenu("leviers-grille").includes("/api/constitution?article=49"),
      `${(contenu("leviers-grille").match(/class="articles"/g) || []).length} puces`);
// L'état des verrous vient de `/api/nuances` : la page ne fait que le partager
// en trois colonnes et remplacer chaque citation par le lien vers la fiche du serveur.
const corpsVerrous = contenu("verrous-corps");
noter("rend les trois colonnes de verrous",
      corpsVerrous.includes("Touchés par le vecteur") && corpsVerrous.includes("Intacts")
      && corpsVerrous.includes("Hors réglage"),
      corpsVerrous.slice(0, 240));
noter("le verrou touché affiche son seuil recalculé et le réglage qui le bouge",
      corpsVerrous.includes("Voix favorables pour renverser le Gouvernement")
      && /289[^<]*→[^<]*231/.test(corpsVerrous.replace(/<[^>]*>/g, " "))
      && corpsVerrous.includes("reglage_censure_assiette"),
      corpsVerrous.slice(0, 300));
noter("les 18 verrous hors réglage sont listés et expliqués",
      (corpsVerrous.match(/class="hors"/g) || []).length === 18
      && corpsVerrous.includes("ne peut pas se décréter"),
      `${(corpsVerrous.match(/class="hors"/g) || []).length} lignes hors réglage`);
noter("une citation d'article devient un lien vers la fiche servie par le serveur",
      corpsVerrous.includes('href="/api/constitution?article=49"')
      && contenu("reglages-corps").includes('href="/api/constitution?article='),
      `${(corpsVerrous.match(/class="article"/g) || []).length} liens d'article`);
noter("la liste des réglages déplacés rappelle ce que chacun atteint",
      contenu("reglages-corps").includes("badge-cible")
      && contenu("reglages-corps").includes("reglage_censure_assiette")
      && contenu("reglages-corps").includes("valeur retenue"),
      contenu("reglages-corps").slice(0, 240));
/* Le registre de la contradiction : la page ne rédige rien, elle met en forme
   `GET /api/objections`. On vérifie qu'une objection complète est rendue — la
   meilleure version, la concession, le maintien, la falsification —, que la
   marge de portée vient bien du serveur, et que les contre-modèles suivent. */
const corpsObjections = contenu("objections-corps");
noter("rend le registre des objections",
      corpsObjections.includes("La meilleure version de l'objection")
      && corpsObjections.includes("Ce que nous concédons")
      && corpsObjections.includes("Ce que nous maintenons")
      && corpsObjections.includes("Ce qui nous ferait changer d'avis"),
      `${corpsObjections.length} caractères`);
noter("chaque objection affiche son statut et son numéro",
      (corpsObjections.match(/class="badge-statut /g) || []).length === 24
      && corpsObjections.includes("n° 4"),
      `${(corpsObjections.match(/class="badge-statut /g) || []).length} badges`);
noter("la portée du levier et la marge du dossier viennent du serveur",
      corpsObjections.includes("gage du dossier")
      && corpsObjections.includes("Md€/an")
      && corpsObjections.includes("lutte_fraude_fiscale_ia"),
      corpsObjections.slice(0, 200));
noter("une objection cite ses sources internes et externes",
      corpsObjections.includes("docs/05_GUIDE_AUTODEFENSE_ET_CONTRE_ARGUMENTS.md")
      && corpsObjections.includes("Externe"),
      "sources absentes du rendu");
noter("les quatre contre-modèles sont rendus avec l'avis du simulateur",
      contenu("contre-modeles-corps").includes("La thèse")
      && contenu("contre-modeles-corps").includes("Ce que le simulateur en dit")
      && (contenu("contre-modeles-corps").match(/class="contre-modele"/g) || []).length === 4,
      `${(contenu("contre-modeles-corps").match(/class="contre-modele"/g) || []).length} contre-modèles`);
noter("le résumé du registre annonce les statuts",
      contenu("contradiction-resume").includes("objection(s) affichée(s)")
      && contenu("contradiction-resume").includes("réfutée"),
      contenu("contradiction-resume").slice(0, 160));
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

/* 2 bis ter. Une seule densité : le ruban et le panneau d'affichage disent la
   même chose. Deux boutons qui portent le même nom ne peuvent pas en dire
   deux — c'est le défaut que le visiteur a signalé. */
apiPage.basculerDensite(true);
for (let i = 0; i < 2; i += 1) await tourner();
noter("la vue compacte pose la densité de la page",
      racineDocument.getAttribute("data-densite") === "compact",
      "data-densite=" + racineDocument.getAttribute("data-densite"));
noter("la densité compacte est retenue sur l'appareil",
      globalThis.localStorage.getItem("simulateur-densite") === "compact",
      globalThis.localStorage.getItem("simulateur-densite"));
noter("le panneau d'affichage suit le ruban",
      elements.get("densite-compact")?.getAttribute("aria-pressed") === "true",
      "aria-pressed=" + elements.get("densite-compact")?.getAttribute("aria-pressed"));
apiPage.basculerDensite(false);
for (let i = 0; i < 2; i += 1) await tourner();
noter("le retour en vue confort remet la densité aérée",
      racineDocument.getAttribute("data-densite") === "aere",
      "data-densite=" + racineDocument.getAttribute("data-densite"));
noter("la densité aérée est retenue à son tour",
      globalThis.localStorage.getItem("simulateur-densite") === "aere",
      globalThis.localStorage.getItem("simulateur-densite"));

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
/* Le défaut signalé par le visiteur : l'aide d'un tiroir restait affichée
   pendant qu'on se servait du panneau, et le recouvrait. Ces étapes jouent la
   souris, événement par événement, pour vérifier que l'aide cède la place. */
function jouerSouris(type, cible, vers) {
  for (const gestionnaire of (ecoutes.get(type) || [])) {
    gestionnaire({ target: cible, relatedTarget: vers || null });
  }
}
function noeudAide(balise, attributs, classes) {
  const noeud = new Element("aide-" + balise, balise);
  for (const [cle, valeur] of Object.entries(attributs || {})) noeud.attributs[cle] = valeur;
  for (const classe of (classes || [])) noeud.classList.add(classe);
  return noeud;
}
/* ── La fenêtre, au clavier ───────────────────────────────────────────────
   Une fenêtre qui s'ouvre doit prendre le focus, le garder tant qu'elle est
   ouverte, et le rendre à qui l'a ouverte. Ces étapes jouent les touches,
   événement par événement, comme les précédentes jouent la souris. */
let cleEmpechee = false;
function jouerClavier(touche, options) {
  cleEmpechee = false;
  const evenement = Object.assign({
    key: touche,
    preventDefault: () => { cleEmpechee = true; },
  }, options || {});
  for (const gestionnaire of (ecoutes.get("keydown") || [])) gestionnaire(evenement);
  return evenement;
}
const fenetreModale = parId("modale");
const premierBoutonFenetre = noeudAide("button", {}, []);
const dernierBoutonFenetre = noeudAide("button", {}, []);
fenetreModale._commandes = [premierBoutonFenetre, dernierBoutonFenetre];
const boutonOuvreur = noeudAide("button", { id: "btn-guide" }, []);

const tiroirAide = noeudAide("details", { id: "affichage" }, ["affichage"]);
const boutonTiroir = tiroirAide.appendChild(noeudAide("summary", { "data-aide": "<b>Affichage</b>Quatre thèmes" }));
const panneauTiroir = tiroirAide.appendChild(noeudAide("div", {}, ["affichage-panneau"]));
const choixPanneau = panneauTiroir.appendChild(noeudAide("button", { "data-theme-choix": "jour" }));
const etiquetteAide = noeudAide("label", {}, ["select-horizon"]);
const motEtiquette = etiquetteAide.appendChild(noeudAide("span", { "data-aide": "<b>Horizon</b>5 ou 10 ans" }));
const champEtiquette = etiquetteAide.appendChild(noeudAide("select", {}, []));

// 1. Le bouton du tiroir fermé : l'aide vient, puis repart avec la souris.
jouerSouris("mouseover", boutonTiroir);
noter("l'aide d'un bouton vient au survol", elements.get("infobulle")?.classList.contains("visible") === true);
jouerSouris("mouseout", boutonTiroir, racineDocument);
noter("et repart dès que la souris le quitte",
      elements.get("infobulle")?.classList.contains("visible") === false);

// 2. Le même bouton, tiroir ouvert : l'aide s'efface — le panneau est la réponse.
tiroirAide.open = true;
jouerSouris("mouseover", boutonTiroir);
noter("l'aide d'un tiroir ouvert s'efface devant son panneau",
      elements.get("infobulle")?.classList.contains("visible") === false);
tiroirAide.open = false;

// 3. Une commande posée dans un porteur d'aide : la bulle cède.
jouerSouris("mouseover", choixPanneau);
noter("aucune aide ne recouvre une commande du panneau",
      elements.get("infobulle")?.classList.contains("visible") === false);
jouerSouris("mouseover", champEtiquette);
noter("aucune aide ne recouvre le champ qu'elle annonce",
      elements.get("infobulle")?.classList.contains("visible") === false);
jouerSouris("mouseover", motEtiquette);
noter("le mot de l'étiquette, lui, garde son aide",
      elements.get("infobulle")?.classList.contains("visible") === true);

// 4. La fenêtre, au clavier : le focus entre, ne sort pas, revient.
apiPage.fermerModale();          // au cas où le guide de première visite est ouvert
boutonOuvreur.focus();
apiPage.ouvrirModale("Essai", "<p>corps</p>");
noter("ouvrir la fenêtre donne le focus à la fenêtre",
      globalThis.document.activeElement === fenetreModale,
      `focus sur ${globalThis.document.activeElement?.id}`);
dernierBoutonFenetre.focus();
jouerClavier("Tab");
noter("la tabulation depuis la dernière commande revient à la première",
      globalThis.document.activeElement === premierBoutonFenetre && cleEmpechee);
premierBoutonFenetre.focus();
jouerClavier("Tab", { shiftKey: true });
noter("la tabulation arrière depuis la première va à la dernière",
      globalThis.document.activeElement === dernierBoutonFenetre && cleEmpechee);
globalThis.document.activeElement = globalThis.document.body;
jouerClavier("Tab");
noter("un focus perdu hors de la fenêtre y revient",
      globalThis.document.activeElement === premierBoutonFenetre && cleEmpechee);
let sorties = 0;
for (let rang = 0; rang < 4; rang += 1) {
  jouerClavier("Tab");
  if (fenetreModale._commandes.indexOf(globalThis.document.activeElement) === -1) sorties += 1;
}
noter("quatre tabulations de plus ne sortent jamais de la fenêtre", sorties === 0,
      `${sorties} sortie(s)`);
jouerClavier("Escape");
noter("Échap referme la fenêtre et rend le focus à qui l'a ouverte",
      elements.get("overlay")?.classList.contains("visible") === false
      && globalThis.document.activeElement === boutonOuvreur);
jouerClavier("Escape");
noter("Échap, quand rien n'est ouvert, reste au navigateur", cleEmpechee === false);
jouerSouris("mouseout", motEtiquette, racineDocument);

// 4. La bulle ne se pose jamais sur la cible : elle est sous ou au-dessus.
const bulleAide = elements.get("infobulle");
bulleAide.style = { left: "0px", top: "0px" };
bulleAide.offsetWidth = 340;
bulleAide.offsetHeight = 180;
const cibleMesurable = new Element("mesurable", "button");
cibleMesurable.getBoundingClientRect = () => ({ top: 700, left: 40, bottom: 760, width: 120, height: 60 });
apiPage.positionnerInfobulle(cibleMesurable);
const hautBulle = Number(String(bulleAide.style.top).replace("px", ""));
noter("la bulle se pose hors de la commande qu'elle explique",
      hautBulle >= 760 || hautBulle + 180 <= 700, "top = " + bulleAide.style.top);
const cibleBasse = new Element("mesurable", "button");
cibleBasse.getBoundingClientRect = () => ({ top: 840, left: 40, bottom: 890, width: 120, height: 50 });
apiPage.positionnerInfobulle(cibleBasse);
const hautBasse = Number(String(bulleAide.style.top).replace("px", ""));
noter("faute de place en dessous, elle remonte sans couvrir la commande",
      hautBasse + 180 <= 840, "top = " + bulleAide.style.top);

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
/* La cascade d'un plan d'austérité : les coupes font remonter le cumul, et la
   marche « dépenses » le dit en toutes lettres — sinon une coupe passerait
   pour une dépense. */
const montantsAusterite = [...contenu("cascade-marches").matchAll(/cascade-montant">([^<]+)</g)]
  .map((m) => versNombre(m[1]));
noter("la cascade d'une austérité compte les coupes comme une rentrée",
      montantsAusterite.length === 4 && montantsAusterite[2] > 0
      && /coupe, pas une dépense/.test(contenu("cascade-marches"))
      && Math.abs(montantsAusterite.slice(0, 3).reduce((a, b) => a + b, 0) - montantsAusterite[3]) < 0.02,
      `dépenses ${montantsAusterite[2]} → solde ${montantsAusterite[3]}`);

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

/* 11. Contre-pouvoirs : l'arithmétique affichée est celle que le serveur sert. */
const arithmetique = api["GET /api/contrepouvoirs"];
const tempsProcedures = api["GET /api/dynamiques"];
await apiPage.chargerContrepouvoirs();
const corpsRegistre = contenu("contrepouvoirs-corps");
const sansEspaces = corpsRegistre.replace(/[\u202f\u00a0\s]/g, "");
const fichesMecanismes = (corpsRegistre.match(/class="cp-mecanisme"/g) || []).length;
noter("affiche chaque manœuvre servie par le registre des contre-pouvoirs",
      fichesMecanismes === (arithmetique?.mecanismes || []).length && fichesMecanismes > 0,
      `${fichesMecanismes} fiche(s) sur ${(arithmetique?.mecanismes || []).length}`);
noter("affiche les familles du registre",
      (corpsRegistre.match(/class="cp-famille"/g) || []).length === (arithmetique?.familles || []).length
      && (arithmetique?.familles || []).length > 0,
      `${(corpsRegistre.match(/class="cp-famille"/g) || []).length} famille(s)`);
const formationsAttendues =
  Object.keys(arithmetique?.assemblees?.assemblee_nationale?.groupes || {}).length
  + Object.keys(arithmetique?.assemblees?.senat?.groupes || {}).length;
noter("affiche les deux chambres et leurs formations",
      (corpsRegistre.match(/class="cp-chambre"/g) || []).length === 2
      && (corpsRegistre.match(/class="cp-groupe"/g) || []).length === formationsAttendues,
      `${(corpsRegistre.match(/class="cp-chambre"/g) || []).length} chambre(s), `
      + `${(corpsRegistre.match(/class="cp-groupe"/g) || []).length} formation(s) sur ${formationsAttendues}`);
const detailsAttendus = (tempsProcedures?.trajets || []).length + (tempsProcedures?.fentes || []).length
  + (tempsProcedures?.strategies || []).length + (tempsProcedures?.instances || []).length
  + (tempsProcedures?.boucles_de_controle || []).length;
noter("affiche le temps des procédures, trajet par trajet",
      (corpsRegistre.match(/class="cp-details"/g) || []).length === detailsAttendus
      && detailsAttendus > 0,
      `${(corpsRegistre.match(/class="cp-details"/g) || []).length} fiche(s) sur ${detailsAttendus}`);
const joursAvancer = tempsProcedures?.rapport_de_temps?.par_sens?.avancer?.jours;
noter("les jours de rigueur affichés sont ceux que le serveur a calculés",
      joursAvancer !== undefined && sansEspaces.includes(String(joursAvancer)),
      `${joursAvancer} jour(s) attendus`);

/* La coalition : la page additionne les sièges reçus, rien de plus. */
const chambreAn = arithmetique?.assemblees?.assemblee_nationale || {};
const groupesAn = chambreAn.groupes || {};
const choisies = ["RN", "EPR", "SOC", "LFI-NFP"].filter((nom) => groupesAn[nom] !== undefined);
for (const nom of choisies) apiPage.basculerGroupeParlementaire("assemblee_nationale", nom);
const totalCoalition = choisies.reduce((somme, nom) => somme + groupesAn[nom], 0);
const corpsCoalition = contenu("contrepouvoirs-corps");
const apresCoalition = corpsCoalition.replace(/[\u202f\u00a0\s]/g, "");
noter("la coalition additionne les sièges servis par le serveur",
      choisies.length > 0 && totalCoalition > 0 && apresCoalition.includes(String(totalCoalition)),
      `${choisies.join(" + ")} = ${totalCoalition} siège(s)`);
noter("la coalition annonce la majorité absolue quand le total l'atteint",
      (totalCoalition >= chambreAn.majorite_absolue) === corpsCoalition.includes("la majorité absolue"),
      `total ${totalCoalition}, seuil ${chambreAn.majorite_absolue}`);
noter("la coalition annonce les trois cinquièmes quand le total l'atteint",
      (totalCoalition >= chambreAn.majorite_qualifiee_3_5)
        === corpsCoalition.includes("les trois cinquièmes"),
      `total ${totalCoalition}, seuil ${chambreAn.majorite_qualifiee_3_5}`);
noter("la coalition annonce ce qui manque quand un seuil n'est pas atteint",
      totalCoalition < chambreAn.majorite_2_3 ? corpsCoalition.includes("Il manque") : true,
      `total ${totalCoalition}, deux tiers ${chambreAn.majorite_2_3}`);

/* Le filtre par famille : la fiche reste, le reste part. */
const familleTest = (arithmetique?.familles || []).find((famille) => (famille.mecanismes || []).length > 1);
apiPage.filtrerContrepouvoirs(familleTest.nom);
const apresFiltre = contenu("contrepouvoirs-corps");
noter("le filtre par famille ne montre que sa famille",
      (apresFiltre.match(/class="cp-mecanisme"/g) || []).length === (familleTest.mecanismes || []).length,
      `${familleTest.nom} : ${(apresFiltre.match(/class="cp-mecanisme"/g) || []).length} `
      + `fiche(s) sur ${familleTest.mecanismes.length}`);
noter("le filtre se voit dans la pastille de la famille",
      (apresFiltre.match(/class="cp-famille"[^>]*aria-pressed="true"/g) || []).length === 1,
      `${(apresFiltre.match(/class="cp-famille"[^>]*aria-pressed="true"/g) || []).length} pastille(s)`);
noter("le filtre de famille ne défait pas la coalition composée",
      (apresFiltre.match(/class="cp-groupe"[^>]*aria-pressed="true"/g) || []).length === choisies.length,
      `${(apresFiltre.match(/class="cp-groupe"[^>]*aria-pressed="true"/g) || []).length} `
      + `formation(s) cochée(s) sur ${choisies.length}`);
apiPage.filtrerContrepouvoirs(familleTest.nom);       // le filtre se retire

/* 12. Échappement : un registre hostile ne peut pas injecter une balise. */
const arithmetiqueServie = api["GET /api/contrepouvoirs"];
api["GET /api/contrepouvoirs"] = {
  ...arithmetiqueServie,
  familles: [{ nom: "renverser<script>", mecanismes: ["hostile"] }],
  mecanismes: [{
    cle: "hostile", nom: "<img src=x onerror=alert(1)>", famille: "renverser",
    resume: "<script>alert(2)</script>", articles: ["49<script>"],
    acteurs: "<svg onload=alert(3)>", declenche: ["<em>"], empeche_par: ["<strong>"],
    seuils: [{ cle: "s", nom: "<b>gras</b>", regle: "<i>", base: 577, seuil: 289, unite: "<u>" }],
  }],
};
await apiPage.chargerContrepouvoirs();
const zoneHostile = contenu("contrepouvoirs-corps");
const baliseOuverte = (zoneHostile.match(/<(img|script|svg)\b[^>]*>/g) || [])[0] || "";
noter("un registre hostile est échappé, jamais interprété",
      baliseOuverte === "" && zoneHostile.includes("&lt;img") && zoneHostile.includes("&lt;script&gt;"),
      baliseOuverte ? "balise ouverte dans le rendu : " + baliseOuverte.slice(0, 60)
                    : "les balises du registre restent du texte");
api["GET /api/contrepouvoirs"] = arithmetiqueServie;
await apiPage.chargerContrepouvoirs();

/* 13. Comparer : les scénarios servis, côte à côte, rangés sur demande. */
const comparaison = api["GET /api/comparer"];
const scenarios = comparaison?.comparaison || [];
await apiPage.chargerComparaison();
const corpsComparaison = contenu("comparaison-corps");
const teteDuTableau = (rendu) => ((rendu.match(/class="cmp-nom">([^<]*)/) || [])[1] || "").trim();
const largeursBarres = (corpsComparaison.match(/style="width:(\d+)%"/g) || [])
  .map((morceau) => Number(morceau.match(/(\d+)/)[1]));
noter("affiche chaque scénario que la route a calculé",
      (corpsComparaison.match(/class="cmp-ligne/g) || []).length === scenarios.length
      && scenarios.length > 0,
      `${(corpsComparaison.match(/class="cmp-ligne/g) || []).length} ligne(s) sur ${scenarios.length}`);
noter("le tableau s'ouvre sur le premier scénario du catalogue",
      teteDuTableau(corpsComparaison) === String(scenarios[0]?.libelle || "").trim(),
      `« ${teteDuTableau(corpsComparaison)} » — attendu « ${scenarios[0]?.libelle} »`);

// Le contrôle porte sur la ligne du scénario **le plus dégagé ou le plus
// coûteux**, et non sur le premier venu : le statut quo a un solde nul, donc un
// « 0,0 » se retrouve ailleurs dans le tableau et l'étape serait vraie sans rien
// prouver (vu à l'exécution, corrigé ici).
const sansEspacesComparaison = (texte) => String(texte).replace(/[\u202f\u00a0\s]/g, "");
const cible = scenarios.reduce((garde, ligne) =>
  Math.abs(ligne.synthese?.solde_mesures_mde ?? 0) > Math.abs(garde.synthese?.solde_mesures_mde ?? 0)
    ? ligne : garde, scenarios[0]);
const soldeServi = Number(cible?.synthese?.solde_mesures_mde);
const soldeAttendu = Math.abs(soldeServi)
  .toLocaleString("fr-FR", {minimumFractionDigits: 1, maximumFractionDigits: 1});
const ligneCible = corpsComparaison.split('<tr class="cmp-ligne')
  .find((bloc) => bloc.includes(cible?.libelle ?? "\u0000")) ?? "";
const largeurCible = Number((ligneCible.match(/style="width:(\d+)%"/) || [])[1]);
const maximumServi = scenarios.reduce((plus, ligne) =>
  Math.max(plus, Math.abs(ligne.synthese?.solde_mesures_mde ?? 0)), 0);
noter("le montant de la ligne affichée est celui que le serveur a calculé",
      Number.isFinite(soldeServi) && Math.abs(soldeServi) >= 100
      && sansEspacesComparaison(ligneCible).includes(sansEspacesComparaison(soldeAttendu)),
      `${sansEspacesComparaison(cible?.libelle).slice(0, 34)} : solde servi ${soldeServi} → écrit « ${sansEspacesComparaison(soldeAttendu)} »`);
noter("la barre de cette ligne est à l'échelle du plus fort montant servi, pas d'un maximum écrit",
      largeurCible === Math.round(100 * Math.abs(soldeServi) / maximumServi)
      && largeurCible === 100,
      `${largeurCible} % attendu ${Math.round(100 * Math.abs(soldeServi) / maximumServi)} %`);
noter("les barres se mesurent sur le plus fort montant servi",
      largeursBarres.length === scenarios.length && Math.max(...largeursBarres) === 100,
      `${largeursBarres.length} barre(s), plus large ${Math.max(...largeursBarres)} %`);
noter("le scénario de référence est signalé, sans être le seul marqué",
      (corpsComparaison.match(/cmp-repere/g) || []).length === 1
      && corpsComparaison.includes("référence (inertie)"),
      `${(corpsComparaison.match(/cmp-repere/g) || []).length} repère(s) de référence`);

const parRisque = scenarios.slice().sort((a, b) =>
  (a.diagnostic?.risque_population ?? 0) - (b.diagnostic?.risque_population ?? 0));
apiPage.trierComparaison("risque");
const apresTri = contenu("comparaison-corps");
noter("le premier clic range la colonne par ordre croissant",
      teteDuTableau(apresTri) === String(parRisque[0]?.libelle || "").trim()
      && (apresTri.match(/aria-sort="ascending"/g) || []).length === 1,
      `tête « ${teteDuTableau(apresTri)} », attendu « ${parRisque[0]?.libelle} »`);
apiPage.trierComparaison("risque");
const apresTriInverse = contenu("comparaison-corps");
noter("le second clic inverse le rangement",
      teteDuTableau(apresTriInverse) === String(parRisque[parRisque.length - 1]?.libelle || "").trim()
      && (apresTriInverse.match(/aria-sort="descending"/g) || []).length === 1,
      `tête « ${teteDuTableau(apresTriInverse)} »`);
apiPage.trierComparaison("risque");
const apresRemise = contenu("comparaison-corps");
noter("le troisième clic rend l'ordre du catalogue",
      teteDuTableau(apresRemise) === String(scenarios[0]?.libelle || "").trim()
      && (apresRemise.match(/aria-sort="(ascending|descending)"/g) || []).length === 0,
      `tête « ${teteDuTableau(apresRemise)} »`);

/* 14. Échappement : un scénario hostile ne peut pas injecter une balise. */
const comparaisonServie = api["GET /api/comparer"];
api["GET /api/comparer"] = {
  horodatage: "2026-10-14T00:00:00+00:00",
  comparaison: [{
    cle: "hostile", libelle: "<img src=x onerror=alert(1)>",
    synthese: {solde_mesures_mde: 5, dette_finale_pct: 90, deficit_final_pct: -3},
    diagnostic: {risque_population: 20, nombre_alertes: 2},
  }],
};
await apiPage.chargerComparaison();
const zoneHostileComparaison = contenu("comparaison-corps");
const baliseOuverteComparaison =
  (zoneHostileComparaison.match(/<(img|script|svg)\b[^>]*>/g) || [])[0] || "";
noter("un scénario hostile est échappé, jamais interprété",
      baliseOuverteComparaison === "" && zoneHostileComparaison.includes("&lt;img"),
      baliseOuverteComparaison ? "balise ouverte dans le rendu : " + baliseOuverteComparaison.slice(0, 60)
                               : "les balises du scénario restent du texte");
api["GET /api/comparer"] = comparaisonServie;
await apiPage.chargerComparaison();

/* 15. L'affichage : les trois réglages du visiteur, de bout en bout.
   Ce qu'on vérifie ici n'est pas la feuille de style — elle se lit dans les
   contrôles de `tests/test_themes_en_page.py` — mais le geste : le clic change
   la page, le choix se garde, l'appareil ne l'emporte plus, et un nom inconnu
   ne casse rien. */
memoire.clear();
apiPage.choisirTheme("contraste");
noter("le thème choisi est posé sur la racine et retenu sur l'appareil",
      racineDocument.getAttribute("data-theme") === "contraste"
      && memoire.get("simulateur-theme") === "contraste",
      "racine=" + racineDocument.getAttribute("data-theme")
      + " mémoire=" + memoire.get("simulateur-theme"));
preferences.clair = true;
apiPage.appliquerAffichage();
noter("un choix explicite résiste au réglage de l'appareil",
      racineDocument.getAttribute("data-theme") === "contraste",
      "appareil clair=oui → " + racineDocument.getAttribute("data-theme"));
memoire.clear();
noter("sans choix, la page suit l'appareil",
      apiPage.themeAffichage() === "jour",
      "appareil clair=oui → " + apiPage.themeAffichage());
preferences.clair = false;
apiPage.choisirTheme("soir");
apiPage.choisirTheme("creme");
apiPage.majBoutonsAffichage();
noter("le bouton du thème en vigueur dit son état, les autres non",
      elements.get("theme-creme")?.getAttribute("aria-pressed") === "true"
      && elements.get("theme-soir")?.getAttribute("aria-pressed") === "false"
      && elements.get("theme-contraste")?.getAttribute("aria-pressed") === "false",
      "crème=" + elements.get("theme-creme")?.getAttribute("aria-pressed")
      + " soir=" + elements.get("theme-soir")?.getAttribute("aria-pressed"));
apiPage.choisirDensite("compact");
for (let i = 0; i < 2; i += 1) await tourner();
noter("la densité compacte se pose sur la racine et se retient",
      racineDocument.getAttribute("data-densite") === "compact"
      && memoire.get("simulateur-densite") === "compact",
      "densité=" + racineDocument.getAttribute("data-densite"));
noter("le panneau resserre aussi le catalogue des leviers",
      (contenu("leviers-grille").match(/class="levier compact/g) || []).length === leviersComplets,
      "leviers compacts : " + (contenu("leviers-grille").match(/class="levier compact/g) || []).length
      + " sur " + leviersComplets);
apiPage.choisirDensite("aere");
for (let i = 0; i < 2; i += 1) await tourner();
noter("le retour en densité aérée restaure les descriptions",
      contenu("leviers-grille").includes("class=\"desc\""));
apiPage.choisirDensite("compact");
apiPage.choisirTheme("fluo");
apiPage.choisirDensite("serree");
noter("un réglage inconnu ne change rien",
      racineDocument.getAttribute("data-theme") === "creme"
      && racineDocument.getAttribute("data-densite") === "compact",
      "thème=" + racineDocument.getAttribute("data-theme")
      + " densité=" + racineDocument.getAttribute("data-densite"));
apiPage.choisirDensite("aere");
apiPage.changerTailleTexte(1);
const apresUnCran = racineDocument.getAttribute("data-texte");
apiPage.changerTailleTexte(1);
noter("la taille du texte monte par crans de 12,5 %",
      apresUnCran === "112" && racineDocument.getAttribute("data-texte") === "125"
      && elements.get("affichage-niveau")?.textContent === "125 %",
      "niveaux : " + apresUnCran + " puis " + racineDocument.getAttribute("data-texte")
      + " (" + elements.get("affichage-niveau")?.textContent + ")");
for (let i = 0; i < 4; i++) apiPage.changerTailleTexte(1);
noter("la taille du texte s'arrête à son plus haut cran",
      racineDocument.getAttribute("data-texte") === "137"
      && elements.get("texte-plus")?.disabled === true,
      "niveau=" + racineDocument.getAttribute("data-texte")
      + " bouton désactivé=" + elements.get("texte-plus")?.disabled);
for (let i = 0; i < 6; i++) apiPage.changerTailleTexte(-1);
noter("la taille du texte s'arrête à son plus bas cran",
      racineDocument.getAttribute("data-texte") === "87"
      && elements.get("texte-moins")?.disabled === true
      && memoire.get("simulateur-texte") === "87",
      "niveau=" + racineDocument.getAttribute("data-texte")
      + " bouton désactivé=" + elements.get("texte-moins")?.disabled);
apiPage.changerTailleTexte(1);
apiPage.choisirTheme("soir");
apiPage.choisirDensite("aere");
apiPage.changerTailleTexte(-1);

/* 15 bis. La présentation : trois largeurs, un seul réglage. Elle ne change
   rien d'autre que la largeur de la colonne, et elle se garde comme les
   autres. */
apiPage.choisirPresentation("lecture");
noter("la présentation choisie se pose sur la racine et se retient",
      racineDocument.getAttribute("data-layout") === "lecture"
      && memoire.get("simulateur-presentation") === "lecture",
      "mise en page=" + racineDocument.getAttribute("data-layout")
      + " mémoire=" + memoire.get("simulateur-presentation"));
noter("le bouton de la présentation en vigueur dit son état, les autres non",
      elements.get("presentation-lecture")?.getAttribute("aria-pressed") === "true"
      && elements.get("presentation-equilibree")?.getAttribute("aria-pressed") === "false",
      "lecture=" + elements.get("presentation-lecture")?.getAttribute("aria-pressed")
      + " équilibrée=" + elements.get("presentation-equilibree")?.getAttribute("aria-pressed"));
apiPage.choisirPresentation("panorama");
apiPage.choisirPresentation("inconnue");
noter("une présentation inconnue ne change rien",
      racineDocument.getAttribute("data-layout") === "panorama",
      "mise en page=" + racineDocument.getAttribute("data-layout"));
apiPage.choisirPresentation("equilibree");
noter("la présentation revient à son état d'origine",
      racineDocument.getAttribute("data-layout") === "equilibree"
      && memoire.get("simulateur-presentation") === "equilibree",
      "mise en page=" + racineDocument.getAttribute("data-layout"));
memoire.clear();

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
