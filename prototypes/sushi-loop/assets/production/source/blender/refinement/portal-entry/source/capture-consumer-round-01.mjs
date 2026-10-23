import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';import path from 'node:path';import {execFileSync} from 'node:child_process';
import crypto from 'node:crypto';
const here=path.dirname(new URL(import.meta.url).pathname),object=path.dirname(here),candidate=path.join(object,'candidates/round-01'),out=path.join(candidate,'consumer');
const python='/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const base='http://127.0.0.1:4217/resources/consumer/index.html';
const report={asset:'portal-entry',round:'round-01',nodeVersion:process.version,deviceScaleFactor:1,scope:'Same frozen current fixture/helpers and actual candidate original-layout atlases; native nearest compositor followed by whole CSS filtering. Utility fixture, not full React/Godot/device integration.',browserModes:[]};
function processes(){return execFileSync('ps',['-axo','pid=,ppid=,comm='],{encoding:'utf8'}).split('\n').map(x=>x.match(/^\s*(\d+)\s+(\d+)\s+(.+)$/)).filter(x=>x&&Number(x[2])===process.pid).map(x=>({pid:Number(x[1]),parentPid:Number(x[2]),executable:x[3]})).filter(x=>/Chrom|headless/i.test(x.executable));}
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
for(const [id,launch] of [['chromium',{headless:true,channel:'chromium'}],['shell',{headless:true}]]){
 const browser=await chromium.launch(launch),record={id,launch,version:browser.version(),actualProcess:processes(),screenshots:[],playback:[],errors:[]};
 for(const p of record.actualProcess)p.commandLine=execFileSync('ps',['-o','command=','-p',String(p.pid)],{encoding:'utf8'}).trim();
 const context=await browser.newContext({viewport:{width:800,height:1240},deviceScaleFactor:1}),page=await context.newPage();
 function listen(p){p.on('pageerror',e=>record.errors.push({type:'pageerror',message:e.message}));p.on('console',m=>{if(m.type()==='error')record.errors.push({type:'console',message:m.text()});});p.on('requestfailed',r=>record.errors.push({type:'requestfailed',url:r.url(),failure:r.failure()}));p.on('response',r=>{if(r.status()>=400)record.errors.push({type:'http',status:r.status(),url:r.url()});});}
 listen(page);
 for(const scale of [1,.5])for(const [bg,color] of [['light','#f3eee4'],['gray','#777777'],['dark','#132033']]){
  await page.setViewportSize({width:scale===1?800:390,height:scale===1?1240:844});await page.goto(`${base}?source=../../atlases&scale=${scale}&bg=${encodeURIComponent(color)}`);await page.waitForFunction(()=>window.ready);
  const file=`${id}-${scale===1?'logical':'phone'}-${bg}.png`;await page.screenshot({path:path.join(out,file),fullPage:true});
  record.screenshots.push({file,viewport:page.viewportSize(),dpr:await page.evaluate(()=>devicePixelRatio),evidence:await page.evaluate(()=>window.evidence)});
 }
 await page.goto(`${base}?source=../../atlases&scale=.5&mode=all&bg=%23777777`);await page.waitForFunction(()=>window.ready);
 const all=`${id}-all48.png`;await page.screenshot({path:path.join(out,all),fullPage:true});record.screenshots.push({file:all,viewport:page.viewportSize(),dpr:1,evidence:await page.evaluate(()=>window.evidence)});
 const canvases=await page.evaluate(()=>Array.from(document.querySelectorAll('main section')).map(cell=>{const label=cell.querySelector('div').textContent.split(' '),canvas=cell.querySelector('canvas');return {direction:label[0],frame:Number(label[2]),png:canvas.toDataURL('image/png'),smoothing:canvas.getContext('2d').imageSmoothingEnabled,plan:window.evidence.frameRecords.find(x=>x.direction===label[0]&&x.frame===Number(label[2])).plan};}));
 record.nativeCanvasReadback=JSON.parse(execFileSync(python,[path.join(here,'compare-canvas-round-01.py')],{input:JSON.stringify(canvases),encoding:'utf8',maxBuffer:30*1024*1024}));
 await context.close();
 const motion=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:1,recordVideo:{dir:out,size:{width:390,height:844}}}),play=await motion.newPage();listen(play);
 await play.goto(`${base}?source=../../atlases&scale=.5&mode=play&bg=%23777777`);await play.waitForFunction(()=>window.ready);await play.evaluate(()=>window.startPlayback());
 for(const t of [.02,.27,.52,.77,1.03,1.5]){
  await play.waitForFunction(t=>window.evidence.elapsed>=t,t);const file=`${id}-play-${String(t).replace('.','_')}.png`;await play.screenshot({path:path.join(out,file)});record.playback.push({file,requestedSeconds:t,evidence:await play.evaluate(()=>window.evidence)});
 }
 await play.waitForFunction(()=>window.evidence.complete);record.playbackFinal=await play.evaluate(()=>window.evidence);
 const video=play.video();await motion.close();await video.saveAs(path.join(out,`${id}-playback.webm`));record.video=`${id}-playback.webm`;await video.delete();
 record.playbackCoverage=Object.fromEntries(['N','E','S','W'].map(d=>[d,record.playbackFinal.frameRecords.filter(x=>x.direction===d).map(x=>x.frame)]));
 for(const d of ['N','E','S','W'])if(record.playbackCoverage[d].join(',')!=='0,1,2,3,4,5,6,7,8,9,10,11')throw new Error(`${id}/${d} playback coverage incomplete`);
 if(!record.playbackFinal.currentFrames.every(x=>x.frame===11)||record.playbackFinal.elapsed<1.9)throw new Error('Terminal hold not observed');
 record.videoSHA256=sha(await fs.readFile(path.join(out,record.video)));
 await browser.close();report.browserModes.push(record);
 console.log('PORTAL_CONSUMER_COMPLETE',id,record.version,'errors',record.errors.length,'actual',record.actualProcess.map(x=>x.executable));
}
const reportPath=path.join(candidate,'consumer-report.json');await fs.writeFile(reportPath,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
