#!/usr/bin/env python3
"""Proba de 30 de secunde: transcrie un clip scurt în română și randează 2 secunde. Dacă trece, poți edita.

    python3 tests/proba_30s.py        (pe Windows: python tests/proba_30s.py)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unelte import platforma  # noqa: E402

DATE = Path(__file__).resolve().parent / "date"
CUVINTE = ("incredibil", "productiv")   # proba.wav: „Mi se pare incredibil câte lucruri poți să faci cu ea și cât de productiv poți să fii.”
CADRE_ASTEPTATE = 60                   # 2 s la 30 fps


def fara_diacritice(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def transcriere_buna(text: str, model: Path) -> bool:
    """Cu modelul mare cerem cuvintele cheie; cu unul mic (testele automate), doar un text de cel puțin trei cuvinte."""
    t = fara_diacritice(text)
    if "large" in model.name:
        return all(c in t for c in CUVINTE)
    return len(t.split()) >= 3


def transcrie(wav: Path, model: Path) -> str:
    cli = platforma.gaseste("whisper-cli")
    if not cli:
        raise SystemExit("whisper-cli lipsește: rulează verificarea (verificare/instalarea.py).")
    r = subprocess.run([cli, "-m", str(model), "-l", "ro", "-np", "-nt", "-f", str(wav)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    return " ".join((r.stdout or "").split())


def comanda_randare(dosar: Path, iesire: Path) -> list[str]:
    """Randarea pornește `node` direct pe intrarea pachetului, nu prin `npx`: pe Windows npx e un .cmd, iar cmd.exe taie
    calea „C:\\Program Files\\…” la primul spațiu când și argumentele au spații (folderul temporar, „C:\\Users\\Ion Popescu”)."""
    node = shutil.which("node")
    if not node:
        raise SystemExit("Node.js lipsește: rulează verificarea (verificare/instalarea.py), îți spune cum îl instalezi.")
    intrare = platforma.RADACINA / "node_modules" / "hyperframes" / "bin" / "hyperframes.mjs"
    return [node, str(intrare), "render", str(dosar), "--fps", "30", "--quality", "draft", "-o", str(iesire)]


def mediu_randare() -> dict[str, str]:
    """Mediul pentru randare, cu telemetria HyperFrames oprită: nimic nu pleacă de pe calculatorul omului."""
    return {**os.environ, "HYPERFRAMES_NO_TELEMETRY": "1"}


def randeaza(dosar: Path, iesire: Path) -> int:
    shutil.copy(platforma.RADACINA / "node_modules" / "gsap" / "dist" / "gsap.min.js", dosar / "gsap.min.js")
    subprocess.run(comanda_randare(dosar, iesire), cwd=platforma.RADACINA, env=mediu_randare(), check=True, timeout=900)
    r = subprocess.run([shutil.which("ffprobe") or "ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                        "-show_entries", "stream=nb_read_frames", "-of", "json", str(iesire)],
                       capture_output=True, text=True, check=True)
    return int(json.loads(r.stdout)["streams"][0]["nb_read_frames"])


def main() -> int:
    platforma.iesire_utf8()
    sys.stdout.reconfigure(line_buffering=True)   # mesajele probei apar în ordine printre cele ale randării, și când ieșirea e un fișier
    model = platforma.model_whisper()
    print("1/2 Transcriu un clip de 4 secunde...")
    text = transcrie(DATE / "proba.wav", model)
    print(f"    Whisper a auzit: {text or '(nimic)'}")
    if not transcriere_buna(text, model):
        print("Transcrierea nu arată bine. Verifică modelul (verificare/instalarea.py) și încearcă din nou.")
        return 1
    print("2/2 Randez 2 secunde (prima dată descarcă și browserul de randare)...")
    with tempfile.TemporaryDirectory(prefix="proba editare ") as d:
        comp = Path(d) / "compozitie"
        shutil.copytree(DATE / "compozitie", comp)
        cadre = randeaza(comp, Path(d) / "proba.mp4")
    if abs(cadre - CADRE_ASTEPTATE) > 1:
        print(f"Randarea a scos {cadre} cadre în loc de {CADRE_ASTEPTATE}. Vezi docs/DEPANARE.md.")
        return 1
    print("\nGata, poți edita.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
