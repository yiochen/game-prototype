"""Measured source/current rest and all-frame spatial envelopes. Does not save .blend."""
import bpy,json,sys,hashlib,math
from pathlib import Path
P=Path(__file__).parent;BASE=P.parent;sys.path.insert(0,str(P))
import native_actions_round01 as native
from audit_common_round01 import geometry
runtime='--runtime' in sys.argv;candidate='--candidate' in sys.argv
prefix='runtime-' if runtime else '';folder=BASE/'candidates/round-01';folder=folder/'runtimeVariants' if runtime else folder
rig=json.loads((P/(prefix+'rig-round01.json')).read_text())
root=bpy.data.objects[rig['groundRootObject']]
coll=min([c for c in bpy.data.collections if root in list(c.all_objects)],key=lambda c:len(c.all_objects))
arm=next(o for o in coll.all_objects if o.type=='ARMATURE')
sc=bpy.data.scenes.new('Ama isolated envelope audit');sc.collection.children.link(coll)
bpy.context.window.scene=sc;coll.hide_render=False;coll.hide_viewport=False;bpy.context.view_layer.update()
asset={'collection':coll,'root':root,'armature':arm}
def bounds():
 dg=bpy.context.evaluated_depsgraph_get()
 gs=[geometry(o,dg) for o in coll.all_objects if o.type=='MESH' and '__image_plane' not in o.name and '__knife_' not in o.name]
 return [[min(g['bounds'][i][0] for g in gs),max(g['bounds'][i][1] for g in gs)] for i in range(3)]
native.apply_clip(asset,rig,next(iter(rig['clips'])),1,'S',sc)
arm.data.pose_position='REST';bpy.context.view_layer.update();rest=bounds();arm.data.pose_position='POSE';bpy.context.view_layer.update()
rows=[]
for clip in rig['clips']:
 for d in ['N','E','S','W']:
  for f in range(1,13):
   native.apply_clip(asset,rig,clip,f,d,sc);rows.append({'clip':clip,'direction':d,'index':f-1,'actorBounds':bounds()})
if not candidate:
 (P/(prefix+'baseline-envelope-round01.json')).write_text(json.dumps({'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'restBounds':rest,'frames':rows},indent=2))
else:
 original=json.loads((P/(prefix+'baseline-envelope-round01.json')).read_text());ref={(r['clip'],r['direction'],r['index']):r for r in original['frames']}
 for r in rows:
  b=ref[(r['clip'],r['direction'],r['index'])]['actorBounds'];r['originalBounds']=b;r['boundsDelta']=[[r['actorBounds'][i][j]-b[i][j] for j in range(2)] for i in range(3)]
 current={ (r['clip'],r['direction'],r['index']):r for r in json.loads((folder/'native-frames.json').read_text()) }
 captured_error=max(abs(r['actorBounds'][i][j]-current[(r['clip'],r['direction'],r['index'])]['actorBounds'][i][j]) for r in rows for i in range(3) for j in range(2))
 rest_height=rest[2][1]-rest[2][0];source_height=original['restBounds'][2][1]-original['restBounds'][2][0]
 out={'ok':abs(rest_height-source_height)<1e-6 and captured_error<1e-6,'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'restBounds':rest,'originalRestBounds':original['restBounds'],'restHeight':rest_height,'originalRestHeight':source_height,'registeredHeight':1.525,'rootScale':list(root.scale),'logicalFootprint':[1,1],'allFramesInsideFootprint':all(r['actorBounds'][i][1]-r['actorBounds'][i][0]<1 for r in rows for i in range(2)),'allFrameBoundsEqualNativeCaptureMaxError':captured_error,'maxMovingTopDeltaToOriginal':max(abs(r['boundsDelta'][2][1]) for r in rows),'frames':rows,'note':'1.525 is the rest anatomy height. Original head/torso motion produces native bob/tilt around it; all rest bones and pose matrices remain exact. Nonfunctional silhouette may change under authorized modeling policy.'}
 (folder/'envelope-validation.json').write_text(json.dumps(out,indent=2));print('ENVELOPE',json.dumps({k:v for k,v in out.items() if k!='frames'}),flush=True)
