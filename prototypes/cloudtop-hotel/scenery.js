import { ART, SCENERY } from './assets.js';

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

export function mountScenery(parent, motion) {
  parent.style.backgroundImage = `url("${ART['sky-paper']}")`;
  const animations = [];
  for (const [kind, pieces] of [['island', ISLANDS], ['cloud', CLOUDS]]) {
    for (const [frame, x, y, size, period, phase] of pieces) {
      const anchor = document.createElement('div');
      anchor.className = `sky-piece sky-${kind}`;
      anchor.style.cssText = `left:${x}%;top:${y}%;width:clamp(68px,${size}vmin,${kind === 'island' ? 260 : 350}px)`;
      const sprite = document.createElement('div'); sprite.className = 'sky-sprite';
      const [sx, sy, width, height] = SCENERY.frames[frame];
      anchor.style.aspectRatio = `${width} / ${height}`;
      sprite.style.backgroundImage = `url("${ART.scenery}")`;
      sprite.style.backgroundSize = `${SCENERY.width / width * 100}% ${SCENERY.height / height * 100}%`;
      sprite.style.backgroundPosition = `${sx / (SCENERY.width - width) * 100}% ${sy / (SCENERY.height - height) * 100}%`;
      anchor.append(sprite); parent.append(anchor);
      // Clouds travel farther; islands bob on independent, slower swells.
      const poses = kind === 'cloud'
        ? ['translate3d(-22%, 1%, 0)', 'translate3d(22%, -2%, 0)', 'translate3d(-22%, 1%, 0)']
        : ['translate3d(-2%, -4%, 0) rotate(-1deg)', 'translate3d(2%, 4%, 0) rotate(1deg)', 'translate3d(-2%, -4%, 0) rotate(-1deg)'];
      const animation = sprite.animate(poses.map(transform => ({ transform })), { duration: period * 1000, iterations: Infinity, easing: 'ease-in-out' });
      animation.pause(); animation.currentTime = phase * period * 1000;
      animations.push(animation);
    }
  }
  function sync() {
    const playing = motion && !document.hidden;
    for (const animation of animations) playing ? animation.play() : animation.pause();
    parent.dataset.motion = String(playing);
  }
  document.addEventListener('visibilitychange', sync); sync();
  return {
    setMotion(value) { motion = value; sync(); },
    destroy() { document.removeEventListener('visibilitychange', sync); animations.forEach(animation => animation.cancel()); parent.replaceChildren(); },
  };
}
