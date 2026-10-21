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
      await expect(stage.getByRole('link', { name: 'Download .blend ↓', exact: true })).toHaveAttribute('href', `https://raw.githubusercontent.com/yiochen/game-prototype/codex/sushi-loop-33-art-catalog/prototypes/sushi-loop/assets/production/${library.production?.editableProject || object.source.blend}`);
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


for (const id of ['chef-lena', 'customer-rosa']) {
  test(`${id} exposes every real clip in four directions while keeping closed atlases unmounted`, async ({ page }) => {
    const object = objects.find(candidate => candidate.id === id);
    test.skip(!object?.clips?.length, `Awaiting actual ${id} Blender exports`);
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`${url}#object-${id}`);
    const stage = page.locator('#prototype-stage');
    const exportedStates = object.clips.map(clip => clip.id);
    if (object.status === 'ready') for (const required of object.requirements?.states || []) expect(exportedStates).toContain(required);
    await expect(stage.locator('.object-animation')).toHaveCount(object.clips.length);
    const before = await stage.locator('.object-tile-scene').first().locator('[data-sprite-source]').first().evaluate(element => ['x', 'y', 'width', 'height'].map(name => element.getAttribute(name)));
    for (const clip of object.clips) {
      const action = stage.locator(`[data-animation="${clip.id}"]`);
      if (!await action.evaluate(element => element.open)) await action.locator('summary').click();
      await expect(stage.locator('.object-animation[open]')).toHaveCount(1);
      await expect(stage.locator('.object-animation:not([open]) svg')).toHaveCount(0);
      for (const direction of ['N', 'E', 'S', 'W']) {
        await expect(action.locator(`[data-object="${id}"][data-direction="${direction}"] [data-sprite-source]`)).toHaveCount(1);
      }
      const first = stage.locator('.object-tile-scene').first().locator(`[data-object="${id}"][data-direction="N"]`);
      const frames = clip.frames || 1;
      for (const frame of [...new Set([0, Math.floor((frames - 1) / 2), frames - 1])]) {
        await stage.getByRole('slider', { name: 'Animation frame' }).fill(String(frame));
        await expect(first).toHaveAttribute('data-frame', String(frame));
      }
      const after = await first.locator('[data-sprite-source]').evaluate(element => ['x', 'y', 'width', 'height'].map(name => element.getAttribute(name)));
      expect(after, `${clip.id} frame/root registration`).toEqual(before);
      const decoded = await action.locator('svg image').evaluateAll(async elements => Promise.all(elements.map(element => new Promise(resolve => { const image = new Image(); image.onload = () => resolve([image.naturalWidth, image.naturalHeight]); image.onerror = () => resolve([0, 0]); image.src = element.getAttribute('href'); }))));
      for (const [width, height] of decoded) { expect(width).toBeGreaterThan(0); expect(height).toBeGreaterThan(0); }
      const displayed = await stage.locator(`[data-object="${id}"] [data-sprite-source]`).evaluateAll(elements => [...new Set(elements.map(element => element.dataset.spriteSource))]);
      const contextCount = (object.interactions || []).flatMap(scene => scene.placements).filter(placement => placement.object === id).length;
      expect(displayed.length, `${clip.id} should not mount unrelated action atlases`).toBeLessThanOrEqual(4 + contextCount);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(391);
  });
}


test('native library thumbnails mount near the browser viewport and release offscreen atlas nodes', async ({ page }) => {
  const published = objects.filter(object => object.status === 'ready' && object.source?.blend && object.clips?.some(clip => Object.values(clip.directions || {}).some(entry => entry.image)));
  test.skip(published.length < 12, 'Awaiting enough published native objects to exercise offscreen cards');
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto(`${url}#object-library`);
  const stage = page.locator('#prototype-stage');
  await stage.getByRole('combobox', { name: 'Show', exact: true }).selectOption('exported');
  const first = stage.locator(`[data-thumbnail-object="${published[0].id}"]`);
  const last = stage.locator(`[data-thumbnail-object="${published.at(-1).id}"]`);
  await expect(first.locator('[data-thumbnail-source]')).toHaveCount(1);
  await expect(last.locator('svg')).toHaveCount(0);
  await expect(last).toHaveAttribute('data-thumbnail-state', 'deferred');
  const initialSize = await first.evaluate(element => [element.getBoundingClientRect().width, element.getBoundingClientRect().height]);
  expect(await stage.locator('[data-thumbnail-source]').count()).toBeLessThan(published.length / 2);
  await last.scrollIntoViewIfNeeded();
  await expect(last.locator('[data-thumbnail-source]')).toHaveCount(1);
  await expect(first.locator('svg')).toHaveCount(0);
  await expect(first).toHaveAttribute('data-thumbnail-state', 'deferred');
  expect(await first.evaluate(element => [element.getBoundingClientRect().width, element.getBoundingClientRect().height])).toEqual(initialSize);
  expect(await stage.locator('[data-thumbnail-source]').count()).toBeLessThan(published.length / 2);
  await page.evaluate(() => window.scrollTo(0, 0));
  await expect(first.locator('[data-thumbnail-source]')).toHaveCount(1);
  await expect(last.locator('svg')).toHaveCount(0);
  const queued = objects.find(object => !object.clips?.length);
  if (queued) {
    await stage.getByRole('combobox', { name: 'Show', exact: true }).selectOption('queued');
    const preview = stage.locator(`[data-thumbnail-object="${queued.id}"]`);
    await expect(preview).toHaveAttribute('data-thumbnail-state', 'queued');
    await expect(preview.locator('svg')).toHaveCount(0);
  }
});


