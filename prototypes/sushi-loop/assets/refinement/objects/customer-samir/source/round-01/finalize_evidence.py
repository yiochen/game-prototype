from pathlib import Path
import json,hashlib,math,shutil
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;P=D.parent.parent;R=P/'candidates/round-01';RES=D/'resources'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(P))
def load(p):return json.loads(p.read_text())
def write(p,a):p.write_text(json.dumps(a,indent=2)+'\n')
# Preserve the exact code bytes used for the final main build before the runtime-only material-name suffix fix.
shutil.copyfile(D/'draft-05-runtime-materials/refine.py',D/'build-main-recipe.py')
valid=load(R/'validation.json');delivery=load(R/'delivery.json');nativeReopen={};surface={};visibility={};deformation={};unique={}
for mode in ['main','runtime']:
 project=D/f'samir-{mode}.blend';h=sha(project);reopened=load(R/mode/'validation-native-reopened.json');original=load(R/mode/'validation-native.json');deps=load(R/f'dependencies-{mode}.json');support=load(R/f'support-{mode}-candidate.json');vis=load(R/f'visibility-{mode}-candidate.json')
 assert reopened['projectSHA256']==deps['projectSHA256']==support['projectSHA256']==vis['projectSHA256']==h
 assert reopened['clips']==original['clips'] and reopened['rig']==original['rig'] and reopened['camera']==original['camera'] and not reopened['errors']
 nativeReopen[mode]={'project':rel(project),'projectSHA256':h,'audit':rel(R/mode/'validation-native-reopened.json'),'allNativeMeasurementsMatchCapturedSequence':True}
 src=load(R/f'support-{mode}-source.json')['samples'];cur=support['samples'];assert len(src)==len(cur)==(480 if mode=='main' else 96);mx={}
 for a,b in zip(src,cur):
  for k in a['supports']:
   e=math.dist(a['supports'][k]['nearestRemodeledSurfaceWorld'],b['supports'][k]['nearestRemodeledSurfaceWorld']);mx[k]=max(mx.get(k,0),e)
 assert max(mx.values())<=.005
 surface[mode]={'samples':len(src),'surfaceProbesPerSample':len(mx),'maxDeviationBySurfaceWorld':mx,'toleranceWorld':.005,'source':rel(R/f'support-{mode}-source.json'),'candidate':rel(R/f'support-{mode}-candidate.json'),'candidateProjectSHA256':h}
 originalVis=load(R/f'visibility-{mode}-source.json');assert originalVis['samples']==vis['samples']
 visibility[mode]={'samples':len(vis['samples']),'nativeVisibilityOwners':vis['ownerCount'],'exactVisibilityTrajectoryMatch':True,'source':rel(R/f'visibility-{mode}-source.json'),'candidate':rel(R/f'visibility-{mode}-candidate.json')}
 weights=vis['actualNativeDeformationWeights'];assert all(w['unweightedVertices']==0 for w in weights.values())
 # The functional hand/thumb/sole mesh vertices and weights are preserved exactly; smoothing uses native bevels.
 functional=[k for k in weights if k.startswith(('palm_','thumb_','minimal_foot_'))]
 assert all(weights[k]['weightDigest']==originalVis['actualNativeDeformationWeights'][k]['weightDigest'] for k in functional)
 deformation[mode]={'functionalMeshGroups':{k:weights[k] for k in functional},'noHeadGroupOnFunctionalHandsThumbsOrSoles':True,'functionalOriginalVertexWeightDigestsPreserved':True,'allBodyVerticesWeighted':True,'completeWeightSummary':rel(R/f'visibility-{mode}-candidate.json')}
 for clip in reopened['clips']:
  for direction in ['S','E','N','W']:
   paths=[R/mode/'frames'/clip/direction/f'{i:02}.png' for i in range(12)];n=len({hashlib.sha256(Image.open(p).convert('RGBA').tobytes()).hexdigest() for p in paths});assert n>=6,(clip,direction,n);unique[f'{clip}-{direction}']=n
valid['reopenedSourceBinding']=nativeReopen;valid['functionalSurfaceAttachments']=surface;valid['allAuthoredVisibilityPaths']=visibility;valid['actualFunctionalNativeDeformation']=deformation;valid['uniqueNativeFramesByClipFacing']=unique;valid['editorBrowserPlaybackEvidence']='candidates/round-01/browser/observations.json';valid['approvalScope']='Technical evidence and editor playback inspection only; independent judge decides aesthetic approval.'
write(R/'validation.json',valid)
# Same actor body also evaluates identically under corresponding main/runtime actions.
a=load(R/'main/validation-native-reopened.json');b=load(R/'runtime/validation-native-reopened.json');pair={}
for main,runtime in [('eat','eat-salmon'),('seated-wait','seated-wait-empty')]:
 mx=0
 for s,t in zip(a['clips'][main]['samples'],b['clips'][runtime]['samples']):
  assert (s['direction'],s['frame'])==(t['direction'],t['frame'])
  mx=max(mx,*[abs(x-y) for x,y in zip(s['bodyBounds'][0]+s['bodyBounds'][1],t['bodyBounds'][0]+t['bodyBounds'][1])])
 assert mx<1e-5;pair[runtime]={'mainBodyPose':main,'samples':48,'maximumBodyBoundDifferenceWorld':mx}
