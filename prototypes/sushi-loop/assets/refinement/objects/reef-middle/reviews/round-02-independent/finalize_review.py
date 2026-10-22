import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json,os,shutil
import PIL
B=Path(__file__).resolve().parent;O=B.parent.parent;P=O/'candidates/round-02';REPO=O.parents[5]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def desc(p):return {'path':os.path.relpath(Path(p),O),'sha256':sha(p),'relativeTo':'experiment'}
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
packetsha=sha(P/'packet.json');assert packetsha=='d60ff36edc6006a0d4082692e7c115be23e1fc1e9d674f8bdc5c2f8ccc447ca8';packet=json.loads((P/'packet.json').read_text())
assert sha(O/'source/round-02.blend')=='51d515119c1a229f57f3b242fdf040b28ef00121692cb3d40d8821dab70ff3c5'
assert sha(REPO/'prototypes/sushi-loop/wireframe/world-sprite-raster.js')==sha(B/'resources/consumer/world-sprite-raster.js')=='570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545'
assert sha(REPO/'prototypes/sushi-loop/wireframe/sprite-layout.js')==sha(B/'resources/consumer/sprite-layout.js')=='099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65'
for package,filename in [('@playwright/test','playwright-test-package.json'),('playwright','playwright-package.json'),('playwright-core','playwright-core-package.json')]:
 src=REPO/'node_modules'/package/'package.json';dst=B/'resources/toolchain'/filename;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
write(B/'resources/toolchain/python-runtime.json',{'pythonExecutable':sys.executable,'python':sys.version,'pythonBinarySHA256':sha(sys.executable),'Pillow':PIL.__version__,'BlenderRuntime':'Actual5.2.2LTS and Python in reopened-native-audit.json and native logs','NodeBrowserRuntime':'Actual executable/hash/options/versions in evidence/toolchain.json/browser-launch.log','infrastructureBoundary':'Installed Blender/Python/Pillow/Node/Playwright/Chrome are execution infrastructure. Exact submitted review drivers and used consumer modules are frozen; no runtime tree clone.'})
base='prototypes/sushi-loop/assets/refinement/objects/reef-middle/reviews/round-02-independent/'
py='/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
commands=[f'PYTHONDONTWRITEBYTECODE=1 {py} {base}prepare_review.py',
 f'PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/blender --background --factory-startup --python {base}reopen_audit.py > {base}reopen.log 2>&1',
 f'DEBUG=pw:browser node {base}independent_consumer_replay.cjs > {base}browser-launch.log 2>&1',
 f'PYTHONDONTWRITEBYTECODE=1 {py} {base}analyze_native.py',f'PYTHONDONTWRITEBYTECODE=1 {py} {base}consumer_and_coverage.py',
 f'PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/blender --background --factory-startup --python {base}ground_and_strip_audit.py > {base}ground-and-strip.log 2>&1',
 f'PYTHONDONTWRITEBYTECODE=1 {py} {base}complete_checks.py',
 f'PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/blender --background --factory-startup --python {base}ground_and_strip_vector_audit.py > {base}ground-and-strip-vector.log 2>&1',
 f'PYTHONDONTWRITEBYTECODE=1 {py} {base}analyze_matched_strips.py > {base}matched-strip-analysis.log 2>&1',f'PYTHONDONTWRITEBYTECODE=1 {py} {base}finalize_review.py']
(B/'commands.txt').write_text('CWD: '+str(REPO)+'\n\nExact actual native/browser/analysis invocations. Drivers and frozen native/consumer inputs were saved before native/browser execution. The bounded Vector follow-up preserves all prior list-arithmetic outputs. Runtime versions/child argv were recorded during execution. Two exploratory inline analyses were subsequently retained as complete_checks.py and analyze_matched_strips.py; the latter was also rerun as the saved driver. No construction recipe was executed.\n\n'+'\n\n'.join(commands)+'\n\nFinal acceptance invocation/output/status are retained separately after final review hash.\n')
inspected=[v['path'] for group in ['candidateRenders','previews'] for v in packet[group].values()]
coverage=json.loads((B/'evidence/coverage-map.json').read_text())
write(B/'inspection-coverage.json',{'candidatePacketSHA256':packetsha,'packetInspectedFiles':inspected,
 'method':'All4 exact packet heroes and all6 exact declared preview files actually viewed. repeated/shell-repeated/fractional additionally viewed through complete1:1pixel-preserving pieces. Fixed-scale before/after inspected as pixel evidence together with actual heroes/use-size, without editor rationale or self-ratings.',
 'allDeclaredPreviewsStatic':True,'noMotionRequired':'Static1frame/nativeframe1/nonloop/12fps/all4 only. No motion clip declared.',
 'fullPixelCoverageOfLargeSheets':coverage['largePreviewCoverage'],
 'additionalActualInspection':['evidence/visual-closeup-N.png','evidence/visual-closeup-E.png','evidence/visual-closeup-S.png','evidence/visual-closeup-W.png','evidence/own-actual-fractional-replay-sheet.png'],
 'nativeHeroAlias':'Independent reopened heroes verified decodedRGBA-identical to packet heroes. Strip residuals are separately retained and are not falsely called exact aliases.'})
