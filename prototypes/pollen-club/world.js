import Phaser from 'phaser';

const COLORS = [0xee9aa8, 0xe7be70, 0xb5a7dc];
export class GardenScene extends Phaser.Scene {
  constructor(getState, getUI, onFrame) { super('Garden'); this.getState = getState; this.getUI = getUI; this.onFrame = onFrame; this.clock = 0; this.fx = []; this.trail = []; }
  create() {
    this.root = this.add.container(0, 0); this.g = this.add.graphics({ x: -200, y: -250 }); this.root.add(this.g);
    this.game.canvas.setAttribute('role', 'img'); this.game.canvas.setAttribute('aria-label', 'A bee, sleepy flowers, and shiny dewdrops in a little garden'); this.game.canvas.dataset.ready = 'true';
  }
  layout() {
    const { width: w, height: h } = this.scale; this.rotated = w > h * 1.2;
    this.zoom = Math.min((w - 12) / (this.rotated ? 500 : 400), (h - 12) / (this.rotated ? 400 : 500));
    this.root.setPosition(w / 2, h / 2).setScale(this.zoom).setRotation(this.rotated ? -Math.PI / 2 : 0);
  }
  toLogical(x, y) {
    const p = this.root.getLocalPoint(x, y); return { x: p.x + 200, y: p.y + 250 };
  }
  toScreen(p) {
    const out = this.root.getWorldTransformMatrix().transformPoint(p.x - 200, p.y - 250);
    return { x: out.x, y: out.y };
  }
  reset() { this.fx = []; this.trail = []; }
  emit(event) {
    if (!['bloom', 'bounce', 'return', 'win'].includes(event.type)) return;
    this.fx.push({ ...event, age: 0 });
  }
  update(_, delta) {
    const dt = Math.min(delta / 1000, 0.05); this.onFrame(dt); this.layout();
    const state = this.getState(), ui = this.getUI();
    if (!ui.paused) this.clock += dt;
    const t = ui.motion ? this.clock : 0;
    for (const fx of this.fx) if (!ui.paused) fx.age += dt;
    this.fx = this.fx.filter(f => f.age < 1);
    if (state.status === 'flying' && !ui.paused) { this.trail.push({ x: state.bee.x, y: state.bee.y }); if (this.trail.length > 35) this.trail.shift(); }
    else if (state.status === 'ready') this.trail = [];
    const g = this.g.clear();
    this.garden(g, t);
    for (const drop of state.drops) this.drop(g, drop, t, ui.motion);
    state.flowers.forEach((f, i) => {
      g.save().translateCanvas(f.x, f.y); if (this.rotated) g.rotateCanvas(Math.PI / 2);
      this.flower(g, { ...f, x: 0, y: 0 }, COLORS[i % COLORS.length], t); g.restore();
    });
    g.fillStyle(0xd4ccac, 0.4).fillEllipse(state.home.x, state.home.y + 18, 65, 20);
    g.lineStyle(3, 0xd8c6a1, 0.7).strokeEllipse(state.home.x, state.home.y + 15, 60, 19);
    g.fillStyle(0xe4d4b5).fillEllipse(state.home.x, state.home.y + 13, 51, 14);
    g.fillStyle(0xf7edcd).fillEllipse(state.home.x, state.home.y + 10, 45, 13);
    for (let i = 0; i < this.trail.length; i++) { const p = this.trail[i]; g.fillStyle(0xe8b94e, i / this.trail.length * 0.4).fillCircle(p.x, p.y, 2 + i / this.trail.length * 3); }
    if (ui.pull && state.status === 'ready') {
      const points = ui.preview;
      points.forEach((p, i) => g.fillStyle(0x718e76, 0.6 * (1 - i / points.length)).fillCircle(p.x, p.y, 3.6 - i / points.length * 1.5));
      const length = Math.hypot(ui.pull.x, ui.pull.y), cap = Math.min(1, 96 / Math.max(1, length));
      g.lineStyle(5, 0xd1bf86, 0.7).lineBetween(state.home.x - 12, state.home.y + 10, state.home.x + ui.pull.x * cap * 0.7, state.home.y + ui.pull.y * cap * 0.7);
      g.lineStyle(5, 0xd1bf86, 0.7).lineBetween(state.home.x + 12, state.home.y + 10, state.home.x + ui.pull.x * cap * 0.7, state.home.y + ui.pull.y * cap * 0.7);
      this.uprightBee(g, state.home.x + ui.pull.x * cap * 0.7, state.home.y + ui.pull.y * cap * 0.7, t, false);
    } else this.uprightBee(g, state.bee.x, state.bee.y + (state.status === 'ready' ? Math.sin(t * 2) * 2 : 0), t, state.status === 'flying');
    if (state.wind.x || state.wind.y) {
      const direction = state.wind.x < 0 ? -1 : 1;
      for (let i = 0; i < 3; i++) { const x = 160 + i * 25 + Math.sin(t * 2 - i) * 6; g.lineStyle(2, 0x9dbda5, 0.7).lineBetween(x, 32, x + 18 * direction, 32); g.lineBetween(x + 18 * direction, 32, x + 12 * direction, 27); }
    }
    if (state.tutorial && state.status === 'ready' && !ui.pull) this.hand(g, state.home, t);
    for (const fx of this.fx) {
      const color = fx.type === 'bloom' ? COLORS[fx.id % COLORS.length] : 0xa7d9d1;
      g.lineStyle(3 * (1 - fx.age), color, 1 - fx.age).strokeCircle(fx.x, fx.y, 20 + fx.age * 55);
      if (ui.motion) for (let i = 0; i < (fx.type === 'bloom' ? 12 : 5); i++) {
        const a = i * 2.399; const d = fx.age * 70;
        g.fillStyle(color, 1 - fx.age).fillEllipse(fx.x + Math.cos(a) * d, fx.y + Math.sin(a) * d + fx.age * fx.age * 45, 7, 11);
      }
    }
  }
  garden(g, t) {
    g.fillStyle(0xe7edda).fillRoundedRect(12, 15, 376, 470, 65);
    g.fillStyle(0xeef1df).fillEllipse(220, 215, 330, 340);
    g.fillStyle(0xdbe7ca).fillEllipse(77, 400, 124, 105).fillEllipse(343, 330, 72, 130);
    g.lineStyle(2, 0xb4c4a1, 0.4);
    for (let i = 0; i < 38; i++) {
      const x = 30 + (i * 71 % 345), y = 39 + (i * 137 % 423);
      const sway = Math.sin(t * 1.5 + i) * 2;
      g.lineBetween(x, y + 8, x + sway, y).lineBetween(x + sway, y, x - 4, y + 3);
      if (i % 4 === 0) g.fillStyle(0xfff9e8, 0.7).fillCircle(x - 6, y - 2, 3);
    }
    for (const [x, y] of [[25, 130], [357, 455], [30, 300], [350, 44]]) {
      g.fillStyle(0xa3bc90).fillEllipse(x, y, 14, 30).fillEllipse(x + 13, y - 7, 15, 24);
      g.lineStyle(1, 0x809f7f, 0.5).lineBetween(x - 2, y + 13, x + 4, y - 10);
    }
    g.lineStyle(3, 0xc1cfb0, 0.7).strokeRoundedRect(13, 16, 374, 468, 65);
  }
  flower(g, f, color, t) {
    const open = f.awake, sway = Math.sin(t * 1.5 + f.id) * (open ? 2 : 0.8);
    g.fillStyle(0x729773, 0.13).fillEllipse(f.x, f.y + 31, 59, 19);
    g.lineStyle(5, 0x80a780).lineBetween(f.x, f.y + 5, f.x - 1, f.y + 30);
    g.fillStyle(0x9aba8a).fillEllipse(f.x - 14, f.y + 21, 22, 10).fillEllipse(f.x + 12, f.y + 16, 20, 11);
    const spread = open ? 22 : 15, r = open ? 13 : 12;
    for (let i = 0; i < 7; i++) { const a = i * Math.PI * 2 / 7 + (open ? t * .04 : 0); g.fillStyle(color).fillCircle(f.x + Math.cos(a) * spread + sway, f.y + Math.sin(a) * spread, r); }
    g.fillStyle(0xffeed0).fillCircle(f.x + sway, f.y, open ? 16 : 13);
    if (open) { g.fillStyle(0x605c4b).fillCircle(f.x - 5 + sway, f.y - 2, 1.8).fillCircle(f.x + 5 + sway, f.y - 2, 1.8); g.lineStyle(1.8, 0x605c4b).beginPath().arc(f.x + sway, f.y + 2, 5, 0.1, Math.PI - 0.1).strokePath(); }
    else { g.lineStyle(1.8, 0x605c4b).lineBetween(f.x - 7, f.y - 1, f.x - 3, f.y + 1).lineBetween(f.x + 3, f.y + 1, f.x + 7, f.y - 1); }
    g.fillStyle(0xe2a186, 0.55).fillEllipse(f.x - 9 + sway, f.y + 4, 5, 3).fillEllipse(f.x + 9 + sway, f.y + 4, 5, 3);
    if (open) { g.fillStyle(0xf6cd77).fillCircle(f.x + 23, f.y - 30 + Math.sin(t * 2) * 2, 3).fillCircle(f.x - 30, f.y - 12, 2); }
  }
  drop(g, d, t, motion) {
    const shimmer = motion ? Math.sin(t * 1.3 + d.id) * 1.5 : 0;
    g.fillStyle(0x659888, 0.12).fillEllipse(d.x + 2, d.y + d.radius * .75, d.radius * 2, 15);
    g.fillStyle(0x9dd7d0, 0.65).fillCircle(d.x, d.y, d.radius);
    g.lineStyle(2.5, 0x6fb5ae, .75).strokeCircle(d.x, d.y, d.radius);
    g.fillStyle(0xddf8ea, 0.8).fillEllipse(d.x - d.radius * .25, d.y - d.radius * .3, d.radius * .65, d.radius * .4);
    g.fillStyle(0xffffff, 0.9).fillCircle(d.x - d.radius * .3, d.y - d.radius * .4 + shimmer, 4);
    g.lineStyle(2, 0xf5fff5, .75).beginPath().arc(d.x, d.y, d.radius - 5, 0.4, 1.3).strokePath();
  }
  bee(g, x, y, t, flying) {
    const wing = 9 + Math.sin(t * (flying ? 65 : 12)) * 3;
    g.fillStyle(0xffffff, .9).fillEllipse(x - 3, y - 12, 15, wing * 2).fillEllipse(x + 8, y - 11, 15, wing * 2);
    g.lineStyle(1.3, 0xb5ccc2).strokeEllipse(x - 3, y - 12, 15, wing * 2);
    g.fillStyle(0x655c45).fillEllipse(x, y, 37, 25);
    g.fillStyle(0xf3c755).fillEllipse(x + 1, y - 1, 34, 23);
    g.fillStyle(0x74613f).fillRoundedRect(x - 9, y - 10, 5, 20, 2).fillRoundedRect(x + 1, y - 10, 5, 20, 2);
    g.fillStyle(0xffd967).fillCircle(x + 13, y - 2, 11);
    g.lineStyle(2, 0x655c45).lineBetween(x + 14, y - 10, x + 16, y - 18);
    g.fillStyle(0x655c45).fillCircle(x + 17, y - 18, 2.5).fillCircle(x + 15, y - 4, 2);
    g.fillStyle(0xe98b70, .7).fillCircle(x + 19, y + 1, 3);
    g.fillStyle(0x655c45).fillTriangle(x - 22, y, x - 14, y - 3, x - 14, y + 3);
  }
  uprightBee(g, x, y, t, flying) { g.save().translateCanvas(x, y); if (this.rotated) g.rotateCanvas(Math.PI / 2); this.bee(g, 0, 0, t, flying); g.restore(); }
  hand(g, home, t) {
    const pull = 15 + (Math.sin(t * 2) + 1) * 24;
    g.lineStyle(2, 0xffffff, 0.9).lineBetween(home.x, home.y + 22, home.x, home.y + pull + 15);
    g.fillStyle(0xffffff, 0.85).fillCircle(home.x, home.y + pull + 15, 10);
    g.lineStyle(2, 0xafba9c).strokeCircle(home.x, home.y + pull + 15, 10);
    g.lineStyle(2, 0x879d7d).lineBetween(home.x, home.y + pull + 18, home.x, home.y + pull + 8);
  }
}
export function mountWorld(getState, getUI, onFrame) {
  const scene = new GardenScene(getState, getUI, onFrame);
  const parent = document.getElementById('world');
  const game = new Phaser.Game({ type: Phaser.AUTO, parent: 'world', transparent: true, antialias: true, scale: { mode: Phaser.Scale.NONE, width: parent.clientWidth, height: parent.clientHeight }, scene, audio: { noAudio: true }, render: { roundPixels: false } });
  const observer = new ResizeObserver(() => { if (parent.clientWidth && parent.clientHeight) game.scale.resize(parent.clientWidth, parent.clientHeight); }); observer.observe(parent);
  game.events.once('destroy', () => observer.disconnect());
  return { scene, game };
}
