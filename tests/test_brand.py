import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unelte import brand  # noqa: E402


class TestBrand(unittest.TestCase):
    def test_fara_fisier_implicitele(self):
        with tempfile.TemporaryDirectory() as d:
            b = brand.incarca(Path(d))
        self.assertEqual(b, brand.IMPLICIT)
        self.assertIsNot(b, brand.IMPLICIT)

    def test_partial_si_scris_de_mana(self):
        b, erori = brand.combina({"culori": {"accent": "#3BF"}, "preferinte": {"filtru_fata": "Ușor", "sunete": "încete"}})
        self.assertEqual(erori, [])
        self.assertEqual(b["culori"]["accent"], "#33bbff")
        self.assertEqual(b["preferinte"]["filtru_fata"], "usor")
        self.assertEqual(b["preferinte"]["sunete"], "incete")
        self.assertTrue(b["preferinte"]["captions"])          # ce nu a scris rămâne implicit
        self.assertEqual(b["preferinte"]["limba"], "ro")

    def test_greselile_spuse_exact(self):
        _, erori = brand.combina({"culori": {"accent": "albastru"}, "logo": "logo.gif",
                                  "preferinte": {"captions": "da", "sunete": "tare", "limba": "română"}})
        text = "\n".join(erori)
        for x in ("culori.accent", "„logo”", "preferinte.captions", "preferinte.sunete", "preferinte.limba"):
            self.assertIn(x, text)

    def test_fisierele_lipsa_si_json_stricat(self):
        with tempfile.TemporaryDirectory(prefix="brand ș ") as d:
            (Path(d) / "brand.json").write_text(json.dumps({"logo": "logo.png"}), encoding="utf-8")
            with self.assertRaises(SystemExit) as e:
                brand.incarca(Path(d))
            self.assertIn("logo.png nu e în brand/", str(e.exception))
            (Path(d) / "brand.json").write_text("{nu e json", encoding="utf-8")
            with self.assertRaises(SystemExit) as e:
                brand.incarca(Path(d))
            self.assertIn("nu e JSON valid", str(e.exception))

    def test_css_stil_si_fisierele_cu_diacritice(self):
        with tempfile.TemporaryDirectory(prefix="brand ă ") as d:
            bd = Path(d) / "brand"
            bd.mkdir()
            (bd / "Logo nou ș.png").write_bytes(b"x")
            (bd / "Fontul meu.ttf").write_bytes(b"x")
            b, erori = brand.combina({"culori": {"accent": "#ff5500", "accent_2": "#112233"}, "logo": "Logo nou ș.png",
                                      "font": "Fontul meu.ttf"})
            self.assertEqual(erori, [])
            brand.copiaza(b, Path(d) / "assets", bd)
            self.assertTrue((Path(d) / "assets" / "brand" / "logo.png").is_file())
            self.assertTrue((Path(d) / "assets" / "brand" / "font.ttf").is_file())
        css = brand.css(b)
        self.assertIn("--accent:#ff5500", css)
        self.assertIn("--accent-rgb:255,85,0", css)
        self.assertIn("--accent-2:#112233", css)
        self.assertIn("url('brand/font.ttf')", css)
        self.assertEqual(brand.logo_html(b), '<img class="kl" src="assets/brand/logo.png" alt="">')
        st = brand.stil({"nume": "Studio", "accent": "#38bdf8", "accent_rgb": "56,189,248"}, b)
        self.assertEqual((st["accent"], st["accent_rgb"]), ("#ff5500", "255,85,0"))
        self.assertEqual(brand.css(brand.IMPLICIT), "")
        self.assertEqual(brand.logo_html(brand.IMPLICIT), "")

    def test_sunete_filtru_limba(self):
        lista = [(0.05, "boom", 0.6, 0.6), (2.0, "pop", 0.55, 0.12)]
        b, _ = brand.combina({"preferinte": {"sunete": "incete", "filtru_fata": "usor", "limba": "EN"}})
        self.assertEqual(brand.sunete(lista, b), [(0.05, "boom", 0.3, 0.6), (2.0, "pop", 0.275, 0.12)])
        self.assertIn("smartblur", brand.filtru_fata(b))
        self.assertEqual(brand.limba(b), "en")
        b, _ = brand.combina({"preferinte": {"sunete": "oprite"}})
        self.assertEqual(brand.sunete(lista, b), [])
        self.assertEqual(brand.filtru_fata(brand.IMPLICIT), "")


if __name__ == "__main__":
    unittest.main()
