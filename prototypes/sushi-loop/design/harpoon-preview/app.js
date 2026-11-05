import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js';
import { GLTFLoader } from 'https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/loaders/GLTFLoader.js';

/* Harpoon review for #23.
   Asset map:
   - Seabed, submarine: approved production sprites (floor-underwater, submarine-yellow travel), drawn on #world.
   - Storm Eel: approved live 3D GLB (design/storm-eel-preview), drawn on #eel with the ART-05 contrast grade.
   - Harpoon, cable: code-drawn on #fx (steel shaft, barbed head, red collar; braided cream rope with brown ink).
   - HUD pills, pause, steering arrows: the approved #22 family (coin-panel nine-slice, cream disc, rounded triangles).
   - Harpoon button: cream disc + brown glyph matching the pause button; SVG ring for cooldown. No baked text. */

const RULES = {
  window_s: 16,               // shooting window from the encounter start
  restless_s: 4,              // restless warning before the window closes
  cooldown_s: 1.6,            // from firing until the next shot is ready
  harpoon_cells_per_s: 15,
  reel_cells_per_s: 22,
  steer_cells_per_s: 3.2,
  route_columns: 11,          // the view shows 7 and follows the ship, as the native view does
  eel_weave_cells: 1.4,
  eel_weave_period_s: 7,
  scroll_cells_per_s: 1.6,
  slowmo_scale: 0.2,          // game speed while a shot is about to strike
  slowmo_lookahead_cells: 2.4,
  slowmo_hold_s: 0.5,         // real seconds held after the hook lands, then eased back
};

const EEL_URL = new URL('../storm-eel-preview/assets/storm-eel.glb', import.meta.url).href;
const FLOOR_URL = new URL('../../assets/production/sprites/floor-underwater/scroll-S.png', import.meta.url).href;
const SUB_URL = new URL('../../assets/production/sprites/submarine-yellow/travel-S.png', import.meta.url).href;

const COLUMNS = 7;
const ELEVATION = THREE.MathUtils.degToRad(35);
const SHIP_SCREEN_Y = 0.74;     // native: the ship rides at 74% of the screen height
const NOSE_CELLS = 1.0;            // ship root -> harpoon muzzle on the hull's nose
const BODY_NORTH = -3.3, BODY_SOUTH = 3.8, BODY_HEIGHT = 0.78;   // eel body in three.js space (north = -z)
const HIT_HALF_WIDTH_CELLS = 0.75;
const LOOPS = new Set(['swim', 'restless', 'hooked', 'struggle', 'exhausted']);
const GLOW = {
  swim: (t) => 0.9 + 0.15 * Math.sin(t * 3),
  restless: (t) => 1.1 + 0.9 * Math.max(0, Math.sin(t * 14)),
  hit: (t) => (t < 0.25 ? 0.15 : 0.8),
  hooked: (t) => 0.9 + 0.3 * Math.sin(t * 8),
  escape: () => 1.4,
};

const $ = (id) => document.getElementById(id);
const phone = $('phone'), stage = $('stage');
const worldCanvas = $('world'), eelCanvas = $('eel'), fxCanvas = $('fx');
const wctx = worldCanvas.getContext('2d'), fctx = fxCanvas.getContext('2d');
const button = $('harpoon'), banner = $('banner'), scrim = $('scrim');
const cards = { paused: $('paused-card') };

// ---------------------------------------------------------------- 3D eel
const renderer = new THREE.WebGLRenderer({ canvas: eelCanvas, alpha: true, antialias: true });
renderer.outputColorSpace = THREE.SRGBColorSpace;
eelCanvas.classList.add('graded');
const scene = new THREE.Scene();
scene.add(new THREE.AmbientLight(0xffffff, 1.9));
const key = new THREE.DirectionalLight(0xffffff, 1.1);
key.position.set(-2, 10, 4);
scene.add(key);
const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 100);
camera.position.set(0, Math.sin(ELEVATION), Math.cos(ELEVATION)).multiplyScalar(30);
camera.lookAt(0, 0, 0);
const eelRoot = new THREE.Group();
scene.add(eelRoot);

