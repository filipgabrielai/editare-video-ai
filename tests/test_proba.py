import sys
import unittest
from pathlib import Path
from unittest import mock

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


class TestComandaRandare(unittest.TestCase):
    def test_randarea_porneste_node_direct_nu_npx_cmd(self):
        # Pe Windows, npx e un .cmd: pornit cu argumente cu spații, cmd.exe taie calea la „C:\\Program” și randarea pică.
        cai = {"node": r"C:\Program Files\nodejs\node.exe", "npx": r"C:\Program Files\nodejs\npx.CMD"}
        with mock.patch("shutil.which", side_effect=lambda n: cai.get(n)):
            cmd = P.comanda_randare(Path("C:/Users/Ion Popescu/proba editare/compozitie"), Path("C:/x/proba.mp4"))
        self.assertTrue(cmd[0].lower().endswith("node.exe"))
        self.assertFalse(cmd[0].lower().endswith((".cmd", ".bat")))
        self.assertTrue(cmd[1].endswith("hyperframes.mjs"))
        self.assertEqual(cmd[2], "render")

    def test_randarea_fara_telemetrie(self):
        # CLAUDE.md promite că nu se trimite nimic nicăieri: telemetria HyperFrames e oprită.
        self.assertEqual(P.mediu_randare().get("HYPERFRAMES_NO_TELEMETRY"), "1")


if __name__ == "__main__":
    unittest.main()
