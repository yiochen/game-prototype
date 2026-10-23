import sys,os,json,math,hashlib,importlib.util,time
sys.dont_write_bytecode=True
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parents[1]; R=P/'resources/native'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def dump(p,x):p.write_text(json.dumps(x,indent=2,default=str)+'\n')
def matrix(x):return [list(r) for r in x]
def bounds(points):
 return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]} if points else None
sc=next(s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33)
bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
root=bpy.data.objects['attack-reef-fragments__ground_root.001']; col=bpy.data.collections['S33_CFX_attack-reef-fragments.001']
def layers(x):
 yield x
 for c in x.children:yield from layers(c)
for l in layers(sc.view_layers[0].layer_collection):l.exclude=False;l.hide_viewport=False
for c in sc.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
col.hide_render=False;col.hide_viewport=False
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
sc.view_layers[0].update()
asset=json.loads((R/'asset.json').read_text());rig=json.loads((R/'rig.json').read_text());asset.update(root=root,collection=col)
runtime=load('judgeruntime',R/'capture_runtime.py');native=load('judgenative',R/'native_actions.py');runtime.scene=lambda:sc;runtime.SCENE_NAME=sc.name
cam_record=runtime.configure_camera(asset['projection'],tuple(asset['frame']),tuple(asset['anchor']),asset['scale'],asset.get('camera_elevation_degrees'))
sc.eevee.taa_render_samples=32;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.image_settings.compression=15;sc.render.use_persistent_data=True
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
materials=[]
for mat in sorted({sl.material for o in col.all_objects if o.type=='MESH' for sl in o.material_slots if sl.material},key=lambda x:x.name):
 materials.append({'name':mat.name,'properties':dict(mat.items()),'diffuseColor':list(mat.diffuse_color),'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':{s.name:list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value for s in n.inputs if hasattr(s,'default_value') and not s.is_linked},'ramp':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements] if n.type=='VALTORGB' else None} for n in mat.node_tree.nodes],'links':[{'from':l.from_node.name+'.'+l.from_socket.name,'to':l.to_node.name+'.'+l.to_socket.name} for l in mat.node_tree.links]})
lights=[{'name':o.name,'matrix':matrix(o.matrix_world),'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size if hasattr(o.data,'size') else None,'properties':dict(o.items())} for o in sc.collection.objects if o.type=='LIGHT']
static={'source':{'path':str(Path(bpy.data.filepath)),'sha256':sha(Path(bpy.data.filepath))},'blenderVersion':bpy.app.version_string,'scene':sc.name,'collection':col.name,'root':root.name,'ownedObjects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'vertices':len(o.data.vertices) if o.type=='MESH' else None,'polygons':len(o.data.polygons) if o.type=='MESH' else None,'modifiers':[{'name':m.name,'type':m.type,'enabledRender':m.show_render,'enabledViewport':m.show_viewport,'width':m.width if hasattr(m,'width') else None,'segments':m.segments if hasattr(m,'segments') else None} for m in o.modifiers],'constraints':[c.name for c in o.constraints],'shapeKeys':list(o.data.shape_keys.key_blocks.keys()) if o.type=='MESH' and o.data.shape_keys else [],'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'hideSet':o.hide_get()} for o in col.all_objects],'camera':cam_record,'cameraData':{'name':sc.camera.name,'orthoScale':sc.camera.data.ortho_scale,'shiftX':sc.camera.data.shift_x,'shiftY':sc.camera.data.shift_y,'sensorFit':sc.camera.data.sensor_fit},'render':{'engine':sc.render.engine,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'resolutionPercentage':sc.render.resolution_percentage,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'samples':32,'filmTransparent':sc.render.film_transparent,'fps':sc.render.fps,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'filterSize':sc.render.filter_size,'compositor':sc.compositing_node_group.name if sc.compositing_node_group else None},'materials':materials,'lights':lights,'world':{'name':sc.world.name,'nodes':[{'name':n.name,'type':n.type,'strength':n.inputs['Strength'].default_value if n.type=='BACKGROUND' else None} for n in sc.world.node_tree.nodes]},'rig':{'armatures':rig['armatures'],'actionCount':rig['actionCount'],'clips':{k:{f:v for f,v in c.items() if f not in ['actions','controlsByFrame']} for k,c in rig['clips'].items()}},'supportInterpretation':'Nine disjoint suspended native fragment solids. Root is effect origin, not a floor contact surface. No native sockets/ports, support mesh, armature, constraints or modular join is authored.'}
dump(P/'native/source-measurements.json',static)
records=[]
for clip,cfg in rig['clips'].items():
 for direction in ['N','E','S','W']:
  for i in range(cfg['frames']):
   native.apply_clip(asset,rig,clip,frame=i+1,direction=direction,scene=sc)
   for o in col.all_objects:o.hide_set(False)
   bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();meshes=[];allraw=[];alleval=[];projected=[]
   for o in col.all_objects:
    if o.type!='MESH':continue
    raw=[o.matrix_world@v.co for v in o.data.vertices];eo=o.evaluated_get(dg);em=eo.to_mesh();ev=[eo.matrix_world@v.co for v in em.vertices];eo.to_mesh_clear()
    for v in ev:
     q=world_to_camera_view(sc,sc.camera,v);projected.append((q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y,q.z))
    meshes.append({'name':o.name,'location':list(o.location),'rotationEuler':list(o.rotation_euler),'scale':list(o.scale),'matrix':matrix(o.matrix_world),'rawAuthoredBounds':bounds(raw),'evaluatedBounds':bounds(ev),'rawVertices':len(raw),'evaluatedVertices':len(ev)})
    allraw+=raw;alleval+=ev
   rec={'clip':clip,'direction':direction,'index':i,'nativeFrame':i+1,'seconds':i/12,'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':matrix(root.matrix_world),'rawAuthoredBounds':bounds(allraw),'evaluatedBounds':bounds(alleval),'projectedEvaluatedBoundsNative':bounds(projected),'objects':meshes}
   folder=P/'native/frames'/clip/direction;folder.mkdir(parents=True,exist_ok=True);dest=folder/f'{i:03d}.png';sc.render.filepath=str(dest);started=time.monotonic();bpy.ops.render.render(write_still=True,scene=sc.name)
   rec.update(path=str(dest.relative_to(P)),sha256=sha(dest),renderSeconds=time.monotonic()-started);records.append(rec)
   dump(P/'native/capture-ledger.json',{'schema':'measured-native-views-v1','sourceSHA256':static['source']['sha256'],'camera':cam_record,'captureRecords':records})
   print('JUDGE_REPLAY '+json.dumps({'clip':clip,'direction':direction,'index':i,'seconds':rec['renderSeconds']}),flush=True)
print('JUDGE_COMPLETE '+str(len(records)),flush=True)
