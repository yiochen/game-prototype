import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
const URL = '/prototypes/pollen-club/?test&ntl-drawer-state=hidden';
async function boot(page, tutorial = false) { await page.goto(URL); await expect(page.locator('canvas')).toHaveAttribute('data-ready', 'true'); await page.getByRole('button', { name: tutorial ? 'Show me how' : 'Straight to the garden' }).click(); }
async function coordinates(page, p) { const a = await page.evaluate(p => window.__pollenClub.point(p), p), b = await page.locator('canvas').boundingBox(); return { x: b.x + a.x, y: b.y + a.y }; }
async function pullBee(page, pull) { const s = await page.evaluate(() => window.__pollenClub.snapshot()); const a = await coordinates(page, s.home), b = await coordinates(page, { x: s.home.x + pull.x, y: s.home.y + pull.y }); await page.mouse.move(a.x, a.y); await page.mouse.down(); await page.mouse.move(b.x, b.y, { steps: 8 }); await page.mouse.up(); }
async function shot(page, name) { await mkdir('artifacts/pollen-club', { recursive: true }); await page.screenshot({ path: `artifacts/pollen-club/${name}.png` }); }

test('the interactive tutorial teaches pulling and a real rebound, then remembers completion', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 }); await boot(page, true);
  await pullBee(page, { x: 0, y: 65 }); await page.evaluate(() => window.__pollenClub.advance(3));
  await expect(page.locator('#modal-title')).toHaveText('One happy flower!'); await page.getByRole('button', { name: 'Try the bounce' }).click();
  await shot(page, 'bounce-lesson'); await pullBee(page, { x: 0, y: 85 }); await page.evaluate(() => window.__pollenClub.advance(5));
  await expect(page.locator('#modal-title')).toHaveText('You’re a natural.'); expect(await page.evaluate(() => window.__pollenClub.snapshot().bounces)).toBeGreaterThan(0);
  await page.getByRole('button', { name: 'Into the garden' }).click(); await expect(page.locator('#blooms')).toHaveText('0 / 3');
  await page.reload(); await expect(page.getByRole('button', { name: 'Play a little round' })).toBeVisible();
});
test('all gardens can finish through real aiming gestures and their result controls', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 }); await boot(page);
  const pulls = [[95.86843533643909, 5.024251799322608], [93.90216967044535, 19.959522318504895], [94.81808069713323, 15.017708643862164], [59.380454746769054, 26.43788179992701], [46.67902132486009, 17.918397477265014]];
  for (let i = 0; i < pulls.length; i++) {
    await pullBee(page, { x: pulls[i][0], y: pulls[i][1] }); await page.evaluate(() => window.__pollenClub.advance(7));
    await expect(page.locator('#blooms')).toHaveText('3 / 3'); await expect(page.locator('#modal')).toBeVisible();
    if (i === 2) await shot(page, 'garden-medal');
    await page.getByRole('button', { name: i === 4 ? 'Another garden tour' : 'Next garden →' }).click();
  }
  await expect(page.locator('#garden-name')).toHaveText('Good morning'); expect(await page.evaluate(() => JSON.parse(localStorage.getItem('pollen-club:medals')))).toEqual([3, 3, 3, 3, 3]);
});
test('a cancelled touch pull preserves the shot, and a release launches exactly once', async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 3 }); const page = await context.newPage(); await boot(page);
  const cdp = await context.newCDPSession(page), s = await page.evaluate(() => window.__pollenClub.snapshot()), a = await coordinates(page, s.home), b = await coordinates(page, { x: s.home.x + 30, y: s.home.y + 55 });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [a] }); await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [b] }); await cdp.send('Input.dispatchTouchEvent', { type: 'touchCancel', touchPoints: [] });
  expect(await page.evaluate(() => window.__pollenClub.snapshot().shots)).toBe(0);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [a] }); await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [b] }); await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  expect(await page.evaluate(() => window.__pollenClub.snapshot().shots)).toBe(1); await context.close();
});
test('small phones, landscape, reduced motion, keyboard aim and pause stay usable', async ({ page }) => {
  const errors = []; page.on('pageerror', e => errors.push(e.message)); await page.emulateMedia({ reducedMotion: 'reduce' }); await boot(page);
  for (const [name, width, height] of [['small', 320, 568], ['phone', 390, 844], ['landscape', 844, 390], ['desktop', 1280, 900]]) {
    await page.setViewportSize({ width, height });
    await expect.poll(async () => { const w = await page.locator('#world').boundingBox(), c = await page.locator('canvas').boundingBox(); return Math.abs(c.width - (w.width - 6)) + Math.abs(c.height - (w.height - 6)); }).toBeLessThan(3);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth && document.documentElement.scrollHeight <= innerHeight)).toBe(true); await shot(page, name);
  }
  await page.locator('#world').focus(); await page.keyboard.press('ArrowRight'); await page.keyboard.press(' '); await expect(page.locator('#shots')).toHaveText('1');
  await page.getByRole('button', { name: 'Pause and open help' }).click(); const before = await page.evaluate(() => window.__pollenClub.snapshot().elapsed); await page.evaluate(() => window.__pollenClub.advance(3)); expect(await page.evaluate(() => window.__pollenClub.snapshot().elapsed)).toBe(before);
  await page.getByRole('button', { name: 'Back to the bee' }).click(); await page.getByRole('button', { name: 'Turn sound on' }).click(); await expect(page.locator('#sound')).toHaveAttribute('aria-pressed', 'true'); expect(errors).toEqual([]);
  await page.goto('/prototypes/pollen-club/'); expect(await page.evaluate(() => window.__pollenClub)).toBeUndefined();
});
test('the playground features all six games and bundles the new illustrated covers', async ({ page }) => {
  await page.goto('/'); await expect(page.locator('.prototype')).toHaveCount(6); await expect(page.locator('.prototype').first()).toHaveAttribute('href', './prototypes/pollen-club/');
  await expect.poll(() => page.locator('.prototype-art img').evaluateAll(imgs => imgs.every(img => img.complete && img.naturalWidth > 0))).toBe(true);
  await page.setViewportSize({ width: 320, height: 740 }); expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true); await shot(page, 'playground');
});
