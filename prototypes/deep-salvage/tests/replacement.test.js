import test from 'node:test';
import assert from 'node:assert/strict';
import { PARTS } from '../parts.js';
import { createState, startDive, movePart, canPlacePart, spawnDrop, storageSlots, tick } from '../engine.js';
const fullHold = () => Object.fromEntries(Object.keys(PARTS).filter(type => !['reactor','pulse'].includes(type)).slice(0,14).map(type => [type,1]));

test('storage, battlefield and unlocked forge sources replace lab parts and return old parts to storage', () => {
  for (const kind of ['storage','drop','forge','grid']) {
    const s=createState(); s.grid[2]={type:'pulse',rotation:0,charge:30};
    let source={kind,type:'mirror',index:0};
    if(kind==='drop') source={kind,id:spawnDrop(s,'mirror').id};
    if(kind==='forge') s.forge.slots[0]={type:'mirror',rotation:3};
    if(kind==='grid') s.grid[0]={type:'mirror',rotation:2};
    assert.equal(canPlacePart(s,source,{kind:'grid',index:2}),true);
    assert.equal(movePart(s,source,{kind:'grid',index:2}),true);
    assert.equal(s.inventory.pulse,2); assert.equal(s.grid[2].type,'mirror');
    if(kind==='grid') {assert.equal(s.grid[0],null); assert.equal(s.grid[2].rotation,2);}
    if(kind==='forge') {assert.equal(s.forge.slots[0],null); assert.equal(s.grid[2].rotation,3);}
    if(kind==='drop') {assert.equal(s.drops.length,0); assert.equal(s.salvaged,1);}
    movePart(s,{kind:'storage',type:'pulse'},{kind:'grid',index:1});
    assert.equal(s.grid[1].charge,undefined,'displaced charge is cleared by stacking');
  }
});

test('full storage replacement rejects atomically unless a stack exists or the incoming last copy frees a slot', () => {
  const s=createState(); s.inventory=fullHold(); s.inventory.mirror=2;
  const before=JSON.stringify(s);
  assert.equal(canPlacePart(s,{kind:'storage',type:'mirror'},{kind:'grid',index:26}),false);
  assert.equal(movePart(s,{kind:'storage',type:'mirror'},{kind:'grid',index:26}),false);
  assert.equal(JSON.stringify(s),before);
  const d=spawnDrop(s,'mirror');
  assert.equal(movePart(s,{kind:'drop',id:d.id},{kind:'grid',index:26}),false);
  assert.ok(s.drops.includes(d)); assert.equal(s.salvaged,0);
  s.inventory.mirror=1; const order=[...storageSlots(s)], freed=order.indexOf('mirror');
  assert.equal(movePart(s,{kind:'storage',type:'mirror'},{kind:'grid',index:26}),true);
  assert.equal(s.inventory.reactor,1); assert.equal(storageSlots(s)[freed],'reactor');
  order.forEach((type,i)=>{if(i!==freed)assert.equal(s.storageOrder[i],type);});
  assert.equal(storageSlots(s).filter(Boolean).length,14);
  s.grid[25]={type:'reactor',rotation:0};
  assert.equal(movePart(s,{kind:'drop',id:d.id},{kind:'grid',index:25}),true);
  assert.equal(s.inventory.reactor,2);
});

test('same-cell drops are no-ops and occupied forge replacement never touches locked inputs', () => {
  const s=createState(); startDive(s); s.spawnIn=100;
  assert.equal(movePart(s,{kind:'grid',index:26},{kind:'grid',index:26}),false);
  assert.equal(s.inventory.reactor,1);
  movePart(s,{kind:'storage',type:'medic'},{kind:'forge',index:0});
  assert.equal(movePart(s,{kind:'storage',type:'amplifier'},{kind:'forge',index:0}),true);
  assert.equal(s.inventory.medic,1);
  movePart(s,{kind:'storage',type:'amplifier'},{kind:'forge',index:1});
  assert.equal(s.forge.job.output,'amplifier2');
  const before=JSON.stringify(s);
  assert.equal(movePart(s,{kind:'storage',type:'mirror'},{kind:'forge',index:0}),false);
  assert.equal(JSON.stringify(s),before);
});

test('consumables cannot replace circuit components and rebuilding is allowed during freeze', () => {
  const s=createState();startDive(s); s.inventory.timeCapsule=2;
  assert.equal(movePart(s,{kind:'storage',type:'timeCapsule'},{kind:'grid',index:2}),false);
  assert.equal(s.inventory.timeCapsule,2); assert.equal(s.grid[2].type,'gun');
  movePart(s,{kind:'storage',type:'timeCapsule'},{kind:'loader',index:0});
  assert.equal(movePart(s,{kind:'storage',type:'pulse'},{kind:'grid',index:2}),true);
  tick(s,1); assert.equal(s.grid[2].charge,undefined); assert.equal(s.inventory.gun,2);
});
