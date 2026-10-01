"""Scenariul unui reel (scenariu.json), scris de Claude pentru fiecare video: titlul, cardurile, rândurile, chipurile și
cuvintele pe care intră. Aici se citește, se validează și se leagă de transcript; mesajele de eroare spun exact ce nu se
potrivește. Formatul e descris în docs/SCENARIU.md."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from unelte import platforma

STILURI = platforma.RADACINA / "stiluri"
ICOANE: dict[str, str] = json.loads((STILURI / "icoane.json").read_text(encoding="utf-8"))
ZONA_SUS, CAPTIONS_MAX = 262, 1480   # tabul „Reels” acoperă ~260 px sus; sub ~1580 stau numele și descrierea
MAX_RANDURI, MAX_TEXT = 4, 34


def norm(s: str) -> list[str]:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").replace("-", " ")
    s = re.sub(r"\.(?=[a-z])", " ", s)   # „3.Bolt.new” (Whisper lipește cuvintele) → 3 bolt new; „5.5” rămâne 55, ca „5,5”
    return re.sub(r"[^a-z0-9% ]", "", s).split()


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def markup(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(text))


def cuvinte(cale: Path) -> list[dict]:
    with open(cale, encoding="utf-8") as f:
        d = json.load(f)
    ws = [dict(w) for w in d["words"] if w.get("type", "word") == "word" and w.get("text", "").strip()]
    for w in ws:
        w["n"] = norm(w["text"])
    return ws


def gaseste(ws: list[dict], fraza: str, de_la: float = 0.0) -> tuple[float, float]:
    tinta = norm(fraza)
    if not tinta:
        raise SystemExit(f"Ancora „{fraza}” e goală.")
    plat = [(i, t) for i, w in enumerate(ws) for t in w["n"]]
    for k in range(len(plat) - len(tinta) + 1):
        if [t for _, t in plat[k:k + len(tinta)]] == tinta and ws[plat[k][0]]["start"] >= de_la:
            return ws[plat[k][0]]["start"], ws[plat[k + len(tinta) - 1][0]]["end"]
    urmeaza = " ".join(w["text"] for w in ws if w["start"] >= de_la)[:160]
    raise SystemExit(f"Ancora „{fraza}” nu apare în transcript după {de_la:.2f} s. Scrie-o cum e în transcript.json; urmează: {urmeaza}")


def corecteaza(ws: list[dict], corecturi: dict[str, str]) -> list[dict]:
    """Corecturile de afișare în captions („cloud code” → „Claude Code”). Potrivirea merge pe bucățile de cuvânt, nu pe cuvinte
    întregi, fiindcă Whisper sparge greșelile altfel („unelte AI” → „un LTE-AI”). Articolul legat rămâne („Code-ul,” →
    „Claude Code-ul,”). Ancorele rămân pe textul din transcript (câmpul n)."""
    for gresit, corect in corecturi.items():
        tinta = norm(gresit)
        if not tinta:
            continue
        plat = [(i, j) for i, w in enumerate(ws) for j in range(len(w["n"]))]   # (cuvântul, a câta bucată din el)
        k = 0
        while k <= len(plat) - len(tinta):
            bucati = plat[k:k + len(tinta)]
            if [ws[i]["n"][j] for i, j in bucati] != tinta or bucati[0][1] != 0 or not ws[bucati[0][0]]["text"]:
                k += 1
                continue
            i0, (i1, j1) = bucati[0][0], bucati[-1]
            ultim = ws[i1]["text"]
            if j1 < len(ws[i1]["n"]) - 1:            # se oprește în mijlocul cuvântului: păstrăm restul, de la cratimă
                if "-" not in ultim:
                    k += 1
                    continue
                coada = ultim[ultim.index("-"):]
            else:
                coada = ultim[len(ultim.rstrip(".,?!;:")):]
            ws[i0]["text"] = corect + coada
            for w in ws[i0 + 1:i1 + 1]:
                w["text"] = ""
            k += len(tinta)
    return ws


def stil(nume: str) -> dict:
    with open(STILURI / nume / "stil.json", encoding="utf-8") as f:
        return json.load(f)


def _text_simplu(t: str) -> str:
    return t.replace("**", "")


def valideaza(sc: dict) -> tuple[list[str], list[str]]:
    erori, avert = [], []
    if not (STILURI / str(sc.get("stil", "")) / "reel.css").is_file():
        erori.append(f"stilul „{sc.get('stil')}” nu există în stiluri/")
    cadru = sc.get("cadru", {})
    for k, v in cadru.items():
        if k not in ("shift", "carduri_y", "captions_y") or not isinstance(v, (int, float)):
            erori.append(f"cadru.{k} nu e cunoscut sau nu e număr")
    if cadru.get("carduri_y", ZONA_SUS) < ZONA_SUS:
        erori.append(f"carduri_y = {cadru['carduri_y']}: sub {ZONA_SUS} px cardurile intră sub tabul „Reels” din Instagram")
    if cadru.get("captions_y", CAPTIONS_MAX) > CAPTIONS_MAX:
        erori.append(f"captions_y = {cadru['captions_y']}: peste {CAPTIONS_MAX} captions intră peste numele și descrierea din Instagram")
    if len(sc.get("titlu", "")) > 30:
        avert.append("titlul are peste 30 de caractere; poate ieși din ecran")
    carduri = sc.get("carduri") or []
    if not carduri:
        erori.append("scenariul nu are carduri")
    vazute = set()
    for c in carduri:
        cid = c.get("id", "")
        if not re.fullmatch(r"[a-z0-9-]+", cid):
            erori.append(f"cardul „{cid}”: id-ul are voie doar litere mici, cifre și cratimă")
        if cid in vazute:
            erori.append(f"cardul „{cid}” apare de două ori")
        vazute.add(cid)
        if not c.get("kicker"):
            erori.append(f"cardul „{cid}” nu are kicker")
        if not c.get("ancora"):
            erori.append(f"cardul „{cid}” nu are ancoră („start” sau o frază din transcript)")
        if not (c.get("randuri") or c.get("chips") or c.get("cifra")):
            erori.append(f"cardul „{cid}” e gol (nici rânduri, nici chipuri, nici cifră)")
        randuri = c.get("randuri", [])
        if len(randuri) > MAX_RANDURI:
            erori.append(f"cardul „{cid}” are {len(randuri)} rânduri; peste 4 rânduri cardul ajunge pe păr")
        for r in randuri:
            if not r.get("text"):
                erori.append(f"cardul „{cid}” are un rând fără text")
            if r.get("icoana") and r["icoana"] not in ICOANE:
                erori.append(f"icoana „{r['icoana']}” nu există (sunt: {', '.join(sorted(ICOANE))})")
            if len(_text_simplu(r.get("text", ""))) > MAX_TEXT:
                avert.append(f"cardul „{cid}”: rândul „{r['text']}” e lung și poate ieși din card; verifică pe planșă")
        if c.get("chips_mod", "aprinde") not in ("aprinde", "apar"):
            erori.append(f"cardul „{cid}”: chips_mod e „aprinde” sau „apar”")
        for ch in c.get("chips", []):
            if not ch.get("text"):
                erori.append(f"cardul „{cid}” are un chip fără text")
    return erori, avert
