import json
import sys
import unittest
from pathlib import Path

RAD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAD))
from procese.editare import scenariu as S  # noqa: E402
from unelte import formate  # noqa: E402


class TestRetete(unittest.TestCase):
    def test_fiecare_reteta_e_un_scenariu_valid_si_e_in_lista(self):
        lista = (RAD / "retete" / "README.md").read_text(encoding="utf-8")
        retete = sorted(p.parent.name for p in (RAD / "retete").glob("*/scenariu.json"))
        self.assertEqual(retete, ["orizontal-simplu", "reel-clasic"])
        for nume in retete:
            sc = json.loads((RAD / "retete" / nume / "scenariu.json").read_text(encoding="utf-8"))
            fmt = sc.get("format", formate.IMPLICIT)
            self.assertEqual(S.valideaza(sc, fmt), ([], []), nume)
            self.assertIn(f"`{nume}`", lista)


if __name__ == "__main__":
    unittest.main()
