#!/usr/bin/env bash
# Publie, dans le dépôt du site M.R.S.C, sa copie du moteur mise à jour.
#
#     bash livraison-mrsc/publier-mrsc.sh [atelier] [branche]
#
# La copie embarquée par le site datait du 8 octobre (99491d8) ; l'amont a
# beaucoup bougé depuis. Le correctif de sécurité du site, lui, ne s'appliquait
# plus : il est rebasé ici (voir LISEZ-MOI.md, à côté de ce script, qui dit ce
# que le rebasage conserve).
#
# Le script copie **le sommet de `main`** au moment où il tourne — c'est ce qui
# garde la veille du site au vert — puis rejoue exactement la CI du site. Il
# travaille dans un dossier jetable, ne touche jamais `main` côté site, et
# s'arrête **avant** de publier si un contrôle échoue.
#
# Pour rejouer une publication à une révision précise (par exemple pour vérifier
# ce colis), donner la révision en troisième argument.
set -euo pipefail

ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ATELIER="${1:-/tmp/mrsc-moteur}"
BRANCHE="${2:-}"
REVISION="${3:-}"
AMONT="https://github.com/thejmimiia-code/D-mocratie-et-politique-du-peuple-pour-le-peuple-par-le-peuple.git"
SITE="https://github.com/thejmimiia-code/MRSC.git"

etape() { printf '\n\033[1m%s\033[0m\n' "$*"; }
bilan() { printf '  ✓ %s\n' "$*"; }

# ─────────────────────────────────────────────────────────── 1. les deux dépôts
etape "1/6 · récupération des dépôts dans $ATELIER"

rm -rf "$ATELIER"
mkdir -p "$ATELIER"
git clone --quiet --depth 1 "$AMONT" "$ATELIER/amont"
git clone --quiet --depth 1 "$SITE" "$ATELIER/site"

if [ -n "$REVISION" ]; then
  # Révision imposée : on va la chercher précisément, sinon la copie partirait
  # du sommet de `main` et le récit du colis ne serait plus vrai.
  if [ "$(git -C "$ATELIER/amont" rev-parse HEAD)" != "$REVISION" ]; then
    git -C "$ATELIER/amont" fetch --quiet --depth 1 origin "$REVISION"
    git -C "$ATELIER/amont" checkout --quiet FETCH_HEAD
  fi
  if [ "$(git -C "$ATELIER/amont" rev-parse HEAD)" != "$REVISION" ]; then
    echo "Révision amont introuvable : $REVISION" >&2
    exit 1
  fi
fi
REVISION_COURTE="$(git -C "$ATELIER/amont" rev-parse --short HEAD)"
bilan "amont à $REVISION_COURTE"
bilan "site à $(git -C "$ATELIER/site" rev-parse --short HEAD)"

cp "$ICI/simulateur-securite-mrsc.patch" \
   "$ATELIER/site/outils/patchs/simulateur-securite-mrsc.patch"
cd "$ATELIER/site"

# ──────────────────────────────────────────────────────────── 2. la copie
etape "2/6 · copie du moteur et correctif du site"
if ! python3 outils/mettre-a-jour-simulateur.py --depuis "$ATELIER/amont"; then
  cat >&2 <<'FIN'
La copie n'a pas été faite : le correctif du site ne s'applique plus sur la
révision visée — l'amont a bougé sous lui. Rien n'a été remplacé.
C'est exactement ce que l'outil doit faire : rebaser le correctif (voir
LISEZ-MOI.md, « Le correctif rebasé, en clair »), puis relancer.
FIN
  exit 1
fi

# ─────────────────────────────────────────── 3. reconstruction et API du site
etape "3/6 · reconstruction de la page et des fonctions api/"

# Six routes servies par le moteur, encore absentes de la liste du site : les
# taire ferait diverger l'API publiée de celle du moteur (la porte
# `verifier-integration.py` le signale). L'ajout est idempotent.
python3 - outils/generer-fonctions-api.py <<'PY'
import pathlib
import sys

ROUTES = ("constitution", "contrepouvoirs", "dynamiques", "instances", "nuances", "objections")
ANCRE = '''    "scenarios",
    "export",
)'''

chemin = pathlib.Path(sys.argv[1])
texte = chemin.read_text(encoding="utf-8")
manquantes = [route for route in ROUTES if f'"{route}",' not in texte]
if not manquantes:
    print("Les six routes du moteur sont déjà exposées : rien à faire.")
    raise SystemExit(0)
if texte.count(ANCRE) != 1:
    raise SystemExit(
        "Le générateur du site a changé de forme : ajoutez à la main "
        + ", ".join(manquantes)
    )
ajout = '    "scenarios",\n    "export",\n' + "".join(
    f'    "{route}",\n' for route in ROUTES
) + ")"
chemin.write_text(texte.replace(ANCRE, ajout, 1), encoding="utf-8")
print("Routes ajoutées à l'API du site : " + ", ".join(manquantes))
PY

