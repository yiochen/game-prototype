import bpy,json,pathlib,importlib.util,math,hashlib
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
out=pathlib.Path(__file__).resolve().parent;res=out/'resources';(out/'source-replay').mkdir(exist_ok=True)
def module(name):
 spec=importlib.util.spec_from_file_location('prep_'+name,res/'blender'/f'{name}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
runtime=module('capture_runtime');native=module('native_actions')
sc=bpy.context.scene;runtime.scene=lambda:sc
rig=json.loads((res/'experiment/inputs/source-rig.json').read_text());asset=json.loads((res/'experiment/inputs/source-assetRecord.json').read_text())
root=bpy.data.objects[rig['groundRootObject']];coll=next(c for c in sc.collection.children if root in list(c.all_objects));asset.update(root=root,collection=coll)
def layers(l):
 yield l
 for child in l.children:yield from layers(child)
for l in layers(sc.view_layers[0].layer_collection):l.exclude=False
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=coll
for c in sc.collection.children:c.hide_render=c!=coll;c.hide_viewport=c!=coll
for o in coll.objects:o.hide_set(False);o.hide_render=False;o.hide_viewport=False
camrec=runtime.configure_camera(asset['projection'],tuple(asset['frame']),tuple(asset['anchor']),asset['scale'])
sc.eevee.taa_render_samples=64;sc.render.filter_size=1.5;sc.render.image_settings.compression=15
sc.render.threads_mode='FIXED';sc.render.threads=4
(out/'source-replay/capture.json').write_text(json.dumps(camrec,indent=2))
originalcam=json.loads((res/'experiment/inputs/source-camera.json').read_text())
assert max(abs(camrec['camera']['projectionMatrix'][i][j]-originalcam['camera']['projectionMatrix'][i][j]) for i in range(4) for j in range(4))<1e-6
assert max(abs(camrec['camera']['worldMatrix'][i][j]-originalcam['camera']['worldMatrix'][i][j]) for i in range(4) for j in range(4))<1e-6
curves=[]
for clip,c in rig['clips'].items():
 for t in c['actions']:
  a=bpy.data.actions[t['action']]
  curves.append({'clip':clip,'owner':t['ownerName'],'action':a.name,'channels':[{'path':fc.data_path,'arrayIndex':fc.array_index,'keys':[{'frame':float(k.co.x),'value':float(k.co.y),'interpolation':k.interpolation} for k in fc.keyframe_points]} for fc in native._fcurves(a)]})
(out/'source-replay/native-curves.json').write_text(json.dumps(curves,indent=2))
def bounds(points):return [[min(p[i] for p in points) for i in range(len(points[0]))],[max(p[i] for p in points) for i in range(len(points[0]))]]
def pose(clip,frame,d):
 native.apply_clip(asset,rig,clip,frame=frame,direction=d,scene=sc);dg=bpy.context.evaluated_depsgraph_get();points=[];states={}
 for o in coll.all_objects:
  if o.type!='MESH':continue
  eo=o.evaluated_get(dg);mesh=eo.to_mesh();points.extend(eo.matrix_world@v.co for v in mesh.vertices);eo.to_mesh_clear()
  states[o.name]={'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'hidden':bool(o.hide_render)}
 xy=[]
 for p in points:
  v=world_to_camera_view(sc,sc.camera,p);xy.append([v.x*asset['frame'][0],(1-v.y)*asset['frame'][1]])
 return {'clip':clip,'frame':frame,'runtimeFrameIndex':frame-1,'direction':d,'nativeBounds':bounds(points),'logicalBounds':bounds(xy),'owners':states}
poses=[];renders=[]
for d in ['N','E','S','W']:
 for clip,frames in [('idle',[1]),('active',list(range(1,14)))]:
  for frame in frames:
   rec=pose(clip,frame,d);poses.append(rec)
   if clip=='idle' or frame in [1,4,7,10]:
    path=out/'source-replay'/f'{clip}-{d}-{frame:02}.png';sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    renders.append({'path':str(path.relative_to(out)),'clip':clip,'frame':frame,'direction':d,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
# Exact original collection/action closure, independent of unrelated library assets.
owned_actions={bpy.data.actions[t['action']] for c in rig['clips'].values() for t in c['actions']}
native.apply_clip(asset,rig,'idle',frame=1,direction='S',scene=sc)
bpy.data.libraries.write(str(out/'source-replay/original-collection.blend'),{coll,*owned_actions},fake_user=True,compress=True)
(out/'source-replay/poses.json').write_text(json.dumps(poses,indent=2));(out/'source-replay/render-manifest.json').write_text(json.dumps({'scope':'Original source native replay, not a candidate. 20 representative captures at 4x, all 52 runtime poses plus closing frame evaluated numerically.','renders':renders},indent=2))
print('SOURCE_REPLAY_DONE',len(poses),len(renders))
