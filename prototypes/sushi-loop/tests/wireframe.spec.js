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

const floorPosition = page => stage(page).locator('[data-pan-scroll]').evaluate(element => element.scrollLeft / element.clientWidth);

async function panTo(page, fraction) {
  const viewport = stage(page).locator('[data-pan-scroll]');
  const size = await viewport.evaluate(element => ({ width: element.clientWidth, left: element.scrollLeft }));
  await viewport.hover({ position: { x: size.width / 2, y: 180 } });
  await page.mouse.wheel(fraction * size.width - size.left, 0);
  await expect.poll(() => floorPosition(page)).toBeCloseTo(fraction, 1);
}

async function openRecipesFromStaff(page) {
  await stage(page).getByRole('button', { name: 'Staff', exact: true }).click();
  await stage(page).getByRole('button', { name: 'Inspect Lena Brooks', exact: true }).click();
  await dialog(page).getByRole('button', { name: 'Recipes', exact: true }).click();
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
  test(`all 56 deep-linked examples render without errors or horizontal clipping at ${name}`, async ({ page }) => {
    test.setTimeout(90_000);
    await page.setViewportSize({ width, height });
    // Layout checks measure the settled popup, not its entrance translation.
    await page.emulateMedia({ reducedMotion: 'reduce' });
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await open(page, 'floor-plan');
    const examples = await page.locator('#example-select option').evaluateAll((options) => options.map((option) => ({ id: option.value, title: option.textContent })));
    expect(examples).toHaveLength(56);
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

test('floating Shop and scene landmarks navigate between editing, Workshop and restaurant', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await open(page, 'restaurant-live');
  await stage(page).getByRole('button', { name: /Shop/ }).click();
  await at(page, 'shop');
  await stage(page).getByRole('button', { name: 'Return to restaurant', exact: true }).click();
  await at(page, 'restaurant-live');
  await stage(page).getByRole('button', { name: 'Edit', exact: true }).click();
  await at(page, 'restaurant-edit');
  await stage(page).getByRole('button', { name: /Shop/ }).click();
  await at(page, 'shop');
  await stage(page).getByRole('button', { name: 'Return to restaurant', exact: true }).click();
  await at(page, 'restaurant-edit');
  await expect(stage(page).getByRole('button', { name: 'Live', exact: true })).toBeVisible();
  await expect(stage(page).getByText('Service paused', { exact: true })).toHaveCount(0);
  await open(page, 'restaurant-expanded');
  await panTo(page, 1);
  await stage(page).getByRole('button', { name: 'Workshop', exact: true }).click();
  await at(page, 'workshop');
  await stage(page).getByRole('button', { name: 'Return to restaurant', exact: true }).click();
  await at(page, 'restaurant-expanded');
  await expect.poll(() => floorPosition(page)).toBeCloseTo(1, 1);
});

test('expedition navigation preserves a deliberate start, pause/resume and confirmed early return', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await open(page, 'restaurant-expanded');
  await panTo(page, 1);
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
  await expect(dialog(page).locator('.dialog-header .dialog-eyebrow')).toHaveText('Level 2');
  await expect(dialog(page).locator('.recipe-group h3, .recipe-details .dialog-eyebrow, .recipe-tier')).toHaveCount(0);
  await expect(dialog(page).locator('.recipe-details')).toHaveClass(/tier-wood/);
  await expect(dialog(page).getByRole('button', { name: 'Inspect Salmon nigiri', exact: true })).toHaveAccessibleDescription(/Wood material/);
  await expect(action(page, 'prepare')).toHaveCount(0);
  await dialog(page).getByRole('button', { name: 'Inspect Cucumber maki', exact: true }).click();
  await expect(dialog(page).getByRole('heading', { name: 'Cucumber maki', exact: true })).toBeVisible();
  await expect(dialog(page).locator('.is-preparing')).toContainText('Salmon nigiri');
  await expect(action(page, 'prepare')).toBeEnabled();
  await action(page, 'prepare').click();
  await at(page, 'restaurant-live');
  await expect(dialog(page)).toHaveCount(0);
  await openRecipesFromStaff(page);
  await expect(dialog(page).locator('.is-preparing')).toContainText('Cucumber maki');
  await open(page, 'recipe-idle');
  await expect(dialog(page).getByRole('heading', { name: 'Choose a recipe', exact: true })).toBeVisible();
  await expect(action(page, 'prepare')).toBeDisabled();
  await dialog(page).getByRole('button', { name: 'Close dialog', exact: true }).click();
  await at(page, 'restaurant-live');
  await openRecipesFromStaff(page);
  await expect(dialog(page).locator('.is-preparing')).toHaveCount(0);
  await open(page, 'restaurant-edit');
  await stage(page).getByRole('button', { name: 'Inspect Omar Haddad', exact: true }).click();
  await at(page, 'staff-detail');
  await expect(dialog(page).getByRole('heading', { name: 'Omar Haddad', exact: true })).toBeVisible();
  await dialog(page).getByRole('button', { name: 'Close dialog', exact: true }).click();
  await at(page, 'restaurant-edit');
  await expect(stage(page).getByRole('button', { name: 'People layer', exact: true })).toHaveAttribute('aria-expanded', 'true');
  await open(page, 'recipe-new');
  const eel = dialog(page).getByRole('button', { name: 'Inspect Eel roll', exact: true });
  await expect(eel).toContainText('NEW');
  await eel.click();
  await expect(eel).not.toContainText('NEW');
});

test('tap markers are visible by default and phone controls retain at least 44px touch targets', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
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
  await expect(dialog(page).locator('.paper-resume')).toHaveCount(1);
  await expect(dialog(page).locator('.resume-pagination')).toContainText('1 / 3');
  await dialog(page).getByRole('button', { name: 'Next applicant', exact: true }).click();
  await dialog(page).getByRole('button', { name: 'Hire Mateo Rivera', exact: true }).click();
  await at(page, 'staff-applicants');
  await expect(dialog(page).locator('.paper-resume')).toHaveCount(1);
  await expect(dialog(page).getByRole('heading', { name: 'Mateo Rivera', exact: true })).toHaveCount(0);
  await expect(dialog(page).locator('.resume-pagination')).toContainText('2 / 2');
  await page.getByRole('button', { name: 'Reset', exact: true }).click();
  await expect(dialog(page).locator('.resume-pagination')).toContainText('1 / 3');
  await expect(dialog(page).getByRole('button', { name: 'Refresh', exact: true })).toBeEnabled();
  await dialog(page).getByRole('button', { name: 'Refresh', exact: true }).click();
  await expect(dialog(page).getByRole('button', { name: 'Wait', exact: true })).toBeDisabled();
  await expect(dialog(page).getByRole('heading', { name: 'Dalia Farouk', exact: true })).toBeVisible();
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
  await expect(dialog(page).locator('.recipe-facts')).toContainText('Lv 5');
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

test('floating Shop stays below upper-left savings during panning and preserves the editing panel on return', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await open(page, 'restaurant-edit');
  await page.evaluate(() => document.fonts.ready);
  await expect(stage(page).locator('.restaurant-world [data-story="shop"]')).toHaveCount(0);
  const shop = stage(page).getByRole('button', { name: 'Shop', exact: true });
  const coin = stage(page).locator('.restaurant-hud .coin-count');
  const before = await shop.boundingBox();
  const amount = await coin.boundingBox();
  const frame = await stage(page).boundingBox();
  expect(before.y).toBeGreaterThan(amount.y + amount.height);
  expect(amount.x - frame.x).toBeLessThan(20);
  expect(before.x - frame.x).toBeLessThan(20);
  await expect(shop.locator('.stock-spark')).toBeVisible();
  await panTo(page, 1.35);
  const after = await shop.boundingBox();
  const afterFrame = await stage(page).boundingBox();
  expect(after.x - afterFrame.x).toBeCloseTo(before.x - frame.x, 1);
  expect(after.y - afterFrame.y).toBeCloseTo(before.y - frame.y, 1);
  await shop.click();
  await at(page, 'shop');
  await stage(page).getByRole('button', { name: 'Return to restaurant', exact: true }).click();
  await at(page, 'restaurant-edit');
  await expect.poll(() => floorPosition(page)).toBeCloseTo(1.35, 1);
  await expect(shop.locator('.stock-spark')).toHaveCount(0);
  await expect(stage(page).getByRole('button', { name: 'Live', exact: true })).toBeVisible();
  await expect(stage(page).getByText('Service paused', { exact: true })).toHaveCount(0);
  await open(page, 'floor-plan');
  await expect(stage(page).locator('.floor-plan-world [data-story="shop"]')).toHaveCount(0);
  await stage(page).getByRole('button', { name: 'Shop', exact: true }).click();
  await stage(page).getByRole('button', { name: 'Return to restaurant', exact: true }).click();
  await at(page, 'floor-plan');
});

test('nested dialogs return to their parent and an inventory toast leaves editing usable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await open(page, 'inventory-empty');
  await expect(dialog(page)).toHaveCount(0);
  await expect(stage(page).getByRole('status')).toContainText('No belt tiles left');
  await stage(page).getByRole('button', { name: 'Shop', exact: true }).click();
  await at(page, 'shop');
  await stage(page).getByRole('button', { name: 'Return to restaurant', exact: true }).click();
  await at(page, 'inventory-empty');
  await expect(dialog(page)).toHaveCount(0);
  await expect(stage(page).getByRole('button', { name: 'Live', exact: true })).toBeVisible();
  await expect(stage(page).getByText('Service paused', { exact: true })).toHaveCount(0);
  await open(page, 'staff-detail');
  await dialog(page).getByRole('button', { name: 'Recipes', exact: true }).click();
  await at(page, 'recipe-picker');
  await dialog(page).getByRole('button', { name: 'Close dialog', exact: true }).click();
  await at(page, 'staff-detail');
  await expect(dialog(page).getByRole('heading', { name: 'Lena Brooks', exact: true })).toBeVisible();
});

