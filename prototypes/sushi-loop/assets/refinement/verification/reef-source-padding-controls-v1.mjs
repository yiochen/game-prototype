import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = path.dirname(fileURLToPath(import.meta.url));
const input = path.resolve(root, '../objects/reef-middle/reviews/preparation-v2/evidence/study-direct2x-filter001/native');
const output = path.join(root, 'reef-source-padding-controls-v1'); fs.mkdirSync(output, { recursive: true });
const server = http.createServer((request, response) => {
  const name = request.url === '/single.png' ? 'single-E.png' : request.url === '/native.png' ? 'three-joined-E.png' : null;
  response.setHeader('Content-Type', name ? 'image/png' : 'text/html');
  response.end(name ? fs.readFileSync(path.join(input, name)) : '<!doctype html><title>Read-only reef source-type controls</title>');
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const browsers = [{ name: 'full-chrome-playwright', executablePath: chromium.executablePath() },
  { name: 'headless-shell' }];
const installed = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
if (fs.existsSync(installed)) browsers.push({ name: 'full-chrome-installed', executablePath: installed });
const reports = [];
try {
  for (const { name, executablePath } of browsers) {
    const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
    try {
      const page = await browser.newPage();
      await page.goto(`http://127.0.0.1:${server.address().port}`);
      const cases = await page.evaluate(async () => {
        const image = async src => { const value = new Image(); value.src = src; await value.decode(); return value; };
        const single = await image('/single.png'), native = await image('/native.png');
        const assembled = document.createElement('canvas'); assembled.width = 896; assembled.height = 1216;
        const ac = assembled.getContext('2d'); ac.imageSmoothingEnabled = false;
        for (const y of [0, 256, 512]) ac.drawImage(single, 256, y);
        const assembledPng = await image(assembled.toDataURL());
        const cases = [];
        const png = native;
        const wide = document.createElement('canvas'); wide.width = png.width; wide.height = png.height;
        wide.getContext('2d').drawImage(png, 0, 0);
        const narrow = document.createElement('canvas'); narrow.width = 384; narrow.height = png.height;
        const nc = narrow.getContext('2d'); nc.imageSmoothingEnabled = false;
        nc.drawImage(png, 256, 0, 384, png.height, 0, 0, 384, png.height);
        const rgba = wide.getContext('2d').getImageData(0, 0, wide.width, wide.height).data;
        let discardedNontransparent = 0;
        for (let y = 0; y < wide.height; y++) for (let x = 0; x < wide.width; x++) {
          if ((x < 256 || x >= 640) && rgba[(y * wide.width + x) * 4 + 3]) discardedNontransparent++;
        }
        if (discardedNontransparent) throw Error('Control crop would discard visible source pixels');
        const narrowPng = await image(narrow.toDataURL());
        for (const phase of [0, .25, .5, .75]) {
          const results = [];
          for (const [method, source, offset] of [['wide-png', png, 0], ['wide-canvas', wide, 0], ['narrow-png', narrowPng, 256], ['narrow-canvas', narrow, 256]]) {
            const canvas = document.createElement('canvas'); canvas.width = png.width + 4; canvas.height = png.height + 4;
            const context = canvas.getContext('2d'); context.imageSmoothingEnabled = false;
            context.drawImage(source, 2 + phase + offset, 2 + phase);
            results.push({ method, rgba: context.getImageData(0, 0, canvas.width, canvas.height).data });
          }
          const expected = results[0].rgba;
          for (const { method, rgba } of results) {
            let differingPixels = 0, opaqueRGBDifferences = 0, maxRGB = 0, maxAlpha = 0;
            for (let i = 0; i < rgba.length; i += 4) {
              let different = false;
              for (let c = 0; c < 4; c++) {
                const delta = Math.abs(expected[i + c] - rgba[i + c]); different ||= delta > 0;
                if (c === 3) maxAlpha = Math.max(maxAlpha, delta);
                else if (expected[i + 3] === 255 && rgba[i + 3] === 255) maxRGB = Math.max(maxRGB, delta);
              }
              if (different) differingPixels++;
              if (expected[i + 3] === 255 && rgba[i + 3] === 255 && [0, 1, 2].some(c => expected[i + c] !== rgba[i + c])) opaqueRGBDifferences++;
            }
            cases.push({ phase, method, differingPixels, opaqueRGBDifferences, maxRGB, maxAlpha, discardedNontransparent });
          }
        }
        return cases;
      });
      reports.push({ name, executablePath: executablePath || 'Playwright default shell', browserVersion: browser.version(), cases });
      console.log(JSON.stringify({ name, browserVersion: browser.version(), differences: cases.filter(item => item.differingPixels) }));
      assert.equal(cases.length, 16);
    } finally { await browser.close(); }
  }
  fs.writeFileSync(path.join(output, 'report.json'), JSON.stringify({ scope: 'Diagnostic only. Identical actual reef pixels with different transparent horizontal padding; placements offset exactly to retain every visible source pixel. Diagnostic copies only; no asset edit. No source art or production helper changed.', reports }, null, 2) + '\n');
} finally { await new Promise(resolve => server.close(resolve)); }