const gltf = await new GLTFLoader().loadAsync(EEL_URL);
const eel = gltf.scene;
eelRoot.add(eel);
const bones = {}, spotMats = [], bodyMats = [];
eel.traverse((o) => {
  if (o.isBone) bones[o.name] = o;
  if (o.isMesh) {
    o.frustumCulled = false;
    const mats = [].concat(o.material).map((m) => {
      const flat = new THREE.MeshLambertMaterial({ name: m.name, color: m.color, flatShading: true, emissive: m.emissive, emissiveIntensity: m.name === 'eel_spot' ? 1 : 0 });
      (m.name === 'eel_spot' ? spotMats : bodyMats).push(flat);
      return flat;
    });
    o.material = Array.isArray(o.material) ? mats : mats[0];
  }
});
const anchorBones = [bones.head, ...Object.keys(bones).filter((n) => n.startsWith('spine_')).sort().map((n) => bones[n])];
const shadowTex = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d'), grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  grad.addColorStop(0, 'rgba(4,28,58,0.30)'); grad.addColorStop(1, 'rgba(4,28,58,0)');
  g.fillStyle = grad; g.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(c);
})();
const shadowMat = new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false });
const blobs = anchorBones.map((bone) => {
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(1.15, 1.15), shadowMat);
  mesh.rotation.x = -Math.PI / 2; mesh.renderOrder = -1; scene.add(mesh);
  return { bone, mesh };
});

const mixer = new THREE.AnimationMixer(eel);
const clips = Object.fromEntries(gltf.animations.map((c) => [c.name, c]));
let action = null, clipName = '', clipTime = 0, flashUntil = 0;
function play(name, fade = 0.25) {
  const next = mixer.clipAction(clips[name]);
  next.reset();
  next.setLoop(LOOPS.has(name) ? THREE.LoopRepeat : THREE.LoopOnce, Infinity);
  next.clampWhenFinished = true;
  next.play();
  if (action && action !== next) next.crossFadeFrom(action, fade, false);
  action = next; clipName = name; clipTime = 0;
}
mixer.addEventListener('finished', () => { if (clipName === 'hit') play('hooked'); });
function showBanner(html, phase) {
  banner.innerHTML = html; banner.hidden = false;
  setTimeout(() => { if (enc.phase === phase) banner.hidden = true; }, 2600);
}

// ---------------------------------------------------------------- 2D world art
const load = (src) => new Promise((ok, bad) => { const i = new Image(); i.onload = () => ok(i); i.onerror = bad; i.src = src; });
const [floorImg, subImg] = await Promise.all([load(FLOOR_URL), load(SUB_URL)]);
const FLOOR_FRAME = 256, SUB_FRAME = [640, 768], SUB_ROOT = [320, 576], SUB_CELL = 256;
{
  // HUD hull icon: the hull's middle band, like the native HUD.
  const c = document.createElement('canvas'); c.width = 320; c.height = 307;
  c.getContext('2d').drawImage(subImg, 160, 338, 320, 307, 0, 0, 320, 307);
  phone.style.setProperty('--ship', `url(${c.toDataURL()})`);
}

