#!/usr/bin/env python3
"""Cuvintele cu timpi pe dublele alese (whisper.cpp local, un cuvânt pe segment), pentru tăietură și captions.

    python3 procese/editare/cuvinte.py proiecte/<slug> IMG_1544_03 IMG_1545_06@250.5 ...

Iese transcripte/<dubla>.json = {dubla, decalaj, words}: timpii din words sunt relativi la bucata tăiată din clip, care începe
la decalaj = 0,15 s înainte de sunetul primului cuvânt (nu de segmentul Whisper, care poate începe peste liniște și buze);
timpul în clip = decalaj + start. Sare peste ce e deja transcris. „<dubla>@<timp>” transcrie dubla de la secunda aceea din
clip (reluarea de după un fals start, vezi false_starturi.py) și înlocuiește transcriptul vechi.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from procese.editare import taietura  # noqa: E402
from unelte import brand, platforma  # noqa: E402


def cuvinte_din_whisper(j: dict) -> list[dict]:
    out = []
    for s in j.get("transcription", []):
        t = s.get("text", "").strip()
        if not t or (t.startswith("[") and t.endswith("]")):
            continue
        out.append({"text": t, "start": round(s["offsets"]["from"] / 1000, 3), "end": round(s["offsets"]["to"] / 1000, 3), "type": "word"})
    return out


def desparte(spec: str) -> tuple[str, float | None]:
    """„IMG_1622_32@250.5” = dubla, transcrisă de la secunda 250,5 din clip (după un fals start)."""
    nume, _, t = spec.partition("@")
    return nume, (float(t) if t else None)


def decalaj_pe_sunet(rms: list[float], prag_db: float, start: float, end: float, de_la: float = 0.0) -> float:
    """De unde pleacă bucata trimisă la Whisper: cu 0,15 s înainte de sunetul primului cuvânt, nu de începutul segmentului
    Whisper. Cu liniște și buze în față, Whisper lipea toate cuvintele dublei de începutul fișierului. Niciodată înainte de
    `de_la` (reluarea de după un fals start): altfel coada falsului start ajunge iar la Whisper."""
    on = taietura.debut(rms, int(start / taietura.PAS), int(end / taietura.PAS), prag_db, int(de_la / taietura.PAS))
    return max(de_la, 0.0, round(on * taietura.PAS - 0.15, 3))


def transcrie_dubla(dosar: Path, d: dict, limba: str = "ro", vocabular: str = "", de_la_timp: float | None = None) -> Path:
    tinta = dosar / "transcripte" / f"{d['dubla']}.json"
    if tinta.exists() and de_la_timp is None:
        return tinta
    lucru = dosar / "lucru"
    raw = lucru / f"{d['clip']}.raw"
    start = d["start"] if de_la_timp is None else de_la_timp
    if raw.exists():
        rms = taietura.rms_db(raw)
        decalaj = decalaj_pe_sunet(rms, taietura.prag(rms), start, d["end"], de_la_timp or 0.0)
    else:
        decalaj = max(0.0, start - 0.15) if de_la_timp is None else start
    seg = lucru / f"{d['dubla']}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(lucru / f"{d['clip']}.wav"), "-ss", f"{decalaj:.3f}",
                    "-to", f"{d['end'] + 0.15:.3f}", str(seg)], check=True)
    cli = platforma.gaseste("whisper-cli")
    if not cli:
        raise SystemExit("whisper-cli lipsește: rulează /instalare.")
    baza = platforma.RADACINA
    rel = lambda p: platforma.cale_pentru_unealta(p, baza)  # noqa: E731
    r = subprocess.run([cli, "-m", rel(platforma.model_whisper()), "-l", limba, "-ml", "1", "-sow", "-oj",
                        "-of", rel(lucru / d["dubla"]), "-np", *(["--prompt", vocabular] if vocabular else []), "-f", rel(seg)],
                       cwd=baza, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"whisper-cli nu a pornit (cod {r.returncode}): " + " ".join((r.stderr or "").strip().splitlines()[-2:]))
    with open(lucru / f"{d['dubla']}.json", encoding="utf-8") as f:
        ws = cuvinte_din_whisper(json.load(f))
    tinta.parent.mkdir(exist_ok=True)
    date = {"dubla": d["dubla"], "decalaj": round(decalaj, 3), "words": ws}
    if de_la_timp is not None:
        date["de_la_timp"] = de_la_timp
    with open(tinta, "w", encoding="utf-8") as f:
        json.dump(date, f, ensure_ascii=False, indent=1)
    return tinta


def main(argv: list[str] | None = None) -> int:
    platforma.iesire_utf8()
    argv = list(sys.argv[1:] if argv is None else argv)
    in_plus = ""
    if "--vocabular" in argv:
        k = argv.index("--vocabular")
        in_plus = argv[k + 1] if k + 1 < len(argv) else ""
        del argv[k:k + 2]
    if len(argv) < 2:
        raise SystemExit('Folosire: cuvinte.py proiecte/<slug> <dubla>[@timp] [<dubla> ...] [--vocabular "bolt.new, Lovable"]')
    dosar = Path(argv[0])
    with open(dosar / "duble.json", encoding="utf-8") as f:
        toate = {d["dubla"]: d for d in json.load(f)}
    b = brand.incarca()
    lb, voc = brand.limba(b), brand.prompt_whisper(b, in_plus)
    for spec in argv[1:]:
        nume, de_la_timp = desparte(spec)
        if nume not in toate:
            raise SystemExit(f"Dubla {nume} nu există în duble.json (sunt: {', '.join(list(toate)[:12])}...).")
        tinta = transcrie_dubla(dosar, toate[nume], lb, voc, de_la_timp)
        with open(tinta, encoding="utf-8") as f:
            ws = json.load(f)["words"]
        print(f"{nume}: {len(ws)} cuvinte | {' '.join(w['text'] for w in ws)[:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
