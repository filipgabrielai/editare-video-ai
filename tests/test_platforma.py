import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unelte import platforma  # noqa: E402


class TestPlatforma(unittest.TestCase):
    def test_sistem_mac(self):
        with mock.patch("platform.system", return_value="Darwin"):
            self.assertEqual(platforma.sistem(), "mac")

    def test_sistem_windows_si_exe(self):
        with mock.patch("platform.system", return_value="Windows"):
            self.assertEqual(platforma.sistem(), "windows")
            self.assertEqual(platforma.exe("whisper-cli"), "whisper-cli.exe")

    def test_exe_fara_extensie_pe_mac(self):
        with mock.patch("platform.system", return_value="Darwin"):
            self.assertEqual(platforma.exe("whisper-cli"), "whisper-cli")

    def test_gaseste_prefera_copia_din_repo_chiar_cu_spatii_si_diacritice(self):
        with tempfile.TemporaryDirectory(prefix="cale cu spațiu ăî ") as d:
            local = Path(d) / platforma.exe("whisper-cli")
            local.write_text("x")
            with mock.patch.object(platforma, "UNELTE_WHISPER", Path(d)):
                self.assertEqual(platforma.gaseste("whisper-cli"), str(local))

    def test_gaseste_cade_pe_path(self):
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(platforma, "UNELTE_WHISPER", Path(d)), \
                mock.patch("shutil.which", return_value="/usr/bin/whisper-cli"):
            self.assertEqual(platforma.gaseste("whisper-cli"), "/usr/bin/whisper-cli")

    def test_model_implicit_si_din_variabila(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("EDITARE_MODEL", None)
            self.assertEqual(platforma.model_whisper().name, "ggml-large-v3-turbo.bin")
        with mock.patch.dict(os.environ, {"EDITARE_MODEL": "ggml-tiny.bin"}):
            self.assertEqual(platforma.model_whisper().name, "ggml-tiny.bin")

    def test_marimi_cunoscute(self):
        self.assertEqual(platforma.MARIMI_MODEL["ggml-large-v3-turbo.bin"], 1624555275)
        self.assertEqual(platforma.MARIMI_MODEL["ggml-tiny.bin"], 77691713)

    def test_whisper_complet_cere_ambele_executabile(self):
        # descarca.py și verificarea trebuie să ceară același lucru, altfel o dezarhivare întreruptă dă o buclă fără ieșire
        with tempfile.TemporaryDirectory(prefix="whisper ăî ") as d:
            (Path(d) / platforma.exe("whisper-cli")).write_text("x")
            self.assertFalse(platforma.whisper_complet(Path(d)))
            (Path(d) / platforma.exe("whisper-server")).write_text("x")
            self.assertTrue(platforma.whisper_complet(Path(d)))


if __name__ == "__main__":
    unittest.main()
