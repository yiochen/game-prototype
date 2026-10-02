import './style.css';
import { createGame, launch, tick, recall, trajectory, medal } from './engine.js';
import { GARDENS } from './balance.js';
import { mountWorld } from './world.js';

const $ = id => document.getElementById(id);
const read = key => { try { return localStorage.getItem(`pollen-club:${key}`); } catch { return null; } };
const save = (key, value) => { try { localStorage.setItem(`pollen-club:${key}`, value); } catch { /* Play also works without storage. */ } };
let state = createGame(), currentLevel = 0, audio;
let medals; try { medals = JSON.parse(read('medals') || '[]'); if (!Array.isArray(medals)) medals = []; } catch { medals = []; }
const ui = { paused: true, motion: !matchMedia('(prefers-reduced-motion: reduce)').matches, pull: null, preview: [], sound: false };
let drag = null, lastPull = { x: 0, y: 65 }, resultShown = false, winTime = 0, rendered = '';
const { scene } = mountWorld(() => state, () => ui, dt => {
  if (ui.paused || document.hidden) return;
  tick(state, dt);
  const events = state.events.splice(0);
  for (const event of events) { scene.emit(event); if (event.type === 'bloom') tone(520 + event.id * 130); else if (event.type === 'bounce') tone(220, .04); }
  render();
  if (state.status === 'won') winTime += dt;
  if (state.status === 'won' && winTime >= (ui.motion ? .85 : .2) && !resultShown) {
    resultShown = true;
    if (state.tutorial) {
      if (state.level === 0) openModal('One happy flower!', 'Now try a dewdrop. Aim at it to bounce toward the next flower.', [{ label: 'Try the bounce', action: () => startTutorial(1) }], { art: true, kicker: 'NICELY FLOWN' });
      else { save('learned', 'yes'); openModal('You’re a natural.', 'Dewdrops and garden edges bounce. Wake every flower, in as few flights as you like.', [{ label: 'Into the garden', action: () => start(0) }], { stars: 3, kicker: 'TUTORIAL COMPLETE' }); }
    } else {
      const stars = medal(state); medals[currentLevel] = Math.max(medals[currentLevel] || 0, stars); save('medals', JSON.stringify(medals));
      openModal(currentLevel === GARDENS.length - 1 ? 'A garden full of joy.' : 'All awake!', `${state.shots} ${state.shots === 1 ? 'flight' : 'flights'} · ${stars === 3 ? 'A lovely little round.' : 'Every bloom is a good bloom.'}`, [{ label: currentLevel === GARDENS.length - 1 ? 'Another garden tour' : 'Next garden →', action: () => start((currentLevel + 1) % GARDENS.length) }, { label: 'Try this garden again', action: () => start(currentLevel), secondary: true }], { stars, kicker: currentLevel === GARDENS.length - 1 ? 'FIVE LITTLE GARDENS' : 'GARDEN COMPLETE' });
    }
  }
});
function tone(frequency, duration = .12) {
  if (!ui.sound) return;
  try { audio ||= new (window.AudioContext || window.webkitAudioContext)(); audio.resume(); const oscillator = audio.createOscillator(), gain = audio.createGain(); oscillator.type = 'sine'; oscillator.frequency.setValueAtTime(frequency, audio.currentTime); oscillator.frequency.exponentialRampToValueAtTime(frequency * 1.35, audio.currentTime + duration); gain.gain.setValueAtTime(.045, audio.currentTime); gain.gain.exponentialRampToValueAtTime(.001, audio.currentTime + duration); oscillator.connect(gain); gain.connect(audio.destination); oscillator.start(); oscillator.stop(audio.currentTime + duration); } catch { ui.sound = false; }
}
function openModal(title, copy, actions, options = {}) {
  ui.paused = true; cancelDrag(); $('modal-title').textContent = title; $('modal-copy').textContent = copy; $('modal-kicker').textContent = options.kicker || 'TAKE A BREATHER';
  $('modal-art').hidden = !options.art; $('medal').hidden = !options.stars;
  $('medal').replaceChildren();
  if (options.stars) for (let i = 0; i < 3; i++) { const s = document.createElement('span'); s.textContent = '✿'; s.className = i < options.stars ? '' : 'dim'; $('medal').append(s); }
  $('modal-actions').replaceChildren();
  for (const { label, action, secondary } of actions) { const button = document.createElement('button'); button.className = secondary ? 'secondary' : 'primary'; button.textContent = label; button.addEventListener('click', () => { $('modal').close(); action(); }); $('modal-actions').append(button); }
  if (!$('modal').open) $('modal').showModal();
}
function start(level) { state = createGame(level); currentLevel = level; finishStart(); }
function startTutorial(level = 0) { state = createGame(level, true); finishStart(); }
function finishStart() { ui.paused = false; ui.pull = null; ui.preview = []; drag = null; resultShown = false; winTime = 0; scene.reset(); lastPull = { x: 0, y: state.tutorial && state.level === 1 ? 85 : 65 }; render(); $('world').focus({ preventScroll: true }); }
function render() {
  const key = [state.level, state.tutorial, state.status, state.shots, state.flowers.map(f => Number(f.awake)).join(''), ui.paused].join(':');
  if (key === rendered) return; rendered = key;
  $('blooms').textContent = `${state.flowers.filter(f => f.awake).length} / ${state.flowers.length}`; $('shots').textContent = state.shots;
  $('garden-name').textContent = state.name; $('chapter-label').textContent = state.tutorial ? `LESSON ${state.level + 1} / 02` : `GARDEN 0${currentLevel + 1} / 05`;
  $('par').textContent = state.tutorial ? 'take your time' : `par ${state.par}`;
  $('launch').disabled = state.status !== 'ready'; $('recall').disabled = state.status !== 'flying';
  $('hint').textContent = state.status === 'flying' ? 'Little wings. Big possibilities.' : state.status === 'won' ? 'Every flower has a smile.' : state.tutorial && state.level === 1 ? 'Aim at the dewdrop. Bounce back to the flower.' : state.tutorial ? 'Pull away from the flower. Release to fly.' : state.wind.x || state.wind.y ? 'A little breeze! The dots show your path.' : 'Pull anywhere. Let go to fly.';
  $('lesson-dot').textContent = state.tutorial ? state.level + 1 : '↗';
  for (const b of $('garden-dots').children) { b.setAttribute('aria-pressed', String(!state.tutorial && Number(b.dataset.level) === currentLevel)); b.disabled = state.tutorial; }
}
GARDENS.forEach((garden, i) => { const b = document.createElement('button'); b.textContent = i + 1; b.dataset.level = i; b.setAttribute('aria-label', `Garden ${i + 1}: ${garden.name}`); b.addEventListener('click', () => { if (!ui.paused) start(i); }); $('garden-dots').append(b); });
function point(event) { const r = $('world').getBoundingClientRect(); return scene.toLogical(event.clientX - r.left - 3, event.clientY - r.top - 3); }
function cancelDrag() { drag = null; ui.pull = null; ui.preview = []; }
$('world').addEventListener('pointerdown', event => {
  if (ui.paused || state.status !== 'ready' || event.button !== 0 || drag) return;
  drag = { id: event.pointerId, start: point(event) }; $('world').setPointerCapture(event.pointerId); ui.pull = { x: 0, y: 0 }; ui.preview = [];
});
$('world').addEventListener('pointermove', event => {
  if (!drag || event.pointerId !== drag.id) return;
  const p = point(event); ui.pull = { x: p.x - drag.start.x, y: p.y - drag.start.y }; ui.preview = trajectory(state, ui.pull); lastPull = { ...ui.pull };
});
$('world').addEventListener('pointerup', event => { if (!drag || event.pointerId !== drag.id) return; const pull = ui.pull; cancelDrag(); if (pull) launch(state, pull); render(); });
$('world').addEventListener('pointercancel', cancelDrag);
$('world').addEventListener('lostpointercapture', cancelDrag);
$('launch').addEventListener('click', () => { if (!ui.paused) { launch(state, lastPull); cancelDrag(); render(); } });
$('recall').addEventListener('click', () => { if (!ui.paused) { recall(state); render(); } });
$('reset').addEventListener('click', () => { if (!ui.paused) state.tutorial ? startTutorial(state.level) : start(currentLevel); });
function help() {
  if ($('modal').open) return;
  openModal('A garden breather.', 'Pull in any direction, then release. Follow the dots. Dewdrops bounce; flowers stay awake. Arrow keys aim, Space flies.', [{ label: 'Back to the bee', action: () => { ui.paused = false; render(); } }, { label: 'Practice the moves', action: () => startTutorial(), secondary: true }, { label: 'Restart garden', action: () => start(currentLevel), secondary: true }]);
}
$('help').addEventListener('click', help);
$('sound').addEventListener('click', () => { ui.sound = !ui.sound; $('sound').setAttribute('aria-pressed', ui.sound); $('sound').setAttribute('aria-label', ui.sound ? 'Turn sound off' : 'Turn sound on'); tone(660); });
$('modal').addEventListener('cancel', event => { event.preventDefault(); });
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') { if (!$('modal').open) help(); return; }
  if (ui.paused || event.target.closest('button,a') || state.status !== 'ready') return;
  if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', ' '].includes(event.key)) event.preventDefault();
  if (event.key === ' ') { launch(state, lastPull); cancelDrag(); }
  else if (event.key.startsWith('Arrow')) {
    let angle = Math.atan2(-lastPull.y, -lastPull.x), power = Math.hypot(lastPull.x, lastPull.y) || 65;
    if (event.key === 'ArrowLeft') angle -= .12; if (event.key === 'ArrowRight') angle += .12;
    if (event.key === 'ArrowUp') power = Math.min(96, power + 7); if (event.key === 'ArrowDown') power = Math.max(15, power - 7);
    lastPull = { x: -Math.cos(angle) * power, y: -Math.sin(angle) * power }; ui.pull = lastPull; ui.preview = trajectory(state, lastPull);
  }
  render();
});
document.addEventListener('visibilitychange', () => { if (document.hidden) { cancelDrag(); if (!$('modal').open) help(); } });
matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', e => { ui.motion = !e.matches; });
render();
openModal('Small bee. Big adventures.', 'Pull back, let go, and give the garden a little joy.', [{ label: read('learned') ? 'Play a little round' : 'Show me how', action: () => read('learned') ? start(0) : startTutorial() }, { label: read('learned') ? 'Practice the moves' : 'Straight to the garden', action: () => read('learned') ? startTutorial() : start(0), secondary: true }], { art: true, kicker: 'WELCOME TO THE CLUB' });
if (new URLSearchParams(location.search).has('test')) window.__pollenClub = { snapshot: () => structuredClone(state), start, tutorial: startTutorial, advance: seconds => { if (!ui.paused) tick(state, seconds); render(); }, point: p => scene.toScreen(p), get paused() { return ui.paused; } };
