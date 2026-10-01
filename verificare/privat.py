#!/usr/bin/env python3
"""Caută date private înainte de orice publicare: căi personale, emailuri, chei, numele comunității plătite, locația din metadatele
fișierelor media (iPhone-ul pune coordonatele GPS în fiecare MOV).

    python3 verificare/privat.py                 fișierele urmărite de git
    python3 verificare/privat.py <fișiere>...    doar fișierele date (de exemplu, ce urcă într-un Release)

Codul de ieșire e 0 doar dacă nu găsește nimic.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unelte import platforma  # noqa: E402

TIPARE = {
    "cale personală": r"(?:/Users/|/home/)[A-Za-z0-9._-]+/|[A-Za-z]:\\Users\\[^\\\s]+",
    "email": r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}",
    "cheie": r"sk-ant-[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[bp]-[A-Za-z0-9-]{10,}",
    "comunitatea plătită": r"(?i)sisteme[ -]ai",
}
MEDIA = (".mp4", ".mov", ".m4v", ".wav", ".mp3", ".m4a", ".png", ".jpg", ".jpeg")
CHEI_LOCATIE = ("location", "iso6709", "gps")


def in_text(text: str) -> list[str]:
    gasite = []
    for fel, tipar in TIPARE.items():
        for m in re.finditer(tipar, text):
            gasite.append(f"{fel}: {m.group(0)[:60]}")
    return gasite


def in_metadate(f: Path) -> list[str]:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format_tags:stream_tags", "-of", "default=nw=1", str(f)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return [f"locație în metadate: {l.split('=')[0]}" for l in r.stdout.splitlines() if any(k in l.lower() for k in CHEI_LOCATIE)]


def verifica(fisiere: list[Path]) -> list[str]:
    out = []
    for f in fisiere:
        if f.suffix.lower() in MEDIA:
            gasite = in_metadate(f)
        else:
            try:
                gasite = in_text(f.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, OSError):
                continue
        out += [f"{f}: {g}" for g in gasite]
    return out


def fisiere_git() -> list[Path]:
    r = subprocess.run(["git", "ls-files", "-z"], cwd=platforma.RADACINA, capture_output=True, check=True)
    return [platforma.RADACINA / p for p in r.stdout.decode("utf-8").split("\0") if p]


def main(argv: list[str] | None = None) -> int:
    platforma.iesire_utf8()
    argv = sys.argv[1:] if argv is None else argv
    gasite = verifica([Path(a) for a in argv] if argv else fisiere_git())
    print("\n".join(gasite) if gasite else "Nimic privat.")
    return 1 if gasite else 0


if __name__ == "__main__":
    sys.exit(main())
