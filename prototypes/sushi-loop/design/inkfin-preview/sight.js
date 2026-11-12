import { isRock } from '../../assets/expedition/route/route.js';

/* Issue #70 review: which chunks stay fair when the Inkfin's ink limits how far ahead the player sees.
   Pure functions over chunk rows (row 0 is the top/exit; the ship travels up). Nothing here draws.

   Movement model at chase speed: each row the ship rises, it can move at most `shift` columns sideways
   (lateral speed / chase rows per second, rounded down), sweeping through open water only.
     - safe: cells from which the top of the chunk is still reachable.
     - doomed: cells reachable from the entry from which it is not (a dead branch, or a wall that
       appears too late to steer round).
   For every fork (a safe cell with a doomed next step) the player must see the end of that doomed
   branch before committing: `needRows` = branch depth + 1.5 rows + the reaction distance. A chunk is
   fair under a sight distance when every fork's need fits. `look` is how far sideways from the ship
   the end of that branch lies, which a light cone must also reach. */

const open = (rows, x, y) => y >= 0 && y < rows.length && x >= 0 && x < rows[y].length && !isRock(rows[y][x]);

export function chaseRowsPerSecond(rules) { return rules.forward_rows_per_second * rules.pursuit_speed_multiplier; }
export function shiftPerRow(rules) { return Math.max(1, Math.floor(rules.lateral_columns_per_second / chaseRowsPerSecond(rules))); }

function steps(rows, x, y, shift) {
  const out = [];
  for (let dx = -shift; dx <= shift; dx++) {
    const nx = x + dx;
    let clear = open(rows, nx, y - 1);
    for (let s = Math.min(x, nx); clear && s <= Math.max(x, nx); s++) if (!open(rows, s, y)) clear = false;
    if (clear) out.push(nx);
  }
  return out;
}

export function analyzeSight(rows, rules) {
  const h = rows.length, w = rows[0].length, shift = shiftPerRow(rules);
  const reactionRows = rules.ink.reaction_seconds * chaseRowsPerSecond(rules);
  const safe = Array.from({ length: h }, () => new Array(w).fill(false));
  for (let x = 0; x < w; x++) safe[0][x] = open(rows, x, 0);
  for (let y = 1; y < h; y++) for (let x = 0; x < w; x++) safe[y][x] = open(rows, x, y) && steps(rows, x, y, shift).some((nx) => safe[y - 1][nx]);
  const reach = Array.from({ length: h }, () => new Array(w).fill(false));
  for (let x = 0; x < w; x++) reach[h - 1][x] = open(rows, x, h - 1);
  for (let y = h - 1; y > 0; y--) for (let x = 0; x < w; x++) if (reach[y][x]) for (const nx of steps(rows, x, y, shift)) reach[y - 1][nx] = true;
  // Depth of each doomed cell's branch (rows it can still climb) and the columns its end spans.
  const depth = Array.from({ length: h }, () => new Array(w).fill(null));
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    if (!reach[y][x] || safe[y][x]) continue;
    const next = y > 0 ? steps(rows, x, y, shift) : [];
    let d = 0, ends = [x];
    for (const nx of next) { const c = depth[y - 1][nx]; if (!c) continue; if (c.d + 1 > d) { d = c.d + 1; ends = [...c.ends]; } else if (c.d + 1 === d) ends.push(...c.ends); }
    depth[y][x] = { d, ends };
  }
  const forks = [];
  const entryTraps = [];
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    if (y === h - 1 && reach[y][x] && !safe[y][x]) entryTraps.push({ x, y, depth: depth[y][x].d });
    if (!reach[y][x] || !safe[y][x] || y === 0) continue;
    for (const nx of steps(rows, x, y, shift)) {
      const c = depth[y - 1][nx];
      if (!c) continue;
      const needRows = c.d + 1.5 + reactionRows, look = Math.max(...c.ends.map((ex) => Math.abs(ex - x)));
      forks.push({ x, y, to: nx, depth: c.d, needRows, look });
    }
  }
  // Any rock in the chunk must be seen at least the row after next, plus the reaction distance.
  const baseline = rows.some((r) => [...r].some((ch, x) => x > 0 && x < w - 1 && isRock(ch))) ? 1.5 + reactionRows : 0;
  const needRows = forks.reduce((m, f) => Math.max(m, f.needRows), baseline);
  return { shift, reactionRows, safe, reach, forks, entryTraps, baseline, needRows };
}

/** Half-width (columns) the light cone covers `k` rows ahead of the ship. */
export function coneHalfWidth(k, ink) {
  const t = Math.max(0, Math.min(1, k / ink.clear_rows));
  return ink.hull_glow_columns + (ink.cone_far_width_columns / 2 - ink.hull_glow_columns) * t;
}

/** Fair under the current ink settings? Band mode checks rows only; cone mode also checks the width. */
export function judge(report, ink) {
  const problems = [];
  if (report.baseline > ink.clear_rows + 1e-6) problems.push(`a rock needs ${report.baseline.toFixed(1)} rows to dodge`);
  for (const f of report.forks) {
    if (f.needRows > ink.clear_rows + 1e-6) problems.push(`fork at row ${f.y} col ${f.x} needs ${f.needRows.toFixed(1)} rows`);
    else if (ink.mode === 'cone' && f.look > coneHalfWidth(f.needRows, ink) + 0.5 + f.needRows * Math.tan((ink.tilt_degrees * Math.PI) / 180)) problems.push(`fork at row ${f.y} col ${f.x} hides its dead end ${f.look} columns to the side`);
  }
  return { fair: problems.length === 0 && report.entryTraps.length === 0, problems: report.entryTraps.length ? [`${report.entryTraps.length} entry cells already trapped`, ...problems] : problems };
}
