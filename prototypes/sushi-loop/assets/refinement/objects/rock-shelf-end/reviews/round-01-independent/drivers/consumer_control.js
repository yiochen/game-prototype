import {worldRasterPlan,paintWorldRaster} from '../resources/world-sprite-raster.js';
import {spriteFrame,groundRoot,orderPlacements} from '../resources/sprite-layout.js';
const facing=['N','E','S','W'], opposite={N:'S',S:'N',E:'W',W:'E'}, neighbor={N:[1,0],E:[0,1],S:[-1,0],W:[0,-1]};
const bases={light:'#eee8dc',gray:'#777777',dark:'#101820'}, phases=[[0,0],[.25,.25],[.5,.5],[.75,.75]],pans=[[0,0],[.25,.5],[.5,.25],[.75,.75]];
const url=(role,d)=>`../../candidates/round-01/${role==='end'?`frames/static/${d}/000.png`:`canonical-middle/published/${d}.png`}`;
const objects=['end','middle'].map(id=>({id,kind:'terrain',footprint:[1,1],frameSize:[192,352],root:[96,248],rootCell:[.5,.5],sourceScale:2,layer:2,clips:[{id:'static',frames:1,fps:12,loop:false,directions:Object.fromEntries(facing.map(d=>[d,{image:url(id,d),rects:[[0,0,384,704]],atlasSize:[384,704]}]))}]}));
const ims=new Map();for(const ob of objects)for(const d of facing){const path=url(ob.id,d),im=new Image();im.src=path;await im.decode();ims.set(path,im)}
function make(kind,d,phase){
 const n=neighbor[d];let items=kind==='pair'?[['middle',d,n],['end',d,[0,0]]]:[['end',opposite[d],n],['middle',d,[0,0]],['end',d,n.map(v=>-v)]];
 const placements=items.map(([object,direction,offset])=>({object,direction,x:(224+offset[0]*128)/128-.5,y:(376+offset[1]*128)/128-.5,offset:phases[phase]}));
 const sprites=orderPlacements(placements,objects).map(p=>{const ob=objects.find(o=>o.id===p.object),f=spriteFrame(ob,ob.clips[0],p.direction,0),g=groundRoot(p,ob,128);return{...f,x:g[0]-f.root[0],y:g[1]-f.root[1],width:f.frameSize[0],height:f.frameSize[1]}});
 const plan=worldRasterPlan(sprites,[0,0,448,608]),can=document.createElement('canvas');paintWorldRaster(can,plan,sprites.map(p=>ims.get(p.image)));return{can,plan,placements};
}
window.configure=async(size,kind='both')=>{
 const grid=document.querySelector('#grid');grid.replaceChildren();grid.style.gridTemplateColumns=size===128?'repeat(2,448px)':'repeat(4,112px)';const record=[];
 const add=(kind,d,bg,p)=>{const {can,plan,placements}=make(kind,d,p),scale=size/128,box=document.createElement('div');box.className='case';box.style.cssText=`width:${448*scale}px;height:${608*scale}px;background:${bases[bg]}`;can.style.cssText=`left:${plan.x*scale+pans[p][0]}px;top:${plan.y*scale+pans[p][1]}px;width:${plan.width/plan.scale*scale}px;height:${plan.height/plan.scale*scale}px`;box.append(can);const label=document.createElement('span');label.className='label';label.textContent=`${kind} ${d} ${bg} ${size} p${p}`;box.append(label);grid.append(box);record.push({kind,d,bg,p,placements,plan:{...plan,sprites:undefined}})};
 if(size===128)for(const d of facing)for(const k of ['pair','closedRun'])add(k,d,'gray',2);
 else for(const d of facing)for(const bg of Object.keys(bases))for(let p=0;p<4;p++)add(kind,d,bg,p);
 await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return record;
};
window.raw=(kind,d)=>{const{can,plan}=make(kind,d,0),c=document.createElement('canvas');c.width=896;c.height=1216;c.getContext('2d').drawImage(can,plan.x*2,plan.y*2);return c.toDataURL('image/png')};
window.ready=true;
