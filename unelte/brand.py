#!/usr/bin/env python3
"""Brandul și preferințele omului, scrise de /personalizare în brand/brand.json și aplicate peste stilul ales.

    python3 unelte/brand.py        verifică brand/brand.json și spune ce e setat (pe Windows: python)

Ce lipsește rămâne ca în stil (Studio) și în preferințele implicite. Logoul și fontul sunt fișierele omului, ținute în brand/
(ignorat de git); în proiect se copiază ca logo.<ext> și font.<ext>, ca numele cu spații și diacritice să nu ajungă în HTML.
"""
from __future__ import annotations

import copy
import difflib
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unelte import platforma  # noqa: E402

BRAND = platforma.RADACINA / "brand"
EXT_LOGO = (".png", ".svg", ".jpg", ".jpeg", ".webp")
EXT_FONT = (".woff2", ".woff", ".ttf", ".otf")
ALEGERI = {"carduri": ("putine", "normal"), "sunete": ("oprite", "incete", "normale"), "filtru_fata": ("niciunul", "usor", "mediu")}
FILTRE_FATA = {   # retușul din CapCut, aproximat: netezire doar pe zonele plate (pielea), plus puțină lumină; nu recunoaște fața
    "niciunul": "",
    "usor": "smartblur=lr=2.5:ls=0.7:lt=4,eq=brightness=0.015:gamma=1.03",
    "mediu": "smartblur=lr=4:ls=0.9:lt=6,eq=brightness=0.025:gamma=1.05:saturation=1.03",
}
VOLUM_SUNETE = {"oprite": 0.0, "incete": 0.5, "normale": 1.0}
FONTURI_REPO = {"geist": None, "instrument serif": "Instrument Serif"}   # fonturile libere din fonturi/; Geist e cel al stilului
IMPLICIT = {"nume": "", "culori": {"accent": None, "accent_2": None}, "font": None, "logo": None, "cta": "", "vocabular": [],
            "preferinte": {"captions": True, "carduri": "normal", "sunete": "normale", "filtru_fata": "niciunul", "limba": "ro"}}


