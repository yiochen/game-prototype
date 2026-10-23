import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import http from 'node:http';
import { chromium } from 'playwright';

const atlas = new URL('../objects/floor-underwater/candidates/round-01/atlases/scroll-N.png', import.meta.url);
const output = new URL('./fractional-atlas-controls/', import.meta.url);
mkdirSync(output, { recursive: true });
const bytes = readFileSync(atlas);
const server = http.createServer((request, response) => {
  response.setHeader('Content-Type', request.url === '/atlas.png' ? 'image/png' : 'text/html');
  response.end(request.url === '/atlas.png' ? bytes : '<!doctype html><title>Fractional atlas controls</title>');
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const binary = '/Users/yiouchen/Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing';
const results = [];
try {
  for (const backend of ['full-chrome', 'headless-shell']) {
    const browser = await chromium.launch({ headless: true,
      ...(backend === 'full-chrome' ? { executablePath: binary } : {}) });
    try {
      const page = await browser.newPage({ viewport: { width: 1200, height: 1200 }, deviceScaleFactor: 1 });
      await page.goto(`http://127.0.0.1:${server.address().port}`);
      const cases = await page.evaluate(async () => {
        const image = new Image();
        image.src = '/atlas.png';
        await image.decode();
        const frame = document.createElement('canvas');
        frame.width = frame.height = 256;
        frame.getContext('2d').imageSmoothingEnabled = false;
        frame.getContext('2d').drawImage(image, 0, 0, 256, 256, 0, 0, 256, 256);
        const bitmap = await createImageBitmap(image, 0, 0, 256, 256);
        const layer = document.createElement('canvas');
        layer.width = layer.height = 768;
        const layerContext = layer.getContext('2d');
        layerContext.imageSmoothingEnabled = false;
        for (let row = 0; row < 3; row++) for (let column = 0; column < 3; column++) {
          layerContext.drawImage(image, 0, 0, 256, 256, column * 256, row * 256, 256, 256);
        }
        const output = [];
        for (const [fx, fy] of [[0, 0], [.25, .75], [.5, 0], [.75, .25]]) {
          for (const method of ['atlas-subrect', 'frame-canvas', 'frame-canvas-whole-rect', 'image-bitmap', 'integer-composed-layer']) {
            const canvas = document.createElement('canvas');
            canvas.width = canvas.height = 874;
            const context = canvas.getContext('2d');
            context.imageSmoothingEnabled = false;
            for (let row = 0; row < 3; row++) for (let column = 0; column < 3; column++) {
              const x = 52 + fx + column * 256, y = 52 + fy + row * 256;
              if (method === 'atlas-subrect') context.drawImage(image, 0, 0, 256, 256, x, y, 256, 256);
              if (method === 'frame-canvas') context.drawImage(frame, x, y);
              if (method === 'frame-canvas-whole-rect') context.drawImage(frame, 0, 0, 256, 256, x, y, 256, 256);
              if (method === 'image-bitmap') context.drawImage(bitmap, x, y);
            }
            if (method === 'integer-composed-layer') context.drawImage(layer, 52 + fx, 52 + fy);
            const data = context.getImageData(54, 54, 764, 764).data;
            let minimumAlpha = 255, nonOpaque = 0;
            for (let index = 3; index < data.length; index += 4) {
              minimumAlpha = Math.min(minimumAlpha, data[index]);
              if (data[index] !== 255) nonOpaque++;
            }
            output.push({ method, fx, fy, minimumAlpha, nonOpaque });
          }
        }
        bitmap.close();
        return output;
      });
      results.push({ backend, version: browser.version(), cases });
    } finally { await browser.close(); }
  }
  const report = { sourceAtlasSHA256: createHash('sha256').update(bytes).digest('hex'),
    scope: 'Renderer controls only. No approved source pixels, geometry, registration or shared helper changed.', results };
  writeFileSync(new URL('results.json', output), JSON.stringify(report, null, 2) + '\n');
  for (const result of results) {
    console.log(JSON.stringify({ backend: result.backend,
      failed: result.cases.filter(item => item.nonOpaque).map(({ method, fx, fy, minimumAlpha, nonOpaque }) => ({ method, fx, fy, minimumAlpha, nonOpaque })) }));
  }
  assert.ok(results.every(result => result.cases.length === 20));
} finally { await new Promise(resolve => server.close(resolve)); }
