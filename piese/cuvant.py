"""Un cuvânt mare care apare pe o ancoră și stă cât îi spui. E și modelul de la care pornești o piesă a ta: copiaz-o în
piese/ale-mele/ sub alt nume și schimb-o (docs/EXTINDERE.md).

În scenariu, la "momente": {"piesa": "cuvant", "id": "suta", "text": "100%", "ancora": "editat", "durata": 1.5}
Opțional: "pana_la" (fraza pe care iese, în locul duratei), "x" și "y" (centrul, în pixeli), "marime" (în pixeli).
"""
from __future__ import annotations

from piese.comun import Context, Fragment
from procese.editare import scenariu as S
from unelte import formate

# centrul și mărimea când scenariul nu le dă: pe 9:16 pe guler, chiar deasupra subtitrărilor (mai sus e fața, și mai sus
# cardurile); pe 16:9 pe partea opusă cardului. Locul bun depinde de cadru: se verifică pe planșe și se mută cu "x" și "y".
LOC = {"9:16": (540, 1395, 110), "16:9": (1440, 330, 130)}
CSS = (".cuvant{position:absolute;z-index:25;opacity:0;white-space:nowrap;font-weight:800;letter-spacing:-0.03em;line-height:1;"
       "color:var(--accent);text-shadow:0 6px 30px rgba(0,0,0,.6)}")


def construieste(ctx: Context, m: dict) -> Fragment:
    for cheie in ("text", "ancora"):
        if not m.get(cheie):
            raise SystemExit(f"Momentul „{m['id']}” (piesa cuvant) nu are „{cheie}”.")
    mid = f"m-{m['id']}"   # toate id-urile unei piese stau sub m-<id>: nu se calcă cu ale kitului
    x, y, marime = LOC[ctx.format]
    if ctx.format == "16:9" and ctx.sc.get("cadru", {}).get("carduri", "stanga") == "dreapta":
        x = formate.dimensiuni("16:9")[0] - x
    x, y, marime = m.get("x", x), m.get("y", y), m.get("marime", marime)
    t0 = max(0.0, ctx.ancora(m["ancora"]) - 0.03)   # timpii vin din transcript și nu coboară sub zero
    t1 = ctx.ancora(m["pana_la"]) if m.get("pana_la") else t0 + float(m.get("durata", 1.5))
    t1 = min(max(t1, t0 + 0.7), ctx.durata)         # intrarea (0,35 s) și ieșirea (0,2 s) nu se calcă
    ctx.sunete.adauga("pop", t0)
    return Fragment(
        html=[f'<div class="piesa cuvant" id="{mid}" style="left:{x}px;top:{y}px;font-size:{marime}px">{S.esc(m["text"])}</div>'],
        css=[CSS],
        js=[f'tl.fromTo("#{mid}", {{xPercent:-50, yPercent:-50, autoAlpha:0, scale:0.6}}, '
            f'{{xPercent:-50, yPercent:-50, autoAlpha:1, scale:1, duration:0.35, ease:"back.out(1.8)"}}, {t0:.3f});',
            f'tl.to("#{mid}", {{autoAlpha:0, scale:0.9, duration:0.2, ease:"power1.in"}}, {t1 - 0.2:.3f});'],
        beats=[(t0, f"cuvânt mare: {m['text']}")],
        intervale=[{"id": m["id"], "intra": round(t0, 3), "iese": round(t1, 3), "el": mid}])   # ca să apară pe planșe
