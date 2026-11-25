// Rules for the kitchen line prototype: a belt network of dumb equipment and junctions. Wall inlets are the only
// source of ingredients, so every plate comes off one with a single ingredient on it. Two ingredients meet only
// where a Join merges the plates waiting at its two ends. A plate holds a set of ingredients, not a stack, so
// the order they go on does not matter; the order a process runs in does.
// Nothing in here looks at a plate to decide where it goes. A junction takes turns between its ways out, and
// every machine takes whatever arrives, so a dish ends up where the belt was drawn and nowhere else. No DOM.
import { BALANCE as B } from './balance.js';

export const DIRS = { N: [0, -1], E: [1, 0], S: [0, 1], W: [-1, 0] };
export const OPP = { N: 'S', E: 'W', S: 'N', W: 'E' };
export const key = (x, y) => `${x},${y}`;
export const xy = (k) => k.split(',').map(Number);
export const step = (k, d) => { const [x, y] = xy(k); return key(x + DIRS[d][0], y + DIRS[d][1]); };
// The map is rooms laid out on a grid, each one a square of floor with a wall between it and the next. A tile
// belongs to one room or to no room at all, and the gap between rooms is no room's: belt cannot be laid there,
// so nothing ever crosses from one kitchen to another.
const PITCH = B.map.size + B.map.gap;
export const roomAt = (k) => {
  const [x, y] = xy(k);
  if (x < 0 || y < 0) return -1;
  const cx = Math.floor(x / PITCH), cy = Math.floor(y / PITCH);
  if (x - cx * PITCH >= B.map.size || y - cy * PITCH >= B.map.size) return -1;
  return B.rooms.findIndex((r) => r.col === cx && r.row === cy);
};
export const local = (k) => { const [x, y] = xy(k); return [x % PITCH, y % PITCH]; };
// How a tile is named to the player: the room it is in, then where it is on that room's own floor.
export const label = (k) => { const i = roomAt(k); return i < 0 ? k : `${B.rooms[i].name} ${local(k).join(',')}`; };
export const inRoom = (k) => roomAt(k) >= 0;
export const sameRoom = (a, b) => roomAt(a) >= 0 && roomAt(a) === roomAt(b);
export const dirBetween = (a, b) => Object.keys(DIRS).find((d) => step(a, d) === b);
const fail = (why) => ({ ok: false, why });
const an = (word) => (/^[aeiou]/i.test(word) ? 'an ' : 'a ') + word;
export const exitAt = (k) => B.exits.findIndex((e) => e.cell === k);
export const roomOf = (i) => B.exits[i].room;
// Wall connectors are fixed to the map, and there are two sorts. An inlet is where a line may begin: belt is
// drawn out of it and nowhere else, so a kitchen grows from the wall. An outlet is where a line ends: belt runs
// into it, and it hands finished dishes to its room or throws everything away. Neither can be moved, and an
// outlet never puts anything back on the belt.
export const KINDS = ['out', 'drop']; // an outlet serves its room · clears the line
export const isWall = (c) => c?.exit != null;
export const isIn = (c) => isWall(c) && c.kind === 'in';
export const isDoor = (c) => isWall(c) && c.kind !== 'in'; // an outlet: where a line ends
// A Join is the one machine with a shape of its own: three tiles in a line, taking a plate in at each end and
// handing the merged plate on from the middle. The middle is a source like an inlet; the ends are tails like an
// outlet, and nothing travels on out of them.
export const isJoin = (c) => c?.st === 'join';
// A Splitter is the same three tiles the other way round: belt runs into its middle and it pushes plates out of
// its two ends, strictly one then the other. Both keep their end tiles in `arms`, so which machine an end
// belongs to is read off the machine it points at.
export const isSplit = (c) => c?.st === 'split';
export const isArm = (c) => !!c?.jn;
export const owner = (state, k) => state.cells[k]?.jn || null;
export const isJoinArm = (state, k) => { const o = owner(state, k); return !!o && state.cells[o].st === 'join'; };
export const isSplitEnd = (state, k) => { const o = owner(state, k); return !!o && state.cells[o].st === 'split'; };
const ARMS = { v: ['N', 'S'], h: ['W', 'E'] };
export const armsOf = (k, axis) => ARMS[axis].map((d) => step(k, d));

