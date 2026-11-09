import {tracks, fixtures} from './balance.js';

export const storageKey = 'sushi-loop-issue28-workshop-review-v1';
const byId = Object.fromEntries(tracks.map(t => [t.id, t]));

export function fixture(name = 'workshop') {
  const f = fixtures[name] || fixtures.workshop;
  return {salvage: f.salvage, levels: {...f.levels}, spent: [], seen: {}};
}

export const maxLevel = id => byId[id].levels.length;
export const statAt = (id, level) => byId[id].levels[Math.min(level, maxLevel(id)) - 1];
export const nextCost = (m, id) => m.levels[id] >= maxLevel(id) ? null : byId[id].costs[m.levels[id] - 1];
// Every part is always fitted; its look tier (1–3) changes at each milestone level.
export const tierOf = (id, level) => 1 + byId[id].looks.filter(l => level >= l).length;
export const canUpgrade = (m, id) => nextCost(m, id) !== null && m.salvage >= nextCost(m, id);

// Pure command boundary. Each upgrade carries a one-time token, so a repeated
// tap, a replayed event or a reload with the same token cannot pay twice.
export function command(m, action) {
  if (action.type !== 'upgrade' || !byId[action.id]) return m;
  if (!action.token || m.spent.includes(action.token)) return m;
  const cost = nextCost(m, action.id);
  if (cost === null || m.salvage < cost) return m;
  const level = m.levels[action.id] + 1;
  const crossed = byId[action.id].looks.includes(level);
  return {
    ...m,
    salvage: m.salvage - cost,
    levels: {...m.levels, [action.id]: level},
    spent: [...m.spent, action.token].slice(-40),
    seen: crossed ? {...m.seen, [action.id]: false} : m.seen,
  };
}

export function restore(storage, name) {
  try {
    const v = JSON.parse(storage.getItem(storageKey));
    if (v && typeof v.salvage === 'number' && v.levels && tracks.every(t => v.levels[t.id] >= 1 && v.levels[t.id] <= maxLevel(t.id))) return {spent: [], seen: {}, ...v};
  } catch {}
  return fixture(name);
}

// What an equivalent run gives with these levels (numbers the dive shows).
export function runProfile(levels, exp) {
  const hull = statAt('hull', levels.hull), strength = statAt('harpoon', levels.harpoon), reach = statAt('collector', levels.collector);
  return {
    hull,
    hitsSurvived: Math.ceil(hull / exp.impactDamage) - 1,
    reelSeconds: exp.resistance / (exp.resistanceDrainPerSecond * strength),
    reach,
    shield: statAt('shield', levels.shield),
    passage: statAt('passage', levels.passage),
    launch: statAt('launch', levels.launch),
  };
}