test('refreshed hires retain their identity and cooking speed through paged roster profiles and stats', async ({ page }) => {
  await open(page, 'staff-applicants');
  await dialog(page).getByRole('button', { name: 'Next applicant', exact: true }).click();
  await dialog(page).getByRole('button', { name: 'Hire Mateo Rivera', exact: true }).click();
  await dialog(page).getByRole('button', { name: 'Refresh', exact: true }).click();
  await dialog(page).getByRole('button', { name: 'Next applicant', exact: true }).click();
  await dialog(page).getByRole('button', { name: 'Hire Ellis Morgan', exact: true }).click();
  await dialog(page).getByRole('button', { name: 'Close dialog', exact: true }).click();
  await at(page, 'staff-roster');
  for (const name of ['Mateo Rivera', 'Ellis Morgan']) {
    if (name === 'Ellis Morgan') await stage(page).getByRole('button', { name: 'Next staff page', exact: true }).click();
    const profile = stage(page).getByRole('button', { name: `Inspect ${name}`, exact: true });
    await expect(profile).toContainText('Unassigned');
    await profile.click();
    await expect(dialog(page).getByRole('heading', { name, exact: true })).toBeVisible();
    await expect(dialog(page).locator('.chef-facts')).toContainText('1.20×');
    await dialog(page).getByRole('button', { name: 'Back to staff', exact: true }).click();
  }
});

