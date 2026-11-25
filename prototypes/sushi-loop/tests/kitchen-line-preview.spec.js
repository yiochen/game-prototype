import { test, expect } from '@playwright/test';
const path = '/prototypes/sushi-loop/design/kitchen-line-preview/?fresh';
const game = (page, fn) => page.evaluate(fn);
const centre = (page, k) => page.evaluate((cell) => window.kitchenLine.centre(cell), k);
// Every room has a floor of its own, and the board shows one at a time, so a tile is given as the room it is in
// and where it sits on that room's 7x7 floor.
const cell = (room, lx, ly) => `${room}:${lx},${ly}`;
const A = (lx, ly) => cell(0, lx, ly), Bm = (lx, ly) => cell(1, lx, ly);
const key = (page, k) => page.evaluate((c) => {
  const [room, rest] = c.split(':'), [lx, ly] = rest.split(',').map(Number), r = window.kitchenLine.E;
  const B = window.kitchenLine.balance, p = B.map.size + B.map.gap, at = B.rooms[+room];
  return r.key(at.col * p + lx, at.row * p + ly);
}, k);
const show = (page, room) => page.evaluate((i) => window.kitchenLine.show(i), room);
async function drag(page, cells) {
  const [x, y] = await centre(page, await key(page, cells[0]));
  await page.mouse.move(x, y); await page.mouse.down();
  for (const k of cells.slice(1)) { const [cx, cy] = await centre(page, await key(page, k)); await page.mouse.move(cx, cy, { steps: 3 }); }
  await page.mouse.up();
}
const tap = async (page, k) => { const [x, y] = await centre(page, await key(page, k)); await page.mouse.click(x, y); };
const at = (page, k, pick) => key(page, k).then((g) => page.evaluate(([c, src]) => eval(src)(window.kitchenLine, c), [g, pick.toString()]));
// The board is laid out from the canvas's measured size, so wait until the tile geometry agrees with the canvas
// on screen. Taps and drags are in page coordinates, and a stale measurement puts them on the wrong tiles.
const ready = (page) => page.waitForFunction(() => {
  const k = window.kitchenLine, c = document.querySelector('canvas');
  if (!k || !c) return false;
  const r = c.getBoundingClientRect();
  if (r.height < 100) return false;
  // the far corner of the room on the board has to land inside the canvas, which a stale measurement will not
  const room = k.balance.rooms[k.view], p = k.balance.map.size + k.balance.map.gap;
  const far = k.E.key(room.col * p + k.balance.map.size - 1, room.row * p + k.balance.map.size - 1);
  const [x, y] = k.centre(far);
  return x > r.left && x < r.right && y > r.top && y < r.bottom;
});
test.beforeEach(async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(path);
  await ready(page);
});

test('the board shows one 7x7 room at a time, and the chips above it are the switch', async ({ page }) => {
  expect(await game(page, () => window.kitchenLine.balance.map.size)).toBe(7);
  await expect(page.locator('.room')).toHaveCount(4);
  await expect(page.locator('.room').first()).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('.room').nth(1)).toHaveClass(/shut/);
  await page.locator('.room').nth(3).click();
  expect(await game(page, () => window.kitchenLine.view)).toBe(3);
  await expect(page.locator('.room').nth(3)).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('#flow')).toContainText('Tatami');
  await expect(page.locator('#hint')).toContainText('has not opened yet');
  // the inlet counts and door counts differ from room to room
  await expect(page.locator('.room').first()).toContainText('3 in · 1 out');
  await expect(page.locator('.room').nth(3)).toContainText('3 in · 3 out');
});

test('a door is tapped between serving its room and clearing the line', async ({ page }) => {
  expect(await at(page, A(6, 4), (k, c) => k.state.cells[c].kind)).toBe('out');
  await tap(page, A(6, 4));
  expect(await at(page, A(6, 4), (k, c) => k.state.cells[c].kind)).toBe('drop');
  await expect(page.locator('#hint')).toContainText('everything that reaches it is thrown out');
  await tap(page, A(6, 4));
  expect(await at(page, A(6, 4), (k, c) => k.state.cells[c].kind)).toBe('out');
  await expect(page.locator('#hint')).toContainText('serves the room now');
});

