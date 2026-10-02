import './style.css';
import { createGame, press, release, tick, rating } from './engine.js';
import { MIXES } from './balance.js';
import { mountWorld } from './world.js';

const $ = id => document.getElementById(id);
const read = key => { try { return localStorage.getItem(`dumpling-disco:${key}`); } catch { return null; } };
const save = (key, value) => { try { localStorage.setItem(`dumpling-disco:${key}`, value); } catch { /* Storage is optional. */ } };
let state = createGame(), mix = 0, audio, resultShown = false, heldPointer = null, heldKey = false, lastBeat = -1, feedback = '', feedbackFor = 0, rendered = '';
const ui = { paused: true, motion: !matchMedia('(prefers-reduced-motion: reduce)').matches, sound: false };
const { scene } = mountWorld(() => state, () => ui, dt => {
  if (ui.paused || document.hidden) return;
  tick(state, dt); feedbackFor = Math.max(0, feedbackFor - dt);
  const beat = Math.floor(state.time / (60 / MIXES[state.mix].bpm));
  if (beat !== lastBeat) { lastBeat = beat; if (!state.tutorial) tone([261.63, 329.63, 392, 329.63][beat % 4], .09, beat % 4 ? .018 : .027); }
  for (const event of state.events.splice(0)) {
    scene.emit(event);
    if (event.type === 'perfect' || event.type === 'good') { feedback = event.type === 'perfect' ? 'Lovely!' : 'Looking good!'; feedbackFor = .7; tone(event.kind === 'hold' ? 784 : 523.25, .15, .05); }
    if (event.type === 'miss') { feedback = 'Keep dancing.'; feedbackFor = .65; }
    if (event.type === 'retry') { feedback = 'Hold a little longer. You’ve got this.'; feedbackFor = 1.2; }
  }
  render();
  if (state.status === 'finished' && !resultShown) {
    resultShown = true; cancelInput();
    if (state.tutorial) { save('learned', 'yes'); openModal('Ready to groove.', 'Thin golden rings: tap. Thick green rings: hold until the rim fills. Let’s cook!', [{ label: 'Let’s dance', action: () => start(0) }], { stars: 3, kicker: 'TUTORIAL COMPLETE' }); }
    else { const best = Math.max(Number(read(`best:${mix}`) || 0), state.score); save(`best:${mix}`, best); openModal(state.perfect >= state.notes.length * .8 ? 'Chef’s kiss!' : 'A delicious little set.', `${state.perfect} lovely beats · ${state.bestCombo} best streak · ${state.score} groove`, [{ label: mix === MIXES.length - 1 ? 'Back to brunch' : 'Next mix →', action: () => start((mix + 1) % MIXES.length) }, { label: 'One more dance', action: () => start(mix), secondary: true }], { stars: rating(state), kicker: `PERSONAL BEST ${best}` }); }
  }
});
function tone(frequency, duration = .12, volume = .04) {
  if (!ui.sound) return;
  try { audio ||= new (window.AudioContext || window.webkitAudioContext)(); audio.resume(); const o = audio.createOscillator(), g = audio.createGain(); o.type = 'sine'; o.frequency.value = frequency; g.gain.setValueAtTime(volume, audio.currentTime); g.gain.exponentialRampToValueAtTime(.001, audio.currentTime + duration); o.connect(g); g.connect(audio.destination); o.start(); o.stop(audio.currentTime + duration); } catch { ui.sound = false; }
}
function cancelInput() { heldPointer = null; heldKey = false; $('pad').classList.remove('held'); }
function rewindHold() {
  if (state.held !== null) { const n = state.notes[state.held]; n.status = 'waiting'; n.grade = null; state.time = n.time; state.held = null; }
  cancelInput();
}
function openModal(title, copy, actions, options = {}) {
  ui.paused = true; rewindHold(); $('modal-title').textContent = title; $('modal-copy').textContent = copy; $('modal-kicker').textContent = options.kicker || 'TAKE A BREATHER';
  $('modal-art').hidden = !options.art; $('medal').hidden = !options.stars; $('medal').replaceChildren();
  if (options.stars) for (let i = 0; i < 3; i++) { const s = document.createElement('span'); s.textContent = '✦'; s.className = i < options.stars ? '' : 'dim'; $('medal').append(s); }
  $('modal-actions').replaceChildren(); for (const { label, action, secondary } of actions) { const b = document.createElement('button'); b.className = secondary ? 'secondary' : 'primary'; b.textContent = label; b.onclick = () => { $('modal').close(); action(); }; $('modal-actions').append(b); }
  if (!$('modal').open) $('modal').showModal();
}
function start(index = 0, tutorial = false) { mix = index; state = createGame(index, tutorial); ui.paused = false; resultShown = false; lastBeat = -1; feedbackFor = 0; scene.reset(); cancelInput(); render(); $('pad').focus({ preventScroll: true }); }
function render() {
  const next = state.notes.find(n => n.status === 'waiting' || n.status === 'holding');
  const key = [mix, state.tutorial, state.status, state.score, state.combo, state.lesson, state.held, next?.id, Boolean(next && next.time - state.time < 1.6), ui.paused, feedbackFor > 0 ? feedback : ''].join(':');
  if (key === rendered) return; rendered = key;
  $('score').textContent = state.score; $('combo').textContent = state.combo; $('mix-name').textContent = state.tutorial ? 'A taste of the beat' : MIXES[mix].name;
  $('chapter-label').textContent = state.tutorial ? `LESSON ${Math.min(2, state.lesson + 1)} / 02` : `MIX 0${mix + 1} / 03`; $('bpm').textContent = state.tutorial ? 'take your time' : `${MIXES[mix].bpm} bpm`;
  $('lesson-dot').textContent = state.tutorial ? Math.min(2, state.lesson + 1) : '♪';
  const holding = state.held !== null;
  $('hint').textContent = feedbackFor ? feedback : holding ? 'Keep holding. Fill the green rim.' : state.tutorial && state.lesson === 1 ? 'Hold on the green ring. Fill the rim.' : next?.kind === 'hold' && next.time - state.time < 1.6 ? 'Hold when the green ring meets the rim.' : 'Tap when the ring meets the golden rim.';
  $('pad-label').textContent = holding ? 'Keep steaming…' : next?.kind === 'hold' && next.time - state.time < 1.6 ? 'Hold to steam' : 'Tap to flip'; $('pad-symbol').textContent = holding ? '≋' : '⌁';
  $('pad').disabled = ui.paused || state.status !== 'playing';
  for (const b of $('mix-dots').children) { b.setAttribute('aria-pressed', String(Number(b.dataset.mix) === mix && !state.tutorial)); b.disabled = state.tutorial; }
}
MIXES.forEach((m, i) => { const b = document.createElement('button'); b.textContent = i + 1; b.dataset.mix = i; b.setAttribute('aria-label', `Mix ${i + 1}: ${m.name}`); b.onclick = () => { if (!ui.paused) start(i); }; $('mix-dots').append(b); });
function down() {
  if (ui.paused || state.status !== 'playing') return;
  if (!press(state)) { feedback = state.tutorial ? 'A little early. Release, then try again.' : 'Follow the ring. Try the next beat.'; feedbackFor = 1.1; }
  $('pad').classList.add('held'); render();
}
function up() { if (!ui.paused) release(state); cancelInput(); render(); }
$('pad').addEventListener('pointerdown', e => { if (e.button !== 0 || heldPointer !== null || ui.paused) return; heldPointer = e.pointerId; $('pad').setPointerCapture(e.pointerId); down(); });
$('pad').addEventListener('pointerup', e => { if (e.pointerId === heldPointer) up(); });
$('pad').addEventListener('pointercancel', e => { if (e.pointerId === heldPointer) up(); });
$('pad').addEventListener('lostpointercapture', () => { if (heldPointer !== null) up(); });
// Keyboard activation has a real press/release lifetime, just like touch.
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { if (!$('modal').open) help(); return; }
  if (ui.paused || e.repeat || heldKey || (e.key !== ' ' && !(e.key === 'Enter' && e.target === $('pad')))) return;
  if (e.target.closest('a,button') && e.target !== $('pad')) return;
  e.preventDefault(); heldKey = true; down();
});
document.addEventListener('keyup', e => { if ((e.key === ' ' || e.key === 'Enter') && heldKey) { e.preventDefault(); up(); } });
function help() {
  if ($('modal').open) return;
  openModal('A little intermission.', 'Tap when a thin ring meets the gold rim. Hold for a thick green ring. Space works too. Sound is optional.', [{ label: 'Back to the beat', action: () => { ui.paused = false; render(); $('pad').focus(); } }, { label: 'Practice the moves', action: () => start(0, true), secondary: true }, { label: 'Restart this mix', action: () => start(mix), secondary: true }]);
}
$('help').onclick = help;
$('sound').onclick = () => { ui.sound = !ui.sound; $('sound').setAttribute('aria-pressed', ui.sound); $('sound').setAttribute('aria-label', ui.sound ? 'Turn sound off' : 'Turn sound on'); tone(660); };
$('modal').addEventListener('cancel', e => e.preventDefault());
document.addEventListener('visibilitychange', () => { if (document.hidden && !$('modal').open) help(); });
window.addEventListener('blur', () => { if (!$('modal').open) help(); });
matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', e => { ui.motion = !e.matches; });
render(); openModal('A pinch of rhythm.', 'Follow the rings. Flip with a tap. Steam with a hold. Sound is optional.', [{ label: read('learned') ? 'Let’s dance' : 'Show me how', action: () => start(0, !read('learned')) }, { label: read('learned') ? 'Practice the moves' : 'Straight to the disco', action: () => start(0, Boolean(read('learned'))), secondary: true }], { art: true, kicker: 'THE PAN IS YOUR DANCE FLOOR' });
if (new URLSearchParams(location.search).has('test')) window.__dumplingDisco = { snapshot: () => structuredClone(state), start, advance: dt => { if (!ui.paused) tick(state, dt); render(); }, get paused() { return ui.paused; } };
