import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { restaurantShowcase } from '../wireframe/restaurant-showcase-data.js';
import { underwaterShowcase } from '../wireframe/underwater-showcase-data.js';
import { groundRoot, placementAtTime, footprintFor, sceneBounds } from '../wireframe/sprite-layout.js';

const production = new URL('../assets/production/', import.meta.url);
const library = JSON.parse(readFileSync(new URL('library.json', production)));
const objects = new Map(library.objects.map(object => [object.id, object]));
const records = new Map(), cameras = new Map();
const native = object => {
  assert.ok(object?.source?.assetRecord, `${object?.id}: a native topology check requires an authored asset record`);
  if (!records.has(object.id)) records.set(object.id, JSON.parse(readFileSync(new URL(object.source.assetRecord, production))));
  return records.get(object.id);
};
const camera = object => {
  if (!cameras.has(object.id)) cameras.set(object.id, JSON.parse(readFileSync(new URL(object.source.camera, production))));
  return cameras.get(object.id);
};
// Read actual authored endpoint rings from the versioned Blender builder AST.
// The audit module is pure stdlib; no bpy, render, packing or file mutation runs.
const sections = JSON.parse(execFileSync('python3', ['-c', String.raw`
import importlib.util,json,pathlib,sys
sys.dont_write_bytecode=True
root=pathlib.Path(sys.argv[1])
spec=importlib.util.spec_from_file_location('readonly_native_sections',root/'validate_connected_fixtures.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
print(json.dumps(module.cross_sections(root/'world_components.py')))
`, fileURLToPath(new URL('source/blender/', production))], { encoding: 'utf8', timeout: 10000 }));
const angles = { S: 0, E: Math.PI / 2, N: Math.PI, W: -Math.PI / 2 };
const normals = { N: [0, 1], E: [1, 0], S: [0, -1], W: [-1, 0] };
const distance = (a, b) => Math.hypot(...a.map((value, index) => value - b[index]));
const rotate = ([x, y], direction) => {
  const angle = angles[direction];
  return [Math.cos(angle) * x - Math.sin(angle) * y, Math.sin(angle) * x + Math.cos(angle) * y];
};
const project = ([x, y, z = 0], direction, object) => {
  [x, y] = rotate([x, y], direction);
  const { calibration: c, captureScale: scale } = camera(object);
  return [0, 1].map(i => (x * c.unitX[i] - y * c.unitDepth[i] + z * c.unitHeight[i]) / scale);
};

function ports(placement) {
  const object = objects.get(placement.object), record = native(object);
  const direction = placement.direction || 'S', root = groundRoot(placement, object);
  const definitions = record.flow ? ['incoming', 'outgoing'].filter(role => record.flow[role]).map(role => {
    const side = record.flow[role], normal = normals[side];
    return { name: role, direction: side, role, position: [...normal.map(v => v * .5), record.flow.deckHeight], normal, profile: 'conveyor-deck' };
  }) : (record.ports || []).map(port => ({ ...port, name: port.name || port.direction }));
  return definitions.map(port => {
    const relative = project(port.position, direction, object);
    assert.ok(distance(relative, object.ports[direction][port.name]) < .001, `${placement.id}/${port.name}: published registration must match native port geometry`);
    if (port.role) assert.equal(object.portDefinition[port.role], port.direction);
    else assert.equal(object.portProfiles[port.name], port.profile);
    // All these native lofts begin at W and leave via E/N/S. Preserve the
    // actual transverse normal so reversed asymmetric profiles cannot pass.
    const tangent = port.direction === 'W' ? port.normal.map(v => -v) : port.normal;
    const transverse = [-tangent[1], tangent[0]];
    const rings = (sections[port.profile] || []).map(ring => ring.map(([width, height]) => {
      const point = project([port.position[0] + transverse[0] * width, port.position[1] + transverse[1] * width, port.position[2] + height], direction, object);
      return point.map((value, i) => value + root[i]);
    }));
    return { key: `${placement.id}:${port.name}`, placement, name: port.name, role: port.role, profile: port.profile,
      point: relative.map((value, i) => value + root[i]), normal: rotate(port.normal, direction), rings };
  });
}

function compatible(a, b) {
  if (a.placement.id === b.placement.id || a.profile !== b.profile || distance(a.point, b.point) > .001) return false;
  if (distance(a.normal, b.normal.map(v => -v)) > .001 || (a.role && a.role === b.role)) return false;
  return a.rings.length === b.rings.length && a.rings.every((ring, i) =>
    ring.every(point => b.rings[i].some(other => distance(point, other) < .001)) &&
    b.rings[i].every(point => ring.some(other => distance(point, other) < .001)));
}

function topology(placements) {
  const all = placements.flatMap(ports);
  const mates = new Map(all.map(port => [port.key, all.filter(other => compatible(port, other))]));
  for (const [key, matches] of mates) assert.ok(matches.length <= 1, `${key}: ambiguous/overlapping seam`);
  return { all, mates, open: all.filter(port => !mates.get(port.key).length), joins: [...mates.values()].filter(matches => matches.length).length / 2 };
}

