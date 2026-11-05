import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js';
import { GLTFLoader } from 'https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/controls/OrbitControls.js';

const EEL_URL = new URL('./assets/storm-eel.glb', import.meta.url).href;
const FLOOR_URL = new URL('../../assets/production/sprites/floor-underwater/scroll-S.png', import.meta.url).href;
const SUB_URL = new URL('../../assets/production/sprites/submarine-yellow/travel-S.png', import.meta.url).href;

// Game framing: 7 columns across the phone; ordinary orthographic character
// camera at 35° elevation looking north. Both the eel and the ship swim north,
// so they hold their screen positions while the seabed scrolls under them.
const COLUMNS = 7;
const ELEVATION = THREE.MathUtils.degToRad(35);
const EEL_SCREEN_Y = 0.34;      // eel body centre, fraction of screen height
const SHIP_SCREEN_Y = 0.80;     // ship root
const SCROLL_CELLS_PER_S = 1.6;

const LOOPS = new Set(['swim', 'restless', 'hooked', 'struggle', 'exhausted']);
const ORDER = ['swim', 'restless', 'hit', 'hooked', 'struggle', 'windup', 'attack', 'recover', 'escape', 'exhausted'];
const LABELS = { swim: 'Swim forward', restless: 'Restless (window ending)', hit: 'Hit by harpoon', hooked: 'Hooked (straining)',
  struggle: 'Struggle (thrash)', windup: 'Turn round & charge', attack: 'Discharge (mouth gape)', recover: 'Turn back to swim',
  escape: 'Escape', exhausted: 'Exhausted / caught' };
// Lateral-organ glow per clip: f(t seconds into clip) -> emissive intensity.
const GLOW = {
  swim: (t) => 0.9 + 0.15 * Math.sin(t * 3),
  restless: (t) => 1.1 + 0.9 * Math.max(0, Math.sin(t * 14)),
  hit: (t) => (t < 0.25 ? 0.15 : 0.8),
  hooked: (t) => 0.9 + 0.3 * Math.sin(t * 8),
  struggle: (t) => 1.0 + 0.6 * Math.abs(Math.sin(t * 9)),
  windup: (t) => 1 + 5 * Math.min(1, t / 0.9) * (0.75 + 0.25 * Math.sin(t * 40)),
  attack: (t) => (t < 0.42 ? 9 : 1 + 8 * Math.exp(-(t - 0.42) * 6)),
  recover: (t) => 1 + 1.5 * Math.exp(-t * 4),
  escape: (t) => 1.4,
  exhausted: (t) => 0.2 + 0.15 * Math.max(0, Math.sin(t * 2.3)) * (Math.sin(t * 17) > 0.6 ? 1 : 0.2),
};

const phone = document.getElementById('phone');
const canvas = document.getElementById('view');
const world = document.getElementById('world');
const wctx = world.getContext('2d');
const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 3));
renderer.outputColorSpace = THREE.SRGBColorSpace;

// Flat lighting: mostly ambient, with a soft key so the low-poly facets still read.
const scene = new THREE.Scene();
scene.add(new THREE.AmbientLight(0xffffff, 1.9));
const key = new THREE.DirectionalLight(0xffffff, 1.1);
key.position.set(-2, 10, 4);
scene.add(key);

const ortho = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 100);
ortho.position.set(0, Math.sin(ELEVATION), Math.cos(ELEVATION)).multiplyScalar(30);
ortho.lookAt(0, 0, 0);
const persp = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
persp.position.set(6, 5, 7);
const controls = new OrbitControls(persp, canvas);
controls.target.set(0, 0.7, 0);
controls.enabled = false;
let camera = ortho;
let mode = 'map';
let W = 390, H = 844, cell = W / COLUMNS, dpr = 1;

const eelRoot = new THREE.Group();
scene.add(eelRoot);

function resize() {
  W = phone.clientWidth; H = phone.clientHeight; cell = W / COLUMNS;
  dpr = Math.min(devicePixelRatio, 3);
  renderer.setSize(W, H, false);
  for (const c of [world]) { c.width = W * dpr; c.height = H * dpr; }
  const halfW = COLUMNS / 2, halfH = halfW * H / W;
  Object.assign(ortho, { left: -halfW, right: halfW, top: halfH, bottom: -halfH });
  ortho.updateProjectionMatrix(); ortho.updateMatrixWorld();
  persp.aspect = W / H; persp.updateProjectionMatrix();
  // place the eel so its body centre sits at EEL_SCREEN_Y (orthographic: linear in z)
  const ndc = (z) => new THREE.Vector3(0, 0.78, z).project(ortho).y;
  const a = ndc(0), b = ndc(1), want = 1 - 2 * EEL_SCREEN_Y;
  eelRoot.position.z = (want - a) / (b - a);
}
new ResizeObserver(resize).observe(phone);

