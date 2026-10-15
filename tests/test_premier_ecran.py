"""
tests/test_premier_ecran.py — ce qu'un téléphone voit avant la première ligne.

Le visiteur l'a dit autrement : « lecture claire et confortable sur un
smartphone ». Mesuré dans Chromium le 15 octobre 2026, à 380 px, la page prenait
**863 px** de cadre — bandeau 566, sommaire 58, ruban 239 — avant le premier mot
de contenu, sur un écran de 780. Le contenu existait ; il n'était pas visible.

Ce fichier tient les quatre promesses de la réponse :

1. **le premier écran se mesure** — `outils/plafonds_premier_ecran.mjs` dit ce
   que valent bandeau + sommaire + ruban, et ce qu'ils valent au maximum ;
2. **un plafond est ancré** — chacun porte la mesure datée dont il vient, et
   aucun n'est *au-dessus* de cette mesure : un plafond qui autorise le statu
   quo ne plafonne rien ;
3. **seul le téléphone est plafonné** — au large, il y a la place ; un plafond
   qui ne se déclenche jamais est du bruit ;
4. **la page tient ce que le plafond suppose** — les règles du palier 480 px
   sont lues dans la feuille servie : les quatre commandes du ruban sur une
   rangée, deux libellés dont un seul est peint, l'horizon dit une fois, et
   aucun texte sous `--t-min`.

Ce qui demande un navigateur — la photographie — vit dans le travail
d'intégration continue ; ce qui n'en demande pas est éprouvé ici.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from outils import contraste_ecran  # noqa: E402
from simulateur.interface import HTML_PAGE  # noqa: E402

NODE = shutil.which("node")
MODULE_PLAFONDS = RACINE / "outils" / "plafonds_premier_ecran.mjs"
RUNNER = RACINE / "tests" / "plafonds_premier_ecran.mjs"
CAPTURES = RACINE / "outils" / "captures_ecran.mjs"

#: Les largeurs de téléphone : celles qu'un visiteur tient dans une main.
LARGEURS_TELEPHONE = (380, 640)


def _css() -> str:
    return contraste_ecran.feuille_de_la_page(HTML_PAGE)


def _declarations(corps: str) -> dict[str, str]:
    return {nom.strip(): valeur.strip().replace("!important", "").strip()
            for nom, valeur in re.findall(r"([-\w]+)\s*:\s*([^;]+)", corps)}


def _regles_dans(selecteur: str, *fragments: str) -> list[tuple[tuple[str, ...], dict[str, str]]]:
    """Les règles dont la liste contient ce sélecteur **et** dont un média colle.

    Rendues avec leur contexte : une règle de palier n'est pas la règle de base,
    et les confondre ferait passer un écran large pour un téléphone.
    """
    sortie = []
    for contexte, liste, corps in contraste_ecran.regles(_css()):
        if selecteur not in [morceau.strip() for morceau in liste.split(",")]:
            continue
        if all(any(fragment in bloc for bloc in contexte) for fragment in fragments):
            sortie.append((contexte, _declarations(corps)))
    return sortie


def _dernier(selecteur: str, propriete: str, *fragments: str) -> str | None:
    """La dernière règle qui **déclare** cette propriété, ou `None`.

    Un sélecteur reçoit plusieurs règles dans le même palier — une pour la
    taille, une pour l'interligne, une pour les marges. Lire « la dernière » ne
    dit pas ce qu'on croit : il faut lire celle qui parle de la propriété.
    """
    for _contexte, pose in reversed(_regles_dans(selecteur, *fragments)):
        if propriete in pose:
            return pose[propriete]
    return None


def _pose(regles: list[tuple[tuple[str, ...], dict[str, str]]]) -> dict[str, str]:
    """La dernière règle, celle qui gagne à la cascade."""
    return regles[-1][1] if regles else {}


#: Le plancher de lecture, et la racine la plus petite que la page propose
#: (`html[data-texte="87"]` → 87,5 % de 16 px). Un texte doit y tenir.
PLANCHER = 12.5
RACINE_MINIMUM = 0.875 * 16


def _en_px(valeur: str) -> float | None:
    """Une longueur du socle, en px, à la plus petite taille de texte."""
    valeur = valeur.strip()
    if valeur.startswith("clamp("):
        # La borne basse est la seule qui compte ici : c'est la plus petite
        # taille que la règle puisse produire sur un écran étroit.
        dedans = valeur[6:].rstrip(")")
        return _en_px(dedans.split(",")[0])
    if valeur.startswith("max("):
        dedans = valeur[4:].rstrip(")")
        tailles = [_en_px(morceau) for morceau in dedans.split(",")]
        connues = [taille for taille in tailles if taille is not None]
        return max(connues) if connues else None
    if valeur == "var(--t-min)":
        return PLANCHER
    trouve = re.match(r"([\d.]+)(px|rem|em)$", valeur)
    if not trouve:
        return None
    nombre = float(trouve.group(1))
    return nombre if trouve.group(2) == "px" else nombre * RACINE_MINIMUM


def _derniere_taille(selecteur: str) -> str | None:
    """La dernière `font-size` qui s'applique à ce sélecteur, tous paliers compris."""
    taille = None
    for _contexte, liste, corps in contraste_ecran.regles(_css()):
        if selecteur not in [morceau.strip() for morceau in liste.split(",")]:
            continue
        pose = _declarations(corps)
        if "font-size" in pose:
            taille = pose["font-size"]
    return taille


