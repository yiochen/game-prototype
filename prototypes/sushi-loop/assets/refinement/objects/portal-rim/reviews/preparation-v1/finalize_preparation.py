from pathlib import Path
import json,hashlib,shutil,subprocess,math,platform
from PIL import Image,ImageChops,ImageStat
P=Path(__file__).resolve().parent;O=P.parents[1];REPO=Path.cwd()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def w(n,d):(P/n).write_text(json.dumps(d,indent=2)+'\n')
ins=json.loads((P/'native-inspection.json').read_text());meas=json.loads((P/'native-measurements.json').read_text());cat=json.loads((P/'resources/inputs/catalog-object.json').read_text());residual=json.loads((P/'source-replay-residuals.json').read_text());camera=ins['camera'];nativeval=json.loads((P/'nativeValidation.json').read_text())
# Preserve additional raw technical function/pack/validator references used in preparing the proposal.
for n,src in [('production_library.py','prototypes/sushi-loop/assets/production/source/blender/production_library.py'),('publish_captures.py','prototypes/sushi-loop/assets/production/source/blender/publish_captures.py'),('pack_captures.py','/Users/yiouchen/.codex/skills/generate-blender-characters/scripts/pack_captures.py')]:shutil.copy2(src,P/'resources/model-source'/n)
for n in ['seal_object.py','promote_object.py','audit_directions.py']:shutil.copy2(Path('prototypes/sushi-loop/assets/refinement/tools')/n,P/'resources/instructions'/n)
for n in ['package.json','package-lock.json']:
 if Path(n).exists():shutil.copy2(n,P/'resources/consumer'/n)
cmds=[
{'name':'nativeReplay','cwd':str(REPO),'env':{'PYTHONDONTWRITEBYTECODE':'1'},'argv':['/opt/homebrew/bin/blender','--background',str(P/'resources/native/original.blend'),'--python',str(P/'capture_original.py')],'stdoutStderr':'logs/blender.log','result':'48 native4x RGBA PNGs and evaluated ledgers; exit0'},
{'name':'groundContactMeasurementOnly','cwd':str(REPO),'env':{'PYTHONDONTWRITEBYTECODE':'1'},'argv':['/opt/homebrew/bin/blender','--background',str(P/'resources/native/original.blend'),'--python',str(P/'measure_contacts.py')],'stdoutStderr':'logs/contacts.log','result':'ground cross sections only, no renders; exit0'},
{'name':'uniformReductionAndResiduals','cwd':str(REPO),'env':{'PYTHONDONTWRITEBYTECODE':'1'},'argv':['/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',str(P/'prepare_pixels.py')],'result':'all48 original atlas cell decoded RGBA exact; exit0'},
{'name':'twoCurrentConsumerModes','cwd':str(REPO),'argv':['node',str(P/'capture_consumer.mjs')],'stdoutStderr':'logs/consumer.log','result':'two headless modes, exact pinned helpers, 3 backgrounds, logical/phone, recorded playback; exit0'},
{'name':'videoDecodeInspection','commandsAndLogs':['logs/video-full-chromium.log','logs/video-headless-shell.log'],'note':'Actual browser WebM at25fps decoded to timed contact sheets. Original fixture loops for2.2seconds then holds its last demonstration frame; the tail in the decoded sheet is that hold, not a source one-shot.'}]
w('commands.json',cmds)
# Derived numerical replay checks, not candidate approval.
metrics={'sourceReplay':{'frames':48,'nativeFrame':[768,1536],'publishedCell':[384,768],'all48PublishedDecodedRGBAExact':all(r['changedPixels']==0 for rs in residual['facings'].values() for r in rs),'maxBorderAlpha':max(r['alphaAtFrameBorder'] for rs in residual['facings'].values() for r in rs)},'nativeFacings':{},'consumer':{}}
for facing,rs in meas['frames'].items():
 frames=rs[:12];close=rs[12]
 metrics['nativeFacings'][facing]={
 'uniqueDecodedFrames':len({hashlib.sha256(Image.open(P/'raw/idle'/facing/f'{i:03d}.png').tobytes()).hexdigest() for i in range(12)}),
 'rootRotationDegrees':math.degrees(frames[0]['rootRotationZ']),
 'rawAuthoredUnion':[[min(r['rawAuthoredBounds'][0][a] for r in frames) for a in range(3)],[max(r['rawAuthoredBounds'][1][a] for r in frames) for a in range(3)]],
 'evaluatedModifierUnion':[[min(r['evaluatedModifierBounds'][0][a] for r in frames) for a in range(3)],[max(r['evaluatedModifierBounds'][1][a] for r in frames) for a in range(3)]],
 'frame13VsFrame1TransformMaxAbs':max(abs(close['objects'][n][k][a]-frames[0]['objects'][n][k][a]) for n in close['objects'] for k in ['location','rotationEuler','scale'] for a in range(3)),
 'supportTransformsStable':all(r['objects'][n]['matrixWorld']==frames[0]['objects'][n]['matrixWorld'] for r in frames for n in frames[0]['objects'] if 'base_rock' in n)}
