import {test,expect} from '@playwright/test';
import {mkdir} from 'node:fs/promises';
test.use({video:process.env.RECORD_BALLOONS?'on':'off'});
async function open(page,seed='paper-test') {
  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.goto(`/prototypes/cloudtop-hotel/?seed=${seed}`);
  await expect(page.locator('#world')).toHaveAttribute('data-ready','true');
  await page.locator('#lobby-play').click();
}
async function waitStage(page,stage) {
  await page.waitForFunction(stage=>JSON.parse(document.querySelector('#world canvas').dataset.balloonJourneys||'[]').some(j=>j.stage===stage),stage);
}
async function shot(page,name) {await mkdir('artifacts/balloons',{recursive:true});await page.screenshot({path:`artifacts/balloons/${name}.png`});}

test('new neighborhoods launch distinct balloons and credit the dock on arrival',async({page})=>{
  await page.setViewportSize({width:1280,height:720}); await open(page);
  await page.evaluate(()=>{
    window.balloonFrames=[];
    const canvas=document.querySelector('#world canvas');
    window.balloonObserver=new MutationObserver(()=>{
      const journeys=JSON.parse(canvas.dataset.balloonJourneys||'[]');
      if(journeys.length) window.balloonFrames.push({time:performance.now(),journeys,counts:Object.fromEntries([...document.querySelectorAll('.dock-chip')].map(el=>[el.dataset.suit,Number(el.querySelector('.dock-count').textContent)]))});
    });
    window.balloonObserver.observe(canvas,{attributes:true,attributeFilter:['data-balloon-journeys']});
  });
  await page.locator('[data-offer-index="0"]').click();
  await waitStage(page,'emerging'); await shot(page,'neighborhood-launch');
  await expect(page.locator('.dock-count')).toHaveText(['0','0','0']);
  await waitStage(page,'rising'); await shot(page,'balloons-rising');
  await waitStage(page,'docking');
  await expect(page.locator('#world')).toHaveAttribute('data-state','picking',{timeout:6000});
  await expect(page.locator('.dock-count')).toHaveText(['1','1','1']);
  const frames=await page.evaluate(()=>{window.balloonObserver.disconnect();return window.balloonFrames;});
  const launched=new Map(frames.flatMap(f=>f.journeys).map(j=>[j.id,j]));
  expect([...launched.values()].map(j=>j.floor).sort()).toEqual([0,1,2]);
  expect(new Set([...launched.values()].map(j=>Math.round(j.source.y))).size).toBe(3);
  expect(frames.at(-1).time-frames[0].time).toBeGreaterThan(2200);
  for(const frame of frames) for(const j of frame.journeys) {
    if(j.stage!=='arrived') expect(frame.counts[j.suit]).toBe(0);
    if(j.stage==='docking') expect(Math.hypot(j.x-j.dock.x,j.y-j.dock.y)).toBeLessThan(50);
  }
});

test('phone flights reattach on resize, reduced motion settles, and replay cancels arrivals',async({page})=>{
  await page.setViewportSize({width:390,height:844}); await open(page);
  await page.locator('[data-offer-index="0"]').click(); await waitStage(page,'hovering');
  await shot(page,'phone-neighborhood');
  await page.setViewportSize({width:844,height:390}); await waitStage(page,'rising');
  const positions=await page.locator('#world canvas').evaluate(canvas=>JSON.parse(canvas.dataset.balloonJourneys));
  for(const j of positions) {expect(j.x-j.width/2).toBeGreaterThanOrEqual(0);expect(j.x+j.width/2).toBeLessThanOrEqual(844);}
  await page.emulateMedia({reducedMotion:'reduce'});
  await expect(page.locator('#world')).toHaveAttribute('data-state','picking');
  await expect(page.locator('.dock-count')).toHaveText(['1','1','1']);
  await expect(page.locator('#world canvas')).toHaveAttribute('data-balloon-journeys','[]');
  await page.locator('#menu-open').click(); await page.locator('#replay').click();
  await page.emulateMedia({reducedMotion:'no-preference'});
  await page.locator('[data-offer-index="0"]').click(); await waitStage(page,'rising');
  await page.locator('#menu-open').click(); await page.locator('#replay').click();
  await expect(page.locator('.dock-count')).toHaveText(['0','0','0']);
  await page.waitForTimeout(2800);
  await expect(page.locator('.dock-count')).toHaveText(['0','0','0']);
  await expect(page.locator('#height')).toHaveText('0');
  await expect(page.locator('#world canvas')).toHaveAttribute('data-balloon-journeys','[]');
});
