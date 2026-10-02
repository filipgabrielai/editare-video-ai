#!/usr/bin/env python3
"""Proba de reel cap-coadă: un clip sintetic cu două duble (vocea din proba.wav, de două ori), într-un folder cu spații și
diacritice, trece prin dublele, cuvintele, tăietura, compoziția, randarea și verificarea. Rulează și în testele automate.

    python3 tests/proba_reel.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAD))
from procese.editare import compozitie, cuvinte, duble, randeaza, taietura  # noqa: E402
from unelte import platforma, proiect  # noqa: E402

NUME = "proba reel automata"


def scrie_json(cale: Path, date) -> None:
    cale.write_text(json.dumps(date, ensure_ascii=False), encoding="utf-8")


def clip_sintetic(folder: Path) -> Path:
    proba = str(RAD / "tests" / "date" / "proba.wav")
    audio = folder / "voce.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", proba, "-f", "lavfi", "-t", "1.5", "-i", "anullsrc=r=16000:cl=mono",
                    "-i", proba, "-filter_complex", "[0:a][1:a][2:a]concat=n=3:v=0:a=1[a]", "-map", "[a]", str(audio)], check=True)
    d = duble.durata(audio)
    clip = folder / "Clipul ăsta.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=s=1080x1920:r=60:d={d:.3f}", "-i", str(audio),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(clip)], check=True)
    audio.unlink()
    return clip


def main() -> int:
    platforma.iesire_utf8()
    sys.stdout.reconfigure(line_buffering=True)
    dosar = proiect.PROIECTE / proiect.slug(NUME)
    shutil.rmtree(dosar, ignore_errors=True)
    try:
        with tempfile.TemporaryDirectory(prefix="filmări noi ") as d:   # clipul trebuie să existe până la tăietură
            return pasi(Path(d), dosar)
    finally:
        shutil.rmtree(dosar, ignore_errors=True)


def pasi(folder: Path, dosar: Path) -> int:
    clip_sintetic(folder)
    print("1/5 Dublele...")
    duble.main([str(folder), "--nume", NUME])
    lista = json.loads((dosar / "duble.json").read_text(encoding="utf-8"))
    if len(lista) != 2:
        print(f"Am găsit {len(lista)} duble în loc de 2.")
        return 1
    a_doua = lista[1]["dubla"]
    print("2/5 Cuvintele...")
    cuvinte.main([str(dosar), a_doua])
    scrie_json(dosar / "bucati.json", [{"dubla": a_doua, "de_la": None, "pana_la": None}])
    print("3/5 Tăietura...")
    taietura.main([str(dosar)])
    scrie_json(dosar / "scenariu.json", {"stil": "studio", "cadru": {"shift": 120, "carduri_y": 280, "captions_y": 1480},
                                         "carduri": [{"id": "proba", "ancora": "start", "kicker": "PROBĂ",
                                                      "randuri": [{"text": "editare în **română**", "icoana": "check"}]}]})
    print("4/5 Compoziția...")
    if compozitie.main([str(dosar)]) != 0:
        return 1
    print("5/5 Randarea și verificarea...")
    if randeaza.main([str(dosar), "--fps", "30", "--calitate", "draft"]) != 0:
        return 1
    print("\nReelul de probă trece.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
