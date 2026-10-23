import test from 'node:test';
import assert from 'node:assert/strict';
import { spriteFrame, sceneBounds, orderPlacements, repeatedPlacements, placementAtTime, reviewFrameCount, groundRoot, attachmentMarkers, footprintFor, directionPlacements, resolveSupportSocket } from '../wireframe/sprite-layout.js';

const character = { id: 'chef', kind: 'character', frameSize: [192, 320], root: [96, 248], sourceScale: 4, clips: [{ id: 'work', fps: 12, frames: 12, directions: { N: { image: 'chef/work-N.png', columns: 6, rows: 2 }, S: { image: 'chef/work-S.png', columns: 6, rows: 2 } } }] };
const clip = character.clips[0];

test('support sockets follow the currently published sprite projection without moving the ground footprint', () => {
  const plate = { object: 'dish', x: 1, y: 2, direction: 'S', offset: [3, 1], supportSocket: { object: 'belt', socket: 'deck', direction: 'S' } };
  for (const deck of [[0, -81.92], [0, -57.344]]) {
    const support = { id: 'belt', sockets: { S: { deck } } };
    const resolved = resolveSupportSocket(plate, [support]);
    assert.deepEqual(resolved.supportOffset, deck);
    assert.deepEqual(groundRoot(resolved, { footprint: [1, 1] }), [195, 321 + deck[1]]);
    assert.deepEqual([resolved.x, resolved.y], [plate.x, plate.y]);
    assert.deepEqual(resolveSupportSocket(resolved, new Map([['belt', support]])), resolved, 'Resolving twice does not add height twice');
  }
  assert.equal(plate.supportOffset, undefined, 'Scene data stays immutable');
  assert.equal(resolveSupportSocket({ object: 'dish' }, [] ).supportOffset, undefined);
  assert.deepEqual(resolveSupportSocket(plate, []).supportOffset, [0, 0], 'A missing registration never guesses a projection height');
});

test('blue cushion attachment uses the published seat delta from the native wood-seat baseline', () => {
  const seated = { object: 'customer', direction: 'W', supportSocket: { object: 'blue', socket: 'seat', relativeTo: { object: 'wood', socket: 'seat' } } };
  for (const scale of [128, 89.6]) {
    const objects = [{ id: 'blue', sockets: { W: { seat: [0, -.55 * scale] } } }, { id: 'wood', sockets: { W: { seat: [0, -.52 * scale] } } }];
    const result = resolveSupportSocket(seated, objects);
    assert.ok(Math.abs(result.supportOffset[1] + .03 * scale) < 1e-8);
    assert.equal(result.supportOffset[0], 0);
  }
});

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

test('ground depth puts a chef behind the front belt, its attached dish above the deck, and a near customer in front', () => {
  const objects = [character, { id: 'belt', kind: 'belt', layer: 1 }, { id: 'dish', kind: 'prop', layer: 3 }, { id: 'floor', kind: 'floor' }, { id: 'customer', kind: 'character', layer: 2 }];
  const placed = [{ object: 'customer', x: 1, y: 2 }, { object: 'dish', x: 1, y: 1, offset: [0, -82] }, { object: 'belt', x: 1, y: 1 }, { object: 'chef', x: 1, y: 0 }, { object: 'floor', x: 0, y: 3 }];
  assert.deepEqual(orderPlacements(placed, objects).map(value => value.object), ['floor', 'chef', 'belt', 'dish', 'customer']);
  assert.deepEqual(placed.map(value => value.object), ['customer', 'dish', 'belt', 'chef', 'floor']);
});

test('explicit background scenery stays first and foreground or overhead pieces stay last', () => {
  const objects = [{ id: 'far-scenery', renderPass: 'background' }, { id: 'customer', kind: 'character' }, { id: 'arch-front', renderPass: 'overhead' }];
  assert.deepEqual(orderPlacements([{ object: 'arch-front', x: 0, y: 0 }, { object: 'customer', x: 0, y: 5 }, { object: 'far-scenery', x: 0, y: 9 }], objects).map(value => value.object), ['far-scenery', 'customer', 'arch-front']);
});

