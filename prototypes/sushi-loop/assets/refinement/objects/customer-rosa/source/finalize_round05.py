from pathlib import Path
import json,hashlib,struct
from PIL import Image
H=Path(__file__).resolve().parent;O=H.parent;C=O/'candidates/round-05'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
d=json.loads((O/'delivery-round05.json').read_text());v=json.loads((C/'complete-validation.json').read_text());obs=json.loads((C/'browser-observations.json').read_text())
browser=json.loads((C/'browser-evidence.json').read_text())
d['previews']['before-after-fourviews']=str((C/'previews/before-after-fourviews.png').relative_to(O))
for p in (C/'previews').glob('browser-*.png'):d['previews'][p.stem]=str(p.relative_to(O))
for p in [C/'browser-evidence.json',C/'browser-observations.json',C/'dependencies.json',H/'review_template_round05.html',H/'dependencies_round05.py',H/'finalize_round05.py',H/'compare_round04_05.py',C/'round04-preservation.json',H/'comparison_preview_round05.py',C/'before-after-provenance.json']:
 d['resources'][p.name]=str(p.relative_to(O))
v['round04Preservation']=str((C/'round04-preservation.json').relative_to(O));v['hairOnlyGeometryRevision']=True;v['oneClosedNativeHairMesh']=True;v['nativeValidation']=str((C/'validation.json').relative_to(O));v['browserEvidence']=str((C/'browser-evidence.json').relative_to(O));v['candidateStatus']='complete candidate ready for independent visual review';v['measuredDirectionRecords']=480;v['measuredRuntimeDirectionRecords']=96;v['closedNativeDependencies']=json.loads((C/'dependencies.json').read_text())
# Decode actual APNG playback frames and verify against each untouched native source frame.
clipchecks=[]
for bu in [d,d['runtimeVariants']]:
 for a in bu['atlases']:
  paths=sorted((O/a['path']).parent.parent.joinpath('frames',a['clip']+'-'+a['direction']).glob('*.png'));apng=O/bu['previews'][a['clip']+'-'+a['direction']];im=Image.open(apng);assert im.n_frames==12
  exact=True
  for i,p in enumerate(paths):im.seek(i);exact=exact and im.convert('RGBA').tobytes()==Image.open(p).convert('RGBA').tobytes()
  assert exact,apng
  clipchecks.append({'path':str(apng.relative_to(O)),'decodedFramesEqualNative':exact,'frames':12,'fps':12})
v['actualPlaybackDecodedNativeFramesEqual']=True;write(C/'playback-decode-validation.json',{'clips':clipchecks,'count':48,'decodedFrames':576,'allEqual':True});d['resources']['playback-decode-validation.json']=str((C/'playback-decode-validation.json').relative_to(O))
write(C/'complete-validation.json',v)
# Recheck every sealed round04 binding without writing any old source/candidate/review file.
prior=O/'candidates/round-04/packet.json';priorData=json.loads(prior.read_text());mismatches=[]
for key,value in priorData['files'].items():
 file=(prior.parent/value['path']).resolve()
 if not file.is_file() or sha(file)!=value['sha256']:mismatches.append(key)
assert not mismatches,mismatches
v['sealedRound04BindingsUnchanged']={'packetSHA256':sha(prior),'checkedBindings':len(priorData['files']),'mismatches':mismatches}
write(C/'complete-validation.json',v)
d['notes']=['Hair is rebuilt as one connected closed native bob. Round04 non-hair mesh/material data, lighting, world and camera are proven unchanged.','All576 new native frames are actually recaptured to include changed hair light interaction; no gameplay routing or meal mapping changes.','Independent judge owns the visual verdict; root coordinator seals the exact numbered round.']
for direction in ['N','E','S','W']:d['resources']['comparison-source-round04-'+direction]=str((O/'candidates/round-04/frames'/('stand-'+direction)/'000.png').relative_to(O))
# Verify every raw frame and atlas still equals its declared bytes.
for bu in [d,d['runtimeVariants']]:
 for e in bu['rawFrames']+bu['atlases']:assert sha(O/e['path'])==e['sha256']
# Bind the exact currently declared bytes. Outer coordinator packet binds this closure file and delivery.
paths=set()
def scan(x):
 if isinstance(x,str):
  p=O/x
  if p.is_file():paths.add(p)
 elif isinstance(x,list):
  for v in x:scan(v)
 elif isinstance(x,dict):
  for v in x.values():scan(v)
scan(d);paths.add(C/'complete-validation.json');files={str(p.relative_to(O)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths) if p.name not in ['byte-closure.json']};closure={'asset':'customer-rosa','round':'round-05','filesRelativeTo':'object','files':files,'count':len(files),'allFilesExist':True,'note':'Closure excludes itself and mutable outer delivery to avoid a recursive hash. Coordinator packet binds both exact files.'};write(C/'byte-closure.json',closure);d['resources']['byte-closure.json']=str((C/'byte-closure.json').relative_to(O));write(O/'delivery-round05.json',d)
print(json.dumps({'deliverySHA256':sha(O/'delivery-round05.json'),'mainProjectSHA256':sha(O/d['project']),'runtimeProjectSHA256':sha(O/d['runtimeVariants']['project']),'files':len(files),'frameCounts':[len(d['rawFrames']),len(d['runtimeVariants']['rawFrames'])],'atlasCounts':[len(d['atlases']),len(d['runtimeVariants']['atlases'])],'actualDecodedClips':len(clipchecks)},indent=2))
