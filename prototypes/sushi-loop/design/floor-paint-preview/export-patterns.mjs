import {chromium} from 'playwright';
import {mkdir,writeFile,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const dest=new URL('../../godot/assets/ui/floor-patterns/',import.meta.url);
await mkdir(dest,{recursive:true});
const browser=await chromium.launch();const page=await browser.newPage({viewport:{width:512,height:512},deviceScaleFactor:1});
await page.goto('http://127.0.0.1:4177/prototypes/sushi-loop/design/floor-paint-preview/?state=owned');
const hashes={};
for(const [id,name] of [['jade','Jade Check'],['terracotta','Terracotta'],['petal','Plum Petal'],['linen','Linen Stripe'],['checker','Harbor Check'],['blue-wave','Blue Wave'],['cream','Original Cream']]){
 await page.evaluate(name=>{document.getElementById('pattern-export')?.remove();const sample=document.querySelector(`[aria-label="${name}"] .pattern`).cloneNode(true);sample.id='pattern-export';Object.assign(sample.style,{position:'fixed',left:'0',top:'0',width:'256px',height:'256px',zIndex:99999});document.body.append(sample);},name);
 await page.locator('#pattern-export').screenshot({path:new URL(id+'.png',dest).pathname});
 hashes[id]=createHash('sha256').update(await readFile(new URL(id+'.png',dest))).digest('hex');
}
await browser.close();
await writeFile(new URL('pattern-export.json',import.meta.url),JSON.stringify({source:'approved floor-paint-preview CSS/production square floor textures',sourceCSSSHA256:createHash('sha256').update(await readFile(new URL('style.css',import.meta.url))).digest('hex'),size:[256,256],anchor:'square full-cell extent, same 2x2 repetition in native previews',hashes},null,2)+'\n');
