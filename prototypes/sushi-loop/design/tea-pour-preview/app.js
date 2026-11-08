/* Tea request and pouring review for #62.
   Asset map:
   - Backdrop and depth rows: the #61 native restaurant capture (../cash-preview/assets); assets/scene/ holds copies of
     the backdrop and row 5 with the baked happy bubble removed, so every guest bubble here is live.
   - Happy bubble: the native smile idle sheet (godot/assets/feedback-variants/sprites/bubble-happy/happy-smile-idle-S.png),
     root (46, 119) lifted 83 px to match the bubble height in the live capture.
   - One bubble per guest: a tea request waits for the happy bubble to finish; tapping it dismisses it for the pour.
   - Tea bubble: a code-drawn tea-green button bubble (distinct from the cream thought bubbles) whose rim drains.
   - Teapot: ImageGen cutout (assets/teapot/), rotated about its spout lip.
   - Pouring sheet: HTML/CSS cream panel with the maple top edge and the shared round cream X; the cup,
     tea, stream, marks and arc control are live SVG because their geometry is gameplay data
     (cups.js profile -> capacity). Nothing in the sheet is baked art yet.
   - Rules: balance.js (tuning), cups.js (geometry -> volume), pour.js (tilt -> flow, drips, grading, tip chance).
   - The restaurant clock never pauses while the sheet is open; only the guest being served stops eating. */

import { TEA } from './balance.js';
import { CUPS } from './cups.js';
import { createPour, gradePour, pourDone, tipChance } from './pour.js';

const SCALE = 390 / 720;
const CELL = 113.6923 * SCALE;
const ORIGIN = { x: 56.8462 * SCALE, y: 136.8462 * SCALE };
const center = (x, y) => ({ x: ORIGIN.x + x * CELL, y: ORIGIN.y + y * CELL });
const zFor = (row) => row * 10 + 5;
const SEATS = [
  { id: 'A', x: 2.85, y: 5 }, { id: 'B', x: 4, y: 5 },
  { id: 'C', x: 3, y: 8 }, { id: 'D', x: 5, y: 8 },
];
const BELTS = [{ row: 6, x0: 70, x1: 300, y: 417 }, { row: 9, x0: 130, x1: 362, y: 601 }];
const SVGNS = 'http://www.w3.org/2000/svg';
const SVG_TAGS = new Set(['image', 'g', 'path', 'rect', 'circle', 'ellipse', 'line', 'text', 'defs', 'clipPath', 'linearGradient', 'radialGradient', 'stop']);

// Pour stage layout (sheet SVG units = CSS px).
const CUP_X = 128, CUP_FLOOR = 306;
const POT_SCALE = 1;
const ARC = { x: 292, y: 316, r: 70, sweep: 80 };
const OUTLINE = '#5a3a24';
// Presentation-only decoration: none of it is inside the profile, so none of it holds tea.
const DECOR = {
  flask: { handles: [{ side: -1, y0: 46, y1: 82 }, { side: 1, y0: 46, y1: 82 }] },
  vase: { handles: [{ side: 1, y0: 84, y1: 124 }] },
  hourglass: { knobs: [{ side: -1, y: 76 }, { side: 1, y: 76 }] },
};
const GRADE_TEXT = {
  ideal: { text: 'Perfect pour!', react: '😍', log: 'ideal' },
  good: { text: 'Nice pour', react: '😊', log: 'good' },
  under: { text: 'A bit light…', react: '🙂', log: 'underfilled' },
  full: { text: 'Brimming!', react: '😮', log: 'too full' },
  overflow: { text: 'Overflow!', react: '😲', log: 'overflowed' },
};

const $ = (id) => document.getElementById(id);
const el = (tag, attrs = {}, parent) => {
  const svgTag = tag === 'svg' || parent?.namespaceURI === SVGNS || SVG_TAGS.has(tag);
  const node = svgTag ? document.createElementNS(SVGNS, tag) : document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  parent?.append(node);
  return node;
};
const reduced = () => $('opt-motion').checked || matchMedia('(prefers-reduced-motion: reduce)').matches;
const rand = (a, b) => a + Math.random() * (b - a);

let now = 0;                         // restaurant clock (seconds); never paused by the pouring sheet
let cash = 9180;
let nextCup = 'cycle', cycle = 0;
let nextAmbient = 4;
const guests = SEATS.map((seat, i) => newGuest(seat, i * 1.3));
let active = null;                   // the open pouring interaction

function newGuest(seat, offset = 0) {
  return {
    seat, phase: 'eating', t: offset, meal: TEA.service.mealSeconds, wantsTea: false, teaAsked: 0,
    request: null, pouring: false, visit: { teaGrade: null, bill: 0 }, visitEnds: now + rand(40, 60),
    badge: null, flash: null, mealRequested: false,
  };
}

// ---------------------------------------------------------------- log + money
function log(html) {
  const li = document.createElement('li');
  li.innerHTML = `<b>${now.toFixed(1)}s</b> ${html}`;
  $('log').prepend(li);
  while ($('log').children.length > 40) $('log').lastElementChild.remove();
}
function floatText(text, x, y, muted = false) {
  const node = el('div', { class: muted ? 'gain muted' : 'gain' }, $('fx'));
  node.textContent = text;
  Object.assign(node.style, { left: `${x}px`, top: `${y}px` });
  node.animate([{ transform: 'translate(-50%,-50%) scale(.7)', opacity: 0 }, { transform: 'translate(-50%,-80%)', opacity: 1, offset: 0.25 }, { transform: 'translate(-50%,-170%)', opacity: 0 }], { duration: reduced() ? 600 : 1000, easing: 'ease-out' }).onfinish = () => node.remove();
}
function earn(amount) {
  cash += amount;
  $('wallet-value').textContent = cash;
  $('wallet').setAttribute('aria-label', `${cash} cash`);
}
const head = (g) => center(g.seat.x, g.seat.y - 1.6);

// ---------------------------------------------------------------- requests
function pending() { return guests.filter((g) => g.wantsTea || g.phase === 'tea-wait').length; }

