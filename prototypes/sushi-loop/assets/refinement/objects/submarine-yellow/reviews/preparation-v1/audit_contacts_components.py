import bpy,json,math,pathlib,hashlib
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
out=pathlib.Path(__file__).resolve().parent;res=out/'resources';rig=json.loads((res/'source-rig.json').read_text());sc=bpy.context.scene
c=bpy.data.collections['S33_PROP_submarine_base.001'];root=bpy.data.objects[rig['groundRootObject']];obs=list(c.all_objects);meshes=[o for o in obs if o.type=='MESH']
def vv(v): return [round(float(x),9) for x in v]
def box(points):return [vv([min(p[i] for p in points) for i in range(3)]),vv([max(p[i] for p in points) for i in range(3)])] if points else None
def datahash(o):return hashlib.sha256(json.dumps({'v':[vv(v.co) for v in o.data.vertices],'p':[list(p.vertices) for p in o.data.polygons]},sort_keys=True).encode()).hexdigest()
initial={'activeCamera':{'name':sc.camera.name,'matrix':[vv(x) for x in sc.camera.matrix_world],'ortho_scale':sc.camera.data.ortho_scale,'shift_x':sc.camera.data.shift_x,'shift_y':sc.camera.data.shift_y},'render':{'resolution':[sc.render.resolution_x,sc.render.resolution_y],'filter_size':sc.render.filter_size,'engine':sc.render.engine,'transparent':sc.render.film_transparent,'view_transform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma},'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'location':vv(o.location),'size':getattr(o.data,'size',None)} for o in sc.objects if o.type=='LIGHT'],'collections':[{'name':x.name,'hide_render':x.hide_render,'objects':len(x.all_objects)} for x in bpy.data.collections if any(q in x.name.lower() for q in ['hull','harpoon','collector','dock','workshop'])]}
oldsc=sc
sc=bpy.data.scenes.new('Judge native audit');sc.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
for light in [o for o in oldsc.objects if o.type=='LIGHT']:sc.collection.objects.link(light)
sc.world=oldsc.world;sc.render.engine=oldsc.render.engine;sc.render.film_transparent=True;sc.render.filter_size=oldsc.render.filter_size;sc.view_settings.view_transform=oldsc.view_settings.view_transform;sc.view_settings.look=oldsc.view_settings.look;sc.view_settings.exposure=oldsc.view_settings.exposure;sc.view_settings.gamma=oldsc.view_settings.gamma
bpy.context.window.scene=sc
camd=bpy.data.cameras.new('Judge source camera calibration');cam=bpy.data.objects.new('Judge source camera calibration',camd);sc.collection.objects.link(cam);camd.type='ORTHO';camd.ortho_scale=3;camd.shift_y=.25;cam.matrix_world=Matrix(json.loads((res/'source-camera.json').read_text())['camera']['worldMatrix']);sc.camera=cam;sc.render.resolution_x=640;sc.render.resolution_y=768;sc.render.resolution_percentage=100
project=lambda p:vv([world_to_camera_view(sc,cam,Vector(p)).x*640,(1-world_to_camera_view(sc,cam,Vector(p)).y)*768])
initial['calibratedCamera']={'matrix':[vv(x) for x in cam.matrix_world],'ortho_scale':3,'shift_y':.25,'root':project((0,0,0)),'unitX':project((1,0,0)),'unitY':project((0,1,0)),'unitZ':project((0,0,1)),'elevationDegrees':math.degrees(math.asin(cam.matrix_world.to_3x3().col[2].z))}
initial['objects']=[{'name':o.name,'parent':o.parent.name if o.parent else None,'mesh':o.data.name,'geometrySHA256':datahash(o),'materials':[m.name for m in o.data.materials],'uvLayers':[x.name for x in o.data.uv_layers],'modifiers':[{'type':m.type,'name':m.name} for m in o.modifiers],'constraints':[{'type':x.type,'name':x.name} for x in o.constraints],'vertices':len(o.data.vertices),'polygons':len(o.data.polygons)} for o in meshes]
initial['resources']={'externalImages':[{'name':x.name,'path':x.filepath,'packed':bool(x.packed_file)} for x in bpy.data.images if x.source=='FILE'],'libraries':[x.filepath for x in bpy.data.libraries],'texts':[x.name for x in bpy.data.texts]}
materials=set(m for o in meshes for m in o.data.materials if m);initial['materials']=[]
for m in materials:
 initial['materials'].append({'name':m.name,'diffuse':vv(m.diffuse_color),'nodes':[{'name':n.name,'type':n.type,'inputs':{s.name:(vv(s.default_value) if hasattr(s.default_value,'__len__') and not isinstance(s.default_value,str) else s.default_value) for s in n.inputs if hasattr(s,'default_value') and not s.is_linked and (isinstance(s.default_value,(int,float,bool,str)) or hasattr(s.default_value,'__len__'))}} for n in m.node_tree.nodes] if m.use_nodes else []})
family=[]
for col in bpy.data.collections:
 if any(q in col.name.lower() for q in ['hull_panel','harpoon_mount','collector_inlet']):
  family.append({'collection':col.name,'objects':[{'name':o.name,'parent':o.parent.name if o.parent else None,'mesh':o.data.name if o.type=='MESH' else None,'geometrySHA256':datahash(o) if o.type=='MESH' else None,'location':vv(o.location),'scale':vv(o.scale),'rotation':vv(o.rotation_euler),'matrix':[vv(r) for r in o.matrix_world],'materials':[m.name for m in o.data.materials] if o.type=='MESH' else []} for o in col.all_objects]})
