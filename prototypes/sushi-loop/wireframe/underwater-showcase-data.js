// A narrow portrait channel, with the outer bank art intentionally beyond the
// authored camera. All native world roots, atlas scale and facing data remain intact.
const item = (id, object, x, y, direction = 'S', clip = 'static', extra = {}) => ({
  id, object, x, y, direction, clip, ...extra,
});
const patrol = (path, duration, phase = 0) => ({ path, duration, phase, loop: true, faceTravel: true });
const submarinePatrol = patrol([
  [3, 10], [3, 8], [3.4, 8], [3.4, 10], [3, 10],
], 48);
// The eel needs room for its long, asymmetric tail in the East/West captures.
// Root centers2.8..3.1 keep every facing clear of the inner cliff atx1.5.
const eelPatrol = patrol([
  [2.3, 6.1], [2.3, 3.8], [2.6, 3.8], [2.6, 6.1], [2.3, 6.1],
], 24, 6);
const fishPatrol = patrol([[4.4, 1.6], [4.4, 2.8], [4.4, 1.6]], 24, 4);

// Canonical section orientation stays constant along each complete bank. Their
// first and last ports are outside the camera; every visible neighbor is joined.
const banks = [.5, 5.5].flatMap((x, side) => Array.from({ length: 17 }, (_, i) =>
  item(`${side ? 'east' : 'west'}-bank-${i}`, [3, 7, 11].includes(i) ? 'rock-wall-edge' : 'rock-wall-middle', x, i - 1, side ? 'W' : 'E')));
const gardens = [0, 1, 2, 3].flatMap(i => [
  item(`west-reef-garden-${i}`, 'underwater-reef-garden-a', -.5, .2 + i * 4, 'S', 'ambient', { timeOffset: i * .2 }),
  item(`east-reef-garden-${i}`, 'underwater-reef-garden-b', 5.5, .4 + i * 4, 'S', 'ambient', { timeOffset: .35 + i * .2 }),
]);

export const underwaterShowcase = {
  id: 'underwater',
  title: 'The turquoise passage',
  description: 'A yellow submarine moves through a narrow turquoise channel, framed by continuous cobalt cliffs, dense reef growth and a few readable pockets of life.',
  gridSize: [7, 14],
  cameraBounds: [0, 0, 7, 14],
  floorId: 'floor-underwater',
  background: 'linear-gradient(180deg, #07425c 0%, #117f91 44%, #0a6179 100%)',
  duration: 48,
  placements: [
    item('light-through-central-water', 'decor-light-shafts', 2.3, 5.2, 'S', 'ambient', { renderPass: 'background', timeOffset: .4 }),
    item('light-through-south-water', 'decor-light-shafts', 2.5, 11.1, 'S', 'ambient', { renderPass: 'background', timeOffset: .8 }),
    ...banks,
    ...gardens,
    // A few bank-bound accents give the channel a readable material contrast.
    item('west-bank-boulder', 'boulder-underwater', 1.05, 10.6, 'N'),
    item('east-bank-column', 'column-broken', 5.2, 2.7, 'W', 'static'),
    item('reef-windup-hazard', 'attack-reef-fragments', 5.05, 6.8, 'S', 'windup'),
    item('west-bank-starfish', 'decor-starfish', .7, 12.6, 'S'),
    item('west-salvage', 'salvage-metal', 1.25, 8.2, 'S', 'shimmer'),
    item('east-salvage', 'salvage-metal', 4.6, 11.8, 'W', 'c-shimmer', { timeOffset: .7 }),
    item('central-north-current', 'route-current', 2.5, 7.1, 'N', 'flow', { renderPass: 'background' }),
    item('lower-north-current', 'route-current', 2.5, 12, 'N', 'flow', { renderPass: 'background', timeOffset: .5 }),
    item('submarine-wake', 'boost-trail', 3, 10, 'N', 'boost', {
      renderPass: 'background', motion: submarinePatrol,
    }),
    item('expedition-submarine', 'submarine-yellow', 3, 10, 'N', 'upgraded-travel', {
      motion: submarinePatrol,
    }),
    item('eel-following-water', 'following-strip', 2.3, 6.1, 'N', 'flow', {
      renderPass: 'background', motion: eelPatrol,
    }),
    item('east-pocket-eel', 'creature-eel', 2.3, 6.1, 'N', 'swim', {
      motion: eelPatrol,
    }),
    item('west-pocket-fish', 'creature-fish', 4.4, 1.6, 'S', 'swim', {
      motion: fishPatrol, timeOffset: .25,
    }),
    item('west-water-bubbles', 'decor-bubbles', 1.75, 7.1, 'S', 'rise', { timeOffset: .6 }),
    item('east-water-bubbles', 'decor-bubbles', 4.4, 4.4, 'S', 'rise', { timeOffset: .2 }),
  ],
  highlights: [
    {
      title: 'A readable central route',
      description: 'The yellow craft stays large and low in the portrait frame. Its small all-facing route keeps the wake attached while currents mark the open channel.',
      objectIds: ['submarine-yellow', 'boost-trail', 'route-current'],
    },
    {
      title: 'Continuous native cliff banks',
      description: 'Each visible cliff section joins the next through the same authored cross-section. The connected runs continue beyond the top and bottom of the camera.',
      objectIds: ['rock-wall-middle', 'rock-wall-edge'],
    },
    {
      title: 'Life and accents in the side pockets',
      description: 'The fish and eel occupy separate upper pockets. A bank-bound reef windup, stone column and salvage add a few distinct accents without filling the craft’s route.',
      objectIds: ['creature-fish', 'creature-eel', 'attack-reef-fragments', 'column-broken', 'salvage-metal', 'decor-bubbles'],
    },
    {
      title: 'Dense borders at one world scale',
      description: 'Two reef-garden variants form continuous outer masses. Their off-camera overhang frames the seven-column channel; their full footprints remain available in the object library.',
      objectIds: ['underwater-reef-garden-a', 'underwater-reef-garden-b', 'boulder-underwater', 'decor-starfish'],
    },
  ],
  note: 'A seven-column,48-second scene study at native tile scale. The authored camera clips outer border art while keeping the central waterway in view. Patrols and the reef windup stage the art composition; individual object pages retain the complete per-asset review.',
};
