import sys
sys.dont_write_bytecode=True
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];E=B/'evidence';R=B/'resources';angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def val(x):
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 try:return list(x)
 except:return str(x)
def graph(nt):
 if nt is None:return None
 nodes=[]
 for n in nt.nodes:
  r={'name':n.name,'type':n.type,'inputs':[{ 'name':i.name,'identifier':i.identifier,'value':val(i.default_value)} for i in n.inputs if hasattr(i,'default_value')]}
  for k in ['operation','blend_type','attribute_name','interpolation_type']:
   if hasattr(n,k):r[k]=getattr(n,k)
  if hasattr(n,'color_ramp'):r['ramp']={'interpolation':n.color_ramp.interpolation,'elements':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]}
  nodes.append(r)
 return {'nodes':nodes,'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in nt.links],'animation':bool(nt.animation_data)}
def activate():
 sc=bpy.context.scene
 def go(l):
  l.exclude=False;l.hide_viewport=False
  for x in l.children:go(x)
 go(sc.view_layers[0].layer_collection)
 for c in bpy.data.collections:c.hide_viewport=False
 sc.view_layers[0].update();return sc
def audit(path,tag):
 bpy.ops.wm.open_mainfile(filepath=str(path));sc=activate();dg=bpy.context.evaluated_depsgraph_get();gs=[]
 for o in sc.objects:
  if o.type!='MESH' or o.hide_render:continue
  ob=o.evaluated_get(dg);m=ob.to_mesh();m.calc_loop_triangles();v=[list(ob.matrix_world@x.co) for x in m.vertices];N=ob.matrix_world.to_3x3().inverted().transposed();d={'name':o.name,'vertices':v,'faces':[list(p.vertices) for p in m.polygons],'materials':[x.name for x in m.materials],'bounds':[[min(x[k] for x in v),max(x[k] for x in v)] for k in range(3)],'meshUsers':o.data.users,'animation':bool(o.animation_data or o.data.animation_data),'shapeKeys':bool(o.data.shape_keys),'constraints':[x.type for x in o.constraints],'modifiers':[x.type for x in o.modifiers],'attributes':[{'name':x.name,'domain':x.domain,'type':x.data_type} for x in m.attributes]}
  if 'continuous_core' in o.name:
   d['triangles']=[{'vertices':[v[i] for i in t.vertices],'vertexIds':list(t.vertices),'normal':list((N@t.normal).normalized()),'cornerNormals':[list(N@m.corner_normals[i].vector) for i in t.loops],'material':m.materials[m.polygons[t.polygon_index].material_index].name,'smooth':m.polygons[t.polygon_index].use_smooth} for t in m.loop_triangles]
  gs.append(d);ob.to_mesh_clear()
 rt=next(o for o in sc.objects if o.type=='EMPTY' and '__root' in o.name);cam=sc.camera;ee=getattr(sc,'eevee',None)
 report={'sourceSHA256':sha(path),'source':str(path),'scene':sc.name,'root':rt.name,'rootProperties':{k:val(rt[k]) for k in rt.keys()},'rootMatrix':[list(x) for x in rt.matrix_world],'geometry':gs,'materials':{m.name:graph(m.node_tree) for m in bpy.data.materials},'world':graph(sc.world.node_tree),'lights':[{'name':o.name,'position':list(o.location),'matrix':[list(x) for x in o.matrix_world],'energy':o.data.energy,'size':o.data.size,'shape':o.data.shape,'color':list(o.data.color)} for o in sc.objects if o.type=='LIGHT' and o.data.energy>0],'camera':{'matrix':[list(x) for x in cam.matrix_world],'type':cam.data.type,'orthoScale':cam.data.ortho_scale,'shiftX':cam.data.shift_x,'shiftY':cam.data.shift_y},'render':{'resolution':[sc.render.resolution_x,sc.render.resolution_y],'percentage':sc.render.resolution_percentage,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'filter':sc.render.filter_size,'engine':sc.render.engine,'samples':getattr(ee,'taa_render_samples',None),'fps':sc.render.fps,'transparent':sc.render.film_transparent,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'compositing':sc.render.use_compositing},'actions':[x.name for x in bpy.data.actions],'images':[x.name for x in bpy.data.images if x.source!='GENERATED'],'libraries':[x.filepath for x in bpy.data.libraries]}
 (E/(tag+'-audit.json')).write_text(json.dumps(report,indent=2)+'\n');return sc,rt
# Audit actual saved canonical before reopening candidate; no construction source imported.
audit(R/'canonical-middle02.blend','canonical')
sc,root=audit(R/'candidate-round01.blend','candidate');cam=sc.camera;sourceObjects=list(sc.objects);baseCol=next(c for c in sc.collection.children if root in list(c.all_objects));records={}
for d,ang in angles.items():
 root.rotation_euler.z=ang;sc.view_layers[0].update();sc.render.filepath=str(E/('hero-'+d+'.png'));bpy.ops.render.render(write_still=True)
 p=world_to_camera_view(sc,cam,Vector((0,0,0)));records[d]={'render':'hero-'+d+'.png','sha256':sha(E/('hero-'+d+'.png')),'rootPixels':[p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y],'actualRootMatrix':[list(x) for x in root.matrix_world]}
# Append exact native companions into this background process, not into any saved model.
def append(path,prefix):
 with bpy.data.libraries.load(str(path),link=False) as (frm,to):to.collections=list(frm.collections)
 cs=[c for c in to.collections if any(o.type=='MESH' for o in c.all_objects)]
 if len(cs)!=1:raise RuntimeError((path,[(c.name,len(c.all_objects)) for c in cs]))
 c=cs[0];sc.collection.children.link(c);r=next(o for o in c.all_objects if o.type=='EMPTY' and '__root' in o.name);return c,r
middle=append(R/'canonical-middle02.blend','middle');edge=append(R/'approved-edge01.blend','edge');corner=append(R/'approved-corner01.blend','corner')
# One additional middle instance is an exact in-memory hierarchy copy for the authored L control.
c2=bpy.data.collections.new('Judge second canonical middle');sc.collection.children.link(c2);mp={}
for o in middle[0].objects:n=o.copy();c2.objects.link(n);mp[o]=n
for o,n in mp.items():
 if o.parent in mp:n.parent=mp[o.parent]
mid2=(c2,mp[middle[1]])
allparts=[(baseCol,root),middle,edge,corner,mid2]
def show(parts):
 for col,rt in allparts:
  col.hide_render=(col,rt) not in parts;col.hide_viewport=False
  for o in col.all_objects:o.hide_viewport=False;o.hide_set(False)
 for layer in sc.view_layers[0].layer_collection.children:layer.exclude=False
 sc.view_layers[0].update()
# Same fixed registered projection, extended canvas only.
sc.render.resolution_x=1664;sc.render.resolution_y=1984;cam.data.ortho_scale=832/128;cam.data.shift_x=0;cam.data.shift_y=0;sc.view_layers[0].update()
def px(v):
 q=world_to_camera_view(sc,cam,Vector(v));return Vector((q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y))
b=px((0,0,0));cam.data.shift_y=1;sc.view_layers[0].update();dy=px((0,0,0)).y-b.y;cam.data.shift_y=(1120-b.y)/dy;sc.view_layers[0].update()
contexts={}
for name in ['direct-canonical-to-end','full-family-L']:
 parts=[(baseCol,root),middle] if name.startswith('direct') else [(baseCol,root),middle,edge,corner,mid2];show(parts)
 specs=[(root,(0,0),0),(middle[1],(-1,0),0)] if name.startswith('direct') else [(root,(0,0),0),(middle[1],(-1,0),0),(corner[1],(-2,0),-math.pi/2),(edge[1],(-2,1),-math.pi/2),(mid2[1],(-2,2),-math.pi/2)]
 for d,ang in angles.items():
  co=math.cos(ang);si=math.sin(ang)
  for rt,(x,y),local in specs:rt.rotation_euler.z=local+ang;rt.location=(co*x-si*y,si*x+co*y,0)
  sc.view_layers[0].update();p=E/(name+'-'+d+'.png');sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
  contexts[name+'-'+d]={'render':p.name,'sha256':sha(p),'actualRoots':[{'name':rt.name,'matrix':[list(x) for x in rt.matrix_world]} for rt,xy,local in specs],'rootPixels':list(px((0,0,0)))}
(E/'reopened-replay-ledger.json').write_text(json.dumps({'heroes':records,'contexts':contexts,'blender':bpy.app.version_string,'noBlendSaved':True,'noConstructionRecipeExecuted':True,'scope':'Independent actual saved-source replay controls with native canonical companions; no candidate edits.'},indent=2)+'\n')
print('JUDGE_NATIVE_REPLAY_COMPLETE')
