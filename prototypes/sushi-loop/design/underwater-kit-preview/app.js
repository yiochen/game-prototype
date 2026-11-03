// Issue #21 expedition review: seeded chunk routes drawn with the approved
// production pieces (and same-recipe v2 variants) over the ground layer.
// Route generation and scene composition come from the shared route module
// that Godot will mirror; this page adds only presentation (particles, glow).
import manifest from '../../assets/expedition/v1/manifest.json';
import v2Library from '../../assets/expedition/v2/library.json';
import originalSet from './original-set.json';
import { analyzeLibrary, assemble, chunkFromMap, composeScene, generate, mulberry32 } from '../../assets/expedition/route/route.js';

// Chunk files are read as-is; analysis happens here at load, like the game.
const chunkFiles = import.meta.glob('../../godot/content/expedition/chunks/*.json', { eager: true, import: 'default' });

const productionUrls = import.meta.glob('../../assets/production/sprites/{floor-underwater,decor-background-rock,decor-foreground-rock,boulder-underwater,column-broken,decor-ruin-fragment,crate-wood,decor-foreground-coral,decor-midground-coral,decor-kelp,decor-starfish,decor-background-wreck,decor-background-fish,decor-light-shafts,submarine-yellow}/*.png', { eager: true, query: '?url', import: 'default' });
const v2Urls = import.meta.glob('../../assets/expedition/v2/sprites/*/*.png', { eager: true, query: '?url', import: 'default' });
const kitUrls = import.meta.glob('../../assets/expedition/v1/sprites/{bed,gold}-*.png', { eager: true, query: '?url', import: 'default' });

const load = (src) => new Promise((resolve, reject) => { const image = new Image(); image.onload = () => resolve(image); image.onerror = () => reject(new Error(`Missing ${src}`)); image.src = src; });

// Kit sprites: the ground-layer beds and the rotating gold.
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

// Production clips (128 logical px per cell, atlases at sourceScale).
const clipImages = {};
await Promise.all([...new Set(Object.values(originalSet.objects).flatMap((o) => o.clips.flatMap((c) => Object.values(c.directions).map((d) => d.image))))]
  .filter((image) => productionUrls[`../../${image}`] || v2Urls[`../../${image}`])
  .map(async (image) => { clipImages[image] = await load(productionUrls[`../../${image}`] ?? v2Urls[`../../${image}`]); }));

/** Draw a clip frame with its ground root at the footprint centre (or at `x, y` when `atRoot`). */
function piece(ctx, id, dir, x, y, cell, time, { salt = 0, clip = 0, atRoot = false, scale = 1, alpha = 1 } = {}) {
  const o = originalSet.objects[id]; const c = o.clips[clip]; const d = c.directions[dir] ?? c.directions.S; const s = (cell / 128) * scale;
  const frame = c.frames > 1 ? c.frameOrder[Math.floor(time * c.fps + salt) % c.frameOrder.length] : 0;
  const [sx, sy, sw, sh] = d.rects[frame];
  const [fw, fh] = o.footprint ?? [1, 1];
  const rx = atRoot ? x : x + fw * 0.5 * cell, ry = atRoot ? y : y + fh * 0.5 * cell;
  if (alpha !== 1) ctx.globalAlpha = alpha;
  ctx.drawImage(clipImages[d.image], sx, sy, sw, sh, rx - o.root[0] * s, ry - o.root[1] * s, o.frameSize[0] * s, o.frameSize[1] * s);
  if (alpha !== 1) ctx.globalAlpha = 1;
}

