import test from 'node:test';
import assert from 'node:assert/strict';
import * as E from '../design/kitchen-line-preview/engine.js';
import { BALANCE as B } from '../design/kitchen-line-preview/balance.js';

const run = (s, until, max = 20000) => { for (let i = 0; i < max && !until(s); i++) E.tick(s); assert.ok(until(s), 'condition reached'); };
const ok = (r) => assert.ok(r.ok, r.why);
const path = (s, cells) => cells.slice(1).forEach((k, i) => ok(E.draw(s, cells[i], k)));
const dishes = (s) => Object.keys(s.cells).filter((k) => s.cells[k].dish);
const give = (s, n) => { s.coins += n; };
const heading = (s, k) => E.OPP[s.cells[k].dish.from];
const on = (s, k) => Object.keys(s.cells[k].dish.on).sort();
// Every room has a floor of its own, so a tile is named by its room and its place on that floor.
const R = (i) => { const r = B.rooms[i]; return (lx, ly) => E.key(r.col * (B.map.size + B.map.gap) + lx, r.row * (B.map.size + B.map.gap) + ly); };
const a = R(0), b = R(1), c = R(2), d = R(3);
// Sets an inlet to deliver one ingredient, however far along the list it is.
const deliver = (s, k, item) => {
  const list = E.inletItems(s);
  ok(E.cycleExit(s, k, list.indexOf(item) - list.indexOf(s.cells[k].item ?? null)));
};
// Turns a machine round until it faces the way the test wants it.
const faceIt = (s, k, want) => { for (let i = 0; i < 4 && E.facing(s, k) !== want; i++) ok(E.turn(s, k)); assert.equal(E.facing(s, k), want); };

// Room B's simplest kitchen: the rice inlet in the west wall and the egg inlet in the north wall merged by one
// Join, carried round to the door in the east wall.
const lineB = (s, x = 'rice', y = 'egg') => {
  give(s, 800);
  ok(E.place(s, b(3, 2), 'join'));
  faceIt(s, b(3, 2), 'h');
  path(s, [b(0, 2), b(1, 2), b(2, 2)]);
  path(s, [b(5, 0), b(5, 1), b(5, 2), b(4, 2)]);
  path(s, [b(3, 2), b(3, 3), b(4, 3), b(5, 3), b(6, 3), b(6, 4)]);
  deliver(s, b(0, 2), x);
  deliver(s, b(5, 0), y);
};
// Room A's salmon runs straight off the wall into the Join, with no tile to spare. Seared nigiri wants the
// salmon seared and the rice plain, so the salmon line is redrawn the long way round to make room for a Sear
// before the Join: a process marks everything already on the plate, and there is no taking it off again.
const searA = (s) => {
  E.unlink(s, a(3, 0), a(3, 1));
  path(s, [a(3, 0), a(4, 0), a(4, 1), a(3, 1)]);
  ok(E.place(s, a(4, 1), 'sear'));
  return a(4, 1);
};
// A ring of belt in the free floor of room A, drawn out of its south inlet as every line must be, then cut loose.
const RING = [a(2, 5), a(3, 5), a(4, 5), a(5, 5), a(5, 4), a(4, 4), a(3, 4), a(2, 4)];
const ring = (s) => { path(s, [a(2, 6), ...RING, a(2, 5)]); deliver(s, a(2, 6), 'rice'); };

test('the map is rooms of their own, each a square of floor with a wall between', () => {
  assert.deepEqual(B.rooms.map((r) => [r.col, r.row]), [[0, 0], [1, 0], [0, 1], [1, 1]]);
  assert.equal(B.map.size, 7, 'the size the finished game will draw');
  assert.deepEqual([B.grid.w, B.grid.h], [15, 15]);
  const s = E.createGame();
  assert.deepEqual([E.roomAt(a(6, 6)), E.roomAt('7,7'), E.roomAt(b(0, 0))], [0, -1, 1]);
  assert.equal(E.inRoom('7,0'), false, 'the wall between two rooms is no room’s floor');
  assert.deepEqual([E.label(a(3, 2)), E.label(d(0, 1))], ['A 3,2', 'D 0,1']);
  assert.match(E.draw(s, a(6, 5), '7,5').why, /cannot cross/, 'and belt cannot be laid across it');
  assert.match(E.place(s, '7,3', 'bin').why, /^$/, 'nor can a machine stand on it');
  // every room has inlets and doors scattered over all four of its walls, and no inlet faces a door across the room
  for (let i = 0; i < B.rooms.length; i++) {
    const r = B.rooms[i], wall = ([x, y]) => (x === 0 ? 'W' : x === 6 ? 'E' : y === 0 ? 'N' : 'S');
    const walls = new Set([...r.in, ...r.out].map(wall));
    assert.equal(walls.size, 4, `room ${r.name} uses all four walls`);
    for (const [ix, iy] of r.in) for (const [ox, oy] of r.out) {
      const across = (wall([ix, iy]) === E.OPP[wall([ox, oy])]) && (ix === ox || iy === oy);
      assert.ok(!across, `room ${r.name}: ${ix},${iy} faces ${ox},${oy} straight across`);
    }
  }
});

test('the kitchen it starts with merges two inlets into nigiri for room A, and it flows', () => {
  const s = E.createGame();
  assert.ok(Object.values(s.cells).every((cl) => cl.links.length <= 2), 'no loop, no junction');
  assert.deepEqual(E.ends(s).map((e) => `${E.label(e.k)} ${e.type}`).sort(),
    ['A 0,1 head', 'A 3,0 head', 'A 3,1 tail', 'A 3,2 head', 'A 3,3 tail', 'A 6,4 tail']);
  assert.deepEqual(E.loose(s), []);
  run(s, (x) => dishes(x).some((k) => Object.keys(x.cells[k].dish.on).length === 1), 60);
  run(s, (x) => x.rooms[0].q.length > 0, 160);
  assert.equal(E.recipeOf(s.rooms[0].q[0]), 'nigiri');
  run(s, (x) => x.coins > 0, 60);
  assert.equal(s.spoiled, 0);
});