def _plafonds() -> dict:
    """Les plafonds, tels que le module les publie — exécuté, pas relu."""
    programme = (f"import {{ PLAFONDS }} from {MODULE_PLAFONDS.as_uri()!r};"
                 "console.log(JSON.stringify(PLAFONDS));")
    resultat = subprocess.run([NODE, "--input-type=module", "-e", programme],
                              capture_output=True, text=True, cwd=str(RACINE))
    if resultat.returncode != 0:
        raise AssertionError(f"le module de plafonds ne s'exécute pas : {resultat.stderr}")
    charge = json.loads(resultat.stdout)
    return {int(largeur): limite for largeur, limite in charge.items()}


def _verdict(vues: list[dict], plafonds: dict | None = None) -> tuple[int, dict]:
    """Joue les plafonds sur des vues, comme le ferait la photographie."""
    with tempfile.TemporaryDirectory() as dossier:
        chemin = Path(dossier) / "vues.json"
        chemin.write_text(json.dumps(vues), encoding="utf-8")
        commande = [NODE, str(RUNNER), str(chemin)]
        if plafonds is not None:
            chemin_plafonds = Path(dossier) / "plafonds.json"
            chemin_plafonds.write_text(json.dumps(plafonds), encoding="utf-8")
            commande.append(str(chemin_plafonds))
        resultat = subprocess.run(commande, capture_output=True, text=True, cwd=str(RACINE))
    return resultat.returncode, json.loads(resultat.stdout)


def _vue(largeur: int, bandeau: int, sommaire: int, ruban: int, nom: str = "vue") -> dict:
    return {"nom": nom, "largeur": largeur,
            "premier_ecran": {"bandeau": bandeau, "sommaire": sommaire, "ruban": ruban,
                              "total": bandeau + sommaire + ruban}}


