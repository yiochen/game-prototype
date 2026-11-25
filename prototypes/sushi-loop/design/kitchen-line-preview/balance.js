// Tuning for the kitchen line prototype. Rules live in engine.js.
// The kitchen is several rooms, each a 7x7 floor of its own with its own walls: the size the finished game will
// draw. Nothing crosses from one room to the next — a room has its own inlets, its own machines and its own
// doors, and feeds its own guests.
// Wall inlets are the only source of ingredients: every plate arrives from one with a single ingredient already
// on it. Equipment only ever does something to a plate that is already travelling — a Join merges the plates
// waiting at its two ends, a Splitter hands what reaches its middle out of its ends by turns, an add-on station
// spoons its ingredient on, a process station works on everything already there. A plate carrying a set no
// recipe allows comes out ruined.
// Nothing sorts. There are no filters, and a junction takes turns between its ways out without looking at the
// plate or at what lies down them, so where a dish ends up is the shape of the belt and nothing else.

const SIZE = 7, GAP = 1; // every room is 7x7, with one tile of wall between rooms

// Each room is a kitchen of its own and the dining room it feeds. `col`/`row` place it on the map; `in` and
// `out` are the wall connectors in its own 0..6 coordinates. Inlets and outlets are scattered over all four
// walls and may share one, but no inlet ever sits straight across the room from an outlet: a line always has to
// turn. The counts differ on purpose — three inlets and one door, three and two, four and one, three and three.
const rooms = [
  { name: 'A', title: 'Counter', color: '#1f8a8a', seats: 2, col: 0, row: 0,
    in: [[0, 1], [3, 0], [2, 6]], out: [[6, 4]] },
  { name: 'B', title: 'Booth', color: '#8a4fbf', seats: 6, col: 1, row: 0,
    in: [[0, 2], [5, 0], [3, 6]], out: [[1, 0], [6, 4]] },
  { name: 'C', title: 'Terrace', color: '#c2762a', seats: 2, col: 0, row: 1,
    in: [[1, 0], [4, 0], [0, 3], [5, 6]], out: [[6, 5]] },
  { name: 'D', title: 'Tatami', color: '#2f6fd0', seats: 3, col: 1, row: 1,
    in: [[0, 1], [2, 0], [6, 6]], out: [[5, 0], [3, 6], [0, 4]] },
];
const at = (r, lx, ly) => `${r.col * (SIZE + GAP) + lx},${r.row * (SIZE + GAP) + ly}`;
const exits = [];
rooms.forEach((r, i) => {
  for (const [x, y] of r.in) exits.push({ cell: at(r, x, y), kind: 'in' });
  for (const [x, y] of r.out) exits.push({ cell: at(r, x, y), room: i, kind: 'out' });
});
const cols = Math.max(...rooms.map((r) => r.col)) + 1, rws = Math.max(...rooms.map((r) => r.row)) + 1;

