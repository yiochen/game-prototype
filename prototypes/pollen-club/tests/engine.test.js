import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createGame, launch, tick, recall, trajectory, medal } from '../engine.js';
import { GARDENS } from '../balance.js';

test('both lessons are completable and the second requires a real dewdrop bounce', () => {
  for (let level = 0; level < 2; level++) { const s = createGame(level, true); assert.ok(launch(s, { x: 0, y: level ? 85 : 65 })); tick(s, 7); assert.equal(s.status, 'won'); assert.equal(s.shots, 1); if (level) assert.ok(s.bounces >= 1); }
});
test('a launch is committed once, short pulls and invalid vectors leave the garden intact', () => {
  const s = createGame(), before = structuredClone(s);
  for (const pull of [{ x: 0, y: 0 }, { x: NaN, y: 30 }, { x: 30, y: Infinity }]) assert.equal(launch(s, pull), false);
  assert.deepEqual(s, before); launch(s, { x: 25, y: 70 }); assert.equal(launch(s, { x: 1, y: 80 }), false); assert.equal(s.shots, 1);
});
test('flight results do not depend on render frame rate, and over-pulling caps power', () => {
  const a = createGame(), b = createGame(); launch(a, { x: 70, y: 50 }); launch(b, { x: 70, y: 50 });
  tick(a, .6); for (let i = 0; i < 36; i++) tick(b, 1 / 60);
  assert.deepEqual(a.bee, b.bee); assert.deepEqual(a.flowers, b.flowers);
  const c = createGame(), d = createGame(); launch(c, { x: 0, y: 96 }); launch(d, { x: 0, y: 1000 }); assert.equal(c.bee.vy, d.bee.vy);
});
test('every aiming dot agrees with the actual wind and collision simulation without mutating it', () => {
  const s = createGame(2), before = structuredClone(s), pull = { x: 44, y: 73 }, dots = trajectory(s, pull);
  assert.deepEqual(s, before); launch(s, pull);
  for (const dot of dots) { tick(s, .045); assert.ok(Math.abs(s.bee.x - dot.x) < 1e-8); assert.ok(Math.abs(s.bee.y - dot.y) < 1e-8); }
});
test('recall returns the bee while keeping flowers awake and retries available', () => {
  const s = createGame(); launch(s, { x: 0, y: 65 }); tick(s, .8); assert.ok(s.flowers[0].awake); assert.ok(recall(s));
  assert.equal(s.status, 'ready'); assert.equal(s.bee.x, s.home.x); assert.equal(s.bee.y, s.home.y); assert.ok(s.flowers[0].awake);
  assert.ok(launch(s, { x: 0, y: 65 })); tick(s, .8); assert.equal(s.events.filter(e => e.type === 'bloom' && e.id === 0).length, 1);
});
test('all five gardens have a reproducible one-flight solution, with medals for gentler play too', () => {
  const solutions = [[95.86843533643909, 5.024251799322608], [93.90216967044535, 19.959522318504895], [94.81808069713323, 15.017708643862164], [59.380454746769054, 26.43788179992701], [46.67902132486009, 17.918397477265014]];
  GARDENS.forEach((_, level) => { const s = createGame(level); launch(s, { x: solutions[level][0], y: solutions[level][1] }); tick(s, 7); assert.equal(s.status, 'won'); assert.equal(medal(s), 3); assert.equal(launch(s, { x: 0, y: 65 }), false); s.shots = s.par + 1; assert.equal(medal(s), 2); s.shots = s.par + 3; assert.equal(medal(s), 1); });
});
