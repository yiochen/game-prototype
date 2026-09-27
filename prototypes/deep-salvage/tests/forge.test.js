import test from 'node:test';
import assert from 'node:assert/strict';
import { BALANCE as B } from '../balance.js';
import { RECIPES, findRecipe } from '../recipes.js';
import { createState, startDive, movePart, startForge, forgeMatches, tick, rebuild, traceCircuit, rotatePart } from '../engine.js';
const part = (type, rotation = 0) => ({ type, rotation });
const add = (s, type) => movePart(s, { kind: 'storage', type }, { kind: 'forge' });

test('every recipe accepts either order, charges once, locks ingredients, and creates exactly one upgrade', () => {
  for (const recipe of RECIPES) for (const ingredients of [recipe.ingredients, [...recipe.ingredients].reverse()]) {
    const s = createState(); startDive(s); s.cash = recipe.cost; s.spawnIn = 100; s.inventory[recipe.output] = 0; s.discovered.delete(recipe.output);
    for (const type of ingredients) s.inventory[type] = (s.inventory[type] || 0) + 1;
    for (const type of ingredients) assert.equal(add(s, type), true);
    assert.equal(findRecipe(...ingredients).output, recipe.output);
    assert.equal(startForge(s), true); assert.equal(s.cash, 0);
    assert.equal(startForge(s), false);
    assert.equal(movePart(s, { kind: 'forge', index: 0 }, { kind: 'storage' }), false);
    tick(s, recipe.seconds - 1); assert.equal(s.inventory[recipe.output] || 0, 0);
    s.paused = true; const remaining = s.forge.job.remaining; tick(s, 20); assert.equal(s.forge.job.remaining, remaining);
    s.paused = false; tick(s, 1.1);
    assert.equal(s.inventory[recipe.output], 1); assert.equal(s.forged, 1);
    assert.deepEqual(s.forge, { slots: [null, null, null, null], job: null });
    assert.deepEqual(s.discoveries, [recipe.output]);
    tick(s, 2); assert.equal(s.inventory[recipe.output], 1);
  }
});

test('forge highlights duplicate and mixed matches; invalid and unaffordable operations are atomic', () => {
  const s = createState(); startDive(s); s.cash = 0;
  assert.equal(add(s, 'amplifier'), true);
  assert.deepEqual([...forgeMatches(s)].sort(), ['amplifier', 'lens']);
  assert.equal(add(s, 'mirror'), false); assert.equal(s.inventory.mirror, 2);
  assert.equal(add(s, 'amplifier'), true); assert.deepEqual([...forgeMatches(s)], ['lens']);
  assert.equal(startForge(s), false); assert.equal(s.cash, 0); assert.equal(s.forge.job, null);
  assert.equal(movePart(s, { kind: 'forge', index: 0 }, { kind: 'storage' }), true);
  assert.equal(s.inventory.amplifier, 1); assert.equal(forgeMatches(s).has('lens'), true);
});

test('installed ingredients keep their rotation when recovered and cannot overwrite occupied cells', () => {
  const s = createState(); s.grid[11] = part('mirror', 3); rebuild(s);
  assert.equal(movePart(s, { kind: 'grid', index: 11 }, { kind: 'forge', index: 1 }), true);
  assert.equal(s.grid[11], null);
  assert.equal(movePart(s, { kind: 'forge', index: 1 }, { kind: 'grid', index: 22 }), false);
  assert.equal(movePart(s, { kind: 'forge', index: 1 }, { kind: 'grid', index: 13 }), true);
  assert.deepEqual(s.grid[13], part('mirror', 3));
});

test('forged splitters branch three ways from every incoming side with the promised power', () => {
  for (const [source, direction] of [[2, 2], [14, 3], [22, 0], [10, 1]]) for (const type of ['splitter2', 'splitter3']) {
    const grid = Array(25).fill(null); grid[source] = part('reactor', direction); grid[12] = part(type);
    for (const index of [2, 14, 22, 10].filter(i => i !== source)) grid[index] = part('gun');
    const circuit = traceCircuit(grid);
    assert.equal(circuit.guns.length, 3);
    assert.ok(circuit.guns.every(g => g.power === (type === 'splitter2' ? 4 : 8)));
  }
});

test('forged components apply their effects and only cores and mirrors rotate', () => {
  const s = createState(); s.grid = Array(25).fill(null);
  s.grid[22] = part('reactor2'); s.grid[17] = part('amplifier2'); s.grid[12] = part('prism'); s.grid[7] = part('lens2'); s.grid[2] = part('gun2'); rebuild(s);
  assert.deepEqual(s.circuit.guns, [{ index: 2, power: B.powerCap, piercing: true, targets: 3 }]);
  for (const type of ['amplifier2', 'splitter2', 'splitter3', 'lens2', 'gun2', 'prism']) { s.grid[12] = part(type); assert.equal(rotatePart(s, 12), false); }
  s.grid[12] = part('mirror2'); assert.equal(rotatePart(s, 12), true);
  assert.equal(rotatePart(s, 22), true);
  const grid = Array(25).fill(null); grid[22] = part('reactor2'); grid[12] = part('mirror2'); grid[14] = part('gun2');
  assert.equal(traceCircuit(grid).guns[0].power, 24);
});

