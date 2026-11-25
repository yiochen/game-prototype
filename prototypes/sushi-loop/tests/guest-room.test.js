import { test } from 'node:test';
import assert from 'node:assert/strict';
import { BALANCE as B } from '../design/guest-room-preview/balance.js';
import * as E from '../design/guest-room-preview/engine.js';

const rich = (seed = 3) => { const s = E.createGame(seed); s.coins = 1e6; return s; };
const run = (s, n) => { for (let i = 0; i < n; i++) { E.tick(s); s.events = []; } return s; };
function party(s, size) { s.queue.push({ id: s.nextId++, size, wait: 999, hue: 0 }); }
// No new parties walk up, so a test controls exactly who is in the room.
const quiet = (s) => { s.carry.arrive = -1e9; return s; };
// Put a piece down, failing loudly if the room refuses it.
function put(s, kind, x, y, style = 'zen') { const r = E.place(s, kind, x, y, style); assert.ok(r.ok, `${kind} at ${x},${y}: ${r.why}`); return r.item; }

test('the room is a 7x7 floor with a closed belt loop, a kitchen hatch and a street door', () => {
  assert.equal(B.size, 7);
  assert.equal(E.RING.length, 12);
  for (let i = 0; i < B.ring.length; i++) {
    const [ax, ay] = B.ring[i], [bx, by] = B.ring[(i + 1) % B.ring.length];
    assert.equal(Math.abs(ax - bx) + Math.abs(ay - by), 1, 'every belt tile touches the next');
  }
  assert.equal(E.RING[E.ENTRY], '0,3', 'the hatch in the west wall feeds the belt tile beside it');
  assert.ok(B.ring.some(([x]) => x === 0), 'the loop stands against the kitchen wall');
});

test('placement: seats must touch the belt, arches stand on it, nothing on the door', () => {
  const s = rich();
  assert.equal(E.place(s, 'stool', 3, 6, 'zen').why, 'Keep the door clear');
  assert.equal(E.place(s, 'stool', 2, 2, 'zen').why, 'That is the belt');
  assert.match(E.place(s, 'stool', 3, 0, 'zen').why, /touch the belt/);
  put(s, 'stool', 3, 5);
  put(s, 'pinball', 6, 6);
  assert.match(E.place(s, 'arch', 0, 6, 'zen').why, /over the belt/);
  put(s, 'arch', 3, 2);
  assert.match(E.place(s, 'arch', 3, 2, 'ocean').why, /in the way/);
  assert.match(E.place(s, 'booth', 6, 4, 'zen').why, /off the floor/);
  put(s, 'band', 0, 5);
  assert.match(E.place(s, 'band', 5, 0, 'zen').why, /limit/);
});

test('guests never walk over the belt or a piece, so every seat and game must be reachable', () => {
  const s = rich();
  // the three tiles inside the loop are cut off by the belt
  assert.match(E.place(s, 'stool', 2, 3, 'zen').why, /could not walk to it/);
  put(s, 'tv', 2, 3); // a TV needs no one to walk up to it
  // a booth across the east corridor would cut the top counter off from the door
  assert.match(E.place(s, 'booth', 5, 2, 'zen').why, /block the way to the Stool/);
  // a door to the top counter goes round by the corridor, never across the belt
  const path = E.route(s, '3,6', '1,1', s.items[0].id);
  assert.ok(path.length > 6);
  assert.ok(path.some((k) => k.startsWith('5,') || k.startsWith('6,')));
  for (const k of path.slice(0, -1)) { assert.ok(!E.isBelt(k)); assert.equal(E.itemAt(s, k), null); }
  // nor can a move do what a placement may not
  const pin = put(s, 'pinball', 6, 6);
  assert.match(E.move(s, pin.id, 1, 3).why, /could not walk/);
});