test('an inlet delivers the one ingredient it is set to, and a plate of it is all a line ever starts with', () => {
  const s = E.createGame();
  assert.deepEqual([s.cells[a(0, 1)].item, s.cells[a(3, 0)].item], ['rice', 'fish'], 'the starter pair');
  assert.equal(s.cells[a(2, 6)].item, undefined, 'every other inlet delivers nothing until it is set');
  run(s, (x) => x.cells[a(1, 1)].dish, 40);
  assert.deepEqual(on(s, a(1, 1)), ['rice'], 'and the plate arrives with that one ingredient already on it');
  // an inlet with nothing set puts nothing on the belt, however much belt runs out of it
  path(s, [a(2, 6), a(2, 5), a(3, 5)]);
  for (let i = 0; i < 80; i++) E.tick(s);
  assert.deepEqual([a(2, 6), a(2, 5), a(3, 5)].filter((k) => s.cells[k].dish), []);
  // tapping it walks through the ingredients the kitchen has reached, and through delivering nothing at all
  assert.deepEqual(E.inletItems(s), [null, 'rice', 'fish'], 'egg comes later');
  assert.deepEqual(E.cycleExit(s, a(2, 6)), { ok: true, item: 'rice' });
  assert.deepEqual(E.cycleExit(s, a(2, 6)), { ok: true, item: 'fish' });
  assert.deepEqual(E.cycleExit(s, a(2, 6)), { ok: true, item: null });
  deliver(s, a(2, 6), 'fish');
  run(s, (x) => x.cells[a(2, 5)].dish, 40);
  assert.deepEqual(on(s, a(2, 5)), ['fish'], 'a line can be fed salmon just as freely as rice');
  s.stage = 5;
  assert.deepEqual(E.inletItems(s), [null, 'nori', 'rice', 'cuke', 'fish', 'egg', 'tuna'], 'the list grows with the kitchen');
  assert.ok(!E.inletItems(s).includes('roe'), 'but roe is an add-on, and only its station spoons it on');
  assert.ok(!E.inletItems(s).includes('wasabi'));
});

test('belt runs straight into a door, and nothing ever comes back out of one', () => {
  const s = E.createGame();
  give(s, 2000);
  assert.deepEqual(E.flows(s, a(6, 3)), ['S'], 'the last piece of the starter line runs into the wall');
  assert.deepEqual(E.flows(s, a(6, 4)), [], 'a door never puts anything back on the belt');
  assert.match(E.draw(s, a(6, 4), a(6, 5)).why, /not out of it/, 'and no belt can be drawn out of one');
  assert.match(E.place(s, a(6, 4), 'bin').why, /keeps its tile/);
  // a line may reach a door from any side it likes
  path(s, [b(0, 2), b(1, 2), b(1, 3), b(1, 4), b(2, 4), b(3, 4), b(4, 4), b(5, 4), b(5, 3), b(6, 3), b(6, 4)]);
  assert.deepEqual(E.flows(s, b(6, 3)), ['S']);
  assert.deepEqual(E.ends(s).filter((e) => e.k === b(6, 4)), [{ k: b(6, 4), type: 'tail' }]);
});

test('a line may only be drawn out of an inlet, a Join’s middle, a Splitter’s end, or belt already laid', () => {
  const s = E.createGame();
  assert.deepEqual(B.rooms.map((r) => r.in.length), [3, 3, 4, 3], 'the rooms have different numbers of inlets');
  assert.ok(E.isIn(s.cells[a(2, 6)]) && !E.isIn(s.cells[a(6, 4)]) && !E.isDoor(s.cells[a(2, 6)]));
  assert.match(E.draw(s, a(3, 5), a(4, 5)).why, /inlet in the wall/, 'not in the middle of the floor');
  ok(E.draw(s, a(2, 6), a(2, 5))); // out of an inlet
  ok(E.draw(s, a(2, 5), a(3, 5))); // and on from belt already laid
  assert.deepEqual(E.ends(s).find((e) => e.k === a(2, 6)), { k: a(2, 6), type: 'head' });
  ok(E.draw(s, a(2, 6), a(1, 6))); // an inlet feeds as many belts as touch it
  assert.deepEqual(E.flows(s, a(2, 6)).sort(), ['N', 'W']);
  assert.match(E.draw(s, a(2, 5), a(2, 6)).why, /not into it/, 'an inlet is a source, never a destination');
  s.cells[a(2, 5)].dish = { on: { rice: [], fish: [] }, worked: true, from: 'S', moved: false, pk: a(2, 5) };
  for (let i = 0; i < 20; i++) E.tick(s);
  assert.equal(s.cells[a(2, 6)].dish, undefined, 'nothing ever travels into an inlet');
});

test('a Join covers three tiles, takes a plate in at each end and hands one on from the middle', () => {
  const s = E.createGame();
  assert.equal(B.stations.join.span, 3);
  assert.deepEqual([s.cells[a(3, 2)].axis, s.cells[a(3, 2)].arms], ['v', [a(3, 1), a(3, 3)]]);
  assert.equal(s.cells[a(3, 1)].jn, a(3, 2));
  assert.match(E.draw(s, a(4, 2), a(3, 2)).why, /out of its middle/, 'nothing runs into the middle');
  assert.match(E.draw(s, a(3, 3), a(4, 3)).why, /not out of one/, 'and nothing runs on out of an end');
  give(s, 500);
  assert.match(E.place(s, a(3, 1), 'bin').why, /part of the machine/);
  // the ends wait for each other: one plate on its own is never handed on, and is not jammed either
  const t = E.createGame();
  t.cells[a(3, 0)].item = null; // the salmon line delivers nothing, so only rice ever reaches the Join
  run(t, (x) => x.cells[a(3, 3)].dish, 120);
  for (let i = 0; i < 80; i++) E.tick(t);
  assert.ok(t.cells[a(3, 3)].dish, 'the rice is still waiting at its end');
  assert.equal(t.cells[a(3, 2)].dish, undefined, 'nothing has been handed on');
  assert.deepEqual(E.jams(t), [], 'a plate waiting for its partner is doing its job');
  assert.equal(t.rooms[0].served, 0);
  assert.equal(t.spoiled, 0);
  // erasing any tile of it lifts the whole machine, refunded in full
  ok(E.erase(t, a(3, 1)));
  assert.equal(t.cells[a(3, 2)].st, undefined);
  assert.equal(t.cells[a(3, 1)].jn, undefined);
  assert.equal(t.coins, B.stations.join.price);
});

