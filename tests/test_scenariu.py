import copy
import json
import sys
import unittest
from pathlib import Path

RAD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAD))
from procese.editare import scenariu as S  # noqa: E402

DATE = RAD / "tests" / "date" / "reel"
SC = json.loads((DATE / "scenariu.json").read_text(encoding="utf-8"))


class TestScenariu(unittest.TestCase):
    def test_norm_fara_diacritice_si_cratima(self):
        self.assertEqual(S.norm("Stânga, Code-ul!"), ["stanga", "code", "ul"])

    def test_ancora_gasita_cand_whisper_lipeste_cuvintele_cu_punct(self):
        # demo-ul pe copia 1080p: Whisper a scris „Locul 3.Bolt.new” și ancora „locul 3” nu se mai găsea
        ws = [{"text": t, "start": k, "end": k + 0.5, "n": S.norm(t)} for k, t in enumerate(["Locul", "3.Bolt.new", "Construiește"])]
        self.assertEqual(S.gaseste(ws, "locul 3"), (0, 1.5))
        self.assertEqual(S.gaseste(ws, "bolt.new"), (1, 1.5))
        self.assertEqual(S.norm("Opus 5.5"), S.norm("Opus 5,5"))   # punctul dintre cifre rămâne lipit

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

    def test_corectura_pastreaza_articolul_cu_cratima(self):
        ws = [{"text": t, "start": k, "end": k + 0.5, "n": S.norm(t)} for k, t in enumerate(["am", "Cloud", "Code-ul,", "care"])]
        texte = [w["text"] for w in S.corecteaza(ws, {"cloud code": "Claude Code"})]
        self.assertEqual(texte, ["am", "Claude Code-ul,", "", "care"])

    def test_corectura_peste_granita_de_cuvinte(self):
        # Whisper aude „unelte AI” ca „un LTE-AI”: greșeala nu se potrivește cuvânt cu cuvânt
        ws = [{"text": t, "start": k, "end": k + 0.5, "n": S.norm(t)} for k, t in enumerate(["Top", "3", "un", "LTE-AI", "pentru", "CloudCo."])]
        texte = [w["text"] for w in S.corecteaza(ws, {"un lte ai": "unelte AI", "cloudco": "Claude Code"})]
        self.assertEqual(texte, ["Top", "3", "unelte AI", "", "pentru", "Claude Code."])

    def test_brand_e_true_sau_false(self):
        sc = copy.deepcopy(SC)
        sc["carduri"][0]["brand"] = "da"
        erori, _ = S.valideaza(sc)
        self.assertTrue(any("brand" in e for e in erori))
        sc["carduri"][0]["brand"] = True
        self.assertEqual(S.valideaza(sc)[0], [])

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
