"""Vérifie que les dossiers du dépôt ont un point d'entrée HTML statique."""

import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDED_DIRS = {
    ".git",
    ".arena",
    ".cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "target",
    "venv",
}


class TestIndexesStatiques(unittest.TestCase):
    def test_chaque_dossier_du_depot_a_un_index_html(self):
        dossiers_sans_index = []
        for dossier, sous_dossiers, _ in os.walk(ROOT):
            sous_dossiers[:] = sorted(
                nom for nom in sous_dossiers if nom not in EXCLUDED_DIRS
            )
            if not (Path(dossier) / "index.html").is_file():
                dossiers_sans_index.append(Path(dossier).relative_to(ROOT).as_posix())

        self.assertEqual(dossiers_sans_index, [])

    def test_page_d_accueil_est_en_francais_et_contient_les_liens_principaux(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('<html lang="fr">', page)
        self.assertIn("Démocratie et politique", page)
        self.assertIn('href="/docs/"', page)
        self.assertIn('href="/simulateur/"', page)
        self.assertIn('href="/tests/"', page)
        self.assertIn("python -m simulateur.dashboard --port 8080", page)


if __name__ == "__main__":
    unittest.main()
