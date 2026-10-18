import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

const url = '/prototypes/sushi-loop/?ntl-drawer-state=hidden';
const library = JSON.parse(await readFile(new URL('../assets/production/library.json', import.meta.url), 'utf8'));
const objects = library.objects;

for (const [width, height] of [[320, 740], [844, 390], [1440, 1000]]) {
  test(`object review has stable pages and contained four-way/3x3/interaction/animation scenes at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(`${url}#object-library`);
    const stage = page.locator('#prototype-stage');
    await expect(stage).toHaveAttribute('data-story', 'object-library');
    await stage.getByRole('combobox', { name: 'Show', exact: true }).selectOption('all');
    await expect(stage.locator('.object-library-card')).toHaveCount(objects.length);
    expect(objects.length).toBeGreaterThan(0);
    const object = objects.find(candidate => candidate.clips?.some(clip => clip.frames > 1)) || objects.find(candidate => candidate.clips?.length) || objects[0];
    await stage.getByRole('searchbox', { name: 'Find an object' }).fill(object.id);
    const link = stage.locator(`a[href="#object-${object.id}"]`);
    await expect(link).toContainText(object.name);
    await link.click();
    await expect(stage).toHaveAttribute('data-story', `object-${object.id}`);
    await expect(stage.getByRole('heading', { name: object.name, exact: true })).toBeVisible();
    if (object.productionStage) await expect(stage).toContainText(object.productionStage);
    if (object.source?.blend) {
      const source = stage.getByRole('link', { name: 'Editable Blender source ↗', exact: true });
      await expect(source).toHaveAttribute('href', `https://github.com/yiochen/game-prototype/blob/codex/sushi-loop-33-art-catalog/prototypes/sushi-loop/assets/production/${object.source.blend}`);
      await expect(source).toHaveAttribute('target', '_blank');
    }
    for (const title of ['Four directions', 'Repeated 3 × 3', 'Interaction & scale', 'Every animation · all directions']) await expect(stage.locator('.object-review-section h3', { hasText: title })).toHaveCount(1);
    const scenes = stage.locator('.object-tile-scene');
    const facings = scenes.first();
    for (const direction of ['N', 'E', 'S', 'W']) await expect(facings.locator(`[data-direction="${direction}"]`)).toHaveCount(1);
    await expect(scenes.nth(1).locator(`[data-object="${object.id}"]`)).toHaveCount(9);
    await stage.getByLabel('Repeated facing', { exact: true }).selectOption('W');
    await expect(scenes.nth(1).locator('[data-direction="W"]')).toHaveCount(9);
    await stage.getByLabel('Scene zoom', { exact: true }).selectOption('2');
    const pan = stage.locator('.object-scene-scroll').first();
    await expect.poll(() => pan.evaluate(element => element.scrollWidth > element.clientWidth)).toBe(true);
    await pan.evaluate(element => { element.scrollLeft = 60; });
    expect(await pan.evaluate(element => element.scrollLeft)).toBeGreaterThan(0);
    await stage.getByLabel('Roots & attachments', { exact: true }).uncheck();
    await expect(stage.locator('.object-root')).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 1);
    await expect(stage.locator('.object-animation')).toHaveCount(object.clips?.length || 0);
    for (const clip of object.clips || []) {
      const animation = stage.locator(`[data-animation="${clip.id}"]`);
      if (!await animation.evaluate(element => element.open)) await animation.locator('summary').click();
      await expect(stage.locator('.object-animation[open]')).toHaveCount(1);
      for (const direction of ['N', 'E', 'S', 'W']) await expect(animation.locator(`[data-direction="${direction}"]`)).toHaveCount(1);
      await expect(stage.locator('.object-animation:not([open]) [data-sprite-source]')).toHaveCount(0);
    }
    const animated = object.clips?.find(clip => clip.frames > 1);
    if (animated) {
      await stage.getByLabel('Scene state', { exact: true }).selectOption(animated.id);
      const slider = stage.getByRole('slider', { name: 'Animation frame' });
      await expect(stage.getByRole('button', { name: 'Play animations' })).toBeVisible();
      await slider.fill('1');
      await expect(facings.locator(`[data-object="${object.id}"][data-frame]`).first()).toHaveAttribute('data-frame', '1');
      await stage.getByRole('button', { name: 'Play animations' }).click();
      await expect(stage.getByRole('button', { name: 'Pause animations' })).toBeVisible();
      await stage.getByRole('button', { name: 'Pause animations' }).click();
      const frozen = await slider.inputValue();
      await page.waitForTimeout(200);
      expect(await slider.inputValue()).toBe(frozen);
    }
    for (const source of await stage.locator('[data-sprite-source]').evaluateAll(elements => elements.map(element => element.dataset.spriteSource))) expect(source).not.toMatch(/concept|catalog-v0/i);
    const imageResults = await stage.locator('svg image').evaluateAll(async elements => Promise.all([...new Set(elements.map(element => element.getAttribute('href')))].map(src => new Promise(resolve => { const image = new Image(); image.onload = () => resolve({ src, width: image.naturalWidth, height: image.naturalHeight }); image.onerror = () => resolve({ src, width: 0, height: 0 }); image.src = src; }))));
    for (const image of imageResults) { expect(image.width, image.src).toBeGreaterThan(0); expect(image.height, image.src).toBeGreaterThan(0); }
    await page.reload();
    await expect(stage).toHaveAttribute('data-story', `object-${object.id}`);
    expect(errors).toEqual([]);
  });
}

