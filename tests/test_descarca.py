import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

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


class TestErori(unittest.TestCase):
    # Omul vede o propoziție în română, nu un traceback, și nu rămân fișiere stricate.
    def test_sursa_indisponibila_da_mesaj(self):
        with tempfile.TemporaryDirectory() as d:
            tinta = Path(d) / "model.bin"
            with self.assertRaises(SystemExit) as e:
                D.descarca((Path(d) / "nu-exista.bin").as_uri(), tinta, 10)
            self.assertIn("internetul", str(e.exception))
            self.assertFalse(tinta.exists())
            self.assertFalse(tinta.with_name("model.bin.part").exists())

    def test_conexiunea_cade_la_jumatate(self):
        class Raspuns:
            headers = {"Content-Length": "100"}

            def __init__(self):
                self.n = 0

            def read(self, _):
                self.n += 1
                if self.n == 1:
                    return b"x" * 50
                raise ConnectionResetError("conexiunea a căzut")

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        with tempfile.TemporaryDirectory() as d, mock.patch("urllib.request.urlopen", return_value=Raspuns()):
            tinta = Path(d) / "model.bin"
            with self.assertRaises(SystemExit) as e:
                D.descarca("https://exemplu.ro/model.bin", tinta, 100)
            self.assertIn("internetul", str(e.exception))
            self.assertFalse(tinta.with_name("model.bin.part").exists())

    def test_arhiva_stricata_da_mesaj_si_e_stearsa(self):
        with tempfile.TemporaryDirectory() as d:
            arhiva = Path(d) / "w.zip"
            arhiva.write_text("<html>pagina de login a rețelei</html>")
            with self.assertRaises(SystemExit) as e:
                D.dezarhiveaza(arhiva, Path(d) / "whisper")
            self.assertIn("încearcă din nou", str(e.exception).lower())
            self.assertFalse(arhiva.exists())


if __name__ == "__main__":
    unittest.main()


class TestDemo(unittest.TestCase):
    def test_demo_se_dezarhiveaza_in_exemple(self):
        with tempfile.TemporaryDirectory(prefix="demo ăî ") as d:
            arhiva = Path(d) / "demo.zip"
            with zipfile.ZipFile(arhiva, "w") as z:
                z.writestr("clipuri/top-3-unelte-ai.mp4", "x")
            with mock.patch.object(D, "URL_DEMO", arhiva.as_uri()), mock.patch.object(D, "EXEMPLE", Path(d) / "exemple"):
                tinta = D.demo()
            self.assertTrue((tinta / "clipuri" / "top-3-unelte-ai.mp4").is_file())
            self.assertFalse((tinta / "demo-reel-v1.zip").exists())   # arhiva nu rămâne în urmă

    def test_demo_deja_descarcat_nu_se_mai_descarca(self):
        with tempfile.TemporaryDirectory() as d:
            clipuri = Path(d) / "exemple" / "demo-reel" / "clipuri"
            clipuri.mkdir(parents=True)
            (clipuri / "top-3-unelte-ai.mp4").write_text("x")
            with mock.patch.object(D, "EXEMPLE", Path(d) / "exemple"), mock.patch.object(D, "descarca") as dl:
                D.demo()
            dl.assert_not_called()
