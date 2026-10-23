import bpy,sys,json,math,importlib.util,hashlib,time
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1]
def mod(n):
 spec=importlib.util.spec_from_file_location('fishprep_'+n,P/'resources/native'/f'{n}.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
def write(n,d):
 p=P/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mat(m):return [list(r) for r in m]
def bound(pts):return {'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)]} if pts else None
A=json.loads((P/'resources/inputs/source-assetRecord.json').read_text());R=json.loads((P/'resources/inputs/source-rig.json').read_text())
scenes=[s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33]
assert len(scenes)==1
s=scenes[0];bpy.context.window.scene=s;bpy.context.window.view_layer=s.view_layers[0]
root=bpy.data.objects[R['groundRootObject']];coll=next(c for c in s.collection.children if root in list(c.all_objects))
# Ensure actual active scene/viewlayer sees owned ancestry and objects, exclude siblings.
def ancestry(lc):
 hit=(lc.collection==coll)
 for c in lc.children:hit=ancestry(c) or hit
 if hit:lc.exclude=False;lc.hide_viewport=False;lc.collection.hide_viewport=False;lc.collection.hide_render=False
 return hit
ancestry(s.view_layers[0].layer_collection)
for lc in s.view_layers[0].layer_collection.children:lc.exclude=lc.collection!=coll
for c in s.collection.children:c.hide_render=c!=coll;c.hide_viewport=c!=coll
owned=list(coll.all_objects)
for o in owned:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
s.view_layers[0].update();bpy.context.evaluated_depsgraph_get().update()
A.update(root=root,collection=coll)
rt=mod('capture_runtime');native=mod('native_actions');rt.scene=lambda:s;rt.SCENE_NAME=s.name
camera=rt.configure_camera(A['projection'],A['frame'],A['anchor'],A['scale'],A.get('camera_elevation_degrees'))
s.render.threads_mode='FIXED';s.render.threads=4
if hasattr(s,'eevee'):
 for k in ['taa_render_samples','taa_samples']:
  if hasattr(s.eevee,k):setattr(s.eevee,k,32)
s.render.image_settings.compression=15
# Capture native material graphs, links and all values actually used by the fish.
materials=[]
for m in sorted({slot.material for o in owned if o.type=='MESH' for slot in o.material_slots if slot.material},key=lambda m:m.name):
 nodes=[]
 for n in m.node_tree.nodes:
  inputs={}
  for i in n.inputs:
   if hasattr(i,'default_value'):
    v=i.default_value
    if isinstance(v,(int,float,str,bool)):inputs[i.name]=v
    elif hasattr(v,'__iter__'):
     try:inputs[i.name]=list(v)
     except TypeError:pass
  item={'name':n.name,'type':n.type,'inputs':inputs}
  if n.type=='VALTORGB':item['colorRamp']=[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]
  nodes.append(item)
 materials.append({'name':m.name,'nodes':nodes,'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in m.node_tree.links],'externalImageNodes':[n.image.name for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]})
write('actual-source-inspection.json',{'sourceSHA256':sha(Path(bpy.data.filepath)),'scene':s.name,'collection':coll.name,'blender':bpy.app.version_string,'camera':camera,'materials':materials,'objects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrix':mat(o.matrix_world),'meshVertices':len(o.data.vertices) if o.type=='MESH' else None,'meshPolygons':len(o.data.polygons) if o.type=='MESH' else None,'modifiers':[{'name':m.name,'type':m.type,'object':getattr(getattr(m,'object',None),'name',None)} for m in o.modifiers],'shapeKeys':list(o.data.shape_keys.key_blocks.keys()) if o.type=='MESH' and o.data.shape_keys else [],'vertexGroups':[v.name for v in o.vertex_groups] if o.type=='MESH' else [],'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'deform':b.use_deform} for b in o.data.bones] if o.type=='ARMATURE' else []} for o in owned],'lightFields':[{'name':o.name,'energy':o.data.energy,'color':list(o.data.color),'size':getattr(o.data,'size',None),'matrix':mat(o.matrix_world)} for o in s.objects if o.type=='LIGHT'],'externalLibraries':[l.filepath for l in bpy.data.libraries],'usedExternalImages':[n for m in materials for n in m['externalImageNodes']],'initialNoncontractDump':'noncontract-active-scene-diagnostic.json is excluded because it used the saved unrelated active scene; do not freeze its bounds/matrices.'})
records=[];loopchecks=[];captures=[]
for clip,recipe in R['clips'].items():
 for d in A['directions']:
  frames=[]
  for fi in range(recipe['frames']+(1 if recipe['loop'] else 0)):
   native.apply_clip(A,R,clip,fi+1,d,s);s.view_layers[0].update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
   raw=[];ev=[];by=[]
   for o in owned:
    if o.type!='MESH':continue
    rp=[o.matrix_world@v.co for v in o.data.vertices];e=o.evaluated_get(dg);mesh=e.to_mesh();ep=[e.matrix_world@v.co for v in mesh.vertices];e.to_mesh_clear();raw.extend(rp);ev.extend(ep)
    by.append({'object':o.name,'rawAuthoredBounds':bound(rp),'evaluatedModifierBounds':bound(ep)})
   points=[world_to_camera_view(s,s.camera,p) for p in ev]
   arm=next(o for o in owned if o.type=='ARMATURE')
   record={'direction':d,'clip':clip,'index':fi,'frame':fi+1,'closingKey':fi==recipe['frames'],'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':mat(root.matrix_world),'rawAuthoredBounds':bound(raw),'evaluatedModifierBounds':bound(ev),'perObjectBounds':by,'cameraBoundsNormalized':{'min':[min(p[i] for p in points) for i in range(2)],'max':[max(p[i] for p in points) for i in range(2)]},'armatureMatrix':mat(arm.matrix_world),'boneMatrices':{b.name:mat(b.matrix) for b in arm.pose.bones},'socketsWorld':{k:list(root.matrix_world@Vector(v)) for k,v in A['sockets'].items()}}
   records.append(record);frames.append(record)
  if recipe['loop']:
   a,b=frames[0],frames[-1];err=max(abs(x-y) for n in a['boneMatrices'] for row1,row2 in zip(a['boneMatrices'][n],b['boneMatrices'][n]) for x,y in zip(row1,row2));loopchecks.append({'clip':clip,'direction':d,'first':1,'closing':13,'maxBoneMatrixResidual':err,'armatureResidual':max(abs(x-y) for r1,r2 in zip(a['armatureMatrix'],b['armatureMatrix']) for x,y in zip(r1,r2))})
  # One bounded native replay sample for every state/facing, plus target-source frame9 S normal.
  fi=9 if clip=='normal' and d=='S' else 0
  native.apply_clip(A,R,clip,fi+1,d,s)
  path=P/'native'/clip/d/(str(fi).zfill(3)+'.png');path.parent.mkdir(parents=True,exist_ok=True);s.render.filepath=str(path);start=time.time();bpy.ops.render.render(write_still=True,scene=s.name)
  captures.append({'clip':clip,'direction':d,'index':fi,'path':str(path.relative_to(P)),'sha256':sha(path),'dimensions':[s.render.resolution_x,s.render.resolution_y],'seconds':time.time()-start,'rootRotationZ':root.rotation_euler.z,'rootMatrix':mat(root.matrix_world)})
  write('native-capture-records.json',{'asset':'creature-fish','camera':camera,'captureRecords':captures,'samples':32,'threads':4,'renderer':s.render.engine,'blender':bpy.app.version_string,'replayScope':'one native sample each of 11 clips x4 facings; all authored frame geometry and loop closure evaluated; full existing catalog atlas playback supplies all original frame pixels.'})
  print('FISH_PREP_CAPTURE',clip,d,fi,flush=True)
write('native-geometry-measurements.json',{'asset':'creature-fish','views':records,'loopChecks':loopchecks,'allClipCount':11,'uniqueFrameCount':528,'sourceScale':4,'rawFrame':[1792,2048],'logicalFrame':A['frame'],'logicalRoot':A['anchor'],'captureCamera':camera})
print('FISH_PREP_COMPLETE',flush=True)
