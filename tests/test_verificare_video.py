import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verificare import video as V  # noqa: E402


class TestVerificareReel(unittest.TestCase):
    def test_xcorr_gaseste_decalajul(self):
        a = [0.0] * 30 + [1.0, 3.0, 1.0] + [0.0] * 60
        b = [0.0] * 33 + [1.0, 3.0, 1.0] + [0.0] * 57
        lag, c = V.xcorr(a, b)
        self.assertEqual(lag, 3)
        self.assertGreater(c, 0.9)

    def test_potriveste_taieturile(self):
        p = V.potriveste([1.0, 2.5], [0.998, 2.52, 7.0])
        self.assertEqual(round(p[0][2]), 2)
        self.assertEqual(round(p[1][2]), 20)
        self.assertEqual(V.potriveste([1.0], []), [(1.0, None, None)])

    def test_evalueaza(self):
        bun = V.Rezultat(negre=[], lag=[(1.0, 0, 0.9)], taieturi=[(1.0, 1.0, 0.0)], lufs=-14.1)
        self.assertTrue(V.evalueaza(bun).ok)
        rau = V.Rezultat(negre=[(3.0, 3.2)], lag=[(1.0, 30, 0.9)], taieturi=[(1.0, 1.05, 50.0)], lufs=-16.0)
        r = V.evalueaza(rau)
        self.assertFalse(r.ok)
        self.assertEqual(len(r.probleme), 4)

    def test_lag_cu_corelatie_slaba_nu_e_problema(self):
        r = V.evalueaza(V.Rezultat(negre=[], lag=[(1.0, 40, 0.2)], taieturi=[], lufs=-14.0))
        self.assertTrue(r.ok)

    def test_un_punct_slab_langa_sunetele_de_card_nu_e_decalaj(self):
        # reelul „Top 3”: 8 puncte la 0 ms, unul la +60 ms cu corelație 0,54 (fereastra prindea sunetul de card, care nu e în voce.wav)
        lag = [(1.0, 0, 0.9), (6.15, 60, 0.54), (10.0, 0, 0.8), (15.0, 0, 0.85)]
        self.assertTrue(V.evalueaza(V.Rezultat(negre=[], lag=lag, taieturi=[], lufs=-14.0)).ok)

    def test_decalaj_clar_sau_repetat_nu_trece(self):
        clar = [(1.0, 0, 0.9), (6.0, 50, 0.9)]
        repetat = [(1.0, 50, 0.6), (6.0, 50, 0.55), (10.0, 0, 0.9)]
        self.assertFalse(V.evalueaza(V.Rezultat(negre=[], lag=clar, taieturi=[], lufs=-14.0)).ok)
        self.assertFalse(V.evalueaza(V.Rezultat(negre=[], lag=repetat, taieturi=[], lufs=-14.0)).ok)

    def test_un_cadru_pe_langa_la_60_fps_nu_trece(self):
        r = V.evalueaza(V.Rezultat(negre=[], lag=[], taieturi=[(1.0, 1.0 + 1 / 60, 1000 / 60)], lufs=-14.0, fps=60))
        self.assertFalse(r.ok)
        r30 = V.evalueaza(V.Rezultat(negre=[], lag=[], taieturi=[(1.0, 1.0 + 1 / 60, 1000 / 60)], lufs=-14.0, fps=30))
        self.assertTrue(r30.ok)   # la 30 fps, tăietura de pe grila de 60 cade între două cadre

    def test_durata_diferita_nu_trece(self):
        r = V.evalueaza(V.Rezultat(negre=[], lag=[], taieturi=[], lufs=-14.0, fps=60, durata=44.75, durata_asteptata=45.75))
        self.assertFalse(r.ok)
        self.assertTrue(any("durata" in p for p in r.probleme))


@unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg lipsește")
class TestVerificareaPrindeGreselile(unittest.TestCase):
    """Randări stricate intenționat, ca verificarea să dovedească că le prinde, nu doar că trece pe cele bune."""
    PROBA = str(Path(__file__).resolve().parent / "date" / "proba.wav")

    def video(self, iesire, af="anull"):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=320x568:r=60:d=3.9", "-i", self.PROBA,
                        "-af", af, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(iesire)], check=True)

    def test_vocea_decalata_cu_50_ms(self):
        with tempfile.TemporaryDirectory() as d:
            voce, bun, rau = Path(d) / "voce.wav", Path(d) / "bun.mp4", Path(d) / "rau.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", self.PROBA, "-ar", "48000", str(voce)], check=True)
            self.video(bun)
            self.video(rau, "adelay=50")
            p_bun = V.verifica(bun, voce, [], 60).probleme
            p_rau = V.verifica(rau, voce, [], 60).probleme
        self.assertFalse(any("decalată" in p for p in p_bun), p_bun)
        self.assertTrue(any("decalată" in p for p in p_rau), p_rau)

    def test_taietura_cu_un_cadru_pe_langa(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "taiat.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=320x568:r=60:d=1", "-f", "lavfi", "-i",
                            "color=c=orange:s=320x568:r=60:d=1", "-filter_complex", "[0:v][1:v]concat=n=2:v=1[v]", "-map", "[v]",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(f)], check=True)
            sc = V.scene(f)
        bun = V.evalueaza(V.Rezultat(negre=[], lag=[], taieturi=V.potriveste([1.0], sc), lufs=-14.0, fps=60))
        rau = V.evalueaza(V.Rezultat(negre=[], lag=[], taieturi=V.potriveste([1.0 + 1 / 60], sc), lufs=-14.0, fps=60))
        self.assertTrue(bun.ok, bun.probleme)
        self.assertFalse(rau.ok)

    def test_un_singur_cadru_negru(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "negru.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=320x568:r=60:d=1", "-f", "lavfi", "-i",
                            "color=c=black:s=320x568:r=60:d=0.0167", "-f", "lavfi", "-i", "testsrc2=s=320x568:r=60:d=1",
                            "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1[v]", "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                            str(f)], check=True)
            self.assertTrue(V.negre(f))


if __name__ == "__main__":
    unittest.main()
