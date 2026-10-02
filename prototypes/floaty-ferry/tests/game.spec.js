import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
const URL = '/prototypes/floaty-ferry/?test&ntl-drawer-state=hidden';
const island = (page, id) => page.locator(`[data-island="${id}"]`);
async function boot(page, tutorial = false) { await page.goto(URL); await expect(page.locator('canvas')).toHaveAttribute('data-ready', 'true'); await page.getByRole('button', { name: tutorial ? 'Show me how' : 'Straight to the coast' }).click(); }
async function coordinates(page, p) { const a = await page.evaluate(p => window.__floatyFerry.point(p), p), b = await page.locator('canvas').boundingBox(); return { x: b.x + a.x, y: b.y + a.y }; }
async function drawRoute(page, a, b) { const s = await page.evaluate(() => window.__floatyFerry.snapshot()), p = await coordinates(page, s.islands[a]), q = await coordinates(page, s.islands[b]); await page.mouse.move(p.x, p.y); await page.mouse.down(); await page.mouse.move(q.x, q.y, { steps: 8 }); await page.mouse.up(); }
async function buttonsRoute(page, a, b) { await island(page, a).click(); await island(page, b).click(); }
async function shot(page, name) { await mkdir('artifacts/floaty-ferry', { recursive: true }); await page.screenshot({ path: `artifacts/floaty-ferry/${name}.png` }); }

test('the tutorial teaches drawing, matching destinations and automatic transfers', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 }); await boot(page, true); await shot(page, 'first-route-lesson');
  await drawRoute(page, 0, 1); await expect(page.locator('#routes')).toHaveText('1 / 4'); await page.evaluate(() => window.__floatyFerry.advance(5));
  await expect(page.locator('#delivered')).toHaveText('1'); await buttonsRoute(page, 0, 2); await page.evaluate(() => window.__floatyFerry.advance(5));
  await expect(page.locator('#hint')).toHaveText('Watch a duck change boats at the gold star.'); await shot(page, 'transfer-lesson'); await page.evaluate(() => window.__floatyFerry.advance(15));
  await expect(page.locator('#modal-title')).toHaveText('Captain, you’re ready.'); expect(await page.evaluate(() => window.__floatyFerry.snapshot().delivered)).toBe(3);
  await page.getByRole('button', { name: 'Start a little day' }).click(); await expect(page.locator('#routes')).toHaveText('0 / 4'); await page.reload(); await expect(page.getByRole('button', { name: 'Start a little day' })).toBeVisible();
});
test('drawn routes move ducks, edit returns passengers, and a full connected day earns another ferry', async ({ page }) => {
  await boot(page); await drawRoute(page, 0, 1); await page.evaluate(() => window.__floatyFerry.advance(1));
  expect(await page.evaluate(() => window.__floatyFerry.snapshot().routes[0].passengers.length)).toBeGreaterThan(0);
  await page.locator('#edit').click(); await page.getByRole('button', { name: 'Remove route: Pebble to Rosy' }).click(); await expect(page.locator('#routes')).toHaveText('0 / 4');
  expect(await page.evaluate(() => window.__floatyFerry.snapshot().islands[0].ducks.length)).toBeGreaterThanOrEqual(2); await page.locator('#edit').click();
  for (const pair of [[0, 1], [0, 2], [1, 3], [2, 4]]) await buttonsRoute(page, ...pair);
  await page.evaluate(() => window.__floatyFerry.advance(31)); await expect(page.locator('#routes')).toHaveText('4 / 5'); await buttonsRoute(page, 0, 5); await shot(page, 'connected-map');
  await page.evaluate(() => window.__floatyFerry.advance(70)); await expect(page.locator('#modal-title')).toHaveText('A lovely day afloat.'); expect(await page.evaluate(() => window.__floatyFerry.snapshot().delivered)).toBeGreaterThan(12);
  await page.getByRole('button', { name: 'Tomorrow’s tide →' }).click(); await expect(page.locator('#chapter-label')).toHaveText('DAY 02'); await expect(page.locator('#delivered')).toHaveText('0');
});
test('touch cancellation never creates a route, while a completed drag does', async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 3 }); const page = await context.newPage(); await boot(page);
  const s = await page.evaluate(() => window.__floatyFerry.snapshot()), a = await coordinates(page, s.islands[0]), b = await coordinates(page, s.islands[1]), cdp = await context.newCDPSession(page);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [a] }); await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [b] }); await cdp.send('Input.dispatchTouchEvent', { type: 'touchCancel', touchPoints: [] });
  await expect(page.locator('#routes')).toHaveText('0 / 4'); await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [a] }); await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [b] }); await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await expect(page.locator('#routes')).toHaveText('1 / 4'); await context.close();
});
test('small phone, landscape, reduced motion, keyboard selections and pause work without overflow', async ({ page }) => {
  const errors = []; page.on('pageerror', e => errors.push(e.message)); await page.emulateMedia({ reducedMotion: 'reduce' }); await boot(page);
  for (const [name, width, height] of [['small', 320, 568], ['phone', 390, 844], ['landscape', 844, 390], ['desktop', 1280, 900]]) {
    await page.setViewportSize({ width, height });
    await expect.poll(async () => { const w = await page.locator('#world').boundingBox(), c = await page.locator('canvas').boundingBox(); return Math.abs(c.width - (w.width - 6)) + Math.abs(c.height - (w.height - 6)); }).toBeLessThan(3);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth && document.documentElement.scrollHeight <= innerHeight)).toBe(true); const controls = await island(page, 0).boundingBox(); expect(controls.width).toBeGreaterThanOrEqual(44); await shot(page, name);
  }
  await island(page, 0).focus(); await page.keyboard.press('Enter'); await island(page, 1).focus(); await page.keyboard.press('Enter'); await expect(page.locator('#routes')).toHaveText('1 / 4');
  await page.getByRole('button', { name: 'Pause and open help' }).click(); const time = await page.evaluate(() => window.__floatyFerry.snapshot().time); await page.evaluate(() => window.__floatyFerry.advance(8)); expect(await page.evaluate(() => window.__floatyFerry.snapshot().time)).toBe(time);
  await page.getByRole('button', { name: 'Back aboard' }).click(); await page.getByRole('button', { name: 'Turn sound on' }).click(); await expect(page.locator('#sound')).toHaveAttribute('aria-pressed', 'true'); expect(errors).toEqual([]);
  await page.goto('/prototypes/floaty-ferry/'); expect(await page.evaluate(() => window.__floatyFerry)).toBeUndefined();
});
