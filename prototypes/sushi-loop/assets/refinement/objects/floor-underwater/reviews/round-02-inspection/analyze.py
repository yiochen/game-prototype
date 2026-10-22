import sys,json,hashlib,os,collections,shutil
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;O=P.parent.parent;RUN=O.parent.parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def desc(p):return {'path':os.path.relpath(p,O),'sha256':sha(p),'bytes':p.stat().st_size,'relativeTo':'object','pathBase':str(O)}
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
proof=RUN/'verification/fractional-world-raster-v1';root=read(proof/'root-verification.json')
for name,r in root['files'].items():assert sha(proof/name)==r['sha256'] and (proof/name).stat().st_size==r['bytes']
assert (P/'resources/world-raster-functions.js').read_bytes()==(proof/'world-raster-functions.js').read_bytes()
old=read(O/'candidates/round-01/fullchrome-control/consumer-report.json');assert len(old['cases'])==1476
failures=[c for c in old['cases'] if c['interiorAlpha']['nonOpaque']];assert len(failures)==264;assert min(c['interiorAlpha']['minAlpha'] for c in old['cases'])==128
fields=['direction','phase','kind','background','width','offset','pan','context','bounds','plan','sprites','smoothingAfterResize'];reports=[]
for backend in ['full-chrome','headless-shell']:
 r=read(P/backend/'report.json');rr=read(proof/backend/'report.json');assert len(r['cases'])==len(rr['cases'])==len(old['cases'])==1476
 for before,now,provided in zip(old['cases'],r['cases'],rr['cases']):
  assert all(before[k]==now[k]==provided[k] for k in fields)
  assert now['interiorAlpha']['minAlpha']==255 and now['interiorAlpha']['nonOpaque']==0 and now['smoothingAfterResize'] is False
  assert now['interiorAlpha']==provided['interiorAlpha']
 assert r['errors']==[]
 for playback in r['playback']:
  phases=[x['phase'] for x in playback['transitions']];assert set(phases)==set(range(12));assert phases.count(0)>=2;assert playback['fps']==12 and playback['periodSeconds']==1
 current=[x for x in r['regressions'] if x['renderer']=='current'];assert all(c['result']['interiorAlpha']['minAlpha']==255 for c in current)
 if backend=='full-chrome':assert [x['result']['interiorAlpha']['minAlpha'] for x in r['regressions'] if x['renderer']=='old']==[191,128]
 reports.append({'backend':backend,'independentReport':desc(P/backend/'report.json'),'providedRootReport':desc(proof/backend/'report.json'),'cases':1476,'minimumInteriorAlpha':255,'alphaFailures':0,'actualPlaybackRuns':len(r['playback']),'allPlaybacksVisitEveryPhaseAndWrap':True,'everyInputRootPanFrameRectScaleBoundsAndPainterSequenceExactToOldAndRoot':True,'errors':[]})
