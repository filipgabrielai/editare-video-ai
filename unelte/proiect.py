"""Folderul unui video: proiecte/<slug>/. Numele din el sunt doar ASCII, fiindcă whisper.cpp pe Windows nu deschide căi cu
diacritice; clipurile brute rămân unde sunt, iar sursa.json ține legătura cu ele."""
from __future__ import annotations

import json
import re
import shutil
import unicodedata
from pathlib import Path

from unelte import formate, platforma

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
    harta: dict[str, str] = {}
    amprente: dict[str, list[int]] = {}
    for k, p in enumerate(clipuri_brute, 1):
        cheie = nume_clip(p.stem, k)
        if cheie in harta:
            cheie = f"{cheie}-{k}"
        harta[cheie] = str(p.resolve())
        st = p.stat()
        amprente[cheie] = [st.st_size, st.st_mtime_ns]
    nou = {"sursa": str(sursa.resolve()), "clipuri": harta, "amprente": amprente}
    if (dosar / "sursa.json").is_file():
        vechi = json.loads((dosar / "sursa.json").read_text(encoding="utf-8"))
        if {k: vechi.get(k) for k in ("clipuri", "amprente")} == {k: nou[k] for k in ("clipuri", "amprente")}:
            print(f"Proiectul {dosar.name} există deja, cu aceleași clipuri: refolosesc ce e calculat.")
        else:
            # un clip refilmat sau alt folder cu același nume: sunetul și cuvintele vechi ar tăia clipul nou la timpii vechi
            print(f"Clipurile din {dosar.name} s-au schimbat față de ultima rulare: refac dublele de la zero.")
            shutil.rmtree(dosar / "lucru", ignore_errors=True)
            shutil.rmtree(dosar / "transcripte", ignore_errors=True)
            (dosar / "duble.json").unlink(missing_ok=True)
    (dosar / "lucru").mkdir(parents=True, exist_ok=True)
    with open(dosar / "sursa.json", "w", encoding="utf-8") as f:
        json.dump(nou, f, ensure_ascii=False, indent=1)
    return dosar


def clipuri(dosar: Path) -> dict[str, Path]:
    with open(dosar / "sursa.json", encoding="utf-8") as f:
        return {k: Path(v) for k, v in json.load(f)["clipuri"].items()}


def format_proiect(dosar: Path, sc: dict | None = None) -> str:
    """Pânza videoului: "format" din scenariu, altfel filmarea de la tăietură, altfel 9:16 (proiectele făcute înainte)."""
    filmare = formate.IMPLICIT
    if (dosar / "taieturi.json").is_file():
        filmare = json.loads((dosar / "taieturi.json").read_text(encoding="utf-8")).get("filmare", formate.IMPLICIT)
    if sc is None and (dosar / "scenariu.json").is_file():
        sc = json.loads((dosar / "scenariu.json").read_text(encoding="utf-8"))
    fmt = (sc or {}).get("format", filmare)
    if fmt != filmare:
        raise SystemExit(f"Scenariul cere {fmt}, dar tăietura e {filmare}. Refă tăietura cu --filmare {fmt}. "
                         "(Pânza și filmarea au același format.)")
    return fmt
