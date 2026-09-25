import { ART, SCENERY } from './assets.js';
import { skyAtHeight } from './altitude.js';
import './sky.css';

// Viewport scenery is separate from the hotel camera and never touches game state.
// [atlas frame, horizontal %, vertical %, size in vmin, period in seconds, phase]
const ISLANDS = [
  [0, 7, 26, 31, 23, .1], [1, 94, 38, 33, 29, .55],
  [0, 5, 62, 29, 27, .75], [2, 95, 73, 27, 21, .35],
  [2, 7, 94, 32, 31, .45],
];
const CLOUDS = [
  [5, 1, 8, 40, 53, .3], [3, 95, 13, 42, 61, .65],
  [4, 14, 23, 21, 47, .15], [4, 93, 30, 23, 59, .8],
  [3, 1, 44, 32, 43, .7], [5, 98, 54, 40, 49, .25],
  [4, 8, 69, 24, 57, .45], [3, 90, 85, 32, 51, .9],
  [5, 1, 97, 44, 63, .2],
];
const SEA = [[5, 2, 87, 65, 67, .2], [3, 98, 90, 64, 73, .7], [4, 22, 99, 40, 79, .4], [4, 80, 98, 42, 83, .6]];
// Individual bounds in the original generated sheet, without resampling it.
const CELESTIAL = [[163, 94, 383, 389], [722, 92, 396, 395], [23, 542, 627, 666], [648, 490, 600, 714]];
// [x%, y%, size px, reveal floor]. Keep the hotel's central column clear.
const STARS = [
  [8, 26, 27, 50], [87, 45, 23, 50], [22, 52, 13, 54], [94, 22, 15, 58],
  [5, 64, 16, 62], [77, 21, 11, 66], [17, 18, 12, 70], [81, 66, 25, 75],
  [26, 32, 14, 78], [96, 57, 13, 82], [9, 46, 10, 86], [75, 38, 12, 90],
  [20, 72, 14, 94], [92, 72, 17, 100], [3, 35, 12, 105], [26, 61, 11, 110],
  [89, 16, 9, 115], [75, 76, 13, 120], [3, 76, 12, 125], [97, 38, 11, 130],
  [30, 22, 10, 135], [72, 56, 11, 140], [12, 22, 42, 150], [92, 65, 37, 150],
];
const CONSTELLATIONS = [
  { name: 'bunny', floor: 125, x: 13, y: 40,
    points: [[23,81],[17,60],[29,44],[44,40],[48,28],[43,6],[52,3],[59,27],[68,5],[77,8],[68,35],[79,44],[76,55],[61,61],[67,78],[80,83],[53,84],[49,75],[41,84]],
    paths: [[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,0],[3,13],[1,17]] },
  { name: 'frog', floor: 130, x: 14, y: 69,
    points: [[13,62],[25,44],[26,23],[36,17],[47,31],[57,31],[66,17],[77,23],[76,44],[88,62],[71,77],[30,77],[36,50],[66,50]],
    paths: [[0,1,2,3,4,5,6,7,8,9,10,11,0],[1,12,13,8],[12,11],[13,10]] },
  { name: 'cat', floor: 125, x: 86, y: 55,
    points: [[22,27],[20,8],[38,21],[58,21],[78,8],[76,37],[62,48],[63,73],[78,86],[43,87],[26,73],[30,48],[12,55],[7,70],[17,85],[43,87]],
    paths: [[0,1,2,3,4,5,6,11,0],[6,7,8,9,10,11],[10,12,13,14,15]] },
  { name: 'hotel', floor: 150, x: 85, y: 53,
    points: [[13,54],[50,30],[87,54],[22,54],[22,88],[78,88],[78,54],[43,88],[43,69],[50,63],[57,69],[57,88],[34,20],[29,6],[44,13],[50,1],[56,13],[71,6],[66,20]],
    paths: [[0,1,2],[3,4,5,6],[7,8,9,10,11],[12,13,14,15,16,17,18,12]] },
];

