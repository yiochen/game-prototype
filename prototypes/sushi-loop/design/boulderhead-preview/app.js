import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js';
import { GLTFLoader } from 'https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/loaders/GLTFLoader.js';
import manifest from '../../assets/expedition/v1/manifest.json';
import v2Library from '../../assets/expedition/v2/library.json';
import originalSet from '../underwater-kit-preview/original-set.json';
import rules from './balance.json';
import { analyzeLibrary, assemble, chunkFromMap, composeScene, generate, hash, mulberry32 } from '../../assets/expedition/route/route.js';
import { collides as hits, rockDistance } from '../eel-strike-preview/fairness.js';
import { REEF_CHUNKS, breachCells, fairLines, lineAt, reefRows } from './reef.js';

/* Boulderhead Parrotfish broken path review for #76, built on the approved #24/#25 chase.
   - Reef chunks: three creature slots are reef chunks, dense brittle reef ('b') round a few dark bedrock
     outcrops. Ordinary chunks between them are unchanged.
   - Smash: the parrotfish swims `lead_rows` ahead and follows one fair line per reef chunk (reef.js).
     Cracks spread on the next breach cells for `crack_seconds`, then its head reaches them and they
     shatter: their collision goes the same frame. Debris is cosmetic. Broken reef stays open.
   - Crash-through: a ship that leaves the breach shatters the brittle reef it touches, at
     `reef_damage` hull (once per hit protection) and a brief slowdown. Bedrock is plain rock.
   The parrotfish is the static concept GLB (assets/creature-boulderhead-parrotfish, no rig): swimming,
   ramming and the hook are faked with transforms. Brittle reef is drawn in code as a placeholder.
   Everything else (terrain, sub, cable, HUD, award, results) is the approved #21-#25 art. */

const FISH_URL = new URL('../../assets/creature-boulderhead-parrotfish/export/boulderhead-parrotfish.glb', import.meta.url).href;
const contentChunks = import.meta.glob('../../godot/content/expedition/chunks/*.json', { eager: true, import: 'default' });
const productionUrls = import.meta.glob('../../assets/production/sprites/{floor-underwater,decor-background-rock,decor-foreground-rock,boulder-underwater,column-broken,decor-ruin-fragment,crate-wood,decor-foreground-coral,decor-midground-coral,decor-kelp,decor-starfish,decor-background-wreck,decor-background-fish,decor-light-shafts,submarine-yellow}/*.png', { eager: true, query: '?url', import: 'default' });
const v2Urls = import.meta.glob('../../assets/expedition/v2/sprites/*/*.png', { eager: true, query: '?url', import: 'default' });
const reefUrls = import.meta.glob('../../assets/expedition/v2/sprites/reef-*/static-S.png', { eager: true, query: '?url', import: 'default' });
const reefBreakUrls = import.meta.glob('../../assets/expedition/v2/sprites/reef-break/reef-*.png', { eager: true, query: '?url', import: 'default' });
const kitUrls = import.meta.glob('../../assets/expedition/v1/sprites/{bed,gold}-*.png', { eager: true, query: '?url', import: 'default' });
const PLATES_URL = new URL('../recipe-picker-preview/raw/plates.png', import.meta.url).href;
const FOOD_URL = new URL('../recipe-picker-preview/raw/food.png', import.meta.url).href;
const COIN_URL = new URL('../../godot/assets/ui/coin.svg', import.meta.url).href;
const BACKDROP_URL = new URL('../pursuit-preview/award-art/v1/backdrop.jpg', import.meta.url).href;
document.documentElement.style.setProperty('--plates', `url(${PLATES_URL})`);
document.documentElement.style.setProperty('--food', `url(${FOOD_URL})`);

const $ = (id) => document.getElementById(id);
const phone = $('phone'), stage = $('stage');
const worldCanvas = $('world'), eelCanvas = $('eel'), fxCanvas = $('fx');
const wctx = worldCanvas.getContext('2d'), fctx = fxCanvas.getContext('2d');
const banner = $('banner'), scrim = $('scrim'), rays = $('rays');
const cards = { paused: $('paused-card'), award: $('award-host'), results: $('results-card') };
const load = (src) => new Promise((ok, bad) => { const i = new Image(); i.onload = () => ok(i); i.onerror = () => bad(new Error(`Missing ${src}`)); i.src = src; });
const R = () => rules.reef;

// ---------------------------------------------------------------- world art (as #22)
const kit = manifest.sprites, kitImages = {}, PX = manifest.cell_pixels;
await Promise.all(Object.entries(kit).filter(([n]) => /^(bed|gold)-/.test(n)).map(async ([n, e]) => { kitImages[n] = await load(kitUrls[`../../assets/expedition/v1/${e.image}`]); }));
const sprite = (ctx, name, x, y, cell) => { const e = kit[name], s = cell / PX; ctx.drawImage(kitImages[name], x - e.origin[0] * s, y - e.origin[1] * s, e.size[0] * s, e.size[1] * s); };
const objects = { ...originalSet.objects };
// #76 reef model (assets/expedition/v2/reef.py): one sprite per neighbour mask and slab pattern, plus rubble.
// Frame 192x512 at 2x, ground root (96, 416) at the cell centre, like the v2 rocks.
const reefArt = {};
await Promise.all(Object.entries(reefUrls).map(async ([file, url]) => { reefArt[file.split('/').at(-2)] = await load(url); }));
// Crack and break sheets (assets/expedition/v2/reef_break.py): per piece, nine 384x1024 frames in a row:
// crack-1..3 (shown over crack_seconds), then break-1..6 at 12 fps; break-6 is the rubble the cell keeps.
const reefBreak = {};
await Promise.all(Object.entries(reefBreakUrls).map(async ([file, url]) => { reefBreak[file.split('/').at(-1).replace('.png', '')] = await load(url); }));
const REEF_FRAME = [192, 512], REEF_ROOT = [96, 416], BREAK_FPS = 12, CRACK_FRAMES = 3, BREAK_FRAMES = 6;
function reefSprite(ctx, id, x, y, dx = 0, frame = -1) {
  const k = cell / 128, img = frame < 0 ? reefArt[id] : reefBreak[id];
  const src = frame < 0 ? [0, 0, img.width, img.height] : [frame * 384, 0, 384, 1024];
  ctx.drawImage(img, ...src, x + dx - REEF_ROOT[0] * k, y - REEF_ROOT[1] * k, REEF_FRAME[0] * k, REEF_FRAME[1] * k);
}
const reefId = (x, y, seed) => `reef-${String(neighbourMask(x, y)).padStart(2, '0')}-${'abc'[Math.floor(seed * 3)]}`;
/** Break frame of a shattered cell (3..8), or 8 once it has settled. */
const breakFrame = (c) => CRACK_FRAMES + Math.min(BREAK_FRAMES - 1, Math.floor((run.t - c.brokenAt) * BREAK_FPS));
const breakSheets = () => $('reef-art').value === 'model' && Object.keys(reefBreak).length > 0;
const modelArt = () => $('reef-art').value === 'model';
const urlFor = (image) => productionUrls[`../../${image}`] ?? v2Urls[`../../${image}`];
const clipImages = {};
await Promise.all([...new Set(Object.values(objects).flatMap((o) => o.clips.flatMap((c) => Object.values(c.directions).map((d) => d.image))))]
  .filter(urlFor).map(async (image) => { clipImages[image] = await load(urlFor(image)); }));
function piece(ctx, id, dir, x, y, cell, time, { salt = 0, clip = 0, atRoot = false, scale = 1 } = {}) {
  const o = objects[id]; if (!o) return;
  const c = o.clips[clip] ?? o.clips[0], d = c.directions[dir] ?? c.directions.S, s = (cell / 128) * scale;
  if (!clipImages[d.image]) return;
  const frame = c.frames > 1 ? c.frameOrder[Math.floor(time * c.fps + salt) % c.frameOrder.length] : 0;
  const [sx, sy, sw, sh] = d.rects[frame], [fw, fh] = o.footprint ?? [1, 1];
  const rx = atRoot ? x : x + fw * 0.5 * cell, ry = atRoot ? y : y + fh * 0.5 * cell;
  ctx.drawImage(clipImages[d.image], sx, sy, sw, sh, rx - o.root[0] * s, ry - o.root[1] * s, o.frameSize[0] * s, o.frameSize[1] * s);
}
{
  const sub = objects['submarine-yellow'].clips[0].directions.S, [sx, sy, sw, sh] = sub.rects[0];
  const c = document.createElement('canvas'); c.width = sw * 0.5; c.height = sh * 0.4;
  c.getContext('2d').drawImage(clipImages[sub.image], sx + sw * 0.25, sy + sh * 0.44, sw * 0.5, sh * 0.4, 0, 0, c.width, c.height);
  phone.style.setProperty('--ship', `url(${c.toDataURL()})`);
}

