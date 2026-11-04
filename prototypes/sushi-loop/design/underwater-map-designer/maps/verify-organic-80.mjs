import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
const base=(process.env.TEST_URL||'http://127.0.0.1:4177').replace(/\/$/,'');
const path='/prototypes/sushi-loop/design/underwater-map-designer/',key='sushi-loop-underwater-map-designer-v1';
const mapPath=new URL('./turquoise-passage-organic-80.json',import.meta.url),map=JSON.parse(readFileSync(mapPath,'utf8'));
const out=new URL(process.env.REVIEW_OUTPUT||'../../../review/21/organic-80/',import.meta.url);mkdirSync(out,{recursive:true});
const browser=await chromium.launch(),errors=[],reports=[];let downloadURL;
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const stored=page=>page.evaluate(k=>JSON.parse(localStorage.getItem(k)).document,key);
const saved=page=>page.waitForFunction(()=>document.querySelector('.save-state')?.textContent.startsWith('Saved locally'));
try{
 for(const [name,width,height] of [['desktop',1440,1000],['phone',390,844],['narrow',320,720],['landscape',844,390]]){
  const ctx=await browser.newContext({viewport:{width,height},acceptDownloads:true}),page=await ctx.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+path);await saved(page);const original=await stored(page);
  // File import exercises exactly the same public path the user's downloaded file uses.
  await page.locator('input[type=file]').setInputFiles(mapPath.pathname);await wait(300);await saved(page);assert.deepEqual(await stored(page),map);
  assert.equal(await page.locator('.document-name input').inputValue(),map.name);
  const bottom=await page.locator('.map-scroll').evaluate(v=>Math.abs(v.scrollTop-(v.scrollHeight-v.clientHeight))<1);assert.equal(bottom,true);
  const dlPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Export JSON',exact:true}).click();const dl=await dlPromise;assert.deepEqual(JSON.parse(readFileSync(await dl.path(),'utf8')),map,'export reproduces imported generation');
  await page.getByRole('button',{name:'Undo',exact:true}).click();await wait(300);assert.deepEqual(await stored(page),original,'import Undo restores the exact existing map');
  // Preset link only opens the existing creation dialog; cancel leaves the draft intact.
  await page.goto(base+path+'?preset=organic-80');await page.getByRole('dialog').waitFor();await page.getByRole('button',{name:'Cancel',exact:true}).click();await saved(page);assert.deepEqual(await stored(page),original,'canceling a preset preserves the existing draft');assert.equal(new URL(page.url()).searchParams.has('preset'),false);
  await page.goto(base+path+'?preset=organic-80');const modal=page.getByRole('dialog');await modal.waitFor();await wait(150);await page.screenshot({path:new URL(`preset-dialog-${name}.png`,out).pathname});
  const link=page.getByRole('link',{name:'Download JSON',exact:true});downloadURL=new URL(await link.getAttribute('href'),page.url()).href;
  const presetDownload=page.waitForEvent('download');await link.click();const downloaded=await presetDownload;assert.deepEqual(JSON.parse(readFileSync(await downloaded.path(),'utf8')),map,'preset download is the exact importable JSON');
  await modal.getByRole('button',{name:'Create map',exact:true}).click();await wait(300);await saved(page);assert.deepEqual(await stored(page),map,'preset loads generated content');assert.equal(new URL(page.url()).searchParams.has('preset'),false);
  await page.screenshot({path:new URL(`loaded-opening-${name}.png`,out).pathname});
  const cell=await page.evaluate(k=>JSON.parse(localStorage.getItem(k)).view.cell,key),vp=page.locator('.map-scroll');
  for(const row of [26,37,53,71,80]){await vp.evaluate((v,{row,cell})=>{v.scrollTop=40+(80-row)*cell-v.clientHeight*.4;},{row,cell});await wait(120);if(name==='desktop'||row===53)await page.screenshot({path:new URL(`${name}-row-${row}.png`,out).pathname});}
  await page.reload();await saved(page);assert.equal(await page.getByRole('dialog').count(),0,'reload resumes the map without reopening the preset dialog');assert.deepEqual(await stored(page),map,'generated content autosaves and restores');
  await page.getByRole('button',{name:'New map',exact:true}).click();await page.getByRole('dialog').getByLabel('Starting point',{exact:true}).selectOption('organic');assert.equal(await page.getByRole('dialog').getByLabel('Map rows',{exact:true}).inputValue(),'80');assert.equal(await page.getByRole('dialog').getByLabel('Map rows',{exact:true}).isDisabled(),true);await page.getByRole('button',{name:'Cancel',exact:true}).click();
  const overflow=await page.evaluate(()=>document.body.scrollWidth>innerWidth);assert.equal(overflow,false);reports.push({name,width,height,checks:['exact JSON file import','JSON export equality','Undo previous map','preset cancel preserves draft','preset download equality','preset load','bottom start','persistent reload','New map option','contained layout']});await ctx.close();console.log(`Verified Organic 80: ${name}`);
 }
 assert.deepEqual(errors,[]);writeFileSync(new URL('browser-verification.json',out),JSON.stringify({base,presetURL:base+path+'?preset=organic-80',downloadURL,reports},null,2)+'\n');console.log('Organic 80 import, download and preset checks passed.');
}finally{await browser.close();}
