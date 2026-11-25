// Canvas UI for the guest room prototype. Rules are in engine.js, tuning in balance.js.
import { BALANCE as B } from './balance.js';
import * as E from './engine.js';

const $ = (s) => document.querySelector(s);
const SAVE = 'sushi-loop-guest-room-v3';
const fresh = new URLSearchParams(location.search).has('fresh');
const canvas = $('#board'), ctx = canvas.getContext('2d');
const INK = '#2a2f45', GOLD = '#e0a12f', RED = '#d0443a';
const N = B.size, STREET = 1.4;
const SPEEDS = [1, 4, 16];

let state = load() || E.createGame(Date.now() % 100000);
let tool = null, style = state.items[0]?.style || 'zen', sel = null, drag = null, warn = null;
let speed = 0, acc = 0, last = performance.now(), effects = [], drawn = new Map(), history = [];
let W = 0, H = 0, dpr = 1, G = { s: 40, ox: 0, oy: 0 };

function load() {
  if (fresh) return null;
  try { const s = JSON.parse(localStorage.getItem(SAVE)); return s?.v === 3 ? { ...s, events: [] } : null; } catch { return null; }
}
function save() { if (!fresh) try { localStorage.setItem(SAVE, JSON.stringify({ ...state, events: [] })); } catch { /* storage may be off */ } }

// --- geometry --------------------------------------------------------------------------------------------
function resize() {
  const r = canvas.getBoundingClientRect();
  dpr = Math.min(3, window.devicePixelRatio || 1); W = r.width; H = r.height;
  canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
  // a little more room on the left, where the kitchen hatch sticks out of the wall
  const s = Math.floor(Math.min(W / (N + 1.1), H / (N + STREET + 0.2)));
  G = { s, ox: (W - s * (N + 0.7)) / 2 + s * 0.7, oy: (H - s * (N + STREET)) / 2 };
}
new ResizeObserver(resize).observe(canvas); resize();
const px = (x, y) => [G.ox + x * G.s, G.oy + y * G.s]; // tile space (floats) to canvas pixels
const centre = (x, y) => { const r = canvas.getBoundingClientRect(), [a, b] = px(x + 0.5, y + 0.5); return [r.left + a, r.top + b]; };
function cellAt(e) {
  const r = canvas.getBoundingClientRect();
  const x = Math.floor((e.clientX - r.left - G.ox) / G.s), y = Math.floor((e.clientY - r.top - G.oy) / G.s);
  return x >= 0 && y >= 0 && x < N && y < N ? [x, y] : null;
}

// --- input -----------------------------------------------------------------------------------------------
function say(res) { if (!res.ok && res.why) { warn = { text: res.why, until: performance.now() + 2400 }; ui(); } return res.ok; }
// A multi-tile piece is put down so the tapped tile is inside it, whichever corner fits.
function anchors(kind, x, y, rot = 0) {
  const [w, h] = E.size(kind, rot), out = [];
  for (let dy = 0; dy < h; dy++) for (let dx = 0; dx < w; dx++) out.push([x - dx, y - dy]);
  return out;
}
function placeAt(x, y) {
  let first = null;
  for (const [ax, ay] of anchors(tool, x, y)) {
    const r = E.place(state, tool, ax, ay, style);
    if (r.ok) { sel = r.item.id; pop(r.item.x + 0.5, r.item.y + 0.5, '✨'); return; }
    first ||= r;
  }
  say(first);
}
canvas.addEventListener('pointerdown', (e) => {
  const c = cellAt(e);
  if (!c) return;
  canvas.setPointerCapture(e.pointerId);
  if (tool) { placeAt(...c); save(); ui(); return; }
  const item = E.itemAt(state, E.key(...c));
  if (item && item.id === sel) drag = { id: item.id, dx: c[0] - item.x, dy: c[1] - item.y, at: c, moved: false };
  else { sel = item?.id ?? null; ui(); }
});
canvas.addEventListener('pointermove', (e) => {
  if (!drag) return;
  const c = cellAt(e);
  if (c && (c[0] !== drag.at[0] || c[1] !== drag.at[1])) { drag.at = c; drag.moved = true; }
});
canvas.addEventListener('pointerup', () => {
  if (drag?.moved) { say(E.move(state, drag.id, drag.at[0] - drag.dx, drag.at[1] - drag.dy)); save(); ui(); }
  drag = null;
});

