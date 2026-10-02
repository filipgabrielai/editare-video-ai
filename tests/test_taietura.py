import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from procese.editare import taietura as T  # noqa: E402

WS = [{"text": t} for t in ["Și", "totodată,", "în", "aplicație", "pot", "în", "aplicație,", "ca"]]


class TestCuvinte(unittest.TestCase):
    def test_idx_prima_a_doua_si_ultima_aparitie(self):
        self.assertEqual(T.idx(WS, "în"), 2)
        self.assertEqual(T.idx(WS, "aplicație#2"), 6)
        self.assertEqual(T.idx(WS, "în@ultimul"), 5)
        self.assertEqual(T.idx(WS, "totodată"), 1)

    def test_idx_cuvant_lipsa_spune_ce_exista(self):
        with self.assertRaises(SystemExit) as e:
            T.idx(WS, "YouTube")
        self.assertIn("aplicație", str(e.exception))


class TestCapete(unittest.TestCase):
    def rms(self, a, b):   # liniște (−80 dB), vorbire (−20 dB) între a și b secunde
        return [(-20.0 if a <= k * T.PAS < b else -80.0) for k in range(int(4 / T.PAS))]

    def test_capete_pe_grila_de_cadre_cu_pad(self):
        a0, a1 = T.capete(self.rms(1.0, 2.0), 1.02, 1.98, 0.0, 1e9)
        self.assertAlmostEqual(a0 * T.FPS, round(a0 * T.FPS), places=6)
        self.assertAlmostEqual(a1 * T.FPS, round(a1 * T.FPS), places=6)
        self.assertTrue(0.9 <= a0 <= 0.97, a0)
        self.assertTrue(1.99 <= a1 <= 2.1, a1)

    def test_nu_trece_de_cuvantul_urmator(self):
        _, a1 = T.capete(self.rms(1.0, 2.5), 1.02, 1.98, 0.0, 2.2)
        self.assertLessEqual(a1, 2.2)

    def test_camera_cu_zgomot_nu_lungeste_pauzele(self):
        # ventilator de laptop la −45 dB: cu pragul fix de −50 dB tot zgomotul era „vorbire” și pauza creștea la ~0,5 s
        rms = [(-20.0 if 1.0 <= k * T.PAS < 2.0 else -45.0) for k in range(int(4 / T.PAS))]
        prag = T.prag(rms)
        self.assertGreater(prag, -45.0)
        a0, a1 = T.capete(rms, 1.02, 1.98, 0.0, 1e9, prag)
        self.assertTrue(0.9 <= a0 <= 0.97, a0)
        self.assertTrue(1.99 <= a1 <= 2.1, a1)

    def test_clicurile_de_buze_nu_sunt_vorbire(self):
        # un clic de 5–10 ms la −46 dB înainte de cuvânt lungea pauza de la tăietură la ~0,5 s (reelul „Top 3”)
        rms = self.rms(1.0, 2.0)
        for t in (0.70, 0.86, 0.865):
            rms[round(t / T.PAS)] = -46.0
        for t in (2.10, 2.105):
            rms[round(t / T.PAS)] = -46.0
        a0, a1 = T.capete(rms, 0.95, 1.98, 0.0, 1e9)
        self.assertTrue(0.9 <= a0 <= 0.97, a0)
        self.assertTrue(1.99 <= a1 <= 2.05, a1)

    def test_whisper_pune_cuvantul_prea_devreme(self):
        # Whisper a pus „Și” cu 150 ms înainte de sunet; căutarea se oprea acolo și lăsa 0,25 s de liniște la tăietură
        a0, _ = T.capete(self.rms(1.0, 2.0), 0.80, 1.98, 0.0, 1e9)
        self.assertTrue(0.9 <= a0 <= 0.97, a0)

    def test_respiratia_inainte_de_cuvant_nu_e_vorbire(self):
        # „Și pe primul loc” (reelul „Top 3”): 80 ms de buze la −42 dB, apoi 0,35 s de liniște în care se uita în lateral, iar
        # Whisper a pus „Și” cu 0,4 s înainte de sunet; bucata pornea de la buze și pauza de la tăietură ajungea la ~0,5 s
        rms = self.rms(1.0, 2.0)
        for k in range(round(0.55 / T.PAS), round(0.63 / T.PAS)):
            rms[k] = -42.0
        a0, _ = T.capete(rms, 0.58, 1.98, 0.0, 1e9)
        self.assertTrue(0.9 <= a0 <= 0.97, a0)

    def test_primul_cuvant_scurt_urmat_de_pauza_ramane(self):
        # „Și… pe primul loc”: un cuvânt scurt, spus la nivelul vorbirii, apoi o pauză, e vorbire și rămâne în bucată
        rms = self.rms(1.0, 2.0)
        for k in range(round(0.55 / T.PAS), round(0.65 / T.PAS)):
            rms[k] = -24.0
        a0, _ = T.capete(rms, 0.58, 1.98, 0.0, 1e9)
        self.assertTrue(0.48 <= a0 <= 0.52, a0)

    def test_inceputul_nu_se_cauta_inaintea_cuvantului_anterior(self):
        # demo-ul pe copia 1080p: Whisper a pus „îți” cu 0,16 s înainte de sunet, căutarea a dat peste „repară” (cuvântul
        # anterior), iar limita de după el a lăsat bucata să pornească în coada lui stinsă, cu 0,13 s înainte de „îți”
        rms = self.rms(1.0, 2.0)
        for k in range(round(0.6 / T.PAS), round(0.85 / T.PAS)):
            rms[k] = -25.0
        a0, _ = T.capete(rms, 0.88, 1.98, 0.9, 1e9)
        self.assertTrue(0.94 <= a0 <= 0.97, a0)

    def test_coada_lungeste_capatul_pe_grila_fara_sa_treaca_de_cuvantul_urmator(self):
        self.assertAlmostEqual(T.cu_coada(2.0, 0.1, 1e9), 2.1)
        self.assertAlmostEqual(T.cu_coada(2.0, 0.1, 2.05) * T.FPS, round(T.cu_coada(2.0, 0.1, 2.05) * T.FPS))
        self.assertLessEqual(T.cu_coada(2.0, 0.1, 2.05), 2.05)
        self.assertEqual(T.cu_coada(2.0, 0.0, 1e9), 2.0)

    def test_in_liniste_pragul_ramane_minus_50(self):
        self.assertEqual(T.prag(self.rms(1.0, 2.0)), T.PRAG)


