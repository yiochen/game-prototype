import Phaser from 'phaser';
import { ART, SHEETS, spriteArt, registerFrames } from './assets.js';
import { segments, longestSegment } from './engine.js';

const TYPES = ['bunny', 'frog', 'cat'];
const INK = '#fff8dd';
const ease = n => 1 - (1 - Phaser.Math.Clamp(n, 0, 1)) ** 3;

// The scene only presents committed state. No gameplay decision depends on a sprite or timer.
class HotelScene extends Phaser.Scene {
  constructor(onReady) { super('hotel'); this.onReady = onReady; this.view = null; this.motion = !matchMedia('(prefers-reduced-motion: reduce)').matches; }
  preload() { for (const key of Object.keys(SHEETS)) this.load.image(key, ART[key]); }
  create() {
    registerFrames(this);
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
    const type = after.history.at(-1).type, count = after.lastEffect.added;
    this.animation = { before, after, start: this.time.now, onFrame, onComplete, delay: type === 'mystery' ? 700 : 100, duration: type === 'overgrow' ? 3200 : count ? Math.min(2900, 1300 + count * 140) : 900, buildStart: type === 'overgrow' ? .47 : .25, buildEnd: .87 };
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
    const { sheet, frame } = spriteArt(key);
    const image = this.add.image(x, y, sheet, frame).setDisplaySize(width, height).setAngle(angle).setAlpha(alpha);
    layer.add(image); return image;
  }
  sprite(layer, sheet, frame, x, y, width, height = width, angle = 0, alpha = 1) {
    const image = this.add.image(x, y, sheet, frame).setDisplaySize(width, height).setAngle(angle).setAlpha(alpha);
    layer.add(image); this.frameLog.push(`${sheet}:${frame}`); return image;
  }
  balloon(layer, type, x, y, size, offset = 0, alpha = 1) {
    const pose = this.motion ? Math.floor(this.time.now / 340 + offset) % 4 : 0;
    return this.sprite(layer, 'actors', (TYPES.indexOf(type) + 1) * 4 + pose, x, y, size, size, 0, alpha);
  }
  label(layer, text, x, y, size = 12, color = INK) {
    const label = this.add.text(x, y, text, { fontFamily: 'Trebuchet MS, sans-serif', fontStyle: 'bold', fontSize: `${size}px`, color, align: 'center', lineSpacing: 4, shadow: { color: '#154f76', blur: 3, offsetY: 2, fill: true } }).setOrigin(.5);
    layer.add(label); return label;
  }
  graphics(layer) { const g = this.add.graphics(); layer.add(g); return g; }
  screenRegion() {
    const { width: w, height: h } = this.scale, canvas = this.game.canvas.getBoundingClientRect();
    const rect = selector => {
      const element = document.querySelector(selector);
      if (!element?.getClientRects().length) return null;
      const bounds = element.getBoundingClientRect(), sx = w / canvas.width, sy = h / canvas.height;
      return { left: (bounds.left - canvas.left) * sx, right: (bounds.right - canvas.left) * sx, top: (bounds.top - canvas.top) * sy, bottom: (bounds.bottom - canvas.top) * sy, height: bounds.height * sy };
    };
    const dashboard = rect('.dashboard'), strategy = rect('#strategy-status');
    const foreground = rect('#tray') ?? rect('#ending');
    const top = Math.max(8, dashboard?.bottom ?? 0, strategy?.bottom ?? 0) + 10;
    const sideTray = foreground && w > h && foreground.left > w * .25;
    const right = sideTray ? foreground.left - 10 : w - 12;
    const bottom = sideTray ? h - 12 : Math.min(h - 12, foreground?.top ?? h) - 4;
    return { left: 12, right, top, bottom, width: Math.max(80, right - 12), height: Math.max(70, bottom - top), sideTray };
  }
  dockPosition(suit) {
    const canvas = this.game.canvas.getBoundingClientRect(), chip = document.querySelector(`.dock-chip.${suit}`)?.getBoundingClientRect();
    return chip ? { x: (chip.left + chip.width / 2 - canvas.left) * this.scale.width / canvas.width, y: (chip.top + chip.height / 2 - canvas.top) * this.scale.height / canvas.height } : { x: this.scale.width * (.25 + TYPES.indexOf(suit) * .25), y: 20 };
  }
  layout(count) {
    const region = this.screenRegion();
    const floorWidth = Math.min(330, region.width * .61, Math.max(100, region.height * .76)), floorHeight = floorWidth / 3;
    const finished = this.view?.phase === 'complete';
    // The island extends .48 widths below the first floor; the finished roof
    // extends .65 above the last. Include both in the whole-hotel camera fit.
    const cap = finished ? .65 : .23;
    const overviewScale = Math.min(1, region.height / Math.max(floorHeight * count + floorWidth * (cap + .5), 1));
    const ending = this.ending === null ? 1 : ease((this.time.now - this.ending) / 1600);
    const scale = this.whole ? (finished ? 1 + (overviewScale - 1) * ending : overviewScale) : 1;
    const width = floorWidth * scale, step = floorHeight * scale;
    const headroom = finished ? width * .68 + 10 : Math.max(region.height * .2, width * .23 + 25);
    const base = this.whole ? region.bottom - width * .5 : Math.max(region.bottom - width * .12, region.top + headroom + count * step);
    // The canvas continues behind the foreground tray. Close-up floors may
    // pass under it naturally; only the camera's focus uses the clear region.
    return { x: (region.left + region.right) / 2, base, width, step, scale, floorWidth, region };
  }
  draw() {
    if (!this.tower || !this.view) return;
    this.frameLog = [];
    const { width: w, height: h } = this.scale;
    this.background.removeAll(true); this.tower.removeAll(true); this.effects.removeAll(true);
    this.drawSky(w, h);
    let state = this.view, current = state.links.length, progress = 1;
    const a = this.animation;
    if (a) {
      progress = Phaser.Math.Clamp((this.time.now - a.start - a.delay) / a.duration, 0, 1);
      const count = a.after.lastEffect.added;
      const delivered = progress < a.buildStart ? 0 : Math.min(count, Math.floor((progress - a.buildStart) / (a.buildEnd - a.buildStart) * count));
      current = a.before.links.length + delivered; state = a.after;
      a.onFrame(current);
    }
    const layout = this.layout(current), { x, base, width, step, scale } = layout;
    if (a && this.motion && this.cameraBase !== null) this.tower.y += this.cameraBase - base;
    this.cameraBase = base;
    const top = base - current * step;
    if (base < h + 100) this.image(this.tower, 'island', x, base + width * .13, width * 1.4, width * .7);
    const first = Math.max(0, Math.floor((base - h - step) / step));
    const visible = [];
    const source = (this.preview?.type === 'overgrow' || a?.after.history.at(-1).type === 'overgrow') ? longestSegment(a?.before ?? state) : null;
    for (let i = first; i < current; i++) {
      const floor = state.links[i]; if (!floor) continue;
      const y = base - (i + .5) * step;
      if (y < -step) continue;
      visible.push(floor.id);
      const wall = this.graphics(this.tower); wall.fillStyle({ bunny: 0xc66f83, frog: 0x879b4c, cat: 0xd88a3c }[floor.suit]); wall.fillRect(x - width / 2, y - step / 2, width, step);
      for (let guest = 0; guest < 3; guest++) {
        const cycle = (this.time.now + floor.id * 617 + guest * 1331) % 7200;
        const rest = [3, 5, 7][(floor.id + guest) % 3];
        const pose = this.motion && width > 70 ? cycle < 190 ? 4 : cycle > 4000 && cycle < 4850 ? 6 : rest : rest;
        const building = this.sprite(this.tower, `rooms-${floor.suit}`, pose, x + (guest - 1) * width / 3, y, width / 3 + .6, step + .5);
        building.setData('floorId', floor.id).setData('floorType', floor.suit);
      }
      const matched = this.preview?.type === 'recall' && this.preview.suit === floor.suit;
      if (matched || (source && i >= source.start && i < source.end)) {
        const g = this.graphics(this.tower); g.lineStyle(2, source ? 0x9f8abc : 0xf6f0c5, .9); g.strokeRoundedRect(x - width / 2 - 3, y - step / 2, width + 6, step, 3);
      }
    }
    const done = this.view.phase === 'complete';
    if (done) {
      const drop = this.ending === null ? 1 : ease((this.time.now - this.ending) / 650);
      this.image(this.tower, 'roof', x, top - width * .31 - (1 - drop) * 60, width * 1.08, width * .67, 0, drop);
      const g = this.graphics(this.effects);
      if (this.ending !== null && this.time.now - this.ending < 2100) for (let i = 0; i < 20; i++) {
        const t = (this.time.now - this.ending) / 2100;
        g.fillStyle([0xffd153, 0xff7aac, 0xa8d55d, 0xa48bea][i % 4], 1 - t);
        g.fillRect(x + Math.sin(i * 13) * w * .35 * t, top + t * h * .6 + Math.cos(i * 7) * 40, 4, 8);
      }
    } else {
      this.image(this.tower, 'platform', x, top - width * .1, width * 1.05, width * .23);
    }
    if (a && progress >= a.buildStart && progress < a.buildEnd && current < a.after.links.length) {
      const fraction = ((progress - a.buildStart) / (a.buildEnd - a.buildStart) * a.after.lastEffect.added) % 1;
      const next = a.after.links[current], pose = Math.min(3, Math.floor(fraction * 4));
      for (let guest = 0; guest < 3; guest++) this.sprite(this.tower, `rooms-${next.suit}`, pose, x + (guest - 1) * width / 3, top - step / 2 - (1 - ease(fraction)) * 14, width / 3, step);
    }
    if (a) this.drawDelivery(a, progress, layout, current);
    else if (this.preview?.type === 'overgrow' && source) this.drawCopycat(layout, source, 0);
    this.game.canvas.dataset.visibleFloors = JSON.stringify(visible);
    this.game.canvas.dataset.floorCount = String(current);
    this.game.canvas.dataset.roof = String(done);
    this.game.canvas.dataset.phase = a ? 'resolving' : this.view.phase;
    this.game.canvas.dataset.spriteFrames = this.frameLog.join(',');
    this.game.canvas.dataset.action = a ? a.after.history.at(-1).type : 'idle';
    this.game.canvas.dataset.choreography = !a ? 'idle' : progress < .18 ? 'spot' : progress < .34 ? 'stamp' : progress < a.buildStart ? 'send' : progress < a.buildEnd ? 'unfold' : 'celebrate';
    this.game.canvas.dataset.motion = String(this.motion);
    this.game.canvas.dataset.viewRegion = JSON.stringify(layout.region);
    this.game.canvas.dataset.towerBounds = JSON.stringify({ left: x - width * .7, right: x + width * .7, top: top - width * (done ? .65 : .23), bottom: base + width * .48, overview: this.whole });
  }
  drawSky(w, h) {
    const drift = this.motion ? Math.sin(this.time.now / 18000) * 8 : 0;
    this.balloon(this.background, 'bunny', w * .12, h * .36 + drift, 35, 1, .85);
    this.balloon(this.background, 'frog', w * .89, h * .14 - drift / 2, 27, 2, .8);
    this.balloon(this.background, 'cat', w * .9, h * .8 + drift / 2, 41, 3, .85);
  }
  drawCopycat(layout, source, progress) {
    const { region } = layout;
    const size = Math.min(115, region.width * .2, region.height * .35), x = Math.max(region.left + size / 2, layout.x - layout.width * .76);
    const y = region.top + region.height * .5;
    const pose = progress < .18 ? 0 : progress < .34 ? 1 : progress < .87 ? 2 : 3;
    this.image(this.effects, 'cloud', x, y + size * .43, size * 1.4, size * .55);
    this.sprite(this.effects, 'actors', pose, x, y, size, size, pose === 1 ? Math.sin(progress * 80) * 3 : 0);
    this.label(this.effects, ['SPOT', 'STAMP', 'SEND', 'HOORAY!'][pose], x, y - size * .6, 11);
    this.label(this.effects, source.suit[0].toUpperCase() + source.suit.slice(1) + ' ×' + source.length, x, y + size * .8, 10);
    if (pose === 1) {
      this.sprite(this.effects, 'rooms-' + source.suit, 0, x + size * .4, y + size * .3, size * .45);
      const g = this.graphics(this.effects); g.lineStyle(2, 0xffe681, .9);
      for (let i = 0; i < 5; i++) { const angle = i / 5 * Math.PI * 2; g.lineBetween(x + Math.cos(angle) * size * .55, y + Math.sin(angle) * size * .5, x + Math.cos(angle) * size * .65, y + Math.sin(angle) * size * .6); }
    }
    return { x, y };
  }
  drawDelivery(a, progress, layout, current) {
    const card = a.after.history.at(-1), { x, base, step, width, region } = layout;
    const count = a.after.lastEffect.added, top = base - current * step;
    let originX = Math.min(region.right - 32, x + width * .72), originY = region.bottom - 10;
    if (card.type === 'overgrow') {
      const actor = this.drawCopycat(layout, longestSegment(a.before), progress); originX = actor.x; originY = actor.y;
    }
    if (!count) {
      this.image(this.effects, 'charm', x, Math.max(region.top + 40, top - 90 - progress * 30), 70, 67, Math.sin(progress * Math.PI * 5) * (1 - progress) * 14, Math.min(1, (1 - progress) * 4));
      return;
    }
    if (this.time.now - a.start < a.delay && card.type === 'mystery') {
      this.image(this.effects, 'parcel', x, Math.max(region.top + 45, top - 80), 82, 78, Math.sin(this.time.now / 65) * 6); return;
    }
    const suit = a.after.links[Math.min(a.after.links.length - 1, current)]?.suit ?? 'bunny';
    const flightStart = card.type === 'overgrow' ? .32 : 0;
    if (progress >= flightStart && progress < a.buildEnd) {
      const t = Phaser.Math.Clamp((progress - flightStart) / (a.buildStart - flightStart + .1), 0, 1);
      const dock = this.dockPosition(suit);
      const sourceX = card.type === 'recall' ? dock.x : originX;
      const sourceY = card.type === 'recall' ? dock.y : originY;
      const boxX = Phaser.Math.Linear(sourceX, x, t), boxY = Phaser.Math.Linear(sourceY, top - 42, t) - Math.sin(t * Math.PI) * 65;
      const alpha = 1 - Phaser.Math.Clamp((progress - a.buildStart) / .3, 0, 1);
      this.sprite(this.effects, 'rooms-' + suit, 0, boxX, boxY, 65, 65, (1 - t) * -18, alpha);
      if (card.type === 'recall') {
        const fleet = Math.min(4, segments(a.before, card.suit).length);
        for (let i = 0; i < fleet; i++) this.balloon(this.effects, suit, boxX + (i - (fleet - 1) / 2) * 34, boxY - 49 - i % 2 * 12, 62, i, Math.max(.2, alpha));
      }
      if (count > 1 && alpha > .1) this.label(this.effects, '×' + count, boxX + 36, boxY - 12, 19);
    }
    if (progress > a.buildEnd) {
      const t = (progress - a.buildEnd) / (1 - a.buildEnd);
      const newRuns = segments(a.after).filter(run => run.id >= a.before.nextLinkId);
      for (const [i, run] of newRuns.slice(0, 5).entries()) {
        const dock = this.dockPosition(run.suit);
        this.balloon(this.effects, run.suit, Phaser.Math.Linear(x, dock.x, t) + Math.sin(t * Math.PI) * (i - 2) * 23, Phaser.Math.Linear(Math.max(top - 20, region.top + 25), dock.y, t), 48, i);
      }
      this.label(this.effects, '+' + count + ' floors', x, Math.max(region.top + 15, top - 30 - t * 25), 24, '#fff0a2');
      const g = this.graphics(this.effects);
      for (let i = 0; i < 12; i++) {
        g.fillStyle([0xffd053, 0xff8cb3, 0xb7e568][i % 3], 1 - t);
        g.fillRect(x + Math.sin(i * 9) * width * t, top - 10 - Math.sin(t * Math.PI) * 35 + Math.cos(i * 7) * t * 35, 3, 6);
      }
    }
    if (card.foundationBonus && progress > .45) this.label(this.effects, 'Streak +' + card.foundationBonus, x, Math.max(region.top + 10, top - 80), 12, '#fff0a2');
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
