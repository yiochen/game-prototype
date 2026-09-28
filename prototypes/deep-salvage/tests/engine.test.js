import test from 'node:test';
import assert from 'node:assert/strict';
import { BALANCE as B } from '../balance.js';
import { createState, traceCircuit, rotatePart, movePart, spawnDrop, tick, startDive, rebuild } from '../engine.js';

const part = (type, rotation = 0) => ({ type, rotation });
const empty = () => Array(36).fill(null);

test('guns accept every incoming direction in every rotation across empty space', () => {
  const sources = [{ index: 2, direction: 2 }, { index: 16, direction: 3 }, { index: 32, direction: 0 }, { index: 12, direction: 1 }];
  for (const { index, direction } of sources) for (let rotation = 0; rotation < 4; rotation++) {
    const grid = empty(); grid[index] = part('reactor', direction); grid[14] = part('gun', rotation);
    const circuit = traceCircuit(grid);
    assert.deepEqual(circuit.guns, [{ index: 14, power: B.reactorPower, piercing: false }]);
    assert.deepEqual(circuit.blocked, []);
  }
});

test('beams from different sides combine into one gun and preserve piercing', () => {
  const grid = empty(); grid[14] = part('gun', 1);
  grid[2] = part('reactor', 2); grid[32] = part('reactor');
  grid[12] = part('reactor', 1); grid[16] = part('reactor', 3);
  grid[20] = part('lens');
  assert.deepEqual(traceCircuit(grid).guns, [{ index: 14, power: B.reactorPower * 4, piercing: true }]);
});

test('amplifiers and lenses accept all four sides and preserve beam direction', () => {
  const routes = [{ source: 2, direction: 2, gun: 32 }, { source: 16, direction: 3, gun: 12 }, { source: 32, direction: 0, gun: 2 }, { source: 12, direction: 1, gun: 16 }];
  for (const type of ['amplifier', 'lens']) for (const route of routes) for (let rotation = 0; rotation < 4; rotation++) {
    const grid = empty();
    grid[route.source] = part('reactor', route.direction); grid[14] = part(type, rotation); grid[route.gun] = part('gun');
    assert.deepEqual(traceCircuit(grid).guns, [{ index: route.gun, power: B.reactorPower * (type === 'amplifier' ? B.amplifier : 1), piercing: type === 'lens' }]);
  }
});

test('splitters accept all four sides and branch perpendicular to each incoming beam', () => {
  for (const [source, direction] of [[2, 2], [16, 3], [32, 0], [12, 1]]) for (let rotation = 0; rotation < 4; rotation++) {
    const grid = empty(), outputs = direction % 2 ? [2, 32] : [12, 16];
    grid[source] = part('reactor', direction); grid[14] = part('splitter', rotation);
    for (const index of outputs) grid[index] = part('gun');
    const guns = traceCircuit(grid).guns.sort((a, b) => a.index - b.index);
    assert.deepEqual(guns, outputs.map(index => ({ index, power: B.reactorPower / 2, piercing: false })));
  }
});

test('only reactors and mirrors rotate; rotating the reactor changes the beam path', () => {
  const state = createState();
  for (const type of ['amplifier', 'lens', 'splitter', 'gun']) {
    state.grid[14] = part(type);
    assert.equal(rotatePart(state, 14), false);
    assert.equal(state.grid[14].rotation, 0);
  }
  state.grid[14] = null;
  assert.equal(rotatePart(state, 32), true);
  assert.equal(state.circuit.guns.length, 0);
  state.grid[13] = part('mirror');
  assert.equal(rotatePart(state, 13), true); assert.equal(state.grid[13].rotation, 1);
});

test('splitter feedback terminates when a ray revisits a directed component', () => {
  const grid = empty(); grid[32] = part('reactor'); grid[14] = part('splitter');
  grid[15] = part('mirror'); grid[9] = part('mirror', 1); grid[8] = part('mirror');
  const circuit = traceCircuit(grid);
  assert.ok(circuit.blocked.includes(15)); assert.ok(circuit.segments.length < 30);
});

test('beams cross empty space and amplify in order', () => {
  const state = createState();
  assert.equal(state.circuit.guns[0].power, 12);
  assert.equal(state.circuit.guns[0].index, 2);
  assert.equal(rotatePart(state, 20), false);
  assert.equal(state.circuit.guns[0].power, 12);
  state.grid[20] = null; rebuild(state);
  assert.equal(state.circuit.guns[0].power, 8);
});

