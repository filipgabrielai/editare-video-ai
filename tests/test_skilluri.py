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


if __name__ == "__main__":
    unittest.main()
