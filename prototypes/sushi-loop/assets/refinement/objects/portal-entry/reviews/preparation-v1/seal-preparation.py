from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;O=H.parent.parent;ROOT=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
expected={
 'source':(ROOT/'prototypes/sushi-loop/assets/production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend','b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'),
 'backup':(ROOT/'prototypes/sushi-loop/assets/refinement/backups/b1765262bfa897ad-sushi-loop-world-library.blend','b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'),
 'dispatch':(ROOT/'prototypes/sushi-loop/assets/refinement/preparation/portal-entry/judge-initial-dispatch.txt','13d8b03cfdb1084696bf539accfa2487605c6785e234e5491a26aca03b664ad7'),
 'original':(O/'inputs/original.png','2f3f2fa433c4a379aff73c88d763403ec1d503a67d337f8302de5522a5be0cd1'),
 'target':(O/'inputs/target.png','933d46b522f51e799f5c99fc61d1b831fe4b4d6bb45b27bdabbf867c0a69f23c'),
 'GLOBALstyle':(ROOT/'prototypes/sushi-loop/assets/refinement/style/warm-soft-reference.png','02e6a13e71b6aba78b85b99f70ac37117b2b6939461ed1bdb2cc3ec334ab4d15'),
 'world-sprite-raster':(ROOT/'prototypes/sushi-loop/wireframe/world-sprite-raster.js','570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545'),
 'sprite-layout':(ROOT/'prototypes/sushi-loop/wireframe/sprite-layout.js','099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65')}
for name,(path,value) in expected.items():assert sha(path)==value,(name,path)
assert sha(H/'resources/native/source.blend')==expected['source'][1]
for name in ['world-sprite-raster','sprite-layout']:assert sha(H/f'resources/consumer/{name}.js')==expected[name][1]
records=json.loads((H/'native-measurements.json').read_text())['views'];assert len(records)==48
assert {(r['direction'],r['index']) for r in records}=={(d,i) for d in ['N','E','S','W'] for i in range(12)}
for r in records:
 assert sha(H/r['path'])==r['sha256']
 expectedrot={'N':180,'E':90,'S':0,'W':-90}[r['direction']]
 assert abs(r['rootRotationZ']*180/3.141592653589793-expectedrot)<1e-4
consumer=json.loads((H/'consumer-report.json').read_text());assert len(consumer['browserModes'])==2
for b in consumer['browserModes']:
 assert b['playbackFinal']['complete']
 for d in ['N','E','S','W']:assert [r['frame'] for r in b['playbackFinal']['frameRecords'] if r['direction']==d]==list(range(12))
 assert all(x['frame']==11 for x in b['playbackFinal']['currentFrames'])
paths=[p for p in H.rglob('*') if p.is_file() and p.name not in ('hashmanifest.json','seal.json')]+[O/'reviews/initial.json',O/'reviews/criteria.json']
assert not any(p.suffix=='.pyc' or '__pycache__' in p.parts for p in paths)
assert all(p.stat().st_size<100_000_000 for p in paths)
files=[{'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths)]
manifest={'version':1,'asset':'portal-entry','stage':'preparation-v1-independent-judge','pathBase':'object-root:prototypes/sushi-loop/assets/refinement/objects/portal-entry','files':files,'externalIdentityBindings':{name:{'path':str(p),'sha256':v} for name,(p,v) in expected.items()},'sourceClosure':'Exact8MB original native project; only actually used camera/native-action/style/light modules; read-only native-builder/library/worker references; own drivers, actual inputs, React bundle sources, commands/logs/captures. No application/runtime tree copied.'}
(H/'hashmanifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
seal={'version':1,'asset':'portal-entry','stage':'preparation-only','status':'SEALED_PREPARATION_PENDING_ROOT_RECONCILIATION','manifest':{'path':'reviews/preparation-v1/hashmanifest.json','sha256':sha(H/'hashmanifest.json')},'initial':{'path':'reviews/initial.json','sha256':sha(O/'reviews/initial.json')},'criteria':{'path':'reviews/criteria.json','sha256':sha(O/'reviews/criteria.json')},'proposedRootNativeContract':{'path':'reviews/preparation-v1/root-native-contract.proposed.json','sha256':sha(H/'root-native-contract.proposed.json')},'evidencePlan':{'path':'reviews/preparation-v1/evidence-plan.json','sha256':sha(H/'evidence-plan.json')},'noCandidateOrApproval':True,'stop':'ROOT reconciliation/freeze required before fresh editor construction; no model/candidate/production/deployment changes.'}
(H/'seal.json').write_text(json.dumps(seal,indent=2)+'\n')
for f in files:assert sha(O/f['path'])==f['sha256']
assert sha(H/'hashmanifest.json')==seal['manifest']['sha256']
print(json.dumps({'sealPath':str(H/'seal.json'),'sealSHA256':sha(H/'seal.json'),'manifestSHA256':seal['manifest']['sha256'],'files':len(files),'bytes':sum(f['bytes'] for f in files),'verified':True,'approval':False},indent=2))
