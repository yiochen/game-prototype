// Canvas UI for the kitchen line prototype. Rules are in engine.js, tuning in balance.js.
// The map is several rooms, each a square floor of its own. One room is on the board at a time and the chips
// above it are the switch: a room is its own kitchen, so there is nothing to see across the wall anyway.
import { BALANCE as B } from './balance.js';
import * as E from './engine.js';

const $ = (s) => document.querySelector(s);
const SAVE = 'sushi-loop-kitchen-line-v12';
const fresh = new URLSearchParams(location.search).has('fresh'); // start over without touching the save
const canvas = $('#board'), ctx = canvas.getContext('2d');
const INK = '#2a2f45', GOLD = '#e0a12f', RED = '#d0443a';
const N = B.map.size, PITCH = B.map.size + B.map.gap;

let state = load() || E.createGame();
let tool = 'belt', stroke = null, warn = null, tip = null, effects = [], sel = null, view = 0;
let lastTick = performance.now(), W = 0, H = 0, dpr = 1, G = { s: 40, ox: 0, oy: 0 };

function load() {
  if (fresh) return null;
  try {
    const s = JSON.parse(localStorage.getItem(SAVE));
    if (s?.v !== 12) return null;
    s.events = [];
    return s;
  } catch { return null; }
}
function save() { if (!fresh) try { localStorage.setItem(SAVE, JSON.stringify({ ...state, events: [] })); } catch { /* storage may be off */ } }

// --- geometry --------------------------------------------------------------------------------------------
// The board shows the room being worked on, at its own size, so a tile is as big as a finger whatever the map
// grows to. Tiles are kept in the map's coordinates throughout; only the drawing subtracts the room's corner.
const origin = () => [B.rooms[view].col * PITCH, B.rooms[view].row * PITCH];
function resize() {
  const r = canvas.getBoundingClientRect();
  dpr = Math.min(3, window.devicePixelRatio || 1); W = r.width; H = r.height;
  canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
  const s = Math.floor(Math.min(W / (N + 0.5), H / (N + 0.6)));
  G = { s, ox: (W - s * N) / 2, oy: (H - s * N) / 2 };
}
new ResizeObserver(resize).observe(canvas); resize();
const centre = (k) => { const [ox, oy] = origin(), [x, y] = E.xy(k); return [G.ox + (x - ox + 0.5) * G.s, G.oy + (y - oy + 0.5) * G.s]; };
const lerp = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
// A plate always sits in the middle of the one tile it takes up, machine or no machine.
const spot = (k) => centre(k);
const here = (k) => E.roomAt(k) === view; // on the floor of the room being shown
function cellAt(e) {
  const r = canvas.getBoundingClientRect(), [ox, oy] = origin();
  const x = Math.floor((e.clientX - r.left - G.ox) / G.s), y = Math.floor((e.clientY - r.top - G.oy) / G.s);
  return x >= 0 && y >= 0 && x < N && y < N ? E.key(x + ox, y + oy) : null;
}

// --- input -----------------------------------------------------------------------------------------------
function say(res) { if (!res.ok && res.why) warn = { text: res.why, until: performance.now() + 2600 }; return res.ok; }

