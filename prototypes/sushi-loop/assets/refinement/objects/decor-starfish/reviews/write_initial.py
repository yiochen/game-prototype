import json,hashlib
from pathlib import Path
E=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/decor-starfish')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inspection=json.loads((E/'reviews/source-inspection.json').read_text())
initial={
 'asset':'decor-starfish','stage':'independent-initial-inspection','candidateApproval':False,
 'inspected':[
  {'path':'brief.json','sha256':sha(E/'brief.json')},
  {'path':'inputs/original.png','sha256':sha(E/'inputs/original.png')},
  {'path':'inputs/target.png','sha256':sha(E/'inputs/target.png')},
  {'path':'../../style/warm-soft-reference.png','sha256':sha(E/'../../style/warm-soft-reference.png')},
  {'path':'inputs/source-camera.json','sha256':sha(E/'inputs/source-camera.json')},
  {'path':'inputs/source-rig.json','sha256':sha(E/'inputs/source-rig.json')},
  {'path':'inputs/catalog-object.json','sha256':sha(E/'inputs/catalog-object.json')},
  {'path':'reviews/source-inspection.json','sha256':sha(E/'reviews/source-inspection.json')},
  {'path':'reviews/original-four-views-logical-backgrounds.png','sha256':sha(E/'reviews/original-four-views-logical-backgrounds.png')}
 ],
 'sourceProject':{'path':inspection['project'],'sha256':sha(Path(inspection['project'])),'collection':'S33_PROP_starfish.001','root':'starfish__root.001','actualBounds':inspection['collections'][0]['bounds'],'measurementMethod':'Opened original .blend in background Blender5.2.2. Enabled source collection for dependency evaluation without saving, then measured transformed mesh bounding corners. Saved dormant object matrices before evaluation are not reliable bounds.'},
 'sourceVisual':[
  'Five-point orange starfish, with ten small pale yellow surface spots. The original four native facings retain distinct orientation on the registered square grid.',
  'The star body is a sharply pointed open triangular fan with one raised center, not a soft organic volume. At logical use size its orange reads nearly flat and its spots read as tiny angular chips.',
  'The target usefully adds plump rounded arm contours, a raised coherent center and tapered arm ridges, warm orange/coral midtone separation and creamy rounded nodule detail. These are design outcomes, not a required vertex construction or spot count.',
  'The target has some highly polished point highlights and outer bright edge traces. Native output should use controlled soft material reflections and clean alpha edges, without copying external halo, rim speckles or inflated target registration.'
 ],
 'sourceTechnical':{
  'meshCount':11,'bodyVertexCount':11,'bodyPolygonCount':10,'decorativeSpotCount':10,
  'physicalZ':[0.07000000029802322,0.17000000178813934],
  'declaredHeight':0.2,'heightInterpretation':'Declared0.2 is a low decoration envelope. Actual source thickness is0.1 at z0.07..0.17. Do not scale the model to0.2 thickness or treat the old open fan/raised lower boundary as immutable. Native closure and rounded construction within z0..0.2 are allowed.',
  'rootWorld':[0,0,0],'footprintCells':[1,1],'rootCell':[0.5,0.5],
  'clip':{'id':'static','sourceClipId':'idle','frames':1,'fps':12,'loop':False,'directions':['N','E','S','W']},
  'armatures':[],'actions':[],'sockets':{},'portProfiles':{},
  'noApplicableRequirements':['modular seam assembly','animation loops','rig deformation','attachment/socket mating','gameplay interaction mechanics'],
  'cameraRecord':'inputs/source-camera.json; matching source/native-records/decor-starfish/camera.json and registered/static-N/guide.json',
  'cameraElevationDegrees':55.00797980144134,'pixelAspect':[1.2206555604934692,1.0],
  'logicalFrame':[192,352],'logicalRoot':[96,248],'logicalCellPixels':128,'nativeRecordCaptureScale':4,'deliveryScale':2,'deliveryFrame':[384,704],
  'logicalBasis':{'x':[128,0],'depth':[0,128],'height':[0,-89.6]},
  'savedActiveSceneWarning':'The source library opens in a generic export scene with35degree camera,768x1280 and square pixels. That state does not match this object\'s production capture. Use the object-specific55.00798degree record and calibration; do not copy the unrelated active camera.',
  'lighting':'Current source has140W broad centered overhead and four symmetric100W area fills; these old powers and old faceted shader recipe are not aesthetic locks. Balanced horizontal light and no directional ground shadow remain locked.'
 },
 'technicalConflictAssessment':'No unresolved source/modeling conflict. Nominal height and dormant active camera require the explicit interpretations above before freeze. The fixed ImageGen target is style/design reference, not dimensional or registration proof.',
 'next':'Coordinator freezes proposed criteria in brief.qualityCriteria before editor candidate work. This file approves no candidate.'
}
criteria={
 'version':1,'asset':'decor-starfish','status':'proposed-awaiting-coordinator-freeze','targetSHA256':sha(E/'inputs/target.png'),
 'judgingPolicy':'Judge visible outcomes with creative modeling freedom. Native reconstruction, improved proportions, construction and purposeful decoration are welcome. No fixed original topology, original part count, target pixel identity, prescribed modeling method or arbitrary score threshold.',
 'rankedVisibleOutcomes':[
  {'rank':1,'id':'coherent-soft-star','outcome':'A recognizable five-armed orange underwater starfish with a unified softly rounded center and organic tapered arms. Corners and notches feel deliberately softened; thickness and broad plane transitions read as native volume rather than a flat angular cutout or intersecting separate wedges. All four facings keep a coherent design and readable separation between arms.', 'materiality':'The dominant improvement over the original flat fan; preserve low-scale decorative role and occupied grid scale.'},
  {'rank':2,'id':'warm-palette-and-readable-detail','outcome':'Retain orange/coral body and pale yellow/cream nodule palette family. Body midtones show gentle variation and broad form shading; nodules look deliberately seated on the surface and legible at intended size. Detail is purposeful and sparse enough that arm volumes remain clear, without noisy microtexture, accidental tiny chips, crowded central bumps or new face/eyes/props.', 'materiality':'Cream detail supports starfish identity, while the body remains the dominant shape. Exact count and source placement of old spots are not locked.'},
  {'rank':3,'id':'soft-balanced-finish','outcome':'Warm broad highlights and controlled edge reflections describe the curved orange material and cream detail without turning surfaces white or creating hard black creases. Every facing retains readable midtones and equivalent lighting quality. Horizontally balanced illumination and no directional ground cast shadow support rotatable use.', 'materiality':'Source faceted shader, power values and sharp original fan facets are not required. Target polish is directional guidance, not mandatory wet plastic or copied glare.'},
  {'rank':4,'id':'clean-pixels-and-use-size','outcome':'At192x352 logical frame and real phone catalog display scale, the star silhouette, rounded volume and cream accents remain distinct. No black patches, material dead spots, coplanar flicker, overlaps that merge arms/nodules, broken seams, clipping, detached pieces, bright alpha fringe, exterior halo/speckles, or unwanted shadow slabs on cream/gray/dark and actual catalog backgrounds.', 'materiality':'Inspect enlarged views to locate defects, but prioritize visible problems that affect the delivered asset and intended use.'}
 ],
 'immutableContract':{
  'registeredProjection':'Use inputs/source-camera.json camera world/projection matrices and pixel aspect[1.2206555604934692,1],55.00797980144134degree orthographic elevation. Match logical basis x[128,0],depth[0,128],height[0,-89.6] and logical root[96,248]. The generic saved active35degree camera is not this object\'s contract.',
  'frames':'One static frame per N/E/S/W,12fps metadata,nonlooping;192x352 logical frame,384x704 delivery frame,sourceScale2,one-cell128px logical grid,transparent RGBA. Native high-resolution capture scale4 is acceptable with documented uniform reduction to scale2. No per-facing fitting, warping, recoloring or alpha recentering.',
  'world':'Ground root[0,0,0],1x1 cell footprint,rootCell[0.5,0.5],nonblocking underwater decoration. Preserve occupied scale with source radial extent0.38 as reference; proportion changes may improve design within its1x1 footprint without enlarging its catalog role.',
  'heightResolution':'Nominal height0.2 is the maximum low-decoration envelope, not source physical thickness. Original actual z is0.07..0.17. Rounded native construction or an underside may occupy z0..0.2; do not lock the source\'s open fan or exact original zmin.',
  'notApplicable':'Actual source has no rig, animation, sockets, ports or modular joins. No modular assembly or animation/fullgame matrix is required for this standalone static asset.',
  'nativeSource':'Candidate is an editable3D collection with renderable native geometry/materials. Final renders must come from the submitted .blend, not painted target cards, postrender image warp or viewpoint-specific raster substitutions.'
 },
 'proportionateEvidence':[
  'Hash-bound candidate packet with edited .blend, exact recipe/settings, fourN/E/S/W transparent native PNGs and original-layout atlases, native validation and concise delivery metadata. Bind or pack external resources; show actual object/collection provenance and dependency closure.',
  'Compact reopened-source audit: actual object-specific camera/projection/pixelaspect/calibration, root transforms and facing rotations, evaluated geometry bounds, static clip metadata, footprint, materials/light and absence of undeclared raster substitutes. Demonstrate the source nominal-versus-physical height interpretation explicitly.',
  'Native replay from that exact closed source for all four static facings, using one capture contract; verify the replays correspond to submitted PNGs. A compact four-view sheet is enough for this static object.',
  'Intended logical-size four-view comparison plus enlarged views on light cream,neutral gray and dark backgrounds. Inspect clean silhouette/alpha and material behavior without treating ImageGen registration as proof.',
  'Real catalog phone-context capture at the asset\'s actual display scale, including the existing W12 decor family and its standalone preview. The declared submarine/eel layered scenery preview may serve as context if it already exists; no newly invented fullgame artifact matrix is needed.'
 ],
 'approval':'Approve only an exact candidate packet whose actual native images visibly meet the ranked outcomes and hard contract, with no material defect/dead spot in any of the four required views. Missing evidence yields needs_evidence; observable defects yield revise. Scores are comparative observations, not pass thresholds.',
 'scope':'Initial criteria only. No candidate exists or is approved by this document.'
}
for name,data in [('initial.json',initial),('proposedcriteria.json',criteria)]:
 (E/'reviews'/name).write_text(json.dumps(data,indent=2)+'\n')
 print(name,sha(E/'reviews'/name))
