import React,{useState,useEffect} from 'react';
import {createRoot} from 'react-dom/client';
import {libraryObjects} from '../../../../../wireframe/object-review-data.js';
import {spriteFrame,groundRoot,orderPlacements,directionPlacements,repeatedPlacements} from '../../../../../wireframe/sprite-layout.js';
const q=new URLSearchParams(location.search),direction=q.get('direction')||'S',mode=q.get('mode')||'independent',study=q.get('study')||'assembly';
const pitch=Number(q.get('pitch')||128),phaseX=Number(q.get('phaseX')||.25),phaseY=Number(q.get('phaseY')||.5),background=q.get('background')||'#808080',initial=Number(q.get('frame')||0),live=q.has('live');
const base=libraryObjects.find(o=>o.id==='belt-corner-n-e'),family=libraryObjects.find(o=>o.id==='belt-straight-n');
const native=structuredClone(base);native.id='bench-native-corner-assembly';native.name='Native connected/unbroken reference';native.frameSize=[448,608];native.root=[224,376];native.sourceScale=2;native.rootCell=[.5,.5];
for(const entry of Object.values(native.clips[0].directions)){entry.atlasSize=[5376,4864];entry.rects=Array.from({length:24},(_,i)=>[i%6*896,Math.floor(i/6)*1216,896,1216]);entry.columns=6;entry.rows=4;entry.frameSize=[448,608];entry.root=[224,376];entry.sourceScale=2;}
libraryObjects.push(native);
const {SpriteScene}=await import('../../../../../wireframe/object-review.jsx');
const rot={N:Math.PI,E:Math.PI/2,S:0,W:-Math.PI/2},r=rot[direction];
const rotate=(x,y)=>[x*Math.cos(r)+y*Math.sin(r),-x*Math.sin(r)+y*Math.cos(r)];
const facing=a=>Object.keys(rot).sort((x,y)=>Math.abs(Math.atan2(Math.sin(rot[x]-a),Math.cos(rot[x]-a)))-Math.abs(Math.atan2(Math.sin(rot[y]-a),Math.cos(rot[y]-a))))[0];
let placements=mode==='independent'?[{object:base.id,x:1,y:1,direction},...[{x:0,y:-1,a:Math.PI},{x:1,y:0,a:-Math.PI/2}].map(({x,y,a})=>{const [dx,dy]=rotate(x,y);return {object:family.id,x:1+Math.round(dx),y:1+Math.round(dy),direction:facing(r+a)}})]:[{object:native.id,x:1,y:1,direction}];
let bounds=[-32-phaseX*128/pitch,-184-phaseY*128/pitch,448,608];
if(study==='facings'){placements=directionPlacements(base,'running');bounds=[-32,-184,960,448];}
if(study==='repeated'){placements=repeatedPlacements(base,direction,'running');bounds=[-32,-184,448,608];}
if(study==='plate'){
 const original=base.interactions.find(i=>i.name.startsWith('Staged')).placements.find(p=>p.object==='dish-salmon');
 const path=original.motion.path.slice(1,-1).map(([x,y])=>[x-1,y-1]).map(([x,y])=>{const [dx,dy]=rotate(x-1,y-1);return [1+dx,1+dy]});
 placements.push({...structuredClone(original),x:path[0][0],y:path[0][1],motion:{path,duration:4,loop:true},direction:'S'});
}
window.benchEvidence={renderer:'Actual current SpriteScene + world-sprite-raster.js',direction,mode,study,pitch,phaseX,phaseY,background,bounds,placements};
window.benchFrames=[];
function Bench(){const [frame,setFrame]=useState(initial),[playing,setPlaying]=useState(live);window.benchSetFrame=f=>{setPlaying(false);setFrame(f)};window.benchPause=()=>setPlaying(false);
 useEffect(()=>{if(!playing)return;const start=performance.now(),first=frame;let raf;const tick=t=>{setFrame((first+Math.floor((t-start)*12/1000))%48);raf=requestAnimationFrame(tick)};raf=requestAnimationFrame(tick);return()=>cancelAnimationFrame(raf)},[playing]);
 useEffect(()=>{window.benchFrames.push({time:performance.now(),frame});window.benchCurrent={frame,playing};},[frame,playing]);
 return <>{live&&<><h1>Corner native candidate · {study}</h1><button onClick={()=>setPlaying(!playing)}>{playing?'Pause':'Play'}</button><input aria-label="Animation frame" type="range" min="0" max="47" value={frame} onChange={e=>{setPlaying(false);setFrame(Number(e.target.value))}}/><span id="status">{frame%24+1}/24 · 12fps</span></>}<SpriteScene placements={placements} gridSize={[0,0]} seconds={frame/12} overlays={false} showGrid={false} background={background} cameraBounds={bounds.map(v=>v/128)} label={`${direction} ${mode} ${study} actual consumer ${pitch}px`}/></>;
}
document.getElementById('root').style.width=`${bounds[2]*pitch/128}px`;
createRoot(document.getElementById('root')).render(<Bench/>);
