import {spriteFrame,clipFor,orderPlacements,groundRoot,sceneBounds,repeatedPlacements,footprintFor} from './resources/consumer/sprite-layout.js';
import {worldRasterPlan,paintWorldRaster} from './resources/consumer/world-sprite-raster.js';
const lib=await fetch('./resources/consumer/selected-library.json').then(r=>r.json());
const camera=await fetch('../../candidates/round-01/published-camera.json').then(r=>r.json());
const clips=['idle','travel','impact','protection','dock-charging','dock-ready','upgraded-idle','upgraded-travel','upgraded-impact','upgraded-protection','upgraded-dock-charging','upgraded-dock-ready'];
const main={id:'submarine-yellow',kind:'character',footprint:[1,2],rootCell:[.5,1],directionFootprints:{N:[1,2],S:[1,2],E:[2,1],W:[2,1]},directionRootCells:{N:[.5,1],S:[.5,1],E:[1,.5],W:[1,.5]},frameSize:[320,384],root:[160,288],sourceScale:2,clips:clips.map(id=>({id,frames:12,fps:12,loop:!id.endsWith('impact'),directions:Object.fromEntries(['N','E','S','W'].map(d=>[d,{image:'../../candidates/round-01/atlases/'+id+'-'+d+'.png',columns:6,rows:2,rects:Array.from({length:12},(_,i)=>[i%6*640,Math.floor(i/6)*768,640,768]),atlasSize:[3840,1536]}]))}))};
const objects=[...lib.objects,main],by=new Map(objects.map(o=>[o.id,o])),images=new Map();window.audit=[];
async function image(url){if(images.has(url))return images.get(url);const im=new Image();im.src=url;await im.decode();images.set(url,im);return im;}
function place(id,p,d,clip,phase=0,support=false){const o=by.get(id),rc=o.directionRootCells?.[d]||o.rootCell||footprintFor(o,d).map(x=>x/2);return {id:id==='dock-floor'?'deck':id,object:id,direction:d,clip,x:2+p[0]-rc[0],y:2-p[1]-rc[1],offset:[phase,phase-p[2]*89.6],...(support?{supportedBy:'deck'}:{})};}
async function draw(placements,seconds=0){
 const ordered=orderPlacements(placements,objects);const sprites=ordered.map(p=>{const o=by.get(p.object),f=spriteFrame(o,clipFor(o,p.clip),p.direction,seconds),g=groundRoot(p,o);return {url:f.image,rect:f.rect,x:g[0]-f.root[0],y:g[1]-f.root[1],width:f.frameSize[0],height:f.frameSize[1]};});
 const loaded=await Promise.all(sprites.map(s=>image(s.url))),bounds=sceneBounds(placements,objects,128,[4,4]),plan=worldRasterPlan(sprites,bounds),canvas=document.createElement('canvas');paintWorldRaster(canvas,plan,loaded);return {canvas,plan,ordered,sprites};
}
window.runMatrix=async({background='#aaa',display='logical',fraction=0,phone=false})=>{
 document.body.className=phone?'phone':'';document.body.style.background=background;document.querySelector('main').replaceChildren();const cases=[];
 for(const mode of ['dock-ready','upgraded-dock-ready','dock-charging','upgraded-dock-charging'])for(const d of ['N','E','S','W']){
  // Exact fixed world roots; environment sprites retain their own55degree
  // projection, main its65degree registration. Height uses actual consumer89.6.
  const ps=[place('dock-floor',[0,0,0],d,'static',fraction),place('dock-entry',[0,-1.5,0],d,'static',fraction),place('workshop-hut',[.78,.35,.23],d,'static',fraction,true),place('submarine-yellow',[-.70,-.42,.23],d,mode,fraction,true)];
  const {canvas,plan,ordered,sprites}=await draw(ps,3/12);canvas.style.width=(plan.width/(display==='native'?1:plan.scale))+'px';canvas.style.height=(plan.height/(display==='native'?1:plan.scale))+'px';const article=document.createElement('article');const label=document.createElement('p');label.textContent=mode+' '+d+' '+display+' offset '+fraction;article.append(label,canvas);document.querySelector('main').append(article);
  const bytes=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(v=>v.toString(16).padStart(2,'0')).join('');cases.push({mode,direction:d,background,display,fraction,worldRoots:{main:[-.70,-.42,.23],floor:[0,0,0],entry:[0,-1.5,0],hut:[.78,.35,.23]},heightProjector89_6:true,ordinaryWholeCanvasSampling:getComputedStyle(canvas).imageRendering,plan:{x:plan.x,y:plan.y,width:plan.width,height:plan.height,scale:plan.scale},order:ordered.map(p=>p.object),sourceRects:sprites.map(s=>s.rect),nativeCanvasRGBAHash:hash});
 }
 document.querySelector('#note').textContent='Main65°/environment55° own registered sprites; fixedroots; native meshes prove physical hover separately. Cover unapproved and absent. Actual frozen renderer and registered support ordering; no pixel fit or corrections.';window.audit.push(...cases);return cases;
};
window.runComparisons=async()=>{
 document.body.className='';document.body.style.background='#b8c0c7';document.querySelector('main').replaceChildren();const results=[];
 for(const d of ['N','E','S','W']){
  const ids=['submarine-yellow','customer-rosa','sub-hull-panels','sub-harpoon-mount','sub-collector-inlet'];const ps=ids.map((id,k)=>place(id,[k*1.8,0,0],d,id==='submarine-yellow'?'upgraded-dock-ready':id==='customer-rosa'?'stand':'idle',.25));const {canvas,plan}=await draw(ps,0);canvas.style.width=plan.width/plan.scale+'px';canvas.style.height=plan.height/plan.scale+'px';const a=document.createElement('article');a.append(canvas);document.querySelector('main').append(a);results.push({direction:d,plan:{width:plan.width,height:plan.height,scale:plan.scale},registeredComparison:'Own registered standalone equipment images versus main exact mounted neutral geometry; no crossprojection raster identity implied.'});
 }
 document.querySelector('main').style.gridTemplateColumns='1fr';return results;
};
window.runRepeated=async()=>{document.querySelector('main').replaceChildren();document.querySelector('main').style.gridTemplateColumns='1fr';const {canvas,plan}=await draw(repeatedPlacements(main,'S','upgraded-idle'),0);canvas.style.width=plan.width/plan.scale+'px';canvas.style.height=plan.height/plan.scale+'px';document.querySelector('main').append(canvas);return {width:plan.width,height:plan.height,scale:plan.scale};};
window.runPlaybacks=async()=>{
 document.body.style.background='#aaa';document.querySelector('main').replaceChildren();document.querySelector('main').style.gridTemplateColumns='repeat(4,320px)';const hosts=[];
 for(const clip of clips)for(const direction of ['N','E','S','W']){const o=main,f=spriteFrame(o,clipFor(o,clip),direction,0),im=await image(f.image),canvas=document.createElement('canvas'),plan=worldRasterPlan([{url:f.image,rect:f.rect,x:0,y:0,width:320,height:384}],[0,0,320,384]),article=document.createElement('article'),p=document.createElement('p');canvas.style.width='320px';canvas.style.height='384px';p.textContent=clip+' '+direction;article.append(p,canvas);document.querySelector('main').append(article);hosts.push({clip,direction,canvas,plan,im,seen:new Set()});}
 const start=performance.now();window.animationFrames=[];await new Promise(resolve=>{function tick(now){const sec=(now-start)/1000;for(const h of hosts){const f=spriteFrame(main,clipFor(main,h.clip),h.direction,sec);h.plan.sprites[0].rect=f.rect;paintWorldRaster(h.canvas,h.plan,[h.im]);h.seen.add(f.frame);}window.animationFrames.push({elapsed:sec,frames:hosts.map(h=>spriteFrame(main,clipFor(main,h.clip),h.direction,sec).frame)});if(sec<2.1)requestAnimationFrame(tick);else resolve();}requestAnimationFrame(tick)});return hosts.map(h=>({clip:h.clip,direction:h.direction,seen:[...h.seen].sort((a,b)=>a-b),fps:12,loop:clipFor(main,h.clip).loop,lastFrame:spriteFrame(main,clipFor(main,h.clip),h.direction,2.1).frame}));
};
window.ready=true;
window.runOnePlayback=async(clip,direction)=>{
 document.body.className='';document.querySelector('main').replaceChildren();document.querySelector('main').style.gridTemplateColumns='320px';const f=spriteFrame(main,clipFor(main,clip),direction,0),im=await image(f.image),canvas=document.createElement('canvas'),plan=worldRasterPlan([{url:f.image,rect:f.rect,x:0,y:0,width:320,height:384}],[0,0,320,384]);canvas.style.width='320px';canvas.style.height='384px';document.querySelector('main').append(canvas);let last=-1;const seen=new Set(),trace=[];const start=performance.now();
 await new Promise(resolve=>{function tick(now){const seconds=(now-start)/1000,frame=spriteFrame(main,clipFor(main,clip),direction,seconds);if(frame.frame!==last){plan.sprites[0].rect=frame.rect;paintWorldRaster(canvas,plan,[im]);trace.push({seconds,frame:frame.frame});seen.add(frame.frame);last=frame.frame;}if(seconds<1.11)requestAnimationFrame(tick);else resolve();}requestAnimationFrame(tick)});
 return {clip,direction,seen:[...seen].sort((a,b)=>a-b),trace,fps:12,loop:!clip.endsWith('impact'),terminalRuntimeFrame:11,closure13OutsideAtlas:true};
};