test('a Splitter is a Join the other way round: in at the middle, out of both ends, exactly half each', () => {
  const s = E.createGame();
  s.stage = 1; give(s, 500);
  ok(E.place(s, a(4, 5), 'split'));
  faceIt(s, a(4, 5), 'v');
  assert.deepEqual(s.cells[a(4, 5)].arms, [a(4, 4), a(4, 6)]);
  assert.match(E.draw(s, a(4, 5), a(5, 5)).why, /into its middle/, 'nothing runs out of the middle');
  assert.match(E.draw(s, a(5, 4), a(4, 4)).why, /not into one/, 'and nothing runs into an end');
  path(s, [a(2, 6), a(3, 6), a(3, 5), a(4, 5)]); // belt into its middle
  path(s, [a(4, 4), a(5, 4), a(5, 5)]); // and a line out of each end
  path(s, [a(4, 6), a(5, 6)]);
  assert.deepEqual(E.ends(s).filter((e) => e.k === a(4, 5)).map((e) => e.type), ['tail'], 'the middle is where a line ends');
  assert.deepEqual(E.ends(s).filter((e) => e.k === a(4, 4)).map((e) => e.type), ['head'], 'and an end is where one begins');
  deliver(s, a(2, 6), 'rice');
  const land = { [a(5, 5)]: 0, [a(5, 6)]: 0 };
  for (let i = 0; i < 1200; i++) { E.tick(s); for (const k in land) if (s.cells[k].dish) { land[k]++; s.cells[k].dish = null; } }
  const [west, east] = Object.values(land);
  assert.ok(west > 10 && Math.abs(west - east) <= 1, `strictly one then the other: ${west} / ${east}`);
});

test('a machine turns where it stands, and the belt it leaves behind stays put', () => {
  const s = E.createGame();
  give(s, 900);
  ok(E.place(s, a(4, 5), 'join'));
  assert.deepEqual([s.cells[a(4, 5)].axis, s.cells[a(4, 5)].arms], ['v', [a(4, 4), a(4, 6)]]);
  path(s, [a(2, 6), a(3, 6), a(4, 6)]); // a line into its south end
  assert.deepEqual(E.turn(s, a(4, 5)), { ok: true, face: 'h' }, 'it turns with belt attached');
  assert.deepEqual(s.cells[a(4, 5)].arms, [a(3, 5), a(5, 5)]);
  assert.equal(s.cells[a(4, 6)].jn, undefined, 'the old end is plain floor again');
  assert.deepEqual(s.cells[a(4, 6)].links, ['W'], 'and it keeps the belt that was drawn to it');
  assert.deepEqual(E.loose(s), [a(4, 6)], 'which is now a loose end for the player to redraw');
  assert.deepEqual(E.turn(s, a(4, 5)), { ok: true, face: 'v' });
  assert.equal(s.cells[a(4, 6)].jn, a(4, 5), 'and turning it back picks the same belt up again');
  // it will not be turned onto its own output belt, nor over a wall connector
  ok(E.draw(s, a(4, 5), a(5, 5)));
  assert.match(E.turn(s, a(4, 5)).why, /no room to turn/, 'an end may not be put where that belt goes');
  ok(E.place(s, a(2, 5), 'join'));
  assert.deepEqual(s.cells[a(2, 5)].axis, 'h', 'an end cannot stand on the inlet in the south wall');
  assert.match(E.turn(s, a(2, 5)).why, /no room to turn/);
});

test('a machine is dragged to a new tile, keeping the way it faces where that still fits', () => {
  const s = E.createGame();
  s.stage = 2; give(s, 4000);
  E.unlink(s, a(3, 0), a(3, 1));
  path(s, [a(3, 0), a(4, 0), a(5, 0), a(5, 1), a(4, 1), a(3, 1)]);
  ok(E.place(s, a(5, 1), 'sear'));
  assert.deepEqual([s.cells[a(5, 1)].face, s.cells[a(5, 1)].work], ['E', [a(6, 1)]]);
  assert.equal(E.machineAt(s, a(6, 1)), a(5, 1), 'either tile belongs to the machine');
  // it will not shuffle one tile along its own line: its body has to stand on bare floor, and that tile is belt
  assert.equal(E.fitsAt(s, a(5, 1), a(4, 1)), null);
  assert.deepEqual(E.fitsAt(s, a(5, 1), a(5, 0)), [a(5, 0), a(6, 0)], 'and it says where it would land');
  assert.deepEqual(E.moveTo(s, a(5, 1), a(5, 0)), { ok: true, k: a(5, 0), face: 'E', turned: false });
  assert.equal(s.cells[a(5, 1)].st, undefined);
  assert.equal(s.cells[a(6, 1)], undefined, 'the floor it stood on is free again');
  assert.deepEqual(s.cells[a(5, 0)].work, [a(6, 0)]);
  assert.deepEqual(s.cells[a(5, 1)].links.sort(), ['N', 'W'], 'the belt it was standing on is untouched');
  run(s, (x) => x.rooms[0].q.length > 0, 900);
  assert.equal(E.recipeOf(s.rooms[0].q[0]), 'seared', 'and the line still works where it stands now');
});

test('a machine turns to fit when it has to, and says so', () => {
  const s = E.createGame();
  s.stage = 4; give(s, 4000);
  ok(E.place(s, a(5, 2), 'roe'));
  assert.equal(s.cells[a(5, 2)].face, 'N');
  ok(E.place(s, a(4, 1), 'bin')); // the tile the roe would want on its new home's north side
  const r = E.moveTo(s, a(5, 2), a(4, 2));
  assert.deepEqual([r.ok, r.k, r.turned], [true, a(4, 2), true]);
  assert.deepEqual(s.cells[a(4, 2)].work, [a(4, 3)], 'it took the free side instead');
  assert.match(E.moveTo(s, a(4, 2), a(0, 1)).why, /covers 2 tiles|wall|tile/, 'and it will not go where it does not fit');
});

