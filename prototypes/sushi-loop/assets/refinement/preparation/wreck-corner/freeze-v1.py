from pathlib import Path
import argparse, copy, hashlib, json, shutil

parser = argparse.ArgumentParser()
parser.add_argument('--editor-initial-sha', required=True)
args = parser.parse_args()
run = Path(__file__).resolve().parents[2]
folder = run / 'objects/wreck-corner'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2) + '\n')

manifest = folder / 'reviews/preparation-v1/manifest.json'
assert sha(manifest) == 'b91f963158c4f687892a4194672cdc52004b3b4da55ccdd424fafecaea315271'
m = read(manifest)
assert len(m['files']) == 283
for f in m['files']:
    p = folder / f['path']
    assert sha(p) == f['sha256'] and p.stat().st_size < 100_000_000, f['path']
initial = folder / 'source/initial-observations.json'
assert len(args.editor_initial_sha) == 64 and sha(initial) == args.editor_initial_sha
pp = folder / 'reviews/source-contract-proposal.json'
cp = folder / 'reviews/proposedcriteria.json'
ep = folder / 'reviews/preparation-v1/evidence-plan.json'
assert sha(pp) == 'ba34791e7e99657a65fd50bdbdff877664a8a60a00dd13c5fdcdc16ea4bdb00c'
assert sha(cp) == 'd0f5327134a8a95b4ce4820ea912ebbacb998de5d0c4eddae79516cfa583a79b'
assert sha(ep) == 'ae09d412dba0c9fb8087ad5a3f9ecd9d376f703d2d69e11f0d8665e250f2853c'
proposal, criteria, plan = read(pp), read(cp), read(ep)
assert len(proposal['authoringBudgetProposal']['finiteXYConvexHullCCW']) == 13
assert len(proposal['finiteSupport']['outlineCCW']) == 10
contract_path = folder / 'inputs/root-native-contract.json'
recon_path = folder / 'inputs/root-preparation-reconciliation-v1.json'
binding_path = folder / 'inputs/approved-wreck-authorities-v1.json'
backup = folder / 'inputs/brief-before-native-freeze.json'
assert not any(p.exists() for p in [contract_path, recon_path, binding_path, backup])

authorities = {}
expected = {
    'wreck-middle': ('d44748684c4e13a25bfd7e28fe5862232ccb8b0d11d530cd9702ea66f525d46c',
                     'f371a2509c600cce6b4f53223aa6c0ed546a9db00b79ffcc78dc8fb710b68005',
                     '6f06d28d217abe29bff3ceaa672814a1233553b87a856f54afb4d28a1a33ac76'),
    'wreck-edge': ('a7f8357632d42d3f5113f7ee3b423634bdd834e0d3cbfb9a058ea513767a1498',
                   '7fe4e36723fe87bea1a94d12f9b85e62b4cafffcc0e34b814b3298e8866aaae1',
                   'aea556e4669f9a9d57bd92d02de484d00a225934d5705a5124683a444c993f58')
}
for asset, (source_sha, packet_sha, review_sha) in expected.items():
    base = folder / 'reviews/preparation-v1/resources/canonical' / asset
    source = base / 'source/round-02.blend'
    packet = base / 'candidates/round-02/packet.json'
    review = base / 'reviews/round-02.json'
    assert sha(source) == source_sha and sha(packet) == packet_sha and sha(review) == review_sha
    p, r = read(packet), read(review)
    assert r['verdict'] == 'approve' and not r['blockers'] and r['candidatePacketSHA256'] == packet_sha
    assert p['files']['candidateProject']['sha256'] == source_sha
    records = {'source': source, 'packet': packet, 'review': review}
    for facing, descriptor in p['candidateRenders'].items():
        hero = base / 'individual' / (facing + '.png')
        assert sha(hero) == descriptor['sha256']
        records['hero-' + facing] = hero
    authorities[asset] = {key: {'path': str(path.relative_to(folder)), 'sha256': sha(path)}
                          for key, path in records.items()}
field = folder / 'reviews/preparation-v1/resources/canonical/wreck-middle/candidates/round-02/canonical-endpoint-fields.json'
authorities['wreck-middle']['endpointFields'] = {'path': str(field.relative_to(folder)), 'sha256': sha(field)}
write(binding_path, {'asset': 'wreck-corner', 'authorities': authorities,
    'scope': 'Exact approved technical source/fields/rig/capture and individual frames retained in immutable own preparation. No corner, derivative or family approval.'})

