import bpy,bmesh,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
base=Path(__file__).resolve().parents[2];res=base/'resources';out=base/'evidence';out.mkdir(exist_ok=True)
record=json.loads((res/'resource-inputs/source-camera.json').read_text())
sc=bpy.context.scene;coll=bpy.data.collections['S33_PROP_rock-half-width.001'];root=bpy.data.objects['rock-half-width__root.001'];mesh=next(o for o in coll.all_objects if o.type=='MESH')
def rows(m):return [list(r) for r in m]
def serial(v):
 try:return list(v)
 except:return str(v)
def write(n,v): (out/n).write_text(json.dumps(v,indent=2,default=serial)+'\n')
def ani(id):
 ad=getattr(id,'animation_data',None)
 return {'name':id.name,'type':type(id).__name__,'action':ad.action.name if ad and ad.action else None,'drivers':[{ 'path':f.data_path,'arrayIndex':f.array_index,'expression':f.driver.expression} for f in ad.drivers] if ad else [],'nla':[t.name for t in ad.nla_tracks] if ad else []}
def enable(l):
 l.exclude=False;l.hide_viewport=False
 for c in l.children:enable(c)
for v in sc.view_layers:enable(v.layer_collection)
for c in sc.collection.children:c.hide_render=c!=coll;c.hide_viewport=c!=coll
coll.hide_render=False;coll.hide_viewport=False
for o in coll.all_objects:o.hide_set(False);o.hide_render=False;o.hide_viewport=False
for o in sc.objects:
 if o.type in {'LIGHT','CAMERA'}:o.hide_set(False);o.hide_render=False;o.hide_viewport=False
sc.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
ev=mesh.evaluated_get(dg);em=ev.to_mesh();verts=[ev.matrix_world@v.co for v in em.vertices]
sections={}
for x in [-.5,-.35,-.1,.1,.35,.5]:
 sections[str(x)]=[list(v) for v in verts if abs(v.x-x)<1e-5]
contactFaces=[]
for p in em.polygons:
 vv=[verts[i] for i in p.vertices]
 if all(abs(v.z)<1e-6 for v in vv):contactFaces.append({'vertices':[list(v) for v in vv],'area':p.area,'normal':list(p.normal)})
