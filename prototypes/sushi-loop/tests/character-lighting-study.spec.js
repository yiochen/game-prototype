import { test, expect } from '@playwright/test';
import { existsSync, readFileSync } from 'node:fs';

const manifestPath = new URL('../assets/character-lighting-study/manifest.json', import.meta.url);
const study = existsSync(manifestPath) ? JSON.parse(readFileSync(manifestPath, 'utf8')) : null;
const environmentPath = new URL('../assets/faceted-material-refinement/manifest.json', import.meta.url);
const environmentStudy = existsSync(environmentPath) ? JSON.parse(readFileSync(environmentPath, 'utf8')) : null;
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
    await expect(stage.locator('[data-lighting-variant="faceted"] .lighting-selection')).toHaveText('Chosen lighting');
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
    const noorLink = new URL(await stage.getByRole('link', { name: 'Compare Noor’s lighting study ↗' }).getAttribute('href'), page.url());
    expect(noorLink.hash).toBe('#character-lighting-study');
    expect(noorLink.searchParams.get('lightingSubject')).toBe('chef-noor');
  });
}

test('connected lighting animation starts paused, scrubs all native frames in sync and wraps its loop', async ({ page }) => {
  test.skip(!environmentStudy?.subjects?.some(subject => subject.id === 'belt-connected'), 'Awaiting the connected native lighting study');
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await page.goto('/prototypes/sushi-loop/?ntl-drawer-state=hidden#character-lighting-study');
  const stage = page.locator('#prototype-stage');
  await stage.getByLabel('Lighting study subject', { exact: true }).selectOption('belt-connected');
  await expect(stage.getByRole('button', { name: 'Play lighting study animation', exact: true })).toBeVisible();
  const slider = stage.getByRole('slider', { name: 'Lighting study animation frame', exact: true });
  await expect(slider).toHaveValue('0');
  await page.waitForTimeout(250);
  await expect(slider).toHaveValue('0');
  await expect(stage.locator('.lighting-capture[data-frame-index="0"]')).toHaveCount(2);
  const subject = environmentStudy.subjects.find(subject => subject.id === 'belt-connected');
  expect(subject.reviewVariantIds).toEqual(['faceted', 'faceted-tuned']);
  for (let frame = 0; frame < 24; frame++) {
    await slider.fill(String(frame));
    await expect(stage.locator(`.lighting-capture[data-frame-index="${frame}"]`)).toHaveCount(2);
    for (const variant of subject.variants) {
      await expect(stage.locator(`[data-lighting-variant="${variant.id}"] [data-lighting-source]`)).toHaveAttribute('data-lighting-source', variant.captures.S.frames[frame]);
    }
  }
  await stage.getByRole('button', { name: 'Play lighting study animation', exact: true }).click();
  await expect.poll(async () => Number(await slider.inputValue())).toBeLessThan(23);
  await stage.getByRole('button', { name: 'Pause lighting study animation', exact: true }).click();
  const frozen = await slider.inputValue();
  await page.waitForTimeout(150);
  await expect(slider).toHaveValue(frozen);
  await expect(stage.locator(`.lighting-capture[data-frame-index="${frozen}"]`)).toHaveCount(2);
});

test('lighting subject deep links survive reload, preserve other query fields and match object-page links', async ({ page }) => {
  test.skip(!environmentStudy?.subjects?.length, 'Awaiting environment lighting subjects');
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/prototypes/sushi-loop/?ntl-drawer-state=hidden&v=lighting-deep-link&lightingSubject=belt-straight#character-lighting-study');
  const stage = page.locator('#prototype-stage');
  const subject = stage.getByLabel('Lighting study subject', { exact: true });
  await expect(subject).toHaveValue('belt-straight');
  await page.reload();
  await expect(subject).toHaveValue('belt-straight');
  await subject.selectOption('crate-wood');
  const selected = new URL(page.url());
  expect(selected.searchParams.get('lightingSubject')).toBe('crate-wood');
  expect(selected.searchParams.get('ntl-drawer-state')).toBe('hidden');
  expect(selected.searchParams.get('v')).toBe('lighting-deep-link');
  expect(selected.hash).toBe('#character-lighting-study');
  await page.reload();
  await expect(subject).toHaveValue('crate-wood');
  await expect(stage.locator('.lighting-study-status')).toContainText('materials approved');
  await expect(stage.locator('.lighting-study-status')).toContainText('historical captures unchanged');
  await expect(stage).not.toContainText('production unchanged');
  await expect(stage).not.toContainText('pending review');
  await expect(stage.getByRole('region', { name: 'Native Blender surface comparison' })).toHaveCount(1);
  for (const [object, expected] of [['belt-straight-e', 'belt-straight'], ['crate-wood', 'crate-wood'], ['belt-corner-n-e', 'belt-connected'], ['chef-noor', 'chef-noor']]) {
    await page.goto(`/prototypes/sushi-loop/?ntl-drawer-state=hidden&v=lighting-deep-link#object-${object}`);
    const link = stage.locator('.object-lighting-study-link');
    const destination = new URL(await link.getAttribute('href'), page.url());
    expect(destination.searchParams.get('lightingSubject')).toBe(expected);
    expect(destination.searchParams.get('v')).toBe('lighting-deep-link');
    await link.click();
    await expect(subject).toHaveValue(expected);
    await page.reload();
    await expect(subject).toHaveValue(expected);
  }
  await page.goto('/prototypes/sushi-loop/?ntl-drawer-state=hidden&lightingSubject=unknown-subject#character-lighting-study');
  await expect(subject).toHaveValue('chef-noor');
});

