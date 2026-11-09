import '../../wireframe/recipe-maple.css';
import './style.css';
import {tracks, groups, tierColors, expedition, live} from './balance.js';
import {powerupIcon, shieldEmblem, shieldBubble, swirl, signalGlow, softFilter} from './powerups.js';
import {storageKey, fixture, restore, command, statAt, maxLevel, nextCost, tierOf, canUpgrade, runProfile} from './model.js';
import layout from './assets/ship-layout.json';
import {sceneTransition} from './transition.js';
import {harpoonIcon, fireHarpoon} from './harpoon.js';

const asset = n => new URL(`./assets/${n}`, import.meta.url).href;
const byId = Object.fromEntries(tracks.map(t => [t.id, t]));
const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
const $ = (s, root = document) => root.querySelector(s);
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const [CW, CH] = layout.capture_size;
const DIVE_CELL = CW / 7; // expedition Route.VIEW_COLUMNS

let review = new URLSearchParams(location.search).get('state') || 'restaurant';
// Restaurant, Workshop and Dive share one saved progression; the other states are fixtures.
const playable = name => ['restaurant', 'workshop', 'dive'].includes(name);
const continues = (from, to) => from === to || (playable(from) && playable(to));
let model = restore(safeStorage(), review);
model = continues(model.review, review) ? {...model, review} : {...fixture(review), review};
let cash = live.cash, opener = null, saleTimer = null, diveFrame = null, serial = 0, rollSerial = 0;

function safeStorage() { try { return localStorage; } catch { return {getItem: () => null, setItem() {}}; } }
function save() { try { localStorage.setItem(storageKey, JSON.stringify(model)); } catch {} }
function commit(action) { const next = command(model, action); if (next !== model) { model = next; save(); } return next; }

/* ---------- shared pieces (gameplay and Shared components use the same markup) ---------- */

const icon = {
  edit: '<path d="m4 16 11-11 4 4L8 20l-5 1 1-5"/>',
  wrench: '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.1L4 16.7 7.3 20l5.3-5.3a4 4 0 0 0 5.1-5.4l-2.6 2.6-2.4-.6-.6-2.4Z"/>',
};
const svg = (name, cls = 'ui-icon') => `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${icon[name]}</svg>`;
const salvage = amount => `<span class="salvage"><img src="${asset('salvage.png')}" alt=""><span>${amount.toLocaleString()}</span></span>`;

// The ship is two ImageGen parts (hull, paired collectors), always fitted and swapped whole at each
// look tier. The Harpoon track changes the fired harpoon instead (harpoon.js), so the hull stays friendly.
// Layers sit in one shared frame (hull-sheet px, origin at the hull centre) whose bounds cover every
// tier mix, so the ship box never changes size and the hull centre (collision centre) stays put.
const parts = {hull: layout.hull, collector: layout.collector}, K = layout.compose;
function shipLayout(levels) {
  const hull = parts.hull[tierOf('hull', levels.hull) - 1], col = parts.collector[tierOf('collector', levels.collector) - 1];
  const hx = -hull.size[0] / 2, hy = -hull.size[1] / 2, cs = K.collector_scale, ov = K.collector_overlap;
  const ly = hull.left[1] + hy - col.bracket[1] * cs;
  return [
    {part: 'collector', file: col.file, x: hull.left[0] + hx + ov - col.bracket[0] * cs, y: ly, w: col.size[0] * cs, h: col.size[1] * cs},
    {part: 'collector', file: col.file, x: hull.right[0] + hx - ov + (col.bracket[0] - col.size[0]) * cs, y: ly, w: col.size[0] * cs, h: col.size[1] * cs, flip: true},
    {part: 'hull', file: hull.file, x: hx, y: hy, w: hull.size[0], h: hull.size[1]},
  ];
}
const FRAME = (() => {
  let x0 = 0, y0 = 0, x1 = 0, y1 = 0;
  for (const h of [1, 3, 5]) for (const c of [1, 3, 4]) for (const l of shipLayout({hull: h, collector: c})) { x0 = Math.min(x0, l.x); y0 = Math.min(y0, l.y); x1 = Math.max(x1, l.x + l.w); y1 = Math.max(y1, l.y + l.h); }
  const half = Math.max(-x0, x1);
  return {x0: -half, y0, w: half * 2, h: y1 - y0, hullH: layout.hull[0].size[1]};
})();
function shipLayers(levels) {
  const pct = (v, total) => `${v / total * 100}%`;
  const imgs = shipLayout(levels).map(l => `<img class="ship-part ${l.flip ? 'flip' : ''}" data-part="${l.part}" src="${asset(l.file)}" alt="" style="left:${pct(l.x - FRAME.x0, FRAME.w)};top:${pct(l.y - FRAME.y0, FRAME.h)};width:${pct(l.w, FRAME.w)};height:${pct(l.h, FRAME.h)}">`).join('');
  return `<span class="ship" style="--w:${FRAME.w};--h:${FRAME.h}">${imgs}</span>`;
}
// Place the ship box so the hull centre lands at (cx, cy) with the given hull height (capture px).
function shipPlacement(place) {
  const s = place.hull_height / FRAME.hullH;
  return `left:${(place.cx + FRAME.x0 * s) / CW * 100}%;top:${(place.cy + FRAME.y0 * s) / CH * 100}%;width:${FRAME.w * s / CW * 100}%`;
}
function shipLabel(levels) {
  return `Yellow submarine: ${tracks.filter(t => t.group === 'equipment' && t.id !== 'harpoon').map(t => t.tiers[tierOf(t.id, levels[t.id]) - 1].toLowerCase()).join(', ')}`;
}
// The harpoon leaves from the hull's nose hatch: its position in the ship box (0–1 of width/height).
function noseInBox(levels) {
  const hull = parts.hull[tierOf('hull', levels.hull) - 1];
  return {x: (hull.nose[0] - hull.size[0] / 2 - FRAME.x0) / FRAME.w, y: (hull.nose[1] - hull.size[1] / 2 - FRAME.y0) / FRAME.h};
}
const partArt = (id, tier) => byId[id].group === 'powerup' ? powerupIcon(id, tier) : id === 'harpoon' ? harpoonIcon(tier) : `<img src="${asset(`ship-${id}-${tier}.png`)}" alt="">`;

