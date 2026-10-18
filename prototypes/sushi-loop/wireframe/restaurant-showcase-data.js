// Native catalog assembly only: positions use the library's ground-root cells.
// The renderer supplies floor tiling, depth sorting, atlas playback and motion.
const place = (id, object, x, y, direction = 'S', clip = 'static', extra = {}) =>
  ({ id, object, x, y, direction, clip, ...extra });

const belts = [
  place('turn-north-west', 'belt-corner-s-e', 3, 3, 'S', 'running'),
  ...Array.from({ length: 5 }, (_, i) => place(`north-belt-${i}`, 'belt-straight-e', 4 + i, 3, 'S', 'running')),
  place('turn-north-east', 'belt-corner-w-s', 9, 3, 'S', 'running'),
  ...Array.from({ length: 2 }, (_, i) => place(`east-belt-${i}`, 'belt-straight-s', 9, 4 + i, 'S', 'running')),
  place('turn-south-east', 'belt-corner-n-w', 9, 6, 'S', 'running'),
  ...Array.from({ length: 5 }, (_, i) => place(`south-belt-${i}`, 'belt-straight-w', 8 - i, 6, 'S', 'running')),
  place('turn-south-west', 'belt-corner-e-n', 3, 6, 'S', 'running'),
  ...Array.from({ length: 2 }, (_, i) => place(`west-belt-${i}`, 'belt-straight-n', 3, 5 - i, 'S', 'running')),
];

// Each arc has the same 48 segments as its native .5-cell centerline. Points
// are placement coordinates; the dish's own [.5,.5] root is added by the renderer.
const arc = (cx, cy, start) => Array.from({ length: 48 }, (_, i) => {
  const angle = start + (i + 1) / 48 * Math.PI / 2;
  return [cx + .5 * Math.cos(angle), cy + .5 * Math.sin(angle)];
});
const circulation = [
  [3.5, 3], [8.5, 3], ...arc(8.5, 3.5, -Math.PI / 2),
  [9, 5.5], ...arc(8.5, 5.5, 0),
  [3.5, 6], ...arc(3.5, 5.5, Math.PI / 2),
  [3, 3.5], ...arc(3.5, 3.5, Math.PI),
];
// Make the shared seam bit-for-bit identical, rather than relying on sin(2π).
circulation[circulation.length - 1] = [...circulation[0]];
const plates = ['dish-salmon', 'dish-cucumber', 'dish-eel', 'dish-salmon', 'dish-cucumber', 'dish-eel']
  .map((object, i) => place(`circulating-plate-${i}`, object, 3.5, 3, 'S', 'static', {
    // Exact registered deck height: .64 world units ×128 logical pixels.
    offset: [0, -81.92], renderPass: 'foreground',
    motion: { path: circulation, duration: 48, loop: true, phase: i * 8 },
  }));

const walls = [
  // Ports: left corner E/S, back run W/E, right corner W/S. Both side runs
  // continue N/S and terminate with a north-facing attachment at their cap.
  place('back-left-wall-corner', 'wall-inner-corner', 0, 0, 'N'),
  ...Array.from({ length: 10 }, (_, i) => place(`back-wall-${i}`, 'wall-middle', 1 + i, 0)),
  place('back-right-wall-corner', 'wall-outer-corner', 11, 0),
  ...[0, 11].flatMap((x, side) => [
    ...Array.from({ length: 3 }, (_, i) => place(`side-wall-${side}-${i}`, 'wall-middle', x, 1 + i, 'W')),
    place(`side-wall-${side}-finished-end`, 'wall-end', x, 4, 'W'),
  ]),
];

const seats = [
  // Stools precede their separate occupants at equal ground depth. Wood-seat
  // contact is already baked into the customer; blue adds exactly3.84px.
  place('rosa-stool', 'stool-wood', 4.7, 2),
  place('rosa-dining', 'customer-rosa', 4.7, 2, 'S', 'eat', { timeOffset: .25 }),
  place('ellis-stool', 'stool-blue', 7.2, 2),
  place('ellis-waiting', 'customer-ellis', 7.2, 2, 'S', 'seated-wait', { offset: [0, -3.84], timeOffset: .6 }),
  place('north-open-stool', 'stool-wood', 6, 2),
  place('samir-stool', 'stool-blue', 10, 5.2, 'W'),
  place('samir-dining', 'customer-samir', 10, 5.2, 'W', 'eat', { offset: [0, -3.84], timeOffset: .8 }),
  place('west-open-stool', 'stool-wood', 2, 4.7, 'E'),
  place('south-open-stool-wood', 'stool-wood', 4.3, 7, 'N'),
  place('south-open-stool-blue', 'stool-blue', 7.6, 7, 'N'),
];

