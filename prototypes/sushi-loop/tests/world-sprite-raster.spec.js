import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';

const source = readFileSync(new URL('../wireframe/world-sprite-raster.js', import.meta.url), 'utf8');
// Exercise the production planning and painting functions in a real browser.
// The hook's React integration is covered by the composed-scene tests.
const rasterFunctions = source.slice(source.indexOf('export function worldRasterPlan'), source.indexOf('export function useWorldSpriteRaster')).replaceAll('export function', 'function');

test('joined native tiles stay continuous through fractional scaling and camera phases', async ({ page }) => {
  await page.setViewportSize({ width: 900, height: 600 });
  await page.setContent('<svg xmlns="http://www.w3.org/2000/svg" style="display:block;background:#808080;overflow:hidden" viewBox="-32 -32 448 192"></svg>');
  await page.addScriptTag({ content: rasterFunctions });
  await page.evaluate(async () => {
    const tile = document.createElement('canvas');
    tile.width = tile.height = 256;
    tile.getContext('2d').fillStyle = '#3598d0';
    tile.getContext('2d').fillRect(0, 0, 256, 256);
    const image = new Image();
    image.src = tile.toDataURL();
    await image.decode();
    const sprites = [0, 128, 256].map(x => ({ rect: [0, 0, 256, 256], x, y: 0, width: 128, height: 128 }));
    const plan = worldRasterPlan(sprites, [-32, -32, 448, 192]);
    const canvas = document.createElement('canvas');
    paintWorldRaster(canvas, plan, [image, image, image]);
    const continuous = document.createElement('canvas');
    continuous.width = canvas.width; continuous.height = canvas.height;
    continuous.getContext('2d').fillStyle = '#3598d0';
    continuous.getContext('2d').fillRect(-plan.x * plan.scale, -plan.y * plan.scale, 384 * plan.scale, 128 * plan.scale);
    window.rasterFixture = { image, canvas, continuous, plan };
    window.showRaster = mode => {
      const svg = document.querySelector('svg');
      svg.replaceChildren();
      if (mode === 'separate') {
        for (const x of [0, 128, 256]) {
          const node = document.createElementNS(svg.namespaceURI, 'image');
          for (const [key, value] of Object.entries({ href: image.src, x, y: 0, width: 128, height: 128 })) node.setAttribute(key, value);
          svg.append(node);
        }
      } else {
        const node = document.createElementNS(svg.namespaceURI, 'foreignObject');
        for (const [key, value] of Object.entries({ x: plan.x, y: plan.y, width: plan.width / plan.scale, height: plan.height / plan.scale })) node.setAttribute(key, value);
        const drawn = mode === 'continuous' ? continuous : canvas;
        drawn.style.cssText = 'display:block;width:100%;height:100%';
        node.append(drawn); svg.append(node);
      }
    };
  });
  let originalFailures = 0;
  for (const pitch of [128, 32, 47.3]) for (const [x, y] of [[0.25, 0.5], [0.5, 0.75], [0.75, 0.25]]) {
    await page.locator('svg').evaluate((svg, { pitch, x, y }) => {
      svg.style.width = `${448 * pitch / 128}px`; svg.style.height = `${192 * pitch / 128}px`;
      svg.style.transform = `translate(${x}px,${y}px)`;
    }, { pitch, x, y });
    await page.evaluate(() => window.showRaster('continuous'));
    const expected = await page.locator('svg').screenshot();
    await page.evaluate(() => window.showRaster('composed'));
    expect((await page.locator('svg').screenshot()).equals(expected), `${pitch}px pitch, phase ${x},${y}`).toBe(true);
    await page.evaluate(() => window.showRaster('separate'));
    if (!(await page.locator('svg').screenshot()).equals(expected)) originalFailures++;
  }
  // Positive control: this fixture must expose the old per-image alpha seam.
  expect(originalFailures).toBeGreaterThan(0);
});
