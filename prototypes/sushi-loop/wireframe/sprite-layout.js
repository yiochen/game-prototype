// Sprite registration is expressed in logical pixels, never inferred from alpha bounds.
export const DIRECTIONS = ['N', 'E', 'S', 'W'];
export const DIRECTION_NAMES = { N: 'North', E: 'East', S: 'South', W: 'West' };
const positive = (value, fallback) => Number.isFinite(Number(value)) && Number(value) > 0 ? Number(value) : fallback;
export function clipFor(object, id) {
  return object?.clips?.find(clip => clip.id === id) || object?.clips?.[0] || null;
}
export function spriteFrame(object, clip, direction, seconds = 0) {
  const entry = clip?.directions?.[direction];
  if (!entry?.image) return null;
  const frameSize = entry.frameSize || clip.frameSize || object.frameSize || [192, 320];
  const root = entry.root || clip.root || object.root || [96, 248];
  const sourceScale = positive(entry.sourceScale ?? clip.sourceScale ?? object.sourceScale, 1);
  const frames = Math.max(1, Math.floor(positive(entry.frames ?? clip.frames, 1)));
  const fps = positive(clip.fps, 12);
  const rawFrame = Math.max(0, Math.floor(Math.max(0, seconds) * fps + 1e-7));
  const frame = clip.loop === false ? Math.min(frames - 1, rawFrame) : rawFrame % frames;
  const offset = Math.max(0, Math.floor(Number(entry.offset) || 0));
  const columns = Math.max(1, Math.floor(positive(entry.columns, frames)));
  const rows = Math.max(1, Math.floor(positive(entry.rows, Math.ceil((frames + offset) / columns))));
  const [width, height] = frameSize;
  const rect = entry.rects?.[frame] || [(offset + frame) % columns * width * sourceScale, Math.floor((offset + frame) / columns) * height * sourceScale, width * sourceScale, height * sourceScale];
  return { image: entry.image, frame, frames, frameSize, root, rect, atlasSize: entry.atlasSize || [width * sourceScale * columns, height * sourceScale * rows] };
}
export function sceneBounds(placements, objects, cellSize = 128, gridSize = [3, 3]) {
  let minX = 0, minY = 0, maxX = gridSize[0] * cellSize, maxY = gridSize[1] * cellSize;
  for (const placement of placements) {
    const object = objects.find(candidate => candidate.id === placement.object);
    if (!object) continue;
    const clip = clipFor(object, placement.clip);
    const frame = spriteFrame(object, clip, placement.direction || 'S', 0);
    const [width, height] = frame?.frameSize || object.frameSize || [192, 320];
    const [rootX, rootY] = frame?.root || object.root || [96, 248];
    const [x, y] = groundRoot(placement, object, cellSize);
    minX = Math.min(minX, x - rootX); minY = Math.min(minY, y - rootY);
    maxX = Math.max(maxX, x - rootX + width); maxY = Math.max(maxY, y - rootY + height);
  }
  const pad = cellSize * .2;
  return [minX - pad, minY - pad, maxX - minX + pad * 2, maxY - minY + pad * 2];
}
export function orderPlacements(placements, objects) {
  return placements.map((placement, index) => ({ ...placement, _index: index })).sort((a, b) => {
    const get = placement => objects.find(object => object.id === placement.object);
    const pass = placement => {
      const object = get(placement) || {};
      const value = placement.renderPass || object.renderPass || (object.kind === 'floor' ? 'background' : 'world');
      return value === 'background' ? 0 : ['foreground', 'overhead', 'overlay'].includes(value) ? 2 : 1;
    };
    const rank = placement => placement.layer ?? get(placement)?.layer ?? (get(placement)?.kind === 'floor' ? 0 : get(placement)?.kind === 'belt' ? 1 : 2);
    const depth = placement => {
      const object = get(placement) || {};
      const footprint = footprintFor(object, placement.direction);
      const rootCell = object.directionRootCells?.[placement.direction || 'S'] || object.rootCell || [footprint[0] / 2, footprint[1] / 2];
      // A support-height offset changes projection, not the object's ground depth.
      return placement.y + rootCell[1];
    };
    return pass(a) - pass(b) || depth(a) - depth(b) || rank(a) - rank(b) || a._index - b._index;
  });
}
export function repeatedPlacements(object, direction = 'S', clip) {
  const footprint = footprintFor(object, direction);
  return Array.from({ length: 9 }, (_, index) => ({ object: object.id, x: index % 3 * footprint[0], y: Math.floor(index / 3) * footprint[1], direction, clip }));
}
export function directionPlacements(object, clip) {
  const extent = Math.max(...DIRECTIONS.flatMap(direction => footprintFor(object, direction)));
  return DIRECTIONS.map((direction, index) => ({ object: object.id, direction, clip, x: index * (extent + 1), y: 0 }));
}

