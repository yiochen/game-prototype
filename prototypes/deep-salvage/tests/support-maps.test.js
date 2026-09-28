import test from 'node:test';
import assert from 'node:assert/strict';
import { BALANCE as B, PART_RULES, MAPS, ENEMY_INFO } from '../balance.js';
import { createState, startDive, tick, rebuild, traceCircuit, movePart, rotatePart, startForge } from '../engine.js';
const part = (type, rotation = 0) => ({ type, rotation });
const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-7, `${a} ≈ ${b}`);
function support(type) {
  const s = createState(); s.grid[2] = part(type); rebuild(s); startDive(s); s.spawnIn = 100; s.shieldCooldown = 100;
  return s;
}
function enemy(type, values = {}) { return { id: 900, type, ...B.enemies[type], maxHp: B.enemies[type].hp, x: .3, y: .5, attackIn: 0, ...values }; }
function emptyFight() { const s = support('shield'); s.grid = Array(30).fill(null); rebuild(s); return s; }

test('support terminals accept and combine every input side, stop beams, and never count as guns', () => {
  for (const type of ['shield', 'medic', 'shield2', 'medic2']) {
    const grid = Array(30).fill(null); grid[14] = part(type);
    for (const [index, rotation] of [[2,2],[16,3],[26,0],[12,1]]) grid[index] = part('reactor', rotation);
    const c = traceCircuit(grid); assert.equal(c.guns.length, 0); assert.equal(c.supports.length, 1); assert.equal(c.supports[0].power, 32); assert.equal(c.segments.length, 8);
    const s = support(type); assert.equal(rotatePart(s, 2), false);
  }
});

test('Shield restores during combat cooldown; Medic repairs hull only, both cap and hold full charge', () => {
  for (const type of ['shield', 'shield2', 'medic', 'medic2']) {
    const s = support(type), rule = PART_RULES[type], resource = rule.resource, max = resource === 'shield' ? B.shield : B.hull;
    const initial = resource === 'hull' ? 10 : 0;
    s[resource] = initial; tick(s, rule.capacity / 12 - .01); near(s[resource], initial);
    tick(s, .01); near(s[resource], initial + rule.restore); assert.ok(s.bursts.some(b => b.kind === (resource === 'shield' ? 'restore' : 'repair')));
    s[resource] = max - 1; tick(s, rule.capacity / 12); near(s[resource], max);
    tick(s, 10); near(s.grid[2].charge, rule.capacity);
    s[resource] = max - 2; tick(s, .01); near(s[resource], max); assert.ok(s.grid[2].charge < 1);
  }
});

test('support energy pauses, survives disconnection and grid moves, but clears on stacking', () => {
  const s = support('medic'); s.hull = 50; tick(s, 1); near(s.grid[2].charge, 12);
  s.paused = true; tick(s, 10); near(s.grid[2].charge, 12); s.paused = false;
  movePart(s, {kind:'grid',index: 2}, {kind:'grid',index: 1}); tick(s, 4); near(s.grid[1].charge, 12); near(s.hull, 50);
  movePart(s, {kind:'grid',index: 1}, {kind:'grid',index: 2}); tick(s, 3); near(s.hull, 62);
  movePart(s, {kind:'grid',index: 2}, {kind:'storage'}); movePart(s, {kind:'storage',type:'medic'}, {kind:'grid',index: 2}); near(s.grid[2].charge || 0, 0);
});

test('amplifiers speed support charging while piercing does not multiply repairs; lethal hits stay lethal', () => {
  const s = support('medic'); s.hull = 50; s.grid[14] = part('amplifier'); s.grid[8] = part('lens2'); rebuild(s);
  tick(s, 48 / 22.5); near(s.hull, 62);
  s.grid[2].charge = 48; s.hull = 1; s.shield = 0; s.enemies = [enemy('crab')]; tick(s, .01);
  assert.equal(s.status, 'lost'); assert.equal(s.hull, 0);
});

test('snipers stop at range and attack without reaching the submarine', () => {
  const s = emptyFight(), e = enemy('sniper', { x: .95, attackIn: 3 }); s.enemies = [e]; tick(s, 2.5);
  assert.ok(e.x > .8 && e.x < .84); assert.equal(s.shield, 24);
  tick(s, 3); assert.ok(s.shield < 24); assert.ok(e.x > .8);
});