test('belt starts at an inlet in the wall, not in the middle of the floor', async ({ page }) => {
  await drag(page, [A(3, 4), A(4, 4), A(5, 4)]); // open floor, nowhere near a wall or a line
  expect(await at(page, A(3, 4), (k, c) => k.state.cells[c])).toBeUndefined();
  await expect(page.locator('#hint')).toContainText('inlet in the wall');
  await drag(page, [A(2, 6), A(2, 5), A(3, 5)]); // out of the spare inlet in the south wall, which is allowed
  expect(await at(page, A(2, 6), (k, c) => k.state.cells[c].links)).toEqual(['N']);
  expect(await at(page, A(2, 6), (k, c) => k.E.ends(k.state).find((e) => e.k === c).type)).toBe('head');
});

test('belt cannot be laid across the wall between two rooms', async ({ page }) => {
  await drag(page, [A(2, 6), A(2, 5), A(3, 5), A(4, 5), A(5, 5), A(6, 5)]);
  const over = await page.evaluate(() => {
    const k = window.kitchenLine;
    return k.E.draw(k.state, k.E.key(6, 5), k.E.key(7, 5)).why;
  });
  expect(over).toContain('cannot cross');
});

test('an inlet is tapped to choose the ingredient it delivers', async ({ page }) => {
  expect(await at(page, A(0, 1), (k, c) => k.state.cells[c].item)).toBe('rice');
  expect(await at(page, A(2, 6), (k, c) => k.state.cells[c].item)).toBeUndefined();
  await drag(page, [A(2, 6), A(2, 5), A(3, 5)]);
  await tap(page, A(2, 6));
  expect(await at(page, A(2, 6), (k, c) => k.state.cells[c].item)).toBe('rice');
  await expect(page.locator('#hint')).toContainText('plate of rice');
  await tap(page, A(2, 6));
  await expect(page.locator('#hint')).toContainText('plate of salmon');
  await expect.poll(() => at(page, A(2, 5), (k, c) => Object.keys(k.state.cells[c].dish?.on || {})), { timeout: 20000 }).toEqual(['fish']);
  await tap(page, A(2, 6)); // and round to delivering nothing at all
  expect(await at(page, A(2, 6), (k, c) => k.state.cells[c].item)).toBe(null);
  await expect(page.locator('#hint')).toContainText('delivers nothing now');
});

test('a Join takes plates in only at its ends, and hands them on only from its middle', async ({ page }) => {
  await drag(page, [A(3, 3), A(4, 3)]); // 3,3 is an end of the starter Join, so no belt runs on out of it
  expect(await at(page, A(4, 3), (k, c) => k.state.cells[c])).toBeUndefined();
  await expect(page.locator('#hint')).toContainText('not out of one');
  await drag(page, [A(4, 2), A(3, 2)]); // and nothing runs into its middle
  await expect(page.locator('#hint')).toContainText('out of its middle');
});

test('a belt drawn to nowhere is called out as a loose end', async ({ page }) => {
  await drag(page, [A(5, 2), A(5, 3), A(5, 4)]);
  expect(await at(page, A(5, 4), (k, c) => k.E.loose(k.state))).toEqual([await key(page, A(5, 4))]);
  await expect(page.locator('#hint')).toContainText('just stops');
  await expect(page.locator('#hint')).toContainText('door in the wall');
});

