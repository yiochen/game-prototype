import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js';
import { GLTFLoader } from 'https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/loaders/GLTFLoader.js';
import manifest from '../../assets/expedition/v1/manifest.json';
import v2Library from '../../assets/expedition/v2/library.json';
import originalSet from '../underwater-kit-preview/original-set.json';
import travelRules from '../expedition-currents-preview/balance.json';
import rules from './balance.json';
import { analyzeLibrary, assemble, chunkFromMap, composeScene, generate, isRock, mulberry32 } from '../../assets/expedition/route/route.js';

/* Pursuit, catch and recipe award review for #24.
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
const productionUrls = import.meta.glob('../../assets/production/sprites/{floor-underwater,decor-background-rock,decor-foreground-rock,boulder-underwater,column-broken,decor-ruin-fragment,crate-wood,decor-foreground-coral,decor-midground-coral,decor-kelp,decor-starfish,decor-background-wreck,decor-background-fish,decor-light-shafts,submarine-yellow}/*.png', { eager: true, query: '?url', import: 'default' });
const v2Urls = import.meta.glob('../../assets/expedition/v2/sprites/*/*.png', { eager: true, query: '?url', import: 'default' });
const kitUrls = import.meta.glob('../../assets/expedition/v1/sprites/{bed,gold}-*.png', { eager: true, query: '?url', import: 'default' });
const PLATES_URL = new URL('../recipe-picker-preview/raw/plates.png', import.meta.url).href;
const FOOD_URL = new URL('../recipe-picker-preview/raw/food.png', import.meta.url).href;
const COIN_URL = new URL('../../godot/assets/ui/coin.svg', import.meta.url).href;
const BACKDROP_URL = new URL('./award-art/v1/backdrop.jpg', import.meta.url).href;
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

const docs = {}, sources = [];
for (const [file, doc] of Object.entries(contentChunks)) { const id = file.split('/').pop().slice(0, -5); docs[id] = doc; sources.push(chunkFromMap(doc, id)); }
const { chunks: library } = analyzeLibrary(sources);
const SEED = 24;
const world = (() => {
  const { rows: grid, spans } = assemble(generate(SEED, library, { slots: travelRules.plan }));
  const scene = composeScene(grid, v2Library.objects, SEED);
  const byRow = Array.from({ length: scene.rows }, () => []);
  for (const o of scene.objects) byRow[o.y].push(o);
  const c = 24, shadow = new OffscreenCanvas((scene.columns + 4) * c, (scene.rows + 4) * c), sctx = shadow.getContext('2d');
  sctx.filter = 'blur(9px)'; sctx.fillStyle = '#04174a';
  for (const b of scene.collision) sctx.fillRect((b.x + 2) * c - 2, (b.y + 2) * c - 2, c + 4, c + 4);
  const fish = Array.from({ length: Math.ceil(scene.rows / 13) }, (_, i) => { const r = mulberry32(SEED * 31 + i); return { y: 4 + i * 13 + r() * 6, speed: 0.25 + r() * 0.25, dir: i % 2 ? -1 : 1, phase: r() * 20 }; });
  return { grid, spans, scene, byRow, shadow: { canvas: shadow, c }, fish };
})();
const COLUMNS = 11, VIEW = 7;

