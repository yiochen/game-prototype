import {worldRasterPlan,paintWorldRaster} from './world-sprite-raster.js';
import {spriteFrame,groundRoot,orderPlacements} from './sprite-layout.js';
const asset=await fetch('../inputs/catalog-object.json').then(r=>r.json());
const params=new URLSearchParams(location.search);const scale=Number(params.get('scale')||.5), bg=params.get('bg')||'#777777';
const mode=params.get('mode')||'sheet',source=params.get('source')||'replay-atlases';
const directions=['N','E','S','W'];const images={};
for(const d of directions){const im=new Image();im.src=`./${source}/${d}.png`;await im.decode();images[d]=im;}
document.body.style.cssText=`margin:0;background:${bg};color:${bg==='#132033'?'white':'black'};font:12px sans-serif;`;
const grid=document.createElement('main');grid.style.cssText=`display:grid;grid-template-columns:repeat(4,${192*scale}px);width:${768*scale}px;`;document.body.append(grid);
const records=[];const cells=[];
const rows=mode==='all'?Array.from({length:12},(_,i)=>i):mode==='play'?[0]:[0,5,11];
for(const frameIndex of rows)for(const direction of directions){
 const cell=document.createElement('section');const label=document.createElement('div');label.style.height='20px';const viewport=document.createElement('div');viewport.style.cssText=`position:relative;overflow:hidden;width:${192*scale}px;height:${384*scale}px;`;const canvas=document.createElement('canvas');viewport.append(canvas);cell.append(label,viewport);grid.append(cell);cells.push({direction,frameIndex,label,canvas});
}
window.evidence={assetId:asset.id,scale,bg,mode,source,helper:'worldRasterPlan + paintWorldRaster + spriteFrame + groundRoot + orderPlacements',frameRecords:records};
function render(seconds){
 for(const cell of cells){
  const t=mode==='play'?seconds:cell.frameIndex/12;const clip=asset.clips[0];const frame=spriteFrame(asset,clip,cell.direction,t);const placement={object:asset.id,x:-.5,y:-.5,direction:cell.direction,clip:'enter'};
  const [gx,gy]=groundRoot(placement,asset);const sprites=orderPlacements([placement],[asset]).map(()=>({x:gx-frame.root[0],y:gy-frame.root[1],width:frame.frameSize[0],height:frame.frameSize[1],rect:frame.rect,url:images[cell.direction].src}));
  const bounds=[-96,-288,192,384],plan=worldRasterPlan(sprites,bounds);paintWorldRaster(cell.canvas,plan,[images[cell.direction]]);
  cell.canvas.style.cssText=`position:absolute;left:${(plan.x-bounds[0])*scale}px;top:${(plan.y-bounds[1])*scale}px;width:${plan.width/plan.scale*scale}px;height:${plan.height/plan.scale*scale}px;`;
  cell.label.textContent=`${cell.direction} enter ${frame.frame}`;cell.current=frame.frame;
  if(mode!=='play'||!records.some(r=>r.direction===cell.direction&&r.frame===frame.frame))records.push({direction:cell.direction,frame:frame.frame,seconds:t,rect:frame.rect,root:frame.root,groundRoot:[gx,gy],plan:{x:plan.x,y:plan.y,width:plan.width,height:plan.height,scale:plan.scale},actualWallTime:performance.now()});
 }
 window.evidence.currentFrames=cells.map(c=>({direction:c.direction,frame:c.current}));
}
render(0);window.ready=true;
window.startPlayback=()=>{const start=performance.now();function tick(now){render((now-start)/1000);window.evidence.elapsed=(now-start)/1000;if(now-start<2000)requestAnimationFrame(tick);else window.evidence.complete=true;}requestAnimationFrame(tick);};
