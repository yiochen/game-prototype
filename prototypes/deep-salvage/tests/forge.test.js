import test from 'node:test';
import assert from 'node:assert/strict';
import { BALANCE as B } from '../balance.js';
import { RECIPES, recipeSlots } from '../recipes.js';
import { createState, startDive, movePart, startForge, forgeMatches, tick, rebuild, traceCircuit, rotatePart } from '../engine.js';
const part = (type, rotation = 0) => ({ type, rotation });
const add = (s, type) => movePart(s, { kind: 'storage', type }, { kind: 'forge' });

test('every recipe automatically starts in either order, charges once and creates one output', () => {
  for (const recipe of RECIPES) for (const ingredients of [recipe.ingredients, [...recipe.ingredients].reverse()]) {
    const s = createState(); startDive(s); s.cash = recipe.cost; s.spawnIn = 100; s.inventory[recipe.output] = 0; s.discovered.delete(recipe.output);
    for (const type of ingredients) s.inventory[type] = (s.inventory[type] || 0) + 1;
    for (let i = 0; i < ingredients.length; i++) {
      assert.equal(add(s, ingredients[i]), true);
      if (i < ingredients.length - 1) assert.equal(s.forge.job, null, 'no smaller recipe may start early');
    }
    assert.equal(s.forge.job.output, recipe.output); assert.equal(s.cash, 0);
    assert.equal(startForge(s), false);
    assert.equal(movePart(s, {kind:'forge',index:0}, {kind:'storage'}), false);
    tick(s, recipe.seconds - 1); assert.equal(s.inventory[recipe.output] || 0, 0);
    s.paused = true; const remaining = s.forge.job.remaining; tick(s, 20); assert.equal(s.forge.job.remaining, remaining);
    s.paused = false; tick(s, 1.1); assert.equal(s.inventory[recipe.output], 1); assert.equal(s.forged, 1);
    assert.deepEqual(s.forge, {slots:Array(B.forgeSlots).fill(null),job:null});
    assert.deepEqual(s.discoveries, [recipe.output]); tick(s, 2); assert.equal(s.inventory[recipe.output], 1);
  }
});

test('recipe multisets are unique and no recipe is contained in another', () => {
  assert.ok(RECIPES.every(recipe => recipe.ingredients.length <= B.forgeSlots));
  for (const a of RECIPES) for (const b of RECIPES) if (a !== b) {
    assert.equal(recipeSlots(a, b.ingredients.map(type => ({type}))), null, `${a.output} overlaps ${b.output}`);
  }
});

test('unrelated ingredients are accepted, preserved and movable while only recipe inputs lock', () => {
  const s = createState(); startDive(s);
  assert.equal(add(s, 'pulse'), true);
  assert.equal(add(s, 'amplifier'), true); assert.equal(add(s, 'amplifier'), true);
  assert.equal(s.forge.job.output, 'amplifier2'); assert.deepEqual(s.forge.job.indices, [1,2]);
  assert.equal(movePart(s, {kind:'forge',index:0}, {kind:'storage'}), true);
  assert.equal(add(s, 'shield'), true);
  tick(s, 7); assert.equal(s.inventory.amplifier2, 1); assert.equal(s.forge.slots[0].type, 'shield');
});

test('unaffordable recipes wait intact and start automatically when cash becomes available', () => {
  const s = createState(); startDive(s); s.cash = 0; s.spawnIn = 100;
  add(s, 'amplifier'); add(s, 'amplifier'); tick(s, 1); assert.equal(s.forge.job, null);
  s.cash = 24; tick(s, .01); assert.equal(s.forge.job.output, 'amplifier2'); assert.equal(s.cash, 0);
  tick(s, .1); assert.equal(s.cash, 0);
});

test('three slots allow arbitrary parts; a full or occupied slot rejects without consuming anything', () => {
  const s = createState(); startDive(s); s.cash = 0; s.inventory.pulse = 4;
  for (let i = 0; i < B.forgeSlots; i++) assert.equal(add(s, 'pulse'), true);
  assert.equal(add(s, 'pulse'), false); assert.equal(s.inventory.pulse, 1); assert.equal(s.forge.job, null);
  assert.equal(movePart(s, {kind:'forge',index:0}, {kind:'forge',index:1}), false);
});

test('installed ingredients keep their rotation when recovered and cannot overwrite occupied cells', () => {
  const s = createState(); s.grid[13] = part('mirror', 3); rebuild(s);
  assert.equal(movePart(s, { kind: 'grid', index: 13 }, { kind: 'forge', index: 1 }), true);
  assert.equal(s.grid[13], null);
  assert.equal(movePart(s, { kind: 'forge', index: 1 }, { kind: 'grid', index: 26 }), false);
  assert.equal(movePart(s, { kind: 'forge', index: 1 }, { kind: 'grid', index: 15 }), true);
  assert.deepEqual(s.grid[15], part('mirror', 3));
});

test('forged splitters branch three ways from every incoming side with the promised power', () => {
  for (const [source, direction] of [[2, 2], [16, 3], [26, 0], [12, 1]]) for (const type of ['splitter2', 'splitter3']) {
    const grid = Array(30).fill(null); grid[source] = part('reactor', direction); grid[14] = part(type);
    for (const index of [2, 16, 26, 12].filter(i => i !== source)) grid[index] = part('gun');
    const circuit = traceCircuit(grid);
    assert.equal(circuit.guns.length, 3);
    assert.ok(circuit.guns.every(g => g.power === (type === 'splitter2' ? 4 : 8)));
  }
});

