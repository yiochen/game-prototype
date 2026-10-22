const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const {chromium}=require('@playwright/test');
const B=path.resolve(__dirname,'..'),O=path.resolve(B,'../..'),C=path.join(O,'candidates/round-01'),OUT=path.join(B,'evidence/consumer');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const server=http.createServer((req,res)=>{try{const u=decodeURIComponent(req.url.split('?')[0]);let f;if(u==='/') {res.setHeader('Content-Type','text/html');return res.end('<html><style>body{margin:0}#stage{position:relative;overflow:hidden}canvas{position:absolute}</style><div id="stage"></div></html>');}if(u.startsWith('/resources/'))f=path.join(B,u);else if(u.startsWith('/native/'))f=path.join(B,'evidence',u.slice(8));else if(u.startsWith('/candidate/'))f=path.join(C,u.slice(11));else throw Error(u);const ext=path.extname(f);res.setHeader('Content-Type',ext==='.js'?'text/javascript':ext==='.json'?'application/json':'image/png');res.end(fs.readFileSync(f));}catch(e){res.statusCode=404;res.end(String(e));}});
(async()=>{fs.mkdirSync(OUT,{recursive:true});await new Promise(r=>server.listen(0,'127.0.0.1',r));try{
for(const [backend,options] of [['full-chromium',{headless:true,channel:'chromium'}],['headless-shell',{headless:true}]]){
 const browser=await chromium.launch(options),page=await browser.newPage({viewport:{width:800,height:600},deviceScaleFactor:1}),errors=[],records=[];page.on('pageerror',e=>errors.push(String(e)));await page.goto(`http://127.0.0.1:${server.address().port}/`);
 await page.evaluate(async()=>{
  const R=await import('/resources/exact-used-raster-functions.js'),L=await import('/resources/sprite-layout.js'),G=await fetch('/resources/context-geometry.json').then(r=>r.json());
  const angles={N:Math.PI,E:Math.PI/2,S:0,W:-Math.PI/2},bounds=[-352,-560,704,864],cache=new Map;
  async function load(u){if(!cache.has(u))cache.set(u,await new Promise((y,n)=>{const im=new Image;im.onload=()=>y(im);im.onerror=()=>n(u);im.src=u;}));return cache.get(u);}
  const canvas=(w,h)=>Object.assign(document.createElement('canvas'),{width:w,height:h});
  const objects=['edge','middle'].map(id=>({id,kind:'terrain',footprint:[1,1],frameSize:[192,352],root:[96,248],sourceScale:2,clips:[{id:'static',frames:1,fps:12,loop:false,directions:Object.fromEntries(['N','E','S','W'].map(d=>[d,{image:id==='edge'?`/candidate/frames/static/${d}/000.png`:`/candidate/evidence/sprites/middle/${d}/000.png`,rects:[[0,0,384,704]],frameSize:[192,352],root:[96,248]}]))}]}));
  window.run=async({d,size,rootPhase,panPhase})=>{
   const a=angles[d],z=size/128,w=Math.ceil(704*z)+24,h=Math.ceil(864*z)+24;
   const placements=[['middle',-1],['edge',0],['middle',1]].map(([object,x],i)=>({id:String(i),object,x:x*Math.cos(a)-.5,y:-x*Math.sin(a)-.5,direction:d,clip:'static'}));
   const sprites=L.orderPlacements(placements,objects).map(p=>{const o=objects.find(q=>q.id===p.object),f=L.spriteFrame(o,o.clips[0],d),r=L.groundRoot(p,o);return {url:f.image,rect:f.rect,x:r[0]-96+rootPhase,y:r[1]-248+rootPhase,width:192,height:352,object:p.object,id:p.id,root:r};});
   const native=[{url:`/native/native-primary-${d}.png`,rect:[0,0,1408,1728],x:-352+rootPhase,y:-560+rootPhase,width:704,height:864}];const stage=document.getElementById('stage');stage.replaceChildren();stage.style.width=(w*2+16)+'px';stage.style.height=h+'px';const out={},arrays={},plans={};
   for(const [name,ss]of [['native',native],['independent',sprites]]){
    const plan=R.worldRasterPlan(ss,bounds),layer=canvas(plan.width,plan.height);R.paintWorldRaster(layer,plan,await Promise.all(ss.map(p=>load(p.url))));plans[name]=plan;
    const display=canvas(w,h),ctx=display.getContext('2d');ctx.imageSmoothingEnabled=true;ctx.drawImage(layer,12+(plan.x+352)*z+panPhase,12+(plan.y+560)*z+panPhase,plan.width/plan.scale*z,plan.height/plan.scale*z);out[name]=display.toDataURL();arrays[name]=ctx.getImageData(0,0,w,h).data;
    layer.style.width=plan.width/plan.scale*z+'px';layer.style.height=plan.height/plan.scale*z+'px';layer.style.left=((name==='native'?0:w+16)+12+(plan.x+352)*z+panPhase)+'px';layer.style.top=(12+(plan.y+560)*z+panPhase)+'px';stage.appendChild(layer);
   }
   const mask=canvas(w,h),mc=mask.getContext('2d'),join=canvas(w,h),jc=join.getContext('2d');mc.fillStyle=jc.fillStyle='#fff';
   for(const [key,x] of [['middle',-1],['edge',0],['middle',1]]){
    const g=G.assets[key],vs=g.vertices.map(v=>{const xx=x*Math.cos(a)+v[0]*Math.cos(a)-v[1]*Math.sin(a),yy=x*Math.sin(a)+v[0]*Math.sin(a)+v[1]*Math.cos(a);return [12+(352+xx*128+rootPhase)*z+panPhase,12+(560-yy*128-v[2]*89.6+rootPhase)*z+panPhase];});
    for(const t of g.triangles){mc.beginPath();t.forEach((i,k)=>mc[k?'lineTo':'moveTo'](...vs[i]));mc.closePath();mc.fill();if(t.every(i=>Math.abs(g.vertices[i][0])>=.42-1e-6)){jc.beginPath();t.forEach((i,k)=>jc[k?'lineTo':'moveTo'](...vs[i]));jc.closePath();jc.fill();}}
   }
   const maskA=mc.getImageData(0,0,w,h).data,joinA=jc.getImageData(0,0,w,h).data,n=arrays.native,b=arrays.independent,rad=size===128?2:1;const metrics={maxAlphaDelta:0,maxOpaqueRGBDelta:0,nativeInteriorAlphaLoss:0,independentInteriorAlphaLoss:0,trueInteriorPixels:0,localJoinMaxRGBDelta:0};
   for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const i=(y*w+x)*4,da=Math.abs(n[i+3]-b[i+3]),dr=Math.max(...[0,1,2].map(k=>Math.abs(n[i+k]-b[i+k])));metrics.maxAlphaDelta=Math.max(metrics.maxAlphaDelta,da);if(n[i+3]===255&&b[i+3]===255)metrics.maxOpaqueRGBDelta=Math.max(metrics.maxOpaqueRGBDelta,dr);
    let inside=maskA[i+3]===255;for(let dy=-rad;dy<=rad&&inside;dy++)for(let dx=-rad;dx<=rad;dx++){const xx=x+dx,yy=y+dy;if(xx<0||yy<0||xx>=w||yy>=h||maskA[(yy*w+xx)*4+3]!==255){inside=false;break;}}
    if(inside){metrics.trueInteriorPixels++;if(n[i+3]<255)metrics.nativeInteriorAlphaLoss++;if(b[i+3]<255)metrics.independentInteriorAlphaLoss++;if(joinA[i+3]===255&&n[i+3]===255&&b[i+3]===255)metrics.localJoinMaxRGBDelta=Math.max(metrics.localJoinMaxRGBDelta,dr);}
   }
   return {out,metrics,plans,sprites,display:[w,h],bounds};
  };
 });
 for(const d of ['N','E','S','W'])for(const size of [128,32])for(const [rootPhase,panPhase]of [[0,0],[.25,.75]]){
  await page.setViewportSize(size===128?{width:800,height:600}:{width:390,height:844});const id=`${d}-${size}-r${rootPhase}-p${panPhase}`,dir=path.join(OUT,backend,id);fs.mkdirSync(dir,{recursive:true});const result=await page.evaluate(p=>window.run(p),{d,size,rootPhase,panPhase});
  for(const [name,url]of Object.entries(result.out))fs.writeFileSync(path.join(dir,name+'.png'),Buffer.from(url.split(',')[1],'base64'));delete result.out;
  for(const [name,color] of [['light','#f6f0e5'],['gray','#80878f'],['dark','#13243a']]){await page.locator('#stage').evaluate((s,c)=>s.style.background=c,color);await page.locator('#stage').screenshot({path:path.join(dir,'css-'+name+'.png')});}
  records.push({id,d,size,rootPhase,panPhase,viewport:page.viewportSize(),DPR:1,...result});
 }
 const report={candidatePacketSHA256:'270d330ded27fa71bc0b1484698e5e75ef671ce5d45bde767d66af559a4ad453',backend,options,browserVersion:browser.version(),node:process.version,playwright:require('@playwright/test/package.json').version,helperHashes:Object.fromEntries(['world-sprite-raster.js','sprite-layout.js','exact-used-raster-functions.js'].map(f=>[f,sha(path.join(B,'resources',f))])),errors,records};fs.writeFileSync(path.join(OUT,backend+'-report.json'),JSON.stringify(report,null,2)+'\n');await browser.close();console.log(backend+' '+records.length+' cases, errors '+errors.length);
}
}finally{server.close();}})().catch(e=>{console.error(e);process.exitCode=1;server.close();});
