import sys,os,json,math,hashlib,importlib.util,time
sys.dont_write_bytecode=True
from pathlib import Path
import bpy
from mathutils import Vector
HERE=Path(__file__).resolve().parent
RES=HERE/'resources';OUT=HERE/'native';OUT.mkdir(exist_ok=True)
def plain(v):
 if v is None or isinstance(v,(str,bool,int,float)):return v
 if isinstance(v,dict):return {str(k):plain(x) for k,x in v.items()}
 try:return [plain(x) for x in v]
 except:return str(v)
def write(name,v):(OUT/name).write_text(json.dumps(plain(v),indent=2)+'\n')
def load(name):
 spec=importlib.util.spec_from_file_location('judge_'+name,RES/'native'/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
native=load('native_actions');runtime=load('capture_runtime')
rig=json.loads((RES/'object/inputs/source-rig.json').read_text());asset=json.loads((RES/'object/inputs/source-assetRecord.json').read_text())
root=bpy.data.objects[rig['groundRootObject']]
sc=next(s for s in bpy.data.scenes if root.name in s.objects)
if bpy.context.window:bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
col=next(c for c in sc.collection.children if root.name in c.all_objects)
owned=list(col.all_objects);asset.update(root=root,collection=col)
initial={'blenderVersion':bpy.app.version_string,'blend':str(Path(bpy.data.filepath).resolve()),'blendSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'scene':sc.name,'sceneProperties':dict(sc.items()),'collection':col.name,'savedActiveCamera':sc.camera.name if sc.camera else None,'savedRender':{'engine':sc.render.engine,'frame':[sc.render.resolution_x,sc.render.resolution_y],'percentage':sc.render.resolution_percentage,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]},'savedRootMatrix':plain(root.matrix_world),'objects':[]}
for o in owned:
 initial['objects'].append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'hideSet':o.hide_get(),'location':plain(o.location),'rotation':plain(o.rotation_euler),'scale':plain(o.scale),'matrix':plain(o.matrix_world),'properties':plain(dict(o.items())),'vertexCount':len(o.data.vertices) if o.type=='MESH' else None,'faceCount':len(o.data.polygons) if o.type=='MESH' else None,'modifiers':[{'name':m.name,'type':m.type,'showRender':m.show_render,'showViewport':m.show_viewport,**{k:getattr(m,k) for k in ('width','segments','levels','render_levels') if hasattr(m,k)}} for m in o.modifiers],'constraints':[{'name':c.name,'type':c.type} for c in o.constraints],'shapeKeys':[] if o.type!='MESH' or not o.data.shape_keys else [k.name for k in o.data.shape_keys.key_blocks],'materials':[s.material.name for s in o.material_slots if s.material]})
write('untouched-inventory.json',initial)
def layers(n):
 yield n
 for c in n.children:yield from layers(c)
