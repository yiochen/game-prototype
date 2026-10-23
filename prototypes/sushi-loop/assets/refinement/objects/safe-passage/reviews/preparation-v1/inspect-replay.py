import bpy, sys, json, math, hashlib, importlib.util, time
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
RES=HERE/'resources'
def load(name):
 s=importlib.util.spec_from_file_location('safe_judge_'+name,RES/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def matrix(m):return [list(r) for r in m]
def plain(v):
 if isinstance(v,(str,bool,int,float)) or v is None:return v
 try:return list(v)
 except:return str(v)
def bounds(points):
 if not points:return None
 return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
def write(name,v):
 p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
sc=next(s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33)
bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
rig=json.loads((RES/'source-rig.json').read_text());asset=json.loads((RES/'source-assetRecord.json').read_text())
root=bpy.data.objects[rig['groundRootObject']]
col=next(c for c in sc.collection.children if root in list(c.all_objects))
asset.update(root=root,collection=col)
saved={'scene':sc.name,'camera':sc.camera.name if sc.camera else None,'cameraMatrix':matrix(sc.camera.matrix_world) if sc.camera else None,'resolution':[sc.render.resolution_x,sc.render.resolution_y], 'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y], 'collection':col.name,'root':root.name,'rootMatrix':matrix(root.matrix_world),'objects':[{'name':o.name,'type':o.type,'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'hide_set':o.hide_get(),'matrixWorld':matrix(o.matrix_world)} for o in col.all_objects]}
def layers(l):
 yield l
 for c in l.children:yield from layers(c)
for l in layers(sc.view_layers[0].layer_collection):l.exclude=False;l.hide_viewport=False
for c in sc.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=col
for c in [col,*list(col.children_recursive)]:c.hide_render=False;c.hide_viewport=False
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
sc.view_layers[0].update();bpy.context.evaluated_depsgraph_get().update()
native=load('native_actions');runtime=load('capture_runtime');runtime.scene=lambda:sc;runtime.SCENE_NAME=sc.name
native.apply_clip(asset,rig,'ambient',frame=1,direction='S',scene=sc)
def geomeasure(include_vertices=False):
 dg=bpy.context.evaluated_depsgraph_get();records=[];rawall=[];evalall=[]
 for o in col.all_objects:
  if o.type!='MESH':continue
  raw=[o.matrix_world@v.co for v in o.data.vertices];ev=o.evaluated_get(dg);me=ev.to_mesh();evaluated=[ev.matrix_world@v.co for v in me.vertices]
  rawall+=raw;evalall+=evaluated
  rec={'object':o.name,'matrixWorld':matrix(o.matrix_world),'rawAuthoredBounds':bounds(raw),'evaluatedBounds':bounds(evaluated),'rawVertexCount':len(o.data.vertices),'rawPolygonCount':len(o.data.polygons),'evaluatedVertexCount':len(me.vertices),'evaluatedPolygonCount':len(me.polygons),'modifiers':[{'name':m.name,'type':m.type,'show_render':m.show_render,'show_viewport':m.show_viewport,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)} for m in o.modifiers],'parent':o.parent.name if o.parent else None,'constraints':[c.name for c in o.constraints],'shapeKeys':[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],'minimumAbsZRaw':min(abs(p.z) for p in raw) if raw else None,'rawVertexCountsByGround':{'below':sum(p.z < -1e-5 for p in raw),'on':sum(abs(p.z)<=1e-5 for p in raw),'above':sum(p.z>1e-5 for p in raw)}}
  if include_vertices:rec['rawWorldVertices']=[list(p) for p in raw]
  records.append(rec);ev.to_mesh_clear()
 return {'rawAuthoredBounds':bounds(rawall),'evaluatedBounds':bounds(evalall),'objects':records}
