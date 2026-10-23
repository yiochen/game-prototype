import bpy, json, sys, math, hashlib, importlib.util
from pathlib import Path
from mathutils import Vector
import numpy as np

HERE=Path(__file__).resolve().parent
OBJ=HERE.parents[1]
MODE=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'main'
HELP=OBJ.parents[2]/'production/source/blender'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
native=module('judge_native',HELP/'native_actions.py')
record=json.loads((OBJ/('inputs/source-rig.json' if MODE=='main' else 'inputs/runtime-variants/export/source/customer-ellis/rig.json')).read_text())
root=bpy.data.objects[record['groundRootObject']]
sc=next(s for s in bpy.data.scenes if root.name in s.objects)
bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
collection=next(c for c in sc.collection.children if root.name in c.all_objects)
for c in sc.collection.children:c.hide_render=c!=collection;c.hide_viewport=c!=collection
for c in [collection]+list(collection.children_recursive):c.hide_render=False;c.hide_viewport=False
def show(layer):
 layer.exclude=False;layer.hide_viewport=False
 for child in layer.children:show(child)
show(sc.view_layers[0].layer_collection)
objects=list(collection.all_objects)
asset={'root':root,'collection':collection}
cam=sc.camera
original_camera={'name':cam.name,'matrix':plain(cam.matrix_world) if 'plain' in globals() else [list(r) for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'resolution':[sc.render.resolution_x,sc.render.resolution_y]}
# Use the actual saved camera of the scene containing Ellis, never startup.
saved=json.loads((OBJ/'inputs/source-camera.json').read_text())
assert cam.data.type=='ORTHO' and abs(cam.data.ortho_scale-1.5)<1e-8
assert max(abs(cam.matrix_world[r][c]-saved['camera']['worldMatrix'][r][c]) for r in range(4) for c in range(4))<1e-6
sc.camera=cam;sc.render.resolution_x=384;sc.render.resolution_y=640;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=1;sc.render.pixel_aspect_y=1;sc.render.fps=12
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.film_transparent=True
bpy.context.view_layer.update()
from bpy_extras.object_utils import world_to_camera_view
def project(p):
 q=world_to_camera_view(sc,cam,Vector(p));return [q.x*384,(1-q.y)*640,q.z]
assert max(abs(a-b) for a,b in zip(project((0,0,0))[:2],[192,496]))<.001
def plain(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return [plain(x) for x in v]
 except:return str(v)
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def props(o):return {k:plain(o[k]) for k in o.keys()}
arm=next(o for o in objects if o.type=='ARMATURE')
food=next(o for o in objects if o.get('representation')=='2D ImageGen sprite, not modeled sushi')
foodroot=food.parent
texture=next(n.image for mat in food.data.materials if mat and mat.use_nodes for n in mat.node_tree.nodes if n.type=='TEX_IMAGE')
packed=bytes(texture.packed_file.data);(HERE/(MODE+'-source-food.png')).write_bytes(packed)
inventory=[]
for o in objects:
 inventory.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'parent_type':o.parent_type,'parent_bone':o.parent_bone,'matrix_parent_inverse':plain(o.matrix_parent_inverse),'location':plain(o.location),'scale':plain(o.scale),'props':props(o),'modifiers':[{'type':m.type,'object':getattr(getattr(m,'object',None),'name',None)} for m in o.modifiers]})
rest=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':plain(b.head_local),'tail':plain(b.tail_local),'matrix':plain(b.matrix_local),'deform':b.use_deform} for b in arm.data.bones]
actions={}
for clip,c in record['clips'].items():
 actions[clip]=[]
 for t in c['actions']:
  a=bpy.data.actions[t['action']];curves=[{'path':f.data_path,'index':f.array_index,'keys':[[float(k.co.x),float(k.co.y),k.interpolation] for k in f.keyframe_points]} for f in native._fcurves(a)]
  actions[clip].append({**t,'curveDigest':digest(curves),'curves':curves})
drivers=[]
for f in food.animation_data.drivers:
 drivers.append({'path':f.data_path,'index':f.array_index,'expression':f.driver.expression,'variables':[{'name':v.name,'targets':[{'id':t.id.name,'path':t.data_path} for t in v.targets]} for v in f.driver.variables]})
report={'mode':MODE,'sourceProject':bpy.data.filepath,'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'scene':sc.name,'collection':collection.name,'originalSavedCamera':original_camera,'camera':{'name':cam.name,'matrix':plain(cam.matrix_world),'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'resolution':[384,640],'rootProjection':project((0,0,0)),'unitXProjection':project((1,0,0)),'unitYProjection':project((0,1,0)),'unitZProjection':project((0,0,1))},'root':{'name':root.name,'matrix':plain(root.matrix_world),'props':props(root)},'inventory':inventory,'armature':{'name':arm.name,'matrix':plain(arm.matrix_world),'props':props(arm),'rest':rest,'restSHA256':digest(rest)},'food':{'plane':food.name,'root':foodroot.name,'vertices':plain([v.co for v in food.data.vertices]),'uv':plain([u.uv for u in food.data.uv_layers.active.data]),'drivers':drivers,'props':props(food),'image':{'name':texture.name,'size':plain(texture.size),'packedSHA256':hashlib.sha256(packed).hexdigest(),'extracted':MODE+'-source-food.png','filepath':texture.filepath}},'actions':actions,'samples':[]}
def meshcoords(o,dg):
 e=o.evaluated_get(dg);m=e.to_mesh();arr=np.empty(len(m.vertices)*3,dtype=np.float64);m.vertices.foreach_get('co',arr);arr=arr.reshape((-1,3));mat=np.array(e.matrix_world);w=arr@mat[:3,:3].T+mat[:3,3];e.to_mesh_clear();return w
