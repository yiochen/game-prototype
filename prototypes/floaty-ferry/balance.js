export const BALANCE = { duration: 100, capacity: 3, speed: 100, dockTime: 0.8, patience: 38, spawnEvery: 3.8, initialRoutes: 4, maxRoutes: 5, unlockAt: 8, step: 1 / 60 };
export const ISLANDS = [
  { id: 0, name: 'Pebble', x: 190, y: 248, color: 0xffc75b, shape: 'star' },
  { id: 1, name: 'Rosy', x: 92, y: 105, color: 0xf390a0, shape: 'heart' },
  { id: 2, name: 'Mint', x: 306, y: 150, color: 0x71cbb2, shape: 'leaf' },
  { id: 3, name: 'Lavender', x: 91, y: 363, color: 0xaca1de, shape: 'moon' },
  { id: 4, name: 'Tangerine', x: 295, y: 397, color: 0xf4aa68, shape: 'sun' },
  { id: 5, name: 'Bluebell', x: 218, y: 65, color: 0x81b9e1, shape: 'diamond' },
];
export const REQUESTS = [[0, 1], [0, 2], [1, 3], [2, 4], [3, 0], [4, 1], [0, 5], [5, 2], [2, 3], [1, 4], [3, 5], [4, 2]];
