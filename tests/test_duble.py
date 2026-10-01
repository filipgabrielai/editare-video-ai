import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAD))
from procese.reel import duble  # noqa: E402

STDERR = """[silencedetect @ 0x1] silence_start: -0.00266667
[silencedetect @ 0x1] silence_end: 1.2 | silence_duration: 1.2
[silencedetect @ 0x1] silence_start: 4.9
[silencedetect @ 0x1] silence_end: 6.4 | silence_duration: 1.5
"""


class TestDuble(unittest.TestCase):
    def test_taceri_din_ffmpeg(self):
        st, en = duble.taceri(STDERR)
        self.assertEqual(st, [0.0, 4.9])
        self.assertEqual(en, [1.2, 6.4])

    def test_intervale_dintre_taceri(self):
        self.assertEqual(duble.intervale([0.0, 4.9], [1.2, 6.4], 10.0), [(1.2, 4.9), (6.4, 10.0)])

    def test_intervalele_prea_scurte_se_sar(self):
        # un click de 0,1 s la început și 0,2 s de zgomot la final nu sunt duble
        self.assertEqual(duble.intervale([0.1, 3.0], [0.5, 4.0], 4.2), [(0.5, 3.0)])

    @unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg lipsește")
    def test_doua_duble_despartite_de_liniste(self):
        with tempfile.TemporaryDirectory() as d:
            wav = Path(d) / "doua.wav"
            proba = str(RAD / "tests" / "date" / "proba.wav")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", proba, "-f", "lavfi", "-t", "1.5", "-i", "anullsrc=r=16000:cl=mono",
                            "-i", proba, "-filter_complex", "[0:a][1:a][2:a]concat=n=3:v=0:a=1[a]", "-map", "[a]", str(wav)], check=True)
            gasite = duble.detecteaza(wav)
        self.assertEqual(len(gasite), 2)
        self.assertLess(gasite[0][1], gasite[1][0])

    def test_limba_ajunge_la_whisper(self):
        apeluri = []

        def fals(cmd, **kw):
            apeluri.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "Hello there", "")
        with tempfile.TemporaryDirectory() as d, mock.patch.object(duble.subprocess, "run", side_effect=fals), \
                mock.patch.object(duble.platforma, "gaseste", return_value="whisper-cli"), \
                mock.patch.object(duble.platforma, "cale_pentru_unealta", side_effect=lambda p, b: str(p)):
            duble.transcrie(Path(d) / "a.wav", 0.0, 1.0, Path(d), "en")
        w = apeluri[-1]
        self.assertEqual(w[w.index("-l") + 1], "en")


if __name__ == "__main__":
    unittest.main()
