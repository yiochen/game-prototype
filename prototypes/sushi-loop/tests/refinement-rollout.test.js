import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const production = new URL('../assets/production/', import.meta.url);
const refinement = new URL('../assets/refinement/', import.meta.url);
const read = url => JSON.parse(readFileSync(url));
const sha = url => createHash('sha256').update(readFileSync(url)).digest('hex');
const library = read(new URL('library.json', production));
const progress = read(new URL('progress.json', refinement));
const promoted = library.objects.filter(object => object.refinement?.status === 'approved');

test('each promoted sprite is the exact accepted candidate with truthful review provenance', () => {
  for (const object of promoted) {
    const root = new URL(`objects/${object.id}/`, refinement);
    const round = object.refinement.round;
    const packetUrl = new URL(`candidates/${round}/packet.json`, root);
    const packet = read(packetUrl);
    const recipeReuse = object.refinement.approvalMethod === 'recipe-reuse';
    const reviewUrl = new URL(`${recipeReuse ? 'validations' : 'reviews'}/${round}.json`, root);
    const review = read(reviewUrl);
    assert.equal(sha(packetUrl), object.refinement.packetSHA256);
    assert.equal(review.candidatePacketSHA256, object.refinement.packetSHA256);
    assert.equal(sha(reviewUrl), object.refinement[recipeReuse ? 'validationSHA256' : 'reviewSHA256']);
    if (object.source.blend) assert.equal(object.captureFingerprint, object.refinement.packetSHA256);
    else assert.equal(object.captureFingerprint, undefined, `${object.id}: fabricated native capture field`);
    assert.equal(review.verdict, recipeReuse ? 'validated' : 'approve');
    if (recipeReuse) {
      assert.equal(review.independentReview, false);
      assert.equal(object.refinement.judge, null);
      const script = fileURLToPath(new URL('../assets/refinement/tools/acceptance_contract.py', import.meta.url));
      const result = JSON.parse(execFileSync('python3', [script, object.id, '--round', round], {encoding: 'utf8'}));
      assert.equal(result.method, 'recipe-reuse');
    }
    assert.deepEqual(review.blockers, []);
    const files = [...Object.values(packet.files), ...Object.values(packet.candidateRenders), ...Object.values(packet.previews)];
    for (const file of files) assert.equal(sha(new URL(file.path, packetUrl)), file.sha256, `${object.id}: changed evidence ${file.path}`);
    const inspectedPreviews = recipeReuse ? ['four-view-sheet', 'phone'].map(name => packet.previews[name]) : Object.values(packet.previews);
    for (const file of [...Object.values(packet.candidateRenders), ...inspectedPreviews]) {
      assert.ok(review.inspectedFiles.includes(file.path), `${object.id}: uninspected view ${file.path}`);
    }
    const approvedHashes = new Set(files.map(file => file.sha256));
    for (const clip of object.clips) for (const entry of Object.values(clip.directions)) {
      assert.ok(approvedHashes.has(sha(new URL(entry.image, production))), `${object.id}/${clip.id}: production pixels differ from approved packet`);
    }
    const editableSource = object.source.refinedSource ?? object.source.blend;
    assert.equal(sha(new URL(editableSource, production)), packet.files.candidateProject.sha256);
    if (object.source.refinedSource) {
      assert.ok(['imagegen-2d', 'procedural-2d'].includes(object.source.pipeline));
      assert.equal(object.source.blend, undefined, `${object.id}: fabricated Blender source`);
    }
  }
});