const RECIPES = Object.keys(B.recipes);
export const ING = Object.keys(B.ingredients);
export const clone = (on) => { const out = {}; for (const i in on) out[i] = [...on[i]]; return out; };
const sameProc = (a, b) => a.length === b.length && a.every((p) => b.includes(p));
// A plate is a dish when it carries exactly the recipe's ingredients, each having had exactly its processes.
const isRecipe = (on, r) => {
  const has = B.recipes[r].has, mine = Object.keys(on);
  return mine.length === Object.keys(has).length && mine.every((i) => has[i] && sameProc(on[i], has[i]));
};
// A plate is still on its way to a recipe while nothing on it is unwanted and nothing has been over-processed.
// A process cannot be undone, so a seared plate can never become the unseared dish.
const viable = (on, r) => {
  const has = B.recipes[r].has;
  return Object.keys(on).every((i) => has[i] && on[i].every((p) => has[i].includes(p)));
};
export const recipeOf = (d) => (d?.on ? RECIPES.find((r) => isRecipe(d.on, r)) || null : null);
export const finished = (d) => !!recipeOf(d);
// Nothing can be made of it any more: no recipe would take what it is carrying.
export const ruined = (d) => !!d?.on && !RECIPES.some((r) => viable(d.on, r));
// Two plates become one: the ingredients of both, and for anything on both, every process either has had.
export function mergeOn(a, b) {
  const out = clone(a);
  for (const i in b) out[i] = out[i] ? [...new Set([...out[i], ...b[i]])] : [...b[i]];
  return out;
}
// The station that puts this ingredient on a plate, and the one that runs this process. A base ingredient has no
// station: it comes off the wall, and a Join is what gets it onto a plate that is already travelling.
export const adderOf = (ing) => Object.keys(B.stations).find((id) => B.stations[id].adds === ing);
export const applierOf = (proc) => Object.keys(B.stations).find((id) => B.stations[id].applies === proc);
export const part = (id) => B.stations[id];
export const price = (id) => part(id).price;
export const unlocked = (state, id) => part(id).from <= state.stage;
// An inlet can be set to any ingredient the kitchen has reached, or to nothing at all. An add-on never appears
// here: a station spoons it on.
export const inletItems = (state) => [null, ...ING.filter((i) => !adderOf(i) && B.ingredients[i].from <= state.stage)];
// A recipe is on the menu once every ingredient in it can be had and every process in it can be run.
export const onMenu = (state, r) => {
  const has = B.recipes[r].has;
  return Object.keys(has).every((i) => {
    const a = adderOf(i);
    return a ? unlocked(state, a) : B.ingredients[i].from <= state.stage;
  }) && [...new Set(Object.values(has).flat())].every((p) => unlocked(state, applierOf(p)));
};

export function createGame() {
  const S = B.start, state = { v: 12, coins: S.coins, tick: 0, stage: 0, served: 0, total: 0, spoiled: 0, done: false,
    wasted: 0, lastWaste: null,
    cells: {}, rooms: B.rooms.map((_, i) => ({ open: i === 0, want: 'any', q: [], cd: 0, empty: 0, served: 0 })), events: [] };
  B.exits.forEach((e, i) => { state.cells[e.cell] = { links: [], outs: [], exit: i, kind: e.kind, hold: 0 }; });
  for (const k in S.inlets || {}) state.cells[k].item = S.inlets[k];
  for (const k in S.joins || {}) fit(state, k, 'join', S.joins[k]); // the shaped machines go down before the belt
  for (const line of S.lines || []) line.forEach((k, i) => i && link(state, line[i - 1], k));
  for (const id in S.stations || {}) fit(state, S.stations[id], id);
  applyStage(state, 0);
  return state;
}

const blank = () => ({ links: [], outs: [] });
// Belt is laid in the direction it is drawn: the link from a to b carries plates that way and no other, so the
// flow is the belt's own, not anything a machine decides.
function link(state, a, b) {
  const d = dirBetween(a, b), A = (state.cells[a] ||= blank()), Z = (state.cells[b] ||= blank());
  A.outs ||= []; Z.outs ||= [];
  if (!A.links.includes(d)) { A.links.push(d); Z.links.push(OPP[d]); }
  if (!A.outs.includes(d)) A.outs.push(d);
  Z.outs = Z.outs.filter((x) => x !== OPP[d]);
}
const bare = (c) => c && !c.links.length && !c.st && c.exit == null && !c.dish && !c.w && !c.jn;
export const flows = (state, k) => state.cells[k]?.outs || [];

function applyStage(state, i) {
  const s = B.stages[i];
  if (s.open != null) state.rooms[s.open].open = true;
  for (const r in s.wants || {}) state.rooms[r].want = s.wants[r];
}

// --- edits -----------------------------------------------------------------------------------------------

// --- what a machine's shape may stand on -------------------------------------------------------------------
// A machine is one anchor tile plus the shape around it. Every test below takes the machine being asked about,
// so a machine turning on the spot or shifting one tile sees its own floor as free rather than as in its way.
const FACES = ['N', 'E', 'S', 'W'];
const mine = (c, self) => c.w === self || c.jn === self;
// Floor a machine's body may stand on: inside the room, with no belt, machine or plate on it.
const canBody = (state, t, self) => {
  if (!inRoom(t)) return false;
  const c = state.cells[t];
  if (!c) return true;
  return mine(c, self) || (!c.links.length && !c.st && c.exit == null && !c.w && !c.jn && !c.dish);
};
// The tile a machine itself stands on: belt is welcome, another machine and the wall are not.
const canSit = (state, t, self) => {
  if (!inRoom(t)) return false;
  const c = state.cells[t];
  if (!c) return true;
  if (c.st && t !== self) return false;
  return mine(c, self) || (c.exit == null && !c.w && !c.jn);
};
// A Join's end is a belt tile, so belt may run into it. What it may not have is belt running out of it.
const canArm = (state, t, self) => {
  if (!inRoom(t)) return false;
  const c = state.cells[t];
  if (!c) return true;
  return c.jn === self || (!c.outs.length && !c.st && c.exit == null && !c.w && !c.jn);
};
// A Join hands its plate on from the middle, so belt may run out of the middle but never into it.
const canMid = (state, t, self) => {
  if (!canSit(state, t, self)) return false;
  const c = state.cells[t];
  return !c || c.links.every((d) => c.outs.includes(d));
};
// A Splitter is fed at its middle, so belt may run into the middle but never out of it.
const canSink = (state, t, self) => {
  if (!canSit(state, t, self)) return false;
  const c = state.cells[t];
  return !c || !c.outs.length;
};
// A Splitter's end is where a line begins, so belt may run out of it but never into it.
const canHead = (state, t, self) => {
  if (!inRoom(t)) return false;
  const c = state.cells[t];
  if (!c) return true;
  return c.jn === self || (c.links.every((d) => c.outs.includes(d)) && !c.st && c.exit == null && !c.w && !c.jn);
};
// Which links of a tile carry plates in rather than out.
const intoOf = (c) => (c ? c.links.filter((d) => !c.outs.includes(d)) : []);

