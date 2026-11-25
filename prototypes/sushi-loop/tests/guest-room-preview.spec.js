import { test, expect } from '@playwright/test';
const path = '/prototypes/sushi-loop/design/guest-room-preview/?fresh';
const game = (page, fn, arg) => page.evaluate(fn, arg);
const centre = (page, x, y) => page.evaluate(([a, b]) => window.guestRoom.centre(a, b), [x, y]);
const tap = async (page, x, y) => { const [a, b] = await centre(page, x, y); await page.mouse.click(a, b); };
async function drag(page, from, to) {
  const [a, b] = await centre(page, ...from), [c, d] = await centre(page, ...to);
  await page.mouse.move(a, b); await page.mouse.down(); await page.mouse.move(c, d, { steps: 5 }); await page.mouse.up();
}
const ready = (page) => page.waitForFunction(() => {
  const g = window.guestRoom, c = document.querySelector('canvas');
  if (!g || !c) return false;
  const r = c.getBoundingClientRect(), [x, y] = g.centre(6, 6);
  return r.height > 100 && x < r.right && y < r.bottom;
});
const piece = (page, x, y) => game(page, ([a, b]) => { const g = window.guestRoom; const i = g.E.itemAt(g.state, g.E.key(a, b)); return i && { kind: i.kind, x: i.x, y: i.y, tier: i.tier, style: i.style, rot: i.rot }; }, [x, y]);

for (const [name, size] of [['phone', { width: 390, height: 844 }], ['landscape', { width: 844, height: 390 }]]) {
  test(`${name}: the room, the dock and every piece fit on screen`, async ({ page }) => {
    await page.setViewportSize(size);
    await page.goto(path); await ready(page);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth || document.documentElement.scrollHeight > innerHeight);
    expect(overflow).toBe(false);
    const [x, y] = await centre(page, 6, 6), [x0, y0] = await centre(page, 0, 0);
    const vp = page.viewportSize();
    expect(x0).toBeGreaterThan(0); expect(y0).toBeGreaterThan(0); expect(x).toBeLessThan(vp.width); expect(y).toBeLessThan(vp.height);
    await expect(page.locator('#parts button')).toHaveCount(8);
  });
}

