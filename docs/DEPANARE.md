# Depanare

## Mac: Homebrew cere parola sau Claude nu-l poate instala
Homebrew se instalează din aplicația Terminal, nu din Claude Code, pentru că îți cere parola de la Mac. Rulează comanda pe care
ți-o dă verificarea, urmează pașii „Next steps” de la final, apoi închide și redeschide Claude Code.

## Mac: am instalat Homebrew, dar verificarea zice că nu-l vede
Pe Mac-urile cu procesor Apple, Homebrew trebuie adăugat o dată în ~/.zprofile. Verificarea îți dă exact linia de rulat în Terminal;
după ea, închide și redeschide Claude Code.

## Windows: „winget nu e recunoscut”
Windows 10 mai vechi nu are winget. Instalează „App Installer” din Microsoft Store, apoi redeschide Claude Code.

## Am instalat ceva, dar verificarea tot zice că lipsește
Windows vede programele noi abia după ce redeschizi terminalul. Închide și redeschide Claude Code, apoi rulează din nou `/instalare`.

## Antivirusul blochează whisper-cli.exe
whisper.cpp e descărcat din pagina oficială (github.com/ggml-org/whisper.cpp). Permite fișierul din antivirus sau pune folderul
`unelte/whisper` la excepții, apoi rulează din nou proba.

## Descărcarea modelului s-a întrerupt
Rulează din nou `python3 instalare/descarca.py model` (pe Windows: `python`). Descărcarea pornește de la zero și nu lasă un model stricat.

## `npm install` dă erori
Verifică versiunea de Node.js: trebuie cel puțin 22 (`node --version`). Dacă e mai veche, instalează versiunea LTS din verificare.

## Randarea din probă eșuează prima dată
La prima randare se descarcă un browser pentru randare. Ai nevoie de internet; rulează din nou `python3 tests/proba_30s.py`.

## Transcrierea iese goală sau aiurea
Verifică modelul (`python3 verificare/instalarea.py`): dacă e „incomplet”, descarcă-l din nou.