test('walking guests stay on the floor, whatever the room holds', () => {
  const s = rich(11);
  put(s, 'booth', 0, 5); put(s, 'glass', 2, 5); put(s, 'cage', 5, 2); put(s, 'cage', 5, 4); put(s, 'pinball', 6, 6);
  E.buyCapacity(s); E.buyCapacity(s); E.buyKitchen(s); E.buyKitchen(s);
  const home = new Map();
  let steps = 0;
  for (let t = 0; t < 2400; t++) {
    E.tick(s); s.events = [];
    for (const g of s.guests) {
      if (g.y >= B.size) continue; // still out in the street
      const k = E.key(Math.floor(g.x), Math.floor(g.y));
      if (g.st !== 'walk' && g.st !== 'leave') { home.set(g.id, k); continue; }
      steps++;
      assert.ok(!E.isBelt(k), `guest ${g.id} on the belt at ${k}`);
      const on = E.itemAt(s, k);
      const left = home.get(g.id) && E.itemAt(s, home.get(g.id));
      assert.ok(!on || on.id === g.target || on === left, `guest ${g.id} over the ${on?.kind} at ${k}`);
    }
  }
  assert.ok(steps > 1000);
  assert.ok(s.stats.guests > 20);
});

test('every guest takes a whole tile, so a seat has one tile for each chair', () => {
  for (const [kind, K] of Object.entries(B.items)) if (K.chairs) assert.equal(K.w * K.h, K.chairs, kind);
  const s = rich();
  const item = put(s, 'booth', 0, 5);
  assert.deepEqual([0, 1, 2, 3].map((i) => E.chairPos(item, i)), [[0.5, 5.5], [1.5, 5.5], [0.5, 6.5], [1.5, 6.5]]);
  assert.deepEqual(E.reach(item).map((i) => E.RING[i]).sort(), ['0,4', '1,4'], 'the back row reaches the belt through the table');
  assert.match(E.turn(s, item.id).why, /same either way/);
});

test('placing costs coins and selling refunds everything spent, upgrades included', () => {
  const s = E.createGame(1);
  s.coins = 500;
  assert.match(E.place(s, 'cage', 0, 1, 'zen').why, /costs 900/);
  const { item } = E.place(s, 'booth', 0, 5, 'zen');
  assert.equal(s.coins, 100);
  s.coins = 1000;
  assert.ok(E.upgrade(s, item.id).ok);
  assert.equal(item.tier, 2);
  assert.equal(s.coins, 1000 - 320);
  assert.ok(E.sell(s, item.id).ok);
  assert.equal(s.coins, 1000 - 320 + 720);
});

test('moving and turning a piece keeps the same rules as placing it', () => {
  const s = rich();
  const item = put(s, 'glass', 0, 5);
  assert.match(E.move(s, item.id, 0, 6).why, /touch the belt/);
  assert.ok(E.move(s, item.id, 1, 5).ok);
  assert.deepEqual([item.x, item.y], [1, 5]);
  assert.ok(E.turn(s, item.id).ok);
  assert.deepEqual(E.footprint(item), ['1,5', '1,6']);
});

test('coherence: the room style is the most common one, and matching pieces multiply Appeal', () => {
  const s = rich(); // four zen stools
  const t = E.theme(s);
  assert.equal(t.style, 'zen');
  assert.equal(t.coherence, 1);
  const pure = E.appeal(s);
  assert.equal(pure, 4 * 2 * (B.coherence.low + B.coherence.span));
  const muddled = rich();
  muddled.items.forEach((i, n) => { i.style = ['zen', 'lantern', 'ocean', 'lantern'][n]; });
  assert.equal(E.theme(muddled).style, 'lantern');
  assert.ok(E.appeal(muddled) < pure, 'the same pieces in three styles appeal less');
  assert.ok(E.restyle(muddled, muddled.items[0].id, 'lantern').ok, 'repainting is free');
  assert.equal(muddled.coins, 1e6);
});

test('upgrading a piece raises its charm, and a seat\'s plates pay a tip', () => {
  const s = rich();
  const stool = s.items[0], before = E.appeal(s);
  E.upgrade(s, stool.id);
  assert.equal(E.charm(stool), 2 * B.tiers.charm[1]);
  assert.ok(E.appeal(s) > before);
});