// --- dock --------------------------------------------------------------------------------------------------
const parts = $('#parts');
for (const [kind, K] of Object.entries(B.items)) {
  const b = document.createElement('button');
  b.dataset.kind = kind; b.setAttribute('aria-pressed', 'false'); b.title = K.does;
  b.innerHTML = `<em>${K.icon}</em>${K.name}<s>${K.price}</s>`;
  b.onclick = () => { tool = tool === kind ? null : kind; sel = null; ui(); };
  parts.append(b);
}
const styles = $('#styles');
for (const [id, S] of Object.entries(B.styles)) {
  const b = document.createElement('button');
  b.dataset.style = id; b.setAttribute('role', 'radio'); b.setAttribute('aria-label', S.name); b.title = S.name;
  b.innerHTML = `<i style="background:${S.base};box-shadow:inset 0 0 0 3px ${S.accent}"></i>`;
  b.onclick = () => { style = id; ui(); };
  styles.append(b);
}
$('#cap').onclick = () => { if (say(E.buyCapacity(state))) { banner(`The room now holds ${E.capacity(state)}`); save(); } ui(); };
$('#kit').onclick = () => { if (say(E.buyKitchen(state))) { banner(`The kitchen sends ${E.kitchenRate(state)} plates a minute`); save(); } ui(); };
$('#cheat').onclick = () => { state.coins += 10000; save(); ui(); };
$('#speed').onclick = () => { speed = (speed + 1) % SPEEDS.length; ui(); };
$('#reset').onclick = () => {
  if (!confirm('Start the guest room over?')) return;
  state = E.createGame(Date.now() % 100000); sel = null; tool = null; history = []; drawn.clear(); save(); ui();
};
$('#sel').addEventListener('click', (e) => {
  const act = e.target.closest('button')?.dataset.act;
  if (!act) return;
  if (act === 'done') tool = null;
  if (act === 'up') say(E.upgrade(state, sel));
  if (act === 'turn') say(E.turn(state, sel));
  if (act === 'paint') say(E.restyle(state, sel, style));
  if (act === 'sell' && say(E.sell(state, sel))) sel = null;
  save(); ui();
});

function banner(text, bad) {
  const b = $('#banner');
  b.innerHTML = `<span>${text}</span>`; b.classList.toggle('bad', !!bad);
  b.classList.remove('show'); void b.offsetWidth; b.classList.add('show');
}
function pop(x, y, text, color = INK) { effects.push({ x, y, text, color, born: performance.now() }); }

