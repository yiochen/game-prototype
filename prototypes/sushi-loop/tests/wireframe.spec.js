import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';

const URL = '/prototypes/sushi-loop/?ntl-drawer-state=hidden';
const stage = (page) => page.locator('#prototype-stage');
const dialog = (page) => stage(page).getByRole('dialog');
const action = (page, name) => stage(page).locator(`[data-action="${name}"]`);

async function open(page, story) {
  // A fresh document verifies that shared deep links initialize their fixture,
  // rather than inheriting a previous interactive mock state via hash navigation.
  if (page.url() !== 'about:blank') await page.goto('about:blank');
  await page.goto(`${URL}#${story}`);
  await expect(stage(page)).toHaveAttribute('data-story', story);
  await expect(page.locator('#story-title')).not.toBeEmpty();
}

async function at(page, story) {
  await expect(page).toHaveURL(new RegExp(`#${story}$`));
  await expect(stage(page)).toHaveAttribute('data-story', story);
}

async function screenshot(page, name) {
  await mkdir('artifacts/sushi-loop', { recursive: true });
  await page.screenshot({ path: `artifacts/sushi-loop/${name}.png`, fullPage: true, animations: 'disabled' });
}

// Read the public example chooser to cover the entire review inventory, while
// keeping interaction tests below independent of renderer/state internals.
for (const [name, width, height] of [
  ['small-phone', 320, 740], ['phone', 390, 844],
  ['landscape', 844, 390], ['desktop', 1440, 1000],
]) {
  test(`all 51 deep-linked examples render without errors or horizontal clipping at ${name}`, async ({ page }) => {
    test.setTimeout(90_000);
    await page.setViewportSize({ width, height });
    // Layout checks measure the settled popup, not its entrance translation.
    await page.emulateMedia({ reducedMotion: 'reduce' });
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await open(page, 'floor-plan');
    const examples = await page.locator('#example-select option').evaluateAll((options) => options.map((option) => ({ id: option.value, title: option.textContent })));
    expect(examples).toHaveLength(51);
    for (const example of examples) {
      await open(page, example.id);
      await expect(page.locator('#story-title')).toHaveText(example.title);
      await expect(stage(page).locator('.scene-host')).not.toBeEmpty();
      const bounds = await page.evaluate(() => {
        const preview = document.querySelector('#prototype-stage').getBoundingClientRect();
        const popup = document.querySelector('#prototype-stage dialog')?.getBoundingClientRect();
        return {
          pageWidth: document.documentElement.scrollWidth, viewportWidth: innerWidth,
          preview: { left: preview.left, right: preview.right, top: preview.top, bottom: preview.bottom },
          popup: popup && { left: popup.left, right: popup.right, top: popup.top, bottom: popup.bottom },
        };
      });
      expect(bounds.pageWidth, `${example.id} page width`).toBeLessThanOrEqual(bounds.viewportWidth + 1);
      expect(bounds.preview.left, `${example.id} left edge`).toBeGreaterThanOrEqual(-1);
      expect(bounds.preview.right, `${example.id} right edge`).toBeLessThanOrEqual(bounds.viewportWidth + 1);
      if (bounds.popup) {
        expect(bounds.popup.left, `${example.id} dialog left`).toBeGreaterThanOrEqual(bounds.preview.left - 1);
        expect(bounds.popup.right, `${example.id} dialog right`).toBeLessThanOrEqual(bounds.preview.right + 1);
        expect(bounds.popup.top, `${example.id} dialog top`).toBeGreaterThanOrEqual(bounds.preview.top - 1);
        expect(bounds.popup.bottom, `${example.id} dialog bottom`).toBeLessThanOrEqual(bounds.preview.bottom + 1);
      }
    }
    expect(errors).toEqual([]);
    await open(page, name === 'desktop' ? 'floor-plan' : name === 'landscape' ? 'staff-applicants' : 'recipe-picker');
    await screenshot(page, `wireframe-${name}`);
  });
}

