// Seeded chunk-based expedition routes for issue #21.
//
// Pure ES module (no Node or DOM APIs): shared by the chunk build/validation
// scripts and the HTML review, and the reference for the Godot port.
//
// A chunk is a short map authored as rows of characters, listed top (exit)
// to bottom (entry); the ship travels upward.
//   '#' rock          'k' rock with kelp   'c' rock with coral   'm' rock with midground coral
//   '.' open water    ',' water with seabed decor                '$' water with gold salvage
// Chunks join only where the exit row of one and the entry row of the next
// share an open run at least MIN_SEAM cells wide, and the real hull (collider,
// forward and maximum sideways speed) can fly through each chunk and across
// each seam without trap lanes.

// World width in cells. The screen shows VIEW_COLUMNS of them and follows the
// ship sideways, so wide forks can put their lanes beyond one screen.
export const COLUMNS = 11;
export const VIEW_COLUMNS = 7;
export const MIN_SEAM = 2;
// Reachability model: per row the ship may slide sideways at most MAX_SHIFT
// cells inside the open run it occupies, then advance one row.
export const MAX_SHIFT = 2;
// Ship physics model (joystick steering): the hull's collider half-size in
// cells; positions every quarter column and sixth of a row, sliding at most
// one quarter column per sixth row (1.5 columns per row). Travel in
// godot/content/expedition.json collides a smaller hull circle (ship_radius ≤
// SHIP_HALF) against round rocks, so this box is the conservative bound; lateral
// speed must stay ≥ 1.5 × forward speed (rules tests check both).
export const SHIP_HALF = [0.32, 0.44];
const QX = 4, QY = 6, SHIP_LO = 2, SHIP_HI = COLUMNS * QX - 2;

