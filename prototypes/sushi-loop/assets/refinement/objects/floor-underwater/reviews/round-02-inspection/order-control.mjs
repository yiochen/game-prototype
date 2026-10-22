import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync} from 'node:fs';
import path from 'node:path';import {fileURLToPath} from 'node:url';import {createRequire} from 'node:module';
const P=path.dirname(fileURLToPath(import.meta.url)),O=path.resolve(P,'../..'),require=createRequire(import.meta.url);
const {chromium}=require(path.join(P,'resources/node-loaded/playwright/index.js'));
const functions=readFileSync(path.join(P,'resources/world-raster-functions.js'),'utf8').replaceAll('export function','function');
const atlas=readFileSync(path.join(O,'candidates/round-01/atlases/scroll-N.png')),reports=[];
for(const backend of ['full-chrome','headless-shell']){
 const browser=await chromium.launch({headless:true,...(backend==='full-chrome'?{executablePath:chromium.executablePath()}:{} )});
 try{
  const page=await browser.newPage();await page.setContent('<body></body>');await page.addScriptTag({content:functions});
  const result=await page.evaluate(async atlasURL=>{
   const image=new Image();image.src=atlasURL;await image.decode();
   const actor=document.createElement('canvas');actor.width=actor.height=256;
   const ac=actor.getContext('2d');ac.fillStyle='#ed408080';ac.fillRect(24,24,208,208);
   const results=[];
   for(const offset of [[0,0],[.125,.375],[.25,.5],[.5,.25],[.875,.625]])for(const phase of [0,5,11]){
    const rect=[phase%6*256,Math.floor(phase/6)*256,256,256];
    const tiles=Array.from({length:9},(_,i)=>({rect,x:offset[0]+i%3*128,y:offset[1]+Math.floor(i/3)*128,width:128,height:128}));
    // Deliberately interpose a differently phased translucent actor before a later
    // tile-phased foreground sprite. Grouping all equal phases would reorder it.
    const actors=[{rect:[0,0,256,256],x:offset[0]+96.125,y:offset[1]+96.375,width:128,height:128},{rect,x:offset[0]+128,y:offset[1]+128,width:128,height:128}];
    const sprites=[...tiles,...actors],plan=worldRasterPlan(sprites,[-32,-32,448,448]);
    const output=document.createElement('canvas');paintWorldRaster(output,plan,[...tiles.map(()=>image),actor,image]);
    const whole=document.createElement('canvas');whole.width=whole.height=768;const wc=whole.getContext('2d');wc.imageSmoothingEnabled=false;
    for(let i=0;i<9;i++)wc.drawImage(image,...rect,i%3*256,Math.floor(i/3)*256,256,256);
    const reference=document.createElement('canvas');reference.width=plan.width;reference.height=plan.height;
    const rc=reference.getContext('2d');rc.imageSmoothingEnabled=false;rc.drawImage(whole,(offset[0]-plan.x)*2,(offset[1]-plan.y)*2);
    for(const [i,sprite] of actors.entries())rc.drawImage(i?image:actor,...sprite.rect,(sprite.x-plan.x)*2,(sprite.y-plan.y)*2,256,256);
    const actual=output.getContext('2d').getImageData(0,0,output.width,output.height).data,expected=rc.getImageData(0,0,reference.width,reference.height).data;
    let differences=0;for(let i=0;i<actual.length;i++)if(actual[i]!==expected[i])differences++;
    const interior=output.getContext('2d').getImageData(Math.ceil((offset[0]-plan.x)*2)+1,Math.ceil((offset[1]-plan.y)*2)+1,766,766).data;
    let nonOpaque=0;for(let i=3;i<interior.length;i+=4)if(interior[i]!==255)nonOpaque++;
    results.push({offset,phase,differences,nonOpaque});
   }return results;
  },'data:image/png;base64,'+atlas.toString('base64'));
  reports.push({backend,browserVersion:browser.version(),atlasSHA256:createHash('sha256').update(atlas).digest('hex'),results:result});
  assert.ok(result.every(r=>r.differences===0&&r.nonOpaque===0));
 }finally{await browser.close();}
}
writeFileSync(path.join(P,'order-control.json'),JSON.stringify({scope:'Exact asset atlas, original positions; independent ordered whole-floor reference plus differently phased translucent actor and later tile-phased foreground. No generic renderer approval.',reports},null,2)+'\n');
console.log(JSON.stringify(reports.map(r=>({backend:r.backend,cases:r.results.length,differences:r.results.reduce((s,r)=>s+r.differences,0),alphaFailures:r.results.filter(r=>r.nonOpaque).length}))));