canvas.addEventListener('pointerdown', (e) => {
  const cell = cellAt(e);
  if (!cell) return;
  canvas.setPointerCapture(e.pointerId);
  if (tool === 'belt') {
    // dragging the machine that is already selected moves it; anything else draws belt as it always did
    const m = E.machineAt(state, cell);
    stroke = m && m === sel ? { move: m, last: cell, tap: cell } : { last: cell, steps: [], tap: cell };
  } else if (tool === 'erase') { say(E.erase(state, cell)); sel = null; stroke = { erase: true, last: cell }; }
  else if (say(E.place(state, cell, tool))) { tip = null; sel = cell; }
  save();
});
canvas.addEventListener('pointermove', (e) => {
  if (!stroke) return;
  const target = cellAt(e);
  if (stroke.move) { if (target && target !== stroke.last) stroke.tap = null; stroke.to = target; return; }
  if (!target || target === stroke.last) return;
  stroke.tap = null;
  if (stroke.erase) { E.erase(state, target); stroke.last = target; return; }
  for (let guard = 0; stroke.last !== target && guard < 20; guard++) {
    const [x, y] = E.xy(stroke.last), [tx, ty] = E.xy(target), dx = tx - x, dy = ty - y;
    const next = Math.abs(dx) >= Math.abs(dy) ? E.key(x + Math.sign(dx), y) : E.key(x, y + Math.sign(dy));
    const back = stroke.steps.at(-1);
    if (back && back.a === next) { E.unlink(state, back.a, back.b); stroke.steps.pop(); } // dragging back undoes
    else { if (!say(E.draw(state, stroke.last, next))) break; stroke.steps.push({ a: stroke.last, b: next }); }
    stroke.last = next;
  }
});
// Saying what just happened also retires the dock's tip: the player has moved on from reading about a part.
const calm = (text) => { tip = null; warn = { text, until: performance.now() + 3000, calm: true }; };
const WAY = { v: 'up and down', h: 'across', N: 'north', E: 'east', S: 'south', W: 'west' };
// A tap, not a drag. On a machine it selects it, ready for the Turn button or a drag to somewhere else; on an
// inlet it steps to the next ingredient; on an outlet it swaps serving for clearing; on a loop of belt it turns
// the loop round.
function tapped(k) {
  const m = E.machineAt(state, k);
  if (m) {
    sel = sel === m ? null : m;
    if (!sel) { calm('Nothing selected now.'); return; }
    const name = E.part(state.cells[m].st).name;
    calm(E.canTurn(state, m)
      ? `${name} selected. Tap Turn to turn it round, or drag it to move it. The belt stays where you drew it.`
      : `${name} selected. Drag it to move it. It covers one tile, so there is nothing to turn.`);
    return;
  }
  sel = null;
  const c = state.cells[k];
  if (!c) return;
  if (c.exit != null) {
    const r = E.cycleExit(state, k);
    if (!r.ok) { calm(r.why); return; }
    if (E.isIn(c)) {
      calm(r.item
        ? `This inlet delivers a plate of ${B.ingredients[r.item].name.toLowerCase()} now. Tap it again for the next ingredient.`
        : 'This inlet delivers nothing now. Tap it again to choose an ingredient.');
      return;
    }
    const name = B.rooms[E.roomOf(c.exit)].name;
    calm(r.kind === 'out'
      ? `Door ${name} serves the room now. Finished dishes go to the guests; anything else is cleared away.`
      : `Door ${name} clears the line now: everything that reaches it is thrown out.`);
    return;
  }
  if (c.links.length && say(E.reverse(state, k))) calm('Turned that belt round.');
}
function endStroke() {
  if (!stroke) return;
  if (stroke.move && stroke.to && stroke.to !== stroke.move) {
    const r = E.moveTo(state, stroke.move, stroke.to);
    if (r.ok) { sel = r.k; calm(r.turned ? 'Moved, and turned to fit. The belt stays where you drew it.' : 'Moved. The belt stays where you drew it.'); }
    else say(r);
  } else if (stroke.tap) tapped(stroke.tap);
  stroke = null; save();
}
canvas.addEventListener('pointerup', endStroke);
canvas.addEventListener('pointercancel', endStroke);

function setTool(t) {
  tool = t; sel = null;
  for (const b of document.querySelectorAll('[data-tool]')) b.setAttribute('aria-pressed', String(b.dataset.tool === t));
  const p = E.part(t);
  const floor = p?.block === 2 ? ' It covers a 2x2 block, so the belt has to turn through it.'
    : p?.size > 1 ? ` It covers ${p.size} tiles: the belt tile and ${p.size === 2 ? 'one tile' : `${p.size - 1} tiles`} of free floor beside it.` : '';
  tip = p ? `${p.name}: ${p.does.toLowerCase()}.${floor} Tap a tile to put one down.` : null;
  if (t === 'belt') tip = 'Belt: drag out of a green inlet in the wall, or on from belt you have already laid, and run it into a door. A line cannot start in the middle of the floor, and it cannot cross into another room.';
  if (t === 'bin') tip = 'Bin: takes whatever reaches it off the belt, and ends the line. It covers one tile. Tap a tile to put one down.';
  if (t === 'join') tip = 'Join: three tiles in a line, on bare floor. Run a belt into each end and one out of the middle, and it merges the two plates waiting there. Tap it to turn it round.';
  if (t === 'split') tip = 'Splitter: three tiles in a line, the other way round from a Join. Run a belt into its middle and one out of each end, and it sends plates out of the two ends by turns, exactly half each. A plain junction takes whichever way is open instead. For thirds, draw three belts out of one tile; join two of those back together and that way carries two thirds.';
  if (t === 'press') tip = 'Press: a 2x2 block standing on a corner of itself, so the only two faces it leaves free are at right angles. The belt has to turn through it. It presses everything already on the plate.';
}
for (const b of document.querySelectorAll('.tools [data-tool]')) b.addEventListener('click', () => setTool(b.dataset.tool));
$('#parts').append(...Object.keys(B.stations).map((id) => {
  const p = E.part(id), b = document.createElement('button');
  b.dataset.tool = id; b.dataset.part = id; b.setAttribute('aria-pressed', 'false'); b.setAttribute('aria-label', `${p.name}, ${p.price} coins`);
  b.innerHTML = `<em>${p.icon}</em>${p.name}<s>${p.price}</s>`;
  b.addEventListener('click', () => setTool(id));
  return b;
}));
$('#turn').addEventListener('click', () => {
  if (!sel) return;
  const r = E.turn(state, sel);
  calm(r.ok ? `Turned it ${WAY[r.face]}. The belt stays where you drew it.` : r.why);
  save();
});
$('#reset').addEventListener('click', () => { if (confirm('Start over?')) { state = E.createGame(); effects = []; sel = null; view = 0; setTool('belt'); save(); } });
// A prototype should not be a waiting room: this hands over enough to buy anything and try it at once.
$('#cheat').addEventListener('click', () => { state.coins += 10000; calm('Cheat: 10,000 coins. Buy whatever you want to try.'); save(); });
// And this counts the dishes this stage is still waiting for as served, so the next room and the next part
// open on the next tick without playing the line out.
$('#skip').addEventListener('click', () => {
  if (state.done) { calm('Every stage is already open.'); return; }
  state.served = E.progress(state).need;
  calm(`Cheat: stage ${state.stage + 1} counted as served. ${B.stages[state.stage + 1]?.title || 'The last stage'} is next.`);
  save();
});