// The ways a machine can be turned. A Join lies along one of two axes; anything with a body cycles which side of
// itself that body stands on; a one-tile machine has only the one way to sit.
export const faces = (id) => (part(id).span ? ['v', 'h'] : part(id).block || (part(id).size || 1) > 1 ? FACES : [null]);
// The tiles a machine would cover at this tile, facing this way, or null if they are not all free. The body is a
// block: for a machine two tiles across that is the one tile on the side it faces, and for a wider one the next
// tiles round from there, so what it covers is always one connected lump.
function shapeAt(state, k, id, face, self = null) {
  const P = part(id);
  if (P.span) {
    const arms = armsOf(k, face);
    if (!arms.every((t) => sameRoom(k, t))) return null; // three tiles in a line, all on one room's floor
    if (P.out) {
      if (!canSink(state, k, self)) return null;
      // a Splitter may not be fed from one of its own ends, which would feed it back into itself
      if (arms.some((t) => intoOf(state.cells[k]).includes(dirBetween(k, t)))) return null;
      return arms.every((t) => canHead(state, t, self)) ? { axis: face, arms } : null;
    }
    if (!canMid(state, k, self)) return null;
    const out = state.cells[k]?.outs || [];
    // a Join may not hand its plate to one of its own ends, which would feed it back into itself
    if (arms.some((t) => out.includes(dirBetween(k, t)))) return null;
    return arms.every((t) => canArm(state, t, self)) ? { axis: face, arms } : null;
  }
  if (!canSit(state, k, self)) return null;
  // A 2x2 machine stands on a corner of its own block, so the only two faces it leaves free are at right
  // angles to each other: the belt has to turn through it.
  if (P.block === 2) {
    const i = FACES.indexOf(face), a = step(k, FACES[i]), b = step(k, FACES[(i + 1) % 4]);
    const work = [a, b, step(a, FACES[(i + 1) % 4])];
    return work.every((t) => canBody(state, t, self)) ? { face, work } : null;
  }
  const work = [];
  for (let i = 0; i < (P.size || 1) - 1; i++) {
    const t = step(k, FACES[(FACES.indexOf(face) + i) % 4]);
    if (!canBody(state, t, self)) return null;
    work.push(t);
  }
  return { face, work };
}
// Writes the machine onto the board, and lifts it off again. Neither touches belt or plates: a tile a machine
// stops covering keeps whatever was drawn on it, which is why turning one leaves loose ends to tidy up.
function install(state, k, id, sh) {
  const c = (state.cells[k] ||= blank());
  c.st = id; c.hold = 0;
  if (sh.arms) { c.axis = sh.axis; c.arms = sh.arms; for (const t of sh.arms) (state.cells[t] ||= blank()).jn = k; }
  else { c.face = sh.face; c.work = sh.work; for (const t of sh.work) (state.cells[t] ||= blank()).w = k; }
  return { ok: true };
}
function uninstall(state, k) {
  const c = state.cells[k];
  for (const t of c.work || []) { const wc = state.cells[t]; if (wc) { delete wc.w; if (bare(wc)) delete state.cells[t]; } }
  for (const t of c.arms || []) { const ac = state.cells[t]; if (ac) { delete ac.jn; if (bare(ac)) delete state.cells[t]; } }
  delete c.work; delete c.arms; delete c.axis; delete c.face;
}
const noRoom = (id) => (part(id).span
  ? `${part(id).name} covers three tiles in a line: put its middle where three tiles sit free side by side.`
  : part(id).block === 2
    ? `${part(id).name} covers a 2x2 block: it needs three free tiles of floor beside it.`
    : `${part(id).name} covers ${part(id).size} tiles: it needs ${part(id).size > 2 ? `${part(id).size - 1} free tiles` : 'one free tile'} of floor beside it.`);

// A line has to be anchored: belt grows out of an inlet in the wall, out of the middle of a Join, or on from
// belt already laid. Nothing can be started in the middle of the floor.
const START = 'Belt starts at an inlet in the wall, at the middle of a Join, at an end of a Splitter, or on from belt you have already laid.';
const anchored = (state, k) => isIn(state.cells[k]) || isJoin(state.cells[k]) || isSplitEnd(state, k) || !!state.cells[k]?.links.length;