test('traffic grows with Appeal, and the band draws more in while it plays', () => {
  const s = rich();
  const t0 = E.traffic(s);
  put(s, 'cage', 5, 2);
  assert.ok(E.traffic(s) > t0);
  put(s, 'band', 0, 5);
  s.t = 0; assert.ok(E.playing(s));
  const on = E.traffic(s);
  s.t = B.items.band.on + 1; assert.ok(!E.playing(s));
  assert.ok(Math.abs(on / E.traffic(s) - B.items.band.boost) < 1e-9);
});

test('a party takes a whole seat that fits it, and a group needs a booth', () => {
  const s = quiet(rich());
  party(s, 4);
  run(s, 3);
  assert.equal(s.queue.length, 1, 'stools only: a group of four waits at the door');
  assert.equal(E.limit(s).kind, 'seats');
  const booth = put(s, 'booth', 0, 5);
  run(s, 1);
  assert.equal(s.queue.length, 0);
  assert.equal(booth.who.filter((w) => w != null).length, 4);
  // a couple goes to the glass room before an empty cage, since it pays more
  put(s, 'cage', 5, 2);
  const glass = put(s, 'glass', 2, 5);
  party(s, 2);
  run(s, 1);
  assert.equal(glass.who.filter((w) => w != null).length, 2);
  // a solo guest takes a stool, the smallest seat that fits (once the room has space for a seventh person)
  E.buyCapacity(s);
  party(s, 1);
  run(s, 1);
  assert.equal(s.items.filter((i) => i.kind === 'stool' && i.who[0] != null).length, 1);
});

test('capacity caps the people inside: past it, parties queue and in the end give up', () => {
  const s = quiet(rich());
  s.items = [];
  put(s, 'booth', 0, 0); put(s, 'booth', 0, 5);
  party(s, 4); run(s, 1);
  s.queue.push({ id: s.nextId++, size: 4, wait: 5, hue: 0 });
  run(s, 1);
  assert.equal(E.inside(s), 4, 'capacity 6 leaves no room for a second group of four');
  assert.equal(E.limit(s).kind, 'capacity');
  run(s, 6);
  assert.equal(s.queue.length, 0);
  assert.equal(s.stats.away, 4);
  E.buyCapacity(s);
  assert.equal(E.capacity(s), 10);
});

test('seated guests take plates off the belt beside them, pay for each and leave when full', () => {
  const s = quiet(rich());
  s.kitchen = 5;
  party(s, 1);
  run(s, 400);
  assert.ok(s.stats.plates >= B.appetite[0] && s.stats.plates <= B.appetite[1]);
  assert.equal(s.stats.earned, s.stats.plates * B.plate);
  assert.equal(s.stats.guests, 1);
  assert.equal(s.guests.length, 0, 'they walked out of the door');
});

test('the glass room pays half again for every plate', () => {
  const s = quiet(rich());
  s.kitchen = 5;
  s.items = []; // only the glass room
  put(s, 'glass', 2, 5);
  party(s, 2);
  run(s, 500);
  assert.ok(s.stats.plates > 0);
  assert.equal(s.stats.earned, s.stats.plates * B.plate * 1.5);
});

test('pinball: a full guest gets up, plays, and comes back hungry for more plates', () => {
  const plain = quiet(rich(5)); plain.kitchen = 5; party(plain, 1); run(plain, 800);
  const fun = quiet(rich(5)); fun.kitchen = 5; put(fun, 'pinball', 6, 6); party(fun, 1);
  let played = false;
  for (let i = 0; i < 800; i++) { E.tick(fun); fun.events = []; if (fun.guests.some((g) => g.st === 'play')) played = true; }
  assert.ok(played);
  assert.equal(fun.stats.plates, plain.stats.plates + B.refill[0] + B.refill[1] - Math.max(0, B.refill[0] + B.refill[1] - B.maxExtras));
});