test('a 2x2 machine stands on a corner of itself, so the belt has to turn through it', () => {
  const s = E.createGame();
  s.stage = 6; give(s, 9000);
  assert.equal(B.stations.press.block, 2);
  assert.deepEqual(E.faces('press'), ['N', 'E', 'S', 'W']);
  // a straight piece of belt has no corner for it: whichever way round it goes, its block lands on the line
  assert.match(E.place(s, a(5, 2), 'press').why, /2x2 block/);
  // so the line is given a corner, and the block fills the quarter the belt does not use
  path(s, [a(2, 6), a(2, 5), a(3, 5), a(3, 4), a(4, 4)]);
  path(s, [a(4, 4), a(4, 3)]);
  ok(E.place(s, a(4, 4), 'press'));
  const cl = s.cells[a(4, 4)];
  assert.deepEqual([cl.face, cl.work], ['E', [a(5, 4), a(4, 5), a(5, 5)]], 'four tiles in all');
  const pts = [a(4, 4), ...cl.work].map(E.local), xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  assert.deepEqual([Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)], [1, 1], 'a 2x2 block');
  // the two faces it leaves free are at right angles, so no straight line can ever pass through it
  const mine = new Set([a(4, 4), ...cl.work]);
  const free = ['N', 'E', 'S', 'W'].filter((dir) => !mine.has(E.step(a(4, 4), dir)));
  assert.deepEqual(free.sort(), ['N', 'W']);
  assert.deepEqual(s.cells[a(4, 4)].links.sort(), ['N', 'W'], 'which is exactly where the belt already turns');
  deliver(s, a(2, 6), 'rice');
  run(s, (x) => x.cells[a(4, 3)].dish, 400);
  assert.deepEqual(s.cells[a(4, 3)].dish.on, { rice: ['press'] }, 'and it presses what goes through it');
});

test('only a machine with more than one way round can be turned', () => {
  const s = E.createGame();
  give(s, 500);
  path(s, [a(2, 6), a(2, 5)]);
  ok(E.place(s, a(2, 5), 'bin'));
  assert.equal(E.canTurn(s, a(2, 5)), false);
  assert.match(E.turn(s, a(2, 5)).why, /nothing to turn/);
  assert.equal(E.canTurn(s, a(3, 2)), true);
  assert.deepEqual(E.faces('join'), ['v', 'h']);
  assert.deepEqual(E.faces('split'), ['v', 'h']);
  assert.deepEqual(E.faces('sear'), ['N', 'E', 'S', 'W']);
  assert.deepEqual(E.faces('bin'), [null]);
  assert.deepEqual(E.faces('wasabi'), [null], 'a one-tile add-on has nothing to turn either');
});

test('a Bin covers one tile and ends the line: belt runs into it and no further', () => {
  const s = E.createGame();
  give(s, 500);
  assert.equal(B.stations.bin.size, 1);
  path(s, [a(2, 6), a(2, 5)]);
  ok(E.place(s, a(2, 5), 'bin'));
  assert.equal(s.cells[a(2, 5)].work?.length ?? 0, 0, 'it claims no floor beside it');
  assert.match(E.draw(s, a(2, 5), a(3, 5)).why, /end of a line/, 'and nothing runs on out of it');
  assert.deepEqual(E.ends(s).find((e) => e.k === a(2, 5)), { k: a(2, 5), type: 'tail' });
  deliver(s, a(2, 6), 'fish');
  run(s, (x) => x.events.some((e) => e.type === 'bin'), 200);
  assert.equal(E.jams(s).length, 0, 'everything that reaches it comes off the belt');
});

test('a door serves its room or clears the line, and does nothing else', () => {
  const s = E.createGame();
  assert.deepEqual(E.KINDS, ['out', 'drop']);
  assert.deepEqual(B.rooms.map((r) => r.out.length), [1, 2, 1, 3], 'the rooms have different numbers of doors');
  run(s, (x) => x.rooms[0].served > 1, 500);
  ok(E.cycleExit(s, a(6, 4)));
  assert.equal(s.cells[a(6, 4)].kind, 'drop');
  s.events.length = 0;
  let handed = 0;
  const waste = s.wasted;
  for (let i = 0; i < 400; i++) { E.tick(s); handed += s.events.filter((e) => e.type === 'exit').length; s.events.length = 0; }
  assert.equal(handed, 0, 'a door set to clear hands nothing to the room');
  assert.ok(s.wasted > waste + 3, 'it throws the dishes away');
  assert.equal(E.jams(s).length, 0, 'and the belt never stops');
  ok(E.cycleExit(s, a(6, 4)));
  assert.equal(s.cells[a(6, 4)].kind, 'out');
});

test('a plate holds a set, so which end of the Join an ingredient comes in at makes no difference', () => {
  const s = E.createGame();
  s.stage = 1; s.rooms[1].open = true; s.rooms[1].want = 'any';
  deliver(s, a(0, 1), 'fish'); deliver(s, a(3, 0), 'rice'); // the starter pair, swapped over
  lineB(s, 'rice', 'fish'); // and the mirror line the usual way round
  run(s, (x) => x.rooms[0].q.length > 0 && x.rooms[1].q.length > 0, 900);
  assert.equal(E.recipeOf(s.rooms[0].q[0]), 'nigiri', 'salmon on the north end makes the same nigiri');
  assert.equal(E.recipeOf(s.rooms[1].q[0]), 'nigiri', 'and so does rice on the west end');
  assert.equal(s.spoiled, 0);
});