function requestTea(g, source = 'button') {
  if (g.teaAsked >= TEA.request.perVisit) { log(`Guest ${g.seat.id} already had a tea request this visit`); return false; }
  if (g.wantsTea || g.phase === 'tea-wait') return false;
  if (pending() >= TEA.request.maxSimultaneous) { log(`Guest ${g.seat.id}: limit of ${TEA.request.maxSimultaneous} pending requests reached`); return false; }
  g.wantsTea = true;
  g.teaAsked++;
  g.cupId = pickCup();
  log(`Guest ${g.seat.id} wants tea${g.phase === 'eating' ? ' (finishing this dish first)' : ''}${source === 'ambient' ? '' : ' · requested'}`);
  if (g.phase === 'happy') log(`Guest ${g.seat.id}'s tea bubble waits for the happy bubble`);
  if (g.phase === 'gap') beginWaiting(g);
  return true;
}
function pickCup() {
  if (nextCup !== 'cycle') return nextCup;
  return CUPS[cycle++ % CUPS.length].id;
}
function beginWaiting(g) {
  g.wantsTea = false;
  g.phase = 'tea-wait';
  g.request = { start: now, deadline: now + TEA.request.patienceSeconds, total: TEA.request.patienceSeconds, cupId: g.cupId, pour: null };
}
function expire(g) {
  g.request = null;
  g.phase = 'gap'; g.t = 0;
  g.flash = { kind: 'putaway', until: now + 0.8 };
  log(`Guest ${g.seat.id}'s tea request expired · cup put away, eating again`);
}

// ---------------------------------------------------------------- restaurant tick
function tick(dt) {
  now += dt;
  for (const g of guests) {
    g.t += dt;
    if (g.phase === 'eating' && g.t >= g.meal) {
      g.t = 0;
      if (g.mealRequested) {
        // The requested dish earns a happy bubble first; nothing else shows until it finishes.
        g.mealRequested = false;
        g.visit.ateRequestedDish = true;
        g.phase = 'happy';
      } else if (g.wantsTea) beginWaiting(g); else g.phase = 'gap';
    } else if (g.phase === 'happy' && g.t >= TEA.service.happySeconds) {
      g.t = 0;
      g.phase = 'gap';
      if (!g.wantsTea && $('opt-auto').checked && Math.random() < TEA.service.teaAfterHappyChance) requestTea(g, 'ambient');
      if (g.wantsTea) beginWaiting(g);
    } else if (g.phase === 'gap') {
      if (g.wantsTea) beginWaiting(g);
      else if (now >= g.visitEnds && !g.wantsTea) leave(g);
      else if (g.t >= TEA.service.gapSeconds) takeDish(g);
    } else if (g.phase === 'tea-wait') {
      // An open pour is guaranteed: its own deadline never ends it; cancelling or serving settles it.
      if (!g.pouring && now >= g.request.deadline) expire(g);
    } else if (g.phase === 'sipping' && g.t >= TEA.service.sipSeconds) {
      g.phase = 'gap'; g.t = 0;
    }
  }
  if ($('opt-auto').checked && now >= nextAmbient) {
    nextAmbient = now + TEA.request.autoEverySeconds * rand(0.7, 1.3);
    const eligible = guests.filter((g) => g.teaAsked < TEA.request.perVisit && !g.wantsTea && g.phase !== 'tea-wait' && !g.pouring);
    if (eligible.length && pending() < TEA.request.maxSimultaneous) requestTea(eligible[Math.floor(Math.random() * eligible.length)], 'ambient');
  }
  tickPlates(dt);
}
function takeDish(g) {
  const [lo, hi] = TEA.service.dishPrice;
  const price = Math.round(rand(lo, hi));
  g.phase = 'eating'; g.t = 0; g.meal = TEA.service.mealSeconds * rand(0.8, 1.2);
  g.mealRequested = !g.visit.ateRequestedDish && Math.random() < TEA.service.requestedDishChance;
  g.visit.bill += price;
  earn(price);
  const at = head(g);
  floatText(`+$${price}`, at.x + 18, at.y + 30);
}
function leave(g) {
  const chance = tipChance(g.visit, TEA);
  const tipped = g.visit.bill > 0 && Math.random() < chance;
  const amount = Math.max(1, Math.round(g.visit.bill * 0.1));
  const at = head(g);
  if (tipped) { earn(amount); floatText(`tip $${amount}`, at.x, at.y + 20); }
  log(`Guest ${g.seat.id} left · tip chance ${(chance * 100).toFixed(0)}%${g.visit.teaGrade ? ` (tea: ${GRADE_TEXT[g.visit.teaGrade.id].log}${g.visit.teaGrade.qualifies ? '' : ', no bonus'})` : ''} → ${tipped ? `tipped $${amount}` : 'no tip'} · a new guest sits`);
  const fresh = newGuest(g.seat);
  fresh.badge = g.badge;
  Object.assign(g, fresh, { badge: g.badge, happyEl: g.happyEl });
}

// ---------------------------------------------------------------- belts (ambient motion)
const plates = [];
let plateClock = 0;
function tickPlates(dt) {
  plateClock -= dt;
  if (plateClock <= 0) {
    plateClock = 2.4;
    for (const belt of BELTS) {
      const node = el('div', { class: Math.random() < 0.4 ? 'plate maki' : 'plate' }, $('world'));
      node.style.setProperty('--food', ['#f08a5d', '#e8604c', '#f4c36a'][Math.floor(Math.random() * 3)]);
      node.style.zIndex = zFor(belt.row);
      plates.push({ node, belt, x: belt.x0 });
    }
  }
  for (let i = plates.length - 1; i >= 0; i--) {
    const p = plates[i];
    p.x += 26 * dt;
    if (p.x > p.belt.x1) { p.node.remove(); plates.splice(i, 1); continue; }
    p.node.style.left = `${p.x}px`;
    p.node.style.top = `${p.belt.y}px`;
  }
}

