import copy
import json
import sys
import unittest
from pathlib import Path

RAD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAD))
from procese.reel import scenariu as S  # noqa: E402

DATE = RAD / "tests" / "date" / "reel"
SC = json.loads((DATE / "scenariu.json").read_text(encoding="utf-8"))


class TestScenariu(unittest.TestCase):
    def test_norm_fara_diacritice_si_cratima(self):
        self.assertEqual(S.norm("Stânga, Code-ul!"), ["stanga", "code", "ul"])

    def test_markup_scapa_html_si_face_bold(self):
        self.assertEqual(S.markup("cu **AI** <b>"), "cu <b>AI</b> &lt;b&gt;")

    def test_gaseste_ancora_scrisa_altfel(self):
        ws = S.cuvinte(DATE / "transcript.json")
        self.assertEqual(S.gaseste(ws, "aici in STANGA")[0], 3.0)

    def test_ancora_lipsa_arata_ce_urmeaza(self):
        ws = S.cuvinte(DATE / "transcript.json")
        with self.assertRaises(SystemExit) as e:
            S.gaseste(ws, "YouTube", 3.0)
        self.assertIn("Aici", str(e.exception))

    def test_corecturi_pe_doua_cuvinte(self):
        ws = S.corecteaza(S.cuvinte(DATE / "transcript.json"), {"cloud code": "Claude Code"})
        texte = [w["text"] for w in ws]
        self.assertIn("Claude Code", texte)
        self.assertEqual(texte[texte.index("Claude Code") + 1], "")
        self.assertEqual(S.gaseste(ws, "Cloud Code")[0], 3.9)   # ancorele rămân pe transcript

    def test_scenariul_bun_trece(self):
        self.assertEqual(S.valideaza(SC)[0], [])

    def test_zona_sigura_si_greselile_comune(self):
        rau = copy.deepcopy(SC)
        rau["cadru"]["carduri_y"] = 200
        rau["cadru"]["captions_y"] = 1600
        rau["carduri"][0]["randuri"][0]["icoana"] = "nu-exista"
        rau["carduri"][1]["id"] = "hook"
        rau["carduri"][0]["randuri"] *= 3
        erori = " | ".join(S.valideaza(rau)[0])
        for bucata in ("carduri_y", "captions_y", "nu-exista", "hook", "4 rânduri"):
            self.assertIn(bucata, erori)


if __name__ == "__main__":
    unittest.main()
