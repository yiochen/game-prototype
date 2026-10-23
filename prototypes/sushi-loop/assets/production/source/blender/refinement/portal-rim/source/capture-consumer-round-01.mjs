import {createServer} from 'vite';
import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const root=process.cwd(), S=path.dirname(fileURLToPath(import.meta.url)), P=path.resolve(S,'../candidates/round-01');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const server=await createServer({configFile:false,root,server:{host:'127.0.0.1',port:0},logLevel:'error'});await server.listen();
const address=server.httpServer.address();const url=`http://127.0.0.1:${address.port}/${path.relative(root,P)}/consumer.html`;
const all=[];
try{for(const [mode,options] of [['full-chromium',{headless:true,channel:'chromium'}],['headless-shell',{headless:true}]]){
 const browser=await chromium.launch(options);const context=await browser.newContext({viewport:{width:840,height:780},deviceScaleFactor:1,recordVideo:{dir:path.join(P,'evidence',mode+'-video'),size:{width:840,height:780}}});const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(url);await page.waitForFunction(()=>window.ready===true);
 const data={mode,browserVersion:browser.version(),launchOptions:options,viewport:{width:840,height:780},deviceScaleFactor:1,fixtureURLPath:path.relative(root,P)+'/consumer.html',helperSHA256:{}};
 for(const n of ['world-sprite-raster.js','sprite-layout.js'])data.helperSHA256[n]=sha(await fs.readFile(path.join(S,'round-01-resources/consumer',n)));
 data.browserProcessObserved=execFileSync('ps',['-axo','pid=,ppid=,command='],{encoding:'utf8'}).split('\n').filter(line=>{const m=line.trim().match(/^(\d+)\s+(\d+)\s+(.*)$/);return m && Number(m[2])===process.pid && /Chrome|chrome|headless/.test(m[3]);});
 data.screenshots=[];for(const [bg,color] of [['light','#eeeeee'],['gray','#808080'],['dark','#161c29']]){await page.evaluate(color=>{window.setBG(color);window.drawAt(10/12)},color);const file=`evidence/consumer-${mode}-${bg}.png`;await page.screenshot({path:path.join(P,file),fullPage:true});data.screenshots.push({path:file,sha256:sha(await fs.readFile(path.join(P,file))),background:color,frame:10});}
 await page.evaluate(()=>window.setBG('#808080'));data.staticFrameRecords=[];
 for(const i of Array.from({length:12},(_,i)=>i)){const records=await page.evaluate(i=>window.drawAt((i+.01)/12),i);const saved=[];for(const r of records){const {canvasRGBA,...rest}=r;const bytes=Buffer.from(canvasRGBA.split(',')[1],'base64');let canvasPath=null;if(r.displayScale===1){canvasPath=`evidence/canvases-${mode}/${r.direction}/${String(i).padStart(3,'0')}.png`;await fs.mkdir(path.dirname(path.join(P,canvasPath)),{recursive:true});await fs.writeFile(path.join(P,canvasPath),bytes);}saved.push({...rest,canvasPNG_SHA256:sha(bytes),canvasPath});}data.staticFrameRecords.push({frame:i,records:saved});}
 data.playback=await page.evaluate(()=>window.play());data.playbackTiming=await page.evaluate(()=>window.playbackTiming);data.errors=errors;
 const video=page.video();await context.close();const videoPath=await video.path();data.video={path:path.relative(P,videoPath),sha256:sha(await fs.readFile(videoPath))};await browser.close();await fs.writeFile(path.join(P,`consumer-${mode}.json`),JSON.stringify(data,null,2)+'\n');all.push(data);console.log('PORTAL_CONSUMER_DONE',mode,browser.version(),data.playback.length);
}}finally{await server.close();}
await fs.writeFile(path.join(P,'consumer-summary.json'),JSON.stringify({candidateRound:'round-01',exactHelpers:true,modes:all.map(d=>({mode:d.mode,version:d.browserVersion,framesObserved:d.playback.length,errors:d.errors,video:d.video,screenshots:d.screenshots}))},null,2)+'\n');