bm=bmesh.new();bm.from_mesh(em)
geometry={'object':mesh.name,'evaluated':True,'viewLayerEnabled':True,'rootMatrix':rows(root.matrix_world),'min':[min(v[i] for v in verts) for i in range(3)],'max':[max(v[i] for v in verts) for i in range(3)],'vertices':[list(v) for v in verts],'polygons':[{'indices':list(p.vertices),'normal':list(p.normal),'smooth':p.use_smooth,'materialIndex':p.material_index,'area':p.area} for p in em.polygons],'sections':sections,'groundContactFaces':contactFaces,'groundContactArea':sum(p['area'] for p in contactFaces),'topology':{'vertices':len(em.vertices),'edges':len(em.edges),'polygons':len(em.polygons),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'wireEdges':sum(e.is_wire for e in bm.edges),'signedVolume':bm.calc_volume(signed=True),'uvLayers':[u.name for u in em.uv_layers],'colorAttributes':[a.name for a in em.color_attributes],'shapeKeys':mesh.data.shape_keys.name if mesh.data.shape_keys else None,'modifiers':[{'name':m.name,'type':m.type} for m in mesh.modifiers]}}
bm.free();ev.to_mesh_clear()
ids=[sc,root,mesh,mesh.data];nodeSeen=set();nodes=[];images=[]
def tree(t):
 if not t or t.name in nodeSeen:return
 nodeSeen.add(t.name);ids.append(t)
 nr=[]
 for n in t.nodes:
  d={'name':n.name,'type':n.bl_idname,'inputs':{s.name:serial(s.default_value) if not isinstance(s.default_value,(str,int,float,bool)) else s.default_value for s in n.inputs if hasattr(s,'default_value')}}
  if getattr(n,'image',None):
   im=n.image;images.append({'name':im.name,'filepath':im.filepath,'source':im.source,'packed':bool(im.packed_file)});ids.append(im)
  if getattr(n,'node_tree',None):d['nodeGroup']=n.node_tree.name;tree(n.node_tree)
  nr.append(d)
 nodes.append({'tree':t.name,'nodes':nr,'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in t.links]})
materials=[]
for m in mesh.data.materials:
 ids.append(m);tree(m.node_tree);materials.append({'name':m.name,'diffuseColor':list(m.diffuse_color),'useNodes':m.use_nodes,'users':m.users,'objectOwners':[o.name for o in bpy.data.objects if any(s.material==m for s in o.material_slots)]})
if sc.world:ids.append(sc.world);tree(sc.world.node_tree)
try:tree(sc.compositing_node_group)
except:tree(getattr(sc,'node_tree',None))
lights=[]
for o in sc.objects:
 if o.type=='LIGHT':
  ids.extend([o,o.data]);tree(o.data.node_tree)
  lights.append({'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'size':getattr(o.data,'size',None),'matrixWorld':rows(o.matrix_world),'hideRender':o.hide_render})
savedCam=sc.camera
ids.extend([savedCam,savedCam.data])
saved={'name':savedCam.name,'matrixWorld':rows(savedCam.matrix_world),'orthoScale':savedCam.data.ortho_scale,'shift':[savedCam.data.shift_x,savedCam.data.shift_y],'resolution':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'engine':sc.render.engine,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'filmTransparent':sc.render.film_transparent}
# Registered camera replay. Do not use the saved unrelated active camera as evidence.
camdata=bpy.data.cameras.new('Judge registered source replay');cam=bpy.data.objects.new('Judge registered source replay',camdata);sc.collection.objects.link(cam);sc.camera=cam
cam.matrix_world=Matrix(record['camera']['worldMatrix']);camdata.type='ORTHO';camdata.sensor_fit='HORIZONTAL';camdata.ortho_scale=192/128;camdata.shift_x=0;camdata.shift_y=0
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=record['camera']['pixelAspect'][0];sc.render.pixel_aspect_y=record['camera']['pixelAspect'][1];sc.render.resolution_x=768;sc.render.resolution_y=1408;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.dither_intensity=0
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
sc.render.fps=12
bpy.context.view_layer.update()
def px(p):
 v=world_to_camera_view(sc,cam,Vector(p));return [v.x*sc.render.resolution_x,(1-v.y)*sc.render.resolution_y]
def configure(frame,anchor,scale):
 sc.render.resolution_x=frame[0]*scale;sc.render.resolution_y=frame[1]*scale;camdata.ortho_scale=frame[0]/128;camdata.shift_x=0;camdata.shift_y=0;bpy.context.view_layer.update()
 b=px((0,0,0));camdata.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-b[1];camdata.shift_y=(anchor[1]*scale-b[1])/dy;camdata.shift_x=(frame[0]/2-anchor[0])/frame[0];bpy.context.view_layer.update()
configure([192,352],[96,248],4)
cal={k:px(p) for k,p in {'root':[0,0,0],'x':[1,0,0],'depth':[0,-1,0],'height':[0,0,1]}.items()}
replay={'matrixWorld':rows(cam.matrix_world),'projectionMatrix':rows(cam.calc_matrix_camera(dg,x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)),'orthoScale':camdata.ortho_scale,'shift':[camdata.shift_x,camdata.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'resolution':[sc.render.resolution_x,sc.render.resolution_y],'calibration':cal}
channels=[ani(i) for i in ids]
write('native-measurement.json',{'blender':bpy.app.version_string,'source':str(res/'original-library.blend'),'geometry':geometry,'materials':materials,'shaderTrees':nodes,'reachableImages':images,'linkedLibraries':[l.filepath for l in bpy.data.libraries],'lights':lights,'temporalChannels':channels,'relevantTemporalChannelsPresent':any(a['action'] or a['drivers'] or a['nla'] for a in channels),'savedUnrelatedCamera':saved,'registeredReplayCamera':replay})
ledger=[]
for d,a in [('S',0),('E',90),('N',180),('W',-90)]:
 root.rotation_euler.z=math.radians(a);sc.frame_set(1);bpy.context.view_layer.update();f=out/f'source-native-{d}.png';sc.render.filepath=str(f);bpy.ops.render.render(write_still=True)
 ledger.append({'path':f.name,'direction':d,'frame':1,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'actualRootMatrix':rows(root.matrix_world),'nativeFrame':[768,1408],'logicalFrame':[192,352],'logicalRoot':[96,248],'captureScale':4})
# Source-only technical join fixtures: exact native original meshes translated one cell.
root.rotation_euler.z=0;bpy.context.view_layer.update()
copies=[]
for dx in [-1,1]:
 ob=mesh.copy();ob.data=mesh.data;ob.name='judge source join '+str(dx);coll.objects.link(ob);ob.parent=None;ob.matrix_world=mesh.matrix_world.copy();ob.location.x+=dx;copies.append(ob)
for d,a in [('S',0),('E',90)]:
 configure([448,576],[224,420],4);rot=Matrix.Rotation(math.radians(a),4,'Z');root.rotation_euler.z=math.radians(a)
 for ob,dx in zip(copies,[-1,1]):ob.matrix_world=rot@Matrix.Translation((dx,0,0))
 bpy.context.view_layer.update();f=out/f'source-native-join-{d}.png';sc.render.filepath=str(f);bpy.ops.render.render(write_still=True)
 ledger.append({'path':f.name,'direction':d,'type':'source-only exact original mesh translated ±1 then facing rotated','rootMatrices':[rows(root.matrix_world)]+[rows(o.matrix_world) for o in copies],'nativeFrame':[1792,2304],'logicalFrame':[448,576],'logicalRoot':[224,420],'captureScale':4})
write('source-render-ledger.json',{'method':'Source-only evidence, no candidate modification or saved model. Exact original core geometry/material used. Registered camera matrix/projection density/root replay; expanded canvas only for joins.','renders':ledger})
