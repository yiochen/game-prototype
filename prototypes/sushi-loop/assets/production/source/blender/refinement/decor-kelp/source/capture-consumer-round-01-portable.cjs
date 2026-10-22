const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const cp=require('node:child_process');const spawnOriginal=cp.spawn;const spawns=[];cp.spawn=function(executable,args,options){spawns.push({executable,args});return spawnOriginal.call(this,executable,args,options);};
const privateRequire=require('node:module').createRequire(path.join(__dirname,'round-01-resources','node_modules','entry.cjs'));const {chromium}=privateRequire('@playwright/test');
const BASE=path.join(__dirname,'round-01-resources'),ROUND=path.join(__dirname,'../candidates/round-01'),OUT=path.join(ROUND,'consumer-v02');fs.mkdirSync(OUT,{recursive:true});
const src=fs.readFileSync(path.join(BASE,'world-sprite-raster.js'),'utf8');
const raster=src.slice(src.indexOf('export function worldRasterPlan'),src.indexOf('export function useWorldSpriteRaster')).replaceAll('export function','function');
const layout=fs.readFileSync(path.join(BASE,'sprite-layout.js'),'utf8');
const own=JSON.parse(fs.readFileSync(path.join(BASE,'catalog-object.json')));
const context=JSON.parse(fs.readFileSync(path.join(BASE,'consumer/context-records.json')));
const img=file=>'data:image/png;base64,'+fs.readFileSync(path.join(file.startsWith('idle-')?path.join(ROUND,'atlases'):path.join(BASE,'consumer'),file)).toString('base64');
(async()=>{const results=[];
for(const mode of ['full-chromium','headless-shell']){
 const spawnStart=spawns.length;const options={headless:true,...(mode==='full-chromium'?{channel:'chromium'}:{})};const browser=await chromium.launch(options);const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:2});
 await page.setContent('<html><head><style>body{margin:0;background:#e5e8e0;font:12px sans-serif}figure{margin:8px;padding:8px;background:#d8ddd7}canvas{display:block;image-rendering:auto}h3{margin:0 0 4px}</style></head><body></body></html>');
 await page.addScriptTag({content:raster});await page.addScriptTag({content:layout.replaceAll('export ','')});
 const data=await page.evaluate(async({own,context,images})=>{
  const atlases={};for(const [name,url]of Object.entries(images)){const image=new Image();image.src=url;await image.decode();atlases[name]=image;}
  const results=[];const make=(id,scale,phase,placements,bounds,background)=>{
   const sprites=orderPlacements(placements,[own,...context.map(c=>({id:c.object,kind:'actor',footprint:[1,1]}))]).map(p=>{
    const o=p.object==='decor-kelp'?own:context.find(c=>c.object===p.object);
    const frame=p.object==='decor-kelp'?spriteFrame(own,own.clips[0],p.direction||'S',phase/12):{rect:[0,0,atlases[p.object].width,atlases[p.object].height],frameSize:o.frameSize,root:o.root};
    const root=groundRoot(p,{...o,footprint:p.object==='decor-kelp'?own.footprint:[1,1]});return{rect:frame.rect,x:root[0]-frame.root[0]+.125,y:root[1]-frame.root[1]+.375,width:frame.frameSize[0],height:frame.frameSize[1],image:atlases[p.object==='decor-kelp'?p.direction||'S':p.object]};
   });const plan=worldRasterPlan(sprites,bounds),canvas=document.createElement('canvas');canvas.width=canvas.height=1;canvas.getContext('2d').imageSmoothingEnabled=true;paintWorldRaster(canvas,plan,sprites.map(s=>s.image));
   const actual=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;
   // Independent common-phase reference uses the whole group at integer offsets before one fractional translation.
   const positions=sprites.map(s=>[(s.x-plan.x)*plan.scale,(s.y-plan.y)*plan.scale]);const x0=Math.min(...positions.map(p=>p[0])),y0=Math.min(...positions.map(p=>p[1]));
   const layer=document.createElement('canvas');layer.width=Math.ceil(Math.max(...sprites.map((s,i)=>positions[i][0]-x0+s.width*plan.scale)));layer.height=Math.ceil(Math.max(...sprites.map((s,i)=>positions[i][1]-y0+s.height*plan.scale)));const lc=layer.getContext('2d');lc.imageSmoothingEnabled=false;
   sprites.forEach((s,i)=>lc.drawImage(s.image,...s.rect,Math.round(positions[i][0]-x0),Math.round(positions[i][1]-y0),s.width*plan.scale,s.height*plan.scale));
   const ref=document.createElement('canvas');ref.width=plan.width;ref.height=plan.height;ref.getContext('2d').imageSmoothingEnabled=false;ref.getContext('2d').drawImage(layer,x0,y0);const expected=ref.getContext('2d').getImageData(0,0,ref.width,ref.height).data;let diff=0;for(let i=0;i<actual.length;i++)if(actual[i]!==expected[i])diff++;
   canvas.style.width=plan.width/plan.scale*scale+'px';canvas.style.height=plan.height/plan.scale*scale+'px';const figure=document.createElement('figure');figure.style.background=background;figure.id=id;figure.innerHTML='<h3>'+id+' · scale '+scale+' · frame '+phase+'</h3>';figure.append(canvas);document.body.append(figure);
   return{id,scale,phase,canvas:[canvas.width,canvas.height],css:[parseFloat(canvas.style.width),parseFloat(canvas.style.height)],nativeCanvasDataURL:canvas.toDataURL('image/png'),imageSmoothingEnabled:canvas.getContext('2d').imageSmoothingEnabled,oracleDifferentChannels:diff,plan:{...plan,sprites:undefined}};
  };
  results.push(make('phone-detail',.570,0,[{object:'decor-kelp',direction:'S',x:0,y:0}],[-32,-352,192,480],'#d8ddd7'));
  results.push(make('thumbnail-control',.099,6,[{object:'decor-kelp',direction:'E',x:0,y:0}],[-32,-352,192,480],'#263e43'));
  results.push(make('registered-context',.570,0,[{object:'decor-kelp',direction:'S',x:0,y:1},...context.map(c=>({...c.placement}))],[-32,-320,896,896],'#168599'));
  return results;
 },{own,context,images:{S:img('idle-S.png'),E:img('idle-E.png'),N:img('idle-N.png'),W:img('idle-W.png'),...Object.fromEntries(context.map(c=>[c.object,img(c.crop)]))}});
 for(const fixture of data){fs.writeFileSync(path.join(OUT,mode+'-'+fixture.id+'-native-canvas.png'),Buffer.from(fixture.nativeCanvasDataURL.split(',')[1],'base64'));delete fixture.nativeCanvasDataURL;}for(const id of ['phone-detail','thumbnail-control','registered-context'])await page.locator('#'+id).screenshot({path:path.join(OUT,mode+'-'+id+'.png')});
 results.push({mode,version:browser.version(),actualBrowserProcesses:spawns.slice(spawnStart).filter(p=>p.args?.includes('--remote-debugging-pipe')),launchOptions:options,viewport:{width:390,height:844},deviceScaleFactor:2,fixtures:data});await browser.close();
}
fs.writeFileSync(path.join(OUT,'results.json'),JSON.stringify({node:process.version,nodeExecutable:process.execPath,helperHashes:Object.fromEntries(['world-sprite-raster.js','sprite-layout.js','catalog-object.json','consumer/context-records.json'].map(n=>[n,crypto.createHash('sha256').update(fs.readFileSync(path.join(BASE,n))).digest('hex')])),fixtureScriptSHA256:crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),playwright:privateRequire('@playwright/test/package.json').version,results},null,2)+'\n');
// Freeze exactly loaded JS modules plus package manifests, excluding browser/runtime trees.
const origin=path.dirname(privateRequire.resolve('playwright/package.json')),modulesRoot=path.dirname(origin),loaded=Object.keys(require.cache).filter(p=>p.startsWith(modulesRoot+path.sep));
const records=[];for(const p of loaded){const rel=path.relative(modulesRoot,p),dst=path.join(BASE,'node_modules',rel);fs.mkdirSync(path.dirname(dst),{recursive:true});if(path.resolve(p)!==path.resolve(dst))fs.copyFileSync(p,dst);records.push({path:'node_modules/'+rel,sha256:crypto.createHash('sha256').update(fs.readFileSync(dst)).digest('hex')});}
for(const p of ['@playwright/test/package.json','playwright/package.json','playwright-core/package.json','playwright-core/browsers.json']){const from=p==='playwright-core/browsers.json'?path.join(path.dirname(privateRequire.resolve('playwright-core/package.json')),'browsers.json'):privateRequire.resolve(p),dst=path.join(BASE,'node_modules',p);fs.mkdirSync(path.dirname(dst),{recursive:true});if(path.resolve(from)!==path.resolve(dst))fs.copyFileSync(from,dst);}
fs.writeFileSync(path.join(OUT,'node-module-closure.json'),JSON.stringify({method:'Actual CommonJS require.cache after both headless captures plus package manifests. Browser binary and Node runtime are external trusted environment, versions recorded; no application tree copied.',files:records},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1});
