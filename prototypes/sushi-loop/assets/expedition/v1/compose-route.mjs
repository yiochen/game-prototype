// Compose the playable expedition route from the authored designer map.
//
//   node prototypes/sushi-loop/assets/expedition/v1/compose-route.mjs
//
// The designer map stays the layout source (obstacle/decor cells). This step
// assigns kit sprites deterministically, derives connected rock beds from
// neighbouring obstacles, places one 2x2 wreck and lays salvage pickups along
// the open passage. Output is shared by the HTML review and Godot content.
import { readFileSync, writeFileSync } from 'node:fs';

const here = new URL('.', import.meta.url);
const mapUrl = new URL('../../../design/underwater-map-designer/maps/turquoise-passage-organic-80.json', here);
const manifestUrl = new URL('./manifest.json', here);

const map = JSON.parse(readFileSync(mapUrl, 'utf8'));
const kit = JSON.parse(readFileSync(manifestUrl, 'utf8')).sprites;
const { columns, rows } = map.grid;

const hash = (x, y, salt) => {
  let h = (x * 374761393 + y * 668265263 + salt * 2147483647) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
};
const family = (prefix) => Object.keys(kit).filter((name) => name.startsWith(prefix)).sort();
const pick = (prefix, x, y, salt) => { const list = family(prefix); return list[Math.floor(hash(x, y, salt) * list.length)]; };

const solid = Array.from({ length: rows }, () => Array(columns).fill(false));
const decorAt = new Map();
for (const p of map.placements) {
  if (p.layer === 'obstacles') solid[p.y][p.x] = p.object;
  else decorAt.set(`${p.x},${p.y}`, p.object);
}

// One 2x2 wreck replaces a solid rock block near the finish (display rows 75–76).
const wreck = { x: 0, y: rows - 76, w: 2, h: 2 };
for (let dy = 0; dy < wreck.h; dy++) for (let dx = 0; dx < wreck.w; dx++) {
  if (!solid[wreck.y + dy][wreck.x + dx]) throw new Error('Wreck must replace solid cells');
}

const isSolid = (x, y) => y >= 0 && y < rows && x >= 0 && x < columns && Boolean(solid[y][x]);
// Off-map columns count as rock so edge walls run flush with the screen.
const bedSolid = (x, y) => (x < 0 || x >= columns) ? (y >= 0 && y < rows && isSolid(Math.max(0, Math.min(columns - 1, x)), y)) : isSolid(x, y);
const inWreck = (x, y) => x >= wreck.x && x < wreck.x + wreck.w && y >= wreck.y && y < wreck.y + wreck.h;

const beds = [], obstacles = [], decor = [];
for (let y = 0; y < rows; y++) for (let x = 0; x < columns; x++) {
  if (!isSolid(x, y)) continue;
  const mask = (bedSolid(x, y - 1) ? 1 : 0) | (bedSolid(x + 1, y) ? 2 : 0) | (bedSolid(x, y + 1) ? 4 : 0) | (bedSolid(x - 1, y) ? 8 : 0);
  beds.push({ x, y, sprite: `bed-${String(mask).padStart(2, '0')}` });
  if (inWreck(x, y)) continue;
  const object = solid[y][x];
  let sprite;
  if (object.startsWith('reef')) sprite = pick('reef-', x, y, 3);
  else {
    const r = hash(x, y, 1);
    // Pale columns read as islands: keep them off fully enclosed interior cells.
    const exposed = !isSolid(x - 1, y) || !isSolid(x + 1, y) || !isSolid(x, y + 1);
    const enclosed = isSolid(x - 1, y) && isSolid(x + 1, y) && isSolid(x, y + 1) && isSolid(x, y - 1);
    sprite = r < 0.17 && exposed ? pick('stone-', x, y, 2) : r < 0.27 && exposed ? pick('reef-', x, y, 3) : r < 0.32 ? pick('rocktall-', x, y, 2) : enclosed && r < 0.6 ? pick('rockbig-', x, y, 4) : pick('rock-', x, y, 2);
  }
  obstacles.push({ x, y, w: 1, h: 1, sprite, family: kit[sprite].family });
}
obstacles.push({ ...wreck, sprite: 'wreck-00', family: 'wreck' });