// Belt joins any two neighbouring tiles. A tile with three or four links is a junction; dishes take turns there.
export function draw(state, a, b) {
  const d = dirBetween(a, b);
  if (!d || !inRoom(a)) return fail('');
  if (!sameRoom(a, b)) return fail('Each room is a kitchen of its own. Belt cannot cross the wall between two rooms.');
  if (isIn(state.cells[b])) return fail('An inlet feeds the belt. Draw out of it, not into it.');
  if (isDoor(state.cells[a])) return fail('An outlet is where a line ends. Belt runs into it, not out of it.');
  if (state.cells[a]?.st === 'bin') return fail('A bin is the end of a line. Belt runs into it, not out of it.');
  if (isJoin(state.cells[b])) return fail('A Join hands the merged plate on. Draw belt out of its middle, not into it.');
  if (isJoinArm(state, a)) return fail('A Join takes plates in at its ends. Draw belt into an end, not out of one.');
  if (isSplit(state.cells[a])) return fail('A Splitter pushes plates out of its ends. Draw belt into its middle, not out of it.');
  if (isSplitEnd(state, b)) return fail('A Splitter hands the plate on from its ends. Draw belt out of an end, not into one.');
  for (const k of [a, b]) if (state.cells[k]?.w) return fail(TAKEN);
  if (!anchored(state, a) && !anchored(state, b)) return fail(START);
  link(state, a, b);
  return { ok: true };
}

export function unlink(state, a, b) {
  const d = dirBetween(a, b);
  if (!state.cells[a]?.links.includes(d)) return;
  for (const [k, dir] of [[a, d], [b, OPP[d]]]) {
    const c = state.cells[k];
    c.links = c.links.filter((x) => x !== dir);
    c.outs = c.outs.filter((x) => x !== dir);
    if (!c.links.length) c.dish = null;
    if (bare(c)) delete state.cells[k];
  }
}

// Erasing lifts the machine first, refunded in full, and only then the belt. Erasing any tile of a machine lifts
// the whole machine.
export function erase(state, k) {
  const c = state.cells[k];
  if (!c) return fail('');
  if (c.w) return erase(state, c.w);
  if (c.jn) return erase(state, c.jn);
  if (c.st) {
    state.coins += price(c.st);
    uninstall(state, k);
    delete c.st; delete c.hold;
  } else if (c.links.length) {
    for (const d of [...c.links]) unlink(state, k, step(k, d));
    c.dish = null;
  } else return fail('');
  if (bare(state.cells[k])) delete state.cells[k];
  return { ok: true };
}

// Puts the part down the first way round that fits. Used by the starting kitchen, which pays nothing.
function fit(state, k, id, want) {
  for (const face of want ? [want, ...faces(id).filter((f) => f !== want)] : faces(id)) {
    const sh = shapeAt(state, k, id, face);
    if (sh) return { ...install(state, k, id, sh), face };
  }
  return fail(noRoom(id));
}

// --- the selected machine --------------------------------------------------------------------------------

// Which machine a tile belongs to, whether it is the tile the machine stands on, a tile of its body, or an end
// of a Join. This is what a tap selects.
export const machineAt = (state, k) => {
  const c = state.cells[k];
  return c ? c.w || c.jn || (c.st ? k : null) : null;
};
export const facing = (state, k) => state.cells[k]?.axis ?? state.cells[k]?.face ?? null;
export const canTurn = (state, k) => !!state.cells[k]?.st && faces(state.cells[k].st).length > 1;
// Turns a machine where it stands, to the next way round that fits. Belt is left exactly where it was drawn, so
// turning one off its line leaves the loose ends behind for the player to redraw.
export function turn(state, k) {
  const c = state.cells[k];
  if (!c?.st) return fail('');
  const list = faces(c.st);
  if (list.length < 2) return fail(`${part(c.st).name} covers one tile. There is nothing to turn.`);
  const now = facing(state, k);
  for (let i = 1; i <= list.length; i++) {
    const face = list[(list.indexOf(now) + i) % list.length];
    if (face === now) break;
    const sh = shapeAt(state, k, c.st, face, k);
    if (!sh) continue;
    uninstall(state, k);
    install(state, k, c.st, sh);
    return { ok: true, face };
  }
  return fail(`There is no room to turn ${part(c.st).name} round here. Clear a tile beside it first.`);
}
// The tiles a machine would cover if it moved to this tile, or null if it will not go there. The ghost under a
// finger dragging a machine about is drawn from this.
export function fitsAt(state, k, to) {
  const c = state.cells[k];
  if (!c?.st || !inRoom(to)) return null;
  const was = facing(state, k);
  for (const face of [was, ...faces(c.st).filter((f) => f !== was)]) {
    const sh = shapeAt(state, to, c.st, face, k);
    if (sh) return [to, ...(sh.arms || sh.work)];
  }
  return null;
}
// Moves a machine to another tile, keeping the way it is facing where that still fits and turning it where it
// does not. The belt stays where it was drawn, and so does any plate the machine was holding.
export function moveTo(state, k, to) {
  const c = state.cells[k];
  if (!c?.st) return fail('');
  if (to === k) return { ok: true, k, face: facing(state, k) };
  if (!inRoom(to)) return fail('');
  const id = c.st, was = facing(state, k);
  for (const face of [was, ...faces(id).filter((f) => f !== was)]) {
    const sh = shapeAt(state, to, id, face, k);
    if (!sh) continue;
    uninstall(state, k);
    delete c.st; delete c.hold;
    if (!c.links.length) c.dish = null; // a plate it was holding has no belt left to sit on
    if (bare(c)) delete state.cells[k];
    install(state, to, id, sh);
    return { ok: true, k: to, face, turned: face !== was };
  }
  return fail(noRoom(id));
}

