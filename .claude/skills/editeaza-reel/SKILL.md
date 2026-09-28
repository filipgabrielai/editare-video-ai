---
name: editeaza-reel
description: Editează un reel pentru Instagram (9:16) din clipurile brute ale omului, cu procesul din repo: dublele, tăietura, cardurile, captions, randarea și verificarea. Folosește când omul scrie /editeaza-reel, cere să-i editezi un reel sau un short, și dă folderul cu clipuri (sau un clip).
---

# Editarea unui reel

Scopul: un DRAFT în `proiecte/<slug>/`, verificat, pe care omul îl poate posta. FINAL doar după OK-ul lui.
Pe Mac folosești `python3`, pe Windows `python` (sau `py -3`). Dacă o comandă spune că lipsește ceva, mergi pe `/instalare`.
Îl ții la curent la pașii mari (dublele, tăietura, planșele, draftul), nu la fiecare comandă.

1. **Dublele:** `python3 procese/reel/duble.py "<folder sau clip>" --nume "<numele reelului>"`. Citește TOATE dublele, nu doar ultima.
   De regulă se păstrează ultima dublă întreagă a fiecărei fraze, dar omul schimbă cuvinte între duble și uneori decide altfel;
   ce nu e clar, îl întrebi. Textele de tip „Mulțumim pentru vizionare!” pe o dublă scurtă sunt Whisper care aude liniștea.
2. **Cuvintele** pe dublele alese: `python3 procese/reel/cuvinte.py proiecte/<slug> <dubla> <dubla> ...`.
3. **Tăietura:** scrii `proiecte/<slug>/bucati.json` (`[{"dubla": "...", "de_la": null, "pana_la": null}]`; „cuvânt#2” = a
   doua apariție, „cuvânt@ultimul” = ultima), apoi `python3 procese/reel/taietura.py proiecte/<slug>`. Verifici în
   `transcript.json` că primul și ultimul cuvânt al fiecărei bucăți sunt întregi. Când scurtezi, scoți fraze sau blocuri întregi,
   niciodată coada unei fraze ca să intri sub o durată.
4. **Conținutul:** fiecare cifră, preț, nume de produs se verifică pe sursa primară (site-ul oficial). Ce a spus omul greșit nu
   se taie: se corectează blând pe card, cu sursa, și i se spune. Nimic tăiat în tăcere: la livrare îi spui tot ce ai scos în
   afară de reluări.
5. **Cadrul:** scoți un cadru (`ffmpeg -ss 1 -i proiecte/<slug>/taiat.mp4 -frames:v 1 proiecte/<slug>/lucru/cadru.jpg`) și îl
   citești: unde e creștetul și bărbia. `shift` coboară videoul cât să nu fie capul sub tabul Reels; cardurile stau deasupra
   părului (`carduri_y` ≥ 262); captions pe guler (`captions_y` ≤ 1480).
6. **Scenariul:** `proiecte/<slug>/scenariu.json`, formatul în `docs/SCENARIU.md`. Card doar pe ce adaugă ceva peste ce se
   vede și se aude: ideea, cifra, pașii. Maximum 4 rânduri, text scurt, cuvântul important cu `**...**`. Ancorele se copiază
   din `transcript.json`. Fiecare aplicație numită primește logoul ei: îl iei doar de pe site-ul oficial (iconița din pagină
   sau pagina de brand), îl pui în `proiecte/<slug>/logo/` și îl verifici cu ochii înainte să-l folosești.
7. **Compoziția:** `python3 procese/reel/compozitie.py proiecte/<slug>`. Dacă dă erori, repari scenariul.
8. **Planșele:** `python3 procese/reel/planse.py proiecte/<slug>` și citești fiecare foaie: nimic important în roșu, cardurile nu
   acoperă fața, textul nu iese din card, captions se citesc. Repari și reiei 7–8.
9. **Randarea:** `python3 procese/reel/randeaza.py proiecte/<slug>`. Dacă verificarea spune „NU TRECE”, nu livrezi: repari
   cauza și randezi din nou.
10. **Livrarea:** scrii `proiecte/<slug>/DESIGN.md` (ce ai ales și de ce: dublele, ce ai scos, cadrul, cardurile, corecturile);
    `VERIFY.md` îl scrie randarea. Îi spui unde e fișierul, durata, ce ai verificat, ce ai scos și ce ai corectat. După OK-ul
    lui, redenumești în „<Titlu> FINAL.mp4”. Nu publici și nu urci nimic.
