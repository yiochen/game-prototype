from pathlib import Path
import hashlib,json
EXP=Path(__file__).resolve().parent.parent
BASE=EXP.parents[3]
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inspection=json.loads((EXP/'reviews/original-inspection.json').read_text())
criteria={
 'asset':'bubble-panic','status':'proposed-awaiting-coordinator-freeze','version':1,
 'fixedTargetSHA256':'71e7b0b1a9c2768f2ee6eb51c0c958e37522bf6db39ddbd3e803e9a15e89c0a6',
 'sourceType':'Existing native2D ImageGen raster plus deterministic publisher. No Blender claim applies.',
 'outcomes':[
  {'id':'form','required':'A rounded, softly full cream speech balloon with a coherent readable rim and attached lower tail. The fixed target supplies fuller rim construction and dimensional icon forms; useful improvements are welcome within registration and identity. No dents, awkward tail joins, pinched cutout, pasted-on pieces or empty featureless dead regions.'},
  {'id':'emotion-identity-color','required':'Immediately read as scared/panicked trapped-customer feedback: one coral-red exclamation body with a distinct separate red dot, one small blue sweat drop, and restrained warm-gold emphasis ticks on ivory cream. Maintain clear symbol separation, familiar palette hierarchy, and the exclamation as the main read. Do not confuse it with preference, puzzled or happy feedback.'},
  {'id':'warm-soft-light','required':'Warm cream midtones, gently rounded shading, restrained warm reflected rim light and legible soft highlights on balloon and symbols. Rim and lower shading must stay coherent with approved heart/smile family context without flattening panic emotion or becoming harsh black contour, metallic edge, bloom or external shadow.'},
  {'id':'detail','required':'Purposeful simple dimensional icon detail, clean gentle occlusion, interior breathing room and tidy tail/rim construction. No noisy ornament, text, disconnected unintended fragments, excessive tiny shine dots, blurry symbol boundaries or accidental surface defects.'},
  {'id':'intended-size-readability','required':'Inspect at82logical-art-width and phone-scale roughly32-36px artwork width, plus enlarged. The exclamation body/dot and blue drop must remain distinguishable, the cream balloon/tail readable, and warm material finish evident at larger scale. Family references are context only, not replacement targets.'},
  {'id':'alpha-and-views','required':'True transparent background; clean antialiasing on light, neutral gray and dark. No opaque rectangles, matte/colored fringe, external glow, clipped edge, seams or detached debris. Same camera-facing artwork in S/N/E/W; inspect all36 unique clip frames and verify all144 alias slots, not just a hero frame.'},
  {'id':'motion','required':'Actually watch all three twelve-frame12fps clips with game-size and enlarged evidence. Preserve original appearance growth/opacity, bob, fade residual opacity, and idle loop. No symbol wandering, new squash, per-frame fit, recolor, temporal speckles, stalls or new unintended flash. Document the inherited discrete-bob loop/transition behavior honestly rather than changing it.'},
  {'id':'runtime-context','required':'Inspect current Godot feedback above a customer using the actual registered draw path and attachment. Panic is selected only for navigation_mode=wander with phase walking/leaving: appear before1s then looping idle; reduced_motion uses idle0; timer is-1 and no timer ring. Keep catalog legacy attachment/context separate. An isolated current-methods Godot harness is acceptable if labeled as such; do not invent new gameplay or claim its fade as currently selected runtime behavior.'},
 ],
 'hardContract':{
  'projection':'screen-space-2d','facingPolicy':'camera-facing','logicalFrame':[192,320],'physicalFrame':[384,640],'logicalRoot':[96,248],'physicalRoot':[192,496],'sourceScale':2,'cellSize':128,'logicalArtWidth':82,
  'clips':[{'id':'appear','frames':12,'fps':12,'loop':False},{'id':'idle','frames':12,'fps':12,'loop':True},{'id':'fade','frames':12,'fps':12,'loop':False}],
  'frameOrder':list(range(12)),'atlas':{'columns':6,'rows':2,'size':[2304,1280],'rectSize':[384,640]},'directions':['S','N','E','W'],'uniqueClipFrames':36,'logicalAliasSlots':144,
  'publisherMath':{'t':'index/12','phase':'t*tau','normalization':'One alpha>8 bounds crop of same asset, then uniform aspect-preserving resize to164physical pixels wide; raw target remains untouched. No extra grading, painting, warp or per-frame/facing fit.', 'appearScale':'.5+.5*sin((index+1)/12*pi/2)','appearAlpha':'(index+1)/12','idleScale':1,'idleAlpha':1,'fadeAlpha':'1-index/12','centerLogical':'[96,248-52-3*sin(index/12*tau)]','pastePhysical':'round(centerLogical*2-imageSize/2)','alphaRounding':'round(sourceAlpha*max(0,opacity))'},
  'currentRuntime':{'source':'godot/scripts/restaurant_view.gd','attachmentLogical':[0,-172],'placement':'base+customer_pose_offset(customer,pitch)+BUBBLE_ATTACHMENT*pitch/art.cell_size','timer':-1,'phases':['walking','leaving'],'navigationMode':'wander','appear':'max(0,wander_elapsed)<1','idleSeconds':'max(0,wander_elapsed)-1','reducedMotion':'idle frame0','fade':'retained delivery/catalog clip; not selected by current panic branch'},
  'legacyCatalogContext':{'offsetLogical':[0,-90],'scope':'catalog interaction only; not evidence of current Godot attachment'},
 },
 'submissionEvidence':[
  'Immutable hash-bound candidate packet with native2D source, exact recipe, target/original hashes, unmodified raw target and original provenance, dependency-closed resources, atlas/metadata/validation/previews and portable replay instructions.',
  'Independently replay from declared same-asset source using exact original publisher math, compare actual frames/atlases, verify all36frames and144alias slots, root/canvas/dimensions/scale/fps/order/loop and no extra art manipulation.',
  'Registered whole-frame sheets plus fixed-region detail at logical and enlarged sizes on light/gray/dark; all clip/frame evidence must refer to exact sealed atlas bytes.',
  'Playable appear/idle/fade12fps at game size and enlarged, with final-frame/loop behavior and elapsed frame timing visible; judge must actually watch playback.',
  'Current Godot-method context capture and source/metadata closure showing correct172px attachment plus shared customer_pose_offset, walking/leaving wander branch, reduced motion, no timer ring; separately label catalog90px legacy context.',
 ],
 'verdictRule':'Visible improvement toward fixed warm-soft target and coherent family finish, no material defects/dead spots, passing capture/asset contract. Missing evidence means needs_evidence; numeric scores never substitute for inspection.',
 'technicalAmbiguities':[
  'Original catalog requirements.states lists appear/fade, but actual original clips also include idle. All three are locked.',
  'Original idle has12frames but only6distinct pixel images due to rounded sinusoidal bob; this is valid inherited behavior and is not a missing-frame defect.',
  'Fade frame11 retains1/12opacity, and appear frame0 starts1/12opacity with growth already above.5. Preserve exact original math rather than demanding fully transparent endpoints.',
  'Target raw canvas971x1620 differs from384x640 capture. Existing2D exception explicitly authorizes one alpha-bounds crop and same-asset uniform82logical-width normalization; raw target must remain sealed.',
  'Legacy catalog offset[0,-90] conflicts with current Godot BUBBLE_ATTACHMENT[0,-172]. Both must be labeled; current runtime proof must use the172px path.',
  'Current panic branch has appear/idle, no fade selection, no timer, and fixed facingS. Do not claim catalogfade or four-facing runtime animation as new gameplay.',
 ]
}
initial={
 'asset':'bubble-panic','reviewer':'fresh-independent-visual-judge','stage':'initial-before-editor-proposals','sourceType':'existing-native2D-raster','editorProposalsRead':False,'candidateApproval':False,
 'inspectedFiles':['brief.json','prompts/judge.txt','inputs/original.png','inputs/target.png','inputs/approved-feedback-family-heart.png','inputs/approved-feedback-family-smile.png','inputs/catalog-object.json','inputs/imagegen-prompt.txt','inputs/original-2d-pipeline/README.md','inputs/original-2d-pipeline/publish_2d.py','../../../production/source/2d/generated/bubble-panic.png','../../../production/sprites/bubble-panic/2d-appear-S.png','../../../production/sprites/bubble-panic/2d-idle-S.png','../../../production/sprites/bubble-panic/2d-fade-S.png','../../../../godot/scripts/restaurant_view.gd','../../../../godot/scripts/art_book.gd','../../../../godot/scripts/session.gd','reviews/original-all36-light.png','reviews/original-all36-gray.png','reviews/original-all36-dark.png','reviews/reference-size-context.png','reviews/original-inspection.json'],
 'hashEvidence':{'originalSourceSHA256':inspection['source']['sha256'],'snapshotSHA256':'f91dffab343b80a29d87dc1df5403ce0b8c2d0233ef357576a7c445a5879c5ba','targetSHA256':criteria['fixedTargetSHA256'],'originalPublisherSHA256':inspection['publisher']['sha256']},
 'observations':{
  'source':'Clean cream balloon with firm thin brown contour, coral-red exclamation and dot, blue sweat drop and gold ticks. Emotion is clear at game size. Surface volume is comparatively shallow and icon details simpler than target.',
  'fixedTarget':'Retains panic identity and palette. Fuller warm cream body, layered rounded brown-gold rim, stronger soft gleams and dimensional symbols. Target is suitable direction; normalization at82logical-width still separates red exclamation/dot and blue drop. Thick rim should remain a coherent warm edge rather than a heavy dark band.',
  'family':'Approved heart/smile context has cream body, warm edge and simple clean soft highlights. Panic can retain own lower-tail form and interior gold ticks; no requirement to copy happy symbols or their external accents.',
  'allFrames':'Viewed all36 source frames on three backgrounds,12perclip. Original replay exactly matches atlas pixels;4directions alias identical metadata. Idle has6distinct rendered images over12frames; appear/fade12distinct. No original matte rectangle or unintended debris seen.',
  'runtime':'Inspected actual current Godot source: wanderwalking/leaving selects panic, appear<1sec thenidle; reduced-motionidle0; timer-1. Draw path adds samecustomer_pose_offset and attachment(0,-172). Catalog original(0,-90)is legacy. Fade remains required asset clip but is not current panic branch.',
 },
 'independentVerification':{'originalPublisherReplayExactAll36':inspection['allPixelsMatch'],'originalSnapshotIsIdle0':inspection['snapshotEqualsIdle0'],'uniqueRequiredFrames':36,'logicalAliasSlots':144,'sourcePlaybackWatched':False,'playbackScope':'No candidate exists. Source animation inspected frame-by-frame; future approval requires actual watched candidate playback.'},
 'technicalAmbiguities':criteria['technicalAmbiguities'],'next':'Coordinator freezes reconciled visible outcomes before editor submission. No candidate verdict issued.'
}
for name,data in [('initial.json',initial),('proposedcriteria.json',criteria),('criteria.json',criteria)]:
 p=EXP/'reviews'/name;p.write_text(json.dumps(data,indent=2)+'\n');print(name,H(p))
