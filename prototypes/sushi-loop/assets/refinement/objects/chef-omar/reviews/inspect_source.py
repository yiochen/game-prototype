"""Judge-only read-only inspection: no .blend writes; source baseline captures."""
import bpy, importlib.util, json, pathlib, hashlib, math, sys
from mathutils import Matrix, Vector
B=pathlib.Path(__file__).resolve().parent.parent
P=B.parents[2]/'production'
H=P/'source/blender'
R=B/'reviews'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def prop(o):
 out={}
 for k in o.keys():
  try:v=o[k];out[k]=v.to_list() if hasattr(v,'to_list') else v.to_dict() if hasattr(v,'to_dict') else v
  except Exception:out[k]=str(o[k])
 return out
rig=json.loads((B/'inputs/source-rig.json').read_text())
cam0=json.loads((B/'inputs/source-camera.json').read_text())
root=bpy.data.objects[rig['groundRootObject']]
coll=next(c for c in bpy.data.collections if root in list(c.objects))
saved={'scene':bpy.context.scene.name,'camera':bpy.context.scene.camera.name if bpy.context.scene.camera else None,'root':prop(root),'collection':coll.name,'rootMatrix':[list(r) for r in root.matrix_world]}
sc=bpy.data.scenes.new('Judge Omar Source Inspection')
sc.collection.children.link(coll);coll.hide_render=False;coll.hide_viewport=False
bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
sc.view_layers[0].update()
native=load('omar_judge_native',H/'native_actions.py')
runtime=load('omar_judge_camera',H/'capture_runtime.py');runtime.scene=lambda:sc;runtime.SCENE_NAME=sc.name
camera=runtime.configure_camera('character-orthographic',(192,320),(96,248),2,35)
sc.render.image_settings.compression=15
asset={'root':root,'collection':coll}
objects=[]
for o in coll.all_objects:
 objects.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'rotationEuler':list(o.rotation_euler),'scale':list(o.scale),'properties':prop(o),'materials':[m.name for m in o.data.materials] if o.type=='MESH' else []})
checks=[]
for clip in ['idle','work','hold','load']:
 for direction in ['N','E','S','W']:
  for i in range(12):
   native.apply_clip(asset,rig,clip,frame=i+1,direction=direction,scene=sc)
   checks.append({'clip':clip,'direction':direction,'index':i,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootLocation':list(root.location),'rootScale':list(root.scale)})
for direction in ['N','E','S','W']:
 native.apply_clip(asset,rig,'idle',frame=1,direction=direction,scene=sc)
 sc.render.filepath=str(R/('source-native-idle-'+direction+'.png'));bpy.ops.render.render(write_still=True)
result={'sourceProject':bpy.data.filepath,'sourceSHA256':sha(bpy.data.filepath),'blenderVersion':bpy.app.version_string,'savedActiveStateNotUsedAsCameraContract':saved,'sourceCollection':coll.name,'camera':camera,'cameraWorldMatrixMaxDifference':max(abs(camera['camera']['worldMatrix'][i][j]-cam0['camera']['worldMatrix'][i][j]) for i in range(4) for j in range(4)),'cameraProjectionMatrixMaxDifference':max(abs(camera['camera']['projectionMatrix'][i][j]-cam0['camera']['projectionMatrix'][i][j]) for i in range(4) for j in range(4)),'objects':objects,'originalActionsApplied':len(checks),'poseFacingSamples':checks,'externalImages':[{'name':im.name,'path':im.filepath,'packed':bool(im.packed_file)} for im in bpy.data.images if im.type!='RENDER_RESULT'],'linkedLibraries':[str(lib.filepath) for lib in bpy.data.libraries],'readOnlySource':True,'blendSaved':False}
(R/'source-native-inspection.json').write_text(json.dumps(result,indent=2,default=str)+'\n')
print('JUDGE_SOURCE_AUDIT',json.dumps({'collection':coll.name,'objectCount':len(objects),'sourceSHA256':result['sourceSHA256'],'cameraWorldMatrixMaxDifference':result['cameraWorldMatrixMaxDifference'],'cameraProjectionMatrixMaxDifference':result['cameraProjectionMatrixMaxDifference'],'sourceSamples':len(checks)}))
