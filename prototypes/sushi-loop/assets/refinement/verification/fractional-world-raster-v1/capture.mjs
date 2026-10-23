import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = path.dirname(fileURLToPath(import.meta.url));
const fixture = path.resolve(root, '../../objects/floor-underwater');
const functions = readFileSync(path.join(root, 'world-raster-functions.js'));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const server = http.createServer((request, response) => {
  const name = decodeURIComponent(request.url.split('?')[0]);
  if (name === '/source/consumer-resources/world-raster-functions.js') {
    response.setHeader('Content-Type', 'text/javascript'); response.end(functions); return;
  }
  const file = path.resolve(fixture, '.' + name);
  if (!file.startsWith(fixture + path.sep)) { response.writeHead(403).end(); return; }
  try {
    response.setHeader('Content-Type', ({ '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png' })[path.extname(file)] || 'text/plain');
    response.end(readFileSync(file));
  } catch { response.writeHead(404).end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const reports = [];
try {
  for (const backend of ['full-chrome', 'headless-shell']) {
    const output = path.join(root, backend); mkdirSync(output, { recursive: true });
    const browser = await chromium.launch({ headless: true,
      ...(backend === 'full-chrome' ? { executablePath: chromium.executablePath() } : {}) });
    try {
      const page = await browser.newPage({ viewport: { width: 1200, height: 1200 }, deviceScaleFactor: 1 });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      page.on('response', response => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
      await page.goto(`http://127.0.0.1:${server.address().port}/source/consumer.html`);
      await page.waitForFunction(() => window.ready);
      const cases = [], offsets = [[0, 0], [.125, .375], [.25, .5], [.5, .25], [.875, .625]];
      const backgrounds = ['#f5f5f0', '#808080', '#14181e'];
      for (const kind of ['native', 'independent']) for (const direction of 'NESW') {
        for (let phase = 0; phase < 12; phase++) for (const offset of offsets) for (const background of backgrounds) {
          const input = { kind, direction, phase, offset, pan: [offset[1], offset[0]], background, width: 320 };
          cases.push(await page.evaluate(input => window.renderCase(input), input));
          if (phase % 4 === 0 && offset === offsets[1] && background === backgrounds[phase / 4]) {
            await page.locator('svg').screenshot({ path: path.join(output, `phone-${kind}-${direction}-${phase}.png`) });
          }
        }
      }
      for (const kind of ['native', 'independent']) for (const direction of 'NESW') for (let bg = 0; bg < 3; bg++) {
        cases.push(await page.evaluate(input => window.renderCase(input), {
          kind, direction, phase: bg * 3, offset: [.25, .5], pan: [.5, .25], background: backgrounds[bg], width: 435.2,
        }));
      }
      for (const direction of 'NESW') for (let bg = 0; bg < 3; bg++) {
        cases.push(await page.evaluate(input => window.renderCase(input), {
          kind: 'independent', direction, phase: bg * 3, offset: [.25, .5], pan: [.5, .25], background: backgrounds[bg], width: 360, context: true,
        }));
        await page.locator('svg').screenshot({ path: path.join(output, `context-${direction}-${bg}.png`) });
      }
      const playback = [];
      for (const direction of 'NESW') for (const kind of ['native', 'independent']) {
        playback.push(await page.evaluate(({ direction, kind }) => window.playLoop(direction, kind, 2.05), { direction, kind }));
      }
      const report = { backend, browserVersion: browser.version(), executable: backend === 'full-chrome' ? chromium.executablePath() : 'Playwright default headless-shell',
        productionFunctionsSHA256: hash(functions), frozenFixtureManifestSHA256: hash(readFileSync(path.join(fixture, 'source/handoff-manifest-round01.json'))),
        method: 'Exact immutable floor consumer fixture; only production pure raster functions supplied by this versioned HTTP override. All original fixture/source/pixels remain unchanged.', cases, playback, errors };
      writeFileSync(path.join(output, 'report.json'), JSON.stringify(report, null, 2) + '\n');
      const summary = { backend, cases: cases.length, alphaFailures: cases.filter(item => item.interiorAlpha.nonOpaque).length, playbackRuns: playback.length, errors };
      reports.push(summary); console.log(JSON.stringify(summary));
      assert.equal(cases.length, 1476); assert.equal(summary.alphaFailures, 0); assert.deepEqual(errors, []);
      assert.ok(playback.every(run => new Set(run.transitions.map(item => item.phase)).size === 12));
    } finally { await browser.close(); }
  }
  writeFileSync(path.join(root, 'summary.json'), JSON.stringify({ reports }, null, 2) + '\n');
} finally { await new Promise(resolve => server.close(resolve)); }