test('unassignment updates the roster and expedition returns recenter while resume retains danger', async ({ page }) => {
  await open(page, 'staff-detail');
  await dialog(page).getByRole('button', { name: 'Unassign', exact: true }).click();
  await dialog(page).getByRole('button', { name: 'Back to staff', exact: true }).click();
  await expect(stage(page).getByRole('button', { name: 'Inspect Lena Brooks', exact: true })).toContainText('Unassigned');
  await stage(page).getByRole('button', { name: 'Close staff tray', exact: true }).click();
  await expect(stage(page).locator('.placed-chef')).toHaveCount(0);
  await expect(stage(page).locator('.starter-service, .customer, .open-belt')).toHaveCount(0);
  await open(page, 'restaurant-expanded');
  await panTo(page, 1);
  await stage(page).getByRole('button', { name: /Submarine.*Ready/ }).click();
  await stage(page).getByRole('button', { name: /Sushi Bar/ }).click();
  await at(page, 'restaurant-live');
  await expect.poll(() => floorPosition(page)).toBeLessThan(.01);
  await open(page, 'expedition-danger');
  await stage(page).getByRole('button', { name: 'Pause', exact: true }).click();
  await dialog(page).getByRole('button', { name: 'Resume', exact: true }).click();
  await expect(stage(page).locator('.attack-column')).toBeVisible();
  await page.getByRole('button', { name: /Preview next event/ }).click();
  await at(page, 'expedition-danger');
  await expect(stage(page).locator('.harpoon-cable.frayed')).toBeVisible();
});

test('floor-plan editor layers toggle the tray, swatches have no captions and Live stays top-right', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await open(page, 'restaurant-live');
  await expect(stage(page).locator('.customer, .open-belt, .starter-service, .pan-controls')).toHaveCount(0);
  const frame = await stage(page).boundingBox();
  for (const name of ['Edit', 'Staff']) {
    const box = await stage(page).getByRole('button', { name, exact: true }).boundingBox();
    expect(box.x).toBeLessThan(frame.x + frame.width / 2);
    expect(box.y).toBeGreaterThan(frame.y + frame.height - 100);
  }
  await stage(page).getByRole('button', { name: 'Edit', exact: true }).click();
  const people = stage(page).getByRole('button', { name: 'People layer', exact: true });
  const layout = stage(page).getByRole('button', { name: 'Layout layer', exact: true });
  const floor = stage(page).getByRole('button', { name: 'Floor layer', exact: true });
  const tray = stage(page).locator('#editor-inventory-tray');
  const controls = await Promise.all([people.boundingBox(), layout.boundingBox(), floor.boundingBox()]);
  expect(controls[0].x).toBeGreaterThan(frame.x + frame.width / 2);
  expect(controls[0].x).toBeCloseTo(controls[2].x, 1);
  expect(controls[0].y).toBeLessThan(controls[1].y);
  expect(controls[1].y).toBeLessThan(controls[2].y);
  await expect(people).toHaveAttribute('aria-expanded', 'true');
  await expect(stage(page).locator('.layer-selected-name')).toHaveText('People');
  await people.click();
  await expect(people).toHaveAttribute('aria-expanded', 'false');
  await expect(tray).toHaveAttribute('inert', '');
  await expect(stage(page).locator('.layer-selected-name')).toHaveText('People');
  await layout.click();
  await expect(layout).toHaveAttribute('aria-expanded', 'true');
  await expect(stage(page).locator('.layer-selected-name')).toHaveText('Layout');
  await expect(tray.getByRole('button', { name: 'Belt tile', exact: true })).toBeVisible();
  await floor.click();
  await expect(floor).toHaveAttribute('aria-expanded', 'true');
  await expect(stage(page).locator('.layer-selected-name')).toHaveText('Floor');
  const swatches = tray.locator('.floor-swatch');
  await expect(swatches).toHaveCount(2);
  for (const swatch of await swatches.all()) expect((await swatch.textContent()).trim()).toBe('');
  await expect(tray.getByRole('button', { name: 'Blue wave', exact: true })).toBeVisible();
  await expect(tray.getByRole('button', { name: 'Previous floor page', exact: true })).toBeDisabled();
  await tray.getByRole('button', { name: 'Next floor page', exact: true }).click();
  await expect(swatches).toHaveCount(1);
  await expect(tray.getByRole('button', { name: 'Checker', exact: true })).toBeVisible();
  await expect(tray.getByRole('button', { name: 'Next floor page', exact: true })).toBeDisabled();
  await tray.getByRole('button', { name: 'Previous floor page', exact: true }).click();
  await expect(tray.getByRole('button', { name: 'Blue wave', exact: true })).toBeVisible();
  await expect(stage(page).getByText(/Service paused|Select a style, then|Owned/)).toHaveCount(0);
  const live = stage(page).getByRole('button', { name: 'Live', exact: true });
  const liveBox = await live.boundingBox(), editFrame = await stage(page).boundingBox();
  expect(liveBox.x).toBeGreaterThan(editFrame.x + editFrame.width / 2);
  expect(liveBox.y - editFrame.y).toBeLessThan(50);
  await live.click();
  await at(page, 'restaurant-live');
  await screenshot(page, 'floor-plan-live-revision');
  await open(page, 'component-editor-controls');
  const sharedFloor = stage(page).getByRole('button', { name: 'Floor layer', exact: true });
  await sharedFloor.click();
  await at(page, 'component-editor-controls');
  await expect(stage(page).getByRole('button', { name: 'Blue wave', exact: true })).toBeVisible();
  await sharedFloor.click();
  await at(page, 'component-editor-controls');
  await expect(sharedFloor).toHaveAttribute('aria-expanded', 'false');
  await expect(stage(page).locator('#editor-inventory-tray')).toHaveAttribute('inert', '');
});

