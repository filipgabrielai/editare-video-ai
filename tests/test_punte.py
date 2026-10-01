import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unelte import punte  # noqa: E402


class TestPunte(unittest.TestCase):
    def test_destinatia_in_skill_urile_personale(self):
        d = punte.destinatie(Path("/acasa/Ștefan Pop"))
        self.assertEqual(d.parts[-4:], (".claude", "skills", "editare-video-ai", "SKILL.md"))

    def test_textul_are_calea_exacta_si_frontmatter(self):
        kit = Path("C:/Users/Ștefan Pop/Documente/editare-video-ai")
        t = punte.text_skill(kit)
        self.assertTrue(t.startswith("---\nname: editare-video-ai\ndescription: "))
        self.assertIn(f"`{kit}`", t)
        self.assertIn(punte.MARCAJ, t)

    def test_scrie_actualizeaza_si_sterge(self):
        with tempfile.TemporaryDirectory(prefix="acasă ș ") as d:
            dest = punte.destinatie(Path(d))
            self.assertEqual(punte.instaleaza(Path(d) / "kit", dest), "scris")
            self.assertEqual(punte.instaleaza(Path(d) / "kit nou", dest), "actualizat")
            self.assertIn("kit nou", dest.read_text(encoding="utf-8"))
            self.assertTrue(punte.sterge(dest))
            self.assertFalse(dest.exists())
            self.assertFalse(punte.sterge(dest))

    def test_nu_suprascrie_un_skill_strain(self):
        with tempfile.TemporaryDirectory() as d:
            dest = punte.destinatie(Path(d))
            dest.parent.mkdir(parents=True)
            dest.write_text("---\nname: editare-video-ai\ndescription: al meu\n---\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                punte.instaleaza(Path(d) / "kit", dest)
            with self.assertRaises(SystemExit):
                punte.sterge(dest)
            self.assertIn("al meu", dest.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
