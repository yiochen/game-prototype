import Phaser from 'phaser';
import { assetManifest } from './artwork.js';

export class WorldScene extends Phaser.Scene {
  constructor(getState, onFrame) { super('Dive'); this.getState = getState; this.onFrame = onFrame; }
  preload() { for (const asset of assetManifest) this.load.svg(asset.key, asset.url); }
  create() {
    this.backdrop = this.add.graphics();
    this.sub = this.add.image(0, 0, 'submarine');
    this.actors = new Map();
    this.effects = this.add.graphics();
    this.game.canvas.setAttribute('aria-label', 'Submarine travelling through a sunken city and automatically fighting incoming drones');
    this.game.canvas.setAttribute('role', 'img');
    this.game.canvas.dataset.ready = 'true';
  }
  update(_, delta) {
    this.onFrame(Math.min(delta / 1000, 0.1));
    const state = this.getState(), w = this.scale.width, h = this.scale.height, t = state.elapsed;
    this.paintWorld(w, h, t);
    const size = Math.min(w * 0.34, 160);
    this.sub.setPosition(w * state.submarine.x, h * state.submarine.y).setDisplaySize(size, size * 130 / 240);
    this.sub.setAngle(Math.sin(t * 0.7) * 2);
    const ids = new Set();
    for (const enemy of state.enemies) {
      ids.add(enemy.id);
      let sprite = this.actors.get(enemy.id);
      if (!sprite) { sprite = this.add.image(0, 0, enemy.type === 'crab' ? 'crab' : 'scout'); this.actors.set(enemy.id, sprite); }
      const width = Math.min(w * (enemy.type === 'crab' ? 0.20 : enemy.type === 'swarm' ? 0.11 : 0.155), 96);
      sprite.setPosition(enemy.x * w, enemy.y * h + Math.sin(t * 2 + enemy.id) * 3).setDisplaySize(width, width * (enemy.type === 'crab' ? 130 / 150 : 110 / 120));
      sprite.setAngle(Math.sin(t * 1.3 + enemy.id) * 7);
    }
    for (const [id, sprite] of this.actors) if (!ids.has(id)) { sprite.destroy(); this.actors.delete(id); }
    this.effects.setDepth(10).clear();
    const g = this.effects;
    for (const e of state.enemies) {
      if (e.hp === e.maxHp) continue;
      const x = e.x * w, y = e.y * h - (e.type === 'crab' ? 38 : 30), width = 30;
      g.fillStyle(0x113b4c, 0.9).fillRoundedRect(x - width / 2 - 1, y - 1, width + 2, 5, 2);
      g.fillStyle(0xf59e88).fillRoundedRect(x - width / 2, y, width * e.hp / e.maxHp, 3, 1);
    }
    for (const shot of state.shots) {
      const color = shot.hostile ? 0xff9c8a : shot.piercing ? 0x8bccff : 0x87fff0;
      g.lineStyle(8, color, shot.life * 1.8).lineBetween(shot.from.x * w, shot.from.y * h, shot.to.x * w, shot.to.y * h);
      g.lineStyle(2.2, shot.hostile ? 0xfff0b0 : 0xe9fff7, Math.min(1, shot.life * 8)).lineBetween(shot.from.x * w, shot.from.y * h, shot.to.x * w, shot.to.y * h);
      g.fillStyle(color, 0.7).fillCircle(shot.to.x * w, shot.to.y * h, 3 + shot.life * 13);
    }
    for (const burst of state.bursts) {
      for (let i = 0; i < 8; i++) {
        const angle = i * Math.PI / 4, radius = (0.5 - burst.life) * 65;
        g.fillStyle(burst.kind === 'hull' ? 0xff967a : 0xffe2a1, burst.life * 2).fillCircle(burst.x * w + Math.cos(angle) * radius, burst.y * h + Math.sin(angle) * radius, burst.life * 7);
      }
    }
  }
  paintWorld(w, h, t) {
    const g = this.backdrop; g.clear();
    for (let i = 0; i < 24; i++) {
      const color = Phaser.Display.Color.Interpolate.ColorWithColor({ r: 34, g: 120, b: 147 }, { r: 15, g: 57, b: 76 }, 24, i);
      g.fillStyle(Phaser.Display.Color.GetColor(color.r, color.g, color.b)).fillRect(0, i * h / 24, w, h / 24 + 1);
    }
    // Broad sunlight shafts, distant architecture, then slower foreground parallax.
    for (let i = 0; i < 4; i++) {
      const x = w * (0.3 + i * 0.25);
      g.fillStyle(0xa2e2d3, 0.035).fillTriangle(x, 0, x + w * 0.08, 0, x - w * 0.4, h * 0.9);
    }
    for (let layer = 0; layer < 2; layer++) {
      for (let i = 0; i < 8; i++) {
        const bw = w * (0.11 + (i % 3) * 0.025), speed = layer ? 6 : 2.8;
        const x = ((i * w * 0.22 - t * speed) % (w * 1.76) + w * 1.76) % (w * 1.76) - w * 0.28;
        const bh = h * (0.26 + ((i * 3 + layer) % 5) * 0.085), y = h * (layer ? 0.93 : 0.80) - bh;
        g.fillStyle(layer ? 0x17465a : 0x286d80, layer ? 1 : 0.7).fillRect(x, y, bw, bh);
        g.fillStyle(layer ? 0x215c69 : 0x337e8b, 0.8).fillRect(x, y, bw * 0.13, bh);
        g.fillStyle(layer ? 0x103c50 : 0x205c70).fillRect(x - 3, y, bw + 6, 7);
        g.fillRect(x + bw * 0.2, y - 10, 5, 10); g.fillRect(x + bw * 0.68, y - 16, 3, 16);
        for (let row = 0; row < 5; row++) for (let col = 0; col < 3; col++) {
          const lit = (i + row * 3 + col) % 11 === 0;
          g.fillStyle(lit ? 0xf4bf69 : layer ? 0x0c3449 : 0x22596e, lit ? 0.65 : 0.8).fillRoundedRect(x + bw * (0.22 + col * 0.25), y + 20 + row * (bh - 25) / 5, bw * 0.10, 9, 1);
        }
      }
    }
    // Cable fixes the route in the fiction, separate from the submarine's attacks.
    g.lineStyle(1.5, 0xe2c77a, 0.26);
    for (let i = 0; i < 16; i++) {
      const x = ((i * 36 - t * 9) % (w + 36) + w + 36) % (w + 36);
      const y = h * (0.67 + x / w * 0.06);
      g.lineBetween(x, y, x + 12, y + 1);
    }
    g.fillStyle(0x123a4c).fillEllipse(w * 0.3, h * 1.00, w * 1.8, h * 0.24);
    g.fillStyle(0x194858).fillEllipse(w * 0.9, h * 1.02, w * 1.2, h * 0.25);
    for (let i = 0; i < 18; i++) {
      const x = ((i * 41 - t * 5) % (w + 60) + w + 60) % (w + 60) - 20;
      const y = h * 0.96 + (i % 3) * 5, length = 12 + (i % 4) * 11;
      g.lineStyle(i % 2 ? 5 : 4, i % 2 ? 0x286c68 : 0x387e70, 0.9);
      g.beginPath(); g.moveTo(x, y); g.lineTo(x - 3, y - length * 0.5); g.lineTo(x + Math.sin(t + i) * 4, y - length); g.strokePath();
      g.fillStyle(0x528b78, 0.7).fillEllipse(x + 2, y - length * 0.5, 9, 4);
    }
    for (let i = 0; i < 22; i++) {
      const x = (i * 79.3 + Math.sin(t * 0.2 + i) * 10) % w, y = ((i * 67.7 - t * (3 + i % 4)) % h + h) % h;
      g.lineStyle(1, 0xc1e8db, 0.12 + (i % 3) * 0.06).strokeCircle(x, y, 1 + i % 3);
    }
    for (let i = 0; i < 5; i++) {
      const x = stateFreeWrap(t * 16 + i * 8, w * 0.16), y = h * 0.49 + Math.sin(t + i) * 6;
      g.lineStyle(1, 0xbae6d9, 0.25).strokeCircle(w * 0.10 - x, y, 1 + i % 3);
    }
  }
}

function stateFreeWrap(value, max) { return ((value % max) + max) % max; }

export function createWorld(parent, getState, onFrame) {
  const game = new Phaser.Game({
    type: Phaser.AUTO, parent, transparent: true, antialias: true,
    scale: { mode: Phaser.Scale.RESIZE, width: parent.clientWidth, height: parent.clientHeight },
    render: { antialias: true, roundPixels: false },
    audio: { noAudio: true }, input: { mouse: false, touch: false, keyboard: false },
    scene: new WorldScene(getState, onFrame),
  });
  const observer = new ResizeObserver(() => {
    if (parent.clientWidth && parent.clientHeight) game.scale.resize(parent.clientWidth, parent.clientHeight);
  });
  observer.observe(parent);
  return { game, destroy: () => { observer.disconnect(); game.destroy(true); } };
}
