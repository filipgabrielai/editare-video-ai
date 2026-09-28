"""Folderul unui video: proiecte/<slug>/. Numele din el sunt doar ASCII, fiindcă whisper.cpp pe Windows nu deschide căi cu
diacritice; clipurile brute rămân unde sunt, iar sursa.json ține legătura cu ele."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from unelte import platforma

PROIECTE = platforma.RADACINA / "proiecte"
VIDEO_EXT = (".mov", ".mp4", ".m4v", ".mkv")


def slug(nume: str) -> str:
    s = unicodedata.normalize("NFD", nume)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s or "video"


def nume_clip(stem: str, k: int) -> str:
    return stem if re.fullmatch(r"[A-Za-z0-9_-]+", stem) else f"clip{k:02d}"


def creeaza(sursa: Path, nume: str | None = None) -> Path:
    """proiecte/<slug>/ pentru un folder de clipuri (sau un singur clip), cu sursa.json și lucru/."""
    if sursa.is_file():
        clipuri_brute = [sursa]
    else:
        clipuri_brute = sorted(p for p in sursa.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXT)
    if not clipuri_brute:
        raise SystemExit(f"Nu am găsit clipuri video ({', '.join(VIDEO_EXT)}) în {sursa}.")
    dosar = PROIECTE / slug(nume or (sursa.stem if sursa.is_file() else sursa.name))
    (dosar / "lucru").mkdir(parents=True, exist_ok=True)
    harta: dict[str, str] = {}
    for k, p in enumerate(clipuri_brute, 1):
        cheie = nume_clip(p.stem, k)
        if cheie in harta:
            cheie = f"{cheie}-{k}"
        harta[cheie] = str(p.resolve())
    with open(dosar / "sursa.json", "w", encoding="utf-8") as f:
        json.dump({"sursa": str(sursa.resolve()), "clipuri": harta}, f, ensure_ascii=False, indent=1)
    return dosar


def clipuri(dosar: Path) -> dict[str, Path]:
    with open(dosar / "sursa.json", encoding="utf-8") as f:
        return {k: Path(v) for k, v in json.load(f)["clipuri"].items()}