test('phone example menu supports search, selection, dismissal and behavior/motion notes', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await open(page, 'floor-plan');
  await page.getByRole('button', { name: 'Examples', exact: true }).click();
  const menu = page.getByRole('dialog', { name: 'Wireframe examples' });
  await expect(menu).toBeVisible();
  await menu.getByRole('searchbox').fill('recipe');
  await expect(menu.getByRole('link', { name: 'Picker · chef tier too low', exact: true })).toBeVisible();
  await expect(menu.getByRole('link', { name: 'Shop · available goods', exact: true })).not.toBeVisible();
  await menu.getByRole('link', { name: 'Picker · chef tier too low', exact: true }).click();
  await at(page, 'recipe-unavailable');
  await expect(page.locator('#story-sidebar')).not.toBeVisible();
  await page.getByRole('button', { name: 'Notes', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Behavior & motion', exact: true })).toBeVisible();
  await expect(page.locator('#documentation')).toContainText('Preparation time');
  await expect(page.locator('#documentation')).toContainText('Motion');
  await page.getByRole('button', { name: 'Examples', exact: true }).click();
  await menu.getByRole('searchbox').fill('no-such-wireframe');
  await expect(menu.getByText('No matching examples.', { exact: true })).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.locator('#story-sidebar')).not.toBeVisible();
});

test('scene landmarks navigate between Shop, editing, Workshop and restaurant', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await open(page, 'restaurant-live');
  await stage(page).getByRole('button', { name: /Shop/ }).click();
  await at(page, 'shop');
  await stage(page).getByRole('button', { name: 'Restaurant', exact: true }).click();
  await at(page, 'restaurant-live');
  await stage(page).getByRole('button', { name: 'Edit', exact: true }).click();
  await at(page, 'restaurant-edit');
  await stage(page).getByRole('button', { name: /Shop/ }).click();
  await at(page, 'shop');
  await stage(page).getByRole('button', { name: 'Restaurant', exact: true }).click();
  await at(page, 'restaurant-edit');
  await expect(stage(page).getByText('Service paused', { exact: true })).toBeVisible();
  await open(page, 'restaurant-expanded');
  await stage(page).locator('[data-action="pan"][data-panel="1"]').click();
  await stage(page).getByRole('button', { name: /Workshop.*Small service hut/ }).click();
  await at(page, 'workshop');
  await stage(page).getByRole('button', { name: 'Sushi Bar', exact: true }).click();
  await at(page, 'restaurant-live');
  await expect(stage(page).locator('[data-action="pan"][data-panel="0"]')).toHaveAttribute('aria-pressed', 'true');
});

test('expedition navigation preserves a deliberate start, pause/resume and confirmed early return', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await open(page, 'restaurant-expanded');
  await stage(page).locator('[data-action="pan"][data-panel="1"]').click();
  await stage(page).getByRole('button', { name: /Submarine.*Ready/ }).click();
  await at(page, 'expedition-start');
  await expect(stage(page).getByRole('heading', { name: 'Ready to depart' })).toBeVisible();
  await stage(page).getByRole('button', { name: 'Start', exact: true }).click();
  await at(page, 'expedition-travel');
  await stage(page).getByRole('button', { name: 'Pause', exact: true }).click();
  await at(page, 'expedition-pause');
  await dialog(page).getByRole('button', { name: 'Resume', exact: true }).click();
  await at(page, 'expedition-resume');
  await page.getByRole('button', { name: /Preview next event/ }).click();
  await at(page, 'expedition-travel');
  await stage(page).getByRole('button', { name: 'Pause', exact: true }).click();
  await dialog(page).getByRole('button', { name: 'Return early…', exact: true }).click();
  await at(page, 'expedition-return');
  await dialog(page).getByRole('button', { name: 'Stay paused', exact: true }).click();
  await at(page, 'expedition-pause');
  await dialog(page).getByRole('button', { name: 'Return early…', exact: true }).click();
  await dialog(page).getByRole('button', { name: 'Return early', exact: true }).click();
  await at(page, 'results-early');
  await expect(stage(page).getByRole('heading', { name: 'Returned early', exact: true })).toBeVisible();
  await expect(stage(page).getByText('No completion bonus because the route was not finished.', { exact: true })).toBeVisible();
  await stage(page).getByRole('button', { name: 'Restaurant', exact: true }).click();
  await at(page, 'restaurant-live');
});