# Snapshot the actual React consumer that supplies registered positions to the audited current functions.
consumer=O/'../../../../wireframe/object-review.jsx';shutil.copyfile(consumer,P/'resources/object-review.jsx')
write(P/'technical-summary.json',{
 'asset':'floor-underwater','round':'round-02','candidatePacket':desc(O/'candidates/round-02/packet.json'),
 'nativeArtReuse':{'review':desc(O/'reviews/round-01.json'),'manifest':desc(O/'reviews/round-01-inspection/manifest.json'),'filesRehashed':770,'mediaReused':37,'coverageMap':desc(P/'coverage-map.json'),'nativeSource':desc(O/'source/round-01.blend'),'findings':'Original judge prior actual native source replay, analytical UV edge/corner/loop controls, all-phase raw/export/native/independent opacity and APNG decoding/playback remain valid for exact bytes. No source/camera/sampling/art re-render or adjustment occurred.'},
 'priorRuntimeFailurePreserved':{'report':desc(O/'candidates/round-01/fullchrome-control/consumer-report.json'),'oldRenderer':desc(P/'resources/world-sprite-raster-old.js'),'totalCases':1476,'failedCases':264,'minAlphaHistogram':dict(collections.Counter(c['interiorAlpha']['minAlpha'] for c in failures)),'aggregateMinimum':128,'independentFreshNegativeControl':'Full Chrome old-helper first/worst inputs re-executed at original positions: alpha191/128 with1532 deficient pixels; current same inputs255/0. Old packet/review remains needs_evidence.'},
 'currentRenderer':{'liveSource':desc(O/'../../../../wireframe/world-sprite-raster.js'),'frozenSource':desc(P/'resources/world-sprite-raster.js'),'exactExecutableExcerpt':desc(P/'resources/world-raster-functions.js'),'exactMatchesProvidedProofExcerpt':True,'actualReactIntegrationSnapshot':desc(P/'resources/object-review.jsx'),'diff':desc(P/'resources/renderer.diff'),'audit':'worldRasterPlan, sprite source rectangles/root/scale/registration, draw order and hook integration stay exact. Only consecutive sprites whose native relative offsets and dimensions are integral may share a temporary native layer. Layer uses exact source rectangles at integer relative coordinates; common original fractional translation applied once. Differently phased actors stop the group; no phase gathering across them. No geometry growth, pixel repair, individual position shift, fit or backend waiver.'},
 'fullRequiredMatrix':reports,'matrixDefinition':{'base':{'kinds':['native','independent'],'facings':list('NESW'),'phases':list(range(12)),'offsets':[[0,0],[.125,.375],[.25,.5],[.5,.25],[.875,.625]],'pan':'swapped root offset axes','backgrounds':['#f5f5f0','#808080','#14181e'],'width':320,'cases':1440},'logicalPatchAdditional':{'kinds':['native','independent'],'facings':list('NESW'),'phases':[0,3,6],'offset':[.25,.5],'pan':[.5,.25],'threeBackgrounds':True,'width':435.2,'cases':24},'contextAdditional':{'kind':'independent','facings':list('NESW'),'phases':[0,3,6],'offset':[.25,.5],'pan':[.5,.25],'threeBackgrounds':True,'width':360,'actualFrozenActors':['submarine-yellow','rock-wall-middle'],'cases':12},'nativeInteriorSample':[766,766],'alphaCriterion':'all interior sampled bytes255, zero nonopaque; outside finite patch edge not mistaken for interior gap'},
 'orderControl':{'report':desc(P/'order-control.json'),'casesPerBackend':15,'exactAssetAtlas':True,'phases':[0,5,11],'offsets':5,'translucentDifferentPhaseActorThenSamePhaseForeground':True,'allRGBADifferences':0,'allAlphaFailures':0,'scope':'Required asset use only; no blanket renderer correctness conclusion'},
 'newDirectVisualObservations':['Both exact new packet browser previews show connected pale ridges and soft aqua water beneath legible submarine and rock; no fine rectangular transparency grid.','Fresh full-Chrome current worst-case phase5 image has continuous branches; old-helper same-input screenshot retains the thin white border grid.','Fresh N/E/W context screenshots preserve the calm coherent water and foreground color separation at phone width.','Prior accepted target differences are unchanged: thinner/more uniform ridges and simpler grain-free pockets; a readable native cartoon interpretation.'],
 'rootProvidedProof':{'rootVerification':desc(proof/'root-verification.json'),'allListedFilesIndependentlyRehashed':len(root['files']),'allCaseMetadataAndCoverageMatchedIndependentReplay':True,'notApprovalAuthority':True},
 'limits':['No approval of old failed packet. No mixed-facing arbitrary joins or independently phased neighbors are inferred. No family/other-object/deferred2D-effect approval.','Remote deployment context is outside this asset verdict; the candidate art has not been promoted/deployed. Current source/helper and exact local dual-backend asset evidence are the basis.'],
 'processNote':'A preliminary own-resource preparation lookup used the wrong old-helper path; it was corrected to the exact sealed preparation-v1 helper before any capture. No candidate data changed.'})
print(json.dumps({'rootProofFilesRehashed':len(root['files']),'sameInputsSpritesAndPlanAllCases':True,'bothBackendsCases':2952,'zeroAlphaFailures':True,'negativeControlFullChrome':[191,128],'old264FailureMinimum':128}))