class TestLesPlafonds(unittest.TestCase):
    """Un plafond sans mesure datée est un chiffre choisi, pas une mesure tenue."""

    @classmethod
    def setUpClass(cls):
        if NODE is None:
            raise unittest.SkipTest("node absent : les plafonds ne s'exécutent pas")
        cls.plafonds = _plafonds()

    def test_les_largeurs_de_telephone_sont_plafonnees(self):
        for largeur in LARGEURS_TELEPHONE:
            with self.subTest(largeur=largeur):
                self.assertIn(largeur, self.plafonds,
                              f"aucun plafond à {largeur} px : le premier écran y dérive")

    def test_chaque_plafond_porte_sa_mesure_datee(self):
        for largeur, limite in self.plafonds.items():
            with self.subTest(largeur=largeur):
                self.assertGreater(limite["avant"], 0,
                                   "un plafond sans mesure ancienne ne vient de nulle part")
                self.assertGreater(limite["mesure"], 0,
                                   "un plafond sans mesure du jour ne tient rien")
                self.assertLessEqual(limite["mesure"], limite["avant"],
                                     "la mesure du jour ne peut pas être pire que l'ancienne "
                                     "— sinon la passe a fait reculer le premier écran")
                self.assertTrue(re.search(r"\d{4}", limite["quand"]),
                                f"« {limite['quand']} » ne dit pas quand la mesure a été prise")
                self.assertTrue(limite["quoi"].strip(),
                                "la mesure ne dit pas de quoi elle est faite")

    def test_aucun_plafond_n_autorise_le_statu_quo(self):
        """Un plafond au-dessus de sa mesure ancienne décrit l'existant au lieu de le corriger."""
        for largeur, limite in self.plafonds.items():
            with self.subTest(largeur=largeur):
                self.assertLess(limite["plafond"], limite["avant"],
                                f"à {largeur} px, le plafond de {limite['plafond']} px "
                                f"autorise les {limite['avant']} px mesurés avant la passe")

    def test_le_plafond_tient_ce_qui_est_mesure(self):
        """Un plafond sous la mesure du jour ferait rougir le travail en cours.

        Sauf une **cible** : là, le plafond demande un gain que la mesure n'a pas
        encore constaté. Le dire est ce qui empêche une cible de devenir un
        plafond qu'on croit tenu.
        """
        for largeur, limite in self.plafonds.items():
            with self.subTest(largeur=largeur):
                if limite.get("cible"):
                    self.assertLess(limite["plafond"], limite["mesure"],
                                    f"à {largeur} px, une cible au-dessus de la mesure "
                                    f"de {limite['mesure']} px ne demande rien")
                    continue
                self.assertGreaterEqual(limite["plafond"], limite["mesure"],
                                        f"à {largeur} px, le plafond de {limite['plafond']} px "
                                        f"est déjà sous les {limite['mesure']} px mesurés")

    def test_seul_le_telephone_est_plafonne(self):
        """Au large, le premier écran fait 394 px sur 900 : un plafond y serait du bruit."""
        source = CAPTURES.read_text(encoding="utf-8")
        largeurs = re.search(r"largeurs:\s*\[([^\]]+)\]", source)
        self.assertIsNotNone(largeurs, "les largeurs photographiées ne se lisent plus")
        photographiees = {int(valeur) for valeur in re.findall(r"\d+", largeurs.group(1))}
        for largeur in self.plafonds:
            with self.subTest(largeur=largeur):
                self.assertIn(largeur, photographiees,
                              f"un plafond à {largeur} px ne serait jamais mesuré")
        self.assertEqual({int(largeur) for largeur in self.plafonds},
                         set(LARGEURS_TELEPHONE),
                         "les plafonds couvrent d'autres largeurs que celles du téléphone")