def bounds(points):return [points.min(axis=0).tolist(),points.max(axis=0).tolist()] if len(points) else None
def project_array(w):
 return np.column_stack((192+w[:,0]*256,496-256*(w[:,1]*math.sin(math.radians(35))+w[:,2]*math.cos(math.radians(35)))))
original=json.loads((OBJ/'reviews'/(MODE+'-audit.json')).read_text())
origlookup={(s['clip'],s['direction'],s['frame']):s for s in original['samples']}
from mathutils.bvhtree import BVHTree
def surface(o,dg,point):
 e=o.evaluated_get(dg);m=e.to_mesh();verts=[e.matrix_world@v.co for v in m.vertices];tree=BVHTree.FromPolygons(verts,[list(f.vertices) for f in m.polygons]);hit=tree.find_nearest(Vector(point));e.to_mesh_clear();return {'sourceWitness':list(point),'nearest':list(hit[0]),'error':float(hit[3])} if hit else None
renderdir=HERE/(MODE+'-native');renderdir.mkdir(exist_ok=True)
for clip,c in record['clips'].items():
 for direction in ['S','E','N','W']:
  for f in range(1,c['frames']+1):
   native.apply_clip(asset,record,clip,frame=f,direction=direction,scene=sc)
   # Hidden food still has a prescribed attachment path. Temporarily expose it
   # to viewport evaluation only; retain authored render visibility and actions.
   food_source_viewport=food.hide_viewport
   food.hide_viewport=False;food.hide_set(False);food.update_tag();bpy.context.view_layer.update()
   dg=bpy.context.evaluated_depsgraph_get();ri=np.array(root.matrix_world.inverted())
   visible=[o for o in objects if o.type=='MESH' and o!=food and not o.hide_render]
   coords=[meshcoords(o,dg) for o in visible];world=np.concatenate(coords) if coords else np.empty((0,3));local=world@ri[:3,:3].T+ri[:3,3]
   bone={b.name:{'head':plain(arm.matrix_world@b.head),'tail':plain(arm.matrix_world@b.tail),'matrix':plain(arm.matrix_world@b.matrix)} for b in arm.pose.bones if b.name in ['pelvis','spine','head','hand_L','hand_R','foot_L','foot_R','hand_goal_L','hand_goal_R','foot_goal_L','foot_goal_R']}
   fc=meshcoords(food,dg)
   sample={'clip':clip,'direction':direction,'frame':f,'rootMatrix':plain(root.matrix_world),'nativeBodyBoundsWorld':bounds(world),'nativeBodyBoundsRoot':bounds(local),'nativeBodyProjectedBounds':bounds(project_array(world)),'contacts':bone,'food':{'visible':not food.hide_render,'authoredHideViewport':food_source_viewport,'rootMatrix':plain(foodroot.matrix_world),'rootProjected':project(foodroot.matrix_world.translation),'planeMatrix':plain(food.matrix_world),'cornersWorld':fc.tolist(),'cornersProjected':[project(v) for v in fc],'localLocation':plain(food.location),'yaw':food.rotation_euler.z},'perMeshBoundsWorld':{o.name:bounds(arr) for o,arr in zip(visible,coords)}}
   originalSample=origlookup[(clip,direction,f)]
   surfaceChecks=[]
   for o in visible:
    if o.name not in originalSample['perMeshBoundsWorld']:continue
    b=originalSample['perMeshBoundsWorld'][o.name];center=[(b[0][j]+b[1][j])*.5 for j in range(3)]
    if '__palm_' in o.name or '__thumb_' in o.name:
     candidateBounds=sample['perMeshBoundsWorld'][o.name];cc=[(candidateBounds[0][j]+candidateBounds[1][j])*.5 for j in range(3)]
     surfaceChecks.append({'object':o.name,'kind':'palm-thumb-geometric-center-vs-source','error':float(np.linalg.norm(np.array(center)-cc)),'sourceCenter':center,'candidateCenter':cc,'groups':[g.name for g in o.vertex_groups]})
    if '__minimal_foot_' in o.name:
     center[2]=b[0][2];surfaceChecks.append({'object':o.name,'kind':'source-sole-center-to-evaluated-surface',**surface(o,dg,center)})
   # Source functional mouth point transported by the unchanged native head bone.
   head=arm.pose.bones['head'];mouth=arm.matrix_world@head.matrix@arm.data.bones['head'].matrix_local.inverted()@Vector((0,-.235,.543));headObj=next(o for o in visible if o.name.endswith('__head.001'))
   surfaceChecks.append({'object':headObj.name,'kind':'mouth-carrier',**surface(headObj,dg,mouth)})
   sample['independentSurfaceChecks']=surfaceChecks
   report['samples'].append(sample)
   if f==5 and clip in (['stand','eat'] if MODE=='main' else ['eat-salmon']):
    sc.render.filepath=str(renderdir/(clip+'-'+direction+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name)
 (HERE/(MODE+'-audit.partial.json')).write_text(json.dumps(report,separators=(',',':')))
report['sampleDigest']=digest(report['samples']);report['sampleCount']=len(report['samples'])
(HERE/(MODE+'-audit.json')).write_text(json.dumps(report,separators=(',',':')))
print('JUDGE_AUDIT_COMPLETE',MODE,len(report['samples']),report['sampleDigest'],flush=True)
