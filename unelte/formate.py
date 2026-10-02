"""Formatele kitului. Pânza e ce se randează (scenariu.json: "format"); filmarea e cum iese taiat.mp4 (se alege la tăietură,
cu --filmare, și stă în taieturi.json). Tot ce ține de dimensiuni și de zonele acoperite de aplicații se citește de aici."""
from __future__ import annotations

FORMATE = {"9:16": (1080, 1920), "16:9": (1920, 1080)}
IMPLICIT = "9:16"
# ce acoperă aplicația în care e văzut videoul: x, y, lățime, înălțime
ZONE = {
    "9:16": [(0, 0, 1080, 260), (0, 1640, 1080, 280), (950, 1120, 130, 520)],   # tabul „Reels”, numele și descrierea, butoanele
    "16:9": [(0, 0, 1920, 54), (0, 1026, 1920, 54), (0, 0, 96, 1080), (1824, 0, 96, 1080)],   # o margine de 5 %
}


def dimensiuni(f: str) -> tuple[int, int]:
    if f not in FORMATE:
        raise SystemExit(f"Formatul „{f}” nu e cunoscut. Sunt: {', '.join(FORMATE)}.")
    return FORMATE[f]


def e_orizontal(latime: int, inaltime: int, rotatie: int = 0) -> bool:
    """Clipurile de telefon filmate vertical sunt 1920x1080 cu rotație de 90°: ffmpeg le întoarce la decodare."""
    if abs(rotatie) % 180 == 90:
        latime, inaltime = inaltime, latime
    return latime > inaltime