// ------------------------------------------------------------ route
const params = new URLSearchParams(location.search);
const sources = Object.entries(chunkFiles).map(([path, doc]) => chunkFromMap(doc, path.split('/').pop().slice(0, -5)));
// Designer "Test in route preview": the painted chunk replaces or joins the library and is forced into the run.
let testChunk = null;
if (params.get('test') === 'chunk') {
  try {
    testChunk = chunkFromMap(JSON.parse(localStorage.getItem('sushi-loop-chunk-test')), 'designer-test');
    sources.push(testChunk);
  } catch { testChunk = null; }
}
const { chunks: library, problems } = analyzeLibrary(sources);
if (Object.keys(problems).length) console.warn('Chunks left out:', problems);
let run;
function buildRun(seed) {
  const sequence = generate(seed, library, { force: testChunk && !problems[testChunk.id] ? testChunk.id : undefined });
  const { rows: grid, spans } = assemble(sequence);
  const scene = composeScene(grid, v2Library.objects, seed);
  const byRow = Array.from({ length: scene.rows }, () => []);
  for (const o of scene.objects) byRow[o.y].push(o);
  // Soft contact shadow of all rock masses, cast slightly south-east.
  const c = 24, shadow = new OffscreenCanvas((scene.columns + 4) * c, (scene.rows + 4) * c), sctx = shadow.getContext('2d');
  sctx.filter = 'blur(9px)'; sctx.fillStyle = '#04174a';
  for (const b of scene.collision) sctx.fillRect((b.x + 2) * c - 2, (b.y + 2) * c - 2, c + 4, c + 4);
  const fish = Array.from({ length: Math.ceil(scene.rows / 13) }, (_, i) => { const r = mulberry32(seed * 31 + i); return { y: 4 + i * 13 + r() * 6, speed: 0.25 + r() * 0.25, dir: i % 2 ? -1 : 1, phase: r() * 20 }; });
  run = { seed, sequence, spans, grid, scene, byRow, shadow: { canvas: shadow, c }, fish };
}

// ------------------------------------------------------------ particles
// Bubbles rise toward the camera, which this projection shows as drifting up
// the screen while growing and fading. Sparks are short additive gold glints.
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
function emitSpark(x, y) {
  const a = Math.random() * Math.PI * 2, s = 0.6 + Math.random() * 1.4;
  particles.push({ kind: 'spark', x, y, vx: Math.cos(a) * s, vy: Math.sin(a) * s - 0.3, r: 0.035 + Math.random() * 0.03, life: 0.45 + Math.random() * 0.3, age: 0, drag: 3.5 });
}
function stepParticles(dt) {
  for (const p of particles) {
    p.age += dt;
    const k = Math.exp(-p.drag * dt);
    p.vx *= k; p.vy *= k;
    if (p.kind === 'bubble') p.vy -= p.rise * dt * 1.6;
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
    } else {
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = 1 - t;
      ctx.fillStyle = '#ffe58a'; ctx.beginPath(); ctx.arc(ox + p.x * cell, oy + p.y * cell, p.r * cell * (1 - t * 0.5), 0, Math.PI * 2); ctx.fill(); ctx.restore();
    }
  }
  ctx.globalAlpha = 1;
}

// Vent bursts: each vent sleeps 1.5–4 s, then releases 3–7 bubbles over ~0.6 s.
const vents = new Map();
function stepVents(dt, top, bottom) {
  for (const v of run.scene.vents) {
    if (v.y < top - 1 || v.y > bottom + 1) continue;
    const key = `${v.x},${v.y}`;
    const s = vents.get(key) ?? { wait: Math.random() * 3, left: 0, gap: 0 };
    if (s.left > 0) {
      s.gap -= dt;
      if (s.gap <= 0) { emitBubble(v.x + (Math.random() - 0.5) * 0.2, v.y, { vy: -0.2, r: 0.025 + Math.random() * 0.035, life: 2.2 + Math.random(), rise: 0.35 }); s.left--; s.gap = 0.08 + Math.random() * 0.12; }
    } else if ((s.wait -= dt) <= 0) { s.left = 3 + Math.floor(Math.random() * 5); s.wait = 1.5 + Math.random() * 2.5; }
    vents.set(key, s);
  }
}

