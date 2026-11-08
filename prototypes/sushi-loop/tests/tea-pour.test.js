import test from 'node:test';
import assert from 'node:assert/strict';
import { TEA } from '../design/tea-pour-preview/balance.js';
import { CUPS } from '../design/tea-pour-preview/cups.js';
import { createPour, flowShare, gradePour, pourDone, tipChance } from '../design/tea-pour-preview/pour.js';

const cup = (id) => CUPS.find((c) => c.id === id);

// Time to raise the level across a height span at a constant flow.
function riseSeconds(c, from, to, flow) {
  return (c.volumeAt(to) - c.volumeAt(from)) / flow;
}

test('narrow sections rise faster than wide ones at equal flow', () => {
  const hourglass = cup('hourglass');
  const waist = riseSeconds(hourglass, 70, 83, 1000);
  const body = riseSeconds(hourglass, 10, 24, 1000);
  assert.ok(body > waist * 5, `body ${body} vs waist ${waist}`);
  const bowl = cup('bowl');
  assert.ok(riseSeconds(bowl, 80, 90, 1000) > riseSeconds(bowl, 0, 10, 1000) * 5);
});

test('level and volume invert each other', () => {
  for (const c of CUPS) {
    for (const y of [0, 7.3, c.height / 2, c.targetHeight, c.height]) {
      assert.ok(Math.abs(c.levelFor(c.volumeAt(y)) - y) < 0.05, `${c.id} at ${y}`);
    }
  }
});

test('crooked offset does not change capacity', () => {
  const vase = cup('vase');
  assert.ok(vase.samples().some((s) => Math.abs(s.dx) > 5));
  const unshifted = vase.samples().reduce((sum, s, i, all) => (i ? sum + Math.PI * ((all[i - 1].r + s.r) / 2) ** 2 * 0.5 : 0), 0);
  assert.ok(Math.abs(unshifted - vase.capacity) < 1e-6);
});

test('upright produces no flow and more tilt produces more flow', () => {
  assert.equal(flowShare(0, TEA.pour), 0);
  assert.equal(flowShare(TEA.pour.deadZone, TEA.pour), 0);
  assert.ok(flowShare(0.5, TEA.pour) < flowShare(0.8, TEA.pour));
  assert.equal(flowShare(1, TEA.pour), 1);
});

test('release stops flow with a small consistent drip', () => {
  const c = cup('yunomi');
  const drip = (seconds, tilt) => {
    const pour = createPour(c, TEA);
    for (let t = 0; t < seconds; t += 1 / 60) pour.step(1 / 60, tilt, true);
    const before = pour.state.volume;
    for (let t = 0; t < 1; t += 1 / 60) pour.step(1 / 60, 0, false);
    return pour.state.volume - before;
  };
  const a = drip(0.4, 0.5), b = drip(0.8, 1);
  assert.ok(Math.abs(a - b) < 1e-6);
  assert.ok(Math.abs(a - c.targetVolume * TEA.pour.dripShare) < 1e-6);
});

test('full tilt reaches the fill line in about the tuned time', () => {
  for (const c of CUPS) {
    const pour = createPour(c, TEA);
    let t = 0;
    while (pour.state.volume < c.targetVolume) { pour.step(1 / 60, 1, true); t += 1 / 60; }
    assert.ok(Math.abs(t - TEA.pour.secondsToTargetAtMax) < 0.05, `${c.id} ${t}`);
  }
});

test('grading and overflow', () => {
  const c = cup('flask');
  assert.equal(gradePour(c, { volume: c.targetVolume, spilled: 0 }, TEA).id, 'ideal');
  assert.equal(gradePour(c, { volume: c.targetVolume * 0.3, spilled: 0 }, TEA).id, 'under');
  assert.equal(gradePour(c, { volume: c.targetVolume * 0.3, spilled: 0 }, TEA).qualifies, false);
  const pour = createPour(c, TEA);
  for (let t = 0; t < 6; t += 1 / 60) pour.step(1 / 60, 1, true);
  assert.ok(pour.state.spilled > 0);
  assert.equal(pour.state.volume, c.capacity);
  assert.equal(gradePour(c, pour.state, TEA).id, 'overflow');
});

test('tea raises the tip chance without guaranteeing a tip', () => {
  const ideal = { id: 'ideal', qualifies: true };
  assert.equal(tipChance({}, TEA), TEA.tip.base);
  assert.equal(tipChance({ teaGrade: { id: 'good', qualifies: true } }, TEA), TEA.tip.tea);
  assert.ok(tipChance({ teaGrade: ideal }, TEA) < 1);
  assert.equal(tipChance({ teaGrade: { id: 'under', qualifies: false } }, TEA), TEA.tip.base);
  assert.equal(tipChance({ teaGrade: ideal, ateRequestedDish: true }, TEA), TEA.tip.requestedDish);
});

test('one pour: serving ends after flow returns to zero and the drops land', () => {
  const c = cup('bowl');
  const pour = createPour(c, TEA);
  pour.step(1 / 60, 0.05, true);
  assert.equal(pourDone(pour.state), false, 'lifting inside the dead zone is not a pour');
  for (let t = 0; t < 0.5; t += 1 / 60) pour.step(1 / 60, 0.7, true);
  assert.equal(pourDone(pour.state), false);
  pour.step(1 / 60, 0.05, true);             // eased back past the dead zone while holding
  assert.equal(pourDone(pour.state), false, 'drops still falling');
  for (let t = 0; t < 1; t += 1 / 60) pour.step(1 / 60, 0, false);
  assert.equal(pourDone(pour.state), true);
});
