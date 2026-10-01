#!/usr/bin/env python3
"""Compoziția unui reel: din scenariu.json, transcript.json și taieturi.json iese index.html pentru HyperFrames.

    python3 procese/reel/compozitie.py proiecte/<slug>

Singură: captions cuvânt cu cuvânt (cuvântul spus e colorat), zoom ușor la fiecare tăietură (pe grila de cadre), umbra de sus,
sunetele în rotație. Din scenariu: titlul, cardurile, rândurile, chipurile, cifrele și cuvintele pe care intră. Reguli: primul
rând al unui card e static (un card care își așteaptă ancora nu stă gol); cardul iese cu 0,08 s înainte să intre următorul;
ultimul card rămâne până la final. Scrie și intervale.json (pentru planșe) și BEATS.md, apoi rulează lint-ul HyperFrames.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from procese.reel import scenariu as S  # noqa: E402
from unelte import hyperframes, platforma  # noqa: E402

FPS = 60
MAX_CAR = 22   # un grup de captions mai lung (la 58 px, centrat) ajunge peste butoanele din dreapta, de la x = 950
ROT = {"card": ["boom", "knock", "tok"], "pop": ["pop", "thump", "click"]}   # trei la carduri: cu două, Filip le auzea la fel
VOL = {"boom": (0.35, 0.6), "knock": (0.35, 0.2), "tok": (0.35, 0.16), "pop": (0.55, 0.12), "thump": (0.5, 0.25), "click": (0.55, 0.14)}   # volum, durată
MIN_PAUZA = 1.0   # între două sunete; sub asta Filip le-a găsit „cam dese”
INALTIME_RAND = {False: 84, True: 66}   # ca .card .row și .card.compact .row din stil


class Sunete:
    """Sunetele în rotație: niciodată același de două ori la rând, cel puțin o secundă între ele. Cardul are prioritate:
    un pop prea aproape de intrarea unui card nu se mai aude."""

    def __init__(self) -> None:
        self.lista: list[tuple[float, str, float, float]] = []
        self.contor = {"card": 0, "pop": 0}
        self.ultim: str | None = None

    def adauga(self, fel: str, t: float, vol: float | None = None) -> None:
        t = round(t * FPS) / FPS
        aproape = [x for x in self.lista if abs(t - x[0]) < MIN_PAUZA]
        if fel == "pop" and aproape:
            return
        if fel == "card":
            if any(x[1] in ROT["card"] for x in aproape):
                return
            self.lista = [x for x in self.lista if x not in aproape]
        rot = ROT[fel]
        nume = rot[self.contor[fel] % len(rot)]
        if nume == self.ultim:
            self.contor[fel] += 1
            nume = rot[self.contor[fel] % len(rot)]
        self.contor[fel] += 1
        self.ultim = nume
        v, d = VOL[nume]
        self.lista.append((t, nume, v if vol is None else vol, d))


def grupuri(ws: list[dict], cuts: list[float], max_n: int = 3) -> list[list[dict]]:
    """Captions în grupuri de cel mult 3 cuvinte; grupul se închide la pauză (> 0,35 s), la tăietură și la punctuație.
    Trei cuvinte rostite în 0,14 s rămâneau aprinse peste celelalte, deci grupul se închide la 3 doar dacă a durat 0,35 s."""
    ws = [w for w in ws if w["text"]]
    out, cur = [], []
    for w in ws:
        if cur:
            gap = w["start"] - cur[-1]["end"]
            taiat = any(cur[-1]["start"] < c <= w["start"] + 0.02 for c in cuts)
            plin = len(cur) >= max_n and (cur[-1]["end"] - cur[0]["start"] >= 0.35 or len(cur) >= max_n + 2)
            lat = len(" ".join(x["text"] for x in cur + [w])) > MAX_CAR
            if plin or lat or gap > 0.35 or taiat or cur[-1]["text"].rstrip()[-1:] in ".,?!":
                out.append(cur)
                cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


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


def planifica(sc: dict, ws: list[dict], cuts: list[float], durata: float, st: dict, logouri: dict[str, str] | None = None) -> dict:
    js: list[str] = []
    html: list[str] = []
    beats: list[tuple[float, str]] = []
    intervale: list[dict] = []
    sun = Sunete()
    cursor = [0.0]
    rgb = st["accent_rgb"]

    def A(fraza: str, inapoi: float = 0.4) -> float:
        t = S.gaseste(ws, fraza, max(0.0, cursor[0] - inapoi))[0]
        cursor[0] = t
        return t

    for i, c in enumerate(cuts):
        js.append(f'tl.set("#stage", {{scale:{1.06 if i % 2 == 0 else 1.0}}}, {round(c * FPS) / FPS - 0.001:.4f});')
    if sc.get("titlu"):
        html.append(f'<div id="titlu">{S.esc(sc["titlu"])}</div>')
        js.append('tl.fromTo("#titlu", {autoAlpha:0, y:-12}, {autoAlpha:1, y:0, duration:0.45, ease:"power2.out"}, 0.05);')

    carduri = sc["carduri"]
    intrari = []
    for c in carduri:
        intrari.append(0.05 if c["ancora"] == "start" else A(c["ancora"]) - 0.05)
    umbra_scurta = False
    for k, c in enumerate(carduri):
        t0 = intrari[k]
        t1 = intrari[k + 1] - 0.08 if k + 1 < len(carduri) else durata
        cid = f"c-{c['id']}"
        corp = []
        for r_i, r in enumerate(c.get("randuri", [])):
            if r.get("logo"):
                nume = [r["logo"]] if isinstance(r["logo"], str) else r["logo"]
                ico = '<span class="lgs">' + "".join(
                    f'<img class="lg{" inv" if n in sc.get("logo_inversat", []) else ""}" src="assets/logo/{S.esc((logouri or {}).get(n, n))}" alt="">'
                    for n in nume) + "</span>"
            else:
                ico = f'<span class="ic">{S.ICOANE[r["icoana"]]}</span>' if r.get("icoana") else ""
            ascuns = " ascuns" if r_i > 0 and r.get("ancora") else ""
            corp.append(f'<div class="row{ascuns}" id="{cid}-r{r_i}">{ico}<span class="et">{S.markup(r["text"])}</span></div>')
        if c.get("chips"):
            corp.append('<div class="row chips">' + "".join(
                f'<span class="chip" id="{cid}-ch{j}"><span>{S.esc(ch["text"])}</span></span>' for j, ch in enumerate(c["chips"])) + "</div>")
        if c.get("cifra"):
            corp.append(f'<div class="row"><span class="cifra" id="{cid}-cifra">{S.esc(c["cifra"]["valoare"])}</span></div>')
        cls = "card compact" if c.get("compact") else "card"
        html.append(f'<div class="{cls}" id="{cid}"><div class="k">{S.esc(c["kicker"])}</div>{"".join(corp)}</div>')
        js.append(f'tl.fromTo("#{cid}", {{xPercent:-50, autoAlpha:0, y:-26, scale:0.94, filter:"blur(10px)"}}, '
                  f'{{xPercent:-50, autoAlpha:1, y:0, scale:1, filter:"blur(0px)", duration:0.5, ease:"back.out(1.3)"}}, {t0:.3f});')
        sun.adauga("card", t0, 0.6 if k == 0 else None)
        if k + 1 < len(carduri):
            js.append(f'tl.to("#{cid}", {{autoAlpha:0, y:-30, scale:0.96, duration:0.28, ease:"power1.in"}}, {t1:.3f});')
        if bool(c.get("compact")) != umbra_scurta:   # pe înregistrări de ecran, doar banda de sus, nu umbra lungă
            umbra_scurta = bool(c.get("compact"))
            js.append(f'tl.set("#umbra", {{autoAlpha:{0 if umbra_scurta else 1}}}, {t0:.3f});')
            js.append(f'tl.set("#umbra2", {{autoAlpha:{1 if umbra_scurta else 0}}}, {t0:.3f});')
        cursor[0] = t0 + 0.05
        for r_i, r in enumerate(c.get("randuri", [])):
            if r_i > 0 and r.get("ancora"):
                tr = max(t0 + 0.35, A(r["ancora"]) - 0.03)
                h = INALTIME_RAND[bool(c.get("compact"))]   # cât primul rând, ca distanța dintre rânduri să fie egală
                js.append(f'tl.fromTo("#{cid}-r{r_i}", {{height:0, minHeight:0, autoAlpha:0, x:-18}}, '
                          f'{{height:{h}, minHeight:{h}, autoAlpha:1, x:0, duration:0.32, ease:"power2.out"}}, {tr:.3f});')
                sun.adauga("pop", tr)
        mod = c.get("chips_mod", "aprinde")
        for j, ch in enumerate(c.get("chips", [])):
            sel = f"#{cid}-ch{j}"
            tc = max(t0 + 0.2, A(ch["ancora"]) - 0.03) if ch.get("ancora") else t0 + 0.2
            if mod == "apar":
                js.append(f'tl.fromTo("{sel}", {{autoAlpha:0, scale:0.5, y:10}}, {{autoAlpha:1, scale:1, y:0, duration:0.45, ease:"back.out(2)"}}, {tc:.3f});')
                js.append(f'tl.set("{sel}", {{backgroundColor:"rgba({rgb},.12)", borderColor:"rgba({rgb},.5)", color:"#ffffff"}}, {tc:.3f});')
            else:
                js.append(f'tl.set("{sel}", {{autoAlpha:1}}, {t0:.3f});')
                js.append(f'tl.fromTo("{sel}", {{backgroundColor:"rgba(148,163,184,.08)", borderColor:"rgba(148,163,184,.3)", color:"#94a3b8"}}, '
                          f'{{backgroundColor:"rgba({rgb},.18)", borderColor:"rgba({rgb},.8)", color:"#ffffff", duration:0.2, immediateRender:false}}, {tc:.3f});')
            sun.adauga("pop", tc)
        if c.get("cifra"):
            tf = max(t0 + 0.2, A(c["cifra"]["ancora"]) - 0.03) if c["cifra"].get("ancora") else t0 + 0.2
            js.append(f'tl.fromTo("#{cid}-cifra", {{autoAlpha:0, scale:0.6}}, {{autoAlpha:1, scale:1, duration:0.4, ease:"back.out(2)"}}, {tf:.3f});')
            sun.adauga("pop", tf)
        text_beat = " / ".join(S._text_simplu(r["text"]) for r in c.get("randuri", [])) or " · ".join(ch["text"] for ch in c.get("chips", []))
        beats.append((t0, f"{c['kicker']}: {text_beat}"))
        intervale.append({"id": c["id"], "intra": round(t0, 3), "iese": round(t1, 3)})
    return {"html": html, "js": js, "sfx": sun.lista, "beats": beats, "intervale": intervale}


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


def mesaj_lint(ok: bool, iesire: str) -> str:
    """Când trece, ajunge ultima linie; când pică, tot, ca să se vadă ce regulă a picat și unde."""
    iesire = iesire.strip()
    if not iesire:
        return ""
    return iesire.splitlines()[-1] if ok else iesire


def pagina(sc: dict, plan: dict, cap_html: list[str], cap_js: list[str], durata: float) -> str:
    c = {"shift": 120, "carduri_y": 370 if sc.get("titlu") else 280, "captions_y": 1480, **sc.get("cadru", {})}
    compact_y = 340 if sc.get("titlu") else S.ZONA_SUS   # cu titlu (262–330 px), cardul compact stă sub el
    sfx = "\n".join(f'  <audio id="sfx-{i}" data-start="{t:.3f}" data-duration="{d:.3f}" data-track-index="{20 + i}" '
                    f'src="assets/sunete/{n}.wav" data-volume="{v}"></audio>' for i, (t, n, v, d) in enumerate(sorted(plan["sfx"])))
    linii_js = "\n".join("    " + x for x in plan["js"] + cap_js)
    return f"""<!doctype html>
