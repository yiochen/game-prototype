import test from 'node:test';
import assert from 'node:assert/strict';
import { BALANCE, createGame, eligibleCards, baseCards, preview, pick, advanceDeal, chain, segments, recallLinks, overgrowLinks, finished, weightedPick, mysteryOutcomes, upgradeValue } from '../engine.js';
function offer(s, family, type, suit) {
 const c=eligibleCards(s).find(c=>c.family===family&&c.type===type&&(suit===undefined||c.suit===suit));
 assert.ok(c,`Missing ${family}/${type}/${suit}`);s.offer=[c];return c;
}
function buy(s,family,type,suit){offer(s,family,type,suit);assert.equal(pick(s,0),true);advanceDeal(s);return s.history.at(-1);}

test('balance data defines all prices, strengths and normalized relative roll boundaries',()=>{
 assert.equal(Object.values(BALANCE.families).reduce((a,b)=>a+b,0),100);
 for(const c of Object.values(BALANCE.base)) assert.ok(c.price>0&&c.weight>0);
 for(const c of Object.values(BALANCE.reactor)){assert.equal(c.prices.length,(c.values ?? c.outcomesByLevel).length);assert.ok(c.prices.every(p=>p>0));}
 const outcomes=BALANCE.base.mystery.outcomes;
 assert.deepEqual([0,.599999,.6,.899999,.9,.999999].map(r=>weightedPick(outcomes,r).links),[1,1,3,3,8,8]);
 const old=BALANCE.base.single.price;
 try{BALANCE.base.single.price=4;assert.equal(eligibleCards(createGame('tune')).find(c=>c.type==='single').price,4);}finally{BALANCE.base.single.price=old;}
});
test('Fixed creates exactly its printed links; power purchases add no incidental link',()=>{
 const s=createGame('fixed');buy(s,'base','single','sun');buy(s,'base','triple','moon');assert.equal(chain(s),4);
 buy(s,'reactor','suit','sun');assert.equal(chain(s),4);assert.equal(s.cash,85);
 assert.equal(baseCards(s).length,2);assert.equal(s.history.length,3);
});
test('Growth counts contiguous segments, and extends them without creating false breaks',()=>{
 const s=createGame('growth');buy(s,'base','single','sun');buy(s,'base','triple','sun');buy(s,'base','triple','moon');
 assert.deepEqual(segments(s).map(r=>r.length),[4,3]);
 buy(s,'growth','recall','sun');assert.equal(chain(s),10);
 buy(s,'growth','polish','sun');assert.equal(chain(s),12);assert.deepEqual(segments(s).map(r=>r.length),[5,3,4]);
 buy(s,'growth','recall','sun');assert.equal(s.history.at(-1).links,6);assert.equal(chain(s),18);
 buy(s,'growth','overgrow');assert.equal(chain(s),23);
 buy(s,'growth','recall','sun');assert.equal(s.history.at(-1).links,6);assert.equal(chain(s),29);
 assert.equal(segments(s).length,3);
});
test('splitting six Sun links increases Recall; purchase boundaries do not',()=>{
 const long=createGame('long');buy(long,'base','triple','sun');buy(long,'reactor','stabilizer');buy(long,'base','triple','sun');
 const split=createGame('split');buy(split,'base','triple','sun');buy(split,'base','single','moon');buy(split,'base','triple','sun');
 assert.equal(segments(long).length,1);assert.equal(recallLinks(long,'sun'),3);assert.equal(recallLinks(split,'sun'),6);
 assert.equal(preview(split,offer(split,'growth','recall','sun')).headline,'+6');
});
test('Recall snapshots once, appends its own suit, and only future purchases reuse those links',()=>{
 const s=createGame('snapshot');buy(s,'base','single','sun');buy(s,'base','single','moon');
 const first=buy(s,'growth','recall','sun');assert.equal(first.links,1);assert.equal(chain(s),3);
 const second=buy(s,'growth','recall','sun');assert.equal(second.links,2);assert.equal(chain(s),5);
 assert.deepEqual(segments(s).map(r=>[r.suit,r.length]),[['sun',1],['moon',1],['sun',3]]);
});
test('Overgrow automatically selects the longest run, scales with length, and caps its bonus',()=>{
 const s=createGame('longest');buy(s,'base','triple','sun');buy(s,'base','triple','sun');buy(s,'base','triple','sun');buy(s,'base','single','moon');
 for(const amount of [4,6,8,8]){assert.equal(overgrowLinks(s),amount);const c=offer(s,'growth','overgrow');assert.equal(preview(s,c).headline,`+${amount}`);pick(s,0);advanceDeal(s);assert.equal(s.lastEffect.added,amount);}
 assert.deepEqual(segments(s).map(r=>[r.suit,r.length]),[['sun',35],['moon',1]]);
 const tie=createGame('tie');buy(tie,'base','single','moon');buy(tie,'base','single','sun');buy(tie,'growth','overgrow');
 assert.deepEqual(segments(tie).map(r=>[r.suit,r.length]),[['moon',2],['sun',1]]);
});
test('upgrade levels replace each other, disappear at max, and affect only future purchases',()=>{
 const s=createGame('levels');buy(s,'base','single','sun');
 for(let level=1;level<=3;level++){
  const c=offer(s,'reactor','suit','sun');assert.equal(c.level,level);pick(s,0);advanceDeal(s);
  assert.equal(upgradeValue(s,'suit','sun'),BALANCE.reactor.suit.values[level-1]);
 }
 assert.equal(eligibleCards(s).some(c=>c.family==='reactor'&&c.type==='suit'&&c.suit==='sun'),false);
 assert.equal(baseCards(s)[0].links,1);
 buy(s,'reactor','assembler');const next=buy(s,'base','single','sun');assert.equal(next.links,5);
 const recalled=buy(s,'growth','recall','sun');assert.equal(recalled.links,3);
});
test('Stabilizer uses explicit odds in one draw, with Reactor applied afterward',()=>{
 const s=createGame('mystery');buy(s,'reactor','stabilizer');buy(s,'reactor','stabilizer');buy(s,'reactor','suit','moon');buy(s,'reactor','assembler');
 const m=buy(s,'base','mystery','moon');assert.ok(mysteryOutcomes(s).some(o=>o.links===m.result));assert.equal(m.links,m.result+1);assert.equal(m.rolls,undefined);
 const r=buy(s,'growth','recall','moon');assert.equal(r.links,Math.min(m.links,BALANCE.growth.recall.linksPerSegmentCap));assert.ok(s.history.every(c=>!('nodes' in c)));
});
test('Rebate cannot stack, affects only next three bases, and requires full price upfront',()=>{
 const s=createGame('rebate');buy(s,'wealth','rebate');assert.equal(s.rebateRemaining,3);
 assert.equal(eligibleCards(s).some(c=>c.type==='rebate'),false);
 buy(s,'reactor','suit','sun');assert.equal(s.rebateRemaining,3);
 for(let n=0;n<3;n++){const before=s.cash;const c=offer(s,'base','single','sun');assert.equal(preview(s,c).cashAfter,before-1);pick(s,0);advanceDeal(s);assert.equal(s.cash,before-1);}
 assert.equal(s.refunded,6);assert.equal(s.rebateRemaining,0);assert.ok(eligibleCards(s).some(c=>c.type==='rebate'));
 s.cash=2;offer(s,'base','single','sun');s.rebateRemaining=1;const before=structuredClone(s);assert.equal(pick(s,0),false);assert.deepEqual(s,before);
});
test('Vault uses cash after its price and zero-effect offers are excluded',()=>{
 const s=createGame('vault');assert.ok(!eligibleCards(s).some(c=>c.family==='growth'));
 const c=offer(s,'wealth','vault');assert.equal(preview(s,c).headline,'+9');buy(s,'wealth','vault');assert.equal(chain(s),9);assert.equal(s.cash,92);
 buy(s,'base','single','moon');assert.deepEqual(eligibleCards(s).filter(c=>c.type==='recall').map(c=>c.suit),['sun','moon']);
 s.cash=17;assert.ok(!eligibleCards(s).some(c=>c.type==='vault'));
});
test('invalid inputs and double purchases are no-ops; reading previews never rolls',()=>{
 const s=createGame('guards');const before=structuredClone(s);
 for(const i of [-1,3,0.5])assert.equal(pick(s,i),false);
 for(let n=0;n<10;n++)for(const c of s.offer)preview(s,c);
 assert.deepEqual(s,before);assert.equal(pick(s,0),true);const resolving=structuredClone(s);
 assert.equal(pick(s,0),false);assert.deepEqual(s,resolving);
});
test('final result waits for reveal, and an affordable fallback keeps runs alive',()=>{
 const s=createGame('end');s.cash=3;offer(s,'base','single','sun');pick(s,0);assert.equal(finished(s),false);
 advanceDeal(s);assert.equal(finished(s),true);assert.equal(chain(s),1);assert.equal(s.cash,0);assert.equal(advanceDeal(s),false);
 for(let seed=0;seed<50;seed++){const s=createGame(seed);s.cash=6;offer(s,'base','single','sun');pick(s,0);advanceDeal(s);assert.ok(s.offer.some(c=>c.price<=3));assert.equal(new Set(s.offer.map(c=>c.id)).size,s.offer.length);}
});
test('full runs terminate, money reconciles and identical seeds replay exactly',()=>{
 for(let seed=0;seed<100;seed++){
  function run(){const s=createGame(seed);while(!finished(s)){
   assert.ok(s.history.length<100);const index=s.offer.findIndex(c=>c.price<=s.cash);assert.ok(index>=0);
   const previous=s.cash;assert.equal(pick(s,index),true);assert.ok(s.cash<previous);advanceDeal(s);
  }assert.equal(s.cash,BALANCE.startingCash-s.spent+s.refunded);assert.equal(new Set(s.links.map(l=>l.id)).size,s.links.length);assert.ok(s.links.every(l=>BALANCE.suits.some(s=>s.id===l.suit)));assert.equal(s.links.length,s.history.reduce((n,e)=>n+e.links,0));assert.ok(!eligibleCards(s).some(c=>c.price<=s.cash));return s;}
  assert.deepEqual(run(),run());
 }
});

test('explicit Stabilizer tables match old best-of probabilities and use one RNG draw at every level',()=>{
 const finalRng=[];
 for(let level=0;level<=3;level++){
  const s=createGame('single-draw');s.upgrades.stabilizer=level;
  const outcomes=mysteryOutcomes(s), n=level+1;
  const expected=[.6**n,.9**n-.6**n,1-.9**n];
  outcomes.forEach((o,i)=>assert.ok(Math.abs(o.weight/100-expected[i])<1e-12));
  const counts=[0,0,0];for(let i=0;i<10000;i++)counts[outcomes.indexOf(weightedPick(outcomes,(i+.5)/10000))]++;
  assert.deepEqual(counts,outcomes.map(o=>Math.round(o.weight*100)));
  buy(s,'base','mystery','moon');finalRng.push(s.prizeRng);
 }
 assert.equal(new Set(finalRng).size,1);
});
