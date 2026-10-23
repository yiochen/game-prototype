import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { clipFor, spriteFrame, sceneBounds, orderPlacements, groundRoot } from './resources/consumer/sprite-layout.js';
import { useWorldSpriteRaster } from './resources/consumer/world-sprite-raster.js';
import selected from './resources/consumer/selected-objects.json';
const objects=structuredClone(selected);
const main=objects.find(o=>o.id==='submarine-yellow');
main.clips=[{id:'fixture',frames:1,fps:12,loop:false,static:true,directions:Object.fromEntries(['N','E','S','W'].map(d=>[d,{image:`../frozen-main-v1/baseline-${d}.png`,rects:[[0,0,640,768]],columns:1,rows:1,atlasSize:[640,768]}]))}];
const fixtureImage=(image)=>new URL('./resources/consumer/'+image,location.href).href;
function Scene({direction,frame}) {
 const placements=[{object:'sub-hull-panels',x:0,y:1,direction,clip:'active'},{object:'creature-eel',x:3,y:1,direction,clip:'swim'},{object:'submarine-yellow',x:1,y:0,direction,clip:'fixture'}];
 const bounds=sceneBounds(placements,objects,128,[5,4]);
 const sprites=orderPlacements(placements,objects).map(p=>{
  const o=objects.find(o=>o.id===p.object),f=spriteFrame(o,clipFor(o,p.clip),direction,frame/12),[x,y]=groundRoot(p,o,128);
  return {url:fixtureImage(f.image),rect:f.rect,x:x-f.root[0],y:y-f.root[1],width:f.frameSize[0],height:f.frameSize[1]};
 });
 const raster=useWorldSpriteRaster(sprites,bounds);
 return <section><strong>{direction} · original independent sprites · frame {frame+1}/12</strong><svg viewBox={bounds.join(' ')} data-ready={raster.ready} data-error={raster.error||''}>
  <defs><pattern id={'grid-'+direction} width="128" height="128" patternUnits="userSpaceOnUse"><path d="M128 0H0V128" fill="none" stroke="#abc5c8" strokeWidth="1"/></pattern></defs>
  <rect width="640" height="512" fill={`url(#grid-${direction})`}/>
  <foreignObject x={raster.plan.x} y={raster.plan.y} width={raster.plan.width/raster.plan.scale} height={raster.plan.height/raster.plan.scale}><canvas ref={raster.canvas} style={{display:'block',width:'100%',height:'100%',visibility:raster.ready?'visible':'hidden'}}/></foreignObject>
 </svg></section>;
}
function App(){const [frame,setFrame]=useState(0);window.setReviewFrame=setFrame;return <main><h1>Panel source preparation</h1><p>Frozen preliminary main body is static. Canonical upgrades are pending. The old panel and eel use separate registered sprites beside it. This does not certify an assembled upgraded Sub.</p><label>Frame <input type="range" min="0" max="11" value={frame} onChange={e=>setFrame(+e.target.value)}/></label>{['N','E','S','W'].map(d=><Scene key={d} direction={d} frame={frame}/>)}</main>;}
createRoot(document.getElementById('root')).render(<App/>);
