import shutil
import sys
import tempfile
import unittest
from pathlib import Path

RAD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAD))
from verificare import ordine  # noqa: E402

PAGINA = """<!doctype html><html><head><meta charset="utf-8"><script src="gsap.min.js"></script></head><body>
<div id="reel" data-composition-id="reel" data-width="400" data-height="300">
<div id="a" class="card" style="position:absolute;width:50px;height:50px;background:red"></div></div>
<script>window.__timelines={};(function(){const tl=gsap.timeline({paused:true});
%s
tl.set({}, {}, 4);window.__timelines["reel"]=tl;})();</script></body></html>"""
GRESIT = 'tl.to("#a", {x:100, duration:0.5, yoyo:true, repeat:5}, 0);\ntl.to("#a", {x:300, duration:0.5, overwrite:"auto"}, 2);'
CORECT = 'tl.fromTo("#a", {x:0}, {x:100, duration:0.5}, 0);\ntl.fromTo("#a", {x:100}, {x:300, duration:0.5, immediateRender:false}, 2);'


class TestProbleme(unittest.TestCase):
    def test_diferentele_de_ordine_sunt_probleme(self):
        rez = {"ndif": 2, "dif": [[0.35, "c-a", "100|none", "0|none"]], "viz": {}}
        p = ordine.probleme(rez, [])
        self.assertEqual(len(p), 1)
        self.assertIn("c-a", p[0])

    def test_cardul_care_ramane_pe_ecran_peste_intervalul_lui(self):
        # o ancoră scurtă a prins alt cuvânt („Acolo” a prins „ține-l acolo”) și elementul a rămas pe ecran până la final
        rez = {"ndif": 0, "dif": [], "viz": {"c-a": [[0.1, 9.0]], "c-b": [[4.0, 9.0]]}}
        iv = [{"id": "a", "intra": 0.05, "iese": 3.9}, {"id": "b", "intra": 3.98, "iese": 9.0}]
        p = ordine.probleme(rez, iv)
        self.assertEqual(len(p), 1)
        self.assertIn("„a”", p[0])
        bine = {"ndif": 0, "dif": [], "viz": {"c-a": [[0.1, 4.1]], "c-b": [[4.0, 9.0]]}}
        self.assertEqual(ordine.probleme(bine, iv), [])

    def test_cardul_care_nu_apare_deloc(self):
        rez = {"ndif": 0, "dif": [], "viz": {"c-a": []}}
        self.assertIn("nu apare", ordine.probleme(rez, [{"id": "a", "intra": 0.05, "iese": 3.9}])[0])

    def test_raportul_spune_trece_sau_nu(self):
        bine = {"n": 3, "momente": 5, "ndif": 0, "dif": [], "viz": {"c-a": [[0.1, 4.1]]}}
        self.assertTrue(ordine.raport(bine, [{"id": "a", "intra": 0.05, "iese": 3.9}]).endswith("TRECE"))
        rau = {"n": 3, "momente": 5, "ndif": 1, "dif": [[0.35, "c-a", "100|none", "0|none"]], "viz": {}}
        self.assertIn("NU TRECE", ordine.raport(rau, []))


@unittest.skipUnless(shutil.which("node") and (RAD / "node_modules" / "puppeteer-core").is_dir() and ordine.browser(),
                     "lipsesc node, pachetele sau browserul de randare")
class TestInBrowser(unittest.TestCase):
    def masoara(self, js):
        with tempfile.TemporaryDirectory() as d:
            shutil.copy(RAD / "node_modules" / "gsap" / "dist" / "gsap.min.js", Path(d) / "gsap.min.js")
            (Path(d) / "index.html").write_text(PAGINA % js, encoding="utf-8")
            return ordine.masoara(Path(d) / "index.html")

    def test_prinde_tweenul_care_depinde_de_ordine(self):
        self.assertGreater(self.masoara(GRESIT)["ndif"], 0)

    def test_pagina_corecta_trece(self):
        rez = self.masoara(CORECT)
        self.assertEqual(rez["ndif"], 0)
        self.assertEqual(rez["momente"], 5)
        self.assertIn("a", rez["viz"])


if __name__ == "__main__":
    unittest.main()
