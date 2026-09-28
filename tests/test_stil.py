import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAD))
from unelte import sunete  # noqa: E402


class TestStil(unittest.TestCase):
    def test_studio_are_tot(self):
        st = json.load(open(RAD / "stiluri" / "studio" / "stil.json", encoding="utf-8"))
        self.assertTrue(st["accent"].startswith("#"))
        css = (RAD / "stiluri" / "studio" / "reel.css").read_text(encoding="utf-8")
        for sel in (".card", ".card.compact", ".chip", ".cap", ".cw", "#titlu", "#captii", "var(--carduri-y)", "var(--captions-y)"):
            self.assertIn(sel, css)
        self.assertNotIn("googleapis", css)   # fără fonturi de pe internet la randare

    def test_fonturi_locale_cu_licenta(self):
        self.assertEqual(len(list((RAD / "fonturi").glob("*.woff2"))), 8)
        self.assertEqual(len(list((RAD / "fonturi").glob("OFL-*.txt"))), 3)

    def test_icoane(self):
        ic = json.load(open(RAD / "stiluri" / "icoane.json", encoding="utf-8"))
        self.assertIn("check", ic)
        self.assertTrue(all(v.startswith("<svg") for v in ic.values()))

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg lipsește")
    def test_sunetele_generate(self):
        with tempfile.TemporaryDirectory() as d:
            fis = sunete.genereaza(Path(d))
            self.assertEqual(sorted(p.stem for p in fis), sorted(sunete.SUNETE))
            for p in fis:
                r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                   capture_output=True, text=True, check=True)
                self.assertAlmostEqual(float(r.stdout), sunete.SUNETE[p.stem][1], delta=0.02)


if __name__ == "__main__":
    unittest.main()
