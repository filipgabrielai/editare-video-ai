"""Titlul care stă sus tot videoul."""
from __future__ import annotations

from piese.comun import Context, Fragment
from procese.editare import scenariu as S


def construieste(ctx: Context) -> Fragment:
    if not ctx.sc.get("titlu"):
        return Fragment()
    return Fragment(html=[f'<div id="titlu">{S.esc(ctx.sc["titlu"])}</div>'],
                    js=['tl.fromTo("#titlu", {autoAlpha:0, y:-12}, {autoAlpha:1, y:0, duration:0.45, ease:"power2.out"}, 0.05);'])
