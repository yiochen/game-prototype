// Review data and tuning only. Native gameplay/save data are deliberately separate.
import {startingChefs, applicants} from '../../wireframe/fixtures.js';
export const storageKey='sushi-loop-issue17-ui-review-v1';
import {balance} from './balance.js';
export {balance} from './balance.js';
export const beltCells=[13,14,15,16,31,32,33,34];
export const speed=(chef,level=chef.level)=>Number(((parseFloat(chef.speed)||1)+(level-1)*chef.growthRate).toFixed(2));
export const cost=chef=>chef.level*balance.upgradeBase;
export const tier=level=>balance.tiers[balance.thresholds.findLastIndex(n=>level>=n)];
export function fixture(state='develop'){
 const staff=[...startingChefs,applicants[1]].map((c,i)=>({...c,assigned:i===0,cell:i===0?19:null,recipe:i===0?'salmon':null}));
 if(state==='max')staff[0].level=staff[0].ceiling;
 if(state==='near-max')staff[0].level=staff[0].ceiling-1;
 if(state==='unassigned')Object.assign(staff[0],{assigned:false,cell:null});
 return {version:1,coins:state==='poor'?60:1240,staff};
}
export function validCell(model,cell,id){return Number.isInteger(cell)&&cell>=0&&cell<42&&!beltCells.includes(cell)&&beltCells.some(b=>Math.abs(b-cell)===6||(Math.floor(b/6)===Math.floor(cell/6)&&Math.abs(b-cell)===1))&&!model.staff.some(c=>c.id!==id&&c.assigned&&c.cell===cell);}
export function command(model,action){
 const c=model.staff.find(c=>c.id===action.id);if(!c)return model;
 const replace=next=>({...model,staff:model.staff.map(x=>x.id===c.id?next:x)});
 if(action.type==='upgrade'){
  // An input carries the level that was previewed. Replayed input is a no-op.
  if(action.expectedLevel!==c.level||c.level>=c.ceiling||model.coins<cost(c))return model;
  return {...replace({...c,level:c.level+1}),coins:model.coins-cost(c)};
 }
 if(action.type==='unassign')return c.assigned?replace({...c,assigned:false,cell:null}):model;
 if(action.type==='place')return !c.assigned&&validCell(model,action.cell,c.id)?replace({...c,assigned:true,cell:action.cell,recipe:null}):model;
 if(action.type==='fire')return {...model,staff:model.staff.filter(x=>x.id!==c.id)};
 if(action.type==='prepare'&&c.assigned&&action.recipe&&action.requiredLevel<=c.level)return replace({...c,recipe:action.recipe});
 return model;
}
export function restore(storage,state){
 try{const v=JSON.parse(storage.getItem(storageKey));const ids=new Set();if(v?.version===1&&Number.isFinite(v.coins)&&v.coins>=0&&Array.isArray(v.staff)&&v.staff.every(c=>{if(!['lena','omar','mateo'].includes(c.id)||ids.has(c.id))return false;ids.add(c.id);return Number.isInteger(c.level)&&c.level>=1&&c.level<=c.ceiling&&c.ceiling<=12&&Number.isFinite(c.growthRate)&&(!c.assigned||Number.isInteger(c.cell));}))return v;}catch{}
 return fixture(state);
}
