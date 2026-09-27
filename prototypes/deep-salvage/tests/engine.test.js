import test from 'node:test';
import assert from 'node:assert/strict';
import { BALANCE as B } from '../balance.js';
import { createState, traceCircuit, rotatePart, movePart, spawnDrop, tick, startDive, rebuild } from '../engine.js';

const part = (type, rotation = 0) => ({ type, rotation });
const empty = () => Array(25).fill(null);

test('beams cross empty space, amplify in order, and require the correct inlet', () => {
  const state = createState();
  assert.equal(state.circuit.guns[0].power, 12);
  assert.equal(state.circuit.guns[0].index, 2);
  rotatePart(state, 17);
  assert.equal(state.circuit.guns.length, 0);
  assert.ok(state.circuit.blocked.includes(17));
  for (let i = 0; i < 3; i++) rotatePart(state, 17);
  assert.equal(state.circuit.guns[0].power, 12);
  state.grid[17] = null; rebuild(state);
  assert.equal(state.circuit.guns[0].power, 8);
});

test('splitter conserves power and mirrors route into independently powered guns', () => {
  const grid = empty();
  grid[22] = part('reactor'); grid[17] = part('amplifier'); grid[12] = part('splitter');
  grid[11] = part('mirror', 1); grid[13] = part('mirror');
  grid[1] = part('gun'); grid[3] = part('gun');
  const split = traceCircuit(grid);
  assert.equal(split.guns.length, 2);
  assert.equal(split.guns.reduce((sum, gun) => sum + gun.power, 0), 12);
  grid[6] = part('amplifier');
  assert.equal(traceCircuit(grid).guns.find(gun => gun.index === 1).power, 9);
  assert.equal(traceCircuit(grid).guns.find(gun => gun.index === 3).power, 6);
});

test('lens changes only the branch that passes through it', () => {
  const grid = empty();
  grid[22] = part('reactor'); grid[12] = part('splitter');
  grid[11] = part('mirror', 1); grid[13] = part('mirror'); grid[8] = part('lens');
  grid[1] = part('gun'); grid[3] = part('gun');
  assert.equal(traceCircuit(grid).guns.find(gun => gun.index === 3).piercing, true);
  assert.equal(traceCircuit(grid).guns.find(gun => gun.index === 1).piercing, false);
});

test('crossing beams stay independent and outward rays terminate at grid boundaries', () => {
  const grid = empty(); grid[22] = part('reactor'); grid[10] = part('reactor', 1);
  grid[2] = part('gun'); grid[14] = part('gun', 1);
  const result = traceCircuit(grid);
  assert.equal(result.guns.length, 2);
  assert.deepEqual(result.guns.map(g => g.power), [8, 8]);
  grid[2] = null; grid[14] = null;
  assert.equal(traceCircuit(grid).guns.length, 0);
  assert.ok(traceCircuit(grid).segments.length < 15);
});

test('dense circuits terminate and amplification is capped', () => {
  const grid = Array.from({ length: 25 }, (_, i) => part('mirror', i % 4)); grid[22] = part('reactor');
  assert.ok(traceCircuit(grid).segments.length < 512);
  const state = createState(); state.grid[12] = part('amplifier'); state.grid[7] = part('amplifier'); rebuild(state);
  assert.equal(state.circuit.guns[0].power, 27);
  assert.ok(state.circuit.guns[0].power <= B.powerCap);
});

test('inventory moves are atomic, stacked copies stay in storage, and rotation is preserved', () => {
  const state = createState();
  assert.equal(movePart(state, { kind: 'storage', type: 'mirror' }, { kind: 'grid', index: 22 }), false);
  assert.equal(state.inventory.mirror, 2);
  assert.equal(movePart(state, { kind: 'storage', type: 'mirror' }, { kind: 'grid', index: 11 }), true);
  assert.equal(state.inventory.mirror, 1);
  rotatePart(state, 11);
  assert.equal(movePart(state, { kind: 'grid', index: 11 }, { kind: 'grid', index: 13 }), true);
  assert.equal(state.grid[13].rotation, 1);
  assert.equal(state.grid[11], null);
  assert.equal(movePart(state, { kind: 'grid', index: 13 }, { kind: 'storage' }), true);
  assert.equal(state.inventory.mirror, 2);
  assert.equal(movePart(state, { kind: 'storage', type: 'lens' }, { kind: 'grid', index: 3 }), false);
});

test('first acquired type queues one discovery, later duplicates stack without interruption', () => {
  const state = createState();
  const a = spawnDrop(state, 'splitter'), b = spawnDrop(state, 'splitter');
  movePart(state, { kind: 'drop', id: a.id }, { kind: 'storage' });
  movePart(state, { kind: 'drop', id: b.id }, { kind: 'storage' });
  assert.deepEqual(state.discoveries, ['splitter']);
  assert.equal(state.inventory.splitter, 2);
  assert.equal(state.drops.length, 0);
  assert.ok(createState([...state.discovered]).discovered.has('splitter'));
});

test('loot falls before aging, flashes near expiry, and held or paused loot cannot expire', () => {
  const state = createState(); startDive(state);
  const drop = spawnDrop(state, 'lens', 0.5, 0.2);
  tick(state, 0.1); assert.equal(drop.life, B.lootLife); assert.ok(drop.y > 0.2);
  drop.landed = true; drop.y = B.floor; drop.life = 0.1;
  state.heldDrop = drop.id; tick(state, 1); assert.ok(state.drops.includes(drop)); assert.equal(drop.life, 0.1);
  state.heldDrop = null; state.paused = true; const time = state.elapsed; tick(state, 10);
  assert.equal(state.elapsed, time); assert.equal(drop.life, 0.1);
  state.paused = false; tick(state, 0.2); assert.ok(!state.drops.includes(drop));
});

test('combat fires automatically, kills an enemy and drops a splitter first', () => {
  const state = createState(); startDive(state); tick(state, 7);
  assert.ok(state.kills >= 1); assert.equal(state.drops[0].type, 'splitter');
  assert.equal(state.submarine.x, B.submarine.x);
});

test('piercing bypasses armor and damages a second target', () => {
  const state = createState(); state.grid[12] = part('lens'); rebuild(state); startDive(state);
  state.spawnIn = 100;
  state.enemies = [1, 2].map(id => ({ id, type: 'crab', ...B.enemies.crab, hp: 62, maxHp: 62, x: 0.6 + id * 0.1, y: 0.4, attackIn: 2 }));
  tick(state, 0.01);
  assert.deepEqual(state.enemies.map(e => e.hp), [50, 50]);
});

test('disconnected weapons lead to loss; an upgraded machine can complete all three waves', () => {
  const lost = createState(); lost.grid[2] = null; rebuild(lost); startDive(lost); tick(lost, 180);
  assert.equal(lost.status, 'lost'); assert.equal(lost.hull, 0);
  const won = createState(); won.grid[12] = part('amplifier'); won.grid[7] = part('lens'); rebuild(won); startDive(won); tick(won, 180);
  assert.equal(won.status, 'won'); assert.equal(won.wave, 2); assert.equal(won.kills, 24);
  const finalTime = won.elapsed; tick(won, 1); assert.equal(won.elapsed, finalTime);
});

test('later waves require engineering, while the opening wave gives time to salvage', () => {
  const state = createState(); startDive(state); tick(state, 25);
  assert.equal(state.hull, 100); assert.ok(state.kills >= 4);
  tick(state, 155);
  assert.equal(state.status, 'lost'); assert.equal(state.wave, 2);
});
