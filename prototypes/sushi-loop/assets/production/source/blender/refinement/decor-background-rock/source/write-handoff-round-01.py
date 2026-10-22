"""Write an editor delivery/resource handoff; this does not seal a candidate packet."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,stat
OBJ=Path(__file__).resolve().parent.parent;SRC=OBJ/'source';OUT=OBJ/'candidates/round-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rec(p):return {'path':str(p.relative_to(OBJ)),'sha256':sha(p),'bytes':p.stat().st_size}
def dumpnew(p,d):
 with p.open('x') as f:json.dump(d,f,indent=2);f.write('\n')
expected={'brief.json':'2b845e5ac3055e3bb0b34dbd0e6fd1f5cb684da3da18c741137c20a8bc7d4607','inputs/root-native-contract.json':'bb437b98db3deb06402e91206f1e53e3664165b8f4c60a72e3ca2f8081b37e0d','inputs/root-preparation-reconciliation-v1.json':'dc9fdf3b1de551b4fa41d9fa3c7c458c3c34094e2ee5ebc82fac87986db0c64b','reviews/proposedcriteria.json':'5e49007e5949f7434f5cac16c2ef3845e34f47e52cd68f180ecd9ba60bf3ebf0','source/initial-observations.json':'17100552b92ac7d42d192143e348d0aacfb73b12ed9c9f8ba97f1a7172426056','inputs/target.png':'b0f3a6a09d5fcac235009e800b28c9c71d4bcffeab8e9ab35e4b6036e970cad6'}
for p,digest in expected.items():assert sha(OBJ/p)==digest,p
native=json.loads((OUT/'native-validation.json').read_text());v=json.loads((OUT/'validation.json').read_text());assert v['allChecksPassed'];assert sha(SRC/'round-01.blend')==native['sourceSHA256']
consumer=json.loads((OUT/'consumer/results.json').read_text());assert len(consumer['modes'])==2
for mode in consumer['modes']:
 assert mode['browserVersion']=='153.0.8010.12' and len(mode['cases'])==6
 for case in mode['cases']:assert case['dpr']==1 and not case['errors']
manifestpath=SRC/'round-01-resource-manifest-v1.json';deliverypath=SRC/'round-01-delivery-v1.json';handoffpath=SRC/'round-01-handoff-v1.json'
files=[]
for parent in [SRC,OUT]:
 for p in parent.rglob('*'):
  if not p.is_file():continue
  assert '__pycache__' not in p.parts,p
  assert p.stat().st_size<100_000_000,p
  if p in [manifestpath,deliverypath,handoffpath] or p.name.endswith('.sha256'):continue
  files.append(p)
# Required untouched records are explicitly bound alongside the private used closure.
for rel in ['brief.json','reviews/proposedcriteria.json','reviews/source-contract-proposal.json','reviews/preparation-v1/manifest.json','reviews/preparation-v1/resources/native/source.blend','reviews/preparation-v1/capture_consumer.mjs','reviews/preparation-v1/audit_capture_source.py','inputs/original.png','inputs/target.png','inputs/source-camera.json','inputs/source-assetRecord.json','inputs/source-rig.json','inputs/root-native-contract.json','inputs/root-preparation-reconciliation-v1.json']:
 files.append(OBJ/rel)
files=sorted(set(files));manifest={'asset':'decor-background-rock','round':'round-01','version':'editor-resource-handoff-v1','pathBase':'object root','files':[rec(p) for p in files],'scope':'Exact actual used private source/consumer dependency closure, all declared native/published/atlas/study/browser/validation outputs, original frozen records, and retained failed attempts. System Blender/Python/Node/Playwright executables are versioned in reproducibility and browser provenance, not copied. No packet/visual approval.'}
dumpnew(manifestpath,manifest)
previews={'four-view-full-native':'candidates/round-01/four-view-native.png','four-view-full-published':'candidates/round-01/four-view-published.png','logical-and64px-cell-neutrals':'candidates/round-01/logical-and-small-neutral-backgrounds.png','repeated3x3-all4-full-native':'candidates/round-01/repeated3x3-all4-full-native.png'}
for mode in consumer['modes']:
 for case in mode['cases']:previews[mode['mode']+'-'+case['config']['name']]=case['screenshot']
delivery={'asset':'decor-background-rock','round':'round-01','version':'editor-delivery-v1','pathBase':'object root','project':'source/round-01.blend','recipeScript':'source/reproduce-round-01.py','validation':'candidates/round-01/validation.json','nativeRecords':{'camera':'candidates/round-01/published-camera.json','assetRecord':'candidates/round-01/assetRecord.json','rig':'candidates/round-01/rig.json'},'heroes':{d:'candidates/round-01/frames/static/'+d+'/000.png' for d in 'NESW'},'previews':previews,'rawFrames':[{'clip':'static','direction':d,'index':0,'path':'candidates/round-01/frames/static/'+d+'/000.png'} for d in 'NESW'],'nativeRawFrames':[{'clip':'static','direction':d,'index':0,'path':'candidates/round-01/native/static/'+d+'/000.png'} for d in 'NESW'],'atlases':[{'clip':'static','direction':d,'path':'candidates/round-01/atlases/static-'+d+'.png','columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]]} for d in 'NESW'],'resources':manifest['files']+[rec(manifestpath)],'resourceManifest':rec(manifestpath),'notes':['Reconstructed five closed irregular cobalt stone masses with real rounded bevels/weighted normals and four shallow native dimples; original four parts and shader replaced within frozen standalone envelope.','Native4x all4 are uniformly reduced over complete canvas by LANCZOS to published2x; exact original1x1 atlases.','Actual camera/root/facing/envelope/static/manifold/ownership/support measured. Tiny camera float residuals and source-replay RGB rounding retained; no decoded source-replay identity claimed.','Six exact helper browser cases in each153 mode; nativecanvas decoded-identical across modes, CSS differences retained. Additional all4 repeated native density sheet has no modular seam assertion.','No image target card, paint-over, pixel repair, per-view adjustments, ground plane, temporal channel, production write or self approval. Original judge to evaluate visible outcomes.'],'status':'immutable editor handoff for ROOT candidate packet sealing and original independent judge; no approval'}
dumpnew(deliverypath,delivery)
handoff={'asset':'decor-background-rock','round':'round-01','version':'handoff-v1','pathBase':'object root','createdUTC':datetime.now(timezone.utc).isoformat(),'status':'STOP: editor handoff complete; ROOT seals and invokes original judge','source':rec(SRC/'round-01.blend'),'delivery':rec(deliverypath),'resourceManifest':rec(manifestpath),'constructionAcknowledgment':rec(SRC/'construction-acknowledgment.json'),'nativeValidation':rec(OUT/'native-validation.json'),'validation':rec(OUT/'validation.json'),'nativeFrames':[rec(OBJ/r['path']) for r in delivery['nativeRawFrames']],'publishedFrames':[rec(OBJ/r['path']) for r in delivery['rawFrames']],'atlases':[rec(OBJ/r['path']) for r in delivery['atlases']],'previews':{name:rec(OBJ/path) for name,path in previews.items()},'resourceCount':len(manifest['files']),'sourceReplayNote':v['sourceReplayDisclosure'],'approvalClaimed':False,'candidatePacketSealedByEditor':False,'sourceAndResourceOwnership':'Only own source/ and candidates/ written. Frozen originals/inputs/brief/reviews/preparation unchanged.'}
dumpnew(handoffpath,handoff)
sidecar=handoffpath.with_suffix('.json.sha256')
with sidecar.open('x') as f:f.write(sha(handoffpath)+'  '+handoffpath.name+'\n')
# Immutable handoff files, not a candidate packet seal. ROOT may add packet files later.
for parent in [SRC,OUT]:
 for p in parent.rglob('*'):
  if p.is_file():p.chmod(stat.S_IRUSR|stat.S_IRGRP|stat.S_IROTH)
print(json.dumps({'source':handoff['source'],'delivery':handoff['delivery'],'resourceManifest':handoff['resourceManifest'],'handoff':rec(handoffpath),'resourceCount':handoff['resourceCount'],'previewCount':len(previews)},indent=2))