test('empty belt inventory is a short toast while layers and floating Shop remain usable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await open(page, 'inventory-empty');
  await expect(dialog(page)).toHaveCount(0);
  await expect(stage(page).getByRole('status')).toHaveText('No belt tiles left');
  await expect(stage(page).locator('.scene-host')).not.toHaveAttribute('inert');
  await stage(page).getByRole('button', { name: 'Floor layer', exact: true }).click();
  await expect(stage(page).getByRole('button', { name: 'Blue wave', exact: true })).toBeVisible();
  await expect(stage(page).getByRole('status')).toHaveCount(0, { timeout: 4000 });
  await stage(page).getByRole('button', { name: 'Layout layer', exact: true }).click();
  await stage(page).getByRole('button', { name: 'Belt tile', exact: true }).click();
  await expect(stage(page).getByRole('status')).toHaveText('No belt tiles left');
  await expect(stage(page).locator('.placement-preview')).toHaveCount(0);
  await stage(page).getByRole('button', { name: 'Shop', exact: true }).click();
  await at(page, 'shop');
});

test('clearance confirmation keeps cost on Clear only, uses Cancel, and greys out unaffordable clearance', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await open(page, 'expansion');
  await expect(dialog(page).getByRole('heading', { name: 'Clear this patch?', exact: true })).toBeVisible();
  await expect(dialog(page).getByRole('button')).toHaveCount(2);
  await expect(dialog(page).locator('.dialog-scroll')).toHaveText('');
  await expect(dialog(page).locator('.dialog-eyebrow')).toHaveCount(0);
  await expect(dialog(page).getByText('240', { exact: true })).toHaveCount(1);
  await dialog(page).getByRole('button', { name: 'Cancel', exact: true }).click();
  await at(page, 'restaurant-live');
  await expect(dialog(page)).toHaveCount(0);
  await open(page, 'expansion-unaffordable');
  await expect(action(page, 'clear-confirm')).toBeDisabled();
  await expect(dialog(page).getByText(/Not enough|Selected footprint|Clearance price|permanent|Open more/)).toHaveCount(0);
  await open(page, 'expansion');
  await action(page, 'clear-confirm').click();
  await at(page, 'restaurant-expanded');
  await expect(stage(page).getByRole('button', { name: 'Workshop', exact: true })).toBeEnabled();
});

