import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from procese.reel import cuvinte  # noqa: E402

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


if __name__ == "__main__":
    unittest.main()
