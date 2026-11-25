// Rules for the guest room prototype. Pure and deterministic: every random draw comes from state.seed.
import { BALANCE as B } from './balance.js';

export const key = (x, y) => `${x},${y}`;
export const xy = (k) => k.split(',').map(Number);
export const RING = B.ring.map(([x, y]) => key(x, y));
const RINGI = new Map(RING.map((k, i) => [k, i]));
export const isBelt = (k) => RINGI.has(k);
export const ENTRY = RINGI.get(key(B.hatch[0] + 1, B.hatch[1])); // the belt tile the hatch sets plates on
const DOORK = key(...B.door);
const RESERVED = new Set([DOORK]);
const ADJ = [[1, 0], [-1, 0], [0, 1], [0, -1]];
const DOOR = [B.door[0] + 0.5, B.door[1] + 0.9];
const inFloor = (x, y) => x >= 0 && y >= 0 && x < B.size && y < B.size;
const needsAccess = (kind) => !!(B.items[kind].chairs || B.items[kind].spots);

// --- walking ------------------------------------------------------------------------------------------------
// Guests walk tile to tile on bare floor, never over the belt or a piece, except the one piece they are going
// to. The tile inside a seat is where they sit, and a game's tile is where they stand to play it.
function blocked(state, items = state.items) {
  const out = new Set(RING);
  for (const i of items) for (const k of footprint(i)) out.add(k);
  return out;
}
export function route(state, from, to, target = null) {
  if (from === to) return [to];
  // the piece a guest is getting up from can be crossed on the way out, as can the one they are going to
  const here = state.items.find((i) => footprint(i).includes(from));
  const solid = blocked(state, state.items.filter((i) => i.id !== target && i !== here));
  const prev = new Map([[from, null]]), queue = [from];
  while (queue.length) {
    const k = queue.shift();
    if (k === to) break;
    const [x, y] = xy(k);
    for (const [dx, dy] of ADJ) {
      const n = key(x + dx, y + dy);
      if (prev.has(n) || !inFloor(x + dx, y + dy) || solid.has(n)) continue;
      prev.set(n, k); queue.push(n);
    }
  }
  if (!prev.has(to)) return null;
  const path = [];
  for (let k = to; k !== from; k = prev.get(k)) path.unshift(k);
  return path;
}
// Floor a guest can reach from the street door, given these pieces.
function reached(state, items) {
  const solid = blocked(state, items), seen = new Set([DOORK]), queue = [DOORK];
  while (queue.length) {
    const [x, y] = xy(queue.shift());
    for (const [dx, dy] of ADJ) {
      const n = key(x + dx, y + dy);
      if (seen.has(n) || !inFloor(x + dx, y + dy) || solid.has(n)) continue;
      seen.add(n); queue.push(n);
    }
  }
  return seen;
}
// A seat or a game is reachable if guests can step onto it from floor joined to the door; once on a seat they
// can move across its own tiles, so a booth's back row is fine as long as one side is open.
function reachable(floor, item) {
  return footprint(item).some((k) => { const [x, y] = xy(k); return ADJ.some(([dx, dy]) => floor.has(key(x + dx, y + dy))); });
}
export function unreachable(state, items = state.items) {
  const floor = reached(state, items);
  return items.filter((i) => needsAccess(i.kind) && !reachable(floor, i));
}
const tileOf = (g) => (g.y >= B.size ? DOORK : key(Math.min(B.size - 1, Math.max(0, Math.floor(g.x))), Math.floor(g.y)));
function goTo(state, g, to, final, target) {
  g.path = route(state, tileOf(g), to, target) || [];
  if (g.y >= B.size && g.path[0] !== DOORK) g.path.unshift(DOORK); // in from the street through the doorway
  g.target = target; [g.tx, g.ty] = final;
}

function rand(state) { // mulberry32
  let t = (state.seed = (state.seed + 0x6d2b79f5) | 0);
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}

export function createGame(seed = 1) {
  const state = {
    v: 3, t: 0, seed, coins: B.start.coins, items: [], nextId: 1,
    plates: RING.map(() => null), guests: [], queue: [], cap: 0, kitchen: 0,
    carry: { cook: 0, arrive: 0 },
    stats: { plates: 0, guests: 0, away: 0, walked: 0, earned: 0 },
    events: [],
  };
  for (const s of B.start.items) add(state, s.kind, s.x, s.y, s.style, s.rot || 0, 0);
  return state;
}

