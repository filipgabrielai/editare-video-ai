import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_tipuri_gresite_spuse_in_romana_nu_traceback(self):
        # review-ul final: „culori” scris ca listă sau ca text dădea AttributeError în loc de un mesaj
        for date in ({"culori": "#ff5500"}, {"culori": ["#ff5500", "#112233"]}, {"preferinte": "captions"}):
            _, erori = brand.combina(date)
            self.assertEqual(len(erori), 1, date)
        self.assertIn("„culori”", brand.combina({"culori": "#ff5500"})[1][0])
        self.assertIn("„preferinte”", brand.combina({"preferinte": "captions"})[1][0])

    def test_cheile_necunoscute_se_spun_cu_sugestie(self):
        # „sunet” în loc de „sunete” era ignorat în tăcere și omul credea că a oprit sunetele
        _, erori = brand.combina({"culoare": {"accent": "#ff5500"}, "culori": {"accnt": "#ff5500"}, "preferinte": {"sunet": "oprite"}})
        text = "\n".join(erori)
        for x in ("„culoare”", "„culori”?", "culori.accnt", "preferinte.sunet", "„sunete”?"):
            self.assertIn(x, text)

    def test_fontul_din_repo_dupa_nume(self):
        # specul: fontul se alege (și) din fonturile libere din repo
        b, erori = brand.combina({"font": "instrument serif"})
        self.assertEqual(erori, [])
        self.assertEqual(b["font"], "Instrument Serif")
        css = brand.css(b)
        self.assertIn("--font-display:'Instrument Serif'", css)
        self.assertNotIn("@font-face", css)
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "brand.json").write_text(json.dumps({"font": "Instrument Serif"}), encoding="utf-8")
            self.assertEqual(brand.incarca(Path(d))["font"], "Instrument Serif")   # nu cere fișier în brand/
            brand.copiaza(b, Path(d) / "assets", Path(d))
            self.assertEqual(list((Path(d) / "assets" / "brand").iterdir()), [])
        self.assertIsNone(brand.combina({"font": "Geist"})[0]["font"])   # Geist e fontul stilului

    def test_vocabularul_pentru_whisper(self):
        # ghidul @pauloshimas + proba pe demo: cu numele date din start, Whisper scrie „despre AI”, nu „despre ei”
        b, erori = brand.combina({"vocabular": [" Claude Code ", "AI", "", "bolt.new"]})
        self.assertEqual(erori, [])
        self.assertEqual(b["vocabular"], ["Claude Code", "AI", "bolt.new"])
        self.assertEqual(brand.prompt_whisper(b), "Claude Code, AI, bolt.new.")
        self.assertEqual(brand.prompt_whisper(b, "Lovable, Codex"), "Claude Code, AI, bolt.new, Lovable, Codex.")
        self.assertEqual(brand.combina({"vocabular": "Claude Code, AI"})[0]["vocabular"], ["Claude Code", "AI"])
        self.assertEqual(brand.prompt_whisper(brand.IMPLICIT), "")
        self.assertIn("„vocabular”", brand.combina({"vocabular": 5})[1][0])

    def test_vocabularul_fara_diacritice_pe_windows(self):
        # whisper.cpp pe Windows citește argumentele în codepage-ul vechi: „ș” ar ajunge „?” în prompt
        b, _ = brand.combina({"vocabular": ["Știri AI", "București"]})
        with mock.patch.object(brand.platforma, "sistem", return_value="windows"):
            self.assertEqual(brand.prompt_whisper(b), "Stiri AI, Bucuresti.")
        with mock.patch.object(brand.platforma, "sistem", return_value="mac"):
            self.assertEqual(brand.prompt_whisper(b), "Știri AI, București.")


if __name__ == "__main__":
    unittest.main()
