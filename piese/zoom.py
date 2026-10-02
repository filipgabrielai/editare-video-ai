"""Zoom ușor la fiecare tăietură, pe grila de cadre: ascunde săritura dintre două duble."""
from __future__ import annotations

from piese.comun import FPS, Context, Fragment


def construieste(ctx: Context) -> Fragment:
    return Fragment(js=[f'tl.set("#stage", {{scale:{1.06 if i % 2 == 0 else 1.0}}}, {round(c * FPS) / FPS - 0.001:.4f});'
                        for i, c in enumerate(ctx.cuts)])
