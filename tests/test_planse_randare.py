import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from procese.editare import planse, randeaza  # noqa: E402


class TestPlanse(unittest.TestCase):
    def test_zonele_instagram(self):
        f = planse.filtru_zone()
        self.assertIn("drawbox=x=0:y=0:w=1080:h=260", f)
        self.assertIn("y=1640", f)
        self.assertIn("x=950:y=1120", f)

    def test_zonele_pe_orizontala(self):
        f = planse.filtru_zone("16:9")
        self.assertIn("drawbox=x=0:y=1026:w=1920:h=54", f)
        self.assertNotIn("1640", f)

    def test_momente_intrare_mijloc_iesire(self):
        m = planse.momente([{"id": "a", "intra": 0.05, "iese": 4.0}, {"id": "b", "intra": 4.08, "iese": 5.0}])
        self.assertEqual(m, [0.65, 2.02, 3.7, 4.54, 4.68, 4.7])   # (0,05+4)/2 = 2,025 e în binar 2,02499…


class TestRandare(unittest.TestCase):
    def test_draftul_urmator(self):
        with tempfile.TemporaryDirectory() as d:
            dosar = Path(d)
            self.assertEqual(randeaza.urmatorul_draft(dosar, "Reel ăî").name, "Reel ăî DRAFT 1.mp4")
            (dosar / "Reel ăî DRAFT 1.mp4").write_text("x")
            (dosar / "Reel ăî DRAFT 3.mp4").write_text("x")
            self.assertEqual(randeaza.urmatorul_draft(dosar, "Reel ăî").name, "Reel ăî DRAFT 4.mp4")

    def test_titlu_cu_paranteze_patrate(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "Top [AI] DRAFT 1.mp4").write_text("x")
            self.assertEqual(randeaza.urmatorul_draft(Path(d), "Top [AI]").name, "Top [AI] DRAFT 2.mp4")

    def test_titlu_cu_caractere_interzise_pe_windows(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(randeaza.urmatorul_draft(Path(d), "Claude vs ChatGPT: 3 diferențe?").name,
                             "Claude vs ChatGPT 3 diferențe DRAFT 1.mp4")
            self.assertEqual(randeaza.urmatorul_draft(Path(d), 'a/b\\c*"d"<e>|').name, "abcde DRAFT 1.mp4")

    def test_verify_md_cu_cifrele(self):
        from verificare import video as V
        with tempfile.TemporaryDirectory() as d:
            r = V.evalueaza(V.Rezultat(negre=[], lag=[(1.0, 0, 0.9)], taieturi=[(1.0, 1.0, 0.0)], lufs=-14.1))
            randeaza.scrie_verify(Path(d), Path(d) / "Reel DRAFT 1.mp4", r)
            text = (Path(d) / "VERIFY.md").read_text(encoding="utf-8")
        self.assertIn("Reel DRAFT 1.mp4", text)
        self.assertIn("-14.1 LUFS", text)
        self.assertIn("TRECE", text)


if __name__ == "__main__":
    unittest.main()
