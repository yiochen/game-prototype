import { test, expect } from '@playwright/test';
for (const [width,height] of [[390,844],[844,390],[1440,1200]]) {
  test(`concept decoration references, facings and composition at ${width}`, async ({page},info)=>{
    await page.setViewportSize({width,height});const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto('/prototypes/sushi-loop/?ntl-drawer-state=hidden#decoration-study');const stage=page.locator('#prototype-stage');
    await expect(stage).toHaveClass(/frame--document/);
    await expect(stage.getByLabel('Decoration contrast',{exact:true})).toHaveValue('strong');
    for(const [theme,title,rows,tall,short] of [['underwater','Underwater',9,'cobalt-crags','pink-coral'],['restaurant','Restaurant',8,'slate-bank','cone-curb']]){
      await stage.getByLabel('Decoration scene',{exact:true}).selectOption(theme);
      await expect(stage.getByRole('img',{name:`Approved ${theme} concept art`,exact:true})).toBeVisible();
      const scene=stage.getByRole('img',{name:`${title} concept decoration perimeter`,exact:true});
      const patch=stage.getByRole('img',{name:`${title} three by three decoration patch`,exact:true});
      const cards=stage.locator('[data-decor-piece]');await expect(cards).toHaveCount(6);
      const comparison=stage.locator('.decor-contrast-study');
      await expect(comparison.locator('.decor-contrast-grid svg')).toHaveCount(3);
      const objects=scene.locator('[data-decor-layer="objects"]');
      const objectSource=await objects.locator('image').first().getAttribute('href');
      const sceneBox=await scene.boundingBox();
      for(const [grade,filter] of [['original','none'],['strong','contrast(1.35)'],['punchier','contrast(1.18)']]){
        await stage.getByLabel('Decoration contrast',{exact:true}).selectOption(grade);
        await expect(objects).toHaveCSS('filter',filter);
        await expect(scene.locator('[data-decor-layer="ground"]')).toHaveCSS('filter','none');
        await expect(comparison.locator('[data-contrast-grade="original"] [data-decor-layer="objects"]')).toHaveCSS('filter','none');
        expect(await objects.locator('image').first().getAttribute('href')).toBe(objectSource);
        const after=await scene.boundingBox();expect(after.width).toBe(sceneBox.width);expect(after.height).toBe(sceneBox.height);
      }
      await stage.getByLabel('Decoration contrast',{exact:true}).selectOption('strong');
      const native=stage.locator('.decor-native-study');
      for(const facing of ['E','N','W','S'])await stage.getByLabel('Native contrast facing',{exact:true}).selectOption(facing);
      const pair=native.locator('.decor-native-grid svg');await expect(pair).toHaveCount(2);
      await expect(pair.nth(0).locator('[data-decor-layer="objects"]')).toHaveCSS('filter','contrast(1.35)');
      await expect(pair.nth(1).locator('[data-decor-layer="objects"]')).toHaveCSS('filter','none');
      expect(await pair.nth(0).getAttribute('viewBox')).toBe(await pair.nth(1).getAttribute('viewBox'));
      const nativeSource=await pair.nth(1).locator('[data-decor-layer="objects"] image').getAttribute('href');
      expect(nativeSource).toBe(await native.getByRole('link',{name:'Baked PNG ↗',exact:true}).getAttribute('href'));
      expect(nativeSource).not.toBe(await pair.nth(0).locator('[data-decor-layer="objects"] image').getAttribute('href'));
      await native.screenshot({path:info.outputPath(`${theme}-native135-${width}.png`)});
      await stage.getByLabel('Contrast comparison piece',{exact:true}).selectOption(short);
      await comparison.screenshot({path:info.outputPath(`${theme}-contrast-${width}.png`)});

      for(const card of await cards.all()){
        await expect(card.locator('.decor-directions svg')).toHaveCount(4);
        await expect(card.locator('.decor-crop svg')).toHaveCount(1);
        expect(Number.parseFloat(await card.locator('strong').textContent())).toBeLessThanOrEqual(3);
      }
      const tallCard=stage.locator(`[data-decor-piece="${tall}"]`);const shortCard=stage.locator(`[data-decor-piece="${short}"]`);
      await expect(tallCard).toContainText('35° upper view · square footing');await expect(shortCard).toContainText('70% square-grid oblique');
      const initial=await tallCard.getByRole('link',{name:'S · native capture ↗',exact:true}).getAttribute('href');
      const floor=await scene.locator('[data-decor-layer="ground"] image').first().getAttribute('href');
      await stage.getByLabel('Decoration projection',{exact:true}).selectOption('oblique');
      await expect(tallCard).toContainText('70% square-grid oblique');expect(await tallCard.getByRole('link',{name:'S · native capture ↗',exact:true}).getAttribute('href')).not.toBe(initial);
      expect(await scene.locator('[data-decor-layer="ground"] image').first().getAttribute('href')).toBe(floor);
      await stage.getByLabel('Decoration projection',{exact:true}).selectOption('mixed');
      await stage.getByLabel('Decoration layer',{exact:true}).uncheck();await expect(scene.locator('[data-decor-layer="objects"]')).toHaveCount(0);await expect(scene.locator('[data-decor-layer="ground"] image')).toHaveCount(7*rows);
      await stage.getByLabel('Decoration layer',{exact:true}).check();await stage.getByLabel('Tile grid & roots',{exact:true}).check();await expect(scene.locator('[data-decor-layer="guides"]')).toHaveCount(1);await stage.getByLabel('Tile grid & roots',{exact:true}).uncheck();
      await stage.getByLabel('Decoration patch selection',{exact:true}).selectOption(short);await stage.getByLabel('Vary facing',{exact:true}).uncheck();
      expect((await patch.locator('[data-decor-layer="objects"] image').evaluateAll(es=>new Set(es.map(e=>e.getAttribute('href'))).size))).toBe(1);
      await stage.getByLabel('Decoration patch selection',{exact:true}).selectOption('mixed');await stage.getByLabel('Vary facing',{exact:true}).check();
      const urls=await cards.locator('.decor-directions image').evaluateAll(es=>[...new Set(es.map(e=>e.getAttribute('href')))]);
      const sizes=await page.evaluate(async urls=>Promise.all(urls.map(src=>new Promise(resolve=>{const i=new Image();i.onload=()=>resolve([i.naturalWidth,i.naturalHeight]);i.onerror=()=>resolve([0,0]);i.src=src;}))),urls);
      expect(sizes.every(([w,h])=>w===768&&h===3072)).toBe(true);
      await patch.screenshot({path:info.outputPath(`${theme}-patch-${width}.png`)});await scene.screenshot({path:info.outputPath(`${theme}-perimeter-${width}.png`)});
      await shortCard.screenshot({path:info.outputPath(`${theme}-reference-card-${width}.png`)});
      expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width+1);
      expect(await page.evaluate(()=>[...document.querySelectorAll('body *')].filter(e=>/auto|scroll/.test(getComputedStyle(e).overflowY)&&e.scrollHeight>e.clientHeight+2&&e.getClientRects().length&&!e.matches('textarea,select')).map(e=>e.className))).toEqual([]);
    }
    expect(errors).toEqual([]);
  });
}
