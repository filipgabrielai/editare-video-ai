import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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


class TestConsola(unittest.TestCase):
    def test_consola_cp1252_nu_opreste_scriptul(self):
        env = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
        r = subprocess.run([sys.executable, str(RAD / "verificare" / "instalarea.py"), "--fara-disc"],
                           capture_output=True, env=env, timeout=120)
        self.assertIn(r.returncode, (0, 1))
        self.assertNotIn(b"UnicodeEncodeError", r.stderr)


if __name__ == "__main__":
    unittest.main()
