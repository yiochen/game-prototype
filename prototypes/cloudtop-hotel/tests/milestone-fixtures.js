import { createGame, pick, advanceDeal, claimMilestone, choiceSuits, pendingMilestone } from '../engine.js';
const seed='sky-2';
const opening=[[0,null],[0,'bunny'],[1,null],[0,null],[0,null],[0,null],[0,null],[1,null],[1,null],[1,null],[0,null],[1,null],[1,'bunny'],[1,null],[1,null],[0,null],[1,null],[0,null],[2,null],[0,null]];
export const pendingRuns = new Map();
const s=createGame(seed), moves=[];
let purchase=0;
while(s.phase==='picking') {
  const index=opening[purchase]?.[0] ?? s.offer.findIndex(c=>c.price<=s.cash);
  const suit=opening[purchase]?.[1] ?? (s.offer[index].type==='choice'?choiceSuits(s)[0]:null);
  if(!pick(s,index,suit)) throw new Error('Invalid milestone fixture');
  moves.push([index,suit]);advanceDeal(s);purchase++;
  while(s.phase==='milestone') {
    pendingRuns.set(pendingMilestone(s).floor,{seed,moves:structuredClone(moves)});
    claimMilestone(s,'tips');moves.push(['gift','tips']);
  }
}
if(pendingRuns.size!==5)throw new Error(`Missing milestone fixtures: ${[...pendingRuns.keys()]}`);
