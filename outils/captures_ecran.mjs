// outils/captures_ecran.mjs — photographier la page, pour la regarder.
//
// La suite de tests sait mesurer des couleurs, des octets et des jetons : elle
// ne sait pas voir. Ce script ouvre la page servie dans un vrai navigateur
// (Chromium, via Puppeteer) et en fait des photographies — quatre thèmes,
// quatre largeurs, les panneaux ouverts, les états, et une descente dans les
// sections. Il écrit aussi un `rapport.json` : les rectangles réellement
// occupés par les barres, les cadres et les panneaux.
//
// Il tourne là où un navigateur existe : dans l'intégration continue (voir
// .github/workflows/captures.yml) ou sur une machine qui a déjà Chromium :
//
//     node outils/captures_ecran.mjs                       # tout
//     node outils/captures_ecran.mjs --largeur 380         # une seule largeur
//     node outils/captures_ecran.mjs --navigateur /usr/bin/chromium
//
// Les images sortent dans captures/ (non versionné : ce sont des mesures, pas
// des sources).

import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const RACINE = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const DOSSIER = process.env.CAPTURES_DOSSIER || path.join(RACINE, "captures");
const THEMES = ["soir", "jour", "creme", "contraste"];

function lireOptions() {
  const options = { largeurs: [1280, 900, 640, 380], navigateur: process.env.CHROMIUM_PATH || null };
  const restes = process.argv.slice(2);
  while (restes.length) {
    const drapeau = restes.shift();
    if (drapeau === "--largeur") options.largeurs = [Number(restes.shift())];
    else if (drapeau === "--navigateur") options.navigateur = restes.shift();
    else if (drapeau === "--url") options.url = restes.shift();
  }
  return options;
}

const options = lireOptions();
const adresse = options.url || process.env.CAPTURES_URL || "http://127.0.0.1:8124/";

let puppeteer;
try {
  ({ default: puppeteer } = await import("puppeteer"));
} catch {
  ({ default: puppeteer } = await import("puppeteer-core"));
}

await mkdir(DOSSIER, { recursive: true });
const navigateur = await puppeteer.launch({
  headless: "shell",
  args: ["--no-sandbox", "--disable-dev-shm-usage"],
  ...(options.navigateur ? { executablePath: options.navigateur } : {}),
});

const rapport = [];

/** Les réglages du visiteur sont posés avant le premier pixel, comme un clic. */
async function regler(page, reglages) {
  await page.evaluateOnNewDocument((valeurs) => {
    try {
      for (const [cle, valeur] of Object.entries(valeurs)) {
        if (valeur) localStorage.setItem("simulateur-" + cle, String(valeur));
      }
    } catch { /* un navigateur sans mémoire : la page prendra ses défauts */ }
  }, reglages);
}

