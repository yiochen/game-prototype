import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

const PROTOTYPE_URL = '/prototypes/sushi-loop/?ntl-drawer-state=hidden';

async function open(page, story = 'floor-plan') {
  await page.goto(`${PROTOTYPE_URL}#${story}`);
  await expect(page.locator('#prototype-stage')).toHaveAttribute('data-story', story);
  const section = page.locator('.feedback-section');
  if (!(await section.isVisible())) await page.getByRole('button', { name: /Notes/ }).click();
  await expect(section).toBeVisible();
  return section;
}

async function select(page, story) {
  await page.locator('#example-select').selectOption(story);
  await expect(page.locator('#prototype-stage')).toHaveAttribute('data-story', story);
  await expect(page.locator('.feedback-section')).toBeVisible();
}

test('comments and unfinished drafts belong to each example, survive reload and can be removed', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const section = await open(page);
  const draft = section.getByRole('textbox', { name: 'What would you change?', exact: true });
  await expect(section.getByRole('button', { name: 'Add comment', exact: true })).toBeDisabled();
  await draft.fill('Move the workshop a little closer to the submarine.');
  await select(page, 'shop');
  await expect(draft).toHaveValue('');
  await draft.fill('Make the owned floor pattern easier to compare.');
  await section.getByRole('button', { name: 'Add comment', exact: true }).click();
  await expect(section.locator('.feedback-comments > li')).toHaveCount(1);
  await expect(section).toContainText('Saved on this device');
  await select(page, 'floor-plan');
  await expect(draft).toHaveValue('Move the workshop a little closer to the submarine.');
  await section.getByRole('button', { name: 'Add comment', exact: true }).click();
  await page.reload();
  await expect(section.locator('.feedback-comment-text')).toHaveText('Move the workshop a little closer to the submarine.');
  await expect(draft).toHaveValue('');
  await select(page, 'shop');
  await expect(section.locator('.feedback-comment-text')).toHaveText('Make the owned floor pattern easier to compare.');
  await section.getByRole('button', { name: /Remove comment saved/ }).click();
  await expect(section.getByText('No comments on this example yet.', { exact: true })).toBeVisible();
  await page.reload();
  await expect(section.locator('.feedback-comments > li')).toHaveCount(0);
  await select(page, 'floor-plan');
  await expect(section.locator('.feedback-comments > li')).toHaveCount(1);
});

test('GitHub handoff includes the note and exact example; export gathers all feedback without posting it', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const externalRequests = [];
  page.on('request', (request) => {
    if (new URL(request.url()).hostname === 'github.com') externalRequests.push({ method: request.method(), url: request.url() });
  });
  const section = await open(page);
  const first = 'Add a clearer entrance label for panel 2.';
  await section.getByRole('textbox').fill(first);
  await section.getByRole('button', { name: 'Add comment', exact: true }).click();
  await select(page, 'recipe-award');
  const note = 'Give Continue more space. <img src=x onerror="alert(1)">\nKeep the base prep time visible.';
  await section.getByRole('textbox').fill(note);
  await section.getByRole('button', { name: 'Add comment', exact: true }).click();
  await expect(section.locator('.feedback-comment-text')).toHaveText(note);
  await expect(section.locator('.feedback-comments img')).toHaveCount(0);
  const link = section.getByRole('link', { name: /Open GitHub feedback form/ });
  const url = new URL(await link.getAttribute('href'));
  expect(url.origin).toBe('https://github.com');
  expect(url.pathname).toBe('/yiochen/game-prototype/issues/new');
  expect(url.searchParams.get('title')).toContain('First-catch recipe award');
  expect(url.searchParams.get('labels')).toBe('wireframe-feedback');
  const body = url.searchParams.get('body');
  expect(body).toContain(note);
  expect(body).toContain('`recipe-award`');
  expect(body).toContain('#recipe-award');
  expect(body).toContain('`codex/sushi-loop-wireframes`');
  expect(body).toContain('shared component');
  await expect(section).toContainText('you still need to submit it');
  await expect(section).toContainText('Submit the GitHub issue, then ask Codex to apply it.');
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    section.getByRole('button', { name: 'Export all .md', exact: true }).click(),
  ]);
  expect(download.suggestedFilename()).toBe('sushi-loop-wireframe-feedback.md');
  const exported = await readFile(await download.path(), 'utf8');
  expect(exported).toContain(first);
  expect(exported).toContain(note);
  expect(exported).toContain('#floor-plan');
  expect(exported).toContain('#recipe-award');
  expect(exported).toContain('not been automatically sent');
  expect(externalRequests).toEqual([]);
});

test('phone feedback reports unavailable storage and uses a download when clipboard access is unavailable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() => {
    Storage.prototype.setItem = () => { throw new DOMException('Unavailable', 'QuotaExceededError'); };
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: undefined });
  });
  const section = await open(page, 'recipe-picker');
  await section.getByRole('textbox').fill('The recipe close control should remain thumb reachable.');
  await section.getByRole('button', { name: 'Add comment', exact: true }).click();
  await expect(section.locator('.feedback-comments > li')).toHaveCount(1);
  await expect(section.locator('.feedback-comment-meta')).toContainText('Only in this tab');
  await expect(section.getByRole('status')).toContainText('only in this tab');
  await section.getByRole('textbox').fill('Unfinished recipe draft survives a story switch.');
  await page.getByRole('button', { name: 'Examples', exact: true }).click();
  await page.getByRole('dialog', { name: 'Wireframe examples' }).getByRole('link', { name: 'Shop · available goods', exact: true }).click();
  await expect(section.getByRole('textbox')).toHaveValue('');
  await section.getByRole('textbox').fill('A separate unfinished Shop draft.');
  await page.getByRole('button', { name: 'Examples', exact: true }).click();
  await page.getByRole('dialog', { name: 'Wireframe examples' }).getByRole('link', { name: 'Picker · eligible recipe', exact: true }).click();
  await expect(section.getByRole('textbox')).toHaveValue('Unfinished recipe draft survives a story switch.');
  await expect(section.locator('.feedback-comment-text')).toHaveText('The recipe close control should remain thumb reachable.');
  await expect(section.locator('.feedback-comment-meta')).toContainText('Only in this tab');
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    section.getByRole('button', { name: 'Copy all feedback', exact: true }).click(),
  ]);
  expect(download.suggestedFilename()).toBe('sushi-loop-wireframe-feedback.md');
  await expect(section.getByRole('status')).toContainText('Clipboard access was unavailable');
  const exportText = await readFile(await download.path(), 'utf8');
  expect(exportText).toContain('The recipe close control should remain thumb reachable.');
  const width = await page.evaluate(() => ({ page: document.documentElement.scrollWidth, viewport: innerWidth }));
  expect(width.page).toBeLessThanOrEqual(width.viewport);
  for (const button of await section.getByRole('button').all()) {
    const box = await button.boundingBox();
    expect(box.height).toBeGreaterThanOrEqual(44);
  }
});
