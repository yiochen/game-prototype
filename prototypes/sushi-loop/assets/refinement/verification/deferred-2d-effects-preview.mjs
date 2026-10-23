import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { chromium } from 'playwright';

const root = new URL('../', import.meta.url);
const policy = JSON.parse(readFileSync(new URL('deferred-2d-effects.json', root)));
const origin = 'https://deploy-preview-37--game-prototypes-yiochen.netlify.app';
const browser = await chromium.launch({ headless: true });
const results = [];
const errors = [];
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
try {
  const page = await browser.newPage();
  page.on('pageerror', error => errors.push(error.message));
  for (const viewport of [{ width: 390, height: 844 }, { width: 1120, height: 720 }]) {
    await page.setViewportSize(viewport);
    for (const object of policy.objects) {
      await page.goto(`${origin}/prototypes/sushi-loop/?ntl-drawer-state=hidden#object-${object.id}`);
      const section = page.locator('.object-refinement');
      await section.waitFor();
      assert.equal(await section.getAttribute('data-refinement-status'), 'deferred');
      assert.match(await section.innerText(), /2D effect · refinement deferred/);
      assert.equal(await page.locator('.object-status').innerText(), '2D effect · deferred');
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      const sprite = page.locator(`[data-object="${object.id}"] [data-sprite-source]`).first();
      const source = await sprite.getAttribute('data-sprite-source');
      const href = await sprite.locator('image').getAttribute('href');
      const response = await page.request.get(new URL(href, page.url()).href);
      assert.equal(response.status(), 200);
      assert.equal(hash(await response.body()), object.originalAtlasHashes[source], source);
      results.push({ id: object.id, ...viewport, label: '2D effect · deferred', status: 'passed' });
    }
  }
  let atlases = 0;
  // Vite publishes content-named URLs, rather than the source directory paths.
  const built = new URL('../../../../../dist/assets/', import.meta.url);
  const urlsByHash = new Map();
  for (const name of readdirSync(built).filter(name => name.endsWith('.png'))) {
    urlsByHash.set(hash(readFileSync(new URL(name, built))), `${origin}/assets/${name}`);
  }
  for (const object of policy.objects) {
    for (const [path, expected] of Object.entries(object.originalAtlasHashes)) {
      assert.ok(urlsByHash.has(expected), `Missing exact built content: ${path}`);
      const response = await page.request.get(urlsByHash.get(expected));
      assert.equal(response.status(), 200, path);
      assert.equal(hash(await response.body()), expected, path);
      atlases += 1;
    }
  }
  assert.deepEqual(errors, []);
  const report = { origin, deployCommit: '3847fc7d7642b28cde23dc63ef4870cc1722e3eb',
    objects: policy.objects.length, originalAtlasContentsVerified: atlases,
    contentURLMethod: 'Exact original SHA-256 matched against local Vite build content-named URL, then fetched from exact ready preview. Default displayed sprite URL independently verified in every browser case.',
    results, errors };
  writeFileSync(new URL('deferred-2d-effects-preview.json', import.meta.url), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ objects: report.objects, originalAtlasesVerified: atlases,
    browserCases: results.length, errors }));
} finally {
  await browser.close();
}
