import { test, expect } from '@playwright/test';
import { existsSync, readFileSync } from 'node:fs';

const manifestPath = new URL('../assets/character-lighting-study/manifest.json', import.meta.url);
const study = existsSync(manifestPath) ? JSON.parse(readFileSync(manifestPath, 'utf8')) : null;
const nestedScrollers = page => page.evaluate(() => [...document.querySelectorAll('body *')].filter(element => /auto|scroll/.test(getComputedStyle(element).overflowY) && element.scrollHeight > element.clientHeight + 2 && element.getClientRects().length && !element.matches('textarea, select')).map(element => element.id || element.className));

for (const [width, height] of [[390, 844], [844, 390], [1440, 1000]]) {
  test(`native character lighting comparison keeps matching scale and one scroller at ${width}px`, async ({ page }, info) => {
    test.skip(!study?.variants?.length, 'Awaiting the isolated native lighting captures');
    await page.setViewportSize({ width, height });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('/prototypes/sushi-loop/?ntl-drawer-state=hidden#character-lighting-study');
    const stage = page.locator('#prototype-stage');
    await expect(stage).toHaveAttribute('data-story', 'character-lighting-study');
    await expect(stage).toHaveClass(/frame--map/);
    await expect(stage).toHaveClass(/frame--document/);
    await expect(stage.locator('.lighting-variant')).toHaveCount(4);
    await expect(stage.locator('.lighting-study-status')).toContainText('16 / 16 native stills');
    await expect(stage.locator('.lighting-pending')).toHaveCount(0);
    await expect(stage.getByRole('link', { name: 'Editable Blender study ↗' })).toBeVisible();
    const frame = study.frame || study.frameSize;
    const captures = stage.locator('.lighting-capture');
    const firstFrame = await captures.first().getAttribute('viewBox');
    expect(firstFrame).toBe([-study.root[0], -study.root[1], ...frame].join(' '));
    for (const direction of ['S', 'E', 'N', 'W']) {
      await stage.getByLabel('Lighting study facing', { exact: true }).selectOption(direction);
      await expect(stage.locator(`.lighting-capture[data-lighting-direction="${direction}"]`)).toHaveCount(4);
      const metadata = await captures.evaluateAll(elements => elements.map(element => [element.getAttribute('viewBox'), element.dataset.frameRoot, element.dataset.cellSize, element.getBoundingClientRect().width, getComputedStyle(element.querySelector('image')).filter]));
      expect(new Set(metadata.map(row => row.slice(0, 3).join('|'))).size).toBe(1);
      expect(new Set(metadata.map(row => row[3].toFixed(3))).size).toBe(1);
      expect(metadata.every(row => row[4] === 'none')).toBe(true);
      const sources = await stage.locator('[data-lighting-source]').evaluateAll(elements => elements.map(element => ({ source: element.dataset.lightingSource, url: element.getAttribute('href') })));
      expect(sources).toHaveLength(4);
      expect(new Set(sources.map(entry => entry.source)).size).toBe(4);
      const decoded = await page.evaluate(async sources => Promise.all(sources.map(({ url }) => new Promise(resolve => { const image = new Image(); image.onload = () => resolve([image.naturalWidth, image.naturalHeight]); image.onerror = () => resolve([0, 0]); image.src = url; }))), sources);
      expect(decoded.every(([w, h]) => w === frame[0] * study.captureScale && h === frame[1] * study.captureScale)).toBe(true);
      if (study.hatCrop) {
        await expect(stage.locator('.lighting-hat-detail')).toHaveCount(4);
        for (const detail of await stage.locator('.lighting-hat-detail').all()) await expect(detail).toHaveAttribute('viewBox', study.hatCrop.join(' '));
      }
      expect(await nestedScrollers(page)).toEqual([]);
    }
    await stage.getByLabel('Tile & root guides', { exact: true }).uncheck();
    await expect(stage.locator('.lighting-ground-guides')).toHaveCount(0);
    await stage.getByLabel('Tile & root guides', { exact: true }).check();
    await expect(stage.locator('.lighting-ground-guides')).toHaveCount(4);
    await stage.getByLabel('Lighting study facing', { exact: true }).selectOption('S');
    await stage.locator('.lighting-comparison').screenshot({ path: info.outputPath(`character-lighting-${width}.png`) });
    await stage.locator('.lighting-concept-reference summary').click();
    const concept = stage.locator('.lighting-concept-reference img');
    await expect(concept).toHaveAttribute('src', /restaurant-concept/);
    await expect(concept).toHaveAttribute('width', '1024');
    await expect(concept).toHaveAttribute('height', '1536');
    expect(await concept.evaluate(element => getComputedStyle(element).filter)).toBe('none');
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 1);
    expect(await nestedScrollers(page)).toEqual([]);
    expect(errors).toEqual([]);
    await page.goto('/prototypes/sushi-loop/?ntl-drawer-state=hidden#object-chef-noor');
    await expect(stage.getByRole('link', { name: 'Compare Noor’s lighting study ↗' })).toHaveAttribute('href', '#character-lighting-study');
  });
}