test('queued objects stay explicitly pending, and comments keep the exact object deep link', async ({ page }) => {
  const queued = objects.find(object => !object.clips?.length);
  test.skip(!queued, 'All objects already have native exports');
  await page.goto(`${url}#object-${queued.id}`);
  const stage = page.locator('#prototype-stage');
  await expect(stage).toContainText('queued for Blender export');
  await expect(stage.locator('[data-sprite-source]')).toHaveCount(0);
  await page.getByRole('button', { name: 'Comments', exact: true }).click();
  const feedback = page.locator('.feedback-section');
  await feedback.getByLabel('What would you change?').fill('Review the four directions and ground anchor.');
  await feedback.getByRole('button', { name: 'Add comment', exact: true }).click();
  const link = new URL(await feedback.getByRole('link', { name: /Open GitHub feedback form/ }).getAttribute('href'));
  expect(link.searchParams.get('body')).toContain(`#object-${queued.id}`);
  expect(link.searchParams.get('body')).toContain('codex/sushi-loop-33-art-catalog');
});

test('a static prop page can play and scrub its animated interaction partner independently', async ({ page }) => {
  const object = objects.find(candidate => candidate.clips?.length && candidate.clips.every(clip => clip.frames === 1) && candidate.interactions?.some(interaction => interaction.placements.some(placement => {
    const related = objects.find(entry => entry.id === placement.object);
    return related?.clips?.find(clip => clip.id === placement.clip)?.frames > 1;
  })));
  test.skip(!object, 'Awaiting a static prop with an exported animated interaction partner');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto(`${url}#object-${object.id}`);
  const stage = page.locator('#prototype-stage');
  await expect(stage.getByRole('button', { name: 'Play animations' })).toBeEnabled();
  await stage.getByRole('slider', { name: 'Animation frame' }).fill('1');
  const own = stage.locator('.object-tile-scene').first().locator(`[data-object="${object.id}"][data-frame]`).first();
  await expect(own).toHaveAttribute('data-frame', '0');
  const animated = stage.locator('.object-interaction [data-frame="1"]');
  expect(await animated.count()).toBeGreaterThan(0);
  await stage.getByRole('button', { name: 'Play animations' }).click();
  await expect(stage.getByRole('button', { name: 'Pause animations' })).toBeVisible();
});
