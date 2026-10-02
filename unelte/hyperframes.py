"""HyperFrames pornit din Python: `node` direct pe intrarea pachetului, nu `npx` (pe Windows npx e un .cmd pe care cmd.exe
îl strică la căi cu spații), fără telemetrie, iar la planșe fără analiza cadrelor trimisă la Gemini (--describe false)."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from unelte import platforma

INTRARE = platforma.RADACINA / "node_modules" / "hyperframes" / "bin" / "hyperframes.mjs"


def comanda(*args: str) -> list[str]:
    node = shutil.which("node")
    if not node:
        raise SystemExit("Node.js lipsește: rulează verificarea (verificare/instalarea.py), îți spune cum îl instalezi.")
    return [node, str(INTRARE), *args]


def mediu() -> dict[str, str]:
    """Mediul proceselor HyperFrames: telemetria oprită (nimic nu pleacă de pe calculatorul omului) și o oră pentru encodare
    (limita implicită de 10 minute cădea la randări lungi, cu calculatorul încărcat). Ce a setat omul rămâne."""
    env = {**os.environ, "HYPERFRAMES_NO_TELEMETRY": "1"}
    env.setdefault("FFMPEG_ENCODE_TIMEOUT_MS", "3600000")
    return env


def args_randare(dosar: Path, iesire: Path, fps: int, calitate: str) -> list[str]:
    return ["render", str(dosar), "--fps", str(fps), "--quality", calitate, "-o", str(iesire)]


def args_snapshot(dosar: Path, momente: list[float], iesire: Path) -> list[str]:
    return ["snapshot", str(dosar), "--at", ",".join(f"{t:.2f}" for t in momente), "--no-end",
            "--describe", "false", "-o", str(iesire)]


def ruleaza(args: list[str], timeout: int = 3600, capteaza: bool = False) -> subprocess.CompletedProcess:
    """Cu intrarea închisă: cu ea deschisă, lint și snapshot rămâneau agățate când nu aveau un terminal în față."""
    if capteaza:
        return subprocess.run(comanda(*args), cwd=platforma.RADACINA, env=mediu(), timeout=timeout, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, encoding="utf-8", errors="replace")
    return subprocess.run(comanda(*args), cwd=platforma.RADACINA, env=mediu(), timeout=timeout, stdin=subprocess.DEVNULL)


def randeaza(dosar: Path, iesire: Path, fps: int = 60, calitate: str = "high") -> None:
    r = ruleaza(args_randare(dosar, iesire, fps, calitate))
    if r.returncode != 0:
        raise SystemExit(f"Randarea a eșuat (cod {r.returncode}); mesajele HyperFrames sunt mai sus.")


def lint(dosar: Path) -> tuple[bool, str]:
    r = ruleaza(["lint", str(dosar)], timeout=300, capteaza=True)
    return r.returncode == 0, (r.stdout or "") + (r.stderr or "")


def snapshot(dosar: Path, momente: list[float], iesire: Path) -> list[Path]:
    iesire.mkdir(parents=True, exist_ok=True)
    for vechi in [*iesire.glob("frame-*.png"), *iesire.glob("contact-sheet*.jpg")]:   # altfel planșa amestecă cadre din compoziția trecută
        vechi.unlink()
    r = ruleaza(args_snapshot(dosar, momente, iesire), timeout=1800, capteaza=True)
    if r.returncode != 0:
        coada = " ".join(((r.stderr or r.stdout) or "").strip().splitlines()[-3:])
        raise SystemExit(f"Planșele n-au ieșit: {coada}")
    return sorted(iesire.glob("frame-*.png"), key=lambda p: int(p.name.split("-")[1]))
