import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unelte import formate  # noqa: E402


class TestFormate(unittest.TestCase):
    def test_dimensiuni(self):
        self.assertEqual(formate.dimensiuni("9:16"), (1080, 1920))
        self.assertEqual(formate.dimensiuni("16:9"), (1920, 1080))

    def test_format_necunoscut_spune_ce_exista(self):
        with self.assertRaises(SystemExit) as e:
            formate.dimensiuni("4:5")
        self.assertIn("9:16", str(e.exception))
        self.assertIn("16:9", str(e.exception))

    def test_orientarea_tine_cont_de_rotatie(self):
        self.assertTrue(formate.e_orizontal(1920, 1080))
        self.assertFalse(formate.e_orizontal(1080, 1920))
        self.assertFalse(formate.e_orizontal(1920, 1080, -90))   # iPhone ținut vertical: 1920x1080 cu rotație
        self.assertTrue(formate.e_orizontal(1080, 1920, 90))

    def test_zonele_stau_in_cadru(self):
        for f, (w, h) in formate.FORMATE.items():
            for x, y, lat, inalt in formate.ZONE[f]:
                self.assertTrue(0 <= x and x + lat <= w and 0 <= y and y + inalt <= h, (f, x, y, lat, inalt))


if __name__ == "__main__":
    unittest.main()
