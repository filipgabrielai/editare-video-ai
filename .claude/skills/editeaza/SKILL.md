---
name: editeaza
description: Editează orice video al omului din clipurile lui brute, reel 9:16 sau video orizontal 16:9, cu procesul din kit (dublele, tăietura, planul pe momente, compoziția, randarea și verificarea). Folosește când omul scrie /editeaza, cere să-i editezi un video, un clip pentru YouTube sau pentru site, o prezentare filmată, sau nu spune ce fel de video e.
---

# Editarea unui video

Scopul: un DRAFT verificat în `proiecte/<slug>/`. FINAL doar după OK-ul omului. Procesul întreg, cu motivele, e în `docs/PROCES.md`.
Pe Mac folosești `python3`, pe Windows `python` (sau `py -3`). Dacă o comandă spune că lipsește ceva, mergi pe `/instalare`.

1. **Ce fel de video e.** Te uiți la un cadru din clip și afli unde îl pune: Instagram, TikTok sau Shorts înseamnă 9:16; YouTube,
   site sau prezentare înseamnă 16:9. Dacă nu reiese din ce ți-a dat, întrebi o singură dată.
2. **Rețeta**, din `retete/README.md`:
   - reel cu omul la cameră: urmezi `/editeaza-reel`, pas cu pas;
   - video orizontal: pașii de mai jos, cu rețeta `orizontal-simplu`.
3. **Ce cere și nu e încă în kit.** Piesele care există sunt în `docs/PIESE.md`. Dacă cere un efect care nu e acolo (text în
   spatele lui, ecran împărțit, obiect în palmă), îi spui limpede: „piesa asta nu e încă în kit”, și ce poți face acum în locul
   ei. Nu improvizezi un efect pe care nu-l poți verifica.
4. **Baza**, la fel ca la reel (pașii 0–4 din `/editeaza-reel`): brandul, dublele, falsele starturi, cuvintele, tăietura,
   conținutul. La orizontală, tăietura e `python3 procese/editare/taietura.py proiecte/<slug> --filmare 16:9`. Dacă tăietura
   spune că un clip e filmat în altă orientare decât formatul cerut, te oprești și îl întrebi ce vrea.
5. **Planul pe momente, înainte să construiești ceva:** un tabel cu timpul, cuvintele lui, ce apare pe ecran și unde. I-l arăți
   și aștepți OK-ul. Schimbările pe plan sunt gratis; după randare, fiecare costă minute.
6. **Cadrul, pe orizontală:** scoți un cadru din `taiat.mp4` și te uiți unde e omul. Cardul stă pe partea liberă
   (`"cadru": {"carduri": "stanga"}` sau `"dreapta"`), niciodată peste față; `carduri_y` de la 140 în jos (200 cu titlu);
   subtitrările pe piept (`captions_y` în jur de 880, cel mult 900). Rândurile de card au cel mult 24 de caractere.
7. **Scenariul** pornește de la `retete/orizontal-simplu/scenariu.json` (`"format": "16:9"`), cu ancorele copiate din
   `transcript.json`. Formatul complet e în `docs/SCENARIU.md`.
8. **Compoziția, planșele, randarea, livrarea:** pașii 7–10 din `/editeaza-reel`. Pe planșe, roșul e marginea de 5 % a cadrului:
   nimic important în ea.
