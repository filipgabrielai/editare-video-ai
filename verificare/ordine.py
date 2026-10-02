#!/usr/bin/env python3
"""Ordinea animațiilor și ce e vizibil când, înainte de randare. Randarea sare prin timeline pe mai mulți lucrători: un tween
care depinde de ce a rulat înaintea lui (yoyo + repeat urmat de overwrite:"auto" pe același element) arată bine la
previzualizare și greșit în mp4. Tot aici se vede un card care rămâne pe ecran peste intervalul lui.

    python3 verificare/ordine.py proiecte/<slug>
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unelte import hyperframes, platforma  # noqa: E402

SCRIPT = Path(__file__).with_suffix(".cjs")
MARJA_INTRARE, MARJA_IESIRE = 0.3, 0.6   # cardul iese în 0,28 s; măsurătoarea merge din 0,1 în 0,1 s
SELECTOR = ".card, #titlu, .piesa"       # ce se urmărește în tabelul de vizibilitate: cardurile, titlul și piesele din momente


def browser() -> str | None:
    """Browserul adus de HyperFrames pentru randare (același pe Mac și pe Windows). None dacă nu e descărcat încă."""
    try:
        r = hyperframes.ruleaza(["browser", "path"], timeout=120, capteaza=True)
    except (SystemExit, OSError, subprocess.TimeoutExpired):
        return None
    cale = next((x.strip() for x in reversed((r.stdout or "").splitlines()) if x.strip()), "")
    return cale if r.returncode == 0 and cale and Path(cale).is_file() else None


def masoara(pagina: Path, selector: str = SELECTOR) -> dict:
    exe = browser()
    if not exe:
        hyperframes.ruleaza(["browser", "ensure"], timeout=1800)
        exe = browser()
    if not exe:
        raise SystemExit("Browserul de randare lipsește și nu s-a putut descărca: rulează /instalare.")
    m = re.search(r'data-width="(\d+)" data-height="(\d+)"', pagina.read_text(encoding="utf-8"))
    w, h = m.groups() if m else ("1080", "1920")
    cmd = [hyperframes.comanda()[0], str(SCRIPT), str(platforma.RADACINA), str(pagina), exe, w, h, selector]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300, stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        raise SystemExit("Testul de ordine nu a pornit: " + " ".join((r.stderr or "").strip().splitlines()[-2:]))
    rez = json.loads(r.stdout)
    if rez.get("eroare"):
        raise SystemExit("Testul de ordine: " + rez["eroare"])
    return rez


def probleme(rez: dict, intervale: list[dict]) -> list[str]:
    out = []
    if rez["ndif"]:
        care = sorted({d[1] for d in rez["dif"]})
        out.append(f"{rez['ndif']} diferențe între parcurgerea înainte și cea amestecată, la: {', '.join(care)}. "
                   "Un tween depinde de ce a rulat înaintea lui (yoyo sau repeat urmat de overwrite pe același element)")
    for iv in intervale:
        v = rez["viz"].get(iv.get("el", f"c-{iv['id']}"))   # piesele din momente își spun elementul; cardurile sunt c-<id>
        ce = "piesa" if "el" in iv else "cardul"
        if v is None:
            continue
        if not v:
            out.append(f"{ce} „{iv['id']}” nu apare deloc pe ecran")
        elif v[0][0] < iv["intra"] - MARJA_INTRARE or v[-1][1] > iv["iese"] + MARJA_IESIRE:
            out.append(f"{ce} „{iv['id']}” se vede între {v[0][0]:.1f} și {v[-1][1]:.1f} s, dar e plănuit între "
                       f"{iv['intra']:.1f} și {iv['iese']:.1f} s")
    return out


def raport(rez: dict, intervale: list[dict]) -> str:
    linii = [f"ordine: {rez['n']} elemente în {rez['momente']} momente, {rez['ndif']} diferențe"]
    linii += [f"  {t:6.2f} s  {eid}: înainte {a} | amestecat {b}" for t, eid, a, b in rez["dif"]]
    linii.append("vizibil (secunde):")
    linii += [f"  {eid:14s} " + ("  ".join(f"{a:.1f}–{b:.1f}" for a, b in v) or "NICIODATĂ") for eid, v in rez["viz"].items()]
    p = probleme(rez, intervale)
    linii.append("TRECE" if not p else "NU TRECE: " + "; ".join(p))
    return "\n".join(linii)


def verifica(dosar: Path) -> bool:
    rez = masoara(dosar / "index.html")
    intervale = json.loads((dosar / "intervale.json").read_text(encoding="utf-8")) if (dosar / "intervale.json").is_file() else []
    print(raport(rez, intervale), flush=True)
    return not probleme(rez, intervale)


def main(argv: list[str] | None = None) -> int:
    platforma.iesire_utf8()
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        raise SystemExit("Folosire: ordine.py proiecte/<slug>")
    return 0 if verifica(Path(argv[0])) else 1


if __name__ == "__main__":
    sys.exit(main())
