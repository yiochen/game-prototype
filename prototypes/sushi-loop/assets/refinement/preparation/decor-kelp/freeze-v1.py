from pathlib import Path
import copy, hashlib, json, shutil

run = Path(__file__).resolve().parents[2]
folder = run / 'objects/decor-kelp'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2) + '\n')

manifest = folder / 'reviews/preparation-v1/manifest.json'
assert sha(manifest) == '1d7de8306e9cc0f2db4bc3d3880d0830b25486f1cf21e3796ea218210e022a3c'
m = read(manifest)
assert len(m['files']) == 190
for f in m['files']:
    p = folder / f['path']
    assert sha(p) == f['sha256'] and p.stat().st_size < 100_000_000, f['path']
initial = folder / 'source/initial-observations.json'
assert sha(initial) == 'e13d45cf88dcf55298ebf63f8126e8071ef7fd1b05b4aed39eca9c1f1c2555db'
proposal_path = folder / 'reviews/source-contract-proposal.json'
criteria_path = folder / 'reviews/proposedcriteria.json'
assert sha(proposal_path) == 'f1f79f771aeccffcfbf63b84db91d2681d42727035d7bd7e2abc64f2435e631f'
assert sha(criteria_path) == 'a23908eb2a6bf6b7c1eb0a14168d4357ba39769a38ffc548805e82ee5f35a3ac'
proposal, criteria = read(proposal_path), read(criteria_path)
adapter = folder / proposal['capture']['nativeProjectionAdapter']['frozenSource']
assert sha(adapter) == 'f00a7b868684ee16989de63e701e8d4496ecbfc14b04fab29e6a605c3d58c178'
style = folder / 'inputs/warm-soft-reference.png'
assert sha(style) == '02e6a13e71b6aba78b85b99f70ac37117b2b6939461ed1bdb2cc3ec334ab4d15'
contract_path = folder / 'inputs/root-native-contract.json'
recon_path = folder / 'inputs/root-preparation-reconciliation-v1.json'
backup = folder / 'inputs/brief-before-native-freeze.json'
assert not any(p.exists() for p in [contract_path, recon_path, backup])

