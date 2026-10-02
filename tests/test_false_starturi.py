import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from procese.editare import false_starturi as F  # noqa: E402


def r10():
    """„Dacă vrei să-ți trimit kit,” (1,00–2,45 s), pauză de 0,27 s, apoi fraza întreagă (2,72–6,00 s)."""
    r = [-80.0] * 700
    for k in list(range(100, 245)) + list(range(272, 600)):
        r[k] = -20.0
    return r


class TestFalseStarturi(unittest.TestCase):
    def test_pauza_din_interior(self):
        self.assertEqual(F.pauze_interioare(r10(), 0.9, 6.1), [(2.45, 2.72)])
        fara = [-20.0 if 100 <= k < 600 else -80.0 for k in range(700)]
        self.assertEqual(F.pauze_interioare(fara, 0.9, 6.1), [])
        scurta = r10()
        for k in range(255, 272):
            scurta[k] = -20.0            # o pauză de 0,10 s e respirație, nu reluare
        self.assertEqual(F.pauze_interioare(scurta, 0.9, 6.1), [])

    def test_ajunge_primul_cuvant(self):
        # 2 oct: cu primele două cuvinte scăpau reluările de un cuvânt („Ai | Ai peste 110”, „Nu ră- | Nu rămâi”)
        self.assertTrue(F.repeta_inceputul("Dacă vrei să-ți trimit kit,", "Dacă vrei să-ți trimit kitul complet"))
        self.assertTrue(F.repeta_inceputul("Ai", "Ai peste 110 lecții"))
        self.assertTrue(F.repeta_inceputul("Înăuntru", "Înăuntrul comunității"))   # cuvântul rupt e începutul celui reluat
        self.assertTrue(F.repeta_inceputul("Nu ră-", "Nu rămâi blocat"))
        self.assertFalse(F.repeta_inceputul("A", "Am scris o comandă"))             # o literă nu ajunge
        self.assertFalse(F.repeta_inceputul("Unul îți editează videourile,", "altul îți scrie"))
        self.assertFalse(F.repeta_inceputul("", "Dacă"))

    def test_cauta_marcheaza_si_spune_de_unde_se_reia(self):
        auzit = {True: "Dacă vrei să-ți trimit kit,", False: "Dacă vrei să-ți trimit kitul complet"}
        gasite = F.cauta(r10(), 0.9, 6.1, lambda a, b: auzit[b < 3.0])
        self.assertEqual(len(gasite), 1)
        self.assertTrue(gasite[0]["repeta"])
        self.assertEqual(gasite[0]["pauza"], (2.45, 2.72))
        self.assertAlmostEqual(gasite[0]["de_la_timp"], 2.64, places=2)   # 0,08 s înainte de reluare


if __name__ == "__main__":
    unittest.main()
