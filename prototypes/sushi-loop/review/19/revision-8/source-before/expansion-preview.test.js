import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fixture,command,neighboring,capacity,restore,storageKey,validPlacement,clearedAt} from '../design/expansion-preview/model.js';
import {patches,economy,decorations,trashFamilies,dockCells} from '../design/expansion-preview/balance.js';
test('configured trash masks match registered native model footprints and exact exported bytes',()=>{
 const here=new URL('../design/expansion-preview/',import.meta.url),r=JSON.parse(readFileSync(new URL('world-registration.json',here)));
 for(const p of patches){const a=r[p.art];assert.ok(a,p.art+' missing native render');const rotated=['E','W'].includes(p.facing);assert.equal(p.w,a.footprint[rotated?1:0]);assert.equal(p.h,a.footprint[rotated?0:1]);assert.equal(a.crop_xywh[2],a.frame_size[0]*2);assert.equal(a.crop_xywh[3],a.frame_size[1]*2);const bytes=readFileSync(new URL(a.destination,here));assert.equal(createHash('sha256').update(bytes).digest('hex'),a.sha256);}
});
test('dense packing covers each future cell exactly once with real object footprints',()=>{
 assert.ok(patches.length>=35);assert.ok(trashFamilies.length>=5);const cells=new Set(dockCells.map(c=>c.join(',')));
 for(const p of patches){const f=trashFamilies.find(f=>f.id===p.family),rotated=['E','W'].includes(p.facing);assert.equal(p.w,f.footprint[rotated?1:0]);assert.equal(p.h,f.footprint[rotated?0:1]);for(let y=p.y;y<p.y+p.h;y++)for(let x=p.x;x<p.x+p.w;x++){assert.ok(x>=7&&x<21&&y>=3&&y<13);assert.ok(!cells.has(`${x},${y}`),p.id+' overlaps another object');cells.add(`${x},${y}`);}}
 assert.equal(cells.size,140);assert.equal(patches.filter(p=>p.family==='garbage-armchair').every(p=>p.w*p.h===1),true);for(const f of trashFamilies)assert.ok(new Set(patches.filter(p=>p.family===f.id).map(p=>p.facing)).size>=2);
});
test('neighboring objects allow player choice and reveal subsequent neighbors',()=>{
 const m=fixture(),available=patches.filter(p=>neighboring(m,p));assert.deepEqual(available.map(p=>p.id),['sofa-west','armchair-west','dock-access','shelves-west']);
 for(const p of available)assert.deepEqual(command(m,{type:'clear',id:p.id}).cleared,[p.id]);
 const far=patches.find(p=>p.x>=14);assert.equal(command(m,{type:'clear',id:far.id}),m);
 const n=command(m,{type:'clear',id:'sofa-west'});assert.ok(neighboring(n,patches.find(p=>p.id==='cabinet-west')));
});
test('clear pays once, persists, and insufficient funds do nothing in Live and Edit',()=>{
 for(const mode of ['live','edit']){let m={...fixture(),mode};m=command(m,{type:'clear',id:'dock-access'});assert.equal(m.coins,460);assert.equal(command(m,{type:'clear',id:'dock-access'}),m);
 const saved=restore({getItem:k=>k===storageKey?JSON.stringify(m):null});assert.deepEqual(saved,m);assert.equal(command(saved,{type:'clear',id:'dock-access'}),saved);
 const poor={...fixture('poor'),mode};assert.equal(command(poor,{type:'clear',id:'dock-access'}),poor);}
});
test('clearing gains only the selected object cells; occupancy never reduces area capacity',()=>{
 let m={...fixture(),mode:'edit'},before=capacity(m);assert.equal(validPlacement(m,7,3),false);m=command(m,{type:'clear',id:'sofa-west'});
 assert.equal(validPlacement(m,7,3),true);assert.equal(validPlacement(m,9,3),false);assert.equal(validPlacement(m,7,5),false);assert.equal(capacity(m).area,before.area+4);
 const cap=capacity(m);m=command(m,{type:'place',x:7,y:3});assert.deepEqual(capacity(m),cap);assert.equal(validPlacement(m,7,3),false);
 m=command(m,{type:'clear',id:'armchair-west'});assert.equal(capacity(m).area,before.area+5);assert.equal(clearedAt(m,7,5),true);assert.equal(clearedAt(m,8,5),false);
});
test('perimeter props sit outside the actual room and never participate in economy or capacity',()=>{
 assert.ok(decorations.every(d=>d.x<=-.5||d.x>=21.5||d.y>=13.5));assert.ok(decorations.length>60);const left=decorations.filter(d=>d.x<0);assert.ok(new Set(left.map(d=>d.family)).size>=5);assert.ok(new Set(left.map(d=>d.y)).size>=20);
 let m=fixture('starter');const base=capacity(m);m=command(m,{type:'tick',seconds:8});assert.equal(m.coins,134);assert.deepEqual(capacity(m),base);
});
test('dock cover is a separate reserved footprint, unlocked only by the configured access car',()=>{
 const start={...fixture(),mode:'edit'};for(const [x,y] of dockCells){assert.equal(clearedAt(start,x,y),false);assert.equal(validPlacement(start,x,y),false);}
 const m=command(start,{type:'clear',id:'dock-access'});for(const [x,y] of dockCells){assert.equal(clearedAt(m,x,y),true);assert.equal(validPlacement(m,x,y),false);}
 assert.equal(capacity(m).area,76);assert.equal(validPlacement(m,7,9),true);assert.equal(validPlacement(m,7,11),false);
});
test('starter service funds access without expansion; Edit pauses it',()=>{
 let m=fixture('starter');const price=patches.find(p=>p.access).price,sales=Math.ceil((price-m.coins)/economy.saleCoins);m=command(m,{type:'tick',seconds:sales*economy.saleSeconds});assert.ok(m.coins>=price);assert.equal(sales,5);assert.ok(command(m,{type:'clear',id:'dock-access'}).cleared.includes('dock-access'));
 const edit=command(m,{type:'mode',value:'edit'});assert.equal(command(edit,{type:'tick',seconds:100}),edit);
});
test('panning preserves fixed scale and mode changes preserve camera; incompatible old region saves reset',()=>{
 const m=command(fixture(),{type:'pan',x:-8.25,y:-2}),edit=command(m,{type:'mode',value:'edit'});assert.deepEqual(edit.camera,m.camera);assert.equal(command(m,{type:'pan',x:NaN,y:0}),m);assert.deepEqual(restore({getItem:()=>'{broken'}),fixture());assert.deepEqual(restore({getItem:()=>JSON.stringify({...m,version:1})}),fixture());
});