// A machine covers a block of floor, so the only thing that keeps two of them apart is that their blocks cannot
// overlap: what you see on the floor is the whole of the rule.
const TAKEN = 'That tile is part of the machine beside it.';

// A machine sits on a belt tile, one to a tile, and covers the floor its body needs.
export function place(state, k, id) {
  if (!inRoom(k)) return fail('');
  if (!unlocked(state, id)) return fail('That is not unlocked yet.');
  const c = state.cells[k];
  if (c?.exit != null) return fail('The wall connector keeps its tile.');
  if (c?.w || c?.jn) return fail(TAKEN);
  if (c?.st) return fail('One machine to a tile. Erase this one first.');
  const cost = price(id);
  if (state.coins < cost) return fail(`That costs ${cost}.`);
  const res = fit(state, k, id);
  if (!res.ok) return res;
  state.coins -= cost;
  return { ok: true };
}

// --- the belt network ------------------------------------------------------------------------------------

// A machine holds the dish it is working on, so whatever is behind it waits: that is the back pressure.
const held = (c) => !!(c.st && c.hold > 0);
// What this machine would make of the dish. An add-on station puts its ingredient on; a process station marks
// everything already on the plate, which is why searing early and searing late are different dishes. A machine
// with nothing to do to a plate leaves it alone, and so never takes hold of it.
export function after(st, d) {
  const S = B.stations[st];
  if (!S) return d;
  if (S.adds) {
    if (d.on[S.adds]) return d;
    return { ...d, on: { ...clone(d.on), [S.adds]: [] } };
  }
  if (S.applies) {
    const on = clone(d.on);
    let any = false;
    for (const i in on) if (!on[i].includes(S.applies)) { on[i].push(S.applies); any = true; }
    return any ? { ...d, on } : d;
  }
  return d;
}
export const changes = (st, d) => after(st, d) !== d;

// Whether the dish on k may move onto t right now. The only thing that ever turns a plate away is that there is
// no room for it: every machine takes whatever arrives, and so does a Join.
function canEnter(state, k, t, d) {
  const c = state.cells[t];
  if (!c || c.w) return false;
  if (c.exit != null) {
    if (isIn(c)) return false; // an inlet is a source, never a destination
    const r = state.rooms[roomOf(c.exit)];
    if (!r.open) return false;
    // Only a finished dish queues up for the guests, so only that waits for room. Anything else is cleared away,
    // which is what keeps a half-built line draining instead of locking solid.
    return c.kind === 'drop' || !finished(d) || r.q.length < B.queue;
  }
  return true;
}

// Where the dish on tile k goes next. A junction takes turns between its ways out and that is the whole of it:
// it does not look at the plate, and it does not look down the belt to see what is there. A free tile beats an
// occupied one, so a dish does not queue behind another when a lane is open. Where a dish ends up is the shape
// of the belt, so a branch drawn to nowhere will take its share of the plates and keep them.
function pick(state, k, d) {
  const c = state.cells[k], turn = c.turn || 0;
  // A Splitter is the one thing that does not take the open lane: it alternates strictly, so each end gets
  // exactly half. If the end whose turn it is has no room, the plate waits for it.
  if (isSplit(c)) {
    const t = c.arms[turn % c.arms.length];
    return canEnter(state, k, t, d) ? t : undefined;
  }
  const list = c.outs;
  let best = null;
  for (let i = 0; i < list.length; i++) {
    const out = list[(turn + i) % list.length], t = step(k, out);
    if (!canEnter(state, k, t, d)) continue;
    const score = state.cells[t].dish ? 0 : 1;
    if (!best || score > best.score) best = { t, score };
  }
  return best?.t;
}

function hop(state, k, t) {
  const from = state.cells[k], d = from.dish;
  from.dish = null;
  from.turn = (from.turn || 0) + 1;
  const c = state.cells[t];
  if (c.exit != null) {
    const room = roomOf(c.exit), r = state.rooms[room];
    if (c.kind === 'out' && finished(d)) {
      r.q.push({ on: clone(d.on) });
      state.events.push({ type: 'exit', room, k: t });
    } else {
      // Served unfinished, the plate comes back round in the wash; dropped, someone has to pick it up.
      state.wasted++;
      state.lastWaste = { k: t, add: needs(d, r.want), tick: state.tick };
      state.events.push({ type: 'waste', k: t, kind: c.kind, room });
    }
    return;
  }
  c.dish = { ...d, on: clone(d.on), worked: false, from: OPP[dirBetween(k, t)], moved: true, pk: k };
}

