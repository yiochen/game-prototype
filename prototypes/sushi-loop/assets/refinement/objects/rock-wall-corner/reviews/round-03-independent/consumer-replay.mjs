import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { fileURLToPath } from 'node:url';
import { chromium } from '@playwright/test';
const REVIEW=path.dirname(fileURLToPath(import.meta.url));
const OUT=path.resolve(REVIEW,'../..');
const dest=path.join(REVIEW,'consumer-replay');fs.mkdirSync(dest,{recursive:true});
const server=http.createServer((req,res)=>{
 let p=path.resolve(OUT,'.'+decodeURIComponent(req.url.split('?')[0]));
 if(req.url!=='/'&&!p.startsWith(OUT+path.sep)){res.writeHead(403);res.end();return;}
 if(req.url==='/'){res.setHeader('Content-Type','text/html');res.end('<!doctype html><style>body{margin:0;background:#dfe3e6}svg{display:block}</style><script type="importmap">{"imports":{"react":"data:text/javascript,export const useLayoutEffect=()=>{};export const useRef=()=>{};export const useState=()=>{};"}}</script>');return;}
 if(!fs.existsSync(p)){res.writeHead(404);res.end();return;}
 res.setHeader('Content-Type',p.endsWith('.js')?'text/javascript':p.endsWith('.png')?'image/png':'application/json');res.end(fs.readFileSync(p));
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const port=server.address().port;
const browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1200,height:1000},deviceScaleFactor:1});page.on('pageerror',e=>console.log('PAGEERROR',e.message));await page.goto(`http://127.0.0.1:${port}/`);
await page.addScriptTag({type:'module',content:`
import * as layout from '/source/resources/sprite-layout.js';
import {worldRasterPlan,paintWorldRaster} from '/source/resources/world-sprite-raster.js';
window.ready=true;
window.renderCase=async (direction,pitch,phase=0,bg='#dfe3e6',pan=0)=>{
 const corner=await fetch('/source/resources/inputs/catalog-object.json').then(r=>r.json());
 const middle={...corner,id:'rock-wall-middle',name:'Exact approved middle',ports:{},portProfiles:{}};
 const dirs=['S','E','N','W'],turn=dirs.indexOf(direction),angle=turn*Math.PI/2;
 const source=[{id:'corner',object:corner.id,x:1,y:1,direction:'S'},{id:'W-middle',object:middle.id,x:0,y:1,direction:'S'},{id:'N-middle',object:middle.id,x:1,y:0,direction:'E'}];
 const placements=source.map(p=>{const x=p.x-1,y=p.y-1;return {...p,x:1+Math.cos(angle)*x+Math.sin(angle)*y+phase/128,y:1-Math.sin(angle)*x+Math.cos(angle)*y+phase/128,direction:dirs[(dirs.indexOf(p.direction)+turn)%4]}});
 const objects=[corner,middle],ordered=layout.orderPlacements(placements,objects),bounds=layout.sceneBounds(placements,objects,128,[3,3]);
 bounds[0]+=phase+pan;bounds[1]+=phase-pan;
 const sprites=ordered.map(p=>{const o=objects.find(o=>o.id===p.object),f=layout.spriteFrame(o,o.clips[0],p.direction,0),root=layout.groundRoot(p,o,128);return {url:p.object===corner.id?'/candidates/round-03/published-static-'+p.direction+'.png':'/source/resources/approved-middle/published-'+p.direction+'.png',rect:f.rect,x:root[0]-f.root[0],y:root[1]-f.root[1],width:f.frameSize[0],height:f.frameSize[1],placement:p}});
 const plan=worldRasterPlan(sprites,bounds),ims=await Promise.all(sprites.map(s=>new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=reject;im.src=s.url;})));
 document.querySelector('svg')?.remove();const ns='http://www.w3.org/2000/svg';const svg=document.createElementNS(ns,'svg');svg.id='scene';svg.setAttribute('viewBox',bounds.join(' '));svg.setAttribute('width',bounds[2]*pitch/128);svg.setAttribute('height',bounds[3]*pitch/128);svg.style.background=bg;
 const foreign=document.createElementNS(ns,'foreignObject');for(const [k,v]of Object.entries({x:plan.x,y:plan.y,width:plan.width/plan.scale,height:plan.height/plan.scale}))foreign.setAttribute(k,v);
 const canvas=document.createElement('canvas');canvas.style.cssText='display:block;width:100%;height:100%';foreign.append(canvas);svg.append(foreign);document.body.append(svg);paintWorldRaster(canvas,plan,ims);await new Promise(requestAnimationFrame);await new Promise(requestAnimationFrame);
 return {direction,pitch,phase,viewport:[innerWidth,innerHeight],placements,order:ordered.map(p=>p.id),bounds,plan:{x:plan.x,y:plan.y,width:plan.width,height:plan.height,scale:plan.scale},canvasSize:[canvas.width,canvas.height],smoothing:canvas.getContext('2d').imageSmoothingEnabled,cssImageRendering:getComputedStyle(canvas).imageRendering,frame:0};
};`});
await page.waitForFunction(()=>window.ready);
const cases=[];
for(const viewport of [{name:'logical',width:1200,height:1100,pitch:128},{name:'phone',width:390,height:844,pitch:32},{name:'landscape',width:844,height:390,pitch:32}]){
 await page.setViewportSize({width:viewport.width,height:viewport.height});
 for(const d of ['N','E','S','W'])for(const phase of [.61])for(const [background,bg] of [['gray','#90959c']]){
  const pitch=viewport.pitch*(phase===.61?.9875:1),pan=phase===.61?.37:0;
  const evidence=await page.evaluate(async ({d,pitch,phase,bg,pan})=>await window.renderCase(d,pitch,phase,bg,pan),{d,pitch,phase,bg,pan});
  const name=viewport.name+'-'+d+'-phase'+phase+'-'+background;await page.locator('#scene').screenshot({path:path.join(dest,name+'.png')});cases.push({...evidence,background,pan,path:'candidates/round-03/consumer/'+name+'.png'});
 }
}
fs.writeFileSync(path.join(dest,'cases.json'),JSON.stringify({fixture:'Exact snapshotted sprite-layout/world-sprite-raster functions, identical SpriteScene mapping and SVG foreignObject canvas presentation. React import stub only; hooks never invoked. Own independent whole BOX2x published corner plus immutable canonical middle atlases. Common native canvas nearest AFTER resize then ordinary browser wholecanvas final filtering. No fit, pixel repair, nudge, masks, added overlap or per-view grades.',browser:browser.version(),cases},null,2)+'\n');await browser.close();server.close();
