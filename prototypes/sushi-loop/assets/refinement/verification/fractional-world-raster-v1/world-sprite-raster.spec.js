import { test, expect, chromium } from '@playwright/test';
import { readFileSync } from 'node:fs';

const source = readFileSync(new URL('../wireframe/world-sprite-raster.js', import.meta.url), 'utf8');
// Exercise the production planning and painting functions in a real browser.
// The hook's React integration is covered by the composed-scene tests.
const rasterFunctions = source.slice(source.indexOf('export function worldRasterPlan'), source.indexOf('export function useWorldSpriteRaster')).replaceAll('export function', 'function');

for (const backend of ['full-chrome', 'headless-shell']) {
  test(`fractional atlas joins and intervening actor order survive in ${backend}`, async () => {
    const browser = await chromium.launch({ headless: true,
      ...(backend === 'full-chrome' ? { executablePath: chromium.executablePath() } : {}) });
    try {
      const page = await browser.newPage();
      await page.setContent('<body></body>');
      await page.addScriptTag({ content: rasterFunctions });
      const results = await page.evaluate(async () => {
        const atlas = document.createElement('canvas');
        atlas.width = 96; atlas.height = 32;
        const ctx = atlas.getContext('2d');
        for (const [column, color] of ['#e04320', '#38a9bd', '#baa246'].entries()) {
          ctx.fillStyle = color; ctx.fillRect(column * 32, 0, 32, 32);
          ctx.fillStyle = '#cbeef0'; ctx.fillRect(column * 32 + 3, 4, 19, 3);
        }
        const image = new Image(); image.src = atlas.toDataURL(); await image.decode();
        const actor = document.createElement('canvas'); actor.width = actor.height = 32;
        actor.getContext('2d').fillStyle = '#e0608080'; actor.getContext('2d').fillRect(2, 2, 28, 28);
        const output = document.createElement('canvas'), results = [];
        for (const [phase, offset] of [[0, 0], [.125, .375], [.25, .5], [.5, .25]].entries()) {
          const rect = [(phase % 3) * 32, 0, 32, 32];
          const tiles = Array.from({ length: 9 }, (_, i) => ({
            rect, x: offset[0] + i % 3 * 16, y: offset[1] + Math.floor(i / 3) * 16, width: 16, height: 16,
          }));
          // A differently phased actor must split groups. A later tile-phased
          // actor stays above it; collecting all equal phases would reorder it.
          const actors = [
            { rect: [0, 0, 32, 32], x: offset[0] + 12.125, y: offset[1] + 12.375, width: 16, height: 16 },
            { rect: [0, 0, 32, 32], x: offset[0] + 16, y: offset[1] + 16, width: 16, height: 16 },
          ];
          const sprites = [...tiles, ...actors], plan = worldRasterPlan(sprites, [-8, -8, 64, 64]);
          paintWorldRaster(output, plan, [...tiles.map(() => image), actor, image]);
          const layer = document.createElement('canvas'); layer.width = layer.height = 96;
          const lc = layer.getContext('2d'); lc.imageSmoothingEnabled = false;
          for (let i = 0; i < 9; i++) lc.drawImage(image, ...rect, i % 3 * 32, Math.floor(i / 3) * 32, 32, 32);
          const reference = document.createElement('canvas'); reference.width = plan.width; reference.height = plan.height;
          const rc = reference.getContext('2d'); rc.imageSmoothingEnabled = false;
          rc.drawImage(layer, (offset[0] - plan.x) * 2, (offset[1] - plan.y) * 2);
          for (const [i, sprite] of actors.entries()) rc.drawImage(i ? image : actor, ...sprite.rect,
            (sprite.x - plan.x) * 2, (sprite.y - plan.y) * 2, 32, 32);
          const actual = output.getContext('2d').getImageData(0, 0, output.width, output.height).data;
          const expected = rc.getImageData(0, 0, reference.width, reference.height).data;
          let differences = 0;
          for (let i = 0; i < actual.length; i++) if (actual[i] !== expected[i]) differences++;
          const interior = output.getContext('2d').getImageData(Math.ceil((offset[0] - plan.x) * 2) + 1,
            Math.ceil((offset[1] - plan.y) * 2) + 1, 93, 93).data;
          let nonOpaque = 0;
          for (let i = 3; i < interior.length; i += 4) if (interior[i] !== 255) nonOpaque++;
          results.push({ offset, differences, nonOpaque });
        }
        return results;
      });
      for (const result of results) {
        expect(result.differences, JSON.stringify(result)).toBe(0);
        expect(result.nonOpaque, JSON.stringify(result)).toBe(0);
      }
    } finally { await browser.close(); }
  });
}

