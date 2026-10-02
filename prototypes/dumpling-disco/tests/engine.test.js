import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createGame, press, release, tick, rating, makeNotes } from '../engine.js';
import { MIXES } from '../balance.js';

test('the tutorial waits at both judgement lines until the player performs tap and hold', () => {
  const s = createGame(0, true); tick(s, 30); assert.equal(s.time, 2); assert.equal(s.missed, 0); assert.ok(press(s)); assert.equal(s.lesson, 1);
  tick(s, 30); assert.equal(s.time, 5); press(s); tick(s, .3); release(s); assert.equal(s.notes[1].status, 'waiting'); assert.equal(s.time, 5);
  press(s); tick(s, 1.3); assert.equal(s.status, 'finished'); assert.equal(s.lesson, 2); assert.equal(s.perfect, 2);
});
test('tap timing distinguishes perfect, good, early inputs and missed notes', () => {
  for (const [offset, grade] of [[.1, 'perfect'], [.18, 'good']]) { const s = createGame(); tick(s, s.notes[0].time + offset); assert.ok(press(s)); assert.equal(s.notes[0].grade, grade); }
  const early = createGame(); tick(early, 1); assert.equal(press(early), false); assert.equal(early.score, 0);
  const late = createGame(); tick(late, late.notes[0].time + .23); assert.equal(late.notes[0].grade, 'miss'); assert.equal(press(late), false);
});
test('repeated taps cannot score one beat twice, and a miss breaks a streak', () => {
  const s = createGame(); tick(s, s.notes[0].time); press(s); for (let i = 0; i < 10; i++) press(s);
  assert.equal(s.score, 100); assert.equal(s.combo, 1); tick(s, s.notes[1].time - s.time + .23); assert.equal(s.combo, 0); assert.equal(s.bestCombo, 1);
});
test('early steam release misses; holding through the end awards exactly once', () => {
  for (const complete of [false, true]) {
    const s = createGame(), hold = s.notes.find(n => n.kind === 'hold'); tick(s, hold.time); press(s); assert.equal(s.held, hold.id);
    tick(s, complete ? hold.duration + .01 : hold.duration / 2); release(s); assert.equal(hold.grade, complete ? 'perfect' : 'miss');
    const score = s.score; release(s); press(s); assert.equal(s.score, score);
  }
});
test('holding through a beat works without a release at exactly the deadline', () => {
  const s = createGame(), n = s.notes.find(n => n.kind === 'hold'); tick(s, n.time); press(s); tick(s, n.duration);
  assert.equal(n.status, 'done'); assert.equal(n.grade, 'perfect'); assert.equal(s.held, null);
});
test('every mix supports a full perfect run, ends once, and rates results from earned score', () => {
  MIXES.forEach((_, mix) => {
    const s = createGame(mix); assert.ok(makeNotes(mix).every((n, i, notes) => i === 0 || n.time > notes[i - 1].time + notes[i - 1].duration));
    for (const n of s.notes) { tick(s, n.time - s.time); press(s); if (n.duration) tick(s, n.duration); }
    tick(s, 3); assert.equal(s.status, 'finished'); assert.equal(s.perfect, s.notes.length); assert.equal(s.score, s.notes.length * 100); assert.equal(rating(s), 3);
    const before = structuredClone(s); assert.equal(press(s), false); tick(s, 100); assert.deepEqual(s, before);
    s.score = s.notes.length * 65; assert.equal(rating(s), 2); s.score = 0; assert.equal(rating(s), 1);
  });
});
