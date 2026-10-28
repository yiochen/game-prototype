import test from 'node:test';
import assert from 'node:assert/strict';
import {fixture,command,restore,storageKey} from '../design/shop-preview/model.js';
test('Shop purchase pays once, respects limited stock and survives save/restore',()=>{
 let m=fixture();m=command(m,{type:'buy',id:'barrel'});assert.equal(m.coins,1080);assert.equal(m.stock.barrel,0);assert.equal(m.inventory.barrel,1);
 assert.equal(command(m,{type:'buy',id:'barrel'}),m);
 const saved=restore({getItem:k=>k===storageKey?JSON.stringify(m):null});assert.deepEqual(saved,m);
 assert.equal(command(saved,{type:'buy',id:'barrel'}),saved);
});
test('unlimited essentials remain available and unaffordable buys do nothing',()=>{
 let m=fixture();for(let i=0;i<5;i++)m=command(m,{type:'buy',id:'belt'});assert.equal(m.inventory.belt,5);assert.equal(m.stock.belt,null);assert.equal(m.coins,1040);
 const poor=fixture('poor');assert.equal(command(poor,{type:'buy',id:'stool'}),poor);
});
test('placement consumes owned stock; occupied drop and repeated return cannot duplicate',()=>{
 let m=command(fixture(),{type:'buy',id:'plant'});m=command(m,{type:'place',id:'plant',cell:36});assert.equal(m.inventory.plant,0);assert.equal(m.objects.length,1);
 assert.equal(command(m,{type:'place',id:'plant',cell:37}),m);assert.equal(command(m,{type:'place',id:'bogus',cell:37}),m);
 m=command(m,{type:'return',id:1});assert.equal(m.inventory.plant,1);assert.equal(m.objects.length,0);assert.equal(command(m,{type:'return',id:1}),m);
 const owned=command(m,{type:'buy',id:'stool'});assert.equal(command(owned,{type:'place',id:'stool',cell:15}),owned);
});
test('Shop navigation has no simulation pause; the saved Edit mode alone controls clock',()=>{
 const m=fixture(),paused=command(m,{type:'tick',seconds:24});assert.equal(paused,m);
 const live=command(m,{type:'mode',value:'live'}),next=command(live,{type:'tick',seconds:24});assert.equal(next.coins,1276);assert.equal(next.charge,69);
 assert.equal(command(next,{type:'tick',seconds:-5}),next);
});

test('Live mode rejects Shop purchases',()=>{const m=fixture('live');assert.equal(command(m,{type:'buy',id:'belt'}),m);});
