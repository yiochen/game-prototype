import { test, expect } from '@playwright/test';

const url = '/prototypes/sushi-loop/?ntl-drawer-state=hidden';
const verticalScrollers = page => page.evaluate(() => [...document.querySelectorAll('body *')].filter(element => {
  const style = getComputedStyle(element);
  return /auto|scroll/.test(style.overflowY) && element.scrollHeight > element.clientHeight + 2 && element.getClientRects().length && !element.matches('textarea, select');
}).map(element => element.id || element.className));

for (const [width, height] of [[390, 844], [844, 390], [1440, 1000]]) {
  test(`review routes use one document scroller at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height });
    await page.emulateMedia({ reducedMotion: 'reduce' });
    for (const story of ['object-library', 'object-customer-rosa', 'art-catalog', 'concept-doodle-catalog', 'component-paper-page', 'component-receipt', 'shop', 'workshop', 'recipe-picker', 'staff-detail', 'floor-plan', 'restaurant-edit']) {
      await page.goto(`${url}#${story}`);
      const stage = page.locator('#prototype-stage');
      await expect(stage).toHaveAttribute('data-story', story);
      expect(await verticalScrollers(page), story).toEqual([]);
      expect(await page.evaluate(() => document.documentElement.scrollWidth), story).toBeLessThanOrEqual(width + 1);
      expect(await page.evaluate(() => document.scrollingElement.scrollHeight), story).toBeGreaterThan(height);
    }
    await page.goto(`${url}#object-customer-rosa`);
    const scene = page.locator('.object-scene-scroll').first();
    await scene.scrollIntoViewIfNeeded();
    const before = await page.evaluate(() => scrollY);
    await scene.hover();
    await page.mouse.wheel(0, 220);
    await expect.poll(() => page.evaluate(() => scrollY)).toBeGreaterThan(before + 50);
    expect(await scene.evaluate(element => element.scrollTop)).toBe(0);
    // Zoomed artwork still pans horizontally while vertical wheel input reaches the page.
    await page.getByLabel('Scene zoom', { exact: true }).selectOption('2');
    await scene.scrollIntoViewIfNeeded();
    await scene.hover();
    await page.mouse.wheel(180, 0);
    await expect.poll(() => scene.evaluate(element => element.scrollLeft)).toBeGreaterThan(0);
    const zoomTop = await page.evaluate(() => scrollY);
    await page.mouse.wheel(0, 180);
    await expect.poll(() => page.evaluate(() => scrollY)).toBeGreaterThan(zoomTop + 30);
    expect(await verticalScrollers(page)).toEqual([]);
  });
}

async function swipeUp(client, x, y) {
  await client.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] });
  for (let step = 1; step <= 6; step++) {
    await client.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x, y: y - step * 26 }] });
    await new Promise(resolve => setTimeout(resolve, 30));
  }
  await client.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
}

test('phone swipes scroll the page over the object library, sprites, and wide floor plan', async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, reducedMotion: 'reduce' });
  const page = await context.newPage();
  const client = await context.newCDPSession(page);
  for (const [story, selector] of [['object-library', '.object-library-card'], ['object-customer-rosa', '.object-scene-scroll'], ['floor-plan', '.plan-scroll']]) {
    await page.goto(`${url}#${story}`);
    const target = page.locator(selector).first();
    await target.scrollIntoViewIfNeeded();
    const bounds = await target.boundingBox();
    const x = Math.min(350, Math.max(40, bounds.x + bounds.width / 2));
    const y = Math.min(720, Math.max(350, bounds.y + Math.min(bounds.height - 12, 210)));
    const before = await page.evaluate(() => scrollY);
    await swipeUp(client, x, y);
    await expect.poll(() => page.evaluate(() => scrollY), { message: `${story} swipe reaches document` }).toBeGreaterThan(before + 30);
    expect(await verticalScrollers(page), story).toEqual([]);
  }
  await context.close();
});

test('mobile example navigation expands in page flow without a second scroller or body lock', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await page.goto(`${url}#object-library`);
  await page.getByRole('button', { name: 'Examples', exact: true }).click();
  const navigation = page.getByRole('complementary', { name: 'Wireframe examples' });
  await expect(navigation).toBeVisible();
  expect(await navigation.evaluate(element => getComputedStyle(element).position)).toBe('static');
  expect(await page.evaluate(() => getComputedStyle(document.body).overflowY)).not.toBe('hidden');
  await navigation.getByRole('searchbox').fill('recipe');
  const before = await page.evaluate(() => scrollY);
  await navigation.getByRole('searchbox').hover();
  await page.mouse.wheel(0, 200);
  await expect.poll(() => page.evaluate(() => scrollY)).toBeGreaterThan(before);
  expect(await verticalScrollers(page)).toEqual([]);
  await navigation.getByRole('link', { name: 'Picker · chef tier too low', exact: true }).click();
  await expect(navigation).not.toBeVisible();
  await expect(page.locator('#prototype-stage')).toHaveAttribute('data-story', 'recipe-unavailable');
  await expect(page.locator('#story-title')).toBeInViewport();
});


test('far-down library navigation opens the object header, Back restores position, and review controls do not jump', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto(`${url}#object-library`);
  const card = page.locator('.object-library-card').last();
  const destination = (await card.getAttribute('href')).slice(1);
  await card.scrollIntoViewIfNeeded();
  const libraryTop = await page.evaluate(() => scrollY);
  expect(libraryTop).toBeGreaterThan(1500);
  await card.click();
  await expect(page.locator('#prototype-stage')).toHaveAttribute('data-story', destination);
  await expect(page.locator('#story-title')).toBeInViewport();
  expect(await page.evaluate(() => scrollY)).toBeLessThan(300);
  await page.goBack();
  await expect(page.locator('#prototype-stage')).toHaveAttribute('data-story', 'object-library');
  await expect.poll(() => page.evaluate(() => scrollY)).toBeCloseTo(libraryTop, 0);

  await page.evaluate(() => scrollTo(0, 0));
  const beforeFilter = await page.evaluate(() => scrollY);
  await page.getByRole('searchbox', { name: 'Find an object' }).fill('customer-rosa');
  expect(await page.evaluate(() => scrollY)).toBe(beforeFilter);
  await page.locator('a[href="#object-customer-rosa"]').filter({ has: page.locator('.object-library-card-text') }).click();
  const slider = page.getByRole('slider', { name: 'Animation frame' });
  await slider.scrollIntoViewIfNeeded();
  const beforeScrub = await page.evaluate(() => scrollY);
  await slider.fill('1');
  expect(await page.evaluate(() => scrollY)).toBe(beforeScrub);
  await page.getByRole('button', { name: 'Play animations', exact: true }).click();
  await page.getByRole('button', { name: 'Pause animations', exact: true }).click();
  expect(await page.evaluate(() => scrollY)).toBe(beforeScrub);
});
