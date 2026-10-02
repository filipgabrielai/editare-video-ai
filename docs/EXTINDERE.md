# Cum îl faci al tău

Kitul e baza: instalarea, procesul, tăietura, subtitrările, cardurile, sunetul și verificarea. Animațiile, culorile și efectele
tale le construiești peste ea, cu Claude. Sunt trei trepte, de la simplu la complex.

Tot ce e al tău stă în două locuri pe care o actualizare a kitului (`git pull` sau o arhivă nouă) nu le atinge: `brand/` și
`piese/ale-mele/`. Dacă schimbi direct fișierele kitului, actualizarea următoare poate intra în conflict cu ce ai schimbat.

## 1. Brandul

`/personalizare`: numele, culorile, fontul, logoul, CTA-ul și preferințele (subtitrări, sunete, filtrul pe față). Detalii în
`docs/PERSONALIZARE.md`.

## 2. Stilul tău, peste al kitului

Creezi `brand/stil.css`. Se încarcă ultimul, deci orice scrii acolo bate stilul kitului și culorile din brand. Îi poți cere lui
Claude: „fă cardurile mai colțuroase și subtitrările galbene”, iar el scrie în fișierul ăsta.

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

**Unde stă:** un fișier în `piese/ale-mele/<nume>.py`. Modelul de la care pornești e `piese/cuvant.py` (piesa `cuvant` a
kitului): îl copiezi sub alt nume și îl schimbi. O piesă a ta cu numele uneia din kit o înlocuiește.

**Cum o folosești:** din scenariu, la `"momente"`, în ordinea din video:

```json
"momente": [
  {"piesa": "cuvant", "id": "suta", "text": "100%", "ancora": "editat", "durata": 1.5},
  {"piesa": "sageata", "id": "s1", "ancora": "uită-te aici"}
]
```

**Regula.** O piesă are o singură funcție, `construieste(ctx, m)`, care întoarce un `Fragment` (HTML, CSS, linii de timeline,
intervale). Ca să treacă prin aceleași verificări ca baza:

1. Elementul ei de bază are id-ul `m-<id>` (id-ul momentului din scenariu) și clasa `piesa`; orice alt id începe cu `m-<id>-`.
   Așa nu calcă niciun element al kitului. Compoziția oprește o piesă care nu respectă asta.
2. Timpii vin din transcript: `ctx.ancora("cuvintele pe care intră")`. Niciodată secunde scrise de mână și niciodată sub zero
   (o poziție negativă împinge toate animațiile videoului; compoziția o refuză).
3. Fiecare element intră cu `tl.fromTo(...)`, cu starea de plecare scrisă. Fără `yoyo` sau `repeat` urmat de alt tween pe
   același element: arată bine la previzualizare și greșit în mp4. Testul de ordine de dinaintea randării prinde asta.
4. Piesa își declară intervalul (`intervale`, cu `"el": "m-<id>"`), ca să apară pe planșe și în tabelul de vizibilitate.
5. Nimic important în zonele roșii de pe planșe, nimic peste față, nimic peste subtitrări.
6. Sunetele se cer prin `ctx.sunete.adauga("pop", t)`: kitul are grijă să nu se calce și să nu se repete.

**Ce primești în `ctx`:** `ctx.ws` (cuvintele cu timpi), `ctx.cuts` (tăieturile), `ctx.durata`, `ctx.format` (`"9:16"` sau
`"16:9"`), `ctx.st` (culorile stilului: `accent`, `accent_rgb`), `ctx.sc` (scenariul), `ctx.ancora(fraza)`, `ctx.sunete`.
În CSS folosești culorile brandului: `var(--accent)`, `var(--accent-2)`, `var(--font-display)`.

**Cum se verifică:** la fel ca orice video. `compozitie.py` oprește id-urile greșite și pozițiile negative; `planse.py` îți
arată piesa în cadru, cu zonele acoperite; `randeaza.py` rulează întâi testul de ordine, apoi verifică mp4-ul. Un draft care pică
nu se livrează, fie că piesa e a kitului sau a ta.

## Mai departe

Efectele mari (tu decupat de pe fundal cu textul în spate, ecranul împărțit în montaj și filmare brută, un obiect care îți
urmărește palma) nu sunt în kit. Se construiesc tot așa, ca piese ale tale, dar cer mai mult: pregătire la filmare, unelte în
plus (HyperFrames are `remove-background` pentru decupaj) și câteva runde de lucru cu Claude. Kitul îți dă baza pe care le
așezi și verificările prin care trec.
