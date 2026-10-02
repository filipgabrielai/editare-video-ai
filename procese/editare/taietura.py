#!/usr/bin/env python3
"""Tăietura reelului, exactă pe cadre, dintr-o singură encodare.

    python3 procese/editare/taietura.py proiecte/<slug> [--filmare 16:9]

bucati.json (scris când alegi dublele): [{"dubla": "IMG_1544_03", "de_la": null, "pana_la": "aplicație#2"}, ...]
de_la / pana_la: primul / ultimul cuvânt păstrat; „text#n” = a n-a apariție, „text@ultimul” = ultima; null = de la primul /
până la ultimul cuvânt al dublei; "coada": 0.1 = secunde în plus la capăt, când omul spune că finalul unui cuvânt nu se aude.
O bucată care continuă fraza (începe cu „și”, sau are "strans": true) se lipește de cea dinainte fără pauză; "strans": false o
lasă cu pauza dintre fraze. Ultima bucată ține 0,25 s din filmare după ultimul cuvânt ("coada": 0 o scoate).
Capetele se pun pe sunet (măsurat pe wav-ul de 16 kHz): înapoi până sub −50 dB, cu 0,02 s înainte și 0,03 s după, iar din
coada de sub −40 dB intră cel mult 0,08 s (pauza la tăietură iese de 0,06–0,10 s, ritmul care sună natural), fără să intre în
cuvântul vecin. Fiecare bucată are intrarea ei (cu -ss), trece prin fps=60 și e
tăiată la numărul exact de cadre: clipurile de telefon au ~59,97 fps, iar tăiatul pe timpi pierdea sau adăuga un cadru.
Filmarea iese la formatul cerut cu --filmare (implicit 9:16): clipul umple cadrul și se decupează, nu se deformează; dacă
orientarea lui e alta, tăietura o spune. Filtrul pe față din preferințe (brand/brand.json) se aplică aici, pe toată imaginea,
inclusiv pe înregistrările de ecran.

Iese: taiat.mp4, voce.wav, taieturi.json, transcript.json (cuvintele pe timpul reelului).
"""
from __future__ import annotations

import array
import json
import math
import re
import subprocess
import sys
import unicodedata
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from procese.editare import duble  # noqa: E402
from unelte import brand, formate, platforma, proiect  # noqa: E402

FPS = 60
PRAG = -50.0
PAD_IN, PAD_OUT = 0.02, 0.03    # măsurate pe varianta postată de Filip a reelului din 1 oct (îmbinările pe care nu le-a mai atins)
COADA_MAX = 0.08                # cât intră din sunetul de sub −40 dB de după ultimul cuvânt (ecou, respirație)
PAS = 0.005
VOCE = -40.0                                  # peste asta e vorbire, pe ferestre de 10 ms la 16 kHz
COADA_STRANS, DEBUT_STRANS = -32.0, -42.0     # măsurate pe ce a strâns Filip de mână în reelurile postate (1 oct 2026)
COADA_FINAL = 0.25                            # cât rămâne omul pe ecran după ultimul cuvânt, cu gura închisă


def norm_cuvant(t: str) -> str:
    return t.strip(".,?!;:-–—„”\"'…").lower()


def idx(ws: list[dict], spec: str, de_la: int = 0) -> int:
    """Indexul cuvântului cerut: „text”, „text#n” (a n-a apariție) sau „text@ultimul”."""
    if spec.endswith("@ultimul"):
        t, n = spec[:-len("@ultimul")], None
    elif "#" in spec:
        t, nr = spec.rsplit("#", 1)
        n = int(nr)
    else:
        t, n = spec, 1
    hits = [i for i in range(de_la, len(ws)) if norm_cuvant(ws[i]["text"]).startswith(norm_cuvant(t))]
    if not hits or (n is not None and n > len(hits)):
        raise SystemExit(f"Cuvântul „{spec}” nu e în dublă. Cuvintele ei: {' '.join(w['text'] for w in ws)}")
    return hits[-1] if n is None else hits[n - 1]


def rms_db(raw: Path) -> list[float]:
    """Nivelul pe fișierul de 8 kHz: îl folosește cuvinte.py, ca să știe de unde trimite dubla la Whisper."""
    a = array.array("f")
    a.frombytes(raw.read_bytes())
    w = int(8000 * PAS)
    return [20 * math.log10(math.sqrt(sum(x * x for x in a[i:i + w]) / w) + 1e-9) for i in range(0, len(a) - w, w)]


