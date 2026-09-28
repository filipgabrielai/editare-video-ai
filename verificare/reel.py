#!/usr/bin/env python3
"""Verificarea unui reel randat: cadre negre, vocea față de voce.wav (în mai multe puncte), tăieturile din imagine față de cele
din sunet, loudness. Un draft care pică aici nu se anunță ca gata.

    python3 verificare/reel.py proiecte/<slug>/<fișierul randat>.mp4
"""
from __future__ import annotations

import array
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from procese.reel import sunet  # noqa: E402
from unelte import platforma  # noqa: E402

SR = 8000
LAG_MAX_MS, CORELATIE_MIN, CORELATIE_CLARA, LUFS_TINTA, LUFS_TOL = 10, 0.5, 0.7, -14.0, 0.5
_AUDIO: dict[str, array.array] = {}


@dataclass
class Rezultat:
    negre: list
    lag: list
    taieturi: list
    lufs: float
    fps: int = 60
    durata: float = 0.0
    durata_asteptata: float = 0.0
    ok: bool = True
    probleme: list = field(default_factory=list)


def toleranta_taietura_ms(fps: int) -> float:
    """Jumătate de cadru (plus 1 ms de rotunjire): o tăietură cu un cadru pe lângă pică, iar la 30 fps o tăietură de pe grila
    de 60 fps, care cade între două cadre, trece."""
    return 500 / fps + 1


def audio(f: Path) -> array.array:
    """Tot sunetul fișierului, decodat o singură dată (cu -ss în AAC ferestrele de la coadă cădeau cu până la 33 ms)."""
    if str(f) not in _AUDIO:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                             capture_output=True, check=True).stdout
        a = array.array("f")
        a.frombytes(raw)
        _AUDIO[str(f)] = a
    return _AUDIO[str(f)]


def anvelopa(a: array.array, t0: float, d: float) -> list[float]:
    x = a[int(t0 * SR):int((t0 + d) * SR)]
    w = SR // 100
    e = [math.sqrt(sum(v * v for v in x[i:i + w]) / w) for i in range(0, len(x) - w, w)]
    m = sum(e) / len(e) if e else 0.0
    return [v - m for v in e]


def xcorr(a: list[float], b: list[float], maxlag: int = 20) -> tuple[int, float]:
    best = (0, -2.0)
    na = math.sqrt(sum(x * x for x in a[maxlag:len(a) - maxlag])) or 1e-9
    nb = math.sqrt(sum(x * x for x in b)) or 1e-9
    for lag in range(-maxlag, maxlag + 1):
        s = sum(a[i] * b[i + lag] for i in range(maxlag, len(a) - maxlag) if 0 <= i + lag < len(b))
        c = s / (na * nb)
        if c > best[1]:
            best = (lag, c)
    return best


def puncte(cuts: list[float], dur: float) -> list[float]:
    p = [1.0] + [c - 1.2 for c in cuts[:3]] + [c + 0.3 for c in cuts[3:6]] + [dur / 2, dur - 2.5]
    return [max(0.0, min(t, dur - 2.0)) for t in p]


def potriveste(cuts: list[float], sc: list[float]) -> list[tuple[float, float | None, float | None]]:
    out = []
    for c in cuts:
        if not sc:
            out.append((c, None, None))
            continue
        dif, s = min((abs(s - c), s) for s in sc)
        out.append((c, s, dif * 1000))
    return out


def negre(f: Path) -> list[tuple[float, float]]:
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(f), "-vf", "blackdetect=d=0.01:pix_th=0.10", "-an", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)]


def scene(f: Path) -> list[float]:
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(f), "-vf", "select='gt(scene,0.06)',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return [float(x) for x in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def evalueaza(r: Rezultat) -> Rezultat:
    r.probleme = []
    if r.negre:
        r.probleme.append(f"cadre negre la {', '.join(f'{a:.2f}' for a, _ in r.negre)} s")
    # Randarea are și sunetele de card, care nu sunt în voce.wav: un punct cu corelație slabă poate arăta un decalaj fals.
    # Un decalaj real e clar (corelație ≥ 0,7) sau apare în cel puțin două puncte.
    decalate = [(t, lag_ms, c) for t, lag_ms, c in r.lag if c >= CORELATIE_MIN and abs(lag_ms) > LAG_MAX_MS]
    for t, lag_ms, c in decalate:
        if c >= CORELATIE_CLARA or len(decalate) >= 2:
            r.probleme.append(f"vocea decalată cu {lag_ms:+d} ms la {t:.2f} s")
    for c, s, dif in r.taieturi:
        if dif is None or dif > toleranta_taietura_ms(r.fps):
            r.probleme.append(f"tăietura de la {c:.3f} s nu cade pe imagine" + (f" ({dif:.0f} ms)" if dif is not None else ""))
    if r.durata_asteptata and abs(r.durata - r.durata_asteptata) > 1.5 / r.fps:
        r.probleme.append(f"durata {r.durata:.3f} s față de {r.durata_asteptata:.3f} s cât are tăietura")
    if abs(r.lufs - LUFS_TINTA) > LUFS_TOL:
        r.probleme.append(f"loudness {r.lufs:.1f} LUFS (trebuie {LUFS_TINTA:.0f} ± {LUFS_TOL})")
    r.ok = not r.probleme
    return r


def durata_video(f: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def fps_video(f: Path) -> int:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True, check=True)
    a, _, b = r.stdout.strip().partition("/")
    return round(float(a) / float(b or 1))


def verifica(f: Path, voce: Path, cuts: list[float], fps: int = 60, durata_asteptata: float | None = None) -> Rezultat:
    dur = sunet.durata_audio(f)
    lag = []
    for t0 in puncte(cuts, dur):
        l, c = xcorr(anvelopa(audio(f), t0, 2.0), anvelopa(audio(voce), t0, 2.0))
        lag.append((t0, l * 10, c))
    return evalueaza(Rezultat(negre=negre(f), lag=lag, taieturi=potriveste(cuts, scene(f)), lufs=sunet.integrat(f), fps=fps,
                              durata=durata_video(f) if durata_asteptata else 0.0, durata_asteptata=durata_asteptata or 0.0))


def raport(r: Rezultat) -> str:
    linii = [f"cadre negre: {len(r.negre)}"]
    linii += [f"  vocea la {t:6.2f} s: decalaj {l:+4d} ms, corelație {c:.2f}" for t, l, c in r.lag]
    linii += [f"  tăietura {c:6.3f} s: imagine {s if s is not None else '-'}, diferență {'-' if d is None else f'{d:.0f} ms'}" for c, s, d in r.taieturi]
    if r.durata_asteptata:
        linii.append(f"durata: {r.durata:.3f} s (tăietura: {r.durata_asteptata:.3f} s)")
    linii.append(f"loudness: {r.lufs:.1f} LUFS")
    linii.append("TRECE" if r.ok else "NU TRECE: " + "; ".join(r.probleme))
    return "\n".join(linii)


def main(argv: list[str] | None = None) -> int:
    platforma.iesire_utf8()
    argv = sys.argv[1:] if argv is None else argv
    f = Path(argv[0])
    dosar = f.parent
    with open(dosar / "taieturi.json", encoding="utf-8") as fh:
        cuts = json.load(fh)["taieturi"]
    r = verifica(f, dosar / "voce.wav", cuts, fps_video(f), durata_video(dosar / "taiat.mp4"))
    print(raport(r))
    return 0 if r.ok else 1


if __name__ == "__main__":
    sys.exit(main())
