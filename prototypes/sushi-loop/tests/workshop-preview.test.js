import test from 'node:test';
import assert from 'node:assert/strict';
import {fixture, command, restore, storageKey, statAt, nextCost, canUpgrade, runProfile} from '../design/workshop-preview/model.js';
import {expedition} from '../design/workshop-preview/balance.js';

test('an affordable upgrade pays for exactly one level', () => {
  const m = fixture('workshop');
  const next = command(m, {type: 'upgrade', id: 'hull', token: 'a'});
  assert.equal(next.levels.hull, m.levels.hull + 1);
  assert.equal(next.salvage, m.salvage - nextCost(m, 'hull'));
  assert.equal(next.levels.harpoon, m.levels.harpoon);
});

test('repeated tokens and reloads cannot pay twice', () => {
  let m = command(fixture('workshop'), {type: 'upgrade', id: 'harpoon', token: 't1'});
  assert.equal(command(m, {type: 'upgrade', id: 'harpoon', token: 't1'}), m);
  assert.equal(command(m, {type: 'upgrade', id: 'harpoon'}), m);
  const saved = restore({getItem: k => k === storageKey ? JSON.stringify(m) : null});
  assert.deepEqual(saved, m);
  assert.equal(command(saved, {type: 'upgrade', id: 'harpoon', token: 't1'}), saved);
});

test('insufficient salvage and the cap reject the upgrade', () => {
  const poor = fixture('unaffordable');
  for (const id of ['hull', 'harpoon', 'collector']) {
    assert.equal(canUpgrade(poor, id), false);
    assert.equal(command(poor, {type: 'upgrade', id, token: id}), poor);
  }
  const max = fixture('max');
  assert.equal(nextCost(max, 'hull'), null);
  assert.equal(command(max, {type: 'upgrade', id: 'hull', token: 'x'}), max);
});

test('reaching the look level marks the part NEW; collector stays modest', () => {
  let m = {...fixture('workshop'), salvage: 1000};
  m = command(m, {type: 'upgrade', id: 'collector', token: 'c1'});
  assert.equal(m.seen.collector, undefined);
  m = command(m, {type: 'upgrade', id: 'collector', token: 'c2'});
  assert.equal(m.seen.collector, false);
  m = command(m, {type: 'upgrade', id: 'collector', token: 'c3'});
  assert.equal(statAt('collector', m.levels.collector), 1.5);
  assert.equal(nextCost(m, 'collector'), null);
});

test('equivalent runs improve on every track without changing pickup value', () => {
  const base = runProfile({hull: 1, harpoon: 1, collector: 1}, expedition);
  const up = runProfile({hull: 3, harpoon: 3, collector: 3}, expedition);
  assert.ok(up.hull > base.hull && up.hitsSurvived > base.hitsSurvived);
  assert.ok(up.reelSeconds < base.reelSeconds);
  assert.ok(up.reach > base.reach);
  assert.equal(expedition.salvagePerPickup, 2);
});

test('every part is fitted from the start and swaps its whole look at each milestone', async () => {
  const {tierOf} = await import('../design/workshop-preview/model.js');
  assert.deepEqual([1, 2, 3, 4, 5].map(l => tierOf('hull', l)), [1, 1, 2, 2, 3]);
  assert.deepEqual([1, 2, 3, 4].map(l => tierOf('collector', l)), [1, 1, 2, 3]);
  let m = {...fixture('max'), salvage: 1000};
  m = command(m, {type: 'upgrade', id: 'harpoon', token: 'h4'});
  assert.equal(m.seen.harpoon, undefined);
  m = command(m, {type: 'upgrade', id: 'harpoon', token: 'h5'});
  assert.equal(m.seen.harpoon, false);
});

test('power-ups are their own tracks: shield duration, passage length and shield at start', async () => {
  const {statAt, tierOf} = await import('../design/workshop-preview/model.js');
  let m = {...fixture('workshop'), salvage: 1000};
  assert.equal(statAt('launch', m.levels.launch), 0);
  m = command(m, {type: 'upgrade', id: 'launch', token: 'l2'});
  assert.equal(statAt('launch', m.levels.launch), 1.5);
  assert.equal(m.seen.launch, false); // the first launch shield is its first look
  m = command(m, {type: 'upgrade', id: 'shield', token: 's2'});
  assert.equal(statAt('shield', m.levels.shield), 4.25);
  assert.equal(tierOf('passage', 4), 3);
  assert.ok(runProfile(m.levels, expedition).shield > expedition.shieldSeconds);
});