// ---------------------------------------------------------------- route
const sources = [];
for (const [file, doc] of Object.entries(contentChunks)) sources.push(chunkFromMap(doc, file.split('/').pop().slice(0, -5)));
// Storm Eel chunks belong to #25. Reef chunks take the creature slots; to the route, brittle reef is water.
const reefById = Object.fromEntries(REEF_CHUNKS.map((c) => [c.id, c]));
const reefSources = REEF_CHUNKS.map((c) => ({ id: c.id, name: c.name, kind: 'creature', creature: 'boulderhead-parrotfish', attackRows: reefRows(c.rows), rows: c.rows.map((r) => r.replaceAll('b', '.')) }));
let library, tables = {};
function buildLibrary() {
  library = analyzeLibrary([...sources.filter((c) => c.kind !== 'creature'), ...reefSources]).chunks;
  tables = Object.fromEntries(REEF_CHUNKS.map((c) => [c.id, fairLines(c, rules)]));
  const sel = $('force'), keep = sel.value;
  sel.replaceChildren(new Option('Seeded', ''), ...REEF_CHUNKS.map((c) => new Option(`${c.name} (${tables[c.id].fair.length} lines)`, c.id)));
  sel.value = keep;
}
const COLUMNS = 11, VIEW = 7;
let world;
function buildWorld(seed, force) {
  buildLibrary();
  const sequence = generate(seed, library, { slots: ['launch', 'start', ...rules.pursuit_plan, 'finish'], force: force || undefined });
  const { rows: grid, spans } = assemble(sequence);
  // Collision grid: intact brittle reef is rock ('#') until something breaks it.
  const solid = grid.map((r) => [...r]);
  const reef = grid.map((r) => Array(r.length).fill(null));
  const rng = mulberry32(seed * 7 + 76);
  for (const sp of spans) {
    const chunk = reefById[sp.id];
    if (!chunk) continue;
    chunk.rows.forEach((row, y) => [...row].forEach((ch, x) => { if (ch === 'b') { solid[sp.y0 + y][x] = '#'; reef[sp.y0 + y][x] = { broken: null, crack: 0, seed: hash(x, sp.y0 + y, 76) }; } }));
    const [top, bottom] = reefRows(chunk.rows), fair = tables[chunk.id].fair;
    const pick = Math.floor(rng() * fair.length);
    sp.reef = { chunk, top, bottom, xs: fair[pick]?.xs ?? null, pick, frontier: bottom };
  }
  const scene = composeScene(grid, v2Library.objects, seed);
  // Nothing grows out of the brittle reef cells; it is drawn whole in code. Bedrock in reef chunks is
  // plain dark rock only (no pale ruins or sealife), so pale always means breakable.
  scene.seabed = scene.seabed.filter((d) => !reef[d.y]?.[d.x]);
  const darkRocks = [...v2Library.objects.filter((o) => o.family === 'rock').map((o) => o.id), 'boulder-underwater', 'decor-background-rock'];
  const inReef = (y) => spans.some((sp) => sp.reef && y >= sp.y0 && y <= sp.y1);
  const dark = (x, y) => darkRocks[Math.floor(hash(x, y, 77) * darkRocks.length)];
  // Pale arches over reef passages would read as brittle too: their two legs become dark rock instead.
  scene.objects = scene.objects.flatMap((o) => {
    if (!inReef(o.y)) return [o];
    if (o.w === undefined) return [{ ...o, id: dark(o.x, o.y) }];
    return [o.x, o.x + o.w - 1].map((x) => ({ x, y: o.y, id: dark(x, o.y), dir: 'S' }));
  });
  const byRow = Array.from({ length: scene.rows }, () => []);
  for (const o of scene.objects) byRow[o.y].push(o);
  const c = 24, shadow = new OffscreenCanvas((scene.columns + 4) * c, (scene.rows + 4) * c), sctx = shadow.getContext('2d');
  sctx.filter = 'blur(9px)'; sctx.fillStyle = '#04174a';
  for (const b of scene.collision) sctx.fillRect((b.x + 2) * c - 2, (b.y + 2) * c - 2, c + 4, c + 4);
  const fish = Array.from({ length: Math.ceil(scene.rows / 13) }, (_, i) => { const r = mulberry32(seed * 31 + i); return { y: 4 + i * 13 + r() * 6, speed: 0.25 + r() * 0.25, dir: i % 2 ? -1 : 1, phase: r() * 20 }; });
  world = { seed, grid, solid, reef, spans, scene, byRow, shadow: { canvas: shadow, c }, fish };
}
const spanAt = (y) => world.spans.find((sp) => y >= sp.y0 && y < sp.y1 + 1);
/** The parrotfish's line at a world row, or null outside reef chunks. */
function lineAtWorld(y) {
  const sp = spanAt(y);
  if (!sp?.reef?.xs) return null;
  return lineAt(sp.reef.xs, sp.reef.top, sp.reef.bottom, y - sp.y0);
}

// ---------------------------------------------------------------- 3D parrotfish (static concept GLB, transforms only)
const ELEVATION = THREE.MathUtils.degToRad(35), SIN_E = Math.sin(ELEVATION);
const renderer = new THREE.WebGLRenderer({ canvas: eelCanvas, alpha: true, antialias: true });
renderer.outputColorSpace = THREE.SRGBColorSpace;
eelCanvas.classList.add('graded');
const scene3 = new THREE.Scene();
scene3.add(new THREE.AmbientLight(0xffffff, 1.9));
const key = new THREE.DirectionalLight(0xffffff, 1.1); key.position.set(-2, 10, 4); scene3.add(key);
const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 100);
camera.position.set(0, Math.sin(ELEVATION), Math.cos(ELEVATION)).multiplyScalar(30); camera.lookAt(0, 0, 0);
const fishRoot = new THREE.Group(); scene3.add(fishRoot);
const body = new THREE.Group(); fishRoot.add(body);
const gltf = await new GLTFLoader().loadAsync(FISH_URL);
const model = gltf.scene; body.add(model);
model.traverse((o) => {
  if (!o.isMesh) return;
  o.frustumCulled = false;
  const mats = [].concat(o.material).map((m) => new THREE.MeshLambertMaterial({ name: m.name, color: m.color, flatShading: true, vertexColors: !!o.geometry.attributes.color }));
  o.material = Array.isArray(o.material) ? mats : mats[0];
});
// Centre the model on its footprint; its nose points north (-z).
const box = new THREE.Box3().setFromObject(model), size = box.getSize(new THREE.Vector3()), mid = box.getCenter(new THREE.Vector3());
model.position.set(-mid.x, -box.min.y, -mid.z);
const HALF_ROWS = (size.z / 2) * SIN_E; // screen rows from the body's centre to its nose
const shadowTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d'), gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(4,28,58,0.32)'); gr.addColorStop(1, 'rgba(4,28,58,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c); })();
const blob = new THREE.Mesh(new THREE.PlaneGeometry(size.x * 1.3, size.z * 1.1), new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false }));
blob.rotation.x = -Math.PI / 2; blob.position.y = 0.02; blob.renderOrder = -1; fishRoot.add(blob);
// The hook from #23: the harpoon stays pinned on the back, behind the head.
const anchor = new THREE.Object3D(); body.add(anchor); anchor.position.set(0, size.y * 0.85, size.z * 0.12);
const tmp = new THREE.Vector3();

// ---------------------------------------------------------------- layout
let W = 390, H = 844, cell = W / VIEW, dpr = 1;
const reduced = () => $('opt-reduced').checked;
function resize() {
  const wide = $('frame').value === 'wide';
  stage.classList.toggle('wide', wide);
  [W, H] = wide ? [470, 820] : $('frame').value.split('x').map(Number);
  cell = W / VIEW; dpr = Math.min(devicePixelRatio || 1, 3);
  phone.style.width = `${W}px`; phone.style.height = `${H}px`; phone.style.setProperty('--u', `${W / 390}px`);
  const edge = Math.min(cell * 1.6, H * 0.18), margin = edge * 0.22;
  phone.style.setProperty('--arrow', `${edge}px`); phone.style.setProperty('--arrow-margin', `${margin}px`); phone.style.setProperty('--arrow-bottom', `${margin * 1.6}px`);
  for (const c of [worldCanvas, fxCanvas]) { c.width = W * dpr; c.height = H * dpr; }
  renderer.setPixelRatio(dpr); renderer.setSize(W, H, false);
  const halfW = VIEW / 2, halfH = halfW * H / W;
  Object.assign(camera, { left: -halfW, right: halfW, top: halfH, bottom: -halfH });
  camera.updateProjectionMatrix(); camera.updateMatrixWorld();
}
$('frame').addEventListener('change', resize);
const toScreen = (v) => { const p = v.clone().project(camera); return { x: (p.x + 1) / 2 * W, y: (1 - p.y) / 2 * H }; };
function roundedTriangle(side, radius = 46, round = 11) {
  const corners = [0, 1, 2].map((i) => { const a = (side > 0 ? 0 : Math.PI) + i * Math.PI * 2 / 3; return [Math.cos(a) * (radius - round * 2), Math.sin(a) * (radius - round * 2)]; });
  const pts = [];
  for (const [cx, cy] of corners) { const st = Math.atan2(cy, cx) - Math.PI / 3; for (let s = 0; s <= 6; s++) { const a = st + s * Math.PI * 2 / 3 / 6; pts.push(`${(cx + Math.cos(a) * round).toFixed(2)},${(cy + Math.sin(a) * round).toFixed(2)}`); } }
  return pts.join(' ');
}
const zones = { [-1]: $('zone-left'), [1]: $('zone-right') };
for (const side of [-1, 1]) for (const poly of zones[side].querySelectorAll('polygon')) poly.setAttribute('points', roundedTriangle(side));

// ---------------------------------------------------------------- rules (mirrors the planned Godot pursuit)
// phase: pursuit -> caught (cutscene) -> award (first discovery only) -> results (Restaurant)
//        pursuit -> escaped (hull gone) -> results
let run;
function restart() {
  buildWorld(Number($('seed').value), $('force').value);
  // The chase starts at the top of the start chunk: the arena's handoff in the game.
  const start = world.spans[1].y0 + 0.5;
  run = { phase: 'pursuit', t: 0, y: start, x: 5.5, vx: 0, steer: 0, hull: rules.hull_max, protection: 0, salvage: 6, collected: [],
    resistance: rules.resistance, fishX: 5.5, yaw: 0, speed: 1, slowT: 0, impacts: 0, crashes: 0, smashed: 0, phaseT: 0, paused: false,
    discovered: true, released: false, toldPath: false };
  camX = 5.5; tilt = 0; hurt = 0; lunge = 0; knock = { x: 0, y: 0 }; particles.length = 0; snap = null;
  fishRoot.scale.setScalar(1); fishRoot.rotation.set(0, 0, 0);
  hideOverlays(); banner.hidden = true; setPhase('pursuit');
  showBanner('Hooked!<small>Reel it in. Dodge the rocks!</small>', 'pursuit', 1800);
  hudIntro(); syncRules();
}
function setPhase(p) { run.phase = p; run.phaseT = 0; phone.dataset.phase = p; }
const reach = rules.ship_radius;
const collides = (x, y, r) => hits(world.solid, x, y, r, rules);
const OFFSETS = []; for (let iy = 0; iy <= 20; iy++) for (let ix = -60; ix <= 60; ix++) OFFSETS.push([ix * 0.05, iy * 0.1]);
OFFSETS.sort((a, b) => a[0] ** 2 + a[1] ** 2 - b[0] ** 2 - b[1] ** 2);
function nearestClear(x, y, r) {
  for (const [dx, dy] of OFFSETS) { const px = x + dx, py = y + dy; if (px < 0.4 || px > COLUMNS - 0.4) continue; if (!collides(px, py, r)) return { x: px, y: py }; }
  return { x, y };
}
const moveToward = (v, to, d) => (Math.abs(to - v) <= d ? to : v + Math.sign(to - v) * d);
/** Shatter one brittle cell: its collision goes now. */
function shatter(x, y, by) {
  const c = world.reef[y]?.[x];
  if (!c || c.broken) return false;
  // The piece it was drawn as when it broke picks its break animation (neighbours round off at once).
  c.breakId = reefId(x, y, c.seed); c.brokenAt = run.t;
  c.broken = by; world.solid[y][x] = '.';
  return true;
}
/** The parrotfish's nose row: it rams every breach row it reaches. */
const noseRow = () => run.y - rules.lead_rows - HALF_ROWS;

