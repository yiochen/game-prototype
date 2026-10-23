import bpy,sys,math,json,hashlib,struct,bmesh
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
SOURCE=Path(bpy.data.filepath);before=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert before=='1efc24a21f1ade2accdcca93446f2c4d9743df4437ad2e927c1c239849003aa4'
sc=bpy.data.scenes['safe-passage warm-soft round-01'];bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
root=bpy.data.objects['safe-passage__root'];col=bpy.data.collections['S33_PROP_safe-passage.001'];owned=sorted(col.all_objects,key=lambda o:o.name)
def mat(m):return [list(r) for r in m]
def bb(v):return {'min':[min(p[i] for p in v) for i in range(3)],'max':[max(p[i] for p in v) for i in range(3)]}
def digest(v):return hashlib.sha256(b''.join(struct.pack('<3f',*p) for p in v)).hexdigest()
def write(n,v):p=H/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def enable():
 def lc(l):
  l.exclude=False;l.hide_viewport=False
  for x in l.children:lc(x)
 lc(sc.view_layers[0].layer_collection)
 sc.collection.hide_render=sc.collection.hide_viewport=False
 for c in [col,*list(col.children_recursive)]:c.hide_render=c.hide_viewport=False
 for o in owned:o.hide_render=o.hide_viewport=False;o.hide_set(False)
 sc.view_layers[0].update();bpy.context.evaluated_depsgraph_get().update()
def project(p):
 q=world_to_camera_view(sc,sc.camera,p);return [q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y]
def curves(a):return [f for l in a.layers for s in l.strips for c in s.channelbags for f in c.fcurves]
enable();sc.frame_set(1)
actions=[];top=[]
for o in owned:
 if o.animation_data and o.animation_data.action:
  a=o.animation_data.action;actions.append({'owner':o.name,'action':a.name,'frameRange':list(a.frame_range),'curves':[{'dataPath':f.data_path,'arrayIndex':f.array_index,'keys':[[k.co.x,k.co.y,k.interpolation] for k in f.keyframe_points]} for f in curves(a)],'drivers':[f.data_path for f in o.animation_data.drivers],'NLATracks':len(o.animation_data.nla_tracks)})
 if o.type=='MESH':
  bm=bmesh.new();bm.from_mesh(o.data);top.append({'object':o.name,'role':o.get('role'),'parent':o.parent.name if o.parent else None,'rawVertices':len(bm.verts),'rawFaces':len(bm.faces),'edgesNotTwoFaces':sum(len(e.link_faces)!=2 for e in bm.edges),'signedVolume':bm.calc_volume(signed=True),'localDeterminant':o.matrix_local.determinant(),'shapeKeys':bool(o.data.shape_keys),'modifiers':[{'name':m.name,'type':m.type,'render':m.show_render,'viewport':m.show_viewport,'levels':getattr(m,'levels',None),'renderLevels':getattr(m,'render_levels',None),'width':getattr(m,'width',None)} for m in o.modifiers]});bm.free()
