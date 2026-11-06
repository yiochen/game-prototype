import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js';
import { GLTFLoader } from 'https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/loaders/GLTFLoader.js';
import manifest from '../../assets/expedition/v1/manifest.json';
import v2Library from '../../assets/expedition/v2/library.json';
import originalSet from '../underwater-kit-preview/original-set.json';
import rules from './balance.json';
import { analyzeLibrary, assemble, chunkFromMap, composeScene, generate, mulberry32 } from '../../assets/expedition/route/route.js';
import { analyzeCreatureChunk, chaseRowsPerSecond, collides as hits } from './fairness.js';

/* Storm Eel discharge review for #25, built on the approved #24 chase.
   - Creature chunks (./chunks, kind "creature", creature "storm-eel") are wide open water. The pursuit plan
     alternates them with ordinary chunks; the eel discharges only inside them (fairness.js).
   - Discharge warning: amber fill, diagonal hatching, dashed amber edges and lightning badges, flashing a few
     times just before the strike (no countdown); code-drawn over the world (#world) so the eel stays above it.
   - Strike: code-drawn jagged bolts on #fx; a lightning hit costs hull with the red hit tint and electric
     sparks, but no knock-back.
   Unchanged from #24:
   Asset map:
   - Route terrain, seabed, gold, submarine: approved production sprites and route chunks (as #21/#22), on #world.
   - Storm Eel: the approved live 3D GLB (#23), on #eel with the ART-05 contrast grade. Clips: hooked/struggle while
     chased, exhausted when caught, escape when the hull gives out.
   - Cable and pinned harpoon: the #23 code-drawn rope and harpoon, drawn over the world on #fx.
   - HUD pills, pause, arrows: the approved #22/#23 family. The resistance pill is the creature's health.
   - Catch cutscene: live scene + code-drawn rays (.catch-rays) and plain outlined text. No baked art.
   - Recipe award: maple card (native PopupSkin family), new ImageGen backdrop (award-art/v1) with the #15 plate and
     dish sheets as separate CSS layers, live text and facts.
   - Results: the existing native receipt card. */

const EEL_URL = new URL('../storm-eel-preview/assets/storm-eel.glb', import.meta.url).href;
const contentChunks = import.meta.glob('../../godot/content/expedition/chunks/*.json', { eager: true, import: 'default' });
const eelChunkDocs = import.meta.glob('./chunks/*.json', { eager: true, import: 'default' });
const productionUrls = import.meta.glob('../../assets/production/sprites/{floor-underwater,decor-background-rock,decor-foreground-rock,boulder-underwater,column-broken,decor-ruin-fragment,crate-wood,decor-foreground-coral,decor-midground-coral,decor-kelp,decor-starfish,decor-background-wreck,decor-background-fish,decor-light-shafts,submarine-yellow}/*.png', { eager: true, query: '?url', import: 'default' });
const v2Urls = import.meta.glob('../../assets/expedition/v2/sprites/*/*.png', { eager: true, query: '?url', import: 'default' });
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

// ---------------------------------------------------------------- world art (as #22)
const kit = manifest.sprites, kitImages = {}, PX = manifest.cell_pixels;
await Promise.all(Object.entries(kit).filter(([n]) => /^(bed|gold)-/.test(n)).map(async ([n, e]) => { kitImages[n] = await load(kitUrls[`../../assets/expedition/v1/${e.image}`]); }));
const sprite = (ctx, name, x, y, cell) => { const e = kit[name], s = cell / PX; ctx.drawImage(kitImages[name], x - e.origin[0] * s, y - e.origin[1] * s, e.size[0] * s, e.size[1] * s); };
const objects = { ...originalSet.objects };
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

const sources = [];
for (const [file, doc] of Object.entries(contentChunks)) sources.push(chunkFromMap(doc, file.split('/').pop().slice(0, -5)));
// Creature chunks: checked by the discharge fairness rules; rejected ones never join the library.
const creature = Object.entries(eelChunkDocs).map(([file, doc]) => {
  const id = file.split('/').pop().slice(0, -5), chunk = { ...chunkFromMap(doc, id), attack: doc.chunk.attack_rows, creature: doc.chunk.creature };
  return { ...chunk, doc, report: analyzeCreatureChunk(chunk, rules) };
}).sort((x, y) => Number(x.report.accepted === false) - Number(y.report.accepted === false) || x.id.localeCompare(y.id));
const accepted = new Map(creature.filter((c) => c.report.accepted).map((c) => [c.id, c]));
// Seams are checked like any chunk; then the eel chunks take their own kind so only "creature" slots offer them.
const library = analyzeLibrary([...sources, ...[...accepted.values()].map((c) => ({ ...c, kind: 'normal' }))]).chunks
  .map((c) => (accepted.has(c.id) ? { ...c, kind: 'creature' } : c));
let world;
function buildWorld(seed, force) {
  const sequence = generate(seed, library, { slots: ['launch', 'start', ...rules.pursuit_plan, 'finish'], force: force || undefined });
  const { rows: grid, spans } = assemble(sequence);
  for (const sp of spans) if (sp.kind === 'creature') sp.creature = accepted.get(sp.id);
  const scene = composeScene(grid, v2Library.objects, seed);
  const byRow = Array.from({ length: scene.rows }, () => []);
  for (const o of scene.objects) byRow[o.y].push(o);
  const c = 24, shadow = new OffscreenCanvas((scene.columns + 4) * c, (scene.rows + 4) * c), sctx = shadow.getContext('2d');
  sctx.filter = 'blur(9px)'; sctx.fillStyle = '#04174a';
  for (const b of scene.collision) sctx.fillRect((b.x + 2) * c - 2, (b.y + 2) * c - 2, c + 4, c + 4);
  const fish = Array.from({ length: Math.ceil(scene.rows / 13) }, (_, i) => { const r = mulberry32(seed * 31 + i); return { y: 4 + i * 13 + r() * 6, speed: 0.25 + r() * 0.25, dir: i % 2 ? -1 : 1, phase: r() * 20 }; });
  world = { seed, grid, spans, scene, byRow, shadow: { canvas: shadow, c }, fish };
}
for (const c of accepted.values()) $('force').append(new Option(c.name, c.id));
const COLUMNS = 11, VIEW = 7;

