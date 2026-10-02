"""Piesele unei compoziții. Ale kitului stau aici; ale omului, în piese/ale-mele/ (nu intră în git, ca brandul, deci o
actualizare a kitului nu le atinge). O piesă a omului cu numele uneia din kit o înlocuiește."""
from __future__ import annotations

import importlib
import importlib.util
import re
from pathlib import Path

ALE_MELE = Path(__file__).resolve().parent / "ale-mele"
DIN_KIT = ("cuvant",)   # piesele kitului care se pun din "momente" (cardurile, titlul și subtitrările au locul lor în scenariu)


def nume_bun(nume) -> bool:
    return isinstance(nume, str) and bool(re.fullmatch(r"[a-z0-9_]+", nume))


def disponibile() -> list[str]:
    ale = [p.stem for p in ALE_MELE.glob("*.py")] if ALE_MELE.is_dir() else []
    return sorted(set(ale) | set(DIN_KIT))


def incarca(nume: str):
    """Modulul piesei: întâi din piese/ale-mele/, apoi din kit."""
    f = ALE_MELE / f"{nume}.py"
    if nume_bun(nume) and f.is_file():
        spec = importlib.util.spec_from_file_location(f"piese_ale_mele_{nume}", f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    elif nume in DIN_KIT:
        mod = importlib.import_module(f"piese.{nume}")
    else:
        raise SystemExit(f"Piesa „{nume}” nu există (sunt: {', '.join(disponibile())}). O piesă nouă se scrie în "
                         f"piese/ale-mele/{nume}.py; cum, în docs/EXTINDERE.md.")
    if not callable(getattr(mod, "construieste", None)):
        raise SystemExit(f"Piesa „{nume}” nu are funcția construieste(ctx, m). Modelul e piese/cuvant.py.")
    return mod
