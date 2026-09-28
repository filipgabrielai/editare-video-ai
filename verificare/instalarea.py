#!/usr/bin/env python3
"""Verifică dacă ai tot ce trebuie ca să editezi și îți spune exact ce lipsește și cum îl instalezi.

    python3 verificare/instalarea.py              (pe Windows: python verificare/instalarea.py)
    python3 verificare/instalarea.py --fara-disc  fără verificarea spațiului liber (în testele automate)

Codul de ieșire e 0 doar dacă totul e în regulă.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unelte import platforma  # noqa: E402

GB = 1024 ** 3
DISC_MINIM_GB = 10
PYTHON_MINIM = (3, 10)
NODE_MINIM = (22,)
DUPA_WINGET = " (după instalare, închide și redeschide Claude Code, ca Windows să-l vadă)"

REPARA = {
    "homebrew": {"mac": 'deschide aplicația Terminal și rulează: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
                        " (îți cere parola de la Mac; urmează pașii „Next steps” de la final), apoi închide și redeschide Claude Code"},
    "python": {"mac": "brew install python", "windows": "winget install -e --id Python.Python.3.12"},
    "node": {"mac": "brew install node", "windows": "winget install -e --id OpenJS.NodeJS.LTS"},
    "ffmpeg": {"mac": "brew install ffmpeg", "windows": "winget install -e --id Gyan.FFmpeg"},
    "whisper": {"mac": "brew install whisper-cpp", "windows": "{py} instalare/descarca.py whisper"},
    "whisper_porneste": {"mac": "brew reinstall whisper-cpp",
                         "windows": "winget install -e --id Microsoft.VCRedist.2015+.x64 (bibliotecile Microsoft de care are nevoie whisper.cpp)"},
    "model": {"*": "{py} instalare/descarca.py model"},
    "pachete": {"*": "npm install"},
    "disc": {"*": f"fă loc pe disc: ai nevoie de cel puțin {DISC_MINIM_GB} GB liberi"},
}


@dataclass
class Verificare:
    nume: str
    ok: bool
    detaliu: str
    repara: str = ""


def versiune(text: str) -> tuple[int, ...] | None:
    """Prima versiune de forma 1.2 sau 1.2.3 din text ('v22.11.0' -> (22, 11, 0))."""
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text or "")
    if not m:
        return None
    return tuple(int(x) for x in m.groups() if x is not None)


def cel_putin(v: tuple[int, ...] | None, minim: tuple[int, ...]) -> bool:
    return v is not None and tuple(v[:len(minim)]) >= minim


def repara(cheie: str, sis: str | None = None) -> str:
    """Comanda de reparat pentru sistemul dat (implicit, cel curent)."""
    sis = sis or platforma.sistem()
    optiuni = REPARA[cheie]
    comanda = (optiuni.get(sis) or optiuni.get("*", "")).replace("{py}", "python" if sis == "windows" else "python3")
    if sis == "windows" and comanda.startswith("winget"):
        comanda += DUPA_WINGET
    return comanda


def ruleaza(args: list[str]) -> str | None:
    """Ieșirea unei comenzi (stdout + stderr) sau None dacă nu pornește."""
    try:
        r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return (r.stdout or "") + (r.stderr or "")


BREW_CAI = (Path("/opt/homebrew/bin/brew"), Path("/usr/local/bin/brew"))   # Apple Silicon, Intel


def ruleaza_cu_cod(args: list[str]) -> tuple[int | None, str]:
    """Codul de ieșire și ieșirea unei comenzi; (None, motivul) dacă nu pornește deloc."""
    try:
        r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, str(e)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def verifica_homebrew(cai: tuple[Path, ...] = BREW_CAI) -> Verificare | None:
    """Homebrew îl instalează omul în Terminal (cere parola). Pe Apple Silicon, după instalare, brew nu e în PATH până nu
    adaugă linia shellenv în ~/.zprofile: atunci îi spunem exact linia, nu din nou comanda de instalare."""
    if platforma.sistem() != "mac":
        return None
    if shutil.which("brew"):
        return Verificare("Homebrew", True, "instalat")
    for cale in cai:
        if cale.is_file():
            return Verificare("Homebrew", False, f"instalat în {cale.parent}, dar Terminalul încă nu-l vede",
                              f"deschide aplicația Terminal și rulează: echo 'eval \"$({cale} shellenv)\"' >> ~/.zprofile"
                              ", apoi închide și redeschide Claude Code")
    return Verificare("Homebrew", False, "lipsește (cu el se instalează restul pe Mac)", repara("homebrew"))


def verifica_python(v: tuple[int, ...] = tuple(sys.version_info[:3])) -> Verificare:
    ok = cel_putin(v, PYTHON_MINIM)
    detaliu = ".".join(map(str, v)) + ("" if ok else f" (trebuie cel puțin {PYTHON_MINIM[0]}.{PYTHON_MINIM[1]})")
    return Verificare("Python", ok, detaliu, "" if ok else repara("python"))


def verifica_node() -> Verificare:
    cale = shutil.which("node")
    v = versiune(ruleaza([cale, "--version"]) or "") if cale else None
    ok = cel_putin(v, NODE_MINIM)
    if not cale:
        detaliu = "lipsește"
    elif not ok:
        detaliu = f"{'.'.join(map(str, v)) if v else 'versiune necunoscută'} (trebuie cel puțin {NODE_MINIM[0]})"
    else:
        detaliu = ".".join(map(str, v))
    return Verificare("Node.js", ok, detaliu, "" if ok else repara("node"))


def encodere_lipsa(text: str) -> list[str]:
    """Encoderele care lipsesc din 'ffmpeg -encoders': libx264 (video) și aac (sunet)."""
    return [enc for enc in ("libx264", "aac") if not re.search(rf"\s{enc}\s", text or "")]


def verifica_ffmpeg() -> Verificare:
    ff, fp = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ff or not fp:
        lipsa = " și ".join(n for n, c in (("ffmpeg", ff), ("ffprobe", fp)) if not c)
        return Verificare("ffmpeg", False, f"lipsește {lipsa}", repara("ffmpeg"))
    lipsa = encodere_lipsa(ruleaza([ff, "-hide_banner", "-encoders"]) or "")
    if lipsa:
        return Verificare("ffmpeg", False, f"instalat, dar fără {', '.join(lipsa)} (îți trebuie varianta completă)", repara("ffmpeg"))
    return Verificare("ffmpeg", True, "instalat, cu libx264 și aac")


def verifica_whisper(ruleaza_cod=ruleaza_cu_cod) -> Verificare:
    """Nu ajunge să existe fișierul: whisper-cli.exe poate să nu pornească (biblioteci Microsoft lipsă, antivirus). Îl pornim."""
    lipsa = [n for n in platforma.WHISPER_EXE if not platforma.gaseste(n)]
    if lipsa:
        return Verificare("whisper.cpp", False, "lipsește " + ", ".join(lipsa), repara("whisper"))
    cod, iesire = ruleaza_cod([platforma.gaseste("whisper-cli"), "--help"])
    if cod != 0:
        coada = " ".join((iesire or "").strip().splitlines()[-2:])[:200] or f"cod {cod}"
        return Verificare("whisper.cpp", False, f"instalat, dar nu pornește ({coada})", repara("whisper_porneste"))
    return Verificare("whisper.cpp", True, "instalat și pornește")


def verifica_model(cale: Path | None = None) -> Verificare:
    cale = cale or platforma.model_whisper()
    if not cale.is_file():
        return Verificare("Modelul Whisper", False, f"lipsește ({cale.name})", repara("model"))
    asteptat = platforma.MARIMI_MODEL.get(cale.name)
    marime = cale.stat().st_size
    if asteptat and marime != asteptat:
        return Verificare("Modelul Whisper", False,
                          f"{cale.name} e incomplet ({marime / GB:.2f} din {asteptat / GB:.2f} GB), descarcă-l din nou", repara("model"))
    return Verificare("Modelul Whisper", True, f"{cale.name} ({marime / GB:.2f} GB)")


def verifica_pachete(radacina: Path | None = None) -> Verificare:
    radacina = radacina or platforma.RADACINA
    ok = (radacina / "node_modules" / "hyperframes" / "package.json").is_file()
    return Verificare("Pachetele (HyperFrames)", ok, "instalate" if ok else "lipsesc", "" if ok else repara("pachete"))


def verifica_disc(liber: int | None = None) -> Verificare:
    liber = shutil.disk_usage(platforma.RADACINA).free if liber is None else liber
    ok = liber >= DISC_MINIM_GB * GB
    detaliu = f"{liber / GB:.0f} GB liberi" + ("" if ok else f" (trebuie cel puțin {DISC_MINIM_GB})")
    return Verificare("Spațiu pe disc", ok, detaliu, "" if ok else repara("disc"))


def toate(cu_disc: bool = True) -> list[Verificare]:
    lista = [verifica_homebrew(), verifica_python(), verifica_node(), verifica_ffmpeg(),
             verifica_whisper(), verifica_model(), verifica_pachete()]
    if cu_disc:
        lista.append(verifica_disc())
    return [v for v in lista if v is not None]


def main(argv: list[str] | None = None) -> int:
    platforma.iesire_utf8()
    argv = sys.argv[1:] if argv is None else argv
    rezultate = toate(cu_disc="--fara-disc" not in argv)
    for v in rezultate:
        print(f"[{'ok' if v.ok else 'lipsește'}] {v.nume}: {v.detaliu}")
        if v.repara:
            print(f"      cum repari: {v.repara}")
    lipsa = [v.nume for v in rezultate if not v.ok]
    if lipsa:
        print("\nMai ai de rezolvat: " + ", ".join(lipsa) + ".")
        return 1
    print("\nTotul e instalat. Urmează proba de 30 de secunde: " + ("python" if platforma.sistem() == "windows" else "python3") + " tests/proba_30s.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
