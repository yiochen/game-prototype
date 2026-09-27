import { BALANCE as B, PART_RULES } from './balance.js';
import { PARTS } from './parts.js';
import { RECIPES, findRecipe, compatibleTypes } from './recipes.js';

const DIR = [[0, -1], [1, 0], [0, 1], [-1, 0]];
const mod = n => (n + 4) % 4;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

export function traceCircuit(grid) {
  const segments = [], guns = new Map(), active = new Set(), blocked = [], queue = [];
  grid.forEach((part, index) => {
    if (part && (PARTS[part.type].base || part.type) === 'reactor') {
      active.add(index);
      queue.push({ index, direction: part.rotation, power: PART_RULES[part.type].power, piercing: false, targets: 1, visited: new Set() });
    }
  });
  let work = 0;
  while (queue.length && work++ < 512) {
    const ray = queue.shift();
    let col = ray.index % B.gridSize, row = Math.floor(ray.index / B.gridSize);
    const [dx, dy] = DIR[ray.direction];
    while (true) {
      const nextCol = col + dx, nextRow = row + dy;
      segments.push({ x1: col + 0.5, y1: row + 0.5, x2: nextCol + 0.5, y2: nextRow + 0.5, power: ray.power, piercing: ray.piercing });
      if (nextCol < 0 || nextRow < 0 || nextCol >= B.gridSize || nextRow >= B.gridSize) break;
      col = nextCol; row = nextRow;
      const index = row * B.gridSize + col, part = grid[index];
      if (!part) continue;
      const visit = `${index}:${ray.direction}`;
      if (ray.visited.has(visit)) { blocked.push(index); break; }
      const visited = new Set(ray.visited); visited.add(visit);
      const family = PARTS[part.type].base || part.type, rule = PART_RULES[part.type];
      if (family === 'reactor') { blocked.push(index); break; }
      active.add(index);
      if (family === 'gun') {
        const existing = guns.get(index);
        const gun = { index, power: Math.min(B.powerCap, (existing?.power || 0) + ray.power * rule.multiplier), piercing: ray.piercing || existing?.piercing || false };
        if (ray.targets > 2 || existing?.targets > 2) gun.targets = Math.max(ray.targets, existing?.targets || 1);
        guns.set(index, gun);
        break;
      }
      const next = { index, power: Math.min(B.powerCap, ray.power * (rule.multiplier || 1)), piercing: ray.piercing || !!rule.targets, targets: Math.max(ray.targets, rule.targets || 1), visited };
      if (family === 'mirror') {
        next.direction = (part.rotation % 2 ? [3, 2, 1, 0] : [1, 0, 3, 2])[ray.direction];
        queue.push(next);
      } else if (family === 'splitter') {
        queue.push({ ...next, power: ray.power * rule.fraction, direction: mod(ray.direction + 1) });
        queue.push({ ...next, power: ray.power * rule.fraction, direction: mod(ray.direction + 3) });
        if (rule.forward) queue.push({ ...next, power: ray.power * rule.fraction, direction: ray.direction });
      } else {
        queue.push({ ...next, direction: ray.direction });
      }
      break;
    }
  }
  return { segments, guns: [...guns.values()], active, blocked: [...new Set(blocked)] };
}

export function createState(known = []) {
  const grid = Array(25).fill(null);
  grid[22] = { type: 'reactor', rotation: 0 };
  grid[17] = { type: 'amplifier', rotation: 0 };
  grid[2] = { type: 'gun', rotation: 0 };
  return {
    status: 'ready', paused: false, elapsed: 0, hull: B.hull,
    grid, inventory: { mirror: 2, gun: 1, amplifier: 2, splitter: 0, lens: 0, reactor: 0 },
    cash: B.startingCash, shield: B.shield, shieldCooldown: 0, forged: 0,
    forge: { slots: [null, null], job: null }, notices: [],
    discovered: new Set(['reactor', 'amplifier', 'gun', 'mirror', ...known.filter(type => PARTS[type])]),
    discoveries: [], wave: 0, spawned: 0, spawnIn: 2, rest: 0,
    enemies: [], drops: [], shots: [], bursts: [], cooldowns: {},
    circuit: traceCircuit(grid), serial: 0, kills: 0, salvaged: 0,
    heldDrop: null, revision: 0, submarine: { ...B.submarine, hitFlash: 0, shieldFlash: 0 },
  };
}

export function startDive(state) { if (state.status === 'ready') state.status = 'running'; }

export function rebuild(state) { state.circuit = traceCircuit(state.grid); state.revision++; }

export function rotatePart(state, index) {
  const part = state.grid[index];
  if (!part || !PARTS[part.type].rotatable || state.status === 'won' || state.status === 'lost') return false;
  part.rotation = mod(part.rotation + 1); rebuild(state); return true;
}

function acquire(state, type) {
  if (!state.discovered.has(type)) { state.discovered.add(type); state.discoveries.push(type); }
}

