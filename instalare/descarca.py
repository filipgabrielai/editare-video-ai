#!/usr/bin/env python3
"""Descarcă ce nu vine din magazine: modelul Whisper și, pe Windows, whisper.cpp.

    python3 instalare/descarca.py model                       modelul implicit (large-v3-turbo, 1,6 GB)
    python3 instalare/descarca.py model --nume ggml-tiny.bin  modelul mic (pentru testele automate)
    python instalare/descarca.py whisper                      Windows: whisper.cpp oficial, în unelte/whisper/

Descărcarea merge într-un fișier .part și se redenumește doar dacă mărimea e cea așteptată:
o descărcare întreruptă nu lasă un model stricat în urmă.
"""
from __future__ import annotations

import argparse
import http.client
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unelte import platforma  # noqa: E402

URL_MODEL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/{nume}"
WHISPER_VERSIUNE = "v1.9.2"   # ultima versiune cu arhive gata făcute pentru Windows (verificat 28 sept 2026)
WHISPER_ARHIVA = "whisper-blas-bin-x64.zip"
URL_WHISPER = "https://github.com/ggml-org/whisper.cpp/releases/download/{versiune}/{arhiva}"


def url_model(nume: str) -> str:
    return URL_MODEL.format(nume=nume)


def url_whisper(versiune: str = WHISPER_VERSIUNE, arhiva: str = WHISPER_ARHIVA) -> str:
    return URL_WHISPER.format(versiune=versiune, arhiva=arhiva)


def marime_corecta(cale: Path, asteptat: int | None) -> bool:
    return cale.is_file() and (asteptat is None or cale.stat().st_size == asteptat)


def descarca(url: str, destinatie: Path, asteptat: int | None = None) -> Path:
    """Descarcă în <destinatie>.part, cu progres; o redenumește doar dacă mărimea e cea așteptată."""
    destinatie.parent.mkdir(parents=True, exist_ok=True)
    part = destinatie.with_name(destinatie.name + ".part")
    cerere = urllib.request.Request(url, headers={"User-Agent": "editare-video-ai"})
    try:
        with urllib.request.urlopen(cerere, timeout=60) as r, open(part, "wb") as f:
            total = int(r.headers.get("Content-Length") or 0) or asteptat or 0
            scris, ultim = 0, -1
            while True:
                bucata = r.read(1 << 20)
                if not bucata:
                    break
                f.write(bucata)
                scris += len(bucata)
                if total:
                    pct = scris * 100 // total
                    if pct != ultim and pct % 5 == 0:
                        print(f"  {destinatie.name}: {pct}%", file=sys.stderr, flush=True)
                        ultim = pct
    except (OSError, http.client.HTTPException) as e:   # rețea căzută, timeout, server indisponibil (URLError/HTTPError sunt OSError)
        part.unlink(missing_ok=True)
        raise SystemExit(f"Nu am putut descărca {destinatie.name} ({e}). Verifică internetul și încearcă din nou.") from None
    if not marime_corecta(part, asteptat):
        marime = part.stat().st_size
        part.unlink()
        raise SystemExit(f"Descărcarea lui {destinatie.name} e incompletă ({marime} din {asteptat} octeți). Încearcă din nou.")
    part.replace(destinatie)
    return destinatie


def dezarhiveaza(arhiva: Path, destinatie: Path) -> None:
    destinatie.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(arhiva) as z:
            z.extractall(destinatie)
    except zipfile.BadZipFile:   # de obicei o pagină de login a rețelei (hotel, birou) venită în locul arhivei
        arhiva.unlink(missing_ok=True)
        raise SystemExit(f"Arhiva {arhiva.name} descărcată e stricată (poate rețeaua ți-a dat o pagină de login în locul ei). "
                         "Încearcă din nou, eventual pe altă rețea.") from None


def model(nume: str) -> Path:
    cale = platforma.MODELE / nume
    if marime_corecta(cale, platforma.MARIMI_MODEL.get(nume)):
        print(f"{nume} e deja descărcat.")
        return cale
    print(f"Descarc {nume} (o singură dată, poate dura câteva minute)...")
    return descarca(url_model(nume), cale, platforma.MARIMI_MODEL.get(nume))


def whisper_windows() -> None:
    if platforma.sistem() != "windows":
        raise SystemExit("Pe Mac, whisper.cpp se instalează cu: brew install whisper-cpp")
    if platforma.whisper_complet(platforma.UNELTE_WHISPER):
        print("whisper.cpp e deja în unelte/whisper/.")
        return
    tinta = platforma.UNELTE_WHISPER.parent   # arhiva are deja folderul Release/
    arhiva = tinta / WHISPER_ARHIVA
    print(f"Descarc whisper.cpp {WHISPER_VERSIUNE} pentru Windows...")
    descarca(url_whisper(), arhiva)
    dezarhiveaza(arhiva, tinta)
    arhiva.unlink()
    print(f"whisper.cpp e în {platforma.UNELTE_WHISPER}")


def main(argv: list[str] | None = None) -> int:
    platforma.iesire_utf8()
    p = argparse.ArgumentParser(description="Descarcă modelul Whisper sau whisper.cpp (Windows).")
    sub = p.add_subparsers(dest="ce", required=True)
    m = sub.add_parser("model", help="modelul Whisper")
    m.add_argument("--nume", default=platforma.MODEL_IMPLICIT)
    sub.add_parser("whisper", help="whisper.cpp pentru Windows")
    a = p.parse_args(argv)
    if a.ce == "model":
        model(a.nume)
    else:
        whisper_windows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