def prag(rms: list[float]) -> float:
    """Pragul de sunet al clipului: −50 dB în liniște (ca la Filip), dar peste zgomotul camerei (ventilator, stradă), altfel tot
    zgomotul e „vorbire” și pauza de la tăietură crește de la 0,06–0,10 s la ~0,5 s. Plafonat la −38 dB, pragul dublelor."""
    if not rms:
        return PRAG
    podea = sorted(rms)[len(rms) // 10]
    return max(PRAG, min(podea + 10, -38.0))


def fara_semne(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in t if unicodedata.category(c) != "Mn"))


def rms_wav(wav: Path, pas: float) -> list[float]:
    """Nivelul pe ferestre de `pas` secunde, din wav-ul de 16 kHz al dublelor. Capetele tăieturii se măsoară aici, nu pe
    fișierul de 8 kHz: „ș” și „s” au energia peste 4 kHz și acolo nu se văd."""
    with wave.open(str(wav), "rb") as w:
        n = round(w.getframerate() * pas)
        a = array.array("h")
        a.frombytes(w.readframes(w.getnframes()))
    if sys.byteorder == "big":
        a.byteswap()
    return [20 * math.log10(math.sqrt(sum(x * x for x in a[i:i + n]) / n) / 32768 + 1e-9) for i in range(0, len(a) - n, n)]


def rms10_db(wav: Path) -> list[float]:
    """Nivelul pe ferestre de 10 ms: pentru îmbinările strânse și pentru falsele starturi."""
    return rms_wav(wav, 0.01)


def sustinut(rms: list[float], k: int, prag_db: float, inapoi: bool = False) -> bool:
    """Sunet care ține (cel puțin 3 din 6 ferestre de 5 ms peste prag), nu un clic de buze sau de microfon de 5–10 ms."""
    fereastra = rms[max(0, k - 5):k + 1] if inapoi else rms[k:k + 6]
    return rms[k] > prag_db and sum(x > prag_db for x in fereastra) >= 3


def sfarsit_sunet(rms: list[float], k: int, prag_db: float) -> int:
    """Primul index de după sunetul care începe la k, după care urmează cel puțin 0,15 s de liniște."""
    j = k
    while j < len(rms) and any(x > prag_db for x in rms[j:j + 30]):
        j += 1
    return j


def debut(rms: list[float], i_s: int, i_e: int, prag_db: float, de_la: int = 0) -> int:
    """Indexul unde începe vorbirea din jurul primului cuvânt (Whisper îl pune cu până la ~150 ms după și ~0,4 s înainte de
    sunet). Un sunet scurt (sub 0,12 s) și slab (cu 15 dB sub vorbire), urmat de liniște, e respirație sau buze, nu vorbire.
    Căutarea pornește cel mai devreme de la `de_la` (după cuvântul anterior): altfel găsea cuvântul anterior și bucata pornea
    în coada lui."""
    varf = max(rms[i_s:i_e + 1], default=0.0)
    k = max(0, i_s - 70, de_la)
    while k < min(len(rms), i_s + 120):
        if sustinut(rms, k, prag_db):
            sf = sfarsit_sunet(rms, k, prag_db)
            if sf - k < 24 and max(rms[k:sf]) < varf - 15:
                k = sf
                continue
            return k
        k += 1
    return i_s


def capete_sunet(rms: list[float], s: float, e: float, lim_s: float, lim_e: float, prag_db: float = PRAG,
                 coada_max: float | None = COADA_MAX) -> tuple[float, float]:
    """Unde începe și unde se termină sunetul bucății, în secunde, fără pad și fără să intre în cuvintele vecine. Din sunetul de
    sub −40 dB de după ultimul cuvânt intră cel mult `coada_max` (None = toată coada, până sub prag)."""
    i_s, i_e = int(s / PAS), int(e / PAS)
    on = max(debut(rms, i_s, i_e, prag_db, int(lim_s / PAS)), int(lim_s / PAS))
    off, tacere = i_e, 0
    for k in range(max(0, i_e - 30), min(len(rms), i_e + 24, int(lim_e / PAS))):
        if sustinut(rms, k, prag_db, inapoi=True):
            off, tacere = k, 0
        else:
            tacere += 1
            if tacere >= 50 and k > i_e:
                break
    voce = next((k for k in range(min(off, len(rms) - 1), on, -1) if rms[k] > VOCE and rms[k - 1] > VOCE), None)
    if voce is not None and coada_max is not None:   # Whisper pune sfârșitul cuvântului și cu 0,1 s mai târziu: capătul mergea pe tot ecoul
        off = min(off, voce + round(coada_max / PAS))
    return on * PAS, off * PAS