export function mountScenery(parent, motion) {
  const paper = document.createElement('div'); paper.className = 'sky-paper';
  paper.style.backgroundImage = `url("${ART['sky-paper']}")`; parent.append(paper);
  const animations = [];
  const entrances = new Set(), celestial = [];
  let height = -1;
  for (const [kind, pieces] of [['island', ISLANDS], ['cloud', CLOUDS], ['sea', SEA]]) {
    for (const [frame, x, y, size, period, phase] of pieces) {
      const anchor = document.createElement('div');
      anchor.className = `sky-piece sky-${kind}`;
      anchor.style.cssText = `left:${x}%;top:${y}%;width:clamp(68px,${size}vmin,${kind === 'island' ? 260 : kind === 'sea' ? 620 : 350}px)`;
      const sprite = document.createElement('div'); sprite.className = 'sky-sprite';
      const [sx, sy, width, height] = SCENERY.frames[frame];
      anchor.style.aspectRatio = `${width} / ${height}`;
      sprite.style.backgroundImage = `url("${ART.scenery}")`;
      sprite.style.backgroundSize = `${SCENERY.width / width * 100}% ${SCENERY.height / height * 100}%`;
      sprite.style.backgroundPosition = `${sx / (SCENERY.width - width) * 100}% ${sy / (SCENERY.height - height) * 100}%`;
      anchor.append(sprite); parent.append(anchor);
      // Clouds travel farther; islands bob on independent, slower swells.
      const poses = kind !== 'island'
        ? ['translate3d(-22%, 1%, 0)', 'translate3d(22%, -2%, 0)', 'translate3d(-22%, 1%, 0)']
        : ['translate3d(-2%, -4%, 0) rotate(-1deg)', 'translate3d(2%, 4%, 0) rotate(1deg)', 'translate3d(-2%, -4%, 0) rotate(-1deg)'];
      const animation = sprite.animate(poses.map(transform => ({ transform })), { duration: period * 1000, iterations: Infinity, easing: 'ease-in-out' });
      animation.pause(); animation.currentTime = phase * period * 1000;
      animations.push(animation);
    }
  }
  function ornament(className, frame, x, y, size) {
    const anchor = document.createElement('div'); anchor.className = `sky-celestial ${className}`;
    anchor.style.cssText = `--x:${x}%;--y:${y}%;${size ? `--size:${size}px;` : ''}`;
    const sprite = document.createElement('div'); sprite.className = 'sky-ornament';
    const [sx, sy, width, height] = CELESTIAL[frame];
    anchor.style.aspectRatio = `${width} / ${height}`;
    sprite.style.backgroundImage = `url("${ART.celestial}")`;
    sprite.style.backgroundSize = `${1254 / width * 100}% ${1254 / height * 100}%`;
    sprite.style.backgroundPosition = `${sx / (1254 - width) * 100}% ${sy / (1254 - height) * 100}%`;
    anchor.append(sprite); parent.append(anchor); return anchor;
  }
  STARS.forEach(([x, y, size, floor], i) => {
    const element = ornament('sky-star', floor >= 75 ? 1 : 0, x, y, size);
    element.style.setProperty('--phase', `${-i * 1.73}s`);
    celestial.push({ element, floor });
  });
  celestial.push({ element: ornament('sky-moon', 2, 84, 29), floor: 100 });
  ornament('sky-ribbon sky-ribbon-left', 3, -3, 42);
  ornament('sky-ribbon sky-ribbon-right', 3, 98, 63);
  for (const { name, floor, x, y, points, paths } of CONSTELLATIONS) {
    const element = document.createElement('div'); element.className = `sky-celestial sky-constellation sky-constellation-${name}`;
    element.style.cssText = `--x:${x}%;--y:${y}%;`;
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('viewBox', '0 0 100 100');
    for (const route of paths) {
      const path = document.createElementNS(svg.namespaceURI, 'path');
      path.setAttribute('d', route.map((index, i) => `${i ? 'L' : 'M'}${points[index].join(' ')}`).join(' ')); path.setAttribute('pathLength', '1'); svg.append(path);
    }
    for (const [px, py] of points) {
      const star = document.createElementNS(svg.namespaceURI, 'polygon');
      star.setAttribute('points', `${px},${py - 2} ${px + .6},${py - .6} ${px + 2},${py} ${px + .6},${py + .6} ${px},${py + 2} ${px - .6},${py + .6} ${px - 2},${py} ${px - .6},${py - .6}`); svg.append(star);
    }
    element.append(svg); parent.append(element); celestial.push({ element, floor, until: name === 'cat' ? 150 : Infinity });
  }
  function settleEntrances() { for (const animation of entrances) animation.cancel(); entrances.clear(); }
  function setHeight(value, { immediate = false } = {}) {
    const sky = skyAtHeight(value);
    if (sky.height === height && !immediate) return;
    const reset = immediate || sky.height < height;
    if (reset) { settleEntrances(); parent.dataset.immediate = 'true'; }
    parent.style.backgroundColor = sky.color;
    for (const [key, val] of Object.entries({
      'island-opacity': sky.islandOpacity, 'island-drop': `${sky.islandDrop}vh`, 'island-scale': sky.islandScale,
      'cloud-drop': `${sky.cloudDrop}vh`, 'cloud-opacity': sky.cloudOpacity, 'sea-opacity': sky.seaOpacity,
      'cloud-filter': `sepia(${sky.night * .3}) saturate(${1 + sky.night * 1.4}) hue-rotate(${sky.night * 165}deg) brightness(${1 - sky.night * .38})`,
      'ribbon-opacity': sky.ribbonOpacity,
    })) parent.style.setProperty(`--${key}`, val);
    for (const { element, floor, until = Infinity } of celestial) {
      const visible = sky.height >= floor && sky.height < until;
      if (visible && element.dataset.visible !== 'true' && motion && !reset && !document.hidden) {
        const target = element.firstElementChild;
        const animation = target.animate([
          { transform: 'perspective(500px) rotateY(-78deg) rotate(-9deg) scale(.55)', opacity: 0 },
          { transform: 'perspective(500px) rotateY(7deg) rotate(2deg) scale(1.025)', opacity: 1, offset: .72 },
          { transform: 'perspective(500px) rotateY(0) rotate(0) scale(1)', opacity: 1 },
        ], { duration: element.classList.contains('sky-moon') ? 2800 : 2100, easing: 'cubic-bezier(.22,.65,.25,1)' });
        entrances.add(animation); animation.onfinish = () => entrances.delete(animation);
      }
      element.dataset.visible = String(visible);
    }
    height = sky.height; parent.dataset.height = String(height); parent.dataset.stage = sky.stage.name;
    if (reset) { parent.getBoundingClientRect(); delete parent.dataset.immediate; }
  }
  function sync() {
    const playing = motion && !document.hidden;
    for (const animation of animations) playing ? animation.play() : animation.pause();
    for (const animation of entrances) playing ? animation.play() : animation.pause();
    parent.dataset.motion = String(playing);
  }
  document.addEventListener('visibilitychange', sync); sync(); setHeight(0, { immediate: true });
  return {
    setHeight,
    setMotion(value) { motion = value; if (!motion) settleEntrances(); sync(); },
    destroy() { document.removeEventListener('visibilitychange', sync); settleEntrances(); animations.forEach(animation => animation.cancel()); parent.replaceChildren(); },
  };
}
