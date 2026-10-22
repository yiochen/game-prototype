import bpy,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[2];R=P/'resources';O=P/'baseline';O.mkdir(exist_ok=True)
write=lambda p,x:Path(p).write_text(json.dumps(x,indent=2,default=str)+'\n')
vec=lambda v:[float(x) for x in v]
mat=lambda m:[vec(row) for row in m]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def enable():
 def en(lc):
  lc.exclude=False;lc.hide_viewport=False
  for c in lc.children:en(c)
 en(bpy.context.view_layer.layer_collection)
 for c in bpy.data.collections:c.hide_viewport=False
 for o in bpy.context.scene.objects:o.hide_set(False);o.hide_viewport=False
 bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
def graph(nt):
 if not nt:return None
 return {'nodes':[{'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'attribute':getattr(n,'attribute_name',None),'vectorType':getattr(n,'vector_type',None),'convertFrom':getattr(n,'convert_from',None),'convertTo':getattr(n,'convert_to',None),'inputs':{s.name:vec(s.default_value) if hasattr(s.default_value,'__len__') and not isinstance(s.default_value,str) else s.default_value for s in n.inputs if hasattr(s,'default_value') and s.type not in {'SHADER','CUSTOM'}}} for n in nt.nodes],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in nt.links]}
def hull(ps):
 ps=sorted(set(tuple(p) for p in ps))
 cross=lambda o,a,b:(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 halves=[]
 for arr in [ps,ps[::-1]]:
  h=[]
  for p in arr:
   while len(h)>=2 and cross(h[-2],h[-1],p)<=1e-12:h.pop()
   h.append(p)
  halves.append(h[:-1])
 return halves[0]+halves[1]
def audit(col,label):
 enable();dg=bpy.context.evaluated_depsgraph_get();roots=[o for o in col.all_objects if o.type=='EMPTY' and o.parent is None];root=roots[0];inv=root.matrix_world.inverted();out={'label':label,'collection':col.name,'root':root.name,'rootMatrix':mat(root.matrix_world),'properties':dict(root.items()),'objects':[],'materials':{},'resources':{'libraries':[{'path':l.filepath} for l in bpy.data.libraries],'images':[{'name':im.name,'path':im.filepath,'packed':bool(im.packed_file)} for im in bpy.data.images if im.source=='FILE']}}
 rawall=[];evalall=[];support=[]
 for ob in col.all_objects:
  ent={'name':ob.name,'type':ob.type,'parent':ob.parent.name if ob.parent else None,'modifiers':[{'name':m.name,'type':m.type,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)} for m in ob.modifiers],'animation':bool(ob.animation_data),'constraints':[c.type for c in ob.constraints]}
  if ob.type=='MESH':
   raw=[inv@ob.matrix_world@v.co for v in ob.data.vertices];rawall+=raw
   eo=ob.evaluated_get(dg);me=eo.to_mesh();ev=[inv@eo.matrix_world@v.co for v in me.vertices];evalall+=ev
   ent['rawBounds']={'min':[min(v[i] for v in raw) for i in range(3)],'max':[max(v[i] for v in raw) for i in range(3)]};ent['evaluatedBounds']={'min':[min(v[i] for v in ev) for i in range(3)],'max':[max(v[i] for v in ev) for i in range(3)]}
   ent['rawVertices']=[vec(v) for v in raw];ent['materials']=[m.name for m in ob.data.materials];ent['meshAttributes']=[{'name':a.name,'type':a.data_type,'domain':a.domain} for a in me.attributes]
   faces=[];caps=[]
   for poly in me.polygons:
    vs=[ev[i] for i in poly.vertices];zz=[v.z for v in vs]
    if max(abs(v.z-.04) for v in vs)<1e-6:
     xy=[vec(v)[:2] for v in vs];area=abs(sum(xy[i][0]*xy[(i+1)%len(xy)][1]-xy[(i+1)%len(xy)][0]*xy[i][1] for i in range(len(xy)))/2)
     support.append({'object':ob.name,'xyPolygon':xy,'z':sum(zz)/len(zz),'area':area,'normal':vec(poly.normal)})
    if min(v.x for v in vs)<-.419999 and max(v.x for v in vs)<-.41999:
     fields={'vertices':[vec(v) for v in vs],'polygonNormal':vec(poly.normal),'material':me.materials[poly.material_index].name,'cornerNormals':[vec(me.corner_normals[i].vector) for i in poly.loop_indices]}
     a=me.attributes.get('CanonicalNormal')
     if a:fields['shaderCanonicalNormal']=[vec(a.data[i].vector) for i in poly.loop_indices]
     if all(abs(v.x+.5)<1e-6 for v in vs):caps.append(fields)
     else:faces.append(fields)
   ent['WcapFaces']=caps;ent['WcollarFaces']=faces
   eo.to_mesh_clear()
   for m in ob.data.materials:out['materials'][m.name]={'graph':graph(m.node_tree),'diffuse':vec(m.diffuse_color)}
  out['objects'].append(ent)
 out['rawAuthoredBounds']={'min':[min(v[i] for v in rawall) for i in range(3)],'max':[max(v[i] for v in rawall) for i in range(3)]};out['evaluatedBounds']={'min':[min(v[i] for v in evalall) for i in range(3)],'max':[max(v[i] for v in evalall) for i in range(3)]};out['rawAuthoringOutlineXY']=hull([vec(v)[:2] for v in rawall]);out['evaluatedOutlineXY']=hull([vec(v)[:2] for v in evalall]);out['finiteLowestSupportFaces']=support;out['geometricZ0Intersection']=[] if min(v.z for v in evalall)>0 else 'requires calculation'
 return out,root
# exact approved native middle scene is the canonical rig resource, untouched on disk
sc=bpy.context.scene;enable()
midcol=next(c for c in sc.collection.children if any(o.name.startswith('wreck-middle__root') for o in c.all_objects))
midroot=next(o for o in midcol.all_objects if o.type=='EMPTY' and o.parent is None)
# load own original collection and exact approved edge collection into in-memory inspection only
for path,asset in [(R/'source/original.blend','wreck-end'),(R/'canonical/wreck-edge/native.blend','wreck-edge')]:
 with bpy.data.libraries.load(str(path),link=False) as (a,b):
  if asset=='wreck-end':name=next(c for c in a.collections if 'wreck-end' in c)
  else:name=next(c for c in a.collections if 'wreck' in c.lower())
  b.collections=[name]
 sc.collection.children.link(b.collections[0])
endcol=next(c for c in sc.collection.children if any(o.get('asset_id')=='wreck-end' for o in c.all_objects));edgecol=next(c for c in sc.collection.children if c!=midcol and c!=endcol and any(o.type=='EMPTY' for o in c.all_objects))
measure,endroot=audit(endcol,'untouched own original');write(P/'source-native-measurements.json',measure)
canonical,midroot=audit(midcol,'exact approved middle02 canonical fields');write(P/'canonical-native-measurements.json',canonical)
edge,edgeroot=audit(edgecol,'exact approved edge02 neighbor static ownership');write(P/'edge-native-measurements.json',edge)
rig={'engine':sc.render.engine,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'dither':sc.render.dither_intensity,'filter':sc.render.filter_size,'world':graph(sc.world.node_tree),'camera':{'name':sc.camera.name,'matrixWorld':mat(sc.camera.matrix_world),'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]},'lights':[{'name':o.name,'matrixWorld':mat(o.matrix_world),'energy':o.data.energy,'color':vec(o.data.color),'shape':o.data.shape,'size':o.data.size,'useShadow':o.data.use_shadow} for o in sc.objects if o.type=='LIGHT']}
write(P/'actual-canonical-rig.json',rig)
# Keep every shader/geometry byte; only set visibility, proper root poses and registered extended view framing in memory.
sc.render.resolution_percentage=100;sc.render.fps=12;sc.frame_set(1)
baseShift=sc.camera.data.shift_y;baseOrtho=sc.camera.data.ortho_scale
records=[]
angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
def capture(folder,d,show,chain=False):
 for col in [endcol,midcol,edgecol]:
  for ob in col.all_objects:ob.hide_render=col not in show
 for root in [endroot,midroot,edgeroot]:root.rotation_euler=(0,0,angles[d]);root.location=(0,0,0)
 if chain:
  r=Matrix.Rotation(angles[d],4,'Z');midroot.location=r@Vector((-1,0,0));edgeroot.location=r@Vector((-2,0,0))
 # geometry root 0 remains native authority; extend canvas at exact fixed projection around midpoint -1.
 width,height=(192,352);origin=(96,248);center=Vector((0,0,0))
 if chain:
  if d in ['N','S']:width,height=448,352;origin=(352 if d=='S' else 96,248)
  else:width,height=192,608;origin=(96,504 if d=='W' else 248)
 # Use camera ortho width scale and shifts derived from actual pixel-root and desired exact size.
 sc.render.resolution_x=width*2;sc.render.resolution_y=height*2
 sc.camera.data.ortho_scale=baseOrtho*width/192
 sc.camera.data.shift_x=-(origin[0]-width/2)/width
 sc.camera.data.shift_y=(origin[1]-height/2)/height*height/(width*sc.render.pixel_aspect_x)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
 pix=world_to_camera_view(sc,sc.camera,Vector((0,0,0)));projection=[pix.x*sc.render.resolution_x,(1-pix.y)*sc.render.resolution_y]
 p=O/folder/(d+'.png');p.parent.mkdir(exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 records.append({'folder':folder,'direction':d,'path':str(p.relative_to(P)),'nativeFrame':[width*2,height*2],'logicalFrame':[width,height],'logicalRoot':origin,'measuredRootPixels':projection,'rootRotationDegrees':math.degrees(endroot.rotation_euler.z),'rootMatrix':mat(endroot.matrix_world),'cameraMatrix':mat(sc.camera.matrix_world),'cameraOrtho':sc.camera.data.ortho_scale,'cameraShift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'objects':[{'root':o.name,'matrix':mat(o.matrix_world)} for o in [endroot,midroot,edgeroot]],'sha256':sha(p)})
for d in 'NESW':capture('original-canonical-rig',d,[endcol]);capture('mixed-native',d,[endcol,midcol,edgecol],True)
write(P/'baseline-capture-records.json',{'source':sha(R/'source/original.blend'),'middle':sha(R/'canonical/wreck-middle/native.blend'),'edge':sha(R/'canonical/wreck-edge/native.blend'),'captureRecords':records,'publication':'direct native2 identity; original derivative only, not candidate or approval'})
print('MEASURED',measure['rawAuthoredBounds'],measure['rawAuthoringOutlineXY'],measure['evaluatedBounds'])
