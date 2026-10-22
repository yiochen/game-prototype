import {spriteFrame,clipFor,orderPlacements,groundRoot} from './resources/sprite-layout.js';
import {worldRasterPlan,paintWorldRaster} from './resources/world-sprite-raster.js';
const names=['dock-floor','dock-entry','workshop-hut','dock-cover','submarine-yellow'];
const objects=await Promise.all(names.map(n=>fetch('./resources/catalog-'+n+'.json').then(r=>r.json())));
const by=new Map(objects.map(o=>[o.id,o]));
const angles={S:0,E:Math.PI/2,N:Math.PI,W:-Math.PI/2};
const specs=[['dock-floor',[0,0,0]],['dock-entry',[0,-1.5,0]],['workshop-hut',[.78,.35,.23]],['submarine-yellow',[-.7,-.42,.23]],['dock-cover',[0,0,.23]]];
const images=new Map();
window.audit=[];
async function run(direction,supported,cover,phase=0){
 const a=angles[direction],c=Math.cos(a),s=Math.sin(a);
 let placements=specs.filter(([id])=>cover||id!=='dock-cover').map(([object,p])=>{
  const x=p[0]*c-p[1]*s,y=p[0]*s+p[1]*c,o=by.get(object),rc=o.directionRootCells?.[direction]||o.rootCell||o.footprint.map(v=>v/2);
  return {id:object==='dock-floor'?'deck':object,object,direction,x:2+x-rc[0],y:2-y-rc[1],offset:[phase,-p[2]*89.6+phase],clip:object==='submarine-yellow'?'dock-ready':o.clips[0].id,...(supported&&['workshop-hut','submarine-yellow'].includes(object)?{supportedBy:'deck'}:{})};
 });
 const order=orderPlacements(placements,objects),sprites=order.map(p=>{
  const o=by.get(p.object),f=spriteFrame(o,clipFor(o,p.clip),direction,0),[x,y]=groundRoot(p,o),url=p.object==='submarine-yellow'?'./resources/published-atlases/'+f.image.split('/').pop():'./resources/context-atlases/'+p.object+'/'+f.image.split('/').pop();
  return {url,rect:f.rect,x:x-f.root[0],y:y-f.root[1],width:f.frameSize[0],height:f.frameSize[1]};
 });
 const loaded=await Promise.all(sprites.map(async p=>{if(images.has(p.url))return images.get(p.url);const im=new Image();im.src=p.url;await im.decode();images.set(p.url,im);return im}));
 const plan=worldRasterPlan(sprites,[0,-128,512,640]);const canvas=document.createElement('canvas');paintWorldRaster(canvas,plan,loaded);canvas.style.width='100%';canvas.style.height='auto';
 const host=document.createElement('article');const h=document.createElement('p');h.textContent=direction+(supported?' explicit support':' source ordinary order')+(cover?' + old cover':'');host.append(h,canvas);document.querySelector('main').append(host);
 const context=canvas.getContext('2d');const before=context.imageSmoothingEnabled;canvas.width=canvas.width+1;paintWorldRaster(canvas,plan,loaded);
 window.audit.push({direction,supported,cover,phase,order:order.map(p=>p.object),plan:{x:plan.x,y:plan.y,width:plan.width,height:plan.height,scale:plan.scale},smoothingBeforeResize:before,smoothingAfterResize:canvas.getContext('2d').imageSmoothingEnabled});
}
for(const d of ['N','E','S','W'])await run(d,false,false);
for(const d of ['N','E','S','W'])await run(d,true,false,.25);
for(const d of ['N','E','S','W'])await run(d,true,true,.5);
window.ready=true;