materials={m for o in col.all_objects if o.type=='MESH' for m in o.data.materials if m}
mats=[]
for m in materials:
 mats.append({'name':m.name,'diffuseColor':list(m.diffuse_color),'useNodes':m.use_nodes,'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:plain(i.default_value) for i in n.inputs if hasattr(i,'default_value') and not i.is_linked},'image':n.image.filepath if n.type=='TEX_IMAGE' and n.image else None} for n in m.node_tree.nodes] if m.use_nodes else [],'links':[{'fromNode':l.from_node.name,'fromSocket':l.from_socket.name,'toNode':l.to_node.name,'toSocket':l.to_socket.name} for l in m.node_tree.links] if m.use_nodes else []})
write('enabled-source-inspection.json',{'savedBeforeEnable':saved,'blenderVersion':bpy.app.version_string,'loadedBlend':bpy.data.filepath,'sourceBlendSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'enabledCollection':col.name,'root':root.name,'rootMatrix':matrix(root.matrix_world),'metadataAsset':{k:v for k,v in asset.items() if k not in ('root','collection')},'enabledSFrame1':geomeasure(True),'materials':mats,'armatures':[o.name for o in col.all_objects if o.type=='ARMATURE'],'externalImages':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images if i.users and i.source=='FILE' and any(n.type=='TEX_IMAGE' and n.image==i for m in materials for n in m.node_tree.nodes)],'libraries':[l.filepath for l in bpy.data.libraries]})
print('SAFE_JUDGE_LOCATORS '+json.dumps({'scene':sc.name,'collection':col.name,'root':root.name,'objects':len(col.all_objects),'meshes':sum(o.type=='MESH' for o in col.all_objects)}),flush=True)
# Exact source capture driver; no source/model edits, frame fitting, camera-facing cards or pixel repair.
camera=runtime.configure_camera(asset['projection'],tuple(asset['frame']),tuple(asset['anchor']),int(asset['scale']))
sc.render.threads_mode='FIXED';sc.render.threads=4
sc.render.image_settings.compression=15
write('camera-measured.json',camera)
write('capture-configuration.json',{'engine':sc.render.engine,'renderResolution':[sc.render.resolution_x,sc.render.resolution_y],'fps':sc.render.fps,'filmTransparent':sc.render.film_transparent,'dither':sc.render.dither_intensity,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'cameraOrthoScale':sc.camera.data.ortho_scale,'lights':[{'name':o.name,'matrix':matrix(o.matrix_world),'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'size':getattr(o.data,'size',None)} for o in sc.objects if o.type=='LIGHT'],'worldStrength':[n.inputs['Strength'].default_value for n in sc.world.node_tree.nodes if n.type=='BACKGROUND'],'nativeScale':4,'publishedScale':2})
records=[];closures={}
for direction in ['N','E','S','W']:
 for index in range(12):
  native.apply_clip(asset,rig,'ambient',frame=index+1,direction=direction,scene=sc);bpy.context.evaluated_depsgraph_get().update()
  gm=geomeasure();p=HERE/'native'/'ambient'/direction/(f'{index:03}.png');p.parent.mkdir(parents=True,exist_ok=True)
  rec={'clip':'ambient','direction':direction,'index':index,'blenderFrame':sc.frame_current,'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':matrix(root.matrix_world),'geometry':gm,'path':str(p.relative_to(HERE))}
  sc.render.filepath=str(p);bpy.ops.render.render(write_still=True,scene=sc.name);rec['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();records.append(rec)
  print('SAFE_JUDGE_FRAME '+direction+' '+str(index),flush=True)
 # closure is measured evaluated geometry and object transforms, not an extra runtime frame.
 native.apply_clip(asset,rig,'ambient',frame=13,direction=direction,scene=sc);closures[direction]={'blenderFrame':13,'rootMatrix':matrix(root.matrix_world),'geometry':geomeasure()}
write('capture-records.json',{'captureRecords':records,'closureFrame13':closures,'nativeFrame':[768,1408],'sourceBlendSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'requestedFrameRange':[1,12],'runtimeFrameOrder':list(range(12)),'closureExcludedFromAtlas':True})
print('SAFE_JUDGE_COMPLETE',flush=True)
