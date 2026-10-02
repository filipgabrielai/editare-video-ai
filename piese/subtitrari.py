"""Subtitrările cuvânt cu cuvânt: grupuri de cel mult 3 cuvinte, cuvântul spus e colorat."""
from __future__ import annotations

from procese.editare import scenariu as S

MAX_CAR = 22   # un grup de captions mai lung (la 58 px, centrat) ajunge peste butoanele din dreapta, de la x = 950


def grupuri(ws: list[dict], cuts: list[float], max_n: int = 3, max_car: int = MAX_CAR) -> list[list[dict]]:
    """Captions în grupuri de cel mult 3 cuvinte; grupul se închide la pauză (> 0,35 s), la tăietură și la punctuație.
    Trei cuvinte rostite în 0,14 s rămâneau aprinse peste celelalte, deci grupul se închide la 3 doar dacă a durat 0,35 s."""
    ws = [w for w in ws if w["text"]]
    out, cur = [], []
    for w in ws:
        if cur:
            gap = w["start"] - cur[-1]["end"]
            taiat = any(cur[-1]["start"] < c <= w["start"] + 0.02 for c in cuts)
            plin = len(cur) >= max_n and (cur[-1]["end"] - cur[0]["start"] >= 0.35 or len(cur) >= max_n + 2)
            lat = len(" ".join(x["text"] for x in cur + [w])) > max_car
            if plin or lat or gap > 0.35 or taiat or cur[-1]["text"].rstrip()[-1:] in ".,?!":
                out.append(cur)
                cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def captions(gr: list[list[dict]], durata: float, accent: str) -> tuple[list[str], list[str]]:
    html, js = [], []
    for gi, g in enumerate(gr):
        t_in = g[0]["start"] - 0.03
        t_out = min((gr[gi + 1][0]["start"] - 0.03) if gi + 1 < len(gr) else durata, g[-1]["end"] + 0.9)
        spans = "".join(f'<span class="cw" id="cw-{gi}-{k}">{S.esc(w["text"])}</span>' for k, w in enumerate(g))
        html.append(f'<div class="cap" id="cap-{gi}">{spans}</div>')
        d_in = max(0.04, min(0.18, (t_out - t_in) * 0.4))   # intrarea și ieșirea nu se suprapun, oricât de scurt e grupul
        t_off = max(t_in + d_in + 0.005, t_out - 0.12)
        d_off = max(0.02, t_out - t_off)
        js.append(f'tl.fromTo("#cap-{gi}", {{xPercent:-50, autoAlpha:0, y:14, scale:0.96}}, {{xPercent:-50, autoAlpha:1, y:0, scale:1, duration:{d_in:.3f}, ease:"power2.out"}}, {t_in:.3f});')
        js.append(f'tl.to("#cap-{gi}", {{autoAlpha:0, duration:{d_off:.3f}, ease:"power1.in", overwrite:"auto"}}, {t_off:.3f});')
        js.append(f'tl.set("#cap-{gi}", {{autoAlpha:0}}, {max(t_out, t_off + d_off) + 0.001:.3f});')
        for k, w in enumerate(g):
            t_w = max(w["start"] - 0.03, t_in)
            t_next = max(g[k + 1]["start"] - 0.03, t_in) if k + 1 < len(g) else t_w + 1
            d_w = max(0.01, min(0.10, t_next - t_w - 0.005))
            js.append(f'tl.to("#cw-{gi}-{k}", {{color:"{accent}", scale:1.05, duration:{d_w:.3f}, ease:"power2.out", overwrite:"auto"}}, {t_w:.3f});')
            if k:
                js.append(f'tl.to("#cw-{gi}-{k - 1}", {{color:"#ffffff", scale:1, duration:{d_w:.3f}, ease:"power2.out", overwrite:"auto"}}, {t_w:.3f});')
    return html, js
