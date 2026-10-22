import bpy, json, math, hashlib, pathlib, sys, importlib.util
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
BASE=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
OBJ=BASE/'prototypes/sushi-loop/assets/refinement/objects/garbage-sofa'
OUT=OBJ/'reviews'
SOURCE=pathlib.Path(bpy.data.filepath)
rig=json.loads((OBJ/'inputs/source-rig.json').read_text())
camera=json.loads((OBJ/'inputs/source-camera.json').read_text())
root=bpy.data.objects[rig['groundRootObject']]
coll=next(c for c in bpy.data.collections if root in list(c.objects))
sc=next(s for s in bpy.data.scenes if root.name in s.objects)
original_active={'scene':bpy.context.scene.name,'camera':bpy.context.scene.camera.name if bpy.context.scene.camera else None}
bpy.context.window.scene=sc
for c in sc.collection.children:c.hide_render=c!=coll;c.hide_viewport=c!=coll
def layers(n):
 yield n
 for x in n.children:yield from layers(x)
for l in layers(sc.view_layers[0].layer_collection):l.exclude=False
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=coll
sc.view_layers[0].update()
spec=importlib.util.spec_from_file_location('judge_native',BASE/'prototypes/sushi-loop/assets/production/source/blender/native_actions.py')
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
asset={'id':'garbage-sofa','root':root,'collection':coll}
def plain(x):
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 if hasattr(x,'items'):return {str(k):plain(v) for k,v in x.items()}
 try:return [plain(v) for v in x]
 except:return str(x)