test('dock and right-side Workshop share three by three floor tiles, with covered peeks before unlock', async ({ page }) => {
  for (const width of [320, 390]) {
    await page.setViewportSize({ width, height: 844 });
    await open(page, 'restaurant-expanded');
    await panTo(page, 1);
    const dock = stage(page).locator('.dock-zone');
    const size = await dock.evaluate(element => {
      const panel = element.closest('.floor-panel');
      const dockBox = element.getBoundingClientRect();
      return { width: dockBox.width, height: dockBox.height, tileWidth: panel.clientWidth / 9, tileHeight: panel.clientHeight / 16 };
    });
    expect(Math.abs(size.width - size.tileWidth * 3)).toBeLessThan(1);
    expect(Math.abs(size.height - size.tileHeight * 3)).toBeLessThan(1);
    const sub = await dock.getByRole('button', { name: /Submarine.*Ready/ }).boundingBox();
    const workshop = await dock.getByRole('button', { name: 'Workshop', exact: true }).boundingBox();
    expect(workshop.x).toBeGreaterThanOrEqual(sub.x + sub.width);
    for (const box of [sub, workshop]) { expect(box.width).toBeGreaterThanOrEqual(44); expect(box.height).toBeGreaterThanOrEqual(44); }
    await stage(page).getByRole('button', { name: 'Staff', exact: true }).click();
    await expect(stage(page).locator('[data-floor-panel="1"]')).toHaveClass(/(?:^|\s)cleared(?:\s|$)/);
    await expect(stage(page).getByRole('button', { name: 'Workshop', exact: true })).toBeEnabled();
    await stage(page).getByRole('button', { name: 'Close staff tray', exact: true }).click();
    await at(page, 'restaurant-expanded');
    await expect.poll(() => floorPosition(page)).toBeCloseTo(1, 1);
    await expect(stage(page).locator('[data-floor-panel="1"]')).toHaveClass(/(?:^|\s)cleared(?:\s|$)/);
    await open(page, 'component-dock');
    const covered = stage(page).locator('.dock-locked');
    await covered.scrollIntoViewIfNeeded();
    await expect(covered.locator('.dock-rags')).toBeVisible();
    for (const button of await covered.getByRole('button').all()) await expect(button).toBeDisabled();
    await expect(covered.getByText(/Ready|Charging|Future access/)).toHaveCount(0);
    await screenshot(page, `covered-dock-${width}`);
  }
});

test('touch drags place a roster preview without opening stats, while taps inspect and shared pages paginate', async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  try {
    const page = await context.newPage();
    await open(page, 'restaurant-live');
    await panTo(page, .35);
    await stage(page).getByRole('button', { name: 'Staff', exact: true }).tap();
    await expect.poll(() => floorPosition(page)).toBeCloseTo(.35, 1);
    await expect(stage(page).locator('.roster-profiles')).toHaveCount(1);
    await expect(stage(page).locator('.roster-profile')).toHaveCount(2);
    await stage(page).getByRole('button', { name: 'Close staff tray', exact: true }).tap();
    await at(page, 'restaurant-live');
    await expect.poll(() => floorPosition(page)).toBeCloseTo(.35, 1);
    await panTo(page, 0);
    await stage(page).getByRole('button', { name: 'Staff', exact: true }).tap();
    await stage(page).scrollIntoViewIfNeeded();
    const frame = await stage(page).boundingBox();
    const profile = stage(page).locator('.roster-profiles').getByRole('button', { name: 'Inspect Omar Haddad', exact: true });
    const card = await profile.boundingBox();
    const start = { x: card.x + card.width / 2, y: card.y + card.height / 2 };
    const end = { x: frame.x + frame.width * .55, y: frame.y + 250 };
    const cdp = await context.newCDPSession(page);
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [start] });
    for (let step=1; step<=8; step++) await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: start.x + (end.x-start.x)*step/8, y: start.y + (end.y-start.y)*step/8 }] });
    await expect(stage(page).locator('.roster-drag-ghost')).toBeVisible();
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await at(page, 'staff-roster');
    await expect(dialog(page)).toHaveCount(0);
    await expect(profile).toContainText('Assigned');
    await expect(stage(page).locator('.roster-placed-chef')).toBeVisible();
    await profile.tap();
    await expect(dialog(page).getByRole('heading', { name: 'Omar Haddad', exact: true })).toBeVisible();
    await expect(dialog(page).locator('.chef-facts')).toContainText('Cooking speed');
    await dialog(page).getByRole('button', { name: 'Unassign', exact: true }).tap();
    await dialog(page).getByRole('button', { name: 'Back to staff', exact: true }).tap();
    await expect(stage(page).locator('.roster-placed-chef')).toHaveCount(0);
    await expect(profile).toContainText('Unassigned');
    await stage(page).getByRole('button', { name: 'Dismiss notification', exact: true }).click();
    // Place once more, then dismissal must remove both profile and preview marker.
    await stage(page).scrollIntoViewIfNeeded();
    const nextCard = await profile.boundingBox(), nextFrame = await stage(page).boundingBox();
    const secondStart = { x: nextCard.x + nextCard.width / 2, y: nextCard.y + nextCard.height / 2 };
    const secondEnd = { x: nextFrame.x + nextFrame.width * .55, y: nextFrame.y + 250 };
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [secondStart] });
    for (let step=1; step<=8; step++) await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: secondStart.x + (secondEnd.x-secondStart.x)*step/8, y: secondStart.y + (secondEnd.y-secondStart.y)*step/8 }] });
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await expect(stage(page).locator('.roster-placed-chef')).toBeVisible();
    await profile.tap();
    await dialog(page).getByRole('button', { name: 'Fire…', exact: true }).tap();
    await dialog(page).getByRole('button', { name: 'Fire Omar', exact: true }).tap();
    await at(page, 'staff-roster');
    await expect(stage(page).locator('.roster-placed-chef')).toHaveCount(0);
    await expect(profile).toHaveCount(0);
    await open(page, 'component-roster-tray');
    await stage(page).getByRole('button', { name: 'Next staff page', exact: true }).tap();
    await expect(stage(page).getByRole('button', { name: 'Inspect Mateo Rivera', exact: true })).toBeVisible();
    await at(page, 'component-roster-tray');
    await stage(page).getByRole('button', { name: 'Previous staff page', exact: true }).tap();
    await expect(stage(page).getByRole('button', { name: 'Inspect Lena Brooks', exact: true })).toBeVisible();
  } finally { await context.close(); }
});