test('first discovery opens its recipe award, then the receipt; repeat catch goes straight to the receipt', async ({ page }) => {
  await open(page, 'catch-first');
  await page.getByRole('button', { name: /Preview next event/ }).click();
  await at(page, 'recipe-award');
  await expect(dialog(page).getByRole('heading', { name: 'New recipe discovered!', exact: true })).toBeVisible();
  await expect(dialog(page)).toContainText('Base prep time');
  await dialog(page).getByRole('button', { name: 'Continue', exact: true }).click();
  await at(page, 'results-complete');
  await expect(stage(page).getByRole('heading', { name: 'Expedition complete', exact: true })).toBeVisible();
  await expect(stage(page).getByText('Eel roll', { exact: true })).toHaveCount(0);
  await open(page, 'catch-repeat');
  await page.getByRole('button', { name: /Preview next event/ }).click();
  await at(page, 'results-complete');
  await expect(dialog(page)).toHaveCount(0);
});

test('recipe inspection keeps current production until Prepare; idle chefs require a choice', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await open(page, 'recipe-picker');
  await expect(dialog(page).locator('.preparing-status')).toContainText('Preparing');
  await expect(action(page, 'prepare')).toHaveCount(0);
  await dialog(page).getByRole('button', { name: 'Inspect Cucumber maki', exact: true }).click();
  await expect(dialog(page).getByRole('heading', { name: 'Cucumber maki', exact: true })).toBeVisible();
  await expect(stage(page).locator('.blackboard b')).toHaveText('Salmon');
  await expect(action(page, 'prepare')).toBeEnabled();
  await action(page, 'prepare').click();
  await at(page, 'restaurant-live');
  await expect(dialog(page)).toHaveCount(0);
  await expect(stage(page).locator('.blackboard b')).toHaveText('Cucumber');
  await open(page, 'recipe-idle');
  await expect(dialog(page).getByRole('heading', { name: 'Choose a recipe', exact: true })).toBeVisible();
  await expect(action(page, 'prepare')).toBeDisabled();
  await dialog(page).getByRole('button', { name: 'Close dialog', exact: true }).click();
  await at(page, 'restaurant-live');
  await expect(stage(page).locator('.blackboard b')).toHaveText('Choose recipe');
  await expect(stage(page).locator('.blackboard small')).toHaveText('Idle');
  await open(page, 'restaurant-edit');
  await action(page, 'place').filter({ hasText: 'Omar' }).click();
  await at(page, 'recipe-idle');
  await expect(dialog(page).getByRole('heading', { name: 'Choose a recipe', exact: true })).toBeVisible();
  await expect(action(page, 'prepare')).toBeDisabled();
  await open(page, 'recipe-new');
  const eel = dialog(page).getByRole('button', { name: 'Inspect Eel roll', exact: true });
  await expect(eel).toContainText('NEW');
  await eel.click();
  await expect(eel).not.toContainText('NEW');
});

test('tap markers are visible by default and phone controls retain at least 44px touch targets', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await open(page, 'restaurant-live');
  const edit = stage(page).getByRole('button', { name: 'Edit', exact: true });
  const staff = stage(page).getByRole('button', { name: 'Staff', exact: true });
  for (const button of [edit, staff]) {
    const box = await button.boundingBox();
    expect(box.width).toBeGreaterThanOrEqual(44);
    expect(box.height).toBeGreaterThanOrEqual(44);
    expect(await button.evaluate((element) => getComputedStyle(element).borderTopStyle)).toBe('dashed');
  }
  const markers = page.getByRole('checkbox', { name: 'Tap targets', exact: true });
  await expect(markers).toBeChecked();
  await markers.uncheck();
  await expect.poll(() => edit.evaluate((element) => getComputedStyle(element).borderTopColor)).toBe('rgba(0, 0, 0, 0)');
  await markers.check();
  await expect.poll(() => edit.evaluate((element) => getComputedStyle(element).borderTopColor)).not.toBe('rgba(0, 0, 0, 0)');
  await open(page, 'recipe-picker');
  const close = dialog(page).getByRole('button', { name: 'Close dialog', exact: true });
  const box = await close.boundingBox();
  expect(box.width).toBeGreaterThanOrEqual(44);
  expect(box.height).toBeGreaterThanOrEqual(44);
});

