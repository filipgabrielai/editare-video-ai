import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAD))
from procese.editare import compozitie as C  # noqa: E402
from procese.editare import scenariu as S  # noqa: E402
from unelte import brand  # noqa: E402

DATE = RAD / "tests" / "date" / "reel"
MARTOR = RAD / "tests" / "date" / "compozitie" / "pagina-9x16.html"


def pagina_din_date() -> str:
    sc = json.loads((DATE / "scenariu.json").read_text(encoding="utf-8"))
    ws = S.corecteaza(S.cuvinte(DATE / "transcript.json"), sc["corecturi"])
    st = S.stil("studio")
    plan = C.planifica(sc, ws, [2.8], 6.0, st)
    cap_html, cap_js = C.captions(C.grupuri(ws, [2.8]), 6.0, st["accent"])
    return C.pagina(sc, plan, cap_html, cap_js, 6.0)


class TestCompozitie(unittest.TestCase):
    def setUp(self):
        self.sc = json.loads((DATE / "scenariu.json").read_text(encoding="utf-8"))
        self.ws = S.corecteaza(S.cuvinte(DATE / "transcript.json"), self.sc["corecturi"])

    def test_pagina_de_reel_e_aceeasi_ca_inainte_de_piese(self):
        # compoziția s-a despărțit în piese; un scenariu de reel scris pentru v1 trebuie să dea aceeași pagină, literă cu literă
        self.assertEqual(pagina_din_date(), MARTOR.read_text(encoding="utf-8").replace("\r\n", "\n"))

    def test_sunetele_nu_se_repeta_si_nu_se_calca(self):
        s = C.Sunete()
        for t in (0.1, 1.0, 1.0, 2.0, 3.0, 4.2):
            s.adauga("card", t)
        self.assertEqual([round(x[0], 2) for x in s.lista], [0.1, 2.0, 3.0, 4.2])   # cel puțin o secundă între sunete
        nume = [x[1] for x in s.lista]
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

    def test_randurile_care_apar_au_aceeasi_inaltime_ca_primul(self):
        # cu height:"auto" rândurile 2 și 3 ieșeau mai joase decât primul (84 px) și al treilea părea înghesuit
        js = "\n".join(C.planifica(self.sc, self.ws, [], 6.0, S.stil("studio"))["js"])
        self.assertNotIn('height:"auto"', js)
        self.assertIn("height:84, minHeight:84", js)

    def test_sunetele_de_card_sunt_incete_si_rare(self):
        s = C.Sunete()
        s.adauga("card", 0.1)
        s.adauga("pop", 0.6)       # prea aproape de card: nu se aude
        s.adauga("pop", 1.5)
        s.adauga("card", 2.0)      # cardul are prioritate: pop-ul de la 1,5 s dispare
        self.assertEqual([round(x[0], 2) for x in s.lista], [0.1, 2.0])
        self.assertTrue(all(v <= 0.4 for _, n, v, _ in s.lista if n in ("boom", "knock")))

    def test_cardurile_jongleaza_intre_trei_sunete(self):
        # Filip pe DRAFT 3 al demo-ului: „să jongleze între 2-3 când apar animațiile”; boom și knock singure sunau la fel
        s = C.Sunete()
        for t in (0.1, 2.0, 4.0, 6.0, 8.0, 10.0):
            s.adauga("card", t)
        nume = [x[1] for x in s.lista]
        self.assertEqual(len(set(nume[:3])), 3)
        self.assertTrue(all(a != b for a, b in zip(nume, nume[1:])))
        self.assertTrue(all((RAD / "sunete" / f"{n}.wav").exists() for n in nume))

    def test_cardul_cu_brand_primeste_logoul(self):
        sc = {"stil": "studio", "carduri": [
            {"id": "hook", "ancora": "start", "kicker": "HOOK", "randuri": [{"text": "a", "icoana": "zap"}]},
            {"id": "final", "ancora": "start", "kicker": "FINAL", "brand": True, "randuri": [{"text": "b", "icoana": "user"}]}]}
        html = "".join(C.planifica(sc, self.ws, [], 6.0, S.stil("studio"), None, '<img class="kl" src="assets/brand/logo.png" alt="">')["html"])
        self.assertEqual(html.count('class="kl"'), 1)
        self.assertIn('<div class="k"><img class="kl" src="assets/brand/logo.png" alt="">FINAL</div>', html)

    def test_preferintele_opresc_sunetele_si_captions(self):
        plan = {"sfx": [(0.05, "boom", 0.6, 0.6)]}
        cap = (["<div class=\"cap\">x</div>"], ["tl.to()"])
        b, _ = brand.combina({"preferinte": {"sunete": "oprite", "captions": False}})
        self.assertEqual(C.aplica_preferinte(plan, cap, b), ([], []))
        self.assertEqual(plan["sfx"], [])
        plan = {"sfx": [(0.05, "boom", 0.6, 0.6)]}
        self.assertEqual(C.aplica_preferinte(plan, cap, brand.IMPLICIT), cap)
        self.assertEqual(plan["sfx"], [(0.05, "boom", 0.6, 0.6)])

    def test_brand_css_in_pagina_si_in_assets(self):
        plan = C.planifica(self.sc, self.ws, [], 6.0, S.stil("studio"))
        p = C.pagina(self.sc, plan, [], [], 6.0)
        self.assertLess(p.index('href="assets/stil.css"'), p.index('href="assets/brand.css"'))
        with tempfile.TemporaryDirectory() as d:
            b, _ = brand.combina({"culori": {"accent": "#ff5500"}})
            C.pregateste_assets(Path(d), "studio", b)
            self.assertIn("--accent:#ff5500", (Path(d) / "assets" / "brand.css").read_text(encoding="utf-8"))

    def test_durata_se_scrie_taiata_in_jos(self):
        # 146,16667 scris „146.1667” trece de granița de cadru și randarea adaugă un cadru gol la coadă (About, 2 oct)
        self.assertEqual(C.dur_str(146.16667), "146.1666")
        self.assertEqual(C.dur_str(26.15), "26.1500")
        self.assertEqual(C.cadre_planificate(146.16667, 60), 8770)
        self.assertEqual(C.cadre_planificate(26.15, 60), 1569)
        self.assertAlmostEqual(C.pe_grila(26.5171), 1591 / 60)   # sunetul AAC e cu ~10 ms mai lung decât imaginea
        plan = C.planifica(self.sc, self.ws, [], 6.0, S.stil("studio"))
        p = C.pagina(self.sc, plan, [], [], 1591 / 60)
        self.assertIn('data-duration="26.5166"', p)
        self.assertNotIn('data-duration="26.517"', p)

    def test_pagina_orizontala(self):
        sc = {"stil": "studio", "format": "16:9", "cadru": {"carduri": "dreapta"},
              "carduri": [{"id": "a", "ancora": "start", "kicker": "A", "randuri": [{"text": "unu"}, {"text": "doi", "ancora": "productiv"}]}]}
        plan = C.planifica(sc, self.ws, [], 6.0, S.stil("studio"), fmt="16:9")
        js = "\n".join(plan["js"])
        self.assertIn("xPercent:0", js)                 # cardul stă lângă om, nu centrat deasupra lui
        self.assertNotIn("xPercent:-50", js)
        self.assertIn("height:72, minHeight:72", js)
        p = C.pagina(sc, plan, [], [], 6.0, "16:9")
        self.assertIn('data-width="1920" data-height="1080"', p)
        self.assertIn("--card-st:auto;--card-dr:96px", p)
        self.assertIn("--captions-y:880px", p)
        with tempfile.TemporaryDirectory() as d:
            C.pregateste_assets(Path(d), "studio", None, "16:9")
            self.assertIn("1920px", (Path(d) / "assets" / "stil.css").read_text(encoding="utf-8"))

    def test_subtitrarile_orizontale_pot_fi_mai_late(self):
        ws = [{"text": t, "start": k * 0.5, "end": k * 0.5 + 0.45} for k, t in enumerate(["îmbunătățește", "videoclipurile", "automat"])]
        self.assertEqual([len(g) for g in C.grupuri(ws, [], max_car=22)], [1, 2])
        self.assertEqual([len(g) for g in C.grupuri(ws, [], max_car=34)], [2, 1])   # „îmbunătățește videoclipurile” are 28

    def test_logourile_in_locul_iconitei(self):
        sc = {"stil": "studio", "logo_inversat": ["openai"], "carduri": [{"id": "l1", "ancora": "start", "kicker": "LOCUL 1",
              "randuri": [{"text": "**Claude Code** și **Codex**", "logo": ["claude", "openai"]}]}]}
        html = "".join(C.planifica(sc, self.ws, [], 6.0, S.stil("studio"), {"claude": "claude.png", "openai": "openai.svg"})["html"])
        self.assertIn('<img class="lg" src="assets/logo/claude.png"', html)
        self.assertIn('<img class="lg inv" src="assets/logo/openai.svg"', html)
        self.assertNotIn('class="ic"', html)

    def test_logo_lipsa_spune_unde_se_pune(self):
        sc = {"carduri": [{"id": "a", "randuri": [{"text": "x", "logo": "bolt"}]}]}
        erori = C.logouri_lipsa(sc, {"claude": "claude.png"})
        self.assertEqual(len(erori), 1)
        self.assertIn("bolt", erori[0])
        self.assertIn("logo/", erori[0])

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
