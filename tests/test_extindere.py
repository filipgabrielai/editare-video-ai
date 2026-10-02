import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAD))
import piese  # noqa: E402
from procese.editare import compozitie as C  # noqa: E402
from procese.editare import scenariu as S  # noqa: E402
from unelte import brand  # noqa: E402
from verificare import ordine  # noqa: E402

DATE = RAD / "tests" / "date" / "reel"
PIESA_MEA = '''from piese.comun import Fragment


def construieste(ctx, m):
    mid = f"m-{m['id']}"
    t = ctx.ancora(m["ancora"])
    return Fragment(html=[f'<div class="piesa sageata" id="{mid}"><i id="{mid}-varf"></i></div>'],
                    css=[".sageata{position:absolute;left:100px;top:900px;opacity:0}"],
                    js=[f'tl.fromTo("#{mid}", {{autoAlpha:0}}, {{autoAlpha:1, duration:0.2}}, {t:.3f});'],
                    intervale=[{"id": m["id"], "intra": t, "iese": t + 1, "el": mid}])
'''
PIESA_RAU = '''from piese.comun import Fragment


def construieste(ctx, m):
    return Fragment(html=['<div id="titlu">peste titlul kitului</div>'])
'''


class TestExtindere(unittest.TestCase):
    def setUp(self):
        self.sc = json.loads((DATE / "scenariu.json").read_text(encoding="utf-8"))
        self.ws = S.corecteaza(S.cuvinte(DATE / "transcript.json"), self.sc["corecturi"])
        self.dir = tempfile.TemporaryDirectory()
        self.ale = Path(self.dir.name)
        self.addCleanup(self.dir.cleanup)
        p = mock.patch.object(piese, "ALE_MELE", self.ale)
        p.start()
        self.addCleanup(p.stop)

    def plan(self, momente):
        return C.planifica({**self.sc, "momente": momente}, self.ws, [2.8], 6.0, S.stil("studio"))

    def test_piesa_omului_intra_in_compozitie(self):
        (self.ale / "sageata.py").write_text(PIESA_MEA, encoding="utf-8")
        plan = self.plan([{"piesa": "sageata", "id": "s1", "ancora": "cât de productiv"}])
        self.assertIn('<div class="piesa sageata" id="m-s1">', "".join(plan["html"]))
        self.assertTrue(any('"#m-s1"' in x for x in plan["js"]))
        self.assertEqual(plan["css"], [".sageata{position:absolute;left:100px;top:900px;opacity:0}"])
        self.assertIn({"id": "s1", "el": "m-s1"}, [{"id": i["id"], "el": i.get("el")} for i in plan["intervale"]])
        p = C.pagina(self.sc, plan, [], [], 6.0)
        self.assertIn("<style>\n.sageata{position:absolute", p)
        self.assertLess(p.index('href="assets/brand.css"'), p.index("<style>"))   # piesele vin după stil și brand

    def test_fara_momente_pagina_ramane_cea_dinainte(self):
        plan = C.planifica(self.sc, self.ws, [2.8], 6.0, S.stil("studio"))
        self.assertEqual(plan["css"], [])
        self.assertNotIn("<style>", C.pagina(self.sc, plan, [], [], 6.0))

    def test_piesa_care_calca_id_urile_kitului_e_oprita(self):
        # o piesă care își numește elementul „titlu” ar fi animată de tween-urile kitului; fiecare piesă stă sub m-<id>
        (self.ale / "rau.py").write_text(PIESA_RAU, encoding="utf-8")
        with self.assertRaises(SystemExit) as e:
            self.plan([{"piesa": "rau", "id": "x"}])
        self.assertIn("m-x", str(e.exception))
        self.assertIn("rau", str(e.exception))

    def test_piesa_care_lipseste_spune_unde_se_scrie(self):
        erori, _ = S.valideaza({**self.sc, "momente": [{"piesa": "confetti", "id": "c1"}]})
        self.assertEqual(len(erori), 1)
        self.assertIn("confetti", erori[0])
        self.assertIn("piese/ale-mele/confetti.py", erori[0])
        self.assertIn("docs/EXTINDERE.md", erori[0])

    def test_momentele_au_id_si_nu_se_repeta(self):
        m = [{"piesa": "cuvant", "text": "a", "ancora": "start"}, {"piesa": "cuvant", "id": "w", "text": "a", "ancora": "x"},
             {"piesa": "cuvant", "id": "w", "text": "b", "ancora": "y"}, {"piesa": "Cuvânt Mare", "id": "z"}]
        erori, _ = S.valideaza({**self.sc, "momente": m})
        self.assertTrue(any("nu are id" in e for e in erori))
        self.assertTrue(any("„w” apare de două ori" in e for e in erori))
        self.assertTrue(any("Cuvânt Mare" in e for e in erori))

    def test_piesa_omului_bate_piesa_kitului_cu_acelasi_nume(self):
        # „copiaz-o în piese/ale-mele/ și schimb-o”: varianta lui e cea folosită
        (self.ale / "cuvant.py").write_text(PIESA_MEA, encoding="utf-8")
        plan = self.plan([{"piesa": "cuvant", "id": "w", "ancora": "cât de productiv"}])
        self.assertIn("sageata", "".join(plan["html"]))

    def test_cuvantul_din_kit(self):
        plan = self.plan([{"piesa": "cuvant", "id": "suta", "text": "100% <b>", "ancora": "cât de productiv", "durata": 1.5}])
        html = "".join(plan["html"])
        self.assertIn('class="piesa cuvant" id="m-suta"', html)
        self.assertIn("100% &lt;b&gt;", html)
        iv = next(i for i in plan["intervale"] if i["id"] == "suta")
        self.assertAlmostEqual(iv["iese"] - iv["intra"], 1.5, places=2)
        self.assertEqual(C.pozitii_negative(plan["js"]), [])
        self.assertTrue(any(n == "pop" for _, n, _, _ in plan["sfx"]))

    def test_cuvantul_fara_text_spune_ce_lipseste(self):
        with self.assertRaises(SystemExit) as e:
            self.plan([{"piesa": "cuvant", "id": "w", "ancora": "cât de productiv"}])
        self.assertIn("text", str(e.exception))

    def test_cuvantul_pe_orizontala_sta_pe_partea_opusa_cardului(self):
        sc = {"stil": "studio", "format": "16:9", "cadru": {"carduri": "dreapta"},
              "carduri": [{"id": "a", "ancora": "start", "kicker": "A", "randuri": [{"text": "unu"}]}],
              "momente": [{"piesa": "cuvant", "id": "w", "text": "AI", "ancora": "cât de productiv"}]}
        html = "".join(C.planifica(sc, self.ws, [], 6.0, S.stil("studio"), fmt="16:9")["html"])
        self.assertIn("left:480px", html)     # cardul e în dreapta: cuvântul în stânga

    def test_stilul_omului_vine_dupa_brand(self):
        with tempfile.TemporaryDirectory() as b, tempfile.TemporaryDirectory() as d, mock.patch.object(brand, "BRAND", Path(b)):
            plan = C.planifica(self.sc, self.ws, [], 6.0, S.stil("studio"))
            C.pregateste_assets(Path(d), "studio")
            self.assertFalse((Path(d) / "assets" / "stil-meu.css").exists())
            self.assertNotIn("stil-meu.css", C.pagina(self.sc, plan, [], [], 6.0, stil_meu=C.stil_meu()))
            (Path(b) / "stil.css").write_text(".card{border-radius:8px}", encoding="utf-8")
            C.pregateste_assets(Path(d), "studio")
            self.assertEqual((Path(d) / "assets" / "stil-meu.css").read_text(encoding="utf-8"), ".card{border-radius:8px}")
            p = C.pagina(self.sc, plan, [], [], 6.0, stil_meu=C.stil_meu())
            self.assertLess(p.index('href="assets/brand.css"'), p.index('href="assets/stil-meu.css"'))

    def test_piesele_omului_se_vad_in_tabelul_de_vizibilitate(self):
        rez = {"ndif": 0, "dif": [], "viz": {"m-s1": [[2.0, 9.0]]}}
        p = ordine.probleme(rez, [{"id": "s1", "intra": 2.0, "iese": 3.0, "el": "m-s1"}])
        self.assertEqual(len(p), 1)
        self.assertIn("„s1”", p[0])
        self.assertIn(".piesa", ordine.SELECTOR)


if __name__ == "__main__":
    unittest.main()
