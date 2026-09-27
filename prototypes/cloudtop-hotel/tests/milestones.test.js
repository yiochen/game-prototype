import test from 'node:test';
import assert from 'node:assert/strict';
import { BALANCE, createGame, pick, advanceDeal, milestoneReward, eligibleCards, choiceSuits } from '../engine.js';
import { replayRun } from '../score-rules.js';
function atHeight(height) {
  const state = createGame('milestone-test');
  state.links = Array.from({length:height}, (_,id) => ({id,suit:'cat',source:0}));
  state.nextLinkId=height;state.phase='resolving';state.offer=[];return state;
}
test('five automatic gifts follow the schedule and increase coin payouts',()=>{
  assert.deepEqual(BALANCE.milestones.map(m=>[m.floor,m.reward]),[[10,'tips'],[25,'assembler'],[50,'stabilizer'],[100,'assembler'],[200,'stabilizer']]);
  for(const [i,m] of BALANCE.milestones.entries()) {
    const s=atHeight(m.floor-1);s.gifts=BALANCE.milestones.slice(0,i).map(m=>({floor:m.floor}));
    advanceDeal(s);assert.equal(s.gifts.length,i);
    s.links.push({id:s.links.length,suit:'cat'});s.phase='resolving';advanceDeal(s);
    assert.equal(s.gifts.length,i+1);assert.equal(s.gifts.at(-1).key,m.reward);assert.equal(s.phase,'picking');
    if(i)assert.ok(m.coins>BALANCE.milestones[i-1].coins);
    const after=structuredClone(s);assert.equal(advanceDeal(s),false);assert.deepEqual(s,after);
  }
});
test('automatic gifts preserve floors, streaks, locks, coupons, purchases and prize RNG',()=>{
  for(const m of BALANCE.milestones)for(const streak of ['foundation','parade']) {
    const s=atHeight(m.floor);s.gifts=BALANCE.milestones.filter(g=>g.floor<m.floor).map(g=>({floor:g.floor}));
    s[streak]=streak==='foundation'?{suit:'cat',bonus:5}:{bonus:5};s.attunement={suit:'cat',remaining:2};s.rebateRemaining=3;
    const before=structuredClone(s),reward=milestoneReward(s,m);advanceDeal(s);
    for(const field of ['links','nextLinkId','foundation','parade','attunement','rebateRemaining','history','spent','refunded','prizeRng','paradeRng','lastEffect'])assert.deepEqual(s[field],before[field],field);
    assert.equal(s.cash,before.cash+reward.coins);assert.equal(s.deals,before.deals+1);
  }
});
test('all crossed gifts arrive once before drawing offers or the roof',()=>{
  const s=atHeight(205);s.cash=0;const before=s.deals;advanceDeal(s);
  assert.deepEqual(s.gifts.map(g=>g.floor),[10,25,50,100,200]);assert.equal(s.deals,before+1);assert.equal(s.phase,'picking');
  assert.equal(s.upgrades.assembler,3);assert.equal(s.upgrades.stabilizer,3);assert.ok(s.offer.some(c=>c.price<=s.cash));
  s.phase='resolving';advanceDeal(s);assert.equal(s.gifts.length,5);
  const cashless=atHeight(10);cashless.cash=0;advanceDeal(cashless);assert.equal(cashless.cash,5);assert.equal(cashless.phase,'picking');
});
test('a maxed scheduled upgrade always becomes the full coin reward',()=>{
  for(const m of BALANCE.milestones.filter(m=>m.reward!=='tips')) {
    const s=atHeight(m.floor);s.gifts=BALANCE.milestones.filter(g=>g.floor<m.floor).map(g=>({floor:g.floor}));s.upgrades[m.reward]=3;
    const cash=s.cash;advanceDeal(s);assert.equal(s.cash,cash+m.coins);assert.equal(s.gifts.at(-1).key,'tips');assert.equal(s.gifts.at(-1).fallback,true);
    assert.equal(s.upgrades[m.reward],3);assert.ok(!eligibleCards(s).some(c=>c.type===m.reward));
  }
});
test('partially capped upgrades keep remaining levels and compensate overflow',()=>{
  const s=atHeight(200);s.gifts=BALANCE.milestones.slice(0,4).map(m=>({floor:m.floor}));s.upgrades.stabilizer=2;
  advanceDeal(s);assert.equal(s.upgrades.stabilizer,3);assert.equal(s.gifts.at(-1).coins,30);assert.equal(s.gifts.at(-1).levels,1);
});
test('purchase-only replays reconstruct rewards and reject user-selected gift actions',()=>{
  const state=createGame('replay-gifts'),moves=[];
  while(state.gifts.length<2 && state.phase==='picking') {
    const index=state.offer.findIndex(c=>c.price<=state.cash),suit=state.offer[index].type==='choice'?choiceSuits(state)[0]:null;
    moves.push([index,suit]);pick(state,index,suit);advanceDeal(state);
  }
  assert.ok(state.gifts.length);assert.deepEqual(replayRun(state.seed,moves,false),state);
  assert.throws(()=>replayRun(state.seed,[...moves,['gift','tips']],false),/Invalid card choice/);
});