test('fractional world placement preserves native coverage after canvas resize', async ({ page }) => {
  await page.setContent('<body></body>');
  await page.addScriptTag({ content: rasterFunctions });
  const results = await page.evaluate(() => {
    const tile = document.createElement('canvas');
    tile.width = tile.height = 128;
    const results = [];
    for (const axis of ['x', 'y']) for (const phase of [0, 0.25, 0.5, 0.75]) {
      const tileContext = tile.getContext('2d');
      tileContext.clearRect(0, 0, 128, 128);
      tileContext.fillStyle = '#c79551';
      // Real registered sprites have transparent padding. The opaque regions
      // touch while the complete source frames overlap by their padding.
      tileContext.fillRect(axis === 'x' ? 1 : 0, axis === 'y' ? 1 : 0,
        axis === 'x' ? 126 : 128, axis === 'y' ? 126 : 128);
      const sprites = [0, 63, 126].map(offset => ({
        rect: [0, 0, 128, 128], x: phase, y: phase, width: 64, height: 64,
        [axis]: phase + offset,
      }));
      const plan = worldRasterPlan(sprites, [-16, -16, 240, 240]);
      const canvas = document.createElement('canvas');
      // Both dimension changes reset context state. Painting must restore it.
      canvas.width = canvas.height = 1;
      canvas.getContext('2d').imageSmoothingEnabled = true;
      paintWorldRaster(canvas, plan, [tile, tile, tile]);
      const whole = document.createElement('canvas');
      whole.width = axis === 'x' ? 380 : 128;
      whole.height = axis === 'y' ? 380 : 128;
      whole.getContext('2d').fillStyle = '#c79551';
      whole.getContext('2d').fillRect(axis === 'x' ? 1 : 0, axis === 'y' ? 1 : 0,
        whole.width - (axis === 'x' ? 2 : 0), whole.height - (axis === 'y' ? 2 : 0));
      const reference = document.createElement('canvas');
      reference.width = canvas.width; reference.height = canvas.height;
      const context = reference.getContext('2d');
      context.imageSmoothingEnabled = false;
      context.drawImage(whole, (phase - plan.x) * plan.scale, (phase - plan.y) * plan.scale);
      const expected = context.getImageData(0, 0, reference.width, reference.height).data;
      const actual = canvas.getContext('2d').getImageData(0, 0, canvas.width, canvas.height).data;
      let differences = 0;
      for (let i = 0; i < actual.length; i++) if (actual[i] !== expected[i]) differences++;
      // Positive control: interpolating the individual fractional edges creates
      // source-over undercoverage even though their authored positions touch.
      context.clearRect(0, 0, reference.width, reference.height);
      context.imageSmoothingEnabled = true;
      for (const sprite of sprites) context.drawImage(tile, ...sprite.rect,
        (sprite.x - plan.x) * plan.scale, (sprite.y - plan.y) * plan.scale, 128, 128);
      const filtered = context.getImageData(0, 0, reference.width, reference.height).data;
      let coverageLoss = 0;
      for (let i = 3; i < filtered.length; i += 4) if (expected[i] === 255 && filtered[i] < 255) coverageLoss++;
      results.push({ axis, phase, differences, coverageLoss, smoothing: canvas.getContext('2d').imageSmoothingEnabled });
    }
    return results;
  });
  for (const result of results) {
    expect(result.differences, JSON.stringify(result)).toBe(0);
    expect(result.smoothing).toBe(false);
  }
  expect(results.filter(result => result.coverageLoss > 0)).toHaveLength(4);
});

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