reconciliation = {
    'asset': 'decor-kelp', 'stage': 'root reconciliation BEFORE construction',
    'preparation': {'path': str(manifest.relative_to(folder)), 'sha256': sha(manifest), 'rootVerifiedFiles': 190},
    'freshEditorInitial': {'path': str(initial.relative_to(folder)), 'sha256': sha(initial)},
    'captureLaw': {
        'decision': 'Adopt actual historical height-dependent ordinary35 native mesh adapter PLUS measured35-degree camera, not camera alone or generic55. Own source-camera.json omits this adapter. Preserve exact common function/order across all facings/phases, without per-view fitting.',
        'adapter': copy.deepcopy(proposal['capture']['nativeProjectionAdapter']),
        'cameraRecord': {'path': 'reviews/preparation-v1/evidence/registered-camera-replay.json', 'sha256': sha(folder / 'reviews/preparation-v1/evidence/registered-camera-replay.json')},
        'domains': 'Unadapted native authoring geometry/support/envelope is the physical contract. Temporarily adapted capture geometry intentionally expands ground Y; that projection correction is not new authoring overhang. Save editable source unadapted and retain exact reproducible capture wrapper. The fixed camera-only unitDepth293.671 is not the complete square-ground capture depth: the source adapter makes native ground depth approximately512.',
        'evaluation': 'For each evaluated phase and proper facing, use current actual object matrices and saved original mesh-data coordinates, apply source formula once per actual vertex, update meshes/view layer, render, finally restore original authoring coordinates even on exceptions. Avoid duplicate adaptation of shared mesh data. New topology/modifiers remain allowed but must provide actual pre-adapter/post-adapter/evaluated evidence and reproduce the same common law, without a view-specific fit or hidden different evaluation order.',
        'historicalLimit': 'Retain failed plain35 replay69904 different pixels/alpha255 and historical-adapter replay2559 different pixels/alpha<=3 at32EEVEE samples. Aligned historical replay is not decoded/byte exact. Do not repair pixels or claim historical exactness.'
    },
    'functionalEnvelope': {
        'decision': 'Adopt declared1x1 unadapted authoring XY[-.5,.5] and Z[0,2.12], representation tolerance1e-6. Original swept top2.0902693 is measured source evidence, not a smaller imposed design budget. All required phases/attachments stay within this budget; proper facing/root/scale preserved.',
        'root': [0, 0, 0], 'scale': [1, 1, 1], 'xy': [-.5, .5], 'z': [0, 2.12], 'tolerance': 1e-6,
        'support': 'Native compact grounded cobalt rubble atZ0 with finite actual contact and all green roots/forks connected through the complete idle. Original ground-face union area~.94184494 and17 mesh counts are observations, not exact area/outline/count/full-square-floor locks. Redesigned support and attachments require fresh finite evidence; bounds alone are insufficient.',
        'role': 'Nonblocking layer2 scenery/1x1, no modular ports/sockets or actor rig. Keep useful quiet hierarchy beside the actual submarine and eel.'
    },
    'temporal': 'Preserve idle12 unique samples/12fps/one-second loop, native1..12/published0..11 and separate native closure13/all4. Fixed blue base/worldroot, connected restrained organic sway. Original14 action owners/42Fcurves/.025 amplitudes/counts are observed implementation, not new locks. Native editable motion and actual closure/contact proof required.',
    'referenceLocatorCorrection': {'path': '../../preparation/decor-kelp/initial-reference-locator-correction.json', 'decision': 'Initial prompt named missing own inputs style copy. Copied exact already-frozen global style reference to this locator; no style or target change, independently inspected before editor initial seal.'},
    'methods': 'Forms, counts, construction, normals, materials and symmetric light recipe are free within this contract. Original Faceted shader, world grade, old silhouette zigzags and old motion amplitude are not aesthetic locks. No current candidate or derivative approval.'
}
hard = [
    'Own actual collection S33 production concept kelp-fan/root of same name plus root; root0/unit scale/properS0 E90 N180 W-90, unadapted authoringXY+/-.5/Z[0,2.12]/tol1e-6 over all required phases. Layer2 nonblocking1x1; no invented ports/fullfloor. Native finite grounded cobalt base atZ0 and attached green roots/branches must remain connected throughout motion, using actual finite contact rather than AABB alone.',
    'Exact historical ordinary35 height-dependent native capture adapter plus measured35-degree camera, horizontal sensor fit/ortho1.5/pixelAspect1:1/shift[0,.75], actual matrices in registered-camera-replay.json. Preserve source law b=max(0,1-max(0,world.z)/.42)^2; world.y*=1+(1/sin35-1)*b; X/Z unchanged; original world matrix inversion, one common invocation/order across all facings/phases; finally restore unadapted authoring mesh data. Saved source editable/unadapted; do not bake view-specific warp or use unrelated saved camera.',
    'Logical192x480/root96,384/cell128, raw native4x768x1920/root384,1536 and published2x384x960/root192,768. Preserve measured source float root error, no root nudge. Uniform whole native canvas LANCZOS reduction to2x; exact6x2 atlas2304x1920/gutter0. One chosen filter/sample/material/light recipe across all phases/views; no crop, fit, per-view recolor, image-plane target, alpha/RGB repair or overlap trick.',
    'Native idle12 unique samples1..12/published0..11 at12fps/loop1s, separate closure13 for evidence, no extra atlas frame. All4 required facings; native editable motion with fixed root/blue base, gentle connected sway, no snap/skating/texture swim. Original owner counts and amplitudes are not locks.',
    'Frozen warm-soft target/palette identity and all proposed visible outcomes unchanged. Dense tapered flowing leaf/lime-green kelp rooted into distinct cobalt stones, organic all4 volume/useful negative space, broad soft colored edge/bend highlights, purposeful readable detail and quiet scenery hierarchy. No chalk/plastic glare/black knots/clipping/disconnected roots/normal seams/halo; no preferred horizontal key/directional ground cast.',
    'All52 native phase/facing measurements including separate closure, all48 unique phases visually covered via sheets and actual four-facing playbacks. Native/logical/phone/tiny light-gray-dark views,3x3density and actual submarine/eel context. Fresh actual finite support/attachments through motion plus pre/post adapter/evaluation/camera/facing/closure evidence and portable actual-used resource closure.',
    'Bounded actual consumer controls: S frame0 actual570 detail+registered context and E frame6 actual099 thumbnail, both prescribed Chromium153 modes at390x844 DPR2; restore nearest sampling after native resize, then ordinary wholecanvas CSS filtering. Preserve actual helper hashes/placement/order; record executable/launch/version and canvas versus actualCSS separately. Expand only a concrete candidate concern, not all-phase Cartesian browser matrix.',
    'Every declared hero/preview/playback directly covered by original independent judge with hash-bound evidence. Prior source/preparation/initial/target/criteria immutable. Unchanged packet/direction/acceptance gates. No Git/production/deploy action by editor/judge and no numerical/source-equality waiver of visible defects.'
]
contract = {
    'asset': 'decor-kelp', 'version': 1, 'status': 'root-frozen-before-construction',
    'sourceProposal': {'path': str(proposal_path.relative_to(folder)), 'sha256': sha(proposal_path)},
    'preparationManifest': {'path': str(manifest.relative_to(folder)), 'sha256': sha(manifest), 'rootVerifiedFiles': 190},
    'nativeContract': proposal, 'hardConstraints': hard,
    'reconciliation': reconciliation, 'requiredEvidence': proposal['evidencePlan']
}
write(recon_path, reconciliation)
write(contract_path, contract)
shutil.copyfile(folder / 'brief.json', backup)
brief = read(folder / 'brief.json')
brief['capture'].update(nativeFrame=[768,1920], nativeCaptureScale=4, publishedFrame=[384,960],
    publication='Uniform whole native4x LANCZOS to published2x, historical ordinary35 native adapter plus measured35 camera.',
    previews=['four-view-sheet','phone','repeated','idle-N','idle-E','idle-S','idle-W'])