// ---------------------------------------------------------------- layout
let W = 390, H = 844, cell = W / COLUMNS, dpr = 1, hitTop = 0, hitBottom = 0;
function resize() {
  const wide = $('frame').value === 'wide';
  stage.classList.toggle('wide', wide);
  [W, H] = wide ? [470, 820] : $('frame').value.split('x').map(Number);
  cell = W / COLUMNS; dpr = Math.min(devicePixelRatio || 1, 3);
  phone.style.width = `${W}px`; phone.style.height = `${H}px`;
  phone.style.setProperty('--u', `${W / 390}px`);
  const edge = Math.min(cell * 1.6, H * 0.18), margin = edge * 0.22;
  phone.style.setProperty('--arrow', `${edge}px`); phone.style.setProperty('--arrow-margin', `${margin}px`); phone.style.setProperty('--arrow-bottom', `${margin * 1.6}px`);
  for (const c of [worldCanvas, fxCanvas]) { c.width = W * dpr; c.height = H * dpr; }
  renderer.setPixelRatio(dpr); renderer.setSize(W, H, false);
  const halfW = COLUMNS / 2, halfH = halfW * H / W;
  Object.assign(camera, { left: -halfW, right: halfW, top: halfH, bottom: -halfH });
  camera.updateProjectionMatrix(); camera.updateMatrixWorld();
  // Orthographic: screen y is linear in z. Put the snout half a cell below the resistance pill.
  const sy = (z) => toScreen(new THREE.Vector3(0, BODY_HEIGHT, z)).y;
  const wantTop = (74 + 50) * (W / 390) + cell * 0.6, a = sy(BODY_NORTH), b = sy(BODY_NORTH + 1);
  eelRoot.position.z = (wantTop - a) / (b - a);
  // Fixed hit area: the rest body, whatever the animation does.
  hitTop = toScreen(new THREE.Vector3(0, BODY_HEIGHT, eelRoot.position.z + BODY_NORTH)).y;
  hitBottom = toScreen(new THREE.Vector3(0, BODY_HEIGHT, eelRoot.position.z + BODY_SOUTH)).y;
}
const toScreen = (v) => { const p = v.clone().project(camera); return { x: (p.x + 1) / 2 * W, y: (1 - p.y) / 2 * H }; };
$('frame').addEventListener('change', resize);

function roundedTriangle(side, radius = 46, round = 11) {
  const corners = [0, 1, 2].map((i) => { const a = (side > 0 ? 0 : Math.PI) + i * Math.PI * 2 / 3; return [Math.cos(a) * (radius - round * 2), Math.sin(a) * (radius - round * 2)]; });
  const points = [];
  for (const [cx, cy] of corners) {
    const start = Math.atan2(cy, cx) - Math.PI / 3;
    for (let s = 0; s <= 6; s++) { const a = start + s * Math.PI * 2 / 3 / 6; points.push(`${(cx + Math.cos(a) * round).toFixed(2)},${(cy + Math.sin(a) * round).toFixed(2)}`); }
  }
  return points.join(' ');
}
const zones = { [-1]: $('zone-left'), [1]: $('zone-right') };
for (const side of [-1, 1]) for (const poly of zones[side].querySelectorAll('polygon')) poly.setAttribute('points', roundedTriangle(side));

// ---------------------------------------------------------------- encounter state
let enc;
function restart() {
  enc = { phase: 'aiming', t: 0, paused: false, shipX: CENTER, camX: CENTER, eelX: CENTER, cool: 0, shots: 0, harpoon: null, steer: 0 };
  if (anchor.parent) anchor.parent.remove(anchor);
  slow = 1; slowHold = 0; focus = null;
  mixer.stopAllAction(); action = null; play('swim', 0);
  eelRoot.position.x = 0;
  hideOverlays(); banner.hidden = true; pressed = false;
  phone.dataset.phase = 'aiming';
}
const CENTER = RULES.route_columns / 2;
const screenX = (wx) => W / 2 + (wx - enc.camX) * cell;
const anchor = new THREE.Object3D();
const shipRoot = () => ({ x: screenX(enc.shipX), y: H * SHIP_SCREEN_Y });
const muzzle = () => { const r = shipRoot(); return { x: r.x, y: r.y - NOSE_CELLS * cell }; };
const ready = () => enc.phase === 'aiming' && !enc.paused && enc.cool <= 0 && !enc.harpoon;

function fire() {
  if (!ready()) return;
  const m = muzzle();
  // Straight up from the ship; the shot keeps its column even if the ship steers on.
  enc.harpoon = { state: 'flying', wx: enc.shipX, y: m.y };
  enc.cool = RULES.cooldown_s; enc.shots++;
}

function hitTest(x, y) {
  const cx = screenX(enc.eelX), cy = (hitTop + hitBottom) / 2;
  const rx = HIT_HALF_WIDTH_CELLS * cell, ry = (hitBottom - hitTop) / 2;
  return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1;
}

