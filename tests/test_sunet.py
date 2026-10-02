import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from procese.editare import sunet  # noqa: E402

LOG = """[Parsed_loudnorm_0 @ 0x1]
{
	"input_i" : "-22.49",
	"input_tp" : "-6.10",
	"input_lra" : "4.20",
	"input_thresh" : "-32.70",
	"output_i" : "-14.01",
	"target_offset" : "0.01"
}
"""


class TestSunet(unittest.TestCase):
    def test_masuratoarea_din_ffmpeg(self):
        m = sunet.json_loudnorm(LOG)
        self.assertEqual(m["input_i"], "-22.49")
        self.assertEqual(sunet.parametri(m), "measured_I=-22.49:measured_TP=-6.10:measured_LRA=4.20:measured_thresh=-32.70:offset=0.01")

    def test_fara_masuratoare_da_mesaj(self):
        with self.assertRaises(SystemExit):
            sunet.json_loudnorm("nimic")

    def test_corectia_nu_muta_sunetul(self):
        self.assertEqual(sunet.corectie("lant", 0.0), "lant")
        c = sunet.corectie("lant", 1.4)
        self.assertIn("volume=1.40dB", c)
        self.assertIn("latency=1", c)          # fără compensare, limitatorul întârzie vocea cu 5 ms
        self.assertIn("level=disabled", c)     # cu auto-nivel, ridică tot sunetul până la limită

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg lipsește")
    def test_aduce_vocea_la_minus_14(self):
        with tempfile.TemporaryDirectory(prefix="sunet ăî ") as d:
            intrare, iesire = Path(d) / "in.m4a", Path(d) / "out.m4a"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(Path(__file__).resolve().parent / "date" / "proba.wav"),
                            "-af", "volume=-12dB", "-c:a", "aac", str(intrare)], check=True)
            lufs = sunet.normalizeaza(intrare, iesire)
        self.assertAlmostEqual(lufs, -14.0, delta=1.0)


if __name__ == "__main__":
    unittest.main()
