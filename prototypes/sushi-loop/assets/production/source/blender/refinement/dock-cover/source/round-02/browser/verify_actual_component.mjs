import fs from'node:fs';import path from'node:path';import{fileURLToPath}from'node:url';import{chromium}from'playwright';
const H=path.dirname(fileURLToPath(import.meta.url)),O=path.resolve(H,'../../..'),OUT=path.join(O,'candidates/round-02/consumer-dom');fs.mkdirSync(OUT,{recursive:true});
const evidence=JSON.parse(fs.readFileSync(path.join(O,'candidates/round-02/consumer/consumer-evidence.json'))),b=await chromium.launch({headless:true}),p=await b.newPage({viewport:{width:390,height:844},deviceScaleFactor:1}),errors=[];
p.on('pageerror',e=>errors.push(String(e)));p.on('console',e=>{if(e.type()==='error')errors.push(e.text());});
await p.goto('http://127.0.0.1:5197/prototypes/sushi-loop/assets/refinement/objects/dock-cover/source/round-02/browser/index.html');await p.waitForSelector('[data-world-raster-ready="true"]');
const records=[],screens=[];let n=0;
async function inspect(r,phase=0){
 const expected=evidence.records.find(m=>m.direction===r.direction&&m.mode===r.mode&&m.clip===r.clip&&m.index===r.index&&m.commonLogicalRootPhase===phase)?.nativeHash;
 if(!expected)throw Error('Missing exact current-consumer reference');
 const scene={direction:r.direction,mode:r.mode,clip:r.clip,index:r.index,phase,pan:0,pitch:390/7,bg:'#f5f2e9'};await p.evaluate(scene=>window.setScene(scene),scene);
 const out=await p.evaluate(async expected=>{for(let attempt=0;attempt<180;attempt++){await new Promise(requestAnimationFrame);const c=document.querySelector('canvas');if(!c||!document.querySelector('[data-world-raster-ready="true"]'))continue;const a=c.getContext('2d').getImageData(0,0,c.width,c.height).data,h=[...new Uint8Array(await crypto.subtle.digest('SHA-256',a))].map(x=>x.toString(16).padStart(2,'0')).join('');if(h===expected)return{actualNativeCanvasSize:[c.width,c.height],decodedRGBASHA256:h,atomicCanvasRead:true};}throw Error('Actual canvas did not reach expected reference');},expected);records.push({...scene,...out,referenceSHA256:expected,exactDecodedNativeCanvasParity:out.decodedRGBASHA256===expected});
 if(phase===0&&r.mode==='upgraded-dock-ready'&&[['covered',0],['uncover',5],['uncover',11]].some(([c,i])=>c===r.clip&&i===r.index)){
  for(const[size,width,height,pitch]of[['phone',390,844,390/7],['desktop',1440,1100,128]]){await p.setViewportSize({width,height});await p.evaluate(q=>window.setScene(q),{...scene,pitch});await p.waitForFunction(q=>window.sceneState.pitch===q,pitch);await p.screenshot({path:path.join(OUT,`${size}-${r.clip}-${r.direction}-${r.index}.png`),fullPage:true});screens.push({size,mode:r.mode,clip:r.clip,direction:r.direction,index:r.index,pitch,path:path.relative(O,path.join(OUT,`${size}-${r.clip}-${r.direction}-${r.index}.png`))});}
  await p.setViewportSize({width:390,height:844});
 }
 if(++n%32===0)console.log('ACTUAL COMPONENT',n);
}
for(const r of evidence.nativeFrames)await inspect(r);
for(const r of evidence.nativeFrames)if(r.clip==='uncover'&&r.index===11)for(const phase of[.25,.5,.75])await inspect(r,phase);
fs.writeFileSync(path.join(OUT,'actual-SpriteScene-parity.json'),JSON.stringify({method:'Exact original SpriteScene function unchanged with current570 full hook and frozen layout; only fixture library and candidate Cover atlas/pass/height inputs adapted. Each case waits for exact decoded native canvas SHA parity against independent current-consumer sampler. Source projections, roots, modes and actual human frame unchanged.',records,screens,errors},null,2)+'\n');console.log(JSON.stringify({records:records.length,allExact:records.every(r=>r.exactDecodedNativeCanvasParity),screens:screens.length,errors}));await b.close();