cam=sc.camera
p0=project(Vector((0,0,0)))
camera={'type':cam.data.type,'matrix':mat(cam.matrix_world),'projectionMatrix':mat(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)),'orthoScale':cam.data.ortho_scale,'sensorFit':cam.data.sensor_fit,'shift':[cam.data.shift_x,cam.data.shift_y],'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'rootPixel':p0,'unitX':[project(Vector((1,0,0)))[i]-p0[i] for i in range(2)],'unitDepth':[project(Vector((0,-1,0)))[i]-p0[i] for i in range(2)],'unitHeight':[project(Vector((0,0,1)))[i]-p0[i] for i in range(2)]}
materials=[]
for m in sorted({m for o in owned if o.type=='MESH' for m in o.data.materials if m},key=lambda m:m.name):
 def plain(x):
  try:return list(x)
  except:return x
 materials.append({'name':m.name,'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:plain(i.default_value) for i in n.inputs if hasattr(i,'default_value') and not i.is_linked},'ramps':[(e.position,list(e.color)) for e in n.color_ramp.elements] if n.type=='VALTORGB' else None,'texture':n.image.filepath if n.type=='TEX_IMAGE' and n.image else None} for n in m.node_tree.nodes],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in m.node_tree.links]})
write('native-source.json',{'sourceSHA256':before,'scene':sc.name,'collection':col.name,'root':root.name,'rootMetadata':{k:root[k] for k in root.keys()},'camera':camera,'topology':top,'actions':actions,'materials':materials,'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'matrix':mat(o.matrix_world),'color':list(o.data.color),'size':o.data.size,'shape':o.data.shape} for o in sc.objects if o.type=='LIGHT'],'world':{'strength':sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value,'color':list(sc.world.node_tree.nodes['Background'].inputs['Color'].default_value)},'render':{'engine':sc.render.engine,'transparent':sc.render.film_transparent,'fps':sc.render.fps,'dither':sc.render.dither_intensity,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'compositor':getattr(getattr(sc,'compositing_node_group',None),'name',None)},'externalLibraries':[l.filepath for l in bpy.data.libraries]})
def measure():
 dg=bpy.context.evaluated_depsgraph_get();dg.update();inv=root.matrix_world.inverted();objects=[];rall=[];eall=[];trees={};vertices={};faces={};world=[]
 for o in owned:
  if o.type!='MESH':continue
  eo=o.evaluated_get(dg);mesh=eo.to_mesh();raw=[inv@o.matrix_world@v.co for v in o.data.vertices];ev=[inv@eo.matrix_world@v.co for v in mesh.vertices];polys=[list(f.vertices) for f in mesh.polygons];vertices[o.name]=ev;faces[o.name]=polys;rall+=raw;eall+=ev;world.extend(eo.matrix_world@v.co for v in mesh.vertices)
  cuts=[]
  if o.get('role')=='stable_stone':
   trees[o.name]=BVHTree.FromPolygons(ev,polys)
   for e in mesh.edges:
    a,b=[ev[i] for i in e.vertices]
    if abs(a.z)<1e-8:cuts.append(list(a))
    if a.z*b.z<0:cuts.append(list(a+(b-a)*(-a.z/(b.z-a.z))))
  objects.append({'object':o.name,'role':o.get('role'),'rawBounds':bb(raw),'evaluatedBounds':bb(ev),'rawVertexCount':len(raw),'evaluatedVertexCount':len(ev),'evaluatedFingerprint':digest(ev),'worldMatrix':mat(eo.matrix_world),'localMatrix':mat(o.matrix_local),'groundIntersections':cuts,'rootWorld':[root.matrix_world.translation.x,root.matrix_world.translation.y,root.matrix_world.translation.z]})
  eo.to_mesh_clear()
 attachments=[]
 for o in owned:
  if o.get('role')!='attached_foliage':continue
  target=o.get('attachmentStone');tree=trees[target];pivot=inv@o.matrix_world.translation;q,n,_,dist=tree.find_nearest(pivot);sign=(pivot-q).dot(n);signed=[]
  for v in vertices[o.name]:
   near,norm,_,d=tree.find_nearest(v);signed.append((v-near).dot(norm))
  attachments.append({'object':o.name,'stone':target,'pivotCanonicalS':list(pivot),'pivotSignedNearestDistance':sign,'evaluatedLeafVerticesInsideStone':sum(v<=1e-6 for v in signed),'evaluatedLeafMinimumSignedDistance':min(signed),'evaluatedLeafMaximumSignedDistance':max(signed),'leafMeshBaseRawAtPivot':o.data.vertices[0].co.length})
 projected=[project(p) for p in world]
 return {'rawBoundsCanonicalS':bb(rall),'evaluatedBoundsCanonicalS':bb(eall),'worldEvaluatedBounds':bb(world),'projectedPixelBounds':{'min':[min(p[i] for p in projected) for i in range(2)],'max':[max(p[i] for p in projected) for i in range(2)]},'objects':objects,'foliageAttachmentMeasurements':attachments,'geometryFingerprint':digest(eall)}
records=[];close={}
for d in 'NESW':
 root.rotation_euler.z={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[d]
 for i in range(12):
  sc.frame_set(i+1);enable();gm=measure();p=H/'native'/d/f'{i:03}.png';p.parent.mkdir(parents=True,exist_ok=True)
  rec={'direction':d,'clip':'ambient','index':i,'blenderFrame':sc.frame_current,'rootRotationZ':root.rotation_euler.z,'rootMatrix':mat(root.matrix_world),'cameraMatrix':mat(cam.matrix_world),'cameraRootPixel':project(Vector((0,0,0))),'geometry':gm,'path':str(p.relative_to(H))}
  sc.render.filepath=str(p);bpy.ops.render.render(write_still=True,scene=sc.name);rec['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();records.append(rec);print('JUDGE_NATIVE_PHASE '+d+' '+str(i),flush=True)
 sc.frame_set(13);enable();close[d]={'rootMatrix':mat(root.matrix_world),'geometry':measure()}
write('native-replay.json',{'sourceSHA256':before,'sourceUnchanged':hashlib.sha256(SOURCE.read_bytes()).hexdigest()==before,'savedSourceChanges':False,'captureRecords':records,'closingFrame13':close,'blenderVersion':bpy.app.version_string,'interpretation':'Independent enabled saved-source replay, no model/action/camera/light/material edits; only root facing, frame evaluation and output path changed unsaved. Canonical raw and evaluated modifier bounds separate. Actual native captures compared to exact submitted native and reduced frames separately.'})
print('JUDGE_NATIVE_COMPLETE',flush=True)
