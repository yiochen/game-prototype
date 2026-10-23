import sys
sys.dont_write_bytecode=True
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parent;OUT=B/'evidence';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(B/'resources/source/round-02.blend'))
sc=bpy.context.scene;root=next(o for o in sc.objects if o.name.startswith('reef-middle__root'))
col=next(c for c in sc.collection.children if root in list(c.all_objects))
def nodes(l):
 yield l
 for c in l.children:yield from nodes(c)
for l in nodes(bpy.context.view_layer.layer_collection):l.exclude=False;l.hide_viewport=False
col.hide_render=False;col.hide_viewport=False
for o in col.all_objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();cam=sc.camera
report={'blender':bpy.app.version_string,'python':sys.version,'sourceSHA256':hashlib.sha256((B/'resources/source/round-02.blend').read_bytes()).hexdigest(),'scene':sc.name,'collection':col.name,'root':root.name,'savedRootMatrix':[list(row) for row in root.matrix_world],'rootProperties':dict(root.items()),'camera':{'name':cam.name,'type':cam.data.type,'matrix':[list(row) for row in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y]},'render':{'resolution':[sc.render.resolution_x,sc.render.resolution_y],'percentage':sc.render.resolution_percentage,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'filterSize':sc.render.filter_size,'engine':sc.render.engine,'fps':sc.render.fps,'transparent':sc.render.film_transparent,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'worldStrength':[n.inputs['Strength'].default_value for n in sc.world.node_tree.nodes if n.type=='BACKGROUND']},'geometry':[],'materials':{},'lights':[],'images':[],'linkedLibraries':[l.filepath for l in bpy.data.libraries],'actions':[a.name for a in bpy.data.actions],'facings':{}}
allpts=[]
for o in col.all_objects:
 if o.type!='MESH':continue
 ev=o.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();mat=root.matrix_world.inverted()@ev.matrix_world;nm=mat.to_3x3().inverted().transposed();pts=[mat@v.co for v in me.vertices];allpts+=pts
 g={'name':o.name,'vertices':len(me.vertices),'triangles':len(me.loop_triangles),'bounds':[[min(v[k] for v in pts),max(v[k] for v in pts)] for k in range(3)],'parent':o.parent.name if o.parent else None,'meshUsers':o.data.users,'modifiers':[m.type for m in o.modifiers],'objectAnimation':bool(o.animation_data),'dataAnimation':bool(o.data.animation_data),'shapeKeys':bool(o.data.shape_keys),'uvLayers':list(me.uv_layers.keys()),'materials':[m.name for m in me.materials]}
 if 'continuous_core' in o.name:
  g['allRootLocalVertices']=[list(v) for v in pts];g['portLoops']={};g['endpointAdjacentTriangles']={}
  for side,x in [('W',-.5),('E',.5)]:
   ids=[i for i,v in enumerate(pts) if abs(v.x-x)<1e-6];g['portLoops'][side]=[list(pts[i]) for i in ids];trs=[]
   for t in me.loop_triangles:
    if any(i in ids for i in t.vertices):trs.append({'vertices':[list(pts[i]) for i in t.vertices],'cornerNormals':[list(nm@me.corner_normals[li].vector) for li in t.loops],'material':me.materials[t.material_index].name})
   g['endpointAdjacentTriangles'][side]=trs
 report['geometry'].append(g)
 for m in me.materials:
  if m.name in report['materials']:continue
  nt=m.node_tree;material={'users':m.users,'animation':bool(m.animation_data),'nodeTreeAnimation':bool(nt.animation_data),'nodes':[],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in nt.links]}
  for n in nt.nodes:
   z={'name':n.name,'type':n.type,'inputs':{}}
   for i in n.inputs:
    if hasattr(i,'default_value') and i.type in ['RGBA','VALUE','VECTOR','BOOLEAN','INT']:z['inputs'][i.name]=list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value
   if n.type=='VALTORGB':z['ramp']={'interpolation':n.color_ramp.interpolation,'elements':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]}
   if n.type=='TEX_IMAGE':z['image']=n.image.name if n.image else None
   material['nodes'].append(z)
  report['materials'][m.name]=material
 ev.to_mesh_clear()
report['bounds']=[[min(v[k] for v in allpts),max(v[k] for v in allpts)] for k in range(3)]
for o in sc.objects:
 if o.type=='LIGHT':report['lights'].append({'name':o.name,'type':o.data.type,'position':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color)})
for i in bpy.data.images:
 if i.source=='FILE':report['images'].append({'name':i.name,'source':i.filepath,'packed':bool(i.packed_file)})
# Audit and render only saved native source, one unchanged camera/light/material recipe across canonical root rotations.
for d,a in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 root.rotation_euler.z=a;sc.frame_set(1);bpy.context.view_layer.update()
 def px(v):
  p=world_to_camera_view(sc,cam,Vector(v));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
 origin=px((0,0,0));unit={name:[v[k]-origin[k] for k in range(2)] for name,v in [('X',px((1,0,0))),('depth',px((0,-1,0))),('height',px((0,0,1)))]}
 path=OUT/('reopened-'+d+'.png');sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 report['facings'][d]={'rotationRadians':root.rotation_euler.z,'rootMatrix':[list(row) for row in root.matrix_world],'rootPixels':origin,'unitPixels':unit,'render':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
(OUT/'reopened-native-audit.json').write_text(json.dumps(report,indent=2,default=str)+'\n');print('INDEPENDENT_REOPEN_AUDIT_COMPLETE',flush=True)