// --- the recipe book -------------------------------------------------------------------------------------
// Every dish, what goes on the plate, in what state, and what the kitchen needs to make it. A room pays
// `wantBonus` over the value for the dish it is asking for.
const procMark = (list) => list.map((p) => `<i class="proc">${B.processes[p].icon} ${B.processes[p].name.toLowerCase()}</i>`).join('');
function bookRows() {
  const wanted = new Set(state.rooms.filter((r) => r.open).map((r) => r.want));
  return Object.keys(B.recipes).map((id) => {
    const r = B.recipes[id], has = r.has;
    const parts = [...new Set([
      ...Object.keys(has).map((i) => E.adderOf(i)).filter(Boolean),
      ...[...new Set(Object.values(has).flat())].map((p) => E.applierOf(p)),
      ...(Object.keys(has).filter((i) => !E.adderOf(i)).length > 1 ? ['join'] : []),
    ])];
    const wall = Object.keys(has).filter((i) => !E.adderOf(i));
    const locked = !E.onMenu(state, id);
    const kit = [`${wall.length} ${wall.length === 1 ? 'inlet' : 'inlets'}`,
      ...parts.map((p) => (p === 'join' ? `${wall.length - 1} ${wall.length - 1 === 1 ? 'Join' : 'Joins'}` : B.stations[p].name))];
    return `<li class="${locked ? 'locked' : ''}${wanted.has(id) ? ' asked' : ''}">`
      + `<b>${r.name}</b><s>${r.value}</s>`
      + `<u>${Object.keys(has).sort((a, b) => B.ingredients[a].z - B.ingredients[b].z)
        .map((i) => `<span>${B.ingredients[i].icon} ${B.ingredients[i].name.toLowerCase()}${procMark(has[i])}</span>`).join('')}</u>`
      + `<em>${kit.join(' · ')}${locked ? ' · not unlocked yet' : ''}${wanted.has(id) ? ' · asked for now' : ''}</em></li>`;
  }).join('');
}
const dlg = $('#bookDlg');
$('#book').addEventListener('click', () => {
  $('#bookList').innerHTML = bookRows();
  dlg.showModal();
});
$('#bookClose').addEventListener('click', () => dlg.close());

// --- events ----------------------------------------------------------------------------------------------
function banner(text) {
  const el = $('#banner'); el.innerHTML = '';
  el.append(Object.assign(document.createElement('span'), { textContent: text }));
  el.classList.remove('show'); void el.offsetWidth; el.classList.add('show');
}
function drain(now) {
  for (const ev of state.events.splice(0)) {
    if (ev.type === 'eat' && here(doorway(ev.room))) effects.push({ k: doorway(ev.room), text: '+' + ev.value, t0: now });
    if (ev.type === 'waste' && here(ev.k)) effects.push({ k: ev.k, text: '✕', t0: now, grey: true });
    if (ev.type === 'stage') { banner(B.stages[ev.stage].title); save(); }
    if (ev.type === 'done') { banner('Every room is served'); save(); }
  }
}

// --- text ------------------------------------------------------------------------------------------------
// The wall a connector is set into, named by the way out through it. Inlets and doors sit on any of the four
// walls, so the arrow on one is worked out from where it is rather than assumed to be a side.
const wallOf = (k) => { const [x, y] = E.local(k); return x === 0 ? 'W' : x === N - 1 ? 'E' : y === 0 ? 'N' : 'S'; };
const doorway = (r) => (B.exits.find((e) => e.room === r && state.cells[e.cell].kind === 'out') || B.exits.find((e) => e.room === r)).cell;
const dishName = (id) => (id === 'any' ? 'any finished dish' : B.recipes[id].name.toLowerCase());
const an = (word) => (/^[aeiou]/i.test(word) ? 'an ' : 'a ') + word;
const list = (xs) => xs.length < 2 ? xs[0] : `${xs.slice(0, -1).join(', ')} and ${xs.at(-1)}`;
const EARLY = 'the plate was brought together before the process it needed, and a process marks everything'
  + ' already on the plate. Draw a short branch into a Bin to take these off, and move that station onto the'
  + ' line that carries the one ingredient, before the Join.';