class TestFiltre(unittest.TestCase):
    def test_umple_9_16_fara_deformare_si_exact_pe_cadre(self):
        f = T.filtre([("IMG_1", 1.5, 3.0), ("IMG_2", 0.0, 1.0)], [0.5, 0.0])
        self.assertIn("trim=end_frame=90", f)
        self.assertIn("force_original_aspect_ratio=increase", f)
        self.assertIn("crop=1080:1920", f)
        self.assertNotIn("trim=-", f)   # bucata care începe la 0 nu primește start negativ
        self.assertTrue(f.endswith("concat=n=2:v=1:a=1[v][a]"))

    def test_filtrul_pe_fata_dupa_decupaj(self):
        f = T.filtre([("IMG_1", 1.5, 3.0)], [0.5], "smartblur=lr=2.5:ls=0.7:lt=4")
        self.assertIn("crop=1080:1920,setsar=1,smartblur=lr=2.5:ls=0.7:lt=4[v0]", f)
        self.assertNotIn("smartblur", T.filtre([("IMG_1", 1.5, 3.0)], [0.5]))

    def test_filmarea_orizontala_umple_16_9(self):
        f = T.filtre([("IMG_1", 1.5, 3.0)], [0.5], filmare="16:9")
        self.assertIn("scale=1920:1080:force_original_aspect_ratio=increase", f)
        self.assertIn("crop=1920:1080", f)
        self.assertNotIn("1080:1920", f)

    def test_clipul_orizontal_decupat_la_9_16_se_spune(self):
        # un clip filmat pe orizontală, tăiat fără --filmare, pierdea marginile în tăcere
        m = T.avertisment_orientare("IMG_1622", True, "9:16")
        self.assertIn("orizontală", m)
        self.assertIn("--filmare 16:9", m)
        self.assertIn("verticală", T.avertisment_orientare("IMG_1", False, "16:9"))
        self.assertEqual(T.avertisment_orientare("IMG_1", False, "9:16"), "")
        self.assertEqual(T.avertisment_orientare("IMG_1", True, "16:9"), "")


if __name__ == "__main__":
    unittest.main()
