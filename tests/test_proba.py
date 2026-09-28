import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import proba_30s as P  # noqa: E402


class TestProba(unittest.TestCase):
    def test_fara_diacritice(self):
        self.assertEqual(P.fara_diacritice("Câte lucruri ȘI Țări"), "cate lucruri si tari")

    def test_modelul_mare_cere_cuvintele_cheie(self):
        mare = Path("ggml-large-v3-turbo.bin")
        self.assertTrue(P.transcriere_buna("Mi se pare incredibil câte lucruri poți să faci și cât de productiv poți să fii.", mare))
        self.assertFalse(P.transcriere_buna("Mulțumim pentru vizionare!", mare))

    def test_modelul_mic_cere_doar_text(self):
        mic = Path("ggml-tiny.bin")
        self.assertTrue(P.transcriere_buna("mi se pare incredibil", mic))
        self.assertFalse(P.transcriere_buna("", mic))


if __name__ == "__main__":
    unittest.main()
