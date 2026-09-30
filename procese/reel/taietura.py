#!/usr/bin/env python3
"""Tăietura reelului, exactă pe cadre, dintr-o singură encodare.

    python3 procese/reel/taietura.py proiecte/<slug>

bucati.json (scris când alegi dublele): [{"dubla": "IMG_1544_03", "de_la": null, "pana_la": "aplicație#2"}, ...]
de_la / pana_la: primul / ultimul cuvânt păstrat; „text#n” = a n-a apariție, „text@ultimul” = ultima; null = de la primul /
până la ultimul cuvânt al dublei; "coada": 0.1 = secunde în plus la capăt, când omul spune că finalul unui cuvânt nu se aude.
Capetele se pun pe sunet: înapoi până sub −50 dB, cu 0,05 s înainte și 0,02 s după (pauza la tăietură iese de 0,06–0,10 s,
ritmul care sună natural), fără să intre în cuvântul vecin. Fiecare bucată are intrarea ei (cu -ss), trece prin fps=60 și e
tăiată la numărul exact de cadre: clipurile de telefon au ~59,97 fps, iar tăiatul pe timpi pierdea sau adăuga un cadru.
Clipurile în peisaj se decupează la 9:16, nu se deformează.

Iese: taiat.mp4, voce.wav, taieturi.json, transcript.json (cuvintele pe timpul reelului).
"""
from __future__ import annotations

import array
import json
import math
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from unelte import platforma, proiect  # noqa: E402

FPS = 60
PRAG = -50.0
PAD_IN, PAD_OUT = 0.05, 0.02
PAS = 0.005


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


def debut(rms: list[float], i_s: int, i_e: int, prag_db: float) -> int:
    """Indexul unde începe vorbirea din jurul primului cuvânt (Whisper îl pune cu până la ~150 ms după și ~0,4 s înainte de
    sunet). Un sunet scurt (sub 0,12 s) și slab (cu 15 dB sub vorbire), urmat de liniște, e respirație sau buze, nu vorbire."""
    varf = max(rms[i_s:i_e + 1], default=0.0)
    k = max(0, i_s - 70)
    while k < min(len(rms), i_s + 120):
        if sustinut(rms, k, prag_db):
            sf = sfarsit_sunet(rms, k, prag_db)
            if sf - k < 24 and max(rms[k:sf]) < varf - 15:
                k = sf
                continue
            return k
        k += 1
    return i_s


def capete(rms: list[float], s: float, e: float, lim_s: float, lim_e: float, prag_db: float = PRAG) -> tuple[float, float]:
    """Începutul și sfârșitul bucății, pe sunet (peste prag), cu pad-ul, fără să treacă de cuvintele vecine, pe grila de cadre."""
    i_s, i_e = int(s / PAS), int(e / PAS)
    on = max(debut(rms, i_s, i_e, prag_db), int(lim_s / PAS))
    off, tacere = i_e, 0
    for k in range(max(0, i_e - 30), min(len(rms), i_e + 24, int(lim_e / PAS))):
        if sustinut(rms, k, prag_db, inapoi=True):
            off, tacere = k, 0
        else:
            tacere += 1
            if tacere >= 50 and k > i_e:
                break
    a0 = round(max(0.0, on * PAS - PAD_IN) * FPS) / FPS
    a1 = round(min(off * PAS + PAD_OUT, lim_e) * FPS) / FPS
    return a0, a1


def cu_coada(a1: float, coada: float, lim_e: float) -> float:
    """Capătul lungit cu „coada” din bucati.json (când omul spune că nu se aude finalul unui cuvânt), pe grila de cadre, fără
    să treacă de cuvântul următor din dublă."""
    if not coada:
        return a1
    return math.floor(min(a1 + coada, lim_e) * FPS + 1e-6) / FPS


def filtre(seg: list[tuple[str, float, float]], s0s: list[float]) -> str:
    J = 1 / (2 * FPS)
    parti = []
    for k, (_, a0, a1) in enumerate(seg):
        r0, r1 = a0 - s0s[k], a1 - s0s[k]
        n = round((a1 - a0) * FPS)
        parti.append(f"[{k}:v:0]trim={max(0.0, r0 - J):.5f}:{r1 + 4 * J:.5f},setpts=PTS-STARTPTS,fps={FPS},trim=end_frame={n},"
                     f"setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1[v{k}];"
                     f"[{k}:a:0]atrim={r0:.5f}:{r1:.5f},asetpts=PTS-STARTPTS,aresample=48000[a{k}]")
    parti.append("".join(f"[v{k}][a{k}]" for k in range(len(seg))) + f"concat=n={len(seg)}:v=1:a=1[v][a]")
    return ";".join(parti)


