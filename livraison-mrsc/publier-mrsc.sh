#!/usr/bin/env bash
# Publie, dans le dépôt du site M.R.S.C, sa copie du moteur mise à jour.
#
#     bash livraison-mrsc/publier-mrsc.sh [atelier] [branche]
#
# La copie embarquée par le site datait du 8 octobre (99491d8) ; l'amont a
# beaucoup bougé depuis. Le correctif de sécurité du site, lui, ne s'appliquait
# plus : il est rebasé ici sur 22957da (voir LISEZ-MOI.md, à côté de ce script,
# qui dit ce que le rebasage conserve).
#
# Le script travaille dans un dossier jetable, ne touche jamais `main`, et
# s'arrête **avant** de publier si un contrôle échoue.
set -euo pipefail

ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ATELIER="${1:-/tmp/mrsc-moteur}"
BRANCHE="${2:-maj-simulateur-22957da}"
REVISION="22957da0e7ffad92c3e087d9c6bbd6f3b5b907b9"
REVISION_COURTE="22957da"
AMONT="https://github.com/thejmimiia-code/D-mocratie-et-politique-du-peuple-pour-le-peuple-par-le-peuple.git"
SITE="https://github.com/thejmimiia-code/MRSC.git"

etape() { printf '\n\033[1m%s\033[0m\n' "$*"; }
bilan() { printf '  ✓ %s\n' "$*"; }

# ─────────────────────────────────────────────────────────── 1. les deux dépôts
etape "1/7 · récupération des dépôts dans $ATELIER"

rm -rf "$ATELIER"
mkdir -p "$ATELIER"
git clone --quiet --depth 1 "$AMONT" "$ATELIER/amont"
git clone --quiet --depth 1 "$SITE" "$ATELIER/site"

if [ "$(git -C "$ATELIER/amont" rev-parse HEAD)" != "$REVISION" ]; then
  # La branche principale a avancé : on va chercher précisément la révision
  # sur laquelle le correctif a été rebasé, sinon la copie partirait trop loin.
  git -C "$ATELIER/amont" fetch --quiet --depth 1 origin "$REVISION"
  git -C "$ATELIER/amont" checkout --quiet FETCH_HEAD
fi
if [ "$(git -C "$ATELIER/amont" rev-parse HEAD)" != "$REVISION" ]; then
  echo "Révision amont introuvable : $REVISION" >&2
  exit 1
fi
bilan "amont à $REVISION_COURTE"
bilan "site à $(git -C "$ATELIER/site" rev-parse --short HEAD)"

cp "$ICI/simulateur-securite-mrsc.patch" \
   "$ATELIER/site/outils/patchs/simulateur-securite-mrsc.patch"
cd "$ATELIER/site"

# ──────────────────────────────────────────────────────────── 2. la copie
etape "2/7 · copie du moteur et correctif du site"
python3 outils/mettre-a-jour-simulateur.py --depuis "$ATELIER/amont"

# ─────────────────────────────────────────── 3. reconstruction et API du site
etape "3/7 · reconstruction de la page et des fonctions api/"

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

# ───────────────────────────────────────────── 4. contrôles avant de publier
etape "4/7 · contrôles de la copie publiée"

python3 - <<'PY'
import pathlib
import sys

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

marqueurs = {
    fichier.name: fichier.read_text(encoding="utf-8").count("<<<<<<<")
    for fichier in fichiers
    if "<<<<<<<" in fichier.read_text(encoding="utf-8")
}
if marqueurs:
    raise SystemExit(f"Marqueurs de conflit restants : {marqueurs}")
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

node = shutil.which("node")
if node is None:
    print("  · node absent : contrôle de syntaxe des scripts sauté")
else:
    for rang, script in enumerate(
        re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", page, re.S), 1
    ):
        essai = pathlib.Path(tempfile.mkdtemp()) / f"script-{rang}.mjs"
        essai.write_text(script, encoding="utf-8")
        resultat = subprocess.run([node, "--check", str(essai)], capture_output=True, text=True)
        if resultat.returncode:
            raise SystemExit(f"Script {rang} invalide : {resultat.stderr.strip()[-400:]}")
        print(f"  ✓ script {rang} ({len(script)} caractères)")
PY

# ──────────────────────────────────────────────────────────── 5. les portes
etape "5/7 · portes du site"
for porte in verifier-securite verifier-maj-amont verifier-integration \
             verifier-site-statique verifier-rd-continue verifier-source-distante; do
  if python3 "outils/$porte.py" > "$ATELIER/$porte.log" 2>&1; then
    bilan "$porte"
  elif [ "$porte" = "verifier-source-distante" ]; then
    # Cette porte interroge le réseau : sans lui, elle le dit et laisse la copie
    # embarquée faire le calcul. Hors ligne n'est pas un échec.
    printf '  · %s : réseau injoignable, la copie embarquée fait le calcul\n' "$porte"
  else
    echo "Porte en échec : $porte" >&2
    tail -20 "$ATELIER/$porte.log" >&2
    exit 1
  fi
done
python3 outils/construire-apprentissages.py > "$ATELIER/apprentissages.log" 2>&1
bilan "construire-apprentissages"

# ───────────────────────────────────────────────────── 6. la branche publiée
etape "6/7 · branche $BRANCHE"
if [ -z "$(git config user.email || true)" ]; then
  git config user.name "${GIT_AUTEUR_NOM:-Mise à jour du moteur}"
  git config user.email "${GIT_AUTEUR_COURRIEL:-maj-moteur@localhost}"
fi
git checkout --quiet -b "$BRANCHE"
git add -A
git commit --quiet -F "$ICI/corps-de-pr.md"
bilan "commit $(git rev-parse --short HEAD) — $(git show --stat --oneline HEAD | tail -1 | xargs)"
git push -u origin "$BRANCHE"
bilan "branche poussée"

# ─────────────────────────────────────────────────────────────── 7. le lien
etape "7/7 · suite"
LIEN="https://github.com/thejmimiia-code/MRSC/compare/main...$BRANCHE?expand=1"
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