// ---------------------------------------------------------------- 3D eel (as #23)
const ELEVATION = THREE.MathUtils.degToRad(35);
const LOOPS = new Set(['swim', 'restless', 'hooked', 'struggle', 'exhausted']);
const GLOW = { hooked: (t) => 0.9 + 0.3 * Math.sin(t * 8), struggle: (t) => 1.1 + 0.5 * Math.max(0, Math.sin(t * 10)), exhausted: (t) => 0.35 + 0.1 * Math.sin(t * 2), escape: () => 1.4 };
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
const START_Y = world.spans[3].y0 - 0.5;
function restart() {
  run = { phase: 'pursuit', t: 0, y: START_Y, x: 5.5, vx: 0, steer: 0, hull: rules.hull_max, protection: 0, salvage: 6, collected: [],
    resistance: rules.resistance, eelX: 5.5, speed: 1, impacts: 0, phaseT: 0, paused: false, discovered: false, released: false };
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
const reach = rules.ship_radius + rules.rock_radius;
function collides(x, y, r) {
  for (let cy = Math.floor(y - r); cy <= Math.floor(y + r); cy++) {
    if (cy < 0 || cy >= world.grid.length) continue;
    for (let cx = Math.floor(x - r); cx <= Math.floor(x + r); cx++) {
      if (cx >= 0 && cx < COLUMNS && isRock(world.grid[cy][cx]) && Math.hypot(cx + 0.5 - x, cy + 0.5 - y) < r) return true;
    }
  }
  return false;
}
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
    run.eelX += (Math.max(Math.max(1.5, camX - 2.4), Math.min(Math.min(COLUMNS - 1.5, camX + 2.4), 5.5 + weave)) - run.eelX) * Math.min(1, dt * 3);
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
    // Resistance is the creature's health: it only drains, never refills.
    run.resistance = Math.max(0, run.resistance - rules.resistance_drain_per_second * dt);
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

function handle(events) {
  for (const e of events) {
    if (e.type === 'pickup') for (let i = 0; i < 6; i++) emitSpark(e.x, e.y - 0.15);
    if (e.type === 'impact') { damage(e.from, e.to); shakeT = 0.35; flashT = 1; }
    if (e.type === 'bump') knock = { x: knock.x + e.from.x - e.to.x, y: knock.y + e.from.y - e.to.y };
    if (e.type === 'caught') {
      // The catch and first recipe are committed here, before any presentation.
      run.discovered = !$('opt-repeat').checked;
      setPhase('caught'); play('exhausted', 0.35); held.clear(); updateSteer();
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
      setPhase('escaped'); play('escape', 0.15); held.clear(); updateSteer();
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
$('picker-link').href = new URL('../../?recipe-ui=1&state=new', location.href).href;
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
  if ($('opt-old-hud').checked) { phone.dataset.hud = 'stacked'; hudAt = -1e9; return; }
  phone.dataset.hud = 'travel'; hudAt = Infinity;
  void phone.offsetWidth;
  setTimeout(() => { if (phone.dataset.hud === 'travel') { phone.dataset.hud = 'versus'; hudAt = performance.now(); } }, 600);
}
// The eel bar fills from empty once it has slid into place, like a boss bar.
const hudFill = () => { const k = Math.max(0, Math.min(1, (performance.now() - hudAt - 450) / 600)); return reduced() ? (performance.now() >= hudAt ? 1 : 0) : 1 - (1 - k) ** 3; };
$('opt-old-hud').addEventListener('change', hudIntro);
$('replay-hud').addEventListener('click', hudIntro);
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
  const v = ctx.createRadialGradient(W / 2, H * 0.55, H * 0.3, W / 2, H * 0.55, H * 0.8);
  v.addColorStop(0, 'rgba(3,20,60,0)'); v.addColorStop(1, 'rgba(3,20,60,.18)'); ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
  if (flashT > 0) { const g = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.75); g.addColorStop(0, 'rgba(255,40,30,0)'); g.addColorStop(1, `rgba(255,40,30,${0.35 * flashT})`); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
  return { ox, oy };
}

const INK = '#24364d';
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
    Impacts: run.impacts,
    'Recipe awarded': run.phase === 'pursuit' || run.phase === 'escaped' ? 'not yet' : run.discovered ? 'Eel roll (first catch)' : 'repeat: none',
  };
  $('state').innerHTML = Object.entries(rows).map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('');
}
$('rules').innerHTML = [
  `Once hooked, ship and eel speed up together to <b>${rules.pursuit_speed_multiplier}×</b> travel speed over ${rules.pursuit_ramp_seconds} s, through ordinary route terrain. The cable stretches freely: no following strip, no range limit.`,
  `Resistance is the eel's health. It drains steadily (${rules.resistance_drain_per_second}/s, about ${Math.round(rules.resistance / rules.resistance_drain_per_second)} s) and never goes back up. The Harpoon button stays hidden: one harpoon only.`,
  `Hits cost hull only (${rules.impact_damage} each, then ${rules.hit_protection_seconds} s protection), with the #23 knock-back and hit animation. Zero hull snaps the cable, the eel escapes, and the run ends as Hull depleted with no recipe and no second try.`,
  `At zero resistance the catch and the first recipe are saved immediately. Hazards end, and a ${rules.catch_cutscene_seconds} s cutscene plays with no Skip. Then the recipe award opens; Continue goes to the results. A repeat catch goes straight to the results.`,
  'After the catch the ship finishes the route automatically: the results include the completion bonus.',
].map((s) => `<li>${s}</li>`).join('');