def main(argv: list[str] | None = None) -> int:
    platforma.iesire_utf8()
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        raise SystemExit("Folosire: taietura.py proiecte/<slug>")
    dosar = Path(argv[0])
    with open(dosar / "bucati.json", encoding="utf-8") as f:
        bucati = json.load(f)
    with open(dosar / "duble.json", encoding="utf-8") as f:
        duble = {d["dubla"]: d for d in json.load(f)}
    surse = proiect.clipuri(dosar)
    seg, cuvinte_reel, acc, rms_cache = [], [], 0.0, {}
    for b in bucati:
        d = duble[b["dubla"]]
        with open(dosar / "transcripte" / f"{b['dubla']}.json", encoding="utf-8") as f:
            tr = json.load(f)
        ws, off = tr["words"], tr["decalaj"]
        if not ws:
            raise SystemExit(f"Dubla {b['dubla']} nu are cuvinte transcrise.")
        i0 = 0 if not b.get("de_la") else idx(ws, b["de_la"])
        i1 = len(ws) - 1 if not b.get("pana_la") else idx(ws, b["pana_la"], i0)
        s, e = ws[i0]["start"] + off, ws[i1]["end"] + off
        lim_s = ws[i0 - 1]["end"] + off + 0.02 if i0 > 0 else 0.0
        lim_e = ws[i1 + 1]["start"] + off - 0.02 if i1 + 1 < len(ws) else 1e9
        if d["clip"] not in rms_cache:
            r = rms_db(dosar / "lucru" / f"{d['clip']}.raw")
            rms_cache[d["clip"]] = (r, prag(r))
        rms, prag_clip = rms_cache[d["clip"]]
        a0, a1 = capete(rms, s, e, lim_s, lim_e, prag_clip)
        a1 = cu_coada(a1, b.get("coada", 0.0), lim_e)
        seg.append((d["clip"], a0, a1))
        for w in ws[i0:i1 + 1]:
            cuvinte_reel.append({"text": w["text"], "start": round(w["start"] + off - a0 + acc, 3),
                                 "end": round(w["end"] + off - a0 + acc, 3), "type": "word"})
        acc += a1 - a0
        print(f"{b['dubla']:14s} {a0:7.3f}-{a1:7.3f} ({a1 - a0:5.2f} s) | {' '.join(w['text'] for w in ws[i0:i1 + 1])}", flush=True)
    cmd = ["ffmpeg", "-v", "error", "-y"]
    s0s = []
    for c, a0, a1 in seg:
        s0 = max(0.0, a0 - 1.0)
        s0s.append(s0)
        cmd += ["-ss", f"{s0:.3f}", "-t", f"{a1 - s0 + 1.0:.3f}", "-i", str(surse[c])]
    cmd += ["-filter_complex", filtre(seg, s0s), "-map", "[v]", "-map", "[a]", "-r", str(FPS), "-c:v", "libx264", "-preset", "fast",
            "-crf", "14", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", str(dosar / "taiat.mp4")]
    subprocess.run(cmd, check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(dosar / "taiat.mp4"), "-vn", "-ac", "1", "-ar", "48000",
                    str(dosar / "voce.wav")], check=True)
    taieturi, t = [], 0.0
    for _, a0, a1 in seg[:-1]:
        t += a1 - a0
        taieturi.append(round(t, 3))
    with open(dosar / "taieturi.json", "w", encoding="utf-8") as f:
        json.dump({"taieturi": taieturi, "bucati": seg}, f, indent=1)
    with open(dosar / "transcript.json", "w", encoding="utf-8") as f:
        json.dump({"words": cuvinte_reel}, f, ensure_ascii=False, indent=1)
    print(f"taiat.mp4: {acc:.2f} s, {len(taieturi)} tăieturi")
    return 0


if __name__ == "__main__":
    sys.exit(main())
