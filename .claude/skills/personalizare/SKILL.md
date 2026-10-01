---
name: personalizare
description: Face kitul al omului: brandul (nume, culori, font, logo, CTA) și preferințele de editare (captions, carduri, sunete, filtrul pe față, limba), scrise în brand/brand.json, plus o probă de stil. Folosește când omul scrie /personalizare, vrea reelurile în culorile sau cu logoul lui, sau la primul reel, dacă brand/brand.json nu există.
---

# Personalizarea

Scopul: `brand/brand.json` scris și o probă de stil pe care omul o vede și o aprobă. Formatul și ce face fiecare câmp: `docs/PERSONALIZARE.md`.
Întrebi pe rând, cu varianta implicită pusă în față, ca omul să poată răspunde doar „da”. Nimic nu e obligatoriu.

1. Dacă `brand/brand.json` există, rulezi `python3 unelte/brand.py` și îi arăți ce e setat; întrebi ce vrea schimbat.
2. Brandul:
   - numele sau handle-ul (apare pe cardul de final);
   - culorile: două, în hex. Dacă are site, îl întrebi dacă le iei de acolo; deschizi pagina, propui culorile principale și le scrii doar
     după ce zice „da”;
   - logoul: calea fișierului lui (PNG sau SVG, ideal pătrat, pe fundal transparent). Îl copiezi în `brand/` cu numele lui;
   - fontul: implicit Geist (cel din stil). Dacă vrea fontul lui, îi ceri fișierul (`.woff2`, `.ttf`, `.otf`) și îi spui că trebuie să aibă
     diacriticele românești și licență care permite folosirea în video;
   - CTA-ul de final, cum îl spune de obicei („urmărește-mă pentru mai multe”, „scrie-mi CURS în privat”).
3. Preferințele: captions (da), carduri (normal; „puține” = doar hook, 1–2 carduri și finalul), sunete (normale / încete / oprite),
   filtrul pe față (niciunul / ușor / mediu: netezește pielea și luminează puțin, ca retușul din CapCut, pe toată imaginea), limba (română).
4. Scrii `brand/brand.json` și rulezi `python3 unelte/brand.py`. Dacă spune ce e greșit, repari și rulezi din nou.
5. Proba: `python3 procese/reel/proba_stil.py` (un minut sau două). Citești `brand/proba-stil.jpg` și i-l arăți: culorile, fontul cu
   „ă â î ș ț”, logoul pe cardul de final. Dacă ceva nu arată bine (diacritice lipsă, logo pe fundal alb), propui schimbarea și reiei 4–5.
6. La final îi spui că de acum fiecare reel iese așa și că poate rula `/personalizare` oricând.

Nu urci nimic și nu folosești fonturi sau logouri găsite pe internet fără să-l întrebi.
