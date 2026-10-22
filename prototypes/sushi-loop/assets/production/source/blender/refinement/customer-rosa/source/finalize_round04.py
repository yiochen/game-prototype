from pathlib import Path
import json,hashlib,struct
from PIL import Image
H=Path(__file__).resolve().parent;O=H.parent;C=O/'candidates/round-04'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
d=json.loads((O/'delivery-round04.json').read_text());v=json.loads((C/'complete-validation.json').read_text());obs=json.loads((C/'browser-observations.json').read_text())
browser={'url':'http://localhost:4178/prototypes/sushi-loop/assets/refinement/objects/customer-rosa/candidates/round-04/review.html','backend':'Chrome through cua_repl','phoneViewport':[390,844],'landscapeViewport':[844,390],'horizontalOverflowObserved':False,'animationSelections':obs,'observedTemporalCounter':['Frame 2 / 12','Frame 11 / 12'],'backgroundsObserved':['gray','light','dark'],'screenshots':[str(p.relative_to(O)) for p in sorted((C/'previews').glob('browser-*.png'))],'temporaryViewportReset':True,'note':'Viewport screenshots saved. Full-page screenshot call timed out in browser backend, so no full-page proof or console-log claim is made.'};write(C/'browser-evidence.json',browser)
for p in (C/'previews').glob('browser-*.png'):d['previews'][p.stem]=str(p.relative_to(O))
for p in [C/'browser-evidence.json',C/'browser-observations.json',C/'dependencies.json',H/'review_template_round04.html',H/'dependencies_round04.py',H/'finalize_round04.py']:
 d['resources'][p.name]=str(p.relative_to(O))
v['nativeValidation']=str((C/'validation.json').relative_to(O));v['browserEvidence']=str((C/'browser-evidence.json').relative_to(O));v['candidateStatus']='complete candidate ready for independent visual review';v['measuredDirectionRecords']=480;v['measuredRuntimeDirectionRecords']=96;v['closedNativeDependencies']=json.loads((C/'dependencies.json').read_text())
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
scan(d);paths.add(C/'complete-validation.json');files={str(p.relative_to(O)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths) if p.name not in ['byte-closure.json']};closure={'asset':'customer-rosa','round':'round-04','filesRelativeTo':'object','files':files,'count':len(files),'allFilesExist':True,'note':'Closure excludes itself and mutable outer delivery to avoid a recursive hash. Coordinator packet binds both exact files.'};write(C/'byte-closure.json',closure);d['resources']['byte-closure.json']=str((C/'byte-closure.json').relative_to(O));write(O/'delivery-round04.json',d)
print(json.dumps({'deliverySHA256':sha(O/'delivery-round04.json'),'mainProjectSHA256':sha(O/d['project']),'runtimeProjectSHA256':sha(O/d['runtimeVariants']['project']),'files':len(files),'frameCounts':[len(d['rawFrames']),len(d['runtimeVariants']['rawFrames'])],'atlasCounts':[len(d['atlases']),len(d['runtimeVariants']['atlases'])],'actualDecodedClips':len(clipchecks)},indent=2))
