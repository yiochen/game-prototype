import { chromium } from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
const out=path.join(here,'consumer');await fs.mkdir(out,{recursive:true});
const resource=path.join(here,'resources/consumer');
const fullRaster=await fs.readFile(path.join(resource,'world-sprite-raster.js'),'utf8');
const exactRaster=fullRaster.slice(fullRaster.indexOf('export function worldRasterPlan'),fullRaster.indexOf('export function useWorldSpriteRaster'));
await fs.writeFile(path.join(resource,'exact-used-raster-functions.js'),exactRaster);
const sha=buffer=>crypto.createHash('sha256').update(buffer).digest('hex');
const provenance={source:'reviews/preparation-v1/resources/consumer/world-sprite-raster.js',sourceSHA256:sha(fullRaster),extract:'reviews/preparation-v1/resources/consumer/exact-used-raster-functions.js',extractSHA256:sha(exactRaster),boundary:['export function worldRasterPlan','before export function useWorldSpriteRaster'],processing:'Exact function/WeakMap text, no edits. React loading hook excluded because the fixture awaits image decoding itself.'};
await fs.writeFile(path.join(out,'raster-extract.json'),JSON.stringify(provenance,null,2)+'\n');
const html=`<!doctype html><html><meta charset="utf-8"><style>
body{margin:0;background:#e9efec;font-family:Arial,sans-serif}h1{font-size:16px;margin:12px}p{font-size:12px;margin:12px}#host{width:100%;overflow:hidden}svg{height:auto;display:block;max-width:none;min-width:100%;overflow:hidden}svg image{image-rendering:auto}canvas{display:block;width:100%;height:100%}
</style><h1 id="title"></h1><p>Original published source · exact registered native-canvas composition · ordinary whole-scene browser filtering</p><div id="host"></div><script type="module">
import {spriteFrame,clipFor,sceneBounds,orderPlacements,directionPlacements,repeatedPlacements,groundRoot} from '/resources/consumer/sprite-layout.js';
import {worldRasterPlan,paintWorldRaster} from '/resources/consumer/exact-used-raster-functions.js';
const lib=await fetch('/resources/consumer/selected-library.json').then(r=>r.json());const objects=lib.objects;const rock=objects.find(o=>o.id==='decor-background-rock');
const load=async url=>{const im=new Image();im.src=url;await im.decode();return im;};
const ns='http://www.w3.org/2000/svg';const node=(name,attrs,parent)=>{const e=document.createElementNS(ns,name);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);parent?.append(e);return e;};
window.show=async config=>{
 const placements=config.kind==='four'?directionPlacements(rock,'static'):config.kind==='repeat'?repeatedPlacements(rock,config.facing,'static'):rock.interactions[0].placements;
 const grid=config.kind==='four'?[8,2]:config.kind==='repeat'?[3,3]:[6,4];
 const bounds=sceneBounds(placements,objects,128,grid).map((v,i)=>i<2?v+(config.pan||0):v);
 const ordered=orderPlacements(placements,objects);
 const sprites=ordered.map(p=>{const o=objects.find(o=>o.id===p.object);const f=spriteFrame(o,clipFor(o,p.clip),p.direction||'S',config.seconds||0);const root=groundRoot(p,o,128);return {...f,url:'/resources/consumer/'+f.image,x:root[0]-f.root[0],y:root[1]-f.root[1],width:f.frameSize[0],height:f.frameSize[1],object:o.id,direction:p.direction};});
 const plan=worldRasterPlan(sprites,bounds);const host=document.getElementById('host');host.replaceChildren();const svg=node('svg',{viewBox:bounds.join(' '),width:'100%'},host);
 const floor=objects.find(o=>o.id==='floor-underwater');const ff=spriteFrame(floor,floor.clips[0],'S',0);const defs=node('defs',{},svg),pattern=node('pattern',{id:'floor',width:128,height:128,patternUnits:'userSpaceOnUse'},defs);
 const floorSvg=node('svg',{width:128,height:128,viewBox:ff.rect.join(' '),overflow:'hidden',preserveAspectRatio:'none'},pattern);node('image',{href:'/resources/consumer/'+ff.image,width:ff.atlasSize[0],height:ff.atlasSize[1]},floorSvg);
 node('rect',{x:0,y:0,width:grid[0]*128,height:grid[1]*128,fill:'#f2f0e6'},svg);node('rect',{x:0,y:0,width:grid[0]*128,height:grid[1]*128,fill:'url(#floor)'},svg);
 const fo=node('foreignObject',{x:plan.x,y:plan.y,width:plan.width/plan.scale,height:plan.height/plan.scale,'pointer-events':'none'},svg);
 const canvas=document.createElement('canvas');fo.append(canvas);const images=await Promise.all(sprites.map(s=>load(s.url)));paintWorldRaster(canvas,plan,images);
 await Promise.all([...svg.querySelectorAll('image')].map(e=>load(e.getAttribute('href'))));
 document.getElementById('title').textContent=config.name;
 return {config,bounds,plan:{...plan,sprites:undefined},spriteRecords:sprites.map(({image,frame,rect,frameSize,root,x,y,width,height,object,direction})=>({image,frame,rect,frameSize,root,x,y,width,height,object,direction})),order:ordered.map(p=>p.object),canvasSize:[canvas.width,canvas.height],canvasPNG:canvas.toDataURL(),cssCanvasRect:canvas.getBoundingClientRect().toJSON(),svgRect:svg.getBoundingClientRect().toJSON(),dpr:devicePixelRatio};
};window.fixtureReady=true;
</script></html>`;
await fs.writeFile(path.join(out,'fixture.html'),html);
const server=http.createServer(async(req,res)=>{try{const url=new URL(req.url,'http://localhost');const filename=url.pathname==='/'?path.join(out,'fixture.html'):path.join(here,decodeURIComponent(url.pathname));if(!filename.startsWith(here+path.sep)){res.writeHead(403);return res.end();}const buffer=await fs.readFile(filename);res.setHeader('Content-Type',filename.endsWith('.js')?'text/javascript':filename.endsWith('.png')?'image/png':filename.endsWith('.json')?'application/json':'text/html');res.end(buffer);}catch{res.writeHead(404);res.end();}});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const port=server.address().port;
const cases=[
 {name:'four-logical-wide',kind:'four',width:1128,height:720},
 {name:'four-phone320',kind:'four',width:320,height:720},
 {name:'repeat-S-phone320',kind:'repeat',facing:'S',width:320,height:720},
 {name:'repeat-N-landscape',kind:'repeat',facing:'N',width:1280,height:720},
 {name:'context-phone320',kind:'context',width:320,height:720},
 {name:'context-landscape-fractional',kind:'context',width:1280,height:720,pan:.1875}
];
const result={status:'source-only preparation; no candidate judgement',node:process.version,playwright:JSON.parse(await fs.readFile(path.join(resource,'playwright-package.json'),'utf8')).version,rasterProvenance:provenance,modes:[],limits:['Bounded standalone fixture uses exact actual sprite-layout/native-raster functions and SpriteScene SVG/foreignObject structure. It is consumer composition evidence; not an assertion of full React catalog page or native Godot execution.','Uses actual source sprites and the object\'s actual declared interaction placements. No other-object aesthetic verdict was read.']};
try{
 for(const [mode,launch] of [['chromium',{headless:true,channel:'chromium'}],['headless-shell',{headless:true}]]){
  const browser=await chromium.launch(launch);const entry={mode,launch,browserVersion:browser.version(),cases:[]};const context=await browser.newContext({deviceScaleFactor:1,reducedMotion:'reduce'});
  for(const c of cases){
   const page=await context.newPage();await page.setViewportSize({width:c.width,height:c.height});const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('http://127.0.0.1:'+port+'/');await page.waitForFunction(()=>window.fixtureReady);
   const rec=await page.evaluate(c=>window.show(c),c);const nativePNG=Buffer.from(rec.canvasPNG.split(',')[1],'base64');delete rec.canvasPNG;const basename=mode+'-'+c.name;
   await fs.writeFile(path.join(out,basename+'-native.png'),nativePNG);await page.screenshot({path:path.join(out,basename+'.png'),fullPage:true});
   entry.cases.push({...rec,viewport:{width:c.width,height:c.height},reducedMotion:'reduce',errors,screenshot:'reviews/preparation-v1/consumer/'+basename+'.png',nativeCanvas:'reviews/preparation-v1/consumer/'+basename+'-native.png',nativeCanvasSHA256:sha(nativePNG)});await page.close();
  }
  await context.close();await browser.close();result.modes.push(entry);console.log('CAPTURED_CONSUMER_MODE',mode,entry.browserVersion,entry.cases.length);
 }
}finally{server.close();}
await fs.writeFile(path.join(out,'results.json'),JSON.stringify(result,null,2)+'\n');
