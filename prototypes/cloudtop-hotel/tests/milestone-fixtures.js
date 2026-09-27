import { createGame, pick, advanceDeal, choiceSuits } from '../engine.js';
const seed='sky-2';
const opening=[0,0,1,0,0,0,0,1,1,1,0,1,1,1,1,0,1,0,2,0];
export const milestoneRuns=new Map();
const state=createGame(seed),moves=[];
while(state.phase==='picking') {
  const index=opening[moves.length]??state.offer.findIndex(c=>c.price<=state.cash);
  const suit=state.offer[index].type==='choice'?choiceSuits(state)[0]:null;
  const before={seed,moves:structuredClone(moves)},count=state.gifts.length;
  if(!pick(state,index,suit))throw new Error('Invalid milestone fixture');
  moves.push([index,suit]);advanceDeal(state);
  for(const gift of state.gifts.slice(count))milestoneRuns.set(gift.floor,{before,move:[index,suit],after:{seed,moves:structuredClone(moves)}});
}
if(milestoneRuns.size!==5)throw new Error('Missing milestone fixtures');
