"""
simulateur/interface.py — Interface web du simulateur interactif.

Le module expose `HTML_PAGE` : une page unique (aucune dépendance externe,
aucun CDN) qui contient :

  * la barre de contexte « instant T » (données réelles, provenance, licences) ;
  * la **console de veille permanente** (`console-pilotage`) : verdict par strate,
    messages de seuil (tolérable → vigilance → risqué → hors-sol), risque pour la
    population, marges de manœuvre restantes et effet de la dernière modification ;
  * la cascade des 5 échelons systémiques, recalculée à chaque simulation ;
  * la grille des scénarios types du dépôt, rejoués année par année ;
  * les préréglages doctrinaux additionnels ;
  * le catalogue de leviers de politique publique réglables (curseurs, interrupteurs), chacun
    annoté d'une **aide au survol** (plage, défaut, valeur courante, effets
    déclarés, mesures en direct) et d'une **bulle explicative** dépliable ;
  * des infobulles instantanées sur les boutons, cases à cocher, cartes de
    domaine, préréglages et scénarios (couche passive : aucun clic capté) ;
  * les **nuances institutionnelles** : seuils recalculés, délais de rigueur, fentes,
    indices, cinq strates, garde-fous de la couche — et l'état des 38 verrous du
    registre, partagé en touchés / intacts / hors réglage, chaque citation de la
    Constitution pointant sur la fiche servie par `/api/constitution` ;
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
  /* Accents M.R.S.C (charte du site : navy #1d3268, bleu #2958a2, vert #456d29,
     or #e7a126, rouge #e55058). Sur fond sombre, on reprend les variantes
     éclaircies déjà appliquées par le site à la page intégrée du simulateur :
     le contraste requis par l'interface sombre est conservé, l'identité aussi. */
  --mrsc-navy:#1d3268; --mrsc-bleu:#2958a2; --mrsc-vert:#456d29;
  --mrsc-or:#e7a126; --mrsc-rouge:#e55058;
  --mrsc-bleu-clair:#91b2e6; --mrsc-vert-clair:#9bc77a;
  --mrsc-rouge-clair:#ff9295; --mrsc-or-clair:#f2c15f;
  /* Une couleur ne porte jamais seule une information : chaque classe a aussi
     un symbole, un libellé écrit et un motif de fond (voir .motif-*). */
  --classe-recettes:#9bc77a; --classe-economies:#9bc77a;
  --classe-depenses:#ff9295; --classe-regles:#91b2e6; --classe-monde:#f2c15f;
  /* Teintes de fond des deux plateaux : déclarées ici, une seule fois, et
     recalculées à l'usage par `color-mix` sur la variable de classe — pour que
     la page suive la palette en vigueur (celle du site quand elle est
     intégrée), sans qu'aucune teinte reste accrochée à l'ancienne. */
  --classe-recettes-fond:rgba(155,199,122,.12);
  --classe-depenses-fond:rgba(255,146,149,.12);
  /* ── Socle de lisibilité ──────────────────────────────────────────────────
     --t-min est le plancher de lecture : aucun texte de la page ne descend
     sous cette taille, quelle que soit la taille de référence. Il s'applique
     par `max(var(--t-min), …)` sur les tailles secondaires, pour que les
     réglages d'agrandissement du texte (125 %, 150 %) continuent de
     fonctionner au-dessus du plancher. */
  --t-min:12.5px;
  /* Palette : une couleur se déclare ici, jamais dans une règle. */
  --panel-3:var(--panel-3);
  /* Hauteur de la barre haute collante : les ancres s'en décalent d'autant. */
  --collant:0px;
  /* ── Plans d'empilement ───────────────────────────────────────────────────
     Une seule échelle, déclarée ici et nulle part ailleurs : ce qui doit passer
     devant le fait par son nom. Les sept nombres qui traînaient dans sept
     règles (56, 60, 80, 120, 200) sont désormais rangés du fond vers le
     premier plan, et le bandeau d'impression a sa place réservée. */
  --z-fond:0; --z-contenu:1; --z-sommaire:56; --z-ruban:60;
  --z-evitement:80; --z-infobulle:120; --z-bandeau:160; --z-modale:200;
}
:focus-visible{outline:3px solid var(--mrsc-or);outline-offset:2px}

*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',Roboto,system-ui,sans-serif;background:
  radial-gradient(1200px 600px at 50% -10%,#16233d 0%,var(--bg) 60%);
  color:var(--texte);min-height:100vh;padding:18px;line-height:1.45}
/* Encoches et coins arrondis : en portrait, la marge de 18 px tombe sous la
   barre d'état ; en paysage, sous l'encoche latérale. Les deux déclarations
   cohabitent — un navigateur qui ne connaît pas `env()` garde la première, la
   valeur de repli assure qu'aucune marge ne disparaît. */
body{padding:max(18px,env(safe-area-inset-top,0px)) max(18px,env(safe-area-inset-right,0px))
  max(18px,env(safe-area-inset-bottom,0px)) max(18px,env(safe-area-inset-left,0px))}
/* Titres en drapeau : un titre ne se casse plus sur un mot orphelin. */
h1,h2,h3{text-wrap:balance}
p{text-wrap:pretty}
.conteneur{max-width:1560px;margin:0 auto}
a{color:var(--accent)}
header.entete{background:linear-gradient(135deg,var(--mrsc-navy),#26375f);border:1px solid var(--border);
  border-color:#344b79;border-radius:14px;padding:18px 22px;margin-bottom:14px;box-shadow:0 10px 30px rgba(0,0,0,.35)}
header.entete h1{font-size:1.45rem;letter-spacing:.2px}
header.entete p{color:var(--texte-dim);font-size:.88rem;margin-top:4px}
.barre-contexte{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:12px}
.barre-contexte .separateur{width:1px;height:22px;background:var(--border);margin:0 2px}
.select-horizon{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--border);
  border-radius:999px;padding:4px 10px;background:var(--panel);color:var(--texte-dim);font-size:.78rem}
.select-horizon select{font:inherit;color:var(--texte);background:var(--panel-2);border:1px solid var(--border);
  border-radius:7px;padding:4px 7px}
.pastille{border-radius:999px;padding:4px 12px;font-size:.75rem;border:1px solid var(--border);
  background:var(--panel);color:var(--texte-dim);white-space:nowrap}
.pastille.live{border-color:var(--vert);color:#bbf7d0;background:rgba(34,197,94,.12)}
.pastille.reference{border-color:var(--ambre);color:#fde68a;background:rgba(245,158,11,.12)}
.pastille.mixte{border-color:var(--accent);color:#bae6fd;background:rgba(56,189,248,.12)}
button{font-family:inherit;font-size:.82rem;cursor:pointer;border-radius:9px;border:1px solid var(--border);
  background:var(--panel-2);color:var(--texte);padding:8px 13px;transition:.15s}
button:hover:not(:disabled){border-color:var(--accent);transform:translateY(-1px)}
button:disabled{opacity:.45;cursor:not-allowed}
button.primaire{background:linear-gradient(135deg,var(--mrsc-navy),var(--mrsc-bleu));border-color:var(--mrsc-bleu)}
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
.metric .libelle{font-size:max(var(--t-min),.74rem);color:var(--texte-dim);text-transform:uppercase;letter-spacing:.4px}
.metric .delta{font-size:.75rem;margin-top:2px}
.delta.hausse{color:var(--vert)} .delta.baisse{color:var(--rouge)} .delta.neutre{color:var(--texte-dim)}
.scenario-card{cursor:pointer;border-left:4px solid var(--accent);transition:.15s}
.scenario-card:hover{background:var(--panel-3);transform:translateY(-2px)}
.scenario-card.actif{box-shadow:0 0 0 2px var(--accent) inset;background:var(--panel-3)}
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

/* ══ Classes de leviers : ce qui entre (vert), ce qui sort (rouge) ══════════
   Cinq classes, un seul vocabulaire visuel : une couleur M.R.S.C, un symbole,
   un libellé écrit et un motif de fond. Le motif et le symbole suffisent quand
   la couleur disparaît (daltonisme, impression noir et blanc, contraste
   renforcé, couleurs forcées). Aucune information n'est portée par la teinte
   seule. */
.motif-uni{background-image:none}
.motif-hachure,[data-motif="hachure"]{background-image:repeating-linear-gradient(45deg,
  var(--teinte-motif,rgba(155,199,122,.18)) 0 5px,transparent 5px 11px)}
.motif-pointille,[data-motif="pointille"]{background-image:radial-gradient(var(--teinte-motif,rgba(145,178,230,.34)) 1px,transparent 1.6px);
  background-size:9px 9px}
.classe-pastille{display:inline-flex;align-items:center;gap:5px;border:1px solid var(--couleur-classe,var(--border));
  border-radius:999px;padding:1px 8px;font-size:max(var(--t-min),.66rem);line-height:1.7;color:var(--couleur-classe,var(--texte));
  background:var(--fond-classe,transparent);white-space:nowrap}
.classe-pastille .symbole{font-weight:800;font-size:max(var(--t-min),.72rem);font-variant-numeric:tabular-nums}
.classe-carte{border:1px solid var(--border);border-left:5px solid var(--couleur-classe);
  border-radius:12px;padding:12px 13px;background:var(--fond-classe);position:relative;overflow:hidden}
.classe-carte h3{font-size:.9rem;margin:0 0 2px;display:flex;align-items:center;gap:7px}
.classe-carte .question{font-size:.76rem;color:var(--texte);font-weight:600;margin:6px 0 4px}
.classe-carte .definition{font-size:max(var(--t-min),.72rem);color:var(--texte-dim);line-height:1.5}
.classe-carte .chiffres{display:flex;flex-wrap:wrap;gap:10px 16px;margin-top:9px;align-items:baseline}
.classe-carte .chiffre{font-size:1.05rem;font-weight:700;color:var(--couleur-classe);font-variant-numeric:tabular-nums}
.classe-carte .chiffre small{display:block;font-size:max(var(--t-min),.64rem);font-weight:400;color:var(--texte-dim)}
.classe-carte .pied{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:10px;
  border-top:1px dashed var(--border);padding-top:8px;font-size:max(var(--t-min),.68rem);color:var(--texte-dim)}
.classe-carte .pied .bouton{font-size:max(var(--t-min),.68rem);padding:4px 9px}
.classe-carte .motif-legende{position:absolute;inset:0;opacity:.5;pointer-events:none;z-index:var(--z-fond)}
.classe-carte > *{position:relative;z-index:var(--z-contenu)}
.balance{margin:12px 0 16px;border:1px solid var(--border);border-radius:12px;background:var(--panel-2);padding:12px 14px}
.balance-titre{display:flex;flex-wrap:wrap;gap:10px;align-items:baseline;justify-content:space-between}
.balance-titre b{font-size:.86rem}
.balance-titre .verdict{font-size:.8rem;font-weight:700}
.balance-plateau{display:grid;grid-template-columns:1fr auto 1fr;align-items:end;gap:10px;margin-top:12px}
.balance-cote{border:1px solid var(--border);border-radius:10px;padding:9px 11px;min-height:96px;
  display:flex;flex-direction:column;justify-content:flex-end;gap:3px}
/* Les deux plateaux se teintent de **leur** variable de classe : quand la page
   est intégrée au site, sa palette (CSS_RETOUR de `outils/construire-simulateur.py`)
   reprend la main. La première ligne est le repli des navigateurs sans
   `color-mix` ; la seconde recalcule la teinte sur la variable de classe. */
.balance-cote.entrees{border-color:var(--classe-recettes);background:var(--classe-recettes-fond);
  background:color-mix(in srgb,var(--classe-recettes) 14%,transparent)}
.balance-cote.sorties{border-color:var(--classe-depenses);background:var(--classe-depenses-fond);
  background:color-mix(in srgb,var(--classe-depenses) 14%,transparent)}
.balance-cote .etiquette{font-size:max(var(--t-min),.68rem);text-transform:uppercase;letter-spacing:.5px;color:var(--texte-dim)}
.balance-cote .montant{font-size:1.3rem;font-weight:700;font-variant-numeric:tabular-nums}
.balance-cote .menage{font-size:max(var(--t-min),.7rem);color:var(--texte-dim)}
.balance-cote .jauge-classe{height:9px;border-radius:6px;background:rgba(255,255,255,.08);overflow:hidden;
  border:1px solid var(--border);margin-top:6px}
.balance-cote .jauge-classe span{display:block;height:100%}
.balance-cote.entrees .jauge-classe span{background:var(--classe-recettes)}
.balance-cote.sorties .jauge-classe span{background:var(--classe-depenses)}
.balance-axe{display:flex;flex-direction:column;align-items:center;gap:4px;min-width:74px}
.balance-axe .fleche{font-size:1.5rem;color:var(--texte-dim);line-height:1}
.balance-axe .net{font-size:.8rem;font-weight:700;text-align:center;font-variant-numeric:tabular-nums}
.balance-axe .net.gain{color:var(--classe-recettes)}
.balance-axe .net.cout{color:var(--classe-depenses)}
.balance-axe .net.neutre{color:var(--texte-dim)}
.balance-detail{margin-top:10px;font-size:max(var(--t-min),.7rem);color:var(--texte-dim);line-height:1.5}
/* Le rythme : la même lecture, année par année. On avance d'un an et tout le
   bloc se relit — balance, cascade, cartes — sans relancer la simulation. */
.annee-classes{display:inline-flex;align-items:center;gap:7px}
.annee-classes button{font-size:max(var(--t-min),.68rem);padding:3px 8px}
.annee-classes .annee-courante{font-size:max(var(--t-min),.74rem);font-weight:700;min-width:86px;text-align:center;
  font-variant-numeric:tabular-nums}
.annee-classes button:disabled{opacity:.45;cursor:not-allowed}
.classe-rythme{margin-top:8px;font-size:max(var(--t-min),.7rem);color:var(--texte-dim);line-height:1.5}
.classe-rythme b{color:var(--texte)}
/* ══ La cascade du plan : l'ordre dans lequel le budget se construit ═══════
   Un seul axe pour toutes les marches : chaque classe part du cumul laissé par
   la précédente et le déplace de son montant — l'escalier se referme sur le
   solde. Les classes « règles » et « monde » n'y entrent pas : leurs unités ne
   sont pas des euros. */
.cascade{margin-top:12px;border-top:1px dashed var(--border);padding-top:10px}
.cascade-titre{display:flex;flex-wrap:wrap;gap:3px 12px;align-items:baseline;justify-content:space-between}
.cascade-titre b{font-size:.8rem}
.cascade-titre .legende{font-size:max(var(--t-min),.66rem);color:var(--texte-dim);font-style:italic}
.cascade-marches{list-style:none;margin:9px 0 0;padding:0;display:flex;flex-direction:column;gap:8px}
.cascade-marche{border-left:3px solid var(--couleur-classe,var(--border));padding-left:8px}
.cascade-ligne{display:grid;grid-template-columns:minmax(150px,1.15fr) minmax(96px,2.6fr) auto;
  gap:9px;align-items:center}
.cascade-nom{display:flex;flex-direction:column;gap:1px;font-size:.75rem;font-weight:600;line-height:1.25}
.cascade-nom .tete{display:flex;gap:5px;align-items:baseline}
.cascade-nom .symbole{color:var(--couleur-classe);font-weight:800;font-variant-numeric:tabular-nums}
.cascade-nom small{font-weight:400;font-size:max(var(--t-min),.64rem);color:var(--texte-dim)}
.cascade-piste{position:relative;height:17px;border:1px solid var(--border);border-radius:5px;
  background:rgba(255,255,255,.045);overflow:hidden}
.cascade-piste i{position:absolute;display:block;border-radius:4px}
.cascade-piste .zero{top:-2px;bottom:-2px;width:1px;background:var(--texte-dim);opacity:.45;border-radius:0}
.cascade-piste .barre{top:1px;bottom:1px;background-color:var(--couleur-classe)}
.cascade-piste .barre.hachure{background-image:repeating-linear-gradient(45deg,
  var(--teinte-motif,rgba(255,255,255,.35)) 0 4px,transparent 4px 9px)}
.cascade-piste .barre.pointille{background-image:radial-gradient(var(--teinte-motif,rgba(255,255,255,.35)) 1px,transparent 1.5px);
  background-size:8px 8px}
.cascade-montant{display:flex;flex-direction:column;align-items:flex-end;text-align:right;
  font-size:.8rem;font-weight:700;font-variant-numeric:tabular-nums;color:var(--couleur-classe,var(--texte));white-space:nowrap}
.cascade-montant small{font-weight:400;font-size:max(var(--t-min),.63rem);color:var(--texte-dim)}
.cascade-detail{margin-top:3px;font-size:max(var(--t-min),.64rem);color:var(--texte-dim);line-height:1.6;
  display:flex;flex-wrap:wrap;gap:4px 6px;align-items:baseline}
.cascade-detail .puce-unite{cursor:default}
.cascade-detail .reste{font-style:italic}
.cascade-total{margin-top:2px;border-top:1px solid var(--border);border-left-color:var(--texte-dim);padding-top:8px}
.cascade-note{margin-top:8px;font-size:max(var(--t-min),.68rem);color:var(--texte-dim);line-height:1.5}
.classes-legende{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 4px}
.classes-legende button{cursor:pointer}
.rampe{display:inline-flex;align-items:flex-end;gap:2px;height:22px;vertical-align:middle}
.rampe i{display:block;width:5px;background:var(--couleur-classe,var(--texte-dim));border-radius:1px;opacity:.85}
.rampe.vide i{background:var(--border)}
.rampe-legende{font-size:max(var(--t-min),.64rem);color:var(--texte-dim);margin-left:6px}
.fiche-menage{margin-top:5px;padding:5px 8px;border:1px dashed var(--border);border-radius:8px;
  font-size:max(var(--t-min),.68rem);color:var(--texte-dim);display:flex;flex-wrap:wrap;gap:4px 10px;align-items:baseline}
.fiche-menage b{color:var(--texte);font-variant-numeric:tabular-nums}
.fiche-menage .statut{border:1px solid var(--ambre);border-radius:999px;padding:0 6px;color:var(--ambre);font-size:max(var(--t-min),.62rem)}
.famille.classee{border-left:5px solid var(--couleur-classe);background-color:var(--fond-classe)}
.famille .tete-famille{display:flex;flex-wrap:wrap;gap:6px;align-items:center;justify-content:space-between;
  border-bottom:1px solid var(--border);padding-bottom:6px;margin-bottom:8px}
.famille .tete-famille h3{border:none;padding:0;margin:0}
.levier[data-classe]{border-left:4px solid var(--couleur-classe);background-color:var(--fond-classe);
  border-radius:0 9px 9px 0;padding-left:9px}
.chips-unites{display:flex;flex-wrap:wrap;gap:5px;margin-top:6px}
.puce-unite{border:1px solid var(--border);border-radius:999px;padding:1px 8px;font-size:max(var(--t-min),.64rem);
  color:var(--texte-dim);background:var(--panel-2);white-space:nowrap;cursor:help}
.puce-unite b{color:var(--couleur-classe,var(--texte));font-variant-numeric:tabular-nums}
.levier .classe-ligne{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:5px}
.levier .classe-motif{font-size:max(var(--t-min),.64rem);color:var(--texte-dim);font-style:italic;line-height:1.45}
.levier .classe-motif.detail{margin-top:3px}
.classes-filtres{display:flex;flex-wrap:wrap;gap:7px;align-items:center;margin:0 0 10px;
  padding:8px 10px;border:1px solid var(--border);border-radius:11px;background:var(--panel-2)}
.classes-filtres .titre{font-size:max(var(--t-min),.72rem);color:var(--texte-dim);text-transform:uppercase;letter-spacing:.5px;margin-right:2px}
.classes-filtres button.actif{box-shadow:0 0 0 2px var(--couleur-classe) inset;background:var(--fond-classe)}
@media (max-width:640px){
  .balance-plateau{grid-template-columns:1fr;align-items:stretch}
  .balance-axe{flex-direction:row;justify-content:center;min-width:0}
  .cascade-ligne{grid-template-columns:1fr;gap:3px}
  .cascade-montant{align-items:flex-start;text-align:left}
  .cascade-nom{font-size:.78rem}
}
@media (prefers-reduced-motion:reduce){
  .classe-carte,.levier[data-classe],.balance{transition:none;animation:none}
}
@media (forced-colors:active){
  .classe-carte,.levier[data-classe],.famille.classee,.balance-cote,.classe-pastille{
    border-color:CanvasText !important;background-image:none !important;background-color:Canvas !important;color:CanvasText !important}
  .classe-pastille .symbole{forced-color-adjust:none}
  /* La cascade garde ses barres visibles sans couleur : un contour suffit à
     montrer l'ampleur et le sens, le chiffre signé reste écrit à côté. */
  .cascade-piste{background:Canvas !important;border-color:CanvasText !important}
  .cascade-piste .barre{background-color:Canvas !important;background-image:none !important;
    border:2px solid CanvasText !important}
  .cascade-piste .zero{background:CanvasText !important}
  .cascade-montant{color:CanvasText !important}
}
@media print{
  .classes-filtres,.balance-axe .fleche{display:none}
  .classe-carte,.balance,.balance-cote,.levier,.famille{background:#fff !important;color:#000 !important;
    border-color:#000 !important;box-shadow:none !important}
  .classe-carte .definition,.classe-carte .pied,.balance-detail,.fiche-menage{color:#000 !important}
  .cascade-piste{background:#fff !important;border-color:#000 !important}
  .cascade-piste .barre{background-color:#fff !important;background-image:none !important;border:1px solid #000 !important}
  .cascade-piste .zero{background:#000 !important}
  .cascade-montant{color:#000 !important}
}
.levier{margin-bottom:11px}
.levier .ligne{display:flex;justify-content:space-between;gap:8px;font-size:.79rem;align-items:baseline}
.levier .nom{font-weight:500}
.levier .valeur{color:var(--accent);font-variant-numeric:tabular-nums;white-space:nowrap}
.levier .desc{font-size:max(var(--t-min),.7rem);color:var(--texte-dim);margin-top:2px}
.levier input[type=range]{width:100%;margin-top:5px;accent-color:var(--accent)}
.levier .source{font-size:max(var(--t-min),.66rem);color:var(--texte-dim);font-style:italic;margin-top:3px}
/* Statut de vérification : lisible sans couleur (texte + bordure), visible à l'impression et à la copie. */
.vstatut{font-size:max(var(--t-min),.66rem);margin-top:4px;padding:3px 6px;border-radius:4px;border:1px solid #3b4a66;color:#c9d3e6}
.vstatut b{font-weight:600}
.vstatut .vnote{font-style:italic;color:#9aa8c2;margin-top:2px}
.vstatut-verifie{border-color:#2f8f5b;color:#bfe9d1}
.vstatut-partiel{border-color:#4c7fd6}
.vstatut-date_decalee,.vstatut-non_verifie,.vstatut-inaccessible{border-style:dashed;border-color:#d68a2b;color:#f3d6a6}
.levier.non-verifie{border-style:dashed;border-color:#d68a2b}
.saisie-citoyenne{margin-top:5px;font-size:max(var(--t-min),.66rem);border:1px dashed #d68a2b;border-radius:4px;padding:4px 6px;background:repeating-linear-gradient(45deg,rgba(214,138,43,.10) 0 6px,transparent 6px 12px)}
.saisie-citoyenne summary{cursor:pointer;color:#f3d6a6}
.saisie-citoyenne input{width:100%;margin:2px 0;background:#0d1526;color:#e8edf7;border:1px solid #3b4a66;border-radius:3px;padding:2px 4px}
.saisie-texte{font-weight:600;color:#f3d6a6;margin-top:3px}
.saisie-etiquette{display:none}
@media print{.saisie-etiquette{display:block;font-weight:700;color:#000}.vstatut{color:#000;border-color:#000}}
.levier .ligne .bascule{margin-bottom:0}
/* Infobulle instantanée : tout réglage ou bouton annoté s'explique au survol
   (et au focus clavier), sans jamais recouvrir les leviers durablement. */
.infobulle{position:fixed;z-index:var(--z-infobulle);max-width:352px;background:#0d1526;border:1px solid var(--accent);
  border-radius:11px;padding:9px 11px;font-size:max(var(--t-min),.74rem);line-height:1.5;color:var(--texte);
  box-shadow:0 16px 38px rgba(2,6,23,.6);pointer-events:none;opacity:0;transition:opacity .08s}
.infobulle.visible{opacity:1}
.infobulle b{color:var(--accent)}
.infobulle .aide-titre{display:block;margin-bottom:3px;font-weight:600;color:var(--texte)}
[data-aide],[data-aide-levier]{cursor:help}
.levier .bulle-bouton{margin-left:auto;background:transparent;border:1px solid var(--border);border-radius:999px;
  color:var(--texte-dim);font-size:max(var(--t-min),.64rem);padding:1px 8px;line-height:1.5;white-space:nowrap}
.levier .bulle-bouton:hover{border-color:var(--accent);color:var(--accent);transform:none}
.levier .bulle-bouton.actif{border-color:var(--accent);color:var(--accent);background:rgba(56,189,248,.12)}
.bulle-levier{grid-column:1/-1;margin-top:9px;border-top:1px dashed var(--border);padding-top:9px;
  font-size:max(var(--t-min),.72rem);line-height:1.5;color:var(--texte-dim)}
.bulle-levier b{color:var(--texte)}
.bulle-levier .bulle-titre{font-size:max(var(--t-min),.67rem);text-transform:uppercase;letter-spacing:.5px;color:var(--texte-dim)}
.bulle-levier .bulle-section{margin-top:8px}
.bulle-levier ul{margin:4px 0 0 14px;padding:0}
.bulle-levier li{margin-bottom:2px}
.bulle-levier .bulle-med{color:var(--texte);font-variant-numeric:tabular-nums}
.bulle-levier .bulle-mesure{border-left:3px solid var(--border);padding-left:8px;margin:7px 0}
.bulle-levier .bulle-mesure.bulle-aggrave{border-left-color:var(--rouge)}
.bulle-levier .bulle-mesure.bulle-favorable{border-left-color:var(--vert)}
.bulle-levier .bulle-domaine{display:inline-block;margin:1px 4px 1px 0;padding:1px 7px;border-radius:999px;
  border:1px solid var(--border);font-variant-numeric:tabular-nums}
.bulle-levier .bulle-domaine.pos{border-color:rgba(34,197,94,.6);color:#86efac}
.bulle-levier .bulle-domaine.neg{border-color:rgba(239,68,68,.6);color:#fca5a5}
.bulle-levier .bulle-alerte{color:#fca5a5}
.bulle-levier .bulle-alerte.vigilance{color:#fcd34d}
.bulle-levier .bulle-journal li{font-style:italic}
.bulle-levier .bulle-note{margin-top:8px;font-style:italic;color:var(--texte-dim)}
.bulle-levier .bulle-chargement{font-style:italic}
.bascule{display:flex;align-items:center;gap:8px;font-size:.79rem;margin-bottom:9px}
.bascule input{width:18px;height:18px;accent-color:var(--vert)}
.recherche{width:100%;padding:9px 12px;border-radius:9px;border:1px solid var(--border);
  background:var(--panel-2);color:var(--texte);margin-bottom:10px}
.domaine{background:var(--panel-2);border:1px solid var(--border);border-radius:11px;padding:12px}
.domaine .tete{display:flex;justify-content:space-between;align-items:center;gap:10px}
.domaine .score{font-size:1.25rem;font-weight:700;font-variant-numeric:tabular-nums}
.domaine .ref{font-size:max(var(--t-min),.7rem);color:var(--texte-dim)}
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
.pied{color:var(--texte-dim);font-size:max(var(--t-min),.72rem);text-align:center;padding:14px 0 26px}
/* Le crédit du mouvement ferme la page : c'est le dernier texte qu'on lit, et
   le seul lien sortant du pied. Il respire comme l'attribution qu'il suit, sans
   dédoubler son espace — d'où le padding haut annulé. */
.pied.credit{margin-top:0;padding:0 0 26px}
.pied.credit a{font-weight:700}
.provenance{font-size:max(var(--t-min),.73rem);color:var(--texte-dim);max-height:210px;overflow:auto}
.provenance div{padding:3px 0;border-bottom:1px dashed rgba(147,163,189,.15)}
.onglets{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.onglets button.actif{background:linear-gradient(135deg,var(--mrsc-navy),var(--mrsc-bleu));border-color:var(--mrsc-bleu)}
.onglets-strates{padding:7px;background:#0f172a;border:1px solid var(--border);border-radius:12px}
.onglets-strates button{flex:1 1 118px;min-height:40px}
.onglets-strates button[aria-selected="true"]{background:linear-gradient(135deg,var(--mrsc-navy),var(--mrsc-bleu));border-color:var(--mrsc-bleu);color:#fff}
.panneau-strate{display:none;min-width:0}
.panneau-strate.actif{display:block}
.strate-intro{font-size:.78rem;color:var(--texte-dim);line-height:1.6;margin:2px 0 12px}
.strate-sous-titre{font-size:.84rem;margin:14px 0 7px;color:var(--texte)}
.tableau-strate{overflow:auto;max-height:430px;border:1px solid var(--border);border-radius:9px}
.tableau-strate table{min-width:600px}
.tableau-strate td.delta-pos{color:#86efac}.tableau-strate td.delta-neg{color:#fca5a5}
.note-source{font-size:max(var(--t-min),.7rem);line-height:1.55;color:var(--texte-dim);margin:8px 0;padding:8px 10px;background:rgba(15,23,42,.7);border-left:3px solid var(--accent);border-radius:0 8px 8px 0}
.grille-profil{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:9px;margin:10px 0}
.champ-profil{display:flex;flex-direction:column;gap:4px;font-size:max(var(--t-min),.72rem);color:var(--texte-dim)}
.champ-profil input,.champ-profil select{width:100%;padding:7px 9px;border-radius:8px;border:1px solid var(--border);background:var(--panel-2);color:var(--texte);font:inherit}
.champ-profil input[type=checkbox]{width:18px;height:18px;accent-color:var(--accent)}
.champ-profil input[readonly]{border-style:dashed;opacity:.86;cursor:default}
.profil-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:9px 0}
.range-bourse{width:120px;accent-color:var(--accent)}
.saisie-euros{max-width:125px;padding:5px 7px;border:1px solid var(--border);border-radius:7px;background:#0d1526;color:var(--texte);font:inherit}
.bourse-table{max-height:520px}
.bourse-table table{min-width:860px}
.bourse-table td,.bourse-table th{vertical-align:middle}
.marches-actions{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin:10px 0}
.marches-actions .pastille{white-space:normal}
.marches-table-row .positif{color:#86efac}.marches-table-row .negatif{color:#fca5a5}
/* ── Console de veille permanente ─────────────────────────────────────── */
.console{border-width:2px}
/* Ruban de veille : une seule ligne collante, jamais devant les leviers. */
.ruban-veille{position:sticky;top:0;z-index:var(--z-ruban);display:flex;align-items:center;gap:10px;
  flex-wrap:wrap;background:linear-gradient(135deg,#0e1a30,#141b33);border:1px solid var(--border);
  border-radius:12px;padding:7px 12px;margin-bottom:12px;box-shadow:0 8px 22px rgba(0,0,0,.45)}
.ruban-veille .ruban-titre{font-size:max(var(--t-min),.68rem);text-transform:uppercase;letter-spacing:.6px;
  color:var(--texte-dim);white-space:nowrap}
.ruban-veille .console-verdict{font-size:.78rem;padding:4px 12px;max-width:520px;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ruban-veille.niveau-vigilance{border-color:rgba(245,158,11,.65)}
.ruban-veille.niveau-risque{border-color:rgba(239,68,68,.7)}
.ruban-veille.niveau-hors_sol{border-color:var(--rouge);
  box-shadow:0 0 0 3px rgba(239,68,68,.25),0 8px 22px rgba(0,0,0,.5)}
.ruban-strates{display:flex;gap:5px;align-items:center}
.ruban-strate{width:26px;height:22px;border-radius:6px;border:1px solid var(--border);
  font-size:max(var(--t-min),.62rem);display:flex;align-items:center;justify-content:center;cursor:help;
  background:var(--panel-2);color:var(--texte-dim);font-weight:700}
.ruban-strate.niveau-favorable,.ruban-strate.niveau-tolerable{background:rgba(34,197,94,.22);color:#bbf7d0;border-color:rgba(34,197,94,.5)}
.ruban-strate.niveau-vigilance{background:rgba(245,158,11,.22);color:#fde68a;border-color:rgba(245,158,11,.55)}
.ruban-strate.niveau-risque{background:rgba(239,68,68,.24);color:#fecaca;border-color:rgba(239,68,68,.6)}
.ruban-strate.niveau-hors_sol{background:var(--rouge);color:#fff;border-color:#fff}
.ruban-pop{font-size:max(var(--t-min),.72rem);color:var(--texte-dim);white-space:nowrap}
.ruban-pop b{font-variant-numeric:tabular-nums}
.ruban-veille .ruban-actions{margin-left:auto;display:flex;gap:6px;flex-wrap:wrap}
.ruban-veille button{padding:5px 10px;font-size:max(var(--t-min),.74rem)}
/* Barre d'outils des leviers et vues */
.barre-leviers{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:10px}
.barre-leviers .recherche{flex:1;min-width:240px;margin-bottom:0}
.barre-leviers label{display:flex;align-items:center;gap:6px;font-size:.76rem;color:var(--texte-dim)}
.leviers-grille.compacte{grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:10px}
.famille.compacte{padding:9px 10px}
.famille.compacte h3{font-size:.76rem;margin-bottom:6px;padding-bottom:4px}
.levier.compact{margin-bottom:6px;display:grid;grid-template-columns:1fr 96px 74px auto;
  gap:6px;align-items:center;padding-bottom:5px;border-bottom:1px dashed rgba(147,163,189,.14)}
.levier.compact .nom{font-size:max(var(--t-min),.73rem)}
.levier.compact input[type=range]{margin-top:0}
.levier.compact .valeur{font-size:max(var(--t-min),.72rem);text-align:right}
.levier.compact .desc,.levier.compact .source,.levier .articles{display:none}
.levier:not(.compact) .articles{display:flex;flex-wrap:wrap;align-items:center;gap:4px;margin-top:4px}
.levier .articles-legende{font-size:max(var(--t-min),.6rem);color:#64748b;text-transform:uppercase;letter-spacing:.04em}
.levier .article{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:max(var(--t-min),.62rem);color:#8ab4ff;
  border:1px solid #2b3d5c;border-radius:6px;padding:0 5px;text-decoration:none;background:#111c2c}
.levier .article:hover{border-color:#8ab4ff;color:#c8dbff}
.levier .articles-hors{font-size:max(var(--t-min),.6rem);color:#64748b;font-style:italic}
/* Nuances institutionnelles : la couche qui traduit les curseurs en droit. */
#section-nuances .nuances-intro{color:#9fb0cc;font-size:.8rem;margin:2px 0 10px}
#section-nuances table{width:100%;border-collapse:collapse;font-size:.76rem}
#section-nuances th{color:var(--texte-dim);text-align:left;font-weight:600;padding:4px 6px;border-bottom:1px solid #2b3d5c}
#section-nuances td{padding:4px 6px;border-bottom:1px solid #1b2740;vertical-align:top}
#section-nuances td.chiffre{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;white-space:nowrap}
#section-nuances .plus{color:#7ee0a3}
#section-nuances .moins{color:#f3a0a0}
#section-nuances .ok{color:#7ee0a3}
#section-nuances .hors{color:#f3a0a0;font-weight:700}
#section-nuances .fentes,#section-nuances .limites{font-size:max(var(--t-min),.74rem);color:#9fb0cc}
#section-nuances .garde-fous{border:1px solid #7f1d1d;background:#2a1214;border-radius:8px;
  padding:8px 10px;margin:8px 0;font-size:.76rem;color:#fecaca}
#section-nuances .puce-indice{display:inline-block;border:1px solid #2b3d5c;border-radius:8px;
  padding:4px 8px;margin:0 6px 6px 0;background:#111c2c;font-size:max(var(--t-min),.74rem)}
#section-nuances .puce-indice b{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
/* Citations : le texte n'est jamais recopié ici, seul le lien vers la fiche servie. */
#section-nuances a.article,#section-verrous a.article{color:#bae6fd;border-bottom:1px dotted #38bdf8;
  text-decoration:none;font-style:normal}
#section-nuances a.article:hover,#section-verrous a.article:hover{border-bottom-style:solid}
#section-nuances .reglages-touches{display:grid;gap:6px;margin-top:6px}
#section-nuances .reglage-touche{background:#131c2f;border:1px solid #2b3d5c;border-radius:8px;
  padding:7px 9px;font-size:.76rem}
#section-nuances .badge-cible{display:inline-block;margin:1px 4px 1px 0;padding:1px 7px;
  border-radius:999px;border:1px solid #2b3d5c;font-variant-numeric:tabular-nums}
#section-verrous .verrou-groupe{margin-top:12px}
#section-verrous .verrou-titre{font-size:max(var(--t-min),.72rem);text-transform:uppercase;letter-spacing:.5px;
  color:#9fb0cc;margin-bottom:4px}
#section-verrous ul{list-style:none;margin:0;padding:0}
#section-verrous li{display:flex;flex-wrap:wrap;gap:8px;align-items:baseline;font-size:.78rem;
  border-bottom:1px dashed rgba(147,163,189,.18);padding:4px 0}
#section-verrous li.touche{border-left:3px solid #ef4444;padding-left:8px}
#section-verrous li.intact{border-left:3px solid #2f8f5b;padding-left:8px}
#section-verrous li.hors{border-left:3px dashed #d68a2b;padding-left:8px}
#section-verrous .verrou-seuil{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  white-space:nowrap}
#section-verrous .puce-reglage{display:inline-block;margin:0 3px;padding:1px 6px;border-radius:999px;
  border:1px solid #2b3d5c;font-size:max(var(--t-min),.7rem);font-style:normal}
#section-contradiction .objection{background:#131c2f;border:1px solid #2b3d5c;border-radius:8px;
  margin:8px 0;padding:8px 10px}
#section-contradiction .objection summary{cursor:pointer;display:flex;flex-wrap:wrap;gap:8px;
  align-items:baseline;font-size:.84rem}
#section-contradiction .objection[open] summary{margin-bottom:6px}
#section-contradiction .objection h4{margin:8px 0 3px;font-size:max(var(--t-min),.74rem);text-transform:uppercase;
  letter-spacing:.4px;color:var(--texte-dim);font-weight:600}
#section-contradiction .objection p{margin:0;font-size:.8rem;line-height:1.45;color:#dbe6f7}
#section-contradiction .objection .attaque{color:#9fb0cc;font-size:.76rem}
#section-contradiction .numero{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  color:var(--texte-dim)}
#section-contradiction .badge-statut{display:inline-block;padding:1px 8px;border-radius:999px;
  border:1px solid #2b3d5c;font-size:max(var(--t-min),.7rem)}
#section-contradiction .badge-statut.ok{color:#7ee0a3;border-color:#2f8f5b}
#section-contradiction .badge-statut.partiel{color:#f3c98b;border-color:#8f6b2f}
#section-contradiction .badge-statut.concede{color:#bae6fd;border-color:#2b6c8f}
#section-contradiction .badge-statut.encours{color:#e6d18b;border-color:#7f6b1d}
#section-contradiction .badge-statut.ouverte{color:#c3cbdb;border-color:#40506e}
#section-contradiction .famille,#section-contradiction .suivi{font-size:max(var(--t-min),.72rem);color:var(--texte-dim)}
#section-contradiction .meta{margin-top:6px;display:flex;flex-wrap:wrap;gap:10px;
  font-size:max(var(--t-min),.74rem);color:#9fb0cc}
#section-contradiction .puce-portee{border:1px dashed #2b3d5c;border-radius:8px;padding:1px 7px}
#section-contradiction ul.sources{list-style:none;margin:4px 0 0;padding:0;font-size:max(var(--t-min),.74rem);
  color:#9fb0cc}
#section-contradiction ul.sources li{margin:2px 0}
#section-contradiction .contre-modele{background:#131c2f;border:1px solid #2b3d5c;
  border-radius:8px;margin:8px 0;padding:8px 10px;font-size:.8rem;line-height:1.45}
#section-contradiction .contre-modele h4{margin:6px 0 3px;font-size:.78rem;color:#bae6fd}
#section-contradiction .contre-modele .porte-par{color:var(--texte-dim);font-size:max(var(--t-min),.74rem);font-style:italic}
#section-contradiction .garde-fous{border:1px solid #7f1d1d;background:#2a1214;border-radius:8px;
  padding:6px 9px;margin:8px 0;font-size:.76rem;color:#f3a0a0}
.levier.modifie{border-left:3px solid var(--accent);padding-left:8px;background:rgba(56,189,248,.06);
  border-radius:0 8px 8px 0}
.levier.modifie .nom{font-weight:700}
.puces{display:flex;gap:4px;flex-wrap:wrap;margin-top:4px}
.puce-effect{font-size:max(var(--t-min),.66rem);border-radius:6px;padding:1px 6px;border:1px solid var(--border);
  white-space:nowrap}
.puce-effect.pos{background:rgba(34,197,94,.16);color:#bbf7d0;border-color:rgba(34,197,94,.45)}
.puce-effect.neg{background:rgba(239,68,68,.16);color:#fecaca;border-color:rgba(239,68,68,.45)}
.console-corps.replie{display:none}
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
  background:var(--panel-2);font-size:max(var(--t-min),.74rem)}
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
.message-seuil .etiquette{font-size:max(var(--t-min),.68rem);text-transform:uppercase;letter-spacing:.4px;font-weight:700}
.message-seuil p{color:var(--texte-dim);margin-top:3px}
.message-seuil .source{font-size:max(var(--t-min),.66rem);color:var(--texte-dim);font-style:italic;margin-top:3px;display:block}
.jauge{height:11px;border-radius:7px;background:var(--panel-3);overflow:hidden;border:1px solid var(--border)}
.jauge > span{display:block;height:100%;transition:width .25s}
.graduations{display:flex;justify-content:space-between;font-size:max(var(--t-min),.64rem);color:var(--texte-dim);margin-top:3px}
.ligne-marge{display:flex;justify-content:space-between;gap:10px;font-size:.75rem;padding:4px 0;
  border-bottom:1px dashed rgba(147,163,189,.18)}
.ligne-marge .droite{color:var(--texte-dim);white-space:nowrap}
.bandeau-hors-sol{background:linear-gradient(90deg,rgba(239,68,68,.35),rgba(239,68,68,.06));
  border:1px solid var(--rouge);border-radius:10px;padding:9px 12px;font-size:.79rem;margin-top:10px}
.bandeau-hors-sol b{font-size:.82rem;letter-spacing:.3px}
.delta-mesure{font-size:.75rem;padding:4px 0;border-bottom:1px dashed rgba(147,163,189,.18);
  display:flex;justify-content:space-between;gap:10px}
.delta-mesure .valeur{font-variant-numeric:tabular-nums;white-space:nowrap}
/* Coût / gain réel : affichage live, rouge ou vert en transparence, comme le
   bandeau hors-sol mais dédié à la mesure budgétaire d'un réglage. */
.cout-gain{border-radius:10px;padding:9px 12px;font-size:.8rem;margin-top:8px;border:1px solid}
.cout-gain b.chiffre{font-size:1.05rem;font-variant-numeric:tabular-nums}
.cout-gain.gain{background:linear-gradient(90deg,rgba(34,197,94,.34),rgba(34,197,94,.06));
  border-color:var(--vert)}
.cout-gain.cout{background:linear-gradient(90deg,rgba(239,68,68,.34),rgba(239,68,68,.06));
  border-color:var(--rouge)}
.cout-gain.neutre{background:rgba(147,163,189,.12);border-color:var(--border)}
.cout-gain .detail{display:flex;flex-wrap:wrap;gap:12px;margin-top:6px;color:var(--texte-dim);font-size:max(var(--t-min),.72rem)}
.cout-gain .trace{margin-top:6px;font-size:max(var(--t-min),.66rem);color:var(--texte-dim);font-style:italic}
/* Badge live sous le levier manipulé et puce du ruban : toujours visibles. */
.cout-live-zone{grid-column:1/-1}
.cout-live{margin-top:6px;border-radius:9px;padding:5px 10px;font-size:.76rem;font-weight:600;
  border:1px solid;font-variant-numeric:tabular-nums}
.cout-live.gain{background:rgba(34,197,94,.20);border-color:rgba(34,197,94,.55);color:#86efac}
.cout-live.cout{background:rgba(239,68,68,.20);border-color:rgba(239,68,68,.55);color:#fca5a5}
.cout-live.neutre{background:rgba(147,163,189,.12);border-color:var(--border);color:var(--texte-dim);font-weight:400}
.ruban-cout{font-size:max(var(--t-min),.72rem);padding:3px 10px;border-radius:999px;border:1px solid;
  white-space:nowrap;font-variant-numeric:tabular-nums;font-weight:600}
.ruban-cout.gain{background:rgba(34,197,94,.20);border-color:rgba(34,197,94,.55);color:#86efac}
.ruban-cout.cout{background:rgba(239,68,68,.20);border-color:rgba(239,68,68,.55);color:#fca5a5}
.ruban-cout.neutre{background:rgba(147,163,189,.12);border-color:var(--border);color:var(--texte-dim)}
/* Coût / gain global : toujours dans la partie visible de la console, même
   quand le détail des seuils est replié. */
.cout-global-veille{margin:10px 0 4px}
/* Bulle explicative : le bloc « mesure live » doit se lire d'un coup d'œil. */
.bulle-levier .bulle-live{margin:8px 0 2px}
/* Audit et traçabilité : tableaux denses et lisibles en bas de page. */
.audit details{background:var(--panel-2);border:1px solid var(--border);border-radius:11px;
  padding:10px 13px;margin-bottom:10px}
.audit summary{cursor:pointer;font-weight:600;font-size:.86rem;color:var(--texte)}
.audit summary:hover{color:var(--accent)}
.audit .corps{margin-top:9px;font-size:max(var(--t-min),.74rem);color:var(--texte-dim)}
.audit table{width:100%;border-collapse:collapse;font-size:max(var(--t-min),.72rem)}
.audit th,.audit td{text-align:left;border-bottom:1px dashed rgba(147,163,189,.18);
  padding:5px 7px;vertical-align:top}
.audit th{color:var(--texte);font-size:max(var(--t-min),.7rem);text-transform:uppercase;letter-spacing:.4px}
.audit td.chiffre{font-variant-numeric:tabular-nums;white-space:nowrap}
.audit .formule{font-family:ui-monospace,Consolas,monospace;font-size:max(var(--t-min),.68rem);color:var(--texte)}
.audit .source-note{color:var(--texte-dim)}
/* ── Sommaire : lire la page dans l'ordre ──────────────────────────────────
   La page est longue : ce bandeau dit où l'on est et dans quel ordre lire.
   Il reprend la logique du parcours : comprendre, régler, mesurer, vérifier. */
.sommaire{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:12px;padding:8px 10px;
  background:var(--panel);border:1px solid var(--border);border-radius:12px}
.sommaire .titre-sommaire{font-size:max(var(--t-min),.68rem);text-transform:uppercase;letter-spacing:.6px;color:var(--texte-dim)}
.sommaire a{font-size:.75rem;text-decoration:none;color:var(--texte-dim);background:var(--panel-2);
  border:1px solid var(--border);border-radius:999px;padding:3px 10px;white-space:nowrap}
.sommaire a:hover{border-color:var(--accent);color:var(--texte)}
.sommaire a.actif{border-color:var(--accent);color:var(--accent);background:rgba(56,189,248,.12)}
.sommaire .etape{font-size:max(var(--t-min),.66rem);color:var(--texte-dim);padding:0 4px}
/* ── Lecture en clair ─────────────────────────────────────────────────────
   Les chiffres du moteur sont justes ; la section « lire le résultat » les
   remet en phrases. Une ligne par question que l'on se pose vraiment. */
.clair-resume{background:var(--panel-2);border:1px solid var(--border);border-left:4px solid var(--accent);
  border-radius:10px;padding:10px 13px;font-size:.88rem;margin-bottom:10px}
.clair-lignes{display:grid;gap:8px;grid-template-columns:repeat(auto-fit,minmax(340px,1fr))}
.clair-ligne{background:var(--panel-2);border:1px solid var(--border);border-radius:10px;padding:9px 12px;font-size:.8rem}
.clair-ligne .clair-tete{display:flex;justify-content:space-between;gap:10px;align-items:baseline;margin-bottom:3px}
.clair-ligne .clair-grandeur{font-weight:600;font-size:.76rem;color:var(--accent)}
.clair-ligne .clair-valeur{font-size:max(var(--t-min),.74rem);color:var(--texte);font-variant-numeric:tabular-nums}
.clair-ligne.niveau-favorable{border-left:3px solid var(--vert)}
.clair-ligne.niveau-defavorable{border-left:3px solid var(--rouge)}
.clair-ligne.niveau-neutre{border-left:3px solid var(--border)}
.clair-ligne .clair-explication{font-size:max(var(--t-min),.7rem);color:var(--texte-dim);margin-top:5px}
.clair-limites{margin-top:10px;font-size:max(var(--t-min),.72rem);color:var(--texte-dim)}
.clair-limites li{margin-left:16px}
/* ── Termes du lexique soulignés dans le texte ──────────────────────────── */
.terme{border-bottom:1px dotted var(--accent);cursor:help}
/* ── Modale (lexique et guide) ──────────────────────────────────────────── */
.overlay{position:fixed;inset:0;z-index:var(--z-modale);background:rgba(2,6,23,.72);display:none;
  align-items:flex-start;justify-content:center;padding:28px 14px;overflow:auto}
.overlay.visible{display:flex}
.modale{background:var(--panel);border:1px solid var(--accent);border-radius:14px;max-width:920px;width:100%;
  box-shadow:0 24px 60px rgba(0,0,0,.55)}
.modale-entete{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 18px;
  border-bottom:1px solid var(--border)}
.modale-entete h2{font-size:1rem}
.modale-corps{padding:14px 18px 18px;max-height:74vh;max-height:74dvh;overflow:auto}
.lexique-recherche{width:100%;margin-bottom:12px;padding:9px 12px;border-radius:9px;border:1px solid var(--border);
  background:var(--panel-2);color:var(--texte);font:inherit;font-size:.85rem}
.lexique-categorie{margin-bottom:14px}
.lexique-categorie h3{font-size:.85rem;color:var(--accent);margin-bottom:3px}
.lexique-categorie p{font-size:max(var(--t-min),.74rem);color:var(--texte-dim);margin-bottom:7px}
.lexique-terme{border-top:1px solid var(--border);padding:7px 0;font-size:.79rem}
.lexique-terme .lexique-mot{font-weight:600}
.lexique-terme .lexique-repere{color:var(--texte-dim);font-size:max(var(--t-min),.74rem);margin-top:3px}
.lexique-terme .lexique-voir{font-size:max(var(--t-min),.72rem);color:var(--accent);margin-top:3px}
.lexique-vide{color:var(--texte-dim);font-size:.8rem}
.guide-etape{background:var(--panel-2);border:1px solid var(--border);border-radius:11px;padding:12px 14px;margin-bottom:10px}
.guide-etape h3{font-size:.88rem;margin-bottom:4px;color:var(--accent)}
.guide-etape p{font-size:.82rem;color:var(--texte)}
.guide-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
@media(max-width:640px){body{padding:10px}header.entete h1{font-size:1.15rem}
  .ruban-veille{position:static}.console-corps{grid-template-columns:1fr}
  .levier.compact{grid-template-columns:1fr 70px auto}}
/* ── Le résumé de tête : les chiffres, puis la phrase ─────────────────────
   On doit comprendre le plan sans faire défiler vingt sections. Le bandeau ne
   calcule rien : il relit la balance (`renderResume` est appelé par
   `renderBalance`), donc les deux affichages ne peuvent pas diverger. */
.resume{background:linear-gradient(135deg,var(--panel-2),var(--panel));border-color:var(--mrsc-bleu)}
.resume-phrase{font-size:max(var(--t-min),.86rem);color:var(--texte);margin:2px 0 10px}
.resume .metric .valeur{font-variant-numeric:tabular-nums}
.resume-gain .valeur{color:var(--vert)}
.resume-cout .valeur{color:var(--rouge)}
.resume-actions{display:flex;flex-wrap:wrap;gap:9px;align-items:center;margin-top:10px}
.resume-actions a{font-size:max(var(--t-min),.8rem);color:var(--texte-dim)}
.resume-actions a:hover{color:var(--texte)}
/* ── Imprimer son plan : un mode, pas une capture ──────────────────────────
   Vingt sections sur une feuille, c'est du papier pour rien. Le bouton entre
   dans un mode visible à l'écran : la page ne montre plus que le résumé, si
   bien que ce qu'on voit est exactement ce qui s'imprimera. Le bandeau annonce
   le mode et propose de lancer l'impression ou de revenir — il ne s'imprime
   jamais lui-même. */
.bandeau-impression{position:sticky;top:0;z-index:var(--z-bandeau);display:none;
  gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:14px;padding:10px 13px;
  border:1px solid var(--accent);border-radius:12px;background:var(--panel);
  font-size:max(var(--t-min),.8rem)}
.bandeau-impression b{color:var(--texte)}
.bandeau-impression .aide{color:var(--texte-dim)}
.note-impression{display:none}
html.impression-plan .bandeau-impression{display:flex}
html.impression-plan .conteneur > *:not(.bandeau-impression):not(#resume){display:none}
/* L'interaction répond au geste, sans jamais devenir un feu d'artifice. */
.resume .metric{transition:transform .15s ease,border-color .15s ease}
.resume .metric:hover{border-color:var(--accent);transform:translateY(-1px)}
.cascade-piste .barre,.balance-cote .jauge-classe span{transition:width .25s ease,left .25s ease}
@media (prefers-reduced-motion:reduce){
  .resume .metric,.cascade-piste .barre,.balance-cote .jauge-classe span{transition:none}
  .resume .metric:hover{transform:none}
}
/* ── Les chapitres : quatre temps dans une page de vingt sections ─────────
   Le sommaire dit l'ordre ; les chapitres disent où l'on est, dans le
   déroulé, sans obliger à remonter. */
.chapitre{display:flex;align-items:flex-start;gap:12px;margin:20px 0 12px;padding:10px 14px;
  border-left:4px solid var(--mrsc-or);background:var(--panel-2);border-radius:0 12px 12px 0}
.chapitre-num{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;
  border-radius:50%;background:var(--mrsc-navy);color:var(--texte);font-weight:700;flex:0 0 auto}
.chapitre-titre{font-size:1.02rem;font-weight:700;letter-spacing:.3px}
.chapitre-aide{font-size:max(var(--t-min),.8rem);color:var(--texte-dim);margin-top:2px}

/* ── Le graphique : lisible à toutes les largeurs ─────────────────────────
   Le dessin a 900 unités de large. Étiré sur un écran de 1400 px, il s'élargit ;
   écrasé sur un téléphone, ses libellés deviennent illisibles. On lui donne
   donc une largeur minimale et une région qui défile : la courbe garde son
   échelle, la page garde sa largeur. */
.graphique{overflow-x:auto;max-width:100%;-webkit-overflow-scrolling:touch}
.graphique .svg-chart{min-width:640px}
.graphique:focus-visible,.tableau-defilant:focus-visible{outline:3px solid var(--mrsc-or);outline-offset:2px}

/* ══ Socle responsive : un seul jeu de règles, tous les écrans ═════════════
   Ce bloc vient en fin de feuille : il s'applique à l'écran seulement, et
   jamais à l'impression (l'impression a ses règles, plus haut). Quatre
   principes, mesurés dans `docs/RD_VISUEL_RESPONSIVE.md` :
   1. rien ne pousse la page — un enfant de grille ou de flex refuse par défaut
      de rétrécir sous son contenu, c'est ainsi qu'un tableau large déborde ;
   2. la page respire selon l'écran, pas selon un palier figé ;
   3. le texte grandit avec l'écran, sans jamais passer sous --t-min ;
   4. le tactile et les formulaires ont leurs propres règles : 44 px de cible,
      16 px de police dans un champ (sinon iOS zoome tout seul au focus). */
@media screen{
  .conteneur,section.bloc,.carte,.famille,.levier,.grille>*,.leviers-grille>*,
  .barre-contexte>*,.sommaire>*,.console-corps>*,.classes-legende>*,
  .balance-plateau>*,.cascade-ligne>*,.classe-carte>*,.audit>*{min-width:0}
  .tableau-defilant{max-width:100%;overflow:auto;-webkit-overflow-scrolling:touch;
    border:1px solid var(--border);border-radius:9px;background:var(--panel-2);
    box-shadow:inset -14px 0 14px -14px rgba(0,0,0,.55)}
  .tableau-defilant>table{margin:0}
  .tableau-defilant:focus-visible{outline:3px solid var(--mrsc-or);outline-offset:2px}
  body{padding:clamp(10px,1.6vw,18px);overflow-wrap:break-word}
  header.entete{padding:clamp(14px,1.6vw,22px)}
  section.bloc{padding:clamp(12px,1.4vw,18px)}
  header.entete h1{font-size:clamp(1.15rem,.8vw + .78rem,1.52rem);line-height:1.3}
  section.bloc>h2{font-size:clamp(1rem,.3vw + .9rem,1.16rem)}
  .metric .valeur{font-size:clamp(1.32rem,.6vw + 1rem,1.55rem)}
  .balance-cote .montant{font-size:clamp(1.3rem,1.1vw + .95rem,1.9rem)}
  .grille.metrics{grid-template-columns:repeat(auto-fit,minmax(min(100%,148px),1fr))}
  .grille.scenarios{grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr))}
  .grille.domaines{grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr))}
  .leviers-grille{grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr))}
  .console-corps{grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr))}
  .audit table,.bourse-table table{font-size:max(var(--t-min),.74rem)}
  section[id],nav[id],h2[id]{scroll-margin-top:calc(var(--collant) + 10px)}
  .lien-evitement{position:fixed;top:max(8px,env(safe-area-inset-top,0px));
    left:max(8px,env(safe-area-inset-left,0px));z-index:var(--z-evitement);
    transform:translateY(-200%);
    background:var(--panel-2);border:1px solid var(--mrsc-or);border-radius:9px;
    padding:10px 14px;color:var(--texte);text-decoration:none}
  .lien-evitement:focus-visible{transform:none}
  .sommaire-bascule{display:none}
}
/* Le sommaire tient sur une ligne et accompagne la lecture. Vingt sections sans
   repère, c'est vingt fois « où suis-je ? » : le bandeau reste en haut. */
@media screen and (min-width:641px){
  :root{--collant:50px}
  .sommaire{position:sticky;top:0;z-index:var(--z-sommaire);flex-wrap:nowrap;overflow-x:auto;
    box-shadow:0 8px 20px rgba(0,0,0,.28)}
  .sommaire-liste{display:flex;flex-wrap:nowrap;align-items:center;gap:6px}
  .ruban-veille{top:var(--collant)}
}
@media screen and (max-width:1200px){
  .sommaire .titre-sommaire{display:none}
  .sommaire-liste{overflow-x:auto}
}
@media screen and (max-width:900px){
  .cascade-ligne{grid-template-columns:minmax(96px,1.1fr) minmax(72px,2.2fr) auto}
  .sommaire{box-shadow:none}
}
@media screen and (max-width:900px){
  /* Deux panneaux de 330 px dans 700 px se lisent mal : un seul, large. */
  .console-corps{grid-template-columns:minmax(0,1fr)}
  .onglets-strates{display:flex;flex-wrap:nowrap;overflow-x:auto}
  .onglets-strates button{flex:0 0 auto}
}
@media screen and (max-width:640px){
  :root{--collant:44px}
  .sommaire{position:sticky;top:0;z-index:var(--z-sommaire);gap:7px;padding:6px;flex-wrap:nowrap}
  .sommaire-bascule{display:inline-flex;align-items:center;gap:7px;min-height:44px;
    border-color:var(--accent);color:var(--texte)}
  .sommaire-liste{display:none}
  .sommaire.ouverte .sommaire-liste{display:flex;flex-wrap:wrap;overflow-x:visible}
  .onglets-strates{display:flex;flex-wrap:nowrap;overflow-x:auto}
  .onglets-strates button{flex:0 0 auto}
  section.bloc>h2{display:block}
  section.bloc>h2 .aide{display:block;margin-top:3px}
}
@media screen and (max-width:480px){
  /* Quatre chiffres en deux colonnes plutôt qu'en quatre : chaque nombre
     garde de la place, y compris « +49,1 Md€/an ». */
  .grille.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}
  .resume .metric .valeur{font-size:1.2rem}
  .pastille{white-space:normal}
  .tableau-defilant table{font-size:max(var(--t-min),.76rem)}
}
/* Le sommaire ouvert sur téléphone ne doit pas manger l'écran : il défile. */
@media screen and (max-width:640px){
  .sommaire.ouverte .sommaire-liste{max-height:46vh;overflow-y:auto}
}
/* Contraste renforcé demandé par le système : bordures plus franches, textes
   secondaires plus lisibles. Aucune information ne dépend de cette règle. */
@media screen and (prefers-contrast:more){
  :root{--border:#4a5c85;--texte-dim:#b9c6dc}
  .carte,section.bloc,.tableau-defilant,.graphique .svg-chart{border-width:2px}
}
@media screen and (pointer:coarse){
  button,.bouton,summary,.onglets button,.onglets-strates button,.sommaire a,
  .sommaire-bascule,.annee-classes button,.classes-filtres button,
  label.select-horizon{min-height:44px}
  .sommaire a,.onglets-strates button,.classes-filtres button,
  .annee-classes button{display:inline-flex;align-items:center}
  input,select,textarea{font-size:max(16px,1rem)}
  input[type=range]{height:34px}
}
/* ══ Rendu différé des sections basses ═════════════════════════════════════
   Dix des vingt-quatre sections (nuances, verrous, contradiction, résultats
   année par année, trajectoires, domaines, matrice, journal, provenance,
   audit) vivent sous la ligne de flottaison : le navigateur n'a pas besoin de
   les mettre en page tant qu'on ne s'en approche pas. `content-visibility:auto`
   le lui dit ; `contain-intrinsic-size` lui donne une hauteur de remplacement,
   sans quoi la barre de défilement sauterait à chaque section atteinte. Rien
   n'est retiré du document : les ancres, la recherche dans la page et
   l'impression continuent de tout trouver. */
#section-nuances,#section-verrous,#section-contradiction,#section-resultats,
#section-trajectoires,#section-domaines,#section-matrice,#section-journal,
#section-provenance,#section-audit{content-visibility:auto;contain-intrinsic-size:auto 620px}

/* ══ Impression : tout le contenu, rien de coupé ════════════════════════════
   À l'écran, les grands tableaux défilent dans une région à hauteur plafonnée :
   c'est confortable et ça n'écrase pas la page. Sur papier, ce plafond
   supprimerait des lignes en silence — les vingt-trois tableaux de l'audit
   feraient trois lignes chacun. On rend donc tout le contenu, on enlève les
   fonds sombres et les barres collantes, et on évite de couper une ligne en
   deux. */
@media print{
  .defilable,.journal,.provenance,.tableau-strate,.bourse-table,.tableau-defilant,.graphique{
    max-height:none;overflow:visible;box-shadow:none;border-color:#000}
  .graphique .svg-chart{min-width:0;height:auto}
  .sommaire,.ruban-veille{position:static;box-shadow:none}
  .sommaire-bascule,.lien-evitement,.resume-actions,.infobulle,.overlay{display:none}
  .resume,.chapitre{background:#fff !important;border-color:#000 !important;box-shadow:none}
  .chapitre-num{background:#fff !important;color:#000 !important;border:1px solid #000}
  tr,li{page-break-inside:avoid}
  a[href^="#"]{text-decoration:none;color:#000}
  /* Le rendu différé est levé : ce qu'on n'a jamais approché à l'écran doit
     quand même s'imprimer. */
  section.bloc{content-visibility:visible}
  /* La ligne d'attribution ne s'imprime qu'ici : sur une feuille détachée, elle
     dit d'où vient le plan. */
  .note-impression{display:block}
  /* Le bandeau sert à se servir de l'impression : il ne s'imprime pas. */
  .bandeau-impression{display:none !important}
  /* Mode « mon plan » : seule la page du plan s'imprime, avec le crédit du
     mouvement en pied — les deux seuls contenus qui aient un sens sur papier. */
  html.impression-plan .conteneur > *{display:none !important}
  html.impression-plan .conteneur > #resume{display:block !important}
  html.impression-plan .conteneur > .pied.credit{display:block !important}
  html.impression-plan #resume{background:#fff !important;border-color:#000 !important}
}
</style>
<script>
  window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
</script>
<script defer src="/_vercel/insights/script.js"></script>
</head>
<body>
<a class="lien-evitement" href="#sommaire">Aller au contenu</a>
<div class="conteneur">

  <div class="bandeau-impression" id="bandeau-impression" role="region" tabindex="-1"
       aria-label="Mode impression : seule la page du plan s'imprimera">
    <b>Mode impression.</b>
    <span class="aide">La page ne montre plus que votre plan : c'est exactement ce qui sortira sur papier.</span>
    <button class="primaire" type="button" onclick="lancerImpression()">🖨️ Lancer l'impression</button>
    <button class="discret" type="button" onclick="quitterImpressionPlan()">Revenir à la page entière</button>
  </div>

  <header class="entete">
    <h1>Simulateur Macro-Politique — Démocratie et politique, du peuple, pour le peuple, par le peuple</h1>
    <p>Choisissez vos politiques : le modèle à 5 échelons propage les effets, domaine par domaine, avec les données publiques réelles du jour.</p>
    <div class="barre-contexte">
      <span class="pastille" id="badge-contexte">contexte : chargement…</span>
      <span class="pastille" id="badge-date">—</span>
      <span class="pastille" id="badge-leviers">—</span>
      <label class="select-horizon" data-aide="<b>Horizon de simulation</b>Une mandature = 5 ans ; deux mandatures consécutives = 10 ans. Les dynamiques à maturation longue s'activent à partir du sixième exercice.">
        Horizon <select id="horizon-simulation" aria-label="Horizon de simulation" onchange="changerHorizon(this.value)">
          <option value="5" selected>1 mandature · 5 ans</option>
          <option value="10">2 mandatures · 10 ans</option>
        </select>
      </label>
      <span class="pastille" id="badge-horizon">une mandature · 5 ans</span>
      <button id="btn-lexique" onclick="ouvrirLexique()" data-aide="<b>Lexique</b>Chaque mot technique employé par la page, défini en français ordinaire, avec un repère chiffré. Les termes soulignés en pointillé dans la page s'expliquent aussi au survol.">📖 Lexique</button>
      <button id="btn-guide" onclick="ouvrirGuide()" data-aide="<b>Guide de démarrage</b>Quatre étapes pour comprendre ce que fait le simulateur, ce qu'il mesure et ce qu'il ne mesure pas.">❓ Guide</button>
      <button id="btn-partage" onclick="partagerReglages()" data-aide="<b>Partager mes réglages</b>Copie une adresse qui rouvre le simulateur exactement sur les réglages affichés. Utile pour soumettre un budget au débat : rien n'est envoyé au serveur, tout est dans le lien.">🔗 Partager mes réglages</button>
      <span class="separateur" aria-hidden="true"></span>
      <button class="discret" onclick="reinitialiser()" data-aide="<b>Réinitialiser</b>Ramène tous les réglages à leur valeur neutre (aucune politique nouvelle) : la référence de comparaison.">Réinitialiser les leviers</button>
      <button class="primaire" id="btn-rafraichir" onclick="rafraichirDonnees()" data-aide="<b>Rafraîchir les données</b>Interroge Eurostat, la BCE, la Banque mondiale, le change et le pétrole depuis votre navigateur ; les sources sans en-tête CORS passent par le relais du serveur. Le contexte « instant T » et les scores sont ensuite recalculés.">Rafraîchir les données (API publiques)</button>
      <button class="primaire" id="btn-simuler" onclick="simuler(true)" data-aide="<b>Simuler avec impacts croisés</b>Recalcule l'horizon sélectionné (5 ou 10 ans), les 20 domaines et la matrice levier × domaine (un réglage isolé à la fois). Le modèle reste une exploration, pas une prévision.">Simuler avec impacts croisés</button>
      <span class="separateur" aria-hidden="true"></span>
      <button id="btn-export-json" disabled onclick="exporter('json')" data-aide="<b>Export JSON</b>Télécharge la simulation affichée : 5 étapes annuelles, 20 domaines, indicateurs, garde-fous et journal causal.">Export JSON</button>
      <button id="btn-export-csv" disabled onclick="exporter('csv')" data-aide="<b>Export CSV</b>Même contenu que l'export JSON, en tableau — pour retravailler les chiffres dans un tableur.">Export CSV</button>
    </div>
    <p class="aide" id="avis-lien" hidden></p>
  </header>

  <section class="bloc resume" id="resume" aria-labelledby="resume-titre">
    <h2 id="resume-titre">🧾 Votre plan en un coup d'œil <span class="aide">les chiffres qui comptent, repris de la balance — rien n'est recalculé ici</span></h2>
    <p class="resume-phrase" id="resume-phrase">Déplacez un curseur : le plan se pèse ici, en milliards d'euros par an.</p>
    <div class="grille metrics">
      <div class="carte metric"><div class="libelle">Solde du plan</div>
        <div class="valeur" id="resume-solde">—</div><div class="delta neutre" id="resume-solde-note">en attente d'une simulation</div></div>
      <div class="carte metric"><div class="libelle">Ce qui entre</div>
        <div class="valeur" id="resume-entrees">—</div><div class="delta neutre">recettes + économies</div></div>
      <div class="carte metric"><div class="libelle">Ce qui sort</div>
        <div class="valeur" id="resume-sorties">—</div><div class="delta neutre" id="resume-sorties-note">dépenses engagées</div></div>
      <div class="carte metric"><div class="libelle">Par ménage</div>
        <div class="valeur" id="resume-menage">—</div><div class="delta neutre" id="resume-menage-note">ordre de grandeur</div></div>
    </div>
    <div class="resume-actions">
      <button class="primaire" type="button" onclick="allerAuxLeviers()">Régler les leviers</button>
      <a href="#section-classes">Voir la balance et les cinq classes</a>
      <button class="discret" type="button" id="bouton-imprimer-plan"
        onclick="imprimerPlan()" aria-describedby="resume-impression-note">🖨️ Imprimer mon plan</button>
    </div>
    <p class="aide note-impression" id="resume-impression-note">Simulateur macro-politique — outil citoyen à code ouvert du M.R.S.C. · thejmimiia-code.github.io/MRSC/simulateur.html</p>
  </section>

  <nav class="sommaire" id="sommaire" aria-label="Sommaire de la page">
    <button type="button" class="sommaire-bascule" id="sommaire-bascule"
      aria-expanded="false" aria-controls="sommaire-liste"
      onclick="basculerSommaire()">☰ Sommaire</button>
    <div class="sommaire-liste" id="sommaire-liste">
    <span class="titre-sommaire">Lire dans l'ordre</span>
    <a href="#section-contexte" onclick="marquerSommaire(this)">1. Où en est-on</a>
    <span class="etape">›</span>
    <a href="#section-clair" onclick="marquerSommaire(this)">2. Ce que ça donne</a>
    <span class="etape">›</span>
    <a href="#section-leviers" onclick="marquerSommaire(this)">3. Régler</a>
    <span class="etape">›</span>
    <a href="#section-classes" onclick="marquerSommaire(this)" data-aide="<b>Les 5 classes de leviers</b>La carte qui manquait : ce qui fait entrer de l'argent (vert), ce qui évite une dépense (vert hachuré), ce qui en engage (rouge), ce qui change les règles (bleu) et ce qui vient de l'extérieur (or).">🧩 Classes</a>
    <span class="etape">›</span>
    <a href="#section-resultats" onclick="marquerSommaire(this)">4. Mesurer</a>
    <span class="etape">›</span>
    <a href="#section-audit" onclick="marquerSommaire(this)">5. Vérifier</a>
    <a href="#console-pilotage" class="discret" style="margin-left:auto" data-aide="<b>Console de veille</b>Le bandeau qui prévient quand un seuil est franchi.">Veille</a>
    <a href="#section-strates" class="discret" data-aide="<b>Vues par strate</b>Local, national, Europe, monde, géopolitique, ménages, bourse.">Strates</a>
    <a href="#section-domaines" class="discret" data-aide="<b>Domaines</b>Les 20 secteurs de l'action publique, notés par écart à la référence.">Domaines</a>
    <a href="#section-matrice" class="discret" data-aide="<b>Matrice</b>L'effet de chaque levier sur chaque domaine, mesuré par différences finies.">Matrice</a>
    <a href="#section-contradiction" class="discret" data-aide="<b>Objections</b>Le registre de la contradiction : la meilleure version de chaque critique, ce que le dépôt concède, ce qu'il maintient, ce qui le ferait changer d'avis — et les quatre contre-modèles auxquels il se mesure.">Objections</a>
  </div>
  </nav>

  <div class="ruban-veille" id="ruban-veille">
    <span class="ruban-titre">Veille permanente</span>
    <span class="console-verdict" id="ruban-verdict">en attente de la première simulation…</span>
    <span class="ruban-strates" id="ruban-strates"></span>
    <span class="ruban-pop" id="ruban-population">risque population —</span>
    <span class="ruban-cout neutre" id="ruban-cout" data-aide="<b>Coût / gain réel du programme actif</b>Solde net des réglages globaux croisés (recettes nouvelles − dépenses nouvelles), recalculé en temps réel à chaque mouvement. Rouge = coût réel, vert = gain réel, en Md€ par an.">💶 coût / gain réel : —</span>
    <span class="ruban-actions">
      <button class="discret" id="btn-console-details" onclick="basculerDetailsConsole()" data-aide="<b>Détail des seuils</b>Replie ou déplie le corps de la console de veille pour libérer l'écran : le verdict et les cinq strates restent affichés.">Masquer le détail des seuils</button>
      <button class="discret" id="btn-densite" onclick="basculerDensite()" data-aide="<b>Vue compacte</b>Une ligne par levier : le catalogue tient à l'écran, tous réglables en direct.">Vue compacte</button>
      <button class="primaire" onclick="allerAuxLeviers()" data-aide="<b>Régler les leviers</b>Fait défiler jusqu'à la grille des paramètres, où chaque geste relance la simulation en direct.">Régler les leviers</button>
      <button class="discret" onclick="allerAudit()" data-aide="<b>Audit &amp; traçabilité</b>Toutes les sources officielles, chaque formule, chaque seuil et la méthode des dynamiques croisées : le simulateur à livre ouvert, pas une boîte noire.">🔍 Audit &amp; sources</button>
    </span>
  </div>

  <div id="zone-alertes"></div>

  <div class="infobulle" id="infobulle" role="tooltip" aria-hidden="true"></div>

  <div class="overlay" id="overlay" aria-hidden="true" onclick="siClicDehors(event)">
    <div class="modale" role="dialog" aria-modal="true" aria-labelledby="modale-titre" id="modale">
      <div class="modale-entete">
        <h2 id="modale-titre">Lexique</h2>
        <button class="discret" onclick="fermerModale()" data-aide="<b>Fermer</b>Revient au simulateur ; le réglage en cours n'est pas perdu.">Fermer ✕</button>
      </div>
      <div class="modale-corps" id="modale-corps"></div>
    </div>
  </div>

  <div class="chapitre" id="chapitre-comprendre">
    <span class="chapitre-num" aria-hidden="true">1</span>
    <div class="chapitre-texte">
      <p class="chapitre-titre">Comprendre</p>
      <p class="chapitre-aide">Où en est le pays aujourd'hui, avec les données publiques réellement collectées — et ce que le plan change.</p>
    </div>
  </div>

  <section class="bloc" id="section-contexte">
    <h2>Contexte « instant T » <span class="aide">données publiques réellement collectées, avec provenance et licence</span></h2>
    <div class="grille metrics" id="grid-metrics"></div>
  </section>

  <section class="bloc console" id="console-pilotage">
    <div class="console-entete">
      <h2>Console de veille permanente <span class="aide">seuils tolérables → hors-sol, strate par strate, mis à jour à chaque réglage</span></h2>
      <div class="console-verdict" id="console-verdict">en attente de la première simulation…</div>
    </div>
    <div class="cout-global-veille">
      <h3 class="console-titre" data-aide="<b>Coût / gain réel des réglages globaux croisés</b>Recettes nouvelles, dépenses nouvelles et solde net de l'ensemble des leviers actifs, croisés par le moteur à chaque simulation : le chiffre se met à jour en temps réel, avec les sources officielles qui l'ancrent. Ce bloc reste affiché même quand le détail des seuils est replié.">💶 Coût / gain réel des réglages globaux croisés</h3>
      <div id="console-cout-global"><div class="aide">en attente de la première simulation…</div></div>
    </div>
    <div id="console-danger"></div>
    <div class="console-strates" id="console-strates"></div>
    <div class="console-corps" id="console-corps">
      <div>
        <h3 class="console-titre">Risque pour la population</h3>
        <div id="console-population"></div>
        <h3 class="console-titre">Effet de votre dernière modification</h3>
        <div id="console-derniere-modification"></div>
        <h3 class="console-titre" data-aide="<b>Conseiller temps réel</b>À chaque mouvement de réglage, le moteur rejoue la trajectoire avec le levier à sa position d'avant puis d'après votre geste : effets directs, ricochets (effet papillon), garde-fous qui basculent et pistes de compensation, comme un conseiller spécialisé.">🦋 Conseiller temps réel (effet papillon)</h3>
        <div id="console-conseil"><div class="aide">Bougez un curseur ou un interrupteur : le conseiller lit chaque décision et ses ricochets en temps réel.</div></div>
      </div>
      <div>
        <h3 class="console-titre">Messages de seuil</h3>
        <div id="console-alertes"></div>
        <h3 class="console-titre">Marges de manœuvre et audaces possibles</h3>
        <div id="console-marges"></div>
      </div>
    </div>
  </section>

  <section class="bloc" id="section-clair">
    <h2>🧭 Lire le résultat <span class="aide">la même simulation, expliquée phrase par phrase — sans jargon, à partir des chiffres déjà calculés</span></h2>
    <div class="clair-resume" id="clair-resume">en attente de la première simulation…</div>
    <div class="clair-lignes" id="clair-lignes"></div>
    <ul class="clair-limites" id="clair-limites"></ul>
  </section>

  <div class="chapitre" id="chapitre-mesurer">
    <span class="chapitre-num" aria-hidden="true">2</span>
    <div class="chapitre-texte">
      <p class="chapitre-titre">Mesurer</p>
      <p class="chapitre-aide">Ce que le plan produit, année par année : la cascade des cinq échelons, les strates, la transmission entre générations.</p>
    </div>
  </div>

  <section class="bloc" id="section-impact">
    <h2>Surface d'impact de vos choix <span class="aide">recettes, dépenses et solde des mesures activées (année terminale)</span></h2>
    <div class="grille metrics" id="grid-impact"></div>
  </section>

  <section class="bloc" id="section-bilan-intergenerationnel">
    <h2>Transmission entre générations <span class="aide">dette, besoins non couverts, investissements à maturité et risque climatique — composantes séparées, sans score synthétique</span></h2>
    <div class="grille metrics" id="bilan-intergenerationnel"></div>
  </section>

  <section class="bloc" id="section-cascade">
    <h2>Cascade systémique des 5 échelons <span class="aide">locale → nationale → européenne → mondiale → géopolitique</span></h2>
    <div class="strates-cascade" id="strates-cascade"></div>
  </section>

  <section class="bloc" id="section-strates">
    <h2>Effets comparés par strate <span class="aide">scénario contre référence — les valeurs simulées restent des écarts de modèle, pas une prévision</span></h2>
    <p class="strate-intro">Parcourez les niveaux territoriaux, les comptes publics, l'Europe, les marchés, la géopolitique et un profil de ménage modifiable. Les observations réelles restent séparées des trajectoires simulées. Les seuls périmètres chiffrés sont ceux dont la source et l'hypothèse sont affichées.</p>
    <div class="onglets onglets-strates" role="tablist" aria-label="Vues par strate">
      <button type="button" role="tab" id="tab-strate-local" aria-selected="true" aria-controls="panneau-strate-local" class="actif" onclick="afficherOngletStrate('local')">Local</button>
      <button type="button" role="tab" id="tab-strate-national" aria-selected="false" aria-controls="panneau-strate-national" onclick="afficherOngletStrate('national')">National</button>
      <button type="button" role="tab" id="tab-strate-europe" aria-selected="false" aria-controls="panneau-strate-europe" onclick="afficherOngletStrate('europe')">Europe</button>
      <button type="button" role="tab" id="tab-strate-mondial" aria-selected="false" aria-controls="panneau-strate-mondial" onclick="afficherOngletStrate('mondial')">Monde</button>
      <button type="button" role="tab" id="tab-strate-geopolitique" aria-selected="false" aria-controls="panneau-strate-geopolitique" onclick="afficherOngletStrate('geopolitique')">Géopolitique</button>
      <button type="button" role="tab" id="tab-strate-menages" aria-selected="false" aria-controls="panneau-strate-menages" onclick="afficherOngletStrate('menages')">Ménages</button>
      <button type="button" role="tab" id="tab-strate-boursier" aria-selected="false" aria-controls="panneau-strate-boursier" onclick="afficherOngletStrate('boursier')">Bourse &amp; marchés</button>
    </div>
    <div class="panneau-strate actif" id="panneau-strate-local" role="tabpanel" aria-labelledby="tab-strate-local"></div>
    <div class="panneau-strate" id="panneau-strate-national" role="tabpanel" aria-labelledby="tab-strate-national"></div>
    <div class="panneau-strate" id="panneau-strate-europe" role="tabpanel" aria-labelledby="tab-strate-europe"></div>
    <div class="panneau-strate" id="panneau-strate-mondial" role="tabpanel" aria-labelledby="tab-strate-mondial"></div>
    <div class="panneau-strate" id="panneau-strate-geopolitique" role="tabpanel" aria-labelledby="tab-strate-geopolitique"></div>
    <div class="panneau-strate" id="panneau-strate-menages" role="tabpanel" aria-labelledby="tab-strate-menages"></div>
    <div class="panneau-strate" id="panneau-strate-boursier" role="tabpanel" aria-labelledby="tab-strate-boursier"></div>
  </section>

  <div class="chapitre" id="chapitre-regler">
    <span class="chapitre-num" aria-hidden="true">3</span>
    <div class="chapitre-texte">
      <p class="chapitre-titre">Régler</p>
      <p class="chapitre-aide">Les scénarios rejouables, les préréglages doctrinaux, les classes de leviers et leurs limites juridiques.</p>
    </div>
  </div>

  <section class="bloc" id="section-scenarios">
    <h2>Scénarios types du dépôt <span class="aide">situations rejouées par le moteur d'origine, année par année — pour comparaison</span></h2>
    <div class="grille scenarios" id="scenario-grid"></div>
  </section>

  <section class="bloc" id="section-presets">
    <h2>Préréglages doctrinaux <span class="aide">des combinaisons cohérentes de leviers, chargées dans le simulateur puis ajustables curseur par curseur</span></h2>
    <div class="grille scenarios" id="preset-grid"></div>
  </section>

  <section class="bloc" id="section-classes">
    <h2>🧩 Les 5 classes de leviers <span class="aide">la carte qui manquait : chaque levier porte une seule classe, un symbole, une couleur M.R.S.C et un motif — l'information reste lisible sans la couleur (impression, daltonisme, contraste renforcé)</span></h2>
    <p class="strate-intro" id="classes-intro">Le catalogue s'organise en <b>5 classes</b> : <b>recettes</b> (ce qui entre), <b>économies d'efficacité</b> (ce qu'on arrête de payer à vide), <b>dépenses et investissements</b> (ce qui sort), <b>règles du jeu</b> (ce qui change la décision, pas les comptes) et <b>monde subi</b> (ce qui vient de l'extérieur). Chaque classe a sa couleur, son symbole, son motif de fond et sa phrase : cliquez une classe pour ne voir que ses leviers.</p>
    <div class="classes-legende" id="classes-legende" role="group" aria-label="Légende des 5 classes"></div>
    <div class="balance" id="balance-classes">
      <div class="balance-titre">
        <b>⚖️ La balance du plan</b>
        <div class="annee-classes" role="group" aria-label="Année lue dans les classes">
          <button type="button" class="discret" id="classe-annee-prec" onclick="changerAnneeClasses(-1)" data-aide="<b>Année précédente</b>Relit la balance, la cascade et les cinq cartes à l'année d'avant : un plan n'arrive pas en une fois, chaque levier a sa montée en charge.">‹ an précédent</button>
          <span class="annee-courante" id="classe-annee-courante" aria-live="polite">dernière année</span>
          <button type="button" class="discret" id="classe-annee-suiv" onclick="changerAnneeClasses(1)" data-aide="<b>Année suivante</b>Avance d'un an dans la même simulation : on voit le plan se remplir, levier par levier, jusqu'à son régime de fin de mandature.">an suivant ›</button>
        </div>
        <span class="verdict" id="balance-verdict">lancez une simulation pour peser les deux plateaux</span>
      </div>
      <div class="balance-plateau">
        <div class="balance-cote entrees" id="balance-entrees">
          <span class="etiquette">Ce qui entre <span aria-hidden="true">+</span></span>
          <span class="montant" id="balance-entrees-montant">—</span>
          <span class="menage" id="balance-entrees-menage">recettes nouvelles + économies d'efficacité</span>
          <span class="jauge-classe"><span id="balance-jauge-entrees" style="width:0%"></span></span>
        </div>
        <div class="balance-axe" aria-hidden="false">
          <span class="fleche" aria-hidden="true">⇄</span>
          <span class="net neutre" id="balance-net">solde : —</span>
        </div>
        <div class="balance-cote sorties" id="balance-sorties">
          <span class="etiquette">Ce qui sort <span aria-hidden="true">−</span></span>
          <span class="montant" id="balance-sorties-montant">—</span>
          <span class="menage" id="balance-sorties-menage">dépenses et investissements</span>
          <span class="jauge-classe"><span id="balance-jauge-sorties" style="width:0%"></span></span>
        </div>
      </div>
      <p class="balance-detail" id="balance-detail">Les montants viennent du moteur : chaque année simulée livre le montant de chaque levier, montée en charge comprise. Aucun total n'est saisi à la main.</p>
      <p class="classe-rythme" id="classe-rythme">Le rythme du plan — combien d'effet arrive la première année, combien à la fin — s'affiche ici dès la première simulation.</p>
      <div class="cascade" id="cascade-classes">
        <div class="cascade-titre">
          <b>🧭 La cascade du plan, marche par marche</b>
          <span class="legende">un seul axe pour toutes les marches : chaque classe déplace le cumul, et l'escalier se referme sur le solde — ce qu'aucun total annuel ne montre</span>
        </div>
        <ol class="cascade-marches" id="cascade-marches"></ol>
        <p class="cascade-note" id="cascade-note">La cascade se dessine dès la première simulation : elle montre dans quel ordre le plan se construit, du premier euro qui entre au solde. Les classes « règles » et « monde » en restent dehors : leurs unités ne sont pas des euros.</p>
      </div>
    </div>
    <div class="grille classes" id="grille-classes"></div>
    <p class="strate-intro" id="classes-note"></p>
  </section>

  <section class="bloc" id="section-leviers">
    <h2>Vos leviers <span class="aide">tous les paramètres du catalogue, visibles et actionnables — chaque geste se répercute en direct ; la section « Nuances institutionnelles », juste en dessous, traduit chaque curseur en seuil et en délai de droit</span></h2>
    <div class="barre-leviers">
      <input class="recherche" id="recherche-levier" placeholder="Rechercher un levier (ex. TVA, défense, RIC, retraites…)" oninput="filtrerLeviers(this.value)" data-aide="<b>Rechercher un réglage</b>Filtre tous les leviers par libellé, description ou clé technique. Le compteur affiche le nombre de leviers visibles et modifiés.">
      <span class="pastille" id="compteur-leviers">—</span>
      <button class="discret" id="btn-classes-seules" onclick="basculerClasseSeules()" data-aide="<b>Mes leviers seulement</b>Masque tout le catalogue sauf les leviers que vous avez déplacés : on relit son propre plan sans se perdre dans les 156 curseurs.">Mes leviers seulement</button>
      <label data-aide="<b>Vue compacte</b>Une ligne par levier, sans description : le catalogue tient à l'écran tout en restant actionnable en direct.">
        <input type="checkbox" id="case-densite" onchange="basculerDensite(this.checked)"> Vue compacte (une ligne par levier)
      </label>
    </div>
    <div class="classes-filtres" id="classes-filtres" role="group" aria-label="Filtrer les leviers par classe"></div>
    <div class="leviers-grille" id="leviers-grille"></div>
  </section>

  <section class="bloc" id="section-nuances">
    <h2>Nuances institutionnelles <span class="aide">ce que les curseurs ci-dessus changent au droit positif : seuils recalculés, délais de rigueur, fentes verrouillées, quatre indices et cinq strates. Calcul de la couche <code>simulateur/nuances_institutionnelles.py</code>, pas une opinion — chaque ligne rappelle l'article et la règle telle qu'elle est écrite.</span></h2>
    <div class="nuances-intro" id="nuances-resume">Le tableau se met à jour avec la simulation.</div>
    <div id="nuances-corps"><div class="carte">Chargement du tableau institutionnel…</div></div>
    <p class="nuances-intro"><button type="button" class="bouton" onclick="rafraichirNuances()">Recalculer maintenant</button>
      <span class="aide">Le bouton relance <code>POST /api/nuances</code> avec le vecteur complet ; la section suit déjà chaque simulation.</span></p>
  </section>

  <section class="bloc" id="section-verrous">
    <h2>Verrous : ce qui tient, ce qui lâche <span class="aide">les 38 règles de blocage du registre <code>simulateur/gouvernance_contrepouvoir.py</code>, partagées en trois colonnes — touchées par le vecteur, intactes, hors de portée d'un curseur. Une quatrième liste rappelle les réglages déplacés et, pour chacun, la catégorie de connaissance qu'il atteint. Rien n'est saisi ici : tout vient de <code>POST /api/nuances</code>.</span></h2>
    <div class="nuances-intro" id="verrous-resume">Le bloc suit la simulation des nuances.</div>
    <div id="verrous-corps"><div class="carte">Chargement de l'état des verrous…</div></div>
    <h3 style="margin:14px 0 6px">Réglages déplacés et ce qu'ils touchent</h3>
    <div id="reglages-corps" class="reglages-touches"></div>
  </section>

  <div class="chapitre" id="chapitre-verifier">
    <span class="chapitre-num" aria-hidden="true">4</span>
    <div class="chapitre-texte">
      <p class="chapitre-titre">Vérifier</p>
      <p class="chapitre-aide">Les objections et leurs réponses, les résultats détaillés, les sources, les licences — et l'audit à livre ouvert.</p>
    </div>
  </div>

  <section class="bloc" id="section-contradiction">
    <h2>Objections, concessions et réponses <span class="aide">le registre de la contradiction (<code>simulateur/contradiction.py</code>) : pour chaque mesure et pour chaque hypothèse du modèle, la meilleure version de la critique, ce que le dépôt concède, ce qu'il maintient, le fait qui le ferait changer d'avis, ses sources et son statut. La portée des leviers est déduite du catalogue (<code>simulateur/parametres.py</code>), jamais saisie. Rien n'est rédigé ici : tout vient de <code>GET /api/objections</code>.</span></h2>
    <div class="nuances-intro" id="contradiction-resume">Chargement du registre…</div>
    <p class="nuances-intro">
      <button type="button" class="bouton" onclick="chargerObjections('')">Tout le registre</button>
      <button type="button" class="bouton" onclick="chargerObjections('?famille=mesure')">Objections sur les mesures</button>
      <button type="button" class="bouton" onclick="chargerObjections('?famille=modele')">Objections sur le modèle</button>
      <button type="button" class="bouton" onclick="chargerObjections('?statut=partiellement_concedee')">Ce qui est concédé</button>
      <span class="aide">Les quatre boutons interrogent le même registre avec un filtre ; la page ne trie ni ne résume rien elle-même.</span>
    </p>
    <div id="objections-corps"><div class="carte">Chargement des objections…</div></div>
    <h3 style="margin:16px 0 6px">Les contre-modèles, et ce que le simulateur en dit</h3>
    <div id="contre-modeles-corps"></div>
  </section>

  <section class="bloc" id="section-resultats">
    <h2>Résultats année par année <span class="aide">tableau détaillé des 5 échelons</span></h2>
    <div class="defilable"><table id="results-table"></table></div>
  </section>

  <section class="bloc" id="section-trajectoires">
    <h2>Trajectoires clés <span class="aide">déficit, dette, taux OAT, tension sociale et confiance</span></h2>
    <div class="graphique" id="graphique-trajectoires">
      <svg class="svg-chart" id="svg-chart" viewBox="0 0 900 210" preserveAspectRatio="none"
        role="img" aria-label="Courbes des trajectoires clés : déficit, dette, taux OAT, tension sociale et confiance, année par année"></svg>
    </div>
  </section>

  <section class="bloc" id="section-domaines">
    <h2>Domaines d'action publique <span class="aide">score 0-100 (50 = aucun écart avec la référence) et indicateurs concrets</span></h2>
    <div class="grille domaines" id="domaines-grille"></div>
  </section>

  <section class="bloc" id="section-matrice">
    <h2>Matrice croisée levier × domaine <span class="aide">effet marginal de chaque levier actif, calculé par le modèle (différences finies) — <span id="matrice-fraicheur">en attente d'une simulation complète</span></span></h2>
    <div class="defilable"><table class="matrice" id="matrice-impacts"></table></div>
  </section>

  <section class="bloc" id="section-journal">
    <h2>Journal causal du moteur <span class="aide">rétroactions générées année par année</span></h2>
    <div class="journal" id="journal"></div>
  </section>

  <section class="bloc" id="section-provenance">
    <h2>Sources, licences et fraîcheur <span class="aide">ce que le simulateur sait, et ce qu'il ne sait pas</span></h2>
    <div class="provenance" id="provenance"></div>
  </section>

  <section class="bloc audit" id="section-audit">
    <h2>🔍 Audit &amp; traçabilité — à livre ouvert <span class="aide">pas de boîte noire : chaque chiffre, chaque formule, chaque seuil et chaque dynamique croisée est vérifiable à la source</span></h2>
    <p class="aide" style="margin-bottom:10px">
      Ce simulateur est un <b>modèle, pas une prophétie</b> : il rend explicites toutes ses
      hypothèses. Vous trouverez ici, de façon permanente et auditable : les sources officielles
      de chaque donnée d'entrée, la formule et la source de chaque indicateur des 20 domaines,
      le champ et la source de chacun des leviers du catalogue, le barème institutionnel complet des
      garde-fous, et la méthode des dynamiques croisées. Tout recoupement est possible.
    </p>
    <details id="audit-sources-details" open>
      <summary>1. Sources officielles des données d'entrée (recoupement possible)</summary>
      <div class="corps" id="audit-sources">chargement…</div>
    </details>
    <details id="audit-domaines-details">
      <summary>2. Les 20 domaines et leurs indicateurs : formule + source de chaque chiffre</summary>
      <div class="corps" id="audit-domaines">chargement…</div>
    </details>
    <details id="audit-leviers-details">
      <summary>3. Les leviers : champ budgétaire, effets déclarés et source</summary>
      <div class="corps" id="audit-leviers">chargement…</div>
    </details>
    <details id="audit-gardefous-details">
      <summary>4. Les 31 garde-fous : seuils, strates et sources institutionnelles</summary>
      <div class="corps" id="audit-gardefous">chargement…</div>
    </details>
    <details id="audit-methodes-details">
      <summary>5. Dynamiques croisées : comment les effets sont calculés (méthode complète)</summary>
      <div class="corps" id="audit-methodes">chargement…</div>
    </details>
    <div class="aide" style="margin-top:10px">
      <b>Bannière MRSC.</b> Outil open-source produit par son créateur pour l'intérêt général :
      utilisation, étude, modification et partage libres et gratuits ; nul ne peut s'en attribuer
      la paternité. Il porte l'ambition d'une vie meilleure et d'une gestion de la nation
      réellement faite « par le peuple, pour le peuple » — une prise de conscience politique par
      la base, citoyenne par citoyenne, citoyen par citoyen.
    </div>
  </section>

  <p class="pied">
    Projet citoyen open-source sous bannière MRSC — « gouvernement du peuple, par le peuple et pour le peuple »
    (Constitution du 4 octobre 1958, article 2). Les chiffres publics sont cités avec leur source ;
    les coefficients d'impact sont documentés dans chaque formule et modifiables.
    Créé par son auteur et mis gratuitement à disposition de toutes et tous : reproduction autorisée
    avec attribution, nul ne peut s'en attribuer le mérite.
    <span class="aide" id="version-interface">Interface v1.10.2 (2026-10-08) — calibration des dépenses du foyer par source publique ou données personnelles; données personnelles locales à la page.</span>
  </p>

  <p class="pied credit">
    © 2026 <a href="https://thejmimiia-code.github.io/MRSC/" target="_blank" rel="noopener noreferrer">Mouvement Représentatif de la Société Civile (M.R.S.C)</a>.
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
/* Les 5 classes de leviers (recettes, économies, dépenses, règles, monde) :
   fiches livrées par le catalogue, totaux recalculés depuis les flux du moteur
   à chaque simulation, et filtre courant. */
let CLASSES = {};
let ORDRE_CLASSES = [];
let DIVISEUR_MENAGES = null;
let CLASSES_DEFINITION = '';
let NOTE_SOLDE = '';
let CLASSES_ANNEES = [];
let CLASSES_REFERENCE = [];
//: Année lue dans la section des classes (0 = première). `null` = dernière
//: année simulée : c'est le régime de fin de mandature que l'on lit par défaut.
let CLASSES_ANNEE_INDEX = null;
let CLASSE_FILTRE = '';
let LEVIERS_MODIFIES_SEULS = false;
const FICHE_CLASSE_DEFAUT = {couleur:'var(--texte-dim)', couleur_html:'transparent',
                             motif:'uni', verdict:'', libelle:'', question:'', definition:''};
let NUANCES = null;   // dernier tableau des nuances institutionnelles
let MARCHES = null;
let ONGLET_STRATE_ACTIF = 'local';
let PROFIL_MENAGE = {
  salaire_brut_mensuel: 0, salaire_expose_smic_mensuel: 0,
  pension_brute_mensuelle: 0, autres_revenus_bruts_mensuels: 0,
  cotisations_hors_csg_mensuelles: 0, base_csg_crds_mensuelle: 0,
  taux_csg_crds_pct: 0, revenu_imposable_annuel: 0, parts_fiscales: 1,
  impot_ir_actuel_mensuel: 0, transferts_actuels_mensuels: 0,
  personnes_minima_sociaux: 0, beneficiaire_aide_logement: false,
  beneficiaire_cheque_energie: false, depenses_panier_total_mensuel: 0,
  depense_energie_mensuelle: 0, capital_restant_du: 0, duree_credit_restante_ans: 20,
  depense_alimentation: 0, depense_alcool_tabac: 0, depense_habillement: 0,
  depense_logement_energie: 0, depense_equipement: 0, depense_sante: 0,
  depense_transport: 0, depense_communication: 0, depense_loisirs: 0,
  depense_education: 0, depense_restaurants: 0, depense_autres: 0,
  portefeuille_exposition_eur: 0
};
const EXPOSITIONS_ACTEURS = {
  ir_0: 0, ir_11: 0, ir_30: 0, ir_41: 0, ir_45: 0,
  entreprises_cotees: 0, entreprises_non_cotees: 0, associations: 0,
  collectivites_locales: 0, communes: 0, epci_metropoles: 0, departements: 0,
  regions_ctu: 0, territoires_outre_mer: 0, organismes_publics: 0,
  etablissements_publics: 0, etablissements_prives: 0, elus_personnels: 0
};
const ACTEURS_EXPOSITION = [
  {cle:'ir_0', libelle:'Foyers fiscaux — tranche marginale 0 %'},
  {cle:'ir_11', libelle:'Foyers fiscaux — tranche marginale 11 %'},
  {cle:'ir_30', libelle:'Foyers fiscaux — tranche marginale 30 %'},
  {cle:'ir_41', libelle:'Foyers fiscaux — tranche marginale 41 %'},
  {cle:'ir_45', libelle:'Foyers fiscaux — tranche marginale 45 %'},
  {cle:'entreprises_cotees', libelle:'Entreprises cotées — exposition saisie'},
  {cle:'entreprises_non_cotees', libelle:'Entreprises non cotées — proxy de marché, hypothèse forte'},
  {cle:'associations', libelle:'Associations — trésorerie exposée saisie'},
  {cle:'collectivites_locales', libelle:'Collectivités locales — exposition non ventilée saisie'},
  {cle:'communes', libelle:'Communes / communes nouvelles — exposition saisie'},
  {cle:'epci_metropoles', libelle:'EPCI / métropoles / groupements — exposition saisie'},
  {cle:'departements', libelle:'Départements / collectivités départementales — exposition saisie'},
  {cle:'regions_ctu', libelle:'Régions / collectivités territoriales uniques — exposition saisie'},
  {cle:'territoires_outre_mer', libelle:'DROM / COM / Nouvelle-Calédonie — exposition saisie'},
  {cle:'organismes_publics', libelle:'État et organismes publics — exposition saisie'},
  {cle:'etablissements_publics', libelle:'Établissements publics — exposition saisie'},
  {cle:'etablissements_prives', libelle:'Établissements privés — exposition saisie'},
  {cle:'elus_personnels', libelle:'Élus — patrimoine personnel déclaré (pas budget du mandat)'}
];
const CATEGORIES_MENAGE = [
  {cle:'alimentation', libelle:'Alimentation et boissons non alcoolisées', ipch:'inflation_ipch_cp01'},
  {cle:'alcool_tabac', libelle:'Boissons alcoolisées, tabac et stupéfiants', ipch:'inflation_ipch_cp02'},
  {cle:'habillement', libelle:'Habillement et chaussures', ipch:'inflation_ipch_cp03'},
  {cle:'logement_energie', libelle:'Logement, eau, gaz, électricité et combustibles', ipch:'inflation_ipch_cp04'},
  {cle:'equipement', libelle:'Meubles et entretien du foyer', ipch:'inflation_ipch_cp05'},
  {cle:'sante', libelle:'Santé', ipch:'inflation_ipch_cp06'},
  {cle:'transport', libelle:'Transports', ipch:'inflation_ipch_cp07'},
  {cle:'communication', libelle:'Information et communication', ipch:'inflation_ipch_cp08'},
  {cle:'loisirs', libelle:'Loisirs, sport et culture', ipch:'inflation_ipch_cp09'},
  {cle:'education', libelle:'Services de l’enseignement', ipch:'inflation_ipch_cp10'},
  {cle:'restaurants', libelle:'Restaurants et hébergement', ipch:'inflation_ipch_cp11'},
  {cle:'autres', libelle:'Autres biens et services', ipch:'inflation_ipch_cp12'}
];
let STRESS_MARCHES = {};
let HORIZON_SIMULATION = 5;
function horizonCourant(){ return HORIZON_SIMULATION; }
function changerHorizon(valeur, relancer){
  HORIZON_SIMULATION = Number(valeur) === 10 ? 10 : 5;
  const select = document.getElementById('horizon-simulation');
  if (select) select.value = String(HORIZON_SIMULATION);
  const badge = document.getElementById('badge-horizon');
  if (badge) badge.textContent = HORIZON_SIMULATION === 10
    ? 'deux mandatures · 10 ans' : 'une mandature · 5 ans';
  if (relancer !== false && SORTIE) simuler(true);
}
//: Simulation précédente (paramètres envoyés + sortie) : c'est elle qui permet
//: d'afficher la conséquence de la DERNIÈRE modification, en direct.
let SIMULATION_PRECEDENTE = null;
//: Effets mesurés, par levier : affichés sous chaque curseur concerné.
let DERNIERES_PUCES = {};
//: Dernier mouvement de réglage : {cle, avant} — la « décision » à l'instant T
//: (position actuelle) par rapport à la position avant le dernier mouvement.
let MOUVEMENT = null;
//: Dernière réponse du conseiller temps réel (budget réel, sources, lecture).
let DERNIER_CONSEIL = null;
//: Leviers touchés par la dernière modification (mis en évidence).
let LEVIERS_MODIFIES = new Set();
//: Vue compacte : une ligne par levier, pour que le catalogue tienne à l'écran.
let VUE_COMPACTE = false;
//: Vrai pendant qu'un curseur est manipulé : on ne reconstruit alors pas la
//: grille, sinon le curseur serait remplacé sous les doigts de l'utilisateur.
let REGLAGE_EN_COURS = false;
//: Bulles explicatives chargées depuis /api/bulle (une par levier, à la demande).
let BULLES = {};
//: Levier dont la bulle est dépliée : elle s'ouvre **dans** la carte du levier,
//: jamais par-dessus, pour que tous les réglages restent visibles et actionnables.
let BULLE_OUVERTE = null;
//: Leviers déjà demandés au serveur (évite les appels répétés).
let BULLES_DEMANDEES = new Set();
//: Libellés des 20 domaines, repris du catalogue pour les bulles.
let LIBELLES_DOMAINES = {};

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
  const libelles = {live:'données live', reference:'référence datée du projet', mixte:'données mixtes'};
  return `<span class="pastille ${mode}">${libelles[mode] || mode}</span>`;
}

/* ── Chargement du catalogue (leviers + domaines) ───────────────────────── */
async function chargerCatalogue(){
  const reponse = await fetch('/api/catalogue');
  CATALOGUE = await reponse.json();
  PARAMS = Object.assign({}, CATALOGUE.parametres.defauts);
  chargerClasses();
  renderLeviers('');
  renderClasses();
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
    ['Nouveaux crédits habitat', fmt(c.taux_credit_immobilier_menages_pct, 2) + ' %',
      (c.provenance?.taux_credit_immobilier_menages_pct?.periode || 'moyenne mensuelle') + ' · hors assurance/frais'],
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
    const periode = info.periode ? ` · période ${info.periode}` : '';
    const collecte = info.date_collecte ? ` · collecté le ${info.date_collecte}` : '';
    const qualite = info.qualite && info.qualite_code ? ` · qualité : ${info.qualite}` : '';
    const frequence = info.frequence ? `<br><span class="texte-dim">Mise à jour : ${info.frequence}</span>` : '';
    const note = info.note ? `<br><span class="texte-dim">${info.note}</span>` : '';
    return `<div><b>${info.libelle}</b> : ${statut}${periode}${collecte}${qualite} · ${info.source}
      ${info.url ? ` · <a href="${info.url}" target="_blank" rel="noopener">source</a>` : ''}
      ${info.licence ? ` · <i>${info.licence}</i>` : ''}${frequence}${note}</div>`;
  }).join('');
  const complementaires = Object.values((CONTEXTE.contexte && CONTEXTE.contexte.series_complementaires) || {});
  const blocComplementaire = complementaires.length
    ? '<div style="margin-top:10px"><b>Séries complémentaires collectées</b> (non utilisées pour le calibrage,'
      + ' conservées pour information) :<br>' + complementaires.map(info =>
        `${info.libelle} : ${fmt(info.valeur, 2)} ${info.unite} (${info.periode || '—'}; collecté le ${info.date_collecte || '—'})`
        + `${info.qualite_code ? ` · ${info.qualite}` : ''} · ${info.frequence || 'fréquence selon la source'}`
        + `${info.url ? ` — <a href="${info.url}" target="_blank" rel="noopener">${info.fournisseur}</a>` : ` — ${info.fournisseur}`}`
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
/* ── Vues par strate : trajectoire comparée et profil ménage local ─────── */
const CLES_ONGLETS_STRATE = ['local','national','europe','mondial','geopolitique','menages','boursier'];
let ANNEE_MENAGE = 0;
// Le budget du foyer peut rester basé sur les saisies par poste ou sur une
// répartition publique INSEE appliquée à un total personnel, sans écraser les saisies.
let MODE_CALIBRAGE_MENAGE = 'personnel';
function contenuOngletStrate(cle, donnees){
  switch (cle){
    case 'local': return afficherLocal(donnees);
    case 'national': return afficherNational(donnees);
    case 'europe': return afficherEurope(donnees);
    case 'mondial': return afficherMonde(donnees);
    case 'geopolitique': return afficherGeopolitique(donnees);
    case 'menages': return afficherMenages(donnees);
    case 'boursier': return contenuBoursier();
    default: return '';
  }
}
function rendreOngletStrate(cle, donnees){
  // Rendu à la demande. Les sept vues (tableaux, profil de ménage, cotations)
  // représentaient l'essentiel du travail d'affichage à chaque simulation ;
  // reconstruire six panneaux que personne ne regarde faisait perdre ce temps
  // à chaque mouvement de curseur. On ne construit que l'onglet visible, et on
  // le (re)construit au moment où il devient visible.
  const panneau = document.getElementById(`panneau-strate-${cle}`);
  if (!panneau) return;
  panneau.innerHTML = contenuOngletStrate(cle, donnees) || '';
  if (cle === 'menages') rendreResultatsMenage(donnees, ANNEE_MENAGE);
  if (cle === 'boursier') renderResultatsBoursiers();
}
function afficherOngletStrate(cle){
  if (!CLES_ONGLETS_STRATE.includes(cle)) return;
  ONGLET_STRATE_ACTIF = cle;
  CLES_ONGLETS_STRATE.forEach(nom => {
    const bouton = document.getElementById(`tab-strate-${nom}`);
    const panneau = document.getElementById(`panneau-strate-${nom}`);
    if (bouton){
      bouton.setAttribute('aria-selected', nom === cle ? 'true' : 'false');
      bouton.className = nom === cle ? 'actif' : '';
      bouton.tabIndex = nom === cle ? 0 : -1;
    }
    if (panneau) panneau.className = nom === cle ? 'panneau-strate actif' : 'panneau-strate';
  });
  if (SORTIE) rendreOngletStrate(cle, SORTIE);
}
function afficherNombre(valeur, precision, unite){
  return `${fmt(valeur, precision)}${unite ? ` ${unite}` : ''}`;
}
function sourceObservatoire(info){
  if (!info) return '';
  const source = echapperTexte(info.source || info.libelle || 'Source publique');
  const url = info.url || info.page_source;
  const lien = url && String(url).startsWith('https://')
    ? ` · <a href="${echapperTexte(url)}" target="_blank" rel="noopener">consulter</a>` : '';
  const periode = info.periode ? ` · période observée : ${echapperTexte(info.periode)}` : '';
  const publication = info.publication_le
    ? ` · publié le ${echapperTexte(info.publication_le)}` : '';
  const collecte = info.collecte_le ? ` · collecté le ${echapperTexte(info.collecte_le)}` : '';
  const frequence = info.frequence ? ` · ${echapperTexte(info.frequence)}` : '';
  const statut = info.statut ? ` · statut : ${echapperTexte(info.statut)}` : '';
  const qualite = info.qualite
    ? ` · qualité : ${echapperTexte(info.qualite)}`
    : (info.qualite_code ? ` · code qualité source : ${echapperTexte(info.qualite_code)}` : '');
  const note = info.note ? `<br>${echapperTexte(info.note)}` : '';
  return `<div class="note-source"><b>${source}</b>${lien}${periode}${publication}${collecte}${frequence}${statut}${qualite}${note}</div>`;
}
function tableauComparatif(etapes, references, indicateurs){
  if (!Array.isArray(etapes) || !etapes.length) return '<p class="aide">Lancez une simulation pour afficher les trajectoires.</p>';
  const lignes = [];
  etapes.forEach((etape, index) => {
    const ref = (references || [])[index] || {};
    indicateurs.forEach(spec => {
      const scenario = etape[spec.cle];
      const reference = ref[spec.cle];
      const numerique = typeof scenario === 'number' && typeof reference === 'number';
      const delta = numerique ? scenario - reference : null;
      let comparaison = '—';
      if (typeof scenario === 'boolean' || typeof reference === 'boolean'){
        comparaison = `${scenario ? 'oui' : 'non'} / ${reference ? 'oui' : 'non'}`;
      } else if (typeof scenario === 'string' || typeof reference === 'string'){
        comparaison = `${echapperTexte(scenario ?? '—')} / ${echapperTexte(reference ?? '—')}`;
      } else if (numerique){
        comparaison = `${fmt(delta, spec.precision ?? 1)} ${spec.unite || ''}`.trim();
      }
      const classe = numerique && spec.sens
        ? (delta * spec.sens > 0.00001 ? 'delta-pos' : (delta * spec.sens < -0.00001 ? 'delta-neg' : '')) : '';
      const scenarioTexte = typeof scenario === 'boolean' ? (scenario ? 'oui' : 'non')
        : (typeof scenario === 'number' ? afficherNombre(scenario, spec.precision ?? 1, spec.unite) : echapperTexte(scenario ?? '—'));
      const referenceTexte = typeof reference === 'boolean' ? (reference ? 'oui' : 'non')
        : (typeof reference === 'number' ? afficherNombre(reference, spec.precision ?? 1, spec.unite) : echapperTexte(reference ?? '—'));
      lignes.push(`<tr><td>${echapperTexte(spec.libelle)}</td><td>Année ${echapperTexte(etape.annee ?? index + 1)}</td>
        <td>${referenceTexte}</td><td>${scenarioTexte}</td><td class="${classe}">${comparaison}</td></tr>`);
    });
  });
  return `<div class="tableau-strate"><table><thead><tr><th>Indicateur</th><th>Horizon</th>
    <th>Référence</th><th>Scénario</th><th>Écart scénario − référence</th></tr></thead><tbody>${lignes.join('')}</tbody></table></div>`;
}
function carteObservation(libelle, valeur, unite, note){
  return `<div class="carte metric"><div class="libelle">${echapperTexte(libelle)}</div>
    <div class="valeur">${echapperTexte(valeur)}</div><div class="delta neutre">${echapperTexte(note || unite || '')}</div></div>`;
}
function afficherLocal(donnees){
  const o = CONTEXTE?.observatoire || {};
  const local = o.finances_locales || {};
  const geo = o.acteurs_et_territoires || {};
  const niveaux = local.croissance_fonctionnement_pct || [];
  const couverture = (geo.couverture_territoriale || []).map(x=>`<tr><td>${echapperTexte(x.niveau)}</td><td>${echapperTexte(x.couverture)}</td></tr>`).join('');
  const tableauLocal = niveaux.length ? `<div class="tableau-strate"><table><thead><tr>
    <th>Niveau territorial</th><th>Évolution des dépenses de fonctionnement</th><th>Évolution des recettes de fonctionnement</th>
    </tr></thead><tbody>${niveaux.map(x => `<tr><td>${echapperTexte(x.libelle)}</td>
      <td>${fmt(x.depenses,1)} %</td><td>${fmt(x.recettes,1)} %</td></tr>`).join('')}</tbody></table></div>`
    : '<p class="aide">Repères financiers locaux indisponibles.</p>';
  return `<p class="strate-intro">Le moteur fournit un indicateur local agrégé; les budgets d'une commune, d'un EPCI, d'un département et d'une région ne sont pas simulés séparément. Les évolutions ci-dessous sont des observations nationales, pas une projection de votre collectivité.</p>
    <div class="grille metrics">${carteObservation('Croissance consolidée des dépenses locales', `${fmt(local.croissance_consolidee_depenses_pct,1)} %`, '', `comptes 2025 · collecte ${local.collecte_le || '—'}`)}</div>
    <h3 class="strate-sous-titre">Finances locales observées, par niveau (2025)</h3>${tableauLocal}
    ${sourceObservatoire(local)}
    <h3 class="strate-sous-titre">Échelles territoriales couvertes et non couvertes</h3>
    <div class="tableau-strate"><table><thead><tr><th>Échelle</th><th>État des données et de la simulation</th></tr></thead><tbody>${couverture||'<tr><td colspan="2">Taxonomie non disponible.</td></tr>'}</tbody></table></div>
    <div class="note-source">Les budgets OFGL restent des agrégats nationaux. Hameaux, quartiers, villages et budgets de collectivités individuelles ne sont pas simulés; les chiffres DROM/COM ne sont pas ventilés ici. « Métropole » est classée dans les EPCI, sans la confondre avec la France métropolitaine.</div>
    <h3 class="strate-sous-titre">Indicateurs du moteur — trajectoire annuelle</h3>
    ${tableauComparatif(donnees.etapes, donnees.etapes_reference, [
      {cle:'tension_sociale_locale',libelle:'Tension sociale locale',unite:'/100',precision:1,sens:-1},
      {cle:'qualite_services_proximite',libelle:'Qualité des services de proximité',unite:'/100',precision:1,sens:1},
      {cle:'produit_taxe_fonciere_mde',libelle:'Produit de taxe foncière — proxy national',unite:'Md€',precision:2,sens:0}
    ])}
    <div class="note-source">Périmètre : France entière dans le moteur. Pas de ventilation départementale, communale ou DROM/COM, pas de fiscalité propre à une collectivité et pas de consolidation des budgets individuels. Les budgets principaux publiés par l'OFGL ne doivent pas être additionnés aux comptes consolidés.</div>`;
}
function tableauFluxNational(donnees){
  const flux=(donnees.flux_annuels||[]).slice(-1)[0]||{}, annee=flux.annee||donnees.horizon||'—';
  const recettes=[
    ['rec_ir_haut_mde','Impôt sur le revenu — tranche supérieure'],
    ['rec_csg_mde','CSG/CRDS'],['rec_tva_hausse_mde','TVA'],
    ['rec_flat_tax_suppression_mde','Prélèvement forfaitaire unique'],
    ['rec_isf_mde','Impôt sur la fortune (levier du modèle)'],
    ['rec_succession_mde','Droits de succession'],['rec_taxe_carbone_mde','Taxe carbone']
  ];
  const depenses=[
    ['education_mde','Éducation'],['sante_mde','Santé / hôpital'],['minima_sociaux_mde','Minima sociaux'],
    ['apl_mde','Aides au logement'],['logement_social_mde','Logement social'],['climat_mde','Climat'],
    ['recherche_mde','Recherche'],['justice_mde','Justice'],['effectifs_etat_mde','Effectifs de l’État'],
    ['effectifs_securite_mde','Sécurité'],['territoires_mde','Territoires'],['relocalisations_mde','Relocalisations']
  ];
  const rangees=(items,sens)=>items.map(([cle,label])=>{
    const valeur=Number(flux[cle]||0),classe=Math.abs(valeur)<0.005?'':(valeur*sens>0?'delta-pos':'delta-neg');
    return `<tr><td>${echapperTexte(label)}</td><td class="${classe}">${valeur>0?'+':''}${fmt(valeur,3)} Md€</td></tr>`;
  }).join('');
  const totalRecettes=Number(flux.recettes_nouvelles_mde||0),totalDepenses=Number(flux.depenses_nouvelles_mde||0);
  return `<h3 class="strate-sous-titre">Sources des variations budgétaires simulées — année ${echapperTexte(annee)}</h3>
    <p class="strate-intro">Flux annuels directs des leviers activés, en Md€ par rapport à la référence sans levier; ils ne sont pas les recettes/dépenses totales de la France. Les postes listés sont des lignes du modèle, pas une ventilation comptable complète.</p>
    <div class="tableau-strate"><table><thead><tr><th>Source / poste budgétaire</th><th>Variation directe</th></tr></thead><tbody>
      <tr><th colspan="2">Recettes fiscales simulées</th></tr>${rangees(recettes,1)}
      <tr><td><b>Total des recettes nouvelles modélisées</b></td><td class="${totalRecettes>=0?'delta-pos':'delta-neg'}"><b>${totalRecettes>0?'+':''}${fmt(totalRecettes,3)} Md€</b></td></tr>
      <tr><th colspan="2">Dépenses publiques simulées</th></tr>${rangees(depenses,-1)}
      <tr><td><b>Total des dépenses nouvelles modélisées</b></td><td class="${totalDepenses>0?'delta-neg':'delta-pos'}"><b>${totalDepenses>0?'+':''}${fmt(totalDepenses,3)} Md€</b></td></tr>
      <tr><td><b>Solde net des leviers</b></td><td class="${totalRecettes-totalDepenses>=0?'delta-pos':'delta-neg'}"><b>${fmt(totalRecettes-totalDepenses,3)} Md€</b></td></tr>
    </tbody></table></div>`;
}
function afficherNational(donnees){
  const n = CONTEXTE?.observatoire?.comptes_nationaux || {};
  const observations = `<div class="grille metrics">${carteObservation('Croissance PIB en volume, 2025', `${fmt(n.croissance_pib_volume_pct,1)} %`, '', 'INSEE · comptes annuels')}
    ${carteObservation('Déficit public, 2025', `${fmt(n.deficit_public_pct_pib,1)} % du PIB`, '', 'INSEE · administrations publiques')}
    ${carteObservation('Dette publique, 2025', `${fmt(n.dette_publique_fin_annee_mde,1)} Md€`, '', `${fmt(n.dette_publique_pct_pib,1)} % du PIB · INSEE`)}</div>`;
  return `<p class="strate-intro">Les comptes observés décrivent l'ensemble des administrations publiques; la trajectoire de simulation représente les mécanismes du modèle, pas une ventilation comptable exhaustive des ministères, opérateurs et organismes.</p>
    ${observations}
    <div class="note-source">Déficit APUL observé : ${fmt(n.deficit_apul_mde,1)} Md€; dont collectivités locales ${fmt(n.deficit_collectivites_locales_mde,1)} Md€. Les APUL incluent aussi les ODAL. Écart de référence conservé : l'INSEE publie une dette 2025 de ${fmt(n.dette_publique_pct_pib,1)} % du PIB; Eurostat fournit une série révisable différente.</div>
    ${sourceObservatoire(n)}
    <h3 class="strate-sous-titre">Comptes nationaux simulés — scénario / référence</h3>
    ${tableauComparatif(donnees.etapes, donnees.etapes_reference, [
      {cle:'pib_nominal_mde',libelle:'PIB nominal',unite:'Md€',precision:1,sens:1},
      {cle:'deficit_nominal_mde',libelle:'Déficit nominal',unite:'Md€',precision:1,sens:-1},
      {cle:'ratio_deficit_pib',libelle:'Déficit / PIB',unite:'%',precision:2,sens:-1},
      {cle:'dette_nominale_mde',libelle:'Dette nominale',unite:'Md€',precision:1,sens:-1},
      {cle:'ratio_dette_pib',libelle:'Dette / PIB',unite:'%',precision:2,sens:-1},
      {cle:'recettes_publiques_totales_mde',libelle:'Recettes publiques totales',unite:'Md€',precision:1,sens:0},
      {cle:'depenses_publiques_totales_mde',libelle:'Dépenses publiques totales',unite:'Md€',precision:1,sens:0},
      {cle:'charge_dette_mde',libelle:'Charge de la dette',unite:'Md€',precision:1,sens:-1}
    ])}
    ${tableauFluxNational(donnees)}
    <div class="note-source">Ne sont pas détaillés ici tous les crédits budgétaires, missions, comptes spéciaux, recettes fiscales et sociales, budgets annexes ou établissements. Les chiffres observés et les leviers simulés sont des périmètres différents. Une hausse de dépense est affichée comme un coût budgétaire, sans jugement sur son utilité sociale.</div>`;
}
function afficherEurope(donnees){
  const e = CONTEXTE?.observatoire?.ipch_europe || {};
  const taux = CONTEXTE?.contexte?.taux_bce_depot;
  return `<p class="strate-intro">Repères réels de l'Union/zone euro distincts des conséquences de scénario. Les décisions de la BCE et les règles européennes ne sont pas modifiées par un curseur du modèle.</p>
    <div class="grille metrics">${carteObservation('IPCH France — estimation flash', `${fmt(e.france_pct,1)} %`, '', `${e.periode || '—'} · qualité ${e.qualite_code || 'non marquée'}`)}
      ${carteObservation('IPCH zone euro 21', `${fmt(e.zone_euro_21_pct,1)} %`, '', `${e.periode || '—'} · estimation flash`)}
      ${carteObservation('Taux BCE — facilité de dépôt', `${fmt(taux,2)} %`, '', 'taux observé, exogène dans cette simulation')}</div>
    ${sourceObservatoire(e)}
    <h3 class="strate-sous-titre">Indicateurs européens simulés</h3>
    ${tableauComparatif(donnees.etapes, donnees.etapes_reference, [
      {cle:'statut_pde_europe',libelle:'Procédure de déficit excessif — proxy du moteur',unite:'',precision:0,sens:-1},
      {cle:'bouclier_tpi_actif',libelle:'Bouclier TPI — état dans le moteur',unite:'',precision:0,sens:0},
      {cle:'sanction_financiere_ue',libelle:'Sanction financière UE — proxy du moteur',unite:'',precision:0,sens:-1}
    ])}
    <div class="note-source">Le statut PDE/TPI affiché est un indicateur simplifié du moteur, pas une décision ni une annonce de la Commission ou de la BCE. L'IPCH par catégorie est publié mensuellement; la flash peut être révisée à la publication complète.</div>`;
}
function afficherMonde(donnees){
  const c = CONTEXTE?.contexte || {};
  return `<p class="strate-intro">Les cotations ci-dessous sont les repères de départ disponibles au serveur. Les chocs futurs sont produits par le modèle; ils ne sont pas des cours à terme ni des prévisions de marché.</p>
    <div class="grille metrics">${carteObservation('OAT France 10 ans', `${fmt(c.taux_oat_10ans,2)} %`, '', c.provenance?.taux_oat_10ans?.periode || 'source dans la provenance')}
      ${carteObservation('Crédit habitat moyen — nouveaux prêts', `${fmt(c.taux_credit_immobilier_menages_pct,2)} %`, '', c.provenance?.taux_credit_immobilier_menages_pct?.periode || 'mensuel')}
      ${carteObservation('EUR/USD', `${fmt(c.eur_usd,4)}`, '', c.provenance?.eur_usd?.periode || 'dernier cours publié')}
      ${carteObservation('Brent', `${fmt(c.brent_usd,2)} $/baril`, '', c.provenance?.brent_usd?.periode || 'dernier cours publié')}
      ${carteObservation('Inflation France', `${fmt(c.inflation_pct,1)} %`, '', c.provenance?.inflation_pct?.periode || 'période dans la provenance')}</div>
    <h3 class="strate-sous-titre">Trajectoire mondiale du moteur</h3>
    ${tableauComparatif(donnees.etapes, donnees.etapes_reference, [
      {cle:'taux_oat_pct',libelle:'OAT 10 ans',unite:'%',precision:2,sens:-1},
      {cle:'spread_bund_bps',libelle:'Spread OAT–Bund',unite:'bps',precision:0,sens:-1},
      {cle:'taux_credit_immobilier_menages',libelle:'Taux nouveaux crédits habitat — proxy',unite:'%',precision:2,sens:-1},
      {cle:'taux_credit_pme',libelle:'Taux crédit PME — proxy',unite:'%',precision:2,sens:-1},
      {cle:'cours_petrole_usd',libelle:'Brent',unite:'$/bbl',precision:1,sens:0},
      {cle:'taux_change_eur_usd',libelle:'EUR/USD',unite:'$',precision:3,sens:0},
      {cle:'facture_energetique_mde',libelle:'Facture énergétique nette',unite:'Md€',precision:1,sens:-1},
      {cle:'inflation_globale_pct',libelle:'Inflation globale modélisée',unite:'%',precision:2,sens:-1}
    ])}
    <div id="resume-bourse-monde"></div>
    <div class="note-source">La transmission de l'OAT au crédit habitat est modélisée à 1 pour 1 autour du taux mensuel BCE/Banque de France; c'est une hypothèse de pass-through, pas une estimation économétrique complète. Les chocs boursiers ne sont pas encore une entrée du PIB, de l'emploi ou du budget public dans ce moteur.</div>`;
}
function afficherGeopolitique(donnees){
  return `<p class="strate-intro">Indicateurs de stress géopolitique du modèle. Les probabilités et indices sont des conventions de stress-test; ils ne constituent ni une évaluation du renseignement ni une probabilité officielle d'événement.</p>
    ${tableauComparatif(donnees.etapes, donnees.etapes_reference, [
      {cle:'indice_tension_geopolitique',libelle:'Indice de tension géopolitique',unite:'/100',precision:1,sens:-1},
      {cle:'probabilite_escalade_mondiale_pct',libelle:'Probabilité d’escalade — proxy',unite:'%',precision:1,sens:-1},
      {cle:'risque_nucleaire_tactique_pct',libelle:'Risque nucléaire tactique — proxy',unite:'%',precision:1,sens:-1},
      {cle:'disponibilite_semiconducteurs_pct',libelle:'Disponibilité des semi-conducteurs',unite:'%',precision:1,sens:1},
      {cle:'effort_defense_pct_pib',libelle:'Effort de défense',unite:'% PIB',precision:2,sens:0},
      {cle:'depenses_defense_mde',libelle:'Dépenses de défense',unite:'Md€',precision:1,sens:0},
      {cle:'chokepoints_sous_tension',libelle:'Points de passage sous tension',unite:'',precision:0,sens:-1},
      {cle:'stocks_strategiques_petrole_jours',libelle:'Stocks stratégiques pétroliers',unite:'jours',precision:0,sens:1}
    ])}
    <div class="note-source">Les conflits, sanctions, alliances, risques de rupture et conséquences humanitaires ne peuvent pas être ramenés à un score prédictif unique. Les leviers de défense ne modélisent pas l'ensemble des engagements internationaux.</div>`;
}

/* Profil fiscal/ménage — saisie éphémère locale, jamais envoyée à l'API. */
function partsPanierNational(){
  const panier = CONTEXTE?.observatoire?.menages?.panier_national_2025?.part_depense_finale_pct || [];
  const parCle = Object.create(null);
  panier.forEach(ligne => {
    const cle = String(ligne?.cle || '');
    const part = Number(ligne?.part);
    if (CATEGORIES_MENAGE.some(item => item.cle === cle) && Number.isFinite(part) && part > 0){
      parCle[cle] = part;
    }
  });
  const somme = CATEGORIES_MENAGE.reduce((total, item) => total + (parCle[item.cle] || 0), 0);
  return {parCle, somme};
}
function depenseBaseProfil(item){
  const cle = typeof item === 'string' ? item : item?.cle;
  if (!cle) return 0;
  if (MODE_CALIBRAGE_MENAGE !== 'insee'){
    const saisie = Number(PROFIL_MENAGE[`depense_${cle}`] ?? 0);
    return Number.isFinite(saisie) ? Math.max(0, saisie) : 0;
  }
  const distribution = partsPanierNational();
  const part = Number(distribution.parCle[cle] || 0);
  const total = Number(PROFIL_MENAGE.depenses_panier_total_mensuel || 0);
  if (!distribution.somme || !Number.isFinite(total) || total <= 0 || part <= 0) return 0;
  return total * part / distribution.somme;
}
function partPanierNationalPct(item){
  const cle = typeof item === 'string' ? item : item?.cle;
  const distribution = partsPanierNational();
  return distribution.somme > 0 ? Number(distribution.parCle[cle] || 0) / distribution.somme * 100 : null;
}
function categoriePanierProfil(cle){
  return CATEGORIES_MENAGE.find(item => `depense_${item.cle}` === cle) || null;
}
function valeurChampProfil(cle){
  if (cle === 'depenses_panier_total_mensuel' && MODE_CALIBRAGE_MENAGE === 'personnel'){
    return totalPanierProfil();
  }
  const categorie = categoriePanierProfil(cle);
  return categorie ? depenseBaseProfil(categorie) : (PROFIL_MENAGE[cle] ?? 0);
}
function champProfil(cle, libelle, unite, step, minimum){
  const valeur = valeurChampProfil(cle);
  const lectureSeule = (cle === 'depenses_panier_total_mensuel' && MODE_CALIBRAGE_MENAGE === 'personnel')
    || (categoriePanierProfil(cle) && MODE_CALIBRAGE_MENAGE === 'insee');
  const nombre = Number(valeur);
  const valeurAffichee = Number.isFinite(nombre)
    ? (lectureSeule ? nombre.toFixed(2) : String(valeur)) : '0';
  return `<label class="champ-profil">${echapperTexte(libelle)}${unite ? ` (${echapperTexte(unite)})` : ''}
    <input type="number" min="${minimum ?? 0}" step="${step ?? 1}" value="${echapperTexte(valeurAffichee)}"
      ${lectureSeule ? 'readonly aria-readonly="true"' : ''}
      data-profil="${echapperTexte(cle)}" onchange="modifierProfilMenage(this)"></label>`;
}
function caseProfil(cle, libelle){
  return `<label class="champ-profil"><span>${echapperTexte(libelle)}</span>
    <input type="checkbox" data-profil="${echapperTexte(cle)}" ${PROFIL_MENAGE[cle] ? 'checked' : ''}
      onchange="modifierProfilMenage(this)"></label>`;
}
function totalPanierProfil(){
  return CATEGORIES_MENAGE.reduce((somme, item) => {
    const valeur = Number(PROFIL_MENAGE[`depense_${item.cle}`] || 0);
    return somme + (Number.isFinite(valeur) ? Math.max(0, valeur) : 0);
  }, 0);
}
function modifierModeCalibrageMenage(mode){
  const choisi = mode === 'insee' && partsPanierNational().somme > 0 ? 'insee' : 'personnel';
  MODE_CALIBRAGE_MENAGE = choisi;
  const select = document.getElementById('mode-calibrage-menage');
  if (select) select.value = choisi;
  renderResultatsMenage(SORTIE);
}
function modifierProfilMenage(champ){
  const cle = champ?.dataset?.profil;
  if (!cle) return;
  const entreePanier = categoriePanierProfil(cle);
  if ((cle === 'depenses_panier_total_mensuel' && MODE_CALIBRAGE_MENAGE === 'personnel')
      || (entreePanier && MODE_CALIBRAGE_MENAGE === 'insee')) return;
  if (champ.type === 'checkbox'){
    PROFIL_MENAGE[cle] = !!champ.checked;
  } else {
    const valeur = Number(champ.value);
    PROFIL_MENAGE[cle] = Number.isFinite(valeur) ? Math.max(0, valeur) : 0;
  }
  if (entreePanier) PROFIL_MENAGE.depenses_panier_total_mensuel = totalPanierProfil();
  renderResultatsMenage(SORTIE);
}
function activerCalibrageINSEE(){
  modifierModeCalibrageMenage('insee');
}
function impotSelonBareme(revenuAnnuel, parts, hausseTrancheSuperieure){
  const tranches = CONTEXTE?.observatoire?.menages?.bareme_ir_2026?.tranches || [];
  const revenu = Math.max(0, Number(revenuAnnuel) || 0);
  const nbParts = Math.max(0.5, Number(parts) || 1);
  const quotient = revenu / nbParts;
  let impotsParPart = 0;
  tranches.forEach(tranche => {
    const bas = Number(tranche.borne_basse) || 0;
    const haut = tranche.borne_haute === null ? quotient : Number(tranche.borne_haute);
    const base = Math.max(0, Math.min(quotient, haut) - bas);
    let taux = Number(tranche.taux_pct) || 0;
    if (tranche.cle === 'ir_45') taux += Number(hausseTrancheSuperieure) || 0;
    impotsParPart += base * Math.max(0, taux) / 100;
  });
  return impotsParPart * nbParts;
}
function facteurPrixCategorie(item, etape, etapeRef, index){
  const complements = CONTEXTE?.contexte?.series_complementaires || {};
  const observation = complements[item.ipch];
  const tauxObserve = Number.isFinite(Number(observation?.valeur))
    ? Number(observation.valeur) : Number(CONTEXTE?.contexte?.inflation_pct || 0);
  const inflationDepart = Number(CONTEXTE?.contexte?.inflation_pct || 0);
  const base = Number(etape?.inflation_globale_pct ?? inflationDepart);
  const ref = Number(etapeRef?.inflation_globale_pct ?? inflationDepart);
  const tauxScenario = Math.max(-10, Math.min(30, tauxObserve + base - inflationDepart));
  const tauxReference = Math.max(-10, Math.min(30, tauxObserve + ref - inflationDepart));
  const exponent = Math.max(1, Number(etape?.annee || index + 1));
  return {scenario:Math.pow(1+tauxScenario/100,exponent),reference:Math.pow(1+tauxReference/100,exponent),observation,tauxScenario,tauxReference};
}
function mensualiteEmprunt(capital, tauxAnnuelPct, dureeAns){
  const montant=Math.max(0,Number(capital)||0), duree=Math.max(1,Number(dureeAns)||1);
  const mensualites=duree*12, taux=Math.max(0,Number(tauxAnnuelPct)||0)/1200;
  if (!montant) return 0;
  if (!taux) return montant/mensualites;
  return montant*taux/(1-Math.pow(1+taux,-mensualites));
}
function projectionMenage(donnees,index,reference){
  const p=PROFIL_MENAGE, etapes=reference?donnees.etapes_reference:donnees.etapes;
  const etape=etapes?.[index]||{}, flux=(reference?donnees.flux_reference:donnees.flux_annuels)?.[index]||{};
  const params=donnees.parametres||{}, annee=Math.max(1,Number(etape.annee||index+1));
  const smic=reference?0:Number(params.smic_revalorisation||0), retraite=reference?0:Number(params.revalorisation_retraites||0);
  const hausseSalaire=Number(p.salaire_expose_smic_mensuel||0)*(Math.pow(1+smic/100,annee)-1);
  const haussePension=Number(p.pension_brute_mensuelle||0)*(Math.pow(1+retraite/100,annee)-1);
  const salaire=Number(p.salaire_brut_mensuel||0)+hausseSalaire, pension=Number(p.pension_brute_mensuelle||0)+haussePension;
  const autres=Number(p.autres_revenus_bruts_mensuels||0), baseCsg=Number(p.base_csg_crds_mensuelle||0)+hausseSalaire+haussePension;
  const tauxCsg=Number(p.taux_csg_crds_pct||0)+(reference?0:Number(params.csg_crds_hausse||0));
  const csg=baseCsg*tauxCsg/100;
  const tauxCotisations=Number(p.salaire_brut_mensuel||0)>0?Number(p.cotisations_hors_csg_mensuelles||0)/Number(p.salaire_brut_mensuel):0;
  const cotisations=Number(p.cotisations_hors_csg_mensuelles||0)+hausseSalaire*tauxCotisations;
  const revenuImposableBase=Number(p.revenu_imposable_annuel||0);
  const revenuImposableProjection=revenuImposableBase+(hausseSalaire+haussePension)*12;
  const hausseIr=reference?0:Number(params.ir_tranche_superieure||0), irSaisi=Number(p.impot_ir_actuel_mensuel||0);
  const impotBase=irSaisi>0?irSaisi:impotSelonBareme(revenuImposableBase,p.parts_fiscales,0)/12;
  const impot=impotBase+(impotSelonBareme(revenuImposableProjection,p.parts_fiscales,hausseIr)-impotSelonBareme(revenuImposableBase,p.parts_fiscales,0))/12;
  const o=CONTEXTE?.observatoire?.menages||{}, minimaNb=Number(o.transferts?.minima_sociaux?.beneficiaires_millions||0)*1e6;
  const aplNb=Number(o.transferts?.aides_logement?.beneficiaires_millions||0)*1e6, chequeNb=Number(o.transferts?.cheque_energie?.beneficiaires_millions||0)*1e6;
  const minimaDelta=Number(p.personnes_minima_sociaux||0)&&minimaNb?Number(flux['levier:revalorisation_minima_sociaux']||0)*1e9/minimaNb/12*Number(p.personnes_minima_sociaux):0;
  const aplDelta=p.beneficiaire_aide_logement&&aplNb?Number(flux['levier:aide_logement']||0)*1e9/aplNb/12:0;
  const chequeDelta=p.beneficiaire_cheque_energie&&chequeNb?Number(flux['levier:cheque_energie']||0)*1e9/chequeNb/12:0;
  const aidesDirectes=reference?0:minimaDelta+aplDelta+chequeDelta;
  const transferts=Number(p.transferts_actuels_mensuels||0)+aidesDirectes;
  const revenuDisponible=salaire+pension+autres-cotisations-csg-impot+transferts;
  const etapeRef=donnees.etapes_reference?.[index]||{};
  const depenses=CATEGORIES_MENAGE.reduce((total,item)=>{
    const facteurs=facteurPrixCategorie(item,etape,etapeRef,index);
    return total+depenseBaseProfil(item)*(reference?facteurs.reference:facteurs.scenario);
  },0);
  const depensesEnergie=Number(p.depense_energie_mensuelle||0);
  const economieTvaEnergie=!reference&&Number(params.tva_energie_5_5||0)>=0.5?depensesEnergie*(0.145/1.20):0;
  const tauxHabitat=Number(etape.taux_credit_immobilier_menages??CONTEXTE?.contexte?.taux_credit_immobilier_menages_pct??0);
  const mensualiteCredit=mensualiteEmprunt(p.capital_restant_du,tauxHabitat,p.duree_credit_restante_ans);
  return {salaire,pension,autres,cotisations,csg,impot,transferts,aidesDirectes,revenuDisponible:revenuDisponible+economieTvaEnergie,
    depenses,reste:revenuDisponible+economieTvaEnergie-depenses,economieTvaEnergie,hausseSalaire,haussePension,tauxHabitat,mensualiteCredit,flux,etape};
}
function rendreResultatsMenage(donnees,index){
  const zone=document.getElementById('menage-resultats');
  if (!zone) return;
  if (!donnees||!donnees.etapes?.length){zone.innerHTML='<p class="aide">Lancez une simulation pour comparer scénario et référence.</p>';return;}
  const i=Math.max(0,Math.min(donnees.etapes.length-1,Number(index??ANNEE_MENAGE)||0)); ANNEE_MENAGE=i;
  const scenario=projectionMenage(donnees,i,false), reference=projectionMenage(donnees,i,true);
  const rows=[
    ['Revenus salariaux bruts',reference.salaire,scenario.salaire],['Pensions brutes',reference.pension,scenario.pension],
    ['Autres revenus bruts déclarés',reference.autres,scenario.autres],['Cotisations hors CSG/CRDS',-reference.cotisations,-scenario.cotisations],
    ['CSG/CRDS',-reference.csg,-scenario.csg],['Impôt sur le revenu',-reference.impot,-scenario.impot],
    ['Transferts et aides déclarés/imputés',reference.transferts,scenario.transferts],
    ['Économie TVA énergie imputable (si dépense saisie)',reference.economieTvaEnergie,scenario.economieTvaEnergie],
    ['Revenu disponible mensuel estimé',reference.revenuDisponible,scenario.revenuDisponible],
    [MODE_CALIBRAGE_MENAGE === 'insee'
      ? 'Panier calibré — parts INSEE 2025 appliquées au total saisi'
      : 'Panier de consommation — données personnelles par poste',
      reference.depenses,scenario.depenses],
    ['Reste après panier calibré',reference.reste,scenario.reste]
  ];
  const tableBudget=`<div class="tableau-strate"><table><thead><tr><th>Poste mensuel</th><th>Référence (€)</th><th>Scénario (€)</th><th>Écart (€)</th></tr></thead><tbody>${rows.map(([label,ref,val])=>{const delta=val-ref,cls=delta>0.005?'delta-pos':(delta< -0.005?'delta-neg':'');return `<tr><td>${echapperTexte(label)}</td><td>${fmt(ref,2)} €</td><td>${fmt(val,2)} €</td><td class="${cls}">${fmt(delta,2)} €</td></tr>`;}).join('')}</tbody></table></div>`;
  const categories=CATEGORIES_MENAGE.map(item=>{
    const base=depenseBaseProfil(item), facteursS=facteurPrixCategorie(item,scenario.etape,donnees.etapes_reference[i]||{},i);
    const facteursR=facteurPrixCategorie(item,donnees.etapes_reference[i]||{},donnees.etapes_reference[i]||{},i);
    const montantS=base*facteursS.scenario,montantR=base*facteursR.reference,delta=montantS-montantR;
    const observation=CONTEXTE?.contexte?.series_complementaires?.[item.ipch];
    const valeurIpch=observation?`${fmt(observation.valeur,1)} % · ${observation.periode||'période inconnue'}${observation.qualite_code?` · ${observation.qualite||observation.qualite_code}`:''}`:`${fmt(CONTEXTE?.contexte?.inflation_pct,1)} % · inflation globale de repli`;
    const baseQualifiee=MODE_CALIBRAGE_MENAGE==='insee'
      ? `${fmt(partPanierNationalPct(item),1)} % · parts INSEE renormalisées`
      : 'montant personnel saisi';
    return `<tr><td>${echapperTexte(item.libelle)}</td><td>${fmt(base,2)} €<br><small>${echapperTexte(baseQualifiee)}</small></td><td>${echapperTexte(valeurIpch)}</td><td>${fmt(montantR,2)} €</td><td>${fmt(montantS,2)} €</td><td class="${delta>0?'delta-neg':(delta<0?'delta-pos':'')}">${fmt(delta,2)} €</td></tr>`;
  }).join('');
  const dflow=(key)=>Number(scenario.flux[`levier:${key}`]||0)-Number(reference.flux[`levier:${key}`]||0);
  const stress=calculerStressMarche().stressPct, plusValue=Number(PROFIL_MENAGE.portefeuille_exposition_eur||0)*stress/100;
  const noteCalibrage=MODE_CALIBRAGE_MENAGE==='insee'
    ? '<div class="note-source"><b>Calibrage actif :</b> le total mensuel saisi par vous est réparti selon la structure de consommation INSEE 2025, normalisée sur les parts positives. Les montants par poste sont calculés pour cette simulation et ne remplacent pas vos saisies personnelles, conservées dans cette page.</div>'
    : '<div class="note-source"><b>Calibrage actif :</b> les montants de consommation par poste viennent de vos saisies personnelles. Les repères publics qualifiés restent visibles pour comparaison et ne sont pas utilisés comme budget individuel.</div>';
  zone.innerHTML=`<p class="strate-intro">Profil saisi par vous dans ce navigateur. Il n'est jamais transmis à l'API, inclus dans un lien de partage ou enregistré après rechargement. Résultats mensuels, nominaux et exploratoires; ils ne remplacent ni une fiche de paie, ni une liquidation d'impôt, ni une décision d'éligibilité.</p>
    ${noteCalibrage}
    <h3 class="strate-sous-titre">Profil modifiable (valeurs déclarées, sans moyenne de ménage inventée)</h3>
    <div class="grille-profil">
      ${champProfil('salaire_brut_mensuel','Salaires bruts du foyer','€/mois',10)}${champProfil('salaire_expose_smic_mensuel','Part de salaire réellement exposée à une hausse du SMIC','€/mois',10)}
      ${champProfil('pension_brute_mensuelle','Pensions brutes','€/mois',10)}${champProfil('autres_revenus_bruts_mensuels','Autres revenus bruts','€/mois',10)}
      ${champProfil('cotisations_hors_csg_mensuelles','Cotisations hors CSG/CRDS','€/mois',10)}${champProfil('base_csg_crds_mensuelle','Assiette CSG/CRDS déclarée','€/mois',10)}
      ${champProfil('taux_csg_crds_pct','Taux actuel CSG/CRDS du profil','%',0.1)}${champProfil('revenu_imposable_annuel','Revenu net imposable du foyer','€/an',100)}
      ${champProfil('parts_fiscales','Parts de quotient familial','parts',0.5,0.5)}${champProfil('impot_ir_actuel_mensuel','Impôt sur le revenu actuellement payé (si connu)','€/mois',10)}
      ${champProfil('transferts_actuels_mensuels','Aides/transferts actuellement reçus (si connus)','€/mois',10)}${champProfil('personnes_minima_sociaux','Personnes allocataires de minima dans le foyer','personnes',1)}
      ${caseProfil('beneficiaire_aide_logement','Je déclare percevoir une aide au logement')}${caseProfil('beneficiaire_cheque_energie','Je déclare être éligible au chèque énergie (repère 2023)')}
      ${champProfil('depenses_panier_total_mensuel',MODE_CALIBRAGE_MENAGE==='insee'?'Total mensuel de dépenses personnelles à répartir':'Total des catégories personnelles (calculé)','€/mois',10)}${champProfil('depense_energie_mensuelle','Dépense d’énergie éligible à TVA réduite','€/mois',10)}
      ${champProfil('capital_restant_du','Capital immobilier restant dû','€',1000)}${champProfil('duree_credit_restante_ans','Durée restante du prêt','années',1,1)}
      ${champProfil('portefeuille_exposition_eur','Exposition boursière personnelle saisie','€',100)}
    </div>
    <div class="profil-actions"><button type="button" onclick="activerCalibrageINSEE()">Utiliser les parts INSEE sans écraser mes saisies</button><span class="aide">Répartition des parts positives, normalisée à 100 %; correction territoriale tourisme −1,3 point exclue. Revenus, aides, énergie et capital de prêt restent vos valeurs personnelles.</span></div>
    <h3 class="strate-sous-titre">Dépenses de consommation par catégorie</h3>
    <div class="tableau-strate"><table><thead><tr><th>Poste</th><th>Base du profil sélectionnée</th><th>IPCH observé / repli</th><th>Référence projetée</th><th>Scénario projeté</th><th>Écart de prix simulé</th></tr></thead><tbody>${categories}</tbody></table></div>
    <div class="grille-profil">${CATEGORIES_MENAGE.map(item=>champProfil(`depense_${item.cle}`,item.libelle,'€/mois',10)).join('')}</div>
    ${tableBudget}
    <div class="note-source"><b>Effets directs :</b> SMIC (${fmt(scenario.hausseSalaire-reference.hausseSalaire,2)} €/mois sur la part saisie); retraites; CSG/CRDS sur assiette/taux saisis; hausse du taux de la tranche supérieure de l'IR, appliquée au barème 2026; minima, aide logement et chèque énergie répartis à partir des flux annuels nationaux seulement si l'éligibilité est déclarée. Flux du moteur (minima / logement / chèque) : ${fmt(dflow('revalorisation_minima_sociaux'),3)} / ${fmt(dflow('aide_logement'),3)} / ${fmt(dflow('cheque_energie'),3)} Md€/an.</div>
    <div class="note-source"><b>Effets indirects/hypothèses :</b> prix par poste = IPCH mensuel du poste + écart d'inflation globale du scénario, composé annuellement; au besoin inflation globale en repli. Prêt immobilier : échéance théorique d'un prêt à taux fixe amortissable; ne recalcule pas un contrat déjà signé et reste à part du panier pour éviter un double compte. Pas de droits APL/minima automatiques, plafonnement du quotient familial, décote/crédits d'impôt, cotisations légales exactes, TVA générale ou fiscalité patrimoniale.</div>
    <div class="note-source">Les données INSEE de consommation et de pouvoir d'achat sont agrégées; comptes annuels révisables. DREES 2024, CNAF 2025 et chèque énergie 2023 (repère ancien) servent uniquement de dénominateurs proportionnels. Elles ne représentent pas le budget réel de votre foyer.</div>
    <div class="grille metrics">${carteObservation('Mensualité théorique — référence',`${fmt(reference.mensualiteCredit,2)} €/mois`,'',`${fmt(reference.tauxHabitat,2)} % · hors assurance`)}${carteObservation('Mensualité théorique — scénario',`${fmt(scenario.mensualiteCredit,2)} €/mois`,'',`${fmt(scenario.tauxHabitat,2)} % · capital ${fmt(PROFIL_MENAGE.capital_restant_du,0)} €`)}${carteObservation('Plus/moins-value boursière brute',`${plusValue>=0?'+':''}${fmt(plusValue,2)} €`,'',`stress pondéré ${fmt(stress,2)} % · hors impôt/frais`)}</div>
    ${sourceObservatoire(CONTEXTE?.observatoire?.menages?.bareme_ir_2026)}`;
}
function afficherMenages(donnees){
  const horizon=donnees.etapes?.length||5;
  ANNEE_MENAGE=Math.min(ANNEE_MENAGE,Math.max(0,horizon-1));
  const options=Array.from({length:horizon},(_,i)=>`<option value="${i}" ${i===ANNEE_MENAGE?'selected':''}>Année ${i+1}</option>`).join('');
  const panier=CONTEXTE?.observatoire?.menages?.panier_national_2025;
  const distribution=partsPanierNational();
  if(!distribution.somme) MODE_CALIBRAGE_MENAGE='personnel';
  const disponible=distribution.somme>0;
  const statut=panier?.statut||'statut de la source non renseigné';
  const sourcePanier=panier?sourceObservatoire(panier)
    :'<div class="note-source">Repère INSEE 2025 indisponible; aucune valeur n’est substituée.</div>';
  return `<div class="profil-actions"><label class="select-horizon">Horizon du budget de profil <select id="annee-menage" onchange="ANNEE_MENAGE=Number(this.value);renderResultatsMenage(SORTIE)">${options}</select></label><span class="pastille">Simulation de profil, pas budget observé</span></div>
    <div class="grille-profil"><label class="champ-profil">Calibrage des dépenses du foyer
      <select id="mode-calibrage-menage" aria-label="Calibrage des dépenses du foyer" onchange="modifierModeCalibrageMenage(this.value)">
        <option value="personnel" ${MODE_CALIBRAGE_MENAGE==='personnel'?'selected':''}>Mes données personnelles saisies par poste</option>
        <option value="insee" ${MODE_CALIBRAGE_MENAGE==='insee'?'selected':''} ${disponible?'':'disabled'}>Structure INSEE 2025 appliquée à mon total · ${echapperTexte(statut)}</option>
      </select></label></div>
    <p class="strate-intro">Les chiffres publics restent accompagnés de leur source, période et statut. Le mode INSEE applique uniquement la structure agrégée de consommation à votre total mensuel saisi; il ne fabrique ni revenu, ni droit individuel. Le mode personnel utilise vos montants par poste. Le calibrage ne change pas la simulation macro.</p>
    <h3 class="strate-sous-titre">Repère public associé au calibrage</h3>${sourcePanier}
    ${disponible?'':'<div class="alerte">Structure publique absente ou inutilisable : le mode INSEE est désactivé. Aucune part n’est inventée.</div>'}
    <div id="menage-resultats"></div>`;
}
function renderResultatsMenage(donnees){rendreResultatsMenage(donnees,ANNEE_MENAGE);}

/* Bourse : cotations distinctes du moteur macro, stress-tests bruts par acteur. */
function initialiserStressMarches(indices){
  const liste=indices||MARCHES?.indices||[], poidsDefaut=liste.length?100/liste.length:0;
  liste.forEach(x=>{if(!STRESS_MARCHES[x.cle])STRESS_MARCHES[x.cle]={actif:true,poids:poidsDefaut,choc:0};});
}
function calculerStressMarche(){
  const indices=MARCHES?.indices||[];initialiserStressMarches(indices);
  let poidsTotal=0,choc=0,poidsCours=0,variation=0;
  indices.forEach(item=>{const r=STRESS_MARCHES[item.cle]||{};if(!r.actif||Number(r.poids)<=0)return;const w=Number(r.poids);poidsTotal+=w;choc+=w*Number(r.choc||0);if(item.variation_jour_pct!==null&&item.variation_jour_pct!==undefined&&Number.isFinite(Number(item.variation_jour_pct))){poidsCours+=w;variation+=w*Number(item.variation_jour_pct);}});
  return {stressPct:poidsTotal?choc/poidsTotal:0,variationPct:poidsCours?variation/poidsCours:null,couverturePoids:poidsTotal?poidsCours/poidsTotal*100:0,poidsTotal};
}
function contenuBoursier(){
  const indices=MARCHES?.indices||[];initialiserStressMarches(indices);
  const avertissement=MARCHES?.avertissement||'Cotations fournies par un flux tiers; vérifiez fraîcheur et conditions de réutilisation.';
  const rows=indices.map(item=>{
    const s=STRESS_MARCHES[item.cle]||{actif:true,poids:0,choc:0};
    const statut=item.statut==='observé'?'cours horodaté du jour (retard non vérifiable)':(item.statut==='dernier cours'?'dernier cours — fermeture ou retard possible':(item.statut==='cache'?'cache horodaté':(item.statut==='ancien'?'cours ancien / périmé':'indisponible')));
    let date='—';
    if(item.horodatage_cours_utc){
      const fuseau=String(item.fuseau_horaire_place||'UTC');
      let localePlace='';
      try{localePlace=new Date(item.horodatage_cours_utc).toLocaleString('fr-FR',{timeZone:fuseau});}catch(_){localePlace=new Date(item.horodatage_cours_utc).toISOString();}
      date=`${localePlace} (${fuseau}) · UTC ${item.horodatage_cours_utc}`;
    }
    const releve=item.horodatage_releve_utc?new Date(item.horodatage_releve_utc).toLocaleString('fr-FR',{timeZone:'Europe/Paris'})+' (Paris)':'date de collecte inconnue';
    const etatPlace=item.etat_place||'Fraîcheur ou calendrier de place non vérifié.';
    const url=typeof item.page_officielle==='string'&&item.page_officielle.startsWith('https://')?echapperTexte(item.page_officielle):'';
    return `<tr class="marches-table-row"><td><label><input type="checkbox" ${s.actif?'checked':''} aria-label="Inclure ${echapperTexte(item.nom)}" onchange="modifierStressMarche('${echapperTexte(item.cle)}','actif',this.checked,this)"> ${echapperTexte(item.nom)}</label><br><small>${echapperTexte(item.region)} · ${url?`<a href="${url}" target="_blank" rel="noopener">${echapperTexte(item.place)}</a>`:echapperTexte(item.place)}</small></td><td>${item.cours===null||item.cours===undefined?'—':fmt(item.cours,2)} ${echapperTexte(item.devise||'')}</td><td class="${Number(item.variation_jour_pct)>0?'positif':(Number(item.variation_jour_pct)<0?'negatif':'')}">${item.variation_jour_pct===null||item.variation_jour_pct===undefined?'—':`${Number(item.variation_jour_pct)>0?'+':''}${fmt(item.variation_jour_pct,2)} %`}</td><td>${echapperTexte(date)}<br><small>${echapperTexte(statut)} · ${echapperTexte(etatPlace)}<br>collecté ${echapperTexte(releve)}</small></td><td><input class="range-bourse" type="range" min="-50" max="50" step="0.5" value="${echapperTexte(s.choc)}" aria-label="Choc hypothétique ${echapperTexte(item.nom)}" oninput="modifierStressMarche('${echapperTexte(item.cle)}','choc',this.value,this)"><output>${fmt(s.choc,1)} %</output></td><td><input class="saisie-euros" type="number" min="0" max="100" step="0.1" value="${Number(s.poids||0).toFixed(1)}" aria-label="Poids de ${echapperTexte(item.nom)}" oninput="modifierStressMarche('${echapperTexte(item.cle)}','poids',this.value,this)"> %</td></tr>`;
  }).join('');
  const statutCollecte=MARCHES?.statut_collecte||'en attente';
  const instant=MARCHES?.date_interrogation_utc?`interrogation serveur ${new Date(MARCHES.date_interrogation_utc).toLocaleString('fr-FR',{timeZone:'Europe/Paris'})} (Paris)`:'aucune collecte demandée';
  const o=CONTEXTE?.observatoire||{}, bareme=o.menages?.bareme_ir_2026||{};
  const tranches=(bareme.tranches||[]).map(t=>`<tr><td>${echapperTexte(t.libelle)}</td><td>${fmt(t.taux_pct,0)} %</td><td><input class="saisie-euros" type="number" min="0" step="100" value="${Number(EXPOSITIONS_ACTEURS[t.cle]||0).toFixed(0)}" aria-label="Exposition ${echapperTexte(t.libelle)}" oninput="modifierExpositionActeur('${echapperTexte(t.cle)}',this.value)"></td><td id="pnl-acteur-${echapperTexte(t.cle)}">—</td></tr>`).join('');
  const acteurs=ACTEURS_EXPOSITION.filter(x=>!x.cle.startsWith('ir_')).map(x=>`<tr><td>${echapperTexte(x.libelle)}</td><td>Statut variable; aucun régime fiscal déduit</td><td><input class="saisie-euros" type="number" min="0" step="100" value="${Number(EXPOSITIONS_ACTEURS[x.cle]||0).toFixed(0)}" aria-label="Exposition ${echapperTexte(x.libelle)}" oninput="modifierExpositionActeur('${echapperTexte(x.cle)}',this.value)"></td><td id="pnl-acteur-${echapperTexte(x.cle)}">—</td></tr>`).join('');
  return `<p class="strate-intro">Flux à la demande sur 13 indices représentatifs, non l’ensemble des sociétés cotées ni tous les marchés. Les indices ne sont pas des titres directement détenus; cours possiblement différés et devises locales.</p>
    <div class="marches-actions"><button type="button" class="primaire" id="btn-rafraichir-marches" onclick="rafraichirMarches(false)">⟳ Rafraîchir les cotations</button><span class="pastille" id="statut-cotations">${echapperTexte(statutCollecte)} · ${echapperTexte(instant)} (Paris)</span><span class="pastille">Refresh manuel; aucune promesse de temps réel</span></div>
    <div class="tableau-strate bourse-table"><table><thead><tr><th>Indice / place</th><th>Dernier niveau</th><th>Variation publiée séance</th><th>Horodatage du cours</th><th>Choc hypothétique</th><th>Poids composite</th></tr></thead><tbody>${rows||'<tr><td colspan="6">Catalogue en cours de chargement…</td></tr>'}</tbody></table></div>
    <div class="note-source"><b>Source :</b> ${echapperTexte(MARCHES?.fournisseur||'Yahoo Finance, via le serveur')}. ${echapperTexte(avertissement)} Liens vers les propriétaires/places dans la première colonne; vérifier fraîcheur, retard et licence avant réutilisation.</div>
    <h3 class="strate-sous-titre">Plus/moins-values brutes par tranche fiscale et acteur</h3><p class="strate-intro">Saisissez une exposition indicative en euros. Le stress composite applique une moyenne pondérée des variations hypothétiques sélectionnées; il ne multiplie pas ces montants par la population et ne connaît pas les portefeuilles réels. Les catégories territoriales sont des cases de saisie, pas des comptes observés; évitez de compter une même exposition à la fois dans « collectivités locales » et dans ses sous-niveaux (commune, EPCI, département, région ou outre-mer).</p>
    <div class="tableau-strate"><table><thead><tr><th>Groupe déclaré</th><th>Repère fiscal/juridique</th><th>Exposition saisie (€)</th><th>P/L séance publié / stress (€)</th></tr></thead><tbody>${tranches}${acteurs}</tbody></table></div><div id="resultats-bourse"></div>
    <div class="note-source">Barème d'IR pour revenus 2025 déclarés en 2026, par part : ${bareme.url?`<a href="${echapperTexte(bareme.url)}" target="_blank" rel="noopener">${echapperTexte(bareme.source)}</a>`:'source non disponible'}. Les tranches marginales ne sont pas des catégories de patrimoine. Associations, entreprises, collectivités et établissements ont des statuts différents; aucun placement réel n'est attribué automatiquement. Les élus ne constituent pas une caisse publique séparée.</div>
    ${sourceObservatoire(o.acteurs_et_territoires)}
    <div class="note-source"><b>Non calculé :</b> dividendes, frais, conversion des devises, fiscalité PEA/CTO/assurance-vie, moins-values reportables, titres non cotés, réserves d'associations, placements des organismes publics. Ces chocs n'affectent pas encore le PIB, l'emploi, les recettes fiscales agrégées ou la dette du moteur macro.</div>`;
}
function renderResultatsBoursiers(){
  const zone=document.getElementById('resultats-bourse');if(!zone)return;
  const r=calculerStressMarche(), pct=r.stressPct, daily=r.variationPct;
  const lignes=ACTEURS_EXPOSITION.map(acteur=>{
    const expo=Number(EXPOSITIONS_ACTEURS[acteur.cle]||0), pStress=expo*pct/100, pJour=daily===null?null:expo*daily/100;
    const cellule=document.getElementById(`pnl-acteur-${acteur.cle}`);
    if(cellule){const cls=pJour>0?'delta-pos':(pJour<0?'delta-neg':'');const clsS=pStress>0?'delta-pos':(pStress<0?'delta-neg':'');cellule.innerHTML=`<span class="${cls}">${pJour===null?'—':`${pJour>0?'+':''}${fmt(pJour,2)} €`}</span><br><small>stress : <span class="${clsS}">${pStress>0?'+':''}${fmt(pStress,2)} €</span></small>`;}
    return {pStress,pJour};
  });
  const totalStress=lignes.reduce((s,x)=>s+x.pStress,0),totalJour=daily===null?null:lignes.reduce((s,x)=>s+(x.pJour||0),0);
  zone.innerHTML=`<div class="grille metrics">${carteObservation('Stress composite choisi',`${pct>0?'+':''}${fmt(pct,2)} %`,'','moyenne pondérée des indices cochés')}${carteObservation('Variation séance publiée',daily===null?'—':`${daily>0?'+':''}${fmt(daily,2)} %`,'',`${fmt(r.couverturePoids,0)} % du poids sélectionné avec variation disponible`)}${carteObservation('P/L brut total — stress',`${totalStress>0?'+':''}${fmt(totalStress,2)} €`,'','expositions saisies seulement')}${carteObservation('P/L brut total — séance',totalJour===null?'—':`${totalJour>0?'+':''}${fmt(totalJour,2)} €`,'','hors devises, frais et impôts')}</div>`;
  renderResumeBourseMonde();renderResultatsMenage(SORTIE);
}
function modifierStressMarche(cle,champ,valeur,element){
  if(!STRESS_MARCHES[cle])STRESS_MARCHES[cle]={actif:true,poids:0,choc:0};
  if(champ==='actif')STRESS_MARCHES[cle].actif=!!valeur;else STRESS_MARCHES[cle][champ]=Number(valeur)||0;
  if(champ==='choc'&&element?.nextElementSibling)element.nextElementSibling.textContent=`${fmt(valeur,1)} %`;
  renderResultatsBoursiers();
}
function modifierExpositionActeur(cle,valeur){if(Object.prototype.hasOwnProperty.call(EXPOSITIONS_ACTEURS,cle))EXPOSITIONS_ACTEURS[cle]=Math.max(0,Number(valeur)||0);renderResultatsBoursiers();}
function renderResumeBourseMonde(){
  const zone=document.getElementById('resume-bourse-monde');if(!zone)return;const r=calculerStressMarche();
  zone.innerHTML=`<div class="note-source"><b>Marchés actions (panneau latéral, pas dans le PIB du moteur) :</b> stress ${r.stressPct>0?'+':''}${fmt(r.stressPct,2)} %; variation publiée ${r.variationPct===null?'—':`${r.variationPct>0?'+':''}${fmt(r.variationPct,2)} %`}. Les chocs modifient seulement les plus/moins-values des expositions saisies.</div>`;
}
async function rafraichirMarches(silencieux){
  const bouton=document.getElementById('btn-rafraichir-marches'),status=document.getElementById('statut-cotations');
  if(bouton){bouton.disabled=true;bouton.textContent='Interrogation des places…';}
  if(status&&!silencieux)status.textContent='Demande de cotations en cours…';
  try{
    const reponse=await fetch('/api/marches?refresh=1'),charge=await reponse.json();
    if(!reponse.ok)throw new Error(charge.error||`HTTP ${reponse.status}`);
    MARCHES=charge;initialiserStressMarches(MARCHES.indices||[]);renderOngletsStrates(SORTIE);
    if(status&&!silencieux)status.textContent=`${charge.statut_collecte||'relevé'} · ${new Date().toLocaleString('fr-FR')}`;
  }catch(erreur){
    if(status)status.textContent=`Cotation non joignable : ${String(erreur).slice(0,140)}`;
    if(!MARCHES)MARCHES={indices:[],statut_collecte:'indisponible',avertissement:'Le serveur ne peut joindre le fournisseur; aucun cours n’est inventé.'};
  }finally{if(bouton){bouton.disabled=false;bouton.textContent='⟳ Rafraîchir les cotations';}renderOngletsStrates(SORTIE);}
}
function renderOngletsStrates(donnees){
  // Seul l'onglet ouvert est (re)construit : voir `rendreOngletStrate`.
  if(!donnees)return;
  rendreOngletStrate(ONGLET_STRATE_ACTIF, donnees);
}

function extraireEurostat(charge, chemin){
  const valeur = charge.value || {};
  const cles = Object.keys(valeur);
  if (!cles.length) return null;
  let cle = chemin && valeur[chemin] !== undefined ? chemin : cles[cles.length - 1];
  let periode = null;
  try {
    const temps = charge.dimension.time.category.index;
    periode = Object.keys(temps).find(code => Number(temps[code]) === Number(cle)) || null;
  } catch (erreur) { periode = null; }
  let qualite = null;
  try {
    const statuts = charge.status || {};
    qualite = Array.isArray(statuts) ? statuts[Number(cle)] : statuts[cle];
    if (qualite && typeof qualite === 'object') qualite = null;
  } catch (erreur) { qualite = null; }
  return {valeur: Number(valeur[cle]), periode: periode,
          qualite_code: qualite ? String(qualite) : null};
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
        // `interroger()` côté serveur renvoie déjà les unités canoniques ; ici,
        // le fetch direct reçoit l'unité brute de l'API (M€ Eurostat, etc.).
        lectures[cle] = {cle: cle,
                         valeur: lecture.valeur * Number(indicateur.conversion || 1),
                         periode: lecture.periode,
                         fournisseur: source.fournisseur, url: source.url, statut: 'live',
                         qualite_code: lecture.qualite_code || null,
                         horodatage: new Date().toISOString()};
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
                             statut: lecture.statut === 'live' ? 'live' : 'reference',
                             qualite_code: lecture.qualite_code || null,
                             horodatage: lecture.horodatage || new Date().toISOString()};
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
  await rafraichirMarches(true);
  bouton.disabled = false;
  bouton.textContent = succes > 0
    ? `Rafraîchir les données (${succes} séries mises à jour)`
    : 'Rafraîchir les données (aucune source joignable)';
  if (SORTIE) simuler(false);
}

/* ══ Les 5 classes de leviers : lire un budget sans être économiste ════════
   Le classement est décidé côté moteur (`simulateur/classes_leviers.py`) et
   livré avec le catalogue : la page ne reclasse rien elle-même, elle affiche.
   Les montants par classe sont recalculés ici à partir des flux annuels du
   moteur (`flux_annuels`, clés `levier:<cle>`) : ce sont donc les montants du
   modèle, montée en charge comprise, jamais une addition faite à la main.
   Règle de lisibilité : couleur + symbole + libellé + motif. La couleur seule
   ne porte jamais l'information. */
function chargerClasses(){
  const bloc = (CATALOGUE && CATALOGUE.parametres && CATALOGUE.parametres.classes) || null;
  if (!bloc){ CLASSES = {}; ORDRE_CLASSES = []; return; }
  CLASSES = {};
  (bloc.classes || []).forEach(fiche => { CLASSES[fiche.cle] = fiche; });
  ORDRE_CLASSES = bloc.ordre || Object.keys(CLASSES);
  DIVISEUR_MENAGES = bloc.diviseur_menages || null;
  CLASSES_DEFINITION = bloc.definition || '';
  NOTE_SOLDE = bloc.note_solde || '';
}
function classeDe(cle){
  const levier = levierParCle(cle);
  return (levier && levier.classe) || null;
}
function ficheClasse(cle){
  const nom = CLASSES[cle] ? cle : classeDe(cle);
  return (nom && CLASSES[nom]) || null;
}
function ficheDe(cle){
  return ficheClasse(cle) || FICHE_CLASSE_DEFAUT;
}
/* Un montant en milliards ne dit rien ; en euros par ménage, si. La conversion
   affiche toujours son diviseur et son statut de vérification. */
function eurosParMenage(montantMde){
  const diviseur = (DIVISEUR_MENAGES && DIVISEUR_MENAGES.valeur) || 30000000;
  return (Number(montantMde) || 0) * 1e9 / diviseur;
}
/* Le facteur d'un levier n'est un montant en euros que pour les trois classes
   monétaires : un dollar de baril (classe « monde ») ou un drapeau 0/1 ne se
   convertit pas en euros par ménage. La page ne le fait jamais. */
function montantUnitairePossible(levier){
  if (!levier) return false;
  if (!(levier.classe === 'recettes' || levier.classe === 'economies' || levier.classe === 'depenses')) return false;
  return Number(levier.facteur) !== 0;
}
function fmtMenage(montantMde){
  const valeur = eurosParMenage(montantMde);
  const arrondi = Math.abs(valeur) >= 100 ? fmt(valeur, 0) : fmt(valeur, 1);
  return `${arrondi} €/ménage/an`;
}
function statutDiviseur(){
  return (DIVISEUR_MENAGES && DIVISEUR_MENAGES.statut) || 'ordre de grandeur';
}
function rampeHtml(profil, couleur){
  // Montée en charge déclarée au catalogue : une réforme ne produit pas ses
  // effets dès la première année. Cinq barres, une par année.
  const valeurs = (profil && profil.length ? profil : [0.4, 0.7, 0.9, 1, 1]);
  const maxi = Math.max(...valeurs, 0.01);
  const barres = valeurs.map((valeur, index) =>
    `<i title="année ${index + 1} : ${Math.round(valeur * 100)} % du régime" `
    + `style="height:${Math.max(3, Math.round(20 * valeur / maxi))}px"></i>`).join('');
  return `<span class="rampe" style="--couleur-classe:${couleur || 'var(--texte-dim)'}" `
    + `role="img" aria-label="montée en charge sur cinq ans : ${valeurs.map(v => Math.round(v * 100) + ' %').join(', ')}">`
    + `${barres}</span>`;
}
/* Un montant signé, écrit comme on le lit : « +12,3 » ou « −12,3 ». Le signe
   est porté par le chiffre, pas par la phrase : un plan d'austérité a des
   montants négatifs dans la classe « dépenses », et les afficher en positif
   ferait passer une coupe pour une dépense. */
function fmtSigne(montantMde, precision){
  const valeur = Number(montantMde) || 0;
  const chiffres = fmt(Math.abs(valeur), precision === undefined ? 2 : precision);
  return `${valeur < 0 ? '−' : '+'}${chiffres}`;
}
function sensDUnMontant(montantMde){
  if (Math.abs(Number(montantMde) || 0) < 1e-9) return 'nul';
  return Number(montantMde) > 0 ? 'positif' : 'negatif';
}
function rampeSerieHtml(valeurs, couleur, unite){
  // Même dessin, mais avec les montants réellement calculés par le moteur,
  // une barre par année simulée : on voit d'un coup d'œil si la mesure monte
  // ou retombe, ce qu'aucun total annuel ne montre.
  const serie = (valeurs && valeurs.length) ? valeurs : [0];
  const maxi = Math.max(...serie.map(valeur => Math.abs(Number(valeur) || 0)), 0.01);
  const etiquette = serie.map((valeur, index) =>
    `année ${index + 1} : ${fmt(valeur, 2)} ${unite || 'Md€/an'}`).join(', ');
  const barres = serie.map((valeur, index) =>
    `<i title="${etiquette.split(', ')[index]}" `
    + `style="height:${Math.max(3, Math.round(20 * Math.abs(Number(valeur) || 0) / maxi))}px"></i>`).join('');
  return `<span class="rampe" style="--couleur-classe:${couleur || 'var(--texte-dim)'}" `
    + `role="img" aria-label="${etiquette}">${barres}</span>`;
}
function pastilleClasse(cle, compacte){
  const fiche = ficheClasse(cle);
  if (!fiche) return '';
  const texte = compacte ? fiche.libelle_court : fiche.libelle;
  return `<span class="classe-pastille motif-${fiche.motif}" `
    + `style="--couleur-classe:${fiche.couleur};--fond-classe:${fiche.couleur_html};`
    + `--teinte-motif:${fiche.couleur_html}" `
    + `data-aide="<b>Classe : ${fiche.libelle}</b>${fiche.question} ${fiche.verdict}. ${fiche.definition}">`
    + `<span class="symbole" aria-hidden="true">${fiche.symbole}</span>${echapperTexte(texte)}</span>`;
}
/* Totaux par classe : le moteur les calcule (`classes_annuelles`), la page les
   affiche. Elle ne reclasse aucun levier et n'additionne aucun montant
   elle-même — ce que dit le solde est donc exactement ce que dit le modèle. */
function calculerClasses(donnees){
  CLASSES_ANNEES = (donnees && donnees.classes_annuelles) || [];
  CLASSES_REFERENCE = (donnees && donnees.classes_reference) || [];
  // L'année lue est choisie par le lecteur : elle survit à une nouvelle
  // simulation tant qu'elle existe encore dans l'horizon simulé.
  if (CLASSES_ANNEE_INDEX === null || CLASSES_ANNEE_INDEX >= CLASSES_ANNEES.length){
    CLASSES_ANNEE_INDEX = Math.max(0, CLASSES_ANNEES.length - 1);
  }
  renderClasses();
}
function classeAnneeAffichee(){
  if (!CLASSES_ANNEES.length) return null;
  const rang = Math.max(0, Math.min(CLASSES_ANNEE_INDEX === null ? CLASSES_ANNEES.length - 1 : CLASSES_ANNEE_INDEX,
                                 CLASSES_ANNEES.length - 1));
  return CLASSES_ANNEES[rang];
}
function classeReferenceAffichee(){
  if (!CLASSES_REFERENCE.length) return null;
  const rang = CLASSES_ANNEE_INDEX === null ? CLASSES_REFERENCE.length - 1 : CLASSES_ANNEE_INDEX;
  return CLASSES_REFERENCE[Math.max(0, Math.min(rang, CLASSES_REFERENCE.length - 1))];
}
function changerAnneeClasses(delta){
  if (!CLASSES_ANNEES.length) return;
  const rangActuel = CLASSES_ANNEE_INDEX === null ? CLASSES_ANNEES.length - 1 : CLASSES_ANNEE_INDEX;
  CLASSES_ANNEE_INDEX = Math.max(0, Math.min(rangActuel + delta, CLASSES_ANNEES.length - 1));
  renderClasses();
}

/* Le rythme : ce qu'un plan ne dit jamais d'un seul chiffre. Combien de son
   effet arrive dès la première année, combien à la fin, et ce que la montée en
   charge change entre les deux. Les comparaisons ne sont faites que si elles
   ont un sens : un solde final nul ou de signe opposé n'a pas de pourcentage. */
function renderRythme(){
  const zone = document.getElementById('classe-rythme');
  const courante = document.getElementById('classe-annee-courante');
  const precedent = document.getElementById('classe-annee-prec');
  const suivant = document.getElementById('classe-annee-suiv');
  const annee = classeAnneeAffichee();
  const rang = annee ? (CLASSES_ANNEE_INDEX === null ? CLASSES_ANNEES.length - 1 : CLASSES_ANNEE_INDEX) : 0;
  if (courante) courante.textContent = annee ? `an ${annee.annee} / ${CLASSES_ANNEES.length}` : 'dernière année';
  if (precedent) precedent.disabled = !annee || rang <= 0;
  if (suivant) suivant.disabled = !annee || rang >= CLASSES_ANNEES.length - 1;
  if (!zone) return;
  if (!annee || !CLASSES_ANNEES.length){
    zone.textContent = 'Le rythme du plan — combien d\u2019effet arrive la première année, combien à la fin — '
      + 's\u2019affiche ici dès la première simulation.';
    return;
  }
  const finale = CLASSES_ANNEES[CLASSES_ANNEES.length - 1];
  const premiere = CLASSES_ANNEES[0];
  const parts = [];
  if (CLASSES_ANNEES.length > 1 && Math.abs(finale.solde_mde) > 0.05
      && Math.sign(finale.solde_mde) === Math.sign(premiere.solde_mde)){
    const part = Math.round(100 * premiere.solde_mde / finale.solde_mde);
    parts.push(`l\u2019an 1 porte <b>${part} %</b> du solde de l\u2019an ${finale.annee} `
      + `(${fmtSigne(premiere.solde_mde, 1)} contre ${fmtSigne(finale.solde_mde, 1)} Md€/an)`);
  } else if (CLASSES_ANNEES.length > 1){
    parts.push(`le solde se déplace de ${fmtSigne(premiere.solde_mde, 1)} Md€/an (an 1) à `
      + `${fmtSigne(finale.solde_mde, 1)} Md€/an (an ${finale.annee}) — le rapport entre les deux `
      + `n\u2019aurait pas de sens, il n\u2019est donc pas affiché`);
  }
  if (annee !== finale){
    const ecart = annee.solde_mde - finale.solde_mde;
    parts.push(`année lue : <b>an ${annee.annee}</b>, solde des classes ${fmtSigne(annee.solde_mde, 2)} Md€/an, `
      + `soit ${fmtSigne(ecart, 2)} Md€/an par rapport au régime de fin de mandature`);
  }
  parts.push(`les cinq cartes portent aussi la courbe année par année : c\u2019est la montée en charge `
    + `déclarée au catalogue, jamais une surprise de calcul`);
  zone.innerHTML = `Rythme du plan : ${parts.join(' ; ')}.`;
}
function renderLegendeClasses(){
  const zone = document.getElementById('classes-legende');
  if (!zone) return;
  zone.innerHTML = ORDRE_CLASSES.map(cle => {
    const fiche = CLASSES[cle];
    const actif = CLASSE_FILTRE === cle ? ' actif' : '';
    return `<button type="button" class="classe-pastille motif-${fiche.motif}${actif}" `
      + `style="--couleur-classe:${fiche.couleur};--fond-classe:${fiche.couleur_html};`
      + `--teinte-motif:${fiche.couleur_html}" onclick="basculerClasse('${cle}')" `
      + `aria-pressed="${CLASSE_FILTRE === cle ? 'true' : 'false'}" `
      + `data-aide="<b>${fiche.libelle} — ${fiche.verdict}</b>${fiche.question} ${fiche.definition} `
      + `Filtrer les leviers sur cette classe (re-cliquer pour tout réafficher).">`
      + `<span class="symbole" aria-hidden="true">${fiche.symbole}</span>${echapperTexte(fiche.libelle)} `
      + `<span aria-hidden="true">· ${fiche.nb_leviers}</span></button>`;
  }).join('');
}
function renderFiltresClasses(){
  const zone = document.getElementById('classes-filtres');
  if (!zone) return;
  const jetons = ORDRE_CLASSES.map(cle => {
    const fiche = CLASSES[cle];
    const actif = CLASSE_FILTRE === cle ? ' actif' : '';
    return `<button type="button" class="classe-pastille motif-${fiche.motif}${actif}" `
      + `style="--couleur-classe:${fiche.couleur};--fond-classe:${fiche.couleur_html};`
      + `--teinte-motif:${fiche.couleur_html}" onclick="basculerClasse('${cle}')" `
      + `aria-pressed="${CLASSE_FILTRE === cle ? 'true' : 'false'}" `
      + `data-aide="<b>${fiche.libelle}</b>${fiche.definition}"><span class="symbole" aria-hidden="true">`
      + `${fiche.symbole}</span>${echapperTexte(fiche.libelle_court)}</button>`;
  }).join('');
  const tous = `<button type="button" class="classe-pastille${CLASSE_FILTRE ? '' : ' actif'}" `
    + `onclick="basculerClasse('${CLASSE_FILTRE}')" data-aide="<b>Toutes les classes</b>Réaffiche `
    + `les 5 classes et leurs leviers.">Toutes</button>`;
  zone.innerHTML = `<span class="titre">Filtrer par classe</span>${jetons}${tous}`;
}
/* ── Le résumé de tête ────────────────────────────────────────────────────
   Quatre chiffres et une phrase, visibles sans faire défiler la page. Toutes
   les valeurs viennent des mêmes fonctions que la balance (`classeAnneeAffichee`,
   `fmtSigne`, `fmtMenage`) et la phrase est celle du verdict de la balance,
   reprise mot pour mot : le résumé ne raconte pas autre chose que la page. */
function renderResume(){
  const solde = document.getElementById('resume-solde');
  if (!solde) return;
  const note = document.getElementById('resume-solde-note');
  const entrees = document.getElementById('resume-entrees');
  const sorties = document.getElementById('resume-sorties');
  const sortiesNote = document.getElementById('resume-sorties-note');
  const menage = document.getElementById('resume-menage');
  const menageNote = document.getElementById('resume-menage-note');
  const phrase = document.getElementById('resume-phrase');
  const annee = classeAnneeAffichee();
  if (!annee){
    if (phrase) phrase.textContent = "Déplacez un curseur : le plan se pèse ici, en milliards d'euros par an.";
    return;
  }
  const montant = Number(annee.solde_mde) || 0;
  const neutre = Math.abs(montant) < 0.05;
  solde.textContent = `${fmtSigne(montant, 1)} Md€/an`;
  if (note) note.textContent = neutre
    ? `à l'équilibre — année ${annee.annee}`
    : (montant > 0 ? 'marge dégagée' : 'marge consommée') + ` — année ${annee.annee}`;
  if (entrees) entrees.textContent = `${fmtSigne(annee.entrees_mde, 1)} Md€/an`;
  if (sorties) sorties.textContent = `${fmtSigne(annee.sorties_mde, 1)} Md€/an`;
  if (sortiesNote) sortiesNote.textContent = annee.sorties_mde < 0
    ? 'budgets en baisse : une coupe, pas une dépense'
    : 'dépenses engagées';
  if (menage) menage.textContent = fmtMenage(montant);
  if (menageNote) menageNote.textContent = 'solde du plan « ' + statutDiviseur() + ' »';
  const verdict = document.getElementById('balance-verdict');
  if (phrase && verdict) phrase.textContent = verdict.textContent;
  const net = document.getElementById('balance-net');
  const carte = solde.parentNode;
  if (net && carte && carte.classList && net.classList){
    carte.classList.toggle('resume-gain', net.classList.contains('gain'));
    carte.classList.toggle('resume-cout', net.classList.contains('cout'));
  }
}

function renderBalance(){
  const annee = classeAnneeAffichee();
  const verdict = document.getElementById('balance-verdict');
  const net = document.getElementById('balance-net');
  const detail = document.getElementById('balance-detail');
  const entrees = document.getElementById('balance-entrees-montant');
  const sorties = document.getElementById('balance-sorties-montant');
  const entreesMenage = document.getElementById('balance-entrees-menage');
  const sortiesMenage = document.getElementById('balance-sorties-menage');
  const jaugeE = document.getElementById('balance-jauge-entrees');
  const jaugeS = document.getElementById('balance-jauge-sorties');
  if (!annee){
    if (verdict) verdict.textContent = 'lancez une simulation pour peser les deux plateaux';
    if (entrees) entrees.textContent = '—';
    if (sorties) sorties.textContent = '—';
    if (net){ net.textContent = 'solde : —'; net.className = 'net neutre'; }
    renderResume();
    return;
  }
  const total = Math.abs(annee.entrees_mde) + Math.abs(annee.sorties_mde);
  const coupes = annee.sorties_mde < 0;
  if (entrees) entrees.textContent = `${fmtSigne(annee.entrees_mde, 1)} Md€/an`;
  if (sorties) sorties.textContent = `${fmtSigne(annee.sorties_mde, 1)} Md€/an`;
  if (entreesMenage) entreesMenage.textContent = `${fmtMenage(annee.entrees_mde)} — recettes + économies`;
  if (sortiesMenage) sortiesMenage.textContent = coupes
    ? `${fmtMenage(annee.sorties_mde)} — budgets en baisse : c'est une coupe, pas une dépense`
    : `${fmtMenage(annee.sorties_mde)} — dépenses engagées`;
  if (jaugeE) jaugeE.style.width = `${total > 0 ? Math.round(100 * Math.abs(annee.entrees_mde) / total) : 0}%`;
  if (jaugeS) jaugeS.style.width = `${total > 0 ? Math.round(100 * Math.abs(annee.sorties_mde) / total) : 0}%`;
  if (net){
    const solde = annee.solde_mde;
    net.className = 'net ' + (Math.abs(solde) < 0.05 ? 'neutre' : (solde > 0 ? 'gain' : 'cout'));
    net.textContent = `solde des classes : ${fmtSigne(solde, 1)} Md€/an`;
  }
  if (verdict){
    const solde = annee.solde_mde;
    verdict.textContent = Math.abs(solde) < 0.05
      ? `année ${annee.annee} : recettes et économies équilibrent les dépenses`
      : (solde > 0
        ? `année ${annee.annee} : le plan dégage ${fmt(solde, 1)} Md€/an de marge`
        : `année ${annee.annee} : le plan consomme ${fmt(Math.abs(solde), 1)} Md€/an de marge`);
  }
  if (detail){
    const ref = classeReferenceAffichee();
    const refTexte = ref
      ? `À leviers neutres (trajectoire de référence), ces deux plateaux sont à zéro : tout `
        + `ce qui est pesé ici est donc bien l'effet du plan, jamais un niveau de départ. `
      : '';
    const soldeMoteur = Number(annee.recettes_moteur_mde) - Number(annee.depenses_moteur_mde);
    detail.innerHTML = `Lecture directe, année ${annee.annee} : recettes `
      + `<b>${fmt(annee.classes.recettes.montant_mde, 2)}</b> + économies `
      + `<b>${fmt(annee.classes.economies.montant_mde, 2)}</b> − dépenses `
      + `<b>${fmt(annee.classes.depenses.montant_mde, 2)}</b> Md€/an = `
      + `<b>${fmtSigne(annee.solde_mde, 2)}</b> Md€/an. `
      + refTexte
      + `Le compte du moteur, lui, range chaque montant par famille : ${fmt(annee.recettes_moteur_mde, 2)} Md€ de `
      + `« recettes nouvelles » et ${fmt(annee.depenses_moteur_mde, 2)} Md€ de « dépenses nouvelles », soit `
      + `${fmtSigne(soldeMoteur, 2)} Md€/an. L'écart avec la lecture par classes (`
      + `${fmtSigne(annee.solde_mde - soldeMoteur, 2)} Md€) a trois causes nommées : une baisse de `
      + `prélèvements compte comme une recette nouvelle alors qu'elle coûte, une économie d'efficacité compte `
      + `comme une dépense nouvelle alors qu'elle rapporte, et les drapeaux 0/1 comptent comme des dépenses `
      + `alors qu'ils ne portent aucun euro. Les deux soldes sont affichés côte à côte, aucun n'est masqué. `
      + `Les classes « règles » et « monde » portent `
      + `<b>${fmt(annee.hors_budget_mde, 2)}</b> unité(s) hors budget (drapeaux, hypothèses de contexte) : `
      + `elles ne sont pas additionnées au solde. `
      + `${echapperTexte(annee.note_hors_budget || '')} `
      + `Conversion : ${(DIVISEUR_MENAGES && DIVISEUR_MENAGES.libelle) || 'ordre de grandeur'} `
      + `(<b>${echapperTexte(statutDiviseur())}</b>).`;
  }
  // Le résumé de tête suit la balance : un seul calcul, deux affichages.
  renderResume();
}
/* ── La cascade : le plan déroulé, marche par marche ─────────────────────
   Ce qu'aucun total annuel ne montre : dans quel ordre le budget se
   construit. Chaque classe part du cumul laissé par la précédente et le
   déplace de son montant ; l'escalier se referme sur le solde. Les classes
   « règles » et « monde » n'y entrent pas — leurs unités (drapeaux 0/1,
   dollars du baril, points de tension) ne sont pas des euros et les
   additionner fabriquerait un faux total. */
function monetaireDe(cle){
  const fiche = CLASSES[cle];
  if (fiche && typeof fiche.monetaire === 'boolean') return fiche.monetaire;
  return cle === 'recettes' || cle === 'economies' || cle === 'depenses';
}
/* Ce qu'une classe fait au cumul : le sens de la classe dit comment elle pèse.
   Une recette ou une économie l'augmente ; une dépense le diminue — et une
   baisse de budget (montant négatif dans « dépenses ») l'augmente d'autant,
   puisqu'une coupe n'est pas une dépense. Le total reproduit exactement le
   solde des classes du moteur (`entrées − sorties`), jamais un total parallèle. */
function contributionClasse(cle, bloc){
  const montant = Number(bloc && bloc.montant_mde) || 0;
  const fiche = CLASSES[cle];
  return (fiche && fiche.sens === 'sortie') ? -montant : montant;
}
function marchesCascade(annee){
  const etapes = [];
  let cumul = 0;
  ORDRE_CLASSES.forEach(cle => {
    if (!monetaireDe(cle)) return;
    const bloc = annee.classes[cle];
    if (!bloc) return;
    const contribution = contributionClasse(cle, bloc);
    const debut = cumul;
    cumul += contribution;
    etapes.push({cle, fiche: CLASSES[cle], bloc, contribution, debut, fin: cumul});
  });
  return {etapes, solde: cumul};
}
function renderCascade(){
  const zone = document.getElementById('cascade-marches');
  const note = document.getElementById('cascade-note');
  if (!zone) return;
  const annee = classeAnneeAffichee();
  if (!annee){
    zone.innerHTML = '';
    if (note) note.textContent = 'La cascade se dessine dès la première simulation : elle montre dans quel '
      + 'ordre le plan se construit, du premier euro qui entre au solde. Les classes « règles » et « monde » '
      + 'en restent dehors : leurs unités ne sont pas des euros.';
    return;
  }
  const calcul = marchesCascade(annee);
  const etapes = calcul.etapes;
  const solde = calcul.solde;
  const bas = Math.min(0, solde, ...etapes.map(etape => Math.min(etape.debut, etape.fin)));
  const haut = Math.max(0, solde, ...etapes.map(etape => Math.max(etape.debut, etape.fin)));
  const etendue = (haut - bas) || 1;
  const borne = valeur => Math.max(0, Math.min(100, 100 * (valeur - bas) / etendue));
  const pisteHtml = (debut, fin, fiche) => {
    const motif = fiche.motif === 'hachure' ? ' hachure' : (fiche.motif === 'pointille' ? ' pointille' : '');
    const gauche = borne(Math.min(debut, fin));
    const largeur = Math.max(0.7, borne(Math.max(debut, fin)) - gauche);
    return `<span class="cascade-piste" style="--couleur-classe:${fiche.couleur};--teinte-motif:${fiche.couleur_html}" aria-hidden="true">`
      + `<i class="zero" style="left:${borne(0)}%"></i>`
      + `<i class="barre${motif}" style="left:${gauche}%;width:${largeur}%"></i></span>`;
  };
  /* Les leviers qui pèsent le plus, nommés : la marche dit combien la classe
     déplace le cumul, les puces disent qui le déplace. */
  const pucesHtml = (bloc, fiche) => {
    const plafond = 4;
    const liste = (bloc.leviers || []);
    const puces = liste.slice(0, plafond).map(entree => {
      const levier = levierParCle(entree.cle) || {};
      const libelle = levier.libelle || entree.cle;
      return `<span class="puce-unite" data-aide-levier="${entree.cle}" `
        + `data-aide="<b>${echapperTexte(libelle)}</b>Ce levier déplace le cumul de `
        + `${fmtSigne(entree.montant_mde, 2)} Md€/an cette année. Classe : `
        + `${echapperTexte(fiche.libelle)}.">`
        + `${echapperTexte(libelle)} <b>${fmtSigne(entree.montant_mde, 2)}</b></span>`;
    }).join('');
    const reste = liste.length - plafond;
    return puces + (reste > 0 ? `<span class="reste">+ ${reste} autre(s) levier(s) actif(s)</span>` : '');
  };
  const lignes = etapes.map((etape, index) => {
    const fiche = etape.fiche;
    const bloc = etape.bloc;
    const coupe = etape.cle === 'depenses' && bloc.montant_mde < 0;
    /* La marche affiche ce qu'elle fait au cumul (le grand chiffre) et, quand
       les deux diffèrent, le montant tel que la classe le lit (les dépenses
       engagées, ou les budgets coupés). */
    const lecture = fiche.sens !== 'sortie' ? ''
      : `<small>${fmt(bloc.montant_mde, 2)} Md€/an de dépenses `
        + `${coupe ? 'en moins — une coupe, pas une dépense' : 'engagées'}</small>`;
    return `<li class="cascade-marche" data-classe="${etape.cle}" `
      + `style="--couleur-classe:${fiche.couleur};--teinte-motif:${fiche.couleur_html}">`
      + `<div class="cascade-ligne">`
      + `<span class="cascade-nom"><span class="tete"><span class="symbole" aria-hidden="true">${fiche.symbole}</span>`
      + `${echapperTexte(fiche.libelle)}</span>`
      + `<small>marche ${index + 1} · ${bloc.nb_actifs} levier(s) actif(s) sur ${fiche.nb_leviers}</small></span>`
      + pisteHtml(etape.debut, etape.fin, fiche)
      + `<span class="cascade-montant">${fmtSigne(etape.contribution, 2)}<small>Md€/an</small>`
      + `<small>cumul ${fmtSigne(etape.fin, 2)}</small>${lecture}</span>`
      + `</div>`
      + `<div class="cascade-detail">`
      + (coupe ? `<span class="reste">budgets en baisse — c'est une coupe, pas une dépense.</span>` : '')
      + pucesHtml(bloc, fiche)
      + `</div></li>`;
  }).join('');
  const couleurSolde = Math.abs(solde) < 0.05 ? 'var(--texte-dim)'
    : (solde > 0 ? 'var(--classe-recettes)' : 'var(--classe-depenses)');
  const total = `<li class="cascade-marche cascade-total" style="--couleur-classe:${couleurSolde};--teinte-motif:rgba(255,255,255,.35)">`
    + `<div class="cascade-ligne">`
    + `<span class="cascade-nom"><span class="tete"><span class="symbole" aria-hidden="true">=</span>Solde des classes</span>`
    + `<small>recettes + économies − dépenses · année ${annee.annee}</small></span>`
    + pisteHtml(0, solde, {couleur: couleurSolde, couleur_html: 'rgba(255,255,255,.35)', motif: 'uni'})
    + `<span class="cascade-montant">${fmtSigne(solde, 2)}<small>Md€/an</small>`
    + `<small>${fmtMenage(solde)}</small></span>`
    + `</div>`
    + `<div class="cascade-detail">`
    + (Math.abs(solde) < 0.05
      ? `Le plan se referme à l'équilibre : ce qui entre paie exactement ce qui sort.`
      : (solde > 0
        ? `Le plan dégage ${fmt(solde, 2)} Md€/an de marge après avoir payé ses dépenses.`
        : `Le plan consomme ${fmt(Math.abs(solde), 2)} Md€/an de marge : les dépenses dépassent ce qui entre.`))
    + `</div></li>`;
  zone.innerHTML = lignes + total;
  if (note){
    const dehors = ORDRE_CLASSES.filter(cle => !monetaireDe(cle)).map(cle => {
      const bloc = annee.classes[cle];
      const fiche = CLASSES[cle];
      if (!fiche) return '';
      return bloc && bloc.nb_actifs
        ? `<b>${echapperTexte(fiche.libelle.toLowerCase())}</b> : ${bloc.nb_actifs} unité(s), `
          + `${fmt(bloc.montant_hors_budget_mde, 2)} hors budget`
        : `${echapperTexte(fiche.libelle.toLowerCase())} : aucun actif`;
    }).filter(Boolean).join(' · ');
    note.innerHTML = `Hors cascade : ${dehors}. Ces unités ne sont pas des euros — les additionner au solde `
      + `fabriquerait un faux total. ${echapperTexte(annee.note_hors_budget || '')}`;
  }
}
function renderClasses(){
  renderLegendeClasses();
  renderFiltresClasses();
  renderRythme();
  renderBalance();
  renderCascade();
  const zone = document.getElementById('grille-classes');
  const note = document.getElementById('classes-note');
  if (!zone) return;
  const annee = classeAnneeAffichee();
  zone.innerHTML = ORDRE_CLASSES.map(cle => {
    const fiche = CLASSES[cle];
    const bloc = annee ? annee.classes[cle] : null;
    const montant = bloc ? bloc.montant_mde : 0;
    const actifs = bloc ? bloc.nb_actifs : 0;
    const monetaire = monetaireDe(cle);
    const chiffre = !bloc
      ? '<span class="chiffre">— <small>lancez une simulation</small></span>'
      : (monetaire
        ? `<span class="chiffre">${fmtSigne(montant, 2)} Md€/an`
          + `<small>${fmtMenage(montant)} · ${actifs} levier(s) actif(s)`
          + `${sensDUnMontant(montant) === 'negatif' && cle === 'depenses' ? ' · budgets en baisse' : ''}`
          + `</small></span>`
        : `<span class="chiffre">${actifs} levier(s)<small>hors budget — des unités, jamais des euros`
          + `</small></span><span class="chips-unites">${chipsHorsBudget(bloc)}</span>`);
    const doctrine = String(fiche.doctrine || '').split('/').pop();
    return `<article class="classe-carte motif-${fiche.motif}" `
      + `style="--couleur-classe:${fiche.couleur};--fond-classe:${fiche.couleur_html};`
      + `--teinte-motif:${fiche.couleur_html}" data-classe="${cle}">`
      + `<h3><span class="symbole" aria-hidden="true">${fiche.symbole}</span> ${echapperTexte(fiche.libelle)} `
      + `<span class="classe-pastille" style="--couleur-classe:${fiche.couleur}">${fibreLeviers(fiche.nb_leviers)}</span></h3>`
      + `<p class="question">${echapperTexte(fiche.question)}</p>`
      + `<p class="definition">${echapperTexte(fiche.definition)}</p>`
      + `<div class="chiffres">${chiffre}</div>`
      + `<div class="pied"><span>${fiche.familles_nb} famille(s) · `
      + rampeSerieHtml(CLASSES_ANNEES.map(anneeClassee => anneeClassee.classes[cle].montant_mde), fiche.couleur)
      + `<span class="rampe-legende">année par année</span></span>`
      + `<button type="button" class="bouton" onclick="basculerClasse('${cle}')" `
      + `data-aide="<b>Voir ces leviers</b>Filtre la grille sur la classe « ${fiche.libelle} ».">`
      + `Voir ces ${fiche.nb_leviers} leviers</button>`
      + `<span>Source : <code>${echapperTexte(doctrine)}</code> · ${echapperTexte(fiche.verdict)}</span></div>`
      + `</article>`;
  }).join('');
  if (note){
    const hors = annee && annee.hors_budget_mde ? ` — dont ${fmt(annee.hors_budget_mde, 2)} unité(s) hors budget.` : '';
    note.innerHTML = (CLASSES_DEFINITION || '') + (NOTE_SOLDE ? ' ' + NOTE_SOLDE : '') + hors
      + (DIVISEUR_MENAGES ? ` Conversion en euros par ménage : `
         + `${echapperTexte(DIVISEUR_MENAGES.libelle)} — `
         + `<b>${echapperTexte(DIVISEUR_MENAGES.statut)}</b>. ${echapperTexte(DIVISEUR_MENAGES.note || '')}` : '');
  }
}
function fibreLeviers(nombre){
  return `${nombre} levier${nombre > 1 ? 's' : ''}`;
}
/* Classes « règles » et « monde » : leurs valeurs ne sont pas des euros mais
   des unités (drapeau 0/1, dollars du baril, points de tension). Additionner
   ces unités entre elles ne veut rien dire : on les liste une par une, avec
   l'unité du levier telle que le catalogue la déclare. */
function chipsHorsBudget(bloc, maxi){
  if (!bloc || !bloc.leviers.length) return '<span class="rampe-legende">aucun actif</span>';
  const limite = maxi || 6;
  const affiches = bloc.leviers.slice(0, limite).map(entree => {
    const levier = levierParCle(entree.cle) || {};
    const unite = levier.unite && levier.unite !== 'bool' ? ` ${levier.unite}` : '';
    const libelle = levier.libelle || entree.cle;
    return `<span class="puce-unite" data-aide-levier="${entree.cle}" `
      + `data-aide="<b>${echapperTexte(libelle)}</b>Valeur mesurée par le moteur cette année : `
      + `${fmt(entree.montant_mde, 2)}${echapperTexte(unite)}. Cette unité n'est pas un euro : elle `
      + `n'entre pas dans le solde.">${echapperTexte(libelle)} `
      + `<b>${fmt(entree.montant_mde, 2)}${echapperTexte(unite)}</b></span>`;
  }).join('');
  const plus = bloc.leviers.length > limite
    ? `<span class="rampe-legende">+ ${bloc.leviers.length - limite} autre(s)</span>` : '';
  return affiches + plus;
}
function basculerClasse(cle){
  const cible = (cle === CLASSE_FILTRE) ? '' : cle;
  CLASSE_FILTRE = (cible && CLASSES[cible]) ? cible : '';
  renderClasses();
  renderLeviers(filtreCourant());
  if (CLASSE_FILTRE){
    const section = document.getElementById('section-leviers');
    if (section && section.scrollIntoView) section.scrollIntoView({behavior:'smooth', block:'start'});
  }
}
function basculerClasseSeules(){
  LEVIERS_MODIFIES_SEULS = !LEVIERS_MODIFIES_SEULS;
  const bouton = document.getElementById('btn-classes-seules');
  if (bouton){
    bouton.textContent = LEVIERS_MODIFIES_SEULS ? 'Tout le catalogue' : 'Mes leviers seulement';
    bouton.setAttribute('aria-pressed', LEVIERS_MODIFIES_SEULS ? 'true' : 'false');
    bouton.className = LEVIERS_MODIFIES_SEULS ? 'primaire' : 'discret';
  }
  renderLeviers(filtreCourant());
}

/* ── Leviers : tout le catalogue, visible et actionnable ───────────────── */
function filtreCourant(){
  const champ = document.getElementById('recherche-levier');
  return (champ && champ.value) || '';
}
function basculerDensite(force){
  VUE_COMPACTE = (force === undefined) ? !VUE_COMPACTE : !!force;
  const case_ = document.getElementById('case-densite');
  if (case_) case_.checked = VUE_COMPACTE;
  const bouton = document.getElementById('btn-densite');
  if (bouton) bouton.textContent = VUE_COMPACTE ? 'Vue confort' : 'Vue compacte';
  renderLeviers(filtreCourant());
}
function basculerDetailsConsole(){
  const corps = document.getElementById('console-corps');
  if (!corps) return;
  corps.classList.toggle('replie');
  const bouton = document.getElementById('btn-console-details');
  if (bouton) bouton.textContent = corps.classList.contains('replie')
    ? 'Afficher le détail des seuils' : 'Masquer le détail des seuils';
}
function allerAuxLeviers(){
  const section = document.getElementById('section-leviers');
  if (section && section.scrollIntoView) section.scrollIntoView({behavior:'smooth', block:'start'});
}
function allerAudit(){
  const section = document.getElementById('section-audit');
  if (section && section.scrollIntoView) section.scrollIntoView({behavior:'smooth', block:'start'});
}
/* ── Aides au survol (infobulles) ─────────────────────────────────────────
   Tout élément portant `data-aide` (bouton, case à cocher, champ) ou
   `data-aide-levier` (réglage : curseur, interrupteur, étiquette de valeur)
   s'explique au survol et au focus clavier. L'infobulle est une couche fixe
   qui ne capte aucun clic (`pointer-events:none`) et disparaît au départ de
   la souris : les leviers restent visibles et actionnables.                    */
function elementInfobulle(){ return document.getElementById('infobulle'); }
function levierParCle(cle){
  if (!CATALOGUE) return null;
  return CATALOGUE.parametres.familles.flatMap(f => f.leviers).find(l => l.cle === cle) || null;
}
function texteAideLevier(cle){
  const levier = levierParCle(cle);
  if (!levier) return '';
  const valeur = PARAMS[cle];
  const famille = (CATALOGUE.familles || []).find(f => f.cle === levier.famille);
  const actif = levier.type === 'interrupteur' ? (valeur >= 0.5 ? 'activé' : 'désactivé')
    : `${fmt(valeur, levier.precision)} ${levier.unite === 'bool' ? '' : levier.unite}`.trim();
  const defaut = levier.type === 'interrupteur'
    ? (levier.defaut >= 0.5 ? 'activé' : 'désactivé')
    : `${fmt(levier.defaut, levier.precision)} ${levier.unite === 'bool' ? '' : levier.unite}`.trim();
  const lignes = [`<span class="aide-titre">${levier.libelle}</span>`];
  lignes.push(`${famille ? famille.libelle : levier.famille} · ${levier.type}`
    + (levier.unite && levier.unite !== 'bool' ? ` · unité : ${levier.unite}` : ''));
  lignes.push(`valeur actuelle <b>${actif}</b> (défaut ${defaut})`);
  if (MOUVEMENT && MOUVEMENT.cle === cle){
    lignes.push(`dernier mouvement : ${fmt(MOUVEMENT.avant, levier.precision)} → `
      + `${fmt(valeur, levier.precision)} — le conseiller temps réel de la console `
      + 'de veille lit cette décision et ses ricochets.');
  }
  if (levier.type === 'interrupteur'){
    lignes.push('interrupteur : activé ou désactivé');
  } else {
    lignes.push(`plage ${fmt(levier.minimum, levier.precision)} → `
      + `${fmt(levier.maximum, levier.precision)} ${levier.unite} · pas ${fmt(levier.pas, 2)}`);
  }
  if (levier.description) lignes.push(levier.description);
  const fiche = ficheClasse(levier.classe);
  if (fiche){
    lignes.push(`Classe « ${fiche.libelle} » (${fiche.symbole}) : ${fiche.verdict}`
      + (levier.classe_motif ? ` — ${levier.classe_motif}` : ''));
  }
  const declares = Object.entries(levier.effets_directs || {}).slice(0, 4).map(([theme, coefficient]) =>
    `${theme} ${coefficient > 0 ? '+' : ''}${fmt(coefficient, 2)}`);
  if (declares.length) lignes.push(`Effets déclarés : ${declares.join(' ; ')}`);
  const puces = (DERNIERES_PUCES[cle] || []).slice(0, 3).map(puce =>
    `${puce.libelle} ${puce.effet_score > 0 ? '+' : ''}${fmt(puce.effet_score, 1)} pt`);
  if (puces.length) lignes.push(`Mesuré à l'instant sur ce réglage : ${puces.join(' ; ')}`);
  const bulle = BULLES[cle];
  if (bulle && bulle.bilan_domaines){
    const mouvements = bulle.bilan_domaines.filter(domaine => domaine.touche).slice(0, 3).map(domaine => {
      const ecart = Math.abs(domaine.maximum) >= Math.abs(domaine.minimum) ? domaine.maximum : domaine.minimum;
      return `${domaine.libelle} ${ecart > 0 ? '+' : ''}${fmt(ecart, 1)} pt`;
    });
    if (mouvements.length) lignes.push(`Aux bornes du réglage : ${mouvements.join(' ; ')}`);
    if (bulle.lecture && bulle.lecture.phrase){
      lignes.push(bulle.lecture.phrase.slice(0, 190) + (bulle.lecture.phrase.length > 190 ? '…' : ''));
    }
  } else {
    lignes.push('Cliquez sur « interactions » pour la chaîne complète : médiateurs touchés, '
      + 'répercussions par domaine, garde-fous et strates.');
  }
  return lignes.join('<br>');
}
function texteAideElement(cible){
  if (!cible || !cible.getAttribute) return '';
  if (cible.getAttribute('data-aide-levier')) return texteAideLevier(cible.getAttribute('data-aide-levier'));
  return cible.getAttribute('data-aide') || '';
}
function positionnerInfobulle(cible){
  const bulle = elementInfobulle();
  if (!bulle) return;
  const rect = (cible && typeof cible.getBoundingClientRect === 'function')
    ? cible.getBoundingClientRect() : null;
  if (!rect || (!rect.width && !rect.height)) return;
  const largeur = (typeof innerWidth === 'number') ? innerWidth : 1200;
  const hauteur = (typeof innerHeight === 'number') ? innerHeight : 900;
  const gauche = Math.max(8, Math.min(rect.left, largeur - 364));
  const enBas = rect.bottom + 12;
  bulle.style.left = `${gauche}px`;
  bulle.style.top = `${(enBas + 220 > hauteur ? Math.max(8, rect.top - 12) : enBas)}px`;
}
function afficherInfobulle(html, cible){
  const bulle = elementInfobulle();
  if (!bulle || !html) return;
  bulle.innerHTML = html;
  bulle.classList.add('visible');
  bulle.setAttribute('aria-hidden', 'false');
  positionnerInfobulle(cible);
}
function masquerInfobulle(){
  const bulle = elementInfobulle();
  if (!bulle) return;
  bulle.classList.remove('visible');
  bulle.setAttribute('aria-hidden', 'true');
}
function survoler(cible){
  // Jamais d'infobulle volante par-dessus un résultat en cours de lecture :
  // pendant qu'un réglage est manipulé, ou quand une bulle « interactions »
  // est ouverte, l'aide flottante s'efface — l'information utile est déjà à
  // l'écran (badge coût/gain live, bulle explicative, console de veille).
  // Valable pour l'ensemble des réglages et des fonctionnalités : survoler
  // est le seul chemin d'affichage des infobulles.
  if (REGLAGE_EN_COURS || BULLE_OUVERTE){ masquerInfobulle(); return; }
  const texte = texteAideElement(cible);
  if (!texte){ masquerInfobulle(); return; }
  afficherInfobulle(texte, cible);
}
function initialiserInfobulles(){
  if (!document.addEventListener) return;
  const cherche = (noeud) => {
    if (!noeud || !noeud.closest) return null;
    // La bulle dépliée reste lisible : pas d'infobulle par-dessus son contenu.
    if (noeud.closest('.bulle-levier')) return null;
    return noeud.closest('[data-aide], [data-aide-levier]');
  };
  document.addEventListener('mouseover', (evenement) => {
    const cible = cherche(evenement.target);
    if (cible) survoler(cible);
  });
  document.addEventListener('mouseout', (evenement) => {
    if (cherche(evenement.relatedTarget)) return;
    masquerInfobulle();
  });
  document.addEventListener('focusin', (evenement) => {
    const cible = cherche(evenement.target);
    if (cible) survoler(cible);
  });
  document.addEventListener('focusout', () => masquerInfobulle());
  document.addEventListener('mousedown', () => masquerInfobulle());
  document.addEventListener('scroll', () => masquerInfobulle(), true);
}

/* ── Bulles explicatives par levier ────────────────────────────────────────
   Chaque réglage porte un bouton « interactions » : la bulle s'ouvre dans la
   carte du levier (jamais par-dessus), avec la chaîne technique, les
   répercussions mesurées borne par borne et la lecture opportunités /
   désagréments. Le contenu vient du serveur (/api/bulle), calculé par
   simulateur/bulles.py sur les formules réelles du modèle.                    */
function libelleDomaine(cle){
  if (CATALOGUE && CATALOGUE.domaines && !Object.keys(LIBELLES_DOMAINES).length){
    for (const domaine of CATALOGUE.domaines){ LIBELLES_DOMAINES[domaine.cle] = domaine.libelle; }
  }
  return LIBELLES_DOMAINES[cle] || cle;
}
function montantTexte(emission){
  if (emission.montant === null || emission.montant === undefined) return 'champ du moteur';
  const signe = emission.montant > 0 ? '+' : '';
  return `${signe}${fmt(emission.montant, 2)} ${emission.unite || ''}`.trim();
}
function pucesDomaines(domaines, maximum){
  return (domaines || []).slice(0, maximum || 20).map(domaine => {
    const delta = domaine.delta;
    return `<span class="bulle-domaine ${delta >= 0 ? 'pos' : 'neg'}">${libelleDomaine(domaine.cle)} `
      + `${delta > 0 ? '+' : ''}${fmt(delta, 1)} pt</span>`;
  }).join('');
}
function chaineHtml(bulle){
  const lignes = (bulle.emissions || []).map(emission => {
    let relais;
    if (emission.relaye){
      const lecteurs = (emission.consommateurs || []).slice(0, 3).map(consommateur =>
        `${consommateur.libelle} (${libelleDomaine(consommateur.domaine)}, ×${fmt(consommateur.coefficient, 2)})`
      ).join(' ; ');
      relais = `lu par : ${lecteurs}`;
    } else if (emission.relais){
      relais = `relais : ${emission.relais}`;
    } else {
      relais = 'aucun relais identifié dans les formules actuelles';
    }
    return `<li><span class="bulle-med">${emission.mediateur}</span> ${montantTexte(emission)} → ${relais}</li>`;
  }).join('');
  const moteur = bulle.champ_moteur
    ? `<li><span class="bulle-med">${bulle.champ_moteur.champ}</span> état du moteur → `
      + "l'effet vit dans les strates 1 à 5 (journal ci-dessous)</li>" : '';
  const maillons = (bulle.maillons_non_relayes || []).map(maillon =>
    `<li class="bulle-alerte">⚠ ${maillon.mediateur} : ${maillon.note}</li>`).join('');
  const vide = (!lignes && !moteur) ? '<li>Aucun médiateur propre : le levier agit par le champ du moteur.</li>' : '';
  return `<div class="bulle-section"><span class="bulle-titre">Chaîne d'interaction (plein régime)</span>`
    + `<ul>${lignes}${moteur}${vide}${maillons}</ul></div>`;
}
function effetsDeclaresHtml(bulle){
  const jetons = [...(bulle.effets_directs || []), ...(bulle.effets_hors_domaine || [])].map(effet => {
    const domaines = (effet.domaines || []).map(cle => libelleDomaine(cle)).join(', ');
    const precision = domaines ? ` → ${domaines}` : ' (thème transverse)';
    return `<span class="bulle-domaine ${effet.coefficient >= 0 ? 'pos' : 'neg'}">`
      + `${effet.theme} ${effet.coefficient > 0 ? '+' : ''}${fmt(effet.coefficient, 2)}${precision}</span>`;
  }).join('');
  return `<div class="bulle-section"><span class="bulle-titre">Effets déclarés au catalogue</span>`
    + `<div>${jetons || 'aucun'}</div></div>`;
}
/* Les identifiants de droit positif attachés à un levier : la puce mène à la fiche
   d'article, pas à un calcul du modèle. Un article n'est jamais une promesse de
   rendement — c'est le texte qui dit si le réglage est licite, et jusqu'où. */
function numerosArticle(levier){
  const bruts = levier.articles || [];
  const numeros = [];
  bruts.forEach(identifiant => {
    const numero = String(identifiant).replace(/^CONST_ART_/, '').replace(/_/g, '-');
    if (/^[0-9]+(-[0-9]+)*$/.test(numero) && !numeros.includes(numero)) numeros.push(numero);
  });
  return numeros;
}
function articlesHtml(levier){
  const numeros = numerosArticle(levier);
  if (!numeros.length) return '';
  const puces = numeros.map(numero => {
    const href = '/api/constitution?article=' + encodeURIComponent(numero);
    const titre = 'Fiche de droit positif de l\'article ' + numero
      + ' — texte, chiffres vérifiés, bornes du modèle, réversibilité. Réponse du serveur,'
      + ' pas un calcul du simulateur.';
    return '<a class="article" href="' + href + '" target="_blank" rel="noopener" title="'
      + titre + '">' + numero + '</a>';
  }).join('');
  const hors = (levier.articles || []).filter(identifiant =>
    !/^CONST_ART_/.test(String(identifiant))).length;
  return '<div class="articles"><span class="articles-legende">droit positif</span>' + puces
    + (hors > 0 ? '<span class="articles-hors">' + hors + ' hors Constitution</span>' : '')
    + '</div>';
}
/* La section « Nuances institutionnelles » : le vecteur courant est envoyé à
   /api/nuances, qui renvoie les seuils recalculés, les délais de rigueur, les
   fentes, les indices, les strates et les garde-fous de la couche. Rien n'est
   inventé ici : chaque chiffre vient du serveur, et les listes de contrôle qui
   ne sont pas vides s'affichent en rouge — un trou de la couche doit se voir. */
async function rafraichirNuances(){
  const zone = document.getElementById('nuances-corps');
  if (!zone) return;
  try{
    const reponse = await fetch('/api/nuances', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({parametres: Object.assign({}, PARAMS)})});
    if (!reponse.ok) throw new Error('HTTP ' + reponse.status);
    NUANCES = await reponse.json();
    renderNuances();
    renderVerrous();
    renderReglagesTouches();
  }catch(erreur){
    zone.innerHTML = '<div class="carte">Le serveur de nuances n\'a pas répondu : '
      + erreur + '. Les curseurs restent utilisables ; seul ce tableau manque.</div>';
  }
}
function ecartHtml(ecart){
  if (!ecart) return '<span class="chiffre">—</span>';
  const classe = ecart > 0 ? 'plus' : 'moins';
  const signe = ecart > 0 ? '+' : '−';
  return '<span class="' + classe + '">' + signe + fmt(Math.abs(ecart), 0) + '</span>';
}
function renderNuances(){
  const zone = document.getElementById('nuances-corps');
  const intro = document.getElementById('nuances-resume');
  if (!zone || !NUANCES) return;
  const resume = NUANCES.resume || {};
  if (intro){
    intro.innerHTML = (resume.reglages_deplaces || 0)
      ? '<b>' + resume.reglages_deplaces + '</b> réglage' + (resume.reglages_deplaces > 1 ? 's' : '')
        + ' déplacé' + (resume.reglages_deplaces > 1 ? 's' : '') + ' sur ' + resume.reglages_disponibles
        + ' · ' + resume.articles_croises + ' articles croisés · ' + resume.trajets_tenables
        + '/' + resume.trajets + ' trajets tenables dans la fenêtre résiduelle'
        + ((resume.fentes_neutralisees || []).length ? ' · ' + resume.fentes_neutralisees.length
          + ' fente(s) verrouillée(s)' : '')
      : 'Aucun réglage institutionnel déplacé : chaque seuil reste à sa valeur de droit. '
        + resume.reglages_disponibles + ' réglages disponibles, ' + resume.articles_croises
        + ' articles croisés.';
  }
  const seuils = Object.values(NUANCES.seuils || {});
  const lignes_seuils = seuils.map(ligne => '<tr><td>' + ligne.nom
    + (ligne.note ? '<br><span class="aide">' + ligne.note + '</span>' : '')
    + '</td><td class="chiffre">' + ligne.article + '</td><td class="chiffre">'
    + fmt(ligne.statu_quo, 0) + ' ' + (ligne.unite || '') + '</td><td class="chiffre">'
    + fmt(ligne.regle, 0) + ' ' + (ligne.unite || '') + '</td><td class="chiffre">'
    + ecartHtml(ligne.ecart) + '</td><td>' + (ligne.reglages_appliques || []).join(', ')
    + '</td></tr>').join('');
  const delais = NUANCES.delais || {};
  const lignes_trajets = (delais.trajets || []).map(ligne => '<tr><td>' + ligne.nom
    + '</td><td class="chiffre">' + fmt(ligne.jours_de_rigueur_statu_quo, 0)
    + ' j</td><td class="chiffre">' + fmt(ligne.jours_de_rigueur_regles, 0) + ' j</td><td>'
    + (ligne.tenable_dans_la_fenetre ? '<span class="ok">tenable</span>'
       : '<span class="hors">hors fenêtre</span>') + '</td></tr>').join('');
  const indices = Object.values(NUANCES.indices || {});
  const puces_indices = indices.map(indice => '<span class="puce-indice" title="'
    + (indice.definition || '') + (indice.borne_appliquee ? ' — valeur bornée à 100' : '')
    + '">' + indice.nom + ' <b>' + fmt(indice.valeur, 1) + '</b> '
    + (indice.ecart ? ecartHtml(indice.ecart) : '') + '</span>').join('');
  const fentes = NUANCES.fentes || [];
  const lignes_fentes = fentes.map(fente => '<span class="puce-indice" title="'
    + (fente.condition_de_verrouillage || '') + '">' + fente.nom
    + ' · robustesse ' + fmt(fente.robustesse_reglee, 0)
    + (fente.neutralisee ? ' · <span class="hors">VERROUILLÉE par '
        + (fente.reglages_appliques || []).join(', ') + '</span>' : '') + '</span>').join('');
  const strates = (NUANCES.strates || []).map(ligne => '<tr><td class="chiffre">' + ligne.strate
    + '</td><td>' + ligne.libelle + '</td><td class="chiffre">' + (ligne.reglages || []).length
    + '</td><td class="chiffre">' + (ligne.reglages_actifs || []).length
    + '</td><td class="chiffre">' + (ligne.verrous_touches || []).length
    + '</td><td class="chiffre">' + (ligne.fentes_verrouillees || []).length + '</td></tr>').join('');
  const trous = [];
  const coherence = NUANCES.coherence || {};
  Object.keys(coherence).forEach(cle => {
    const valeur = coherence[cle];
    if (Array.isArray(valeur) && valeur.length && /sans|inconnu|non_|perimees|vides|anormaux|orphelins/.test(cle)){
      trous.push('<b>' + cle + '</b> : ' + valeur.join(', '));
    }
  });
  zone.innerHTML = (trous.length
      ? '<div class="garde-fous">Garde-fous de la couche : ' + trous.join(' · ')
        + ' — un trou vient de s\'ouvrir dans la couche, il doit être comblé.</div>'
      : '<div class="carte">Garde-fous au vert : aucun verrou sans explication, aucun réglage '
        + 'sans cible chiffrée, aucune fente ni trajet inatteignable, sur '
        + (coherence.reglages_catalogue || 0) + ' réglages et '
        + Object.keys(coherence.total_connaissances || {}).length + ' registres croisés.</div>')
    + '<h3 style="margin:10px 0 6px">Indices</h3><div>' + (puces_indices || '—') + '</div>'
    + '<h3 style="margin:12px 0 6px">Seuils recalculés</h3><table><thead><tr><th>Règle</th>'
    + '<th>Article</th><th>Droit</th><th>Réglé</th><th>Écart</th><th>Réglages appliqués</th>'
    + '</tr></thead><tbody>' + (lignes_seuils || '<tr><td colspan="6">Aucun seuil bougé.</td></tr>')
    + '</tbody></table>'
    + '<h3 style="margin:12px 0 6px">Délais de rigueur</h3><table><thead><tr><th>Trajet</th>'
    + '<th>Droit</th><th>Réglé</th><th>Fenêtre résiduelle</th></tr></thead><tbody>'
    + (lignes_trajets || '<tr><td colspan="4">—</td></tr>') + '</tbody></table>'
    + '<h3 style="margin:12px 0 6px">Fentes</h3><div class="fentes">'
    + (lignes_fentes || '—') + '</div>'
    + '<h3 style="margin:12px 0 6px">Cinq strates</h3><table><thead><tr><th>Strate</th><th>Niveau</th>'
    + '<th>Réglages</th><th>Déplacés</th><th>Verrous touchés</th><th>Fentes verrouillées</th>'
    + '</tr></thead><tbody>' + (strates || '<tr><td colspan="6">—</td></tr>') + '</tbody></table>'
    + '<p class="limites">Limites assumées de la couche : ' + (NUANCES.limites || []).join(' ') + '</p>';
}
/* Bloc « verrous » + réglages déplacés. Le principe reste le même que partout
   ailleurs dans la page : le navigateur ne calcule et ne décore aucun chiffre,
   il met en forme ce que `/api/nuances` a renvoyé. Les seules choses ajoutées
   sont des liens vers les fiches d'article servies par `/api/constitution`. */
function lienCitation(identifiant){
  /* Même transformation que `numerosArticle` pour les leviers : un identifiant de
     citation de la Constitution devient le lien vers la fiche servie par le serveur.
     « LOI_… », « DDHC_… », « REGLOC_… » n'ont pas de route dédiée : ils restent du
     texte brut, jamais un lien inventé qui renverrait un 404 au lecteur. */
  const brut = String(identifiant || '');
  if (!/^CONST_ART_/.test(brut)) return '<code>' + echapperTexte(brut || '—') + '</code>';
  const numero = brut.replace(/^CONST_ART_/, '').replace(/_/g, '-');
  if (!/^[0-9]+(-[0-9]+)*$/.test(numero)) return '<code>' + echapperTexte(brut) + '</code>';
  return '<a class="article" href="/api/constitution?article=' + encodeURIComponent(numero)
    + '" target="_blank" rel="noopener" title="Fiche de droit positif de l\'article ' + numero
    + ' — texte, chiffres vérifiés, bornes du modèle. Réponse du serveur, pas un calcul du simulateur.">'
    + echapperTexte(brut) + '</a>';
}
function pucesReglages(cles){
  const catalogue = (NUANCES && NUANCES.reglages) || {};
  return (cles || []).map(cle => '<span class="puce-reglage" title="'
    + echapperTexte((catalogue[cle] || {}).libelle || '') + '">'
    + echapperTexte(cle) + '</span>').join(' ');
}
function seuilVerrouHtml(verrou){
  if (verrou.seuil_statu_quo === undefined || verrou.seuil_statu_quo === null) return '';
  const fleche = verrou.ecart ? ' <span class="' + (verrou.ecart < 0 ? 'moins' : 'plus') + '">'
    + (verrou.ecart < 0 ? '−' : '+') + fmt(Math.abs(verrou.ecart), 0) + '</span>' : '';
  return '<span class="verrou-seuil">' + fmt(verrou.seuil_statu_quo, 0) + ' '
    + echapperTexte(verrou.unite || '') + ' → <b>' + fmt(verrou.seuil_regule, 0) + '</b>'
    + echapperTexte(verrou.unite || '') + fleche + '</span>';
}
function ligneVerrouHtml(verrou, classe, suiteHtml){
  return '<li class="' + classe + '"><span>' + lienCitation(verrou.article) + '</span>'
    + '<span>' + echapperTexte(verrou.nom) + '</span>' + seuilVerrouHtml(verrou)
    + (suiteHtml || '') + '</li>';
}
function renderVerrous(){
  const zone = document.getElementById('verrous-corps');
  const intro = document.getElementById('verrous-resume');
  if (!zone) return;
  const etat = (NUANCES && NUANCES.verrous) || null;
  if (!etat){
    if (intro) intro.innerHTML = '';
    zone.innerHTML = '<div class="carte">L\'état des verrous n\'a pas été renvoyé par '
      + '<code>/api/nuances</code> : la page préfère afficher cette absence plutôt que '
      + 'de reconstituer les chiffres côté navigateur.</div>';
    return;
  }
  const touches = (etat.touches || []).map(verrou => ligneVerrouHtml(verrou, 'touche',
    '<span>' + pucesReglages(verrou.reglages) + (verrou.note ? ' <span class="aide">'
      + echapperTexte(verrou.note) + '</span>' : '') + '</span>'));
  const intacts = (etat.intacts || []).map(verrou => ligneVerrouHtml(verrou, 'intact',
    (verrou.note && (verrou.reglages || []).length)
      ? '<span>' + pucesReglages(verrou.reglages) + '</span>' : ''));
  const hors = (etat.hors_reglage || []).map(verrou => ligneVerrouHtml(verrou, 'hors',
    '<span class="aide" title="' + echapperTexte(verrou.explication || '') + '">'
    + echapperTexte(verrou.explication || '') + '</span>'));
  const avertissements = (etat.avertissements || []).map(ligne => '<li class="touche"><span>'
    + lienCitation(ligne.article) + '</span><span>' + echapperTexte(ligne.nom)
    + ' — ' + echapperTexte(ligne.message) + '</span>' + pucesReglages(ligne.reglages)
    + '</li>').join('');
  if (intro){
    intro.innerHTML = '<b>' + touches.length + '</b> verrou(s) touché(s) · '
      + '<b>' + intacts.length + '</b> intact(s) · <b>' + hors.length
      + '</b> hors de portée d\'un curseur, sur ' + etat.total
      + ' règles de blocage au registre. Un verrou « hors réglage » n\'est pas un oubli : '
      + 'la colonne dit pourquoi il ne peut pas se décréter.';
  }
  zone.innerHTML = '<div class="verrou-groupe"><div class="verrou-titre">Touchés par le vecteur</div>'
    + '<ul>' + (touches.join('') || '<li class="intact">Aucun : chaque seuil est à sa valeur de droit.</li>')
    + '</ul></div>'
    + '<div class="verrou-groupe"><div class="verrou-titre">Intacts</div><ul>'
    + (intacts.join('') || '<li>—</li>') + '</ul></div>'
    + '<div class="verrou-groupe"><div class="verrou-titre">Hors réglage</div><ul>'
    + (hors.join('') || '<li>—</li>') + '</ul></div>'
    + (avertissements ? '<div class="garde-fous">Neutralisations en cours : '
        + avertissements + '</div>' : '');
}
function renderReglagesTouches(){
  const zone = document.getElementById('reglages-corps');
  if (!zone) return;
  const catalogue = (NUANCES && NUANCES.reglages) || {};
  const deplaces = Object.keys(catalogue).filter(cle => catalogue[cle].deplace);
  if (!deplaces.length){
    zone.innerHTML = '<div class="carte">Aucun réglage institutionnel déplacé : le droit '
      + 'positif est à son état default, rien n\'a donc d\'effet à montrer ici.</div>';
    return;
  }
  const groupes = ['verrou', 'fente', 'trajet', 'mecanisme', 'instance', 'strategie'];
  zone.innerHTML = deplaces.sort().map(cle => {
    const ligne = catalogue[cle];
    const parCategorie = {};
    (ligne.cibles || []).forEach(cible => {
      const categorie = groupes.indexOf(cible[0]) >= 0 ? cible[0] : 'autre';
      (parCategorie[categorie] = parCategorie[categorie] || []).push(cible[1]);
    });
    const badges = groupes.filter(groupe => parCategorie[groupe]).map(groupe =>
      '<span class="badge-cible" title="' + echapperTexte(parCategorie[groupe].join(', ')) + '">'
      + groupe + ' ' + parCategorie[groupe].length + '</span>').join('');
    const valeur = (ligne.type === 'interrupteur')
      ? (ligne.valeur ? 'activé' : 'éteint')
      : fmt(ligne.valeur, 0) + (ligne.unite ? ' ' + echapperTexte(ligne.unite) : '');
    return '<div class="reglage-touche"><b>' + echapperTexte(ligne.libelle || cle) + '</b> '
      + '<span class="aide">' + echapperTexte(cle) + '</span>'
      + '<div>valeur retenue : <b>' + valeur + '</b> (défaut ' + fmt(ligne.defaut, 0)
      + ', taux ' + fmt((ligne.taux || 0) * 100, 0) + ' %)'
      + (badges ? ' · touches : ' + badges : '')
      + (ligne.sans_geometrie ? ' · <i>' + echapperTexte(ligne.sans_geometrie) + '</i>' : '')
      + '</div>'
      + articlesHtml(ligne)
      + '</div>';
  }).join('');
}
function mesuresHtml(bulle){
  const blocs = (bulle.mesures || []).map(mesure => {
    const seuils = mesure.seuils || {};
    const population = seuils.population || {};
    const mouvementes = mesure.domaines_mouvementes || [];
    const negatifs = mouvementes.filter(domaine => domaine.delta < 0).length;
    const classes = [];
    if (negatifs) classes.push('bulle-aggrave');
    if (mouvementes.length - negatifs) classes.push('bulle-favorable');
    const domaines = mouvementes.length
      ? pucesDomaines(mouvementes, 20)
      : '<i>aucun des 20 domaines ne bouge au-delà de 0,2 pt</i>';
    const indicateurs = (mesure.indicateurs || []).slice(0, 4).map(indicateur =>
      `<li>${indicateur.libelle} : ${fmt(indicateur.valeur_reference, 2)} → ${fmt(indicateur.valeur, 2)} `
      + `${indicateur.unite || ''} (${indicateur.ecart > 0 ? '+' : ''}${fmt(indicateur.ecart, 2)})</li>`
    ).join('');
    const alertes = (seuils.alertes || []).slice(0, 4).map(alerte =>
      `<li class="bulle-alerte ${alerte.niveau}">${alerte.libelle} : ${alerte.valeur_texte} `
      + `${alerte.unite || ''} — ${alerte.message || ''} (${alerte.strate_libelle || ''})</li>`
    ).join('');
    const journal = (mesure.journal || []).slice(0, 4).map(ligne =>
      `<li>${ligne.strate ? `[${ligne.strate}] ` : ''}${ligne.texte}</li>`).join('');
    const risque = (population.risque === null || population.risque === undefined) ? ''
      : ` · risque population ${fmt(population.risque, 1)} (${population.niveau_libelle || '—'})`;
    return `<div class="bulle-mesure ${classes.join(' ')}">`
      + `<div><b>${mesure.nom}</b> · score moyen ${fmt(mesure.score_moyen, 1)} · `
      + `niveau ${seuils.niveau_global_libelle || '—'}${risque}</div>`
      + `<div>${domaines}</div>`
      + (indicateurs ? `<ul>${indicateurs}</ul>` : '')
      + (alertes ? `<ul>${alertes}</ul>` : '')
      + (journal ? `<ul class="bulle-journal">${journal}</ul>` : '')
      + `</div>`;
  }).join('');
  return `<div class="bulle-section"><span class="bulle-titre">Répercussions mesurées `
    + `(réglage isolé, autres leviers neutres)</span>${blocs}</div>`;
}
function lectureHtml(bulle){
  const lecture = bulle.lecture || {};
  const liste = (entrees, gabarit) => (entrees || []).map(gabarit).join('');
  const opportunites = liste(lecture.opportunites, entree =>
    `<li><b>${entree.libelle}</b> +${fmt(entree.gain, 1)} pt à « ${entree.mesure} »`
    + (entree.relais && entree.relais.length ? ` — via ${entree.relais.join(' ; ')}` : '') + '</li>');
  const desagrements = liste(lecture.desagrements, entree =>
    `<li><b>${entree.libelle}</b> ${fmt(entree.perte, 1)} pt à « ${entree.mesure} »`
    + (entree.relais && entree.relais.length ? ` — via ${entree.relais.join(' ; ')}` : '') + '</li>');
  const surveillance = liste(lecture.a_surveiller, entree =>
    `<li class="bulle-alerte ${entree.niveau || ''}">${entree.libelle}`
    + (entree.niveau_libelle ? ` — ${entree.niveau_libelle}` : '')
    + (entree.strate_libelle ? ` (${entree.strate_libelle})` : '')
    + ((entree.valeur_texte === undefined || entree.valeur_texte === null)
       ? '' : ` : ${entree.valeur_texte} ${entree.unite || ''}`)
    + ((entree.avant === undefined || entree.avant === null)
       ? '' : ` — ${fmt(entree.avant, 1)} → ${fmt(entree.apres, 1)}`) + '</li>');
  const compensations = liste(lecture.compensations, entree =>
    `<li>${entree.libelle} : ${(entree.leviers || []).map(levier => levier.libelle).join(', ')}</li>`);
  const bloc = (titre, contenu) => contenu
    ? `<div class="bulle-section"><span class="bulle-titre">${titre}</span><ul>${contenu}</ul></div>` : '';
  const bouge = (lecture.opportunites || []).length + (lecture.desagrements || []).length;
  return bloc('Opportunités', opportunites) + bloc('Désagréments', desagrements)
    + bloc('À surveiller (garde-fous et strates)', surveillance)
    + bloc('Pistes de compensation déclarées au catalogue', compensations)
    + (bouge ? '' : '<div class="bulle-section">Aucun domaine noté ne bouge aux bornes de ce '
        + 'réglage : voir la chaîne d\'interaction et le journal des strates.</div>');
}
/* ── Mesure live dans la bulle : coût / gain réel du réglage, rafraîchie dès
     le déplacement (mise à jour DOM directe, sans re-rendu de la grille). ── */
function coutGainHtml(budget, libelleMouvement){
  if (!budget) return '';
  const solde = budget.solde_delta_mde || 0;
  const classe = solde > 0.005 ? 'gain' : (solde < -0.005 ? 'cout' : 'neutre');
  const titre = solde > 0.005
    ? `Gain réel : <b class="chiffre">+${fmt(solde, 2)} Md€ / an</b>`
    : (solde < -0.005
       ? `Coût réel : <b class="chiffre">${fmt(solde, 2)} Md€ / an</b>`
       : 'Effet budgétaire net nul à ce réglage');
  const sources = (DERNIER_CONSEIL && DERNIER_CONSEIL.sources || [])
    .filter(s => s.valeur !== null && s.valeur !== undefined).slice(0, 6)
    .map(s => `${s.libelle} ${fmt(s.valeur, 2)} ${s.unite || ''} (${s.source || 'source officielle'})`)
    .join(' ; ');
  return `<div class="cout-gain ${classe}">
    <div>${titre}${libelleMouvement ? ` <span class="aide">— ${libelleMouvement}</span>` : ''}</div>
    <div class="detail">
      <span>Recettes : ${fmt(budget.recettes_delta_mde || 0, 2)} Md€</span>
      <span>Dépenses : ${fmt(budget.depenses_delta_mde || 0, 2)} Md€</span>
      <span>Déficit : ${budget.deficit_delta_pt_pib >= 0 ? '+' : ''}${fmt(budget.deficit_delta_pt_pib || 0, 2)} pt PIB</span>
      <span>Charge de la dette : ${fmt(budget.charge_dette_delta_mde || 0, 2)} Md€</span>
    </div>
    ${sources ? `<div class="trace">Ancré sur les sources officielles : ${sources}.</div>` : ''}
  </div>`;
}
function bulleLiveHtml(cle){
  if (DERNIER_CONSEIL && DERNIER_CONSEIL.cle === cle && DERNIER_CONSEIL.budget){
    return coutGainHtml(DERNIER_CONSEIL.budget,
                        (DERNIER_CONSEIL.mouvement || {}).phrase
                          ? (DERNIER_CONSEIL.mouvement.phrase.replace(/\*\*/g, '')) : '')
      + `<div class="bulle-note">Mesure recalculée en direct par le moteur à chaque déplacement `
      + 'du réglage (position avant → position actuelle) : ce bloc se rafraîchit dès le mouvement.</div>';
  }
  return '<div class="cout-gain neutre"><div>Déplacez ce curseur ou basculez cet interrupteur : '
    + 'le coût / gain réel de ce réglage précis s\'affichera ici immédiatement, en rouge ou vert.</div></div>';
}
function majBulleLive(){
  // Mise à jour immédiate du bloc live de la bulle ouverte, sans re-rendu :
  // indispensable pendant qu'un curseur est en cours de manipulation.
  if (BULLE_OUVERTE){
    const zone = document.getElementById('bulle-live');
    if (zone) zone.innerHTML = bulleLiveHtml(BULLE_OUVERTE);
  }
  majBadgeCoutLive();
}
/* Badge live sous le levier manipulé : coût / gain réel de ce réglage précis,
   visible immédiatement sans ouvrir la bulle. */
function badgeCoutLiveHtml(cle){
  if (!DERNIER_CONSEIL || DERNIER_CONSEIL.cle !== cle || !DERNIER_CONSEIL.budget) return '';
  const solde = DERNIER_CONSEIL.budget.solde_delta_mde || 0;
  if (Math.abs(solde) < 0.005){
    return '<div class="cout-live neutre">💶 Effet budgétaire de ce réglage : nul (mesuré par le moteur)</div>';
  }
  return solde > 0
    ? `<div class="cout-live gain">💶 Gain réel de ce réglage : +${fmt(solde, 2)} Md€ / an</div>`
    : `<div class="cout-live cout">💶 Coût réel de ce réglage : ${fmt(solde, 2)} Md€ / an</div>`;
}
function zoneCoutLiveHtml(cle){
  return `<div class="cout-live-zone">${badgeCoutLiveHtml(cle)}</div>`;
}
function majBadgeCoutLive(){
  // Écriture DOM directe : le badge du dernier levier déplacé est mis à jour
  // dès que le moteur a répondu, même si la grille n'est pas reconstruite.
  if (!DERNIER_CONSEIL || !DERNIER_CONSEIL.budget) return;
  const carte = document.querySelector(`.levier[data-cle="${DERNIER_CONSEIL.cle}"]`);
  if (!carte) return;
  let zone = carte.querySelector('.cout-live-zone');
  if (!zone){
    zone = document.createElement('div');
    zone.className = 'cout-live-zone';
    carte.appendChild(zone);
  }
  zone.innerHTML = badgeCoutLiveHtml(DERNIER_CONSEIL.cle);
}
function placeholderMesure(cle){
  // Retour immédiat dès le début du geste : le badge passe en « mesure en
  // cours » avant même la réponse du serveur.
  const carte = document.querySelector(`.levier[data-cle="${cle}"]`);
  if (!carte) return;
  let zone = carte.querySelector('.cout-live-zone');
  if (!zone){
    zone = document.createElement('div');
    zone.className = 'cout-live-zone';
    carte.appendChild(zone);
  }
  zone.innerHTML = '<div class="cout-live neutre">⏳ Mesure du coût / gain réel de ce mouvement…</div>';
}
/* Ce que la bulle explique en plus : la classe du levier, ce qu'elle signifie
   pour le budget, et pourquoi ce levier est rangé là plutôt qu'ailleurs. */
function classeBulleHtml(cle){
  const levier = levierParCle(cle);
  const fiche = levier ? ficheClasse(levier.classe) : null;
  if (!fiche) return '';
  const montant = Math.abs(Number(levier.facteur) || 0);
  const monetaire = montantUnitairePossible(levier);
  return `<div class="bulle-section"><span class="bulle-titre">Classe : `
    + `<span class="classe-pastille motif-${fiche.motif}" style="--couleur-classe:${fiche.couleur};`
    + `--fond-classe:${fiche.couleur_html};--teinte-motif:${fiche.couleur_html}">`
    + `<span class="symbole" aria-hidden="true">${fiche.symbole}</span>${echapperTexte(fiche.libelle)}</span></span>`
    + `<div class="classe-motif">${echapperTexte(fiche.question)} ${echapperTexte(fiche.verdict)}.</div>`
    + `<div class="classe-motif detail">Pourquoi cette classe : ${echapperTexte(levier.classe_motif || '')}</div>`
    + (monetaire && montant
       ? `<div class="classe-motif detail">Ordre de grandeur : <b>${fmtMenage(montant)}</b> `
         + `par unité réglée (${echapperTexte(statutDiviseur())}).</div>`
       : `<div class="classe-motif detail">Aucun montant budgétaire direct dans le modèle : `
         + `ce levier se juge sur ses effets institutionnels, pas sur une ligne de dépense.</div>`)
    + `<div class="classe-motif detail">Montée en charge déclarée : `
    + `${rampeHtml(levier.profil, fiche.couleur)}`
    + `${echapperTexte((levier.profil || []).map(valeur => Math.round(valeur * 100) + ' %').join(' · '))}</div>`
    + `</div>`;
}
function htmlBulle(bulle){
  return `<div class="bulle-levier">`
    + `<div class="bulle-titre">Bulle explicative — ${bulle.libelle} `
    + `(${bulle.famille_libelle}, ${bulle.type})</div>`
    + classeBulleHtml(bulle.cle)
    + `<div class="bulle-live" id="bulle-live">${bulleLiveHtml(bulle.cle)}</div>`
    + chaineHtml(bulle) + effetsDeclaresHtml(bulle) + mesuresHtml(bulle) + lectureHtml(bulle)
    + (bulle.sans_effet_mesure
       ? '<div class="bulle-section bulle-alerte">Aucun des 20 domaines notés ne bouge : les '
         + 'répercussions listées ci-dessus sont institutionnelles (strates 1 à 5).</div>' : '')
    + `<div class="bulle-note">${bulle.avertissement || ''}</div></div>`;
}
function bulleHtml(cle){
  if (BULLE_OUVERTE !== cle) return '';
  if (Object.prototype.hasOwnProperty.call(BULLES, cle)){
    return BULLES[cle]
      ? htmlBulle(BULLES[cle])
      : '<div class="bulle-levier bulle-chargement">Bulle indisponible : le serveur n\'a pas répondu.</div>';
  }
  return '<div class="bulle-levier bulle-chargement">Calcul des interactions en cours…</div>';
}
function bulleBoutonHtml(cle){
  const actif = BULLE_OUVERTE === cle;
  return `<button class="bulle-bouton${actif ? ' actif' : ''}" data-bulle="${cle}" `
    + `data-aide="<b>Bulle explicative</b>Ouvre la fiche du réglage : chaîne d'interaction `
    + '(médiateurs → indicateurs → domaines), répercussions mesurées à chaque borne, '
    + 'garde-fous et strates concernées, puis opportunités, désagréments et pistes de '
    + 'compensation. La fiche s\'ouvre dans la carte, sans recouvrir les leviers." '
    + `onclick="ouvrirBulle('${cle}')">`
    + `${actif ? '▾ interactions' : '▸ interactions'}</button>`;
}
async function chargerBulle(cle){
  if (Object.prototype.hasOwnProperty.call(BULLES, cle) || BULLES_DEMANDEES.has(cle)) return;
  BULLES_DEMANDEES.add(cle);
  try {
    const reponse = await fetch(`/api/bulle?levier=${encodeURIComponent(cle)}&detail=complet`);
    const donnees = await reponse.json();
    BULLES[cle] = (donnees && donnees.cle === cle) ? donnees : null;
  } catch (erreur){
    BULLES[cle] = null;
  }
  if (BULLE_OUVERTE === cle) renderLeviers(filtreCourant());
}
async function ouvrirBulle(cle){
  masquerInfobulle(); // la bulle ouverte devient l'aide : plus d'aide flottante
  if (BULLE_OUVERTE === cle){
    BULLE_OUVERTE = null;
    renderLeviers(filtreCourant());
    return;
  }
  BULLE_OUVERTE = cle;
  renderLeviers(filtreCourant());
  await chargerBulle(cle);
}
function puceHtml(effet){
  const sens = effet.effet_score > 0 ? 'amélioration' : 'dégradation';
  const texteAide = `<b>${effet.libelle}</b>Effet mesuré après votre dernière modification : ${sens} de `
    + `${fmt(Math.abs(effet.effet_score), 1)} pt de score (différences finies, réglage isolé, `
    + 'comparaison à la trajectoire neutre).';
  return `<span class="puce-effect ${effet.effet_score > 0 ? 'pos' : 'neg'}" data-aide="${texteAide}">`
    + `${effet.libelle} ${effet.effet_score > 0 ? '+' : ''}${fmt(effet.effet_score, 1)}</span>`;
}
function pucesHtml(cle){
  const effets = DERNIERES_PUCES[cle] || [];
  if (!effets.length) return '';
  return '<div class="puces">' + effets.map(puceHtml).join('') + '</div>';
}
function dateFrancaise(iso){ return iso ? String(iso).split('-').reverse().join('/') : ''; }
function badgeVerificationHtml(levier){
  const v = levier.verification || {};
  const statut = v.statut || 'non_verifie';
  const date = v.verifie_le ? ` (consulté le ${dateFrancaise(v.verifie_le)})` : '';
  const source = v.source_url ? ` · <a href="${echapperTexte(v.source_url)}" target="_blank" rel="noopener">source</a>` : '';
  return `<div class="vstatut vstatut-${statut}"><b>${echapperTexte(v.libelle || 'Non vérifié')}</b>${echapperTexte(date)}${source} · <a href="${echapperTexte(v.page || '#')}" target="_blank" rel="noopener">détail et contribution</a><div class="vnote">${echapperTexte(v.note || 'Statut non renseigné.')}</div></div>`;
}
function lireSaisie(cle){
  try { return JSON.parse(localStorage.getItem('mrsc-saisie-' + cle) || '{}'); } catch(e){ return {}; }
}
function ecrireSaisie(cle, champ, valeur){
  const donnees = lireSaisie(cle);
  donnees[champ] = valeur;
  try { localStorage.setItem('mrsc-saisie-' + cle, JSON.stringify(donnees)); } catch(e){}
  return donnees;
}
function texteSaisie(cle, unite){
  const d = lireSaisie(cle);
  const valeur = (d.valeur === undefined || d.valeur === '') ? 'aucune valeur saisie' : `${d.valeur} ${unite || ''}`;
  const source = d.source ? d.source : 'aucune source indiquée';
  return `VALEUR CITOYENNE NON VÉRIFIÉE PAR LE MRSC : ${valeur} (source : ${source}). Ce chiffre n'entre pas dans le calcul du simulateur.`;
}
function majSaisie(cle, champ, valeur, unite){
  ecrireSaisie(cle, champ, valeur);
  document.querySelectorAll(`[data-saisie-texte="${cle}"]`).forEach(el => { el.textContent = texteSaisie(cle, unite); });
}
function saisieCitoyenneHtml(levier){
  const v = levier.verification || {};
  if (v.statut === 'verifie') return '';
  const d = lireSaisie(levier.cle);
  const unite = levier.unite === 'bool' ? '' : levier.unite;
  return `<details class="saisie-citoyenne" data-cle="${levier.cle}">
      <summary>Noter ma propre valeur sourcée (non vérifiée par le MRSC)</summary>
      <label>Valeur citoyenne (${echapperTexte(unite)}) <input type="number" step="any" value="${d.valeur ?? ''}" oninput="majSaisie('${levier.cle}','valeur',this.value,'${echapperTexte(unite)}')"></label>
      <label>Lien vers la source officielle <input type="url" value="${echapperTexte(d.source || '')}" oninput="majSaisie('${levier.cle}','source',this.value,'${echapperTexte(unite)}')"></label>
      <div class="saisie-texte" data-saisie-texte="${levier.cle}">${echapperTexte(texteSaisie(levier.cle, unite))}</div>
      <div class="saisie-etiquette">VALEUR CITOYENNE NON VÉRIFIÉE — ${echapperTexte(levier.libelle)}</div>
    </details>`;
}
function nonVerifie(levier){ return (levier.verification && levier.verification.statut !== 'verifie') ? ' non-verifie' : ''; }
function renderLeviers(filtre){
  const recherche = (filtre || '').toLowerCase();
  const zones = CATALOGUE.parametres.familles.map(famille => {
    const leviers = famille.leviers.filter(levier =>
      (!CLASSE_FILTRE || levier.classe === CLASSE_FILTRE)
      && (!LEVIERS_MODIFIES_SEULS || LEVIERS_MODIFIES.has(levier.cle))
      && (!recherche || levier.libelle.toLowerCase().includes(recherche)
          || levier.description.toLowerCase().includes(recherche)
          || levier.cle.includes(recherche)));
    if (!leviers.length) return '';
    const contenu = leviers.map(levier => {
      const valeur = PARAMS[levier.cle];
      const modifie = LEVIERS_MODIFIES.has(levier.cle);
      const fiche = ficheClasse(levier.classe) || FICHE_CLASSE_DEFAUT;
      const valeurTexte = levier.type === 'interrupteur'
        ? (valeur >= 0.5 ? 'activé' : 'désactivé')
        : `${fmt(valeur, levier.precision)} ${levier.unite === 'bool' ? '' : levier.unite}`;
      const bouton = bulleBoutonHtml(levier.cle);
      const bascule = `<div class="ligne" data-aide-levier="${levier.cle}"><label class="bascule"><input type="checkbox" aria-label="${levier.libelle}" ${valeur >= 0.5 ? 'checked' : ''}
             onchange="majLevier('${levier.cle}', this.checked ? 1 : 0)"> ${levier.libelle}
             <span class="valeur" data-aide-levier="${levier.cle}">${valeurTexte}</span></label>${bouton}</div>`;
      const curseur = `<div class="ligne" data-aide-levier="${levier.cle}"><span class="nom" data-aide-levier="${levier.cle}">${levier.libelle}</span>
             <span class="valeur" data-aide-levier="${levier.cle}">${valeurTexte}</span>${bouton}</div>
           <input type="range" data-aide-levier="${levier.cle}" aria-label="${levier.libelle}" min="${levier.minimum}" max="${levier.maximum}" step="${levier.pas}"
                  value="${valeur}" oninput="majLevier('${levier.cle}', parseFloat(this.value))"
                  onchange="terminerReglage()">`;
      const curseurCompact = `<span class="nom" data-aide-levier="${levier.cle}">${levier.libelle}</span>
           <input type="range" data-aide-levier="${levier.cle}" aria-label="${levier.libelle}" min="${levier.minimum}" max="${levier.maximum}" step="${levier.pas}"
                  value="${valeur}" oninput="majLevier('${levier.cle}', parseFloat(this.value))"
                  onchange="terminerReglage()">
           <span class="valeur" data-aide-levier="${levier.cle}">${valeurTexte}</span>${bouton}`;
      if (VUE_COMPACTE){
        const contenuLevier = levier.type === 'interrupteur'
          ? `<span class="nom" data-aide-levier="${levier.cle}">${levier.libelle}</span>
             <label class="bascule" data-aide-levier="${levier.cle}"><input type="checkbox" data-aide-levier="${levier.cle}" aria-label="${levier.libelle}" ${valeur >= 0.5 ? 'checked' : ''}
               onchange="majLevier('${levier.cle}', this.checked ? 1 : 0); terminerReglage()"></label>
             <span class="valeur" data-aide-levier="${levier.cle}">${valeurTexte}</span>${bouton}`
          : curseurCompact;
        return `<div class="levier compact${modifie ? ' modifie' : ''}${nonVerifie(levier)}" data-cle="${levier.cle}"
          data-classe="${levier.classe}" data-motif="${fiche.motif}" data-aide-levier="${levier.cle}"
          style="--couleur-classe:${fiche.couleur};--fond-classe:${fiche.couleur_html};--teinte-motif:${fiche.couleur_html}">
          ${contenuLevier}${badgeVerificationHtml(levier)}${saisieCitoyenneHtml(levier)}${pucesHtml(levier.cle)}${zoneCoutLiveHtml(levier.cle)}${bulleHtml(levier.cle)}</div>`;
      }
      const commande = levier.type === 'interrupteur' ? bascule : curseur;
      const classeLigne = `<div class="classe-ligne">${pastilleClasse(levier.classe, true)}`
        + `<span class="rampe-legende">${echapperTexte(fiche.verdict)}</span>`
        + `${rampeHtml(levier.profil, fiche.couleur)}`
        + `<span class="rampe-legende">montée en charge</span></div>`;
      const ficheMenage = montantUnitairePossible(levier)
        ? `<div class="fiche-menage"><span>Ordre de grandeur : <b>${fmtMenage(Math.abs(Number(levier.facteur) || 0))}</b>`
          + ` par unité réglée</span><span class="statut">${echapperTexte(statutDiviseur())}</span>`
          + `<span>${echapperTexte(levier.classe_motif || '')}</span></div>`
        : `<div class="fiche-menage"><span>${levier.classe === 'monde'
             ? 'Hypothèse de contexte : ni recette ni dépense décidée ici.'
             : 'Aucun montant budgétaire direct : ce levier se juge sur ses effets, pas sur une ligne.'}</span>`
          + `<span>${echapperTexte(levier.classe_motif || '')}</span></div>`;
      return `<div class="levier${modifie ? ' modifie' : ''}${nonVerifie(levier)}"`
        + ` data-cle="${levier.cle}" data-classe="${levier.classe}" data-motif="${fiche.motif}"`
        + ` data-aide-levier="${levier.cle}"`
        + ` style="--couleur-classe:${fiche.couleur};--fond-classe:${fiche.couleur_html};--teinte-motif:${fiche.couleur_html}">
        ${commande}
        ${classeLigne}
        <div class="desc">${levier.description}</div>
        ${ficheMenage}
        ${levier.source ? `<div class="source">Source citée : ${levier.source}</div>` : ''}
        ${articlesHtml(levier)}
        ${badgeVerificationHtml(levier)}${saisieCitoyenneHtml(levier)}
        ${pucesHtml(levier.cle)}${zoneCoutLiveHtml(levier.cle)}${bulleHtml(levier.cle)}
      </div>`;
    }).join('');
    // Les classes présentes dans la famille : une famille peut en contenir
    // plusieurs (la fiscalité des ménages porte des recettes et des baisses de
    // prélèvements qui coûtent). On l'affiche au lieu de le cacher.
    const classesFamille = [];
    leviers.forEach(levier => { if (classesFamille.indexOf(levier.classe) < 0) classesFamille.push(levier.classe); });
    const tete = `<div class="tete-famille"><h3 style="color:${famille.couleur}">${famille.libelle}</h3>`
      + `<span>${classesFamille.map(cle => pastilleClasse(cle, true)).join(' ')}</span></div>`;
    return `<div class="famille${VUE_COMPACTE ? ' compacte' : ''}${classesFamille.length === 1 ? ' classee motif-' + ficheDe(classesFamille[0]).motif : ''}"`
      + `${classesFamille.length === 1 ? ` style="--couleur-classe:${ficheDe(classesFamille[0]).couleur};--fond-classe:${ficheDe(classesFamille[0]).couleur_html};--teinte-motif:${ficheDe(classesFamille[0]).couleur_html}"` : ''}>`
      + `${tete}${contenu}</div>`;
  }).join('');
  document.getElementById('leviers-grille').innerHTML = zones
    || '<div class="carte">Aucun levier ne correspond à cette recherche.</div>';
  const grille = document.getElementById('leviers-grille');
  grille.className = 'leviers-grille' + (VUE_COMPACTE ? ' compacte' : '');
  const affiches = (grille.innerHTML.match(/class="levier/g) || []).length;
  const compteur = document.getElementById('compteur-leviers');
  if (compteur){
    compteur.textContent = `${affiches} levier(s) affiché(s)`
      + (LEVIERS_MODIFIES.size ? ` · ${LEVIERS_MODIFIES.size} modifié(s)` : '')
      + (VUE_COMPACTE ? ' · vue compacte' : '');
  }
}
function filtrerLeviers(valeur){ renderLeviers(valeur); }
function terminerReglage(){
  // Le curseur vient d'être relâché : on peut reconstruire la grille sans
  // interrompre la manipulation, pour afficher les puces d'impact à jour.
  REGLAGE_EN_COURS = false;
  renderLeviers(filtreCourant());
}
function majLevier(cle, valeur){
  // La « décision » : on mémorise la position du réglage AVANT ce geste, pour
  // que le conseiller temps réel mesure exactement le dernier mouvement.
  if (!MOUVEMENT || MOUVEMENT.cle !== cle) MOUVEMENT = {cle: cle, avant: PARAMS[cle]};
  REGLAGE_EN_COURS = true;
  masquerInfobulle(); // le résultat live prime : rien ne doit le recouvrir
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
  // Retour immédiat dès le début du geste : le badge sous le levier passe en
  // « mesure en cours », puis la mesure réelle arrive du moteur.
  placeholderMesure(cle);
  if (BULLE_OUVERTE === cle){
    const zone = document.getElementById('bulle-live');
    if (zone) zone.innerHTML = '<div class="cout-gain neutre"><div>Mesure du coût / gain réel '
      + 'en cours… le moteur rejoue la trajectoire avec votre mouvement.</div></div>';
  }
}
let minuteur = null;
function planifierSimulation(){
  document.getElementById('badge-leviers').textContent =
    `${nombreLeviersActifs()} leviers actifs — calcul en cours…`;
  if (minuteur) clearTimeout(minuteur);
  minuteur = setTimeout(() => simuler(false), 180);
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
    card.setAttribute('data-aide', `<b>${scenario.nom}</b>${scenario.description}`
      + '<br>Cliquez pour rejouer ce scénario historique du dépôt (moteur d\'origine).');
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
    card.setAttribute('data-aide', `<b>${preset.libelle}</b>${preset.description}`
      + '<br>Cliquez pour charger ces réglages dans la console : chacun reste ensuite ajustable au curseur.');
    card.innerHTML = `<h3>${preset.libelle}</h3><p>${preset.description}</p>`;
    card.onclick = (ev) => chargerPreset(key, ev);
    grid.appendChild(card);
  });
}
function chargerPreset(cle, ev){
  const preset = CATALOGUE.parametres.presets[cle];
  if (!preset) return;
  if (cle === 'double_mandature') changerHorizon(10, false);
  PARAMS = Object.assign({}, CATALOGUE.parametres.defauts, preset.parametres);
  // Les leviers du préréglage sont marqués comme modifiés : on voit d'un coup
  // d'œil ce que le programme change, et où il faut ajuster.
  LEVIERS_MODIFIES = new Set(Object.keys(preset.parametres).filter(nom =>
    Math.abs((preset.parametres[nom] || 0) - (CATALOGUE.parametres.defauts[nom] || 0)) > 1e-9));
  renderLeviers(filtreCourant());
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
  const horizon = donnees.resultats.length;
  document.getElementById('grid-impact').innerHTML = `
    <div class="carte metric"><div class="libelle">Scénario historique</div>
      <div class="valeur">${donnees.nom}</div>
      <div class="delta neutre">résultats du moteur d'origine (${horizon} ans)</div></div>
    <div class="carte metric"><div class="libelle">Déficit année ${final.annee}</div>
      <div class="valeur">${fmt(final.ratio_deficit_pib, 2)} % PIB</div>
      <div class="delta ${couleurDelta(-final.ratio_deficit_pib)}">dette ${fmt(final.ratio_dette_pib, 1)} % PIB</div></div>
    <div class="carte metric"><div class="libelle">OAT 10 ans</div>
      <div class="valeur">${fmt(final.taux_oat_pct, 2)} %</div>
      <div class="delta neutre">spread ${fmt(final.spread_bund_bps, 0)} bps</div></div>
    <div class="carte metric"><div class="libelle">Tension sociale</div>
      <div class="valeur">${fmt(final.tension_sociale_locale, 1)}/100</div>
      <div class="delta neutre">confiance ${fmt(final.confiance_democratique, 1)}/100</div></div>`;
  renderTableau(donnees.resultats);
  const actifsMatures = {
    cycle_long: final.investissements_matures_mde || 0,
    capital_humain_proxy: final.capital_humain_mature_mde || 0,
    capacites_bitd_proxy: final.capacites_defense_matures_mde || 0,
  };
  renderBilanIntergenerationnel({synthese: {bilan_intergenerationnel: {
    annee_terminal: final.annee,
    dette_publique_mde: final.dette_nominale_mde,
    dette_publique_pct_pib: final.ratio_dette_pib,
    besoin_non_couvert_capital_public_mde: final.dette_technique_infrastructures_mde || 0,
    investissements_longs_engages_cumules_mde: final.investissements_longs_engages_cumules_mde || 0,
    actifs_arrives_a_maturite_mde: actifsMatures,
    risque_climat_annualise_hors_budget_mde: final.dommages_climat_subis_mde || 0,
    dommages_climat_evites_annualises_hors_budget_mde: final.dommages_climat_evites_mde || 0,
    note_methodologique: 'Composantes séparées, sans score synthétique ni pondération normative.'
  }}});
  changerHorizon(horizon, false);
  document.getElementById('badge-leviers').textContent =
    `scénario « ${donnees.nom} » — ${horizon} exercice(s) simulé(s)`;
  activerExports();
}

/* ── Lexique : le vocabulaire de la page, en français ordinaire ─────────────
   Le simulateur emploie des mots de métier (spread, PDE, point de base…). Ce
   lexique les définit sans jargon, les souligne dans les textes affichés et
   s'ouvre aussi en panneau complet. Rien n'est inventé ici : chaque définition
   renvoie à une grandeur réellement calculée par le modèle.                  */
let LEXIQUE = null;
let LEXIQUE_PAR_CLE = {};
let TABLE_TERMES = {};
let REGEX_TERMES = null;

function formeMarquable(forme){
  // On ne souligne ni les formes trop courtes (faux positifs en pagaille),
  // ni celles qui contiennent un chiffre (« 3 % », « OAT 10 ans »).
  if (!forme || forme.length < 3) return false;
  if (/[0-9]/.test(forme)) return false;
  return true;
}

function definirLexique(donnees){
  LEXIQUE = donnees;
  LEXIQUE_PAR_CLE = {};
  (donnees.termes || []).forEach(terme => { LEXIQUE_PAR_CLE[terme.cle] = terme; });
  TABLE_TERMES = {};
  const formes = [];
  (donnees.formes || []).forEach(item => {
    if (!formeMarquable(item.forme)) return;
    TABLE_TERMES[item.forme.toLowerCase()] = item.cle;
    formes.push(item.forme.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  });
  formes.sort((a, b) => b.length - a.length);
  // Bornes « lettre » et non « \b » : \b est ASCII, il se trompe sur « été ».
  REGEX_TERMES = formes.length
    ? new RegExp('(?<![\\p{L}\\d])(' + formes.join('|') + ')(?![\\p{L}\\d])', 'giu')
    : null;
}

async function chargerLexique(){
  if (LEXIQUE) return LEXIQUE;
  try {
    const reponse = await fetch('/api/lexique');
    const donnees = await reponse.json();
    if (donnees && donnees.termes) definirLexique(donnees);
  } catch (erreur){
    /* Le lexique est un confort : une route muette ne casse pas la page. */
  }
  return LEXIQUE;
}

function echapperAttribut(texte){
  return echapperTexte(texte || '').replace(/"/g, '&quot;');
}

function marquerUnTerme(trouve){
  const cle = TABLE_TERMES[trouve.toLowerCase()];
  const terme = cle ? LEXIQUE_PAR_CLE[cle] : null;
  if (!terme) return trouve;
  const aide = `<b>${echapperAttribut(terme.terme)}</b>${echapperAttribut(terme.definition)}`
    + (terme.repere ? `<br><i>Repère :</i> ${echapperAttribut(terme.repere)}` : '')
    + '<br><i>Du lexique — « 📖 Lexique » en haut de page pour tout lire.</i>';
  return `<span class="terme" data-aide="${aide}">${trouve}</span>`;
}

function baliserTermes(html){
  if (!REGEX_TERMES || !html) return html;
  const texte = String(html);
  // Déjà balisé : on ne réécrit pas par-dessus (sinon les balises s'imbriquent).
  if (texte.indexOf('class="terme"') !== -1) return texte;
  let sortie = '';
  let i = 0;
  while (i < texte.length){
    const ouvrant = texte.indexOf('<', i);
    if (ouvrant === -1){ sortie += texte.slice(i).replace(REGEX_TERMES, marquerUnTerme); break; }
    sortie += texte.slice(i, ouvrant).replace(REGEX_TERMES, marquerUnTerme);
    // On recopie la balise telle quelle : le « > » qui la ferme peut être
    // à l'intérieur d'un attribut (data-aide contient du HTML), donc on
    // parcourt la balise en respectant les guillemets au lieu de s'arrêter
    // au premier « > » venu — sinon on injecterait des balises dans un
    // attribut et la page serait cassée.
    let j = ouvrant + 1;
    let guillemet = null;
    while (j < texte.length){
      const caractere = texte[j];
      if (guillemet){
        if (caractere === guillemet) guillemet = null;
      } else if (caractere === '"' || caractere === "'"){
        guillemet = caractere;
      } else if (caractere === '>'){
        j += 1;
        break;
      }
      j += 1;
    }
    sortie += texte.slice(ouvrant, j);
    i = j;
  }
  return sortie;
}

function appliquerLexique(id){
  const zone = document.getElementById(id);
  if (!zone || !REGEX_TERMES) return;
  zone.innerHTML = baliserTermes(zone.innerHTML);
}

function marquerTextes(){
  if (!REGEX_TERMES) return;
  ['section-clair', 'clair-lignes', 'zone-alertes', 'console-corps', 'provenance']
    .forEach(appliquerLexique);
}

/* ── Modale : lexique et guide ──────────────────────────────────────────── */
function ouvrirModale(titre, contenuHtml){
  const overlay = document.getElementById('overlay');
  const corps = document.getElementById('modale-corps');
  const titreModale = document.getElementById('modale-titre');
  if (!overlay || !corps) return;
  if (titreModale) titreModale.textContent = titre;
  corps.innerHTML = contenuHtml || '';
  overlay.classList.add('visible');
  overlay.setAttribute('aria-hidden', 'false');
  masquerInfobulle();
}

function fermerModale(){
  const overlay = document.getElementById('overlay');
  if (!overlay) return;
  overlay.classList.remove('visible');
  overlay.setAttribute('aria-hidden', 'true');
}

function siClicDehors(evenement){
  if (evenement && evenement.target && evenement.target.id === 'overlay') fermerModale();
}

function rendreLexique(recherche){
  const corps = document.getElementById('modale-corps');
  if (!corps) return;
  if (!LEXIQUE){
    corps.innerHTML = '<div class="lexique-vide">Lexique en cours de chargement…</div>';
    return;
  }
  const motif = (recherche || '').trim().toLowerCase();
  const garder = terme => !motif
    || String(terme.terme).toLowerCase().includes(motif)
    || String(terme.definition).toLowerCase().includes(motif)
    || String(terme.repere).toLowerCase().includes(motif)
    || (terme.formes || []).some(forme => String(forme).toLowerCase().includes(motif));
  const libellesVoir = cles => (cles || [])
    .map(cle => (LEXIQUE_PAR_CLE[cle] || {}).terme || cle)
    .map(echapperTexte).join(' · ');
  const groupes = (LEXIQUE.categories || []).map(categorie => {
    const termes = (LEXIQUE.termes || []).filter(
      terme => terme.categorie === categorie.cle && garder(terme));
    if (!termes.length) return '';
    return `<div class="lexique-categorie">
      <h3>${echapperTexte(categorie.libelle)}</h3>
      <p>${echapperTexte(categorie.introduction)}</p>
      ${termes.map(terme => `<div class="lexique-terme">
        <div class="lexique-mot">${echapperTexte(terme.terme)}</div>
        <div>${echapperTexte(terme.definition)}</div>
        ${terme.repere ? `<div class="lexique-repere">Repère : ${echapperTexte(terme.repere)}</div>` : ''}
        ${(terme.voir || []).length ? `<div class="lexique-voir">Voir aussi : ${libellesVoir(terme.voir)}</div>` : ''}
      </div>`).join('')}
    </div>`;
  }).join('');
  const precision = motif
    ? ` — filtré par « ${echapperTexte(motif)} »`
    : ' — le jargon du simulateur, expliqué sans jargon.';
  corps.innerHTML =
    `<input class="lexique-recherche" id="lexique-champ" aria-label="Rechercher un terme du lexique"
       placeholder="Chercher un mot : spread, dette, pouvoir d'achat…"
       value="${echapperAttribut(recherche || '')}" oninput="filtrerLexique(this.value)">
     <div class="aide" style="margin-bottom:10px">${LEXIQUE.nombre} mot(s) sur ${LEXIQUE.total}${precision}</div>
     ${groupes || '<div class="lexique-vide">Aucun terme ne correspond à cette recherche.</div>'}`;
}

function filtrerLexique(valeur){
  rendreLexique(valeur);
  const champ = document.getElementById('lexique-champ');
  if (champ && typeof champ.focus === 'function'){
    champ.focus();
    if (typeof champ.setSelectionRange === 'function'){
      const fin = String(champ.value || '').length;
      champ.setSelectionRange(fin, fin);
    }
  }
}

async function ouvrirLexique(recherche){
  await chargerLexique();
  ouvrirModale('📖 Lexique — les mots du simulateur, en français ordinaire', '');
  rendreLexique(recherche || '');
  const champ = document.getElementById('lexique-champ');
  if (champ && typeof champ.focus === 'function') champ.focus();
}

/* ── Guide de démarrage : quatre étapes, pas de jargon ──────────────────── */
const ETAPES_GUIDE = [
  ['Vous êtes aux commandes',
   'Les réglages plus bas sont des décisions publiques possibles : un taux, une règle, une dépense. '
   + 'Bougez-en un seul et tout se recalcule — budget, dette, emploi, climat social. Rien n\'est '
   + 'envoyé nulle part : le calcul se fait sur le serveur, vos réglages restent votre affaire.'],
  ['Tout est comparé à une référence',
   'Le simulateur recalcule toujours, en parallèle, ce qui se passerait sans votre décision. Les '
   + 'chiffres affichés sont donc des ÉCARTS par rapport à cette référence : un score de 50 veut '
   + 'dire « aucun effet », ce n\'est ni une bonne ni une mauvaise note.'],
  ['La veille vous prévient',
   'Le bandeau collé en haut indique si la trajectoire franchit un seuil : tolérable, vigilance, '
   + 'risqué, hors-sol. Ce sont des repères du modèle — pas des seuils officiels, sauf quand la '
   + 'source est citée.'],
  ['Vérifiez tout',
   'Chaque donnée a une source, chaque indicateur une formule, chaque seuil un barème : tout est '
   + 'dans « 🔍 Audit &amp; traçabilité », en bas de page. Et gardez en tête la règle du dépôt : '
   + 'un modèle n\'est pas une prophétie.'],
];

function contenuGuide(){
  return ETAPES_GUIDE.map(([titre, texte], rang) =>
    `<div class="guide-etape"><h3>${rang + 1}. ${titre}</h3><p>${texte}</p></div>`).join('')
    + '<div class="guide-actions">'
    + '<button class="primaire" onclick="fermerModale()">Compris, commencer</button>'
    + '<button onclick="fermerModale();ouvrirLexique(\'\')">📖 Ouvrir le lexique</button>'
    + '</div>'
    + '<div class="aide" style="margin-top:10px">Vous pourrez rouvrir ce guide et le lexique à '
    + 'tout moment depuis les boutons en haut de page.</div>';
}

function ouvrirGuide(){
  ouvrirModale('❓ Comment lire ce simulateur', contenuGuide());
}

function guideDejaVu(){
  try {
    return typeof localStorage !== 'undefined'
      && localStorage.getItem('simulateur_guide_vu') === '1';
  } catch (erreur){
    return false; // navigation privée, stockage refusé : on montre le guide
  }
}

function marquerGuideVu(){
  try {
    if (typeof localStorage !== 'undefined') localStorage.setItem('simulateur_guide_vu', '1');
  } catch (erreur){ /* sans conséquence */ }
}

/* ── Réglages partageables par lien ─────────────────────────────────────────
   Un budget se discute : encore faut-il pouvoir le montrer. Le lien ne
   transporte que les leviers réellement déplacés, relus par-dessus les valeurs
   neutres à l'ouverture — quelques centaines de caractères, jamais les 101
   paramètres. Rien ne quitte le navigateur et rien n'est envoyé au serveur :
   l'adresse suffit, elle se colle dans un message ou un tract. */
function reglagesModifies(){
  const defauts = (CATALOGUE && CATALOGUE.parametres && CATALOGUE.parametres.defauts) || {};
  const modifies = {};
  Object.keys(PARAMS).forEach(cle => {
    if (PARAMS[cle] !== defauts[cle]) modifies[cle] = PARAMS[cle];
  });
  return modifies;
}

function lienReglages(){
  const modifies = reglagesModifies();
  const base = (window.location && window.location.origin ? window.location.origin : '')
    + (window.location && window.location.pathname ? window.location.pathname : '/');
  if (!Object.keys(modifies).length) return base;
  return base + '?sim=' + encodeURIComponent(JSON.stringify(modifies));
}

function reglagesDepuisLien(texte){
  /* Une adresse se transmet de main en main : on n'en croit jamais le contenu.
     Seuls les leviers réellement présents dans le catalogue sont repris, et
     seulement si la valeur est un nombre — jamais une chaîne, jamais une clé
     inconnue. Aucune valeur n'est injectée dans le HTML. */
  const defauts = (CATALOGUE && CATALOGUE.parametres && CATALOGUE.parametres.defauts) || {};
  const repris = {};
  if (!texte) return repris;
  let brut;
  try { brut = JSON.parse(texte); } catch (erreur){ return repris; }
  if (!brut || typeof brut !== 'object' || Array.isArray(brut)) return repris;
  Object.keys(brut).forEach(cle => {
    const valeur = brut[cle];
    if (Object.prototype.hasOwnProperty.call(defauts, cle)
        && typeof valeur === 'number' && isFinite(valeur)) repris[cle] = valeur;
  });
  return repris;
}

function avisLien(nombre){
  const zone = document.getElementById('avis-lien');
  if (!zone) return;
  zone.textContent = `Réglages repris du lien : ${nombre} levier`
    + (nombre > 1 ? 's' : '') + ' replacé' + (nombre > 1 ? 's' : '')
    + '. Modifiez-les, comparez, puis partagez à votre tour.';
  zone.hidden = false;
}

function appliquerLien(){
  /* Renvoie vrai si l'adresse portait des réglages : le programme de départ
     (« mandature ») est alors laissé de côté, sinon il s'ajouterait aux
     réglages repris et le lien ne décrirait plus ce que l'on a partagé. */
  const texte = (typeof URLSearchParams !== 'undefined' && window.location)
    ? new URLSearchParams(window.location.search).get('sim') : null;
  const repris = reglagesDepuisLien(texte);
  const nombre = Object.keys(repris).length;
  if (!nombre) return false;
  PARAMS = Object.assign({}, PARAMS, repris);
  avisLien(nombre);
  return true;
}

async function partagerReglages(){
  const lien = lienReglages();
  const bouton = document.getElementById('btn-partage');
  const libelle = bouton ? bouton.textContent : '';
  const pressePapiers = typeof navigator !== 'undefined' && navigator.clipboard
    && typeof navigator.clipboard.writeText === 'function';
  if (pressePapiers){
    try {
      await navigator.clipboard.writeText(lien);
      if (bouton){
        bouton.textContent = '✅ Lien copié';
        setTimeout(() => { bouton.textContent = libelle; }, 2500);
      }
      return lien;
    } catch (erreur){ /* repli : on montre l'adresse */ }
  }
  /* Sans presse-papiers accessible (navigation non chiffrée, vieux
     navigateur), l'adresse reste recopiable à la main. */
  if (typeof window !== 'undefined' && typeof window.prompt === 'function'){
    window.prompt('Copiez cette adresse : elle rouvre le simulateur sur vos réglages.', lien);
  }
  return lien;
}

/* ── Sommaire : situer le lecteur dans la page ──────────────────────────── */
function initialiserModale(){
  if (!document.addEventListener) return;
  document.addEventListener('keydown', evenement => {
    if (evenement && evenement.key === 'Escape') fermerModale();
  });
}

/* ── Sommaire repliable ───────────────────────────────────────────────────
   Sur téléphone, vingt ancres empilées repousseraient le contenu hors de
   l'écran : le bandeau s'ouvre à la demande, et reste en haut de page. Sur
   grand écran, le bouton n'existe pas (voir la feuille de style). */
function basculerSommaire(){
  const nav = document.getElementById('sommaire');
  const bouton = document.getElementById('sommaire-bascule');
  if (!nav || !nav.classList || !bouton) return;
  const ouverte = nav.classList.toggle('ouverte');
  if (bouton.setAttribute) bouton.setAttribute('aria-expanded', ouverte ? 'true' : 'false');
}

/* ── Les aides atteignables au doigt ──────────────────────────────────────
   Une infobulle s'ouvre au survol et au focus. Au doigt, ni l'un ni l'autre :
   les éléments annotés qui ne sont pas déjà un bouton, un lien ou un champ
   deviennent focalisables — sur appareil tactile seulement, pour ne pas
   ajouter vingt-sept arrêts de tabulation à un clavier d'ordinateur. */
function pointerGrossier(){
  return typeof window !== 'undefined' && typeof window.matchMedia === 'function'
    && window.matchMedia('(pointer:coarse)').matches === true;
}

function rendreAidesFocalisables(force){
  if (!document.querySelectorAll || typeof document.createElement !== 'function') return 0;
  if (force !== true && !pointerGrossier()) return 0;
  const aides = document.querySelectorAll('[data-aide], [data-aide-levier]');
  if (!aides || !aides.length || typeof aides.forEach !== 'function') return 0;
  const dejaFocalisables = ['button', 'a', 'input', 'select', 'textarea', 'summary'];
  let poses = 0;
  aides.forEach(function(noeud){
    if (!noeud.setAttribute) return;
    if (noeud.hasAttribute && noeud.hasAttribute('tabindex')) return;
    const balise = ('' + (noeud.tagName || '')).toLowerCase();
    if (dejaFocalisables.indexOf(balise) >= 0) return;
    noeud.setAttribute('tabindex', '0');
    poses += 1;
  });
  return poses;
}

/* ── Tableaux larges : la page ne déborde jamais ──────────────────────────
   Un tableau de 860 px posé dans un écran de 360 px ne rétrécit pas : il
   pousse tout le reste, et toute la page devient glissante. Chaque tableau
   large reçoit donc sa propre région défilante, nommée et atteignable au
   clavier. Le tableau lui-même n'est pas touché — les colonnes, les en-têtes
   et les chiffres restent ceux du moteur. */
function tableauDejaDefilant(tableau){
  let parent = tableau.parentElement;
  while (parent && parent !== document.body){
    const classes = (parent.classList && parent.className) || '';
    if (('' + classes).indexOf('tableau-defilant') >= 0
      || ('' + classes).indexOf('defilable') >= 0
      || ('' + classes).indexOf('tableau-strate') >= 0
      || ('' + classes).indexOf('modale-corps') >= 0
      || ('' + classes).indexOf('journal') >= 0
      || ('' + classes).indexOf('provenance') >= 0) return true;
    parent = parent.parentElement;
  }
  return false;
}

function rendreTableauxDefilants(){
  if (!document.querySelectorAll || typeof document.createElement !== 'function') return 0;
  const tableaux = document.querySelectorAll('table');
  if (!tableaux || !tableaux.length || typeof tableaux.forEach !== 'function') return 0;
  let poses = 0;
  tableaux.forEach(function(tableau){
    if (!tableau.parentNode || !tableau.parentNode.insertBefore) return;
    if (tableauDejaDefilant(tableau)) return;
    const enveloppe = document.createElement('div');
    enveloppe.className = 'tableau-defilant';
    enveloppe.setAttribute('role', 'region');
    enveloppe.setAttribute('tabindex', '0');
    const legende = tableau.getAttribute && tableau.getAttribute('data-legende');
    enveloppe.setAttribute('aria-label',
      (legende ? legende : 'Tableau de résultats') + ' — faites défiler horizontalement');
    tableau.parentNode.insertBefore(enveloppe, tableau);
    enveloppe.appendChild(tableau);
    poses += 1;
  });
  return poses;
}

function marquerSommaire(lien){
  if (!document.querySelectorAll) return;
  document.querySelectorAll('.sommaire a').forEach(ancre => ancre.classList.remove('actif'));
  if (lien && lien.classList) lien.classList.add('actif');
  // Choisir une destination referme le sommaire ouvert au doigt : la page
  // reste devant, l'utilisateur voit où il arrive.
  const nav = document.getElementById('sommaire');
  const bouton = document.getElementById('sommaire-bascule');
  if (nav && nav.classList && nav.classList.contains('ouverte')){
    nav.classList.remove('ouverte');
    if (bouton && bouton.setAttribute) bouton.setAttribute('aria-expanded', 'false');
  }
}

/* ── Imprimer son plan ────────────────────────────────────────────────────
   Le mode vit à l'écran autant que sur le papier : la page ne montre plus que
   le résumé, donc on voit ce qui s'imprimera avant de lancer l'impression. On
   ne parie pas sur le moment où le navigateur rend la main — l'appel est
   bloquant chez certains, asynchrone chez d'autres : la classe reste posée
   après `window.print()`, et c'est le bandeau qui relance l'impression ou
   ramène la page entière. */
function imprimerPlan(){
  const racine = document.documentElement;
  if (!racine || !racine.classList) return false;
  racine.classList.add('impression-plan');
  return lancerImpression();
}

function lancerImpression(){
  if (typeof window.print !== 'function') return false;
  try {
    window.print();
  } catch (erreur) {
    /* Impression refusée par le navigateur : le mode reste posé, le bandeau
       propose de réessayer ou de revenir — la page n'est pas abîmée. */
  }
  return true;
}

function quitterImpressionPlan(){
  const racine = document.documentElement;
  if (racine && racine.classList) racine.classList.remove('impression-plan');
  // Retour au bouton qui a ouvert le mode : le focus ne se perd pas dans une
  // barre qui vient de disparaître.
  const declencheur = document.getElementById('bouton-imprimer-plan');
  if (declencheur && typeof declencheur.focus === 'function') declencheur.focus();
  return true;
}

/* ── Lecture en clair ─────────────────────────────────────────────────────
   Le moteur produit des nombres exacts et illisibles. La section « Lire le
   résultat » les remet en phrases, à partir des mêmes chiffres — jamais à
   côté d'eux. Aucune phrase n'ajoute d'information absente de la sortie.   */
function renderLecture(donnees){
  const zoneResume = document.getElementById('clair-resume');
  const zoneLignes = document.getElementById('clair-lignes');
  const zoneLimites = document.getElementById('clair-limites');
  if (!zoneResume || !zoneLignes) return;
  const lecture = (donnees && donnees.lecture) || null;
  if (!lecture || !(lecture.lignes || []).length){
    zoneResume.textContent = 'La lecture en clair apparaît après la première simulation.';
    zoneLignes.innerHTML = '';
    if (zoneLimites) zoneLimites.innerHTML = '';
    return;
  }
  zoneResume.textContent = lecture.resume || '';
  zoneLignes.innerHTML = (lecture.lignes || []).map(ligne =>
    `<div class="clair-ligne niveau-${ligne.niveau || 'neutre'}">
       <div class="clair-tete">
         <span class="clair-grandeur">${echapperTexte(ligne.grandeur)}</span>
         <span class="clair-valeur">${echapperTexte(ligne.valeur)}</span>
       </div>
       <div>${echapperTexte(ligne.texte)}</div>
       <div class="clair-explication">${echapperTexte(ligne.explication || '')}</div>
     </div>`).join('');
  if (zoneLimites){
    zoneLimites.innerHTML = (lecture.limites || [])
      .map(limite => `<li>${echapperTexte(limite)}</li>`).join('');
  }
}

/* ── Simulation paramétrique ────────────────────────────────────────────── */
async function simuler(avecImpacts){
  const bouton = document.getElementById('btn-simuler');
  bouton.disabled = true;
  const parametresEnvoyes = Object.assign({}, PARAMS);
  const horizon = horizonCourant();
  try {
    const reponse = await fetch('/api/simuler', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({parametres: parametresEnvoyes, horizon: horizon,
                            avec_impacts: !!avecImpacts, max_impacts: 16})
    });
    const donnees = await reponse.json();
    if (donnees.error){ alert('Erreur de simulation : ' + donnees.error); return; }
    SORTIE = donnees;
    calculerClasses(donnees);
    renderImpact(donnees);
    renderLecture(donnees);
    renderBilanIntergenerationnel(donnees);
    renderStrates(donnees);
    renderOngletsStrates(donnees);
    renderTableau(donnees.etapes);
    renderGraphique(donnees.etapes);
    renderDomaines(donnees);
    renderMatrice(donnees);
    renderJournal(donnees);
    renderAlertes(donnees);
    renderConsole(donnees);
    renderCoutGlobal(donnees);
    // Les termes techniques des textes affichés deviennent lisibles au survol.
    marquerTextes();
    renderDerniereModification(SIMULATION_PRECEDENTE,
                               {parametres: parametresEnvoyes, sortie: donnees});
    majEffetsParLevier(donnees, SIMULATION_PRECEDENTE, parametresEnvoyes);
    majConseilTempsReel(parametresEnvoyes);
    rafraichirNuances();
    SIMULATION_PRECEDENTE = {parametres: parametresEnvoyes, sortie: donnees, horizon: horizon};
    // La grille est reconstruite avec ses puces d'impact — sauf pendant qu'un
    // curseur est manipulé, pour ne pas le remplacer sous les doigts.
    if (!REGLAGE_EN_COURS) renderLeviers(filtreCourant());
    document.getElementById('badge-leviers').textContent =
      `${nombreLeviersActifs()} leviers actifs · simulation ${horizon} ans · score moyen ${fmt(donnees.synthese.score_moyen_domaines,1)} (référence ${fmt(donnees.synthese.score_moyen_reference,1)})`;
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
/* Coût / gain réel des réglages globaux croisés : les flux budgétaires de
   l'ensemble des leviers actifs, croisés par le moteur, remis à jour à chaque
   simulation. Ancré sur les chiffres clefs des sources officielles. */
function renderCoutGlobal(donnees){
  const zone = document.getElementById('console-cout-global');
  const ruban = document.getElementById('ruban-cout');
  if (!zone) return;
  const synthese = donnees.synthese || {};
  const recettes = synthese.recettes_nouvelles_mde || 0;
  const depenses = synthese.depenses_nouvelles_mde || 0;
  const solde = synthese.solde_mesures_mde || 0;
  const actifs = nombreLeviersActifs();
  if (ruban){
    ruban.className = 'ruban-cout ' + (solde > 0.005 ? 'gain' : (solde < -0.005 ? 'cout' : 'neutre'));
    ruban.textContent = !actifs ? '💶 coût / gain réel : —'
      : (solde > 0.005 ? `💶 gain réel : +${fmt(solde, 1)} Md€/an`
         : (solde < -0.005 ? `💶 coût réel : ${fmt(solde, 1)} Md€/an`
            : '💶 effet net : 0 Md€'));
  }
  if (!actifs){
    zone.innerHTML = '<div class="cout-gain neutre"><div>Aucun levier actif : activez des réglages '
      + 'pour mesurer leur coût / gain réel croisé en temps réel.</div></div>';
    return;
  }
  const classe = solde > 0.005 ? 'gain' : (solde < -0.005 ? 'cout' : 'neutre');
  const titre = solde > 0.005
    ? `Gain réel du programme actif : <b class="chiffre">+${fmt(solde, 1)} Md€ / an</b>`
    : (solde < -0.005
       ? `Coût réel du programme actif : <b class="chiffre">${fmt(solde, 1)} Md€ / an</b>`
       : 'Programme actif : effet budgétaire net nul');
  const c = (CONTEXTE && CONTEXTE.contexte) || {};
  zone.innerHTML = `<div class="cout-gain ${classe}">
    <div>${titre} <span class="aide">(${actifs} levier(s) actif(s), effets croisés)</span></div>
    <div class="detail">
      <span>Recettes nouvelles : ${fmt(recettes, 1)} Md€</span>
      <span>Dépenses nouvelles : ${fmt(depenses, 1)} Md€</span>
      <span>Déficit final : ${fmt(synthese.deficit_final_pct, 2)} % PIB</span>
      <span>Dette finale : ${fmt(synthese.dette_finale_pct, 1)} % PIB</span>
    </div>
    <div class="trace">Recalculé à chaque mouvement, croisé avec les autres réglages — ancré sur :
      PIB ${fmt(c.pib_nominal_mde, 0)} Md€, OAT ${fmt(c.taux_oat_10ans, 2)} %,
      déficit constaté ${fmt(c.deficit_public_pct_pib, 1)} % PIB
      (sources officielles en bas de page).</div>
  </div>`;
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

  // Ruban collant : la même information en une ligne, pour que les leviers
  // restent visibles et cliquables pendant tout le réglage.
  const ruban = document.getElementById('ruban-veille');
  if (ruban){
    ruban.className = 'ruban-veille ' + classeNiveau(diagnostic.niveau_global);
    document.getElementById('ruban-verdict').textContent =
      `${etiquetteNiveau(diagnostic.niveau_global).toUpperCase()} · ${verdict.nombre_alertes || 0} alerte(s)`
      + (verdict.nombre_hors_sol ? ` · ${verdict.nombre_hors_sol} HORS-SOL` : '');
    document.getElementById('ruban-strates').innerHTML = (diagnostic.strates || []).map(strate =>
      `<span class="ruban-strate ${classeNiveau(strate.niveau)}"
             data-aide="<b>${strate.libelle}</b>${etiquetteNiveau(strate.niveau)} — ${strate.alertes.length} seuil(s) en alerte. Cliquez sur « détails » pour le détail des seuils.">S${strate.strate}</span>`
    ).join('');
    const risque = (diagnostic.population || {}).valeur;
    document.getElementById('ruban-population').innerHTML =
      `risque population <b class="${classeNiveau((diagnostic.population || {}).niveau)}">${fmt(risque, 0)}/100</b>`;
  }

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

function majEffetsParLevier(donnees, precedente, parametresEnvoyes){
  const puces = {};
  const modifies = new Set();
  if (precedente){
    Object.keys(parametresEnvoyes).forEach(cle => {
      if (Math.abs((parametresEnvoyes[cle] || 0) - (precedente.parametres[cle] || 0)) > 1e-9){
        modifies.add(cle);
      }
    });
    // Un seul levier touché : la variation de chaque domaine lui est
    // directement imputable, on peut donc la chiffrer sous son curseur.
    if (modifies.size === 1){
      const cle = [...modifies][0];
      const avantScores = {};
      (precedente.sortie.domaines || []).forEach(domaine => { avantScores[domaine.cle] = domaine.score; });
      const effets = (donnees.domaines || [])
        .map(domaine => ({libelle: domaine.libelle,
                          effet_score: domaine.score - (avantScores[domaine.cle] === undefined
                            ? 50 : avantScores[domaine.cle])}))
        .filter(effet => Math.abs(effet.effet_score) >= 0.1)
        .sort((a, b) => Math.abs(b.effet_score) - Math.abs(a.effet_score))
        .slice(0, 3);
      if (effets.length) puces[cle] = effets;
    }
  }
  // « Simuler avec impacts croisés » : le modèle fournit l'effet marginal de
  // chaque levier actif, domaine par domaine — on l'affiche sous le curseur.
  (donnees.impacts || []).forEach(impact => {
    const effets = (impact.effets || [])
      .filter(effet => Math.abs(effet.effet_score) >= 0.1)
      .sort((a, b) => Math.abs(b.effet_score) - Math.abs(a.effet_score))
      .slice(0, 3)
      .map(effet => ({libelle: effet.libelle, effet_score: effet.effet_score}));
    if (effets.length){
      puces[impact.levier] = effets;
      modifies.add(impact.levier);
    }
  });
  DERNIERES_PUCES = puces;
  LEVIERS_MODIFIES = modifies;
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

/* ── Conseiller temps réel (« effet papillon ») ────────────────────────────
   À chaque simulation déclenchée par un mouvement de réglage, on demande au
   serveur de rejouer le moteur avec le levier à sa position d'avant le geste
   puis à sa position à l'instant T : la différence est exactement celle de la
   décision. Le panneau rend effets directs, ricochets, garde-fous basculés,
   journal nouveau et pistes de compensation — pour TOUS les leviers.        */
async function majConseilTempsReel(parametresEnvoyes){
  const zone = document.getElementById('console-conseil');
  if (!zone) return;
  if (!MOUVEMENT) return;
  const cle = MOUVEMENT.cle;
  const apres = parametresEnvoyes[cle];
  if (apres === undefined || Math.abs(apres - MOUVEMENT.avant) < 1e-9) return;
  try {
    const reponse = await fetch('/api/conseil', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({parametres: parametresEnvoyes, cle: cle,
                            avant: MOUVEMENT.avant, apres: apres,
                            horizon: horizonCourant()})
    });
    const conseil = await reponse.json();
    // Le conseil affiché correspond au dernier mouvement réellement demandé.
    if (conseil && !conseil.error && MOUVEMENT && MOUVEMENT.cle === cle){
      DERNIER_CONSEIL = conseil;
      renderConseil(conseil);
      // Rafraîchissement immédiat de la bulle du réglage déplacé : le coût /
      // gain réel doit être lisible dès la fin du mouvement, sans clic.
      majBulleLive();
    }
  } catch (erreur){
    /* Le conseil est un confort : un serveur muet ne casse pas la page. */
  }
}
function renderConseil(conseil){
  const zone = document.getElementById('console-conseil');
  if (!zone) return;
  const niveau = conseil.verdict_niveau || 'inconnu';
  const domaines = (conseil.domaines || []);
  const directs = domaines.filter(d => d.direct);
  const ricochets = domaines.filter(d => !d.direct);
  const ligneDomaine = d =>
    `<div class="delta-mesure"><span>${d.direct ? '→ ' : '🦋 '}${d.libelle}</span>
       <span class="valeur ${d.favorable ? 'delta hausse' : 'delta baisse'}">
         ${d.delta > 0 ? '+' : ''}${fmt(d.delta, 1)} pt ${d.favorable ? '✓' : '✗'}</span></div>`;
  const grandeurs = (conseil.grandeurs || []).map(g =>
    `<div class="delta-mesure"><span>${g.libelle} : ${fmt(g.avant, g.precision)} → ${fmt(g.apres, g.precision)}</span>
       <span class="valeur ${g.favorable ? 'delta hausse' : 'delta baisse'}">
         ${g.delta > 0 ? '+' : ''}${fmt(g.delta, g.precision)} ${g.favorable ? '✓' : '✗'}</span></div>`).join('');
  const gardes = (conseil.garde_fous || []).map(g =>
    `<div class="delta-mesure"><span>${g.libelle}</span>
       <span class="etiquette ${classeNiveau(g.niveau_avant)}">${etiquetteNiveau(g.niveau_avant)}</span>
       <span class="valeur">→</span>
       <span class="etiquette ${classeNiveau(g.niveau_apres)}">${etiquetteNiveau(g.niveau_apres)}</span></div>
     <div class="aide">${g.message}</div>`).join('');
  const journal = (conseil.journal || []).map(m => `<div class="aide">• ${m}</div>`).join('');
  const comp = (conseil.compensations || []).map(c =>
    `<span class="puce-effect pos" data-aide="<b>Piste de compensation</b>${c.libelle} : effet déclaré favorable au domaine dégradé (catalogue).">${c.libelle}</span>`).join(' ');
  zone.innerHTML =
    `<div class="message-seuil ${classeNiveau(niveau)}">
       <div class="tete"><span>${conseil.mouvement ? conseil.mouvement.phrase.replace(/\*\*/g, '') : conseil.libelle}</span>
         <span class="etiquette ${classeNiveau(niveau)}">${etiquetteNiveau(niveau)}</span></div>
       <p class="aide">${conseil.lecture || ''}</p>
     </div>`
    + (conseil.budget ? coutGainHtml(conseil.budget, 'coût / gain réel de ce mouvement') : '')
    + (directs.length ? `<div class="aide"><b>Effets directs :</b></div>` + directs.map(ligneDomaine).join('') : '')
    + (ricochets.length ? `<div class="aide"><b>Par ricochet (effet papillon) :</b></div>` + ricochets.map(ligneDomaine).join('') : '')
    + (grandeurs ? `<div class="aide"><b>Grandeurs qui basculent :</b></div>` + grandeurs : '')
    + (gardes ? `<div class="aide"><b>Garde-fous :</b></div>` + gardes : '')
    + (journal ? `<div class="aide"><b>Signaux nouveaux :</b></div>` + journal : '')
    + (comp ? `<div class="aide"><b>Pistes de compensation :</b> ${comp}</div>` : '');
}

function renderImpact(donnees){
  const s = donnees.synthese;
  const anneeTerminale = donnees.horizon || donnees.etapes?.length || 5;
  const cartes = [
    [`Recettes nouvelles (an ${anneeTerminale})`, fmt(s.recettes_nouvelles_mde, 1) + ' Md€', 'mesures activées'],
    [`Dépenses nouvelles (an ${anneeTerminale})`, fmt(s.depenses_nouvelles_mde, 1) + ' Md€', 'mesures activées'],
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
      `PIB année ${anneeTerminale} vs référence`],
    ['Domaines en hausse', String(s.nombre_domaines_en_hausse), `${s.nombre_domaines_en_baisse} en baisse`],
  ];
  document.getElementById('grid-impact').innerHTML = cartes.map(([libelle, valeur, sous]) =>
    `<div class="carte metric"><div class="libelle">${libelle}</div><div class="valeur">${valeur}</div>
      <div class="delta neutre">${sous}</div></div>`).join('');
}
function renderBilanIntergenerationnel(donnees){
  const zone = document.getElementById('bilan-intergenerationnel');
  const bilan = donnees.synthese?.bilan_intergenerationnel;
  if (!zone || !bilan) return;
  const actifs = bilan.actifs_arrives_a_maturite_mde || {};
  const cartes = [
    ['Dette publique', `${fmt(bilan.dette_publique_mde, 1)} Md€`, `${fmt(bilan.dette_publique_pct_pib, 1)} % PIB`],
    ['Besoin de patrimoine non couvert (proxy)', `${fmt(bilan.besoin_non_couvert_capital_public_mde, 1)} Md€`, 'pas une dette comptable'],
    ['Investissements longs engagés', `${fmt(bilan.investissements_longs_engages_cumules_mde, 1)} Md€`, 'cumul des flux modélisés'],
    ['Cycle long arrivé à maturité', `${fmt(actifs.cycle_long, 1)} Md€`, 'stock modèle, pas rendement observé'],
    ['Capital humain arrivé à maturité', `${fmt(actifs.capital_humain_proxy, 1)} Md€`, 'proxy sans rendement PIB présumé'],
    ['Capacités BITD arrivées à maturité', `${fmt(actifs.capacites_bitd_proxy, 1)} Md€`, 'proxy de calendrier LPM'],
    ['Risque climatique annualisé', `${fmt(bilan.risque_climat_annualise_hors_budget_mde, 2)} Md€`, 'hors déficit APU'],
    ['Dommages climatiques évités (proxy)', `${fmt(bilan.dommages_climat_evites_annualises_hors_budget_mde, 2)} Md€`, 'hors recettes publiques'],
  ];
  zone.innerHTML = cartes.map(([libelle, valeur, sous]) =>
    `<div class="carte metric"><div class="libelle">${libelle}</div><div class="valeur">${valeur}</div>
      <div class="delta neutre">${sous}</div></div>`).join('')
    + `<div class="source-note" style="grid-column:1/-1">${bilan.note_methodologique || ''} Données et hypothèses : audit de traçabilité et R&D P16-P21.</div>`;
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
    const texteAide = `<b>${domaine.libelle}</b>${domaine.description}<br>`
      + `score ${fmt(domaine.score, 1)}/100 — écart à la référence ${ecart >= 0 ? '+' : ''}${fmt(ecart, 1)} pt `
      + `(50 = aucune politique ; « sans politique » = tendance spontanée du modèle).<br>`
      + `${domaine.indicateurs.length} indicateur(s) chiffré(s), chacun avec sa source.`;
    return `<div class="domaine" data-aide="${texteAide}" style="border-top:3px solid ${domaine.couleur}">
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
let DERNIERE_MATRICE = '';
function renderMatrice(donnees){
  const zone = document.getElementById('matrice-impacts');
  if (!zone) return;
  const fraicheur = document.getElementById('matrice-fraicheur');
  const impacts = donnees.impacts || [];
  if (!impacts.length){
    // Pendant qu'un curseur bouge, la matrice exigerait une simulation par
    // levier : l'écran se figerait. On garde la dernière matrice calculée et
    // on l'annonce, plutôt que d'effacer l'information sous les yeux.
    if (DERNIERE_MATRICE){
      zone.innerHTML = DERNIERE_MATRICE;
      if (fraicheur) fraicheur.textContent = 'dernière matrice calculée — « Simuler avec impacts croisés » la remet à jour';
      return;
    }
    zone.innerHTML =
      '<tbody><tr><td>Aucun levier actif : activez des leviers puis lancez « Simuler avec impacts croisés ».</td></tr></tbody>';
    if (fraicheur) fraicheur.textContent = 'en attente d\'une simulation complète';
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
  DERNIERE_MATRICE = html + '</tbody>';
  zone.innerHTML = DERNIERE_MATRICE;
  if (fraicheur) fraicheur.textContent = 'calculée à la dernière simulation complète';
}
function renderJournal(donnees){
  const lignes = (donnees.journal || []).map(texte => `<div>${texte}</div>`).join('');
  document.getElementById('journal').innerHTML = lignes || '<div>Journal vide.</div>';
}

/* ── Actions ────────────────────────────────────────────────────────────── */
function reinitialiser(){
  PARAMS = Object.assign({}, CATALOGUE.parametres.defauts);
  DERNIERES_PUCES = {};
  LEVIERS_MODIFIES = new Set();
  renderLeviers(filtreCourant());
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
/* ── Audit & traçabilité : tout le recoupement, à livre ouvert ─────────────
   Chaque bloc rend des données déjà chargées (catalogue, contexte) ou le
   barème des garde-fous : aucun chiffre n'avance sans sa source. */
function echapperTexte(texte){
  return String(texte === null || texte === undefined ? '' : texte)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
function auditSourcesHtml(){
  const contexte = (CONTEXTE && CONTEXTE.contexte) || {};
  const provenance = contexte.provenance || {};
  const lignes = Object.keys(provenance).map(cle => {
    const fiche = provenance[cle];
    const valeur = contexte[cle];
    const url = fiche.url
      ? ` <a href="${echapperTexte(fiche.url)}" rel="noopener">consulter</a>` : '';
    return `<tr><td>${echapperTexte(fiche.libelle)}</td>
      <td class="chiffre">${valeur === null || valeur === undefined ? '—' : fmt(valeur, 2)} ${echapperTexte(fiche.unite || '')}</td>
      <td>${echapperTexte(fiche.periode || '—')}</td>
      <td>${echapperTexte(fiche.statut || '')}</td>
      <td class="source-note">${echapperTexte(fiche.source || '')}${url}</td>
      <td class="source-note">${echapperTexte(fiche.licence || '')}</td></tr>`;
  }).join('');
  return `<table><thead><tr><th>Grandeur d'entrée</th><th>Valeur retenue</th><th>Période</th>
    <th>Statut</th><th>Source</th><th>Licence</th></tr></thead><tbody>${lignes}</tbody></table>
    <div class="source-note" style="margin-top:6px">« live » = valeur relevée sur l'API publique
    officielle à l'instant T ; « référence » = valeur documentaire du dépôt (le serveur n'a pas
    pu interroger l'API). Le bouton « Rafraîchir les données » relève les valeurs depuis votre
    navigateur et les transmet au simulateur : le recoupement est toujours possible.</div>`;
}
function auditDomainesHtml(){
  const domaines = (CATALOGUE && CATALOGUE.domaines) || [];
  return domaines.map(domaine => {
    const indicateurs = (domaine.indicateurs || []).map(indicateur =>
      `<tr><td>${echapperTexte(indicateur.libelle)}</td>
       <td class="formule">${echapperTexte(indicateur.formule)}</td>
       <td class="chiffre">${echapperTexte(indicateur.unite || '')} (${indicateur.sens > 0 ? 'hausse = amélioration' : 'hausse = dégradation'})</td>
       <td class="source-note">${echapperTexte(indicateur.source || '')}</td></tr>`).join('');
    return `<div style="margin-bottom:12px"><b style="color:${domaine.couleur}">${echapperTexte(domaine.libelle)}</b>
      <span class="source-note">— ${echapperTexte(domaine.description || '')}</span>
      <table><thead><tr><th>Indicateur</th><th>Formule du score</th><th>Unité et sens</th>
      <th>Source</th></tr></thead><tbody>${indicateurs}</tbody></table></div>`;
  }).join('');
}
function auditLeviersHtml(){
  const familles = ((CATALOGUE && CATALOGUE.parametres) || {}).familles || [];
  return familles.map(famille => {
    const leviers = (famille.leviers || []).map(levier => {
      const effets = Object.entries(levier.effets_directs || {})
        .map(([theme, coefficient]) => `${echapperTexte(theme)} ${coefficient > 0 ? '+' : ''}${fmt(coefficient, 2)}`)
        .join(', ') || '—';
      return `<tr><td>${echapperTexte(levier.libelle)} <span class="source-note">(${echapperTexte(levier.type)})</span></td>
        <td>${echapperTexte(levier.champ || '')} ${echapperTexte(levier.ligne || '')}</td>
        <td>${effets}</td>
        <td class="source-note">${echapperTexte(levier.source || '')}</td>
        <td>${echapperTexte((levier.verification || {}).libelle || '')} <span class="source-note">${echapperTexte((levier.verification || {}).verifie_le || '')}</span></td></tr>`;
    }).join('');
    return `<div style="margin-bottom:12px"><b>${echapperTexte(famille.libelle || famille.cle)}</b>
      <table><thead><tr><th>Levier</th><th>Champ / ligne budgétaire</th>
      <th>Effets déclarés (thème, coefficient)</th><th>Source</th><th>Statut de vérification</th></tr></thead>
      <tbody>${leviers}</tbody></table></div>`;
  }).join('');
}
function auditGardeFousHtml(bareme){
  const lignes = (bareme.garde_fous || []).map(garde => {
    const bornes = (garde.bornes || []).map(borne =>
      `${borne.seuil === null || borne.seuil === undefined ? '∞' : fmt(borne.seuil, garde.precision)} `
      + `→ ${echapperTexte((bareme.libelles_niveaux || {})[borne.niveau] || borne.niveau)}`
    ).join(' ; ');
    return `<tr><td>${echapperTexte(garde.libelle)}${garde.en_ecart ? ' <span class="source-note">(écart)</span>' : ''}</td>
      <td>${echapperTexte(garde.strate_libelle || ('strate ' + garde.strate))}</td>
      <td>${echapperTexte(bornes)}</td>
      <td class="chiffre">${echapperTexte(garde.unite || '')}</td>
      <td class="source-note">${echapperTexte(garde.source || '')}</td></tr>`;
  }).join('');
  return `<table><thead><tr><th>Grandeur surveillée</th><th>Strate</th>
    <th>Seuils (valeur → niveau)</th><th>Unité</th><th>Source institutionnelle</th></tr></thead>
    <tbody>${lignes}</tbody></table>`;
}
function auditMethodesHtml(){
  const nbLeviers = (((CATALOGUE || {}).parametres || {}).defauts
                     ? Object.keys(CATALOGUE.parametres.defauts).length : 0);
  const nbDomaines = ((CATALOGUE || {}).domaines || []).length;
  // Préréglages et scénarios sont comptés comme les leviers : lus dans les
  // données servies, jamais écrits en dur dans la phrase qui les annonce.
  const nbPresets = Object.keys((CATALOGUE || {}).presets || {}).length;
  const nbScenarios = Object.keys(SCENARIOS || {}).length;
  const nbIndicateurs = ((CATALOGUE || {}).domaines || [])
    .reduce((somme, domaine) => somme + (domaine.indicateurs || []).length, 0);
  return `<ul style="margin-left:16px;line-height:1.7">
    <li><b>Scores 0-100 :</b> chaque domaine est noté par rapport à la trajectoire de référence
      (aucun levier actif) : 50 = aucune politique. Les écarts sont des écarts de politique
      publique, jamais des prophéties.</li>
    <li><b>Dynamiques croisées :</b> la matrice levier × domaine est calculée par le moteur par
      <b>différences finies</b> (chaque levier actif est rejoué isolément et comparé à la
      trajectoire neutre) : aucun coefficient d'interaction n'est saisi à la main.</li>
    <li><b>Conseiller temps réel :</b> chaque mouvement de réglage rejoue deux simulations
      complètes (levier à sa position d'avant, puis d'après le geste, toutes choses égales) ;
      la différence affichée est exactement celle de la décision, effets directs et ricochets
      compris.</li>
    <li><b>Périmètre chiffré :</b> ${nbLeviers} leviers, ${nbDomaines} domaines,
      ${nbIndicateurs} indicateurs (formule + source), 31 garde-fous (26 absolus + 5 en écart),
      ${nbPresets} préréglages, ${nbScenarios} scénarios.</li>
    <li><b>Hypothèses P16-P21 (scénarios, pas observations) :</b> patrimoine : 145/24 = 6,04 Md€/an,
      annualisation exploratoire des 140-150 Md€ de besoins à 2050 ; climat : 143/30 = 4,77 Md€/an
      de pertes moyennes (hors budget APU), avec le ratio Barnier 8/30 annualisé uniquement comme
      hypothèse de prévention ; maturités capital humain / BITD : 8 / 6 ans, sans rendement PIB ni
      effet automatique sur le spread ; saturation administrative : seuil 8, hypothèse de stress-test.
      Sources : <a href="https://www.ccomptes.fr/sites/default/files/2024-04/NEB-2023-Gestion-patrimoine-immobilier-Etat.pdf" rel="noopener">Cour des comptes</a>,
      <a href="https://www.ecologie.gouv.fr/sites/default/files/documents/PNACC3.pdf" rel="noopener">PNACC-3</a>,
      <a href="https://www.defense.gouv.fr/sites/default/files/ministere-armees/LPM.pdf" rel="noopener">LPM 2024-2030</a> et
      <a href="https://www.insee.fr/fr/statistiques/9004289" rel="noopener">projections INSEE 2026</a>.
      Les coefficients/délais qui ne sont pas des observations restent explicitement exploratoires.</li>
    <li><b>Calibrage :</b> les grandeurs d'entrée (PIB, dette, OAT, BCE, inflation, chômage,
      Brent, change) proviennent des API publiques officielles listées au bloc 1 ; les
      multiplicateurs et élasticités sont cités dans chaque formule (bloc 2).</li>
    <li><b>Code :</b> le moteur, le barème, le catalogue et cette page sont dans le dépôt
      (Python standard, sans dépendance externe) : chaque formule affichée ici correspond à une
      fonction du code, vérifiable ligne à ligne.</li>
  </ul>`;
}
async function chargerAudit(){
  const zoneSources = document.getElementById('audit-sources');
  const zoneDomaines = document.getElementById('audit-domaines');
  const zoneLeviers = document.getElementById('audit-leviers');
  const zoneGardes = document.getElementById('audit-gardefous');
  const zoneMethodes = document.getElementById('audit-methodes');
  try {
    if (zoneSources) zoneSources.innerHTML = auditSourcesHtml();
    if (zoneDomaines) zoneDomaines.innerHTML = auditDomainesHtml();
    if (zoneLeviers) zoneLeviers.innerHTML = auditLeviersHtml();
    if (zoneMethodes) zoneMethodes.innerHTML = auditMethodesHtml();
    if (zoneGardes){
      const reponse = await fetch('/api/garde_fous');
      const bareme = await reponse.json();
      zoneGardes.innerHTML = (bareme && bareme.garde_fous)
        ? auditGardeFousHtml(bareme)
        : '<div class="source-note">barème indisponible</div>';
    }
    initialiserInfobulles();
  } catch (erreur){
    /* L'audit est un confort : une route muette ne casse pas le simulateur. */
  }
}

/* Bloc « objections » : le registre de la contradiction, servi par
   `GET /api/objections`. La page ne rédige aucune objection, ne classe aucun
   statut et ne calcule aucun écart : elle met en forme ce que le registre de
   `simulateur/contradiction.py` déclare, marges de portée comprises (le serveur
   les déduit du catalogue, la page ne fait que les écrire). Les objections
   vivent dans des `<details>` : vingt-quatre textes dépliés d'un coup
   décourageraient la lecture, et le lecteur qui veut le détail l'ouvre. */
const CLASSE_STATUT = {refutee: 'ok', partiellement_concedee: 'partiel',
                       concedee: 'concede', en_cours: 'encours', ouverte: 'ouverte'};
function ligneSourceObjection(source){
  if (source.nature === 'interne'){
    return '<li><b>Interne</b> : <code>' + echapperTexte(source.chemin) + '</code>'
      + (source.reference ? ' — ' + echapperTexte(source.reference) : '') + '</li>';
  }
  return '<li><b>Externe</b> : ' + echapperTexte(source.reference)
    + ' <i>(' + echapperTexte(source.date) + ')</i>'
    + (source.origine ? ' — portée par ' + echapperTexte(source.origine) : '') + '</li>';
}
function pucePorteeObjection(o){
  if (o.portee_mde === null || o.portee_mde === undefined){
    return o.levier ? '<span class="puce-portee">levier <code>' + echapperTexte(o.levier)
      + '</code> · réforme sans montant au catalogue</span>' : '';
  }
  let texte = '<span class="puce-portee">levier <code>' + echapperTexte(o.levier)
    + '</code> · portée <b>' + fmt(o.portee_mde, 0) + ' Md€/an</b>';
  if (o.gage_mde_an !== null && o.gage_mde_an !== undefined){
    texte += ' · gage du dossier <b>' + fmt(o.gage_mde_an, 0) + ' Md€/an</b> · marge <b>'
      + fmt(o.marge_de_portee_mde, 0) + ' Md€/an</b> non comptée';
  }
  return texte + '</span>';
}
function carteObjection(o){
  const classe = CLASSE_STATUT[o.statut] || 'ouverte';
  const sources = (o.sources || []).map(ligneSourceObjection).join('');
  return '<details class="objection" data-statut="' + echapperTexte(o.statut)
    + '" data-famille="' + echapperTexte(o.famille) + '">'
    + '<summary><span class="numero">n° ' + o.numero + '</span>'
    + '<b>' + echapperTexte(o.titre) + '</b>'
    + '<span class="badge-statut ' + classe + '">' + echapperTexte(o.statut) + '</span>'
    + '<span class="famille">' + echapperTexte(o.famille)
    + (o.fiche ? ' · fiche ' + o.fiche : '') + '</span>'
    + (o.suivi ? '<span class="suivi">' + echapperTexte(o.suivi) + '</span>' : '')
    + '</summary>'
    + '<h4>La meilleure version de l\'objection</h4><p>' + echapperTexte(o.objection_forte) + '</p>'
    + (o.attaque_faible ? '<p class="attaque">Attaque d\'origine, conservée pour mémoire : '
        + echapperTexte(o.attaque_faible) + '</p>' : '')
    + '<h4>Ce que nous concédons</h4><p>' + echapperTexte(o.concession) + '</p>'
    + '<h4>Ce que nous maintenons, et pourquoi</h4><p>' + echapperTexte(o.maintien) + '</p>'
    + '<h4>Ce qui nous ferait changer d\'avis</h4><p>' + echapperTexte(o.falsification) + '</p>'
    + '<h4>Statut et suites</h4><p>' + echapperTexte(o.statut_libelle)
    + (o.changements ? ' — ' + echapperTexte(o.changements) : '') + '</p>'
    + '<div class="meta">' + pucePorteeObjection(o) + '</div>'
    + (sources ? '<h4>Sources</h4><ul class="sources">' + sources + '</ul>' : '')
    + '</details>';
}
function carteContreModele(modele){
  const scenarios = (modele.scenarios || []).map(cle =>
    '<code>' + echapperTexte(cle) + '</code>').join(', ');
  return '<div class="contre-modele"><b>' + echapperTexte(modele.titre) + '</b> '
    + '<span class="porte-par">' + echapperTexte(modele.porte_par) + '</span>'
    + '<h4>La thèse</h4><p>' + echapperTexte(modele.these) + '</p>'
    + '<h4>Ce que le simulateur en dit</h4><p>'
    + echapperTexte(modele.ce_que_le_simulateur_en_dit) + '</p>'
    + (scenarios ? '<p class="famille">Scénarios comparables : ' + scenarios + '</p>' : '')
    + '<h4>Ce que nous lui concédons</h4><p>' + echapperTexte(modele.concession) + '</p>'
    + '<h4>Où nous ne le suivons pas</h4><p>' + echapperTexte(modele.divergence) + '</p>'
    + (modele.ouverts ? '<h4>Ce qui reste ouvert</h4><p>' + echapperTexte(modele.ouverts) + '</p>' : '')
    + '</div>';
}
function renderObjections(donnees){
  const zone = document.getElementById('objections-corps');
  const intro = document.getElementById('contradiction-resume');
  const zoneModeles = document.getElementById('contre-modeles-corps');
  if (!zone) return;
  const lignes = donnees.objections || [];
  if (intro){
    const comptes = (donnees.comptes && donnees.comptes.par_statut) || {};
    const statuts = Object.keys(comptes).filter(cle => comptes[cle])
      .map(cle => '<b>' + comptes[cle] + '</b> ' + echapperTexte(cle)).join(' · ');
    const fous = donnees.garde_fous ? Object.keys(donnees.garde_fous) : [];
    intro.innerHTML = lignes.length + ' objection(s) affichée(s) sur le registre'
      + (statuts ? ' — ' + statuts : '')
      + '. Une objection « réfutée » est une objection à laquelle la réponse tient sous sa '
      + 'forme forte ; une objection « concédée » a changé le texte, le chiffre ou la mesure.'
      + (fous.length ? ' <span class="hors">Garde-fous en défaut : '
          + echapperTexte(fous.join(', ')) + '</span>' : '');
  }
  zone.innerHTML = lignes.map(carteObjection).join('')
    || '<div class="carte">Aucune objection ne correspond à ce filtre.</div>';
  if (zoneModeles && donnees.contre_modeles){
    zoneModeles.innerHTML = donnees.contre_modeles.map(carteContreModele).join('');
  }
}
async function chargerObjections(filtre){
  const zone = document.getElementById('objections-corps');
  if (!zone) return;
  zone.innerHTML = '<div class="carte">Chargement des objections…</div>';
  try {
    const reponse = await fetch('/api/objections' + (filtre || ''));
    const donnees = await reponse.json();
    if (donnees.error) throw new Error(donnees.error);
    renderObjections(donnees);
  } catch (erreur){
    zone.innerHTML = '<div class="carte">Le registre des objections n\'a pas répondu : '
      + echapperTexte(erreur.message) + '. La page affiche cette absence plutôt que de '
      + 'rédiger les objections elle-même.</div>';
  }
}

(async function demarrer(){
  await chargerCatalogue();
  initialiserInfobulles();
  initialiserModale();
  renderScenarios();
  await chargerContexte(false);
  chargerAudit();
  // Le registre des objections se charge comme l'audit : une requête, aucun
  // calcul, et la page reste lisible si le serveur ne répond pas.
  chargerObjections('');
  // Le lexique se charge en tâche de fond : les termes soulignés apparaissent
  // dès la première simulation, sans rien retarder.
  chargerLexique();
  // Une adresse partagée décrit déjà un réglage complet : le programme de
  // départ ne s'y ajoute pas, sinon le lien ne rouvrirait pas la même chose.
  const depuisLien = appliquerLien();
  if (depuisLien) simuler(true); else chargerPreset('mandature', null);
  activerExports();
  // Premier relevé de cotations séparé, sans retarder l'initialisation du moteur.
  rafraichirMarches(true);
  // Guide de première visite : quatre étapes, jamais imposé deux fois.
  if (!guideDejaVu()){
    ouvrirGuide();
    marquerGuideVu();
  }
  // Les tableaux arrivent par vagues (strates, audit, bourse, nuances) : on les
  // enveloppe une fois pour toutes, à chaque rendu, sans dépendre d'un moteur
  // de rendu précis — la page reste lisible même sans observateur.
  rendreTableauxDefilants();
  rendreAidesFocalisables();
  if (typeof MutationObserver === 'function' && document.body){
    let enAttente = false;
    const observateur = new MutationObserver(function(){
      if (enAttente) return;
      enAttente = true;
      setTimeout(function(){
        enAttente = false;
        rendreTableauxDefilants();
        // Les leviers sont réécrits à chaque filtre : leurs aides aussi.
        rendreAidesFocalisables();
      }, 120);
    });
    observateur.observe(document.body, {childList: true, subtree: true});
  }
})();
</script>
</body>
</html>
"""
