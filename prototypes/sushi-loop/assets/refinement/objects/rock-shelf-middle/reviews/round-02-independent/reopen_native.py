import bpy,sys,json,math,pathlib,hashlib
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
B=pathlib.Path(__file__).parent;E=B/'evidence';s=bpy.context.scene;root=bpy.data.objects['rock-shelf-middle__root'];cam=s.camera
assert hashlib.sha256((B/'resources/source.blend').read_bytes()).hexdigest()=='2c0bf0dcbc9c4a2e23f96a0cacd30360cb3be271f4cb465c7b49690970daacc1'
root.rotation_euler=(0,0,0);s.frame_set(1)
for c in s.collection.children:c.hide_viewport=False
for l in s.view_layers[0].layer_collection.children:l.exclude=False;l.hide_viewport=False
for o in s.objects:o.hide_set(False);o.hide_viewport=False
s.view_layers[0].update();dep=bpy.context.evaluated_depsgraph_get();meshes=[o for o in s.objects if o.type=='MESH'];core=next(o for o in meshes if 'sculpted_core' in o.name)
def scalar(v):
 try:return list(v)
 except:return v
materials=[]
for m in bpy.data.materials:
 materials.append({'name':m.name,'users':m.users,'linked':bool(m.library),'action':m.animation_data.action.name if m.animation_data and m.animation_data.action else None,'nodeAction':m.node_tree.animation_data.action.name if m.node_tree and m.node_tree.animation_data and m.node_tree.animation_data.action else None,'nodes':[{'name':n.name,'type':n.bl_idname,'attribute':getattr(n,'attribute_name',None),'inputs':[(i.name,scalar(i.default_value)) for i in n.inputs if hasattr(i,'default_value')]} for n in m.node_tree.nodes] if m.node_tree else [],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links] if m.node_tree else []})
