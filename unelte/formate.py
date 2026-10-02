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


CSS = {"9:16": "reel.css", "16:9": "orizontal.css"}                      # fișierul stilului, în stiluri/<stil>/
CADRU = {"9:16": {"shift": 120, "carduri_y": 280, "captions_y": 1480},   # ce pune compoziția când scenariul nu spune
         "16:9": {"carduri": "stanga", "carduri_y": 140, "captions_y": 880}}
CARDURI_Y_CU_TITLU = {"9:16": 370, "16:9": 200}
COMPACT_Y = {"9:16": (262, 340), "16:9": (64, 140)}                      # cardul compact: fără titlu, cu titlu
CARDURI_Y_MIN = {"9:16": 262, "16:9": 54}
CAPTIONS_Y_MAX = {"9:16": 1480, "16:9": 900}
MAX_TEXT = {"9:16": 34, "16:9": 24}                                      # caractere pe un rând de card
MAX_CAR = {"9:16": 22, "16:9": 34}                                       # caractere într-un grup de subtitrări
RAND = {"9:16": {False: 84, True: 66}, "16:9": {False: 72, True: 60}}    # înălțimea rândului de card (normal, compact), ca în CSS
MARGINE_CARD = 96                                                        # 16:9: cardul stă la 5 % de marginea lui