function pips(t, level) {
  const dots = Array.from({length: t.levels.length}, (_, i) => `<i class="${i < level ? 'on' : ''} ${t.looks.includes(i + 1) ? 'look' : ''}"></i>`).join('');
  return `<span class="pips" role="img" aria-label="Level ${level} of ${t.levels.length}; new look at levels ${t.looks.join(' and ')}">${dots}</span>`;
}

// Power-ups say what they do and which way the next level moves it; their numbers stay internal.
function powerupCopy(t, level, max) {
  const trend = max ? '' : statAt(t.id, level) === 0 ? t.unlock : t.better;
  return `<p class="pu-does">${t.does}</p>${trend ? `<p class="pu-trend"><svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2 8 6 3.5 10 8" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>${trend}</p>` : '<p class="pu-trend done">Fully upgraded</p>'}`;
}
function upgradeCard(t, m, {pressed = false} = {}) {
  const level = m.levels[t.id], max = level >= maxLevel(t.id), cost = nextCost(m, t.id), fresh = m.seen?.[t.id] === false;
  const current = t.format(statAt(t.id, level)), next = max ? '' : t.format(statAt(t.id, level + 1));
  const action = max
    ? `<div class="max-stamp" role="img" aria-label="Maximum level">MAX</div>`
    : `<button type="button" class="cost-action up-action ${pressed ? 'sample-pressed' : ''}" data-upgrade="${t.id}" ${canUpgrade(m, t.id) ? '' : 'disabled'} aria-label="Upgrade ${t.name} to level ${level + 1} for ${cost} salvage${canUpgrade(m, t.id) ? '' : ', not enough salvage'}"><small>Upgrade</small>${salvage(cost)}</button>`;
  return `<article class="up-row ${max ? 'is-max' : ''}" data-track="${t.id}" aria-label="${t.name}">
    <div class="up-art">${partArt(t.id, tierOf(t.id, level))}${fresh ? '<span class="new-tag">NEW</span>' : ''}</div>
    <div class="up-copy">
      <h2>${t.name}<span class="lv">Lv ${level}</span></h2>
      ${t.group === 'powerup' ? powerupCopy(t, level, max) : `<p class="stat-label">${t.stat}</p>
      <p class="stat"><b class="cur">${current}</b>${max ? '' : `<i aria-label="to">→</i><b class="next">${next}</b>`}</p>`}
      ${pips(t, level)}
    </div>
    ${action}
  </article>`;
}

// The Workshop is its own room: ImageGen room art anchored to the top, the cradle and ship laid
// out in whatever floor is free between the wall and the card tray (see layoutRoom).
const ROOM = {w: 853, h: 1844, wallBottom: 540, door: [45, 290, 210, 530], sign: [283, 323, 547, 420]};
const roomBox = ([x0, y0, x1, y1]) => `left:${x0 / ROOM.w * 100}%;top:${y0 / ROOM.h * 100}%;width:${(x1 - x0) / ROOM.w * 100}%;height:${(y1 - y0) / ROOM.h * 100}%`;
function workshopRoom(m) {
  return `<section class="ws-room" role="dialog" aria-modal="true" aria-labelledby="ws-title">
    <img class="room-fill" src="${asset('workshop-room.webp')}" alt="" aria-hidden="true">
    <div class="room-art" data-room>
      <img src="${asset('workshop-room.webp')}" alt="">
      <h1 id="ws-title" class="room-sign" style="${roomBox(ROOM.sign)}"><span>Workshop</span></h1>
      <button type="button" class="doorway" data-close style="${roomBox(ROOM.door)}" aria-label="Back to the Sushi Bar"><span class="door-tag"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5 8 12l7 7" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>Sushi Bar</span></button>
    </div>
    <svg class="fire-layer" data-fire aria-hidden="true"></svg>
    <button type="button" class="ws-hero" data-hero data-test-fire aria-label="Test-fire the ${esc(byId.harpoon.tiers[tierOf('harpoon', m.levels.harpoon) - 1].toLowerCase())}"><img class="cradle" src="${asset('workshop-cradle.png')}" alt=""><div class="hero-ship" data-slip>${shipLayers(m.levels)}</div></button>
    <span class="sr-only" data-ship-label>${esc(shipLabel(m.levels))}</span>
    <div class="room-hud"><div class="pill salvage-pill" aria-label="${m.salvage} salvage" data-balance>${salvage(m.salvage)}</div></div>
    <section class="ws-tray wr-panel" aria-label="Upgrades">${trayTabs(m)}<div class="ws-list wr-catalog" id="ws-panel" role="tabpanel" aria-labelledby="tab-${activeGroup}" tabindex="0">${trackCards(m)}</div></section>
  </section>`;
}