for layer in layers(sc.view_layers[0].layer_collection):layer.exclude=False;layer.hide_viewport=False
for layer in sc.view_layers[0].layer_collection.children:layer.exclude=layer.collection!=col
for c in sc.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
# Enable actual collection ancestry and owned objects before native cohort evaluation.
col.hide_render=False;col.hide_viewport=False
for o in owned:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
runtime.scene=lambda:sc;runtime.SCENE_NAME=sc.name
camera=runtime.configure_camera(asset['projection'],tuple(asset['frame']),tuple(asset['anchor']),int(asset['scale']))
sc.render.image_settings.compression=15
sc.render.threads_mode='FIXED';sc.render.threads=4
if hasattr(sc,'eevee'):sc.eevee.taa_render_samples=32
write('capture-camera.json',camera)
write('capture-settings.json',{'engine':sc.render.engine,'samples':getattr(getattr(sc,'eevee',None),'taa_render_samples',None),'fps':sc.render.fps,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'color':{'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma},'transparent':sc.render.film_transparent,'cameraName':sc.camera.name,'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'lights':[{'name':o.name,'energy':o.data.energy,'type':o.data.type,'position':plain(o.location),'size':getattr(o.data,'size',None),'matrix':plain(o.matrix_world)} for o in sc.objects if o.type=='LIGHT' and o.data.energy],'world':{'name':sc.world.name,'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:plain(i.default_value) for i in n.inputs if hasattr(i,'default_value')}} for n in sc.world.node_tree.nodes]},'compositor':{'name':sc.compositing_node_group.name if sc.compositing_node_group else None,'properties':dict(sc.compositing_node_group.items()) if sc.compositing_node_group else {}}})
materials={s.material for o in owned for s in o.material_slots if s.material}
write('native-resources.json',{'libraries':[{'name':l.name,'filepath':l.filepath} for l in bpy.data.libraries],'ownedMaterialNames':[m.name for m in materials],'materials':[{'name':m.name,'properties':plain(dict(m.items())),'nodes':[{'name':n.name,'type':n.type,'properties':{k:getattr(n,k) for k in ('blend_type','operation','mode') if hasattr(n,k)},'inputs':{i.name:plain(i.default_value) for i in n.inputs if hasattr(i,'default_value')}} for n in m.node_tree.nodes],'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in m.node_tree.links]} for m in materials],'ownedImages':list({n.image.filepath for m in materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image})})
actionEvidence=[]
for clip,c in rig['clips'].items():
 for target in c['actions']:
  a=bpy.data.actions[target['action']];curves=[]
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for f in bag.fcurves:curves.append({'dataPath':f.data_path,'arrayIndex':f.array_index,'extrapolation':f.extrapolation,'keys':[[float(p.co.x),float(p.co.y),p.interpolation] for p in f.keyframe_points]})
  actionEvidence.append({'clip':clip,'owner':target['ownerName'],'action':a.name,'frameRange':plain(a.frame_range),'curves':curves})
write('action-channels.json',actionEvidence)
def bounds(points):
 return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)],'count':len(points)} if points else None
def measure(clip,direction,frame):
 native.apply_clip(asset,rig,clip,frame=frame,direction=direction,scene=sc)
 # hide_set is never a cohort channel, all owned objects must be evaluable.
 for o in owned:o.hide_set(False)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
 raw=[];ev=[];ob=[]
 for o in owned:
  if o.type!='MESH':continue
  e=o.evaluated_get(dg);visible=not e.hide_render
  rawpts=[o.matrix_world@v.co for v in o.data.vertices]
  mesh=e.to_mesh();evpts=[e.matrix_world@v.co for v in mesh.vertices]
  if visible:raw+=rawpts;ev+=evpts
  ob.append({'name':o.name,'visible':visible,'rawAuthoredTransformed':bounds(rawpts),'evaluatedModifier':bounds(evpts),'location':plain(o.location),'rotation':plain(o.rotation_euler),'scale':plain(o.scale),'matrix':plain(o.matrix_world)})
  e.to_mesh_clear()
 return {'clip':clip,'direction':direction,'sourceFrame':frame,'frameIndex':frame-1,'rootRotationZ':float(root.rotation_euler.z),'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':plain(root.matrix_world),'rawAuthoredBounds':bounds(raw),'evaluatedBounds':bounds(ev),'objects':ob}
records=[]
for clip,c in rig['clips'].items():
 for d in ['N','E','S','W']:
  for frame in range(1,13):records.append(measure(clip,d,frame))
write('all432-native-measurements.json',{'asset':'salvage-metal','sourceSHA256':initial['blendSHA256'],'camera':camera,'captureRecords':records})
terminal=[]
for clip,c in rig['clips'].items():
 for frame in ([1,12,13] if c['loop'] else [1,12,13,24]):terminal.append(measure(clip,'S',frame))
write('closure-and-hold-measurements.json',terminal)
# Bounded rendered proof: all nine states in all four facings at frame0;
# key/mid/end S plus loop closure or terminal hold. Published atlas playback adds all phases.
jobs=[]
for clip,c in rig['clips'].items():
 for d in ['N','E','S','W']:jobs.append((clip,d,1))
 for frame in [4,7,10,12,13]:jobs.append((clip,'S',frame))
 if not c['loop']:jobs.append((clip,'S',24))
captures=[]
for i,(clip,d,frame) in enumerate(jobs):
 rec=measure(clip,d,frame);rel=Path('raw')/clip/d/(f'{frame-1:03d}.png');p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(p)
 bpy.ops.render.render(write_still=True,scene=sc.name)
 captures.append({**{k:v for k,v in rec.items() if k not in ['objects']},'path':str(Path('native')/rel),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 print('JUDGE_SOURCE_CAPTURE',i+1,len(jobs),clip,d,frame,flush=True)
 write('capture-records.json',{'sourceSHA256':initial['blendSHA256'],'camera':camera,'captureRecords':captures})
print('PREPARATION_NATIVE_COMPLETE',len(records),len(captures),flush=True)