export const restaurantShowcase = {
  id: 'restaurant',
  title: 'The restaurant, assembled',
  description: 'A warm cutaway dining room with a complete conveyor island, working chefs, seated guests and dense garden borders around a broad entrance.',
  gridSize: [12, 12],
  floorId: 'floor-cream',
  background: '#e7dfcf',
  duration: 48,
  placements: [
    ...walls,
    place('back-lantern', 'lantern-gold', 2.4, 1.1, 'S', 'ambient', { timeOffset: .3 }),
    place('back-barrel', 'barrel-wood', 8.7, 1.1),
    // Multi-cell native assemblies pack off-grid pots, rocks, foliage and small
    // accents into the margins while leaving the conveyor and dining aisle open.
    place('west-border-garden', 'restaurant-border-garden-a', .05, .65, 'S', 'ambient'),
    place('east-border-garden', 'restaurant-border-garden-b', 9.95, .8, 'S', 'ambient', { timeOffset: .35 }),
    place('front-west-garden', 'restaurant-corner-garden-a', .05, 7.95, 'S', 'ambient', { timeOffset: .65 }),
    place('front-east-garden', 'restaurant-corner-garden-b', 8.95, 7.95, 'S', 'ambient', { timeOffset: .15 }),
    ...belts,
    // The recipe boards use the approved independent shared-cell registration.
    place('lena-board', 'chef-blackboard', 4.4, 5, 'S', 'selected', { offset: [-42, 12] }),
    place('lena-working', 'chef-lena', 4.4, 5, 'S', 'work'),
    place('noor-board', 'chef-blackboard', 7.7, 5, 'S', 'cucumber-selected', { offset: [-42, 12], timeOffset: .4 }),
    place('noor-working', 'chef-noor', 7.7, 5, 'S', 'work', { timeOffset: .5 }),
    place('omar-preparing', 'chef-omar', 6.1, 4, 'N', 'hold', { timeOffset: .7 }),
    ...seats,
    ...plates,
    place('entrance-lantern', 'lantern-gold', 3.05, 9.55, 'S', 'ambient', { timeOffset: .8 }),
    place('blank-welcome-sign', 'sign-blank', 8.05, 9.5),
    // A closed8.96-cell path /16s matches the native walking gait's .56cell/s.
    // It stays in the open front aisle, away from stools, gateposts and belts.
    place('june-in-aisle', 'customer-june', 4.05, 7.9, 'E', 'walk', {
      motion: {
        path: [[4.05, 7.9], [8.03, 7.9], [8.03, 8.4], [4.05, 8.4], [4.05, 7.9]],
        duration: 16, loop: true, phase: 2, faceTravel: true,
      },
    }),
    // The four-cell entrance is centered on the aisle. Its own front row keeps
    // the native pillars and two-cell opening clear of the walking loop.
    place('restaurant-entrance', 'entry-finished', 4, 11),
  ],
  highlights: [
    {
      title: 'A connected conveyor loop',
      description: 'Four directed native turns connect the straight runs. Separate plates follow the modeled quarter-circle centerline above the moving deck.',
      objectIds: ['belt-corner-s-e', 'belt-corner-w-s', 'belt-corner-n-w', 'belt-corner-e-n', 'belt-straight-e'],
    },
    {
      title: 'Chefs and dishes at one scale',
      description: 'Two working chefs, a chef holding a finished dish and independent recipe boards share the island without resizing their sprites.',
      objectIds: ['chef-lena', 'chef-noor', 'chef-omar', 'chef-blackboard', 'dish-salmon', 'dish-cucumber', 'dish-eel'],
    },
    {
      title: 'Seating and an open aisle',
      description: 'Customers sit on separate registered stools. Blue cushions use their recorded support-height adjustment; another guest walks the clear front lane.',
      objectIds: ['stool-wood', 'stool-blue', 'customer-rosa', 'customer-ellis', 'customer-samir', 'customer-june'],
    },
    {
      title: 'A finished cutaway room',
      description: 'Matching wall profiles wrap the back and sides, with finished ends, a four-tile entrance, a blank sign, storage and lanterns framing its central opening.',
      objectIds: ['wall-middle', 'wall-inner-corner', 'wall-outer-corner', 'wall-end', 'entry-finished', 'sign-blank', 'barrel-wood', 'lantern-gold'],
    },
    {
      title: 'Dense garden borders',
      description: 'Two narrow border gardens and two broad corner gardens combine off-grid foliage, stones, pots and small accents into four reusable native assemblies.',
      objectIds: ['restaurant-border-garden-a', 'restaurant-border-garden-b', 'restaurant-corner-garden-a', 'restaurant-corner-garden-b'],
    },
  ],
  note: 'Animated scene composition for asset review. Dish circulation is staged independently of slat timing; the aisle walk is a presentation path. This is not occupancy, cooking or service simulation. All sprites retain their native scale and ground registration; final art approval remains pending.',
};