// ------------------------------------------------------------ drawing
function drawWorld(ctx, w, h, { cell, topRow, time, ship, collected = new Set(), grid = false, camX = null }) {
  const { scene } = run;
  // camX: world column at the screen centre (null = centre the whole world).
  const ox = camX === null ? (w - scene.columns * cell) / 2 : w / 2 - camX * cell, oy = -topRow * cell;
  const top = Math.max(0, Math.floor(topRow) - 1), bottom = Math.min(scene.rows - 1, Math.ceil(topRow + h / cell) + 3);
  ctx.fillStyle = '#0b2f63'; ctx.fillRect(0, 0, w, h);
  // Floor: the production animated seabed tile with faint square seams.
  for (let y = top; y <= bottom; y++) for (let x = 0; x < scene.columns; x++) piece(ctx, 'floor-underwater', 'S', ox + x * cell, oy + y * cell, cell + 0.5, time);
  ctx.strokeStyle = 'rgba(190, 245, 255, 0.22)'; ctx.lineWidth = Math.max(1, cell / 60); ctx.beginPath();
  for (let x = 0; x <= scene.columns; x++) { ctx.moveTo(ox + x * cell, oy + top * cell); ctx.lineTo(ox + x * cell, oy + (bottom + 1) * cell); }
  for (let y = top; y <= bottom + 1; y++) { ctx.moveTo(ox, oy + y * cell); ctx.lineTo(ox + scene.columns * cell, oy + y * cell); }
  ctx.stroke();
  const { canvas: shadow, c } = run.shadow, k = cell / c;
  ctx.globalAlpha = 0.55; ctx.drawImage(shadow, ox - 2 * cell + cell * 0.1, oy - 2 * cell + cell * 0.16, shadow.width * k, shadow.height * k); ctx.globalAlpha = 1;
  for (const f of run.fish) {
    const span = scene.columns + 4, head = ((f.phase + time * f.speed) % span + span) % span - 2;
    piece(ctx, 'decor-background-fish', f.dir > 0 ? 'E' : 'W', ox + (f.dir > 0 ? head : scene.columns - head) * cell, oy + f.y * cell, cell, time, { atRoot: true, salt: f.phase * 7 });
  }
  for (const d of scene.seabed) if (d.y >= top && d.y <= bottom) piece(ctx, d.id, d.dir, ox + (d.x + 0.5) * cell, oy + (d.y + 0.5) * cell, cell, time, { atRoot: true, scale: d.scale ?? 1 });
  if (ship) {
    // The hull floats above the seabed: a soft shadow lands below and slightly behind it.
    ctx.save(); ctx.translate(ox + (ship.x + 0.06) * cell, oy + (ship.y + 0.42) * cell); ctx.scale(1, 0.5);
    const shade = ctx.createRadialGradient(0, 0, 0, 0, 0, cell * 0.62);
    shade.addColorStop(0, 'rgba(4, 30, 70, 0.5)'); shade.addColorStop(0.55, 'rgba(4, 30, 70, 0.3)'); shade.addColorStop(1, 'rgba(4, 30, 70, 0)');
    ctx.fillStyle = shade; ctx.beginPath(); ctx.arc(0, 0, cell * 0.62, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  }
  for (const b of scene.beds) if (b.y >= top && b.y <= bottom) sprite(ctx, b.sprite, ox + b.x * cell, oy + b.y * cell, cell);
  scene.pickups.forEach((p, i) => {
    if (collected.has(i) || p.y < top || p.y > bottom + 1) return;
    const bob = Math.sin(time * 2.4 + i) * 0.05;
    // Warm additive halo, pulsing out of phase between nuggets, plus a brief glint.
    const gx = ox + p.x * cell, gy = oy + (p.y - 0.15 + bob) * cell, pulse = 0.75 + 0.25 * Math.sin(time * 3.2 + i * 1.7);
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    const halo = ctx.createRadialGradient(gx, gy, 0, gx, gy, cell * 0.62 * pulse);
    halo.addColorStop(0, 'rgba(255, 226, 120, 0.55)'); halo.addColorStop(0.45, 'rgba(255, 190, 60, 0.22)'); halo.addColorStop(1, 'rgba(255, 170, 40, 0)');
    ctx.fillStyle = halo; ctx.beginPath(); ctx.arc(gx, gy, cell * 0.62 * pulse, 0, Math.PI * 2); ctx.fill();
    const glint = Math.max(0, Math.sin(time * 1.3 + i * 2.3)) ** 24;
    if (glint > 0.02) {
      const gs = cell * 0.32 * glint, sx = gx + cell * 0.14, sy = gy - cell * 0.16;
      ctx.fillStyle = `rgba(255, 255, 235, ${glint})`; ctx.beginPath();
      ctx.moveTo(sx, sy - gs); ctx.lineTo(sx + gs * 0.18, sy - gs * 0.18); ctx.lineTo(sx + gs, sy); ctx.lineTo(sx + gs * 0.18, sy + gs * 0.18);
      ctx.lineTo(sx, sy + gs); ctx.lineTo(sx - gs * 0.18, sy + gs * 0.18); ctx.lineTo(sx - gs, sy); ctx.lineTo(sx - gs * 0.18, sy - gs * 0.18); ctx.fill();
    }
    ctx.restore();
    sprite(ctx, `gold-${String(Math.floor(time * 10 + i * 3) % 12).padStart(2, '0')}`, ox + (p.x - 0.75) * cell, oy + (p.y - 0.75 + bob - 0.12) * cell, cell * 1.5);
  });
  let shipDrawn = !ship;
  const drawShip = () => { piece(ctx, 'submarine-yellow', 'S', ox + ship.x * cell, oy + ship.y * cell, cell, time, { atRoot: true }); shipDrawn = true; };
  for (let y = top; y <= bottom; y++) {
    // A landmark at or south of the ship's row stands in front of it: the span covers the hull as it passes under.
    if (!shipDrawn && y >= Math.floor(ship.y) && run.byRow[y].some((o) => o.w > 1)) drawShip();
    for (const o of run.byRow[y]) piece(ctx, o.id, o.dir, ox + o.x * cell, oy + o.y * cell, cell, time, { salt: o.x * 5 + o.y * 3 });
  }
  drawParticles(ctx, ox, oy, cell);
  if (!shipDrawn) drawShip();
  for (const s of scene.shafts) if (s.y >= top - 2 && s.y <= bottom) piece(ctx, s.id, s.dir, ox + s.x * cell, oy + s.y * cell, cell * 1.6, time, { salt: s.y });
  const v = ctx.createRadialGradient(w / 2, h * 0.55, h * 0.3, w / 2, h * 0.55, h * 0.8);
  v.addColorStop(0, 'rgba(3, 20, 60, 0)'); v.addColorStop(1, 'rgba(3, 20, 60, 0.18)');
  ctx.fillStyle = v; ctx.fillRect(0, 0, w, h);
  if (grid) {
    ctx.save(); ctx.lineWidth = 2; ctx.strokeStyle = 'rgba(255, 90, 90, 0.85)';
    for (const b of scene.collision) if (b.y >= top && b.y <= bottom) ctx.strokeRect(ox + b.x * cell + 1, oy + b.y * cell + 1, cell - 2, cell - 2);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.7)'; ctx.setLineDash([6, 6]);
    for (const s of run.spans) { const y = oy + (s.y1 + 1) * cell; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }
    if (ship) { ctx.setLineDash([]); ctx.strokeStyle = '#ffe14d'; ctx.strokeRect(ox + (ship.x - 0.32) * cell, oy + (ship.y - 0.44) * cell, 0.64 * cell, 0.88 * cell); }
    ctx.restore();
  }
}

