# editare-video-ai

Sistemul meu de editare video, în română, pe care îl rulezi în Claude Code: de la clipurile brute la un reel pentru Instagram
sau un video de YouTube gata de postat. E construit pe ce am învățat editând peste 20 de videouri cu el.

**Stare:** în construcție. Versiunea 0.1 are instalarea și proba de 30 de secunde; editarea vine în versiunile următoare.

## Ce îți trebuie

- Claude Code, cu cel puțin planul Pro.
- Un Mac sau un PC cu Windows 10/11, și cel puțin 10 GB liberi pe disc.
- Restul (ffmpeg, whisper.cpp, Node.js, Python, modelul Whisper) le instalează Claude pentru tine.

## Instalare

1. Descarci repo-ul (butonul „Code” → „Download ZIP”, sau `git clone`) și îl dezarhivezi.
2. Deschizi folderul în Claude Code.
3. Scrii `/instalare` și aprobi comenzile pe care ți le propune. La final îți spune „Gata, poți edita.”

## Cât costă

Repo-ul e gratuit. Transcrierea e locală, deci gratuită. Claude Code consumă din limitele abonamentului tău; un YouTube întreg
consumă mult. Detaliile în `docs/COSTURI.md` (vine în versiunile următoare).

## Credit

Structura e inspirată de `hyperframes-student-kit` al lui Nate Herk (MIT). Randarea folosește HyperFrames (Apache-2.0).
Licențele complete în `THIRD_PARTY_NOTICES.md`.

## Licență

MIT, vezi `LICENSE`.