const fmt = (n) => Math.round(n).toLocaleString('en-US');
function ui() {
  $('#coins').textContent = fmt(state.coins);
  const now = state.t, old = history.find((h) => now - h.t <= 240) || history[0];
  const perMin = old && now > old.t ? (state.stats.earned - old.earned) / ((now - old.t) / 240) : 0;
  $('#rate').textContent = `${fmt(perMin)} / min`;
  const th = E.theme(state);
  $('#appeal').textContent = `★ ${E.appeal(state).toFixed(0)}`;
  $('#theme').innerHTML = th.style
    ? `<i style="background:${B.styles[th.style].base}"></i>${Math.round(th.coherence * 100)}% ×${th.mult.toFixed(1)}`
    : '—';
  $('#theme').title = th.style ? `${B.styles[th.style].name}: ${Math.round(th.coherence * 100)}% of the pieces match` : '';
  const q = state.queue.reduce((s, p) => s + p.size, 0);
  $('#inside').textContent = `${E.inside(state)}/${E.capacity(state)}${q ? ` +${q}` : ''}`;
  $('#traffic').textContent = `${E.traffic(state).toFixed(1)}/min${E.playing(state) ? ' 🎸' : ''}`;

  const flow = $('#flow');
  if (warn && performance.now() < warn.until) { flow.textContent = warn.text; flow.className = 'warn'; }
  else { const l = E.limit(state); flow.textContent = l.text; flow.className = l.kind === 'ok' ? '' : 'warn'; }

  for (const b of parts.children) {
    b.setAttribute('aria-pressed', String(b.dataset.kind === tool));
    b.classList.toggle('poor', state.coins < B.items[b.dataset.kind].price);
  }
  for (const b of styles.children) b.setAttribute('aria-checked', String(b.dataset.style === style));
  const cp = E.capPrice(state), kp = E.kitchenPrice(state);
  $('#cap').innerHTML = cp == null ? `Capacity ${E.capacity(state)}<br>max` : `Capacity ${E.capacity(state)} → ${B.capacity.size[state.cap + 1]}<br><s>${fmt(cp)}</s>`;
  $('#kit').innerHTML = kp == null ? `Kitchen ${E.kitchenRate(state)}/min<br>max` : `Kitchen ${E.kitchenRate(state)} → ${B.kitchen.perMin[state.kitchen + 1]}/min<br><s>${fmt(kp)}</s>`;
  $('#cap').disabled = cp == null; $('#kit').disabled = kp == null;

  const box = $('#sel'), item = sel != null && E.byId(state, sel);
  if (tool) {
    const K = B.items[tool];
    box.innerHTML = `<p><b>${K.icon} ${K.names?.[style] || K.name}</b> · ${B.styles[style].name}<br>${K.does}. Tap the floor${K.onBelt ? ' over the belt' : K.chairs ? ' beside the belt' : ''}.</p><button data-act="done">Done</button>`;
  } else if (item) {
    const K = E.spec(item), cost = E.upgradeCost(item);
    const who = K.chairs ? ` · seats ${K.chairs}` : K.spots ? ` · ${K.spots} player` : '';
    box.innerHTML = `<p><b>${K.icon} ${E.nameOf(item)}</b> ${'★'.repeat(item.tier)}${'☆'.repeat(3 - item.tier)}<br>charm ${E.charm(item).toFixed(0)}${who}${K.pay ? ` · pays ×${K.pay}` : ''} · drag to move</p>`
      + (item.style !== style ? `<button data-act="paint" title="Repaint in ${B.styles[style].name}, free"><i style="display:inline-block;width:10px;height:10px;border-radius:3px;background:${B.styles[style].base}"></i> Paint</button>` : '')
      + (K.w !== K.h ? '<button data-act="turn">Turn</button>' : '')
      + `<button class="buy" data-act="up" ${cost == null ? 'disabled' : ''}>${cost == null ? 'Max' : `★ ${fmt(cost)}`}</button>`
      + `<button data-act="sell">Sell +${fmt(item.spent)}</button>`;
  } else box.innerHTML = '<p>Tap a piece to select it, or pick one below and tap the floor. Selling refunds in full.</p>';
}

// --- events ------------------------------------------------------------------------------------------------
const EMOTE = { cheer: '⚽', dance: '🎵', hungry: '😋', grumpy: '😠', happy: '♥' };
function events() {
  for (const ev of state.events) {
    if (ev.type === 'coin') pop(ev.x, ev.y - 0.3, `+${ev.pay}`, '#9a6a0c');
    else if (EMOTE[ev.type]) pop(ev.x, ev.y - 0.35, EMOTE[ev.type], ev.type === 'grumpy' ? RED : '#c2417a');
    else if (ev.type === 'goal') { const tv = E.byId(state, ev.id); if (tv) { tv.flash = performance.now(); pop(tv.x + 0.5, tv.y, 'GOAL!', '#2f8a3a'); } }
    else if (ev.type === 'set') banner('🎸 The band starts a set: everyone is hungry again');
    else if (ev.type === 'away') pop(B.door[0] + 0.5, N + 0.6, ev.why === 'full' ? 'Full 💨' : ev.why === 'seat' ? 'No seat 💨' : '💨', RED);
  }
  state.events = [];
}

