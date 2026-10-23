import{worldRasterPlan,paintWorldRaster}from'./world-sprite-raster.js';
import{spriteFrame,clipFor,attachmentMarkers}from'./sprite-layout.js';
const C=await(await fetch('../consumer-catalog.json')).json();
const directions=['N','E','S','W'],colors={light:'#f3f1e8',gray:'#858c92',dark:'#152338'},ns='http://www.w3.org/2000/svg';
const stage=document.querySelector('#stage'),heading=document.querySelector('#heading');
let images=new Map(),cards=[],running=false,trace=[],start=0;
async function load(c){for(const d of directions){const url=c.directions[d].image;if(!images.has(url)){const im=new Image();im.src='../'+url;await im.decode();images.set(url,im);}}}
function node(tag,attrs={}){const el=document.createElementNS(ns,tag);for(const[k,v]of Object.entries(attrs))el.setAttribute(k,v);return el;}
function card(clip,d,t,zoom,bg,sockets){
 const div=document.createElement('div');div.className='card';div.style.background=colors[bg];div.style.width=`${448*zoom}px`;div.style.height=`${512*zoom}px`;
 const label=document.createElement('div');label.className='label';div.append(label);
 const svg=node('svg',{viewBox:'-224 -352 448 512',width:448*zoom,height:512*zoom});div.append(svg);
 const foreign=node('foreignObject'),canvas=document.createElement('canvas');foreign.append(canvas);svg.append(foreign);
 if(sockets){svg.append(node('circle',{cx:0,cy:0,r:4,fill:'none',stroke:'#ff8844','stroke-width':1}));for(const m of attachmentMarkers(C,clip,d)){const[x,y]=m.position;svg.append(node('circle',{cx:x,cy:y,r:m.name==='nose'?4:6,fill:'none',stroke:m.name==='nose'?'#ffcc55':'#ff55cc','stroke-width':1}));const text=node('text',{x:x+7,y:y-6,fill:'#ef44b8','font-size':10});text.textContent=m.name;svg.append(text);}}
 function paint(seconds){const f=spriteFrame(C,clip,d,seconds),p=worldRasterPlan([{rect:f.rect,x:-f.root[0],y:-f.root[1],width:f.frameSize[0],height:f.frameSize[1]}],[-224,-352,448,512]);foreign.setAttribute('x',p.x);foreign.setAttribute('y',p.y);foreign.setAttribute('width',p.width/p.scale);foreign.setAttribute('height',p.height/p.scale);paintWorldRaster(canvas,p,[images.get(f.image)]);label.textContent=`${clip.id} ${d} f${f.frame}`;div.dataset.frame=f.frame;return f.frame;}
 paint(t);stage.append(div);return{paint,div,d};
}
window.show=async({clipId='normal',mode='logical',bg='gray',zoom=1,seconds=0,sockets=false,framesByFacing=null}={})=>{
 running=false;cards=[];stage.replaceChildren();const c=clipFor(C,clipId);await load(c);heading.textContent=`Native fish BODY · ${c.id} · ${mode} · ${bg} · zoom ${zoom}`;
 stage.style.gridTemplateColumns=`repeat(${mode==='sheet'?12:mode==='phone'?2:4},${448*zoom}px)`;
 for(const d of directions){if(mode==='sheet'){for(let i=0;i<12;i++)cards.push(card(c,d,i/12,zoom,bg,sockets));}else cards.push(card(c,d,framesByFacing?framesByFacing[d]/12:seconds,zoom,bg,sockets));}
 return{clip:c.id,mode,bg,zoom,count:cards.length,frame:[448,512],root:[224,352],sourceScale:C.sourceScale,rects:c.directions.S.rects,frameOrder:c.frameOrder,frames:c.frames,fps:c.fps,loop:c.loop,framesByFacing,helperSemantics:'Native nearest after common canvas assembly, then ordinary whole CSS filtering; exact current helpers.'};
};
window.play=async({clipId,mode='phone',bg='gray'}={})=>{await window.show({clipId,mode,bg,zoom:mode==='phone'?.4:1});trace=[];start=performance.now();running=true;function tick(now){if(!running)return;const seconds=(now-start)/1000;const frames=cards.map(c=>c.paint(seconds));trace.push({rafTimestamp:now,elapsed:seconds,frames});requestAnimationFrame(tick);}requestAnimationFrame(tick);return{performanceStart:start,epochStart:performance.timeOrigin+start};};
window.stop=()=>{running=false;return{trace,end:performance.now(),phaseOrder:directions};};window.fixtureReady=true;