export function sourcePart(state, source) {
  if (source.kind === 'forge') return !state.forge.job ? state.forge.slots[source.index] || null : null;
  if (source.kind === 'grid') return state.grid[source.index] || null;
  if (source.kind === 'storage') return state.inventory[source.type] > 0 ? { type: source.type, rotation: 0 } : null;
  if (source.kind === 'drop') {
    const drop = state.drops.find(item => item.id === source.id);
    return drop ? { type: drop.type, rotation: 0 } : null;
  }
  return null;
}

export function forgeMatches(state) {
  const ingredients = state.forge.slots.filter(Boolean);
  return !state.forge.job && ingredients.length === 1 ? compatibleTypes(ingredients[0].type) : new Set();
}

export function forgeRecipe(state) {
  const [a, b] = state.forge.slots;
  return a && b ? findRecipe(a.type, b.type) : null;
}

export function canAddToForge(state, type, index = state.forge.slots.findIndex(p => !p)) {
  if (state.forge.job || ![0, 1].includes(index) || state.forge.slots[index]) return false;
  const other = state.forge.slots[1 - index];
  return other ? !!findRecipe(type, other.type) : RECIPES.some(r => r.ingredients.includes(type));
}

export function startForge(state) {
  const recipe = forgeRecipe(state);
  if (state.status !== 'running' || state.paused || state.forge.job || !recipe || state.cash < recipe.cost) return false;
  state.cash -= recipe.cost;
  state.forge.job = { ...recipe, remaining: recipe.seconds };
  state.revision++; return true;
}

function advanceForge(state, dt) {
  const job = state.forge.job; if (!job) return;
  job.remaining = Math.max(0, job.remaining - dt);
  if (job.remaining > 0) return;
  state.inventory[job.output] = (state.inventory[job.output] || 0) + 1;
  acquire(state, job.output); state.forged++;
  state.notices.push(`${PARTS[job.output].name} forged · added to hold`);
  state.forge = { slots: [null, null], job: null }; state.revision++;
}

// Validate first, then commit. Invalid/cancelled gestures never consume anything.
export function movePart(state, source, target) {
  if (state.status === 'won' || state.status === 'lost') return false;
  const part = sourcePart(state, source);
  if (!part) return false;
  if (target.kind === 'grid' && (!Number.isInteger(target.index) || target.index < 0 || target.index >= 25 || state.grid[target.index])) return false;
  if (!['grid', 'storage', 'forge'].includes(target.kind)) return false;
  const forgeIndex = target.index ?? state.forge.slots.findIndex(p => !p);
  if (target.kind === 'forge' && (source.kind === 'forge' || !canAddToForge(state, part.type, forgeIndex))) return false;
  if (source.kind === 'storage' && target.kind === 'storage') return false;
  if (source.kind === 'grid') state.grid[source.index] = null;
  if (source.kind === 'storage') state.inventory[part.type]--;
  if (source.kind === 'forge') state.forge.slots[source.index] = null;
  if (source.kind === 'drop') {
    state.drops = state.drops.filter(item => item.id !== source.id);
    state.salvaged++;
    acquire(state, part.type);
  }
  if (target.kind === 'storage') state.inventory[part.type] = (state.inventory[part.type] || 0) + 1;
  else if (target.kind === 'forge') state.forge.slots[forgeIndex] = { ...part };
  else state.grid[target.index] = { ...part };
  state.heldDrop = null;
  rebuild(state); return true;
}

export function spawnDrop(state, type, x = 0.68, y = 0.4) {
  const landingSlots = [0.72, 0.50, 0.86, 0.33, 0.16];
  const free = landingSlots.find(slot => !state.drops.some(d => Math.abs(d.x - slot) < 0.09));
  const drop = { id: ++state.serial, type, x: clamp(free ?? x, 0.10, 0.9), y, fall: 0, life: B.lootLife, landed: false };
  state.drops.push(drop); return drop;
}

function killEnemy(state, enemy) {
  if (enemy.dead) return;
  enemy.dead = true;
  state.bursts.push({ id: ++state.serial, x: enemy.x, y: enemy.y, life: 0.5, kind: 'enemy' });
  const reward = enemy.bounty || 5;
  state.cash += reward;
  state.bursts.push({ id: ++state.serial, x: enemy.x, y: enemy.y, life: 1, kind: 'cash', amount: reward });
  if (state.kills % B.partDropEvery === 0) spawnDrop(state, B.lootOrder[Math.floor(state.kills / B.partDropEvery) % B.lootOrder.length], enemy.x, enemy.y);
  state.kills++;
}