test('paper résumé touch swipes browse in both directions without hiring and shared resume stays interactive', async ({ browser }) => {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  try {
    const page = await context.newPage();
    await open(page, 'staff-applicants');
    const cdp = await context.newCDPSession(page);
    async function swipe(direction) {
      const paper = dialog(page).locator('.paper-resume');
      await paper.scrollIntoViewIfNeeded();
      const box = await paper.boundingBox();
      const start = { x: box.x + box.width * (direction < 0 ? .8 : .2), y: box.y + box.height * .4 };
      await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [start] });
      for (let step=1;step<=8;step++) await cdp.send('Input.dispatchTouchEvent', { type:'touchMove', touchPoints:[{x:start.x + direction * box.width*.07*step,y:start.y}] });
      await cdp.send('Input.dispatchTouchEvent', { type:'touchEnd', touchPoints:[] });
    }
    await expect(dialog(page).locator('.paper-resume')).toHaveCount(1);
    await swipe(-1);
    await expect(dialog(page).getByRole('heading', { name: 'Mateo Rivera', exact: true })).toBeVisible();
    await expect(dialog(page).locator('.dialog-eyebrow')).toContainText('Staff 2 / 4');
    await swipe(1);
    await expect(dialog(page).getByRole('heading', { name: 'Ama Mensah', exact: true })).toBeVisible();
    await dialog(page).getByRole('button', { name: 'Hire Ama Mensah', exact: true }).tap();
    await expect(dialog(page).locator('.dialog-eyebrow')).toContainText('Staff 3 / 4');
    await expect(dialog(page).getByRole('heading', { name: 'Mateo Rivera', exact: true })).toBeVisible();
    await open(page, 'component-applicant-resume');
    await stage(page).getByRole('button', { name: 'Next applicant', exact: true }).tap();
    await at(page, 'component-applicant-resume');
    await expect(stage(page).getByRole('heading', { name: 'Mateo Rivera', exact: true })).toBeVisible();
    await stage(page).getByRole('button', { name: 'Hire Mateo Rivera', exact: true }).tap();
    await expect(stage(page).getByRole('heading', { name: 'Mateo Rivera', exact: true })).toHaveCount(0);
  } finally { await context.close(); }
});

test('Shop, Workshop and the shared paper page reveal an inert restaurant behind a top-right return corner', async ({ page }) => {
  for (const width of [320, 390, 844]) {
    await page.setViewportSize({ width, height: width === 844 ? 390 : 844 });
    for (const id of ['shop', 'workshop', 'component-paper-page']) {
      await open(page, id);
      const paper = stage(page).locator('.paper-page');
      const corner = paper.getByRole('button', { name: 'Return to restaurant', exact: true });
      await corner.scrollIntoViewIfNeeded();
      const pageBox = await paper.boundingBox(), cornerBox = await corner.boundingBox();
      expect(cornerBox.x + cornerBox.width).toBeCloseTo(pageBox.x + pageBox.width - 8, 0);
      expect(cornerBox.y - pageBox.y).toBeCloseTo(8, 0);
      expect(cornerBox.width).toBeGreaterThanOrEqual(44);
      expect(cornerBox.height).toBeGreaterThanOrEqual(44);
      await expect(paper.locator('.paper-restaurant-background')).toHaveAttribute('inert', '');
      await expect(paper.locator('.paper-restaurant-background [data-floor-panel]')).toHaveCount(3);
      await expect(paper.locator('.paper-sheet')).toBeVisible();
      await corner.hover();
      await expect.poll(async () => (await corner.boundingBox()).width).toBeCloseTo(72, 0);
      if (id === 'shop') {
        await expect(paper.locator('.catalog-card')).toHaveCount(4);
        await expect(paper.locator('.group-heading, .scene-note, .scene-return')).toHaveCount(0);
        const prices = paper.locator('.buy-action');
        await expect(prices).toHaveText(['40', '80', '320', '600']);
        await expect(paper.getByRole('button', { name: 'Buy Belt tile', exact: true })).toBeEnabled();
      }
      if (id === 'workshop') await expect(paper.locator('.workshop-door')).toHaveCount(0);
    }
  }
});

