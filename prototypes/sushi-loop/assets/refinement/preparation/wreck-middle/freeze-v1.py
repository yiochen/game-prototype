from pathlib import Path
import hashlib
import json
import shutil

run = Path(__file__).resolve().parents[2]
root = run.parents[3]
folder = run / 'objects/wreck-middle'
prep = folder / 'reviews/preparation-v1'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text())


def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2) + '\n')


manifest_path = prep / 'manifest.json'
assert sha(manifest_path) == '99db512a0ed5ef839b0f241cd3edcc93e745fe8f39d5eec916ead041890ce6bb'
manifest = read(manifest_path)
assert len(manifest['files']) == 113
assert Path(manifest['pathBases']['worktree']).resolve() == root
external = []
for record in manifest['files']:
    path = Path(record['path']) if record['pathBase'] == 'absolute' else root / record['path']
    assert sha(path) == record['sha256']
    assert path.stat().st_size < 100_000_000
    if record['pathBase'] == 'absolute':
        dest = folder / 'inputs/preparation-instructions' / path.parent.name / path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            assert sha(dest) == record['sha256']
        else:
            shutil.copyfile(path, dest)
        external.append({'originalPath': str(path), 'path': dest.relative_to(folder).as_posix(), 'sha256': sha(dest)})

initial = folder / 'source/initial-observations.json'
assert sha(initial) == '55def4309b79bb828b66c04c98b38a2db60ec981de848e0b3ac0936b707b87f1'
measured = read(prep / 'native-contract-measurements.json')
criteria = read(folder / 'reviews/criteria.json')
plan = read(prep / 'evidence-plan.json')
points = sorted({tuple(v[:2]) for plane in measured['clearanceAndEnvelope']['sourceOuterConvexHull']['planes'] for v in plane['polygon']})


def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


lower, upper = [], []
for point in points:
    while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
        lower.pop()
    lower.append(point)
for point in reversed(points):
    while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
        upper.pop()
    upper.append(point)
xy_hull = [list(point) for point in lower[:-1] + upper[:-1]]
library = read(run.parent / 'production/library.json')
obj = next(obj for obj in library['objects'] if obj['id'] == 'wreck-middle')
assert obj['height'] == .78 and not obj.get('refinement')
reconciliation = {
    'asset': 'wreck-middle', 'status': 'root decisions before construction',
    'preparationManifestSHA256': sha(manifest_path),
    'geometry': {
        'fixed': 'Actual finite three-rectangle W/E sections, handedness, one-cell pitch, root and finite lowest lower-rail patch/ground clearance.',
        'authoringEnvelope': {'xyPolygonCCW': xy_hull, 'z': [.04, .78], 'tolerance': 1e-6},
        'provenance': 'Monotonic-chain convex hull of XY projections of the measured source outer-hull vertices; vertical clearance uses the existing catalog worldHeight. This is an explicit root size budget before editing.',
        'source3DHull': 'Retained as a measured source observation. Its sloping hardware-dependent planes are not an implicit collision law or a required copy of the old upper silhouette.',
        'freedom': 'New native interior construction, upper proportions, decoration, part counts and use of blank bays may improve inside the finite XY/height budget. Original per-part boxes and sampled empty bays are observations. No geometry may reach Z0 or extend beyond this budget.'},
    'canonicalCollars': {'W': [-.5, -.42], 'E': [.42, .5],
        'reason': 'Explicit .08 finite collars fit inside the measured uninterrupted .15 terminal intervals while leaving interior modeling freedom.',
        'fields': 'Fresh middle may redesign native normal/material/albedo fields coherently. Actual shader-used fields and longitudinal derivatives must match under W/E translation. The exact approved result becomes a future family resource; source weak shading is not a lock.'},
    'sampling': plan['samplingProposal'], 'externalPreparationInputs': external,
    'freshEditorInitial': {'path': 'source/initial-observations.json', 'sha256': sha(initial)},
    'scope': 'No candidate, family, production or Godot approval; fixed target and independent visible outcomes retained.'}