// Growth roots on the seabed inside a rock nest: the cell's rock becomes a
// nest variant and the matching growth sprite (rendered with that nest as a
// holdout) is placed as non-collidable decor.
const obstacleAt = new Map(obstacles.map((o) => [`${o.x},${o.y}`, o]));
const nests = family('nest-');
function growIn(x, y, kind, dressing = false) {
  const nest = nests[Math.floor(hash(x, y, 14) * nests.length)];
  const options = family(`grow-${kind}-${nest.slice(5)}`);
  const obstacle = obstacleAt.get(`${x},${y}`);
  obstacle.sprite = nest; obstacle.family = 'rock';
  decor.push({ x, y, sprite: options[Math.floor(hash(x, y, 15) * options.length)], anchor: 'nest', ...(dressing ? { dressing: true } : {}) });
}

for (const [key, object] of decorAt) {
  const [x, y] = key.split(',').map(Number);
  if (inWreck(x, y)) continue;
  if (isSolid(x, y)) {
    const r = hash(x, y, 5);
    const kind = object === 'decor-kelp' ? (r < 0.6 ? 'kelp' : 'garden')
      : object === 'decor-foreground-coral' ? (r < 0.7 ? 'coral' : 'branch')
      : (r < 0.5 ? 'garden' : r < 0.8 ? 'coral' : 'star');
    growIn(x, y, kind);
  } else {
    const kind = object === 'decor-kelp' ? 'seabed-grass-' : object === 'decor-foreground-coral' ? (hash(x, y, 8) < 0.5 ? 'seabed-pebbles-' : 'seabed-star-') : 'seabed-fan-';
    decor.push({ x, y, sprite: pick(kind, x, y, 9), anchor: 'seabed' });
  }
}

// Dressing: the authored map marks where decor clusters start; the concept is
// lusher, so undecorated rock also carries growth (never collidable).
const dressing = [['coral', 0.4], ['branch', 0.2], ['garden', 0.15], ['kelp', 0.15], ['star', 0.1]];
for (let y = 0; y < rows; y++) for (let x = 0; x < columns; x++) {
  if (!isSolid(x, y) || inWreck(x, y) || decorAt.has(`${x},${y}`)) continue;
  const exposed = !isSolid(x - 1, y) || !isSolid(x + 1, y) || !isSolid(x, y + 1) || !isSolid(x, y - 1);
  if (hash(x, y, 11) >= (exposed ? 0.3 : 0.12)) continue;
  let r = hash(x, y, 12), kind = dressing[0][0];
  for (const [name, weight] of dressing) { if (r < weight) { kind = name; break; } r -= weight; }
  growIn(x, y, kind, true);
}

// Passage centre per row, walking from the start (bottom) toward the finish.
const runs = (y) => {
  const out = []; let start = -1;
  for (let x = 0; x <= columns; x++) {
    const open = x < columns && !isSolid(x, y);
    if (open && start < 0) start = x;
    if (!open && start >= 0) { out.push([start, x - 1]); start = -1; }
  }
  return out;
};
const centres = new Array(rows);
let previous = columns / 2;
for (let y = rows - 1; y >= 0; y--) {
  const options = runs(y);
  options.sort((a, b) => Math.abs((a[0] + a[1] + 1) / 2 - previous) - Math.abs((b[0] + b[1] + 1) / 2 - previous));
  const [a, b] = options[0];
  previous = Math.min(Math.max(previous, a + 0.5), b + 0.5);
  if (b - a >= 2) previous = (a + b + 1) / 2;
  centres[y] = previous;
}

// Salvage: short trails of three, then a gap, never inside obstacle cells.
const pickups = [];
for (let y = rows - 5, n = 0; y > 1; y--, n++) {
  if (n % 7 > 2) continue;
  const x = centres[y];
  const cell = Math.floor(x);
  if (isSolid(cell, y) || isSolid(Math.min(columns - 1, Math.ceil(x - 0.5)), y)) continue;
  pickups.push({ x: Number(x.toFixed(2)), y: y + 0.5 });
}

