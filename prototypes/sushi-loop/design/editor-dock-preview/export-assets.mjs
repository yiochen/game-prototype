import {chromium} from '@playwright/test';
import {createHash} from 'node:crypto';
import {readFile,writeFile,mkdir,copyFile} from 'node:fs/promises';
import {dirname,resolve,relative} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const here=dirname(fileURLToPath(import.meta.url));
const game=resolve(here,'../..');
const repository=resolve(game,'../..');
const output=resolve(game,'assets/ui/editor/html-export-v1');
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const gutter=16;
const specs=[
  {id:'board',kind:'board',width:720,height:291,radius:18,slice:[36,36,36,18]},
  {id:'tab-normal',kind:'tab',width:208,radius:12,slice:[30,30,30,36]},
  {id:'tab-pressed',kind:'tab',width:208,radius:12,slice:[30,30,30,36],pressed:true},
  {id:'tab-selected',kind:'tab',width:208,radius:22,slice:[40,40,40,18],selected:true},
  {id:'shop-normal',kind:'shop',width:148,radius:30,slice:[50,0,50,0],horizontalOnly:true},
  {id:'shop-pressed',kind:'shop',width:148,radius:30,slice:[50,0,50,0],horizontalOnly:true,pressed:true},
  {id:'hud-cream-normal',kind:'hud',width:208,radius:35,slice:[52,0,52,0],horizontalOnly:true},
  {id:'hud-cream-pressed',kind:'hud',width:208,radius:35,slice:[52,0,52,0],horizontalOnly:true,pressed:true},
  {id:'hud-live-normal',kind:'hud',width:147,radius:35,slice:[52,0,52,0],horizontalOnly:true,live:true},
  {id:'hud-live-pressed',kind:'hud',width:147,radius:35,slice:[52,0,52,0],horizontalOnly:true,live:true,pressed:true},
  {id:'quantity-badge',kind:'badge',width:42,height:42},
  {id:'coin-emblem',kind:'coin',width:54,height:54},
  {id:'panel-maple',kind:'panel',width:480,height:320,radius:20,slice:[38,38,38,38]},
  {id:'tab-backdrop',kind:'backdrop',width:720,height:78},
  {id:'footer-waves',kind:'waves',width:664,height:34},
  ...['people','layout','floor'].map(category=>({id:`connected-${category}`,kind:'connected',category,width:720,height:369})),
  ...['people','layout','floor','shop','back','edit','play','star'].map(icon=>({id:`icon-${icon}`,kind:'icon',icon,width:32,height:32})),
];
const browser=await chromium.launch();
try{
  const source=await browser.newPage({viewport:{width:720,height:1280}});
  await source.goto(pathToFileURL(resolve(here,'screens/layout.phone.html')).href);
  await source.waitForSelector('html[data-ready=true]');
  await source.evaluate(()=>document.fonts.ready);
  const templates=await source.evaluate(()=>{
    const svg=selector=>document.querySelector(selector).outerHTML;
    return {
      dock:document.querySelector('.dock').outerHTML,
      coin:document.querySelector('.coin-art').outerHTML,
      icons:{people:svg('#tab-people .icon'),layout:svg('#tab-layout .icon'),floor:svg('#tab-floor .icon'),shop:svg('.shop-action .icon'),back:svg('.back .icon'),edit:svg('.hud-editing .icon'),play:svg('.hud-live .icon'),star:svg('.coin-art .icon')},
    };
  });
  const css=await readFile(resolve(here,'shared.css'),'utf8');
  const manifest={version:1,logical_canvas:[720,1280],scales:[1,2],transparent_gutter:gutter,color_space:'sRGB',alpha:'RGBA, transparent gutters',dynamic_text_baked:false,
    source:{renderer:'Playwright Chromium',browser_version:browser.version(),files:{}},assets:{},textures:{},
    text:{font:'fonts/Nunito.ttf',ink:'#592c10',cream:'#fff3db',hud_ink:'#123f62',category_font_size:26,item_font_size:25,quantity_font_size:24},
    notes:['Use connected-* at uniform scale for an exact selected-tab/board seam.','Individual surfaces include transparent shadow gutters. Face rects and nine-patch margins are in each PNG variant.','Tile the nine-patch center to preserve grain proportions; do not stretch a whole PNG.','1x variants map to logical units. 2x variants have every coordinate doubled; scale the entire UI consistently.','Labels, quantities, interactive hit targets and focus rings remain native Godot controls.']};
  for(const name of ['shared.css','app.js','export-stage.html','export-assets.mjs','assets/wood-grain.png','assets/waves.png']){
    manifest.source.files[relative(repository,resolve(here,name))]=hash(await readFile(resolve(here,name)));
  }
  await mkdir(output,{recursive:true});
  for(const scale of manifest.scales){
    const context=await browser.newContext({viewport:{width:1024,height:1400},deviceScaleFactor:scale});
    const page=await context.newPage();
    const errors=[];page.on('pageerror',error=>errors.push(error.message));
    await page.goto(pathToFileURL(resolve(here,'export-stage.html')).href);
    // Reuse authored :active declarations without synthesizing browser input.
    await page.evaluate(css=>{
      const sheet=new CSSStyleSheet();sheet.replaceSync(css);
      const active=[];
      const visit=rules=>{for(const rule of rules){if(rule.selectorText?.includes(':active'))active.push(`${rule.selectorText.replaceAll(':active','.is-export-pressed')}{${rule.style.cssText}}`);if(rule.cssRules)visit(rule.cssRules);}};
      visit(sheet.cssRules);
      const style=document.createElement('style');style.textContent=active.join('\n')+'\n.export-composite .category-navigation::before{display:none}.export-composite .board{bottom:0}.export-composite .icon,.export-composite .caption{display:none}';document.head.append(style);
    },css);
    await mkdir(resolve(output,`png/${scale}x`),{recursive:true});
    for(const spec of specs){
      const geometry=await page.evaluate(async({spec,templates,gutter})=>{
        const stage=document.querySelector('#stage');stage.replaceChildren();
        const create=(tag,className)=>{const el=document.createElement(tag);el.className=className;stage.append(el);return el;};
        let host,target;
        if(spec.kind==='tab'){
          host=create('button','tab');host.setAttribute('aria-selected',String(!!spec.selected));host.innerHTML='<span class="surface"></span>';target=host.firstElementChild;
          target.style.setProperty('--wood-position',spec.selected?'0px 78px':'0px 0px');
        }else if(spec.kind==='shop'){
          host=create('button','shop-action');host.innerHTML='<span class="surface"></span>';target=host.firstElementChild;
        }else if(spec.kind==='hud'){
          host=create('button',`hud-mode ${spec.live?'hud-live':'hud-editing'}`);host.innerHTML='<span class="hud-surface"></span>';target=host.firstElementChild;
        }else if(spec.kind==='board')host=target=create('div','board');
        else if(spec.kind==='panel')host=target=create('section','shop-view');
        else if(spec.kind==='badge')host=target=create('span','quantity');
        else if(spec.kind==='backdrop')host=target=create('nav','category-navigation');
        else if(spec.kind==='waves'){host=target=create('div','wave-window');host.innerHTML='<div class="waves"></div>';}
        else if(spec.kind==='coin'){stage.innerHTML=templates.coin;host=target=stage.firstElementChild;}
        else if(spec.kind==='icon'){stage.innerHTML=templates.icons[spec.icon];host=target=stage.firstElementChild;host.style.color='#ffffff';}
        else if(spec.kind==='connected'){
          stage.innerHTML=templates.dock;host=target=stage.firstElementChild;host.classList.add('export-composite');
          host.querySelector('.inventory').remove();host.querySelector('.wave-window').remove();
          for(const tab of host.querySelectorAll('.tab')){
            const selected=tab.dataset.category===spec.category;tab.setAttribute('aria-selected',String(selected));tab.style.visibility=selected?'visible':'hidden';
            tab.querySelectorAll('.icon,.caption').forEach(el=>el.remove());
          }
          host.querySelector('.shop-action').style.visibility='hidden';
        }
        Object.assign(host.style,{position:'absolute',left:`${gutter}px`,top:`${gutter}px`,right:'auto',bottom:'auto',width:`${spec.width}px`,margin:'0',padding:'0'});
        if(spec.height)host.style.height=`${spec.height}px`;
        if(spec.kind==='connected'){
          const board=host.querySelector('.board').getBoundingClientRect();
          for(const face of host.querySelectorAll('.surface')){const b=face.getBoundingClientRect();face.style.setProperty('--wood-size','720px auto');face.style.setProperty('--wood-position',`${board.left-b.left}px ${board.top-b.top}px`);}
        }
        await document.fonts.ready;
        const urls=new Set();for(const el of stage.querySelectorAll('*'))for(const m of getComputedStyle(el).backgroundImage.matchAll(/url\(["']?(.*?)["']?\)/g))urls.add(m[1]);
        await Promise.all([...urls].map(url=>new Promise((resolve,reject)=>{const img=new Image();img.onload=resolve;img.onerror=()=>reject(new Error(url));img.src=url;})));
        const b=target.getBoundingClientRect(),control=host.getBoundingClientRect();
        const x=Math.floor(b.x)-gutter,y=Math.floor(b.y)-gutter;
        const width=Math.ceil(b.right)-x+gutter,height=Math.ceil(b.bottom)-y+gutter;
        if(spec.pressed)host.classList.add('is-export-pressed');
        return {clip:{x,y,width,height},face_rect:[b.x-x,b.y-y,b.width,b.height],face_offset_in_control:[b.x-control.x,b.y-control.y],control_size:[spec.width,spec.height||78],radius:spec.radius||0};
      },{spec,templates,gutter});
      const bytes=await page.screenshot({clip:geometry.clip,omitBackground:true,animations:'disabled'});
      const path=`png/${scale}x/${spec.id}.png`;
      await writeFile(resolve(output,path),bytes);
      const size=[bytes.readUInt32BE(16),bytes.readUInt32BE(20)];
      if(size[0]!==geometry.clip.width*scale||size[1]!==geometry.clip.height*scale)throw new Error(`Unexpected PNG dimensions: ${spec.id}`);
      if(!manifest.assets[spec.id]){
        const drawOffset=geometry.face_offset_in_control.map((n,i)=>n-geometry.face_rect[i]);
        const expand=[-drawOffset[0],-drawOffset[1],geometry.clip.width+drawOffset[0]-geometry.control_size[0],geometry.clip.height+drawOffset[1]-geometry.control_size[1]];
        manifest.assets[spec.id]={kind:spec.kind,logical_size:[geometry.clip.width,geometry.clip.height],face_rect:geometry.face_rect,face_offset_in_control:geometry.face_offset_in_control,control_size:geometry.control_size,draw_offset:drawOffset,stylebox_expand_margins_ltrb:expand,pressed_offset_baked:spec.pressed?[0,2]:[0,0],resize:spec.horizontalOnly?'horizontal_only_tile_center':spec.slice?'nine_patch_tile_center':'uniform_only',variants:{}};
      }
      const variant={path,size,face_rect:geometry.face_rect.map(n=>n*scale),sha256:hash(bytes)};
      if(spec.slice)variant.nine_patch_margins_ltrb=spec.slice.map(n=>n*scale);
      manifest.assets[spec.id].variants[`${scale}x`]=variant;
    }
    if(errors.length)throw new Error(errors.join('\n'));
    await context.close();
  }
  for(const name of ['wood-grain','waves']){
    const path=`textures/${name}.png`;await mkdir(resolve(output,'textures'),{recursive:true});await copyFile(resolve(here,`assets/${name}.png`),resolve(output,path));
    manifest.textures[name]={path,sha256:hash(await readFile(resolve(output,path)))};
  }
  await mkdir(resolve(output,'fonts'),{recursive:true});
  for(const name of ['Nunito.ttf','Nunito-OFL.txt'])await copyFile(resolve(game,`godot/assets/fonts/${name}`),resolve(output,`fonts/${name}`));
  await mkdir(resolve(output,'svg'),{recursive:true});
  for(const [name,svg] of Object.entries(templates.icons))await writeFile(resolve(output,`svg/icon-${name}.svg`),svg.replace('<svg ','<svg xmlns="http://www.w3.org/2000/svg" '));
  await copyFile(resolve(here,'export-readme.md'),resolve(output,'README.md'));
  await writeFile(resolve(output,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
  console.log(`Exported ${specs.length} transparent assets at 1x and 2x to ${relative(repository,output)}`);
}finally{await browser.close();}
