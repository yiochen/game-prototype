import { clipFor, spriteFrame, groundRoot, orderPlacements, sceneBounds } from './resources/browser/sprite-layout.js';
import { worldRasterPlan, paintWorldRaster } from './resources/browser/world-sprite-raster.js';
const own=await (await fetch('./resources/inputs/catalog-object.json')).json();
const selected=await (await fetch('./resources/browser/selected-objects.json')).json();
const main=selected.find(o=>o.id==='submarine-yellow');
const eel=selected.find(o=>o.id==='creature-eel');
const q=new URLSearchParams(location.search);const D=q.get('d')||'S',phase=Number(q.get('f')||1),pitch=Number(q.get('pitch')||128),bg=q.get('bg')||'#dce1df';
for(const c of own.clips)for(const d of Object.keys(c.directions)) c.directions[d].image=`./publication-source/${c.id}-${d}.png`;
for(const o of [main,eel])for(const c of o.clips)for(const d of Object.keys(c.directions)) c.directions[d].image=`./resources/browser/${c.directions[d].image}`;
// Separate published native sprite specimens share the actual catalog placement API.
// They are not attached to the main image or composited as integrated art.
const objects=[own,main,eel];
const placements=[{object:own.id,x:0,y:1,direction:D,clip:'active'},{object:main.id,x:1.5,y:0,direction:D,clip:'upgraded-dock-ready'},{object:eel.id,x:4,y:1,direction:D,clip:'swim'}];
const bounds=sceneBounds(placements,objects,128,[6,4]);
const seconds=(phase-1)/12;
const sprites=orderPlacements(placements,objects).map(p=>{const o=objects.find(o=>o.id===p.object),clip=clipFor(o,p.clip);const fr=spriteFrame(o,clip,p.direction,o===own?seconds:0);const [x,y]=groundRoot(p,o,128);return {url:fr.image,rect:fr.rect,x:x-fr.root[0],y:y-fr.root[1],width:fr.frameSize[0],height:fr.frameSize[1],object:o.id,frame:fr.frame};});
const plan=worldRasterPlan(sprites,bounds);const loaded=await Promise.all(sprites.map(s=>new Promise((ok,fail)=>{const i=new Image();i.onload=()=>ok(i);i.onerror=()=>fail(Error(s.url));i.src=s.url;})));
const canvas=document.createElement('canvas');paintWorldRaster(canvas,plan,loaded);canvas.style.cssText='display:block;width:100%;height:100%';
const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox',bounds.join(' '));svg.style.width=`${bounds[2]*pitch/128}px`;svg.style.height=`${bounds[3]*pitch/128}px`;svg.style.background=bg;
const fo=document.createElementNS('http://www.w3.org/2000/svg','foreignObject');for(const [k,v]of Object.entries({x:plan.x,y:plan.y,width:plan.width/plan.scale,height:plan.height/plan.scale}))fo.setAttribute(k,String(v));fo.append(canvas);svg.append(fo);
const title=document.createElement('p');title.textContent=`SOURCE DIAGNOSTIC · ${D} phase ${phase}/12 · cell ${pitch}px · separate own sprite / snapshotted assembled upgraded Sub (legacy catalog) / eel. No sprite attachment overlay.`;
document.body.append(title,svg);window.consumerEvidence={direction:D,phase,pitch,bounds,plan:{...plan,sprites},source:'Exact snapshotted sprite-layout.js + world-sprite-raster.js, common native canvas -> one browser scale. Unchanged production source art is comparison context only.',ready:true};document.body.dataset.ready='true';