def capete(rms: list[float], s: float, e: float, lim_s: float, lim_e: float, prag_db: float = PRAG) -> tuple[float, float]:
    """Începutul și sfârșitul bucății, pe sunet (peste prag), cu pad-ul, fără să treacă de cuvintele vecine, pe grila de cadre."""
    on, sf = capete_sunet(rms, s, e, lim_s, lim_e, prag_db)
    a0 = round(max(0.0, on - PAD_IN) * FPS) / FPS
    a1 = round(min(sf + PAD_OUT, lim_e) * FPS) / FPS
    return a0, a1


def e_strans(b: dict, primul_cuvant: str, k: int) -> bool:
    """Bucata continuă fraza celei dinainte și se lipește aproape fără pauză: cerut în bucati.json ("strans": true / false),
    altfel când începe cu „și”. Între fraze rămâne pauza de 0,06–0,10 s."""
    if k == 0:
        return False
    if "strans" in b:
        return bool(b["strans"])
    return fara_semne(primul_cuvant) == "si"


def debut_strans(r10: list[float], on: float, e: float, lim_s: float) -> float:
    """Începutul strâns: primul sunet care ține peste −42 dB în cele 0,12 s dinaintea vocii, fără pad."""
    k0 = max(0, int((on - 0.05) / 0.01))
    v0 = next((k for k in range(k0, min(len(r10) - 1, int(e / 0.01))) if r10[k] > VOCE and r10[k + 1] > VOCE), None)
    if v0 is None:
        return max(on, lim_s)
    k = max(0, v0 - 12)
    while k < v0 and not (r10[k] > DEBUT_STRANS and r10[k + 1] > DEBUT_STRANS):
        k += 1
    return max(k * 0.01, lim_s)


def sfarsit_strans(r10: list[float], on: float, sf: float) -> float:
    """Sfârșitul strâns: ultima fereastră peste −32 dB, plus 0,04 s. Niciodată după sfârșitul normal."""
    k = min(len(r10) - 1, int(sf / 0.01))
    while k > int(on / 0.01) and r10[k] <= COADA_STRANS:
        k -= 1
    return min(sf, (k + 1) * 0.01 + 0.04)


def _capat(text: str, k: int) -> str:
    cuv = text.split()
    return fara_semne(cuv[k]) if cuv else ""


