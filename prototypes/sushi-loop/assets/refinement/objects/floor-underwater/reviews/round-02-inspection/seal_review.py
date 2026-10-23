import sys,json,hashlib,os,subprocess
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;O=P.parent.parent;RUN=O.parent.parent;REPO=RUN.parents[3]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def desc(p):return {'path':os.path.relpath(p,O),'sha256':sha(p),'bytes':p.stat().st_size,'relativeTo':'object','pathBase':str(O)}
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
packet=O/'candidates/round-02/packet.json';d=read(packet);prior=read(O/'reviews/round-01.json');excluded=[O/'reviews/round-02.json',P/'manifest.json',P/'seal.json',P/'acceptance-tool-output.json']
files={}
for r in read(P/'reuse-audit.json')['packetResources']+read(O/'reviews/round-01-inspection/manifest.json')['files']+read(P/'served-resources.json')['resources']:
 p=(Path(r['pathBase'])/r['path']).resolve();assert sha(p)==r['sha256'] and p.stat().st_size<100_000_000;files[str(p)]=desc(p)
for p in [O/'reviews/round-01.json',O/'reviews/round-01-inspection/manifest.json',O/'reviews/round-01-inspection/seal.json',packet,RUN/'preparation/floor-underwater/publish-consumer-v2.py',O/'../../../../wireframe/world-sprite-raster.js',O/'../../../../wireframe/object-review.jsx',RUN/'tools/acceptance_contract.py']:
 p=p.resolve();files[str(p)]=desc(p)
for p in P.rglob('*'):
 if p.is_file() and p not in excluded:files[str(p.resolve())]=desc(p)