// ---------------------------------------------------------------- guest badges
function renderBadges() {
  for (const g of guests) {
    if (!g.badge) {
      g.badge = el('div', { class: 'badge' }, $('badges'));
      const at = head(g);
      Object.assign(g.badge.style, { left: `${at.x}px`, top: `${at.y}px` });
    }
    if (!g.happyEl) {
      g.happyEl = el('div', { class: 'happy-bubble', hidden: '' }, $('badges'));
      const at = center(g.seat.x, g.seat.y);
      Object.assign(g.happyEl.style, { left: `${at.x}px`, top: `${at.y}px` });
    }
    g.happyEl.hidden = g.phase !== 'happy';
    if (g.phase === 'happy') {
      const f = reduced() ? 0 : Math.floor(now * 12) % 12;
      g.happyEl.style.backgroundPosition = `${-(f % 6) * 92}px ${-Math.floor(f / 6) * 154}px`;
    }
    let kind = g.phase;
    if (g.pouring) kind = 'pouring';      // tapped: the tea bubble is dismissed while the pour is open
    if (g.flash && now < g.flash.until) kind = g.flash.kind;
    const left = g.request ? Math.max(0, (g.request.deadline - now) / g.request.total) : 0;
    if (g.badge.dataset.kind !== kind) {
      g.badge.dataset.kind = kind;
      g.badge.replaceChildren();
      if (kind === 'tea-wait') {
        const ask = el('button', { class: 'tea-ask', 'aria-label': `Pour tea for guest ${g.seat.id}` }, g.badge);
        ask.innerHTML = `<span class="tail"></span><span class="face">${teaFace()}</span><svg class="ring" viewBox="0 0 66 66" aria-hidden="true"><circle class="track" cx="33" cy="33" r="31"/><circle class="left" cx="33" cy="33" r="31" pathLength="100"/></svg>`;
        ask.addEventListener('click', (event) => { event.stopPropagation(); openPour(g); });
        el('div', { class: 'cup-gesture', 'aria-hidden': 'true' }, g.badge).innerHTML = cupIcon();
      } else if (kind === 'sipping') {
        const r = el('div', { class: 'react pop' }, g.badge);
        r.textContent = `🍵${GRADE_TEXT[g.lastGrade]?.react ?? ''}`;
      } else if (kind === 'putaway') {
        el('div', { class: 'putaway' }, g.badge).innerHTML = cupIcon(28);
      }
    }
    if (kind === 'tea-wait') {
      const ask = g.badge.querySelector('.tea-ask');
      ask.querySelector('.ring .left').setAttribute('stroke-dasharray', `${(left * 100).toFixed(1)} 100`);
      ask.classList.toggle('low', left <= TEA.request.pulseFraction);
    }
  }
}
function teaFace() {
  return `<svg viewBox="0 0 30 30"><path d="M10 4q-2 3 0 6M15 3q-2 3 0 7M20 4q-2 3 0 6" fill="none" stroke="#fff3dc" stroke-width="2.2" stroke-linecap="round"/><path d="M5 12h18l-2 10q-1 4-5 4h-4q-4 0-5-4z" fill="#fff3dc" stroke="${OUTLINE}" stroke-width="2" stroke-linejoin="round"/><path d="M23 15q4 0 3 4t-4 3" fill="none" stroke="#fff3dc" stroke-width="2.6" stroke-linecap="round"/><ellipse cx="14" cy="12.5" rx="8.5" ry="1.6" fill="#9fcb5c"/></svg>`;
}
function cupIcon(size = 22) {
  return `<svg viewBox="0 0 22 18" width="${size}" height="${size * 18 / 22}"><path d="M3 3h14l-2 11q-1 3-4 3H9q-3 0-4-3z" fill="#f6efe0" stroke="${OUTLINE}" stroke-width="2.5" stroke-linejoin="round"/><path d="M17 6q4 0 3 4t-4 3" fill="none" stroke="${OUTLINE}" stroke-width="2.5"/></svg>`;
}

// ---------------------------------------------------------------- cup drawing (shared with the cup sheet)
function cupGeometry(cup, cx, floor) {
  const s = cup.samples();
  const P = (x, y) => `${x.toFixed(1)} ${y.toFixed(1)}`;
  const left = s.map((p) => [cx + p.dx - p.r, floor - p.y]);
  const right = s.map((p) => [cx + p.dx + p.r, floor - p.y]);
  const interior = `M${P(...left[left.length - 1])} ${left.slice().reverse().map((p) => `L${P(...p)}`).join(' ')} ${right.map((p) => `L${P(...p)}`).join(' ')} Z`;
  const w = cup.wall, b = cup.base, s0 = s[0];
  const outerL = s.map((p) => [cx + p.dx - p.r - w, floor - p.y]);
  const outerR = s.map((p) => [cx + p.dx + p.r + w, floor - p.y]);
  const bottomY = floor + b, rr = Math.min(10, b);
  const outer = `M${P(...outerL[outerL.length - 1])} ${outerL.slice().reverse().map((p) => `L${P(...p)}`).join(' ')}`
    + ` Q${P(cx + s0.dx - s0.r - w, bottomY)} ${P(cx + s0.dx - s0.r - w + rr, bottomY)} L${P(cx + s0.dx + s0.r + w - rr, bottomY)}`
    + ` Q${P(cx + s0.dx + s0.r + w, bottomY)} ${P(...outerR[0])} ${outerR.map((p) => `L${P(...p)}`).join(' ')} Z`;
  const top = s[s.length - 1];
  return { interior, outer, bottomY, s0, top, maxOuter: Math.max(...s.map((p) => Math.abs(p.dx) + p.r)) + w };
}