def capete_bucata(on: float, sf: float, lim_s: float, lim_e: float, r10: list[float] | None, strans_in: bool, strans_out: bool,
                  asculta=None, ultim: str = "", prim: str = "", sf_lung: float | None = None) -> tuple[float, float, bool]:
    """Capetele bucății pe grila de cadre. Normal: 0,02 s înainte de sunet și 0,03 s după. Strâns: pe sunet, fără pad.
    Sfârșitul se alege de la cel mai strâns la cel mai sigur: strâns (dacă bucata următoare continuă fraza), cu coada limitată
    (sf), cu toată coada (sf_lung). Un sfârșit care scurtează bucata se ascultă (asculta(a, b) întoarce textul): sfârșitul
    strâns mânca „-ri” din „videoclipuri”, iar coada limitată mânca „-uri” din „prompturi”. Rămâne doar dacă ultimul cuvânt
    se aude ca în transcript, sau ca în bucata cu toată coada și terminat la fel ca în transcript (Whisper aude „clode” pentru
    „Claude” și acolo: nu s-a pierdut nimic; „prompt” pentru „prompturi” nu dovedește nimic, deci rămâne toată coada).
    Începutul strâns sărea peste un „ș” slab („Și dacă vrei” se auzea „Dacă vrei”): dacă primul cuvânt nu se mai aude, bucata
    pornește pe sunetul găsit de tăietura normală, tot fără pad. Întoarce și dacă sfârșitul a rămas strâns."""
    def cadru(t: float) -> float:
        return round(min(t, lim_e) * FPS) / FPS

    t0 = debut_strans(r10, on, sf, lim_s) if strans_in else max(0.0, on - PAD_IN)
    a0 = round(t0 * FPS) / FPS
    scurt, sigur = cadru(sf + PAD_OUT), cadru(max(sf, sf_lung or sf) + PAD_OUT)
    variante = [(cadru(sfarsit_strans(r10, on, sf)), True)] if strans_out else []
    variante += [(scurt, False)] if scurt < sigur else []
    variante.append((sigur, False))
    if not asculta:
        return a0, variante[0][0], variante[0][1]
    ales, auzit, martor = variante[-1], None, None
    for a1, strans in variante[:-1]:
        text = asculta(a0, a1)
        auzit = text if auzit is None else auzit
        u, asteptat = _capat(text, -1), fara_semne(ultim)
        if u and u != asteptat:
            martor = _capat(asculta(a0, sigur), -1) if martor is None else martor
        if u and (u == asteptat or (u == martor and u[-2:] == asteptat[-2:])):
            ales = (a1, strans)
            break
    if strans_in and prim:
        auzit = asculta(a0, min(sigur, a0 + 2.0)) if auzit is None else auzit
        if _capat(auzit, 0) != fara_semne(prim):
            a0 = round(max(on, lim_s) * FPS) / FPS
    return a0, ales[0], ales[1]


