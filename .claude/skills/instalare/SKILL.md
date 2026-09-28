---
name: instalare
description: Instalează și verifică tot ce trebuie pentru editare, pe Mac și Windows, apoi rulează proba de 30 de secunde. Folosește când omul scrie /instalare, când deschide repo-ul prima dată, sau când o comandă de editare spune că lipsește ceva (ffmpeg, whisper, Node, modelul).
---

# Instalarea

Scopul: omul ajunge la „Gata, poți edita.” fără să știe ce e un terminal. Tu rulezi comenzile, el doar le aprobă.

1. Află sistemul. Pe Mac folosești `python3`, pe Windows `python`. Dacă Python lipsește cu totul (comanda nu pornește):
   - Mac: întâi Homebrew, cu comanda oficială de pe brew.sh (aceeași ca în `verificare/instalarea.py`), apoi `brew install python`.
   - Windows: `winget install -e --id Python.Python.3.12`, apoi îi spui să închidă și să redeschidă Claude Code.
2. Rulează `python3 verificare/instalarea.py`. Citește fiecare rând `[lipsește]`.
3. Pentru fiecare lipsă, în ordinea din listă: spune-i într-o propoziție ce e și de ce trebuie, apoi rulează comanda din „cum repari”.
   Pe Windows, după orice `winget`, spune-i să închidă și să redeschidă Claude Code, apoi reia de la pasul 2.
4. Modelul Whisper (1,6 GB) și pachetele: `python3 instalare/descarca.py model`, apoi `npm install`. Spune-i că durează câteva minute.
5. Rulează din nou verificarea, până când totul e `[ok]`.
6. Proba: `python3 tests/proba_30s.py`. Dacă trece, îi spui „Gata, poți edita.” și ce urmează.
7. Dacă ceva nu merge după două încercări, deschizi `docs/DEPANARE.md` și urmezi pașii de acolo.

Nu instala nimic fără să spui ce e. Nu folosi sudo. Nu rula comenzi care șterg sau schimbă setări de sistem în afara celor de mai sus.
