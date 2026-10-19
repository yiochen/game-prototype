import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { chromium } from 'playwright';

// Record the real review site's tiled sprite renderer after final publication.
// No source sprites, artwork, timing, CSS or DOM composition are substituted.
const here = dirname(fileURLToPath(import.meta.url));
const prototype = resolve(here, '../../..');
const production = resolve(prototype, 'assets/production');
const { values } = parseArgs({ options: {
  'base-url': { type: 'string', default: 'http://127.0.0.1:4175' },
  'output-dir': { type: 'string', default: resolve(here, 'videos') },
  'expected-source-sha': { type: 'string' },
} });
const expectedSource = values['expected-source-sha'];
assert.match(expectedSource || '', /^[a-f0-9]{64}$/, 'Pass the final approved Blender SHA with --expected-source-sha.');
const manifestBytes = await readFile(resolve(production, 'library.json'));
const manifest = JSON.parse(manifestBytes);
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
assert.equal(manifest.approval?.finalAssets, 'approved', 'Refusing to record an unfinished production manifest.');
assert.equal(manifest.production?.visualApproval, 'approved', 'Final production approval must be published first.');
assert.equal(manifest.production?.nativeSourceSHA256?.['sushi-loop-world-library.blend'], expectedSource, 'Manifest does not identify the requested final source.');
assert.equal(sha(await readFile(resolve(production, 'source/blender/sushi-loop-world-library.blend'))), expectedSource, 'Saved Blender project differs from the requested source.');
const output = resolve(values['output-dir']);
const raw = resolve(output, '.playwright-raw');
await mkdir(raw, { recursive: true });
const cases = [
  { id: 'chef-work-load', object: 'chef-lena', clips: ['work', 'load'], seconds: 4.2 },
  { id: 'customer-walk-sit-eat', object: 'customer-rosa', clips: ['walk', 'sit-down', 'seated-wait', 'eat'], seconds: 3.2 },
  { id: 'connected-conveyor', object: 'belt-corner-n-e', clips: ['running'], seconds: 10.2, interaction: true },
];
const sizes = [
  { id: 'phone', viewport: { width: 390, height: 844 }, zoom: '2' },
  { id: 'closeup', viewport: { width: 820, height: 1100 }, zoom: '1' },
];
for (const item of cases) {
  const object = manifest.objects.find(object => object.id === item.object);
  assert.ok(object, `Missing ${item.object}`);
  for (const clip of item.clips) assert.ok(object.clips.some(entry => entry.id === clip && entry.frames >= 6), `Missing complete ${item.object}/${clip}`);
}
const browser = await chromium.launch();
const receipts = [];
const hashCache = new Map();
async function verifyVisibleExports(page, locator) {
  const entries = await locator.locator('[data-sprite-source]').evaluateAll(nodes => nodes.map(node => ({ source: node.dataset.spriteSource, url: node.querySelector('image')?.getAttribute('href') })));
  assert.ok(entries.length, 'No real production sprite exports are mounted.');
  for (const { source, url } of entries) {
    assert.ok(source.startsWith('sprites/') && !source.includes('..') && url, 'Only registered production exports may be recorded.');
    if (!hashCache.has(url)) {
      const response = await page.request.get(new URL(url, page.url()).href);
      assert.ok(response.ok(), `Failed production image: ${source}`);
      const remoteHash = sha(await response.body());
      assert.equal(remoteHash, sha(await readFile(resolve(production, source))), `Browser image differs from final published production export: ${source}`);
      hashCache.set(url, { source, sha256: remoteHash });
    }
  }
  assert.equal(await locator.locator('.object-export-pending').count(), 0, 'Pending cells cannot appear in final footage.');
  const loaded = await locator.locator('image').evaluateAll(async nodes => Promise.all([...new Set(nodes.map(node => node.getAttribute('href')))].map(url => new Promise(resolve => {
    const image = new Image(); image.onload = () => resolve(image.naturalWidth > 0); image.onerror = () => resolve(false); image.src = url;
  }))));
  assert.ok(loaded.every(Boolean), 'An image was not decoded before recording.');
  return [...new Set(entries.map(entry => entry.source))];
}
async function prepare(page, item, size) {
  await page.goto(new URL(`/prototypes/sushi-loop/?ntl-drawer-state=hidden#object-${item.object}`, values['base-url']).href);
  await page.locator('#prototype-stage').waitFor();
  assert.equal(await page.locator('.object-review-heading .object-status').textContent(), 'Approved', 'Browser build does not use the final approved manifest.');
  await page.getByLabel('Roots & attachments', { exact: true }).uncheck();
  await page.getByLabel('Scene zoom', { exact: true }).selectOption(item.interaction ? '1' : size.zoom);
  await page.getByLabel('Scene state', { exact: true }).selectOption(item.clips[0]);
  await page.getByRole('slider', { name: 'Animation frame', exact: true }).fill('0');
  const section = page.locator('.object-review-section').nth(item.interaction ? 2 : 0);
  const scene = item.interaction ? section.locator('.object-interaction').last().locator('.object-scene-scroll') : section.locator('.object-scene-scroll');
  await verifyVisibleExports(page, scene);
  return { target: item.interaction ? scene.locator('..') : section, scene };
}
try {
  for (const size of sizes) for (const item of cases) {
    // Verify build/source consistency before enabling recording, then repeat
    // preparation in the actual recorded context to retain visible controls.
    const preflight = await browser.newContext({ viewport: size.viewport, reducedMotion: 'reduce' });
    const preflightPage = await preflight.newPage();
    await prepare(preflightPage, item, size);
    await preflight.close();
    const context = await browser.newContext({ viewport: size.viewport, reducedMotion: 'reduce', recordVideo: { dir: raw, size: size.viewport } });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const { target, scene } = await prepare(page, item, size);
    const samples = [];
    for (const clip of item.clips) {
      await page.getByLabel('Scene state', { exact: true }).selectOption(clip);
      await page.getByRole('slider', { name: 'Animation frame', exact: true }).fill('0');
      const sources = await verifyVisibleExports(page, scene);
      await page.getByRole('button', { name: 'Play animations', exact: true }).click();
      await target.evaluate(node => window.scrollTo({ top: node.getBoundingClientRect().top + window.scrollY - 12, behavior: 'instant' }));
      await scene.evaluate(node => { node.scrollLeft = 0; });
      const observed = new Set();
      const started = performance.now();
      let panned = false;
      while ((performance.now() - started) < item.seconds * 1000) {
        const states = await scene.locator(`[data-object="${item.object}"]`).evaluateAll(nodes => nodes.map(node => Number(node.dataset.frame)));
        states.forEach(frame => observed.add(frame));
        if (size.id === 'phone' && !item.interaction && !panned && performance.now() - started > item.seconds * 500) {
          await scene.evaluate(node => { node.scrollLeft = node.scrollWidth - node.clientWidth; }); panned = true;
        }
        await page.waitForTimeout(55);
      }
      assert.ok(observed.size >= 6, `${item.object}/${clip}: fewer than six native frames were visible.`);
      samples.push({ clip, sources, observedFrameIndices: [...observed].sort((a, b) => a - b), sceneViewBox: await scene.locator('svg.object-tile-scene').getAttribute('viewBox') });
      await page.getByRole('button', { name: 'Pause animations', exact: true }).click();
    }
    assert.deepEqual(errors, [], 'Browser errors occurred during footage.');
    const screenshot = resolve(output, `${item.id}-${size.id}.png`);
    await target.evaluate(node => window.scrollTo({ top: node.getBoundingClientRect().top + window.scrollY - 12, behavior: 'instant' }));
    await page.screenshot({ path: screenshot });
    const video = page.video();
    await context.close();
    const destination = resolve(output, `${item.id}-${size.id}.webm`);
    await video.saveAs(destination);
    const videoBytes = await readFile(destination);
    receipts.push({ id: `${item.id}-${size.id}`, sourceSHA256: expectedSource, viewport: size.viewport, zoom: item.interaction ? '1' : size.zoom, url: page.url(), video: destination.split('/').pop(), sha256: sha(videoBytes), bytes: videoBytes.length, screenshot: screenshot.split('/').pop(), samples });
    console.log(`${item.id}-${size.id}: recorded ${samples.map(sample => `${sample.clip}:${sample.observedFrameIndices.length}`).join(', ')} native frames`);
    await writeFile(resolve(output, 'recordings.json'), JSON.stringify({ version: 1, productionManifestSHA256: sha(manifestBytes), sourceSHA256: expectedSource, browser: await browser.version(), input: 'Actual approved production sprite atlases rendered by the unchanged wireframe tile renderer', imageReceipts: [...hashCache.values()], recordings: receipts }, null, 2) + '\n');
  }
} finally {
  await browser.close();
  await rm(raw, { recursive: true, force: true });
}