// --- pieces ----------------------------------------------------------------------------------------------
export const spec = (item) => B.items[item.kind];
export function size(kind, rot) { const K = B.items[kind]; return rot ? [K.h, K.w] : [K.w, K.h]; }
export function tiles(kind, x, y, rot = 0) {
  const [w, h] = size(kind, rot), out = [];
  for (let dy = 0; dy < h; dy++) for (let dx = 0; dx < w; dx++) out.push(key(x + dx, y + dy));
  return out;
}
export const footprint = (item) => tiles(item.kind, item.x, item.y, item.rot);
export const byId = (state, id) => state.items.find((i) => i.id === id);
export function itemAt(state, k) {
  // a piece over the belt is found before the belt, and only an arch stands on one
  return state.items.find((i) => footprint(i).includes(k)) || null;
}
export const nameOf = (item) => spec(item).names?.[item.style] || spec(item).name;
// Belt tiles a seat can reach: every belt tile touching it.
export function reach(item) {
  const out = new Set();
  for (const k of footprint(item)) {
    const [x, y] = xy(k);
    for (const [dx, dy] of ADJ) { const n = key(x + dx, y + dy); if (RINGI.has(n)) out.add(RINGI.get(n)); }
  }
  return [...out];
}

export function canPlace(state, kind, x, y, rot = 0, ignore = null) {
  const K = B.items[kind];
  if (!K) return { ok: false, why: 'Unknown piece' };
  const ts = tiles(kind, x, y, rot);
  for (const k of ts) {
    const [tx, ty] = xy(k);
    if (tx < 0 || ty < 0 || tx >= B.size || ty >= B.size) return { ok: false, why: 'That runs off the floor' };
    if (RESERVED.has(k)) return { ok: false, why: 'Keep the door clear' };
    const other = state.items.find((i) => i.id !== ignore && footprint(i).includes(k));
    if (other) return { ok: false, why: `${nameOf(other)} is in the way` };
    if (K.onBelt ? !RINGI.has(k) : RINGI.has(k)) return { ok: false, why: K.onBelt ? `${K.name}es stand over the belt` : 'That is the belt' };
  }
  if (K.max && state.items.filter((i) => i.kind === kind && i.id !== ignore).length >= K.max) return { ok: false, why: `One ${K.name.toLowerCase()} is the room's limit` };
  if (K.chairs && !reach({ kind, x, y, rot }).length) return { ok: false, why: 'A seat has to touch the belt to reach the plates' };
  // nothing may cut guests off from a seat or a game, this piece included
  const ghost = { id: -1, kind, x, y, rot };
  const cut = unreachable(state, [...state.items.filter((i) => i.id !== ignore), ghost]);
  if (cut.includes(ghost)) return { ok: false, why: 'Guests could not walk to it there' };
  if (cut.length) return { ok: false, why: `That would block the way to the ${nameOf(cut[0])}` };
  return { ok: true };
}

function add(state, kind, x, y, style, rot, spent) {
  const K = B.items[kind];
  const item = { id: state.nextId++, kind, x, y, rot, style, tier: 1, spent };
  if (K.chairs) item.who = Array(K.chairs).fill(null);
  if (K.spots) item.who = Array(K.spots).fill(null);
  state.items.push(item);
  return item;
}

export function place(state, kind, x, y, style, rot = 0) {
  const K = B.items[kind];
  const res = canPlace(state, kind, x, y, rot);
  if (!res.ok) return res;
  if (state.coins < K.price) return { ok: false, why: `${K.name} costs ${K.price}` };
  state.coins -= K.price;
  return { ok: true, item: add(state, kind, x, y, style, rot, K.price) };
}

