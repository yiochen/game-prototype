import json,hashlib,math
from pathlib import Path
b=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-noor');c=b/'candidates/round-02';p=json.loads((c/'packet.json').read_text())
h=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
v=json.loads((b/'reviews/round02-verification.json').read_text());s=json.loads((b/'reviews/round02-independent-summary.json').read_text());physical=json.loads((b/'reviews/round02-independent-physical-audit.json').read_text());sourcePhysical=json.loads((b/'reviews/round02-independent-approved-source-audit.json').read_text());fresh=json.loads((b/'reviews/round02-fresh-independent-render.json').read_text());controls=json.loads((b/'reviews/round02-video-controls-independent.json').read_text());mapping=json.loads((b/'reviews/held-food-v2-visible-mapping.json').read_text());sens=mapping['fixedMappingSensitivity']
assert h(c/'packet.json')=='1fd6c78167a41a27aa7f4aeb79acc3729c3887476af1755bb5007b5c5e7544c0'
assert h(b/'brief-v3-held-food-semantic-contact.json')=='17a1d8894c36dd8b8beaaf892662c5a9acac4b9012f9e6574da3d46c0b9af98e'
assert h(b/'reviews/proposedcriteria-held-food-v2.json')=='7c2fa530df93c9d259675d9bb30ce119bdf3bfbb9c69736051e3d1841729a74e'
assert not physical['mismatches'] and not sourcePhysical['mismatches']
assert all(not v[k] for k in ['hashMismatches','atlasCellMismatches','singleSheetCellMismatches','pairedSheetCellMismatches','phoneCellMismatches'])
assert controls['phoneExactCellMismatches']==[]
required=[x['path'] for d in ['candidateRenders','previews'] for x in p[d].values()]
allfiles=sorted({x['path'] for d in ['files','candidateRenders','previews'] for x in p[d].values()})
readOnlyBrowser={
 'nativePlaybackPage':'candidates/round-02/playback.html','actualBrowserViewport':[1200,1155],
 'nativePageVideos':32,'readyState4':32,'mediaErrors':0,'playbackRate':1,
 'nativeCSSFrame':[192,320],'phoneCSSFrame':[48,80],
 'loopingNativeIdleWorkHold':12,'endedNativeLoadAtOneSecond':4,
 'loopingPhoneSourceAndCanonicalHold':8,'endedPhoneSourceAndCanonicalLoadAtOneSecond':8,
 'servingPlaybackPage':'reviews/round02-judge-context-playback.html','servingVideos':8,
 'servingCSSFrame':[256,320],'servingReadyState4':8,'servingErrors':0,
 'servingEndsAtOneSecond':8,'servingLoop':False,
 'method':'Actual Play controls and screenshots inspected in Chrome; DOM readback confirmed loaded media, rate, dimensions and end/loop states. Actual sealed files also fully decoded. Agent-created tab closed after inspection.',
 'phoneEvidenceQualification':'Four declared390x844 PNGs are native composed proofs, independently pixel-verified at48x80 character scale. These are not browser390x844 screenshots. Neither the submitted optional viewport timeout report nor this desktop playback check is represented as a portrait browser capture. Actual catalog phone/landscape checks belong to coordinator post-promotion integration.'}