// Equipment | Power-ups tabs keep three cards per tab, so the tray (and the ship's floor) keeps its height.
let activeGroup = 'equipment';
const trackCards = m => tracks.filter(t => t.group === activeGroup).map(t => upgradeCard(t, m)).join('');
// The game's one tab control (r7): maple segments, the selected one cream. Shared by the Workshop tray
// and the Edit inventory dock. items: [{id, label, icon?, dot?}]; `attr` names the data attribute.
function tabBar(items, active, {attr, controls, label}) {
  return `<div class="ws-tabs" role="tablist" aria-label="${label}">${items.map(it => {
    const on = it.id === active;
    return `<button type="button" role="tab" id="tab-${it.id}" data-${attr}="${it.id}" aria-selected="${on}" aria-controls="${controls}" tabindex="${on ? 0 : -1}">${it.icon || ''}<span>${it.label}</span>${it.dot ? '<i class="tab-dot" aria-label="upgrade available"></i>' : ''}</button>`;
  }).join('')}</div>`;
}
function trayTabs(m) {
  return tabBar(groups.map(g => ({id: g.id, label: g.name, dot: g.id !== activeGroup && tracks.some(t => t.group === g.id && canUpgrade(m, t.id))})), activeGroup, {attr: 'group', controls: 'ws-panel', label: 'Upgrades'});
}
function refreshTray(host) {
  $('.ws-tabs', host).outerHTML = trayTabs(model);
  const list = $('.ws-list', host);
  list.innerHTML = trackCards(model); list.setAttribute('aria-labelledby', `tab-${activeGroup}`);
}
function layoutRoom(host) {
  const room = $('.ws-room', host);
  if (!room) return;
  const W = room.clientWidth, H = room.clientHeight, aspect = ROOM.w / ROOM.h;
  // Cover the screen, anchored to the top; on wide screens cap the room and let the blurred fill show.
  const roomW = W > H * 0.62 ? H * 0.62 : Math.max(W, H * aspect), roomH = roomW / aspect;
  const art = $('[data-room]', room);
  Object.assign(art.style, {width: `${roomW}px`, left: `${(W - roomW) / 2}px`});
  art.style.setProperty('--room-w', `${roomW}px`);
  const wall = ROOM.wallBottom / ROOM.h * roomH;
  const tray = $('.ws-tray', room);
  tray.style.maxHeight = `${Math.max(150, H - wall - 120)}px`;
  const freeTop = wall + 6, freeBottom = H - tray.offsetHeight - 6, freeH = freeBottom - freeTop;
  const cradleH = Math.max(80, Math.min(freeH * 0.9, roomW * 0.5 / 0.681)), cradleW = cradleH * 0.681;
  const hero = $('[data-hero]', room);
  Object.assign(hero.style, {width: `${cradleW}px`, height: `${cradleH}px`, left: `${(W - cradleW) / 2}px`, top: `${freeTop + (freeH - cradleH) / 2}px`});
  // The hull rests centred on the cradle at ~70% of its height; the harpoon may reach past its bow.
  const s = cradleH * 0.7 / FRAME.hullH;
  Object.assign($('[data-slip]', room).style, {width: `${FRAME.w * s}px`, left: `${cradleW / 2 + FRAME.x0 * s}px`, top: `${cradleH * 0.52 + FRAME.y0 * s}px`, transform: 'none'});
}
/* ---------- scenes ---------- */

const place = layout.placement;
// Dock props from the native capture (780×1688 logical frame).
const HUT = {left: 595, top: 840, width: 145, height: 270};
const SUB = {left: 420, top: 925, width: 150, height: 160};

function restaurantScene() {
  return `<div class="world" data-world="restaurant">
      <img class="backdrop" src="${asset('restaurant-dock.webp')}" alt="Live restaurant with the dock: deck, yellow submarine and Workshop hut">
      <img class="interactable hut-art" src="${asset('workshop-hut.png')}" alt="" style="${box({left: place.hut.left, top: place.hut.top, width: place.hut.width, height: place.hut.width * 542 / 296})}">
      <div class="dock-ship interactable" style="${shipPlacement(place.restaurant)}" data-dock-ship>${shipLayers(model.levels)}</div>
      <button type="button" class="hotspot hut" data-open-workshop style="${box(HUT)}" aria-label="Open Workshop"></button>
      <button type="button" class="hotspot sub" data-dive style="${box(SUB)}" aria-label="Submarine · start a dive"></button>
    </div>
    <div class="hud">
      <div class="pill cash" role="img" aria-label="${cash} cash" data-cash><img src="${asset('cash.png')}" alt=""><b>${cash.toLocaleString()}</b></div>
      <button type="button" class="pill edit" aria-label="Edit (not part of this review)">${svg('edit')}<span>Edit</span></button>
    </div>
    <div class="ws-host" data-host hidden></div>
    <div class="toast" data-toast role="status"></div>`;
}
const box = b => `left:${b.left / CW * 100}%;top:${b.top / CH * 100}%;width:${b.width / CW * 100}%;height:${b.height / CH * 100}%`;

