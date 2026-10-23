import {createServer} from 'vite';
import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
const root=process.cwd(), P=path.resolve('prototypes/sushi-loop/assets/refinement/objects/portal-rim/reviews/preparation-v1');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const server=await createServer({configFile:false,root,server:{host:'127.0.0.1',port:0},logLevel:'error'});await server.listen();
const address=server.httpServer.address();const url=`http://127.0.0.1:${address.port}/${path.relative(root,P)}/consumer.html`;
const all=[];
try{for(const [mode,options] of [['full-chromium',{headless:true,channel:'chromium'}],['headless-shell',{headless:true}]]){
 const browser=await chromium.launch(options);const context=await browser.newContext({viewport:{width:840,height:780},deviceScaleFactor:1,recordVideo:{dir:path.join(P,'evidence',mode+'-video'),size:{width:840,height:780}}});const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(url);await page.waitForFunction(()=>window.ready===true);
 const data={mode,browserVersion:browser.version(),launchOptions:options,viewport:{width:840,height:780},deviceScaleFactor:1,fixtureURLPath:path.relative(root,P)+'/consumer.html',helperSHA256:{}};
 for(const n of ['world-sprite-raster.js','sprite-layout.js'])data.helperSHA256[n]=sha(await fs.readFile(path.join(P,'resources/consumer',n)));
 data.screenshots=[];for(const [bg,color] of [['light','#eeeeee'],['gray','#808080'],['dark','#161c29']]){await page.evaluate(color=>{window.setBG(color);window.drawAt(10/12)},color);const file=`evidence/consumer-${mode}-${bg}.png`;await page.screenshot({path:path.join(P,file),fullPage:true});data.screenshots.push({path:file,sha256:sha(await fs.readFile(path.join(P,file))),background:color,frame:10});}
 await page.evaluate(()=>window.setBG('#808080'));data.staticFrameRecords=[];
 for(const i of [0,3,6,9]){const records=await page.evaluate(i=>window.drawAt(i/12),i);data.staticFrameRecords.push({frame:i,records:records.map(r=>{const {canvasRGBA,...rest}=r;return {...rest,canvasPNG_SHA256:sha(Buffer.from(canvasRGBA.split(',')[1],'base64'))}})});}
 data.playback=await page.evaluate(()=>window.play());data.errors=errors;
 const video=page.video();await context.close();const videoPath=await video.path();data.video={path:path.relative(P,videoPath),sha256:sha(await fs.readFile(videoPath))};await browser.close();await fs.writeFile(path.join(P,`consumer-${mode}.json`),JSON.stringify(data,null,2)+'\n');all.push(data);console.log('PORTAL_CONSUMER_DONE',mode,browser.version(),data.playback.length);
}}finally{await server.close();}
await fs.writeFile(path.join(P,'consumer-summary.json'),JSON.stringify({preparationOnly:true,exactHelpers:true,modes:all.map(d=>({mode:d.mode,version:d.browserVersion,framesObserved:d.playback.length,errors:d.errors,video:d.video,screenshots:d.screenshots}))},null,2)+'\n');
