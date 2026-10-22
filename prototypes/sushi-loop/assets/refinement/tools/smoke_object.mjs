import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { chromium } from 'playwright';

const ids = process.argv.slice(2);
assert.ok(ids.length && ids.every(id => /^[a-z0-9-]+$/.test(id)), 'Pass catalog object IDs');
const origin = process.env.SUSHI_REFINEMENT_ORIGIN || 'http://127.0.0.1:4178';
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => {
    if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
  });
  for (const id of ids) {
    const states = [];
    for (const viewport of [{ width: 390, height: 844 }, { width: 1120, height: 720 }]) {
      await page.setViewportSize(viewport);
      await page.goto(`${origin}/prototypes/sushi-loop/?ntl-drawer-state=hidden#object-${id}`);
      const section = page.locator('.object-refinement');
      await section.waitFor();
      const status = await section.getAttribute('data-refinement-status');
      assert.ok(['approved', 'published'].includes(status), `${id}: ${status}`);
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `${id}: horizontal overflow`);
      const sprite = page.locator(`[data-object="${id}"] [data-sprite-source]`).first();
      await sprite.waitFor({ state: 'attached' });
      const source = await sprite.getAttribute('data-sprite-source');
      const href = await sprite.locator('image').getAttribute('href');
      const response = await page.request.get(new URL(href, page.url()).href);
      assert.equal(response.status(), 200, `${id}: atlas request failed`);
      const atlasSHA256 = hash(await response.body());
      assert.equal(atlasSHA256, hash(readFileSync(new URL(`../../production/${source}`, import.meta.url))),
        `${id}: served atlas differs from exact promoted bytes`);
      states.push({ ...viewport, status, source, atlasSHA256 });
    }
    assert.deepEqual(errors, [], `${id}: browser errors`);
    console.log(JSON.stringify({ asset: id, viewports: states, errors }));
  }
} finally {
  await browser.close();
}