test('the starter line delivers nigiri to room A and the page never scrolls', async ({ page }) => {
  await expect.poll(() => game(page, () => window.kitchenLine.state.rooms[0].served), { timeout: 20000 }).toBeGreaterThan(0);
  await expect.poll(() => game(page, () => window.kitchenLine.state.coins)).toBeGreaterThan(0);
  await expect(page.locator('.room').first()).toContainText('A');
  expect(await game(page, () => Object.values(window.kitchenLine.state.cells).every((c) => c.links.length <= 2))).toBe(true);
  expect(await game(page, () => document.documentElement.scrollHeight <= innerHeight && document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('a branch can be drawn, dragging back undoes it and erase clears a tile', async ({ page }) => {
  await drag(page, [A(5, 2), A(5, 3), A(5, 4)]);
  expect(await at(page, A(5, 2), (k, c) => k.state.cells[c].links.length)).toBe(3);
  await drag(page, [A(5, 4), A(4, 4), A(3, 4), A(4, 4), A(5, 4)]); // dragging back along a branch undoes it
  expect(await at(page, A(4, 4), (k, c) => k.state.cells[c])).toBeUndefined();
  expect(await at(page, A(3, 4), (k, c) => k.state.cells[c])).toBeUndefined();
  await page.locator('[data-tool="erase"]').click();
  await tap(page, A(5, 4));
  expect(await at(page, A(5, 4), (k, c) => k.state.cells[c])).toBeUndefined();
});

test('a Join is bought from the dock, turned with the Turn button and dragged somewhere else', async ({ page }) => {
  await game(page, () => { window.kitchenLine.state.coins = 1000; });
  const join = page.locator('[data-part="join"]'), turn = page.locator('#turn');
  await expect(turn).toBeDisabled();
  await join.click();
  await expect(page.locator('#hint')).toContainText('three tiles in a line');
  await tap(page, A(4, 5));
  expect(await at(page, A(4, 5), (k, c) => k.state.cells[c].st)).toBe('join');
  expect(await at(page, A(4, 5), (k, c) => k.state.cells[c].arms)).toEqual([await key(page, A(4, 4)), await key(page, A(4, 6))]);
  await expect(page.locator('[data-part="sear"]')).toBeHidden();
  await expect(page.locator('[data-part]')).toHaveCount(7); // Join, Bin, Splitter, Sear, Wasabi, Roe, Press
  // putting one down selects it, so Turn is live straight away
  await expect(turn).toBeEnabled();
  await turn.click();
  expect(await at(page, A(4, 5), (k, c) => k.state.cells[c].arms)).toEqual([await key(page, A(3, 5)), await key(page, A(5, 5))]);
  await expect(page.locator('#hint')).toContainText('across');
  // changing tool drops the selection, and a tap picks it back up
  await page.locator('[data-tool="belt"]').click();
  await expect(turn).toBeDisabled();
  await tap(page, A(4, 5));
  await expect(page.locator('#hint')).toContainText('Join selected');
  await expect(turn).toBeEnabled();
  // and the selected machine is dragged to where it should go: one row down, where its ends fit as they are
  await drag(page, [A(4, 5), A(4, 6)]);
  expect(await at(page, A(4, 6), (k, c) => k.state.cells[c].st)).toBe('join');
  expect(await at(page, A(4, 5), (k, c) => k.state.cells[c])).toBeUndefined();
  await expect(page.locator('#hint')).toContainText('belt stays where you drew it');
});

test('a Splitter is bought from the dock once it is unlocked, and faces both ways', async ({ page }) => {
  await game(page, () => { window.kitchenLine.state.coins = 1000; window.kitchenLine.state.stage = 1; });
  await expect(page.locator('[data-part="split"]')).toBeVisible();
  await page.locator('[data-part="split"]').click();
  await expect(page.locator('#hint')).toContainText('exactly half each');
  await tap(page, A(4, 5));
  expect(await at(page, A(4, 5), (k, c) => k.state.cells[c].st)).toBe('split');
  expect(await at(page, A(4, 5), (k, c) => k.state.cells[c].arms)).toEqual([await key(page, A(4, 4)), await key(page, A(4, 6))]);
  await page.locator('#turn').click();
  expect(await at(page, A(4, 5), (k, c) => k.state.cells[c].axis)).toBe('h');
});

test('a 2x2 Press only goes where the belt already turns', async ({ page }) => {
  await game(page, () => { window.kitchenLine.state.coins = 9000; window.kitchenLine.state.stage = 6; });
  await page.locator('[data-part="press"]').click();
  await expect(page.locator('#hint')).toContainText('belt has to turn through it');
  await tap(page, A(5, 2)); // a straight piece of the starter line: its block would land on the line
  expect(await at(page, A(5, 2), (k, c) => k.state.cells[c].st)).toBeUndefined();
  await expect(page.locator('#hint')).toContainText('2x2 block');
  await page.locator('[data-tool="belt"]').click();
  await drag(page, [A(2, 6), A(2, 5), A(3, 5), A(3, 4), A(4, 4)]); // a line with a corner in it
  await drag(page, [A(4, 4), A(4, 3)]);
  await page.locator('[data-part="press"]').click();
  await tap(page, A(4, 4));
  expect(await at(page, A(4, 4), (k, c) => k.state.cells[c].work.length)).toBe(3);
  expect(await at(page, A(4, 4), (k, c) => k.state.cells[c].links.sort())).toEqual(['N', 'W']);
});

test('dragging an unselected machine still draws belt, and a tap elsewhere drops the selection', async ({ page }) => {
  await drag(page, [A(3, 3), A(4, 3)]); // an end of the starter Join, with nothing selected: this is belt drawing
  await expect(page.locator('#hint')).toContainText('not out of one');
  await tap(page, A(3, 2)); // select the Join
  await expect(page.locator('#hint')).toContainText('Join selected');
  await expect(page.locator('#turn')).toBeEnabled();
  await tap(page, A(5, 5)); // empty floor
  await expect(page.locator('#turn')).toBeDisabled();
  expect(await at(page, A(3, 2), (k, c) => k.state.cells[c].st)).toBe('join');
});

test('the flow line is about the room on the board, not the whole kitchen', async ({ page }) => {
  await expect(page.locator('#flow')).toContainText('Counter');
  await expect(page.locator('#flow')).toContainText('2 seats');
  await expect(page.locator('#flow')).not.toHaveClass(/short/);
  await expect.poll(() => game(page, () => window.kitchenLine.state.stage), { timeout: 90000 }).toBe(1);
  await expect(page.locator('#flow')).not.toHaveClass(/short/, { timeout: 2000 }); // the counter is still fine
  await page.locator('.room').nth(1).click();
  await expect(page.locator('#flow')).toContainText('6 seats');
  await expect(page.locator('#flow')).toHaveClass(/short/);
  await expect(page.locator('.room').nth(1)).toContainText('short');
  await expect(page.locator('#hint')).toContainText(/never get served|has run out|another inlet|Set an inlet|No inlet/);
});

test('a line with nothing to merge onto it keeps moving, and the hint names what it needs', async ({ page }) => {
  await game(page, () => {
    const { state, E, balance: B } = window.kitchenLine;
    const p = B.map.size + B.map.gap, b = (x, y) => E.key(B.rooms[1].col * p + x, B.rooms[1].row * p + y);
    state.coins = 1000; state.stage = 1; state.rooms[1].open = true; state.rooms[1].want = 'tamago';
    const line = [b(0, 2), b(1, 2), b(1, 3), b(1, 4), b(2, 4), b(3, 4), b(4, 4), b(5, 4), b(5, 3), b(6, 3), b(6, 4)];
    line.slice(1).forEach((k, i) => E.draw(state, line[i], k));
    E.cycleExit(state, b(0, 2), 2); // set the inlet to rice, with nothing on the line to join it to
    window.kitchenLine.show(1);
  });
  await ready(page);
  await expect.poll(() => game(page, () => window.kitchenLine.state.wasted), { timeout: 20000 }).toBeGreaterThan(1);
  await expect(page.locator('#hint')).toContainText('being cleared at B 6,4');
  await expect(page.locator('#hint')).toContainText('Join');
  expect(await game(page, () => window.kitchenLine.E.jams(window.kitchenLine.state))).toEqual([]);
});

test('a Join in the wrong place ruins plates, and the hint says how to clear them', async ({ page }) => {
  await game(page, () => {
    const { state, E, balance: B } = window.kitchenLine;
    const p = B.map.size + B.map.gap, b = (x, y) => E.key(B.rooms[1].col * p + x, B.rooms[1].row * p + y);
    state.coins = 1000; state.stage = 1; state.rooms[1].open = true;
    E.place(state, b(3, 2), 'join'); // a line of its own that merges salmon with egg: no recipe allows it
    E.turn(state, b(3, 2));
    for (const line of [[b(0, 2), b(1, 2), b(2, 2)], [b(5, 0), b(5, 1), b(5, 2), b(4, 2)],
      [b(3, 2), b(3, 3), b(4, 3), b(5, 3), b(6, 3), b(6, 4)]]) {
      line.slice(1).forEach((k, i) => E.draw(state, line[i], k));
    }
    const list = E.inletItems(state);
    E.cycleExit(state, b(0, 2), list.indexOf('fish'));
    E.cycleExit(state, b(5, 0), list.indexOf('egg'));
    window.kitchenLine.show(1);
  });
  await ready(page);
  await expect.poll(() => game(page, () => window.kitchenLine.state.spoiled), { timeout: 30000 }).toBeGreaterThan(0);
  await expect(page.locator('#hint')).toContainText('ruined plate');
  await expect(page.locator('#hint')).toContainText('Bin');
});

test('a machine will not be put down on the block another machine covers', async ({ page }) => {
  await game(page, () => { window.kitchenLine.state.coins = 1000; });
  await page.locator('[data-part="join"]').click();
  await tap(page, A(3, 3)); // an end of the starter Join
  expect(await at(page, A(3, 3), (k, c) => k.state.cells[c].st)).toBeUndefined();
  await expect(page.locator('#hint')).toContainText('part of the machine');
  await tap(page, A(4, 5)); // but three tiles of bare floor take one
  expect(await at(page, A(4, 5), (k, c) => k.state.cells[c].st)).toBe('join');
});

test('the cheat button hands over enough coins to buy anything at once', async ({ page }) => {
  expect(await game(page, () => window.kitchenLine.state.coins)).toBeLessThan(100);
  await expect(page.locator('[data-part="join"]')).toBeDisabled();
  await page.locator('#cheat').click();
  expect(await game(page, () => window.kitchenLine.state.coins)).toBeGreaterThan(9000);
  await expect(page.locator('#hint')).toContainText('Buy whatever you want to try');
  await expect(page.locator('[data-part="join"]')).toBeEnabled();
});

test('the recipe book shows every dish, what goes on the plate and what the kitchen needs', async ({ page }) => {
  await expect(page.locator('#bookDlg')).toBeHidden();
  await page.locator('#book').click();
  await expect(page.locator('#bookDlg')).toBeVisible();
  await expect(page.locator('#bookList li')).toHaveCount(10);
  const nigiri = page.locator('#bookList li').first();
  await expect(nigiri).toContainText('Nigiri');
  await expect(nigiri).toContainText('rice');
  await expect(nigiri).toContainText('salmon');
  await expect(nigiri).toContainText('2 inlets · 1 Join');
  // a dish with a process says which, and one the kitchen has not reached yet is marked
  const seared = page.locator('#bookList li', { hasText: 'Seared nigiri' });
  await expect(seared).toContainText('seared');
  await expect(seared).toContainText('not unlocked yet');
  await expect(page.locator('#bookList li', { hasText: 'Cucumber maki' })).toContainText('3 inlets · 2 Joins');
  await expect(page.locator('#bookList li', { hasText: 'Roe tamago' })).toContainText('Roe');
  await page.locator('#bookClose').click();
  await expect(page.locator('#bookDlg')).toBeHidden();
});

test('the skip button counts this stage\u2019s dishes as served and opens the next one', async ({ page }) => {
  expect(await game(page, () => window.kitchenLine.state.stage)).toBe(0);
  await expect(page.locator('#goalLabel')).toContainText('/8');
  await page.locator('#skip').click();
  await expect.poll(() => game(page, () => window.kitchenLine.state.stage), { timeout: 10000 }).toBe(1);
  await expect(page.locator('#banner')).toContainText('booth');
  await expect(page.locator('.room').nth(1)).not.toHaveClass(/shut/);
  await expect(page.locator('[data-part="split"]')).toBeVisible(); // the Splitter unlocks with it
  // and it keeps going, all the way to the last stage
  for (let i = 0; i < 5; i++) {
    await page.locator('#skip').click();
    await expect.poll(() => game(page, () => window.kitchenLine.state.stage), { timeout: 10000 }).toBe(i + 2);
  }
  await expect(page.locator('.room:not(.shut)')).toHaveCount(4);
  await expect(page.locator('[data-part="press"]')).toBeVisible();
  await page.locator('#skip').click();
  await expect.poll(() => game(page, () => window.kitchenLine.state.done), { timeout: 10000 }).toBe(true);
  await page.locator('#skip').click();
  await expect(page.locator('#hint')).toContainText('already open');
});

test('room B opens with the next stage and asks for its own dish', async ({ page }) => {
  await expect.poll(() => game(page, () => window.kitchenLine.state.stage), { timeout: 90000 }).toBe(1);
  await expect(page.locator('#banner')).toContainText('booth');
  await expect(page.locator('.room:not(.shut)')).toHaveCount(2); // the terrace and the tatami room are still shut
  await expect(page.locator('.room').nth(1)).toContainText('tamago');
  await page.locator('.room').nth(1).click();
  await ready(page);
  await expect(page.locator('#hint')).toContainText(/egg|seats|inlet|No inlet/);
});