// A presentation path moves only its separate sprite; it is not belt/game simulation.
export function placementAtTime(placement, seconds = 0) {
  const motion = placement.motion;
  if (!motion?.path?.length || motion.path.length < 2) return placement;
  const points = motion.path;
  const segments = points.slice(1).map((point, index) => Math.hypot(point[0] - points[index][0], point[1] - points[index][1]));
  const distance = segments.reduce((sum, length) => sum + length, 0);
  if (!distance) return placement;
  const progress = Math.max(0, seconds) / positive(motion.duration, 4);
  let remaining = (motion.loop === false ? Math.min(1, progress) : progress % 1) * distance;
  for (let index = 0; index < segments.length; index++) {
    if (remaining <= segments[index] || index === segments.length - 1) {
      const t = segments[index] ? Math.min(1, remaining / segments[index]) : 0;
      const [x, y] = points[index], [nextX, nextY] = points[index + 1];
      return { ...placement, x: x + (nextX - x) * t, y: y + (nextY - y) * t };
    }
    remaining -= segments[index];
  }
  return placement;
}

export function reviewFrameCount(object, library = []) {
  const gcd = (a, b) => b ? gcd(b, a % b) : a;
  const loops = [], oneShots = [];
  const addClip = clip => {
    if (!clip) return;
    const counts = [clip.frames || 1, ...Object.values(clip.directions || {}).map(entry => entry.frames || clip.frames || 1)];
    (clip.loop === false ? oneShots : loops).push(...counts);
  };
  for (const clip of object.clips || []) addClip(clip);
  for (const interaction of object.interactions || []) for (const placement of interaction.placements || []) {
    const related = library.find(candidate => candidate.id === placement.object);
    if (related) addClip(clipFor(related, placement.clip));
    if (placement.motion) (placement.motion.loop === false ? oneShots : loops).push(Math.max(1, Math.round(positive(placement.motion.duration, 4) * 12)));
  }
  const period = loops.reduce((value, count) => value * Math.max(1, count) / gcd(value, Math.max(1, count)), 1);
  return period * Math.ceil(Math.max(1, ...oneShots) / period);
}

export function groundRoot(placement, object, cellSize = 128) {
  const footprint = footprintFor(object, placement.direction);
  const rootCell = object.directionRootCells?.[placement.direction || 'S'] || object.rootCell || [footprint[0] / 2, footprint[1] / 2];
  return [(placement.x + rootCell[0]) * cellSize + (placement.offset?.[0] || 0), (placement.y + rootCell[1]) * cellSize + (placement.offset?.[1] || 0)];
}

export function attachmentMarkers(object, clip, direction) {
  const entry = clip?.directions?.[direction];
  const sockets = entry?.sockets || object.sockets?.[direction] || object.sockets || {};
  const ports = entry?.ports || object.ports?.[direction] || object.ports || [];
  const socketEntries = Array.isArray(sockets) ? sockets.map((value, index) => [value.name || `socket ${index + 1}`, value.position || value]) : Object.entries(sockets).map(([name, value]) => [name, value.position || value]);
  const portEntries = Array.isArray(ports) ? ports.map((value, index) => [value.name || `port ${index + 1}`, value.position || value]) : Object.entries(ports).map(([name, value]) => [name, value.position || value]);
  return [...socketEntries.map(([name, position]) => ({ name, position, kind: 'socket' })), ...portEntries.map(([name, position]) => ({ name, position, kind: 'port' }))].filter(marker => Array.isArray(marker.position) && marker.position.length >= 2 && marker.position.slice(0, 2).every(value => Number.isFinite(value)));
}

export function footprintFor(object, direction = 'S') {
  return object.directionFootprints?.[direction] || object.footprint || [1, 1];
}
