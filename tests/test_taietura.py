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
        self.assertTrue(0.96 <= a0 <= 0.99, a0)
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
        self.assertTrue(0.96 <= a0 <= 0.99, a0)
        self.assertTrue(1.99 <= a1 <= 2.1, a1)

    def test_clicurile_de_buze_nu_sunt_vorbire(self):
        # un clic de 5–10 ms la −46 dB înainte de cuvânt lungea pauza de la tăietură la ~0,5 s (reelul „Top 3”)
        rms = self.rms(1.0, 2.0)
        for t in (0.70, 0.86, 0.865):
            rms[round(t / T.PAS)] = -46.0
        for t in (2.10, 2.105):
            rms[round(t / T.PAS)] = -46.0
        a0, a1 = T.capete(rms, 0.95, 1.98, 0.0, 1e9)
        self.assertTrue(0.96 <= a0 <= 0.99, a0)
        self.assertTrue(1.99 <= a1 <= 2.05, a1)

    def test_whisper_pune_cuvantul_prea_devreme(self):
        # Whisper a pus „Și” cu 150 ms înainte de sunet; căutarea se oprea acolo și lăsa 0,25 s de liniște la tăietură
        a0, _ = T.capete(self.rms(1.0, 2.0), 0.80, 1.98, 0.0, 1e9)
        self.assertTrue(0.96 <= a0 <= 0.99, a0)

    def test_respiratia_inainte_de_cuvant_nu_e_vorbire(self):
        # „Și pe primul loc” (reelul „Top 3”): 80 ms de buze la −42 dB, apoi 0,35 s de liniște în care se uita în lateral, iar
        # Whisper a pus „Și” cu 0,4 s înainte de sunet; bucata pornea de la buze și pauza de la tăietură ajungea la ~0,5 s
        rms = self.rms(1.0, 2.0)
        for k in range(round(0.55 / T.PAS), round(0.63 / T.PAS)):
            rms[k] = -42.0
        a0, _ = T.capete(rms, 0.58, 1.98, 0.0, 1e9)
        self.assertTrue(0.96 <= a0 <= 0.99, a0)

    def test_primul_cuvant_scurt_urmat_de_pauza_ramane(self):
        # „Și… pe primul loc”: un cuvânt scurt, spus la nivelul vorbirii, apoi o pauză, e vorbire și rămâne în bucată
        rms = self.rms(1.0, 2.0)
        for k in range(round(0.55 / T.PAS), round(0.65 / T.PAS)):
            rms[k] = -24.0
        a0, _ = T.capete(rms, 0.58, 1.98, 0.0, 1e9)
        self.assertTrue(0.51 <= a0 <= 0.54, a0)

    def test_inceputul_nu_se_cauta_inaintea_cuvantului_anterior(self):
        # demo-ul pe copia 1080p: Whisper a pus „îți” cu 0,16 s înainte de sunet, căutarea a dat peste „repară” (cuvântul
        # anterior), iar limita de după el a lăsat bucata să pornească în coada lui stinsă, cu 0,13 s înainte de „îți”
        rms = self.rms(1.0, 2.0)
        for k in range(round(0.6 / T.PAS), round(0.85 / T.PAS)):
            rms[k] = -25.0
        a0, _ = T.capete(rms, 0.88, 1.98, 0.9, 1e9)
        self.assertTrue(0.96 <= a0 <= 0.99, a0)

    def test_coada_lungeste_capatul_pe_grila_fara_sa_treaca_de_cuvantul_urmator(self):
        self.assertAlmostEqual(T.cu_coada(2.0, 0.1, 1e9), 2.1)
        self.assertAlmostEqual(T.cu_coada(2.0, 0.1, 2.05) * T.FPS, round(T.cu_coada(2.0, 0.1, 2.05) * T.FPS))
        self.assertLessEqual(T.cu_coada(2.0, 0.1, 2.05), 2.05)
        self.assertEqual(T.cu_coada(2.0, 0.0, 1e9), 2.0)

    def test_pauza_dintre_fraze_e_cea_din_variantele_postate(self):
        # pe filmarea reelului din 1 oct, cu 0,05 s înainte și coada lăsată liberă, fiecare îmbinare ieșea cu ~0,1 s mai largă
        # decât în varianta postată de Filip (58,57 s față de 56,93 s): 0,02 s înainte de sunet și 0,03 s după
        a0, a1 = T.capete(self.rms(1.0, 2.0), 1.02, 1.98, 0.0, 1e9)
        self.assertTrue(0.97 <= a0 <= 0.99, a0)
        self.assertTrue(2.02 <= a1 <= 2.04, a1)

    def test_coada_de_sub_voce_intra_cel_mult_80_ms(self):
        # după ultimul cuvânt rămâne ecou sau respirație la −46 dB, iar Whisper pune sfârșitul cuvântului cu 0,1 s mai târziu:
        # capătul mergea pe toată coada. Sub −40 dB intră cel mult 0,08 s
        rms = self.rms(1.0, 2.0)
        for k in range(round(2.0 / T.PAS), round(2.3 / T.PAS)):
            rms[k] = -46.0
        _, a1 = T.capete(rms, 1.02, 2.10, 0.0, 1e9)
        self.assertTrue(2.09 <= a1 <= 2.12, a1)

    def test_nivelul_pe_5_ms_din_wav_pentru_capete(self):
        # capetele se măsoară pe wav-ul de 16 kHz: la 8 kHz „s” și „ș” aproape nu se văd, iar cu 0,02 s în față s-ar pierde
        import array, math, tempfile, wave
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "ton.wav"
            a = array.array("h", [0] * 16000 + [int(3276.8 * math.sin(2 * math.pi * 6000 * i / 16000)) for i in range(16000)])
            if sys.byteorder == "big":
                a.byteswap()
            with wave.open(str(f), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); w.writeframes(a.tobytes())
            r = T.rms_wav(f, T.PAS)
        self.assertEqual(len(r), 399)
        self.assertLess(r[100], -80)
        self.assertAlmostEqual(r[300], -23.0, delta=0.5)

    def test_in_liniste_pragul_ramane_minus_50(self):
        self.assertEqual(T.prag(self.rms(1.0, 2.0)), T.PRAG)