for (const [width, height] of [[390, 844], [844, 390], [1440, 1000]]) {
  test(`environment lighting subjects preserve native registration and synchronized conveyor frames at ${width}px`, async ({ page }, info) => {
    test.skip(!environmentStudy?.subjects?.length, 'Awaiting the native environment lighting study');
    await page.setViewportSize({ width, height });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('/prototypes/sushi-loop/?ntl-drawer-state=hidden#character-lighting-study');
    const stage = page.locator('#prototype-stage');
    const subjectSelect = stage.getByLabel('Lighting study subject', { exact: true });
    await expect(subjectSelect.locator('option')).toHaveCount(4);
    for (const subject of environmentStudy.subjects) {
      await subjectSelect.selectOption(subject.id);
      await expect(stage.locator('.character-lighting-study')).toHaveAttribute('data-lighting-subject', subject.id);
      await expect(stage.locator('.lighting-projection-note')).toContainText('70% square-grid environment camera');
      await expect(stage.locator('.lighting-study-status')).toContainText('8 / 8 native stills');
      expect(subject.reviewVariantIds).toEqual(['faceted', 'faceted-tuned']);
      await expect(stage.locator('.lighting-variant')).toHaveCount(2);
      await expect(stage.locator('[data-lighting-variant="faceted"] .lighting-selection')).toHaveText('Chosen lighting');
      await expect(stage.locator('[data-lighting-variant="faceted-tuned"] .lighting-selection')).toHaveText('Approved materials');
      await expect(stage.locator('.lighting-pending')).toHaveCount(0);
      const frame = subject.frame || subject.frameSize;
      const captures = stage.locator('.lighting-capture');
      for (const direction of ['S', 'E', 'N', 'W']) {
        await stage.getByLabel('Lighting study facing', { exact: true }).selectOption(direction);
        await expect(stage.locator(`.lighting-capture[data-lighting-direction="${direction}"]`)).toHaveCount(2);
        for (const capture of await captures.all()) {
          await expect(capture).toHaveAttribute('viewBox', [-subject.root[0], -subject.root[1], ...frame].join(' '));
          await expect(capture).toHaveAttribute('data-frame-root', subject.root.join(' '));
          await expect(capture.locator('[data-lighting-floor]')).toHaveAttribute('width', String(subject.footprint[0] * 128));
          await expect(capture.locator('[data-lighting-floor]')).toHaveAttribute('height', String(subject.footprint[1] * 128));
        }
        const sources = await stage.locator('[data-lighting-source]').evaluateAll(elements => elements.map(element => ({ source: element.dataset.lightingSource, url: element.getAttribute('href'), filter: getComputedStyle(element).filter })));
        expect(sources.every(entry => entry.filter === 'none')).toBe(true);
        expect(new Set(sources.map(entry => entry.source)).size).toBe(2);
        const decoded = await page.evaluate(async sources => Promise.all(sources.map(({ url }) => new Promise(resolve => { const image = new Image(); image.onload = () => resolve([image.naturalWidth, image.naturalHeight]); image.onerror = () => resolve([0, 0]); image.src = url; }))), sources);
        expect(decoded.every(([w, h]) => w === frame[0] * subject.captureScale && h === frame[1] * subject.captureScale)).toBe(true);
        expect(await nestedScrollers(page)).toEqual([]);
      }
      await stage.getByLabel('Lighting study facing', { exact: true }).selectOption('S');
      const frameCount = Math.max(1, ...subject.variants.map(variant => variant.captures?.S?.frames?.length || 1));
      if (frameCount > 1) {
        expect(frameCount).toBe(24);
        const slider = stage.getByRole('slider', { name: 'Lighting study animation frame', exact: true });
        await expect(slider).toHaveAttribute('max', '23');
        await slider.fill('5');
        await expect(stage.locator('.lighting-capture[data-frame-index="5"]')).toHaveCount(2);
        for (const variant of subject.variants) await expect(stage.locator(`[data-lighting-variant="${variant.id}"] [data-lighting-source]`)).toHaveAttribute('data-lighting-source', variant.captures.S.frames[5]);
        await stage.getByRole('button', { name: 'Play lighting study animation', exact: true }).click();
        await expect.poll(() => slider.inputValue()).not.toBe('5');
        await stage.getByRole('button', { name: 'Pause lighting study animation', exact: true }).click();
        const frozen = await slider.inputValue();
        await page.waitForTimeout(150);
        expect(await slider.inputValue()).toBe(frozen);
        await slider.fill('0');
      } else await expect(stage.locator('.lighting-playback')).toHaveCount(0);
      await stage.locator('.lighting-comparison').screenshot({ path: info.outputPath(`environment-lighting-${subject.id}-${width}.png`) });
      if (width === 390 && subject.id === 'crate-wood') await page.screenshot({ fullPage: true, path: info.outputPath('faceted-materials-phone-full-page.png') });
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 1);
    }
    await subjectSelect.selectOption('chef-noor');
    await expect(stage.locator('.lighting-projection-note')).toContainText('35° character camera');
    await expect(stage.locator('.lighting-study-status')).toContainText('16 / 16 native stills');
    expect(errors).toEqual([]);
  });
}