test('paper corner returns restore the collapsed editor, exact camera and opener focus', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await open(page, 'restaurant-expanded');
  await panTo(page, 1.2);
  await stage(page).getByRole('button', { name: 'Edit', exact: true }).click();
  await stage(page).getByRole('button', { name: 'People layer', exact: true }).click();
  await expect(stage(page).locator('#editor-inventory-tray')).toHaveAttribute('inert', '');
  for (const name of ['Shop', 'Workshop']) {
    const opener = stage(page).getByRole('button', { name, exact: true });
    await opener.click();
    await at(page, name.toLowerCase());
    await expect.poll(() => floorPosition(page)).toBeCloseTo(1.2, 1);
    const corner = stage(page).getByRole('button', { name: 'Return to restaurant', exact: true });
    await corner.focus();
    await page.keyboard.press('Enter');
    await at(page, 'restaurant-edit');
    await expect.poll(() => floorPosition(page)).toBeCloseTo(1.2, 1);
    await expect(stage(page).locator('#editor-inventory-tray')).toHaveAttribute('inert', '');
    await expect(opener).toBeFocused();
  }
});

test('the HUD reserves away-earnings space and recipe tiles show known dish prices', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await open(page, 'component-restaurant-hud');
  const examples = stage(page).locator('.hud-example');
  const relativeShopPosition = example => example.evaluate(element => {
    const frame = element.querySelector('.restaurant-hud').getBoundingClientRect();
    const shop = element.querySelector('.shop-shortcut').getBoundingClientRect();
    return { x: shop.x - frame.x, y: shop.y - frame.y };
  });
  const steady = await relativeShopPosition(examples.nth(0));
  const away = await relativeShopPosition(examples.nth(1));
  expect(steady.x).toBeCloseTo(away.x, 1);
  expect(steady.y).toBeCloseTo(away.y, 1);
  await expect(examples.nth(0).getByText('+420 while away', { exact: true })).toBeHidden();
  await expect(examples.nth(1).getByText('+420 while away', { exact: true })).toBeVisible();
  await open(page, 'component-recipe-tile');
  const salmon = stage(page).getByRole('button', { name: 'Inspect Salmon nigiri', exact: true });
  const eel = stage(page).getByRole('button', { name: 'Inspect Eel roll', exact: true });
  await expect(salmon.locator('.recipe-tile-price')).toHaveText('18');
  await expect(eel.locator('.recipe-tile-price')).toHaveText('48');
  await expect(salmon).toHaveAccessibleDescription(/Price 18 coins/);
  await expect(stage(page).getByRole('button', { name: 'Inspect Undiscovered dish', exact: true }).locator('.recipe-tile-price')).toHaveCount(0);
  await open(page, 'recipe-picker');
  await expect(dialog(page).getByRole('button', { name: 'Inspect Salmon nigiri', exact: true }).locator('.recipe-tile-price')).toHaveText('18');
  await expect(dialog(page).getByRole('button', { name: 'Inspect Cucumber maki', exact: true }).locator('.recipe-tile-price')).toHaveText('12');
});

test('compact roster cards share their row with edge carets and preserve accessible pagination', async ({ page }) => {
  for (const width of [320, 390]) {
    await page.setViewportSize({ width, height: 844 });
    await open(page, 'component-roster-tray');
    const rail = stage(page).getByRole('navigation', { name: 'Staff pages', exact: true });
    const profiles = rail.locator('.roster-profile');
    await expect(profiles).toHaveCount(3);
    await expect(rail.getByRole('group', { name: 'Staff page 1 of 2', exact: true })).toBeVisible();
    await expect(rail.getByText('1 / 2', { exact: true })).toHaveCount(0);
    const previous = rail.getByRole('button', { name: 'Previous staff page', exact: true });
    const next = rail.getByRole('button', { name: 'Next staff page', exact: true });
    await expect(previous).toBeDisabled();
    const cards = await Promise.all((await profiles.all()).map(profile => profile.boundingBox()));
    const left = await previous.boundingBox(), right = await next.boundingBox();
    expect(left.x + left.width).toBeLessThanOrEqual(cards[0].x);
    expect(right.x).toBeGreaterThanOrEqual(cards[2].x + cards[2].width);
    expect(left.y + left.height / 2).toBeCloseTo(cards[0].y + cards[0].height / 2, 1);
    expect(right.y + right.height / 2).toBeCloseTo(cards[2].y + cards[2].height / 2, 1);
    for (const card of cards) {
      expect(card.width).toBeGreaterThanOrEqual(44);
      expect(card.width).toBeLessThan(90);
      expect(card.height).toBeGreaterThanOrEqual(44);
    }
    await next.click();
    await expect(rail.getByRole('group', { name: 'Staff page 2 of 2', exact: true })).toBeVisible();
    await expect(rail.getByRole('button', { name: 'Inspect Mateo Rivera', exact: true })).toBeVisible();
    await expect(next).toBeDisabled();
    await previous.click();
    await expect(rail.getByRole('button', { name: 'Inspect Lena Brooks', exact: true })).toBeVisible();
    await at(page, 'component-roster-tray');
  }
});