const tmp = new THREE.Vector3();
function hook(x, y) {
  // Pin the harpoon to the body part it struck, on the eel's back, so it rides every animation.
  let best = null, bestD = Infinity;
  for (const b of anchorBones) {
    b.getWorldPosition(tmp);
    const s = toScreen(tmp), d = (s.x - x) ** 2 + (s.y - y) ** 2;
    if (d < bestD) { bestD = d; best = b; }
  }
  best.getWorldPosition(tmp); tmp.y += 0.38;
  best.add(anchor); anchor.position.copy(best.worldToLocal(tmp.clone()));
  enc.harpoon = { state: 'attached', x, y, at: enc.t };
  enc.phase = 'hooked'; phone.dataset.phase = 'hooked';
  play('hit', 0.1); flashUntil = performance.now() + 140;
  showBanner('Hooked!<small>The chase begins next</small>', 'hooked');
  slowHold = RULES.slowmo_hold_s;
}

// ---------------------------------------------------------------- input
let pressed = false;
button.addEventListener('pointerdown', (e) => {
  e.preventDefault(); button.setPointerCapture(e.pointerId); pressed = true; fire();
});
for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) button.addEventListener(type, () => { pressed = false; });
button.addEventListener('click', (e) => e.preventDefault());   // firing happens on press, not release
button.addEventListener('keydown', (e) => { if ((e.key === 'Enter') && !e.repeat) { pressed = true; fire(); e.preventDefault(); } });
button.addEventListener('keyup', (e) => { if (e.key === 'Enter') pressed = false; });

const held = new Map(), keys = { ArrowLeft: false, ArrowRight: false };
function updateSteer() {
  let v = 0;
  for (const side of held.values()) v += side;
  v += (keys.ArrowRight ? 1 : 0) - (keys.ArrowLeft ? 1 : 0);
  enc.steer = enc.paused ? 0 : Math.max(-1, Math.min(1, v));
  for (const side of [-1, 1]) zones[side].classList.toggle('down', enc.steer * side > 0);
}
for (const side of [-1, 1]) {
  const zone = zones[side];
  zone.addEventListener('pointerdown', (e) => { zone.setPointerCapture(e.pointerId); held.set(e.pointerId, side); updateSteer(); e.preventDefault(); });
  zone.addEventListener('pointermove', (e) => {
    if (!held.has(e.pointerId)) return;
    const r = phone.getBoundingClientRect(); held.set(e.pointerId, e.clientX < r.left + r.width / 2 ? -1 : 1); updateSteer();
  });
  for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) zone.addEventListener(type, (e) => { held.delete(e.pointerId); updateSteer(); });
}
addEventListener('keydown', (e) => {
  if (e.key in keys && !e.repeat) { keys[e.key] = true; updateSteer(); e.preventDefault(); }
  if (e.key === ' ' && !e.repeat && !(e.target instanceof HTMLButtonElement && e.target !== button)) { pressed = true; fire(); e.preventDefault(); }
  if (e.key === 'Escape') pause();
});
addEventListener('keyup', (e) => { if (e.key in keys) { keys[e.key] = false; updateSteer(); } if (e.key === ' ') pressed = false; });
addEventListener('blur', () => { held.clear(); keys.ArrowLeft = keys.ArrowRight = false; pressed = false; updateSteer(); });

function hideOverlays() { scrim.hidden = true; for (const c of Object.values(cards)) c.hidden = true; }
function show(card) { scrim.hidden = false; for (const [n, c] of Object.entries(cards)) c.hidden = n !== card; }
function pause() {
  if (enc.paused || enc.phase === 'escaped') return;
  enc.paused = true; held.clear(); updateSteer(); show('paused'); $('resume').focus();
}
$('pause').addEventListener('click', pause);
$('resume').addEventListener('click', () => { enc.paused = false; hideOverlays(); });
$('return-early').addEventListener('click', restart);
$('restart').addEventListener('click', () => { restart(); button.focus(); });
$('jump-restless').addEventListener('click', () => { if (enc.phase === 'aiming') enc.t = Math.max(enc.t, RULES.window_s - RULES.restless_s - 0.01); });
for (const tab of document.querySelectorAll('[role="tab"]')) {
  tab.addEventListener('click', () => {
    for (const t of document.querySelectorAll('[role="tab"]')) t.setAttribute('aria-selected', String(t === tab));
    for (const v of document.querySelectorAll('.view')) v.hidden = v.id !== tab.dataset.view;
  });
}

