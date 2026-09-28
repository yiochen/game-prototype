import test from 'node:test';
import assert from 'node:assert/strict';
import { BALANCE as B } from '../balance.js';
import { createState, startDive, tick, rebuild, traceCircuit, movePart } from '../engine.js';

const part = type => ({ type, rotation: 0 });
function encounter(type = 'gun', count = 1) {
  const s = createState(); s.grid[2] = part(type); rebuild(s); startDive(s); s.spawnIn = 100;
  s.enemies = Array.from({ length: count }, (_, i) => ({ id: 1000 + i, type: 'warden', hp: 1000, maxHp: 1000, armor: 4, shield: 0, speed: 0, x: .6 + i * .1, y: .4, attackIn: 10 }));
  return s;
}
const near = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-7, `${actual} ≈ ${expected}`);

test('laser applies small continuous damage, with frame-independent armor and no shot cooldown', () => {
  const a = encounter(), b = encounter();
  tick(a, .01); const first = a.enemies[0].hp;
  assert.ok(first < 1000 && first > 999);
  tick(a, .01); assert.ok(a.enemies[0].hp < first);
  assert.equal(a.laserBeams.length, 1); assert.equal(a.shots.length, 0);
  tick(a, .98);
  for (let i = 0; i < 100; i++) tick(b, .01);
  near(a.enemies[0].hp, 1000 - (12 - 4) * B.laserDamagePerEnergy);
  near(a.enemies[0].hp, b.enemies[0].hp);
  assert.ok(a.bursts.length <= 2, 'damage labels are aggregated');
  a.grid[20] = null; a.grid[32] = null; rebuild(a); tick(a, .1);
  assert.equal(a.laserBeams.length, 0);
});

test('pulse accepts all four directions, combines inputs, and terminates the circuit', () => {
  const grid = Array(36).fill(null); grid[14] = part('pulse');
  for (const [index, rotation] of [[2, 2], [16, 3], [32, 0], [12, 1]]) grid[index] = { type: 'reactor', rotation };
  const circuit = traceCircuit(grid);
  assert.deepEqual(circuit.guns, [{ index: 14, power: 32, piercing: false, mode: 'pulse' }]);
  assert.equal(circuit.segments.length, 9);
});

test('pulse charges before firing a large hit, resets, then charges again', () => {
  const s = encounter('pulse'); tick(s, 2.9);
  near(s.grid[2].charge, 34.8); assert.equal(s.enemies[0].hp, 1000); assert.equal(s.shots.length, 0);
  tick(s, .1); near(s.grid[2].charge, 0); near(s.enemies[0].hp, 950);
  assert.ok(s.shots.some(shot => shot.pulse)); assert.equal(s.laserBeams.length, 0);
  tick(s, 3); near(s.enemies[0].hp, 900);
});

test('amplified pulse charges faster; lens piercing carries through shields and multiple targets', () => {
  const s = encounter('pulse', 3); s.grid[14] = part('amplifier'); s.grid[8] = part('lens'); rebuild(s);
  s.enemies[0].shield = 20;
  tick(s, 2);
  near(s.enemies[0].shield, 0); near(s.enemies[0].hp, 966);
  near(s.enemies[1].hp, 946); near(s.enemies[2].hp, 1000);
  assert.equal(s.shots.filter(shot => shot.pulse).length, 2);
});

test('charge waits at full with no target, pauses, survives disconnection and moving but clears in hold', () => {
  const s = encounter('pulse'); const enemy = s.enemies.pop(); tick(s, 5);
  near(s.grid[2].charge, B.pulseCapacity); assert.equal(s.shots.length, 0);
  s.paused = true; s.enemies.push(enemy); tick(s, 1); assert.equal(enemy.hp, 1000);
  s.paused = false; s.grid[32] = null; rebuild(s); tick(s, 1); assert.equal(enemy.hp, 1000);
  assert.equal(movePart(s, { kind: 'grid', index: 2 }, { kind: 'grid', index: 8 }), true);
  near(s.grid[8].charge, B.pulseCapacity);
  s.grid[32] = part('reactor'); rebuild(s); tick(s, .01); near(enemy.hp, 950);
  tick(s, 1); assert.ok(s.grid[8].charge > 0);
  movePart(s, { kind: 'grid', index: 8 }, { kind: 'storage' });
  movePart(s, { kind: 'storage', type: 'pulse' }, { kind: 'grid', index: 8 });
  assert.equal(s.grid[8].charge || 0, 0);
});

test('laser and pulse operate independently and retarget after a kill without duplicate rewards', () => {
  const s = encounter('pulse', 2); s.grid[30] = part('reactor'); s.grid[0] = part('gun'); rebuild(s);
  tick(s, .5); assert.equal(s.laserBeams.length, 1); assert.equal(s.shots.length, 0); near(s.grid[2].charge, 6);
  s.enemies[0].hp = .01; tick(s, .01); assert.equal(s.kills, 1);
  tick(s, .01); assert.equal(s.laserBeams[0].targetId, 1001); assert.equal(s.kills, 1);
});


test('pulse preserves fractional charge across shots at different frame rates', () => {
  const a = encounter('pulse'), b = encounter('pulse');
  for (const s of [a, b]) { s.grid[14] = part('prism'); rebuild(s); }
  tick(a, 6.88);
  for (let i = 0; i < 688; i++) tick(b, .01);
  near(a.enemies[0].hp, 1000 - 4 * B.pulseDamage);
  near(a.enemies[0].hp, b.enemies[0].hp);
  near(a.grid[2].charge, b.grid[2].charge);
});
