/* Cash-note and tip-jar review for #61.
   Asset map:
   - Backdrop: real native capture of the live restaurant (seed 41, 45 s in), HUD coin hidden.
   - Row layers: the same frame re-rendered one depth bucket at a time (tools/capture_cash_layers.gd),
     so cash and the jar sort between rows like native sprites. Geometry in assets/restaurant-live.json.
   - Cash piles, HUD icon, sale pop: 2D SVG art in assets/ (catalog scale: 256 px per cell).
   - Tip jar: native Blender renders, assets/jar-*.png from tools/build_tip_jar.py (five fill states, one south view;
     frame 192x384 at 128 px per cell, root (96, 288)).
   - Outline: one runtime SVG filter (dilate + flood + soft glow), so its colour stays a single tunable value.
   - Touch: hit targets live in a layer above every sprite, so hidden cash stays tappable. */

const SCALE = 390 / 720;                 // native logical canvas 720 wide -> 390 px phone
const CELL = 113.6923 * SCALE;
const ORIGIN = { x: 56.8462 * SCALE, y: 136.8462 * SCALE };   // centre of cell (0, 0)
const COLUMNS = 6;                       // column 6 is half off-screen at this camera
const FIRST_ROW = 3, LAST_ROW = 13;      // rows 0-2 are the wall backdrop
const JAR_TILE = { x: 1, y: 11 };
const BLOCKED = new Set([
  '1,6', '2,6', '3,6', '4,6', '2,9', '3,9', '4,9', '5,9',   // belts
  '1,7', '2,10', '6,10',                                     // chefs
  '2,5', '4,5', '3,8', '5,8', '6,6',                         // seats
  '4,3', '5,3',                                              // doorway
  `${JAR_TILE.x},${JAR_TILE.y}`,
]);
const SEATS = [{ x: 2, y: 5 }, { x: 4, y: 5 }, { x: 3, y: 8 }, { x: 5, y: 8 }];
const OUTLINES = [
  { name: 'Cyan', color: '#19e3ff' },
  { name: 'Magenta', color: '#ff2bd6' },
  { name: 'Electric yellow', color: '#ffe500' },
  { name: 'Orange', color: '#ff7a00' },
  { name: 'White', color: '#ffffff' },
];
const ART = [new URL('./assets/cash-1.svg', import.meta.url).href, new URL('./assets/cash-2.svg', import.meta.url).href, new URL('./assets/cash-3.svg', import.meta.url).href];
const ICON = new URL('./assets/cash-icon.svg', import.meta.url).href, POP = new URL('./assets/cash-pop.svg', import.meta.url).href;
const JAR = {
  empty: new URL('./assets/jar-empty.png', import.meta.url).href,
  quarter: new URL('./assets/jar-quarter.png', import.meta.url).href,
  half: new URL('./assets/jar-half.png', import.meta.url).href,
  most: new URL('./assets/jar-most.png', import.meta.url).href,
  full: new URL('./assets/jar-full.png', import.meta.url).href,
};
const JAR_STATES = [['Empty', 0], ['Quarter', 0.25], ['Half', 0.5], ['Most', 0.78], ['Full', 1]];
const TOSS_S = 0.5, FLIGHT_S = 0.55, JAR_FLIGHT_S = 0.7;
const WALLET_ICON = { x: 38.2, y: 83.2 };   // centre of the HUD cash icon inside the phone

const $ = (id) => document.getElementById(id);
const phone = $('phone'), world = $('world'), hits = $('hits'), fx = $('fx'), wallet = $('wallet');
const piles = new Map();                 // "x,y" -> { x, y, amount, el, hit }
const jar = { balance: 34, capacity: 100 };

const center = (x, y) => ({ x: ORIGIN.x + x * CELL, y: ORIGIN.y + y * CELL });
const key = (x, y) => `${x},${y}`;
const reduced = () => $('opt-motion').checked;
const tierOf = (amount) => (amount > +$('t3').value ? 2 : amount > +$('t2').value ? 1 : 0);
// A depth bucket k holds sprites whose ground depth is in (k-1, k]; cash at row r sorts after bucket r.
const zFor = (row) => row * 10 + 5;