// ---------------------------------------------------------------- drawing
const INK = '#24364d';
function drawHarpoon(x, y, angle, { head = true } = {}) {
  // Tip at (x, y); `angle` is the direction the head points.
  const u = W / 390, len = cell * 0.95;
  fctx.save(); fctx.translate(x, y); fctx.rotate(angle + Math.PI / 2);
  fctx.lineJoin = 'round'; fctx.lineCap = 'round';
  // shaft
  fctx.fillStyle = '#c9d4df'; fctx.strokeStyle = INK; fctx.lineWidth = 2.2 * u;
  fctx.beginPath(); fctx.roundRect(-2.6 * u, 8 * u, 5.2 * u, len - 8 * u, 2 * u); fctx.fill(); fctx.stroke();
  // red collar near the tail
  fctx.fillStyle = '#e2553f';
  fctx.beginPath(); fctx.roundRect(-4.2 * u, len - 13 * u, 8.4 * u, 7 * u, 2.5 * u); fctx.fill(); fctx.stroke();
  if (head) {
    // barbed head
    fctx.fillStyle = '#eef3f7';
    fctx.beginPath();
    fctx.moveTo(0, -3 * u); fctx.lineTo(8 * u, 14 * u); fctx.lineTo(3 * u, 12 * u); fctx.lineTo(2.6 * u, 16 * u);
    fctx.lineTo(-2.6 * u, 16 * u); fctx.lineTo(-3 * u, 12 * u); fctx.lineTo(-8 * u, 14 * u); fctx.closePath();
    fctx.fill(); fctx.stroke();
  }
  fctx.restore();
  return { x: x - Math.cos(angle) * len, y: y - Math.sin(angle) * len };   // tail, where the cable ties on
}

function drawCable(a, b, slack, t) {
  const u = W / 390, mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
  const dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1;
  const nx = -dy / d, ny = dx / d, sag = slack * Math.min(d * 0.18, cell * 0.8) * Math.sin(t * 9);
  const cx = mx + nx * sag + (slack ? cell * 0.15 * slack : 0), cy = my + ny * sag;
  const path = () => { fctx.beginPath(); fctx.moveTo(a.x, a.y); fctx.quadraticCurveTo(cx, cy, b.x, b.y); };
  fctx.lineCap = 'round';
  path(); fctx.strokeStyle = 'rgba(5,31,69,.25)'; fctx.lineWidth = 7 * u; fctx.stroke();
  path(); fctx.strokeStyle = '#6b4526'; fctx.lineWidth = 5 * u; fctx.stroke();
  path(); fctx.strokeStyle = '#f3dcae'; fctx.lineWidth = 2.8 * u; fctx.stroke();
  // braid ticks
  fctx.setLineDash([2.2 * u, 4.4 * u]); fctx.lineDashOffset = -t * 40;
  path(); fctx.strokeStyle = '#a77a4b'; fctx.lineWidth = 2.8 * u; fctx.stroke();
  fctx.setLineDash([]);
}

function drawWorld(t, scroll) {
  wctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const f = Math.floor(t * 12) % 12, fx0 = (f % 6) * FLOOR_FRAME, fy0 = Math.floor(f / 6) * FLOOR_FRAME;
  const off = (scroll % 1) * cell, ox = screenX(0);
  wctx.fillStyle = '#0b2f63'; wctx.fillRect(0, 0, W, H);
  for (let y = -1; y * cell < H + cell; y++) for (let x = 0; x < RULES.route_columns; x++) {
    wctx.drawImage(floorImg, fx0, fy0, FLOOR_FRAME, FLOOR_FRAME, ox + x * cell, y * cell + off, cell + 0.5, cell + 0.5);
  }
  // Faint cell seams, as the native seabed draws them.
  wctx.strokeStyle = 'rgba(190,245,255,.22)'; wctx.lineWidth = Math.max(1, cell / 60); wctx.beginPath();
  for (let x = 0; x <= RULES.route_columns; x++) { wctx.moveTo(ox + x * cell, 0); wctx.lineTo(ox + x * cell, H); }
  for (let y = -1; y * cell < H + cell; y++) { wctx.moveTo(0, y * cell + off); wctx.lineTo(W, y * cell + off); }
  wctx.stroke();
  const r = shipRoot(), k = cell / SUB_CELL, sx = (f % 6) * SUB_FRAME[0], sy = Math.floor(f / 6) * SUB_FRAME[1];
  wctx.drawImage(subImg, sx, sy, SUB_FRAME[0], SUB_FRAME[1], r.x - SUB_ROOT[0] * k, r.y - SUB_ROOT[1] * k, SUB_FRAME[0] * k, SUB_FRAME[1] * k);
}

