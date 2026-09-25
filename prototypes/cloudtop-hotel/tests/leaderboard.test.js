import test from 'node:test';
import assert from 'node:assert/strict';
import { createGame, pick, advanceDeal, beginRoof, finishRoof, choiceSuits } from '../engine.js';
import { replayRun, scoreOf, cleanName, compareScores, SCORE_VERSION } from '../score-rules.js';
import { handleLeaderboard } from '../leaderboard-service.js';
import { createGuestbook } from '../guestbook-storage.js';

export function completed(seed = 'guestbook-test') {
  const state = createGame(seed), moves = [];
  while (state.phase === 'picking') {
    const index = state.offer.findIndex(c => c.price <= state.cash);
    const suit = state.offer[index].type === 'choice' ? choiceSuits(state)[0] : null;
    moves.push([index,suit]); pick(state,index,suit); advanceDeal(state);
  }
  beginRoof(state); finishRoof(state);
  return {state, record:{version:SCORE_VERSION,name:'Cloud Keeper',seed,moves}};
}
function memoryStore() {
  let data = null, revision = 0;
  return {
    async get() { return structuredClone(data); },
    async getWithMetadata() { return data ? {data:structuredClone(data),etag:String(revision)} : null; },
    async setJSON(key,next,condition) {
      if (condition.onlyIfNew ? data !== null : condition.onlyIfMatch !== String(revision)) return {modified:false};
      data = structuredClone(next); revision++; return {modified:true,etag:String(revision)};
    },
  };
}
const request = body => new Request('https://cloudtop.test/api/cloudtop-hotel/leaderboard',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});

test('replay derives the finished score and rejects unfinished, invalid, and overlong records',()=>{
  const {record,state} = completed(); assert.deepEqual(replayRun(record.seed,record.moves),state);
  assert.throws(()=>replayRun(record.seed,record.moves.slice(0,-1)),/Finish/);
  assert.throws(()=>replayRun(record.seed,[[3,null]]),/could not be bought/);
  assert.throws(()=>replayRun(record.seed,Array(101).fill([0])),/Invalid/);
  assert.throws(()=>replayRun('../store',record.moves),/Invalid/);
  assert.throws(()=>replayRun(record.seed,[[0,'dragon']]),/Invalid/);
});
test('names normalize and ranking has stable deterministic tie breakers',()=>{
  assert.equal(cleanName('  Café   Sky  '),'Café Sky'); assert.throws(()=>cleanName('<script>')); assert.throws(()=>cleanName(' '));
  const row = {floors:50,neighborhoods:10,coins:0,createdAt:'2026-01-01',id:'a'};
  const ranks = [row,{...row,id:'b',coins:1},{...row,id:'c',neighborhoods:11},{...row,id:'d',floors:51}].sort(compareScores);
  assert.deepEqual(ranks.map(r=>r.id),['d','c','b','a']);
});
test('API computes scores, collapses identical replays and ignores forged score fields',async()=>{
  const store=memoryStore(),{record,state}=completed();
  const response=await handleLeaderboard(request({...record,floors:999999}),store); assert.equal(response.status,201);
  const result=await response.json(); assert.equal(result.rank,1); assert.equal(result.entry.floors,state.links.length); assert.equal(result.entries.length,1);
  const retry=await handleLeaderboard(request({...record,name:'Another name',moves:record.moves.map(([i,s])=>s?[i,s]:[i])}),store);
  assert.equal(retry.status,200); assert.equal((await retry.json()).entry.name,'Cloud Keeper');
  const get=await handleLeaderboard(new Request('https://cloudtop.test/api/cloudtop-hotel/leaderboard'),store);
  assert.equal((await get.json()).entries.length,1); assert.equal(get.headers.get('cache-control'),'no-store');
});
test('simultaneous submissions retry conditional writes without dropping scores',async()=>{
  const store=memoryStore();
  const results=await Promise.all(['one','two','three','four'].map(seed=>handleLeaderboard(request(completed(seed).record),store)));
  assert.ok(results.every(r=>r.status===201)); assert.equal((await store.get()).length,4);
  const busy={...store,async setJSON(){return {modified:false};}};
  assert.equal((await handleLeaderboard(request(completed('five').record),busy)).status,503);
});
test('API rejects malformed, incomplete, foreign-origin and oversized submissions',async()=>{
  const store=memoryStore(), {record}=completed();
  for (const body of [null,{...record,version:'old'},{...record,name:'<img>'},{...record,moves:[]},{...record,moves:[[99]]}]) assert.equal((await handleLeaderboard(request(body),store)).status,400);
  const foreign=request(record); foreign.headers.set('Origin','https://elsewhere.test'); assert.equal((await handleLeaderboard(foreign,store)).status,403);
  assert.equal((await handleLeaderboard(request({...record,name:'a'.repeat(13000)}),store)).status,413);
});
test('local runs survive reload, recompute tampered scores, resume, and fail gracefully without storage',()=>{
  let raw=null; const storage={getItem:()=>raw,setItem:(key,value)=>{raw=value;}};
  const {record,state}=completed(), run={id:'local-1',seed:record.seed,moves:record.moves};
  const book=createGuestbook(storage); book.saveActive({...run,moves:run.moves.slice(0,2)});
  assert.equal(createGuestbook(storage).data.active.moves.length,2);
  assert.equal(book.finish(run,state).saved,true); book.finish(run,state); assert.equal(book.data.runs.length,1);
  const corrupted=JSON.parse(raw); corrupted.runs[0].floors=99999; raw=JSON.stringify(corrupted);
  assert.equal(createGuestbook(storage).data.runs[0].floors,scoreOf(state).floors); assert.equal(createGuestbook(storage).data.active,null);
  const blocked=createGuestbook({getItem(){throw Error();},setItem(){throw Error();}});
  assert.equal(blocked.finish(run,state).saved,false); assert.equal(blocked.data.runs.length,1);
  raw='{bad json'; assert.equal(createGuestbook(storage).data.runs.length,0);
});