// ------------------------------------------------------------ travel view
const travel = document.getElementById('travel');
const stage = document.getElementById('stage');
const toggle = document.getElementById('toggle');
const rowInput = document.getElementById('row');
const rowOut = document.getElementById('row-out');
const frameSelect = document.getElementById('frame');
const gridToggle = document.getElementById('grid');
const seedInput = document.getElementById('seed');
const chunkStrip = document.getElementById('chunks');
let size = [390, 844];
let running = true;
const state = { y: 0, x: 3.5, prevX: 3.5, camX: 5.5, collected: new Set(), trail: 0, thrust: 0 };

function startRun(seed) {
  buildRun(seed);
  seedInput.value = String(seed);
  rowInput.max = String(run.scene.rows);
  particles.length = 0; vents.clear();
  state.y = run.scene.rows - 0.5; state.x = state.prevX = state.camX = run.scene.autopilot[run.scene.rows - 1]; state.collected.clear();
  const url = new URL(location.href); url.searchParams.set('seed', String(seed)); history.replaceState(null, '', url);
  chunkStrip.replaceChildren(...run.spans.map((s) => {
    const chip = document.createElement('button');
    chip.className = `chip ${s.kind}`; chip.dataset.y1 = String(s.y1);
    chip.innerHTML = `<b>${s.id}</b><span>${s.kind} · ${s.difficulty}</span>`;
    chip.title = `Jump to ${s.id}`;
    chip.addEventListener('click', () => { state.y = s.y1 + 0.5; state.x = run.scene.autopilot[s.y1]; state.collected.clear(); particles.length = 0; });
    return chip;
  }));
  views[document.querySelector('[role="tab"][aria-selected="true"]')?.dataset.view]?.();
}
document.getElementById('reroll').addEventListener('click', () => startRun(Math.floor(Math.random() * 99999) + 1));
seedInput.addEventListener('change', () => startRun(Math.max(1, Number(seedInput.value) | 0)));

function resize() {
  const wide = frameSelect.value === 'wide';
  stage.classList.toggle('wide', wide);
  size = wide ? [Math.min(460, innerWidth - 40), Math.min(900, innerHeight - 190)] : frameSelect.value.split('x').map(Number);
  const dpr = devicePixelRatio || 1;
  travel.width = size[0] * dpr; travel.height = size[1] * dpr;
  travel.style.width = `${size[0]}px`; travel.style.height = `${size[1]}px`;
}
frameSelect.addEventListener('change', resize);
addEventListener('resize', resize);
resize();
toggle.addEventListener('click', () => { running = !running; toggle.textContent = running ? 'Pause' : 'Play'; toggle.setAttribute('aria-pressed', String(running)); });
rowInput.addEventListener('input', () => { state.y = run.scene.rows - Number(rowInput.value) + 0.5; state.x = run.scene.autopilot[Math.floor(state.y)]; state.collected.clear(); particles.length = 0; });