// ---------------------------------------------------------------- rolling counter
function odometer(el, initial) {
  let current = String(initial);
  const digit = (d) => {
    const cell = document.createElement('span');
    cell.className = 'd';
    const glyph = document.createElement('span');
    glyph.textContent = d;
    cell.append(glyph);
    return cell;
  };
  el.replaceChildren(...[...current].map(digit));
  return (value) => {
    const next = String(value);
    if (next === current) return;
    const up = value > Number(current);
    while (el.children.length < next.length) el.prepend(digit(' '));
    while (el.children.length > next.length) el.firstElementChild.remove();
    const padded = current.padStart(next.length, ' ');
    [...next].forEach((d, i) => {
      const cell = el.children[i];
      while (cell.children.length > 1) cell.firstElementChild.remove();
      if (padded[i] === d) return;
      const old = cell.firstElementChild;
      const fresh = document.createElement('span');
      fresh.textContent = d;
      cell.append(fresh);
      if (reduced()) { old.remove(); return; }
      // Earning rolls digits up, spending rolls them down; lower digits move first.
      const dir = up ? 1 : -1, delay = (next.length - 1 - i) * 35;
      const timing = { duration: 340, delay, easing: 'cubic-bezier(.2,.9,.25,1)', fill: 'both' };
      old.animate([{ transform: 'translateY(0)' }, { transform: `translateY(${-dir * 100}%)` }], timing).onfinish = () => old.remove();
      fresh.animate([{ transform: `translateY(${dir * 100}%)` }, { transform: 'translateY(0)' }], timing);
    });
    current = next;
    if (!reduced()) {
      el.animate([{ transform: 'scale(1)' }, { transform: `scale(${up ? 1.24 : 1.14})`, color: up ? '#238a4b' : '#c8452e', offset: 0.3 }, { transform: 'scale(1)' }], { duration: 420, easing: 'ease-out' });
    }
  };
}
const showWallet = odometer($('wallet-value'), 9180);
let shown = 9180;
function credit(amount) {
  shown += amount;
  showWallet(shown);
  wallet.setAttribute('aria-label', `${shown} cash`);
}

// ---------------------------------------------------------------- floor piles
function pileElement(amount, delay = Math.random() * -1.7) {
  const el = document.createElement('div');
  el.className = 'pile';
  el.style.animationDelay = `${delay}s`;
  el.innerHTML = `<div class="shadow"></div><div class="bob"><img alt=""></div>`;
  el.querySelector('img').src = ART[tierOf(amount)];
  return el;
}

function place(x, y, amount) {
  const el = pileElement(amount);
  const at = center(x, y);
  el.style.left = `${at.x}px`;
  el.style.top = `${at.y}px`;
  el.style.zIndex = zFor(y);
  world.append(el);
  const hit = document.createElement('button');
  hit.className = 'hit';
  hit.style.left = `${at.x}px`;
  hit.style.top = `${at.y - CELL * 0.15}px`;
  hit.setAttribute('aria-label', `Collect $${amount} tip`);
  hit.addEventListener('pointerdown', (event) => { event.preventDefault(); collectAround(x, y); });
  hit.addEventListener('click', (event) => { if (event.detail === 0) collectAround(x, y); });
  hits.append(hit);
  const pile = { x, y, amount, el, hit };
  piles.set(key(x, y), pile);
  return pile;
}

function refreshArt() {
  for (const pile of piles.values()) pile.el.querySelector('img').src = ART[tierOf(pile.amount)];
  renderTiers();
}

// ---------------------------------------------------------------- tipping
function freeNeighbours(seat) {
  const out = [];
  for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
    const x = seat.x + dx, y = seat.y + dy;
    if (!dx && !dy) continue;
    if (x < 0 || x >= COLUMNS || y < FIRST_ROW || y > LAST_ROW) continue;
    if (BLOCKED.has(key(x, y)) || piles.has(key(x, y))) continue;
    out.push({ x, y });
  }
  return out;
}