test('dialog backdrop does not dismiss or activate the scene; keyboard focus stays inside and Escape closes recipe only', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await open(page, 'recipe-picker');
  await stage(page).locator('[data-scrim]').click({ position: { x: 2, y: 2 } });
  await at(page, 'recipe-picker');
  await expect(dialog(page)).toBeVisible();
  await expect(stage(page).locator('.scene-host')).toHaveAttribute('inert', '');
  for (let i = 0; i < 14; i++) {
    await page.keyboard.press(i < 7 ? 'Tab' : 'Shift+Tab');
    expect(await page.evaluate(() => document.querySelector('#prototype-stage dialog').contains(document.activeElement))).toBe(true);
  }
  await page.keyboard.press('Escape');
  await at(page, 'restaurant-live');
  await open(page, 'expedition-pause');
  await stage(page).locator('[data-scrim]').click({ position: { x: 2, y: 2 } });
  await page.keyboard.press('Escape');
  await at(page, 'expedition-pause');
  await expect(dialog(page).getByRole('button', { name: 'Resume', exact: true })).toBeVisible();
});

test('hiring stays in applicants with remaining candidates; reset restores the fixture', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await open(page, 'staff-applicants');
  await expect(dialog(page).locator('.applicant-card')).toHaveCount(3);
  await dialog(page).getByRole('button', { name: 'Hire Mateo Rivera', exact: true }).click();
  await at(page, 'staff-applicants');
  await expect(dialog(page).locator('.applicant-card')).toHaveCount(2);
  await expect(dialog(page).getByRole('heading', { name: 'Mateo Rivera', exact: true })).toHaveCount(0);
  await expect(dialog(page)).toContainText('2 applications remain');
  await page.getByRole('button', { name: 'Reset', exact: true }).click();
  await expect(dialog(page).locator('.applicant-card')).toHaveCount(3);
  await expect(dialog(page).getByRole('button', { name: 'Refresh', exact: true })).toBeEnabled();
  await dialog(page).getByRole('button', { name: 'Refresh', exact: true }).click();
  await expect(dialog(page).getByRole('button', { name: 'Wait', exact: true })).toBeDisabled();
  await expect(dialog(page).getByRole('heading', { name: 'Ellis Morgan', exact: true })).toBeVisible();
});

test('unaffordable, ineligible, full and MAX examples keep facts visible and block their unavailable action', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 740 });
  for (const [story, unavailableAction] of [
    ['recipe-unavailable', 'prepare'], ['recipe-undiscovered', 'prepare'],
    ['staff-full', 'hire'], ['staff-unaffordable', 'level-up'],
    ['shop-unaffordable', 'purchase'], ['workshop-unaffordable', 'upgrade'],
    ['expansion-unaffordable', 'clear-confirm'],
  ]) {
    await open(page, story);
    const buttons = action(page, unavailableAction);
    expect(await buttons.count()).toBeGreaterThan(0);
    for (const button of await buttons.all()) await expect(button).toBeDisabled();
  }
  await open(page, 'recipe-unavailable');
  await expect(dialog(page).locator('.recipe-facts')).toContainText('—');
  await expect(dialog(page).locator('.recipe-facts')).toContainText('Copper');
  await open(page, 'staff-max');
  await expect(dialog(page).getByText('MAX', { exact: true })).toBeVisible();
  await expect(action(page, 'level-up')).toHaveCount(0);
  await open(page, 'workshop-max');
  await expect(stage(page).getByText('MAX', { exact: true })).toBeVisible();
  await screenshot(page, 'wireframe-max-and-disabled');
});

test('native phone swipes pan the restaurant while fixed controls stay reachable', async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  const page = await context.newPage();
  await open(page, 'restaurant-live');
  await page.evaluate(() => document.fonts.ready);
  const floor = await stage(page).locator('[data-pan-scroll]').boundingBox();
  const controls = await stage(page).locator('.restaurant-actions').boundingBox();
  const beforeStage = await stage(page).boundingBox();
  const cdp = await context.newCDPSession(page);
  const start = { x: floor.x + floor.width * .84, y: floor.y + floor.height * .72 };
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [start] });
  for (let step = 1; step <= 8; step++) {
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: start.x - step * floor.width * .08, y: start.y }] });
  }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await expect.poll(() => stage(page).locator('[data-pan-scroll]').evaluate((element) => element.scrollLeft)).toBeGreaterThan(floor.width * .4);
  const afterControls = await stage(page).locator('.restaurant-actions').boundingBox();
  const afterStage = await stage(page).boundingBox();
  // Page scrolling may move the frame; the HUD must stay fixed within it.
  expect(afterControls.x - afterStage.x).toBeCloseTo(controls.x - beforeStage.x, 1);
  expect(afterControls.y - afterStage.y).toBeCloseTo(controls.y - beforeStage.y, 1);
  await expect(stage(page).getByRole('button', { name: 'Edit', exact: true })).toBeVisible();
  await screenshot(page, 'wireframe-touch-pan');
  await context.close();
});

