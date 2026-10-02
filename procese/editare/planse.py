#!/usr/bin/env python3
"""Planșele de dinainte de randare: cadre la intrarea, mijlocul și ieșirea fiecărui card, cu zonele acoperite de Instagram
marcate cu roșu (sus tabul „Reels”, jos numele și descrierea, în dreapta butoanele). Nimic important nu are voie în roșu.

    python3 procese/editare/planse.py proiecte/<slug>          → proiecte/<slug>/planse/foaie-01.jpg, ...
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from unelte import hyperframes, platforma  # noqa: E402

ZONE = [(0, 0, 1080, 260), (0, 1640, 1080, 280), (950, 1120, 130, 520)]   # x, y, lățime, înălțime


def filtru_zone() -> str:
    return ",".join(f"drawbox=x={x}:y={y}:w={w}:h={h}:color=red@0.28:t=fill" for x, y, w, h in ZONE)


def momente(intervale: list[dict]) -> list[float]:
    out = set()
    for iv in intervale:
        a, b = iv["intra"], iv["iese"]
        out.update({round(a + 0.6, 2), round((a + b) / 2, 2), round(max(a + 0.6, b - 0.3), 2)})
    return sorted(out)


def main(argv: list[str] | None = None) -> int:
    platforma.iesire_utf8()
    argv = sys.argv[1:] if argv is None else argv
    dosar = Path(argv[0])
    with open(dosar / "intervale.json", encoding="utf-8") as f:
        intervale = json.load(f)
    lucru = dosar / "lucru" / "planse"
    cadre = hyperframes.snapshot(dosar, momente(intervale), lucru)
    marcate = []
    for k, p in enumerate(cadre):
        m = lucru / f"m{k:03d}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(p), "-vf", f"{filtru_zone()},scale=360:640", str(m)], check=True)
        marcate.append(m)
    iesire = dosar / "planse"
    iesire.mkdir(exist_ok=True)
    for f in iesire.glob("foaie-*.jpg"):
        f.unlink()
    for i in range(0, len(marcate), 6):
        lista = marcate[i:i + 6]
        intrari = []
        for m in lista:
            intrari += ["-i", str(m)]
        n = len(lista)
        graf = "".join(f"[{j}:v]" for j in range(n)) + f"hstack=inputs={n}[o]" if n > 1 else "[0:v]copy[o]"
        subprocess.run(["ffmpeg", "-v", "error", "-y", *intrari, "-filter_complex", graf, "-map", "[o]",
                        str(iesire / f"foaie-{i // 6 + 1:02d}.jpg")], check=True)
    print(f"{len(marcate)} cadre în {len(list(iesire.glob('foaie-*.jpg')))} foi: {iesire}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