initial['familyComponentCollections']=family
(out/'contact-audit-inventory.json').write_text(json.dumps(initial,indent=2))
def apply(clip,frame,d):
 for o in obs:
  if o.animation_data:
   o.animation_data.action=None
   for tr in o.animation_data.nla_tracks: tr.mute=True
 for t in rig['clips'][clip]['actions']:
  assert t['ownerType']=='Object',t
  o=bpy.data.objects[t['ownerName']];o.animation_data_create();a=bpy.data.actions[t['action']];o.animation_data.action=a
  slots=[s for s in a.slots if s.identifier==t['slotIdentifier']];assert len(slots)==1;tgt=slots[0];o.animation_data.action_slot=tgt
 root.rotation_euler.z={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[d];sc.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update()
def phase(clip,frame,d):
 apply(clip,frame,d);dg=bpy.context.evaluated_depsgraph_get();allpts=[];parts=[]
 for o in meshes:
  if o.hide_render: continue
  eo=o.evaluated_get(dg);me=eo.to_mesh();pts=[eo.matrix_world@v.co for v in me.vertices];b=box(pts);parts.append({'name':o.name,'worldBounds':b,'location':vv(o.location),'scale':vv(o.scale),'rotation':vv(o.rotation_euler),'vertices':len(me.vertices)});allpts+=pts;eo.to_mesh_clear()
 return {'clip':clip,'direction':d,'frame':frame,'visibleCount':len(parts),'bounds':box(allpts),'projectedBounds':[[min(project(p)[i] for p in allpts) for i in range(2)],[max(project(p)[i] for p in allpts) for i in range(2)]],'parts':parts}

apply('dock-ready',1,'S');dg=bpy.context.evaluated_depsgraph_get();contacts=[]
for o in meshes:
 if o.hide_render or not any(x in o.name for x in ['skid','strut','harpoon','collector','headlight']):continue
 eo=o.evaluated_get(dg);me=eo.to_mesh();pts=[eo.matrix_world@v.co for v in me.vertices];faces=[]
 for poly in me.polygons:
  n=(eo.matrix_world.to_3x3().inverted().transposed()@poly.normal).normalized();pp=[pts[i] for i in poly.vertices]
  if n.z<-.99:faces.append({'normal':vv(n),'bounds':box(pp),'vertices':[vv(v) for v in pp]})
 contacts.append({'name':o.name,'bounds':box(pts),'lowerHorizontalFaces':faces});eo.to_mesh_clear()
apply('upgraded-dock-ready',1,'S');up=[]
for o in meshes:
 if o.hide_render or not any(x in o.name for x in ['harpoon','collector','armor']):continue
 eo=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=eo.to_mesh();up.append({'name':o.name,'bounds':box([eo.matrix_world@v.co for v in me.vertices]),'location':vv(o.location),'rotation':vv(o.rotation_euler)});eo.to_mesh_clear()
(out/'native-contact-and-sockets.json').write_text(json.dumps({'sourceDockRoot':[-.7,-.42,.23],'sourceDeckBroadZ':.22,'sourceNominalSkidBottomZ':.045,'sourceSkidBottomRangeLocal':[.027,.063],'actualContactSurfaces':contacts,'declaredSockets':rig['sockets'],'declaredSocketObjects':[],'requirementsOnlyNames':['cable','headlight'],'integratedUpgradeAttachmentGeometry':up},indent=2))
component=[]
for aid,colname in [('sub-hull-panels','S33_PROP_hull_panel.001'),('sub-harpoon-mount','S33_PROP_harpoon_mount.001'),('sub-collector-inlet','S33_PROP_collector_inlet.001')]:
 col=bpy.data.collections[colname];sc.collection.children.link(col);col.hide_render=False;col.hide_viewport=False;crig=json.loads((res/(aid+'-rig.json')).read_text());co=list(col.all_objects);rt=bpy.data.objects[crig['groundRootObject']]
 for clip,info in crig['clips'].items():
  for o in co:
   if o.animation_data:o.animation_data.action=None
  for t in info['actions']:
   obj=bpy.data.objects[t['ownerName']];obj.animation_data_create();a=bpy.data.actions[t['action']];obj.animation_data.action=a;obj.animation_data.action_slot=next(s for s in a.slots if s.identifier==t['slotIdentifier'])
  for d in ['N','E','S','W']:
   rt.rotation_euler.z={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[d]
   for frame in range(1,info['frames']+1):
    sc.frame_set(frame);bpy.context.view_layer.update();ps=[];pts=[]
    for o in co:
     if o.type!='MESH' or o.hide_render:continue
     eo=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=eo.to_mesh();pp=[eo.matrix_world@v.co for v in me.vertices];pts+=pp;ps.append({'name':o.name,'location':vv(o.location),'rotation':vv(o.rotation_euler),'scale':vv(o.scale),'bounds':box(pp)});eo.to_mesh_clear()
    component.append({'asset':aid,'clip':clip,'frame':frame,'direction':d,'loop':info['loop'],'static':info['static'],'bounds':box(pts),'parts':ps})
(out/'component-native-phases.json').write_text(json.dumps(component,separators=(',',':')))
print('CONTACT AND COMPONENTS',len(component),flush=True)
