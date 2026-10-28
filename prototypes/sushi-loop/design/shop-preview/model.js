import {catalog,timing} from './balance.js';
export const storageKey='sushi-loop-issue18-shop-review-v2';
export const beltCells=[15,16,17,18,29,30,31,32];
export function fixture(state='shop') {return {version:1,coins:state==='poor'?24:1240,stock:Object.fromEntries(catalog.map(i=>[i.id,i.stock])),inventory:Object.fromEntries(catalog.map(i=>[i.id,0])),objects:[],mode:state==='live'?'live':'edit',category:'layout',camera:{x:0,y:0},elapsed:0,charge:45,nextId:1};}
export function restore(storage,state){try{const v=JSON.parse(storage.getItem(storageKey));if(v?.version===1&&Number.isFinite(v.coins)&&v.coins>=0&&['live','edit'].includes(v.mode)&&v.camera&&Number.isFinite(v.camera.x)&&Number.isFinite(v.camera.y)&&Array.isArray(v.objects)&&catalog.every(i=>Number.isInteger(v.inventory?.[i.id])&&v.inventory[i.id]>=0&&(i.stock===null?v.stock?.[i.id]===null:Number.isInteger(v.stock?.[i.id])&&v.stock[i.id]>=0)))return v;}catch{}return fixture(state);}
export function validCell(model,cell){return Number.isInteger(cell)&&cell>=0&&cell<49&&!beltCells.includes(cell)&&![22,24].includes(cell)&&!model.objects.some(o=>o.cell===cell);}
export function command(m,a){
 if(a.type==='buy'){const i=catalog.find(i=>i.id===a.id);if(m.mode!=='edit'||!i||m.coins<i.price||m.stock[i.id]===0)return m;return {...m,coins:m.coins-i.price,inventory:{...m.inventory,[i.id]:m.inventory[i.id]+1},stock:{...m.stock,[i.id]:m.stock[i.id]===null?null:m.stock[i.id]-1}};}
 if(a.type==='place'){if(!catalog.some(i=>i.id===a.id)||!m.inventory[a.id]||!validCell(m,a.cell))return m;return {...m,inventory:{...m.inventory,[a.id]:m.inventory[a.id]-1},objects:[...m.objects,{id:m.nextId,kind:a.id,cell:a.cell,rotation:0}],nextId:m.nextId+1};}
 if(a.type==='return'){const o=m.objects.find(o=>o.id===a.id);if(!o)return m;return {...m,objects:m.objects.filter(o=>o!==o),inventory:{...m.inventory,[o.kind]:m.inventory[o.kind]+1}};}
 if(a.type==='mode'&&['edit','live'].includes(a.value))return {...m,mode:a.value};
 if(a.type==='category'&&['people','layout','floor'].includes(a.value))return {...m,category:a.value};
 if(a.type==='pan'&&Number.isFinite(a.x)&&Number.isFinite(a.y))return {...m,camera:{x:Math.max(-120,Math.min(120,a.x)),y:Math.max(-70,Math.min(70,a.y))}};
 if(a.type==='tick'&&m.mode==='live'&&Number.isFinite(a.seconds)&&a.seconds>0){const elapsed=m.elapsed+a.seconds,sales=Math.floor(elapsed/timing.saleSeconds)-Math.floor(m.elapsed/timing.saleSeconds);return {...m,elapsed,coins:m.coins+sales*timing.saleCoins,charge:Math.min(timing.chargeSeconds,m.charge+a.seconds)};}
 return m;
}
