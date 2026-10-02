#!/usr/bin/env python3
"""Compoziția unui video: din scenariu.json, transcript.json și taieturi.json iese index.html pentru HyperFrames.

    python3 procese/editare/compozitie.py proiecte/<slug>

Piesele stau în piese/ (zoomul la tăieturi, titlul, cardurile, subtitrările); aici se asamblează, se aplică brandul și
preferințele omului, se scrie pagina, intervale.json (pentru planșe) și BEATS.md, apoi se rulează lint-ul HyperFrames.
"""
from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import piese  # noqa: E402
from piese import card, titlu, zoom  # noqa: E402
from piese.card import INALTIME_RAND  # noqa: E402,F401
from piese.comun import FPS, MIN_PAUZA, ROT, VOL, Context, Sunete  # noqa: E402,F401
from piese.subtitrari import MAX_CAR, captions, grupuri  # noqa: E402,F401
from procese.editare import scenariu as S  # noqa: E402
from unelte import brand, formate, hyperframes, platforma, proiect  # noqa: E402


def logouri_proiect(dosar: Path) -> dict[str, str]:
    """Logourile puse de om în proiecte/<slug>/logo/ (fișierele oficiale), după nume: {"claude": "claude.png"}."""
    d = dosar / "logo"
    if not d.is_dir():
        return {}
    return {p.stem: p.name for p in sorted(d.iterdir()) if p.suffix.lower() in (".png", ".svg", ".jpg", ".jpeg", ".webp")}


def logouri_lipsa(sc: dict, logouri: dict[str, str]) -> list[str]:
    erori = []
    for c in sc.get("carduri", []):
        for r in c.get("randuri", []):
            for n in ([r["logo"]] if isinstance(r.get("logo"), str) else r.get("logo") or []):
                if n not in logouri:
                    erori.append(f"logoul „{n}” lipsește: pune fișierul oficial (de pe site-ul lor) în proiecte/<slug>/logo/{n}.png sau .svg")
    return erori


def planifica(sc: dict, ws: list[dict], cuts: list[float], durata: float, st: dict, logouri: dict[str, str] | None = None,
              logo_brand: str = "", fmt: str = formate.IMPLICIT) -> dict:
    """Piesele compoziției, în ordinea în care se așază pe timeline: zoomul la tăieturi, titlul, cardurile, apoi momentele
    (piesele puse din scenariu, ale kitului sau ale omului)."""
    ctx = Context(sc=sc, ws=ws, cuts=cuts, durata=durata, st=st, logouri=logouri or {}, logo_brand=logo_brand, format=fmt)
    fr = [p.construieste(ctx) for p in (zoom, titlu, card)]
    ctx.cursor = 0.0   # ancorele momentelor se caută de la început, în ordinea în care sunt scrise
    fr += [moment(ctx, m) for m in sc.get("momente", [])]
    return {"html": [x for f in fr for x in f.html], "js": [x for f in fr for x in f.js], "sfx": ctx.sunete.lista,
            "beats": [x for f in fr for x in f.beats], "intervale": [x for f in fr for x in f.intervale],
            "css": list(dict.fromkeys(x for f in fr for x in f.css))}


def moment(ctx: Context, m: dict):
    """Fragmentul unui moment din scenariu. Regula pieselor: rădăcina are id-ul m-<id> și clasa „piesa”, iar toate celelalte
    id-uri încep cu m-<id>-. Așa o piesă a omului nu poate călca un element al kitului (un al doilea „titlu” ar fi animat
    de tween-urile titlului), iar testul de ordine și planșele o găsesc."""
    f = piese.incarca(m["piesa"]).construieste(ctx, m)
    mid = f"m-{m['id']}"
    html = "".join(f.html)
    straine = [i for i in re.findall(r'\bid="([^"]*)"', html) if i != mid and not i.startswith(mid + "-")]
    radacina = re.search(rf'<[^>]*\bid="{re.escape(mid)}"[^>]*>', html)
    if straine or not radacina or not re.search(r'\bclass="[^"]*\bpiesa\b', radacina.group(0)):
        raise SystemExit(f"Piesa „{m['piesa']}” (momentul „{m['id']}”): elementul ei de bază trebuie să aibă id=\"{mid}\" și clasa "
                         f"„piesa”, iar celelalte id-uri să înceapă cu {mid}-" + (f" (am găsit: {', '.join(straine)})" if straine else "")
                         + ". Vezi docs/EXTINDERE.md.")
    return f