(b/'reviews/round02-browser-independent-observations.json').write_text(json.dumps(readOnlyBrowser,indent=2)+'\n')
r={
 'asset':'chef-noor','round':2,'scope':'Canonical held-food dependency closure only; approved body aesthetic direction remains approved.',
 'verdict':'approve','candidatePacketSHA256':h(c/'packet.json'),
 'candidateProjectSHA256':p['files']['candidateProject']['sha256'],
 'approvedBodyProjectSHA256':'8225bd9a7269434a678691699ee7a0827469f39348ab37ce0df6afc23e8d113c',
 'frozenBrief':'brief-v3-held-food-semantic-contact.json','frozenBriefSHA256':h(b/'brief-v3-held-food-semantic-contact.json'),
 'criteriaVersion':'v3-held-food-semantic-contact (frozen original v2 judge proposal)',
 'criteriaSHA256':h(b/'reviews/proposedcriteria-held-food-v2.json'),
 'criteriaStatus':'Applied actual frozen v3 qualityCriteria and coordinatorResolution. The embedded proposal status/name is historical. No new art direction or score threshold was introduced.',
 'inspectedFiles':allfiles,
 'inspectionCoverage':{
  'hashEntriesChecked':894,'allBoundResourcesHashVerified':True,'hashMismatches':0,
  'nativeHeroes':4,'nativeFrames':192,'activeFoodFrames':96,'hiddenFoodFrames':96,
  'nativeAtlases':16,'declaredPreviews':122,'allFrameBackgroundSheets':48,
  'pairedSourceCanonicalBackgroundSheets':24,'native12fpsMP4s':16,'sourceCanonicalServingMP4s':8,
  'phoneProofPNGs390x844':4,'phoneServingContextPNG':1,'nativeContactExtremaPNGs':4,
  'sameInputControlPhases':12,'sameInputControlPNGs':72,
  'independentlyReopenedCandidatePhases':192,'independentlyReopenedApprovedSourcePhases':192,
  'independentlyRenderedCandidateFrames':2,'allDeclaredRenderAndPreviewPathsCovered':set(required)<=set(allfiles),
  'pathInterpretation':'inspectedFiles uses exact packet-relative paths. Every listed path was integrity-inspected. Pixel/source/playback inspection is described below; an integrity-only check is not claimed to be visual judgment.',
  'methods':[
   'All894 packet records independently hashed. Brief, original/backup, target, canonical dependency, editable candidate, capture data, resources and previews retain their sealed bytes.',
   'All192 native frames viewed across four states/facings on light/gray/dark through12 judge-created verified montages. Every cell of48 declared all-frame sheets and24 paired source/canonical sheets independently matched its raw registered composite; all16 atlases independently matched192 raw cells. Four hold000 native heroes are included in these inspected cells.',
   'Directly inspected target, extracted exact canonical packed artwork, four-view, repeated/comparison, all three background overviews, all four contact-extrema figures, all four native390x844 phone proofs, phone serving context, and fresh radiance control comparisons. Every phone source/canonical cell independently matched the corresponding48x80 raw-frame composite.',
   'All24 actual submitted MP4s independently probed and fully decoded:12frames at12fps each. Each native clip was checked against its corresponding native composite. All96 source/canonical serving frames were inspected in a decoded montage. Actual native/phone playback and all8 serving clips were played in Chrome; load ends held and does not loop.',
   'Fresh read-only background Blender reopened exact8ed24395 candidate and exact8225bd9a approved source separately. Each independently evaluated192 phases and78 protected meshes per phase. Coordinate/normal/world-coordinate hashes match the approved-source records in all14976 comparisons for each reopened file. No project save occurred.',
   'Candidate independently resampled food/root/driver pointers, UV, packed bytes, light/camera/shader and hand endpoints at192 phases. Two additional native64-sample Cycles GPU frames (hold N000 and load E005) were freshly rendered from the exact saved candidate without saving it and reproduced delivered frames within1RGB level and identical alpha.',
   'Read submitted technical phase/parity/closure/semantic/replay/radiance/browser evidence and independently checked actual control pixels. Editor self-rating content was not read or used; its declared file received integrity inspection only.'
  ],
  'excludedFromJudgmentEvidence':[{'path':'editor-inspection.json','reason':'Declared preview hash verified only; editor self-rating/content intentionally excluded from independent art judgment.'}]
 },
 'scores':{'shapeVolume':8,'color':8,'lightingHighlights':8,'materialDetail':8,'artifactFreeReadability':9},
 'scoreExplanations':{
  'shapeVolume':'Approved body score retained. The separate2D dish keeps canonical aspect, source semantic occupied width and support; no claim of newly modeled food volume.',
  'color':'Exact canonical salmon/rice/plate RGBA is preserved, while the approved mediumtan/green/blueblack/ivory/plum/dark-shoe identity remains intact.',
  'lightingHighlights':'Approved native light/world/material treatment is structurally unchanged. Changed-food emission produces measured nonzero secondary body color residuals; actual native/control comparisons show no material worsening.',
  'materialDetail':'Approved body construction remains unchanged. Canonical fish striations, rice and plate read cleanly at the fixed native/use scales with original Linear/CLIP/Emission1 graph.',
  'artifactFreeReadability':'All active/hidden frames, backgrounds and phone/serving contexts retain stable source contact and occlusion without a new rectangle, fringe, flip, food leak, crop or temporal defect.'
 },
 'criteriaFindings':[
  {'rank':1,'id':'exact-canonical-art-and-aspect','result':'pass','evidence':'Fresh main-source extraction is exact4389d1e6607e6afbfb3cd03594afb4196394b14c5ee6ca6a92fb534cd3b9ebe4 at731x505. Full0..1 UV and one frozen aspect-correct quad; no additional crop, paint, alpha/color grade or food variant. Exact artwork is recognizable in E/S and the source-visible portion of W.'},
  {'rank':2,'id':'same-visible-plate-size-and-support','result':'pass','evidence':'One global local-vertex/fullUV map matches the frozen source-specific values within Blender float storage. Alpha128 uses exclusive729px canonical support, not730, and preserves44.0785844logicalpx occupied width. Independently evaluated96 live phases preserve semantic bottompoint to max3.2490453e-9world component difference; palms have0 world endpoint difference. Supplied full-vector audit reports max2.28882e-5native pixels and width8.57390e-9world. Original driver target/expressions and0.6 camera-ray law are exact; dormant hidden matrices are excluded from active-placement authority.'},
  {'rank':3,'id':'supported-stable-readable-food','result':'pass','evidence':'All96 live hold/load frames remain source-supported without visible new floating/sliding, wrong-facing flip, alpha card/fringe, contact break or material extra face/hand occlusion. Canonical visible height adds1.0519423logicalpx at fixed width. S lower-face overlap, E/W profile/hair overlap and strong N concealment are inherited and remain acceptable. All96 idle/work frames keep food hidden. Actual load remains out-and-back ending held at1second; no belt release is invented.'}
 ],
 'observations':[
  {'area':'Semantic measurement','evidence':'Primary alpha>=128 is used only to measure support; actual canonical alpha and fullUV remain untouched. Source support[16,237,1238,1051], bottom midpoint[633.5,1051]; canonical support[1,1,730,504], bottom midpoint[367.5,504]. Old padded crop/nominal.35 is provenance only.'},
  {'area':'Sensitivity convention','evidence':'Alpha64/192 retain the exact frozen map sensitivity. Width offsets are respectively+0.06046445 and-0.06046445logicalpx. Alpha64 bottom camera-basis components are[-0.08433851,-0.06046445]logicalpx; Euclidean length is0.10378logicalpx, rather than each component being0.10378. Alpha192 components are[-0.00635817,-0.03607086]. This matches the frozen proposed fixed map; the primary128 support is effectively exact. The proposal wording under0.1 describes component magnitudes and must not be restated as an under0.1 Euclidean result.'},
  {'area':'Body/knife invariance','evidence':'Fresh actual original and candidate geometry audits independently matched14976 coordinate/normal comparisons each. Protected static scene/action/rig/material/light/camera keys match, with only the frozen food image/quad/UV and9 derived food-only fields differing. The display quad is excluded from physical bounds. No body redesign or extra runtime variant is present.'},
  {'area':'Radiance controls','evidence':'Independently checked12phases of source/source, candidate/candidate and restored-old-food/source control pairs; maximum same-input RGB difference1/255 and alpha0. Actual changed-input hold/load residuals are separately reported. Conservative opaque-body regions outside full-quad union+8px show changed-input maxima3–8/255, not bit-identical bodyRGB. Source-restored controls and unchanged physical/shader/light state isolate these from a body-edit claim; direct native views show no material style/readability defect.'},
  {'area':'Phone and browser evidence','evidence':'Native390x844 phone proofs and exact48x80 cells are present. Actual desktop Chrome playback showed32 ready videos at rate1 without media errors; native videos are192x320CSS and phone comparisons48x80CSS. The additional8 source/canonical serving clips played and ended held without errors. No portrait browser screenshot is claimed. Actual catalog phone/landscape served-atlas checks remain coordinator integration work after promotion.'}
 ],
 'blockers':[],
 'remainingDifferences':[
  'Canonical food artwork/aspect replaces the older1254px padded packed food. At preserved occupied width its visible height is30.4136186logicalpx versus29.3616763 (+1.0519423); this required aspect change is accepted after all-frame contact/occlusion review.',
  'Changed canonical Emission1 food radiance yields small nonzero bodyRGB residuals above same-input noise (measured conservative body maxima up to8/255). No blanket exact bodyRGB identity is claimed; immutable body/rig/material/light/camera state and restored-old-food controls pass.',
  'The original separate2D food remains largely concealed in N, partly hair-occluded in E/W and overlaps the lower face in S. Load still ends held with no new released dish/belt travel. These source behaviors are preserved.',
  'Native phone-scale proofs and desktop playback are approved asset evidence. Actual catalog390x844 and landscape integration screenshots are not part of this candidate approval and remain for the coordinator after promotion.'
 ],
 'technicalEvidence':{
  'canonicalPackedSHA256':s['packedImageSHA256'],'canonicalImageSize':[731,505],'canonicalUV':'Full0..1',
  'globalMapping':'Frozen exact mesh-local vertex map; source parent/actions/transforms/drivers unchanged.',
  'driverRoot':'chef_noor__ground_root.001','yawExpression':'-facing','locationXExpression':'-sin(facing)*0.39319298125871605','locationYExpression':'-cos(facing)*0.39319298125871605','planeZLocal':0.27531668543815613,'worldCameraRayDepthBias':0.6,
  'foodDriversExact':s['foodDriversExact'],'foodShaderExact':s['foodMaterialExact'],'lightsExact':s['lightsExact'],'cameraExact':s['cameraExact'],
  'all192VisibilityExact':s['all192VisibilityExact'],'activeSemanticFrameCount':96,
  'maxSemanticPointComponentDifferenceWorld':s['maxSemanticPointComponentDifferenceWorld'],'maxPalmBoneEndpointComponentDifferenceWorld':0,
  'approvedSourcePhysicalComparisons':sourcePhysical['physicalMeshComparisons'],'candidatePhysicalComparisons':physical['physicalMeshComparisons'],'physicalMismatches':0,
  'hidden96FrameMaxRGBA':v['hiddenFrameMaxRGBA'],'atlasCellMismatches':0,'sourceCanonicalSheetCellMismatches':0,'phoneCellMismatches':0,
  'videoFrameCount':12,'videoFPS':12,'nativeVideoFilesDecoded':16,'servingVideoFilesDecoded':8,
  'maxNativeVideoMeanRGBCompressionDifference':max(max(x.get('meanRGBErrorVsCorrespondingNativeComposite',[0])) for x in controls['videos']),
  'independentlyFreshRenderedFrames':fresh['renders'],'browser':readOnlyBrowser,
  'sourceAndCandidateProjectSavedDuringReview':False
 },
 'supportingJudgeEvidence':[]
}
for path in ['reviews/round02-verification.json','reviews/round02-independent-summary.json','reviews/round02-native-independent-inspection.json','reviews/round02-independent-physical-audit.json','reviews/round02-independent-approved-source-audit.json','reviews/round02-fresh-independent-render.json','reviews/round02-fresh-independent-hold-N-000.png','reviews/round02-fresh-independent-load-E-005.png','reviews/round02-video-controls-independent.json','reviews/round02-decoded-serving-allframes.png','reviews/round02-browser-independent-observations.json','reviews/round02-judge-context-playback.html','reviews/round02-inspected-packed.png']+[x['path'] for x in v['montages']]:
 r['supportingJudgeEvidence'].append({'path':path,'sha256':h(b/path)})
assert len(r['blockers'])<=3
(b/'reviews/round-02.json').write_text(json.dumps(r,indent=2)+'\n')
print('VERDICT',r['verdict'],'REVIEW_SHA256',h(b/'reviews/round-02.json'),'INSPECTED_UNIQUE_PATHS',len(allfiles),'REQUIRED_RENDER_PREVIEW_PATHS',len(required))
