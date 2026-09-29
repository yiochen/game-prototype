import test from 'node:test';
import assert from 'node:assert/strict';
import { PARTS } from '../parts.js';
import { createState, startDive, movePart, spawnDrop, storageSlots, tick, traceCircuit } from '../engine.js';
const fullHold = excluded => Object.fromEntries(Object.keys(PARTS).filter(type => !excluded.includes(type)).slice(0,14).map(type => [type,1]));

test('storage caps at fourteen stacks, accepts duplicates and rejects new types without consuming their source', () => {
  const s = createState(); s.inventory = fullHold(['prism']);
  const drop = spawnDrop(s,'prism');
  assert.equal(movePart(s,{kind:'drop',id:drop.id},{kind:'storage'}),false);
  assert.equal(s.drops[0].id,drop.id); assert.equal(s.salvaged,0); assert.equal(s.discovered.has('prism'),false);
  s.grid[0] = {type:'prism',rotation:0};
  assert.equal(movePart(s,{kind:'grid',index:0},{kind:'storage'}),false);
  assert.equal(s.grid[0].type,'prism');
  const type = Object.keys(s.inventory)[0], duplicate = spawnDrop(s,type);
  assert.equal(movePart(s,{kind:'drop',id:duplicate.id},{kind:'storage'}),true);
  assert.equal(s.inventory[type],2); assert.equal(storageSlots(s).filter(Boolean).length,14);
});

test('using the final copy frees exactly its slot, which a new type can reuse without shifting neighbors', () => {
  const s = createState(), before = [...storageSlots(s)], index = before.indexOf('reactor');
  assert.equal(movePart(s,{kind:'storage',type:'reactor'},{kind:'grid',index:24}),true);
  const after = storageSlots(s); assert.equal(after[index],null);
  before.forEach((type,i) => { if(i !== index) assert.equal(after[i],type); });
  const drop = spawnDrop(s,'lens'); movePart(s,{kind:'drop',id:drop.id},{kind:'storage'});
  assert.equal(storageSlots(s)[index],'lens'); assert.equal(storageSlots(s).length,14);
});

test('a forged output waits in a consumed forge slot when storage is full, then can be recovered without loss', () => {
  const s = createState(); s.inventory = fullHold(['amplifier2']); s.inventory.amplifier=3;
  startDive(s); s.spawnIn=1000;
  for(let i=0;i<2;i++) assert.equal(movePart(s,{kind:'storage',type:'amplifier'},{kind:'forge'}),true);
  tick(s,7); assert.equal(s.forged,1); assert.equal(s.forge.job,null);
  assert.equal(s.forge.slots[0].type,'amplifier2'); assert.equal(s.inventory.amplifier2,undefined);
  assert.equal(movePart(s,{kind:'forge',index:0},{kind:'storage'}),false);
  movePart(s,{kind:'storage',type:'mirror'},{kind:'grid',index:0});
  assert.equal(movePart(s,{kind:'forge',index:0},{kind:'storage'}),true);
  assert.equal(s.inventory.amplifier2,1); assert.equal(storageSlots(s).filter(Boolean).length,14);
  tick(s,2); assert.equal(s.inventory.amplifier2,1);
});

test('the rectangular lab has thirty cells and rays leave after its fifth row', () => {
  const s = createState(); assert.equal(s.grid.length,30);
  assert.equal(movePart(s,{kind:'storage',type:'mirror'},{kind:'grid',index:30}),false);
  assert.equal(movePart(s,{kind:'storage',type:'mirror'},{kind:'grid',index:29}),true);
  const grid = Array(30).fill(null); grid[24]={type:'reactor',rotation:2};
  const circuit=traceCircuit(grid); assert.equal(circuit.segments.length,1);
  assert.equal(circuit.segments[0].y2,5.5);
});
