"""Preparation-only replay of saved source. No .blend writes or geometry edits."""
import bpy, sys, math, json, hashlib, importlib.util, time
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent
NATIVE=BASE/'resources/native'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=2)+'\n')
def load(n):
 spec=importlib.util.spec_from_file_location('portal_judge_'+n,NATIVE/(n+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def plain(x):
 if x is None or isinstance(x,(str,int,float,bool)):return x
 try:return [plain(v) for v in x]
 except:return str(x)
def matrix(m):return [list(r) for r in m]
def bounds(vertices):
 a=list(vertices)
 if not a:return None
 return [[min(v[i] for v in a) for i in range(3)],[max(v[i] for v in a) for i in range(3)]]
def object_record(o,dg):
 d={'type':o.type,'parent':o.parent.name if o.parent else None,'matrixWorld':matrix(o.matrix_world),'location':list(o.location),'rotationEuler':list(o.rotation_euler),'scale':list(o.scale),'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'hideSet':o.hide_get(),'modifiers':[{'name':m.name,'type':m.type,'showRender':m.show_render,'showViewport':m.show_viewport,**({k:plain(getattr(m,k)) for k in ['width','segments','limit_method']} if m.type=='BEVEL' else {})} for m in o.modifiers]}
 if o.type=='MESH':
  raw=[o.matrix_world@v.co for v in o.data.vertices];eo=o.evaluated_get(dg);me=eo.to_mesh();ev=[eo.matrix_world@v.co for v in me.vertices]
  d.update(rawAuthoredBounds=bounds(raw),evaluatedModifierBounds=bounds(ev),rawVertexCount=len(o.data.vertices),evaluatedVertexCount=len(me.vertices),materials=[s.material.name if s.material else None for s in o.material_slots],shapeKeys=[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],rawMinZVertices=[list(v) for v in raw if v.z<=min(p.z for p in raw)+1e-6])
  eo.to_mesh_clear()
 return d
def graph(mat):
 return {'name':mat.name,'properties':{k:plain(mat[k]) for k in mat.keys()},'nodes':[{'name':n.name,'type':n.type,'label':n.label,'inputs':{i.name:plain(i.default_value) for i in n.inputs if hasattr(i,'default_value') and not i.is_linked},**({'image':n.image.name,'filepath':n.image.filepath,'packed':bool(n.image.packed_file)} if n.type=='TEX_IMAGE' and n.image else {})} for n in mat.node_tree.nodes] if mat.use_nodes else [],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in mat.node_tree.links] if mat.use_nodes else []}
scenes=[s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33]
assert len(scenes)==1
sc=scenes[0];bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
rig=json.loads((BASE/'resources/inputs/source-rig.json').read_text());asset=json.loads((BASE/'resources/inputs/source-assetRecord.json').read_text());root=bpy.data.objects[rig['groundRootObject']]
col=next(c for c in sc.collection.children if root in list(c.all_objects));owned=list(col.all_objects)
initial={'blender':bpy.app.version_string,'scene':sc.name,'sourceSHA256':sha(bpy.data.filepath),'savedFrame':sc.frame_current,'collection':col.name,'root':root.name,'savedCamera':{'name':sc.camera.name,'type':sc.camera.data.type,'orthoScale':sc.camera.data.ortho_scale,'matrixWorld':matrix(sc.camera.matrix_world),'resolution':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]} if sc.camera else None,'savedVisibility':{o.name:[o.hide_render,o.hide_viewport,o.hide_get()] for o in owned}}
# Enable actual ancestry and every owned object before any evaluated measurement.
def layers(l):
 yield l
 for c in l.children:yield from layers(c)
for l in layers(sc.view_layers[0].layer_collection):l.exclude=False;l.hide_viewport=False
for c in sc.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
for c in [col,*list(col.children_recursive)]:c.hide_render=False;c.hide_viewport=False
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=col
for o in owned:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
sc.view_layers[0].update();bpy.context.evaluated_depsgraph_get().update()
asset.update(root=root,collection=col,clips=rig['clips'])
runtime=load('capture_runtime');native=load('native_actions');runtime.scene=lambda:sc;runtime.SCENE_NAME=sc.name
camera=runtime.configure_camera(asset['projection'],tuple(asset['frame']),tuple(asset['anchor']),int(asset['scale']))
sc.render.image_settings.compression=15;sc.render.use_file_extension=True;sc.render.use_persistent_data=True;sc.render.threads_mode='FIXED';sc.render.threads=4
if hasattr(sc,'eevee'):
 for n in ['taa_render_samples','taa_samples']:
  if hasattr(sc.eevee,n):setattr(sc.eevee,n,32)
initial['camera']=camera;initial['actualCamera']={'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'clipStartEnd':[sc.camera.data.clip_start,sc.camera.data.clip_end]}
initial['render']={'engine':sc.render.engine,'frame':[sc.render.resolution_x,sc.render.resolution_y],'fps':sc.render.fps,'transparent':sc.render.film_transparent,'filterSize':sc.render.filter_size,'dither':sc.render.dither_intensity,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'gamma':sc.view_settings.gamma,'exposure':sc.view_settings.exposure,'compositor':sc.compositing_node_group.name if sc.compositing_node_group else None}
initial['lights']=[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'location':list(o.location),'rotation':list(o.rotation_euler),'size':getattr(o.data,'size',None)} for o in sc.collection.objects if o.type=='LIGHT']
initial['materials']=[graph(m) for m in sorted({s.material for o in owned if o.type=='MESH' for s in o.material_slots if s.material},key=lambda x:x.name)]
initial['nativeActions']=[{'owner':t['ownerName'],'action':t['action'],'frameRange':list(bpy.data.actions[t['action']].frame_range),'slot':t.get('slotIdentifier')} for t in rig['clips']['idle']['actions']]
initial['rigFacts']={'armatures':[o.name for o in owned if o.type=='ARMATURE'],'shapeKeys':[o.name for o in owned if o.type=='MESH' and o.data.shape_keys],'constraints':{o.name:[c.type for c in o.constraints] for o in owned if o.constraints},'externalParents':[o.name for o in owned if o.parent and o.parent not in owned]}
write(BASE/'native-inspection.json',initial)
records=[];measurements={};closure={}
for facing in ['N','E','S','W']:
 measurements[facing]=[]
 for i in range(13):
  native.apply_clip(asset,rig,'idle',frame=i+1,direction=facing,scene=sc)
  sc.view_layers[0].update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
  objs={o.name:object_record(o,dg) for o in owned}
  raw=bounds([Vector(p) for d in objs.values() if d.get('rawAuthoredBounds') for p in d['rawAuthoredBounds']]);evaluated=bounds([Vector(p) for d in objs.values() if d.get('evaluatedModifierBounds') for p in d['evaluatedModifierBounds']])
  rec={'direction':facing,'clip':'idle','frameIndex':i,'blenderFrame':i+1,'rootRotationZ':root.rotation_euler.z,'rootMatrix':matrix(root.matrix_world),'rawAuthoredBounds':raw,'evaluatedModifierBounds':evaluated,'objects':objs}
  measurements[facing].append(rec)
  if i==12:closure[facing]=rec;continue
  path=BASE/'raw'/'idle'/facing/(f'{i:03d}.png');path.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(path);started=time.monotonic();bpy.ops.render.render(write_still=True,scene=sc.name)
  records.append({k:rec[k] for k in ['direction','clip','frameIndex','blenderFrame','rootRotationZ','rootMatrix','rawAuthoredBounds','evaluatedModifierBounds']}|{'path':str(path.relative_to(BASE)),'sha256':sha(path),'seconds':time.monotonic()-started})
  write(BASE/'capture-progress.json',{'done':len(records),'total':48,'last':records[-1]['path']});print('PORTAL_PROGRESS',len(records),str(path),flush=True)
write(BASE/'native-measurements.json',{'rootObject':root.name,'measurementPolicy':'Enabled ancestry and owned objects, updated depsgraph; transformed raw authored geometry and evaluated modifiers measured separately. Source snapshot, no design locks inferred.','nativeGeometryMeasurements':{k:[r['objects'] for r in v] for k,v in measurements.items()},'frames':measurements,'loopClosureFrames':closure})
write(BASE/'nativeValidation.json',{'asset':'portal-rim','preparationOnly':True,'sourceSHA256':initial['sourceSHA256'],'source':str(Path(bpy.data.filepath)),'camera':camera,'actualCamera':initial['actualCamera'],'captureRecords':records,'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'sourceScale':4,'measurementLedger':'native-measurements.json','loopClosureMeasured':True,'renderSettings':initial['render'],'approval':False})
print('PORTAL_COMPLETE',len(records),flush=True)
