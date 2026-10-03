import { BALANCE as B, MIXES } from './balance.js';

export function makeNotes(mixIndex) {
  const mix = MIXES[mixIndex % MIXES.length], beat = 60 / mix.bpm;
  let time = 2.4;
  return mix.pattern.map((kind, id) => {
    const duration = kind === 'hold' ? beat * 1.5 : 0;
    const note = { id, kind, time, duration, status: 'waiting', grade: null };
    time += beat * (kind === 'hold' ? 3 : id % 4 === 3 ? 2 : 1.5);
    return note;
  });
}
export function createGame(mix = 0, tutorial = false) {
  const notes = tutorial ? [{ id: 0, kind: 'tap', time: 2, duration: 0, status: 'waiting' }, { id: 1, kind: 'hold', time: 5, duration: 1.2, status: 'waiting' }] : makeNotes(mix);
  return { mix, tutorial, notes, time: 0, score: 0, combo: 0, bestCombo: 0, perfect: 0, good: 0, missed: 0, status: 'playing', held: null, events: [], lesson: 0 };
}
function award(state, note, grade) {
  note.status = 'done'; note.grade = grade; state.held = null;
  if (grade === 'miss') { state.combo = 0; state.missed++; }
  else { state.combo++; state[grade]++; state.score += grade === 'perfect' ? 100 : 65; state.bestCombo = Math.max(state.bestCombo, state.combo); }
  state.events.push({ type: grade, id: note.id, kind: note.kind });
  if (state.tutorial) state.lesson = note.id + 1;
}
export function press(state) {
  if (state.status !== 'playing' || state.held !== null) return false;
  const note = state.notes.find(n => n.status === 'waiting' && Math.abs(n.time - state.time) <= B.good);
  if (!note) { state.events.push({ type: 'empty' }); return false; }
  const grade = Math.abs(note.time - state.time) <= B.perfect ? 'perfect' : 'good';
  if (note.kind === 'hold') { note.status = 'holding'; note.grade = grade; state.held = note.id; state.events.push({ type: 'steam', id: note.id }); }
  else award(state, note, grade);
  return true;
}
export function release(state) {
  if (state.held === null || state.status !== 'playing') return false;
  const note = state.notes[state.held];
  if (state.time >= note.time + note.duration - B.holdGrace) award(state, note, note.grade);
  else if (state.tutorial) { note.status = 'waiting'; note.grade = null; state.held = null; state.time = note.time; state.events.push({ type: 'retry' }); }
  else award(state, note, 'miss');
  return true;
}
export function tick(state, dt) {
  if (state.status !== 'playing' || !Number.isFinite(dt) || dt <= 0) return;
  let next = state.time + dt;
  // Lessons wait for the player's action at the actual judgement line.
  if (state.tutorial) {
    const waiting = state.notes.find(n => n.status === 'waiting');
    if (waiting) next = Math.min(next, waiting.time);
  }
  state.time = next;
  for (const note of state.notes) {
    if (note.status === 'holding' && state.time >= note.time + note.duration) award(state, note, note.grade);
    else if (!state.tutorial && note.status === 'waiting' && state.time > note.time + B.good) award(state, note, 'miss');
  }
  const last = state.notes.at(-1);
  if (state.tutorial ? state.lesson === 2 : state.time > last.time + last.duration + B.finishTail) {
    state.status = 'finished'; state.events.push({ type: 'finish' });
  }
}
export function rating(state) {
  const ratio = state.score / (state.notes.length * 100);
  return ratio >= 0.85 ? 3 : ratio >= 0.5 ? 2 : 1;
}