brief['constraints']['nativeContract'] = 'inputs/root-native-contract.json'
brief['qualityCriteria'] = {
    'status': 'root-frozen-before-construction',
    'definitionOfGood': 'Warm softly finished native kelp with flowing connected green fronds, distinct grounded cobalt stones, broad controlled highlights, readable quiet hierarchy and continuous gentle idle in all required views and use sizes.',
    'priorityOutcomes': criteria['visibleOutcomes'], 'hardConstraints': hard,
    'criteriaFile': str(criteria_path.relative_to(folder)), 'criteriaFileSHA256': sha(criteria_path),
    'nativeContract': 'inputs/root-native-contract.json', 'nativeContractSHA256': sha(contract_path),
    'preparationManifestSHA256': sha(manifest), 'requiredEvidence': proposal['evidencePlan']
}
resources = brief.setdefault('technicalResources', {})
resources.update(rootNativeContract='inputs/root-native-contract.json',
    preparationReconciliation='inputs/root-preparation-reconciliation-v1.json',
    nativePreparationManifest=str(manifest.relative_to(folder)),
    freshEditorInitial='source/initial-observations.json', warmSoftReference='inputs/warm-soft-reference.png')
for f in m['files']:
    resources['prepared:' + f['path']] = f['path']
write(folder / 'brief.json', brief)
p = run / 'progress.json'
d = read(p)
entry = next(x for x in d['objects'] if x['id'] == 'decor-kelp')
entry.update(status='editing', editor='catalog_decor_kelp_editor_v1', judge='catalog_decor_kelp_judge_v1',
    editorStatus='starting-construction', judgeStatus='prepared-awaiting-candidate',
    stage='native-kelp-round01', briefSHA256=sha(folder/'brief.json'))
write(p,d)
print(json.dumps({'asset':'decor-kelp','rootVerifiedPreparationFiles':190,
    'briefSHA256':sha(folder/'brief.json'),'contractSHA256':sha(contract_path),
    'reconciliationSHA256':sha(recon_path)}))
