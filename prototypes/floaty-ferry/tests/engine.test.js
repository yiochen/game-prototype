import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createGame, connect, disconnect, nextHop, tick, addDuck, rating } from '../engine.js';
import { BALANCE as B } from '../balance.js';

const count = s => s.delivered + s.splashes + s.islands.reduce((n, i) => n + i.ducks.length, 0) + s.routes.reduce((n, r) => n + r.passengers.length, 0);
test('a captain learns two direct routes and a real boat transfer without random requests or expiry', () => {
  const s = createGame(true); tick(s, 50); assert.equal(s.lesson, 0); assert.equal(s.splashes, 0); assert.equal(s.nextDuck, 1);
  assert.equal(connect(s, 0, 2), false); assert.ok(connect(s, 0, 1)); tick(s, 5); assert.equal(s.lesson, 2);
  assert.ok(connect(s, 0, 2)); tick(s, 5); assert.equal(s.lesson, 4); assert.ok(s.events.some(e => e.type === 'spawn' && e.island === 1 && e.destination === 2));
  tick(s, 15); assert.equal(s.status, 'finished'); assert.equal(s.delivered, 3); assert.equal(count(s), s.nextDuck);
});
test('invalid routes, duplicates and route-budget overflow preserve all boats and ducks', () => {
  const s = createGame();
  for (const pair of [[0, 0], [-1, 2], [0, NaN], [0, 9], [0, 1.5]]) assert.equal(connect(s, ...pair), false);
  assert.ok(connect(s, 0, 1)); assert.equal(connect(s, 1, 0), false);
  for (const to of [2, 3, 4]) assert.ok(connect(s, 0, to)); assert.equal(connect(s, 0, 5), false); assert.equal(s.routes.length, B.initialRoutes); assert.equal(count(s), s.nextDuck);
});
test('ducklings follow shortest connected paths and deliver after changing boats', () => {
  const s = createGame(); connect(s, 0, 1); connect(s, 0, 2); addDuck(s, 1, 2);
  assert.equal(nextHop(s, 1, 2), 0); assert.equal(nextHop(s, 1, 5), null); tick(s, 15);
  assert.ok(s.events.some(e => e.type === 'deliver' && e.duck === 2)); assert.equal(count(s), s.nextDuck);
});
test('three-seat ferries board in queue order, and moving a route returns onboard ducks to its last shore', () => {
  const s = createGame(); for (let i = 0; i < 4; i++) addDuck(s, 0, 1); connect(s, 0, 1); tick(s, 1);
  assert.equal(s.routes[0].passengers.length, B.capacity); assert.deepEqual(s.routes[0].passengers.map(d => d.id), [0, 2, 3]);
  const before = count(s); assert.ok(disconnect(s, s.routes[0].id)); assert.equal(count(s), before); assert.equal(s.islands[0].ducks.length, 6); assert.equal(disconnect(s, 999), false);
});
test('eight happy arrivals unlock a fifth ferry and boats never duplicate ducklings', () => {
  const s = createGame(); connect(s, 0, 1); for (let i = 0; i < 10; i++) addDuck(s, 0, 1); tick(s, 24);
  assert.ok(s.delivered >= B.unlockAt); assert.equal(s.maxRoutes, 5); assert.equal(s.events.filter(e => e.type === 'upgrade').length, 1); assert.equal(count(s), s.nextDuck);
});
test('a day ends once; unserved ducks swim away without terminating play', () => {
  const s = createGame(); tick(s, B.patience + 1); assert.ok(s.splashes >= 2); assert.equal(s.status, 'playing'); assert.equal(count(s), s.nextDuck);
  tick(s, 100); assert.equal(s.status, 'finished'); assert.equal(s.time, B.duration); assert.equal(s.events.filter(e => e.type === 'finish').length, 1);
  const before = structuredClone(s); tick(s, 30); assert.equal(connect(s, 0, 1), false); assert.equal(disconnect(s, 0), false); assert.deepEqual(s, before);
  assert.equal(rating(s), 1); s.delivered = 12; assert.equal(rating(s), 2); s.delivered = 24; assert.equal(rating(s), 3);
});
test('the same route plan produces the same requests and voyages across frame rates', () => {
  const a = createGame(), b = createGame(); for (const s of [a, b]) { connect(s, 0, 1); connect(s, 0, 2); connect(s, 1, 3); connect(s, 2, 4); }
  tick(a, 20); for (let i = 0; i < 600; i++) tick(b, 1 / 30);
  assert.deepEqual(a.routes, b.routes); assert.deepEqual(a.islands, b.islands); assert.equal(a.delivered, b.delivered); assert.equal(count(a), a.nextDuck);
});