def pozitii_negative(linii: list[str]) -> list[str]:
    """Liniile de timeline puse înainte de zero. Una singură ajunge ca GSAP să împingă tot timeline-ul cu atât: animațiile cad
    apoi după imagine și după sunet, cu un cadru sau două."""
    return [x for x in linii if re.search(r",\s*-\d[\d.]*\);\s*$", x)]


def aplica_preferinte(plan: dict, cap: tuple[list[str], list[str]], b: dict) -> tuple[list[str], list[str]]:
    """Preferințele omului peste plan: volumul sunetelor (sau fără), captions sau nu."""
    plan["sfx"] = brand.sunete(plan["sfx"], b)
    return cap if b["preferinte"]["captions"] else ([], [])


def mesaj_lint(ok: bool, iesire: str) -> str:
    """Când trece, ajunge ultima linie; când pică, tot, ca să se vadă ce regulă a picat și unde."""
    iesire = iesire.strip()
    if not iesire:
        return ""
    return iesire.splitlines()[-1] if ok else iesire


def stil_meu() -> bool:
    """Omul are un stil al lui peste al kitului: brand/stil.css."""
    return (brand.BRAND / "stil.css").is_file()


def pagina(sc: dict, plan: dict, cap_html: list[str], cap_js: list[str], durata: float, fmt: str = formate.IMPLICIT,
           stil_meu: bool = False) -> str:
    w, h = formate.dimensiuni(fmt)
    c = {**formate.CADRU[fmt], **({"carduri_y": formate.CARDURI_Y_CU_TITLU[fmt]} if sc.get("titlu") else {}), **sc.get("cadru", {})}
    compact_y = formate.COMPACT_Y[fmt][1 if sc.get("titlu") else 0]   # cu titlu, cardul compact stă sub el
    if fmt == "9:16":
        pozitii = f"--shift:{c['shift']}px;--carduri-y:{c['carduri_y']}px;--captions-y:{c['captions_y']}px;--compact-y:{compact_y}px"
    else:   # pe orizontală cardul stă lângă om, pe partea liberă a cadrului
        st, dr = (f"{formate.MARGINE_CARD}px", "auto") if c["carduri"] == "stanga" else ("auto", f"{formate.MARGINE_CARD}px")
        pozitii = f"--carduri-y:{c['carduri_y']}px;--captions-y:{c['captions_y']}px;--compact-y:{compact_y}px;--card-st:{st};--card-dr:{dr}"
    ds = dur_str(durata)
    in_plus = '\n<link rel="stylesheet" href="assets/stil-meu.css">' if stil_meu else ""   # stilul omului, peste brand
    if plan.get("css"):                                                                     # stilul pieselor din momente
        in_plus += "\n<style>\n" + "\n".join(plan["css"]) + "\n</style>"
    sfx = "\n".join(f'  <audio id="sfx-{i}" data-start="{t:.3f}" data-duration="{d:.3f}" data-track-index="{20 + i}" '
                    f'src="assets/sunete/{n}.wav" data-volume="{v}"></audio>' for i, (t, n, v, d) in enumerate(sorted(plan["sfx"])))
    linii_js = "\n".join("    " + x for x in plan["js"] + cap_js)
    return f"""<!doctype html>
<html lang="ro"><head><meta charset="utf-8"><title>{S.esc(sc.get("titlu") or "Reel")}</title>
<script src="assets/gsap.min.js"></script>
<link rel="stylesheet" href="assets/fonturi/fonturi.css">
<link rel="stylesheet" href="assets/stil.css">
<link rel="stylesheet" href="assets/brand.css">{in_plus}
</head><body>
<div id="reel" data-composition-id="reel" data-start="0" data-duration="{ds}" data-width="{w}" data-height="{h}"
  style="{pozitii}">
  <div id="fund" class="clip" data-start="0" data-duration="{ds}" data-track-index="0"></div>
  <div id="stage">
    <video id="vid" class="clip" data-start="0" data-duration="{ds}" data-track-index="1" src="taiat.mp4" muted playsinline></video>
  </div>
  <div id="umbra"></div>
  <div id="umbra2"></div>
  <audio id="voce" data-start="0" data-duration="{ds}" data-track-index="9" src="voce.wav" data-volume="1"></audio>
  {chr(10).join("  " + h for h in plan["html"])}
  <div id="captii">
  {chr(10).join("    " + h for h in cap_html)}
  </div>
{sfx}
</div>
<script>
  window.__timelines = window.__timelines || {{}};
  (function() {{
    const tl = gsap.timeline({{ paused: true }});
{linii_js}
    tl.set({{}}, {{}}, {ds});
    window.__timelines["reel"] = tl;
  }})();
</script>
</body></html>
"""


