import {worldRasterPlan,paintWorldRaster} from './world-sprite-raster.js';
import {spriteFrame,groundRoot,orderPlacements} from './sprite-layout.js';
const get=async u=>await(await fetch(u)).json();
const original=await get('../resources/catalog-object.json'),middle=await get('../resources/wreck-middle-catalog.json'),edge=await get('../resources/wreck-edge-catalog.json');
const captures=await get('../../candidates/round-01/capture-records.json');
const cases=[{id:'logical128-integer',cssScale:1,rootOffset:[0,0],pan:[0,0]},{id:'logical128-fractional',cssScale:.773,rootOffset:[.375,.625],pan:[.213,-.371]},{id:'phone32-integer',cssScale:.25,rootOffset:[0,0],pan:[0,0]},{id:'phone32-fractional',cssScale:.25,rootOffset:[.375,.625],pan:[.213,-.371]}];
const c=cases.find(c=>c.id===new URLSearchParams(location.search).get('case'));window.evidence={case:c,actualDPR:devicePixelRatio,fixtures:[]};window.nativeCanvasPNGs=[];
const image=url=>new Promise((yes,no)=>{const i=new Image;i.onload=()=>yes(i);i.onerror=no;i.src=url;});
const next={S:'E',E:'N',N:'W',W:'S'};
for(const o of [original,middle,edge])for(const d of ['N','E','S','W'])o.clips[0].directions[d].image=o===original?'../../candidates/round-01/atlases/static-'+d+'.png':'../resources/'+o.id+'/'+d+'.png';
for(const kind of ['middle-L','mixed-edge-L'])for(const d of ['N','E','S','W']){
 const record=captures.records.find(r=>r.path===kind+'/'+d+'.png'),size=record.camera.frame,origin=record.camera.root,roots=record.assembly.roots;
 const west=kind==='middle-L'?middle:edge,objects=[original,middle,edge];
 const placements=[{id:kind+'-corner-'+d,object:original.id,direction:d,x:-.5,y:-.5,offset:c.rootOffset},{id:kind+'-west-'+d,object:west.id,direction:d,x:Math.round(roots[1][0])-.5,y:-Math.round(roots[1][1])-.5,offset:c.rootOffset},{id:kind+'-north-'+d,object:middle.id,direction:next[d],x:Math.round(roots[2][0])-.5,y:-Math.round(roots[2][1])-.5,offset:c.rootOffset}];
 const ordered=orderPlacements(placements,objects),sprites=ordered.map(p=>{const o=objects.find(o=>o.id===p.object),f=spriteFrame(o,o.clips[0],p.direction,0),r=groundRoot(p,o,128);return{x:r[0]-f.root[0],y:r[1]-f.root[1],width:f.frameSize[0],height:f.frameSize[1],rect:f.rect,url:new URL(f.image,location.href).href};});
 const bounds=[-origin[0]+c.pan[0],-origin[1]+c.pan[1],...size],plan=worldRasterPlan(sprites,bounds),raw=document.createElement('canvas');paintWorldRaster(raw,plan,await Promise.all(sprites.map(s=>image(s.url))));
 const ref={x:-origin[0]+c.rootOffset[0],y:-origin[1]+c.rootOffset[1],width:size[0],height:size[1],rect:[0,0,size[0]*2,size[1]*2],url:new URL('../../candidates/round-01/'+kind+'/'+d+'.png',location.href).href};
 const control=document.createElement('canvas'),refPlan=worldRasterPlan([ref],bounds);paintWorldRaster(control,refPlan,[await image(ref.url)]);
 window.nativeCanvasPNGs.push({id:kind+'-'+d+'-independent',png:raw.toDataURL()},{id:kind+'-'+d+'-native-control',png:control.toDataURL()});
 for(const [bg,color]of [['light','#eeeeee'],['gray','#808080'],['dark','#151923']]){
  const sec=document.createElement('section');sec.id=kind+'-'+d+'-'+bg;sec.style.width=size[0]*c.cssScale+'px';const label=document.createElement('p');label.textContent=kind+' / '+d+' / '+bg;sec.append(label);
  const canvas=document.createElement('canvas');canvas.width=size[0]*2;canvas.height=size[1]*2;const ctx=canvas.getContext('2d');ctx.fillStyle=color;ctx.fillRect(0,0,canvas.width,canvas.height);ctx.imageSmoothingEnabled=false;ctx.drawImage(raw,(plan.x-bounds[0])*2,(plan.y-bounds[1])*2);canvas.style.width=size[0]*c.cssScale+'px';canvas.style.height=size[1]*c.cssScale+'px';sec.append(canvas);document.querySelector('#fixture').append(sec);
  window.evidence.fixtures.push({kind,direction:d,background:bg,color,orderedPlacements:ordered,plan,bounds,referencePlan:refPlan,nativeSize:[raw.width,raw.height],controlSize:[control.width,control.height],displayCSS:[size[0]*c.cssScale,size[1]*c.cssScale],nativeSmoothing:raw.getContext('2d').imageSmoothingEnabled,displayCanvasSmoothing:ctx.imageSmoothingEnabled});
 }
}
window.ready=true;