test('splitter conserves power and mirrors route into independently powered guns', () => {
  const grid = empty();
  grid[32] = part('reactor'); grid[20] = part('amplifier'); grid[14] = part('splitter');
  grid[13] = part('mirror', 1); grid[15] = part('mirror');
  grid[1] = part('gun'); grid[3] = part('gun');
  const split = traceCircuit(grid);
  assert.equal(split.guns.length, 2);
  assert.equal(split.guns.reduce((sum, gun) => sum + gun.power, 0), 12);
  grid[7] = part('amplifier');
  assert.equal(traceCircuit(grid).guns.find(gun => gun.index === 1).power, 9);
  assert.equal(traceCircuit(grid).guns.find(gun => gun.index === 3).power, 6);
});

test('lens changes only the branch that passes through it', () => {
  const grid = empty();
  grid[32] = part('reactor'); grid[14] = part('splitter');
  grid[13] = part('mirror', 1); grid[15] = part('mirror'); grid[9] = part('lens');
  grid[1] = part('gun'); grid[3] = part('gun');
  assert.equal(traceCircuit(grid).guns.find(gun => gun.index === 3).piercing, true);
  assert.equal(traceCircuit(grid).guns.find(gun => gun.index === 1).piercing, false);
});

test('crossing beams stay independent and outward rays terminate at grid boundaries', () => {
  const grid = empty(); grid[32] = part('reactor'); grid[12] = part('reactor', 1);
  grid[2] = part('gun'); grid[16] = part('gun', 1);
  const result = traceCircuit(grid);
  assert.equal(result.guns.length, 2);
  assert.deepEqual(result.guns.map(g => g.power), [8, 8]);
  grid[2] = null; grid[16] = null;
  assert.equal(traceCircuit(grid).guns.length, 0);
  assert.ok(traceCircuit(grid).segments.length < 15);
});

test('dense circuits terminate and amplification is capped', () => {
  const grid = Array.from({ length: 36 }, (_, i) => part('mirror', i % 4)); grid[32] = part('reactor');
  assert.ok(traceCircuit(grid).segments.length < 512);
  const state = createState(); state.grid[14] = part('amplifier'); state.grid[8] = part('amplifier'); rebuild(state);
  assert.equal(state.circuit.guns[0].power, 27);
  assert.ok(state.circuit.guns[0].power <= B.powerCap);
});

test('inventory moves are atomic, stacked copies stay in storage, and rotation is preserved', () => {
  const state = createState();
  assert.equal(movePart(state, { kind: 'storage', type: 'mirror' }, { kind: 'grid', index: 32 }), false);
  assert.equal(state.inventory.mirror, 2);
  assert.equal(movePart(state, { kind: 'storage', type: 'mirror' }, { kind: 'grid', index: 13 }), true);
  assert.equal(state.inventory.mirror, 1);
  rotatePart(state, 13);
  assert.equal(movePart(state, { kind: 'grid', index: 13 }, { kind: 'grid', index: 15 }), true);
  assert.equal(state.grid[15].rotation, 1);
  assert.equal(state.grid[13], null);
  assert.equal(movePart(state, { kind: 'grid', index: 15 }, { kind: 'storage' }), true);
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
  const state = createState(); state.grid[14] = part('lens'); rebuild(state); startDive(state);
  state.spawnIn = 100;
  state.enemies = [1, 2].map(id => ({ id, type: 'crab', ...B.enemies.crab, hp: 62, maxHp: 62, x: 0.6 + id * 0.1, y: 0.4, attackIn: 2 }));
  tick(state, 0.01);
  for (const enemy of state.enemies) assert.ok(Math.abs(enemy.hp - (62 - 12 * B.laserDamagePerEnergy * .01)) < 1e-8);
});

test('disconnected weapons lead to loss; an upgraded machine can complete all three waves', () => {
  const lost = createState(); lost.grid[2] = null; rebuild(lost); startDive(lost); tick(lost, 180);
  assert.equal(lost.status, 'lost'); assert.equal(lost.hull, 0);
  const won = createState(); won.grid[14] = part('amplifier2'); won.grid[8] = part('lens'); rebuild(won); startDive(won); tick(won, 180);
  assert.equal(won.status, 'won'); assert.equal(won.wave, 2); assert.equal(won.kills, 39);
  const finalTime = won.elapsed; tick(won, 1); assert.equal(won.elapsed, finalTime);
});

test('later waves require engineering, while the opening wave gives time to salvage', () => {
  const state = createState(); startDive(state); tick(state, 25);
  assert.equal(state.hull, 100); assert.ok(state.kills >= 4);
  tick(state, 155);
  assert.equal(state.status, 'lost'); assert.equal(state.wave, 1);
});