class Ascultari:
    """Ce a auzit Whisper la capetele bucăților, ținut minte în lucru/ascultari.json. Fiecare ascultare e un whisper-cli pornit
    de la zero (modelul de 1,6 GB): la re-tăiere, capetele bucăților neschimbate revin exact la fel și nu se mai ascultă. Ce
    n-a mers (text gol) nu se ține minte."""

    def __init__(self, fisier: Path, model: str, limba: str) -> None:
        self.fisier, self.prefix = fisier, f"{model}|{limba}"
        self.noi = self.din_cache = 0
        try:
            self.date = json.loads(fisier.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.date = {}

    def asculta(self, clip: str, a: float, b: float, transcrie) -> str:
        cheie = f"{self.prefix}|{clip}|{a:.3f}|{b:.3f}"
        if cheie in self.date:
            self.din_cache += 1
            return self.date[cheie]
        self.noi += 1
        text = transcrie(a, b)
        if text:
            self.date[cheie] = text
        return text

    def salveaza(self) -> None:
        self.fisier.write_text(json.dumps(self.date, ensure_ascii=False, indent=1), encoding="utf-8")


def coada_bucatii(b: dict, ultima: bool) -> float:
    """Secundele în plus la capăt: "coada" din bucati.json; la ultima bucată, implicit 0,25 s din filmare după ultimul cuvânt
    (fără ele videoul se termină pe ultima silabă și pare tăiat). Nu e liniște pentru animații și nu e cadru înghețat."""
    return b.get("coada", COADA_FINAL if ultima else 0.0)


def cu_coada(a1: float, coada: float, lim_e: float) -> float:
    """Capătul lungit cu „coada” din bucati.json (când omul spune că nu se aude finalul unui cuvânt), pe grila de cadre, fără
    să treacă de cuvântul următor din dublă."""
    if not coada:
        return a1
    return math.floor(min(a1 + coada, lim_e) * FPS + 1e-6) / FPS


def orientare(clip: Path) -> tuple[int, int, int]:
    """Lățimea, înălțimea și rotația clipului, cum le dă ffprobe."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:stream_side_data=rotation", "-of", "json", str(clip)],
                       capture_output=True, text=True, check=True)
    s = json.loads(r.stdout)["streams"][0]
    rot = next((int(float(x["rotation"])) for x in s.get("side_data_list", []) if "rotation" in x), 0)
    return s["width"], s["height"], rot


def avertisment_orientare(nume: str, orizontal: bool, filmare: str) -> str:
    if orizontal and filmare == "9:16":
        return (f"atenție: {nume} e filmat pe orizontală și îl decupez la 9:16 (rămâne mijlocul). "
                "Pentru un video orizontal, refă tăietura cu --filmare 16:9.")
    if not orizontal and filmare == "16:9":
        return f"atenție: {nume} e filmat pe verticală; la 16:9 rămâne doar o bandă din mijlocul lui."
    return ""


def filtre(seg: list[tuple[str, float, float]], s0s: list[float], extra: str = "", filmare: str = formate.IMPLICIT) -> str:
    """Lanțul ffmpeg al tăieturii; `extra` (filtrul pe față din preferințe) se pune după decupajul la formatul filmării."""
    J = 1 / (2 * FPS)
    w, h = formate.dimensiuni(filmare)
    parti = []
    for k, (_, a0, a1) in enumerate(seg):
        r0, r1 = a0 - s0s[k], a1 - s0s[k]
        n = round((a1 - a0) * FPS)
        parti.append(f"[{k}:v:0]trim={max(0.0, r0 - J):.5f}:{r1 + 4 * J:.5f},setpts=PTS-STARTPTS,fps={FPS},trim=end_frame={n},"
                     f"setpts=PTS-STARTPTS,scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={w}:{h},setsar=1"
                     f"{',' + extra if extra else ''}[v{k}];"
                     f"[{k}:a:0]atrim={r0:.5f}:{r1:.5f},asetpts=PTS-STARTPTS,aresample=48000,"
                     f"apad=whole_dur={n / FPS:.5f},atrim=end={n / FPS:.5f}[a{k}]")
    parti.append("".join(f"[v{k}][a{k}]" for k in range(len(seg))) + f"concat=n={len(seg)}:v=1:a=1[v][a]")
    return ";".join(parti)


def main(argv: list[str] | None = None) -> int:
    platforma.iesire_utf8()
    argv = list(sys.argv[1:] if argv is None else argv)
    filmare = formate.IMPLICIT
    if "--filmare" in argv:
        k = argv.index("--filmare")
        filmare = argv[k + 1] if k + 1 < len(argv) else ""
        del argv[k:k + 2]
    if not argv:
        raise SystemExit("Folosire: taietura.py proiecte/<slug> [--filmare 16:9]")
    formate.dimensiuni(filmare)
    dosar = Path(argv[0])
    with open(dosar / "bucati.json", encoding="utf-8") as f:
        bucati = json.load(f)
    with open(dosar / "duble.json", encoding="utf-8") as f:
        toate = {d["dubla"]: d for d in json.load(f)}
    surse = proiect.clipuri(dosar)
    for nume in sorted({toate[x["dubla"]]["clip"] for x in bucati}):
        lat, inalt, rot = orientare(surse[nume])
        if (m := avertisment_orientare(nume, formate.e_orizontal(lat, inalt, rot), filmare)):
            print(m)
    b = brand.incarca()
    extra = brand.filtru_fata(b)
    if extra:
        print(f"filtru pe față: {b['preferinte']['filtru_fata']}")
    lb = brand.limba(b)
    plan, rms_cache, r10_cache, dur_cache = [], {}, {}, {}
    for k, bc in enumerate(bucati):
        d = toate[bc["dubla"]]
        with open(dosar / "transcripte" / f"{bc['dubla']}.json", encoding="utf-8") as f:
            tr = json.load(f)
        ws, off = tr["words"], tr["decalaj"]
        if not ws:
            raise SystemExit(f"Dubla {bc['dubla']} nu are cuvinte transcrise.")
        i0 = 0 if not bc.get("de_la") else idx(ws, bc["de_la"])
        i1 = len(ws) - 1 if not bc.get("pana_la") else idx(ws, bc["pana_la"], i0)
        clip = d["clip"]
        wav = dosar / "lucru" / f"{clip}.wav"
        if clip not in rms_cache:
            r = rms_wav(wav, PAS)
            rms_cache[clip] = (r, prag(r))
            dur_cache[clip] = duble.durata(wav)
        s, e = ws[i0]["start"] + off, ws[i1]["end"] + off
        lim_s = ws[i0 - 1]["end"] + off + 0.02 if i0 > 0 else tr.get("de_la_timp", 0.0)
        lim_e = ws[i1 + 1]["start"] + off - 0.02 if i1 + 1 < len(ws) else dur_cache[clip]
        on, sf = capete_sunet(rms_cache[clip][0], s, e, lim_s, lim_e, rms_cache[clip][1])
        sf_lung = capete_sunet(rms_cache[clip][0], s, e, lim_s, lim_e, rms_cache[clip][1], coada_max=None)[1]
        plan.append({"b": bc, "clip": clip, "wav": wav, "on": on, "sf": sf, "sf_lung": sf_lung, "lim_s": lim_s, "lim_e": lim_e, "off": off,
                     "ws": ws[i0:i1 + 1], "strans": e_strans(bc, ws[i0]["text"], k)})

    ascultari = Ascultari(dosar / "lucru" / "ascultari.json", platforma.model_whisper().name, lb)

    def ascultator(clip: str, wav: Path):
        def transcrie(a: float, t: float) -> str:
            try:
                return duble.transcrie(wav, a, t, dosar / "lucru", lb)
            except SystemExit:
                return ""
        return lambda a, t: ascultari.asculta(clip, a, t, transcrie)

    seg, cuvinte_reel, acc = [], [], 0.0
    for k, p in enumerate(plan):
        strans_in = p["strans"]
        strans_out = k + 1 < len(plan) and plan[k + 1]["strans"]
        r10 = None
        if strans_in or strans_out:
            if p["clip"] not in r10_cache:
                r10_cache[p["clip"]] = rms10_db(p["wav"])
            r10 = r10_cache[p["clip"]]
        a0, a1, a_ramas = capete_bucata(p["on"], p["sf"], p["lim_s"], p["lim_e"], r10, strans_in, strans_out,
                                        ascultator(p["clip"], p["wav"]), p["ws"][-1]["text"], p["ws"][0]["text"], p["sf_lung"])
        if strans_out and not a_ramas:
            print(f"   {p['b']['dubla']}: sfârșitul strâns mânca ultimul cuvânt („{p['ws'][-1]['text']}”), rămâne cel normal")
        a1 = cu_coada(a1, coada_bucatii(p["b"], k == len(plan) - 1), p["lim_e"])
        seg.append((p["clip"], a0, a1))
        for w in p["ws"]:
            cuvinte_reel.append({"text": w["text"], "start": round(w["start"] + p["off"] - a0 + acc, 3),
                                 "end": round(w["end"] + p["off"] - a0 + acc, 3), "type": "word"})
        acc += a1 - a0
        semn = ("[" if strans_in else " ") + ("]" if a_ramas else " ")
        print(f"{p['b']['dubla']:14s} {a0:7.3f}-{a1:7.3f} ({a1 - a0:5.2f} s) {semn} | {' '.join(w['text'] for w in p['ws'])}", flush=True)
    ascultari.salveaza()
    if ascultari.noi or ascultari.din_cache:
        print(f"capete ascultate cu Whisper: {ascultari.noi} (alte {ascultari.din_cache} știute de la tăietura dinainte)", flush=True)
    cmd = ["ffmpeg", "-v", "error", "-y"]
    s0s = []
    for c, a0, a1 in seg:
        s0 = max(0.0, a0 - 1.0)
        s0s.append(s0)
        cmd += ["-ss", f"{s0:.3f}", "-t", f"{a1 - s0 + 1.0:.3f}", "-i", str(surse[c])]
    cmd += ["-filter_complex", filtre(seg, s0s, extra, filmare), "-map", "[v]", "-map", "[a]", "-r", str(FPS), "-c:v", "libx264", "-preset", "fast",
            "-crf", "14", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", str(dosar / "taiat.mp4")]
    subprocess.run(cmd, check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(dosar / "taiat.mp4"), "-vn", "-ac", "1", "-ar", "48000",
                    str(dosar / "voce.wav")], check=True)
    taieturi, t = [], 0.0
    for _, a0, a1 in seg[:-1]:
        t += a1 - a0
        taieturi.append(round(t, 3))
    with open(dosar / "taieturi.json", "w", encoding="utf-8") as f:
        json.dump({"taieturi": taieturi, "bucati": seg, "filmare": filmare}, f, indent=1)
    with open(dosar / "transcript.json", "w", encoding="utf-8") as f:
        json.dump({"words": cuvinte_reel}, f, ensure_ascii=False, indent=1)
    print(f"taiat.mp4: {acc:.2f} s, {len(taieturi)} tăieturi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
