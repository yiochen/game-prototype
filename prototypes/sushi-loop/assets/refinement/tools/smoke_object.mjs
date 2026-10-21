import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const ids = process.argv.slice(2);
assert.ok(ids.length && ids.every(id => /^[a-z0-9-]+$/.test(id)), 'Pass catalog object IDs');
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
      await page.goto(`http://127.0.0.1:4178/prototypes/sushi-loop/?ntl-drawer-state=hidden#object-${id}`);
      const section = page.locator('.object-refinement');
      await section.waitFor();
      const status = await section.getAttribute('data-refinement-status');
      assert.ok(['approved', 'published'].includes(status), `${id}: ${status}`);
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `${id}: horizontal overflow`);
      states.push({ ...viewport, status });
    }
    assert.deepEqual(errors, [], `${id}: browser errors`);
    console.log(JSON.stringify({ asset: id, viewports: states, errors }));
  }
} finally {
  await browser.close();
}
