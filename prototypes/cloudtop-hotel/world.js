import Phaser from 'phaser';
import { ART } from './assets.js';
import { segments, longestSegment } from './engine.js';

const TYPES = ['bunny', 'frog', 'cat'];
const INK = '#435c50';
const ease = n => 1 - (1 - Phaser.Math.Clamp(n, 0, 1)) ** 3;

// The scene only presents committed state. No gameplay decision depends on a sprite or timer.
class HotelScene extends Phaser.Scene {
  constructor(onReady) { super('hotel'); this.onReady = onReady; this.view = null; this.motion = !matchMedia('(prefers-reduced-motion: reduce)').matches; }
  preload() { for (const [key, url] of Object.entries(ART)) this.load.svg(key, url); }
  create() {
    this.background = this.add.container(); this.tower = this.add.container(); this.effects = this.add.container();
    this.lastDraw = -Infinity; this.whole = false; this.cameraBase = null; this.scale.on('resize', () => { this.cameraBase = null; this.tower.y = 0; this.draw(); });
    this.onReady(this);
  }
  setState(state) {
    const wasDone = this.view?.phase === 'complete';
    this.animation = null; this.view = structuredClone(state);
    this.ending = state.phase === 'complete' && !wasDone && this.motion ? this.time.now : null;
    if (state.phase === 'complete' && !wasDone) this.whole = true;
    if (state.phase !== 'complete') this.ending = null;
    this.draw();
  }
  reset(state) { this.cameraBase = null; this.tower.y = 0; this.whole = false; this.preview = null; this.ending = null; this.view = null; this.setState(state); }
  inspect(offer) { this.preview = offer; this.draw(); }
  toggleOverview() { this.whole = !this.whole; this.draw(); return this.whole; }
  animate(before, after, { onFrame, onComplete }) {
    this.preview = null;
    this.animation = { before, after, start: this.time.now, onFrame, onComplete, delay: after.history.at(-1).type === 'mystery' ? 580 : 130, duration: after.lastEffect.added ? 1550 : 650 };
    this.draw();
  }
  skip() {
    const animation = this.animation;
    if (!animation) return;
    this.animation = null; this.view = animation.after; animation.onComplete();
  }
  update(time, delta) {
    if (!this.view) return;
    this.tower.y *= Math.exp(-delta / 85);
    if (time - this.lastDraw < 1000 / 12) return;
    this.lastDraw = time;
    if (this.animation) {
      const a = this.animation, elapsed = time - a.start;
      if (elapsed >= a.delay + a.duration) { this.skip(); return; }
      this.draw();
    } else if (this.motion) this.draw();
  }
  image(layer, key, x, y, width, height, angle = 0, alpha = 1) {
    const image = this.add.image(x, y, key).setDisplaySize(width, height).setAngle(angle).setAlpha(alpha);
    layer.add(image); return image;
  }
  label(layer, text, x, y, size = 12, color = INK) {
    const label = this.add.text(x, y, text, { fontFamily: 'Georgia, serif', fontSize: `${size}px`, color, align: 'center', lineSpacing: 3 }).setOrigin(.5);
    layer.add(label); return label;
  }
  graphics(layer) { const g = this.add.graphics(); layer.add(g); return g; }
  layout(count) {
    const { width: w, height: h } = this.scale;
    const floorWidth = Math.min(196, Math.max(130, w * .4)), floorHeight = floorWidth * .31;
    const available = Math.max(50, h - 75);
    const overviewScale = Math.min(1, available / Math.max(floorHeight * count + 60, 1));
    const finished = this.view?.phase === 'complete';
    const ending = this.ending === null ? 1 : ease((this.time.now - this.ending) / 1600);
    const scale = this.whole ? (finished ? 1 + (overviewScale - 1) * ending : overviewScale) : 1;
    const width = floorWidth * scale, step = floorHeight * scale;
    const base = Math.max(h - 48, h * .2 + count * step);
    // Keep construction near the middle until enough floors exist to follow the open top.
    return { x: w / 2, base: this.whole ? h - 42 : base, width, step, scale, floorWidth };
  }
  draw() {
    if (!this.tower || !this.view) return;
    const { width: w, height: h } = this.scale;
    this.background.removeAll(true); this.tower.removeAll(true); this.effects.removeAll(true);
    this.drawSky(w, h);
    let state = this.view, current = state.links.length, progress = 1;
    const a = this.animation;
    if (a) {
      progress = Phaser.Math.Clamp((this.time.now - a.start - a.delay) / a.duration, 0, 1);
      const count = a.after.lastEffect.added;
      const delivered = progress < .18 ? 0 : Math.min(count, Math.floor((progress - .18) / .66 * count));
      current = a.before.links.length + delivered; state = a.after;
      a.onFrame(current);
    }
    const layout = this.layout(current), { x, base, width, step, scale } = layout;
    if (a && this.motion && this.cameraBase !== null) this.tower.y += this.cameraBase - base;
    this.cameraBase = base;
    const top = base - current * step;
    if (base < h + 100) this.image(this.tower, 'island', x, base + 43 * scale, width * 1.65, width * .8);
    const first = Math.max(0, Math.floor((base - h - step) / step));
    const visible = [];
    const source = (this.preview?.type === 'overgrow' || a?.after.history.at(-1).type === 'overgrow') ? longestSegment(a?.before ?? state) : null;
    for (let i = first; i < current; i++) {
      const floor = state.links[i]; if (!floor) continue;
      const y = base - (i + .5) * step;
      if (y < -step) continue;
      visible.push(floor.id);
      const building = this.image(this.tower, `floor-${floor.suit}-${(floor.id * 7 + floor.source) % 4}`, x, y, width, step);
      building.setData('floorId', floor.id).setData('floorType', floor.suit);
      if (width > 65) for (let guest = 0; guest < 3; guest++) {
        const active = this.motion && (floor.id + guest) % 9 === Math.floor(this.time.now / 1800) % 9;
        const pose = active ? Math.floor(this.time.now / 250) % 2 : (floor.id + guest * 2) % 5;
        this.image(this.tower, `resident-${floor.suit}-${pose}`, x + width * (guest - 1) * .265, y - step * .03, width * .126, width * .126);
      }
      const matched = this.preview?.type === 'recall' && this.preview.suit === floor.suit;
      if (matched || (source && i >= source.start && i < source.end)) {
        const g = this.graphics(this.tower); g.lineStyle(2, source ? 0x9f8abc : 0xf6f0c5, .9); g.strokeRoundedRect(x - width / 2 - 3, y - step / 2, width + 6, step, 3);
      }
    }
    const done = this.view.phase === 'complete';
    if (done) {
      const drop = this.ending === null ? 1 : ease((this.time.now - this.ending) / 650);
      this.image(this.tower, 'roof', x, top - width * .135 - (1 - drop) * 60, width * 1.08, width * .36, 0, drop);
      this.label(this.tower, 'CLOUDTOP HOTEL', x, Math.min(h - 16, base + 19), Math.max(9, 13 * scale));
      const g = this.graphics(this.effects);
      if (this.ending !== null && this.time.now - this.ending < 2100) for (let i = 0; i < 20; i++) {
        const t = (this.time.now - this.ending) / 2100;
        g.fillStyle([0xe1b475, 0xc693ae, 0x8aaa89][i % 3], 1 - t);
        g.fillRect(x + Math.sin(i * 13) * w * .35 * t, top + t * h * .6 + Math.cos(i * 7) * 40, 4, 8);
      }
    } else {
      this.image(this.tower, 'platform', x, top, width * 1.05, width * .115);
      if (!current && !a) {
        this.label(this.tower, 'A little paper.\nA lot of possibility.', x, Math.max(35, top - 112), w < 420 ? 19 : 27);
        this.label(this.tower, 'Choose a card to welcome your first guest', x, top - 47, w < 420 ? 10 : 12, '#728478');
      }
    }
    if (a && progress >= .18 && progress < .84 && current < a.after.links.length) {
      const fraction = ((progress - .18) / .66 * a.after.lastEffect.added) % 1;
      const next = a.after.links[current], pose = Math.min(2, Math.floor(fraction * 3));
      this.image(this.tower, `unfold-${next.suit}-${pose}`, x, top - step / 2, width, step);
    }
    if (a) this.drawDelivery(a, progress, layout, current);
    else if (this.preview?.type === 'overgrow' && source) this.drawCopycat(layout, source, 0);
    this.game.canvas.dataset.visibleFloors = JSON.stringify(visible);
    this.game.canvas.dataset.floorCount = String(current);
    this.game.canvas.dataset.roof = String(done);
    this.game.canvas.dataset.phase = a ? 'resolving' : this.view.phase;
  }
  drawSky(w, h) {
    const g = this.graphics(this.background);
    // Folded sun, paper rays and soft horizon lines.
    const sunX = w * .79, sunY = h * .2, radius = Math.min(36, h * .12);
    g.fillStyle(0xefce88, .6); g.fillCircle(sunX, sunY, radius);
    g.fillStyle(0xf3d995, .9); g.fillTriangle(sunX, sunY - radius, sunX + radius, sunY, sunX, sunY + radius);
    g.lineStyle(1, 0xacbcac, .18);
    for (let i = 0; i < 4; i++) g.lineBetween(w * .05, h * (.3 + i * .17), w * .9, h * (.27 + i * .17));
    const drift = this.motion ? Math.sin(this.time.now / 16000) * 12 : 0;
    this.image(this.background, 'cloud', w * .12 + drift, h * .25, Math.min(w * .28, 170), 72, -4, .8);
    this.image(this.background, 'cloud', w * .87 - drift, h * .64, Math.min(w * .32, 210), 87, 4, .65);
    this.image(this.background, 'cloud', w * .1 - drift / 2, h * .91, 130, 60, 0, .6);
    this.image(this.background, 'balloon-bunny', w * .17, h * .56 + drift / 2, 21, 30, -6, .42);
    this.image(this.background, 'balloon-cat', w * .88, h * .12 + drift / 2, 16, 23, 8, .35);
  }
  drawCopycat(layout, source, progress) {
    const x = Math.max(43, layout.x - layout.width * .88), y = Math.max(60, this.scale.height * .58);
    this.image(this.effects, 'cloud', x, y + 30, 99, 44);
    this.image(this.effects, 'copycat', x, y - 15, 66, 73, progress > .3 && progress < .5 ? -7 : 0);
    this.label(this.effects, `Copycat\n${source.suit[0].toUpperCase() + source.suit.slice(1)} ×${source.length}`, x, y + 57, 10);
    return { x, y };
  }
  drawDelivery(a, progress, layout, current) {
    const card = a.after.history.at(-1), { x, base, step, width } = layout;
    const count = a.after.lastEffect.added, top = base - current * step;
    let originX = x + width * .8, originY = this.scale.height * .85;
    if (card.type === 'overgrow') {
      const actor = this.drawCopycat(layout, longestSegment(a.before), progress); originX = actor.x; originY = actor.y;
    }
    if (!count) {
      this.image(this.effects, 'charm', x, Math.max(35, top - 65 - progress * 20), 54, 54, (1 - progress) * -15, Math.min(1, (1 - progress) * 3));
      return;
    }
    if (this.time.now - a.start < a.delay && card.type === 'mystery') {
      this.image(this.effects, 'parcel', x, Math.max(40, top - 65), 64, 64, Math.sin(this.time.now / 65) * 5); return;
    }
    if (progress < .85) {
      const suit = a.after.links[Math.min(a.after.links.length - 1, current)]?.suit ?? 'bunny';
      const t = Math.min(1, progress / .55);
      const sourceX = card.type === 'recall' ? this.scale.width * (.25 + TYPES.indexOf(suit) * .25) : originX;
      const sourceY = card.type === 'recall' ? -20 : originY;
      const boxX = Phaser.Math.Linear(sourceX, x, t), boxY = Phaser.Math.Linear(sourceY, top - 27, t) - Math.sin(t * Math.PI) * 50;
      this.image(this.effects, `box-${suit}`, boxX, boxY, 38, 38, (1 - t) * -16, 1 - Math.max(0, (progress - .7) * 6));
      if (card.type === 'recall') {
        const fleet = Math.min(3, segments(a.before, card.suit).length);
        for (let i = 0; i < fleet; i++) this.image(this.effects, `balloon-${suit}`, boxX + (i - (fleet - 1) / 2) * 22, boxY - 43 - (i % 2) * 10, 33, 48);
      }
      const ordinary = count - (card.foundationBonus ?? 0);
      if (ordinary > 1) this.label(this.effects, `×${ordinary}`, boxX + 30, boxY, 15);
      if (card.foundationBonus && progress > .35) this.label(this.effects, `Streak +${card.foundationBonus}`, x, Math.max(30, top - 70), 12, '#927ba1');
    }
    if (progress > .77) {
      const newRuns = segments(a.after).filter(run => run.id >= a.before.nextLinkId);
      const t = (progress - .77) / .23;
      for (const [i, run] of newRuns.slice(0, 5).entries()) {
        const dockX = this.scale.width * (.25 + TYPES.indexOf(run.suit) * .25);
        this.image(this.effects, `balloon-${run.suit}`, Phaser.Math.Linear(x, dockX, t) + Math.sin(t * Math.PI) * (i - 2) * 16, Phaser.Math.Linear(Math.max(top - 20, 50), -25, t), 27, 39, (1 - t) * 8);
      }
    }
  }
}

export function mountWorld(parent) {
  let scene;
  const ready = new Promise(resolve => {
    scene = new HotelScene(resolve);
  });
  const game = new Phaser.Game({ type: Phaser.CANVAS, parent, width: parent.clientWidth, height: parent.clientHeight, transparent: true, banner: false, audio: { noAudio: true }, scene, render: { antialias: true, roundPixels: false }, scale: { mode: Phaser.Scale.NONE } });
  const resize = new ResizeObserver(() => { if (parent.clientWidth && parent.clientHeight) game.scale.resize(parent.clientWidth, parent.clientHeight); });
  resize.observe(parent);
  game.canvas.setAttribute('aria-label', 'Paper hotel and arriving guests'); game.canvas.setAttribute('role', 'img');
  return { ready, destroy: () => { resize.disconnect(); game.destroy(true); } };
}
