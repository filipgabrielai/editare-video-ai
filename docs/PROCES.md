# Procesul, de la filmare la mp4

Același drum pentru orice video. Claude nu deschide un editor: scrie montajul ca pe o pagină web și o randează.

## 1. Filmezi

Pe trepied, fără să miști camera. Lași greșelile și reluările înăuntru: se scot la tăietură. Pentru reels filmezi vertical,
pentru YouTube sau site orizontal. Lumină pe față, microfonul aproape.

## 2. Ascultă

- `duble.py` împarte fiecare clip pe tăceri și transcrie fiecare dublă local, cu Whisper. Nimic nu pleacă de pe calculator.
- Claude citește toate dublele și alege: de regulă ultima dublă întreagă a fiecărei fraze.
- `false_starturi.py` caută reluările ascunse în dublele alese (o încercare ruptă, o pauză scurtă, fraza din nou).
- `cuvinte.py` scoate fiecare cuvânt cu secunda lui. De aici vin tăietura, subtitrările și momentul fiecărui card.

## 3. Se uită

Claude scoate cadre din filmare și le citește: unde e capul, ce e liber în cadru, ce e pe ecran. De aici vin pozițiile:
cardurile nu acoperă fața, subtitrările stau pe guler sau pe piept, nimic important în zonele acoperite de aplicație.

## 4. Construiește

- **Tăietura** (`taietura.py`), exactă pe cadre: între fraze rămân 0,06–0,10 s; în interiorul unei fraze, aproape nimic;
  finalul rămâne 0,25 s pe om. Capetele care scurtează o bucată se ascultă, ca niciun cuvânt să nu rămână ciuntit. Întâi
  tăietura, apoi efectele: altfel se mută toate.
- **Planul pe momente**, aprobat de tine înainte de construcție.
- **Scenariul** (`scenariu.json`, vezi `docs/SCENARIU.md`), pornit de la o rețetă din `retete/`.
- **Compoziția** (`compozitie.py`) pune piesele pe cuvintele lor; **planșele** (`planse.py`) arată cadrele cu zonele acoperite
  marcate cu roșu.
- **Randarea** (`randeaza.py`) verifică întâi ordinea animațiilor, apoi scoate mp4-ul și îl verifică: numărul de cadre, cadre
  negre, sincronul vocii, tăieturile de imagine pe cele de sunet, −14 LUFS. Un draft care pică nu se livrează.

## 5. Te uiți și dai note

Primești un DRAFT. Îi scrii ca unui editor: o schimbare pe rând, cu secunda și cu ce vrei să vezi. Claude repară, randează un
draft nou și îl verifică din nou. FINAL se face doar când zici tu.

Un reel clasic iese din prima rundă sau a doua. Un video cu efecte se face în conversație, draft cu draft: socotește câteva runde.