function step(state, dt) {
  state.elapsed += dt;
  advanceForge(state, dt);
  state.shieldCooldown = Math.max(0, state.shieldCooldown - dt);
  if (!state.shieldCooldown) state.shield = Math.min(B.shield, state.shield + B.shieldRegen * dt);
  for (const actor of [state.submarine, ...state.enemies]) {
    actor.hitFlash = Math.max(0, (actor.hitFlash || 0) - dt);
    actor.shieldFlash = Math.max(0, (actor.shieldFlash || 0) - dt);
  }
  state.submarine.y = B.submarine.y + Math.sin(state.elapsed * 0.35) * 0.025;
  for (const shot of state.shots) shot.life -= dt;
  for (const burst of state.bursts) burst.life -= dt;
  state.shots = state.shots.filter(s => s.life > 0);
  state.bursts = state.bursts.filter(s => s.life > 0);
  for (const drop of state.drops) {
    if (drop.id === state.heldDrop) continue;
    if (!drop.landed) {
      drop.fall += dt * 0.55; drop.y += drop.fall * dt;
      if (drop.y >= B.floor) { drop.y = B.floor; drop.landed = true; }
    } else { drop.life -= dt; drop.x = Math.max(0.09, drop.x - dt * 0.002); }
  }
  state.drops = state.drops.filter(d => d.life > 0 || d.id === state.heldDrop);

  const wave = B.waves[state.wave];
  if (state.rest > 0) {
    state.rest -= dt;
    if (state.rest <= 0) { state.wave++; state.spawned = 0; state.spawnIn = 0.5; }
  } else if (state.spawned < wave.enemies.length) {
    state.spawnIn -= dt;
    if (state.spawnIn <= 0) {
      const type = wave.enemies[state.spawned], stats = B.enemies[type];
      state.enemies.push({ id: ++state.serial, type, ...stats, shield: stats.shield || 0, maxShield: stats.shield || 0, hitFlash: 0, shieldFlash: 0, maxHp: stats.hp, x: 1.04, y: [0.34, 0.60, 0.45, 0.26, 0.66][state.spawned % 5], attackIn: stats.attackInterval });
      state.spawned++; state.spawnIn += wave.interval;
    }
  }

  for (const enemy of state.enemies) {
    if (enemy.x > state.submarine.x + 0.14) enemy.x -= enemy.speed * dt;
    else {
      enemy.attackIn -= dt;
      if (enemy.attackIn <= 0) {
        const absorbed = Math.min(state.shield, enemy.damage);
        state.shield -= absorbed; state.shieldCooldown = B.shieldDelay;
        const hullDamage = enemy.damage - absorbed;
        state.hull = Math.max(0, state.hull - hullDamage);
        if (absorbed) state.submarine.shieldFlash = 0.45;
        if (hullDamage) state.submarine.hitFlash = 0.35;
        enemy.attackIn += enemy.attackInterval;
        state.shots.push({ id: ++state.serial, from: { x: enemy.x, y: enemy.y }, to: { ...state.submarine }, life: 0.22, hostile: true });
        state.bursts.push({ id: ++state.serial, x: state.submarine.x, y: state.submarine.y, life: 0.6, kind: hullDamage ? 'hull' : 'shield', amount: enemy.damage });
      }
    }
  }

  for (const gun of state.circuit.guns) {
    state.cooldowns[gun.index] = (state.cooldowns[gun.index] || 0) - dt;
    if (state.cooldowns[gun.index] > 0) continue;
    const targets = state.enemies.filter(e => !e.dead && e.x < 0.99).sort((a, b) => a.x - b.x);
    const target = targets[0];
    if (!target) continue;
    const hits = gun.piercing ? targets.slice(0, gun.targets || 2) : [target];
    for (const enemy of hits) {
      const damage = Math.max(1, gun.power - (gun.piercing ? 0 : enemy.armor));
      const absorbed = Math.min(enemy.shield || 0, damage);
      enemy.shield = (enemy.shield || 0) - absorbed;
      enemy.hp -= damage - absorbed;
      if (absorbed) enemy.shieldFlash = 0.45;
      if (damage > absorbed) enemy.hitFlash = 0.25;
      state.bursts.push({ id: ++state.serial, x: enemy.x, y: enemy.y, life: 0.6, kind: absorbed ? 'shield' : 'hit', amount: damage });
      state.shots.push({ id: ++state.serial, from: { x: state.submarine.x + 0.09, y: state.submarine.y - 0.02 + (gun.index % 2) * 0.055 }, to: { x: enemy.x, y: enemy.y }, life: 0.20, power: gun.power, piercing: gun.piercing });
      if (enemy.hp <= 0) killEnemy(state, enemy);
    }
    state.cooldowns[gun.index] = B.shotInterval;
  }
  state.enemies = state.enemies.filter(e => !e.dead);
  if (state.hull <= 0) { state.status = 'lost'; return; }
  if (state.rest <= 0 && state.spawned === wave.enemies.length && !state.enemies.length) {
    if (state.wave === B.waves.length - 1) state.status = 'won';
    else state.rest = B.intermission;
  }
}

export function tick(state, seconds) {
  if (state.status !== 'running' || state.paused || seconds <= 0 || !Number.isFinite(seconds)) return;
  let remaining = Math.min(seconds, 300);
  while (remaining > 0 && state.status === 'running') {
    const dt = Math.min(0.05, remaining); step(state, dt); remaining -= dt;
  }
}