export function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Integer-only (32-bit) so the GDScript port reproduces it bit for bit.
export function hash(x, y, salt) {
  let h = (Math.imul(x, 374761393) + Math.imul(y, 668265263) + Math.imul(salt, 2147483647)) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

export const isRock = (ch) => ch === '#' || ch === 'k' || ch === 'c' || ch === 'm';
const openAt = (rows, x, y) => y >= 0 && y < rows.length && x >= 0 && x < rows[y].length && !isRock(rows[y][x]);

/** Contiguous open runs of a row as [start, end] inclusive. */
export function runs(row) {
  const out = []; let start = -1;
  for (let x = 0; x <= row.length; x++) {
    const open = x < row.length && !isRock(row[x]);
    if (open && start < 0) start = x;
    if (!open && start >= 0) { out.push([start, x - 1]); start = -1; }
  }
  return out;
}

const openSet = (row) => [...row].map((ch, x) => (isRock(ch) ? -1 : x)).filter((x) => x >= 0);

/** Widest shared open run between two rows (seam width). */
export function seamWidth(upperEntry, lowerExit) {
  let best = 0, run = 0;
  for (let x = 0; x < upperEntry.length; x++) {
    run = !isRock(upperEntry[x]) && !isRock(lowerExit[x]) ? run + 1 : 0;
    best = Math.max(best, run);
  }
  return best;
}

/**
 * Cells reachable from the entry row moving up, sliding at most `shift` cells
 * sideways per row within an open run. Returns a Set of "x,y".
 */
export function reachable(rows, shift = MAX_SHIFT) {
  const h = rows.length, seen = new Set();
  let frontier = openSet(rows[h - 1]).map((x) => x);
  for (const x of frontier) seen.add(`${x},${h - 1}`);
  for (let y = h - 1; y > 0; y--) {
    const next = new Set();
    for (const x of frontier) {
      // Slide within this row's run, then rise if the cell above is open.
      for (let dx = -shift; dx <= shift; dx++) {
        const nx = x + dx;
        let clear = true;
        for (let s = Math.min(x, nx); s <= Math.max(x, nx); s++) if (!openAt(rows, s, y)) clear = false;
        if (!clear) continue;
        seen.add(`${nx},${y}`);
        if (openAt(rows, nx, y - 1)) next.add(nx);
      }
    }
    frontier = [...next];
    for (const x of frontier) seen.add(`${x},${y - 1}`);
  }
  return seen;
}

/**
 * Open cells reachable from the entry from which the exit cannot be reached
 * (moving up/sideways without a speed limit). Any such cell is a dead end.
 */
export function deadEnds(rows) {
  const h = rows.length;
  const canExit = new Set();
  for (const x of openSet(rows[0])) canExit.add(`${x},0`);
  for (let y = 0; y < h; y++) {
    // Cells in a run whose any member can rise into a known exit-connected cell.
    for (const [a, b] of runs(rows[y])) {
      let ok = false;
      for (let x = a; x <= b; x++) if (canExit.has(`${x},${y}`) || (y > 0 && canExit.has(`${x},${y - 1}`))) ok = true;
      if (ok) for (let x = a; x <= b; x++) canExit.add(`${x},${y}`);
    }
  }
  const reach = reachable(rows, rows[0].length);
  return [...reach].filter((key) => !canExit.has(key));
}

/** Difficulty 1–5 from narrowness, required swerving and rock density. */
export function difficulty(rows) {
  let narrow = 0, swerve = 0, rock = 0, prev = null;
  const reach = reachable(rows);
  for (let y = rows.length - 1; y >= 0; y--) {
    const usable = runs(rows[y]).filter(([a, b]) => { for (let x = a; x <= b; x++) if (reach.has(`${x},${y}`)) return true; return false; });
    if (!usable.length) continue;
    const widest = usable.reduce((m, [a, b]) => Math.max(m, b - a + 1), 0);
    narrow += 1 / widest;
    const ref = prev ?? rows[0].length / 2;
    const centre = usable.map(([a, b]) => (a + b) / 2).sort((p, q) => Math.abs(p - ref) - Math.abs(q - ref) || p - q)[0];
    if (prev !== null) swerve += Math.abs(centre - prev);
    prev = centre;
    // Rock density inside the outermost open cells, so wall padding does not count.
    const first = Math.min(...usable.map(([a]) => a)), last = Math.max(...usable.map(([, b]) => b));
    const span = Math.min(VIEW_COLUMNS, last - first + 3);
    let inner = 0; for (let x = first - 1; x <= last + 1; x++) if (x >= 0 && x < rows[y].length && isRock(rows[y][x])) inner++;
    rock += inner / span;
  }
  const n = rows.length;
  const score = 1 + 5 * (narrow / n - 0.25) + 3 * (swerve / n) + 2 * (rock / n - 0.45);
  return Math.round(Math.min(5, Math.max(1, score)) * 2) / 2;
}

// ------------------------------------------------------------ chunk files
// Each chunk is a map-designer document (format sushi-loop-underwater-map)
// with a `chunk` block. Layers: obstacles (rock), decor (growth on rock or
// seabed decor on water) and pickups (gold salvage).
const GROWTH = { 'decor-kelp': 'k', 'decor-foreground-coral': 'c', 'decor-midground-coral': 'm' };
const GROWTH_IDS = { k: 'decor-kelp', c: 'decor-foreground-coral', m: 'decor-midground-coral' };

/** Designer document → { id, kind, source, difficultyOverride, rows }. */
export function chunkFromMap(doc, id) {
  const { columns, rows: height } = doc.grid;
  const cells = Array.from({ length: height }, () => Array(columns).fill('.'));
  const at = (layer) => new Map(doc.placements.filter((p) => p.layer === layer).map((p) => [`${p.x},${p.y}`, p.object]));
  const rock = at('obstacles'), decor = at('decor'), gold = at('pickups');
  for (let y = 0; y < height; y++) for (let x = 0; x < columns; x++) {
    const key = `${x},${y}`;
    if (rock.has(key)) cells[y][x] = GROWTH[decor.get(key)] ?? '#';
    else if (gold.has(key)) cells[y][x] = '$';
    else if (decor.has(key)) cells[y][x] = ',';
  }
  const meta = doc.chunk ?? {};
  return { id, name: doc.name, kind: meta.kind ?? 'normal', source: meta.source ?? '', difficultyOverride: meta.difficulty ?? null, rows: cells.map((r) => r.join('')) };
}

/** Rows → designer document (used to migrate text chunks and by tests). */
export function chunkToMap({ name, kind, source = '', difficultyOverride = null, rows }) {
  const placements = [];
  const add = (layer, object, x, y) => placements.push({ id: `${layer}:${x}:${y}`, layer, object, x, y, direction: 'S', footprint: [1, 1] });
  rows.forEach((row, y) => [...row].forEach((ch, x) => {
    if (isRock(ch)) { add('obstacles', 'rock-wall-middle', x, y); if (GROWTH_IDS[ch]) add('decor', GROWTH_IDS[ch], x, y); }
    else if (ch === ',') add('decor', 'decor-starfish', x, y);
    else if (ch === '$') add('pickups', 'salvage-gold', x, y);
  }));
  return {
    format: 'sushi-loop-underwater-map', version: 1, name,
    grid: { columns: rows[0].length, rows: rows.length, cellSize: 128 }, floor: 'floor-underwater',
    coordinates: { origin: 'top-left', x: 'right', y: 'down', placement: 'cell-top-left' },
    layers: [{ id: 'obstacles', collidable: true }, { id: 'decor', collidable: false }, { id: 'pickups', collidable: false }],
    chunk: { kind, difficulty: difficultyOverride, source },
    placements,
  };
}

/**
 * Analyse chunks at load time: drop invalid ones (reported), score
 * difficulty unless overridden, and list which chunks may follow each.
 */
export function analyzeLibrary(chunks) {
  const problems = {};
  const valid = [];
  // Library order feeds weighted picks, so every loader sorts the same way.
  for (const chunk of [...chunks].sort((p, q) => (p.id < q.id ? -1 : p.id > q.id ? 1 : 0))) {
    const found = validateChunk(chunk);
    if (found.length) { problems[chunk.id] = found; continue; }
    valid.push({ ...chunk, difficulty: chunk.difficultyOverride ?? difficulty(chunk.rows) });
  }
  for (const lower of valid) {
    // Launch chunks open the route: only launch or the start chunk may follow one.
    const opening = (upper) => (upper.kind === 'start' || upper.kind === 'launch' ? lower.kind === 'launch' : true);
    lower.next = lower.kind === 'finish' ? [] : valid.filter((upper) => upper !== lower && opening(upper) && compatible(lower, upper)).map((u) => u.id);
  }
  return { chunks: valid, problems };
}

/** Validate one chunk; returns a list of problems (empty when sound). */
export function validateChunk(chunk) {
  const problems = [];
  const { rows } = chunk;
  if (!rows.length || !rows.every((r) => r.length === COLUMNS)) return [`rows must be ${COLUMNS} cells wide`];
  // Issue #22 feature chunks (current, portal, boost) are offered only by their own plan slots.
  if (!['launch', 'start', 'normal', 'rest', 'fork', 'finish', 'current', 'portal', 'boost'].includes(chunk.kind ?? 'normal')) problems.push(`unknown kind ${chunk.kind}`);
  const reach = reachable(rows);
  if (!openSet(rows[0]).some((x) => reach.has(`${x},0`))) problems.push('exit unreachable at steering speed');
  const dead = deadEnds(rows);
  if (dead.length) problems.push(`dead ends at ${dead.join(' ')}`);
  problems.push(...shipProblems(rows));
  for (let y = 0; y < rows.length; y++) for (let x = 0; x < rows[y].length; x++) {
    if (rows[y][x] === '$' && !reach.has(`${x},${y}`)) problems.push(`unreachable gold ${x},${y}`);
  }
  // Launch: the preparation cruise runs straight up the middle without steering.
  if (chunk.kind === 'launch') {
    if (rows.some((r) => r.includes('$'))) problems.push('launch chunks carry no gold');
    if (rows.some((r) => [...r.slice(4, 7)].some(isRock))) problems.push('launch chunks keep columns 4-6 open');
  }
  return problems;
}

/**
 * Fly the real hull through rows: positions every quarter column and sixth
 * of a row, sliding at most one quarter column per step through open water.
 * Reports an exit the hull cannot reach, gold it cannot collect and still
 * leave, and lanes it can enter but never leave (one-cell diagonal steps
 * would need instant steering).
 */
export function shipProblems(rows) {
  const top = QY / 2, bottom = rows.length * QY - QY / 2;
  const free = (yy) => {
    const y = yy / QY, line = [];
    for (let i = SHIP_LO; i <= SHIP_HI; i++) {
      const x = i / QX;
      let open = true;
      for (let cy = Math.max(0, Math.floor(y - SHIP_HALF[1])); cy <= Math.min(rows.length - 1, Math.floor(y + SHIP_HALF[1])) && open; cy++)
        for (let cx = Math.max(0, Math.floor(x - SHIP_HALF[0])); cx <= Math.min(COLUMNS - 1, Math.floor(x + SHIP_HALF[0])); cx++) if (isRock(rows[cy][cx])) { open = false; break; }
      line[i] = open;
    }
    return line;
  };
  // One step: stay or slide a quarter column; the hull must fit before and after.
  const step = (live, open) => {
    const next = [];
    for (let i = SHIP_LO; i <= SHIP_HI; i++) next[i] = open[i] && ((live[i] && open[i]) || (!!live[i - 1] && !!open[i - 1]) || (!!live[i + 1] && !!open[i + 1]));
    return next;
  };
  const opens = {};
  for (let yy = top; yy <= bottom; yy++) opens[yy] = free(yy);
  const forward = { [bottom]: opens[bottom] }, alive = { [top]: opens[top] };
  for (let yy = bottom - 1; yy >= top; yy--) forward[yy] = step(forward[yy + 1], opens[yy]);
  for (let yy = top + 1; yy <= bottom; yy++) alive[yy] = step(alive[yy - 1], opens[yy]);
  const problems = [];
  if (!forward[top].some(Boolean)) problems.push('exit unreachable by the ship');
  for (let y = 0; y < rows.length; y++) {
    const yy = y * QY + QY / 2, f = forward[yy], a = alive[yy];
    for (let x = 0; x < COLUMNS; x++) {
      if (rows[y][x] !== '$') continue;
      let ok = false;
      for (let i = SHIP_LO; i <= SHIP_HI && !ok; i++) ok = f[i] && a[i] && Math.abs(i / QX - x - 0.5) <= 0.6;
      if (!ok) problems.push(`gold ${x},${y} out of the ship's reach`);
    }
    for (const [a0, b0] of runs(rows[y])) {
      let entered = false, leaves = false;
      for (let i = Math.max(SHIP_LO, a0 * QX); i <= Math.min(SHIP_HI, (b0 + 1) * QX); i++) { entered ||= f[i]; leaves ||= f[i] && a[i]; }
      if (entered && !leaves) problems.push(`trap lane ${a0}-${b0},${y}`);
    }
  }
  return problems;
}

/**
 * Hull check across a seam: `upper`'s last rows over `lower`'s first rows.
 * Only problems the upper chunk introduces count; the same window under open
 * water filters out artifacts of starting the hull anywhere on its bottom row.
 */
export function seamFlies(lower, upper) {
  const below = lower.rows.slice(0, 4), above = upper.rows.slice(-4);
  const flight = (rows) => shipProblems(rows).filter((p) => !p.startsWith('gold'));
  const baseline = new Set(flight([...above.map(() => '.'.repeat(COLUMNS)), ...below]));
  return flight([...above, ...below]).every((p) => baseline.has(p));
}

/** May `upper` directly follow `lower` (upper sits above, ship rises into it)? */
export function compatible(lower, upper) {
  // Each chunk is validated on its own; across the seam the hull must still fly.
  return seamWidth(upper.rows[upper.rows.length - 1], lower.rows[0]) >= MIN_SEAM && seamFlies(lower, upper);
}

/**
 * Plan a run: open-water launch lead-in, start, a rising difficulty curve with a rest stop and a fork,
 * then the finish. Returns the chunk sequence from start (bottom) to finish.
 */
export function generate(seed, library, { slots, force } = {}) {
  const rng = mulberry32(seed);
  const plan = slots ?? ['launch', 'launch', 'start', 1.5, 2, 'rest', 2.5, 'fork', 3, 3.5, 'rest', 'fork', 4, 'finish'];
  const byId = Object.fromEntries(library.map((c) => [c.id, c]));
  const sequence = [];
  const used = new Map();
  for (const slot of plan) {
    const prev = sequence[sequence.length - 1];
    const kind = typeof slot === 'string' ? slot : 'normal';
    const target = typeof slot === 'number' ? slot : null;
    // A forced chunk (designer test) takes the first slot of its kind that can follow.
    const forced = force && !used.has(force) ? byId[force] : null;
    if (forced && forced.kind === kind && (!prev || prev.next.includes(forced.id))) {
      sequence.push(forced); used.set(forced.id, 1); continue;
    }
    let pool = library.filter((c) => c.kind === kind && (!prev || prev.next.includes(c.id)));
    if (!pool.length && prev) pool = library.filter((c) => (c.kind === 'normal' || c.kind === 'rest') && prev.next.includes(c.id));
    if (!pool.length) throw new Error(`No chunk can follow ${prev?.id} for slot ${slot}`);
    const weights = pool.map((c) => (target === null ? 1 : Math.exp(-2.2 * Math.abs(c.difficulty - target))) / (1 + 3 * (used.get(c.id) ?? 0)));
    let r = rng() * weights.reduce((a, b) => a + b, 0), pick = pool[pool.length - 1];
    for (let i = 0; i < pool.length; i++) { r -= weights[i]; if (r <= 0) { pick = pool[i]; break; } }
    sequence.push(byId[pick.id]);
    used.set(pick.id, (used.get(pick.id) ?? 0) + 1);
  }
  return sequence;
}

/** Stack a chunk sequence (start first) into one grid, finish at the top. */
export function assemble(sequence) {
  const rows = [];
  const spans = [];
  for (let i = sequence.length - 1; i >= 0; i--) {
    const c = sequence[i];
    spans.push({ id: c.id, kind: c.kind, difficulty: c.difficulty, y0: rows.length, y1: rows.length + c.rows.length - 1 });
    rows.push(...c.rows);
  }
  return { rows, spans: spans.reverse() };
}

// ------------------------------------------------------------------ scene
// Sprite choice for an assembled grid using the approved production pieces,
// the v2 same-recipe variants and the kit's ground-layer beds.

const DIRS = ['N', 'E', 'S', 'W'];

export function composeScene(grid, v2, seed) {
  const rows = grid.length, COLS = grid[0].length;
  const H = (x, y, salt) => hash(x, y + seed * 977, salt);
  const solid = (x, y) => y >= 0 && y < rows && x >= 0 && x < COLS && isRock(grid[y][x]);
  const bedSolid = (x, y) => (x < 0 || x >= COLS) ? (y >= 0 && y < rows && solid(Math.max(0, Math.min(COLS - 1, x)), y)) : solid(x, y);
  const exposed = (x, y) => !solid(x - 1, y) || !solid(x + 1, y) || !solid(x, y + 1) || !solid(x, y - 1);

  const beds = [];
  for (let y = 0; y < rows; y++) for (let x = 0; x < COLS; x++) {
    if (!solid(x, y)) continue;
    const mask = (bedSolid(x, y - 1) ? 1 : 0) | (bedSolid(x + 1, y) ? 2 : 0) | (bedSolid(x, y + 1) ? 4 : 0) | (bedSolid(x - 1, y) ? 8 : 0);
    beds.push({ x, y, sprite: `bed-${String(mask).padStart(2, '0')}` });
  }

  const rocks = v2.filter((o) => o.family === 'rock');
  const pale = ['column-broken', 'decor-ruin-fragment', ...v2.filter((o) => o.family === 'ruin').map((o) => o.id)];
  const landmarkIds = new Set(v2.filter((o) => o.family === 'landmark').map((o) => o.id));
  const seaEdge = v2.filter((o) => o.family === 'sealife-edge').map((o) => o.id);
  const seaFloor = v2.filter((o) => o.family === 'sealife-floor').map((o) => o.id);

  // Landmarks span a 1–3 cell passage bordered by rock, at least 10 rows apart.
  const landmarks = [], legs = new Set();
  const styles = ['arch-ruin', 'bridge', 'arch-pointed', 'arch-broken'];
  for (let y = rows - 6; y > 3; y--) {
    if (landmarks.some((a) => Math.abs(a.y - y) < 10)) continue;
    for (const [a, b] of runs(grid[y])) {
      const span = b - a + 1;
      if (span > 3 || a === 0 || b === COLS - 1 || !solid(a - 1, y) || !solid(b + 1, y) || H(a, y, 51) > 0.5) continue;
      const order = styles.slice(Math.floor(H(a, y, 53) * styles.length)).concat(styles);
      const id = order.map((s) => `${s}-${span}`).find((i) => landmarkIds.has(i));
      landmarks.push({ x: a - 1, y, w: span + 2, h: 1, id, dir: 'S' });
      legs.add(`${a - 1},${y}`); legs.add(`${b + 1},${y}`);
      break;
    }
  }

  const objects = [], chosen = new Map();
  const plantFor = { k: 'decor-kelp', c: 'decor-foreground-coral', m: 'decor-midground-coral' };
  for (let y = 0; y < rows; y++) for (let x = 0; x < COLS; x++) {
    if (!solid(x, y) || legs.has(`${x},${y}`)) continue;
    const ch = grid[y][x];
    const dir = DIRS[Math.floor(H(x, y, 21) * 4)];
    const edge = exposed(x, y);
    // Authored growth marks become plants about 40% of the time; bare edges sprout occasionally.
    let plant = plantFor[ch] && H(x, y, 24) < 0.42 ? plantFor[ch] : null;
    if (!plant && ch === '#' && edge && H(x, y, 27) < 0.1) plant = H(x, y, 28) < 0.65 ? 'decor-foreground-coral' : H(x, y, 29) < 0.5 ? 'decor-midground-coral' : 'decor-kelp';
    if (plant) { objects.push({ x, y, id: plant, dir }); chosen.set(`${x},${y}`, plant); continue; }
    const r = H(x, y, 23);
    const paleNear = [[-1, 0], [0, -1], [-1, -1], [1, -1]].some(([dx, dy]) => pale.includes(chosen.get(`${x + dx},${y + dy}`)));
    let id;
    if (edge && !paleNear && r < 0.24) id = pale[Math.floor(H(x, y, 25) * pale.length)];
    else if (edge && r >= 0.24 && r < 0.3 && seaEdge.length) id = seaEdge[Math.floor(H(x, y, 22) * seaEdge.length)];
    else {
      const pool = [...rocks.filter((o) => (edge ? o.height < 1.7 : o.height > 0.9)).map((o) => o.id),
        'decor-background-rock', 'decor-foreground-rock', ...(edge ? [] : ['boulder-underwater'])];
      id = pool[Math.floor(H(x, y, 26) * pool.length)];
    }
    objects.push({ x, y, id, dir });
    chosen.set(`${x},${y}`, id);
  }
  objects.push(...landmarks);

  const seabed = [], pickups = [], vents = [];
  let shells = 0;
  for (let y = 0; y < rows; y++) for (let x = 0; x < COLS; x++) {
    const ch = grid[y][x];
    if (ch === '$') pickups.push({ x: x + 0.5, y: y + 0.5 });
    if (ch === ',') {
      const r = H(x, y, 31);
      if (r < 0.3) seabed.push({ x, y, id: 'decor-starfish', dir: DIRS[Math.floor(H(x, y, 32) * 4)], scale: 0.55 });
      else if (r < 0.4 && shells < 6 && seaFloor.length) {
        seabed.push({ x, y, id: seaFloor[Math.floor(H(x, y, 33) * seaFloor.length)], dir: DIRS[Math.floor(H(x, y, 32) * 4)], scale: 0.7 });
        shells++;
      }
    }
    if (!solid(x, y) && (solid(x - 1, y) || solid(x + 1, y)) && H(x, y, 41) < 0.07) vents.push({ x: x + 0.5, y: y + 0.85 });
  }
  const shafts = [];
  for (let y = 3; y < rows; y += 9) shafts.push({ x: Math.floor(H(y, 1, 42) * COLS), y, id: 'decor-light-shafts', dir: 'S' });

  // Steering guide for the review autopilot: nearest open-run centre per row.
  const autopilot = new Array(rows);
  let prev = COLS / 2;
  for (let y = rows - 1; y >= 0; y--) {
    const opts = runs(grid[y]).sort((p, q) => Math.abs((p[0] + p[1] + 1) / 2 - prev) - Math.abs((q[0] + q[1] + 1) / 2 - prev) || p[0] - q[0]);
    const [a, b] = opts[0];
    prev = Math.min(Math.max(prev, a + 0.5), b + 0.5);
    if (b - a >= 2) prev = (a + b + 1) / 2;
    autopilot[y] = prev;
  }
  const collision = [];
  for (let y = 0; y < rows; y++) for (let x = 0; x < COLS; x++) if (solid(x, y)) collision.push({ x, y });
  return { columns: COLS, viewColumns: VIEW_COLUMNS, rows, beds, objects, seabed, pickups, vents, shafts, autopilot, collision };
}
