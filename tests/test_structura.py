import os
import unittest
from pathlib import Path

RAD = Path(__file__).resolve().parents[1]
SARITE = {"node_modules", "proiecte", "lucru-demo", "modele", ".git", "brand", ".superpowers", "__pycache__"}
VECHI = ("procese.reel", "procese/reel", "verificare/reel.py", "verificare import reel")


def fisiere():
    for radacina, dosare, nume in os.walk(RAD):
        dosare[:] = [d for d in dosare if d not in SARITE]
        for n in nume:
            if n.endswith((".py", ".md", ".yml")) and n != "test_structura.py":
                yield Path(radacina) / n


class TestStructura(unittest.TestCase):
    def test_procesele_stau_in_procese_editare(self):
        self.assertTrue((RAD / "procese" / "editare" / "taietura.py").is_file())
        self.assertTrue((RAD / "verificare" / "video.py").is_file())
        self.assertFalse((RAD / "procese" / "reel").exists())

    def test_nimic_nu_mai_trimite_la_caile_vechi(self):
        gasite = [f"{p.relative_to(RAD)}: {v}" for p in fisiere() for v in VECHI if v in p.read_text(encoding="utf-8")]
        self.assertEqual(gasite, [])


if __name__ == "__main__":
    unittest.main()
