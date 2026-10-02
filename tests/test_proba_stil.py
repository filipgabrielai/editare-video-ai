import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from procese.editare import proba_stil as P  # noqa: E402
from procese.editare import scenariu as S  # noqa: E402
from unelte import brand  # noqa: E402


class TestProbaStil(unittest.TestCase):
    def test_transcriptul_are_diacriticele_si_incape(self):
        ws = P.transcript_proba()["words"]
        self.assertIn("ș,", [w["text"] for w in ws])
        self.assertLessEqual(ws[-1]["end"], P.DURATA)
        self.assertTrue(all(a["end"] <= b["start"] for a, b in zip(ws, ws[1:])))

    def test_scenariul_e_valid_si_poarta_brandul(self):
        b, _ = brand.combina({"nume": "Ana Pop", "cta": "scrie-mi **CURS** în privat"})
        sc = P.scenariu_proba(b)
        self.assertEqual(S.valideaza(sc)[0], [])
        final = sc["carduri"][-1]
        self.assertTrue(final["brand"])
        self.assertEqual(final["kicker"], "ANA POP")
        self.assertEqual(final["randuri"][0]["text"], "scrie-mi **CURS** în privat")
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "transcript.json"
            f.write_text(json.dumps(P.transcript_proba(), ensure_ascii=False), encoding="utf-8")
            ws = S.cuvinte(f)
        for c in sc["carduri"]:
            if c["ancora"] != "start":
                S.gaseste(ws, c["ancora"])
            for r in c["randuri"]:
                if r.get("ancora"):
                    S.gaseste(ws, r["ancora"])

    def test_fara_brand_textele_implicite(self):
        final = P.scenariu_proba(brand.IMPLICIT)["carduri"][-1]
        self.assertEqual(final["kicker"], "FINAL")
        self.assertIn("urmărește-mă", final["randuri"][0]["text"])


if __name__ == "__main__":
    unittest.main()
