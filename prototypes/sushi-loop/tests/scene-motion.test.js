import test from 'node:test';
import assert from 'node:assert/strict';
import { placementAtTime, groundRoot, sceneBounds, spriteFrame } from '../wireframe/sprite-layout.js';

const ship = {
  id: 'ship', footprint: [1, 2], frameSize: [320, 384], root: [160, 288],
  directionFootprints: { N: [1, 2], E: [2, 1], S: [1, 2], W: [2, 1] },
  clips: [{ id: 'travel', fps: 12, frames: 12, directions: Object.fromEntries(['N', 'E', 'S', 'W'].map(direction => [direction, { image: `${direction}.png`, columns: 6 }])) }],
};
const route = { object: 'ship', x: 0, y: 0, direction: 'N', clip: 'travel', motion: { path: [[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]], duration: 8, faceTravel: true } };
const close = (a, b, epsilon = 1e-7) => assert.ok(a.every((value, index) => Math.abs(value - b[index]) < epsilon), `${a} should meet ${b}`);

test('a rectangular actor uses its four captured facings while its world ground root follows one continuous route', () => {
  for (const [seconds, direction, root] of [[1, 'E', [192, 128]], [3, 'S', [320, 256]], [5, 'W', [192, 384]], [7, 'N', [64, 256]]]) {
    const pose = placementAtTime(route, seconds, ship);
    assert.equal(pose.direction, direction);
    close(groundRoot(pose, ship), root);
    assert.equal(spriteFrame(ship, ship.clips[0], pose.direction, seconds).image, `${direction}.png`);
  }
  for (const turn of [2, 4, 6, 8]) {
    const before = groundRoot(placementAtTime(route, turn - 1e-7, ship), ship);
    const after = groundRoot(placementAtTime(route, turn + 1e-7, ship), ship);
    close(before, after, .0001);
  }
});

test('phased actors share the same path at different positions and close with the scene clock', () => {
  const staggered = { ...route, motion: { ...route.motion, phase: 2 } };
  for (const seconds of [0, 1, 3, 5, 7]) {
    const actual = placementAtTime(staggered, seconds, ship);
    const expected = placementAtTime(route, seconds + 2, ship);
    close(groundRoot(actual, ship), groundRoot(expected, ship));
    assert.equal(actual.direction, expected.direction);
  }
  close(groundRoot(placementAtTime(staggered, 0, ship), ship), groundRoot(placementAtTime(staggered, 48, ship), ship));
});

test('authored irregular roots and support offsets remain attached through facing changes', () => {
  const irregular = { ...ship, directionRootCells: { N: [.3, 1.2], E: [1.4, .3], S: [.7, .8], W: [.9, .6] } };
  const placement = { ...route, offset: [10, -36] };
  close(groundRoot(placementAtTime(placement, 1, irregular), irregular), [176.4, 117.6]);
  close(groundRoot(placementAtTime(placement, 3, irregular), irregular), [304.4, 245.6]);
});

test('swept scene bounds retain every captured facing canvas along the complete moving path', () => {
  const broad = structuredClone(ship);
  Object.assign(broad.clips[0].directions.E, { frameSize: [600, 400], root: [300, 310] });
  const bounds = sceneBounds([route], [broad], 128, [1, 1]);
  for (let seconds = 0; seconds < 8; seconds += .125) {
    const pose = placementAtTime(route, seconds, broad);
    const root = groundRoot(pose, broad);
    const frame = spriteFrame(broad, broad.clips[0], pose.direction, seconds);
    const left = root[0] - frame.root[0], top = root[1] - frame.root[1];
    assert.ok(left >= bounds[0] && top >= bounds[1]);
    assert.ok(left + frame.frameSize[0] <= bounds[0] + bounds[2]);
    assert.ok(top + frame.frameSize[1] <= bounds[1] + bounds[3]);
  }
});

test('a fixed-facing curved dish path retains its original root registration and endpoint hold', () => {
  const dish = { id: 'dish', footprint: [1, 1] };
  const placement = { object: 'dish', direction: 'W', x: 1, y: 1, offset: [0, -81.92], motion: { path: [[1, 1], [3, 1], [3, 2]], duration: 3, loop: false } };
  const pose = placementAtTime(placement, 9, dish);
  assert.equal(pose.direction, 'W');
  close(groundRoot(pose, dish), [448, 238.08]);
});
