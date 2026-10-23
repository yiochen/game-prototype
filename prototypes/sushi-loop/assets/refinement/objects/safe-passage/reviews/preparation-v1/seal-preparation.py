from pathlib import Path
import json,hashlib,sys,subprocess
from datetime import datetime,timezone
from PIL import Image
import PIL
H=Path(__file__).resolve().parent;O=H.parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
resources=H/'resources'
expected={'original-library.blend':'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6','original.png':'8f4c1b1981c610fb7e5c7ddb0f30223c44e192617e79587bc33a47d61e78fb5d','target.png':'b1ab9e429321a9a8e34bbffcdfa6c0d0ab71ad46db8e037a55b0283e854b96c7','warm-soft-reference.png':'02e6a13e71b6aba78b85b99f70ac37117b2b6939461ed1bdb2cc3ec334ab4d15','world-sprite-raster.js':'570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545','sprite-layout.js':'099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65','judge-initial-dispatch.txt':'7d82374def04ad7dc853f4012bb1cb81c50c892c71da0a4679feb25a333bca96'}
for name,digest in expected.items():assert sha(resources/name)==digest,(name,sha(resources/name))
for n in ['initial.json','criteria.json']:assert (O/'reviews'/n).read_bytes()==(H/n).read_bytes()
cap=json.loads((H/'capture-records.json').read_text());assert len(cap['captureRecords'])==48
for r in cap['captureRecords']:
 p=H/r['path'];assert sha(p)==r['sha256'];assert Image.open(p).size==(768,1408)
assert not list(H.rglob('__pycache__'))
for p in H.rglob('*'):
 if p.is_file():assert p.stat().st_size<100000000,p
runtime={'python':{'executable':sys.executable,'version':sys.version},'Pillow':{'version':PIL.__version__,'modulePath':str(Path(PIL.__file__)),'moduleSHA256':sha(Path(PIL.__file__)),'ImageModuleSHA256':sha(Path(Image.__file__))},'node':subprocess.run(['node','--version'],capture_output=True,text=True).stdout.strip(),'ffmpeg':subprocess.run(['ffmpeg','-version'],capture_output=True,text=True).stdout.splitlines()[0],'toolchainPolicy':'System/runtime executable trees are external toolchain dependencies, not copied app trees. Frozen exact used native drivers/source, original blend, images, browser helpers/fixture and generated optimized React dependency are included.'}
(H/'runtime.json').write_text(json.dumps(runtime,indent=2)+'\n')
files=[]
for p in sorted(H.rglob('*')):
 if p.is_file() and p.name not in ['hash-manifest.json','seal.json']:files.append({'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size})
for p in [O/'reviews/initial.json',O/'reviews/criteria.json']:files.append({'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size})
manifest={'asset':'safe-passage','stage':'preparation-v1','pathBase':'object root / prototypes/sushi-loop/assets/refinement/objects/safe-passage','files':files,'fileCount':len(files),'totalBytes':sum(f['bytes'] for f in files),'sourceHashChecks':expected,'excludedFromManifest':['reviews/preparation-v1/hash-manifest.json','reviews/preparation-v1/seal.json'],'status':'complete independent preparation; pending ROOT reconciliation/freeze; not candidate approval'}
mp=H/'hash-manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n')
seal={'asset':'safe-passage','stage':'preparation-v1','status':'sealed-preparation-only-awaiting-ROOT-reconciliation','sealedAtUTC':datetime.now(timezone.utc).isoformat(),'manifest':{'path':str(mp.relative_to(O)),'sha256':sha(mp)},'entryPoints':{'initial':'reviews/initial.json','independentCriteria':'reviews/criteria.json','proposedContract':'reviews/preparation-v1/root-native-contract.json','scopedEvidencePlan':'reviews/preparation-v1/scoped-evidence-plan.json','observations':'reviews/preparation-v1/preparation-observations.json','nativeRecords':'reviews/preparation-v1/capture-records.json','compatibleOriginalValidation':'reviews/preparation-v1/native-validation-original.json','sourceReconciliation':'reviews/preparation-v1/source-provenance-reconciliation.json','browserRecords':'reviews/preparation-v1/browser/manifest.json'},'allRequiredOriginalFrames':48,'candidateCreated':False,'editorConstruction':False,'approval':'none; no candidate/family/production/Godot approval','noOtherAgentsOrGitOrProductionOrLiveBlenderOrDevice':True,'excluded2DEffects':13}
(H/'seal.json').write_text(json.dumps(seal,indent=2)+'\n')
# Independently verify every manifest record after final construction; no further writes.
for f in files:assert sha(O/f['path'])==f['sha256'],f['path']
print(json.dumps({'manifestSHA256':sha(mp),'sealSHA256':sha(H/'seal.json'),'fileCount':len(files),'totalBytes':manifest['totalBytes'],'maxFileBytes':max(f['bytes'] for f in files)},indent=2))