function drawFx(t) {
  fctx.setTransform(1, 0, 0, 1, 0, 0); fctx.clearRect(0, 0, fxCanvas.width, fxCanvas.height);
  fctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  drawIris();
  if ($('opt-hit').checked) {
    const cx = screenX(enc.eelX), cy = (hitTop + hitBottom) / 2;
    fctx.fillStyle = 'rgba(255,51,102,.22)'; fctx.strokeStyle = 'rgba(255,51,102,.8)'; fctx.lineWidth = 2;
    fctx.beginPath(); fctx.ellipse(cx, cy, HIT_HALF_WIDTH_CELLS * cell, (hitBottom - hitTop) / 2, 0, 0, Math.PI * 2); fctx.fill(); fctx.stroke();
  }
  const h = enc.harpoon;
  if (!h) return;
  const m = muzzle();
  if (h.state === 'attached') {
    anchor.getWorldPosition(tmp);
    const p = toScreen(tmp);
    const ang = Math.atan2(p.y - m.y, p.x - m.x);
    // Taut line with a little thrum; the head is buried in the eel.
    const tail = drawHarpoonTailFirst(p, ang);
    drawCable(m, tail, 0.06, t);
    drawHarpoon(p.x, p.y, ang, { head: false });
    const age = enc.t - h.at;
    if (age < 0.35) {
      fctx.strokeStyle = `rgba(255,246,223,${1 - age / 0.35})`; fctx.lineWidth = 3 * (W / 390);
      fctx.beginPath(); fctx.arc(p.x, p.y, cell * (0.2 + age * 1.6), 0, Math.PI * 2); fctx.stroke();
    }
    return;
  }
  const hx = screenX(h.wx);
  const ang = h.state === 'flying' ? -Math.PI / 2 : Math.atan2(m.y - h.y, m.x - hx) + Math.PI;
  const tail = { x: hx - Math.cos(ang) * cell * 0.95, y: h.y - Math.sin(ang) * cell * 0.95 };
  drawCable(m, tail, h.state === 'flying' ? 0.35 : 0.9, t);
  drawHarpoon(hx, h.y, ang);
}
// Slow-motion focus: the scene dims outside a circle that shrinks onto the impact point (then the
// pinned anchor) as the game slows, with a bright ring on its edge; it opens again as speed returns.
function drawIris() {
  const k = Math.max(0, Math.min(1, (1 - slow) / (1 - RULES.slowmo_scale)));
  if (k <= 0.01 || !focus) return;
  if (enc.harpoon?.state === 'attached') { anchor.getWorldPosition(tmp); focus = toScreen(tmp); }
  const far = Math.hypot(W, H), near = cell * 1.5, e = k * k * (3 - 2 * k);
  const r = far + (near - far) * e, u = W / 390;
  fctx.save();
  fctx.beginPath(); fctx.rect(0, 0, W, H); fctx.arc(focus.x, focus.y, r, 0, Math.PI * 2);
  fctx.fillStyle = `rgba(4, 20, 48, ${0.5 * e})`; fctx.fill('evenodd');
  fctx.strokeStyle = `rgba(255, 246, 223, ${0.9 * e})`; fctx.lineWidth = 3 * u;
  fctx.beginPath(); fctx.arc(focus.x, focus.y, r, 0, Math.PI * 2); fctx.stroke();
  fctx.strokeStyle = `rgba(255, 246, 223, ${0.45 * e})`; fctx.lineWidth = 1.5 * u;
  fctx.beginPath(); fctx.arc(focus.x, focus.y, r * 1.18 + cell * 0.2, 0, Math.PI * 2); fctx.stroke();
  fctx.restore();
}
// Tail position for a harpoon whose tip sits at p pointing along ang (drawn after the cable).
const drawHarpoonTailFirst = (p, ang) => ({ x: p.x - Math.cos(ang) * cell * 0.95, y: p.y - Math.sin(ang) * cell * 0.95 });

