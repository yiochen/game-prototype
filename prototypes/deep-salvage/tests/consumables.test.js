import test from 'node:test';
import assert from 'node:assert/strict';
import { BALANCE as B, CONSUMABLE_RULES, MAPS } from '../balance.js';
import { PARTS } from '../parts.js';
import { createState, startDive, tick, movePart, spawnDrop, rebuild, canConsume, storageSlots } from '../engine.js';
const running = () => { const s = createState(); startDive(s); s.spawnIn = 100; return s; };
const use = (s, type, index = 0) => movePart(s, { kind: 'storage', type }, { kind: 'loader', index });

test('supplies collect and stack without activating, share fourteen slots, and never install into the circuit', () => {
  const s = running(); s.hull = 50;
  for (let i = 0; i < 2; i++) { const d = spawnDrop(s, 'repairKit'); assert.equal(movePart(s, {kind:'drop',id:d.id}, {kind:'storage'}), true); }
  assert.equal(s.inventory.repairKit, 2); assert.equal(s.hull, 50);
  assert.equal(storageSlots(s).filter(t => t === 'repairKit').length, 1);
  assert.equal(movePart(s, {kind:'storage',type:'repairKit'}, {kind:'grid',index:0}), false);
  assert.equal(s.inventory.repairKit, 2); assert.equal(s.grid[0], null);
  s.inventory = Object.fromEntries(Object.keys(PARTS).filter(t => t !== 'timeCapsule').slice(0,14).map(t => [t,1]));
  const d = spawnDrop(s, 'timeCapsule');
  assert.equal(movePart(s, {kind:'drop',id:d.id}, {kind:'storage'}), false);
  assert.ok(s.drops.includes(d)); assert.equal(s.timeFreeze, 0);
  assert.equal(movePart(s, {kind:'drop',id:d.id}, {kind:'loader',index:1}), true);
  assert.equal(s.timeFreeze, 8); assert.equal(s.inventory.timeCapsule, undefined);
});

test('both loaders consume one copy, cap repairs, reject ineffective uses and reject component parts', () => {
  for (const [type, rule] of Object.entries(CONSUMABLE_RULES).filter(([,r]) => r.resource)) for (const index of [0,1]) {
    const s = running(); s.inventory[type] = 3;
    assert.equal(use(s,type,index), false); assert.equal(s.inventory[type],3);
    s[rule.resource] = 0;
    if (rule.resource === 'hull') s.hull = 1;
    assert.equal(use(s,type,index), true);
    assert.equal(s[rule.resource], Math.min(rule.resource === 'hull' ? 100 : 24, rule.amount + (rule.resource === 'hull' ? 1 : 0)));
    s[rule.resource] = (rule.resource === 'hull' ? 100 : 24) - 1;
    assert.equal(use(s,type,index), true); assert.equal(s.inventory[type],1);
    assert.equal(use(s,type,index), false); assert.equal(s.inventory[type],1);
    assert.equal(use(s,'mirror',index),false); assert.equal(s.inventory.mirror,2);
    assert.equal(s.cash,B.startingCash);
  }
  const s = running(); s.inventory.timeCapsule = 1;
  for (const index of [-1,2,NaN]) assert.equal(use(s,'timeCapsule',index),false);
  s.paused = true; assert.equal(use(s,'timeCapsule'),false);
  s.paused = false; s.hull = 0; assert.equal(use(s,'timeCapsule'),false);
  s.status = 'lost'; assert.equal(use(s,'timeCapsule'),false); assert.equal(s.inventory.timeCapsule,1);
});

