import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const root = path.dirname(fileURLToPath(import.meta.url));
const input = path.resolve(root, '../objects/reef-middle/reviews/preparation-v2/evidence/study-direct2x-filter001/native');
const output = path.join(root, 'reef-source-type-controls-v1'); fs.mkdirSync(output, { recursive: true });
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
        for (const [sourceName, png] of [['single', single], ['native', native], ['assembled', assembledPng]]) {
          const copy = document.createElement('canvas'); copy.width = png.width; copy.height = png.height;
          copy.getContext('2d').imageSmoothingEnabled = false; copy.getContext('2d').drawImage(png, 0, 0);
          for (const phase of [0, .25, .5, .75]) {
            const results = [];
            for (const method of ['png-rect', 'png-whole', 'canvas-rect', 'canvas-whole']) {
              const canvas = document.createElement('canvas'); canvas.width = png.width + 4; canvas.height = png.height + 4;
              const context = canvas.getContext('2d'); context.imageSmoothingEnabled = false;
              const src = method.startsWith('png') ? png : copy;
              if (method.endsWith('rect')) context.drawImage(src, 0, 0, png.width, png.height, 2 + phase, 2 + phase, png.width, png.height);
              else context.drawImage(src, 2 + phase, 2 + phase);
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
              cases.push({ sourceName, phase, method, differingPixels, opaqueRGBDifferences, maxRGB, maxAlpha });
            }
          }
        }
        return cases;
      });
      reports.push({ name, executablePath: executablePath || 'Playwright default shell', browserVersion: browser.version(), cases });
      console.log(JSON.stringify({ name, browserVersion: browser.version(), differences: cases.filter(item => item.differingPixels) }));
      assert.equal(cases.length, 48);
    } finally { await browser.close(); }
  }
  fs.writeFileSync(path.join(output, 'report.json'), JSON.stringify({ scope: 'Diagnostic only. Pixel-identical PNG versus integer-copied canvas sources, actual immutable reef captures. No source art or production helper changed.', reports }, null, 2) + '\n');
} finally { await new Promise(resolve => server.close(resolve)); }
