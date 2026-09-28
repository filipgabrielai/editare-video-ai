import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from procese.reel import taietura as T  # noqa: E402

WS = [{"text": t} for t in ["Și", "totodată,", "în", "aplicație", "pot", "în", "aplicație,", "ca"]]


class TestCuvinte(unittest.TestCase):
    def test_idx_prima_a_doua_si_ultima_aparitie(self):
        self.assertEqual(T.idx(WS, "în"), 2)
        self.assertEqual(T.idx(WS, "aplicație#2"), 6)
        self.assertEqual(T.idx(WS, "în@ultimul"), 5)
        self.assertEqual(T.idx(WS, "totodată"), 1)

    def test_idx_cuvant_lipsa_spune_ce_exista(self):
        with self.assertRaises(SystemExit) as e:
            T.idx(WS, "YouTube")
        self.assertIn("aplicație", str(e.exception))


class TestCapete(unittest.TestCase):
    def rms(self, a, b):   # liniște (−80 dB), vorbire (−20 dB) între a și b secunde
        return [(-20.0 if a <= k * T.PAS < b else -80.0) for k in range(int(4 / T.PAS))]

    def test_capete_pe_grila_de_cadre_cu_pad(self):
        a0, a1 = T.capete(self.rms(1.0, 2.0), 1.02, 1.98, 0.0, 1e9)
        self.assertAlmostEqual(a0 * T.FPS, round(a0 * T.FPS), places=6)
        self.assertAlmostEqual(a1 * T.FPS, round(a1 * T.FPS), places=6)
        self.assertTrue(0.9 <= a0 <= 0.97, a0)
        self.assertTrue(1.99 <= a1 <= 2.1, a1)

    def test_nu_trece_de_cuvantul_urmator(self):
        _, a1 = T.capete(self.rms(1.0, 2.5), 1.02, 1.98, 0.0, 2.2)
        self.assertLessEqual(a1, 2.2)


class TestFiltre(unittest.TestCase):
    def test_umple_9_16_fara_deformare_si_exact_pe_cadre(self):
        f = T.filtre([("IMG_1", 1.5, 3.0), ("IMG_2", 0.0, 1.0)], [0.5, 0.0])
        self.assertIn("trim=end_frame=90", f)
        self.assertIn("force_original_aspect_ratio=increase", f)
        self.assertIn("crop=1080:1920", f)
        self.assertNotIn("trim=-", f)   # bucata care începe la 0 nu primește start negativ
        self.assertTrue(f.endswith("concat=n=2:v=1:a=1[v][a]"))


if __name__ == "__main__":
    unittest.main()
