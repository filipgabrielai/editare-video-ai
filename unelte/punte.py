#!/usr/bin/env python3
"""Puntea spre sistemul tău de Claude Code: un skill mic în ~/.claude/skills/editare-video-ai/ care spune unde e kitul. Din orice
sesiune Claude Code („editează videoul din folderul X”) Claude lucrează apoi în folderul kitului, cu regulile lui. Kitul rămâne
separat și se actualizează ca până acum; skill-ul se șterge oricând.

    python3 unelte/punte.py instaleaza     scrie (sau actualizează) skill-ul
    python3 unelte/punte.py arata          arată unde ar sta și ce ar scrie
    python3 unelte/punte.py sterge         îl șterge
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unelte import platforma  # noqa: E402

NUME = "editare-video-ai"
MARCAJ = "<!-- scris de editare-video-ai (unelte/punte.py) -->"


def destinatie(acasa: Path | None = None) -> Path:
    return (acasa or Path.home()) / ".claude" / "skills" / NUME / "SKILL.md"


def text_skill(kit: Path) -> str:
    return f"""---
name: {NUME}
description: Editează orice video (reel 9:16 sau orizontal 16:9) din clipuri brute cu kitul editare-video-ai, care stă în {kit}. Folosește când omul cere să-i editezi un video, un reel, un short sau un clip pentru YouTube din clipurile lui, din orice proiect.
---

{MARCAJ}

Kitul de editare e în: `{kit}`

Când omul cere un video:
1. Lucrezi în folderul kitului: comenzile le rulezi de acolo, iar proiectul iese în `{kit / 'proiecte'}`. Clipurile lui rămân unde sunt.
2. Citești `{kit / 'CLAUDE.md'}` și `{kit / '.claude' / 'skills' / 'editeaza' / 'SKILL.md'}` și urmezi pașii de acolo.
3. Brandul și preferințele lui sunt în `{kit / 'brand' / 'brand.json'}`. Dacă lipsește, îi propui personalizarea din kit
   (`{kit / '.claude' / 'skills' / 'personalizare' / 'SKILL.md'}`).
4. La editare au prioritate regulile kitului; pentru restul, regulile sistemului lui.

Skill-ul ăsta l-a pus kitul; se șterge cu: python3 unelte/punte.py sterge (din folderul kitului; pe Windows: python).
"""


def _al_nostru(dest: Path) -> bool:
    return MARCAJ in dest.read_text(encoding="utf-8", errors="replace")


def instaleaza(kit: Path, dest: Path) -> str:
    if dest.exists() and not _al_nostru(dest):
        raise SystemExit(f"În {dest} e deja un skill care nu e pus de kit. Nu-l suprascriu; redenumește-l sau șterge-l tu întâi.")
    stare = "actualizat" if dest.exists() else "scris"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text_skill(kit), encoding="utf-8")
    return stare


def sterge(dest: Path) -> bool:
    if not dest.exists():
        return False
    if not _al_nostru(dest):
        raise SystemExit(f"{dest} nu e pus de kit; nu-l șterg.")
    dest.unlink()
    if not any(dest.parent.iterdir()):
        dest.parent.rmdir()
    return True


def main(argv: list[str] | None = None) -> int:
    platforma.iesire_utf8()
    p = argparse.ArgumentParser(description="Puntea spre sistemul tău de Claude Code.")
    p.add_argument("ce", choices=["instaleaza", "sterge", "arata"])
    a = p.parse_args(argv)
    dest, kit = destinatie(), platforma.RADACINA
    if a.ce == "arata":
        print(f"{dest}\n\n{text_skill(kit)}")
    elif a.ce == "instaleaza":
        print(f"Skill-ul {instaleaza(kit, dest)}: {dest}")
    else:
        print(f"Șters: {dest}" if sterge(dest) else "Nu era pus.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