// Dive power-up placements (capture px): a shield pickup and a portal entrance ahead, both with the
// lime interaction signal. The ship's bubble shows Shield at start, then a picked-up shield, in its tier colour.
const SHIELD_AT = {x: 250, y: 760}, PORTAL_AT = {x: 540, y: 470};
let bubbleTimer = null;
function runBubble() {
  const g = $('[data-bubble]', phone);
  if (!g) return;
  const p = runProfile(model.levels, expedition), color = tierColors[tierOf('shield', model.levels.shield) - 1], r = DIVE_CELL * 0.62;
  // Loop: launch shield (if owned) → gap → a pickup's full shield duration → gap.
  const phases = [...(p.launch ? [['launch', p.launch]] : []), ['gap', 1.2], ['pickup', p.shield], ['gap', 1.4]], total = phases.reduce((a, [, d]) => a + d, 0);
  const start = performance.now();
  const tick = () => {
    if (!g.isConnected) return;
    let t = ((performance.now() - start) / 1000) % total, out = '';
    for (const [kind, d] of phases) { if (t < d) { if (kind !== 'gap') out = shieldBubble(r, color, reduced() ? 1 : 1 - t / d); break; } t -= d; }
    g.innerHTML = out;
    bubbleTimer = requestAnimationFrame(tick);
  };
  cancelAnimationFrame(bubbleTimer); tick();
}
// Edit mode inventory dock (r7) on the shared tab control: People | Layout | Floor, Shop as its own action.
const dockArt = n => new URL(`../editor-dock-preview/assets/${n}.png`, import.meta.url).href;
const ICON = {
  people: '<path d="M4 21v-3a8 8 0 0 1 16 0v3M8 6a4 4 0 1 0 8 0 4 4 0 0 0-8 0"/>',
  layout: '<path d="M4 5h16v14H4ZM4 10h16M10 10v9"/>',
  floor: '<path d="M3 3h7v7H3ZM14 3h7v7h-7ZM3 14h7v7H3ZM14 14h7v7h-7Z"/>',
  shop: '<path d="M5 7h14l2 14H3L5 7Zm3 0V5a4 4 0 0 1 8 0v2"/>',
};
const tabIcon = k => `<svg class="tab-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON[k]}</svg>`;
const GOODS = {
  people: [['chef-lena', 'Lena', null], ['chef-omar', 'Omar', null]],
  layout: [['belt-straight-e', 'Belt', 6], ['stool-wood', 'Stool', 4], ['plant-angular', 'Plant', 2], ['crate-wood', 'Crate', 2], ['barrel-wood', 'Barrel', 1]],
  floor: [['floor-cream', 'Cream', null]],
};
let dockCategory = 'layout';
function dockGoods() {
  return GOODS[dockCategory].map(([art, name, count]) => `<button type="button" class="good ${dockCategory}"><span class="good-art"><img src="${dockArt(art)}" alt=""></span><span class="good-name">${name}</span>${count ? `<i class="count">${count}</i>` : ''}</button>`).join('');
}
function editScene() {
  return `<div class="world" data-world="restaurant"><img class="backdrop" src="${asset('restaurant-dock.webp')}" alt="Restaurant in Edit mode"><div class="dock-ship plain" style="${shipPlacement(place.restaurant)}">${shipLayers(model.levels)}</div></div>
    <div class="hud"><div class="pill cash" role="img" aria-label="${cash} cash"><img src="${asset('cash.png')}" alt=""><b>${cash.toLocaleString()}</b></div><span class="pill editing">${svg('edit')}<span>Editing</span></span><button type="button" class="pill live">Live</button></div>
    <section class="edit-dock wr-panel" aria-label="Inventory">
      <div class="dock-head">${tabBar(['people', 'layout', 'floor'].map(k => ({id: k, label: k[0].toUpperCase() + k.slice(1), icon: tabIcon(k)})), dockCategory, {attr: 'category', controls: 'dock-goods', label: 'Editing category'})}
        <button type="button" class="dock-shop" aria-haspopup="dialog">${tabIcon('shop')}<span>Shop</span></button></div>
      <div class="dock-goods wr-catalog" id="dock-goods" role="tabpanel" aria-labelledby="tab-${dockCategory}">${dockGoods()}</div>
    </section>`;
}
function diveScene() {
  const p = runProfile(model.levels, expedition), dp = place.dive;
  return `<div class="world" data-world="dive">
      <img class="backdrop" src="${asset('dive.webp')}" alt="Expedition travelling between reef walls">
      <div class="dive-ship" style="${shipPlacement(dp)}" role="img" aria-label="${esc(shipLabel(model.levels))}">${shipLayers(model.levels)}</div>
      <svg class="dive-features" viewBox="0 0 ${CW} ${CH}" aria-hidden="true"><defs>${softFilter}</defs>
        <g transform="translate(${SHIELD_AT.x} ${SHIELD_AT.y})" class="bob">${signalGlow(DIVE_CELL * 0.42)}${shieldEmblem(DIVE_CELL * 0.3, 'dive')}</g>
        <g transform="translate(${PORTAL_AT.x} ${PORTAL_AT.y})">${signalGlow(DIVE_CELL * 0.62)}<g class="spin">${swirl(DIVE_CELL * 0.36, tierColors[tierOf('passage', model.levels.passage) - 1])}</g></g>
        <g transform="translate(${dp.cx} ${dp.cy - DIVE_CELL * 0.08})" data-bubble></g>
      </svg>
      <img class="portal-ring" src="${asset('portal-ring.png')}" alt="" style="left:${(PORTAL_AT.x - DIVE_CELL * 0.525) / CW * 100}%;top:${(PORTAL_AT.y - DIVE_CELL * 0.5) / CH * 100}%;width:${DIVE_CELL * 1.05 / CW * 100}%">
      <div class="dive-pickups" data-pickups aria-hidden="true"></div>
      <svg class="fire-layer" data-dive-fire viewBox="0 0 ${CW} ${CH}" aria-hidden="true"></svg>
      <div class="dive-hull" role="img" aria-label="Hull ${p.hull} of ${p.hull}"><b>${p.hull}</b><small>/ ${p.hull}</small></div>
    </div>`;
}