export const BALANCE = {
  tickMs: 300,
  speed: 6, // every piece of equipment takes the same time over one dish, and holds it while it works
  feed: 6, // ticks between deliveries from one inlet
  map: { size: SIZE, gap: GAP, cols, rows: rws },
  grid: { w: cols * (SIZE + GAP) - GAP, h: rws * (SIZE + GAP) - GAP },
  rooms,
  exits,
  queue: 5, // dishes a dining room holds before its connector backs up
  eat: 40, // ticks one seat takes over one dish
  starve: 30, // ticks with an empty room before it complains
  wantBonus: 1.6, // pay for the dish a room is asking for
  // What can sit on a plate. A plate holds a set of these, never an order, so salmon then rice and rice then
  // salmon make the same nigiri. `z` is only how they stack when drawn. `from` is the stage an inlet can
  // deliver it. An ingredient with an add-on station of its own needs no inlet.
  ingredients: {
    nori: { name: 'Nori', icon: '🟩', z: -1, shape: 'wrap', color: '#24402c', from: 3 },
    rice: { name: 'Rice', icon: '🍚', z: 0, shape: 'ball', color: '#fbf6ea', from: 0 },
    cuke: { name: 'Cucumber', icon: '🥒', z: 1, shape: 'stick', color: '#7fb069', from: 3 },
    fish: { name: 'Salmon', icon: '🐟', z: 2, shape: 'slab', color: '#f08a5d', from: 0 },
    egg: { name: 'Egg', icon: '🥚', z: 2, shape: 'slab', color: '#f2c14e', from: 1 },
    tuna: { name: 'Tuna', icon: '🟥', z: 2, shape: 'slab', color: '#c0392b', from: 5 },
    roe: { name: 'Roe', icon: '🟠', z: 3, shape: 'dots', color: '#e2601a', from: 99 },
    wasabi: { name: 'Wasabi', icon: '🟢', z: 4, shape: 'dab', color: '#5f8d2f', from: 99 },
  },
  // What can be done to an ingredient. A process marks everything on the plate when it runs, so searing before
  // the fish is on is not the same as searing after: order matters for processes and nothing else.
  processes: {
    sear: { name: 'Seared', icon: '🔥', tint: '#8a5a2b' },
    press: { name: 'Pressed', icon: '🧱', tint: '#6a6f8f' },
  },
  // Equipment. Nothing here is a source: a base ingredient comes off the wall and nowhere else.
  // `span: 3` is three tiles in a line. A Join takes a plate in at each end and hands the merged plate on from
  // its middle; a Splitter (`out: true`) is the same shape the other way round — belt runs into its middle and
  // it pushes plates out of its ends strictly one, then the other.
  // `size` is a straight block of that many tiles, and `block: 2` is a 2x2 block whose belt tile is a corner of
  // it: the only two faces left free are at right angles, so the belt has to turn through the machine.
  stations: {
    join: { name: 'Join', icon: '🔗', span: 3, price: 200, from: 0, does: 'Waits for a plate at each end, then merges the two into one' },
    bin: { name: 'Bin', icon: '🗑️', size: 1, price: 80, from: 0, does: 'Takes whatever reaches it off the belt, and ends the line' },
    split: { name: 'Splitter', icon: '🔀', span: 3, out: true, price: 260, from: 1, does: 'Takes plates in at its middle and sends them out of its two ends by turns, exactly half each' },
    sear: { name: 'Sear', icon: '🔥', applies: 'sear', size: 2, price: 900, from: 2, does: 'Sears everything already on the plate' },
    wasabi: { name: 'Wasabi', icon: '🟢', adds: 'wasabi', size: 1, price: 500, from: 3, does: 'Dabs wasabi onto whatever arrives' },
    roe: { name: 'Roe', icon: '🟠', adds: 'roe', size: 2, price: 1500, from: 4, does: 'Spoons roe onto whatever arrives' },
    press: { name: 'Press', icon: '🧱', applies: 'press', block: 2, price: 2200, from: 6, does: 'Presses everything already on the plate into a block' },
  },
  // A recipe is a set of ingredients and the processes each one must have had. Nothing may be on the plate that
  // the recipe does not name, and nothing it names may be missing. A dish of n ingredients off the wall takes
  // n inlets and n-1 Joins. Four of these are never asked for: they are there for a room with inlets to spare.
  // The two processed dishes are deliberately opposite. Seared nigiri is torched salmon on plain rice, so the
  // Sear has to run on the salmon line before the Join: a process marks everything on the plate, so searing the
  // whole nigiri seasons the rice as well and makes no dish at all. Pressed tuna is a block pressed rice and
  // all, so its Press goes after the Join. One machine, one rule, and where it stands is the whole difference.
  recipes: {
    nigiri: { name: 'Nigiri', has: { rice: [], fish: [] }, value: 12 },
    tamago: { name: 'Tamago', has: { rice: [], egg: [] }, value: 10 },
    seared: { name: 'Seared nigiri', has: { rice: [], fish: ['sear'] }, value: 26 },
    spicy: { name: 'Wasabi nigiri', has: { rice: [], fish: [], wasabi: [] }, value: 24 },
    jewel: { name: 'Roe tamago', has: { rice: [], egg: [], roe: [] }, value: 30 },
    deluxe: { name: 'Roe nigiri', has: { rice: [], fish: [], roe: [] }, value: 34 },
    maki: { name: 'Cucumber maki', has: { rice: [], cuke: [], nori: [] }, value: 28 },
    tekka: { name: 'Tekka maki', has: { rice: [], tuna: [], nori: [] }, value: 40 },
    oshi: { name: 'Pressed tuna', has: { rice: ['press'], tuna: ['press'] }, value: 48 },
    dragon: { name: 'Dragon roll', has: { rice: [], tuna: [], cuke: [], nori: [] }, value: 56 },
  },
  // The kitchen room A starts with: a rice line and a salmon line running into a Join, and the nigiri it merges
  // carried round to room A's one door. Nothing is straight through: the door is not across from any inlet.
  start: {
    coins: 0,
    joins: { '3,2': 'v' },
    lines: [
      ['0,1', '1,1', '2,1', '2,2', '2,3', '3,3'],
      ['3,0', '3,1'],
      ['3,2', '4,2', '5,2', '6,2', '6,3', '6,4'],
    ],
    inlets: { '0,1': 'rice', '3,0': 'fish' },
  },
  stages: [
    { need: 8, title: 'The counter opens', wants: { 0: 'any' } },
    { need: 18, title: 'The booth seats eight and wants tamago', open: 1, wants: { 1: 'tamago' } },
    { need: 32, title: 'The counter pays for seared nigiri', wants: { 0: 'seared' } },
    { need: 55, title: 'The terrace opens and wants cucumber maki', open: 2, wants: { 2: 'maki' } },
    { need: 85, title: 'The booth pays for roe', wants: { 1: 'jewel' } },
    { need: 125, title: 'The tatami room books in and wants nigiri', open: 3, wants: { 3: 'nigiri' } },
    { need: 180, title: 'The tatami room pays for pressed tuna', wants: { 3: 'oshi' } },
  ],
};
