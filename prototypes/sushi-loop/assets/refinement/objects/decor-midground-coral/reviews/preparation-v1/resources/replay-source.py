import bpy, pathlib,json,sys,math,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
BASE=pathlib.Path(__file__).parent.parent
RES=BASE/'resources';sys.dont_write_bytecode=True

def load(name):
 spec=importlib.util.spec_from_file_location('judge_'+name,RES/'native'/(name+'.py'));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
runtime=load('capture_runtime');actions=load('native_actions')
col=bpy.data.collections['S33 production concept pink-coral.001'];root=bpy.data.objects['S33 production concept pink-coral root.001']
# Reconstruct only the registered source asset in a clean scene, avoiding saved unrelated active camera.
runtime.SCENE_NAME='Judge Source Replay decor-midground-coral';sc=runtime.scene();sc.collection.children.link(col)
col.hide_render=False;col.hide_viewport=False
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
for lc in sc.view_layers[0].layer_collection.children:lc.exclude=False;lc.hide_viewport=False
bpy.context.view_layer.update()
asset={'root':root,'collection':col};rig=json.loads((RES/'input/source-rig.json').read_text()); recordedCamera=json.loads((RES/'input/source-camera.json').read_text());meta=runtime.configure_camera('square-top-front-oblique',(192,384),(96,288),4)
# Geometry/source untouched: only camera/light/compositor capture environment is reconstructed.
cam=sc.camera
sc.render.fps=12
folder=BASE/'evidence/native';folder.mkdir(parents=True,exist_ok=True)
def mat(m):return [list(row) for row in m]
def points(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();pts=[root.matrix_world.inverted()@ev.matrix_world@v.co for v in mesh.vertices];polys=[list(p.vertices) for p in mesh.polygons];ev.to_mesh_clear();return pts,polys
records=[]; keyrecords=[]; contactrecords=[]
for direction in ['N','E','S','W']:
 for frame in range(1,14):
  apply=actions.apply_clip(asset,rig,'idle',frame,direction,sc);bpy.context.view_layer.update()
  pts=[];meshrows=[];treeverts=[];treepolys=[]
  for o in col.all_objects:
   if o.type!='MESH':continue
   pp,faces=points(o);pts.extend(pp)
   meshrows.append({'name':o.name,'rotation':list(o.rotation_euler),'location':list(o.location),'scale':list(o.scale),'bounds':[[min(p[i] for p in pp),max(p[i] for p in pp)] for i in range(3)]})
   if o.get('studyRole')=='body':
    offset=len(treeverts);treeverts.extend(pp);treepolys.extend([[offset+v for v in face] for face in faces])
  tree=BVHTree.FromPolygons(treeverts,treepolys,all_triangles=False)
  # Finite vertical surface tests for original coral base rings: compare actual z to actual rubble surface.
  contacts=[]
  for o in col.all_objects:
   if o.type!='MESH' or o.get('studyRole')!='vegetation':continue
   pp,faces=points(o);ring=pp[:12];tests=[]
   for p in ring:
    hit,normal,index,distance=tree.ray_cast(Vector((p.x,p.y,2)),Vector((0,0,-1)),3)
    tests.append({'point':list(p),'surfaceZ':hit.z if hit else None,'penetration':hit.z-p.z if hit else None})
   contacts.append({'name':o.name,'baseRingTests':tests,'supportedRingPoints':sum(t['penetration'] is not None and t['penetration']>=-1e-5 for t in tests)})
  px=[world_to_camera_view(sc,cam,root.matrix_world@p) for p in pts]
  row={'direction':direction,'frame':frame,'rootRotationZ':root.rotation_euler.z,'rootMatrix':mat(root.matrix_world),'boundsRoot':[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)],'projectedBoundsPixels':[min(p.x for p in px)*768,min((1-p.y) for p in px)*1536,max(p.x for p in px)*768,max((1-p.y) for p in px)*1536],'objects':meshrows}
  records.append(row);contactrecords.append({'direction':direction,'frame':frame,'tubeContacts':contacts})
  dest=folder/direction/f'{frame-1:03}.png';dest.parent.mkdir(exist_ok=True);sc.render.filepath=str(dest);bpy.ops.render.render(write_still=True,scene=sc.name)
  print('CAPTURED',direction,frame,flush=True)
# exact all actual key channels, including duplicate loop closure
for entry in rig['clips']['idle']['actions']:
 owner=bpy.data.objects[entry['ownerName']];action=bpy.data.actions[entry['action']];channels=[]
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in bag.fcurves:channels.append({'path':curve.data_path,'index':curve.array_index,'keys':[[float(k.co.x),float(k.co.y),k.interpolation] for k in curve.keyframe_points]})
 keyrecords.append({'owner':owner.name,'action':action.name,'slot':owner.animation_data.action_slot.identifier,'channels':channels})
source={'asset':'decor-midground-coral','sourceFile':str(RES/'native/original-library.blend'),'originalSavedFrame':4,'nativeFrame':[768,1536],'logicalFrame':[192,384],'logicalRoot':[96,288],'sourceScale':4,'publishedSourceScale':2,'camera':meta,'inputCamera':recordedCamera,'cameraMatrixMaxDifference':max(abs(meta['camera']['worldMatrix'][i][j]-recordedCamera['camera']['worldMatrix'][i][j]) for i in range(4) for j in range(4)),'captureRecords':records,'temporalKeys':keyrecords,'contacts':contactrecords,'rootTransform':{'location':list(root.location),'scale':list(root.scale)},'lightRig':[{'name':o.name,'role':o.get('s33FacetedRole'),'location':list(o.location),'color':list(o.data.color),'energy':o.data.energy,'size':o.data.size} for o in sc.objects if o.type=='LIGHT'],'dependencies':'resources/native/* and input/source-rig.json, frozen before replay','limitations':['Replay uses exact saved native action cohort. Original snapshot can originate from pose callback with name-sensitive phase; decoded difference is measured separately.','No candidate constructed. Source design, shaders and geometry retained.']}
(BASE/'source-replay.json').write_text(json.dumps(source,indent=2)+'\n')
print('REPLAY_COMPLETE',flush=True)