// ---------------------------------------------------------------- shadow
// Soft blobs along the spine: the shadow follows the curl without a shadow map.
const shadowTex = (() => {
  const c = document.createElement('canvas'); c.width = c.height = 64;
  const g = c.getContext('2d'); const grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  grad.addColorStop(0, 'rgba(4,28,58,0.30)'); grad.addColorStop(1, 'rgba(4,28,58,0)');
  g.fillStyle = grad; g.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(c);
})();
const shadowMat = new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false });
const blobs = [];

// Static hit area: the harpoon target must not change with animation.
const hitArea = new THREE.Mesh(new THREE.CircleGeometry(1, 48), new THREE.MeshBasicMaterial({ color: 0xff3366, transparent: true, opacity: 0.25, depthTest: false }));
hitArea.rotation.x = -Math.PI / 2;
hitArea.scale.set(0.9, 3.7, 1);
hitArea.position.set(0, 0.05, 0.3);
hitArea.renderOrder = 10;
hitArea.visible = false;
eelRoot.add(hitArea);

// ---------------------------------------------------------------- eel
let mixer, clips = {}, current = null, currentName = '', clipTime = 0, spotMats = [], allMats = [], bones = {};
let queue = [], hold = 0, flashUntil = 0, repeatFlow = null;
const gltf = await new GLTFLoader().loadAsync(EEL_URL);
const eel = gltf.scene;
eelRoot.add(eel);
eel.traverse((o) => {
  if (o.isBone) bones[o.name] = o;
  if (o.isMesh) {
    o.frustumCulled = false;
    // faceted, flat-lit material keeping the authored colours
    const mats = [].concat(o.material).map((m) => {
      const flat = new THREE.MeshLambertMaterial({ name: m.name, color: m.color, flatShading: true,
        emissive: m.emissive, emissiveIntensity: m.name === 'eel_spot' ? 1 : 0 });
      allMats.push(flat);
      if (m.name === 'eel_spot') spotMats.push(flat);
      return flat;
    });
    o.material = Array.isArray(o.material) ? mats : mats[0];
  }
});
const spineBones = Object.keys(bones).filter((n) => n.startsWith('spine_')).sort().map((n) => bones[n]);
for (const b of [bones.head, ...spineBones]) {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), shadowMat);
  m.rotation.x = -Math.PI / 2; m.renderOrder = -1;
  scene.add(m); blobs.push({ bone: b, mesh: m });
}

mixer = new THREE.AnimationMixer(eel);
for (const c of gltf.animations) clips[c.name] = c;
mixer.addEventListener('finished', () => advance());

const clipBox = document.getElementById('clips');
for (const name of ORDER) {
  const b = document.createElement('button');
  b.textContent = LABELS[name] + (LOOPS.has(name) ? ' ↻' : '');
  b.dataset.clip = name;
  b.addEventListener('click', () => {
    queue = []; hold = 0; repeatFlow = null;
    if (name === 'attack') { play('windup'); queue = [['attack'], ['recover'], ['swim', 0]]; return; }
    play(name);
    if (!LOOPS.has(name)) queue = name === 'escape' ? [['pause', 1.0], ['reset']] : name === 'windup' ? [['attack'], ['recover'], ['swim', 0]] : [['swim', 0]];
  });
  clipBox.append(b);
}

function play(name, fade = 0.25) {
  const next = mixer.clipAction(clips[name]);
  next.reset();
  next.setLoop(LOOPS.has(name) ? THREE.LoopRepeat : THREE.LoopOnce, Infinity);
  next.clampWhenFinished = true;
  next.play();
  if (current && current !== next) next.crossFadeFrom(current, fade, false);
  current = next; currentName = name; clipTime = 0;
  if (name === 'hit') flashUntil = performance.now() + 120;
  document.getElementById('now').textContent = LABELS[name];
  for (const b of clipBox.children) b.classList.toggle('on', b.dataset.clip === name);
}

// queue entries: [clip, seconds-to-hold-if-loop]
function advance() {
  if (!queue.length) { if (repeatFlow) repeatFlow(); return; }
  const [name, secs] = queue.shift();
  if (name === 'pause') { hold = secs; return; }
  if (name === 'reset') { mixer.stopAllAction(); current = null; play('swim', 0); return; }
  play(name);
  hold = LOOPS.has(name) ? secs : 0;
}

