// Bounded fixture of actual consumer functions and frozen object/image inputs.
// No mutable global catalog or Vite server is read by this check.
import { chromium } from './resources/runtime/node_modules/@playwright/test/index.mjs';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import * as layout from './resources/sprite-layout.js';
const OUT=path.dirname(fileURLToPath(import.meta.url));
const RES=path.join(OUT,'resources');const DEST=path.join(OUT,'consumer-baseline');fs.mkdirSync(DEST,{recursive:true});
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const end=JSON.parse(fs.readFileSync(path.join(RES,'object/inputs/catalog-object.json'),'utf8'));
const middle=JSON.parse(JSON.stringify(end));middle.id='rock-wall-middle';middle.name='Frozen approved-middle bounded fixture';
// Registration/one-cell frame contract is exact approved-middle familySettings.
// Paths are explicitly bound to canonical reference images; no mutable library.
const objects=[end,middle];const byId=new Map(objects.map(o=>[o.id,o]));
const source=fs.readFileSync(path.join(RES,'world-sprite-raster.js'),'utf8');
const raster=source.slice(source.indexOf('export function worldRasterPlan'),source.indexOf('export function useWorldSpriteRaster')).replaceAll('export function','function');
const imageData={};for(const dir of 'NESW'){
 imageData[`rock-wall-end-${dir}`]='data:image/png;base64,'+fs.readFileSync(path.join(RES,`source-catalog/static-${dir}.png`)).toString('base64');
 imageData[`rock-wall-middle-${dir}`]='data:image/png;base64,'+fs.readFileSync(path.join(RES,`approved-middle/published-${dir}.png`)).toString('base64');
}
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:900,height:700},deviceScaleFactor:1});
await page.setContent('<!doctype html><html><body style="margin:0"><svg xmlns="http://www.w3.org/2000/svg" id="scene" style="display:block;overflow:hidden" viewBox="-168 -328 336 496"></svg></body></html>');
await page.addScriptTag({content:raster});
await page.evaluate(async data=>{
 window.loaded={};for(const [key,value]of Object.entries(data)){const i=new Image();i.src=value;await i.decode();window.loaded[key]=i;}
 window.fixtureCanvas=document.createElement('canvas');
 window.drawFixture=(sprites,bounds,pitch,phase,bg)=>{
  const svg=document.getElementById('scene');svg.replaceChildren();
  svg.style.width=`${336*pitch/128}px`;svg.style.height=`${496*pitch/128}px`;svg.style.transform=`translate(${phase[0]}px,${phase[1]}px)`;svg.style.background=bg;document.body.style.background=bg;
  const plan=worldRasterPlan(sprites,bounds);
  // Force dimensions/state to wrong values first to prove nearest is restored after resize.
  const canvas=window.fixtureCanvas;canvas.width=1;canvas.height=1;canvas.getContext('2d').imageSmoothingEnabled=true;
  paintWorldRaster(canvas,plan,sprites.map(s=>window.loaded[s.imageKey]));
  const node=document.createElementNS(svg.namespaceURI,'foreignObject');
  for(const[k,v]of Object.entries({x:plan.x,y:plan.y,width:plan.width/plan.scale,height:plan.height/plan.scale}))node.setAttribute(k,v);
  canvas.style.cssText='display:block;width:100%;height:100%;image-rendering:auto';node.append(canvas);svg.append(node);
  return {plan,smoothingAfterResize:canvas.getContext('2d').imageSmoothingEnabled,canvasSize:[canvas.width,canvas.height],cssPitch:pitch,background:bg,finalCanvasStyle:canvas.style.cssText};
 };
},imageData);
const vectors={S:[1,0],E:[0,-1],N:[-1,0],W:[0,1]};const opposite={S:'N',N:'S',E:'W',W:'E'};
const cases=[];
for(const endDir of 'NESW')for(const middleMode of ['same-facing','reversed-middle']){
 const v=vectors[endDir];const middleDir=middleMode==='same-facing'?endDir:opposite[endDir];
 const placements=[{id:'middle',object:middle.id,x:-v[0]*.5-.5,y:-v[1]*.5-.5,direction:middleDir},{id:'end',object:end.id,x:v[0]*.5-.5,y:v[1]*.5-.5,direction:endDir}];
 const ordered=layout.orderPlacements(placements,objects);
 for(const pitch of [128,32,47.3])for(const phase of [[0,0],[.25,.5],[.5,.75],[.75,.25]])for(const bg of ['#808080','#f5f2e9','#182231']){
  const sprites=ordered.map(p=>{const ob=byId.get(p.object);const f=layout.spriteFrame(ob,layout.clipFor(ob,'static'),p.direction,0);const r=layout.groundRoot(p,ob,128);return {imageKey:p.object+'-'+p.direction,rect:f.rect,x:r[0]-f.root[0],y:r[1]-f.root[1],width:f.frameSize[0],height:f.frameSize[1]};});
  const viewport=pitch===32?{width:390,height:844}:pitch===47.3?{width:844,height:390}:{width:900,height:700};
  await page.setViewportSize(viewport);
  const result=await page.evaluate(args=>window.drawFixture(...args),[sprites,[-168,-328,336,496],pitch,phase,bg]);
  const keep=bg==='#808080'&&phase[0]===.25||middleMode==='same-facing'&&pitch===128&&phase[0]===0&&bg!=='#808080';
  const id=[endDir,middleMode,pitch,phase.join('-'),bg.slice(1)].join('-');
  if(keep)await page.locator('#scene').screenshot({path:path.join(DEST,id+'.png')});
  if(result.smoothingAfterResize!==false)throw Error('Nearest sampling was not restored after resize');
  cases.push({id,endDir,middleDir,middleMode,pitch,phase,bg,viewport,placements,order:ordered.map(p=>p.id),result,retained:keep?`consumer-baseline/${id}.png`:null});
 }
}
const facts={purpose:'Preparation diagnostic source catalog end with exact canonical middle, not candidate approval',actualConsumerFunctionHashes:{'sprite-layout.js':hash(path.join(RES,'sprite-layout.js')),'world-sprite-raster.js':hash(path.join(RES,'world-sprite-raster.js')),'object-review.jsx':hash(path.join(RES,'object-review.jsx')),'object-review.css':hash(path.join(RES,'object-review.css'))},boundedFixture:'Only two frozen object descriptors; end descriptor exact source catalog. Middle shares fixed registered frame/root/scale/footprint from canonical family settings and uses exact immutable approved images.',placements:'End local+X=.5 / middle local-X=-.5, each complete assembly rotated through all4; reversed-middle probes W-to-W via180-degree middle rotation. No image nudge, overlap, warps, per-view fit or pixel repair.',sampling:'Actual worldRasterPlan + paintWorldRaster; common native2x grid. Nearest restored after dimensions reset. One complete foreignObject canvas receives ordinary final browser filtering.',browserVersion:browser.version(),browserExecutable:chromium.executablePath(),browserExecutableSHA256:hash(chromium.executablePath()),nodeVersion:process.version,caseCount:cases.length,retained:cases.filter(c=>c.retained).length,cases};
fs.writeFileSync(path.join(OUT,'consumer-fixture-evidence.json'),JSON.stringify(facts,null,2)+'\n');
await browser.close();console.log(JSON.stringify({cases:cases.length,retained:facts.retained,version:facts.browserVersion}));
