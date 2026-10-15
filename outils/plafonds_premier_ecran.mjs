// outils/plafonds_premier_ecran.mjs — ce qu'un téléphone voit avant le contenu.
//
// **Le problème, mesuré le 15 octobre 2026 dans Chromium, à 380 px** : le
// bandeau faisait 566 px, le sommaire 58, le ruban de veille 239 — soit
// **863 px** de cadre avant la première ligne de contenu, sur un écran de 780.
// Le visiteur ouvrait la page et ne voyait que la page se présenter. À 640 px,
// le même compte donnait 350 + 58 + 206 = **614 px**.
//
// Un cadre n'est pas condamnable en soi : c'est sa **part de l'écran** qui
// décide si le contenu existe pour le lecteur. D'où ce fichier : les plafonds
// du premier écran, par largeur, avec les mesures datées dont chacun vient — et
// une fonction pure qui dit lesquels sont dépassés.
//
// Quatre règles :
//
// 1. **Un plafond porte ses mesures datées** (`avant`, `mesure`, `quand`,
//    `quoi`) : sans elles, un plafond est un chiffre choisi, pas une mesure
//    tenue ;
// 2. **il bat l'état ancien** (`plafond < avant`) : un plafond qui autorise le
//    statu quo ne plafonne rien ;
// 3. **il tient l'état mesuré** (`plafond >= mesure`), avec une petite marge —
//    un plafond qu'on dépasse d'un pixel à chaque passage ne dit plus rien. Un
//    plafond marqué `cible` dit l'inverse : il demande un gain qui n'est pas
//    encore mesuré, et l'entrée est complétée dès la mesure suivante ;
// 4. **seul le téléphone est plafonné.** Au large, le premier écran fait 394 px
//    sur 900 : il y a la place. Un plafond qui ne se déclenche jamais est du
//    bruit — et un contrôle qu'on ne lit plus ne contrôle plus rien.
//
// Le plafond est un **cliquet** : il ne remonte pas. La passe du 15 octobre 2026
// l'a posé à 700 px (380) et 540 px (640) après avoir mesuré 685 et 524 ; la
// suite se juge sur la direction — un écran de téléphone fait 780 px de haut,
// et le contenu doit y commencer.

/** La hauteur du premier écran : ce qu'un visiteur voit avant le contenu. */
export const PLAFONDS = {
  380: {
    plafond: 700,
    avant: 863,
    mesure: 685,
    quand: "15 octobre 2026",
    quoi: "bandeau 475 + sommaire 58 + ruban 152 (avant la passe : 566 + 58 + 239)",
  },
  640: {
    //: **Une cible** : le palier 640 vient de recevoir les règles du premier
    //: écran, et le plafond demande le gain avant de le constater. La mesure
    //: d'après remplace `cible` par le chiffre atteint — un plafond tenu ne se
    //: devine pas, il se mesure.
    plafond: 540,
    avant: 614,
    mesure: 614,
    cible: true,
    quand: "15 octobre 2026",
    quoi: "cible de 540 px ; 614 px mesurés avant la passe (350 + 58 + 206)",
  },
};

/** La mesure d'un premier écran, en px — `null` si la vue ne la porte pas. */
export function hauteur(vue) {
  return typeof vue?.premier_ecran?.total === "number" ? vue.premier_ecran.total : null;
}

/**
 * Les vues qui dépassent leur plafond, avec de quoi le corriger sans chercher.
 *
 * Une vue sans plafond pour sa largeur n'est jamais signalée : c'est la règle 4.
 * Une vue qui ne porte pas de mesure est signalée à part — on ne peut pas
 * tenir un plafond sur ce qu'on ne mesure pas.
 */
export function depassements(vues, plafonds = PLAFONDS) {
  const sortie = [];
  for (const vue of vues || []) {
    const limite = plafonds[vue?.largeur];
    if (!limite) continue;
    const mesure = hauteur(vue);
    if (mesure === null) {
      sortie.push({ nom: vue?.nom ?? "(vue sans nom)", largeur: vue.largeur, mesure: null,
        plafond: limite.plafond, exces: null,
        phrase: "la vue ne porte pas de mesure de premier écran" });
      continue;
    }
    if (mesure > limite.plafond) {
      const parties = vue.premier_ecran;
      sortie.push({
        nom: vue.nom, largeur: vue.largeur, mesure, plafond: limite.plafond,
        exces: mesure - limite.plafond,
        phrase: `${vue.nom} : premier écran de ${mesure} px pour un plafond de `
          + `${limite.plafond} px (${mesure - limite.plafond} px de trop) — `
          + `bandeau ${parties.bandeau}, sommaire ${parties.sommaire}, ruban ${parties.ruban}`,
      });
    }
  }
  return sortie;
}

/** Ce qu'on écrit, dans le résumé comme dans le journal : tenu, ou dépassé. */
export function lignes(vues, plafonds = PLAFONDS) {
  const sortie = [];
  const fait = depassements(vues, plafonds);
  const largeurs = Object.keys(plafonds).map(Number).sort((a, b) => a - b);
  for (const largeur of largeurs) {
    const limite = plafonds[largeur];
    const vuesIci = (vues || []).filter((vue) => vue.largeur === largeur);
    const mesures = vuesIci.map(hauteur).filter((valeur) => valeur !== null);
    if (!mesures.length) continue;
    const pire = Math.max(...mesures);
    sortie.push(`**Premier écran à ${largeur} px** : ${pire} px mesurés (${vuesIci.length} vue(s)) `
      + `pour un plafond de ${limite.plafond} px — `
      + (pire > limite.plafond ? "**DÉPASSÉ**"
        : (limite.cible ? "tenu, **cible atteinte**" : "tenu"))
      + ` ; ancré sur ${limite.avant} px le ${limite.quand} (${limite.quoi}).`);
  }
  for (const depassement of fait) sortie.push(`- ⛔ ${depassement.phrase}`);
  return sortie;
}
