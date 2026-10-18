// A seven-column portrait composition at the catalog's native world scale.
// The authored camera clips only the outer border art, not the playfield.
const place = (id, object, x, y, direction = 'S', clip = 'static', extra = {}) =>
  ({ id, object, x, y, direction, clip, ...extra });

const belts = [
  place('turn-north-west', 'belt-corner-s-e', 3, 3, 'S', 'running'),
  place('north-belt-0', 'belt-straight-e', 4, 3, 'S', 'running'),
  place('turn-north-east', 'belt-corner-w-s', 5, 3, 'S', 'running'),
  ...Array.from({ length: 5 }, (_, i) => place(`east-belt-${i}`, 'belt-straight-s', 5, 4 + i, 'S', 'running')),
  place('turn-south-east', 'belt-corner-n-w', 5, 9, 'S', 'running'),
  place('south-belt-0', 'belt-straight-w', 4, 9, 'S', 'running'),
  place('turn-south-west', 'belt-corner-e-n', 3, 9, 'S', 'running'),
  ...Array.from({ length: 5 }, (_, i) => place(`west-belt-${i}`, 'belt-straight-n', 3, 8 - i, 'S', 'running')),
];

// Native .5-cell quarter circles retain the modeled curve at every corner.
const arc = (cx, cy, start) => Array.from({ length: 48 }, (_, i) => {
  const angle = start + (i + 1) / 48 * Math.PI / 2;
  return [cx + .5 * Math.cos(angle), cy + .5 * Math.sin(angle)];
});
const circulation = [
  [3.5, 3], [4.5, 3], ...arc(4.5, 3.5, -Math.PI / 2),
  [5, 8.5], ...arc(4.5, 8.5, 0),
  [3.5, 9], ...arc(3.5, 8.5, Math.PI / 2),
  [3, 3.5], ...arc(3.5, 3.5, Math.PI),
];
circulation[circulation.length - 1] = [...circulation[0]];
const plates = ['dish-salmon', 'dish-cucumber', 'dish-eel', 'dish-salmon', 'dish-cucumber', 'dish-eel']
  .map((object, i) => place(`circulating-plate-${i}`, object, 3.5, 3, 'S', 'static', {
    offset: [0, -81.92], renderPass: 'foreground',
    motion: { path: circulation, duration: 48, loop: true, phase: i * 8 },
  }));

// Both vertical wall profiles continue beyond the camera. Gardens overlap their
// outer sides to form continuous framing rather than isolated decoration islands.
const walls = [-.25, 6.25].flatMap((x, side) => Array.from({ length: 16 }, (_, i) =>
  place(`${side ? 'east' : 'west'}-room-wall-${i}`, 'wall-middle', x, i - 1, side ? 'W' : 'E')));
const gardens = [0, 1, 2].flatMap(i => [
  place(`west-border-garden-${i}`, 'restaurant-border-garden-a', -1.15, .2 + i * 4, 'S', 'ambient', { timeOffset: i * .2 }),
  place(`east-border-garden-${i}`, 'restaurant-border-garden-b', 5.95, .4 + i * 4, 'S', 'ambient', { timeOffset: .35 + i * .2 }),
]);
const seats = [
  place('rosa-stool', 'stool-wood', 4, 4.5, 'W'),
  place('rosa-dining', 'customer-rosa', 4, 4.5, 'W', 'eat', { timeOffset: .25 }),
  place('samir-stool', 'stool-blue', 4, 7, 'W'),
  place('samir-dining', 'customer-samir', 4, 7, 'W', 'eat', { offset: [0, -3.84], timeOffset: .8 }),
  place('ellis-stool', 'stool-blue', 3.7, 10.4, 'N'),
  place('ellis-waiting', 'customer-ellis', 3.7, 10.4, 'N', 'seated-wait', { offset: [0, -3.84], timeOffset: .6 }),
];

export const restaurantShowcase = {
  id: 'restaurant',
  title: 'The restaurant, assembled',
  description: 'A close portrait view: the entrance anchors the back of the room, chefs work along a tall conveyor, and guests sit within its compact dining counter.',
  gridSize: [7, 13],
  cameraBounds: [0, 0, 7, 13],
  floorId: 'floor-cream',
  background: '#e7dfcf',
  duration: 48,
  placements: [
    ...walls,
    ...gardens,
    place('restaurant-entrance', 'entry-finished', 1.5, 1.8),
    place('back-lantern', 'lantern-gold', .9, 1.7, 'S', 'ambient', { timeOffset: .3 }),
    place('entrance-lantern', 'lantern-gold', 5.5, 1.7, 'S', 'ambient', { timeOffset: .8 }),
    ...belts,
    place('lena-board', 'chef-blackboard', 1.8, 4.5, 'E', 'selected', { offset: [42, 12] }),
    place('lena-working', 'chef-lena', 1.8, 4.5, 'E', 'work'),
    place('noor-board', 'chef-blackboard', 1.8, 7.1, 'E', 'cucumber-selected', { offset: [42, 12], timeOffset: .4 }),
    place('noor-working', 'chef-noor', 1.8, 7.1, 'E', 'work', { timeOffset: .5 }),
    ...seats,
    ...plates,
    // Exactly8.96cells /16s matches the native .56cell/s walking gait. The lane
    // stays west of the conveyor and outside the separate front dining stool.
    place('june-in-aisle', 'customer-june', .95, 8.8, 'E', 'walk', {
      motion: {
        path: [[.95, 8.8], [2.15, 8.8], [2.15, 12.08], [.95, 12.08], [.95, 8.8]],
        duration: 16, loop: true, phase: 2, faceTravel: true,
      },
    }),
  ],
  highlights: [
    {
      title: 'A tall, connected conveyor',
      description: 'Sixteen native modules form a narrow closed counter. Its long working edge and bottom turn establish the portrait composition; independent dishes follow the actual quarter-circle centerline.',
      objectIds: ['belt-corner-s-e', 'belt-corner-w-s', 'belt-corner-n-w', 'belt-corner-e-n', 'belt-straight-n', 'belt-straight-s'],
    },
    {
      title: 'Chefs and dishes at one scale',
      description: 'Two chefs face the working edge while their separate recipe boards and the circulating dishes retain the catalog’s registered scale.',
      objectIds: ['chef-lena', 'chef-noor', 'chef-blackboard', 'dish-salmon', 'dish-cucumber', 'dish-eel'],
    },
    {
      title: 'Guests around the counter',
      description: 'Two guests dine along the inside edge and another occupies the front stool. June walks the open left aisle at her native gait speed.',
      objectIds: ['stool-wood', 'stool-blue', 'customer-rosa', 'customer-samir', 'customer-ellis', 'customer-june'],
    },
    {
      title: 'An entrance and continuous garden edges',
      description: 'The four-tile entrance sits at the back. Two garden variants repeat along the outer walls; the seven-column camera intentionally cuts their outer overhang to frame the room.',
      objectIds: ['entry-finished', 'wall-middle', 'lantern-gold', 'restaurant-border-garden-a', 'restaurant-border-garden-b'],
    },
  ],
  note: 'A seven-column scene composition using native sprite scale. The authored camera crops outer border art; individual object pages retain full sprite canvases. Dish travel is staged independently of slat timing, and the aisle walk is a presentation path. Scene-asset approval remains pending.',
};