function drawCup(cup, parent, cx, floor, uid) {
  const geo = cupGeometry(cup, cx, floor);
  const [glazeTop, glazeBottom] = cup.glaze;
  const defs = el('defs', {}, parent);
  const grad = el('linearGradient', { id: `glaze-${uid}`, x1: 0, x2: 1 }, defs);
  el('stop', { offset: 0, 'stop-color': glazeBottom }, grad);
  el('stop', { offset: 0.35, 'stop-color': glazeTop }, grad);
  el('stop', { offset: 1, 'stop-color': glazeBottom }, grad);
  const cavity = el('radialGradient', { id: `cavity-${uid}`, cx: 0.5, cy: 0.15, r: 0.9 }, defs);
  el('stop', { offset: 0, 'stop-color': '#fffaf0' }, cavity);
  el('stop', { offset: 1, 'stop-color': '#ead9bb' }, cavity);
  const clip = el('clipPath', { id: `outer-${uid}` }, defs);
  el('path', { d: geo.outer }, clip);
  // Foot ring, handles and knobs sit outside the profile: decoration only.
  if (cup.foot) {
    const fw = (geo.s0.r + cup.wall) * 0.72;
    el('rect', { x: cx + geo.s0.dx - fw, y: geo.bottomY - 4, width: fw * 2, height: cup.foot + 4, rx: 4, fill: glazeBottom, stroke: OUTLINE, 'stroke-width': 4 }, parent);
  }
  for (const h of DECOR[cup.id]?.handles ?? []) {
    const ya = floor - h.y0, yb = floor - h.y1, xa = cx + cup.shiftAt(h.y0) + h.side * (cup.radiusAt(h.y0) + cup.wall - 2);
    const xb = cx + cup.shiftAt(h.y1) + h.side * (cup.radiusAt(h.y1) + cup.wall - 2);
    const bulge = Math.max(xa * h.side, xb * h.side) * h.side + h.side * 22;
    const d = `M${xa} ${ya} C${bulge} ${ya + 4} ${bulge} ${yb - 4} ${xb} ${yb}`;
    el('path', { d, fill: 'none', stroke: OUTLINE, 'stroke-width': 13, 'stroke-linecap': 'round' }, parent);
    el('path', { d, fill: 'none', stroke: glazeBottom, 'stroke-width': 6, 'stroke-linecap': 'round' }, parent);
  }
  for (const k of DECOR[cup.id]?.knobs ?? []) {
    el('circle', { cx: cx + cup.shiftAt(k.y) + k.side * (cup.radiusAt(k.y) + cup.wall + 4), cy: floor - k.y, r: 8, fill: glazeBottom, stroke: OUTLINE, 'stroke-width': 4 }, parent);
  }
  el('path', { d: geo.outer, fill: `url(#glaze-${uid})` }, parent);
  // Glaze band near the base, clipped to the body.
  const band = el('g', { 'clip-path': `url(#outer-${uid})` }, parent);
  el('rect', { x: cx - 120, y: floor - 16, width: 240, height: 9, fill: cup.band, opacity: 0.85 }, band);
  el('rect', { x: cx - 120, y: floor - cup.height * 0.62, width: 240, height: 3, fill: cup.band, opacity: 0.5 }, band);
  el('path', { d: geo.outer, fill: 'none', stroke: OUTLINE, 'stroke-width': 4, 'stroke-linejoin': 'round' }, parent);
  el('path', { d: geo.interior, fill: `url(#cavity-${uid})`, stroke: OUTLINE, 'stroke-width': 2.5, 'stroke-linejoin': 'round', 'stroke-opacity': 0.75 }, parent);
  // Rounded lip across each rim wall.
  const t = geo.top, rimY = floor - cup.height;
  for (const side of [-1, 1]) {
    el('line', { x1: cx + t.dx + side * t.r, y1: rimY, x2: cx + t.dx + side * (t.r + cup.wall), y2: rimY, stroke: OUTLINE, 'stroke-width': 5, 'stroke-linecap': 'round' }, parent);
  }
  return geo;
}

// ---------------------------------------------------------------- teapot (tip of the spout at 0,0, upright)
// ImageGen ceramic teapot (assets/teapot/: prompts, raw outputs, keyed cutout). teapot-pour.png is that cutout
// cropped to source (180, 160, 1160x741) and drawn at 158x101; the spout lip sits at (4.8, 32.7) and is the pivot.
const POT_ART = new URL('./assets/teapot-pour.png', import.meta.url).href;
const POT_SIZE = { w: 158, h: 101 }, POT_TIP = { x: 4.8, y: 32.7 };
function drawPot(parent, scale = 1) {
  const g = el('g', { transform: `scale(${scale})` }, parent);
  el('image', { href: POT_ART, x: -POT_TIP.x, y: -POT_TIP.y, width: POT_SIZE.w, height: POT_SIZE.h }, g);
  return g;
}

// ---------------------------------------------------------------- pouring sheet
const svg = $('pour');
function arcPoint(deg, r = ARC.r) {
  const a = deg * Math.PI / 180;
  return { x: ARC.x + r * Math.sin(a), y: ARC.y - r * Math.cos(a) };
}
function arcPath(deg) {
  const a = arcPoint(0), b = arcPoint(Math.max(0.01, deg));
  return `M${a.x} ${a.y} A${ARC.r} ${ARC.r} 0 0 1 ${b.x} ${b.y}`;
}
$('arc-track').setAttribute('d', arcPath(ARC.sweep));
$('arc-hit').setAttribute('d', arcPath(ARC.sweep));
drawPot(el('g', { transform: 'translate(-16 -4)' }, $('knob-pot')), 0.2);

function openPour(g) {
  if (active || g.phase !== 'tea-wait') return;
  const cup = CUPS.find((c) => c.id === g.request.cupId);
  g.pouring = true;
  // Patience stops while the pour is open; cancelling resumes it with exactly what was left.
  g.request.remaining = Math.max(0, g.request.deadline - now);
  const floor = CUP_FLOOR;
  active = {
    guest: g, cup, pour: createPour(cup, TEA), floor, tilt: 0, shownTilt: 0, held: false, finished: false,
    tip: { x: CUP_X + cup.shiftAt(cup.height), y: floor - cup.height - 72 },
    trace: [], t0: now, drops: [], spills: [], lastSpill: 0,
  };
  $('cup-layer').replaceChildren(); $('marks').replaceChildren(); $('pot').replaceChildren();
  $('drips').replaceChildren(); $('spill').replaceChildren(); $('steam').replaceChildren();
  const geo = drawCup(cup, $('cup-layer'), CUP_X, floor, 'live');
  active.geo = geo;
  $('interior-clip-path').setAttribute('d', geo.interior);
  drawMarks(cup, geo, floor);
  active.potNode = drawPot($('pot'));
  $('sheet-title').textContent = `Tea for guest ${g.seat.id}`;
  $('sheet-cup').textContent = `${cup.name} · ${cup.note}`;
  $('verdict').textContent = '';
  $('hint').textContent = 'One pour: drag the handle down the arc';
  $('cancel').hidden = false;
  $('scrim').hidden = false;
  const sheet = $('sheet');
  sheet.hidden = false;
  sheet.classList.remove('opening'); void sheet.offsetWidth; sheet.classList.add('opening');
  sheet.focus({ preventScroll: true });
  log(`Opened the pour for guest ${g.seat.id} (${cup.name}) · bubble dismissed, patience paused at ${g.request.remaining.toFixed(1)}s`);
  renderPour();
}

