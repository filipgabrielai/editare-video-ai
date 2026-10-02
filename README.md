# editare-video-ai

Kitul meu de editare video, în română, pe care îl rulezi în Claude Code: pui clipurile brute (duble, greșeli, tot), iar Claude
alege dublele, taie la cadru, pune cardurile, subtitrările și sunetele, și îți dă videoul verificat, în culorile și cu logoul tău.
E construit pe ce am învățat editând peste 20 de videouri.

**Ce e:** baza unui sistem de editare, nu un editor cu toate efectele. Îți instalează ce trebuie, îți dă procesul pas cu pas
(`docs/PROCES.md`) și scoate din prima un reel 9:16 sau un video orizontal 16:9 tăiat curat, cu subtitrări, carduri și sunete.
Animațiile, culorile și efectele tale le construiești peste bază, cu Claude: `docs/EXTINDERE.md`.

## Înainte și după

Demo-ul: un clip brut de 2:20 cu 31 de duble → un reel de vreo 25 de secunde. Clipul brut și reelul scos de kit sunt în
[Release-ul demo](https://github.com/filipgabrielai/editare-video-ai/releases/tag/demo-reel-v1).

## Ce îți trebuie

- Claude Code, cu cel puțin planul Pro.
- Un Mac sau un PC cu Windows 10/11, și cel puțin 10 GB liberi pe disc.
- Restul (ffmpeg, whisper.cpp, Node.js, Python, modelul Whisper) le instalează Claude pentru tine.

## Cel mai simplu: dă-i linkul lui Claude Code

Deschide Claude Code în folderul în care vrei să stea kitul și scrie-i:

> Clonează https://github.com/filipgabrielai/editare-video-ai (dacă nu merge cu git, descarcă arhiva ZIP și dezarhiveaz-o), apoi
> citește CLAUDE.md din el și fă instalarea.

Claude îl aduce, îi citește regulile și te duce prin instalare. De acolo continui cu pașii 2 și 3 de mai jos.

## Trei pași

1. **Instalare:** dacă nu l-ai luat cu linkul, descarci repo-ul (butonul „Code” → „Download ZIP”), îl deschizi în Claude Code și scrii `/instalare`.
   Aprobi comenzile pe care ți le propune; la final îți spune „Gata, poți edita.”
2. **Personalizare:** `/personalizare`. Îți ia numele, culorile, logoul, fontul, CTA-ul și preferințele (captions, sunete, filtrul pe față),
   apoi îți arată o probă de stil. Detalii în `docs/PERSONALIZARE.md`.
3. **Editare:** pune clipurile într-un folder și scrie `/editeaza` urmat de calea către folder (orice video), sau `/editeaza-reel`
   urmat de cale (direct reel). Primești în `proiecte/` videoul, gata de postat după ce te uiți pe el. Procesul, pas cu pas, e în `docs/PROCES.md`. Vrei să încerci fără clipurile tale: `python3 instalare/descarca.py demo` și urmezi `exemple/demo-reel/README.md`.

## Cum îi dai feedback

Te uiți pe draft și îi scrii ca unui editor: o schimbare pe rând, cu secunda și cu ce vrei să vezi, nu cum s-o facă.
„La 0:14 e o pauză prea lungă.” „La 0:23 nu se aude finalul cuvântului.” „La final scrie «ei» în loc de «AI».”
Claude repară, randează un draft nou și îl verifică din nou. FINAL se face doar când zici tu.

## Cum îl faci al tău

Trei trepte: brandul (`/personalizare`), stilul tău peste al kitului (`brand/stil.css`) și piesele tale, adică efectele pe care i le
ceri lui Claude și pe care le pui pe cuvintele tale (`piese/ale-mele/`). Tot ce construiești trece prin aceleași verificări ca
baza, iar o actualizare a kitului nu se atinge de ce e al tău. Pas cu pas: `docs/EXTINDERE.md`.

## Din sistemul tău de Claude Code

Dacă ai deja un sistem în Claude Code, scrie `/leaga-de-sistem`: kitul rămâne în folderul lui, iar din orice proiect poți cere
„editează videoul din folderul X”. Se scoate oricând.

## Cât costă

Kitul e gratuit. Transcrierea e locală, deci gratuită. Claude Code consumă din limitele abonamentului tău. Detalii în `docs/COSTURI.md`.

## Credit

Structura e inspirată de `hyperframes-student-kit` al lui Nate Herk (MIT). Randarea folosește HyperFrames (Apache-2.0).
Licențele complete în `THIRD_PARTY_NOTICES.md`.

## Licență

MIT, vezi `LICENSE`.
