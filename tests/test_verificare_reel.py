import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verificare import reel as V  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