test('the portrait restaurant conveyor is one directed16-module closed loop at native deck ports', () => {
  const belts = restaurantShowcase.placements.filter(p => objects.get(p.object).kind === 'belt');
  assert.equal(belts.length, 16);
  const graph = topology(belts);
  assert.equal(graph.open.length, 0);
  assert.equal(graph.joins, belts.length);
  const visited = new Set();
  let current = belts[0];
  do {
    assert.ok(!visited.has(current.id), 'A disconnected short cycle must not masquerade as the complete loop');
    visited.add(current.id);
    const next = graph.mates.get(`${current.id}:outgoing`);
    assert.equal(next.length, 1);
    assert.equal(next[0].role, 'incoming');
    current = next[0].placement;
  } while (current.id !== belts[0].id);
  assert.equal(visited.size, belts.length);
});

test('seven-column cameras preserve native hero scale, the back entrance and continuous room edges', () => {
  for (const scene of [restaurantShowcase, underwaterShowcase]) {
    const [x, y, width, height] = scene.cameraBounds;
    assert.deepEqual([x, y, width], [0, 0, 7]);
    assert.deepEqual(scene.gridSize, [width, height]);
    assert.ok(height > width, `${scene.id}: the composition must remain portrait`);
    const padded = sceneBounds(scene.placements, library.objects, 128, scene.gridSize);
    assert.ok(padded[2] > width * 128, `${scene.id}: outer art must be cropped by the authored camera, not shrink the playfield through automatic canvas fitting`);
  }
  const [left, top, width, height] = restaurantShowcase.cameraBounds.map(value => value * 128);
  const inside = ([x, y]) => x >= left && x <= left + width && y >= top - .001 && y <= top + height;
  const chefs = restaurantShowcase.placements.filter(p => objects.get(p.object).family === 'W05');
  assert.ok(chefs.length >= 2, 'The working edge needs its two visible chefs');
  for (const chef of chefs) {
    const object = objects.get(chef.object), root = groundRoot(chef, object);
    const rise = project([0, 0, native(object).height], chef.direction, object);
    assert.ok(inside(root) && inside(root.map((value, axis) => value + rise[axis])), `${chef.id}: native feet and head remain inside the fixed camera`);
    // The approved C125 cast has short legs; a chef without a tall hat is
    // about 1.5 world tiles high, or 17.55% of this seven-column camera.
    assert.ok(Math.abs(rise[1]) / width >= .175, `${chef.id}: the native character must remain a readable hero at this camera width`);
  }
  const entrance = restaurantShowcase.placements.find(p => p.id === 'restaurant-entrance');
  const object = objects.get(entrance.object), record = native(object), root = groundRoot(entrance, object);
  assert.deepEqual(footprintFor(object, entrance.direction), [4, 1]);
  assert.ok(Math.abs(root[0] - (left + width / 2)) < .001, 'The four-tile entrance is centered on the portrait room');
  assert.ok(root[0] - 2 * 128 >= left && root[0] + 2 * 128 <= left + width, 'The entrance retains all four tiles inside the camera');
  assert.ok(inside(root.map((value, axis) => value + project([0, 0, record.height], entrance.direction, object)[axis])), 'The entrance roof remains inside the upper camera edge');
  const beltRoots = restaurantShowcase.placements.filter(p => objects.get(p.object).kind === 'belt').map(p => groundRoot(p, objects.get(p.object)));
  assert.ok(root[1] < Math.min(...beltRoots.map(point => point[1])), 'The entrance anchors the back of the room');
  const opening = record.supportLayout.openCenterCells;
  assert.equal(opening.length, 2);
  assert.deepEqual(opening.map(([x]) => x).sort(), [1, 2], 'The two center cells stay open between the outer supports');
  assert.ok(record.supportLayout.supportCells.every(([x, y]) => !opening.some(cell => cell[0] === x && cell[1] === y)));

  const walls = restaurantShowcase.placements.filter(p => p.object.startsWith('wall-'));
  const graph = topology(walls);
  assert.equal(walls.length, 32);
  assert.equal(graph.joins, walls.length - 2, 'Two uninterrupted room-wall runs preserve every native seam');
  assert.equal(graph.open.length, 4);
  for (const port of graph.open) {
    const ring = port.rings.flat();
    assert.ok(ring.length && (ring.every(point => point[1] < top) || ring.every(point => point[1] > top + height)), `${port.key}: unfinished native wall cross-section must remain wholly outside the authored camera`);
  }
});