write(folder / 'inputs/root-preparation-reconciliation-v1.json', reconciliation)
hard = [
    'True W/E planes X±.5, source ordered asymmetric three disconnected rectangular YZ sections: lower Y±.18/Z.04...20; upper Y±.09/Z.60...74; rear lip Y.20...26/Z.16...35. Preserve exact measured float geometry/winding/handedness and proper all4 root rotations; no mirrored rear lip, port growth or rounded join cuts.',
    'Keep root(0,0,0), pitch1, occupied cell[[0,0]], sockets{}, static frame1/one unique frame/12fps/nonloop/all4. Finite lowest lower-rail support X±.5/Y±.18 at Z.04/area.36; empty geometric Z0 and .04 ground clearance. Do not invent a fullfloor ground patch.',
    'Explicit root authoring budget is measured finite XY convex hull in inputs/root-preparation-reconciliation-v1.json with Z[.04,.78], 1e-6 representation tolerance. Measured hardware-dependent source3D convex hull/per-part boxes/old counts/blank bays are observations, not extra hard locks. Native forms/structure/decoration may change inside this budget; no AABB-only certification.',
    'Establish coherent new canonical endpoint fields on full .08 collars X[-.5,-.42] and [.42,.5] for all three actual profiles. Complete actual normalized post-interpolation shader-used normal/albedo/material/alpha/needed tangent fields and longitudinal derivatives agree under W/E translation, including all4 rotations. Cap normals distinct from visible side normals. Method free with actual finite-field equivalence; no ID/point-only proof or literal node/storage identity veto. Interior detail must meet the new collar fields continuously.',
    'Registered elevation55.0079798/aspect1.22065556/ortho1.5/logical192352/root96248/cell128/directnative2x384704/root192496/filter.01 and exact identity publication/no reduction. Same camera/root/material/lighting recipe across all4; soft symmetric lighting with no preferred horizontal light/directional ground shadow. Exact chosen native rig and active shaders become canonical evidence for future derivatives.',
    'Native single4 and true native three-module repeats4 plus independent individually captured repeats/current570/099 actual consumer. Execute the four bounded cases per two headless modes in the fixed plan, all4 facings/lightgraydark/logical128/phone32/integer/fractional root-pan-CSS, retain native canvas and CSS separately. Expand only for a concrete issue. No family-wide approval inferred.',
    'Visible clean true joins and purposeful crafted blue/cyan hull/slate structure/pale hardware volumes at use size. No local crack/stripe/band/doubled cutcap/alpha puncture/black deadspots/clipping/material-normal discontinuity waiver. Preserve broad finite-light/outer precision residuals honestly. No fit/crop/warp/perviewshift/recolor/paint/targetcard/RGBalpha repair/overlap/halo/shared consumer change. Comparison-only extent diagnosis only for actual discrepancy with zero visible discard and exact integer restoration.'
]
contract = {'asset': 'wreck-middle', 'version': 1, 'status': 'root-frozen-before-construction',
    'preparationManifest': {'path': 'reviews/preparation-v1/manifest.json', 'sha256': sha(manifest_path), 'rootVerifiedFiles': 113},
    'sourceProposal': {'path': 'reviews/preparation-v1/root-proposal.md', 'sha256': sha(prep / 'root-proposal.md')},
    'nativeMeasurements': {'path': 'reviews/preparation-v1/native-contract-measurements.json', 'sha256': sha(prep / 'native-contract-measurements.json')},
    'finitePorts': measured['ports'], 'finiteSupport': measured['finiteSupport'],
    'reconciliation': reconciliation, 'hardConstraints': hard, 'requiredEvidence': plan}
contract_path = folder / 'inputs/root-native-contract.json'
assert not contract_path.exists()
write(contract_path, contract)
backup = folder / 'inputs/brief-before-native-freeze.json'
assert not backup.exists()
shutil.copyfile(folder / 'brief.json', backup)
brief = read(folder / 'brief.json')
brief['capture'].update(nativeFrame=[384, 704], nativeCaptureScale=2, publishedFrame=[384, 704],
    publication='Exact direct-native2x PNG/filter.01, no reduction.', previews=['four-view-sheet', 'repeated', 'phone'])
brief['constraints']['nativeContract'] = 'inputs/root-native-contract.json'
brief['qualityCriteria'] = {'status': 'root-frozen-before-construction',
    'definitionOfGood': 'A crafted blue/cyan wreck frame with substantial soft edge volumes, purposeful wear/slate hardware/pale accents and seamless native repeated connections in every facing.',
    'priorityOutcomes': criteria['aesthetic'], 'hardConstraints': hard,
    'criteriaFile': 'reviews/criteria.json', 'criteriaFileSHA256': sha(folder / 'reviews/criteria.json'),
    'nativeContract': 'inputs/root-native-contract.json', 'nativeContractSHA256': sha(contract_path),
    'preparationManifestSHA256': sha(manifest_path), 'requiredEvidence': plan}
resources = brief.setdefault('technicalResources', {})
resources.update(rootNativeContract='inputs/root-native-contract.json',
    rootReconciliation='inputs/root-preparation-reconciliation-v1.json',
    preparationProposal='reviews/preparation-v1/root-proposal.md',
    nativeMeasurements='reviews/preparation-v1/native-contract-measurements.json',
    preparationManifest='reviews/preparation-v1/manifest.json', evidencePlan='reviews/preparation-v1/evidence-plan.json')
for record in manifest['files']:
    if record['pathBase'] == 'worktree':
        path = root / record['path']
        if path.is_relative_to(prep / 'resources'):
            resources['preparedResource:' + path.relative_to(prep).as_posix()] = path.relative_to(folder).as_posix()
write(folder / 'brief.json', brief)
progress_path = run / 'progress.json'
progress = read(progress_path)
item = next(item for item in progress['objects'] if item['id'] == 'wreck-middle')
item.update(status='editing', editor='catalog_wreck_middle_editor_v1', judge='catalog_wreck_middle_judge_v1',
    editorStatus='starting-construction', judgeStatus='prepared-awaiting-candidate',
    stage='canonical-wreck-middle-round01', briefSHA256=sha(folder / 'brief.json'))
write(progress_path, progress)
print(json.dumps({'asset': 'wreck-middle', 'verifiedPreparationFiles': 113,
    'briefSHA256': sha(folder / 'brief.json'), 'contractSHA256': sha(contract_path),
    'reconciliationSHA256': sha(folder / 'inputs/root-preparation-reconciliation-v1.json'), 'xyHullVertices': len(xy_hull)}))