// Acceptance zone drawn on the cup itself: a green good band across walls and interior, a gold ideal
// band inside it, and the dashed fill line. Drawn over the tea, translucent, so it stays readable.
function drawMarks(cup, geo, floor) {
  const m = $('marks');
  const ty = floor - cup.targetHeight;
  const good = TEA.grade.goodBand * cup.height, ideal = TEA.grade.idealBand * cup.height;
  const body = el('g', { 'clip-path': 'url(#outer-live)' }, m);
  el('rect', { x: 0, y: ty - good, width: 390, height: good * 2, fill: '#7ed15a', opacity: 0.32 }, body);
  el('rect', { x: 0, y: ty - ideal, width: 390, height: ideal * 2, fill: '#ffc91c', opacity: 0.75 }, body);
  for (const y of [ty - good, ty + good]) el('line', { x1: 0, x2: 390, y1: y, y2: y, stroke: '#3f8a32', 'stroke-width': 2, opacity: 0.8 }, body);
  const inner = el('g', { 'clip-path': 'url(#interior-clip)' }, m);
  el('line', { x1: 0, x2: 390, y1: ty, y2: ty, stroke: OUTLINE, 'stroke-width': 2, 'stroke-dasharray': '6 5' }, inner);
}

function closePour() {
  if (!active) return;
  active.guest.pouring = false;
  active = null;
  $('sheet').hidden = true;
  $('scrim').hidden = true;
  stopPourSound();
}

function cancelPour() {
  if (!active || active.finished || active.pour.state.poured) return;
  const g = active.guest;
  closePour();
  g.request.deadline = now + g.request.remaining;
  if (g.request.remaining <= 0) expire(g);
  else log(`Cancelled · guest ${g.seat.id}'s tea bubble returns with ${g.request.remaining.toFixed(1)}s left`);
}

function serve() {
  if (!active || active.finished || !active.pour.state.poured) return;
  const { guest: g, cup, pour } = active;
  active.finished = true;
  active.held = false; active.tilt = 0;
  drag = null;
  setDragging(false);
  const grade = gradePour(cup, pour.state, TEA);
  const words = GRADE_TEXT[grade.id];
  const verdict = $('verdict');
  verdict.textContent = words.text;
  verdict.setAttribute('class', grade.id === 'under' || grade.id === 'full' ? 'verdict small' : 'verdict');
  verdict.setAttribute('x', CUP_X); verdict.setAttribute('y', active.floor - cup.height - 84);
  if (!reduced()) verdict.animate([{ transform: 'scale(.5)', opacity: 0 }, { transform: 'scale(1.08)', opacity: 1, offset: 0.6 }, { transform: 'scale(1)' }], { duration: 380, easing: 'ease-out' });
  verdict.style.transformOrigin = `${CUP_X}px ${active.floor - cup.height - 94}px`;
  $('hint').textContent = grade.qualifies ? (g.visit.teaGrade ? 'Already counted this visit' : 'Tip chance up') : 'Too little tea for the tip bonus';
  if (grade.id === 'ideal' || grade.id === 'good') steam(grade.id === 'ideal');
  sound(grade.id);
  const first = !g.visit.teaGrade;
  if (first) g.visit.teaGrade = grade;
  g.lastGrade = grade.id;
  const before = tipChance({ ...g.visit, teaGrade: null }, TEA), after = tipChance(g.visit, TEA);
  log(`Served guest ${g.seat.id}: <b>${words.log}</b> (level ${(grade.offset * 100).toFixed(1)}% of height from the line${pour.state.spilled ? ', spilled' : ''}) · tip chance ${(before * 100).toFixed(0)}% → ${(after * 100).toFixed(0)}%`);
  updateReadout(true);
  setTimeout(() => {
    closePour();
    g.request = null;
    g.phase = 'sipping'; g.t = 0;
  }, reduced() ? 900 : 1500);
}

function steam(strong) {
  const s = $('steam');
  const rimY = active.floor - active.cup.height;
  const x0 = CUP_X + active.cup.shiftAt(active.cup.height);
  const count = strong ? 4 : 3;
  for (let i = 0; i < count; i++) {
    const x = x0 + (i - (count - 1) / 2) * 14;
    const p = el('path', { d: `M${x} ${rimY - 6} q-7 -10 0 -20 t0 -20`, fill: 'none', stroke: '#fff', 'stroke-width': 5, 'stroke-linecap': 'round', opacity: 0.85 }, s);
    if (!reduced()) p.animate([{ transform: 'translateY(6px)', opacity: 0 }, { opacity: 0.9, offset: 0.3 }, { transform: 'translateY(-26px)', opacity: 0 }], { duration: 1300, delay: i * 120, iterations: 2 });
  }
  if (strong) {
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2;
      const star = el('text', { x: x0, y: rimY - 40, 'font-size': 18, 'text-anchor': 'middle' }, s);
      star.textContent = '✦';
      star.setAttribute('fill', '#ffc91c');
      if (!reduced()) star.animate([{ transform: 'translate(0,0) scale(.4)', opacity: 1 }, { transform: `translate(${Math.cos(a) * 70}px, ${Math.sin(a) * 50}px) scale(1)`, opacity: 0 }], { duration: 900, easing: 'ease-out', fill: 'forwards' });
    }
  }
}