// Where a process station has to stand. A process marks everything already on the plate, so a dish that wants
// only one of its ingredients worked on needs the machine on that ingredient's own line, before the Join.
function where(want, id) {
  const P = B.stations[id], has = B.recipes[want]?.has;
  if (!P?.applies || !has) return '';
  const marked = Object.keys(has).filter((i) => has[i].includes(P.applies));
  if (marked.length === Object.keys(has).length) return ' Every ingredient is worked on, so it goes after the Join.';
  return ` Only the ${list(marked.map((i) => B.ingredients[i].name.toLowerCase()))} is ${B.processes[P.applies].name.toLowerCase()}`
    + `, and a process marks everything already on the plate, so it goes on that line before the Join.`;
}
const per = (rate) => `${(B.tickMs / 1000 / rate).toFixed(1)}s`; // seconds between dishes, from dishes per tick
const at = (k) => E.label(k); // tiles are named by their room and their place on that room's floor
// Advice is about the room on the board: each room is a kitchen of its own, so a problem in another one waits
// its turn behind the chip that is flashing.
function advice() {
  if (tip) return tip;
  const r = state.rooms[view], mine = (list) => list.filter(here);
  if (!r.open) return `${B.rooms[view].title} has not opened yet. Serve more dishes and the guests will arrive.`;
  const bad = mine(E.spoiled(state))[0];
  if (bad) return `A ruined plate is going round at ${at(bad)}: this line brought together a set no recipe allows. Draw a short branch into a Bin to take them off, and fix the line that made them.`;
  const stop = mine(E.loose(state))[0];
  if (stop) return `The belt at ${at(stop)} just stops. A line runs from an inlet in the wall to somewhere its plates can go: a door in the wall, or a Bin. A loop needs neither.`;
  const bin = E.wasting(state);
  if (bin && here(bin.k)) {
    return bin.add === 'order'
      ? `Plates are being cleared at ${at(bin.k)} unfinished, and nothing can be done to them now: ${EARLY}`
      : `Plates are being cleared at ${at(bin.k)} unfinished. Put ${an(B.stations[bin.add].name)} station on that line.`;
  }
  const alone = E.lonely(state);
  if (alone && here(alone.k)) return `The plate at ${at(alone.k)} has waited a long time at one end of a Join. A Join needs a plate at each end: run a belt into ${at(alone.other)} as well.`;
  const idle = E.stuck(state);
  if (idle && here(idle.k)) {
    return idle.add === 'order'
      ? `The plates on the belt at ${at(idle.k)} can never become the dish: ${EARLY}`
      : `The plates on the belt at ${at(idle.k)} have nothing to do: this line has no ${B.stations[idle.add].name} station on it.`;
  }
  const jam = mine(E.jams(state))[0];
  if (jam) return `A plate at ${at(jam)} has nowhere to go. Erase it, or give that belt a way on.`;
  if (!Object.keys(state.cells).some((k) => here(k) && E.isIn(state.cells[k]) && state.cells[k].item && state.cells[k].links.length)) {
    return `No inlet in ${B.rooms[view].title} is delivering anything. Tap a green inlet in the wall to choose the ingredient it sends down the belt.`;
  }
  if (r.empty > B.starve) {
    const doors = B.exits.filter((e) => e.room === view).map((e) => at(e.cell));
    return `${B.rooms[view].title} has run out. Run a belt into ${doors.length > 1 ? 'one of its doors' : 'its door'}`
      + ` at ${doors.join(' or ')}, and tap that door until it serves.`;
  }
  if (r.want !== 'any') {
    const hole = E.unfed(state, r.want, view), gap = E.missing(state, r.want, view);
    const asked = `${B.rooms[view].title} is paying extra for ${dishName(r.want)}.`;
    if (hole.length) return `${asked} Set an inlet in this room to deliver ${B.ingredients[hole[0]].name.toLowerCase()}, and join it onto that line.`;
    if (gap.length) return `${asked} Add ${an(B.stations[gap[0]].name)} station to the line in this room.${where(r.want, gap[0])}`;
  }
  const cap = E.capacity(state).rooms[view];
  if (cap?.short) {
    return `${B.rooms[view].title}'s ${cap.seats} seats want a dish every ${per(cap.eats)}, and this room's line can only make one every `
      + `${cap.made > 0 ? per(cap.made) : '—'}. Some guests never get served: ${cap.limitText}.`;
  }
  if (state.done) return 'Every room is served. Keep building: the menu has dishes no room has asked for yet.';
  const p = E.progress(state), left = Math.max(0, p.need - p.served);
  const doors = B.exits.filter((e) => e.room === view).length;
  if (doors > 1) {
    return `Serve ${left} more dishes. ${B.rooms[view].title} has ${doors} doors. A Splitter sends exactly half down each way;`
      + (doors > 2 ? ' three belts out of one tile each take a third, and joining two of those back up carries two thirds.'
        : ' a plain junction takes whichever way is open instead.');
  }
  return `Serve ${left} more dishes. Every machine takes the same time and holds the plate while it works.`;
}

