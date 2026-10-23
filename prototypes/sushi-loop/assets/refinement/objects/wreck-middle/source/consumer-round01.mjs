import {worldRasterPlan,paintWorldRaster} from './round01-resources/world-sprite-raster.js';
import {spriteFrame,groundRoot,orderPlacements} from './round01-resources/sprite-layout.js';
const object=await (await fetch('./round01-resources/catalog-object.json')).json();
const cases=[{id:'logical128-integer',cellCSS:128,cssScale:1,rootOffsetLogical:[0,0],panLogical:[0,0]},{id:'logical128-fractional',cellCSS:98.944,cssScale:.773,rootOffsetLogical:[.375,.625],panLogical:[.213,-.371]},{id:'phone32-integer',cellCSS:32,cssScale:.25,rootOffsetLogical:[0,0],panLogical:[0,0]},{id:'phone32-fractional',cellCSS:32,cssScale:.25,rootOffsetLogical:[.375,.625],panLogical:[.213,-.371]}];
const c=cases.find(c=>c.id===new URLSearchParams(location.search).get('case'))||cases[0];window.evidence={case:c,actualDPR:devicePixelRatio,fixtures:[]};window.nativeCanvasPNGs=[];
for(const d of ['N','E','S','W']) for(const [bg,color]of [['light','#eeeeee'],['gray','#808080'],['dark','#151923']]){
 const vertical=['E','W'].includes(d),size=vertical?[192,608]:[448,352],origin=vertical?[96,376]:[224,248];
 const clip=object.clips[0];clip.directions[d].image='../candidates/round-01/atlases/static-'+d+'.png';
 const placements=[-1,0,1].map((v,i)=>({id:d+i,object:object.id,direction:d,x:(vertical?0:v)-.5,y:(vertical?v:0)-.5,offset:c.rootOffsetLogical}));
 const ordered=orderPlacements(placements,[object]);
 const sprites=ordered.map(p=>{const f=spriteFrame(object,clip,d,0),r=groundRoot(p,object,128);return{x:r[0]-f.root[0],y:r[1]-f.root[1],width:f.frameSize[0],height:f.frameSize[1],rect:f.rect,url:new URL(f.image,location.href).href};});
 const bounds=[-origin[0]+c.panLogical[0],-origin[1]+c.panLogical[1],...size];const plan=worldRasterPlan(sprites,bounds);
 const imgs=await Promise.all(sprites.map(s=>new Promise((ok,no)=>{let im=new Image;im.onload=()=>ok(im);im.onerror=no;im.src=s.url;})));
 const raw=document.createElement('canvas');paintWorldRaster(raw,plan,imgs);
 // A transparent unchanged native-canvas dump is distinct from this displayed CSS composite.
 if(bg==='light'){
  window.nativeCanvasPNGs.push({id:d+'-independent',png:raw.toDataURL()});
  const reference={x:-origin[0]+c.rootOffsetLogical[0],y:-origin[1]+c.rootOffsetLogical[1],width:size[0],height:size[1],rect:[0,0,size[0]*2,size[1]*2],url:new URL('../candidates/round-01/connected-native/'+d+'.png',location.href).href};
  const refImage=await new Promise((ok,no)=>{const i=new Image;i.onload=()=>ok(i);i.onerror=no;i.src=reference.url;});const refPlan=worldRasterPlan([reference],bounds),control=document.createElement('canvas');paintWorldRaster(control,refPlan,[refImage]);window.nativeCanvasPNGs.push({id:d+'-connected-native-control',png:control.toDataURL()});
  const aa=raw.getContext('2d').getImageData(0,0,raw.width,raw.height).data,bb=control.getContext('2d').getImageData(0,0,control.width,control.height).data;let maxima=[0,0,0,0],count=0;for(let p=0;p<aa.length;p+=4){let changed=false;for(let k=0;k<4;k++){const dif=Math.abs(aa[p+k]-bb[p+k]);maxima[k]=Math.max(maxima[k],dif);changed ||=dif!==0;}count+=changed?1:0;}window.evidence.fixtures.push({direction:d,kind:'connected-native-control-comparison',nativeSize:[raw.width,raw.height],controlNativeSize:[control.width,control.height],rawRGBAMax:maxima,differentPixels:count,referencePlan:refPlan,interpretation:'Raw finite-light/precision/consumer differences retained; no numerical waiver for a visible join.'});
 }
 const section=document.createElement('section');section.id=d+'-'+bg;section.style.width=size[0]*c.cssScale+'px';const label=document.createElement('p');label.textContent=d+' / '+bg;section.append(label);const display=document.createElement('canvas');display.width=size[0]*2;display.height=size[1]*2;let ctx=display.getContext('2d');ctx.fillStyle=color;ctx.fillRect(0,0,display.width,display.height);ctx.imageSmoothingEnabled=false;ctx.drawImage(raw,(plan.x-bounds[0])*2,(plan.y-bounds[1])*2);display.style.width=size[0]*c.cssScale+'px';display.style.height=size[1]*c.cssScale+'px';section.append(display);document.querySelector('#fixture').append(section);
 window.evidence.fixtures.push({direction:d,background:bg,color,orderedPlacements:ordered,plan,bounds,displayNative:[display.width,display.height],displayCSS:[size[0]*c.cssScale,size[1]*c.cssScale],nativeCanvas:[raw.width,raw.height]});
}
window.ready=true;
