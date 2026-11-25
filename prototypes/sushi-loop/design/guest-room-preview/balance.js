// Tuning for the guest room prototype. Rules live in engine.js.
// The guest room is the 7x7 dining room behind a kitchen's door. The kitchen hatch sets plates on a fixed belt
// that runs out of the kitchen wall and back, like a conveyor-sushi counter. Guests walk on the floor only:
// never over the belt or another piece, so every seat and game must be reachable from the street door.
// Nothing here is a puzzle: every piece is a plus,
// and the choices are which pluses, and how long to keep guests in the room.
// - Appeal brings guests in. Every piece has charm, multiplied by how well the room keeps to one style.
// - Capacity is how many people may be inside at all; past it they queue at the door and give up.
// - Seats are where guests eat. A party takes a whole seat, so couples and groups need seats their size.
//   Every guest takes one whole tile, as in the game, so a seat is as many tiles as it has chairs: a booth for
//   four is 2x2 round a table, and only has to touch the belt somewhere for the table to reach the plates.
// - Appetite is how many plates a guest eats. Pinball, the sports TV and the band make guests hungry again,
//   so each guest is worth more — but holds a place in the room for longer.

export const BALANCE = {
  tickMs: 250, // 4 ticks a second
  size: 7,
  // The belt is a fixed loop, clockwise. Seats have to stand beside it to reach the plates.
  // The loop stands against the west wall, so floor runs round its other three sides: a row of seats along
  // the top and the bottom with an aisle behind each, joined by a two-tile corridor down the east side. The
  // three tiles inside the loop can only be reached over the belt, so no guest can get to them.
  ring: [[0, 2], [1, 2], [2, 2], [3, 2], [4, 2], [4, 3], [4, 4], [3, 4], [2, 4], [1, 4], [0, 4], [0, 3]],
  hatch: [-1, 3], // the kitchen's hatch, in the west wall; plates come onto the belt tile beside it
  door: [3, 6], // the street door, on the south wall
  beltEvery: 2, // ticks for a plate to move one tile
  plate: 10, // coins a plate pays before seat bonuses
  dishes: ['🍣', '🍙', '🍤', '🥢'],
  walk: 0.3, // tiles a guest walks in one tick
  eat: 12, // ticks over one plate
  appetite: [2, 3], // plates a guest arrives wanting, lowest and highest
  maxExtras: 3, // the most a guest's appetite can be topped up over one visit, from every source together
  hungry: 160, // ticks a seated guest waits for a plate before walking out
  standWait: 40, // ticks a guest back from playing waits for a free chair before going home
  queueMax: 5, // parties that will stand at the door; any more walk on by
  queuePatience: 60, // ticks a party waits at the door
  // Traffic: parties a minute = base + charm-based Appeal x perAppeal, and the band draws more while it plays.
  traffic: { base: 2, perAppeal: 0.15 },
  parties: [{ size: 1, w: 4 }, { size: 2, w: 4 }, { size: 4, w: 2 }],
  // Coherence: the share of pieces in the room's main style. Appeal is multiplied by low + span x coherence,
  // so a room all of one style gets x1.4 and a muddle of three styles about x0.87.
  coherence: { low: 0.6, span: 0.8 },
  styles: {
    zen: { name: 'Zen wood', base: '#b9874f', dark: '#7a5230', accent: '#efdcb4' },
    lantern: { name: 'Lantern night', base: '#c8443a', dark: '#7f2620', accent: '#f2c14e' },
    ocean: { name: 'Ocean', base: '#2f7fb0', dark: '#1d4f70', accent: '#a7dcea' },
  },
  // Upgrading a piece multiplies its charm, and a seat's plates pay a tip on top.
  tiers: { charm: [1, 1.6, 2.4], tip: [1, 1.15, 1.3], cost: [0, 0.8, 1.6] },
  // `chairs` makes a seat, which must touch the belt. `spots` is an activity guests leave their seat for.
  // `onBelt` pieces stand over a belt tile, and plates run underneath them.
  items: {
    stool: { name: 'Stool', icon: '🪑', w: 1, h: 1, chairs: 1, price: 60, charm: 2, does: 'One guest, eating alone' },
    cage: { name: 'Bird cage', icon: '🪺', w: 1, h: 1, chairs: 1, price: 900, charm: 14, does: 'A hanging cage for one. Tourists love it' },
    booth: { name: 'Booth', icon: '🛋️', w: 2, h: 2, chairs: 4, price: 400, charm: 5, does: 'Four round a table: the only place a group can sit' },
    glass: { name: 'Glass room', icon: '🫧', w: 2, h: 1, chairs: 2, pay: 1.5, price: 1500, charm: 8, does: 'Private room for two, side by side. Plates pay half again' },
    pinball: { name: 'Pinball', icon: '🕹️', w: 1, h: 1, spots: 1, play: 24, price: 700, charm: 4, does: 'A full guest plays a round, then comes back hungry' },
    tv: { name: 'Sports TV', icon: '📺', w: 1, h: 1, every: 60, price: 500, charm: 3, does: 'Every goal, the whole room orders another plate' },
    band: { name: 'Band', icon: '🎸', w: 2, h: 2, max: 1, on: 40, off: 80, boost: 1.6, price: 2500, charm: 10, does: 'Each set draws a crowd in, and makes everyone seated hungry again' },
    arch: { name: 'Arch', icon: '⛩️', w: 1, h: 1, onBelt: true, price: 300, charm: 6, does: 'Stands over the belt; plates run underneath',
      names: { zen: 'Torii arch', lantern: 'Lantern arch', ocean: 'Wave tunnel' } },
  },
  // Each top-up to a guest's appetite. Pinball gives two plates' hunger the first time and one the second.
  refill: [2, 1],
  // Room-wide upgrades, by level. The kitchen stands in for the kitchen line: plates a minute through the hatch.
  capacity: { size: [6, 10, 14, 20, 28, 40], price: [0, 250, 600, 1200, 2500, 5000] },
  kitchen: { perMin: [12, 20, 30, 45, 65, 90], price: [0, 300, 700, 1500, 3000, 6000] },
  start: {
    coins: 400,
    items: [
      { kind: 'stool', x: 1, y: 1, style: 'zen' }, { kind: 'stool', x: 2, y: 1, style: 'zen' },
      { kind: 'stool', x: 3, y: 1, style: 'zen' }, { kind: 'stool', x: 4, y: 1, style: 'zen' },
    ],
  },
};