write(R/'main-runtime-body-parity.json',pair)
# Full phone-size registered sprite context. This is an inspection canvas, not a replacement game UI.
phone=Image.new('RGBA',(390,844),'#f2e7d1');dr=ImageDraw.Draw(phone)
for yy in range(300,844,73):dr.line((0,yy,390,yy),fill='#dbceaf')
for xx in range(3,390,128):dr.line((xx,300,xx,844),fill='#dbceaf')
im=Image.open(R/'contexts/frames/eat/S/04.png').convert('RGBA');phone.alpha_composite(im.resize((192,352),Image.Resampling.LANCZOS),(99,282));dr.text((24,48),'Samir | registered phone context',fill='#1d3342');dr.text((24,72),'logical192x320 / 12fps / unchanged native root',fill='#1d3342');dr.line((190,530,200,530),fill='#a6432b',width=2);dr.line((195,525,195,535),fill='#a6432b',width=2);dr.text((24,782),'Separate stool + new actor; food is packed2D',fill='#1d3342');phone.save(R/'contexts/phone-size.png')
delivery['previews']['phone-size']='candidates/round-01/contexts/phone-size.png'
for p in (R/'browser').glob('*.png'):delivery['previews']['browser-'+p.stem]=rel(p)
delivery['recipe']=rel(D/'build-main-recipe.py');delivery['runtimeVariants']['recipe']=rel(D/'refine.py')
delivery['nativeRecordHashes']={mode:{k:sha(P/v) for k,v in (delivery['nativeRecords'] if mode=='main' else delivery['runtimeVariants']['nativeRecords']).items()} for mode in ['main','runtime']}
delivery['sourceHashes']={mode:sha(D/f'samir-{mode}.blend') for mode in ['main','runtime']}
delivery['modelingNotes']=['Native solid curved bill and stronger crown rounding; source intersecting fringe tops remodeled below bill underside.','Continuous side/rear hair shell replaces overlapping primitive crown/back masses. Front scallops remain distinct and coherent.','Rounded eye/cheek/moustache masses and bevel refinement; visible native collar leaves; distinct navy trousers and blue-black shoes.','Symmetric broad warm light and new native body shaders. Main/runtime actual mesh/material/group/weight signatures agree.','Drafts retain their original cap/hair intersection and old runtime shader issue as development history; current source/frames are the exact final candidate.']
# Exact input source paths, including context and raw packed original food payloads.
prov=load(D/'input-provenance.json')
for mode in ['main','runtime']:
 q=RES/f'source-{mode}-food.png';prov[q.name]={'sourcePath':str(P/'reviews'/('baseline-'+mode)/'original-packed-food.png'),'nativeSourcePackedSHA256':load(RES/f'source-{mode}-audit.json')['food']['packedSHA256'],'sha256':sha(q)}
for direction in ['S','E','N','W']:
 q=RES/f'context-stool-{direction}.png';prov[q.name]={'sourcePath':str(P.parent/'stool-wood/candidates/round-06/atlases'/f'static-{direction}.png'),'sha256':sha(q),'role':'Approved separate context sprite; shared native root192,496; actual raster384x704, uniform scale2.'}
q=RES/'context-stool-camera.json';prov[q.name]={'sourcePath':str(P.parent/'stool-wood/candidates/round-06/records/camera.json'),'sha256':sha(q),'note':'Historical record captureScale4 field is stale; actual approved384x704 raster is scale2. Context uses actual common logical anchor96,248 and no per-pose fitting.'}
write(D/'input-provenance.json',prov)
# Explicit packet closure includes actual retained draft .blend/frame bytes, not only their hashes.
excludeNames={'delivery.json','file-hashes.json','resources-manifest.json'}
files=[]
for base in [P/'source',P/'candidates/round-01']:
 for q in base.rglob('*'):
  if q.is_file() and '__pycache__' not in q.parts and q.suffix not in ['.pyc','.blend1'] and q.name not in excludeNames:files.append(q)
resources={rel(q):rel(q) for q in sorted(set(files))}
resources['candidates/round-01/resources-manifest.json']='candidates/round-01/resources-manifest.json';resources['candidates/round-01/file-hashes.json']='candidates/round-01/file-hashes.json'
manifest={rel(q):{'sha256':sha(q),'bytes':q.stat().st_size} for q in sorted(set(files))}
write(R/'resources-manifest.json',{'scope':'All explicitly declared current+retained-draft source/render/evidence bytes. Main/runtime final .blend and all576 current frames are separately identified by delivery. Excludes pycache/transient backups.','files':manifest})
delivery['resources']=resources;delivery['retainedDraftResourceCount']=sum('/draft-' in k for k in resources);delivery['resourceManifest']='candidates/round-01/resources-manifest.json';write(R/'delivery.json',delivery)
hashes={rel(q):sha(q) for q in [D/'samir-main.blend',D/'samir-runtime.blend',D/'build-main-recipe.py',D/'refine.py',R/'validation.json',R/'delivery.json',R/'resources-manifest.json']};write(R/'file-hashes.json',hashes)
assert all((P/v).is_file() for v in delivery['resources'].values())
print(json.dumps({'delivery':rel(R/'delivery.json'),'hashes':hashes,'resourceFiles':len(resources),'retainedDraftResourceFiles':delivery['retainedDraftResourceCount'],'nativeFrames':len(delivery['rawFrames'])+len(delivery['runtimeVariants']['rawFrames']),'atlases':len(delivery['atlases'])+len(delivery['runtimeVariants']['atlases']),'surfaceMaximumWorld':max(v for x in surface.values() for v in x['maxDeviationBySurfaceWorld'].values())},indent=2))
