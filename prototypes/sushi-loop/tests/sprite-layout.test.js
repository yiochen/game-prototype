import test from 'node:test';
import assert from 'node:assert/strict';
import { spriteFrame, sceneBounds, orderPlacements, repeatedPlacements, placementAtTime, reviewFrameCount, groundRoot, attachmentMarkers } from '../wireframe/sprite-layout.js';

const character = { id: 'chef', kind: 'character', frameSize: [192, 320], root: [96, 248], sourceScale: 4, clips: [{ id: 'work', fps: 12, frames: 12, directions: { N: { image: 'chef/work-N.png', columns: 6, rows: 2 }, S: { image: 'chef/work-S.png', columns: 6, rows: 2 } } }] };
const clip = character.clips[0];

test('native 4x atlas selection preserves the authored logical frame and ground root across poses', () => {
  const first = spriteFrame(character, clip, 'N', 0);
  const seventh = spriteFrame(character, clip, 'N', .5);
  const south = spriteFrame(character, clip, 'S', .5);
  assert.deepEqual(first.rect, [0, 0, 768, 1280]);
  assert.deepEqual(seventh.rect, [0, 1280, 768, 1280]);
  assert.deepEqual(seventh.atlasSize, [4608, 2560]);
  assert.deepEqual(seventh.frameSize, first.frameSize);
  assert.deepEqual(south.root, first.root);
  assert.equal(spriteFrame(character, clip, 'E', 0), null);
});

test('static four-direction sheet offsets are separate atlas panels, without rotating a source sprite', () => {
  const staticClip = { frames: 1, directions: { W: { image: 'stool.png', columns: 4, rows: 1, offset: 3 } } };
  assert.deepEqual(spriteFrame(character, staticClip, 'W', 100).rect, [2304, 0, 768, 1280]);
  assert.equal(spriteFrame(character, staticClip, 'W', 100).frame, 0);
});

test('loops wrap at 12 fps; one-shot exports retain the final pose when the shared clock continues', () => {
  assert.equal(spriteFrame(character, clip, 'N', 1).frame, 0);
  assert.equal(spriteFrame(character, { ...clip, loop: false }, 'N', 8).frame, 11);
  assert.equal(spriteFrame(character, clip, 'N', -1).frame, 0);
});

test('an explicit irregular atlas layout uses its recorded source rectangles', () => {
  const layout = { frames: 2, directions: { N: { image: 'raw.png', atlasSize: [2400, 2400], rects: [[8, 16, 768, 1280], [800, 20, 768, 1280]] } } };
  const frame = spriteFrame(character, layout, 'N', 1 / 12);
  assert.deepEqual(frame.rect, [800, 20, 768, 1280]);
  assert.deepEqual(frame.atlasSize, [2400, 2400]);
});

test('3x3 repetition uses declared multi-cell footprint spacing with no fitting', () => {
  const placements = repeatedPlacements({ id: 'hut', footprint: [2, 3] }, 'W', 'idle');
  assert.equal(placements.length, 9);
  assert.deepEqual(placements[4], { object: 'hut', x: 2, y: 3, direction: 'W', clip: 'idle' });
  assert.deepEqual([placements[8].x, placements[8].y], [4, 6]);
});

test('scene bounds retain upward artwork and attachment offsets instead of clipping to the tile', () => {
  const normal = sceneBounds([{ object: 'chef', x: 0, y: 0 }], [character]);
  const lifted = sceneBounds([{ object: 'chef', x: 0, y: 0, offset: [0, -50] }], [character]);
  assert.ok(normal[1] < -180);
  assert.equal(lifted[1], normal[1] - 50);
  assert.equal(lifted[3], normal[3] + 50);
});

test('all decks precede food and people; foreground keeps ground-depth ordering', () => {
  const objects = [character, { id: 'belt', kind: 'belt' }, { id: 'dish', kind: 'prop' }, { id: 'floor', kind: 'floor' }];
  const placed = [{ object: 'dish', x: 1, y: 0 }, { object: 'belt', x: 1, y: 3 }, { object: 'chef', x: 1, y: 1 }, { object: 'floor', x: 0, y: 2 }];
  assert.deepEqual(orderPlacements(placed, objects).map(value => value.object), ['floor', 'belt', 'dish', 'chef']);
  assert.deepEqual(placed.map(value => value.object), ['dish', 'belt', 'chef', 'floor']);
});

test('a separate plate follows a belt presentation path at constant distance speed, and scrubs exactly', () => {
  const plate = { object: 'dish', x: 0, y: 0, motion: { path: [[0, 0], [2, 0], [2, 1]], duration: 3 } };
  assert.deepEqual([placementAtTime(plate, 1).x, placementAtTime(plate, 1).y], [1, 0]);
  assert.deepEqual([placementAtTime(plate, 2.5).x, placementAtTime(plate, 2.5).y], [2, .5]);
  assert.deepEqual([placementAtTime(plate, 3).x, placementAtTime(plate, 3).y], [0, 0]);
  const once = { ...plate, motion: { ...plate.motion, loop: false } };
  assert.deepEqual([placementAtTime(once, 9).x, placementAtTime(once, 9).y], [2, 1]);
});


test('the shared review clock closes every loop even when clip durations differ', () => {
  const object = { clips: [{ frames: 12 }, { frames: 18 }, { frames: 1 }], interactions: [] };
  assert.equal(reviewFrameCount(object), 36);
  assert.equal(reviewFrameCount({ clips: [{ frames: 12 }, { frames: 25, loop: false }] }), 36);
  assert.equal(reviewFrameCount({ clips: [], interactions: [{ placements: [{ motion: { duration: 4 } }] }] }), 48);
});


test('multi-cell ground roots center the complete footprint and retain explicit irregular anchors', () => {
  assert.deepEqual(groundRoot({ x: 2, y: 3 }, { footprint: [3, 2] }), [448, 512]);
  assert.deepEqual(groundRoot({ x: 2, y: 3 }, { footprint: [3, 2], rootCell: [.5, 1.5] }), [320, 576]);
  assert.deepEqual(groundRoot({ x: 0, y: 0 }, {}), [64, 64]);
});

test('attachment overlays use explicitly recorded projected offsets and direction overrides', () => {
  const object = { sockets: { seat: [0, -40] }, ports: [{ name: 'in', position: [-64, -32] }] };
  assert.deepEqual(attachmentMarkers(object, null, 'S'), [{ name: 'seat', position: [0, -40], kind: 'socket' }, { name: 'in', position: [-64, -32], kind: 'port' }]);
  assert.deepEqual(attachmentMarkers(object, { directions: { N: { sockets: { hand: [12, -80] } } } }, 'N')[0], { name: 'hand', position: [12, -80], kind: 'socket' });
});


test('a static object still plays the running belt or character in its interaction scene', () => {
  const stool = { id: 'stool', clips: [{ id: 'static', frames: 1 }], interactions: [{ placements: [{ object: 'belt', clip: 'running' }] }] };
  const belt = { id: 'belt', clips: [{ id: 'paused', frames: 1 }, { id: 'running', frames: 12 }] };
  assert.equal(reviewFrameCount(stool, [stool, belt]), 12);
  assert.equal(reviewFrameCount({ ...stool, interactions: [{ placements: [{ object: 'belt', clip: 'paused' }] }] }, [stool, belt]), 1);
  assert.equal(reviewFrameCount({ ...stool, interactions: [{ placements: [{ object: 'missing' }] }] }, [stool, belt]), 1);
});