assert sha(RUN/'tools/acceptance_contract.py')==sha(P/'resources/acceptance_contract.py')
old=read(O/'reviews/round-01-inspection/manifest.json')
prerequisites=[r for r in old['runtimePrerequisites'] if r['name'] in ['Python','Node','Chromium']]
headless=Path('/Users/yiouchen/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell');assert headless.is_file()
prerequisites.append({'name':'Chromium headless-shell','executablePath':str(headless),'sha256':sha(headless),'version':'153.0.8010.12 / Playwright revision1243','role':'runtime prerequisite; no copied app tree'})
for r in prerequisites:assert sha(Path(r['executablePath']))==r['sha256']
manifest={'schema':'floor-underwater-round02-original-independent-review-evidence-v1','asset':'floor-underwater','round':'round-02','candidatePacketSHA256':sha(packet),'relativeTo':'object','pathBase':str(O),'coverage':desc(P/'coverage-map.json'),'technicalSummary':desc(P/'technical-summary.json'),'runtimePrerequisites':prerequisites,'reproduction':desc(P/'README.txt'),'files':sorted(files.values(),key=lambda x:x['path']),'excludedSelfAndPostReview':[os.path.relpath(p,O) for p in excluded],'postReviewSeal':'reviews/round-02-inspection/seal.json binds final review, manifest and exact unchanged-tool acceptance stdout to avoid a circular hash graph.','scope':'Approval is for this exact round02 asset packet/native art/current consumer only; old failed packet remains needs_evidence, no family/deployment approval.'}
write(P/'manifest.json',manifest)
review={'asset':'floor-underwater','round':'round-02','verdict':'approve','candidatePacketSHA256':sha(packet),'allChecksPassed':True,'inspectedFiles':[r['path'] for group in ['candidateRenders','previews'] for r in d[group].values()],
 'scores':{'shapeVolume':8,'color':8,'lightingHighlights':7,'materialDetail':8,'artifactFreeReadability':8},
 'scoreNotes':{'shapeVolume':prior['scoreNotes']['shapeVolume'],'artifactFreeReadability':'Current exact shared renderer removes the demonstrated fractional transparency grid; native art is unchanged. Scores describe the outcome and do not replace contract checks.'},
 'observations':[
 'The connected pale caustic network, rounded soft aqua regions and gentle darker pockets improve the original framed two-ribbon water. Optical depth and purposeful detail fit the fixed warm-soft target interpretation while retaining calm turquoise water.',
 'The exact same native source, all raw/published/native-patch/atlas media, APNGs and 37 previously inspected media are hash-proven unchanged. Their all-four-facing/all-phase native, logical, phone, background, loop and periodic edge/corner findings remain valid; explicit receipt and path mappings are in the coverage manifest.',
 'Both new exact packet browser previews and fresh all-four-facing context captures show connected water beneath a legible submarine and rock. No thin rectangular transparency grid, new halo, clipping or harsh directional shadow appears.',
 'Independent complete current-helper replay passes 1476 cases in each Chrome backend with minimum interior alpha255, zero nonopaque interiors or browser errors. All16 actual two-second playbacks visit every phase and wrap. Every input, original root/pan, source rectangle, scale, bounds and painter sequence matches both the old matrix and provided current proof.',
 'Independent fresh old-helper controls still reproduce full-Chrome alpha191 and128 with1532 deficient pixels at the original first/worst inputs. Current same inputs are fully opaque. Old264 failures/minimum128 and round01 needs_evidence verdict remain immutable.',
 'The current fix composes only consecutive sprites with integral native relative placement before applying their common original fractional translation once. Exact asset atlas ordering controls pass15 cases per backend against an ordered reference, including an intervening differently phased translucent actor. No native geometry overhang, pixel repair, position nudge, camera or sampling change is used.'
 ],'blockers':[],'remainingDifferences':prior['remainingDifferences'],'nativeArtBlockingIssues':[],
 'technicalEvidence':{'primaryBindings':'Exact source e432f30d, version brief f92c2dd7, original target/criteria/native contract unchanged; exact current renderer570a0d0d with independent cross-backend replay. Full hashes and explicit path bases are in the supplemental manifest.','coverage':'All4 candidate renders +35 previews:37 original actual visual/APNG inspections reused only with exact path/hash identity,2 new declared browser previews directly opened.','nativeContract':'Prior original judge actual source/camera/native replay/opacity/periodicity/closing-key evidence retained for exact source and all media bytes; no source re-render or sampling adjustment.','runtime':'2952/2952 opaque current matrix cases,16/16 phase-complete wrapping actual playbacks,30/30 ordering control cases without RGBA differences. Old fullChrome264/min128 failure evidence is preserved.','scope':'Only this exact round02 asset art and current consumer evidence; no other object/family, arbitrary mixed-facing or independently phased joins, generic renderer or deployment approval.'},
 'supplementalEvidence':{'path':'reviews/round-02-inspection/manifest.json','sha256':sha(P/'manifest.json'),'relativeTo':'object','pathBase':str(O)},'next':'Keep this review and evidence immutable. Coordinator may use this exact approved packet and unchanged acceptance checks for the authorized handoff; no further judge source or production writes.'}
write(O/'reviews/round-02.json',review)
result=subprocess.run([sys.executable,str(RUN/'tools/acceptance_contract.py'),'floor-underwater','--round','round-02'],capture_output=True,text=True,check=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
(P/'acceptance-tool-output.json').write_text(result.stdout);accept=json.loads(result.stdout);assert accept['sha256']==sha(O/'reviews/round-02.json') and accept['method']=='independent-review'
write(P/'seal.json',{'schema':'floor-underwater-round02-review-seal-v1','candidatePacketSHA256':sha(packet),'review':desc(O/'reviews/round-02.json'),'manifest':desc(P/'manifest.json'),'acceptanceOutput':desc(P/'acceptance-tool-output.json'),'acceptanceTool':desc(RUN/'tools/acceptance_contract.py'),'verdict':'approve','allChecksPassed':True})
print(result.stdout.strip());print(json.dumps({'reviewSHA256':sha(O/'reviews/round-02.json'),'manifestSHA256':sha(P/'manifest.json'),'sealSHA256':sha(P/'seal.json'),'manifestFiles':len(files),'maximumBytes':max(r['bytes'] for r in files.values())}))