// ---------------------------------------------------------------- arc control (relative drag)
let drag = null;
function local(event) {
  const r = svg.getBoundingClientRect();
  return { x: (event.clientX - r.left) * 390 / r.width, y: (event.clientY - r.top) * 330 / r.height };
}
function angleAt(p) {
  let a = Math.atan2(p.x - ARC.x, -(p.y - ARC.y)) * 180 / Math.PI;
  if (a < -120) a += 360;
  return a;
}
function setDragging(on) { $('sheet').classList.toggle('dragging', on); }
for (const target of [$('arc-hit'), $('knob')]) {
  target.addEventListener('pointerdown', (event) => {
    if (!active || active.finished || active.pour.state.poured) return;
    event.preventDefault();
    unlockAudio();
    svg.setPointerCapture(event.pointerId);
    drag = { id: event.pointerId, a0: angleAt(local(event)), t0: active.tilt };
    active.held = true;
    setDragging(true);
  });
}
svg.addEventListener('pointermove', (event) => {
  if (!drag || event.pointerId !== drag.id || !active) return;
  const a = angleAt(local(event));
  active.tilt = Math.max(0, Math.min(1, drag.t0 + (a - drag.a0) / ARC.sweep));
});
const release = (event) => {
  if (!drag || event.pointerId !== drag.id) return;
  drag = null;
  if (active) { active.held = false; active.tilt = 0; }
  setDragging(false);
};
svg.addEventListener('pointerup', release);
svg.addEventListener('pointercancel', release);
svg.addEventListener('lostpointercapture', release);
// Keyboard: hold Space / ArrowDown to pour; ArrowUp/Down adjust while held.
document.addEventListener('keydown', (event) => {
  if (!active) return;
  if (event.key === 'Escape') { event.preventDefault(); cancelPour(); return; }
  if (active.finished || (active.pour.state.poured && !active.held)) return;
  if (event.key === ' ' || event.key === 'ArrowDown') {
    event.preventDefault();
    active.held = true;
    active.tilt = Math.min(1, (active.tilt || 0.3) + (event.repeat ? 0.04 : 0));
  } else if (event.key === 'ArrowUp' && active.held) {
    active.tilt = Math.max(0, active.tilt - 0.08);
  }
});
document.addEventListener('keyup', (event) => {
  if (active && !drag && (event.key === ' ' || event.key === 'ArrowDown')) { active.held = false; active.tilt = 0; }
});
$('cancel').addEventListener('click', cancelPour);
// The scrim swallows taps so pouring never reaches the scene underneath.
for (const type of ['pointerdown', 'click']) $('scrim').addEventListener(type, (event) => { event.preventDefault(); event.stopPropagation(); });

// ---------------------------------------------------------------- pour frame
function stepPour(dt) {
  if (!active) return;
  const a = active;
  if (!a.finished) {
    a.pour.step(dt, a.tilt, a.held);
    // Easing back to upright while still holding also ends the pour: lock the control and let the pot return.
    if (a.pour.state.poured && a.pour.state.flow === 0 && a.held) { a.held = false; a.tilt = 0; drag = null; setDragging(false); }
    a.trace.push({ t: now - a.t0, level: a.pour.level() / a.cup.height, flow: a.pour.state.flow });
    if (a.trace.length > 1200) a.trace.shift();
    if (pourDone(a.pour.state)) serve();
  }
  // Pot follows the control, springing upright quickly on release.
  const k = a.held ? 1 : Math.min(1, dt / TEA.pour.returnSeconds * 3);
  a.shownTilt += (a.tilt - a.shownTilt) * (a.held ? Math.min(1, dt * 30) : k);
  // Drops: a short consistent trail after each stop.
  const s = a.pour.state;
  if (s.drip > 0 && Math.random() < dt * 14) a.drops.push({ x: a.tip.x + rand(-1, 1), y: a.tip.y + 2, vy: 30 });
  if (s.spilled > a.lastSpill + 1) {
    a.lastSpill = s.spilled;
    if (a.spills.length < 60 && Math.random() < 0.5) {
      const top = a.geo.top, rimY = a.floor - a.cup.height;
      const side = Math.random() < 0.5 ? -1 : 1;
      a.spills.push({ x: CUP_X + top.dx + side * (top.r + a.cup.wall), y: rimY, vx: side * rand(10, 40), vy: rand(-20, 10), side });
    }
  }
  const level = a.pour.level();
  const surfaceY = a.floor - level;
  for (const d of a.drops) { d.vy += 900 * dt; d.y += d.vy * dt; }
  a.drops = a.drops.filter((d) => d.y < surfaceY);
  for (const p of a.spills) { p.vy += 700 * dt; p.x += p.vx * dt; p.y += p.vy * dt; }
  a.spills = a.spills.filter((p) => p.y < a.geo.bottomY + 14);
  sound('flow', s.flow + (s.drip ? 0.08 : 0));
}

function renderPour() {
  if (!active) return;
  const a = active;
  const { state } = a.pour;
  const level = a.pour.level();
  const surfaceY = a.floor - level;
  $('liquid').setAttribute('y', surfaceY);
  $('liquid').setAttribute('height', Math.max(0, level + 4));
  $('surface').setAttribute('y', surfaceY - 1);
  $('surface').setAttribute('opacity', level > 0.5 ? 1 : 0);
  a.potNode.setAttribute('transform', `translate(${a.tip.x} ${a.tip.y}) rotate(${-a.shownTilt * TEA.pour.maxTiltDegrees}) scale(${POT_SCALE})`);
  // Stream from the spout tip straight down to the surface; width follows flow.
  const flow = state.flow;
  if (flow > 0) {
    const w = 2 + flow * 7, bottom = surfaceY + 2;
    const wobble = Math.sin(now * 40) * 0.4;
    $('stream-path').setAttribute('d', `M${a.tip.x - w / 2} ${a.tip.y} L${a.tip.x + w / 2} ${a.tip.y} L${a.tip.x + w * 0.4 + wobble} ${bottom} L${a.tip.x - w * 0.4 + wobble} ${bottom} Z`);
  } else $('stream-path').setAttribute('d', '');
  $('drips').replaceChildren(...a.drops.map((d) => el('ellipse', { cx: d.x, cy: d.y, rx: 2.4, ry: 3.4, fill: '#8dbb4d' })));
  const puddle = Math.min(60, state.spilled / a.cup.capacity * 300);
  const spill = [...a.spills.map((p) => el('circle', { cx: p.x, cy: p.y, r: 3.5, fill: '#8dbb4d' }))];
  if (puddle > 0) spill.unshift(el('ellipse', { cx: CUP_X + a.geo.s0.dx, cy: a.geo.bottomY + 12, rx: a.geo.maxOuter + puddle, ry: 4 + puddle / 10, fill: '#9fcb5c', opacity: 0.8 }));
  $('spill').replaceChildren(...spill);
  // Control.
  const deg = a.tilt * ARC.sweep;
  const knob = arcPoint(deg);
  $('knob').setAttribute('transform', `translate(${knob.x} ${knob.y})`);
  $('knob-pot').setAttribute('transform', `rotate(${-a.shownTilt * TEA.pour.maxTiltDegrees})`);
  $('arc-fill').setAttribute('d', a.tilt > 0.005 ? arcPath(deg) : '');
  $('arc-fill').setAttribute('stroke', a.tilt <= TEA.pour.deadZone ? '#d8c3a2' : '#8fbf5a');
  if (!a.finished) {
    $('cancel').hidden = state.poured;
    if (state.poured) $('hint').textContent = 'Ease back or let go to serve';
    else if (a.held) $('hint').textContent = 'Tilt further to pour';
  }
  updateReadout(false);
}