// Original art set: the approved #33 production objects only, one standalone
// piece per rock cell on the shared ground layer, with no connected wall/shelf
// modules. Growth cells show the plant itself instead of a rock, so coral and
// kelp stand on the seabed between neighbouring rocks.
const CLIPS = {
  'floor-underwater': ['scroll'], 'decor-background-rock': ['static'], 'decor-foreground-rock': ['static'],
  'boulder-underwater': ['static'], 'column-broken': ['static'], 'decor-ruin-fragment': ['static'], 'crate-wood': ['static'],
  'decor-foreground-coral': ['idle'], 'decor-midground-coral': ['idle'], 'decor-kelp': ['idle'], 'decor-starfish': ['static'],
  'decor-background-wreck': ['static'], 'decor-background-fish': ['swim'], 'decor-bubbles': ['rise'], 'decor-light-shafts': ['ambient'],
  'salvage-metal': ['shimmer', 'b-shimmer', 'c-shimmer'], 'submarine-yellow': ['travel'],
};
const DIRS = ['N', 'E', 'S', 'W'];
const growthAt = new Map(decor.filter((d) => d.anchor === 'nest').map((d) => [`${d.x},${d.y}`, d.sprite.split('-')[1]]));
const exposedAt = (x, y) => !isSolid(x - 1, y) || !isSolid(x + 1, y) || !isSolid(x, y + 1) || !isSolid(x, y - 1);
const original = [];
// Extra pieces from the v2 experiment (same recipes as production): rocks at
// several heights/shades, pale statues/pillars and multi-tile arches.
const v2 = JSON.parse(readFileSync(new URL('../v2/library.json', here), 'utf8'));
const v2ids = v2.objects.map((o) => o.id);
const v2rocks = v2.objects.filter((o) => o.family === 'rock');
const PALE = ['column-broken', 'decor-ruin-fragment', ...v2.objects.filter((o) => o.family === 'ruin').map((o) => o.id)];

// Arches: span a 1–3 cell passage whose two bordering cells are rock; the
// legs stand on those (already collidable) cells and the span stays open.
const arches = [];
const archLegs = new Set();
for (let y = rows - 8; y > 3; y--) {
  if (arches.some((a) => Math.abs(a.y - y) < 12)) continue;
  for (const [a, b] of runs(y)) {
    const span = b - a + 1;
    if (span > 3 || a === 0 || b === columns - 1 || !isSolid(a - 1, y) || !isSolid(b + 1, y)) continue;
    if (hash(a, y, 51) > 0.55) continue;
    // Cycle styles so consecutive landmarks differ; fall back to any style with this span.
    const styles = ['arch-ruin', 'bridge', 'arch-pointed', 'arch-broken'];
    const ids = new Set(v2.objects.filter((o) => o.family === 'landmark').map((o) => o.id));
    const preferred = styles.slice(arches.length % styles.length).concat(styles).map((st) => `${st}-${span}`);
    arches.push({ x: a - 1, y, w: span + 2, h: 1, id: preferred.find((id) => ids.has(id)), solid: [[a - 1, y], [b + 1, y]] });
    archLegs.add(`${a - 1},${y}`); archLegs.add(`${b + 1},${y}`);
    break;
  }
}

