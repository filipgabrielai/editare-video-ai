"""Ce împart piesele unei compoziții: contextul (cuvintele, tăieturile, stilul, formatul, sunetele) și forma fragmentului pe
care îl întoarce fiecare. O piesă e un modul cu `construieste(ctx) -> Fragment`."""
from __future__ import annotations

from dataclasses import dataclass, field

from procese.editare import scenariu as S
from unelte import formate

FPS = 60
ROT = {"card": ["boom", "knock", "tok"], "pop": ["pop", "thump", "click"]}   # trei la carduri: cu două, Filip le auzea la fel
VOL = {"boom": (0.35, 0.6), "knock": (0.35, 0.2), "tok": (0.35, 0.16), "pop": (0.55, 0.12), "thump": (0.5, 0.25), "click": (0.55, 0.14)}   # volum, durată
MIN_PAUZA = 1.0   # între două sunete; sub asta Filip le-a găsit „cam dese”


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


@dataclass
class Fragment:
    html: list[str] = field(default_factory=list)
    js: list[str] = field(default_factory=list)
    beats: list[tuple[float, str]] = field(default_factory=list)
    intervale: list[dict] = field(default_factory=list)


@dataclass
class Context:
    sc: dict
    ws: list[dict]
    cuts: list[float]
    durata: float
    st: dict
    logouri: dict[str, str] = field(default_factory=dict)
    logo_brand: str = ""
    format: str = formate.IMPLICIT
    sunete: Sunete = field(default_factory=Sunete)
    cursor: float = 0.0

    def ancora(self, fraza: str, inapoi: float = 0.4) -> float:
        """Secunda la care începe fraza în transcript, căutată de la ultima ancoră încoace: aceeași frază spusă de două ori
        prinde apariția care urmează, nu prima din video."""
        t = S.gaseste(self.ws, fraza, max(0.0, self.cursor - inapoi))[0]
        self.cursor = t
        return t