test('forged components apply their effects and only cores and mirrors rotate', () => {
  const s = createState(); s.grid = Array(30).fill(null);
  s.grid[26] = part('reactor2'); s.grid[20] = part('amplifier2'); s.grid[14] = part('prism'); s.grid[8] = part('lens2'); s.grid[2] = part('gun2'); rebuild(s);
  assert.deepEqual(s.circuit.guns, [{ index: 2, power: B.powerCap, piercing: true, targets: 3 }]);
  for (const type of ['amplifier2', 'splitter2', 'splitter3', 'lens2', 'gun2', 'prism']) { s.grid[14] = part(type); assert.equal(rotatePart(s, 14), false); }
  s.grid[14] = part('mirror2'); assert.equal(rotatePart(s, 14), true);
  assert.equal(rotatePart(s, 26), true);
  const grid = Array(30).fill(null); grid[26] = part('reactor2'); grid[14] = part('mirror2'); grid[16] = part('gun2');
  assert.equal(traceCircuit(grid).guns[0].power, 24);
});

test('every kill earns cash but only one in four enemies drops a part', () => {
  const s = createState(); startDive(s); s.spawnIn = 100;
  for (let i = 0; i < 8; i++) {
    s.enemies = [{ id: 1000 + i, type: 'scout', ...B.enemies.scout, hp: 1, maxHp: 38, x: .6, y: .4, attackIn: 2 }];
    tick(s, .1);
  }
  assert.equal(s.kills, 8); assert.equal(s.cash, B.startingCash + 8 * B.enemies.scout.bounty);
  assert.deepEqual(s.drops.map(d => d.type), ['splitter', 'timeCapsule', 'lens', 'repairKit']);
});

test('shields absorb first, hull hits trigger feedback, and shields recharge only after the delay', () => {
  const s = createState(); s.grid = Array(30).fill(null); rebuild(s); startDive(s); s.spawnIn = 100;
  s.enemies = [{ id: 1, type: 'warden', ...B.enemies.warden, x: .3, y: .4, attackIn: 0 }];
  tick(s, .01); assert.equal(s.hull, 100); assert.equal(s.shield, 10); assert.ok(s.submarine.shieldFlash > 0);
  s.enemies[0].attackIn = 0; tick(s, .01); assert.equal(s.hull, 96); assert.equal(s.shield, 0); assert.ok(s.submarine.hitFlash > 0);
  s.enemies = []; tick(s, 5.8); assert.equal(s.shield, 0);
  tick(s, 1); assert.ok(s.shield > 0); assert.equal(s.hull, 96);
});

test('enemy shields and hull hits expose distinct animations and rail piercing hits three enemies', () => {
  const s = createState(); s.grid[14] = part('lens2'); rebuild(s); startDive(s); s.spawnIn = 100;
  s.enemies = [1, 2, 3].map(id => ({ id, type: 'warden', ...B.enemies.warden, shield: id === 1 ? 40 : 0, maxHp: 180, x: .5 + id * .1, y: .4, attackIn: 2 }));
  tick(s, .01);
  assert.ok(Math.abs(s.enemies[0].shield - (40 - 15 * B.laserDamagePerEnergy * .01)) < 1e-8); assert.equal(s.enemies[0].hp, 180); assert.ok(s.enemies[0].shieldFlash > 0);
  assert.ok(s.enemies[1].hp < 180); assert.equal(s.enemies[1].hp, s.enemies[2].hp);
  tick(s, .4); assert.ok(s.enemies[1].hitFlash > 0);
});

test('an affordable opening forge and a salvaged lens can beat the tougher dive with real damage taken', () => {
  const s = createState(); startDive(s);
  assert.equal(add(s, 'amplifier'), true); assert.equal(add(s, 'amplifier'), true); assert.ok(s.forge.job);
  for (let i = 0; i < 360 && s.status === 'running'; i++) {
    tick(s, .5);
    for (const drop of [...s.drops]) movePart(s, { kind: 'drop', id: drop.id }, { kind: 'storage' });
    if (s.inventory.amplifier2 && !s.grid[14]) movePart(s, { kind: 'storage', type: 'amplifier2' }, { kind: 'grid', index: 14 });
    if (s.inventory.lens && !s.grid[8]) movePart(s, { kind: 'storage', type: 'lens' }, { kind: 'grid', index: 8 });
  }
  assert.equal(s.status, 'won'); assert.equal(s.kills, 39); assert.equal(s.salvaged, 17);
  assert.ok(s.hull > 0 && s.hull < 60); assert.equal(s.forged, 1);
});

test('a staged ingredient can complete the next recipe once the current job frees slots', () => {
  const s = createState(); startDive(s); s.cash = 100; s.spawnIn = 100;
  add(s, 'amplifier'); add(s, 'amplifier'); add(s, 'mirror');
  assert.equal(s.forge.job.output, 'amplifier2');
  tick(s, 6.1); assert.equal(s.inventory.amplifier2, 1);
  assert.equal(add(s, 'mirror'), true); assert.equal(add(s, 'pulse'), true); assert.equal(s.forge.job.output, 'mirror2');
  tick(s, 5.1); assert.equal(s.inventory.mirror2, 1); assert.equal(s.forge.slots[1].type, 'pulse'); assert.equal(s.cash, 60);
});