test('every kill earns cash but only one in four enemies drops a part', () => {
  const s = createState(); startDive(s); s.spawnIn = 100;
  for (let i = 0; i < 8; i++) {
    s.enemies = [{ id: 1000 + i, type: 'scout', ...B.enemies.scout, hp: 1, maxHp: 38, x: .6, y: .4, attackIn: 2 }];
    tick(s, .1);
  }
  assert.equal(s.kills, 8); assert.equal(s.cash, B.startingCash + 8 * B.enemies.scout.bounty);
  assert.deepEqual(s.drops.map(d => d.type), ['splitter', 'lens']);
});

test('shields absorb first, hull hits trigger feedback, and shields recharge only after the delay', () => {
  const s = createState(); s.grid = Array(25).fill(null); rebuild(s); startDive(s); s.spawnIn = 100;
  s.enemies = [{ id: 1, type: 'warden', ...B.enemies.warden, x: .3, y: .4, attackIn: 0 }];
  tick(s, .01); assert.equal(s.hull, 100); assert.equal(s.shield, 10); assert.ok(s.submarine.shieldFlash > 0);
  s.enemies[0].attackIn = 0; tick(s, .01); assert.equal(s.hull, 96); assert.equal(s.shield, 0); assert.ok(s.submarine.hitFlash > 0);
  s.enemies = []; tick(s, 5.8); assert.equal(s.shield, 0);
  tick(s, 1); assert.ok(s.shield > 0); assert.equal(s.hull, 96);
});

test('enemy shields and hull hits expose distinct animations and rail piercing hits three enemies', () => {
  const s = createState(); s.grid[12] = part('lens2'); rebuild(s); startDive(s); s.spawnIn = 100;
  s.enemies = [1, 2, 3].map(id => ({ id, type: 'warden', ...B.enemies.warden, shield: id === 1 ? 40 : 0, maxHp: 180, x: .5 + id * .1, y: .4, attackIn: 2 }));
  tick(s, .01);
  assert.ok(Math.abs(s.enemies[0].shield - (40 - 15 * B.laserDamagePerEnergy * .01)) < 1e-8); assert.equal(s.enemies[0].hp, 180); assert.ok(s.enemies[0].shieldFlash > 0);
  assert.ok(s.enemies[1].hp < 180); assert.equal(s.enemies[1].hp, s.enemies[2].hp);
  tick(s, .4); assert.ok(s.enemies[1].hitFlash > 0);
});

test('an affordable opening forge and a salvaged lens can beat the tougher dive with real damage taken', () => {
  const s = createState(); startDive(s);
  assert.equal(add(s, 'amplifier'), true); assert.equal(add(s, 'amplifier'), true); assert.equal(startForge(s), true);
  for (let i = 0; i < 360 && s.status === 'running'; i++) {
    tick(s, .5);
    for (const drop of [...s.drops]) movePart(s, { kind: 'drop', id: drop.id }, { kind: 'storage' });
    if (s.inventory.amplifier2 && !s.grid[12]) movePart(s, { kind: 'storage', type: 'amplifier2' }, { kind: 'grid', index: 12 });
    if (s.inventory.lens && !s.grid[7]) movePart(s, { kind: 'storage', type: 'lens' }, { kind: 'grid', index: 7 });
  }
  assert.equal(s.status, 'won'); assert.equal(s.kills, 39); assert.equal(s.salvaged, 10);
  assert.ok(s.hull > 0 && s.hull < 60); assert.equal(s.forged, 1);
});

test('three- and four-part recipes require exact quantities, support holes, and reject a fifth item safely', () => {
  const s = createState(); startDive(s); s.cash = 100; s.inventory.splitter = 5;
  assert.equal(movePart(s, { kind: 'storage', type: 'splitter' }, { kind: 'forge', index: 3 }), true);
  assert.equal(add(s, 'splitter'), true);
  assert.equal(findRecipe(...s.forge.slots.filter(Boolean).map(p => p.type)).output, 'splitter2');
  assert.equal(add(s, 'splitter'), true); assert.equal(startForge(s), false); assert.equal(s.cash, 100);
  assert.deepEqual([...forgeMatches(s)], ['splitter']);
  assert.equal(add(s, 'splitter'), true); assert.equal(add(s, 'splitter'), false); assert.equal(s.inventory.splitter, 1);
  assert.equal(startForge(s), true); assert.equal(s.forge.job.output, 'splitter3'); assert.equal(s.cash, 40);
  assert.equal(findRecipe('lens', 'amplifier', 'amplifier').output, 'prism2');
  assert.equal(findRecipe('lens', 'amplifier').output, 'prism');
  assert.equal(findRecipe('lens', 'lens', 'amplifier'), null);
});