// ---------------------------------------------------------------- panel readout + trace
let lastTrace = null;
function updateReadout(final) {
  const a = active;
  if (a) lastTrace = { trace: a.trace, cup: a.cup };
  const rows = [];
  if (a) {
    const level = a.pour.level();
    const rise = a.pour.state.flow * a.pour.maxFlow * a.cup.riseRate(level);
    rows.push(['Cup', a.cup.name], ['Tilt', `${(a.tilt * 100).toFixed(0)}% (${(a.shownTilt * TEA.pour.maxTiltDegrees).toFixed(0)}°)`], ['Flow', `${(a.pour.state.flow * 100).toFixed(0)}%`],
      ['Level', `${level.toFixed(1)} / ${a.cup.height} px (line ${a.cup.targetHeight.toFixed(0)})`], ['Rise speed', `${rise.toFixed(0)} px/s here`],
      ['Volume', `${(a.pour.state.volume / a.cup.targetVolume * 100).toFixed(0)}% of target`]);
  }
  if (!final && frameCount % 6) return;
  $('readout').innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('');
  drawTrace();
}
function drawTrace() {
  const c = $('trace'), ctx = c.getContext('2d');
  ctx.clearRect(0, 0, c.width, c.height);
  if (!lastTrace || !lastTrace.trace.length) return;
  const { trace, cup } = lastTrace;
  const T = Math.max(5, trace[trace.length - 1].t);
  const X = (t) => 10 + (t / T) * (c.width - 20), Y = (v) => c.height - 10 - v * (c.height - 20);
  const target = cup.targetHeight / cup.height;
  ctx.fillStyle = '#a9d77b33';
  ctx.fillRect(10, Y(target + TEA.grade.goodBand), c.width - 20, Y(target - TEA.grade.goodBand) - Y(target + TEA.grade.goodBand));
  ctx.fillStyle = '#ffc91c55';
  ctx.fillRect(10, Y(target + TEA.grade.idealBand), c.width - 20, Y(target - TEA.grade.idealBand) - Y(target + TEA.grade.idealBand));
  ctx.strokeStyle = '#ffffff22'; ctx.beginPath(); ctx.moveTo(10, Y(1)); ctx.lineTo(c.width - 10, Y(1)); ctx.stroke();
  ctx.fillStyle = '#4e86b855';
  for (const p of trace) if (p.flow) ctx.fillRect(X(p.t), c.height - 10 - p.flow * 18, 1.5, p.flow * 18);
  ctx.strokeStyle = '#c5e47f'; ctx.lineWidth = 2.5; ctx.beginPath();
  trace.forEach((p, i) => (i ? ctx.lineTo(X(p.t), Y(p.level)) : ctx.moveTo(X(p.t), Y(p.level))));
  ctx.stroke();
  ctx.fillStyle = '#9cc3dd'; ctx.font = '11px Nunito, sans-serif';
  ctx.fillText(`${cup.name} · ${T.toFixed(1)}s`, 14, 16);
}

