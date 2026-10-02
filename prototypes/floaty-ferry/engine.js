import { BALANCE as B, ISLANDS, REQUESTS } from './balance.js';

export function createGame(tutorial = false, day = 1) {
  const state = { tutorial, day, status: 'playing', time: 0, accumulator: 0, spawnClock: 0, spawnIndex: 0, nextDuck: 0, nextRoute: 0, delivered: 0, splashes: 0, maxRoutes: B.initialRoutes, islands: ISLANDS.map(i => ({ ...i, ducks: [] })), routes: [], events: [], lesson: 0 };
  addDuck(state, 0, 1); if (!tutorial) addDuck(state, 0, 2);
  return state;
}
export function connect(state, a, b) {
  if (state.status !== 'playing' || !Number.isInteger(a) || !Number.isInteger(b) || a === b || !state.islands[a] || !state.islands[b] || state.routes.length >= state.maxRoutes || state.routes.some(r => r.a === a && r.b === b || r.a === b && r.b === a)) return false;
  if (state.tutorial && (state.lesson === 0 && !([a, b].includes(0) && [a, b].includes(1)) || state.lesson === 1 || state.lesson === 2 && !([a, b].includes(0) && [a, b].includes(2)))) return false;
  state.routes.push({ id: state.nextRoute++, a, b, from: a, to: b, progress: 0, dock: B.dockTime, passengers: [], departed: false });
  state.events.push({ type: 'connect', a, b });
  if (state.tutorial) state.lesson = state.lesson === 0 ? 1 : 3;
  return true;
}
export function disconnect(state, id) {
  if (state.status !== 'playing' || state.tutorial) return false;
  const index = state.routes.findIndex(r => r.id === id); if (index < 0) return false;
  const route = state.routes[index];
  state.islands[route.from].ducks.push(...route.passengers);
  state.routes.splice(index, 1); state.events.push({ type: 'disconnect' }); return true;
}
export function nextHop(state, from, to) {
  if (from === to) return null;
  const visited = new Set([from]), queue = [{ node: from, first: null }];
  while (queue.length) {
    const { node, first } = queue.shift();
    for (const route of state.routes) {
      const neighbor = route.a === node ? route.b : route.b === node ? route.a : null;
      if (neighbor === null || visited.has(neighbor)) continue;
      const hop = first ?? neighbor; if (neighbor === to) return hop;
      visited.add(neighbor); queue.push({ node: neighbor, first: hop });
    }
  }
  return null;
}
export function addDuck(state, from, destination) {
  const duck = { id: state.nextDuck++, destination, age: 0 };
  state.islands[from].ducks.push(duck); state.events.push({ type: 'spawn', island: from, destination });
  return duck;
}
function board(state, route) {
  const island = state.islands[route.from];
  const leaving = island.ducks.filter(d => nextHop(state, route.from, d.destination) === route.to).slice(0, B.capacity - route.passengers.length);
  route.passengers.push(...leaving); island.ducks = island.ducks.filter(d => !leaving.includes(d));
  route.departed = true;
}
function arrive(state, route) {
  const island = state.islands[route.to];
  for (const duck of route.passengers) {
    if (duck.destination === island.id) {
      state.delivered++; state.events.push({ type: 'deliver', island: island.id, duck: duck.id });
    } else island.ducks.push(duck);
  }
  route.passengers = [];
  [route.from, route.to] = [route.to, route.from]; route.progress = 0; route.dock = B.dockTime; route.departed = false;
  if (state.delivered >= B.unlockAt && state.maxRoutes < B.maxRoutes) { state.maxRoutes = B.maxRoutes; state.events.push({ type: 'upgrade' }); }
  if (state.tutorial && state.lesson === 1 && state.delivered >= 1) { state.lesson = 2; addDuck(state, 0, 2); }
  else if (state.tutorial && state.lesson === 3 && state.delivered >= 2) { state.lesson = 4; addDuck(state, 1, 2); }
  else if (state.tutorial && state.lesson === 4 && state.delivered >= 3) { state.lesson = 5; state.status = 'finished'; state.events.push({ type: 'finish' }); }
}
function step(state, dt) {
  state.time += dt;
  if (!state.tutorial) {
    state.spawnClock += dt;
    while (state.spawnClock >= B.spawnEvery) {
      state.spawnClock -= B.spawnEvery;
      const [a, b] = REQUESTS[(state.spawnIndex++ + state.day - 1) % REQUESTS.length]; addDuck(state, a, b);
    }
    for (const island of state.islands) {
      for (const duck of island.ducks) duck.age += dt;
      const leaving = island.ducks.filter(d => d.age > B.patience);
      if (leaving.length) { state.splashes += leaving.length; state.events.push({ type: 'splash', island: island.id }); island.ducks = island.ducks.filter(d => d.age <= B.patience); }
    }
  }
  for (const route of state.routes) {
    if (route.dock > 0) { route.dock -= dt; if (route.dock <= 0) board(state, route); continue; }
    const a = state.islands[route.from], b = state.islands[route.to];
    route.progress += B.speed * dt / Math.hypot(a.x - b.x, a.y - b.y);
    if (route.progress >= 1) arrive(state, route);
  }
  if (!state.tutorial && state.time >= B.duration) { state.time = B.duration; state.status = 'finished'; state.events.push({ type: 'finish' }); }
}
export function tick(state, dt) {
  if (state.status !== 'playing' || !Number.isFinite(dt) || dt <= 0) return;
  state.accumulator += Math.min(dt, 120);
  while (state.accumulator + 1e-10 >= B.step && state.status === 'playing') { state.accumulator -= B.step; step(state, B.step); }
}
export function boatPosition(state, route) {
  const a = state.islands[route.from], b = state.islands[route.to];
  return { x: a.x + (b.x - a.x) * route.progress, y: a.y + (b.y - a.y) * route.progress };
}
export function rating(state) { return state.delivered >= 24 ? 3 : state.delivered >= 12 ? 2 : 1; }
