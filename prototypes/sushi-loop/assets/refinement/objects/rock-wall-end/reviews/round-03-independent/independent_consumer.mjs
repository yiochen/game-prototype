import { chromium } from './resources/experiment/source/resources/runtime/node_modules/@playwright/test/index.mjs';
import * as layout from './resources/experiment/source/resources/sprite-layout.js';
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';
const OUT=path.dirname(fileURLToPath(import.meta.url)),BASE=path.join(OUT,'resources/experiment'),C=path.join(BASE,'candidates/round-03');
const DEST=path.join(OUT,'consumer-reproduction');fs.mkdirSync(DEST,{recursive:true});
const end=JSON.parse(fs.readFileSync(path.join(BASE,'inputs/catalog-object.json'))),middle={...end,id:'rock-wall-middle'};
const objects=[end,middle],map=new Map(objects.map(o=>[o.id,o]));
const src=fs.readFileSync(path.join(BASE,'source/resources/world-sprite-raster.js'),'utf8');
const pure=src.slice(src.indexOf('export function worldRasterPlan'),src.indexOf('export function useWorldSpriteRaster')).replaceAll('export function','function');
const browser=await chromium.launch({headless:true}),page=await browser.newPage({deviceScaleFactor:1});
await page.setContent('<!doctype html><html><body style="margin:0"><svg xmlns="http://www.w3.org/2000/svg" id="scene" style="display:block;overflow:hidden" viewBox="-168 -328 336 496"></svg></body></html>');
await page.addScriptTag({content:pure});
const data={};for(const d of 'NESW')for(const type of ['end','middle']){
 const p=type==='end'?path.join(C,`atlases/static-${d}.png`):path.join(BASE,`inputs/approved-middle/published-${d}.png`);
 data[`rock-wall-${type}-${d}`]='data:image/png;base64,'+fs.readFileSync(p).toString('base64');
}
await page.evaluate(async data=>{window.images={};for(const[k,v]of Object.entries(data)){let im=new Image();im.src=v;await im.decode();window.images[k]=im;}window.draw=(sprites,pitch,phase,bg)=>{
 const svg=document.querySelector('svg');svg.replaceChildren();svg.style.width=`${336*pitch/128}px`;svg.style.height=`${496*pitch/128}px`;svg.style.transform=`translate(${phase[0]}px,${phase[1]}px)`;svg.style.background=bg;document.body.style.background=bg;
 const plan=worldRasterPlan(sprites,[-168,-328,336,496]),canvas=document.createElement('canvas');canvas.width=1;canvas.height=1;canvas.getContext('2d').imageSmoothingEnabled=true;
 paintWorldRaster(canvas,plan,sprites.map(s=>window.images[s.key]));
 const node=document.createElementNS(svg.namespaceURI,'foreignObject');for(const[k,v]of Object.entries({x:plan.x,y:plan.y,width:plan.width/plan.scale,height:plan.height/plan.scale}))node.setAttribute(k,v);
 canvas.style.cssText='display:block;width:100%;height:100%;image-rendering:auto';node.append(canvas);svg.append(node);
 return {plan,nearestAfterResize:!canvas.getContext('2d').imageSmoothingEnabled,raw:canvas.toDataURL()};};},data);
const v={N:[-1,0],E:[0,-1],S:[1,0],W:[0,1]},results=[];
for(const d of 'NESW')for(const pitch of [128,32,47.3])for(const phase of [[.25,.5],[.75,.25]])for(const bg of ['#808080','#f5f2e9','#182231']){
 const a=v[d],ps=[{id:'middle',object:middle.id,x:-a[0]*.5-.5,y:-a[1]*.5-.5,direction:d},{id:'end',object:end.id,x:a[0]*.5-.5,y:a[1]*.5-.5,direction:d}],ordered=layout.orderPlacements(ps,objects);
 const sprites=ordered.map(p=>{const o=map.get(p.object),f=layout.spriteFrame(o,layout.clipFor(o,'static'),d,0),r=layout.groundRoot(p,o);return{key:p.object+'-'+d,rect:f.rect,x:r[0]-f.root[0],y:r[1]-f.root[1],width:f.frameSize[0],height:f.frameSize[1]};});
 const viewport=pitch===32?{width:390,height:844}:pitch===47.3?{width:844,height:390}:{width:900,height:700};await page.setViewportSize(viewport);
 const r=await page.evaluate(args=>window.draw(...args),[sprites,pitch,phase,bg]);if(!r.nearestAfterResize)throw Error('sampling reset failure');
 const id=`${d}-same-facing-${pitch}-${phase.join('-')}-${bg.slice(1)}`;
 const png=await page.locator('svg').screenshot();let delivered=path.join(C,'consumer',id+'.png');
 const pngEqual=fs.existsSync(delivered)?png.equals(fs.readFileSync(delivered)):null;
 if(bg==='#808080'&&phase[0]===.25){fs.writeFileSync(path.join(DEST,id+'.png'),png);if(pitch!==128)await page.screenshot({path:path.join(DEST,'viewport-'+id+'.png')});}
 if(pitch===128&&phase[0]===.25&&bg==='#808080')fs.writeFileSync(path.join(DEST,`raw-native-${d}.png`),Buffer.from(r.raw.split(',')[1],'base64'));
 delete r.raw;results.push({d,pitch,phase,bg,viewport,id,sprites,order:ordered.map(p=>p.id),result:r,deliveredScreenshotBytesEqual:pngEqual});
}
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const report={packetSHA256:hash(path.join(C,'packet.json')),method:'Independent bounded harness using copied actual consumer functions, direct candidate atlas/canonical image inputs, complete shared native canvas then ordinary final filtering. No pixel repair or per-view fitting.',browserVersion:browser.version(),cases:results,allNearestAfterResize:results.every(r=>r.result.nearestAfterResize),comparableScreenshotCount:results.filter(r=>r.deliveredScreenshotBytesEqual!==null).length,allComparableScreenshotsExact:results.filter(r=>r.deliveredScreenshotBytesEqual!==null).every(r=>r.deliveredScreenshotBytesEqual)};
fs.writeFileSync(path.join(OUT,'independent-consumer-report.json'),JSON.stringify(report,null,2)+'\n');await browser.close();console.log(JSON.stringify({cases:results.length,compared:report.comparableScreenshotCount,exact:report.allComparableScreenshotsExact}));
