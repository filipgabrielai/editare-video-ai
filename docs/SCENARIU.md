# Scenariul unui reel

Claude scrie `proiecte/<slug>/scenariu.json` după ce citește transcriptul și se uită la un cadru din `taiat.mp4`.

```json
{
 "titlu": "Productivitate cu AI",
 "stil": "studio",
 "cadru": {"shift": 120, "carduri_y": 370, "captions_y": 1480},
 "corecturi": {"cloud code": "Claude Code"},
 "carduri": [
  {"id": "hook", "ancora": "start", "kicker": "PRODUCTIVITATE CU AI",
   "randuri": [{"text": "câte lucruri faci cu **AI**", "icoana": "zap"},
               {"text": "cât de **productiv** poți fi", "icoana": "chart-column", "ancora": "cât de productiv"}]},
  {"id": "stanga", "ancora": "Aici în stânga", "kicker": "ÎN STÂNGA · CLAUDE CODE", "compact": true,
   "chips": [{"text": "rulează", "ancora": "rulează"}, {"text": "verifică", "ancora": "verifică"}]}
 ]
}
```

- `titlu` (opțional): stă sus tot reelul, la 262 px. Cu titlu, cardurile pornesc de la 370 px.
- `cadru`: `shift` coboară videoul (capul să nu fie sub tabul Reels), `carduri_y` (≥ 262), `captions_y` (≤ 1480, pe guler).
- `corecturi`: ce a auzit Whisper greșit → cum se afișează în captions. Ancorele rămân cum sunt în `transcript.json`.
- `carduri`: în ordinea din video. `ancora` = „start” sau fraza din transcript pe care intră cardul (scrisă ca în transcript;
  diacriticele, majusculele și punctuația nu contează). Cardul iese când intră următorul; ultimul rămâne până la final.
- `randuri` (max 4): `text` cu `**cuvântul important**` colorat, `icoana` (numele din `stiluri/icoane.json`), `ancora`
  (opțional) pe care apare rândul. Primul rând e mereu static.
- `chips`: etichete scurte; `chips_mod` „aprinde” (stau gri, se aprind pe ancoră) sau „apar” (apar pe ancoră).
- `cifra`: `{"valoare": "80%", "ancora": "..."}`, o cifră mare.
- `compact`: card mic la 262 px, pentru când pe ecran e o înregistrare de ecran (se vede mai mult din ea).
