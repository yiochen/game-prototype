import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { restaurantShowcase } from '../wireframe/restaurant-showcase-data.js';
import { underwaterShowcase } from '../wireframe/underwater-showcase-data.js';
import { placementAtTime, groundRoot } from '../wireframe/sprite-layout.js';
const library = JSON.parse(readFileSync(new URL('../assets/production/library.json', import.meta.url), 'utf8'));
const byId = new Map(library.objects.map(object => [object.id, object]));
const scenes = [restaurantShowcase, underwaterShowcase];
const divides = (whole, part) => Math.abs(whole / part - Math.round(whole / part)) < 1e-8;

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
