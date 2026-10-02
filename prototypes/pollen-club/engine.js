import { BALANCE as B, GARDENS, LESSONS } from './balance.js';

export function createGame(level = 0, tutorial = false) {
  const data = (tutorial ? LESSONS : GARDENS)[level % (tutorial ? LESSONS : GARDENS).length];
  return {
    level, tutorial, name: data.name, par: data.par, home: { x: data.home[0], y: data.home[1] },
    flowers: data.flowers.map(([x, y], id) => ({ id, x, y, awake: false })),
    drops: data.drops.map(([x, y, radius], id) => ({ id, x, y, radius })),
    wind: { x: data.wind[0], y: data.wind[1] },
    bee: { x: data.home[0], y: data.home[1], vx: 0, vy: 0 },
    status: 'ready', shots: 0, elapsed: 0, accumulator: 0, events: [], bounces: 0,
  };
}
export function launch(state, pull) {
  if (state.status !== 'ready' || !Number.isFinite(pull.x) || !Number.isFinite(pull.y)) return false;
  const length = Math.hypot(pull.x, pull.y);
  if (length < B.pullMin) return false;
  const strength = Math.min(length, B.pullMax) / length * B.launchPower;
  state.bee.vx = -pull.x * strength; state.bee.vy = -pull.y * strength;
  state.status = 'flying'; state.elapsed = 0; state.accumulator = 0; state.shots++;
  state.events.push({ type: 'launch', ...state.bee }); return true;
}
function integrate(state, dt) {
  const b = state.bee;
  b.vx += state.wind.x * dt; b.vy += state.wind.y * dt;
  b.vx *= Math.exp(-B.friction * dt); b.vy *= Math.exp(-B.friction * dt);
  b.x += b.vx * dt; b.y += b.vy * dt; state.elapsed += dt;
  for (const [axis, low, high] of [['x', 22, B.width - 22], ['y', 26, B.height - 24]]) {
    if (b[axis] < low || b[axis] > high) {
      b[axis] = Math.max(low, Math.min(high, b[axis]));
      b[`v${axis}`] *= -B.restitution;
      state.events.push({ type: 'bounce', x: b.x, y: b.y }); state.bounces++;
    }
  }
  for (const drop of state.drops) {
    let dx = b.x - drop.x, dy = b.y - drop.y;
    const distance = Math.hypot(dx, dy), radius = drop.radius + B.beeRadius;
    if (distance >= radius) continue;
    if (distance < 0.001) { dx = 1; dy = 0; }
    const norm = Math.hypot(dx, dy), nx = dx / norm, ny = dy / norm;
    b.x = drop.x + nx * (radius + 0.1); b.y = drop.y + ny * (radius + 0.1);
    const dot = b.vx * nx + b.vy * ny;
    if (dot < 0) {
      b.vx -= (1 + B.restitution) * dot * nx; b.vy -= (1 + B.restitution) * dot * ny;
      state.events.push({ type: 'bounce', x: drop.x, y: drop.y, id: drop.id }); state.bounces++;
    }
  }
  for (const flower of state.flowers) {
    if (flower.awake || Math.hypot(b.x - flower.x, b.y - flower.y) > B.flowerRadius + B.beeRadius) continue;
    flower.awake = true; state.events.push({ type: 'bloom', x: flower.x, y: flower.y, id: flower.id });
  }
  if (state.flowers.every(f => f.awake)) {
    state.status = 'won'; state.events.push({ type: 'win', x: b.x, y: b.y });
  } else if (state.elapsed >= B.maxFlight || Math.hypot(b.vx, b.vy) < B.stopSpeed) {
    recall(state);
  }
}
export function tick(state, dt) {
  if (state.status !== 'flying' || !Number.isFinite(dt) || dt <= 0) return;
  state.accumulator += Math.min(dt, 10);
  while (state.accumulator + 1e-10 >= B.step && state.status === 'flying') {
    state.accumulator -= B.step; integrate(state, B.step);
  }
}
export function recall(state) {
  if (state.status !== 'flying') return false;
  state.status = 'ready'; state.bee = { ...state.home, vx: 0, vy: 0 };
  state.events.push({ type: 'return', ...state.home }); return true;
}
// Preview follows the real integrator, including wind, rims and dewdrops.
export function trajectory(state, pull) {
  const copy = structuredClone(state); copy.events = [];
  if (!launch(copy, pull)) return [];
  const points = [];
  for (let i = 0; i < 26 && copy.status === 'flying'; i++) {
    tick(copy, 0.045); points.push({ x: copy.bee.x, y: copy.bee.y }); copy.events = [];
  }
  return points;
}
export function medal(state) { return state.status !== 'won' ? 0 : state.shots <= state.par ? 3 : state.shots <= state.par + 2 ? 2 : 1; }