const shown = {};
function put(id, value, prop = 'textContent') {
  if (shown[id + prop] === value) return;
  shown[id + prop] = value;
  if (prop === 'width') $(id).style.width = value; else $(id)[prop] = value;
}
function hud(now) {
  const p = E.progress(state);
  if (sel && !state.cells[sel]?.st) sel = null; // it was erased out from under the selection
  const turnable = !!sel && E.canTurn(state, sel);
  $('#turn').disabled = !turnable;
  $('#turn').setAttribute('aria-label', turnable ? `Turn the ${E.part(state.cells[sel].st).name}` : 'Turn: select a machine first');
  put('#coins', state.coins.toLocaleString('en-US'));
  put('#goalLabel', state.done ? `All done · ${state.total} dishes` : `Dishes ${Math.min(p.served, p.need)}/${p.need}`);
  put('#goalFill', state.done ? '100%' : Math.min(100, (100 * p.served) / p.need) + '%', 'width');
  if (warn && now > warn.until) warn = null;
  put('#hint', warn ? warn.text : advice());
  $('#hint').classList.toggle('warn', !!warn && !warn.calm);
  for (const b of document.querySelectorAll('[data-part]')) {
    const id = b.dataset.part;
    b.hidden = !E.unlocked(state, id);
    b.disabled = state.coins < E.price(id);
  }
  const cap = E.capacity(state), mine = cap.rooms[view];
  put('#flow', mine
    ? `${B.rooms[view].title}: this room's line makes a dish every ${mine.made > 0 ? per(mine.made) : '—'} at best. ${mine.seats} seats want one every ${per(mine.eats)}.`
    : `${B.rooms[view].title} has not opened yet.`);
  $('#flow').classList.toggle('short', !!mine?.short);
  const sig = view + '|' + state.rooms.map((r, i) => `${r.open}${r.want}${r.q.length}${r.empty > B.starve}${cap.rooms[i]?.short}`).join('|');
  if (shown.rooms !== sig) {
    shown.rooms = sig;
    $('#serving').replaceChildren(...state.rooms.map((r, i) => {
      const el = document.createElement('button');
      el.className = 'room' + (r.open && r.empty > B.starve ? ' hungry' : '') + (cap.rooms[i]?.short ? ' short' : '') + (r.open ? '' : ' shut');
      el.dataset.room = String(i);
      el.setAttribute('aria-pressed', String(i === view));
      const doors = B.exits.filter((e) => e.room === i).length, ins = B.rooms[i].in.length;
      el.setAttribute('aria-label', `Room ${B.rooms[i].name}, the ${B.rooms[i].title}, `
        + (r.open ? `${B.rooms[i].seats} seats, ${ins} inlets, ${doors} ${doors === 1 ? 'door' : 'doors'}, wants ${dishName(r.want)}, ${r.q.length} on hand` : 'not open yet')
        + (cap.rooms[i]?.short ? ', more seats than this room can feed' : ''));
      el.innerHTML = `<b><i style="background:${B.rooms[i].color}"></i>${B.rooms[i].name} · ${r.open ? dishName(r.want) : 'shut'}</b>`
        + `<u>${Array.from({ length: B.queue }, (_, n) => `<s class="${n < r.q.length ? 'full' : ''}"></s>`).join('')}`
        + `<i class="seats">${B.rooms[i].seats} seats · ${ins} in · ${doors} out${cap.rooms[i]?.short ? ' · short' : ''}</i></u>`;
      el.addEventListener('click', () => { view = i; sel = null; shown.rooms = null; });
      return el;
    }));
  }
}