for mode in ['full-chromium','headless-shell']:
 d=json.loads((P/f'consumer-{mode}.json').read_text());metrics['consumer'][mode]={'browserVersion':d['browserVersion'],'errors':d['errors'],'updates':len(d['playback']),'observedRawFrames':[v['rawFrame'] for v in d['playback']],'expectedFrameSequence':all(v['frame']==v['rawFrame']%12 for v in d['playback']),'noSkippedFrames':all(b['rawFrame']==a['rawFrame']+1 for a,b in zip(d['playback'],d['playback'][1:]))}
metrics['browserModesCompared']={}
for bg in ['light','gray','dark']:
 a=Image.open(P/'evidence'/f'consumer-full-chromium-{bg}.png').convert('RGBA');b=Image.open(P/'evidence'/f'consumer-headless-shell-{bg}.png').convert('RGBA');diff=ImageChops.difference(a,b)
 metrics['browserModesCompared'][bg]={'decodedPixelsExact':not any(any(px) for px in diff.get_flattened_data()),'extrema':diff.getextrema()}
w('verification-metrics.json',metrics)
contract={
'asset':'portal-rim','version':'judge-proposal-v1','status':'PROPOSED — ROOT must reconcile/freeze before fresh editor construction','noCandidateApproval':True,
'actualSource':{'path':'resources/native/original.blend','sha256':ins['sourceSHA256'],'originalProject':'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend','scene':ins['scene'],'collection':ins['collection'],'rootObject':ins['root'],'identity':'Thin vertical open cyan rim with blue ornaments and two finite navy supports. Source12meshes+root are evidence, not part-count locks.','sourceFunction':'resources/model-source/prop_builders.py::build_portal','catalogMapping':'resources/model-source/production_library.py maps portal-rim to idle only; portal-entry is a different catalog object.'},
'fixedRegistration':{'projection':cat['projection'],'logicalFrame':[192,384],'logicalRoot':[96,288],'cellSize':128,'worldRoot':[0,0,0],'frameRootMustNotBeFitted':True,'nativeCaptureScale':4,'nativeFrame':[768,1536],'publishedSourceScale':2,'publishedCell':[384,768],'pixelAspect':camera['camera']['pixelAspect'],'worldCameraMatrix':camera['camera']['worldMatrix'],'projectionMatrix':camera['camera']['projectionMatrix'],'orthoScale':ins['actualCamera']['orthoScale'],'shift':ins['actualCamera']['shift'],'calibration4x':camera['calibration'],'elevationDegrees':camera['camera']['elevationDegrees'],'nativeAndPublishedMetadataMustBeDistinguished':True,'publication':'Uniform whole-frame LANCZOS4x to2x with original rectangle layout; no fitting, cropping art, view shifts, RGB/alpha repair, recolor, warp or painted replacement.'},
'requiredDelivery':{'clips':[{'id':'idle','sourceClipId':'idle','frames':12,'fps':12,'loop':True,'publishedIndices':list(range(12)),'nativeFrames':list(range(1,13)),'closingKeyFrame':13,'closingFrameExcludedFromAtlas':True}],'directions':['N','E','S','W'],'nativeRootRotationDegrees':{'S':0,'E':90,'N':180,'W':-90},'atlases':{'columns':6,'rows':2,'size':[2304,1536],'rects':cat['clips'][0]['directions']['S']['rects']},'noAdditionalRequiredStates':['entry','enter']},
'functionalRoleAndContacts':{
'gameRole':'W14 safe route/decor object, layered beside traveling submarine; source notes explicitly no access mechanic. No gameplay hazard/reward/progression changes.',
'rootAndFootprint':{'footprint':[1,1],'rootCell':[.5,.5],'occupiedCells':[[0,0]],'supportCells':[[0,0]],'directionFootprints':cat['directionFootprints'],'meaning':'Catalog placement registration. It does not imply a1×1 opaque ground or constrain all visible geometry to±0.5.'},
'entrySocket3D':[0,0,.74],'entrySocketLogicalRelativeAllViews':[0,-66.30402709960937],'socketMeaning':'Center reference remains fixed and coherently inside the opening; not an attachment or modular seam and no measured ship-passage collision contract.',
'groundEvidence':'ground-contact-measurements.json; two finite source z0 hulls, each area0.0335667188 world² in S, minZ=-0.06. Preserve stable grounded support role but allow native support geometry redesign; do not require exact old hulls or floor opacity.',
'opening':'Actual empty geometry/transparent center in the vertical XZ plane nearY0. Keep an open upright ring; no opaque portal disk, camera-facing target card or artificial alpha cutout.',
'attachmentsPortsRig':{'ports':{},'portProfiles':{},'externalParents':[],'armatures':[],'shapeKeys':[],'constraints':[],'attachmentsRequired':False,'modularAssemblyRequired':False},
'interactionFixture':'Catalog submarine neighbor is scale/presentation only. No true physical attachment/family seam fixture is required. A future root-requested context fixture can show honest registered scale without inventing ship traversal.'},
'sourceGeometryReferenceOnly':{'rawAuthoredAndEvaluatedSeparated':True,'baselineSourceEnvelopeByFacing':{f:metrics['nativeFacings'][f]['rawAuthoredUnion'] for f in metrics['nativeFacings']},'evaluatedModifierEnvelopeByFacing':{f:metrics['nativeFacings'][f]['evaluatedModifierUnion'] for f in metrics['nativeFacings']},'notAutomaticNewSizeLocks':True,'record':'native-measurements.json'},
'rootDesignBudgetProposal':{
'status':'ROOT decision required before editor; these proposed bounds are not frozen by the judge.',
'recommendedCanonicalSAllowance':{'X':[-.73,.73],'Y':[-.30,.30],'Z':[-.06,1.48]},
'reason':'Leaves a little silhouette growth beyond source sweptX±.716194 and gives coherent side thickness, while respecting declared height1.48 and the registered192px frame. Raw and evaluated geometry must both be reported. Root may choose a different useful budget if all fixed frame/contact/socket/role constraints still pass.',
'finalVisibleGate':'Every required view/frame remains inside complete frame with a transparent border after uniform reduction, without per-view fitting; source has zero border alpha in all48. Neither weak old geometry nor evaluated bevel trim becomes an exact new envelope.',
'allowed':'Rebuild forms/proportions/structure/topology/counts, improve purposeful bevels/ornaments/support connections, add restrained gold/neutral craft accents while cyan/blue/navy stays dominant.',
'orientation':'Keep physically rotated cardinal views; E/W can remain naturally edge-on. Improve profile construction/readability coherently, not by billboarding or choosing a separate camera.'},
'animationContract':{
'actualSource':'Ten object action owners: main rim+outer hoop pulse oppositely; eight blue ornaments circulate around the ring; two supports remain stationary. No shader actions, rig deformation or shape keys.',
'visibleRequirement':'Retain one-second12-frame12fps seamless idle pulse/circulation and stable support/root/socket role. At least six visually unique frames required by catalog; source has twelve distinct decoded frames in every direction.',
'closureEvidence':'Measured frame13 is transform-exact to frame1. Runtime12unique frames exclude duplicate closure. Inspect11→0 in actual playback.',
'freedom':'Action names, owner count and ornament count need not remain identical. If count/construction changes, adapt native motion symmetry to close cleanly rather than copying an invalid old angular/reset recipe.'},
'lightingAndMaterial':{
'actualSource':'resources/native/catalog_faceted.py + native-inspection.json. Centered140W area overhead atZ4.5,size3.5; four equal100W,size4 cardinal fills at radius3,Z1.8; worldStrength0. Active surface matte Principled roughness.85,specularIORlevel.03,metallic0,emission0; actual world-Z lower-tone ramp and RGB-only1.35sRGB contrast compositor.',
'policy':'Native material/light improvements allowed coherently. Preserve no preferred horizontal light direction/no directional ground shadow and actual transparent output. Do not lock old roughness/power/contrast merely to preserve weak source appearance.',
'visibleOutcome':'Warm soft crafted volume with cyan energy focus, readable dark supports and broad highlights; no black patches, clipped highlights, face seams, coplanar overlap, alpha fringe or painted target features.'},
'consumer':{'helpers':{'world-sprite-raster.js':'570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545','sprite-layout.js':'099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65'},'preserve':'Logicalframe/root, sourceScale, rect/order and actual sprite placement. Current helpers unchanged. Native independent canvas and CSS browser screenshot are different evidence layers.','requiredBrowserModes':[{'headless':True,'channel':'chromium'},{'headless':True}],'representativeDisplayScales':[1,.55],'backgrounds':['#eeeeee','#808080','#161c29'],'note':'Phone0.55 is a representative whole-frame CSS scale, not device integration or Godot approval.'},
'excluded':'All13marked2D effects, source/candidate editing, family approval, production integration, publishing, Git/index changes, liveBlender/device access and additional agents.'}
w('root-native-contract.json',contract)
plan={
'asset':'portal-rim','scope':'Preparation baseline now; later candidate review only after root freeze.',
'preparedEvidence':{'native':'raw/idle/{N,E,S,W}/000..011.png at768x1536, nativeValidation.json captureRecords carry actual measured root matrices/angles; source untouched. Native measurement13 closure retained without a redundant render.','nativeVisualInspection':'evidence/native-allframes-{N,E,S,W}.png cover all48whole frames at logical scale ongray. RawS010/E010 also inspected enlarged.','sourceReplayParity':'source-replay-residuals.json proves every4xreplay→2xcell matches original published source pixels exactly; retained original atlases.','currentConsumer':'Six actual screenshots in evidence/consumer-{full-chromium,headless-shell}-{light,gray,dark}.png show allfour views at logical1 and phone.55. Both webm recordings plus logs show sequential12fps playback over two loops. Decoded timed contact sheets inspected across loop seam; demonstration holds after2.2s.','fixture':'No functional family/attachment fixture exists; generic repeated preview in old brief should be removed as inapplicable rather than silently treated as seam approval.'},
'futureCandidateMinimum':[
'All48native captures and all48published frames in original4atlases, editable source/resource closure and exact recipe; raw source/camera/root/filter and measured authored/evaluated geometry separated.',
'NativeValidation target must expose actual captureRecords/views with measured facing+rootRotationZ/rootMatrix, and nativeGeometryMeasurements must use facing→list-of-frame mappings. Rich incompatible ledger may be separately bound with thin supported nativeValidation; never fabricate checks or weaken validators.',
'Allview/allframe native fullframe sheets, representative intendedlogical/phone threebackground screens in bothbrowsermodes, and actual12fps playback with11→0 closure; include meaningful native and consumer evidence as packet resources.',
'Physical support/root stability and entry center/socket opening evidence; no unnecessary modular repeat, hull/harpoon attachment or excluded2D effect fixture.',
'Judge must inspect every declared packet candidateRenders/previews with exact-path coverage. Future acceptance_contract.py and unchanged direction audit must pass before any approval. No universal score threshold or proof by hashes alone.'
],
'sourceEvidenceLimits':[
'Original is a baseline with flat saturated bands/dark supports; replay parity proves provenance, not desired appearance.',
'SingleS target does not define E/W/N aesthetics or justify camera/frame shifts.',
'Exact physical ship clearance was not authored as an interaction; do not invent a ship passage guarantee.',
'Consumer evidence is isolatedsprite render and wholeframe scaling, not full catalog/Godot/device approval. CSS filtered pixels and Pillow reductions are not assumed identical.',
'Preparation has no candidate, frozen root contract or editorial verdict. Stop now for root reconciliation/freeze.'
]}
w('scoped-evidence-plan.json',plan)
inspected=['evidence/native-allframes-'+f+'.png' for f in ['N','E','S','W']]+['evidence/consumer-'+m+'-'+b+'.png' for m in ['full-chromium','headless-shell'] for b in ['light','gray','dark']]+['evidence/playback-'+m+'-sheet.png' for m in ['full-chromium','headless-shell']]
w('preparation-review.json',{
'asset':'portal-rim','stage':'preparation-only','verdict':'prepared-for-root-reconciliation','candidateApproval':False,
'inspectedFiles':inspected,'enlargedRawInspections':['raw/idle/S/010.png','raw/idle/E/010.png'],
'visualFindings':['All48nativeframes show expected openN/Sring, thinE/Wprofile and stable supports. Mainhoop breathes and ornaments advance around it; no fullframe clipping visible.','Currentlogical and phone evidence keeps cyanring recognizable, but the source lowernavy surfaces lose detail against dark background and the broadcyan bands readflat. These are baseline design improvement opportunities, not a candidate rejection.','Both browser configurations visibly agree on the prepared isolatedfixture. Their exact screenshot decoded pixels also match on allthree backgrounds.','Timedactualbrowser recording sheets show advancing rim/ornament state and a loop crossing; frameupdate logs cover0..26 in sequence without skips. Fixture intentionally holds at the end; rawsource remains looptrue.'],
'provenanceFindings':metrics,
'notApproved':['Any model/candidate','A frozen technical/designbudget','The portal family or separateportal-entry','Production/library/Godot/preview publishing'],
'nextOwner':'ROOT reconciles root-native-contract.json and criteria.json, freezes exact versions, then dispatches a fresh editor.'})
# Environment records document installed runtimes without copying app/runtime trees.
env={'python':platform.python_version(),'pillow':Image.__version__,'blender':ins['blender'],'node':subprocess.run(['node','--version'],capture_output=True,text=True,check=True).stdout.strip(),'packages':{},'ffmpeg':subprocess.run(['/opt/homebrew/bin/ffmpeg','-version'],capture_output=True,text=True,check=True).stdout.splitlines()[0],'dependencyPolicy':'Project .blend and exact actual-used own scripts, inputs, capture modules, unchangedconsumer helpers, rawcaptures and evidence are sealed. Runtime binaries/stdlib/npm application trees are environment requirements, not copied project resources. No textures/libraries occur in active portal material graph; no foreignparent/modifierobject/rig dependencies.'}
for pkg in ['vite','@playwright/test','react']:
 out=subprocess.run(['node','-p',f"require('{pkg}/package.json').version"],capture_output=True,text=True)
 env['packages'][pkg]=out.stdout.strip() if out.returncode==0 else 'unavailable as direct package.json; see frozen lockfile'
w('environment.json',env)
(P/'README.txt').write_text('Portal rim independent judge preparation v1\n\nRead initial.json and criteria.json for the independent interpretation. Read root-native-contract.json for the proposed technical/design contract; ROOT must reconcile and freeze it before a fresh editor. scoped-evidence-plan.json separates completedbaseline evidence from future candidate requirements.\n\nNative replay:48requiredframes, actual4x camera/capture, unchanged source and10saved object actions. All48uniformly reduced2xcells are decoded RGBA-exact with the original atlases. Raw/evaluated measurements and finite z0 contact hulls remain separate from permittednewdesignbudget.\n\nBrowser:exact pinnedcurrenthelpers, bothdocumentedheadlessmodes, viewport840x780,DPR1, logical1/phone0.55,light/gray/dark. Actual2.2secondplayback retainedinWebM; fixture holdsitslastdemonstrationframeafterward. No candidate, production, family, device, Godot or publishing approval.\n\nAll filepaths in hash-manifest.json are relative to the portal-rim object directory. seal.json binds that manifest; it is a preparation integrity seal only. Runtimes remain external environment dependencies.\n')
print('PORTAL_PREPARATION_READY_TO_SEAL',len(inspected))
