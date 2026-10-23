"""Preparation only: evaluate and capture unchanged source from frozen resources."""
import sys, json, math, hashlib, importlib.util
from pathlib import Path
sys.dont_write_bytecode=True
import bpy
from mathutils import Vector
P=Path(__file__).resolve().parent;R=P/'resources'
def load(n):
 s=importlib.util.spec_from_file_location('floor_prep_'+n,R/(n+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
native=load('native_actions');runtime=load('capture_runtime')
scene=bpy.context.scene
rig=json.loads((R/'inputs/source-rig.json').read_text());record=json.loads((R/'inputs/source-assetRecord.json').read_text())
root=bpy.data.objects[rig['groundRootObject']]
col=next(c for c in scene.collection.children if root in list(c.all_objects))
asset=dict(record,root=root,collection=col,clips=rig['clips'])
for c in scene.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
for layer in scene.view_layers[0].layer_collection.children:layer.exclude=layer.collection!=col
col.hide_render=False;col.hide_viewport=False
runtime.scene=lambda:scene;runtime.SCENE_NAME=scene.name
camera=runtime.configure_camera('square-top-front-oblique',(128,128),(64,64),4)
scene.render.image_settings.compression=15
scene.render.use_persistent_data=True
if hasattr(scene.eevee,'taa_render_samples'):scene.eevee.taa_render_samples=32
if hasattr(scene.eevee,'taa_samples'):scene.eevee.taa_samples=32
def pv(v):return [round(float(x),10) for x in v]
def bound(coords):return [[min(p[i] for p in coords),max(p[i] for p in coords)] for i in range(3)]
def point_edge_y(mesh,x):
 out=[]
 for edge in mesh.edges:
  a,b=[mesh.vertices[i].co for i in edge.vertices]
  if (a.x-x)*(b.x-x)<=0 and abs(a.x-b.x)>1e-10:
   t=(x-a.x)/(b.x-a.x);out.append(float(a.y+t*(b.y-a.y)))
 return sorted(set(round(v,9) for v in out))
report={'stage':'unchanged-source-preparation','blender':bpy.app.version_string,'camera':camera,'sceneAtLoad':'preparation-v1/source-collection-first-inspection.json','collection':col.name,'root':{'name':root.name,'location':pv(root.location),'scale':pv(root.scale)},'meshes':[],'materials':[],'actions':[],'phases':{},'resources':{},'lights':[]}
for o in col.all_objects:
 if o.type!='MESH':continue
 d={'name':o.name,'data':o.data.name,'sharedObjectUsers':[x.name for x in bpy.data.objects if x.type=='MESH' and x.data==o.data],'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'uvLayers':[u.name for u in o.data.uv_layers],'hasCustomNormals':o.data.has_custom_normals,'normalZ':sorted(set(round(p.normal.z,6) for p in o.data.polygons)),'materialSlots':[m.name for m in o.data.materials],'modifiers':[m.type for m in o.modifiers],'meshBaseCoordinates':[pv(v.co) for v in o.data.vertices] if len(o.data.vertices)<10 else None}
 report['meshes'].append(d)
for mat in sorted({m for o in col.all_objects if o.type=='MESH' for m in o.data.materials},key=lambda m:m.name):
 ns=[]
 for n in mat.node_tree.nodes:
  vals={}
  for inp in n.inputs:
   if hasattr(inp,'default_value') and not inp.is_linked:
    v=inp.default_value
    if isinstance(v,(str,bool,float,int)):vals[inp.name]=v
    else:
     try:vals[inp.name]=list(v)
     except TypeError:pass
  ns.append({'name':n.name,'type':n.bl_idname,'inputs':vals,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None})
 report['materials'].append({'name':mat.name,'sharedObjectUsers':[o.name for o in bpy.data.objects if o.type=='MESH' and mat in list(o.data.materials)],'nodes':ns,'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in mat.node_tree.links],'animationData':bool(mat.node_tree.animation_data),'surfaceRenderMethod':mat.surface_render_method,'useBackfaceCulling':mat.use_backface_culling})
for target in rig['clips']['scroll']['actions']:
 a=bpy.data.actions[target['action']];curves=native._fcurves(a)
 report['actions'].append({'name':a.name,'owner':target,'frameRange':pv(a.frame_range),'fcurves':[{'path':f.data_path,'index':f.array_index,'keys':[{'co':pv(k.co),'interpolation':k.interpolation} for k in f.keyframe_points]} for f in curves]})
for frame in range(1,14):
 native.apply_clip(asset,rig,'scroll',frame,'S',scene)
 deps=bpy.context.evaluated_depsgraph_get();items=[]
 for o in col.all_objects:
  if o.type!='MESH':continue
  ev=o.evaluated_get(deps);me=ev.to_mesh();coords=[ev.matrix_world@v.co for v in me.vertices]
  items.append({'name':o.name,'bounds':bound(coords),'area':sum(p.area for p in me.polygons),'normalZ':sorted(set(round(p.normal.z,6) for p in me.polygons)),'coordinateSHA256':hashlib.sha256(json.dumps([pv(v) for v in coords],separators=(',',':')).encode()).hexdigest(),'leftBoundaryYAtPitch':point_edge_y(me,-.5),'rightBoundaryYAtPitch':point_edge_y(me,.5),'keyValues':{k.name:k.value for k in o.data.shape_keys.key_blocks} if o.data.shape_keys else {}})
  ev.to_mesh_clear()
 report['phases'][str(frame)]=items
for o in scene.objects:
 if o.type=='LIGHT' and o.data.energy>0:report['lights'].append({'name':o.name,'type':o.data.type,'energy':o.data.energy,'size':getattr(o.data,'size',None),'position':pv(o.location),'rotation':pv(o.rotation_euler)})
ownimages={n.image for m in [m for o in col.all_objects if o.type=='MESH' for m in o.data.materials] for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
report['resources']={'externalLibraries':[x.filepath for x in bpy.data.libraries],'ownImages':[{'name':x.name,'filepath':x.filepath,'packed':bool(x.packed_file)} for x in ownimages],'drivers':[o.name for o in col.all_objects if o.animation_data and o.animation_data.drivers]}
(P/'source-native-audit.json').write_text(json.dumps(report,indent=2)+'\n')
out=P/'replay-raw';out.mkdir(exist_ok=True)
for direction in 'NESW':
 folder=out/direction;folder.mkdir(exist_ok=True)
 for frame in range(1,13):
  native.apply_clip(asset,rig,'scroll',frame,direction,scene)
  scene.render.filepath=str(folder/(str(frame-1).zfill(3)+'.png'))
  bpy.ops.render.render(write_still=True)
  print('FLOOR_REPLAY',direction,frame,flush=True)
native.apply_clip(asset,rig,'scroll',13,'S',scene)
scene.render.filepath=str(out/'S-closure-13.png');bpy.ops.render.render(write_still=True)
print('FLOOR_DONE',flush=True)
