import bpy,json,math,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round-01'
rig=json.loads((OBJ/'inputs/source-rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']];col=bpy.data.collections['S33_CHARACTER_chef_rowan.001']
spec=importlib.util.spec_from_file_location('native',HERE/'resources/original-native-actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
col.hide_viewport=False;col.hide_render=False;bpy.context.view_layer.update()
asset=dict(root=root,collection=col);food=bpy.data.objects[root.name+'__held_dish-salmon'];plane=bpy.data.objects[food.name+'__image_plane']
drivers=[]
for o in [root,food,plane]:
 if o.animation_data:
  for f in o.animation_data.drivers:
   drivers.append(dict(object=o.name,path=f.data_path,index=f.array_index,expression=f.driver.expression,
                       variables=[dict(name=v.name,type=v.type,targets=[dict(object=getattr(t.id,'name',None),dataPath=t.data_path) for t in v.targets]) for v in f.driver.variables]))
records=[]
for clip in rig['clips']:
 for direction in ['N','E','S','W']:
  for frame in range(1,13):
   native.apply_clip(asset,rig,clip,frame,direction,bpy.context.scene);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();m=plane.evaluated_get(dg).matrix_world
   records.append(dict(clip=clip,direction=direction,frame=frame,worldRotation=[list(r) for r in m.to_3x3().normalized()],worldWidth=(m.to_3x3()@Vector((.28,0,0))).length,worldHeight=(m.to_3x3()@Vector((0,.28*505/731,0))).length))
baseline=records[0]['worldRotation'];maxrot=max(abs(r['worldRotation'][i][j]-baseline[i][j]) for r in records for i in range(3) for j in range(3))
original=json.loads((HERE/'inspection-v1/native-action-audit.json').read_text());old={(f['clip'],f['direction'],f['frame']):f for f in original['frames']}
audit=json.loads((OUT/'native-audit.json').read_text());knife_error=0
for f in audit['frames']:
 o=old[(f['clip'],f['direction'],f['frame'])]
 for key in [root.name+'__knife_blade',root.name+'__knife_handle']:
  if key in f['object_bounds']:
   knife_error=max(knife_error,max(abs(a-b) for ra,rb in zip(f['object_bounds'][key],o['object_bounds'][key]) for a,b in zip(ra,rb)))
data=dict(activeBrief='brief-v2-food.json',sourceSHA256=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
          originalYawCancellationDrivers=drivers,planeLocalLocation=list(plane.location),planeLocalRotation=list(plane.rotation_euler),
          actualCameraRayDepthBiasWorld=Vector(plane.location).length*root.scale.x,
          maximumWorldOrientationDifferenceAcross192=maxrot,sourceNativeKnifeBoundsMaximumError=knife_error,
          checks=[dict(name='food camera orientation fixed through native yaw cancellation',passed=maxrot<1e-6),
                  dict(name='exact .35 world display width every pose',passed=all(abs(r['worldWidth']-.35)<1e-6 for r in records)),
                  dict(name='exact canonical731:505 aspect every pose',passed=all(abs(r['worldHeight']-.35*505/731)<1e-6 for r in records)),
                  dict(name='original .6 world camera ray depth bias',passed=abs(Vector(plane.location).length*root.scale.x-.6)<1e-6),
                  dict(name='original native knife bounds every pose',passed=knife_error<1e-6)],records=records)
data['allChecksPassed']=all(c['passed'] for c in data['checks'])
(OUT/'food-native-audit.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({k:v for k,v in data.items() if k!='records'},indent=2))
