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
    return Fragment(html=['<div id="titlu">peste titlul kitului</div>'], intervale=[{"id": m["id"], "intra": 1, "iese": 2, "el": "titlu"}])
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
        cu_stil = C.pagina(self.sc, plan, [], [], 6.0, stil_meu=True)
        self.assertLess(cu_stil.index("<style>"), cu_stil.index('href="assets/stil-meu.css"'))   # stilul omului bate și piesele

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

    def test_o_piesa_stricata_spune_ce_are_nu_da_traceback(self):
        # omul își face prima piesă cu Claude: orice greșeală din ea trebuie spusă pe nume, cu fișierul și momentul
        stricate = {
            "pica": "def construieste(ctx, m):\n    raise ValueError('ceva')\n",
            "nimic": "def construieste(ctx, m):\n    return None\n",
            "dict": "def construieste(ctx, m):\n    return {'html': []}\n",
            "sintaxa": "def construieste(ctx, m)\n    return 1\n",
            "veche": "from piese.comun import Fragment\ndef construieste(ctx):\n    return Fragment()\n",
            "import_rau": "import nu_exista_asa_ceva\ndef construieste(ctx, m):\n    return 1\n",
        }
        for nume, cod in stricate.items():
            (self.ale / f"{nume}.py").write_text(cod, encoding="utf-8")
            with self.assertRaises(SystemExit, msg=nume) as e:
                self.plan([{"piesa": nume, "id": "x"}])
            self.assertIn(f"„{nume}”", str(e.exception), nume)
            self.assertIn("piese/cuvant.py", str(e.exception), nume)

    def test_piesa_isi_declara_intervalul(self):
        # fără interval, piesa nu apare nici pe planșe, nici în tabelul de vizibilitate: nimeni n-ar vedea-o înainte de randare
        (self.ale / "muta.py").write_text('from piese.comun import Fragment\n\n\ndef construieste(ctx, m):\n'
                                           '    return Fragment(html=[f\'<div class="piesa" id="m-{m["id"]}"></div>\'])\n', encoding="utf-8")
        with self.assertRaises(SystemExit) as e:
            self.plan([{"piesa": "muta", "id": "x"}])
        self.assertIn("intervale", str(e.exception))

    def test_regula_id_urilor_pe_ghilimele_simple_si_data_id(self):
        baza = "from piese.comun import Fragment\n\n\ndef construieste(ctx, m):\n    return Fragment(html=[%r], intervale=[{'id': m['id'], 'intra': 1, 'iese': 2, 'el': 'm-' + m['id']}])\n"
        (self.ale / "simple.py").write_text(baza % """<div class='piesa' id='m-x'><i id='titlu'></i></div>""", encoding="utf-8")
        with self.assertRaises(SystemExit) as e:
            self.plan([{"piesa": "simple", "id": "x"}])
        self.assertIn("titlu", str(e.exception))
        (self.ale / "date.py").write_text(baza % """<div class="piesa" id="m-x" data-id="abc"></div>""", encoding="utf-8")
        self.assertIn('data-id="abc"', "".join(self.plan([{"piesa": "date", "id": "x"}])["html"]))   # data-id nu e id

    def test_cuvantul_cu_durata_scrisa_gresit(self):
        with self.assertRaises(SystemExit) as e:
            self.plan([{"piesa": "cuvant", "id": "w", "text": "a", "ancora": "cât de productiv", "durata": "mult"}])
        self.assertIn("durata", str(e.exception))

    def test_momentele_scrise_gresit_spun_ce_au(self):
        erori, _ = S.valideaza({**self.sc, "momente": ["cuvant", {"id": "x"}, {"piesa": "card", "id": "y"}]})
        self.assertTrue(any("nu e un obiect" in e for e in erori))
        self.assertTrue(any("nu are „piesa”" in e for e in erori))
        self.assertTrue(any("„card”" in e and "carduri" in e for e in erori))   # cardurile au locul lor în scenariu
        self.assertFalse(any("None" in e for e in erori))

    def test_doar_piesele_adevarate_sunt_listate(self):
        for f in ("__init__.py", "Test.py", "o-piesa.py", "sageata.py"):
            (self.ale / f).write_text(PIESA_MEA, encoding="utf-8")
        self.assertEqual(piese.disponibile(), ["cuvant", "sageata"])
        (self.ale / "card.py").write_text(PIESA_MEA, encoding="utf-8")       # nu înlocuiește cardurile kitului
        self.assertNotIn("card", piese.disponibile())

    def test_pozitia_negativa_e_prinsa_si_pe_mai_multe_linii(self):
        self.assertEqual(len(C.pozitii_negative(['tl.to("#a", {x:1}, 0.5);\ntl.to("#a", {x:2}, -0.5);', 'tl.to("#b", {x:1}, -0.25)'])), 2)

    def test_ce_e_al_omului_nu_e_urmarit_de_git(self):
        # git aruncă fără avertisment un fișier ignorat când kitul începe să urmărească același nume: în folderele omului
        # kitul nu ține nimic în afară de .gitkeep
        import shutil
        import subprocess
        if not shutil.which("git") or not (RAD / ".git").exists():
            self.skipTest("nu e un repo git")
        r = subprocess.run(["git", "ls-files", "piese/ale-mele", "brand"], cwd=RAD, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(sorted(r.stdout.split()), ["brand/.gitkeep", "piese/ale-mele/.gitkeep"])

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
            self.assertTrue(p.split("</head>")[0].rstrip().endswith('href="assets/stil-meu.css">'))   # ultimul din <head>

    def test_piesele_omului_se_vad_in_tabelul_de_vizibilitate(self):
        rez = {"ndif": 0, "dif": [], "viz": {"m-s1": [[2.0, 9.0]]}}
        p = ordine.probleme(rez, [{"id": "s1", "intra": 2.0, "iese": 3.0, "el": "m-s1"}])
        self.assertEqual(len(p), 1)
        self.assertIn("„s1”", p[0])
        self.assertIn(".piesa", ordine.SELECTOR)


if __name__ == "__main__":
    unittest.main()
