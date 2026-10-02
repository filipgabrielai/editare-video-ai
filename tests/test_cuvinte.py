import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from procese.editare import cuvinte  # noqa: E402
from procese.editare import taietura as T  # noqa: E402

WHISPER = {"transcription": [
    {"text": " Mi", "offsets": {"from": 120, "to": 300}},
    {"text": " se", "offsets": {"from": 300, "to": 410}},
    {"text": "[BLANK_AUDIO]", "offsets": {"from": 410, "to": 900}},
    {"text": " pare,", "offsets": {"from": 900, "to": 1180}},
    {"text": " ", "offsets": {"from": 1180, "to": 1200}},
]}


class TestCuvinte(unittest.TestCase):
    def test_cuvinte_din_whisper(self):
        ws = cuvinte.cuvinte_din_whisper(WHISPER)
        self.assertEqual([w["text"] for w in ws], ["Mi", "se", "pare,"])
        self.assertEqual((ws[0]["start"], ws[0]["end"]), (0.12, 0.3))
        self.assertTrue(all(w["type"] == "word" for w in ws))

    def test_dubla_pleaca_de_la_sunet_nu_de_la_segmentul_whisper(self):
        # „Și pe primul loc” (reelul „Top 3”): segmentul Whisper începea cu 0,4 s înainte de voce, peste buze și liniște, iar
        # Whisper a lipit toate cuvintele dublei de începutul fișierului (captions cu 0,3–0,5 s prea devreme)
        rms = [(-20.0 if 1.0 <= k * T.PAS < 2.0 else -80.0) for k in range(int(4 / T.PAS))]
        for k in range(round(0.55 / T.PAS), round(0.63 / T.PAS)):
            rms[k] = -42.0
        self.assertAlmostEqual(cuvinte.decalaj_pe_sunet(rms, T.PRAG, 0.58, 1.98), 0.85, delta=0.01)
        self.assertAlmostEqual(cuvinte.decalaj_pe_sunet(rms, T.PRAG, 1.0, 1.98), 0.85, delta=0.01)
        la_inceput = [(-20.0 if k * T.PAS < 1.0 else -80.0) for k in range(int(4 / T.PAS))]
        self.assertEqual(cuvinte.decalaj_pe_sunet(la_inceput, T.PRAG, 0.05, 0.9), 0.0)

    def test_limba_ajunge_la_whisper(self):
        apeluri = []

        def fals(cmd, **kw):
            if "-oj" in cmd:
                apeluri.append(cmd)
                Path(cmd[cmd.index("-of") + 1] + ".json").write_text(json.dumps({"transcription": []}), encoding="utf-8")
            return subprocess.CompletedProcess(cmd, 0, "", "")
        with tempfile.TemporaryDirectory() as d, mock.patch.object(cuvinte.subprocess, "run", side_effect=fals), \
                mock.patch.object(cuvinte.platforma, "gaseste", return_value="whisper-cli"), \
                mock.patch.object(cuvinte.platforma, "cale_pentru_unealta", side_effect=lambda p, b: str(p)):
            (Path(d) / "lucru").mkdir()
            cuvinte.transcrie_dubla(Path(d), {"dubla": "c_01", "clip": "c", "start": 1.0, "end": 2.0}, "en")
            cuvinte.transcrie_dubla(Path(d), {"dubla": "c_02", "clip": "c", "start": 3.0, "end": 4.0}, "ro", "Claude Code, AI.")
        self.assertEqual(apeluri[0][apeluri[0].index("-l") + 1], "en")
        self.assertNotIn("--prompt", apeluri[0])
        self.assertEqual(apeluri[1][apeluri[1].index("--prompt") + 1], "Claude Code, AI.")


if __name__ == "__main__":
    unittest.main()
