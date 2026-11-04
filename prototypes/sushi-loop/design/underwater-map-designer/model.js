import catalog from './assets/catalog.json' with {type:'json'};
import {exampleBarriers} from './example-layout.js';
// Gold salvage is a chunk pickup, not a world sprite: it has no catalog frames.
const pickupAssets=[{id:'salvage-gold',name:'Gold salvage',layer:'pickups',group:'Salvage',directions:{S:{footprint:[1,1]}},footprint:[1,1]}];
export const assets=catalog.filter(a=>a.layer!=='floor');
export const assetById=new Map([...catalog,...pickupAssets].map(a=>[a.id,a]));
export const storageKey='sushi-loop-underwater-map-designer-v1';
export const limits={minColumns:3,maxColumns:32,minRows:8,maxRows:256,maxName:80,maxImportBytes:8*1024*1024};
export const layers=[{id:'obstacles',name:'Obstacles',collidable:true},{id:'decor',name:'Decor',collidable:false},{id:'pickups',name:'Gold',collidable:false}];
// Route chunks are 11-column maps carrying a `chunk` block (see route.js).
export const chunkKinds=['launch','start','normal','rest','fork','finish'];
export const chunkColumns=11;
export const blockTypes=[
 {layer:'obstacles',name:'Obstacle',color:'#e3a073',object:'rock-wall-middle',description:'Solid block · collidable'},
 {layer:'decor',name:'Decor',color:'#75b8a3',object:'decor-foreground-coral',description:'Decoration · non-collidable'},
 {layer:'pickups',name:'Gold',color:'#f2c230',object:'salvage-gold',description:'Gold salvage · open water only'},
];
export const blockTypeByLayer=new Map(blockTypes.map(t=>[t.layer,t]));
// Display rows follow the submarine's route: 1 at the bottom, increasing upward.
export const rowNumber=(map,y)=>map.rows-y;
export const startingCell=map=>({x:Math.floor(map.columns/2),y:map.rows-1});
export const cellKey=(layer,x,y)=>`${layer}:${x}:${y}`;
export function blankMap(name='Untitled passage',columns=7,rows=80,chunk=null){return {name,columns,rows,placements:[],chunk};}
export function exampleMap(){
 const map=blankMap('Turquoise passage'),items=[];
 for(let y=0;y<map.rows;y++)for(const [x,direction] of [[0,'E'],[6,'W']])items.push({layer:'obstacles',object:'rock-wall-middle',x,y,direction});
 for(const p of exampleBarriers){const y=p.y+72;if(y>=0&&y<map.rows)items.push({layer:'obstacles',object:p.object,x:p.x,y,direction:p.direction});}
 for(let y=0;y<map.rows;y+=2)for(const x of [0,6])items.push({layer:'decor',object:(y+x)%6===0?'decor-kelp':(y+x)%6===2?'decor-midground-coral':'decor-foreground-coral',x,y,direction:'S'});
 return paintCells(map,items,null);
}
export function inside(map,x,y){return Number.isInteger(x)&&Number.isInteger(y)&&x>=0&&y>=0&&x<map.columns&&y<map.rows;}
export function at(map,layer,x,y){return map.placements.find(p=>p.layer===layer&&p.x===x&&p.y===y);}
// Each cell holds one independent tile per layer. A replacement never touches the other layer.
export function paintCells(map,cells,brush){
 const items=new Map(map.placements.map(p=>[cellKey(p.layer,p.x,p.y),p]));let changed=false;
 for(const cell of cells){
  const {x,y}=cell,layer=brush?.layer||cell.layer;if(!inside(map,x,y)||!layers.some(l=>l.id===layer))continue;
  const key=cellKey(layer,x,y),old=items.get(key);
  const tile=brush?{...brush,x,y}:cell;
  if(tile.erase){if(items.delete(key))changed=true;continue;}
  const asset=assetById.get(tile.object);if(!asset||asset.layer!==layer||!asset.directions[tile.direction])continue;
  if(old?.object===tile.object&&old.direction===tile.direction)continue;
  items.set(key,{id:key,layer,object:tile.object,x,y,direction:tile.direction});changed=true;
 }
 return changed?{...map,placements:[...items.values()]}:map;
}
export function lineCells(a,b){
 const result=[],dx=b.x-a.x,dy=b.y-a.y,steps=Math.max(Math.abs(dx),Math.abs(dy),1);
 for(let i=0;i<=steps;i++)result.push({x:Math.round(a.x+dx*i/steps),y:Math.round(a.y+dy*i/steps)});
 return result;
}
export function rectCells(a,b,map){
 const cells=[];for(let y=Math.max(0,Math.min(a.y,b.y));y<=Math.min(map.rows-1,Math.max(a.y,b.y));y++)for(let x=Math.max(0,Math.min(a.x,b.x));x<=Math.min(map.columns-1,Math.max(a.x,b.x));x++)cells.push({x,y});return cells;
}
export function resizeMap(map,columns,rows){
 if(!Number.isInteger(columns)||columns<limits.minColumns||columns>limits.maxColumns||!Number.isInteger(rows)||rows<limits.minRows||rows>limits.maxRows)throw Error('Use 3–32 columns and 8–256 rows.');
 return {...map,columns,rows,placements:map.placements.filter(p=>p.x<columns&&p.y<rows)};
}
export function exportMap(map){
 return {format:'sushi-loop-underwater-map',version:1,name:map.name.trim()||'Untitled passage',grid:{columns:map.columns,rows:map.rows,cellSize:128},floor:'floor-underwater',coordinates:{origin:'top-left',x:'right',y:'down',placement:'cell-top-left'},layers:layers.filter(l=>l.id!=='pickups'||map.chunk||map.placements.some(p=>p.layer==='pickups')).map(({id,collidable})=>({id,collidable})),...(map.chunk?{chunk:{kind:map.chunk.kind,difficulty:map.chunk.difficulty??null,...(map.chunk.source?{source:map.chunk.source}:{})}}:{}),placements:[...map.placements].sort((a,b)=>a.layer.localeCompare(b.layer)||a.y-b.y||a.x-b.x).map(p=>({...p,footprint:assetById.get(p.object).directions[p.direction].footprint}))};
}
export function parseMap(input){
 let value;try{value=typeof input==='string'?JSON.parse(input):input;}catch{throw Error('This file is not valid JSON.');}
 if(!value||value.format!=='sushi-loop-underwater-map'||value.version!==1)throw Error('Choose a version 1 Sushi Loop underwater map.');
 const {columns,rows,cellSize}=value.grid||{};resizeMap(blankMap(),columns,rows);
 if(cellSize!==128||value.floor!=='floor-underwater')throw Error('This map needs the registered 128-unit underwater grid.');
 if(typeof value.name!=='string'||value.name.length>limits.maxName)throw Error('Map names must be 80 characters or fewer.');
 if(!Array.isArray(value.placements)||value.placements.length>columns*rows*layers.length)throw Error('The map has too many tiles.');
 let chunk=null;
 if(value.chunk!=null){
  const {kind,difficulty,source}=value.chunk;
  if(!chunkKinds.includes(kind))throw Error('Chunk kind must be start, normal, rest, fork or finish.');
  if(difficulty!=null&&!(typeof difficulty==='number'&&difficulty>=1&&difficulty<=5))throw Error('Chunk difficulty must be between 1 and 5.');
  chunk={kind,difficulty:difficulty??null,...(typeof source==='string'?{source}:{})};
 }
 const occupied=new Set(),placements=[];
 for(const p of value.placements){
  if(!p||!layers.some(l=>l.id===p.layer))throw Error('A tile has an unknown layer.');
  const asset=assetById.get(p.object);if(!asset||asset.layer!==p.layer)throw Error(`Unknown tile or wrong layer: ${String(p.object).slice(0,80)}.`);
  if(!inside({columns,rows},p.x,p.y))throw Error('A tile is outside the map or is not on a whole cell.');
  if(!asset.directions[p.direction])throw Error(`Unknown direction for ${p.object}.`);
  const key=cellKey(p.layer,p.x,p.y);if(occupied.has(key))throw Error('Two tiles occupy the same cell and layer.');occupied.add(key);
  placements.push({id:key,layer:p.layer,object:p.object,x:p.x,y:p.y,direction:p.direction});
 }
 return {name:value.name.trim()||'Untitled passage',columns,rows,placements,chunk};
}
export function fileName(name){return (name.normalize('NFKC').replace(/[^\p{L}\p{N}._-]+/gu,'-').replace(/^-+|-+$/g,'').slice(0,80)||'underwater-map')+'.json';}