async function photographier(nom, { theme, largeur, preparation }) {
  const page = await navigateur.newPage();
  await page.setViewport({ width: largeur, height: largeur <= 640 ? 780 : 900, deviceScaleFactor: 1 });
  await regler(page, { theme, densite: "aere", presentation: "equilibree" });
  await page.goto(adresse, { waitUntil: "networkidle2", timeout: 90000 });
  await page.waitForFunction(() => typeof window.simuler === "function", { timeout: 60000 });
  /* Le guide de première visite s'ouvre par-dessus la page (c'est sa raison
     d'être). La mesure des cadres, elle, porte sur la page : on le referme — et
     une vue lui est consacrée, pour qu'il soit vu lui aussi. */
  const guide = await page.$("#overlay.visible, #overlay.ouvert");
  if (guide) {
    await page.evaluate(() => {
      if (typeof window.fermerModale === "function") window.fermerModale();
      else document.getElementById("overlay")?.classList.remove("visible", "ouvert");
    });
    await new Promise((r) => setTimeout(r, 250));
  }
  if (preparation) await preparation(page);
  await new Promise((r) => setTimeout(r, 400));
  await page.screenshot({ path: path.join(DOSSIER, `${nom}.png`) });
  const mesures = await page.evaluate(() => {
    /* Ce qu'un doigt toucherait : au centre de chaque commande, qui est le
       dessus ? Un panneau, une bulle, un bandeau collant posé par-dessus — et
       la commande devient inaccessible sans que rien ne le dise. C'est la
       question du visiteur, posée en une ligne : « la bulle occulte l'accès aux
       boutons ». */
    const recouverts = [];
    const commandes = document.querySelectorAll(
      ".entete button, .entete summary, .sommaire a, .ruban-veille button, "
      + ".resume-actions a, .resume-actions button, .affichage-panneau button, "
      + ".outils-panneau button, .classes-filtres button");
    for (const commande of commandes) {
      const r = commande.getBoundingClientRect();
      if (!r.width || !r.height || r.bottom < 0 || r.top > window.innerHeight) continue;
      const dessus = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
      if (dessus && dessus !== commande && !commande.contains(dessus)) {
        recouverts.push({
          texte: (commande.textContent || "").trim().slice(0, 30).replace(/\s+/g, " "),
          par: dessus.id || dessus.className || dessus.tagName,
        });
      }
    }
    const boite = (selecteur) => {
      const element = document.querySelector(selecteur);
      if (!element) return null;
      const r = element.getBoundingClientRect();
      const style = getComputedStyle(element);
      return {
        selecteur,
        haut: Math.round(r.top + window.scrollY),
        largeur: Math.round(r.width),
        hauteur: Math.round(r.height),
        tour: style.padding,
        marge: style.margin,
        enfants: element.childElementCount,
        range: style.flexWrap || style.gridTemplateColumns || "",
        deborde_largeur: element.scrollWidth > element.clientWidth + 1,
      };
    };
    return {
      hauteur_page: document.documentElement.scrollHeight,
      debordement_horizontal: document.documentElement.scrollWidth > window.innerWidth + 1,
      recouverts,
      boites: [".entete", ".entete .barre-contexte", ".entete .barre-contexte button",
        ".entete .etat-contexte", ".sommaire", ".sommaire-liste", ".ruban-veille",
        ".ruban-veille .ruban-actions", "#resume .resume-actions", ".affichage-panneau",
        ".outils-panneau", ".conteneur"].map(boite).filter(Boolean),
    };
  });
  rapport.push({ nom, theme, largeur, ...mesures });
  await page.close();
  console.log("  ·", nom, `${largeur} px — page de ${mesures.hauteur_page} px`,
    mesures.debordement_horizontal ? "⚠ DÉBORDEMENT HORIZONTAL" : "",
    mesures.recouverts.length
      ? `⚠ ${mesures.recouverts.length} commande(s) recouverte(s) : `
        + mesures.recouverts.map((r) => `« ${r.texte} » sous ${r.par}`).join(", ")
      : `· ${mesures.boites.length} cadres mesurés, aucune commande recouverte`);
}

// 1. Le premier écran : quatre thèmes, quatre largeurs.
for (const largeur of options.largeurs) {
  for (const theme of THEMES) {
    if (largeur <= 380 && theme !== "soir" && theme !== "jour") continue;
    await photographier(`accueil-${theme}-${largeur}`, { theme, largeur });
  }
}

// 2. Les panneaux ouverts : c'est là que le visiteur règle l'affichage.
for (const largeur of [1280, 380]) {
  await photographier(`panneau-affichage-jour-${largeur}`, {
    theme: "jour", largeur,
    preparation: (page) => page.click(".affichage > summary"),
  });
  await photographier(`panneau-outils-jour-${largeur}`, {
    theme: "jour", largeur,
    preparation: (page) => page.click(".outils > summary"),
  });
}

// 3. Le guide de première visite, tel qu'un visiteur le reçoit.
await photographier("guide-premiere-visite-jour-1280", {
  theme: "jour", largeur: 1280,
  preparation: (page) => page.evaluate(() => {
    if (typeof window.ouvrirGuide === "function") window.ouvrirGuide();
  }),
});

