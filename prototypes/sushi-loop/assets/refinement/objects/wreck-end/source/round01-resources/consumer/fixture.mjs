import {worldRasterPlan,paintWorldRaster} from './world-sprite-raster.js';
import {spriteFrame,groundRoot,orderPlacements} from './sprite-layout.js';
const base=await(await fetch('../contracts/catalog-object.json')).json();
const ids=['wreck-end','wreck-middle','wreck-edge'];
const cases=[{id:'logical128-integer',cssScale:1,rootOffset:[0,0],pan:[0,0]},{id:'logical128-fractional',cssScale:.773,rootOffset:[.375,.625],pan:[.213,-.371]},{id:'phone32-integer',cssScale:.25,rootOffset:[0,0],pan:[0,0]},{id:'phone32-fractional',cssScale:.25,rootOffset:[.375,.625],pan:[.213,-.371]}];
const c=cases.find(c=>c.id===new URLSearchParams(location.search).get('case'));window.evidence={case:c,actualDPR:devicePixelRatio,fixtures:[]};window.nativeCanvasPNGs=[];
const image=url=>new Promise((yes,no)=>{const i=new Image;i.onload=()=>yes(i);i.onerror=no;i.src=url;});
for(const d of ['N','E','S','W']){
 const vertical=['E','W'].includes(d),size=vertical?[192,608]:[448,352],origin=vertical?[96,d==='W'?504:248]:[d==='S'?352:96,248],angle={N:Math.PI,E:Math.PI/2,S:0,W:-Math.PI/2}[d];
 const objects=ids.map(id=>{const o=structuredClone(base);o.id=id;for(const x of 'NESW')o.clips[0].directions[x].image=id==='wreck-end'?'../../../candidates/round-01/atlases/static-'+x+'.png':'../canonical/'+id+'/frames/'+x+'.png';return o;});
 const placements=ids.map((id,i)=>({id:id+'-'+d,object:id,direction:d,x:-i*Math.cos(angle)-.5,y:i*Math.sin(angle)-.5,offset:c.rootOffset}));
 // Eliminate representational trigonometric epsilon only at exact cardinal world-cell positions.
 for(const p of placements){p.x=Math.round(p.x*2)/2;p.y=Math.round(p.y*2)/2;}
 const ordered=orderPlacements(placements,objects),sprites=ordered.map(p=>{const o=objects.find(o=>o.id===p.object),f=spriteFrame(o,o.clips[0],d,0),r=groundRoot(p,o,128);return{x:r[0]-f.root[0],y:r[1]-f.root[1],width:f.frameSize[0],height:f.frameSize[1],rect:f.rect,url:new URL(f.image,location.href).href};});
 const bounds=[-origin[0]+c.pan[0],-origin[1]+c.pan[1],...size],plan=worldRasterPlan(sprites,bounds),raw=document.createElement('canvas');paintWorldRaster(raw,plan,await Promise.all(sprites.map(s=>image(s.url))));
 const ref={x:-origin[0]+c.rootOffset[0],y:-origin[1]+c.rootOffset[1],width:size[0],height:size[1],rect:[0,0,size[0]*2,size[1]*2],url:new URL('../../../candidates/round-01/connected-native/'+d+'.png',location.href).href};
 const control=document.createElement('canvas'),refPlan=worldRasterPlan([ref],bounds);paintWorldRaster(control,refPlan,[await image(ref.url)]);
 window.nativeCanvasPNGs.push({id:d+'-independent',png:raw.toDataURL()},{id:d+'-native-control',png:control.toDataURL()});
 for(const [bg,color]of [['light','#eeeeee'],['gray','#808080'],['dark','#151923']]){
  const sec=document.createElement('section');sec.id=d+'-'+bg;sec.style.width=size[0]*c.cssScale+'px';const label=document.createElement('p');label.textContent=d+' / '+bg;sec.append(label);
  const checks=[];
  for(const [label,layer,rplan]of [['independent',raw,plan],['native-control',control,refPlan]]){
   const caption=document.createElement('p');caption.textContent=label;sec.append(caption);
   const canvas=document.createElement('canvas');canvas.width=size[0]*2;canvas.height=size[1]*2;const ctx=canvas.getContext('2d');ctx.fillStyle=color;ctx.fillRect(0,0,canvas.width,canvas.height);ctx.imageSmoothingEnabled=false;ctx.drawImage(layer,(rplan.x-bounds[0])*2,(rplan.y-bounds[1])*2);canvas.style.width=size[0]*c.cssScale+'px';canvas.style.height=size[1]*c.cssScale+'px';sec.append(canvas);checks.push({label,nearestAfterResize:ctx.imageSmoothingEnabled===false,wholeCSSImageRendering:getComputedStyle(canvas).imageRendering});
  }
  document.querySelector('#fixture').append(sec);for(let n=0;n<checks.length;n++)checks[n].wholeCSSImageRendering=getComputedStyle(sec.querySelectorAll('canvas')[n]).imageRendering;
  window.evidence.fixtures.push({direction:d,background:bg,color,orderedPlacements:ordered,plan,bounds,referencePlan:refPlan,nativeSize:[raw.width,raw.height],controlSize:[control.width,control.height],nativeNearestRestoredAfterResize:checks.every(v=>v.nearestAfterResize),actualDisplayChecks:checks,displayCSS:[size[0]*c.cssScale,size[1]*c.cssScale]});
 }
}
window.ready=true;