test('a process marks whatever is on the plate at the time, so its order does matter', () => {
  // seared nigiri is torched salmon on plain rice, so the Sear belongs on the salmon line, before the Join
  assert.deepEqual(B.recipes.seared.has, { rice: [], fish: ['sear'] });
  const s = E.createGame();
  s.stage = 2; give(s, 4000);
  searA(s);
  run(s, (x) => x.cells[a(3, 1)].dish, 900);
  assert.deepEqual(s.cells[a(3, 1)].dish.on, { fish: ['sear'] }, 'the salmon is seared on its own, before the rice meets it');
  run(s, (x) => x.rooms[0].q.length > 0, 900);
  assert.equal(E.recipeOf(s.rooms[0].q[0]), 'seared');
  assert.equal(s.spoiled, 0);
  // the same machine after the Join: it marks the rice as well, and a process can never be taken off again
  const t = E.createGame();
  t.stage = 2; give(t, 4000);
  ok(E.place(t, a(5, 2), 'sear'));
  run(t, (x) => x.cells[a(6, 2)].dish, 900);
  assert.deepEqual(t.cells[a(6, 2)].dish.on, { rice: ['sear'], fish: ['sear'] }, 'everything on the plate is seared');
  assert.equal(E.recipeOf(t.cells[a(6, 2)].dish), null, 'so it is no dish at all');
  assert.ok(E.ruined(t.cells[a(6, 2)].dish), 'it is ruined: seared rice is on no recipe');
  assert.equal(E.needs(t.cells[a(6, 2)].dish, 'seared'), null);
  // and a plate joined before its sear says so: nothing left to it would make a dish
  assert.equal(E.needs({ on: { rice: [], fish: [] } }, 'seared'), 'order', 'the Sear had to run before the Join');
  // pressed tuna is the other way round: the whole block is pressed, rice and all, so its Press goes after
  assert.deepEqual(B.recipes.oshi.has, { rice: ['press'], tuna: ['press'] });
  assert.equal(E.needs({ on: { rice: [], tuna: [] } }, 'oshi'), 'press');
});

test('a tail always takes the plate, so a half-built line drains instead of locking solid', () => {
  const s = E.createGame();
  s.stage = 1; s.rooms[1].open = true; s.rooms[1].want = 'tamago';
  path(s, [b(0, 2), b(1, 2), b(1, 3), b(1, 4), b(2, 4), b(3, 4), b(4, 4), b(5, 4), b(5, 3), b(6, 3), b(6, 4)]);
  deliver(s, b(0, 2), 'rice'); // a line with nothing to merge onto it
  run(s, (x) => x.wasted > 2, 600);
  assert.equal(s.rooms[1].served, 0, 'nothing is sold');
  assert.deepEqual(E.wasting(s)?.add, 'join', 'and it says what would stop the waste');
  let moving = 0;
  for (let i = 0; i < 30; i++) { E.tick(s); moving += [b(1, 3), b(1, 4), b(2, 4), b(3, 4), b(4, 4)].filter((k) => s.cells[k].dish).length; }
  assert.ok(moving > 5, 'the belt is still carrying plates along');
  assert.deepEqual(E.jams(s), []);
  // the same two ingredients through a Join make the dish
  const t = E.createGame();
  t.stage = 1; t.rooms[1].open = true; t.rooms[1].want = 'tamago';
  lineB(t, 'rice', 'egg');
  run(t, (x) => x.rooms[1].served > 2, 2400);
  assert.equal(t.spoiled, 0);
});

test('the belt carries the direction, not the machines on it', () => {
  const s = E.createGame();
  assert.deepEqual(E.flows(s, a(4, 2)), ['E'], 'the starter line was laid west to east');
  assert.equal(s.cells[a(3, 2)].out, undefined, 'and a machine holds no direction of its own');
  ok(E.draw(s, a(5, 2), a(4, 2)));
  assert.deepEqual(E.flows(s, a(4, 2)), [], 'that piece runs the other way now, so nothing leaves this tile');
  assert.deepEqual(E.flows(s, a(5, 2)).sort(), ['E', 'W']);
  ok(E.draw(s, a(4, 2), a(5, 2)));
  assert.deepEqual(E.flows(s, a(4, 2)), ['E']);
});

test('a loop needs no wall connector, and tapping the belt turns the whole loop round', () => {
  const s = E.createGame();
  ring(s);
  run(s, (x) => x.cells[a(3, 5)].dish, 200);
  ok(E.erase(s, a(2, 6))); // cut loose, which is the only way to a loop of its own
  assert.deepEqual(E.loose(s), [], 'a loop has no ends at all');
  assert.deepEqual(E.flows(s, a(4, 5)), ['E'], 'it runs the way it was drawn');
  run(s, (x) => RING.some((k) => x.cells[k].dish), 60);
  const at = RING.find((k) => s.cells[k].dish), went = heading(s, at);
  ok(E.reverse(s, a(5, 4))); // tap any tile of the loop
  assert.deepEqual(E.flows(s, a(4, 5)), ['W'], 'every piece of it runs the other way now');
  assert.equal(heading(s, at), E.OPP[went], 'and the plate already on the belt is going back the other way');
  for (let i = 0; i < 120; i++) E.tick(s);
  assert.equal(s.spoiled, 0);
  assert.match(E.reverse(s, a(5, 2)).why, /wall/, 'a line joined to the wall takes its direction from there');
});

test('every machine takes the same time, holds the plate while it works and backs the belt up behind it', () => {
  const s = E.createGame();
  run(s, (x) => x.cells[a(3, 2)].hold === B.speed, 160);
  assert.ok(s.cells[a(3, 1)].dish && s.cells[a(3, 3)].dish, 'the Join has a plate waiting at each end');
  for (let i = 0; i < B.speed - 1; i++) E.tick(s);
  assert.equal(s.cells[a(3, 2)].dish, undefined, 'the middle is still empty while it works');
  E.tick(s);
  assert.deepEqual(on(s, a(3, 2)), ['fish', 'rice'], 'the two plates come out as one when the work is done');
});

test('a Join is dumb too: it merges whatever is waiting, and a set no recipe allows ruins the plate', () => {
  const s = E.createGame();
  s.stage = 1; s.rooms[1].open = true;
  lineB(s, 'fish', 'egg'); // salmon with egg on the same plate is no dish at all
  run(s, (x) => x.spoiled > 0, 900);
  const bad = E.spoiled(s)[0];
  assert.deepEqual(on(s, bad), ['egg', 'fish']);
  assert.ok(E.ruined(s.cells[bad].dish) && !E.finished(s.cells[bad].dish));
  for (let i = 0; i < 300; i++) { E.tick(s); assert.ok(s.rooms[1].q.every((x) => !E.ruined(x)), 'a ruined plate is never delivered'); }
});

