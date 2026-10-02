import re
import sys
import unittest
from pathlib import Path

RAD = Path(__file__).resolve().parents[1]
USI = ("instalare", "personalizare", "editeaza", "editeaza-reel", "leaga-de-sistem")


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

    def test_kitul_nu_mai_e_doar_de_reeluri(self):
        readme = (RAD / "README.md").read_text(encoding="utf-8")
        self.assertIn("`/editeaza`", readme)
        self.assertIn("16:9", readme)
        self.assertNotIn("Kitul meu de editare de reeluri", readme)
        usa = (RAD / ".claude" / "skills" / "editeaza" / "SKILL.md").read_text(encoding="utf-8")
        for x in ("--filmare 16:9", "retete/README.md", "docs/PROCES.md", "docs/PIESE.md", "Planul pe momente"):
            self.assertIn(x, usa)

    def test_ce_nu_e_inca_in_kit_se_spune(self):
        # cine vine din ghid nu trebuie să aștepte un efect și să primească altceva
        piese = (RAD / "docs" / "PIESE.md").read_text(encoding="utf-8")
        for x in ("text în spatele", "ecran împărțit", "obiect în palmă", "nu e încă în kit"):
            self.assertIn(x, piese)
        self.assertIn("nu e încă în kit", (RAD / ".claude" / "skills" / "editeaza" / "SKILL.md").read_text(encoding="utf-8"))
        self.assertIn("docs/PIESE.md", (RAD / "README.md").read_text(encoding="utf-8"))

    def test_lectiile_de_taietura_sunt_in_pasii_de_reel(self):
        reel = (RAD / ".claude" / "skills" / "editeaza-reel" / "SKILL.md").read_text(encoding="utf-8")
        for x in ("false_starturi.py", '"strans": false', "<dubla>@<timp>", "pot scoate", "procese/editare/", "duble.json"):
            self.assertIn(x, reel)
        ghid = (RAD / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("Fără cozi de liniște pentru animații", ghid)
        self.assertIn("docs/PIESE.md", ghid)

    def test_procesul_are_cele_cinci_faze(self):
        proces = (RAD / "docs" / "PROCES.md").read_text(encoding="utf-8")
        for faza in ("## 1. Filmezi", "## 2. Ascultă", "## 3. Se uită", "## 4. Construiește", "## 5. Te uiți și dai note"):
            self.assertIn(faza, proces)

    def test_scenariul_spune_de_format(self):
        sc = (RAD / "docs" / "SCENARIU.md").read_text(encoding="utf-8")
        for x in ('`format`', "--filmare", '„stanga”'):
            self.assertIn(x, sc)


if __name__ == "__main__":
    unittest.main()
