#!/usr/bin/env python3
"""Falsele starturi ascunse în dublele alese: o încercare ruptă, o pauză scurtă, apoi fraza spusă din nou. Whisper le netezește
și scrie textul curat, deci din transcript nu se văd; una a ajuns așa într-un reel livrat (1,45 s în plus).

    python3 procese/editare/false_starturi.py proiecte/<slug> <dubla> [<dubla> ...]

Pentru fiecare dublă: pauzele din interior de cel puțin 0,2 s (sub −45 dB), cu ce se aude înainte și după fiecare. Când partea
de după începe cu același cuvânt ca partea dinainte, dubla e marcată: o asculți și, dacă e reluare, transcrii cuvintele de la
reluare (cuvinte.py proiecte/<slug> <dubla>@<timp>). Se rulează pe toate dublele alese, înainte de cuvinte.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from procese.editare import duble, taietura  # noqa: E402
from unelte import brand, platforma  # noqa: E402

PAUZA, LINISTE = 0.20, -45.0


def _voce(r10: list[float], s: float, e: float) -> list[int]:
    return [k for k in range(max(0, int(s / 0.01)), min(len(r10), int(e / 0.01))) if r10[k] > taietura.VOCE]


def pauze_interioare(r10: list[float], s: float, e: float) -> list[tuple[float, float]]:
    voce = _voce(r10, s, e)
    if not voce:
        return []
    out, st = [], None
    for k in range(voce[0], voce[-1] + 1):
        if r10[k] < LINISTE:
            st = k if st is None else st
        else:
            if st is not None and (k - st) * 0.01 >= PAUZA - 1e-9:
                out.append((round(st * 0.01, 2), round(k * 0.01, 2)))
            st = None
    return out


def repeta_inceputul(inainte: str, dupa: str) -> bool:
    """Ajunge primul cuvânt: partea de după pauză pornește chiar pe sfârșitul pauzei, deci dacă începe cu același cuvânt (sau
    cu cuvântul din care înainte s-a spus doar începutul: „Înăuntru | Înăuntrul”), cuvântul a fost spus din nou."""
    a = [x for x in (taietura.fara_semne(t) for t in inainte.split()) if x]
    b = [x for x in (taietura.fara_semne(t) for t in dupa.split()) if x]
    if not a or not b:
        return False
    scurt, lung = sorted((a[0], b[0]), key=len)
    return a[0] == b[0] or (len(scurt) >= 2 and lung.startswith(scurt))


def cauta(r10: list[float], s: float, e: float, asculta) -> list[dict]:
    """Pauzele din interiorul dublei, cu ce se aude înainte și după fiecare (asculta(a, b) întoarce textul)."""
    voce = _voce(r10, s, e)
    out = []
    for a, b in pauze_interioare(r10, s, e):
        inainte = asculta(max(0.0, voce[0] * 0.01 - 0.1), a + 0.05)
        dupa = asculta(b - 0.08, voce[-1] * 0.01 + 0.15)
        out.append({"pauza": (a, b), "inainte": inainte, "dupa": dupa, "repeta": repeta_inceputul(inainte, dupa),
                    "de_la_timp": round(b - 0.08, 2)})
    return out


def main(argv: list[str] | None = None) -> int:
    platforma.iesire_utf8()
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 2:
        raise SystemExit("Folosire: false_starturi.py proiecte/<slug> <dubla> [<dubla> ...]")
    dosar = Path(argv[0])
    with open(dosar / "duble.json", encoding="utf-8") as f:
        toate = {d["dubla"]: d for d in json.load(f)}
    lb = brand.limba(brand.incarca())
    r10, marcate = {}, []
    for nume in argv[1:]:
        if nume not in toate:
            raise SystemExit(f"Dubla {nume} nu există în duble.json.")
        d = toate[nume]
        wav = dosar / "lucru" / f"{d['clip']}.wav"
        if d["clip"] not in r10:
            r10[d["clip"]] = taietura.rms10_db(wav)
        gasite = cauta(r10[d["clip"]], d["start"] - 0.1, d["end"] + 0.1,
                       lambda a, b, wav=wav: duble.transcrie(wav, a, b, dosar / "lucru", lb))
        if not gasite:
            print(f"{nume}: fără pauze în interior", flush=True)
        for g in gasite:
            a, b = g["pauza"]
            print(f"{nume}: pauză {a:.2f}–{b:.2f} ({b - a:.2f} s) | înainte: „{g['inainte']}” | după: „{g['dupa']}”", flush=True)
            if g["repeta"]:
                marcate.append(nume)
                print(f"   !! repetă începutul: ascult-o; dacă e reluare: cuvinte.py {dosar} {nume}@{g['de_la_timp']}", flush=True)
    de_ascultat = sorted(set(marcate))
    print(f"\n{len(de_ascultat)} duble de ascultat din {len(argv) - 1}: {' '.join(de_ascultat) or 'niciuna'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