<html lang="ro"><head><meta charset="utf-8"><title>{S.esc(sc.get("titlu") or "Reel")}</title>
<script src="assets/gsap.min.js"></script>
<link rel="stylesheet" href="assets/fonturi/fonturi.css">
<link rel="stylesheet" href="assets/stil.css">
</head><body>
<div id="reel" data-composition-id="reel" data-start="0" data-duration="{durata:.3f}" data-width="1080" data-height="1920"
  style="--shift:{c['shift']}px;--carduri-y:{c['carduri_y']}px;--captions-y:{c['captions_y']}px;--compact-y:{compact_y}px">
  <div id="fund" class="clip" data-start="0" data-duration="{durata:.3f}" data-track-index="0"></div>
  <div id="stage">
    <video id="vid" class="clip" data-start="0" data-duration="{durata:.3f}" data-track-index="1" src="taiat.mp4" muted playsinline></video>
  </div>
  <div id="umbra"></div>
  <div id="umbra2"></div>
  <audio id="voce" data-start="0" data-duration="{durata:.3f}" data-track-index="9" src="voce.wav" data-volume="1"></audio>
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
    tl.set({{}}, {{}}, {durata:.3f});
    window.__timelines["reel"] = tl;
  }})();
</script>
</body></html>
"""


def pregateste_assets(dosar: Path, stil: str) -> None:
    rad = platforma.RADACINA
    a = dosar / "assets"
    (a / "fonturi").mkdir(parents=True, exist_ok=True)
    (a / "sunete").mkdir(exist_ok=True)
    shutil.copy(rad / "node_modules" / "gsap" / "dist" / "gsap.min.js", a / "gsap.min.js")
    shutil.copy(rad / "stiluri" / stil / "reel.css", a / "stil.css")
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


def durata_video(f: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def main(argv: list[str] | None = None) -> int:
    platforma.iesire_utf8()
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        raise SystemExit("Folosire: compozitie.py proiecte/<slug>")
    dosar = Path(argv[0])
    with open(dosar / "scenariu.json", encoding="utf-8") as f:
        sc = json.load(f)
    erori, avert = S.valideaza(sc)
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
    st = S.stil(sc["stil"])
    plan = planifica(sc, ws, cuts, durata, st, logouri)
    cap_html, cap_js = captions(grupuri(ws, cuts), durata, st["accent"])
    pregateste_assets(dosar, sc["stil"])
    (dosar / "index.html").write_text(pagina(sc, plan, cap_html, cap_js, durata), encoding="utf-8")
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
