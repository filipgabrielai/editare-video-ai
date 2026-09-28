import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAD))
from procese.reel import compozitie as C  # noqa: E402
from procese.reel import scenariu as S  # noqa: E402

DATE = RAD / "tests" / "date" / "reel"


class TestCompozitie(unittest.TestCase):
    def setUp(self):
        self.sc = json.loads((DATE / "scenariu.json").read_text(encoding="utf-8"))
        self.ws = S.corecteaza(S.cuvinte(DATE / "transcript.json"), self.sc["corecturi"])

    def test_sunetele_nu_se_repeta_si_nu_se_calca(self):
        s = C.Sunete()
        for t in (0.1, 1.0, 1.0, 2.0, 3.0):
            s.adauga("card", t)
        nume = [x[1] for x in s.lista]
        self.assertEqual(len(nume), 4)
        self.assertTrue(all(a != b for a, b in zip(nume, nume[1:])))

    def test_grupuri(self):
        gr = C.grupuri(self.ws, [2.8])
        self.assertTrue(all(len(g) <= 3 or g[-1]["end"] - g[0]["start"] < 0.35 for g in gr))
        self.assertTrue(any(g[-1]["text"] == "fi." for g in gr))   # punctuația închide grupul
        self.assertFalse(any(g[0]["start"] < 2.8 < g[-1]["start"] for g in gr))   # nici un grup peste tăietură

    def test_planul_cardurilor(self):
        p = C.planifica(self.sc, self.ws, [2.8], 6.0, S.stil("studio"))
        iv = {x["id"]: x for x in p["intervale"]}
        self.assertEqual(iv["hook"]["intra"], 0.05)
        self.assertAlmostEqual(iv["hook"]["iese"], iv["stanga"]["intra"] - 0.08, places=3)
        self.assertAlmostEqual(iv["stanga"]["intra"], 3.0 - 0.05, places=3)
        self.assertEqual(iv["stanga"]["iese"], 6.0)
        js = "\n".join(p["js"])
        self.assertIn('"#c-hook-r1"', js)                  # rândul 2 intră pe ancoră
        self.assertNotIn('"#c-hook-r0", {height', js)       # primul rând e static
        self.assertIn('tl.set("#stage", {scale:1.06}, 2.7990);', js)   # zoom pe grila de cadre

    def test_cardul_compact_nu_intra_sub_titlu(self):
        plan = C.planifica(self.sc, self.ws, [], 6.0, S.stil("studio"))
        self.assertIn("--compact-y:340px", C.pagina(self.sc, plan, [], [], 6.0))
        fara_titlu = {k: v for k, v in self.sc.items() if k != "titlu"}
        self.assertIn("--compact-y:262px", C.pagina(fara_titlu, plan, [], [], 6.0))
        css = (RAD / "stiluri" / "studio" / "reel.css").read_text(encoding="utf-8")
        self.assertIn(".card.compact{top:var(--compact-y)", css)

    def test_culoarea_cuvintelor_nu_se_calca(self):
        # două cuvinte rostite la 10 ms unul după altul: tween-ul următor preia culoarea, nu se suprapune cu primul
        ws = [{"text": "Mi", "start": 0.04, "end": 0.05}, {"text": "se", "start": 0.05, "end": 0.2}, {"text": "pare", "start": 0.2, "end": 0.5}]
        _, js = C.captions(C.grupuri(ws, []), 2.0, "#38bdf8")
        culori = [x for x in js if "color:" in x]
        self.assertTrue(culori)
        self.assertTrue(all('overwrite:"auto"' in x for x in culori))

    def test_captions_nu_ajung_la_butoane(self):
        # trei cuvinte lungi la 58 px trec de x = 950, unde încep butoanele din dreapta
        ws = [{"text": t, "start": k * 0.5, "end": k * 0.5 + 0.45} for k, t in enumerate(["îmbunătățește", "videoclipurile", "automat"])]
        gr = C.grupuri(ws, [])
        self.assertTrue(all(len(" ".join(w["text"] for w in g)) <= C.MAX_CAR for g in gr))
        self.assertEqual(len(gr), 2)

    def test_lint_picat_arata_tot(self):
        self.assertEqual(C.mesaj_lint(True, "linia 1\n◇  0 errors"), "◇  0 errors")
        self.assertEqual(C.mesaj_lint(False, "✖ missing_timeline: ...\n◇  1 error"), "✖ missing_timeline: ...\n◇  1 error")

    def test_captions_sar_cuvintele_contopite(self):
        html = "".join(C.captions(C.grupuri(self.ws, []), 6.0, "#38bdf8")[0])
        self.assertIn("Claude Code", html)
        self.assertNotIn('"></span><span', html.replace('class="cw"', ""))

    @unittest.skipUnless(shutil.which("ffmpeg") and (RAD / "node_modules" / "hyperframes").is_dir(), "lipsesc ffmpeg sau pachetele")
    def test_index_trece_de_lint(self):
        with tempfile.TemporaryDirectory(dir=RAD / "proiecte", prefix="_test-compozitie-") as d:
            dosar = Path(d)
            for f in ("transcript.json", "scenariu.json"):
                shutil.copy(DATE / f, dosar / f)
            (dosar / "taieturi.json").write_text(json.dumps({"taieturi": [2.8], "bucati": []}), encoding="utf-8")
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=1080x1920:r=60:d=6", "-f", "lavfi",
                            "-i", "anullsrc=r=48000:cl=mono", "-t", "6", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                            str(dosar / "taiat.mp4")], check=True)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(dosar / "taiat.mp4"), "-vn", "-ac", "1", "-ar", "48000",
                            str(dosar / "voce.wav")], check=True)
            self.assertEqual(C.main([str(dosar)]), 0)
            self.assertTrue((dosar / "index.html").is_file())
            self.assertTrue((dosar / "assets" / "gsap.min.js").is_file())


if __name__ == "__main__":
    unittest.main()
