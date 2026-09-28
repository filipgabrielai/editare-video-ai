import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from instalare import descarca as D  # noqa: E402


class TestAdrese(unittest.TestCase):
    def test_url_model(self):
        self.assertEqual(D.url_model("ggml-tiny.bin"), "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin")

    def test_url_whisper(self):
        self.assertTrue(D.url_whisper().endswith("/v1.9.2/whisper-blas-bin-x64.zip"))


class TestDescarcare(unittest.TestCase):
    def test_marime_corecta(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "a.bin"
            f.write_bytes(b"12345")
            self.assertTrue(D.marime_corecta(f, 5))
            self.assertFalse(D.marime_corecta(f, 6))
            self.assertTrue(D.marime_corecta(f, None))

    def test_descarca_in_cale_cu_spatii(self):
        with tempfile.TemporaryDirectory(prefix="descărcări cu spațiu ") as d:
            sursa = Path(d) / "sursa.bin"
            sursa.write_bytes(b"x" * 3000)
            tinta = Path(d) / "modele noi" / "model.bin"
            D.descarca(sursa.as_uri(), tinta, 3000)
            self.assertTrue(tinta.is_file())
            self.assertFalse(tinta.with_name("model.bin.part").exists())

    def test_descarcarea_incompleta_nu_lasa_nimic(self):
        with tempfile.TemporaryDirectory() as d:
            sursa = Path(d) / "sursa.bin"
            sursa.write_bytes(b"x" * 100)
            tinta = Path(d) / "model.bin"
            with self.assertRaises(SystemExit):
                D.descarca(sursa.as_uri(), tinta, 5000)
            self.assertFalse(tinta.exists())
            self.assertFalse(tinta.with_name("model.bin.part").exists())

    def test_dezarhiveaza_pastreaza_release(self):
        with tempfile.TemporaryDirectory(prefix="unelte ăî ") as d:
            arhiva = Path(d) / "w.zip"
            with zipfile.ZipFile(arhiva, "w") as z:
                z.writestr("Release/whisper-cli.exe", "x")
                z.writestr("Release/whisper-server.exe", "x")
            D.dezarhiveaza(arhiva, Path(d) / "whisper")
            self.assertTrue((Path(d) / "whisper" / "Release" / "whisper-cli.exe").is_file())


if __name__ == "__main__":
    unittest.main()