const glowWith = (color, r) => signalGlow(r, color);
function galleryScene() {
  const base = fixture('workshop');
  const poor = {...base, salvage: 25};
  const maxed = {...base, levels: {...base.levels, hull: 5}};
  const fresh = {...base, levels: {...base.levels, harpoon: 3}, seen: {harpoon: false}};
  const looks = [['Base', {hull: 1, harpoon: 1, collector: 1}], ['Lv 3 · all', {hull: 3, harpoon: 3, collector: 3}], ['MAX · all', {hull: 5, harpoon: 5, collector: 4}], ['Mixed', {hull: 5, harpoon: 1, collector: 3}], ['Mixed', {hull: 1, harpoon: 5, collector: 4}]];
  const row = (label, html) => `<section class="g-row"><h3>${label}</h3><div class="g-catalog wr-catalog">${html}</div></section>`;
  return `<div class="gallery wr-panel">
    <h2>Shared components</h2>
    ${row('Normal', upgradeCard(byId.hull, base))}
    ${row('Pressed', upgradeCard(byId.hull, base, {pressed: true}))}
    ${row('Disabled · not enough salvage', upgradeCard(byId.harpoon, poor))}
    ${row('NEW · look just unlocked', upgradeCard(byId.harpoon, fresh))}
    ${row('MAX · final stats, no cost or arrow', upgradeCard(byId.hull, maxed))}
    <section class="g-row"><h3>Part tiers (whole-sprite swaps) and composed ships · dry / in water</h3>
      <div class="g-tiers">${tracks.map(t => `<div><b>${t.name}</b>${t.tiers.map((name, i) => `<figure>${partArt(t.id, i + 1)}<figcaption>${name}<br><small>${i ? `Lv ${t.looks[i - 1]}` : 'Base'}</small></figcaption></figure>`).join('')}</div>`).join('')}</div>
      <div class="g-looks">${looks.map(([label, lv]) => `<figure><span class="g-ship">${shipLayers(lv)}</span><span class="g-ship dive">${shipLayers(lv)}</span><figcaption>${label}</figcaption></figure>`).join('')}</div>
    </section>
    <section class="g-row"><h3>Power-up cards · colour is the look (white → violet → gold)</h3><div class="g-catalog wr-catalog">${tracks.filter(t => t.group === 'powerup').map(t => upgradeCard(t, {...base, levels: {...base.levels, shield: 3, passage: 4, launch: 1}})).join('')}</div></section>
    <section class="g-row"><h3>Dive signal glow on real water · lime = good/interactable (chosen), green blends into the cyan, red reserved for harmful</h3>
      <div class="g-glow">${[['Lime · chosen', 'good', '#b4ff2e'], ['Pure green · rejected', 'x', '#2bff5b'], ['Red · harmful (future)', 'bad', '#ff3b3b']].map(([label, kind, color]) => `<figure><svg viewBox="-60 -110 120 230" aria-hidden="true"><defs>${softFilter}</defs><g transform="translate(0 -45)" class="bob">${glowWith(color, 32)}${shieldEmblem(24, `g${kind}`)}</g><g transform="translate(0 55)">${glowWith(color, 46)}<g class="spin">${swirl(27, tierColors[0])}</g><image href="${asset('portal-ring.png')}" x="-39" y="-38" width="78" height="80"/></g></svg><figcaption>${label}</figcaption></figure>`).join('')}</div>
    </section>
    <section class="g-row"><h3>Salvage balance and doorway exit</h3><div class="g-inline"><div class="pill salvage-pill">${salvage(180)}</div><span class="door-tag sample"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5 8 12l7 7" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>Sushi Bar</span></div></section>
  </div>`;
}

/* ---------- behaviour ---------- */

const phone = $('#phone');
function render() {
  cancelAnimationFrame(diveFrame);
  clearInterval(diveShotTimer);
  phone.className = `phone view-${review}`;
  applyScreen();
  const transition = $('.iris', phone); // a scene switch in progress survives the re-render
  phone.innerHTML = review === 'dive' ? diveScene() : review === 'gallery' ? galleryScene() : review === 'edit' ? editScene() : restaurantScene();
  if (transition) phone.append(transition);
  $('#state').value = review;
  if (review === 'dive') { runPickups(); diveShots(); runBubble(); }
  if (['workshop', 'unaffordable', 'max'].includes(review)) openWorkshop(null, {fromReview: true});
  notes();
}

function openWorkshop(button, {fromReview = false} = {}) {
  const host = $('[data-host]', phone);
  if (!host || !host.hidden) return;
  opener = button || $('[data-open-workshop]', phone);
  host.hidden = false;
  activeGroup = 'equipment';
  host.innerHTML = workshopRoom(model);
  layoutRoom(host);
  if (!fromReview) history.pushState({workshop: true}, '');
  phone.classList.add('workshop-open');
  requestAnimationFrame(() => ($('[data-upgrade]:not([disabled])', host) || $('[data-close]', host))?.focus({preventScroll: true}));
}

function hideWorkshop() {
  const host = $('[data-host]', phone);
  if (!host || host.hidden) return;
  // NEW tags are acknowledged once the player has seen the page.
  model = {...model, seen: {}}; save();
  host.hidden = true; host.innerHTML = '';
  phone.classList.remove('workshop-open');
  refreshDock();
  (opener?.isConnected ? opener : $('[data-open-workshop]', phone))?.focus({preventScroll: true});
}
function closeWorkshop() { if (history.state?.workshop) history.back(); else leaveWorkshop(); }

