// outils/plafonds_premier_ecran.mjs — ce qu'un téléphone voit avant le contenu.
//
// **Le problème, mesuré le 15 octobre 2026 dans Chromium, à 380 px** : le
// bandeau faisait 566 px, le sommaire 58, le ruban de veille 239 — soit
// **863 px** de cadre avant la première ligne de contenu, sur un écran de
// 780. Le visiteur ouvrait la page et ne voyait que la page se présenter. À
// 640 px, le même compte donnait 350 + 58 + 206 = **614 px**.
//
// Un cadre n'est pas condamnable en soi : c'est sa **part de l'écran** qui
// décide si le contenu existe pour le lecteur. D'où ce fichier : les plafonds
// du premier écran, par largeur, avec la mesure datée dont chacun vient — et
// une fonction pure qui dit lesquels sont dépassés.
//
// Trois règles, les mêmes que celles des budgets de fluidité :
//
// 1. **Un plafond porte sa mesure datée** (`mesure`, `quand`, `quoi`) : sans
//    elle, un plafond est un chiffre choisi, pas une mesure tenue ;
// 2. **Aucun plafond n'est au-dessus de sa mesure** : un plafond qui autorise
//    le statu quo ne plafonne rien. Il doit forcer le progrès, pas le décrire ;
// 3. **Seul le téléphone est plafonné.** Au large, le premier écran fait 394 px
//    sur 900 : il y a la place. Un plafond qui ne se déclenche jamais est du
//    bruit — et un contrôle qu'on ne lit plus ne contrôle plus rien.

/** La hauteur du premier écran : ce qu'un visiteur voit avant le contenu. */
export const PLAFONDS = {
  380: {
    plafond: 620,
    mesure: 863,
    quand: "15 octobre 2026",
    quoi: "bandeau 566 + sommaire 58 + ruban 239",
  },
  640: {
    plafond: 480,
    mesure: 614,
    quand: "15 octobre 2026",
    quoi: "bandeau 350 + sommaire 58 + ruban 206",
  },
};

/** La mesure d'un premier écran, en px — `null` si la vue ne la porte pas. */
export function hauteur(vue) {
  return typeof vue?.premier_ecran?.total === "number" ? vue.premier_ecran.total : null;
}

/**
 * Les vues qui dépassent leur plafond, avec de quoi le corriger sans chercher.
 *
 * Une vue sans plafond pour sa largeur n'est jamais signalée : c'est la règle 3.
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
      + (pire > limite.plafond ? "**DÉPASSÉ**" : "tenu")
      + ` ; ancré sur ${limite.mesure} px le ${limite.quand} (${limite.quoi}).`);
  }
  for (const depassement of fait) sortie.push(`- ⛔ ${depassement.phrase}`);
  return sortie;
}
