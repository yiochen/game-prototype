// Issue #22 review: lateral currents, a travel boost and an optional portal
// into a safe bonus passage, on top of the issue #21 expedition.
//
// Route generation and scene composition come from the shared route module
// (route.js). Feature chunks are ordinary designer chunks with two extra
// layers (`currents`, `features`) that route.js ignores. Rules here mirror
// the Godot expedition book so the approved behaviour ports directly; balance
// lives in balance.json.
import manifest from '../../assets/expedition/v1/manifest.json';
import v2Library from '../../assets/expedition/v2/library.json';
import v3Library from '../../assets/expedition/v3/library.json';
import originalSet from '../underwater-kit-preview/original-set.json';
import rules from './balance.json';
import { analyzeLibrary, assemble, chunkFromMap, composeScene, generate, isRock, mulberry32 } from '../../assets/expedition/route/route.js';

const contentChunks = import.meta.glob('../../godot/content/expedition/chunks/*.json', { eager: true, import: 'default' });
const productionUrls = import.meta.glob('../../assets/production/sprites/{floor-underwater,decor-background-rock,decor-foreground-rock,boulder-underwater,column-broken,decor-ruin-fragment,crate-wood,decor-foreground-coral,decor-midground-coral,decor-kelp,decor-starfish,decor-background-wreck,decor-background-fish,decor-light-shafts,submarine-yellow}/*.png', { eager: true, query: '?url', import: 'default' });
const v2Urls = import.meta.glob('../../assets/expedition/v2/sprites/*/*.png', { eager: true, query: '?url', import: 'default' });
const v3Urls = import.meta.glob('../../assets/expedition/v3/sprites/*/*.png', { eager: true, query: '?url', import: 'default' });
const kitUrls = import.meta.glob('../../assets/expedition/v1/sprites/{bed,gold}-*.png', { eager: true, query: '?url', import: 'default' });

const load = (src) => new Promise((resolve, reject) => { const image = new Image(); image.onload = () => resolve(image); image.onerror = () => reject(new Error(`Missing ${src}`)); image.src = src; });

// ------------------------------------------------------------ art
const kit = manifest.sprites;
const kitImages = {};
await Promise.all(Object.entries(kit).filter(([name]) => /^(bed|gold)-/.test(name)).map(async ([name, entry]) => {
  kitImages[name] = await load(kitUrls[`../../assets/expedition/v1/${entry.image}`]);
}));
const PX = manifest.cell_pixels;
function sprite(ctx, name, x, y, cell) {
  const entry = kit[name]; const s = cell / PX;
  ctx.drawImage(kitImages[name], x - entry.origin[0] * s, y - entry.origin[1] * s, entry.size[0] * s, entry.size[1] * s);
}

// original-set already contains the production objects and the v2 variants; v3 adds the portal ring.
const objects = { ...originalSet.objects };
for (const o of v3Library.objects) objects[o.id] = { ...o, clips: o.clips.map((c) => ({ ...c, directions: Object.fromEntries(Object.entries(c.directions).map(([d, v]) => [d, { ...v, image: `assets/expedition/v3/${v.image}` }])) })) };
const urlFor = (image) => productionUrls[`../../${image}`] ?? v2Urls[`../../${image}`] ?? v3Urls[`../../${image}`];
const clipImages = {};
await Promise.all([...new Set(Object.values(objects).flatMap((o) => o.clips.flatMap((c) => Object.values(c.directions).map((d) => d.image))))]
  .filter(urlFor).map(async (image) => { clipImages[image] = await load(urlFor(image)); }));

/** Draw a clip frame with its ground root at the footprint centre (or at `x, y` when `atRoot`). */
function piece(ctx, id, dir, x, y, cell, time, { salt = 0, clip = 0, atRoot = false, scale = 1 } = {}) {
  const o = objects[id]; const c = o.clips[clip] ?? o.clips[0]; const d = c.directions[dir] ?? c.directions.S; const s = (cell / 128) * scale;
  const frame = c.frames > 1 ? c.frameOrder[Math.floor(time * c.fps + salt) % c.frameOrder.length] : 0;
  const [sx, sy, sw, sh] = d.rects[frame];
  const [fw, fh] = o.footprint ?? [1, 1];
  const rx = atRoot ? x : x + fw * 0.5 * cell, ry = atRoot ? y : y + fh * 0.5 * cell;
  ctx.drawImage(clipImages[d.image], sx, sy, sw, sh, rx - o.root[0] * s, ry - o.root[1] * s, o.frameSize[0] * s, o.frameSize[1] * s);
}

// HUD hull icon: the hull's middle band, like the native HUD.
{
  const sub = objects['submarine-yellow'].clips[0].directions.S, [sx, sy, sw, sh] = sub.rects[0];
  const canvas = document.createElement('canvas'); canvas.width = sw * 0.5; canvas.height = sh * 0.4;
  canvas.getContext('2d').drawImage(clipImages[sub.image], sx + sw * 0.25, sy + sh * 0.44, sw * 0.5, sh * 0.4, 0, 0, canvas.width, canvas.height);
  document.getElementById('phone').style.setProperty('--ship', `url(${canvas.toDataURL()})`);
}

// ------------------------------------------------------------ worlds
// A world is one scrolling grid: the main route, or a bonus passage.
const docs = {};
const sources = [];
for (const [file, doc] of Object.entries(contentChunks)) {
  const id = file.split('/').pop().slice(0, -5); docs[id] = doc; sources.push(chunkFromMap(doc, id));
}
const { chunks: library, problems } = analyzeLibrary(sources);
if (Object.keys(problems).length) console.warn('Chunks left out:', problems);

function makeWorld(grid, seed, extra = {}) {
  const scene = composeScene(grid, v2Library.objects, seed);
  const byRow = Array.from({ length: scene.rows }, () => []);
  for (const o of scene.objects) byRow[o.y].push(o);
  const c = 24, shadow = new OffscreenCanvas((scene.columns + 4) * c, (scene.rows + 4) * c), sctx = shadow.getContext('2d');
  sctx.filter = 'blur(9px)'; sctx.fillStyle = '#04174a';
  for (const b of scene.collision) sctx.fillRect((b.x + 2) * c - 2, (b.y + 2) * c - 2, c + 4, c + 4);
  const fish = Array.from({ length: Math.ceil(scene.rows / 13) }, (_, i) => { const r = mulberry32(seed * 31 + i); return { y: 4 + i * 13 + r() * 6, speed: 0.25 + r() * 0.25, dir: i % 2 ? -1 : 1, phase: r() * 20 }; });
  const world = { grid, scene, byRow, shadow: { canvas: shadow, c }, fish, currents: new Map(), boosts: [], portals: [], streaks: [], ...extra };
  return world;
}

/** Current cells → soft seabed wash and the drifting streaks that show direction and speed. */
function dressCurrents(world, seed) {
  const { scene } = world, c = 24;
  const wash = new OffscreenCanvas((scene.columns + 4) * c, (scene.rows + 4) * c), wctx = wash.getContext('2d');
  wctx.filter = 'blur(6px)'; wctx.fillStyle = '#d6fbff';
  for (const [key] of world.currents) { const [x, y] = key.split(',').map(Number); wctx.fillRect((x + 2) * c, (y + 2) * c, c, c); }
  world.wash = { canvas: wash, c };
  const rng = mulberry32(seed * 13 + 5);
  for (let y = 0; y < scene.rows; y++) {
    let x = 0;
    while (x < scene.columns) {
      const dir = world.currents.get(`${x},${y}`);
      if (!dir) { x++; continue; }
      let b = x; while (world.currents.get(`${b + 1},${y}`) === dir) b++;
      const width = b - x + 1;
      for (let n = 0; n < Math.max(1, Math.round(width * 1.2)); n++) world.streaks.push({ a: x, b: b + 1, y: y + 0.12 + rng() * 0.76, dir, phase: rng() * width, len: 0.55 + rng() * 0.5, wave: rng() * 6, head: rng() < 0.6 });
      x = b + 1;
    }
  }
}

