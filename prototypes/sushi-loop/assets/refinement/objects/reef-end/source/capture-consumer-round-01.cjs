/* Exact570/099 consumer evidence, fixed registered frames, all planned cases. */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const {chromium}=require('@playwright/test');
const B=__dirname,O=path.resolve(B,'..'),C=path.join(O,'candidates/round-01'),OUT=path.join(C,'consumer');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
if(fs.existsSync(OUT))throw Error('Immutable consumer output exists');fs.mkdirSync(OUT,{recursive:true});
const server=http.createServer((req,res)=>{try{const p=path.join(O,decodeURIComponent(req.url.split('?')[0]));if(!p.startsWith(O+path.sep))throw Error('outside object');res.setHeader('Content-Type',p.endsWith('.js')?'text/javascript':p.endsWith('.json')?'application/json':p.endsWith('.png')?'image/png':'text/html');res.end(fs.readFileSync(p));}catch(e){res.statusCode=404;res.end('missing');}});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));try{
for(const [backend,options] of [['full-chromium',{headless:true,channel:'chromium'}],['headless-shell',{headless:true}]]){
 const browser=await chromium.launch(options);try{
 const records=[],errors=[],page=await browser.newPage({viewport:{width:1200,height:1200},deviceScaleFactor:1});page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(`http://127.0.0.1:${server.address().port}/source/resources/host.html`);
 await page.evaluate(async()=>{
  const R=await import('/source/resources/exact-used-raster-functions.js'),L=await import('/source/resources/sprite-layout.js');
  const geometry=await fetch('/candidates/round-01/context-geometry.json').then(r=>r.json());
  const dirs=['S','E','N','W'],angles={S:0,E:Math.PI/2,N:Math.PI,W:-Math.PI/2},bounds=[-416,-560,832,992],cache=new Map;
  const layouts={'direct-canonical-to-end':[['middle',-1,0,0,['E']],['end',0,0,0,['W']]],'full-family-L':[['middle',-2,2,-1,['E']],['edge',-2,1,-1,['W','E']],['corner',-2,0,-1,['W','N']],['middle',-1,0,0,['W','E']],['end',0,0,0,['W']]]};
  const can=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;};
  const load=url=>new Promise((yes,no)=>{const im=new Image;im.onload=()=>yes(im);im.onerror=()=>no(Error(url));im.src=url;});
  async function image(url){if(!cache.has(url))cache.set(url,await load(url));return cache.get(url);}
  function object(key){return{id:key,kind:'terrain',layer:2,frameSize:[192,352],root:[96,248],sourceScale:2,footprint:[1,1],rootCell:[.5,.5],clips:[{id:'static',frames:1,fps:12,loop:false,directions:Object.fromEntries(dirs.map(d=>[d,{image:key==='end'?`/candidates/round-01/frames/static/${d}/000.png`:key==='corner'?`/source/resources/corner-binding/${d}.png`:`/source/resources/heroes/reef-${key}/${d}.png`,rects:[[0,0,384,704]],sourceScale:2}]))}]};}
  const objects=['middle','edge','corner','end'].map(object);
  window.runCase=async({kind,d,size,rootPhase,panPhase})=>{
   const a=angles[d],q=dirs.indexOf(d),zoom=size/128,layout=layouts[kind];
   const placements=layout.map(([key,x,y,local],i)=>({id:'placement-'+i,object:key,x:x*Math.cos(a)-y*Math.sin(a)-.5,y:-(x*Math.sin(a)+y*Math.cos(a))-.5,direction:dirs[(q+local+4)%4],clip:'static'}));
   const sprites=L.orderPlacements(placements,objects).map(p=>{const o=objects.find(v=>v.id===p.object),f=L.spriteFrame(o,o.clips[0],p.direction,0),root=L.groundRoot(p,o,128);return{url:f.image,rect:f.rect,x:root[0]-f.root[0]+rootPhase,y:root[1]-f.root[1]+rootPhase,width:f.frameSize[0],height:f.frameSize[1],id:p.id,asset:p.object,direction:p.direction,root};});
   const native=[{url:`/candidates/round-01/native/contexts/${kind}-${d}.png`,rect:[0,0,1664,1984],x:bounds[0]+rootPhase,y:bounds[1]+rootPhase,width:832,height:992,id:'native-context'}];
   const w=Math.ceil(832*zoom)+24,h=Math.ceil(992*zoom)+24,stage=document.getElementById('stage');stage.replaceChildren();stage.style.width=(2*w+16)+'px';stage.style.height=h+'px';
   const out={},arrays={},plans={};
   for(const [name,ss] of [['native',native],['independent',sprites]]){
    const plan=R.worldRasterPlan(ss,bounds),layer=can(plan.width,plan.height);R.paintWorldRaster(layer,plan,await Promise.all(ss.map(s=>image(s.url))));plans[name]={x:plan.x,y:plan.y,width:plan.width,height:plan.height,scale:plan.scale};
    const display=can(w,h),ctx=display.getContext('2d');ctx.imageSmoothingEnabled=true;ctx.drawImage(layer,12+(plan.x-bounds[0])*zoom+panPhase,12+(plan.y-bounds[1])*zoom+panPhase,plan.width/plan.scale*zoom,plan.height/plan.scale*zoom);
    arrays[name]=ctx.getImageData(0,0,w,h).data;out[name]=display.toDataURL('image/png');
    layer.style.width=(plan.width/plan.scale*zoom)+'px';layer.style.height=(plan.height/plan.scale*zoom)+'px';layer.style.left=((name==='native'?0:w+16)+12+(plan.x-bounds[0])*zoom+panPhase)+'px';layer.style.top=(12+(plan.y-bounds[1])*zoom+panPhase)+'px';stage.appendChild(layer);
   }
   const mask=can(w,h),mc=mask.getContext('2d'),join=can(w,h),jc=join.getContext('2d');mc.fillStyle=jc.fillStyle='#fff';
   for(const [key,x,y,local,ports] of layout){
    const g=geometry.assets[key],rot=a+local*Math.PI/2,rx=x*Math.cos(a)-y*Math.sin(a),ry=x*Math.sin(a)+y*Math.cos(a);
    const vv=g.vertices.map(v=>{const xx=rx+v[0]*Math.cos(rot)-v[1]*Math.sin(rot),yy=ry+v[0]*Math.sin(rot)+v[1]*Math.cos(rot);return[12+(416+128*xx+rootPhase)*zoom+panPhase,12+(560-128*yy-89.6*v[2]+rootPhase)*zoom+panPhase];});
    for(const t of g.triangles){
     mc.beginPath();t.forEach((i,k)=>mc[k?'lineTo':'moveTo'](...vv[i]));mc.closePath();mc.fill();
     const near=ports.some(port=>t.every(i=>{const v=g.vertices[i];return port==='W'?v[0]<=-.42+1e-6:port==='E'?v[0]>=.42-1e-6:v[1]>=.42-1e-6;}));
     if(near){jc.beginPath();t.forEach((i,k)=>jc[k?'lineTo':'moveTo'](...vv[i]));jc.closePath();jc.fill();}
    }
   }
   const m=mc.getImageData(0,0,w,h).data,j=jc.getImageData(0,0,w,h).data,n=arrays.native,b=arrays.independent,rad=size===128?2:1;
   const diagnostic=can(w,h),dc=diagnostic.getContext('2d'),dm=dc.createImageData(w,h),samples=[];
   let alphaDifferences=0,maxAlphaDelta=0,opaqueRGBDifferences=0,maxOpaqueRGBDelta=0,finiteInteriorPixels=0,nativeInteriorAlphaLoss=0,independentInteriorAlphaLoss=0,localJoinPixels=0,localJoinNativeAlphaLoss=0,localJoinIndependentAlphaLoss=0,localJoinRGBDifferences=0,localJoinMaxRGBDelta=0,localJoinSumRGB=0,outerAlphaDifferences=0;
   for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const i=(y*w+x)*4,da=Math.abs(n[i+3]-b[i+3]),dr=Math.max(...[0,1,2].map(k=>Math.abs(n[i+k]-b[i+k])));if(da){alphaDifferences++;maxAlphaDelta=Math.max(maxAlphaDelta,da);}if(n[i+3]===255&&b[i+3]===255&&dr){opaqueRGBDifferences++;maxOpaqueRGBDelta=Math.max(maxOpaqueRGBDelta,dr);}
    let inside=m[i+3]===255;
    if(inside)for(let dy=-rad;dy<=rad&&inside;dy++)for(let dx=-rad;dx<=rad;dx++){const xx=x+dx,yy=y+dy;if(xx<0||yy<0||xx>=w||yy>=h||m[(yy*w+xx)*4+3]!==255){inside=false;break;}}
    if(inside){finiteInteriorPixels++;if(n[i+3]<255)nativeInteriorAlphaLoss++;if(b[i+3]<255)independentInteriorAlphaLoss++;}else if(da)outerAlphaDifferences++;
    if(inside&&j[i+3]===255){localJoinPixels++;if(n[i+3]<255)localJoinNativeAlphaLoss++;if(b[i+3]<255)localJoinIndependentAlphaLoss++;if(n[i+3]===255&&b[i+3]===255){if(dr)localJoinRGBDifferences++;localJoinMaxRGBDelta=Math.max(localJoinMaxRGBDelta,dr);localJoinSumRGB+=dr;}dm.data.set([Math.min(255,dr*6),Math.min(255,da*6),n[i+3]<255||b[i+3]<255?255:0,255],i);if((da||dr>30)&&samples.length<24)samples.push({xy:[x,y],native:Array.from(n.slice(i,i+4)),independent:Array.from(b.slice(i,i+4)),alphaDelta:da,maxRGBDelta:dr});}
   }
   dc.putImageData(dm,0,0);out['local-join-mask']=diagnostic.toDataURL('image/png');
   return{out,metrics:{alphaDifferences,maxAlphaDelta,opaqueRGBDifferences,maxOpaqueRGBDelta,finiteInteriorPixels,nativeInteriorAlphaLoss,independentInteriorAlphaLoss,localJoinPixels,localJoinNativeAlphaLoss,localJoinIndependentAlphaLoss,localJoinRGBDifferences,localJoinMaxRGBDelta,localJoinMeanMaxRGBDelta:localJoinSumRGB/Math.max(1,localJoinPixels),outerAlphaDifferences},localSamples:samples,plans,sprites,placements,layout,display:{width:w,height:h,zoom,cssStage:[2*w+16,h]},bounds,maskMethod:'Project actual evaluated finite core triangles at actual proper rotations. Union mask eroded2 output pixels at128,1 at32; true local collar masks use only joined ports, never fullcell/AABB alpha equality.'};
  };
 });
 const phases=[[0,0],[.25,0],[.5,0],[.75,0],[0,.25],[0,.5],[0,.75],[.25,.75]];
 for(const kind of ['direct-canonical-to-end','full-family-L'])for(const d of ['N','E','S','W'])for(const size of [128,32])for(let phase=0;phase<phases.length;phase++){
  const[rootPhase,panPhase]=phases[phase],id=`${kind}-${d}-${size}-phase${phase}`,dir=path.join(OUT,backend,id);fs.mkdirSync(dir,{recursive:true});
  const result=await page.evaluate(p=>window.runCase(p),{kind,d,size,rootPhase,panPhase});
  const media={};for(const[name,url]of Object.entries(result.out)){const p=path.join(dir,name+'.png');fs.writeFileSync(p,Buffer.from(url.split(',')[1],'base64'));media[name]=path.relative(O,p);}delete result.out;
  for(const[bg,color]of [['light','#f6f6f2'],['gray','#808080'],['dark','#181e26']]){await page.locator('#stage').evaluate((e,c)=>e.style.background=c,color);const p=path.join(dir,'actual-css-'+bg+'.png');await page.locator('#stage').screenshot({path:p});media['css-'+bg]=path.relative(O,p);}
  records.push({id,kind,d,size,phase,rootPhase,panPhase,viewport:page.viewportSize(),deviceScaleFactor:1,media,...result});
 }
 const executable=options.channel==='chromium'?chromium.executablePath():null;
 fs.writeFileSync(path.join(OUT,backend+'-results.json'),JSON.stringify({backend,browserVersion:browser.version(),launchOptions:options,chromiumDefaultExecutable:chromium.executablePath(),chromiumDefaultExecutableSHA256:sha(chromium.executablePath()),actualChildArgv:'Recorded by DEBUG=pw:browser in source/round-01-consumer-launch.log, including actual headless-shell executable',viewport:{width:1200,height:1200},DPR:1,errors,helperHashes:Object.fromEntries(['world-sprite-raster.js','sprite-layout.js','exact-used-raster-functions.js'].map(f=>[f,sha(path.join(B,'resources',f))])),records},null,2)+'\n');
 console.log(JSON.stringify({backend,version:browser.version(),transparentPairs:records.length,backgroundCSSCases:records.length*3,errors:errors.length}));
 }finally{await browser.close();}
}
fs.writeFileSync(path.join(OUT,'toolchain.json'),JSON.stringify({node:process.version,nodeExecutable:process.execPath,nodeSHA256:sha(process.execPath),platform:process.platform,arch:process.arch,playwrightVersion:require('@playwright/test/package.json').version,playwrightPackageSHA256:sha(require.resolve('@playwright/test/package.json')),playwrightCoreVersion:require('playwright-core/package.json').version,playwrightCorePackageSHA256:sha(require.resolve('playwright-core/package.json')),launchArgvLog:'source/round-01-consumer-launch.log',fullMatrix:'2 contexts × 4 directions × 2 sizes × 8 root/pan pairs × 3 backgrounds × 2 actual browser configurations =768 CSS cases;256 transparent native/independent pairs'},null,2)+'\n');
}finally{server.close();}})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