class TestLeVerdict(unittest.TestCase):
    """Le verdict nomme la vue, la mesure, le plafond, et de combien ça dépasse."""

    @classmethod
    def setUpClass(cls):
        if NODE is None:
            raise unittest.SkipTest("node absent : les plafonds ne s'exécutent pas")

    def test_une_vue_au_dessus_est_refusee_avec_ses_chiffres(self):
        code, verdict = _verdict([_vue(380, 566, 58, 239, "accueil-jour-380")])
        self.assertEqual(code, 1, "un dépassement n'a pas fait échouer le contrôle")
        self.assertEqual(len(verdict["depassements"]), 1)
        depassement = verdict["depassements"][0]
        self.assertEqual(depassement["nom"], "accueil-jour-380")
        self.assertEqual(depassement["exces"], 863 - depassement["plafond"])
        for morceau in ("bandeau 566", "sommaire 58", "ruban 239"):
            self.assertIn(morceau, depassement["phrase"],
                          "le verdict ne dit pas où la place se perd")

    def test_une_vue_sous_le_plafond_passe(self):
        code, verdict = _verdict([_vue(380, 400, 58, 150)])
        self.assertEqual(code, 0, "une vue sous le plafond a été refusée")
        self.assertEqual(verdict["depassements"], [])
        self.assertTrue(any("tenu" in ligne for ligne in verdict["lignes"]))

    def test_une_largeur_sans_plafond_n_est_jamais_signalee(self):
        """Le grand écran n'est pas plafonné : 394 px sur 900, il y a la place."""
        code, verdict = _verdict([_vue(1280, 248, 66, 80)])
        self.assertEqual(code, 0)
        self.assertEqual(verdict["depassements"], [])

    def test_une_vue_sans_mesure_est_signalee(self):
        """On ne tient pas un plafond sur ce qu'on ne mesure pas."""
        code, verdict = _verdict([{"nom": "accueil-sans-mesure", "largeur": 380}])
        self.assertEqual(code, 1)
        self.assertIsNone(verdict["depassements"][0]["mesure"])
        self.assertIn("ne porte pas de mesure", verdict["depassements"][0]["phrase"])

    def test_le_plafond_est_lu_dans_le_module_et_non_recopie(self):
        """Le runner accepte des plafonds de passage : c'est ce qui le rend éprouvable."""
        code, verdict = _verdict([_vue(380, 566, 58, 239)], {380: {"plafond": 2000,
                                                                  "mesure": 863,
                                                                  "quand": "2026",
                                                                  "quoi": "essai"}})
        self.assertEqual(code, 0, "le runner a ignoré les plafonds qu'on lui donne")
        self.assertEqual(verdict["depassements"], [])


class TestLaMesureEstBranchee(unittest.TestCase):
    """Un plafond qu'on se contente d'afficher ne plafonne rien."""

    def test_l_outil_mesure_les_trois_cadres_du_premier_ecran(self):
        source = CAPTURES.read_text(encoding="utf-8")
        self.assertIn('hauteurDe(".entete")', source)
        self.assertIn('hauteurDe(".sommaire")', source)
        self.assertIn('hauteurDe(".ruban-veille")', source)
        self.assertIn("total: bandeau + sommaire + ruban", source,
                      "le premier écran n'est plus la somme de ses cadres")

    def test_le_rapport_montre_le_texte_peint(self):
        """`textContent` lit aussi ce qui est masqué : le rapport s'y est trompé.

        Une commande porte deux libellés — le long au large, le court sur un
        téléphone — et un seul est peint. Lire `textContent` les additionnait :
        le rapport annonçait « référence datée du projetréf » là où l'écran ne
        montre qu'un texte. Un rapport qu'on lit pour savoir ce qui est à
        l'écran doit lire ce qui est à l'écran.
        """
        source = CAPTURES.read_text(encoding="utf-8")
        for extrait in ('texte: (commande.textContent', 'texte: (enfant.textContent'):
            with self.subTest(extrait=extrait):
                self.assertNotIn(extrait, source,
                                 "le rapport étiquette un nœud par du texte masqué")
        self.assertGreaterEqual(source.count("innerText"), 2,
                                "les deux étiquettes du rapport ne lisent plus ce qui est peint")

    def test_l_outil_echoue_quand_un_plafond_est_depasse(self):
        source = CAPTURES.read_text(encoding="utf-8")
        self.assertIn("depassements(rapport)", source,
                      "l'outil ne confronte plus ses mesures aux plafonds")
        self.assertIn("process.exit(1)", source,
                      "un plafond dépassé ne fait plus échouer la photographie")

    def test_l_outil_publie_le_verdict_dans_le_resume(self):
        source = CAPTURES.read_text(encoding="utf-8")
        self.assertIn("lignes_premier_ecran(rapport)", source,
                      "le résumé ne dit plus où en est le premier écran")
        self.assertIn("plan(\".ruban-veille\")", source,
                      "le ruban n'est plus détaillé : on ne saurait pas où il prend sa hauteur")


