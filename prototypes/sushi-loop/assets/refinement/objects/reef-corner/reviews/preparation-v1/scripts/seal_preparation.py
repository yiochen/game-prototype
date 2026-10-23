from pathlib import Path
import json,hashlib,sys,platform,datetime,PIL
from PIL import Image
p=Path(__file__).resolve().parents[1]
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def read(s):return json.loads((p/s).read_text())
def write(s,v):(p/s).write_text(json.dumps(v,indent=2)+'\n')
expected={'resources/source/original.blend':'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6','resources/canonical/round-02.blend':'51d515119c1a229f57f3b242fdf040b28ef00121692cb3d40d8821dab70ff3c5','resources/canonical/packet.json':'d60ff36edc6006a0d4082692e7c115be23e1fc1e9d674f8bdc5c2f8ccc447ca8','resources/canonical/review.json':'f60dabe7a9e2ff5f0460f0e63a16fcd98a849415b21277cab7eb87ac1ec1a71e','resources/consumer/world-sprite-raster.js':'570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545','resources/consumer/sprite-layout.js':'099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65'}
checks={s:sha(p/s)==h for s,h in expected.items()};assert all(checks.values()),checks
m=read('evidence/native-measurements.json');c=read('evidence/canonical-native-audit.json');out=read('evidence/finite-support-outline.json');compare=read('evidence/original-replay-comparison.json')
assert max(m['WMaximumPositionError'],m['NMaximumPositionError'])<1e-5
assert len(out['boundaryLoops'])==1 and not out['holes']
assert [len(c['bands'][s]['triangles']) for s in ['W','E']]==[16,16]
assert compare['maxChannels'][3]==0
for facing in ['N','E','S','W']:
 assert Image.open(p/'evidence/original-replay'/f'native4x-{facing}.png').size==(768,1408)
 assert Image.open(p/'evidence/original-replay'/f'published2x-{facing}.png').size==(384,704)
for f in p.rglob('*.json'):json.loads(f.read_text())
py=Path(sys.executable);bl=Path('/opt/homebrew/bin/blender')
write('toolchain.json',{'actualExecuted':{'Blender':{'path':str(bl),'resolvedPath':str(bl.resolve()),'sha256':sha(bl),'version':'5.2.2 LTS','buildHash':'d13f752e3b9c','evidenceLogs':['native-audit-v4.log','original-replay.log','canonical-audit.log']},'Python':{'path':str(py),'resolvedPath':str(py.resolve()),'sha256':sha(py),'version':sys.version},'Pillow':{'version':PIL.__version__,'module':PIL.__file__},'platform':platform.platform(),'bytecode':'All actual driver executions set PYTHONDONTWRITEBYTECODE=1; Blender scripts do not import project helper modules. No __pycache__ generated in closure.'},'actualModules':'Native scripts: bpy, mathutils, bpy_extras.object_utils, Python stdlib. Python scripts: Pillow and stdlib. Source .blend closure carries packed native resources; no linked libraries or required external textures used by inspected object.','notExecuted':['Node/Playwright/browser','live Blender','CUA/native device','candidate model build','Git/build/deploy'],'futureBrowser':'assembly-evidence-plan.json and saved HEADLESS-BROWSER-CONFIGS.txt specify required two headless modes; actual versions/DPR/viewport must be recorded at execution.'})
write('checks.json',{'status':'preparation integrity checks passed; no candidate art/seam approval','expectedInputHashes':checks,'nativeProfilePositionTolerance':1e-5,'maximumProfilePositionError':max(m['WMaximumPositionError'],m['NMaximumPositionError']),'finiteSupport':{'triangleCount':8,'outerVertices':8,'holes':0,'area':out['unionArea'],'accidentalInternalFoldsNotFrozen':True},'canonicalBands':{'trianglesPerBand':16,'actualEvaluatedBarycentricFieldSamples':len(c['renderedFieldSamples']),'unchangedBandGeometryFits':True},'historicalReplay':{'all4Frames':True,'nativeSize':[768,1408],'publicationSize':[384,704],'alphaExactToSnapshotS':True,'differentRGBPixelsS':41,'maximumChannelDifferenceS':1},'candidateBuilt':False,'browserRun':False,'approval':False,'rootFreezePending':True})
# Separate manifest and seal avoid recursive self hashes. Every saved actual-used file is hash-bound.
files=[]
for f in sorted(p.rglob('*')):
 if not f.is_file() or f.name in ['manifest.json','seal.json','seal-preparation.log']:continue
 assert f.stat().st_size<100_000_000,f
 files.append({'path':str(f.relative_to(p)),'bytes':f.stat().st_size,'sha256':sha(f)})
write('manifest.json',{'schemaVersion':1,'asset':'reef-corner','scope':'fresh independent preparation-v1 only; root reconciliation/freeze pending; no derivative approval','files':files,'totalFiles':len(files),'totalBytes':sum(f['bytes'] for f in files),'exclusions':['manifest.json (hash in seal.json)','seal.json (nonrecursive final seal)','seal-preparation.log (contains seal hash printed after manifest)'],'dependencyClosure':'Minimal actual-used saved native originals/canonical source, fixedtargets/instructions/consumer reference, exact local drivers and raw logs/captures/measurements/proposals. Installed Blender/Python/Pillow recorded by toolchain rather than copied as binaries.'})
write('seal.json',{'schemaVersion':1,'asset':'reef-corner','stage':'PREPARATION SEALED / root reconciliation/freeze pending','manifestSHA256':sha(p/'manifest.json'),'fileCount':len(files),'totalBytes':sum(f['bytes'] for f in files),'criteriaSHA256':sha(p/'criteria.json'),'rootContractProposalSHA256':sha(p/'root-contract-proposal.json'),'assemblyEvidencePlanSHA256':sha(p/'assembly-evidence-plan.json'),'verdict':'not-applicable: preparation only; no candidate/family/production approval','next':'STOP. Root reconciles and freezes before a fresh independent editor.'})
for r in files:assert sha(p/r['path'])==r['sha256']
print(json.dumps({'manifestSHA256':sha(p/'manifest.json'),'sealSHA256':sha(p/'seal.json'),'files':len(files),'bytes':sum(f['bytes'] for f in files),'checks':'passed','next':'STOP for root reconciliation/freeze'},indent=2))
