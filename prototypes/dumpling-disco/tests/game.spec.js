import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
const URL = '/prototypes/dumpling-disco/?test&ntl-drawer-state=hidden';
async function boot(page, tutorial = false) { await page.goto(URL); await expect(page.locator('canvas')).toHaveAttribute('data-ready', 'true'); await page.getByRole('button', { name: tutorial ? 'Show me how' : 'Straight to the disco' }).click(); }
async function shot(page, name) { await mkdir('artifacts/dumpling-disco', { recursive: true }); await page.screenshot({ path: `artifacts/dumpling-disco/${name}.png` }); }

test('the tutorial waits for tap and hold, and the pad responds to keyboard press/release', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 }); await boot(page, true); await page.locator('#pad').click();
  await expect(page.locator('#hint')).toHaveText('A little early. Release, then try again.'); await expect(page.locator('#score')).toHaveText('0'); await page.evaluate(() => window.__dumplingDisco.advance(20));
  expect(await page.evaluate(() => window.__dumplingDisco.snapshot().time)).toBe(2); await shot(page, 'tap-lesson'); await page.locator('#pad').click(); await expect(page.locator('#score')).toHaveText('100');
  await page.evaluate(() => window.__dumplingDisco.advance(20)); await expect(page.locator('#pad-label')).toHaveText('Hold to steam');
  await page.keyboard.down(' '); await page.evaluate(() => window.__dumplingDisco.advance(.55)); await shot(page, 'steam-lesson');
  await page.evaluate(() => window.__dumplingDisco.advance(.7)); await page.keyboard.up(' '); await expect(page.locator('#modal-title')).toHaveText('Ready to groove.');
  expect(await page.evaluate(() => window.__dumplingDisco.snapshot().score)).toBe(200); await page.getByRole('button', { name: 'Let’s dance' }).click(); await expect(page.locator('#mix-name')).toHaveText('Sesame Street');
  await page.reload(); await expect(page.getByRole('button', { name: 'Let’s dance' })).toBeVisible();
});
test('a cancelled touch hold can be retried in the lesson without losing the tap reward', async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 3 }); const page = await context.newPage(); await boot(page, true);
  await page.evaluate(() => window.__dumplingDisco.advance(2)); await page.locator('#pad').tap(); await page.evaluate(() => window.__dumplingDisco.advance(3));
  const b = await page.locator('#pad').boundingBox(), p = { x: b.x + b.width / 2, y: b.y + b.height / 2 }, cdp = await context.newCDPSession(page);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [p] }); await page.evaluate(() => window.__dumplingDisco.advance(.25)); await cdp.send('Input.dispatchTouchEvent', { type: 'touchCancel', touchPoints: [] });
  expect(await page.evaluate(() => window.__dumplingDisco.snapshot().held)).toBeNull(); await expect(page.locator('#score')).toHaveText('100');
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [p] }); await page.evaluate(() => window.__dumplingDisco.advance(1.3)); await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await expect(page.locator('#modal-title')).toHaveText('Ready to groove.'); await context.close();
});
test('a set finishes even with missed beats, and next/replay actions select the right mix', async ({ page }) => {
  await boot(page); for (let i = 0; i < 3; i++) {
    await page.evaluate(() => window.__dumplingDisco.advance(100)); await expect(page.locator('#modal-title')).toHaveText('A delicious little set.');
    if (i === 0) await shot(page, 'set-result'); await page.getByRole('button', { name: i === 2 ? 'Back to brunch' : 'Next mix →' }).click();
  }
  await expect(page.locator('#mix-name')).toHaveText('Sesame Street');
  await page.getByRole('button', { name: 'Pause and open help' }).click(); const time = await page.evaluate(() => window.__dumplingDisco.snapshot().time); await page.evaluate(() => window.__dumplingDisco.advance(5)); expect(await page.evaluate(() => window.__dumplingDisco.snapshot().time)).toBe(time);
  await page.getByRole('button', { name: 'Restart this mix' }).click(); await expect(page.locator('#score')).toHaveText('0');
});
test('mobile, short landscape, reduced motion and sound controls fit and render without errors', async ({ page }) => {
  const errors = []; page.on('pageerror', e => errors.push(e.message)); await page.emulateMedia({ reducedMotion: 'reduce' }); await boot(page, true);
  for (const [name, width, height] of [['small', 320, 568], ['phone', 390, 844], ['landscape', 844, 390], ['desktop', 1280, 900]]) {
    await page.setViewportSize({ width, height });
    await expect.poll(async () => { const w = await page.locator('#world').boundingBox(), c = await page.locator('canvas').boundingBox(); return Math.abs(c.width - (w.width - 6)) + Math.abs(c.height - (w.height - 6)); }).toBeLessThan(3);
    const pad = await page.locator('#pad').boundingBox(); expect(pad.height).toBeGreaterThanOrEqual(44); expect(pad.y + pad.height).toBeLessThanOrEqual(height);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth && document.documentElement.scrollHeight <= innerHeight)).toBe(true); await shot(page, name);
  }
  await page.getByRole('button', { name: 'Turn sound on' }).click(); await expect(page.locator('#sound')).toHaveAttribute('aria-pressed', 'true'); expect(errors).toEqual([]);
  await page.goto('/prototypes/dumpling-disco/'); expect(await page.evaluate(() => window.__dumplingDisco)).toBeUndefined();
});