class TestLaPageTientLePlafond(unittest.TestCase):
    """Ce que la page applique **à un téléphone**, relu dans la feuille servie.

    La largeur n'est pas écrite ici : le contrôle demande quelles règles
    s'appliquent vraiment à 380 px — un palier qui rétrécirait à 480 px laisserait
    passer un téléphone de 430 px, et le plafond repose sur ces règles-là.
    """

    LARGEUR = 380

    def _telephone(self, selecteur: str) -> list[tuple[tuple[str, ...], dict[str, str]]]:
        sortie = []
        for contexte, liste, corps in contraste_ecran.regles(_css()):
            if selecteur not in [morceau.strip() for morceau in liste.split(",")]:
                continue
            bornes = [int(trouve) for bloc in contexte
                      for trouve in re.findall(r"max-width:\s*(\d+)px", bloc)]
            if bornes and min(bornes) >= self.LARGEUR:
                sortie.append((contexte, _declarations(corps)))
        return sortie

    def test_quatre_commandes_tiennent_sur_une_rangee(self):
        """Deux rangées de 44 px coûtaient 51 px de haut pour 44 px de boutons.

        Mesuré le 15 octobre 2026 : le ruban d'un téléphone passe de 239 à
        152 px à 380, et de 206 à 152 à 640.
        """
        pose = self._telephone(".ruban-veille .ruban-actions")
        self.assertTrue(pose, "les commandes du ruban ne sont plus réglées pour un téléphone")
        colonnes = _pose(pose).get("grid-template-columns", "")
        self.assertIn("repeat(4", colonnes.replace(" ", ""),
                      f"les quatre commandes ne tiennent plus sur une rangée : {colonnes}")

    def test_la_cible_du_doigt_n_a_pas_ete_rognee(self):
        """44 px : c'est la cible du doigt, pas du décor."""
        poses = [pose for _contexte, pose
                 in self._telephone(".ruban-veille .ruban-actions button")]
        self.assertTrue(poses, "les commandes du ruban ne sont plus réglées pour un téléphone")
        for pose in poses:
            with self.subTest(pose=pose):
                hauteur = pose.get("min-height") or pose.get("height")
                if hauteur is not None:
                    self.assertGreaterEqual(_en_px(hauteur) or 0, 44,
                                            f"la cible du doigt est rabotée à {hauteur}")
                if "font-size" in pose:
                    taille = _en_px(pose["font-size"])
                    self.assertIsNotNone(taille, f"taille illisible : {pose['font-size']}")
                    self.assertGreaterEqual(taille, PLANCHER,
                                            "un libellé de commande sous le plancher : "
                                            + pose["font-size"])

    def test_un_seul_libelle_est_peint_a_la_fois(self):
        """Le long dit tout, le court tient dans une rangée : jamais les deux.

        La règle est celle de la page, pas du ruban : les pastilles d'état
        portent le même couple — « référence datée du projet » ne tient pas sur
        la rangée d'un téléphone, « référence datée » si.
        """
        base = [pose for contexte, pose in _regles_dans(".mot-court")
                if not contexte]
        self.assertTrue(base, "le libellé court n'est plus masqué au large")
        self.assertEqual(base[-1].get("display"), "none")
        courts = self._telephone(".mot-court")
        longs = self._telephone(".mot-long")
        self.assertEqual(_pose(courts).get("display"), "inline",
                         "le libellé court ne s'affiche pas sur un téléphone")
        self.assertEqual(_pose(longs).get("display"), "none",
                         "le libellé long reste peint sur un téléphone")

    def test_les_pastilles_d_etat_portent_les_deux_textes(self):
        """Chaque pastille a ses deux textes, et rien n'est caché aux lecteurs.

        Le texte écarté l'est par `display:none`, donc il sort aussi de l'arbre
        d'accessibilité : rien n'est lu deux fois, et rien ne se tait. C'est
        pourquoi les textes des pastilles ne portent **pas** `aria-hidden` —
        contrairement aux libellés des commandes du ruban, dont le nom
        accessible est tenu à part par `aria-label`.
        """
        for identifiant in ("badge-date", "badge-leviers"):
            with self.subTest(pastille=identifiant):
                self.assertIn(f'id="{identifiant}-long"', HTML_PAGE,
                              f"{identifiant} n'a plus de texte long repéré")
                self.assertIn(f'id="{identifiant}-court"', HTML_PAGE,
                              f"{identifiant} n'a plus de texte court repéré")
        debut = HTML_PAGE.index('id="badge-date"')
        bloc = HTML_PAGE[debut:HTML_PAGE.index("</span></span>", debut)]
        self.assertNotIn("aria-hidden", bloc,
                         "un texte d'état caché aux lecteurs d'écran : ce qui est "
                         "peint doit être ce qui est lu")

    def test_les_deux_textes_d_une_pastille_sont_ecrits_ensemble(self):
        """Sinon la pastille annoncerait l'état précédent — ou resterait vide."""
        source = HTML_PAGE[HTML_PAGE.index("function direLaPastille"):]
        source = source[:source.index("\nfunction ", 10)]
        self.assertIn("longu.textContent = long", source,
                      "le texte long n'est plus écrit")
        self.assertIn("court_.textContent = court", source,
                      "le texte court n'est plus écrit")
        self.assertIn("noeud.textContent = long", source,
                      "une page sans repères ne retombe plus sur le texte long")
        for site in ("badge-date", "badge-leviers"):
            with self.subTest(site=site):
                self.assertIn(f"direLaPastille('{site}'", HTML_PAGE,
                              f"{site} n'est plus écrit par direLaPastille")
                self.assertNotIn(f"getElementById('{site}').textContent", HTML_PAGE,
                                 f"{site} est encore écrit en clair, sans son texte court")

    def test_le_contexte_dit_aussi_son_texte_court(self):
        """« référence datée du projet » (25 signes) ne tient pas sur 340 px."""
        source = HTML_PAGE[HTML_PAGE.index("function pastille(mode)"):]
        source = source[:source.index("\nfunction ", 10)]
        self.assertIn("mot-long", source, "la pastille de contexte n'a plus de texte long")
        self.assertIn("mot-court", source, "la pastille de contexte n'a plus de texte court")
        for mode in ("live", "reference", "mixte"):
            with self.subTest(mode=mode):
                self.assertIn(f"{mode}:", source, f"le mode {mode} n'a plus ses deux textes")

    def test_chaque_commande_du_ruban_porte_ses_deux_libelles(self):
        for identifiant in ("btn-console-details", "btn-densite", "aller-leviers", "aller-audit"):
            with self.subTest(bouton=identifiant):
                self.assertIn(f'id="{identifiant}-long"', HTML_PAGE,
                              f"{identifiant} n'a plus de libellé long repéré")
                self.assertIn(f'id="{identifiant}-court"', HTML_PAGE,
                              f"{identifiant} n'a plus de libellé court repéré")

    def test_le_titre_cede_un_cran_sur_un_telephone(self):
        """Le titre du bandeau : 18,4 px au palier 640, 16,8 à 480.

        Mesuré le 15 octobre 2026 : à 380 px, quatre lignes de titre coûtaient
        96 px et quatre lignes de phrase 85 — le bandeau en faisait 436. Le
        titre descend d'un cran et la phrase resserre son interligne : deux
        rangées de texte en moins, sans qu'aucun corps ne passe sous le plancher
        de lecture (`--t-min`, 12,5 px, à la plus petite taille de texte).
        """
        grand = _dernier("header.entete h1", "font-size", "(max-width:640px)")
        petit = _dernier("header.entete h1", "font-size", "(max-width:480px)")
        self.assertIsNotNone(grand, "la taille du titre au palier 640 ne se lit plus")
        self.assertIsNotNone(petit, "le titre ne cède plus rien à 480 px")
        taille_grande = _en_px(grand)
        taille_petite = _en_px(petit)
        self.assertIsNotNone(taille_petite, f"taille illisible pour le titre : {petit}")
        self.assertLess(taille_petite, taille_grande,
                        "le titre ne descend pas d'un cran : le bandeau ne gagne rien")
        self.assertGreaterEqual(taille_petite, PLANCHER,
                                "le titre passe sous le plancher de lecture")
        interligne_grand = _dernier("header.entete .accroche", "line-height",
                                    "(max-width:640px)")
        interligne_petit = _dernier("header.entete .accroche", "line-height",
                                    "(max-width:480px)")
        self.assertIsNotNone(interligne_petit, "la phrase ne resserre plus son interligne")
        self.assertLess(float(interligne_petit), float(interligne_grand),
                        "l'interligne de la phrase ne se resserre pas")

    def test_l_horodatage_d_un_telephone_tient_en_onze_signes(self):
        """Deux formes du même instant, écrites depuis la même source.

        L'écran large dit `horodatage : 2026-10-15 15:09 UTC` (157 px mesurés) ;
        la rangée d'un téléphone n'en garde que onze signes, `15/10 15:09`, ce
        qui laisse le contexte et les leviers côte à côte — et fait passer la
        ligne d'état de trois rangées à deux.
        """
        source = HTML_PAGE[HTML_PAGE.index("function renderContexte"):]
        source = source[:source.index("\nfunction ", 10)]
        self.assertIn("const instant = c.horodatage.replace('T', ' ').slice(0, 16);", source,
                      "l'horodatage n'est plus lu une seule fois pour ses deux formes")
        self.assertIn("`horodatage : ${instant} UTC`", source,
                      "la forme longue ne dit plus l'année et le fuseau")
        self.assertIn("`${jour.slice(8, 10)}/${jour.slice(5, 7)} ${heure}`", source,
                      "la forme courte de l'horodatage n'est plus construite")
        court = source[source.index("`${jour.slice(8, 10)}"):]
        court = court[:court.index("`") + 1]
        self.assertNotIn("UTC", court, "la forme courte garde le fuseau : elle ne tient plus")
        self.assertNotIn("horodatage", court,
                         "la forme courte répète le mot de la forme longue")

    def test_la_ligne_d_etat_se_resserre_sur_un_telephone(self):
        """Trois pastilles et le select de l'horizon sur deux rangées, pas trois."""
        def horizontal(valeur: str | None) -> float:
            self.assertIsNotNone(valeur, "la pastille n'a plus de rembourrage à ce palier")
            morceaux = valeur.split()
            self.assertEqual(len(morceaux), 2, f"rembourrage inattendu : {valeur}")
            return float(morceaux[-1].rstrip("px"))

        petit = horizontal(_dernier("header.entete .etat-contexte .pastille", "padding",
                                    "(max-width:480px)"))
        grand = horizontal(_dernier("header.entete .etat-contexte .pastille", "padding",
                                    "(max-width:640px)"))
        self.assertLess(petit, grand,
                        "les pastilles ne se resserrent pas d'un palier à l'autre")
        ecart_petit = float(_dernier("header.entete .etat-contexte", "gap",
                                     "(max-width:480px)").rstrip("px"))
        ecart_grand = float(_dernier("header.entete .etat-contexte", "gap",
                                     "(max-width:640px)").rstrip("px"))
        self.assertLess(ecart_petit, ecart_grand,
                        "l'écart entre pastilles ne se resserre pas")

    def test_les_deux_libelles_sont_ecrits_ensemble(self):
        """Sinon le premier clic remet le libellé long, et le ruban regonfle."""
        source = HTML_PAGE[HTML_PAGE.index("function direLeBouton"):]
        source = source[:source.index("\nfunction ", 10)]
        # Les **écritures**, pas la présence des mots : un repère qu'on lit sans
        # le remplir laisserait le bouton annoncer l'état précédent.
        self.assertIn("longu.textContent = long", source, "le libellé long n'est plus écrit")
        self.assertIn("court_.textContent = court", source, "le libellé court n'est plus écrit")
        self.assertIn("setAttribute('aria-label', long)", source,
                      "le nom accessible ne suit plus le libellé du bouton")
        self.assertIn("bouton.textContent = long", source,
                      "une page sans repères ne retombe plus sur le libellé long")
        for fonction in ("function basculerDensite", "function basculerDetailsConsole"):
            with self.subTest(fonction=fonction):
                corps = HTML_PAGE[HTML_PAGE.index(fonction):][:1400]
                self.assertIn("direLeBouton(", corps,
                              f"{fonction} écrit encore un seul libellé")
                self.assertNotIn("bouton.textContent =", corps,
                                 f"{fonction} réécrit le bouton en clair, spans compris")

    def test_l_horizon_ne_se_dit_qu_une_fois_sur_un_telephone(self):
        """Le select porte l'horizon ; la pastille le répétait sur une rangée entière."""
        cache = self._telephone("#badge-horizon")
        self.assertTrue(cache, "la pastille d'horizon n'est plus écartée sur un téléphone")
        self.assertEqual(_pose(cache).get("display"), "none")
        self.assertNotIn('id="horizon-simulation" class', HTML_PAGE)
        self.assertIn('id="horizon-simulation"', HTML_PAGE,
                      "le select qui porte l'horizon a disparu : il ne se dit plus du tout")
        self.assertIn("changerHorizon", HTML_PAGE,
                      "rien ne relie plus le select à l'état de la page")

    def test_la_barre_du_bandeau_se_range_en_deux_colonnes(self):
        """Trois rangées dont une trouée pour quatre commandes : deux suffisent."""
        poses = [pose for _contexte, pose in self._telephone("header.entete .barre-contexte")
                 if "grid-template-columns" in pose]
        self.assertTrue(poses, "la barre du bandeau n'est plus rangée pour un téléphone")
        colonnes = poses[-1]["grid-template-columns"].replace(" ", "")
        self.assertIn("repeat(2", colonnes,
                      f"la barre ne se range plus en deux colonnes : {colonnes}")

    def test_la_lecture_ne_retrecit_pas(self):
        """C'est la mise en page qui se resserre, pas le texte qui rétrécit.

        Le corps est mesuré **à la plus petite taille de texte que la page
        propose** (racine à 87,5 %) : une règle qui passerait sous le plancher de
        lecture ne se verrait sur aucun écran large, et se verrait sur tous les
        téléphones qui règlent le texte en petit.
        """
        for selecteur in ("header.entete h1", "header.entete .accroche"):
            with self.subTest(selecteur=selecteur):
                regle = _derniere_taille(selecteur)
                self.assertIsNotNone(regle, f"{selecteur} n'a plus de taille déclarée")
                taille = _en_px(regle)
                self.assertIsNotNone(taille, f"taille illisible pour {selecteur} : {regle}")
                self.assertGreaterEqual(taille, PLANCHER,
                                        f"{selecteur} tombe à {taille:.1f} px ({regle}) "
                                        "à la plus petite taille de texte")


if __name__ == "__main__":
    unittest.main()
