import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { restaurantShowcase } from '../wireframe/restaurant-showcase-data.js';
import { underwaterShowcase } from '../wireframe/underwater-showcase-data.js';
import { placementAtTime, groundRoot, resolveSupportSocket } from '../wireframe/sprite-layout.js';
const library = JSON.parse(readFileSync(new URL('../assets/production/library.json', import.meta.url), 'utf8'));
const byId = new Map(library.objects.map(object => [object.id, object]));
const scenes = [restaurantShowcase, underwaterShowcase];
const divides = (whole, part) => Math.abs(whole / part - Math.round(whole / part)) < 1e-8;

test('aisle walking compensates native planted-foot travel in every projected facing', () => {
  const walker = restaurantShowcase.placements.find(placement => placement.id === 'june-in-aisle');
  const object = byId.get(walker.object);
  const audit = JSON.parse(readFileSync(new URL('../review/33/character-rollout/character-audit.json', import.meta.url))).assets[walker.object];
  const camera = JSON.parse(readFileSync(new URL(`../assets/production/${object.source.camera}`, import.meta.url)));
  const stride = audit.walkWorldTravelPerCycle;
  const calibration = camera.calibration;
  const basis = name => calibration[name] || calibration[`native${name[0].toUpperCase()}${name.slice(1)}`].map((value, axis) => value - calibration.nativeRoot[axis]);
  const projected = [basis('unitX')[0], basis('unitDepth')[1]].map(value => value / camera.captureScale);
  assert.ok(Math.abs(stride - .225) < 1e-8, 'Selected C125 native stance cycle is the route calibration authority');
  for (const direction of ['N', 'E', 'S', 'W']) {
    const axis = ['N', 'S'].includes(direction) ? 1 : 0;
    assert.ok(Math.abs(object.locomotion.projectedWalkTravelPerCycle[direction] * 128 - stride * projected[axis]) < .0001, 'Published stride must match the float32-measured camera within0.0001 logical pixels per cycle');
  }
  assert.ok(projected[1] < projected[0] * .6, 'This regression must exercise ordinary35° depth foreshortening');
  assert.equal(walker.motion.segmentDurations.reduce((sum, duration) => sum + duration, 0), 16);
  const unphased = { ...walker, motion: { ...walker.motion, phase: 0 } };
  const dt = 1 / 12;
  let start = 0;
  for (let index = 0; index < walker.motion.segmentDurations.length; index++) {
    const a = groundRoot(placementAtTime(unphased, start + .125, object), object);
    const b = groundRoot(placementAtTime(unphased, start + .125 + dt, object), object);
    const from = walker.motion.path[index], to = walker.motion.path[index + 1];
    for (const axis of [0, 1]) {
      const nativePlantedFootTravel = -Math.sign(to[axis] - from[axis]) * stride * projected[axis] * dt;
      assert.ok(Math.abs(b[axis] - a[axis] + nativePlantedFootTravel) < .00001, `Segment${index}, axis${axis}: sprite root must cancel the native camera's planted-foot motion`);
    }
    start += walker.motion.segmentDurations[index];
  }
});

test('the full C125 turning envelope stays in the clear aisle away from border, chefs and conveyor', () => {
  const walker = restaurantShowcase.placements.find(placement => placement.id === 'june-in-aisle');
  const audit = JSON.parse(readFileSync(new URL('../review/33/character-rollout/character-audit.json', import.meta.url))).assets[walker.object];
  const halfWidth = audit.maximumWidthCells / 2, halfDepth = audit.maximumDepthCells / 2;
  const chefs = restaurantShowcase.placements.filter(placement => byId.get(placement.object).family === 'W05');
  for (let frame = 0; frame <= 16 * 12; frame++) {
    const pose = placementAtTime(walker, frame / 12, byId.get(walker.object));
    const [x, y] = groundRoot(pose, byId.get(walker.object)).map(value => value / 128);
    assert.ok(x - halfWidth >= 1 && x + halfWidth < 3, 'The complete turning width stays between the border column and conveyor');
    for (const chef of chefs) assert.ok(x + halfWidth <= chef.x || x - halfWidth >= chef.x + 1 || y + halfDepth <= chef.y || y - halfDepth >= chef.y + 1, 'The complete native turning footprint does not overlap a chef tile');
  }
});