export function move(state, id, x, y, rot) {
  const item = byId(state, id);
  if (!item) return { ok: false };
  const r = rot ?? item.rot;
  const res = canPlace(state, item.kind, x, y, r, id);
  if (!res.ok) return res;
  Object.assign(item, { x, y, rot: r });
  // guests sitting in it move with it
  for (const g of state.guests) if (g.seat === id && g.st !== 'walk') [g.x, g.y] = chairPos(item, g.chair);
  return { ok: true };
}
export function turn(state, id) {
  const item = byId(state, id), K = item && spec(item);
  if (!item || K.w === K.h) return { ok: false, why: 'That piece looks the same either way' };
  return move(state, id, item.x, item.y, item.rot ? 0 : 1);
}
// Repainting is free: matching a room's style should never cost a player the pieces they already own.
export function restyle(state, id, style) {
  const item = byId(state, id);
  if (!item || !B.styles[style]) return { ok: false };
  item.style = style;
  return { ok: true };
}
export const upgradeCost = (item) => item.tier >= 3 ? null : Math.round(spec(item).price * B.tiers.cost[item.tier]);
export function upgrade(state, id) {
  const item = byId(state, id), cost = item && upgradeCost(item);
  if (cost == null) return { ok: false, why: 'Fully upgraded' };
  if (state.coins < cost) return { ok: false, why: `Upgrading costs ${cost}` };
  state.coins -= cost; item.spent += cost; item.tier++;
  return { ok: true };
}
// Selling gives back everything spent, so rearranging a room is never a loss.
export function sell(state, id) {
  const item = byId(state, id);
  if (!item) return { ok: false };
  for (const g of state.guests) {
    if (g.seat === id) { g.seat = null; g.chair = null; if (g.st !== 'leave') { g.st = 'stand'; g.wait = 0; } }
    if (g.spot === id) { g.spot = null; g.timer = 0; }
  }
  state.items = state.items.filter((i) => i !== item);
  state.coins += item.spent;
  return { ok: true };
}

export const capacity = (state) => B.capacity.size[state.cap];
export const kitchenRate = (state) => B.kitchen.perMin[state.kitchen];
const nextPrice = (table, lvl) => table.price[lvl + 1] ?? null;
export const capPrice = (state) => nextPrice(B.capacity, state.cap);
export const kitchenPrice = (state) => nextPrice(B.kitchen, state.kitchen);
export function buyCapacity(state) {
  const p = capPrice(state);
  if (p == null) return { ok: false, why: 'The room holds as many as it ever can' };
  if (state.coins < p) return { ok: false, why: `More room costs ${p}` };
  state.coins -= p; state.cap++; return { ok: true };
}
export function buyKitchen(state) {
  const p = kitchenPrice(state);
  if (p == null) return { ok: false, why: 'The kitchen is as fast as it gets' };
  if (state.coins < p) return { ok: false, why: `A faster kitchen costs ${p}` };
  state.coins -= p; state.kitchen++; return { ok: true };
}

// --- appeal ----------------------------------------------------------------------------------------------
// The room's style is whichever has the most pieces; coherence is the share of pieces in it.
export function theme(state) {
  const n = {};
  for (const i of state.items) n[i.style] = (n[i.style] || 0) + 1;
  const best = Object.entries(n).sort((a, b) => b[1] - a[1])[0];
  if (!best) return { style: null, coherence: 0, mult: B.coherence.low };
  const coherence = best[1] / state.items.length;
  return { style: best[0], coherence, mult: B.coherence.low + B.coherence.span * coherence };
}
export const charm = (item) => spec(item).charm * B.tiers.charm[item.tier - 1];
export function appeal(state) {
  const sum = state.items.reduce((s, i) => s + charm(i), 0);
  return sum * theme(state).mult;
}
export const band = (state) => state.items.find((i) => i.kind === 'band');
export function playing(state) {
  const b = band(state);
  if (!b) return false;
  const K = spec(b);
  return state.t % (K.on + K.off) < K.on;
}
// Parties a minute walking up to the door.
export function traffic(state) {
  const base = B.traffic.base + appeal(state) * B.traffic.perAppeal;
  return base * (playing(state) ? B.items.band.boost : 1);
}