const chosen = new Map();
for (let y = 0; y < rows; y++) for (let x = 0; x < columns; x++) {
  if (!isSolid(x, y) || archLegs.has(`${x},${y}`)) continue;
  const dir = DIRS[Math.floor(hash(x, y, 21) * 4)];
  const growth = growthAt.get(`${x},${y}`);
  const plant = { coral: 'decor-foreground-coral', branch: 'decor-midground-coral', garden: hash(x, y, 22) < 0.5 ? 'decor-midground-coral' : 'decor-kelp', kelp: 'decor-kelp' }[growth];
  const keep = { coral: 0.42, branch: 0.4, garden: 0.3, kelp: 0.28 }[growth] ?? 0;
  if (plant && hash(x, y, 24) < keep) { original.push({ x, y, id: plant, dir }); chosen.set(`${x},${y}`, plant); continue; }
  const exposed = exposedAt(x, y);
  const r = hash(x, y, 23);
  const paleNear = [[-1, 0], [0, -1], [-1, -1], [1, -1]].some(([dx, dy]) => PALE.includes(chosen.get(`${x + dx},${y + dy}`)));
  let id;
  if (exposed && !paleNear && r < 0.24) id = PALE[Math.floor(hash(x, y, 25) * PALE.length)];
  else if (exposed && r >= 0.24 && r < 0.26) id = 'crate-wood';
  else {
    // Interior cells lean tall (the wall mass), passage edges lean low/mid.
    const pool = [...v2rocks.filter((o) => exposed ? o.height < 1.7 : o.height > 0.9).map((o) => o.id),
      'decor-background-rock', 'decor-foreground-rock', ...(exposed ? [] : ['boulder-underwater'])];
    id = pool[Math.floor(hash(x, y, 26) * pool.length)];
  }
  original.push({ x, y, id, dir });
  chosen.set(`${x},${y}`, id);
}
for (const a of arches) original.push({ ...a, dir: 'S' });
// Open-water dressing from the map's seabed decor cells: starfish, plus a
// couple of sunken-boat silhouettes. Effects sit in open water near rocks.
const seabedOriginal = [];
let wrecks = 0;
for (const d of decor.filter((d) => d.anchor === 'seabed')) {
  const r = hash(d.x, d.y, 31);
  if (r < 0.3) seabedOriginal.push({ x: d.x, y: d.y, id: 'decor-starfish', dir: DIRS[Math.floor(hash(d.x, d.y, 32) * 4)], scale: 0.55 });
  else if (r < 0.4 && wrecks < 2) { seabedOriginal.push({ x: d.x, y: d.y, id: 'decor-background-wreck', dir: 'S' }); wrecks++; }
}
const effects = [];
for (let y = 1; y < rows - 1; y++) for (let x = 0; x < columns; x++) {
  if (isSolid(x, y) || !(isSolid(x - 1, y) || isSolid(x + 1, y))) continue;
  const r = hash(x, y, 41);
  if (r < 0.06) effects.push({ x, y, id: 'decor-bubbles', dir: 'S' });
}
for (let y = 3; y < rows; y += 9) effects.push({ x: Math.floor(hash(y, 1, 42) * columns), y, id: 'decor-light-shafts', dir: 'S' });
const library = JSON.parse(readFileSync(new URL('../../production/library.json', here), 'utf8'));
for (const o of library.objects) o.base = 'assets/production';
for (const o of v2.objects) o.base = 'assets/expedition/v2';
for (const id of v2ids) CLIPS[id] = ['static'];
const originalSet = {};
for (const [id, clipIds] of Object.entries(CLIPS)) {
  const entry = library.objects.find((o) => o.id === id) ?? v2.objects.find((o) => o.id === id);
  originalSet[id] = { name: entry.name ?? id, footprint: entry.footprint, frameSize: entry.frameSize, root: entry.root, sourceScale: entry.sourceScale,
    clips: clipIds.map((clipId) => {
      const clip = entry.clips.find((c) => c.id === clipId);
      return { id: clipId, fps: clip.fps, frames: clip.frames, frameOrder: clip.frameOrder,
        directions: Object.fromEntries(Object.entries(clip.directions).map(([d, v]) => [d, { image: `${entry.base}/${v.image}`, rects: v.rects }])) };
    }) };
}
writeFileSync(new URL('../../../design/underwater-kit-preview/original-set.json', here), JSON.stringify({ source: 'assets/production/library.json', objects: originalSet }) + '\n');

const route = {
  format: 'sushi-loop-expedition-route',
  version: 1,
  source: { map: 'design/underwater-map-designer/maps/turquoise-passage-organic-80.json', name: map.name },
  coordinates: 'Cells are top-left integer coordinates; y increases toward the start (south). The ship departs from the bottom row and travels toward y = 0.',
  columns, rows,
  start: { x: columns / 2, y: rows - 0.5 },
  finish_y: 0,
  beds, obstacles, decor, pickups,
  original: { objects: original, seabed: seabedOriginal, effects },
  autopilot: centres.map((c) => Number(c.toFixed(2))),
};
console.log(`route: ${obstacles.length} obstacles, ${beds.length} beds, ${decor.length} decor, ${pickups.length} pickups`);