// Relative sideways drag steers; release hands back to the review autopilot.
let drag = null;
travel.addEventListener('pointerdown', (e) => { drag = { x: e.clientX, ship: state.x }; travel.setPointerCapture(e.pointerId); });
travel.addEventListener('pointermove', (e) => { if (drag) state.x = Math.max(0.4, Math.min(run.scene.columns - 0.4, drag.ship + (e.clientX - drag.x) / (size[0] / run.scene.viewColumns))); });
for (const type of ['pointerup', 'pointercancel']) travel.addEventListener(type, () => { drag = null; });

let last = performance.now(), clock = 0;
function frame(now) {
  const dt = Math.max(0, Math.min(0.05, (now - last) / 1000)); last = now; clock += dt;
  const cell = size[0] / run.scene.viewColumns;
  const topRow = state.y - (size[1] * 0.74) / cell;
  // Horizontal follow: a small dead zone keeps ordinary steering from swaying
  // the view; the camera stops at the world edges.
  const half = run.scene.viewColumns / 2, offset = state.x - state.camX, dead = 0.7;
  const want = Math.abs(offset) > dead ? state.x - Math.sign(offset) * dead : state.camX;
  state.camX += (Math.min(run.scene.columns - half, Math.max(half, want)) - state.camX) * Math.min(1, dt * 4);
  if (running) {
    state.y -= dt * 2.1;
    if (state.y < 0.5) startRun(run.seed);
    if (!drag) {
      const target = run.scene.autopilot[Math.max(0, Math.floor(state.y - 1.2))];
      state.x += (target - state.x) * Math.min(1, dt * 2.6);
    }
    const steer = dt > 0 ? (state.x - state.prevX) / dt : 0; state.prevX = state.x;
    // Propeller wake: steady stream pushed backward, curling with the steering.
    state.trail += dt * 24;
    while (state.trail >= 1) { state.trail--; emitBubble(state.x + (Math.random() - 0.5) * 0.12, state.y + 0.62, { vx: -steer * 0.25 + (Math.random() - 0.5) * 0.3, vy: 1.4 + Math.random() * 0.6, r: 0.03 + Math.random() * 0.045, life: 1.3 + Math.random() * 0.8 }); }
    // Side thrusters fizz harder while steering.
    state.thrust += dt * (5 + Math.min(40, Math.abs(steer) * 18));
    while (state.thrust >= 1) {
      state.thrust--;
      const side = Math.random() < 0.5 ? -1 : 1;
      emitBubble(state.x + side * 0.4, state.y + 0.38, { vx: side * 0.35 - steer * 0.3, vy: 0.9 + Math.random() * 0.4, r: 0.02 + Math.random() * 0.03, life: 0.8 + Math.random() * 0.5 });
    }
    run.scene.pickups.forEach((p, i) => {
      if (state.collected.has(i) || Math.abs(p.x - state.x) > 0.55 || Math.abs(p.y - state.y) > 0.6) return;
      state.collected.add(i);
      for (let n = 0; n < 10; n++) emitSpark(p.x, p.y - 0.15);
      for (let n = 0; n < 6; n++) emitBubble(p.x + (Math.random() - 0.5) * 0.3, p.y, { vx: (Math.random() - 0.5) * 0.8, vy: (Math.random() - 0.5) * 0.6, r: 0.02 + Math.random() * 0.03, life: 0.9 + Math.random() * 0.5 });
    });
    stepVents(dt, Math.floor(topRow), Math.ceil(topRow + size[1] / cell));
  }
  stepParticles(running ? dt : 0);
  rowInput.value = String(Math.max(1, Math.round(run.scene.rows - state.y + 0.5))); rowOut.textContent = rowInput.value;
  for (const chip of chunkStrip.children) {
    const span = run.spans.find((s) => String(s.y1) === chip.dataset.y1);
    chip.classList.toggle('current', state.y >= span.y0 && state.y < span.y1 + 1);
  }
  const ctx = travel.getContext('2d'); const dpr = devicePixelRatio || 1;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  drawWorld(ctx, size[0], size[1], { cell, topRow, time: clock, ship: { x: state.x, y: state.y }, collected: state.collected, grid: gridToggle.checked, camX: state.camX });
  requestAnimationFrame(frame);
}

