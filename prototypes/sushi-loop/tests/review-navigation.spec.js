import { test, expect } from '@playwright/test';
const url = '/prototypes/sushi-loop/?ntl-drawer-state=hidden';
for (const [width, height] of [[390, 844], [844, 390], [1325, 1224]]) {
  test(`object navigation keeps feedback attached to each object at ${width}`, async ({ page }, info) => {
    await page.setViewportSize({ width, height });
    await page.goto(`${url}#object-chef-blackboard`);
    const stage = page.locator('#prototype-stage');
    const objects = await page.locator('#example-select option').evaluateAll(options => options.filter(option => option.value.startsWith('object-') && option.value !== 'object-library').map(option => option.value));
    const index = objects.indexOf('object-chef-blackboard');
    const neighbor = objects[index + 1];
    const previous = page.getByRole('button', { name: 'Previous object', exact: true });
    const next = page.getByRole('button', { name: 'Next object', exact: true });
    await page.getByRole('button', { name: 'Comments', exact: true }).click();
    const feedback = page.locator('.feedback-section');
    const draft = feedback.getByLabel('What would you change?', { exact: true });
    await draft.fill('Blackboard draft stays with this object.');
    await next.click();
    await expect(stage).toHaveAttribute('data-story', neighbor);
    await expect(draft).toHaveValue('');
    expect(await page.evaluate(() => window.scrollY)).toBe(0);
    await draft.fill('Separate review for the next object.');
    await feedback.getByRole('button', { name: 'Add comment', exact: true }).click();
    await previous.click();
    await expect(stage).toHaveAttribute('data-story', 'object-chef-blackboard');
    await expect(draft).toHaveValue('Blackboard draft stays with this object.');
    await expect(feedback.locator('.feedback-comment-text')).toHaveCount(0);
    await next.click();
    await expect(feedback.locator('.feedback-comment-text')).toHaveText('Separate review for the next object.');
    await page.reload();
    await page.getByRole('button', { name: 'Comments', exact: true }).click();
    await expect(feedback.locator('.feedback-comment-text')).toHaveText('Separate review for the next object.');
    await page.goto(`${url}#${objects[0]}`);
    await previous.click();
    await expect(stage).toHaveAttribute('data-story', objects.at(-1));
    await next.click();
    await expect(stage).toHaveAttribute('data-story', objects[0]);
    await expect(page.locator('.example-position')).toHaveText(`1 / ${objects.length}`);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 1);
    for (const button of [previous, next]) {
      const box = await button.boundingBox();
      expect(box.height).toBeGreaterThanOrEqual(44);
      expect(box.x).toBeGreaterThanOrEqual(0);
      expect(box.x + box.width).toBeLessThanOrEqual(width);
    }
    await page.locator('.preview-toolbar').screenshot({ path: info.outputPath(`review-navigation-${width}.png`) });
  });
}
