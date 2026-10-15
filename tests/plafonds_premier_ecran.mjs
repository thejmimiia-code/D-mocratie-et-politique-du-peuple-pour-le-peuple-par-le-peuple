/**
 * tests/plafonds_premier_ecran.mjs — joue les plafonds du premier écran sur des vues.
 *
 * Usage : node tests/plafonds_premier_ecran.mjs <vues.json> [plafonds.json]
 *
 * La charge est une liste de vues, telles que `outils/captures_ecran.mjs` les
 * écrit dans `captures/rapport.json`. Le rapport, en JSON sur la sortie
 * standard, dit ce que la fonction pure répond — et l'état de sortie vaut 1
 * dès qu'un plafond est dépassé, comme dans la veille et les budgets.
 *
 * Il existe pour que les plafonds soient **éprouvables sans navigateur** : la
 * photographie demande Chromium, le verdict n'en demande pas.
 */
import { readFileSync } from "node:fs";
import { depassements, lignes, PLAFONDS } from "../outils/plafonds_premier_ecran.mjs";

const [, , cheminVues, cheminPlafonds] = process.argv;
if (!cheminVues) {
  console.error("usage: node tests/plafonds_premier_ecran.mjs <vues.json> [plafonds.json]");
  process.exit(2);
}

const vues = JSON.parse(readFileSync(cheminVues, "utf8"));
const plafonds = cheminPlafonds ? JSON.parse(readFileSync(cheminPlafonds, "utf8")) : PLAFONDS;
const fait = depassements(vues, plafonds);
console.log(JSON.stringify({ depassements: fait, lignes: lignes(vues, plafonds) }, null, 1));
process.exit(fait.length ? 1 : 0);
