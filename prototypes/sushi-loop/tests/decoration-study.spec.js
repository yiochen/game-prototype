import { test, expect } from '@playwright/test';
for (const [width, height] of [[390,844],[844,390],[1440,1200]]) {
  test(`decoration layers and full-tile review at ${width}`, async ({page}, info) => {
    await page.setViewportSize({width,height});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto('/prototypes/sushi-loop/?ntl-drawer-state=hidden#decoration-study');
    const stage=page.locator('#prototype-stage');
    await expect(stage).toHaveClass(/frame--document/);
    const scene=stage.getByRole('img',{name:'Underwater decoration shoreline arrangement A',exact:true});
    await expect(scene).toHaveAttribute('data-height-ratio','0.7');
    await expect(scene.locator('[data-decor-layer="ground"] image')).toHaveCount(63);
    const count=await scene.locator('[data-decor-layer="objects"] image').count();expect(count).toBeGreaterThan(25);
    const links=await stage.locator('svg image').evaluateAll(es=>[...new Set(es.map(e=>e.getAttribute('href')))]);
    const decoded=await page.evaluate(async urls=>Promise.all(urls.map(src=>new Promise(resolve=>{const i=new Image();i.onload=()=>resolve([i.naturalWidth,i.naturalHeight]);i.onerror=()=>resolve([0,0]);i.src=src;}))),links);
    expect(decoded.every(([w,h])=>w===768&&h===3072)).toBe(true);
    const heightSelect=stage.getByLabel('Decoration height study',{exact:true});
    for(const [version,peakHeight,pngHeight] of [['original','0.91',1536],['moderate','1.60',1536],['bold','4.00',3072]]) {
      await heightSelect.selectOption(version);
      await expect(scene).toHaveAttribute('data-height-version',version);
      await expect(stage.locator('[data-decor-piece="spire"]')).toContainText(`${peakHeight} tiles high on screen`);
      const url=await scene.locator('[data-decor-layer="objects"] image').first().getAttribute('href');
      const size=await page.evaluate(src=>new Promise(resolve=>{const i=new Image();i.onload=()=>resolve([i.naturalWidth,i.naturalHeight]);i.onerror=()=>resolve([0,0]);i.src=src;}),url);
      expect(size).toEqual([768,pngHeight]);
      // The highest first-row peak must fit above the unchanged ground pitch.
      const viewBox=(await scene.getAttribute('viewBox')).split(' ').map(Number);
      expect(viewBox[1]).toBeLessThan(-Number(peakHeight)*128);
    }
    await stage.getByLabel('Decoration layer',{exact:true}).uncheck();
    await expect(scene.locator('[data-decor-layer="objects"]')).toHaveCount(0);
    await expect(scene.locator('[data-decor-layer="ground"] image')).toHaveCount(63);
    await stage.getByLabel('Decoration layer',{exact:true}).check();
    await stage.getByLabel('Tile grid & roots',{exact:true}).check();
    await expect(scene.locator('[data-decor-layer="guides"]')).toHaveCount(1);
    const before=await scene.locator('[data-decor-layer="objects"] image').first().getAttribute('href');
    await stage.getByRole('button',{name:'Arrangement A · switch',exact:true}).click();
    const second=stage.getByRole('img',{name:'Underwater decoration shoreline arrangement B',exact:true});
    expect(await second.locator('[data-decor-layer="objects"] image').first().getAttribute('href')).not.toBe(before);
    await stage.getByLabel('Decoration patch selection',{exact:true}).selectOption('coral');
    await stage.getByLabel('Vary facing',{exact:true}).uncheck();
    const patch=stage.getByRole('img',{name:'Three by three decoration coverage test',exact:true});
    await expect(patch.locator('[data-decor-layer="objects"] image')).toHaveCount(9);
    expect((await patch.locator('[data-decor-layer="objects"] image').evaluateAll(es=>[...new Set(es.map(e=>e.getAttribute('href')))])).length).toBe(1);
    for(const facing of ['E','N','W','S'])await stage.getByLabel('Decoration object facing',{exact:true}).selectOption(facing);
    await expect(stage.locator('[data-decor-piece]')).toHaveCount(5);
    await stage.getByLabel('Tile grid & roots',{exact:true}).uncheck();
    await second.screenshot({path:info.outputPath(`decor-shoreline-${width}.png`)});
    await stage.getByLabel('Decoration patch selection',{exact:true}).selectOption('mixed');
    await stage.getByLabel('Vary facing',{exact:true}).check();
    await patch.screenshot({path:info.outputPath(`decor-patch-${width}.png`)});
    for(const version of ['moderate','original']) {
      await heightSelect.selectOption(version);
      await patch.screenshot({path:info.outputPath(`decor-patch-${version}-${width}.png`)});
    }
    await heightSelect.selectOption('bold');
    expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width+1);
    expect(await page.evaluate(()=>[...document.querySelectorAll('body *')].filter(e=>/auto|scroll/.test(getComputedStyle(e).overflowY)&&e.scrollHeight>e.clientHeight+2&&e.getClientRects().length&&!e.matches('textarea,select')).map(e=>e.className))).toEqual([]);
    expect(errors).toEqual([]);
  });
}
