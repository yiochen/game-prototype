from pathlib import Path
import json,hashlib
O=Path(__file__).resolve().parents[1];R=O/'reviews';P=O/'candidates/round-02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
packet=read(P/'packet.json');audit=read(R/'round02-judge-native-audit.json');files=read(R/'round02-judge-file-audit.json');checks=read(R/'round02-judge-final-checks.json');validation=read(P/'validation.json');contexts=read(R/'round02-judge-context-evidence.json');detail=read(R/'round02-judge-native-detail-manifest.json')
assert checks['allChecksPassed']and audit['allActionsEqual']and files['allPacketHashesMatch']and files['allAtlasPixelsMatch']and files['witnessReplay']['pixelsEqual']
assert len(validation['nativeCaptures'])==len(audit['samples'])==100
captures=validation['nativeCaptures'];measurements=audit['samples']
captureDelta=max(abs(c['localBounds'][p][i]-s['localBounds'][p][i])for c,s in zip(captures,measurements)for p in ['min','max']for i in range(3))
rootDelta=max(abs(c['rootMatrix'][i][j]-s['root'][i][j])for c,s in zip(captures,measurements)for i in range(4)for j in range(4))
assert all((c['clip'],c['direction'],c['frame'])==(s['clip'],s['direction'],s['frame'])for c,s in zip(captures,measurements))
parts={p['name']:p for p in audit['idleParts']};contactMatches=all(c['bounds']==parts[c['name']]['bounds']and c['groundPointsWithin002']==parts[c['name']]['groundPoints']for c in validation['supportContacts'])
playback={
 'packetSHA256':sha(P/'packet.json'),
 'method':'Actual browser review through the existing worktree Vite HTTP server using Chrome CUA. Screenshots and accessibility states were inspected in the tool session. These observations are not a saved screen recording and are not inferred from a still atlas.',
 'sealedPlayer':{
  'path':'candidates/round-02/previews/temporal-player.html','sha256':sha(P/'previews/temporal-player.html'),
  'url':'http://127.0.0.1:4178/prototypes/sushi-loop/assets/refinement/objects/garbage-sofa/candidates/round-02/previews/temporal-player.html',
  'directions':['N','E','S','W'],'sofaFrameDisplayed':[224,288],'nativeFrame':[896,1152],
  'observedStates':[
   {'background':'gray','elapsedMs':25174,'highlightedWraps':25,'highlightedIndex':2,'clearanceIndex':11,'terminalHold':True,'presentations':303,'allDecoded':True},
   {'background':'gray','afterReplay':True,'elapsedMs':277,'highlightedIndex':3,'clearanceIndex':3,'terminalHold':False,'visual':'All four facings visibly separate into individual source-role pieces.'},
   {'background':'gray','elapsedMs':5328,'highlightedWraps':5,'highlightedIndex':3,'clearanceIndex':11,'terminalHold':True,'presentations':64},
   {'background':'dark','afterReplay':True,'elapsedMs':275,'highlightedIndex':3,'clearanceIndex':3,'terminalHold':False,'visual':'Four facing streams remain readable against dark; no halo or disappearing surfaces.'}
  ],
  'visualResult':'Repeated highlighted wraps are subtle and continuous without root travel, color flicker or texture swimming. Clearance has the original distinct translation/lift/yaw/shrink progression; its small opaque frame11 pieces hold instead of looping, fading or becoming empty. Light/gray/dark static full-frame sheets were separately inspected at logical and phone size.'
 },
 'registeredFloorPlayer':{
  **contexts['temporalPlayer'],
  'observedStates':[
   {'clip':'highlighted','elapsedMs':13262,'index':3,'highlightedWraps':13,'terminalHold':False,'allDecoded':True},
   {'clip':'highlighted','elapsedMs':22213,'index':2,'highlightedWraps':22,'terminalHold':False,'allDecoded':True},
   {'clip':'clearance','elapsedMs':6077,'index':11,'terminalHold':True,'allDecoded':True},
   {'clip':'clearance','afterReplay':True,'elapsedMs':226,'index':2,'terminalHold':False,'allDecoded':True}
  ],
  'visualResult':'All four facings observed together on the unchanged registered cream floor beside the unchanged human. The highlight remains seated through repeated wraps. Clearance exposes floor between parts and finishes with opaque scattered fragments; no substitute transparent endpoint. The literal catalog root relationship and uniform context scale remain fixed.'
 },
 'playbackPolicyVerified':'Both HTML players use the sealed 12 ordered moving phases at 12fps, elapsed-time modulo12 for highlighted and min(11,index) for clearance. Full native frames are uniformly displayed; no alpha-fit, recolor or frame substitution.',
 'limits':['No persisted video or browser screenshot file was generated; actual observations and screenshot inspections are recorded in the tool session. Reopenable players and their exact frame inputs are hash-bound here and in the context manifest.','The source original preparation player was unavailable through file navigation; no claim of original temporal observation is made. Original numeric animation and phase images were independently audited before editor dispatch. Candidate actual temporal inspection is completed.']
}
save(R/'round02-judge-playback-observations.json',playback)
manifest={'packetSHA256':sha(P/'packet.json'),'scope':'Independent round02 judge supplemental evidence only. All files reside under reviews/. Sealed packet, native project, selected original delivery/validation, raw frames, atlases and production resources were not modified.','files':[{'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(R.glob('round02*'))if p.is_file()and p.name!='round02-judge-supplement-manifest.json']}
save(R/'round02-judge-supplement-manifest.json',manifest)
inspected=sorted(set(v['path']for group in ['candidateRenders','previews']for v in packet[group].values()))
coverage=[]
for group in ['candidateRenders','previews']:
 for name,v in packet[group].items():
  path=v['path']
  if group=='candidateRenders':method='Direct complete native idle frame; enlarged exact-pixel native detail; logical/phone three-background sheet and four-view sheet.'
  elif name=='temporal-player':method='Actual browser playback, including repeated highlighted wraps and clearance one-shot opaque terminal hold in all four facings.'
  elif any(clip in name for clip in ['highlighted','clearance'])and 'three-backgrounds'in path:method='Every phase on all three backgrounds at logical/phone size through all exact crop rectangles in round02-judge-file-audit.json; native details and complete native atlases also inspected.'
  else:method='Direct saved presentation inspection. Aliases resolve to the same inspected hash-bound file.'
  coverage.append({'packetField':group+'.'+name,'path':path,'sha256':v['sha256'],'method':method})
review={
 'asset':'garbage-sofa','round':2,'verdict':'approve','candidatePacketSHA256':sha(P/'packet.json'),
 'frozenBriefSHA256':sha(O/'brief.json'),'fixedTargetSHA256':sha(O/'inputs/target.png'),
 'selectedEvidence':{
  'delivery':{'path':'delivery-round02.json','sha256':sha(O/'delivery-round02.json')},
  'deliverySnapshot':{'path':'candidates/round-02/delivery.snapshot.json','sha256':sha(P/'delivery.snapshot.json')},
  'validation':{'path':'candidates/round-02/validation.json','sha256':sha(P/'validation.json')},
  'nativeProject':{'path':'source/round-02.blend','sha256':sha(O/'source/round-02.blend')},
  'selectionNote':'The original delivery snapshot and original validation are selected. delivery-compat-v1 is an unselected metadata draft, not a replacement validation. Original validation.nativeCaptures is a measured100-record list.'
 },
 'inspectedFiles':inspected,'packetCoverage':coverage,
 'additionalInspectedEvidence':{
  'nativeFrames':[{'path':x['path'],'sha256':x['sha256']}for x in files['nativeFrames']],
  'nativeAtlases':[{'path':x['path'],'sha256':x['sha256']}for x in files['atlases']],
  'diagnostics':[{'path':str(p.relative_to(O)),'sha256':sha(p)}for p in [P/'underside.png',P/'support-contact.png']],
  'nativeFrameInspection':'All100 native phase PNGs inspected through all28 native-pixel diagnostic crop pages, plus every logical/phone/background phase through72 exact presentation crops. Diagnostic alpha crops are for surface inspection only; registration uses complete fixed frames and measured roots. All12 whole original-layout atlases were inspected, and each of their100 regions was independently compared pixel-for-pixel to its raw frame.',
  'nativeDetailManifest':{'path':'reviews/round02-judge-native-detail-manifest.json','sha256':sha(R/'round02-judge-native-detail-manifest.json')},
  'contextManifest':{'path':'reviews/round02-judge-context-evidence.json','sha256':sha(R/'round02-judge-context-evidence.json')},
  'contextInspection':'All15 supplemental native/logical/phone context outputs directly inspected: adjacent repeated sofas N/E/S/W and the literal catalog example. Actual all-facing floor motion was independently observed through the bound floor player.'
 },
 'scores':{'shapeVolume':8,'color':8,'lightingHighlights':8,'materialDetail':8,'artifactFreeReadability':8},
 'scoreInterpretation':'Comparative judgments against the original native snapshot and fixed target, not a numerical approval threshold. All five dimensions apply.',
 'observations':[
  {'criterion':'shapeVolume','finding':'The source hard bevelled slabs are substantially improved by native puffy back pillows, bowed/compressed seat volumes, continuous rounded arm ends and a credible wood understructure. Piping follows these surfaces. N/E/W continue the same construction with a paneled rear and side repairs; they do not read as view-specific substitutes.'},
  {'criterion':'color','finding':'Warm faded rose upholstery, the contrasting cream replacement seat, ochre repair cloth and honey-brown frame/rubbish retain the source identity and move toward the chosen target. The replacement seat stays clearly distinct on light, gray, dark and cream floor.'},
  {'criterion':'softLightHighlights','finding':'Broad soft highlights describe the rounded cloth and wood. Lower cloth and rail surfaces remain readable without the source dead dark band, blown rims or hard faceted steps. The shared cardinal-symmetric native lights give coherent warmth in all four rotations and no directional floor shadow.'},
  {'criterion':'materialDetail','finding':'Raised native piping, stitched patch, opened seat tear, cream stuffing/spring and restrained cloth wear provide useful discarded-furniture character. Cloth, cotton and wood read as different surfaces at logical size. At phone size the patch/tear and replacement seat remain legible while fine stitches appropriately recede.'},
  {'criterion':'artifactFreeNativeOutput','finding':'No material intersections, broken corners, coplanar flicker, unintended black holes, raster halos, exposed target cards or frame clipping were found in the100 phases, enlarged details, underside/contact views and temporal streams. Primary parts expose modeled surfaces cleanly during separation. Small cotton/patch pieces separate on the original explicit role trajectories; that separation is preserved animation, not an accidental unparented detail.'},
  {'criterion':'contextAndMotion','finding':'Registered floor/human and adjacent repetitions retain the intended substantial2x2 obstacle scale. Supplemental E/W repetition and literal catalog placement close the limited S/N-only and different human-position coverage of the sealed context sheets. Actual highlighted playback crosses well over three wraps without root drift; clearance is a one shot and holds small opaque debris at the original terminal phase.'}
 ],
 'blockers':[],
 'remainingDifferences':[
  'Cushions and arms are more regular and less deeply rumpled than the painted target; the target has more irregular compression, sharper cloth folds and more abundant torn/stuffed areas. The candidate still meets the frozen soft upholstered-volume and discarded-character outcomes.',
  'The native design uses restrained low-contrast wear, cleaner piping and a narrow seat tear instead of reproducing the target stain/stitch count or its extra back/arm tears. Fine surface detail recedes more at phone size; the major worn cues remain readable.',
  'Target framing, enlarged apparent scale, orange edge halo and incidental imagegen surface noise were not copied. Registered source projection and animation semantics take precedence.',
  'Thin native trim/repair solids include some zero-area bevel corner faces and evaluated capped curve details report boundary loops. Main mesh solids have no nonmanifold edges, and no corresponding visible shipping artifact was found. Approval does not claim every evaluated detail is a single watertight mesh suitable for an unrelated3D export.'
 ],
 'technicalEvidence':{
  'inspectionAuthority':'Original independent source audit and criteria were saved before editor work. Applied the exact root-frozen brief including semantic support regions and useful topology freedom. No old mesh-count/slab-shape aesthetic requirement was introduced.',
  'integrity':{'packetReferenceCount':828,'allCurrentPacketReferencesMatch':checks['packetReferenceRecheck']['allMatch'],'briefProjectDeliveryValidationHashesUnchanged':True},
  'originalValidationCrossCheck':{'nativeCaptures':100,'orderedClipFacingFrameLabelsMatchIndependentAudit':True,'boundsMaxAbsoluteDifference':captureDelta,'rootMatrixMaxAbsoluteDifference':rootDelta,'supportContactRecordsMatchIndependentGeometry':contactMatches},
  'capture':checks['capture'],'rootMatrices':checks['rootMatrices'],'envelopes':checks['unions'],'mainBodyWidth':checks['mainBodyWidth'],'supports':checks['supports'],'rubbishGround':checks['rubbishGround'],'rasterClipCheck':checks['rasterClipCheck'],
  'animation':{'originalNativeActionsCompared':60,'allOriginalCurveHashesEqual':audit['allActionsEqual'],'integerFacingSamples':100,'fractionalSamples':91,'fractionalSampleStepFrames':.25,'driverMaxErrors':audit['driverErrors'],'highlightedFrame1To13ClosureMaxMatrixError':audit['closureMaxMatrixError'],'semantics':'Distinct original semantic carriers preserve local pulse, outward radial trajectories, signed yaw cohorts, role lift order and uniform shrink to0.1; root has facing rotation only. No replacement root bob, color blink, alpha fade or empty terminal.'},
  'nativeConstruction':{'counts':{'EMPTY':21,'MESH':32,'CURVE':41},'explanation':'20 original semantic owners are preserved as animated native carriers with rebuilt editable geometry. Topology counts are evidence, not frozen aesthetic locks. The native source contains no raster images or external libraries/fonts; all scene geometry belongs to the sofa collection.', 'materialClosure':checks['materialClosure']},
  'illumination':{'lights':audit['lights'],'world':audit['render']['worldNodes'],'finding':'Four equal45W/size4 cardinal soft fills at radius3,z2.5 plus centered105W/size4 overhead,z4.5; uniform world. Same warm color and shared scene across rotations. No receiving floor geometry is in native captures.'},
  'atlas':{'nativeFrames':100,'originalLayoutAtlases':12,'allAtlasRawFramePixelsEqual':files['allAtlasPixelsMatch'],'layout':'idle1x1; highlighted/clearance6x2, exact896x1152 cells,12fps.'},
  'replay':files['witnessReplay'],
  'actualPlayback':{'path':'reviews/round02-judge-playback-observations.json','sha256':sha(R/'round02-judge-playback-observations.json')},
  'contexts':{'allFourFacingsRepeated':True,'literalCatalogExample':True,'nativePitch':256,'logicalPitch':128,'sourceScale':2,'literalSofaRootNative':[512,768],'literalHumanRootNative':[1152,640],'wholeFramesIdentityComposited':True,'floorAndHumanInputsMatchOriginal':checks['contextInputsMatchOriginal'],'all12ExcludedFloorSpritesUnchanged':all(x['pass']for x in checks['excludedFloorIntegrity'])},
  'limits':[
   'Independent fresh Blender raster replay was one selected witness: clearance/E/runtime005 (authored6), RGBA-identical to shipping. This does not establish PNG identity or fresh rerender identity for every phase. All100 native poses and91 local intermediate samples were independently measured; all shipping phase pixels were inspected and compared with all atlas regions.',
   'Intermediate native samples are quarter-frame evaluations, not a mathematical proof over every real-valued instant. Exact preserved source action curves plus sampled bounds and temporal inspection support the frozen contract.',
   'The supplemental floor/repetition/literal-placement evidence was generated only under reviews/ from the complete exact sealed frames and unchanged floor/human. It supplements the sealed packet and does not amend its bytes or select the compatibility draft.',
   'This approval binds only the exact reviewed packet/project/original delivery/validation and grants no production, publishing or unrelated asset approval.'
  ]
 },
 'supplementalEvidence':{'path':'reviews/round02-judge-supplement-manifest.json','sha256':sha(R/'round02-judge-supplement-manifest.json'),'allInputOutputHashes':'Context, native-detail and file-audit manifests list exact inputs, source rectangles, registration, output hashes and atlas/frame comparisons. The supplement manifest binds every independent round02 judge script, report and generated image/player.'},
 'decision':'Approve the sealed round02 candidate. It visibly improves native form, warm palette, soft illumination and useful construction detail toward the fixed target while satisfying the frozen functional contract. Required inspection is complete and no material blocker remains.'
}
assert contactMatches and captureDelta==0 and rootDelta==0
assert len(review['packetCoverage'])==sum(len(packet[k])for k in ['candidateRenders','previews'])
save(R/'round-02.json',review)
print(json.dumps({'verdict':review['verdict'],'path':str((R/'round-02.json').relative_to(O)),'sha256':sha(R/'round-02.json'),'packetSHA256':review['candidatePacketSHA256'],'uniqueRequiredFiles':len(inspected),'packetAliasRecords':len(coverage),'nativeFrames':len(files['nativeFrames']),'atlases':len(files['atlases']),'supplementalFiles':len(manifest['files']),'validationCaptureBoundsDelta':captureDelta,'validationRootDelta':rootDelta,'supportContactRecordsMatch':contactMatches},indent=2))