// --- guests ----------------------------------------------------------------------------------------------
export const inside = (state) => state.guests.filter((g) => g.st !== 'leave').length;
// One guest to a tile, as in the game: chair i is the middle of the seat's i-th tile.
export function chairPos(item, i) {
  const [tx, ty] = xy(footprint(item)[i]);
  return [tx + 0.5, ty + 0.5];
}
const seats = (state) => state.items.filter((i) => spec(i).chairs);
// A party takes a whole empty seat of its size or the next one up, and a couple takes the glass room before a
// cage of the same size because it pays more.
export function pickSeat(state, n) {
  return seats(state)
    .filter((s) => s.who.length >= n && s.who.every((w) => w == null))
    .sort((a, b) => a.who.length - b.who.length || (spec(b).pay || 1) - (spec(a).pay || 1))[0] || null;
}
function sitDown(state, g, item, i) {
  item.who[i] = g.id; g.seat = item.id; g.chair = i;
  goTo(state, g, footprint(item)[i], chairPos(item, i), item.id); g.st = 'walk'; g.next = 'seat'; g.wait = 0;
}
function freeChair(state, g) {
  const own = g.lastSeat != null && byId(state, g.lastSeat);
  if (own && own.who.includes(null)) return [own, own.who.indexOf(null)];
  for (const s of seats(state)) { const i = s.who.indexOf(null); if (i >= 0) return [s, i]; }
  return null;
}
function standUp(state, g) {
  const s = g.seat != null && byId(state, g.seat);
  if (s) s.who[g.chair] = null;
  g.lastSeat = g.seat; g.seat = null; g.chair = null;
}
function leave(state, g, why) {
  standUp(state, g);
  const a = g.spot != null && byId(state, g.spot);
  if (a) a.who[a.who.indexOf(g.id)] = null;
  g.spot = null; g.st = 'leave'; goTo(state, g, DOORK, DOOR, null);
  if (why) state.events.push({ type: why, x: g.x, y: g.y });
}
const seated = (g) => g.st === 'seat' || g.st === 'eat';
// A top-up to a guest's appetite, shared by every source and capped across the visit.
function topUp(state, g, n, why) {
  const add = Math.min(n, B.maxExtras - g.extras);
  if (add <= 0) return 0;
  g.app += add; g.extras += add;
  if (why) state.events.push({ type: why, x: g.x, y: g.y });
  return add;
}
function payFor(item) {
  return Math.round(B.plate * (spec(item).pay || 1) * B.tiers.tip[item.tier - 1]);
}

function admit(state) {
  for (const p of [...state.queue]) {
    const room = capacity(state) - inside(state), seat = room >= p.size && pickSeat(state, p.size);
    if (seat) {
      state.queue = state.queue.filter((q) => q !== p);
      for (let i = 0; i < p.size; i++) {
        const lo = B.appetite[0], hi = B.appetite[1];
        const g = { id: state.nextId++, party: p.id, hue: p.hue, x: DOOR[0] + (i - (p.size - 1) / 2) * 0.3, y: DOOR[1] + 0.3,
          app: lo + Math.floor(rand(state) * (hi - lo + 1)), extras: 0, visits: 0, ate: 0, seat: null, chair: null, spot: null, lastSeat: null, path: [] };
        sitDown(state, g, seat, i);
        state.guests.push(g);
      }
      state.events.push({ type: 'enter', size: p.size });
    } else if (--p.wait <= 0) {
      state.queue = state.queue.filter((q) => q !== p);
      state.stats.away += p.size;
      state.events.push({ type: 'away', size: p.size, why: room < p.size ? 'full' : 'seat' });
    }
  }
}

function arrive(state) {
  state.carry.arrive += traffic(state) / (60000 / B.tickMs);
  while (state.carry.arrive >= 1) {
    state.carry.arrive -= 1;
    let r = rand(state) * B.parties.reduce((s, p) => s + p.w, 0), size = 1;
    for (const p of B.parties) { if ((r -= p.w) < 0) { size = p.size; break; } }
    if (state.queue.length >= B.queueMax) { state.stats.away += size; state.events.push({ type: 'away', size, why: 'queue' }); continue; }
    state.queue.push({ id: state.nextId++, size, wait: B.queuePatience, hue: Math.floor(rand(state) * 360) });
  }
}

function belt(state) {
  if (state.t % B.beltEvery === 0) {
    const n = RING.length, moved = RING.map(() => null);
    state.plates.forEach((p, i) => { if (p) moved[(i + 1) % n] = p; });
    state.plates = moved;
  }
  state.carry.cook = Math.min(state.carry.cook + kitchenRate(state) / (60000 / B.tickMs), 1);
  if (state.carry.cook >= 1 && !state.plates[ENTRY]) {
    state.carry.cook -= 1;
    state.plates[ENTRY] = { dish: B.dishes[Math.floor(rand(state) * B.dishes.length)] };
  }
}

function shows(state) {
  for (const tv of state.items.filter((i) => i.kind === 'tv')) {
    if ((state.t + tv.id * 17) % spec(tv).every !== 0) continue;
    state.events.push({ type: 'goal', id: tv.id });
    for (const g of state.guests) if (seated(g)) topUp(state, g, 1, 'cheer');
  }
  const b = band(state);
  if (b && state.t % (spec(b).on + spec(b).off) === 0) {
    state.events.push({ type: 'set', id: b.id });
    for (const g of state.guests) if (seated(g)) topUp(state, g, 1, 'dance');
  }
}