// ---------------------------------------------------------------- 3D eel (as #23)
const ELEVATION = THREE.MathUtils.degToRad(35);
const LOOPS = new Set(['swim', 'restless', 'hooked', 'struggle', 'exhausted']);
const GLOW = { windup: (t) => 1 + Math.min(1, t / rules.discharge.warn_seconds) * 1.6 + 0.4 * Math.sin(t * 22), attack: (t) => 2.6 + 0.8 * Math.sin(t * 40), hooked: (t) => 0.9 + 0.3 * Math.sin(t * 8), struggle: (t) => 1.1 + 0.5 * Math.max(0, Math.sin(t * 10)), exhausted: (t) => 0.35 + 0.1 * Math.sin(t * 2), escape: () => 1.4 };
const renderer = new THREE.WebGLRenderer({ canvas: eelCanvas, alpha: true, antialias: true });
renderer.outputColorSpace = THREE.SRGBColorSpace;
eelCanvas.classList.add('graded');
const scene3 = new THREE.Scene();
scene3.add(new THREE.AmbientLight(0xffffff, 1.9));
const key = new THREE.DirectionalLight(0xffffff, 1.1); key.position.set(-2, 10, 4); scene3.add(key);
const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 100);
camera.position.set(0, Math.sin(ELEVATION), Math.cos(ELEVATION)).multiplyScalar(30); camera.lookAt(0, 0, 0);
const eelRoot = new THREE.Group(); scene3.add(eelRoot);
const gltf = await new GLTFLoader().loadAsync(EEL_URL);
const eel = gltf.scene; eelRoot.add(eel);
const bones = {}, spotMats = [], bodyMats = [];
eel.traverse((o) => {
  if (o.isBone) bones[o.name] = o;
  if (o.isMesh) {
    o.frustumCulled = false;
    const mats = [].concat(o.material).map((m) => {
      const flat = new THREE.MeshLambertMaterial({ name: m.name, color: m.color, flatShading: true, emissive: m.emissive, emissiveIntensity: m.name === 'eel_spot' ? 1 : 0 });
      (m.name === 'eel_spot' ? spotMats : bodyMats).push(flat); return flat;
    });
    o.material = Array.isArray(o.material) ? mats : mats[0];
  }
});
const spine = [bones.head, ...Object.keys(bones).filter((n) => n.startsWith('spine_')).sort().map((n) => bones[n])];
const shadowTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d'), gr = g.createRadialGradient(32, 32, 0, 32, 32, 32); gr.addColorStop(0, 'rgba(4,28,58,0.30)'); gr.addColorStop(1, 'rgba(4,28,58,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c); })();
const shadowMat = new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false });
const blobs = spine.map((bone) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(1.15, 1.15), shadowMat); m.rotation.x = -Math.PI / 2; m.renderOrder = -1; scene3.add(m); return { bone, mesh: m }; });
const mixer = new THREE.AnimationMixer(eel);
const clips = Object.fromEntries(gltf.animations.map((c) => [c.name, c]));
let action = null, clipName = '', clipTime = 0;
function play(name, fade = 0.25) {
  if (name === clipName) return;
  const next = mixer.clipAction(clips[name]); next.reset();
  next.setLoop(LOOPS.has(name) ? THREE.LoopRepeat : THREE.LoopOnce, Infinity); next.clampWhenFinished = true; next.play();
  if (action && action !== next) next.crossFadeFrom(action, fade, false);
  action = next; clipName = name; clipTime = 0;
}
// The hook from #23: the harpoon stays pinned on the struck body part's back.
const anchor = new THREE.Object3D();
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
    resistance: rules.resistance, eelX: 5.5, speed: 1, impacts: 0, phaseT: 0, paused: false, discovered: true, released: false,
    attack: null, cooldown: 0, strikes: 0, zaps: 0, rng: mulberry32(world.seed * 977 + 25) };
  bolts = null;
  camX = 5.5; tilt = 0; hurt = 0; knock = { x: 0, y: 0 }; particles.length = 0; snap = null;
  eelRoot.scale.setScalar(1); eelRoot.rotation.y = 0; mixer.stopAllAction(); action = null; clipName = ''; play('hooked', 0);
  eel.updateMatrixWorld(true);
  const bone = bones.spine_02 ?? spine[3];
  if (anchor.parent) anchor.parent.remove(anchor);
  bone.getWorldPosition(tmp); tmp.y += 0.38; bone.add(anchor); anchor.position.copy(bone.worldToLocal(tmp.clone()));
  hideOverlays(); banner.hidden = true; setPhase('pursuit');
  showBanner('Hooked!<small>Reel it in. Dodge the rocks!</small>', 'pursuit', 1800);
  hudIntro();
}
function setPhase(p) { run.phase = p; run.phaseT = 0; phone.dataset.phase = p; }
const reach = rules.ship_radius;
const collides = (x, y, r) => hits(world.grid, x, y, r, rules);
const OFFSETS = []; for (let iy = 0; iy <= 20; iy++) for (let ix = -60; ix <= 60; ix++) OFFSETS.push([ix * 0.05, iy * 0.1]);
OFFSETS.sort((a, b) => a[0] ** 2 + a[1] ** 2 - b[0] ** 2 - b[1] ** 2);
function nearestClear(x, y, r) {
  for (const [dx, dy] of OFFSETS) { const px = x + dx, py = y + dy; if (px < 0.4 || px > COLUMNS - 0.4) continue; if (!collides(px, py, r)) return { x: px, y: py }; }
  return { x, y };
}
const moveToward = (v, to, d) => (Math.abs(to - v) <= d ? to : v + Math.sign(to - v) * d);

