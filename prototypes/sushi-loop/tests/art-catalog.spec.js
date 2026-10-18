import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';

const url = '/prototypes/sushi-loop/?ntl-drawer-state=hidden#art-catalog';

test('world concept catalog keeps zoom and all 17 item families usable at phone, landscape and desktop sizes', async ({ page }) => {
  for (const [width, height] of [[320, 740], [844, 390], [1440, 1000]]) {
    await page.setViewportSize({ width, height });
    await page.goto(url);
    const stage = page.locator('#prototype-stage');
    await expect(stage).toHaveAttribute('data-story', 'art-catalog');
    await expect(stage).toContainText('CONCEPT APPROVAL PENDING');
    const image = stage.getByRole('img', { name: /^Issue 33 low-poly/ });
    await expect.poll(() => image.evaluate(el => el.complete && el.naturalWidth)).toBe(1024);
    const scroller = stage.getByLabel('Scroll world concept sheet', { exact: true });
    await expect.poll(() => scroller.evaluate(el => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
    await stage.getByRole('button', { name: 'Zoom sheet', exact: true }).click();
    expect(await scroller.evaluate(el => el.scrollWidth > el.clientWidth)).toBe(true);
    await scroller.evaluate(el => { el.scrollLeft = 200; });
    expect(await scroller.evaluate(el => el.scrollLeft)).toBeGreaterThan(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 1);
    await stage.getByRole('button', { name: 'Fit sheet', exact: true }).click();
    await expect.poll(() => scroller.evaluate(el => el.scrollWidth <= el.clientWidth + 1)).toBe(true);
    await mkdir('artifacts/sushi-loop', { recursive: true });
    await stage.screenshot({ path: `artifacts/sushi-loop/art-catalog-sheet-${width}.png` });
    await stage.getByRole('button', { name: 'Zoom sheet', exact: true }).click();
    await scroller.evaluate(el => { el.scrollTop = 500; el.scrollLeft = 200; });
    await stage.getByRole('button', { name: 'Browse items', exact: true }).click();
    expect(await stage.getByLabel('Scroll asset family details', { exact: true }).evaluate(el => [el.scrollTop, el.scrollLeft])).toEqual([0, 0]);
    const select = stage.getByLabel('Asset family', { exact: true });
    await expect(select.locator('option')).toHaveCount(17);
    await expect(stage.getByRole('button', { name: 'Previous asset family' })).toBeDisabled();
    for (let index = 0; index < 17; index++) {
      await select.selectOption(String(index));
      await expect(stage.locator('.world-catalog-family-id')).toContainText(`W${String(index + 1).padStart(2, '0')}`);
      await expect(stage.locator('.world-catalog-panel').first()).toBeVisible();
    }
    await expect(stage.getByRole('button', { name: 'Next asset family' })).toBeDisabled();
    await select.selectOption('4');
    await expect(stage.locator('.world-catalog-family')).toContainText('Lena Brooks');
    await expect(stage.locator('.world-catalog-family')).toContainText('Rowan McLeod');
    await stage.screenshot({ path: `artifacts/sushi-loop/art-catalog-chefs-${width}.png` });
    await select.selectOption('7');
    for (const name of ['Salmon nigiri', 'Cucumber maki', 'Eel roll']) await expect(stage.locator('.world-catalog-family')).toContainText(name);
    await expect(stage.getByRole('img', { name: 'Dishes & world feedback concept detail, sheet panel 3', exact: true })).toBeVisible();
    await stage.screenshot({ path: `artifacts/sushi-loop/art-catalog-dishes-${width}.png` });
    await page.getByRole('button', { name: 'Reset', exact: true }).click();
    await expect(stage.getByRole('button', { name: 'Concept sheet', exact: true })).toHaveAttribute('aria-pressed', 'true');
  }
});

test('catalog comments retain their exact review branch through reload and GitHub handoff', async ({ page }) => {
  await page.goto(url);
  await page.getByRole('button', { name: 'Comments', exact: true }).click();
  const feedback = page.locator('.feedback-section');
  await feedback.getByLabel('What would you change?').fill('W04: make the connected belt rails wider.');
  await feedback.getByRole('button', { name: 'Add comment', exact: true }).click();
  await page.reload();
  await page.getByRole('button', { name: 'Comments', exact: true }).click();
  await expect(feedback.locator('.feedback-comment-text')).toHaveText('W04: make the connected belt rails wider.');
  const link = new URL(await feedback.getByRole('link', { name: /Open GitHub feedback form/ }).getAttribute('href'));
  expect(link.searchParams.get('body')).toContain('codex/sushi-loop-33-art-catalog');
  expect(link.searchParams.get('body')).toContain('art-catalog');
  expect(link.searchParams.get('body')).toContain('W04: make the connected belt rails wider.');
});