test('native refinement preserves every original clip and registered root', () => {
  for (const object of promoted) {
    const original = read(new URL(`objects/${object.id}/final/original-catalog-object.json`, refinement));
    for (const key of ['clips', 'frameSize', 'root', 'sourceScale', 'footprint', 'height', 'projection', 'sockets', 'ports']) {
      assert.deepEqual(object[key], original[key], `${object.id}: changed ${key}`);
    }
    if (!object.source.blend) {
      assert.equal(object.registration.method, 'fixed-frame-2d');
      assert.deepEqual(object.registration.anchor, object.root);
      assert.deepEqual(object.registration.completeFrame, object.frameSize);
      assert.equal(object.registration.sourceScale, object.sourceScale);
      assert.equal(object.registration.sourceCaptureScale, undefined);
      continue;
    }
    const camera = read(new URL(object.source.camera, production));
    assert.deepEqual(camera.frame, object.frameSize);
    assert.deepEqual(camera.anchor, object.root);
    assert.equal(camera.captureScale, object.sourceScale);
    assert.equal(object.registration.sourceCaptureScale, object.sourceScale);
    if (camera.approvedRecordSHA256) {
      const recordUrl = new URL(`../inputs/approved-camera-record.json`, new URL(object.source.blend, production));
      assert.equal(sha(recordUrl), camera.approvedRecordSHA256);
      if (camera.nativeMeasurement) {
        const measured = read(recordUrl);
        assert.deepEqual(camera.nativeMeasurement, measured);
        assert.deepEqual(measured.nativeFrame, object.frameSize.map(value => value * object.sourceScale));
        assert.deepEqual(camera.calibration.root, measured.rootPx);
        assert.deepEqual(camera.camera, {type: 'orthographic', worldMatrix: measured.matrix,
          orthoScale: measured.orthoScale, shift: measured.shift});
        const packetUrl = new URL(`objects/${object.id}/candidates/${object.refinement.round}/packet.json`, refinement);
        const packet = read(packetUrl);
        const audit = Object.values(packet.files).find(file => file.sha256 === camera.approvedNativeValidationSHA256);
        assert.ok(audit, `${object.id}: measured camera validation is not approved`);
        const native = read(new URL(audit.path, packetUrl));
        assert.equal(native.allChecksPassed, true);
        assert.deepEqual(native.camera, measured);
      } else {
        const selected = read(recordUrl).assets[camera.selectedAsset];
        for (const key of ['frame', 'anchor', 'captureScale', 'camera', 'registrationPoint', 'nativeObjectOrigin']) {
          assert.deepEqual(camera[key], selected[key], `${object.id}: backdrop camera normalization changed ${key}`);
        }
      }
    }
  }
});

test('native facing evidence follows the original publisher rotation convention', () => {
  const script = fileURLToPath(new URL('../assets/refinement/tools/audit_directions.py', import.meta.url));
  for (const object of promoted.filter(object => object.source.blend)) {
    const result = JSON.parse(execFileSync('python3', [script, object.id, '--round', object.refinement.round], { encoding: 'utf8' }));
    assert.equal(result.status, 'passed', object.id);
  }
});

test('independent object pairs stay separate and conveyor recipe reuse follows user scope', () => {
  const assigned = progress.objects.filter(object => object.editor || object.judge);
  const ids = assigned.flatMap(object => [object.editor, object.judge]);
  assert.ok(ids.every(Boolean));
  assert.equal(new Set(ids).size, ids.length, 'Agent instance reused across objects or roles');
  const policy = read(new URL('conveyor-recipe-policy.json', refinement));
  for (const object of progress.objects.filter(object => object.workflow === 'recipe-reuse')) {
    assert.ok(policy.scope.includes(object.id));
    assert.equal(object.independentReviewRequired, false);
  }
  assert.equal(progress.completed, promoted.length);
  assert.equal(progress.total, progress.objects.filter(object => !['skipped', 'deferred'].includes(object.status)).length);
});

test('restaurant floor tiles retain their original catalog contract and image bytes', () => {
  const excluded = read(new URL('excluded-restaurant-floors.json', refinement));
  assert.deepEqual(Object.keys(excluded).sort(), ['floor-blue-wave', 'floor-checker', 'floor-cream']);
  for (const [id, baseline] of Object.entries(excluded)) {
    assert.deepEqual(library.objects.find(object => object.id === id), baseline.object);
    assert.equal(progress.objects.find(object => object.id === id).status, 'skipped');
    for (const [image, expected] of Object.entries(baseline.images)) assert.equal(sha(new URL(image, production)), expected);
  }
});
