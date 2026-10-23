import fs from 'node:fs';
import assert from 'node:assert/strict';
import {orderPlacements,footprintFor} from './sprite-layout.js';
const base = new URL('.', import.meta.url);
const library=JSON.parse(fs.readFileSync(new URL('library-before-cover.json',base)));
const before=library.objects,after=structuredClone(before);
after.find(o=>o.id==='dock-cover').renderPass='overhead';
const roots={'dock-floor':[0,0,0],'dock-entry':[0,-1.5,0],'submarine-yellow':[-.7,-.42,.23],'workshop-hut':[.78,.35,.23],'dock-cover':[0,0,.23],'customer-rosa':[.35,-.9,.22]};
const output={scope:'Code/metadata order evidence only; no candidate/native visibility approval.',orders:{}};
for(const [direction,angle] of Object.entries({N:Math.PI,E:Math.PI/2,S:0,W:-Math.PI/2})){
 const placements=Object.entries(roots).map(([object,[x,y,z]])=>{
  const obj=before.find(o=>o.id===object),fp=footprintFor(obj,direction);
  const root=obj.directionRootCells?.[direction]||obj.rootCell||fp.map(v=>v/2);
  const rx=Math.cos(angle)*x-Math.sin(angle)*y,ry=Math.sin(angle)*x+Math.cos(angle)*y;
  return {object,id:object==='dock-floor'?'dock-deck':object,x:1.5+rx-root[0],y:1.5-ry-root[1],offset:[0,-89.6*z],direction,...(['submarine-yellow','workshop-hut','customer-rosa'].includes(object)?{supportedBy:'dock-deck'}:{})};
 });
 const frozen=JSON.stringify(placements);
 const source=orderPlacements(placements,before).map(p=>p.object),proposed=orderPlacements(placements,after).map(p=>p.object);
 assert.equal(proposed.at(-1),'dock-cover');
 for(const object of ['workshop-hut','submarine-yellow','customer-rosa'])assert(proposed.indexOf('dock-floor')<proposed.indexOf(object));
 assert.equal(JSON.stringify(placements),frozen);
 output.orders[direction]={before:source,proposed,placements};
}
fs.writeFileSync(new URL('order-check.json',base),JSON.stringify(output,null,2)+'\n');
console.log('All4 overhead order checks pass; placements unchanged.');