files={}
for p in B.rglob('*'):
 if p.is_file() and p.name not in ['manifest.json','postreview-seal.json','final-gate.json','final-gate.log','run_final_gate.py']:
  files[str(p.resolve())]=p
for group in ['files','candidateRenders','previews']:
 for v in packet[group].values():
  p=(P/v['path']).resolve();assert sha(p)==v['sha256'];files[str(p)]=p
files[str((P/'packet.json').resolve())]=P/'packet.json'
assert all(p.stat().st_size<100_000_000 for p in files.values())
assert not any('__pycache__' in p.parts and p.is_relative_to(B) for p in files.values())
manifest={'asset':'reef-middle','round':'round-02','candidatePacketSHA256':packetsha,'relativeTo':'experiment','pathBase':str(O),
 'scope':'Exact candidate-bound independent review. Full exact packet resource closure and only actual used review inputs/drivers/evidence retained. Prior sealed artifacts/source/target/criteria/production untouched.',
 'files':[dict(desc(p),bytes=p.stat().st_size) for p in sorted(files.values())],
 'visualCoverage':desc(B/'inspection-coverage.json'),'exclusions':'Final review, final-gate and postreviewseal bound separately to avoid self-hashcycles; no installed runtime tree clone.'}
write(B/'manifest.json',manifest)
consumer=json.loads((B/'evidence/independent-consumer-findings.json').read_text())['reports']
review={'asset':'reef-middle','round':'round-02','independentReview':True,'verdict':'approve',
 'candidatePacketSHA256':packetsha,'sourceSHA256':sha(O/'source/round-02.blend'),'briefSHA256':sha(O/'brief.json'),'nativeContractSHA256':sha(O/'inputs/root-native-contract.json'),
 'inspectedFiles':inspected,'scores':{'shapeVolume':8,'color':7,'lightingHighlights':7,'materialDetail':7,'artifactFreeReadability':8},
 'observations':[
  'The prior support-massing/stone-separation blocker is resolved. Raised blue boulders now have clear light top planes and darker side volumes instead of near-flat cyan outline fragments. All4 views show distinct stones at logical128; at phone32 they simplify into a coherent blue reef support without losing the teal focal/purple supporting hierarchy.',
  'The central support has meaningful stepped relief and large plane changes in its front/side bands. Together with the selected larger stones it reads as a crafted reef-rock mass rather than the previous blank slab carrying tubes. The fixed-scale round01/02 comparison agrees with the direct native and use-size inspection.',
  'The hollow teal focal group and two purple tube clusters remain clear, with local dark openings and soft rounded bright rims. The blue/cyan, teal and purple palette remains coherent, with readable broad midtones and no broad black base or clipped white sparkle.',
  'All4 required facings have useful silhouette/volume and purposeful large detail. I found no materially dead side, clipping, coplanar flash, artificial glow/fringe or directional ground shadow in the inspected native/use-size/context images.',
  'All4 actual native and independent three-middle assemblies, baseline and representative fractional root/pan previews, show no visibly identified true local alpha crack, dark/light join stripe, step or exposed internal cap at logical128 or phone32 on light/gray/dark. The numerical residuals remain separately reported rather than waived.',
  'The saved source was independently reopened without running construction. All4 hero pixels replay exactly. Evaluated exact8point ports, adjacent triangle/corner normals and actual native Position.Z albedo graphs establish continuous cut/band fields. The finite rectangular ground, closed core, private meshes, envelope, static resources, registered direct2x camera/filter and symmetric native lights pass.'
 ],
 'blockers':[],
 'resolvedPriorBlockers':[{'id':'reef-support-massing-and-stone-separation','priorReview':'reviews/round-01.json','outcome':'Larger raised blue stones and stepped central relief establish clear rock volume and plane hierarchy in all4 intended-size views while preserving coral grouping and exact functional ports.','evidenceFiles':['frames/static/N/000.png','frames/static/E/000.png','frames/static/S/000.png','frames/static/W/000.png','use-size-sheet.png','round-01-round-02-comparison.png']}],
 'remainingDifferences':[
  'The native design is simpler and more faceted than the richly terraced single-view ImageGen target, with fewer coral branches and small ornaments. Its selected larger forms supply the required readable reef hierarchy; literal ornament density is not required.',
  'Some broad planar spans remain near the exact finite interfaces. In context they form a coherent continuous modular surface around the newly shaped interior, and no longer leave the support visually blank. Literal rounded target ends or extraheight would conflict with the frozen connector/envelope contract.',
  'The native material is matte with broad colored planes rather than the target\u2019s stronger painted/glossy highlights. The soft light, local depth and palette separation satisfy the frozen style outcome without requiring photographic or pixel identity.'
 ],
 'technicalEvidence':{
  'packetIntegrity':desc(B/'packet-integrity.json'),'recordCountVerified':len(json.loads((B/'packet-integrity.json').read_text())['records']),
  'nativeFindings':desc(B/'evidence/independent-native-findings.json'),'groundAndInitialStripReplay':desc(B/'evidence/independent-support-and-strip-findings.json'),
  'matchedArithmeticStripReplay':desc(B/'evidence/matched-arithmetic-strip-findings.json'),'consumerFindings':desc(B/'evidence/independent-consumer-findings.json'),'coverage':desc(B/'inspection-coverage.json'),
  'checks':{'savedSourceIndependentlyReopened':True,'all4DecodedHeroReplayExact':True,'finiteProfileAdjacentCornerNormalsAndNativeAlbedoFields':True,'finiteGroundAreaAndClosedCore':True,'boundsHeightStaticPrivateResources':True,'registeredCameraRootFilterDirect2x':True,'actual570ConsumerIndependentlyReplayed':True,'all10DeclaredMediaPathsActuallyInspected':True},
  'groundArea':.7599999895319343,'coreEdgeIncidence':'All864evaluatedcoreedges have2incidentpolygons;102bottomtriangles tile finite.76rectangle atZ0.',
  'nativeReplayLimits':'Heroes decodedRGBA exact. Initial optional strip driver stored projected coordinates in Python lists and rootY752.0000305, rather than capture float32 Vector rootY751.9999390; all raw differences retained. One matched-arithmetic saved-source replay leaves N/E/S4/6/5pixels with maxRGB1 and exactalpha; Wexact. Editor separately reported6/2/8pixels,maxRGB1,exactalpha,Wexact. Small residual cause is not isolated; no frame is replaced/repaired and strip exactness is not claimed.',
  'consumerScope':'128cases=2backendsx4facingsx2sizesx8root/panpairs; all raw actual/native/independent images and comparison-only equal-extents controls retained.',
  'rawAndCalibratedResiduals':consumer,
  'interpretationLimits':'Actual fullChrome retains large unequal-intermediate nearest-tie residuals (maxalpha255,maxopaqueRGB194,finiteportlocalRGB162). Equal-extents comparison-only controls prove0visiblepixelsdiscarded and exactintegerrestoration; they do not change published art/consumer or waive visible local seams, true-interioralpha or nativefield mismatches. All measured actual finite-port opaque-interior samples have alpha255. Native finite-area-light/context RGB and outer silhouette sampling residuals remain honestly recorded. The approve verdict also relies on inspected actual unmodified consumer joins and independent native field continuity, not a universal RGB/alpha equality claim.',
  'staticCadence':'Static1frame/nativeframe1/nonloop/12fps/all4 only. No motion claim.',
  'gateExpectation':'Unchanged acceptance_contract is run against the final review hash; stdout/status/toolhash are sealed separately.'
 },
 'supplementalEvidence':{'path':'reviews/round-02-independent/manifest.json','sha256':sha(B/'manifest.json')},
 'scope':'Approval of this exact reef-middle round-02 candidate only. No derivative-family, production, deployment or Godot approval.'}
assert len(inspected)==10
write(O/'reviews/round-02.json',review)
for item in manifest['files']:assert sha(O/item['path'])==item['sha256'],item['path']
print(json.dumps({'verdict':review['verdict'],'reviewSHA256':sha(O/'reviews/round-02.json'),'manifestSHA256':sha(B/'manifest.json'),'boundFiles':len(manifest['files'])}))