def r10(coada=True):
    """Ferestre de 10 ms: liniște, un „ș” slab (0,96–1,00 s), voce (1,00–2,00 s), coada stinsă a ultimului cuvânt (2,00–2,15 s)."""
    r = [-80.0] * 400
    for k in range(96, 100):
        r[k] = -41.0
    for k in range(100, 200):
        r[k] = -20.0
    if coada:
        for k in range(200, 215):
            r[k] = -36.0
    return r


class TestStrans(unittest.TestCase):
    def test_bucata_care_incepe_cu_si_continua_fraza(self):
        self.assertTrue(T.e_strans({}, "Și", 1))
        self.assertTrue(T.e_strans({}, "și,", 2))
        self.assertFalse(T.e_strans({}, "Sigur", 1))
        self.assertFalse(T.e_strans({}, "Și", 0))                    # prima bucată nu are de ce să se lipească
        self.assertFalse(T.e_strans({"strans": False}, "Și", 1))     # „Și acum partea importantă” deschide altă idee
        self.assertTrue(T.e_strans({"strans": True}, "altul", 1))    # enumerare fără „și”

    def test_debutul_strans_porneste_pe_sunet(self):
        # măsurat pe ce a strâns Filip de mână: bucata începe chiar pe sunet (~−42 dB), fără marjă
        self.assertAlmostEqual(T.debut_strans(r10(), 0.95, 2.0, 0.0), 0.96, places=2)
        fara_s = r10()
        for k in range(96, 100):
            fara_s[k] = -80.0
        self.assertAlmostEqual(T.debut_strans(fara_s, 0.98, 2.0, 0.0), 1.00, places=2)
        self.assertAlmostEqual(T.debut_strans(r10(), 0.95, 2.0, 0.98), 0.98, places=2)   # nu intră în cuvântul dinainte

    def test_sfarsitul_strans_taie_coada_stinsa(self):
        self.assertAlmostEqual(T.sfarsit_strans(r10(), 1.0, 2.15), 2.04, places=2)   # ultima fereastră peste −32 dB, plus 0,04 s
        self.assertAlmostEqual(T.sfarsit_strans(r10(), 1.0, 2.02), 2.02, places=2)   # niciodată după sfârșitul normal

    def test_capetele_normale_si_stranse(self):
        a0, a1, s_out = T.capete_bucata(0.95, 2.15, 0.0, 1e9, r10(), False, False)
        self.assertAlmostEqual(a0, round(0.93 * T.FPS) / T.FPS)
        self.assertAlmostEqual(a1, round(2.18 * T.FPS) / T.FPS)
        self.assertFalse(s_out)
        a0, a1, s_out = T.capete_bucata(0.95, 2.15, 0.0, 1e9, r10(), True, True)
        self.assertAlmostEqual(a0, round(0.96 * T.FPS) / T.FPS)
        self.assertAlmostEqual(a1, round(2.04 * T.FPS) / T.FPS)
        self.assertTrue(s_out)

    def test_plasa_de_siguranta_asculta_ultimul_cuvant(self):
        # sfârșitul strâns mânca „-ri” din „videoclipuri” (1 oct): dacă Whisper nu mai aude același cuvânt, rămâne sfârșitul normal
        _, a1, s_out = T.capete_bucata(0.95, 2.15, 0.0, 1e9, r10(), False, True,
                                       lambda a, b: "și videoclipuri" if b > 2.1 else "și videoclipu", "videoclipuri.")
        self.assertFalse(s_out)
        self.assertAlmostEqual(a1, round(2.18 * T.FPS) / T.FPS)
        _, a1, s_out = T.capete_bucata(0.95, 2.15, 0.0, 1e9, r10(), False, True, lambda a, b: "Și Videoclipuri", "videoclipuri.")
        self.assertTrue(s_out)
        self.assertAlmostEqual(a1, round(2.04 * T.FPS) / T.FPS)
        _, _, s_out = T.capete_bucata(0.95, 2.15, 0.0, 1e9, r10(), False, True, lambda a, b: "", "videoclipuri.")
        self.assertFalse(s_out)   # Whisper n-a auzit nimic (sau lipsește): nu riscăm cuvântul

    def test_inceputul_strans_nu_mananca_un_s_slab(self):
        # demo-ul „Top 3”, „Și dacă vrei să înveți”: „ș” e la −50 dB, începutul strâns pornea pe „i” și se auzea „Dacă vrei”
        r = r10()
        for k in range(96, 100):
            r[k] = -50.0
        a0, _, _ = T.capete_bucata(0.95, 2.15, 0.0, 1e9, r, True, False, lambda a, b: "Dacă vrei", "vrei.", "Și")
        self.assertAlmostEqual(a0, round(0.95 * T.FPS) / T.FPS)    # pe sunetul găsit la tăietura normală, tot fără pad
        a0, _, _ = T.capete_bucata(0.95, 2.15, 0.0, 1e9, r, True, False, lambda a, b: "și dacă vrei", "vrei.", "Și")
        self.assertAlmostEqual(a0, round(1.00 * T.FPS) / T.FPS)    # primul cuvânt se aude: rămâne strâns
        a0, _, _ = T.capete_bucata(0.95, 2.15, 0.97, 1e9, r, True, False, lambda a, b: "Dacă vrei", "vrei.", "Și")
        self.assertAlmostEqual(a0, round(0.97 * T.FPS) / T.FPS)    # nici așa nu intră în cuvântul dinainte

    def test_sfarsitul_slab_al_cuvantului_nu_se_pierde(self):
        # demo-ul „Top 3”: „doar din prompturi”, cu „-uri” sub −40 dB; cu coada limitată la 0,08 s se auzea „prompt”.
        # Când limita chiar scurtează bucata, bucata se ascultă; dacă ultimul cuvânt nu mai iese, rămâne toată coada
        a0, a1, _ = T.capete_bucata(0.95, 2.08, 0.0, 1e9, None, False, False,
                                    lambda a, b: "doar din prompturi" if b > 2.2 else "doar din prompt", "prompturi.", "doar", 2.25)
        self.assertAlmostEqual(a1, round(2.28 * T.FPS) / T.FPS)
        # Whisper aude la fel de greșit și bucata lungă („clode” în loc de „Claude”): nu e semn că s-a pierdut ceva
        _, a1, _ = T.capete_bucata(0.95, 2.08, 0.0, 1e9, None, False, False, lambda a, b: "editat de clode", "Claude.", "editat", 2.25)
        self.assertAlmostEqual(a1, round(2.11 * T.FPS) / T.FPS)
        apeluri = []   # fără coadă în plus nu e nimic de ascultat
        T.capete_bucata(0.95, 2.08, 0.0, 1e9, None, False, False, lambda a, b: apeluri.append(b) or "", "x", "y", 2.08)
        self.assertEqual(apeluri, [])

    def test_capete_sunet_cu_toata_coada(self):
        rms = [(-20.0 if 1.0 <= k * T.PAS < 2.0 else -80.0) for k in range(int(4 / T.PAS))]
        for k in range(round(2.0 / T.PAS), round(2.3 / T.PAS)):
            rms[k] = -46.0
        _, scurt = T.capete_sunet(rms, 1.02, 2.10, 0.0, 1e9)
        _, lung = T.capete_sunet(rms, 1.02, 2.10, 0.0, 1e9, coada_max=None)
        self.assertAlmostEqual(scurt, 2.08, delta=0.011)
        self.assertGreater(lung, 2.15)

    def test_martorul_nu_scuza_o_silaba_pierduta(self):
        # dacă Whisper aude „prompt” și pe bucata cu toată coada, asta nu dovedește că „-uri” nu s-a pierdut: capătul scurt
        # rămâne doar când ce se aude se termină ca în transcript („clode” / „Claude”), altfel rămâne toată coada
        _, a1, _ = T.capete_bucata(0.95, 2.08, 0.0, 1e9, None, False, False, lambda a, b: "doar din prompt", "prompturi.", "doar", 2.25)
        self.assertAlmostEqual(a1, round(2.28 * T.FPS) / T.FPS)

    def test_ce_s_a_ascultat_o_data_nu_se_mai_asculta(self):
        # fiecare ascultare e un whisper-cli pornit de la zero (modelul de 1,6 GB); la re-tăiere capetele neschimbate revin la fel
        import tempfile
        apeluri = []

        def transcrie(a, b):
            apeluri.append((a, b))
            return "" if b > 9 else f"text {a} {b}"
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "ascultari.json"
            asc = T.Ascultari(f, "ggml-large-v3-turbo.bin", "ro")
            self.assertEqual(asc.asculta("IMG_1", 1.0, 2.5, transcrie), "text 1.0 2.5")
            self.assertEqual(asc.asculta("IMG_1", 1.0, 2.5, transcrie), "text 1.0 2.5")
            self.assertEqual(asc.asculta("IMG_1", 1.0, 2.6, transcrie), "text 1.0 2.6")     # alt capăt: se ascultă
            self.assertEqual(asc.asculta("IMG_1", 1.0, 9.5, transcrie), "")
            self.assertEqual(asc.asculta("IMG_1", 1.0, 9.5, transcrie), "")                # Whisper n-a mers: nu se ține minte
            self.assertEqual(len(apeluri), 4)
            self.assertEqual((asc.noi, asc.din_cache), (4, 1))
            asc.salveaza()
            alta = T.Ascultari(f, "ggml-large-v3-turbo.bin", "ro")                        # la următoarea tăietură
            self.assertEqual(alta.asculta("IMG_1", 1.0, 2.5, transcrie), "text 1.0 2.5")
            self.assertEqual(len(apeluri), 4)
            mic = T.Ascultari(f, "ggml-tiny.bin", "ro")                                   # alt model aude altceva
            mic.asculta("IMG_1", 1.0, 2.5, transcrie)
            self.assertEqual(len(apeluri), 5)

    def test_cuvintele_stau_in_bucata_lor(self):
        # Whisper pune primul cuvânt și cu 0,05 s înainte de sunet; cu 0,02 s în fața bucății, cuvântul ieșea la −0,03 s în
        # transcript.json și o ancoră pe el „nu apărea în transcript după 0,00 s” (proba cap-coadă, 2 oct)
        ws = [{"text": "Mi", "start": 0.10, "end": 0.30}, {"text": "se", "start": 0.30, "end": 0.45}, {"text": "pare.", "start": 0.45, "end": 1.40}]
        out = T.cuvinte_pe_video(ws, 5.0, 5.15, 6.20, 10.0)        # bucata e 5,15–6,20 în clip și începe la 10,0 în video
        self.assertEqual([w["text"] for w in out], ["Mi", "se", "pare."])
        self.assertEqual(out[0]["start"], 10.0)                    # nu înaintea bucății
        self.assertAlmostEqual(out[0]["end"], 10.15)
        self.assertAlmostEqual(out[1]["start"], 10.15)
        self.assertAlmostEqual(out[2]["end"], 11.05)               # nu după bucată
        self.assertTrue(all(w["start"] <= w["end"] for w in out))

    def test_finalul_ramane_pe_om(self):
        # Filip, 2 oct: fără 0,25 s după ultimul cuvânt, cu gura închisă, videoul „pare tăiat”
        self.assertEqual(T.coada_bucatii({}, True), 0.25)
        self.assertEqual(T.coada_bucatii({}, False), 0.0)
        self.assertEqual(T.coada_bucatii({"coada": 0}, True), 0)       # omul o poate opri
        self.assertEqual(T.coada_bucatii({"coada": 0.1}, False), 0.1)

    def test_fara_semne(self):
        self.assertEqual(T.fara_semne("Și,"), "si")
        self.assertEqual(T.fara_semne("videoclipuri."), "videoclipuri")

    def test_capete_sunet_da_secundele_fara_pad(self):
        rms = [(-20.0 if 1.0 <= k * T.PAS < 2.0 else -80.0) for k in range(int(4 / T.PAS))]
        on, sf = T.capete_sunet(rms, 1.02, 1.98, 0.0, 1e9)
        self.assertAlmostEqual(on, 1.0, delta=0.011)
        self.assertAlmostEqual(sf, 2.0, delta=0.011)

    def test_nivelul_pe_10_ms_din_wav(self):
        # „ș” și „s” au energia peste 4 kHz: îmbinările strânse se măsoară pe wav-ul de 16 kHz, nu pe fișierul de 8 kHz
        import array, math, tempfile, wave
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "ton.wav"
            a = array.array("h", [0] * 16000 + [int(3276.8 * math.sin(2 * math.pi * 6000 * i / 16000)) for i in range(16000)])
            if sys.byteorder == "big":
                a.byteswap()
            with wave.open(str(f), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(16000); w.writeframes(a.tobytes())
            r = T.rms10_db(f)
        self.assertEqual(len(r), 199)
        self.assertLess(r[50], -80)                       # liniște
        self.assertAlmostEqual(r[150], -23.0, delta=0.5)  # un ton de 6 kHz la o zecime din maxim: −20 dB vârf, −23 dB RMS


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

    def test_sunetul_fiecarei_bucati_are_exact_cadrele_ei(self):
        # AAC lasă ~10 ms în plus la coada fiecărei bucăți; adunate, împing vocea față de imagine
        f = T.filtre([("IMG_1", 1.5, 3.0)], [0.5])
        self.assertIn("apad=whole_dur=1.50000,atrim=end=1.50000[a0]", f)


if __name__ == "__main__":
    unittest.main()
