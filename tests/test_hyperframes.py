import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unelte import hyperframes as HF  # noqa: E402


class TestHyperframes(unittest.TestCase):
    def test_porneste_node_direct(self):
        with mock.patch("shutil.which", return_value=r"C:\Program Files\nodejs\node.exe"):
            cmd = HF.comanda("render", "x")
        self.assertTrue(cmd[0].endswith("node.exe"))
        self.assertTrue(cmd[1].endswith("hyperframes.mjs"))
        self.assertEqual(cmd[2:], ["render", "x"])

    def test_fara_node_spune_ce_lipseste(self):
        with mock.patch("shutil.which", return_value=None), self.assertRaises(SystemExit) as e:
            HF.comanda("lint", ".")
        self.assertIn("Node.js", str(e.exception))

    def test_fara_telemetrie(self):
        self.assertEqual(HF.mediu()["HYPERFRAMES_NO_TELEMETRY"], "1")

    def test_snapshot_fara_gemini_si_fara_cadrul_de_final(self):
        a = HF.args_snapshot(Path("p"), [1.0, 2.25], Path("o"))
        self.assertEqual(a[a.index("--describe") + 1], "false")
        self.assertIn("--no-end", a)
        self.assertEqual(a[a.index("--at") + 1], "1.00,2.25")

    def test_argumentele_randarii(self):
        self.assertEqual(HF.args_randare(Path("p"), Path("o.mp4"), 60, "high"),
                         ["render", "p", "--fps", "60", "--quality", "high", "-o", "o.mp4"])

    def test_snapshot_nu_amesteca_cadre_vechi(self):
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            iesire = Path(d) / "planse"
            iesire.mkdir()
            (iesire / "frame-05-at-9.0s.png").write_text("de la compoziția trecută")
            (iesire / "contact-sheet-2.jpg").write_text("tot de atunci")
            gata = subprocess.CompletedProcess([], 0, "", "")
            with mock.patch.object(HF, "ruleaza", return_value=gata):
                self.assertEqual(HF.snapshot(Path("p"), [1.0], iesire), [])
            self.assertFalse((iesire / "contact-sheet-2.jpg").exists())


if __name__ == "__main__":
    unittest.main()
