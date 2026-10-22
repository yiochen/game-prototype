import {worldRasterPlan,paintWorldRaster} from './resources/world-sprite-raster.js';
import {spriteFrame,groundRoot,orderPlacements} from './resources/sprite-layout.js';
const base='../candidates/round-01/';
const dirs=['N','E','S','W'];const opp={N:'S',S:'N',E:'W',W:'E'};const delta={S:[-128,0],N:[128,0],E:[0,128],W:[0,-128]};
const colors={light:'#eee8dc',gray:'#777777',dark:'#101820'};const phases=[[0,0],[.25,.25],[.5,.5],[.75,.75]];const pans=[[0,0],[.25,.5],[.5,.25],[.75,.75]];
const makeObj=(id)=>({id,kind:'terrain',footprint:[1,1],rootCell:[.5,.5],frameSize:[192,352],root:[96,248],sourceScale:2,layer:2,clips:[{id:'static',frames:1,fps:12,loop:false,directions:Object.fromEntries(dirs.map(d=>[d,{image:base+(id==='end'?`atlases/static-${d}.png`:`canonical-middle/published/${d}.png`),rects:[[0,0,384,704]],columns:1,rows:1,atlasSize:[384,704]}]))}]});
const objects=[makeObj('end'),makeObj('middle')];const images=new Map();
for(const obj of objects)for(const d of dirs){const url=obj.clips[0].directions[d].image;const im=new Image();im.src=url;await im.decode();images.set(url,im)}
function assembly(kind,d){const [dx,dy]=delta[d];if(kind==='single')return [{object:'end',direction:d,off:[0,0]}];if(kind==='pair')return [{object:'middle',direction:d,off:[dx,dy]},{object:'end',direction:d,off:[0,0]}];if(kind==='closedRun')return [{object:'end',direction:opp[d],off:[dx,dy]},{object:'middle',direction:d,off:[0,0]},{object:'end',direction:d,off:[-dx,-dy]}];return [...Array.from({length:13},(_,i)=>({object:'middle',direction:d,off:[dx*(i-6),dy*(i-6)]})),{object:'end',direction:opp[d],off:[dx*7,dy*7]},{object:'end',direction:d,off:[-dx*7,-dy*7]}]}
function raster(kind,d,phase=0,root=[224,376],bounds=[0,0,448,608]){
 const ps=assembly(kind,d).map(p=>({...p,x:(root[0]+p.off[0])/128-.5,y:(root[1]+p.off[1])/128-.5,offset:phases[phase]}));
 const sprites=orderPlacements(ps,objects).map(p=>{const o=objects.find(o=>o.id===p.object),f=spriteFrame(o,o.clips[0],p.direction,0),[x,y]=groundRoot(p,o,128);return {...f,x:x-f.root[0],y:y-f.root[1],width:f.frameSize[0],height:f.frameSize[1]}});
 const plan=worldRasterPlan(sprites,bounds),can=document.createElement('canvas');paintWorldRaster(can,plan,sprites.map(s=>images.get(s.image)));return {can,plan,sprites,placements:ps};
}
function add(kind,d,size,bg,phase,width=448,height=608,root=[224,376],pan=null){
 const {can,plan}=raster(kind,d,phase,root,[0,0,width,height]);const scale=size/128;const box=document.createElement('div');box.className='case';box.style.cssText=`width:${width*scale}px;height:${height*scale}px;background:${colors[bg]}`;const pp=pan||pans[phase];can.style.cssText=`left:${plan.x*scale+pp[0]}px;top:${plan.y*scale+pp[1]}px;width:${plan.width/plan.scale*scale}px;height:${plan.height/plan.scale*scale}px`;box.append(can);const label=document.createElement('span');label.className='label';label.textContent=`${d} ${bg} p${phase} · ${size}`;box.append(label);document.querySelector('#stage').append(box);return {kind,d,size,bg,phase,plan:{...plan,sprites:undefined}};
}
window.configure=async ({kind='pair',size=128,long=false,viewport=[360,780],root=null,phase=0,direction='S'}={})=>{
 const stage=document.querySelector('#stage');stage.replaceChildren();const manifest=[];
 if(long){stage.style.gridTemplateColumns='1fr';const [w,h]=viewport;manifest.push(add('longRun',direction,size,'light',phase,w*128/size,(h-110)*128/size,root||[w/2*128/size,(h/2)*128/size],pans[phase]));}
 else{stage.style.gridTemplateColumns=`repeat(4,${448*size/128}px)`;for(const d of dirs)for(const bg of Object.keys(colors))for(let p=0;p<4;p++)manifest.push(add(kind,d,size,bg,p));}
 document.querySelector('#summary').textContent=`${long?'13 canonical middles + 2 opposed ends':kind} · cell${size} · all four native facings / three backgrounds / four common phases · helper unchanged`;
 await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return manifest;
};
window.commonRaster=(kind,d)=>{const {can,plan}=raster(kind,d,0);const out=document.createElement('canvas');out.width=896;out.height=1216;out.getContext('2d').drawImage(can,-Math.round(-plan.x*plan.scale),-Math.round(-plan.y*plan.scale));return out.toDataURL('image/png')};
await window.configure({kind:'closedRun',size:32});window.ready=true;
