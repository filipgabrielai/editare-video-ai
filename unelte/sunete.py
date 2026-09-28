#!/usr/bin/env python3
"""Sunetele repo-ului, generate de noi din formule (ffmpeg aevalsrc), deci fără nicio licență de altcineva.

    python3 unelte/sunete.py            rescrie sunete/*.wav
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RADACINA = Path(__file__).resolve().parents[1]
SUNETE = {   # nume: (expresia semnalului, durata în secunde)
    "boom": ("0.75*sin(2*PI*55*t)*exp(-4*t)+0.2*sin(2*PI*110*t)*exp(-6*t)", 0.9),
    "knock": ("0.65*sin(2*PI*140*t)*exp(-18*t)+0.25*sin(2*PI*320*t)*exp(-40*t)", 0.25),
    "thump": ("0.9*sin(2*PI*90*t)*exp(-12*t)", 0.3),
    "pop": ("0.7*sin(2*PI*(600+900*exp(-30*t))*t)*exp(-25*t)", 0.15),
    "click": ("0.6*sin(2*PI*2000*t)*exp(-80*t)", 0.08),
    "tick": ("0.5*sin(2*PI*3500*t)*exp(-120*t)", 0.05),
}


def genereaza(dosar: Path) -> list[Path]:
    dosar.mkdir(parents=True, exist_ok=True)
    out = []
    for nume, (expr, d) in SUNETE.items():
        f = dosar / f"{nume}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d={d}",
                        "-af", f"afade=t=out:st={d - 0.02:.3f}:d=0.02",   # fără clic la capăt
                        "-ac", "1", "-c:a", "pcm_s16le", str(f)], check=True)
        out.append(f)
    return out


if __name__ == "__main__":
    print("\n".join(str(p) for p in genereaza(RADACINA / "sunete")))
    sys.exit(0)