function step(dt) {
  run.t += dt; run.phaseT += dt;
  const ev = [];
  const weave = rules.weave_columns * Math.sin(2 * Math.PI * run.t / rules.weave_period_seconds) + 0.35 * Math.sin(run.t * 2.3);
  if (run.phase === 'pursuit') {
    run.speed = Math.min(rules.pursuit_speed_multiplier, 1 + (rules.pursuit_speed_multiplier - 1) * run.t / rules.pursuit_ramp_seconds);
    run.y -= rules.forward_rows_per_second * run.speed * dt;
    run.protection = Math.max(0, run.protection - dt);
    run.vx = moveToward(run.vx, run.steer * rules.lateral_columns_per_second, rules.lateral_acceleration * dt);
    run.x += run.vx * dt;
    if (run.x < 0.4 || run.x > COLUMNS - 0.4) { run.x = Math.max(0.4, Math.min(COLUMNS - 0.4, run.x)); run.vx = 0; }
    // It weaves across the route but stays in the ship's view, so the cable always reads.
    // While discharging it holds over its chosen strip.
    const goal = run.attack ? run.attack.centre : 5.5 + weave;
    run.eelX += (Math.max(Math.max(1.5, camX - 2.4), Math.min(Math.min(COLUMNS - 1.5, camX + 2.4), goal)) - run.eelX) * Math.min(1, dt * (run.attack ? 5 : 3));
    world.scene.pickups.forEach((g, i) => {
      if (run.collected.includes(i) || Math.abs(g.x - run.x) > rules.pickup_radius || Math.abs(g.y - run.y) > rules.pickup_radius) return;
      run.collected.push(i); run.salvage += rules.salvage_per_pickup; ev.push({ type: 'pickup', x: g.x, y: g.y });
    });
    if (collides(run.x, run.y, reach)) {
      // Rock is solid: knock back to the nearest clear water; only the first touch dents the hull.
      const from = { x: run.x, y: run.y }, to = nearestClear(run.x, run.y, reach + rules.knockback_clearance);
      run.x = to.x; run.y = to.y; run.vx = 0;
      if (run.protection <= 0) {
        run.hull = Math.max(0, run.hull - rules.impact_damage); run.protection = rules.hit_protection_seconds; run.impacts++;
        ev.push({ type: 'impact', from, to });
        if (run.hull <= 0) { ev.push({ type: 'hull_gone' }); return ev; }
      } else ev.push({ type: 'bump', from, to });
    }
    ev.push(...stepDischarge(dt));
    if (run.hull <= 0) { ev.push({ type: 'hull_gone' }); return ev; }
    // Resistance is the creature's health: it only drains, never refills.
    if (!$('opt-hold').checked) run.resistance = Math.max(0, run.resistance - rules.resistance_drain_per_second * dt);
    if (run.resistance <= 0) ev.push({ type: 'caught' });
  } else if (run.phase === 'caught') {
    // Hazards are over: the chase eases to a stop while the cutscene plays.
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

// ---------------------------------------------------------------- discharge (mirrors the planned Godot rules)
const D = rules.discharge, fwd = chaseRowsPerSecond(rules);
const spanAt = (y) => world.spans.find((sp) => y >= sp.y0 && y < sp.y1 + 1);
const between = ([lo, hi]) => lo + run.rng() * (hi - lo);
function stepDischarge(dt) {
  const ev = [];
  run.cooldown = Math.max(0, run.cooldown - dt);
  const a = run.attack;
  if (a) {
    a.t += dt;
    if (a.phase === 'windup' && a.t >= D.warn_seconds) { a.phase = 'strike'; ev.push({ type: 'discharge' }); }
    if (a.phase === 'strike') {
      // Only the live strip hurts, with the usual hit protection; no knock-back.
      if (run.protection <= 0 && Math.abs(run.x - a.centre) < a.w / 2 + rules.ship_radius * 0.5) {
        run.hull = Math.max(0, run.hull - D.damage); run.protection = rules.hit_protection_seconds; run.zaps++;
        ev.push({ type: 'zap', x: run.x, y: run.y });
      }
      if (a.t >= D.warn_seconds + D.active_seconds) { afterglow = { x0: a.x0, w: a.w, t: 0 }; run.attack = null; run.strikes++; run.cooldown = between(D.cooldown_seconds); }
    }
    return ev;
  }
  // A new windup only starts inside a creature chunk, from that chunk's table of fair strikes.
  const sp = spanAt(run.y);
  if (!sp?.creature || run.cooldown > 0 || run.speed < rules.pursuit_speed_multiplier) return ev;
  const strikeRow = run.y - sp.y0 - D.warn_seconds * fwd;
  const entry = sp.creature.report.strikes.find((s) => Math.abs(s.row - strikeRow) <= D.fairness.row_step / 2);
  if (!entry) return ev;
  // Not tracking: one fixed strip, on screen, picked by weight with a lean towards the ship.
  const pool = entry.fair.filter((s) => Math.abs(s.centre - camX) <= VIEW / 2 - s.w / 2 - 0.15);
  if (!pool.length) return ev;
  const weights = pool.map((s) => Math.exp(-((s.centre - run.x) ** 2) / (2 * D.aim_spread_columns ** 2)));
  let r = run.rng() * weights.reduce((x, y) => x + y, 0), pick = pool[pool.length - 1];
  for (let i = 0; i < pool.length; i++) { r -= weights[i]; if (r <= 0) { pick = pool[i]; break; } }
  run.attack = { phase: 'windup', t: 0, x0: pick.x0, w: pick.w, centre: pick.centre, chunk: sp.id, row: entry.row, choices: entry.fair };
  ev.push({ type: 'windup' });
  return ev;
}

// Any warning or live strike vanishes the moment the chase ends (catch or escape).
function clearDischarge() { run.attack = null; afterglow = null; bolts = null; strikeFlash = 0; }

function handle(events) {
  for (const e of events) {
    if (e.type === 'pickup') for (let i = 0; i < 6; i++) emitSpark(e.x, e.y - 0.15);
    if (e.type === 'impact') { damage(e.from, e.to); shakeT = 0.35; flashT = 1; }
    if (e.type === 'discharge') { bolts = null; boltT = 0; strikeFlash = 1; shakeT = Math.max(shakeT, 0.2); }
    if (e.type === 'zap') {
      // Lightning: hull tint and electric sparks, no knock-back.
      hurt = 1; flashT = 1;
      if (!reduced()) for (let i = 0; i < 18; i++) emitSpark(e.x + (Math.random() - 0.5) * 0.5, e.y - 0.3 - Math.random() * 0.4, i % 3 ? '#bff4ff' : '#fff6b8', 2.2);
    }
    if (e.type === 'bump') knock = { x: knock.x + e.from.x - e.to.x, y: knock.y + e.from.y - e.to.y };
    if (e.type === 'caught') {
      // The catch and first recipe are committed here, before any presentation.
      clearDischarge(); setPhase('caught'); play('exhausted', 0.35); held.clear(); updateSteer();
      catchFrom = { x: eelRoot.position.x, z: eelRoot.position.z };
      showBanner(`Caught!<small>Storm Eel${run.discovered ? ' · first catch' : ''}</small>`, 'caught', rules.catch_cutscene_seconds * 1000);
      for (let i = 0; i < 26; i++) emitBubble(run.eelX + (Math.random() - 0.5) * 2, run.y - rules.lead_rows + (Math.random() - 0.2) * 2, { vy: -0.6 - Math.random(), vx: (Math.random() - 0.5) * 1.2, r: 0.04 + Math.random() * 0.05, life: 1.6 + Math.random(), rise: 0.6 });
    }
    if (e.type === 'harpoon_released') {
      anchor.getWorldPosition(tmp); const p = toScreen(tmp), { ox, oy } = origin();
      const wx = (p.x - ox) / cell, wy = (p.y - oy) / cell;
      for (let i = 0; i < 8; i++) emitSpark(wx, wy, '#fff3c4', 1.2);
      for (let i = 0; i < 6; i++) emitBubble(wx + (Math.random() - 0.5) * 0.3, wy, { vx: (Math.random() - 0.5), vy: -0.4 - Math.random() * 0.4, r: 0.03 + Math.random() * 0.03, life: 1, rise: 0.5 });
    }
    if (e.type === 'cutscene_done') { banner.hidden = true; run.discovered ? openAward() : openResults('complete'); }
    if (e.type === 'hull_gone') {
      // The only pursuit attempt ends: the cable snaps and the creature gets away. No recipe.
      clearDischarge(); setPhase('escaped'); play('escape', 0.15); held.clear(); updateSteer();
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
function makeAward() {
  const node = $('award-template').content.firstElementChild.cloneNode(true);
  node.querySelector('.award-backdrop').src = BACKDROP_URL;
  node.querySelector('.coin').src = COIN_URL;
  return node;
}
function openAward() {
  setPhase('award');
  const host = cards.award; host.replaceChildren(makeAward());
  host.querySelector('.award-continue').addEventListener('click', () => openResults('complete'));
  show('award'); host.querySelector('.award-continue').focus();
}
function fillResults(root, outcome, pickups) {
  const done = outcome === 'complete', bonus = done ? rules.completion_bonus : 0;
  root.querySelector('h2').textContent = done ? 'Expedition complete' : 'Hull depleted';
  root.querySelector('[data-r="pickups"], #r-pickups').textContent = pickups;
  const bonusRow = [root.querySelector('#r-bonus-label'), root.querySelector('#r-bonus')];
  for (const n of bonusRow) n.hidden = !done;
  root.querySelector('#r-bonus').textContent = `+${bonus}`;
  root.querySelector('#r-total').textContent = pickups + bonus;
}
function openResults(outcome) {
  // A surviving ship finishes the route automatically after the catch.
  setPhase('results'); fillResults(cards.results, outcome, run.salvage); show('results'); $('restaurant').focus();
}
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
// Encounter HUD: one mirrored "versus" row (hull left, eel right); the gold count hides.
// The travel HUD (gold count) gives way to the versus row when the creature arrives.
let hudAt = 0;
function hudIntro() {
  phone.dataset.hud = 'travel'; hudAt = Infinity;
  void phone.offsetWidth;
  setTimeout(() => { if (phone.dataset.hud === 'travel') { phone.dataset.hud = 'versus'; hudAt = performance.now(); } }, 600);
}
// The eel bar fills from empty once it has slid into place, like a boss bar.
const hudFill = () => { const k = Math.max(0, Math.min(1, (performance.now() - hudAt - 450) / 600)); return reduced() ? (performance.now() >= hudAt ? 1 : 0) : 1 - (1 - k) ** 3; };
for (const id of ['seed', 'force']) $(id).addEventListener('change', restart);
$('next-eel').addEventListener('click', () => {
  if (run.phase !== 'pursuit') return;
  const next = [...world.spans].filter((sp) => sp.creature && sp.y0 < run.y - 1).sort((a, b) => b.y0 - a.y0)[0];
  if (!next) return;
  run.y = next.y1 + 1.5; run.x = 5.5; run.vx = 0; run.attack = null; run.cooldown = 0; run.protection = 0; camX = 5.5;
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
let bolts = null, boltT = 0, strikeFlash = 0, afterglow = null;
let tilt = 0, hurt = 0, knock = { x: 0, y: 0 }, shakeT = 0, flashT = 0, snap = null, catchFrom = null, camX = 5.5;
function damage(from, to) {
  hurt = 1; knock = { x: knock.x + from.x - to.x, y: knock.y + from.y - to.y };
  if (reduced()) return;
  const d = Math.hypot(from.x - to.x, from.y - to.y) || 1, ax = (from.x - to.x) / d, ay = (from.y - to.y) / d;
  for (let i = 0; i < 14; i++) emitSpark(from.x + ax * 0.35, from.y + ay * 0.35 - 0.2, `hsl(${30 + Math.random() * 20} 100% 60%)`, 1.8);
  for (let i = 0; i < 6; i++) particles.push({ kind: 'chip', x: from.x, y: from.y - 0.2, vx: -ax * (1 + Math.random() * 1.4) + (Math.random() - 0.5), vy: -ay * (1 + Math.random()) - 0.4, r: 0.05 + Math.random() * 0.04, life: 0.6 + Math.random() * 0.3, age: 0, drag: 2.5, spin: (Math.random() - 0.5) * 24 });
  for (let i = 0; i < 8; i++) emitBubble(from.x + (Math.random() - 0.5) * 0.4, from.y, { vx: (Math.random() - 0.5) * 1.2, vy: -0.3 - Math.random() * 0.4, r: 0.03 + Math.random() * 0.04, life: 1 + Math.random() * 0.5, rise: 0.45 });
}
function stepParticles(dt) {
  for (const p of particles) { p.age += dt; const k = Math.exp(-p.drag * dt); p.vx *= k; p.vy *= k; if (p.kind === 'bubble') p.vy -= p.rise * dt * 1.6; p.x += p.vx * dt; p.y += p.vy * dt; }
  for (let i = particles.length - 1; i >= 0; i--) if (particles[i].age >= particles[i].life) particles.splice(i, 1);
}
function drawParticles(ctx, ox, oy) {
  for (const p of particles) {
    const t = p.age / p.life, x = ox + p.x * cell, y = oy + p.y * cell;
    if (p.kind === 'bubble') { const r = p.r * (1 + 0.3 * t) * cell; ctx.globalAlpha = Math.min(1, p.age * 8) * (1 - t * t); ctx.drawImage(bubbleSprite, x + Math.sin(p.age * p.freq + p.phase) * p.wob * cell - r, y - r, r * 2, r * 2); }
    else if (p.kind === 'chip') { const r = p.r * cell, a = p.age * p.spin; ctx.globalAlpha = 1 - t * t; ctx.fillStyle = '#ffc733'; ctx.beginPath(); ctx.moveTo(x + Math.cos(a) * r, y + Math.sin(a) * r); ctx.lineTo(x + Math.cos(a + 2.3) * r * 0.7, y + Math.sin(a + 2.3) * r * 0.7); ctx.lineTo(x + Math.cos(a + 3.9) * r * 0.9, y + Math.sin(a + 3.9) * r * 0.9); ctx.fill(); }
    else if (p.kind === 'line') { ctx.globalAlpha = 0.7 * Math.sin(Math.PI * t); ctx.strokeStyle = '#e8fdff'; ctx.lineWidth = Math.max(1.5, cell * 0.035); ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y - p.len * cell); ctx.stroke(); }
    else { ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = 1 - t; ctx.fillStyle = p.color; ctx.beginPath(); ctx.arc(x, y, p.r * cell * (1 - t * 0.5), 0, Math.PI * 2); ctx.fill(); ctx.restore(); }
  }
  ctx.globalAlpha = 1;
}
// Red-tinted copy of the hull for the hit flash.
const tintCanvas = document.createElement('canvas'), tctx = tintCanvas.getContext('2d');

// ---------------------------------------------------------------- drawing
const topRow = () => Math.max(0, run.y + knock.y - H * 0.74 / cell);
const origin = () => {
  const s = shakeT > 0 && !reduced() ? shakeT / 0.35 : 0;
  return { ox: W / 2 - camX * cell + Math.sin(performance.now() * 0.071) * s * cell * 0.08, oy: -topRow() * cell + Math.cos(performance.now() * 0.053) * s * cell * 0.08 };
};
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
      // Red hit tint over the hull only.
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
    for (const o of world.byRow[y]) piece(ctx, o.id, o.dir, ox + o.x * cell, oy + o.y * cell, cell, time, { salt: o.x * 5 + o.y * 3 });
  }
  drawParticles(ctx, ox, oy);
  if (!drawn) drawShip();
  for (const s of scene.shafts) if (s.y >= top - 2 && s.y <= bottom) piece(ctx, s.id, s.dir, ox + s.x * cell, oy + s.y * cell, cell * 1.6, time, { salt: s.y });
  if ($('opt-zones').checked) drawZones(ctx, ox, oy);
  drawStrip(ctx, ox, time);
  const v = ctx.createRadialGradient(W / 2, H * 0.55, H * 0.3, W / 2, H * 0.55, H * 0.8);
  v.addColorStop(0, 'rgba(3,20,60,0)'); v.addColorStop(1, 'rgba(3,20,60,.18)'); ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
  if (flashT > 0) { const g = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.75); g.addColorStop(0, 'rgba(255,40,30,0)'); g.addColorStop(1, `rgba(255,40,30,${0.35 * flashT})`); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
  return { ox, oy };
}

const INK = '#24364d', AMBER = '#ffb52e', FLASH_SECONDS = 0.6, FLASHES = 3;
// Diagonal hatching for the warned strip (shape as well as colour).
const hatch = (() => { const n = 32, c = new OffscreenCanvas(n, n), g = c.getContext('2d'); g.strokeStyle = '#c96a00'; g.lineWidth = 7; g.beginPath(); for (let k = -1; k <= 1; k++) { g.moveTo(k * n - 4, n + 4); g.lineTo(k * n + n + 4, -4); } g.stroke(); return c; })();
let hatchPattern = null;
/** The warned strip: amber fill, diagonal hatching and dashed amber edges; white-hot while live. */
function drawStrip(ctx, ox, time) {
  const a = run.attack, u = W / 390;
  const glow = afterglow && afterglow.t < 0.3 ? afterglow : null;
  if (!a && !glow) return;
  const x0 = ox + (a ?? glow).x0 * cell, w = (a ?? glow).w * cell;
  ctx.save();
  if (a?.phase === 'windup') {
    // Steady, then a few bright flashes just before it goes live (no countdown).
    const k = Math.min(1, a.t / 0.3), into = a.t - (D.warn_seconds - FLASH_SECONDS);
    const flash = into >= 0 && (reduced() ? 1 : Math.floor(into / (FLASH_SECONDS / (FLASHES * 2))) % 2 === 0);
    ctx.globalAlpha = 1;
    ctx.fillStyle = `rgba(255,170,30,${0.3 * k})`; ctx.fillRect(x0, 0, w, H);
    if (flash) { ctx.fillStyle = 'rgba(255,214,120,.45)'; ctx.fillRect(x0, 0, w, H); }
    hatchPattern ??= ctx.createPattern(hatch, 'repeat');
    const scale = cell / 64, scroll = reduced() ? 0 : (time * cell * 0.5) % (32 * scale);
    hatchPattern.setTransform(new DOMMatrix().translate(x0, scroll).scale(scale));
    ctx.globalAlpha = (flash ? 0.95 : 0.65) * k; ctx.fillStyle = hatchPattern; ctx.fillRect(x0, 0, w, H);
    ctx.globalAlpha = k;
    for (const ex of [x0, x0 + w]) {
      ctx.lineCap = 'round'; ctx.strokeStyle = 'rgba(36,54,77,.7)'; ctx.lineWidth = 6 * u; ctx.setLineDash([12 * u, 8 * u]);
      ctx.lineDashOffset = reduced() ? 0 : -time * 40 * u;
      ctx.beginPath(); ctx.moveTo(ex, 0); ctx.lineTo(ex, H); ctx.stroke();
      ctx.strokeStyle = AMBER; ctx.lineWidth = 3.5 * u; ctx.stroke();
    }
    ctx.setLineDash([]);
  } else {
    // Live (and a short afterglow): a white-hot strip.
    const k = a ? 1 - 0.4 * (a.t - D.warn_seconds) / D.active_seconds : 0.6 * (1 - glow.t / 0.3);
    ctx.fillStyle = `rgba(255,222,130,${0.55 * k})`; ctx.fillRect(x0, 0, w, H);
    ctx.globalCompositeOperation = 'lighter'; ctx.fillStyle = `rgba(255,214,120,${0.35 * k})`; ctx.fillRect(x0 - cell * 0.15, 0, w + cell * 0.3, H);
  }
  ctx.restore();
}
/** Review overlay: each eel chunk's strike rows and, during a windup, every fair strip it could have used. */
function drawZones(ctx, ox, oy) {
  const u = W / 390;
  ctx.save(); ctx.font = `800 ${11 * u}px Nunito, sans-serif`;
  for (const sp of world.spans) {
    const top = oy + sp.y0 * cell;
    ctx.fillStyle = sp.creature ? '#ffd27a' : 'rgba(230,248,255,.75)'; ctx.fillText(`${sp.kind === 'creature' ? 'EEL · ' : ''}${sp.id}`, 8 * u, top + 14 * u);
    ctx.strokeStyle = 'rgba(230,248,255,.35)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(0, top); ctx.lineTo(W, top); ctx.stroke();
    if (!sp.creature) continue;
    const [a, b] = sp.creature.attack, y0 = oy + (sp.y0 + a) * cell, y1 = oy + (sp.y0 + b) * cell;
    ctx.strokeStyle = AMBER; ctx.lineWidth = 3 * u;
    for (const x of [4 * u, W - 4 * u]) { ctx.beginPath(); ctx.moveTo(x + (x < W / 2 ? 8 : -8) * u, y0); ctx.lineTo(x, y0); ctx.lineTo(x, y1); ctx.lineTo(x + (x < W / 2 ? 8 : -8) * u, y1); ctx.stroke(); }
  }
  if (run.attack) {
    ctx.setLineDash([4 * u, 4 * u]); ctx.lineWidth = 1.5 * u; ctx.strokeStyle = 'rgba(255,255,255,.7)';
    const at = oy + (world.spans.find((sp) => sp.id === run.attack.chunk && sp.creature)?.y0 ?? 0) * cell + run.attack.row * cell;
    run.attack.choices.forEach((c, i) => { const y = at - 6 * u - (i % 6) * 4 * u; ctx.beginPath(); ctx.moveTo(ox + c.x0 * cell + 3, y); ctx.lineTo(ox + (c.x0 + c.w) * cell - 3, y); ctx.stroke(); });
    ctx.setLineDash([]);
  }
  ctx.restore();
}
/** Lightning badge: amber disc, ink rim, white bolt. */
function badge(x, y, r) {
  const u = W / 390;
  fctx.save(); fctx.translate(x, y); fctx.lineJoin = 'round';
  fctx.fillStyle = 'rgba(5,31,69,.3)'; fctx.beginPath(); fctx.arc(1.5 * u, 3 * u, r, 0, Math.PI * 2); fctx.fill();
  fctx.fillStyle = AMBER; fctx.strokeStyle = INK; fctx.lineWidth = 2.6 * u; fctx.beginPath(); fctx.arc(0, 0, r, 0, Math.PI * 2); fctx.fill(); fctx.stroke();
  fctx.fillStyle = '#ffd98a'; fctx.beginPath(); fctx.arc(-r * 0.25, -r * 0.3, r * 0.45, 0, Math.PI * 2); fctx.fill();
  const bolt = [[0.18, -0.72], [-0.38, 0.1], [-0.02, 0.1], [-0.16, 0.72], [0.4, -0.14], [0.04, -0.14]];
  fctx.beginPath(); bolt.forEach(([bx, by], i) => fctx[i ? 'lineTo' : 'moveTo'](bx * r, by * r)); fctx.closePath();
  fctx.fillStyle = '#fffdf3'; fctx.fill(); fctx.lineWidth = 2 * u; fctx.stroke();
  fctx.restore();
}
function boltPath(x0, w, from, to) {
  const pts = [], step = cell * 0.45;
  let x = x0 + w * (0.3 + Math.random() * 0.4);
  for (let y = from; y <= to + step; y += step) { pts.push([x, y]); x = Math.max(x0 + w * 0.15, Math.min(x0 + w * 0.85, x + (Math.random() - 0.5) * w * 0.55)); }
  return pts;
}
/** Badges during the windup; jagged bolts from the eel while the strike is live. */
function drawDischarge(ox) {
  const a = run.attack, u = W / 390;
  if (!a) return;
  const cx = ox + a.centre * cell, x0 = ox + a.x0 * cell, w = a.w * cell;
  if (a.phase === 'windup') {
    const pop = reduced() ? 1 : Math.min(1, a.t / 0.18) * (1 + 0.15 * Math.sin(Math.min(1, a.t / 0.3) * Math.PI));
    const shipY = origin().oy + (run.y + 1.5) * cell;
    badge(cx, 96 * u, cell * 0.32 * pop);
    badge(cx, Math.min(H - 30 * u, shipY), cell * 0.26 * pop);
    return;
  }
  bones.head.getWorldPosition(tmp); const eelY = Math.max(0, toScreen(tmp).y);
  if (!bolts || boltT > (reduced() ? 0.2 : 0.06)) { bolts = [boltPath(x0, w, eelY, H), boltPath(x0, w, eelY, H), boltPath(x0, w, -10, eelY)]; boltT = 0; }
  fctx.save(); fctx.lineJoin = 'round'; fctx.lineCap = 'round';
  for (const [i, pts] of bolts.entries()) {
    const path = () => { fctx.beginPath(); pts.forEach(([x, y], j) => fctx[j ? 'lineTo' : 'moveTo'](x, y)); };
    fctx.globalCompositeOperation = 'lighter';
    path(); fctx.strokeStyle = 'rgba(255,170,40,.45)'; fctx.lineWidth = (i === 2 ? 7 : 12) * u; fctx.stroke();
    fctx.globalCompositeOperation = 'source-over';
    path(); fctx.strokeStyle = '#fff1a8'; fctx.lineWidth = (i === 2 ? 3 : 5) * u; fctx.stroke();
    path(); fctx.strokeStyle = '#ffffff'; fctx.lineWidth = (i === 2 ? 1.2 : 2) * u; fctx.stroke();
  }
  fctx.restore();
  if (strikeFlash > 0 && !reduced()) { fctx.fillStyle = `rgba(255,246,214,${0.18 * strikeFlash})`; fctx.fillRect(0, 0, W, H); }
}
function drawHarpoon(x, y, angle, { head = false } = {}) {
  const u = W / 390, len = cell * 0.95;
  fctx.save(); fctx.translate(x, y); fctx.rotate(angle + Math.PI / 2); fctx.lineJoin = 'round'; fctx.lineCap = 'round';
  fctx.fillStyle = '#c9d4df'; fctx.strokeStyle = INK; fctx.lineWidth = 2.2 * u;
  fctx.beginPath(); fctx.roundRect(-2.6 * u, 8 * u, 5.2 * u, len - 8 * u, 2 * u); fctx.fill(); fctx.stroke();
  fctx.fillStyle = '#e2553f'; fctx.beginPath(); fctx.roundRect(-4.2 * u, len - 13 * u, 8.4 * u, 7 * u, 2.5 * u); fctx.fill(); fctx.stroke();
  if (head) {
    // The barbed head, visible once the harpoon is pulled free.
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
  // Chase speed: pale streaks rush past both sides.
  if (run.phase === 'pursuit' && !reduced()) {
    fctx.strokeStyle = 'rgba(232,253,255,.5)'; fctx.lineWidth = Math.max(1.5, cell * 0.035); fctx.lineCap = 'round';
    for (let i = 0; i < 10; i++) {
      const side = i % 2 ? 1 : -1, lane = (i * 0.37) % 1, x = W / 2 + side * (W * 0.32 + lane * W * 0.16), y = ((t * 900 * run.speed / 1.4 + i * 211) % (H + 200)) - 100;
      fctx.globalAlpha = 0.25 + 0.35 * lane; fctx.beginPath(); fctx.moveTo(x, y); fctx.lineTo(x, y + cell * (0.8 + lane)); fctx.stroke();
    }
    fctx.globalAlpha = 1;
  }
  if (run.phase === 'pursuit') drawDischarge(ox);
  const nose = { x: ox + (run.x + knock.x) * cell, y: oy + (run.y + knock.y - 1) * cell };
  anchor.getWorldPosition(tmp); const p = toScreen(tmp);
  if (snap) {
    // The cable parts in the middle and both halves fall slack and fade.
    const a = Math.max(0, 1 - snap.t / 0.9), mid = { x: (nose.x + p.x) / 2, y: (nose.y + p.y) / 2 };
    rope(nose, { x: mid.x - cell * 0.6 * snap.t, y: mid.y + cell * 2 * snap.t }, { x: cell * 0.4, y: cell * 0.6 }, t, a);
    return;
  }
  if (run.phase === 'caught' || run.phase === 'award' || run.phase === 'results') {
    // Caught: the harpoon pulls free of the eel and reels back into the ship's nose, then is stowed.
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
  // Taut while chasing (a fast thrum), easing slack as the eel is reeled in.
  const thrum = run.phase === 'pursuit' ? Math.sin(t * 31) * cell * 0.05 : Math.sin(t * 4) * cell * 0.2;
  rope(nose, tail, { x: thrum, y: run.phase === 'caught' ? cell * 0.3 : 0 }, t);
  drawHarpoon(p.x, p.y, ang);
}

// ---------------------------------------------------------------- creature placement
// Ground root `lead_rows` ahead of the ship. Screen y is linear in z for the ortho camera: y = H/2 + z·sin(e)·cell.
function placeEel(ox, oy, dt) {
  const target = { x: (ox + run.eelX * cell - W / 2) / cell, z: (oy + (run.y - rules.lead_rows) * cell - H / 2) / (Math.sin(ELEVATION) * cell) };
  if (run.phase === 'caught' && catchFrom) {
    // Cutscene: the exhausted eel is drawn into the centre of the screen and grows, framed by the rays.
    const k = Math.min(1, run.phaseT / 0.9), e = reduced() ? 1 : k * k * (3 - 2 * k);
    const centre = { x: 0, z: (H * 0.4 - H / 2) / (Math.sin(ELEVATION) * cell) };
    eelRoot.position.set(catchFrom.x + (centre.x - catchFrom.x) * e, 0, catchFrom.z + (centre.z - catchFrom.z) * e);
    eelRoot.scale.setScalar(1 + 0.45 * e);
    eelRoot.rotation.y = -0.45 * e;
  } else if (run.phase === 'escaped') {
    eelRoot.position.set(target.x, 0, target.z - run.phaseT * run.phaseT * 6);
  } else if (run.phase === 'pursuit') {
    eelRoot.position.set(target.x, 0, target.z); eelRoot.scale.setScalar(1);
  }
}

// ---------------------------------------------------------------- HUD and state readout
function syncUi() {
  const hull = Math.round(run.hull), res = Math.max(0, run.resistance);
  $('hull-fill').style.width = `calc(${hull}% - 6 * var(--u))`;
  $('hull-fill').style.background = run.hull <= 35 ? '#f0603b' : '#6cbf4b';
  $('hull').setAttribute('aria-label', `Hull ${hull}%`);
  $('salvage-value').textContent = run.salvage; $('salvage').setAttribute('aria-label', `${run.salvage} salvage this expedition`);
  const shown = res * hudFill();
  $('resistance-fill').style.width = `calc(${shown}% - 6 * var(--u) * ${shown / 100})`;
  $('resistance').setAttribute('aria-label', `Storm Eel resistance ${Math.ceil(res)}%`);
  phone.dataset.low = res < 25 ? '1' : '0';
  const rows = {
    Phase: run.paused ? 'pursuit (paused)' : run.phase,
    Speed: `${(run.speed * 100).toFixed(0)}% of travel`,
    Resistance: `${res.toFixed(0)} / ${rules.resistance}`,
    Hull: `${hull} / ${rules.hull_max}`,
    Chunk: (() => { const sp = spanAt(run.y); return sp ? `${sp.kind === 'creature' ? 'Eel · ' : ''}${sp.creature?.name ?? sp.id}` : '—'; })(),
    Discharge: run.attack ? `${run.attack.phase} · columns ${run.attack.x0}–${run.attack.x0 + run.attack.w} · ${run.attack.choices.length} fair choices` : run.cooldown > 0 ? `cooldown ${run.cooldown.toFixed(1)} s` : 'ready',
    Strikes: run.strikes,
    'Rock hits': run.impacts,
    'Lightning hits': run.zaps,
  };
  $('state').innerHTML = Object.entries(rows).map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('');
}
$('rules').innerHTML = [
  `The chase plan is <b>normal → eel chunk → normal → eel chunk → normal</b> (difficulty ${rules.pursuit_plan.filter((x) => typeof x === 'number').join(', ')}). Speed, resistance, rock hits and the catch are unchanged from #24.`,
  `The eel discharges <b>only inside its own chunks</b>, and only while the live strike falls inside the chunk's <code>attack_rows</code>. Ordinary chunks never get lightning.`,
  `Windup ${rules.discharge.warn_seconds} s: the eel moves over one fixed strip (${rules.discharge.width_columns.join(' or ')} columns, not tracking) and charges. The strip shows amber fill, diagonal hatching, dashed edges and lightning badges, then flashes ${FLASHES} times in the last ${FLASH_SECONDS} s before the strike.`,
  `Strike ${rules.discharge.active_seconds} s: ship inside the strip loses ${rules.discharge.damage} hull (hit protection applies, no knock-back, no resistance change). Then ${rules.discharge.cooldown_seconds.join('–')} s before the next windup.`,
  `Fairness: each eel chunk is checked when it loads. For every strike row and strip, every position the ship could hold at the windup must still have a way out, after a ${rules.discharge.fairness.reaction_seconds} s reaction at ${Math.round(rules.discharge.fairness.reach_margin * 100)}% sideways speed, ${rules.discharge.fairness.lane_slack_columns} columns clear of the strip and without touching rock. The eel only picks from those fair strips, leaning towards the ship. A chunk with fewer than ${rules.discharge.fairness.min_choices} fair strips at any strike row is rejected (see the Eel chunks tab).`,
].map((s) => `<li>${s}</li>`).join('');

// Eel chunks tab: each chunk beside its fairness table (strip centre across, strike row down).
{
  const host = $('fairness'), px = 14;
  $('fair-note').innerHTML = `Each creature chunk beside its fairness tables. Down: the row where a strike would go live (amber bracket = <code>attack_rows</code>). Across: the strip's centre. <b class="ok">Green</b> fair, <b class="bad">red</b> unfair (some position could not get out), grey over too little water to matter. Accepted chunks join the library; rejected ones never appear in a route.`;
  for (const c of creature) {
    const fig = document.createElement('figure'); fig.className = c.report.accepted ? 'accepted' : 'rejected';
    const cv = document.createElement('canvas'), rows = c.rows.length, gap = 26, wid = COLUMNS * px;
    cv.width = (wid * 3 + gap * 2) * 2; cv.height = (rows * px + 22) * 2; cv.style.width = `${cv.width / 2}px`;
    const g = cv.getContext('2d'); g.scale(2, 2); g.translate(0, 18);
    g.font = '800 11px Nunito, sans-serif'; g.fillStyle = '#d7e6f2';
    g.fillText('Chunk', 0, -6); g.fillText('2-column strip', wid + gap, -6); g.fillText('3-column strip', 2 * (wid + gap), -6);
    for (let k = 0; k < 3; k++) {
      const ox = k * (wid + gap);
      c.rows.forEach((row, y) => [...row].forEach((ch, x) => {
        g.fillStyle = /[#cmk]/.test(ch) ? (k ? '#29405f' : '#34557d') : k ? '#13284a' : '#1d6aa0';
        g.fillRect(ox + x * px, y * px, px - 1, px - 1);
        if (!k && ch === '$') { g.fillStyle = '#ffd34d'; g.beginPath(); g.arc(ox + x * px + px / 2, y * px + px / 2, 3.5, 0, 7); g.fill(); }
      }));
      const [a, b] = c.attack; g.strokeStyle = AMBER; g.lineWidth = 2;
      g.beginPath(); g.moveTo(ox - 1 + 5, a * px); g.lineTo(ox - 1, a * px); g.lineTo(ox - 1, b * px); g.lineTo(ox - 1 + 5, b * px); g.stroke();
      if (!k) continue;
      for (const s of c.report.strikes) for (const r of s.results) {
        if (r.w !== k + 1) continue;
        g.fillStyle = !r.meaningful ? '#5b6b80' : r.fair ? '#58c45a' : '#ef5a3c';
        g.beginPath(); g.arc(ox + r.centre * px, s.row * px, 3.4, 0, 7); g.fill();
      }
    }
    const cap = document.createElement('figcaption');
    cap.innerHTML = `<b>${c.name}</b> <code>${c.id}</code> · ${c.report.accepted ? '<span class="ok">accepted</span>' : `<span class="bad">rejected: ${c.report.problems.join('; ')}</span>`}${c.doc.chunk.review_example ? ' · <i>deliberate bad example</i>' : ''}`;
    fig.append(cv, cap); host.append(fig);
  }
}

// Capture hook for the review screenshots (tools in the scratchpad drive it).
window.review = { get run() { return run; }, get world() { return world; }, restart };

// ---------------------------------------------------------------- loop
resize();
restart();
const clock = new THREE.Clock();
let artTime = 0;
renderer.setAnimationLoop(() => {
  const real = Math.min(clock.getDelta(), 0.1) * ($('opt-slow').checked ? 0.25 : 1);
  const dt = run.paused || ['award', 'results'].includes(run.phase) ? 0 : real;
  artTime += real * (run.paused ? 0 : 1);
  let remaining = dt;
  while (remaining > 0) { const s = Math.min(remaining, 0.05); remaining -= s; handle(step(s)); }
  if (snap) snap.t += dt;
  if (!run.paused) {
    tilt += ((run.phase === 'pursuit' ? Math.max(-1, Math.min(1, run.vx / rules.lateral_columns_per_second)) * 0.3 : 0) - tilt) * Math.min(1, real * 10);
    boltT += real; strikeFlash = Math.max(0, strikeFlash - real * 6); if (afterglow) afterglow.t += real;
    hurt = Math.max(0, hurt - real * 1.8); flashT = Math.max(0, flashT - real * 2.2); shakeT = Math.max(0, shakeT - real);
    const kk = Math.exp(-real * 14); knock = { x: knock.x * kk, y: knock.y * kk };
    stepParticles(dt);
    if (run.phase === 'pursuit' && Math.random() < real * 20) emitBubble(run.x + (Math.random() - 0.5) * 0.12, run.y + 0.62, { vy: 1.4 + Math.random() * 0.6, r: 0.03 + Math.random() * 0.04, life: 1.2, rise: 0.4 });
  }
  const half = VIEW / 2, off = run.x - camX, want = Math.abs(off) > 0.7 ? run.x - Math.sign(off) * 0.7 : camX;
  camX += (Math.max(half, Math.min(COLUMNS - half, want)) - camX) * Math.min(1, real * 4);
  const { ox, oy } = drawWorld(artTime);
  placeEel(ox, oy, dt);
  if (run.phase === 'pursuit') play(run.attack ? (run.attack.phase === 'windup' ? 'windup' : 'attack') : run.resistance < 30 ? 'struggle' : 'hooked', 0.15);
  mixer.update(run.paused ? 0 : real); clipTime += real;
  for (const m of spotMats) m.emissiveIntensity = (GLOW[clipName] ?? (() => 1))(clipTime);
  eel.updateMatrixWorld(true);
  for (const { bone, mesh } of blobs) { bone.getWorldPosition(tmp); mesh.position.set(tmp.x, 0.02, tmp.z); mesh.visible = run.phase !== 'caught'; }
  renderer.render(scene3, camera);
  // Rays centre on the creature during the cutscene.
  if (run.phase === 'caught' || run.phase === 'award') {
    bones.spine_04?.getWorldPosition(tmp); const c = toScreen(tmp);
    rays.style.setProperty('--rx', `${(c.x / W * 100).toFixed(1)}%`); rays.style.setProperty('--ry', `${(c.y / H * 100).toFixed(1)}%`);
    rays.style.setProperty('--spin', `${reduced() ? 0 : (artTime * 12) % 360}deg`);
  }
  drawFx(artTime, ox, oy);
  syncUi();
});