def rows(x):return [[float(v) for v in r] for r in x]
def bounds(points):
 if not points:return None
 return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def verts(o,dg):
 ev=o.evaluated_get(dg);m=ev.to_mesh();inv=root.matrix_world.inverted()
 ps=[inv@ev.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();return ps
objects=list(coll.all_objects)
result={'blender':bpy.app.version_string,'source':{'path':str(SOURCE),'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest()},'originalActive':original_active,'scene':sc.name,'collection':coll.name,'root':{'name':root.name,'matrix':rows(root.matrix_world),'properties':plain(dict(root))},'objects':[],'actions':{},'samples':[]}
for o in objects:
 result['objects'].append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'properties':plain(dict(o)),'matrixLocal':rows(o.matrix_local),'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers],'constraints':[c.type for c in o.constraints],'vertices':len(o.data.vertices) if o.type=='MESH' else None,'materials':[m.name for m in o.data.materials] if o.type=='MESH' else [],'hideRender':o.hide_render,'hideViewport':o.hide_viewport})
for clip,record in rig['clips'].items():
 result['actions'][clip]=[]
 for t in record['actions']:
  a=bpy.data.actions[t['action']]
  curves=[{'path':fc.data_path,'index':fc.array_index,'keys':[{'co':list(k.co),'interpolation':k.interpolation} for k in fc.keyframe_points]} for fc in native._fcurves(a)]
  result['actions'][clip].append({**t,'curves':curves,'sha256':digest(curves)})
 for direction in ['S','E','N','W']:
  for f in range(1,record['frames']+1):
   native.apply_clip(asset,rig,clip,f,direction,sc);dg=bpy.context.evaluated_depsgraph_get();allps=[];parts=[];world=[]
   for o in objects:
    if o.type!='MESH':continue
    ps=verts(o,dg);allps+=ps;world += [root.matrix_world@p for p in ps]
    parts.append({'name':o.name,'bounds':bounds(ps),'matrixLocal':rows(o.matrix_local),'scale':list(o.scale),'rotationEuler':list(o.rotation_euler),'location':list(o.location),'hideRender':o.hide_render,'visibleCamera':o.visible_camera,'vertexHash':digest([[round(v,8) for v in p] for p in ps]),'groundVerticesWithin004':sum(abs(p.z)<=.04 for p in ps)})
   result['samples'].append({'clip':clip,'direction':direction,'frame':f,'rootMatrix':rows(root.matrix_world),'localBounds':bounds(allps),'worldBounds':bounds(world),'parts':parts})
 # actual closing pose, evaluated separately
 if record.get('closingKeyFrame'):
  native.apply_clip(asset,rig,clip,record['closingKeyFrame'],'S',sc)
  dg=bpy.context.evaluated_depsgraph_get()
  result['loopClosure']={'frame':record['closingKeyFrame'],'parts':[{'name':o.name,'vertexHash':digest([[round(v,8) for v in p] for p in verts(o,dg)])} for o in objects if o.type=='MESH']}
native.apply_clip(asset,rig,'idle',1,'S',sc);dg=bpy.context.evaluated_depsgraph_get()
result['idleParts']=[{'name':o.name,'bounds':bounds(verts(o,dg)),'groundPoints':[[float(v) for v in p] for p in verts(o,dg) if abs(p.z)<=.04]} for o in objects if o.type=='MESH']
materials={m for o in objects if o.type=='MESH' for m in o.data.materials if m}
result['materials']=[]
for m in materials:
 result['materials'].append({'name':m.name,'diffuseColor':list(m.diffuse_color),'useNodes':m.use_nodes,'surfaceRenderMethod':getattr(m,'surface_render_method',None),'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':{s.name:plain(s.default_value) for s in n.inputs if hasattr(s,'default_value')},'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None} for n in m.node_tree.nodes] if m.use_nodes else [],'links':[{'from':l.from_node.name+'.'+l.from_socket.name,'to':l.to_node.name+'.'+l.to_socket.name} for l in m.node_tree.links] if m.use_nodes else []})
result['resources']={'libraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':i.name,'source':i.source,'path':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images],'fonts':[{'name':f.name,'path':f.filepath,'packed':bool(f.packed_file)} for f in bpy.data.fonts],'externalObjectData':[o.name for o in objects if o.library or (o.data and o.data.library)]}
result['savedCameras']=[{'name':o.name,'matrix':rows(o.matrix_world),'orthoScale':o.data.ortho_scale,'type':o.data.type,'shift':[o.data.shift_x,o.data.shift_y]} for o in sc.objects if o.type=='CAMERA']
# Reconstruct the registered asset camera in memory only, independent of saved active camera.
cam=bpy.data.objects.new('Judge registered sofa camera',bpy.data.cameras.new('Judge registered sofa camera'));sc.collection.objects.link(cam);sc.camera=cam
cam.matrix_world=Matrix(camera['camera']['worldMatrix']);cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=448/128;cam.data.shift_x=0;cam.data.shift_y=0
sc.render.resolution_x=896;sc.render.resolution_y=1152;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=camera['camera']['pixelAspect'][0];sc.render.pixel_aspect_y=1
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return [p.x*896,(1-p.y)*1152]
bpy.context.view_layer.update();base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-base[1];cam.data.shift_y=(704-base[1])/dy;bpy.context.view_layer.update()
result['registeredCamera']={'matrix':rows(cam.matrix_world),'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'root':px((0,0,0)),'unitX':px((1,0,0)),'unitDepth':px((0,-1,0)),'unitHeight':px((0,0,1)),'projectionMatrix':rows(cam.calc_matrix_camera(dg,x=896,y=1152,scale_x=sc.render.pixel_aspect_x,scale_y=1))}
result['topology']=[]
for o in objects:
 if o.type!='MESH':continue
 edge_counts={e.index:0 for e in o.data.edges}
 for poly in o.data.polygons:
  for li in poly.loop_indices:edge_counts[o.data.loops[li].edge_index]+=1
 result['topology'].append({'name':o.name,'polygons':len(o.data.polygons),'edges':len(o.data.edges),'boundaryEdges':sum(n==1 for n in edge_counts.values()),'nonmanifoldEdges':sum(n!=2 for n in edge_counts.values()),'zeroAreaFaces':sum(p.area<1e-10 for p in o.data.polygons),'uvLayers':list(o.data.uv_layers.keys()),'shapeKeys':list(o.data.shape_keys.key_blocks.keys()) if o.data.shape_keys else [],'drivers':len(o.animation_data.drivers) if o.animation_data else 0})
result['sourceSceneLighting']=[{'name':o.name,'position':list(o.location),'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'size':getattr(o.data,'size',None)} for o in sc.objects if o.type=='LIGHT']
result['source']['unchangedAfter']=hashlib.sha256(SOURCE.read_bytes()).hexdigest()==result['source']['sha256']
(OUT/'source-audit-raw.json').write_text(json.dumps(result,indent=2)+'\n')
print('JUDGE_AUDIT_COMPLETE',json.dumps({'collection':coll.name,'objects':len(objects),'samples':len(result['samples']),'idleBounds':result['samples'][0]['localBounds'],'camera':result['registeredCamera'],'hashUnchanged':result['source']['unchangedAfter']}))