// ------------------------------------------------------------ other views
function drawCompare() {
  const canvas = document.getElementById('compare-canvas');
  const w = 420, h = 630, dpr = devicePixelRatio || 1;
  canvas.width = w * dpr; canvas.height = h * dpr;
  const ctx = canvas.getContext('2d'); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const cell = w / run.scene.viewColumns;
  // Frame the first fork so the comparison shows a split passage.
  const fork = run.spans.find((s) => s.kind === 'fork') ?? run.spans[1];
  const shipY = fork.y1 - 1.5, shipX = run.scene.autopilot[Math.floor(shipY)];
  document.getElementById('compare-chunk').textContent = fork.id;
  const half = run.scene.viewColumns / 2;
  drawWorld(ctx, w, h, { cell, topRow: shipY + 2 - h / cell, time: 3.2, ship: { x: shipX, y: shipY }, camX: Math.min(run.scene.columns - half, Math.max(half, shipX)) });
}

function drawOverview() {
  const strips = document.getElementById('strips'); strips.replaceChildren();
  const cell = 24, dpr = devicePixelRatio || 1;
  for (const s of run.spans) {
    const figure = document.createElement('figure');
    const canvas = document.createElement('canvas');
    const w = run.scene.columns * cell, h = (s.y1 - s.y0 + 1) * cell;
    canvas.width = w * dpr; canvas.height = h * dpr; canvas.style.width = `${w}px`; canvas.style.height = `${h}px`;
    canvas.setAttribute('aria-label', `${s.id}, ${s.kind}, difficulty ${s.difficulty}`);
    const ctx = canvas.getContext('2d'); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    drawWorld(ctx, w, h, { cell, topRow: s.y0, time: 0, ship: null });
    const caption = document.createElement('figcaption');
    caption.innerHTML = `<b>${s.id}</b><br>${s.kind} · difficulty ${s.difficulty}`;
    figure.append(canvas, caption); strips.append(figure);
  }
}

function drawKit() {
  const pieces = document.getElementById('pieces'); pieces.replaceChildren();
  for (const [id, o] of Object.entries(originalSet.objects)) {
    if (['floor-underwater', 'submarine-yellow', 'salvage-metal', 'decor-bubbles', 'decor-light-shafts', 'decor-background-fish'].includes(id)) continue;
    const [fw, fh] = o.footprint ?? [1, 1], cell = 64, dpr = devicePixelRatio || 1;
    const w = (fw + 1) * cell, h = (fh + 3.2) * cell;
    const canvas = document.createElement('canvas'); canvas.width = w * dpr; canvas.height = h * dpr;
    const ctx = canvas.getContext('2d'); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const x0 = cell / 2, y0 = h - (fh + 0.3) * cell;
    ctx.fillStyle = '#35b6dc'; ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = 'rgba(160, 238, 255, 0.35)';
    for (let gx = -1; gx <= fw + 1; gx++) for (let gy = -4; gy <= fh; gy++) ctx.strokeRect(x0 + gx * cell, y0 + gy * cell, cell, cell);
    ctx.strokeStyle = '#ffe14d'; ctx.lineWidth = 2; ctx.strokeRect(x0, y0, fw * cell, fh * cell);
    piece(ctx, id, 'S', x0, y0, cell, 0);
    const card = document.createElement('div'); card.className = 'piece';
    const label = document.createElement('span');
    label.innerHTML = `<b>${id}</b><br>${o.clips[0].directions.S.image.includes('/v2/') ? 'new · same recipe' : 'production'} · ${fw}×${fh}`;
    card.append(canvas, label); pieces.append(card);
  }
}

const views = { compare: drawCompare, overview: drawOverview, kit: drawKit };
for (const tab of document.querySelectorAll('[role="tab"]')) tab.addEventListener('click', () => {
  for (const other of document.querySelectorAll('[role="tab"]')) other.setAttribute('aria-selected', String(other === tab));
  for (const view of document.querySelectorAll('.view')) view.hidden = view.id !== tab.dataset.view;
  views[tab.dataset.view]?.();
});
startRun(Math.max(1, Number(params.get('seed')) | 0) || 21);
if (params.get('view')) document.querySelector(`[data-view="${params.get('view')}"]`)?.click();
requestAnimationFrame(frame);