test('camera-facing effects explain four world-facing contexts while ordinary objects retain directional review', async ({ page }) => {
  const cameraFacing = objects.find(object => object.facingPolicy === 'camera-facing' && object.clips?.length);
  test.skip(!cameraFacing, 'Awaiting native camera-facing effect exports');
  await page.goto(`${url}#object-${cameraFacing.id}`);
  const stage = page.locator('#prototype-stage');
  await expect(stage.locator('.object-facing-policy')).toHaveText('Camera-facing artwork · four world-facing contexts');
  const firstSection = stage.locator('.object-review-section').first();
  await expect(firstSection).toContainText('Four facing contexts: camera-facing artwork stays readable');
  await expect(firstSection.getByRole('img', { name: `${cameraFacing.name}: camera-facing artwork in North, East, South and West world-facing contexts`, exact: true })).toBeVisible();
  for (const direction of ['N', 'E', 'S', 'W']) await expect(firstSection.locator(`[data-object="${cameraFacing.id}"][data-direction="${direction}"]`)).toHaveCount(1);
  const ordinary = objects.find(object => !['camera-facing', 'single-player-facing'].includes(object.facingPolicy) && object.clips?.length);
  await page.goto(`${url}#object-${ordinary.id}`);
  await expect(stage.locator('.object-facing-policy')).toHaveCount(0);
  await expect(stage.locator('.object-review-section').first()).toContainText('Same tile pitch and ground root in every facing.');
});

for (const [width, height] of [[390, 844], [844, 390]]) {
  test(`blank signs and image-generated feedback preserve their declared 2D review policy at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    const stage = page.locator('#prototype-stage');
    for (const id of ['chef-blackboard', 'sign-blank']) {
      await page.goto(`${url}#object-${id}`);
      await expect(stage.locator('.object-facing-policy')).toContainText('Single player-facing surface');
      await expect(stage.getByLabel('Repeated facing', { exact: true }).locator('option')).toHaveCount(1);
      const firstScene = stage.locator('.object-tile-scene').first();
      await expect(firstScene.locator(`[data-object="${id}"]`)).toHaveCount(1);
      await expect(firstScene.locator('[data-direction="S"]')).toHaveCount(1);
      await expect(stage.locator('.object-review-section').first()).toContainText('front-edge placement');
      const interaction = stage.locator('.object-interaction').first();
      await expect(interaction.locator(`[data-object="${id}"]`)).toHaveCount(1);
      await expect(stage.locator('[data-animation^="cucumber-"]')).toHaveCount(0);
      await expect(stage.locator('[data-animation^="eel-"]')).toHaveCount(0);
    }
    await page.goto(`${url}#object-bubble-happy`);
    await expect(stage.getByRole('link', { name: 'Original ImageGen artwork ↗' })).toBeVisible();
    await expect(stage.getByRole('link', { name: 'Editable Blender source ↗' })).toHaveCount(0);
    const firstScene = stage.locator('.object-tile-scene').first();
    const sources = await firstScene.locator('[data-sprite-source]').evaluateAll(elements => elements.map(element => element.dataset.spriteSource));
    expect(sources.length).toBe(4);
    expect(new Set(sources).size).toBe(1);
    await stage.getByRole('slider', { name: 'Animation frame' }).fill('5');
    await expect(firstScene.locator('[data-frame="5"]')).toHaveCount(4);
    await page.goto(`${url}#object-eel-warning-strip`);
    await expect(stage.getByRole('link', { name: 'Editable Godot 2D effect ↗' })).toBeVisible();
    await expect(stage.getByRole('link', { name: 'Editable Blender source ↗' })).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 1);
  });
}

for (const [width, height] of [[320,740],[844,390]]) test(`approved wall and gate replace the retired entrance in the catalog at ${width}px`, async ({page}, testInfo) => {
  await page.setViewportSize({width,height});
  await page.emulateMedia({reducedMotion:'reduce'});
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto(`${url}#object-library`);
  const stage=page.locator('#prototype-stage');
  await expect(stage.locator('a[href="#object-entry-finished"]')).toHaveCount(0);
  for (const id of ['backdrop-wall','backdrop-entrance']) {
    await stage.getByRole('searchbox',{name:'Find an object'}).fill(id);
    await stage.locator(`a[href="#object-${id}"]`).click();
    await expect(stage).toHaveAttribute('data-story',`object-${id}`);
    await expect(stage.getByRole('heading',{name:objects.find(o=>o.id===id).name,exact:true})).toBeVisible();
    await expect(stage).toContainText('uniform');
    await expect(stage.locator('.object-export-pending')).toHaveCount(0);
    await expect(stage.getByRole('combobox',{name:'Repeated facing'}).locator('option')).toHaveCount(1);
    const frames=stage.locator('[data-sprite-source]');
    await expect(frames.first()).toHaveAttribute('data-sprite-source',`sprites/${id}/static-S.png`);
    await frames.locator('image').evaluateAll(async nodes=>Promise.all([...new Set(nodes.map(n=>n.getAttribute('href')))].map(src=>new Promise((resolve,reject)=>{const image=new Image();image.onload=resolve;image.onerror=reject;image.src=src;}))));
    await stage.locator('.object-review-section').first().screenshot({path:testInfo.outputPath(`${id}-${width}.png`)});
    const source=await stage.getByRole('link',{name:'Download .blend ↓',exact:true}).getAttribute('href');
    expect((await page.request.get(source)).ok()).toBe(true);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width+1);
    await stage.getByRole('link',{name:'← Object library',exact:true}).click();
  }
  expect(errors).toEqual([]);
});
