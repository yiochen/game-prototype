/* Candidate-specific reuse of frozen extent procedure; comparison only.
 * Trigger: retained actual full-Chromium alpha255/opaqueRGB209 residuals.
 * No change to art, source frames, registration, helpers or production runtime.
 */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const {chromium}=require('@playwright/test');const O=path.resolve(__dirname,'..'),C=path.join(O,'candidates/round-01'),OUT=path.join(C,'extent-diagnostic');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
if(fs.existsSync(OUT))throw Error('Immutable diagnostic output exists');fs.mkdirSync(OUT,{recursive:true});
const server=http.createServer((req,res)=>{try{const p=path.join(O,decodeURIComponent(req.url.split('?')[0]));if(!p.startsWith(O+path.sep))throw Error('outside');res.setHeader('Content-Type',p.endsWith('.js')?'text/javascript':p.endsWith('.json')?'application/json':p.endsWith('.png')?'image/png':'text/html');res.end(fs.readFileSync(p));}catch(e){res.statusCode=404;res.end('missing');}});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));try{
for(const[backend,options]of [['full-chromium',{headless:true,channel:'chromium'}],['headless-shell',{headless:true}]]){
 const browser=await chromium.launch(options);try{
 const page=await browser.newPage({viewport:{width:1200,height:1200},deviceScaleFactor:1});await page.goto(`http://127.0.0.1:${server.address().port}/source/resources/host.html`);
 const result=await page.evaluate(async backend=>{
  const R=await import('/source/resources/exact-used-raster-functions.js'),raw=await fetch(`/candidates/round-01/consumer/${backend}-results.json`).then(r=>r.json()),cache=new Map,controls=[],records=[];
  const can=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;};
  const load=url=>new Promise((yes,no)=>{const im=new Image;im.onload=()=>yes(im);im.onerror=()=>no(Error(url));im.src=url;});
  const pixels=c=>c.getContext('2d').getImageData(0,0,c.width,c.height).data;
  const imagePixels=im=>{const c=can(im.width,im.height);c.getContext('2d').drawImage(im,0,0);return pixels(c);};
  async function image(url){if(!cache.has(url))cache.set(url,await load(url));return cache.get(url);}
  function metrics(a,b,mask){let differingPixels=0,maxAlphaDelta=0,opaqueRGBDifferences=0,maxOpaqueRGBDelta=0,localPixels=0,localAlphaDeficits=0,localMaxRGBDelta=0,localSum=0;
   for(let i=0;i<a.length;i+=4){const da=Math.abs(a[i+3]-b[i+3]),dr=Math.max(...[0,1,2].map(k=>Math.abs(a[i+k]-b[i+k])));if(da||dr)differingPixels++;maxAlphaDelta=Math.max(maxAlphaDelta,da);if(a[i+3]===255&&b[i+3]===255&&dr){opaqueRGBDifferences++;maxOpaqueRGBDelta=Math.max(maxOpaqueRGBDelta,dr);}if(mask&&mask[i+3]===255){localPixels++;if(a[i+3]<255||b[i+3]<255)localAlphaDeficits++;if(a[i+3]===255&&b[i+3]===255){localMaxRGBDelta=Math.max(localMaxRGBDelta,dr);localSum+=dr;}}}
   return{differingPixels,maxAlphaDelta,opaqueRGBDifferences,maxOpaqueRGBDelta,localPixels,localAlphaDeficits,localMaxRGBDelta,localMeanMaxRGBDelta:localSum/Math.max(1,localPixels)};}
  for(const kind of ['direct-canonical-to-end','full-family-L'])for(const d of ['N','E','S','W']){
   const zero=raw.records.find(r=>r.kind===kind&&r.d===d&&r.size===128&&r.phase===0),bounds=zero.bounds,ss=zero.sprites;
   const left=Math.min(...ss.map(s=>s.x)),top=Math.min(...ss.map(s=>s.y)),right=Math.max(...ss.map(s=>s.x+s.width)),bottom=Math.max(...ss.map(s=>s.y+s.height));
   const crop={x:Math.round((left-bounds[0])*2),y:Math.round((top-bounds[1])*2),width:Math.round((right-left)*2),height:Math.round((bottom-top)*2)};
   const native=await image(`/candidates/round-01/native/contexts/${kind}-${d}.png`),full=can(native.width,native.height);full.getContext('2d').drawImage(native,0,0);const src=pixels(full);let discardedVisiblePixels=0;
   for(let y=0;y<full.height;y++)for(let x=0;x<full.width;x++)if((x<crop.x||x>=crop.x+crop.width||y<crop.y||y>=crop.y+crop.height)&&src[(y*full.width+x)*4+3])discardedVisiblePixels++;
   if(discardedVisiblePixels)throw Error('Comparison-only crop discards visible pixels');
   const cropped=can(crop.width,crop.height),ctx=cropped.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.drawImage(native,crop.x,crop.y,crop.width,crop.height,0,0,crop.width,crop.height);const cropPNG=cropped.toDataURL('image/png'),cropImage=await load(cropPNG);
   const restored=can(full.width,full.height),rc=restored.getContext('2d');rc.imageSmoothingEnabled=false;rc.drawImage(cropImage,crop.x,crop.y);const integerRestoration=metrics(src,pixels(restored));if(integerRestoration.differingPixels)throw Error('Comparison-only restoration changed integer pixels');
   controls.push({kind,d,crop,originalDimensions:[native.width,native.height],independentIntermediateExtent:[crop.width,crop.height],discardedVisiblePixels,integerRestoration,cropPNG});
   for(const record of raw.records.filter(r=>r.kind===kind&&r.d===d)){
    const {rootPhase,panPhase,display}=record,zoom=display.zoom,plan=R.worldRasterPlan(record.sprites,bounds);const diagnostic=can(plan.width,plan.height);
    const pp={...plan,sprites:[{x:bounds[0]+crop.x/2+rootPhase,y:bounds[1]+crop.y/2+rootPhase,width:crop.width/2,height:crop.height/2,rect:[0,0,crop.width,crop.height]}]};R.paintWorldRaster(diagnostic,pp,[cropImage]);
    const out=can(display.width,display.height),oc=out.getContext('2d');oc.imageSmoothingEnabled=true;oc.drawImage(diagnostic,12+(plan.x-bounds[0])*zoom+panPhase,12+(plan.y-bounds[1])*zoom+panPhase,plan.width/plan.scale*zoom,plan.height/plan.scale*zoom);const diag=pixels(out);
    const actual=imagePixels(await image('/'+record.media.native)),independent=imagePixels(await image('/'+record.media.independent)),mask=imagePixels(await image('/'+record.media['local-join-mask']));
    records.push({id:record.id,kind,d,size:record.size,phase:record.phase,rootPhase,panPhase,actualConsumer:metrics(independent,actual,mask),comparisonOnlyEqualExtent:metrics(independent,diag,mask),paddingOnlyEffect:metrics(actual,diag,mask),comparisonPNG:out.toDataURL('image/png')});
   }
  }
  return{scope:'Comparison only; source extent normalized using registered sprite rectangles, not alpha fitting. All raw actual consumer outputs remain unchanged. Zero visible discard and exact integer restoration are prerequisites, never approval or a runtime workaround.',controls,records};
 },backend);
 for(const control of result.controls){const p=path.join(OUT,backend,control.kind+'-'+control.d+'-diagnostic-source.png');fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,Buffer.from(control.cropPNG.split(',')[1],'base64'));delete control.cropPNG;control.cropPath=path.relative(O,p);}
 for(const record of result.records){const p=path.join(OUT,backend,record.id+'.png');fs.writeFileSync(p,Buffer.from(record.comparisonPNG.split(',')[1],'base64'));delete record.comparisonPNG;record.comparisonPath=path.relative(O,p);}
 fs.writeFileSync(path.join(OUT,backend+'-results.json'),JSON.stringify({backend,browserVersion:browser.version(),launchOptions:options,viewport:{width:1200,height:1200},DPR:1,actualChildArgvLog:'source/round-01-extent-launch.log',frozenProcedureSHA256:sha(path.join(__dirname,'resources/frozen-source-extent-procedure.cjs')),frozenInterpretationSHA256:sha(path.join(__dirname,'resources/frozen-source-extent-interpretation.json')),...result},null,2)+'\n');
 console.log(JSON.stringify({backend,version:browser.version(),cases:result.records.length,controls:result.controls.length,zeroVisibleDiscard:result.controls.every(c=>c.discardedVisiblePixels===0),exactIntegerRestoration:result.controls.every(c=>c.integerRestoration.differingPixels===0)}));
 }finally{await browser.close();}
}
}finally{server.close();}})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
