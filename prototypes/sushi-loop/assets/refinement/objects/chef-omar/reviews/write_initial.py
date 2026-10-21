import pathlib,json,hashlib
B=pathlib.Path(__file__).resolve().parent.parent
R=B/'reviews'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def write(n,d):(R/n).write_text(json.dumps(d,indent=2)+'\n')
brief=json.loads((B/'brief.json').read_text());audit=json.loads((R/'source-native-inspection.json').read_text())
viewed=['inputs/original.png','inputs/target.png','inputs/family-concept.png','../../style/warm-soft-reference.png','reviews/source-native-four-view.png','reviews/source-catalog-overview.png','reviews/source-runtime-variants-overview.png','reviews/source-target-intended-size.png']
write('initial.json',{
 'asset':'chef-omar','stage':'independent-source-target-calibration','candidateGraded':False,
 'independence':{'freshJudge':True,'editorProposalsRead':False,'otherObjectAestheticVerdictsRead':False,'ownership':'reviews/ only'},
 'inspectedImages':[{'path':p,'sha256':sha(B/p),'inspection':'actually viewed'} for p in viewed],
 'sourceEvidence':{'blend':brief['source']['project'],'blendSHA256':audit['sourceSHA256'],'collection':audit['sourceCollection'],'objectCount':len(audit['objects']),'method':'Opened source .blend read-only in Blender 5.2.2; isolated actual Omar collection; applied all 192 native catalog action/facing frames; rendered idle frame00 in every facing using the registered 35-degree camera at scale2. No blend save.','audit':'reviews/source-native-inspection.json','script':'reviews/inspect_source.py','cameraWorldMatrixMaxDifferenceFromRecorded':audit['cameraWorldMatrixMaxDifference'],'cameraProjectionMatrixMaxDifferenceFromRecorded':audit['cameraProjectionMatrixMaxDifference'],'visualCoverage':'4 native idle recaptures plus original runtime frame05 in every catalog and supplemental clip/facing, via hash-listed overview crops. This is representative baseline inspection, not visual review of all baseline animation frames.','overviewManifest':'reviews/source-overview-manifest.json','sourceRig':'inputs/source-rig.json','sourceCamera':'inputs/source-camera.json'},
 'sourceObservations':[
  'Omar is already recognizable through the amber/tan head and ears, cropped blue-black fringe, two-lobed dark moustache, ivory toque/coat, teal bib/apron/necktie, short dark shoe ends and large-head proportions.',
  'The native source toque reads as a tall stepped stack with broad almost-white flat zones; internal crown and band shaping are difficult to perceive. Source torso and cuffs have conspicuous angular planes, the apron is a flat stack of rectangular panels, and dark hair has some merged dark areas.',
  'Native source S is the front, N is back, E and W are side profiles. A single frontal target cannot establish unseen back/side styling, so these views must be judged for coherent design and clear form rather than imagined reference details.',
  'Serving views rely on evaluated hands, knife/work attachments and camera-facing salmon/cucumber food cutouts. Their existing visibility and transfer behavior are part of the locked action contract, independent of allowed body-model improvements.'
 ],
 'targetUsefulImprovements':[
  'Broad rounded toque lobes and soft recessed fold transitions give the hat a crafted fabric volume; a curved lower band separates hat from fringe.',
  'Rounded fringe clumps, ears, cheeks/nose and twin moustache lobes give the head a friendly toy-like form while retaining identity.',
  'Layered collar, tie knot/tails, rolled cuffs, subtle buttons, dimensional apron bib/pocket/waist and restrained hem seams make the compact clothing construction easier to read.',
  'Warm ivory, rich teal and amber skin are separated by soft broad light, with controlled highlights and readable dark blue-black hair and shoes.'
 ],
 'targetLimits':[
  'The generated target is 971x1619 and occupies a substantially larger share of its canvas than the registered 384x640 source. Its apparent size, more frontal presentation and additional exposed shoes are not proof of compliant framing, camera, height or feet registration.',
  'The generated target has bright jagged edge/halo pixels and warm rim emphasis. Do not copy those artifacts or introduce a preferred horizontal light direction.',
  'Target sheen and stitching are subordinate to intended-size silhouette and garment readability. Exact lobe, pocket, button and mesh part counts are not constraints.'
 ],
 'technicalContract':{'nativeFrame':[384,640],'logicalFrame':[192,320],'logicalRoot':[96,248],'sourceScale':2,'elevationDegrees':35,'height':1.5999999642372131,'footprint':[1,1],'nativeRootScale':1.25,'nativeRootRotationsDegrees':{'S':0,'E':90,'N':180,'W':-90},'catalogFrames':192,'supplementalFrames':96,'requiredTotalNativeFrames':288,'catalogClips':['idle','work','hold','load'],'supplementalClips':['hold-cucumber','load-cucumber'],'framesPerClipFacing':12,'fps':12,'loops':['idle','work','hold','hold-cucumber'],'nonLoops':['load','load-cucumber'],'requiredFullPacketCoverage':True},
 'reviewStatus':'Proposed visible criteria ready for coordinator reconciliation and freeze; no candidate exists or is graded.'
})
write('criteria.json',{
 'asset':'chef-omar','status':'proposed-for-coordinator-freeze','basis':'Independent direct viewing of fixed target and native/registered source, plus brief modelingPolicy version2.','priorityOutcomes':[
  {'rank':1,'outcome':'A dimensional, softly folded chef toque and rounded friendly head replace the source stepped white tower and hard planar appearance while preserving Omar\'s amber, blue-black, moustached identity and the fixed overall gameplay envelope.'},
  {'rank':2,'outcome':'Coat, teal tie/apron and cuffs read as connected purposeful garments with clear layers, thickness and one or two crafted details visible at logical192x320, including side/back views and bent serving/work poses.'},
  {'rank':3,'outcome':'Soft warm shading separates skin, ivory, teal and navy masses in every native facing without blown white slabs, dead black patches, harsh outline halos or direction-dependent color changes.'}
 ],
 'aestheticCriteria':{
  'shapeVolume':{'desired':['Rounded broad toque lobes/folds with a convincing band and coherent side/back continuation; no flat stepped tower silhouette unless it still visibly achieves the target\'s soft fabric volume.','Friendly large head, compact body and readable rounded hair, ears, nose, moustache, sleeves, palms and shoe forms. Modeling may change nonfunctional proportions, structure, topology and part counts.','Clothing layers have clear hierarchy: ivory coat/collar/cuffs beneath teal necktie/apron/bib/waist/pocket; details should feel attached and purposeful.'],'failureExamples':['Toque remains an almost blank white extrusion.','Parts swell into head/arm/food clearance or detach from the body.','New detail produces an incoherent side/back silhouette.']},
  'color':{'desired':['Maintain original medium tan/amber skin, blue-black cropped fringe and moustache, warm ivory toque/coat, teal apron/necktie and dark footwear.','Use warm soft separation and tasteful local value variation; do not shift Omar toward the family concept\'s brown curls, red scarf or blue apron.','Preserve salmon and cucumber food identity and exact approved 2D food dependencies unless the coordinator explicitly changes that contract.']},
  'lightingHighlights':{'desired':['Broad soft illumination reveals rounded surfaces and fabric folds, retains creamy ivory detail and keeps navy hair/footwear legible.','One common horizontally symmetric lighting/material treatment works in every rotation; no preferred lateral key/rim and no directional ground shadow.','Highlights are controlled and shape-describing; avoid white clipping, sharp plastic glare and outline halos.']},
  'materialDetail':{'desired':['A restrained soft cartoon material vocabulary: skin smooth and warm, hair softly satiny, cloth gently matte/satin with dimensional hems/folds.','Purposeful details such as collar, cuff roll, apron rim/pocket, tie or button remain useful at intended size. Exact target micro-stitching is optional.','Finish remains native editable geometry/materials; no target-textured actor card, painted angle correction or per-facing recoloring. Existing food cutouts remain explicitly identified as 2D.']},
  'artifactFreeReadability':{'desired':['At logical192x320 and enlarged native384x640, face, hat, coat and apron remain distinct against light, gray and dark backgrounds.','All 288 native frames have coherent silhouette, stable garment and hair shading, intact hands, proper occlusion and no mesh tears, coplanar flicker, floating parts, seams, clipping, collapsed cloth, alpha debris or changing outline bands.','Every clip/facing must show the original timing, poses, hand/dish and knife relationships; salmon and cucumber load transfer/visibility stay coherent.','Unseen views continue the design without requiring invented frontal reference details.']}
 },
 'immutableTechnicalCriteria':[
  'Registered character orthographic camera: 35-degree elevation, original world/projection matrices, pixel aspect1:1; fixed native384x640 frame, logical192x320, logical root96,248, sourceScale2. No per-view or per-frame fitting, reframing, rotation relabeling, raster warp or scale adjustment.',
  'Preserve 1x1 gameplay footprint, original C125/root1.25 functional anatomy and height1.6, feet/ground and seat contact, rig/rest/action behavior and functional attachment/clearance positions throughout animation; geometry within the permitted nonfunctional design freedom may improve.',
  'Original cardinal convention must be verified from source: S0 degrees, E+90, N180, W-90, including source child orientation. Validate actual measured transforms, not only dictionary labels.',
  'Catalog idle/work/hold/load each12frames x4facings at12fps gives192frames; supplemental Godot hold-cucumber/load-cucumber each12frames x4facings gives96more, total288. Preserve loop flags, frame order, visibility keys and timing.',
  'Preserve exact original atlas layout6columns x2rows, each frame384x640, atlas2304x1280; supplemental clips remain separately declared runtimeVariants, outside original catalog atlas map.',
  'Native project/resource closure must reopen correctly, including packed salmon/cucumber images or exact declared resources, rig records and reconstruction recipe. Hash-bound packet must include every source, output, dependency and validation.'
 ],
 'requiredReviewEvidence':[
  'Hash-bound editable source .blend(s), exact recipe, native camera/root/facing calibration, all288 named raw frame records and atlases; supplemental project/source/recipe/validation/resources must be explicit.',
  'Visually inspect every catalog and runtime-variant frame through verified contact sheets, plus actual playback for all24clip/facing combinations at original12fps, including non-loop load endings and loop boundaries.',
  'Show four facing hero views, intended-size repeated sprites, and light/gray/dark background readability. No single frontal hero can substitute for action and rotation evidence.',
  'Native validation of stable evaluated topology/deformations through all288 frames; original rest/action timing, foot/root/hand/food/knife contacts and visibility; bounds and functional envelope; reopen audit of linked libraries and packed/external images.',
  'Missing coverage, dependencies, motion previews or native technical validation yields needs_evidence rather than approval.'
 ],
 'judgingPolicy':'Reward useful native design improvements. Source differences alone, changed part counts or absent optional target microdetails are not defects. Enforce identity, style/readability and locked gameplay/capture contracts. Scores are comparative evidence, not universal pass thresholds.'
})
print('Wrote reviews/initial.json and reviews/criteria.json')
