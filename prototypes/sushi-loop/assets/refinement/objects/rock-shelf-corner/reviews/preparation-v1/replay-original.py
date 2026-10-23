import bpy,sys,math,json,importlib.util,pathlib,hashlib
from mathutils import Vector
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent;E=P/'evidence';E.mkdir(exist_ok=True)
s=next(sc for sc in bpy.data.scenes if sc.get('source')=='native_actions.py' and sc.get('issue')==33)
bpy.context.window.scene=s;bpy.context.window.view_layer=s.view_layers[0]
c=bpy.data.collections['S33_PROP_rock-shelf-corner.001'];root=bpy.data.objects['rock-shelf-corner__root.001']
incidental={'scene':s.name,'camera':s.camera.name,'worldMatrix':[list(r) for r in s.camera.matrix_world],'frame':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y]}
def layer(n):
 n.exclude=False
 for q in n.children:layer(q)
layer(s.view_layers[0].layer_collection)
for q in s.collection.children:q.hide_viewport=q!=c;q.hide_render=q!=c
for q in s.view_layers[0].layer_collection.children:q.exclude=q.collection!=c
c.hide_viewport=False;c.hide_render=False
s.frame_set(1);root.rotation_euler=(0,0,0);s.view_layers[0].update();dg=bpy.context.evaluated_depsgraph_get()
pts=[];records=[];ground=[]
for o in c.all_objects:
 r={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixWorld':[list(v) for v in o.matrix_world],'objectAnimation':bool(o.animation_data),'shapeKeys':bool(o.type=='MESH' and o.data.shape_keys)}
 if o.type=='MESH':
  eo=o.evaluated_get(dg);m=eo.to_mesh();vs=[eo.matrix_world@v.co for v in m.vertices];pts+=vs;m.calc_loop_triangles();r['bounds']=[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]];r['vertices']=[list(v) for v in vs];r['polygons']=[{'vertices':list(p.vertices),'normal':list(p.normal),'material':p.material_index,'smooth':p.use_smooth} for p in m.polygons];r['materialAnimation']=[{'name':m.name,'material':bool(m.animation_data),'nodes':bool(m.node_tree and m.node_tree.animation_data)} for m in o.data.materials if m]
  for t in m.loop_triangles:
   vv=[vs[i] for i in t.vertices]
   if all(abs(v.z)<1e-7 for v in vv):ground.append({'object':o.name,'polygon':t.polygon_index,'vertices':[list(v) for v in vv]})
  eo.to_mesh_clear()
 records.append(r)
(P/'measured-original.json').write_text(json.dumps({'incidentalSavedCamera':incidental,'scene':s.name,'collection':c.name,'root':root.name,'rootMatrix':[list(v) for v in root.matrix_world],'bounds':[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]],'objects':records,'finiteGroundTriangles':ground,'animationActions':[]},indent=2)+'\n')
spec=importlib.util.spec_from_file_location('corner_private_runtime',P/'resources/capture_runtime.py');runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime);runtime.scene=lambda:s
s.eevee.taa_render_samples=32;s.render.filter_size=1.5;s.render.image_settings.compression=15
ledger={}
for d,a in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 root.rotation_euler.z=a;s.view_layers[0].update();record=runtime.configure_camera('square-top-front-oblique',(192,352),(96,248),4)
 s.eevee.taa_render_samples=32;s.render.filter_size=1.5;s.render.image_settings.compression=15
 s.render.filepath=str(E/f'original-{d}-4x.png');bpy.ops.render.render(write_still=True,scene=s.name)
 record.update(direction=d,rootMatrix=[list(v) for v in root.matrix_world],frameCurrent=s.frame_current,filterSize=s.render.filter_size,samples=s.eevee.taa_render_samples)
 ledger[d]=record
(E/'historical-replay-camera.json').write_text(json.dumps(ledger,indent=2)+'\n')
print('BOUNDED ALL4 ORIGINAL REPLAY COMPLETE')
