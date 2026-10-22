import {worldRasterPlan,paintWorldRaster} from './resources/browser/world-sprite-raster.js';
import {spriteFrame,clipFor,groundRoot,orderPlacements,sceneBounds} from './resources/browser/sprite-layout.js';
const params=new URLSearchParams(location.search),root='./resources/';
const own=await fetch(root+'catalog-object.json').then(r=>r.json());
const context=await fetch(root+'context/objects.json').then(r=>r.json());
const objects=[own,...context.filter(o=>o.id!==own.id)];
const tone=params.get('tone')||'gray',pitch=+(params.get('pitch')||128),mode=params.get('mode')||'views',phase=+(params.get('phase')||0),clip=params.get('clip')||'static';
const bgs={gray:'#7d8792',light:'#eee7d9',dark:'#13202d',water:'#124b65'};document.body.style.background=bgs[tone];
const title=document.getElementById('title');title.textContent=`Native coral round01 · ${mode} · cell ${pitch}px · ${tone} · common phase ${phase}`;
let placements,grid;
if(mode==='context'){placements=own.interactions[0].placements;grid=own.interactions[0].gridSize;}
else if(mode==='repeated'){placements=Array.from({length:9},(_,i)=>({object:own.id,x:i%3,y:Math.floor(i/3),direction:'S',clip}));grid=[3,3];}
else {placements=['N','E','S','W'].map((direction,i)=>({object:own.id,x:i*2,y:0,direction,clip}));grid=[7,1];}
const bounds=sceneBounds(placements,objects,128,grid),ns='http://www.w3.org/2000/svg';
const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',bounds.join(' '));svg.style.width=`${bounds[2]*pitch/128}px`;svg.style.height=`${bounds[3]*pitch/128}px`;svg.style.background=bgs[tone];svg.style.display='block';document.getElementById('scene').append(svg);
// Same wholecanvas SVG foreignObject presentation as actual SpriteScene, no imageRendering override.
const foreign=document.createElementNS(ns,'foreignObject'),canvas=document.createElement('canvas');foreign.append(canvas);svg.append(foreign);canvas.style.display='block';canvas.style.width='100%';canvas.style.height='100%';
const cache=new Map();async function load(url){if(cache.has(url))return cache.get(url);const img=new Image();img.src=url;await img.decode();cache.set(url,img);return img;}
window.paintAt=async(seconds=0)=>{
 const sprites=orderPlacements(placements,objects).map(p=>{const o=objects.find(o=>o.id===p.object),d=p.direction||'S';const f=spriteFrame(o,clipFor(o,p.clip),d,seconds);const[x,y]=groundRoot(p,o,128);const url=o.id===own.id?'../../candidates/round-01/atlases/'+(p.clip||own.clips[0].id)+'-'+d+'.png':root+'context/'+f.image;
 return{url,rect:f.rect,x:x-f.root[0]+phase,y:y-f.root[1]+phase,width:f.frameSize[0],height:f.frameSize[1],object:o.id,direction:d,frame:f.frame};});
 const plan=worldRasterPlan(sprites,bounds),images=await Promise.all(sprites.map(s=>load(s.url)));paintWorldRaster(canvas,plan,images);foreign.setAttribute('x',plan.x);foreign.setAttribute('y',plan.y);foreign.setAttribute('width',plan.width/plan.scale);foreign.setAttribute('height',plan.height/plan.scale);
 await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
 window.evidence={ready:true,seconds,mode,pitch,tone,phase,viewport:[innerWidth,innerHeight],bounds,plan:{...plan,sprites},intermediateSmoothing:canvas.getContext('2d').imageSmoothingEnabled,finalFiltering:'ordinary SVG foreignObject wholecanvas filtering; no imageRendering override',placements,actualFrames:sprites.map(s=>({object:s.object,direction:s.direction,frame:s.frame})),canvasSize:[canvas.width,canvas.height],rgba:undefined};return window.evidence;
};
window.canvasRGBA=()=>Array.from(canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data);
await window.paintAt(+(params.get('seconds')||0));
