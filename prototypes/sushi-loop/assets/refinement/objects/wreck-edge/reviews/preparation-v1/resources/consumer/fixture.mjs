import {worldRasterPlan,paintWorldRaster} from './world-sprite-raster.js';
import {spriteFrame,groundRoot,orderPlacements} from './sprite-layout.js';
const original=await(await fetch('../inputs/catalog-object.json')).json();
const canonical=structuredClone(original);canonical.id='wreck-middle';canonical.name='Approved middle02 metadata-equivalent native frame';
const cases=[{id:'logical128-integer',cssScale:1,rootOffset:[0,0],pan:[0,0]},{id:'logical128-fractional',cssScale:.773,rootOffset:[.375,.625],pan:[.213,-.371]},{id:'phone32-integer',cssScale:.25,rootOffset:[0,0],pan:[0,0]},{id:'phone32-fractional',cssScale:.25,rootOffset:[.375,.625],pan:[.213,-.371]}];
const c=cases.find(c=>c.id===new URLSearchParams(location.search).get('case'));window.evidence={case:c,actualDPR:devicePixelRatio,fixtures:[]};window.nativeCanvasPNGs=[];
const image=url=>new Promise((yes,no)=>{const i=new Image;i.onload=()=>yes(i);i.onerror=no;i.src=url;});
for(const d of ['N','E','S','W']){
 const vertical=['E','W'].includes(d),size=vertical?[192,608]:[448,352],origin=vertical?[96,376]:[224,248];
 original.clips[0].directions[d].image='../../baseline/original-canonical-rig/'+d+'.png';canonical.clips[0].directions[d].image='../canonical/frames/'+d+'.png';
 const sign=['N','W'].includes(d)?-1:1;
 const placements=[-1,0,1].map((v,i)=>({id:d+'-local'+v,object:v===0?original.id:canonical.id,direction:d,x:(vertical?0:v*sign)-.5,y:(vertical?-v*sign:0)-.5,offset:c.rootOffset}));
 const objects=[original,canonical],ordered=orderPlacements(placements,objects);
 const sprites=ordered.map(p=>{const o=objects.find(o=>o.id===p.object),f=spriteFrame(o,o.clips[0],d,0),r=groundRoot(p,o,128);return{x:r[0]-f.root[0],y:r[1]-f.root[1],width:f.frameSize[0],height:f.frameSize[1],rect:f.rect,url:new URL(f.image,location.href).href};});
 const bounds=[-origin[0]+c.pan[0],-origin[1]+c.pan[1],...size],plan=worldRasterPlan(sprites,bounds),raw=document.createElement('canvas');paintWorldRaster(raw,plan,await Promise.all(sprites.map(s=>image(s.url))));
 const ref={x:-origin[0]+c.rootOffset[0],y:-origin[1]+c.rootOffset[1],width:size[0],height:size[1],rect:[0,0,size[0]*2,size[1]*2],url:new URL('../../baseline/mixed-native/'+d+'.png',location.href).href};
 const control=document.createElement('canvas'),refPlan=worldRasterPlan([ref],bounds);paintWorldRaster(control,refPlan,[await image(ref.url)]);
 window.nativeCanvasPNGs.push({id:d+'-independent',png:raw.toDataURL()},{id:d+'-native-control',png:control.toDataURL()});
 for(const [bg,color]of [['light','#eeeeee'],['gray','#808080'],['dark','#151923']]){
  const sec=document.createElement('section');sec.id=d+'-'+bg;sec.style.width=size[0]*c.cssScale+'px';const label=document.createElement('p');label.textContent=d+' / '+bg;sec.append(label);
  const canvas=document.createElement('canvas');canvas.width=size[0]*2;canvas.height=size[1]*2;const ctx=canvas.getContext('2d');ctx.fillStyle=color;ctx.fillRect(0,0,canvas.width,canvas.height);ctx.imageSmoothingEnabled=false;ctx.drawImage(raw,(plan.x-bounds[0])*2,(plan.y-bounds[1])*2);canvas.style.width=size[0]*c.cssScale+'px';canvas.style.height=size[1]*c.cssScale+'px';sec.append(canvas);document.querySelector('#fixture').append(sec);
  window.evidence.fixtures.push({direction:d,background:bg,color,orderedPlacements:ordered,plan,bounds,referencePlan:refPlan,nativeSize:[raw.width,raw.height],controlSize:[control.width,control.height],displayCSS:[size[0]*c.cssScale,size[1]*c.cssScale]});
 }
}
window.ready=true;