// ---------------------------------------------------------------- slow motion
// When the flying harpoon's column will cross the (fixed) hit area within the lookahead, the whole
// game slows so the strike reads; it holds briefly after the hook, then eases back to full speed.
let slow = 1, slowHold = 0;
let focus = null;   // screen point the slow-motion iris closes on
function strikeImminent() {
  const h = enc.harpoon;
  if (enc.phase !== 'aiming' || h?.state !== 'flying') return false;
  const x = screenX(h.wx), reach = RULES.slowmo_lookahead_cells * cell;
  for (let d = 0; d <= reach; d += cell * 0.2) if (hitTest(x, h.y - d)) { focus = { x, y: h.y - d }; return true; }
  return false;
}
function updateSlow(real) {
  let target = 1;
  if (slowHold > 0) { slowHold -= real; target = RULES.slowmo_scale; }
  else if (strikeImminent()) target = RULES.slowmo_scale;
  slow += (target - slow) * Math.min(1, real * (target < slow ? 14 : 3.5));
  if (Math.abs(slow - 1) < 0.01) slow = 1;
}

// ---------------------------------------------------------------- loop
let scroll = 0, artTime = 0;
const clock = new THREE.Clock();
function step(dt) {
  enc.t += dt;
  scroll += dt * RULES.scroll_cells_per_s;
  enc.shipX = Math.max(0.4, Math.min(RULES.route_columns - 0.4, enc.shipX + enc.steer * RULES.steer_cells_per_s * dt));
  // Camera follows the ship with a small dead zone and stops at the route edges (native view).
  const half = COLUMNS / 2, offset = enc.shipX - enc.camX;
  const want = Math.abs(offset) > 0.7 ? enc.shipX - Math.sign(offset) * 0.7 : enc.camX;
  enc.camX += (Math.max(half, Math.min(RULES.route_columns - half, want)) - enc.camX) * Math.min(1, dt * 4);
  const weave = enc.phase === 'hooked' ? 0.4 : 1;
  const eelWant = CENTER + RULES.eel_weave_cells * Math.sin(2 * Math.PI * enc.t / RULES.eel_weave_period_s) * weave;
  enc.eelX += (eelWant - enc.eelX) * Math.min(1, dt * 3);
  eelRoot.position.x = enc.eelX - enc.camX;
  enc.cool = Math.max(0, enc.cool - dt);

  if (enc.phase === 'aiming') {
    if (enc.t >= RULES.window_s - RULES.restless_s && clipName === 'swim') play('restless');
    if (enc.t >= RULES.window_s && !enc.harpoon) {
      // The window closes once nothing is in flight; a shot already on its way still counts.
      enc.phase = 'escaped'; phone.dataset.phase = 'none'; play('escape', 0.15);
      showBanner('It got away<small>No recipe this time</small>', 'escaped');
    }
  }

  const h = enc.harpoon;
  if (h?.state === 'flying') {
    h.y -= RULES.harpoon_cells_per_s * cell * dt;
    if (enc.phase === 'aiming' && hitTest(screenX(h.wx), h.y)) hook(screenX(h.wx), h.y);
    else if (h.y < -cell) h.state = 'reeling';
  } else if (h?.state === 'reeling') {
    // Reel back toward the ship's nose (world x in cells, y in screen px).
    const m = muzzle(), hx = screenX(h.wx), d = Math.hypot(m.x - hx, m.y - h.y), s = RULES.reel_cells_per_s * cell * dt;
    if (d <= s + cell * 0.95) enc.harpoon = null;
    else { h.wx += (m.x - hx) / d * s / cell; h.y += (m.y - h.y) / d * s; }
  }
}

