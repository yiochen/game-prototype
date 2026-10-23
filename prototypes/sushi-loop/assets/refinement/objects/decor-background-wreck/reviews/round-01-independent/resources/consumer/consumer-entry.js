import {worldRasterPlan,paintWorldRaster} from './world-sprite-raster.js';
import {spriteFrame,clipFor,sceneBounds,orderPlacements,groundRoot,directionPlacements,repeatedPlacements} from './sprite-layout.js';
window.drawSourceStudy=async function({kind,cell=128,background='#eef2ed',phase=[0,0],seconds=0,pan=[0,0]}){
 const fixture=await(await fetch('/resources/consumer/fixture.json')).json(),objects=fixture.objects,own=objects[0];
 let placements,grid;
 if(kind==='facings'){placements=directionPlacements(own,'static');grid=[8,1];}
 else if(kind==='repeat'){placements=repeatedPlacements(own,'S','static');grid=[3,3];}
 else{placements=own.interactions[0].placements;grid=own.interactions[0].gridSize;}
 placements=placements.map(p=>({...p,offset:phase}));const bounds=sceneBounds(placements,objects,128,grid);bounds[0]+=pan[0];bounds[1]+=pan[1];
 const sprites=orderPlacements(placements,objects).map(p=>{const o=objects.find(x=>x.id===p.object),f=spriteFrame(o,clipFor(o,p.clip),p.direction||'S',seconds),[x,y]=groundRoot(p,o,128);return{url:'/resources/consumer/'+f.image,rect:f.rect,x:x-f.root[0],y:y-f.root[1],width:f.frameSize[0],height:f.frameSize[1],object:o.id,frame:f.frame};});
 const plan=worldRasterPlan(sprites,bounds),imgs=await Promise.all(sprites.map(s=>new Promise((resolve,reject)=>{const i=new Image();i.onload=()=>resolve(i);i.onerror=reject;i.src=s.url;})));
 const ns='http://www.w3.org/2000/svg';document.body.replaceChildren();document.body.style.cssText=`margin:0;background:${background}`;const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox',bounds.join(' '));svg.style.cssText=`display:block;width:${bounds[2]*cell/128}px;height:${bounds[3]*cell/128}px;background:${background}`;document.body.append(svg);
 if(kind!=='facings'){
  const floor=objects.find(o=>o.id==='floor-underwater'),frame=spriteFrame(floor,floor.clips[0],'S',0),image=new Image();await new Promise((resolve,reject)=>{image.onload=resolve;image.onerror=reject;image.src='/resources/consumer/'+frame.image;});
  // The actual SpriteScene floor is a repeated SVG image pattern beneath the native world canvas.
  const defs=document.createElementNS(ns,'defs'),pat=document.createElementNS(ns,'pattern');pat.id='floor';pat.setAttribute('width',128);pat.setAttribute('height',128);pat.setAttribute('patternUnits','userSpaceOnUse');const tile=document.createElementNS(ns,'svg');tile.setAttribute('width',128);tile.setAttribute('height',128);tile.setAttribute('viewBox',frame.rect.join(' '));tile.setAttribute('overflow','hidden');const im=document.createElementNS(ns,'image');im.setAttribute('href',image.src);im.setAttribute('width',frame.atlasSize[0]);im.setAttribute('height',frame.atlasSize[1]);tile.append(im);pat.append(tile);defs.append(pat);svg.append(defs);const rect=document.createElementNS(ns,'rect');rect.setAttribute('width',grid[0]*128);rect.setAttribute('height',grid[1]*128);rect.setAttribute('fill','url(#floor)');svg.append(rect);
 }
 const fo=document.createElementNS(ns,'foreignObject');fo.setAttribute('x',plan.x);fo.setAttribute('y',plan.y);fo.setAttribute('width',plan.width/plan.scale);fo.setAttribute('height',plan.height/plan.scale);svg.append(fo);const canvas=document.createElement('canvas');canvas.style.cssText='display:block;width:100%;height:100%';fo.append(canvas);paintWorldRaster(canvas,plan,imgs);
 const rgba=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;const digest=await crypto.subtle.digest('SHA-256',rgba);return{kind,cell,background,phase,seconds,pan,bounds,plan:{...plan,sprites:plan.sprites},cssSize:[bounds[2]*cell/128,bounds[3]*cell/128],canvasSize:[canvas.width,canvas.height],smoothingAfterResize:canvas.getContext('2d').imageSmoothingEnabled,nativeCanvasRGBA256:[...new Uint8Array(digest)].map(v=>v.toString(16).padStart(2,'0')).join(''),frames:sprites.map(s=>({object:s.object,index:s.frame})),userAgent:navigator.userAgent,dpr:devicePixelRatio};
};
