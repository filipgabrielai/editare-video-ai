# Rețetele

O rețetă e un scenariu de la care pornești: Claude o copiază în `proiecte/<slug>/scenariu.json` și o adaptează la ce ai spus în
video (ancorele „start” devin cuvinte din transcript, textele devin ale tale).

| Rețeta | Pentru ce | Format | Tăietura |
|---|---|---|---|
| `reel-clasic` | reel cu tine la cameră: carduri deasupra capului, subtitrări pe guler | 9:16 | `taietura.py proiecte/<slug>` |
| `orizontal-simplu` | video orizontal cu tine la cameră (YouTube, site, prezentare): cardul lângă tine, subtitrări pe piept | 16:9 | `taietura.py proiecte/<slug> --filmare 16:9` |

Pe orizontală, rândurile de card au cel mult 24 de caractere, iar cardul stă pe partea liberă a cadrului (`cadru.carduri`:
„stanga” sau „dreapta”). Efectele mari (text în spatele tău, ecran împărțit, obiect în palmă) vin ca piese în versiunile
următoare; ce există acum e în `docs/PIESE.md`.