test.describe('phone', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(path); await ready(page);
    // no guests walk up unless a test lets them, so coin counts stay exact
    await game(page, () => { window.guestRoom.state.carry.arrive = -1e9; });
  });

  test('starts with four stools at the counter and the seats limit showing', async ({ page }) => {
    expect(await game(page, () => window.guestRoom.state.items.map((i) => i.kind))).toEqual(['stool', 'stool', 'stool', 'stool']);
    await expect(page.locator('#inside')).toContainText('/6');
    await expect(page.locator('#theme')).toContainText('100%');
    await expect(page.locator('#coins')).toHaveText('400');
  });

  test('the cheat fills the purse, and a picked piece goes down where the floor is tapped', async ({ page }) => {
    await page.locator('#cheat').click();
    await expect(page.locator('#coins')).toHaveText('10,400');
    await page.locator('#parts [data-kind="booth"]').click();
    await expect(page.locator('#sel')).toContainText('Booth');
    // a 2x2 piece tapped by the wall is shifted so the tapped tile is inside it
    await tap(page, 1, 6);
    expect(await piece(page, 1, 6)).toMatchObject({ kind: 'booth', x: 1, y: 5 });
    await expect(page.locator('#coins')).toHaveText('10,000');
    // a seat away from the belt is refused with the reason
    await page.locator('#parts [data-kind="stool"]').click();
    await tap(page, 6, 0);
    expect(await piece(page, 6, 0)).toBe(null);
    await expect(page.locator('#flow')).toContainText('touch the belt');
    // and so is one guests could not walk to, inside the loop
    await tap(page, 2, 3);
    expect(await piece(page, 2, 3)).toBe(null);
    await expect(page.locator('#flow')).toContainText('could not walk');
  });

  test('the style picker colours new pieces, and Paint restyles a placed one for free', async ({ page }) => {
    await page.locator('#cheat').click();
    await page.locator('#styles [data-style="ocean"]').click();
    await page.locator('#parts [data-kind="arch"]').click();
    await tap(page, 3, 2);
    expect(await piece(page, 3, 2)).toMatchObject({ kind: 'arch', style: 'ocean' });
    await expect(page.locator('#sel')).toContainText('Wave tunnel');
    await expect(page.locator('#theme')).toContainText('80%');
    await page.locator('#sel [data-act="done"]').click();
    await tap(page, 3, 2);
    await page.locator('#styles [data-style="zen"]').click();
    const coins = await page.locator('#coins').textContent();
    await page.locator('#sel [data-act="paint"]').click();
    expect(await piece(page, 3, 2)).toMatchObject({ style: 'zen' });
    await expect(page.locator('#coins')).toHaveText(coins);
    await expect(page.locator('#theme')).toContainText('100%');
  });

  test('a selected piece upgrades, turns, moves by drag and sells for a full refund', async ({ page }) => {
    await page.locator('#cheat').click();
    await page.locator('#parts [data-kind="glass"]').click();
    await tap(page, 0, 5);
    await page.locator('#sel [data-act="done"]').click();
    await tap(page, 0, 5);
    await expect(page.locator('#sel')).toContainText('★☆☆');
    await page.locator('#sel [data-act="up"]').click();
    expect(await piece(page, 0, 5)).toMatchObject({ tier: 2 });
    await page.locator('#sel [data-act="turn"]').click();
    expect(await piece(page, 0, 6)).toMatchObject({ rot: 1 });
    await drag(page, [0, 5], [2, 5]);
    expect(await piece(page, 2, 6)).toMatchObject({ kind: 'glass', x: 2, y: 5, rot: 1 });
    expect(await piece(page, 0, 5)).toBe(null);
    await page.locator('#sel [data-act="sell"]').click();
    expect(await piece(page, 2, 5)).toBe(null);
    await expect(page.locator('#coins')).toHaveText('10,400');
  });

  test('capacity and kitchen upgrades are bought from the dock', async ({ page }) => {
    await page.locator('#cheat').click();
    await page.locator('#cap').click();
    await expect(page.locator('#inside')).toContainText('/10');
    await page.locator('#kit').click();
    await expect(page.locator('#kit')).toContainText('Kitchen 20');
    expect(await game(page, () => window.guestRoom.state.coins)).toBe(10400 - 250 - 300);
  });

  test('guests come in, eat off the belt and pay, faster with the speed button', async ({ page }) => {
    await game(page, () => { window.guestRoom.state.carry.arrive = 0.99; });
    await page.locator('#speed').click(); await page.locator('#speed').click();
    await expect(page.locator('#speed')).toHaveText('×16');
    await page.waitForFunction(() => window.guestRoom.state.stats.plates >= 3, null, { timeout: 20000 });
    expect(await game(page, () => window.guestRoom.state.coins)).toBeGreaterThan(400);
  });

  test('pinball takes full guests away from their seat and sends them back hungry', async ({ page }) => {
    await game(page, () => {
      const g = window.guestRoom, s = g.state; s.coins = 1e5; s.kitchen = 5;
      g.E.place(s, 'pinball', 6, 6, 'zen');
      s.queue.push({ id: s.nextId++, size: 1, wait: 999, hue: 40 });
    });
    const saw = await game(page, () => {
      const g = window.guestRoom; let play = false, back = false;
      for (let i = 0; i < 600; i++) { g.run(1); for (const x of g.state.guests) { if (x.st === 'play') play = true; if (play && x.visits && (x.st === 'seat' || x.st === 'eat')) back = true; } }
      return { play, back };
    });
    expect(saw).toEqual({ play: true, back: true });
  });
});
