import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAD))
from verificare import instalarea as I  # noqa: E402

GB = 1024 ** 3


class TestVersiuni(unittest.TestCase):
    def test_versiune(self):
        self.assertEqual(I.versiune("v22.11.0"), (22, 11, 0))
        self.assertEqual(I.versiune("Python 3.12.1"), (3, 12, 1))
        self.assertIsNone(I.versiune("nimic aici"))

    def test_cel_putin(self):
        self.assertTrue(I.cel_putin((22, 3, 1), (22,)))
        self.assertFalse(I.cel_putin((20, 11, 0), (22,)))
        self.assertFalse(I.cel_putin(None, (22,)))

    def test_python_vechi_cere_reparatie(self):
        v = I.verifica_python((3, 9, 6))
        self.assertFalse(v.ok)
        self.assertIn("3.10", v.detaliu)
        self.assertTrue(v.repara)


class TestFfmpeg(unittest.TestCase):
    COMPLET = " V....D libx264              libx264 H.264 / AVC\n A....D aac                  AAC (Advanced Audio Coding)\n"

    def test_encodere_complete(self):
        self.assertEqual(I.encodere_lipsa(self.COMPLET), [])

    def test_build_minimal_fara_libx264(self):
        self.assertEqual(I.encodere_lipsa(" A....D aac  AAC\n A....D libfdk_aac  Fraunhofer\n"), ["libx264"])


class TestModel(unittest.TestCase):
    def test_model_lipsa(self):
        v = I.verifica_model(Path(tempfile.gettempdir()) / "nu-exista" / "ggml-tiny.bin")
        self.assertFalse(v.ok)
        self.assertIn("lipsește", v.detaliu)

    def test_model_incomplet_dupa_o_descarcare_intrerupta(self):
        with tempfile.TemporaryDirectory(prefix="modele ăî ") as d:
            cale = Path(d) / "ggml-tiny.bin"
            cale.write_bytes(b"0" * 10)
            v = I.verifica_model(cale)
            self.assertFalse(v.ok)
            self.assertIn("incomplet", v.detaliu)

    def test_model_necunoscut_e_acceptat(self):
        with tempfile.TemporaryDirectory() as d:
            cale = Path(d) / "ggml-alt-model.bin"
            cale.write_bytes(b"0" * 10)
            self.assertTrue(I.verifica_model(cale).ok)


class TestDiscSiReparatii(unittest.TestCase):
    def test_disc(self):
        self.assertFalse(I.verifica_disc(5 * GB).ok)
        self.assertTrue(I.verifica_disc(20 * GB).ok)

    def test_winget_spune_sa_redeschida(self):
        self.assertIn("redeschide", I.repara("node", "windows"))
        self.assertNotIn("redeschide", I.repara("node", "mac"))

    def test_comanda_python_pe_fiecare_sistem(self):
        self.assertTrue(I.repara("model", "windows").startswith("python "))
        self.assertTrue(I.repara("model", "mac").startswith("python3 "))


class TestHomebrew(unittest.TestCase):
    # Installerul Homebrew cere parola de sudo și un terminal real: din Claude Code nu poate rula, îl rulează omul în Terminal.
    def test_homebrew_se_instaleaza_din_terminal(self):
        r = I.repara("homebrew", "mac")
        self.assertIn("Terminal", r)
        self.assertIn("redeschide", r)

    def test_homebrew_instalat_dar_nevazut_in_path(self):
        with tempfile.TemporaryDirectory() as d:
            brew = Path(d) / "brew"
            brew.write_text("x")
            with mock.patch.object(I.platforma, "sistem", return_value="mac"), mock.patch("shutil.which", return_value=None):
                v = I.verifica_homebrew(cai=(brew,))
        self.assertFalse(v.ok)
        self.assertIn("shellenv", v.repara)
        self.assertIn(str(brew), v.repara)

    def test_homebrew_lipsa_cu_totul(self):
        with mock.patch.object(I.platforma, "sistem", return_value="mac"), mock.patch("shutil.which", return_value=None):
            v = I.verifica_homebrew(cai=(Path("/nu/exista/brew"),))
        self.assertFalse(v.ok)
        self.assertIn("Terminal", v.repara)


class TestWhisperPorneste(unittest.TestCase):
    # whisper-cli.exe poate exista și totuși să nu pornească (lipsesc bibliotecile Microsoft, antivirus): verificarea îl pornește.
    def test_whisper_care_nu_porneste(self):
        with mock.patch.object(I.platforma, "gaseste", return_value="C:/unelte/whisper-cli.exe"), \
                mock.patch.object(I.platforma, "sistem", return_value="windows"):
            v = I.verifica_whisper(ruleaza_cod=lambda args: (3221225781, "The code execution cannot proceed because VCRUNTIME140.dll was not found."))
        self.assertFalse(v.ok)
        self.assertIn("nu pornește", v.detaliu)
        self.assertIn("VCRedist", v.repara)

    def test_whisper_care_porneste(self):
        with mock.patch.object(I.platforma, "gaseste", return_value="/opt/homebrew/bin/whisper-cli"):
            v = I.verifica_whisper(ruleaza_cod=lambda args: (0, "usage: whisper-cli [options] file0 file1 ..."))
        self.assertTrue(v.ok)


class TestConsola(unittest.TestCase):
    def test_consola_cp1252_nu_opreste_scriptul(self):
        env = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
        r = subprocess.run([sys.executable, str(RAD / "verificare" / "instalarea.py"), "--fara-disc"],
                           capture_output=True, env=env, timeout=120)
        self.assertIn(r.returncode, (0, 1))
        self.assertNotIn(b"UnicodeEncodeError", r.stderr)


if __name__ == "__main__":
    unittest.main()
