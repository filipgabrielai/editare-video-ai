#!/usr/bin/env python3
"""Proba cap-coadă, pe reel (9:16) și pe orizontală (16:9): un clip sintetic cu două duble (vocea din proba.wav, de două ori),
într-un folder cu spații și diacritice, trece prin dublele, cuvintele, tăietura, compoziția, randarea și verificarea. Rulează și
în testele automate.

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
from procese.editare import compozitie, cuvinte, duble, randeaza, scenariu, taietura  # noqa: E402
from unelte import formate, platforma, proiect  # noqa: E402

NUME = "proba reel automata"


def scrie_json(cale: Path, date) -> None:
    cale.write_text(json.dumps(date, ensure_ascii=False), encoding="utf-8")


def clip_sintetic(folder: Path, filmare: str) -> Path:
    w, h = formate.dimensiuni(filmare)
    proba = str(RAD / "tests" / "date" / "proba.wav")
    audio = folder / "voce.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", proba, "-f", "lavfi", "-t", "1.5", "-i", "anullsrc=r=16000:cl=mono",
                    "-i", proba, "-filter_complex", "[0:a][1:a][2:a]concat=n=3:v=0:a=1[a]", "-map", "[a]", str(audio)], check=True)
    d = duble.durata(audio)
    clip = folder / "Clipul ăsta.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=s={w}x{h}:r=60:d={d:.3f}", "-i", str(audio),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(clip)], check=True)
    audio.unlink()
    return clip


def main() -> int:
    platforma.iesire_utf8()
    sys.stdout.reconfigure(line_buffering=True)
    for filmare in ("9:16", "16:9"):
        nume = f"{NUME} {filmare.replace(':', 'x')}"
        dosar = proiect.PROIECTE / proiect.slug(nume)
        shutil.rmtree(dosar, ignore_errors=True)
        print(f"\n=== {filmare} ===")
        try:
            with tempfile.TemporaryDirectory(prefix="filmări noi ") as d:   # clipul trebuie să existe până la tăietură
                if pasi(Path(d), dosar, nume, filmare) != 0:
                    return 1
        finally:
            shutil.rmtree(dosar, ignore_errors=True)
    print("\nProba trece pe 9:16 și pe 16:9.")
    return 0


def pasi(folder: Path, dosar: Path, nume: str, filmare: str) -> int:
    clip_sintetic(folder, filmare)
    print("1/5 Dublele...")
    duble.main([str(folder), "--nume", nume])
    lista = json.loads((dosar / "duble.json").read_text(encoding="utf-8"))
    if len(lista) != 2:
        print(f"Am găsit {len(lista)} duble în loc de 2.")
        return 1
    a_doua = lista[1]["dubla"]
    print("2/5 Cuvintele...")
    cuvinte.main([str(dosar), a_doua])
    scrie_json(dosar / "bucati.json", [{"dubla": a_doua, "de_la": None, "pana_la": None}])
    print("3/5 Tăietura...")
    taietura.main([str(dosar), "--filmare", filmare])
    cadru = {"shift": 120, "carduri_y": 280, "captions_y": 1480} if filmare == "9:16" else {"carduri": "dreapta"}
    cuvintele = json.loads((dosar / "transcript.json").read_text(encoding="utf-8"))["words"]
    primul = next(w["text"] for w in cuvintele if scenariu.norm(w["text"]))   # modelul mic poate începe cu un semn
    scrie_json(dosar / "scenariu.json", {"stil": "studio", "format": filmare, "cadru": cadru,
                                         "carduri": [{"id": "proba", "ancora": "start", "kicker": "PROBĂ",
                                                      "randuri": [{"text": "editare în **română**", "icoana": "check"}]}],
                                         # o piesă pusă din scenariu, pe primul cuvânt: și ea trece prin ordine, randare și verificare
                                         "momente": [{"piesa": "cuvant", "id": "proba", "text": "PROBĂ", "ancora": primul, "durata": 1.2}]})
    print("4/5 Compoziția...")
    if compozitie.main([str(dosar)]) != 0:
        return 1
    print("5/5 Randarea și verificarea...")
    if randeaza.main([str(dosar), "--fps", "30", "--calitate", "draft"]) != 0:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