def pregateste_assets(dosar: Path, stil: str, b: dict | None = None, fmt: str = formate.IMPLICIT) -> None:
    b = b or brand.IMPLICIT
    rad = platforma.RADACINA
    a = dosar / "assets"
    (a / "fonturi").mkdir(parents=True, exist_ok=True)
    (a / "sunete").mkdir(exist_ok=True)
    shutil.copy(rad / "node_modules" / "gsap" / "dist" / "gsap.min.js", a / "gsap.min.js")
    shutil.copy(rad / "stiluri" / stil / formate.CSS[fmt], a / "stil.css")
    for f in (rad / "fonturi").glob("*.woff2"):
        shutil.copy(f, a / "fonturi" / f.name)
    shutil.copy(rad / "fonturi" / "fonturi.css", a / "fonturi" / "fonturi.css")
    for f in (rad / "sunete").glob("*.wav"):
        shutil.copy(f, a / "sunete" / f.name)
    if (dosar / "logo").is_dir():
        (a / "logo").mkdir(exist_ok=True)
        for f in (dosar / "logo").iterdir():
            if f.is_file():
                shutil.copy(f, a / "logo" / f.name)
    (a / "brand.css").write_text(brand.css(b), encoding="utf-8")
    (a / "stil-meu.css").unlink(missing_ok=True)
    if stil_meu():
        shutil.copy(brand.BRAND / "stil.css", a / "stil-meu.css")
    brand.copiaza(b, a)


def pe_grila(d: float) -> float:
    return round(d * FPS) / FPS


def dur_str(x: float) -> str:
    """Durata pentru data-duration, cu 4 zecimale, tăiată în jos: rotunjită, trece de granița de cadru și randarea adaugă un
    cadru la coadă, în care filmarea nu mai are imagine."""
    return f"{math.floor(x * 10000 + 1e-6) / 10000:.4f}"


def cadre_planificate(durata: float, fps: int) -> int:
    """Câte cadre randează HyperFrames pentru durata scrisă în pagină (rotunjește în sus)."""
    return math.ceil(float(dur_str(durata)) * fps - 1e-6)


def durata_video(f: Path) -> float:
    """Durata imaginii, pe grila de cadre. Durata fișierului e cu ~10 ms mai lungă (sunetul AAC)."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True, check=True)
    return pe_grila(float(r.stdout.strip().split(",")[0]))


def main(argv: list[str] | None = None) -> int:
    platforma.iesire_utf8()
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        raise SystemExit("Folosire: compozitie.py proiecte/<slug>")
    dosar = Path(argv[0])
    with open(dosar / "scenariu.json", encoding="utf-8") as f:
        sc = json.load(f)
    fmt = proiect.format_proiect(dosar, sc)
    erori, avert = S.valideaza(sc, fmt)
    logouri = logouri_proiect(dosar)
    erori += logouri_lipsa(sc, logouri)
    for x in avert:
        print("atenție:", x)
    if erori:
        print("\n".join("eroare: " + x for x in erori))
        return 1
    ws = S.corecteaza(S.cuvinte(dosar / "transcript.json"), sc.get("corecturi", {}))
    with open(dosar / "taieturi.json", encoding="utf-8") as f:
        cuts = json.load(f)["taieturi"]
    durata = durata_video(dosar / "taiat.mp4")
    b = brand.incarca()
    st = brand.stil(S.stil(sc["stil"]), b)
    plan = planifica(sc, ws, cuts, durata, st, logouri, brand.logo_html(b), fmt)
    cap_html, cap_js = aplica_preferinte(plan, captions(grupuri(ws, cuts, max_car=formate.MAX_CAR[fmt]), durata, st["accent"]), b)
    pregateste_assets(dosar, sc["stil"], b, fmt)
    if (negative := pozitii_negative(plan["js"] + cap_js)):
        print("eroare: animații puse înainte de secunda zero (ar împinge tot timeline-ul):\n  " + "\n  ".join(negative[:5]))
        return 1
    (dosar / "index.html").write_text(pagina(sc, plan, cap_html, cap_js, durata, fmt, stil_meu()), encoding="utf-8")
    with open(dosar / "intervale.json", "w", encoding="utf-8") as f:
        json.dump(plan["intervale"], f, indent=1)
    beats = ["# Beat-uri", "", "| t | ce apare |", "|---|---|"] + [f"| {t:.2f} | {x} |" for t, x in plan["beats"]]
    (dosar / "BEATS.md").write_text("\n".join(beats) + "\n", encoding="utf-8")
    ok, iesire = hyperframes.lint(dosar)
    print(mesaj_lint(ok, iesire))
    for t, x in plan["beats"]:
        print(f"  {t:6.2f}  {x}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
