#!/usr/bin/env python3
"""Randarea videoului la calitatea finală, vocea la −14 LUFS și verificarea. Înainte de randare se verifică ordinea
animațiilor (verificare/ordine.py): cu o problemă acolo nu se randează. Fișierul se numește „<Titlu> DRAFT n.mp4”; FINAL se
face doar după OK-ul omului (redenumire, nu randare nouă).

    python3 procese/editare/randeaza.py proiecte/<slug> [--fps 60] [--calitate high]
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from procese.editare import sunet  # noqa: E402
from unelte import hyperframes, platforma  # noqa: E402
from verificare import ordine  # noqa: E402
from verificare import video as verificare_video  # noqa: E402


def nume_fisier(titlu: str) -> str:
    """Titlul ca nume de fișier: fără caracterele interzise pe Windows (<>:"/\\|?*), fără punct sau spațiu la final."""
    t = re.sub(r"\s+", " ", re.sub(r'[<>:"/\\|?*]', "", titlu)).strip(" .")
    return t or "reel"


def urmatorul_draft(dosar: Path, titlu: str) -> Path:
    titlu = nume_fisier(titlu)
    nr = [int(m.group(1)) for p in dosar.glob(f"{glob.escape(titlu)} DRAFT *.mp4") if (m := re.search(r"DRAFT (\d+)\.mp4$", p.name))]
    return dosar / f"{titlu} DRAFT {max(nr, default=0) + 1}.mp4"


def scrie_verify(dosar: Path, draft: Path, r: verificare_video.Rezultat) -> Path:
    """VERIFY.md în proiect: ce s-a verificat pe draft, cu cifre."""
    tinta = dosar / "VERIFY.md"
    tinta.write_text(f"# Verificare: {draft.name}\n\n```\n{verificare_video.raport(r)}\n```\n", encoding="utf-8")
    return tinta


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
    print("Verific ordinea animațiilor...", flush=True)
    if not ordine.verifica(dosar):
        print("Nu randez: repară ce e mai sus (în scenariu sau în piesa care a scris tween-ul) și reia compoziția.")
        return 1
    brut = dosar / "lucru" / "randare.mp4"
    print(f"Randez la {a.fps} fps, calitate {a.calitate} (câteva minute)...", flush=True)
    hyperframes.randeaza(dosar, brut, a.fps, a.calitate)
    iesire = urmatorul_draft(dosar, titlu)
    lufs = sunet.normalizeaza(brut, iesire)
    print(f"{iesire.name}: vocea la {lufs:.1f} LUFS. Verific...", flush=True)
    with open(dosar / "taieturi.json", encoding="utf-8") as f:
        cuts = json.load(f)["taieturi"]
    r = verificare_video.verifica(iesire, dosar / "voce.wav", cuts, a.fps, verificare_video.durata_video(dosar / "taiat.mp4"))
    print(verificare_video.raport(r))
    scrie_verify(dosar, iesire, r)
    return 0 if r.ok else 1


if __name__ == "__main__":
    sys.exit(main())