test('both underwater banks join actual native cliff profiles and continue wholly beyond the camera', () => {
  const terrain = underwaterShowcase.placements.filter(p => {
    const object = objects.get(p.object);
    if (['imagegen-2d', 'procedural-2d'].includes(object.source?.pipeline)) {
      assert.equal(object.source.assetRecord, undefined, `${object.id}: flat artwork must not claim a native topology record`);
      assert.equal(object.ports, undefined, `${object.id}: 2D overlays cannot supply terrain seam ports`);
      return false;
    }
    return native(object).ports?.length;
  });
  const graph = topology(terrain);
  assert.equal(terrain.length, 34);
  assert.equal(graph.joins, terrain.length - 2);
  const [, top, , height] = underwaterShowcase.cameraBounds.map(value => value * 128);
  for (const side of ['west', 'east']) {
    const bank = terrain.filter(p => p.id.startsWith(`${side}-bank-`)).sort((a, b) => a.y - b.y);
    assert.equal(bank.length, 17);
    assert.equal(bank.filter(p => p.y >= 0 && p.y < underwaterShowcase.gridSize[1]).length, 14);
    assert.deepEqual([...new Set(bank.map(p => p.object))].sort(), ['rock-wall-edge', 'rock-wall-middle']);
    for (let i = 1; i < bank.length; i++) {
      const previous = bank[i - 1];
      assert.ok(graph.all.filter(port => port.placement.id === previous.id).some(port => graph.mates.get(port.key).some(mate => mate.placement.id === bank[i].id)), `${previous.id} must join its next visible/overscan neighbor through the real cross-section`);
    }
  }
  // These are intentional offscreen continuations, not visible unfinished ends.
  // Test the complete elevated profile: a ground point alone can be outside
  // while the tall cliff cross-section still projects into the bottom of frame.
  const intentionalOpen = {
    'west-bank-0:E': 'The west cliff continues beyond the top camera boundary.',
    'west-bank-16:W': 'The west cliff continues below the bottom camera boundary.',
    'east-bank-0:W': 'The east cliff continues beyond the top camera boundary.',
    'east-bank-16:E': 'The east cliff continues below the bottom camera boundary.',
  };
  assert.deepEqual(graph.open.map(port => port.key).sort(), Object.keys(intentionalOpen).sort());
  for (const port of graph.open) {
    const ring = port.rings.flat();
    assert.ok(ring.length && (ring.every(point => point[1] < top) || ring.every(point => point[1] > top + height)), `${port.key}: ${intentionalOpen[port.key]}`);
  }
});

test('matching labels and coincident points cannot hide a flipped asymmetric reef or wreck end', () => {
  for (const family of ['reef', 'wreck']) {
    const [end] = ports({ id: 'reversed-end', object: `${family}-end`, x: 0, y: 0, direction: 'N' });
    const [middle] = ports({ id: 'middle', object: `${family}-middle`, x: 1, y: 0, direction: 'S' });
    assert.equal(end.profile, middle.profile);
    assert.ok(distance(end.point, middle.point) < .001);
    assert.equal(compatible(end, middle), false, `${family}: its one-sided native section must remain on the same side`);
  }
});

for (const [actorId, attachmentId] of [
  ['expedition-submarine', 'submarine-wake'], ['east-pocket-eel', 'eel-following-water'],
]) test(`${actorId} and its separate attachment keep one ground root through every turn`, () => {
  const actor = underwaterShowcase.placements.find(p => p.id === actorId);
  const attachment = underwaterShowcase.placements.find(p => p.id === attachmentId);
  const object = objects.get(actor.object), attachedObject = objects.get(attachment.object);
  const at = (placement, item, seconds) => groundRoot(placementAtTime(placement, seconds, item), item);
  const facings = new Set();
  for (let frame = 0; frame <= underwaterShowcase.duration * 12; frame++) {
    const seconds = frame / 12;
    const placed = placementAtTime(actor, seconds, object), attached = placementAtTime(attachment, seconds, attachedObject);
    assert.equal(placed.direction, attached.direction);
    assert.ok(distance(at(actor, object, seconds), at(attachment, attachedObject, seconds)) < 1e-7, `${actorId}: attachment drift at${seconds}s`);
    facings.add(placed.direction);
  }
  assert.deepEqual([...facings].sort(), ['E', 'N', 'S', 'W']);
  assert.notDeepEqual(footprintFor(object, 'N'), footprintFor(object, 'E'), 'This regression must exercise a rectangular native footprint');
  const path = actor.motion.path;
  const lengths = path.slice(1).map((point, i) => distance(point, path[i]));
  const total = lengths.reduce((a, b) => a + b, 0);
  const speed = total / actor.motion.duration * 128, epsilon = 1e-5;
  const initial = groundRoot({ ...actor, x: 0, y: 0 }, object);
  let traversed = 0;
  for (let i = 0; i < path.length; i++) {
    const time = ((actor.motion.duration * traversed / total - (actor.motion.phase || 0)) % actor.motion.duration + actor.motion.duration) % actor.motion.duration;
    const expected = path[i].map((value, axis) => value * 128 + initial[axis]);
    assert.ok(distance(at(actor, object, time), expected) < 1e-6, `${actorId}: a facing change moved its registered root`);
    const before = (time - epsilon + actor.motion.duration) % actor.motion.duration;
    const after = (time + epsilon) % actor.motion.duration;
    assert.ok(distance(at(actor, object, before), at(actor, object, after)) <= speed * epsilon * 2 + 1e-6, `${actorId}: half-cell jump at a rectangular footprint turn`);
    if (i < lengths.length) traversed += lengths[i];
  }
});
