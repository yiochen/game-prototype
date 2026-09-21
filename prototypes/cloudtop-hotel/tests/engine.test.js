import test from 'node:test';
import assert from 'node:assert/strict';
import { BALANCE, createGame, eligibleCards, baseCards, preview, pick, advanceDeal, chain, segments, recallLinks, overgrowLinks, finished, weightedPick, mysteryOutcomes, upgradeValue, choiceSuits } from '../engine.js';
function offer(s, family, type, suit) {
 const c=eligibleCards(s).find(c=>c.family===family&&c.type===type&&(suit===undefined||c.suit===suit));
 assert.ok(c,`Missing ${family}/${type}/${suit}`);s.offer=[c];return c;
}
function buy(s,family,type,suit){offer(s,family,type,suit);assert.equal(pick(s,0),true);advanceDeal(s);return s.history.at(-1);}

test('balance data defines all prices, strengths and normalized relative roll boundaries',()=>{
 assert.ok(Object.values(BALANCE.families).every(weight=>weight>0));
 for(const c of Object.values(BALANCE.base)) assert.ok(c.price>0&&c.weight>0);
 for(const c of Object.values(BALANCE.reactor)){assert.equal(c.prices.length,(c.values ?? c.outcomesByLevel).length);assert.ok(c.prices.every(p=>p>0));}
 const outcomes=BALANCE.base.mystery.outcomes;
 assert.deepEqual([0,.599999,.6,.899999,.9,.999999].map(r=>weightedPick(outcomes,r).links),[1,1,3,3,8,8]);
 const old=BALANCE.base.single.price;
 try{BALANCE.base.single.price=4;assert.equal(eligibleCards(createGame('tune')).find(c=>c.type==='single').price,4);}finally{BALANCE.base.single.price=old;}
});
test('Fixed creates exactly its printed links; power purchases add no incidental link',()=>{
 const s=createGame('fixed');buy(s,'base','single','bunny');buy(s,'base','triple','frog');assert.equal(chain(s),4);
 buy(s,'reactor','suit','bunny');assert.equal(chain(s),4);assert.equal(s.cash,85);
 assert.equal(baseCards(s).length,2);assert.equal(s.history.length,3);
});
test('Recall replaces Polish, counts segments regardless of length, and preserves existing links',()=>{
 const s=createGame('growth');buy(s,'base','single','bunny');buy(s,'base','triple','bunny');buy(s,'base','triple','frog');
 assert.deepEqual(segments(s).map(r=>r.length),[4,3]);
 assert.deepEqual([...new Set(eligibleCards(s).filter(c=>c.family==='growth').map(c=>c.type))],['recall','overgrow']);
 const before=structuredClone(s.links);
 buy(s,'growth','recall','bunny');assert.equal(chain(s),8);
 assert.deepEqual(s.links.slice(0,before.length),before);
 assert.deepEqual(segments(s).map(r=>r.length),[4,3,1]);
 buy(s,'growth','recall','bunny');assert.equal(s.history.at(-1).links,2);assert.equal(chain(s),10);
 buy(s,'growth','overgrow');assert.equal(chain(s),12);
 buy(s,'growth','recall','bunny');assert.equal(s.history.at(-1).links,2);assert.equal(chain(s),14);
 assert.equal(segments(s).length,3);
});
test('splitting six Bunny links increases Recall; purchase boundaries do not',()=>{
 const long=createGame('long');buy(long,'base','triple','bunny');buy(long,'reactor','stabilizer');buy(long,'base','triple','bunny');
 const split=createGame('split');buy(split,'base','triple','bunny');buy(split,'base','single','frog');buy(split,'base','triple','bunny');
 assert.equal(segments(long).length,1);assert.equal(recallLinks(long,'bunny'),1);assert.equal(recallLinks(split,'bunny'),2);
 assert.equal(preview(split,offer(split,'growth','recall','bunny')).headline,'+2');
});
test('Recall snapshots once, appends its own suit, and only future purchases reuse those links',()=>{
 const s=createGame('snapshot');buy(s,'base','single','bunny');buy(s,'base','single','frog');
 const first=buy(s,'growth','recall','bunny');assert.equal(first.links,1);assert.equal(chain(s),3);
 const second=buy(s,'growth','recall','bunny');assert.equal(second.links,2);assert.equal(chain(s),5);
 assert.deepEqual(segments(s).map(r=>[r.suit,r.length]),[['bunny',1],['frog',1],['bunny',3]]);
 const third=buy(s,'growth','recall','bunny');assert.equal(third.links,2);assert.equal(segments(s,'bunny').length,2);
});
test('Overgrow appends the longest run’s suit, snapshots its length, and caps its bonus',()=>{
 const s=createGame('longest');buy(s,'base','triple','bunny');buy(s,'base','triple','bunny');buy(s,'base','triple','bunny');buy(s,'base','single','frog');
 for(const amount of [4,4,4,6,8]){
  const before=structuredClone(s.links);assert.equal(overgrowLinks(s),amount);const c=offer(s,'growth','overgrow');assert.equal(preview(s,c).headline,`+${amount}`);pick(s,0);advanceDeal(s);assert.equal(s.lastEffect.added,amount);
  assert.deepEqual(s.links.slice(0,before.length),before);assert.ok(s.links.slice(before.length).every(l=>l.suit==='bunny'));
 }
 assert.deepEqual(segments(s).map(r=>[r.suit,r.length]),[['bunny',9],['frog',1],['bunny',26]]);
 const tie=createGame('tie');buy(tie,'base','single','frog');buy(tie,'base','single','bunny');buy(tie,'growth','overgrow');
 assert.deepEqual(segments(tie).map(r=>[r.suit,r.length]),[['frog',1],['bunny',1],['frog',1]]);
});
test('upgrade levels replace each other, disappear at max, and affect only future purchases',()=>{
 const s=createGame('levels');buy(s,'base','single','bunny');
 for(let level=1;level<=3;level++){
  const c=offer(s,'reactor','suit','bunny');assert.equal(c.level,level);pick(s,0);advanceDeal(s);
  assert.equal(upgradeValue(s,'suit','bunny'),BALANCE.reactor.suit.values[level-1]);
 }
 assert.equal(eligibleCards(s).some(c=>c.family==='reactor'&&c.type==='suit'&&c.suit==='bunny'),false);
 assert.equal(baseCards(s)[0].links,1);
 buy(s,'reactor','assembler');const next=buy(s,'base','single','bunny');assert.equal(next.links,5);
 const recalled=buy(s,'growth','recall','bunny');assert.equal(recalled.links,1);
});
test('Stabilizer uses explicit odds in one draw, with Reactor applied afterward',()=>{
 const s=createGame('mystery');buy(s,'reactor','stabilizer');buy(s,'reactor','stabilizer');buy(s,'reactor','suit','frog');buy(s,'reactor','assembler');
 const m=buy(s,'base','mystery','frog');assert.ok(mysteryOutcomes(s).some(o=>o.links===m.result));assert.equal(m.links,m.result+1);assert.equal(m.rolls,undefined);
 const r=buy(s,'growth','recall','frog');assert.equal(r.links,1);assert.ok(s.history.every(c=>!('nodes' in c)));
});
test('Rebate cannot stack, affects only next three bases, and requires full price upfront',()=>{
 const s=createGame('rebate');buy(s,'wealth','rebate');assert.equal(s.rebateRemaining,3);
 assert.equal(eligibleCards(s).some(c=>c.type==='rebate'),false);
 buy(s,'reactor','suit','bunny');assert.equal(s.rebateRemaining,3);
 for(let n=0;n<3;n++){const before=s.cash;const c=offer(s,'base','single','bunny');assert.equal(preview(s,c).cashAfter,before-1);pick(s,0);advanceDeal(s);assert.equal(s.cash,before-1);}
 assert.equal(s.refunded,6);assert.equal(s.rebateRemaining,0);assert.ok(eligibleCards(s).some(c=>c.type==='rebate'));
 s.cash=2;offer(s,'base','single','bunny');s.rebateRemaining=1;const before=structuredClone(s);assert.equal(pick(s,0),false);assert.deepEqual(s,before);
});
test('Vault uses cash after its price and zero-effect offers are excluded',()=>{
 const s=createGame('vault');assert.ok(!eligibleCards(s).some(c=>c.family==='growth'));
 const c=offer(s,'wealth','vault');assert.equal(preview(s,c).headline,'+9');buy(s,'wealth','vault');assert.equal(chain(s),9);assert.equal(s.cash,92);
 buy(s,'base','single','frog');assert.deepEqual(eligibleCards(s).filter(c=>c.type==='recall').map(c=>c.suit),['bunny','frog']);
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
 const s=createGame('end');s.cash=3;offer(s,'base','single','bunny');pick(s,0);assert.equal(finished(s),false);
 advanceDeal(s);assert.equal(finished(s),true);assert.equal(chain(s),1);assert.equal(s.cash,0);assert.equal(advanceDeal(s),false);
 for(let seed=0;seed<50;seed++){const s=createGame(seed);s.cash=6;offer(s,'base','single','bunny');pick(s,0);advanceDeal(s);assert.ok(s.offer.some(c=>c.price<=3));assert.equal(new Set(s.offer.map(c=>c.id)).size,s.offer.length);}
});
test('full runs terminate, money reconciles and identical seeds replay exactly',()=>{
 for(let seed=0;seed<100;seed++){
  function run(){const s=createGame(seed);while(!finished(s)){
   assert.ok(s.history.length<100);const index=s.offer.findIndex(c=>c.price<=s.cash);assert.ok(index>=0);
   const previous=s.cash, before=structuredClone(s.links);assert.equal(pick(s,index,s.offer[index].type==='choice'?choiceSuits(s)[0]:undefined),true);assert.deepEqual(s.links.slice(0,before.length),before);assert.ok(s.cash<previous);advanceDeal(s);
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
  buy(s,'base','mystery','frog');finalRng.push(s.prizeRng);
 }
 assert.equal(new Set(finalRng).size,1);
});

test('Choice 1 validates selection before spending and stacks the chosen Reactor, Assembler, Rebate and Foundation',()=>{
 const s=createGame('choice');buy(s,'reactor','suit','frog');buy(s,'reactor','assembler');buy(s,'wealth','rebate');buy(s,'strategy','foundation');
 const c=offer(s,'base','choice'),before=structuredClone(s);
 assert.ok(c.price>BALANCE.base.single.price);
 assert.equal(pick(s,0),false);assert.equal(pick(s,0,'invalid'),false);assert.deepEqual(s,before);
 assert.equal(preview(s,c,'frog').headline,'+4');assert.equal(preview(s,c,'bunny').headline,'+3');assert.deepEqual(s,before);
 assert.equal(pick(s,0,'frog'),true);assert.equal(s.history.at(-1).suit,'frog');assert.equal(s.history.at(-1).links,4);assert.equal(s.cash,before.cash-c.price+2);assert.equal(s.foundation.bonus,1);
 assert.deepEqual(s.links.map(l=>l.suit),Array(4).fill('frog'));
});

test('Foundation advances on matching suited purchases, pauses on suitless cards and ends on switching',()=>{
 const s=createGame('foundation');buy(s,'strategy','foundation');
 assert.equal(chain(s),0);assert.ok(!eligibleCards(s).some(c=>c.type==='foundation'));
 for(const [family,type,amount] of [['base','single',2],['growth','recall',3],['reactor','suit',3]]){
  const c=offer(s,family,type,'bunny');assert.equal(preview(s,c).foundationBonus,s.foundation.bonus+1);
  assert.equal(pick(s,0),true);advanceDeal(s);assert.equal(s.history.at(-1).links,amount);
 }
 const before=structuredClone(s.foundation);buy(s,'wealth','rebate');assert.deepEqual(s.foundation,before);
 const c=offer(s,'base','single','frog');assert.equal(preview(s,c).endsFoundation,true);assert.equal(preview(s,c).headline,'+1');
 pick(s,0);advanceDeal(s);assert.equal(s.foundation,null);assert.equal(s.history.at(-1).links,1);
 assert.ok(eligibleCards(s).some(c=>c.type==='foundation'));buy(s,'strategy','foundation');buy(s,'base','single','frog');assert.equal(s.foundation.bonus,1);
});

test('Mosaic variations print all suit orders, append exactly that pattern and end Foundation',()=>{
 const initial=createGame('mosaic'), mosaics=eligibleCards(initial).filter(c=>c.type==='mosaic');
 assert.equal(mosaics.length,24);assert.equal(new Set(mosaics.map(c=>c.id)).size,24);
 for(const pattern of BALANCE.base.mosaic.patterns){
  const variants=mosaics.filter(c=>c.pattern===pattern.id);assert.equal(variants.length,6);
  assert.deepEqual(new Set(variants.map(c=>c.sequence[0])),new Set(BALANCE.suits.map(s=>s.id)));
  assert.deepEqual(new Set(variants.map(c=>c.sequence.at(-1))),new Set(BALANCE.suits.map(s=>s.id)));
 }
 for(const mosaic of mosaics){
  const s=createGame('mosaic');buy(s,'base','single',mosaic.sequence[0]);buy(s,'reactor','suit',mosaic.sequence[0]);buy(s,'reactor','assembler');buy(s,'wealth','rebate');buy(s,'strategy','foundation');
  const before=structuredClone(s.links);s.offer=[mosaic];assert.equal(preview(s,mosaic).headline,'+3');assert.equal(preview(s,mosaic).endsFoundation,true);
  assert.equal(pick(s,0),true);assert.deepEqual(s.links.slice(0,before.length),before);assert.deepEqual(s.links.slice(before.length).map(l=>l.suit),mosaic.sequence);
  assert.equal(s.foundation,null);assert.equal(s.history.at(-1).refund,2);assert.equal(s.rebateRemaining,2);
 }
});

test('Attunement locks exactly the next shops including Choice, pauses Mosaic, and does not refresh',()=>{
 const s=createGame('attunement');buy(s,'strategy','foundation');buy(s,'strategy','attunement','frog');
 assert.deepEqual(s.attunement,{suit:'frog',remaining:3});assert.equal(s.foundation.bonus,1);
 const prize=s.prizeRng;
 for(let remaining=3;remaining>0;remaining--){
  assert.equal(s.attunement.remaining,remaining);
  for(const c of [...s.offer,...eligibleCards(s)]){assert.ok(!c.suit||c.suit==='frog');assert.ok(!c.sequence);assert.notEqual(c.type,'attunement');}
  assert.deepEqual(choiceSuits(s),['frog']);
  if(remaining===3){
   offer(s,'base','choice');const before=structuredClone(s);assert.equal(pick(s,0,'bunny'),false);assert.deepEqual(s,before);
   assert.equal(pick(s,0,'frog'),true);advanceDeal(s);
  } else if(remaining===2) buy(s,'wealth','rebate');
  else buy(s,'base','single','frog');
 }
 assert.equal(s.attunement,null);assert.equal(s.foundation.bonus,3);assert.equal(s.prizeRng,prize);
 assert.equal(choiceSuits(s).length,3);assert.ok(eligibleCards(s).some(c=>c.type==='mosaic'));assert.ok(eligibleCards(s).some(c=>c.suit==='bunny'));assert.ok(eligibleCards(s).some(c=>c.type==='attunement'));
});

test('Attunement preserves affordable fallback and final-purchase settlement',()=>{
 for(let seed=0;seed<30;seed++){
  const s=createGame(seed);buy(s,'strategy','attunement','cat');s.cash=7;
  offer(s,'base','choice');pick(s,0,'cat');advanceDeal(s);
  assert.ok(s.offer.some(c=>c.price<=3));assert.ok(s.offer.every(c=>!c.suit||c.suit==='cat'));assert.equal(new Set(s.offer.map(c=>c.id)).size,s.offer.length);
  offer(s,'base','single','cat');pick(s,0);assert.equal(finished(s),false);advanceDeal(s);assert.equal(finished(s),true);assert.equal(chain(s),2);
 }
});
