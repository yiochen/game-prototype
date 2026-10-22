import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((P/'reviews/source-audit.json').read_text())
contract={
 'nativeSource':{'path':a['source'],'sha256':a['sha256'],'scene':a['scene'],'collection':a['collection'],'groundRootObject':a['root']['name'],'intrinsicRootMatrix':a['root']['matrixWorld']},
 'camera':{'type':'ORTHO','elevationDegrees':55.00797890615988,'orthoScale':1.5,'sensorFit':'HORIZONTAL','worldMatrix':a['restoredAssetCapture']['worldMatrix'],'pixelAspect':[1.2206555604934692,1.0],'publicationResolution':[384,704],'logicalFrame':[192,352],'logicalRoot':[96,256],'sourceScale':2,'cellSize':128,'worldUnitsPerCell':1,'publicationCalibration':a['restoredAssetCapture']['calibration'],'nativeSourceCaptureScale':4,'nativeResolutionAtScale4':[768,1408],'nativeRootAtScale4':[384,1024],'axes':{'x':'X','depth':'-Y','height':'Z'},'logicalProjection':'x=96+128X; y=256-128Y-89.6Z','phaseByFacingDegrees':{'N':180,'E':90,'S':0,'W':-90},'savedStartupCameraWarning':'The library starts on an unrelated character capture at 35 degrees, square pixels and 768x1280. Restore this asset camera; do not inherit that startup camera.'},
 'envelope':{'footprint':[1,1],'occupiedCells':[[0,0]],'rootCell':[0.5,0.5],'sourceRootLocalXYZBounds':a['rootLocalBounds'],'contactPlaneZ':0,'catalogDeclaredHeight':1.05,'measuredSourceMaximumZ':1.0750000476837158,'interpretation':'Preserve the one-cell X/Y gameplay envelope and grounded contact, with no growth above the measured native source clearance. The small authored crown offsets make the actual source 0.025 taller than its declared1.05 height. Native shape redistribution within this envelope is allowed; source per-facing silhouette and part counts are not locked.','blocking':False,'layer':4},
 'viewsAnimation':{'directions':['N','E','S','W'],'clip':'static','framesPerFacing':1,'fps':12,'loop':False,'animated':False,'actions':[],'armatures':[],'shapeKeys':[]},
 'attachmentsModularity':{'sockets':{},'ports':{},'joinPlanes':[],'supportCells':[],'overheadCells':[],'interpretation':'Standalone scenery rock bank. No modular join profile, attachment, or moving clearance was found. A repeated preview checks coherent scenery use, not a nonexistent watertight tile seam.'},
 'observationsNotConstraints':{'meshCount':4,'verticesPerOldMesh':32,'polygonsPerOldMesh':26,'uvLayers':[],'modifiers':[],'imageTextureDependencies':[],'oldLighting':'140W overhead plus four equal100W cardinal fills, world strength0','interpretation':'Mesh count, original prism contours, face allocations, shader graph and old light energy values may be changed to achieve the authorized design. No demand to preserve weak old geometry or old material implementation.'},
 'sourceSnapshotRelationship':'The restored native S facing matches the original snapshot composition, with a small edge/antialiasing difference because this inspection renders directly at publication scale2. Other facings are independently inspected native source renders.',
 'requiredLightingOutcome':'No preferred horizontal lighting direction and no directional ground shadow. Same fixed camera, materials and light setup for every facing. No per-view fit, warping, recoloring or target-image card.'
}
criteria={
 'schemaVersion':1,'asset':'decor-foreground-rock','status':'proposed-awaiting-coordinator-freeze','targetSHA256':sha(P/'inputs/target.png'),'sourceAudit':'reviews/source-audit.json','sourceTechnicalContract':contract,
 'priorityOutcomes':[
  {'rank':1,'outcome':'A designed bank of irregular, broad, weighty cobalt stone volumes, with a strong crown and readable stepped support masses; replace the repeated octagonal-column appearance and long blank prism sides in all facings.'},
  {'rank':2,'outcome':'Soft cartoon volume with luminous cyan upper planes and restrained pale warm edge accents over saturated cobalt midtones. Keep darker lower planes readable instead of large near-black slabs.'},
  {'rank':3,'outcome':'Readable facets and meaningful creases at intended catalog size, with clean grounded silhouette and no dead spots, distracting glow or directional ground shadow.'}
 ],
 'visibleCriteria':{
  'shapeVolume':[
   'Reads immediately as a compact natural cobalt rock bank used as foreground scenery, with convincing solid weight and stepped stone grouping inside the locked footprint and height envelope.',
   'Uses purposeful asymmetry, varied broad face angles, softened/chamfered stone transitions and clear major-to-minor mass hierarchy, inspired by the target. Useful native redesign of forms, proportions, structure and stone details is rewarded.',
   'N/E/S/W remain coherent views of the same3D object; every view has intentional sculpted volume and face breakup. Avoid tall uniform extruded side slabs, repeated identical octagonal cylinders, or a single front-only polished face.',
   'No exact old mesh count, target stone count, old polygon count, exact source silhouette, or unchanged small-part placement is required. Native improvements may alter the arrangement while preserving recognizable role, palette and technical contract.'
  ],
  'color':[
   'Preserve the original cobalt/royal-blue palette family. Broaden the visible blue range toward clear cyan top planes and rich cobalt midtones, keeping lower/deeper planes blue rather than crushed black.',
   'Use restrained pale cream/warm-tinted highlights where helpful for the selected warm soft cartoon style; the asset should remain blue rock, with no requirement to turn the material orange/brown.',
   'Keep adjacent facet colors related and deliberate. Avoid isolated neon streaks, chalk-white patches, oversaturated flat-blue bands, or a uniformly pale washed-out object.'
  ],
  'lightHighlights':[
   'Broad soft value transitions describe the stone volume, and controlled upper-edge highlights distinguish adjacent stone planes. The target favors light-filled upper surfaces and clear face transitions over the source flat solid-color bands.',
   'No fixed preferred horizontal key/rim direction: surface treatment must remain coherent when the root turns through every required facing under one unchanged setup. An intentional vertical top-to-bottom tendency is compatible with this requirement.',
   'Retain visible lower and occluded stone form without broad near-black dead zones. Do not flatten the full rock into emission-like uniform values or blow the crown to white.',
   'No directional shadow cast outside the object on an added ground or transparent canvas. Do not copy the target outer halo, stray cyan speckles, or directional yellow rim literally.'
  ],
  'materialDetail':[
   'Stone feels broad, lightly worn and tactile in the soft cartoon style; facets can remain graphic. Small chamfers, sculpted chips, creases, subtle surface variation or other purposeful details may enrich the native model.',
   'Facets and creases follow coherent3D stone construction and remain subordinate to the large masses. No need to copy every generated crack or painted polygon exactly.',
   'Avoid shiny ice/crystal reading, plastic gloss, razor-white drawn outlines, noisy bump texture or detail that disguises unresolved geometry. The native material must read cleanly around all facings.',
   'Do not preserve a blank old surface or weak contour merely for fidelity. Added decoration is optional and should serve the rock identity without overwhelming scenery readability.'
  ],
  'intendedSizeReadability':[
   'Inspect unwarped384x704 publication frames at logical192x352 and smaller catalog-use placements. Main crown, support masses and important face separations remain readable without relying on zoom.',
   'The asset remains scenery beside the submarine/creature interaction: retain clear actor and warning silhouettes and avoid an oversized high-contrast luminous beacon. Compare actual use context or a representative registered preview.',
   'Four-view sheet and repeated/scenery preview must use fixed root and scale. Expected variations from turning the object are allowed; do not fit each silhouette to the target image.'
  ],
  'defects':[
   'Clean alpha edges on light, gray and dark backgrounds, with no exterior colored halo, isolated speckles, unintended transparent holes, clipped tips or crop.',
   'No black patches, coplanar flicker, exposed open ends, abrupt broken normals, intersecting crease artifacts, light leaks, or muddy geometry overlaps at any required facing.',
   'Stones make convincing contact at the locked ground plane. No floating lower pieces, accidental undercuts exposing hollow geometry, or newly visible off-grid supports.'
  ]
 },
 'requiredCandidateEvidence':[
  'Immutable candidate packet binding exact edited.blend bytes, exact recipe/settings, validation, native resources and all four static native renders. No raster card, paint-over or post-render repair.',
  'Every publication atlas384x704 is one static frame at12fps with unchanged logical192x352 frame, root96,256, sourceScale2 and N/E/S/W facing phases. If rendering internally at scale4, document the single common native-to-publication reduction.',
  'Reopened native audit proves asset collection/root identity, actual55.00798-degree square-grid camera and calibration, pixel aspect, ground contact, measured one-cell geometry/clearance envelope, unchanged static state and empty socket/port contract.',
  'One unchanged material/light/capture setup across all four directions; native evidence for no preferred horizontal light and no directional ground shadow. Old numeric light energy values are not acceptance criteria.',
  'Inspect all raw facings, four-view sheet, light/gray/dark background sheet, intended logical-size rendering and repeated or scenery interaction preview. Repetition does not require modular seams for this standalone object.',
  'Saved/reopened source and resource closure demonstrate reproducible native output, with hashes and no missing external dependencies. A packet manifest alone does not certify source structure or appearance.'
 ],
 'targetInterpretation':{
  'use':'Style/design exploration for richer crafted stone shapes, varied angular face structure, luminous soft blue upper volumes and controlled edge accents.',
  'notTechnicalEvidence':'Target has a different926x1698 canvas and generated silhouette/registration drift; it does not establish camera, root, footprint, height or per-view silhouette. Preserve the measured native contract over target pixel registration.',
  'doNotCopy':['Exterior halo and stray alpha speckles','Strong one-sided warm rim','Potentially ice-like white highlights','Any generated form that would exceed the measured native footprint/clearance'],
  'unseenViews':'The target shows one composed view. Judge other native facings for coherent quality and defects without inventing exact reference views.'
 },
 'approvalBasis':'Visible material improvement toward the fixed target and selected style in every required view, all frozen technical constraints passing, and no material defects. Scores are comparative observations, not universal pass thresholds.'
}
initial={
 'schemaVersion':1,'asset':'decor-foreground-rock','role':'independent visual judge','status':'initial-inspection-complete-awaiting-frozen-criteria-and-immutable-candidate','noEditorProposalRead':True,
 'inspectedFiles':[{'path':str(p.relative_to(P)),'sha256':sha(p)}for p in [P/'inputs/original.png',P/'inputs/target.png',P/'../../style/warm-soft-reference.png',*[P/f'reviews/source-native-{d}.png'for d in 'NESW'],P/'reviews/initial-use-size-sheet.png',P/'reviews/initial-backgrounds.png']],
 'inspectedNativeSource':{'project':a['source'],'sha256':a['sha256'],'audit':'reviews/source-audit.json','script':'reviews/audit_source.py','writesLimitedTo':'reviews/; source project was opened and never saved'},
 'originalScores':{'shapeVolume':4,'color':5,'lightingHighlights':4,'materialDetail':3,'artifactFreeReadability':5},
 'observations':[
  'The original S snapshot is recognizable as a cobalt rock bank with a larger upper mass and stepped lower boulders. It has a strong blue identity, simple clean silhouette and grounded base.',
  'The repeated rounded-octagonal contours and nearly vertical lower slabs make the geometry read like joined extruded posts. Wide uniform blue face bands and narrow top rings produce little natural stone construction.',
  'The inspected native N view has an especially long dark blank front slab and narrow right-side support. W exposes another large uniform lower face. These are material all-view opportunities; merely improving the target-facing S view would leave weak sides.',
  'The fixed target offers richer irregular crown/shoulder contours, larger distinct sculpted facets, strong major-to-minor mass grouping and useful dark creases. Light cyan upper planes and small pale warm accents make the surfaces feel more light-filled and softer.',
  'At192x352 use size, the target retains more legible internal stone transitions than the source, while tiny painted texture is mostly subordinate. A native result should preserve this broad hierarchy without requiring every generated microfacet.',
  'Target defects include exterior cyan fringe/speckles and a stronger one-sided warm rim. These are not desired output features. Its taller/larger redistributed silhouette is aesthetic exploration, not a camera or envelope specification.',
  'The selected plant reference supports clear warm soft cartoon light and strong readable volumes. The rock should retain its cobalt palette rather than imitate the reference plant colors.'
 ],
 'rankedDesiredOutcomes':criteria['priorityOutcomes'],
 'actualSourceContract':contract,
 'technicalInspectionLimits':[
  'Only this object was inspected; no source, production, target or brief changes were made.',
  'Native source render visibility was explicitly restored from excluded library view layers. The first blank inspection attempt was discarded and overwritten in reviews/ before conclusions.',
  'The four replays were rendered directly at publication scale2; original snapshot appears to come from source-scale4 reduction, so subpixel alpha differences are not treated as model changes.',
  'Measured source height1.075 differs from metadata declared1.05 because of authored crown offsets. Coordinator should freeze the measured existing clearance envelope explicitly.',
  'No candidate exists yet and no approval is issued.'
 ],
 'proposedCriteria':'reviews/proposedcriteria.json'
}
(P/'reviews/proposedcriteria.json').write_text(json.dumps(criteria,indent=2)+'\n')
(P/'reviews/initial.json').write_text(json.dumps(initial,indent=2)+'\n')
print(json.dumps({'initial':str(P/'reviews/initial.json'),'proposedCriteria':str(P/'reviews/proposedcriteria.json'),'audit':str(P/'reviews/source-audit.json')},indent=2))