test('a machine with nothing to do to a plate lets it straight through', () => {
  const s = E.createGame();
  s.stage = 4; give(s, 9000);
  ok(E.place(s, a(5, 2), 'roe'));
  ok(E.place(s, a(4, 2), 'roe')); // a second roe station on a line that already has one
  run(s, (x) => x.rooms[0].served > 2, 1400);
  assert.equal(s.spoiled, 0, 'roe twice is still one roe, not a ruined plate');
  assert.equal(E.changes('roe', { on: { rice: [], fish: [], roe: [] } }), false);
});

test('a machine covers a block of floor, and that block is the whole of the spacing rule', () => {
  const s = E.createGame();
  s.stage = 2; give(s, 4000);
  assert.equal(B.stations.sear.size, 2);
  ok(E.place(s, a(5, 2), 'sear'));
  assert.deepEqual(s.cells[a(5, 2)].work, [a(5, 1)], 'the sear covers two tiles in all');
  assert.match(E.place(s, a(5, 1), 'bin').why, /part of the machine/, 'its floor is taken');
  assert.match(E.draw(s, a(5, 1), a(4, 1)).why, /part of the machine/, 'and belt cannot cross it either');
  // nothing else keeps machines apart: one may sit on the very next belt tile if its block fits
  ok(E.place(s, a(4, 2), 'sear'));
  assert.deepEqual(s.cells[a(4, 2)].work, [a(4, 1)]);
});

test('a machine needs free floor beside it, keeps it clear, and gives it back when lifted', () => {
  const s = E.createGame();
  s.stage = 2; give(s, 1000);
  ok(E.place(s, a(5, 2), 'sear'));
  assert.equal(s.cells[a(5, 1)].w, a(5, 2));
  ok(E.erase(s, a(5, 1))); // erasing the work space lifts the machine it belongs to
  assert.equal(s.cells[a(5, 2)].st, undefined);
  assert.equal(s.cells[a(5, 1)], undefined);
  assert.equal(s.coins, 1000);
  ok(E.draw(s, a(5, 2), a(5, 1))); // the floor it gave back takes belt off the line again
});

test('nothing sorts: a room takes whatever the belt brings it, and pays extra only for what it asked for', () => {
  const s = E.createGame();
  s.stage = 1; s.rooms[0].want = 'tamago'; // room A asks for a dish this line cannot make
  assert.deepEqual(E.unfed(s, 'tamago', 0), ['egg'], 'no inlet in this room is delivering the egg it wants');
  assert.deepEqual(E.missing(s, 'tamago', 0), [], 'and the Join it needs is already there');
  run(s, (x) => x.rooms[0].served > 2, 900);
  assert.equal(E.recipeOf(s.rooms[0].q[0] || { on: { rice: [], fish: [] } }), 'nigiri', 'the nigiri is served all the same');
  const plain = E.createGame();
  run(plain, (x) => x.coins >= B.recipes.nigiri.value, 400);
  assert.equal(plain.coins, B.recipes.nigiri.value, 'a room paid the plain price for a dish it did not ask for');
});

test('a plate waiting at one end of a Join says so, once it is clear nothing is coming to the other', () => {
  const s = E.createGame();
  s.cells[a(3, 0)].item = null; // the salmon line is turned off, so only rice ever arrives
  for (let i = 0; i < 220; i++) E.tick(s);
  assert.deepEqual(E.lonely(s), { k: a(3, 3), other: a(3, 1) });
  assert.deepEqual(E.jams(s).includes(a(3, 3)), false, 'it is early, not jammed');
  deliver(s, a(3, 0), 'fish');
  run(s, (x) => E.lonely(x) === null, 200);
  run(s, (x) => x.rooms[0].served > 0, 300);
});

test('a branch into a Bin takes plates off the belt, ruined ones included', () => {
  const s = E.createGame();
  s.stage = 1; s.rooms[1].open = true;
  lineB(s, 'fish', 'egg'); // salmon with egg is no dish at all
  run(s, (x) => x.spoiled > 2, 1400);
  give(s, 300);
  path(s, [b(4, 3), b(4, 4), b(4, 5)]);
  ok(E.place(s, b(4, 5), 'bin'));
  run(s, (x) => x.events.some((e) => e.type === 'bin'), 900);
  deliver(s, b(0, 2), null); deliver(s, b(5, 0), null); // stop the wall, so the belt can empty
  run(s, (x) => E.spoiled(x).length === 0, 4000);
  assert.deepEqual(E.jams(s), []);
});

test('a full room backs the line up instead of letting dishes be thrown away', () => {
  const s = E.createGame();
  s.rooms[0].cd = 100000; // room A stops eating and fills up
  run(s, (x) => x.rooms[0].q.length === B.queue, 900);
  for (let i = 0; i < 600; i++) E.tick(s);
  assert.equal(s.spoiled, 0, 'a backed-up line spoils nothing');
  assert.ok(dishes(s).length > 4, 'and the belt behind it has backed up');
});

test('a junction takes turns without looking, so both branches get their share whatever is down them', () => {
  const s = E.createGame();
  // three belts out of one tile is how a line is split in thirds; merging two of them again makes two thirds
  path(s, [a(5, 2), a(5, 3), a(5, 4)]);
  path(s, [a(5, 2), a(5, 1)]);
  assert.equal(s.cells[a(5, 2)].outs.length, 3, 'a junction with three ways out');
  assert.deepEqual(E.loose(s).sort(), [a(5, 1), a(5, 4)].sort());
  const land = { [a(5, 1)]: 0, [a(5, 4)]: 0, [a(6, 4)]: 0 };
  let served = 0;
  for (let i = 0; i < 2000; i++) {
    E.tick(s);
    served += s.events.filter((e) => e.type === 'exit').length; s.events.length = 0;
    for (const k of [a(5, 1), a(5, 4)]) if (s.cells[k].dish) { land[k]++; s.cells[k].dish = null; }
  }
  const thirds = [land[a(5, 1)], land[a(5, 4)], served];
  assert.ok(Math.min(...thirds) > 8, `every way out gets its share: ${thirds.join(' / ')}`);
  assert.ok(Math.max(...thirds) - Math.min(...thirds) <= 3, `and they are even: ${thirds.join(' / ')}`);
});

