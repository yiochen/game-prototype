import { isRock } from '../../assets/expedition/route/route.js';

/* Issue #25 discharge rules shared by the review page and its Node check (check.mjs).
   Pure functions over chunk rows; nothing here draws.

   A creature chunk (kind "creature") names its creature and the rows where a strike may be live
   (attack_rows, chunk rows counted from the top). For every strike row in that window and every
   cell-aligned strip, fairStrikes() decides whether the strike is
     - meaningful: the strip lies over at least `min_open_columns` of open water, and
     - fair: from EVERY position the ship could hold when the windup starts (and would get through
       the terrain alone from), it can stay out
       of the strip (plus `lane_slack_columns`) while it is live, without touching rock, after a
       `reaction_seconds` delay and at `reach_margin` of its real sideways speed.
   A chunk is accepted when every strike row offers at least `min_choices` fair strips.
   At run time the eel only picks from that table, so it never needs to search terrain. */

export const COLUMNS = 11;

/** Rock lookup with the canyon wall continuing past the side columns (as expedition_book.gd). */
export function rockAt(rows, cx, cy) {
  if (cy < 0 || cy >= rows.length) return false;
  if (cx < 0 || cx >= rows[cy].length) return true;
  return isRock(rows[cy][cx]);
}

/** Signed distance to rock cell (cx, cy)'s rounded square; faces against rock extend into it. */
export function rockDistance(rows, cx, cy, px, py, rules) {
  const inset = rules.rock_inset, corner = rules.rock_corner_radius;
  const x0 = cx + (rockAt(rows, cx - 1, cy) ? -corner : inset), x1 = cx + 1 - (rockAt(rows, cx + 1, cy) ? -corner : inset);
  const y0 = cy + (rockAt(rows, cx, cy - 1) ? -corner : inset), y1 = cy + 1 - (rockAt(rows, cx, cy + 1) ? -corner : inset);
  const qx = Math.abs(px - (x0 + x1) / 2) - ((x1 - x0) / 2 - corner), qy = Math.abs(py - (y0 + y1) / 2) - ((y1 - y0) / 2 - corner);
  return Math.hypot(Math.max(qx, 0), Math.max(qy, 0)) + Math.min(Math.max(qx, qy), 0) - corner;
}

export function collides(rows, x, y, reach, rules) {
  for (let cy = Math.floor(y - reach - 1); cy <= Math.floor(y + reach + 1); cy++) {
    if (cy < 0 || cy >= rows.length) continue;
    for (let cx = Math.floor(x - reach - 1); cx <= Math.floor(x + reach + 1); cx++) {
      if (cx >= 0 && cx < rows[cy].length && rockAt(rows, cx, cy) && rockDistance(rows, cx, cy, x, y, rules) < reach) return true;
    }
  }
  return false;
}

/** Every cell-aligned strip the discharge can choose: { x0, w, centre }. */
export function strips(discharge) {
  const out = [];
  for (const w of discharge.width_columns) for (let x0 = 1; x0 + w <= COLUMNS - 1; x0++) out.push({ x0, w, centre: x0 + w / 2 });
  return out;
}

/** Chase speed once the pursuit ramp is done, in rows per second. */
export const chaseRowsPerSecond = (rules) => rules.forward_rows_per_second * rules.pursuit_speed_multiplier;

/** Strike rows sampled for a chunk: the row the ship is on when the strike goes live. */
export function strikeRows(chunk, rules) {
  const d = rules.discharge, f = d.fairness, fwd = chaseRowsPerSecond(rules), [a, b] = chunk.attack;
  const out = [];
  // The whole live window lies inside attack_rows; the windup starts inside the chunk.
  for (let r = b; r - d.active_seconds * fwd >= a - 1e-6; r -= f.row_step) if (r + d.warn_seconds * fwd <= chunk.rows.length - 0.5) out.push(+r.toFixed(3));
  return out;
}

const LO = 0.4, HI = COLUMNS - 0.4, SUB = 6, SLIDE = 3;

/** Is the strike at chunk row `strike` through `strip` fair, and meaningful? */
export function judge(rows, strike, strip, rules) {
  const d = rules.discharge, f = d.fairness, fwd = chaseRowsPerSecond(rules);
  const open = (() => { let n = 0; for (let x = strip.x0 + 0.05; x < strip.x0 + strip.w; x += 0.1) if (!rockAt(rows, Math.floor(x), Math.floor(strike))) n++; return n * 0.1; })();
  if (open < f.min_open_columns) return { meaningful: false, fair: true };
  const r0 = strike + d.warn_seconds * fwd, end = d.warn_seconds + d.active_seconds + f.reaction_seconds;
  // Positions are spaced so the ship slides exactly SLIDE positions per step at its reduced speed.
  const dt = 1 / (fwd * SUB), steps = Math.ceil(end / dt), STEP = rules.lateral_columns_per_second * f.reach_margin * dt / SLIDE;
  const N = Math.floor((HI - LO) / STEP) + 1, slide = SLIDE;
  const xs = Array.from({ length: N }, (_, i) => LO + i * STEP), half = strip.w / 2 + rules.ship_radius + f.lane_slack_columns;
  const clear = Array.from({ length: steps + 1 }, (_, k) => xs.map((x) => !collides(rows, x, r0 - k * dt * fwd, rules.ship_radius, rules)));
  // Backwards from the end: good[i] = the ship at xs[i] at step k can still come through.
  const survivors = (strike) => {
    let good = clear[steps];
    for (let k = steps - 1; k >= 0; k--) {
      const t = k * dt, live = strike && t >= d.warn_seconds && t <= d.warn_seconds + d.active_seconds, s = t < f.reaction_seconds ? 0 : slide;
      const next = new Array(N).fill(false);
      for (let i = 0; i < N; i++) {
        if (!clear[k][i] || (live && Math.abs(xs[i] - strip.centre) < half)) continue;
        for (let j = Math.max(0, i - s); j <= Math.min(N - 1, i + s); j++) if (good[j]) { next[i] = true; break; }
      }
      good = next;
    }
    return good;
  };
  // Every position that would come through the terrain alone must still come through the strike.
  const terrain = survivors(false), struck = survivors(true);
  const fair = terrain.every((ok, i) => !ok || struck[i]);
  return { meaningful: true, fair };
}

/** { strikes: [{ row, fair: [strip…] }], accepted, problems } for one creature chunk. */
export function analyzeCreatureChunk(chunk, rules) {
  const all = strips(rules.discharge), strikes = [], bad = [];
  for (const row of strikeRows(chunk, rules)) {
    const results = all.map((s) => ({ ...s, ...judge(chunk.rows, row, s, rules) }));
    const fair = results.filter((r) => r.meaningful && r.fair);
    strikes.push({ row, results, fair });
    if (fair.length < rules.discharge.fairness.min_choices) bad.push(row);
  }
  const problems = [];
  if (!strikes.length) problems.push('attack_rows leave no room for a strike');
  if (bad.length) problems.push(`fewer than ${rules.discharge.fairness.min_choices} fair strips at rows ${Math.min(...bad)}–${Math.max(...bad)}`);
  return { strikes, accepted: problems.length === 0, problems };
}
