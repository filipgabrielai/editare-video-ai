# Piesele

O piesă e un efect testat, pe care Claude îl pune pe cuvintele tale din scenariu. Codul lor e în `piese/`.

| Piesa | Ce face | Unde o scrii în scenariu | Formate | Sisteme |
|---|---|---|---|---|
| `card` | card cu rânduri, chipuri sau o cifră, care intră pe un cuvânt | `carduri` | 9:16 (deasupra capului), 16:9 (lângă tine) | Mac, Windows |
| `subtitrari` | subtitrări cuvânt cu cuvânt, cuvântul spus e colorat | singure, din transcript | 9:16, 16:9 | Mac, Windows |
| `titlu` | titlul care stă sus tot videoul | `titlu` | 9:16, 16:9 | Mac, Windows |
| `zoom` | zoom ușor la fiecare tăietură | singur, la tăieturi | 9:16, 16:9 | Mac, Windows |
| `cuvant` | un cuvânt mare care apare pe o ancoră; e și modelul pentru piesele tale | `momente` | 9:16, 16:9 | Mac, Windows |

Pentru niciuna nu trebuie filmat nimic în plus.

## Piesele tale

Kitul e baza. Animațiile și efectele tale le construiești peste ea, ca piese în `piese/ale-mele/`, și trec prin aceleași
verificări ca piesele kitului. Cum, pas cu pas: `docs/EXTINDERE.md`.

Efectele mari (text în spatele tău, ecran împărțit, obiect în palmă) nu sunt în kit: sunt genul de lucruri pe care ți le
construiești tu, cu Claude, pe baza asta.
