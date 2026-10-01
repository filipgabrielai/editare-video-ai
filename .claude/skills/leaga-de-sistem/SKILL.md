---
name: leaga-de-sistem
description: Leagă kitul de sistemul de Claude Code al omului, ca să poată cere un reel din orice proiect („editează reelul din folderul X”). Folosește când omul scrie /leaga-de-sistem, întreabă cum folosește kitul din sistemul lui, sau la finalul instalării.
---

# Puntea spre sistemul tău

1. Îi explici într-o propoziție: kitul rămâne în folderul lui; în `~/.claude/skills/` (pe Windows, în folderul tău de utilizator)
   se pune un singur fișier care spune unde e kitul, ca să-l găsească orice sesiune Claude Code. Nimic altceva din sistemul lui nu se schimbă.
2. Rulezi `python3 unelte/punte.py arata` și îi arăți unde ar sta și ce ar scrie. Abia după „da”: `python3 unelte/punte.py instaleaza`.
3. Îi spui cum îl folosește: din orice proiect deschis în Claude Code, „editează reelul din folderul <cale>”. Dacă mută kitul în alt folder,
   rulează din nou `/leaga-de-sistem`. Ca să-l scoată: `python3 unelte/punte.py sterge`.
4. Dacă `instaleaza` spune că acolo e deja un skill străin, nu-l atingi: îi spui ce e și îl lași pe el să decidă.