// Dishes move one tile a tick. Repeated passes let a queue shuffle forward behind whoever moved first. A plate
// that has reached the end of a Join stays where it is until the Join has both of them.
const parked = (state, c, k) => isJoinArm(state, k);
function advance(state) {
  const cells = state.cells;
  for (const k in cells) if (cells[k].dish) { cells[k].dish.moved = false; cells[k].dish.pk = k; }
  for (let pass = 0; pass < B.grid.w * B.grid.h; pass++) {
    let moved = false;
    for (const k in cells) {
      const d = cells[k].dish;
      if (!d || d.moved || held(cells[k])) continue;
      if (parked(state, cells[k], k)) { if (!pass) d.jam = (d.jam || 0) + 1; continue; }
      const t = pick(state, k, d);
      d.jam = t ? 0 : (d.jam || 0) + 1;
      if (!t || cells[t].dish) continue;
      hop(state, k, t); moved = true;
    }
    if (!moved) break;
  }
  rotate(state);
}

// A belt packed end to end has no free tile to move into, but a full ring should still turn. Any closed chain of
// dishes that all want the tile in front of them moves together.
function rotate(state) {
  const cells = state.cells, want = {}, seen = new Set();
  for (const k in cells) {
    const d = cells[k].dish;
    if (!d || d.moved || held(cells[k]) || parked(state, cells[k], k)) continue;
    const t = pick(state, k, d);
    if (t && cells[t].dish && !held(cells[t]) && !parked(state, cells[t], t)) want[k] = t;
  }
  for (const start in want) {
    if (seen.has(start)) continue;
    const path = [], at = {};
    let k = start;
    while (k && want[k] && at[k] === undefined) { at[k] = path.length; path.push(k); k = want[k]; }
    if (k && at[k] !== undefined) {
      const ring = path.slice(at[k]), dishes = ring.map((q) => cells[q].dish);
      ring.forEach((q, i) => {
        const n = ring.length, src = ring[(i + n - 1) % n];
        cells[q].dish = { ...dishes[(i + n - 1) % n], from: OPP[dirBetween(src, q)], moved: true, pk: src };
        cells[q].turn = (cells[q].turn || 0) + 1;
      });
    }
    for (const q of path) seen.add(q);
  }
}

// A Join waits for a plate at each end, takes the usual time over the two of them and hands one plate on from
// the middle. It looks at neither of them: whatever they are carrying ends up on one plate, and a set no recipe
// allows is ruined like any other.
function joinWork(state, k, c) {
  const [a, b] = c.arms, A = state.cells[a], Z = state.cells[b];
  if (c.hold > 0) {
    if (--c.hold > 0) return;
    if (c.dish || !A?.dish || !Z?.dish) return;
    const on = mergeOn(A.dish.on, Z.dish.on);
    A.dish = null; Z.dish = null;
    c.dish = { on, worked: true, from: null, moved: true, pk: k };
    if (ruined(c.dish)) { c.dish.spoiled = true; state.spoiled++; state.events.push({ type: 'ruin', k }); }
    state.events.push({ type: 'join', k });
    return;
  }
  if (!c.dish && A?.dish && Z?.dish) c.hold = B.speed;
}

// Every machine takes the same time and holds its dish while it works. None of them look at what they are
// given: the ingredient goes on whatever arrives, and the wrong order ruins the plate.
function stations(state) {
  for (const k in state.cells) {
    const c = state.cells[k];
    if (!c.st) continue;
    if (c.st === 'join') { joinWork(state, k, c); continue; }
    if (c.hold > 0) {
      if (--c.hold > 0) continue;
      if (c.st === 'bin') { if (c.dish) { c.dish = null; state.events.push({ type: 'bin', k }); } continue; }
      if (c.dish && changes(c.st, c.dish)) {
        c.dish.on = after(c.st, c.dish).on;
        c.dish.worked = true; // this machine has had its turn, and gets no second go while the plate waits here
        if (ruined(c.dish) && !c.dish.spoiled) { c.dish.spoiled = true; state.spoiled++; state.events.push({ type: 'ruin', k }); }
      }
      continue;
    }
    // A ruined plate is rubbish: nothing adds to it, and only the bin will take it. A machine with nothing to do
    // to this plate lets it straight through.
    if (c.dish && (c.st === 'bin' || (!c.dish.worked && !ruined(c.dish) && changes(c.st, c.dish)))) c.hold = B.speed;
  }
}

