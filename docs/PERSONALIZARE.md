# Personalizarea

`/personalizare` scrie `brand/brand.json`. Îl poți edita și de mână; `python3 unelte/brand.py` (pe Windows: `python`) îți spune dacă e corect.

```json
{
 "nume": "Ana Pop",
 "culori": {"accent": "#ff5500", "accent_2": "#c2410c"},
 "font": "Fontul meu.ttf",
 "logo": "logo.png",
 "cta": "scrie-mi **CURS** în privat",
 "vocabular": ["Claude Code", "AI", "Ana Pop"],
 "preferinte": {"captions": true, "carduri": "normal", "sunete": "incete", "filtru_fata": "usor", "limba": "ro"}
}
```

- `nume`: apare ca titlu pe cardul de final.
- `culori.accent`: cuvintele colorate, marginea cardurilor, cuvântul spus din captions. `culori.accent_2`: a doua culoare din iconițe.
- `font`: „Geist” (implicit) sau „Instrument Serif” (cu serife), amândouă din kit; ori fișierul fontului tău, pus în `brand/`
  (`.woff2`, `.ttf`, `.otf`), care trebuie să aibă diacriticele românești.
- `logo`: fișierul tău, pus în `brand/` (nu intră în git).
- `cta`: textul cardului de final; `**cuvânt**` iese colorat.
- `vocabular`: numele și cuvintele pe care le spui des și le vrei scrise corect în captions (unelte, brandul tău, „AI”). Transcrierea
  le primește din start și greșește mai rar („despre AI”, nu „despre ei”); ce mai scapă se repară cu corecturi, la fiecare reel.
- `preferinte.captions`: `true` sau `false`.
- `preferinte.carduri`: `normal` sau `putine` (doar hook, 1–2 carduri și finalul).
- `preferinte.sunete`: `normale`, `incete` sau `oprite`.
- `preferinte.filtru_fata`: `niciunul`, `usor` sau `mediu`. Netezește pielea și luminează puțin, ca retușul din CapCut; se aplică pe toată
  imaginea, inclusiv pe înregistrările de ecran.
- `preferinte.limba`: limba în care vorbești, pentru transcriere (`ro`, `en`...). Kitul e testat pe română.

Ce nu e setat rămâne ca în stilul Studio. Proba de stil (`python3 procese/editare/proba_stil.py`) îți arată rezultatul în `brand/proba-stil.jpg`.
