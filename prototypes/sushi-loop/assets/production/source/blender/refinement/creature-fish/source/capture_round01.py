import bpy,sys,json,hashlib,time,math
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import fish_round01 as rt
OUT=P.parent/'candidates/round-01';OUT.mkdir(parents=True,exist_ok=True)
R=json.loads((P/'round-01-resources/inputs/rig-original.json').read_text())
SOURCE=Path(bpy.data.filepath);SOURCE_SHA=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
def write(n,d):
 p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def maxmat(a,b):return max(abs(x-y) for ra,rb in zip(a,b) for x,y in zip(ra,rb))
def residual(a,b):return max((x-y).length for x,y in zip(a,b))
records=[];motion=[];controls=[];allmin=[1e9]*3;allmax=[-1e9]*3
for clip,recipe in R['clips'].items():
 for d in rt.FACING:
  first=None;firstverts=None;maxbone=0;maxvertex=0
  for i in range(12):
   row,verts=rt.measure(clip,i+1,d,True)
   if i==0:first=row;firstverts=verts
   b=max(maxmat(first['boneMatrices'][n],m) for n,m in row['boneMatrices'].items());v=residual(firstverts,verts)
   row['maxBoneMatrixEntryDifferenceFromFrame1']=b;row['maxArmatureRelativeVertexDisplacementFromFrame1']=v
   maxbone=max(maxbone,b);maxvertex=max(maxvertex,v)
   box=row['evaluatedModifierBounds'];pr=row['cameraBoundsNormalized']
   assert all(box['min'][j]>=(-1.02 if j<2 else .02)-1e-5 and box['max'][j]<=(1.02 if j<2 else 1.18)+1e-5 for j in range(3)),(clip,d,i,box)
   assert all(0<pr['min'][j]<pr['max'][j]<1 for j in range(2)),(clip,d,i,'camera clipping',pr)
   assert all(abs(row['rootMatrix'][j][3])<1e-8 for j in range(3))
   for j in range(3):allmin[j]=min(allmin[j],box['min'][j]);allmax[j]=max(allmax[j],box['max'][j])
   records.append(row)
  motion.append({'clip':clip,'direction':d,'maxEvaluatedBoneMatrixDifference':maxbone,'maxArmatureRelativeVertexDisplacement':maxvertex,'genuineResponse':maxbone>1e-5 and maxvertex>1e-5})
  assert maxbone>1e-5 and maxvertex>1e-5,(clip,d,'no genuine response')
  if recipe['loop']:
   end,ev=rt.measure(clip,13,d,True);ref=first;refverts=firstverts
   c={'clip':clip,'direction':d,'kind':'loop','frames':[1,13],'boneResidual':max(maxmat(ref['boneMatrices'][n],m) for n,m in end['boneMatrices'].items()),'armatureResidual':maxmat(ref['armatureMatrix'],end['armatureMatrix']),'relativeVertexResidual':residual(refverts,ev)}
   assert max(c['boneResidual'],c['armatureResidual'],c['relativeVertexResidual'])<1e-5,c
  else:
   ref,refverts=rt.measure(clip,12,d,True);rr=[]
   for f in [13,24]:
    end,ev=rt.measure(clip,f,d,True);rr.append({'frame':f,'boneResidual':max(maxmat(ref['boneMatrices'][n],m) for n,m in end['boneMatrices'].items()),'armatureResidual':maxmat(ref['armatureMatrix'],end['armatureMatrix']),'relativeVertexResidual':residual(refverts,ev)})
   c={'clip':clip,'direction':d,'kind':'one-shot-terminal-hold','frames':[12,13,24],'residuals':rr}
   assert all(max(x['boneResidual'],x['armatureResidual'],x['relativeVertexResidual'])<1e-5 for x in rr),c
  controls.append(c)
  print('FISH_PREFLIGHT',clip,d,'bone',round(maxbone,6),'relativevertex',round(maxvertex,6),flush=True)
write('geometry-ledger.json',{'asset':'creature-fish','projectSHA256':SOURCE_SHA,'views':records,'motionResponse':motion,'closureAndTerminalControls':controls,'globalEvaluatedBounds':{'min':allmin,'max':allmax},'frozenBudget':{'min':[-1.02,-1.02,.02],'max':[1.02,1.02,1.18]},'method':'Actual scene/viewlayer/depsgraph. Raw object-transformed and evaluated modifier vertices all528 required phase/facing cells. Armature inverse removes whole-object bob/rotation for body response. No changing source, camera, materials, light or geometry during validation/capture.'})
write('native-camera.json',rt.camera_record())
if '--measure-only' in sys.argv:print('FISH_PREFLIGHT_COMPLETE',allmin,allmax,flush=True);raise SystemExit
captures=[];sc=bpy.context.scene
for clip,recipe in R['clips'].items():
 for d in rt.FACING:
  for i in range(12):
   rt.apply(clip,i+1,d);row=next(r for r in records if r['clip']==clip and r['direction']==d and r['index']==i)
   path=OUT/'native'/clip/d/(f'{i:03d}.png');path.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(path);start=time.time();bpy.ops.render.render(write_still=True)
   captures.append({'clip':clip,'direction':d,'index':i,'frame':i+1,'path':str(path.relative_to(P.parent)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'dimensions':[1792,2048],'seconds':time.time()-start,
    'rootRotationZ':bpy.data.objects[rt.ROOT].rotation_euler.z,'rootMatrix':rt.mat(bpy.data.objects[rt.ROOT].matrix_world),'cameraMatrix':rt.mat(sc.camera.matrix_world),'evaluatedBounds':row['evaluatedModifierBounds'],'effectiveOwnership':row['effectiveOwnership'],'projectSHA256':SOURCE_SHA})
  write('native-capture-records.json',{'asset':'creature-fish','project':str(SOURCE),'projectSHA256':SOURCE_SHA,'camera':rt.camera_record(),'captureScale':4,'nativeFrame':[1792,2048],'captureRecords':captures,'blender':bpy.app.version_string,'buildHash':bpy.app.build_hash.decode(),'renderEngine':sc.render.engine,'renderSamples':32,'threads':4})
  print('FISH_CAPTURE',clip,d,len(captures),flush=True)
assert len(captures)==528
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_SHA
print('FISH_CAPTURE_COMPLETE',SOURCE_SHA,flush=True)
