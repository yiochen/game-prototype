import test from 'node:test';
import assert from 'node:assert/strict';
import {assets,assetById,blankMap,exampleMap,paintCells,lineCells,rectCells,resizeMap,exportMap,parseMap,fileName,limits,rowNumber,startingCell} from '../design/underwater-map-designer/model.js';
const rock={layer:'obstacles',object:'rock-wall-middle',direction:'S'};
const coral={layer:'decor',object:'decor-foreground-coral',direction:'E'};
test('paint replaces only its layer; erase preserves overlapping decoration and repeated paint is a no-op',()=>{
 let map=blankMap();map=paintCells(map,[{x:2,y:3}],rock);map=paintCells(map,[{x:2,y:3}],coral);assert.equal(map.placements.length,2);
 assert.equal(paintCells(map,[{x:2,y:3}],coral),map);
 map=paintCells(map,[{x:2,y:3}],{layer:'obstacles',erase:true});assert.deepEqual(map.placements.map(p=>p.layer),['decor']);
 assert.equal(paintCells(map,[{x:-1,y:3},{x:7,y:3}],rock),map);
});
test('sparse strokes fill every crossed cell and clipped rectangles stay inside the map',()=>{
 const map=paintCells(blankMap(),lineCells({x:0,y:5},{x:6,y:5}),rock);assert.equal(map.placements.length,7);assert.deepEqual(map.placements.map(p=>p.x),[0,1,2,3,4,5,6]);
 const cells=rectCells({x:-5,y:77},{x:9,y:90},blankMap());assert.equal(cells.length,21);assert.ok(cells.every(p=>p.x>=0&&p.x<7&&p.y>=77&&p.y<80));
});
test('export/import roundtrip retains exact asset IDs, integer coordinates, facings and collision layers',()=>{
 let map=paintCells(blankMap('Coral passage',9,32),[{x:2,y:17}],rock);map=paintCells(map,[{x:2,y:17}],coral);
 const json=exportMap(map),roundtrip=exportMap(parseMap(JSON.stringify(json)));assert.deepEqual(roundtrip,json);assert.deepEqual(json.layers,[{id:'obstacles',collidable:true},{id:'decor',collidable:false}]);assert.equal(json.grid.cellSize,128);assert.equal(json.coordinates.origin,'top-left');assert.ok(json.placements.every(p=>p.footprint.every(Number.isInteger)));
});
test('imports reject unknown assets, fractional positions, wrong layers, duplicate cells and unsupported versions',()=>{
 const good=exportMap(paintCells(blankMap(),[{x:2,y:3}],rock));
 for(const mutation of [v=>v.version=99,v=>v.grid.rows=1000,v=>v.placements[0].x=.5,v=>v.placements[0].x=8,v=>v.placements[0].object='missing',v=>v.placements[0].direction='NE',v=>v.placements[0].layer='decor',v=>v.placements.push({...v.placements[0]})]){const v=structuredClone(good);mutation(v);assert.throws(()=>parseMap(v));}
 assert.throws(()=>parseMap('{broken'));
});
test('resize deliberately crops out-of-bounds tiles without changing surviving coordinates',()=>{
 const original=paintCells(blankMap('Resize',9,32),[{x:8,y:20},{x:2,y:3}],rock);const resized=resizeMap(original,7,16);assert.equal(original.placements.length,2);assert.deepEqual(resized.placements.map(p=>[p.x,p.y]),[[2,3]]);assert.throws(()=>resizeMap(original,2,16));assert.throws(()=>resizeMap(original,7,1.5));
});
test('legacy tunnel maps retain registered tile IDs, frames and facings',()=>{
 const map=exampleMap();assert.deepEqual(exportMap(parseMap(exportMap(map))),exportMap(map));assert.ok(map.placements.length>200);assert.equal(assets.length,30);for(const a of assets){assert.ok(['obstacles','decor'].includes(a.layer));for(const d of Object.values(a.directions)){assert.ok(d.frameSize.every(v=>v>0));assert.equal(d.root.length,2);assert.ok(d.footprint.every(Number.isInteger));}}assert.ok(assetById.has('floor-underwater'));assert.equal(fileName('My reef / draft'),'My-reef-draft.json');
});

test('the largest supported dense map fits inside its own JSON import limit',()=>{
 const map=blankMap('Maximum supported map',32,256),cells=[];for(let y=0;y<256;y++)for(let x=0;x<32;x++){cells.push({...rock,x,y});cells.push({...coral,x,y});}
 const dense=paintCells(map,cells,null),text=JSON.stringify(exportMap(dense),null,2);assert.ok(Buffer.byteLength(text)<limits.maxImportBytes);assert.equal(parseMap(text).placements.length,32*256*2);
});

test('bottom-first display rows and keyboard start preserve existing exported coordinates',()=>{
 const map=blankMap('Upward route',7,80),start=startingCell(map);assert.deepEqual(start,{x:3,y:79});assert.equal(rowNumber(map,start.y),1);assert.equal(rowNumber(map,start.y-1),2);assert.equal(rowNumber(map,0),80);
 const painted=paintCells(map,[start],rock),exported=exportMap(painted);assert.equal(exported.placements[0].y,79);assert.equal(exported.coordinates.origin,'top-left');assert.deepEqual(exportMap(parseMap(exported)),exported);
});