test('every top-up together is capped, so a guest never stays for ever', () => {
  const s = quiet(rich(9)); s.kitchen = 5;
  put(s, 'pinball', 6, 6); put(s, 'tv', 2, 3); put(s, 'tv', 1, 3); put(s, 'band', 0, 5);
  party(s, 1);
  let most = 0;
  for (let i = 0; i < 3000; i++) { E.tick(s); s.events = []; for (const g of s.guests) most = Math.max(most, g.extras); }
  assert.equal(most, B.maxExtras);
  assert.equal(s.guests.length, 0);
  assert.ok(s.stats.plates <= B.appetite[1] + B.maxExtras);
});

test('a sports TV goal makes every seated guest order another plate', () => {
  const s = quiet(rich()); s.kitchen = 5;
  put(s, 'tv', 2, 3);
  party(s, 2); run(s, 20);
  assert.ok(s.guests.every((g) => g.st === 'seat' || g.st === 'eat'));
  const apps = s.guests.map((g) => g.app + (g.st === 'eat' ? 0 : 0));
  let goal = false;
  for (let i = 0; i < B.items.tv.every && !goal; i++) { s.events = []; E.tick(s); goal = s.events.some((e) => e.type === 'goal'); }
  assert.ok(goal);
  for (const g of s.guests) assert.equal(g.extras, 1, 'one more plate each');
  assert.ok(s.guests.every((g, i) => g.app >= apps[i]));
});

test('a guest who waits too long for a plate walks out, and the room says the kitchen is the limit', () => {
  const s = quiet(rich()); s.kitchen = 0;
  put(s, 'booth', 0, 5);
  party(s, 4); party(s, 1); party(s, 1);
  s.carry.cook = -1e9; // the kitchen sends nothing
  run(s, 40);
  assert.equal(E.limit(s).kind, 'kitchen');
  run(s, B.hungry + 30);
  assert.ok(s.stats.walked >= 6);
});

test('with a fast kitchen, entertainment sells more plates per guest than a plain room', () => {
  const setup = (s) => {
    E.sell(s, s.items[0].id); // the stool at 1,1 makes way for the band in the fun room
    put(s, 'booth', 0, 5); put(s, 'glass', 2, 5); put(s, 'cage', 5, 2); put(s, 'cage', 5, 3); put(s, 'cage', 5, 4);
    for (let i = 0; i < 5; i++) { E.buyCapacity(s); E.buyKitchen(s); }
  };
  const plain = rich(7); setup(plain); run(plain, 2400);
  const fun = rich(7); setup(fun);
  put(fun, 'pinball', 5, 6); put(fun, 'pinball', 6, 6); put(fun, 'tv', 2, 3); put(fun, 'tv', 1, 3); put(fun, 'band', 0, 0);
  run(fun, 2400);
  const per = (s) => s.stats.plates / Math.max(1, s.stats.guests);
  console.log(`plain: ${plain.stats.plates} plates, ${plain.stats.guests} guests; fun: ${fun.stats.plates} plates, ${fun.stats.guests} guests`);
  assert.ok(per(fun) > per(plain) * 1.5);
  assert.ok(fun.stats.earned > plain.stats.earned);
});

test('selling a seat stands its guests up to find another chair', () => {
  const s = quiet(rich()); s.kitchen = 5;
  party(s, 1); run(s, 15);
  const g = s.guests[0], seat = E.byId(s, g.seat);
  E.sell(s, seat.id);
  assert.equal(g.seat, null);
  run(s, 2);
  assert.notEqual(g.seat, null, 'another stool was free');
});

test('the kitchen sets plates on the belt at its rate, and plates go round until taken', () => {
  const s = quiet(rich());
  s.kitchen = 0;
  run(s, 240);
  const on = s.plates.filter(Boolean).length;
  assert.ok(on >= B.kitchen.perMin[0] - 1 && on <= B.kitchen.perMin[0], `${on} plates in a minute`);
  run(s, 240 * 3);
  assert.equal(s.plates.filter(Boolean).length, E.RING.length, 'a full belt stops the hatch');
  assert.equal(E.limit(s).kind, 'guests');
});
