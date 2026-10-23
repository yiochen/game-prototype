import json,hashlib,datetime
from pathlib import Path
P=Path(__file__).resolve().parents[1]
R=P/'reviews'
b=json.loads((P/'brief.json').read_text())
source=(P/b['source']['project']).resolve()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
initial={
 'asset':'chef-ama','reviewStage':'independent-initial-inspection','createdAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidateVerdict':None,
 'independence':{'readEditorProposals':False,'receivedPriorAestheticConclusions':False,'scope':'Ama only; own reviews/ only. No source, brief, target, production or candidate files modified.'},
 'authority':{'skill':'/Users/yiouchen/.codex/skills/refine-3d-model/SKILL.md','judgePrompt':'prompts/judge.txt','brief':'brief.json','nativeSource':str(source),'sourceSHA256':sha(source),'sourceHashMatchesBrief':sha(source)==b['source']['projectSHA256'],'nativeActionsAndEvaluatedGeometryTakePriorityOverStaleCustomProperties':True},
 'inspectedFiles':[
  {'path':'inputs/original.png','sha256':sha(P/'inputs/original.png'),'inspection':'Direct image at native384x640; logical-size diagnostic comparison.'},
  {'path':'inputs/target.png','sha256':sha(P/'inputs/target.png'),'inspection':'Direct large image and logical192x320 canvas fit; used only as style/design direction, not registration.'},
  {'path':'../../style/warm-soft-reference.png','sha256':sha(P/'../../style/warm-soft-reference.png'),'inspection':'Direct style-only image; warm broad light and readable dimensional forms.'},
  {'path':'inputs/family-concept.png','sha256':sha(P/'inputs/family-concept.png'),'inspection':'Direct family-style image and logical-size diagnostic; its white toque/blue apron/red tie do not replace Ama identity.'},
  {'path':'inputs/source-camera.json','inspection':'Read complete registered camera record.'},
  {'path':'inputs/source-rig.json','inspection':'Read source key structure, native action cohorts, clip policy, bones/sockets via script; evaluated actual action assignments in Blender.'},
  {'path':'inputs/source-assetRecord.json','inspection':'Read original asset record; captureScale4 is historical source record, brief/catalog requires scale2 delivery.'},
  {'path':'inputs/catalog-object.json','inspection':'Read registration, all16 atlas layouts, timing, footprint, interactions and declared contacts.'},
  {'path':'../../prompts/native-capture-notes.md','inspection':'Read technical notes only, including isolated scene and native facing convention.'},
  {'path':'reviews/source-state-facing-gray.png','inspection':'Direct full sheet: all16 clip/facing frame-zero crops at logical192x320.'},
  {'path':'reviews/source-state-facing-light.png','inspection':'Direct full sheet on warm light background.'},
  {'path':'reviews/source-state-facing-dark.png','inspection':'Direct full sheet on dark blue-gray background.'},
  {'path':'reviews/reference-logical-size.png','inspection':'Direct comparison; target fills more of its canvas and must not drive camera fitting.'},
  {'path':'reviews/source-inspection.json','inspection':'Generated read-only native inspection; every source clip evaluated across frames1..12 in direction S.'},
  {'path':'reviews/source-sheets.json','inspection':'Hash/rect mapping of diagnostic sheets to original production atlases.'}
 ],
 'nativeSourceFindings':{
  'blenderVersion':'5.2.2 LTS','collection':'S33_CHARACTER_chef_ama.002','groundRoot':'chef_ama__ground_root.002','rootLocation':[0,0,0],'rootScale':[1.25,1.25,1.25],'rootRotationAtInspection':[0,0,0],'objectCount':63,'meshCount':59,
  'idleFrame1EvaluatedBounds':[[-0.4025000035762787,-0.3481249511241913,1.1109793085495312e-08],[0.4341636896133423,0.3829374611377716,1.5249998569488525]],
  'nativeActionCohorts':'6 owners per state, all24 assigned actions present. All12 unique source frames per state evaluated without calling procedural pose().',
  'actualFacingMeaning':'Original production sheets show S front, N back, E/W opposite profiles; publisher root rotations S0,E+90,N180,W-90 must retain actual source child transforms.',
  'heldDishProvenance':'Source held_dish-salmon contains an explicitly named image_plane with transparent_2D_material. This legacy source insert is not evidence of a rebuilt native3D dish. Keep provenance honest; native geometry/action evidence is authoritative for chef and actual attachments.',
  'functionalEnvelopeInterpretation':'One-cell body/rest envelope and functional1.525 height remain locked. Original action hold/load dish reaches y about-0.643 at frame1; do not incorrectly reject the preserved functional held-prop extension by comparing all action bounds to idle-body bounds.'
 },
 'sourceBaseline':{
  'scores':{'shapeVolume':4,'color':5,'lightingHighlights':3,'materialDetail':3,'artifactFreeReadability':6},
  'scoreScope':'Comparative initial impressions from original front and16 frame-zero crops; not candidate grades, not a numeric pass threshold.',
  'observations':[
   'Ama is recognizable in front: dark-brown face, short scalloped dark fringe, golden-yellow headwrap, ivory coat, green bib/apron and tie, small dark shoe ends. These identities are already clear and should survive refinement.',
   'The original headwrap has a pointed angular crown and near-flat very bright yellow upper faces; its horizontal folds read as parallel extruded bars. The target gives the cloth more believable broad folds and a softly rolled band.',
   'The source apron is mainly stacked flat rectangular masses with a tiny rectangular pocket mark; sleeves and torso show harsh faceted transitions. At logical size the lower garment details merge into a green block.',
   'Original E/W profiles show a very thin front headwrap edge, compact nose/face edge, rounded hair mass at back and a slab-like sleeve/torso transition. Side and rear design quality needs an independent bar because the target supplies only a front view.',
   'The source yellow highlights approach flat pale neon yellow while skin and green apron shade down strongly. The target offers warmer graded golden fabric, cream coat and green volume separation but its lighter orange skin conflicts with the identity lock.',
   'Source footwear is a small dark horizontal toe indication; it should remain grounded/readable without adding incompatible height or changing action feet.',
   'The target apron straps, pocket edge, collar/cuffs and tied waist are useful purposeful construction cues. Exact stitching, button count, hair lobe count, source part count and decorative arrangement are not required.',
   'Intentional dark pupils, hair, shoe soles, and contact creases are legitimate. Unexplained near-black patches, merged surfaces and invisible shape changes would be defects.'
  ]
 },
 'targetInterpretation':{
  'adopt':['Warm softly lit cartoon volume','Readable folded headwrap with softly rounded cloth boundaries','Short dark fringe/expressive friendly face','Constructed ivory collar and cuffs','Green apron/tie with readable functional detail and coherent silhouette'],
  'doNotCopy':['Lighter orange/copper skin drift','Target canvas filling/framing or apparent different camera/scale','Colored alpha fringe/halo and detached bright specks','Unseen rear/profile forms invented as reference facts','Family concept white toque, blue apron or red necktie','Photo-texture or exact microstitching that disappears at intended size'],
  'modelingFreedom':'Native proportions, forms, structure and purposeful decorations may improve; source weak geometry/part counts are not constraints. Aesthetic departures are judged by outcome and locked identity/function.'
 },
 'rankedDesiredOutcomes':[
  {'rank':1,'outcome':'A golden folded cloth headwrap and friendly short-fringe head that have soft, deliberate volume and coherent front/profile/rear construction, with Ama still dark-brown.'},
  {'rank':2,'outcome':'An ivory chef coat and green apron/tie that read as connected crafted garments with meaningful visible collar/cuff/apron/pocket/waist hierarchy at logical use size.'},
  {'rank':3,'outcome':'Warm broad light, controlled highlights and clean separations through all states/facings, with grounded feet and continuous hand/knife/dish/load action contacts.'}
 ],
 'evidenceLimits':[
  'No candidate submitted or judged; this initial file grants no approval.',
  'Inspected all16 original clip/facing frame-zero image crops, not every frame of every source atlas or source playback.',
  'Native source evaluated all48 clip/frame poses in S only; all-cardinal candidate review still requires complete192 actual native frames, every clip/facing playback, contact/evaluated geometry evidence and hash-bound packet.',
  'No exact camera/root/envelope measurements inferred from target or diagnostic sheet pixels. Exact native restoration and projection calibration remain candidate validation requirements.',
  'The source inspection script does not certify correct rendered hand/dish/knife contact from bone coordinates alone.'
 ]
}
criteria={
 'asset':'chef-ama','status':'proposed-for-coordinator-freeze','version':1,'candidateVerdict':None,
 'judgingBasis':'Observable outcome toward fixed warm soft cartoon target, with authorized native modeling/design improvement. Original weak forms and part counts are not constraints. No prescribed editor methods. Technical invariants and identity override target drift.',
 'immutableConstraints':[
  {'id':'contract-registration','requirement':'Native384x640 RGBA transparent frames, logical192x320, root[96,248], sourceScale2, cell128, orthographic registered35-degree camera, no per-view fitting/warping/recoloring. Calibrate actual source root and unit axes numerically.'},
  {'id':'contract-identity','requirement':'Ama Mensah retains dark-brown skin, short dark-brown fringe, golden-yellow folded headwrap, ivory coat, GREEN apron AND necktie, dark shoes. Target skin/framing/halo and family different hat/colors are not authority.'},
  {'id':'contract-body-function','requirement':'Preserve native root uniform1.25 scale, functional1.525 height, original one-cell body/clearance envelope, existing ground and action contact behavior. Compare actual evaluated source/candidate geometry/actions, not stale custom metadata. Preserve original functional prop reach rather than imposing rest-body bounds on every held dish.'},
  {'id':'contract-animation','requirement':'Original idle/work/hold/load each12 unique frames at12fps in N/E/S/W:192 native frames; idle/work/hold loop, load nonloop; original6x2 atlas rect/layout per direction,2304x1280 atlases. Source publisher S0,E+90,N180,W-90 and native child transforms retained.'},
  {'id':'contract-native-delivery','requirement':'Editable native scene produces exact delivered sprites; no target card/paintover substitute. Retained source2D inserts are explicitly identified, never represented as rebuilt3D. All external resources dependency-closed or bound in packet.'},
  {'id':'contract-lighting','requirement':'One coherent material/light configuration across rotations. No preferred horizontal lighting direction or directional ground shadow. Soft self-shadow/contact shading may describe volume without hiding functional parts.'}
 ],
 'aestheticOutcomes':[
  {'id':'form-headwrap','priority':1,'dimension':'shapeVolume','success':'Headwrap reads as purposeful folded golden cloth with broad legible fold transitions, a coherent band and knot/wrap structure. Top, side and back have deliberate volume instead of an angular blank cap or razor-thin facade. Better proportions are welcome inside the locked envelope.'},
  {'id':'form-face-hair','priority':1,'dimension':'shapeVolume','success':'Friendly readable cartoon face retains Ama identity. Dark short fringe, hair mass, ears, face/nose and headwrap connect coherently; profiles remain appealing and clear. Avoid detached features, broken hair-to-hat gaps, overgrown fringe or blank faceless-looking profiles caused by collapsed feature depth.'},
  {'id':'form-garment','priority':1,'dimension':'shapeVolume','success':'Coat, collar/cuffs, green tie, apron bib/waist/skirt and limbs have intentional connected proportions and readable cloth construction. Forms look comfortably rounded and crafted rather than stacked slabs or inflated beads; original awkward shapes may be rebuilt.'},
  {'id':'color-identity-hierarchy','priority':1,'dimension':'color','success':'Rich dark-brown skin and dark-brown hair remain distinct; golden-yellow wrap, warm ivory coat, green tie/apron and dark shoes stay legible as separate palette families under the warm light. Avoid orange/light skin drift, fluorescent flat yellow, muddy near-black apron or wholesale tinting that erases material separation.'},
  {'id':'light-soft-volume','priority':1,'dimension':'lightingHighlights','success':'Broad soft highlights and gentle warm shade transitions describe crown folds, rounded face, collar/sleeve volume and apron shape across all facings. Golden/ivory areas retain shading and color instead of clipping to flat white; dark regions retain useful volume. No artificial halo, harsh light seam or baked directional cast shadow.'},
  {'id':'detail-purposeful','priority':2,'dimension':'materialDetail','success':'A restrained set of visible crafted garment details makes the apron and chef role feel finished: functional edges, pocket/waist/tie/collar structure or equivalent useful decoration. Details must survive at logical size and belong to the same cloth language. Exact target stitches, buttons, seam counts and source part counts are not required; decorative noise or unreadable microtexture is not a substitute for shape.'},
  {'id':'readability-use-size','priority':1,'dimension':'artifactFreeReadability','success':'At logical192x320 with registered scale, front/profile/rear silhouettes, friendly face where visible, wrap folds, ivory/green garment divisions, hands, shoes and active knife/dish remain readable. Inspect light/gray/dark backgrounds and repeated/use-context preview without upscaling to excuse disappearing detail.'},
  {'id':'profiles-and-rear','priority':1,'dimension':'shapeVolume','success':'N/E/S/W read as the same coherent constructed character. Side/rear cloth, hair, garment and wrap transitions have deliberate volume and finish; no front-only quality or large dead blank slabs. The single front target does not dictate unseen shapes.'},
  {'id':'artifact-free','priority':1,'dimension':'artifactFreeReadability','success':'No material black patches, coplanar shimmer, ragged geometry ends, hollow garment gaps, visible intersections, broken corners, abrupt unintended normals/seams, blown highlight flats, clipping, alpha halos or detached specks. Intentional pupils/dark hair/shoes/contact creases are judged as designed forms, not defects by darkness alone.'},
  {'id':'motion-and-contacts','priority':1,'dimension':'artifactFreeReadability','success':'Every clip/facing retains stable topology and clean shape/material transitions over all frames. Feet stay grounded with original anchoring; sleeves/hands remain attached; knife grip/work action, held dish and load transfer are continuous, correctly occluded and plausible at the original functional contacts. No sliding/hovering hands, dish tunneling, knife through body, popping visibility, distorted apron/tie, texture swimming or loop-boundary snap; preserve load completion and nonloop behavior.'}
 ],
 'requiredReviewEvidence':{
  'packet':'Immutable hash-bound packet including exact reopened editable source, all192 native PNGs/atlas rect references, all16 clips/facing motion previews, fixed target, validation, resources, registration and render settings. Record measured root rotation or matrix for each direction.',
  'visual':'Inspect all192 frames directly or via verified labeled contact sheets, all16 motion previews, four-view sheet, repeated/use-context preview, logical-size and enlarged crops on light/gray/dark. Full frame sheets may be supplemented with detail crops; do not silently omit frames.',
  'native':'Numerical camera/root/unit-axis calibration; actual evaluated per-frame body/functional bounds and scale; bone/action compatibility and rest/topology stability; visible foot/hand/dish/knife/load surface contact evidence against evaluated source baseline; complete clip/frame/direction/timing/layout audit; source/resource/render SHA-256 binding.',
  'limits':'A manifest, source custom-property claim, bone coordinate list, unrendered model save or a single good idle/front still cannot certify the full result. Missing required evidence produces needs_evidence; visible defects produce revise.'
 },
 'approvalRule':'Visible material improvement toward warm soft cartoon form/light/detail, every frozen outcome satisfied without material all-facing or motion defects, and passing native/registration/action contract. No universal numeric threshold; no candidate verdict at this stage.'
}
(R/'initial.json').write_text(json.dumps(initial,indent=2)+'\n')
(R/'criteria.json').write_text(json.dumps(criteria,indent=2)+'\n')
print('saved',R/'initial.json',R/'criteria.json')
