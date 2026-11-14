import { mulberry32 } from '../../assets/expedition/route/route.js';
import { collides } from '../eel-strike-preview/fairness.js';

/* Issue #76 reef rules shared by the review page and its Node check (check.mjs). Pure; nothing here draws.

   A reef chunk is a creature chunk packed with brittle reef ('b') around a few bedrock outcrops ('#').
   Open water aprons sit at the entry (bottom) and exit (top), so the reef reads as a wall the
   parrotfish rams into, and any line can meet any neighbouring chunk.

   A line is the parrotfish's course through the reef: one column centre per reef row (bottom to top).
   The breach is every brittle cell the line's `breach_columns`-wide strip overlaps by at least
   OVERLAP. A line is valid when its strip never touches bedrock, and fair when a steering bot with
   the ship's real handling, a reaction delay and no more look-ahead than the parrotfish's lead
   follows it from every entry position without touching reef. Each chunk keeps up to
   `lines_per_chunk` fair lines; a dive picks one per chunk, so the route cannot be memorised. */

export const COLUMNS = 11;
const OVERLAP = 0.35;

/** Reef chunk: rows top (exit) to bottom (entry); walls in columns 0 and 10. */
function reefChunk(id, name, height, outcrops) {
  const rows = Array.from({ length: height }, (_, y) => [...(y < 2 || y >= height - 3 ? '#.........#' : '#bbbbbbbbb#')]);
  for (const [x, y, w, h] of outcrops) for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) rows[y + j][x + i] = '#';
  return { id, name, rows: rows.map((r) => r.join('')) };
}

export const REEF_CHUNKS = [
  reefChunk('reef-pillars', 'Reef Pillars', 18, [[3, 4, 2, 2], [7, 8, 2, 2], [2, 11, 2, 2], [6, 13, 1, 1]]),
  reefChunk('reef-slalom', 'Bedrock Slalom', 18, [[1, 4, 3, 1], [6, 7, 4, 1], [1, 10, 3, 1], [7, 13, 3, 1]]),
  reefChunk('reef-twin', 'Twin Outcrops', 18, [[3, 4, 1, 3], [7, 4, 1, 3], [5, 9, 1, 2], [2, 12, 2, 1], [7, 12, 2, 1]]),
  reefChunk('reef-scatter', 'Scattered Reef', 18, [[5, 5, 1, 1], [2, 8, 1, 1], [8, 10, 1, 1], [5, 13, 1, 1]]),
];

/** The reef rows of a chunk as [first, last], counted from the top. */
export function reefRows(rows) {
  const ys = rows.map((r, y) => (r.includes('b') ? y : -1)).filter((y) => y >= 0);
  return [ys[0], ys[ys.length - 1]];
}

/** Columns a strip centred on x breaks in a row. */
export function breachCells(x, width) {
  const out = [], a = x - width / 2, b = x + width / 2;
  for (let cx = Math.floor(a); cx <= Math.floor(b); cx++) if (Math.min(b, cx + 1) - Math.max(a, cx) >= OVERLAP) out.push(cx);
  return out;
}

/** Carve one line through a chunk's reef rows, bottom to top, or null when the chunk boxes it in. */
export function carveLine(rows, rng, rules) {
  const r = rules.reef, [top, bottom] = reefRows(rows), n = bottom - top + 1;
  const lo = 1 + r.breach_columns / 2 - OVERLAP + 0.05, hi = COLUMNS - lo;
  const ok = (x, y) => x >= lo && x <= hi && breachCells(x, r.breach_columns).every((cx) => rows[y][cx] !== '#');
  const steps = []; for (let s = -r.max_shift_columns; s <= r.max_shift_columns + 1e-9; s += 0.2) steps.push(Math.round(s * 10) / 10);
  // Waypoints every few rows make it wind; depth-first search with backtracking keeps it inside the reef.
  const targets = Array.from({ length: Math.ceil(n / 4) + 1 }, () => lo + rng() * (hi - lo));
  const xs = [];
  const go = (i, x) => {
    if (!ok(x, bottom - i)) return false;
    xs[i] = x;
    if (i === n - 1) return true;
    const t = targets[Math.floor((i + 1) / 4)];
    const order = steps.map((s) => ({ s, w: -Math.abs(x + s - t) + rng() * 1.2 })).sort((p, q) => q.w - p.w);
    for (const { s } of order) if (go(i + 1, Math.round((x + s) * 10) / 10)) return true;
    return false;
  };
  for (let tries = 0; tries < 12; tries++) if (go(0, Math.round((lo + rng() * (hi - lo)) * 10) / 10)) return xs.slice(0, n);
  return null;
}

/** Rows as collision grid with the line's breach open (intact reef counts as rock). */
export function carvedGrid(rows, xs, rules) {
  const [top, bottom] = reefRows(rows), grid = rows.map((r) => [...r].map((ch) => (ch === 'b' ? '#' : ch)));
  xs.forEach((x, i) => { for (const cx of breachCells(x, rules.reef.breach_columns)) grid[bottom - i][cx] = '.'; });
  return { grid, top, bottom };
}

/** Line x at a chunk row (fractional, rows counted from the top); entry and exit aprons hold the end values. */
export function lineAt(xs, top, bottom, y) {
  const i = Math.max(0, Math.min(xs.length - 1, bottom + 0.5 - y)), k = Math.floor(i), f = i - k;
  return k + 1 < xs.length ? xs[k] + (xs[k + 1] - xs[k]) * f : xs[k];
}

/**
 * Steering bot: real handling (lateral speed and acceleration at chase speed), a reaction delay, and
 * look-ahead no further than the parrotfish's head. Returns the first reef contact or null.
 */
export function flyLine(rows, xs, rules, startX) {
  // The ship arrives from the previous chunk: four rows of open water below the entry stand in for it.
  const { grid, top, bottom } = carvedGrid(rows, xs, rules);
  for (let i = 0; i < 4; i++) grid.push([...'#.........#']);
  const fwd = rules.forward_rows_per_second * rules.pursuit_speed_multiplier, dt = 1 / 60;
  const look = rules.reef.bot_look_rows, delay = Math.round(rules.reef.reaction_seconds / dt);
  let x = startX, y = grid.length - 0.6, vx = 0;
  const seen = [];
  while (y > 0.6) {
    seen.push(lineAt(xs, top, bottom, y - look));
    const goal = seen[Math.max(0, seen.length - 1 - delay)];
    const want = Math.abs(goal - x) < 0.06 ? 0 : Math.sign(goal - x) * Math.min(1, Math.abs(goal - x) * 3) * rules.lateral_columns_per_second;
    vx += Math.max(-rules.lateral_acceleration * dt, Math.min(rules.lateral_acceleration * dt, want - vx));
    x += vx * dt; y -= fwd * dt;
    if (collides(grid, x, y, rules.ship_radius, rules)) return { x, y };
  }
  return null;
}

/** Fair lines for one chunk: each flown from the far left, centre and far right of the entry. */
export function fairLines(chunk, rules, seed = 76) {
  const rng = mulberry32(seed + chunk.id.length * 131), fair = [], rejected = [];
  for (let k = 0; k < rules.reef.candidate_lines && fair.length < rules.reef.lines_per_chunk; k++) {
    const xs = carveLine(chunk.rows, rng, rules);
    if (!xs) continue;
    const hit = [1.6, 5.5, 9.4].map((sx) => flyLine(chunk.rows, xs, rules, sx)).find(Boolean);
    (hit ? rejected : fair).push({ xs, hit });
  }
  return { fair, rejected };
}
