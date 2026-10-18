import { test, expect } from '@playwright/test';

const url = '/prototypes/sushi-loop/?ntl-drawer-state=hidden#character-scale-study';
const nestedScrollers = page => page.evaluate(() => [...document.querySelectorAll('body *')].filter(element => /auto|scroll/.test(getComputedStyle(element).overflowY) && element.scrollHeight > element.clientHeight + 2 && element.getClientRects().length && !element.matches('textarea, select')).map(element => element.id || element.className));

for (const [width, height] of [[390, 844], [844, 390], [1440, 1000]]) {
  test(`native B/C character study keeps shared tile registration at ${width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(url);
    const stage = page.locator('#prototype-stage');
    await expect(stage).toHaveAttribute('data-story', 'character-scale-study');
    await expect(stage).toHaveClass(/frame--document/);
    await expect(stage.locator('.character-scale-status')).toHaveText('24 / 24 native captures · 2 designs · 3 scales · 4 directions');
    await expect(stage.locator('.character-scale-pending')).toHaveCount(0);
    await expect(stage.locator('[data-character-design]')).toHaveCount(2);
    await expect(stage.locator('[data-character-comparison]')).toHaveCount(6);
    await expect(stage.locator('.character-scale-fit.is-fit')).toHaveCount(6);
    await expect(stage.locator('.character-scale-capture')).toHaveCount(12);
    const roots = await stage.locator('.character-scale-capture>svg').evaluateAll(elements => elements.map(element => element.dataset.frameRoot));
    expect(new Set(roots).size).toBe(1);
    const initialFrames = await stage.locator('.character-scale-capture>svg').evaluateAll(elements => elements.map(element => [element.getAttribute('viewBox'), Number(element.getAttribute('width')), Number(element.getAttribute('height'))]));
    expect(new Set(initialFrames.map(frame => frame.join('|'))).size).toBe(1);
    expect(await stage.locator('.character-scale-capture').evaluateAll(elements => [...new Set(elements.map(element => element.dataset.characterDirection))])).toEqual(['S', 'E']);
    const pan = stage.locator('.character-scale-comparison-scroll');
    await stage.locator('.character-scale-capture').first().scrollIntoViewIfNeeded();
    for (const fraction of [0, .5, 1]) {
      await pan.evaluate((element, part) => { element.scrollLeft = (element.scrollWidth - element.clientWidth) * part; }, fraction);
      await expect.poll(() => stage.locator('.character-scale-capture[data-capture-mounted="true"] image').count()).toBeGreaterThan(0);
    }
    const sourceLinks = await stage.locator('.character-scale-capture figcaption a').filter({ hasText: 'Native PNG' }).evaluateAll(elements => elements.map(element => element.href));
    const decoded = await page.evaluate(async sources => Promise.all(sources.map(src => new Promise(resolve => { const image = new Image(); image.onload = () => resolve([image.naturalWidth, image.naturalHeight]); image.onerror = () => resolve([0, 0]); image.src = src; }))), sourceLinks);
    expect(decoded.every(([w, h], index) => w === initialFrames[index][1] / 64 * 128 * 4 && h === initialFrames[index][2] / 64 * 128 * 4)).toBe(true);
    await stage.getByLabel('Character study tile size', { exact: true }).selectOption('80');
    await expect(stage.locator('.character-scale-capture>svg').first()).toHaveAttribute('data-tile-pitch', '80');
    const smallerFrames = await stage.locator('.character-scale-capture>svg').evaluateAll(elements => elements.map(element => [element.getAttribute('viewBox'), Number(element.getAttribute('width')), Number(element.getAttribute('height'))]));
    smallerFrames.forEach((frame, index) => {
      expect(frame[0]).toBe(initialFrames[index][0]);
      expect(frame[1]).toBeCloseTo(initialFrames[index][1] * 1.25, 5);
      expect(frame[2]).toBeCloseTo(initialFrames[index][2] * 1.25, 5);
    });
    await stage.getByLabel('Character view pair', { exact: true }).selectOption('back');
    expect(await stage.locator('.character-scale-capture').evaluateAll(elements => [...new Set(elements.map(element => element.dataset.characterDirection))])).toEqual(['N', 'W']);
    await expect(stage.locator('.character-scale-capture[data-character-direction="N"]')).toHaveCount(6);
    await expect(stage.locator('.character-scale-capture[data-character-direction="W"]')).toHaveCount(6);
    await stage.getByLabel('Tile & footprint guides', { exact: true }).uncheck();
    await expect(stage.locator('.character-scale-tile-guides')).toHaveCount(0);
    await stage.getByLabel('Tile & footprint guides', { exact: true }).check();
    await stage.getByLabel('Tile layout character design', { exact: true }).selectOption('B');
    await stage.getByLabel('Tile layout character scale', { exact: true }).selectOption('125');
    await stage.getByLabel('Tile layout character facing', { exact: true }).selectOption('E');
    const arrangement = stage.locator('.character-scale-arrangement');
    await expect(arrangement).toHaveAttribute('data-layout-variant', 'B');
    await expect(arrangement).toHaveAttribute('data-layout-scale', '125');
    await expect(arrangement).toHaveAttribute('data-layout-direction', 'E');
    await expect(arrangement.locator('[data-character-placement]')).toHaveCount(9);
    await expect(arrangement).toHaveAttribute('data-tile-pitch', '80');
    expect(await nestedScrollers(page)).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 1);
    await stage.getByLabel('Character view pair', { exact: true }).selectOption('front');
    await pan.evaluate(element => { element.scrollLeft = 0; });
    await pan.screenshot({ path: testInfo.outputPath(`character-scale-comparison-${width}.png`) });
    await arrangement.screenshot({ path: testInfo.outputPath(`character-scale-tiles-${width}.png`) });
    await pan.scrollIntoViewIfNeeded();
    const before = await page.evaluate(() => scrollY);
    await pan.hover();
    await page.mouse.wheel(0, 180);
    await expect.poll(() => page.evaluate(() => scrollY)).toBeGreaterThan(before + 30);
    expect(await pan.evaluate(element => element.scrollTop)).toBe(0);
    expect(await nestedScrollers(page)).toEqual([]);
    expect(errors).toEqual([]);
  });
}