function step(dt) {
  run.t += dt; run.phaseT += dt;
  const ev = [];
  if (run.phase === 'pursuit') {
    const ramp = Math.min(rules.pursuit_speed_multiplier, 1 + (rules.pursuit_speed_multiplier - 1) * run.t / rules.pursuit_ramp_seconds);
    run.slowT = Math.max(0, run.slowT - dt);
    const slow = run.slowT > 0 ? R().slow_multiplier + (1 - R().slow_multiplier) * (1 - run.slowT / R().slow_seconds) ** 2 : 1;
    run.speed = ramp * slow;
    run.y -= rules.forward_rows_per_second * run.speed * dt;
    run.protection = Math.max(0, run.protection - dt);
    run.vx = moveToward(run.vx, run.steer * rules.lateral_columns_per_second, rules.lateral_acceleration * dt);
    run.x += run.vx * dt;
    if (run.x < 0.4 || run.x > COLUMNS - 0.4) { run.x = Math.max(0.4, Math.min(COLUMNS - 0.4, run.x)); run.vx = 0; }
    ev.push(...stepReef());
    world.scene.pickups.forEach((g, i) => {
      if (run.collected.includes(i) || Math.abs(g.x - run.x) > rules.pickup_radius || Math.abs(g.y - run.y) > rules.pickup_radius) return;
      run.collected.push(i); run.salvage += rules.salvage_per_pickup; ev.push({ type: 'pickup', x: g.x, y: g.y });
    });
    if (collides(run.x, run.y, reach)) {
      // Brittle reef shatters under the hull: hull damage once per hit protection and a short slowdown, no knock-back.
      const near = [];
      for (let cy = Math.floor(run.y - 1.5); cy <= Math.floor(run.y + 1.5); cy++) for (let cx = Math.floor(run.x - 1.5); cx <= Math.floor(run.x + 1.5); cx++) {
        const c = world.reef[cy]?.[cx];
        if (c && !c.broken && rockDistance(world.solid, cx, cy, run.x, run.y, rules) < reach + 0.04) near.push([cx, cy]);
      }
      if (near.length) {
        for (const [cx, cy] of near) shatter(cx, cy, 'ship');
        run.crashes++; run.slowT = R().slow_seconds;
        const hurtNow = run.protection <= 0 && R().reef_damage > 0;
        if (hurtNow) { run.hull = Math.max(0, run.hull - R().reef_damage); run.protection = rules.hit_protection_seconds; run.impacts++; }
        ev.push({ type: 'crash', cells: near, hurt: hurtNow, x: run.x, y: run.y });
      }
      if (collides(run.x, run.y, reach)) {
        // Bedrock and ordinary rock are solid: knock back to the nearest clear water; only the first touch dents the hull.
        const from = { x: run.x, y: run.y }, to = nearestClear(run.x, run.y, reach + rules.knockback_clearance);
        run.x = to.x; run.y = to.y; run.vx = 0;
        if (run.protection <= 0) {
          run.hull = Math.max(0, run.hull - rules.impact_damage); run.protection = rules.hit_protection_seconds; run.impacts++;
          ev.push({ type: 'impact', from, to });
        } else ev.push({ type: 'bump', from, to });
      }
      if (run.hull <= 0) { ev.push({ type: 'hull_gone' }); return ev; }
    }
    // Resistance is the creature's health: it only drains, never refills.
    if (!$('opt-hold').checked) run.resistance = Math.max(0, run.resistance - rules.resistance_drain_per_second * dt);
    if (run.resistance <= 0) ev.push({ type: 'caught' });
  } else if (run.phase === 'caught') {
    run.speed = Math.max(0, run.speed - dt * 2);
    run.y -= rules.forward_rows_per_second * run.speed * dt;
    run.vx = 0;
    if (!run.released && run.phaseT >= RETRACT_START) { run.released = true; ev.push({ type: 'harpoon_released' }); }
    if (run.phaseT >= rules.catch_cutscene_seconds) ev.push({ type: 'cutscene_done' });
  } else if (run.phase === 'escaped') {
    run.speed = Math.max(0, run.speed - dt * 1.5);
    run.y -= rules.forward_rows_per_second * run.speed * dt;
    if (run.phaseT >= rules.escape_seconds) ev.push({ type: 'escape_done' });
  }
  return ev;
}

// ---------------------------------------------------------------- reef (mirrors the planned Godot rules)
const crackRows = () => R().crack_seconds * rules.forward_rows_per_second * rules.pursuit_speed_multiplier;
function stepReef() {
  const ev = [], ny = noseRow();
  for (const sp of world.spans) {
    const rf = sp.reef;
    if (!rf?.xs) continue;
    if (!run.toldPath && ny < sp.y1 + 1 && ny > sp.y0) { run.toldPath = true; ev.push({ type: 'first_reef' }); }
    // Rows the nose has reached shatter along the breach; the next ones crack first.
    while (rf.frontier >= rf.top && ny <= sp.y0 + rf.frontier + 1) {
      const y = sp.y0 + rf.frontier, cells = breachCells(rf.xs[rf.bottom - rf.frontier], R().breach_columns).filter((x) => shatter(x, y, 'fish'));
      if (cells.length) { run.smashed += cells.length; ev.push({ type: 'smash', y, cells, first: rf.frontier === rf.bottom }); }
      rf.frontier--;
    }
    for (let r = rf.frontier; r >= Math.max(rf.top, rf.frontier - 3); r--) {
      const y = sp.y0 + r, k = R().crack_seconds > 0 ? Math.max(0, Math.min(1, 1 - (ny - (y + 1)) / crackRows())) : 0;
      for (const x of breachCells(rf.xs[rf.bottom - r], R().breach_columns)) { const c = world.reef[y][x]; if (c && !c.broken) c.crack = k; }
    }
  }
  return ev;
}

function handle(events) {
  for (const e of events) {
    if (e.type === 'pickup') for (let i = 0; i < 6; i++) emitSpark(e.x, e.y - 0.15);
    if (e.type === 'impact') { damage(e.from, e.to); hit(rules.impact_damage); }
    if (e.type === 'bump') knock = { x: knock.x + e.from.x - e.to.x, y: knock.y + e.from.y - e.to.y };
    if (e.type === 'smash') { lunge = 1; for (const x of e.cells) debris(x + 0.5, e.y + 0.5, 7, 1); e.first ? sfx('reef_breach', 1) : sfx('reef_smash', 0.55, 0.12); }
    if (e.type === 'crash') {
      // Ramming reef must be unmistakable: the same red hit as rock, plus a jolt and the hull's own crunch.
      for (const [x, y] of e.cells) debris(x + 0.5, y + 0.5, 9, 1.1);
      const [cx, cy] = e.cells.reduce(([a, b], [x, y]) => [a + x + 0.5, b + y + 0.5], [0, 0]).map((v) => v / e.cells.length);
      if (e.hurt) { damage({ x: e.x + (cx - e.x) * 0.5, y: e.y + (cy - e.y) * 0.5 }, { x: e.x, y: e.y }); hit(R().reef_damage); sfx('reef_crash', 1); }
      else { shakeT = Math.max(shakeT, 0.2); knock = { x: knock.x + (e.x - cx) * 0.12, y: knock.y + 0.12 }; sfx('reef_crash', 0.45); }
    }
    if (e.type === 'first_reef') showBanner('Reef ahead!<small>Follow the broken path</small>', 'pursuit', 2200);
    if (e.type === 'caught') {
      setPhase('caught'); held.clear(); updateSteer();
      catchFrom = { x: fishRoot.position.x, z: fishRoot.position.z };
      showBanner(`Caught!<small>Boulderhead Parrotfish${run.discovered ? ' · first catch' : ''}</small>`, 'caught', rules.catch_cutscene_seconds * 1000);
      for (let i = 0; i < 26; i++) emitBubble(run.fishX + (Math.random() - 0.5) * 2, run.y - rules.lead_rows + (Math.random() - 0.2) * 2, { vy: -0.6 - Math.random(), vx: (Math.random() - 0.5) * 1.2, r: 0.04 + Math.random() * 0.05, life: 1.6 + Math.random(), rise: 0.6 });
    }
    if (e.type === 'harpoon_released') {
      anchor.getWorldPosition(tmp); const p = toScreen(tmp), { ox, oy } = origin();
      const wx = (p.x - ox) / cell, wy = (p.y - oy) / cell;
      for (let i = 0; i < 8; i++) emitSpark(wx, wy, '#fff3c4', 1.2);
    }
    if (e.type === 'cutscene_done') { banner.hidden = true; run.discovered ? openAward() : openResults('complete'); }
    if (e.type === 'hull_gone') {
      setPhase('escaped'); held.clear(); updateSteer();
      snap = { t: 0 }; showBanner('It got away<small>Hull depleted</small>', 'escaped', rules.escape_seconds * 1000 + 400);
    }
    if (e.type === 'escape_done') { banner.hidden = true; openResults('hull_depleted'); }
  }
}