test('People uses shared roster profiles and closes stats or applicants back to the same editor', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 740 });
  for (const origin of ['restaurant-edit', 'component-editor-controls']) {
    await open(page, origin);
    await expect(stage(page).getByRole('group', { name: 'Staff page 1 of 1', exact: true })).toBeVisible();
    await expect(stage(page).getByRole('button', { name: 'Inspect Lena Brooks', exact: true })).toBeVisible();
    await stage(page).getByRole('button', { name: 'Inspect Omar Haddad', exact: true }).click();
    await expect(dialog(page).getByRole('heading', { name: 'Omar Haddad', exact: true })).toBeVisible();
    await expect(dialog(page).locator('.chef-facts')).toContainText('Cooking speed');
    await dialog(page).getByRole('button', { name: 'Close dialog', exact: true }).click();
    await at(page, origin);
    await expect(stage(page).getByRole('button', { name: 'People layer', exact: true })).toHaveAttribute('aria-expanded', 'true');
    await stage(page).getByRole('button', { name: 'Applicants', exact: true }).click();
    await expect(dialog(page).getByRole('button', { name: 'Back to staff', exact: true })).toHaveCount(0);
    await dialog(page).getByRole('button', { name: 'Close dialog', exact: true }).click();
    await at(page, origin);
    await expect(stage(page).getByRole('button', { name: 'Inspect Omar Haddad', exact: true })).toBeVisible();
  }
});

test('inventory edge carets browse objects without closing the editor or resetting the empty-belt state', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await open(page, 'inventory-empty');
  const rail = stage(page).getByRole('navigation', { name: 'Inventory pages', exact: true });
  const previous = rail.getByRole('button', { name: 'Previous inventory page', exact: true });
  const next = rail.getByRole('button', { name: 'Next inventory page', exact: true });
  await expect(previous).toBeDisabled();
  await expect(rail.getByRole('button', { name: 'Belt tile', exact: true })).toContainText('0');
  await expect(rail.getByRole('button', { name: 'Chair', exact: true })).toBeVisible();
  await next.click();
  await expect(rail.getByRole('button', { name: 'Plant', exact: true })).toBeVisible();
  await expect(next).toBeDisabled();
  await previous.click();
  await rail.getByRole('button', { name: 'Belt tile', exact: true }).click();
  await expect(stage(page).getByRole('status')).toHaveText('No belt tiles left');
  await expect(dialog(page)).toHaveCount(0);
  await expect(stage(page).getByRole('button', { name: 'Live', exact: true })).toBeVisible();
});

test('pause, early-return, dismissal and recipe-award overlays keep only their essential copy', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.setViewportSize({ width: 320, height: 740 });
  await open(page, 'expedition-pause');
  await expect(dialog(page).getByRole('heading', { name: 'Paused', exact: true })).toBeVisible();
  await expect(dialog(page).locator('.dialog-eyebrow, .dialog-scroll')).toHaveCount(0);
  const resume = await dialog(page).getByRole('button', { name: 'Resume', exact: true }).boundingBox();
  const early = await dialog(page).getByRole('button', { name: 'Return early…', exact: true }).boundingBox();
  expect(resume.y).toBeCloseTo(early.y, 1);
  expect(early.x).toBeGreaterThan(resume.x + resume.width);
  for (const button of [resume, early]) { expect(button.width).toBeGreaterThanOrEqual(44); expect(button.height).toBeGreaterThanOrEqual(44); }
  await dialog(page).getByRole('button', { name: 'Return early…', exact: true }).click();
  await expect(dialog(page).locator('.dialog-scroll')).toHaveText('Keep your haul. No completion bonus.');
  await open(page, 'expedition-resume');
  await expect(stage(page).getByRole('status')).toHaveText(/3\s*Returning to ship\.\.\./);
  await expect(stage(page).getByText(/Resuming expedition|Scene remains frozen|Frozen scene|Paused · no steering/)).toHaveCount(0);
  await open(page, 'staff-fire');
  await expect(dialog(page).getByText(/coin refund/)).toHaveCount(0);
  await expect(dialog(page)).toContainText('permanently leave');
  await open(page, 'recipe-award');
  await expect(dialog(page).getByText(/Chef requirement|Copper · Lv/)).toHaveCount(0);
  await expect(dialog(page)).toContainText('Base prep time');
  const award = dialog(page).getByRole('img', { name: 'Eel roll on a copper material background', exact: true });
  await expect(award).toBeVisible();
  expect(await award.evaluate(element => getComputedStyle(element).backgroundImage)).not.toBe('none');
  await open(page, 'staff-applicants');
  await expect(dialog(page).getByRole('button', { name: 'Back to staff', exact: true })).toHaveCount(0);
  const close = dialog(page).getByRole('button', { name: 'Close dialog', exact: true });
  await close.focus();
  await page.keyboard.press('Shift+Tab');
  expect(await dialog(page).evaluate(element => element.contains(document.activeElement))).toBe(true);
  await page.keyboard.press('Tab');
  await expect(close).toBeFocused();
});
