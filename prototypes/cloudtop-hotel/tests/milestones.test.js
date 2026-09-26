import test from 'node:test';
import assert from 'node:assert/strict';
import { BALANCE, createGame, pick, advanceDeal, claimMilestone, pendingMilestone, milestoneReward, eligibleCards, beginRoof, choiceSuits } from '../engine.js';
import { replayRun, scoreOf } from '../score-rules.js';

function pending(height = 10) {
  const state = createGame('milestone-test');
  state.links = Array.from({length:height}, (_,id) => ({id,suit:'cat',source:0}));
  state.nextLinkId = height; state.phase = 'resolving'; state.offer = [];
  advanceDeal(state); return state;
}
test('milestones trigger only at 10, 25, 50, 100 and 200 and gifts get stronger', () => {
  assert.deepEqual(BALANCE.milestones.map(m => m.floor), [10,25,50,100,200]);
  for (const [i,m] of BALANCE.milestones.entries()) {
    const s = pending(m.floor - 1); s.gifts = BALANCE.milestones.slice(0,i).map(m => ({floor:m.floor}));
    assert.equal(pendingMilestone(s), undefined);
    s.links.push({id:s.links.length,suit:'cat'}); s.phase='resolving'; advanceDeal(s);
    assert.equal(s.phase,'milestone'); assert.equal(pendingMilestone(s).floor,m.floor);
    if (i) { const previous = BALANCE.milestones[i-1]; assert.ok(m.coins > previous.coins); assert.ok(m.levels >= previous.levels); assert.ok(m.bonusCoins > previous.bonusCoins); }
  }
});
test('all gift choices preserve floors, streaks, locks, coupons, purchases and prize RNG', () => {
  for (const key of ['tips','assembler','stabilizer','suit:bunny','suit:frog','suit:cat']) {
    for (const streak of ['foundation','parade']) {
      const s = pending(); s[streak] = streak === 'foundation' ? {suit:'cat',bonus:5} : {bonus:5};
      s.attunement = {suit:'cat',remaining:2}; s.rebateRemaining=3;
      const before = structuredClone(s), reward=milestoneReward(s,key);
      assert.equal(pick(s,0),false); assert.equal(beginRoof(s),false);
      assert.equal(claimMilestone(s,key),true);
      for (const field of ['links','nextLinkId','foundation','parade','attunement','rebateRemaining','history','spent','refunded','prizeRng','paradeRng','lastEffect']) assert.deepEqual(s[field],before[field],`${key}: ${field}`);
      assert.equal(s.cash,before.cash+reward.coins);
      if(key!=='tips') assert.equal(s.upgrades[key],1);
      assert.equal(s.deals,before.deals+1);
      const claimed=structuredClone(s);assert.equal(claimMilestone(s,key),false);assert.deepEqual(s,claimed);
    }
  }
});
test('crossed milestones queue in order, reject invalid claims and rescue a cashless run before the roof', () => {
  const s=pending(205);s.cash=0;
  const before=structuredClone(s);assert.equal(claimMilestone(s,'suit:dragon'),false);assert.deepEqual(s,before);
  for(const m of BALANCE.milestones) {
    assert.equal(pendingMilestone(s).floor,m.floor);assert.equal(beginRoof(s),false);
    assert.equal(claimMilestone(s,'tips'),true);
  }
  assert.equal(s.phase,'picking');assert.equal(s.cash,130);assert.equal(s.gifts.length,5);
  assert.equal(s.deals,before.deals+1);
  assert.ok(s.offer.some(c=>c.price<=s.cash));
});
test('upgrade caps convert excess levels to coins and the next shop contains no stale upgrade', () => {
  const s=pending(200);s.gifts=BALANCE.milestones.slice(0,4).map(m=>({floor:m.floor}));s.upgrades.stabilizer=2;
  assert.deepEqual(milestoneReward(s,'stabilizer'), {key:'stabilizer',before:2,after:3,levels:1,coins:30});
  claimMilestone(s,'stabilizer');assert.equal(s.upgrades.stabilizer,3);
  assert.ok(!s.offer.some(c=>c.type==='stabilizer'));assert.ok(!eligibleCards(s).some(c=>c.type==='stabilizer'));
  const maxed=pending(25);maxed.gifts=[{floor:10}];maxed.upgrades.assembler=3;
  claimMilestone(maxed,'assembler');assert.equal(maxed.gifts.at(-1).coins,8);assert.equal(maxed.upgrades.assembler,3);
});
test('gift replay restores pending and claimed rewards, rejects forgery and includes tips in score', () => {
  const state=createGame('replay-gifts'),moves=[];
  while(state.phase==='picking') {
    const index=state.offer.findIndex(c=>c.price<=state.cash),suit=state.offer[index].type==='choice'?choiceSuits(state)[0]:null;
    moves.push([index,suit]);pick(state,index,suit);advanceDeal(state);
  }
  assert.equal(state.phase,'milestone');assert.deepEqual(replayRun(state.seed,moves,false),state);
  assert.throws(()=>replayRun(state.seed,[...moves,[0,null]],false),/could not be bought/);
  assert.throws(()=>replayRun(state.seed,[['gift','tips']],false),/Invalid milestone/);
  assert.throws(()=>replayRun(state.seed,[...moves,['gift','tips','extra']],false),/Invalid milestone/);
  moves.push(['gift','stabilizer']);claimMilestone(state,'stabilizer');
  assert.deepEqual(replayRun(state.seed,moves,false),state);
  assert.throws(()=>replayRun(state.seed,[...moves,['gift','tips']],false),/Invalid milestone/);
  assert.equal(scoreOf(state).coins,state.cash);
});