// ---------------------------------------------------------------- overlays
function hideOverlays() { scrim.hidden = true; for (const c of Object.values(cards)) c.hidden = true; }
function show(card) { scrim.hidden = false; for (const [n, c] of Object.entries(cards)) c.hidden = n !== card; }
let bannerTimer = 0;
function showBanner(html, phase, ms) {
  banner.innerHTML = html; banner.hidden = false; banner.style.animation = 'none'; void banner.offsetWidth; banner.style.animation = '';
  clearTimeout(bannerTimer); bannerTimer = setTimeout(() => { if (run.phase === phase) banner.hidden = true; }, ms);
}
function openAward() {
  setPhase('award');
  const node = $('award-template').content.firstElementChild.cloneNode(true);
  node.querySelector('.award-backdrop').src = BACKDROP_URL; node.querySelector('.coin').src = COIN_URL;
  cards.award.replaceChildren(node);
  node.querySelector('.award-continue').addEventListener('click', () => openResults('complete'));
  show('award'); node.querySelector('.award-continue').focus();
}
function fillResults(root, outcome, pickups) {
  const done = outcome === 'complete', bonus = done ? rules.completion_bonus : 0;
  root.querySelector('h2').textContent = done ? 'Expedition complete' : 'Hull depleted';
  root.querySelector('#r-pickups').textContent = pickups;
  for (const n of [root.querySelector('#r-bonus-label'), root.querySelector('#r-bonus')]) n.hidden = !done;
  root.querySelector('#r-bonus').textContent = `+${bonus}`;
  root.querySelector('#r-total').textContent = pickups + bonus;
}
function openResults(outcome) { setPhase('results'); fillResults(cards.results, outcome, run.salvage); show('results'); $('restaurant').focus(); }
// Restaurant leaves the expedition; this review restarts the chase instead.
$('restaurant').addEventListener('click', restart);
function pause() {
  if (run.paused || run.phase !== 'pursuit') return;
  run.paused = true; held.clear(); updateSteer(); show('paused'); $('resume').focus();
}
$('pause').addEventListener('click', pause);
$('resume').addEventListener('click', () => { run.paused = false; hideOverlays(); });
$('return-early').addEventListener('click', () => { run.paused = false; setPhase('results'); fillResults(cards.results, 'returned_early', run.salvage); cards.results.querySelector('h2').textContent = 'Returned early'; show('results'); });
$('restart').addEventListener('click', restart);
$('skip-catch').addEventListener('click', () => { if (run.phase === 'pursuit') run.resistance = Math.min(run.resistance, 3); });
$('low-hull').addEventListener('click', () => { if (run.phase === 'pursuit') run.hull = Math.min(run.hull, 25); });
$('opt-reduced').addEventListener('change', () => phone.classList.toggle('reduced', reduced()));
let hudAt = 0;
function hudIntro() {
  phone.dataset.hud = 'travel'; hudAt = Infinity;
  void phone.offsetWidth;
  setTimeout(() => { if (phone.dataset.hud === 'travel') { phone.dataset.hud = 'versus'; hudAt = performance.now(); } }, 600);
}
const hudFill = () => { const k = Math.max(0, Math.min(1, (performance.now() - hudAt - 450) / 600)); return reduced() ? (performance.now() >= hudAt ? 1 : 0) : 1 - (1 - k) ** 3; };
for (const id of ['seed', 'force']) $(id).addEventListener('change', restart);
$('next-reef').addEventListener('click', () => {
  if (run.phase !== 'pursuit') return;
  const next = world.spans.filter((sp) => sp.reef && sp.y0 + sp.reef.bottom < run.y - 3).sort((a, b) => b.y0 - a.y0)[0];
  if (!next) return;
  // Arrive a few rows before the reef wall, centred on the breach's entry.
  run.y = next.y1 + 1 + rules.lead_rows * 0.6; run.x = next.reef.xs[0]; run.vx = 0; run.protection = 0;
  ({ x: run.x, y: run.y } = nearestClear(run.x, run.y, reach + rules.knockback_clearance)); camX = Math.max(3.5, Math.min(7.5, run.x)); run.fishX = run.x;
});
for (const tab of document.querySelectorAll('[role="tab"]')) tab.addEventListener('click', () => {
  for (const t of document.querySelectorAll('[role="tab"]')) t.setAttribute('aria-selected', String(t === tab));
  for (const v of document.querySelectorAll('.view')) v.hidden = v.id !== tab.dataset.view;
});

// ---------------------------------------------------------------- input
const held = new Map(), keys = { ArrowLeft: false, ArrowRight: false };
function updateSteer() {
  let v = 0;
  for (const side of held.values()) v += side;
  v += (keys.ArrowRight ? 1 : 0) - (keys.ArrowLeft ? 1 : 0);
  run.steer = run.paused || run.phase !== 'pursuit' ? 0 : Math.max(-1, Math.min(1, v));
  for (const side of [-1, 1]) zones[side].classList.toggle('down', run.steer * side > 0);
}
for (const side of [-1, 1]) {
  const zone = zones[side];
  zone.addEventListener('pointerdown', (e) => { zone.setPointerCapture(e.pointerId); held.set(e.pointerId, side); updateSteer(); e.preventDefault(); });
  zone.addEventListener('pointermove', (e) => { if (!held.has(e.pointerId)) return; const r = phone.getBoundingClientRect(); held.set(e.pointerId, e.clientX < r.left + r.width / 2 ? -1 : 1); updateSteer(); });
  for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) zone.addEventListener(type, (e) => { held.delete(e.pointerId); updateSteer(); });
}
addEventListener('keydown', (e) => { if (e.key in keys && !e.repeat) { keys[e.key] = true; updateSteer(); e.preventDefault(); } if (e.key === 'Escape') pause(); });
addEventListener('keyup', (e) => { if (e.key in keys) { keys[e.key] = false; updateSteer(); } });
addEventListener('blur', () => { held.clear(); keys.ArrowLeft = keys.ArrowRight = false; updateSteer(); });

// ---------------------------------------------------------------- sound (audio/generate_reef_audio.py)
// The browser only starts audio after a gesture, so the context resumes on the first key or touch.
const audio = new AudioContext(), buffers = {}, lastPlayed = {}, played = [];
for (const name of ['reef_breach', 'reef_smash', 'reef_crash']) {
  fetch(new URL(`./audio/${name}.wav`, import.meta.url).href).then((r) => r.arrayBuffer()).then((b) => audio.decodeAudioData(b)).then((d) => { buffers[name] = d; });
}
for (const type of ['pointerdown', 'keydown']) addEventListener(type, () => audio.state !== 'running' && audio.resume(), { capture: true });
function sfx(name, gain = 1, jitter = 0.05) {
  played.push(name);
  if (!$('opt-sound').checked || !buffers[name] || audio.state !== 'running') return;
  // Rows break about three times a second; overlapping copies closer than 90 ms only smear.
  const now = audio.currentTime; if (now - (lastPlayed[name] ?? -1) < 0.09) return; lastPlayed[name] = now;
  const src = audio.createBufferSource(), g = audio.createGain();
  src.buffer = buffers[name]; src.playbackRate.value = 1 + (Math.random() * 2 - 1) * jitter; g.gain.value = gain;
  src.connect(g).connect(audio.destination); src.start();
}

// ---------------------------------------------------------------- particles and hit feedback
const particles = [];
const bubbleSprite = (() => {
  const size = 64, c = new OffscreenCanvas(size, size), g = c.getContext('2d'), r = size / 2 - 2;
  const f = g.createRadialGradient(size * 0.45, size * 0.42, r * 0.1, size / 2, size / 2, r);
  f.addColorStop(0, 'rgba(210,248,255,.08)'); f.addColorStop(0.75, 'rgba(190,240,255,.22)'); f.addColorStop(1, 'rgba(235,252,255,.85)');
  g.fillStyle = f; g.beginPath(); g.arc(size / 2, size / 2, r, 0, Math.PI * 2); g.fill();
  g.fillStyle = 'rgba(255,255,255,.95)'; g.beginPath(); g.ellipse(size * 0.36, size * 0.33, r * 0.26, r * 0.17, -0.6, 0, Math.PI * 2); g.fill();
  return c;
})();
function emitBubble(x, y, { vx = 0, vy = 0, r = 0.05, life = 2, rise = 0.4, drag = 2.2 } = {}) { particles.push({ kind: 'bubble', x, y, vx, vy, r, life, age: 0, rise, drag, wob: 0.04, freq: 3 + Math.random() * 4, phase: Math.random() * 6.3 }); }
function emitSpark(x, y, color = '#ffe58a', speed = 1) { const a = Math.random() * Math.PI * 2, s = (0.6 + Math.random() * 1.4) * speed; particles.push({ kind: 'spark', x, y, color, vx: Math.cos(a) * s, vy: Math.sin(a) * s - 0.3, r: 0.035 + Math.random() * 0.03, life: 0.45 + Math.random() * 0.3, age: 0, drag: 3.5 }); }
/** Reef fragments burst out of a shattered cell and settle; cosmetic only, they never collide. */
function debris(x, y, n, power) {
  if (breakSheets()) n = Math.ceil(n / 4);   // the break sheet draws the chunks; a few code shards add spray
  if (reduced()) n = Math.ceil(n / 3);
  for (let i = 0; i < n; i++) {
    const a = Math.random() * Math.PI * 2, s = (0.8 + Math.random() * 1.8) * power;
    particles.push({ kind: 'shard', x: x + (Math.random() - 0.5) * 0.6, y: y + (Math.random() - 0.5) * 0.6, vx: Math.cos(a) * s, vy: Math.sin(a) * s, r: 0.07 + Math.random() * 0.09, life: 0.9 + Math.random() * 0.6, age: 0, drag: 4, spin: (Math.random() - 0.5) * 14, tone: Math.random() });
  }
  for (let i = 0; i < 4; i++) emitBubble(x + (Math.random() - 0.5) * 0.8, y, { vx: (Math.random() - 0.5), vy: -0.3 - Math.random() * 0.5, r: 0.03 + Math.random() * 0.04, life: 1.2, rise: 0.45 });
  particles.push({ kind: 'puff', x, y, life: 0.7, age: 0, vx: 0, vy: 0, drag: 0 });
}
let hitstop = 0, tilt = 0, hurt = 0, lunge = 0, knock = { x: 0, y: 0 }, shakeT = 0, flashT = 0, snap = null, catchFrom = null, camX = 5.5;
function damage(from, to) {
  hurt = 1; knock = { x: knock.x + from.x - to.x, y: knock.y + from.y - to.y };
  if (reduced()) return;
  const d = Math.hypot(from.x - to.x, from.y - to.y) || 1, ax = (from.x - to.x) / d, ay = (from.y - to.y) / d;
  for (let i = 0; i < 14; i++) emitSpark(from.x + ax * 0.35, from.y + ay * 0.35 - 0.2, `hsl(${30 + Math.random() * 20} 100% 60%)`, 1.8);
  for (let i = 0; i < 8; i++) emitBubble(from.x + (Math.random() - 0.5) * 0.4, from.y, { vx: (Math.random() - 0.5) * 1.2, vy: -0.3 - Math.random() * 0.4, r: 0.03 + Math.random() * 0.04, life: 1 + Math.random() * 0.5, rise: 0.45 });
}
/** Every hull loss: red screen edge, hit-stop, shake, the hull bar flashes and the loss floats off the ship. */
const popups = [];
function hit(amount) {
  hurt = 1; flashT = 1; shakeT = 0.4; if (!reduced()) hitstop = 0.07;
  const pill = $('hull'); pill.classList.remove('hit'); void pill.offsetWidth; pill.classList.add('hit');
  popups.push({ text: `−${amount}`, x: run.x, y: run.y - 0.9, age: 0 });
}
function stepParticles(dt) {
  for (const p of popups) p.age += dt;
  while (popups.length && popups[0].age > 0.9) popups.shift();
  for (const p of particles) { p.age += dt; const k = Math.exp(-p.drag * dt); p.vx *= k; p.vy *= k; if (p.kind === 'bubble') p.vy -= p.rise * dt * 1.6; p.x += p.vx * dt; p.y += p.vy * dt; }
  for (let i = particles.length - 1; i >= 0; i--) if (particles[i].age >= particles[i].life) particles.splice(i, 1);
}
function drawParticles(ctx, ox, oy) {
  for (const p of particles) {
    const t = p.age / p.life, x = ox + p.x * cell, y = oy + p.y * cell;
    if (p.kind === 'bubble') { const r = p.r * (1 + 0.3 * t) * cell; ctx.globalAlpha = Math.min(1, p.age * 8) * (1 - t * t); ctx.drawImage(bubbleSprite, x + Math.sin(p.age * p.freq + p.phase) * p.wob * cell - r, y - r, r * 2, r * 2); }
    else if (p.kind === 'shard') {
      const r = p.r * cell, a = p.age * p.spin, lift = Math.sin(Math.min(1, t * 1.6) * Math.PI) * cell * 0.25;
      ctx.globalAlpha = t > 0.75 ? (1 - t) / 0.25 : 1; ctx.fillStyle = p.tone < 0.5 ? '#efe4c9' : '#cdb78f'; ctx.strokeStyle = '#7d6a4b'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x + Math.cos(a) * r, y - lift + Math.sin(a) * r); ctx.lineTo(x + Math.cos(a + 2.2) * r * 0.8, y - lift + Math.sin(a + 2.2) * r * 0.8); ctx.lineTo(x + Math.cos(a + 4) * r * 0.9, y - lift + Math.sin(a + 4) * r * 0.9); ctx.closePath(); ctx.fill(); ctx.stroke();
    } else if (p.kind === 'puff') {
      const r = cell * (0.5 + t * 0.9); ctx.globalAlpha = 0.45 * (1 - t);
      const g = ctx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, 'rgba(240,232,210,.9)'); g.addColorStop(1, 'rgba(240,232,210,0)'); ctx.fillStyle = g; ctx.fillRect(x - r, y - r, r * 2, r * 2);
    } else { ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = 1 - t; ctx.fillStyle = p.color; ctx.beginPath(); ctx.arc(x, y, p.r * cell * (1 - t * 0.5), 0, Math.PI * 2); ctx.fill(); ctx.restore(); }
  }
  ctx.globalAlpha = 1;
}
const tintCanvas = document.createElement('canvas'), tctx = tintCanvas.getContext('2d');