test('a packed ring still turns', () => {
  const s = E.createGame();
  ring(s);
  ok(E.erase(s, a(2, 6)));
  for (const k of RING) s.cells[k].dish = { on: { rice: [], fish: [] }, worked: true, from: 'W' };
  const before = RING.map((k) => s.cells[k].dish);
  E.tick(s);
  assert.equal(RING.filter((k) => s.cells[k].dish).length, RING.length, 'no dish was lost');
  assert.ok(RING.some((k, i) => s.cells[k].dish !== before[i]), 'the ring moved');
});

test('each room is judged on its own line, and a Splitter never makes more of an ingredient', () => {
  const s = E.createGame();
  const one = E.capacity(s);
  assert.deepEqual(one.rooms.map((r) => !!r), [true, false, false, false], 'a room that has not opened counts for nothing');
  assert.equal(one.rooms[0].seats, B.rooms[0].seats);
  assert.equal(one.short, false, 'two inlets and a Join keep the counter fed');
  s.stage = 1; s.rooms[1].open = true; s.rooms[1].want = 'tamago';
  const two = E.capacity(s);
  assert.equal(two.rooms[0].short, false, 'the booth opening does not take anything away from the counter');
  assert.ok(two.rooms[1].short, 'the booth has no line of its own yet');
  assert.match(two.rooms[1].limitText, /inlet in this room/, 'and the wall is what is holding it back');
  lineB(s, 'rice', 'egg');
  assert.equal(E.capacity(s).rooms[1].short, false, 'a line of its own feeds its six seats');
  // splitting the rice in two does not make more rice: the dish is still capped by the scarcest ingredient
  const was = E.capacity(s).rooms[1].made;
  give(s, 300);
  ok(E.place(s, b(1, 4), 'split'));
  assert.equal(E.capacity(s).rooms[1].made, was, 'a Splitter divides a stream, it never multiplies one');
  s.stage = 4; s.rooms[1].want = 'jewel';
  assert.ok(E.capacity(s).rooms[1].short);
  assert.equal(E.capacity(s).rooms[1].limit, 'roe');
  assert.deepEqual(E.missing(s, 'jewel', 1), ['roe'], 'roe is an add-on, so a station puts it on');
  assert.deepEqual(E.unfed(s, 'jewel', 1), [], 'and the wall is already delivering both its base ingredients');
});

test('placing costs coins, erasing gives them back, and locked parts are refused', () => {
  const s = E.createGame();
  assert.match(E.place(s, a(3, 5), 'sear').why, /not unlocked/);
  assert.match(E.place(s, a(3, 5), 'join').why, /costs/);
  give(s, 250);
  ok(E.place(s, a(3, 5), 'join'));
  assert.equal(s.coins, 50);
  assert.match(E.place(s, a(3, 5), 'bin').why, /One machine/);
  assert.match(E.place(s, a(6, 4), 'bin').why, /wall connector/);
  ok(E.erase(s, a(3, 5)));
  assert.equal(s.coins, 250);
  assert.equal(B.filters, undefined, 'there are no filters: the belt is the only thing that steers a plate');
});

test('three ingredients means two Joins in series, and nothing before the last one is a dish yet', () => {
  const s = E.createGame();
  s.stage = 3; give(s, 4000);
  s.rooms[2].open = true; s.rooms[2].want = 'maki';
  // the terrace wants cucumber maki: rice, cucumber and nori, so two merges one after the other
  ok(E.place(s, c(2, 2), 'join')); faceIt(s, c(2, 2), 'v');
  ok(E.place(s, c(4, 3), 'join')); faceIt(s, c(4, 3), 'v');
  path(s, [c(1, 0), c(1, 1), c(2, 1)]);
  path(s, [c(0, 3), c(1, 3), c(2, 3)]);
  path(s, [c(2, 2), c(3, 2)]);
  path(s, [c(4, 0), c(4, 1), c(4, 2)]);
  path(s, [c(3, 2), c(3, 3), c(3, 4), c(4, 4)]);
  path(s, [c(4, 3), c(5, 3), c(5, 4), c(5, 5), c(6, 5)]);
  deliver(s, c(1, 0), 'rice'); deliver(s, c(4, 0), 'cuke'); deliver(s, c(0, 3), 'nori');
  assert.deepEqual(E.loose(s), []);
  run(s, (x) => x.cells[c(3, 2)].dish, 600);
  assert.deepEqual(on(s, c(3, 2)), ['nori', 'rice'], 'two of the three are on after the first Join');
  assert.equal(E.recipeOf(s.cells[c(3, 2)].dish), null, 'which is no dish yet');
  assert.ok(!E.ruined(s.cells[c(3, 2)].dish), 'and not ruined either: it is on its way to one');
  run(s, (x) => x.rooms[2].q.length > 0, 1600);
  assert.equal(E.recipeOf(s.rooms[2].q[0]), 'maki');
  assert.equal(s.spoiled, 0);
});

