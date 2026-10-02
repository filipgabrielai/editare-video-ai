// Două controale înainte de randare, în browserul adus de HyperFrames:
//  1. ordinea: starea fiecărui element cu id trebuie să fie aceeași când timeline-ul e parcurs înainte și când se sare la
//     aceleași momente în ordine amestecată (randarea pe mai mulți lucrători sare). O diferență e un tween care depinde de ce
//     a rulat înaintea lui.
//  2. ce e vizibil și când, pentru elementele date prin selector.
// Uz: node verificare/ordine.cjs <rădăcina kitului> <pagina.html> <browser> <lățime> <înălțime> <selector>   → JSON pe ieșire
const path = require("path");
const { pathToFileURL } = require("url");
const [kit, pagina, exe, w, h, selector] = process.argv.slice(2);
const puppeteer = require(path.join(kit, "node_modules", "puppeteer-core"));

(async () => {
  const browser = await puppeteer.launch({ executablePath: exe, headless: true,
    args: ["--autoplay-policy=no-user-gesture-required", "--allow-file-access-from-files"] });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width: parseInt(w, 10), height: parseInt(h, 10) });
    await page.goto(pathToFileURL(path.resolve(pagina)).href, { waitUntil: "load" });
    await new Promise(r => setTimeout(r, 1000));
    const rez = await page.evaluate((selector) => {
      const cid = Object.keys(window.__timelines || {})[0];
      if (!cid) return { eroare: "pagina nu are niciun timeline (window.__timelines)" };
      const tl = window.__timelines[cid];
      const dur = tl.duration();
      const els = [...document.querySelectorAll("[id]")].filter(e => !["VIDEO", "AUDIO", "SCRIPT"].includes(e.tagName));
      const stare = () => els.map(e => { const c = getComputedStyle(e);
        const tr = c.transform === "matrix(1, 0, 0, 1, 0, 0)" ? "none" : c.transform;   // identitatea e totuna cu „none”
        return [c.visibility === "hidden" ? 0 : Math.round(parseFloat(c.opacity) * 100), tr, c.color, c.height].join("|"); });
      const timpi = []; for (let t = 0.35; t < dur; t += 0.731) timpi.push(Math.round(t * 1000) / 1000);
      const inainte = {}; for (const t of timpi) { tl.seek(t, false); inainte[t] = stare(); }
      const am = timpi.slice(); let s = 12345;   // amestecat, dar la fel de fiecare dată
      for (let i = am.length - 1; i > 0; i--) { s = (s * 1103515245 + 12345) % 2147483648; const j = s % (i + 1); [am[i], am[j]] = [am[j], am[i]]; }
      const dif = [];
      for (const t of am) { tl.seek(t, false); const st = stare(); st.forEach((v, i) => { if (v !== inainte[t][i]) dif.push([t, els[i].id, inainte[t][i], v]); }); }
      const beat = selector ? [...document.querySelectorAll(selector)].filter(e => e.id) : [];
      const viz = {}; beat.forEach(e => viz[e.id] = []);
      const zecime = t => Math.round(t * 10) / 10;
      for (let k = 0; k <= Math.floor(dur * 10); k++) {
        const t = k / 10;
        tl.seek(t, false);
        beat.forEach(e => { const c = getComputedStyle(e);
          if (c.visibility !== "hidden" && parseFloat(c.opacity) > 0.02) { const a = viz[e.id];
            if (a.length && t - a[a.length - 1][1] < 0.151) a[a.length - 1][1] = zecime(t); else a.push([zecime(t), zecime(t)]); } });
      }
      return { dur, n: els.length, momente: timpi.length, ndif: dif.length, dif: dif.slice(0, 20), viz };
    }, selector);
    process.stdout.write(JSON.stringify(rez));
  } finally {
    await browser.close();
  }
})().catch(e => { process.stderr.write(String(e && e.stack || e)); process.exit(1); });
