const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const {chromium}=require('@playwright/test');
const O=path.resolve(__dirname,'..'),OUT=path.join(O,'candidates/round-01/consumer');fs.mkdirSync(OUT,{recursive:true});
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const server=http.createServer((req,res)=>{try{let f=path.join(O,decodeURIComponent(req.url.split('?')[0]));if(!f.startsWith(O+path.sep))throw Error('path');res.setHeader('Content-Type',f.endsWith('.js')?'text/javascript':f.endsWith('.json')?'application/json':f.endsWith('.png')?'image/png':'text/html');res.end(fs.readFileSync(f));}catch(e){res.statusCode=404;res.end('missing');}});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));try{
for(const [backend,options] of [['full-chromium',{headless:true,channel:'chromium'}],['headless-shell',{headless:true}]]){
 const browser=await chromium.launch(options);const records=[],errors=[];const page=await browser.newPage({viewport:{width:800,height:600},deviceScaleFactor:1});page.on('pageerror',e=>errors.push(String(e)));await page.goto(`http://127.0.0.1:${server.address().port}/source/resources/host.html`);
 await page.evaluate(async()=>{
  const R=await import('/source/resources/exact-used-raster-functions.js'),L=await import('/source/resources/sprite-layout.js');const geometry=await fetch('/candidates/round-01/evidence/context-geometry.json').then(r=>r.json());const load=url=>new Promise((yes,no)=>{const im=new Image;im.onload=()=>yes(im);im.onerror=()=>no(url);im.src=url;});const cache=new Map;
  const dirs=['S','E','N','W'],angles={S:0,E:Math.PI/2,N:Math.PI,W:-Math.PI/2};const bounds=[-352,-560,704,864],root=[352,560];
  const layouts={primary:[['middle',-1,0,0],['edge',0,0,0],['middle',1,0,0]],topology:[['middle',-1,0,0],['edge',0,0,0],['corner',1,0,0],['middle',1,1,1],['end',1,2,1]]};
  async function image(url){if(!cache.has(url))cache.set(url,await load(url));return cache.get(url);}
  function can(w,h){const c=document.createElement('canvas');c.width=w;c.height=h;return c;}
  function object(key){return {id:key,kind:'terrain',frameSize:[192,352],root:[96,248],sourceScale:2,footprint:[1,1],clips:[{id:'static',frames:1,fps:12,loop:false,directions:Object.fromEntries(dirs.map(d=>[d,{image:key==='edge'?`/candidates/round-01/frames/static/${d}/000.png`:`/candidates/round-01/evidence/sprites/${key}/${d}/000.png`,frameSize:[192,352],root:[96,248],rects:[[0,0,384,704]],sourceScale:2}]))}]};}
  const objects=['middle','edge','corner','end'].map(object);
  window.runCase=async({kind,d,size,rootPhase,panPhase})=>{
   const a=angles[d],quarter=dirs.indexOf(d),zoom=size/128;const layout=layouts[kind];const placements=layout.map(([key,x,y,q],i)=>{const rx=x*Math.cos(a)-y*Math.sin(a),ry=x*Math.sin(a)+y*Math.cos(a);return {id:'placement'+i,object:key,x:rx-.5,y:-ry-.5,direction:dirs[(quarter+q)%4],clip:'static'};});
   const sprites=L.orderPlacements(placements,objects).map(p=>{const o=objects.find(o=>o.id===p.object),f=L.spriteFrame(o,o.clips[0],p.direction,0),r=L.groundRoot(p,o,128);return {url:f.image,rect:f.rect,x:r[0]-f.root[0]+rootPhase,y:r[1]-f.root[1]+rootPhase,width:f.frameSize[0],height:f.frameSize[1],id:p.id,asset:p.object,direction:p.direction,root:r};});
   const native=[{url:`/candidates/round-01/evidence/native-${kind}-${d}.png`,rect:[0,0,1408,1728],x:-352+rootPhase,y:-560+rootPhase,width:704,height:864,id:'actual-native-context',root:[0,0]}];
   const stage=document.getElementById('stage');stage.replaceChildren();const w=Math.ceil(704*zoom)+24,h=Math.ceil(864*zoom)+24;stage.style.width=(w*2+16)+'px';stage.style.height=h+'px';const arrays={},out={},plans={},grid={};
   for(const [name,ss]of [['native',native],['independent',sprites]]){
    const plan=R.worldRasterPlan(ss,bounds),layer=can(plan.width,plan.height);R.paintWorldRaster(layer,plan,await Promise.all(ss.map(s=>image(s.url))));plans[name]=plan;
    const display=can(w,h),ctx=display.getContext('2d');ctx.imageSmoothingEnabled=true;ctx.drawImage(layer,12+(plan.x-bounds[0])*zoom+panPhase,12+(plan.y-bounds[1])*zoom+panPhase,plan.width/plan.scale*zoom,plan.height/plan.scale*zoom);out[name]=display.toDataURL('image/png');arrays[name]=ctx.getImageData(0,0,w,h).data;
    layer.style.width=(plan.width/plan.scale*zoom)+'px';layer.style.height=(plan.height/plan.scale*zoom)+'px';layer.style.left=((name==='native'?0:w+16)+12+(plan.x-bounds[0])*zoom+panPhase)+'px';layer.style.top=(12+(plan.y-bounds[1])*zoom+panPhase)+'px';stage.appendChild(layer);
   }
   // Source-specific finite native triangle masks: project actual core, erode outer coverage, retain local .08 joins.
   const mask=can(w,h),mc=mask.getContext('2d');mc.fillStyle='#fff';const join=can(w,h),jc=join.getContext('2d');jc.fillStyle='#fff';
   for(const [key,x,y,q]of layout){const src=geometry.assets[key],rot=a+q*Math.PI/2;const vv=src.vertices.map(v=>{const xx=x*Math.cos(a)-y*Math.sin(a)+v[0]*Math.cos(rot)-v[1]*Math.sin(rot),yy=x*Math.sin(a)+y*Math.cos(a)+v[0]*Math.sin(rot)+v[1]*Math.cos(rot);return [12+(352+xx*128+rootPhase)*zoom+panPhase,12+(560-yy*128-v[2]*89.6+rootPhase)*zoom+panPhase];});for(const t of src.triangles){mc.beginPath();t.forEach((i,k)=>mc[k?'lineTo':'moveTo'](...vv[i]));mc.closePath();mc.fill();if(kind==='primary'&&t.every(i=>Math.abs(src.vertices[i][0])>=.42-1e-6)){jc.beginPath();t.forEach((i,k)=>jc[k?'lineTo':'moveTo'](...vv[i]));jc.closePath();jc.fill();}}
   }
   const m=mc.getImageData(0,0,w,h).data,j=jc.getImageData(0,0,w,h).data,local=can(w,h),lc=local.getContext('2d'),lm=lc.createImageData(w,h),interior=can(w,h),ic=interior.getContext('2d'),im=ic.createImageData(w,h);let alphaDifferences=0,maxAlphaDelta=0,opaqueRGBDifferences=0,maxRGBDelta=0,trueInteriorPixels=0,nativeInteriorAlphaLoss=0,independentInteriorAlphaLoss=0,localJoinRGBDifferences=0,localJoinMaxRGBDelta=0;const n=arrays.native,b=arrays.independent;
   const rad=size===128?2:1;
   for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=(y*w+x)*4;let da=Math.abs(n[i+3]-b[i+3]);if(da){alphaDifferences++;maxAlphaDelta=Math.max(maxAlphaDelta,da);}let dr=Math.max(...[0,1,2].map(k=>Math.abs(n[i+k]-b[i+k])));if(n[i+3]===255&&b[i+3]===255&&dr){opaqueRGBDifferences++;maxRGBDelta=Math.max(maxRGBDelta,dr);}let inside=m[i+3]===255;
    if(inside)for(let dy=-rad;dy<=rad&&inside;dy++)for(let dx=-rad;dx<=rad;dx++){let xx=x+dx,yy=y+dy;if(xx<0||yy<0||xx>=w||yy>=h||m[(yy*w+xx)*4+3]!==255){inside=false;break;}}
    if(inside){trueInteriorPixels++;if(n[i+3]<255)nativeInteriorAlphaLoss++;if(b[i+3]<255)independentInteriorAlphaLoss++;im.data.set([n[i+3]<255?255:0,b[i+3]<255?80:140,b[i+3]<255?255:0,255],i);}
    if(j[i+3]===255&&inside){lm.data.set([dr*8,da*8,0,255],i);if(n[i+3]===255&&b[i+3]===255&&dr){localJoinRGBDifferences++;localJoinMaxRGBDelta=Math.max(localJoinMaxRGBDelta,dr);}}
   }
   lc.putImageData(lm,0,0);ic.putImageData(im,0,0);out['local-join-rgba-mask']=local.toDataURL('image/png');out['true-interior-alpha-mask']=interior.toDataURL('image/png');
   return {out,metrics:{alphaDifferences,maxAlphaDelta,opaqueRGBDifferences,maxRGBDelta,trueInteriorPixels,nativeInteriorAlphaLoss,independentInteriorAlphaLoss,localJoinRGBDifferences,localJoinMaxRGBDelta},plans,sprites,layout,display:{width:w,height:h,zoom,cssStage:[w*2+16,h]},bounds};
  };
 });
 for(const kind of ['primary','topology'])for(const d of ['N','E','S','W'])for(const size of [128,32]){
  const phases=kind==='primary'?[[0,0],[.25,0],[.5,0],[.75,0],[0,.25],[0,.5],[0,.75],[.25,.75]]:[[0,0],[.25,.75]];await page.setViewportSize(size===128?{width:800,height:600}:{width:390,height:844});
  for(let phase=0;phase<phases.length;phase++){
   const [rootPhase,panPhase]=phases[phase],id=`${kind}-${d}-${size}-phase${phase}`,casePath=path.join(OUT,backend,id);fs.mkdirSync(casePath,{recursive:true});const data=await page.evaluate(p=>window.runCase(p),{kind,d,size,rootPhase,panPhase});
   for(const [name,url]of Object.entries(data.out))fs.writeFileSync(path.join(casePath,name+'.png'),Buffer.from(url.split(',')[1],'base64'));delete data.out;
   if(phase===0||phase===phases.length-1)for(const [bg,color]of [['light','#f6f0e5'],['gray','#80878f'],['dark','#13243a']]){await page.locator('#stage').evaluate((s,c)=>s.style.background=c,color);await page.locator('#stage').screenshot({path:path.join(casePath,`actual-css-${bg}.png`)});}
   records.push({id,kind,d,size,rootPhase,panPhase,viewport:page.viewportSize(),deviceScaleFactor:1,...data});
  }
 }
 fs.writeFileSync(path.join(OUT,backend+'-results.json'),JSON.stringify({backend,browserVersion:browser.version(),options,executable:chromium.executablePath(),processArgs:browser.process?.()?.spawnargs??null,errors,helperHashes:Object.fromEntries(['world-sprite-raster.js','sprite-layout.js','exact-used-raster-functions.js'].map(f=>[f,sha(path.join(__dirname,'resources',f))])),records},null,2)+'\n');await browser.close();console.log(backend+' cases='+records.length+' errors='+errors.length);
}
}finally{server.close();}})().catch(e=>{console.error(e);process.exitCode=1;server.close();});
