#!/usr/bin/env python3
"""Sunetele repo-ului, generate de noi din formule (ffmpeg aevalsrc), deci fără nicio licență de altcineva.

    python3 unelte/sunete.py            rescrie sunete/*.wav
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RADACINA = Path(__file__).resolve().parents[1]
SUNETE = {   # nume: (expresia semnalului, durata în secunde, vârful în dB)
    # după setul acceptat de Filip în 4 runde: joase și scurte, fără whoosh și fără clinchete înalte, la vârf −16…−21 dB
    "boom": ("sin(2*PI*(50+25*exp(-20*t))*t)*exp(-7*t)", 0.6, -16.0),
    "knock": ("sin(2*PI*(75+50*exp(-20*t))*t)*exp(-28*t)", 0.2, -17.0),
    "thump": ("sin(2*PI*(50+175*exp(-60*t))*t)*exp(-22*t)", 0.25, -21.0),
    "tok": ("sin(2*PI*(260+90*exp(-45*t))*t)*exp(-32*t)", 0.16, -19.0),   # al treilea sunet de card, ca lemnul: mai sus decât knock, tot scurt
    "pop": ("sin(2*PI*1040*t)*(1-exp(-400*t))*exp(-20*t)", 0.12, -21.0),
    "click": ("sin(2*PI*750*t)*exp(-600*t)", 0.14, -21.0),
    "tick": ("sin(2*PI*3500*t)*exp(-120*t)", 0.05, -26.0),
}


def _varf(f: Path) -> float:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(f), "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return float(r.stderr.split("max_volume:")[1].split("dB")[0])


def genereaza(dosar: Path) -> list[Path]:
    dosar.mkdir(parents=True, exist_ok=True)
    out = []
    for nume, (expr, d, varf) in SUNETE.items():
        brut, f = dosar / f"{nume}.brut.wav", dosar / f"{nume}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d={d}",
                        "-ac", "1", "-c:a", "pcm_f32le", str(brut)], check=True)
        castig = varf - _varf(brut)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(brut),
                        "-af", f"volume={castig:.2f}dB,afade=t=out:st={d - 0.02:.3f}:d=0.02",   # la vârful cerut, fără clic la capăt
                        "-ac", "1", "-c:a", "pcm_s16le", str(f)], check=True)
        brut.unlink()
        out.append(f)
    return out

if __name__ == "__main__":
    print("\n".join(str(p) for p in genereaza(RADACINA / "sunete")))
    sys.exit(0)