test('restaurant plates reference the active conveyor deck socket through the complete route', () => {
  const deck = byId.get('belt-straight-e').sockets.S.deck;
  const plates = restaurantShowcase.placements.filter(placement => placement.object.startsWith('dish-'));
  assert.equal(plates.length, 6);
  for (const plate of plates) {
    assert.equal(plate.offset, undefined, 'No fixed100%/70% recipe may detach plates during native publication');
    assert.deepEqual(plate.supportSocket, { object: 'belt-straight-e', socket: 'deck', direction: 'S' });
    const resolved = resolveSupportSocket(plate, byId);
    assert.deepEqual(resolved.supportOffset, deck);
    for (const seconds of [0, 12, 24, 36, 48]) {
      const at = placementAtTime(resolved, seconds, byId.get(plate.object));
      const plain = { ...at, supportOffset: [0, 0] };
      const supportedRoot = groundRoot(at, byId.get(plate.object));
      const ground = groundRoot(plain, byId.get(plate.object));
      assert.ok(supportedRoot.every((value, axis) => Math.abs(value - ground[axis] - deck[axis]) < 1e-8));
    }
  }
});

for (const scene of scenes) {
  test(`${scene.id}: complete scene and inspection links reference real catalog objects and clips`, () => {
    assert.ok(scene.title && scene.description);
    assert.ok(scene.gridSize.length === 2 && scene.gridSize.every(value => Number.isFinite(value) && value > 0));
    assert.equal(byId.get(scene.floorId)?.kind, 'floor');
    const used = new Set([scene.floorId]);
    const ids = new Set();
    for (const placement of scene.placements) {
      assert.ok(placement.id && !ids.has(placement.id), `Stable unique placement ID: ${placement.id}`);
      ids.add(placement.id);
      const object = byId.get(placement.object);
      assert.ok(object, `${placement.object} is a real native catalog object`);
      used.add(placement.object);
      assert.ok(Number.isFinite(placement.x) && Number.isFinite(placement.y));
      if (placement.clip) assert.ok(object.clips.some(clip => clip.id === placement.clip), `${placement.object}/${placement.clip} must not silently fall back to another state`);
      const clip = object.clips.find(candidate => candidate.id === placement.clip) || object.clips[0];
      const directions = placement.motion?.faceTravel ? ['N', 'E', 'S', 'W'] : [placement.direction || 'S'];
      for (const direction of directions) assert.ok(clip.directions[direction]?.image, `${placement.id}: exact captured ${direction} facing must be available`);
      if (placement.motion) assert.ok(placement.motion.path.length >= 2 && placement.motion.path.every(point => point.length === 2 && point.every(Number.isFinite)), `${placement.id}: staged path positions must be finite`);
    }
    assert.ok(scene.highlights.length);
    for (const highlight of scene.highlights) {
      assert.ok(highlight.title && highlight.description && highlight.objectIds.length);
      for (const id of highlight.objectIds) assert.ok(used.has(id), `${id}: inspection link must describe an object used in this scene`);
    }
  });

  test(`${scene.id}: scene clock closes every staged path and looping native animation`, () => {
    assert.ok(Number.isFinite(scene.duration) && scene.duration > 0);
    assert.ok(Number.isInteger(scene.duration * 12), 'Scene clock must end on a native 12fps frame boundary');
    for (const placement of scene.placements) {
      const object = byId.get(placement.object);
      const clip = object.clips.find(candidate => candidate.id === placement.clip) || object.clips[0];
      assert.equal(clip.fps, 12);
      if (clip.loop !== false && clip.frames > 1) assert.ok(divides(scene.duration, clip.frames / clip.fps), `${placement.id}: native loop must close at scene wrap`);
      if (!placement.motion || placement.motion.loop === false) continue;
      assert.ok(Number.isFinite(placement.motion.duration) && placement.motion.duration > 0);
      assert.ok(divides(scene.duration, placement.motion.duration), `${placement.id}: a ${placement.motion.duration}s route must not be cut short by the ${scene.duration}s scene clock`);
      const start = placementAtTime(placement, 0, object);
      const end = placementAtTime(placement, scene.duration, object);
      const a = groundRoot(start, object), b = groundRoot(end, object);
      assert.ok(a.every((value, index) => Math.abs(value - b[index]) < 1e-5), `${placement.id}: ground root must close after the complete scene cycle`);
      assert.equal(start.direction || 'S', end.direction || 'S');
    }
  });
}