// ---------------------------------------------------------------- drawing
const topRow = () => Math.max(0, run.y + knock.y - H * 0.74 / cell);
const origin = () => {
  const s = shakeT > 0 && !reduced() ? shakeT / 0.35 : 0;
  return { ox: W / 2 - camX * cell + Math.sin(performance.now() * 0.071) * s * cell * 0.08, oy: -topRow() * cell + Math.cos(performance.now() * 0.053) * s * cell * 0.08 };
};
// Brittle reef placeholder: pale cracked limestone blocks with branching white coral on some. Bedrock keeps the
// approved rock art, so the two read apart. Each block is drawn on its collision shape (the #24 rounded square):
// open faces inset by rock_inset, faces against rock flat, and exposed corners rounded by rock_corner_radius. So
// as soon as a neighbour breaks, the corners it exposes round off and the breach looks as wide as it flies.
const REEF_H = 0.26;
const isReef = (x, y) => { const c = world.reef[y]?.[x]; return !!c && !c.broken; };
const solidAt = (x, y) => x < 0 || x >= COLUMNS || world.solid[y]?.[x] === '#';
// Neighbour mask as the seabed beds: N=1, E=2, S=4, W=8, set when that side is solid (reef or rock).
const neighbourMask = (x, y) => (solidAt(x, y - 1) ? 1 : 0) | (solidAt(x + 1, y) ? 2 : 0) | (solidAt(x, y + 1) ? 4 : 0) | (solidAt(x - 1, y) ? 8 : 0);
function footprint(ctx, x0, y0, x1, y1, radii) { ctx.beginPath(); ctx.roundRect(x0, y0, x1 - x0, y1 - y0, radii); }
function drawReefCell(ctx, ox, oy, x, y, time) {
  const c = world.reef[y][x], s = c.seed, px = ox + x * cell, py = oy + y * cell;
  const jit = c.crack > 0.55 && !reduced() ? Math.sin(time * 70 + s * 40) * cell * 0.02 * c.crack : 0;
  if (modelArt()) {
    const id = reefId(x, y, s);
    // Cracking cells show the sheet's crack stages, spreading from the impact point; the static piece otherwise.
    if (c.crack > 0 && breakSheets() && reefBreak[id]) reefSprite(ctx, id, px + cell / 2, py + cell / 2, jit, Math.min(CRACK_FRAMES - 1, Math.floor(c.crack * CRACK_FRAMES)));
    else {
      reefSprite(ctx, id, px + cell / 2, py + cell / 2, jit);
      // Without sheets, code-drawn cracks sit on the top face, about a quarter cell above the ground centre.
      if (c.crack > 0) cracks(ctx, px + cell / 2 + jit, py + cell * 0.24, c.crack, s);
    }
    return;
  }
  const h = cell * (REEF_H + (s - 0.5) * 0.06);
  const L = solidAt(x - 1, y), Rt = solidAt(x + 1, y), U = solidAt(x, y - 1), D = solidAt(x, y + 1);
  const ins = rules.rock_inset * cell, rad = rules.rock_corner_radius * cell;
  const x0 = px + (L ? 0 : ins) + jit, x1 = px + cell - (Rt ? 0 : ins) + jit, y0 = py + (U ? 0 : ins), y1 = py + cell - (D ? 0 : ins);
  const radii = [!L && !U ? rad : 0, !Rt && !U ? rad : 0, !Rt && !D ? rad : 0, !L && !D ? rad : 0];
  // Sides: the footprint swept up to the top face.
  ctx.fillStyle = '#b39a70';
  for (const k of [0, 0.34, 0.67]) { footprint(ctx, x0, y0 - h * k, x1, y1 - h * k, radii); ctx.fill(); }
  ctx.fillStyle = 'rgba(70,50,25,.2)'; footprint(ctx, x0, y0, x1, y1, radii); ctx.fill();
  // Top face: two slabs of different tone, clipped to the rounded shape.
  const t0 = y0 - h, t1 = y1 - h;
  const split = 0.3 + hash(x, y, 81) * 0.4, vertical = hash(x, y, 82) < 0.5;
  const tones = ['#ece2c8', '#e2d5b6', '#f3ead4'];
  ctx.save(); footprint(ctx, x0, t0, x1, t1, radii); ctx.clip();
  ctx.fillStyle = tones[Math.floor(s * 3)]; ctx.fillRect(x0, t0, x1 - x0, t1 - t0);
  ctx.fillStyle = tones[(Math.floor(s * 3) + 1) % 3];
  if (vertical) ctx.fillRect(x0 + (x1 - x0) * split, t0, (x1 - x0) * (1 - split), t1 - t0); else ctx.fillRect(x0, t0 + (t1 - t0) * split, x1 - x0, (t1 - t0) * (1 - split));
  ctx.strokeStyle = 'rgba(120,96,60,.5)'; ctx.lineWidth = Math.max(1, cell / 70); ctx.beginPath();
  if (vertical) { ctx.moveTo(x0 + (x1 - x0) * split, t0); ctx.lineTo(x0 + (x1 - x0) * split, t1); } else { ctx.moveTo(x0, t0 + (t1 - t0) * split); ctx.lineTo(x1, t0 + (t1 - t0) * split); }
  ctx.stroke();
  // Bevels: a lit rim on open top faces and a shaded one on open bottoms.
  ctx.lineWidth = cell * 0.05;
  if (!U) { ctx.strokeStyle = 'rgba(255,255,255,.4)'; footprint(ctx, x0, t0, x1, t1 + cell, radii); ctx.stroke(); }
  if (!D) { ctx.strokeStyle = 'rgba(110,85,50,.25)'; footprint(ctx, x0, t0 - cell, x1, t1, radii); ctx.stroke(); }
  ctx.restore();
  // Outline only along open faces.
  ctx.strokeStyle = 'rgba(120,96,60,.55)'; ctx.lineWidth = Math.max(1, cell / 70);
  if (!L || !Rt || !U || !D) { ctx.save(); footprint(ctx, x0, t0, x1, y1, radii); ctx.clip(); footprint(ctx, x0 - (L ? cell : 0), t0 - (U ? cell : 0), x1 + (Rt ? cell : 0), y1 + (D ? cell : 0), radii); ctx.stroke(); ctx.restore(); }
  if (hash(x, y, 83) < 0.3) coral(ctx, (x0 + x1) / 2 + (hash(x, y, 84) - 0.5) * cell * 0.3, t0 + (t1 - t0) * 0.6, cell * 0.36, x * 7 + y, hash(x, y, 85) < 0.75 ? '#f6efe2' : '#e98aa3');
  if (c.crack > 0) cracks(ctx, (x0 + x1) / 2, (t0 + t1) / 2, c.crack, s);
}
function coral(ctx, x, y, size, salt, color) {
  const rng = mulberry32(salt * 13 + 5);
  ctx.save(); ctx.lineCap = 'round';
  const branch = (bx, by, a, len, w, d) => {
    const ex = bx + Math.cos(a) * len, ey = by + Math.sin(a) * len;
    ctx.strokeStyle = 'rgba(80,60,40,.35)'; ctx.lineWidth = w + 2; ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(ex, ey); ctx.stroke();
    ctx.strokeStyle = color; ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(ex, ey); ctx.stroke();
    if (d > 0) { branch(ex, ey, a - 0.5 - rng() * 0.3, len * 0.7, w * 0.75, d - 1); branch(ex, ey, a + 0.5 + rng() * 0.3, len * 0.7, w * 0.75, d - 1); }
  };
  for (const a of [-Math.PI / 2 - 0.5, -Math.PI / 2 + 0.1, -Math.PI / 2 + 0.6]) branch(x, y, a + (rng() - 0.5) * 0.3, size * 0.45, size * 0.12, 2);
  ctx.restore();
}
function cracks(ctx, x, y, k, s) {
  const rng = mulberry32(Math.floor(s * 1e6));
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  for (let i = 0; i < 5; i++) {
    let a = (i / 5) * Math.PI * 2 + rng(), px = x, py = y;
    const pts = [[px, py]];
    for (let j = 0; j < 3; j++) { a += (rng() - 0.5) * 0.9; px += Math.cos(a) * cell * 0.17 * k; py += Math.sin(a) * cell * 0.17 * k; pts.push([px, py]); }
    for (const [w, col] of [[3.4, 'rgba(60,40,20,.45)'], [1.6, '#ffffff']]) { ctx.strokeStyle = col; ctx.lineWidth = w * (cell / 56); ctx.beginPath(); pts.forEach(([u, v], n) => (n ? ctx.lineTo(u, v) : ctx.moveTo(u, v))); ctx.stroke(); }
  }
  ctx.restore();
}
/** Rubble left on the seabed of a shattered cell. */
function drawRubble(ctx, ox, oy, x, y) {
  const rng = mulberry32(x * 131 + y * 977);
  for (let i = 0; i < 5; i++) {
    const px = ox + (x + 0.15 + rng() * 0.7) * cell, py = oy + (y + 0.2 + rng() * 0.65) * cell, r = cell * (0.05 + rng() * 0.06);
    ctx.fillStyle = 'rgba(10,40,80,.25)'; ctx.beginPath(); ctx.ellipse(px + r * 0.2, py + r * 0.5, r * 1.1, r * 0.6, 0, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = rng() < 0.5 ? '#e6dabd' : '#cbb68f'; ctx.beginPath(); ctx.moveTo(px - r, py); ctx.lineTo(px - r * 0.2, py - r * 0.8); ctx.lineTo(px + r, py - r * 0.2); ctx.lineTo(px + r * 0.4, py + r * 0.5); ctx.closePath(); ctx.fill();
  }
}
function drawWorld(time) {
  const ctx = wctx; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const { scene } = world, { ox, oy } = origin(), tr = topRow();
  const top = Math.max(0, Math.floor(tr) - 1), bottom = Math.min(scene.rows - 1, Math.ceil(tr + H / cell) + 3);
  ctx.fillStyle = '#0b2f63'; ctx.fillRect(0, 0, W, H);
  for (let y = top; y <= bottom; y++) for (let x = 0; x < scene.columns; x++) piece(ctx, 'floor-underwater', 'S', ox + x * cell, oy + y * cell, cell + 0.5, time);
  ctx.strokeStyle = 'rgba(190,245,255,.22)'; ctx.lineWidth = Math.max(1, cell / 60); ctx.beginPath();
  for (let x = 0; x <= scene.columns; x++) { ctx.moveTo(ox + x * cell, oy + top * cell); ctx.lineTo(ox + x * cell, oy + (bottom + 1) * cell); }
  for (let y = top; y <= bottom + 1; y++) { ctx.moveTo(ox, oy + y * cell); ctx.lineTo(ox + scene.columns * cell, oy + y * cell); }
  ctx.stroke();
  const { canvas: sh, c } = world.shadow, k = cell / c;
  ctx.globalAlpha = 0.55; ctx.drawImage(sh, ox - 2 * cell + cell * 0.1, oy - 2 * cell + cell * 0.16, sh.width * k, sh.height * k); ctx.globalAlpha = 1;
  for (const f of world.fish) { const span = scene.columns + 4, head = ((f.phase + time * f.speed) % span + span) % span - 2; piece(ctx, 'decor-background-fish', f.dir > 0 ? 'E' : 'W', ox + (f.dir > 0 ? head : scene.columns - head) * cell, oy + f.y * cell, cell, time, { atRoot: true, salt: f.phase * 7 }); }
  for (const d of scene.seabed) if (d.y >= top && d.y <= bottom) piece(ctx, d.id, d.dir, ox + (d.x + 0.5) * cell, oy + (d.y + 0.5) * cell, cell, time, { atRoot: true, scale: d.scale ?? 1 });
  for (let y = top; y <= bottom; y++) for (let x = 0; x < COLUMNS; x++) if (world.reef[y][x]?.broken) {
    const c = world.reef[y][x];
    // A breaking cell draws in the reef pass (its chunks fly over the rows behind); settled, its last frame is rubble.
    if (breakSheets() && reefBreak[c.breakId]) { if (breakFrame(c) === CRACK_FRAMES + BREAK_FRAMES - 1) reefSprite(ctx, c.breakId, ox + (x + 0.5) * cell, oy + (y + 0.5) * cell, 0, CRACK_FRAMES + BREAK_FRAMES - 1); }
    else if (modelArt()) reefSprite(ctx, `reef-rubble-${hash(x, y, 87) < 0.5 ? 'a' : 'b'}`, ox + (x + 0.5) * cell, oy + (y + 0.5) * cell); else drawRubble(ctx, ox, oy, x, y);
  }
  // Reef shadow on the open seabed below it.
  ctx.fillStyle = 'rgba(4,23,74,.28)';
  if (!modelArt()) for (let y = top; y <= bottom; y++) for (let x = 0; x < COLUMNS; x++) if (isReef(x, y) && !isReef(x, y + 1)) ctx.fillRect(ox + x * cell, oy + (y + 1) * cell, cell, cell * 0.18);
  const ship = { x: run.x + knock.x, y: run.y + knock.y };
  ctx.save(); ctx.translate(ox + (ship.x + 0.06) * cell, oy + (ship.y + 0.42) * cell); ctx.scale(1, 0.5);
  const shade = ctx.createRadialGradient(0, 0, 0, 0, 0, cell * 0.62); shade.addColorStop(0, 'rgba(4,30,70,.5)'); shade.addColorStop(1, 'rgba(4,30,70,0)');
  ctx.fillStyle = shade; ctx.beginPath(); ctx.arc(0, 0, cell * 0.62, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  for (const b of scene.beds) if (b.y >= top && b.y <= bottom) sprite(ctx, b.sprite, ox + b.x * cell, oy + b.y * cell, cell);
  scene.pickups.forEach((p, i) => {
    if (run.collected.includes(i) || p.y < top || p.y > bottom + 1) return;
    const bob = Math.sin(time * 2.4 + i) * 0.05;
    sprite(ctx, `gold-${String(Math.floor(time * 10 + i * 3) % 12).padStart(2, '0')}`, ox + (p.x - 0.75) * cell, oy + (p.y - 0.75 + bob - 0.12) * cell, cell * 1.5);
  });
  if ($('opt-line').checked) drawLines(ctx, ox, oy);
  let drawn = false;
  const drawShip = () => {
    drawn = true;
    const sx = ox + ship.x * cell, sy = oy + ship.y * cell, pivotY = sy - cell * 0.35;
    const wobble = reduced() ? 0 : Math.sin(hurt * 26) * hurt * hurt * 0.35;
    const blink = run.protection > 0 && run.phase === 'pursuit' && !reduced() && Math.floor(time * 12) % 2;
    ctx.save(); ctx.translate(sx, pivotY); ctx.rotate(tilt + wobble); ctx.translate(-sx, -pivotY);
    ctx.globalAlpha = blink ? 0.45 : 1;
    piece(ctx, 'submarine-yellow', 'S', sx, sy, cell, time, { atRoot: true, clip: run.protection > 0 && run.phase === 'pursuit' ? 1 : 0 });
    if (hurt > 0.02) {
      const o = objects['submarine-yellow'], s = cell / 128, fw = o.frameSize[0] * s, fh = o.frameSize[1] * s;
      tintCanvas.width = Math.ceil(fw); tintCanvas.height = Math.ceil(fh);
      tctx.clearRect(0, 0, fw, fh); piece(tctx, 'submarine-yellow', 'S', o.root[0] * s, o.root[1] * s, cell, time, { atRoot: true, clip: 1 });
      tctx.globalCompositeOperation = 'source-atop'; tctx.fillStyle = `rgba(255,40,30,${0.55 * hurt * hurt})`; tctx.fillRect(0, 0, fw, fh); tctx.globalCompositeOperation = 'source-over';
      ctx.drawImage(tintCanvas, sx - o.root[0] * s, sy - o.root[1] * s);
    }
    ctx.restore(); ctx.globalAlpha = 1;
  };
  for (let y = top; y <= bottom; y++) {
    if (!drawn && y >= Math.floor(ship.y) && world.byRow[y].some((o) => o.w > 1)) drawShip();
    for (let x = 0; x < COLUMNS; x++) {
      if (isReef(x, y)) drawReefCell(ctx, ox, oy, x, y, time);
      else { const c = world.reef[y]?.[x]; if (c?.broken && breakSheets() && reefBreak[c.breakId] && breakFrame(c) < CRACK_FRAMES + BREAK_FRAMES - 1) reefSprite(ctx, c.breakId, ox + (x + 0.5) * cell, oy + (y + 0.5) * cell, 0, breakFrame(c)); }
    }
    for (const o of world.byRow[y]) piece(ctx, o.id, o.dir, ox + o.x * cell, oy + o.y * cell, cell, time, { salt: o.x * 5 + o.y * 3 });
    // The hull draws after the reef row it sits in, so the reef behind it never covers it.
    if (!drawn && y === Math.floor(ship.y + 0.5)) drawShip();
  }
  drawParticles(ctx, ox, oy);
  if (!drawn) drawShip();
  for (const s of scene.shafts) if (s.y >= top - 2 && s.y <= bottom) piece(ctx, s.id, s.dir, ox + s.x * cell, oy + s.y * cell, cell * 1.6, time, { salt: s.y });
  const v = ctx.createRadialGradient(W / 2, H * 0.55, H * 0.3, W / 2, H * 0.55, H * 0.8);
  v.addColorStop(0, 'rgba(3,20,60,0)'); v.addColorStop(1, 'rgba(3,20,60,.18)'); ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
  if (flashT > 0) {
    // Hit: a red glow along every screen edge, strong enough to read over pale reef.
    const d = W * 0.16, a = 0.7 * flashT, edge = (x0, y0, x1, y1) => { const g = ctx.createLinearGradient(x0, y0, x1, y1); g.addColorStop(0, `rgba(235,30,25,${a})`); g.addColorStop(1, 'rgba(235,30,25,0)'); return g; };
    ctx.fillStyle = edge(0, 0, d, 0); ctx.fillRect(0, 0, d, H);
    ctx.fillStyle = edge(W, 0, W - d, 0); ctx.fillRect(W - d, 0, d, H);
    ctx.fillStyle = edge(0, 0, 0, d); ctx.fillRect(0, 0, W, d);
    ctx.fillStyle = edge(0, H, 0, H - d); ctx.fillRect(0, H - d, W, d);
  }
  return { ox, oy };
}
/** Review overlay: each reef chunk's chosen line and its name. */
function drawLines(ctx, ox, oy) {
  const u = W / 390;
  ctx.save(); ctx.font = `800 ${11 * u}px Nunito, sans-serif`;
  for (const sp of world.spans) {
    const t = oy + sp.y0 * cell;
    ctx.fillStyle = sp.reef ? '#ffd75e' : 'rgba(230,248,255,.75)'; ctx.fillText(sp.reef ? `REEF · ${sp.reef.chunk.name} · line ${sp.reef.pick + 1}/${tables[sp.id].fair.length}` : sp.id, 8 * u, t + 14 * u);
    ctx.strokeStyle = 'rgba(230,248,255,.35)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(0, t); ctx.lineTo(W, t); ctx.stroke();
    if (!sp.reef?.xs) continue;
    ctx.setLineDash([6 * u, 5 * u]); ctx.strokeStyle = '#ffd75e'; ctx.lineWidth = 2.5 * u; ctx.beginPath();
    sp.reef.xs.forEach((x, i) => { const y = oy + (sp.y0 + sp.reef.bottom - i + 0.5) * cell; i ? ctx.lineTo(ox + x * cell, y) : ctx.moveTo(ox + x * cell, y); });
    ctx.stroke(); ctx.setLineDash([]);
  }
  ctx.restore();
}
const INK = '#24364d';
function drawHarpoon(x, y, angle, { head = false } = {}) {
  const u = W / 390, len = cell * 0.95;
  fctx.save(); fctx.translate(x, y); fctx.rotate(angle + Math.PI / 2); fctx.lineJoin = 'round'; fctx.lineCap = 'round';
  fctx.fillStyle = '#c9d4df'; fctx.strokeStyle = INK; fctx.lineWidth = 2.2 * u;
  fctx.beginPath(); fctx.roundRect(-2.6 * u, 8 * u, 5.2 * u, len - 8 * u, 2 * u); fctx.fill(); fctx.stroke();
  fctx.fillStyle = '#e2553f'; fctx.beginPath(); fctx.roundRect(-4.2 * u, len - 13 * u, 8.4 * u, 7 * u, 2.5 * u); fctx.fill(); fctx.stroke();
  if (head) {
    fctx.fillStyle = '#eef3f7'; fctx.beginPath();
    fctx.moveTo(0, -3 * u); fctx.lineTo(8 * u, 14 * u); fctx.lineTo(3 * u, 12 * u); fctx.lineTo(2.6 * u, 16 * u);
    fctx.lineTo(-2.6 * u, 16 * u); fctx.lineTo(-3 * u, 12 * u); fctx.lineTo(-8 * u, 14 * u); fctx.closePath(); fctx.fill(); fctx.stroke();
  }
  fctx.restore();
}
function rope(a, b, bend, t, alpha = 1) {
  const u = W / 390, cx = (a.x + b.x) / 2 + bend.x, cy = (a.y + b.y) / 2 + bend.y;
  const path = () => { fctx.beginPath(); fctx.moveTo(a.x, a.y); fctx.quadraticCurveTo(cx, cy, b.x, b.y); };
  fctx.globalAlpha = alpha; fctx.lineCap = 'round';
  path(); fctx.strokeStyle = 'rgba(5,31,69,.25)'; fctx.lineWidth = 7 * u; fctx.stroke();
  path(); fctx.strokeStyle = '#6b4526'; fctx.lineWidth = 5 * u; fctx.stroke();
  path(); fctx.strokeStyle = '#f3dcae'; fctx.lineWidth = 2.8 * u; fctx.stroke();
  fctx.setLineDash([2.2 * u, 4.4 * u]); fctx.lineDashOffset = -t * 60; path(); fctx.strokeStyle = '#a77a4b'; fctx.lineWidth = 2.8 * u; fctx.stroke(); fctx.setLineDash([]);
  fctx.globalAlpha = 1;
}
const RETRACT_START = 0.4, RETRACT_SECONDS = 1.0;
function drawFx(t, ox, oy) {
  fctx.setTransform(1, 0, 0, 1, 0, 0); fctx.clearRect(0, 0, fxCanvas.width, fxCanvas.height); fctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  if (run.phase === 'pursuit' && !reduced()) {
    fctx.strokeStyle = 'rgba(232,253,255,.5)'; fctx.lineWidth = Math.max(1.5, cell * 0.035); fctx.lineCap = 'round';
    for (let i = 0; i < 10; i++) {
      const side = i % 2 ? 1 : -1, lane = (i * 0.37) % 1, x = W / 2 + side * (W * 0.32 + lane * W * 0.16), y = ((t * 900 * run.speed / 1.4 + i * 211) % (H + 200)) - 100;
      fctx.globalAlpha = 0.25 + 0.35 * lane; fctx.beginPath(); fctx.moveTo(x, y); fctx.lineTo(x, y + cell * (0.8 + lane)); fctx.stroke();
    }
    fctx.globalAlpha = 1;
  }
  // Hull loss numbers rise off the ship.
  for (const p of popups) {
    const k = p.age / 0.9, u = W / 390;
    fctx.save(); fctx.globalAlpha = k > 0.6 ? (1 - k) / 0.4 : 1; fctx.font = `900 ${(22 + 8 * Math.max(0, 1 - k * 5)) * u}px Nunito, sans-serif`; fctx.textAlign = 'center';
    const x = ox + p.x * cell, y = oy + (p.y - k * 0.8) * cell;
    fctx.lineWidth = 5 * u; fctx.strokeStyle = '#fff'; fctx.strokeText(p.text, x, y); fctx.fillStyle = '#e8352a'; fctx.fillText(p.text, x, y); fctx.restore();
  }
  const nose = { x: ox + (run.x + knock.x) * cell, y: oy + (run.y + knock.y - 1) * cell };
  anchor.getWorldPosition(tmp); const p = toScreen(tmp);
  if (snap) {
    const a = Math.max(0, 1 - snap.t / 0.9), mid = { x: (nose.x + p.x) / 2, y: (nose.y + p.y) / 2 };
    rope(nose, { x: mid.x - cell * 0.6 * snap.t, y: mid.y + cell * 2 * snap.t }, { x: cell * 0.4, y: cell * 0.6 }, t, a);
    return;
  }
  if (run.phase === 'caught' || run.phase === 'award' || run.phase === 'results') {
    const k = run.phase === 'caught' ? Math.max(0, Math.min(1, (run.phaseT - RETRACT_START) / RETRACT_SECONDS)) : 1;
    if (k >= 1) return;
    const e = k * k * (3 - 2 * k), at = { x: p.x + (nose.x - p.x) * e, y: p.y + (nose.y - p.y) * e };
    const away = Math.atan2(at.y - nose.y, at.x - nose.x), len = cell * 0.95 * (1 - Math.max(0, k - 0.8) / 0.2);
    const tail = { x: at.x - Math.cos(away) * len, y: at.y - Math.sin(away) * len };
    if (Math.hypot(tail.x - nose.x, tail.y - nose.y) > 2) rope(nose, tail, { x: Math.sin(t * 6) * cell * 0.25 * (1 - e), y: cell * 0.5 * (1 - e) }, t);
    drawHarpoon(at.x, at.y, away, { head: true });
    return;
  }
  const ang = Math.atan2(p.y - nose.y, p.x - nose.x);
  const tail = { x: p.x - Math.cos(ang) * cell * 0.95, y: p.y - Math.sin(ang) * cell * 0.95 };
  const thrum = run.phase === 'pursuit' ? Math.sin(t * 31) * cell * 0.05 : Math.sin(t * 4) * cell * 0.2;
  rope(nose, tail, { x: thrum, y: run.phase === 'caught' ? cell * 0.3 : 0 }, t);
  drawHarpoon(p.x, p.y, ang);
}

// ---------------------------------------------------------------- creature placement
// Body centre `lead_rows` ahead of the ship. Screen y is linear in z for the ortho camera: y = H/2 + z·sin(e)·cell.
function placeFish(ox, oy, dt, time) {
  const centre = run.y - rules.lead_rows, nose = centre - HALF_ROWS, tailRow = centre + HALF_ROWS;
  if (run.phase === 'pursuit') {
    // In a reef chunk the body lies along the line; elsewhere it weaves ahead as the eel does.
    const weave = 5.5 + rules.weave_columns * Math.sin(2 * Math.PI * run.t / rules.weave_period_seconds) + 0.35 * Math.sin(run.t * 2.3);
    const head = lineAtWorld(nose), tail = lineAtWorld(tailRow);
    const hx = head ?? weave, tx = tail ?? hx;
    // Weaving stays in the ship's view so the cable reads; in reef the line wins.
    const goal = head !== null ? (hx + tx) / 2 : Math.max(Math.max(1.5, camX - 2.6), Math.min(Math.min(COLUMNS - 1.5, camX + 2.6), weave));
    run.fishX += (goal - run.fishX) * Math.min(1, dt * (head !== null ? 9 : 3));
    const wantYaw = head !== null ? Math.atan2(-(hx - tx), (tailRow - nose) / SIN_E) : -(goal - run.fishX) * 0.25;
    run.yaw += (wantYaw - run.yaw) * Math.min(1, dt * 6);
  }
  const target = { x: (ox + run.fishX * cell - W / 2) / cell, z: (oy + centre * cell - H / 2) / (SIN_E * cell) };
  if (run.phase === 'caught' && catchFrom) {
    const k = Math.min(1, run.phaseT / 0.9), e = reduced() ? 1 : k * k * (3 - 2 * k);
    const mid = { x: 0, z: (H * 0.4 - H / 2) / (SIN_E * cell) };
    fishRoot.position.set(catchFrom.x + (mid.x - catchFrom.x) * e, 0, catchFrom.z + (mid.z - catchFrom.z) * e);
    fishRoot.scale.setScalar(1 + 0.3 * e); fishRoot.rotation.y = run.yaw * (1 - e) - 0.45 * e;
    body.rotation.set(0, 0, Math.sin(time * 2) * 0.05);
  } else if (run.phase === 'escaped') {
    fishRoot.position.set(target.x, 0, target.z - run.phaseT * run.phaseT * 6);
  } else if (run.phase === 'pursuit') {
    fishRoot.position.set(target.x, 0, target.z); fishRoot.scale.setScalar(1); fishRoot.rotation.y = run.yaw;
    // Swim wiggle, plus a lunge and head-down pitch on each smash.
    const still = reduced() ? 0 : 1;
    body.position.z = -0.35 * lunge * still;
    body.rotation.set(0.12 * lunge * still, Math.sin(time * 7) * 0.07 * still, 0);
  }
}

// ---------------------------------------------------------------- HUD and state readout
function syncUi() {
  const hull = Math.round(run.hull), res = Math.max(0, run.resistance), pct = res / rules.resistance * 100;
  $('hull-fill').style.width = `calc(${hull}% - 6 * var(--u))`;
  $('hull-fill').style.background = run.hull <= 35 ? '#f0603b' : '#6cbf4b';
  $('hull').setAttribute('aria-label', `Hull ${hull}%`);
  $('salvage-value').textContent = run.salvage; $('salvage').setAttribute('aria-label', `${run.salvage} salvage this expedition`);
  const shown = pct * hudFill();
  $('resistance-fill').style.width = `calc(${shown}% - 6 * var(--u) * ${shown / 100})`;
  $('resistance').setAttribute('aria-label', `Boulderhead resistance ${Math.ceil(pct)}%`);
  phone.dataset.low = pct < 25 ? '1' : '0';
  const sp = spanAt(run.y);
  const rows = {
    Phase: run.paused ? 'pursuit (paused)' : run.phase,
    Speed: `${(run.speed * 100).toFixed(0)}% of travel${run.slowT > 0 ? ' · slowed' : ''}`,
    Resistance: `${res.toFixed(0)} / ${rules.resistance}`,
    Hull: `${hull} / ${rules.hull_max}`,
    Chunk: sp ? (sp.reef ? `Reef · ${sp.reef.chunk.name} · line ${sp.reef.pick + 1}` : sp.id) : '—',
    'Reef the fish broke': `${run.smashed} cells`,
    'Crash-throughs': run.crashes,
    'Hull hits': run.impacts,
  };
  $('state').innerHTML = Object.entries(rows).map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('');
}
function syncRules() {
  const r = R(), fwd = rules.forward_rows_per_second * rules.pursuit_speed_multiplier;
  $('rules').innerHTML = [
    `The chase plan is <b>ordinary → reef, three times, then ordinary</b> (route version 7). Speed, resistance (${rules.resistance}, about ${Math.round(rules.resistance / rules.resistance_drain_per_second)} s), rock hits and the catch are unchanged from #24.`,
    `Reef chunks are dense <b>brittle reef</b> (pale, cracked) round a few <b>bedrock</b> outcrops (the dark approved rock), with open water at the entry and exit.`,
    `The parrotfish swims ${rules.lead_rows} rows ahead (its nose about ${(rules.lead_rows + HALF_ROWS).toFixed(1)} rows, ${((rules.lead_rows + HALF_ROWS) / fwd).toFixed(1)} s at chase speed). In reef it follows one of its chunk's fair lines, picked per dive. Cracks spread over the next breach cells for ${r.crack_seconds} s, then its nose reaches them and they shatter: their collision goes the same frame. The breach is ${r.breach_columns} columns wide and turns at most ${r.max_shift_columns} columns per row. Debris is cosmetic; broken reef stays open.`,
    `Off the path, the hull shatters any brittle reef it touches: ${r.reef_damage} hull (once per ${rules.hit_protection_seconds} s hit protection) and a ${r.slow_seconds} s slowdown to ${Math.round(r.slow_multiplier * 100)}%, with no knock-back. Bedrock and ordinary rock are solid as in #24 (${rules.impact_damage} hull, knock-back).`,
    `Fair lines (reef.js): a steering bot with the ship's handling, a ${r.reaction_seconds} s reaction and ${r.bot_look_rows} rows of look-ahead (well inside the fish's lead) flies each line from the left, centre and right of the entry without touching reef. Each chunk keeps up to ${r.lines_per_chunk}.`,
  ].map((s) => `<li>${s}</li>`).join('');
}

// Reef chunks tab: each chunk with its fair lines (gold) and rejected ones (red, with the bot's first contact).
function renderChunks() {
  const host = $('fairness'), px = 16, r = R();
  host.replaceChildren();
  $('fair-note').innerHTML = `Every reef chunk at breach <b>${r.breach_columns} columns</b> and sharpest turn <b>${r.max_shift_columns} columns per row</b>. Pale cells are brittle reef, dark cells bedrock. <b style="color:#ffd75e">Gold</b> lines passed the steering bot; <b class="bad">red</b> ones failed (dot: first contact). A chunk needs at least one fair line to join a route.`;
  for (const c of REEF_CHUNKS) {
    const { fair, rejected } = tables[c.id];
    const fig = document.createElement('figure'); fig.className = fair.length ? 'accepted' : 'rejected';
    const cv = document.createElement('canvas'), rows = c.rows.length, wid = COLUMNS * px;
    cv.width = wid * 2; cv.height = rows * px * 2; cv.style.width = `${wid}px`;
    const g = cv.getContext('2d'); g.scale(2, 2);
    c.rows.forEach((row, y) => [...row].forEach((ch, x) => { g.fillStyle = ch === '#' ? '#2b4466' : ch === 'b' ? '#d9ccab' : '#1d6aa0'; g.fillRect(x * px, y * px, px - 1, px - 1); }));
    const [, bottom] = reefRows(c.rows);
    const path = (xs, col, w) => { g.strokeStyle = col; g.lineWidth = w; g.beginPath(); xs.forEach((x, i) => { const y = (bottom - i + 0.5) * px; i ? g.lineTo(x * px, y) : g.moveTo(x * px, y); }); g.stroke(); };
    for (const l of rejected.slice(0, 3)) { path(l.xs, 'rgba(239,90,60,.8)', 2); g.fillStyle = '#ef5a3c'; g.beginPath(); g.arc(l.hit.x * px, l.hit.y * px, 3.5, 0, 7); g.fill(); }
    for (const l of fair) path(l.xs, 'rgba(255,215,94,.9)', 2);
    const cap = document.createElement('figcaption');
    cap.innerHTML = `<b>${c.name}</b> <code>${c.id}</code><br>${fair.length ? `<span class="ok">${fair.length} fair lines</span>` : '<span class="bad">no fair line</span>'}${rejected.length ? ` · ${rejected.length} rejected` : ''}`;
    fig.append(cv, cap); host.append(fig);
  }
}

// Settings: feel ones apply live; ones that change the lines rebuild them and restart the chase.
const controls = {
  lead: [rules, 'lead_rows', (v) => `${v} rows`, false], crack: [R(), 'crack_seconds', (v) => `${v} s`, false],
  width: [R(), 'breach_columns', (v) => `${v} cols`, true], shift: [R(), 'max_shift_columns', (v) => `${v} col/row`, true],
  damage: [R(), 'reef_damage', (v) => `${v} hull`, false], slow: [R(), 'slow_multiplier', (v) => `${Math.round(v * 100)}%`, false],
};
for (const [id, [obj, k, fmt, rebuild]] of Object.entries(controls)) {
  const input = $(id); input.value = obj[k]; $(`${id}-out`).textContent = fmt(obj[k]);
  input.addEventListener('input', () => { obj[k] = Number(input.value); $(`${id}-out`).textContent = fmt(obj[k]); });
  input.addEventListener('change', () => { if (rebuild) { restart(); renderChunks(); } syncRules(); });
}

window.review = { sounds: { buffers, played }, get run() { return run; }, get world() { return world; }, get tables() { return tables; }, rules, restart };

// ---------------------------------------------------------------- loop
resize();
restart();
renderChunks();
const clock = new THREE.Clock();
let artTime = 0;
renderer.setAnimationLoop(() => {
  const frame = Math.min(clock.getDelta(), 0.1) * ($('opt-slow').checked ? 0.25 : 1);
  // Hit-stop: the world nearly freezes for a beat when the hull takes a hit.
  const real = hitstop > 0 ? frame * 0.08 : frame; hitstop = Math.max(0, hitstop - frame);
  const dt = run.paused || ['award', 'results'].includes(run.phase) ? 0 : real;
  artTime += real * (run.paused ? 0 : 1);
  let remaining = dt;
  while (remaining > 0) { const s = Math.min(remaining, 0.05); remaining -= s; handle(step(s)); }
  if (snap) snap.t += dt;
  if (!run.paused) {
    tilt += ((run.phase === 'pursuit' ? Math.max(-1, Math.min(1, run.vx / rules.lateral_columns_per_second)) * 0.3 : 0) - tilt) * Math.min(1, real * 10);
    hurt = Math.max(0, hurt - real * 1.8); flashT = Math.max(0, flashT - frame * 1.6); shakeT = Math.max(0, shakeT - real); lunge = Math.max(0, lunge - real * 5);
    const kk = Math.exp(-real * 14); knock = { x: knock.x * kk, y: knock.y * kk };
    stepParticles(dt);
    if (run.phase === 'pursuit' && Math.random() < real * 20) emitBubble(run.x + (Math.random() - 0.5) * 0.12, run.y + 0.62, { vy: 1.4 + Math.random() * 0.6, r: 0.03 + Math.random() * 0.04, life: 1.2, rise: 0.4 });
  }
  const half = VIEW / 2, off = run.x - camX, want = Math.abs(off) > 0.7 ? run.x - Math.sign(off) * 0.7 : camX;
  camX += (Math.max(half, Math.min(COLUMNS - half, want)) - camX) * Math.min(1, real * 4);
  const { ox, oy } = drawWorld(artTime);
  placeFish(ox, oy, dt, artTime);
  fishRoot.updateMatrixWorld(true);
  renderer.render(scene3, camera);
  if (run.phase === 'caught' || run.phase === 'award') {
    fishRoot.getWorldPosition(tmp); const c = toScreen(tmp);
    rays.style.setProperty('--rx', `${(c.x / W * 100).toFixed(1)}%`); rays.style.setProperty('--ry', `${(c.y / H * 100).toFixed(1)}%`);
    rays.style.setProperty('--spin', `${reduced() ? 0 : (artTime * 12) % 360}deg`);
  }
  drawFx(artTime, ox, oy);
  syncUi();
});