// --- drawing ---------------------------------------------------------------------------------------------
function box(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
function emoji(text, x, y, size, alpha = 1) {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = INK;
  ctx.font = `${size}px system-ui, "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif`;
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(text, x, y + size * 0.06); ctx.restore();
}
// A plate and everything on it. The plate holds a set, not a stack, so the ingredients are drawn in their own
// fixed order however they were put on. A processed ingredient is drawn in that process's colour. A plate
// carrying a set no recipe allows is ruined, and says so: a red rim and a cross through it.
function plate(x, y, d, scale = 1) {
  const r = G.s * 0.24 * scale, bad = E.ruined(d);
  ctx.fillStyle = '#fff'; ctx.strokeStyle = bad ? RED : 'rgba(42,47,69,.35)'; ctx.lineWidth = bad ? 2.5 : 1.5;
  ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); ctx.stroke();
  ctx.strokeStyle = 'rgba(42,47,69,.35)'; ctx.lineWidth = 1.5;
  let h = 0;
  for (const id of Object.keys(d.on).sort((a, b) => B.ingredients[a].z - B.ingredients[b].z)) {
    const ing = B.ingredients[id], yy = y - h;
    const shape = {
      ball: () => { ctx.beginPath(); ctx.ellipse(x, yy + r * 0.1, r * 0.66, r * 0.5, 0, 0, 7); },
      slab: () => box(x - r * 0.74, yy - r * 0.5, r * 1.48, r * 0.66, r * 0.3),
      dots: () => { ctx.beginPath(); for (let i = -1; i <= 1; i++) { ctx.moveTo(x + i * r * 0.4 + r * 0.19, yy + r * 0.04); ctx.arc(x + i * r * 0.4, yy + r * 0.04, r * 0.19, 0, 7); } },
      // nori wraps what is on the plate instead of sitting on top of it, so a roll stays as low as a nigiri
      wrap: () => box(x - r * 0.86, yy - r * 0.26, r * 1.72, r * 0.52, r * 0.24),
      stick: () => box(x - r * 0.62, yy - r * 0.34, r * 1.24, r * 0.4, r * 0.18),
      dab: () => { ctx.beginPath(); ctx.arc(x + r * 0.5, yy, r * 0.2, 0, 7); },
    }[ing.shape];
    ctx.fillStyle = ing.color; shape(); ctx.fill();
    if (ing.shape === 'ball') ctx.stroke();
    // a processed ingredient keeps its own shape and colour underneath, so the dish is still readable
    for (const pr of d.on[id]) { ctx.save(); ctx.globalAlpha *= 0.55; ctx.fillStyle = B.processes[pr].tint; shape(); ctx.fill(); ctx.restore(); }
    h += ing.shape === 'ball' ? r * 0.16 : ing.shape === 'slab' ? r * 0.46 : ing.shape === 'stick' ? r * 0.3 : 0;
  }
  if (!bad) return;
  ctx.strokeStyle = RED; ctx.lineWidth = 3; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(x - r * 0.6, y - r * 0.6); ctx.lineTo(x + r * 0.6, y + r * 0.6);
  ctx.moveTo(x + r * 0.6, y - r * 0.6); ctx.lineTo(x - r * 0.6, y + r * 0.6); ctx.stroke();
}
// A machine is one block of floor: every tile it covers is filled, and only the outside of the block is drawn,
// so what is on the floor is exactly the room it takes up. The belt runs through its one belt tile, so the
// plate being worked on takes that tile and nothing else can pass: the queue builds up behind.
function blockFace(tiles, fill, line) {
  const s = G.s, mine = new Set(tiles);
  ctx.fillStyle = fill;
  for (const t of tiles) { const [tx, ty] = centre(t); ctx.fillRect(tx - s / 2, ty - s / 2, s, s); }
  ctx.strokeStyle = line; ctx.lineWidth = 2.5;
  ctx.beginPath();
  for (const t of tiles) {
    const [tx, ty] = centre(t), l = tx - s / 2, r = tx + s / 2, u = ty - s / 2, d = ty + s / 2;
    if (!mine.has(E.step(t, 'N'))) { ctx.moveTo(l, u); ctx.lineTo(r, u); }
    if (!mine.has(E.step(t, 'S'))) { ctx.moveTo(l, d); ctx.lineTo(r, d); }
    if (!mine.has(E.step(t, 'W'))) { ctx.moveTo(l, u); ctx.lineTo(l, d); }
    if (!mine.has(E.step(t, 'E'))) { ctx.moveTo(r, u); ctx.lineTo(r, d); }
  }
  ctx.stroke();
}
function beltThrough(tiles) {
  const s = G.s;
  ctx.strokeStyle = '#3d4566'; ctx.lineWidth = s * 0.3; ctx.lineCap = 'butt';
  ctx.beginPath();
  for (const t of tiles) {
    const [tx, ty] = centre(t);
    for (const dir of state.cells[t]?.links || []) { ctx.moveTo(tx, ty); ctx.lineTo(tx + E.DIRS[dir][0] * s * 0.5, ty + E.DIRS[dir][1] * s * 0.5); }
  }
  ctx.stroke(); ctx.lineCap = 'round';
}
function timer(k, hold) {
  const [x, y] = centre(k), s = G.s;
  ctx.strokeStyle = GOLD; ctx.lineWidth = 3.5; ctx.lineCap = 'butt';
  ctx.beginPath(); ctx.arc(x, y, s * 0.37, -Math.PI / 2, -Math.PI / 2 + 2 * Math.PI * (1 - hold / B.speed)); ctx.stroke();
  ctx.lineCap = 'round';
}
function drawStation(k) {
  const c = state.cells[k], s = G.s, busy = c.hold > 0, tiles = [k, ...(c.work || [])];
  blockFace(tiles, '#fffaf0', INK);
  beltThrough([k]);
  // the icon sits in the middle of the body, clear of the belt tile the plates ride along
  const body = c.work?.length ? c.work : [k];
  const mid = body.reduce((acc, t) => { const [bx, by] = centre(t); return [acc[0] + bx / body.length, acc[1] + by / body.length]; }, [0, 0]);
  emoji(B.stations[c.st].icon, mid[0], mid[1], s * 0.46, busy ? 0.55 : 1);
  if (busy) timer(k, c.hold);
}

