import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {backdropLayout} from '../wireframe/restaurant-backdrop-layout.js';
const root=new URL('../assets/production/',import.meta.url);
const library=JSON.parse(readFileSync(new URL('library.json',root)));
test('the approved catalog replaces the retired entrance and lays out three walls, gate, then walls',()=>{
  assert.ok(!library.objects.some(o=>o.id==='entry-finished'));
  assert.equal(existsSync(new URL('sprites/entry-finished',root)),false);
  const hash=path=>createHash('sha256').update(readFileSync(path)).digest('hex');
  for (const [id,source,width] of [['backdrop-wall','wall-plain',1],['backdrop-entrance','gate',4]]) {
    const object=library.objects.find(o=>o.id===id);
    assert.deepEqual(object.footprint,[width,3]);
    assert.deepEqual(object.rootCell,[width/2,3]);
    assert.equal(object.sourceScale,3);
    assert.equal(object.backdrop.lighting,'uniform ambient');
    assert.deepEqual(Object.keys(object.clips[0].directions),['S']);
    const path=new URL(object.clips[0].directions.S.image,root);
    assert.equal(hash(path),hash(new URL(`../restaurant-backdrop/uniform35/renders/${source}.png`,root)));
    assert.ok(existsSync(new URL(object.source.blend,root)));
  }
  const layout=backdropLayout(21);
  assert.deepEqual(layout.walls.map(p=>p.x),[0,1,2,...Array.from({length:14},(_,i)=>i+7)]);
  assert.deepEqual([layout.gate.x,layout.gate.width,layout.opening.x,layout.opening.width],[3,4,4,2]);
  const coverage=Array(21).fill(0);
  for(const piece of [...layout.walls,layout.gate])for(let x=piece.x;x<piece.x+piece.width;x++)coverage[x]++;
  assert.ok(coverage.every(count=>count===1));
});
