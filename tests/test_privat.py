import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verificare import privat  # noqa: E402


class TestPrivat(unittest.TestCase):
    def test_gaseste_ce_e_privat(self):
        text = "\n".join(["/Us" + "ers/ion/Desktop/clip.mov", "C:\\" + "Users\\ion\\x", "ion@" + "exemplu.ro",
                          "sk-" + "ant-abcdefghijklmnop", "comunitatea Sist" + "eme AI"])
        gasite = privat.in_text(text)
        for fel in ("cale personală", "email", "cheie", "comunitatea plătită"):
            self.assertIn(fel, " ".join(gasite))

    def test_textul_curat(self):
        self.assertEqual(privat.in_text("python3 procese/reel/taietura.py proiecte/<slug>"), [])

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg lipsește")
    def test_locatia_din_metadate(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "clip.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=s=64x64:d=0.2", "-metadata",
                            "location=+44.4268+026.1025/", str(f)], check=True)
            self.assertTrue(privat.in_metadate(f))
            curat = Path(d) / "curat.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(f), "-map_metadata", "-1", str(curat)], check=True)
            self.assertEqual(privat.in_metadate(curat), [])

    def test_repo_e_curat(self):
        self.assertEqual(privat.verifica(privat.fisiere_git()), [])


if __name__ == "__main__":
    unittest.main()