// --- drawing -------------------------------------------------------------------------------------------------
const rr = (x, y, w, h, r) => { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); };
const circle = (x, y, r) => { ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); };
function emoji(t, x, y, size) { ctx.font = `${size}px system-ui, "Apple Color Emoji", sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(t, x, y); }
const ringPos = (i) => { const [x, y] = B.ring[(i + B.ring.length) % B.ring.length]; return [x + 0.5, y + 0.5]; };

function room() {
  const s = G.s, [x0, y0] = px(0, 0);
  // street
  ctx.fillStyle = '#cfc7b8'; ctx.fillRect(x0 - s * 0.2, y0 + N * s, N * s + s * 0.4, STREET * s);
  ctx.fillStyle = '#b9b09f'; for (let i = 0; i < N * 2; i++) ctx.fillRect(x0 + i * s / 2, y0 + (N + STREET * 0.55) * s, s * 0.25, 2);
  // floor: boards tinted by the room's style
  const th = E.theme(state), S = th.style && B.styles[th.style];
  ctx.fillStyle = '#efe4cf'; ctx.fillRect(x0, y0, N * s, N * s);
  if (S) { ctx.globalAlpha = 0.08 + 0.12 * th.coherence; ctx.fillStyle = S.base; ctx.fillRect(x0, y0, N * s, N * s); ctx.globalAlpha = 1; }
  ctx.strokeStyle = 'rgba(42,47,69,.07)'; ctx.lineWidth = 1;
  for (let i = 1; i < N; i++) { ctx.beginPath(); ctx.moveTo(x0 + i * s, y0); ctx.lineTo(x0 + i * s, y0 + N * s); ctx.moveTo(x0, y0 + i * s); ctx.lineTo(x0 + N * s, y0 + i * s); ctx.stroke(); }
  // walls, with the door gap and the kitchen hatch
  const t = Math.max(4, s * 0.12);
  ctx.fillStyle = INK;
  ctx.fillRect(x0 - t, y0 - t, N * s + 2 * t, t);
  ctx.fillRect(x0 + N * s, y0 - t, t, N * s + 2 * t);
  ctx.fillRect(x0 - t, y0 + N * s, B.door[0] * s + t, t);
  ctx.fillRect(x0 + (B.door[0] + 1) * s, y0 + N * s, (N - B.door[0] - 1) * s + t, t);
  ctx.fillRect(x0 - t, y0 - t, t, B.hatch[1] * s + t);
  ctx.fillRect(x0 - t, y0 + (B.hatch[1] + 1) * s, t, (N - B.hatch[1] - 1) * s + t);
  // hatch: a steel window in the wall the kitchen pushes plates through
  const [hx, hy] = px(...B.hatch);
  ctx.fillStyle = '#9aa3ad'; rr(hx + s * 0.35, hy + s * 0.06, s * 0.62, s * 0.88, s * 0.12); ctx.fill();
  emoji('🍳', hx + s * 0.62, hy + s * 0.5, s * 0.36);
  // door mat
  const [dx, dy] = px(...B.door);
  ctx.fillStyle = '#a5523a'; rr(dx + s * 0.15, dy + s * 0.55, s * 0.7, s * 0.38, s * 0.08); ctx.fill();
}

function beltTrack() {
  const s = G.s, n = B.ring.length;
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.strokeStyle = '#59606f'; ctx.lineWidth = s * 0.78;
  ctx.beginPath(); B.ring.forEach(([x, y], i) => { const [a, b] = px(x + 0.5, y + 0.5); i ? ctx.lineTo(a, b) : ctx.moveTo(a, b); }); ctx.closePath(); ctx.stroke();
  ctx.strokeStyle = '#7b8292'; ctx.lineWidth = s * 0.6; ctx.stroke();
  // chevrons, drifting with the belt
  const phase = beltPhase();
  ctx.strokeStyle = 'rgba(255,255,255,.28)'; ctx.lineWidth = Math.max(1.5, s * 0.04);
  for (let i = 0; i < n; i++) {
    const a = ringPos(i), b = ringPos(i + 1), p = [a[0] + (b[0] - a[0]) * phase, a[1] + (b[1] - a[1]) * phase];
    const [cx, cy] = px(...p), ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(ang);
    ctx.beginPath(); ctx.moveTo(-s * 0.08, -s * 0.16); ctx.lineTo(s * 0.06, 0); ctx.lineTo(-s * 0.08, s * 0.16); ctx.stroke();
    ctx.restore();
  }
}
let frac = 0;
const beltPhase = () => ((state.t % B.beltEvery) + frac) / B.beltEvery;

function stars(item, x, y) {
  if (item.tier < 2) return;
  ctx.fillStyle = GOLD; ctx.font = `700 ${Math.round(G.s * 0.2)}px system-ui`; ctx.textAlign = 'right'; ctx.textBaseline = 'top';
  ctx.fillText('★'.repeat(item.tier - 1), x, y);
}
function chairs(item) {
  const S = B.styles[item.style];
  item.who.forEach((_, i) => { const [x, y] = px(...E.chairPos(item, i)); ctx.fillStyle = S.accent; circle(x, y, G.s * 0.3); ctx.fill(); ctx.strokeStyle = S.dark; ctx.lineWidth = 1.5; ctx.stroke(); });
}
function piece(item, now) {
  const s = G.s, S = B.styles[item.style], [w, h] = E.size(item.kind, item.rot), [x, y] = px(item.x, item.y);
  const W2 = w * s, H2 = h * s, cx = x + W2 / 2, cy = y + H2 / 2;
  ctx.lineWidth = 2;
  switch (item.kind) {
    case 'stool':
      ctx.fillStyle = S.dark; circle(cx, cy, s * 0.3); ctx.fill();
      ctx.fillStyle = S.base; circle(cx, cy, s * 0.24); ctx.fill();
      break;
    case 'cage': {
      // hangs from the ceiling: a chain to the top of the tile, a dome of bars, a round floor
      ctx.strokeStyle = S.dark; ctx.beginPath(); ctx.moveTo(cx, y + 1); ctx.lineTo(cx, cy - s * 0.42); ctx.stroke();
      ctx.fillStyle = S.accent; circle(cx, cy, s * 0.42); ctx.fill();
      ctx.strokeStyle = S.base; ctx.lineWidth = Math.max(1.5, s * 0.035);
      for (let i = -3; i <= 3; i++) { const dx = (i / 3.5) * s * 0.42, dy = Math.sqrt(Math.max(0, (s * 0.42) ** 2 - dx * dx)); ctx.beginPath(); ctx.moveTo(cx + dx, cy - dy); ctx.lineTo(cx + dx, cy + dy); ctx.stroke(); }
      ctx.lineWidth = Math.max(2, s * 0.06); circle(cx, cy, s * 0.42); ctx.stroke();
      break;
    }
    case 'booth': {
      // 2x2: a bench down each side and the table between them, two guests facing two
      ctx.fillStyle = S.dark; rr(x + s * 0.05, y + s * 0.05, W2 - s * 0.1, H2 - s * 0.1, s * 0.16); ctx.fill();
      ctx.fillStyle = S.base;
      rr(x + s * 0.1, y + s * 0.1, s * 0.62, H2 - s * 0.2, s * 0.12); ctx.fill();
      rr(x + W2 - s * 0.72, y + s * 0.1, s * 0.62, H2 - s * 0.2, s * 0.12); ctx.fill();
      ctx.fillStyle = S.accent; rr(cx - s * 0.2, y + s * 0.16, s * 0.4, H2 - s * 0.32, s * 0.08); ctx.fill();
      ctx.strokeStyle = S.dark; ctx.lineWidth = 1.5; ctx.stroke();
      break;
    }
    case 'glass': {
      // two guests side by side behind glass, a candle between them
      ctx.fillStyle = 'rgba(190,225,240,.45)'; rr(x + s * 0.05, y + s * 0.05, W2 - s * 0.1, H2 - s * 0.1, s * 0.12); ctx.fill();
      ctx.strokeStyle = S.base; ctx.lineWidth = Math.max(3, s * 0.07); ctx.stroke();
      chairs(item);
      ctx.strokeStyle = 'rgba(255,255,255,.85)'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(x + s * 0.14, y + s * 0.4); ctx.lineTo(x + s * 0.34, y + s * 0.16); ctx.moveTo(x + W2 - s * 0.34, y + H2 - s * 0.14); ctx.lineTo(x + W2 - s * 0.14, y + H2 - s * 0.36); ctx.stroke();
      emoji('🕯️', cx, cy, s * 0.24);
      break;
    }
    case 'pinball':
      ctx.fillStyle = S.dark; rr(x + s * 0.18, y + s * 0.06, s * 0.64, s * 0.72, s * 0.1); ctx.fill();
      ctx.fillStyle = S.base; rr(x + s * 0.24, y + s * 0.12, s * 0.52, s * 0.5, s * 0.06); ctx.fill();
      for (let i = 0; i < 3; i++) { ctx.fillStyle = (Math.floor(now / 200) + i) % 3 ? S.accent : '#fff'; circle(x + s * (0.36 + i * 0.14), y + s * (0.26 + (i % 2) * 0.16), s * 0.05); ctx.fill(); }
      break;
    case 'tv': {
      const lit = item.flash && now - item.flash < 1200;
      ctx.fillStyle = S.dark; rr(x + s * 0.08, y + s * 0.16, s * 0.84, s * 0.58, s * 0.06); ctx.fill();
      ctx.fillStyle = lit && Math.floor(now / 150) % 2 ? '#f2c14e' : '#3d8f4a'; ctx.fillRect(x + s * 0.14, y + s * 0.22, s * 0.72, s * 0.46);
      ctx.strokeStyle = 'rgba(255,255,255,.7)'; ctx.lineWidth = 1; ctx.strokeRect(x + s * 0.2, y + s * 0.28, s * 0.6, s * 0.34);
      ctx.beginPath(); ctx.moveTo(cx, y + s * 0.28); ctx.lineTo(cx, y + s * 0.62); ctx.stroke();
      ctx.fillStyle = S.base; ctx.fillRect(cx - s * 0.12, y + s * 0.74, s * 0.24, s * 0.08);
      break;
    }
    case 'band': {
      ctx.fillStyle = S.dark; rr(x + s * 0.05, y + s * 0.05, W2 - s * 0.1, H2 - s * 0.1, s * 0.12); ctx.fill();
      ctx.fillStyle = S.base; rr(x + s * 0.12, y + s * 0.12, W2 - s * 0.24, H2 - s * 0.24, s * 0.08); ctx.fill();
      const on = E.playing(state), bob = on ? Math.sin(now / 120) * s * 0.05 : 0;
      emoji('🎸', x + s * 0.6, y + s * 0.75 + bob, s * 0.48);
      emoji('🥁', x + s * 1.35, y + s * 0.6 - bob, s * 0.48);
      emoji('🎤', x + s * 1.1, y + s * 1.4 + bob, s * 0.4);
      if (on) { ctx.fillStyle = S.accent; ctx.font = `700 ${Math.round(s * 0.3)}px system-ui`; ctx.fillText('♪', x + s * 0.3 + Math.sin(now / 300) * 4, y + s * 0.3 - (now / 30) % (s * 0.2)); ctx.fillText('♫', x + s * 1.7, y + s * 1.3 - (now / 25) % (s * 0.25)); }
      break;
    }
  }
  stars(item, x + W2 - 2, y + 2);
}

// An arch stands over the belt, across the way plates run, so it is drawn after them.
function arch(item) {
  const s = G.s, S = B.styles[item.style], i = E.RING.indexOf(E.key(item.x, item.y));
  const a = ringPos(i - 1), b = ringPos(i + 1), along = Math.abs(b[0] - a[0]) >= Math.abs(b[1] - a[1]) ? 'h' : 'v';
  const [cx, cy] = px(item.x + 0.5, item.y + 0.5);
  ctx.save(); ctx.translate(cx, cy); if (along === 'v') ctx.rotate(Math.PI / 2);
  // belt runs along x here; posts sit above and below it
  if (item.style === 'zen') {
    ctx.fillStyle = S.dark; ctx.fillRect(-s * 0.06, -s * 0.5, s * 0.12, s * 0.12); ctx.fillRect(-s * 0.06, s * 0.38, s * 0.12, s * 0.12);
    ctx.fillStyle = '#c8443a'; ctx.fillRect(-s * 0.13, -s * 0.52, s * 0.08, s * 1.04); ctx.fillStyle = INK; ctx.fillRect(-s * 0.17, -s * 0.56, s * 0.05, s * 1.12);
    ctx.fillStyle = '#c8443a'; ctx.fillRect(s * 0.05, -s * 0.46, s * 0.06, s * 0.92);
  } else if (item.style === 'lantern') {
    ctx.strokeStyle = S.dark; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(0, -s * 0.5); ctx.quadraticCurveTo(s * 0.12, 0, 0, s * 0.5); ctx.stroke();
    for (const t of [-0.3, 0, 0.3]) { ctx.fillStyle = S.base; ctx.beginPath(); ctx.ellipse(s * 0.06, t * s, s * 0.09, s * 0.12, 0, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = S.accent; ctx.fillRect(s * 0.03, t * s - s * 0.13, s * 0.06, s * 0.03); }
    ctx.fillStyle = S.dark; ctx.fillRect(-s * 0.05, -s * 0.52, s * 0.1, s * 0.1); ctx.fillRect(-s * 0.05, s * 0.42, s * 0.1, s * 0.1);
  } else {
    ctx.globalAlpha = 0.6; ctx.fillStyle = S.base; rr(-s * 0.32, -s * 0.48, s * 0.64, s * 0.96, s * 0.3); ctx.fill(); ctx.globalAlpha = 1;
    ctx.strokeStyle = S.accent; ctx.lineWidth = 2;
    for (const t of [-0.2, 0, 0.2]) { ctx.beginPath(); ctx.moveTo(t * s - s * 0.06, -s * 0.42); ctx.quadraticCurveTo(t * s + s * 0.1, 0, t * s - s * 0.06, s * 0.42); ctx.stroke(); }
  }
  ctx.restore();
  stars(item, cx + s / 2 - 2, cy - s / 2 + 2);
}

function plates() {
  const s = G.s, phase = beltPhase();
  state.plates.forEach((p, i) => {
    if (!p) return;
    const a = ringPos(i), b = ringPos(i + 1), [x, y] = px(a[0] + (b[0] - a[0]) * phase, a[1] + (b[1] - a[1]) * phase);
    ctx.fillStyle = '#fff'; circle(x, y, s * 0.24); ctx.fill(); ctx.strokeStyle = '#d0443a'; ctx.lineWidth = 2; ctx.stroke();
    emoji(p.dish, x, y, s * 0.28);
  });
}

function guests(now) {
  const s = G.s, seen = new Set();
  for (const g of state.guests) {
    seen.add(g.id);
    const d = drawn.get(g.id) || [g.x, g.y];
    d[0] += (g.x - d[0]) * 0.25; d[1] += (g.y - d[1]) * 0.25; drawn.set(g.id, d);
    let [x, y] = px(...d);
    if (g.st === 'play') x += Math.sin(now / 90 + g.id) * s * 0.04;
    ctx.globalAlpha = g.st === 'leave' ? 0.6 : 1;
    ctx.fillStyle = `hsl(${g.hue} 55% 62%)`; circle(x, y, s * 0.27); ctx.fill();
    ctx.strokeStyle = INK; ctx.lineWidth = 1.5; ctx.stroke();
    ctx.globalAlpha = 1;
    if (g.st === 'eat' && g.dish) emoji(g.dish, x + s * 0.2, y + s * 0.16, s * 0.24);
    if (g.st !== 'leave') for (let i = 0; i < g.app; i++) { ctx.fillStyle = '#d0443a'; circle(x - (g.app - 1) * s * 0.05 + i * s * 0.1, y - s * 0.36, s * 0.035); ctx.fill(); }
  }
  for (const id of drawn.keys()) if (!seen.has(id)) drawn.delete(id);
  // the queue at the door, one cluster per party
  state.queue.forEach((p, n) => {
    const side = n % 2 ? 1 : -1, slot = Math.floor(n / 2);
    const bx = B.door[0] + 0.5 + side * (1 + slot * 1.1);
    for (let i = 0; i < p.size; i++) {
      const [x, y] = px(bx + ((i % 2) - 0.5) * 0.46 * (p.size > 1), N + 0.55 + Math.floor(i / 2) * 0.46 - (p.size > 2) * 0.1);
      ctx.fillStyle = `hsl(${p.hue} 55% 62%)`; circle(x, y, s * 0.22); ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 1.2; ctx.stroke();
    }
    const [x, y] = px(bx, N + 0.2), f = Math.max(0, p.wait / B.queuePatience);
    ctx.strokeStyle = f > 0.35 ? '#4a9b5f' : RED; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(x - s * 0.25, y); ctx.lineTo(x - s * 0.25 + s * 0.5 * f, y); ctx.stroke();
  });
}

function overlay(now) {
  const s = G.s;
  const item = sel != null && E.byId(state, sel);
  if (item) {
    const [w, h] = E.size(item.kind, item.rot), [x, y] = px(item.x, item.y);
    ctx.strokeStyle = GOLD; ctx.lineWidth = 3; ctx.setLineDash([6, 4]); rr(x + 2, y + 2, w * s - 4, h * s - 4, 8); ctx.stroke(); ctx.setLineDash([]);
    if (drag?.moved) {
      const nx = drag.at[0] - drag.dx, ny = drag.at[1] - drag.dy, ok = E.canPlace(state, item.kind, nx, ny, item.rot, item.id).ok;
      const [gx, gy] = px(nx, ny);
      ctx.fillStyle = ok ? 'rgba(74,155,95,.35)' : 'rgba(208,68,58,.35)'; rr(gx + 2, gy + 2, w * s - 4, h * s - 4, 8); ctx.fill();
    }
  }
  // where the chosen piece could go
  if (tool) {
    ctx.fillStyle = 'rgba(74,155,95,.16)';
    for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) if (E.canPlace(state, tool, x, y).ok) { const [a, b] = px(x, y); ctx.fillRect(a + 3, b + 3, s - 6, s - 6); }
  }
  effects = effects.filter((e) => now - e.born < 1100);
  for (const e of effects) {
    const t = (now - e.born) / 1100, [x, y] = px(e.x, e.y - t * 0.6);
    ctx.globalAlpha = 1 - t * t; ctx.fillStyle = e.color;
    ctx.font = `800 ${Math.round(s * 0.26)}px system-ui, "Apple Color Emoji"`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(e.text, x, y); ctx.globalAlpha = 1;
  }
}

function draw(now) {
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, W, H);
  room();
  beltTrack();
  for (const i of state.items) if (!E.spec(i).onBelt) piece(i, now);
  plates();
  guests(now);
  for (const i of state.items) if (E.spec(i).onBelt) arch(i);
  overlay(now);
}

// --- loop --------------------------------------------------------------------------------------------------
let uiAt = 0, saveAt = 0;
function frame(now) {
  const dt = Math.min(1000, now - last); last = now;
  acc += dt * SPEEDS[speed];
  let n = 0;
  while (acc >= B.tickMs && n++ < 200) {
    acc -= B.tickMs; E.tick(state); events();
    if (state.t % 20 === 0) { history.push({ t: state.t, earned: state.stats.earned }); if (history.length > 40) history.shift(); }
  }
  frac = acc / B.tickMs;
  draw(now);
  if (now - uiAt > 250) { uiAt = now; ui(); $('#speed').textContent = `×${SPEEDS[speed]}`; $('#speed').setAttribute('aria-pressed', String(speed > 0)); }
  if (now - saveAt > 2000) { saveAt = now; save(); }
  requestAnimationFrame(frame);
}
ui();
requestAnimationFrame(frame);

window.guestRoom = {
  get state() { return state; }, E, balance: B, centre,
  run(n) { for (let i = 0; i < n; i++) { E.tick(state); events(); } ui(); },
  get sel() { return sel; }, get tool() { return tool; },
};
