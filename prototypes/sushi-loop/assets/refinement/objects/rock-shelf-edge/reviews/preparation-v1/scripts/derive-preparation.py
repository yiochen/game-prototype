from pathlib import Path
import json,hashlib,math,shutil,sys,platform
from PIL import Image,ImageChops
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent.parent
ROOT=BASE.parents[8] if False else Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
EXP=BASE.parent.parent
ASSET=ROOT/'prototypes/sushi-loop/assets'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Retain exactly the images/metadata inspected in the independent first pass.
extras={
 'references/original.png':EXP/'inputs/original.png',
 'references/target.png':EXP/'inputs/target.png',
 'references/family-concept.png':EXP/'inputs/family-concept.png',
 'references/warm-soft-reference.png':ASSET/'refinement/style/warm-soft-reference.png',
 'metadata/brief.json':EXP/'brief.json'}
manifest=[item for item in json.loads((BASE/'input-manifest.json').read_text()) if item['path'] not in extras]
for rel,p in extras.items():
 q=BASE/'resources'/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
 manifest.append({'path':rel,'source':str(p),'sha256':sha(q),'bytes':q.stat().st_size})
(BASE/'input-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
original=json.loads((BASE/'original-native-measurements.json').read_text())
canonical=json.loads((BASE/'canonical-native-measurements.json').read_text())
def core(d):return next(o for o in d['objects'] if o.get('endpointFaces'))
a,b=core(original),core(canonical)
ports={}
for p in ['W','E']:
 af=a['endpointFaces'][p];bf=b['endpointFaces'][p]
 ac=next(f for f in af if f['cap']);bc=next(f for f in bf if f['cap'])
 ap=sorted(c['position'] for c in ac['corners']);bp=sorted(c['position'] for c in bc['corners'])
 err=max(abs(x-y) for u,v in zip(ap,bp) for x,y in zip(u,v))
 ports[p]={'geometricProfileMaxAbsError':err,'sameGeometry':err<1e-7,'canonicalCap':bc,'canonicalAdjacentFaces':[{**f,'corners':[c for c in f['corners'] if abs(abs(c['position'][0])-.5)<1e-6]} for f in bf if not f['cap']],'sourceAdjacentFaces':[{**f,'corners':[c for c in f['corners'] if abs(abs(c['position'][0])-.5)<1e-6]} for f in af if not f['cap']]}
compat={
 'asset':'rock-shelf-edge','mode':'preparation-only','canonical':{'blendSHA256':sha(BASE/'resources/canonical/round-03.blend'),'packetSHA256':sha(BASE/'resources/canonical/packet.json'),'technicalBasis':'actual reopened native evaluated mesh, corner normals, point albedo attribute and material nodes; no aesthetic reviews read'},
 'originalGeometryCompatible':True,'originalNormalFieldCompatible':False,'originalShaderAlbedoCompatible':False,
 'sourceFeasibility':'Native reconstruction is feasible within the source finite envelope and canonical port profile. Existing flat port normals and dark world-height ramp are not compatible with canonical smooth field and blue-cyan shader as-is. The source topology/part count is not locked; editor must realize useful target-inspired low rock forms while carrying the exact canonical boundary field.',
 'ports':ports,
 'canonicalMaterialRecords':'canonical-native-measurements.json#/materials',
 'canonicalMainShader':{'attribute':'rock_shelf_albedo, FLOAT_COLOR POINT','roughness':.47,'specularIOR':.24,'coatWeight':.09,'coatRoughness':.35,'emissionStrength':.11,'emissionColor':'same point albedo'},
 'canonicalCutfaceShader':'Exact native planar cut stone v3 node graph retained in canonical-native-measurements.json; Object local Y*2.2 and Z*4.5 2D DISTANCE_TO_EDGE Voronoi(randomness.55), EASE color ramp(.005/.045/.13) and native bump. Both ports preserve signed localY and nativeZ; localX is unused. Do not reflect coordinates.',
 'canonicalNormalField':'Use actual corner-normal samples and field from hash-bound canonical source. At Z0 exposed side normal is (0,±1,0); at Z.28 it is approximately (0,±1,.000062242); at top Y±.39/Z.43 approximately (0,±.348958,.937139), shared by the shoulder and crown. Bottom remains -Z; planar cap remains outward ±X. Tiny stored normal compression values are retained as evidence, not permission to simplify to flat normals.',
 'toleranceProposal':{'geometryAbsWorld':1e-6,'albedoAbsLinear':1e-6,'unitNormalComponent':1e-5,'warning':'Numerical tolerances support native identity checks only. All required visible family assemblies still must pass; aggregate pixel errors do not waive visible seams.'},
 'unresolvedCandidateEvidence':'No derivative candidate exists. No mixed-family source or candidate assembly was constructed/approved in this preparation. Native direct versus independently rendered family RGB residuals require the future evidence matrix; original single-asset replay residual is exactly zero.'}
(BASE/'compatibility.json').write_text(json.dumps(compat,indent=2)+'\n')
directions={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}
assemblies=[]
for d,ang in directions.items():
 u=[round(math.cos(ang)),round(math.sin(ang)),0]
 placements=[{'asset':'rock-shelf-middle','source':'exact approved round-03','nativeRoot':[-u[0],-u[1],0],'rotationZ':ang,'facing':d,'contact':'middle E -> edge W'},{'asset':'rock-shelf-edge','source':'future hash-bound derivative candidate','nativeRoot':[0,0,0],'rotationZ':ang,'facing':d,'contact':'W and E'},{'asset':'rock-shelf-middle','source':'exact approved round-03','nativeRoot':u,'rotationZ':ang,'facing':d,'contact':'edge E -> middle W'}]
 for p in placements:p['logicalRootOffset']=[128*p['nativeRoot'][0],-128*p['nativeRoot'][1]]
 assemblies.append({'direction':d,'placements':placements,'nativeContactPlanes':'Both true contacts lie exactly half a pitch from center, in this common authored rotation; no reflection or overlap. Root-to-root pitch1 native /128 logical.','exposedEnds':'Outside middle cutfaces stay open for cap/field inspection.'})
plan={
 'status':'required evidence proposal; root freeze before editor','asset':'rock-shelf-edge',
 'identity':{'canonicalBlend':sha(BASE/'resources/canonical/round-03.blend'),'canonicalPacket':sha(BASE/'resources/canonical/packet.json'),'worldRaster':sha(BASE/'resources/consumer/world-sprite-raster.js'),'spriteLayout':sha(BASE/'resources/consumer/sprite-layout.js')},
 'assemblies':assemblies,
 'separateSinglePortControls':['edge W connected to exact middle E; opposite edge E exposed','edge E connected to exact middle W; opposite edge W exposed'],
 'extendedControl':'A longer straight mixed run with two edge placements separated by canonical middles, all four rotations, using exact source contact phase. No corner/end assumption is introduced by the edge name.',
 'renderPairs':[
 {'id':'native-joined','method':'Load exact candidate plus exact approved middle geometry. Apply only authored shared root rotations/translations. Render whole connected assembly once using the same common canonical light rig and camera.'},
 {'id':'independent','method':'Use actual single-asset native4x captures, common filter0.5, complete-canvas BOX4x->2x. Assemble ordinary 2x atlas sprites at their registered roots through unchanged current consumer functions. No RGB/alpha repair, extra overlap, per-view offsets, fits, hidden caps or runtime helpers.'}],
 'nativeCanvas':{'logicalFrame':[448,608],'logicalRoot':[224,376],'captureScale':4,'nativeFrame':[1792,2432],'publicationScale':2,'publishedFrame':[896,1216],'projection':'same registered55.0079798/aspect1.22065556; common frame chosen before capture and unchanged across directions/pairs'},
 'consumer':{'functions':['spriteFrame','groundRoot','orderPlacements','worldRasterPlan','paintWorldRaster'],'sourceScale':2,'cell':128,'composition':'Actual source-scale common world canvas; imageSmoothingEnabled=false within it; ordinary complete canvas CSS/browser filtering after composition. Preserve current plan guard and painter order.','browserEvidence':'Use real browser screenshots from fixed layout. Pure functions may be imported with a local unused React-hook stub; the two frozen consumer modules themselves remain exact. Save exact harness, driver, browser version/DPR and logs.'},
 'presentationMatrix':{'backgrounds':{'light':'#eef2ed','gray':'#909090','dark':'#172539'},'logicalCellSizes':[128,32],'directions':['N','E','S','W'],'basePhase':0,'fractionalTests':[
 {'id':'css','method':'Move whole completed canvas relative to page at logical offsets(.25,0),(.5,.5),(.75,.25); both128 and32 cells, actual resulting physical offsets recorded.'},
 {'id':'world-root','method':'Common fractional root offsets(0,0),(.25,.25),(.5,.75),(.75,.5)logical pixels for all contacting modules, preserving exact relative pitch.'},
 {'id':'pan','method':'Change raster bounds/camera pan through phases0,.25,.5,.75 logical in each axis with fixed world roots; include representative paired fractional offsets and record actual worldRasterPlan origin.'}],
 'all4EveryBackground':True,'fractionalPhaseBackground':'gray plus light/dark at any suspicious join; inspect phone32 directly and enlarged crops alongside native128.'},
 'measurements':['Verify all exact source/packet/resource hashes and no frozen-byte changes.','Reopen native source; measure root, profile, endpoint material/albedo/custom corner normals, bounds, support/ground, no animation/rig drift, camera/lighting/sampling and own atlas metadata.','Measure alpha only on actual native opaque support/exposed surfaces, including local seam neighborhoods. Do not demand opaque full cells or import a tall-wall/floor test.','Compare native joined and independent assembly: record alpha deficits, straight/composited RGB max/mean, local seam traces and local crops separately from broad finite-area-light shading residuals.','Review visible seams, exposed end closure, clipping, halos, dark cavities, form/decor readability, and light/gray/dark silhouettes for all required views. No numerical-only waiver.'],
 'delivery':'Exact candidate blend plus minimal used module/resource closure, all4 raw native and2x atlases, native mixed assemblies, independent consumer captures, explicit pose/camera ledger and native validation, packet manifest. Judge returns needs_evidence if any required slice is missing. No candidate/family approval is issued now.'}
(BASE/'assembly-evidence-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
contract={
 'asset':'rock-shelf-edge','version':1,'status':'judge-proposed; root freeze required; preparation only',
 'independence':'Own original/target/family/reference and actual original collection inspected and initial.json plus criteria.json saved before canonical technical source was read. No editor proposals or other object aesthetic review read.',
 'source':{'blendSHA256':sha(BASE/'resources/source/source.blend'),'collection':original['collection'],'root':original['root'],'rootMatrix':original['rootMatrix'],'basis':{'X':'X','depth':'-Y','height':'Z'},'measurements':'original-native-measurements.json','evaluationCaveat':'Original whole-library hidden viewport layers yield stale child transforms if sampled without enabling layers/object viewport evaluation. Final measurement explicitly enables native layer collection and updates graph; replay camera registration plus byte-identical atlas output independently confirms interpretation.'},
 'role':{'kind':'terrain','footprint':[1,1],'nonblocking':False,'rootCell':[.5,.5],'occupiedCells':[[0,0]],'supportCells':[[0,0]],'overheadCells':[],'sockets':{}},
 'functionalEnvelope':{'actualAllGeometryBounds':original['bounds'],'actualGroundBounds':original['groundBounds'],'nominalMaxHeight':.45,'coreMaxZ':a['bounds'][1][2],'designEnvelopeProposal':[[-.5,-.5090895891189575,0],[.5,.45,.45]],'groundSupportPolicy':'Keep finite core ground at X[-.5,.5],Y[-.45,.45],Z0; no full1x1 opaque slab/floor. Source edge dressing extends in negativeY to-.509089589 with all flakeZ>=.019999996, while ground footprint remains unchanged. Preserve this actual finite decorative allowance, do not infer symmetric fullcell fill.','metadataReconciliation':'1x1 describes collision/placement cells, not a promise that every decorative vertex lies within +/-0.5. Actual original flake extends0.009089589 beyond negativeY nominal cell and is elevated. Root should explicitly freeze this measured distinction before editor work.'},
 'ports':{'profileId':'rock-shelf-section-v1','actualVariant':'straight two-port with negativeY side flake; no turn; no terminated port','planes':{'W':{'axis':'X','value':-.5,'origin':[-.5,0,0],'normal':[-1,0,0]},'E':{'axis':'X','value':.5,'origin':[.5,0,0],'normal':[1,0,0]}},'orderedYZ':[[-.45,0],[.45,0],[.45,.28],[.39,.43],[-.39,.43],[-.45,.28]],'pitch':1,'handedness':'Local transverse+Y retained at both ports. Straight same-facing canonical middle at each root±rotatedX; no reflection. The edge has two closed planar caps in isolated native source; both caps become internal when matched. Broad±Y sides are non-port exposed boundaries.','canonicalEndpointAuthority':'resources/canonical/round-03.blend exact SHA3e6c7cbe865a918dbeec5faf1a48af540f6290e7afc41ef4c987162617199422; actual endpoint corner-normal, point albedo and material/shader field in compatibility.json. Boundary geometry alone is insufficient.','noJoinRepairs':['no rounding across true cutplanes','no vertex/cap overhang beyond X±.5','no overlap concealment','no RGB or alpha editing','no per-view offsets or fit','no gaps or exposed internal caps']},
 'capture':{'projection':'top-down-oblique-square-grid','cameraElevationDegrees':55.00797980144134,'pixelAspect':[1.2206555604934692,1],'cameraType':'ORTHO','orthoScale':1.5,'sensorFit':'HORIZONTAL','logicalFrame':[192,352],'logicalRoot':[96,248],'cell':128,'nativeScale':4,'nativeFrame':[768,1408],'publishScale':2,'publishFrame':[384,704],'cardinalRotationZ':directions,'unitProjectionLogical':{'root':[96,248],'X':[128,0],'depth':[0,128],'height':[0,-89.6]},'noPerViewFit':True,'saved35Camera':'Whole-library presentation camera768x1280/aspect1 is incidental; all4 exact registered replay establishes the source55.0079798 contract.'},
 'staticMotion':{'clip':'static','uniqueFrames':1,'nativeFrame':1,'fps':12,'loop':False,'allDirections':['N','E','S','W'],'armatures':0,'actions':'none on own objects, materials or node trees; no shape keys'},
 'canonicalNativeResources':{'endpointMaterialNormalField':'Exact canonical round03 source, measured in compatibility.json. Interior construction may improve, while boundary field must remain continuous.','lighting':'Canonical broad finite symmetric rig: overhead850W at(0,0,18),DISK15; four1850W cardinal fills at radius15,Z6,DISK12 targeting(0,0,.2); use_shadowFalse; world0; no ground receiver. One common rig for all required single and assembly views. Actual rig stored in canonical-native-measurements.json.','shader':'Canonical blue-cyan main material and planar cutface field, retained exact in canonical-native-measurements.json and canonical blend. Original dark ramp/flat fields are baseline evidence, not family-compatible input.'},
 'sampling':{'engine':'BLENDER_EEVEE','samples':32,'filterSize':.5,'publish':'Uniform complete-frame BOX4x-to2x, alpha and RGB unchanged except ordinary resampling. Actual current consumer does native common-grid composition then whole canvas browser filtering.','historicalReplay':'Exact all4 byte match with historical filter1.5+whole-frameLANCZOS. Historical bytes unchanged. canonical-sampling captures are diagnostic new outputs only; no join seam pass is inferred from single renders.'},
 'visibleCriteria':'../criteria.json','compatibility':'compatibility.json','requiredFamilyEvidence':'assembly-evidence-plan.json',
 'freedom':'Native form/proportion/construction/decoration/topology may change usefully within hard finite registration/port/height/support/animation constraints. Keep blue/cyan rock role; original three cracks and one flake count are not design constraints. Target image proportions, painterly halo, bright caustic strokes or tallwall/fullcell floor laws are not technical authority.',
 'verdict':'Preparation complete for root reconciliation/freeze only. No candidate, family, production or integration approval.'}
(BASE/'proposed-root-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
# Honest separate classification of single-source renderer residual and study deltas.
deltas={}
for d in 'NESW':
 aa=Image.open(BASE/f'captures/historical/published-{d}-2x.png').convert('RGBA');bb=Image.open(BASE/f'captures/canonical-sampling/published-{d}-2x.png').convert('RGBA');df=ImageChops.difference(aa,bb)
 deltas[d]={'differentPixels':sum(p!=(0,0,0,0) for p in df.getdata()),'maxRGBA':[x[1] for x in df.getextrema()]}
(BASE/'replay-findings.json').write_text(json.dumps({'historicalAll4ExactPngByteMatch':True,'comparison':'captures/historical/comparison.json','rendererResidualHistorical':{'N':0,'E':0,'S':0,'W':0},'canonicalSamplingDiagnosticDeltaToHistorical':deltas,'classification':'Common .5/BOX study changes edge sampling only; source geometry/material/light preserved. No direct joined-v-independent family comparison has occurred. Broad finite-area-light RGB residuals and visible local joins remain separate mandatory future measurements, with no numerical-only seam waiver.','historicalRawCaptureCaveat':'Guides reference historical source-captures PNG hashes, but raw production source-captures files are absent. Fresh replay raw4x is retained; all4 published PNG bytes match exactly.'},indent=2)+'\n')
# Acknowledge and quarantine the initial stale-graph measurement attempt rather than using it.
(BASE/'measurement-notes.json').write_text(json.dumps({'firstAttempt':'The first original measurement incorrectly saw child identity matrices because whole-library viewport layers were hidden; it reported flake unit-icosphere bounds+-0.8944/0.8506/1 and cracks nearZ0. This was rejected immediately, not interpreted as native source bounds.','repair':'Final measure-native.py explicitly enables all native layer collections, collection viewport flags and object viewport evaluation before graph sampling. Final original native bounds correctly place cracksZ.443..449 and flakeY-.509089589,Z.02..36.','sourceBytesModified':False,'savedFinalEvidence':'original-native-measurements.json','independentConfirmation':'Registered all4 replay exactly matches historical PNG bytes.'},indent=2)+'\n')
# Hash current original input paths after all work; no writes went back to these paths.
checks=[]
for x in manifest:
 p=Path(x['source']);current=sha(p);checks.append({'source':str(p),'retained':x['path'],'expected':x['sha256'],'current':current,'unchanged':current==x['sha256']})
assert all(c['unchanged'] for c in checks)
(BASE/'frozen-input-verification.json').write_text(json.dumps(checks,indent=2)+'\n')
(BASE/'environment.json').write_text(json.dumps({'pythonExecutable':sys.executable,'pythonVersion':sys.version,'platform':platform.platform(),'pillowVersion':Image.__version__,'blenderExecutable':'/opt/homebrew/bin/blender','blenderVersion':'5.2.2 LTS d13f752e3b9c','blenderBinarySHA256':sha(Path('/opt/homebrew/bin/blender')),'pythonBinarySHA256':sha(Path(sys.executable)),'bytecodeWrites':'disabled by PYTHONDONTWRITEBYTECODE=1 and sys.dont_write_bytecode=True; imported private files only inside own reviews resources','scope':'No Git, production edits, source-model save, candidate construction, live Blender, device, runtime mutation or extra agents.'},indent=2)+'\n')
print(json.dumps({'portsGeometricErrors':{p:v['geometricProfileMaxAbsError'] for p,v in ports.items()},'sourceBounds':original['bounds'],'canonicalBounds':canonical['bounds'],'filesCreated':['compatibility.json','assembly-evidence-plan.json','proposed-root-contract.json','replay-findings.json','frozen-input-verification.json'],'allInputSourcesUnchanged':True},indent=2))
