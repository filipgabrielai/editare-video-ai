# Cum îl faci al tău

Kitul e baza: instalarea, procesul, tăietura, subtitrările, cardurile, sunetul și verificarea. Animațiile, culorile și efectele
tale le construiești peste ea, cu Claude. Sunt trei trepte, de la simplu la complex.

Tot ce e al tău stă în două locuri pe care o actualizare a kitului nu le atinge (`git pull`, sau o arhivă nouă dezarhivată
peste același folder): `brand/` și `piese/ale-mele/`. Dacă schimbi direct fișierele kitului, actualizarea următoare poate intra
în conflict cu ce ai schimbat.

## 1. Brandul

`/personalizare`: numele, culorile, fontul, logoul, CTA-ul și preferințele (subtitrări, sunete, filtrul pe față). Detalii în
`docs/PERSONALIZARE.md`.

## 2. Stilul tău, peste al kitului

Creezi `brand/stil.css`. Se încarcă ultimul, după stilul kitului, culorile din brand și stilul pieselor, deci ce scrii acolo
le bate pe toate. Îi poți cere lui Claude: „fă cardurile mai colțuroase și fundalul subtitrărilor mai închis”, iar el scrie în
fișierul ăsta.

Un singur lucru nu se schimbă de aici: culoarea cuvântului spus din subtitrări. O pune kitul, cuvânt cu cuvânt, din culoarea de
accent a brandului; o schimbi din `/personalizare`.

Ce poți schimba, pe nume:

| Ce | Selector |
|---|---|
| cardul | `.card`, cel mic: `.card.compact` |
| eticheta de sus a cardului | `.card .k` |
| rândul și textul lui | `.card .row`, `.card .et`, cuvântul colorat: `.card .et b` |
| iconița | `.ic` |
| chipurile, cifra | `.chip`, `.cifra` |
| titlul | `#titlu` |
| subtitrările | `.cap` (grupul), `.cw` (cuvântul) |

După ce schimbi stilul, uită-te la proba de stil (`python3 procese/editare/proba_stil.py`) și la planșe: înălțimea rândurilor de
card e socotită de kit (84 px pe 9:16, 72 px pe 16:9), deci dacă mărești mult textul, verifică să nu se calce rândurile.

## 3. Piesele tale

O piesă e un efect pe care îl pui pe cuvintele tale: un cuvânt mare, o săgeată, o bară de progres, o imagine care apare.
Îi spui lui Claude ce vrei să vezi, unde și pe ce cuvânt; el scrie piesa.

**Unde stă:** un fișier în `piese/ale-mele/<nume>.py` (numele: litere mici, cifre și `_`). Modelul de la care pornești e
`piese/cuvant.py` (piesa `cuvant` a kitului): îl copiezi sub alt nume și îl schimbi. O piesă a ta numită tot `cuvant` o
înlocuiește pe a kitului. Cardurile, titlul, subtitrările și zoomul sunt ale bazei: le schimbi înfățișarea din
`brand/stil.css`, nu le înlocuiești de aici.

**Cum o folosești:** din scenariu, la `"momente"`, în ordinea din video:

```json
"momente": [
  {"piesa": "cuvant", "id": "suta", "text": "100%", "ancora": "editat", "durata": 1.5},
  {"piesa": "sageata", "id": "s1", "ancora": "uită-te aici"}
]
```

**Regula.** O piesă are o singură funcție, `construieste(ctx, m)`, care întoarce un `Fragment` (HTML, CSS, linii de timeline,
intervale).

Ce verifică kitul singur, și oprește compoziția dacă nu e așa:

1. Elementul de bază al piesei are id-ul `m-<id>` (id-ul momentului din scenariu) și clasa `piesa`; orice alt id începe cu
   `m-<id>-`. Așa nu calcă niciun element al kitului.
2. Piesa își declară intervalul (`intervale`, cu `"el": "m-<id>"`): fără el n-ar apărea nici pe planșe, nici în tabelul de
   vizibilitate.
3. Niciun timp negativ, nici în interval, nici ca poziție pe timeline: o singură poziție negativă împinge toate animațiile
   videoului.
4. Ordinea: testul de dinaintea randării compară timeline-ul parcurs înainte cu cel parcurs amestecat. Un `yoyo` sau `repeat`
   urmat de alt tween pe același element arată bine la previzualizare și greșit în mp4; aici se prinde.
5. O piesă care pică, are o greșeală de scriere sau întoarce altceva decât un `Fragment` e oprită cu numele ei și cu motivul.

Ce ține de tine și de Claude, și se vede pe planșe:

- Timpii vin din transcript: `ctx.ancora("cuvintele pe care intră")`, nu secunde scrise de mână. Tăietura se schimbă de la un
  draft la altul, iar secundele scrise de mână rămân în urmă.
- Fiecare element intră cu `tl.fromTo(...)`, cu starea de plecare scrisă.
- Nimic important în zonele roșii, nimic peste față, nimic peste subtitrări.
- Sunetele se cer prin `ctx.sunete.adauga("pop", t)`: kitul are grijă să nu se calce și să nu se repete.

**Ce primești în `ctx`:** `ctx.ws` (cuvintele cu timpi), `ctx.cuts` (tăieturile), `ctx.durata`, `ctx.format` (`"9:16"` sau
`"16:9"`), `ctx.st` (culorile stilului: `accent`, `accent_rgb`), `ctx.sc` (scenariul), `ctx.ancora(fraza)`, `ctx.sunete`.
În CSS folosești culorile brandului: `var(--accent)`, `var(--accent-2)`, `var(--font-display)`.

**Cum se verifică:** la fel ca orice video. `compozitie.py` face verificările 1, 2, 3 și 5; `planse.py` îți arată piesa în
cadru, cu zonele acoperite; `randeaza.py` rulează întâi testul de ordine, apoi verifică mp4-ul. Un draft care pică nu se
livrează, fie că piesa e a kitului sau a ta.

## Mai departe

Efectele mari (tu decupat de pe fundal cu textul în spate, ecranul împărțit în montaj și filmare brută, un obiect care îți
urmărește palma) nu sunt în kit. Se construiesc tot așa, ca piese ale tale, dar cer mai mult: pregătire la filmare, unelte în
plus (HyperFrames are `remove-background` pentru decupaj) și câteva runde de lucru cu Claude. Kitul îți dă baza pe care le
așezi și verificările prin care trec.
