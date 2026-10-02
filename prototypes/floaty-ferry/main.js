import './style.css';
import { createGame, connect, disconnect, tick, rating } from './engine.js';
import { BALANCE as B, ISLANDS } from './balance.js';
import { mountWorld } from './world.js';

const $ = id => document.getElementById(id), SYMBOLS = ['★', '♥', '❧', '☾', '✹', '◆'];
const read = key => { try { return localStorage.getItem(`floaty-ferry:${key}`); } catch { return null; } };
const save = (key, value) => { try { localStorage.setItem(`floaty-ferry:${key}`, value); } catch { /* Storage is optional. */ } };
let state = createGame(), day = 1, resultShown = false, audio, drag = null, transient = '', transientFor = 0, controlsKey = '', rendered = '';
const ui = { paused: true, motion: !matchMedia('(prefers-reduced-motion: reduce)').matches, sound: false, selected: null, pointer: null, edit: false };
const { scene } = mountWorld(() => state, () => ui, dt => {
  if (ui.paused || document.hidden) return;
  tick(state, dt); transientFor = Math.max(0, transientFor - dt);
  for (const event of state.events.splice(0)) { scene.emit(event); if (event.type === 'deliver') tone(540 + event.island * 85); if (event.type === 'upgrade') toast('A new ferry! You can draw five routes.'); }
  render();
  if (state.status === 'finished' && !resultShown) {
    resultShown = true;
    if (state.tutorial) { save('learned', 'yes'); openModal('Captain, you’re ready.', 'Ducklings change boats to find their way. Connect more islands as the day gets busy.', [{ label: 'Start a little day', action: () => start(false, 1) }], { stars: 3, kicker: 'TUTORIAL COMPLETE' }); }
    else { const best = Math.max(Number(read('best') || 0), state.delivered); save('best', best); openModal('A lovely day afloat.', `${state.delivered} ducklings home · ${state.splashes ? `${state.splashes} went for a swim` : 'happy little passengers'} · best ${best}`, [{ label: 'Tomorrow’s tide →', action: () => start(false, day + 1) }, { label: 'Sail this day again', action: () => start(false, day), secondary: true }], { stars: rating(state), kicker: `DAY ${String(day).padStart(2, '0')} COMPLETE` }); }
  }
});
function tone(frequency) {
  if (!ui.sound) return;
  try { audio ||= new (window.AudioContext || window.webkitAudioContext)(); audio.resume(); const o = audio.createOscillator(), g = audio.createGain(); o.type = 'sine'; o.frequency.setValueAtTime(frequency, audio.currentTime); o.frequency.exponentialRampToValueAtTime(frequency * 1.2, audio.currentTime + .16); g.gain.setValueAtTime(.04, audio.currentTime); g.gain.exponentialRampToValueAtTime(.001, audio.currentTime + .16); o.connect(g); g.connect(audio.destination); o.start(); o.stop(audio.currentTime + .16); } catch { ui.sound = false; }
}
function clearSelection() { ui.selected = null; ui.pointer = null; drag = null; }
function toast(text) { transient = text; transientFor = 2.4; }
function openModal(title, copy, actions, options = {}) {
  ui.paused = true; clearSelection(); $('modal-title').textContent = title; $('modal-copy').textContent = copy; $('modal-kicker').textContent = options.kicker || 'TAKE A BREATHER'; $('modal-art').hidden = !options.art;
  $('medal').hidden = !options.stars; $('medal').replaceChildren();
  if (options.stars) for (let i = 0; i < 3; i++) { const s = document.createElement('span'); s.textContent = '♡'; s.className = i < options.stars ? '' : 'dim'; $('medal').append(s); }
  $('modal-actions').replaceChildren(); for (const { label, action, secondary } of actions) { const b = document.createElement('button'); b.className = secondary ? 'secondary' : 'primary'; b.textContent = label; b.onclick = () => { $('modal').close(); action(); }; $('modal-actions').append(b); }
  if (!$('modal').open) $('modal').showModal();
}
function start(tutorial = false, nextDay = 1) { day = nextDay; state = createGame(tutorial, day); ui.paused = false; ui.edit = false; clearSelection(); resultShown = false; transientFor = 0; controlsKey = ''; scene.reset(); render(); $('world').focus({ preventScroll: true }); }
function renderControls() {
  const key = `${ui.edit}:${state.routes.map(r => r.id).join(',')}:${state.tutorial}:${state.lesson}`;
  if (key !== controlsKey) {
    controlsKey = key; $('island-controls').replaceChildren();
    if (ui.edit) for (const route of state.routes) {
      const b = document.createElement('button'); b.textContent = '×'; b.style.setProperty('--island', '#f0b5a5'); b.setAttribute('aria-label', `Remove route: ${ISLANDS[route.a].name} to ${ISLANDS[route.b].name}`); b.onclick = () => { disconnect(state, route.id); render(); }; $('island-controls').append(b);
    } else ISLANDS.forEach((island, i) => {
      const b = document.createElement('button'); b.textContent = SYMBOLS[i]; b.style.setProperty('--island', `#${island.color.toString(16)}`); b.dataset.island = i; b.setAttribute('aria-label', `Select ${island.name} island, ${island.shape}`); b.onclick = () => { if (!ui.paused) select(i); }; $('island-controls').append(b);
    });
  }
  for (const b of $('island-controls').children) if (b.dataset.island !== undefined) { const id = Number(b.dataset.island); b.setAttribute('aria-pressed', String(id === ui.selected)); b.disabled = state.tutorial && (![0, 1].includes(id) && !(state.lesson >= 2 && id === 2) || [1, 3, 4].includes(state.lesson)); }
}
function render() {
  const key = [day, state.tutorial, state.status, state.delivered, state.maxRoutes, state.routes.map(r => r.id).join(','), state.lesson, Math.ceil(B.duration - state.time), ui.selected, ui.edit, ui.paused, transientFor > 0 ? transient : ''].join(':');
  if (key === rendered) return; rendered = key;
  $('delivered').textContent = state.delivered; $('routes').textContent = `${state.routes.length} / ${state.maxRoutes}`;
  $('chapter-label').textContent = state.tutorial ? `LESSON ${state.lesson < 2 ? '01' : state.lesson < 4 ? '02' : '03'} / 03` : `DAY ${String(day).padStart(2, '0')}`;
  $('day-name').textContent = state.tutorial ? 'A captain’s first sail' : ['The slow coast', 'A peachy crossing', 'Hello, blue horizon'][(day - 1) % 3];
  const remaining = Math.ceil(B.duration - state.time); $('time').textContent = state.tutorial ? 'take your time' : `${Math.floor(remaining / 60)}:${String(remaining % 60).padStart(2, '0')}`;
  $('time-fill').style.width = `${state.tutorial ? 100 : Math.max(0, 1 - state.time / B.duration) * 100}%`;
  $('lesson-dot').textContent = state.tutorial ? state.lesson < 2 ? 1 : state.lesson < 4 ? 2 : 3 : '↝';
  const prompts = ['Draw from the gold star to the pink heart.', 'All aboard! Watch the pink duckling arrive.', 'Now connect the gold star to the mint leaf.', 'Off to Mint. Colors show where ducks want to go.', 'Watch a duck change boats at the gold star.'];
  $('hint').textContent = transientFor ? transient : ui.edit ? 'Tap a route or × to return its ferry.' : state.tutorial ? prompts[Math.min(state.lesson, prompts.length - 1)] : ui.selected !== null ? `From ${ISLANDS[ui.selected].name}… choose another island.` : 'Draw between islands. Boats do the rest.';
  $('edit').disabled = state.tutorial; $('edit').setAttribute('aria-pressed', ui.edit); $('edit').textContent = ui.edit ? '✓ Done editing' : '✂ Edit routes'; $('clear-selection').disabled = ui.selected === null; document.body.classList.toggle('editing', ui.edit); renderControls();
}
function tryConnect(a, b) {
  if (connect(state, a, b)) { tone(390); }
  else if (a !== b) toast(state.routes.length >= state.maxRoutes ? 'All ferries busy. Edit a route to move one.' : state.tutorial ? 'Follow the glowing islands for this lesson.' : 'Those islands already have a ferry.');
  clearSelection(); render();
}
function select(id) {
  if (state.tutorial && ([1, 3, 4].includes(state.lesson) || id > 1 && !(state.lesson >= 2 && id === 2))) return;
  if (ui.selected === null) ui.selected = id;
  else if (ui.selected === id) clearSelection();
  else tryConnect(ui.selected, id);
  render();
}
function point(e) { const r = $('world').getBoundingClientRect(); return scene.toLogical(e.clientX - r.left - 3, e.clientY - r.top - 3); }
function nearest(p) { return state.islands.find(i => Math.hypot(p.x - i.x, p.y - i.y) < Math.max(40, 22 / scene.zoom))?.id ?? null; }
function removeNear(p) {
  let best = null, closest = Infinity;
  for (const route of state.routes) {
    const a = ISLANDS[route.a], b = ISLANDS[route.b], dx = b.x - a.x, dy = b.y - a.y;
    const ratio = Math.max(0, Math.min(1, ((p.x - a.x) * dx + (p.y - a.y) * dy) / (dx * dx + dy * dy)));
    const distance = Math.hypot(p.x - a.x - dx * ratio, p.y - a.y - dy * ratio);
    if (distance < closest) { closest = distance; best = route; }
  }
  if (best && closest < Math.max(20, 22 / scene.zoom)) disconnect(state, best.id); render();
}
$('world').addEventListener('pointerdown', e => {
  if (ui.paused || e.button !== 0 || drag) return;
  const p = point(e), id = nearest(p);
  if (ui.edit) { removeNear(p); return; }
  if (id === null) { clearSelection(); render(); return; }
  if (state.tutorial && ([1, 3, 4].includes(state.lesson) || id > 1 && !(state.lesson >= 2 && id === 2))) return;
  drag = { pointer: e.pointerId, origin: id, before: ui.selected, moved: false };
  ui.selected = id; ui.pointer = p; $('world').setPointerCapture(e.pointerId); render();
});
$('world').addEventListener('pointermove', e => { if (!drag || drag.pointer !== e.pointerId) return; const p = point(e); drag.moved ||= Math.hypot(p.x - ISLANDS[drag.origin].x, p.y - ISLANDS[drag.origin].y) > 15; ui.pointer = p; });
$('world').addEventListener('pointerup', e => {
  if (!drag || drag.pointer !== e.pointerId) return;
  const id = nearest(point(e)), d = drag; drag = null; ui.pointer = null;
  if (id !== null && id !== d.origin) tryConnect(d.origin, id);
  else if (id !== null && d.before !== null && d.before !== id) tryConnect(d.before, id);
  else if (id === d.before || id === null && d.moved) clearSelection();
  render();
});
$('world').addEventListener('pointercancel', () => { clearSelection(); render(); });
$('world').addEventListener('lostpointercapture', () => { if (drag) { clearSelection(); render(); } });
$('clear-selection').onclick = () => { clearSelection(); render(); };
$('edit').onclick = () => { if (!ui.paused) { ui.edit = !ui.edit; clearSelection(); render(); } };
$('reset').onclick = () => { if (!ui.paused) start(state.tutorial, day); };
function help() {
  if ($('modal').open) return;
  openModal('A shore break.', 'Connect two islands by dragging or tapping. Match duck colors and shapes to islands. Boats transfer ducks automatically. Pink rings mean a long wait; eight arrivals earn a fifth ferry.', [{ label: 'Back aboard', action: () => { ui.paused = false; render(); } }, { label: 'Practice the routes', action: () => start(true), secondary: true }, { label: 'Restart this day', action: () => start(false, day), secondary: true }]);
}
$('help').onclick = help;
$('sound').onclick = () => { ui.sound = !ui.sound; $('sound').setAttribute('aria-pressed', ui.sound); $('sound').setAttribute('aria-label', ui.sound ? 'Turn sound off' : 'Turn sound on'); tone(660); };
$('modal').addEventListener('cancel', e => e.preventDefault());
document.addEventListener('keydown', e => { if (e.key === 'Escape' && !$('modal').open) { if (ui.selected !== null) { clearSelection(); render(); } else help(); } });
document.addEventListener('visibilitychange', () => { if (document.hidden) { clearSelection(); if (!$('modal').open) help(); } });
matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', e => { ui.motion = !e.matches; });
render(); openModal('Every duck has a place.', 'Connect the islands. Duckling colors and shapes tell you where they want to go.', [{ label: read('learned') ? 'Start a little day' : 'Show me how', action: () => start(!read('learned')) }, { label: read('learned') ? 'Practice the routes' : 'Straight to the coast', action: () => start(Boolean(read('learned'))), secondary: true }], { art: true, kicker: 'WELCOME ABOARD' });
if (new URLSearchParams(location.search).has('test')) window.__floatyFerry = { snapshot: () => structuredClone(state), start, advance: dt => { if (!ui.paused) tick(state, dt); render(); }, point: p => scene.toScreen(p), get paused() { return ui.paused; } };