// Wall inlets are the only thing that puts a plate on a belt, and each delivers the one ingredient it is set
// to, already plated. An inlet has no direction of its own: the plate leaves whichever way the belt out of it
// runs.
function inlets(state) {
  for (const k in state.cells) {
    const c = state.cells[k];
    if (!isIn(c) || !c.item) continue;
    if (c.hold > 0) { c.hold--; continue; }
    if (c.dish || !c.links.length) continue;
    c.dish = { on: { [c.item]: [] }, worked: true, from: null, moved: true, pk: k };
    c.hold = B.feed;
  }
}
// Tapping a loop turns the belt round, and the plates on it with it. A belt joined to the wall or to a Join
// takes its direction from there, so there is nothing to turn.
export function reverse(state, k) {
  const c = state.cells[k];
  if (!c?.links.length) return fail('');
  const mine = [...reach(state, k)];
  if (mine.some((t) => state.cells[t].exit != null)) return fail('This belt runs from the wall. Erase it and draw it the other way.');
  if (mine.some((t) => isArm(state.cells[t]) || isJoin(state.cells[t]) || isSplit(state.cells[t]))) return fail('This belt runs through a Join or a Splitter. Erase it and draw it the other way.');
  for (const t of mine) {
    const cell = state.cells[t];
    cell.outs = cell.links.filter((d) => !cell.outs.includes(d) && state.cells[step(t, d)]);
    if (cell.dish?.from) cell.dish.from = OPP[cell.dish.from];
  }
  return { ok: true };
}
// Every tile joined to k by belt, whichever way each piece of it runs.
function reach(state, k) {
  const seen = new Set([k]), queue = [k];
  while (queue.length) {
    const t = queue.shift();
    for (const dir of state.cells[t].links) { const n = step(t, dir); if (state.cells[n] && !seen.has(n)) { seen.add(n); queue.push(n); } }
  }
  return seen;
}

// An outlet serves its room or clears the line. Tapping it swaps which. Tapping an inlet walks it through the
// ingredients the kitchen has reached, and through delivering nothing at all.
export function cycleExit(state, k, by = 1) {
  const c = state.cells[k];
  if (c?.exit == null) return fail('');
  if (isIn(c)) {
    const list = inletItems(state);
    c.item = list[(list.indexOf(c.item ?? null) + by + list.length) % list.length];
    c.hold = 0;
    return { ok: true, item: c.item };
  }
  c.kind = KINDS[(KINDS.indexOf(c.kind) + by + KINDS.length) % KINDS.length];
  return { ok: true, kind: c.kind };
}

// Where each stretch of belt begins and ends. A line runs from a head — an inlet in the wall, the middle of a
// Join, an end of a Splitter — to a tail: an outlet in the wall, a Bin, the end of a Join, a Splitter's middle.
// A loop has neither and needs neither.
// Anything else is a loose end, and the plates stack up against it.
export function ends(state) {
  const out = [];
  for (const k in state.cells) {
    const c = state.cells[k];
    if (c.links.length !== 1) continue;
    const head = isIn(c) || isJoin(c) || isSplitEnd(state, k);
    const tail = isDoor(c) || c.st === 'bin' || isSplit(c) || isJoinArm(state, k);
    out.push({ k, type: head ? 'head' : tail ? 'tail' : 'loose' });
  }
  return out;
}
export const loose = (state) => ends(state).filter((e) => e.type === 'loose').map((e) => e.k);

// The next thing a plate is waiting for: the machine that would take it further along some recipe, or the Join
// that would bring it the ingredient it is missing. An ingredient comes before a process, since a process marks
// whatever is on the plate at the time.
export function needs(d, want) {
  const fits = (x) => !!B.recipes[x] && viable(d.on, x) && !isRecipe(d.on, x);
  const r = (want && fits(want) && want) || RECIPES.find(fits);
  if (!r) return null;
  const has = B.recipes[r].has;
  for (const i in has) if (!d.on[i]) return adderOf(i) || 'join';
  for (const i in has) for (const pr of has[i]) if (!d.on[i].includes(pr)) {
    const st = applierOf(pr);
    // Running it on this plate would mark everything already on it, and this recipe does not want that. The
    // plate was brought together before the process it needed, and a process can never be taken off again.
    return ruined(after(st, d)) ? 'order' : st;
  }
  return null;
}
// Plates being cleared at a doorway for want of a machine, while it is still happening.
export function wasting(state) {
  const w = state.lastWaste;
  return w && w.add && state.tick - w.tick < 60 ? w : null;
}
// A plate stopped on a belt where nothing will ever touch it: the line is missing the machine it names. A plate
// waiting at the end of a Join is not stopped, it is early; lonely() is what reports one of those.
export function stuck(state) {
  for (const k of jams(state)) {
    const d = state.cells[k].dish;
    if (finished(d) || ruined(d)) continue;
    const mine = reach(state, k);
    if ([...mine].some((t) => isJoinArm(state, t) || (state.cells[t].st && changes(state.cells[t].st, d) && !ruined(after(state.cells[t].st, d))))) continue;
    const add = needs(d);
    if (add) return { k, add };
  }
  return null;
}

function dine(state) {
  state.rooms.forEach((r, i) => {
    if (!r.open) return;
    if (!r.q.length) { r.empty++; return; }
    r.empty = 0;
    if (r.cd > 0) { r.cd--; return; }
    const d = r.q.shift(), id = recipeOf(d), value = Math.round(B.recipes[id].value * (r.want === id ? B.wantBonus : 1));
    state.coins += value; state.served++; state.total++; r.served++;
    r.cd = Math.max(1, Math.round(B.eat / B.rooms[i].seats));
    state.events.push({ type: 'eat', room: i, value, recipe: id });
  });
}

