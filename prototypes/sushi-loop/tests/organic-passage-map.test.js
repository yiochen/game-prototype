import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {parseMap,exportMap} from '../design/underwater-map-designer/model.js';
import {findPassage} from '../design/underwater-map-designer/maps/analyze-passage.mjs';
const source=JSON.parse(readFileSync(new URL('../design/underwater-map-designer/maps/sources/turquoise-passage-user-reference.json',import.meta.url),'utf8'));
const generated=JSON.parse(readFileSync(new URL('../design/underwater-map-designer/maps/turquoise-passage-organic-80.json',import.meta.url),'utf8'));
const map=parseMap(generated),opening=v=>v.placements.filter(p=>p.y>=55).sort((a,b)=>a.id.localeCompare(b.id));
const obstacle=new Set(map.placements.filter(p=>p.layer==='obstacles').map(p=>`${p.x}:${80-p.y}`));
const decor=new Set(map.placements.filter(p=>p.layer==='decor').map(p=>`${p.x}:${80-p.y}`));
test('organic 80 is an editor-importable document preserving every user-authored opening placement',()=>{
 assert.equal(map.columns,7);assert.equal(map.rows,80);assert.deepEqual(opening(generated),opening(source));assert.deepEqual(exportMap(map),generated);
});
test('full route has a passage for the preview collider; extension has room for a larger ship and bounded steering',()=>{
 assert.equal(findPassage(map).passable,true);
 assert.equal(findPassage(map,{fromRow:25,width:.8,length:1.6,maxLateralPerRow:3}).passable,true);
});
test('generated tight sections require steering and provide a wider island/recovery pocket',()=>{
 for(const [a,b] of [[26,34],[41,50],[51,68],[69,77]]){
  const straight=Array.from({length:7},(_,x)=>x).filter(x=>Array.from({length:b-a+1},(_,i)=>i+a).every(r=>!obstacle.has(`${x}:${r}`)));
  assert.equal(straight.length,0,`Rows ${a}–${b} must require lateral movement`);
 }
 assert.ok([35,39].every(r=>Array.from({length:7},(_,x)=>x).filter(x=>!obstacle.has(`${x}:${r}`)).length>=5));
 assert.ok([36,37,38].every(r=>obstacle.has(`3:${r}`)&&[1,2,4,5].every(x=>!obstacle.has(`${x}:${r}`))));
 const density=(a,b)=>[...obstacle].filter(k=>{const r=Number(k.split(':')[1]);return r>=a&&r<=b;}).length/((b-a+1)*7);
 assert.ok(density(1,8)<.2);assert.ok(density(26,34)>.55);assert.ok(density(51,68)>.55);assert.ok(density(78,80)<.2);
});
test('generated decor accompanies obstacles and every generated obstacle is dressed or adjacent to a dressed cell',()=>{
 const near=[[0,0],[1,0],[-1,0],[0,1],[0,-1]];
 for(const key of decor){const [x,r]=key.split(':').map(Number);if(r<26)continue;assert.ok(near.some(([dx,dr])=>obstacle.has(`${x+dx}:${r+dr}`)),`Floating decor at ${key}`);}
 for(const key of obstacle){const [x,r]=key.split(':').map(Number);if(r<26)continue;assert.ok(near.some(([dx,dr])=>decor.has(`${x+dx}:${r+dr}`)),`Undressed obstacle at ${key}`);}
});