objects=[];worldverts=[]
for o in meshes:
 ev=o.evaluated_get(dep);me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];worldverts+=vs
 objects.append({'name':o.name,'parent':o.parent.name if o.parent else None,'vertices':len(vs),'polygons':len(me.polygons),'bounds':[[min(v[k] for v in vs) for k in range(3)],[max(v[k] for v in vs) for k in range(3)]],'bottomArea':sum(p.area for p in me.polygons if all(abs(vs[i].z)<1e-6 for i in p.vertices)),'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None,'modifiers':[m.type for m in o.modifiers],'shapeKeys':bool(o.data.shape_keys),'materialSlots':[m.name if m else None for m in o.data.materials],'geometryLibrary':bool(o.data.library)})
 ev.to_mesh_clear()
ev=core.evaluated_get(dep);me=ev.to_mesh();me.calc_loop_triangles();vs=[ev.matrix_world@v.co for v in me.vertices];tris=list(me.loop_triangles);tree=BVHTree.FromPolygons(vs,[tuple(t.vertices) for t in tris],all_triangles=True);al=me.color_attributes['rock_shelf_albedo'];caps=[]
for p in me.polygons:
 if all(abs(abs(vs[i].x)-.5)<1e-6 for i in p.vertices) and abs(p.normal.x)>.999:
  caps.append({'vertices':[list(vs[i]) for i in p.vertices],'normal':list(p.normal),'smooth':p.use_smooth,'materialIndex':p.material_index})
def sample(x,surface,t):
 if surface=='top':origin=Vector((x,t,2));direction=Vector((0,0,-1))
 else:sign=-1 if surface=='front' else 1;origin=Vector((x,sign*2,t));direction=Vector((0,-sign,0))
 hit,normal,i,dist=tree.ray_cast(origin,direction,4)
 if hit is None:return None
 tr=tris[i];p0,p1,p2=[vs[v] for v in tr.vertices];u=p1-p0;v=p2-p0;q=hit-p0;den=u.dot(u)*v.dot(v)-u.dot(v)**2;b=(v.dot(v)*q.dot(u)-u.dot(v)*q.dot(v))/den;c=(u.dot(u)*q.dot(v)-u.dot(v)*q.dot(u))/den;a=1-b-c;weights=[a,b,c]
 n=sum((ev.matrix_world.to_3x3()@me.corner_normals[j].vector*w for j,w in zip(tr.loops,weights)),Vector()).normalized()
 colors=[al.data[j if al.domain=='CORNER' else vi].color for j,vi in zip(tr.loops,tr.vertices)];color=[sum(weights[j]*colors[j][k] for j in range(3)) for k in range(4)]
 return {'point':list(hit),'normal':list(n),'albedo':color,'material':core.data.materials[me.polygons[tr.polygon_index].material_index].name}
samples=[];maxres={'YZ':0,'normal':0,'albedo':0}
for inset in [0,.0001,.005,.02,.06]:
 for surface,ts in [('top',[-.35,-.18,0,.18,.35]),('front',[.02,.12,.24,.32,.40]),('back',[.02,.12,.24,.32,.40])]:
  for t in ts:
   a=sample(-.5+inset,surface,t);b=sample(.5-inset,surface,t)
   if a is None or b is None:delta=None
   else:
    delta={'YZ':max(abs(a['point'][k]-b['point'][k]) for k in [1,2]),'normal':max(abs(a['normal'][k]-b['normal'][k]) for k in range(3)),'albedo':max(abs(a['albedo'][k]-b['albedo'][k]) for k in range(4))}
    for k in maxres:maxres[k]=max(maxres[k],delta[k])
   samples.append({'inset':inset,'surface':surface,'transverse':t,'W':a,'E':b,'delta':delta})
ev.to_mesh_clear()
def camera_info():
 dep=bpy.context.evaluated_depsgraph_get()
 def px(p):v=world_to_camera_view(s,cam,Vector(p));return Vector((v.x*s.render.resolution_x,(1-v.y)*s.render.resolution_y))
 p=px((0,0,0));return {'worldMatrix':[list(r) for r in cam.matrix_world],'type':cam.data.type,'orthoScale':cam.data.ortho_scale,'sensorFit':cam.data.sensor_fit,'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'frame':[s.render.resolution_x,s.render.resolution_y],'shift':[cam.data.shift_x,cam.data.shift_y],'calibration':{'root':list(p),'unitX':list(px((1,0,0))-p),'unitDepth':list(px((0,-1,0))-p),'unitHeight':list(px((0,0,1))-p)}}
settings={'engine':s.render.engine,'samples':s.eevee.taa_render_samples,'filterSize':s.render.filter_size,'filmTransparent':s.render.film_transparent,'image':{'format':s.render.image_settings.file_format,'colorMode':s.render.image_settings.color_mode,'depth':s.render.image_settings.color_depth},'colorManagement':{'view':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma},'dither':s.render.dither_intensity,'frameStart':s.frame_start,'frameEnd':s.frame_end,'fps':s.render.fps}
lights=[{'name':o.name,'type':o.data.type,'position':list(o.location),'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color),'rotation':list(o.rotation_euler)} for o in s.objects if o.type=='LIGHT']
record={'sourceSHA256':hashlib.sha256((B/'resources/source.blend').read_bytes()).hexdigest(),'scene':s.name,'blender':bpy.app.version_string,'objects':objects,'allBounds':[[min(v[k] for v in worldverts) for k in range(3)],[max(v[k] for v in worldverts) for k in range(3)]],'rootMatrix':[list(r) for r in root.matrix_world],'caps':caps,'endpointBandSamples':samples,'endpointMaxResidual':maxres,'materials':materials,'lights':lights,'camera':camera_info(),'settings':settings,'libraries':[l.filepath for l in bpy.data.libraries],'imageResources':[{'name':i.name,'filepath':i.filepath,'source':i.source,'packed':bool(i.packed_file)} for i in bpy.data.images],'armatures':[o.name for o in s.objects if o.type=='ARMATURE'],'dataActions':[a.name for a in bpy.data.actions]}
(E/'native-inspection.json').write_text(json.dumps(record,indent=2)+'\n')
views={};angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
for d,angle in angles.items():
 root.rotation_euler.z=angle;s.frame_set(1);s.view_layers[0].update();views[d]={'actualRootMatrix':[list(r) for r in root.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world],'rotationZ':root.rotation_euler.z,'camera':camera_info()};s.render.filepath=str(E/f'reopened-{d}-4x.png');bpy.ops.render.render(write_still=True)
# Duplicate original meshes in memory only; shared frozen material resources, no construction edits or blend save.
root.rotation_euler.z=0;s.view_layers[0].update();assembly=bpy.data.collections.new('judge_only_strip');s.collection.children.link(assembly);ar=bpy.data.objects.new('judge_only_strip_root',None);assembly.objects.link(ar)
for k in [-1,0,1]:
 for original in meshes:
  o=original.copy();o.data=original.data;o.parent=ar;assembly.objects.link(o);o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=original.matrix_world.copy();o.location.x+=k
for o in meshes:o.hide_render=True
s.render.resolution_x=448*4;s.render.resolution_y=608*4;cam.data.ortho_scale=448/128;cam.data.shift_x=0;cam.data.shift_y=0;s.view_layers[0].update()
def py():v=world_to_camera_view(s,cam,Vector((0,0,0)));return (1-v.y)*s.render.resolution_y
base=py();cam.data.shift_y=1;s.view_layers[0].update();delta=py()-base;cam.data.shift_y=(376*4-base)/delta;s.view_layers[0].update()
for d,angle in angles.items():
 ar.rotation_euler.z=angle;s.view_layers[0].update();views[d]['stripCamera']=camera_info();s.render.filepath=str(E/f'reopened-strip-{d}-4x.png');bpy.ops.render.render(write_still=True)
(E/'reopen-pose-ledger.json').write_text(json.dumps(views,indent=2)+'\n');print('INDEPENDENT REOPEN COMPLETE')
