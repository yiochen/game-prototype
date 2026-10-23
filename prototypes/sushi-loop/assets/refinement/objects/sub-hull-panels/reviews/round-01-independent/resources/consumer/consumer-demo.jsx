import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import {clipFor,spriteFrame,sceneBounds,orderPlacements,groundRoot} from './resources/consumer/sprite-layout.js';
import {useWorldSpriteRaster} from './resources/consumer/world-sprite-raster.js';
import objects from './consumer-objects.json';
const colors={light:'#F5F1E8',gray:'#A8ADAE',dark:'#253038'};
function Scene({direction,frame,clip,bg}){
 const placements=[{object:'sub-hull-panels',x:0,y:1,direction,clip},{object:'creature-eel',x:3,y:1,direction,clip:'swim'},{object:'submarine-yellow',x:1,y:0,direction,clip:'native-mounted-neutral'}];
 const bounds=sceneBounds(placements,objects,128,[5,4]);
 const sprites=orderPlacements(placements,objects).map(p=>{
  const o=objects.find(o=>o.id===p.object),f=spriteFrame(o,clipFor(o,p.clip),direction,frame/12),[x,y]=groundRoot(p,o,128);
  return {url:new URL(f.image,location.href).href,rect:f.rect,x:x-f.root[0],y:y-f.root[1],width:f.frameSize[0],height:f.frameSize[1]};
 });
 const raster=useWorldSpriteRaster(sprites,bounds);
 return <section style={{background:colors[bg]}}><strong>{direction} · {clip} · frame {frame+1}/12</strong><svg viewBox={bounds.join(' ')} data-ready={raster.ready} data-error={raster.error||''} data-direction={direction} data-native-scale={raster.plan.scale}>
  <foreignObject x={raster.plan.x} y={raster.plan.y} width={raster.plan.width/raster.plan.scale} height={raster.plan.height/raster.plan.scale}><canvas ref={raster.canvas} style={{display:'block',width:'100%',height:'100%',visibility:raster.ready?'visible':'hidden'}}/></foreignObject>
 </svg></section>;
}
function App(){const [state,setState]=useState({frame:0,clip:'active',bg:'gray'});window.setReviewState=s=>setState(prev=>({...prev,...s}));return <main data-clip={state.clip} data-frame={state.frame} data-bg={state.bg}><h1>Hull armor native candidate</h1><p>Each scene shows a separate armor pair, an actual native assembled upgraded Sub, and an eel beside it. The frozen preliminary body is static; other equipment is provisional. Full native canvas composition uses nearest sampling, followed by ordinary whole-scene display filtering.</p><label>Phase<input type="range" min="0" max="11" value={state.frame} onChange={e=>setState({...state,frame:+e.target.value})}/></label><nav>{['idle','active'].map(clip=><button key={clip} onClick={()=>setState({...state,clip})}>{clip}</button>)}{Object.keys(colors).map(bg=><button key={bg} onClick={()=>setState({...state,bg})}>{bg}</button>)}</nav>{['N','E','S','W'].map(d=><Scene key={d} direction={d} {...state}/>)}</main>}
createRoot(document.getElementById('root')).render(<App/>);