python3 outils/construire-simulateur.py
python3 outils/generer-fonctions-api.py

# ───────────────────────────────────────── 4. les contrôles de la CI du site
etape "4/6 · rejeu de la CI du site"

python3 -m py_compile simulateur/*.py api/*.py outils/*.py
bilan "py_compile"
python3 outils/construire-apprentissages.py --verifier || exit 1
bilan "construire-apprentissages --verifier"
python3 outils/construire-simulateur.py --verifier || exit 1
bilan "construire-simulateur --verifier"
for porte in verifier-rd-continue verifier-site-statique verifier-securite verifier-integration; do
  if python3 "outils/$porte.py" > "$ATELIER/$porte.log" 2>&1; then
    bilan "$porte"
  else
    echo "Porte en échec : $porte" >&2
    tail -20 "$ATELIER/$porte.log" >&2
    exit 1
  fi
done

# ─────────────────────────────────── 5. les contrôles propres à cette copie
etape "5/6 · contrôles de la copie publiée"

python3 - <<'PY'
import pathlib

# Les durcissements du site absents de l'amont : ils ne doivent jamais
# disparaître dans une mise à jour du moteur.
GARDE = (
    "413 Payload Too Large",
    "414 URI Too Long",
    "DELAI_COLLECTE_NAVIGATEUR_MS",
    "DELAI_SOURCE_NAVIGATEUR_MS",
    "DUREE_CACHE_MARCHES_SECONDES",
    "DUREE_CACHE_PROXY_SECONDES",
    "LECTURES_NAVIGATEUR",
    "LIMITE_JSON_SOURCE_NAVIGATEUR",
    "MAX_BULLES_PAR_REQUETE",
    "MAX_COTATION_RESPONSE_BYTES",
    "MAX_QUERY_FIELDS",
    "MAX_REQUEST_BODY_BYTES",
    "MAX_REQUEST_TARGET_BYTES",
    "MAX_SOURCE_RESPONSE_BYTES",
    "SIMULATEUR_LOG_ERREURS",
    "nosniff",
)

fichiers = sorted(pathlib.Path("simulateur").glob("*.py"))
modules = {fichier: fichier.read_text(encoding="utf-8") for fichier in fichiers}
tout = "\n".join(modules.values())

perdues = [garde for garde in GARDE if garde not in tout]
if perdues:
    raise SystemExit("Protections perdues dans la copie : " + ", ".join(perdues))
print(f"  ✓ les {len(GARDE)} protections du site sont présentes")

restants = {fichier.name for fichier, texte in modules.items() if "<<<<<<<" in texte}
if restants:
    raise SystemExit(f"Marqueurs de conflit restants : {sorted(restants)}")
print("  ✓ aucun marqueur de conflit")

page = pathlib.Path("simulateur/index.html").read_text(encoding="utf-8")
if "/_vercel/insights" in page:
    raise SystemExit("La page embarquée porte encore la balise d'analytique Vercel")
print(f"  ✓ page reconstruite : {len(page)} caractères, autonome")

# Les scripts écrits dans la page doivent être du JavaScript valide : c'est
# exactement ce qu'une fusion de HTML en conflit casse sans le dire.
import re  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402

import json  # noqa: E402

# Les données structurées de la page : ce sont des données, pas du JavaScript.
# Les confondre ferait échouer `node --check` sur du JSON valide (défaut vu en
# vrai : le moteur pose désormais un `<script type="application/ld+json">`).
TYPES_JS = ("text/javascript", "application/javascript", "module")
balises = re.findall(r"<script([^>]*)>(.*?)</script>", page, re.S)
a_verifier, structures = [], []
for attributs, contenu in balises:
    if re.search(r"\bsrc\s*=", attributs):
        continue
    trouve = re.search(r"\btype\s*=\s*[\"']([^\"']*)[\"']", attributs)
    type_ = (trouve.group(1) if trouve else "text/javascript").lower().split(";", 1)[0].strip()
    if type_ in TYPES_JS:
        a_verifier.append(contenu)
    elif type_ in ("application/ld+json", "application/json"):
        structures.append((type_, contenu))

if not structures:
    raise SystemExit("Données structurées absentes de la page publiée")
for type_, contenu in structures:
    try:
        charge = json.loads(contenu)
    except json.JSONDecodeError as erreur:
        raise SystemExit(f"{type_} invalide : {erreur}")
    types = []
    cles = set()

    def _parcourir(noeud):
        if isinstance(noeud, dict):
            if "@type" in noeud:
                types.append(str(noeud["@type"]))
            cles.update(str(cle) for cle in noeud)
            for valeur in noeud.values():
                _parcourir(valeur)
        elif isinstance(noeud, list):
            for valeur in noeud:
                _parcourir(valeur)

    _parcourir(charge)
    interdits = {"aggregateRating", "review", "ratingValue", "faqPage"} & cles
    if interdits:
        raise SystemExit("Données structurées malhonnêtes : " + ", ".join(sorted(interdits)))
    print(f"  ✓ {type_} : JSON valide, types {', '.join(types) or 'aucun'}")

node = shutil.which("node")
if node is None:
    print("  · node absent : contrôle de syntaxe des scripts sauté")
else:
    print(f"  · {len(balises)} balise(s) <script>, {len(a_verifier)} en JavaScript à vérifier")
    for rang, script in enumerate(a_verifier, 1):
        essai = pathlib.Path(tempfile.mkdtemp()) / f"script-{rang}.mjs"
        essai.write_text(script, encoding="utf-8")
        resultat = subprocess.run([node, "--check", str(essai)], capture_output=True, text=True)
        if resultat.returncode:
            raise SystemExit(f"Script {rang} invalide : {resultat.stderr.strip()[-400:]}")
        print(f"  ✓ script JavaScript {rang} ({len(script)} caractères)")
PY

# La veille du site compare la révision copiée au sommet de `main` : elle a sa
# propre exécution hebdomadaire, et doit dire « à jour » ici.
if python3 outils/verifier-maj-amont.py > "$ATELIER/veille.log" 2>&1; then
  bilan "verifier-maj-amont — la copie est le sommet de main"
else
  printf '  ! verifier-maj-amont signale un retard :\n'
  sed 's/^/    /' "$ATELIER/veille.log" | tail -6
fi

# Cette porte interroge le réseau : sans lui, elle le dit et laisse la copie
# embarquée faire le calcul. Hors ligne n'est pas un échec.
if python3 outils/verifier-source-distante.py > "$ATELIER/source-distante.log" 2>&1; then
  bilan "verifier-source-distante"
else
  printf '  · verifier-source-distante : réseau injoignable, la copie embarquée fait le calcul\n'
fi

# ───────────────────────────────────────────────────── 6. la branche publiée
etape "6/6 · branche et demande de fusion"
if [ -z "$BRANCHE" ]; then
  BRANCHE="maj-moteur-$REVISION_COURTE"
fi
if [ -z "$(git config user.email || true)" ]; then
  git config user.name "${GIT_AUTEUR_NOM:-Mise à jour du moteur}"
  git config user.email "${GIT_AUTEUR_COURRIEL:-maj-moteur@localhost}"
fi
git checkout --quiet -b "$BRANCHE"
git add -A
git commit --quiet -F "$ICI/corps-de-pr.md"
bilan "commit $(git rev-parse --short HEAD)"
if git push -u origin "$BRANCHE"; then
  bilan "branche $BRANCHE poussée"
else
  # Le seul point que cet atelier n'a pas : l'écriture dans le dépôt du site.
  # La copie, elle, est faite et vérifiée : on la rend donc applicable.
  DIFF="$ATELIER/maj-site-$REVISION_COURTE.patch"
  git diff --binary main "$BRANCHE" > "$DIFF"
  printf '\n  ! Poussée refusée : le compte de cet atelier ne peut pas écrire dans %s.\n' "$SITE"
  printf '    La copie est faite, vérifiée, et committée ici (%s) :\n' "$(git rev-parse --short HEAD)"
  printf '    son diff complet est écrit dans\n\n      %s\n\n' "$DIFF"
  printf '    Depuis un compte autorisé, deux voies :\n'
  printf '      1. pousser la branche telle quelle :\n'
  printf '         cd %s && git push -u origin %s\n' "$PWD" "$BRANCHE"
  printf '      2. ou rejouer le diff sur un clone neuf :\n'
  printf '         git clone %s site && cd site\n' "$SITE"
  printf '         git checkout -b %s && git apply %s\n' "$BRANCHE" "$DIFF"
  printf '         git add -A && git commit -F %s && git push -u origin %s\n' "$ICI/corps-de-pr.md" "$BRANCHE"
  exit 1
fi

LIEN="https://github.com/thejmimiia-code/MRSC/compare/main...$BRANCHE?expand=1"
echo
echo "  Relecture puis fusion : $LIEN"
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  if gh pr create --repo thejmimiia-code/MRSC --base main --head "$BRANCHE" \
       --title "Moteur embarqué mis à jour vers $REVISION_COURTE, correctif du site rebasé" \
       --body-file "$ICI/corps-de-pr.md" 2>"$ATELIER/pr.log"; then
    gh pr view --repo thejmimiia-code/MRSC "$BRANCHE" --json url --jq .url
  else
    echo "  (demande de fusion non créée automatiquement, voir $ATELIER/pr.log)"
  fi
fi
echo "  Le site publie ensuite tout seul : deploy-pages.yml sur main."
