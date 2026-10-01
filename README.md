# editare-video-ai

Kitul meu de editare de reeluri, în română, pe care îl rulezi în Claude Code: pui clipurile brute (duble, greșeli, tot), iar Claude
alege dublele, taie la cadru, pune cardurile, captions și sunetele, și îți dă un reel 9:16 verificat, în culorile și cu logoul tău.
E construit pe ce am învățat editând peste 20 de videouri.

**Ce face acum:** reeluri (Instagram, TikTok, Shorts). Editarea de YouTube și stiluri noi vin în versiunile următoare.

## Înainte și după

Demo-ul: un clip brut de 2:20 cu 31 de duble → un reel de 26 de secunde. Clipul brut și reelul scos de kit sunt în
[Release-ul demo](https://github.com/filipgabrielai/editare-video-ai/releases/tag/demo-reel-v1).

## Ce îți trebuie

- Claude Code, cu cel puțin planul Pro.
- Un Mac sau un PC cu Windows 10/11, și cel puțin 10 GB liberi pe disc.
- Restul (ffmpeg, whisper.cpp, Node.js, Python, modelul Whisper) le instalează Claude pentru tine.

## Trei pași

1. **Instalare:** descarci repo-ul (butonul „Code” → „Download ZIP”, sau `git clone`), îl deschizi în Claude Code și scrii `/instalare`.
   Aprobi comenzile pe care ți le propune; la final îți spune „Gata, poți edita.”
2. **Personalizare:** `/personalizare`. Îți ia numele, culorile, logoul, fontul, CTA-ul și preferințele (captions, sunete, filtrul pe față),
   apoi îți arată o probă de stil. Detalii în `docs/PERSONALIZARE.md`.
3. **Editare:** pune clipurile într-un folder și scrie `/editeaza-reel "<calea către folder>"`. Primești în `proiecte/` reelul, gata de
   postat după ce te uiți pe el. Vrei să încerci fără clipurile tale: `python3 instalare/descarca.py demo` și urmezi `exemple/demo-reel/README.md`.

## Din sistemul tău de Claude Code

Dacă ai deja un sistem în Claude Code, scrie `/leaga-de-sistem`: kitul rămâne în folderul lui, iar din orice proiect poți cere
„editează reelul din folderul X”. Se scoate oricând.

## Cât costă

Kitul e gratuit. Transcrierea e locală, deci gratuită. Claude Code consumă din limitele abonamentului tău. Detalii în `docs/COSTURI.md`.

## Credit

Structura e inspirată de `hyperframes-student-kit` al lui Nate Herk (MIT). Randarea folosește HyperFrames (Apache-2.0).
Licențele complete în `THIRD_PARTY_NOTICES.md`.

## Licență

MIT, vezi `LICENSE`.
