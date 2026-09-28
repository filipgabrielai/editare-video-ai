#!/usr/bin/env python3
"""Vocea la −14 LUFS (true peak −1,5) în două treceri, imaginea copiată.

    python3 procese/reel/sunet.py <intrare.mp4> <iesire.mp4>

Vocea brută e pe la −22 LUFS cu vârfuri de −6 dBTP, deci loudnorm nu poate rămâne liniar și trece singur pe dinamic; la capătul
fișierului golește bufferul (~3 s) decalat. De aceea: 5 s de liniște adăugate, loudnorm, apoi tăiat înapoi exact la durata sunetului.
Pe clipuri scurte (sub ~10 s) loudnorm dinamic rămâne sub țintă (−15,4 în loc de −14 pe 4 s de voce), așa că se măsoară rezultatul
și, dacă e nevoie, se adaugă câștigul care lipsește, cu un limitator la −1,5 dB (compensat, nu mută sunetul) ca vârfurile să nu treacă.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


def json_loudnorm(text: str) -> dict:
    blocuri = re.findall(r"\{[^{}]*\}", text)
    if not blocuri:
        raise SystemExit("ffmpeg nu a întors măsurătoarea de loudness (loudnorm).")
    return json.loads(blocuri[-1])


def parametri(m: dict) -> str:
    return (f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
            f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}")


def _masoara(f: Path, filtru: str) -> dict:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(f), "-af", filtru, "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return json_loudnorm(r.stderr)


def durata_audio(f: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def integrat(f: Path) -> float:
    return float(_masoara(f, "loudnorm=print_format=json")["input_i"])


TINTA, TOLERANTA, LIMITA = -14.0, 0.2, 0.8414   # 0,8414 = −1,5 dBFS


def corectie(lant: str, castig: float) -> str:
    """Lanțul de filtre cu câștigul care lipsește, urmat de limitator (fără auto-nivel, cu întârzierea compensată)."""
    if not castig:
        return lant
    return f"{lant},volume={castig:.2f}dB,alimiter=limit={LIMITA}:level=disabled:latency=1"


def normalizeaza(intrare: Path, iesire: Path) -> float:
    m = _masoara(intrare, "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json")
    d = durata_audio(intrare)
    lant = (f"apad=pad_dur=5,loudnorm=I=-14:TP=-1.5:LRA=11:{parametri(m)}:linear=true,aresample=48000,"
            f"atrim=end={d:.6f},asetpts=PTS-STARTPTS")
    castig = 0.0
    nivel = float(_masoara(intrare, f"{lant},loudnorm=print_format=json")["input_i"])
    for _ in range(4):
        if abs(nivel - TINTA) <= TOLERANTA:
            break
        castig += TINTA - nivel
        nivel = float(_masoara(intrare, f"{corectie(lant, castig)},loudnorm=print_format=json")["input_i"])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(intrare), "-af", corectie(lant, castig),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", str(iesire)], check=True)
    return integrat(iesire)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Folosire: sunet.py <intrare> <iesire>")
    print(f"{normalizeaza(Path(sys.argv[1]), Path(sys.argv[2])):.1f} LUFS")