// A Join and a Splitter are the same three tiles the opposite way round. A Join takes plates in at its two ends
// and they wait there until both are filled, and the merged plate leaves from the middle. A Splitter is fed at
// its middle and pushes plates out of its ends by turns. The arrows say which way it runs.
function drawSpan(k) {
  const c = state.cells[k], s = G.s, out = E.isSplit(c), tiles = [k, ...c.arms];
  blockFace(tiles, out ? '#e3f4f4' : '#f1edff', out ? '#0e6f6f' : '#4b3f8f');
  beltThrough(tiles);
  for (const t of c.arms) {
    const [ax, ay] = centre(t);
    arrow(ax, ay, out ? E.dirBetween(k, t) : E.dirBetween(t, k), out ? '#0e6f6f' : '#4b3f8f', 0.38);
  }
  const [x, y] = centre(k);
  emoji(B.stations[c.st].icon, x, y, s * 0.34, c.dish ? 0.3 : 0.75);
  if (c.hold > 0) timer(k, c.hold);
}

// The mark on a piece of belt that says which way it carries plates.
function chevron(x, y, dir) {
  const s = G.s, [dx, dy] = E.DIRS[dir], px = -dy, py = dx, a = 0.3, b = 0.12;
  ctx.strokeStyle = 'rgba(247,241,227,.55)'; ctx.lineWidth = Math.max(2, s * 0.05); ctx.lineJoin = 'round';
  ctx.beginPath();
  ctx.moveTo(x + dx * s * b + px * s * 0.1, y + dy * s * b + py * s * 0.1);
  ctx.lineTo(x + dx * s * a, y + dy * s * a);
  ctx.lineTo(x + dx * s * b - px * s * 0.1, y + dy * s * b - py * s * 0.1);
  ctx.stroke();
}

// A small chevron on a tile, pointing the way the belt runs from it.
function arrow(x, y, dir, color, len = 0.42) {
  const s = G.s, [dx, dy] = E.DIRS[dir], px = -dy, py = dx, back = len - 0.22;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(x + dx * s * len, y + dy * s * len);
  ctx.lineTo(x + dx * s * back + px * s * 0.13, y + dy * s * back + py * s * 0.13);
  ctx.lineTo(x + dx * s * back - px * s * 0.13, y + dy * s * back - py * s * 0.13);
  ctx.fill();
}

