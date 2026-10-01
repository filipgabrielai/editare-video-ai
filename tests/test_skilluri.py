import re
import sys
import unittest
from pathlib import Path

RAD = Path(__file__).resolve().parents[1]
USI = ("instalare", "personalizare", "editeaza-reel", "leaga-de-sistem")


class TestSkilluri(unittest.TestCase):
    def test_fiecare_skill_are_nume_si_descriere(self):
        for d in sorted((RAD / ".claude" / "skills").iterdir()):
            text = (d / "SKILL.md").read_text(encoding="utf-8")
            m = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", text)
            self.assertIsNotNone(m, d.name)
            self.assertEqual(m.group(1).strip(), d.name)

    def test_usile_sunt_in_ghid(self):
        ghid = (RAD / "CLAUDE.md").read_text(encoding="utf-8")
        for u in USI:
            self.assertTrue((RAD / ".claude" / "skills" / u / "SKILL.md").is_file(), u)
            self.assertIn(f"`/{u}`", ghid)

    def test_kitul_se_poate_lua_doar_cu_linkul(self):
        # Filip: „să pot să îl iau ca link și să îi zic la Claude Code: clonează acest repository”
        readme = (RAD / "README.md").read_text(encoding="utf-8")
        self.assertIn("Clonează https://github.com/filipgabrielai/editare-video-ai", readme)
        self.assertIn("citește CLAUDE.md din el", readme)
        ghid = (RAD / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("din folderul kitului", ghid)      # sesiunea poate fi deschisă în alt folder decât kitul
        self.assertIn("`/leaga-de-sistem`", ghid)

    def test_omul_afla_cum_da_feedback_si_ce_e_vocabularul(self):
        readme = (RAD / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Cum îi dai feedback", readme)
        self.assertIn("`vocabular`", (RAD / "docs" / "PERSONALIZARE.md").read_text(encoding="utf-8"))
        self.assertIn("--vocabular", (RAD / ".claude" / "skills" / "editeaza-reel" / "SKILL.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
