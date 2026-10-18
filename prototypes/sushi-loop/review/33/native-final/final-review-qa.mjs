import { createRequire } from 'node:module';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = '/Users/yiouchen/.codex/worktrees/sushi-loop-33-art-catalog/game-prototype';
const require = createRequire(join(root, 'package.json'));
const { chromium, expect } = require('@playwright/test');
const { spriteFrame, groundRoot, footprintFor, reviewFrameCount } = await import(pathToFileURL(join(root, 'prototypes/sushi-loop/wireframe/sprite-layout.js')));
const library = JSON.parse(await readFile(join(root, 'prototypes/sushi-loop/assets/production/library.json'), 'utf8'));
const objects = library.objects;
const output = '/private/tmp/sushi-object-review/final-117';
const base = process.env.REVIEW_URL || 'http://127.0.0.1:4189/prototypes/sushi-loop/?ntl-drawer-state=hidden';
const directions = ['N', 'E', 'S', 'W'];
const targets = ['submarine-yellow', 'garbage-sofa', 'garbage-car', 'garbage-shelving', 'harpoon-projectile', 'harpoon-cable', 'creature-fish', 'creature-eel', 'belt-straight-n', 'belt-corner-n-e', 'chef-blackboard', 'bubble-preference', 'salvage-metal'];
const snapshots = new Set(['submarine-yellow', 'garbage-car', 'harpoon-projectile', 'creature-eel', 'belt-corner-n-e', 'chef-blackboard', 'bubble-preference', 'salvage-metal']);
expect(objects).toHaveLength(117);
expect(objects.filter(object => object.status !== 'ready')).toEqual([]);
expect(library.approval?.finalAssets).toMatch(/pending/);
await mkdir(output, { recursive: true });
const browser = await chromium.launch();
const results = [], errors = [], failedImages = [];
try {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
  page.on('pageerror', error => errors.push(error.message));
  const nestedScrollers = () => page.evaluate(() => [...document.querySelectorAll('body *')].filter(element => /auto|scroll/.test(getComputedStyle(element).overflowY) && element.scrollHeight > element.clientHeight + 2 && element.getClientRects().length && !element.matches('textarea, select')).map(element => element.id || element.className));
  async function decodeVisibleSceneImages(scene) {
    const values = await scene.locator('image').evaluateAll(async elements => Promise.all([...new Set(elements.map(element => element.getAttribute('href')))].map(src => new Promise(resolve => {
      const image = new Image();
      image.onload = () => resolve({ src, width: image.naturalWidth, height: image.naturalHeight });
      image.onerror = () => resolve({ src, width: 0, height: 0 });
      image.src = src;
    }))));
    failedImages.push(...values.filter(value => !value.width || !value.height));
    return values;
  }
  for (const id of targets) {
    const object = objects.find(entry => entry.id === id);
    expect(object, id).toBeTruthy();
    expect(object.clips.length, id).toBeGreaterThan(0);
    await page.goto(`${base}#object-${id}`);
    const stage = page.locator('#prototype-stage');
    await expect(stage).toHaveAttribute('data-story', `object-${id}`);
    await expect(stage.locator('.object-export-pending')).toHaveCount(0);
    expect(await nestedScrollers(), id).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth), id).toBeLessThanOrEqual(391);
    const repeated = stage.locator('.object-tile-scene').nth(1);
    for (const direction of directions) {
      await stage.getByLabel('Repeated facing', { exact: true }).selectOption(direction);
      const footprint = footprintFor(object, direction);
      const tiles = repeated.locator(`g[data-object="${id}"]`);
      await expect(tiles).toHaveCount(9);
      const rects = await tiles.locator(':scope > .object-footprint').evaluateAll(elements => elements.map(element => ['x','y','width','height'].map(name => Number(element.getAttribute(name)))));
      expect(rects).toEqual(Array.from({ length: 9 }, (_, index) => [index % 3 * footprint[0] * 128, Math.floor(index / 3) * footprint[1] * 128, footprint[0] * 128, footprint[1] * 128]));
    }
    await stage.getByLabel('Repeated facing', { exact: true }).selectOption('S');
    const initialRoot = [...object.root];
    for (const clip of object.clips) {
      if (id.startsWith('belt-')) expect(clip.frames).toBe(24);
      if (clip.frames > 1) expect(clip.frames).toBeGreaterThanOrEqual(6);
      expect(Object.keys(clip.directions).sort()).toEqual([...directions].sort());
      await stage.getByLabel('Scene state', { exact: true }).selectOption(clip.id);
      await expect(stage.locator('.object-animation[open]')).toHaveCount(1);
      await expect(stage.locator('.object-animation:not([open]) svg')).toHaveCount(0);
      const facings = stage.locator('.object-tile-scene').first();
      const extent = Math.max(...directions.flatMap(direction => footprintFor(object, direction)));
      const frames = [...new Set([0, Math.floor((clip.frames - 1) / 2), clip.frames - 1])];
      for (const frame of frames) {
        if (reviewFrameCount(object, objects) > 1) await stage.getByRole('slider', { name: 'Animation frame' }).fill(String(frame));
        for (const [index, direction] of directions.entries()) {
          const registered = spriteFrame(object, clip, direction, frame / 12);
          const pose = facings.locator(`g[data-object="${id}"][data-direction="${direction}"]`);
          await expect(pose).toHaveAttribute('data-frame', String(frame));
          const actual = await pose.locator(':scope > svg[data-sprite-source]').evaluate(element => ({ source: element.dataset.spriteSource, geometry: ['x','y','width','height'].map(name => Number(element.getAttribute(name))), rect: element.getAttribute('viewBox').split(' ').map(Number) }));
          const projectedRoot = groundRoot({ x: index * (extent + 1), y: 0, direction }, object, 128);
          expect(actual.source).toBe(registered.image);
          expect(actual.geometry).toEqual([projectedRoot[0] - registered.root[0], projectedRoot[1] - registered.root[1], ...registered.frameSize]);
          expect(actual.rect).toEqual(registered.rect);
          expect(registered.root).toEqual(initialRoot);
        }
      }
      await decodeVisibleSceneImages(facings);
    }
    const variants = Object.keys(object.variants || {});
    if (id === 'submarine-yellow') {
      expect(variants).toEqual(expect.arrayContaining(['baseline', 'upgraded']));
      await expect(stage.locator('.object-interaction').filter({ hasText: 'Baseline and upgraded' })).toHaveCount(1);
    }
    if (['chef-blackboard', 'bubble-preference'].includes(id)) expect(variants).toEqual(expect.arrayContaining(['salmon-nigiri', 'cucumber-maki', 'eel-roll']));
    if (id === 'salvage-metal') expect(variants).toEqual(expect.arrayContaining(['plate', 'bent']));
    for (const variant of Object.values(object.variants || {})) for (const clipId of variant.clips || []) expect(object.clips.map(clip => clip.id), id).toContain(clipId);
    if (snapshots.has(id)) {
      await stage.getByLabel('Scene state', { exact: true }).selectOption(object.clips[0].id);
      if (reviewFrameCount(object, objects) > 1) await stage.getByRole('slider', { name: 'Animation frame' }).fill('0');
      await decodeVisibleSceneImages(stage);
      await stage.locator('.object-review-section').first().screenshot({ path: join(output, `${id}-phone-directions.png`) });
      if (await stage.locator('.object-interaction').count()) await stage.locator('.object-interaction').first().screenshot({ path: join(output, `${id}-phone-context.png`) });
    }
    results.push({ id, states: object.clips.length, variants, frameSize: object.frameSize, root: object.root, maxFrames: reviewFrameCount(object, objects), nestedVerticalScrollers: await nestedScrollers() });
    console.log(`PASS ${id}: ${object.clips.length} clips, ${variants.length} variants`);
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  for (const id of ['submarine-yellow', 'garbage-car', 'creature-fish', 'belt-straight-n']) {
    await page.goto(`${base}#object-${id}`);
    const stage = page.locator('#prototype-stage');
    await decodeVisibleSceneImages(stage);
    expect(await nestedScrollers()).toEqual([]);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: join(output, `${id}-desktop.png`) });
    if (await stage.locator('.object-interaction').count()) await stage.locator('.object-interaction').first().screenshot({ path: join(output, `${id}-desktop-context.png`) });
  }
  expect(failedImages).toEqual([]);
  expect(errors).toEqual([]);
  await writeFile(join(output, 'report.json'), JSON.stringify({ objectCount: objects.length, readyCount: objects.filter(object => object.status === 'ready').length, results, failedImages, errors }, null, 2));
  console.log(`Final QA passed: ${targets.length} objects; ${results.reduce((sum, item) => sum + item.states, 0)} clips`);
} finally {
  await browser.close();
}
