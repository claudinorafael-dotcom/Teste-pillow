/* ---------- X-Wines catalog lookup (offline index published with the page) ---------- */
const XW = { wineries:null, loading:null, shards:{}, SHARDS:128,
  STOP: new Set("de di del della dei do da dos das la le el los las the y e et and en vina vinedos bodega bodegas vinicola cantina cantine tenuta tenute chateau domaine domaines casa wines wine winery figli fratelli herederos familia family famiglia estate estates vineyards vineyard cave caves quinta weingut".split(" ")) };
/* keepPar: catalog names keep what is in parentheses ("Brut (Carte Jaune)"); our own fields drop it ("Montes (Grupo X)"). */
function xwNorm(t, keepPar){ let x = String(t||"").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase(); if (!keepPar) x = x.replace(/\([^)]*\)/g, " "); return x.replace(/[^a-z0-9]+/g, " ").trim(); }
function xwToks(t, keepPar){ return xwNorm(t, keepPar).split(" ").filter(w => w.length > 1 && !XW.STOP.has(w)); }
async function xwLoadWineries(){
  if (XW.wineries) return XW.wineries;
  if (!XW.loading) XW.loading = XW.fetchJson("xw/wineries.json").then(a => { XW.wineries = a.map(([id, name]) => ({ id, name, t: xwToks(name, true), sq: xwNorm(name, true).replace(/ /g, "") })); return XW.wineries; });
  return XW.loading;
}
async function xwShard(wineryId){
  const k = String(wineryId % XW.SHARDS).padStart(3, "0");
  if (!XW.shards[k]) XW.shards[k] = XW.fetchJson(`xw/w/${k}.json`);
  return (await XW.shards[k])[String(wineryId)] || [];
}
/* Returns up to 3 candidates [{score, wineryId, winery, id, name, type, grapes, country, region, abv, body, acid, harm, avg, n, vint}] */
async function xwLookup(q){
  const wineries = await xwLoadWineries();
  const pT = new Set(xwToks(q.produtor)), vT = xwToks(q.vinho), all = new Set([...pT, ...vT, ...xwToks(q.uvas)]);
  const pv = new Set([...pT, ...vT]);
  const sq = xwNorm((q.produtor||"") + " " + (q.vinho||"")).replace(/ /g, "");
  if (!pv.size) return [];
  const cands = [];
  for (const w of wineries){
    if (!w.t.length) continue;
    let m = 0, inP = 0, len = 0;
    for (const t of w.t){ if (pv.has(t)){ m++; len += t.length; if (pT.has(t)) inP++; } }
    const allIn = m === w.t.length, sub = w.sq.length >= 6 && sq.includes(w.sq);
    if (!(allIn || sub || (m >= 2 && m / w.t.length >= 0.66))) continue;
    cands.push({ w, s: (sub && !allIn ? w.sq.length : len) + inP * 3 + (allIn ? 2 : 0), inP });
  }
  cands.sort((a,b) => b.s - a.s);
  const out = [];
  for (const c of cands.slice(0, 8)){
    const wines = await xwShard(c.w.id);
    for (const r of wines){
      const nT = xwToks(r[1], true); if (!nT.length) continue;
      const full = new Set([...nT, ...c.w.t]);
      const cv = vT.length ? vT.filter(t => full.has(t)).length / vT.length : 0;
      const vs = nT.filter(t => all.has(t)).length / nT.length;
      const score = 0.5 * cv + 0.3 * vs + 0.2 * (c.inP ? 1 : 0.6);
      out.push({ score, wineryId:c.w.id, winery:c.w.name, id:r[0], name:r[1], type:r[2], grapes:r[3], country:r[4], region:r[5], abv:r[6], body:r[7], acid:r[8], harm:r[9], avg:r[10], n:r[11], vint:r[12] });
    }
  }
  out.sort((a,b) => b.score - a.score || (b.n||0) - (a.n||0));
  return out.filter(o => o.score >= 0.55).slice(0, 3);
}
function xwVintage(c, safra){ const m = String(c.vint||"").split(",").map(x => x.split(":")).find(x => x[0] === String(safra||"")); return m ? { avg:Number(m[1]), n:Number(m[2]) } : null; }
