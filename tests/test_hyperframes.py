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

    def test_intrarea_e_inchisa_si_encodarea_are_timp(self):
        # lint și snapshot rămâneau agățate cu intrarea deschisă; encodarea cădea la limita de 600 s cu calculatorul încărcat
        with mock.patch.object(HF.subprocess, "run") as run, mock.patch("shutil.which", return_value="node"):
            HF.ruleaza(["lint", "x"], capteaza=True)
            HF.ruleaza(["render", "x"])
        for apel in run.call_args_list:
            self.assertIs(apel.kwargs["stdin"], HF.subprocess.DEVNULL)
        self.assertEqual(HF.mediu()["FFMPEG_ENCODE_TIMEOUT_MS"], "3600000")
        with mock.patch.dict(HF.os.environ, {"FFMPEG_ENCODE_TIMEOUT_MS": "99"}):
            self.assertEqual(HF.mediu()["FFMPEG_ENCODE_TIMEOUT_MS"], "99")   # ce a pus omul rămâne

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
