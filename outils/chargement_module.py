"""outils/chargement_module.py — charger un script dont le nom n'est pas un nom de module.

Pourquoi ce fichier existe
--------------------------
Plusieurs scripts du dépôt ne s'importent pas normalement : `verifier-compteurs.py`
porte un tiret, `api/[...path].py` porte des crochets, d'autres vivent dans
`outils/`. Les tests les chargent donc par leur chemin, avec
`importlib.util.spec_from_file_location`.

Ce chargeur-là écrit un **cache de bytecode** (`__pycache__/….pyc`) à côté du
script, et Python le croit encore valable quand la **taille** et l'**horodatage
en secondes** de la source n'ont pas bougé. Deux conséquences, vues pour de vrai
dans ce dépôt :

* une écriture de la même longueur que la précédente, faite dans la même seconde
  — `None` remplacé par `True`, par exemple — laisse Python servir l'ancien
  bytecode : le fichier sur le disque est neuf, le code chargé ne l'est pas ;
* un **sabotage** peut alors « passer » contre une version qui n'est plus celle
  du dépôt, ou être « attrapé » après avoir été restauré. C'est l'instrument de
  mesure qui ment, pas le code mesuré.

`charger_module` lit donc la source et la compile explicitement : rien n'est mis
en cache, rien n'est relu d'un fichier intermédiaire. Le coût est de quelques
millisecondes, payées une fois par test.

    from outils.chargement_module import charger_module
    verificateur = charger_module("verifier_compteurs", RACINE / "outils" / "verifier-compteurs.py")
"""

from __future__ import annotations

import sys
import types
from pathlib import Path


def charger_module(
    nom: str,
    chemin: str | Path,
    *,
    enregistrer: bool = True,
) -> types.ModuleType:
    """Exécute le fichier `chemin` comme un module nommé `nom`.

    `enregistrer` (par défaut) inscrit le module dans `sys.modules` **avant** de
    l'exécuter : c'est nécessaire aux `@dataclass` dont les annotations sont
    différées par `from __future__ import annotations`. En cas d'échec, rien ne
    reste dans `sys.modules`.
    """
    chemin = Path(chemin)
    module = types.ModuleType(nom)
    module.__file__ = str(chemin)      # les scripts qui calculent leur racine depuis __file__
    module.__package__ = ""
    if enregistrer:
        sys.modules[nom] = module
    try:
        code = compile(chemin.read_text(encoding="utf-8"), str(chemin), "exec")
        exec(code, module.__dict__)
    except BaseException:
        if enregistrer and sys.modules.get(nom) is module:
            del sys.modules[nom]
        raise
    return module