reconciliation = {
    'asset': 'wreck-corner', 'stage': 'root reconciliation BEFORE construction',
    'preparation': {'path': str(manifest.relative_to(folder)), 'sha256': sha(manifest), 'rootVerifiedFiles': 283},
    'freshEditorInitial': {'path': str(initial.relative_to(folder)), 'sha256': sha(initial)},
    'authoringEnvelope': {
        'decision': 'Adopt own measured RAW thirteen-point XY convex hull extruded Z[.04,.78], tolerance1e-6. Enabled parented source transforms are authority. The evaluated eleven-point bevel hull and inactive negative-Z probes are retained diagnostics, not the design budget. Do not import middle/edge AABBs, per-part boxes, sloping3D hull, old hardware count or old corner construction.',
        'xy': proposal['authoringBudgetProposal']['finiteXYConvexHullCCW'], 'z': [.04,.78], 'tolerance': 1e-6
    },
    'support': {
        'decision': 'Preserve actual finite lowest lower-rail support union with the ten-point source outline atZ.04, area.33363961130866043 within1e-6 representation tolerance. Topology/triangulation may change; this is finite support coverage, not AABB/triangle-count equality. No support atZ0, arbitrary fullsquarefloor, base lift/drop or new outside support.',
        'outline': proposal['finiteSupport']['outlineCCW'],
        'area': proposal['finiteSupport']['triangleArea'], 'z': .04, 'tolerance': 1e-6
    },
    'canonical': {
        'binding': {'path': str(binding_path.relative_to(folder)), 'sha256': sha(binding_path)},
        'decision': 'Adopt exact approved middle02 complete finite.08 W/N contact fields/rig/world/capture, W identity and N properRz+90 of canonicalE, transverse=-X/rearX[-.26,-.20]. Opposing N neighbor is canonicalW atroot(0,1), rotation+90. All outer facings proper rotations. Actual shader-used normalized postinterpolation fields are normative; equivalent native graph/storage allowed. Edge02 is an exact bounded mixed-L neighbor, not family approval.'
    },
    'interiorFreedom': 'Native corner forms, proportions, construction, topology, part counts, iron/hardware and purposeful details may improve inside own budget. Preserve coherent open-bay/rail reading without imposing exact source hole layout, old blankness or an invented actor traversal path. No arbitrary opaque-pixel demand across legitimate open bays; source equality/numerical checks never waive a visible local defect.',
    'captureExtension': 'Hero ortho1.5/direct2x remains fixed. True native L evidence uses declared integer canvas extension and corresponding proportional ortho scale preserving128 logical units/cell, actual projected basis and authored roots, not per-view art fitting. Keep full original individual frames/capture and measure common basis/root correspondence.',
    'unchanged': 'Fixed warm-soft target, proposed visible criteria, camera/registration/static timing/atlas, canonical contact law and bounded8 actual browser runs unchanged. No current candidate approval.'
}
hard = [
    'Own actual S33_PROP_wreck-corner.001/rootwreck-corner__root.001, root0/unit scale/properS0 E90 N180 W-90/pitch1/staticframe1/range1..1/12fps/nonloop/1x1/layer2. Actual own RAW13point XY hull extrudedZ[.04,.78]/tol1e-6, proper-rotated all4; evaluated11point bevel hull, inactive negativeZ, middle AABB/perpart/3Dhull/count/old construction are not locks.',
    'Preserve actual finite ten-point lowest support union atZ.04/area.33363961130866043/tol1e-6. Same actual finite region, triangulation free; not AABB/count-only evidence. No Z0/fullsquarefloor, lifted/dropped base or outside overhang. Declaredheight.78 budget is not old actualtop.74 maximum.',
    'TrueW[-.5,0,0] andN[0,.5,0] ordered three disconnected finite canonical rectangles, proper handedness/outward capwindings. W canonicalW identity; N canonicalE properRz+90 with transverse-X/rearX[-.26,-.20]. Preserve exact original float contours under all4 proper rotations, no mirror/cut rounding/deletion/overlap/growth/step/fake alpha.',
    'Complete.08 W x[-.5,-.42] andN y[.42,.5] canonical side/cap fields: actual shader-used normalized postinterpolation normals/albedo/material/alpha/needed tangent/longitudinal derivatives match exact approved middle02 under the proper mapping. Actual cap response distinct from side fields. Equivalent native storage/graphs allowed if actual fields match; contour IDs/unlinked attributes/isolated samples alone insufficient. Interior transition must be coherent.',
    'Exact registered55.0079798/aspect1.22065556/ortho1.5/logical192352/root96248/cell128, DIRECTnative2x384704/root192496/filter.01/full PNG identity/no reduction/1x1atlas/all4. Actual canonical EEVEE/Standard/None/exposure0/gamma1/dither0/worldStrength.28/color(.72,.80,1), overhead195Wsize8Z5+4equal114Wsize8radius6Z4 DISKshadowfalse; full actual graph/matrices govern. No old Faceted/world0/contrast135 reset, preferred horizontal key/directionalgroundcast or perview adjustment.',
    'All4 true native L: owncorner0/a, W middle02 rootRz(a)*(-1,0,0)/rotationa, N middle02 rootRz(a)*(0,1,0)/rotationa+90. Bounded mixedL replaces W middle with exact approved edge02, N middle stays. Proper real contacts/unitpitch/fullgeometry/no fitting. Exact approved individual art compared through actual570/099 at same roots/order/atlasrects. Expanded logical320480/native640960 proof uses actual coordinate-derived roots/common128 basis and proportional camera extension only; hero unchanged.',
    'Frozen4case x2 prescribed Chromium153 modes/all4/nativeL+mixedL/lightgraydark/128+32/integer-fractionalroot+pan and actualCSS plan. Nativecanvas nearest AFTER every resize then ordinary wholeCSS filtering. Record actual versions/executables/options/viewport/DPR/fixtures/roots/order/helper/native-control/atlas hashes and raw differences. Expand concrete concern only, no large Cartesian matrix. No unapproved end/corner circular authority or family approval.',
    'Fixed six visible criteria: purposeful substantial soft blue hull/iron/pale fasteners/rounded L structure, controlled colored highlights/material separation/useful detail/open-bay readability/all4 coherence128/32. No localized crack/slit/stripe/step/doubled cap/normal seam/blackpatch/halo/clipping/deadspot waiver. Legitimate continuous open construction accepted on visible merits; broad finite-light/exterior raster residuals separate and honest.',
    'Native editable portable private actual-used closure/static ownership, measured source/camera/root/finite support/fullfields required. No targetcard/paint/fit/crop/warp/nudge/overlap/perviewrecolor/RGBalpha repair/sharedhelper changes. Every declared hero/preview directly covered by original judge, samehash aliases mapped explicitly. Unchanged integrity/direction/acceptance gates. Preserve originals/preparation/initial/target/criteria/prior signed rounds immutable; no source/production/Git/deploy/device/liveBlender actions outside own experiment.'
]
contract = {'asset':'wreck-corner','version':1,'status':'root-frozen-before-construction',
    'sourceProposal':{'path':str(pp.relative_to(folder)),'sha256':sha(pp)},
    'preparationManifest':{'path':str(manifest.relative_to(folder)),'sha256':sha(manifest),'rootVerifiedFiles':283},
    'nativeContract':proposal,'hardConstraints':hard,'reconciliation':reconciliation,
    'requiredEvidence':plan,'approvedCanonical':authorities}