def _fara_semne(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _simplu(s: str) -> str:
    return _fara_semne(s.lower()).strip()


def culoare(v) -> str | None:
    """'#3BF' sau '#38bdf8' (cu sau fără #) → '#38bdf8'; altceva → None."""
    if not isinstance(v, str):
        return None
    m = re.fullmatch(r"#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", v.strip())
    if not m:
        return None
    h = m.group(1).lower()
    return "#" + ("".join(c * 2 for c in h) if len(h) == 3 else h)


def rgb(hexa: str) -> str:
    return ",".join(str(int(hexa[i:i + 2], 16)) for i in (1, 3, 5))


def _necunoscute(date: dict, stiute, prefix: str = "") -> list[str]:
    """O cheie scrisă greșit („sunet” în loc de „sunete”) ar lăsa implicitul fără să spună nimic: o spunem, cu sugestie."""
    out = []
    for k in date:
        if k not in stiute:
            aproape = difflib.get_close_matches(str(k), list(stiute), n=1)
            out.append(f"câmp necunoscut „{prefix}{k}”" + (f" (voiai „{aproape[0]}”?)" if aproape else ""))
    return out


def font_din_repo(b: dict) -> bool:
    return b["font"] in FONTURI_REPO.values() and b["font"] is not None


def combina(date) -> tuple[dict, list[str]]:
    """Brandul complet (implicitele + ce a scris omul, normalizat) și greșelile, în română."""
    b = copy.deepcopy(IMPLICIT)
    if not isinstance(date, dict):
        return b, ["brand.json trebuie să fie un obiect JSON ({...})"]
    erori = _necunoscute(date, IMPLICIT)
    date = dict(date)
    for k, exemplu in (("culori", '{"accent": "#38bdf8", "accent_2": "#2563eb"}'), ("preferinte", '{"captions": true, "sunete": "normale"}')):
        if k in date and not isinstance(date[k], dict):
            erori.append(f"„{k}” e un obiect, de exemplu {exemplu}")
            del date[k]
        elif k in date:
            erori += _necunoscute(date[k], IMPLICIT[k], f"{k}.")
    for k in ("nume", "cta"):
        if k in date:
            if isinstance(date[k], str):
                b[k] = date[k].strip()
            else:
                erori.append(f"„{k}” trebuie să fie text")
    for k in ("accent", "accent_2"):
        v = (date.get("culori") or {}).get(k)
        if v is not None:
            c = culoare(v)
            if c:
                b["culori"][k] = c
            else:
                erori.append(f"culori.{k} = {v!r}: scrie culoarea în hex, de exemplu „#38bdf8”")
    for k, ext in (("logo", EXT_LOGO), ("font", EXT_FONT)):
        v = date.get(k)
        if v:
            if k == "font" and isinstance(v, str) and _simplu(v) in FONTURI_REPO:
                b[k] = FONTURI_REPO[_simplu(v)]
            elif isinstance(v, str) and Path(v).suffix.lower() in ext:
                b[k] = v
            elif k == "font":
                erori.append(f"„font” e „Geist”, „Instrument Serif” sau numele unui fișier din brand/ ({', '.join(ext)})")
            else:
                erori.append(f"„{k}” e numele unui fișier din brand/ ({', '.join(ext)})")
    if "vocabular" in date:
        v = date["vocabular"].split(",") if isinstance(date["vocabular"], str) else date["vocabular"]
        if isinstance(v, list) and all(isinstance(x, str) for x in v):
            b["vocabular"] = [x.strip() for x in v if x.strip()][:40]
        else:
            erori.append('„vocabular” e o listă de cuvinte, de exemplu ["Claude Code", "AI"]')
    pref = date.get("preferinte") or {}
    if "captions" in pref:
        if isinstance(pref["captions"], bool):
            b["preferinte"]["captions"] = pref["captions"]
        else:
            erori.append("preferinte.captions e true sau false")
    for k, ok in ALEGERI.items():
        if k in pref:
            v = _simplu(str(pref[k]))
            if v in ok:
                b["preferinte"][k] = v
            else:
                erori.append(f"preferinte.{k} = {pref[k]!r}: alege una din {', '.join(ok)}")
    if "limba" in pref:
        v = str(pref["limba"]).strip().lower()
        if re.fullmatch(r"[a-z]{2}", v):
            b["preferinte"]["limba"] = v
        else:
            erori.append(f"preferinte.limba = {pref['limba']!r}: codul limbii din două litere, de exemplu „ro” sau „en”")
    return b, erori


def incarca(dosar: Path | None = None) -> dict:
    """brand/brand.json combinat cu implicitele. Fără fișier: implicitele. Cu greșeli: se oprește și spune exact ce e greșit."""
    dosar = dosar or BRAND
    f = dosar / "brand.json"
    if not f.is_file():
        return copy.deepcopy(IMPLICIT)
    try:
        date = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"brand/brand.json nu e JSON valid (rândul {e.lineno}): {e.msg}. Rulează /personalizare ca să-l rescrii.") from None
    b, erori = combina(date)
    for k in ("logo", "font"):
        if b[k] and not (k == "font" and font_din_repo(b)) and not (dosar / b[k]).is_file():
            erori.append(f"„{k}”: fișierul {b[k]} nu e în brand/")
    if erori:
        raise SystemExit("brand/brand.json are greșeli:\n" + "\n".join("- " + x for x in erori))
    return b


def stil(st: dict, b: dict) -> dict:
    """Stilul ales cu accentul omului peste el (captions și chipurile își iau culoarea din JS, nu din CSS)."""
    st = dict(st)
    if b["culori"]["accent"]:
        st["accent"] = b["culori"]["accent"]
        st["accent_rgb"] = rgb(b["culori"]["accent"])
    return st