test('leeches drain double shield with correctly calculated hull spillover', () => {
  const s = emptyFight(); s.shield = 10; s.enemies = [enemy('leech')]; tick(s, .01);
  near(s.shield, 0); near(s.hull, 97); assert.equal(s.bursts.find(b => b.kind === 'hull').amount, 3);
  s.shield = 24; s.enemies[0].attackIn = 0; tick(s, .01); near(s.shield, 8);
  assert.equal(s.bursts.find(b => b.kind === 'shield').amount, 16);
});

test('menders heal nearby allies up to max, never themselves or distant allies', () => {
  const s = emptyFight(), m = enemy('mender', { hp: 20, x: .7, speed: 0, attackIn: 100 });
  const close = enemy('crab', { id:901, hp:123, x:.8, speed:0 }), far = enemy('crab', { id:902, hp:50, x:.95, speed:0 });
  s.enemies = [m, close, far]; tick(s, 1); near(close.hp, 125); near(m.hp, 20); near(far.hp, 50);
});

test('bombers explode once without awarding kill loot, but shooting them awards cash', () => {
  const s = emptyFight(); s.enemies = [enemy('bomber')]; tick(s, .01);
  near(s.hull, 98); near(s.shield, 0); assert.equal(s.enemies.length, 0); assert.equal(s.kills, 0); assert.equal(s.cash, B.startingCash);
  tick(s, 1); near(s.hull, 98);
  s.grid[26] = part('reactor'); s.grid[2] = part('gun'); rebuild(s); s.enemies = [enemy('bomber', {x:.7,hp:.001})]; tick(s,.01);
  assert.equal(s.kills, 1); assert.equal(s.cash, B.startingCash + B.enemies.bomber.bounty);
});

test('every route has valid encounters covering all ten enemy roles and deterministic completion', () => {
  const present = new Set();
  for (const [mapId, map] of Object.entries(MAPS)) {
    const s = createState([], mapId); startDive(s);
    // Strong fixture isolates route progression from player build quality.
    s.grid[14] = part('amplifier2'); s.grid[8] = part('lens2'); s.grid[2] = part('gun2');
    s.grid[24] = part('reactor2'); s.grid[0] = part('medic2'); rebuild(s); tick(s, 240);
    assert.equal(s.status, 'won', mapId); assert.equal(s.wave, map.waves.length - 1);
    for (const wave of map.waves) for (const type of wave.enemies) { assert.ok(B.enemies[type] && ENEMY_INFO[type]); present.add(type); }
  }
  assert.equal(present.size, 10); assert.equal(createState([], 'invalid').mapId, 'city');
});

test('Foundry is beatable using starting inventory, earned cash, salvaged lens and a refit forge', () => {
  const s = createState([], 'foundry'); startDive(s);
  for (let i = 0; i < 2; i++) movePart(s, {kind:'storage',type:'amplifier'}, {kind:'forge'});
  assert.ok(s.forge.job);
  movePart(s, {kind:'storage',type:'reactor'}, {kind:'grid',index: 24});
  movePart(s, {kind:'storage',type:'medic'}, {kind:'grid',index: 0});
  let heavy = false;
  for (let i = 0; i < 480 && s.status === 'running'; i++) {
    tick(s, .5);
    for (const drop of [...s.drops]) movePart(s, {kind:'drop',id:drop.id}, {kind:'storage'});
    for (const [type,index] of [['amplifier2',14],['lens',8],['gun2',2]]) if (s.inventory[type] && !s.grid[index]) movePart(s, {kind:'storage',type}, {kind:'grid',index});
    if (!heavy && s.rest > 6 && !s.forge.job && s.inventory.gun && s.cash >= 24) {
      movePart(s, {kind:'grid',index: 2}, {kind:'forge'}); movePart(s, {kind:'storage',type:'gun'}, {kind:'forge'});
      heavy = s.forge.job?.output === 'gun2';
    }
  }
  assert.equal(heavy, true); assert.equal(s.forged, 2); assert.equal(s.status, 'won'); assert.equal(s.kills, 39);
});
