import Phaser from 'phaser';
import { boatPosition } from './engine.js';
import { BALANCE as B } from './balance.js';

const ROUTE_COLORS = [0xdc969f, 0x79b8a6, 0xa99bce, 0xe7b477, 0x81b1cc];
export class CoastScene extends Phaser.Scene {
  constructor(getState, getUI, onFrame) { super('Coast'); this.getState = getState; this.getUI = getUI; this.onFrame = onFrame; this.clock = 0; this.fx = []; }
  create() {
    this.root = this.add.container(0, 0); this.g = this.add.graphics({ x: -200, y: -250 }); this.root.add(this.g);
    this.game.canvas.setAttribute('role', 'img'); this.game.canvas.setAttribute('aria-label', 'Six colorful toy islands, waiting ducklings, and ferries on drawn routes'); this.game.canvas.dataset.ready = 'true';
  }
  reset() { this.fx = []; }
  emit(event) { if (['deliver', 'splash', 'connect'].includes(event.type)) this.fx.push({ ...event, age: 0 }); }
  layout() {
    const { width: w, height: h } = this.scale; this.rotated = w > h * 1.2;
    this.zoom = Math.min((w - 12) / (this.rotated ? 500 : 400), (h - 12) / (this.rotated ? 400 : 500));
    this.root.setPosition(w / 2, h / 2).setScale(this.zoom).setRotation(this.rotated ? -Math.PI / 2 : 0);
  }
  toLogical(x, y) { const p = this.root.getLocalPoint(x, y); return { x: p.x + 200, y: p.y + 250 }; }
  toScreen(p) { const out = this.root.getWorldTransformMatrix().transformPoint(p.x - 200, p.y - 250); return { x: out.x, y: out.y }; }
  upright(g, x, y, draw) { g.save().translateCanvas(x, y); if (this.rotated) g.rotateCanvas(Math.PI / 2); draw(); g.restore(); }
  update(_, delta) {
    const dt = Math.min(delta / 1000, .05); this.onFrame(dt); this.layout();
    const state = this.getState(), ui = this.getUI(); if (!ui.paused) this.clock += dt;
    const t = ui.motion ? this.clock : 0, g = this.g.clear();
    this.sea(g, t);
    for (const fx of this.fx) if (!ui.paused) fx.age += dt;
    this.fx = this.fx.filter(f => f.age < 1.1);
    for (const route of state.routes) {
      const a = state.islands[route.a], b = state.islands[route.b], color = ROUTE_COLORS[route.id % ROUTE_COLORS.length];
      g.lineStyle(ui.edit ? 9 : 7, ui.edit ? 0xe9a18f : color, ui.edit ? .65 : .75).lineBetween(a.x, a.y, b.x, b.y);
      const length = Math.hypot(a.x - b.x, a.y - b.y), dots = Math.floor(length / 16);
      for (let i = 1; i < dots; i++) { const p = i / dots; g.fillStyle(0xf7fff4, .8).fillCircle(a.x + (b.x - a.x) * p, a.y + (b.y - a.y) * p, 1.7); }
    }
    if (ui.selected !== null) {
      const a = state.islands[ui.selected];
      g.lineStyle(2, 0xffffff, .8).strokeCircle(a.x, a.y, 46 + Math.sin(t * 3) * 2);
      if (ui.pointer) { g.lineStyle(5, 0xffffff, .8).lineBetween(a.x, a.y, ui.pointer.x, ui.pointer.y); g.fillStyle(0xffffff, .9).fillCircle(ui.pointer.x, ui.pointer.y, 5); }
    }
    for (const island of state.islands) {
      const active = !state.tutorial || [0, 1].includes(island.id) || state.lesson >= 2 && island.id === 2;
      this.upright(g, island.x, island.y, () => this.island(g, { ...island, x: 0, y: 0 }, state, t, active));
    }
    for (const route of state.routes) {
      const p = boatPosition(state, route), color = ROUTE_COLORS[route.id % ROUTE_COLORS.length];
      const from = state.islands[route.from], to = state.islands[route.to], distance = Math.hypot(to.x - from.x, to.y - from.y);
      const pier = Math.min(43, distance / 3) * (1 - 2 * route.progress);
      p.x += (to.x - from.x) / distance * pier; p.y += (to.y - from.y) / distance * pier;
      this.upright(g, p.x, p.y, () => this.boat(g, route, state, t, color));
    }
    if (state.tutorial && (state.lesson === 0 || state.lesson === 2)) {
      const a = state.islands[0], b = state.islands[state.lesson === 0 ? 1 : 2], p = (Math.sin(t * 1.7) + 1) / 2;
      g.lineStyle(2, 0xffffff, .45).lineBetween(a.x, a.y, b.x, b.y);
      g.lineStyle(3, 0xffffff, .9).strokeCircle(b.x, b.y, 48 + Math.sin(t * 3) * 2);
      if (ui.selected === null) { const x = a.x + (b.x - a.x) * p, y = a.y + (b.y - a.y) * p; g.fillStyle(0xffffff, .85).fillCircle(x, y, 8); g.lineStyle(2, 0x79afa3).strokeCircle(x, y, 8); }
    }
    for (const fx of this.fx) {
      const island = state.islands[fx.island ?? fx.b]; if (!island) continue;
      const alpha = 1 - fx.age / 1.1, color = fx.type === 'splash' ? 0xf2aca3 : 0xfffae2;
      g.lineStyle(3 * alpha, color, alpha).strokeEllipse(island.x, island.y + 13, 88 + fx.age * 65, 60 + fx.age * 42);
      if (ui.motion && fx.type === 'deliver') for (let i = 0; i < 9; i++) { const a = i * 2.399, d = 25 + fx.age * 55; g.fillStyle(island.color, alpha).fillCircle(island.x + Math.cos(a) * d, island.y + Math.sin(a) * d - fx.age * 18, 3); }
    }
  }
  sea(g, t) {
    g.fillStyle(0xbce4df).fillRoundedRect(10, 12, 380, 475, 60);
    g.fillStyle(0xc9eae2, .6).fillEllipse(192, 250, 342, 345);
    for (let i = 0; i < 34; i++) {
      const x = 25 + i * 73 % 348, y = 27 + i * 127 % 440, sway = Math.sin(t * .65 + i) * 4;
      g.lineStyle(1.5, 0xf4fff0, .3 + Math.sin(t * .7 + i) * .1).beginPath().arc(x + sway, y, 9, .4, 2.7).strokePath();
    }
    g.fillStyle(0x9bcdc4, .6).fillEllipse(342, 305, 22, 16).fillEllipse(350, 303, 10, 7);
    g.fillStyle(0xd5ddd1).fillEllipse(346, 299, 19, 15); g.fillStyle(0xabb8a6).fillEllipse(345, 296, 14, 9);
    g.fillStyle(0xf5f0da).fillCircle(35, 432, 9).fillCircle(42, 425, 7); g.fillStyle(0xc8cbbb).fillEllipse(38, 430, 7, 3);
    g.lineStyle(2, 0xa6d7ca, .7).strokeRoundedRect(11, 13, 378, 473, 60);
  }
  symbol(g, shape, x, y, size, color, background = 0xfffbeb) {
    g.fillStyle(color);
    if (shape === 'star' || shape === 'sun') {
      const points = []; for (let i = 0; i < 10; i++) { const a = i * Math.PI / 5 - Math.PI / 2, r = i % 2 ? size * .52 : size; points.push({ x: x + Math.cos(a) * r, y: y + Math.sin(a) * r }); } g.fillPoints(points, true);
      if (shape === 'sun') g.fillCircle(x, y, size * .6);
    } else if (shape === 'heart') { g.fillCircle(x - size * .4, y - size * .2, size * .55).fillCircle(x + size * .4, y - size * .2, size * .55).fillTriangle(x - size * .9, y - size * .1, x + size * .9, y - size * .1, x, y + size); }
    else if (shape === 'leaf') { g.fillEllipse(x, y, size * 1.25, size * 1.9); g.lineStyle(1, 0xffffff, .8).lineBetween(x, y - size * .7, x, y + size * .7); }
    else if (shape === 'moon') { g.fillCircle(x, y, size); g.fillStyle(background).fillCircle(x + size * .45, y - size * .3, size * .8); }
    else g.fillPoints([{ x, y: y - size }, { x: x + size * .85, y }, { x, y: y + size }, { x: x - size * .85, y }], true);
  }
  island(g, island, state, t, active) {
    const { x, y, color } = island;
    g.fillStyle(0x609f91, .16).fillEllipse(x + 2, y + 21, 99, 70);
    g.fillStyle(active ? 0xe1cb9c : 0xd3dbbf).fillEllipse(x, y + 10, 91, 68);
    g.fillStyle(active ? 0xfff1c5 : 0xe0e8cc).fillEllipse(x, y + 4, 91, 62);
    g.fillStyle(active ? 0xd1dda7 : 0xd4e2c8).fillEllipse(x, y, 73, 46);
    g.fillStyle(active ? 0xb4c990 : 0xbdd5b5).fillEllipse(x - 23, y - 4, 16, 28);
    g.fillStyle(active ? 0xa3bf88 : 0xbdd5b5).fillEllipse(x - 18, y - 16, 16, 20);
    g.lineStyle(3, 0xb6a078).lineBetween(x + 9, y - 3, x + 9, y - 37);
    g.fillStyle(active ? color : 0xb6cdc1).fillRoundedRect(x - 6, y - 49, 31, 27, 10);
    this.symbol(g, island.shape, x + 9, y - 36, 7.5, 0xfffbeb, active ? color : 0xb6cdc1);
    g.fillStyle(0xfffbeb).fillCircle(x - 29, y + 15, 3).fillCircle(x + 29, y + 11, 2);
    island.ducks.slice(0, 4).forEach((d, i) => {
      const target = state.islands[d.destination], dx = x - 25 + i * 16, dy = y + 7 + (i % 2 ? -2 : 2);
      this.duck(g, dx, dy + Math.sin(t * 2 + i) * 1, target.color, .85);
      g.fillStyle(target.color).fillCircle(dx - 2, dy - 13, 7);
      this.symbol(g, target.shape, dx - 2, dy - 13, 3.8, 0xfffbeb, target.color);
      if (!state.tutorial && d.age > B.patience * .65) { const danger = Math.min(1, d.age / B.patience); g.lineStyle(2, 0xe99ba1, .9).beginPath().arc(dx, dy + 2, 12, -Math.PI / 2, -Math.PI / 2 + danger * Math.PI * 2).strokePath(); }
    });
    if (island.ducks.length > 4) for (let i = 0; i < Math.min(4, island.ducks.length - 4); i++) g.fillStyle(0xee939b).fillCircle(x - 10 + i * 6, y + 23, 2.2);
  }
  duck(g, x, y, color, scale = 1) {
    g.fillStyle(color).fillEllipse(x, y + 5 * scale, 20 * scale, 14 * scale);
    g.fillStyle(0xfff8dc).fillCircle(x + 5 * scale, y - 3 * scale, 7 * scale);
    g.fillStyle(0xf0b856).fillTriangle(x + 9 * scale, y - 3 * scale, x + 15 * scale, y - 1 * scale, x + 9 * scale, y + 1 * scale);
    g.fillStyle(0x416865).fillCircle(x + 7 * scale, y - 4 * scale, 1.25 * scale);
    g.fillStyle(0xffffff, .4).fillEllipse(x - 3 * scale, y + 3 * scale, 8 * scale, 5 * scale);
  }
  boat(g, route, state, t, color) {
    const bob = Math.sin(t * 2 + route.id) * 1.4;
    g.lineStyle(2, 0xf2fff4, .55).strokeEllipse(0, 12 + bob, 61, 20);
    g.fillStyle(0x4e9589, .15).fillEllipse(0, 10 + bob, 52, 20);
    g.fillStyle(0x718d82).fillEllipse(0, 7 + bob, 47, 24);
    g.fillStyle(color).fillEllipse(0, 4 + bob, 47, 23);
    g.fillStyle(0xfff2cf).fillEllipse(0, 1 + bob, 41, 16);
    g.fillStyle(0xe4c696).fillRoundedRect(-18, -1 + bob, 32, 6, 3);
    g.lineStyle(2, 0x739589).lineBetween(-17, bob - 3, -17, bob - 21);
    g.fillStyle(color).fillTriangle(-16, bob - 21, -16, bob - 11, -5, bob - 17);
    route.passengers.forEach((duck, i) => this.duck(g, -8 + i * 9, -5 + bob, state.islands[duck.destination].color, .6));
    if (!route.passengers.length) g.fillStyle(0xe7bd75).fillCircle(2, bob - 3, 3);
  }
}
export function mountWorld(getState, getUI, onFrame) {
  const scene = new CoastScene(getState, getUI, onFrame);
  const parent = document.getElementById('world');
  const game = new Phaser.Game({ type: Phaser.AUTO, parent: 'world', transparent: true, antialias: true, scale: { mode: Phaser.Scale.NONE, width: parent.clientWidth, height: parent.clientHeight }, scene, audio: { noAudio: true } });
  const observer = new ResizeObserver(() => { if (parent.clientWidth && parent.clientHeight) game.scale.resize(parent.clientWidth, parent.clientHeight); }); observer.observe(parent);
  game.events.once('destroy', () => observer.disconnect());
  return { scene, game };
}