const STRIKE = [['windup'], ['attack'], ['recover']];
function flowAttack() {
  play('swim'); hold = 2.4;
  queue = [...STRIKE, ['swim', 0.01]];
  repeatFlow = flowAttack;
}
document.getElementById('flow-attack').addEventListener('click', flowAttack);
document.getElementById('flow-catch').addEventListener('click', () => {
  repeatFlow = null;
  play('swim'); hold = 1.5;
  queue = [['hit'], ['hooked', 1.6], ...STRIKE, ['struggle', 1.4], ['hooked', 1.0], ...STRIKE, ['struggle', 1.0], ['exhausted', 0]];
});
document.getElementById('flow-escape').addEventListener('click', () => {
  repeatFlow = null;
  play('swim'); hold = 1.2;
  queue = [['restless', 2.2], ['escape'], ['pause', 1.0], ['reset']];
});

const grade = document.getElementById('opt-grade');
grade.addEventListener('change', () => canvas.classList.toggle('graded', grade.checked));
canvas.classList.toggle('graded', grade.checked);
const scrollOpt = document.getElementById('opt-scroll');
document.getElementById('opt-hit').addEventListener('change', (e) => { hitArea.visible = e.target.checked; });
const speed = document.getElementById('opt-speed');
speed.addEventListener('input', () => { document.getElementById('speed-out').textContent = speed.value + '×'; });

for (const tab of document.querySelectorAll('[role="tab"]')) {
  tab.addEventListener('click', () => {
    mode = tab.dataset.view;
    for (const t of document.querySelectorAll('[role="tab"]')) t.setAttribute('aria-selected', String(t === tab));
    phone.classList.toggle('inspect', mode === 'inspect');
    camera = mode === 'inspect' ? persp : ortho;
    controls.enabled = mode === 'inspect';
  });
}

// ---------------------------------------------------------------- world (2D)
const load = (src) => new Promise((ok, bad) => { const i = new Image(); i.onload = () => ok(i); i.onerror = bad; i.src = src; });
const [floorImg, subImg] = await Promise.all([load(FLOOR_URL), load(SUB_URL)]);
const FLOOR_FRAME = 256;                         // 6 x 2 atlas, 12 fps caustics
const SUB_FRAME = [640, 768], SUB_ROOT = [320, 576], SUB_CELL = 256;   // source px per cell
let scrollRows = 0;

function drawWorld(t) {
  wctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const f = Math.floor(t * 12) % 12, fx0 = (f % 6) * FLOOR_FRAME, fy0 = Math.floor(f / 6) * FLOOR_FRAME;
  const off = (scrollRows % 1) * cell;
  for (let y = -1; y * cell < H + cell; y++) {
    for (let x = 0; x < COLUMNS; x++) {
      wctx.drawImage(floorImg, fx0, fy0, FLOOR_FRAME, FLOOR_FRAME, x * cell, y * cell + off, cell + 0.5, cell + 0.5);
    }
  }
  // ship: travel loop
  const img = subImg;
  const sf = Math.floor(t * 12) % 12, sx = (sf % 6) * SUB_FRAME[0], sy = Math.floor(sf / 6) * SUB_FRAME[1];
  const k = cell / SUB_CELL;
  wctx.drawImage(img, sx, sy, SUB_FRAME[0], SUB_FRAME[1], W / 2 - SUB_ROOT[0] * k, H * SHIP_SCREEN_Y - SUB_ROOT[1] * k, SUB_FRAME[0] * k, SUB_FRAME[1] * k);
}


play('swim', 0);
resize();
flowAttack();

const clock = new THREE.Clock();
let worldTime = 0;
const tmp = new THREE.Vector3();
renderer.setAnimationLoop(() => {
  const dt = clock.getDelta() * Number(speed.value);
  worldTime += dt;
  mixer.update(dt);
  clipTime += dt;
  if (hold > 0) { hold -= dt; if (hold <= 0) { hold = 0; advance(); } }
  if (scrollOpt.checked) scrollRows += dt * SCROLL_CELLS_PER_S;

  const glow = (GLOW[currentName] ?? (() => 1))(clipTime);
  for (const m of spotMats) m.emissiveIntensity = glow;
  const flash = performance.now() < flashUntil;
  for (const m of allMats) if (!spotMats.includes(m)) m.emissive.setScalar(flash ? 0.6 : 0);

  eel.updateMatrixWorld(true);
  for (const { bone, mesh } of blobs) {
    bone.getWorldPosition(tmp);
    mesh.position.set(tmp.x, 0.02, tmp.z);
    const s = bone === bones.head ? 1.0 : 1.15;
    mesh.scale.set(s, s, 1);
  }

  if (mode === 'map') drawWorld(worldTime);
  controls.update();
  renderer.render(scene, camera);
});
