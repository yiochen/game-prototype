import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, mkdirSync, writeFileSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const base = path.dirname(fileURLToPath(import.meta.url));
const output = path.join(base, 'fractional-world-raster-release-v1'); mkdirSync(output, { recursive: true });
const dist = path.resolve(base, '../../../../../dist');
const origin = 'https://deploy-preview-37--game-prototypes-yiochen.netlify.app';
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const browser = await chromium.launch({ headless: true, executablePath: chromium.executablePath() });
const cases = [], scripts = new Map(), pending = [], errors = [];
try {
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => {
    const url = new URL(response.url());
    if (url.origin !== origin) return;
    if (response.status() >= 400) errors.push(`${response.status()} ${url.pathname}`);
    if (!url.pathname.startsWith('/assets/') || !url.pathname.endsWith('.js')) return;
    pending.push((async () => {
      const local = path.join(dist, url.pathname);
      assert.ok(existsSync(local), `Remote script absent from current build: ${url.pathname}`);
      const digest = hash(await response.body());
      assert.equal(digest, hash(readFileSync(local)), `Remote script differs: ${url.pathname}`);
      scripts.set(url.pathname, digest);
    })());
  });
  for (const [width, height] of [[390, 844], [1120, 720]]) for (const scene of ['restaurant', 'underwater']) {
    await page.setViewportSize({ width, height });
    await page.goto(`${origin}/prototypes/sushi-loop/?ntl-drawer-state=hidden#scene-${scene}`);
    const svg = page.locator(`.object-scene-scroll[data-scene-id="${scene}"] .object-tile-scene`);
    await svg.locator('canvas').waitFor();
    await page.waitForFunction(scene => document.querySelector(`.object-scene-scroll[data-scene-id="${scene}"] .object-tile-scene`)?.dataset.worldRasterReady === 'true', scene);
    const metrics = await svg.locator('canvas').evaluate(canvas => ({ width: canvas.width, height: canvas.height,
      smoothing: canvas.getContext('2d').imageSmoothingEnabled,
      painted: canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data.some((value, index) => index % 4 === 3 && value > 0) }));
    assert.equal(metrics.smoothing, false); assert.ok(metrics.painted);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.locator('.world-showcase-figure').screenshot({ path: path.join(output, `${scene}-${width}.png`) });
    cases.push({ scene, width, height, metrics });
  }
  await Promise.all(pending);
  assert.ok(scripts.size > 0); assert.deepEqual(errors, []);
  const report = { commit: 'c2c6062fa2a205d5261cdd54cea7b29ab30c5a91', netlifyDeployId: '6ada1d5e41c5826be3c1dac5',
    state: 'ready', exactCommitStatus: 'success', browser: browser.version(), executable: chromium.executablePath(),
    rendererSHA256: '570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545', cases,
    servedScriptsMatchingCurrentLocalBuild: Object.fromEntries(scripts), errors };
  writeFileSync(path.join(output, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ cases: cases.length, exactServedScripts: scripts.size, errors }));
} finally { await browser.close(); }
