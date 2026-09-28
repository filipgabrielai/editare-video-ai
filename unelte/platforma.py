"""Sistemul pe care rulează, unde sunt uneltele și unde stă modelul Whisper. Folosit de instalare, verificare și procese."""
from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path

RADACINA = Path(__file__).resolve().parents[1]
MODELE = RADACINA / "modele"
UNELTE_WHISPER = RADACINA / "unelte" / "whisper" / "Release"   # Windows: arhiva oficială whisper.cpp, dezarhivată de instalare/descarca.py
MODEL_IMPLICIT = "ggml-large-v3-turbo.bin"
MARIMI_MODEL = {"ggml-large-v3-turbo.bin": 1624555275, "ggml-tiny.bin": 77691713}   # octeți, de pe Hugging Face (x-linked-size)
WHISPER_EXE = ("whisper-cli", "whisper-server")


def sistem() -> str:
    """'mac', 'windows' sau 'linux'."""
    return {"Darwin": "mac", "Windows": "windows"}.get(platform.system(), "linux")


def exe(nume: str) -> str:
    """Numele executabilului pe sistemul curent (pe Windows, cu .exe)."""
    return nume + ".exe" if sistem() == "windows" else nume


def gaseste(nume: str) -> str | None:
    """Calea către o unealtă: întâi copia din repo (unelte/whisper/Release), apoi PATH. None dacă lipsește."""
    local = UNELTE_WHISPER / exe(nume)
    if local.is_file():
        return str(local)
    return shutil.which(nume)


def whisper_complet(dosar: Path) -> bool:
    """Copia de Windows e completă doar cu ambele executabile: o dezarhivare întreruptă poate lăsa doar unul."""
    return all((dosar / exe(n)).is_file() for n in WHISPER_EXE)


def model_whisper() -> Path:
    """Modelul Whisper folosit: EDITARE_MODEL (numele fișierului din modele/) sau large-v3-turbo."""
    return MODELE / os.environ.get("EDITARE_MODEL", MODEL_IMPLICIT)


def iesire_utf8() -> None:
    """Consola de Windows scrie implicit în cp1252 și se oprește la prima diacritică: trecem ieșirea pe UTF-8."""
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
