import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { directionPlacements, reviewDirections, orderPlacements } from '../wireframe/sprite-layout.js';
import { restaurantShowcase } from '../wireframe/restaurant-showcase-data.js';
import { underwaterShowcase } from '../wireframe/underwater-showcase-data.js';

const root = new URL('../assets/production/', import.meta.url);
const overrides = JSON.parse(readFileSync(new URL('source/2d/overrides.json', root)));
const prompts = JSON.parse(readFileSync(new URL('source/2d/prompts.json', root)));
const library = JSON.parse(readFileSync(new URL('library.json', root)));
const deleted = /^(restaurant-(border|corner)-garden|underwater-(reef|coral)-garden)-[ab]$/;

test('every review-required state selects an actual exported clip', () => {
  for (const object of library.objects) for (const state of object.requirements?.states || []) {
    assert.ok(object.clips.some(clip => clip.id === state), `${object.id}/${state} must not silently fall back to another animation`);
  }
});

test('all dishes and bubbles use retained original ImageGen raster artwork', () => {
  const generated = Object.values(overrides).filter(object => object.source.pipeline === 'imagegen-2d');
  assert.equal(generated.length, 8);
  for (const object of generated) {
    assert.equal(object.source.blend, undefined);
    assert.equal(object.facingPolicy, 'camera-facing');
    const original = readFileSync(new URL(object.source.artwork, root));
    assert.equal(createHash('sha256').update(original).digest('hex'), object.source.sha256);
    assert.equal(original.subarray(1, 4).toString(), 'PNG');
    assert.ok(prompts.some(prompt => prompt.id === object.id && prompt.provider === 'Built-in ImageGen' && prompt.prompt.length > 100));
    for (const clip of object.clips) {
      assert.deepEqual(Object.keys(clip.directions), ['S', 'N', 'E', 'W']);
      assert.equal(new Set(Object.values(clip.directions).map(entry => entry.image)).size, 1, 'Screen-facing art stays readable across world facings');
    }
  }
});

test('five attack and eel cues have editable Godot 2D drawing source and no Blender model', () => {
  const effects = Object.values(overrides).filter(object => object.source.pipeline === 'procedural-2d');
  assert.equal(effects.length, 5);
  const source = readFileSync(new URL('source/2d/world_effects.gd', root), 'utf8');
  assert.match(source, /extends Node2D/);
  assert.match(source, /func _draw\(\)/);
  for (const effect of effects) {
    assert.equal(effect.source.blend, undefined);
    assert.ok(existsSync(new URL(effect.source.godot, root)));
    assert.ok(source.includes(effect.id));
  }
});

test('2D animation atlases retain complete registered frames with at least six unique images', () => {
  for (const object of Object.values(overrides)) for (const clip of object.clips) {
    assert.equal(clip.fps, 12);
    for (const entry of Object.values(clip.directions)) {
      assert.ok(existsSync(new URL(entry.image, root)));
      assert.equal(entry.rects.length, clip.frames);
      if (clip.frames > 1) assert.ok(entry.uniqueFrames >= 6, `${object.id}/${clip.id}`);
      for (const rect of entry.rects) assert.deepEqual(rect.slice(2), object.frameSize.map(value => value * 2));
    }
  }
});

test('flat registrations describe their current 2D canvas and contain no superseded 3D socket data', () => {
  for (const object of [...Object.values(overrides), ...library.objects.filter(object => ['imagegen-2d','procedural-2d'].includes(object.source?.pipeline))]) {
    assert.equal(object.registration.method, 'fixed-frame-2d');
    assert.deepEqual(object.registration.completeFrame, object.frameSize);
    assert.deepEqual(object.registration.anchor, object.root);
    assert.equal(object.registration.sourceScale, object.sourceScale);
    assert.equal(object.registration.sourceCaptureScale, undefined);
    assert.equal(object.registration.poseFitting, false);
    for (const field of ['sockets3D','socketSpace','captureFingerprint','height','ports','sockets']) assert.equal(object[field], undefined, `${object.id}: stale native field ${field}`);
    assert.equal(object.validation.rigEvidence, undefined);
    assert.doesNotMatch(object.requirements.notes, /same dish geometry|projected from declared native attachment/i);
  }
});

test('a single player-facing sign exposes only its readable surface in the review grid', () => {
  const sign = { id: 'sign-blank', footprint: [1, 1], facingPolicy: 'single-player-facing' };
  assert.deepEqual(reviewDirections(sign), ['S']);
  assert.deepEqual(directionPlacements(sign, 'static'), [{ object: 'sign-blank', direction: 'S', clip: 'static', x: 0, y: 0 }]);
  assert.deepEqual(reviewDirections({}), ['N', 'E', 'S', 'W']);
});

test('complete scenes replace deleted garden stamps with layered individual objects', () => {
  for (const scene of [restaurantShowcase, underwaterShowcase]) {
    assert.ok(scene.placements.every(placement => !deleted.test(placement.object)));
    assert.ok(scene.highlights.every(highlight => highlight.objectIds.every(id => !deleted.test(id))));
  }
  for (const board of restaurantShowcase.placements.filter(placement => placement.object === 'chef-blackboard')) {
    assert.equal(board.direction, 'S');
    assert.equal(board.renderPass, 'foreground');
    assert.equal(board.offset, undefined, 'Native front-edge model controls placement instead of a second screen offset');
    const chef = restaurantShowcase.placements.find(placement => placement.object.startsWith('chef-') && placement.object !== 'chef-blackboard' && placement.x === board.x && placement.y === board.y);
    assert.ok(chef, 'Board shares the chef tile');
  }
});

test('front-edge signs paint over their shared-tile occupant regardless of insertion order', () => {
  for (const id of ['chef-blackboard', 'sign-blank']) {
    const object = library.objects.find(object => object.id === id);
    assert.equal(object.renderPass, 'foreground', `${id}: shared source policy controls layering`);
    const scene = object.interactions[0];
    const sign = scene.placements.find(placement => placement.object === id);
    const occupant = scene.placements.find(placement => placement.object !== id);
    assert.equal(sign.renderPass, 'foreground');
    for (const placements of [[sign, occupant], [occupant, sign]]) {
      assert.equal(orderPlacements(placements, library.objects).at(-1).object, id);
    }
  }
});

test('all production variant bindings name real exported clips and the blackboard has one blank surface', () => {
  for (const object of library.objects) {
    const exported = new Set(object.clips.map(clip => clip.id));
    for (const [variant, binding] of Object.entries(object.variants || {})) {
      assert.ok(binding.clips?.length, `${object.id}/${variant}: a variant must bind exported visual states`);
      for (const clip of binding.clips) assert.ok(exported.has(clip), `${object.id}/${variant} binds missing clip ${clip}`);
    }
  }
  const board = library.objects.find(object => object.id === 'chef-blackboard');
  assert.deepEqual(board.variants, { blank: { clips: ['idle', 'selected', 'recipe-change'] } });
  assert.deepEqual(board.requirements.variants, ['blank']);
  assert.match(board.requirements.notes, /blank player-facing board/);
  assert.match(board.requirements.notes, /drawn dynamically in Godot/);
  assert.doesNotMatch(board.requirements.notes, /three recipe artworks/);
});
