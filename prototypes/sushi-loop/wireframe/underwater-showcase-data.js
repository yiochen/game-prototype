// Tile origins stay independent of native sprite bounds and capture scale.
// S preserves each environment module's authored orientation. Matching profile
// runs below keep their section handedness through every corner and end.
const item = (id, object, x, y, direction = 'S', clip = 'static', extra = {}) => ({
  id, object, x, y, direction, clip, ...extra,
});

const patrol = (path, duration, phase = 0) => ({
  path, duration, phase, loop: true, faceTravel: true,
});

const submarinePatrol = patrol([
  [6, 8.2], [6, 2.4], [7.8, 2.4], [7.8, 8.2], [6, 8.2],
], 48);

const eelPatrol = patrol([
  [9.6, 8.8], [9.6, 7.1], [10.7, 7.1], [10.7, 8.8], [9.6, 8.8],
], 24, 6);

const fishPatrol = patrol([
  [4.1, 7.4], [4.6, 7.4], [4.6, 8.8], [4.1, 8.8], [4.1, 7.4],
], 24, 4);

export const underwaterShowcase = {
  id: 'underwater',
  title: 'The turquoise passage',
  description: 'A yellow submarine explores a clear-water canyon between cobalt cliffs, densely layered reef gardens and the ribs of an old wreck.',
  gridSize: [14, 12],
  floorId: 'floor-underwater',
  background: 'linear-gradient(180deg, #07425c 0%, #117f91 44%, #0a6179 100%)',
  duration: 48,
  placements: [
    // Quiet distance: silhouettes sit behind the route and its inhabitants.
    item('distant-west-spires', 'decor-background-rock', 2.1, 0.1, 'S', 'static', { renderPass: 'background' }),
    item('distant-east-spires', 'decor-background-rock', 9.8, 0.2, 'N', 'static', { renderPass: 'background' }),
    item('distant-wreck-silhouette', 'decor-background-wreck', 3.3, 1.1, 'S', 'static', { renderPass: 'background' }),
    item('distant-upper-school', 'decor-background-fish', 4.4, 1.5, 'S', 'swim', { renderPass: 'background', timeOffset: 0.3 }),
    item('distant-portal-school', 'decor-background-fish', 8.6, 1.3, 'N', 'swim', { renderPass: 'background', timeOffset: 0.7 }),
    item('light-through-west-water', 'decor-light-shafts', 4.5, 3.2, 'S', 'ambient', { renderPass: 'background' }),
    item('light-through-central-water', 'decor-light-shafts', 7.1, 5.2, 'S', 'ambient', { renderPass: 'background', timeOffset: 0.4 }),
    item('light-through-south-water', 'decor-light-shafts', 5.7, 10.5, 'S', 'ambient', { renderPass: 'background', timeOffset: 0.8 }),

    // Left canyon: west-facing profile normal, running north from its bend.
    item('west-wall-front-edge', 'rock-wall-edge', 0, 10),
    item('west-wall-bottom-turn', 'rock-wall-corner', 1, 10),
    item('west-wall-lower-seam', 'rock-wall-middle', 1, 9, 'E'),
    item('west-wall-lower-edge', 'rock-wall-edge', 1, 8, 'E'),
    item('west-wall-mid-low', 'rock-wall-middle', 1, 7, 'E'),
    item('west-wall-mid-high', 'rock-wall-middle', 1, 6, 'E'),
    item('west-wall-wreck-edge', 'rock-wall-edge', 1, 5, 'E'),
    item('west-wall-upper-seam', 'rock-wall-middle', 1, 4, 'E'),
    item('west-wall-upper-edge', 'rock-wall-edge', 1, 3, 'E'),
    item('west-wall-finished-tip', 'rock-wall-end', 1, 2, 'E'),

    // Right canyon: the reversed whole run preserves the asymmetric section.
    item('east-wall-distant-edge', 'rock-wall-edge', 13, 1, 'N'),
    item('east-wall-upper-turn', 'rock-wall-corner', 12, 1, 'N'),
    item('east-wall-upper-seam', 'rock-wall-middle', 12, 2, 'W'),
    item('east-wall-upper-edge', 'rock-wall-edge', 12, 3, 'W'),
    item('east-wall-reef-seam', 'rock-wall-middle', 12, 4, 'W'),
    item('east-wall-mid-seam', 'rock-wall-middle', 12, 5, 'W'),
    item('east-wall-patrol-edge', 'rock-wall-edge', 12, 6, 'W'),
    item('east-wall-lower-seam', 'rock-wall-middle', 12, 7, 'W'),
    item('east-wall-lower-edge', 'rock-wall-middle', 12, 8, 'W'),
    item('east-wall-finished-tip', 'rock-wall-end', 12, 9, 'W'),

    // A continuous wreck rib emerges from the left rock face, then turns north.
    item('wreck-buried-rib', 'wreck-middle', 2, 5),
    item('wreck-rib-turn', 'wreck-corner', 3, 5),
    item('wreck-rising-rib', 'wreck-edge', 3, 4, 'E'),
    item('wreck-finished-rib', 'wreck-end', 3, 3, 'E'),
    item('wreck-broken-column', 'column-broken', 2.2, 3.2, 'S', 'idle'),
    item('wreck-scattered-masonry', 'decor-ruin-fragment', 3.9, 4.6, 'E', 'idle'),
    item('wreck-kelp-growth', 'decor-kelp', 2.1, 5.3, 'S', 'sway', { timeOffset: 0.4 }),

    // Low shelf at the near-left shoreline leaves the main waterway open.
    item('near-shelf-west-run', 'rock-shelf-middle', 2, 10),
    item('near-shelf-turn', 'rock-shelf-corner', 3, 10),
    item('near-shelf-upright', 'rock-shelf-edge', 3, 9, 'E'),
    item('near-shelf-finished-tip', 'rock-shelf-end', 3, 8, 'E'),
    item('near-shelf-column', 'column-broken', 4.1, 10.3, 'W', 'static'),
    item('near-shelf-masonry', 'decor-ruin-fragment', 3.8, 11, 'S', 'static'),

    // One matching-profile reef, with the warm coral grouped around its lip.
    item('reef-west-lip', 'reef-middle', 9, 5),
    item('reef-center-lip', 'reef-edge', 10, 5),
    item('reef-north-turn', 'reef-corner', 11, 5),
    item('reef-upright', 'reef-middle', 11, 4, 'E'),
    item('reef-finished-tip', 'reef-end', 11, 3, 'E'),
    item('reef-mouth-coral', 'decor-midground-coral', 8.8, 4.9, 'S', 'ambient'),
    item('reef-inner-coral', 'decor-midground-coral', 10.3, 3.7, 'W', 'ambient', { timeOffset: 0.5 }),
    item('reef-tall-kelp', 'decor-kelp', 10.3, 2.8, 'S', 'sway', { timeOffset: 0.8 }),
    item('reef-small-boulder', 'boulder-underwater', 10.5, 5.8, 'N'),

    // Dense native composites break away from tile-center repetition. Each
    // garden occupies a bank or corner outside the unchanged patrol routes.
    item('west-reef-garden', 'underwater-reef-garden-a', 0, 2.4, 'S', 'ambient'),
    item('east-reef-garden', 'underwater-reef-garden-b', 12, 4.15, 'S', 'ambient', { timeOffset: .35 }),
    item('near-west-coral-garden', 'underwater-coral-garden-a', .05, 8.95, 'S', 'ambient', { timeOffset: .65 }),
    item('far-east-coral-garden', 'underwater-coral-garden-b', 10.95, .05, 'S', 'ambient', { timeOffset: .15 }),
    item('west-bank-coral-mid', 'decor-midground-coral', 0.1, 6.5, 'E', 'ambient', { timeOffset: 0.6 }),
    item('west-bank-kelp-low', 'decor-kelp', 1.9, 8, 'S', 'sway', { timeOffset: 0.2 }),
    item('east-bank-kelp-low', 'decor-kelp', 11.6, 9.9, 'W', 'sway', { timeOffset: 0.7 }),

    // Portal, currents and salvage make the central negative space a route.
    item('north-water-portal', 'portal-rim', 6.4, 0.8, 'S', 'idle'),
    item('portal-left-flank', 'safe-passage', 5.1, 1.1, 'S', 'ambient'),
    item('portal-right-flank', 'safe-passage', 8.1, 1.1, 'N', 'ambient'),
    item('central-north-current', 'route-current', 6, 5.4, 'N', 'flow', { renderPass: 'background' }),
    item('lower-north-current', 'route-current', 6, 9.7, 'N', 'flow', { renderPass: 'background', timeOffset: 0.5 }),
    item('wreck-salvage', 'salvage-metal', 4.4, 4.9, 'S', 'shimmer'),
    item('route-salvage', 'salvage-metal', 5.1, 6.2, 'E', 'b-shimmer', { timeOffset: 0.3 }),
    item('reef-salvage', 'salvage-metal', 8.8, 8.9, 'W', 'c-shimmer', { timeOffset: 0.7 }),

    // Shared route roots keep wake/strip attachments moving with their actors.
    item('submarine-wake', 'boost-trail', 6, 8.2, 'N', 'boost', {
      renderPass: 'background', motion: submarinePatrol,
    }),
    item('expedition-submarine', 'submarine-yellow', 6, 8.2, 'N', 'upgraded-travel', {
      motion: submarinePatrol,
    }),
    item('eel-following-water', 'following-strip', 9.6, 8.8, 'N', 'flow', {
      renderPass: 'background', motion: eelPatrol,
    }),
    item('east-pocket-eel', 'creature-eel', 9.6, 8.8, 'N', 'swim', {
      motion: eelPatrol,
    }),
    item('west-pocket-fish', 'creature-fish', 4.1, 7.4, 'E', 'swim', {
      motion: fishPatrol, timeOffset: 0.25,
    }),
    item('wreck-water-bubbles', 'decor-bubbles', 3.6, 6.2, 'S', 'rise', { timeOffset: 0.6 }),
    item('reef-water-bubbles', 'decor-bubbles', 10.4, 2.4, 'S', 'rise', { timeOffset: 0.2 }),

    // Near framing stays outside the craft's full patrol envelope.
    item('foreground-east-rock', 'decor-foreground-rock', 12, 10.9, 'W', 'static', { renderPass: 'foreground' }),
    item('foreground-east-coral', 'decor-foreground-coral', 11, 11, 'N', 'idle', { renderPass: 'foreground', timeOffset: 0.7 }),
    item('foreground-east-starfish', 'decor-starfish', 10, 11, 'S', 'static'),
  ],
  highlights: [
    {
      title: 'A clear route through the canyon',
      description: 'The warm yellow craft remains the focal point against turquoise open water. Northbound currents and a distant portal make the passage readable at a glance.',
      objectIds: ['submarine-yellow', 'route-current', 'portal-rim', 'safe-passage'],
    },
    {
      title: 'Connected terrain, distinct materials',
      description: 'Cobalt walls, a low shelf, reef and open wreck ribs each join through their own matching native cross-section. Bends keep the same tile pitch and orientation as the adjoining modules.',
      objectIds: ['rock-wall-corner', 'rock-shelf-corner', 'reef-corner', 'wreck-corner'],
    },
    {
      title: 'Life in the side pockets',
      description: 'A fish explores the quieter wreck bank while a slender eel circles the coral side. Kelp, bubbles and dim schools create movement around the broad central lane.',
      objectIds: ['creature-fish', 'creature-eel', 'decor-kelp', 'decor-bubbles', 'decor-background-fish'],
    },
    {
      title: 'Depth without losing the playfield',
      description: 'Quiet distant silhouettes and light sit behind the craft. Bright coral and broken masonry gather along the banks, with foreground framing kept outside the patrol routes.',
      objectIds: ['decor-background-rock', 'decor-background-wreck', 'decor-light-shafts', 'decor-foreground-coral', 'column-broken'],
    },
    {
      title: 'Dense, reusable reef gardens',
      description: 'Two elongated reef gardens and two broad coral gardens layer rocks, coral, kelp and seafloor accents at fractional offsets along the banks. Their footprints stay outside the craft and creature patrols.',
      objectIds: ['underwater-reef-garden-a', 'underwater-reef-garden-b', 'underwater-coral-garden-a', 'underwater-coral-garden-b'],
    },
  ],
  note: 'A 48-second scene study using the catalog’s native tile scale, four captured facings and animation cadence. Patrol paths stage the art composition; the object pages retain the complete per-asset review.',
};
