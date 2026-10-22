import pathlib, json, hashlib

B = pathlib.Path(__file__).parent
OBJ = B.parent.parent
P = OBJ / 'candidates/round-02/packet.json'
R = OBJ / 'reviews/round-02.json'
M = B / 'manifest.json'
S = B / 'seal.json'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(p, data):
    p.write_text(json.dumps(data, indent=2) + '\n')

assert not any(p.exists() for p in [R, M, S]), 'Never overwrite a signed review'
assert sha(P) == '8977786df9528051c31bf94c293b743e65a9632c65635693ec2a0b93d54f280c'
assert sha(OBJ / 'source/round-02.blend') == '2c0bf0dcbc9c4a2e23f96a0cacd30360cb3be271f4cb465c7b49690970daacc1'
assert sha(B / 'resources/source.blend') == sha(OBJ / 'source/round-02.blend')
assert sha(OBJ / 'reviews/round-01.json') == '5a90743010161a112d750fbe88dcb553474f74c93c1fd83958e08b98447989c8'
assert sha(OBJ / 'reviews/round-01-independent/manifest.json') == 'cce8ec7b963857faeb9d36afb993fdcf9ca10ff4fee9c15cc726185ba8555ecb'
assert sha(B / 'resources/brief.json') == '708eb790e6ba8e5c81287fa7ad3589bbb24a733922c197a7104c7e3ed0533275'
assert sha(B / 'resources/root-native-contract.json') == '00de726dbd7b195ae6b3322e07e4fcb2b62ecf342f3ec90c5390db799a788742'
assert sha(B / 'resources/criteria.json') == 'ea0a7afbb9c7a252ba65bcdcca1c8c8dbc671245cf0511417a96fedb85adb58f'
packet = json.loads(P.read_text())
inspected = ['static-N.png', 'static-E.png', 'static-S.png', 'static-W.png',
             'four-view-sheet.png', 'consumer-gray-all4.png', 'native-all4-4x.png',
             'consumer-light-all4.png', 'consumer-dark-all4.png',
             'consumer-phases-NS.png', 'consumer-phases-EW.png']
assert set(inspected) == {r['path'] for group in ['candidateRenders', 'previews'] for r in packet[group].values()}
verification = json.loads((B / 'evidence/packet-verification.json').read_text())
assert verification['allMatch'] and verification['packetSHA256'] == sha(P)
control = json.loads((B / 'evidence/frozen-current-consumer-control.json').read_text())
assert control['allExact'] and len(control['comparisons']) == 8
assert all(x['nativePositionsIntegral'] for x in control['comparisons'])
files = []
for p in sorted(B.rglob('*')):
    if p.is_file() and p not in [M, S]:
        assert p.stat().st_size < 100000000
        assert '__pycache__' not in p.parts
        files.append({'path': str(p.relative_to(OBJ)), 'sha256': sha(p), 'bytes': p.stat().st_size})