write(recon_path, reconciliation)
write(contract_path, contract)
shutil.copyfile(folder/'brief.json', backup)
brief = read(folder/'brief.json')
brief['capture'].update(nativeFrame=[384,704],nativeCaptureScale=2,publishedFrame=[384,704],
    publication='Exact direct native2x PNG identity/filter.01; no reduction.',previews=['four-view-sheet','phone','repeated'])
brief['constraints']['nativeContract']='inputs/root-native-contract.json'
brief['qualityCriteria']={'status':'root-frozen-before-construction',
    'definitionOfGood':criteria['definitionOfGood'],'priorityOutcomes':criteria['priorityOutcomes'],
    'hardConstraints':hard,'criteriaFile':str(cp.relative_to(folder)),'criteriaFileSHA256':sha(cp),
    'nativeContract':'inputs/root-native-contract.json','nativeContractSHA256':sha(contract_path),
    'preparationManifestSHA256':sha(manifest),'requiredEvidence':plan}
resources=brief.setdefault('technicalResources',{})
resources.update(rootNativeContract='inputs/root-native-contract.json',
    preparationReconciliation='inputs/root-preparation-reconciliation-v1.json',
    approvedCanonicalBinding=str(binding_path.relative_to(folder)),nativePreparationManifest=str(manifest.relative_to(folder)),
    freshEditorInitial=str(initial.relative_to(folder)))
for f in m['files']:
    resources['prepared:'+f['path']]=f['path']
write(folder/'brief.json',brief)
p=run/'progress.json';d=read(p);entry=next(x for x in d['objects'] if x['id']=='wreck-corner')
entry.update(status='editing',editor='catalog_wreck_corner_editor_v1',judge='catalog_wreck_corner_judge_v1',
    editorStatus='starting-construction',judgeStatus='prepared-awaiting-candidate',
    stage='native-wreck-corner-round01',briefSHA256=sha(folder/'brief.json'))
write(p,d)
write(run/'preparation/wreck-corner/freeze-execution-v1.json',{
    'scriptSHA256':sha(Path(__file__)),'editorInitialSHA256':args.editor_initial_sha,
    'preparationManifestSHA256':sha(manifest),'rootVerifiedPreparationFiles':283,
    'briefSHA256':sha(folder/'brief.json'),'contractSHA256':sha(contract_path),'reconciliationSHA256':sha(recon_path)})
print(json.dumps({'asset':'wreck-corner','briefSHA256':sha(folder/'brief.json'),
    'contractSHA256':sha(contract_path),'reconciliationSHA256':sha(recon_path)}))