test('nested dialogs return to their parent and an inventory Shop detour stays in editing', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await open(page, 'inventory-empty');
  await dialog(page).getByRole('button', { name: 'Visit Shop', exact: true }).click();
  await at(page, 'shop');
  await stage(page).getByRole('button', { name: 'Restaurant', exact: true }).click();
  await at(page, 'restaurant-edit');
  await expect(dialog(page)).toHaveCount(0);
  await expect(stage(page).getByText('Service paused', { exact: true })).toBeVisible();
  await open(page, 'staff-detail');
  await dialog(page).getByRole('button', { name: 'Recipes', exact: true }).click();
  await at(page, 'recipe-picker');
  await dialog(page).getByRole('button', { name: 'Close dialog', exact: true }).click();
  await at(page, 'staff-detail');
  await expect(dialog(page).getByRole('heading', { name: 'Lena Brooks', exact: true })).toBeVisible();
});

test('refreshed hires retain their identity and cooking speed in the shared roster and detail', async ({ page }) => {
  await open(page, 'staff-applicants');
  await dialog(page).getByRole('button', { name: 'Hire Mateo Rivera', exact: true }).click();
  await dialog(page).getByRole('button', { name: 'Refresh', exact: true }).click();
  await dialog(page).getByRole('button', { name: 'Hire Ellis Morgan', exact: true }).click();
  await dialog(page).getByRole('button', { name: 'Back to staff', exact: true }).click();
  await at(page, 'staff-roster');
  for (const name of ['Mateo Rivera', 'Ellis Morgan']) {
    const card = stage(page).locator('.staff-card').filter({ has: page.getByRole('heading', { name, exact: true }) });
    await expect(card).toContainText('1.20×');
    await expect(card).toContainText('Unassigned');
  }
  await stage(page).locator('.staff-card').filter({ hasText: 'Ellis Morgan' }).getByRole('button', { name: 'Unassigned · details', exact: true }).click();
  await expect(dialog(page).getByRole('heading', { name: 'Ellis Morgan', exact: true })).toBeVisible();
  await expect(dialog(page).locator('.chef-facts')).toContainText('1.20×');
});

test('unassignment updates the floor and expedition returns recenter while resume retains danger', async ({ page }) => {
  await open(page, 'staff-detail');
  await dialog(page).getByRole('button', { name: 'Unassign', exact: true }).click();
  await dialog(page).getByRole('button', { name: 'Back to staff', exact: true }).click();
  await stage(page).getByRole('button', { name: 'Restaurant', exact: true }).click();
  await expect(stage(page).locator('.placed-chef')).toHaveCount(0);
  await expect(stage(page).getByText('No chef assigned · Choose one in Edit', { exact: true })).toBeVisible();
  await open(page, 'restaurant-expanded');
  await stage(page).locator('[data-action="pan"][data-panel="1"]').click();
  await stage(page).getByRole('button', { name: /Submarine.*Ready/ }).click();
  await stage(page).getByRole('button', { name: /Sushi Bar/ }).click();
  await at(page, 'restaurant-live');
  await expect(stage(page).locator('[data-action="pan"][data-panel="0"]')).toHaveAttribute('aria-pressed', 'true');
  await open(page, 'expedition-danger');
  await stage(page).getByRole('button', { name: 'Pause', exact: true }).click();
  await dialog(page).getByRole('button', { name: 'Resume', exact: true }).click();
  await expect(stage(page).locator('.attack-column')).toBeVisible();
  await page.getByRole('button', { name: /Preview next event/ }).click();
  await at(page, 'expedition-danger');
  await expect(stage(page).locator('.harpoon-cable.frayed')).toBeVisible();
});