function tip(amount) {
  const seats = SEATS.filter((seat) => freeNeighbours(seat).length);
  if (!seats.length) { tipToJar(amount); return; }
  const seat = seats[Math.floor(Math.random() * seats.length)];
  const options = freeNeighbours(seat);
  const target = options[Math.floor(Math.random() * options.length)];
  const pile = place(target.x, target.y, amount);
  if (reduced()) return;
  // Tossed from the guest's hands in an arc, then a small landing bounce before it starts to float.
  const from = center(seat.x, seat.y - 0.45), to = center(target.x, target.y);
  const dx = from.x - to.x, dy = from.y - to.y;
  const frames = [];
  for (let i = 0; i <= 12; i++) {
    const t = i / 12;
    const arc = -4 * CELL * 0.7 * t * (1 - t);
    frames.push({ transform: `translate(${dx * (1 - t)}px, ${dy * (1 - t) + arc}px) rotate(${(1 - t) * -200}deg)`, offset: t * 0.72 });
  }
  frames.push({ transform: 'translate(0, 0) scale(1.18, 0.8)', offset: 0.82 });
  frames.push({ transform: 'translate(0, -6px) scale(0.95, 1.06)', offset: 0.92 });
  frames.push({ transform: 'none', offset: 1 });
  pile.el.classList.add('landing');
  // In flight the cash is above the scene; it joins its row once it lands.
  pile.el.style.zIndex = 500;
  const bob = pile.el.querySelector('.bob');
  const duration = TOSS_S * 1000 / 0.72;
  const motion = bob.animate(frames.map((f) => ({ ...f, transform: `translateY(-50%) ${f.transform}` })), { duration, easing: 'linear' });
  pile.el.querySelector('.shadow').animate([{ opacity: 0, transform: 'scale(.4)' }, { opacity: 0, offset: 0.5 }, { opacity: 1, transform: 'scale(1)' }], { duration });
  setTimeout(() => { pile.el.style.zIndex = zFor(target.y); }, duration * 0.72);
  motion.onfinish = () => { pile.el.style.animationDelay = '0s'; pile.el.classList.remove('landing'); };
}

// ---------------------------------------------------------------- collecting
function collectAround(x, y) {
  const taken = [...piles.values()].filter((p) => Math.abs(p.x - x) <= 1 && Math.abs(p.y - y) <= 1);
  if (!taken.length) return;
  let total = 0;
  for (const pile of taken) {
    piles.delete(key(pile.x, pile.y));
    total += pile.amount;
    pile.hit.remove();
    pile.el.classList.add('gone');
    setTimeout(() => pile.el.remove(), 200);
    flyToWallet(center(pile.x, pile.y), pile.amount, [1, 3, 5][tierOf(pile.amount)]);
  }
  const at = center(x, y);
  floatText(`+$${total}`, at.x, at.y - CELL * 0.55);
}

function flyToWallet(from, amount, notes) {
  if (reduced()) { credit(amount); return; }
  const to = WALLET_ICON;
  for (let i = 0; i < notes; i++) {
    const el = document.createElement('div');
    el.className = 'flyer';
    el.innerHTML = `<img src="${ICON}" alt="">`;
    fx.append(el);
    const start = { x: from.x + (Math.random() - 0.5) * CELL * 0.4, y: from.y + (Math.random() - 0.5) * CELL * 0.3 };
    const control = { x: (start.x + to.x) / 2 + CELL * 0.8, y: Math.min(start.y, to.y) - CELL * 0.2 };
    const frames = [];
    for (let s = 0; s <= 10; s++) {
      const t = s / 10, u = 1 - t;
      const px = u * u * start.x + 2 * u * t * control.x + t * t * to.x;
      const py = u * u * start.y + 2 * u * t * control.y + t * t * to.y;
      frames.push({ transform: `translate(${px}px, ${py}px) scale(${1.1 - 0.4 * t}) rotate(${t * 220}deg)`, opacity: t > 0.92 ? 0 : 1 });
    }
    const share = Math.round(amount / notes * (i + 1)) - Math.round(amount / notes * i);
    const run = el.animate(frames, { duration: FLIGHT_S * 1000, delay: i * 70, easing: 'cubic-bezier(.45,0,.75,1)', fill: 'backwards' });
    run.onfinish = () => { el.remove(); credit(share); bump(); };
  }
}

function bump() { wallet.classList.remove('bump'); void wallet.offsetWidth; wallet.classList.add('bump'); }

function floatText(text, x, y, muted = false) {
  const el = document.createElement('div');
  el.className = muted ? 'gain muted' : 'gain';
  el.textContent = text;
  el.style.left = `${x}px`; el.style.top = `${y}px`;
  fx.append(el);
  el.animate([{ transform: 'translate(-50%, -50%) scale(.7)', opacity: 0 }, { transform: 'translate(-50%, -80%) scale(1.05)', opacity: 1, offset: 0.25 }, { transform: 'translate(-50%, -160%)', opacity: 0 }], { duration: 900, easing: 'ease-out' }).onfinish = () => el.remove();
}

// ---------------------------------------------------------------- tip jar
function jarState(fraction) {
  if (fraction <= 0) return 'empty';
  if (fraction >= 1) return 'full';
  if (fraction < 0.375) return 'quarter';
  if (fraction < 0.64) return 'half';
  return 'most';
}

function jarElement() {
  const el = document.createElement('div');
  el.className = 'jar';
  el.innerHTML = `<img class="jar-art" alt=""><div class="jar-label"></div>`;
  return el;
}

