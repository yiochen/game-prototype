import {worldRasterPlan,paintWorldRaster} from './world-sprite-raster.js';
import {spriteFrame,clipFor,attachmentMarkers} from './sprite-layout.js';
const C=await (await fetch('catalog-object.json')).json();
const dirs=['N','E','S','W'], colors={light:'#f3f1e8',gray:'#858c92',dark:'#152338'};
const ns='http://www.w3.org/2000/svg',stage=document.querySelector('#stage'),heading=document.querySelector('#heading');
let images=new Map(), cards=[],running=false,trace=[],runStart=0;
async function load(clip){for(const d of dirs){const e=clip.directions[d];if(!images.has(e.image)){const im=new Image();im.src=e.image;await im.decode();images.set(e.image,im);}}}
function node(tag,attrs={}){const n=document.createElementNS(ns,tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);return n;}
function card(clip,d,seconds,zoom,bg,sockets=false){
 const div=document.createElement('div');div.className='card';div.style.background=colors[bg];div.style.width=`${448*zoom}px`;div.style.height=`${512*zoom}px`;
 const label=document.createElement('div');label.className='label';div.append(label);
 const svg=node('svg',{viewBox:'-224 -352 448 512',width:448*zoom,height:512*zoom});div.append(svg);
 const foreign=node('foreignObject'),canvas=document.createElement('canvas');foreign.append(canvas);svg.append(foreign);
 if(sockets)for(const mark of attachmentMarkers(C,clip,d)){const [x,y]=mark.position;svg.append(node('circle',{cx:x,cy:y,r:4,fill:'none',stroke:mark.name==='nose'?'#ffcc55':'#ff55cc','stroke-width':1}));const t=node('text',{x:x+6,y:y-5,fill:'#ff55cc','font-size':10});t.textContent=mark.name;svg.append(t);}
 function paint(t){const f=spriteFrame(C,clip,d,t);const p=worldRasterPlan([{rect:f.rect,x:-f.root[0],y:-f.root[1],width:f.frameSize[0],height:f.frameSize[1]}],[-224,-352,448,512]);foreign.setAttribute('x',p.x);foreign.setAttribute('y',p.y);foreign.setAttribute('width',p.width/p.scale);foreign.setAttribute('height',p.height/p.scale);paintWorldRaster(canvas,p,[images.get(f.image)]);label.textContent=`${clip.id} ${d} f${f.frame}`;div.dataset.frame=f.frame;return f.frame;}
 paint(seconds);stage.append(div);return {paint,div,d,clip};
}
window.show=async({clipId='normal',mode='sheet',bg='gray',zoom=.4,seconds=0,sockets=false}={})=>{
 running=false;cards=[];stage.replaceChildren();const clip=clipFor(C,clipId);await load(clip);heading.textContent=`creature-fish · ${clip.id} · ${mode} · full registered frame · zoom ${zoom} · ${bg}`;
 if(mode==='sheet'){stage.style.gridTemplateColumns=`repeat(12, ${448*zoom}px)`;for(const d of dirs)for(let i=0;i<12;i++)cards.push(card(clip,d,i/12,zoom,bg,sockets));}
 else {stage.style.gridTemplateColumns=`repeat(${mode==='phone'?2:4}, ${448*zoom}px)`;for(const d of dirs)cards.push(card(clip,d,seconds,zoom,bg,sockets));}
 return{count:cards.length,clip:clip.id,zoom,frame:[448,512],root:[224,352],sourceScale:C.sourceScale,rects:clip.directions.S.rects,frames:clip.frames,fps:clip.fps,loop:clip.loop};
};
window.play=async(clipId,bg='gray')=>{await window.show({clipId,mode:'phone',bg,zoom:.4});trace=[];runStart=performance.now();running=true;function tick(now){if(!running)return;const seconds=(now-runStart)/1000;const frames=cards.map(c=>c.paint(seconds));const entry={elapsed:seconds,frames};if(!trace.length||JSON.stringify(trace.at(-1).frames)!==JSON.stringify(frames))trace.push(entry);requestAnimationFrame(tick);}requestAnimationFrame(tick);};
window.stop=()=>{running=false;return trace;};window.fixtureReady=true;