manifest = {
    'schema': 'independent-judge-supplement-v1', 'asset': 'rock-shelf-middle', 'round': 'round-02',
    'candidatePacketSHA256': sha(P), 'sourceSHA256': sha(OBJ / 'source/round-02.blend'), 'files': files,
    'scope': 'Original independent judge full art and technical review of the exact sealed round-02 candidate. Candidate/source/inputs/preparation/prior verdict unchanged. Native saved-source reopen, endpoint fields, publication, actual consumer and all declared visual media independently checked. No model save or art edits; no family or promotion approval.',
    'resourceClosure': 'Exact source/packet/brief/criteria/contract/references/instructions, sealed raw single/strip and published inputs, frozen and current actual consumer helpers, independent scripts, minimal executable Pillow/Playwright closure, reopens/strips/measurements/browser captures. Application/Python/Node/browser runtimes externally pinned; no full runtime trees duplicated.'
}
write(M, manifest)
review = {
    'asset': 'rock-shelf-middle', 'round': 'round-02', 'verdict': 'revise',
    'candidatePacketSHA256': sha(P), 'candidateProjectSHA256': sha(OBJ / 'source/round-02.blend'),
    'independentReview': True, 'firstArtReview': False,
    'scope': 'Full shape/color/light/detail/use-size/all4/continuity assessment against the same frozen target and criteria. Round-01 remains immutable. No editor rationale or self-rating used to decide appearance.',
    'inspectedFiles': inspected,
    'inspectionCoverage': {
        'method': 'All 11 exact declared packet media paths were directly opened at original image detail. No unseen aliases or hash-only appearance coverage claimed.',
        'candidateRenders': 'Direct individual 384x704 transparent N/E/S/W inspection.',
        'four-view-sheet': 'Direct source 2x, logical 128-cell and phone 32-cell across light/gray/dark.',
        'native-all4-4x': 'Direct 3072x1408 all-four native sheet, including major surfaces, lower body, cutfaces and embedded stones.',
        'consumerSheets': 'Direct all-four native three-middle versus independently captured three-middle, on light/gray/dark at logical 128-cell and phone 32-cell.',
        'fractionalSheets': 'Direct complete NS and EW sheets cover all four directions at logical phases 0/.25/.5/.75 at logical 128-cell and phone 32-cell.',
        'independentExtraInspection': [
            'reviews/round-02-independent/resources/original.png',
            'reviews/round-02-independent/resources/target.png',
            'reviews/round-02-independent/evidence/consumer-gray-all4.png',
            'reviews/round-02-independent/evidence/consumer-light-all4.png',
            'reviews/round-02-independent/evidence/consumer-dark-all4.png',
            'reviews/round-02-independent/evidence/consumer-phases-N.png',
            'reviews/round-02-independent/evidence/consumer-phases-E.png',
            'reviews/round-02-independent/evidence/consumer-phases-S.png',
            'reviews/round-02-independent/evidence/consumer-phases-W.png'
        ]
    },
    'scores': {'shapeVolume': 7, 'color': 7, 'lightingHighlights': 6, 'materialDetail': 6, 'artifactFreeReadability': 7},
    'scoreContext': 'Comparative observations, not numeric acceptance thresholds. Major slab volume and E/W cutface readability improved materially. The same lower-body criterion remains unresolved in N/S, so technical success and higher scores do not establish art approval.',
    'priorBlockerDisposition': [
        {'id': 'major-rock-volume', 'status': 'addressed', 'evidence': 'Large rounded/gently faceted cyan slab faces and broad turning-plane highlights now read before the cracks in every facing, including logical 128-cell and phone 32-cell. A shallow interpretation of the selected style is acceptable within the locked height budget.'},
        {'id': 'lower-body-readability', 'status': 'partially-addressed', 'evidence': 'E/W exposed cutfaces now contain clear mid-blue faceted stone fields. N/S is brighter than round-01, but its lower body still reads as a band with blurred dark grooves rather than coherent lower stone planes.'}
    ],
    'observations': [
        'All four views retain the low blue/cyan shelf identity, coherent registration and continuous modular silhouette. The major crown now has substantial slab masses with broad plane/highlight transitions. Thin joints and the lavender/teal embedded stones remain secondary, including at phone 32-cell. This resolves the prior flat decorated-slab blocker without requiring literal target topology.',
        'Blue/cyan value separation is more useful than round-01. Broad highlights are soft and consistent across the four facings. The E/W open cutfaces now read as modeled blue stone planes rather than dark blank trapezoids. No preferred horizontal light direction, directional ground shadow, blown highlight, bright silhouette fringe, clipping or absent facing was observed.',
        'In N/S, the lower body below the pale nearly straight ledge still loses material and plane definition. Around x85–300,y555–612 in the 2x frames, dark marks blur into the mid-blue band instead of defining substantial rounded or gently faceted rock faces. This remains visible in native/source, logical 128-cell and phone 32-cell repeat composites on all three backgrounds. A brightness lift alone has not resolved the lower-body criterion.',
        'Actual same-handed joins are visually clean in all four native and independent assemblies, including the inspected logical/CSS fractional phases. No port crack, bright/dark edge line, crown step or visible internal cap was observed. Broad finite-area-light/occlusion RGB differences between the native whole strip and independent singles remain and are not described as full-image RGB identity.',
        'The selected target has richer layered stone construction. The candidate now establishes sufficient major crown volume for this finite shelf; exact target stone sizes, topology and tall relief are not required. The outstanding difference is the readability of the N/S lower stone body.'
    ],
    'blockers': [{
        'rank': 1, 'id': 'lower-body-readability',
        'location': 'N/S lower front body, approximately x85–300,y555–612 in static-N.png and static-S.png at 2x, below the pale ledge around y520–555; corresponding native, logical 128-cell, phone 32-cell and repeated consumer views.',
        'effect': 'The lower mass reads as a blue band with blurred dark grooves rather than coherent modeled stone faces. The new brightness and successful crown volume do not provide useful lower-body plane/material definition; it remains a weak region at use size.',
        'desiredOutcome': 'Make substantial mid-blue lower stone faces, soft turning planes and restrained recesses readable in N/S at 128-cell and 32-cell under the common symmetric light. Preserve the successful major crown forms and E/W cutface progress. Keep the exact finite endpoint section, continuous endpoint normal/albedo bands, envelope and actual ground support unchanged. The editor may choose the native method; this does not require more height, target topology or merely a global brightness increase.',
        'criteria': ['materials-color', 'light', 'artifact-free-all4']
    }],
    'remainingDifferences': [
        'Shallower relief, simpler large-slab construction and smaller embedded pebbles than the single-view target are acceptable under the fixed 0.45 height budget; target part counts and exact topology are not requirements.',
        'The cool blue/cyan palette and restrained secondary pebble colors retain the shelf identity. The target cyan fringe/glow is not required.',
        'True W/E cutplanes remain flat and finite. Rounded target outer-edge pixels do not override the modular section. No edge/corner/end or derivative-family approval is inferred.',
        'Renderer/evaluation replay residuals and broad area-light RGB differences are retained as measured limits, without repairs or claims of universal fresh bit identity.'
    ],
    'technicalEvidence': {
        'packetBinding': 'All 597 records across packet files (586), four candidate renders and seven previews were independently hashed and matched. Exact packet/source/frozen brief/contract/criteria are bound in the supplemental manifest. No candidate bytes or prior signed artifacts were changed.',
        'nativeReopen': 'The exact source was copied byte-for-byte and reopened in background Blender 5.2.2 LTS. No editor build recipe was run and no blend was saved. Actual N/E/S/W root poses and native three-middle strips were independently rendered with saved geometry/material/light settings. Strip instances copy actual native mesh data in memory at X -1/0/+1 with one common cardinal rotation.',
        'registration': 'Native 768x1408, root [384,992.000061], unit X [512,0], depth [0,511.999939], height [0,-358.400146]; ORTHO 1.5 HORIZONTAL, registered 55.0079798 camera matrix and pixel aspect 1.22065556. Actual all-four matrices retained. Full published 384x704 frames/root [192,496] and sourceScale 2 are preserved.',
        'finiteGeometry': 'Actual W/E X ±0.5 cap vertex cycles reproduce the six-point (Y,Z) profile [(-.45,0),(.45,0),(.45,.28),(.39,.43),(-.39,.43),(-.45,.28)]. Overall bounds [-.5,-.449999988,0]..[.5,.449999988,.448884994]. Native bottom area .8999999687. Intentional .05 non-port transparent margins are retained; no full-cell opaque ground requirement is imported. No overlap or endpoint extension.',
        'endpointContinuity': '75 paired ray samples at insets 0/.0001/.005/.02/.06 use actual evaluated triangles and barycentric custom corner normals/vertex albedo. Maximum paired YZ 3.5762787e-7, normal 3.4236697e-5, albedo 3.3877967e-8. Cap faces use actual flat ±X normals and the shared native planar-cut material. Actual attribute/corner-normal signatures, material graph nodes/inputs/links and resource ownership are retained, not labels/AABBs alone.',
        'resourceAndMotion': 'Three private native mesh objects (core 9903 vertices/9794 polygons plus two embedded stones) and four native material resources. Actual POINT vertex-albedo and custom corner-normal fields inspected. No image resources, linked libraries, actions, armatures or shape keys. Frame 1 only at 12 fps, nonloop. Symmetric centered overhead area light 850W/size15 at Z18 and four equal cardinal area lights 1850W/size12 at XY radius15/Z6; no ground receiver.',
        'samplingAndPublication': 'Saved EEVEE 32, filter_size .5, transparent RGBA8 PNG, Standard/None exposure0 gamma1 dither0. Every sealed native 4x complete-frame BOX reduction exactly equals the published 2x decoded RGBA. No alpha/RGB edits, fitting, per-view changes or registration nudges.',
        'actualConsumer': 'Actual spriteFrame/groundRoot/orderPlacements/worldRasterPlan/paintWorldRaster functions imported with nearest restored after common canvas resize, then ordinary final whole-canvas CSS filtering. Independent browser captures cover all four directions, light/gray/dark, logical 128-cell, phone 32-cell and logical 0/.25/.5/.75 phases. Declared provided sheets additionally cover phone fractional phases. Exact source and loaded helper closure are frozen.',
        'frozenCurrentConsumerDistinction': 'sprite-layout.js remains SHA099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65. Packet-frozen world-sprite-raster.js SHA4ddc7495ade39f75adcce7d5400fc54326d588270b6fad9a5cca133f7df34bb0 differs from current SHA570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545. Root identified its separate shared-renderer change as c2c6062fa; this is not an editor alteration. Both code versions are frozen. The independent eight-case control produces identical encoded PNG canvases for all four joined and four independent actual cases, whose native sprite positions are integral. This is output equivalence for those inspected cases, not hash identity, general fractional-native-placement proof or authorization to version the frozen consumer contract.',
        'localSeams': 'Against independently reopened native strips, all four assemblies have zero alpha below255 on native-opaque pixels, globally and in projected finite cutface masks; minimum assembled alpha is255. N/S cutband maxRGB [1,1,1], average [.04452,.02588,.01161]. E cutface maxRGB [10,19,20], average [.65821,.49301,.44260]; W [10,18,19], average [.58683,.36356,.23112]. Whole-image native-opaque RGB differences are also retained in the evidence. Broad finite-light/occlusion residuals do not create visible local joins in the inspected cases; no full-image RGB identity is claimed.',
        'replayResiduals': 'Supplied ordinary clean replay retains one W blue-byte native difference of1, with exact published BOX output; N/E/S single native outputs match. Its strips retain three N pixels, three S pixels and one W pixel at one byte; E strip matches. My inspection-first replay retains N171/E109/S172/W128 changed native pixels, maxRGB up to5 and alpha0; published N49/E26/S43/W24 pixels, maxRGB1 alpha0. Native strips retain N1026/E807/S1080/W804 changed pixels, maxRGB13/maxAlpha9 across all four. These are unchanged recorded outputs, without retries or repairs to force equality. Independent native-opaque assembly coverage remains complete and visible joins remain clean; no universal fresh bit-identity claim.',
        'limits': 'Candidate-specific source/consumer review, not full-game, other engine or device verification. Numerical contract success does not establish appearance approval. Unchanged acceptance_contract.py is frozen/read; the strict approval gate is not run because this verdict is revise.'
    },
    'supplementalEvidence': {'path': 'reviews/round-02-independent/manifest.json', 'sha256': sha(M)},
    'approvalScope': None,
    'nextAction': 'Address the one remaining visible lower-body outcome in a new sealed candidate while preserving the frozen contract and successful crown/cutface progress. The original independent judge reviews that exact new packet. This verdict grants no family, Git, production, device or promotion approval.'
}
write(R, review)
write(S, {
    'asset': 'rock-shelf-middle', 'round': 'round-02', 'verdict': 'revise',
    'candidatePacketSHA256': sha(P), 'review': str(R.relative_to(OBJ)), 'reviewSHA256': sha(R),
    'supplementalEvidence': {'path': str(M.relative_to(OBJ)), 'sha256': sha(M)},
    'files': len(files), 'bytes': sum(v['bytes'] for v in files),
    'immutable': 'Keep review/manifest/listed resources immutable; future verdicts require a new versioned review and exact sealed packet.'
})
print(json.dumps(json.loads(S.read_text()), indent=2))
