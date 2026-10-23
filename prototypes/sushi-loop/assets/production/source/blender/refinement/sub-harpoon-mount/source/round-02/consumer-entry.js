import {clipFor,spriteFrame,groundRoot,orderPlacements,sceneBounds} from './resources/browser/sprite-layout.js';
import {worldRasterPlan,paintWorldRaster} from './resources/browser/world-sprite-raster.js';
const base='./source/round-02/';
const own=await(await fetch('./inputs/catalog-object.json')).json();
const selected=await(await fetch(base+'resources/browser/selected-objects.json')).json();
const main=selected.find(o=>o.id==='submarine-yellow'),eel=selected.find(o=>o.id==='creature-eel');
const qs=new URLSearchParams(location.search),direction=qs.get('d')||'S',phase=Number(qs.get('f')||0),tone=qs.get('bg')||'gray',fraction=Number(qs.get('fraction')||.37),landscape=innerWidth>=768;
const backgrounds={light:'#f5f0e6',gray:'#9ca7ac',dark:'#1c2732'},bg=backgrounds[tone];
for(const c of own.clips)for(const d of Object.keys(c.directions))c.directions[d].image=`./candidates/round-02/atlases/${c.id}-${d}.png`;
const upgrade=clipFor(main,'upgraded-dock-ready');
main.clips=[{...upgrade,frames:1,fps:12,loop:false,static:true,frameOrder:[0],directions:Object.fromEntries(['N','E','S','W'].map(d=>[d,{image:`./candidates/round-02/assembled/upgraded-dock-ready-${d}.png`,columns:1,rows:1,atlasSize:[640,768],rects:[[0,0,640,768]]}]))}];
for(const c of eel.clips)for(const d of Object.keys(c.directions))c.directions[d].image=base+'resources/browser/'+c.directions[d].image;
const objects=[own,main,eel],clip=phase===0?'idle':'active',seconds=phase===0?0:(phase-1+.25)/12;
document.body.style.background=bg;document.body.style.color=tone==='dark'?'#f3eee5':'#243645';
const header=document.createElement('header');header.textContent=`${direction} · ${phase===0?'IDLE neutral':`ACTIVE ${phase}/12`} · native candidate on static preliminary main; other gear PROVISIONAL`;document.body.append(header);
const cases=[];
async function scene(label,placements,pitch,boundsOverride){
 const title=document.createElement('p');title.textContent=label;document.body.append(title);
 const natural=sceneBounds(placements,objects,128,[7,4]);
 const bounds=boundsOverride||natural;bounds[0]+=fraction;bounds[1]+=fraction*.71;
 const sprites=orderPlacements(placements,objects).map(p=>{const o=objects.find(o=>o.id===p.object),fr=spriteFrame(o,clipFor(o,p.clip),direction,o===own?seconds:0),[x,y]=groundRoot(p,o,128);return{url:fr.image,rect:fr.rect,x:x-fr.root[0],y:y-fr.root[1],width:fr.frameSize[0],height:fr.frameSize[1],object:o.id,frame:fr.frame,root:[x,y]};});
 const plan=worldRasterPlan(sprites,bounds),images=await Promise.all(sprites.map(s=>new Promise((ok,no)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=()=>no(Error(s.url));im.src=s.url;})));
 const canvas=document.createElement('canvas');paintWorldRaster(canvas,plan,images);canvas.style.cssText='display:block;width:100%;height:100%';
 const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox',bounds.join(' '));svg.style.width=`${bounds[2]*pitch/128}px`;svg.style.height=`${bounds[3]*pitch/128}px`;svg.style.display='block';svg.style.maxWidth='none';
 const foreign=document.createElementNS(svg.namespaceURI,'foreignObject');for(const[k,v]of Object.entries({x:plan.x,y:plan.y,width:plan.width/plan.scale,height:plan.height/plan.scale}))foreign.setAttribute(k,String(v));foreign.append(canvas);svg.append(foreign);document.body.append(svg);
 cases.push({label,pitch,bounds,plan:{...plan},samplerAfterResize:canvas.getContext('2d').imageSmoothingEnabled,canvasSize:[canvas.width,canvas.height],cssSize:[bounds[2]*pitch/128,bounds[3]*pitch/128],finalFilter:'ordinary browser whole canvas filter; no image-rendering override'});
}
const shared=[{object:own.id,x:0,y:1,direction,clip,offset:[fraction,fraction]},{object:main.id,x:2,y:1,direction,clip:'upgraded-dock-ready',offset:[fraction,fraction]},{object:eel.id,x:5,y:1,direction,clip:'swim',offset:[fraction,fraction]}];
if(landscape){await scene('128px cells · independent launcher / actual native assembled upgraded Sub / eel',shared,128);}
else{await scene('128px cell · complete registered launcher frame',[shared[0]],128,[-32,-56,192,352]);}
const row=document.createElement('div');row.id='small-scenes';document.body.append(row);
await scene('47.3px cells · independent launcher / assembled upgraded Sub / eel',shared,47.3);
await scene('32px cells · same shared world scale and fractional registration',shared,32);
window.consumerEvidence={ready:true,direction,phase,clip,seconds,tone,fraction,viewport:[innerWidth,innerHeight],actualMainClip:'upgraded-dock-ready',actualMainCapture:'Native assembled canonical-neutral own resources at frozen mount on static preliminary frozen body; other gear PROVISIONAL',cases,source:'Exact copied real sprite-layout.js and world-sprite-raster.js. Nearest sampling reasserted by paintWorldRaster after resize, then browser final wholecanvas filtering. No own sprite overlay attachment.'};
document.body.dataset.ready='true';
