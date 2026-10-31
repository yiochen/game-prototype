import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {fixture,command,neighboring,capacity,restore,storageKey,validPlacement,clearedAt,dockBlockers,dockReady,dockRevealed} from '../design/expansion-preview/model.js';
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
test('native Godot clearance content preserves the approved layout, costs and facings',()=>{
 const native=JSON.parse(readFileSync(new URL('../godot/content/expansion.json',import.meta.url)));
 assert.deepEqual(native.dock_cells,dockCells);assert.deepEqual(native.floor,{columns:21,rows:13,starterColumns:7,backdropRows:3});
 assert.deepEqual(native.patches,patches.map(p=>({id:p.id,name:p.name,art_id:p.family,facing:p.facing,x:p.x,y:p.y,w:p.w,h:p.h,price:p.price})));
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
test('dock stays covered until every side and corner neighbor is cleared, including after reload',()=>{
 const start={...fixture(),mode:'edit'};for(const [x,y] of dockCells){assert.equal(clearedAt(start,x,y),false);assert.equal(validPlacement(start,x,y),false);}
 const expected=['armchair-west','dock-access','trash-9-4','trash-8-5','trash-10-6','trash-10-8','trash-10-9'];assert.deepEqual(dockBlockers(start).map(p=>p.id),expected);
 const partial=command(start,{type:'clear',id:'dock-access'});assert.equal(dockReady(partial),false);assert.equal(capacity(partial).area,76);assert.equal(validPlacement(partial,7,9),true);
 const oldSave=restore({getItem:()=>JSON.stringify(partial)});assert.deepEqual(oldSave.cleared,['dock-access']);assert.equal(dockReady(oldSave),false);
 for(const missing of expected){const m={...start,cleared:expected.filter(id=>id!==missing)};assert.equal(dockReady(m),false,missing+' must block uncovering');assert.deepEqual(dockBlockers(m).map(p=>p.id),[missing]);for(const [x,y] of dockCells){assert.equal(clearedAt(m,x,y),false);assert.equal(validPlacement(m,x,y),false);}}
 let m={...start,cleared:expected};assert.equal(dockReady(m),true);assert.equal(dockRevealed(m),false);assert.ok(patches.some(p=>!m.cleared.includes(p.id)),'unrelated trash need not be removed');for(const [x,y] of dockCells)assert.equal(clearedAt(m,x,y),false);m=command(m,{type:'reveal'});assert.equal(dockRevealed(m),true);for(const [x,y] of dockCells){assert.equal(clearedAt(m,x,y),true);assert.equal(validPlacement(m,x,y),false);}assert.equal(capacity(m).area,94);assert.equal(validPlacement(m,7,11),false);
});
test('starter service funds all surrounding trash and each is reachable before dock access; Edit pauses it',()=>{
 let m=fixture('starter');const price=dockBlockers(m).reduce((n,p)=>n+p.price,0),sales=Math.ceil((price-m.coins)/economy.saleCoins);assert.equal(price,820);m=command(m,{type:'tick',seconds:sales*economy.saleSeconds});assert.ok(m.coins>=price);assert.equal(sales,50);
 const order=['armchair-west','dock-access','trash-8-5','trash-9-4','trash-10-6','trash-10-8','trash-10-9'];for(const [i,id] of order.entries()){const p=patches.find(p=>p.id===id);assert.ok(neighboring(m,p),id+' must be reachable without uncovering');const next=command(m,{type:'clear',id});assert.notEqual(next,m);m=next;assert.equal(dockReady(m),i===order.length-1);}assert.equal(m.coins,0);
 const edit=command(m,{type:'mode',value:'edit'});assert.equal(command(edit,{type:'tick',seconds:100}),edit);
});
test('panning preserves fixed scale and mode changes preserve camera; incompatible old region saves reset',()=>{
 const m=command(fixture(),{type:'pan',x:-8.25,y:-2}),edit=command(m,{type:'mode',value:'edit'});assert.deepEqual(edit.camera,m.camera);assert.equal(command(m,{type:'pan',x:NaN,y:0}),m);assert.deepEqual(restore({getItem:()=>'{broken'}),fixture());assert.deepEqual(restore({getItem:()=>JSON.stringify({...m,version:1})}),fixture());
});

test('reveal is a free, explicit, idempotent saved choice; older already-opened saves migrate',()=>{
 const closed=fixture();assert.equal(command(closed,{type:'reveal'}),closed);
 const ready={...closed,coins:0,cleared:dockBlockers(closed).map(p=>p.id)};assert.equal(dockReady(ready),true);assert.equal(dockRevealed(ready),false);
 const pending=restore({getItem:()=>JSON.stringify(ready)});assert.equal(dockRevealed(pending),false);
 const revealed=command(pending,{type:'reveal'});assert.equal(dockRevealed(revealed),true);assert.equal(revealed.coins,0);assert.deepEqual(revealed.camera,ready.camera);assert.equal(command(revealed,{type:'reveal'}),revealed);
 assert.deepEqual(restore({getItem:()=>JSON.stringify(revealed)}),revealed);
 const old={...ready,version:2};delete old.revealed;assert.equal(dockRevealed(restore({getItem:()=>JSON.stringify(old)})),true);
 old.cleared=['dock-access'];assert.equal(dockRevealed(restore({getItem:()=>JSON.stringify(old)})),false);
});
