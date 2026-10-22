"""Create the independent judge's exact sealed-packet review; review files only."""
import json, hashlib
from pathlib import Path
OBJ=Path(__file__).resolve().parent.parent
ROOT=OBJ/'candidates/round03'
REV=OBJ/'reviews'
PACKET_SHA='31f601704e551f17da16a8472dcd081b04ab83f4095dc1a6d4b13e01c9533395'
assert hashlib.sha256((ROOT/'packet.json').read_bytes()).hexdigest()==PACKET_SHA
p=json.loads((ROOT/'packet.json').read_text())
entries=[v for group in ['files','candidateRenders','previews'] for v in p[group].values()]
unique={v['path']:v for v in entries}
checks=[]
for path,v in unique.items():
    actual=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    assert actual==v['sha256'],path
    checks.append({'path':path,'sha256':actual,'exact':True})
(REV/'round03-independent-integrity-evidence.json').write_text(json.dumps({'packetSHA256':PACKET_SHA,'uniqueBoundPaths':len(unique),'allExact':True,'files':checks},indent=2)+'\n')
required=[v['path'] for g in ['candidateRenders','previews'] for v in p[g].values()]
raw=[v['path'] for v in p['files'].values() if v['path'].startswith('raw-frames/')]
atlases=[v['path'] for v in p['files'].values() if v['path'].startswith('atlases/')]
controls=[v['path'] for v in p['files'].values() if v['path'].startswith('controls/')]
technical=['../../brief-v3-held-food-semantic-contact.json','../../reviews/proposedcriteria-held-food-v2.json','../../inputs/original.png','../../inputs/target.png','../../inputs/imagegen-prompt.txt','../../prompts/judge.txt','../../inputs/source-rig.json','../../source/round02.blend','../../source/round03.blend','../../source/round03-resources/canonical-salmon.png','../../source/round03-resources/historical-salmon.png','../../source/round03-recipe.json','../../source/round03-baseline.json','../../source/round03_common.py','../../source/compare_radiance_round03.py','../../source/probe_frozen_round03.py','validation.json','audit-validation.json','dependency-change.json','calibrated-radiance-validation.json','frozen-extra-approved.json','frozen-extra-candidate.json','camera.json','assetRecord.json','delivery.snapshot.json','delivery-verification.json']
inspected=list(dict.fromkeys(required+raw+atlases+controls+[x for x in technical if x in unique]))
assert set(required)<=set(inspected)
native=json.loads((REV/'round03-independent-native-evidence.json').read_text())
radiance=json.loads((REV/'round03-independent-radiance-evidence.json').read_text())
frozen=json.loads((REV/'round03-frozen-source-recheck.json').read_text())
assert frozen['allFrozenPropertiesExact']
report={
 'asset':'chef-mateo','round':'round03','verdict':'approve',
 'candidatePacketSHA256':PACKET_SHA,
 'approvedBodySHA256':'3822fb7b734408a0e176d5546cfda3213754a620382c58a691717dee56c8df3e',
 'candidateProjectSHA256':'b0e7450c0e204426a93bd798b6ba83a9d2a3d6c368987fe887370a3e7f7613f9',
 'frozenBriefSHA256':'e699452c13c421593cf1d1de45a8449222376b7cb6d71ad310b7337d4427c7ac',
 'frozenCriteriaSHA256':'1cc5468541adb3f7ea223a09febca87f3af290f77ff83f3ae47e1ea627a57ec4',
 'scope':'Narrow canonical held-food dependency closure against frozen v3 semantic-contact criteria. Approved round02 chef design is preserved; no extra Mateo variants.',
 'inspectedFiles':inspected,
 'inspectionCoverage':{
   'pathBase':'Every inspectedFiles entry is relative to candidates/round03/packet.json. Supplemental judge evidence is listed separately.',
   'integrity':f'All {len(unique)} unique packet-bound paths rehashed and matched, including exact native projects and resources. Integrity-only coverage of other bound recipe/history files is recorded separately from visual inspection.',
   'visual':'All 4 heroes and all 34 declared previews inspected. All 192 native frames inspected through exact verified all-frame sheets, with hold/load contact crops covering all 96 visible-state samples. All 16 atlas layouts/cells verified against raw RGBA frames. Four views, light/gray/dark, enlarged edges, repeated, serving work/hold/load and logical phone previews reviewed.',
   'temporal':'All 16 actual MP4 files decoded, every decoded frame inspected in judge strips, and all 16 played in the bound playback index via local Chrome. Each stream is 384x640, 12 frames, 12 fps, 1 second. All 12 idle/work/hold clips observed playing and looping; all 4 load clips observed ended at 1.0 seconds with loop false.',
   'native':'Both exact Blender sources opened without saving. Independent all-192 evaluated nonfood geometry/normal and food matrix/visibility comparison; fixed-mapping corners/support/occupied width measured. Comprehensive inspected property serializer replay confirms frozen meshes/objects/materials/rest rig/actions/capture settings. Packed canonical resource and no linked libraries verified.',
   'calibration':'All 18 A/B/C control triplets visually inspected in ungraded judge crops. Independent NumPy mask/delta recomputation exactly reproduces all 18 bound measurement rows and confirms each control image hash.'
 },
 'scores':{'shapeVolume':8,'color':8,'lightingHighlights':7,'materialDetail':7,'artifactFreeReadability':8},
 'scoreExplanation':'These retain the approved warm, softly lit cartoon chef assessment. The narrow dependency replacement preserves the approved native body and gives the held dish the exact canonical artwork, correct aspect and stable original semantic support; the source food remains an explicitly identified 2D insert.',
 'criteriaResults':[
  {'id':'canonical_food_identity','result':'pass','evidence':'Exact packed 731x505 canonical RGBA hash 4389d1e6607e6afbfb3cd03594afb4196394b14c5ee6ca6a92fb534cd3b9ebe4; full UV [0,0]..[1,1]. At logical/phone size S and E retain readable orange salmon, white rice and complete ivory plate. W keeps the original body occlusion. Light/gray/dark and enlarged views show clean alpha without a new halo, cropped rim, stretch or added grade.'},
  {'id':'source_semantic_contact_scale','result':'pass','evidence':'One global rest-quad/full-UV mapping implements the frozen alpha>=128 occupied-width and plate-bottom support correspondence. Independent visible occupied width 0.3443639037467841..0.34436396829942456 world, approximately 44.0786 logical pixels. Independent support maximum error 1.4901161193847656e-08 world; mapped-corner error 0.0. Source nominal padded .35 remains historical provenance rather than an incompatible new full-quad requirement.'},
  {'id':'occlusion_and_orientation','result':'pass','evidence':'All hold/load phases in S/E/N/W inspected at logical and enlarged contact sizes and serving context. The canonical silhouette sits at the original visible plate support. No new clipping, overlap pop or disconnected support appears relative to the approved source. N remains intentionally hidden by the body; W retains the original cheek/body overlap. Native matrices preserve Mateo visible .6 camera-toward law and yaw cancellation; no per-view fit or foreign depth law.'},
  {'id':'temporal_and_alpha_continuity','result':'pass','evidence':'All 192 samples and all 16 real playbacks reviewed. Food remains hidden during idle/work and stable during hold/load, including load endpoints. No new support/scale jump, crop or plane-rotation shimmer, halo flicker, food pop or altered source loop policy observed.'},
  {'id':'approved_body_preservation','result':'pass','evidence':'Approved tan skin, brown hair, fitted folded red headband/tie, ivory coat, blue apron, red necktie and dark footwear remain coherent in all views. Independent native comparison confirms all 62 nonfood mesh definitions/evaluated poses, weights/UV/corner normals, rig/rest/actions, material definitions and capture/light settings unchanged. Body RGB is not asserted invariant under changed emissive food: same-input control floor and observed canonical response are measured separately and the actual small response is visually acceptable.'}
 ],
 'observations':[
  'The held canonical artwork reads as the same salmon dish at gameplay scale, with its full ivory plate retained. The new full artwork aspect is respected rather than stretching to the old padded crop.',
  'The new semantic mapping preserves the source support relationship through authored bob and serving motion. Front, side and rear overlaps stay continuous. The source rear occlusion and partial west occlusion are intentional inherited behavior, not new missing-food defects.',
  'The physical chef, knife and animation remain the approved round02 native design. The food replacement introduces no visible change to silhouette, action readability, headband layering or phone-scale body identity.',
  'The changed canonical food produces a real measured nonfood RGB response above calibrated repeatability noise. Across 798734 conservative opaque nonfood screen pixels, A/B floor mean absolute channel delta is 0.000042150035764931335 and maximum 1/255; C/B observed mean is 0.21043551420122344 and maximum 13/255. These are 8-bit channel units, not percent. The 18 actual control triplets show modest local response without a global grade or material redesign.',
  'The source is an editable native 3D chef with one honestly declared 2D food plane. The exact canonical texture is packed and also present at its portable relative resource path; no linked Blender libraries are required.',
  'The assetRecord artStyle correction aligns stale historical metadata with the unchanged camera artStyle. It is metadata repair; independently inspected native scene/material/light/camera properties remain exact.'
 ],
 'blockers':[],
 'remainingDifferences':[
  'Canonical food pixels, silhouette details, full-quad aspect and allowed local emitted-light response differ from the historical cropped artwork according to the frozen dependency mapping.',
  'The food remains completely occluded in N and partially occluded in W under the unchanged source depth law. These approved-source behaviors are retained.'
 ],
 'technicalEvidence':{
  'packetIntegrity':{'uniqueBoundPaths':len(unique),'allMatch':True},
  'nativeIndependent':{k:native[k] for k in ['bodyDefinitionsExact','bodyMeshCount','actionsExact','restBonesExact','actualSceneSettingsExact','foodShaderGraphAndRayFlagsUnchanged','all192BodyEvaluationsExact','all192SourceFoodMatricesAndVisibilityExact','maximumMappedCornerWorldResidual','maximumSemanticSupportWorldResidual','visibleWidthRange']},
  'frozenPropertiesReplay':frozen['checks'],
  'normalOpenState':frozen['sources'][1]['savedState'],
  'sourceSpecificLaw':'Actual hold/load .6 camera-toward depth, source yaw cancellation and evaluated palm midpoint+[0,0,.0225] remain. Native bound residuals: depth 5.364418032005602e-08 world; prop-to-palm 2.1811248612857532e-07. Original hidden idle/work transforms retained, including hidden smaller quad scale; not forced to the visible law.',
  'nativeBoundResiduals':{'mappedCornerWorld':0.0,'semanticSupportNativePx':3.0517578125e-05,'semanticOccupiedWidthWorld':3.915288671052508e-08,'matrixDelta':0.0,'footDelta':0.0,'bodyBoundsDelta':0.0},
  'capture':'35 degree registered orthographic, 384x640 native / 192x320 logical / root [96,248], scale 2, 6x2 atlases 2304x1280, original 12-frame cohorts and 12fps, S0/E+90/N180/W-90. Foot/body/contact envelopes equal approved source; prop reach is assessed separately from body clearance.',
  'radianceMask':'Intersection alpha>=128 of A/B/C excluding union of projected old/new entire food quads dilated 4 native pixels. Conservative opaque nonfood screen mask, not semantic per-material segmentation. Observed C/B response includes calibrated render noise; no exact bodyRGB or pure-radiance-only claim.',
  'sameInputCalibration':radiance['sameInputCalibration'],'canonicalActualRGBDelta':radiance['canonicalActualRGBDelta'],
  'metadata':'Only assetRecord artStyle changed relative to round02 assetRecord, matching current camera metadata. Native frozen definition replay passes.'
 },
 'supplementalReviewEvidence':[
  'reviews/inspect_round03_semantic.py','reviews/round03-independent-native-evidence.json','reviews/round03-independent-native-inspection.log','reviews/recheck_round03_frozen.py','reviews/round03-frozen-source-recheck.json','reviews/verify_round03_pixels.py','reviews/round03-independent-pixel-evidence.json','reviews/round03-decoded-videos-idle.png','reviews/round03-decoded-videos-work.png','reviews/round03-decoded-videos-hold.png','reviews/round03-decoded-videos-load.png','reviews/verify_round03_radiance.py','reviews/round03-independent-radiance-evidence.json','reviews/round03-control-triplets-hidden.png','reviews/round03-control-triplets-N.png','reviews/round03-control-triplets-E.png','reviews/round03-control-triplets-S.png','reviews/round03-control-triplets-W.png','reviews/round03-independent-integrity-evidence.json'
 ],
 'approvalBinding':'Approval applies only to exact sealed packet bytes and the frozen v3 dependency scope. No candidate edits, regeneration, extra runtime variants or body redesign are included. Judge changed reviews only.'
}
(REV/'round03.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'verdict':report['verdict'],'packetSHA256':PACKET_SHA,'uniqueBoundPaths':len(unique),'requiredHeroPreviewPaths':len(required),'requiredHeroPreviewCoverageComplete':set(required)<=set(inspected),'inspectedPaths':len(inspected),'reviewSHA256':hashlib.sha256((REV/'round03.json').read_bytes()).hexdigest()}))