// Every scene switch goes through sceneTransition: the iris closes on what was tapped and reopens on
// the new scene's focus (the ship on its cradle, the hut on the dock, the ship in the water).
const centreOf = el => { const r = el.getBoundingClientRect(), p = phone.getBoundingClientRect(); return {x: r.left - p.left + r.width / 2, y: r.top - p.top + r.height / 2}; };
const go = (from, swap, to) => sceneTransition(phone, {from, swap, to, loaderIcon: asset('salvage.png'), reduced: reduced()});
function enterWorkshop(button) {
  go(centreOf(button), () => openWorkshop(button), () => { const hero = $('[data-hero]', phone); return hero && centreOf(hero); });
}
function leaveWorkshop() {
  const door = $('.doorway', phone);
  if (!door) return hideWorkshop();
  go(centreOf(door), () => hideWorkshop(), () => centreOf($('[data-open-workshop]', phone)));
}
function enterDive(button) {
  go(centreOf(button), () => { review = 'dive'; model = {...model, review}; save(); history.replaceState(null, '', `?state=${review}`); render(); }, () => { const ship = $('.dive-ship', phone); return ship && centreOf(ship); });
}

function refreshDock() {
  const dock = $('[data-dock-ship]', phone);
  if (dock) dock.innerHTML = shipLayers(model.levels);
}

function upgrade(id, token) {
  const before = model, after = commit({type: 'upgrade', id, token});
  if (after === before) return;
  const host = $('[data-host]', phone), t = byId[id];
  const row = $(`.up-row[data-track="${id}"]`, host);
  row.outerHTML = upgradeCard(t, model);
  // Other cards may have become unaffordable.
  for (const other of tracks) if (other.id !== id) { const r = $(`.up-row[data-track="${other.id}"]`, host); if (r) r.outerHTML = upgradeCard(other, model); }
  $('.ws-tabs', host).outerHTML = trayTabs(model);
  rollBalance($('[data-balance]', host), shownBalance(host, before.salvage), model.salvage);
  layoutRoom(host);
  const fresh = $(`.up-row[data-track="${id}"]`, host);
  const button = $('[data-upgrade]', fresh);
  (button && !button.disabled ? button : $('.ws-list', host)).focus({preventScroll: true});
  if (!reduced()) {
    fresh.animate([{background: '#ffe6a4'}, {background: 'transparent'}], {duration: 700, easing: 'ease-out'});
    $('.stat .cur', fresh)?.animate([{transform: 'scale(1.18)'}, {transform: 'scale(1)'}], {duration: 360, easing: 'cubic-bezier(.3,1.6,.5,1)'});
  }
  if (id === 'harpoon') testFire(host);
  if (t.looks.includes(model.levels[id])) {
    $('[data-slip]', host).innerHTML = shipLayers(model.levels);
    $('[data-ship-label]', host).textContent = shipLabel(model.levels);
    const part = $(`[data-slip] [data-part="${id}"]`, host);
    if (part && !reduced()) part.animate([{opacity: 0, transform: 'translateY(-6%) scale(1.06)', filter: 'brightness(1.8)'}, {opacity: 1, transform: 'none', filter: 'brightness(1)'}], {duration: 520, easing: 'cubic-bezier(.2,.9,.3,1)'});
    sparkle($('[data-slip]', host));
  }
  notes();
}

const shownBalance = (host, fallback) => Number($('[data-balance] .salvage span', host)?.textContent.replace(/,/g, '')) || fallback;
let cancelShot = null;
function testFire(host) {
  const svg = $('[data-fire]', host), ship = $('[data-slip] .ship', host);
  if (!svg || !ship) return;
  cancelShot?.();
  $('[data-test-fire]', host).setAttribute('aria-label', `Test-fire the ${byId.harpoon.tiers[tierOf('harpoon', model.levels.harpoon) - 1].toLowerCase()}`);
  const box = ship.getBoundingClientRect(), frame = svg.getBoundingClientRect(), n = noseInBox(model.levels);
  const cell = box.height * 0.42;
  cancelShot = fireHarpoon(svg, {nose: {x: box.left - frame.left + box.width * n.x, y: box.top - frame.top + box.height * n.y}, cell, tier: tierOf('harpoon', model.levels.harpoon), reach: Math.min(box.top - frame.top, cell * 2.2), reduced: reduced()});
}
function rollBalance(node, from, to) {
  node.setAttribute('aria-label', `${to} salvage`);
  const label = $('.salvage span', node);
  if (reduced()) { label.textContent = to.toLocaleString(); return; }
  // Only the latest roll writes; a timer lands the exact value even if frames are throttled.
  const token = ++rollSerial, start = performance.now();
  const step = now => { if (token !== rollSerial) return; const k = Math.min(1, (now - start) / 420); label.textContent = Math.round(from + (to - from) * (1 - (1 - k) ** 3)).toLocaleString(); if (k < 1 && label.isConnected) requestAnimationFrame(step); };
  requestAnimationFrame(step);
  setTimeout(() => { if (token === rollSerial) label.textContent = to.toLocaleString(); }, 460);
  node.animate([{transform: 'scale(1)'}, {transform: 'scale(.92)'}, {transform: 'scale(1)'}], {duration: 260});
}

function sparkle(slip) {
  if (reduced()) return;
  for (let i = 0; i < 7; i++) {
    const s = document.createElement('span');
    s.className = 'spark'; s.style.left = `${38 + Math.random() * 24}%`; s.style.top = `${30 + Math.random() * 40}%`;
    slip.append(s);
    s.animate([{transform: 'scale(0)', opacity: 1}, {transform: `translate(${(Math.random() - .5) * 60}px,${-20 - Math.random() * 30}px) scale(1)`, opacity: 0}], {duration: 650 + i * 40, easing: 'ease-out'}).onfinish = () => s.remove();
  }
}

