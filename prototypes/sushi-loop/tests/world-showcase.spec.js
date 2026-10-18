import { test, expect } from '@playwright/test';
import { restaurantShowcase } from '../wireframe/restaurant-showcase-data.js';
import { underwaterShowcase } from '../wireframe/underwater-showcase-data.js';
const url = '/prototypes/sushi-loop/?ntl-drawer-state=hidden';
const scenes = [restaurantShowcase, underwaterShowcase];
const nestedScrollers = page => page.evaluate(() => [...document.querySelectorAll('body *')].filter(element => /auto|scroll/.test(getComputedStyle(element).overflowY) && element.scrollHeight > element.clientHeight + 2 && element.getClientRects().length && !element.matches('textarea, select')).map(element => element.id || element.className));

for (const [width, height] of [[320, 740], [844, 390], [1440, 1000]]) {
  test(`composed scenes expose native art and working review controls at ${width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    for (const scene of scenes) {
      await page.goto(`${url}#scene-${scene.id}`);
      const stage = page.locator('#prototype-stage');
      await expect(stage).toHaveAttribute('data-story', `scene-${scene.id}`);
      await expect(stage).toHaveClass(/frame--map/);
      await expect(stage.getByRole('heading', { name: scene.title, exact: true })).toBeVisible();
      const pan = stage.locator(`.object-scene-scroll[data-scene-id="${scene.id}"]`);
      const svg = pan.locator('.object-tile-scene');
      await expect(svg.locator(':scope > g[data-placement]')).toHaveCount(scene.placements.length);
      await expect(stage.locator('.object-export-pending')).toHaveCount(0);
      await expect(stage.locator('.object-root, [data-calibration-grid]')).toHaveCount(0);
      await expect(stage.getByRole('button', { name: 'Play scene animations', exact: true })).toBeVisible();
      const slider = stage.getByRole('slider', { name: 'Scene animation frame' });
      await expect(slider).toHaveAttribute('max', String(scene.duration * 12 - 1));
      const beforeBounds = await svg.getAttribute('viewBox');
      const expectedCamera = scene.cameraBounds.map(value => value * 128);
      expect(beforeBounds).toBe(expectedCamera.join(' '));
      expect(expectedCamera[2]).toBe(896);
      const sources = await svg.locator('[data-sprite-source]').evaluateAll(nodes => nodes.map(node => node.dataset.spriteSource));
      expect(sources.length).toBe(scene.placements.length);
      expect(sources.every(source => source.startsWith('sprites/') && !/concept|catalog-v0/.test(source))).toBe(true);
      const decoded = await svg.locator('image').evaluateAll(async nodes => Promise.all([...new Set(nodes.map(node => node.getAttribute('href')))].map(src => new Promise(resolve => { const image = new Image(); image.onload = () => resolve([image.naturalWidth, image.naturalHeight]); image.onerror = () => resolve([0, 0]); image.src = src; }))));
      expect(decoded.every(([w, h]) => w > 0 && h > 0)).toBe(true);
      await stage.locator('.world-showcase-figure').screenshot({ path: testInfo.outputPath(`${scene.id}-${width}-fit.png`) });
      const moving = scene.placements.find(placement => placement.motion);
      const mover = svg.locator(`:scope > g[data-placement="${moving.id}"] > svg[data-sprite-source]`);
      const beforePosition = await mover.evaluate(element => ['x', 'y'].map(key => element.getAttribute(key)));
      await slider.fill(String(Math.round(moving.motion.duration * 3)));
      expect(await mover.evaluate(element => ['x', 'y'].map(key => element.getAttribute(key)))).not.toEqual(beforePosition);
      expect(await svg.getAttribute('viewBox')).toBe(beforeBounds);
      await stage.locator('.world-showcase-figure').screenshot({ path: testInfo.outputPath(`${scene.id}-${width}-quarter-path.png`) });
      await stage.getByLabel('Tile grid', { exact: true }).check();
      await stage.getByLabel('Roots & ports', { exact: true }).check();
      await expect(svg.locator('[data-calibration-grid]')).toHaveCount(1);
      await expect(svg.locator('.object-root')).toHaveCount(scene.placements.length);
      await stage.getByLabel('Tile grid', { exact: true }).uncheck();
      await stage.getByLabel('Roots & ports', { exact: true }).uncheck();
      await stage.getByLabel('Scene zoom', { exact: true }).selectOption('2');
      await expect.poll(() => pan.evaluate(element => element.scrollWidth > element.clientWidth)).toBe(true);
      await pan.evaluate(element => { element.scrollLeft = 70; });
      expect(await pan.evaluate(element => element.scrollLeft)).toBeGreaterThan(0);
      expect(await pan.evaluate(element => element.scrollTop)).toBe(0);
      await stage.getByLabel('Scene zoom', { exact: true }).selectOption('1');
      await slider.fill('0');
      await stage.getByRole('button', { name: 'Play scene animations', exact: true }).click();
      await expect.poll(() => slider.inputValue()).not.toBe('0');
      await stage.getByRole('button', { name: 'Pause scene animations', exact: true }).click();
      const paused = await slider.inputValue();
      await page.waitForTimeout(130);
      expect(await slider.inputValue()).toBe(paused);
      expect(await nestedScrollers(page)).toEqual([]);
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 1);
      await expect(stage.locator('.world-highlight')).toHaveCount(scene.highlights.length);
      for (const highlight of scene.highlights) for (const id of highlight.objectIds) expect(await stage.locator(`.world-highlights a[href="#object-${id}"]`).count()).toBeGreaterThan(0);
      await stage.locator('.world-asset-index summary').click();
      const used = new Set([scene.floorId, ...scene.placements.map(placement => placement.object)]);
      await expect(stage.locator('.world-asset-index a')).toHaveCount(used.size);
    }
    expect(errors).toEqual([]);
  });
}