// Screens tab: the same award and results components, frozen.
{
  const list = $('screens-list');
  const fig = (node, caption) => { const f = document.createElement('figure'); f.append(node); const c = document.createElement('figcaption'); c.textContent = caption; f.append(c); list.append(f); };
  const a = makeAward(); a.style.animation = 'none'; fig(a, 'Recipe award · first catch (Red plate)');
  const pressed = makeAward(); pressed.style.animation = 'none'; pressed.querySelector('.award-continue').classList.add('is-pressed'); pressed.querySelector('.award-continue').style.cssText = 'transform:translateY(2px);box-shadow:inset 0 1px #ffab83,0 2px #bd4528'; fig(pressed, 'Award · Continue pressed');
  for (const [outcome, title] of [['complete', 'Results · caught and finished'], ['hull_depleted', 'Results · hull depleted in the chase']]) {
    const r = cards.results.cloneNode(true); r.hidden = false; r.removeAttribute('id');
    for (const n of r.querySelectorAll('[id]')) n.id = n.id;
    fillResults(r, outcome, outcome === 'complete' ? 30 : 18); r.querySelector('button').tabIndex = -1; fig(r, title);
  }
}

// ---------------------------------------------------------------- loop
resize();
restart();
const clock = new THREE.Clock();
let artTime = 0;
renderer.setAnimationLoop(() => {
  const real = Math.min(clock.getDelta(), 0.1);
  const dt = run.paused || ['award', 'results'].includes(run.phase) ? 0 : real;
  artTime += real * (run.paused ? 0 : 1);
  let remaining = dt;
  while (remaining > 0) { const s = Math.min(remaining, 0.05); remaining -= s; handle(step(s)); }
  if (snap) snap.t += dt;
  if (!run.paused) {
    tilt += ((run.phase === 'pursuit' ? Math.max(-1, Math.min(1, run.vx / rules.lateral_columns_per_second)) * 0.3 : 0) - tilt) * Math.min(1, real * 10);
    hurt = Math.max(0, hurt - real * 1.8); flashT = Math.max(0, flashT - real * 2.2); shakeT = Math.max(0, shakeT - real);
    const kk = Math.exp(-real * 14); knock = { x: knock.x * kk, y: knock.y * kk };
    stepParticles(dt);
    if (run.phase === 'pursuit' && Math.random() < real * 20) emitBubble(run.x + (Math.random() - 0.5) * 0.12, run.y + 0.62, { vy: 1.4 + Math.random() * 0.6, r: 0.03 + Math.random() * 0.04, life: 1.2, rise: 0.4 });
  }
  const half = VIEW / 2, off = run.x - camX, want = Math.abs(off) > 0.7 ? run.x - Math.sign(off) * 0.7 : camX;
  camX += (Math.max(half, Math.min(COLUMNS - half, want)) - camX) * Math.min(1, real * 4);
  const { ox, oy } = drawWorld(artTime);
  placeEel(ox, oy, dt);
  if (run.phase === 'pursuit') play(run.resistance < 30 ? 'struggle' : 'hooked');
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