test('freeze stops all battle clocks, damage, charging, healing, loot and forge while allowing circuit edits', () => {
  const s = running(); s.inventory.timeCapsule = 1;
  s.grid[24] = {type:'reactor',rotation:0}; s.grid[0] = {type:'medic',rotation:0,charge:40};
  s.grid[2] = {type:'pulse',rotation:0,charge:30}; rebuild(s);
  movePart(s,{kind:'storage',type:'amplifier'},{kind:'forge',index:0});
  movePart(s,{kind:'storage',type:'amplifier'},{kind:'forge',index:1});
  s.hull = 60; s.shield = 0; s.shieldCooldown = 2;
  s.enemies = [{id:900,...B.enemies.crab,type:'crab',x:.3,y:.4,attackIn:0}];
  const d = spawnDrop(s,'mirror'); d.landed = true;
  s.shots.push({life:.2}); s.bursts.push({life:.4});
  assert.equal(use(s,'timeCapsule'),true);
  const clocks = state => JSON.stringify([state.elapsed,state.hull,state.shield,state.shieldCooldown,state.enemies,state.submarine,state.shots,state.bursts,state.drops,state.spawnIn,state.rest,state.forge.job,state.grid[0],state.grid[2]]);
  const before = clocks(s); tick(s,3,.2); assert.equal(clocks(s),before); assert.equal(s.timeFreeze,5);
  assert.equal(movePart(s,{kind:'storage',type:'mirror'},{kind:'grid',index:13}),true);
  assert.equal(s.grid[13].type,'mirror'); assert.equal(s.paused,false);
  s.paused = true; tick(s,30); assert.equal(s.timeFreeze,5); s.paused = false;
  tick(s,5); assert.equal(s.timeFreeze,0); assert.equal(clocks(s),before);
  tick(s,.1); assert.ok(s.elapsed > 0); assert.ok(s.hull < 60); assert.ok(s.forge.job.remaining < 6); assert.ok(s.grid[0].charge > 40);
});

test('extra capsules extend real-time freeze, and expiry simulates only the leftover time at drag speed', () => {
  const s = running(); s.inventory.timeCapsule = 2; s.inventory.timeCapsule2 = 1;
  use(s,'timeCapsule'); tick(s,2,.2); assert.equal(s.timeFreeze,6);
  use(s,'timeCapsule2',1); assert.equal(s.timeFreeze,26); assert.equal(s.freezeDuration,26);
  tick(s,27,.2); assert.equal(s.timeFreeze,0); assert.ok(Math.abs(s.elapsed - .2) < 1e-9);
  assert.equal(s.inventory.timeCapsule,1); assert.equal(s.inventory.timeCapsule2,0);
  assert.equal(s.loaders[1].remaining,0);
});

test('a complete recipe assembled during freeze waits to charge cash and begin', () => {
  const s = running(); s.inventory.timeCapsule = 1; use(s,'timeCapsule');
  for (const index of [0,1]) movePart(s,{kind:'storage',type:'amplifier'},{kind:'forge',index});
  tick(s,7); assert.equal(s.forge.job,null); assert.equal(s.cash,24);
  tick(s,1.1); assert.equal(s.forge.job.output,'amplifier2'); assert.equal(s.cash,0);
});

test('forged consumables remain usable from the forge when storage is full', () => {
  const s = running(); s.cash = 100; s.hull = 20;
  s.inventory = Object.fromEntries(Object.keys(PARTS).filter(t => t !== 'repairKit2').slice(0,14).map(t => [t,1]));
  s.inventory.repairKit = 3;
  for (const index of [0,1]) assert.equal(movePart(s,{kind:'storage',type:'repairKit'},{kind:'forge',index}),true);
  assert.equal(movePart(s,{kind:'forge',index:0},{kind:'loader',index:0}),false);
  tick(s,5.1); assert.equal(s.forge.slots[0].type,'repairKit2'); assert.equal(s.inventory.repairKit2,undefined);
  assert.equal(movePart(s,{kind:'forge',index:0},{kind:'loader',index:0}),true);
  assert.equal(s.hull,80); assert.equal(s.forge.slots[0],null);
});

test('every level guarantees an early capsule, followed by occasional rotating supplies and cash on every kill', () => {
  for (const map of Object.keys(MAPS)) {
    const s = createState([],map); startDive(s); s.spawnIn = 100;
    for (let i = 0; i < 18; i++) {
      s.enemies = [{ id:1000+i,type:'scout',...B.enemies.scout,hp:1,maxHp:38,x:.6,y:.4,attackIn:2 }]; tick(s,.1);
      if (i === 1) assert.equal(s.drops.filter(d => d.type === 'timeCapsule').length,1);
    }
    assert.deepEqual(s.drops.filter(d => PARTS[d.type].consumable).map(d => d.type),['timeCapsule','repairKit','shieldCell','timeCapsule']);
    assert.equal(s.cash,B.startingCash + 18 * B.enemies.scout.bounty);
    assert.ok(canConsume(s,'timeCapsule'));
  }
});