function paintJar(el, balanceValue, capacity) {
  el.querySelector('.jar-art').src = JAR[jarState(balanceValue / capacity)];
  el.classList.toggle('has-cash', balanceValue > 0);
  el.classList.toggle('is-full', balanceValue >= capacity);
  el.querySelector('.jar-label').textContent = balanceValue >= capacity ? `FULL · $${capacity}` : `$${balanceValue} / $${capacity}`;
}

const jarEl = jarElement();
const jarHit = document.createElement('button');
{
  const at = center(JAR_TILE.x, JAR_TILE.y);
  Object.assign(jarEl.style, { left: `${at.x - CELL * 0.75}px`, top: `${at.y - CELL * 2.25}px`, width: `${CELL * 1.5}px`, zIndex: zFor(JAR_TILE.y) });
  world.append(jarEl);
  jarHit.className = 'hit jar-hit';
  Object.assign(jarHit.style, { left: `${at.x}px`, top: `${at.y - CELL * 0.6}px`, width: `${CELL}px`, height: `${CELL * 1.8}px` });
  jarHit.addEventListener('click', collectJar);
  hits.append(jarHit);
}
function updateJar() {
  paintJar(jarEl, jar.balance, jar.capacity);
  jarHit.setAttribute('aria-label', jar.balance ? `Collect $${jar.balance} from tip jar` : 'Tip jar, empty');
}

function jarBounce() {
  if (!reduced()) jarEl.querySelector('.jar-art').animate([{ transform: 'scale(1)' }, { transform: 'scale(1.06, .94)', offset: 0.3 }, { transform: 'scale(.98, 1.03)', offset: 0.65 }, { transform: 'scale(1)' }], { duration: 320, easing: 'ease-out' });
}

function collectJar() {
  if (!jar.balance) return;
  const amount = jar.balance;
  jar.balance = 0;
  updateJar();
  jarBounce();
  const at = center(JAR_TILE.x, JAR_TILE.y - 0.8);
  flyToWallet(at, amount, Math.min(6, 2 + Math.floor(amount / 40)));
  floatText(`+$${amount}`, at.x + CELL * 0.3, at.y - CELL * 0.3);
}

function tipToJar(amount) {
  const seat = SEATS[Math.floor(Math.random() * SEATS.length)];
  const accepted = Math.min(amount, jar.capacity - jar.balance);
  const from = center(seat.x, seat.y - 0.6);
  if (accepted <= 0) {
    // Full jar: no flight, only a muted tip icon fading above the guest.
    floatText(`$${amount} tip lost`, from.x, from.y - CELL * 0.3, true);
    return;
  }
  const land = () => {
    jar.balance += accepted;
    updateJar();
    jarBounce();
    const top = center(JAR_TILE.x, JAR_TILE.y - 1.2);
    floatText(`+$${accepted}`, top.x + CELL * 0.2, top.y);
  };
  if (reduced()) { land(); return; }
  const to = center(JAR_TILE.x, JAR_TILE.y - 1.05);
  const el = document.createElement('div');
  el.className = 'flyer big';
  el.innerHTML = `<img src="${ART[tierOf(accepted)]}" alt="">`;
  fx.append(el);
  const frames = [];
  for (let s = 0; s <= 14; s++) {
    const t = s / 14;
    const px = from.x + (to.x - from.x) * t, py = from.y + (to.y - from.y) * t - 4 * CELL * 1.1 * t * (1 - t);
    frames.push({ transform: `translate(${px}px, ${py}px) rotate(${t * 300}deg) scale(${1 - 0.35 * t})` });
  }
  el.animate(frames, { duration: JAR_FLIGHT_S * 1000, easing: 'linear' }).onfinish = () => { el.remove(); land(); };
}

// ---------------------------------------------------------------- automatic sales (existing coin-pop replacement)
function salePop() {
  if (!$('opt-sales').checked || document.hidden) return;
  const seat = SEATS[Math.floor(Math.random() * SEATS.length)];
  const price = [10, 14, 32, 48][Math.floor(Math.random() * 4)];
  const at = center(seat.x, seat.y);
  credit(price);
  if (reduced()) return;
  const el = document.createElement('img');
  el.className = 'sale-pop';
  el.src = POP;
  el.alt = '';
  el.style.left = `${at.x}px`; el.style.top = `${at.y - CELL * 1.3}px`;
  fx.append(el);
  el.animate([{ transform: 'translateY(10px) scale(.3)', opacity: 0 }, { transform: 'translateY(0) scale(1.1)', opacity: 1, offset: 0.25 }, { transform: 'translateY(-26px) scale(1)', opacity: 0 }], { duration: 900, easing: 'ease-out' }).onfinish = () => el.remove();
}