function afterMeal(state, g) {
  if (g.extras < B.maxExtras) {
    const game = state.items.find((i) => spec(i).spots && i.who.includes(null));
    if (game && (B.refill[g.visits] || 0) > 0) {
      standUp(state, g);
      game.who[game.who.indexOf(null)] = g.id;
      g.spot = game.id; goTo(state, g, key(game.x, game.y), [game.x + 0.5, game.y + 0.78], game.id); g.st = 'walk'; g.next = 'play'; g.timer = spec(game).play;
      return;
    }
  }
  state.stats.guests++;
  leave(state, g, 'happy');
}

function step(state, g) {
  switch (g.st) {
    case 'walk': case 'leave': {
      // a piece put down across the way since the route was planned: plan again from here
      const next = g.path[0];
      const here = itemAt(state, tileOf(g));
      if (next && next !== g.path.at(-1) && blocked(state, state.items.filter((i) => i.id !== g.target && i !== here)).has(next)) {
        g.path = route(state, tileOf(g), g.path.at(-1), g.target) || [];
      }
      const [wx, wy] = g.path.length ? xy(g.path[0]).map((v) => v + 0.5) : [g.tx, g.ty];
      const dx = wx - g.x, dy = wy - g.y, d = Math.hypot(dx, dy);
      if (d > B.walk) { g.x += (dx / d) * B.walk; g.y += (dy / d) * B.walk; return true; }
      g.x = wx; g.y = wy;
      if (g.path.length) { g.path.shift(); return true; }
      if (g.st === 'leave') return false;
      g.st = g.next;
      return true;
    }
    case 'seat': {
      if (g.app <= 0) { afterMeal(state, g); return true; }
      const s = byId(state, g.seat);
      const i = reach(s).find((r) => state.plates[r]);
      if (i != null) {
        g.dish = state.plates[i].dish; state.plates[i] = null;
        const pay = payFor(s);
        state.coins += pay; state.stats.earned += pay; state.stats.plates++; g.ate++;
        state.events.push({ type: 'coin', x: g.x, y: g.y, pay });
        g.st = 'eat'; g.timer = B.eat; g.wait = 0;
      } else if (++g.wait > B.hungry) { state.stats.walked++; leave(state, g, 'grumpy'); }
      return true;
    }
    case 'eat':
      if (--g.timer <= 0) { g.dish = null; g.app--; g.st = 'seat'; if (g.app <= 0) afterMeal(state, g); }
      return true;
    case 'play': {
      if (--g.timer > 0 && g.spot != null) return true;
      const game = g.spot != null && byId(state, g.spot);
      if (game) game.who[game.who.indexOf(g.id)] = null;
      g.spot = null;
      const got = topUp(state, g, B.refill[g.visits] || 0, 'hungry');
      g.visits++;
      if (!got) { state.stats.guests++; leave(state, g, 'happy'); return true; }
      g.st = 'stand'; g.wait = 0;
      return true;
    }
    case 'stand': {
      const c = freeChair(state, g);
      if (c) sitDown(state, g, c[0], c[1]);
      else if (++g.wait > B.standWait) { state.stats.guests++; leave(state, g, 'happy'); }
      return true;
    }
  }
  return true;
}

export function tick(state) {
  state.t++;
  belt(state);
  shows(state);
  arrive(state);
  admit(state);
  state.guests = state.guests.filter((g) => step(state, g));
  return state;
}

// --- what holds the room back -----------------------------------------------------------------------------
// One answer at a time, the most pressing first, so the player always knows which half of the game to work on.
export function limit(state) {
  const load = state.plates.filter(Boolean).length / RING.length;
  const waiting = state.guests.filter((g) => g.st === 'seat' && g.app > 0 && g.wait > 12).length;
  const front = state.queue[0];
  if (waiting >= 2 && load < 0.3) return { kind: 'kitchen', text: 'The kitchen is the limit: seated guests are waiting for plates' };
  if (front && capacity(state) - inside(state) < front.size) return { kind: 'capacity', text: 'Capacity is the limit: guests are queuing because the room is full' };
  if (front && !pickSeat(state, front.size)) {
    const n = front.size === 1 ? 'a solo guest' : front.size === 2 ? 'a couple' : `a group of ${front.size}`;
    return { kind: 'seats', text: `Seats are the limit: no free seat fits ${n}` };
  }
  if (load > 0.75 && !state.queue.length) return { kind: 'guests', text: 'Guests are the limit: plates go round uneaten. Raise Appeal' };
  return { kind: 'ok', text: 'Everything is keeping up' };
}