function buildMain(seed) {
  const sequence = generate(seed, library, { slots: rules.plan });
  const { rows: grid, spans } = assemble(sequence);
  const world = makeWorld(grid, seed, { kind: 'main', spans, sequence });
  for (const span of spans) {
    for (const p of docs[span.id].placements ?? []) {
      const y = span.y0 + p.y;
      if (p.layer === 'currents') world.currents.set(`${p.x},${y}`, p.object === 'current-east' ? 1 : -1);
      if (p.layer === 'features' && p.object === 'boost') world.boosts.push({ id: world.boosts.length, x: p.x + 0.5, y: y + 0.5 });
      if (p.layer === 'features' && p.object === 'portal-ring') {
        // Spans run start-first: rejoin at the entry row of the chunk after the skipped one(s).
        const at = spans.indexOf(span), rejoin = spans[Math.min(spans.length - 1, at + 1 + rules.passage_rejoin_skips_chunks)];
        const ry = rejoin.y1 + 0.5;
        world.portals.push({ id: world.portals.length, x: p.x + 0.5, y: y + 0.5, rejoin: { x: world.scene.autopilot[rejoin.y1], y: ry } });
      }
    }
  }
  dressCurrents(world, seed);
  // The finish chunk stands in for the creature encounter: boosts end at its edge.
  const finish = spans.find((s) => s.kind === 'finish');
  world.encounterEdge = finish ? finish.y1 + 1 : 0;
  return world;
}

/** Bonus passage: a winding three-wide channel lined with salvage; the whole width carries the ship forward. */
function buildPassage(seed, portalId) {
  const rows = rules.passage_rows, rng = mulberry32(seed * 101 + portalId * 7 + 3);
  const phase = rng() * 6, amp = 1.6 + rng() * 0.6;
  const centre = (y) => 5.5 + amp * Math.sin(y * 0.24 + phase) * Math.min(1, Math.min(y, rows - 1 - y) / 4);
  const grid = [];
  for (let y = 0; y < rows; y++) {
    const c = centre(y), open = y < 3 || y > rows - 4 ? 2 : 1;
    let row = '';
    for (let x = 0; x < 11; x++) {
      const inside = Math.abs(x + 0.5 - c) <= open + 0.5;
      const gold = inside && Math.abs(x + 0.5 - c) < 0.5 && y > 3 && y < rows - 4 && y % rules.passage_gold_every_rows === 0;
      const decor = inside && !gold && rng() < 0.12;
      row += inside ? (gold ? '$' : decor ? ',' : '.') : '#';
    }
    grid.push(row);
  }
  const world = makeWorld(grid, seed * 7 + portalId + 11, { kind: 'passage', centre });
  // Forward flow lines across the channel: the strong current the ride follows.
  world.flow = Array.from({ length: rows * 2 }, () => ({ y: rng() * rows, dx: (rng() - 0.5) * 2.4, len: 0.6 + rng() * 0.6, head: rng() < 0.5 }));
  return world;
}

// ------------------------------------------------------------ run state
// Mirrors the saved Godot run, plus the #22 fields: boost (seconds left),
// boosts_taken, portals_used and passage {portal, y, x, collected}.
let main, passage = null;
let run, transition = null;
const half = [rules.ship_collider[0] / 2, rules.ship_collider[1] / 2];
// The ride starts and ends a few rows inside the passage so both whirlpools sit clear of the HUD and arrows.
const PASSAGE_IN = 3.2, PASSAGE_OUT = 3.2;

function newRun(seed) {
  main = buildMain(seed); passage = null; transition = null;
  const startY = main.scene.rows - 0.5;
  run = { seed, y: startY, x: main.scene.autopilot[main.scene.rows - 1], steer: 0, vx: 0, hull: rules.hull_max, salvage: 0, collected: [],
    protection: 0, boost: 0, boosts_taken: [], portals_used: [], passage: null, paused: false, impacts: 0 };
  camX = run.x; particles.length = 0; vents.clear();
  seedInput.value = String(seed);
  const url = new URL(location.href); url.searchParams.set('seed', String(seed)); history.replaceState(null, '', url);
  chunkList.replaceChildren(...main.spans.map((s) => { const li = document.createElement('li'); li.textContent = s.id; li.dataset.y0 = s.y0; li.dataset.y1 = s.y1; li.classList.toggle('feature', FEATURE_KINDS.includes(s.kind)); return li; }));
  hideOverlays(); flash = null; outflow = null;
}

const world = () => (run.passage ? passage : main);
const FEATURE_KINDS = ['current', 'portal', 'boost'];

function overlaps(grid, x, y) {
  for (let cy = Math.floor(y - half[1]); cy <= Math.floor(y + half[1]); cy++) {
    if (cy < 0 || cy >= grid.length) continue;
    for (let cx = Math.floor(x - half[0]); cx <= Math.floor(x + half[0]); cx++) if (cx >= 0 && cx < 11 && isRock(grid[cy][cx])) return true;
  }
  return false;
}
const moveToward = (v, to, d) => (Math.abs(to - v) <= d ? to : v + Math.sign(to - v) * d);
const currentAt = (w, x, y) => w.currents.get(`${Math.floor(x)},${Math.floor(y)}`) ?? 0;

/** One rules step (≤ 0.05 s). Returns presentation events. */
function step(dt) {
  const events = [];
  if (run.paused || transition) return events;
  const w = world();
  run.protection = Math.max(0, run.protection - dt);
  if (run.passage) {
    // Safe ride: a strong current carries the ship along the channel; nothing damages it.
    const p = run.passage;
    p.y -= rules.passage_forward_rows_per_second * dt;
    if (rideMode() === 'auto') { p.x += (w.centre(p.y) - p.x) * Math.min(1, dt * 6); run.vx = 0; }
    else {
      run.vx = moveToward(run.vx, run.steer * rules.lateral_columns_per_second, rules.lateral_acceleration * dt);
      // The channel walls are soft: the current eases the ship back between them.
      p.x += run.vx * dt; const c = w.centre(p.y); p.x = Math.max(c - 1.1, Math.min(c + 1.1, p.x));
    }
    w.scene.pickups.forEach((g, i) => {
      if (p.collected.includes(i) || Math.abs(g.x - p.x) > rules.pickup_radius || Math.abs(g.y - p.y) > rules.pickup_radius) return;
      p.collected.push(i); run.salvage += rules.salvage_per_pickup; events.push({ type: 'pickup', x: g.x, y: g.y });
    });
    if (p.y <= PASSAGE_OUT) { transition = { kind: 'exit', t: 0 }; events.push({ type: 'exit' }); }
    return events;
  }
  const boosted = run.boost > 0;
  run.y -= rules.forward_rows_per_second * (boosted ? rules.boost_forward_multiplier : 1) * dt;
  if (boosted) {
    run.boost = Math.max(0, run.boost - dt);
    // Ends before the encounter: the boost never carries into the finish.
    if (run.y <= w.encounterEdge + 0.5) run.boost = 0;
    if (run.boost === 0) events.push({ type: 'boost_end' });
  }
  run.vx = moveToward(run.vx, run.steer * rules.lateral_columns_per_second, rules.lateral_acceleration * dt);
  // The current adds to steering; letting go removes only the player's part.
  const push = currentAt(w, run.x, run.y) * rules.current_columns_per_second;
  run.x += (run.vx + push) * dt;
  if (run.x < 0.4 || run.x > 10.6) { run.x = Math.max(0.4, Math.min(10.6, run.x)); run.vx = 0; }
  w.scene.pickups.forEach((g, i) => {
    if (run.collected.includes(i) || Math.abs(g.x - run.x) > rules.pickup_radius || Math.abs(g.y - run.y) > rules.pickup_radius) return;
    run.collected.push(i); run.salvage += rules.salvage_per_pickup; events.push({ type: 'pickup', x: g.x, y: g.y });
  });
  for (const b of w.boosts) {
    if (run.boosts_taken.includes(b.id) || Math.abs(b.x - run.x) > rules.boost_radius || Math.abs(b.y - run.y) > rules.boost_radius) continue;
    if (run.y <= w.encounterEdge + 0.5) continue;
    run.boosts_taken.push(b.id); run.boost = rules.boost_seconds; events.push({ type: 'boost', x: b.x, y: b.y });
  }
  for (const p of w.portals) {
    if (run.portals_used.includes(p.id) || Math.abs(p.x - run.x) > rules.portal_radius || Math.abs(p.y - run.y) > rules.portal_radius) continue;
    // Entering commits: the portal is spent before the ride, so a save never repeats it.
    run.portals_used.push(p.id); run.boost = 0;
    const ride = passageFor(p.id), startY = ride.scene.rows - PASSAGE_IN;
    run.passage = { portal: p.id, y: startY, x: ride.centre(startY), collected: [] };
    run.passage.entry = { x: p.x, y: p.y };
    transition = { kind: 'enter', t: 0, from: { x: p.x, y: p.y } };
    events.push({ type: 'enter' });
    return events;
  }
  if (overlaps(w.grid, run.x, run.y)) {
    if (run.boost > 0) { if (run.protection <= 0) { run.protection = 0.3; events.push({ type: 'shield', x: run.x, y: run.y }); } }
    else if (run.protection <= 0) {
      run.hull = Math.max(0, run.hull - rules.impact_damage); run.protection = rules.hit_protection_seconds; run.impacts++;
      events.push({ type: 'impact' });
      if (run.hull <= 0) { events.push({ type: 'ended', outcome: 'hull_depleted' }); return events; }
    }
  }
  if (run.y <= 0.5) events.push({ type: 'ended', outcome: 'complete' });
  return events;
}