// Tiles holding a dish that has had nowhere to go for a while, so the hint can point at them. A dish waiting on a
// filter for a room to catch up, or at the end of a Join for its partner, is doing its job, not jammed.
export const nextTile = (state, k) => (state.cells[k]?.dish ? pick(state, k, state.cells[k].dish) : null);
export const jams = (state) => Object.keys(state.cells).filter((k) => state.cells[k].dish?.jam > 40 && !isJoinArm(state, k));
// A plate that has waited a long time at one end of a Join, because nothing is reaching the other end.
export function lonely(state) {
  for (const k in state.cells) {
    const c = state.cells[k];
    if (!isJoinArm(state, k) || !(c.dish?.jam > 120)) continue;
    const other = state.cells[c.jn].arms.find((t) => t !== k);
    if (!state.cells[other]?.dish) return { k, other };
  }
  return null;
}
// Ruined plates going round the belt. Only a Bin takes one off, and only because the belt was drawn into one.
export const spoiled = (state) => Object.keys(state.cells).filter((k) => ruined(state.cells[k].dish));

export function progress(state) {
  const need = B.stages[state.stage].need;
  return { need, served: state.served, ready: state.served >= need };
}

// What one room's own line can make at best against what its seats can eat. Nothing is shared between rooms:
// a room's inlets, Joins and stations are the only ones that feed it, so each is judged on its own.
// A recipe costs the room one inlet stream for each ingredient off the wall, one Join for each merge those
// take, and one machine for every add-on and process on top.
export function capacity(state) {
  const rooms = state.rooms.map((r, i) => {
    if (!r.open) return null;
    const have = {}, streams = {};
    let fed = 0;
    for (const k in state.cells) {
      if (roomAt(k) !== i) continue;
      const c = state.cells[k];
      if (c.st) have[c.st] = (have[c.st] || 0) + 1;
      if (isIn(c) && c.item && c.links.length) { fed++; streams[c.item] = (streams[c.item] || 0) + 1; }
    }
    const rate = (id) => (have[id] || 0) / B.speed; // dishes a tick this many of that machine can handle
    const has = B.recipes[r.want]?.has;
    const wall = has ? Object.keys(has).filter((x) => !adderOf(x)) : null;
    const parts = has
      ? [...Object.keys(has).map(adderOf).filter(Boolean), ...[...new Set(Object.values(has).flat())].map(applierOf)]
      : [];
    // An inlet delivers one whole stream of the one ingredient it is set to, and a dish needs one of each, so
    // what the room can make is the scarcest ingredient on the plate. A Splitter divides a stream; it never
    // makes more of it, so splitting never raises this.
    let made, limit = null;
    if (wall) {
      made = Infinity;
      for (const ing of wall) { const q = (streams[ing] || 0) / B.feed; if (q < made) { made = q; limit = null; } }
    } else made = fed / B.feed / 2; // with no dish in mind, two ingredients and one Join is the cheapest dish
    if (wall && wall.length > 1) { const j = rate('join') / (wall.length - 1); if (j < made) { made = j; limit = 'join'; } }
    for (const id of parts) { const q = rate(id); if (q < made) { made = q; limit = id; } }
    const seats = B.rooms[i].seats, eats = seats / B.eat;
    return { seats, eats, made, limit, short: eats > made + 1e-9,
      // Named so a hint can say what to add without knowing whether the wall or a machine is the bottleneck.
      limitText: limit ? `add ${an(B.stations[limit].name)} station in this room` : 'set another inlet in this room to deliver an ingredient' };
  });
  return { rooms, short: rooms.some((x) => x?.short) };
}

// Ingredients a dish needs that no inlet is delivering. Nothing can be bought to fix this: an inlet has to be
// set to them.
export function unfed(state, want, room) {
  if (!B.recipes[want]) return [];
  const bases = new Set(Object.keys(state.cells).filter((k) => room == null || roomAt(k) === room)
    .map((k) => state.cells[k]).filter((c) => isIn(c) && c.item && c.links.length).map((c) => c.item));
  return Object.keys(B.recipes[want].has).filter((i) => !adderOf(i) && !bases.has(i));
}
// Equipment the kitchen has not got that a dish cannot be made without.
export function missing(state, want, room) {
  if (want === 'ruined') return [];
  const have = new Set(Object.keys(state.cells).filter((k) => room == null || roomAt(k) === room)
    .map((k) => state.cells[k]).filter((c) => c.st).map((c) => c.st));
  const r = want === 'any' ? RECIPES.find((x) => onMenu(state, x)) : want;
  if (!r) return [];
  const has = B.recipes[r].has, need = [];
  for (const i in has) { const a = adderOf(i); if (a) need.push(a); }
  for (const pr of new Set(Object.values(has).flat())) need.push(applierOf(pr));
  // Two things off the wall have to be brought together, and a Join is the only thing that does that.
  if (Object.keys(has).filter((i) => !adderOf(i)).length > 1) need.push('join');
  return [...new Set(need)].filter((id) => id && !have.has(id));
}

export function tick(state) {
  state.tick++;
  advance(state);
  inlets(state);
  stations(state);
  dine(state);
  if (progress(state).ready) {
    if (state.stage + 1 < B.stages.length) {
      state.stage++; state.served = 0;
      applyStage(state, state.stage);
      state.events.push({ type: 'stage', stage: state.stage });
    } else if (!state.done) { state.done = true; state.events.push({ type: 'done' }); }
  }
}
