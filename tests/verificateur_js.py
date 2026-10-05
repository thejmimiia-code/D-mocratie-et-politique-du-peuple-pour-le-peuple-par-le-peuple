"""Vérificateur d'équilibre des délimiteurs d'un source JavaScript.

Le simulateur sert une page dont tout le JavaScript vit dans une chaîne Python :
une accolade oubliée ne se voit qu'à l'exécution, dans le navigateur de
l'utilisateur. Ce module fournit un contrôle statique minimal (délimiteurs,
chaînes, gabarits `` `…${…}` ``, littéraux d'expression régulière,
commentaires) utilisable par les tests comme par la ligne de commande.
"""

from __future__ import annotations

OUVRANTS = {"(": ")", "[": "]", "{": "}"}
FERMANTS = {v: k for k, v in OUVRANTS.items()}
#: Caractères après lesquels un « / » ouvre une expression régulière.
AVANT_REGEX = set("(,=:[!&|?{};+-*%<>~^") | {"\n", "\t", " "}


def _ligne(texte: str, index: int) -> int:
    return texte.count("\n", 0, index) + 1


def verifier_js(texte: str) -> tuple[bool, str]:
    """Retourne (équilibré, message) en ignorant chaînes, gabarits et commentaires."""
    pile: list[tuple[str, int]] = []   # délimiteurs ouvrants (code) : (symbole, position)
    contextes: list[tuple[str, str]] = [("code", "")]  # ("code", "") ou ("chaine", guillemet)
    precedents: list[str] = ["\n"]     # dernier caractère signifiant, par contexte
    #: Profondeur de pile à l'entrée de chaque substitution `${…}` : c'est elle
    #: qui distingue l'accolade fermante de la substitution de celle d'un objet
    #: littéral imbriqué (`` `${f({})}` ``).
    profondeurs: list[int] = []
    i, n = 0, len(texte)
    while i < n:
        genre, cle = contextes[-1]
        c = texte[i]

        if genre == "chaine":
            if c == "\\":
                i += 2
                continue
            if c == cle:
                contextes.pop()
                precedents.pop()
                i += 1
                continue
            if c == "\n":                      # chaîne non terminée : on sort
                contextes.pop()
                precedents.pop()
                continue
            i += 1
            continue

        if genre == "code" and cle == "gabarit":
            # À l'intérieur d'un gabarit `` ` `` : seuls « ` » et « ${ » comptent.
            if c == "\\":
                i += 2
                continue
            if c == "`":
                contextes.pop()
                precedents.pop()
                precedents[-1] = "`"
                i += 1
                continue
            if c == "$" and i + 1 < n and texte[i + 1] == "{":
                pile.append(("{", i))
                contextes.append(("code", "substitution"))
                precedents.append("{")
                profondeurs.append(len(pile))
                i += 2
                continue
            i += 1
            continue

        # ── code (racine ou substitution) ───────────────────────────────────
        precedent = precedents[-1]
        if c == "/" and i + 1 < n and texte[i + 1] == "/":
            while i < n and texte[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and texte[i + 1] == "*":
            i += 2
            while i + 1 < n and not (texte[i] == "*" and texte[i + 1] == "/"):
                i += 1
            i += 2
            continue
        if c == "/" and precedent in AVANT_REGEX:
            i += 1
            dans_classe = False
            while i < n:
                if texte[i] == "\\":
                    i += 2
                    continue
                if texte[i] == "[":
                    dans_classe = True
                elif texte[i] == "]":
                    dans_classe = False
                elif texte[i] == "/" and not dans_classe:
                    break
                elif texte[i] == "\n":
                    break
                i += 1
            i += 1
            while i < n and texte[i].isalpha():      # drapeaux (/g, /i, /m…)
                i += 1
            precedents[-1] = "/"
            continue
        if c in "'\"":
            contextes.append(("chaine", c))
            precedents.append(c)
            i += 1
            continue
        if c == "`":
            contextes.append(("code", "gabarit"))
            precedents.append("`")
            i += 1
            continue
        if c in OUVRANTS:
            pile.append((c, i))
        elif c == "}" and cle == "substitution" and len(pile) == profondeurs[-1]:
            # L'accolade ramène la pile à sa profondeur d'entrée : c'est celle
            # de la substitution. Celles des objets littéraux ont déjà été
            # consommées par la branche générique ci-dessous.
            pile.pop()
            contextes.pop()
            precedents.pop()
            profondeurs.pop()
            precedents[-1] = "}"
            i += 1
            continue
        elif c == "}" and cle == "substitution":
            if not pile or pile[-1][0] != "{":
                return False, f"gabarit « ${{ » non fermé ligne {_ligne(texte, i)}"
            pile.pop()
        elif c in FERMANTS:
            if not pile or pile[-1][0] != FERMANTS[c]:
                return False, f"délimiteur « {c} » inattendu ligne {_ligne(texte, i)}"
            pile.pop()
        if not c.isspace():
            precedents[-1] = c
        i += 1

    if pile or len(contextes) != 1:
        details = ", ".join(f"« {symbole} » ligne {_ligne(texte, position)}"
                            for symbole, position in pile[-4:])
        return False, f"non fermé : {details or contextes[-1][0]}"
    return True, "équilibré"


if __name__ == "__main__":  # pragma: no cover - outil en ligne de commande
    import re
    import sys

    sys.path.insert(0, ".")
    from simulateur.interface import HTML_PAGE

    script = "\n".join(re.findall(r"<script>(.*?)</script>", HTML_PAGE, re.S))
    ok, message = verifier_js(script)
    print(("OK" if ok else "ÉCHEC") + " : " + message)
    raise SystemExit(0 if ok else 1)