// 4. Les états : survol, focus, densité resserrée.
await photographier("etat-survol-jour-1280", {
  theme: "jour", largeur: 1280,
  preparation: async (page) => {
    await page.hover("#btn-simuler");
  },
});
await photographier("etat-compact-jour-1280", {
  theme: "jour", largeur: 1280,
  preparation: (page) => page.evaluate(() => window.basculerDensite(true)),
});

// 4. Une descente dans la page : les temps forts.
for (const cible of ["resume", "section-classes", "console-pilotage"]) {
  await photographier(`section-${cible}-jour-1280`, {
    theme: "jour", largeur: 1280,
    preparation: (page) => page.evaluate((id) => {
      document.getElementById(id)?.scrollIntoView({ block: "start" });
    }, cible),
  });
}

await writeFile(path.join(DOSSIER, "rapport.json"), JSON.stringify(rapport, null, 1), "utf8");

/* Le résumé : la même mesure, en texte, pour être lu sans ouvrir une image —
   dans le journal de l'intégration continue, dans le rapport du travail, et
   dans le commentaire de la demande de fusion. */
const recouverts = rapport.filter((vue) => vue.recouverts.length);
const debordent = rapport.filter((vue) => vue.debordement_horizontal);
const lignes = [];
lignes.push(`Captures : ${rapport.length} vues, ${options.largeurs.join(" / ")} px, quatre thèmes.`);
lignes.push("");
const boite = (vue, selecteur) => vue.boites.find((b) => b.selecteur === selecteur);
const nombre = (valeur) => (valeur === undefined ? "—" : String(valeur));
// Une hauteur ne dit pas tout : sous 640 px, le sommaire fait 58 px parce qu'il
// est replié sur son bouton, et la barre du bandeau 76 px parce que ses quatre
// commandes tiennent en deux rangées. Les deux colonnes qui suivent le disent.
lignes.push("| Vue | Largeur | Page | Bandeau | Barre (rangées) | Sommaire (enfants) | Ruban |");
lignes.push("|---|---:|---:|---:|---:|---:|---:|");
for (const vue of rapport) {
  const barre = boite(vue, ".entete .barre-contexte");
  const sommaire = boite(vue, ".sommaire");
  const rangées = barre ? Math.max(1, Math.round(barre.hauteur / 34)) : 0;
  lignes.push(`| ${vue.nom} | ${vue.largeur} | ${vue.hauteur_page} | `
    + `${nombre(boite(vue, ".entete")?.hauteur)} | ${nombre(barre?.hauteur)} (${rangées}) | `
    + `${nombre(sommaire?.hauteur)} (${nombre(sommaire?.enfants)}) | `
    + `${nombre(boite(vue, ".ruban-veille")?.hauteur)} |`);
}
const glisse = rapport.filter((vue) => vue.boites.some((b) => b.deborde_largeur));
lignes.push("");
lignes.push(glisse.length
  ? `**Cadres qui défilent latéralement** : ${glisse.map((vue) => vue.nom + " ("
      + vue.boites.filter((b) => b.deborde_largeur).map((b) => b.selecteur).join(", ") + ")").join(" ; ")}`
  : "**Aucun cadre ne défile latéralement** : tout tient dans la largeur.");
lignes.push("");
lignes.push(recouverts.length
  ? `**Commandes recouvertes** : ${recouverts.map((vue) => `${vue.nom} (${vue.recouverts.length})`).join(", ")}`
  : "**Aucune commande recouverte** dans les " + rapport.length + " vues.");
if (recouverts.length) {
  for (const vue of recouverts) {
    for (const dessus of vue.recouverts) lignes.push(`- ${vue.nom} : « ${dessus.texte} » sous ${dessus.par}`);
  }
}
lignes.push(debordent.length
  ? `**Débordement horizontal** : ${debordent.map((vue) => vue.nom).join(", ")}`
  : "**Aucun débordement horizontal** : la page ne glisse pas latéralement.");
const resume = lignes.join("\n");
await writeFile(path.join(DOSSIER, "resume.md"), resume, "utf8");
console.log(resume);
await navigateur.close();
console.log(`${rapport.length} captures écrites dans ${DOSSIER}`);
