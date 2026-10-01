#!/usr/bin/env python3
"""Proba de stil: 4 secunde cu un card, captions și cardul de final în brandul tău, ca să vezi cum arată înainte de primul reel.
Textul are „ă â î ș ț”: dacă fontul tău nu le are, se vede aici.

    python3 procese/reel/proba_stil.py        → brand/proba-stil.mp4 și brand/proba-stil.jpg
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from procese.reel import compozitie  # noqa: E402
from unelte import brand, hyperframes, platforma  # noqa: E402

TEXT = "Așa arată reelurile tale: cardurile, captions și cardul de final, cu ă, â, î, ș, ț."
DURATA = 4.0


def transcript_proba() -> dict:
    cuv = TEXT.split()
    pas = (DURATA - 0.4) / len(cuv)
    return {"words": [{"text": w, "start": round(0.2 + i * pas, 3), "end": round(0.2 + (i + 1) * pas - 0.03, 3), "type": "word"}
                      for i, w in enumerate(cuv)]}


def scenariu_proba(b: dict) -> dict:
    return {"stil": "studio", "cadru": {"shift": 0, "carduri_y": 280, "captions_y": 1480},
            "carduri": [
                {"id": "proba", "ancora": "start", "kicker": "PROBĂ DE STIL",
                 "randuri": [{"text": "culorile **tale**", "icoana": "zap"},
                             {"text": "diacritice: ă â î **ș ț**", "icoana": "check", "ancora": "cardurile"}]},
                {"id": "final", "ancora": "cardul de final", "kicker": (b["nume"] or "final").upper(), "brand": True,
                 "randuri": [{"text": b["cta"] or "urmărește-mă pentru **mai multe**", "icoana": "user"}]}]}


def scrie(cale: Path, date) -> None:
    cale.write_text(json.dumps(date, ensure_ascii=False, indent=1), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    platforma.iesire_utf8()
    b = brand.incarca()
    dosar = brand.BRAND / "proba"
    shutil.rmtree(dosar, ignore_errors=True)
    dosar.mkdir(parents=True)
    d = f"{DURATA:.3f}"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c=0x1e293b:s=1080x1920:r=30:d={d}",
                    "-f", "lavfi", "-t", d, "-i", "anullsrc=r=48000:cl=mono", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-shortest", str(dosar / "taiat.mp4")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-t", d, "-i", "anullsrc=r=48000:cl=mono",
                    str(dosar / "voce.wav")], check=True)
    scrie(dosar / "transcript.json", transcript_proba())
    scrie(dosar / "taieturi.json", {"taieturi": [], "bucati": []})
    scrie(dosar / "scenariu.json", scenariu_proba(b))
    if compozitie.main([str(dosar)]) != 0:
        return 1
    video = brand.BRAND / "proba-stil.mp4"
    hyperframes.randeaza(dosar, video, 30, "draft")
    cadre = hyperframes.snapshot(dosar, [1.6, 3.6], dosar / "cadre")
    intrari = []
    for c in cadre:
        intrari += ["-i", str(c)]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *intrari, "-filter_complex",
                    "".join(f"[{i}:v]scale=540:960[s{i}];" for i in range(len(cadre))) + "".join(f"[s{i}]" for i in range(len(cadre)))
                    + f"hstack=inputs={len(cadre)}[o]", "-map", "[o]", str(brand.BRAND / "proba-stil.jpg")], check=True)
    print(f"Proba de stil: {video} și {brand.BRAND / 'proba-stil.jpg'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
