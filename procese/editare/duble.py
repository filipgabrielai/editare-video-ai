#!/usr/bin/env python3
"""Dublele unui reel: fiecare clip se împarte pe tăceri (−38 dB, 0,45 s), iar fiecare dublă (sunetul dintre două tăceri) se
transcrie local cu whisper.cpp, ca să alegi citind. Nimic nu pleacă de pe calculator.

    python3 procese/editare/duble.py "<folderul cu clipuri sau un clip>" [--nume "Numele reelului"]

Iese în proiecte/<slug>/: sursa.json, lucru/<clip>.wav (16 kHz, pentru whisper), lucru/<clip>.raw (8 kHz, pentru capetele
tăieturii) și duble.json [{dubla, clip, nr, start, end, text}], cu timpii în clip.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from unelte import brand, platforma, proiect  # noqa: E402

PRAG, MIN_TACERE, MIN_DUBLA = -38, 0.45, 0.25


def taceri(text: str) -> tuple[list[float], list[float]]:
    st = [max(0.0, float(x)) for x in re.findall(r"silence_start: (-?[\d.]+)", text)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", text)]
    return st, en


def intervale(starturi: list[float], capete: list[float], durata_totala: float) -> list[tuple[float, float]]:
    """Dublele = intervalele cu sunet dintre tăceri; ce e mai scurt de 0,25 s e zgomot."""
    return [(round(a, 3), round(b, 3)) for a, b in zip([0.0] + capete, starturi + [durata_totala]) if b - a >= MIN_DUBLA]


def durata(f: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def detecteaza(wav: Path) -> list[tuple[float, float]]:
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(wav), "-af", f"silencedetect=n={PRAG}dB:d={MIN_TACERE}", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    st, en = taceri(r.stderr)
    return intervale(st, en, durata(wav))


def extrage_audio(clip: Path, lucru: Path, nume: str) -> tuple[Path, Path]:
    wav, raw = lucru / f"{nume}.wav", lucru / f"{nume}.raw"
    if not wav.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(clip), "-vn", "-ac", "1", "-ar", "16000", str(wav)], check=True)
    if not raw.exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(clip), "-vn", "-ac", "1", "-ar", "8000", "-f", "f32le", str(raw)], check=True)
    return wav, raw


def transcrie(wav: Path, a: float, b: float, lucru: Path, limba: str = "ro", vocabular: str = "") -> str:
    seg = lucru / "dubla.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-ss", f"{a:.3f}", "-to", f"{b:.3f}", str(seg)], check=True)
    cli = platforma.gaseste("whisper-cli")
    if not cli:
        raise SystemExit("whisper-cli lipsește: rulează /instalare.")
    baza = platforma.RADACINA
    r = subprocess.run([cli, "-m", platforma.cale_pentru_unealta(platforma.model_whisper(), baza), "-l", limba, "-np", "-nt",
                        *(["--prompt", vocabular] if vocabular else []), "-f", platforma.cale_pentru_unealta(seg, baza)],
                       cwd=baza, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"whisper-cli nu a pornit (cod {r.returncode}): " + " ".join((r.stderr or "").strip().splitlines()[-2:]))
    return " ".join((r.stdout or "").split())


def main(argv: list[str] | None = None) -> int:
    platforma.iesire_utf8()
    p = argparse.ArgumentParser(description="Împarte clipurile pe duble și le transcrie local.")
    p.add_argument("sursa", help="folderul cu clipurile brute sau un singur clip")
    p.add_argument("--nume", help="numele reelului (implicit, numele folderului)")
    p.add_argument("--vocabular", default="", help="nume și cuvinte din reel, cu virgulă, pe lângă cele din brand (\"bolt.new, Lovable\")")
    a = p.parse_args(argv)
    sursa = Path(a.sursa).expanduser()
    if not sursa.exists():
        raise SystemExit(f"Nu găsesc {sursa}.")
    dosar = proiect.creeaza(sursa, a.nume)
    lucru = dosar / "lucru"
    rezultat = []
    harta = proiect.clipuri(dosar)
    b = brand.incarca()
    lb, voc = brand.limba(b), brand.prompt_whisper(b, a.vocabular)
    for nume, clip in harta.items():
        wav, _ = extrage_audio(clip, lucru, nume)
        d = durata(wav)
        for n, (x, y) in enumerate(detecteaza(wav), 1):
            text = transcrie(wav, max(0.0, x - 0.15), min(d, y + 0.15), lucru, lb, voc)
            rezultat.append({"dubla": f"{nume}_{n:02d}", "clip": nume, "nr": n, "start": x, "end": y, "text": text})
            print(f"{nume}_{n:02d}  {x:7.2f}-{y:7.2f}  ({y - x:5.2f} s)  {text}", flush=True)
    with open(dosar / "duble.json", "w", encoding="utf-8") as f:
        json.dump(rezultat, f, ensure_ascii=False, indent=1)
    print(f"\n{len(rezultat)} duble în {len(harta)} clipuri. Proiectul: {dosar}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
