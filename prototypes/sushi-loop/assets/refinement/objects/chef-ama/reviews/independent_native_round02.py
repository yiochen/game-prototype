import bpy,json,sys,hashlib,numpy as np,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-ama');R=P/'reviews/round02-independent-native';R.mkdir(exist_ok=True);role=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'candidate';sys.path.insert(0,str(P.parents[2]/'production/source/blender'));import native_actions as NA
rig=json.loads((P/'inputs/source-rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']];coll=next(c for c in bpy.data.collections if root in list(c.all_objects));sc=next(s for s in bpy.data.scenes if root.name in s.objects);bpy.context.window.scene=sc
for lc in sc.view_layers[0].layer_collection.children:lc.exclude=False
coll.hide_render=False;coll.hide_viewport=False;bpy.context.view_layer.update();objects=sorted(list(coll.all_objects),key=lambda o:o.name);physical=[o for o in objects if o.type=='MESH' and '__image_plane' not in o.name];plane=next(o for o in objects if '__image_plane' in o.name);arm=next(o for o in objects if o.type=='ARMATURE');asset={'root':root,'collection':coll}
def H(x):return hashlib.sha256(x).hexdigest()
def arr(collection,key,n):
 a=np.empty(len(collection)*n,dtype=np.float32);collection.foreach_get(key,a);return H(a.tobytes())
def mat(m):return [list(r) for r in m]
def val(v):
 if isinstance(v,(int,float,str,bool)) or v is None:return v
 if hasattr(v,'name'):return v.name
 try:return list(v)
 except:return str(v)
