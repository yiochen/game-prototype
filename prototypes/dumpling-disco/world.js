import Phaser from 'phaser';
import { BALANCE as B, MIXES } from './balance.js';

export class KitchenScene extends Phaser.Scene {
  constructor(getState, getUI, onFrame) { super('Kitchen'); this.getState = getState; this.getUI = getUI; this.onFrame = onFrame; this.clock = 0; this.fx = []; }
  create() {
    this.root = this.add.container(0, 0); this.g = this.add.graphics({ x: -200, y: -250 }); this.root.add(this.g);
    this.game.canvas.setAttribute('role', 'img'); this.game.canvas.setAttribute('aria-label', 'Dancing dumplings in a pan. Beat rings shrink toward the gold rim; thick green rings ask for a hold.'); this.game.canvas.dataset.ready = 'true';
  }
  reset() { this.fx = []; }
  emit(event) { if (['perfect', 'good', 'miss', 'steam'].includes(event.type)) this.fx.push({ ...event, age: 0 }); }
  update(_, delta) {
    const dt = Math.min(delta / 1000, .05); this.onFrame(dt);
    const state = this.getState(), ui = this.getUI(); if (!ui.paused) this.clock += dt;
    const t = ui.motion ? this.clock : 0, g = this.g.clear();
    const { width: w, height: h } = this.scale, rotated = w > h * 1.2;
    this.root.setPosition(w / 2, h / 2).setScale(Math.min((w - 12) / (rotated ? 500 : 400), (h - 12) / (rotated ? 400 : 500))).setRotation(rotated ? -Math.PI / 2 : 0);
    this.backdrop(g, t);
    for (const fx of this.fx) if (!ui.paused) fx.age += dt;
    this.fx = this.fx.filter(f => f.age < .9);
    const beat = 60 / MIXES[state.mix].bpm, phase = (state.time % beat) / beat;
    g.fillStyle(0x443b56, .14).fillEllipse(200, 387, 238, 31);
    g.fillStyle(0x9987b4).fillRoundedRect(161, 361, 78, 71, 22);
    g.fillStyle(0xc2b3d4).fillRoundedRect(173, 371, 54, 45, 12);
    g.fillStyle(0x675972).fillRoundedRect(42, 246, 53, 25, 12).fillRoundedRect(305, 246, 53, 25, 12);
    g.lineStyle(4, 0xbda5b4).strokeRoundedRect(43, 247, 52, 23, 12).strokeRoundedRect(306, 247, 52, 23, 12);
    g.fillStyle(0x695d7a).fillCircle(200, 259, 122);
    g.fillStyle(0x51475e).fillCircle(200, 257, 112);
    g.fillStyle(0x60556d).fillCircle(200, 254, 100);
    g.lineStyle(6, 0xe9b774).strokeCircle(200, 257, 119);
    g.lineStyle(1.5, 0xffd896, .6).strokeCircle(200, 257, 124);
    // The rim's beat pulse is a time cue even with sound and decorative motion off.
    g.lineStyle(2, 0xffe6b0, Math.max(0, 1 - phase * 3) * .7).strokeCircle(200, 257, 126 + phase * 8);
    const upcoming = state.notes.filter(n => n.status === 'waiting' && n.time - state.time <= B.early && n.time - state.time >= -B.good).reverse();
    for (const note of upcoming) {
      const progress = Math.max(0, Math.min(1.15, (state.time - note.time + B.early) / B.early));
      const radius = 205 - progress * 86;
      const color = note.kind === 'hold' ? 0xb6e0bf : 0xf7c384;
      g.lineStyle(note.kind === 'hold' ? 8 : 4, color, .3 + Math.min(1, progress) * .65).strokeCircle(200, 257, radius);
      if (note.kind === 'hold') { g.lineStyle(2, 0xe4f8dc, .7).strokeCircle(200, 257, radius + 7); for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; g.fillStyle(color, .9).fillCircle(200 + Math.cos(a) * radius, 257 + Math.sin(a) * radius, 5); } }
      else { g.fillStyle(0xffe9b8, .9).fillCircle(200, 257 - radius, 6); }
    }
    const holding = state.held !== null ? state.notes[state.held] : null;
    if (holding) {
      const progress = Math.min(1, Math.max(0, (state.time - holding.time) / holding.duration));
      g.fillStyle(0xd1efba, .12).fillCircle(200, 257, 110);
      g.lineStyle(9, 0xc4e8b6).beginPath().arc(200, 257, 119, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * progress).strokePath();
      for (let i = 0; i < 6; i++) { const y = 220 - (state.time * 55 + i * 23) % 110; g.lineStyle(5, 0xfffbeb, .18 + progress * .2).beginPath().arc(148 + i * 20, y, 9, -.8, .8).strokePath(); }
    }
    for (let i = 0; i < 3; i++) {
      const flip = this.fx.findLast(f => f.id % 3 === i && ['perfect', 'good'].includes(f.type));
      const miss = this.fx.findLast(f => f.id % 3 === i && f.type === 'miss');
      const jump = flip && ui.motion ? Math.sin(Math.min(1, flip.age / .65) * Math.PI) * 60 : 0;
      const x = [152, 249, 198][i], y = [283, 284, 225][i] - jump;
      const squash = flip && ui.motion ? 1 + Math.sin(flip.age * 12) * .13 : 1;
      g.save().translateCanvas(x, y + (ui.motion ? Math.sin(t * 2 + i) * 2 : 0)); if (rotated) g.rotateCanvas(Math.PI / 2);
      this.dumpling(g, 0, 0, squash, Boolean(miss), i, Boolean(holding)); g.restore();
      if (flip) { g.fillStyle(0xffd780, (1 - flip.age / .9) * .8).fillCircle(x + 34, y - 34, 3).fillCircle(x - 33, y - 15, 2); }
    }
    for (const fx of this.fx) if (fx.type === 'perfect' || fx.type === 'good') {
      const alpha = Math.max(0, 1 - fx.age / .9);
      for (let i = 0; i < (ui.motion ? 12 : 0); i++) { const a = i * 2.399, d = 90 + fx.age * 80; this.star(g, 200 + Math.cos(a) * d, 257 + Math.sin(a) * d, 4, i % 2 ? 0xffc67b : 0xb8d8af, alpha); }
    }
    const done = state.notes.filter(n => n.status === 'done').length;
    for (let i = 0; i < state.notes.length; i++) { const x = 45 + i / (state.notes.length - 1) * 310; g.fillStyle(i < done ? state.notes[i].grade === 'miss' ? 0xc0b0cc : 0xe3b96b : 0xdcd1e5).fillCircle(x, 460, i < done ? 3.5 : 2.5); }
  }
  star(g, x, y, size, color, alpha = 1) { g.fillStyle(color, alpha).fillPoints([{ x, y: y - size * 1.5 }, { x: x + size * .4, y: y - size * .4 }, { x: x + size * 1.5, y }, { x: x + size * .4, y: y + size * .4 }, { x, y: y + size * 1.5 }, { x: x - size * .4, y: y + size * .4 }, { x: x - size * 1.5, y }, { x: x - size * .4, y: y - size * .4 }], true); }
  backdrop(g, t) {
    g.fillStyle(0xede2f0).fillRoundedRect(13, 16, 374, 469, 60);
    g.fillStyle(0xe5d8eb).fillRoundedRect(16, 18, 368, 75, 45);
    for (let i = 0; i < 8; i++) g.fillStyle(i % 2 ? 0xeacbdd : 0xf5e4e9).fillRoundedRect(28 + i * 44, 19, 42, 53 + (i % 2) * 8, { tl: 0, tr: 0, bl: 20, br: 20 });
    g.lineStyle(2, 0xd3bfd8, .65).lineBetween(28, 101, 373, 101);
    g.fillStyle(0xcab5d0).fillRoundedRect(20, 410, 360, 30, 12);
    g.fillStyle(0xf3e2cf).fillRoundedRect(36, 373, 39, 42, 9);
    g.fillStyle(0xa5c596).fillEllipse(57, 361, 20, 34).fillEllipse(43, 369, 19, 29).fillEllipse(68, 372, 20, 25);
    g.lineStyle(2, 0x80a77a).lineBetween(56, 390, 56, 352);
    g.fillStyle(0xedc382).fillRoundedRect(319, 378, 28, 35, 7); g.fillStyle(0xe9ad75).fillRoundedRect(321, 372, 24, 10, 4);
    g.fillStyle(0xf6e6d4).fillRoundedRect(323, 387, 20, 13, 3); g.fillStyle(0x8e789e).fillCircle(333, 393, 3);
    for (const [x, y, s] of [[51, 150, 6], [343, 126, 5], [74, 342, 4], [310, 352, 6]]) this.star(g, x, y + Math.sin(t + x) * 2, s, 0xc8b1d7, .6);
    g.lineStyle(3, 0xd9c7df, .5).strokeRoundedRect(14, 17, 372, 467, 60);
  }
  dumpling(g, x, y, squash, sad, index, steaming) {
    const w = 62 * squash, h = 49 / squash;
    g.fillStyle(0x292335, .2).fillEllipse(x, y + 28, 61, 15);
    g.lineStyle(3, 0xe5baa0).lineBetween(x - w * .44, y + 4, x - w * .56, y - 3).lineBetween(x + w * .44, y + 4, x + w * .56, y - 4);
    g.fillStyle(sad ? 0xe9dace : steaming ? 0xf8eddd : 0xffecd7).fillEllipse(x, y + 4, w, h);
    g.fillStyle(0xfff2dd).fillTriangle(x - w * .46, y + 3, x, y - h * .66, x + w * .46, y + 3);
    g.lineStyle(2, 0xe3bfa9, .85);
    for (let i = -2; i <= 2; i++) g.lineBetween(x + i * 9 * squash, y - h * .34 + Math.abs(i) * 3, x + i * 6, y - 2);
    g.fillStyle([0xb4cca0, 0xf2bb81, 0xb9a4d5][index]).fillEllipse(x, y - h * .4 - 3, 16, 7);
    g.fillStyle(0x675365).fillCircle(x - 9, y + 5, 2.2).fillCircle(x + 9, y + 5, 2.2);
    g.lineStyle(2, 0x675365).beginPath().arc(x, y + (sad ? 16 : 10), 5, sad ? Math.PI + .2 : .1, sad ? Math.PI * 2 - .2 : Math.PI - .1).strokePath();
    g.fillStyle(0xe9a3a6, .7).fillEllipse(x - 17, y + 11, 8, 5).fillEllipse(x + 17, y + 11, 8, 5);
  }
}
export function mountWorld(getState, getUI, onFrame) {
  const scene = new KitchenScene(getState, getUI, onFrame);
  const parent = document.getElementById('world');
  const game = new Phaser.Game({ type: Phaser.AUTO, parent: 'world', transparent: true, antialias: true, scale: { mode: Phaser.Scale.NONE, width: parent.clientWidth, height: parent.clientHeight }, scene, audio: { noAudio: true } });
  const observer = new ResizeObserver(() => { if (parent.clientWidth && parent.clientHeight) game.scale.resize(parent.clientWidth, parent.clientHeight); }); observer.observe(parent);
  game.events.once('destroy', () => observer.disconnect());
  return { scene, game };
}