def css(b: dict) -> str:
    """brand.css, pus după stilul ales: culorile și fontul omului. Gol dacă n-a setat nimic."""
    linii, var = [], []
    if font_din_repo(b):   # Instrument Serif are o singură greutate: fără bold sintetic pe carduri și captions
        var.append(f"--font-display:'{b['font']}','Geist','Helvetica Neue',Arial,sans-serif")
        linii.append(".card .et,.card .et b,.cw,#titlu,.chip span{font-weight:400}")
    elif b["font"]:
        linii.append(f"@font-face{{font-family:'Brand';src:url('brand/font{Path(b['font']).suffix.lower()}');font-display:block}}")
        var.append("--font-display:'Brand','Geist','Helvetica Neue',Arial,sans-serif")
    if b["culori"]["accent"]:
        var += [f"--accent:{b['culori']['accent']}", f"--accent-rgb:{rgb(b['culori']['accent'])}"]
    if b["culori"]["accent_2"]:
        var.append(f"--accent-2:{b['culori']['accent_2']}")
    if var:
        linii.append(":root{" + ";".join(var) + "}")
    return "".join(x + "\n" for x in linii)


def copiaza(b: dict, assets: Path, dosar: Path | None = None) -> None:
    dosar = dosar or BRAND
    tinta = assets / "brand"
    tinta.mkdir(parents=True, exist_ok=True)
    for k in ("logo", "font"):
        if b[k] and not (k == "font" and font_din_repo(b)):
            shutil.copy(dosar / b[k], tinta / f"{k}{Path(b[k]).suffix.lower()}")


def logo_html(b: dict) -> str:
    return f'<img class="kl" src="assets/brand/logo{Path(b["logo"]).suffix.lower()}" alt="">' if b["logo"] else ""


def sunete(lista: list[tuple[float, str, float, float]], b: dict) -> list[tuple[float, str, float, float]]:
    f = VOLUM_SUNETE[b["preferinte"]["sunete"]]
    return [] if f == 0 else [(t, n, round(v * f, 3), d) for t, n, v, d in lista]


def filtru_fata(b: dict) -> str:
    return FILTRE_FATA[b["preferinte"]["filtru_fata"]]


def limba(b: dict) -> str:
    return b["preferinte"]["limba"]


def prompt_whisper(b: dict, in_plus: str = "") -> str:
    """Vocabularul dat lui Whisper din start (numele de unelte, „AI”): le scrie corect în loc de „despre ei” sau „un LTE-AI”.
    Pe Windows, fără diacritice: whisper.cpp citește argumentele în codepage-ul vechi și „ș” ar ajunge „?”."""
    cuvinte = b["vocabular"] + [x.strip() for x in in_plus.split(",") if x.strip()]
    if not cuvinte:
        return ""
    text = ", ".join(cuvinte) + "."
    return _fara_semne(text) if platforma.sistem() == "windows" else text


def rezumat(b: dict) -> str:
    p = b["preferinte"]
    return "\n".join([
        f"nume: {b['nume'] or '-'}",
        f"culori: {b['culori']['accent'] or 'ca stilul'} / {b['culori']['accent_2'] or 'ca stilul'}",
        f"font: {b['font'] or 'Geist (al stilului)'}",
        f"logo: {b['logo'] or '-'}",
        f"CTA: {b['cta'] or '-'}",
        f"vocabular: {', '.join(b['vocabular']) or '-'}",
        f"captions: {'da' if p['captions'] else 'nu'} · carduri: {p['carduri']} · sunete: {p['sunete']} · "
        f"filtru pe față: {p['filtru_fata']} · limba: {p['limba']}",
    ])


def main(argv: list[str] | None = None) -> int:
    platforma.iesire_utf8()
    print(rezumat(incarca()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