test('on-deck people draw above their support while external stairs retain native depth ordering', () => {
  const objects = [{ id: 'deck', kind: 'prop', footprint: [3, 3], layer: 0 }, { id: 'person', kind: 'character' }, { id: 'entry', kind: 'prop' }];
  for (const [y, expected] of [[-2, ['entry', 'deck', 'person']], [3, ['deck', 'person', 'entry']]]) {
    const placements = [{ object: 'deck', x: 0, y: 0 }, { object: 'person', x: 1, y: .1, offset: [0, -19.712], supportedBy: 'deck' }, { object: 'entry', x: 1, y }];
    const original = JSON.stringify(placements);
    assert.deepEqual(orderPlacements(placements, objects).map(value => value.object), expected);
    assert.equal(JSON.stringify(placements), original, 'Sorting must not move supported artwork or mutate scene data');
  }
});

test('explicit support instances and support chains preserve foreground passes', () => {
  const objects = [{ id: 'deck', kind: 'prop', footprint: [3, 3] }, { id: 'stool', kind: 'prop' }, { id: 'person', kind: 'character' }, { id: 'front', renderPass: 'foreground' }];
  const placements = [{ id: 'person', object: 'person', y: -3, supportedBy: 'seat' }, { id: 'seat', object: 'stool', y: -2, supportedBy: 'west' }, { id: 'east', object: 'deck', y: 5 }, { id: 'west', object: 'deck', y: 0 }, { id: 'front', object: 'front', y: -9 }];
  assert.deepEqual(orderPlacements(placements, objects).map(value => value.id), ['west', 'seat', 'person', 'east', 'front']);
});

test('ambiguous, missing, cyclic or conflicting-pass support cannot silently choose a draw order', () => {
  const objects = [{ id: 'deck', kind: 'prop' }, { id: 'person', kind: 'character' }, { id: 'overlay', renderPass: 'foreground' }];
  assert.throws(() => orderPlacements([{ object: 'deck', y: 0 }, { object: 'deck', y: 2 }, { object: 'person', y: 1, supportedBy: 'deck' }], objects), /ambiguous/);
  assert.throws(() => orderPlacements([{ object: 'person', y: 1, supportedBy: 'missing' }], objects), /Invalid/);
  assert.throws(() => orderPlacements([{ id: 'a', object: 'deck', y: 0, supportedBy: 'b' }, { id: 'b', object: 'person', y: 1, supportedBy: 'a' }], objects), /Cyclic/);
  assert.throws(() => orderPlacements([{ id: 'top', object: 'overlay', y: 0 }, { object: 'person', y: 1, supportedBy: 'top' }], objects), /render pass/);
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


test('rectangular footprints rotate registration, repeated spacing and facing-panel clearance together', () => {
  const entry = { id: 'entry', footprint: [3, 1], directionFootprints: { N: [3, 1], E: [1, 3], S: [3, 1], W: [1, 3] } };
  assert.deepEqual(footprintFor(entry, 'E'), [1, 3]);
  assert.deepEqual(groundRoot({ x: 0, y: 0, direction: 'E' }, entry), [64, 192]);
  assert.deepEqual(groundRoot({ x: 0, y: 0, direction: 'S' }, entry), [192, 64]);
  const repeated = repeatedPlacements(entry, 'W', 'static');
  assert.deepEqual([repeated[4].x, repeated[4].y], [1, 3]);
  assert.deepEqual(directionPlacements(entry, 'static').map(placement => placement.x), [0, 4, 8, 12]);
  assert.deepEqual(groundRoot({ x: 0, y: 0, direction: 'E' }, { ...entry, directionRootCells: { E: [.5, 2] } }), [64, 256]);
});


test('foreground depth follows the full ground footprint while support height preserves seat layering', () => {
  const objects = [{ id: 'large-prop', kind: 'prop', footprint: [3, 3] }, { id: 'customer', kind: 'character', footprint: [1, 1] }, { id: 'stool', kind: 'prop', footprint: [1, 1] }];
  assert.deepEqual(orderPlacements([{ object: 'large-prop', x: 0, y: 0 }, { object: 'customer', x: 1, y: 0 }], objects).map(value => value.object), ['customer', 'large-prop']);
  assert.deepEqual(orderPlacements([{ object: 'stool', x: 1, y: 1 }, { object: 'customer', x: 1, y: 1, offset: [0, -84] }], objects).map(value => value.object), ['stool', 'customer']);
});
