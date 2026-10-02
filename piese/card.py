"""Cardurile: intră pe ancora lor și ies când intră următorul (ultimul rămâne până la final). Primul rând e static (un card
care își așteaptă ancora nu stă gol), celelalte apar pe ancorele lor; chipurile și cifra la fel."""
from __future__ import annotations

from piese.comun import Context, Fragment
from procese.editare import scenariu as S

INALTIME_RAND = {False: 84, True: 66}   # ca .card .row și .card.compact .row din stil


def construieste(ctx: Context) -> Fragment:
    html: list[str] = []
    js: list[str] = []
    beats: list[tuple[float, str]] = []
    intervale: list[dict] = []
    rgb = ctx.st["accent_rgb"]
    carduri = ctx.sc["carduri"]
    intrari = []
    for c in carduri:
        intrari.append(0.05 if c["ancora"] == "start" else ctx.ancora(c["ancora"]) - 0.05)
    umbra_scurta = False
    for k, c in enumerate(carduri):
        t0 = intrari[k]
        t1 = intrari[k + 1] - 0.08 if k + 1 < len(carduri) else ctx.durata
        cid = f"c-{c['id']}"
        corp = []
        for r_i, r in enumerate(c.get("randuri", [])):
            if r.get("logo"):
                nume = [r["logo"]] if isinstance(r["logo"], str) else r["logo"]
                ico = '<span class="lgs">' + "".join(
                    f'<img class="lg{" inv" if n in ctx.sc.get("logo_inversat", []) else ""}" src="assets/logo/{S.esc(ctx.logouri.get(n, n))}" alt="">'
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
        marca = ctx.logo_brand if c.get("brand") else ""   # logoul omului, pe cardul de final
        html.append(f'<div class="{cls}" id="{cid}"><div class="k">{marca}{S.esc(c["kicker"])}</div>{"".join(corp)}</div>')
        js.append(f'tl.fromTo("#{cid}", {{xPercent:-50, autoAlpha:0, y:-26, scale:0.94, filter:"blur(10px)"}}, '
                  f'{{xPercent:-50, autoAlpha:1, y:0, scale:1, filter:"blur(0px)", duration:0.5, ease:"back.out(1.3)"}}, {t0:.3f});')
        ctx.sunete.adauga("card", t0, 0.6 if k == 0 else None)
        if k + 1 < len(carduri):
            js.append(f'tl.to("#{cid}", {{autoAlpha:0, y:-30, scale:0.96, duration:0.28, ease:"power1.in"}}, {t1:.3f});')
        if bool(c.get("compact")) != umbra_scurta:   # pe înregistrări de ecran, doar banda de sus, nu umbra lungă
            umbra_scurta = bool(c.get("compact"))
            js.append(f'tl.set("#umbra", {{autoAlpha:{0 if umbra_scurta else 1}}}, {t0:.3f});')
            js.append(f'tl.set("#umbra2", {{autoAlpha:{1 if umbra_scurta else 0}}}, {t0:.3f});')
        ctx.cursor = t0 + 0.05
        for r_i, r in enumerate(c.get("randuri", [])):
            if r_i > 0 and r.get("ancora"):
                tr = max(t0 + 0.35, ctx.ancora(r["ancora"]) - 0.03)
                h = INALTIME_RAND[bool(c.get("compact"))]   # cât primul rând, ca distanța dintre rânduri să fie egală
                js.append(f'tl.fromTo("#{cid}-r{r_i}", {{height:0, minHeight:0, autoAlpha:0, x:-18}}, '
                          f'{{height:{h}, minHeight:{h}, autoAlpha:1, x:0, duration:0.32, ease:"power2.out"}}, {tr:.3f});')
                ctx.sunete.adauga("pop", tr)
        mod = c.get("chips_mod", "aprinde")
        for j, ch in enumerate(c.get("chips", [])):
            sel = f"#{cid}-ch{j}"
            tc = max(t0 + 0.2, ctx.ancora(ch["ancora"]) - 0.03) if ch.get("ancora") else t0 + 0.2
            if mod == "apar":
                js.append(f'tl.fromTo("{sel}", {{autoAlpha:0, scale:0.5, y:10}}, {{autoAlpha:1, scale:1, y:0, duration:0.45, ease:"back.out(2)"}}, {tc:.3f});')
                js.append(f'tl.set("{sel}", {{backgroundColor:"rgba({rgb},.12)", borderColor:"rgba({rgb},.5)", color:"#ffffff"}}, {tc:.3f});')
            else:
                js.append(f'tl.set("{sel}", {{autoAlpha:1}}, {t0:.3f});')
                js.append(f'tl.fromTo("{sel}", {{backgroundColor:"rgba(148,163,184,.08)", borderColor:"rgba(148,163,184,.3)", color:"#94a3b8"}}, '
                          f'{{backgroundColor:"rgba({rgb},.18)", borderColor:"rgba({rgb},.8)", color:"#ffffff", duration:0.2, immediateRender:false}}, {tc:.3f});')
            ctx.sunete.adauga("pop", tc)
        if c.get("cifra"):
            tf = max(t0 + 0.2, ctx.ancora(c["cifra"]["ancora"]) - 0.03) if c["cifra"].get("ancora") else t0 + 0.2
            js.append(f'tl.fromTo("#{cid}-cifra", {{autoAlpha:0, scale:0.6}}, {{autoAlpha:1, scale:1, duration:0.4, ease:"back.out(2)"}}, {tf:.3f});')
            ctx.sunete.adauga("pop", tf)
        text_beat = " / ".join(S._text_simplu(r["text"]) for r in c.get("randuri", [])) or " · ".join(ch["text"] for ch in c.get("chips", []))
        beats.append((t0, f"{c['kicker']}: {text_beat}"))
        intervale.append({"id": c["id"], "intra": round(t0, 3), "iese": round(t1, 3)})
    return Fragment(html=html, js=js, beats=beats, intervale=intervale)