// Live service continues behind the Workshop (review clock: an occasional sale).
function tickSales() {
  clearInterval(saleTimer);
  saleTimer = setInterval(() => {
    const pill = $('[data-cash]', phone);
    if (!pill || document.hidden) return;
    cash += live.saleAmounts[serial++ % live.saleAmounts.length];
    pill.setAttribute('aria-label', `${cash} cash`);
    $('b', pill).textContent = cash.toLocaleString();
  }, live.saleEverySeconds * 1000);
}

// Dive: salvage drifts down the lane; inside attraction range it is drawn to the ship.
function runPickups() {
  const layer = $('[data-pickups]', phone);
  if (!layer) return;
  const p = runProfile(model.levels, expedition), dp = place.dive;
  const ship = {x: dp.cx, y: dp.cy};
  const lanes = [-1.35, 1.0, -0.8, 1.45, 0.7, -1.1];
  const items = lanes.map((dx, i) => ({dx, y: -2.4 - i * 1.6, node: Object.assign(document.createElement('img'), {src: asset('salvage.png'), className: 'pickup', alt: ''}), pulled: false}));
  items.forEach(it => layer.append(it.node));
  let last = performance.now();
  const speed = 2.1; // rows per second (forward_rows_per_second)
  const frame = now => {
    const dt = Math.min(.05, (now - last) / 1000); last = now;
    for (const it of items) {
      if (!reduced()) it.y += speed * dt;
      let x = it.dx, y = it.y;
      const dist = Math.hypot(x, y);
      if (dist <= p.reach) it.pulled = true;
      if (it.pulled) { const k = Math.max(0, 1 - 6 * dt); it.dx *= k; it.y *= k; x = it.dx; y = it.y; }
      if (Math.hypot(x, y) < expedition.shipRadius || it.y > 3) {
        if (it.pulled) pop(layer, ship);
        it.dx = lanes[(lanes.indexOf(it.dx) + 1 + Math.floor(now) % lanes.length) % lanes.length] || lanes[0];
        it.y = -6; it.pulled = false; x = it.dx; y = it.y;
      }
      it.node.style.left = `${(ship.x + x * DIVE_CELL) / CW * 100}%`;
      it.node.style.top = `${(ship.y + y * DIVE_CELL) / CH * 100}%`;
      it.node.classList.toggle('pulled', it.pulled);
    }
    diveFrame = requestAnimationFrame(frame);
  };
  diveFrame = requestAnimationFrame(frame);
}
// The dive fires the current harpoon every few seconds from the nose hatch (capture px).
let diveShotTimer = null;
function diveShots() {
  clearInterval(diveShotTimer);
  const shoot = () => {
    const svg = $('[data-dive-fire]', phone);
    if (!svg || document.hidden) return;
    const dp = place.dive, s = dp.hull_height / FRAME.hullH, n = noseInBox(model.levels);
    fireHarpoon(svg, {nose: {x: dp.cx + FRAME.x0 * s + FRAME.w * s * n.x, y: dp.cy + FRAME.y0 * s + FRAME.h * s * n.y}, cell: DIVE_CELL, tier: tierOf('harpoon', model.levels.harpoon), reach: DIVE_CELL * 4.5, reduced: reduced()});
  };
  shoot(); diveShotTimer = setInterval(shoot, 2600);
}
function pop(layer, ship) {
  const s = document.createElement('span');
  s.className = 'pickup-pop'; s.textContent = `+${expedition.salvagePerPickup}`;
  s.style.left = `${ship.x / CW * 100}%`; s.style.top = `${(ship.y - 70) / CH * 100}%`;
  layer.append(s);
  s.animate([{transform: 'translate(-50%,0)', opacity: 1}, {transform: 'translate(-50%,-30px)', opacity: 0}], {duration: 700}).onfinish = () => s.remove();
}

function notes() {
  const base = runProfile({hull: 1, harpoon: 1, collector: 1}, expedition), now = runProfile(model.levels, expedition);
  const lv = tracks.map(t => `<li><b>${t.name}</b> Lv ${model.levels[t.id]}/${maxLevel(t.id)} · ${t.format(statAt(t.id, model.levels[t.id]))} · ${t.tiers[tierOf(t.id, model.levels[t.id]) - 1].toLowerCase()}</li>`).join('');
  const guide = {
    edit: 'Edit mode inventory on the shared tab control (the same maple segments as the Workshop). People, Layout and Floor are tabs; Shop stays its own action. Arrow keys switch tabs.',
    restaurant: 'The submarine and hut carry the approved cyan interactable outline. Tap the <b>Workshop hut</b> on the dock to open the Workshop. Live service keeps running (cash rises). The dock submarine shows every fitted part. Tap the submarine to see a dive.',
    workshop: 'The Workshop is its own room. Upgrade pays exactly one level and stays on the page. Reaching <b>Lv 3</b> fits that part on the cradle with a NEW tag, then on the dock and in the dive. Leave through the <b>Sushi Bar</b> doorway, Escape or Back. Try the Screen sizes: the room stays anchored to its wall and the ship always sits in the free floor above the cards.',
    unaffordable: 'Every Upgrade is disabled and no shortage message appears. Use <b>+100 salvage</b> to make them affordable again.',
    max: 'Hull is at its cap: the card keeps its final stat and shows MAX with no cost or arrow.',
    dive: 'The ring is the attraction range; salvage inside it is drawn to the ship (value unchanged). The hull readout is the full upgraded maximum on departure.',
    gallery: 'The same card, balance, close and ship-look components used in the Workshop, dock and dive.',
  }[review];
  $('#notes').innerHTML = `<h2>${$('#state').selectedOptions[0].textContent}</h2><p>${guide}</p>
    <h3>Equipment</h3><ul>${lv}</ul><p class="salv">${salvage(model.salvage)} banked</p>
    <h3>Equivalent run · base → now</h3>
    <table><tr><th>Max hull</th><td>${base.hull} → <b>${now.hull}</b></td></tr>
    <tr><th>Rock hits survived</th><td>${base.hitsSurvived} → <b>${now.hitsSurvived}</b></td></tr>
    <tr><th>Eel reel-in time</th><td>${base.reelSeconds.toFixed(1)} s → <b>${now.reelSeconds.toFixed(1)} s</b></td></tr>
    <tr><th>Attraction range</th><td>${base.reach.toFixed(1)} → <b>${now.reach.toFixed(1)} tiles</b></td></tr>
    <tr><th>Shield duration</th><td>${base.shield} → <b>${now.shield} s</b></td></tr>
    <tr><th>Passage ride</th><td>${base.passage} → <b>${now.passage} rows</b></td></tr>
    <tr><th>Shield at start</th><td>${base.launch ? base.launch + ' s' : 'none'} → <b>${now.launch ? now.launch + ' s' : 'none'}</b></td></tr>
    <tr><th>Salvage per pickup</th><td>${expedition.salvagePerPickup} → <b>${expedition.salvagePerPickup}</b></td></tr></table>
    <p class="fine">Encounters do not scale to equipment. Collision footprint stays a ${expedition.shipRadius}-tile circle; parts are visual only.</p>`;
}