def graph(nt):
 if not nt:return None
 return {'nodes':[{'name':n.name,'type':n.type,'inputs':[(i.name,val(i.default_value)) for i in n.inputs if hasattr(i,'default_value')],'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None} for n in nt.nodes],'links':sorted([(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in nt.links])}
static={'meshes':{},'actions':{},'restBones':{bb.name:{'parent':bb.parent.name if bb.parent else None,'deform':bb.use_deform,'matrix':mat(bb.matrix_local)} for bb in arm.data.bones},'materials':{m.name:graph(m.node_tree) for m in bpy.data.materials if m.users},'lights':{o.name:{'position':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size,'type':o.data.type} for o in sc.objects if o.type=='LIGHT'},'world':graph(sc.world.node_tree),'camera':{'matrix':mat(sc.camera.matrix_world),'ortho':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y]},'render':{'frame':[sc.render.resolution_x,sc.render.resolution_y],'aspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'fps':sc.render.fps,'engine':sc.render.engine,'device':sc.cycles.device,'samples':sc.cycles.samples,'seed':sc.cycles.seed,'animatedSeed':sc.cycles.use_animated_seed,'adaptive':sc.cycles.use_adaptive_sampling,'adaptiveThreshold':sc.cycles.adaptive_threshold,'denoise':sc.cycles.use_denoising,'filter':sc.cycles.pixel_filter_type,'filterWidth':sc.cycles.filter_width,'view':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure}}
for o in physical:
 mesh=o.data;static['meshes'][o.name]={'co':arr(mesh.vertices,'co',3),'normals':arr(mesh.vertices,'normal',3),'cornerNormals':arr(mesh.corner_normals,'vector',3),'topology':H(json.dumps({'faces':[list(p.vertices) for p in mesh.polygons],'smooth':[p.use_smooth for p in mesh.polygons],'matIndex':[p.material_index for p in mesh.polygons],'uv':{uv.name:[list(v.uv) for v in uv.data] for uv in mesh.uv_layers}},sort_keys=True).encode()),'weights':H(json.dumps([[(g.group,g.weight) for g in v.groups] for v in mesh.vertices]).encode()),'materials':[m.name if m else None for m in mesh.materials],'parent':o.parent.name if o.parent else None,'matrixParentInverse':mat(o.matrix_parent_inverse),'modifiers':[(m.name,m.type,m.object.name if m.type=='ARMATURE' and m.object else None) for m in o.modifiers]}
for n in sorted({a['action'] for c in rig['clips'].values() for a in c['actions']}):
 a=bpy.data.actions[n];curves=[]
 for fc in NA._fcurves(a):curves.append({'path':fc.data_path,'index':fc.array_index,'extrapolation':fc.extrapolation,'keys':[(list(k.co),list(k.handle_left),list(k.handle_right),k.interpolation,k.handle_left_type,k.handle_right_type) for k in fc.keyframe_points]})
 static['actions'][n]=H(json.dumps(curves,sort_keys=True).encode())
phases=[]
for clip in ['idle','work','hold','load']:
 for d in ['N','E','S','W']:
  for index in range(12):
   NA.apply_clip(asset,rig,clip,index+1,d,sc);visibility={o.name:[o.hide_render,o.hide_viewport] for o in objects}
   for o in objects:o.hide_viewport=False
   bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();records={}
   for o in physical:
    ev=o.evaluated_get(dg);m=ev.to_mesh();records[o.name]={'co':arr(m.vertices,'co',3),'normal':arr(m.vertices,'normal',3),'cornerNormal':arr(m.corner_normals,'vector',3),'polygonNormal':arr(m.polygons,'normal',3),'matrix':mat(ev.matrix_world),'counts':[len(m.vertices),len(m.edges),len(m.polygons),len(m.loops)],'visibility':visibility[o.name]};ev.to_mesh_clear()
   ap=arm.evaluated_get(dg);pe=plane.evaluated_get(dg);rp=world_to_camera_view(sc,sc.camera,Vector((0,0,0)))
   phases.append({'clip':clip,'direction':d,'index':index,'physicalObjects':records,'pose':{pb.name:mat(pb.matrix) for pb in ap.pose.bones},'rootMatrix':mat(root.matrix_world),'rootRotation':root.rotation_euler.z,'rootNativePixel':[rp.x*sc.render.resolution_x,(1-rp.y)*sc.render.resolution_y],'planeMatrix':mat(pe.matrix_world),'planeVisibility':visibility[plane.name]})
   for o in objects:o.hide_viewport=visibility[o.name][1]
# Render controls from unchanged exact saved file. No source writes or render-setting edits except installed Metal device selection/output path.
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for dev in prefs.devices:dev.use=(dev.type=='METAL')
controls=[]
for clip,d,index,label in [('hold','S',0,'hold-S-000-a'),('hold','S',0,'hold-S-000-b'),('hold','N',5,'hold-N-005'),('load','W',5,'load-W-005')]:
 NA.apply_clip(asset,rig,clip,index+1,d,sc);sc.render.filepath=str(R/(role+'-'+label+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name);controls.append({'clip':clip,'direction':d,'index':index,'path':str((R/(role+'-'+label+'.png')).relative_to(P)),'sha256':H((R/(role+'-'+label+'.png')).read_bytes())})
im=next(n.image for m in plane.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE')
food={'quad':[list(v.co) for v in plane.data.vertices],'uv':[list(v.uv) for v in plane.data.uv_layers.active.data],'packedSHA256':H(im.packed_file.data),'size':list(im.size),'rayFlags':{k:getattr(plane,k) for k in ['visible_camera','visible_diffuse','visible_glossy','visible_shadow','visible_transmission','visible_volume_scatter']},'drivers':[(fc.data_path,fc.array_index,fc.driver.expression) for fc in plane.animation_data.drivers],'images':[{'name':i.name,'packed':bool(i.packed_file),'sha256':H(i.packed_file.data) if i.packed_file else None} for i in bpy.data.images if i.type=='IMAGE'],'libraries':[l.filepath for l in bpy.data.libraries]}
(R/(role+'.json')).write_text(json.dumps({'role':role,'sourceSHA256':H(Path(bpy.data.filepath).read_bytes()),'static':static,'phases':phases,'food':food,'controls':controls},sort_keys=True)+'\n');print('AMA_ROUND02_JUDGE_NATIVE',role,len(phases),len(physical))