// ---------------------------------------------------------------- outline controls
function setOutline(color) {
  document.querySelector('#outline feFlood').setAttribute('flood-color', color);
  for (const b of $('swatches').children) b.setAttribute('aria-checked', String(b.dataset.color === color));
}
function setWidth(value) {
  document.querySelector('#outline feMorphology').setAttribute('radius', value);
  $('width-out').textContent = `${value} px`;
}
function setGlow(on) { document.querySelector('#outline feFuncA').setAttribute('slope', on ? '0.9' : '0'); }

for (const o of OUTLINES) {
  const b = document.createElement('button');
  b.setAttribute('role', 'radio');
  b.dataset.color = o.color;
  b.title = o.name;
  b.setAttribute('aria-label', o.name);
  b.style.background = o.color;
  b.onclick = () => setOutline(o.color);
  $('swatches').append(b);
}

// ---------------------------------------------------------------- tiers and jar views
function renderTiers() {
  const t2 = +$('t2').value, t3 = +$('t3').value;
  const rows = [
    { name: 'One note', range: `$1–${t2}`, amount: Math.max(1, t2) },
    { name: 'Three notes', range: `$${t2 + 1}–${t3}`, amount: t3 },
    { name: 'A bundle', range: `Over $${t3}`, amount: t3 + 1 },
  ];
  $('tier-grid').replaceChildren(...rows.map((row) => {
    const card = document.createElement('div');
    card.className = 'tier';
    card.innerHTML = `<h3>${row.name}</h3><p>${row.range}</p><div class="cells"><div class="floor small"></div><div class="floor big"></div></div>`;
    for (const floor of card.querySelectorAll('.floor')) floor.append(pileElement(row.amount));
    return card;
  }));
}

function renderJarStates() {
  $('jar-grid').replaceChildren(...JAR_STATES.map(([name, fraction]) => {
    const card = document.createElement('div');
    card.className = 'tier jar-card';
    card.innerHTML = `<h3>${name}</h3><div class="jar-floor"></div>`;
    const el = jarElement();
    paintJar(el, Math.round(fraction * 100), 100);
    card.querySelector('.jar-floor').append(el);
    return card;
  }));
}

for (const [name, fraction] of JAR_STATES) {
  const b = document.createElement('button');
  b.textContent = name;
  b.onclick = () => { jar.balance = Math.round(fraction * jar.capacity); updateJar(); };
  $('jar-presets').append(b);
}

// ---------------------------------------------------------------- wiring
function reset() {
  for (const pile of piles.values()) { pile.el.remove(); pile.hit.remove(); }
  piles.clear();
  place(5, 5, 6);
  place(1, 8, 24);
  place(4, 7, 80);
  place(3, 7, 15);
  place(0, 4, 3);
  jar.balance = 34;
  updateJar();
}

for (const b of document.querySelectorAll('[data-tip]')) b.onclick = () => tip(+b.dataset.tip);
$('tip-random').onclick = () => tip(Math.max(1, Math.round(Math.random() ** 2 * 90)));
$('tip-jar').onclick = () => tipToJar(15);
$('jar-capacity').onchange = (e) => { jar.capacity = +e.target.value; jar.balance = Math.min(jar.balance, jar.capacity); updateJar(); };
$('spend').onclick = () => credit(-120);
$('reset').onclick = reset;
$('opt-motion').onchange = () => document.body.classList.toggle('reduced', reduced());
$('opt-width').oninput = (e) => setWidth(e.target.value);
$('opt-glow').onchange = (e) => setGlow(e.target.checked);
$('t2').onchange = refreshArt;
$('t3').onchange = refreshArt;
for (const tab of document.querySelectorAll('[role=tab]')) tab.onclick = () => {
  for (const t of document.querySelectorAll('[role=tab]')) t.setAttribute('aria-selected', String(t === tab));
  for (const v of document.querySelectorAll('.view')) v.hidden = v.id !== tab.dataset.view;
};
for (const layer of document.querySelectorAll('.row-layer')) layer.style.zIndex = Number(layer.dataset.depth) * 10;

let demo = 9180;
const showDemo = odometer($('demo-value'), demo);
$('demo-up').onclick = () => showDemo(demo += 37);
$('demo-down').onclick = () => showDemo(demo -= 120);

const fit = () => { phone.style.zoom = String(Math.min(1, (document.documentElement.clientWidth - 52) / 390)); };
addEventListener('resize', fit);
fit();
setOutline(OUTLINES[0].color);
reset();
renderTiers();
renderJarStates();
setInterval(salePop, 3200);
