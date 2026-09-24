// Encode original generated PNGs for delivery without resizing, recoloring or
// compositing. Keep the original RGBA sprite sheets beside the WebP exports.
import { chromium } from '@playwright/test';
import { readFile, writeFile } from 'node:fs/promises';
const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  for (const name of process.argv.slice(2).length ? process.argv.slice(2) : ['rooms-bunny', 'rooms-frog', 'rooms-cat', 'actors', 'props', 'sky', 'sky-paper', 'scenery', 'cardboard-tray', 'dock-paper', 'card-powers', 'card-types']) {
    const png = await readFile(new URL(`${name}.png`, import.meta.url));
    const encoded = await page.evaluate(async data => {
      const image = new Image(); image.src = `data:image/png;base64,${data}`; await image.decode();
      const canvas = document.createElement('canvas'); canvas.width = image.width; canvas.height = image.height;
      canvas.getContext('2d').drawImage(image, 0, 0);
      return canvas.toDataURL('image/webp', .9).split(',')[1];
    }, png.toString('base64'));
    const webp = Buffer.from(encoded, 'base64'); await writeFile(new URL(`${name}.webp`, import.meta.url), webp);
    console.log(`${name}: ${Math.round(png.length / 1024)} → ${Math.round(webp.length / 1024)} KiB`);
  }
} finally { await browser.close(); }