function passageFor(portalId) {
  if (!passage || passage.portal !== portalId) { passage = buildPassage(run.seed, portalId); passage.portal = portalId; }
  return passage;
}

/** Passage end: rejoin the main route one chunk on, through an outflow swirl. */
function rejoin() {
  const p = main.portals[run.passage.portal];
  run.x = p.rejoin.x; run.y = p.rejoin.y; run.vx = 0;
  run.passage = null; camX = run.x; particles.length = 0;
  outflow = { x: run.x, y: run.y, t: 0 };
}

// ------------------------------------------------------------ particles
const bubbleSprite = (() => {
  const size = 64, canvas = new OffscreenCanvas(size, size), ctx = canvas.getContext('2d'), r = size / 2 - 2;
  const fill = ctx.createRadialGradient(size * 0.45, size * 0.42, r * 0.1, size / 2, size / 2, r);
  fill.addColorStop(0, 'rgba(210, 248, 255, 0.08)'); fill.addColorStop(0.75, 'rgba(190, 240, 255, 0.22)'); fill.addColorStop(1, 'rgba(235, 252, 255, 0.85)');
  ctx.fillStyle = fill; ctx.beginPath(); ctx.arc(size / 2, size / 2, r, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = 'rgba(255, 255, 255, 0.95)'; ctx.beginPath(); ctx.ellipse(size * 0.36, size * 0.33, r * 0.26, r * 0.17, -0.6, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = 'rgba(255, 255, 255, 0.5)'; ctx.beginPath(); ctx.arc(size * 0.64, size * 0.68, r * 0.08, 0, Math.PI * 2); ctx.fill();
  return canvas;
})();
const particles = [];
function emitBubble(x, y, { vx = 0, vy = 0, r = 0.05, life = 2, rise = 0.4, drag = 2.2 } = {}) {
  particles.push({ kind: 'bubble', x, y, vx, vy, r, life, age: 0, rise, drag, grow: 0.25 + Math.random() * 0.25, wob: 0.03 + Math.random() * 0.05, freq: 3 + Math.random() * 4, phase: Math.random() * 6.3 });
}
function emitSpark(x, y, color = '#ffe58a') {
  const a = Math.random() * Math.PI * 2, s = 0.6 + Math.random() * 1.4;
  particles.push({ kind: 'spark', x, y, color, vx: Math.cos(a) * s, vy: Math.sin(a) * s - 0.3, r: 0.035 + Math.random() * 0.03, life: 0.45 + Math.random() * 0.3, age: 0, drag: 3.5 });
}
function emitSpeedLine(x, y) { particles.push({ kind: 'line', x, y, vx: 0, vy: 7 + Math.random() * 3, len: 0.5 + Math.random() * 0.5, life: 0.35, age: 0, drag: 0 }); }
function stepParticles(dt, w) {
  for (const p of particles) {
    p.age += dt;
    const k = Math.exp(-p.drag * dt);
    p.vx *= k; p.vy *= k;
    if (p.kind === 'bubble') {
      p.vy -= p.rise * dt * 1.6;
      // Bubbles caught in a current drift with it.
      const push = currentAt(w, p.x, p.y) * rules.current_columns_per_second;
      if (push) p.vx += (push - p.vx) * Math.min(1, dt * 3);
    }
    p.x += p.vx * dt; p.y += p.vy * dt;
  }
  for (let i = particles.length - 1; i >= 0; i--) if (particles[i].age >= particles[i].life) particles.splice(i, 1);
}
function drawParticles(ctx, ox, oy, cell) {
  for (const p of particles) {
    const t = p.age / p.life;
    if (p.kind === 'bubble') {
      const r = p.r * (1 + p.grow * t) * cell, x = ox + (p.x + Math.sin(p.age * p.freq + p.phase) * p.wob) * cell, y = oy + p.y * cell;
      ctx.globalAlpha = Math.min(1, p.age * 8) * (1 - t * t);
      ctx.drawImage(bubbleSprite, x - r, y - r, r * 2, r * 2);
    } else if (p.kind === 'line') {
      ctx.globalAlpha = 0.7 * Math.sin(Math.PI * t); ctx.strokeStyle = '#e8fdff'; ctx.lineWidth = Math.max(1.5, cell * 0.035); ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(ox + p.x * cell, oy + p.y * cell); ctx.lineTo(ox + p.x * cell, oy + (p.y - p.len) * cell); ctx.stroke();
    } else {
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = 1 - t;
      ctx.fillStyle = p.color; ctx.beginPath(); ctx.arc(ox + p.x * cell, oy + p.y * cell, p.r * cell * (1 - t * 0.5), 0, Math.PI * 2); ctx.fill(); ctx.restore();
    }
  }
  ctx.globalAlpha = 1;
}
const vents = new Map();
function stepVents(dt, w, top, bottom) {
  for (const v of w.scene.vents) {
    if (v.y < top - 1 || v.y > bottom + 1) continue;
    const key = `${w.kind}:${v.x},${v.y}`;
    const s = vents.get(key) ?? { wait: Math.random() * 3, left: 0, gap: 0 };
    if (s.left > 0) {
      s.gap -= dt;
      if (s.gap <= 0) { emitBubble(v.x + (Math.random() - 0.5) * 0.2, v.y, { vy: -0.2, r: 0.025 + Math.random() * 0.035, life: 2.2 + Math.random(), rise: 0.35 }); s.left--; s.gap = 0.08 + Math.random() * 0.12; }
    } else if ((s.wait -= dt) <= 0) { s.left = 3 + Math.floor(Math.random() * 5); s.wait = 1.5 + Math.random() * 2.5; }
    vents.set(key, s);
  }
}

// ------------------------------------------------------------ feature drawing
/** Drifting flow lines: tapered streaks at the current's real speed, some with a chevron head. */
function drawStreaks(ctx, w, ox, oy, cell, time, top, bottom) {
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (const s of w.streaks) {
    if (s.y < top - 1 || s.y > bottom + 1) continue;
    const width = s.b - s.a, travel = ((s.phase + time * rules.current_columns_per_second) % width + width) % width;
    const head = s.dir > 0 ? s.a + travel : s.b - travel;
    const u = travel / width, alpha = Math.sin(Math.PI * u) ** 0.7;
    const tail = head - s.dir * s.len;
    const y = oy + (s.y + Math.sin(time * 2 + s.wave + head) * 0.04) * cell;
    const grad = ctx.createLinearGradient(ox + tail * cell, 0, ox + head * cell, 0);
    grad.addColorStop(0, 'rgba(240, 254, 255, 0)'); grad.addColorStop(1, `rgba(240, 254, 255, ${0.95 * alpha})`);
    ctx.strokeStyle = grad; ctx.lineWidth = Math.max(2, cell * 0.055);
    ctx.beginPath(); ctx.moveTo(ox + tail * cell, y + cell * 0.03); ctx.quadraticCurveTo(ox + (tail + head) / 2 * cell, y - cell * 0.05, ox + head * cell, y); ctx.stroke();
    if (s.head) {
      const hx = ox + head * cell, k = cell * 0.11;
      ctx.strokeStyle = `rgba(240, 254, 255, ${0.95 * alpha})`; ctx.lineWidth = Math.max(2, cell * 0.06);
      ctx.beginPath(); ctx.moveTo(hx - s.dir * k, y - k); ctx.lineTo(hx, y); ctx.lineTo(hx - s.dir * k, y + k); ctx.stroke();
    }
  }
  ctx.restore();
}

/** Passage current: flow lines rushing forward (up the screen) between the walls. */
function drawFlow(ctx, w, ox, oy, cell, time, top, bottom) {
  const rows = w.scene.rows, speed = rules.passage_forward_rows_per_second * 1.7;
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (const f of w.flow) {
    const y = ((f.y - time * speed) % rows + rows) % rows;
    if (y < top - 1 || y > bottom + 1 || y < 1 || y > rows - 2) continue;
    const x = w.centre(y) + f.dx, alpha = 0.8 * Math.min(1, (y - 1) / 2, (rows - 2 - y) / 2);
    const grad = ctx.createLinearGradient(0, oy + (y + f.len) * cell, 0, oy + y * cell);
    grad.addColorStop(0, 'rgba(240, 254, 255, 0)'); grad.addColorStop(1, `rgba(240, 254, 255, ${alpha})`);
    ctx.strokeStyle = grad; ctx.lineWidth = Math.max(2, cell * 0.05);
    ctx.beginPath(); ctx.moveTo(ox + x * cell, oy + (y + f.len) * cell); ctx.lineTo(ox + x * cell, oy + y * cell); ctx.stroke();
    if (f.head) {
      const k = cell * 0.1; ctx.strokeStyle = `rgba(240, 254, 255, ${alpha})`;
      ctx.beginPath(); ctx.moveTo(ox + x * cell - k, oy + y * cell + k); ctx.lineTo(ox + x * cell, oy + y * cell); ctx.lineTo(ox + x * cell + k, oy + y * cell + k); ctx.stroke();
    }
  }
  ctx.restore();
}

/** Whirlpool seen from above: a dark core with bright spiral arms turning inward. */
function drawSwirl(ctx, x, y, r, time, strength = 1) {
  if (r <= 0.5 || strength <= 0) return;
  ctx.save(); ctx.translate(x, y);
  const core = ctx.createRadialGradient(0, 0, 0, 0, 0, r);
  core.addColorStop(0, `rgba(3, 26, 66, ${0.95 * strength})`); core.addColorStop(0.55, `rgba(12, 92, 150, ${0.75 * strength})`); core.addColorStop(1, 'rgba(90, 220, 255, 0)');
  ctx.fillStyle = core; ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill();
  ctx.lineCap = 'round';
  for (let arm = 0; arm < 3; arm++) {
    ctx.beginPath();
    for (let i = 0; i <= 24; i++) {
      const u = i / 24, a = arm * (Math.PI * 2 / 3) - time * 2.6 + u * 3.2, rr = r * (0.95 - u * 0.8);
      const px = Math.cos(a) * rr, py = Math.sin(a) * rr;
      i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
    }
    ctx.strokeStyle = `rgba(190, 250, 255, ${0.8 * strength})`; ctx.lineWidth = Math.max(1.5, r * 0.11); ctx.stroke();
  }
  ctx.restore();
}

/** Shield pickup: a shield emblem with a cool halo and a pulsing ring (rules call it the boost). */
function drawBoost(ctx, x, y, cell, time, salt = 0) {
  const bob = Math.sin(time * 2.2 + salt) * 0.05 * cell, r = cell * 0.3;
  const cy = y - cell * 0.12 + bob;
  const pulse = (time * 0.9 + salt) % 1;
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  const halo = ctx.createRadialGradient(x, cy, 0, x, cy, cell * 0.62);
  halo.addColorStop(0, 'rgba(110, 240, 255, 0.45)'); halo.addColorStop(1, 'rgba(60, 200, 255, 0)');
  ctx.fillStyle = halo; ctx.beginPath(); ctx.arc(x, cy, cell * 0.62, 0, Math.PI * 2); ctx.fill();
  ctx.globalCompositeOperation = 'source-over';
  ctx.strokeStyle = `rgba(200, 252, 255, ${0.7 * (1 - pulse)})`; ctx.lineWidth = Math.max(1.5, cell * 0.03);
  ctx.beginPath(); ctx.arc(x, cy, r * (1 + pulse * 0.9), 0, Math.PI * 2); ctx.stroke();
  // Shield emblem: navy-rimmed heater shield with a cool blue face, white inner rim and a highlight.
  const shield = (k) => {
    const w = r * 0.95 * k, h = r * 1.15 * k, top = cy - h * 0.82;
    ctx.beginPath(); ctx.moveTo(x, top + h * 0.08);
    ctx.quadraticCurveTo(x + w * 0.5, top - h * 0.06, x + w, top + h * 0.06);
    ctx.bezierCurveTo(x + w * 1.02, cy + h * 0.25, x + w * 0.62, cy + h * 0.72, x, cy + h * 0.98);
    ctx.bezierCurveTo(x - w * 0.62, cy + h * 0.72, x - w * 1.02, cy + h * 0.25, x - w, top + h * 0.06);
    ctx.quadraticCurveTo(x - w * 0.5, top - h * 0.06, x, top + h * 0.08); ctx.closePath();
  };
  ctx.lineJoin = 'round';
  shield(1); ctx.fillStyle = '#0d3f78'; ctx.fill(); ctx.strokeStyle = '#082a52'; ctx.lineWidth = Math.max(2, cell * 0.04); ctx.stroke();
  const face = ctx.createLinearGradient(x - r, cy - r, x + r, cy + r);
  face.addColorStop(0, '#8fe3ff'); face.addColorStop(0.45, '#2f9be8'); face.addColorStop(1, '#1559b8');
  shield(0.8); ctx.fillStyle = face; ctx.fill(); ctx.strokeStyle = 'rgba(255, 255, 255, 0.95)'; ctx.lineWidth = Math.max(1.5, cell * 0.03); ctx.stroke();
  // Left-half sheen, as on the concept HUD shield.
  ctx.save(); shield(0.8); ctx.clip(); ctx.fillStyle = 'rgba(255, 255, 255, 0.28)'; ctx.fillRect(x - r * 1.2, cy - r * 1.4, r * 1.2, r * 2.8); ctx.restore();
  ctx.fillStyle = 'rgba(255, 255, 255, 0.9)'; ctx.beginPath(); ctx.ellipse(x - r * 0.38, cy - r * 0.45, r * 0.12, r * 0.07, -0.7, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}

/** Boosted hull: a shield bubble whose bright rim drains with the time left. */
function drawShield(ctx, x, y, cell, fraction, time, bump) {
  const r = cell * (0.66 + bump * 0.08), cy = y - cell * 0.28;
  ctx.save();
  const fill = ctx.createRadialGradient(x, cy, r * 0.5, x, cy, r);
  fill.addColorStop(0, 'rgba(160, 245, 255, 0.05)'); fill.addColorStop(0.85, 'rgba(160, 245, 255, 0.22)'); fill.addColorStop(1, 'rgba(220, 253, 255, 0.5)');
  ctx.fillStyle = fill; ctx.beginPath(); ctx.arc(x, cy, r, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = 'rgba(220, 253, 255, 0.35)'; ctx.lineWidth = Math.max(1.5, cell * 0.03); ctx.stroke();
  ctx.strokeStyle = `rgba(240, 255, 255, ${0.8 + 0.2 * Math.sin(time * 12)})`; ctx.lineWidth = Math.max(2.5, cell * 0.06); ctx.lineCap = 'round';
  ctx.beginPath(); ctx.arc(x, cy, r, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * fraction); ctx.stroke();
  ctx.restore();
}

// ------------------------------------------------------------ world drawing
function drawWorld(ctx, w, width, height, { cell, topRow, time, ship, shipScale = 1, shipSpin = 0, camX, grid = false, collected, boostsTaken = [], portalsUsed = [], shield = null }) {
  const { scene } = w;
  const ox = width / 2 - camX * cell, oy = -topRow * cell;
  const top = Math.max(0, Math.floor(topRow) - 1), bottom = Math.min(scene.rows - 1, Math.ceil(topRow + height / cell) + 3);
  ctx.fillStyle = '#0b2f63'; ctx.fillRect(0, 0, width, height);
  for (let y = top; y <= bottom; y++) for (let x = 0; x < scene.columns; x++) piece(ctx, 'floor-underwater', 'S', ox + x * cell, oy + y * cell, cell + 0.5, time);
  if (w.kind === 'passage') {
    // Same seabed, deeper water: the passage reads as a sheltered grotto, not a new biome.
    ctx.fillStyle = 'rgba(22, 34, 110, 0.32)'; ctx.fillRect(0, 0, width, height);
  }
  ctx.strokeStyle = 'rgba(190, 245, 255, 0.22)'; ctx.lineWidth = Math.max(1, cell / 60); ctx.beginPath();
  for (let x = 0; x <= scene.columns; x++) { ctx.moveTo(ox + x * cell, oy + top * cell); ctx.lineTo(ox + x * cell, oy + (bottom + 1) * cell); }
  for (let y = top; y <= bottom + 1; y++) { ctx.moveTo(ox, oy + y * cell); ctx.lineTo(ox + scene.columns * cell, oy + y * cell); }
  ctx.stroke();
  if (w.wash) { const k = cell / w.wash.c; ctx.globalAlpha = 0.42 + 0.06 * Math.sin(time * 1.7); ctx.drawImage(w.wash.canvas, ox - 2 * cell, oy - 2 * cell, w.wash.canvas.width * k, w.wash.canvas.height * k); ctx.globalAlpha = 1; }
  const { canvas: shadow, c } = w.shadow, k = cell / c;
  ctx.globalAlpha = 0.55; ctx.drawImage(shadow, ox - 2 * cell + cell * 0.1, oy - 2 * cell + cell * 0.16, shadow.width * k, shadow.height * k); ctx.globalAlpha = 1;
  for (const f of w.fish) {
    const span = scene.columns + 4, head = ((f.phase + time * f.speed) % span + span) % span - 2;
    piece(ctx, 'decor-background-fish', f.dir > 0 ? 'E' : 'W', ox + (f.dir > 0 ? head : scene.columns - head) * cell, oy + f.y * cell, cell, time, { atRoot: true, salt: f.phase * 7 });
  }
  for (const d of scene.seabed) if (d.y >= top && d.y <= bottom) piece(ctx, d.id, d.dir, ox + (d.x + 0.5) * cell, oy + (d.y + 0.5) * cell, cell, time, { atRoot: true, scale: d.scale ?? 1 });
  if (w.kind === 'passage') {
    // Entry and exit whirlpools at the passage ends.
    drawSwirl(ctx, ox + w.centre(scene.rows - PASSAGE_IN) * cell, oy + (scene.rows - PASSAGE_IN) * cell, cell * 0.45, time);
    drawSwirl(ctx, ox + w.centre(PASSAGE_OUT) * cell, oy + PASSAGE_OUT * cell, cell * 0.45, -time);
  }
  // Portal: whirlpool inside the sunken stone ring; a used ring is still and dim.
  for (const p of w.portals) {
    if (p.y < top - 1 || p.y > bottom + 1) continue;
    const used = portalsUsed.includes(p.id);
    if (!used) {
      ctx.save(); ctx.globalCompositeOperation = 'lighter';
      const glow = ctx.createRadialGradient(ox + p.x * cell, oy + p.y * cell, 0, ox + p.x * cell, oy + p.y * cell, cell * 0.9);
      glow.addColorStop(0, `rgba(90, 230, 255, ${0.35 + 0.12 * Math.sin(time * 3)})`); glow.addColorStop(1, 'rgba(90, 230, 255, 0)');
      ctx.fillStyle = glow; ctx.beginPath(); ctx.arc(ox + p.x * cell, oy + p.y * cell, cell * 0.9, 0, Math.PI * 2); ctx.fill(); ctx.restore();
      drawSwirl(ctx, ox + p.x * cell, oy + p.y * cell, cell * 0.36, time);
    } else {
      ctx.fillStyle = 'rgba(4, 30, 70, 0.45)'; ctx.beginPath(); ctx.ellipse(ox + p.x * cell, oy + p.y * cell, cell * 0.3, cell * 0.3, 0, 0, Math.PI * 2); ctx.fill();
    }
    piece(ctx, 'portal-ring', 'S', ox + p.x * cell, oy + p.y * cell, cell, time, { atRoot: true });
  }
  if (outflow && w.kind === 'main') drawSwirl(ctx, ox + outflow.x * cell, oy + outflow.y * cell, cell * 0.45 * (1 - outflow.t), -time, 1 - outflow.t);
  drawStreaks(ctx, w, ox, oy, cell, time, top, bottom);
  if (w.flow) drawFlow(ctx, w, ox, oy, cell, time, top, bottom);
  if (ship && shipScale > 0.05) {
    ctx.save(); ctx.translate(ox + (ship.x + 0.06) * cell, oy + (ship.y + 0.42) * cell); ctx.scale(shipScale, 0.5 * shipScale);
    const shade = ctx.createRadialGradient(0, 0, 0, 0, 0, cell * 0.62);
    shade.addColorStop(0, 'rgba(4, 30, 70, 0.5)'); shade.addColorStop(0.55, 'rgba(4, 30, 70, 0.3)'); shade.addColorStop(1, 'rgba(4, 30, 70, 0)');
    ctx.fillStyle = shade; ctx.beginPath(); ctx.arc(0, 0, cell * 0.62, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  }
  for (const b of scene.beds) if (b.y >= top && b.y <= bottom) sprite(ctx, b.sprite, ox + b.x * cell, oy + b.y * cell, cell);
  scene.pickups.forEach((p, i) => {
    if (collected.includes(i) || p.y < top || p.y > bottom + 1) return;
    const bob = Math.sin(time * 2.4 + i) * 0.05, gx = ox + p.x * cell, gy = oy + (p.y - 0.15 + bob) * cell, pulse = 0.75 + 0.25 * Math.sin(time * 3.2 + i * 1.7);
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    const halo = ctx.createRadialGradient(gx, gy, 0, gx, gy, cell * 0.62 * pulse);
    halo.addColorStop(0, 'rgba(255, 226, 120, 0.55)'); halo.addColorStop(0.45, 'rgba(255, 190, 60, 0.22)'); halo.addColorStop(1, 'rgba(255, 170, 40, 0)');
    ctx.fillStyle = halo; ctx.beginPath(); ctx.arc(gx, gy, cell * 0.62 * pulse, 0, Math.PI * 2); ctx.fill(); ctx.restore();
    sprite(ctx, `gold-${String(Math.floor(time * 10 + i * 3) % 12).padStart(2, '0')}`, ox + (p.x - 0.75) * cell, oy + (p.y - 0.75 + bob - 0.12) * cell, cell * 1.5);
  });
  for (const b of w.boosts) if (!boostsTaken.includes(b.id) && b.y >= top && b.y <= bottom + 1) drawBoost(ctx, ox + b.x * cell, oy + b.y * cell, cell, time, b.id * 1.3);
  let shipDrawn = !ship;
  const drawShip = () => {
    shipDrawn = true;
    if (shipScale <= 0.05) return;
    const sx = ox + ship.x * cell, sy = oy + ship.y * cell;
    ctx.save(); ctx.translate(sx, sy - cell * 0.25); ctx.rotate(shipSpin); ctx.scale(shipScale, shipScale); ctx.translate(-sx, -(sy - cell * 0.25));
    const hurt = run.protection > 0 && run.boost <= 0 && !run.passage && !transition;
    ctx.globalAlpha = hurt && Math.floor(time * 12) % 2 ? 0.45 : 1;
    piece(ctx, 'submarine-yellow', 'S', sx, sy, cell, time, { atRoot: true, clip: hurt ? 1 : 0 });
    ctx.restore(); ctx.globalAlpha = 1;
    if (shield) drawShield(ctx, sx, sy, cell, shield.fraction, time, shield.bump);
  };
  for (let y = top; y <= bottom; y++) {
    if (!shipDrawn && y >= Math.floor(ship.y) && w.byRow[y].some((o) => o.w > 1)) drawShip();
    for (const o of w.byRow[y]) piece(ctx, o.id, o.dir, ox + o.x * cell, oy + o.y * cell, cell, time, { salt: o.x * 5 + o.y * 3 });
  }
  drawParticles(ctx, ox, oy, cell);
  if (!shipDrawn) drawShip();
  for (const s of scene.shafts) if (s.y >= top - 2 && s.y <= bottom) piece(ctx, s.id, s.dir, ox + s.x * cell, oy + s.y * cell, cell * 1.6, time, { salt: s.y });
  const v = ctx.createRadialGradient(width / 2, height * 0.55, height * 0.3, width / 2, height * 0.55, height * 0.8);
  v.addColorStop(0, 'rgba(3, 20, 60, 0)'); v.addColorStop(1, `rgba(3, 20, 60, ${w.kind === 'passage' ? 0.4 : 0.18})`);
  ctx.fillStyle = v; ctx.fillRect(0, 0, width, height);
  if (grid) {
    ctx.save(); ctx.lineWidth = 2; ctx.strokeStyle = 'rgba(255, 90, 90, 0.85)';
    for (const b of scene.collision) if (b.y >= top && b.y <= bottom) ctx.strokeRect(ox + b.x * cell + 1, oy + b.y * cell + 1, cell - 2, cell - 2);
    ctx.strokeStyle = 'rgba(127, 243, 255, 0.9)';
    for (const [key, dir] of w.currents) { const [x, y] = key.split(',').map(Number); if (y >= top && y <= bottom) { ctx.fillStyle = 'rgba(127, 243, 255, 0.9)'; ctx.font = `${cell * 0.3}px Nunito`; ctx.fillText(dir > 0 ? '→' : '←', ox + (x + 0.35) * cell, oy + (y + 0.6) * cell); } }
    if (ship) { ctx.strokeStyle = '#ffe14d'; ctx.strokeRect(ox + (ship.x - half[0]) * cell, oy + (ship.y - half[1]) * cell, 2 * half[0] * cell, 2 * half[1] * cell); }
    ctx.restore();
  }
  return { ox, oy };
}

// ------------------------------------------------------------ page
const phone = document.getElementById('phone');
const stage = document.getElementById('stage');
const travel = document.getElementById('travel');
const seedInput = document.getElementById('seed');
const frameSelect = document.getElementById('frame');
const chunkList = document.getElementById('chunks');
const zones = { [-1]: document.getElementById('zone-left'), [1]: document.getElementById('zone-right') };
const rideNote = document.getElementById('ride-note');
const scrim = document.getElementById('scrim');
const cards = { paused: document.getElementById('paused-card'), results: document.getElementById('results-card'), countdown: document.getElementById('countdown') };
const rideMode = () => document.querySelector('input[name="ride"]:checked').value;
for (const el of document.querySelectorAll('[data-rule]')) el.textContent = String(rules[el.dataset.rule]);

let size = [390, 844];
function resize() {
  // Wider window and landscape keep the playfield portrait-contained, as the game does.
  const wide = frameSelect.value === 'wide' || frameSelect.value === 'landscape';
  stage.classList.toggle('wide', wide); stage.classList.toggle('landscape', frameSelect.value === 'landscape');
  size = frameSelect.value === 'wide' ? [470, 820] : frameSelect.value === 'landscape' ? [320, 390] : frameSelect.value.split('x').map(Number);
  const dpr = devicePixelRatio || 1;
  travel.width = size[0] * dpr; travel.height = size[1] * dpr;
  phone.style.width = `${size[0]}px`; phone.style.height = `${size[1]}px`;
  phone.style.setProperty('--u', `${size[0] / 390}px`);
  // Arrow geometry matches the native view: bottom corners, clear of the ship's lane.
  const cell = size[0] / 7, edge = Math.min(cell * 1.6, size[1] * 0.18), margin = edge * 0.22;
  phone.style.setProperty('--arrow', `${edge}px`); phone.style.setProperty('--arrow-margin', `${margin}px`); phone.style.setProperty('--arrow-bottom', `${margin * 1.6}px`);
}
frameSelect.addEventListener('change', resize); resize();

// Rounded triangle points, as expedition_view.gd draws them.
function roundedTriangle(side, radius = 50, round = 12) {
  const corners = [0, 1, 2].map((i) => { const a = (side > 0 ? 0 : Math.PI) + i * Math.PI * 2 / 3; return [Math.cos(a) * (radius - round * 2), Math.sin(a) * (radius - round * 2)]; });
  const points = [];
  for (const [cx, cy] of corners) {
    const start = Math.atan2(cy, cx) - Math.PI / 3;
    for (let s = 0; s <= 6; s++) { const a = start + s * Math.PI * 2 / 3 / 6; points.push(`${(cx + Math.cos(a) * round).toFixed(2)},${(cy + Math.sin(a) * round).toFixed(2)}`); }
  }
  return points.join(' ');
}
for (const side of [-1, 1]) for (const poly of zones[side].querySelectorAll('polygon')) poly.setAttribute('points', roundedTriangle(side, 46, 11));

// Steering input: held touches per side and keyboard arrows.
const held = new Map(); const keys = { ArrowLeft: false, ArrowRight: false };
function updateSteer() {
  let value = 0;
  for (const side of held.values()) value += side;
  value += (keys.ArrowRight ? 1 : 0) - (keys.ArrowLeft ? 1 : 0);
  value = Math.max(-1, Math.min(1, value));
  const steerable = !run.paused && !transition && (!run.passage || rideMode() === 'steer');
  run.steer = steerable && !autopilot.checked ? value : 0;
  for (const side of [-1, 1]) zones[side].classList.toggle('down', steerable && value * side > 0);
}
for (const side of [-1, 1]) {
  const zone = zones[side];
  zone.addEventListener('pointerdown', (e) => { zone.setPointerCapture(e.pointerId); held.set(e.pointerId, side); updateSteer(); e.preventDefault(); });
  zone.addEventListener('pointermove', (e) => {
    if (!held.has(e.pointerId)) return;
    // A thumb sliding across the middle switches arrows.
    const r = phone.getBoundingClientRect(); held.set(e.pointerId, e.clientX < r.left + r.width / 2 ? -1 : 1); updateSteer();
  });
  for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) zone.addEventListener(type, (e) => { held.delete(e.pointerId); updateSteer(); });
}
addEventListener('keydown', (e) => { if (e.key in keys && !e.repeat) { keys[e.key] = true; updateSteer(); e.preventDefault(); } if (e.key === 'Escape') pause(); });
addEventListener('keyup', (e) => { if (e.key in keys) { keys[e.key] = false; updateSteer(); } });
addEventListener('blur', () => { held.clear(); keys.ArrowLeft = keys.ArrowRight = false; });

// Pause, countdown, results.
let countdown = 0;
function hideOverlays() { scrim.hidden = true; for (const c of Object.values(cards)) c.hidden = true; }
function show(card) { scrim.hidden = false; for (const [name, c] of Object.entries(cards)) c.hidden = name !== card; }
function pause() {
  if (run.paused || !cards.results.hidden) return;
  run.paused = true; run.steer = 0; run.vx = 0; held.clear(); show('paused'); document.getElementById('resume').focus();
}
document.getElementById('pause').addEventListener('click', pause);
document.getElementById('resume').addEventListener('click', () => { countdown = 3; show('countdown'); });
document.getElementById('return-early').addEventListener('click', () => finish('returned_early'));
document.getElementById('again').addEventListener('click', () => newRun(run.seed));
function finish(outcome) {
  run.paused = true; transition = null;
  const bonus = outcome === 'complete' ? rules.completion_bonus : 0;
  document.getElementById('results-title').textContent = { complete: 'Expedition complete', returned_early: 'Returned early', hull_depleted: 'Hull depleted' }[outcome];
  document.getElementById('r-pickups').textContent = String(run.salvage);
  document.getElementById('r-bonus').textContent = bonus ? `+${bonus}` : '0';
  document.getElementById('r-total').textContent = String(run.salvage + bonus);
  show('results');
}

// Save & reopen: serialise the run as Godot would, drop all live state, restore behind Paused.
const SAVE_KEY = 'sushi-loop-22-run';
document.getElementById('save-reload').addEventListener('click', () => {
  // A save in the middle of a transition lands on its far side; the portal is already spent.
  if (transition?.kind === 'exit') rejoin();
  transition = null;
  const saved = JSON.stringify(run);
  try { localStorage.setItem(SAVE_KEY, saved); } catch { /* storage unavailable: keep the in-memory copy */ }
  const restored = JSON.parse(saved);
  newRun(restored.seed);
  run = { ...restored, paused: false, steer: 0, vx: 0 };
  if (run.passage) passageFor(run.passage.portal);
  camX = run.passage ? run.passage.x : run.x;
  pause();
  flash = { text: 'Saved and reopened', t: 2 };
});
document.getElementById('restart').addEventListener('click', () => newRun(run.seed));
seedInput.addEventListener('change', () => newRun(Math.max(1, Number(seedInput.value) | 0)));
const autopilot = document.getElementById('autopilot');
const gridToggle = document.getElementById('grid');
for (const input of document.querySelectorAll('input[name="ride"]')) input.addEventListener('change', updateSteer);

// Review jumps.
document.querySelectorAll('[data-jump]').forEach((button) => button.addEventListener('click', () => {
  newRun(run.seed);
  const kind = button.dataset.jump;
  const place = (y) => { run.y = y; run.x = main.scene.autopilot[Math.floor(y)]; camX = run.x; };
  if (kind === 'current') { const s = main.spans.find((s) => s.kind === 'current'); place(s.y1 + 2.5); }
  if (kind === 'boost') { const b = main.boosts[0]; place(b.y + 3.2); run.x = b.x; }
  if (kind === 'portal') { const p = main.portals[0]; place(p.y + 4.5); }
  if (kind === 'encounter') { place(main.encounterEdge + 7.5); run.boost = rules.boost_seconds; flash = { text: 'Shield given 7 rows before the encounter', t: 2.5 }; }
  phone.focus?.();
}));

// ------------------------------------------------------------ frame
let camX = 5.5, last = performance.now(), clock = 0, flash = null, outflow = null, shieldBump = 0, trail = 0, thrust = 0, prevX = 0;
function frame(now) {
  const dt = Math.max(0, Math.min(0.05, (now - last) / 1000)); last = now; clock += dt;
  const cell = size[0] / 7;
  if (!run.paused && !transition) {
    if (autopilot.checked) autoSteer();
    let remaining = dt;
    while (remaining > 0) {
      const sub = Math.min(remaining, 0.05); remaining -= sub;
      for (const e of step(sub)) present(e);
      if (run.paused) break;
    }
  }
  if (countdown > 0) { countdown -= dt; cards.countdown.querySelector('b').textContent = String(Math.max(1, Math.ceil(countdown))); if (countdown <= 0) { run.paused = false; hideOverlays(); updateSteer(); } }
  if (transition) {
    transition.t += dt / rules.transition_seconds;
    if (transition.kind === 'exit' && transition.t >= 0.5 && !transition.switched) { transition.switched = true; rejoin(); }
    if (transition.t >= 1) { transition = null; updateSteer(); }
  }
  if (outflow) { outflow.t += dt / 1.6; if (outflow.t >= 1) outflow = null; }
  shieldBump = Math.max(0, shieldBump - dt * 4);
  const w = world();
  const ship = run.passage ? { x: run.passage.x, y: run.passage.y } : { x: run.x, y: run.y };
  // Enter: the old scene shows until the iris closes.
  const inEnterFirstHalf = transition?.kind === 'enter' && transition.t < 0.5;
  const shown = inEnterFirstHalf ? main : w;
  const shownShip = inEnterFirstHalf ? { x: transition.from.x, y: transition.from.y } : ship;
  // Camera follows sideways with a dead zone and stops at the world edges.
  const halfView = 3.5, offset = shownShip.x - camX, want = Math.abs(offset) > 0.7 ? shownShip.x - Math.sign(offset) * 0.7 : camX;
  camX += (Math.min(11 - halfView, Math.max(halfView, want)) - camX) * Math.min(1, dt * 4);
  if (transition && transition.t >= 0.5 && transition.t < 0.55) camX = Math.min(11 - halfView, Math.max(halfView, shownShip.x));
  const topRow = Math.max(0, Math.min(shown.scene.rows - size[1] / cell, shownShip.y - (size[1] * 0.74) / cell));
  if (!run.paused) emitWake(dt, shownShip, w);
  stepParticles(run.paused ? 0 : dt, shown);
  stepVents(dt, shown, Math.floor(topRow), Math.ceil(topRow + size[1] / cell));

  // Ship presentation through portals: spin down into the whirlpool, rise out of the next.
  let shipScale = 1, shipSpin = 0;
  if (transition) {
    const t = transition.t, k = t < 0.5 ? t / 0.5 : (1 - t) / 0.5;
    if (transition.kind === 'enter' ? t < 0.5 : t < 0.5) { shipScale = 1 - Math.min(1, k * 1.15); shipSpin = k * Math.PI * 2.5; }
    else { shipScale = 1 - Math.min(1, k * 1.15); shipSpin = -k * Math.PI * 2; }
  }
  const ctx = travel.getContext('2d'); const dpr = devicePixelRatio || 1;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const view = drawWorld(ctx, shown, size[0], size[1], {
    cell, topRow, time: clock, ship: shownShip, shipScale, shipSpin, camX, grid: gridToggle.checked,
    collected: shown.kind === 'passage' ? run.passage?.collected ?? [] : run.collected, boostsTaken: run.boosts_taken, portalsUsed: inEnterFirstHalf ? run.portals_used.filter((id) => id !== run.passage?.portal) : run.portals_used,
    shield: run.boost > 0 && !run.passage ? { fraction: run.boost / rules.boost_seconds, bump: shieldBump } : null,
  });
  if (transition) drawIris(ctx, transition.t, view.ox + shownShip.x * cell, view.oy + shownShip.y * cell);
  if (flash) { flash.t -= dt; drawFlash(ctx, flash.text, Math.min(1, flash.t * 2)); if (flash.t <= 0) flash = null; }

  // Controls: the passage ride dims the arrows unless the steerable option is chosen.
  const riding = !!run.passage || transition;
  const disabled = riding && (rideMode() === 'auto' || transition);
  for (const side of [-1, 1]) { zones[side].classList.toggle('disabled', !!disabled); zones[side].setAttribute('aria-disabled', String(!!disabled)); }
  rideNote.hidden = !(run.passage && !transition && rideMode() === 'auto');
  if (disabled) for (const side of [-1, 1]) zones[side].classList.remove('down');
  refreshHud(); refreshState();
  requestAnimationFrame(frame);
}

function drawIris(ctx, t, x, y) {
  // Closes on the whirlpool, opens on the next one.
  const max = Math.hypot(size[0], size[1]);
  const k = t < 0.5 ? 1 - t / 0.5 : (t - 0.5) / 0.5;
  const r = Math.max(0, k * k * max);
  ctx.save(); ctx.fillStyle = '#041530'; ctx.beginPath(); ctx.rect(0, 0, size[0], size[1]); ctx.arc(x, y - 6, r, 0, Math.PI * 2, true); ctx.fill('evenodd');
  ctx.strokeStyle = 'rgba(160, 245, 255, 0.8)'; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(x, y - 6, r, 0, Math.PI * 2); if (r > 4) ctx.stroke();
  ctx.restore();
}
function drawFlash(ctx, text, alpha) {
  ctx.save(); ctx.globalAlpha = alpha; ctx.font = `800 ${15 * size[0] / 390}px Nunito`; ctx.textAlign = 'center';
  const w = ctx.measureText(text).width + 28, y = size[1] * 0.2;
  ctx.fillStyle = 'rgba(4, 24, 58, 0.6)'; ctx.beginPath(); ctx.roundRect(size[0] / 2 - w / 2, y - 18, w, 32, 16); ctx.fill();
  ctx.fillStyle = '#eafcff'; ctx.fillText(text, size[0] / 2, y + 4); ctx.restore();
}

function emitWake(dt, ship, w) {
  const steer = dt > 0 ? (ship.x - prevX) / dt : 0; prevX = ship.x;
  const fast = run.passage ? 1.6 : run.boost > 0 ? rules.boost_forward_multiplier : 1;
  trail += dt * 24 * fast;
  while (trail >= 1) { trail--; emitBubble(ship.x + (Math.random() - 0.5) * 0.12, ship.y + 0.62, { vx: -steer * 0.25 + (Math.random() - 0.5) * 0.3, vy: 1.4 * fast + Math.random() * 0.6, r: 0.03 + Math.random() * 0.045, life: 1.3 + Math.random() * 0.8 }); }
  thrust += dt * (5 + Math.min(40, Math.abs(steer) * 18));
  while (thrust >= 1) { thrust--; const side = Math.random() < 0.5 ? -1 : 1; emitBubble(ship.x + side * 0.4, ship.y + 0.38, { vx: side * 0.35 - steer * 0.3, vy: 0.9 + Math.random() * 0.4, r: 0.02 + Math.random() * 0.03, life: 0.8 + Math.random() * 0.5 }); }
  // Speed lines while boosted or riding the passage current.
  if ((run.boost > 0 || run.passage) && Math.random() < dt * 30) emitSpeedLine(ship.x + (Math.random() < 0.5 ? -1 : 1) * (0.7 + Math.random() * 1.6), ship.y - 3 - Math.random() * 3);
}

function present(e) {
  if (e.type === 'pickup') {
    for (let n = 0; n < 10; n++) emitSpark(e.x, e.y - 0.15);
    document.getElementById('salvage').classList.remove('pop'); void document.getElementById('salvage').offsetWidth; document.getElementById('salvage').classList.add('pop');
  }
  if (e.type === 'boost') { for (let n = 0; n < 16; n++) emitSpark(e.x, e.y - 0.12, '#9ff4ff'); flash = { text: 'Shield! No collision damage', t: 1.6 }; }
  if (e.type === 'shield') { shieldBump = 1; for (let n = 0; n < 6; n++) emitSpark(e.x, e.y - 0.3, '#c8fbff'); }
  if (e.type === 'impact') { phone.animate([{ transform: 'translate(0,0)' }, { transform: 'translate(-4px,2px)' }, { transform: 'translate(3px,-2px)' }, { transform: 'translate(0,0)' }], { duration: 250 }); }
  if (e.type === 'enter') { held.clear(); updateSteer(); }
  if (e.type === 'ended') finish(e.outcome);
}

/** Review autopilot: steer toward the route guide, detouring into the portal and onto the boost. */
function autoSteer() {
  if (run.passage) { run.steer = 0; return; }
  let target = main.scene.autopilot[Math.max(0, Math.floor(run.y - 1.2))];
  for (const p of main.portals) if (!run.portals_used.includes(p.id) && run.y - p.y > 0 && run.y - p.y < 5) target = p.x;
  for (const b of main.boosts) if (!run.boosts_taken.includes(b.id) && run.y - b.y > 0 && run.y - b.y < 3) target = b.x;
  const push = currentAt(main, run.x, run.y) * rules.current_columns_per_second;
  const error = target - run.x - push * 0.25;
  run.steer = Math.abs(error) < 0.08 ? 0 : Math.max(-1, Math.min(1, error * 2.2));
}

function refreshHud() {
  const fraction = Math.max(0, run.hull / rules.hull_max);
  document.getElementById('hull-fill').style.width = `calc(${fraction * 100}% - ${6 * size[0] / 390}px)`;
  const hull = document.getElementById('hull');
  hull.classList.toggle('low', fraction <= 0.35); hull.classList.toggle('shielded', run.boost > 0 || !!run.passage);
  hull.setAttribute('aria-label', `Hull ${Math.round(fraction * 100)}%${run.boost > 0 ? ', shield' : ''}`);
  document.getElementById('salvage-value').textContent = String(run.salvage);
  document.getElementById('salvage').setAttribute('aria-label', `${run.salvage} salvage this expedition`);
}

const stateList = document.getElementById('state');
function refreshState() {
  const w = world();
  const push = run.passage ? 0 : currentAt(main, run.x, run.y);
  const span = main.spans.find((s) => run.y >= s.y0 && run.y < s.y1 + 1);
  const rows = [
    ['Where', run.passage ? `bonus passage · row ${Math.max(0, Math.round(w.scene.rows - run.passage.y))}/${w.scene.rows}` : `main route · ${span?.id ?? '-'}`],
    ['Steering input', run.steer.toFixed(2)],
    ['Current', push ? `${push > 0 ? 'east →' : '← west'} ${rules.current_columns_per_second} col/s` : 'none'],
    ['Shield', run.boost > 0 ? `${run.boost.toFixed(1)} s left · ×${rules.boost_forward_multiplier} speed` : 'off'],
    ['Damage protection', run.boost > 0 || run.passage ? 'shield / passage' : run.protection > 0 ? `${run.protection.toFixed(1)} s after a hit` : 'none'],
    ['Portal', run.portals_used.length ? 'used (cannot repeat)' : main.portals.length ? 'available' : 'not in this route'],
    ['Passage salvage', run.passage ? `${run.passage.collected.length} picked up` : '-'],
    ['Hull · salvage', `${run.hull} · ${run.salvage}`],
  ];
  stateList.replaceChildren(...rows.flatMap(([k, v]) => { const dt = document.createElement('dt'), dd = document.createElement('dd'); dt.textContent = k; dd.textContent = v; return [dt, dd]; }));
  for (const li of chunkList.children) li.classList.toggle('here', !run.passage && run.y >= Number(li.dataset.y0) && run.y < Number(li.dataset.y1) + 1);
}

// ------------------------------------------------------------ elements gallery
function drawGallery() {
  const gallery = document.getElementById('gallery'); gallery.replaceChildren();
  const cell = 96, dpr = devicePixelRatio || 1;
  const tile = (label, note, w, h, paint) => {
    const canvas = document.createElement('canvas'); canvas.width = w * dpr; canvas.height = h * dpr; canvas.style.aspectRatio = `${w} / ${h}`;
    const ctx = canvas.getContext('2d'); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = '#35b6dc'; ctx.fillRect(0, 0, w, h);
    for (let y = 0; y < h / cell + 1; y++) for (let x = 0; x < w / cell + 1; x++) piece(ctx, 'floor-underwater', 'S', x * cell, y * cell, cell + 0.5, 0);
    paint(ctx);
    const div = document.createElement('div'); div.className = 'tile';
    const span = document.createElement('span'); span.innerHTML = `<b>${label}</b><br>${note}`;
    div.append(canvas, span); gallery.append(div);
  };
  const fake = (currents) => { const w = { scene: { rows: 3, columns: 3 }, currents: new Map(currents), streaks: [] }; dressCurrents(w, 3); return w; };
  for (const [label, dir] of [['Current · east', 1], ['Current · west', -1]]) {
    const w = fake([0, 1, 2].flatMap((y) => [0, 1, 2].map((x) => [`${x},${y}`, dir])));
    tile(label, 'seabed wash + drifting flow lines', cell * 3, cell * 3, (ctx) => {
      const k = cell / w.wash.c; ctx.globalAlpha = 0.3; ctx.drawImage(w.wash.canvas, -2 * cell, -2 * cell, w.wash.canvas.width * k, w.wash.canvas.height * k); ctx.globalAlpha = 1;
      drawStreaks(ctx, w, 0, 0, cell, 1.3, 0, 3);
    });
  }
  tile('Shield pickup', 'shield emblem, pulsing halo', cell * 2, cell * 2, (ctx) => drawBoost(ctx, cell, cell * 1.1, cell, 0.4));
  tile('Shield active', 'bubble rim drains with time left', cell * 2, cell * 2, (ctx) => { piece(ctx, 'submarine-yellow', 'S', cell, cell * 1.3, cell, 0, { atRoot: true }); drawShield(ctx, cell, cell * 1.3, cell, 0.62, 0, 0); });
  tile('Portal · open', 'sunken ring, live whirlpool', cell * 2, cell * 2, (ctx) => { drawSwirl(ctx, cell, cell * 1.15, cell * 0.36, 0.8); piece(ctx, 'portal-ring', 'S', cell, cell * 1.15, cell, 0, { atRoot: true }); });
  tile('Portal · used', 'still and dim; cannot be re-entered', cell * 2, cell * 2, (ctx) => { ctx.fillStyle = 'rgba(4, 30, 70, 0.45)'; ctx.beginPath(); ctx.arc(cell, cell * 1.15, cell * 0.3, 0, Math.PI * 2); ctx.fill(); piece(ctx, 'portal-ring', 'S', cell, cell * 1.15, cell, 0, { atRoot: true }); });
  tile('Passage outflow', 'rejoin whirlpool on the main route', cell * 2, cell * 2, (ctx) => drawSwirl(ctx, cell, cell, cell * 0.45, 0.3));
  tile('Gold (for contrast)', 'existing salvage pickup', cell * 2, cell * 2, (ctx) => sprite(ctx, 'gold-00', cell - 0.75 * cell, cell - 0.75 * cell, cell * 1.5));
  const arrows = (label, cls) => {
    const div = document.createElement('div'); div.className = 'tile';
    div.innerHTML = `<div class="phone" style="width:100%;aspect-ratio:2/1;background:#35b6dc;--arrow:72px;--arrow-margin:16px;--arrow-bottom:22px"><div class="zone left ${cls}" style="top:0"><svg class="arrow" viewBox="-50 -50 100 100"><polygon class="drop" points="${roundedTriangle(-1, 46, 11)}"/><polygon class="face" points="${roundedTriangle(-1, 46, 11)}"/></svg></div><div class="zone right" style="top:0"><svg class="arrow" viewBox="-50 -50 100 100"><polygon class="drop" points="${roundedTriangle(1, 46, 11)}"/><polygon class="face" points="${roundedTriangle(1, 46, 11)}"/></svg></div></div><span><b>${label}</b></span>`;
    if (cls === 'disabled') div.querySelector('.right').classList.add('disabled');
    gallery.append(div);
  };
  arrows('Arrows · left pressed', 'down');
  arrows('Arrows · passage ride (disabled)', 'disabled');
}

for (const tab of document.querySelectorAll('[role="tab"]')) tab.addEventListener('click', () => {
  for (const other of document.querySelectorAll('[role="tab"]')) other.setAttribute('aria-selected', String(other === tab));
  for (const view of document.querySelectorAll('.view')) view.hidden = view.id !== tab.dataset.view;
  if (tab.dataset.view === 'elements') drawGallery();
});

const params = new URLSearchParams(location.search);
newRun(Math.max(1, Number(params.get('seed')) | 0) || 22);
if (params.get('view')) document.querySelector(`[data-view="${params.get('view')}"]`)?.click();
if (params.get('autopilot')) autopilot.checked = true;
if (params.get('jump')) document.querySelector(`[data-jump="${params.get('jump')}"]`)?.click();
requestAnimationFrame(frame);
