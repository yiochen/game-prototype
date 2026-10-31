import {floor,patches,economy,dockCells} from './balance.js';
export const storageKey='sushi-loop-issue19-expansion-review-v2';
const dockMask=new Set(dockCells.map(c=>c.join(','))),dockBorder=new Set();
for(const [x,y] of dockCells)for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++)if(!dockMask.has(`${x+dx},${y+dy}`))dockBorder.add(`${x+dx},${y+dy}`);
const dockTrash=patches.filter(p=>Array.from({length:p.h},(_,dy)=>Array.from({length:p.w},(_,dx)=>dockBorder.has(`${p.x+dx},${p.y+dy}`)).some(Boolean)).some(Boolean));
export function dockBlockers(m){return dockTrash.filter(p=>!m.cleared.includes(p.id));}
export function dockReady(m){return dockBlockers(m).length===0;}
export function dockRevealed(m){return m.revealed===true&&dockReady(m);}
export function fixture(state='restaurant'){
 return {version:3,revealed:state==='expanded',mode:state==='edit'?'edit':'live',coins:state==='poor'?60:state==='starter'?economy.startingCoins:economy.reviewCoins,cleared:state==='expanded'?dockTrash.map(p=>p.id):state==='almost'?dockTrash.filter(p=>p.id!=='dock-access').map(p=>p.id):state==='partial'?['dock-access']:[],objects:[],camera:{x:state==='bare'?0:state==='starter'||state==='edge'?1.25:-4,y:0},elapsed:0,category:'layout'};
}
export function restore(storage,state){try{let m=JSON.parse(storage.getItem(storageKey));if(m?.version===2&&Array.isArray(m.cleared)&&!Object.hasOwn(m,'revealed'))m={...m,version:3,revealed:dockReady(m)};if(m?.version===3&&typeof m.revealed==='boolean'&&(!m.revealed||dockReady(m))&&['live','edit'].includes(m.mode)&&Number.isFinite(m.coins)&&m.coins>=0&&Array.isArray(m.cleared)&&new Set(m.cleared).size===m.cleared.length&&m.cleared.every(id=>patches.some(p=>p.id===id))&&Array.isArray(m.objects)&&Number.isFinite(m.camera?.x)&&Number.isFinite(m.camera?.y)&&Number.isFinite(m.elapsed))return m;}catch{}return fixture(state);}
export function clearedAt(m,x,y){return x>=0&&x<floor.columns&&y>=floor.backdropRows&&y<floor.rows&&(x<floor.starterColumns||(dockRevealed(m)&&dockCells.some(c=>c[0]===x&&c[1]===y))||patches.some(p=>m.cleared.includes(p.id)&&x>=p.x&&x<p.x+p.w&&y>=p.y&&y<p.y+p.h));}
export function neighboring(m,p){return !m.cleared.includes(p.id)&&(Array.from({length:p.h},(_,i)=>clearedAt(m,p.x-1,p.y+i)||clearedAt(m,p.x+p.w,p.y+i)).some(Boolean)||Array.from({length:p.w},(_,i)=>clearedAt(m,p.x+i,p.y-1)||clearedAt(m,p.x+i,p.y+p.h)).some(Boolean));}
export function capacity(m){const area=70+patches.filter(p=>m.cleared.includes(p.id)).reduce((n,p)=>n+p.w*p.h,0);return {area,staff:3+Math.floor((area-70)/9),arrivalPotential:area/70};}
export function validPlacement(m,x,y){return clearedAt(m,x,y)&&!m.objects.some(o=>o.x===x&&o.y===y)&&!(x<7&&((y===6&&x>=1&&x<=4)||(y===9&&x>=2&&x<=5)))&&!dockCells.some(c=>c[0]===x&&c[1]===y);}
export function command(m,a){
 switch(a.type){
  case 'clear':{const p=patches.find(p=>p.id===a.id);return p&&neighboring(m,p)&&m.coins>=p.price?{...m,coins:m.coins-p.price,cleared:[...m.cleared,p.id]}:m;}
  case 'reveal':return dockReady(m)&&!m.revealed?{...m,revealed:true}:m;
  case 'mode':return ['live','edit'].includes(a.value)?{...m,mode:a.value}:m;
  case 'pan':return Number.isFinite(a.x)&&Number.isFinite(a.y)?{...m,camera:{x:Math.max(-23,Math.min(3,a.x)),y:Math.max(-15,Math.min(5,a.y))}}:m;
  case 'category':return ['people','layout','floor'].includes(a.value)?{...m,category:a.value}:m;
  case 'place':return m.mode==='edit'&&m.objects.length<4&&Number.isInteger(a.x)&&Number.isInteger(a.y)&&validPlacement(m,a.x,a.y)?{...m,objects:[...m.objects,{x:a.x,y:a.y,art:'stool-wood'}]}:m;
  case 'tick':{if(m.mode!=='live'||!Number.isFinite(a.seconds)||a.seconds<=0)return m;const elapsed=m.elapsed+a.seconds,payments=Math.floor(elapsed/economy.saleSeconds)-Math.floor(m.elapsed/economy.saleSeconds);return {...m,elapsed,coins:m.coins+payments*economy.saleCoins};}
  default:return m;
 }
}
