import { test, expect } from '@playwright/test';

for (const viewport of [{ width: 390, height: 844 }, { width: 844, height: 390 }]) {
  test(`Android exhibition page fits ${viewport.width}×${viewport.height}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    const failed = [];
    page.on('response', response => { if (response.status() >= 400) failed.push(response.url()); });
    await page.goto('/prototypes/sushi-loop/');
    await expect(page.getByRole('heading', { name: /A little kitchen/ })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Three little voyages.' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Sunlit Shallows' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Coral Current' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Lantern Trench' })).toBeVisible();
    await page.evaluate(() => document.fonts.ready);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    expect(await page.locator('img').evaluateAll(images => images.every(image => image.complete && image.naturalWidth > 0))).toBe(true);
    await page.getByRole('link', { name: /Get ready to play/ }).click();
    await expect(page).toHaveURL(/#install$/);
    await expect(page.getByText('The Android APK is provided in the private Google Drive handoff.')).toBeVisible();
    expect(await page.locator('a[href$=".apk"]').count()).toBe(0);
    expect(errors).toEqual([]);
    expect(failed).toEqual([]);
  });
}

test('homepage registers the native Android exhibition', async ({ page }) => {
  await page.goto('/');
  const game = page.locator('a.prototype[href="./prototypes/sushi-loop/"]');
  await expect(game).toContainText('Sushi Loop');
  await expect(game).toContainText('Android');
  await game.click();
  await expect(page).toHaveURL(/prototypes\/sushi-loop\/$/);
});