/* ---------- wiring ---------- */

phone.addEventListener('click', e => {
  const t = e.target.closest('button');
  if (!t || t.disabled) return;
  if (t.matches('[data-open-workshop]')) enterWorkshop(t);
  else if (t.matches('[data-close]') && t.closest('[data-host]')) closeWorkshop();
  else if (t.matches('[data-upgrade]') && t.closest('[data-host]')) { if (e.detail < 2) upgrade(t.dataset.upgrade, `${t.dataset.upgrade}-${model.levels[t.dataset.upgrade]}-${Date.now()}`); }
  else if (t.matches('[data-group]')) { activeGroup = t.dataset.group; const host = t.closest('[data-host]'); refreshTray(host); layoutRoom(host); $(`#tab-${activeGroup}`, host).focus(); }
  else if (t.matches('[data-category]')) { dockCategory = t.dataset.category; $('.dock-head .ws-tabs', phone).outerHTML = tabBar(['people', 'layout', 'floor'].map(k => ({id: k, label: k[0].toUpperCase() + k.slice(1), icon: tabIcon(k)})), dockCategory, {attr: 'category', controls: 'dock-goods', label: 'Editing category'}); const g = $('#dock-goods', phone); g.innerHTML = dockGoods(); g.setAttribute('aria-labelledby', `tab-${dockCategory}`); $(`#tab-${dockCategory}`, phone).focus(); }
  else if (t.matches('[data-test-fire]')) testFire(t.closest('[data-host]'));
  else if (t.matches('[data-dive]')) enterDive(t);
});
addEventListener('keydown', e => {
  if (e.target.matches?.('[data-category]') && ['ArrowLeft', 'ArrowRight'].includes(e.key)) { const tabs = [...e.target.parentElement.children], i = tabs.indexOf(e.target); tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length].click(); return; }
  if (e.target.matches?.('[role=tab]') && ['ArrowLeft', 'ArrowRight'].includes(e.key)) { const i = groups.findIndex(g => g.id === activeGroup); groups[(i + (e.key === 'ArrowRight' ? 1 : groups.length - 1)) % groups.length] && $(`[data-group="${groups[(i + (e.key === 'ArrowRight' ? 1 : groups.length - 1)) % groups.length].id}"]`, phone).click(); return; } if (e.key === 'Escape' && !$('[data-host]', phone)?.hidden) closeWorkshop(); });
addEventListener('popstate', () => leaveWorkshop());
addEventListener('blur', () => { for (const a of document.getAnimations()) if (a.effect?.target?.classList?.contains('spark')) a.finish(); });

$('#state').addEventListener('change', e => { const from = review; review = e.target.value; model = continues(from, review) ? {...model, review} : {...fixture(review), review}; save(); history.replaceState(null, '', `?state=${review}`); render(); });
const screenSelect = $('#screen');
function applyScreen() {
  const v = screenSelect.value;
  phone.classList.toggle('fill', v === 'fill');
  phone.style.setProperty('--ratio', v === 'fill' ? 'auto' : v);
  try { localStorage.setItem(storageKey + '-screen', v); } catch {}
}
try { const saved = localStorage.getItem(storageKey + '-screen'); if (saved) screenSelect.value = saved; else if (innerWidth < 900) screenSelect.value = 'fill'; } catch {}
screenSelect.addEventListener('change', applyScreen);
applyScreen();
$('#reset').addEventListener('click', () => { model = {...fixture(review), review}; cash = live.cash; save(); render(); });
$('#earn').addEventListener('click', () => {
  const from = model.salvage; model = {...model, salvage: model.salvage + 100}; save();
  const host = $('[data-host]', phone);
  if (host && !host.hidden) { refreshTray(host); rollBalance($('[data-balance]', host), from, model.salvage); }
  notes();
});

new ResizeObserver(() => { const host = $('[data-host]', phone); if (host && !host.hidden) layoutRoom(host); }).observe(phone);
render();
tickSales();
