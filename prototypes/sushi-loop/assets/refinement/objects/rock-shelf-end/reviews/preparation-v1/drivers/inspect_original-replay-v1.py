import sys
sys.dont_write_bytecode=True
import bpy, json, math, importlib.util
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
def save(rel,data):
 (ROOT/rel).write_text(json.dumps(data,indent=2)+'\n')
def simple(v):
 try:return list(v)
 except TypeError:return v

def inspect_material(m):
 if not m:return None
 rec={'name':m.name,'properties':{k:simple(m[k]) for k in m.keys()},'diffuseColor':list(m.diffuse_color),'useNodes':m.use_nodes}
 if m.use_nodes:
  nodes=[]
  for n in m.node_tree.nodes:
   info={'name':n.name,'type':n.type,'label':n.label,'inputs':{},'outputs':{}}
   for s in n.inputs:
    if hasattr(s,'default_value'):
     try:info['inputs'][s.name]=simple(s.default_value)
     except:pass
   for attr in ['blend_type','operation','vector_type','convert_from','convert_to','interpolation','noise_dimensions','normalize']:
    if hasattr(n,attr):info[attr]=getattr(n,attr)
   if hasattr(n,'color_ramp'):info['ramp']=[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]
   nodes.append(info)
  rec.update(nodes=nodes,links=[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in m.node_tree.links])
 return rec
scenes=[s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33]
assert len(scenes)==1
sc=scenes[0];bpy.context.window.scene=sc
rig=json.loads((ROOT/'resources/input/source-rig.json').read_text());asset=json.loads((ROOT/'resources/input/source-assetRecord.json').read_text())
r=bpy.data.objects[rig['groundRootObject']]
col=next(c for c in sc.collection.children if r in list(c.all_objects))
bpy.context.view_layer.update()
saved={'scene':sc.name,'sceneProperties':{k:simple(sc[k]) for k in sc.keys()},'camera':{'name':sc.camera.name,'matrixWorld':[list(row) for row in sc.camera.matrix_world],'rotationEuler':list(sc.camera.rotation_euler),'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y]},'render':{'engine':sc.render.engine,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'filterSize':sc.render.filter_size,'filmTransparent':sc.render.film_transparent,'fps':sc.render.fps},'collection':col.name,'root':{'name':r.name,'location':list(r.location),'rotation':list(r.rotation_euler),'scale':list(r.scale),'properties':{k:simple(r[k]) for k in r.keys()}},'objects':[],'materials':[],'externalImages':[],'libraries':[],'blenderVersion':bpy.app.version_string}
# Source may be saved in an incidental facing; measure authored local S geometry.
r.rotation_euler=(0,0,0);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();inv=r.matrix_world.inverted()
allp=[];ground=[];port=[]
materials=set()
for o in sorted(col.all_objects,key=lambda o:o.name):
 rec={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers],'constraints':[{'name':c.name,'type':c.type} for c in o.constraints],'animationData':bool(o.animation_data),'materials':[slot.material.name if slot.material else None for slot in o.material_slots]}
 if o.type=='MESH':
  ev=o.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles();pts=[inv@ev.matrix_world@v.co for v in mesh.vertices];allp+=pts
  ground+=[list(v) for v in pts if abs(v.z)<1e-6]
  port+=[list(v) for v in pts if abs(v.x+.5)<1e-6]
  rec.update(vertices=[list(p) for p in pts],faces=[{'vertices':list(p.vertices),'normal':list(p.normal),'materialIndex':p.material_index,'smooth':p.use_smooth} for p in mesh.polygons],cornerNormals=[list(n.vector) for n in mesh.corner_normals],attributes=[{'name':a.name,'domain':a.domain,'type':a.data_type} for a in mesh.attributes],uvLayers=[u.name for u in mesh.uv_layers],shapeKeys=list(o.data.shape_keys.key_blocks.keys()) if o.data.shape_keys else [])
  ev.to_mesh_clear()
  materials.update(s.material for s in o.material_slots if s.material)
 saved['objects'].append(rec)
saved['boundsLocalS']=[[min(p[i] for p in allp) for i in range(3)],[max(p[i] for p in allp) for i in range(3)]]
saved['groundZ0Vertices']=ground;saved['portXminusHalfVertices']=port
saved['materials']=[inspect_material(m) for m in sorted(materials,key=lambda m:m.name)]
saved['externalImages']=[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file),'source':i.source} for i in bpy.data.images if i.source=='FILE' and i.users]
saved['libraries']=[l.filepath for l in bpy.data.libraries]
save('measurements/original-native.json',saved)
# Exact known native capture path, loading unmodified copied capture modules.
spec=importlib.util.spec_from_file_location('saved_capture_runtime',ROOT/'resources/capture/capture_runtime.py');rt=importlib.util.module_from_spec(spec);spec.loader.exec_module(rt);rt.scene=lambda:sc;rt.SCENE_NAME=sc.name
for c in sc.collection.children:c.hide_render=(c!=col);c.hide_viewport=(c!=col)
def layers(n):
 yield n
 for c in n.children:yield from layers(c)
for layer in layers(sc.view_layers[0].layer_collection):layer.exclude=False
for layer in sc.view_layers[0].layer_collection.children:layer.exclude=(layer.collection!=col)
sc.frame_set(1)
cam=rt.configure_camera(asset['projection'],tuple(asset['frame']),tuple(asset['anchor']),asset['scale'])
sc.render.image_settings.compression=15
save('measurements/replay-camera.json',{'camera':cam,'filterSize':sc.render.filter_size,'renderEngine':sc.render.engine,'sourceFrame':1,'directions':{'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}})
for d,angle in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 r.rotation_euler=(0,0,angle);bpy.context.view_layer.update()
 sc.render.filepath=str(ROOT/'captures/original-native'/f'{d}.png')
 bpy.ops.render.render(write_still=True,scene=sc.name)
print('ORIGINAL_MEASUREMENT_AND_REPLAY_COMPLETE '+str(ROOT))
