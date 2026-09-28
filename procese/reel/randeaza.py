#!/usr/bin/env python3
"""Randarea reelului la calitatea finală, vocea la −14 LUFS și verificarea. Fișierul se numește „<Titlu> DRAFT n.mp4”;
FINAL se face doar după OK-ul omului (redenumire, nu randare nouă).

    python3 procese/reel/randeaza.py proiecte/<slug> [--fps 60] [--calitate high]
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from procese.reel import sunet  # noqa: E402
from unelte import hyperframes, platforma  # noqa: E402
from verificare import reel as verificare_reel  # noqa: E402


def urmatorul_draft(dosar: Path, titlu: str) -> Path:
    nr = [int(m.group(1)) for p in dosar.glob(f"{glob.escape(titlu)} DRAFT *.mp4") if (m := re.search(r"DRAFT (\d+)\.mp4$", p.name))]
    return dosar / f"{titlu} DRAFT {max(nr, default=0) + 1}.mp4"


def main(argv: list[str] | None = None) -> int:
    platforma.iesire_utf8()
    p = argparse.ArgumentParser(description="Randează reelul și îl verifică.")
    p.add_argument("dosar")
    p.add_argument("--fps", type=int, default=60)
    p.add_argument("--calitate", default="high", choices=["draft", "standard", "high"])
    a = p.parse_args(argv)
    dosar = Path(a.dosar)
    with open(dosar / "scenariu.json", encoding="utf-8") as f:
        titlu = json.load(f).get("titlu") or dosar.name
    brut = dosar / "lucru" / "randare.mp4"
    print(f"Randez la {a.fps} fps, calitate {a.calitate} (câteva minute)...", flush=True)
    hyperframes.randeaza(dosar, brut, a.fps, a.calitate)
    iesire = urmatorul_draft(dosar, titlu)
    lufs = sunet.normalizeaza(brut, iesire)
    print(f"{iesire.name}: vocea la {lufs:.1f} LUFS. Verific...", flush=True)
    with open(dosar / "taieturi.json", encoding="utf-8") as f:
        cuts = json.load(f)["taieturi"]
    r = verificare_reel.verifica(iesire, dosar / "voce.wav", cuts)
    print(verificare_reel.raport(r))
    return 0 if r.ok else 1


if __name__ == "__main__":
    sys.exit(main())
