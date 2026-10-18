import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { restaurantShowcase } from '../wireframe/restaurant-showcase-data.js';
import { underwaterShowcase } from '../wireframe/underwater-showcase-data.js';
import { groundRoot, placementAtTime, footprintFor } from '../wireframe/sprite-layout.js';

const production = new URL('../assets/production/', import.meta.url);
const library = JSON.parse(readFileSync(new URL('library.json', production)));
const objects = new Map(library.objects.map(object => [object.id, object]));
const records = new Map(), cameras = new Map();
const native = object => {
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

test('the restaurant conveyor is one directed18-module closed loop at native deck ports', () => {
  const belts = restaurantShowcase.placements.filter(p => objects.get(p.object).kind === 'belt');
  assert.equal(belts.length, 18);
  const graph = topology(belts);
  assert.equal(graph.open.length, 0);
  assert.equal(graph.joins, 18);
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
  assert.equal(visited.size, 18);
});

test('restaurant walls form a continuous cutaway with two genuinely finished ends', () => {
  const walls = restaurantShowcase.placements.filter(p => p.object.startsWith('wall-'));
  const graph = topology(walls);
  assert.equal(walls.length, 20);
  assert.equal(graph.joins, 19);
  assert.deepEqual(graph.open, []);
  assert.equal(walls.filter(p => p.object === 'wall-end').length, 2);
  const left = graph.mates.get('back-left-wall-corner:W')[0];
  const right = graph.mates.get('back-right-wall-corner:S')[0];
  assert.equal(left.placement.id, 'back-wall-0');
  assert.equal(right.placement.id, 'side-wall-1-0');
});

test('underwater canyon, shelf, reef and wreck preserve actual profile geometry through their joins', () => {
  const terrain = underwaterShowcase.placements.filter(p => native(objects.get(p.object)).ports?.length);
  const graph = topology(terrain);
  assert.equal(terrain.length, 33);
  assert.equal(graph.joins, 28);
  const knownJoins = [
    ['west-wall-bottom-turn:N', 'west-wall-lower-seam'],
    ['east-wall-upper-turn:N', 'east-wall-upper-seam'],
    ['wreck-rib-turn:N', 'wreck-rising-rib'],
    ['near-shelf-turn:N', 'near-shelf-upright'],
    ['reef-north-turn:N', 'reef-upright'],
  ];
  for (const [port, neighbor] of knownJoins) assert.equal(graph.mates.get(port)[0]?.placement.id, neighbor, port);
  // Exposed cutaway/embedded tips are intentional; no other native port may
  // silently become an open seam when a module is moved or turned.
  const intentionalOpen = {
    'west-wall-front-edge:W': 'Canyon continues beyond the west cutaway boundary.',
    'east-wall-distant-edge:W': 'Rotated native W port reaches the east cutaway boundary.',
    'wreck-buried-rib:W': 'Open rib disappears toward the rocky bank.',
    'near-shelf-west-run:W': 'Shelf exposes its bank-side cutaway cross-section.',
    'reef-west-lip:W': 'Reef lip ends inside the bank-side coral cluster.',
  };
  assert.deepEqual(graph.open.map(port => port.key).sort(), Object.keys(intentionalOpen).sort());
  for (const explanation of Object.values(intentionalOpen)) assert.ok(explanation.length > 20);
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