// ---------------------------------------------------------------- sound (WebAudio, unlocked on first touch)
let audio = null, noise = null;
function unlockAudio() {
  if (audio || !$('opt-sound').checked) return;
  try {
    audio = new AudioContext();
    const buffer = audio.createBuffer(1, audio.sampleRate, audio.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
    const src = audio.createBufferSource(); src.buffer = buffer; src.loop = true;
    const filter = audio.createBiquadFilter(); filter.type = 'bandpass'; filter.frequency.value = 900; filter.Q.value = 0.8;
    const gain = audio.createGain(); gain.gain.value = 0;
    src.connect(filter).connect(gain).connect(audio.destination); src.start();
    noise = { gain, filter, buffer };
  } catch { audio = null; }
}
function stopPourSound() { if (noise) noise.gain.gain.setTargetAtTime(0, audio.currentTime, 0.03); }
function tone(freq, at, length = 0.5, type = 'sine', volume = 0.18) {
  const o = audio.createOscillator(), g = audio.createGain();
  o.type = type; o.frequency.value = freq;
  g.gain.setValueAtTime(0, at); g.gain.linearRampToValueAtTime(volume, at + 0.01); g.gain.exponentialRampToValueAtTime(0.001, at + length);
  o.connect(g).connect(audio.destination); o.start(at); o.stop(at + length);
}
function sound(kind, amount = 0) {
  if (!audio || !$('opt-sound').checked) { if (noise && kind === 'flow') noise.gain.gain.value = 0; return; }
  const t = audio.currentTime;
  if (kind === 'flow') {
    noise.gain.gain.setTargetAtTime(Math.min(0.12, amount * 0.12), t, 0.04);
    noise.filter.frequency.setTargetAtTime(700 + (active ? active.pour.level() / active.cup.height : 0) * 1400, t, 0.1);
  } else if (kind === 'ideal') { [784, 988, 1175, 1568].forEach((f, i) => tone(f, t + i * 0.08, 0.7)); }
  else if (kind === 'good') { [784, 1175].forEach((f, i) => tone(f, t + i * 0.1, 0.6)); }
  else if (kind === 'under' || kind === 'full') tone(523, t, 0.4, 'triangle', 0.12);
  else if (kind === 'overflow') {
    const src = audio.createBufferSource(); src.buffer = noise.buffer;
    const g = audio.createGain(); g.gain.setValueAtTime(0.25, t); g.gain.exponentialRampToValueAtTime(0.001, t + 0.35);
    src.connect(g).connect(audio.destination); src.start(t); src.stop(t + 0.4);
    tone(330, t + 0.05, 0.3, 'triangle', 0.1);
  }
}
document.addEventListener('pointerdown', unlockAudio, { once: true });

// ---------------------------------------------------------------- panel controls
const reqBox = $('request-buttons');
for (const g of guests) {
  const b = el('button', {}, reqBox);
  b.textContent = `Guest ${g.seat.id} asks`;
  b.addEventListener('click', () => requestTea(guests.find((x) => x.seat === g.seat)));
}
$('happy-tea').addEventListener('click', () => {
  const g = guests.find((x) => x.teaAsked < TEA.request.perVisit && !x.wantsTea && ['eating', 'gap'].includes(x.phase) && !x.visit.ateRequestedDish);
  if (!g) { log('No guest free for this right now (try New visits)'); return; }
  g.phase = 'eating'; g.t = 0; g.meal = 1.2; g.mealRequested = true;
  requestTea(g);
});
$('two').addEventListener('click', () => {
  const ready = guests.filter((g) => g.teaAsked < TEA.request.perVisit && g.phase !== 'tea-wait' && !g.wantsTea);
  let made = 0;
  for (const g of ready) {
    if (made === 2) break;
    if (requestTea(g)) made++;
  }
  if (!made) log('No guest can ask right now (each visit allows one request; try New visits)');
});
$('new-visits').addEventListener('click', () => {
  for (const g of guests) { g.teaAsked = 0; g.visit = { teaGrade: null, bill: g.visit.bill, ateRequestedDish: false }; }
  log('New visits: every guest may ask for tea again');
});
const picks = $('cup-picks');
for (const opt of [{ id: 'cycle', name: 'Cycle all' }, ...CUPS]) {
  const b = el('button', { role: 'radio', 'aria-checked': String(opt.id === nextCup) }, picks);
  b.textContent = opt.name;
  b.addEventListener('click', () => {
    nextCup = opt.id;
    for (const x of picks.children) x.setAttribute('aria-checked', String(x === b));
  });
}
const TUNING = [
  ['Seconds to line at full tilt', TEA.pour, 'secondsToTargetAtMax', 1, 5, 0.1],
  ['Flow curve exponent', TEA.pour, 'flowCurve', 1, 3, 0.1],
  ['Dead zone (no flow)', TEA.pour, 'deadZone', 0, 0.35, 0.01],
  ['Drip share', TEA.pour, 'dripShare', 0, 0.08, 0.005],
  ['Patience (s)', TEA.request, 'patienceSeconds', 4, 25, 1],
  ['Ideal band (± height)', TEA.grade, 'idealBand', 0.01, 0.08, 0.005],
  ['Good band (± height)', TEA.grade, 'goodBand', 0.03, 0.18, 0.005],
];
for (const [name, obj, key, min, max, step] of TUNING) {
  const id = `tune-${key}`;
  const label = el('label', { for: id }, $('tune'));
  label.textContent = name;
  const wrap = el('div', { class: 'row', style: 'margin:0' }, $('tune'));
  const input = el('input', { type: 'range', id, min, max, step, value: obj[key] }, wrap);
  const out = el('output', {}, wrap);
  out.textContent = obj[key];
  input.addEventListener('input', () => { obj[key] = Number(input.value); out.textContent = input.value; });
}
$('opt-motion').addEventListener('change', () => document.body.classList.toggle('reduced', reduced()));
document.body.classList.toggle('reduced', reduced());
for (const layer of document.querySelectorAll('.row-layer')) layer.style.zIndex = Number(layer.dataset.depth) * 10;

// ---------------------------------------------------------------- tabs + cup sheet
for (const tab of document.querySelectorAll('[role=tab]')) {
  tab.addEventListener('click', () => {
    for (const t of document.querySelectorAll('[role=tab]')) t.setAttribute('aria-selected', String(t === tab));
    for (const v of document.querySelectorAll('.view')) v.hidden = v.id !== tab.dataset.view;
  });
}
CUPS.forEach((cup, i) => {
  const card = el('article', { class: 'cup-card' }, $('cup-grid'));
  card.innerHTML = `<h3>${cup.name}</h3><p>${cup.note}</p>`;
  const s = el('svg', { viewBox: '0 0 260 230' }, card);
  const floor = 205, cx = 96;
  drawCup(cup, el('g', {}, s), cx, floor, `sheet-${i}`);
  const ty = floor - cup.targetHeight;
  el('line', { x1: cx - 70, x2: cx + 70, y1: ty, y2: ty, stroke: OUTLINE, 'stroke-width': 2, 'stroke-dasharray': '6 5' }, s);
  // Relative rise speed (1 / area) by height for this cup.
  const ys = [];
  for (let y = 3; y < cup.height; y += 6) ys.push(y);
  const max = Math.max(...ys.map((y) => cup.riseRate(y)));
  for (const y of ys) el('rect', { x: 186, y: floor - y - 2.5, width: Math.max(2, cup.riseRate(y) / max * 66), height: 4, rx: 2, fill: '#6c9c3c' }, s);
  el('text', { x: 186, y: floor + 18, 'font-size': 11, fill: '#8a6a4c' }, s).textContent = 'rise speed →';
});

// ---------------------------------------------------------------- fit + loop
function fit() {
  const phone = $('phone');
  const narrow = innerWidth <= 440;
  const z = narrow ? Math.min(innerWidth / 390, innerHeight / 844) : Math.min(1, (innerHeight - 90) / 864);
  phone.style.zoom = Math.max(0.4, Math.min(1, z)).toFixed(3);
}
addEventListener('resize', fit);
fit();

let last = performance.now(), frameCount = 0;
function frame(t) {
  const dt = Math.min(0.05, (t - last) / 1000);
  last = t;
  frameCount++;
  tick(dt);
  stepPour(dt);
  renderBadges();
  renderPour();
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

// Test hook: lets the browser check drive the clock deterministically.
window.__tea = { guests, requestTea, openPour, beginWaiting, get active() { return active; }, get now() { return now; }, tick };