test('a room with two doors is fed by two lines, with a Splitter dividing the one rice inlet', () => {
  const s = E.createGame();
  s.stage = 1; s.rooms[1].open = true; s.rooms[1].want = 'tamago';
  give(s, 1200);
  ok(E.place(s, b(2, 3), 'split')); faceIt(s, b(2, 3), 'v');
  ok(E.place(s, b(4, 1), 'join')); faceIt(s, b(4, 1), 'h');
  ok(E.place(s, b(4, 4), 'join')); faceIt(s, b(4, 4), 'h');
  path(s, [b(0, 2), b(1, 2), b(1, 3), b(2, 3)]); // one rice inlet into the Splitter
  path(s, [b(2, 2), b(3, 2), b(3, 1)]); // half the rice to the north line
  path(s, [b(5, 0), b(5, 1)]);
  path(s, [b(4, 1), b(4, 0), b(3, 0), b(2, 0), b(1, 0)]);
  path(s, [b(2, 4), b(3, 4)]); // and half to the south line
  path(s, [b(3, 6), b(4, 6), b(5, 6), b(5, 5), b(5, 4)]);
  path(s, [b(4, 4), b(4, 3), b(5, 3), b(6, 3), b(6, 4)]);
  deliver(s, b(0, 2), 'rice'); deliver(s, b(5, 0), 'egg'); deliver(s, b(3, 6), 'egg');
  assert.deepEqual(E.loose(s), [], 'both lines run from the wall to a door of their own');
  assert.equal(E.capacity(s).rooms[1].short, false, 'two lines feed the booth\u2019s six seats');
  const served = {};
  run(s, (x) => x.rooms[1].served > 8, 6000);
  s.events.length = 0; // the counter has been serving all along, and this is about the booth's two doors
  for (let i = 0; i < 1200; i++) { E.tick(s); for (const e of s.events) if (e.type === 'exit' && E.roomAt(e.k) === 1) served[e.k] = (served[e.k] || 0) + 1; s.events.length = 0; }
  assert.equal(Object.keys(served).length, 2, 'both doors are handing dishes to the guests');
  assert.equal(s.spoiled, 0);
});

test('the kitchen can be grown stage by stage until all four rooms are served', () => {
  const s = E.createGame();
  const buy = (k, id) => { run(s, (x) => x.coins >= E.price(id), 40000); ok(E.place(s, k, id)); };
  run(s, (x) => x.stage >= 1);
  // The booth wants tamago. Its six seats take more than one line can carry, so the rice inlet is split in two
  // and each half is merged with an egg inlet of its own, each line running to a door of its own.
  buy(b(2, 3), 'split'); faceIt(s, b(2, 3), 'v');
  buy(b(4, 1), 'join'); faceIt(s, b(4, 1), 'h');
  buy(b(4, 4), 'join'); faceIt(s, b(4, 4), 'h');
  path(s, [b(0, 2), b(1, 2), b(1, 3), b(2, 3)]);
  path(s, [b(2, 2), b(3, 2), b(3, 1)]);
  path(s, [b(5, 0), b(5, 1)]);
  path(s, [b(4, 1), b(4, 0), b(3, 0), b(2, 0), b(1, 0)]);
  path(s, [b(2, 4), b(3, 4)]);
  path(s, [b(3, 6), b(4, 6), b(5, 6), b(5, 5), b(5, 4)]);
  path(s, [b(4, 4), b(4, 3), b(5, 3), b(6, 3), b(6, 4)]);
  deliver(s, b(0, 2), 'rice'); deliver(s, b(5, 0), 'egg'); deliver(s, b(3, 6), 'egg');
  assert.equal(E.capacity(s).rooms[1].short, false, 'the booth has two lines of its own now');
  assert.deepEqual(E.loose(s), []);
  run(s, (x) => x.stage >= 2);
  // The counter pays for seared nigiri: torched salmon on plain rice. A process marks everything already on
  // the plate, so the Sear has to run on the salmon line before the Join, and the salmon line is redrawn the
  // long way round to leave it a tile to stand on.
  run(s, (x) => x.coins >= E.price('sear'), 40000);
  searA(s);
  assert.deepEqual(E.loose(s), []);
  run(s, (x) => x.stage >= 3);
  // The terrace wants cucumber maki: three ingredients off the wall, so two Joins one after the other.
  buy(c(2, 2), 'join'); faceIt(s, c(2, 2), 'v');
  buy(c(4, 3), 'join'); faceIt(s, c(4, 3), 'v');
  path(s, [c(1, 0), c(1, 1), c(2, 1)]);
  path(s, [c(0, 3), c(1, 3), c(2, 3)]);
  path(s, [c(2, 2), c(3, 2)]);
  path(s, [c(4, 0), c(4, 1), c(4, 2)]);
  path(s, [c(3, 2), c(3, 3), c(3, 4), c(4, 4)]);
  path(s, [c(4, 3), c(5, 3), c(5, 4), c(5, 5), c(6, 5)]);
  deliver(s, c(1, 0), 'rice'); deliver(s, c(4, 0), 'cuke'); deliver(s, c(0, 3), 'nori');
  run(s, (x) => x.stage >= 4);
  // The booth pays for roe: an add-on, so a station of its own on each of its two lines.
  buy(b(2, 0), 'roe'); faceIt(s, b(2, 0), 'S');
  buy(b(5, 3), 'roe'); faceIt(s, b(5, 3), 'N');
  run(s, (x) => x.stage >= 5);
  // The tatami room opens. Its rice comes off the west wall and its fish off the north wall.
  buy(d(2, 2), 'join'); faceIt(s, d(2, 2), 'h');
  path(s, [d(0, 1), d(0, 2), d(1, 2)]);
  path(s, [d(2, 0), d(2, 1), d(3, 1), d(3, 2)]);
  path(s, [d(2, 2), d(2, 3), d(2, 4), d(2, 5), d(3, 5), d(3, 6)]);
  deliver(s, d(0, 1), 'rice');
  deliver(s, d(2, 0), 'fish');
  assert.deepEqual(E.loose(s), []);
  run(s, (x) => x.stage >= 6);
  // Last, the tatami room pays for pressed tuna: tuna off the wall, and a 2x2 Press on the corner its line
  // already turns on, since that is the only way a belt can pass through one.
  deliver(s, d(2, 0), 'tuna');
  buy(d(2, 5), 'press');
  assert.deepEqual(s.cells[d(2, 5)].work, [d(2, 6), d(1, 5), d(1, 6)]);
  run(s, (x) => x.done);
  assert.ok(s.rooms.every((r) => r.served > 0), 'every one of the four rooms has been fed');
  for (const k of E.jams(s)) ok(E.erase(s, k));
  run(s, (x) => E.jams(x).length === 0, 300);
  console.log(`done at tick ${s.tick} (${Math.round((s.tick * B.tickMs) / 1000)}s), coins ${s.coins}, dishes ${s.total}, ruined ${s.spoiled}, wasted ${s.wasted}`);
});
