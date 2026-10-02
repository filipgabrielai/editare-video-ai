"""Piesele unei compoziții. Ale kitului stau aici; ale omului, în piese/ale-mele/ (nu intră în git, ca brandul, deci o
actualizare a kitului nu le atinge). O piesă a omului cu numele unei piese puse din "momente" (acum: cuvant) o înlocuiește;
piesele de bază (cardurile, titlul, subtitrările, zoomul) au locul lor în scenariu și nu se înlocuiesc de acolo."""
from __future__ import annotations

import importlib
import importlib.util
import re
from pathlib import Path

ALE_MELE = Path(__file__).resolve().parent / "ale-mele"
DIN_KIT = ("cuvant",)   # piesele kitului care se pun din "momente"
DE_BAZA = ("card", "titlu", "subtitrari", "zoom", "comun")   # au locul lor în scenariu; un fișier cu numele lor în ale-mele/ nu le înlocuiește


def nume_bun(nume) -> bool:
    return isinstance(nume, str) and bool(re.fullmatch(r"[a-z0-9_]+", nume))


def disponibile() -> list[str]:
    ale = [p.stem for p in ALE_MELE.glob("*.py") if nume_bun(p.stem) and not p.stem.startswith("_")] if ALE_MELE.is_dir() else []
    return sorted((set(ale) | set(DIN_KIT)) - set(DE_BAZA))


def incarca(nume: str):
    """Modulul piesei: întâi din piese/ale-mele/, apoi din kit."""
    f = ALE_MELE / f"{nume}.py"
    if nume in disponibile() and f.is_file():
        try:
            spec = importlib.util.spec_from_file_location(f"piese_ale_mele_{nume}", f)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception as e:   # greșeală de scriere, import care lipsește: se spune pe nume, nu cu un traceback
            raise SystemExit(f"Piesa „{nume}” (piese/ale-mele/{nume}.py) nu se poate încărca: {type(e).__name__}: {e}. "
                             "Modelul e piese/cuvant.py.") from None
    elif nume in DIN_KIT:
        mod = importlib.import_module(f"piese.{nume}")
    else:
        raise SystemExit(f"Piesa „{nume}” nu există (sunt: {', '.join(disponibile())}). O piesă nouă se scrie în "
                         f"piese/ale-mele/{nume}.py; cum, în docs/EXTINDERE.md.")
    if not callable(getattr(mod, "construieste", None)):
        raise SystemExit(f"Piesa „{nume}” nu are funcția construieste(ctx, m). Modelul e piese/cuvant.py.")
    return mod