function render(now) {
  const { s, ox, oy } = G, cells = state.cells;
  const phase = Math.min(1, (now - lastTick) / B.tickMs);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = '#cbbd9f'; box(ox - 7, oy - 7, s * N + 14, s * N + 14, 16); ctx.fill();
  ctx.fillStyle = '#f7f1e3'; box(ox, oy, s * N, s * N, 9); ctx.fill();
  ctx.fillStyle = 'rgba(42,47,69,.035)';
  for (let x = 0; x < N; x++) for (let y = 0; y < N; y++) if ((x + y) % 2) ctx.fillRect(ox + x * s, oy + y * s, s, s);

  // The belt, with a chevron on each piece for the way it runs
  ctx.lineCap = 'round';
  for (const k in cells) {
    const c = cells[k];
    if (!c.links.length || !here(k)) continue;
    const [x, y] = centre(k);
    ctx.strokeStyle = '#3d4566'; ctx.lineWidth = s * 0.46;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y);
    for (const dir of c.links) { ctx.moveTo(x, y); ctx.lineTo(x + E.DIRS[dir][0] * s * 0.5, y + E.DIRS[dir][1] * s * 0.5); }
    ctx.stroke();
    if (c.links.length > 2) { ctx.fillStyle = GOLD; const r = s * 0.13; ctx.beginPath(); ctx.moveTo(x, y - r); ctx.lineTo(x + r, y); ctx.lineTo(x, y + r); ctx.lineTo(x - r, y); ctx.fill(); }
    for (const dir of c.outs || []) chevron(x, y, dir); // which way this piece of belt runs
  }

  // Wall connectors, drawn over the belt that reaches them. Green inlets feed the belt and are the only place a
  // line may begin; a room-coloured door serves its room, a grey one clears the line. The arrow points the way
  // the plates travel, through whichever of the four walls the connector is set into.
  B.exits.forEach((e) => {
    if (!here(e.cell)) return;
    const c = cells[e.cell], [x, y] = centre(e.cell), side = wallOf(e.cell);
    if (E.isIn(c)) {
      // An inlet is the only place a line may begin, and it shows the ingredient it delivers. Tap to change it.
      ctx.fillStyle = c.item ? '#2f7d4f' : '#5d7a68'; ctx.strokeStyle = ctx.fillStyle; ctx.lineWidth = 3;
      box(x - s * 0.44, y - s * 0.44, s * 0.88, s * 0.88, 10); ctx.fill(); ctx.stroke();
      if (c.item) {
        ctx.fillStyle = '#fff';
        ctx.beginPath(); ctx.arc(x, y - s * 0.13, s * 0.26, 0, 7); ctx.fill();
        emoji(B.ingredients[c.item].icon, x, y - s * 0.13, s * 0.3);
      } else {
        ctx.fillStyle = '#fff';
        ctx.font = `800 ${s * 0.24}px system-ui, sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText('TAP', x, y - s * 0.13);
      }
      arrow(x, y + s * 0.23, E.OPP[side], '#fff', 0.19); // plates come in off the wall
      return;
    }
    const room = state.rooms[e.room];
    const drop = c.kind === 'drop';
    const col = drop ? '#7a7566' : B.rooms[e.room].color;
    ctx.globalAlpha = room.open ? 1 : 0.35;
    ctx.fillStyle = col; ctx.strokeStyle = col; ctx.lineWidth = 3;
    box(x - s * 0.44, y - s * 0.44, s * 0.88, s * 0.88, 10); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#fff';
    ctx.font = `800 ${s * 0.32}px system-ui, sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(B.rooms[e.room].name, x, y - s * 0.19);
    arrow(x, y + s * 0.06, side, '#fff', 0.24); // plates leave through the wall
    if (drop) emoji('🗑️', x, y + s * 0.3, s * 0.26);
    else for (let n = 0; n < B.queue; n++) {
      ctx.globalAlpha = (room.open ? 1 : 0.35) * (n < room.q.length ? 1 : 0.3);
      ctx.beginPath(); ctx.arc(x + (n - (B.queue - 1) / 2) * s * 0.15, y + s * 0.32, s * 0.045, 0, 7); ctx.fill();
    }
    ctx.globalAlpha = 1;
    if (room.open && !drop && room.empty > B.starve) { ctx.strokeStyle = RED; ctx.lineWidth = 3; box(x - s * 0.47, y - s * 0.47, s * 0.94, s * 0.94, 12); ctx.stroke(); }
  });

  // A belt that just stops: its plates have nowhere to go, so they stack up against it.
  for (const { k, type } of E.ends(state)) {
    if (type !== 'loose' || !here(k)) continue;
    const [x, y] = centre(k);
    ctx.strokeStyle = '#c4861c'; ctx.lineWidth = 3; ctx.setLineDash([5, 4]);
    ctx.beginPath(); ctx.arc(x, y, s * 0.34, 0, 7); ctx.stroke(); ctx.setLineDash([]);
  }

  // Machines cover a block of floor around their belt tile; the plates ride over them.
  for (const k in cells) {
    const c = cells[k];
    if (!here(k)) continue;
    if (E.isJoin(c) || E.isSplit(c)) drawSpan(k);
    else if (c.st) drawStation(k);
  }
  for (const k in cells) {
    const d = cells[k].dish;
    if (!d || !here(k)) continue;
    const p = d.pk && d.pk !== k && here(d.pk) ? lerp(spot(d.pk), spot(k), phase) : spot(k);
    plate(p[0], p[1], d, 1);
  }

  // the selected machine, and the ghost of where a dragged one would land
  const ring = (tiles, colour) => {
    ctx.strokeStyle = colour; ctx.lineWidth = 3; ctx.setLineDash([6, 4]);
    for (const t of tiles) { const [tx, ty] = centre(t); ctx.strokeRect(tx - s / 2 + 2, ty - s / 2 + 2, s - 4, s - 4); }
    ctx.setLineDash([]);
  };
  if (sel && cells[sel]?.st && here(sel)) ring([sel, ...(cells[sel].arms || cells[sel].work || [])], GOLD);
  if (stroke?.move && stroke.to) {
    const land = E.fitsAt(state, stroke.move, stroke.to);
    ring(land || [stroke.to], land ? '#2f7d4f' : RED);
  }

  effects = effects.filter((f) => now - f.t0 < 800);
  for (const f of effects) {
    if (!here(f.k)) continue;
    const [x, y] = centre(f.k), t = (now - f.t0) / 800;
    ctx.globalAlpha = 1 - t; ctx.fillStyle = f.grey ? '#7a7566' : '#9a6a0c'; ctx.font = `800 ${s * 0.3}px system-ui, sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(f.text, x, y - s * (0.5 + 0.4 * t)); ctx.globalAlpha = 1;
  }
}

function frame(now) {
  if (now - lastTick > B.tickMs * 200) lastTick = now - B.tickMs * 200; // cap catch-up after a long pause
  let ticked = false;
  while (now - lastTick >= B.tickMs) { E.tick(state); lastTick += B.tickMs; ticked = true; }
  drain(now);
  if (ticked && state.tick % 15 === 0) save();
  hud(now);
  render(now);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

// For browser checks.
window.kitchenLine = {
  get state() { return state; }, E, balance: B,
  get view() { return view; }, show(i) { view = i; sel = null; shown.rooms = null; },
  centre(k) { const r = canvas.getBoundingClientRect(), [x, y] = centre(k); return [r.left + x, r.top + y]; },
};
