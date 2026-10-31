import {floor,patches,economy,dockCells} from './balance.js';
export const storageKey='sushi-loop-issue19-expansion-review-v2';
export function fixture(state='restaurant'){
 return {version:2,mode:state==='edit'?'edit':'live',coins:state==='poor'?60:state==='starter'?economy.startingCoins:economy.reviewCoins,cleared:state==='expanded'?['dock-access']:[],objects:[],camera:{x:state==='starter'||state==='edge'?1.25:-4,y:0},elapsed:0,category:'layout'};
}
export function restore(storage,state){try{const m=JSON.parse(storage.getItem(storageKey));if(m?.version===2&&['live','edit'].includes(m.mode)&&Number.isFinite(m.coins)&&m.coins>=0&&Array.isArray(m.cleared)&&m.cleared.every(id=>patches.some(p=>p.id===id))&&Array.isArray(m.objects)&&Number.isFinite(m.camera?.x)&&Number.isFinite(m.camera?.y)&&Number.isFinite(m.elapsed))return m;}catch{}return fixture(state);}
export function clearedAt(m,x,y){return x>=0&&x<floor.columns&&y>=floor.backdropRows&&y<floor.rows&&(x<floor.starterColumns||(m.cleared.includes('dock-access')&&dockCells.some(c=>c[0]===x&&c[1]===y))||patches.some(p=>m.cleared.includes(p.id)&&x>=p.x&&x<p.x+p.w&&y>=p.y&&y<p.y+p.h));}
export function neighboring(m,p){return !m.cleared.includes(p.id)&&(Array.from({length:p.h},(_,i)=>clearedAt(m,p.x-1,p.y+i)||clearedAt(m,p.x+p.w,p.y+i)).some(Boolean)||Array.from({length:p.w},(_,i)=>clearedAt(m,p.x+i,p.y-1)||clearedAt(m,p.x+i,p.y+p.h)).some(Boolean));}
export function capacity(m){const area=70+patches.filter(p=>m.cleared.includes(p.id)).reduce((n,p)=>n+p.w*p.h,0);return {area,staff:3+Math.floor((area-70)/9),arrivalPotential:area/70};}
export function validPlacement(m,x,y){return clearedAt(m,x,y)&&!m.objects.some(o=>o.x===x&&o.y===y)&&!(x<7&&((y===6&&x>=1&&x<=4)||(y===9&&x>=2&&x<=5)))&&!(m.cleared.includes('dock-access')&&dockCells.some(c=>c[0]===x&&c[1]===y));}
export function command(m,a){
 switch(a.type){
  case 'clear':{const p=patches.find(p=>p.id===a.id);return p&&neighboring(m,p)&&m.coins>=p.price?{...m,coins:m.coins-p.price,cleared:[...m.cleared,p.id]}:m;}
  case 'mode':return ['live','edit'].includes(a.value)?{...m,mode:a.value}:m;
  case 'pan':return Number.isFinite(a.x)&&Number.isFinite(a.y)?{...m,camera:{x:Math.max(-23,Math.min(3,a.x)),y:Math.max(-15,Math.min(5,a.y))}}:m;
  case 'category':return ['people','layout','floor'].includes(a.value)?{...m,category:a.value}:m;
  case 'place':return m.mode==='edit'&&m.objects.length<4&&Number.isInteger(a.x)&&Number.isInteger(a.y)&&validPlacement(m,a.x,a.y)?{...m,objects:[...m.objects,{x:a.x,y:a.y,art:'stool-wood'}]}:m;
  case 'tick':{if(m.mode!=='live'||!Number.isFinite(a.seconds)||a.seconds<=0)return m;const elapsed=m.elapsed+a.seconds,payments=Math.floor(elapsed/economy.saleSeconds)-Math.floor(m.elapsed/economy.saleSeconds);return {...m,elapsed,coins:m.coins+payments*economy.saleCoins};}
  default:return m;
 }
}
