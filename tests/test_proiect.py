import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unelte import proiect  # noqa: E402


class TestProiect(unittest.TestCase):
    def test_slug_fara_diacritice(self):
        self.assertEqual(proiect.slug("Reel Productivitate maximă cu AI"), "reel-productivitate-maxima-cu-ai")
        self.assertEqual(proiect.slug("  Ștefan & Țara!! "), "stefan-tara")
        self.assertEqual(proiect.slug("ăîș"), "ais")
        self.assertEqual(proiect.slug("!!!"), "video")

    def test_nume_clip(self):
        self.assertEqual(proiect.nume_clip("IMG_1544", 1), "IMG_1544")
        self.assertEqual(proiect.nume_clip("Clipul ăsta", 2), "clip02")

    def test_creeaza_din_folder_cu_diacritice(self):
        with tempfile.TemporaryDirectory() as d:
            sursa = Path(d) / "Filmări noi"
            sursa.mkdir()
            for n in ("IMG_2.MOV", "Clip ăsta.mp4", "note.txt"):
                (sursa / n).write_text("x")
            with mock.patch.object(proiect, "PROIECTE", Path(d) / "proiecte"):
                dosar = proiect.creeaza(sursa, "Reel de probă")
                harta = proiect.clipuri(dosar)
            self.assertEqual(dosar.name, "reel-de-proba")
            self.assertEqual(sorted(harta), ["IMG_2", "clip01"])
            self.assertTrue((dosar / "lucru").is_dir())
            self.assertEqual(json.loads((dosar / "sursa.json").read_text(encoding="utf-8"))["clipuri"]["clip01"], str((sursa / "Clip ăsta.mp4").resolve()))

    def test_folder_fara_clipuri(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaises(SystemExit):
            proiect.creeaza(Path(d))

    def test_clipuri_schimbate_sterg_ce_s_a_calculat_din_cele_vechi(self):
        # refilmezi „Clipul ăsta.mp4” în același folder: sunetul și cuvintele vechi nu au voie să rămână
        with tempfile.TemporaryDirectory() as d:
            sursa = Path(d) / "clipuri"
            sursa.mkdir()
            (sursa / "Clipul ăsta.mp4").write_text("vechi")
            with mock.patch.object(proiect, "PROIECTE", Path(d) / "proiecte"):
                dosar = proiect.creeaza(sursa)
                (dosar / "lucru" / "clip01.wav").write_text("sunet vechi")
                (dosar / "transcripte").mkdir()
                (dosar / "duble.json").write_text("[]")
                proiect.creeaza(sursa)                       # nimic schimbat: cache-ul rămâne
                self.assertTrue((dosar / "lucru" / "clip01.wav").exists())
                (sursa / "Clipul ăsta.mp4").write_text("filmat din nou, alt conținut")
                proiect.creeaza(sursa)
            self.assertFalse((dosar / "lucru" / "clip01.wav").exists())
            self.assertFalse((dosar / "transcripte").exists())
            self.assertFalse((dosar / "duble.json").exists())

    def test_formatul_proiectului(self):
        with tempfile.TemporaryDirectory() as d:
            dosar = Path(d)
            self.assertEqual(proiect.format_proiect(dosar, {"carduri": []}), "9:16")      # proiect făcut înainte: fără nimic scris
            (dosar / "taieturi.json").write_text(json.dumps({"taieturi": [], "bucati": []}), encoding="utf-8")
            self.assertEqual(proiect.format_proiect(dosar, {}), "9:16")                   # taieturi.json din v1, fără „filmare”
            (dosar / "taieturi.json").write_text(json.dumps({"taieturi": [], "bucati": [], "filmare": "16:9"}), encoding="utf-8")
            self.assertEqual(proiect.format_proiect(dosar, {}), "16:9")                   # scenariul nu spune: formatul filmării
            self.assertEqual(proiect.format_proiect(dosar, {"format": "16:9"}), "16:9")
            with self.assertRaises(SystemExit) as e:
                proiect.format_proiect(dosar, {"format": "9:16"})
            self.assertIn("--filmare 9:16", str(e.exception))


if __name__ == "__main__":
    unittest.main()