function syncUi() {
  const state = enc.phase !== 'aiming' ? 'hidden' : enc.paused ? 'paused' : ready() ? 'ready' : 'cooling';
  button.dataset.state = state;
  button.classList.toggle('is-down', pressed && state !== 'hidden');
  button.style.setProperty('--p', state === 'cooling' ? (1 - enc.cool / RULES.cooldown_s).toFixed(3) : '1');
  button.setAttribute('aria-disabled', String(state !== 'ready'));
  button.setAttribute('aria-label', state === 'ready' ? 'Harpoon' : 'Harpoon, reloading');
  const rows = {
    Phase: enc.paused ? `${enc.phase} (paused)` : enc.phase === 'aiming' && enc.t >= RULES.window_s - RULES.restless_s ? 'aiming · restless' : enc.phase,
    'Window (review only)': `${Math.min(enc.t, RULES.window_s).toFixed(1)} / ${RULES.window_s} s`,
    Harpoon: enc.harpoon ? enc.harpoon.state : ready() ? 'ready' : enc.phase === 'aiming' ? 'reloading' : '—',
    'Shots fired': enc.shots,
    'Game speed': `${Math.round(slow * 100)}%`,
    Hooks: enc.phase === 'hooked' ? 1 : 0,
  };
  $('state').innerHTML = Object.entries(rows).map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('');
}

$('rules').innerHTML = [
  `Shooting window: <b>${RULES.window_s} s</b>, no countdown. The eel turns <b>restless</b> for the last ${RULES.restless_s} s, keeping its hit area and movement.`,
  `One shot per fresh press, straight up from the ship. Cooldown <b>${RULES.cooldown_s} s</b> from firing, shown by the filling ring; no ammunition.`,
  `Slow motion: when a shot is about to strike, the scene dims outside a circle that closes onto the impact point and the game drops to <b>${Math.round(RULES.slowmo_scale * 100)}%</b> speed, holds briefly after the hook, then eases back. A shot that just misses also slows, then recovers.`,
  `A miss reels back in. A hit pins the harpoon to the struck body part and the line stays tied to the ship: one hook, no recipe yet.`,
  `Steering (halves of the playfield) and the Harpoon button are separate touches: you can hold a direction and fire with the other thumb.`,
].map((s) => `<li>${s}</li>`).join('');

// Button states gallery: the same component, frozen in each state.
$('gallery').innerHTML = [['ready', 1, false, 'Ready'], ['ready', 1, true, 'Pressed'], ['cooling', 0.25, false, 'Reloading 25%'], ['cooling', 0.75, false, 'Reloading 75%'], ['paused', 1, false, 'Paused']]
  .map(([s, p, down, label]) => `<figure><div class="harpoon-btn${down ? ' is-down' : ''}" data-state="${s}" style="--p:${p}" role="img" aria-label="Harpoon button, ${label}">${button.innerHTML}</div><figcaption>${label}</figcaption></figure>`).join('')
  + '<figure><div class="harpoon-btn" data-state="hidden" aria-hidden="true">' + button.innerHTML + '</div><figcaption>Hidden once hooked or escaped</figcaption></figure>';

resize();
restart();
renderer.setAnimationLoop(() => {
  const real = Math.min(clock.getDelta(), 0.1);
  if (!enc.paused) updateSlow(real);
  const dt = enc.paused ? 0 : real * slow;
  artTime += dt;
  step(dt);
  mixer.update(dt);
  clipTime += dt;
  const glow = (GLOW[clipName] ?? (() => 1))(clipTime);
  for (const m of spotMats) m.emissiveIntensity = glow;
  const flash = performance.now() < flashUntil;
  for (const m of bodyMats) m.emissive.setScalar(flash ? 0.6 : 0);
  eel.updateMatrixWorld(true);
  for (const { bone, mesh } of blobs) { bone.getWorldPosition(tmp); mesh.position.set(tmp.x, 0.02, tmp.z); }
  drawWorld(artTime, scroll);
  renderer.render(scene, camera);
  drawFx(artTime);
  syncUi();
});
