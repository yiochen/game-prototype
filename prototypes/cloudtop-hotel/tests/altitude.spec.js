import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { replayRun, SCORE_VERSION } from '../score-rules.js';
import { skyAtHeight } from '../altitude.js';

// A legal 178-floor game; only the normal saved-run interface is used.
const run = { seed: 'sky-2', moves: [[0,null],[0,'bunny'],[1,null],[0,null],[0,null],[0,null],[0,null],[1,null],[1,null],[1,null],[0,null],[1,null],[1,'bunny'],[1,null],[1,null],[0,null],[1,null],[0,null],[2,null],[0,null]] };
async function setup(page, reduced) {
  await page.emulateMedia({ reducedMotion: reduced ? 'reduce' : 'no-preference' });
  await page.addInitScript(({ run, version }) => {
    const count = Number(new URL(location.href).searchParams.get('testMoves') || 0);
    localStorage.setItem('cloudtop-guestbook-v1', JSON.stringify({ runs: [], active: { id: 'altitude-test', version, seed: run.seed, moves: run.moves.slice(0, count) }, sound: false }));
  }, { run, version: SCORE_VERSION });
}
async function resume(page, moves) {
  await page.goto(`/prototypes/cloudtop-hotel/?testMoves=${moves}`);
  await expect(page.locator('#world')).toHaveAttribute('data-ready', 'true');
  await page.locator('#lobby-resume').click();
  await expect(page.locator('body')).toHaveAttribute('data-screen', 'game');
}
async function shot(page, name) {
  await mkdir('artifacts/altitude', { recursive: true });
  await page.screenshot({ path: `artifacts/altitude/${name}.png` });
}

test('seven altitude stages survive saved-run resume and stay fixed during camera changes', async ({ page }) => {
  const errors = []; page.on('pageerror', error => errors.push(error.message));
  await setup(page, true); await page.setViewportSize({ width: 1440, height: 900 });
  for (const moves of [0, 10, 12, 13, 16, 18, 19]) {
    const height = replayRun(run.seed, run.moves.slice(0, moves), false).links.length;
    await resume(page, moves);
    const sky = page.locator('.sky-backdrop');
    await expect(sky).toHaveAttribute('data-height', String(height));
    await expect(sky).toHaveAttribute('data-stage', skyAtHeight(height).stage.name);
    const appearance = await sky.evaluate(el => ({ color: el.style.backgroundColor, islands: getComputedStyle(el.querySelector('.sky-island')).opacity, moon: el.querySelector('.sky-moon').dataset.visible }));
    expect(appearance.moon).toBe(String(height >= 100));
    if (height >= 50) expect(appearance.islands).toBe('0');
    if (height >= 75) {
      const clouds = await page.locator('.sky-cloud,.sky-sea').evaluateAll(elements => elements.map(el => getComputedStyle(el).opacity));
      expect(clouds).toHaveLength(13);
      expect(clouds.every(opacity => opacity === '0')).toBe(true);
    }
    await shot(page, `desktop-${height}`);
    if (height) {
      await page.locator('#camera-toggle').click();
      await expect(sky).toHaveAttribute('data-height', String(height));
      expect(await sky.evaluate(el => el.style.backgroundColor)).toBe(appearance.color);
      await page.locator('#camera-toggle').click();
    }
  }
  await expect(page.locator('.sky-constellation-hotel')).toHaveAttribute('data-visible', 'true');
  await expect(page.locator('.sky-constellation-cat')).toHaveAttribute('data-visible', 'false');
  for (const [name, width, height] of [['phone',390,844],['small-phone',320,568],['landscape',844,390]]) {
    await page.setViewportSize({ width, height }); await shot(page, name);
    await expect(page.locator('#menu-open')).toBeInViewport();
    await expect(page.locator('#offers .offer-card').first()).toBeInViewport();
    // Off-screen scenery is intentionally clipped; it must not widen the document.
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  }
  await page.locator('#menu-open').click(); await page.locator('#lobby-open').click();
  await expect(page.locator('.sky-backdrop')).toHaveAttribute('data-stage', 'Cloud Gardens');
  await shot(page, 'high-altitude-lobby');
  await page.locator('#lobby-resume').click();
  await expect(page.locator('.sky-backdrop')).toHaveAttribute('data-stage', 'Celestial Summit');
  expect(errors).toEqual([]);
});

test('new sky details unfold with visible floors, settle for reduced motion, and clear on replay', async ({ page }) => {
  await setup(page, false); await page.setViewportSize({ width: 1280, height: 720 });
  await resume(page, 11); // 49 floors, immediately before the first stars.
  await page.evaluate(() => {
    window.skyFrames = [];
    window.skyObserver = new MutationObserver(() => window.skyFrames.push({ sky: Number(document.querySelector('.sky-backdrop').dataset.height), hud: Number(document.querySelector('#height').textContent) }));
    window.skyObserver.observe(document.querySelector('.sky-backdrop'), { attributes: true, attributeFilter: ['data-height'] });
  });
  await page.locator('[data-offer-index="1"]').click();
  await expect(page.locator('.sky-star[data-visible="true"]').first()).toBeVisible();
  expect(await page.locator('.sky-star[data-visible="true"] .sky-ornament').first().evaluate(el => el.getAnimations().some(animation => animation.effect.getTiming().duration === 2100))).toBe(true);
  await expect(page.locator('#world')).toHaveAttribute('data-state', 'picking');
  const frames = await page.evaluate(() => { window.skyObserver.disconnect(); return window.skyFrames; });
  expect(frames.length).toBeGreaterThan(5);
  for (const frame of frames) expect(frame.sky).toBe(frame.hud);
  expect(frames.at(-1).sky).toBe(62);

  await resume(page, 15); // 90 floors; the next delivery crosses 100.
  await page.locator('[data-offer-index="0"]').click();
  await expect(page.locator('.sky-moon')).toHaveAttribute('data-visible', 'true');
  await shot(page, 'moon-unfolding');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await expect(page.locator('.sky-backdrop')).toHaveAttribute('data-height', '102');
  await expect(page.locator('.sky-moon .sky-ornament')).toHaveCSS('transform', 'none');
  expect(await page.locator('.sky-backdrop').evaluate(el => el.getAnimations({ subtree: true }).every(animation => animation.playState === 'paused'))).toBe(true);
  await page.locator('#menu-open').click(); await page.locator('#replay').click();
  await expect(page.locator('.sky-backdrop')).toHaveAttribute('data-stage', 'Cloud Gardens');
  await expect(page.locator('.sky-moon')).toHaveAttribute('data-visible', 'false');
  await expect(page.locator('.sky-island').first()).toHaveCSS('opacity', '1');
  await expect(page.locator('.sky-cloud').first()).toHaveCSS('opacity', '1');
  await expect(page.locator('.sky-celestial[data-visible="true"]')).toHaveCount(0);
});