test('scene links and inspection preserve exact routes and return to the scene header', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto(`${url}#object-library`);
  const stage = page.locator('#prototype-stage');
  await stage.locator('a[href="#scene-restaurant"]').click();
  await expect(stage).toHaveAttribute('data-story', 'scene-restaurant');
  await stage.getByRole('navigation', { name: 'Scene previews' }).getByRole('link', { name: 'Underwater scene', exact: true }).click();
  await expect(stage).toHaveAttribute('data-story', 'scene-underwater');
  await expect(page.locator('#story-title')).toBeInViewport();
  const link = stage.locator('.world-highlights a').first();
  const destination = (await link.getAttribute('href')).slice(1);
  await link.click();
  await expect(stage).toHaveAttribute('data-story', destination);
  await expect(page.locator('#story-title')).toBeInViewport();
  await page.goBack();
  await expect(stage).toHaveAttribute('data-story', 'scene-underwater');
  await page.getByRole('button', { name: 'Examples', exact: true }).click();
  const sidebar = page.getByRole('complementary', { name: 'Wireframe examples' });
  await expect(sidebar.getByRole('link', { name: 'Restaurant scene', exact: true })).toBeVisible();
  await expect(sidebar.getByRole('link', { name: 'Underwater scene', exact: true })).toBeVisible();
});

test('a phone swipe over either full map scrolls the document at fit and detail zoom', async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, reducedMotion: 'reduce' });
  const page = await context.newPage();
  const client = await context.newCDPSession(page);
  for (const scene of scenes) for (const zoom of ['1', '2']) {
    await page.goto(`${url}#scene-${scene.id}`);
    await page.getByLabel('Scene zoom', { exact: true }).selectOption(zoom);
    const target = page.locator(`.object-scene-scroll[data-scene-id="${scene.id}"]`);
    await target.scrollIntoViewIfNeeded();
    await page.evaluate(() => { const max = document.scrollingElement.scrollHeight - innerHeight; if (max - scrollY < 180) scrollTo(0, Math.max(0, max - 180)); });
    const bounds = await target.boundingBox();
    const x = Math.min(350, Math.max(40, bounds.x + bounds.width / 2));
    const y = Math.min(720, Math.max(350, bounds.y + Math.min(bounds.height - 12, 210)));
    const before = await page.evaluate(() => scrollY);
    await client.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] });
    for (let step = 1; step <= 6; step++) { await client.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x, y: y - step * 26 }] }); await new Promise(resolve => setTimeout(resolve, 30)); }
    await client.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await expect.poll(() => page.evaluate(() => scrollY), { message: `${scene.id}/${zoom}× map swipe reaches document` }).toBeGreaterThan(before + 30);
    expect(await target.evaluate(element => element.scrollTop)).toBe(0);
    expect(await nestedScrollers(page)).toEqual([]);
  }
  await context.close();
});
